import ast
import base64
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import runpy
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import venv
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    ROOT
    / "databricks"
    / "notebooks"
    / "b08_n1_uc_native_overlay_lock_candidate.py"
)
PARAMETER_ENVIRONMENT_NAMES = (
    "HETERODIFF_REPO_ROOT_OVERRIDE",
    "HETERODIFF_B08_N1_UC_NATIVE_EXECUTION_MODE",
    "HETERODIFF_B08_N1_UC_NATIVE_NETWORK_BUILD_AUTHORIZED",
    "HETERODIFF_B08_N1_UC_NATIVE_ONE_SHOT_ACKNOWLEDGEMENT",
    "HETERODIFF_B08_N1_UC_NATIVE_REVIEW_PACKAGE_AUTHORIZATION",
)


class _Widgets:
    def __init__(self, supplied=None):
        self.values = dict(supplied or {})
        self.defaults = {}

    def text(self, name, default, label):
        self.defaults[name] = default
        self.values.setdefault(name, default)

    def dropdown(self, name, default, choices, label):
        assert default in choices
        self.defaults[name] = default
        self.values.setdefault(name, default)

    def get(self, name):
        return self.values[name]


class _Dbutils:
    def __init__(self, supplied=None):
        self.widgets = _Widgets(supplied)


def _forbidden(label):
    def fail(*args, **kwargs):
        raise AssertionError(label)

    return fail


@pytest.fixture(scope="module")
def module():
    with contextlib.redirect_stdout(io.StringIO()):
        return runpy.run_path(str(NOTEBOOK))


def _error_code(raised):
    return raised.value.code


def _globals(module, function_name):
    # runpy returns a snapshot dictionary; function globals are the live namespace.
    return module[function_name].__globals__


def _intent_binding(module, payload=b"intent\n"):
    return {
        "name": module["ATTEMPT_INTENT_LEAF_NAME"],
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "fresh_readback_count": 2,
    }


def _fake_destination(module, store, payload=b"intent\n"):
    return {
        "absolute_path": module["CANDIDATE_PREFIX"].as_posix(),
        "parent_path": module["CANDIDATE_PARENT"].as_posix(),
        "candidate_id": module["CANDIDATE_ID"],
        "intent": _intent_binding(module, payload),
        "store": store,
    }


class _RecordingStore:
    def __init__(
        self,
        intent,
        write_error=None,
        attempt_state=None,
        mark_terminal_create_before_error=False,
    ):
        self.intent = intent
        self.write_error = write_error
        self.attempt_state = attempt_state
        self.mark_terminal_create_before_error = (
            mark_terminal_create_before_error
        )
        self.events = []

    def verify_binding(self, name, expected_sha256, expected_size):
        self.events.append(("verify", name, expected_sha256, expected_size))
        return dict(self.intent)

    def write_bytes(self, name, payload):
        self.events.append(("write", name, payload))
        if (
            self.mark_terminal_create_before_error
            and self.attempt_state is not None
        ):
            if name.endswith(".construction-receipt.json"):
                self.attempt_state["success_receipt_create_call_begun"] = True
                self.attempt_state["success_receipt_may_exist"] = True
            elif name.endswith(".construction-failure-receipt.json"):
                self.attempt_state["failure_receipt_create_call_begun"] = True
                self.attempt_state["failure_receipt_may_exist"] = True
        if self.write_error is not None:
            raise self.write_error
        return {
            "name": name,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "fresh_readback_count": 2,
        }


def test_fixed_candidate_constants_and_probe_bindings(module):
    assert module["CANDIDATE_PARENT"] == Path(
        "/Volumes/development/team_eds_supplychain/b08_runtime_output"
    )
    assert module["CANDIDATE_ID"] == "b08-n1-overlay-candidate-003"
    assert module["CANDIDATE_PREFIX"] == (
        module["CANDIDATE_PARENT"] / module["CANDIDATE_ID"]
    )
    assert module["DURABLE_OUTPUT_DIRECTORY"] == (
        module["CANDIDATE_PREFIX"].as_posix()
    )
    assert module["PAYLOAD_CHUNK_BYTES"] == 256 * 1024 * 1024
    assert module["PAYLOAD_CHUNK_LIMIT"] == 128
    assert module["PAYLOAD_ARCHIVE_BYTE_LIMIT"] == 32 * 1024**3
    assert module["EXPECTED_PROBE_REVIEW_FILE_SHA256"] == (
        "7612dbe3c4072c0ab2847bb17d99d6a5aa66ccfff80734f0d961baec57229a59"
    )
    assert module["EXPECTED_PROBE_OUTCOME_FILE_SHA256"] == (
        "f96160da93789d4749b3ce005182a0f57a49a5bc4408296d46ca4fd7fc71bcd7"
    )


def test_reserved_namespace_is_fixed_complete_and_unique(module):
    names = module["reserved_candidate_leaf_names"]()
    assert len(names) == 132
    assert len(set(names)) == len(names)
    assert names[0] == "b08-n1-overlay-candidate-003.attempt-intent.json"
    assert names[1] == "b08-n1-overlay-candidate-003.payload-0000.bin"
    assert names[128] == "b08-n1-overlay-candidate-003.payload-0127.bin"
    assert names[-3:] == (
        "b08-n1-overlay-candidate-003.payload-manifest.json",
        "b08-n1-overlay-candidate-003.construction-receipt.json",
        "b08-n1-overlay-candidate-003.construction-failure-receipt.json",
    )
    assert all("/" not in name and "\\" not in name for name in names)


@pytest.mark.parametrize("ordinal", [-1, 128, True, "0", None])
def test_chunk_leaf_name_rejects_noncanonical_ordinals(module, ordinal):
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["candidate_chunk_leaf_name"](ordinal)
    assert _error_code(raised) == "UC_PAYLOAD_CHUNK_ORDINAL_INVALID"


def test_destination_wrong_prefix_short_circuits_without_visibility_io(
    module, monkeypatch
):
    monkeypatch.setitem(
        _globals(module, "validate_destination"),
        "object_kind",
        _forbidden("visibility touched"),
    )
    details, errors = module["validate_destination"]("/Volumes/wrong")
    assert details["path"] == module["CANDIDATE_PREFIX"].as_posix()
    assert errors == ["UC_CANDIDATE_PREFIX_NOT_EXACT"]


def test_destination_requires_every_reserved_leaf_absent(module, monkeypatch):
    collision = module["PAYLOAD_MANIFEST_LEAF_NAME"]

    def classify(path):
        if path == module["CANDIDATE_PARENT"]:
            return "DIRECTORY"
        if path == module["CANDIDATE_PREFIX"]:
            return "ABSENT"
        return "REGULAR_FILE" if path.name == collision else "ABSENT"

    monkeypatch.setitem(
        _globals(module, "validate_destination"), "object_kind", classify
    )
    details, errors = module["validate_destination"](
        module["CANDIDATE_PREFIX"].as_posix()
    )
    assert details["colliding_reserved_leaf_names"] == [collision]
    assert details["all_reserved_leaves_absent"] is False
    assert errors == ["UC_CANDIDATE_RESERVED_NAMESPACE_NOT_EMPTY"]


def test_default_widgets_hold_without_network_or_write(
    monkeypatch, capsys
):
    for name in PARAMETER_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    fake_dbutils = _Dbutils()
    source_before = NOTEBOOK.read_bytes()
    monkeypatch.setattr(socket, "socket", _forbidden("network attempted"))
    monkeypatch.setattr(
        subprocess, "Popen", _forbidden("child process attempted")
    )
    monkeypatch.setattr(tempfile, "mkdtemp", _forbidden("temp write attempted"))
    monkeypatch.setattr(venv.EnvBuilder, "create", _forbidden("venv attempted"))
    original_open = os.open

    def read_only_open(path, flags, *args, **kwargs):
        mutating_flags = (
            os.O_WRONLY
            | os.O_RDWR
            | os.O_CREAT
            | os.O_TRUNC
            | os.O_APPEND
        )
        if os.fspath(path) == os.devnull:
            return original_open(path, flags, *args, **kwargs)
        if flags & mutating_flags:
            raise AssertionError("mutating open attempted")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", read_only_open)
    monkeypatch.setattr(Path, "write_bytes", _forbidden("write attempted"))
    monkeypatch.setattr(Path, "write_text", _forbidden("write attempted"))
    monkeypatch.setattr(Path, "mkdir", _forbidden("mkdir attempted"))
    monkeypatch.setattr(shutil, "copyfile", _forbidden("copy attempted"))
    monkeypatch.setattr(shutil, "rmtree", _forbidden("delete attempted"))

    runpy.run_path(str(NOTEBOOK), init_globals={"dbutils": fake_dbutils})
    result = json.loads(capsys.readouterr().out)

    assert result["construction_authorized"] is False
    assert result["decision"].startswith("HOLD_")
    assert result["safety"]["files_written"] is False
    assert result["safety"]["direct_external_network_or_contact_accessed"] is False
    assert result["source_identity_preflight"]["exact"] is True
    assert "source_git_preflight" not in result
    assert result["safety"][
        "read_only_local_git_child_processes_executed"
    ] is False
    assert fake_dbutils.widgets.defaults == {
        "b08_n1_uc_native_execution_mode": "PREFLIGHT_ONLY",
        "b08_n1_uc_native_network_build_authorized": "false",
        "b08_n1_uc_native_one_shot_acknowledgement": "NOT_AUTHORIZED",
        "b08_n1_uc_native_review_package_authorization": "NOT_AUTHORIZED",
    }
    assert NOTEBOOK.read_bytes() == source_before


def test_public_postconstruction_failure_reports_narrow_child_process_claims():
    source = NOTEBOOK.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(NOTEBOOK))
    handlers = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not isinstance(node.type, ast.Name):
            continue
        if node.type.id != "CandidateConstructionError":
            continue
        constants = {
            child.value
            for child in ast.walk(node)
            if isinstance(child, ast.Constant)
            and isinstance(child.value, str)
        }
        if "TERMINAL_NO_GO_SPENT_ATTEMPT_REVIEW_REQUIRED" in constants:
            handlers.append((node, constants))
    assert len(handlers) == 1
    handler, constants = handlers[0]
    literal_pairs = {
        (key.value, value.value)
        for mapping in ast.walk(handler)
        if isinstance(mapping, ast.Dict)
        for key, value in zip(mapping.keys, mapping.values)
        if isinstance(key, ast.Constant)
        and isinstance(key.value, str)
        and isinstance(value, ast.Constant)
    }
    assert (
        "child_process_external_file_access_audited",
        False,
    ) in literal_pairs
    assert (
        "child_process_side_effects_outside_staging_proven_absent",
        False,
    ) in literal_pairs
    assert {
        "THIRD_PARTY_CHILD_PROCESS_UNRELATED_FILE_ACCESS_ABSENT",
        "THIRD_PARTY_CHILD_PROCESS_SIDE_EFFECTS_OUTSIDE_STAGING_ABSENT",
        "THIRD_PARTY_CHILD_PROCESS_NETWORK_ENDPOINT_CONFINEMENT",
    }.issubset(constants)
    assert "direct_external_network_or_contact_accessed" not in constants
    assert "network_or_contact_accessed" not in constants


def _install_ready_preflight_fakes(module, monkeypatch):
    globals_ = _globals(module, "preflight")
    repo_root = Path("/reviewed/repository")
    profile = {"target": {}, "f153_environment": {}}
    profile_validation = {
        "valid": True,
        "file_sha256": "1" * 64,
        "semantic_sha256": "2" * 64,
        "errors": [],
    }
    review = {
        "relative_path": module["V2_REVIEW_RELATIVE_PATH"].as_posix(),
        "sha256": module["EXPECTED_V2_REVIEW_FILE_SHA256"],
        "size_bytes": 10,
        "mode_octal": "0644",
    }
    probe_review = {
        "relative_path": module["PROBE_REVIEW_RELATIVE_PATH"].as_posix(),
        "sha256": module["EXPECTED_PROBE_REVIEW_FILE_SHA256"],
        "size_bytes": 11,
        "mode_octal": "0644",
    }
    probe_outcome = {
        "relative_path": module["PROBE_OUTCOME_RELATIVE_PATH"].as_posix(),
        "sha256": module["EXPECTED_PROBE_OUTCOME_FILE_SHA256"],
        "size_bytes": 12,
        "mode_octal": "0644",
    }
    builder = {
        "relative_path": module["BUILDER_NOTEBOOK_RELATIVE_PATH"].as_posix(),
        "sha256": "b" * 64,
        "size_bytes": 101,
        "canonical_mode_octal": "0644",
        "runtime_mode_used_for_identity": False,
        "terminal_lf_policy": "EXACT_BYTES",
    }
    launcher = {
        "relative_path": module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"].as_posix(),
        "sha256": "c" * 64,
        "size_bytes": 102,
        "canonical_mode_octal": "0644",
        "runtime_mode_used_for_identity": False,
        "terminal_lf_policy": module["LAUNCHER_TERMINAL_LF_POLICY"],
    }
    source_manifest = {
        "record_sha256": "d" * 64,
        "files": [
            {
                "relative_path": "pyproject.toml",
                "sha256": "e" * 64,
                "size_bytes": 1,
                "mode_octal": "0644",
            }
        ],
    }
    source_identity = {
        "schema_version": module["SOURCE_IDENTITY_SCHEMA"],
        "record_sha256": "f" * 64,
        "source_date_epoch": module["REVIEWED_SOURCE_DATE_EPOCH"],
        "selected_source_bytes_match_reviewed_snapshot": True,
        "live_git_checkout_identity_verified": False,
    }
    by_label = {
        "V2_INDEPENDENT_REVIEW": review,
        "UC_VOLUME_PROBE_INDEPENDENT_REVIEW": probe_review,
        "UC_VOLUME_PROBE_001_OUTCOME": probe_outcome,
        "BUILDER_NOTEBOOK": builder,
        "HASH_FIRST_LAUNCHER_NOTEBOOK": launcher,
    }

    monkeypatch.setitem(globals_, "locate_repo_root", lambda: repo_root)
    monkeypatch.setitem(
        globals_,
        "validate_profile",
        lambda path, raw=None: (profile, profile_validation),
    )
    monkeypatch.setitem(
        globals_,
        "read_physical_source_bytes",
        lambda path, root: (
            module["PROFILE_RELATIVE_PATH"],
            b"{}\n",
            0o644,
        ),
    )
    monkeypatch.setitem(
        globals_,
        "regular_file_binding",
        lambda root, path, label: dict(by_label[label]),
    )
    monkeypatch.setitem(
        globals_, "project_source_manifest", lambda root: source_manifest
    )
    monkeypatch.setitem(
        globals_,
        "canonical_source_binding",
        lambda root, path, label, **kwargs: dict(by_label[label]),
    )
    monkeypatch.setitem(
        globals_,
        "reviewed_source_snapshot_identity",
        lambda *args, **kwargs: dict(source_identity),
    )
    monkeypatch.setitem(
        globals_, "object_kind", lambda path: "ABSENT"
    )
    monkeypatch.setitem(
        globals_,
        "validate_destination",
        lambda value: ({"path": value, "all_reserved_leaves_absent": True}, []),
    )
    monkeypatch.setitem(
        globals_,
        "observe_runtime",
        lambda value: {"exact": True, "mismatches": {}},
    )
    monkeypatch.setitem(
        globals_,
        "observe_environment",
        lambda value: {"exact": True, "mismatches": {}},
    )
    review_package = module["candidate_review_package"](
        source_manifest,
        builder,
        launcher,
        source_identity,
        profile_validation,
        review,
        probe_review,
        probe_outcome,
    )
    launch_evidence = {
        "schema_version": module["HASH_FIRST_LAUNCH_SCHEMA"],
        "builder_relative_path": builder["relative_path"],
        "operator_expected_builder_sha256": builder["sha256"],
        "executed_payload_sha256": builder["sha256"],
        "executed_payload_size_bytes": builder["size_bytes"],
        "launcher_relative_path": launcher["relative_path"],
        "launcher_source_identity_kind": module[
            "LAUNCHER_SOURCE_IDENTITY_KIND"
        ],
        "launcher_source_sha256": launcher["sha256"],
        "launcher_source_size_bytes": launcher["size_bytes"],
        "launcher_terminal_lf_policy": module[
            "LAUNCHER_TERMINAL_LF_POLICY"
        ],
        "same_in_memory_payload_compiled_and_executed": True,
    }
    ready = {
        "EXECUTION_MODE": module["CONSTRUCT_MODE"],
        "_NETWORK_AUTHORIZATION_TEXT": "true",
        "NETWORK_AND_BUILD_AUTHORIZED": True,
        "ONE_SHOT_ACKNOWLEDGEMENT": module["ACKNOWLEDGEMENT_TEXT"],
        "REVIEW_PACKAGE_AUTHORIZATION": (
            module["REVIEW_AUTHORIZATION_PREFIX"]
            + review_package["record_sha256"]
        ),
        "_HASH_FIRST_LAUNCH_EVIDENCE": launch_evidence,
    }
    for key, value in ready.items():
        monkeypatch.setitem(globals_, key, value)
    return globals_, ready, review_package, launch_evidence, builder, launcher


@pytest.mark.parametrize(
    ("gate", "held_value", "required_fragment"),
    (
        ("EXECUTION_MODE", "PREFLIGHT_ONLY", "EXECUTION_MODE="),
        (
            "NETWORK_AND_BUILD_AUTHORIZED",
            False,
            "NETWORK_AND_BUILD_AUTHORIZED=True",
        ),
        (
            "ONE_SHOT_ACKNOWLEDGEMENT",
            "NOT_AUTHORIZED",
            "ONE_SHOT_ACKNOWLEDGEMENT=",
        ),
        (
            "REVIEW_PACKAGE_AUTHORIZATION",
            "NOT_AUTHORIZED",
            "REVIEW_PACKAGE_AUTHORIZATION=",
        ),
    ),
)
def test_preflight_requires_exact_conjunction_of_all_four_operator_gates(
    module, monkeypatch, gate, held_value, required_fragment
):
    globals_, ready, _, _, _, _ = _install_ready_preflight_fakes(
        module, monkeypatch
    )
    authorized = module["preflight"]()
    assert authorized["construction_authorized"] is True
    assert authorized["errors"] == []

    monkeypatch.setitem(globals_, gate, held_value)
    held = module["preflight"]()
    assert held["construction_authorized"] is False
    assert any(
        required_fragment in item for item in held["required_inputs"]
    )


def test_preflight_requires_exact_review_package_authorization_and_hash_launch(
    module, monkeypatch
):
    globals_, ready, package, evidence, builder, launcher = (
        _install_ready_preflight_fakes(module, monkeypatch)
    )
    assert module["parse_review_package_authorization"](
        module["REVIEW_AUTHORIZATION_PREFIX"] + package["record_sha256"]
    ) == package["record_sha256"]

    monkeypatch.setitem(
        globals_,
        "REVIEW_PACKAGE_AUTHORIZATION",
        module["REVIEW_AUTHORIZATION_PREFIX"] + "f" * 64,
    )
    mismatch = module["preflight"]()
    assert mismatch["construction_authorized"] is False
    assert "REVIEW_PACKAGE_AUTHORIZATION_SHA256_MISMATCH" in mismatch["errors"]

    monkeypatch.setitem(
        globals_, "REVIEW_PACKAGE_AUTHORIZATION", ready["REVIEW_PACKAGE_AUTHORIZATION"]
    )
    monkeypatch.setitem(globals_, "_HASH_FIRST_LAUNCH_EVIDENCE", None)
    absent = module["preflight"]()
    assert absent["construction_authorized"] is False
    assert (
        "RUN_THROUGH_HASH_FIRST_LAUNCHER_WITH_REVIEWED_BUILDER_SHA256"
        in absent["required_inputs"]
    )

    tampered = dict(evidence)
    tampered["executed_payload_size_bytes"] += 1
    monkeypatch.setitem(globals_, "_HASH_FIRST_LAUNCH_EVIDENCE", tampered)
    invalid = module["preflight"]()
    assert invalid["construction_authorized"] is False
    assert "HASH_FIRST_LAUNCH_EVIDENCE_BINDING_MISMATCH" in invalid["errors"]

    missing_policy = dict(evidence)
    del missing_policy["launcher_terminal_lf_policy"]
    validated, errors = module["validate_hash_first_launch_evidence"](
        missing_policy, builder, launcher
    )
    assert validated is None
    assert errors == ["HASH_FIRST_LAUNCH_EVIDENCE_SHAPE_INVALID"]

    wrong_policy = dict(evidence)
    wrong_policy["launcher_terminal_lf_policy"] = "EXACT_BYTES"
    validated, errors = module["validate_hash_first_launch_evidence"](
        wrong_policy, builder, launcher
    )
    assert validated is None
    assert errors == ["HASH_FIRST_LAUNCH_EVIDENCE_BINDING_MISMATCH"]

    validated, errors = module["validate_hash_first_launch_evidence"](
        evidence, builder, launcher
    )
    assert errors == []
    assert validated == evidence


