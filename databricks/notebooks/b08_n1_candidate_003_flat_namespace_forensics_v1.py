# Databricks notebook source
# MAGIC %md
# MAGIC # B08 N1 candidate-003 flat-namespace read-only forensics V1
# MAGIC
# MAGIC This notebook performs exactly two separately opened, bounded
# MAGIC observations of the candidate-003 reserved namespace in the fixed
# MAGIC Unity Catalog Volume.
# MAGIC Candidate-003 uses flat sibling objects: the virtual candidate path is
# MAGIC expected to remain absent. The notebook individually inspects only the
# MAGIC 132 protocol-reserved names and never enumerates unrelated Volume
# MAGIC contents. It opens and reads only the exact attempt-intent and
# MAGIC construction-failure-receipt leaves.
# MAGIC
# MAGIC The notebook has no widgets or alternate runtime target. It performs no
# MAGIC write, rename, delete, permission change, direct external network
# MAGIC access, subprocess, package operation, Spark/REST operation, or
# MAGIC scientific/data operation. Reading the fixed /Volumes target is
# MAGIC explicitly reported as Databricks-managed storage I/O.
# MAGIC Matching observations establish only repeatable path-visible evidence;
# MAGIC they do not establish historical identity, atomicity, freshness, cache
# MAGIC coherence, immutability, physical durability, or future stability.

# COMMAND ----------

import hashlib
import json
import os
import stat


SCHEMA_VERSION = (
    "heterodiff-b08-n1-candidate-003-flat-namespace-forensics-v1"
)
EXACT_PARENT = (
    "/Volumes/development/team_eds_supplychain/b08_runtime_output"
)
CANDIDATE_ID = "b08-n1-overlay-candidate-003"
VIRTUAL_CANDIDATE_PREFIX = f"{EXACT_PARENT}/{CANDIDATE_ID}"

INTENT_LEAF_NAME = f"{CANDIDATE_ID}.attempt-intent.json"
PAYLOAD_MANIFEST_LEAF_NAME = f"{CANDIDATE_ID}.payload-manifest.json"
SUCCESS_RECEIPT_LEAF_NAME = f"{CANDIDATE_ID}.construction-receipt.json"
FAILURE_RECEIPT_LEAF_NAME = (
    f"{CANDIDATE_ID}.construction-failure-receipt.json"
)
CONTROL_LEAF_NAMES = (INTENT_LEAF_NAME, FAILURE_RECEIPT_LEAF_NAME)
PAYLOAD_CHUNK_COUNT = 128

ATTEMPT_INTENT_SCHEMA = "heterodiff-b08-n1-uc-native-attempt-intent-v2"
FAILURE_RECEIPT_SCHEMA = (
    "heterodiff-b08-n1-uc-native-failure-receipt-v1"
)
ATTEMPT_INTENT_DOMAIN = (
    b"heterodiff/b08/n1/uc-native-attempt-intent/v2\0"
)

# These values were independently reconstructed from the exact V2 builder,
# source snapshot, package authorization, launcher evidence, and the three
# Databricks-observed 0755 review bindings reported immediately before the
# candidate-003 activation.
EXPECTED_INTENT_SIZE_BYTES = 15_973
EXPECTED_INTENT_FILE_SHA256 = (
    "ea8441151c07aef1a6fdf3320ff54d61237d3812b0c679cc0c2954a8db416015"
)
EXPECTED_INTENT_RECORD_SHA256 = (
    "f9832c8b78a802254891b2d6f117c6c54f958a729bbac44f7bc1fcb5979f224f"
)
EXPECTED_REVIEW_PACKAGE_SHA256 = (
    "5404dd580fac351e888d40836a399d5490396f35df576013eb1a78ecd20d9b23"
)
EXPECTED_BUILDER_SHA256 = (
    "7c7edb28f459618b1f35538e444b9cf40e70026b02fd0919ded9a20097f9014d"
)
EXPECTED_LAUNCHER_SHA256 = (
    "7035ee3fdee6fb6b50005798f8c178a140ee1d3727471d8a58ef160f66f57afb"
)
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "0e2decc9d0c6dbb4ff6b41dec4ee78b6139ea2aa8a419880e3e06ff4f8716021"
)
EXPECTED_SOURCE_IDENTITY_SHA256 = (
    "9716f23666953d87b8a02d0d4c18fe85bdb83597dd5a6e390551e9e413f36eec"
)

# A valid builder receipt is far below this deliberately narrower forensic
# ceiling. Oversized controls are reported but never opened.
MAX_CONTROL_LEAF_BYTES = 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
MAX_COMMAND_JOURNAL_ENTRIES = 64
MAX_DIAGNOSTIC_TAIL_BYTES = 64 * 1024
MAX_ERROR_DETAIL_BYTES = 8 * 1024
MAX_JOURNAL_ARG_COUNT = 256
MAX_JOURNAL_STRING_BYTES = 16 * 1024
MAX_EXECUTION_DETAIL_BYTES = 4 * 1024
MAX_CAPTURED_STREAM_BYTES = 16 * 1024 * 1024
MAX_OBSERVED_STREAM_BYTES = MAX_CAPTURED_STREAM_BYTES + 64 * 1024
LINUX_MAX_SIGNAL_NUMBER = 64
POSIX_MAX_EXIT_STATUS = 255
PIP_IDENTITY_CONTROL_FILE_BYTE_LIMIT = 16 * 1024 * 1024
PIP_PAYLOAD_FILE_LIMIT = 250_000
WHEEL_FILE_BYTE_LIMIT = 4 * 1024 * 1024 * 1024
WHEEL_MEMBER_LIMIT = 250_000
WHEEL_CENTRAL_DIRECTORY_BYTE_LIMIT = 64 * 1024 * 1024

EXPECTED_CANDIDATE_EXECUTION_ERROR_CODES = {
    "TOOL_OUTPUT_READER_DID_NOT_QUIESCE",
    "TOOL_SUBPROCESS_SUPERVISOR_FAILED",
    "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
    "TOOL_OUTPUT_READER_FAILED",
}
EXPECTED_OS_EXECUTION_ERROR_TYPES = {
    "OSError",
    "BlockingIOError",
    "ChildProcessError",
    "ConnectionError",
    "BrokenPipeError",
    "ConnectionAbortedError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "FileExistsError",
    "FileNotFoundError",
    "InterruptedError",
    "IsADirectoryError",
    "NotADirectoryError",
    "PermissionError",
    "ProcessLookupError",
    "TimeoutError",
    "TimeoutExpired",
}

# The only subprocess sequence reachable from the reviewed candidate-003 V2
# builder after a durable intent has been committed. A receipt is accepted by
# this narrow forensic tool only when its journal is an exact nonempty prefix
# ending in one failed entry. Non-journal construction failures remain spent,
# but require a separately reviewed diagnostic rather than being generalized
# here.
EXPECTED_TOOL_JOURNAL_STEPS = (
    "bind_host_pip_identity_before_bootstrap",
    "download_bootstrap_pip_wheel",
    "rebind_host_pip_identity_before_target_install",
    "bootstrap_pip_into_isolated_venv",
    "bind_isolated_venv_pip_identity_after_bootstrap",
    "download_exact_build_tool_wheels",
    "install_exact_build_tools_in_isolated_venv",
    "verify_isolated_build_tool_versions",
    "build_project_wheel_from_source_copy",
    "resolve_exact_runtime_roots_to_wheels",
    "install_hash_locked_wheelhouse_to_isolated_overlay",
    "rebind_isolated_venv_pip_identity_before_manifest",
)
EXPECTED_PIP_IDENTITY_PROBE_SIZE_BYTES = 12_179
EXPECTED_PIP_IDENTITY_PROBE_SHA256 = (
    "12ec0e3ba51bc36372fa66fc2976992a0eec7ad76c1929ee7c59628b976fe86c"
)

INTENT_TOP_LEVEL_KEYS = {
    "schema_version",
    "record_sha256",
    "state",
    "profile",
    "source",
    "external_review_authority",
    "destination",
    "network",
    "construction",
    "nonproofs",
}
FAILURE_TOP_LEVEL_KEYS = {
    "schema_version",
    "decision",
    "attempt_intent_sha256",
    "error_code",
    "error_detail",
    "attempt_state_before_failure_receipt_commit",
    "safety",
    "not_proven",
}
EXPECTED_FAILURE_SAFETY = {
    "base_runtime_install_target_requested_by_notebook": False,
    "study_or_test_data_path_requested_by_notebook": False,
    "spark_operation_requested_by_notebook": False,
    "databricks_rest_api_requested_by_notebook": False,
    "scientific_execution_requested_by_notebook": False,
    "canonical_repository_lock_write_requested_by_notebook": False,
    "child_process_external_file_access_audited": False,
    "child_process_side_effects_outside_staging_proven_absent": False,
}
EXPECTED_FAILURE_NONPROOFS = [
    "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
    "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_STAGING_ABSENT",
    "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
]
REQUIRED_ATTEMPT_STATE_KEYS = {
    "attempt_namespace_spent",
    "intent_create_begun",
    "durable_intent_committed",
    "durable_intent_may_exist",
    "durable_intent_expected_sha256",
    "durable_intent_expected_size_bytes",
    "managed_uc_write_phase_entered",
    "managed_uc_write_begun",
    "managed_uc_exclusive_create_calls_begun",
    "managed_uc_confirmed_leaf_count",
    "managed_uc_confirmed_bytes_written",
    "managed_uc_last_leaf_create_begun",
    "managed_uc_last_leaf_may_exist",
    "managed_uc_last_leaf_expected_sha256",
    "managed_uc_last_leaf_expected_size_bytes",
    "managed_uc_last_confirmed_binding",
    "managed_uc_confirmed_bindings",
    "staging_write_begun",
    "preintent_source_identity_verification_begun",
    "preintent_source_identity_verification_completed",
    "postintent_source_identity_verification_begun",
    "postintent_source_identity_verification_completed",
    "staged_source_manifest_verified",
    "network_contact_begun",
    "package_resolution_begun",
    "isolated_venv_creation_begun",
    "host_pip_identity",
    "host_pip_identity_reverified_before_target_install",
    "bootstrap_pip_wheel_binding",
    "bootstrap_pip_lock_binding",
    "isolated_venv_pip_identity",
    "bootstrap_pip_install_begun",
    "build_tool_install_begun",
    "project_wheel_build_begun",
    "overlay_install_begun",
    "managed_uc_payload_publish_begun",
    "success_receipt_phase_entered",
    "success_receipt_create_call_begun",
    "success_receipt_may_exist",
    "success_receipt_committed",
    "failure_receipt_commit_begun",
    "failure_receipt_create_call_begun",
    "failure_receipt_may_exist",
    "failure_receipt_committed",
    "failure_receipt_error_code",
    "failure_receipt_error_detail",
    "failure_receipt_skipped_for_terminal_receipt_ambiguity",
    "terminal_receipt_ambiguity",
    "staging_cleanup_begun",
    "staging_cleanup_completed",
    "last_started_step",
    "last_completed_step",
    "last_failed_step",
    "command_journal",
}
ATTEMPT_STATE_BOOLEAN_KEYS = {
    "attempt_namespace_spent",
    "intent_create_begun",
    "durable_intent_committed",
    "durable_intent_may_exist",
    "managed_uc_write_phase_entered",
    "managed_uc_write_begun",
    "staging_write_begun",
    "preintent_source_identity_verification_begun",
    "preintent_source_identity_verification_completed",
    "postintent_source_identity_verification_begun",
    "postintent_source_identity_verification_completed",
    "staged_source_manifest_verified",
    "network_contact_begun",
    "package_resolution_begun",
    "isolated_venv_creation_begun",
    "host_pip_identity_reverified_before_target_install",
    "bootstrap_pip_install_begun",
    "build_tool_install_begun",
    "project_wheel_build_begun",
    "overlay_install_begun",
    "managed_uc_payload_publish_begun",
    "success_receipt_phase_entered",
    "success_receipt_create_call_begun",
    "success_receipt_may_exist",
    "success_receipt_committed",
    "failure_receipt_commit_begun",
    "failure_receipt_create_call_begun",
    "failure_receipt_may_exist",
    "failure_receipt_committed",
    "failure_receipt_skipped_for_terminal_receipt_ambiguity",
    "terminal_receipt_ambiguity",
    "staging_cleanup_begun",
    "staging_cleanup_completed",
}


