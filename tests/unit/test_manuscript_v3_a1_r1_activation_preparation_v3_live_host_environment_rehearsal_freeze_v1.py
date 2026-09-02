from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys

import pytest


WORKSPACE = Path(__file__).resolve().parents[2]
CONTRACTS_PATH = (
    WORKSPACE / "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_contracts_v3.py"
)
AUTHORITY_PATH = (
    WORKSPACE / "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_authority_v3.py"
)
RUNTIME_PATH = (
    WORKSPACE / "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_runtime_v3.py"
)


def _load(name: str, path: Path) -> object:
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


CONTRACTS = _load("v3_rehearsal_contracts_test", CONTRACTS_PATH)
AUTHORITY = _load("v3_rehearsal_authority_test", AUTHORITY_PATH)
RUNTIME = _load("v3_rehearsal_runtime_test", RUNTIME_PATH)

HUMAN = WORKSPACE / AUTHORITY.HUMAN_PATH
MACHINE = WORKSPACE / AUTHORITY.MACHINE_PATH
TEST = WORKSPACE / AUTHORITY.TEST_PATH
RESULT = WORKSPACE / AUTHORITY.RESULT_PATH


def _fail(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("forbidden live side effect reached in V3 freeze test")


@pytest.fixture(autouse=True)
def _forbid_live_rehearsal_entropy_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "Popen", _fail)
    monkeypatch.setattr(subprocess, "run", _fail)
    monkeypatch.setattr(subprocess, "call", _fail)
    monkeypatch.setattr(subprocess, "check_call", _fail)
    monkeypatch.setattr(subprocess, "check_output", _fail)
    monkeypatch.setattr(secrets, "token_bytes", _fail)
    monkeypatch.setattr(secrets, "token_hex", _fail)
    monkeypatch.setattr(socket, "create_connection", _fail)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha(label: str) -> str:
    return _sha256(label.encode("ascii"))


def _request() -> dict[str, object]:
    return CONTRACTS.finish_request(
        {
            "schema": CONTRACTS.REQUEST_SCHEMA,
            "registration_raw_sha256": _sha("registration-raw"),
            "registration_record_sha256": _sha("registration-record"),
            "human_sha256": _sha("human"),
            "contracts_sha256": _sha("contracts"),
            "authority_sha256": _sha("authority"),
            "runtime_sha256": _sha("runtime"),
            "test_sha256": _sha("test"),
            "v2_terminal_registration_record_sha256": (
                CONTRACTS.V2_TERMINAL_REGISTRATION_RECORD_SHA256
            ),
            "environment_policy_sha256": CONTRACTS.environment_policy()[
                "policy_sha256"
            ],
            "workspace_anchor_identity_sha256": _sha("workspace-anchor"),
            "profile_id": CONTRACTS.PROFILE_ID,
            "rehearsal_ordinal": 0,
            "python_relative_path": CONTRACTS.PYTHON_RELATIVE_PATH,
            "python_realpath": CONTRACTS.PYTHON_REALPATH,
            "python_flags": list(CONTRACTS.PYTHON_FLAGS),
            "requested_environment_sha256": CONTRACTS.REQUESTED_ENVIRONMENT_SHA256,
            "hash_probe_sha256": CONTRACTS.HASH_PROBE_SHA256,
            "child_observation_schema": CONTRACTS.CHILD_OBSERVATION_SCHEMA,
            "result_schema": CONTRACTS.RESULT_SCHEMA,
            "planned_result_relative_path": CONTRACTS.PLANNED_RESULT_RELATIVE_PATH,
            "future_v3_marker_relative_path": (
                CONTRACTS.FUTURE_V3_MARKER_RELATIVE_PATH
            ),
            "future_v3_preparation_root_relative_path": (
                CONTRACTS.FUTURE_V3_PREPARATION_ROOT_RELATIVE_PATH
            ),
            "workspace_write_requested": False,
            "entropy_requested": False,
            "network_contact_requested": False,
            "scientific_execution_requested": False,
            "request_sha256": None,
        }
    )