def test_uc_store_source_excludes_posix_custody_and_mutation_primitives():
    source = NOTEBOOK.read_text(encoding="utf-8")
    seam = source.split("class UcVolumeAppendOnlyStore:", 1)[1].split(
        "def verify_durable_intent_custody", 1
    )[0]
    for forbidden in (
        "fsync(",
        "fchmod(",
        "chmod(",
        "chown(",
        "rename(",
        "replace(",
        "unlink(",
        "rmtree(",
        ".st_dev",
        ".st_ino",
        ".st_mtime",
    ):
        assert forbidden not in seam
    assert "os.O_EXCL" in seam
    assert "os.O_NOFOLLOW" in seam
    assert "for ordinal in (1, 2)" in seam


def test_uc_store_exclusive_create_and_two_readbacks(module, tmp_path):
    state = module["initial_attempt_state"]()
    name = "candidate.payload"
    payload = b"bounded payload"
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name}, state)
    binding = store.write_bytes(name, payload)

    assert (tmp_path / name).read_bytes() == payload
    assert binding == {
        "name": name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "fresh_readback_count": 2,
    }
    assert state["attempt_namespace_spent"] is True
    assert state["managed_uc_exclusive_create_calls_begun"] == 1
    assert state["managed_uc_confirmed_leaf_count"] == 1
    assert state["managed_uc_confirmed_bytes_written"] == len(payload)


def test_uc_store_collision_preserves_original_bytes(module, tmp_path):
    state = module["initial_attempt_state"]()
    name = "candidate.payload"
    original = b"original"
    store = module["UcVolumeAppendOnlyStore"](
        tmp_path, {name, "unused.reserved"}, state
    )
    store.write_bytes(name, original)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        store.write_bytes(name, b"replacement")

    assert _error_code(raised) == "UC_EXCLUSIVE_CREATE_COLLISION"
    assert (tmp_path / name).read_bytes() == original
    assert state["managed_uc_exclusive_create_calls_begun"] == 2
    assert state["managed_uc_confirmed_leaf_count"] == 1


def test_uc_store_retains_every_confirmed_binding_across_later_collision(
    module, tmp_path
):
    state = module["initial_attempt_state"]()
    names = {"first.control", "second.control"}
    store = module["UcVolumeAppendOnlyStore"](tmp_path, names, state)
    first = store.write_bytes("first.control", b"first")
    second = store.write_bytes("second.control", b"second")
    confirmed_before_failure = list(state["managed_uc_confirmed_bindings"])

    with pytest.raises(module["CandidateConstructionError"]):
        store.write_bytes("first.control", b"replacement")

    assert confirmed_before_failure == [first, second]
    assert state["managed_uc_confirmed_bindings"] == [first, second]
    assert state["managed_uc_last_confirmed_binding"] == second
    assert state["managed_uc_confirmed_leaf_count"] == 2
    assert state["managed_uc_confirmed_bytes_written"] == 11


def test_uc_store_partial_writes_complete_exact_payload(
    module, tmp_path, monkeypatch
):
    name = "candidate.payload"
    payload = b"0123456789abcdef"
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name})
    original_write = os.write
    calls = {"count": 0}

    def partial_write(descriptor, remaining):
        calls["count"] += 1
        return original_write(descriptor, remaining[:3])

    monkeypatch.setattr(os, "write", partial_write)
    binding = store.write_bytes(name, payload)
    assert calls["count"] > 1
    assert binding["sha256"] == hashlib.sha256(payload).hexdigest()
    assert (tmp_path / name).read_bytes() == payload


def test_uc_store_zero_write_is_spent_ambiguous_and_unconfirmed(
    module, tmp_path, monkeypatch
):
    state = module["initial_attempt_state"]()
    name = "candidate.payload"
    payload = b"payload"
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name}, state)
    monkeypatch.setattr(os, "write", lambda descriptor, remaining: 0)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        store.write_bytes(name, payload)

    assert _error_code(raised) == "UC_EXCLUSIVE_WRITE_FAILED_AFTER_CREATE"
    assert raised.value.telemetry == {
        "attempt_namespace_spent": True,
        "managed_uc_last_leaf_may_exist": name,
        "managed_uc_last_leaf_expected_sha256": hashlib.sha256(payload).hexdigest(),
        "managed_uc_last_leaf_expected_size_bytes": len(payload),
    }
    assert (tmp_path / name).exists()
    assert state["attempt_namespace_spent"] is True
    assert state["managed_uc_confirmed_leaf_count"] == 0


def test_uc_store_verify_binding_uses_two_fresh_reads(module, tmp_path):
    name = "candidate.payload"
    payload = b"payload"
    (tmp_path / name).write_bytes(payload)
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name})
    original_read = store.read_binding
    calls = []

    def recording_read(*args, **kwargs):
        calls.append((args, kwargs))
        return original_read(*args, **kwargs)

    store.read_binding = recording_read
    binding = store.verify_binding(
        name, hashlib.sha256(payload).hexdigest(), len(payload)
    )
    assert len(calls) == 2
    assert binding["fresh_readback_count"] == 2


def test_uc_store_tamper_is_rejected(module, tmp_path):
    name = "candidate.payload"
    payload = b"original"
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name})
    binding = store.write_bytes(name, payload)
    (tmp_path / name).write_bytes(b"tampered")

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        store.verify_binding(name, binding["sha256"], binding["size_bytes"])
    assert _error_code(raised) == "UC_REPEATABLE_READBACK_BINDING_MISMATCH"


def test_uc_store_symlink_collision_never_touches_target(module, tmp_path):
    name = "candidate.payload"
    target = tmp_path / "outside"
    target.write_bytes(b"preserve")
    (tmp_path / name).symlink_to(target)
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name})

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        store.write_bytes(name, b"replacement")
    assert _error_code(raised) == "UC_EXCLUSIVE_CREATE_COLLISION"
    assert target.read_bytes() == b"preserve"


def test_uc_store_rejects_unreserved_and_malformed_names(module, tmp_path):
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {"allowed"})
    for name in ("other", "../allowed", "a/b", "a\\b", "", 1):
        with pytest.raises(module["CandidateConstructionError"]) as raised:
            store.write_bytes(name, b"x")
        assert _error_code(raised) == "UC_RESERVED_LEAF_NAME_INVALID"
    assert list(tmp_path.iterdir()) == []


def test_uc_store_rejects_control_object_over_bound_before_create(
    module, tmp_path, monkeypatch
):
    name = "candidate.control.json"
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name})
    globals_ = module["UcVolumeAppendOnlyStore"]._write_chunks.__globals__
    monkeypatch.setitem(globals_, "CONTROL_OBJECT_BYTE_LIMIT", 3)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        store.write_bytes(name, b"1234")
    assert _error_code(raised) == "UC_CONTROL_OBJECT_TOO_LARGE"
    assert not (tmp_path / name).exists()


def test_uc_store_call_limit_is_fail_closed_before_parent_open(
    module, tmp_path
):
    name = "candidate.control.json"
    state = module["initial_attempt_state"]()
    state["managed_uc_exclusive_create_calls_begun"] = len(
        module["reserved_candidate_leaf_names"]()
    )
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name}, state)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        store.write_bytes(name, b"payload")
    assert _error_code(raised) == "UC_EXCLUSIVE_CREATE_CALL_LIMIT_EXCEEDED"
    assert not (tmp_path / name).exists()


def test_uc_store_file_region_binds_exact_slice(module, tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"prefix-PAYLOAD-suffix")
    name = "candidate.payload"
    expected = b"PAYLOAD"
    store = module["UcVolumeAppendOnlyStore"](tmp_path, {name})
    binding = store.write_file_region(
        name,
        source,
        7,
        len(expected),
        hashlib.sha256(expected).hexdigest(),
    )
    assert (tmp_path / name).read_bytes() == expected
    assert binding["size_bytes"] == len(expected)


def test_start_attempt_commits_intent_as_first_managed_object(
    module, tmp_path, monkeypatch
):
    candidate_prefix = tmp_path / module["CANDIDATE_ID"]
    globals_ = _globals(module, "start_durable_attempt")
    monkeypatch.setitem(globals_, "CANDIDATE_PARENT", tmp_path)
    monkeypatch.setitem(globals_, "CANDIDATE_PREFIX", candidate_prefix)
    state = module["initial_attempt_state"]()
    payload = b'{"state":"spent-before-network"}\n'
    destination = module["start_durable_attempt"](
        candidate_prefix, payload, state
    )
    assert destination["intent"] == {
        "name": module["ATTEMPT_INTENT_LEAF_NAME"],
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "fresh_readback_count": 2,
    }
    assert state["managed_uc_exclusive_create_calls_begun"] == 1
    assert state["managed_uc_confirmed_leaf_count"] == 1
    assert state["durable_intent_committed"] is True
    assert (tmp_path / module["ATTEMPT_INTENT_LEAF_NAME"]).read_bytes() == payload


def _write_overlay_entrypoint(overlay, venv_python, name="demo"):
    script = overlay / "bin" / name
    script.parent.mkdir(parents=True, exist_ok=True)
    original = b"#!" + os.fsencode(str(venv_python)) + b"\nprint('ok')\n"
    script.write_bytes(original)
    record = (
        overlay
        / "lib"
        / "python3.12"
        / "site-packages"
        / f"{name}-1.0.dist-info"
        / "RECORD"
    )
    record.parent.mkdir(parents=True, exist_ok=True)
    relative_script = "../../../bin/" + name
    record.write_text(
        ",".join(
            (
                relative_script,
                "sha256=old-binding",
                str(len(original)),
            )
        )
        + "\n"
        + f"{name}-1.0.dist-info/RECORD,,\n",
        encoding="utf-8",
    )
    return script, record


def _write_complete_overlay(overlay, creation_umask, payload_mode):
    site = overlay / "lib" / "python3.12" / "site-packages"
    data_path = site / "demo" / "__init__.py"
    dist_info = site / "demo-1.0.dist-info"
    metadata_path = dist_info / "METADATA"
    record_path = dist_info / "RECORD"
    data = b"VALUE = 1\n"
    metadata = b"Name: demo\nVersion: 1.0\n"
    prior_umask = os.umask(creation_umask)
    try:
        data_path.parent.mkdir(parents=True)
        dist_info.mkdir()
        data_path.write_bytes(data)
        metadata_path.write_bytes(metadata)
        record_rows = [
            "demo/__init__.py,"
            + _wheel_record_hash(data)
            + f",{len(data)}",
            "demo-1.0.dist-info/METADATA,"
            + _wheel_record_hash(metadata)
            + f",{len(metadata)}",
            "demo-1.0.dist-info/RECORD,,",
        ]
        record_payload = ("\n".join(record_rows) + "\n").encode("utf-8")
        record_path.write_bytes(record_payload)
    finally:
        os.umask(prior_umask)
    os.chmod(data_path, payload_mode)
    return {
        data_path.relative_to(overlay).as_posix(): data,
        metadata_path.relative_to(overlay).as_posix(): metadata,
        record_path.relative_to(overlay).as_posix(): record_payload,
    }


def _expected_overlay_payload_manifest(module, payloads, executable_path=None):
    rows = []
    for relative, payload in payloads.items():
        rows.append(
            {
                "relative_path": relative,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "mode_octal": (
                    "0755" if relative == executable_path else "0644"
                ),
            }
        )
    rows.sort(key=lambda item: item["relative_path"])
    return hashlib.sha256(module["canonical_json_bytes"](rows)).hexdigest()


def test_overlay_payload_manifest_canonicalizes_raw_modes_and_umasks(
    module, tmp_path
):
    specifications = (
        ("nonexec-a", 0o077, 0o600, False),
        ("nonexec-b", 0o002, 0o664, False),
        ("exec-a", 0o077, 0o700, True),
        ("exec-b", 0o002, 0o775, True),
    )
    outcomes = {}
    raw_metadata_modes = {}
    for label, creation_umask, payload_mode, executable in specifications:
        overlay = tmp_path / label
        payloads = _write_complete_overlay(
            overlay, creation_umask, payload_mode
        )
        data_relative = "lib/python3.12/site-packages/demo/__init__.py"
        outcomes[label] = module["verify_installed_overlay"](
            overlay, [{"normalized_name": "demo", "version": "1.0"}]
        )
        raw_metadata_modes[label] = (
            overlay
            / "lib/python3.12/site-packages/demo-1.0.dist-info/METADATA"
        ).stat().st_mode & 0o777
        assert outcomes[label]["payload_manifest_sha256"] == (
            _expected_overlay_payload_manifest(
                module,
                payloads,
                data_relative if executable else None,
            )
        )

    assert raw_metadata_modes["nonexec-a"] != raw_metadata_modes["nonexec-b"]
    assert outcomes["nonexec-a"] == outcomes["nonexec-b"]
    assert outcomes["exec-a"] == outcomes["exec-b"]
    assert outcomes["nonexec-a"]["payload_manifest_sha256"] != (
        outcomes["exec-a"]["payload_manifest_sha256"]
    )
    assert outcomes["nonexec-a"]["ownership_manifest_sha256"] == (
        outcomes["exec-a"]["ownership_manifest_sha256"]
    )


@pytest.mark.parametrize(
    ("limit_name", "limit", "error_code"),
    (
        (
            "OVERLAY_TREE_ENTRY_LIMIT",
            1,
            "OVERLAY_VERIFICATION_TREE_ENTRY_LIMIT_EXCEEDED",
        ),
        (
            "OVERLAY_TREE_TOTAL_BYTE_LIMIT",
            1,
            "OVERLAY_VERIFICATION_TREE_TOTAL_BYTE_LIMIT_EXCEEDED",
        ),
        (
            "OVERLAY_DISTRIBUTION_LIMIT",
            0,
            "OVERLAY_DISTRIBUTION_LIMIT_EXCEEDED",
        ),
        (
            "OVERLAY_RECORD_ROW_LIMIT",
            2,
            "OVERLAY_RECORD_ROW_LIMIT_EXCEEDED",
        ),
        (
            "OVERLAY_SINGLE_FILE_BYTE_LIMIT",
            1,
            "OVERLAY_RECORD_PAYLOAD_SIZE_OR_TYPE_INVALID",
        ),
    ),
)
def test_overlay_verification_enforces_tree_distribution_record_and_file_bounds(
    module, monkeypatch, tmp_path, limit_name, limit, error_code
):
    overlay = tmp_path / "overlay"
    _write_complete_overlay(overlay, 0o022, 0o644)
    monkeypatch.setitem(
        _globals(module, "verify_installed_overlay"), limit_name, limit
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_installed_overlay"](
            overlay, [{"normalized_name": "demo", "version": "1.0"}]
        )

    assert _error_code(raised) == error_code


@pytest.mark.parametrize(
    ("control_limit", "error_code"),
    (
        (1, "OVERLAY_METADATA_FILE_SIZE_OR_TYPE_INVALID"),
        (30, "OVERLAY_RECORD_FILE_SIZE_OR_TYPE_INVALID"),
    ),
)
def test_overlay_verification_bounds_metadata_and_record_control_files(
    module, monkeypatch, tmp_path, control_limit, error_code
):
    overlay = tmp_path / "overlay"
    _write_complete_overlay(overlay, 0o022, 0o644)
    monkeypatch.setitem(
        _globals(module, "verify_installed_overlay"),
        "OVERLAY_CONTROL_FILE_BYTE_LIMIT",
        control_limit,
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_installed_overlay"](
            overlay, [{"normalized_name": "demo", "version": "1.0"}]
        )

    assert _error_code(raised) == error_code


@pytest.mark.parametrize("missing_field", ("hash", "size"))
def test_overlay_record_requires_hash_and_size_as_an_exact_pair(
    module, tmp_path, missing_field
):
    overlay = tmp_path / "overlay"
    _write_complete_overlay(overlay, 0o022, 0o644)
    record = next(overlay.rglob("*.dist-info/RECORD"))
    with record.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    rows[0][1 if missing_field == "hash" else 2] = ""
    with record.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_installed_overlay"](
            overlay, [{"normalized_name": "demo", "version": "1.0"}]
        )

    assert _error_code(raised) == "OVERLAY_RECORD_HASH_SIZE_PAIR_INCOMPLETE"


def test_overlay_record_rejects_non_urlsafe_base64_digest(module, tmp_path):
    overlay = tmp_path / "overlay"
    _write_complete_overlay(overlay, 0o022, 0o644)
    record = next(overlay.rglob("*.dist-info/RECORD"))
    with record.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    rows[0][1] = "sha256=***not-base64url***"
    with record.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_installed_overlay"](
            overlay, [{"normalized_name": "demo", "version": "1.0"}]
        )

    assert _error_code(raised) == "OVERLAY_RECORD_HASH_ENCODING_INVALID"


def test_overlay_verification_binds_reopened_payload_to_tree_scan_size(
    module, monkeypatch, tmp_path
):
    overlay = tmp_path / "overlay"
    _write_complete_overlay(overlay, 0o022, 0o644)
    payload = overlay / "lib/python3.12/site-packages/demo/__init__.py"
    globals_ = _globals(module, "verify_installed_overlay")
    original_tree = globals_["bounded_physical_tree"]

    def scan_then_grow(*args, **kwargs):
        result = original_tree(*args, **kwargs)
        payload.write_bytes(payload.read_bytes() + b"GROWTH")
        return result

    monkeypatch.setitem(globals_, "bounded_physical_tree", scan_then_grow)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_installed_overlay"](
            overlay, [{"normalized_name": "demo", "version": "1.0"}]
        )

    assert _error_code(raised) == "OVERLAY_FILE_SIZE_CHANGED_AFTER_TREE_SCAN"
    assert raised.value.detail == (
        "lib/python3.12/site-packages/demo/__init__.py"
    )


def test_overlay_entrypoint_normalization_rewrites_shebang_and_record(
    module, tmp_path
):
    overlay = tmp_path / "candidate" / "overlay"
    venv_python = tmp_path / "random-build-root" / "bin" / "python"
    script, record = _write_overlay_entrypoint(overlay, venv_python)
    result = module["normalize_overlay_entrypoint_shebangs"](
        overlay, venv_python
    )

    expected = b"#!/usr/bin/env python3\nprint('ok')\n"
    assert script.read_bytes() == expected
    with record.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == [
        "../../../bin/demo",
        module["record_sha256_field"](expected),
        str(len(expected)),
    ]
    assert result == {
        "normalized_script_count": 1,
        "normalized_scripts": [
            {
                "relative_path": "bin/demo",
                "sha256": hashlib.sha256(expected).hexdigest(),
                "size_bytes": len(expected),
            }
        ],
        "record_file_count_rewritten": 1,
        "stable_shebang": "/usr/bin/env python3",
        "volatile_interpreter_paths_persisted": False,
    }


