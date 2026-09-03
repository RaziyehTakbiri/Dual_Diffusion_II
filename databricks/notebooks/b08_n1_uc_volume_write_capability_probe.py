# Databricks notebook source
# MAGIC %md
# MAGIC # B08 N1 — bounded Unity Catalog Volume write-capability probe
# MAGIC
# MAGIC Candidate-002 proved that its intent reached complete expected bytes and
# MAGIC its unparsed failure receipt reached stable path-visible bytes, even though
# MAGIC the old writer rejected a later POSIX
# MAGIC durability/identity step. This notebook therefore tests only the storage
# MAGIC properties required by the replacement writer: exclusive create, complete
# MAGIC sequential write and close, fresh-descriptor size/SHA-256 readback,
# MAGIC no-clobber collision behavior, and a bounded two-process create race.
# MAGIC
# MAGIC The probe is data-free and targets two exact retained control-object paths
# MAGIC below the existing `b08_runtime_output` Volume; PASS requires two exact
# MAGIC 4 KiB payloads. It performs
# MAGIC at most four exclusive-create calls; PASS requires exactly four. It writes
# MAGIC at most 12 KiB even if the race primitive is broken. It performs no fsync,
# MAGIC chmod/chown, inode/device
# MAGIC acceptance, rename, deletion, package operation, direct external endpoint,
# MAGIC Spark or Databricks REST call, or scientific execution. Databricks-managed
# MAGIC Unity Catalog storage I/O is the exact capability under test. The default
# MAGIC mode is read
# MAGIC only. An authorized attempt is one-shot; after any create call begins, do
# MAGIC not rerun it regardless of outcome.

# COMMAND ----------

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import select
import stat
import subprocess
import sys
import time


SCHEMA_VERSION = "heterodiff-b08-n1-uc-volume-write-capability-probe-v1"
RUN_MODE = "RUN_ONE_BOUNDED_UC_VOLUME_WRITE_CAPABILITY_PROBE"
ACKNOWLEDGEMENT_TEXT = (
    "AUTHORIZE_ONE_DATA_FREE_UC_VOLUME_WRITE_CAPABILITY_PROBE_001"
)
PROBE_ID = "b08-n1-uc-volume-write-capability-probe-001"
PROBE_PARENT = Path(
    "/Volumes/development/team_eds_supplychain/b08_runtime_output"
)
PRIMARY_LEAF = PROBE_PARENT / f"{PROBE_ID}-primary.bin"
RACE_LEAF = PROBE_PARENT / f"{PROBE_ID}-race.bin"
PAYLOAD_BYTES = 4096
READ_CHUNK_BYTES = 4096
MAX_CONTROL_LEAF_BYTES = 4096
EXCLUSIVE_CREATE_CALL_LIMIT = 4
MAXIMUM_POSSIBLE_PAYLOAD_BYTES_WRITTEN = 3 * PAYLOAD_BYTES
CHILD_TIMEOUT_SECONDS = 30

