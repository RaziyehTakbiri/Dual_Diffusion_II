# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # B08 N1 — UC-native isolated overlay and F152 lock candidate-003
# MAGIC
# MAGIC This notebook constructs a review-pending, data-free dependency candidate
# MAGIC without directing any install at the Databricks base Python environment.
# MAGIC Its default mode is read-only preflight. Construction is possible only
# MAGIC after the bounded widget inputs are explicit and the one-shot
# MAGIC authorization gates are deliberately enabled.
# MAGIC
# MAGIC Construction uses a temporary isolated virtual environment, accepts wheels
# MAGIC only, builds the project wheel from a copied source-only tree, installs the
# MAGIC resulting exact hash lock into a separate overlay directory, verifies the
# MAGIC wheel and installed-file closures, builds one deterministic local archive,
# MAGIC and streams that archive into bounded append-only objects below the exact
# MAGIC Unity Catalog Volume parent qualified by probe-001. Each object uses
# MAGIC exclusive create, complete close, and two fresh size/SHA-256 readbacks.
# MAGIC No UC-storage decision uses fsync, chmod, device/inode, timestamp, rename,
# MAGIC deletion, or directory identity. The final success receipt is the commit
# MAGIC marker; every candidate object remains review-pending. The notebook does
# MAGIC not supply study/test-data paths, Spark operations, Databricks REST calls,
# MAGIC or scientific-execution requests. Downloaded build tools run as bounded
# MAGIC child processes but are not OS-sandboxed, so unrelated-file access and
# MAGIC side effects by third-party code are explicitly not proven absent. The
# MAGIC notebook uses only bounded widgets to receive operator parameters without
# MAGIC editing this tracked source file.
# MAGIC
# MAGIC Candidate-003's parent, identifier, complete reserved namespace, official
# MAGIC indexes, accepted V2 profile, and successful probe-001 outcome are fixed in
# MAGIC this source. Always enter through the separately reviewed hash-first
# MAGIC launcher. Construction additionally requires the execution mode,
# MAGIC network/build authority, exact one-shot acknowledgement, and an exact
# MAGIC review-package authorization token issued only after the default preflight
# MAGIC output is independently reviewed. A direct builder-notebook run cannot
# MAGIC authorize construction.
# MAGIC The caller-supplied launch evidence is procedural operator attestation;
# MAGIC the exact reviewed, Git-tracked launcher is the trust anchor and cannot
# MAGIC cryptographically self-attest its own active bytes.
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
import signal
import shutil
import stat
import struct
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import venv
import zipfile


# COMMAND ----------

CONSTRUCT_MODE = "CONSTRUCT_ONE_UC_NATIVE_REVIEW_PENDING_CANDIDATE_003"
ACKNOWLEDGEMENT_TEXT = (
    "AUTHORIZE_ONE_DATA_FREE_N1_UC_NATIVE_NETWORK_BUILD_CANDIDATE_003"
)
REVIEW_AUTHORIZATION_PREFIX = (
    "AUTHORIZE_REVIEWED_CANDIDATE_003_PACKAGE_SHA256_"
)
REVIEW_PACKAGE_DOMAIN = b"heterodiff/b08/n1/candidate-003-review-package/v1\0"
HASH_FIRST_LAUNCH_SCHEMA = "heterodiff-b08-n1-hash-first-launch-v1"
GIT_REVISION_VERIFICATION_STATE = (
    "VERIFIED_READ_ONLY_BEFORE_INTENT_POST_INTENT_RECHECK_REQUIRED_"
    "BEFORE_NETWORK_OR_BUILD"
)


# COMMAND ----------

# OPERATOR INPUTS
#
# Values are supplied through Databricks widgets, so this tracked notebook never
# needs to be edited and the Git checkout can remain byte-clean. Outside
# Databricks, tests may use the named environment-variable fallbacks.
_WIDGET_API = globals().get("dbutils")
_WIDGET_INPUT_ACCESSED = _WIDGET_API is not None
_HASH_FIRST_LAUNCH_EVIDENCE = globals().get(
    "HETERODIFF_HASH_FIRST_LAUNCH_EVIDENCE"
)


def operator_parameter(name, default, label, choices=None):
    environment_name = "HETERODIFF_" + name.upper()
    if _WIDGET_API is None:
        return os.environ.get(environment_name, default)
    if choices is None:
        _WIDGET_API.widgets.text(name, default, label)
    else:
        _WIDGET_API.widgets.dropdown(name, default, list(choices), label)
    return _WIDGET_API.widgets.get(name)


def read_only_tool_environment():
    return {
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


REPO_ROOT_OVERRIDE = (
    os.environ.get("HETERODIFF_REPO_ROOT_OVERRIDE") or None
)
CANDIDATE_PARENT = Path(
    "/Volumes/development/team_eds_supplychain/b08_runtime_output"
)
CANDIDATE_ID = "b08-n1-overlay-candidate-003"
CANDIDATE_PREFIX = CANDIDATE_PARENT / CANDIDATE_ID
DURABLE_OUTPUT_DIRECTORY = CANDIDATE_PREFIX.as_posix()
PAYLOAD_CHUNK_BYTES = 256 * 1024 * 1024
PAYLOAD_CHUNK_LIMIT = 128
PAYLOAD_ARCHIVE_BYTE_LIMIT = PAYLOAD_CHUNK_BYTES * PAYLOAD_CHUNK_LIMIT
UC_READ_CHUNK_BYTES = 1024 * 1024
ARCHIVE_MEMBER_LIMIT = 250_000
ARCHIVE_MEMBER_NAME_BYTE_LIMIT = 65_535
ARCHIVE_CONSERVATIVE_FIXED_OVERHEAD_BYTES = 1024
ARCHIVE_CONSERVATIVE_MEMBER_OVERHEAD_BYTES = 512
ARCHIVE_TREE_ENTRY_LIMIT = 500_000
CONTROL_OBJECT_BYTE_LIMIT = 64 * 1024 * 1024
TOOL_COMMAND_LIMIT = 64
TOOL_OUTPUT_STREAM_BYTE_LIMIT = 16 * 1024 * 1024
TOOL_FAILURE_DIAGNOSTIC_TAIL_BYTE_LIMIT = 64 * 1024
TOOL_FAILURE_DETAIL_BYTE_LIMIT = 4 * 1024
TOOL_TIMEOUT_SECONDS = 1800
TOOL_REAP_SECONDS = 10
WHEEL_FILE_BYTE_LIMIT = 4 * 1024 * 1024 * 1024
WHEEL_ARTIFACT_LIMIT = 256
WHEEL_DIRECTORY_BYTE_LIMIT = 16 * 1024 * 1024 * 1024
WHEEL_MEMBER_LIMIT = 250_000
WHEEL_CENTRAL_DIRECTORY_BYTE_LIMIT = 64 * 1024 * 1024
WHEEL_MEMBER_BYTE_LIMIT = 4 * 1024 * 1024 * 1024
WHEEL_UNCOMPRESSED_BYTE_LIMIT = 16 * 1024 * 1024 * 1024
WHEEL_CONTROL_MEMBER_BYTE_LIMIT = 16 * 1024 * 1024
PIP_IDENTITY_CONTROL_FILE_BYTE_LIMIT = 16 * 1024 * 1024
OVERLAY_CONTROL_FILE_BYTE_LIMIT = 16 * 1024 * 1024
OVERLAY_ENTRYPOINT_BYTE_LIMIT = 1024 * 1024
OVERLAY_ENTRYPOINT_LIMIT = 10_000
OVERLAY_RECORD_ROW_LIMIT = 250_000
OVERLAY_DISTRIBUTION_LIMIT = 256
OVERLAY_TREE_ENTRY_LIMIT = 250_000
OVERLAY_SINGLE_FILE_BYTE_LIMIT = 4 * 1024 * 1024 * 1024
OVERLAY_TREE_TOTAL_BYTE_LIMIT = 16 * 1024 * 1024 * 1024
OVERLAY_SITE_PACKAGES_RELATIVE_PATH = Path("lib/python3.12/site-packages")
SOURCE_TREE_ENTRY_LIMIT = 100_000
SOURCE_FILE_BYTE_LIMIT = 16 * 1024 * 1024
SOURCE_TOTAL_BYTE_LIMIT = 512 * 1024 * 1024

# These reviewed defaults avoid manual URL copying. A future mirror change
# requires a new source revision and review; credentials are never accepted.
PRIMARY_SIMPLE_INDEX_URL = "https://pypi.org/simple"
PYTORCH_CPU_SIMPLE_INDEX_URL = "https://download.pytorch.org/whl/cpu"

# Construction requires four deliberate gates plus the hash-first launcher.
EXECUTION_MODE = operator_parameter(
    "b08_n1_uc_native_execution_mode",
    "PREFLIGHT_ONLY",
    "UC-native candidate-003 execution mode",
    ("PREFLIGHT_ONLY", CONSTRUCT_MODE),
)
_NETWORK_AUTHORIZATION_TEXT = operator_parameter(
    "b08_n1_uc_native_network_build_authorized",
    "false",
    "Authorize candidate-003 network/build (true or false)",
    ("false", "true"),
)
NETWORK_AND_BUILD_AUTHORIZED = _NETWORK_AUTHORIZATION_TEXT == "true"
ONE_SHOT_ACKNOWLEDGEMENT = (
    operator_parameter(
        "b08_n1_uc_native_one_shot_acknowledgement",
        "NOT_AUTHORIZED",
        "One-shot candidate-003 acknowledgement",
        ("NOT_AUTHORIZED", ACKNOWLEDGEMENT_TEXT),
    )
)
REVIEW_PACKAGE_AUTHORIZATION = operator_parameter(
    "b08_n1_uc_native_review_package_authorization",
    "NOT_AUTHORIZED",
    "Exact independently reviewed candidate-003 package authorization",
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
PROBE_REVIEW_RELATIVE_PATH = Path(
    "PROJECT_B08_N1_UC_VOLUME_WRITE_CAPABILITY_PROBE_INDEPENDENT_REVIEW.md"
)
EXPECTED_PROBE_REVIEW_FILE_SHA256 = (
    "7612dbe3c4072c0ab2847bb17d99d6a5aa66ccfff80734f0d961baec57229a59"
)
PROBE_OUTCOME_RELATIVE_PATH = Path(
    "PROJECT_B08_N1_UC_VOLUME_WRITE_CAPABILITY_PROBE_001_OUTCOME.md"
)
EXPECTED_PROBE_OUTCOME_FILE_SHA256 = (
    "f96160da93789d4749b3ce005182a0f57a49a5bc4408296d46ca4fd7fc71bcd7"
)
BUILDER_NOTEBOOK_RELATIVE_PATH = Path(
    "databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py"
)
LAUNCHER_NOTEBOOK_RELATIVE_PATH = Path(
    "databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate_launcher.py"
)
NOTEBOOK_SCHEMA = "heterodiff-b08-n1-uc-native-overlay-construction-v1"
MANIFEST_SCHEMA = "heterodiff-b08-n1-uc-native-overlay-manifest-v1"
RECEIPT_SCHEMA = "heterodiff-b08-n1-uc-native-overlay-receipt-v1"
ATTEMPT_INTENT_SCHEMA = "heterodiff-b08-n1-uc-native-attempt-intent-v1"
FAILURE_RECEIPT_SCHEMA = "heterodiff-b08-n1-uc-native-failure-receipt-v1"
SOURCE_MANIFEST_DOMAIN = b"heterodiff/b08/n1/project-source-manifest/v1\0"
OVERLAY_MANIFEST_DOMAIN = b"heterodiff/b08/n1/uc-native-overlay-manifest/v1\0"
ATTEMPT_INTENT_DOMAIN = b"heterodiff/b08/n1/uc-native-attempt-intent/v1\0"

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
WHEEL_FILENAME_DISTRIBUTION = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9._]*[A-Za-z0-9])?"
)
WHEEL_METADATA_NAME = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
)
WHEEL_VERSION_TOKEN = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9.!+_]*[A-Za-z0-9])?"
)
WHEEL_BUILD_TOKEN = re.compile(r"[0-9][A-Za-z0-9_]*")
WHEEL_TAG_COMPONENT = re.compile(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*")


class CandidateConstructionError(RuntimeError):
    def __init__(
        self,
        code,
        detail=None,
        telemetry=None,
        stdout=None,
        stderr=None,
        output_capture_complete=None,
    ):
        super().__init__(code if detail is None else f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.telemetry = telemetry
        self.stdout = stdout
        self.stderr = stderr
        self.output_capture_complete = output_capture_complete


def canonical_json_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def immutable_json_snapshot(value):
    """Return a deep, alias-free snapshot suitable for durable records."""
    return json.loads(canonical_json_bytes(value).decode("ascii"))


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_file(path, maximum_bytes=None):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if maximum_bytes is not None and size > maximum_bytes:
                raise CandidateConstructionError(
                    "FILE_EXCEEDS_HASH_BYTE_LIMIT", path.name
                )
            digest.update(chunk)
    return digest.hexdigest(), size


def sha256_regular_file_nofollow(path, maximum_bytes, label):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise CandidateConstructionError(label + "_OPEN_FAILED") from error
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size < 0
            or opened.st_size > maximum_bytes
        ):
            raise CandidateConstructionError(
                label + "_SIZE_OR_TYPE_INVALID"
            )
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > maximum_bytes:
                raise CandidateConstructionError(
                    label + "_EXPANDED_PAST_LIMIT"
                )
            digest.update(chunk)
        final = os.fstat(descriptor)
        if size != opened.st_size or final.st_size != opened.st_size:
            raise CandidateConstructionError(
                label + "_SIZE_CHANGED_DURING_READ"
            )
        return (
            digest.hexdigest(),
            size,
            opened.st_mode,
            opened.st_nlink,
        )
    finally:
        os.close(descriptor)


def read_regular_file_nofollow_bounded(path, maximum_bytes, label):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise CandidateConstructionError(label + "_OPEN_FAILED") from error
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size < 0
            or opened.st_size > maximum_bytes
        ):
            raise CandidateConstructionError(
                label + "_SIZE_OR_TYPE_INVALID"
            )
        payload = bytearray()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > maximum_bytes:
                raise CandidateConstructionError(
                    label + "_EXPANDED_PAST_LIMIT"
                )
        final = os.fstat(descriptor)
        if len(payload) != opened.st_size or final.st_size != opened.st_size:
            raise CandidateConstructionError(
                label + "_SIZE_CHANGED_DURING_READ"
            )
        return bytes(payload)
    finally:
        os.close(descriptor)


def bounded_physical_tree(root, entry_limit, total_byte_limit, label):
    root = Path(root)
    try:
        root_mode = root.lstat().st_mode
    except OSError as error:
        raise CandidateConstructionError(label + "_ROOT_STAT_FAILED") from error
    if not stat.S_ISDIR(root_mode):
        raise CandidateConstructionError(label + "_ROOT_NOT_DIRECTORY")
    directories = []
    files = []
    file_observations = []
    total_size = 0
    entry_count = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = os.scandir(directory)
        except OSError as error:
            raise CandidateConstructionError(
                label + "_DIRECTORY_SCAN_FAILED"
            ) from error
        with entries:
            for entry in entries:
                entry_count += 1
                if entry_count > entry_limit:
                    raise CandidateConstructionError(
                        label + "_ENTRY_LIMIT_EXCEEDED"
                    )
                path = Path(entry.path)
                try:
                    observed = entry.stat(follow_symlinks=False)
                except OSError as error:
                    raise CandidateConstructionError(
                        label + "_ENTRY_STAT_FAILED"
                    ) from error
                if stat.S_ISDIR(observed.st_mode):
                    directories.append(path)
                    pending.append(path)
                elif stat.S_ISREG(observed.st_mode):
                    if observed.st_size < 0:
                        raise CandidateConstructionError(
                            label + "_FILE_SIZE_INVALID"
                        )
                    total_size += observed.st_size
                    if total_size > total_byte_limit:
                        raise CandidateConstructionError(
                            label + "_TOTAL_BYTE_LIMIT_EXCEEDED"
                        )
                    files.append(path)
                    file_observations.append(
                        {
                            "relative_path": path.relative_to(root).as_posix(),
                            "size_bytes": observed.st_size,
                            "mode": observed.st_mode,
                            "link_count": observed.st_nlink,
                        }
                    )
                else:
                    raise CandidateConstructionError(
                        label + "_NONPHYSICAL_ENTRY",
                        path.relative_to(root).as_posix(),
                    )
    directories.sort(key=lambda item: item.relative_to(root).as_posix())
    files.sort(key=lambda item: item.relative_to(root).as_posix())
    file_observations.sort(key=lambda item: item["relative_path"])
    return {
        "directories": directories,
        "files": files,
        "file_observations": file_observations,
        "entry_count": entry_count,
        "total_file_size_bytes": total_size,
    }


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
            physical_relative_object_kind(
                candidate, Path("pyproject.toml")
            )
            == "REGULAR_FILE"
            and physical_relative_object_kind(
                candidate, Path("src/heterodiff")
            )
            == "DIRECTORY"
            and physical_relative_object_kind(
                candidate, PROFILE_RELATIVE_PATH
            )
            == "REGULAR_FILE"
            and physical_relative_object_kind(
                candidate, V2_REVIEW_RELATIVE_PATH
            )
            == "REGULAR_FILE"
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