def test_oversized_overlay_entrypoint_is_rejected_by_bounded_reader(
    module, monkeypatch, tmp_path
):
    overlay = tmp_path / "candidate" / "overlay"
    script = overlay / "bin" / "oversized"
    script.parent.mkdir(parents=True)
    (overlay / module["OVERLAY_SITE_PACKAGES_RELATIVE_PATH"]).mkdir(
        parents=True
    )
    with script.open("wb") as handle:
        handle.truncate(module["OVERLAY_ENTRYPOINT_BYTE_LIMIT"] + 1)
    monkeypatch.setattr(
        Path,
        "read_bytes",
        _forbidden("unbounded Path.read_bytes used for entrypoint"),
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["normalize_overlay_entrypoint_shebangs"](
            overlay, tmp_path / "venv" / "bin" / "python"
        )

    assert _error_code(raised) == (
        "OVERLAY_ENTRYPOINT_SCRIPT_SIZE_OR_TYPE_INVALID"
    )


def test_overlay_entrypoint_requires_exactly_one_record_owner(module, tmp_path):
    overlay = tmp_path / "candidate" / "overlay"
    venv_python = tmp_path / "random-build-root" / "bin" / "python"
    _, record = _write_overlay_entrypoint(overlay, venv_python)
    duplicate = record.parent.parent / "other-1.0.dist-info" / "RECORD"
    duplicate.parent.mkdir()
    duplicate.write_bytes(record.read_bytes())

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["normalize_overlay_entrypoint_shebangs"](
            overlay, venv_python
        )
    assert _error_code(raised) == (
        "OVERLAY_ENTRYPOINT_RECORD_OWNERSHIP_NOT_EXACT"
    )


def test_overlay_entrypoint_ignores_nested_vendored_dist_info_owner(
    module, tmp_path
):
    overlay = tmp_path / "candidate" / "overlay"
    venv_python = tmp_path / "random-build-root" / "bin" / "python"
    script, record = _write_overlay_entrypoint(overlay, venv_python)
    nested_record = (
        record.parent.parent
        / "vendor"
        / "vendored-1.0.dist-info"
        / "RECORD"
    )
    nested_record.parent.mkdir(parents=True)
    nested_payload = record.read_bytes()
    nested_record.write_bytes(nested_payload)

    result = module["normalize_overlay_entrypoint_shebangs"](
        overlay, venv_python
    )

    assert result["normalized_script_count"] == 1
    assert result["record_file_count_rewritten"] == 1
    assert script.read_bytes().startswith(b"#!/usr/bin/env python3\n")
    assert nested_record.read_bytes() == nested_payload


def test_overlay_entrypoint_record_parent_traversal_may_not_escape_overlay(
    module, tmp_path
):
    overlay = tmp_path / "candidate" / "overlay"
    venv_python = tmp_path / "random-build-root" / "bin" / "python"
    _, record = _write_overlay_entrypoint(overlay, venv_python)
    rows = list(csv.reader(io.StringIO(record.read_text(encoding="utf-8"))))
    rows[0][0] = "../../../../outside-overlay"
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    record.write_text(output.getvalue(), encoding="utf-8")

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["normalize_overlay_entrypoint_shebangs"](
            overlay, venv_python
        )

    assert _error_code(raised) == (
        "OVERLAY_RECORD_PATH_ESCAPES_DURING_ENTRYPOINT_NORMALIZATION"
    )


def test_portability_scanner_detects_marker_split_across_read_chunks(
    module, tmp_path, monkeypatch
):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    marker = "/volatile/random/staging-root"
    (candidate / "payload").write_bytes(b"abc" + marker.encode("utf-8") + b"z")
    globals_ = _globals(module, "verify_candidate_has_no_volatile_path_bytes")
    monkeypatch.setitem(globals_, "UC_READ_CHUNK_BYTES", 5)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_candidate_has_no_volatile_path_bytes"](
            candidate, (("STAGING_ROOT", marker),)
        )
    assert _error_code(raised) == "CANDIDATE_CONTAINS_VOLATILE_ABSOLUTE_PATH"
    assert raised.value.detail == "payload:STAGING_ROOT"


def test_portability_scanner_returns_complete_safe_projection(module, tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "a").write_bytes(b"safe")
    (candidate / "b").write_bytes(b"also-safe")
    result = module["verify_candidate_has_no_volatile_path_bytes"](
        candidate,
        (
            ("STAGING_ROOT", "/volatile/staging"),
            ("HOST_PYTHON", "/volatile/python"),
        ),
    )
    assert result == {
        "checked_file_count": 2,
        "checked_payload_bytes": 13,
        "marker_roles": ["HOST_PYTHON", "STAGING_ROOT"],
        "volatile_absolute_path_bytes_found": False,
    }


def _pip_identity_for_root(root):
    site = root / "lib" / "python3.12" / "site-packages"
    return {
        "pip_install_prefix": str(root),
        "pip_distribution_root": str(site),
        "pip_module_file": str(site / "pip" / "__init__.py"),
        "pip_record_file": str(site / "pip-25.0.1.dist-info" / "RECORD"),
        "python_executable": str(root / "bin" / "python"),
        "pip_version": "25.0.1",
        "pip_module_file_sha256": "1" * 64,
        "pip_module_file_size_bytes": 100,
        "pip_record_file_sha256": "2" * 64,
        "pip_record_file_size_bytes": 200,
        "pip_payload_closure_exact": True,
        "pip_payload_file_count": 10,
        "pip_payload_hashed_record_count": 9,
        "pip_payload_unhashed_record_count": 1,
        "pip_payload_unrecorded_bytecode_count": 0,
        "pip_payload_manifest_sha256": "3" * 64,
    }


def test_portable_pip_identity_is_equal_across_independent_roots(
    module, tmp_path
):
    first_root = tmp_path / "random-a" / "venv"
    second_root = tmp_path / "unrelated-b" / "venv"
    first = module["portable_pip_identity_evidence"](
        _pip_identity_for_root(first_root), "ISOLATED_BUILD_VENV"
    )
    second = module["portable_pip_identity_evidence"](
        _pip_identity_for_root(second_root), "ISOLATED_BUILD_VENV"
    )
    assert first == second
    assert first["absolute_runtime_paths_persisted"] is False
    assert first["path_projection"] == {
        "pip_distribution_root_relative_to_install_prefix": (
            "lib/python3.12/site-packages"
        ),
        "pip_module_file_relative_to_install_prefix": (
            "lib/python3.12/site-packages/pip/__init__.py"
        ),
        "pip_record_file_relative_to_install_prefix": (
            "lib/python3.12/site-packages/pip-25.0.1.dist-info/RECORD"
        ),
    }
    assert first["python_executable_relationship"] == (
        "RESOLVED_TARGET_WITHIN_INSTALL_PREFIX"
    )
    assert first["content_derived_payload_closure_persisted"] is True
    assert first["omitted_absolute_path_fields"] == [
        "pip_install_prefix",
        "pip_distribution_root",
        "pip_module_file",
        "pip_record_file",
        "python_executable",
    ]
    for key in (
        "pip_payload_file_count",
        "pip_payload_hashed_record_count",
        "pip_payload_manifest_sha256",
        "pip_payload_unhashed_record_count",
        "pip_payload_unrecorded_bytecode_count",
        "pip_record_file_sha256",
        "pip_record_file_size_bytes",
    ):
        assert first[key] == _pip_identity_for_root(first_root)[key]
    encoded = module["canonical_json_bytes"](first)
    assert os.fsencode(str(first_root)) not in encoded
    assert os.fsencode(str(second_root)) not in encoded


def test_command_journal_is_semantic_and_excludes_tool_output(
    module, tmp_path, monkeypatch
):
    first = tmp_path / "random-a"
    second = tmp_path / "unrelated-b"
    primary = "https://pypi.org/simple"
    torch = "https://download.pytorch.org/whl/cpu"
    command_1 = module["sanitized_command"](
        [str(first / "bin" / "tool"), primary, torch],
        primary,
        torch,
        first,
    )
    command_2 = module["sanitized_command"](
        [str(second / "bin" / "tool"), primary, torch],
        primary,
        torch,
        second,
    )
    assert command_1 == command_2 == [
        "<COMMAND_CWD>/bin/tool",
        "<PRIMARY_INDEX_URL>",
        "<PYTORCH_CPU_INDEX_URL>",
    ]
    outputs = iter((b"first nondeterministic output", b"different output"))

    def execute(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=next(outputs), stderr=b"noise")

    monkeypatch.setitem(
        _globals(module, "run_tool"), "run_subprocess_bounded", execute
    )
    journals = []
    returned = []
    for cwd in (first, second):
        cwd.mkdir()
        journal = []
        returned.append(
            module["run_tool"](
                journal,
                "semantic-step",
                [str(cwd / "bin" / "tool"), primary, torch],
                cwd,
                {},
                primary,
                torch,
            )
        )
        journals.append(journal)
    assert returned[0] != returned[1]
    assert journals[0] == journals[1] == [
        {
            "step": "semantic-step",
            "argv": [
                "<COMMAND_CWD>/bin/tool",
                "<PRIMARY_INDEX_URL>",
                "<PYTORCH_CPU_INDEX_URL>",
            ],
            "returncode": 0,
            "stdout_and_stderr_persisted": False,
            "output_excluded_as_nondeterministic_tool_telemetry": True,
        }
    ]
    assert "first nondeterministic output" not in json.dumps(journals)
    assert "different output" not in json.dumps(journals)


def test_failure_stream_evidence_is_bounded_hashed_and_sanitized(
    module, monkeypatch, tmp_path
):
    cwd = tmp_path / "volatile-runtime-root"
    cwd.mkdir()
    primary = "https://pypi.org/simple"
    torch = "https://download.pytorch.org/whl/cpu"
    raw = (
        b"discarded-prefix-" * 40
        + os.fsencode(str(cwd))
        + b"\n"
        + primary.encode("ascii")
        + b"\n"
        + torch.encode("ascii")
        + b"\nhttps://alice:secret@example.invalid/simple"
    )
    globals_ = _globals(module, "bounded_failure_stream_evidence")
    monkeypatch.setitem(
        globals_, "TOOL_FAILURE_DIAGNOSTIC_TAIL_BYTE_LIMIT", 256
    )

    evidence = module["bounded_failure_stream_evidence"](
        raw,
        len(raw) + 17,
        False,
        cwd,
        primary,
        torch,
    )

    assert evidence["captured_byte_count"] == len(raw)
    assert evidence["captured_sha256"] == hashlib.sha256(raw).hexdigest()
    assert evidence["observed_byte_count_before_termination"] == len(raw) + 17
    assert evidence["capture_complete_through_process_termination"] is False
    assert evidence["sanitized_tail_byte_limit"] == 256
    tail = evidence["sanitized_tail_utf8"]
    assert len(tail.encode("utf-8")) <= 256
    assert "<COMMAND_CWD>" in tail
    assert "<PRIMARY_INDEX_URL>" in tail
    assert "<PYTORCH_CPU_INDEX_URL>" in tail
    assert "<REDACTED_CREDENTIALS>" in tail
    for secret in (str(cwd), primary, torch, "alice", "secret"):
        assert secret not in tail
    assert evidence["runtime_paths_and_exact_index_urls_sanitized"] is True


def test_run_tool_failure_persists_only_bounded_sanitized_diagnostics(
    module, monkeypatch, tmp_path
):
    cwd = tmp_path / "volatile-runtime-root"
    cwd.mkdir()
    primary = "https://pypi.org/simple"
    torch = "https://download.pytorch.org/whl/cpu"
    stdout = (str(cwd) + " " + primary).encode("utf-8")
    stderr = b"https://user:password@example.invalid/simple"
    state = module["initial_attempt_state"]()
    intent = _intent_binding(module)
    state.update(
        {
            "durable_intent_committed": True,
            "durable_intent_expected_sha256": intent["sha256"],
            "durable_intent_expected_size_bytes": intent["size_bytes"],
        }
    )
    globals_ = _globals(module, "run_tool")
    monkeypatch.setitem(
        globals_, "verify_durable_intent_custody", lambda *args: intent
    )
    monkeypatch.setitem(
        globals_,
        "run_subprocess_bounded",
        lambda *args: subprocess.CompletedProcess(
            args[0], 23, stdout=stdout, stderr=stderr
        ),
    )
    journal = []

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["run_tool"](
            journal,
            "hostile-failure-step",
            [str(cwd / "bin" / "tool"), primary, torch],
            cwd,
            {},
            primary,
            torch,
            state,
            (),
            {"intent": intent},
        )

    assert _error_code(raised) == "TOOL_STEP_FAILED"
    assert raised.value.detail == "hostile-failure-step:returncode=23"
    assert raised.value.telemetry == module["immutable_json_snapshot"](state)
    assert len(journal) == 1
    entry = journal[0]
    assert entry["stdout_and_stderr_persisted"] == (
        "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY"
    )
    assert entry["output_excluded_as_nondeterministic_tool_telemetry"] is False
    encoded = module["canonical_json_bytes"](entry)
    for secret in (str(cwd), primary, torch, "user", "password"):
        assert secret.encode("utf-8") not in encoded
    assert b"<COMMAND_CWD>" in encoded
    assert b"<PRIMARY_INDEX_URL>" in encoded
    assert b"<REDACTED_CREDENTIALS>" in encoded
    assert entry["failure_diagnostics"]["stdout"]["captured_sha256"] == (
        hashlib.sha256(stdout).hexdigest()
    )
    assert entry["failure_diagnostics"]["stderr"]["captured_sha256"] == (
        hashlib.sha256(stderr).hexdigest()
    )


def test_run_tool_preserves_bounded_sanitized_candidate_error_detail(
    module, monkeypatch, tmp_path
):
    cwd = tmp_path / "volatile-runtime-root"
    cwd.mkdir()
    primary = "https://pypi.org/simple"
    torch = "https://download.pytorch.org/whl/cpu"
    secret_url = "https://detail-user:detail-password@example.invalid/simple"
    raw_detail = " ".join(
        (
            "discarded-prefix" * 500,
            "stderr:OSError",
            str(cwd),
            primary,
            torch,
            secret_url,
        )
    )
    subprocess_error = module["CandidateConstructionError"](
        "TOOL_OUTPUT_READER_FAILED",
        raw_detail,
        stdout=b"bounded stdout",
        stderr=b"bounded stderr",
        output_capture_complete=False,
    )
    subprocess_error.observed_stream_bytes = {"stdout": 19, "stderr": 23}

    def fail(*args):
        raise subprocess_error

    monkeypatch.setitem(
        _globals(module, "run_tool"), "run_subprocess_bounded", fail
    )
    journal = []
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["run_tool"](
            journal,
            "reader-failure",
            [sys.executable, "-c", "pass"],
            cwd,
            dict(os.environ),
            primary,
            torch,
        )

    assert _error_code(raised) == "TOOL_OUTPUT_READER_FAILED"
    assert len(journal) == 1
    detail = journal[0]["execution_error_detail"]
    assert len(detail.encode("utf-8")) <= module["TOOL_FAILURE_DETAIL_BYTE_LIMIT"]
    assert "stderr:OSError" in detail
    assert "<COMMAND_CWD>" in detail
    assert "<PRIMARY_INDEX_URL>" in detail
    assert "<PYTORCH_CPU_INDEX_URL>" in detail
    assert "<REDACTED_CREDENTIALS>" in detail
    for secret in (
        str(cwd),
        primary,
        torch,
        "detail-user",
        "detail-password",
    ):
        assert secret not in detail
        assert secret not in raised.value.detail
    assert raised.value.detail == (
        "reader-failure:TOOL_OUTPUT_READER_FAILED:" + detail
    )


def test_bounded_subprocess_captures_normal_stdout_and_stderr(module, tmp_path):
    completed = module["run_subprocess_bounded"](
        [
            sys.executable,
            "-c",
            (
                "import os;"
                "os.write(1,b'bounded stdout');"
                "os.write(2,b'bounded stderr')"
            ),
        ],
        tmp_path,
        dict(os.environ),
    )
    assert completed.returncode == 0
    assert completed.stdout == b"bounded stdout"
    assert completed.stderr == b"bounded stderr"


@pytest.mark.parametrize(("descriptor", "label"), ((1, "stdout"), (2, "stderr")))
def test_bounded_subprocess_output_overflow_terminates_and_reaps_child(
    module, monkeypatch, tmp_path, descriptor, label
):
    globals_ = _globals(module, "run_subprocess_bounded")
    monkeypatch.setitem(globals_, "TOOL_OUTPUT_STREAM_BYTE_LIMIT", 64)
    monkeypatch.setitem(globals_, "TOOL_REAP_SECONDS", 2)
    real_popen = subprocess.Popen
    processes = []

    def recording_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", recording_popen)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["run_subprocess_bounded"](
            [
                sys.executable,
                "-c",
                (
                    "import os,time;"
                    f"os.write({descriptor},b'x'*4096);"
                    "time.sleep(30)"
                ),
            ],
            tmp_path,
            dict(os.environ),
        )
    assert _error_code(raised) == "TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED"
    assert raised.value.detail == label
    assert len(processes) == 1
    assert processes[0].poll() is not None