def _passing_snapshot() -> dict[str, object]:
    synthetic_uid = 12345
    environment = dict(RUNTIME.REQUESTED_ENVIRONMENT)
    environment[RUNTIME.DARWIN_KEY] = "0x%X:0x0:0x0" % synthetic_uid
    return {
        "environment": environment,
        "actual_darwin_key_removed_before_observation": True,
        "actual_environment_normalized_after_capture": True,
        "uid": synthetic_uid,
        "euid": synthetic_uid,
        "gid": 1234,
        "egid": 1234,
        "supplemental_root_group_absent": True,
        "process_taint_absent": True,
        "name": "__main__",
        "spec_is_none": True,
        "python_argv": list(RUNTIME.EXPECTED_PYTHON_ARGV),
        "native_argv": list(RUNTIME.EXPECTED_NATIVE_ARGV),
        "cwd": str(WORKSPACE),
        "implementation": "CPython",
        "version_info": [3, 11, 5],
        "platform": ["Darwin", "arm64"],
        "executable": str(RUNTIME.PYTHON_PATH),
        "executable_realpath": str(RUNTIME.PYTHON_REALPATH),
        "flags": {
            "dont_write_bytecode": 1,
            "hash_randomization": 0,
            "ignore_environment": 0,
            "isolated": 0,
            "no_site": 1,
            "no_user_site": 1,
            "safe_path": True,
            "utf8_mode": 1,
            "pycache_prefix_is_dev_null": True,
        },
        "hash_probe_sha256": RUNTIME.HASH_PROBE_SHA256,
        "sys_path": list(RUNTIME.EXPECTED_SYS_PATH),
        "site_imported": False,
    }


def _observation(snapshot: dict[str, object] | None = None) -> dict[str, object]:
    request = _request()
    return RUNTIME.evaluate_snapshot(
        _passing_snapshot() if snapshot is None else snapshot,
        request["request_sha256"],
    )


def _protected_snapshot() -> dict[str, object]:
    return {
        "schema": CONTRACTS.PROTECTED_SNAPSHOT_SCHEMA,
        "protected_path_roster_sha256": _sha("protected-roster"),
        "workspace_anchor_identity_sha256": _sha("workspace-anchor"),
        "rows": [],
        "v2_terminal_registration_record_sha256": (
            CONTRACTS.V2_TERMINAL_REGISTRATION_RECORD_SHA256
        ),
        "v2_terminal_validated_head_sha256": _sha("v2-head"),
        "v2_terminal_preparation_event_count": 3,
        "future_v3_marker_absent": True,
        "future_v3_preparation_root_absent": True,
        "planned_result_absent": True,
        "snapshot_sha256": _sha("snapshot"),
    }


def _supervisor() -> dict[str, bool]:
    return {
        "supervisor_direct_file_main": True,
        "supervisor_spec_is_none": True,
        "supervisor_python_argv_exact": True,
        "supervisor_native_argv_exact": True,
        "supervisor_environment_exact_after_normalization": True,
        "supervisor_python_flags_exact": True,
        "supervisor_cwd_exact": True,
        "supervisor_profile_exact": True,
    }


def _result_for_observation(observation: dict[str, object]) -> dict[str, object]:
    request = _request()
    request_payload = CONTRACTS.canonical_json(request) + b"\n"
    observation_payload = CONTRACTS.canonical_json(observation) + b"\n"
    child = {
        "launch_count": 1,
        "exit_observed": True,
        "exit_code": 0,
        "stdout": observation_payload,
        "stderr_byte_count": 0,
        "failure_code": None,
    }
    snapshot = _protected_snapshot()
    return AUTHORITY._build_result(
        CONTRACTS,
        request_payload,
        request,
        _supervisor(),
        snapshot,
        copy.deepcopy(snapshot),
        child,
    )


