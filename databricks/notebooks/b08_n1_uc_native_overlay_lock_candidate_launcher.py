# Databricks notebook source
# MAGIC %md
# MAGIC # B08 N1 — hash-first launcher for candidate-003
# MAGIC
# MAGIC This small launcher is the only reviewed entrypoint for the UC-native
# MAGIC candidate-003 builder. It reads the tracked builder once, rejects links
# MAGIC and oversized payloads, verifies the exact externally supplied SHA-256,
# MAGIC and then compiles and executes those same in-memory bytes. Before control
# MAGIC transfers to the builder, the launcher performs no network, Spark, REST,
# MAGIC study-data, package, or filesystem-write operation.
# MAGIC The active launcher cannot cryptographically self-attest its own bytes:
# MAGIC executing the exact reviewed, Git-tracked launcher is the operator-held
# MAGIC procedural trust anchor. Its launch evidence is therefore an operator-
# MAGIC attested binding, not an unforgeable self-attestation.

# COMMAND ----------

from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import stat


BUILDER_RELATIVE_PATH = PurePosixPath(
    "databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py"
)
LAUNCHER_RELATIVE_PATH = PurePosixPath(
    "databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate_launcher.py"
)
BUILDER_BYTE_LIMIT = 4 * 1024 * 1024
LAUNCH_SCHEMA = "heterodiff-b08-n1-hash-first-launch-v1"
_DBUTILS = globals().get("dbutils")


def launcher_parameter():
    name = "b08_n1_uc_native_launcher_expected_builder_sha256"
    default = "NOT_AUTHORIZED"
    if _DBUTILS is None:
        return os.environ.get(
            "HETERODIFF_B08_N1_UC_NATIVE_LAUNCHER_EXPECTED_BUILDER_SHA256",
            default,
        )
    _DBUTILS.widgets.text(
        name,
        default,
        "Exact independently reviewed candidate-003 builder SHA-256",
    )
    return _DBUTILS.widgets.get(name)


def physical_relative_kind(root, relative):
    root = Path(root)
    relative = Path(relative.as_posix())
    if relative.is_absolute() or any(
        part in ("", ".", "..") for part in relative.parts
    ):
        return "INVALID"
    try:
        root_mode = root.lstat().st_mode
    except OSError:
        return "UNAVAILABLE"
    if not stat.S_ISDIR(root_mode):
        return "INVALID"
    current = root
    for ordinal, part in enumerate(relative.parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return "ABSENT"
        except OSError:
            return "UNAVAILABLE"
        is_last = ordinal == len(relative.parts) - 1
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


def locate_repo_root():
    candidates = []
    source_hint = globals().get("__file__")
    if isinstance(source_hint, (str, os.PathLike)) and str(source_hint):
        source_parent = Path(source_hint).expanduser().resolve().parent
        candidates.extend([source_parent, *source_parent.parents])
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])
    override = os.environ.get("HETERODIFF_REPO_ROOT_OVERRIDE")
    if override:
        candidates.insert(0, Path(override).expanduser().resolve())
    for candidate in dict.fromkeys(candidates):
        if (
            physical_relative_kind(
                candidate, PurePosixPath("pyproject.toml")
            )
            == "REGULAR_FILE"
            and physical_relative_kind(
                candidate, PurePosixPath("src/heterodiff")
            )
            == "DIRECTORY"
            and physical_relative_kind(candidate, BUILDER_RELATIVE_PATH)
            == "REGULAR_FILE"
            and physical_relative_kind(candidate, LAUNCHER_RELATIVE_PATH)
            == "REGULAR_FILE"
        ):
            return candidate
    raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")


