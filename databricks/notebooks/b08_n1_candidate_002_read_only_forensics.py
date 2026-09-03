# Databricks notebook source
# MAGIC %md
# MAGIC # B08 N1 candidate-002 read-only forensic inventory
# MAGIC
# MAGIC This notebook performs one bounded, control-evidence-only inspection of
# MAGIC the spent `candidate-002` directory. It does not create, modify, rename,
# MAGIC chmod, delete, or repair any object. It does not use Spark, the
# MAGIC Databricks REST API, a direct external endpoint, package tooling, study
# MAGIC data, calibration, training, or inference. Reading `/Volumes` does use
# MAGIC Databricks-managed storage I/O through the mounted FUSE path.

# COMMAND ----------

import hashlib
import json
import os
import stat


SCHEMA_VERSION = "heterodiff-b08-n1-candidate-002-read-only-forensics-v1"
EXACT_TARGET_DIRECTORY = (
    "/Volumes/development/team_eds_supplychain/b08_runtime_output/"
    "b08-n1-overlay-candidate-002"
)
EXPECTED_ROOT_DEVICE = 86
EXPECTED_ROOT_INODE = 8
EXPECTED_INTENT_SHA256 = (
    "cf85b36123e72c2e23be2796ab70cc9056af5578c648545edeb13a3ce24759ae"
)
EXPECTED_INTENT_SIZE_BYTES = 2322
EXPECTED_LEAF_NAMES = (
    "attempt-intent.json",
    "construction-failure-receipt.json",
)
MAX_VISIBLE_LEAF_COUNT = 8
MAX_VISIBLE_LEAF_NAME_BYTES = 255
MAX_CONTROL_LEAF_BYTES = 1024 * 1024


def kind_from_mode(mode):
    if stat.S_ISREG(mode):
        return "REGULAR_FILE"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    if stat.S_ISFIFO(mode):
        return "FIFO"
    if stat.S_ISSOCK(mode):
        return "SOCKET"
    if stat.S_ISCHR(mode):
        return "CHARACTER_DEVICE"
    if stat.S_ISBLK(mode):
        return "BLOCK_DEVICE"
    return "OTHER"


def stat_projection(observed):
    return {
        "device": observed.st_dev,
        "inode": observed.st_ino,
        "kind": kind_from_mode(observed.st_mode),
        "mode_octal": format(stat.S_IMODE(observed.st_mode), "04o"),
        "size_bytes": observed.st_size,
    }


def stable_stat_identity(observed):
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_mode,
        observed.st_size,
        observed.st_mtime_ns,
    )


def hash_regular_leaf(
    directory_descriptor,
    name,
    expected_stat,
    observation_state,
):
    if expected_stat.st_size > MAX_CONTROL_LEAF_BYTES:
        return {
            "payload_read": False,
            "payload_read_skip_reason": "CONTROL_LEAF_SIZE_EXCEEDS_BOUND",
        }
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    observation_state["control_leaf_payload_read_may_have_been_performed"] = True
    descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    try:
        before_read = os.fstat(descriptor)
        if not stat.S_ISREG(before_read.st_mode):
            raise RuntimeError("OPENED_LEAF_NOT_REGULAR")
        if (
            before_read.st_dev,
            before_read.st_ino,
        ) != (
            expected_stat.st_dev,
            expected_stat.st_ino,
        ):
            raise RuntimeError("LEAF_BINDING_CHANGED_DURING_READ")
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            if size > MAX_CONTROL_LEAF_BYTES:
                raise RuntimeError("CONTROL_LEAF_READ_EXCEEDS_BOUND")
        after_read = os.fstat(descriptor)
        if stable_stat_identity(before_read) != stable_stat_identity(after_read):
            raise RuntimeError("LEAF_CHANGED_DURING_READ")
        if size != after_read.st_size:
            raise RuntimeError("LEAF_READ_SIZE_MISMATCH")
        return {
            "payload_read": True,
            "sha256": digest.hexdigest(),
            "read_size_bytes": size,
        }
    finally:
        os.close(descriptor)