def canonical_json_bytes(value):
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def strict_json_equal(left, right):
    """Compare parsed JSON without Python's bool/int/float coercions."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(
            strict_json_equal(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            strict_json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def reserved_leaf_names():
    return (
        INTENT_LEAF_NAME,
        *(
            f"{CANDIDATE_ID}.payload-{ordinal:04d}.bin"
            for ordinal in range(PAYLOAD_CHUNK_COUNT)
        ),
        PAYLOAD_MANIFEST_LEAF_NAME,
        SUCCESS_RECEIPT_LEAF_NAME,
        FAILURE_RECEIPT_LEAF_NAME,
    )


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


def validate_frozen_contract():
    names = reserved_leaf_names()
    if len(names) != 132 or len(set(names)) != 132:
        raise RuntimeError("FROZEN_RESERVED_NAMESPACE_INVALID")
    for name in names:
        if (
            not name
            or name in (".", "..")
            or "/" in name
            or "\\" in name
            or not name.startswith(CANDIDATE_ID + ".")
        ):
            raise RuntimeError("FROZEN_RESERVED_LEAF_NAME_INVALID")
    if not EXACT_PARENT.startswith("/Volumes/"):
        raise RuntimeError("FROZEN_PARENT_NOT_UNITY_CATALOG_VOLUME")
    if VIRTUAL_CANDIDATE_PREFIX != f"{EXACT_PARENT}/{CANDIDATE_ID}":
        raise RuntimeError("FROZEN_VIRTUAL_PREFIX_INVALID")
    for feature in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK"):
        if not hasattr(os, feature):
            raise RuntimeError("REQUIRED_OS_FEATURE_UNAVAILABLE:" + feature)
    if os.open not in os.supports_dir_fd:
        raise RuntimeError("OS_OPEN_DIR_FD_UNSUPPORTED")
    if os.stat not in os.supports_dir_fd:
        raise RuntimeError("OS_STAT_DIR_FD_UNSUPPORTED")
    if os.stat not in os.supports_follow_symlinks:
        raise RuntimeError("OS_STAT_NOFOLLOW_UNSUPPORTED")


def open_parent_descriptor(observation_state):
    observed = os.lstat(EXACT_PARENT)
    if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
        raise RuntimeError("EXACT_PARENT_NOT_NONSYMLINK_DIRECTORY")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open(EXACT_PARENT, flags)
    observation_state["parent_descriptor_open_completed_count"] += 1
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode):
            raise RuntimeError("OPENED_PARENT_NOT_DIRECTORY")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def stat_relative(descriptor, name, observation_state):
    try:
        observed = os.stat(
            name,
            dir_fd=descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return {"kind": "ABSENT", "name": name}
    result = {
        "kind": kind_from_mode(observed.st_mode),
        "name": name,
        "size_bytes": observed.st_size,
    }
    observation_state["reserved_path_visibility_observed"] = True
    return result


def namespace_projection(descriptor, observation_state):
    return {
        "virtual_candidate_prefix": stat_relative(
            descriptor, CANDIDATE_ID, observation_state
        ),
        "reserved_leaves": [
            stat_relative(descriptor, name, observation_state)
            for name in reserved_leaf_names()
        ],
    }


def read_control_leaf(descriptor, name, before, observation_state):
    if before["kind"] != "REGULAR_FILE":
        return None, {
            **before,
            "payload_read": False,
            "read_refusal": "CONTROL_LEAF_NOT_REGULAR",
        }
    if before["size_bytes"] < 0 or before["size_bytes"] > MAX_CONTROL_LEAF_BYTES:
        return None, {
            **before,
            "payload_read": False,
            "read_refusal": "CONTROL_LEAF_SIZE_EXCEEDS_FORENSIC_BOUND",
        }

    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    observation_state["control_payload_open_may_have_begun"] = True
    descriptor_leaf = os.open(name, flags, dir_fd=descriptor)
    try:
        payload = bytearray()
        opened = os.fstat(descriptor_leaf)
        if not stat.S_ISREG(opened.st_mode):
            raise RuntimeError("OPENED_CONTROL_LEAF_NOT_REGULAR")
        if opened.st_size < 0 or opened.st_size > MAX_CONTROL_LEAF_BYTES:
            raise RuntimeError("OPENED_CONTROL_LEAF_SIZE_EXCEEDS_BOUND")
        while True:
            remaining = MAX_CONTROL_LEAF_BYTES + 1 - len(payload)
            if remaining <= 0:
                raise RuntimeError("CONTROL_LEAF_READ_EXCEEDS_BOUND")
            observation_state[
                "control_payload_read_syscall_may_have_begun"
            ] = True
            chunk = os.read(
                descriptor_leaf,
                min(READ_CHUNK_BYTES, remaining),
            )
            observation_state[
                "control_payload_read_syscall_completed"
            ] = True
            if not chunk:
                break
            observation_state[
                "positive_control_payload_bytes_observed"
            ] = True
            observation_state["control_payload_bytes_read_total"] += len(
                chunk
            )
            payload.extend(chunk)
            if len(payload) > MAX_CONTROL_LEAF_BYTES:
                raise RuntimeError("CONTROL_LEAF_READ_EXCEEDS_BOUND")
        after_descriptor = os.fstat(descriptor_leaf)
    finally:
        os.close(descriptor_leaf)

    after_path = os.stat(
        name,
        dir_fd=descriptor,
        follow_symlinks=False,
    )
    if not stat.S_ISREG(after_path.st_mode):
        raise RuntimeError("CONTROL_LEAF_PATH_NOT_REGULAR_AFTER_READ")
    if not (
        before["size_bytes"]
        == opened.st_size
        == len(payload)
        == after_descriptor.st_size
        == after_path.st_size
    ):
        raise RuntimeError("CONTROL_LEAF_SIZE_UNSTABLE_DURING_READ")
    observation_state["control_payload_reads_completed"] += 1
    raw = bytes(payload)
    return raw, {
        "kind": "REGULAR_FILE",
        "name": name,
        "payload_read": True,
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
    }


def snapshot(ordinal, observation_state):
    observation_state["snapshot_count_attempted"] += 1
    observation_state["active_snapshot_ordinal"] = ordinal
    observation_state["databricks_managed_storage_io_attempted"] = True
    observation_state[
        "databricks_managed_storage_io_may_have_been_performed"
    ] = True
    descriptor = open_parent_descriptor(observation_state)
    try:
        before = namespace_projection(descriptor, observation_state)
        by_name = {
            item["name"]: item for item in before["reserved_leaves"]
        }
        control_payloads = {}
        control_bindings = {}
        for name in CONTROL_LEAF_NAMES:
            payload, binding = read_control_leaf(
                descriptor,
                name,
                by_name[name],
                observation_state,
            )
            control_payloads[name] = payload
            control_bindings[name] = binding
        after = namespace_projection(descriptor, observation_state)
        if before != after:
            raise RuntimeError("RESERVED_NAMESPACE_CHANGED_WITHIN_SNAPSHOT")
    finally:
        os.close(descriptor)

    present = [
        item for item in after["reserved_leaves"]
        if item["kind"] != "ABSENT"
    ]
    absent_names = [
        item["name"] for item in after["reserved_leaves"]
        if item["kind"] == "ABSENT"
    ]
    projection = {
        "parent": EXACT_PARENT,
        "candidate_id": CANDIDATE_ID,
        "virtual_candidate_prefix": after["virtual_candidate_prefix"],
        "reserved_leaf_count": len(after["reserved_leaves"]),
        "present_reserved_leaves": present,
        "absent_reserved_leaf_count": len(absent_names),
        "absent_reserved_leaf_names_sha256": sha256_bytes(
            canonical_json_bytes(absent_names)
        ),
        "control_leaves": control_bindings,
    }
    result = {
        "ordinal": ordinal,
        "projection": projection,
        "projection_sha256": sha256_bytes(canonical_json_bytes(projection)),
        "control_payloads": control_payloads,
    }
    observation_state["snapshot_count_completed"] += 1
    observation_state["active_snapshot_ordinal"] = None
    observation_state["completed_projection_sha256s"].append(
        result["projection_sha256"]
    )
    return result


def reject_nonfinite(value):
    raise ValueError("NONFINITE_JSON_NUMBER:" + value)


def reject_duplicate_keys(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("DUPLICATE_JSON_KEY:" + key)
        value[key] = child
    return value


def parse_canonical_ascii_json(payload, label):
    try:
        decoded = payload.decode("ascii")
        value = json.loads(
            decoded,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(label + "_NOT_STRICT_ASCII_JSON") from error
    if type(value) is not dict:
        raise RuntimeError(label + "_NOT_JSON_OBJECT")
    if payload != canonical_json_bytes(value) + b"\n":
        raise RuntimeError(label + "_NOT_CANONICAL_JSON_PLUS_ONE_LF")
    return value


def nested_mapping(value, key, errors, label):
    child = value.get(key) if type(value) is dict else None
    if type(child) is not dict:
        errors.append(label + "_NOT_OBJECT")
        return {}
    return child


def validate_intent(payload):
    errors = []
    intent = parse_canonical_ascii_json(payload, "ATTEMPT_INTENT")
    raw_sha256 = sha256_bytes(payload)
    if len(payload) != EXPECTED_INTENT_SIZE_BYTES:
        errors.append("INTENT_SIZE_DIFFERS_FROM_RECONSTRUCTED_EXPECTATION")
    if raw_sha256 != EXPECTED_INTENT_FILE_SHA256:
        errors.append("INTENT_FILE_SHA256_DIFFERS_FROM_RECONSTRUCTED_EXPECTATION")
    if set(intent) != INTENT_TOP_LEVEL_KEYS:
        errors.append("INTENT_TOP_LEVEL_KEYS_MISMATCH")
    if intent.get("schema_version") != ATTEMPT_INTENT_SCHEMA:
        errors.append("INTENT_SCHEMA_MISMATCH")
    if intent.get("state") != "ATTEMPT_SPENT_BEFORE_NETWORK_OR_BUILD":
        errors.append("INTENT_STATE_MISMATCH")
    projection = dict(intent)
    declared_record_sha256 = projection.pop("record_sha256", None)
    computed_record_sha256 = sha256_bytes(
        ATTEMPT_INTENT_DOMAIN + canonical_json_bytes(projection)
    )
    if declared_record_sha256 != computed_record_sha256:
        errors.append("INTENT_INTERNAL_RECORD_SHA256_INVALID")
    if declared_record_sha256 != EXPECTED_INTENT_RECORD_SHA256:
        errors.append("INTENT_INTERNAL_RECORD_SHA256_UNEXPECTED")

    destination = nested_mapping(
        intent, "destination", errors, "INTENT_DESTINATION"
    )
    if destination.get("parent") != EXACT_PARENT:
        errors.append("INTENT_PARENT_MISMATCH")
    if destination.get("virtual_candidate_prefix") != VIRTUAL_CANDIDATE_PREFIX:
        errors.append("INTENT_VIRTUAL_PREFIX_MISMATCH")
    if destination.get("candidate_id") != CANDIDATE_ID:
        errors.append("INTENT_CANDIDATE_ID_MISMATCH")
    if destination.get("reserved_leaf_names") != list(reserved_leaf_names()):
        errors.append("INTENT_RESERVED_NAMESPACE_MISMATCH")
    if destination.get("required_initial_state") != "ALL_RESERVED_LEAVES_ABSENT":
        errors.append("INTENT_REQUIRED_INITIAL_STATE_MISMATCH")

    authority = nested_mapping(
        intent,
        "external_review_authority",
        errors,
        "INTENT_EXTERNAL_REVIEW_AUTHORITY",
    )
    review_package = nested_mapping(
        authority, "review_package", errors, "INTENT_REVIEW_PACKAGE"
    )
    if review_package.get("record_sha256") != EXPECTED_REVIEW_PACKAGE_SHA256:
        errors.append("INTENT_REVIEW_PACKAGE_SHA256_MISMATCH")
    if (
        authority.get("operator_authorized_review_package_sha256")
        != EXPECTED_REVIEW_PACKAGE_SHA256
    ):
        errors.append("INTENT_OPERATOR_AUTHORIZATION_SHA256_MISMATCH")
    if authority.get("authorization_matched_before_intent") is not True:
        errors.append("INTENT_AUTHORIZATION_MATCH_NOT_TRUE")
    launch = nested_mapping(
        authority,
        "hash_first_launch_evidence",
        errors,
        "INTENT_HASH_FIRST_LAUNCH_EVIDENCE",
    )
    if launch.get("executed_payload_sha256") != EXPECTED_BUILDER_SHA256:
        errors.append("INTENT_EXECUTED_BUILDER_SHA256_MISMATCH")
    if launch.get("launcher_source_sha256") != EXPECTED_LAUNCHER_SHA256:
        errors.append("INTENT_LAUNCHER_SHA256_MISMATCH")
    if launch.get("same_in_memory_payload_compiled_and_executed") is not True:
        errors.append("INTENT_SAME_PAYLOAD_EXECUTION_NOT_TRUE")

    source = nested_mapping(intent, "source", errors, "INTENT_SOURCE")
    if source.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST_SHA256:
        errors.append("INTENT_SOURCE_MANIFEST_SHA256_MISMATCH")
    reviewed_source = nested_mapping(
        source,
        "reviewed_source_identity",
        errors,
        "INTENT_REVIEWED_SOURCE_IDENTITY",
    )
    if reviewed_source.get("record_sha256") != EXPECTED_SOURCE_IDENTITY_SHA256:
        errors.append("INTENT_SOURCE_IDENTITY_SHA256_MISMATCH")
    construction_notebook = nested_mapping(
        source,
        "construction_notebook",
        errors,
        "INTENT_CONSTRUCTION_NOTEBOOK",
    )
    if construction_notebook.get("sha256") != EXPECTED_BUILDER_SHA256:
        errors.append("INTENT_CONSTRUCTION_NOTEBOOK_SHA256_MISMATCH")
    hash_first_launcher = nested_mapping(
        source,
        "hash_first_launcher",
        errors,
        "INTENT_HASH_FIRST_LAUNCHER",
    )
    if hash_first_launcher.get("sha256") != EXPECTED_LAUNCHER_SHA256:
        errors.append("INTENT_HASH_FIRST_LAUNCHER_SHA256_MISMATCH")

    return intent, {
        "valid": not errors,
        "errors": errors,
        "file_sha256": raw_sha256,
        "size_bytes": len(payload),
        "declared_record_sha256_is_lower_hex": is_lower_hex_sha256(
            declared_record_sha256
        ),
        "declared_record_sha256_matches_computed": (
            declared_record_sha256 == computed_record_sha256
        ),
        "declared_record_sha256_matches_expected": (
            declared_record_sha256 == EXPECTED_INTENT_RECORD_SHA256
        ),
        "computed_record_sha256": computed_record_sha256,
    }


def is_lower_hex_sha256(value):
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def is_safe_token(value, maximum_bytes=256):
    return (
        type(value) is str
        and 0 < len(value.encode("ascii", errors="ignore")) <= maximum_bytes
        and value.isascii()
        and all(
            character.isalnum() or character in "_-.:"
            for character in value
        )
    )


def is_ascii_identifier(value):
    return (
        type(value) is str
        and value.isascii()
        and value.isidentifier()
    )


def is_linux_subprocess_returncode(value):
    return (
        type(value) is int
        and (
            value == 0
            or 1 <= value <= POSIX_MAX_EXIT_STATUS
            or -LINUX_MAX_SIGNAL_NUMBER <= value <= -1
        )
    )


def opaque_text_binding(value):
    if value is None:
        return {"present": False, "size_bytes": 0, "sha256": None}
    raw = value.encode("utf-8")
    return {
        "present": True,
        "size_bytes": len(raw),
        "sha256": sha256_bytes(raw),
    }


def expected_nonidentity_journal_argv(step):
    venv_python = "<COMMAND_CWD>/build-venv/bin/python"
    tool_wheelhouse = "<COMMAND_CWD>/candidate/build-tool-wheelhouse"
    runtime_wheelhouse = "<COMMAND_CWD>/candidate/wheelhouse"
    return {
        "download_bootstrap_pip_wheel": [
            "<HOST_PYTHON>", "-I", "-B", "-m", "pip", "--isolated",
            "--disable-pip-version-check", "--no-cache-dir", "--quiet",
            "download", "--no-input", "--no-deps", "--only-binary=:all:",
            "--index-url", "<PRIMARY_INDEX_URL>", "--dest",
            tool_wheelhouse, "pip==25.0.1",
        ],
        "bootstrap_pip_into_isolated_venv": [
            "<HOST_PYTHON>", "-I", "-B", "-m", "pip", "--isolated",
            "--disable-pip-version-check", "--no-cache-dir", "--quiet",
            "--python", venv_python, "install", "--no-input", "--no-index",
            "--no-deps", "--only-binary=:all:", "--no-compile",
            "--require-hashes", "--find-links", tool_wheelhouse,
            "--requirement", "<COMMAND_CWD>/candidate/bootstrap-pip.lock",
        ],
        "download_exact_build_tool_wheels": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "download", "--no-deps", "--only-binary=:all:",
            "--index-url", "<PRIMARY_INDEX_URL>", "--dest", tool_wheelhouse,
            "setuptools==74.0.0", "wheel==0.45.1",
        ],
        "install_exact_build_tools_in_isolated_venv": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "install", "--no-index", "--only-binary=:all:",
            "--require-hashes", "--find-links", tool_wheelhouse,
            "--requirement", "<COMMAND_CWD>/candidate/build-tools.lock",
        ],
        "verify_isolated_build_tool_versions": [
            venv_python,
            "-c",
            (
                "import json;from importlib import metadata;print(json.dumps("
                "{name:metadata.version(name) for name in "
                "('pip','setuptools','wheel')},sort_keys=True))"
            ),
        ],
        "build_project_wheel_from_source_copy": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "wheel", "--no-deps", "--no-build-isolation",
            "--wheel-dir", runtime_wheelhouse, "<COMMAND_CWD>/project-source",
        ],
        "resolve_exact_runtime_roots_to_wheels": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "download", "--only-binary=:all:", "--index-url",
            "<PRIMARY_INDEX_URL>", "--extra-index-url",
            "<PYTORCH_CPU_INDEX_URL>", "--dest", runtime_wheelhouse,
            "numpy==2.4.6", "scipy==1.17.1", "threadpoolctl==3.6.0",
            "torch==2.12.1+cpu",
        ],
        "install_hash_locked_wheelhouse_to_isolated_overlay": [
            venv_python, "-m", "pip", "--isolated", "--no-cache-dir",
            "--quiet", "install", "--no-index", "--only-binary=:all:",
            "--require-hashes", "--ignore-installed", "--no-compile",
            "--find-links", runtime_wheelhouse, "--prefix",
            "<COMMAND_CWD>/candidate/overlay", "--requirement",
            (
                "<COMMAND_CWD>/candidate/"
                "b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock.candidate"
            ),
        ],
    }.get(step)


def validate_journal_argv(step, argv, errors):
    identity_steps = {
        "bind_host_pip_identity_before_bootstrap": "<HOST_PYTHON>",
        "rebind_host_pip_identity_before_target_install": "<HOST_PYTHON>",
        "bind_isolated_venv_pip_identity_after_bootstrap": (
            "<COMMAND_CWD>/build-venv/bin/python"
        ),
        "rebind_isolated_venv_pip_identity_before_manifest": (
            "<COMMAND_CWD>/build-venv/bin/python"
        ),
    }
    if step in identity_steps:
        if (
            type(argv) is not list
            or len(argv) != 5
            or argv[:4] != [identity_steps[step], "-I", "-B", "-c"]
            or type(argv[4]) is not str
            or len(argv[4].encode("utf-8"))
            != EXPECTED_PIP_IDENTITY_PROBE_SIZE_BYTES
            or sha256_bytes(argv[4].encode("utf-8"))
            != EXPECTED_PIP_IDENTITY_PROBE_SHA256
        ):
            errors.append("FAILURE_COMMAND_JOURNAL_ARGV_BINDING_MISMATCH")
        return
    expected = expected_nonidentity_journal_argv(step)
    if expected is None or argv != expected:
        errors.append("FAILURE_COMMAND_JOURNAL_ARGV_BINDING_MISMATCH")


def validate_portable_pip_identity(value, expected_role, errors, label):
    expected_keys = {
        "pip_module_file_sha256",
        "pip_module_file_size_bytes",
        "pip_payload_closure_exact",
        "pip_payload_file_count",
        "pip_payload_hashed_record_count",
        "pip_payload_manifest_sha256",
        "pip_payload_unhashed_record_count",
        "pip_payload_unrecorded_bytecode_count",
        "pip_record_file_sha256",
        "pip_record_file_size_bytes",
        "pip_version",
        "runtime_role",
        "path_projection",
        "python_executable_relationship",
        "absolute_runtime_paths_persisted",
        "content_derived_payload_closure_persisted",
        "omitted_absolute_path_fields",
    }
    if type(value) is not dict or set(value) != expected_keys:
        errors.append(label + "_SHAPE_INVALID")
        return
    if value.get("runtime_role") != expected_role:
        errors.append(label + "_ROLE_INVALID")
    if value.get("pip_version") != "25.0.1":
        errors.append(label + "_VERSION_INVALID")
    for key in (
        "pip_module_file_sha256",
        "pip_payload_manifest_sha256",
        "pip_record_file_sha256",
    ):
        if not is_lower_hex_sha256(value.get(key)):
            errors.append(label + "_SHA256_INVALID:" + key)
    for key in ("pip_module_file_size_bytes", "pip_record_file_size_bytes"):
        if (
            type(value.get(key)) is not int
            or value.get(key) <= 0
            or value.get(key) > PIP_IDENTITY_CONTROL_FILE_BYTE_LIMIT
        ):
            errors.append(label + "_SIZE_INVALID:" + key)
    count_keys = (
        "pip_payload_file_count",
        "pip_payload_hashed_record_count",
        "pip_payload_unhashed_record_count",
        "pip_payload_unrecorded_bytecode_count",
    )
    counts = [value.get(key) for key in count_keys]
    if (
        value.get("pip_payload_closure_exact") is not True
        or any(
            type(item) is not int
            or item < 0
            or item > PIP_PAYLOAD_FILE_LIMIT
            for item in counts
        )
        or type(counts[0]) is not int
        or counts[0] < 3
        or (
            all(type(item) is int for item in counts)
            and counts[1] + counts[2] < 3
        )
        or all(type(item) is int for item in counts)
        and sum(counts[1:]) != counts[0]
    ):
        errors.append(label + "_PAYLOAD_CLOSURE_INVALID")
    paths = value.get("path_projection")
    expected_path_keys = {
        "pip_distribution_root_relative_to_install_prefix",
        "pip_module_file_relative_to_install_prefix",
        "pip_record_file_relative_to_install_prefix",
    }
    if type(paths) is not dict or set(paths) != expected_path_keys:
        errors.append(label + "_PATH_PROJECTION_INVALID")
    else:
        for path_value in paths.values():
            if (
                type(path_value) is not str
                or not path_value
                or path_value.startswith("/")
                or path_value.endswith("/")
                or "\\" in path_value
                or any(
                    part in ("", ".", "..")
                    for part in path_value.split("/")
                )
            ):
                errors.append(label + "_PATH_PROJECTION_INVALID")
                break
        else:
            distribution_path = paths[
                "pip_distribution_root_relative_to_install_prefix"
            ]
            module_path = paths[
                "pip_module_file_relative_to_install_prefix"
            ]
            record_path = paths[
                "pip_record_file_relative_to_install_prefix"
            ]
            distribution_parts = distribution_path.split("/")
            module_parts = module_path.split("/")
            record_parts = record_path.split("/")
            if (
                distribution_path != "lib/python3.12/site-packages"
                or module_parts != distribution_parts + ["pip", "__init__.py"]
                or len(record_parts) != len(distribution_parts) + 2
                or record_parts[: len(distribution_parts)]
                != distribution_parts
                or record_parts[-1] != "RECORD"
                or record_parts[-2] != "pip-25.0.1.dist-info"
            ):
                errors.append(label + "_PATH_RELATIONSHIP_INVALID")
    executable_relationship = value.get("python_executable_relationship")
    if executable_relationship not in {
        "RESOLVED_TARGET_OUTSIDE_INSTALL_PREFIX",
        "RESOLVED_TARGET_WITHIN_INSTALL_PREFIX",
    }:
        errors.append(label + "_EXECUTABLE_RELATIONSHIP_INVALID")
    elif (
        expected_role == "ISOLATED_BUILD_VENV"
        and executable_relationship != "RESOLVED_TARGET_WITHIN_INSTALL_PREFIX"
    ):
        errors.append(label + "_EXECUTABLE_RELATIONSHIP_INVALID")
    if value.get("absolute_runtime_paths_persisted") is not False:
        errors.append(label + "_ABSOLUTE_PATH_POLICY_INVALID")
    if value.get("content_derived_payload_closure_persisted") is not True:
        errors.append(label + "_PAYLOAD_POLICY_INVALID")
    if value.get("omitted_absolute_path_fields") != [
        "pip_install_prefix",
        "pip_distribution_root",
        "pip_module_file",
        "pip_record_file",
        "python_executable",
    ]:
        errors.append(label + "_OMITTED_PATHS_INVALID")


def validate_bootstrap_wheel_binding(value, errors):
    expected_keys = {
        "filename",
        "sha256",
        "size_bytes",
        "distribution_name",
        "normalized_name",
        "version",
        "wheel_tags",
        "embedded_record_sha256",
        "embedded_payload_file_count",
        "central_directory",
    }
    if type(value) is not dict or set(value) != expected_keys:
        errors.append("FAILURE_BOOTSTRAP_WHEEL_BINDING_SHAPE_INVALID")
        return
    if (
        value.get("filename") != "pip-25.0.1-py3-none-any.whl"
        or value.get("normalized_name") != "pip"
        or value.get("distribution_name") != "pip"
        or value.get("version") != "25.0.1"
        or not is_lower_hex_sha256(value.get("sha256"))
        or type(value.get("size_bytes")) is not int
        or value.get("size_bytes") <= 0
        or value.get("size_bytes") > WHEEL_FILE_BYTE_LIMIT
        or not is_lower_hex_sha256(value.get("embedded_record_sha256"))
        or type(value.get("embedded_payload_file_count")) is not int
        or value.get("embedded_payload_file_count") < 3
        or value.get("embedded_payload_file_count") > WHEEL_MEMBER_LIMIT
        or value.get("wheel_tags") != ["py3-none-any"]
    ):
        errors.append("FAILURE_BOOTSTRAP_WHEEL_BINDING_CONTENT_INVALID")
    central = value.get("central_directory")
    if type(central) is not dict or set(central) != {
        "entry_count", "size_bytes", "offset_bytes", "zip64"
    }:
        errors.append("FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID")
    elif (
        type(central.get("entry_count")) is not int
        or central.get("entry_count") <= 0
        or central.get("entry_count") > WHEEL_MEMBER_LIMIT
        or type(central.get("size_bytes")) is not int
        or central.get("size_bytes") <= 0
        or central.get("size_bytes") > WHEEL_CENTRAL_DIRECTORY_BYTE_LIMIT
        or type(central.get("offset_bytes")) is not int
        or central.get("offset_bytes") < 0
        or type(central.get("zip64")) is not bool
        or (
            type(value.get("embedded_payload_file_count")) is int
            and central.get("entry_count")
            < value.get("embedded_payload_file_count")
        )
        # Every accepted central-directory entry has a nonempty filename.
        # The exact pip wheel also has METADATA, RECORD, and WHEEL names whose
        # combined length exceeds the three one-byte minima by 79 bytes. Those
        # three required controls are nonempty, adding at least three compressed
        # payload bytes to the local-file area.
        or central.get("size_bytes")
        < 47 * central.get("entry_count") + 79
        or (
            type(value.get("embedded_payload_file_count")) is int
            and central.get("offset_bytes")
            < 31 * value.get("embedded_payload_file_count") + 82
        )
        or (
            central.get("zip64") is False
            and central.get("entry_count") >= 0xFFFF
        )
        or (
            type(value.get("size_bytes")) is int
            and central.get("offset_bytes")
            + central.get("size_bytes")
            + (98 if central.get("zip64") is True else 22)
            > value.get("size_bytes")
        )
    ):
        errors.append("FAILURE_BOOTSTRAP_WHEEL_CENTRAL_DIRECTORY_INVALID")


def validate_bootstrap_lock_binding(value, wheel_binding, errors):
    if (
        type(value) is not dict
        or set(value) != {"filename", "sha256"}
        or value.get("filename") != "bootstrap-pip.lock"
        or not is_lower_hex_sha256(value.get("sha256"))
    ):
        errors.append("FAILURE_BOOTSTRAP_LOCK_BINDING_INVALID")
        return
    if type(wheel_binding) is not dict:
        errors.append("FAILURE_BOOTSTRAP_LOCK_DERIVATION_UNAVAILABLE")
        return
    expected_lock = (
        "# REVIEW-PENDING F152 CANDIDATE; not an authority or runtime "
        "install instruction.\n"
        "# Install only after independent acceptance with --no-index "
        "--only-binary=:all: --require-hashes.\n"
        + str(wheel_binding.get("normalized_name"))
        + "=="
        + str(wheel_binding.get("version"))
        + " \\\n"
        + "    --hash=sha256:"
        + str(wheel_binding.get("sha256"))
        + "\n"
    ).encode("ascii")
    if value.get("sha256") != sha256_bytes(expected_lock):
        errors.append("FAILURE_BOOTSTRAP_LOCK_SHA256_DERIVATION_MISMATCH")


def diagnostic_stream_is_canonical_empty(stream):
    return (
        type(stream) is dict
        and stream.get("captured_byte_count") == 0
        and stream.get("observed_byte_count_before_termination") == 0
        and stream.get("captured_sha256") == sha256_bytes(b"")
        and stream.get("sanitized_tail_utf8") == ""
        and stream.get("capture_complete_through_process_termination")
        is False
    )


def validate_exception_diagnostic_reachability(
    execution_error,
    execution_detail,
    diagnostics,
    diagnostic_completeness,
    errors,
):
    if (
        type(diagnostics) is not dict
        or set(diagnostics) != {"stdout", "stderr"}
        or len(diagnostic_completeness) != 2
    ):
        return
    if execution_error == "TimeoutExpired":
        if any(value is not True for value in diagnostic_completeness):
            errors.append(
                "FAILURE_DIAGNOSTIC_TIMEOUT_CAPTURE_NOT_COMPLETE"
            )
        for stream_name in ("stdout", "stderr"):
            stream = diagnostics.get(stream_name)
            if type(stream) is not dict:
                continue
            captured = stream.get("captured_byte_count")
            observed = stream.get(
                "observed_byte_count_before_termination"
            )
            if (
                type(captured) is int
                and type(observed) is int
                and (
                    observed < captured
                    or observed - captured > READ_CHUNK_BYTES
                )
            ):
                errors.append(
                    "FAILURE_DIAGNOSTIC_TIMEOUT_COUNT_DELTA_INVALID:"
                    + stream_name
                )
        return
    if execution_error in EXPECTED_CANDIDATE_EXECUTION_ERROR_CODES:
        if any(value is not False for value in diagnostic_completeness):
            errors.append(
                "FAILURE_DIAGNOSTIC_CANDIDATE_ERROR_CAPTURE_NOT_INCOMPLETE"
            )
        if execution_error in {
            "TOOL_OUTPUT_READER_FAILED",
            "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED",
        }:
            # These branches are selected only after both reader threads have
            # quiesced. A reader can account for one returned chunk before a
            # buffer extension fails, so each stream's observed/captured lag
            # is bounded by exactly one read chunk.
            for stream_name in ("stdout", "stderr"):
                stream = diagnostics.get(stream_name)
                if type(stream) is not dict:
                    continue
                captured = stream.get("captured_byte_count")
                observed = stream.get(
                    "observed_byte_count_before_termination"
                )
                if (
                    type(captured) is int
                    and type(observed) is int
                    and (
                        observed < captured
                        or observed - captured > READ_CHUNK_BYTES
                    )
                ):
                    errors.append(
                        "FAILURE_DIAGNOSTIC_QUIESCENT_READER_COUNT_DELTA_"
                        "INVALID:"
                        + stream_name
                    )
        if execution_error == "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED":
            stream = diagnostics.get(execution_detail)
            if (
                type(stream) is not dict
                or stream.get("captured_byte_count")
                != MAX_CAPTURED_STREAM_BYTES
                or type(stream.get("observed_byte_count_before_termination"))
                is not int
                or stream.get("observed_byte_count_before_termination")
                <= MAX_CAPTURED_STREAM_BYTES
                or stream.get("observed_byte_count_before_termination")
                > MAX_CAPTURED_STREAM_BYTES + READ_CHUNK_BYTES
            ):
                errors.append(
                    "FAILURE_DIAGNOSTIC_STREAM_OVERFLOW_EVIDENCE_INVALID"
                )
        return
    if execution_error in EXPECTED_OS_EXECUTION_ERROR_TYPES:
        if any(value is not False for value in diagnostic_completeness):
            errors.append(
                "FAILURE_DIAGNOSTIC_POPEN_OS_ERROR_CAPTURE_NOT_INCOMPLETE"
            )
        if not all(
            diagnostic_stream_is_canonical_empty(diagnostics.get(name))
            for name in ("stdout", "stderr")
        ):
            errors.append(
                "FAILURE_DIAGNOSTIC_POPEN_OS_ERROR_NOT_CANONICAL_EMPTY"
            )


def validate_journal(journal, errors):
    if type(journal) is not list:
        errors.append("FAILURE_COMMAND_JOURNAL_NOT_ARRAY")
        return {"entry_count": 0, "journal_sha256": None, "entries": []}
    if len(journal) > MAX_COMMAND_JOURNAL_ENTRIES:
        errors.append("FAILURE_COMMAND_JOURNAL_EXCEEDS_BOUND")
        return {"entry_count": len(journal), "journal_sha256": None, "entries": []}
    public = []
    for ordinal, entry in enumerate(journal):
        if type(entry) is not dict:
            errors.append("FAILURE_COMMAND_JOURNAL_ENTRY_NOT_OBJECT")
            continue
        allowed_keys = {
            "step",
            "argv",
            "returncode",
            "execution_error",
            "execution_error_detail",
            "failure_diagnostics",
            "stdout_and_stderr_persisted",
            "output_excluded_as_nondeterministic_tool_telemetry",
        }
        if not {"step", "argv", "returncode", "stdout_and_stderr_persisted"}.issubset(
            entry
        ) or not set(entry).issubset(allowed_keys):
            errors.append("FAILURE_COMMAND_JOURNAL_ENTRY_SHAPE_INVALID")
        step = entry.get("step")
        if not is_safe_token(step):
            errors.append("FAILURE_COMMAND_JOURNAL_STEP_INVALID")
        returncode = entry.get("returncode")
        if returncode is not None and not is_linux_subprocess_returncode(
            returncode
        ):
            errors.append("FAILURE_COMMAND_JOURNAL_RETURNCODE_INVALID")
        argv = entry.get("argv")
        if (
            type(argv) is not list
            or not argv
            or len(argv) > MAX_JOURNAL_ARG_COUNT
            or any(
                type(argument) is not str
                or len(argument.encode("utf-8")) > MAX_JOURNAL_STRING_BYTES
                for argument in argv
            )
        ):
            errors.append("FAILURE_COMMAND_JOURNAL_ARGV_INVALID")
        else:
            validate_journal_argv(step, argv, errors)
        persistence = entry.get("stdout_and_stderr_persisted")
        if persistence not in (
            False,
            "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY",
        ):
            errors.append("FAILURE_COMMAND_JOURNAL_PERSISTENCE_INVALID")
        excluded = entry.get(
            "output_excluded_as_nondeterministic_tool_telemetry"
        )
        if excluded is not None and type(excluded) is not bool:
            errors.append("FAILURE_COMMAND_JOURNAL_OUTPUT_FLAG_INVALID")
        execution_error = entry.get("execution_error")
        if execution_error is not None and not is_safe_token(execution_error):
            errors.append("FAILURE_COMMAND_JOURNAL_EXECUTION_ERROR_INVALID")
        execution_detail = entry.get("execution_error_detail")
        if execution_detail is not None and (
            type(execution_detail) is not str
            or len(execution_detail.encode("utf-8"))
            > MAX_EXECUTION_DETAIL_BYTES
        ):
            errors.append("FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_INVALID")
        item = {
            "ordinal": ordinal,
            "step_binding": opaque_text_binding(step),
            "returncode": returncode,
        }
        if execution_error is not None:
            item["execution_error_binding"] = opaque_text_binding(
                execution_error
            )
        diagnostics = entry.get("failure_diagnostics")
        if returncode is None:
            if set(entry) != {
                "step",
                "argv",
                "returncode",
                "execution_error",
                "execution_error_detail",
                "failure_diagnostics",
                "stdout_and_stderr_persisted",
            }:
                errors.append(
                    "FAILURE_COMMAND_JOURNAL_EXCEPTION_SHAPE_INVALID"
                )
            if execution_error is None:
                errors.append("FAILURE_COMMAND_JOURNAL_OUTCOME_INCOMPLETE")
            if diagnostics is None:
                errors.append("FAILURE_COMMAND_JOURNAL_DIAGNOSTICS_REQUIRED")
            if persistence != "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY":
                errors.append("FAILURE_COMMAND_JOURNAL_PERSISTENCE_MISMATCH")
        elif execution_error is not None:
            errors.append("FAILURE_COMMAND_JOURNAL_OUTCOME_CONFLICT")
        elif returncode == 0:
            if set(entry) != {
                "step",
                "argv",
                "returncode",
                "stdout_and_stderr_persisted",
                "output_excluded_as_nondeterministic_tool_telemetry",
            }:
                errors.append(
                    "FAILURE_COMMAND_JOURNAL_SUCCESS_SHAPE_INVALID"
                )
            if diagnostics is not None or persistence is not False:
                errors.append("FAILURE_COMMAND_JOURNAL_SUCCESS_SHAPE_INVALID")
            if excluded is not True:
                errors.append("FAILURE_COMMAND_JOURNAL_SUCCESS_OUTPUT_FLAG_INVALID")
        else:
            if set(entry) != {
                "step",
                "argv",
                "returncode",
                "failure_diagnostics",
                "stdout_and_stderr_persisted",
                "output_excluded_as_nondeterministic_tool_telemetry",
            }:
                errors.append(
                    "FAILURE_COMMAND_JOURNAL_FAILURE_SHAPE_INVALID"
                )
            if diagnostics is None:
                errors.append("FAILURE_COMMAND_JOURNAL_DIAGNOSTICS_REQUIRED")
            if persistence != "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY":
                errors.append("FAILURE_COMMAND_JOURNAL_PERSISTENCE_MISMATCH")
            if excluded is not False:
                errors.append("FAILURE_COMMAND_JOURNAL_FAILURE_OUTPUT_FLAG_INVALID")
        if diagnostics is not None:
            if (
                type(diagnostics) is not dict
                or set(diagnostics) != {"stdout", "stderr"}
            ):
                errors.append("FAILURE_DIAGNOSTICS_NOT_OBJECT")
            else:
                safe_diagnostics = {}
                diagnostic_completeness = []
                for stream_name in ("stdout", "stderr"):
                    stream = diagnostics.get(stream_name)
                    expected_stream_keys = {
                        "captured_byte_count",
                        "captured_sha256",
                        "observed_byte_count_before_termination",
                        "capture_complete_through_process_termination",
                        "sanitized_tail_byte_limit",
                        "sanitized_tail_utf8",
                        "runtime_paths_and_exact_index_urls_sanitized",
                    }
                    if type(stream) is not dict or set(stream) != expected_stream_keys:
                        errors.append("FAILURE_DIAGNOSTIC_STREAM_NOT_OBJECT")
                        continue
                    captured = stream.get("captured_byte_count")
                    observed = stream.get(
                        "observed_byte_count_before_termination"
                    )
                    captured_sha256 = stream.get("captured_sha256")
                    capture_complete = stream.get(
                        "capture_complete_through_process_termination"
                    )
                    if (
                        type(captured) is not int
                        or captured < 0
                        or captured > MAX_CAPTURED_STREAM_BYTES
                    ):
                        errors.append("FAILURE_DIAGNOSTIC_CAPTURE_COUNT_INVALID")
                    if (
                        type(observed) is not int
                        or observed < 0
                        or observed > MAX_OBSERVED_STREAM_BYTES
                        or (type(captured) is int and observed < captured)
                    ):
                        errors.append("FAILURE_DIAGNOSTIC_OBSERVED_COUNT_INVALID")
                    if not is_lower_hex_sha256(captured_sha256):
                        errors.append("FAILURE_DIAGNOSTIC_CAPTURE_SHA256_INVALID")
                    if type(capture_complete) is not bool:
                        errors.append("FAILURE_DIAGNOSTIC_COMPLETENESS_INVALID")
                    else:
                        diagnostic_completeness.append(capture_complete)
                        if (
                            type(returncode) is int
                            and returncode != 0
                            and capture_complete is not True
                        ):
                            errors.append(
                                "FAILURE_DIAGNOSTIC_NONZERO_CAPTURE_INCOMPLETE"
                            )
                    tail_limit = stream.get("sanitized_tail_byte_limit")
                    if (
                        type(tail_limit) is not int
                        or tail_limit != MAX_DIAGNOSTIC_TAIL_BYTES
                    ):
                        errors.append("FAILURE_DIAGNOSTIC_TAIL_LIMIT_INVALID")
                    if stream.get(
                        "runtime_paths_and_exact_index_urls_sanitized"
                    ) is not True:
                        errors.append("FAILURE_DIAGNOSTIC_STREAM_NOT_SANITIZED")
                        continue
                    tail = stream.get("sanitized_tail_utf8")
                    if type(tail) is not str:
                        errors.append("FAILURE_DIAGNOSTIC_TAIL_NOT_STRING")
                        continue
                    if len(tail.encode("utf-8")) > MAX_DIAGNOSTIC_TAIL_BYTES:
                        errors.append("FAILURE_DIAGNOSTIC_TAIL_EXCEEDS_BOUND")
                        continue
                    if (
                        capture_complete is True
                        and type(observed) is int
                        and type(captured) is int
                        and observed != captured
                        and execution_error != "TimeoutExpired"
                    ):
                        errors.append(
                            "FAILURE_DIAGNOSTIC_COMPLETE_COUNT_MISMATCH"
                        )
                    if type(captured) is int and captured == 0:
                        if captured_sha256 != sha256_bytes(b""):
                            errors.append(
                                "FAILURE_DIAGNOSTIC_EMPTY_CAPTURE_SHA256_MISMATCH"
                            )
                        if tail != "":
                            errors.append(
                                "FAILURE_DIAGNOSTIC_EMPTY_CAPTURE_HAS_TAIL"
                            )
                    elif type(captured) is int and captured > 0:
                        if captured_sha256 == sha256_bytes(b""):
                            errors.append(
                                "FAILURE_DIAGNOSTIC_NONEMPTY_CAPTURE_HAS_"
                                "EMPTY_SHA256"
                            )
                        if tail == "":
                            errors.append(
                                "FAILURE_DIAGNOSTIC_NONEMPTY_CAPTURE_HAS_"
                                "EMPTY_TAIL"
                            )
                    safe_diagnostics[stream_name] = {
                        "captured_byte_count": captured,
                        "captured_sha256": captured_sha256,
                        "observed_byte_count_before_termination": observed,
                        "capture_complete_through_process_termination": (
                            capture_complete
                        ),
                        "sanitized_tail_size_bytes": len(
                            tail.encode("utf-8")
                        ),
                        "sanitized_tail_sha256": sha256_bytes(
                            tail.encode("utf-8")
                        ),
                    }
                if (
                    len(diagnostic_completeness) == 2
                    and diagnostic_completeness[0]
                    is not diagnostic_completeness[1]
                ):
                    errors.append(
                        "FAILURE_DIAGNOSTIC_STREAM_COMPLETENESS_DIVERGED"
                    )
                if returncode is None and execution_error is not None:
                    validate_exception_diagnostic_reachability(
                        execution_error,
                        execution_detail,
                        diagnostics,
                        diagnostic_completeness,
                        errors,
                    )
                item["failure_diagnostic_bindings"] = safe_diagnostics
        public.append(item)
    return {
        "entry_count": len(journal),
        "journal_sha256": sha256_bytes(canonical_json_bytes(journal)),
        "entries": public,
    }


def validate_failure_receipt(payload, actual_intent_sha256):
    errors = []
    receipt = parse_canonical_ascii_json(
        payload, "CONSTRUCTION_FAILURE_RECEIPT"
    )
    if set(receipt) != FAILURE_TOP_LEVEL_KEYS:
        errors.append("FAILURE_TOP_LEVEL_KEYS_MISMATCH")
    if receipt.get("schema_version") != FAILURE_RECEIPT_SCHEMA:
        errors.append("FAILURE_SCHEMA_MISMATCH")
    if (
        receipt.get("decision")
        != "TERMINAL_NO_GO_PARTIAL_OR_FAILED_ATTEMPT_REVIEW_REQUIRED"
    ):
        errors.append("FAILURE_DECISION_MISMATCH")
    if receipt.get("attempt_intent_sha256") != actual_intent_sha256:
        errors.append("FAILURE_RECEIPT_INTENT_BINDING_MISMATCH")
    error_code = receipt.get("error_code")
    if not is_safe_token(error_code):
        errors.append("FAILURE_ERROR_CODE_INVALID")
    error_detail = receipt.get("error_detail")
    if error_detail is not None and type(error_detail) is not str:
        errors.append("FAILURE_ERROR_DETAIL_INVALID")
    elif (
        type(error_detail) is str
        and len(error_detail.encode("utf-8")) > MAX_ERROR_DETAIL_BYTES
    ):
        errors.append("FAILURE_ERROR_DETAIL_EXCEEDS_BOUND")
    if not strict_json_equal(
        receipt.get("safety"), EXPECTED_FAILURE_SAFETY
    ):
        errors.append("FAILURE_SAFETY_PROJECTION_MISMATCH")
    if not strict_json_equal(
        receipt.get("not_proven"), EXPECTED_FAILURE_NONPROOFS
    ):
        errors.append("FAILURE_NONPROOFS_MISMATCH")

    state = receipt.get("attempt_state_before_failure_receipt_commit")
    if type(state) is not dict:
        errors.append("FAILURE_ATTEMPT_STATE_NOT_OBJECT")
        state = {}
    allowed_state_keys = REQUIRED_ATTEMPT_STATE_KEYS | {
        "staging_cleanup_error"
    }
    for key in sorted(REQUIRED_ATTEMPT_STATE_KEYS - set(state)):
        errors.append("FAILURE_ATTEMPT_STATE_REQUIRED_KEY_MISSING:" + key)
    if set(state) - allowed_state_keys:
        errors.append("FAILURE_ATTEMPT_STATE_UNEXPECTED_KEYS")
    if (
        "staging_cleanup_error" in state
        and not is_ascii_identifier(state.get("staging_cleanup_error"))
    ):
        errors.append("FAILURE_STAGING_CLEANUP_ERROR_INVALID")
    if (
        state.get("staging_cleanup_begun") is True
        and state.get("staging_cleanup_completed") is False
        and "staging_cleanup_error" not in state
    ):
        errors.append("FAILURE_STAGING_CLEANUP_OUTCOME_INCOMPLETE")
    if (
        state.get("staging_cleanup_completed") is True
        and "staging_cleanup_error" in state
    ):
        errors.append("FAILURE_STAGING_CLEANUP_OUTCOME_CONFLICT")
    for key in sorted(ATTEMPT_STATE_BOOLEAN_KEYS & set(state)):
        if type(state[key]) is not bool:
            errors.append("FAILURE_ATTEMPT_STATE_BOOLEAN_INVALID:" + key)
    if state.get("package_resolution_begun") is not state.get(
        "network_contact_begun"
    ):
        errors.append("FAILURE_ATTEMPT_STATE_NETWORK_RESOLUTION_DIVERGED")
    causal_implications = (
        (
            "postintent_source_identity_verification_completed",
            "postintent_source_identity_verification_begun",
        ),
        (
            "staging_write_begun",
            "postintent_source_identity_verification_completed",
        ),
        ("staged_source_manifest_verified", "staging_write_begun"),
        ("isolated_venv_creation_begun", "staged_source_manifest_verified"),
        ("network_contact_begun", "isolated_venv_creation_begun"),
        ("bootstrap_pip_install_begun", "network_contact_begun"),
        ("project_wheel_build_begun", "build_tool_install_begun"),
        ("overlay_install_begun", "project_wheel_build_begun"),
        ("managed_uc_payload_publish_begun", "overlay_install_begun"),
        ("staging_cleanup_begun", "staging_write_begun"),
        ("staging_cleanup_completed", "staging_cleanup_begun"),
    )
    for later, prerequisite in causal_implications:
        if state.get(later) is True and state.get(prerequisite) is not True:
            errors.append(
                "FAILURE_ATTEMPT_STATE_CAUSALITY_INVALID:"
                + later
                + "_REQUIRES_"
                + prerequisite
            )
    if state.get("bootstrap_pip_install_begun") is not state.get(
        "build_tool_install_begun"
    ):
        errors.append("FAILURE_ATTEMPT_STATE_BOOTSTRAP_BUILD_FLAGS_DIVERGED")
    required_true = (
        "attempt_namespace_spent",
        "intent_create_begun",
        "durable_intent_committed",
        "durable_intent_may_exist",
        "managed_uc_write_phase_entered",
        "managed_uc_write_begun",
        "preintent_source_identity_verification_begun",
        "preintent_source_identity_verification_completed",
        "failure_receipt_commit_begun",
    )
    for key in required_true:
        if state.get(key) is not True:
            errors.append("FAILURE_ATTEMPT_STATE_REQUIRED_TRUE:" + key)
    required_false = (
        "success_receipt_phase_entered",
        "success_receipt_create_call_begun",
        "success_receipt_may_exist",
        "success_receipt_committed",
        "terminal_receipt_ambiguity",
        "failure_receipt_create_call_begun",
        "failure_receipt_may_exist",
        "failure_receipt_committed",
        "failure_receipt_skipped_for_terminal_receipt_ambiguity",
    )
    for key in required_false:
        if state.get(key) is not False:
            errors.append("FAILURE_ATTEMPT_STATE_REQUIRED_FALSE:" + key)
    if state.get("durable_intent_expected_sha256") != actual_intent_sha256:
        errors.append("FAILURE_STATE_INTENT_SHA256_MISMATCH")
    if (
        type(state.get("durable_intent_expected_size_bytes")) is not int
        or state.get("durable_intent_expected_size_bytes")
        != EXPECTED_INTENT_SIZE_BYTES
    ):
        errors.append("FAILURE_STATE_INTENT_SIZE_MISMATCH")
    if state.get("failure_receipt_error_code") is not None:
        errors.append("FAILURE_PRECOMMIT_RECEIPT_ERROR_CODE_NOT_NONE")
    if state.get("failure_receipt_error_detail") is not None:
        errors.append("FAILURE_PRECOMMIT_RECEIPT_ERROR_DETAIL_NOT_NONE")
    for key in ("last_started_step", "last_completed_step", "last_failed_step"):
        value = state.get(key)
        if value is not None and not is_safe_token(value):
            errors.append("FAILURE_ATTEMPT_STATE_STAGE_INVALID:" + key)
    if not is_safe_token(state.get("last_failed_step")):
        errors.append("FAILURE_LAST_FAILED_STEP_INVALID")
    journal = state.get("command_journal")
    journal_projection = validate_journal(journal, errors)
    observed_journal_steps = (
        [entry.get("step") for entry in journal]
        if type(journal) is list
        and all(type(entry) is dict for entry in journal)
        else []
    )
    if type(journal) is not list or not journal:
        errors.append(
            "FAILURE_COMMAND_JOURNAL_EXACT_NONEMPTY_PREFIX_REQUIRED"
        )
    elif (
        len(journal) > len(EXPECTED_TOOL_JOURNAL_STEPS)
        or observed_journal_steps
        != list(EXPECTED_TOOL_JOURNAL_STEPS[: len(journal)])
    ):
        errors.append("FAILURE_COMMAND_JOURNAL_STEP_PREFIX_MISMATCH")
    failed_journal_entries = []
    if type(journal) is list:
        for ordinal, entry in enumerate(journal):
            if type(entry) is not dict:
                continue
            returncode = entry.get("returncode")
            execution_error = entry.get("execution_error")
            if (
                type(returncode) is int
                and returncode != 0
            ) or execution_error is not None:
                failed_journal_entries.append((ordinal, entry))
    if len(failed_journal_entries) != 1:
        errors.append(
            "FAILURE_COMMAND_JOURNAL_EXACTLY_ONE_FAILURE_REQUIRED"
        )
    if len(failed_journal_entries) == 1:
        failure_ordinal, failure_entry = failed_journal_entries[-1]
        if type(journal) is list and failure_ordinal != len(journal) - 1:
            errors.append("FAILURE_COMMAND_JOURNAL_FAILURE_NOT_FINAL")
        if failure_entry.get("step") != state.get("last_failed_step"):
            errors.append("FAILURE_COMMAND_JOURNAL_FAILED_STEP_MISMATCH")
        if failure_entry.get("step") != state.get("last_started_step"):
            errors.append("FAILURE_COMMAND_JOURNAL_STARTED_STEP_MISMATCH")
        expected_last_completed = (
            EXPECTED_TOOL_JOURNAL_STEPS[failure_ordinal - 1]
            if failure_ordinal > 0
            else "create_isolated_build_venv"
        )
        if state.get("last_completed_step") != expected_last_completed:
            errors.append(
                "FAILURE_COMMAND_JOURNAL_LAST_COMPLETED_STEP_MISMATCH"
            )

        exact_reachable_flags = {
            "postintent_source_identity_verification_begun": True,
            "postintent_source_identity_verification_completed": True,
            "staging_write_begun": True,
            "staged_source_manifest_verified": True,
            "isolated_venv_creation_begun": True,
            "network_contact_begun": failure_ordinal >= 1,
            "package_resolution_begun": failure_ordinal >= 1,
            "host_pip_identity_reverified_before_target_install": (
                failure_ordinal >= 3
            ),
            "bootstrap_pip_install_begun": failure_ordinal >= 3,
            "build_tool_install_begun": failure_ordinal >= 3,
            "project_wheel_build_begun": failure_ordinal >= 8,
            "overlay_install_begun": failure_ordinal >= 10,
            "managed_uc_payload_publish_begun": False,
            "success_receipt_phase_entered": False,
            "staging_cleanup_begun": True,
        }
        for key, expected_value in exact_reachable_flags.items():
            if state.get(key) is not expected_value:
                errors.append(
                    "FAILURE_ATTEMPT_STATE_REACHABILITY_MISMATCH:" + key
                )

        exact_mapping_presence = {
            "host_pip_identity": failure_ordinal >= 1,
            "bootstrap_pip_wheel_binding": failure_ordinal >= 2,
            "bootstrap_pip_lock_binding": failure_ordinal >= 2,
            "isolated_venv_pip_identity": failure_ordinal >= 5,
        }
        for key, expected_present in exact_mapping_presence.items():
            value = state.get(key)
            if expected_present:
                if type(value) is not dict or not value:
                    errors.append(
                        "FAILURE_ATTEMPT_STATE_REQUIRED_MAPPING_MISSING:"
                        + key
                    )
            elif value is not None:
                errors.append(
                    "FAILURE_ATTEMPT_STATE_PREMATURE_MAPPING:" + key
                )
        if failure_ordinal >= 1:
            validate_portable_pip_identity(
                state.get("host_pip_identity"),
                "HOST_NOTEBOOK_INTERPRETER",
                errors,
                "FAILURE_HOST_PIP_IDENTITY",
            )
        if failure_ordinal >= 2:
            bootstrap_wheel_binding = state.get(
                "bootstrap_pip_wheel_binding"
            )
            validate_bootstrap_wheel_binding(
                bootstrap_wheel_binding, errors
            )
            validate_bootstrap_lock_binding(
                state.get("bootstrap_pip_lock_binding"),
                bootstrap_wheel_binding,
                errors,
            )
        if failure_ordinal >= 5:
            validate_portable_pip_identity(
                state.get("isolated_venv_pip_identity"),
                "ISOLATED_BUILD_VENV",
                errors,
                "FAILURE_ISOLATED_PIP_IDENTITY",
            )
        failure_returncode = failure_entry.get("returncode")
        failure_execution_error = failure_entry.get("execution_error")
        if type(failure_returncode) is int and failure_returncode != 0:
            if (
                error_code != "TOOL_STEP_FAILED"
                or failure_execution_error is not None
            ):
                errors.append("FAILURE_COMMAND_JOURNAL_NONZERO_BINDING_MISMATCH")
            expected_error_detail = (
                str(failure_entry.get("step"))
                + ":returncode="
                + str(failure_returncode)
            )
            if error_detail != expected_error_detail:
                errors.append(
                    "FAILURE_COMMAND_JOURNAL_NONZERO_DETAIL_MISMATCH"
                )
            journal_failure_class = "SUBPROCESS_NONZERO_EXIT"
        elif failure_execution_error is not None:
            failure_execution_detail = failure_entry.get(
                "execution_error_detail"
            )
            if failure_execution_error in EXPECTED_CANDIDATE_EXECUTION_ERROR_CODES:
                expected_error_code = failure_execution_error
                if (
                    failure_execution_error
                    == "TOOL_OUTPUT_READER_DID_NOT_QUIESCE"
                    and failure_execution_detail is not None
                ):
                    errors.append(
                        "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH"
                    )
                elif (
                    failure_execution_error
                    == "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED"
                    and failure_execution_detail not in {"stdout", "stderr"}
                ):
                    errors.append(
                        "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH"
                    )
                elif failure_execution_error == "TOOL_OUTPUT_READER_FAILED":
                    detail_parts = (
                        failure_execution_detail.split(":", 1)
                        if type(failure_execution_detail) is str
                        else []
                    )
                    if (
                        len(detail_parts) != 2
                        or detail_parts[0] not in {"stdout", "stderr"}
                        or failure_execution_detail.count(":") != 1
                        or not is_ascii_identifier(detail_parts[1])
                    ):
                        errors.append(
                            "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH"
                        )
                elif (
                    failure_execution_error
                    == "TOOL_SUBPROCESS_SUPERVISOR_FAILED"
                    and not is_ascii_identifier(failure_execution_detail)
                ):
                    errors.append(
                        "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH"
                    )
            elif failure_execution_error in EXPECTED_OS_EXECUTION_ERROR_TYPES:
                expected_error_code = "TOOL_STEP_EXECUTION_FAILED"
                if failure_execution_detail is not None:
                    errors.append(
                        "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH"
                    )
            else:
                expected_error_code = None
                errors.append(
                    "FAILURE_COMMAND_JOURNAL_EXECUTION_ERROR_CLASS_INVALID"
                )
            if error_code != expected_error_code:
                errors.append(
                    "FAILURE_COMMAND_JOURNAL_EXECUTION_ERROR_BINDING_MISMATCH"
                )
            expected_error_detail = (
                str(failure_entry.get("step"))
                + ":"
                + str(failure_execution_error)
                + (
                    ""
                    if failure_execution_detail is None
                    else ":" + str(failure_execution_detail)
                )
            )
            if error_detail != expected_error_detail:
                errors.append(
                    "FAILURE_COMMAND_JOURNAL_EXECUTION_DETAIL_MISMATCH"
                )
            journal_failure_class = "SUBPROCESS_EXECUTION_EXCEPTION"
        else:
            journal_failure_class = "INVALID_JOURNALED_FAILURE"
    else:
        failure_ordinal = None
        failure_returncode = None
        journal_failure_class = "UNVERIFIED_NONJOURNALED_FAILURE"

    confirmed = state.get("managed_uc_confirmed_bindings")
    if type(confirmed) is not list:
        errors.append("FAILURE_CONFIRMED_BINDINGS_NOT_ARRAY")
        confirmed = []
    validated_bindings = []
    for binding in confirmed:
        if type(binding) is not dict or set(binding) != {
            "name",
            "sha256",
            "size_bytes",
            "fresh_readback_count",
        }:
            errors.append("FAILURE_CONFIRMED_BINDING_SHAPE_INVALID")
            continue
        if binding.get("name") not in reserved_leaf_names():
            errors.append("FAILURE_CONFIRMED_BINDING_NAME_INVALID")
        if not is_lower_hex_sha256(binding.get("sha256")):
            errors.append("FAILURE_CONFIRMED_BINDING_SHA256_INVALID")
        if (
            type(binding.get("size_bytes")) is not int
            or binding.get("size_bytes") <= 0
        ):
            errors.append("FAILURE_CONFIRMED_BINDING_SIZE_INVALID")
        if (
            type(binding.get("fresh_readback_count")) is not int
            or binding.get("fresh_readback_count") != 2
        ):
            errors.append("FAILURE_CONFIRMED_BINDING_READBACK_COUNT_INVALID")
        validated_bindings.append(binding)
    binding_names = [binding.get("name") for binding in validated_bindings]
    if len(binding_names) != len(set(binding_names)):
        errors.append("FAILURE_CONFIRMED_BINDING_NAMES_NOT_UNIQUE")
    expected_intent_binding = {
        "name": INTENT_LEAF_NAME,
        "sha256": actual_intent_sha256,
        "size_bytes": EXPECTED_INTENT_SIZE_BYTES,
        "fresh_readback_count": 2,
    }
    matching_intent_bindings = [
        binding for binding in validated_bindings
        if strict_json_equal(binding, expected_intent_binding)
    ]
    if len(matching_intent_bindings) != 1:
        errors.append("FAILURE_CONFIRMED_INTENT_BINDING_NOT_EXACTLY_ONE")
    if any(name != INTENT_LEAF_NAME for name in binding_names):
        errors.append("FAILURE_CONFIRMED_NONCONTROL_BINDING_NOT_CURRENTLY_VISIBLE")
    confirmed_count = state.get("managed_uc_confirmed_leaf_count")
    confirmed_bytes = state.get("managed_uc_confirmed_bytes_written")
    if type(confirmed_count) is not int or confirmed_count < 0:
        errors.append("FAILURE_CONFIRMED_LEAF_COUNT_INVALID")
    elif confirmed_count != len(validated_bindings):
        errors.append("FAILURE_CONFIRMED_LEAF_COUNT_MISMATCH")
    valid_sizes = [
        binding["size_bytes"] for binding in validated_bindings
        if type(binding.get("size_bytes")) is int
        and binding.get("size_bytes") > 0
    ]
    if type(confirmed_bytes) is not int or confirmed_bytes < 0:
        errors.append("FAILURE_CONFIRMED_BYTE_COUNT_INVALID")
    elif confirmed_bytes != sum(valid_sizes):
        errors.append("FAILURE_CONFIRMED_BYTE_COUNT_MISMATCH")
    last_confirmed = state.get("managed_uc_last_confirmed_binding")
    expected_last_confirmed = (
        validated_bindings[-1] if validated_bindings else None
    )
    if not strict_json_equal(last_confirmed, expected_last_confirmed):
        errors.append("FAILURE_LAST_CONFIRMED_BINDING_MISMATCH")
    if state.get("managed_uc_last_leaf_create_begun") != INTENT_LEAF_NAME:
        errors.append("FAILURE_LAST_LEAF_CREATE_NAME_MISMATCH")
    if state.get("managed_uc_last_leaf_may_exist") != INTENT_LEAF_NAME:
        errors.append("FAILURE_LAST_LEAF_MAY_EXIST_NAME_MISMATCH")
    if state.get("managed_uc_last_leaf_expected_sha256") != actual_intent_sha256:
        errors.append("FAILURE_LAST_LEAF_EXPECTED_SHA256_MISMATCH")
    if (
        type(state.get("managed_uc_last_leaf_expected_size_bytes")) is not int
        or state.get("managed_uc_last_leaf_expected_size_bytes")
        != EXPECTED_INTENT_SIZE_BYTES
    ):
        errors.append("FAILURE_LAST_LEAF_EXPECTED_SIZE_MISMATCH")
    create_calls = state.get("managed_uc_exclusive_create_calls_begun")
    if (
        type(create_calls) is not int
        or create_calls != 1
    ):
        errors.append("FAILURE_EXCLUSIVE_CREATE_CALL_COUNT_INVALID")

    return receipt, {
        "valid": not errors,
        "errors": errors,
        "file_sha256": sha256_bytes(payload),
        "size_bytes": len(payload),
        "diagnosis": {
            "failure_class": journal_failure_class,
            "failed_journal_entry_ordinal": failure_ordinal,
            "failed_journal_returncode": failure_returncode,
            "error_code_binding": opaque_text_binding(error_code),
            "error_detail_binding": opaque_text_binding(error_detail),
            "stage_bindings": {
                "last_started_step": opaque_text_binding(
                    state.get("last_started_step")
                ),
                "last_completed_step": opaque_text_binding(
                    state.get("last_completed_step")
                ),
                "last_failed_step": opaque_text_binding(
                    state.get("last_failed_step")
                ),
            },
            "network_contact_begun": state.get("network_contact_begun"),
            "package_resolution_begun": state.get(
                "package_resolution_begun"
            ),
            "isolated_venv_creation_begun": state.get(
                "isolated_venv_creation_begun"
            ),
            "bootstrap_pip_install_begun": state.get(
                "bootstrap_pip_install_begun"
            ),
            "build_tool_install_begun": state.get(
                "build_tool_install_begun"
            ),
            "project_wheel_build_begun": state.get(
                "project_wheel_build_begun"
            ),
            "overlay_install_begun": state.get("overlay_install_begun"),
            "managed_uc_payload_publish_begun": state.get(
                "managed_uc_payload_publish_begun"
            ),
            "staging_cleanup_begun": state.get("staging_cleanup_begun"),
            "staging_cleanup_completed": state.get(
                "staging_cleanup_completed"
            ),
            "managed_uc_exclusive_create_calls_begun": state.get(
                "managed_uc_exclusive_create_calls_begun"
            ),
            "managed_uc_confirmed_leaf_count": state.get(
                "managed_uc_confirmed_leaf_count"
            ),
            "managed_uc_confirmed_bytes_written": state.get(
                "managed_uc_confirmed_bytes_written"
            ),
            "command_journal": journal_projection,
        },
    }


def custody_projection(pair_completed):
    return {
        "required_basis": (
            "TWO_INDEPENDENT_PATH_VISIBLE_RESERVED_NAMESPACE_AND_"
            "CONTROL_CONTENT_SNAPSHOTS"
        ),
        "required_snapshot_pair_completed": pair_completed,
        "flat_sibling_object_protocol": True,
        "virtual_candidate_directory_required": False,
        "object_storage_semantics": True,
        "device_inode_mode_timestamp_used_for_acceptance": False,
        "historical_object_identity_claimed": False,
        "receipt_writer_identity_authenticated": False,
        "receipt_builder_authorship_claimed": False,
        "atomic_snapshot_claimed": False,
        "freshness_or_cache_coherence_claimed": False,
        "immutability_claimed": False,
        "physical_durability_claimed": False,
        "future_stability_claimed": False,
    }


def safety_projection(observation_state, completed):
    return {
        "applies_only_to_this_forensic_run": True,
        "read_only_parent_open_flags_only": True,
        "mutating_filesystem_operation_requested_by_notebook": False,
        "unexpected_or_payload_leaf_payload_opened_or_read": False,
        "control_payload_open_may_have_begun": observation_state[
            "control_payload_open_may_have_begun"
        ],
        "control_payload_read_syscall_may_have_begun": observation_state[
            "control_payload_read_syscall_may_have_begun"
        ],
        "control_payload_read_syscall_completed": observation_state[
            "control_payload_read_syscall_completed"
        ],
        "positive_control_payload_bytes_observed": observation_state[
            "positive_control_payload_bytes_observed"
        ],
        "control_payload_bytes_read_total": observation_state[
            "control_payload_bytes_read_total"
        ],
        "control_payload_reads_completed": observation_state[
            "control_payload_reads_completed"
        ],
        "snapshot_pair_completed": completed,
        "direct_external_network_endpoint_accessed": False,
        "databricks_managed_storage_io_attempted": observation_state[
            "databricks_managed_storage_io_attempted"
        ],
        "databricks_managed_storage_io_may_have_been_performed": (
            observation_state[
                "databricks_managed_storage_io_may_have_been_performed"
            ]
        ),
        "parent_descriptor_open_completed_count": observation_state[
            "parent_descriptor_open_completed_count"
        ],
        "subprocess_or_package_operation_executed": False,
        "spark_or_databricks_rest_accessed": False,
        "study_or_test_data_accessed": False,
        "calibration_training_or_inference_executed": False,
    }


def inspect_candidate(observation_state):
    first = snapshot(1, observation_state)
    second = snapshot(2, observation_state)
    first_public = first["projection"]
    second_public = second["projection"]
    snapshots_equal = (
        first_public == second_public
        and first["projection_sha256"] == second["projection_sha256"]
        and first["control_payloads"] == second["control_payloads"]
    )
    common = {
        "schema_version": SCHEMA_VERSION,
        "scope": "DATA_FREE_READ_ONLY_CANDIDATE_003_FORENSICS_ONLY",
        "target_parent": EXACT_PARENT,
        "candidate_id": CANDIDATE_ID,
        "virtual_candidate_prefix": VIRTUAL_CANDIDATE_PREFIX,
        "exact_hard_coded_target_only": True,
        "construction_or_reuse_authorized": False,
        "candidate_004_authorized": False,
        "snapshot_count_attempted": observation_state[
            "snapshot_count_attempted"
        ],
        "snapshot_count_completed": observation_state[
            "snapshot_count_completed"
        ],
        "snapshots_equal": snapshots_equal,
        "snapshot_projections": [first_public, second_public],
        "custody_model": custody_projection(True),
        "bounds": {
            "reserved_leaf_count": len(reserved_leaf_names()),
            "control_leaf_payload_allowlist": list(CONTROL_LEAF_NAMES),
            "maximum_control_leaf_bytes": MAX_CONTROL_LEAF_BYTES,
            "read_chunk_bytes": READ_CHUNK_BYTES,
        },
        "expected_intent_binding_basis": {
            "size_bytes": EXPECTED_INTENT_SIZE_BYTES,
            "file_sha256": EXPECTED_INTENT_FILE_SHA256,
            "internal_record_sha256": EXPECTED_INTENT_RECORD_SHA256,
            "review_binding_mode_basis": "THREE_DATABRICKS_OBSERVED_0755_BINDINGS",
            "review_package_sha256": EXPECTED_REVIEW_PACKAGE_SHA256,
        },
    }
    if not snapshots_equal:
        any_path_visible = any(
            bool(projection["present_reserved_leaves"])
            or projection["virtual_candidate_prefix"]["kind"] != "ABSENT"
            for projection in (first_public, second_public)
        )
        return {
            **common,
            "decision": "HOLD_FORENSIC_PATH_SNAPSHOTS_NOT_REPEATABLE",
            "candidate_disposition": (
                "PERMANENTLY_SPENT_UNRESOLVED"
                if any_path_visible
                else "SPENT_NOT_ESTABLISHED_BY_THIS_CAPTURE"
            ),
            "safety": safety_projection(observation_state, True),
        }

    projection = first_public
    present_names = [
        item["name"] for item in projection["present_reserved_leaves"]
    ]
    virtual_kind = projection["virtual_candidate_prefix"]["kind"]
    unresolved_disposition = (
        "PERMANENTLY_SPENT_UNRESOLVED"
        if present_names or virtual_kind != "ABSENT"
        else "SPENT_NOT_ESTABLISHED_BY_THIS_CAPTURE"
    )
    success_visible = SUCCESS_RECEIPT_LEAF_NAME in present_names
    payload_or_manifest_visible = any(
        name == PAYLOAD_MANIFEST_LEAF_NAME
        or name.startswith(f"{CANDIDATE_ID}.payload-")
        for name in present_names
    )
    if virtual_kind != "ABSENT":
        return {
            **common,
            "decision": "HOLD_VIRTUAL_CANDIDATE_PREFIX_NOT_ABSENT",
            "candidate_disposition": unresolved_disposition,
            "safety": safety_projection(observation_state, True),
        }
    if success_visible:
        return {
            **common,
            "decision": "HOLD_TERMINAL_RECEIPT_AMBIGUITY",
            "candidate_disposition": "PERMANENTLY_SPENT_TERMINAL_AMBIGUITY",
            "safety": safety_projection(observation_state, True),
        }
    if payload_or_manifest_visible:
        return {
            **common,
            "decision": "HOLD_PARTIAL_CANDIDATE_NAMESPACE_REVIEW_REQUIRED",
            "candidate_disposition": "PERMANENTLY_SPENT_PARTIAL_PAYLOAD_VISIBLE",
            "safety": safety_projection(observation_state, True),
        }
    if set(present_names) != set(CONTROL_LEAF_NAMES):
        return {
            **common,
            "decision": "HOLD_EXPECTED_CONTROL_PAIR_INCOMPLETE",
            "candidate_disposition": unresolved_disposition,
            "safety": safety_projection(observation_state, True),
        }
    unread = [
        name for name, binding in projection["control_leaves"].items()
        if binding.get("payload_read") is not True
    ]
    if unread:
        return {
            **common,
            "decision": "HOLD_ALLOWLISTED_CONTROL_LEAF_UNREAD",
            "unread_control_leaf_names": sorted(unread),
            "candidate_disposition": unresolved_disposition,
            "safety": safety_projection(observation_state, True),
        }

    intent_payload = first["control_payloads"][INTENT_LEAF_NAME]
    failure_payload = first["control_payloads"][FAILURE_RECEIPT_LEAF_NAME]
    try:
        _, intent_validation = validate_intent(intent_payload)
        _, failure_validation = validate_failure_receipt(
            failure_payload,
            sha256_bytes(intent_payload),
        )
    except RuntimeError as error:
        return {
            **common,
            "decision": "HOLD_FORENSIC_CONTROL_PARSE_FAILED",
            "error_detail": str(error),
            "candidate_disposition": "PERMANENTLY_SPENT_UNRESOLVED",
            "safety": safety_projection(observation_state, True),
        }
    validation_errors = (
        intent_validation["errors"] + failure_validation["errors"]
    )
    result = {
        **common,
        "control_validation": {
            "intent": intent_validation,
            "failure_receipt": {
                key: value for key, value in failure_validation.items()
                if key != "diagnosis"
            },
        },
        "candidate_disposition": (
            "PERMANENTLY_SPENT_SCHEMA_CONFORMANT_TERMINAL_FAILURE"
            if not validation_errors
            else "PERMANENTLY_SPENT_UNRESOLVED"
        ),
        "safety": safety_projection(observation_state, True),
    }
    if validation_errors:
        result["decision"] = "HOLD_FORENSIC_CONTROL_VALIDATION_FAILED"
        result["validation_errors"] = validation_errors
    else:
        result[
            "decision"
        ] = (
            "PASS_READ_ONLY_FORENSIC_SCHEMA_CONFORMANT_JOURNALED_"
            "TERMINAL_FAILURE_RECEIPT"
        )
        result[
            "forensic_classification"
        ] = (
            "SCHEMA_CONFORMANT_EXPECTED_INTENT_LINKED_JOURNALED_"
            "TERMINAL_FAILURE_RECEIPT"
        )
        result["diagnosis"] = failure_validation["diagnosis"]
    return result


def public_failure(error, observation_state):
    snapshot_pair_completed = (
        observation_state["snapshot_count_completed"] == 2
        and len(observation_state["completed_projection_sha256s"]) == 2
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "DATA_FREE_READ_ONLY_CANDIDATE_003_FORENSICS_ONLY",
        "decision": "READ_ONLY_CANDIDATE_003_FORENSIC_INSPECTION_FAILED",
        "target_parent": EXACT_PARENT,
        "candidate_id": CANDIDATE_ID,
        "exact_hard_coded_target_only": True,
        "error_type_binding": opaque_text_binding(type(error).__name__),
        "error_detail_binding": opaque_text_binding(str(error)),
        "snapshot_count_attempted": observation_state[
            "snapshot_count_attempted"
        ],
        "snapshot_count_completed": observation_state[
            "snapshot_count_completed"
        ],
        "active_snapshot_ordinal_at_failure": observation_state[
            "active_snapshot_ordinal"
        ],
        "completed_projection_sha256s": observation_state[
            "completed_projection_sha256s"
        ],
        "custody_model": custody_projection(snapshot_pair_completed),
        "candidate_disposition": (
            "PERMANENTLY_SPENT_UNRESOLVED"
            if observation_state["reserved_path_visibility_observed"]
            else "SPENT_STATUS_UNRESOLVED_BY_THIS_CAPTURE"
        ),
        "construction_or_reuse_authorized": False,
        "candidate_004_authorized": False,
        "safety": safety_projection(
            observation_state, snapshot_pair_completed
        ),
    }


def capture_candidate():
    observation_state = {
        "snapshot_count_attempted": 0,
        "snapshot_count_completed": 0,
        "active_snapshot_ordinal": None,
        "completed_projection_sha256s": [],
        "databricks_managed_storage_io_attempted": False,
        "databricks_managed_storage_io_may_have_been_performed": False,
        "parent_descriptor_open_completed_count": 0,
        "reserved_path_visibility_observed": False,
        "control_payload_open_may_have_begun": False,
        "control_payload_read_syscall_may_have_begun": False,
        "control_payload_read_syscall_completed": False,
        "positive_control_payload_bytes_observed": False,
        "control_payload_bytes_read_total": 0,
        "control_payload_reads_completed": 0,
    }
    try:
        validate_frozen_contract()
        return inspect_candidate(observation_state)
    except BaseException as error:
        return public_failure(error, observation_state)


def main():
    print(json.dumps(capture_candidate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