def test_bounded_subprocess_timeout_terminates_and_reaps_child(
    module, monkeypatch, tmp_path
):
    globals_ = _globals(module, "run_subprocess_bounded")
    monkeypatch.setitem(globals_, "TOOL_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setitem(globals_, "TOOL_REAP_SECONDS", 2)
    real_popen = subprocess.Popen
    processes = []

    def recording_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", recording_popen)
    with pytest.raises(subprocess.TimeoutExpired):
        module["run_subprocess_bounded"](
            [sys.executable, "-c", "import time;time.sleep(30)"],
            tmp_path,
            dict(os.environ),
        )
    assert len(processes) == 1
    assert processes[0].poll() is not None


def test_bounded_subprocess_reader_start_failure_terminates_and_reaps_child(
    module, monkeypatch, tmp_path
):
    globals_ = _globals(module, "run_subprocess_bounded")
    monkeypatch.setitem(globals_, "TOOL_REAP_SECONDS", 2)
    real_popen = subprocess.Popen
    real_thread = threading.Thread
    processes = []
    created_threads = 0

    def recording_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        processes.append(process)
        return process

    class StartFailure:
        ident = None

        def __init__(self):
            self.join_calls = 0

        def start(self):
            raise RuntimeError("injected reader start failure")

        def join(self, timeout=None):
            self.join_calls += 1

        @staticmethod
        def is_alive():
            return False

    def thread_factory(*args, **kwargs):
        nonlocal created_threads
        created_threads += 1
        if created_threads == 2:
            return StartFailure()
        return real_thread(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", recording_popen)
    monkeypatch.setattr(threading, "Thread", thread_factory)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["run_subprocess_bounded"](
            [sys.executable, "-c", "import time;time.sleep(30)"],
            tmp_path,
            dict(os.environ),
        )
    assert _error_code(raised) == "TOOL_SUBPROCESS_SUPERVISOR_FAILED"
    assert raised.value.detail == "RuntimeError"
    assert raised.value.stdout == b""
    assert raised.value.stderr == b""
    assert raised.value.output_capture_complete is False
    assert raised.value.observed_stream_bytes == {"stdout": 0, "stderr": 0}
    assert created_threads == 2
    assert len(processes) == 1
    assert processes[0].poll() is not None


def test_run_tool_reader_start_failure_is_reaped_and_durably_diagnosable(
    module, monkeypatch, tmp_path
):
    globals_ = _globals(module, "run_subprocess_bounded")
    monkeypatch.setitem(globals_, "TOOL_REAP_SECONDS", 2)
    real_popen = subprocess.Popen
    real_thread = threading.Thread
    processes = []
    failed_thread = None
    created_threads = 0

    def recording_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        processes.append(process)
        return process

    class StartFailure:
        ident = None

        def __init__(self):
            self.join_calls = 0

        def start(self):
            raise RuntimeError("injected reader start failure")

        def join(self, timeout=None):
            self.join_calls += 1

        @staticmethod
        def is_alive():
            return False

    def thread_factory(*args, **kwargs):
        nonlocal created_threads, failed_thread
        created_threads += 1
        if created_threads == 2:
            failed_thread = StartFailure()
            return failed_thread
        return real_thread(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", recording_popen)
    monkeypatch.setattr(threading, "Thread", thread_factory)
    journal = []
    primary = "https://pypi.org/simple"
    torch = "https://download.pytorch.org/whl/cpu"
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["run_tool"](
            journal,
            "reader-start-failure",
            [sys.executable, "-c", "import time;time.sleep(30)"],
            tmp_path,
            dict(os.environ),
            primary,
            torch,
        )

    assert _error_code(raised) == "TOOL_SUBPROCESS_SUPERVISOR_FAILED"
    assert len(processes) == 1
    assert processes[0].poll() is not None
    assert created_threads == 2
    assert failed_thread is not None
    assert failed_thread.join_calls >= 1
    assert len(journal) == 1
    entry = journal[0]
    assert entry["execution_error"] == "TOOL_SUBPROCESS_SUPERVISOR_FAILED"
    assert entry["execution_error_detail"] == "RuntimeError"
    assert entry["returncode"] is None
    assert entry["stdout_and_stderr_persisted"] == (
        "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY"
    )
    assert entry["failure_diagnostics"]["stdout"] == (
        module["bounded_failure_stream_evidence"](
            b"", 0, False, tmp_path, primary, torch
        )
    )
    assert entry["failure_diagnostics"]["stderr"] == (
        module["bounded_failure_stream_evidence"](
            b"", 0, False, tmp_path, primary, torch
        )
    )
    assert raised.value.detail == (
        "reader-start-failure:TOOL_SUBPROCESS_SUPERVISOR_FAILED:RuntimeError"
    )


def test_isolated_environment_confines_temp_cache_and_configuration(
    module, tmp_path
):
    staging = tmp_path / "staging"
    venv_root = staging / "build-venv"
    tool_temp = staging / "tool-tmp"
    venv_root.mkdir(parents=True)
    tool_temp.mkdir()
    deterministic = {"PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1"}

    environment = module["isolated_environment"](
        venv_root, 123456789, deterministic, tool_temp
    )
    assert environment["PYTHONHASHSEED"] == "0"
    assert environment["OMP_NUM_THREADS"] == "1"
    assert environment["PATH"] == f"{venv_root / 'bin'}:/usr/bin:/bin"
    assert environment["TMPDIR"] == str(tool_temp.resolve())
    assert environment["TMP"] == str(tool_temp.resolve())
    assert environment["TEMP"] == str(tool_temp.resolve())
    assert environment["PIP_CONFIG_FILE"] == os.devnull
    assert environment["PIP_DISABLE_PIP_VERSION_CHECK"] == "1"
    assert environment["PIP_NO_CACHE_DIR"] == "1"
    assert environment["PIP_NO_INPUT"] == "1"
    assert environment["SOURCE_DATE_EPOCH"] == "123456789"

    outside = tmp_path / "outside-temp"
    outside.mkdir()
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["isolated_environment"](
            venv_root, 123456789, deterministic, outside
        )
    assert _error_code(raised) == "TOOL_TEMP_ROOT_ESCAPES_STAGING"


def test_every_pip_cli_explicitly_disables_cache():
    tree = ast.parse(NOTEBOOK.read_text(encoding="utf-8"))
    pip_commands = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "run_tool":
            continue
        if len(node.args) < 3:
            continue
        strings = [
            child.value
            for child in ast.walk(node.args[2])
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        ]
        if "-m" in strings and "pip" in strings:
            pip_commands.append(strings)
    assert len(pip_commands) == 7
    assert all("--no-cache-dir" in command for command in pip_commands)
    assert all("--isolated" in command for command in pip_commands)


def test_candidate_root_is_created_before_all_candidate_children():
    source = NOTEBOOK.read_text(encoding="utf-8")
    construct = source.split("def construct_candidate(", 1)[1]
    parent = construct.index("candidate_root.mkdir(mode=0o750)")
    child_creates = [
        construct.index("tool_wheelhouse.mkdir(mode=0o750)"),
        construct.index("runtime_wheelhouse.mkdir(mode=0o750)"),
        construct.index("overlay_root.mkdir(mode=0o750)"),
    ]
    assert all(parent < child for child in child_creates)


def test_construct_rebinds_source_identity_review_package_before_attempt_intent():
    tree = ast.parse(NOTEBOOK.read_text(encoding="utf-8"))
    construct = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "construct_candidate"
    )
    review_calls = [
        node
        for node in ast.walk(construct)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "candidate_review_package"
    ]
    assert len(review_calls) == 1
    review_call = review_calls[0]
    assert len(review_call.args) == 8
    assert isinstance(review_call.args[3], ast.Name)
    assert review_call.args[3].id == "preintent_source_identity"

    construct_source = ast.get_source_segment(
        NOTEBOOK.read_text(encoding="utf-8"), construct
    )
    assert construct_source is not None
    source_rebind = construct_source.index(
        "preintent_source_identity = reviewed_source_snapshot_identity("
    )
    review_rebind = construct_source.index("candidate_review_package(")
    attempt_intent = construct_source.index("build_attempt_intent(")
    durable_start = construct_source.index("start_durable_attempt(")
    assert source_rebind < review_rebind < attempt_intent < durable_start


def test_real_ensurepip_observation_is_portable_and_matches_runtime(module):
    plan = module["pip_bootstrap_plan"]()
    observation = plan["ensurepip_observation"]
    spec = importlib.util.find_spec("ensurepip")
    assert observation["available"] is (spec is not None)
    assert observation["absolute_origin_persisted"] is False
    assert plan["required_pip_version"] == "25.0.1"
    projection = observation["origin_projection"]
    if projection is not None:
        assert projection["kind"] in {
            "BUILT_IN",
            "FROZEN",
            "HOST_PREFIX_RELATIVE",
            "OUTSIDE_HOST_PREFIX",
        }
        relative = projection["relative_to_host_prefix"]
        if projection["kind"] == "HOST_PREFIX_RELATIVE":
            assert relative
            assert not PurePosixPath(relative).is_absolute()
        else:
            assert relative is None
    encoded = module["canonical_json_bytes"](plan)
    if spec is not None and isinstance(spec.origin, str):
        assert os.fsencode(str(Path(spec.origin).resolve())) not in encoded


def _local_python_candidates():
    candidates = [Path(sys.executable)]
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if directory:
            candidates.extend(
                Path(directory) / name for name in ("python3", "python")
            )
    framework_root = Path("/Library/Frameworks/Python.framework/Versions")
    if framework_root.is_dir():
        candidates.extend(framework_root.glob("*/bin/python3"))
    unique = []
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved in seen or not os.access(resolved, os.X_OK):
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


@pytest.fixture(scope="module")
def pip_probe_runtime(module):
    failures = []
    for executable in _local_python_candidates():
        try:
            completed = subprocess.run(
                [
                    str(executable),
                    "-I",
                    "-B",
                    "-c",
                    module["PIP_IDENTITY_PROBE"],
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                close_fds=True,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            failures.append(f"{executable}:{type(error).__name__}")
            continue
        if completed.returncode == 0:
            return executable, completed
        failures.append(
            f"{executable}:returncode={completed.returncode}:"
            + completed.stderr.decode("utf-8", errors="replace")[-120:]
        )
    pytest.skip("no local pip RECORD runtime accepted the bounded probe: " + "; ".join(failures))


def test_embedded_pip_identity_probe_declares_all_streaming_bounds(module):
    probe = module["PIP_IDENTITY_PROBE"]
    for declaration in (
        "CONTROL_FILE_BYTE_LIMIT = 16 * 1024 * 1024",
        "RECORD_ROW_LIMIT = 250_000",
        "PHYSICAL_DIRECTORY_LIMIT = 250_000",
        "PAYLOAD_FILE_LIMIT = 250_000",
        "PAYLOAD_SINGLE_FILE_BYTE_LIMIT = 4 * 1024 * 1024 * 1024",
        "PAYLOAD_TOTAL_BYTE_LIMIT = 16 * 1024 * 1024 * 1024",
        "READ_CHUNK_BYTES = 1024 * 1024",
    ):
        assert declaration in probe
    for rejection in (
        "PIP_RECORD_ROW_LIMIT_EXCEEDED",
        "PIP_PHYSICAL_DIRECTORY_LIMIT_EXCEEDED",
        "PIP_PHYSICAL_FILE_LIMIT_EXCEEDED",
        "PIP_PAYLOAD_FILE_LIMIT_EXCEEDED",
        "PIP_PAYLOAD_TOTAL_BYTE_LIMIT_EXCEEDED",
    ):
        assert rejection in probe
    assert "def read_regular_file_bounded(" in probe
    assert "os.read(descriptor, READ_CHUNK_BYTES)" in probe
    assert ".read_bytes(" not in probe


def _run_fake_pip_identity_probe(module, tmp_path, script_record_path):
    prefix = tmp_path / "isolated-prefix"
    distribution_root = prefix / "lib" / "python3.12" / "site-packages"
    module_path = distribution_root / "pip" / "__init__.py"
    dist_info = distribution_root / "pip-1.0.dist-info"
    metadata_path = dist_info / "METADATA"
    record_path = dist_info / "RECORD"
    script_path = prefix / "bin" / "pip"
    module_path.parent.mkdir(parents=True)
    dist_info.mkdir()
    script_path.parent.mkdir(parents=True)
    module_payload = b"__version__ = '1.0'\n"
    metadata_payload = b"Name: pip\nVersion: 1.0\n"
    script_payload = b"#!/usr/bin/env python3\n"
    module_path.write_bytes(module_payload)
    metadata_path.write_bytes(metadata_payload)
    script_path.write_bytes(script_payload)

    def digest_field(payload):
        encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest())
        return "sha256=" + encoded.rstrip(b"=").decode("ascii")

    rows = [
        (
            "pip/__init__.py",
            digest_field(module_payload),
            str(len(module_payload)),
        ),
        (
            "pip-1.0.dist-info/METADATA",
            digest_field(metadata_payload),
            str(len(metadata_payload)),
        ),
        ("pip-1.0.dist-info/RECORD", "", ""),
        (
            script_record_path,
            digest_field(script_payload),
            str(len(script_payload)),
        ),
    ]
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    record_path.write_text(output.getvalue(), encoding="utf-8")

    probe = module["PIP_IDENTITY_PROBE"]
    spec_line = 'spec = importlib.util.find_spec("pip")'
    prefix_line = "install_prefix = Path(sys.prefix).resolve()"
    assert probe.count(spec_line) == 1
    assert probe.count(prefix_line) == 1
    probe = probe.replace(
        spec_line,
        "spec = type('FakeSpec', (), {'origin': "
        + repr(str(module_path))
        + "})()",
        1,
    ).replace(
        prefix_line,
        "install_prefix = Path(" + repr(str(prefix)) + ").resolve()",
        1,
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", probe],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        close_fds=True,
        timeout=60,
    )
    return completed, prefix


def test_embedded_pip_identity_probe_allows_bounded_parent_script_path(
    module, tmp_path
):
    completed, prefix = _run_fake_pip_identity_probe(
        module, tmp_path, "../../../bin/pip"
    )

    assert completed.returncode == 0, completed.stderr.decode(
        "utf-8", errors="replace"
    )
    identity = json.loads(completed.stdout)
    assert identity["pip_install_prefix"] == str(prefix.resolve())
    assert identity["pip_payload_file_count"] == 4
    assert identity["pip_payload_hashed_record_count"] == 3
    assert identity["pip_payload_unhashed_record_count"] == 1


def test_embedded_pip_identity_probe_rejects_parent_path_escape(
    module, tmp_path
):
    completed, _ = _run_fake_pip_identity_probe(
        module, tmp_path, "../../../../outside-prefix"
    )

    assert completed.returncode != 0
    assert completed.stdout == b""
    assert "PIP_RECORD_PATH_ESCAPES_INSTALL_PREFIX" in completed.stderr.decode(
        "utf-8", errors="replace"
    )


def test_embedded_pip_identity_probe_executes_against_a_local_interpreter(
    pip_probe_runtime
):
    executable, completed = pip_probe_runtime
    identity = json.loads(completed.stdout.decode("utf-8"))
    assert completed.stderr == b""
    assert Path(identity["python_executable"]).resolve() == executable.resolve()
    assert identity["pip_payload_closure_exact"] is True
    assert identity["pip_payload_file_count"] > 0
    assert identity["pip_payload_file_count"] == sum(
        identity[key]
        for key in (
            "pip_payload_hashed_record_count",
            "pip_payload_unhashed_record_count",
            "pip_payload_unrecorded_bytecode_count",
        )
    )
    for key in (
        "pip_module_file_sha256",
        "pip_payload_manifest_sha256",
        "pip_record_file_sha256",
    ):
        assert len(identity[key]) == 64
        int(identity[key], 16)


@pytest.mark.parametrize(
    ("declaration", "replacement", "expected_error"),
    (
        (
            "RECORD_ROW_LIMIT = 250_000",
            "RECORD_ROW_LIMIT = 0",
            "PIP_RECORD_ROW_LIMIT_EXCEEDED",
        ),
        (
            "PAYLOAD_FILE_LIMIT = 250_000",
            "PAYLOAD_FILE_LIMIT = 0",
            "PIP_PAYLOAD_FILE_LIMIT_EXCEEDED",
        ),
        (
            "PHYSICAL_DIRECTORY_LIMIT = 250_000",
            "PHYSICAL_DIRECTORY_LIMIT = 0",
            "PIP_PHYSICAL_DIRECTORY_LIMIT_EXCEEDED",
        ),
        (
            "PAYLOAD_TOTAL_BYTE_LIMIT = 16 * 1024 * 1024 * 1024",
            "PAYLOAD_TOTAL_BYTE_LIMIT = 0",
            "PIP_PAYLOAD_TOTAL_BYTE_LIMIT_EXCEEDED",
        ),
    ),
)
def test_embedded_pip_identity_probe_low_bounds_fail_closed(
    module,
    pip_probe_runtime,
    declaration,
    replacement,
    expected_error,
):
    executable, _ = pip_probe_runtime
    probe = module["PIP_IDENTITY_PROBE"]
    assert probe.count(declaration) == 1
    hostile = probe.replace(declaration, replacement, 1)
    completed = subprocess.run(
        [str(executable), "-I", "-B", "-c", hostile],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        close_fds=True,
        timeout=60,
    )
    assert completed.returncode != 0
    assert completed.stdout == b""
    assert expected_error in completed.stderr.decode("utf-8", errors="replace")


def test_portable_pip_identity_retains_content_derived_closure_variability(
    module, tmp_path
):
    first = _pip_identity_for_root(tmp_path / "one")
    second = _pip_identity_for_root(tmp_path / "two")
    second.update(
        {
            "pip_record_file_sha256": "a" * 64,
            "pip_record_file_size_bytes": 999,
            "pip_payload_file_count": 333,
            "pip_payload_hashed_record_count": 111,
            "pip_payload_unhashed_record_count": 222,
            "pip_payload_unrecorded_bytecode_count": 17,
            "pip_payload_manifest_sha256": "b" * 64,
        }
    )
    first_evidence = module["portable_pip_identity_evidence"](
        first, "ISOLATED_BUILD_VENV"
    )
    second_evidence = module["portable_pip_identity_evidence"](
        second, "ISOLATED_BUILD_VENV"
    )
    assert first_evidence != second_evidence
    for key in (
        "pip_record_file_sha256",
        "pip_record_file_size_bytes",
        "pip_payload_file_count",
        "pip_payload_hashed_record_count",
        "pip_payload_unhashed_record_count",
        "pip_payload_unrecorded_bytecode_count",
        "pip_payload_manifest_sha256",
    ):
        assert first_evidence[key] == first[key]
        assert second_evidence[key] == second[key]


def test_portable_host_pip_identity_records_symlink_target_relationship_only(
    module, tmp_path
):
    prefix = tmp_path / "host-prefix"
    (prefix / "bin").mkdir(parents=True)
    real_interpreter = tmp_path / "runtime" / "python"
    real_interpreter.parent.mkdir()
    real_interpreter.write_bytes(b"host interpreter")
    link = prefix / "bin" / "python"
    link.symlink_to(real_interpreter)
    identity = _pip_identity_for_root(prefix)
    identity["python_executable"] = str(link.resolve())

    evidence = module["portable_pip_identity_evidence"](
        identity, "HOST_NOTEBOOK_INTERPRETER"
    )
    assert evidence["python_executable_relationship"] == (
        "RESOLVED_TARGET_OUTSIDE_INSTALL_PREFIX"
    )
    encoded = module["canonical_json_bytes"](evidence)
    assert os.fsencode(str(link)) not in encoded
    assert os.fsencode(str(real_interpreter)) not in encoded


def _lock_record(name="demo", version="1.0", digest=None):
    return {
        "normalized_name": name,
        "version": version,
        "sha256": digest or "a" * 64,
    }


def test_lock_candidate_bytes_emits_sorted_exact_hash_locked_requirements(
    module
):
    payload = module["lock_candidate_bytes"](
        [
            _lock_record("zeta", "2.0", "b" * 64),
            _lock_record("alpha", "1.0", "a" * 64),
        ]
    )

    assert payload.endswith(b"\n")
    assert payload.count(b"alpha==1.0 \\\n") == 1
    assert payload.count(b"zeta==2.0 \\\n") == 1
    assert payload.index(b"alpha==1.0") < payload.index(b"zeta==2.0")
    assert b"    --hash=sha256:" + b"a" * 64 in payload
    assert b"    --hash=sha256:" + b"b" * 64 in payload


@pytest.mark.parametrize(
    "record",
    (
        _lock_record(name="Demo"),
        _lock_record(name="demo_pkg"),
        _lock_record(version="1.0\n--index-url=https://attacker.invalid"),
        _lock_record(version="1.0\\\n--find-links=https://attacker.invalid"),
        _lock_record(digest="A" * 64),
        _lock_record(digest="a" * 63),
        _lock_record(digest="a" * 64 + "\n--trusted-host=attacker.invalid"),
    ),
)
def test_lock_candidate_bytes_rejects_identity_hash_and_newline_injection(
    module, record
):
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["lock_candidate_bytes"]([record])

    assert _error_code(raised) == "LOCK_CANDIDATE_RECORD_IDENTITY_INVALID"


def test_lock_candidate_bytes_rejects_duplicate_distribution(module):
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["lock_candidate_bytes"](
            [_lock_record("demo", "1.0"), _lock_record("demo", "2.0")]
        )

    assert _error_code(raised) == "LOCK_CANDIDATE_DUPLICATE_DISTRIBUTION"
    assert raised.value.detail == "demo"


def _wheel_record_hash(payload):
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest())
    return "sha256=" + encoded.rstrip(b"=").decode("ascii")


def _write_test_wheel(path, data_payload=b"VALUE = 1\n"):
    data_name = "demo/__init__.py"
    metadata_name = "demo-1.0.dist-info/METADATA"
    wheel_name = "demo-1.0.dist-info/WHEEL"
    record_name = "demo-1.0.dist-info/RECORD"
    metadata = b"Name: demo\nVersion: 1.0\n"
    wheel = (
        b"Wheel-Version: 1.0\n"
        b"Generator: hostile-unit-test\n"
        b"Root-Is-Purelib: true\n"
        b"Tag: py3-none-any\n"
    )
    members = {
        data_name: data_payload,
        metadata_name: metadata,
        wheel_name: wheel,
    }
    rows = [
        f"{name},{_wheel_record_hash(payload)},{len(payload)}"
        for name, payload in members.items()
    ]
    rows.append(f"{record_name},,")
    members[record_name] = ("\n".join(rows) + "\n").encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return members


def _write_identity_test_wheel(
    path,
    *,
    distribution="demo",
    version="1.0",
    metadata_parent="demo-1.0.dist-info",
    record_parent="demo-1.0.dist-info",
    wheel_parent="demo-1.0.dist-info",
):
    data_name = "demo/__init__.py"
    metadata_name = f"{metadata_parent}/METADATA"
    record_name = f"{record_parent}/RECORD"
    wheel_name = f"{wheel_parent}/WHEEL"
    members = {
        data_name: b"VALUE = 1\n",
        metadata_name: (
            f"Name: {distribution}\nVersion: {version}\n".encode("utf-8")
        ),
        wheel_name: (
            b"Wheel-Version: 1.0\n"
            b"Generator: hostile-unit-test\n"
            b"Root-Is-Purelib: true\n"
            b"Tag: py3-none-any\n"
        ),
    }
    rows = [
        f"{name},{_wheel_record_hash(payload)},{len(payload)}"
        for name, payload in members.items()
    ]
    rows.append(f"{record_name},,")
    members[record_name] = ("\n".join(rows) + "\n").encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return members


@pytest.mark.parametrize(
    ("distribution", "version", "error_code"),
    (
        ("demo bad", "1.0", "WHEEL_METADATA_IDENTITY_MISMATCH"),
        ("demo\\bad", "1.0", "WHEEL_METADATA_IDENTITY_MISMATCH"),
        (
            "demo",
            "1.0\\\n --find-links https://attacker.invalid/simple",
            "WHEEL_METADATA_IDENTITY_MISMATCH",
        ),
        ("demo", "1.0 bad", "WHEEL_METADATA_IDENTITY_MISMATCH"),
        (
            "demo\nName: injected",
            "1.0",
            "WHEEL_METADATA_IDENTITY_CARDINALITY_INVALID",
        ),
    ),
)
def test_inspect_wheel_rejects_unsafe_or_injected_metadata_identity(
    module, tmp_path, distribution, version, error_code
):
    path = tmp_path / "demo-1.0-py3-none-any.whl"
    _write_identity_test_wheel(
        path, distribution=distribution, version=version
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["inspect_wheel"](path)

    assert _error_code(raised) == error_code


@pytest.mark.parametrize(
    ("metadata_parent", "record_parent", "wheel_parent"),
    (
        (
            "other-1.0.dist-info",
            "demo-1.0.dist-info",
            "demo-1.0.dist-info",
        ),
        (
            "demo-1.0.dist-info",
            "other-1.0.dist-info",
            "demo-1.0.dist-info",
        ),
        (
            "demo-1.0.dist-info",
            "demo-1.0.dist-info",
            "other-1.0.dist-info",
        ),
    ),
)
def test_inspect_wheel_requires_all_control_members_in_filename_dist_info(
    module, tmp_path, metadata_parent, record_parent, wheel_parent
):
    path = tmp_path / "demo-1.0-py3-none-any.whl"
    _write_identity_test_wheel(
        path,
        metadata_parent=metadata_parent,
        record_parent=record_parent,
        wheel_parent=wheel_parent,
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["inspect_wheel"](path)

    assert _error_code(raised) == "WHEEL_DIST_INFO_IDENTITY_BINDING_MISMATCH"


def _write_central_directory_shape(path, *, entry_count=1, size=1):
    central = b"C"
    eocd = struct.pack(
        "<4s4H2LH",
        b"PK\x05\x06",
        0,
        0,
        entry_count,
        entry_count,
        size,
        0,
        0,
    )
    path.write_bytes(central + eocd)


def _write_zip64_central_directory_shape(path):
    central = b"C"
    zip64_offset = len(central)
    zip64_eocd = struct.pack(
        "<4sQ2H2L4Q",
        b"PK\x06\x06",
        44,
        45,
        45,
        0,
        0,
        1,
        1,
        len(central),
        0,
    )
    locator = struct.pack(
        "<4sLQL", b"PK\x06\x07", 0, zip64_offset, 1
    )
    eocd = struct.pack(
        "<4s4H2LH",
        b"PK\x05\x06",
        0,
        0,
        0xFFFF,
        0xFFFF,
        0xFFFFFFFF,
        0xFFFFFFFF,
        0,
    )
    path.write_bytes(central + zip64_eocd + locator + eocd)


def test_inspect_wheel_preflights_central_directory_before_zipfile(
    module, monkeypatch, tmp_path
):
    path = tmp_path / "demo-1.0-py3-none-any.whl"
    _write_test_wheel(path)
    globals_ = _globals(module, "inspect_wheel")
    original_preflight = globals_["preflight_zip_central_directory"]
    original_zipfile = zipfile.ZipFile
    events = []

    def recording_preflight(*args, **kwargs):
        events.append("central-directory-preflight")
        return original_preflight(*args, **kwargs)

    def recording_zipfile(*args, **kwargs):
        assert events == ["central-directory-preflight"]
        events.append("zipfile-open")
        return original_zipfile(*args, **kwargs)

    monkeypatch.setitem(
        globals_, "preflight_zip_central_directory", recording_preflight
    )
    monkeypatch.setattr(zipfile, "ZipFile", recording_zipfile)
    module["inspect_wheel"](path)
    assert events == ["central-directory-preflight", "zipfile-open"]


@pytest.mark.parametrize("declared_bound", ("entry-count", "central-size"))
def test_inspect_wheel_rejects_declared_central_bounds_before_zipfile(
    module, monkeypatch, tmp_path, declared_bound
):
    path = tmp_path / "hostile.whl"
    globals_ = _globals(module, "inspect_wheel")
    if declared_bound == "entry-count":
        monkeypatch.setitem(globals_, "WHEEL_MEMBER_LIMIT", 1)
        _write_central_directory_shape(path, entry_count=2)
        expected_error = "WHEEL_MEMBER_COUNT_LIMIT_EXCEEDED"
    else:
        assert globals_["WHEEL_CENTRAL_DIRECTORY_BYTE_LIMIT"] == 64 * 1024 * 1024
        _write_central_directory_shape(
            path,
            size=globals_["WHEEL_CENTRAL_DIRECTORY_BYTE_LIMIT"] + 1,
        )
        expected_error = "WHEEL_CENTRAL_DIRECTORY_BOUNDS_INVALID"
    monkeypatch.setattr(
        zipfile,
        "ZipFile",
        _forbidden("ZipFile opened before central-directory rejection"),
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["inspect_wheel"](path)

    assert _error_code(raised) == expected_error


def test_zip_central_directory_preflight_accepts_classic_and_zip64_shapes(
    module, tmp_path
):
    classic = tmp_path / "classic.zip"
    _write_central_directory_shape(classic)
    classic_record = module["preflight_zip_central_directory"](
        classic, classic.stat().st_size
    )
    assert classic_record == {
        "entry_count": 1,
        "size_bytes": 1,
        "offset_bytes": 0,
        "zip64": False,
    }

    zip64 = tmp_path / "zip64.zip"
    _write_zip64_central_directory_shape(zip64)
    zip64_record = module["preflight_zip_central_directory"](
        zip64, zip64.stat().st_size
    )
    assert zip64_record == {
        "entry_count": 1,
        "size_bytes": 1,
        "offset_bytes": 0,
        "zip64": True,
    }


def test_inspect_wheel_stream_hashes_every_member_without_zipfile_read(
    module, monkeypatch, tmp_path
):
    path = tmp_path / "demo-1.0-py3-none-any.whl"
    payload = b"x" * (1024 * 1024 + 17)
    members = _write_test_wheel(path, payload)
    original_member_read = zipfile.ZipExtFile.read
    read_sizes = []

    def recording_member_read(self, size=-1):
        read_sizes.append(size)
        return original_member_read(self, size)

    monkeypatch.setattr(
        zipfile.ZipFile,
        "read",
        _forbidden("whole ZIP member read attempted"),
    )
    monkeypatch.setattr(zipfile.ZipExtFile, "read", recording_member_read)
    record = module["inspect_wheel"](path)
    assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert record["size_bytes"] == path.stat().st_size
    assert record["distribution_name"] == "demo"
    assert record["version"] == "1.0"
    assert record["embedded_payload_file_count"] == len(members)
    assert read_sizes.count(1024 * 1024) > len(members)


def test_inspect_wheel_rehash_detects_growth_during_inspection(
    module, monkeypatch, tmp_path
):
    path = tmp_path / "demo-1.0-py3-none-any.whl"
    _write_test_wheel(path)
    original_zipfile = zipfile.ZipFile

    class AppendingZipFile:
        def __init__(self, *args, **kwargs):
            self.inner = original_zipfile(*args, **kwargs)
            self.mutated = False

        def infolist(self):
            result = self.inner.infolist()
            if not self.mutated:
                self.mutated = True
                with path.open("ab") as handle:
                    handle.write(b"X")
            return result

        def __getattr__(self, name):
            return getattr(self.inner, name)

    monkeypatch.setattr(zipfile, "ZipFile", AppendingZipFile)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["inspect_wheel"](path)

    assert _error_code(raised) == "WHEEL_FILE_CHANGED_DURING_INSPECTION"


def test_wheel_directory_rechecks_each_inspected_artifact_size(
    module, monkeypatch, tmp_path
):
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    path = wheelhouse / "demo-1.0-py3-none-any.whl"
    path.write_bytes(b"initial-wheel-bytes")
    globals_ = _globals(module, "inspect_wheel_directory")

    def changed_size_record(observed_path):
        return {
            "filename": observed_path.name,
            "size_bytes": observed_path.stat().st_size + 1,
            "normalized_name": "demo",
            "version": "1.0",
        }

    monkeypatch.setitem(globals_, "inspect_wheel", changed_size_record)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["inspect_wheel_directory"](wheelhouse)

    assert _error_code(raised) == (
        "WHEEL_DIRECTORY_FILE_SIZE_CHANGED_DURING_INSPECTION"
    )


@pytest.mark.parametrize(
    ("limit_name", "limit", "error_code"),
    (
        ("WHEEL_FILE_BYTE_LIMIT", 1, "WHEEL_FILE_SIZE_LIMIT_EXCEEDED"),
        ("WHEEL_MEMBER_LIMIT", 3, "WHEEL_MEMBER_COUNT_LIMIT_EXCEEDED"),
        ("WHEEL_MEMBER_BYTE_LIMIT", 1, "WHEEL_MEMBER_SIZE_LIMIT_EXCEEDED"),
        (
            "WHEEL_UNCOMPRESSED_BYTE_LIMIT",
            1,
            "WHEEL_UNCOMPRESSED_SIZE_LIMIT_EXCEEDED",
        ),
        (
            "WHEEL_CONTROL_MEMBER_BYTE_LIMIT",
            1,
            "WHEEL_CONTROL_MEMBER_SIZE_LIMIT_EXCEEDED",
        ),
    ),
)
def test_inspect_wheel_enforces_file_member_control_and_aggregate_bounds(
    module, monkeypatch, tmp_path, limit_name, limit, error_code
):
    path = tmp_path / "demo-1.0-py3-none-any.whl"
    _write_test_wheel(path)
    monkeypatch.setitem(_globals(module, "inspect_wheel"), limit_name, limit)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["inspect_wheel"](path)
    assert _error_code(raised) == error_code


def _write_raw_wheel_entries(path, entries):
    file_types = {
        "file": stat.S_IFREG | 0o644,
        "directory": stat.S_IFDIR | 0o755,
        "symlink": stat.S_IFLNK | 0o777,
        "fifo": stat.S_IFIFO | 0o600,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, kind in entries:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = file_types[kind] << 16
            archive.writestr(info, b"target" if kind == "symlink" else b"x")


@pytest.mark.parametrize(
    ("entries", "error_code"),
    (
        (("a//b", "file"), "WHEEL_UNSAFE_ARCHIVE_PATH"),
        (("a/./b", "file"), "WHEEL_UNSAFE_ARCHIVE_PATH"),
        (("a/\x1fb", "file"), "WHEEL_UNSAFE_ARCHIVE_PATH"),
        (("a/\x7fb", "file"), "WHEEL_UNSAFE_ARCHIVE_PATH"),
        (("../escape/", "directory"), "WHEEL_UNSAFE_ARCHIVE_PATH"),
        (
            (("aliased", "file"), ("aliased/", "directory")),
            "WHEEL_UNSAFE_ARCHIVE_PATH",
        ),
        (("link", "symlink"), "WHEEL_NONREGULAR_ARCHIVE_MEMBER"),
        (("pipe", "fifo"), "WHEEL_NONREGULAR_ARCHIVE_MEMBER"),
    ),
)
def test_inspect_wheel_rejects_noncanonical_aliased_and_nonregular_members(
    module, tmp_path, entries, error_code
):
    path = tmp_path / "hostile.whl"
    if entries and isinstance(entries[0], str):
        entries = (entries,)
    _write_raw_wheel_entries(path, entries)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["inspect_wheel"](path)
    assert _error_code(raised) == error_code


def test_canonicalized_candidates_archive_identically_across_random_roots(
    module, tmp_path
):
    candidates = []
    archives = []
    for root_name in ("random-a", "unrelated-b"):
        root = tmp_path / root_name
        candidate = root / "candidate"
        overlay = candidate / "overlay"
        venv_python = root / "build-venv" / "bin" / "python"
        _write_overlay_entrypoint(overlay, venv_python)
        normalization = module["normalize_overlay_entrypoint_shebangs"](
            overlay, venv_python
        )
        evidence = module["portable_pip_identity_evidence"](
            _pip_identity_for_root(root / "build-venv"),
            "ISOLATED_BUILD_VENV",
        )
        journal = module["sanitized_command"](
            [str(root / "build-venv" / "bin" / "python"), "-m", "pip"],
            "https://pypi.org/simple",
            "https://download.pytorch.org/whl/cpu",
            root,
        )
        (candidate / "portable-evidence.json").write_bytes(
            module["canonical_json_bytes"](
                {
                    "entrypoint_normalization": normalization,
                    "pip_identity": evidence,
                    "journal_argv": journal,
                }
            )
            + b"\n"
        )
        module["verify_candidate_has_no_volatile_path_bytes"](
            candidate,
            (("STAGING_ROOT", root), ("VENV_PYTHON", venv_python)),
        )
        archive_path = root / "candidate.zip"
        module["build_deterministic_candidate_archive"](
            candidate, archive_path
        )
        candidates.append(candidate)
        archives.append(archive_path)

    assert archives[0].read_bytes() == archives[1].read_bytes()
    assert (candidates[0] / "portable-evidence.json").read_bytes() == (
        candidates[1] / "portable-evidence.json"
    ).read_bytes()


def _make_archive_source(root):
    root.mkdir()
    (root / "a.txt").write_bytes(b"alpha\n")
    executable = root / "bin" / "run"
    executable.parent.mkdir()
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)


def test_deterministic_archive_is_byte_repeatable_and_metadata_normalized(
    module, tmp_path
):
    source = tmp_path / "source"
    _make_archive_source(source)
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    binding_1 = module["build_deterministic_candidate_archive"](source, first)
    binding_2 = module["build_deterministic_candidate_archive"](source, second)

    assert first.read_bytes() == second.read_bytes()
    assert binding_1 == binding_2
    assert binding_1["format"] == "ZIP_STORED_ZIP64"
    assert binding_1["descriptor_pinned_member_and_hash_verification"] is True
    assert [item["relative_path"] for item in binding_1["members"]] == [
        "a.txt",
        "bin/run",
    ]
    assert [item["mode_octal"] for item in binding_1["members"]] == [
        "0644",
        "0755",
    ]
    with zipfile.ZipFile(first) as archive:
        assert all(
            info.compress_type == zipfile.ZIP_STORED
            for info in archive.infolist()
        )
        assert all(
            info.date_time == (1980, 1, 1, 0, 0, 0)
            for info in archive.infolist()
        )


def test_archive_verification_rejects_path_replacement_while_descriptor_pinned(
    module, tmp_path, monkeypatch
):
    source = tmp_path / "source"
    _make_archive_source(source)
    archive = tmp_path / "candidate.zip"
    replacement = tmp_path / "replacement.zip"
    replacement_payload = b"replacement-path-object"
    real_read = os.read
    replaced = False

    def replace_after_initial_descriptor_hash(descriptor, size):
        nonlocal replaced
        payload = real_read(descriptor, size)
        if not payload and not replaced and archive.exists():
            try:
                same_object = (
                    os.fstat(descriptor).st_ino == archive.stat().st_ino
                )
            except OSError:
                same_object = False
            if same_object:
                replacement.write_bytes(replacement_payload)
                os.replace(replacement, archive)
                replaced = True
        return payload

    monkeypatch.setattr(os, "read", replace_after_initial_descriptor_hash)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["build_deterministic_candidate_archive"](source, archive)

    assert replaced is True
    assert archive.read_bytes() == replacement_payload
    assert _error_code(raised) == (
        "LOCAL_ARCHIVE_CHANGED_DURING_DESCRIPTOR_VERIFICATION"
    )


def test_archive_in_place_mutation_between_bookend_hashes_is_rejected(
    module, tmp_path, monkeypatch
):
    source = tmp_path / "source"
    _make_archive_source(source)
    archive_path = tmp_path / "candidate.zip"
    real_zip_file = zipfile.ZipFile
    mutated = False

    class MutateAfterReadVerification:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __enter__(self):
            return self.wrapped.__enter__()

        def __exit__(self, exc_type, exc_value, traceback):
            nonlocal mutated
            result = self.wrapped.__exit__(exc_type, exc_value, traceback)
            if exc_type is None:
                with archive_path.open("r+b") as handle:
                    first = handle.read(1)
                    handle.seek(0)
                    handle.write(bytes((first[0] ^ 1,)))
                mutated = True
            return result

    def zip_file_with_postverify_mutation(*args, **kwargs):
        wrapped = real_zip_file(*args, **kwargs)
        mode = kwargs.get("mode", args[1] if len(args) > 1 else "r")
        if mode == "r":
            return MutateAfterReadVerification(wrapped)
        return wrapped

    monkeypatch.setattr(zipfile, "ZipFile", zip_file_with_postverify_mutation)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["build_deterministic_candidate_archive"](
            source, archive_path
        )

    assert mutated is True
    assert _error_code(raised) == (
        "LOCAL_ARCHIVE_CHANGED_DURING_DESCRIPTOR_VERIFICATION"
    )


def test_archive_rejects_member_changed_after_preassembly_binding(
    module, tmp_path, monkeypatch
):
    source = tmp_path / "source"
    source.mkdir()
    member = source / "member.bin"
    member.write_bytes(b"A" * 32)
    archive = tmp_path / "candidate.zip"
    globals_ = _globals(module, "build_deterministic_candidate_archive")
    original_enumerator = globals_["staging_archive_members"]

    def enumerate_then_mutate(source_root):
        records = original_enumerator(source_root)
        member.write_bytes(b"B" * 32)
        return records

    monkeypatch.setitem(
        globals_, "staging_archive_members", enumerate_then_mutate
    )
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["build_deterministic_candidate_archive"](source, archive)
    assert _error_code(raised) == "STAGING_ARCHIVE_MEMBER_CHANGED_DURING_WRITE"
    assert raised.value.detail == "member.bin"


@pytest.mark.parametrize(
    "relative",
    [
        PurePosixPath("/absolute"),
        PurePosixPath("../escape"),
        PurePosixPath("."),
        PurePosixPath("safe\\unsafe"),
        PurePosixPath("control\x01name"),
    ],
)
def test_archive_relative_path_rejects_unsafe_members(module, relative):
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["safe_archive_relative_path"](relative)
    assert _error_code(raised) == "ARCHIVE_MEMBER_PATH_UNSAFE"


def test_archive_rejects_symlink_members(module, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "target"
    target.write_bytes(b"outside")
    (source / "link").symlink_to(target)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["staging_archive_members"](source)
    assert _error_code(raised) == "STAGING_ARCHIVE_UNSAFE_FILE"


def test_archive_rejects_hard_link_members(module, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    first = source / "first"
    first.write_bytes(b"same inode")
    os.link(first, source / "second")
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["staging_archive_members"](source)
    assert _error_code(raised) == "STAGING_ARCHIVE_HARD_LINK_NOT_PERMITTED"


def test_archive_member_limit_is_fail_closed(module, tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a").write_bytes(b"a")
    (source / "b").write_bytes(b"b")
    globals_ = _globals(module, "staging_archive_members")
    monkeypatch.setitem(globals_, "ARCHIVE_MEMBER_LIMIT", 1)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["staging_archive_members"](source)
    assert _error_code(raised) == "STAGING_ARCHIVE_MEMBER_LIMIT_EXCEEDED"


def test_archive_chunk_plan_binds_order_offsets_sizes_and_hashes(
    module, tmp_path, monkeypatch
):
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"abcdefgh")
    globals_ = _globals(module, "plan_archive_chunks")
    monkeypatch.setitem(globals_, "PAYLOAD_CHUNK_BYTES", 3)
    monkeypatch.setitem(globals_, "PAYLOAD_CHUNK_LIMIT", 3)
    monkeypatch.setitem(globals_, "PAYLOAD_ARCHIVE_BYTE_LIMIT", 9)
    records = module["plan_archive_chunks"](archive)
    assert [item["ordinal"] for item in records] == [0, 1, 2]
    assert [item["offset_bytes"] for item in records] == [0, 3, 6]
    assert [item["size_bytes"] for item in records] == [3, 3, 2]
    assert [item["sha256"] for item in records] == [
        hashlib.sha256(part).hexdigest()
        for part in (b"abc", b"def", b"gh")
    ]
    assert [item["name"] for item in records] == [
        "b08-n1-overlay-candidate-003.payload-0000.bin",
        "b08-n1-overlay-candidate-003.payload-0001.bin",
        "b08-n1-overlay-candidate-003.payload-0002.bin",
    ]


def test_archive_chunk_limit_is_fail_closed(module, tmp_path, monkeypatch):
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"abcde")
    globals_ = _globals(module, "plan_archive_chunks")
    monkeypatch.setitem(globals_, "PAYLOAD_CHUNK_BYTES", 2)
    monkeypatch.setitem(globals_, "PAYLOAD_CHUNK_LIMIT", 2)
    monkeypatch.setitem(globals_, "PAYLOAD_ARCHIVE_BYTE_LIMIT", 100)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](archive)
    assert _error_code(raised) == "PAYLOAD_CHUNK_LIMIT_EXCEEDED"


def test_archive_binding_change_before_chunk_plan_is_rejected(module, tmp_path):
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"original")
    expected_sha256 = hashlib.sha256(b"original").hexdigest()
    archive.write_bytes(b"tampered")
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](
            archive, expected_sha256, len(b"original")
        )
    assert _error_code(raised) == "PAYLOAD_ARCHIVE_CHANGED_BEFORE_CHUNK_PLAN"


def test_empty_archive_payload_is_rejected(module, tmp_path):
    archive = tmp_path / "empty.bin"
    archive.write_bytes(b"")
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](archive)
    assert _error_code(raised) == "PAYLOAD_ARCHIVE_DESCRIPTOR_OBJECT_INVALID"


def test_archive_chunk_plan_rejects_symlink_without_following(
    module, tmp_path
):
    target = tmp_path / "target.bin"
    target.write_bytes(b"bound archive")
    link = tmp_path / "archive-link.bin"
    link.symlink_to(target)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](link)

    assert _error_code(raised) == "PAYLOAD_ARCHIVE_DESCRIPTOR_ACCESS_FAILED"


def test_archive_chunk_plan_rejects_hard_linked_archive(module, tmp_path):
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"bound archive")
    os.link(archive, tmp_path / "second-name.bin")

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](archive)

    assert _error_code(raised) == "PAYLOAD_ARCHIVE_DESCRIPTOR_OBJECT_INVALID"