def physical_relative_object_kind(root, relative_path):
    root = Path(root)
    relative_path = Path(relative_path)
    if relative_path.is_absolute() or any(
        part in ("", ".", "..") for part in relative_path.parts
    ):
        return "INVALID"
    try:
        root_mode = root.lstat().st_mode
    except OSError:
        return "UNAVAILABLE"
    if not stat.S_ISDIR(root_mode):
        return "INVALID"
    current = root
    for ordinal, part in enumerate(relative_path.parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return "ABSENT"
        except OSError:
            return "UNAVAILABLE"
        is_last = ordinal == len(relative_path.parts) - 1
        if not is_last:
            if not stat.S_ISDIR(mode):
                return "INVALID"
            continue
        if stat.S_ISREG(mode):
            return "REGULAR_FILE"
        if stat.S_ISDIR(mode):
            return "DIRECTORY"
        if stat.S_ISLNK(mode):
            return "SYMLINK"
        return "OTHER"
    return "DIRECTORY"


def validate_profile(profile_path, raw):
    if type(raw) is not bytes or len(raw) > SOURCE_FILE_BYTE_LIMIT:
        raise CandidateConstructionError("PROFILE_PAYLOAD_NOT_BOUNDED_BYTES")
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
        "exact_scope": "WHEEL_SELECTION_RUNTIME_ABI_FIELDS_ONLY",
        "whole_native_profile_exact_claimed": False,
        "unobserved_native_profile_target_fields": [
            "cloud_provider",
            "compute_mode",
            "cpu_only",
            "databricks_runtime_release",
            "gpu_enabled",
            "machine_learning_runtime",
            "photon_enabled",
            "runtime_engine",
            "service",
            "spark_version",
        ],
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


def candidate_chunk_leaf_name(ordinal):
    if type(ordinal) is not int or not 0 <= ordinal < PAYLOAD_CHUNK_LIMIT:
        raise CandidateConstructionError("UC_PAYLOAD_CHUNK_ORDINAL_INVALID")
    return f"{CANDIDATE_ID}.payload-{ordinal:04d}.bin"


ATTEMPT_INTENT_LEAF_NAME = f"{CANDIDATE_ID}.attempt-intent.json"
PAYLOAD_MANIFEST_LEAF_NAME = f"{CANDIDATE_ID}.payload-manifest.json"
SUCCESS_RECEIPT_LEAF_NAME = f"{CANDIDATE_ID}.construction-receipt.json"
FAILURE_RECEIPT_LEAF_NAME = (
    f"{CANDIDATE_ID}.construction-failure-receipt.json"
)


def reserved_candidate_leaf_names():
    return (
        ATTEMPT_INTENT_LEAF_NAME,
        *(candidate_chunk_leaf_name(i) for i in range(PAYLOAD_CHUNK_LIMIT)),
        PAYLOAD_MANIFEST_LEAF_NAME,
        SUCCESS_RECEIPT_LEAF_NAME,
        FAILURE_RECEIPT_LEAF_NAME,
    )


def validate_destination(value):
    errors = []
    expected_prefix = CANDIDATE_PREFIX.as_posix()
    details = {
        "configured": True,
        "path": expected_prefix,
        "candidate_id": CANDIDATE_ID,
        "parent": CANDIDATE_PARENT.as_posix(),
        "parent_kind": None,
        "virtual_prefix_kind": None,
        "reserved_leaf_count": len(reserved_candidate_leaf_names()),
        "all_reserved_leaves_absent": False,
        "colliding_reserved_leaf_names": [],
    }
    if value != expected_prefix:
        errors.append("UC_CANDIDATE_PREFIX_NOT_EXACT")
        return details, errors
    pure_parent = PurePosixPath(CANDIDATE_PARENT.as_posix())
    if (
        not pure_parent.is_absolute()
        or len(pure_parent.parts) != 5
        or pure_parent.parts[:2] != ("/", "Volumes")
        or any(part in ("", ".", "..") for part in pure_parent.parts[2:])
    ):
        errors.append("UC_CANDIDATE_PARENT_PATH_NOT_EXACT_VOLUME_ROOT")
        return details, errors
    try:
        details["parent_kind"] = object_kind(CANDIDATE_PARENT)
        details["virtual_prefix_kind"] = object_kind(CANDIDATE_PREFIX)
        collisions = []
        for name in reserved_candidate_leaf_names():
            if object_kind(CANDIDATE_PARENT / name) != "ABSENT":
                collisions.append(name)
        details["colliding_reserved_leaf_names"] = collisions
        details["all_reserved_leaves_absent"] = (
            details["virtual_prefix_kind"] == "ABSENT" and not collisions
        )
    except OSError as error:
        errors.append("UC_CANDIDATE_NAMESPACE_VISIBILITY_FAILED")
        details["visibility_error"] = type(error).__name__
        return details, errors
    if details["parent_kind"] != "DIRECTORY":
        errors.append("UC_CANDIDATE_PARENT_MUST_BE_DIRECTORY")
    if details["virtual_prefix_kind"] != "ABSENT":
        errors.append("UC_CANDIDATE_VIRTUAL_PREFIX_MUST_BE_ABSENT")
    if details["colliding_reserved_leaf_names"]:
        errors.append("UC_CANDIDATE_RESERVED_NAMESPACE_NOT_EMPTY")
    return details, errors


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


def candidate_review_package(
    source_manifest,
    builder_source_binding,
    launcher_source_binding,
    source_git_binding,
    profile_validation,
    review_binding,
    probe_review_binding,
    probe_outcome_binding,
):
    projection = {
        "schema_version": "heterodiff-b08-n1-candidate-003-review-package-v1",
        "builder_source_binding": builder_source_binding,
        "launcher_source_binding": launcher_source_binding,
        "project_source_manifest_sha256": source_manifest["record_sha256"],
        "project_source_file_count": len(source_manifest["files"]),
        "source_git_binding": source_git_binding,
        "native_profile_file_sha256": profile_validation["file_sha256"],
        "native_profile_semantic_sha256": profile_validation[
            "semantic_sha256"
        ],
        "native_target_review_sha256": review_binding["sha256"],
        "uc_volume_probe_review_sha256": probe_review_binding["sha256"],
        "uc_volume_probe_outcome_sha256": probe_outcome_binding["sha256"],
    }
    return {
        **projection,
        "record_sha256": sha256_bytes(
            REVIEW_PACKAGE_DOMAIN + canonical_json_bytes(projection)
        ),
    }


def parse_review_package_authorization(value):
    if type(value) is not str or not value.startswith(
        REVIEW_AUTHORIZATION_PREFIX
    ):
        return None
    digest = value[len(REVIEW_AUTHORIZATION_PREFIX):]
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        return None
    return digest


def validate_hash_first_launch_evidence(
    evidence,
    builder_source_binding,
    launcher_source_binding,
):
    required_keys = {
        "schema_version",
        "builder_relative_path",
        "operator_expected_builder_sha256",
        "executed_payload_sha256",
        "executed_payload_size_bytes",
        "launcher_relative_path",
        "launcher_source_sha256",
        "launcher_source_size_bytes",
        "same_in_memory_payload_compiled_and_executed",
    }
    if type(evidence) is not dict:
        return None, ["HASH_FIRST_LAUNCH_EVIDENCE_REQUIRED"]
    if set(evidence) != required_keys:
        return None, ["HASH_FIRST_LAUNCH_EVIDENCE_SHAPE_INVALID"]
    expected = {
        "schema_version": HASH_FIRST_LAUNCH_SCHEMA,
        "builder_relative_path": BUILDER_NOTEBOOK_RELATIVE_PATH.as_posix(),
        "operator_expected_builder_sha256": builder_source_binding["sha256"],
        "executed_payload_sha256": builder_source_binding["sha256"],
        "executed_payload_size_bytes": builder_source_binding["size_bytes"],
        "launcher_relative_path": LAUNCHER_NOTEBOOK_RELATIVE_PATH.as_posix(),
        "launcher_source_sha256": launcher_source_binding["sha256"],
        "launcher_source_size_bytes": launcher_source_binding["size_bytes"],
        "same_in_memory_payload_compiled_and_executed": True,
    }
    if evidence != expected:
        return None, ["HASH_FIRST_LAUNCH_EVIDENCE_BINDING_MISMATCH"]
    return immutable_json_snapshot(expected), []


def preflight():
    repo_root = locate_repo_root()
    profile_path = repo_root / PROFILE_RELATIVE_PATH
    _, profile_payload, _ = read_physical_source_bytes(
        profile_path, repo_root
    )
    profile, profile_validation = validate_profile(
        profile_path, profile_payload
    )
    review_binding = regular_file_binding(
        repo_root,
        V2_REVIEW_RELATIVE_PATH,
        "V2_INDEPENDENT_REVIEW",
    )
    probe_review_binding = regular_file_binding(
        repo_root,
        PROBE_REVIEW_RELATIVE_PATH,
        "UC_VOLUME_PROBE_INDEPENDENT_REVIEW",
    )
    probe_outcome_binding = regular_file_binding(
        repo_root,
        PROBE_OUTCOME_RELATIVE_PATH,
        "UC_VOLUME_PROBE_001_OUTCOME",
    )
    source_manifest = project_source_manifest(repo_root)
    builder_source_binding = regular_file_binding(
        repo_root,
        BUILDER_NOTEBOOK_RELATIVE_PATH,
        "BUILDER_NOTEBOOK",
    )
    launcher_source_binding = regular_file_binding(
        repo_root,
        LAUNCHER_NOTEBOOK_RELATIVE_PATH,
        "HASH_FIRST_LAUNCHER_NOTEBOOK",
    )
    authorized_review_package_sha256 = parse_review_package_authorization(
        REVIEW_PACKAGE_AUTHORIZATION
    )
    hash_first_launch_evidence, hash_first_launch_errors = (
        validate_hash_first_launch_evidence(
            _HASH_FIRST_LAUNCH_EVIDENCE,
            builder_source_binding,
            launcher_source_binding,
        )
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
    source_git_preflight_journal = []
    try:
        (
            source_git_revision,
            source_git_epoch,
            source_git_provenance,
        ) = git_identity(
            repo_root,
            source_git_preflight_journal,
            read_only_tool_environment(),
            PRIMARY_SIMPLE_INDEX_URL,
            PYTORCH_CPU_SIMPLE_INDEX_URL,
            None,
            None,
            source_manifest,
            builder_source_binding,
            launcher_source_binding,
        )
    except (CandidateConstructionError, OSError) as git_error:
        source_git_preflight = {
            "exact": False,
            "revision": None,
            "source_date_epoch": None,
            "provenance": None,
            "error_code": (
                git_error.code
                if isinstance(git_error, CandidateConstructionError)
                else "SOURCE_GIT_PREFLIGHT_FILESYSTEM_FAILED"
            ),
            "error_detail": (
                git_error.detail
                if isinstance(git_error, CandidateConstructionError)
                else type(git_error).__name__
            ),
            "command_journal": source_git_preflight_journal,
        }
        errors.append("BOUND_SOURCE_GIT_PREFLIGHT_FAILED")
    else:
        source_git_preflight = {
            "exact": True,
            "revision": source_git_revision,
            "source_date_epoch": source_git_epoch,
            "provenance": source_git_provenance,
            "error_code": None,
            "error_detail": None,
            "command_journal": source_git_preflight_journal,
        }
    if source_git_preflight["exact"]:
        source_git_review_binding = {
            key: source_git_preflight[key]
            for key in ("revision", "source_date_epoch", "provenance")
        }
        review_package = candidate_review_package(
            source_manifest,
            builder_source_binding,
            launcher_source_binding,
            source_git_review_binding,
            profile_validation,
            review_binding,
            probe_review_binding,
            probe_outcome_binding,
        )
    else:
        review_package = None
    if (
        REVIEW_PACKAGE_AUTHORIZATION != "NOT_AUTHORIZED"
        and authorized_review_package_sha256 is None
    ):
        errors.append("REVIEW_PACKAGE_AUTHORIZATION_FORMAT_INVALID")
    if (
        authorized_review_package_sha256 is not None
        and (
            review_package is None
            or authorized_review_package_sha256
            != review_package["record_sha256"]
        )
    ):
        errors.append("REVIEW_PACKAGE_AUTHORIZATION_SHA256_MISMATCH")
    if _HASH_FIRST_LAUNCH_EVIDENCE is not None:
        errors.extend(hash_first_launch_errors)
    if review_binding["sha256"] != EXPECTED_V2_REVIEW_FILE_SHA256:
        errors.append("V2_INDEPENDENT_REVIEW_SHA256_MISMATCH")
    if (
        probe_review_binding["sha256"]
        != EXPECTED_PROBE_REVIEW_FILE_SHA256
    ):
        errors.append("UC_VOLUME_PROBE_REVIEW_SHA256_MISMATCH")
    if (
        probe_outcome_binding["sha256"]
        != EXPECTED_PROBE_OUTCOME_FILE_SHA256
    ):
        errors.append("UC_VOLUME_PROBE_OUTCOME_SHA256_MISMATCH")
    required_features = {
        "o_cloexec": hasattr(os, "O_CLOEXEC"),
        "o_directory": hasattr(os, "O_DIRECTORY"),
        "o_nofollow": hasattr(os, "O_NOFOLLOW"),
        "open_dir_fd": os.open in os.supports_dir_fd,
    }
    if not all(required_features.values()):
        errors.append("UC_REQUIRED_EXCLUSIVE_CREATE_PRIMITIVE_UNAVAILABLE")
    required_inputs = []
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
    if authorized_review_package_sha256 is None:
        required_inputs.append(
            "REVIEW_PACKAGE_AUTHORIZATION="
            + REVIEW_AUTHORIZATION_PREFIX
            + "<independently-reviewed-package-sha256>"
        )
    if hash_first_launch_evidence is None:
        required_inputs.append(
            "RUN_THROUGH_HASH_FIRST_LAUNCHER_WITH_REVIEWED_BUILDER_SHA256"
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
        and source_git_preflight["exact"]
        and not errors
        and not required_inputs
        and EXECUTION_MODE == CONSTRUCT_MODE
        and NETWORK_AND_BUILD_AUTHORIZED is True
        and ONE_SHOT_ACKNOWLEDGEMENT == ACKNOWLEDGEMENT_TEXT
        and review_package is not None
        and authorized_review_package_sha256
        == review_package["record_sha256"]
        and hash_first_launch_evidence is not None
    )
    if construction_authorized:
        decision = "PROCEED_ONE_UC_NATIVE_ISOLATED_NETWORK_BUILD_CANDIDATE_003"
    elif runtime is not None and not runtime["exact"]:
        decision = "HOLD_RUNTIME_PROFILE_MISMATCH_REQUIRES_REVIEW"
    else:
        decision = "HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE"
    return {
        "schema_version": NOTEBOOK_SCHEMA,
        "scope": "DATA_FREE_UC_NATIVE_OVERLAY_CANDIDATE_003_CONSTRUCTION_ONLY",
        "decision": decision,
        "construction_authorized": construction_authorized,
        "repo_root": repo_root,
        "profile": profile,
        "profile_validation": profile_validation,
        "v2_independent_review_binding": review_binding,
        "uc_volume_probe_review_binding": probe_review_binding,
        "uc_volume_probe_outcome_binding": probe_outcome_binding,
        "source_manifest": source_manifest,
        "builder_source_binding": builder_source_binding,
        "launcher_source_binding": launcher_source_binding,
        "review_package": review_package,
        "source_git_preflight": source_git_preflight,
        "authorized_review_package_sha256": (
            authorized_review_package_sha256
        ),
        "hash_first_launch_evidence": hash_first_launch_evidence,
        "required_uc_features": required_features,
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
            "direct_external_network_or_contact_accessed": False,
            "read_only_local_git_child_processes_executed": True,
            "databricks_managed_uc_metadata_io_may_have_been_performed": True,
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
    root = Path(root)
    path = Path(path)
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise CandidateConstructionError("SOURCE_PATH_ESCAPES_ROOT") from error
    if physical_relative_object_kind(root, relative) != "REGULAR_FILE":
        raise CandidateConstructionError(
            "SOURCE_PATH_NOT_PHYSICAL_REGULAR_FILE", relative.as_posix()
        )
    return relative


def open_relative_regular_file_nofollow(root, relative, label):
    root = Path(root)
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or any(
        part in ("", ".", "..") for part in relative.parts
    ):
        raise CandidateConstructionError(label + "_RELATIVE_PATH_INVALID")
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    directory_descriptors = []
    try:
        try:
            current = os.open(root, directory_flags)
        except OSError as error:
            raise CandidateConstructionError(
                label + "_ROOT_OPEN_FAILED"
            ) from error
        directory_descriptors.append(current)
        for part in relative.parts[:-1]:
            try:
                current = os.open(
                    part,
                    directory_flags,
                    dir_fd=current,
                )
            except OSError as error:
                raise CandidateConstructionError(
                    label + "_ANCESTOR_OPEN_FAILED", relative.as_posix()
                ) from error
            directory_descriptors.append(current)
        try:
            return os.open(
                relative.parts[-1],
                file_flags,
                dir_fd=current,
            )
        except OSError as error:
            raise CandidateConstructionError(
                label + "_LEAF_OPEN_FAILED", relative.as_posix()
            ) from error
    finally:
        for descriptor in reversed(directory_descriptors):
            os.close(descriptor)


def read_physical_source_bytes(path, root):
    relative = require_regular_source_file(path, root)
    descriptor = open_relative_regular_file_nofollow(
        root, relative, "SOURCE_FILE"
    )
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size < 0
            or opened.st_size > SOURCE_FILE_BYTE_LIMIT
        ):
            raise CandidateConstructionError(
                "SOURCE_FILE_SIZE_OR_TYPE_INVALID", relative.as_posix()
            )
        payload = bytearray()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > SOURCE_FILE_BYTE_LIMIT:
                raise CandidateConstructionError(
                    "SOURCE_FILE_EXPANDED_PAST_LIMIT", relative.as_posix()
                )
        final = os.fstat(descriptor)
        if len(payload) != opened.st_size or final.st_size != opened.st_size:
            raise CandidateConstructionError(
                "SOURCE_FILE_SIZE_CHANGED_DURING_READ", relative.as_posix()
            )
        return relative, bytes(payload), opened.st_mode & 0o777
    finally:
        os.close(descriptor)


def enumerate_project_python_sources(repo_root):
    package_root = repo_root / "src" / "heterodiff"
    if (
        physical_relative_object_kind(repo_root, Path("src"))
        != "DIRECTORY"
        or physical_relative_object_kind(
            repo_root, Path("src/heterodiff")
        )
        != "DIRECTORY"
    ):
        raise CandidateConstructionError(
            "SOURCE_PACKAGE_ROOT_NOT_PHYSICAL_DIRECTORY"
        )
    sources = []
    pending = [package_root]
    entry_count = 0
    while pending:
        directory = pending.pop()
        relative_directory = directory.relative_to(repo_root)
        if (
            physical_relative_object_kind(repo_root, relative_directory)
            != "DIRECTORY"
        ):
            raise CandidateConstructionError(
                "SOURCE_TREE_DIRECTORY_NOT_PHYSICAL",
                relative_directory.as_posix(),
            )
        try:
            entries = os.scandir(directory)
        except OSError as error:
            raise CandidateConstructionError(
                "SOURCE_TREE_DIRECTORY_SCAN_FAILED",
                relative_directory.as_posix(),
            ) from error
        with entries:
            for entry in entries:
                entry_count += 1
                if entry_count > SOURCE_TREE_ENTRY_LIMIT:
                    raise CandidateConstructionError(
                        "SOURCE_TREE_ENTRY_LIMIT_EXCEEDED"
                    )
                child = Path(entry.path)
                relative_child = child.relative_to(repo_root)
                try:
                    mode = entry.stat(follow_symlinks=False).st_mode
                except OSError as error:
                    raise CandidateConstructionError(
                        "SOURCE_TREE_ENTRY_STAT_FAILED",
                        relative_child.as_posix(),
                    ) from error
                if stat.S_ISDIR(mode):
                    pending.append(child)
                elif stat.S_ISREG(mode):
                    if child.suffix == ".py":
                        sources.append(child)
                else:
                    raise CandidateConstructionError(
                        "SOURCE_TREE_NONPHYSICAL_ENTRY",
                        relative_child.as_posix(),
                    )
    return sorted(sources, key=lambda item: item.relative_to(repo_root).as_posix())


def project_source_manifest(repo_root):
    sources = [repo_root / "pyproject.toml", repo_root / "README.md"]
    sources.extend(enumerate_project_python_sources(repo_root))
    records = []
    total_size = 0
    for path in sources:
        relative, payload, observed_mode = read_physical_source_bytes(
            path, repo_root
        )
        size = len(payload)
        total_size += size
        if total_size > SOURCE_TOTAL_BYTE_LIMIT:
            raise CandidateConstructionError(
                "SOURCE_TOTAL_BYTE_LIMIT_EXCEEDED"
            )
        digest = sha256_bytes(payload)
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
    try:
        relative, payload, observed_mode = read_physical_source_bytes(
            path, repo_root
        )
    except CandidateConstructionError as error:
        raise CandidateConstructionError(
            label + "_NOT_PHYSICAL_REGULAR_FILE",
            relative_path.as_posix(),
        ) from error
    if relative != relative_path:
        raise CandidateConstructionError(label + "_RELATIVE_PATH_MISMATCH")
    digest = sha256_bytes(payload)
    size = len(payload)
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
        relative, payload, observed_mode = read_physical_source_bytes(
            source, repo_root
        )
        canonical_mode = 0o755 if observed_mode & 0o111 else 0o644
        if (
            relative.as_posix() != record["relative_path"]
            or sha256_bytes(payload) != record["sha256"]
            or len(payload) != record["size_bytes"]
            or format(canonical_mode, "04o") != record["mode_octal"]
        ):
            raise CandidateConstructionError(
                "SOURCE_CHANGED_BEFORE_STAGING_COPY"
            )
        target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        if object_kind(target) != "ABSENT":
            raise CandidateConstructionError("STAGING_SOURCE_COLLISION")
        write_local_exclusive(target, payload)
        os.chmod(target, int(record["mode_octal"], 8))
        copied_sha256, copied_size = sha256_file(target)
        if (
            copied_sha256 != record["sha256"]
            or copied_size != record["size_bytes"]
        ):
            raise CandidateConstructionError("STAGING_SOURCE_COPY_MISMATCH")
        if format(target.stat().st_mode & 0o777, "04o") != record["mode_octal"]:
            raise CandidateConstructionError("STAGING_SOURCE_MODE_MISMATCH")


def runtime_path_replacements(cwd):
    pairs = [
        (str(Path(cwd).resolve()), "<COMMAND_CWD>"),
        (str(Path(sys.executable).resolve()), "<HOST_PYTHON>"),
        (str(Path(sys.prefix).resolve()), "<HOST_PREFIX>"),
    ]
    unique = {}
    for source, target in pairs:
        if source and source not in ("/", "."):
            unique[source] = target
    return sorted(unique.items(), key=lambda item: len(item[0]), reverse=True)


def sanitize_runtime_text(value, cwd):
    result = value
    for source, target in runtime_path_replacements(cwd):
        result = result.replace(source, target)
    return result


def sanitized_command(argv, primary_url, torch_url, cwd=None):
    cwd = Path.cwd() if cwd is None else cwd
    result = []
    for value in argv:
        if value == primary_url:
            result.append("<PRIMARY_INDEX_URL>")
        elif value == torch_url:
            result.append("<PYTORCH_CPU_INDEX_URL>")
        else:
            result.append(sanitize_runtime_text(str(value), cwd))
    return result


def bounded_failure_stream_evidence(
    payload,
    observed_bytes,
    capture_complete,
    cwd,
    primary_url,
    torch_url,
):
    if payload is None:
        raw = b""
    elif isinstance(payload, bytes):
        raw = payload
    elif isinstance(payload, str):
        raw = payload.encode("utf-8", errors="replace")
    else:
        raw = bytes(payload)
    sanitized = raw.decode("utf-8", errors="replace")
    sanitized = sanitized.replace(primary_url, "<PRIMARY_INDEX_URL>")
    sanitized = sanitized.replace(torch_url, "<PYTORCH_CPU_INDEX_URL>")
    sanitized = sanitize_runtime_text(sanitized, cwd)
    sanitized = re.sub(
        r"(https?://)[^/@\s:]+:[^/@\s]+@",
        r"\1<REDACTED_CREDENTIALS>@",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized_bytes = sanitized.encode("utf-8", errors="replace")
    tail_bytes = sanitized_bytes[-TOOL_FAILURE_DIAGNOSTIC_TAIL_BYTE_LIMIT:]
    tail_text = tail_bytes.decode("utf-8", errors="ignore")
    return {
        "captured_byte_count": len(raw),
        "captured_sha256": sha256_bytes(raw),
        "observed_byte_count_before_termination": max(
            len(raw), int(observed_bytes)
        ),
        "capture_complete_through_process_termination": bool(
            capture_complete
        ),
        "sanitized_tail_byte_limit": (
            TOOL_FAILURE_DIAGNOSTIC_TAIL_BYTE_LIMIT
        ),
        "sanitized_tail_utf8": tail_text,
        "runtime_paths_and_exact_index_urls_sanitized": True,
    }


def subprocess_failure_diagnostics(
    stdout,
    stderr,
    observed_stream_bytes,
    capture_complete,
    cwd,
    primary_url,
    torch_url,
):
    observed = observed_stream_bytes or {}
    return {
        "stdout": bounded_failure_stream_evidence(
            stdout,
            observed.get("stdout", 0),
            capture_complete,
            cwd,
            primary_url,
            torch_url,
        ),
        "stderr": bounded_failure_stream_evidence(
            stderr,
            observed.get("stderr", 0),
            capture_complete,
            cwd,
            primary_url,
            torch_url,
        ),
    }


def bounded_failure_detail(value, cwd, primary_url, torch_url):
    if value is None:
        return None
    raw = str(value).encode("utf-8", errors="replace")
    sanitized = bounded_failure_stream_evidence(
        raw,
        len(raw),
        True,
        cwd,
        primary_url,
        torch_url,
    )["sanitized_tail_utf8"]
    bounded = sanitized.encode("utf-8", errors="replace")[
        -TOOL_FAILURE_DETAIL_BYTE_LIMIT:
    ]
    return bounded.decode("utf-8", errors="ignore")


def terminate_process_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (AttributeError, OSError):
        if process.poll() is None:
            process.kill()


def run_subprocess_bounded(argv, cwd, environment):
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    observed_stream_bytes = {"stdout": 0, "stderr": 0}
    overflows = []
    reader_errors = []
    process = None
    threads = []
    timed_out = False

    def read_stream(label, stream):
        try:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    return
                observed_stream_bytes[label] += len(chunk)
                remaining = TOOL_OUTPUT_STREAM_BYTE_LIMIT - len(buffers[label])
                if len(chunk) > remaining:
                    if remaining > 0:
                        buffers[label].extend(chunk[:remaining])
                    overflows.append(label)
                    return
                buffers[label].extend(chunk)
        except BaseException as error:
            reader_errors.append((label, error))

    try:
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            start_new_session=True,
            bufsize=0,
        )
        threads = [
            threading.Thread(
                target=read_stream,
                args=(label, stream),
                daemon=True,
            )
            for label, stream in (
                ("stdout", process.stdout),
                ("stderr", process.stderr),
            )
        ]
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + TOOL_TIMEOUT_SECONDS
        while process.poll() is None:
            if reader_errors:
                terminate_process_group(process)
                break
            if overflows:
                terminate_process_group(process)
                break
            if time.monotonic() >= deadline:
                timed_out = True
                terminate_process_group(process)
                break
            time.sleep(0.05)
        try:
            returncode = process.wait(timeout=TOOL_REAP_SECONDS)
        except subprocess.TimeoutExpired:
            terminate_process_group(process)
            returncode = process.wait(timeout=TOOL_REAP_SECONDS)
        for thread in threads:
            thread.join(timeout=TOOL_REAP_SECONDS)
        if any(thread.is_alive() for thread in threads):
            terminate_process_group(process)
            error = CandidateConstructionError(
                "TOOL_OUTPUT_READER_DID_NOT_QUIESCE",
                stdout=bytes(buffers["stdout"]),
                stderr=bytes(buffers["stderr"]),
                output_capture_complete=False,
            )
            error.observed_stream_bytes = dict(observed_stream_bytes)
            raise error
    except BaseException as raw_error:
        if process is not None:
            try:
                terminate_process_group(process)
            except BaseException:
                pass
            try:
                process.wait(timeout=TOOL_REAP_SECONDS)
            except BaseException:
                pass
        for thread in threads:
            try:
                thread.join(timeout=TOOL_REAP_SECONDS)
            except BaseException:
                pass
        if isinstance(raw_error, CandidateConstructionError):
            if raw_error.stdout is None:
                raw_error.stdout = bytes(buffers["stdout"])
            if raw_error.stderr is None:
                raw_error.stderr = bytes(buffers["stderr"])
            if raw_error.output_capture_complete is None:
                raw_error.output_capture_complete = False
            raw_error.observed_stream_bytes = dict(observed_stream_bytes)
            raise
        if process is None and isinstance(raw_error, OSError):
            raise
        wrapped = CandidateConstructionError(
            "TOOL_SUBPROCESS_SUPERVISOR_FAILED",
            type(raw_error).__name__,
            stdout=bytes(buffers["stdout"]),
            stderr=bytes(buffers["stderr"]),
            output_capture_complete=False,
        )
        wrapped.observed_stream_bytes = dict(observed_stream_bytes)
        raise wrapped from raw_error
    finally:
        if process is not None:
            for stream in (process.stdout, process.stderr):
                try:
                    stream.close()
                except BaseException:
                    pass
    if timed_out:
        error = subprocess.TimeoutExpired(
            argv,
            TOOL_TIMEOUT_SECONDS,
            output=bytes(buffers["stdout"]),
            stderr=bytes(buffers["stderr"]),
        )
        error.observed_stream_bytes = dict(observed_stream_bytes)
        error.output_capture_complete = True
        raise error
    if overflows:
        error = CandidateConstructionError(
            "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
            sorted(set(overflows))[0],
            stdout=bytes(buffers["stdout"]),
            stderr=bytes(buffers["stderr"]),
            output_capture_complete=False,
        )
        error.observed_stream_bytes = dict(observed_stream_bytes)
        raise error
    if reader_errors:
        label, error = reader_errors[0]
        wrapped = CandidateConstructionError(
            "TOOL_OUTPUT_READER_FAILED",
            f"{label}:{type(error).__name__}",
            stdout=bytes(buffers["stdout"]),
            stderr=bytes(buffers["stderr"]),
            output_capture_complete=False,
        )
        wrapped.observed_stream_bytes = dict(observed_stream_bytes)
        raise wrapped from error
    return subprocess.CompletedProcess(
        argv,
        returncode,
        bytes(buffers["stdout"]),
        bytes(buffers["stderr"]),
    )


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
    if len(journal) >= TOOL_COMMAND_LIMIT:
        raise CandidateConstructionError(
            "TOOL_COMMAND_LIMIT_EXCEEDED", str(TOOL_COMMAND_LIMIT)
        )
    if attempt_state is not None:
        if attempt_state.get("durable_intent_committed") is not True:
            raise CandidateConstructionError(
                "DURABLE_INTENT_REQUIRED_BEFORE_NETWORK_OR_BUILD",
                step,
                telemetry=immutable_json_snapshot(attempt_state),
            )
        if durable_attempt is None:
            raise CandidateConstructionError(
                "DURABLE_INTENT_CUSTODY_REQUIRED_BEFORE_TOOL_STEP",
                step,
                telemetry=immutable_json_snapshot(attempt_state),
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
                telemetry=immutable_json_snapshot(attempt_state),
            ) from error
        for flag in phase_flags:
            attempt_state[flag] = True
        attempt_state["last_started_step"] = step
    try:
        completed = run_subprocess_bounded(argv, cwd, environment)
    except (
        CandidateConstructionError,
        OSError,
        subprocess.TimeoutExpired,
    ) as error:
        execution_error = (
            error.code
            if isinstance(error, CandidateConstructionError)
            else type(error).__name__
        )
        execution_error_detail = (
            bounded_failure_detail(
                error.detail,
                cwd,
                primary_url,
                torch_url,
            )
            if isinstance(error, CandidateConstructionError)
            else None
        )
        stdout = (
            error.stdout
            if isinstance(error, CandidateConstructionError)
            else getattr(error, "output", None)
        )
        stderr = getattr(error, "stderr", None)
        failure_diagnostics = subprocess_failure_diagnostics(
            stdout,
            stderr,
            getattr(error, "observed_stream_bytes", None),
            getattr(error, "output_capture_complete", False),
            cwd,
            primary_url,
            torch_url,
        )
        entry = {
            "step": step,
            "argv": sanitized_command(argv, primary_url, torch_url, cwd),
            "returncode": None,
            "execution_error": execution_error,
            "execution_error_detail": execution_error_detail,
            "failure_diagnostics": failure_diagnostics,
            "stdout_and_stderr_persisted": (
                "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY"
            ),
        }
        journal.append(entry)
        if attempt_state is not None:
            attempt_state["command_journal"] = list(journal)
            attempt_state["last_failed_step"] = step
        wrapped_detail = f"{step}:{execution_error}"
        if execution_error_detail is not None:
            wrapped_detail += f":{execution_error_detail}"
        raise CandidateConstructionError(
            (
                error.code
                if isinstance(error, CandidateConstructionError)
                else "TOOL_STEP_EXECUTION_FAILED"
            ),
            wrapped_detail,
            telemetry=(
                None
                if attempt_state is None
                else immutable_json_snapshot(attempt_state)
            ),
        ) from error
    entry = {
        "step": step,
        "argv": sanitized_command(argv, primary_url, torch_url, cwd),
        "returncode": completed.returncode,
        "stdout_and_stderr_persisted": False,
        "output_excluded_as_nondeterministic_tool_telemetry": True,
    }
    journal.append(entry)
    if attempt_state is not None:
        attempt_state["command_journal"] = list(journal)
    if completed.returncode != 0:
        entry["failure_diagnostics"] = subprocess_failure_diagnostics(
            completed.stdout,
            completed.stderr,
            {
                "stdout": len(completed.stdout),
                "stderr": len(completed.stderr),
            },
            True,
            cwd,
            primary_url,
            torch_url,
        )
        entry["stdout_and_stderr_persisted"] = (
            "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY"
        )
        entry["output_excluded_as_nondeterministic_tool_telemetry"] = False
        if attempt_state is not None:
            attempt_state["command_journal"] = list(journal)
        if attempt_state is not None:
            attempt_state["last_failed_step"] = step
        raise CandidateConstructionError(
            "TOOL_STEP_FAILED",
            f"{step}:returncode={completed.returncode}",
            telemetry=(
                None
                if attempt_state is None
                else immutable_json_snapshot(attempt_state)
            ),
        )
    if attempt_state is not None:
        attempt_state["last_completed_step"] = step
    return completed.stdout


def isolated_environment(
    venv_root,
    source_date_epoch,
    deterministic_environment,
    tool_temp_root,
):
    bin_path = venv_root / "bin"
    tool_temp_root = Path(tool_temp_root).resolve()
    try:
        tool_temp_root.relative_to(Path(venv_root).resolve().parent)
    except ValueError as error:
        raise CandidateConstructionError(
            "TOOL_TEMP_ROOT_ESCAPES_STAGING"
        ) from error
    if object_kind(tool_temp_root) != "DIRECTORY":
        raise CandidateConstructionError("TOOL_TEMP_ROOT_NOT_DIRECTORY")
    environment = dict(deterministic_environment)
    environment.update({
        "PATH": f"{bin_path}:/usr/bin:/bin",
        "HOME": str(tool_temp_root),
        "NETRC": os.devnull,
        "XDG_CACHE_HOME": str(tool_temp_root),
        "XDG_CONFIG_HOME": str(tool_temp_root),
        "TMPDIR": str(tool_temp_root),
        "TMP": str(tool_temp_root),
        "TEMP": str(tool_temp_root),
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
    ensurepip_origin = None
    if ensurepip_spec is not None and ensurepip_spec.origin is not None:
        if ensurepip_spec.origin in ("built-in", "frozen"):
            ensurepip_origin = {
                "kind": ensurepip_spec.origin.upper().replace("-", "_"),
                "relative_to_host_prefix": None,
            }
        else:
            try:
                relative_origin = Path(ensurepip_spec.origin).resolve().relative_to(
                    Path(sys.prefix).resolve()
                )
            except (OSError, ValueError):
                ensurepip_origin = {
                    "kind": "OUTSIDE_HOST_PREFIX",
                    "relative_to_host_prefix": None,
                }
            else:
                ensurepip_origin = {
                    "kind": "HOST_PREFIX_RELATIVE",
                    "relative_to_host_prefix": relative_origin.as_posix(),
                }
    return {
        "method": "BOUND_HOST_PIP_INSTALLS_INSPECTED_PINNED_WHEEL",
        "required_pip_version": required_bootstrap_pip_version(),
        "ensurepip_observation": {
            "available": ensurepip_spec is not None,
            "origin_projection": ensurepip_origin,
            "absolute_origin_persisted": False,
        },
    }


def preflight_zip_central_directory(path, artifact_size, source_handle=None):
    path = Path(path)

    def read_exact_range(offset, length):
        if offset < 0 or length < 0 or offset + length > artifact_size:
            raise CandidateConstructionError(
                "WHEEL_RANGE_READ_OUT_OF_BOUNDS", path.name
            )
        owned_descriptor = None
        if source_handle is None:
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
            try:
                owned_descriptor = os.open(path, flags)
            except OSError as error:
                raise CandidateConstructionError(
                    "WHEEL_RANGE_OPEN_FAILED", path.name
                ) from error
            descriptor = owned_descriptor
        else:
            descriptor = source_handle.fileno()
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_size != artifact_size
            ):
                raise CandidateConstructionError(
                    "WHEEL_RANGE_SOURCE_BINDING_CHANGED", path.name
                )
            os.lseek(descriptor, offset, os.SEEK_SET)
            payload = bytearray()
            while len(payload) < length:
                chunk = os.read(descriptor, length - len(payload))
                if not chunk:
                    break
                payload.extend(chunk)
            final = os.fstat(descriptor)
            if (
                len(payload) != length
                or final.st_size != artifact_size
            ):
                raise CandidateConstructionError(
                    "WHEEL_RANGE_READ_INCOMPLETE", path.name
                )
            return bytes(payload)
        finally:
            if owned_descriptor is not None:
                os.close(owned_descriptor)

    if artifact_size < 22:
        raise CandidateConstructionError("WHEEL_EOCD_UNAVAILABLE", path.name)
    tail_size = min(artifact_size, 22 + 65_535)
    tail = read_exact_range(artifact_size - tail_size, tail_size)
    signature = b"PK\x05\x06"
    search_end = len(tail)
    eocd_relative = -1
    while search_end >= 0:
        candidate = tail.rfind(signature, 0, search_end)
        if candidate < 0:
            break
        if candidate + 22 <= len(tail):
            comment_size = struct.unpack_from("<H", tail, candidate + 20)[0]
            if candidate + 22 + comment_size == len(tail):
                eocd_relative = candidate
                break
        search_end = candidate
    if eocd_relative < 0:
        raise CandidateConstructionError("WHEEL_EOCD_INVALID", path.name)
    (
        _,
        disk_number,
        central_directory_disk,
        disk_entries,
        total_entries,
        central_directory_size,
        central_directory_offset,
        _,
    ) = struct.unpack_from("<4s4H2LH", tail, eocd_relative)
    if (
        disk_number != 0
        or central_directory_disk != 0
        or disk_entries != total_entries
    ):
        raise CandidateConstructionError(
            "WHEEL_MULTIDISK_ARCHIVE_REJECTED", path.name
        )
    eocd_absolute = artifact_size - tail_size + eocd_relative
    zip64_required = (
        total_entries == 0xFFFF
        or central_directory_size == 0xFFFFFFFF
        or central_directory_offset == 0xFFFFFFFF
    )
    if zip64_required:
        locator_offset = eocd_absolute - 20
        if locator_offset < 0:
            raise CandidateConstructionError(
                "WHEEL_ZIP64_LOCATOR_UNAVAILABLE", path.name
            )
        locator = read_exact_range(locator_offset, 20)
        (
            locator_signature,
            zip64_disk,
            zip64_eocd_offset,
            disk_count,
        ) = struct.unpack("<4sLQL", locator)
        if (
            locator_signature != b"PK\x06\x07"
            or zip64_disk != 0
            or disk_count != 1
            or zip64_eocd_offset + 56 > locator_offset
        ):
            raise CandidateConstructionError(
                "WHEEL_ZIP64_LOCATOR_INVALID", path.name
            )
        zip64_eocd = read_exact_range(zip64_eocd_offset, 56)
        (
            zip64_signature,
            zip64_record_size,
            _,
            _,
            zip64_disk_number,
            zip64_central_disk,
            zip64_disk_entries,
            total_entries,
            central_directory_size,
            central_directory_offset,
        ) = struct.unpack("<4sQ2H2L4Q", zip64_eocd)
        if (
            zip64_signature != b"PK\x06\x06"
            or zip64_record_size < 44
            or zip64_disk_number != 0
            or zip64_central_disk != 0
            or zip64_disk_entries != total_entries
        ):
            raise CandidateConstructionError(
                "WHEEL_ZIP64_EOCD_INVALID", path.name
            )
        central_directory_end_limit = zip64_eocd_offset
    else:
        central_directory_end_limit = eocd_absolute
    if total_entries <= 0 or total_entries > WHEEL_MEMBER_LIMIT:
        raise CandidateConstructionError(
            "WHEEL_MEMBER_COUNT_LIMIT_EXCEEDED", path.name
        )
    if (
        central_directory_size <= 0
        or central_directory_size > WHEEL_CENTRAL_DIRECTORY_BYTE_LIMIT
        or central_directory_offset >= artifact_size
        or central_directory_offset + central_directory_size
        > central_directory_end_limit
    ):
        raise CandidateConstructionError(
            "WHEEL_CENTRAL_DIRECTORY_BOUNDS_INVALID", path.name
        )
    return {
        "entry_count": total_entries,
        "size_bytes": central_directory_size,
        "offset_bytes": central_directory_offset,
        "zip64": zip64_required,
    }


def inspect_wheel(path):
    path = Path(path)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise CandidateConstructionError(
            "WHEEL_FILE_OPEN_FAILED", path.name
        ) from error

    def hash_open_descriptor():
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size < 0
            or opened.st_size > WHEEL_FILE_BYTE_LIMIT
        ):
            raise CandidateConstructionError(
                "WHEEL_FILE_SIZE_LIMIT_EXCEEDED", path.name
            )
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        observed_size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            observed_size += len(chunk)
            if observed_size > WHEEL_FILE_BYTE_LIMIT:
                raise CandidateConstructionError(
                    "WHEEL_FILE_SIZE_LIMIT_EXCEEDED", path.name
                )
            digest.update(chunk)
        final = os.fstat(descriptor)
        if (
            observed_size != opened.st_size
            or final.st_size != opened.st_size
        ):
            raise CandidateConstructionError(
                "WHEEL_FILE_SIZE_CHANGED_DURING_READ", path.name
            )
        return digest.hexdigest(), observed_size

    source_handle = None
    archive = None
    try:
        artifact_sha256, size = hash_open_descriptor()
        if size <= 0:
            raise CandidateConstructionError("WHEEL_FILE_EMPTY", path.name)
        source_handle = os.fdopen(descriptor, "rb", closefd=False)
        central_directory = preflight_zip_central_directory(
            path, size, source_handle=source_handle
        )
        source_handle.seek(0)
        try:
            archive = zipfile.ZipFile(source_handle)
        except (OSError, zipfile.BadZipFile) as error:
            source_handle.close()
            raise CandidateConstructionError(
                "WHEEL_ARCHIVE_INVALID", path.name
            ) from error
        infos = archive.infolist()
        if (
            len(infos) > WHEEL_MEMBER_LIMIT
            or len(infos) != central_directory["entry_count"]
        ):
            raise CandidateConstructionError(
                "WHEEL_MEMBER_COUNT_LIMIT_EXCEEDED", path.name
            )
        if len({item.filename for item in infos}) != len(infos):
            raise CandidateConstructionError(
                "WHEEL_DUPLICATE_ARCHIVE_PATH", path.name
            )
        canonical_member_paths = set()
        for info in infos:
            name = info.filename
            pure = PurePosixPath(name)
            canonical_name = pure.as_posix() + ("/" if info.is_dir() else "")
            canonical_key = pure.as_posix()
            unix_file_type = stat.S_IFMT(info.external_attr >> 16)
            accepted_file_types = (
                (0, stat.S_IFDIR) if info.is_dir() else (0, stat.S_IFREG)
            )
            if (
                not name
                or canonical_key in ("", ".")
                or pure.is_absolute()
                or ".." in pure.parts
                or "\\" in name
                or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in name
                )
                or name != canonical_name
                or canonical_key in canonical_member_paths
            ):
                raise CandidateConstructionError(
                    "WHEEL_UNSAFE_ARCHIVE_PATH", path.name
                )
            if unix_file_type not in accepted_file_types:
                raise CandidateConstructionError(
                    "WHEEL_NONREGULAR_ARCHIVE_MEMBER", path.name
                )
            canonical_member_paths.add(canonical_key)
        names = [item.filename for item in infos if not item.is_dir()]
        info_by_name = {item.filename: item for item in infos}
        if not path.name.endswith(".whl"):
            raise CandidateConstructionError(
                "WHEEL_FILENAME_SUFFIX_INVALID", path.name
            )
        filename_fields = path.name[:-4].split("-")
        if len(filename_fields) == 5:
            (
                filename_distribution,
                filename_version,
                python_tag,
                abi_tag,
                platform_tag,
            ) = filename_fields
            build_tag = None
        elif len(filename_fields) == 6:
            (
                filename_distribution,
                filename_version,
                build_tag,
                python_tag,
                abi_tag,
                platform_tag,
            ) = filename_fields
        else:
            raise CandidateConstructionError(
                "WHEEL_FILENAME_FIELD_COUNT_INVALID", path.name
            )
        if (
            WHEEL_FILENAME_DISTRIBUTION.fullmatch(filename_distribution)
            is None
            or WHEEL_VERSION_TOKEN.fullmatch(filename_version) is None
            or (
                build_tag is not None
                and WHEEL_BUILD_TOKEN.fullmatch(build_tag) is None
            )
            or WHEEL_TAG_COMPONENT.fullmatch(python_tag) is None
            or WHEEL_TAG_COMPONENT.fullmatch(abi_tag) is None
            or WHEEL_TAG_COMPONENT.fullmatch(platform_tag) is None
        ):
            raise CandidateConstructionError(
                "WHEEL_FILENAME_TOKEN_INVALID", path.name
            )
        expected_dist_info = (
            f"{filename_distribution}-{filename_version}.dist-info"
        )
        total_uncompressed = 0
        for info in infos:
            if info.flag_bits & 0x1:
                raise CandidateConstructionError(
                    "WHEEL_ENCRYPTED_MEMBER_REJECTED", path.name
                )
            if info.file_size < 0 or info.file_size > WHEEL_MEMBER_BYTE_LIMIT:
                raise CandidateConstructionError(
                    "WHEEL_MEMBER_SIZE_LIMIT_EXCEEDED", path.name
                )
            if info.is_dir() and (
                info.file_size != 0 or info.compress_size != 0
            ):
                raise CandidateConstructionError(
                    "WHEEL_DIRECTORY_MEMBER_NOT_EMPTY", path.name
                )
            if not info.is_dir():
                total_uncompressed += info.file_size
                if total_uncompressed > WHEEL_UNCOMPRESSED_BYTE_LIMIT:
                    raise CandidateConstructionError(
                        "WHEEL_UNCOMPRESSED_SIZE_LIMIT_EXCEEDED", path.name
                    )
        metadata_names = [
            name
            for name in names
            if len(PurePosixPath(name).parts) == 2
            and PurePosixPath(name).parts[0].endswith(".dist-info")
            and PurePosixPath(name).parts[1] == "METADATA"
        ]
        record_names = [
            name
            for name in names
            if len(PurePosixPath(name).parts) == 2
            and PurePosixPath(name).parts[0].endswith(".dist-info")
            and PurePosixPath(name).parts[1] == "RECORD"
        ]
        wheel_names = [
            name
            for name in names
            if len(PurePosixPath(name).parts) == 2
            and PurePosixPath(name).parts[0].endswith(".dist-info")
            and PurePosixPath(name).parts[1] == "WHEEL"
        ]
        if (
            len(metadata_names) != 1
            or len(record_names) != 1
            or len(wheel_names) != 1
        ):
            raise CandidateConstructionError(
                "WHEEL_DIST_INFO_CARDINALITY_INVALID", path.name
            )
        expected_controls = {
            f"{expected_dist_info}/METADATA",
            f"{expected_dist_info}/RECORD",
            f"{expected_dist_info}/WHEEL",
        }
        if {
            metadata_names[0], record_names[0], wheel_names[0]
        } != expected_controls:
            raise CandidateConstructionError(
                "WHEEL_DIST_INFO_IDENTITY_BINDING_MISMATCH", path.name
            )
        for name in canonical_member_paths:
            top_level = PurePosixPath(name).parts[0]
            if (
                top_level.endswith(".dist-info")
                and top_level != expected_dist_info
            ):
                raise CandidateConstructionError(
                    "WHEEL_FOREIGN_TOP_LEVEL_DIST_INFO_MEMBER", path.name
                )

        def read_control_member(name, label):
            info = info_by_name[name]
            if info.file_size > WHEEL_CONTROL_MEMBER_BYTE_LIMIT:
                raise CandidateConstructionError(
                    "WHEEL_CONTROL_MEMBER_SIZE_LIMIT_EXCEEDED", label
                )
            payload = bytearray()
            with archive.open(info, mode="r") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    payload.extend(chunk)
                    if len(payload) > WHEEL_CONTROL_MEMBER_BYTE_LIMIT:
                        raise CandidateConstructionError(
                            "WHEEL_CONTROL_MEMBER_EXPANDED_PAST_LIMIT", label
                        )
            if len(payload) != info.file_size:
                raise CandidateConstructionError(
                    "WHEEL_CONTROL_MEMBER_SIZE_MISMATCH", label
                )
            return bytes(payload)

        message = email.parser.BytesParser().parsebytes(
            read_control_member(metadata_names[0], "METADATA")
        )
        distribution_headers = message.get_all("Name", [])
        version_headers = message.get_all("Version", [])
        if len(distribution_headers) != 1 or len(version_headers) != 1:
            raise CandidateConstructionError(
                "WHEEL_METADATA_IDENTITY_CARDINALITY_INVALID", path.name
            )
        distribution = distribution_headers[0]
        version = version_headers[0]
        if type(distribution) is not str or type(version) is not str:
            raise CandidateConstructionError(
                "WHEEL_METADATA_IDENTITY_TYPE_INVALID", path.name
            )
        try:
            distribution.encode("ascii")
            version.encode("ascii")
        except UnicodeEncodeError as error:
            raise CandidateConstructionError(
                "WHEEL_METADATA_IDENTITY_NOT_ASCII", path.name
            ) from error
        if (
            WHEEL_METADATA_NAME.fullmatch(distribution) is None
            or WHEEL_VERSION_TOKEN.fullmatch(version) is None
            or normalized_name(distribution)
            != normalized_name(filename_distribution)
            or version != filename_version
        ):
            raise CandidateConstructionError(
                "WHEEL_METADATA_IDENTITY_MISMATCH", path.name
            )
        record_bytes = read_control_member(record_names[0], "RECORD")
        try:
            record_text = record_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                "WHEEL_RECORD_NOT_UTF8", path.name
            ) from error
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
            info = info_by_name[record_path]
            digest = hashlib.sha256()
            observed_size = 0
            with archive.open(info, mode="r") as member_handle:
                while True:
                    chunk = member_handle.read(1024 * 1024)
                    if not chunk:
                        break
                    observed_size += len(chunk)
                    if observed_size > info.file_size:
                        raise CandidateConstructionError(
                            "WHEEL_MEMBER_EXPANDED_PAST_DECLARED_SIZE",
                            path.name,
                        )
                    digest.update(chunk)
            if observed_size != info.file_size:
                raise CandidateConstructionError(
                    "WHEEL_MEMBER_OBSERVED_SIZE_MISMATCH", path.name
                )
            if bool(hash_field) != bool(size_field):
                raise CandidateConstructionError(
                    "WHEEL_RECORD_HASH_SIZE_PAIR_INCOMPLETE", path.name
                )
            if hash_field:
                algorithm, separator, encoded = hash_field.partition("=")
                if separator != "=" or algorithm != "sha256":
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_NON_SHA256_HASH", path.name
                    )
                padding = "=" * ((4 - len(encoded) % 4) % 4)
                try:
                    declared = base64.b64decode(
                        (encoded + padding).encode("ascii"),
                        altchars=b"-_",
                        validate=True,
                    )
                except (TypeError, ValueError, base64.binascii.Error) as error:
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_HASH_ENCODING_INVALID", path.name
                    ) from error
                if declared != digest.digest():
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_HASH_MISMATCH", path.name
                    )
            elif record_path != record_names[0]:
                raise CandidateConstructionError(
                    "WHEEL_RECORD_UNHASHED_NON_RECORD_MEMBER", path.name
                )
            if size_field:
                try:
                    declared_size = int(size_field)
                except ValueError as error:
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_SIZE_INVALID", path.name
                    ) from error
                if declared_size != observed_size:
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_SIZE_MISMATCH", path.name
                    )
        if record_paths != set(names):
            raise CandidateConstructionError(
                "WHEEL_RECORD_PAYLOAD_CLOSURE_INCOMPLETE", path.name
            )
        wheel_payload = read_control_member(wheel_names[0], "WHEEL")
        try:
            wheel_payload.decode("ascii")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                "WHEEL_METADATA_CONTROL_NOT_ASCII", path.name
            ) from error
        wheel_message = email.parser.BytesParser().parsebytes(wheel_payload)
        tags = wheel_message.get_all("Tag", [])
        expected_tags = sorted(
            f"{python_value}-{abi_value}-{platform_value}"
            for python_value in python_tag.split(".")
            for abi_value in abi_tag.split(".")
            for platform_value in platform_tag.split(".")
        )
        if (
            not tags
            or any(
                type(tag) is not str
                or re.fullmatch(
                    r"[A-Za-z0-9_]+-[A-Za-z0-9_]+-[A-Za-z0-9_]+",
                    tag,
                )
                is None
                for tag in tags
            )
            or sorted(tags) != expected_tags
        ):
            raise CandidateConstructionError(
                "WHEEL_TAG_BINDING_MISMATCH", path.name
            )
        final_sha256, final_size = hash_open_descriptor()
        if final_sha256 != artifact_sha256 or final_size != size:
            raise CandidateConstructionError(
                "WHEEL_FILE_CHANGED_DURING_INSPECTION", path.name
            )
    finally:
        if archive is not None:
            archive.close()
        if source_handle is not None and not source_handle.closed:
            source_handle.close()
        os.close(descriptor)
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
        "central_directory": central_directory,
    }