def test_six_additive_paths_exist_and_operational_v3_paths_remain_absent() -> None:
    owned = (HUMAN, MACHINE, CONTRACTS_PATH, AUTHORITY_PATH, RUNTIME_PATH, TEST)
    assert all(path.is_file() and not path.is_symlink() for path in owned)
    if not RESULT.exists():
        assert not (WORKSPACE / AUTHORITY.FUTURE_V3_MARKER_PATH).exists()
        assert not (WORKSPACE / AUTHORITY.FUTURE_V3_PREPARATION_ROOT).exists()
    for relative, digest, size in AUTHORITY.POSTMORTEM_BINDINGS:
        payload = (WORKSPACE / relative).read_bytes()
        assert len(payload) == size
        assert _sha256(payload) == digest


def test_machine_registration_is_canonical_self_digested_and_live_bound() -> None:
    payload = MACHINE.read_bytes()
    record = json.loads(payload.decode("ascii"))
    assert payload == _canonical(record) + b"\n"
    body = copy.deepcopy(record)
    claimed = body["record_sha256"]
    body["record_sha256"] = None
    assert claimed == _sha256(AUTHORITY.REGISTRATION_DOMAIN + _canonical(body))
    CONTRACTS_BOOTSTRAP = AUTHORITY._bootstrap_static_bindings(WORKSPACE)
    assert CONTRACTS_BOOTSTRAP[1] == record
    checked = AUTHORITY._load_registration(WORKSPACE, CONTRACTS)[1]
    assert checked == record
    assert record["milestone_state"] == AUTHORITY.PRE_RUN_STATE
    assert record["rehearsal_protocol"]["mechanical_one_shot_enforcement"] is False
    assert record["rehearsal_protocol"]["prepublication_replay_resistance"] is False
    authorization = record["user_authorization_provenance"]
    assert authorization["source"] == "CONVERSATION_VISIBLE_TEXT"
    assert authorization["normalized_visible_assent_text"] == "Okay, go through it."
    assert authorization["trailing_transport_whitespace_or_entity_normalized"] is True
    assert (
        authorization[
            "raw_user_message_transport_bytes_bound_as_registered_workspace_artifact"
        ]
        is False
    )
    assert authorization["rehearsal_retry_authorized"] is False
    assert authorization["v3_marker_root_nonce_or_capsule_authorized"] is False
    publication = record["publication_boundary"]
    assert publication["evidence_classification"] == "INTERNAL_PUBLICATION_EXCLUDED"
    assert publication["future_result_workspace_registration_required"] is True
    assert publication["future_result_anonymous_or_public_release_permitted"] is False
    assert (
        publication["publication_safe_derivative_requires_fresh_anonymity_audit"]
        is True
    )


def test_exact_sixteen_key_environment_and_flag_policy_is_frozen() -> None:
    policy = CONTRACTS.environment_policy()
    assert len(CONTRACTS.REQUESTED_ENVIRONMENT) == 16
    assert list(CONTRACTS.REQUESTED_ENVIRONMENT) == sorted(
        CONTRACTS.REQUESTED_ENVIRONMENT
    )
    assert policy["requested_environment"] == CONTRACTS.REQUESTED_ENVIRONMENT
    assert "PATH" not in CONTRACTS.REQUESTED_ENVIRONMENT
    assert "HOME" not in CONTRACTS.REQUESTED_ENVIRONMENT
    assert "PYTHONPATH" not in CONTRACTS.REQUESTED_ENVIRONMENT
    assert "PYTHONHOME" not in CONTRACTS.REQUESTED_ENVIRONMENT
    assert not any(key.startswith("DYLD_") for key in CONTRACTS.REQUESTED_ENVIRONMENT)
    assert CONTRACTS.REQUESTED_ENVIRONMENT["PYTHONHASHSEED"] == "0"
    assert CONTRACTS.REQUESTED_ENVIRONMENT["PYTHONNOUSERSITE"] == "1"
    assert list(CONTRACTS.PYTHON_FLAGS) == ["-P", "-B", "-S", "-X", "utf8"]
    assert "-I" not in CONTRACTS.PYTHON_FLAGS
    assert "-E" not in CONTRACTS.PYTHON_FLAGS
    assert "-s" not in CONTRACTS.PYTHON_FLAGS