EXPECTED_ENVIRONMENT = {
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


# COMMAND ----------

_WIDGET_API = globals().get("dbutils")
_WIDGET_INPUT_ACCESSED = _WIDGET_API is not None


def operator_choice(name, default, label, choices):
    if _WIDGET_API is None:
        return default
    _WIDGET_API.widgets.dropdown(name, default, list(choices), label)
    return _WIDGET_API.widgets.get(name)


EXECUTION_MODE = operator_choice(
    "b08_n1_uc_volume_probe_mode",
    "PREFLIGHT_ONLY",
    "UC Volume capability-probe mode",
    ("PREFLIGHT_ONLY", RUN_MODE),
)
_WRITE_AUTHORIZATION_TEXT = operator_choice(
    "b08_n1_uc_volume_probe_write_authorized",
    "false",
    "Authorize two retained leaves, four create attempts, max 12 KiB",
    ("false", "true"),
)
WRITE_AUTHORIZED = _WRITE_AUTHORIZATION_TEXT == "true"
ONE_SHOT_ACKNOWLEDGEMENT = operator_choice(
    "b08_n1_uc_volume_probe_acknowledgement",
    "NOT_AUTHORIZED",
    "One-shot probe acknowledgement",
    ("NOT_AUTHORIZED", ACKNOWLEDGEMENT_TEXT),
)


# COMMAND ----------

class ProbeError(RuntimeError):
    def __init__(self, code, detail=None):
        super().__init__(code if detail is None else f"{code}: {detail}")
        self.code = code
        self.detail = detail


def canonical_json_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def fixed_payload(label):
    values = {
        "PRIMARY": b"P",
        "COLLISION": b"C",
        "RACE_A": b"A",
        "RACE_B": b"B",
    }
    if label not in values:
        raise ProbeError("INVALID_FIXED_PAYLOAD_LABEL")
    return values[label] * PAYLOAD_BYTES


PAYLOAD_BINDINGS = {
    label: {
        "sha256": sha256_bytes(fixed_payload(label)),
        "size_bytes": PAYLOAD_BYTES,
    }
    for label in ("PRIMARY", "COLLISION", "RACE_A", "RACE_B")
}


def object_kind(path):
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return "ABSENT"
    if stat.S_ISREG(observed.st_mode):
        return "REGULAR_FILE"
    if stat.S_ISDIR(observed.st_mode):
        return "DIRECTORY"
    if stat.S_ISLNK(observed.st_mode):
        return "SYMLINK"
    return "OTHER"


def validate_fixed_paths(parent, primary_leaf, race_leaf):
    errors = []
    expected_parent = PurePosixPath(
        "/Volumes/development/team_eds_supplychain/b08_runtime_output"
    )
    observed_parent = PurePosixPath(str(parent))
    if observed_parent != expected_parent:
        errors.append("PROBE_PARENT_NOT_EXACT")
    if not observed_parent.is_absolute() or observed_parent.parts[:2] != (
        "/",
        "Volumes",
    ):
        errors.append("PROBE_PARENT_NOT_UNITY_CATALOG_VOLUME_PATH")
    if primary_leaf.parent != parent or race_leaf.parent != parent:
        errors.append("PROBE_LEAF_OUTSIDE_EXACT_PARENT")
    if primary_leaf == race_leaf:
        errors.append("PROBE_LEAF_NAMES_NOT_DISTINCT")
    if primary_leaf != parent / f"{PROBE_ID}-primary.bin":
        errors.append("PRIMARY_PROBE_LEAF_NOT_EXACT")
    if race_leaf != parent / f"{PROBE_ID}-race.bin":
        errors.append("RACE_PROBE_LEAF_NOT_EXACT")
    return errors


def observe_kind_for_preflight(label, path, errors):
    try:
        return object_kind(path)
    except OSError as error:
        errors.append(label + "_VISIBILITY_FAILED:" + type(error).__name__)
        return "UNAVAILABLE"


def runtime_observation():
    observed = {
        "architecture": platform.machine(),
        "databricks_runtime_version": os.environ.get(
            "DATABRICKS_RUNTIME_VERSION"
        ),
        "python_version": platform.python_version(),
    }
    expected = {
        "architecture": "x86_64",
        "databricks_runtime_version": "17.3",
        "python_version": "3.12.3",
    }
    mismatches = {
        name: {"expected": expected[name], "observed": observed[name]}
        for name in expected
        if observed[name] != expected[name]
    }
    return {
        "exact": not mismatches,
        "expected": expected,
        "mismatches": mismatches,
        "observed": observed,
    }


def environment_observation(environment=None):
    source = os.environ if environment is None else environment
    observed = {name: source.get(name) for name in EXPECTED_ENVIRONMENT}
    mismatches = {
        name: {
            "expected": EXPECTED_ENVIRONMENT[name],
            "observed": observed[name],
        }
        for name in EXPECTED_ENVIRONMENT
        if observed[name] != EXPECTED_ENVIRONMENT[name]
    }
    return {
        "exact": not mismatches,
        "expected": EXPECTED_ENVIRONMENT,
        "mismatches": mismatches,
        "observed": observed,
    }


def preflight(
    execution_mode=None,
    write_authorized=None,
    acknowledgement=None,
    parent=PROBE_PARENT,
    primary_leaf=PRIMARY_LEAF,
    race_leaf=RACE_LEAF,
    runtime=None,
    environment=None,
):
    selected_mode = EXECUTION_MODE if execution_mode is None else execution_mode
    selected_write_authorized = (
        WRITE_AUTHORIZED if write_authorized is None else write_authorized
    )
    selected_acknowledgement = (
        ONE_SHOT_ACKNOWLEDGEMENT
        if acknowledgement is None
        else acknowledgement
    )
    runtime_result = runtime_observation() if runtime is None else runtime
    environment_result = environment_observation(environment)
    errors = validate_fixed_paths(parent, primary_leaf, race_leaf)

    parent_kind = observe_kind_for_preflight("PROBE_PARENT", parent, errors)
    primary_kind = observe_kind_for_preflight(
        "PRIMARY_PROBE_LEAF",
        primary_leaf,
        errors,
    )
    race_kind = observe_kind_for_preflight(
        "RACE_PROBE_LEAF",
        race_leaf,
        errors,
    )
    if parent_kind != "DIRECTORY":
        errors.append("EXACT_PROBE_PARENT_NOT_DIRECTORY")
    if primary_kind != "ABSENT":
        errors.append("PRIMARY_PROBE_LEAF_MUST_BE_ABSENT")
    if race_kind != "ABSENT":
        errors.append("RACE_PROBE_LEAF_MUST_BE_ABSENT")
    if not runtime_result["exact"]:
        errors.append("RUNTIME_PROFILE_MISMATCH")
    if not environment_result["exact"]:
        errors.append("DETERMINISTIC_ENVIRONMENT_MISMATCH")
    required_features = {
        "O_CLOEXEC": hasattr(os, "O_CLOEXEC"),
        "O_DIRECTORY": hasattr(os, "O_DIRECTORY"),
        "O_NOFOLLOW": hasattr(os, "O_NOFOLLOW"),
        "dir_fd_for_open": os.open in os.supports_dir_fd,
        "dir_fd_for_stat": os.stat in os.supports_dir_fd,
        "follow_symlinks_for_stat": os.stat in os.supports_follow_symlinks,
    }
    if not all(required_features.values()):
        errors.append("REQUIRED_EXCLUSIVE_CREATE_PRIMITIVE_UNAVAILABLE")

    required_inputs = []
    if selected_mode != RUN_MODE:
        required_inputs.append("EXECUTION_MODE=" + RUN_MODE)
    if selected_write_authorized is not True:
        required_inputs.append("WRITE_AUTHORIZED=True")
    if selected_acknowledgement != ACKNOWLEDGEMENT_TEXT:
        required_inputs.append(
            "ONE_SHOT_ACKNOWLEDGEMENT=" + ACKNOWLEDGEMENT_TEXT
        )

    authorized = not errors and not required_inputs
    if authorized:
        decision = "PROCEED_ONE_BOUNDED_UC_VOLUME_WRITE_CAPABILITY_PROBE"
    elif errors:
        decision = "HOLD_UC_VOLUME_PROBE_PREFLIGHT_FAILED"
    else:
        decision = "HOLD_UC_VOLUME_PROBE_AUTHORITY_INCOMPLETE"

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "DATA_FREE_UC_VOLUME_WRITE_CAPABILITY_PROBE_ONLY",
        "decision": decision,
        "probe_authorized": authorized,
        "probe_id": PROBE_ID,
        "fixed_paths": {
            "parent": str(parent),
            "parent_kind": parent_kind,
            "primary_leaf": str(primary_leaf),
            "primary_leaf_kind": primary_kind,
            "race_leaf": str(race_leaf),
            "race_leaf_kind": race_kind,
        },
        "bounds": {
            "exclusive_create_call_limit": EXCLUSIVE_CREATE_CALL_LIMIT,
            "maximum_possible_payload_bytes_written": (
                MAXIMUM_POSSIBLE_PAYLOAD_BYTES_WRITTEN
            ),
            "payload_bytes_per_successful_writer": PAYLOAD_BYTES,
            "probe_leaf_count": 2,
            "read_chunk_bytes": READ_CHUNK_BYTES,
        },
        "payload_bindings": PAYLOAD_BINDINGS,
        "required_features": required_features,
        "runtime": runtime_result,
        "environment": environment_result,
        "required_inputs": sorted(required_inputs),
        "errors": sorted(set(errors)),
        "safety": {
            "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
            "files_written": False,
            "child_processes_started": False,
            "fsync_chmod_chown_inode_device_rename_or_delete_used": False,
            "databricks_managed_storage_io_may_have_been_performed": True,
            "direct_external_network_endpoint_accessed": False,
            "package_resolution_build_or_install_executed": False,
            "spark_or_databricks_rest_accessed": False,
            "study_or_test_data_accessed": False,
            "calibration_training_or_inference_executed": False,
            "unity_catalog_volume_metadata_io_attempted": True,
            "unity_catalog_volume_payload_io_attempted": False,
        },
    }