def test_archive_chunk_plan_rejects_sparse_oversized_archive(
    module, tmp_path
):
    archive = tmp_path / "oversized.bin"
    with archive.open("wb") as handle:
        handle.truncate(module["PAYLOAD_ARCHIVE_BYTE_LIMIT"] + 1)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](archive)

    assert _error_code(raised) == "PAYLOAD_ARCHIVE_DESCRIPTOR_OBJECT_INVALID"


def test_archive_chunk_plan_uses_only_bounded_descriptor_reads(
    module, tmp_path, monkeypatch
):
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"0123456789abcdef")
    globals_ = _globals(module, "plan_archive_chunks")
    monkeypatch.setitem(globals_, "PAYLOAD_CHUNK_BYTES", 5)
    monkeypatch.setitem(globals_, "UC_READ_CHUNK_BYTES", 3)
    real_read = os.read
    requested_sizes = []

    def recording_read(descriptor, size):
        requested_sizes.append(size)
        return real_read(descriptor, size)

    monkeypatch.setattr(os, "read", recording_read)
    records = module["plan_archive_chunks"](archive)

    assert [record["size_bytes"] for record in records] == [5, 5, 5, 1]
    assert requested_sizes
    assert max(requested_sizes) <= 3


def test_archive_chunk_plan_rejects_path_replacement_after_initial_hash(
    module, tmp_path, monkeypatch
):
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"0123456789abcdef")
    replacement = tmp_path / "replacement.bin"
    replacement_payload = b"replacement-path"
    real_read = os.read
    replaced = False

    def replace_after_initial_hash(descriptor, size):
        nonlocal replaced
        payload = real_read(descriptor, size)
        if not payload and not replaced:
            replacement.write_bytes(replacement_payload)
            os.replace(replacement, archive)
            replaced = True
        return payload

    monkeypatch.setattr(os, "read", replace_after_initial_hash)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](archive)

    assert replaced is True
    assert archive.read_bytes() == replacement_payload
    assert _error_code(raised) == (
        "PAYLOAD_ARCHIVE_LINK_COUNT_CHANGED_DURING_PLAN"
    )