def test_prefrozen_hash_probe_is_exact_and_not_outcome_selected() -> None:
    assert len(CONTRACTS.HASH_PROBE_PREIMAGE) == 82
    assert not CONTRACTS.HASH_PROBE_PREIMAGE.endswith(b"\n")
    assert CONTRACTS.HASH_PROBE_PREIMAGE == _canonical(
        list(CONTRACTS.HASH_PROBE_VALUES)
    )
    assert _sha256(CONTRACTS.HASH_PROBE_PREIMAGE) == CONTRACTS.HASH_PROBE_SHA256
    registration = json.loads(MACHINE.read_text("ascii"))
    fixture = registration["hash_probe"]
    assert fixture["fixture_known_before_live_rehearsal"] is True
    assert fixture["digest_domain"] == "DIRECT_SHA256_NO_DOMAIN_SEPARATOR"


def test_child_pass_observation_is_privacy_safe_and_strictly_validated() -> None:
    observation = _observation()
    assert observation["outcome"] == "PASS"
    assert observation["failure_code"] == "NONE"
    assert CONTRACTS.validate_child_observation(observation) == observation
    payload = CONTRACTS.canonical_json(observation)
    assert b"0x3039" not in payload
    assert b'"uid"' not in payload
    assert b'"gid"' not in payload
    assert str(WORKSPACE).encode() not in payload
    assert observation["raw_environment_emitted"] is False
    assert observation["raw_identity_emitted"] is False
    assert observation["hash_probe_sha256"] == CONTRACTS.HASH_PROBE_SHA256
    assert observation["hash_probe_matches_prefrozen_reference"] is True
    banned = b"0x1" + b"F5:0x0:0x0"
    for path in (HUMAN, MACHINE, CONTRACTS_PATH, AUTHORITY_PATH, RUNTIME_PATH, TEST):
        if path.exists():
            assert banned not in path.read_bytes()


def test_live_builder_removes_actual_injected_key_and_verifies_exact16(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_payload = CONTRACTS.canonical_json(_request()) + b"\n"
    snapshot = _passing_snapshot()
    snapshot.pop("actual_darwin_key_removed_before_observation")
    snapshot.pop("actual_environment_normalized_after_capture")
    actual_environment = dict(snapshot["environment"])
    monkeypatch.setattr(RUNTIME.os, "environ", actual_environment)
    monkeypatch.setattr(RUNTIME, "live_snapshot", lambda: copy.deepcopy(snapshot))
    observation = RUNTIME.build_live_observation(request_payload)
    assert actual_environment == RUNTIME.REQUESTED_ENVIRONMENT
    assert RUNTIME.DARWIN_KEY not in actual_environment
    assert observation["darwin_injected_removed_before_observation"] is True
    assert observation["requested_environment_exact_after_normalization"] is True
    assert CONTRACTS.validate_child_observation(observation) == observation


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda value: value["environment"].update({"PATH": "/bin"}),
            "EFFECTIVE_ENVIRONMENT",
        ),
        (
            lambda value: value["environment"].pop(RUNTIME.DARWIN_KEY),
            "DARWIN_ENVIRONMENT",
        ),
        (
            lambda value: (
                value.update({"uid": 0, "euid": 0}),
                value["environment"].update({RUNTIME.DARWIN_KEY: "0x0:0x0:0x0"}),
            ),
            "IDENTITY",
        ),
        (
            lambda value: value.update({"supplemental_root_group_absent": False}),
            "IDENTITY",
        ),
        (
            lambda value: value["flags"].update({"hash_randomization": 1}),
            "PYTHON_FLAGS",
        ),
        (lambda value: value.update({"hash_probe_sha256": "0" * 64}), "HASH_PROBE"),
        (lambda value: value.update({"sys_path": []}), "SYS_PATH"),
        (lambda value: value.update({"site_imported": True}), "SITE_MODULE"),
    ],
)
def test_child_failure_codes_are_exact_and_truthful(
    mutation: object, expected: str
) -> None:
    snapshot = _passing_snapshot()
    mutation(snapshot)
    observation = _observation(snapshot)
    assert observation["outcome"] == "FAIL"
    assert observation["failure_code"] == expected
    assert CONTRACTS.validate_child_observation(observation) == observation
    if expected == "HASH_PROBE":
        assert observation["hash_probe_sha256"] == CONTRACTS.HASH_PROBE_SHA256
        assert observation["hash_probe_matches_prefrozen_reference"] is False


