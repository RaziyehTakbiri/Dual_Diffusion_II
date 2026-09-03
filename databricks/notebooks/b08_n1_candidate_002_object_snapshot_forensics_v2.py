# Databricks notebook source
# MAGIC %md
# MAGIC # B08 N1 candidate-002 object-snapshot forensics V2
# MAGIC
# MAGIC This notebook performs two bounded, independent, control-evidence-only
# MAGIC read snapshots of the exact spent `candidate-002` path. It makes no
# MAGIC identity or continuity claim from FUSE device, inode, mode, or timestamp
# MAGIC metadata. Each snapshot opens and closes a new root descriptor, requires
# MAGIC a stable name/kind/size roster, and hashes only two exact allowlisted
# MAGIC control leaves. Matching snapshots establish only two sequentially
# MAGIC matching path-visible observations—not historical identity, atomicity,
# MAGIC freshness, cache coherence, or future stability.

# COMMAND ----------

import hashlib
import json
import os
import stat


SCHEMA_VERSION = (
    "heterodiff-b08-n1-candidate-002-object-snapshot-forensics-v2"
)
EXACT_TARGET_DIRECTORY = (
    "/Volumes/development/team_eds_supplychain/b08_runtime_output/"
    "b08-n1-overlay-candidate-002"
)
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
READ_CHUNK_BYTES = 64 * 1024


def canonical_json_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


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


def validate_visible_name(name):
    if (
        type(name) is not str
        or not name
        or name in (".", "..")
        or "/" in name
        or "\\" in name
        or len(os.fsencode(name)) > MAX_VISIBLE_LEAF_NAME_BYTES
    ):
        raise RuntimeError("INVALID_VISIBLE_LEAF_NAME")