def classify_intent(entry):
    if entry is None:
        return "ATTEMPT_INTENT_NOT_VISIBLE"
    if entry["kind"] != "REGULAR_FILE":
        return "ATTEMPT_INTENT_NOT_REGULAR"
    size = entry["size_bytes"]
    digest = entry.get("sha256")
    if size == 0:
        return "ZERO_BYTE_INTENT_VISIBLE_FAILURE_BEFORE_PAYLOAD_WRITE_LIKELY"
    if size < EXPECTED_INTENT_SIZE_BYTES:
        return "PARTIAL_INTENT_PAYLOAD_VISIBLE"
    if (
        size == EXPECTED_INTENT_SIZE_BYTES
        and digest == EXPECTED_INTENT_SHA256
    ):
        return "COMPLETE_EXPECTED_INTENT_PAYLOAD_VISIBLE"
    return "INTENT_PAYLOAD_MISMATCH_VISIBLE"


def inspect_spent_attempt(
    path,
    expected_root_device,
    expected_root_inode,
    observation_state,
):
    observation_state["filesystem_read_attempted"] = True
    root_lstat = os.lstat(path)
    if not stat.S_ISDIR(root_lstat.st_mode) or stat.S_ISLNK(root_lstat.st_mode):
        raise RuntimeError("SPENT_ATTEMPT_ROOT_NOT_PHYSICAL_DIRECTORY")
    if (
        root_lstat.st_dev,
        root_lstat.st_ino,
    ) != (
        expected_root_device,
        expected_root_inode,
    ):
        raise RuntimeError("REPORTED_SPENT_ATTEMPT_ROOT_BINDING_MISMATCH")

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    directory_descriptor = os.open(path, flags)
    try:
        root_fstat = os.fstat(directory_descriptor)
        if (
            root_fstat.st_dev,
            root_fstat.st_ino,
        ) != (
            root_lstat.st_dev,
            root_lstat.st_ino,
        ):
            raise RuntimeError("SPENT_ATTEMPT_ROOT_BINDING_CHANGED_DURING_OPEN")

        names = []
        iterator = os.scandir(directory_descriptor)
        try:
            for visible in iterator:
                if len(names) >= MAX_VISIBLE_LEAF_COUNT:
                    raise RuntimeError("VISIBLE_LEAF_COUNT_EXCEEDS_BOUND")
                name = visible.name
                if (
                    type(name) is not str
                    or not name
                    or "/" in name
                    or "\\" in name
                    or len(name.encode("utf-8")) > MAX_VISIBLE_LEAF_NAME_BYTES
                ):
                    raise RuntimeError("INVALID_VISIBLE_LEAF_NAME")
                names.append(name)
        finally:
            iterator.close()
        names.sort()

        entries = []
        for name in names:
            observed = os.stat(
                name,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            entry = {
                "name": name,
                "payload_read": False,
                **stat_projection(observed),
            }
            if (
                name in EXPECTED_LEAF_NAMES
                and stat.S_ISREG(observed.st_mode)
            ):
                entry.update(
                    hash_regular_leaf(
                        directory_descriptor,
                        name,
                        observed,
                        observation_state,
                    )
                )
                if entry.get("payload_read") is True:
                    observation_state[
                        "control_leaf_payload_read_performed"
                    ] = True
            entries.append(entry)

        final_descriptor_stat = os.fstat(directory_descriptor)
        if stable_stat_identity(root_fstat) != stable_stat_identity(
            final_descriptor_stat
        ):
            raise RuntimeError("SPENT_ATTEMPT_ROOT_CHANGED_DURING_INVENTORY")
        final_declared_stat = os.lstat(path)
        if (
            stable_stat_identity(root_fstat)
            != stable_stat_identity(final_declared_stat)
        ):
            raise RuntimeError("SPENT_ATTEMPT_DECLARED_PATH_REBOUND")
    finally:
        os.close(directory_descriptor)

    by_name = {entry["name"]: entry for entry in entries}
    intent = by_name.get("attempt-intent.json")
    return {
        "schema_version": SCHEMA_VERSION,
        "decision": "READ_ONLY_FORENSIC_INVENTORY_COMPLETE",
        "target_directory": path,
        "target_matches_frozen_path": path == EXACT_TARGET_DIRECTORY,
        "root": stat_projection(root_lstat),
        "root_matches_reported_attempt_binding": True,
        "visible_leaf_names": names,
        "entries": entries,
        "unexpected_leaf_names": sorted(
            set(names).difference(EXPECTED_LEAF_NAMES)
        ),
        "expected_but_absent_leaf_names": sorted(
            set(EXPECTED_LEAF_NAMES).difference(names)
        ),
        "intent_expectation": {
            "sha256": EXPECTED_INTENT_SHA256,
            "size_bytes": EXPECTED_INTENT_SIZE_BYTES,
        },
        "intent_matches_expected_sha256": (
            intent is not None
            and intent.get("sha256") == EXPECTED_INTENT_SHA256
        ),
        "intent_matches_expected_size": (
            intent is not None
            and intent.get("size_bytes") == EXPECTED_INTENT_SIZE_BYTES
            and intent.get("read_size_bytes") == EXPECTED_INTENT_SIZE_BYTES
        ),
        "forensic_classification": classify_intent(intent),
        "safety": {
            "mutating_filesystem_operation_requested_by_notebook": False,
            "chmod_or_chown_requested_by_notebook": False,
            "filesystem_payload_read_performed": any(
                entry.get("payload_read") is True for entry in entries
            ),
            "control_leaf_payload_read_performed": observation_state[
                "control_leaf_payload_read_performed"
            ],
            "unexpected_leaf_payload_opened_or_read": False,
            "unity_catalog_volume_read_performed": path.startswith("/Volumes/"),
            "databricks_managed_storage_io_performed": path.startswith(
                "/Volumes/"
            ),
            "direct_external_network_endpoint_accessed": False,
            "package_resolution_build_or_install_executed": False,
            "spark_accessed": False,
            "databricks_rest_api_accessed": False,
            "study_or_test_data_path_requested_by_notebook": False,
            "calibration_training_or_inference_executed": False,
        },
    }


def public_failure(path, error, observation_state):
    return {
        "schema_version": SCHEMA_VERSION,
        "decision": "READ_ONLY_FORENSIC_INVENTORY_FAILED",
        "target_directory": path,
        "error_type": type(error).__name__,
        "error_detail": str(error),
        "safety": {
            "mutating_filesystem_operation_requested_by_notebook": False,
            "chmod_or_chown_requested_by_notebook": False,
            "unexpected_leaf_payload_opened_or_read": False,
            "control_leaf_payload_read_performed": observation_state[
                "control_leaf_payload_read_performed"
            ],
            "control_leaf_payload_read_may_have_been_performed": (
                observation_state[
                    "control_leaf_payload_read_may_have_been_performed"
                ]
            ),
            "unity_catalog_volume_read_attempted": path.startswith("/Volumes/"),
            "databricks_managed_storage_io_may_have_been_performed": (
                path.startswith("/Volumes/")
            ),
            "direct_external_network_endpoint_accessed": False,
            "package_resolution_build_or_install_executed": False,
            "spark_accessed": False,
            "databricks_rest_api_accessed": False,
            "study_or_test_data_path_requested_by_notebook": False,
            "calibration_training_or_inference_executed": False,
        },
    }


def capture_spent_attempt(path, expected_root_device, expected_root_inode):
    observation_state = {
        "filesystem_read_attempted": False,
        "control_leaf_payload_read_may_have_been_performed": False,
        "control_leaf_payload_read_performed": False,
    }
    try:
        return inspect_spent_attempt(
            path,
            expected_root_device,
            expected_root_inode,
            observation_state,
        )
    except BaseException as error:
        return public_failure(path, error, observation_state)


def main():
    result = capture_spent_attempt(
        EXACT_TARGET_DIRECTORY,
        EXPECTED_ROOT_DEVICE,
        EXPECTED_ROOT_INODE,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