def test_archive_chunk_plan_rejects_in_place_mutation_after_initial_hash(
    module, tmp_path, monkeypatch
):
    archive = tmp_path / "archive.bin"
    archive.write_bytes(b"0123456789abcdef")
    real_read = os.read
    mutated = False

    def mutate_after_initial_hash(descriptor, size):
        nonlocal mutated
        payload = real_read(descriptor, size)
        if not payload and not mutated:
            with archive.open("r+b") as handle:
                first = handle.read(1)
                handle.seek(0)
                handle.write(bytes((first[0] ^ 1,)))
            mutated = True
        return payload

    monkeypatch.setattr(os, "read", mutate_after_initial_hash)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["plan_archive_chunks"](archive)

    assert mutated is True
    assert _error_code(raised) == "PAYLOAD_ARCHIVE_CHANGED_DURING_PLAN"


def test_archive_publication_integrates_chunks_manifest_and_intent_custody(
    module, tmp_path, monkeypatch
):
    source = tmp_path / "work" / "candidate"
    source.parent.mkdir()
    _make_archive_source(source)
    uc_parent = tmp_path / "uc"
    uc_parent.mkdir()
    state = module["initial_attempt_state"]()
    store = module["UcVolumeAppendOnlyStore"](
        uc_parent, module["reserved_candidate_leaf_names"](), state
    )
    intent_payload = b'{"state":"spent"}\n'
    intent = store.write_bytes(
        module["ATTEMPT_INTENT_LEAF_NAME"], intent_payload
    )
    destination = {
        "intent": intent,
        "store": store,
    }
    monkeypatch.setitem(
        _globals(module, "publish_candidate_archive"),
        "verify_archive_evidence_consistency",
        lambda *args: {"projection_sha256": "e" * 64},
    )
    result = module["publish_candidate_archive"](
        source,
        destination,
        intent["sha256"],
        intent["size_bytes"],
        [],
        [],
        {"record_sha256": "a" * 64},
        "manifest.json",
        "b" * 64,
        1,
        {
            "regular_file_count": 2,
            "payload_manifest_sha256": "c" * 64,
        },
    )
    assert result["chunk_count"] == 1
    assert result["success_receipt_included"] is False
    chunk = result["chunks"][0]
    assert (uc_parent / chunk["name"]).read_bytes() == (
        source.parent / "candidate-payload.zip"
    ).read_bytes()
    manifest_payload = (
        uc_parent / module["PAYLOAD_MANIFEST_LEAF_NAME"]
    ).read_bytes()
    manifest = json.loads(manifest_payload)
    projection = dict(manifest)
    record_sha256 = projection.pop("record_sha256")
    assert record_sha256 == hashlib.sha256(
        b"heterodiff/b08/n1/uc-native-payload-manifest/v1\0"
        + module["canonical_json_bytes"](projection)
    ).hexdigest()
    assert manifest["attempt_intent"] == intent
    assert manifest["chunks"][0]["binding"]["fresh_readback_count"] == 2
    assert not (uc_parent / module["SUCCESS_RECEIPT_LEAF_NAME"]).exists()


def test_payload_manifest_is_finalized_before_first_chunk_create(
    module, tmp_path, monkeypatch
):
    source = tmp_path / "work" / "candidate"
    source.parent.mkdir()
    _make_archive_source(source)
    intent = _intent_binding(module)
    events = []

    class Store:
        attempt_state = None

        def verify_binding(self, name, expected_sha256, expected_size):
            events.append(("verify-intent", name))
            return dict(intent)

        def write_file_region(
            self, name, source_path, offset, size, expected_sha256
        ):
            assert "manifest-finalized" in events
            events.append(("chunk-create", name))
            return {
                "name": name,
                "sha256": expected_sha256,
                "size_bytes": size,
                "fresh_readback_count": 2,
            }

        def write_bytes(self, name, payload):
            assert "manifest-finalized" in events
            events.append(("manifest-create", name))
            return {
                "name": name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "fresh_readback_count": 2,
            }

    globals_ = _globals(module, "publish_candidate_archive")
    canonical = globals_["canonical_json_bytes"]

    def observe_manifest_finalization(value):
        if (
            isinstance(value, dict)
            and value.get("schema_version")
            == "heterodiff-b08-n1-uc-native-payload-manifest-v1"
            and value.get("record_sha256") not in (None, "0" * 64)
        ):
            events.append("manifest-finalized")
        return canonical(value)

    monkeypatch.setitem(
        globals_, "canonical_json_bytes", observe_manifest_finalization
    )
    monkeypatch.setitem(
        globals_,
        "verify_archive_evidence_consistency",
        lambda *args: {"projection_sha256": "e" * 64},
    )
    result = module["publish_candidate_archive"](
        source,
        {"intent": intent, "store": Store()},
        intent["sha256"],
        intent["size_bytes"],
        [],
        [],
        {"record_sha256": "a" * 64},
        "manifest.json",
        "b" * 64,
        1,
        {
            "regular_file_count": 2,
            "payload_manifest_sha256": "c" * 64,
        },
    )
    first_chunk_index = next(
        index
        for index, event in enumerate(events)
        if isinstance(event, tuple) and event[0] == "chunk-create"
    )
    assert events.index("manifest-finalized") < first_chunk_index
    assert result["payload_manifest"]["chunks"] == result["chunks"]


def _published_payload_verification_case(module, ordinals=(0,)):
    intent = _intent_binding(module, b"bound intent\n")
    manifest = {
        "name": module["PAYLOAD_MANIFEST_LEAF_NAME"],
        "sha256": "d" * 64,
        "size_bytes": 701,
        "fresh_readback_count": 2,
    }
    chunks = []
    bindings = {
        intent["name"]: intent,
        manifest["name"]: manifest,
    }
    for ordinal in ordinals:
        name = module["candidate_chunk_leaf_name"](ordinal)
        binding = {
            "name": name,
            "sha256": format(ordinal + 1, "064x"),
            "size_bytes": ordinal + 11,
            "fresh_readback_count": 2,
        }
        chunks.append(
            {"ordinal": ordinal, "name": name, "binding": binding}
        )
        bindings[name] = binding

    class Store:
        def __init__(self):
            self.calls = []

        def verify_binding(self, name, expected_sha256, expected_size):
            self.calls.append((name, expected_sha256, expected_size))
            return dict(bindings[name])

    store = Store()
    destination = {"intent": intent, "store": store}
    publish = {
        "payload_manifest_binding": manifest,
        "chunks": chunks,
    }
    return destination, publish, store, bindings


@pytest.mark.parametrize(
    "occupied_name",
    (
        "UNUSED_CHUNK",
        "FAILURE_RECEIPT",
        "SUCCESS_RECEIPT",
        "VIRTUAL_PREFIX",
    ),
)
def test_published_payload_rejects_every_extra_reserved_namespace_object(
    module, monkeypatch, occupied_name
):
    destination, publish, store, _ = _published_payload_verification_case(
        module
    )
    paths = {
        "UNUSED_CHUNK": (
            module["CANDIDATE_PARENT"]
            / module["candidate_chunk_leaf_name"](1)
        ),
        "FAILURE_RECEIPT": (
            module["CANDIDATE_PARENT"]
            / module["FAILURE_RECEIPT_LEAF_NAME"]
        ),
        "SUCCESS_RECEIPT": (
            module["CANDIDATE_PARENT"]
            / module["SUCCESS_RECEIPT_LEAF_NAME"]
        ),
        "VIRTUAL_PREFIX": module["CANDIDATE_PREFIX"],
    }
    occupied_path = paths[occupied_name]
    monkeypatch.setitem(
        _globals(module, "verify_published_payload_before_success"),
        "object_kind",
        lambda path: "REGULAR_FILE" if Path(path) == occupied_path else "ABSENT",
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_published_payload_before_success"](
            destination, publish
        )

    assert _error_code(raised) == "UC_RESERVED_NAMESPACE_NOT_EXACT_BEFORE_SUCCESS"
    detail = json.loads(raised.value.detail)
    if occupied_name == "VIRTUAL_PREFIX":
        assert detail == {
            "nonabsent_reserved_leaves": [],
            "virtual_prefix_kind": "REGULAR_FILE",
        }
    else:
        assert detail == {
            "nonabsent_reserved_leaves": [
                {"kind": "REGULAR_FILE", "name": occupied_path.name}
            ],
            "virtual_prefix_kind": "ABSENT",
        }
    assert store.calls == []


def test_published_payload_rejects_attempt_intent_rebinding(
    module, monkeypatch
):
    destination, publish, store, bindings = (
        _published_payload_verification_case(module)
    )
    original_verify = store.verify_binding

    def rebind_intent(name, expected_sha256, expected_size):
        observed = original_verify(name, expected_sha256, expected_size)
        if name == module["ATTEMPT_INTENT_LEAF_NAME"]:
            observed["sha256"] = "f" * 64
        return observed

    store.verify_binding = rebind_intent
    monkeypatch.setitem(
        _globals(module, "verify_published_payload_before_success"),
        "object_kind",
        lambda path: "ABSENT",
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_published_payload_before_success"](
            destination, publish
        )

    assert _error_code(raised) == "UC_ATTEMPT_INTENT_CHANGED_BEFORE_SUCCESS"
    assert [call[0] for call in store.calls] == [
        module["ATTEMPT_INTENT_LEAF_NAME"]
    ]
    assert bindings[module["ATTEMPT_INTENT_LEAF_NAME"]] == destination["intent"]


def test_published_payload_returns_complete_reserved_namespace_projection(
    module, monkeypatch
):
    destination, publish, store, bindings = (
        _published_payload_verification_case(module, (0, 1))
    )
    monkeypatch.setitem(
        _globals(module, "verify_published_payload_before_success"),
        "object_kind",
        lambda path: "ABSENT",
    )

    result = module["verify_published_payload_before_success"](
        destination, publish
    )

    used_names = sorted(record["name"] for record in publish["chunks"])
    present_names = {
        module["ATTEMPT_INTENT_LEAF_NAME"],
        module["PAYLOAD_MANIFEST_LEAF_NAME"],
        *used_names,
    }
    absent_names = sorted(
        set(module["reserved_candidate_leaf_names"]()) - present_names
    )
    assert result["attempt_intent"] == destination["intent"]
    assert result["payload_manifest"] == publish["payload_manifest_binding"]
    assert result["chunks"] == [bindings[name] for name in used_names]
    assert result["chunk_count"] == 2
    assert result["used_chunk_names_sha256"] == hashlib.sha256(
        module["canonical_json_bytes"](used_names)
    ).hexdigest()
    assert result["expected_present_reserved_leaf_count"] == 4
    assert result["expected_absent_reserved_leaf_count"] == 128
    assert result["expected_absent_reserved_leaf_names_sha256"] == (
        hashlib.sha256(module["canonical_json_bytes"](absent_names)).hexdigest()
    )
    assert result["reserved_namespace_projection_complete"] is True
    projection = dict(result)
    projection_sha256 = projection.pop("projection_sha256")
    assert projection_sha256 == hashlib.sha256(
        module["canonical_json_bytes"](projection)
    ).hexdigest()
    assert [call[0] for call in store.calls] == [
        module["ATTEMPT_INTENT_LEAF_NAME"],
        module["PAYLOAD_MANIFEST_LEAF_NAME"],
        *[record["name"] for record in publish["chunks"]],
    ]


def test_published_payload_rejects_duplicate_used_chunk(module, monkeypatch):
    destination, publish, store, _ = _published_payload_verification_case(
        module
    )
    publish["chunks"].append(dict(publish["chunks"][0]))
    monkeypatch.setitem(
        _globals(module, "verify_published_payload_before_success"),
        "object_kind",
        _forbidden("namespace visibility reached after malformed chunks"),
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_published_payload_before_success"](
            destination, publish
        )

    assert _error_code(raised) == "UC_PUBLISHED_CHUNK_NAMESPACE_INVALID"
    assert store.calls == []


@pytest.mark.parametrize("ordinals", ((1,), (1, 0)))
def test_published_payload_rejects_gapped_or_reordered_chunk_ordinals(
    module, monkeypatch, ordinals
):
    destination, publish, store, _ = _published_payload_verification_case(
        module, ordinals
    )
    monkeypatch.setitem(
        _globals(module, "verify_published_payload_before_success"),
        "object_kind",
        _forbidden("namespace visibility reached after malformed chunks"),
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_published_payload_before_success"](
            destination, publish
        )

    assert _error_code(raised) == "UC_PUBLISHED_CHUNK_NAMESPACE_INVALID"
    assert store.calls == []


@pytest.mark.parametrize(
    ("ordinal", "name_kind"),
    (
        ("0", "MATCH_ZERO"),
        (True, "MATCH_ZERO"),
        (1, "MATCH_ZERO"),
    ),
)
def test_published_payload_rejects_malformed_or_mismatched_chunk_ordinal(
    module, monkeypatch, ordinal, name_kind
):
    destination, publish, store, _ = _published_payload_verification_case(
        module
    )
    assert name_kind == "MATCH_ZERO"
    publish["chunks"][0]["ordinal"] = ordinal
    monkeypatch.setitem(
        _globals(module, "verify_published_payload_before_success"),
        "object_kind",
        _forbidden("namespace visibility reached after malformed chunks"),
    )

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_published_payload_before_success"](
            destination, publish
        )

    assert _error_code(raised) == "UC_PUBLISHED_CHUNK_NAMESPACE_INVALID"
    assert store.calls == []


def test_initial_attempt_state_is_unspent_and_has_no_false_success(module):
    state = module["initial_attempt_state"]()
    assert state["attempt_namespace_spent"] is False
    assert state["intent_create_begun"] is False
    assert state["durable_intent_committed"] is False
    assert state["managed_uc_exclusive_create_calls_begun"] == 0
    assert state["managed_uc_confirmed_leaf_count"] == 0
    assert state["managed_uc_confirmed_bytes_written"] == 0
    assert state["managed_uc_confirmed_bindings"] == []
    assert state["managed_uc_last_leaf_expected_sha256"] is None
    assert state["managed_uc_last_leaf_expected_size_bytes"] is None
    assert state["success_receipt_phase_entered"] is False
    assert state["success_receipt_create_call_begun"] is False
    assert state["success_receipt_may_exist"] is False
    assert state["success_receipt_committed"] is False
    assert state["failure_receipt_create_call_begun"] is False
    assert state["failure_receipt_may_exist"] is False
    assert state["failure_receipt_committed"] is False
    assert state["terminal_receipt_ambiguity"] is False
    assert state["command_journal"] == []


def test_persisted_attempt_snapshot_does_not_alias_confirmed_bindings(module):
    state = module["initial_attempt_state"]()
    first = {
        "name": "candidate.payload-0000.bin",
        "sha256": "a" * 64,
        "size_bytes": 7,
        "fresh_readback_count": 2,
    }
    second = {
        "name": "candidate.payload-0001.bin",
        "sha256": "b" * 64,
        "size_bytes": 11,
        "fresh_readback_count": 2,
    }
    state["managed_uc_confirmed_bindings"].append(first)
    state["managed_uc_confirmed_leaf_count"] = 1
    snapshot = module["immutable_json_snapshot"](state)
    state["managed_uc_confirmed_bindings"].append(second)
    state["managed_uc_confirmed_leaf_count"] = 2

    assert snapshot["managed_uc_confirmed_bindings"] == [first]
    assert snapshot["managed_uc_confirmed_leaf_count"] == 1
    assert snapshot["managed_uc_confirmed_bindings"] is not (
        state["managed_uc_confirmed_bindings"]
    )
    assert "dict(attempt_state)" not in NOTEBOOK.read_text(encoding="utf-8")