def test_failure_priority_rejects_favorable_relabeling() -> None:
    snapshot = _passing_snapshot()
    snapshot["python_argv"] = []
    snapshot["flags"]["hash_randomization"] = 1
    snapshot["hash_probe_sha256"] = "0" * 64
    observation = _observation(snapshot)
    assert observation["failure_code"] == "ARGV"
    forged = copy.deepcopy(observation)
    forged["failure_code"] = "HASH_PROBE"
    forged["observation_sha256"] = None
    forged = CONTRACTS._finish(
        forged, "observation_sha256", CONTRACTS.CHILD_OBSERVATION_DOMAIN
    )
    with pytest.raises(CONTRACTS.ContractError):
        CONTRACTS.validate_child_observation(forged)
    leaked = copy.deepcopy(_observation(snapshot))
    leaked["hash_probe_sha256"] = "0" * 64
    leaked["observation_sha256"] = None
    leaked = CONTRACTS._finish(
        leaked, "observation_sha256", CONTRACTS.CHILD_OBSERVATION_DOMAIN
    )
    with pytest.raises(CONTRACTS.ContractError):
        CONTRACTS.validate_child_observation(leaked)


def test_pass_result_embeds_observation_and_binds_transport_and_snapshots() -> None:
    result = _result_for_observation(_observation())
    assert result["outcome"] == "PASS"
    assert result["child_launch_count"] == 1
    assert result["retry_count"] == 0
    assert result["mechanical_one_shot_enforced"] is False
    assert result["prepublication_replay_resistance"] is False
    assert CONTRACTS.validate_result(result) == result
    child_payload = CONTRACTS.canonical_json(result["child_observation"]) + b"\n"
    assert result["child_stdout_byte_count"] == len(child_payload)
    assert result["child_observation_raw_sha256"] == _sha256(child_payload)


def test_child_fail_result_is_preserved_without_selection_or_retry() -> None:
    snapshot = _passing_snapshot()
    snapshot["site_imported"] = True
    result = _result_for_observation(_observation(snapshot))
    assert result["outcome"] == "FAIL"
    assert result["failure_code"] == "SITE_MODULE"
    assert result["child_observation"]["site_imported"] is True
    assert result["retry_count"] == 0
    assert CONTRACTS.validate_result(result) == result


def test_transport_failure_is_typed_and_no_child_retry_is_represented() -> None:
    request = _request()
    request_payload = CONTRACTS.canonical_json(request) + b"\n"
    snapshot = _protected_snapshot()
    child = {
        "launch_count": 0,
        "exit_observed": False,
        "exit_code": None,
        "stdout": b"",
        "stderr_byte_count": 0,
        "failure_code": "CHILD_PROCESS",
    }
    result = AUTHORITY._build_result(
        CONTRACTS,
        request_payload,
        request,
        _supervisor(),
        snapshot,
        copy.deepcopy(snapshot),
        child,
    )
    assert result["outcome"] == "FAIL"
    assert result["failure_code"] == "CHILD_PROCESS"
    assert result["child_launch_count"] == 0
    assert result["child_exit_observed"] is False
    assert result["child_observation"] is None
    assert CONTRACTS.validate_result(result) == result