def open_root_descriptor(path):
    observed = os.lstat(path)
    if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
        raise RuntimeError(
            "SPENT_ATTEMPT_ROOT_NOT_VISIBLE_NONSYMLINK_DIRECTORY"
        )
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode):
            raise RuntimeError("OPENED_SPENT_ATTEMPT_ROOT_NOT_DIRECTORY")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def bounded_roster(directory_descriptor):
    names = []
    iterator = os.scandir(directory_descriptor)
    try:
        for visible in iterator:
            if len(names) >= MAX_VISIBLE_LEAF_COUNT:
                raise RuntimeError("VISIBLE_LEAF_COUNT_EXCEEDS_BOUND")
            validate_visible_name(visible.name)
            names.append(visible.name)
    finally:
        iterator.close()

    roster = []
    for name in sorted(names):
        observed = os.stat(
            name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        roster.append(
            {
                "kind": kind_from_mode(observed.st_mode),
                "name": name,
                "size_bytes": observed.st_size,
            }
        )
    return roster


def read_control_leaf(directory_descriptor, name, observation_state):
    before = os.stat(
        name,
        dir_fd=directory_descriptor,
        follow_symlinks=False,
    )
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise RuntimeError("CONTROL_LEAF_NOT_REGULAR")
    if before.st_size > MAX_CONTROL_LEAF_BYTES:
        raise RuntimeError("CONTROL_LEAF_SIZE_EXCEEDS_BOUND")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    observation_state["control_leaf_payload_read_may_have_been_performed"] = True
    descriptor = os.open(
        name,
        flags,
        dir_fd=directory_descriptor,
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise RuntimeError("OPENED_CONTROL_LEAF_NOT_REGULAR")
        if opened.st_size > MAX_CONTROL_LEAF_BYTES:
            raise RuntimeError("OPENED_CONTROL_LEAF_SIZE_EXCEEDS_BOUND")

        digest = hashlib.sha256()
        size = 0
        while True:
            remaining = MAX_CONTROL_LEAF_BYTES + 1 - size
            if remaining <= 0:
                raise RuntimeError("CONTROL_LEAF_READ_EXCEEDS_BOUND")
            chunk = os.read(
                descriptor,
                min(READ_CHUNK_BYTES, remaining),
            )
            if not chunk:
                break
            observation_state["control_leaf_payload_bytes_read_total"] += len(
                chunk
            )
            observation_state["control_leaf_payload_read_performed"] = True
            digest.update(chunk)
            size += len(chunk)
            if size > MAX_CONTROL_LEAF_BYTES:
                raise RuntimeError("CONTROL_LEAF_READ_EXCEEDS_BOUND")
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)

    after_path = os.stat(
        name,
        dir_fd=directory_descriptor,
        follow_symlinks=False,
    )
    if not stat.S_ISREG(after_path.st_mode):
        raise RuntimeError("CONTROL_LEAF_PATH_NOT_REGULAR_AFTER_READ")
    if (
        before.st_size != size
        or opened.st_size != size
        or after_descriptor.st_size != size
        or after_path.st_size != size
    ):
        raise RuntimeError("CONTROL_LEAF_SIZE_UNSTABLE_DURING_READ")

    observation_state["control_leaf_payload_read_performed"] = True
    observation_state["control_leaf_payload_reads_completed"] += 1
    return {
        "payload_read": True,
        "sha256": digest.hexdigest(),
        "size_bytes": size,
    }


def snapshot_projection(path, ordinal, observation_state):
    observation_state["snapshot_count_attempted"] += 1
    observation_state["active_snapshot_ordinal"] = ordinal
    directory_descriptor = open_root_descriptor(path)
    try:
        roster_before = bounded_roster(directory_descriptor)
        control_leaves = {}
        by_name = {entry["name"]: entry for entry in roster_before}
        for name in EXPECTED_LEAF_NAMES:
            roster_entry = by_name.get(name)
            if roster_entry is None:
                control_leaves[name] = {
                    "present": False,
                    "payload_read": False,
                }
            elif roster_entry["kind"] != "REGULAR_FILE":
                control_leaves[name] = {
                    "kind": roster_entry["kind"],
                    "present": True,
                    "payload_read": False,
                    "size_bytes": roster_entry["size_bytes"],
                }
            elif roster_entry["size_bytes"] > MAX_CONTROL_LEAF_BYTES:
                control_leaves[name] = {
                    "kind": roster_entry["kind"],
                    "present": True,
                    "payload_read": False,
                    "read_refusal": "CONTROL_LEAF_SIZE_EXCEEDS_BOUND",
                    "size_bytes": roster_entry["size_bytes"],
                }
            else:
                control_leaves[name] = {
                    "kind": "REGULAR_FILE",
                    "present": True,
                    **read_control_leaf(
                        directory_descriptor,
                        name,
                        observation_state,
                    ),
                }

        roster_after = bounded_roster(directory_descriptor)
        if roster_before != roster_after:
            raise RuntimeError("VISIBLE_LEAF_ROSTER_CHANGED_WITHIN_SNAPSHOT")
    finally:
        os.close(directory_descriptor)

    final_root = os.lstat(path)
    if not stat.S_ISDIR(final_root.st_mode) or stat.S_ISLNK(final_root.st_mode):
        raise RuntimeError(
            "SPENT_ATTEMPT_ROOT_NOT_VISIBLE_NONSYMLINK_DIRECTORY_AFTER_SNAPSHOT"
        )

    projection = {
        "control_leaves": control_leaves,
        "roster": roster_after,
        "target_directory": path,
    }
    result = {
        "ordinal": ordinal,
        "projection": projection,
        "projection_sha256": hashlib.sha256(
            canonical_json_bytes(projection)
        ).hexdigest(),
    }
    observation_state["completed_snapshots"].append(result)
    observation_state["snapshot_count_completed"] += 1
    observation_state["active_snapshot_ordinal"] = None
    return result


def classify_intent(projection):
    intent = projection["control_leaves"]["attempt-intent.json"]
    if not intent["present"]:
        return "STABLY_NOT_VISIBLE_IN_TWO_PATH_SNAPSHOTS"
    if intent.get("kind") != "REGULAR_FILE":
        return "STABLY_NONREGULAR_INTENT_NOT_READ"
    if intent.get("payload_read") is not True:
        return "STABLY_UNREAD_INTENT_REQUIRES_REVIEW"
    size = intent["size_bytes"]
    digest = intent["sha256"]
    if size == 0:
        return "STABLY_ZERO_BYTE_INTENT_VISIBLE"
    if size < EXPECTED_INTENT_SIZE_BYTES:
        return "STABLY_PARTIAL_INTENT_VISIBLE"
    if size == EXPECTED_INTENT_SIZE_BYTES and digest == EXPECTED_INTENT_SHA256:
        return "STABLY_COMPLETE_EXPECTED_INTENT_VISIBLE"
    return "STABLY_MISMATCHING_INTENT_VISIBLE"


def safety_projection(path, observation_state, completed):
    volume_path = path.startswith("/Volumes/")
    projection = {
        "mutating_filesystem_operation_requested_by_notebook": False,
        "chmod_or_chown_requested_by_notebook": False,
        "control_leaf_payload_read_performed": observation_state[
            "control_leaf_payload_read_performed"
        ],
        "control_leaf_payload_read_may_have_been_performed": (
            observation_state[
                "control_leaf_payload_read_may_have_been_performed"
            ]
        ),
        "control_leaf_payload_bytes_read_total": observation_state[
            "control_leaf_payload_bytes_read_total"
        ],
        "control_leaf_payload_reads_completed": observation_state[
            "control_leaf_payload_reads_completed"
        ],
        "unexpected_leaf_payload_opened_or_read": False,
        "unity_catalog_volume_read_attempted": volume_path,
        "databricks_managed_storage_io_may_have_been_performed": volume_path,
        "direct_external_network_endpoint_accessed": False,
        "package_resolution_build_or_install_executed": False,
        "spark_accessed": False,
        "databricks_rest_api_accessed": False,
        "study_or_test_data_path_requested_by_notebook": False,
        "calibration_training_or_inference_executed": False,
    }
    if completed:
        projection["unity_catalog_volume_read_performed"] = volume_path
        projection["databricks_managed_storage_io_performed"] = volume_path
    return projection


def custody_projection(required_pair_completed):
    projection = {
        "required_basis": (
            "TWO_INDEPENDENT_PATH_VISIBLE_ROSTER_AND_CONTENT_SNAPSHOTS"
        ),
        "required_snapshot_pair_completed": required_pair_completed,
        "object_storage_semantics": True,
        "prior_device_inode_gate_used": False,
        "device_inode_permission_bits_or_timestamp_used_for_custody_acceptance": False,
        "path_object_continuity_with_failed_run_claimed": False,
        "between_snapshot_object_identity_claimed": False,
        "atomic_snapshot_claimed": False,
        "freshness_or_cache_coherence_claimed": False,
        "future_stability_claimed": False,
    }
    if required_pair_completed:
        projection[
            "observed_basis"
        ] = "TWO_INDEPENDENT_PATH_VISIBLE_ROSTER_AND_CONTENT_SNAPSHOTS"
    else:
        projection["observed_basis"] = "PARTIAL_OR_NO_SNAPSHOT_PAIR"
    return projection


def inspect_spent_attempt(path, observation_state):
    first = snapshot_projection(path, 1, observation_state)
    second = snapshot_projection(path, 2, observation_state)
    same = (
        first["projection_sha256"] == second["projection_sha256"]
        and first["projection"] == second["projection"]
    )
    common = {
        "schema_version": SCHEMA_VERSION,
        "target_directory": path,
        "exact_target_only": path == EXACT_TARGET_DIRECTORY,
        "custody_model": custody_projection(True),
        "bounds": {
            "maximum_visible_leaf_count": MAX_VISIBLE_LEAF_COUNT,
            "maximum_visible_leaf_name_bytes": MAX_VISIBLE_LEAF_NAME_BYTES,
            "maximum_control_leaf_bytes": MAX_CONTROL_LEAF_BYTES,
            "read_chunk_bytes": READ_CHUNK_BYTES,
        },
        "snapshot_count_attempted": observation_state[
            "snapshot_count_attempted"
        ],
        "snapshot_count_completed": observation_state[
            "snapshot_count_completed"
        ],
        "snapshots": [first, second],
        "snapshots_equal": same,
        "safety": safety_projection(path, observation_state, True),
    }
    if not same:
        return {
            **common,
            "decision": "HOLD_FORENSIC_PATH_SNAPSHOTS_NOT_REPEATABLE",
            "forensic_classification": "UNRESOLVED_NONREPEATABLE_SNAPSHOTS",
        }

    projection = first["projection"]
    unread_present_control_leaves = sorted(
        name
        for name, value in projection["control_leaves"].items()
        if value["present"] and value.get("payload_read") is not True
    )
    unexpected = sorted(
        entry["name"]
        for entry in projection["roster"]
        if entry["name"] not in EXPECTED_LEAF_NAMES
    )
    result = {
        **common,
        "stable_projection_sha256": first["projection_sha256"],
        "stable_projection": projection,
        "unread_present_control_leaf_names": unread_present_control_leaves,
        "unexpected_leaf_names": unexpected,
        "unexpected_leaf_review_required": bool(unexpected),
        "forensic_classification": classify_intent(projection),
    }
    if unread_present_control_leaves:
        result["decision"] = "HOLD_FORENSIC_ALLOWLISTED_CONTROL_LEAF_UNREAD"
    else:
        result[
            "decision"
        ] = "READ_ONLY_FORENSIC_REPEATABLE_PATH_SNAPSHOTS_COMPLETE"
    return result


def public_failure(path, error, observation_state):
    return {
        "schema_version": SCHEMA_VERSION,
        "decision": "READ_ONLY_OBJECT_SNAPSHOT_FORENSIC_INVENTORY_FAILED",
        "target_directory": path,
        "exact_target_only": path == EXACT_TARGET_DIRECTORY,
        "error_type": type(error).__name__,
        "error_detail": str(error),
        "custody_model": custody_projection(False),
        "snapshot_count_attempted": observation_state[
            "snapshot_count_attempted"
        ],
        "snapshot_count_completed": observation_state[
            "snapshot_count_completed"
        ],
        "active_snapshot_ordinal_at_failure": observation_state[
            "active_snapshot_ordinal"
        ],
        "completed_snapshots": observation_state["completed_snapshots"],
        "safety": safety_projection(path, observation_state, False),
    }


def capture_spent_attempt(path):
    observation_state = {
        "snapshot_count_attempted": 0,
        "snapshot_count_completed": 0,
        "active_snapshot_ordinal": None,
        "completed_snapshots": [],
        "control_leaf_payload_read_may_have_been_performed": False,
        "control_leaf_payload_read_performed": False,
        "control_leaf_payload_bytes_read_total": 0,
        "control_leaf_payload_reads_completed": 0,
    }
    try:
        return inspect_spent_attempt(path, observation_state)
    except BaseException as error:
        return public_failure(path, error, observation_state)


def main():
    result = capture_spent_attempt(EXACT_TARGET_DIRECTORY)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