def test_attempt_intent_binds_namespace_evidence_and_network_hashes(module):
    profile = {"file_sha256": "1" * 64, "semantic_sha256": "2" * 64}
    source_manifest = {"record_sha256": "3" * 64}
    binding = {"relative_path": "review", "sha256": "4" * 64}
    probe_review = {"relative_path": "probe-review", "sha256": "5" * 64}
    probe_outcome = {"relative_path": "probe-outcome", "sha256": "6" * 64}
    builder = {"relative_path": "builder", "sha256": "7" * 64}
    launcher = {"relative_path": "launcher", "sha256": "8" * 64}
    review_package = {"record_sha256": "9" * 64}
    launch_evidence = {
        "schema_version": module["HASH_FIRST_LAUNCH_SCHEMA"],
        "same_in_memory_payload_compiled_and_executed": True,
    }
    preintent_source_identity = {
        "record_sha256": "a" * 64,
        "source_date_epoch": 1_700_000_000,
        "selected_source_bytes_match_reviewed_snapshot": True,
        "live_git_checkout_identity_verified": False,
    }
    record, payload = module["build_attempt_intent"](
        profile,
        binding,
        probe_review,
        probe_outcome,
        preintent_source_identity,
        source_manifest,
        builder,
        launcher,
        review_package,
        launch_evidence,
        module["CANDIDATE_PREFIX"],
        "https://pypi.org/simple",
        "https://download.pytorch.org/whl/cpu",
    )
    projection = dict(record)
    projection.pop("record_sha256")
    expected_record_hash = hashlib.sha256(
        module["ATTEMPT_INTENT_DOMAIN"]
        + module["canonical_json_bytes"](projection)
    ).hexdigest()
    assert record["record_sha256"] == expected_record_hash
    assert payload == module["canonical_json_bytes"](record) + b"\n"
    assert record["state"] == "ATTEMPT_SPENT_BEFORE_NETWORK_OR_BUILD"
    assert record["source"]["reviewed_source_identity"] == (
        preintent_source_identity
    )
    assert record["source"]["source_date_epoch"] == (
        preintent_source_identity["source_date_epoch"]
    )
    assert record["source"]["source_identity_verification_state"] == (
        module["SOURCE_IDENTITY_VERIFICATION_STATE"]
    )
    assert record["source"]["live_git_checkout_identity_verified"] is False
    assert record["source"]["whole_repository_cleanliness_checked"] is False
    assert record["destination"]["reserved_leaf_names"] == list(
        module["reserved_candidate_leaf_names"]()
    )
    assert record["destination"]["required_initial_state"] == (
        "ALL_RESERVED_LEAVES_ABSENT"
    )
    assert record["construction"]["success_receipt_is_commit_marker"] is True
    assert record["external_review_authority"] == {
        "review_package": review_package,
        "operator_authorized_review_package_sha256": "9" * 64,
        "authorization_matched_before_intent": True,
        "hash_first_launch_evidence": launch_evidence,
    }
    assert {
        "LARGE_OBJECT_WRITE_GENERALIZATION_FROM_PROBE",
        "CAPACITY_OR_STORAGE_RESERVATION",
        "UNOBSERVED_NATIVE_PROFILE_TARGET_FIELDS",
    }.issubset(record["nonproofs"])
    assert "https://" not in payload.decode("ascii")


def test_runtime_profile_observation_explicitly_limits_exactness_claim(module):
    profile = json.loads(
        (ROOT / module["PROFILE_RELATIVE_PATH"]).read_text(encoding="ascii")
    )
    observation = module["observe_runtime"](profile)
    assert observation["exact_scope"] == "WHEEL_SELECTION_RUNTIME_ABI_FIELDS_ONLY"
    assert observation["whole_native_profile_exact_claimed"] is False
    assert set(observation["unobserved_native_profile_target_fields"]) == {
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
    }


def _materialize_reviewed_snapshot_repo(
    module,
    tmp_path,
    *,
    executable_presentation=False,
    launcher_without_terminal_lf=False,
):
    repo = tmp_path / "snapshot-repo"
    (repo / "src").mkdir(parents=True)
    shutil.copytree(ROOT / "src" / "heterodiff", repo / "src" / "heterodiff")
    selected = (
        Path("README.md"),
        Path("pyproject.toml"),
        module["SOURCE_SNAPSHOT_RELATIVE_PATH"],
        module["BUILDER_NOTEBOOK_RELATIVE_PATH"],
        module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"],
    )
    for relative in selected:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    if launcher_without_terminal_lf:
        launcher = repo / module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"]
        payload = launcher.read_bytes()
        assert payload.endswith(b"\n")
        launcher.write_bytes(payload[:-1])
    if executable_presentation:
        for path in (
            repo / "README.md",
            repo / "pyproject.toml",
            *(repo / "src" / "heterodiff").rglob("*.py"),
            repo / module["SOURCE_SNAPSHOT_RELATIVE_PATH"],
            repo / module["BUILDER_NOTEBOOK_RELATIVE_PATH"],
            repo / module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"],
        ):
            path.chmod(0o755)
    return repo


def _reviewed_snapshot_bindings(module, repo):
    manifest = module["project_source_manifest"](repo)
    builder = module["canonical_source_binding"](
        repo,
        module["BUILDER_NOTEBOOK_RELATIVE_PATH"],
        "BUILDER_NOTEBOOK",
    )
    launcher = module["canonical_source_binding"](
        repo,
        module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"],
        "HASH_FIRST_LAUNCHER_NOTEBOOK",
        ignore_one_optional_terminal_lf=True,
    )
    return manifest, builder, launcher


def test_reviewed_snapshot_identity_is_gitless_mode_and_lf_transport_stable(
    module, monkeypatch, tmp_path
):
    repo = _materialize_reviewed_snapshot_repo(
        module,
        tmp_path,
        executable_presentation=True,
        launcher_without_terminal_lf=True,
    )
    assert not (repo / ".git").exists()
    monkeypatch.setattr(
        subprocess, "Popen", _forbidden("Git or child process attempted")
    )
    manifest, builder, launcher = _reviewed_snapshot_bindings(module, repo)
    identity = module["reviewed_source_snapshot_identity"](
        repo, manifest, builder, launcher
    )

    assert manifest["record_sha256"] == (
        module["EXPECTED_PROJECT_SOURCE_MANIFEST_SHA256"]
    )
    assert len(manifest["files"]) == module["EXPECTED_PROJECT_SOURCE_FILE_COUNT"]
    assert {record["mode_octal"] for record in manifest["files"]} == {"0644"}
    assert builder["canonical_mode_octal"] == "0644"
    assert launcher["canonical_mode_octal"] == "0644"
    assert identity["selected_source_bytes_match_reviewed_snapshot"] is True
    assert identity["runtime_git_metadata_consulted"] is False
    assert identity["live_git_checkout_identity_verified"] is False
    assert identity["whole_repository_cleanliness_checked"] is False
    projection = dict(identity)
    digest = projection.pop("record_sha256")
    assert digest == hashlib.sha256(
        module["SOURCE_IDENTITY_DOMAIN"]
        + module["canonical_json_bytes"](projection)
    ).hexdigest()


def test_reviewed_snapshot_rejects_one_byte_source_change(module, tmp_path):
    repo = _materialize_reviewed_snapshot_repo(module, tmp_path)
    source = repo / "src" / "heterodiff" / "__init__.py"
    source.write_bytes(source.read_bytes() + b"\n")
    manifest, builder, launcher = _reviewed_snapshot_bindings(module, repo)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["reviewed_source_snapshot_identity"](
            repo, manifest, builder, launcher
        )
    assert _error_code(raised) == "SOURCE_MANIFEST_DIFFERS_FROM_REVIEWED_SNAPSHOT"


def test_reviewed_snapshot_rejects_anchor_substitution(module, tmp_path):
    repo = _materialize_reviewed_snapshot_repo(module, tmp_path)
    anchor = repo / module["SOURCE_SNAPSHOT_RELATIVE_PATH"]
    anchor.write_bytes(anchor.read_bytes().replace(b"304", b"305", 1))
    manifest, builder, launcher = _reviewed_snapshot_bindings(module, repo)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["reviewed_source_snapshot_identity"](
            repo, manifest, builder, launcher
        )
    assert _error_code(raised) == "SOURCE_SNAPSHOT_FILE_BINDING_MISMATCH"


def test_reviewed_snapshot_rejects_unreviewed_extra_source(module, tmp_path):
    repo = _materialize_reviewed_snapshot_repo(module, tmp_path)
    (repo / "src" / "heterodiff" / "unreviewed_extra.py").write_bytes(
        b"UNREVIEWED = True\n"
    )
    manifest, builder, launcher = _reviewed_snapshot_bindings(module, repo)

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["reviewed_source_snapshot_identity"](
            repo, manifest, builder, launcher
        )
    assert _error_code(raised) == "SOURCE_MANIFEST_DIFFERS_FROM_REVIEWED_SNAPSHOT"


def test_launcher_binding_ignores_exactly_one_optional_terminal_lf(
    module, tmp_path
):
    repo = _materialize_reviewed_snapshot_repo(module, tmp_path)
    relative = module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"]
    with_lf = module["canonical_source_binding"](
        repo,
        relative,
        "HASH_FIRST_LAUNCHER_NOTEBOOK",
        ignore_one_optional_terminal_lf=True,
    )
    launcher = repo / relative
    launcher.write_bytes(launcher.read_bytes()[:-1])
    without_lf = module["canonical_source_binding"](
        repo,
        relative,
        "HASH_FIRST_LAUNCHER_NOTEBOOK",
        ignore_one_optional_terminal_lf=True,
    )
    assert with_lf == without_lf
    launcher.write_bytes(launcher.read_bytes() + b"\n\n")
    two_lf = module["canonical_source_binding"](
        repo,
        relative,
        "HASH_FIRST_LAUNCHER_NOTEBOOK",
        ignore_one_optional_terminal_lf=True,
    )
    assert two_lf != without_lf


def test_nonterminal_launcher_change_invalidates_review_package(
    module, tmp_path
):
    repo = _materialize_reviewed_snapshot_repo(module, tmp_path)
    manifest, builder, launcher = _reviewed_snapshot_bindings(module, repo)
    identity = module["reviewed_source_snapshot_identity"](
        repo, manifest, builder, launcher
    )
    profile = {"file_sha256": "1" * 64, "semantic_sha256": "2" * 64}
    review = {"relative_path": "review", "sha256": "3" * 64}
    probe_review = {"relative_path": "probe-review", "sha256": "4" * 64}
    probe_outcome = {"relative_path": "probe-outcome", "sha256": "5" * 64}
    original = module["candidate_review_package"](
        manifest,
        builder,
        launcher,
        identity,
        profile,
        review,
        probe_review,
        probe_outcome,
    )

    launcher_path = repo / module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"]
    payload = launcher_path.read_bytes()
    launcher_path.write_bytes(b"# changed\n" + payload)
    changed_launcher = module["canonical_source_binding"](
        repo,
        module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"],
        "HASH_FIRST_LAUNCHER_NOTEBOOK",
        ignore_one_optional_terminal_lf=True,
    )
    changed_identity = module["reviewed_source_snapshot_identity"](
        repo, manifest, builder, changed_launcher
    )
    changed = module["candidate_review_package"](
        manifest,
        builder,
        changed_launcher,
        changed_identity,
        profile,
        review,
        probe_review,
        probe_outcome,
    )

    assert changed_launcher["sha256"] != launcher["sha256"]
    assert changed["record_sha256"] != original["record_sha256"]


def test_builder_change_invalidates_launch_and_review_authorization(
    module, tmp_path
):
    repo = _materialize_reviewed_snapshot_repo(module, tmp_path)
    manifest, builder, launcher = _reviewed_snapshot_bindings(module, repo)
    identity = module["reviewed_source_snapshot_identity"](
        repo, manifest, builder, launcher
    )
    profile = {"file_sha256": "1" * 64, "semantic_sha256": "2" * 64}
    review = {"relative_path": "review", "sha256": "3" * 64}
    probe_review = {"relative_path": "probe-review", "sha256": "4" * 64}
    probe_outcome = {"relative_path": "probe-outcome", "sha256": "5" * 64}
    original = module["candidate_review_package"](
        manifest,
        builder,
        launcher,
        identity,
        profile,
        review,
        probe_review,
        probe_outcome,
    )
    launch_evidence = {
        "schema_version": module["HASH_FIRST_LAUNCH_SCHEMA"],
        "builder_relative_path": builder["relative_path"],
        "operator_expected_builder_sha256": builder["sha256"],
        "executed_payload_sha256": builder["sha256"],
        "executed_payload_size_bytes": builder["size_bytes"],
        "launcher_relative_path": launcher["relative_path"],
        "launcher_source_identity_kind": module[
            "LAUNCHER_SOURCE_IDENTITY_KIND"
        ],
        "launcher_source_sha256": launcher["sha256"],
        "launcher_source_size_bytes": launcher["size_bytes"],
        "launcher_terminal_lf_policy": module[
            "LAUNCHER_TERMINAL_LF_POLICY"
        ],
        "same_in_memory_payload_compiled_and_executed": True,
    }

    changed_builder = dict(builder)
    changed_builder["sha256"] = "f" * 64
    changed_identity = module["reviewed_source_snapshot_identity"](
        repo, manifest, changed_builder, launcher
    )
    changed = module["candidate_review_package"](
        manifest,
        changed_builder,
        launcher,
        changed_identity,
        profile,
        review,
        probe_review,
        probe_outcome,
    )
    validated, errors = module["validate_hash_first_launch_evidence"](
        launch_evidence, changed_builder, launcher
    )

    assert validated is None
    assert errors == ["HASH_FIRST_LAUNCH_EVIDENCE_BINDING_MISMATCH"]
    assert changed["record_sha256"] != original["record_sha256"]


def test_source_copy_uses_reviewed_mode_not_runtime_mount_mode(module, tmp_path):
    repo = tmp_path / "source"
    package = repo / "src" / "heterodiff"
    package.mkdir(parents=True)
    (repo / "pyproject.toml").write_bytes(b"[project]\nname='mode-test'\n")
    (repo / "README.md").write_bytes(b"mode test\n")
    (package / "__init__.py").write_bytes(b"VALUE = 1\n")
    for path in (repo / "pyproject.toml", repo / "README.md", package / "__init__.py"):
        path.chmod(0o755)
    manifest = module["project_source_manifest"](repo)
    destination = tmp_path / "copied"

    module["copy_source_tree"](repo, manifest, destination)

    assert module["project_source_manifest"](destination) == manifest
    for record in manifest["files"]:
        copied = destination / record["relative_path"]
        assert stat.S_IMODE(copied.stat().st_mode) == 0o644


def test_active_preflight_and_construct_never_call_git_identity():
    source = NOTEBOOK.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    for name in ("preflight", "construct_candidate"):
        calls = {
            node.func.id
            for node in ast.walk(functions[name])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "git_identity" not in calls
    construct_source = ast.get_source_segment(source, functions["construct_candidate"])
    assert construct_source is not None
    postintent = construct_source.index(
        "postintent_source_identity = reviewed_source_snapshot_identity("
    )
    staging = construct_source.index("tempfile.mkdtemp(")
    assert postintent < staging


def _git_source_binding(path, repo_root):
    payload = path.read_bytes()
    mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
    return {
        "relative_path": path.relative_to(repo_root).as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "mode_octal": format(mode, "04o"),
    }


def _git_provenance_fixture(module, tmp_path):
    repo = tmp_path / "repo"
    relative_paths = (
        "README.md",
        "pyproject.toml",
        "src/heterodiff/__init__.py",
        module["BUILDER_NOTEBOOK_RELATIVE_PATH"].as_posix(),
        module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"].as_posix(),
    )
    for ordinal, relative in enumerate(relative_paths):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"bound-{ordinal}\n".encode("ascii"))
    unbound = repo / "unbound-sensitive.txt"
    unbound.write_bytes(b"must not be read")
    bindings = {
        relative: _git_source_binding(repo / relative, repo)
        for relative in relative_paths
    }
    manifest_paths = (
        "README.md",
        "pyproject.toml",
        "src/heterodiff/__init__.py",
    )
    source_manifest = {
        "files": [bindings[relative] for relative in manifest_paths],
        "record_sha256": "f" * 64,
    }
    index_records = {}
    head_records = {}
    for relative in sorted(relative_paths):
        path = repo / relative
        payload = path.read_bytes()
        mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        blob = hashlib.sha1(
            b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
        ).hexdigest()
        index_records[relative] = f"{mode} {blob} 0\t{relative}\0".encode(
            "utf-8"
        )
        head_records[relative] = f"{mode} blob {blob}\t{relative}\0".encode(
            "utf-8"
        )
    return {
        "repo": repo,
        "unbound": unbound,
        "bindings": bindings,
        "source_manifest": source_manifest,
        "index_records": index_records,
        "head_records": head_records,
    }


def test_project_source_manifest_rejects_external_package_directory_symlink(
    module, tmp_path
):
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "pyproject.toml").write_bytes(b"[project]\nname = 'bounded'\n")
    (repo / "README.md").write_bytes(b"bounded\n")
    external_package = tmp_path / "external-package"
    external_package.mkdir()
    external_source = external_package / "__init__.py"
    external_source.write_bytes(b"EXTERNAL_SENTINEL = True\n")
    (repo / "src" / "heterodiff").symlink_to(
        external_package, target_is_directory=True
    )
    before = external_source.read_bytes()

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["project_source_manifest"](repo)

    assert _error_code(raised) == "SOURCE_PACKAGE_ROOT_NOT_PHYSICAL_DIRECTORY"
    assert external_source.read_bytes() == before


def test_git_provenance_reads_only_exact_bound_worktree_paths(
    module, monkeypatch, tmp_path
):
    fixture = _git_provenance_fixture(module, tmp_path)
    reads = []
    globals_ = _globals(module, "verify_source_manifest_git_provenance")
    original_read = globals_["read_physical_source_bytes"]

    def recording_read(path, root):
        reads.append(Path(path))
        return original_read(path, root)

    monkeypatch.setitem(globals_, "read_physical_source_bytes", recording_read)
    result = module["verify_source_manifest_git_provenance"](
        fixture["repo"],
        fixture["source_manifest"],
        fixture["bindings"]["databricks/notebooks/"
            "b08_n1_uc_native_overlay_lock_candidate.py"],
        fixture["bindings"]["databricks/notebooks/"
            "b08_n1_uc_native_overlay_lock_candidate_launcher.py"],
        b"".join(fixture["index_records"].values()),
        b"".join(fixture["head_records"].values()),
    )
    expected_reads = {
        fixture["repo"] / relative for relative in fixture["bindings"]
    }
    assert set(reads) == expected_reads
    assert len(reads) == len(expected_reads)
    assert fixture["unbound"] not in reads
    assert result["whole_repository_cleanliness_checked"] is False
    assert result["unbound_worktree_paths_accessed"] is False


def test_git_provenance_rejects_external_source_ancestor_symlink(
    module, tmp_path
):
    fixture = _git_provenance_fixture(module, tmp_path)
    package = fixture["repo"] / "src" / "heterodiff"
    external_package = tmp_path / "external-package"
    package.rename(external_package)
    package.symlink_to(external_package, target_is_directory=True)
    external_source = external_package / "__init__.py"
    before = external_source.read_bytes()

    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_source_manifest_git_provenance"](
            fixture["repo"],
            fixture["source_manifest"],
            fixture["bindings"]["databricks/notebooks/"
                "b08_n1_uc_native_overlay_lock_candidate.py"],
            fixture["bindings"]["databricks/notebooks/"
                "b08_n1_uc_native_overlay_lock_candidate_launcher.py"],
            b"".join(fixture["index_records"].values()),
            b"".join(fixture["head_records"].values()),
        )

    assert _error_code(raised) == "SOURCE_PATH_NOT_PHYSICAL_REGULAR_FILE"
    assert raised.value.detail == "src/heterodiff/__init__.py"
    assert external_source.read_bytes() == before