def inspect_wheel_directory(directory):
    objects = []
    aggregate_size = 0
    observed_sizes = {}
    for path in directory.iterdir():
        if len(objects) >= WHEEL_ARTIFACT_LIMIT:
            raise CandidateConstructionError(
                "WHEEL_DIRECTORY_ARTIFACT_LIMIT_EXCEEDED"
            )
        if object_kind(path) != "REGULAR_FILE":
            raise CandidateConstructionError(
                "WHEEL_DIRECTORY_HAS_NONREGULAR_OBJECT"
            )
        if path.suffix != ".whl":
            raise CandidateConstructionError(
                "SDIST_OR_NON_WHEEL_ARTIFACT_PRESENT"
            )
        observed = path.lstat()
        size = observed.st_size
        if size < 0 or size > WHEEL_FILE_BYTE_LIMIT:
            raise CandidateConstructionError(
                "WHEEL_FILE_SIZE_LIMIT_EXCEEDED", path.name
            )
        aggregate_size += size
        if aggregate_size > WHEEL_DIRECTORY_BYTE_LIMIT:
            raise CandidateConstructionError(
                "WHEEL_DIRECTORY_BYTE_LIMIT_EXCEEDED"
            )
        objects.append(path)
        observed_sizes[path.name] = size
    objects.sort(key=lambda item: item.name)
    if not objects:
        raise CandidateConstructionError("WHEEL_DIRECTORY_EMPTY")
    records = [inspect_wheel(path) for path in objects]
    inspected_aggregate_size = 0
    for record in records:
        if record["size_bytes"] != observed_sizes.get(record["filename"]):
            raise CandidateConstructionError(
                "WHEEL_DIRECTORY_FILE_SIZE_CHANGED_DURING_INSPECTION",
                record["filename"],
            )
        inspected_aggregate_size += record["size_bytes"]
        if inspected_aggregate_size > WHEEL_DIRECTORY_BYTE_LIMIT:
            raise CandidateConstructionError(
                "WHEEL_DIRECTORY_BYTE_LIMIT_EXCEEDED"
            )
    if inspected_aggregate_size != aggregate_size:
        raise CandidateConstructionError(
            "WHEEL_DIRECTORY_AGGREGATE_SIZE_CHANGED_DURING_INSPECTION"
        )
    names = [record["normalized_name"] for record in records]
    if len(names) != len(set(names)):
        raise CandidateConstructionError("DUPLICATE_DISTRIBUTION_WHEELS")
    return records