def test_preflight_precedes_child_failure_and_postflight_does_not_censor_child() -> None:
    request = _request()
    request_payload = CONTRACTS.canonical_json(request) + b"\n"
    child_observation = _observation({**_passing_snapshot(), "site_imported": True})
    child = {
        "launch_count": 1,
        "exit_observed": True,
        "exit_code": 0,
        "stdout": CONTRACTS.canonical_json(child_observation) + b"\n",
        "stderr_byte_count": 0,
        "failure_code": None,
    }
    preflight = _protected_snapshot()
    preflight["planned_result_absent"] = False
    preflight_failure = AUTHORITY._build_result(
        CONTRACTS,
        request_payload,
        request,
        _supervisor(),
        preflight,
        copy.deepcopy(preflight),
        child,
    )
    assert preflight_failure["failure_code"] == "PROTECTED_CUSTODY"
    assert CONTRACTS.validate_result(preflight_failure) == preflight_failure

    clean = _protected_snapshot()
    dirty_postflight = copy.deepcopy(clean)
    dirty_postflight["planned_result_absent"] = False
    postflight_and_child_failure = AUTHORITY._build_result(
        CONTRACTS,
        request_payload,
        request,
        _supervisor(),
        clean,
        dirty_postflight,
        child,
    )
    assert postflight_and_child_failure["failure_code"] == "SITE_MODULE"
    assert CONTRACTS.validate_result(postflight_and_child_failure) == (
        postflight_and_child_failure
    )


def test_contracts_reject_extra_keys_bool_integer_alias_and_rehashed_drift() -> None:
    request = _request()
    for mutation in (
        lambda value: value.update({"extra": False}),
        lambda value: value.update({"rehearsal_ordinal": False}),
        lambda value: value.update({"python_flags": ["-I", "-S", "-B"]}),
        lambda value: value.update({"planned_result_relative_path": "elsewhere.json"}),
    ):
        forged = copy.deepcopy(request)
        mutation(forged)
        forged["request_sha256"] = None
        forged = CONTRACTS._finish(forged, "request_sha256", CONTRACTS.REQUEST_DOMAIN)
        with pytest.raises(CONTRACTS.ContractError):
            CONTRACTS.validate_request(forged)