# COMMAND ----------

def validate_leaf_name(name):
    if (
        type(name) is not str
        or not name
        or name in (".", "..")
        or "/" in name
        or "\\" in name
    ):
        raise ProbeError("INVALID_CONTROL_LEAF_NAME")


def open_parent_descriptor(parent):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open(parent, flags)
    try:
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise ProbeError("OPENED_PROBE_PARENT_NOT_DIRECTORY")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def read_binding(parent, leaf_name):
    validate_leaf_name(leaf_name)
    parent_descriptor = open_parent_descriptor(parent)
    descriptor = None
    try:
        before = os.stat(
            leaf_name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            raise ProbeError("CONTROL_LEAF_NOT_REGULAR", leaf_name)
        if before.st_size > MAX_CONTROL_LEAF_BYTES:
            raise ProbeError("CONTROL_LEAF_SIZE_EXCEEDS_BOUND", leaf_name)

        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        descriptor = os.open(
            leaf_name,
            flags,
            dir_fd=parent_descriptor,
        )
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ProbeError("OPENED_CONTROL_LEAF_NOT_REGULAR", leaf_name)
        if opened.st_size > MAX_CONTROL_LEAF_BYTES:
            raise ProbeError(
                "OPENED_CONTROL_LEAF_SIZE_EXCEEDS_BOUND", leaf_name
            )
        digest = hashlib.sha256()
        size = 0
        while True:
            remaining = MAX_CONTROL_LEAF_BYTES + 1 - size
            if remaining <= 0:
                raise ProbeError("CONTROL_LEAF_READ_EXCEEDS_BOUND", leaf_name)
            chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining))
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            if size > MAX_CONTROL_LEAF_BYTES:
                raise ProbeError("CONTROL_LEAF_READ_EXCEEDS_BOUND", leaf_name)
    finally:
        try:
            if descriptor is not None:
                os.close(descriptor)
        finally:
            os.close(parent_descriptor)

    if size != before.st_size or size != opened.st_size:
        raise ProbeError("CONTROL_LEAF_SIZE_UNSTABLE", leaf_name)
    return {
        "name": leaf_name,
        "sha256": digest.hexdigest(),
        "size_bytes": size,
    }