PIP_IDENTITY_PROBE = """
import base64
import csv
import email.parser
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

CONTROL_FILE_BYTE_LIMIT = 16 * 1024 * 1024
DISTRIBUTION_ROOT_ENTRY_LIMIT = 100_000
RECORD_ROW_LIMIT = 250_000
PHYSICAL_DIRECTORY_LIMIT = 250_000
PAYLOAD_FILE_LIMIT = 250_000
PAYLOAD_SINGLE_FILE_BYTE_LIMIT = 4 * 1024 * 1024 * 1024
PAYLOAD_TOTAL_BYTE_LIMIT = 16 * 1024 * 1024 * 1024
READ_CHUNK_BYTES = 1024 * 1024


def read_regular_file_bounded(path, maximum_bytes, label, retain_payload):
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise RuntimeError(label + "_OPEN_FAILED") from error
    try:
        opened_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_stat.st_mode)
            or opened_stat.st_size < 0
            or opened_stat.st_size > maximum_bytes
        ):
            raise RuntimeError(label + "_OBJECT_OR_SIZE_INVALID")
        digest = hashlib.sha256()
        observed_size = 0
        retained = bytearray() if retain_payload else None
        while True:
            chunk = os.read(descriptor, READ_CHUNK_BYTES)
            if not chunk:
                break
            observed_size += len(chunk)
            if observed_size > maximum_bytes:
                raise RuntimeError(label + "_EXPANDED_PAST_LIMIT")
            digest.update(chunk)
            if retained is not None:
                retained.extend(chunk)
        final_stat = os.fstat(descriptor)
        if (
            observed_size != opened_stat.st_size
            or final_stat.st_size != opened_stat.st_size
        ):
            raise RuntimeError(label + "_SIZE_CHANGED_DURING_READ")
        return (
            digest.digest(),
            observed_size,
            None if retained is None else bytes(retained),
        )
    finally:
        os.close(descriptor)


spec = importlib.util.find_spec("pip")
if spec is None or not isinstance(spec.origin, str):
    raise RuntimeError("PIP_MODULE_ORIGIN_UNAVAILABLE")
install_prefix = Path(sys.prefix).resolve()
module_path = Path(spec.origin).resolve()
module_root = module_path.parent
distribution_root = module_root.parent
if module_root.name != "pip":
    raise RuntimeError("PIP_MODULE_ROOT_INVALID")
distribution_root_stat = distribution_root.lstat()
if (
    stat.S_ISLNK(distribution_root_stat.st_mode)
    or not stat.S_ISDIR(distribution_root_stat.st_mode)
):
    raise RuntimeError("PIP_DISTRIBUTION_ROOT_INVALID")
dist_info_candidates = []
distribution_root_entry_count = 0
with os.scandir(distribution_root) as entries:
    for entry in entries:
        distribution_root_entry_count += 1
        if distribution_root_entry_count > DISTRIBUTION_ROOT_ENTRY_LIMIT:
            raise RuntimeError("PIP_DISTRIBUTION_ROOT_ENTRY_LIMIT_EXCEEDED")
        if (
            entry.name.lower().startswith("pip-")
            and entry.name.lower().endswith(".dist-info")
        ):
            if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                raise RuntimeError("PIP_DIST_INFO_OBJECT_INVALID")
            dist_info_candidates.append(Path(entry.path).resolve())
if len(dist_info_candidates) != 1:
    raise RuntimeError("PIP_DIST_INFO_CARDINALITY_INVALID")
dist_info_root = dist_info_candidates[0]
metadata_path = dist_info_root / "METADATA"
record_path = dist_info_root / "RECORD"
module_digest, module_size, _ = read_regular_file_bounded(
    module_path,
    CONTROL_FILE_BYTE_LIMIT,
    "PIP_MODULE_FILE",
    False,
)
_, _, metadata_payload = read_regular_file_bounded(
    metadata_path,
    CONTROL_FILE_BYTE_LIMIT,
    "PIP_METADATA_FILE",
    True,
)
metadata = email.parser.BytesParser().parsebytes(metadata_payload)
distribution_name = metadata.get("Name")
distribution_version = metadata.get("Version")
if (
    not isinstance(distribution_name, str)
    or distribution_name.lower().replace("_", "-") != "pip"
    or not isinstance(distribution_version, str)
    or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", distribution_version)
    is None
):
    raise RuntimeError("PIP_METADATA_IDENTITY_INVALID")
record_digest, record_size, record_payload = read_regular_file_bounded(
    record_path,
    CONTROL_FILE_BYTE_LIMIT,
    "PIP_RECORD_FILE",
    True,
)
try:
    record_text = record_payload.decode("utf-8")
except UnicodeDecodeError as error:
    raise RuntimeError("PIP_RECORD_NOT_UTF8") from error
declared_paths = set()
resolved_paths = set()
payload_manifest = []
payload_bytes_hashed = 0
hashed_record_count = 0
unhashed_record_count = 0
record_row_count = 0
for row in csv.reader(io.StringIO(record_text)):
    record_row_count += 1
    if record_row_count > RECORD_ROW_LIMIT:
        raise RuntimeError("PIP_RECORD_ROW_LIMIT_EXCEEDED")
    if len(row) != 3:
        raise RuntimeError("PIP_RECORD_ROW_SHAPE_INVALID")
    relative, declared_digest, declared_size = row
    pure = PurePosixPath(relative)
    if (
        not relative
        or relative in declared_paths
        or "\\\\" in relative
        or pure.is_absolute()
        or relative != pure.as_posix()
        or any(part in ("", ".") for part in pure.parts)
        or any(
            ord(character) < 32 or ord(character) == 127
            for character in relative
        )
    ):
        raise RuntimeError("PIP_RECORD_PATH_INVALID")
    declared_paths.add(relative)
    located = Path(os.path.abspath(os.path.join(distribution_root, *pure.parts)))
    try:
        located.relative_to(install_prefix)
    except ValueError as error:
        raise RuntimeError("PIP_RECORD_PATH_ESCAPES_INSTALL_PREFIX") from error
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
    remaining_payload_bytes = PAYLOAD_TOTAL_BYTE_LIMIT - payload_bytes_hashed
    if remaining_payload_bytes <= 0:
        raise RuntimeError("PIP_PAYLOAD_TOTAL_BYTE_LIMIT_EXCEEDED")
    actual_digest, actual_size, _ = read_regular_file_bounded(
        resolved,
        min(PAYLOAD_SINGLE_FILE_BYTE_LIMIT, remaining_payload_bytes),
        "PIP_RECORD_PAYLOAD",
        False,
    )
    payload_bytes_hashed += actual_size
    if bool(declared_digest) != bool(declared_size):
        raise RuntimeError("PIP_RECORD_HASH_SIZE_PAIR_INCOMPLETE")
    if declared_digest:
        algorithm, separator, encoded = declared_digest.partition("=")
        if algorithm != "sha256" or separator != "=" or not encoded:
            raise RuntimeError("PIP_RECORD_DIGEST_INVALID")
        padding = "=" * (-len(encoded) % 4)
        try:
            decoded_digest = base64.b64decode(
                (encoded + padding).encode("ascii"),
                altchars=b"-_",
                validate=True,
            )
        except (UnicodeEncodeError, ValueError, base64.binascii.Error) as error:
            raise RuntimeError("PIP_RECORD_DIGEST_ENCODING_INVALID") from error
        if decoded_digest != actual_digest:
            raise RuntimeError("PIP_RECORD_DIGEST_MISMATCH")
        try:
            expected_size = int(declared_size)
        except ValueError as error:
            raise RuntimeError("PIP_RECORD_SIZE_INVALID") from error
        if expected_size != actual_size:
            raise RuntimeError("PIP_RECORD_SIZE_MISMATCH")
        hashed_record_count += 1
    else:
        unhashed_record_count += 1
    payload_manifest.append({
        "install_relative_path": install_relative,
        "record_declared": True,
        "sha256": actual_digest.hex(),
        "size_bytes": actual_size,
    })
    if len(payload_manifest) > PAYLOAD_FILE_LIMIT:
        raise RuntimeError("PIP_PAYLOAD_FILE_LIMIT_EXCEEDED")

physical_payload_paths = set()
physical_directory_count = 0
for physical_root in (module_root, dist_info_root):
    root_stat = physical_root.lstat()
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise RuntimeError("PIP_PAYLOAD_ROOT_NOT_PHYSICAL_DIRECTORY")
    pending = [physical_root]
    while pending:
        current = pending.pop()
        physical_directory_count += 1
        if physical_directory_count > PHYSICAL_DIRECTORY_LIMIT:
            raise RuntimeError("PIP_PHYSICAL_DIRECTORY_LIMIT_EXCEEDED")
        with os.scandir(current) as entries:
            for entry in entries:
                if entry.is_symlink():
                    raise RuntimeError("PIP_PAYLOAD_SYMLINK_REJECTED")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    physical_payload_paths.add(Path(entry.path).resolve())
                    if len(physical_payload_paths) > PAYLOAD_FILE_LIMIT:
                        raise RuntimeError("PIP_PHYSICAL_FILE_LIMIT_EXCEEDED")
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
    remaining_payload_bytes = PAYLOAD_TOTAL_BYTE_LIMIT - payload_bytes_hashed
    if remaining_payload_bytes <= 0:
        raise RuntimeError("PIP_PAYLOAD_TOTAL_BYTE_LIMIT_EXCEEDED")
    payload_digest, payload_size, _ = read_regular_file_bounded(
        path,
        min(PAYLOAD_SINGLE_FILE_BYTE_LIMIT, remaining_payload_bytes),
        "PIP_UNRECORDED_BYTECODE",
        False,
    )
    payload_bytes_hashed += payload_size
    payload_manifest.append({
        "install_relative_path": install_relative,
        "record_declared": False,
        "sha256": payload_digest.hex(),
        "size_bytes": payload_size,
    })
    if len(payload_manifest) > PAYLOAD_FILE_LIMIT:
        raise RuntimeError("PIP_PAYLOAD_FILE_LIMIT_EXCEEDED")

payload_manifest.sort(key=lambda item: item["install_relative_path"])
payload_manifest_bytes = json.dumps(
    payload_manifest,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
print(json.dumps({
    "pip_distribution_root": str(distribution_root),
    "pip_install_prefix": str(install_prefix),
    "pip_module_file": str(module_path),
    "pip_module_file_sha256": module_digest.hex(),
    "pip_module_file_size_bytes": module_size,
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
    "pip_record_file_sha256": record_digest.hex(),
    "pip_record_file_size_bytes": record_size,
    "pip_version": distribution_version,
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
    if root is not None:
        lexical_python = Path(python_executable)
        try:
            lexical_python.relative_to(root)
        except ValueError as error:
            raise CandidateConstructionError(
                "PIP_IDENTITY_LEXICAL_PYTHON_ESCAPES_EXPECTED_ROOT",
                step,
            ) from error
        if object_kind(lexical_python) != "REGULAR_FILE":
            raise CandidateConstructionError(
                "PIP_IDENTITY_LEXICAL_PYTHON_NOT_REGULAR",
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
            or size_value > PIP_IDENTITY_CONTROL_FILE_BYTE_LIMIT
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
        (
            observed_digest,
            observed_size,
            _,
            _,
        ) = sha256_regular_file_nofollow(
            path,
            PIP_IDENTITY_CONTROL_FILE_BYTE_LIMIT,
            "PIP_IDENTITY_CONTROL_FILE",
        )
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


def portable_pip_identity_evidence(identity, runtime_role):
    if runtime_role not in (
        "HOST_NOTEBOOK_INTERPRETER",
        "ISOLATED_BUILD_VENV",
    ):
        raise CandidateConstructionError("PIP_IDENTITY_RUNTIME_ROLE_INVALID")
    install_prefix = Path(identity["pip_install_prefix"])
    path_keys = (
        "pip_distribution_root",
        "pip_module_file",
        "pip_record_file",
    )
    relative_paths = {}
    try:
        for key in path_keys:
            relative_paths[key + "_relative_to_install_prefix"] = (
                Path(identity[key]).relative_to(install_prefix).as_posix()
            )
    except ValueError as error:
        raise CandidateConstructionError(
            "PIP_IDENTITY_PORTABLE_PROJECTION_ESCAPES_PREFIX"
        ) from error
    volatile_path_keys = {
        "pip_install_prefix",
        "python_executable",
        *path_keys,
    }
    evidence = {
        key: value
        for key, value in identity.items()
        if key not in volatile_path_keys
    }
    evidence["runtime_role"] = runtime_role
    evidence["path_projection"] = relative_paths
    try:
        Path(identity["python_executable"]).relative_to(install_prefix)
    except ValueError:
        executable_relationship = "RESOLVED_TARGET_OUTSIDE_INSTALL_PREFIX"
    else:
        executable_relationship = "RESOLVED_TARGET_WITHIN_INSTALL_PREFIX"
    evidence["python_executable_relationship"] = executable_relationship
    evidence["absolute_runtime_paths_persisted"] = False
    evidence["content_derived_payload_closure_persisted"] = True
    evidence["omitted_absolute_path_fields"] = [
        "pip_install_prefix",
        "pip_distribution_root",
        "pip_module_file",
        "pip_record_file",
        "python_executable",
    ]
    return immutable_json_snapshot(evidence)


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
    host_pip_identity = bind_pip_identity(
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
    binding["host_pip_identity"] = portable_pip_identity_evidence(
        host_pip_identity, "HOST_NOTEBOOK_INTERPRETER"
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
            "--no-cache-dir",
            "--quiet",
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
    write_local_exclusive(
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
    if rebound_host_identity != host_pip_identity:
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
            "--no-cache-dir",
            "--quiet",
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
    isolated_venv_pip_identity = bind_pip_identity(
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
    binding["isolated_venv_pip_identity"] = portable_pip_identity_evidence(
        isolated_venv_pip_identity, "ISOLATED_BUILD_VENV"
    )
    attempt_state["isolated_venv_pip_identity"] = binding[
        "isolated_venv_pip_identity"
    ]
    return binding


def lock_candidate_bytes(wheel_records):
    records = list(wheel_records)
    if not records or len(records) > WHEEL_ARTIFACT_LIMIT:
        raise CandidateConstructionError(
            "LOCK_CANDIDATE_RECORD_COUNT_INVALID"
        )
    validated = []
    observed_names = set()
    for record in records:
        if not isinstance(record, dict):
            raise CandidateConstructionError(
                "LOCK_CANDIDATE_RECORD_INVALID"
            )
        name = record.get("normalized_name")
        version = record.get("version")
        digest = record.get("sha256")
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is None
            or normalized_name(name) != name
            or not isinstance(version, str)
            or WHEEL_VERSION_TOKEN.fullmatch(version) is None
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise CandidateConstructionError(
                "LOCK_CANDIDATE_RECORD_IDENTITY_INVALID"
            )
        if name in observed_names:
            raise CandidateConstructionError(
                "LOCK_CANDIDATE_DUPLICATE_DISTRIBUTION", name
            )
        observed_names.add(name)
        validated.append((name, version, digest))
    lines = [
        "# REVIEW-PENDING F152 CANDIDATE; not an authority or runtime "
        "install instruction.",
        "# Install only after independent acceptance with --no-index "
        "--only-binary=:all: --require-hashes.",
    ]
    for name, version, digest in sorted(validated):
        lines.append(f"{name}=={version} \\")
        lines.append(f"    --hash=sha256:{digest}")
    return ("\n".join(lines) + "\n").encode("ascii")


def reverify_candidate_artifacts_before_manifest(
    candidate_root,
    tool_wheelhouse,
    runtime_wheelhouse,
    tool_records,
    runtime_records,
    tool_lock_path,
    runtime_lock_path,
    bootstrap_pip_binding,
):
    rebound_tool_records = inspect_wheel_directory(tool_wheelhouse)
    rebound_runtime_records = inspect_wheel_directory(runtime_wheelhouse)
    if rebound_tool_records != tool_records:
        raise CandidateConstructionError(
            "BUILD_TOOL_WHEELHOUSE_CHANGED_BEFORE_MANIFEST"
        )
    if rebound_runtime_records != runtime_records:
        raise CandidateConstructionError(
            "RUNTIME_WHEELHOUSE_CHANGED_BEFORE_MANIFEST"
        )
    bootstrap_record = next(
        (
            record
            for record in rebound_tool_records
            if record["normalized_name"] == "pip"
        ),
        None,
    )
    if bootstrap_record != bootstrap_pip_binding.get("bootstrap_wheel"):
        raise CandidateConstructionError(
            "BOOTSTRAP_PIP_WHEEL_CHANGED_BEFORE_MANIFEST"
        )
    expected_controls = (
        (
            "bootstrap_lock",
            Path(candidate_root)
            / bootstrap_pip_binding["bootstrap_lock"]["filename"],
            lock_candidate_bytes([bootstrap_record]),
        ),
        (
            "build_tool_lock",
            Path(tool_lock_path),
            lock_candidate_bytes(rebound_tool_records),
        ),
        (
            "runtime_lock",
            Path(runtime_lock_path),
            lock_candidate_bytes(rebound_runtime_records),
        ),
    )
    control_bindings = {}
    for label, path, expected_payload in expected_controls:
        observed_payload = read_regular_file_nofollow_bounded(
            path,
            CONTROL_OBJECT_BYTE_LIMIT,
            "PREARCHIVE_" + label.upper(),
        )
        if observed_payload != expected_payload:
            raise CandidateConstructionError(
                "PREARCHIVE_CONTROL_FILE_BINDING_MISMATCH", label
            )
        control_bindings[label] = {
            "relative_path": path.relative_to(candidate_root).as_posix(),
            "sha256": sha256_bytes(observed_payload),
            "size_bytes": len(observed_payload),
        }
    if (
        control_bindings["bootstrap_lock"]["sha256"]
        != bootstrap_pip_binding["bootstrap_lock"]["sha256"]
    ):
        raise CandidateConstructionError(
            "BOOTSTRAP_PIP_LOCK_CHANGED_BEFORE_MANIFEST"
        )
    return {
        "build_tool_wheelhouse_reinspection_exact": True,
        "runtime_wheelhouse_reinspection_exact": True,
        "bootstrap_pip_wheel_reinspection_exact": True,
        "control_files": control_bindings,
    }


def write_local_exclusive(path, payload, mode=0o640):
    """Write a no-clobber file in ephemeral POSIX staging only."""
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


class UcVolumeAppendOnlyStore:
    """A narrow path-visible writer matching the accepted probe semantics."""

    def __init__(self, parent, allowed_leaf_names, attempt_state=None):
        self.parent = Path(parent)
        self.allowed_leaf_names = frozenset(allowed_leaf_names)
        self.attempt_state = attempt_state

    def _validate_name(self, name):
        if (
            type(name) is not str
            or name not in self.allowed_leaf_names
            or not name
            or "/" in name
            or "\\" in name
            or name in (".", "..")
            or any(ord(character) < 32 for character in name)
        ):
            raise CandidateConstructionError("UC_RESERVED_LEAF_NAME_INVALID")

    def _open_parent(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            return os.open(self.parent, flags)
        except OSError as error:
            raise CandidateConstructionError(
                "UC_PARENT_OPEN_FAILED", type(error).__name__
            ) from error

    @staticmethod
    def _close_once(descriptor, error_code):
        if descriptor is None:
            return
        try:
            os.close(descriptor)
        except BaseException as error:
            raise CandidateConstructionError(
                error_code, type(error).__name__
            ) from error

    def read_binding(self, name, maximum_bytes=None):
        self._validate_name(name)
        parent_descriptor = self._open_parent()
        leaf_descriptor = None
        body_error = None
        digest = hashlib.sha256()
        size = 0
        try:
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
            leaf_descriptor = os.open(
                name, flags, dir_fd=parent_descriptor
            )
            while True:
                chunk = os.read(leaf_descriptor, UC_READ_CHUNK_BYTES)
                if not chunk:
                    break
                size += len(chunk)
                if maximum_bytes is not None and size > maximum_bytes:
                    raise CandidateConstructionError(
                        "UC_READBACK_EXCEEDS_EXPECTED_SIZE", name
                    )
                digest.update(chunk)
        except BaseException as error:
            body_error = error
        close_error = None
        if leaf_descriptor is not None:
            try:
                self._close_once(
                    leaf_descriptor, "UC_READBACK_LEAF_CLOSE_FAILED"
                )
            except BaseException as error:
                close_error = error
        try:
            self._close_once(
                parent_descriptor, "UC_READBACK_PARENT_CLOSE_FAILED"
            )
        except BaseException as error:
            if close_error is None:
                close_error = error
        if body_error is not None:
            if isinstance(body_error, CandidateConstructionError):
                raise body_error
            raise CandidateConstructionError(
                "UC_READBACK_FAILED",
                f"{name}:{type(body_error).__name__}",
            ) from body_error
        if close_error is not None:
            raise close_error
        return {"name": name, "sha256": digest.hexdigest(), "size_bytes": size}

    def verify_binding(self, name, expected_sha256, expected_size):
        readbacks = []
        for ordinal in (1, 2):
            observed = self.read_binding(name, maximum_bytes=expected_size)
            if (
                observed["sha256"] != expected_sha256
                or observed["size_bytes"] != expected_size
            ):
                raise CandidateConstructionError(
                    "UC_REPEATABLE_READBACK_BINDING_MISMATCH",
                    f"{name}:readback={ordinal}",
                )
            readbacks.append(observed)
        if readbacks[0] != readbacks[1]:
            raise CandidateConstructionError(
                "UC_REPEATABLE_READBACKS_DISAGREE", name
            )
        return {
            "name": name,
            "sha256": expected_sha256,
            "size_bytes": expected_size,
            "fresh_readback_count": 2,
        }

    def _write_chunks(self, name, chunks, expected_sha256, expected_size):
        self._validate_name(name)
        if (
            type(expected_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
            or type(expected_size) is not int
            or expected_size <= 0
        ):
            raise CandidateConstructionError("UC_EXPECTED_BINDING_INVALID")
        state = self.attempt_state
        if re.fullmatch(
            re.escape(CANDIDATE_ID) + r"\.payload-[0-9]{4}\.bin", name
        ):
            if expected_size > PAYLOAD_CHUNK_BYTES:
                raise CandidateConstructionError("UC_PAYLOAD_CHUNK_TOO_LARGE")
        elif expected_size > CONTROL_OBJECT_BYTE_LIMIT:
            raise CandidateConstructionError("UC_CONTROL_OBJECT_TOO_LARGE")
        if (
            state is not None
            and state["managed_uc_exclusive_create_calls_begun"]
            >= len(reserved_candidate_leaf_names())
        ):
            raise CandidateConstructionError(
                "UC_EXCLUSIVE_CREATE_CALL_LIMIT_EXCEEDED"
            )
        parent_descriptor = self._open_parent()
        leaf_descriptor = None
        created = False
        digest = hashlib.sha256()
        size = 0
        body_error = None
        try:
            flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | os.O_CLOEXEC
            )
            if state is not None:
                state["managed_uc_write_begun"] = True
                state["managed_uc_exclusive_create_calls_begun"] += 1
                state["managed_uc_last_leaf_create_begun"] = name
                state["managed_uc_last_leaf_expected_sha256"] = (
                    expected_sha256
                )
                state["managed_uc_last_leaf_expected_size_bytes"] = (
                    expected_size
                )
                # Once the exclusive-create call boundary is reached, preserve
                # the leaf conservatively as possibly present. An asynchronous
                # exception may arrive after the backend creates the object but
                # before Python receives or stores the descriptor.
                state["managed_uc_last_leaf_may_exist"] = name
                state["attempt_namespace_spent"] = True
                if name == ATTEMPT_INTENT_LEAF_NAME:
                    state["intent_create_begun"] = True
                    state["durable_intent_may_exist"] = True
                elif name == SUCCESS_RECEIPT_LEAF_NAME:
                    state["success_receipt_create_call_begun"] = True
                    state["success_receipt_may_exist"] = True
                elif name == FAILURE_RECEIPT_LEAF_NAME:
                    state["failure_receipt_create_call_begun"] = True
                    state["failure_receipt_may_exist"] = True
            try:
                leaf_descriptor = os.open(
                    name, flags, 0o600, dir_fd=parent_descriptor
                )
            except FileExistsError as error:
                raise CandidateConstructionError(
                    "UC_EXCLUSIVE_CREATE_COLLISION", name
                ) from error
            created = True
            for chunk in chunks:
                if not isinstance(chunk, (bytes, bytearray, memoryview)):
                    raise CandidateConstructionError(
                        "UC_WRITE_STREAM_CHUNK_INVALID", name
                    )
                view = memoryview(chunk)
                while view:
                    written = os.write(leaf_descriptor, view)
                    if written <= 0:
                        raise CandidateConstructionError(
                            "UC_EXCLUSIVE_WRITE_DID_NOT_PROGRESS", name
                        )
                    digest.update(view[:written])
                    size += written
                    if size > expected_size:
                        raise CandidateConstructionError(
                            "UC_EXCLUSIVE_WRITE_EXCEEDS_EXPECTED_SIZE", name
                        )
                    view = view[written:]
            if size != expected_size or digest.hexdigest() != expected_sha256:
                raise CandidateConstructionError(
                    "UC_EXCLUSIVE_WRITE_SOURCE_BINDING_MISMATCH", name
                )
        except BaseException as error:
            body_error = error
        close_error = None
        if leaf_descriptor is not None:
            try:
                self._close_once(
                    leaf_descriptor, "UC_CREATED_LEAF_CLOSE_FAILED"
                )
            except BaseException as error:
                close_error = error
        try:
            self._close_once(
                parent_descriptor, "UC_CREATED_LEAF_PARENT_CLOSE_FAILED"
            )
        except BaseException as error:
            if close_error is None:
                close_error = error
        if body_error is not None or close_error is not None:
            raw_error = body_error or close_error
            if created:
                detail = (
                    raw_error.code
                    if isinstance(raw_error, CandidateConstructionError)
                    else type(raw_error).__name__
                )
                raise CandidateConstructionError(
                    "UC_EXCLUSIVE_WRITE_FAILED_AFTER_CREATE",
                    f"{name}:{detail}",
                    telemetry={
                        "attempt_namespace_spent": True,
                        "managed_uc_last_leaf_may_exist": name,
                        "managed_uc_last_leaf_expected_sha256": expected_sha256,
                        "managed_uc_last_leaf_expected_size_bytes": expected_size,
                    },
                ) from raw_error
            if isinstance(raw_error, CandidateConstructionError):
                raise raw_error
            raise CandidateConstructionError(
                "UC_EXCLUSIVE_CREATE_FAILED",
                f"{name}:{type(raw_error).__name__}",
            ) from raw_error
        try:
            binding = self.verify_binding(name, expected_sha256, expected_size)
        except BaseException as error:
            code = (
                error.code
                if isinstance(error, CandidateConstructionError)
                else type(error).__name__
            )
            raise CandidateConstructionError(
                "UC_POST_CREATE_READBACK_FAILED",
                f"{name}:{code}",
                telemetry={
                    "attempt_namespace_spent": True,
                    "managed_uc_last_leaf_may_exist": name,
                    "managed_uc_last_leaf_expected_sha256": expected_sha256,
                    "managed_uc_last_leaf_expected_size_bytes": expected_size,
                },
            ) from error
        if state is not None:
            state["managed_uc_confirmed_leaf_count"] += 1
            state["managed_uc_confirmed_bytes_written"] += expected_size
            state["managed_uc_last_confirmed_binding"] = binding
            state["managed_uc_confirmed_bindings"].append(binding)
        return binding

    def write_bytes(self, name, payload):
        if not isinstance(payload, bytes):
            raise CandidateConstructionError("UC_WRITE_PAYLOAD_NOT_BYTES")
        return self._write_chunks(
            name, (payload,), sha256_bytes(payload), len(payload)
        )

    def write_file_region(
        self, name, source_path, offset, size, expected_sha256
    ):
        if (
            object_kind(source_path) != "REGULAR_FILE"
            or type(offset) is not int
            or type(size) is not int
            or offset < 0
            or size <= 0
        ):
            raise CandidateConstructionError("UC_FILE_REGION_INVALID")

        def chunks():
            remaining = size
            with source_path.open("rb") as handle:
                handle.seek(offset)
                while remaining:
                    chunk = handle.read(min(UC_READ_CHUNK_BYTES, remaining))
                    if not chunk:
                        raise CandidateConstructionError(
                            "UC_FILE_REGION_SOURCE_TRUNCATED", name
                        )
                    remaining -= len(chunk)
                    yield chunk

        return self._write_chunks(
            name, chunks(), expected_sha256, size
        )


def verify_durable_intent_custody(
    durable_attempt,
    expected_intent_sha256,
    expected_intent_size,
):
    binding = durable_attempt["store"].verify_binding(
        ATTEMPT_INTENT_LEAF_NAME,
        expected_intent_sha256,
        expected_intent_size,
    )
    if durable_attempt["intent"] != binding:
        raise CandidateConstructionError("UC_ATTEMPT_INTENT_BINDING_MISMATCH")
    return binding


def start_durable_attempt(destination, intent_bytes, attempt_state):
    if Path(destination) != CANDIDATE_PREFIX:
        raise CandidateConstructionError("UC_CANDIDATE_PREFIX_NOT_EXACT")
    store = UcVolumeAppendOnlyStore(
        CANDIDATE_PARENT,
        reserved_candidate_leaf_names(),
        attempt_state,
    )
    try:
        intent_binding = store.write_bytes(
            ATTEMPT_INTENT_LEAF_NAME, intent_bytes
        )
    except CandidateConstructionError as error:
        telemetry = immutable_json_snapshot(attempt_state)
        if error.telemetry is not None:
            telemetry.update(error.telemetry)
        raise CandidateConstructionError(
            "UC_ATTEMPT_INTENT_COMMIT_FAILED",
            error.code,
            telemetry=telemetry,
        ) from error
    attempt_state["durable_intent_committed"] = True
    return {
        "absolute_path": CANDIDATE_PREFIX.as_posix(),
        "parent_path": CANDIDATE_PARENT.as_posix(),
        "candidate_id": CANDIDATE_ID,
        "intent": intent_binding,
        "store": store,
    }


def record_sha256_field(payload):
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest())
    return "sha256=" + encoded.rstrip(b"=").decode("ascii")


def normalize_overlay_entrypoint_shebangs(overlay_root, venv_python):
    overlay_root = Path(overlay_root).resolve()
    script_root = overlay_root / "bin"
    if object_kind(script_root) == "ABSENT":
        return {
            "normalized_script_count": 0,
            "normalized_scripts": [],
            "record_file_count_rewritten": 0,
            "stable_shebang": "/usr/bin/env python3",
            "volatile_interpreter_paths_persisted": False,
        }
    if object_kind(script_root) != "DIRECTORY":
        raise CandidateConstructionError("OVERLAY_SCRIPT_ROOT_NOT_DIRECTORY")
    allowed_shebangs = {
        b"#!" + os.fsencode(str(venv_python)),
        b"#!" + os.fsencode(str(Path(venv_python).resolve())),
    }
    stable_shebang = b"#!/usr/bin/env python3"
    normalized = {}
    script_paths = []
    for path in script_root.iterdir():
        if len(script_paths) >= OVERLAY_ENTRYPOINT_LIMIT:
            raise CandidateConstructionError(
                "OVERLAY_ENTRYPOINT_COUNT_LIMIT_EXCEEDED"
            )
        script_paths.append(path)
    for path in sorted(script_paths, key=lambda item: item.name):
        if object_kind(path) != "REGULAR_FILE":
            raise CandidateConstructionError(
                "OVERLAY_SCRIPT_OBJECT_NOT_REGULAR", path.name
            )
        payload = read_regular_file_nofollow_bounded(
            path,
            OVERLAY_ENTRYPOINT_BYTE_LIMIT,
            "OVERLAY_ENTRYPOINT_SCRIPT",
        )
        first_line, separator, remainder = payload.partition(b"\n")
        if first_line not in allowed_shebangs:
            continue
        if separator != b"\n":
            raise CandidateConstructionError(
                "OVERLAY_ENTRYPOINT_SHEBANG_NOT_TERMINATED", path.name
            )
        rewritten = stable_shebang + b"\n" + remainder
        path.write_bytes(rewritten)
        normalized[path.resolve()] = {
            "relative_path": path.relative_to(overlay_root).as_posix(),
            "sha256": sha256_bytes(rewritten),
            "size_bytes": len(rewritten),
        }

    owner_count = {path: 0 for path in normalized}
    rewritten_records = 0
    site_packages_root = overlay_root / OVERLAY_SITE_PACKAGES_RELATIVE_PATH
    if object_kind(site_packages_root) != "DIRECTORY":
        raise CandidateConstructionError(
            "OVERLAY_SITE_PACKAGES_ROOT_NOT_DIRECTORY"
        )
    overlay_tree = bounded_physical_tree(
        overlay_root,
        OVERLAY_TREE_ENTRY_LIMIT,
        OVERLAY_TREE_TOTAL_BYTE_LIMIT,
        "OVERLAY_ENTRYPOINT_TREE",
    )
    record_paths = [
        path
        for path in overlay_tree["files"]
        if path.name == "RECORD"
        and path.parent.name.endswith(".dist-info")
        and path.parent.parent == site_packages_root
    ]
    if len(record_paths) > OVERLAY_DISTRIBUTION_LIMIT:
        raise CandidateConstructionError(
            "OVERLAY_DISTRIBUTION_LIMIT_EXCEEDED"
        )
    for record_path in record_paths:
        if object_kind(record_path) != "REGULAR_FILE":
            raise CandidateConstructionError("OVERLAY_RECORD_NOT_REGULAR_FILE")
        record_payload = read_regular_file_nofollow_bounded(
            record_path,
            OVERLAY_CONTROL_FILE_BYTE_LIMIT,
            "OVERLAY_RECORD_FILE",
        )
        try:
            record_text = record_payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                "OVERLAY_RECORD_NOT_UTF8"
            ) from error
        rows = []
        for row in csv.reader(io.StringIO(record_text)):
            rows.append(row)
            if len(rows) > OVERLAY_RECORD_ROW_LIMIT:
                raise CandidateConstructionError(
                    "OVERLAY_RECORD_ROW_LIMIT_EXCEEDED"
                )
        changed = False
        record_base = record_path.parent.parent
        for row in rows:
            if len(row) != 3:
                raise CandidateConstructionError(
                    "OVERLAY_RECORD_ROW_INVALID_DURING_ENTRYPOINT_NORMALIZATION"
                )
            pure = PurePosixPath(row[0])
            if (
                not row[0]
                or pure.is_absolute()
                or "\\" in row[0]
                or row[0] != pure.as_posix()
                or any(part in ("", ".") for part in pure.parts)
                or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in row[0]
                )
            ):
                raise CandidateConstructionError(
                    "OVERLAY_RECORD_PATH_UNSAFE_DURING_ENTRYPOINT_NORMALIZATION"
                )
            target = Path(
                os.path.abspath(os.path.join(record_base, *pure.parts))
            )
            try:
                target.relative_to(overlay_root)
            except ValueError as error:
                raise CandidateConstructionError(
                    "OVERLAY_RECORD_PATH_ESCAPES_DURING_ENTRYPOINT_NORMALIZATION"
                ) from error
            if target not in normalized:
                continue
            payload = read_regular_file_nofollow_bounded(
                target,
                OVERLAY_ENTRYPOINT_BYTE_LIMIT,
                "OVERLAY_NORMALIZED_ENTRYPOINT",
            )
            row[1] = record_sha256_field(payload)
            row[2] = str(len(payload))
            owner_count[target] += 1
            changed = True
        if changed:
            output = io.StringIO(newline="")
            writer = csv.writer(output, lineterminator="\n")
            writer.writerows(rows)
            record_path.write_bytes(output.getvalue().encode("utf-8"))
            rewritten_records += 1
    if any(count != 1 for count in owner_count.values()):
        raise CandidateConstructionError(
            "OVERLAY_ENTRYPOINT_RECORD_OWNERSHIP_NOT_EXACT"
        )
    records = [normalized[path] for path in sorted(normalized, key=str)]
    return {
        "normalized_script_count": len(records),
        "normalized_scripts": records,
        "record_file_count_rewritten": rewritten_records,
        "stable_shebang": "/usr/bin/env python3",
        "volatile_interpreter_paths_persisted": False,
    }


def verify_candidate_has_no_volatile_path_bytes(candidate_root, markers):
    candidate_root = Path(candidate_root)
    encoded_markers = []
    for label, value in markers:
        encoded = os.fsencode(str(value))
        if encoded and encoded not in [item[1] for item in encoded_markers]:
            encoded_markers.append((label, encoded))
    maximum_marker = max((len(item[1]) for item in encoded_markers), default=1)
    candidate_tree = bounded_physical_tree(
        candidate_root,
        ARCHIVE_TREE_ENTRY_LIMIT,
        PAYLOAD_ARCHIVE_BYTE_LIMIT,
        "PORTABILITY_SCAN_TREE",
    )
    observed_sizes = {
        item["relative_path"]: item["size_bytes"]
        for item in candidate_tree["file_observations"]
    }
    checked_files = 0
    checked_bytes = 0
    for path in candidate_tree["files"]:
        relative_path = path.relative_to(candidate_root).as_posix()
        expected_size = observed_sizes[relative_path]
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            descriptor = os.open(path, flags)
        except OSError as error:
            raise CandidateConstructionError(
                "PORTABILITY_SCAN_FILE_OPEN_FAILED", relative_path
            ) from error
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_size != expected_size
            ):
                raise CandidateConstructionError(
                    "PORTABILITY_SCAN_FILE_BINDING_CHANGED", relative_path
                )
            carry = b""
            file_bytes = 0
            while True:
                chunk = os.read(descriptor, UC_READ_CHUNK_BYTES)
                if not chunk:
                    break
                file_bytes += len(chunk)
                checked_bytes += len(chunk)
                if (
                    file_bytes > expected_size
                    or checked_bytes > PAYLOAD_ARCHIVE_BYTE_LIMIT
                ):
                    raise CandidateConstructionError(
                        "PORTABILITY_SCAN_BYTE_LIMIT_EXCEEDED",
                        relative_path,
                    )
                window = carry + chunk
                for label, marker in encoded_markers:
                    if marker in window:
                        raise CandidateConstructionError(
                            "CANDIDATE_CONTAINS_VOLATILE_ABSOLUTE_PATH",
                            f"{relative_path}:{label}",
                        )
                carry = window[-(maximum_marker - 1):]
            final = os.fstat(descriptor)
            if (
                file_bytes != expected_size
                or final.st_size != expected_size
            ):
                raise CandidateConstructionError(
                    "PORTABILITY_SCAN_FILE_SIZE_CHANGED", relative_path
                )
        finally:
            os.close(descriptor)
        checked_files += 1
    if checked_bytes != candidate_tree["total_file_size_bytes"]:
        raise CandidateConstructionError(
            "PORTABILITY_SCAN_AGGREGATE_SIZE_CHANGED"
        )
    return {
        "checked_file_count": checked_files,
        "checked_payload_bytes": checked_bytes,
        "marker_roles": sorted(label for label, _ in encoded_markers),
        "volatile_absolute_path_bytes_found": False,
    }


def verify_installed_overlay(overlay_root, lock_records):
    overlay_root = Path(os.path.abspath(str(overlay_root)))
    site_packages_root = overlay_root / OVERLAY_SITE_PACKAGES_RELATIVE_PATH
    if object_kind(site_packages_root) != "DIRECTORY":
        raise CandidateConstructionError(
            "OVERLAY_SITE_PACKAGES_ROOT_NOT_DIRECTORY"
        )
    overlay_tree = bounded_physical_tree(
        overlay_root,
        OVERLAY_TREE_ENTRY_LIMIT,
        OVERLAY_TREE_TOTAL_BYTE_LIMIT,
        "OVERLAY_VERIFICATION_TREE",
    )
    actual_files = [
        path.relative_to(overlay_root).as_posix()
        for path in overlay_tree["files"]
    ]
    observed_sizes = {
        item["relative_path"]: item["size_bytes"]
        for item in overlay_tree["file_observations"]
    }
    dist_infos = [
        path
        for path in overlay_tree["directories"]
        if path.name.endswith(".dist-info")
        and path.parent == site_packages_root
    ]
    if len(dist_infos) > OVERLAY_DISTRIBUTION_LIMIT:
        raise CandidateConstructionError(
            "OVERLAY_DISTRIBUTION_LIMIT_EXCEEDED"
        )
    installed = {}
    declared_paths = set()
    ownership = {}
    payload_rows = []
    reopened_total_size = 0
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
        metadata_payload = read_regular_file_nofollow_bounded(
            metadata_path,
            OVERLAY_CONTROL_FILE_BYTE_LIMIT,
            "OVERLAY_METADATA_FILE",
        )
        message = email.parser.BytesParser().parsebytes(metadata_payload)
        name = normalized_name(message.get("Name", ""))
        version = message.get("Version")
        if not name or not version or name in installed:
            raise CandidateConstructionError("OVERLAY_DISTRIBUTION_IDENTITY_INVALID")
        installed[name] = version
        record_base = Path(os.path.abspath(str(dist_info.parent)))
        absolute_record_path = Path(os.path.abspath(str(record_path)))
        record_payload = read_regular_file_nofollow_bounded(
            record_path,
            OVERLAY_CONTROL_FILE_BYTE_LIMIT,
            "OVERLAY_RECORD_FILE",
        )
        try:
            record_text = record_payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                "OVERLAY_RECORD_NOT_UTF8"
            ) from error
        record_row_count = 0
        for row in csv.reader(io.StringIO(record_text)):
            record_row_count += 1
            if record_row_count > OVERLAY_RECORD_ROW_LIMIT:
                raise CandidateConstructionError(
                    "OVERLAY_RECORD_ROW_LIMIT_EXCEEDED"
                )
            if len(row) != 3:
                raise CandidateConstructionError("OVERLAY_RECORD_ROW_INVALID")
            relative_text, hash_field, size_field = row
            pure = PurePosixPath(relative_text)
            if (
                not relative_text
                or pure.is_absolute()
                or "\\" in relative_text
                or relative_text != pure.as_posix()
                or any(part in ("", ".") for part in pure.parts)
                or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in relative_text
                )
            ):
                raise CandidateConstructionError("OVERLAY_RECORD_PATH_UNSAFE")
            payload_path = Path(
                os.path.abspath(os.path.join(record_base, *pure.parts))
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
            digest, size, opened_mode, _ = sha256_regular_file_nofollow(
                payload_path,
                OVERLAY_SINGLE_FILE_BYTE_LIMIT,
                "OVERLAY_RECORD_PAYLOAD",
            )
            if size != observed_sizes.get(relative):
                raise CandidateConstructionError(
                    "OVERLAY_FILE_SIZE_CHANGED_AFTER_TREE_SCAN", relative
                )
            reopened_total_size += size
            if reopened_total_size > OVERLAY_TREE_TOTAL_BYTE_LIMIT:
                raise CandidateConstructionError(
                    "OVERLAY_TREE_TOTAL_BYTE_LIMIT_EXCEEDED"
                )
            if bool(hash_field) != bool(size_field):
                raise CandidateConstructionError(
                    "OVERLAY_RECORD_HASH_SIZE_PAIR_INCOMPLETE"
                )
            if hash_field:
                algorithm, separator, encoded = hash_field.partition("=")
                if separator != "=" or algorithm != "sha256":
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_NON_SHA256_HASH"
                    )
                padding = "=" * ((4 - len(encoded) % 4) % 4)
                try:
                    declared = base64.b64decode(
                        (encoded + padding).encode("ascii"),
                        altchars=b"-_",
                        validate=True,
                    ).hex()
                except (
                    UnicodeEncodeError,
                    ValueError,
                    base64.binascii.Error,
                ) as error:
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_HASH_ENCODING_INVALID"
                    ) from error
                if declared != digest:
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_HASH_MISMATCH"
                    )
                try:
                    declared_size = int(size_field)
                except ValueError as error:
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_SIZE_INVALID"
                    ) from error
                if declared_size != size:
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_SIZE_MISMATCH"
                    )
            elif payload_path != absolute_record_path:
                raise CandidateConstructionError(
                    "OVERLAY_RECORD_UNHASHED_NON_RECORD_FILE"
                )
            payload_rows.append(
                {
                    "relative_path": relative,
                    "sha256": digest,
                    "size_bytes": size,
                    "mode_octal": format(
                        0o755
                        if opened_mode & 0o111
                        else 0o644,
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
    if reopened_total_size != overlay_tree["total_file_size_bytes"]:
        raise CandidateConstructionError(
            "OVERLAY_TREE_AGGREGATE_SIZE_CHANGED"
        )
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
        or relative_path
        in (
            BUILDER_NOTEBOOK_RELATIVE_PATH.as_posix(),
            LAUNCHER_NOTEBOOK_RELATIVE_PATH.as_posix(),
        )
    )


def parse_git_index_stage(payload):
    records = {}
    for raw_entry in payload.split(b"\0"):
        if not raw_entry:
            continue
        metadata, separator, raw_path = raw_entry.partition(b"\t")
        if separator != b"\t":
            raise CandidateConstructionError("GIT_INDEX_ENTRY_INVALID")
        fields = metadata.split(b" ")
        if len(fields) != 3:
            raise CandidateConstructionError("GIT_INDEX_METADATA_INVALID")
        try:
            mode = fields[0].decode("ascii")
            object_id = fields[1].decode("ascii")
            stage = fields[2].decode("ascii")
            relative_path = raw_path.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                "GIT_INDEX_ENTRY_ENCODING_INVALID"
            ) from error
        pure = PurePosixPath(relative_path)
        if (
            pure.is_absolute()
            or "\\" in relative_path
            or relative_path != pure.as_posix()
            or any(part in ("", ".", "..") for part in pure.parts)
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in relative_path
            )
        ):
            raise CandidateConstructionError("GIT_INDEX_PATH_UNSAFE")
        if not is_provenance_bound_path(relative_path):
            continue
        if (
            mode not in ("100644", "100755")
            or re.fullmatch(r"[0-9a-f]{40}", object_id) is None
            or stage != "0"
            or relative_path in records
        ):
            raise CandidateConstructionError(
                "GIT_INDEX_SOURCE_ENTRY_INVALID",
                relative_path,
            )
        records[relative_path] = {
            "relative_path": relative_path,
            "git_mode": mode,
            "git_blob_sha1": object_id,
            "git_stage": 0,
        }
    return records


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
            or relative_path != pure.as_posix()
            or any(part in ("", ".", "..") for part in pure.parts)
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in relative_path
            )
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
    launcher_source_binding,
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
    if (
        type(launcher_source_binding) is not dict
        or launcher_source_binding.get("relative_path")
        != LAUNCHER_NOTEBOOK_RELATIVE_PATH.as_posix()
        or launcher_source_binding["relative_path"] in manifest_by_path
        or launcher_source_binding["relative_path"]
        == builder_source_binding["relative_path"]
    ):
        raise CandidateConstructionError(
            "HASH_FIRST_LAUNCHER_BINDING_INVALID"
        )
    bound_by_path = {
        **manifest_by_path,
        builder_source_binding["relative_path"]: builder_source_binding,
        launcher_source_binding["relative_path"]: launcher_source_binding,
    }
    manifest_paths = sorted(manifest_by_path)
    bound_paths = sorted(bound_by_path)
    index_records = parse_git_index_stage(index_paths_payload)
    index_paths = sorted(index_records)
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
        _, payload, observed_mode = read_physical_source_bytes(
            path, repo_root
        )
        current_sha256 = sha256_bytes(payload)
        current_size = len(payload)
        canonical_mode = 0o755 if observed_mode & 0o111 else 0o644
        expected_git_mode = "100755" if canonical_mode == 0o755 else "100644"
        git_blob_sha1 = hashlib.sha1(
            b"blob "
            + str(current_size).encode("ascii")
            + b"\0"
            + payload
        ).hexdigest()
        index_record = index_records[relative_path]
        head_record = head_records[relative_path]
        if (
            record.get("sha256") != current_sha256
            or record.get("size_bytes") != current_size
            or record.get("mode_octal") != format(canonical_mode, "04o")
            or index_record["git_mode"] != head_record["git_mode"]
            or index_record["git_blob_sha1"] != head_record["git_blob_sha1"]
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
                "git_index_matches_head": True,
                "sha256": current_sha256,
                "size_bytes": current_size,
                "mode_octal": format(canonical_mode, "04o"),
            }
        )
    return {
        "all_bound_paths_present_in_index_and_head": True,
        "all_bound_worktree_bytes_match_head_blobs": True,
        "construction_notebook_present_in_index_and_matches_head": True,
        "hash_first_launcher_present_in_index_and_matches_head": True,
        "whole_repository_cleanliness_checked": False,
        "unbound_worktree_paths_accessed": False,
        "bound_path_count": len(bound_paths),
        "manifest_path_count": len(manifest_paths),
        "manifest_paths_sha256": sha256_bytes(
            canonical_json_bytes(manifest_paths)
        ),
        "git_index_stage_stdout_sha256": sha256_bytes(index_paths_payload),
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
    launcher_source_binding=None,
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
    if launcher_source_binding is None:
        raise CandidateConstructionError(
            "HASH_FIRST_LAUNCHER_BINDING_REQUIRED_FOR_GIT_IDENTITY"
        )
    index_paths_payload = run_tool(
        journal,
        "git_index_source_stage",
        [
            *git,
            "ls-files",
            "--cached",
            "--stage",
            "-z",
            "--",
            "pyproject.toml",
            "README.md",
            "src/heterodiff",
            BUILDER_NOTEBOOK_RELATIVE_PATH.as_posix(),
            LAUNCHER_NOTEBOOK_RELATIVE_PATH.as_posix(),
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
            LAUNCHER_NOTEBOOK_RELATIVE_PATH.as_posix(),
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
        launcher_source_binding,
        index_paths_payload,
        head_tree_payload,
    )
    epoch_text = run_tool(
        journal,
        "git_commit_epoch",
        [*git, "show", "-s", "--format=%ct", revision],
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
    final_revision = run_tool(
        journal,
        "git_revision_recheck_before_build",
        [*git, "rev-parse", "--verify", "HEAD"],
        repo_root,
        git_environment,
        primary_url,
        torch_url,
        attempt_state,
        (),
        durable_attempt,
    ).decode("ascii").strip()
    if final_revision != revision:
        raise CandidateConstructionError("SOURCE_REVISION_CHANGED_DURING_BINDING")
    return revision, int(epoch_text), source_provenance


def safe_archive_relative_path(relative):
    text = relative.as_posix()
    pure = PurePosixPath(text)
    if (
        pure.is_absolute()
        or not text
        or text in (".", "..")
        or "\\" in text
        or any(part in ("", ".", "..") for part in pure.parts)
        or any(ord(character) < 32 for character in text)
    ):
        raise CandidateConstructionError("ARCHIVE_MEMBER_PATH_UNSAFE", text)
    return text


def staging_archive_members(source_root):
    source_root = Path(source_root)
    try:
        source_tree = bounded_physical_tree(
            source_root,
            ARCHIVE_TREE_ENTRY_LIMIT,
            PAYLOAD_ARCHIVE_BYTE_LIMIT,
            "STAGING_ARCHIVE_TREE",
        )
    except CandidateConstructionError as error:
        if error.code == "STAGING_ARCHIVE_TREE_NONPHYSICAL_ENTRY":
            raise CandidateConstructionError(
                "STAGING_ARCHIVE_UNSAFE_FILE", error.detail
            ) from error
        raise
    members = []
    hashed_size = 0
    observed_sizes = {
        item["relative_path"]: item["size_bytes"]
        for item in source_tree["file_observations"]
    }
    for path in source_tree["files"]:
        relative = path.relative_to(source_root)
        relative_text = safe_archive_relative_path(relative)
        if len(relative_text.encode("utf-8")) > ARCHIVE_MEMBER_NAME_BYTE_LIMIT:
            raise CandidateConstructionError(
                "STAGING_ARCHIVE_MEMBER_NAME_LIMIT_EXCEEDED"
            )
        remaining_bytes = PAYLOAD_ARCHIVE_BYTE_LIMIT - hashed_size
        if remaining_bytes < 0:
            raise CandidateConstructionError(
                "STAGING_ARCHIVE_TOTAL_BYTE_LIMIT_EXCEEDED"
            )
        digest, size, opened_mode, opened_link_count = (
            sha256_regular_file_nofollow(
                path,
                remaining_bytes,
                "STAGING_ARCHIVE_MEMBER",
            )
        )
        if opened_link_count != 1:
            raise CandidateConstructionError(
                "STAGING_ARCHIVE_HARD_LINK_NOT_PERMITTED", relative_text
            )
        if size != observed_sizes[relative_text]:
            raise CandidateConstructionError(
                "STAGING_ARCHIVE_FILE_SIZE_CHANGED_AFTER_TREE_SCAN",
                relative_text,
            )
        hashed_size += size
        source_mode = opened_mode & 0o777
        archive_mode = 0o755 if source_mode & 0o111 else 0o644
        members.append(
            {
                "relative_path": relative_text,
                "sha256": digest,
                "size_bytes": size,
                "mode_octal": format(archive_mode, "04o"),
                "_source_path": path,
            }
        )
        if len(members) > ARCHIVE_MEMBER_LIMIT:
            raise CandidateConstructionError(
                "STAGING_ARCHIVE_MEMBER_LIMIT_EXCEEDED"
            )
    if hashed_size != source_tree["total_file_size_bytes"]:
        raise CandidateConstructionError(
            "STAGING_ARCHIVE_TREE_SIZE_CHANGED_DURING_HASH"
        )
    names = [item["relative_path"] for item in members]
    if not members:
        raise CandidateConstructionError("STAGING_ARCHIVE_EMPTY")
    if len(names) != len(set(names)):
        raise CandidateConstructionError("STAGING_ARCHIVE_DUPLICATE_MEMBER")
    return members


def build_deterministic_candidate_archive(source_root, archive_path):
    if object_kind(archive_path) != "ABSENT":
        raise CandidateConstructionError("LOCAL_ARCHIVE_PATH_COLLISION")
    members = staging_archive_members(source_root)
    conservative_archive_bound = (
        ARCHIVE_CONSERVATIVE_FIXED_OVERHEAD_BYTES
        + sum(
            member["size_bytes"]
            + ARCHIVE_CONSERVATIVE_MEMBER_OVERHEAD_BYTES
            + 2 * len(member["relative_path"].encode("utf-8"))
            for member in members
        )
    )
    if conservative_archive_bound > PAYLOAD_ARCHIVE_BYTE_LIMIT:
        raise CandidateConstructionError(
            "LOCAL_ARCHIVE_CONSERVATIVE_SIZE_BOUND_EXCEEDED",
            str(conservative_archive_bound),
        )
    try:
        with zipfile.ZipFile(
            archive_path,
            mode="x",
            compression=zipfile.ZIP_STORED,
            allowZip64=True,
        ) as archive:
            for member in members:
                info = zipfile.ZipInfo(
                    member["relative_path"],
                    date_time=(1980, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = (
                    (stat.S_IFREG | int(member["mode_octal"], 8)) << 16
                )
                info.flag_bits |= 0x800
                member_size_written = 0
                member_digest = hashlib.sha256()
                source_descriptor = os.open(
                    member["_source_path"],
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                )
                try:
                    opened = os.fstat(source_descriptor)
                    if (
                        not stat.S_ISREG(opened.st_mode)
                        or opened.st_size != member["size_bytes"]
                        or opened.st_nlink != 1
                    ):
                        raise CandidateConstructionError(
                            "STAGING_ARCHIVE_SOURCE_BINDING_CHANGED",
                            member["relative_path"],
                        )
                    source = os.fdopen(
                        source_descriptor, "rb", closefd=False
                    )
                    with archive.open(info, mode="w", force_zip64=True) as target:
                        while True:
                            chunk = source.read(UC_READ_CHUNK_BYTES)
                            if not chunk:
                                break
                            member_size_written += len(chunk)
                            if member_size_written > member["size_bytes"]:
                                raise CandidateConstructionError(
                                    "STAGING_ARCHIVE_MEMBER_GREW_DURING_WRITE",
                                    member["relative_path"],
                                )
                            member_digest.update(chunk)
                            target.write(chunk)
                    source.close()
                    final = os.fstat(source_descriptor)
                finally:
                    os.close(source_descriptor)
                if (
                    member_size_written != member["size_bytes"]
                    or member_digest.hexdigest() != member["sha256"]
                    or final.st_size != member["size_bytes"]
                ):
                    raise CandidateConstructionError(
                        "STAGING_ARCHIVE_MEMBER_CHANGED_DURING_WRITE",
                        member["relative_path"],
                    )
                if archive_path.stat().st_size > PAYLOAD_ARCHIVE_BYTE_LIMIT:
                    raise CandidateConstructionError(
                        "LOCAL_ARCHIVE_SIZE_LIMIT_EXCEEDED_DURING_WRITE"
                    )
    except CandidateConstructionError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        raise CandidateConstructionError(
            "LOCAL_DETERMINISTIC_ARCHIVE_BUILD_FAILED",
            type(error).__name__,
        ) from error
    public_members = [
        {key: value for key, value in member.items() if key != "_source_path"}
        for member in members
    ]
    archive_descriptor = None

    def hash_archive_descriptor(descriptor, expected_size):
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        observed_size = 0
        while True:
            chunk = os.read(descriptor, UC_READ_CHUNK_BYTES)
            if not chunk:
                break
            observed_size += len(chunk)
            if observed_size > PAYLOAD_ARCHIVE_BYTE_LIMIT:
                raise CandidateConstructionError(
                    "LOCAL_ARCHIVE_EXPANDED_PAST_SIZE_LIMIT"
                )
            digest.update(chunk)
        final = os.fstat(descriptor)
        if observed_size != expected_size or final.st_size != expected_size:
            raise CandidateConstructionError(
                "LOCAL_ARCHIVE_SIZE_CHANGED_DURING_DESCRIPTOR_HASH"
            )
        return digest.hexdigest(), observed_size

    def verify_archive_descriptor(descriptor):
        os.lseek(descriptor, 0, os.SEEK_SET)
        duplicated = os.dup(descriptor)
        with os.fdopen(duplicated, "rb", closefd=True) as archive_file:
            with zipfile.ZipFile(archive_file, mode="r") as archive:
                infos = archive.infolist()
                if [info.filename for info in infos] != [
                    member["relative_path"] for member in public_members
                ]:
                    raise CandidateConstructionError(
                        "LOCAL_ARCHIVE_MEMBER_ORDER_MISMATCH"
                    )
                if archive.testzip() is not None:
                    raise CandidateConstructionError(
                        "LOCAL_ARCHIVE_MEMBER_CRC_MISMATCH"
                    )
                for info, member in zip(infos, public_members):
                    mode = (info.external_attr >> 16) & 0o777
                    if (
                        info.compress_type != zipfile.ZIP_STORED
                        or info.file_size != member["size_bytes"]
                        or format(mode, "04o") != member["mode_octal"]
                        or info.date_time != (1980, 1, 1, 0, 0, 0)
                    ):
                        raise CandidateConstructionError(
                            "LOCAL_ARCHIVE_MEMBER_METADATA_MISMATCH",
                            member["relative_path"],
                        )
                    digest = hashlib.sha256()
                    observed_size = 0
                    with archive.open(info, mode="r") as archived_member:
                        while True:
                            chunk = archived_member.read(UC_READ_CHUNK_BYTES)
                            if not chunk:
                                break
                            digest.update(chunk)
                            observed_size += len(chunk)
                            if observed_size > member["size_bytes"]:
                                raise CandidateConstructionError(
                                    "LOCAL_ARCHIVE_MEMBER_EXPANDED_DURING_"
                                    "VERIFICATION",
                                    member["relative_path"],
                                )
                    if (
                        digest.hexdigest() != member["sha256"]
                        or observed_size != member["size_bytes"]
                    ):
                        raise CandidateConstructionError(
                            "LOCAL_ARCHIVE_MEMBER_CONTENT_BINDING_MISMATCH",
                            member["relative_path"],
                        )

    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        archive_descriptor = os.open(archive_path, flags)
        opened = os.fstat(archive_descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size <= 0
            or opened.st_size > PAYLOAD_ARCHIVE_BYTE_LIMIT
            or opened.st_nlink != 1
        ):
            raise CandidateConstructionError(
                "LOCAL_ARCHIVE_DESCRIPTOR_OBJECT_INVALID"
            )
        initial_binding = hash_archive_descriptor(
            archive_descriptor, opened.st_size
        )
        verify_archive_descriptor(archive_descriptor)
        final_binding = hash_archive_descriptor(
            archive_descriptor, opened.st_size
        )
        final = os.fstat(archive_descriptor)
        if (
            final_binding != initial_binding
            or final.st_size != opened.st_size
            or final.st_nlink != 1
        ):
            raise CandidateConstructionError(
                "LOCAL_ARCHIVE_CHANGED_DURING_DESCRIPTOR_VERIFICATION"
            )
        archive_sha256, archive_size = final_binding
    except CandidateConstructionError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        raise CandidateConstructionError(
            "LOCAL_ARCHIVE_REOPEN_FAILED", type(error).__name__
        ) from error
    finally:
        if archive_descriptor is not None:
            os.close(archive_descriptor)
    return {
        "format": "ZIP_STORED_ZIP64",
        "sha256": archive_sha256,
        "size_bytes": archive_size,
        "member_count": len(public_members),
        "members": public_members,
        "members_sha256": sha256_bytes(canonical_json_bytes(public_members)),
        "timestamp_normalization": "1980-01-01T00:00:00",
        "descriptor_pinned_member_and_hash_verification": True,
    }


def plan_archive_chunks(
    archive_path, expected_archive_sha256=None, expected_archive_size=None
):
    descriptor = None

    def descriptor_hash(expected_size):
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, UC_READ_CHUNK_BYTES)
            if not chunk:
                break
            size += len(chunk)
            if size > PAYLOAD_ARCHIVE_BYTE_LIMIT:
                raise CandidateConstructionError(
                    "PAYLOAD_ARCHIVE_EXPANDED_PAST_SIZE_LIMIT"
                )
            digest.update(chunk)
        final = os.fstat(descriptor)
        if size != expected_size or final.st_size != expected_size:
            raise CandidateConstructionError(
                "PAYLOAD_ARCHIVE_SIZE_CHANGED_DURING_HASH"
            )
        return digest.hexdigest(), size

    try:
        descriptor = os.open(
            archive_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        )
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size <= 0
            or opened.st_size > PAYLOAD_ARCHIVE_BYTE_LIMIT
            or opened.st_nlink != 1
        ):
            raise CandidateConstructionError(
                "PAYLOAD_ARCHIVE_DESCRIPTOR_OBJECT_INVALID"
            )
        archive_sha256, archive_size = descriptor_hash(opened.st_size)
        if (
            expected_archive_sha256 is not None
            and (
                archive_sha256 != expected_archive_sha256
                or archive_size != expected_archive_size
            )
        ):
            raise CandidateConstructionError(
                "PAYLOAD_ARCHIVE_CHANGED_BEFORE_CHUNK_PLAN"
            )
        records = []
        offset = 0
        os.lseek(descriptor, 0, os.SEEK_SET)
        while offset < archive_size:
            ordinal = len(records)
            if ordinal >= PAYLOAD_CHUNK_LIMIT:
                raise CandidateConstructionError("PAYLOAD_CHUNK_LIMIT_EXCEEDED")
            target_size = min(PAYLOAD_CHUNK_BYTES, archive_size - offset)
            digest = hashlib.sha256()
            remaining = target_size
            while remaining:
                chunk = os.read(
                    descriptor, min(UC_READ_CHUNK_BYTES, remaining)
                )
                if not chunk:
                    raise CandidateConstructionError(
                        "PAYLOAD_ARCHIVE_TRUNCATED_DURING_CHUNK_PLAN"
                    )
                digest.update(chunk)
                remaining -= len(chunk)
            records.append(
                {
                    "ordinal": ordinal,
                    "name": candidate_chunk_leaf_name(ordinal),
                    "offset_bytes": offset,
                    "size_bytes": target_size,
                    "sha256": digest.hexdigest(),
                }
            )
            offset += target_size
        if os.read(descriptor, 1):
            raise CandidateConstructionError(
                "PAYLOAD_ARCHIVE_GREW_DURING_CHUNK_PLAN"
            )
        planned_size = sum(item["size_bytes"] for item in records)
        if offset != archive_size or planned_size != archive_size:
            raise CandidateConstructionError("PAYLOAD_CHUNK_PLAN_SIZE_MISMATCH")
        if descriptor_hash(opened.st_size) != (archive_sha256, archive_size):
            raise CandidateConstructionError(
                "PAYLOAD_ARCHIVE_CHANGED_DURING_PLAN"
            )
        final = os.fstat(descriptor)
        if final.st_nlink != 1:
            raise CandidateConstructionError(
                "PAYLOAD_ARCHIVE_LINK_COUNT_CHANGED_DURING_PLAN"
            )
        return records
    except CandidateConstructionError:
        raise
    except OSError as error:
        raise CandidateConstructionError(
            "PAYLOAD_ARCHIVE_DESCRIPTOR_ACCESS_FAILED",
            type(error).__name__,
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def verify_archive_evidence_consistency(
    archive,
    tool_records,
    runtime_records,
    prearchive_reverification,
    manifest_relative,
    manifest_file_sha256,
    manifest_size_bytes,
    overlay,
):
    archive_members = {
        member["relative_path"]: member for member in archive["members"]
    }
    expected_bindings = []
    for directory, records in (
        ("build-tool-wheelhouse", tool_records),
        ("wheelhouse", runtime_records),
    ):
        for record in records:
            expected_bindings.append(
                {
                    "relative_path": f'{directory}/{record["filename"]}',
                    "sha256": record["sha256"],
                    "size_bytes": record["size_bytes"],
                }
            )
    expected_bindings.extend(
        prearchive_reverification["control_files"].values()
    )
    expected_bindings.append(
        {
            "relative_path": manifest_relative.as_posix(),
            "sha256": manifest_file_sha256,
            "size_bytes": manifest_size_bytes,
        }
    )
    for expected in expected_bindings:
        observed = archive_members.get(expected["relative_path"])
        if observed is None or any(
            observed.get(key) != expected[key]
            for key in ("sha256", "size_bytes")
        ):
            raise CandidateConstructionError(
                "ARCHIVE_EVIDENCE_BINDING_MISMATCH",
                expected["relative_path"],
            )
    overlay_rows = []
    for relative_path, member in archive_members.items():
        if not relative_path.startswith("overlay/"):
            continue
        overlay_rows.append(
            {
                "relative_path": relative_path[len("overlay/"):],
                "sha256": member["sha256"],
                "size_bytes": member["size_bytes"],
                "mode_octal": member["mode_octal"],
            }
        )
    overlay_rows.sort(key=lambda item: item["relative_path"])
    if (
        len(overlay_rows) != overlay["regular_file_count"]
        or sha256_bytes(canonical_json_bytes(overlay_rows))
        != overlay["payload_manifest_sha256"]
    ):
        raise CandidateConstructionError(
            "ARCHIVE_OVERLAY_PAYLOAD_MANIFEST_MISMATCH"
        )
    expected_path_set = {
        binding["relative_path"] for binding in expected_bindings
    } | {
        "overlay/" + row["relative_path"] for row in overlay_rows
    }
    if (
        len(expected_path_set)
        != len(expected_bindings) + len(overlay_rows)
        or set(archive_members) != expected_path_set
    ):
        raise CandidateConstructionError(
            "ARCHIVE_CANDIDATE_PAYLOAD_CLOSURE_MISMATCH"
        )
    projection = {
        "wheel_and_control_binding_count": len(expected_bindings),
        "all_wheel_and_control_bindings_exact": True,
        "overlay_regular_file_count": len(overlay_rows),
        "overlay_payload_manifest_sha256": overlay[
            "payload_manifest_sha256"
        ],
        "overlay_payload_manifest_reconstructed_from_archive": True,
        "archive_candidate_path_set_exact": True,
    }
    return {
        **projection,
        "projection_sha256": sha256_bytes(canonical_json_bytes(projection)),
    }


def publish_candidate_archive(
    source_root,
    destination_binding,
    expected_intent_sha256,
    expected_intent_size,
    tool_records,
    runtime_records,
    prearchive_reverification,
    manifest_relative,
    manifest_file_sha256,
    manifest_size_bytes,
    overlay,
):
    archive_path = Path(source_root).parent / "candidate-payload.zip"
    archive = build_deterministic_candidate_archive(source_root, archive_path)
    archive["evidence_consistency"] = verify_archive_evidence_consistency(
        archive,
        tool_records,
        runtime_records,
        prearchive_reverification,
        manifest_relative,
        manifest_file_sha256,
        manifest_size_bytes,
        overlay,
    )
    chunks = plan_archive_chunks(
        archive_path,
        archive["sha256"],
        archive["size_bytes"],
    )
    store = destination_binding["store"]
    projected_chunks = [
        {
            **record,
            "binding": {
                "name": record["name"],
                "sha256": record["sha256"],
                "size_bytes": record["size_bytes"],
                "fresh_readback_count": 2,
            },
        }
        for record in chunks
    ]
    manifest = {
        "schema_version": "heterodiff-b08-n1-uc-native-payload-manifest-v1",
        "record_sha256": "0" * 64,
        "candidate_id": CANDIDATE_ID,
        "attempt_intent": destination_binding["intent"],
        "archive": archive,
        "chunks": projected_chunks,
        "limits": {
            "chunk_bytes": PAYLOAD_CHUNK_BYTES,
            "chunk_limit": PAYLOAD_CHUNK_LIMIT,
            "archive_byte_limit": PAYLOAD_ARCHIVE_BYTE_LIMIT,
        },
        "custody_model": {
            "basis": "REPEATABLE_EXACT_PATH_VISIBLE_SIZE_AND_SHA256_BINDINGS",
            "fresh_readbacks_per_created_object": 2,
            "atomic_snapshot_claimed": False,
            "cache_coherence_claimed": False,
            "future_fuse_stability_claimed": False,
            "historical_object_identity_or_lineage_claimed": False,
            "immutability_claimed": False,
            "physical_durability_claimed": False,
            "universal_atomicity_claimed": False,
        },
    }
    projection = dict(manifest)
    projection.pop("record_sha256")
    manifest["record_sha256"] = sha256_bytes(
        b"heterodiff/b08/n1/uc-native-payload-manifest/v1\0"
        + canonical_json_bytes(projection)
    )
    payload = canonical_json_bytes(manifest) + b"\n"
    if len(payload) > CONTROL_OBJECT_BYTE_LIMIT:
        raise CandidateConstructionError(
            "UC_PAYLOAD_MANIFEST_CONTROL_OBJECT_TOO_LARGE"
        )
    # The complete manifest and every resulting object binding are known and
    # bounded before the first payload-chunk create. Actual bindings must equal
    # this exact projection; no post-write manifest growth is possible.
    published_chunks = []
    for projected in projected_chunks:
        verify_durable_intent_custody(
            destination_binding,
            expected_intent_sha256,
            expected_intent_size,
        )
        binding = store.write_file_region(
            projected["name"],
            archive_path,
            projected["offset_bytes"],
            projected["size_bytes"],
            projected["sha256"],
        )
        if binding != projected["binding"]:
            raise CandidateConstructionError(
                "UC_PUBLISHED_CHUNK_BINDING_DIFFERS_FROM_PRECOMPUTED_MANIFEST",
                projected["name"],
            )
        published_chunks.append({**projected, "binding": binding})
    if published_chunks != projected_chunks:
        raise CandidateConstructionError(
            "UC_PUBLISHED_CHUNK_SEQUENCE_DIFFERS_FROM_PRECOMPUTED_MANIFEST"
        )
    verify_durable_intent_custody(
        destination_binding,
        expected_intent_sha256,
        expected_intent_size,
    )
    manifest_binding = store.write_bytes(PAYLOAD_MANIFEST_LEAF_NAME, payload)
    return {
        "archive": archive,
        "chunk_count": len(published_chunks),
        "chunks": published_chunks,
        "payload_manifest": manifest,
        "payload_manifest_binding": manifest_binding,
        "success_receipt_included": False,
    }


def verify_published_payload_before_success(
    destination_binding, publish_binding
):
    store = destination_binding["store"]
    expected_present_names = {
        ATTEMPT_INTENT_LEAF_NAME,
        PAYLOAD_MANIFEST_LEAF_NAME,
    }
    used_chunk_names = []
    for expected_ordinal, record in enumerate(publish_binding["chunks"]):
        name = record.get("name")
        ordinal = record.get("ordinal")
        if (
            type(ordinal) is not int
            or ordinal != expected_ordinal
            or type(name) is not str
            or name != candidate_chunk_leaf_name(ordinal)
            or name in expected_present_names
        ):
            raise CandidateConstructionError(
                "UC_PUBLISHED_CHUNK_NAMESPACE_INVALID"
            )
        expected_present_names.add(name)
        used_chunk_names.append(name)
    all_reserved_names = set(reserved_candidate_leaf_names())
    if not expected_present_names < all_reserved_names:
        raise CandidateConstructionError(
            "UC_PUBLISHED_PRESENT_NAMESPACE_INVALID"
        )
    expected_absent_names = sorted(
        all_reserved_names - expected_present_names
    )
    observed_nonabsent = []
    for name in expected_absent_names:
        kind = object_kind(CANDIDATE_PARENT / name)
        if kind != "ABSENT":
            observed_nonabsent.append({"name": name, "kind": kind})
    virtual_prefix_kind = object_kind(CANDIDATE_PREFIX)
    if observed_nonabsent or virtual_prefix_kind != "ABSENT":
        raise CandidateConstructionError(
            "UC_RESERVED_NAMESPACE_NOT_EXACT_BEFORE_SUCCESS",
            canonical_json_bytes(
                {
                    "nonabsent_reserved_leaves": observed_nonabsent,
                    "virtual_prefix_kind": virtual_prefix_kind,
                }
            ).decode("ascii"),
        )
    intent_expected = destination_binding["intent"]
    intent_observed = store.verify_binding(
        ATTEMPT_INTENT_LEAF_NAME,
        intent_expected["sha256"],
        intent_expected["size_bytes"],
    )
    if intent_observed != intent_expected:
        raise CandidateConstructionError(
            "UC_ATTEMPT_INTENT_CHANGED_BEFORE_SUCCESS"
        )
    manifest_expected = publish_binding["payload_manifest_binding"]
    manifest_observed = store.verify_binding(
        PAYLOAD_MANIFEST_LEAF_NAME,
        manifest_expected["sha256"],
        manifest_expected["size_bytes"],
    )
    chunk_bindings = []
    for record in publish_binding["chunks"]:
        expected = record["binding"]
        observed = store.verify_binding(
            record["name"],
            expected["sha256"],
            expected["size_bytes"],
        )
        chunk_bindings.append(observed)
    projection = {
        "basis": (
            "SEQUENTIAL_FRESH_PATH_VISIBLE_BINDING_AND_RESERVED_"
            "NAMESPACE_REVERIFICATION"
        ),
        "attempt_intent": intent_observed,
        "payload_manifest": manifest_observed,
        "chunks": chunk_bindings,
        "chunk_count": len(chunk_bindings),
        "used_chunk_names_sha256": sha256_bytes(
            canonical_json_bytes(sorted(used_chunk_names))
        ),
        "expected_present_reserved_leaf_count": len(expected_present_names),
        "expected_absent_reserved_leaf_count": len(expected_absent_names),
        "expected_absent_reserved_leaf_names_sha256": sha256_bytes(
            canonical_json_bytes(expected_absent_names)
        ),
        "all_expected_absent_reserved_leaves_observed_absent": True,
        "virtual_candidate_prefix_observed_absent": True,
        "reserved_namespace_projection_complete": (
            len(expected_present_names) + len(expected_absent_names)
            == len(all_reserved_names)
        ),
        "atomic_snapshot_claimed": False,
        "cache_coherence_claimed": False,
        "concurrent_external_namespace_mutation_excluded": False,
    }
    return {
        **projection,
        "projection_sha256": sha256_bytes(canonical_json_bytes(projection)),
    }


def initial_attempt_state():
    return {
        "attempt_namespace_spent": False,
        "intent_create_begun": False,
        "durable_intent_committed": False,
        "durable_intent_may_exist": False,
        "durable_intent_expected_sha256": None,
        "durable_intent_expected_size_bytes": None,
        "managed_uc_write_phase_entered": False,
        "managed_uc_write_begun": False,
        "managed_uc_exclusive_create_calls_begun": 0,
        "managed_uc_confirmed_leaf_count": 0,
        "managed_uc_confirmed_bytes_written": 0,
        "managed_uc_last_leaf_create_begun": None,
        "managed_uc_last_leaf_may_exist": None,
        "managed_uc_last_leaf_expected_sha256": None,
        "managed_uc_last_leaf_expected_size_bytes": None,
        "managed_uc_last_confirmed_binding": None,
        "managed_uc_confirmed_bindings": [],
        "staging_write_begun": False,
        "preintent_git_verification_begun": False,
        "preintent_git_verification_completed": False,
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
        "managed_uc_payload_publish_begun": False,
        "success_receipt_phase_entered": False,
        "success_receipt_create_call_begun": False,
        "success_receipt_may_exist": False,
        "success_receipt_committed": False,
        "failure_receipt_commit_begun": False,
        "failure_receipt_create_call_begun": False,
        "failure_receipt_may_exist": False,
        "failure_receipt_committed": False,
        "failure_receipt_error_code": None,
        "failure_receipt_error_detail": None,
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
    if attempt_state.get("success_receipt_create_call_begun") is True:
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
    probe_review_binding,
    probe_outcome_binding,
    preintent_git_binding,
    source_manifest,
    builder_binding,
    launcher_binding,
    review_package,
    hash_first_launch_evidence,
    destination_root,
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
            "uc_volume_probe_independent_review": probe_review_binding,
            "uc_volume_probe_001_outcome": probe_outcome_binding,
        },
        "source": {
            "git_revision": preintent_git_binding["revision"],
            "source_date_epoch": preintent_git_binding[
                "source_date_epoch"
            ],
            "git_revision_verification_state": (
                GIT_REVISION_VERIFICATION_STATE
            ),
            "preintent_git_provenance": preintent_git_binding[
                "provenance"
            ],
            "source_manifest_sha256": source_manifest["record_sha256"],
            "construction_notebook": builder_binding,
            "hash_first_launcher": launcher_binding,
        },
        "external_review_authority": {
            "review_package": review_package,
            "operator_authorized_review_package_sha256": review_package[
                "record_sha256"
            ],
            "authorization_matched_before_intent": True,
            "hash_first_launch_evidence": hash_first_launch_evidence,
        },
        "destination": {
            "virtual_candidate_prefix": destination_root.as_posix(),
            "parent": CANDIDATE_PARENT.as_posix(),
            "candidate_id": CANDIDATE_ID,
            "reserved_leaf_names": list(reserved_candidate_leaf_names()),
            "required_initial_state": "ALL_RESERVED_LEAVES_ABSENT",
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
            "external_concurrent_candidate_namespace_mutation_permitted": False,
            "uc_storage_protocol": "FLAT_APPEND_ONLY_EXCLUSIVE_CREATE",
            "payload_encoding": "DETERMINISTIC_ZIP_STORED_ZIP64_CHUNKS",
            "path_visible_binding": "EXACT_SIZE_AND_SHA256_TWO_FRESH_READBACKS",
            (
                "fsync_chmod_chown_inode_device_timestamp_rename_or_delete_"
                "used_for_uc_custody"
            ): False,
            "success_receipt_is_commit_marker": True,
        },
        "nonproofs": [
            "ATOMIC_SNAPSHOT",
            "CACHE_COHERENCE",
            "FUTURE_RUNTIME_OR_FUSE_STABILITY",
            "HISTORICAL_OBJECT_IDENTITY_OR_LINEAGE",
            "IMMUTABILITY",
            "PHYSICAL_DURABILITY",
            "LARGE_OBJECT_WRITE_GENERALIZATION_FROM_PROBE",
            "CAPACITY_OR_STORAGE_RESERVATION",
            "UNOBSERVED_NATIVE_PROFILE_TARGET_FIELDS",
            "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
            "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_STAGING_ABSENT",
            "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
            "UNIVERSAL_ATOMICITY",
        ],
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
        "attempt_state_before_failure_receipt_commit": (
            immutable_json_snapshot(attempt_state)
        ),
        "safety": {
            "base_runtime_install_target_requested_by_notebook": False,
            "study_or_test_data_path_requested_by_notebook": False,
            "spark_operation_requested_by_notebook": False,
            "databricks_rest_api_requested_by_notebook": False,
            "scientific_execution_requested_by_notebook": False,
            "canonical_repository_lock_write_requested_by_notebook": False,
            "child_process_external_file_access_audited": False,
            "child_process_side_effects_outside_staging_proven_absent": False,
        },
        "not_proven": [
            "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
            "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_STAGING_ABSENT",
            "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
        ],
    }
    del destination_root
    verify_durable_intent_custody(
        destination_binding,
        attempt_intent_sha256,
        destination_binding["intent"]["size_bytes"],
    )
    success_receipt_kind = object_kind(
        CANDIDATE_PARENT / SUCCESS_RECEIPT_LEAF_NAME
    )
    if success_receipt_kind != "ABSENT":
        raise CandidateConstructionError(
            "UC_SUCCESS_RECEIPT_VISIBLE_FAILURE_RECEIPT_SUPPRESSED",
            success_receipt_kind,
            telemetry={
                "terminal_receipt_ambiguity": True,
                "success_receipt_may_exist": True,
                "failure_receipt_skipped_for_terminal_receipt_ambiguity": (
                    True
                ),
                "success_receipt_leaf_name": SUCCESS_RECEIPT_LEAF_NAME,
                "success_receipt_observed_kind": success_receipt_kind,
            },
        )
    payload = canonical_json_bytes(receipt) + b"\n"
    store = destination_binding["store"]
    try:
        binding = store.write_bytes(
            FAILURE_RECEIPT_LEAF_NAME, payload
        )
    except BaseException as write_error:
        error_telemetry = (
            write_error.telemetry
            if isinstance(write_error, CandidateConstructionError)
            and write_error.telemetry is not None
            else {}
        )
        live_state = getattr(store, "attempt_state", None) or {}
        create_call_begun = (
            live_state.get("failure_receipt_create_call_begun") is True
            or error_telemetry.get("failure_receipt_may_exist") is True
            or error_telemetry.get("managed_uc_last_leaf_may_exist")
            == FAILURE_RECEIPT_LEAF_NAME
        )
        if not create_call_begun:
            if isinstance(write_error, CandidateConstructionError):
                raise write_error
            raise CandidateConstructionError(
                "UC_FAILURE_RECEIPT_PRE_CREATE_FAILED",
                type(write_error).__name__,
            ) from write_error
        write_code = (
            write_error.code
            if isinstance(write_error, CandidateConstructionError)
            else type(write_error).__name__
        )
        telemetry = {
            "failure_receipt_may_exist": True,
            "failure_receipt_leaf_name": FAILURE_RECEIPT_LEAF_NAME,
            "failure_receipt_write_error": write_code,
            "failure_receipt_expected_sha256": live_state.get(
                "managed_uc_last_leaf_expected_sha256"
            ),
            "failure_receipt_expected_size_bytes": live_state.get(
                "managed_uc_last_leaf_expected_size_bytes"
            ),
        }
        telemetry.update(error_telemetry)
        raise CandidateConstructionError(
            "UC_FAILURE_RECEIPT_COMMIT_AMBIGUOUS",
            write_code,
            telemetry=telemetry,
        ) from write_error
    return receipt, binding


def commit_success_receipt(
    destination_binding,
    expected_intent_sha256,
    expected_intent_size,
    payload,
):
    verify_durable_intent_custody(
        destination_binding,
        expected_intent_sha256,
        expected_intent_size,
    )
    store = destination_binding["store"]
    try:
        receipt_binding = store.write_bytes(
            SUCCESS_RECEIPT_LEAF_NAME, payload
        )
    except BaseException as write_error:
        error_telemetry = (
            write_error.telemetry
            if isinstance(write_error, CandidateConstructionError)
            and write_error.telemetry is not None
            else {}
        )
        live_state = getattr(store, "attempt_state", None) or {}
        create_call_begun = (
            live_state.get("success_receipt_create_call_begun") is True
            or error_telemetry.get("success_receipt_may_exist") is True
            or error_telemetry.get("managed_uc_last_leaf_may_exist")
            == SUCCESS_RECEIPT_LEAF_NAME
        )
        if not create_call_begun:
            if isinstance(write_error, CandidateConstructionError):
                raise write_error
            raise CandidateConstructionError(
                "UC_SUCCESS_RECEIPT_PRE_CREATE_FAILED",
                type(write_error).__name__,
            ) from write_error
        write_code = (
            write_error.code
            if isinstance(write_error, CandidateConstructionError)
            else type(write_error).__name__
        )
        telemetry = {
            "terminal_receipt_ambiguity": True,
            "success_receipt_may_exist": True,
            "success_receipt_leaf_name": SUCCESS_RECEIPT_LEAF_NAME,
            "success_receipt_write_error": write_code,
            "success_receipt_expected_sha256": live_state.get(
                "managed_uc_last_leaf_expected_sha256"
            ),
            "success_receipt_expected_size_bytes": live_state.get(
                "managed_uc_last_leaf_expected_size_bytes"
            ),
        }
        telemetry.update(error_telemetry)
        raise CandidateConstructionError(
            "UC_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS",
            write_code,
            telemetry=telemetry,
        ) from write_error
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
        provisional_environment = read_only_tool_environment()
        source_manifest = project_source_manifest(repo_root)
        if source_manifest != preflight_result["source_manifest"]:
            raise CandidateConstructionError(
                "PROJECT_SOURCE_MANIFEST_CHANGED_AFTER_PREFLIGHT"
            )
        builder_source_binding = regular_file_binding(
            repo_root,
            BUILDER_NOTEBOOK_RELATIVE_PATH,
            "BUILDER_NOTEBOOK",
        )
        if builder_source_binding != preflight_result[
            "builder_source_binding"
        ]:
            raise CandidateConstructionError(
                "BUILDER_SOURCE_BINDING_CHANGED_AFTER_PREFLIGHT"
            )
        launcher_source_binding = regular_file_binding(
            repo_root,
            LAUNCHER_NOTEBOOK_RELATIVE_PATH,
            "HASH_FIRST_LAUNCHER_NOTEBOOK",
        )
        if launcher_source_binding != preflight_result[
            "launcher_source_binding"
        ]:
            raise CandidateConstructionError(
                "HASH_FIRST_LAUNCHER_BINDING_CHANGED_AFTER_PREFLIGHT"
            )
        hash_first_launch_evidence = preflight_result[
            "hash_first_launch_evidence"
        ]
        if hash_first_launch_evidence is None:
            raise CandidateConstructionError(
                "HASH_FIRST_LAUNCH_EVIDENCE_REQUIRED"
            )
        attempt_state["preintent_git_verification_begun"] = True
        (
            preintent_revision,
            preintent_source_date_epoch,
            preintent_source_provenance,
        ) = git_identity(
            repo_root,
            journal,
            provisional_environment,
            primary_url,
            torch_url,
            None,
            None,
            source_manifest,
            builder_source_binding,
            launcher_source_binding,
        )
        preintent_git_binding = {
            "revision": preintent_revision,
            "source_date_epoch": preintent_source_date_epoch,
            "provenance": preintent_source_provenance,
        }
        expected_git_preflight = preflight_result.get(
            "source_git_preflight"
        )
        if (
            type(expected_git_preflight) is not dict
            or expected_git_preflight.get("exact") is not True
            or any(
                expected_git_preflight.get(key)
                != preintent_git_binding[key]
                for key in (
                    "revision",
                    "source_date_epoch",
                    "provenance",
                )
            )
        ):
            raise CandidateConstructionError(
                "SOURCE_GIT_BINDING_CHANGED_AFTER_PREFLIGHT"
            )
        review_package = candidate_review_package(
            source_manifest,
            builder_source_binding,
            launcher_source_binding,
            preintent_git_binding,
            profile_validation,
            preflight_result["v2_independent_review_binding"],
            preflight_result["uc_volume_probe_review_binding"],
            preflight_result["uc_volume_probe_outcome_binding"],
        )
        if (
            review_package != preflight_result["review_package"]
            or preflight_result["authorized_review_package_sha256"]
            != review_package["record_sha256"]
        ):
            raise CandidateConstructionError(
                "REVIEW_PACKAGE_AUTHORITY_CHANGED_AFTER_PREFLIGHT"
            )
        attempt_state["preintent_git_verification_completed"] = True
        attempt_intent, attempt_intent_bytes = build_attempt_intent(
            profile_validation,
            preflight_result["v2_independent_review_binding"],
            preflight_result["uc_volume_probe_review_binding"],
            preflight_result["uc_volume_probe_outcome_binding"],
            preintent_git_binding,
            source_manifest,
            builder_source_binding,
            launcher_source_binding,
            review_package,
            hash_first_launch_evidence,
            destination_root,
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
        attempt_state["command_journal"] = list(journal)
        detail = raw_pre_intent_error.code if isinstance(
            raw_pre_intent_error,
            CandidateConstructionError,
        ) else type(raw_pre_intent_error).__name__
        attempt_state["last_failed_step"] = "construct_pre_intent_bindings"
        raise CandidateConstructionError(
            "PRE_INTENT_CONSTRUCTION_FAILED",
            detail,
            telemetry=immutable_json_snapshot(attempt_state),
        ) from raw_pre_intent_error
    attempt_state["last_completed_step"] = "construct_pre_intent_bindings"
    attempt_state["managed_uc_write_phase_entered"] = True
    try:
        destination_binding = start_durable_attempt(
            destination_root,
            attempt_intent_bytes,
            attempt_state,
        )
    except BaseException as raw_start_error:
        error = (
            raw_start_error
            if isinstance(raw_start_error, CandidateConstructionError)
            else CandidateConstructionError(
                "UC_ATTEMPT_INTENT_START_FAILED",
                type(raw_start_error).__name__,
            )
        )
        if error.telemetry is not None:
            attempt_state.update(error.telemetry)
        attempt_state["last_failed_step"] = "commit_uc_attempt_intent"
        # A failed or ambiguous intent create has no safe authority for writing
        # a second terminal object. Preserve the namespace exactly as observed.
        raise CandidateConstructionError(
            error.code,
            error.detail,
            telemetry=immutable_json_snapshot(attempt_state),
        ) from raw_start_error
    attempt_state["durable_intent_committed"] = True
    attempt_state["last_completed_step"] = "commit_uc_attempt_intent"
    staging_root = None
    try:
        if destination_binding["intent"]["sha256"] != attempt_intent_sha256:
            raise CandidateConstructionError(
                "DURABLE_INTENT_BINDING_MISMATCH",
                telemetry=immutable_json_snapshot(attempt_state),
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
            launcher_source_binding,
        )
        if (
            revision != preintent_git_binding["revision"]
            or source_date_epoch
            != preintent_git_binding["source_date_epoch"]
            or source_provenance != preintent_git_binding["provenance"]
        ):
            raise CandidateConstructionError(
                "SOURCE_GIT_BINDING_CHANGED_AFTER_INTENT",
                telemetry=immutable_json_snapshot(attempt_state),
            )
        attempt_state["command_journal"] = list(journal)
        try:
            staging_root = Path(tempfile.mkdtemp(prefix="heterodiff-b08-n1-"))
            attempt_state["staging_write_begun"] = True
        except OSError as error:
            raise CandidateConstructionError(
                "STAGING_CREATION_FAILED",
                type(error).__name__,
                telemetry=immutable_json_snapshot(attempt_state),
            ) from error
        build_venv = staging_root / "build-venv"
        candidate_root = staging_root / "candidate"
        tool_wheelhouse = candidate_root / "build-tool-wheelhouse"
        runtime_wheelhouse = candidate_root / "wheelhouse"
        overlay_root = candidate_root / "overlay"
        copied_source = staging_root / "project-source"
        tool_temp_root = staging_root / "tool-tmp"
        candidate_root.mkdir(mode=0o750)
        tool_wheelhouse.mkdir(mode=0o750)
        runtime_wheelhouse.mkdir(mode=0o750)
        overlay_root.mkdir(mode=0o750)
        tool_temp_root.mkdir(mode=0o700)
        host_tool_environment = dict(provisional_environment)
        host_tool_environment.update(
            {
                "HOME": str(tool_temp_root),
                "NETRC": os.devnull,
                "XDG_CACHE_HOME": str(tool_temp_root),
                "XDG_CONFIG_HOME": str(tool_temp_root),
                "TMPDIR": str(tool_temp_root),
                "TMP": str(tool_temp_root),
                "TEMP": str(tool_temp_root),
                "PIP_CONFIG_FILE": os.devnull,
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_CACHE_DIR": "1",
                "PIP_NO_INPUT": "1",
            }
        )

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
            tool_temp_root,
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
            host_tool_environment,
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
                "--no-cache-dir",
                "--quiet",
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
        write_local_exclusive(tool_lock_path, lock_candidate_bytes(tool_records))
        run_tool(
            journal,
            "install_exact_build_tools_in_isolated_venv",
            [
                venv_python,
                "-m",
                "pip",
                "--isolated",
                "--no-cache-dir",
                "--quiet",
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
                "--no-cache-dir",
                "--quiet",
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
                "--no-cache-dir",
                "--quiet",
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
        write_local_exclusive(lock_path, lock_bytes)
        lock_sha256 = sha256_bytes(lock_bytes)

        run_tool(
            journal,
            "install_hash_locked_wheelhouse_to_isolated_overlay",
            [
                venv_python,
                "-m",
                "pip",
                "--isolated",
                "--no-cache-dir",
                "--quiet",
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
        entrypoint_normalization = normalize_overlay_entrypoint_shebangs(
            overlay_root, venv_python
        )
        overlay = verify_installed_overlay(overlay_root, runtime_records)
        final_isolated_pip_identity = bind_pip_identity(
            journal,
            "rebind_isolated_venv_pip_identity_before_manifest",
            venv_python,
            staging_root,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            destination_binding,
            required_bootstrap_pip_version(),
            expected_root=build_venv,
        )
        if portable_pip_identity_evidence(
            final_isolated_pip_identity, "ISOLATED_BUILD_VENV"
        ) != bootstrap_pip_binding["isolated_venv_pip_identity"]:
            raise CandidateConstructionError(
                "ISOLATED_PIP_IDENTITY_CHANGED_BEFORE_MANIFEST"
            )
        bootstrap_pip_binding[
            "isolated_venv_pip_identity_reverified_before_manifest"
        ] = True
        prearchive_reverification = (
            reverify_candidate_artifacts_before_manifest(
                candidate_root,
                tool_wheelhouse,
                runtime_wheelhouse,
                tool_records,
                runtime_records,
                tool_lock_path,
                lock_path,
                bootstrap_pip_binding,
            )
        )

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
                "path_visible_intent_binding": destination_binding["intent"],
                "virtual_candidate_prefix": CANDIDATE_PREFIX.as_posix(),
                "custody_model": {
                    "basis": "REPEATABLE_EXACT_PATH_VISIBLE_SIZE_AND_SHA256_BINDINGS",
                    "fresh_readbacks_per_created_object": 2,
                    "device_inode_permission_timestamp_acceptance": False,
                    "fsync_or_directory_fsync_claimed": False,
                    "atomic_snapshot_claimed": False,
                },
            },
            "profile": {
                "relative_path": PROFILE_RELATIVE_PATH.as_posix(),
                "file_sha256": profile_validation["file_sha256"],
                "semantic_sha256": profile_validation["semantic_sha256"],
                "independent_review": preflight_result[
                    "v2_independent_review_binding"
                ],
                "uc_volume_probe_independent_review": preflight_result[
                    "uc_volume_probe_review_binding"
                ],
                "uc_volume_probe_001_outcome": preflight_result[
                    "uc_volume_probe_outcome_binding"
                ],
            },
            "source": {
                "git_revision": revision,
                "bound_source_head_index_worktree_exact": True,
                "source_date_epoch": source_date_epoch,
                "manifest": source_manifest,
                "git_provenance": source_provenance,
                "construction_notebook": builder_source_binding,
                "hash_first_launcher": launcher_source_binding,
                "external_review_package": review_package,
                "hash_first_launch_evidence": hash_first_launch_evidence,
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
                "temporary_directory_policy": {
                    "staging_relative_path": "tool-tmp",
                    "tmpdir_tmp_and_temp_bound_to_staging": True,
                    "pip_no_cache_dir_cli_enforced": True,
                    "pip_config_file_devnull": True,
                    (
                        "outside_staging_temp_or_cache_requested_by_"
                        "notebook"
                    ): False,
                },
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
            "prearchive_artifact_reverification": prearchive_reverification,
            "overlay": overlay,
            "overlay_entrypoint_normalization": entrypoint_normalization,
            "overlay_install": {
                "prefix_isolated": True,
                "ignore_installed": True,
                "no_index": True,
                "require_hashes": True,
                "only_binary": True,
            },
            "command_journal": journal,
            "attempt_state_before_publish": immutable_json_snapshot(
                attempt_state
            ),
            "safety": {
                "base_runtime_install_target_requested_by_notebook": False,
                "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
                "databricks_rest_api_requested_by_notebook": False,
                "study_or_test_data_path_requested_by_notebook": False,
                "spark_operation_requested_by_notebook": False,
                "scientific_execution_requested_by_notebook": False,
                "project_or_scientific_import_requested_by_notebook": False,
                "canonical_repository_lock_write_requested_by_notebook": False,
                "tracker_or_timetable_edit_requested_by_notebook": False,
                "child_process_external_file_access_audited": False,
                (
                    "child_process_side_effects_outside_staging_"
                    "proven_absent"
                ): False,
            },
            "not_proven": [
                "ATOMIC_SNAPSHOT_OR_CACHE_COHERENCE",
                "FUTURE_RUNTIME_OR_FUSE_STABILITY",
                "HISTORICAL_OBJECT_IDENTITY_OR_LINEAGE",
                "IMMUTABILITY_OR_PHYSICAL_DURABILITY",
                "F152_INDEPENDENT_ACCEPTANCE",
                "F151_PRODUCTION_RUNTIME_MANIFEST",
                "F153_EFFECTIVE_WHOLE_RUNTIME_SATISFACTION",
                "UNOBSERVED_NATIVE_PROFILE_TARGET_FIELDS",
                "LARGE_OBJECT_WRITE_GENERALIZATION_FROM_PROBE",
                "CAPACITY_OR_STORAGE_RESERVATION",
                "DRIVER_WORKER_EQUIVALENCE",
                "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
                "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_STAGING_ABSENT",
                "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
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
        write_local_exclusive(manifest_path, manifest_bytes)
        manifest_file_sha256 = sha256_bytes(manifest_bytes)
        portability_verification = verify_candidate_has_no_volatile_path_bytes(
            candidate_root,
            (
                ("STAGING_ROOT", staging_root),
                ("REPOSITORY_ROOT", repo_root),
                ("HOST_PYTHON", Path(sys.executable).resolve()),
                ("HOST_PREFIX", Path(sys.prefix).resolve()),
            ),
        )

        receipt = {
            "schema_version": RECEIPT_SCHEMA,
            "decision": "CANDIDATE_CONSTRUCTED_REVIEW_REQUIRED_DO_NOT_INSTALL",
            "scope": "DATA_FREE_UC_NATIVE_ISOLATED_OVERLAY_CANDIDATE_003_ONLY",
            "uc_virtual_candidate_prefix": DURABLE_OUTPUT_DIRECTORY,
            "uc_parent": CANDIDATE_PARENT.as_posix(),
            "candidate_id": CANDIDATE_ID,
            "attempt_intent_sha256": attempt_intent_sha256,
            "attempt_intent_binding": destination_binding["intent"],
            "custody_model": {
                "basis": "REPEATABLE_EXACT_PATH_VISIBLE_SIZE_AND_SHA256_BINDINGS",
                "fresh_readbacks_per_created_object": 2,
                "flat_append_only_exclusive_create": True,
                "success_receipt_is_commit_marker": True,
                "device_inode_permission_timestamp_acceptance": False,
                "fsync_or_directory_fsync_claimed": False,
                "independent_reconstruction_and_review_required": True,
            },
            "profile_file_sha256": profile_validation["file_sha256"],
            "v2_independent_review_sha256": preflight_result[
                "v2_independent_review_binding"
            ]["sha256"],
            "uc_volume_probe_review_sha256": preflight_result[
                "uc_volume_probe_review_binding"
            ]["sha256"],
            "uc_volume_probe_outcome_sha256": preflight_result[
                "uc_volume_probe_outcome_binding"
            ]["sha256"],
            "source_revision": revision,
            "source_manifest_sha256": source_manifest["record_sha256"],
            "source_git_provenance": source_provenance,
            "construction_notebook": builder_source_binding,
            "hash_first_launcher": launcher_source_binding,
            "external_review_package": review_package,
            "hash_first_launch_evidence": hash_first_launch_evidence,
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
            "overlay_entrypoint_normalization": entrypoint_normalization,
            "candidate_portability_verification": portability_verification,
            "attempt_state_before_publish": immutable_json_snapshot(
                attempt_state
            ),
            "safety": {
                "network_resolution_executed_under_explicit_gate": True,
                "base_runtime_install_target_requested_by_notebook": False,
                "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
                "databricks_rest_api_requested_by_notebook": False,
                "all_runtime_artifacts_are_wheels": True,
                "sdist_accepted": False,
                "pip_no_cache_dir_cli_enforced": True,
                "all_tool_temporary_directories_bound_inside_staging": True,
                "reserved_uc_namespace_was_absent_at_preflight": True,
                "uc_publish_exclusive_create_no_clobber": True,
                "uc_object_fsync_chmod_chown_rename_or_delete_used": False,
                "study_or_test_data_path_requested_by_notebook": False,
                "spark_operation_requested_by_notebook": False,
                "scientific_execution_requested_by_notebook": False,
                "child_process_external_file_access_audited": False,
                (
                    "child_process_side_effects_outside_staging_"
                    "proven_absent"
                ): False,
            },
            "not_authorized": [
                "INSTALL_OVERLAY_IN_PRODUCTION_RUNTIME",
                "WRITE_CANONICAL_F152_LOCK",
                "F152_OR_F151_CLOSURE",
                "B08_OR_WAVE2_CLOSURE",
                "SCIENTIFIC_EXECUTION",
            ],
            "not_proven": [
                "ATOMIC_SNAPSHOT",
                "CACHE_COHERENCE",
                "FUTURE_RUNTIME_OR_FUSE_STABILITY",
                "HISTORICAL_OBJECT_IDENTITY_OR_LINEAGE",
                "IMMUTABILITY",
                "PHYSICAL_DURABILITY",
                "LARGE_OBJECT_WRITE_GENERALIZATION_FROM_PROBE",
                "CAPACITY_OR_STORAGE_RESERVATION",
                "UNOBSERVED_NATIVE_PROFILE_TARGET_FIELDS",
                "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
                "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_STAGING_ABSENT",
                "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
                "UNIVERSAL_ATOMICITY",
            ],
        }
        attempt_state["managed_uc_payload_publish_begun"] = True
        attempt_state["last_started_step"] = "publish_uc_payload_objects"
        verify_durable_intent_custody(
            destination_binding,
            attempt_intent_sha256,
            len(attempt_intent_bytes),
        )
        publish_binding = publish_candidate_archive(
            candidate_root,
            destination_binding,
            attempt_intent_sha256,
            len(attempt_intent_bytes),
            tool_records,
            runtime_records,
            prearchive_reverification,
            manifest_relative,
            manifest_file_sha256,
            len(manifest_bytes),
            overlay,
        )
        attempt_state["last_completed_step"] = "publish_uc_payload_objects"

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
                telemetry=immutable_json_snapshot(attempt_state),
            ) from cleanup_error
        staging_root = None
        attempt_state["staging_cleanup_completed"] = True
        attempt_state["last_completed_step"] = "cleanup_staging_before_success"

        attempt_state["last_started_step"] = (
            "reverify_uc_payload_before_success_receipt"
        )
        receipt["precommit_path_visible_verification"] = (
            verify_published_payload_before_success(
                destination_binding, publish_binding
            )
        )
        verify_durable_intent_custody(
            destination_binding,
            attempt_intent_sha256,
            len(attempt_intent_bytes),
        )
        attempt_state["last_completed_step"] = (
            "reverify_uc_payload_before_success_receipt"
        )

        receipt["uc_payload"] = {
            "archive": {
                "format": publish_binding["archive"]["format"],
                "sha256": publish_binding["archive"]["sha256"],
                "size_bytes": publish_binding["archive"]["size_bytes"],
                "member_count": publish_binding["archive"]["member_count"],
                "members_sha256": publish_binding["archive"]["members_sha256"],
            },
            "chunk_count": publish_binding["chunk_count"],
            "payload_manifest_semantic_sha256": publish_binding[
                "payload_manifest"
            ]["record_sha256"],
            "payload_manifest_binding": publish_binding[
                "payload_manifest_binding"
            ],
        }
        attempt_state["success_receipt_phase_entered"] = True
        attempt_state["last_started_step"] = "commit_success_receipt"
        receipt["attempt_state_before_success_receipt_commit"] = (
            immutable_json_snapshot(attempt_state)
        )
        receipt_bytes = canonical_json_bytes(receipt) + b"\n"
        if len(receipt_bytes) > CONTROL_OBJECT_BYTE_LIMIT:
            raise CandidateConstructionError(
                "UC_SUCCESS_RECEIPT_CONTROL_OBJECT_TOO_LARGE"
            )
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
            "attempt_state": immutable_json_snapshot(attempt_state),
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
                telemetry=immutable_json_snapshot(attempt_state),
            ) from raw_error
        attempt_state["failure_receipt_commit_begun"] = True
        try:
            _, failure_binding = commit_failure_receipt(
                destination_root,
                destination_binding,
                attempt_intent_sha256,
                construction_error,
                immutable_json_snapshot(attempt_state),
            )
        except BaseException as receipt_error:
            if (
                isinstance(receipt_error, CandidateConstructionError)
                and receipt_error.telemetry is not None
            ):
                attempt_state.update(receipt_error.telemetry)
            receipt_error_code = (
                receipt_error.code
                if isinstance(receipt_error, CandidateConstructionError)
                else type(receipt_error).__name__
            )
            if isinstance(receipt_error, CandidateConstructionError):
                receipt_error_detail = (
                    None
                    if receipt_error.detail is None
                    else str(receipt_error.detail)[:4096]
                )
            else:
                receipt_error_detail = None
            attempt_state["failure_receipt_error_code"] = (
                receipt_error_code
            )
            attempt_state["failure_receipt_error_detail"] = (
                receipt_error_detail
            )
            if attempt_state.get("terminal_receipt_ambiguity") is True:
                attempt_state[
                    "failure_receipt_skipped_for_terminal_receipt_ambiguity"
                ] = True
                raise CandidateConstructionError(
                    construction_error.code,
                    construction_error.detail,
                    telemetry=immutable_json_snapshot(attempt_state),
                ) from receipt_error
            if attempt_state.get("failure_receipt_create_call_begun") is True:
                attempt_state["failure_receipt_may_exist"] = True
            attempt_state["failure_receipt_error"] = type(receipt_error).__name__
            raise CandidateConstructionError(
                "FAILURE_RECEIPT_COMMIT_FAILED",
                (
                    f"construction={construction_error.code};"
                    f"receipt={receipt_error_code}"
                ),
                telemetry=immutable_json_snapshot(attempt_state),
            ) from receipt_error
        attempt_state["failure_receipt_committed"] = True
        attempt_state["failure_receipt_binding"] = failure_binding
        raise CandidateConstructionError(
            construction_error.code,
            construction_error.detail,
            telemetry=immutable_json_snapshot(attempt_state),
        ) from raw_error


def public_preflight_result(result):
    return {
        key: value
        for key, value in result.items()
        if key
        not in (
            "repo_root",
            "profile",
            "primary_index",
            "torch_index",
            "source_manifest",
        )
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
            "direct_external_network_or_contact_accessed": False,
            "databricks_managed_uc_metadata_io_may_have_been_performed": True,
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
            visible_control_objects = {}
            for name in (
                ATTEMPT_INTENT_LEAF_NAME,
                PAYLOAD_MANIFEST_LEAF_NAME,
                SUCCESS_RECEIPT_LEAF_NAME,
                FAILURE_RECEIPT_LEAF_NAME,
            ):
                try:
                    visible_control_objects[name] = object_kind(
                        CANDIDATE_PARENT / name
                    )
                except OSError:
                    visible_control_objects[name] = "UNAVAILABLE"
            success_receipt_outcome_ambiguous = bool(
                telemetry.get("terminal_receipt_ambiguity")
                or telemetry.get("success_receipt_may_exist")
                or visible_control_objects[SUCCESS_RECEIPT_LEAF_NAME]
                != "ABSENT"
            )
            if success_receipt_outcome_ambiguous:
                telemetry = dict(telemetry)
                telemetry["terminal_receipt_ambiguity"] = True
                telemetry["success_receipt_may_exist"] = True
            result = {
                "schema_version": RECEIPT_SCHEMA,
                "decision": (
                    (
                        "TERMINAL_SUCCESS_RECEIPT_OUTCOME_"
                        "AMBIGUOUS_REVIEW_REQUIRED"
                    )
                    if success_receipt_outcome_ambiguous
                    else "TERMINAL_NO_GO_SPENT_ATTEMPT_REVIEW_REQUIRED"
                    if (
                        telemetry.get("attempt_namespace_spent")
                        or telemetry.get("durable_intent_committed")
                        or telemetry.get("durable_intent_may_exist")
                    )
                    else "NO_GO_CANDIDATE_CONSTRUCTION_FAILED_BEFORE_INTENT"
                ),
                "error_code": error.code,
                "error_detail": error.detail,
                "attempt_state": telemetry,
                "success_receipt_outcome_ambiguous": (
                    success_receipt_outcome_ambiguous
                ),
                "uc_virtual_candidate_prefix": DURABLE_OUTPUT_DIRECTORY,
                "uc_control_object_kinds_after_failure": visible_control_objects,
                "safety": {
                    "base_runtime_install_target_requested_by_notebook": False,
                    "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
                    "databricks_rest_api_requested_by_notebook": False,
                    "study_or_test_data_path_requested_by_notebook": False,
                    "spark_operation_requested_by_notebook": False,
                    "scientific_execution_requested_by_notebook": False,
                    (
                        "canonical_repository_lock_write_requested_"
                        "by_notebook"
                    ): False,
                    "child_process_external_file_access_audited": False,
                    (
                        "child_process_side_effects_outside_staging_"
                        "proven_absent"
                    ): False,
                    (
                        "databricks_managed_uc_metadata_io_may_have_"
                        "been_performed"
                    ): True,
                },
                "not_proven": [
                    "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
                    (
                        "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_"
                        "STAGING_ABSENT"
                    ),
                    "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
                ],
            }
        print(json.dumps(result, indent=2, sort_keys=True))