def read_open_descriptor_once(descriptor):
    body_error = None
    payload = bytearray()
    try:
        observed = os.fstat(descriptor)
        if not stat.S_ISREG(observed.st_mode):
            raise RuntimeError("BUILDER_NOT_REGULAR_FILE")
        if observed.st_size <= 0 or observed.st_size > BUILDER_BYTE_LIMIT:
            raise RuntimeError("BUILDER_SIZE_OUT_OF_BOUNDS")
        while len(payload) <= BUILDER_BYTE_LIMIT:
            chunk = os.read(descriptor, min(1024 * 1024, BUILDER_BYTE_LIMIT + 1))
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) != observed.st_size:
            raise RuntimeError("BUILDER_SIZE_CHANGED_DURING_READ")
    except BaseException as error:
        body_error = error
    if body_error is not None:
        raise body_error
    return bytes(payload)


def read_builder_once(path):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open(path, flags)
    try:
        return read_open_descriptor_once(descriptor)
    finally:
        os.close(descriptor)


def read_repository_file_once(repo_root, relative_path):
    if physical_relative_kind(repo_root, relative_path) != "REGULAR_FILE":
        raise RuntimeError("REPOSITORY_FILE_NOT_PHYSICAL_REGULAR_FILE")
    relative = Path(relative_path.as_posix())
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    directory_descriptors = []
    leaf_descriptor = None
    try:
        current = os.open(repo_root, directory_flags)
        directory_descriptors.append(current)
        for part in relative.parts[:-1]:
            current = os.open(
                part,
                directory_flags,
                dir_fd=current,
            )
            directory_descriptors.append(current)
        leaf_descriptor = os.open(
            relative.parts[-1],
            file_flags,
            dir_fd=current,
        )
        return read_open_descriptor_once(leaf_descriptor)
    finally:
        if leaf_descriptor is not None:
            os.close(leaf_descriptor)
        for descriptor in reversed(directory_descriptors):
            os.close(descriptor)


def main():
    expected_sha256 = launcher_parameter()
    repo_root = locate_repo_root()
    builder_path = repo_root / Path(BUILDER_RELATIVE_PATH.as_posix())
    payload = read_repository_file_once(repo_root, BUILDER_RELATIVE_PATH)
    launcher_payload = read_repository_file_once(
        repo_root, LAUNCHER_RELATIVE_PATH
    )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    observed_size = len(payload)
    launcher_sha256 = hashlib.sha256(launcher_payload).hexdigest()
    launcher_size = len(launcher_payload)
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256 or "") is None:
        print(
            json.dumps(
                {
                    "decision": "HOLD_REVIEWED_BUILDER_SHA256_REQUIRED",
                    "builder_relative_path": BUILDER_RELATIVE_PATH.as_posix(),
                    "observed_builder_sha256": observed_sha256,
                    "observed_builder_size_bytes": observed_size,
                    "required_input": (
                        "64-lowerhex independently reviewed builder SHA-256"
                    ),
                    "builder_executed": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if expected_sha256 != observed_sha256:
        print(
            json.dumps(
                {
                    "decision": "STOP_REVIEWED_BUILDER_SHA256_MISMATCH",
                    "builder_relative_path": BUILDER_RELATIVE_PATH.as_posix(),
                    "operator_expected_builder_sha256": expected_sha256,
                    "observed_builder_sha256": observed_sha256,
                    "observed_builder_size_bytes": observed_size,
                    "builder_executed": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    launch_evidence = {
        "schema_version": LAUNCH_SCHEMA,
        "builder_relative_path": BUILDER_RELATIVE_PATH.as_posix(),
        "operator_expected_builder_sha256": expected_sha256,
        "executed_payload_sha256": observed_sha256,
        "executed_payload_size_bytes": observed_size,
        "launcher_relative_path": LAUNCHER_RELATIVE_PATH.as_posix(),
        "launcher_source_sha256": launcher_sha256,
        "launcher_source_size_bytes": launcher_size,
        "same_in_memory_payload_compiled_and_executed": True,
    }
    namespace = {
        "__builtins__": __builtins__,
        "__file__": str(builder_path),
        "__name__": "__main__",
        "dbutils": _DBUTILS,
        "HETERODIFF_HASH_FIRST_LAUNCH_EVIDENCE": launch_evidence,
    }
    code = compile(payload, str(builder_path), "exec")
    exec(code, namespace, namespace)


main()