def require_binding(parent, leaf_name, payload):
    observed = read_binding(parent, leaf_name)
    expected = {
        "name": leaf_name,
        "sha256": sha256_bytes(payload),
        "size_bytes": len(payload),
    }
    if observed != expected:
        raise ProbeError("CONTROL_LEAF_BINDING_MISMATCH", leaf_name)
    return observed


def write_payload_exclusive(
    parent,
    leaf_name,
    payload,
    state,
    role,
    write_payload=True,
):
    validate_leaf_name(leaf_name)
    if len(payload) != PAYLOAD_BYTES:
        raise ProbeError("PROBE_PAYLOAD_SIZE_NOT_EXACT", role)
    if (
        state["exclusive_create_calls_begun_or_may_have_begun"]
        >= EXCLUSIVE_CREATE_CALL_LIMIT
    ):
        raise ProbeError("EXCLUSIVE_CREATE_CALL_LIMIT_EXCEEDED")
    state["last_started_operation"] = role
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= os.O_NOFOLLOW | os.O_CLOEXEC
    parent_descriptor = open_parent_descriptor(parent)
    descriptor = None
    offset = 0
    try:
        state["exclusive_create_calls_begun_or_may_have_begun"] += 1
        state["direct_exclusive_create_calls_begun"] += 1
        descriptor = os.open(
            leaf_name,
            flags,
            0o600,
            dir_fd=parent_descriptor,
        )
        state["confirmed_successful_create_count"] += 1
        if write_payload:
            state["payload_write_begun"] = True
            while offset < len(payload):
                written = os.write(descriptor, payload[offset:])
                if written <= 0:
                    raise ProbeError("CONTROL_LEAF_WRITE_MADE_NO_PROGRESS", role)
                offset += written
    finally:
        try:
            if descriptor is not None:
                os.close(descriptor)
        finally:
            os.close(parent_descriptor)
    if write_payload:
        state["confirmed_complete_payload_bytes_written"] += offset
    state["last_completed_operation"] = role