def test_git_provenance_rejects_staged_index_blob_divergent_from_head(
    module, tmp_path
):
    fixture = _git_provenance_fixture(module, tmp_path)
    relative = "src/heterodiff/__init__.py"
    mode = fixture["index_records"][relative].split(b" ", 1)[0].decode("ascii")
    fixture["index_records"][relative] = (
        f"{mode} {'0' * 40} 0\t{relative}\0".encode("utf-8")
    )
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["verify_source_manifest_git_provenance"](
            fixture["repo"],
            fixture["source_manifest"],
            fixture["bindings"]["databricks/notebooks/"
                "b08_n1_uc_native_overlay_lock_candidate.py"],
            fixture["bindings"]["databricks/notebooks/"
                "b08_n1_uc_native_overlay_lock_candidate_launcher.py"],
            b"".join(fixture["index_records"].values()),
            b"".join(fixture["head_records"].values()),
        )
    assert _error_code(raised) == "SOURCE_MANIFEST_CONTENT_OR_IDENTITY_MISMATCH"
    assert raised.value.detail == relative


def test_git_identity_uses_captured_revision_and_rechecks_head_before_build(
    module, monkeypatch, tmp_path
):
    first_revision = "1" * 40
    changed_revision = "2" * 40
    calls = []

    def fake_run_tool(journal, step, argv, *args, **kwargs):
        calls.append((step, list(argv)))
        return {
            "git_local_config_safety": b"",
            "git_revision": (first_revision + "\n").encode("ascii"),
            "git_index_source_stage": b"index",
            "git_head_source_tree": b"head",
            "git_commit_epoch": b"123456789\n",
            "git_revision_recheck_before_build": (
                changed_revision + "\n"
            ).encode("ascii"),
        }[step]

    globals_ = _globals(module, "git_identity")
    monkeypatch.setitem(globals_, "run_tool", fake_run_tool)
    monkeypatch.setitem(
        globals_,
        "verify_source_manifest_git_provenance",
        lambda *args: {"provenance": "verified"},
    )
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["git_identity"](
            tmp_path,
            [],
            {},
            "https://pypi.org/simple",
            "https://download.pytorch.org/whl/cpu",
            {},
            {},
            source_manifest={"files": []},
            builder_source_binding={"relative_path": "builder"},
            launcher_source_binding={"relative_path": "launcher"},
        )
    assert _error_code(raised) == "SOURCE_REVISION_CHANGED_DURING_BINDING"
    by_step = dict(calls)
    assert first_revision in by_step["git_head_source_tree"]
    assert first_revision in by_step["git_commit_epoch"]
    expected_pathspecs = [
        "pyproject.toml",
        "README.md",
        "src/heterodiff",
        module["BUILDER_NOTEBOOK_RELATIVE_PATH"].as_posix(),
        module["LAUNCHER_NOTEBOOK_RELATIVE_PATH"].as_posix(),
    ]
    for step in ("git_index_source_stage", "git_head_source_tree"):
        argv = by_step[step]
        assert argv[argv.index("--") + 1:] == expected_pathspecs
    assert "--stage" in by_step["git_index_source_stage"]
    assert all("status" not in argv for _, argv in calls)
    assert [step for step, _ in calls] == [
        "git_local_config_safety",
        "git_revision",
        "git_index_source_stage",
        "git_head_source_tree",
        "git_commit_epoch",
        "git_revision_recheck_before_build",
    ]
    assert by_step["git_revision_recheck_before_build"][-3:] == [
        "rev-parse",
        "--verify",
        "HEAD",
    ]


def test_success_receipt_verifies_intent_before_exclusive_write(module):
    intent = _intent_binding(module)
    store = _RecordingStore(intent)
    destination = _fake_destination(module, store)
    payload = b'{"decision":"success"}\n'
    binding = module["commit_success_receipt"](
        destination, intent["sha256"], intent["size_bytes"], payload
    )
    assert [event[0] for event in store.events] == ["verify", "write"]
    assert store.events[1][1] == module["SUCCESS_RECEIPT_LEAF_NAME"]
    assert binding["sha256"] == hashlib.sha256(payload).hexdigest()


def test_success_receipt_write_failure_is_terminally_ambiguous(module):
    intent = _intent_binding(module)
    state = module["initial_attempt_state"]()
    state["success_receipt_phase_entered"] = True
    injected = module["CandidateConstructionError"]("INJECTED_WRITE_FAILURE")
    store = _RecordingStore(
        intent,
        write_error=injected,
        attempt_state=state,
        mark_terminal_create_before_error=True,
    )
    destination = _fake_destination(module, store)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["commit_success_receipt"](
            destination, intent["sha256"], intent["size_bytes"], b"receipt\n"
        )
    assert _error_code(raised) == "UC_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert state["success_receipt_create_call_begun"] is True
    assert raised.value.telemetry["terminal_receipt_ambiguity"] is True
    assert raised.value.telemetry["success_receipt_may_exist"] is True


def test_success_parent_open_failure_before_create_keeps_failure_eligible(
    module, tmp_path, monkeypatch
):
    state = module["initial_attempt_state"]()
    state["success_receipt_phase_entered"] = True
    store = module["UcVolumeAppendOnlyStore"](
        tmp_path, module["reserved_candidate_leaf_names"](), state
    )
    destination = _fake_destination(module, store)

    def parent_open_fails():
        raise module["CandidateConstructionError"]("UC_PARENT_OPEN_FAILED")

    monkeypatch.setitem(
        _globals(module, "commit_success_receipt"),
        "verify_durable_intent_custody",
        lambda *args: destination["intent"],
    )
    monkeypatch.setattr(store, "_open_parent", parent_open_fails)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["commit_success_receipt"](
            destination,
            destination["intent"]["sha256"],
            destination["intent"]["size_bytes"],
            b"receipt\n",
        )
    assert _error_code(raised) == "UC_PARENT_OPEN_FAILED"
    assert state["success_receipt_phase_entered"] is True
    assert state["success_receipt_create_call_begun"] is False
    assert state["success_receipt_may_exist"] is False
    assert state["managed_uc_last_leaf_expected_sha256"] is None
    assert state["managed_uc_last_leaf_expected_size_bytes"] is None
    assert module["suppress_failure_receipt_if_success_publication_uncertain"](
        state
    ) is False
    assert state["failure_receipt_skipped_for_terminal_receipt_ambiguity"] is False


def test_success_leaf_create_call_boundary_records_expected_binding_and_ambiguity(
    module, tmp_path, monkeypatch
):
    state = module["initial_attempt_state"]()
    state["success_receipt_phase_entered"] = True
    store = module["UcVolumeAppendOnlyStore"](
        tmp_path, module["reserved_candidate_leaf_names"](), state
    )
    destination = _fake_destination(module, store)
    payload = b"success receipt bytes\n"
    original_open = os.open

    def interrupt_leaf_create(path, flags, *args, **kwargs):
        if path == module["SUCCESS_RECEIPT_LEAF_NAME"]:
            raise KeyboardInterrupt("at exclusive-create boundary")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setitem(
        _globals(module, "commit_success_receipt"),
        "verify_durable_intent_custody",
        lambda *args: destination["intent"],
    )
    monkeypatch.setattr(os, "open", interrupt_leaf_create)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["commit_success_receipt"](
            destination,
            destination["intent"]["sha256"],
            destination["intent"]["size_bytes"],
            payload,
        )
    assert _error_code(raised) == "UC_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert state["success_receipt_create_call_begun"] is True
    assert state["success_receipt_may_exist"] is True
    assert state["managed_uc_last_leaf_may_exist"] == (
        module["SUCCESS_RECEIPT_LEAF_NAME"]
    )
    assert state["managed_uc_last_leaf_expected_sha256"] == hashlib.sha256(
        payload
    ).hexdigest()
    assert state["managed_uc_last_leaf_expected_size_bytes"] == len(payload)
    assert raised.value.telemetry["success_receipt_expected_sha256"] == (
        hashlib.sha256(payload).hexdigest()
    )
    assert raised.value.telemetry["success_receipt_expected_size_bytes"] == len(
        payload
    )


def test_failure_receipt_verifies_intent_and_success_absence_before_write(
    module, monkeypatch
):
    intent = _intent_binding(module)
    store = _RecordingStore(intent)
    destination = _fake_destination(module, store)
    monkeypatch.setitem(
        _globals(module, "commit_failure_receipt"),
        "object_kind",
        lambda path: "ABSENT",
    )
    error = module["CandidateConstructionError"]("BUILD_FAILED", "injected")
    receipt, binding = module["commit_failure_receipt"](
        module["CANDIDATE_PREFIX"],
        destination,
        intent["sha256"],
        error,
        {"attempt_namespace_spent": True},
    )
    assert [event[0] for event in store.events] == ["verify", "write"]
    assert store.events[1][1] == module["FAILURE_RECEIPT_LEAF_NAME"]
    assert receipt["error_code"] == "BUILD_FAILED"
    assert receipt["error_detail"] == "injected"
    assert "attempt_state_before_failure_receipt_commit" in receipt
    assert "attempt_state" not in receipt
    assert binding["fresh_readback_count"] == 2


def test_failure_receipt_preserves_exact_bounded_sanitized_tool_failure(
    module, monkeypatch, tmp_path
):
    intent = _intent_binding(module)
    store = _RecordingStore(intent)
    destination = _fake_destination(module, store)
    cwd = tmp_path / "volatile-root"
    cwd.mkdir()
    primary = "https://pypi.org/simple"
    torch = "https://download.pytorch.org/whl/cpu"
    diagnostics = module["subprocess_failure_diagnostics"](
        os.fsencode(str(cwd)) + b" " + primary.encode("ascii"),
        b"https://sensitive-user-9081:sensitive-pass-7312@example.invalid/simple",
        {"stdout": 123, "stderr": 456},
        False,
        cwd,
        primary,
        torch,
    )
    attempt_state = {
        "attempt_namespace_spent": True,
        "command_journal": [
            {
                "step": "resolve-lock",
                "failure_diagnostics": diagnostics,
                "stdout_and_stderr_persisted": (
                    "BOUNDED_SANITIZED_FAILURE_EVIDENCE_ONLY"
                ),
            }
        ],
    }
    error = module["CandidateConstructionError"](
        "TOOL_STEP_FAILED", "resolve-lock:returncode=17"
    )
    globals_ = _globals(module, "commit_failure_receipt")
    monkeypatch.setitem(globals_, "object_kind", lambda path: "ABSENT")
    monkeypatch.setitem(
        globals_, "verify_durable_intent_custody", lambda *args: intent
    )

    receipt, _ = module["commit_failure_receipt"](
        module["CANDIDATE_PREFIX"],
        destination,
        intent["sha256"],
        error,
        attempt_state,
    )

    assert receipt["error_code"] == "TOOL_STEP_FAILED"
    assert receipt["error_detail"] == "resolve-lock:returncode=17"
    assert receipt["attempt_state_before_failure_receipt_commit"] == (
        module["immutable_json_snapshot"](attempt_state)
    )
    persisted = json.loads(store.events[-1][2])
    assert persisted == receipt
    encoded = store.events[-1][2]
    for secret in (
        str(cwd),
        primary,
        "sensitive-user-9081",
        "sensitive-pass-7312",
    ):
        assert secret.encode("utf-8") not in encoded
    assert b"<COMMAND_CWD>" in encoded
    assert b"<PRIMARY_INDEX_URL>" in encoded
    assert b"<REDACTED_CREDENTIALS>" in encoded


def test_failure_leaf_create_call_boundary_records_expected_binding_telemetry(
    module, tmp_path, monkeypatch
):
    intent = _intent_binding(module)
    state = module["initial_attempt_state"]()
    store = module["UcVolumeAppendOnlyStore"](
        tmp_path, module["reserved_candidate_leaf_names"](), state
    )
    destination = _fake_destination(module, store)
    original_open = os.open

    def interrupt_leaf_create(path, flags, *args, **kwargs):
        if path == module["FAILURE_RECEIPT_LEAF_NAME"]:
            raise KeyboardInterrupt("at exclusive-create boundary")
        return original_open(path, flags, *args, **kwargs)

    globals_ = _globals(module, "commit_failure_receipt")
    monkeypatch.setitem(
        globals_, "verify_durable_intent_custody", lambda *args: intent
    )
    monkeypatch.setitem(globals_, "object_kind", lambda path: "ABSENT")
    monkeypatch.setattr(os, "open", interrupt_leaf_create)
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["commit_failure_receipt"](
            module["CANDIDATE_PREFIX"],
            destination,
            intent["sha256"],
            module["CandidateConstructionError"]("BUILD_FAILED"),
            {"attempt_namespace_spent": True},
        )
    assert _error_code(raised) == "UC_FAILURE_RECEIPT_COMMIT_AMBIGUOUS"
    assert state["failure_receipt_create_call_begun"] is True
    assert state["failure_receipt_may_exist"] is True
    assert raised.value.telemetry["failure_receipt_expected_sha256"] == (
        state["managed_uc_last_leaf_expected_sha256"]
    )
    assert raised.value.telemetry["failure_receipt_expected_size_bytes"] == (
        state["managed_uc_last_leaf_expected_size_bytes"]
    )
    assert state["managed_uc_last_leaf_expected_sha256"] is not None
    assert state["managed_uc_last_leaf_expected_size_bytes"] > 0


def test_failure_receipt_is_suppressed_when_success_is_visible(
    module, monkeypatch
):
    intent = _intent_binding(module)
    store = _RecordingStore(intent)
    destination = _fake_destination(module, store)
    monkeypatch.setitem(
        _globals(module, "commit_failure_receipt"),
        "object_kind",
        lambda path: (
            "REGULAR_FILE"
            if path.name == module["SUCCESS_RECEIPT_LEAF_NAME"]
            else "ABSENT"
        ),
    )
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["commit_failure_receipt"](
            module["CANDIDATE_PREFIX"],
            destination,
            intent["sha256"],
            module["CandidateConstructionError"]("BUILD_FAILED"),
            {},
        )
    assert _error_code(raised) == (
        "UC_SUCCESS_RECEIPT_VISIBLE_FAILURE_RECEIPT_SUPPRESSED"
    )
    assert [event[0] for event in store.events] == ["verify"]
    assert raised.value.telemetry == {
        "terminal_receipt_ambiguity": True,
        "success_receipt_may_exist": True,
        "failure_receipt_skipped_for_terminal_receipt_ambiguity": True,
        "success_receipt_leaf_name": module["SUCCESS_RECEIPT_LEAF_NAME"],
        "success_receipt_observed_kind": "REGULAR_FILE",
    }


def test_public_failure_classification_honors_path_visible_success_receipt(
    module,
):
    source = NOTEBOOK.read_text(encoding="utf-8")
    preflight_call = "    preflight_result = preflight()"
    construct_call = "            result = construct_candidate(preflight_result)"
    visibility_call = """                    visible_control_objects[name] = object_kind(
                        CANDIDATE_PARENT / name
                    )"""
    assert source.count(preflight_call) == 1
    assert source.count(construct_call) == 1
    assert source.count(visibility_call) == 1
    instrumented = source.replace(
        preflight_call,
        '    preflight_result = {"construction_authorized": True}',
        1,
    ).replace(
        construct_call,
        "            raise CandidateConstructionError(\n"
        "                'INJECTED_FAILURE',\n"
        "                telemetry={'attempt_namespace_spent': True},\n"
        "            )",
        1,
    ).replace(
        visibility_call,
        "                    visible_control_objects[name] = (\n"
        "                        'REGULAR_FILE'\n"
        "                        if name == SUCCESS_RECEIPT_LEAF_NAME\n"
        "                        else 'ABSENT'\n"
        "                    )",
        1,
    )
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        exec(
            compile(instrumented, str(NOTEBOOK), "exec"),
            {"__name__": "__main__", "__file__": str(NOTEBOOK)},
        )
    result = json.loads(printed.getvalue())

    assert result["decision"] == (
        "TERMINAL_SUCCESS_RECEIPT_OUTCOME_AMBIGUOUS_REVIEW_REQUIRED"
    )
    assert result["success_receipt_outcome_ambiguous"] is True
    assert result["attempt_state"]["terminal_receipt_ambiguity"] is True
    assert result["attempt_state"]["success_receipt_may_exist"] is True
    assert result["uc_control_object_kinds_after_failure"][
        module["SUCCESS_RECEIPT_LEAF_NAME"]
    ] == "REGULAR_FILE"


def test_success_phase_entry_alone_does_not_suppress_failure_receipt(module):
    state = module["initial_attempt_state"]()
    state["success_receipt_phase_entered"] = True
    assert module["suppress_failure_receipt_if_success_publication_uncertain"](
        state
    ) is False
    assert state["terminal_receipt_ambiguity"] is False
    assert state["success_receipt_may_exist"] is False
    assert state["failure_receipt_skipped_for_terminal_receipt_ambiguity"] is False


def test_success_create_call_uncertainty_suppresses_failure_receipt(module):
    state = module["initial_attempt_state"]()
    state["success_receipt_phase_entered"] = True
    state["success_receipt_create_call_begun"] = True
    assert module["suppress_failure_receipt_if_success_publication_uncertain"](
        state
    ) is True
    assert state["terminal_receipt_ambiguity"] is True
    assert state["success_receipt_may_exist"] is True
    assert state["failure_receipt_skipped_for_terminal_receipt_ambiguity"] is True


def test_run_tool_verifies_intent_before_phase_flags_and_subprocess(
    module, monkeypatch, tmp_path
):
    events = []
    state = module["initial_attempt_state"]()
    state.update(
        {
            "durable_intent_committed": True,
            "durable_intent_expected_sha256": "a" * 64,
            "durable_intent_expected_size_bytes": 12,
        }
    )

    def verify(*args):
        events.append("verify")

    def execute(*args, **kwargs):
        assert events == ["verify"]
        assert state["network_contact_begun"] is True
        events.append("subprocess")
        return SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"")

    monkeypatch.setitem(
        _globals(module, "run_tool"), "verify_durable_intent_custody", verify
    )
    monkeypatch.setitem(
        _globals(module, "run_tool"), "run_subprocess_bounded", execute
    )
    journal = []
    output = module["run_tool"](
        journal,
        "network_step",
        ["tool", "--flag"],
        tmp_path,
        {},
        "https://pypi.org/simple",
        "https://download.pytorch.org/whl/cpu",
        state,
        ("network_contact_begun",),
        {"intent": "binding"},
    )
    assert events == ["verify", "subprocess"]
    assert output == b"ok"
    assert state["last_completed_step"] == "network_step"
    assert journal[0]["returncode"] == 0


def test_run_tool_tampered_intent_refuses_before_phase_or_subprocess(
    module, monkeypatch, tmp_path
):
    state = module["initial_attempt_state"]()
    state.update(
        {
            "durable_intent_committed": True,
            "durable_intent_expected_sha256": "a" * 64,
            "durable_intent_expected_size_bytes": 12,
        }
    )

    def reject(*args):
        raise module["CandidateConstructionError"]("UC_INTENT_TAMPERED")

    monkeypatch.setitem(
        _globals(module, "run_tool"), "verify_durable_intent_custody", reject
    )
    monkeypatch.setattr(subprocess, "run", _forbidden("subprocess attempted"))
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["run_tool"](
            [],
            "network_step",
            ["tool"],
            tmp_path,
            {},
            "https://pypi.org/simple",
            "https://download.pytorch.org/whl/cpu",
            state,
            ("network_contact_begun",),
            {"intent": "binding"},
        )
    assert _error_code(raised) == "UC_INTENT_TAMPERED"
    assert state["network_contact_begun"] is False
    assert state["last_failed_step"] == "network_step"


def test_run_tool_requires_committed_intent_before_custody_or_subprocess(
    module, monkeypatch, tmp_path
):
    state = module["initial_attempt_state"]()
    monkeypatch.setitem(
        _globals(module, "run_tool"),
        "verify_durable_intent_custody",
        _forbidden("custody verification attempted"),
    )
    monkeypatch.setattr(subprocess, "run", _forbidden("subprocess attempted"))
    with pytest.raises(module["CandidateConstructionError"]) as raised:
        module["run_tool"](
            [],
            "build_step",
            ["tool"],
            tmp_path,
            {},
            "https://pypi.org/simple",
            "https://download.pytorch.org/whl/cpu",
            state,
            (),
            {"intent": "binding"},
        )
    assert _error_code(raised) == "DURABLE_INTENT_REQUIRED_BEFORE_NETWORK_OR_BUILD"