def test_status_is_read_only_and_transition_classification_is_future_safe() -> None:
    status = AUTHORITY.status()
    assert status["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert status["execution_authorized"] is False
    assert status["marker_authorized"] is False
    if (
        status["future_v3_marker_present"]
        or status["future_v3_preparation_root_present"]
    ):
        expected_state = AUTHORITY.UNVALIDATED_FUTURE_STATE
    else:
        expected_state = {
            "ABSENT": AUTHORITY.PRE_RUN_STATE,
            "PASS": AUTHORITY.PASS_STATE,
            "FAIL": AUTHORITY.FAIL_STATE,
            "INVALID": AUTHORITY.INVALID_RESULT_STATE,
        }[status["result_state"]]
    assert status["milestone_state"] == expected_state
    if RESULT.exists():
        parsed = CONTRACTS.parse_canonical(RESULT.read_bytes(), "RESULT")
        if status["result_state"] in {"PASS", "FAIL"}:
            assert status["result_sha256"] == parsed["result_sha256"]
        else:
            assert status["result_state"] == "INVALID"
    assert AUTHORITY._classify_transition("PASS", False, False) == AUTHORITY.PASS_STATE
    assert AUTHORITY._classify_transition("FAIL", False, False) == AUTHORITY.FAIL_STATE
    assert (
        AUTHORITY._classify_transition("PASS", True, True)
        == AUTHORITY.UNVALIDATED_FUTURE_STATE
    )
    with pytest.raises(TypeError):
        AUTHORITY.StaticRehearsalQualification()
    qualification = AUTHORITY.load_static_qualification()
    assert qualification.record_sha256 == status["static_registration_record_sha256"]


def test_imported_runpy_and_forged_argument_routes_cannot_launch() -> None:
    assert AUTHORITY.main(["--status"]) == 64
    assert RUNTIME.main(["--wrong-child-action"]) == 64
    with pytest.raises(AUTHORITY.RehearsalAuthorityError):
        AUTHORITY.rehearse_live_host()


def test_source_import_and_effect_inventory_is_narrow_and_no_writer_exists() -> None:
    contracts_tree = ast.parse(CONTRACTS_PATH.read_text("utf-8"))
    authority_tree = ast.parse(AUTHORITY_PATH.read_text("utf-8"))
    runtime_tree = ast.parse(RUNTIME_PATH.read_text("utf-8"))
    forbidden_imports = {
        "heterodiff",
        "numpy",
        "scipy",
        "torch",
        "secrets",
        "socket",
        "tempfile",
    }
    for tree in (contracts_tree, authority_tree, runtime_tree):
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        assert not imported & forbidden_imports
    runtime_imports = {
        alias.name.split(".")[0]
        for node in ast.walk(runtime_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "subprocess" not in runtime_imports
    authority_text = AUTHORITY_PATH.read_text("utf-8")
    runtime_text = RUNTIME_PATH.read_text("utf-8")
    assert authority_text.count("subprocess.Popen(") == 1
    assert authority_text.count('getattr(sys.flags, "safe_path", False)') == 1
    assert runtime_text.count('getattr(sys.flags, "safe_path", False)') == 1
    assert "secrets." not in authority_text
    assert "socket." not in authority_text
    assert "O_WRONLY" not in authority_text
    assert "O_CREAT" not in authority_text
    assert "write_text(" not in authority_text
    assert "write_bytes(" not in authority_text


def test_hashes_are_checked_before_contract_or_child_execution() -> None:
    authority_text = AUTHORITY_PATH.read_text("utf-8")
    bootstrap_offset = authority_text.index("def _bootstrap_static_bindings")
    contracts_pin_offset = authority_text.index(
        'contracts_row["raw_sha256"] != EXPECTED_CONTRACTS_RAW_SHA256',
        bootstrap_offset,
    )
    runtime_pin_offset = authority_text.index(
        'runtime_row["raw_sha256"] != EXPECTED_RUNTIME_RAW_SHA256',
        bootstrap_offset,
    )
    module_execution_offset = authority_text.index("specification.loader.exec_module")
    assert bootstrap_offset > module_execution_offset
    assert contracts_pin_offset > bootstrap_offset
    assert runtime_pin_offset > contracts_pin_offset
    assert "_bootstrap_static_bindings(WORKSPACE_ROOT)" in authority_text
    rehearsal_offset = authority_text.index("def rehearse_live_host")
    preflight_offset = authority_text.index(
        "preflight = _protected_snapshot", rehearsal_offset
    )
    pristine_offset = authority_text.index(
        'raise RehearsalAuthorityError("rehearsal preflight is not pristine")',
        preflight_offset,
    )
    child_offset = authority_text.index("child = _run_child_bounded", pristine_offset)
    assert preflight_offset < pristine_offset < child_offset


def test_tampered_contract_is_rejected_before_any_module_execution(
    tmp_path: Path,
) -> None:
    for _, relative in AUTHORITY.STATIC_BINDING_PATHS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(WORKSPACE / relative, destination)
    machine_destination = tmp_path / AUTHORITY.MACHINE_PATH
    machine_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MACHINE, machine_destination)
    contract_destination = tmp_path / AUTHORITY.CONTRACTS_PATH
    contract_destination.write_bytes(contract_destination.read_bytes() + b"\n")
    with pytest.raises(AUTHORITY.RehearsalAuthorityError):
        AUTHORITY._bootstrap_static_bindings(tmp_path)


def test_transport_buffer_is_bounded_and_reports_exact_overrun() -> None:
    target = bytearray(b"abc")
    assert AUTHORITY._bounded_extend(target, b"defgh", 6) is True
    assert bytes(target) == b"abcdef"
    assert len(target) == 6
    full = bytearray(b"abcd")
    assert AUTHORITY._bounded_extend(full, b"x", 4) is True
    assert bytes(full) == b"abcd"


def test_stdout_overflow_kill_remains_a_typed_bounded_failure() -> None:
    request = _request()
    request_payload = CONTRACTS.canonical_json(request) + b"\n"
    snapshot = _protected_snapshot()
    child = {
        "launch_count": 1,
        "exit_observed": True,
        "exit_code": -9,
        "stdout": b"x" * AUTHORITY.MAXIMUM_CHILD_STDOUT_BYTES,
        "stderr_byte_count": 0,
        "failure_code": "CHILD_STDOUT",
    }
    result = AUTHORITY._build_result(
        CONTRACTS,
        request_payload,
        request,
        _supervisor(),
        snapshot,
        copy.deepcopy(snapshot),
        child,
    )
    assert result["outcome"] == "FAIL"
    assert result["failure_code"] == "CHILD_STDOUT"
    assert result["child_stdout_byte_count"] == 64 * 1024
    assert result["child_exit_code"] == -9
    assert CONTRACTS.validate_result(result) == result


def test_status_admission_rejects_impossible_rehashed_result_gates() -> None:
    admitted = _result_for_observation(_observation())
    assert AUTHORITY._result_matches_canonical_route(admitted) is True
    for name in (
        "supervisor_native_argv_exact",
        "protected_custody_unchanged",
        "planned_result_absent_after",
    ):
        forged = copy.deepcopy(admitted)
        forged[name] = False
        forged["outcome"] = "FAIL"
        forged["failure_code"] = (
            "SUPERVISOR_BOUNDARY"
            if name.startswith("supervisor_")
            else "PROTECTED_CUSTODY"
        )
        forged["result_sha256"] = None
        forged = CONTRACTS._finish(forged, "result_sha256", CONTRACTS.RESULT_DOMAIN)
        CONTRACTS.validate_result(forged)
        assert AUTHORITY._result_matches_canonical_route(forged) is False
    unsafe_child = copy.deepcopy(_observation())
    unsafe_child["raw_environment_emitted"] = True
    unsafe_child["outcome"] = "FAIL"
    unsafe_child["failure_code"] = "RAW_ENVIRONMENT_EMISSION"
    unsafe_child["observation_sha256"] = None
    unsafe_child = CONTRACTS._finish(
        unsafe_child, "observation_sha256", CONTRACTS.CHILD_OBSERVATION_DOMAIN
    )
    unsafe_result = _result_for_observation(unsafe_child)
    assert CONTRACTS.validate_result(unsafe_result) == unsafe_result
    assert AUTHORITY._result_matches_canonical_route(unsafe_result) is False


def test_workspace_anchor_is_canonical_internal_and_copy_replay_is_rejected(
    tmp_path: Path,
) -> None:
    anchor = AUTHORITY.workspace_anchor_identity()
    assert anchor["contains_no_path_uid_gid_or_cf_value"] is True
    assert anchor["publication_inclusion_permitted"] is False
    assert set(anchor) == {
        "schema",
        "root_identity",
        "pyproject_identity",
        "contains_no_path_uid_gid_or_cf_value",
        "publication_inclusion_permitted",
        "identity_sha256",
    }
    with pytest.raises(AUTHORITY.RehearsalAuthorityError):
        AUTHORITY.workspace_anchor_identity(tmp_path)


def test_no_focused_pyc_or_pycache_artifact_is_created() -> None:
    stems = (
        CONTRACTS_PATH.stem,
        AUTHORITY_PATH.stem,
        RUNTIME_PATH.stem,
        TEST.stem,
    )
    matches = []
    for root in (WORKSPACE / "research/production", WORKSPACE / "tests/unit"):
        cache = root / "__pycache__"
        if cache.exists():
            matches.extend(
                path
                for path in cache.iterdir()
                if any(stem in path.name for stem in stems)
            )
    assert matches == []