RACE_CHILD_SOURCE = r'''
import hashlib
import json
import os
import stat
import sys

label = sys.argv[1]
parent = sys.argv[2]
leaf_name = sys.argv[3]
payload_size = int(sys.argv[4])
payload_byte = {"RACE_A": b"A", "RACE_B": b"B"}[label]
payload = payload_byte * payload_size
parent_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
parent_descriptor = os.open(parent, parent_flags)
if not stat.S_ISDIR(os.fstat(parent_descriptor).st_mode):
    os.close(parent_descriptor)
    raise RuntimeError("OPENED_PROBE_PARENT_NOT_DIRECTORY")
sys.stdout.write("READY\n")
sys.stdout.flush()
if sys.stdin.buffer.read(1) != b"G":
    os.close(parent_descriptor)
    raise RuntimeError("START_SIGNAL_INVALID")
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
descriptor = None
result = {"label": label, "open_succeeded": False, "status": None}
try:
    descriptor = os.open(leaf_name, flags, 0o600, dir_fd=parent_descriptor)
except FileExistsError:
    result["status"] = "COLLISION"
except BaseException as error:
    result["status"] = "ERROR"
    result["error_phase"] = "OPEN"
    result["error_type"] = type(error).__name__
else:
    result["open_succeeded"] = True
    offset = 0
    try:
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise RuntimeError("WRITE_MADE_NO_PROGRESS")
            offset += written
    except BaseException as error:
        result["status"] = "ERROR"
        result["error_phase"] = "WRITE"
        result["error_type"] = type(error).__name__
        result["bytes_written_before_error"] = offset
    else:
        result["status"] = "CREATED"
        result["sha256"] = hashlib.sha256(payload).hexdigest()
        result["size_bytes"] = len(payload)
    finally:
        try:
            os.close(descriptor)
        except BaseException as error:
            result["status"] = "ERROR"
            result["error_phase"] = "CLOSE"
            result["error_type"] = type(error).__name__
            result["bytes_written_before_error"] = offset
        descriptor = None
finally:
    try:
        if descriptor is not None:
            os.close(descriptor)
    finally:
        os.close(parent_descriptor)
sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")))
'''.strip()


def terminate_children(processes):
    rows = []
    for process in processes:
        try:
            if process.poll() is None:
                process.kill()
        except (OSError, ProcessLookupError):
            pass
    for process in processes:
        try:
            if process.poll() is None:
                process.wait(timeout=5)
        except (OSError, ProcessLookupError, subprocess.TimeoutExpired):
            pass
    for ordinal, process in enumerate(processes):
        try:
            returncode = process.poll()
        except (OSError, ProcessLookupError):
            returncode = None
        rows.append(
            {
                "ordinal": ordinal,
                "quiescence_confirmed": returncode is not None,
                "returncode": returncode,
            }
        )
    return {
        "all_children_quiescent": all(
            row["quiescence_confirmed"] for row in rows
        ),
        "children": rows,
        "termination_requested": True,
    }


def observe_completed_children(processes):
    rows = []
    for ordinal, process in enumerate(processes):
        returncode = process.poll()
        rows.append(
            {
                "ordinal": ordinal,
                "quiescence_confirmed": returncode is not None,
                "returncode": returncode,
            }
        )
    return {
        "all_children_quiescent": all(
            row["quiescence_confirmed"] for row in rows
        ),
        "children": rows,
        "termination_requested": False,
    }


def close_child_pipes(processes):
    for process in processes:
        for name in ("stdin", "stdout", "stderr"):
            stream = getattr(process, name, None)
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass


def validate_race_results(results, state):
    if (
        type(results) is not list
        or len(results) != 2
        or any(type(item) is not dict for item in results)
    ):
        raise ProbeError("RACE_CHILD_RESULT_ROSTER_INVALID")
    labels = [item.get("label") for item in results]
    if any(type(label) is not str for label in labels) or sorted(labels) != [
        "RACE_A",
        "RACE_B",
    ]:
        raise ProbeError("RACE_CHILD_LABEL_ROSTER_INVALID")

    created = [item for item in results if item.get("status") == "CREATED"]
    collisions = [
        item for item in results if item.get("status") == "COLLISION"
    ]
    if len(created) != 1 or len(collisions) != 1:
        raise ProbeError("RACE_DID_NOT_HAVE_EXACTLY_ONE_WINNER", repr(results))

    winner = created[0]
    expected_winner = {
        "label": winner["label"],
        "open_succeeded": True,
        "sha256": PAYLOAD_BINDINGS[winner["label"]]["sha256"],
        "size_bytes": PAYLOAD_BYTES,
        "status": "CREATED",
    }
    if winner != expected_winner:
        raise ProbeError("RACE_WINNER_REPORT_BINDING_INVALID")
    if collisions[0] != {
        "label": collisions[0]["label"],
        "open_succeeded": False,
        "status": "COLLISION",
    }:
        raise ProbeError("RACE_COLLISION_REPORT_INVALID")
    state["confirmed_successful_create_count"] += 1
    state["confirmed_complete_payload_bytes_written"] += PAYLOAD_BYTES
    state["payload_write_begun"] = True
    return winner


def run_two_process_race(parent, leaf_name, state):
    validate_leaf_name(leaf_name)
    processes = []
    labels = ("RACE_A", "RACE_B")
    try:
        for label in labels:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    RACE_CHILD_SOURCE,
                    label,
                    str(parent),
                    leaf_name,
                    str(PAYLOAD_BYTES),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(process)
        state["child_processes_started"] = 2

        pending_streams = {process.stdout for process in processes}
        deadline = time.monotonic() + CHILD_TIMEOUT_SECONDS
        while pending_streams:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProbeError("RACE_CHILD_READY_TIMEOUT")
            readable, _, _ = select.select(
                list(pending_streams),
                [],
                [],
                remaining,
            )
            if not readable:
                raise ProbeError("RACE_CHILD_READY_TIMEOUT")
            for stream in readable:
                if stream.readline() != b"READY\n":
                    raise ProbeError("RACE_CHILD_READY_SIGNAL_INVALID")
                pending_streams.remove(stream)

        if (
            state["exclusive_create_calls_begun_or_may_have_begun"]
            + len(processes)
            > EXCLUSIVE_CREATE_CALL_LIMIT
        ):
            raise ProbeError("EXCLUSIVE_CREATE_CALL_LIMIT_EXCEEDED")
        for process in processes:
            state["exclusive_create_calls_begun_or_may_have_begun"] += 1
            state["race_create_releases_or_calls_may_have_begun"] += 1
            process.stdin.write(b"G")
            process.stdin.flush()
            process.stdin.close()
            process.stdin = None

        results = []
        for process in processes:
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(process.args, 0)
                stdout, stderr = process.communicate(timeout=remaining)
            except subprocess.TimeoutExpired as error:
                raise ProbeError("RACE_CHILD_TIMEOUT") from error
            if process.returncode != 0 or stderr:
                raise ProbeError(
                    "RACE_CHILD_PROCESS_FAILED",
                    f"returncode={process.returncode}",
                )
            try:
                results.append(json.loads(stdout.decode("ascii")))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ProbeError("RACE_CHILD_OUTPUT_INVALID") from error

        state["race_child_cleanup"] = observe_completed_children(processes)
        if not state["race_child_cleanup"]["all_children_quiescent"]:
            raise ProbeError("RACE_CHILD_QUIESCENCE_NOT_CONFIRMED")
        winner = validate_race_results(results, state)
        return {
            "child_results": sorted(results, key=lambda item: item["label"]),
            "winner": winner,
        }
    except BaseException:
        state["child_processes_started"] = len(processes)
        state["race_child_cleanup"] = terminate_children(processes)
        raise
    finally:
        close_child_pipes(processes)


def fresh_state():
    return {
        "attempt_spent": False,
        "child_processes_started": 0,
        "direct_exclusive_create_calls_begun": 0,
        "exclusive_create_calls_begun_or_may_have_begun": 0,
        "last_completed_operation": None,
        "last_failed_operation": None,
        "last_started_operation": None,
        "confirmed_complete_payload_bytes_written": 0,
        "payload_write_begun": False,
        "race_create_releases_or_calls_may_have_begun": 0,
        "race_child_cleanup": None,
        "confirmed_successful_create_count": 0,
    }


def run_probe(
    parent=PROBE_PARENT,
    primary_leaf=PRIMARY_LEAF,
    race_leaf=RACE_LEAF,
):
    state = fresh_state()
    primary_payload = fixed_payload("PRIMARY")
    collision_payload = fixed_payload("COLLISION")
    try:
        if object_kind(primary_leaf) != "ABSENT":
            raise ProbeError("PRIMARY_PROBE_LEAF_MUST_BE_ABSENT")
        if object_kind(race_leaf) != "ABSENT":
            raise ProbeError("RACE_PROBE_LEAF_MUST_BE_ABSENT")

        state["attempt_spent"] = True
        write_payload_exclusive(
            parent,
            primary_leaf.name,
            primary_payload,
            state,
            "PRIMARY_EXCLUSIVE_CREATE_AND_WRITE",
        )
        primary_before_collision = require_binding(
            parent,
            primary_leaf.name,
            primary_payload,
        )

        state["last_started_operation"] = "PRIMARY_INTENTIONAL_COLLISION"
        try:
            write_payload_exclusive(
                parent,
                primary_leaf.name,
                collision_payload,
                state,
                "PRIMARY_INTENTIONAL_COLLISION",
                write_payload=False,
            )
        except FileExistsError:
            collision_result = "FILE_EXISTS_ERROR"
            state["last_completed_operation"] = (
                "PRIMARY_INTENTIONAL_COLLISION"
            )
        else:
            raise ProbeError("PRIMARY_COLLISION_UNEXPECTEDLY_CREATED")
        primary_after_collision = require_binding(
            parent,
            primary_leaf.name,
            primary_payload,
        )
        if primary_before_collision != primary_after_collision:
            raise ProbeError("PRIMARY_BINDING_CHANGED_ACROSS_COLLISION")

        state["last_started_operation"] = "TWO_PROCESS_RACE"
        race = run_two_process_race(parent, race_leaf.name, state)
        winner_payload = fixed_payload(race["winner"]["label"])
        race_readback_1 = require_binding(
            parent,
            race_leaf.name,
            winner_payload,
        )
        race_readback_2 = require_binding(
            parent,
            race_leaf.name,
            winner_payload,
        )
        if race_readback_1 != race_readback_2:
            raise ProbeError("RACE_BINDING_NOT_REPEATABLE")
        state["last_completed_operation"] = "TWO_PROCESS_RACE"

        if (
            state["exclusive_create_calls_begun_or_may_have_begun"]
            != EXCLUSIVE_CREATE_CALL_LIMIT
        ):
            raise ProbeError("EXCLUSIVE_CREATE_CALL_COUNT_NOT_EXACT")
        if state["confirmed_successful_create_count"] != 2:
            raise ProbeError("SUCCESSFUL_CREATE_COUNT_NOT_EXACT")
        if (
            state["confirmed_complete_payload_bytes_written"]
            != 2 * PAYLOAD_BYTES
        ):
            raise ProbeError("PAYLOAD_BYTES_WRITTEN_NOT_EXACT")

        return {
            "schema_version": SCHEMA_VERSION,
            "scope": "DATA_FREE_UC_VOLUME_WRITE_CAPABILITY_PROBE_ONLY",
            "decision": (
                "PASS_UC_VOLUME_EXCLUSIVE_CREATE_AND_REPEATABLE_"
                "READBACK_CAPABILITY"
            ),
            "probe_id": PROBE_ID,
            "attempt_state": state,
            "primary": {
                "binding_before_collision": primary_before_collision,
                "collision_result": collision_result,
                "binding_after_collision": primary_after_collision,
            },
            "race": {
                **race,
                "readback_1": race_readback_1,
                "readback_2": race_readback_2,
            },
            "bounds": {
                "exclusive_create_call_limit": EXCLUSIVE_CREATE_CALL_LIMIT,
                "exclusive_create_calls_used": state[
                    "exclusive_create_calls_begun_or_may_have_begun"
                ],
                "maximum_possible_payload_bytes_written": (
                    MAXIMUM_POSSIBLE_PAYLOAD_BYTES_WRITTEN
                ),
                "confirmed_complete_payload_bytes_written": state[
                    "confirmed_complete_payload_bytes_written"
                ],
                "preserved_leaf_count": 2,
            },
            "payload_bindings": PAYLOAD_BINDINGS,
            "preservation": {
                "delete_rename_repair_or_rerun_permitted": False,
                "primary_leaf": str(primary_leaf),
                "race_leaf": str(race_leaf),
            },
            "nonproofs": [
                "ATOMIC_SNAPSHOT",
                "CACHE_COHERENCE",
                "FUTURE_RUNTIME_OR_FUSE_STABILITY",
                "HISTORICAL_OBJECT_IDENTITY_OR_LINEAGE",
                "IMMUTABILITY",
                "UNIVERSAL_ATOMICITY",
            ],
            "project_delta": {
                "b08_closed": False,
                "f151_closed": False,
                "f152_closed": False,
                "formal_tests": ["OPEN", "OPEN", "PENDING"],
                "marked_tasks_complete_open_total": [62, 101, 163],
                "wave_2_closed": False,
            },
            "safety": {
                "files_written": True,
                "child_processes_started": True,
                "fsync_chmod_chown_inode_device_rename_or_delete_used": False,
                "databricks_managed_storage_io_performed": True,
                "direct_external_network_endpoint_accessed": False,
                "package_resolution_build_or_install_executed": False,
                "spark_or_databricks_rest_accessed": False,
                "study_or_test_data_accessed": False,
                "calibration_training_or_inference_executed": False,
                "unity_catalog_volume_io_attempted": True,
                "unity_catalog_volume_io_performed": True,
            },
        }
    except BaseException as error:
        state["last_failed_operation"] = state["last_started_operation"]
        if isinstance(error, ProbeError):
            error_code = error.code
            error_detail = error.detail
        else:
            error_code = type(error).__name__
            error_detail = str(error)
        child_cleanup = state.get("race_child_cleanup")
        child_quiescence_confirmed = (
            child_cleanup is None
            or child_cleanup.get("all_children_quiescent") is True
        )
        if state["attempt_spent"] and not child_quiescence_confirmed:
            decision = (
                "TERMINAL_NO_GO_SPENT_UC_VOLUME_CAPABILITY_PROBE_"
                "CLUSTER_TERMINATION_REQUIRED"
            )
        elif state["attempt_spent"]:
            decision = (
                "TERMINAL_NO_GO_SPENT_UC_VOLUME_CAPABILITY_PROBE_"
                "REVIEW_REQUIRED"
            )
        else:
            decision = "NO_GO_UNSPENT_UC_VOLUME_CAPABILITY_PROBE"
        return {
            "schema_version": SCHEMA_VERSION,
            "scope": "DATA_FREE_UC_VOLUME_WRITE_CAPABILITY_PROBE_ONLY",
            "decision": decision,
            "probe_id": PROBE_ID,
            "error_code": error_code,
            "error_detail": error_detail,
            "attempt_state": state,
            "preservation": {
                "delete_rename_repair_or_rerun_permitted": False,
                "terminate_cluster_before_forensics_required": (
                    not child_quiescence_confirmed
                ),
                "primary_leaf": str(primary_leaf),
                "race_leaf": str(race_leaf),
            },
            "payload_bindings": PAYLOAD_BINDINGS,
            "project_delta": {
                "b08_closed": False,
                "f151_closed": False,
                "f152_closed": False,
                "formal_tests": ["OPEN", "OPEN", "PENDING"],
                "marked_tasks_complete_open_total": [62, 101, 163],
                "wave_2_closed": False,
            },
            "safety": {
                "files_may_have_been_written": state["attempt_spent"],
                "child_processes_may_have_started": bool(
                    state["child_processes_started"]
                ),
                "race_child_quiescence_confirmed": (
                    child_quiescence_confirmed
                ),
                "fsync_chmod_chown_inode_device_rename_or_delete_used": False,
                "databricks_managed_storage_io_may_have_been_performed": True,
                "direct_external_network_endpoint_accessed": False,
                "package_resolution_build_or_install_executed": False,
                "spark_or_databricks_rest_accessed": False,
                "study_or_test_data_accessed": False,
                "calibration_training_or_inference_executed": False,
                "unity_catalog_volume_io_attempted": True,
            },
        }


# COMMAND ----------

def main():
    preflight_result = preflight()
    printable = dict(preflight_result)
    printable.pop("probe_authorized", None)
    if not preflight_result["probe_authorized"]:
        print(json.dumps(printable, indent=2, sort_keys=True))
        return
    print(json.dumps(run_probe(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
