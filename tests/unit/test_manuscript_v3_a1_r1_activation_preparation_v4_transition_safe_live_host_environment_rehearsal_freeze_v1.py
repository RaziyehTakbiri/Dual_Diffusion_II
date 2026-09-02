from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import types

import pytest


ROOT = Path(__file__).resolve().parents[2]
HUMAN = ROOT / (
    "manuscript_v3/a1_r1_activation_preparation_v4_transition_safe_live_host_"
    "environment_rehearsal_freeze_v1.md"
)
MACHINE = ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_freeze_v1.json"
)
CONTRACTS = ROOT / (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_contracts_v4.py"
)
AUTHORITY = ROOT / (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_authority_v4.py"
)
RUNTIME = ROOT / (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_runtime_v4.py"
)
TEST = Path(__file__).resolve()
V3_HUMAN = ROOT / (
    "manuscript_v3/a1_r1_activation_preparation_v3_live_host_environment_"
    "rehearsal_terminal_failure_registration_v1.md"
)
V3_MACHINE = ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_"
    "host_environment_rehearsal_terminal_failure_registration_v1.json"
)
V3_VALIDATOR = ROOT / (
    "research/diagnostics/finite_association_r1_activation_preparation_v3_"
    "live_host_environment_rehearsal_terminal_failure_registration_v1.py"
)
V3_TEST = ROOT / (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_terminal_failure_registration_v1.py"
)
V3_BINDINGS = (
    (V3_HUMAN, 13052, "f89fcf120c3afdd4930621c325e3daec7715ba28443c1a9f191a0ac39a163c71"),
    (V3_MACHINE, 21053, "282188fc035c835e54acb0da6f1cdafa0a3d9d4f98e89650180b583ba31218c7"),
    (V3_VALIDATOR, 44262, "2ae995d7609778f9201e3a90a2861c74898dfdc357b3f0b6f75b46bc68ce78bd"),
    (V3_TEST, 26261, "6872b0923e118c4ceee297d5c8deb7d479a930892338596ce1751c055f29a2a5"),
)
V3_SELF = "69f730c8579c25750240831141f67777e8477b2b0ad93eab632ef7df4549216a"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _file_bytes(value: object) -> bytes:
    return _canonical(value) + b"\n"


def _load_raw_module(name: str, path: Path) -> types.ModuleType:
    raw = path.read_bytes()
    namespace = {
        "__name__": name,
        "__file__": str(path),
        "__package__": "",
        "__spec__": None,
    }
    module = types.ModuleType(name)
    module.__dict__.update(namespace)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def modules() -> tuple[types.ModuleType, types.ModuleType, types.ModuleType]:
    return (
        _load_raw_module("v4_contracts_fixture", CONTRACTS),
        _load_raw_module("v4_authority_fixture", AUTHORITY),
        _load_raw_module("v4_runtime_fixture", RUNTIME),
    )


def _machine_record() -> tuple[bytes, dict[str, object]]:
    raw = MACHINE.read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert type(record) is dict
    assert _file_bytes(record) == raw
    return raw, record


def _attach(authority: types.ModuleType, body: dict[str, object], key: str) -> dict[str, object]:
    return authority._attach(body, key)


def _base_chain(
    contracts: types.ModuleType,
    authority: types.ModuleType,
    *,
    admitted: bool,
) -> dict[str, object]:
    registration = _attach(authority, {"fixture": "ISOLATED_SYNTHETIC"}, "record_sha256")
    registration_raw = _file_bytes(registration)
    authorization_body = authority._authorization_expected_fields()
    authorization_body.update(
        {
            "v4_registration_record_sha256": registration["record_sha256"],
            "v4_registration_raw_sha256": _sha(registration_raw),
        }
    )
    authorization = _attach(authority, authorization_body, "record_sha256")
    authorization_raw = _file_bytes(authorization)
    marker = authority._make_marker(
        registration_raw, registration, authorization_raw, authorization
    )
    marker_raw = _file_bytes(marker)
    genesis = authority._make_genesis(
        marker_raw,
        marker,
        registration_raw,
        authorization_raw,
        authorization,
    )
    genesis_raw = _file_bytes(genesis)
    event_zero = authority._make_event_zero(
        marker_raw, marker, registration_raw, genesis_raw, genesis
    )
    event_zero_raw = _file_bytes(event_zero)
    gates = {name: True for name in authority.PRECHILD_GATE_ORDER}
    if not admitted:
        gates["v4_source_closure_exact"] = False
    event_one = authority._make_prechild_event(
        contracts if admitted else None,
        admitted,
        gates,
        marker_raw,
        marker,
        registration_raw,
        event_zero_raw,
        event_zero,
    )
    event_one_raw = _file_bytes(event_one)
    return {
        "registration": registration,
        "registration_raw": registration_raw,
        "authorization": authorization,
        "authorization_raw": authorization_raw,
        "marker": marker,
        "marker_raw": marker_raw,
        "genesis": genesis,
        "genesis_raw": genesis_raw,
        "event_zero": event_zero,
        "event_zero_raw": event_zero_raw,
        "event_one": event_one,
        "event_one_raw": event_one_raw,
    }


def _put(path: Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(mode)


def _make_operational_fixture(
    root: Path,
    authority: types.ModuleType,
    chain: dict[str, object],
) -> dict[str, Path]:
    paths = authority._operational_paths(root)
    for directory in (paths["root"], paths["ledger"], paths["events"]):
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)
    _put(paths["lock"], b"", 0o600)
    _put(paths["genesis"], chain["genesis_raw"], 0o600)
    return paths


def test_static_registration_self_cycle_and_absences(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, runtime = modules
    raw, machine = _machine_record()
    assert machine["schema_version"] == contracts.REGISTRATION_SCHEMA
    assert machine["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert machine["milestone_state"] == contracts.STATIC_STATE
    body = dict(machine)
    claimed = body.pop("record_sha256")
    assert claimed == _sha(_canonical(body))
    plan = dict(machine)
    plan.pop("record_sha256")
    plan.pop("static_plan_sha256")
    plan.pop("registration_bindings")
    assert machine["static_plan_sha256"] == _sha(_canonical(plan))
    assert machine["static_plan_sha256"] == authority.EXPECTED_REGISTRATION_STATIC_PLAN_SHA256
    expected = (
        ("HUMAN_FREEZE", HUMAN),
        ("CONTRACTS", CONTRACTS),
        ("SOLE_WRITER_AUTHORITY", AUTHORITY),
        ("ENVIRONMENT_CHILD", RUNTIME),
        ("HOSTILE_TEST", TEST),
    )
    rows = machine["registration_bindings"]
    assert len(rows) == len(expected)
    for ordinal, (row, (role, path)) in enumerate(zip(rows, expected)):
        payload = path.read_bytes()
        status = path.lstat()
        assert row == {
            "ordinal": ordinal,
            "role": role,
            "path": str(path.relative_to(ROOT)),
            "raw_sha256": _sha(payload),
            "bytes": len(payload),
            "mode_octal": "0644",
            "nlink": 1,
        }
        assert stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode)
        assert stat.S_IMODE(status.st_mode) == 0o644 and status.st_nlink == 1
    assert authority.EXPECTED_CONTRACTS_RAW_SHA256 == _sha(CONTRACTS.read_bytes())
    assert authority.EXPECTED_RUNTIME_RAW_SHA256 == _sha(RUNTIME.read_bytes())
    assert authority._load_registration() == (raw, machine)
    for path in (
        authority.AUTHORIZATION_PATH,
        authority.MARKER_PATH,
        authority.PREPARATION_ROOT,
        authority.RESULT_PATH,
    ):
        with pytest.raises(FileNotFoundError):
            path.lstat()


def test_static_status_is_read_only_and_preauthorized_false(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    _contracts, authority, _runtime = modules
    before = {path: _sha(path.read_bytes()) for path in (HUMAN, MACHINE, CONTRACTS, AUTHORITY, RUNTIME, TEST)}
    status = authority.status()
    after = {path: _sha(path.read_bytes()) for path in before}
    assert after == before
    assert status["milestone_state"] == authority.STATIC_STATE
    assert status["registration_record_exact"] is True
    assert status["source_closure_evaluated_by_status"] is False
    assert status["authorization_record_present"] is False
    assert status["live_rehearsal_authorized_by_certificate"] is False
    assert status["prechild_admission_ready_claimed"] is False
    assert status["attempt_spent"] is False
    assert status["retry_permitted"] is False


def test_v3_terminal_and_transitive_v2_custody_reopen() -> None:
    for path, size, digest in V3_BINDINGS:
        raw = path.read_bytes()
        assert len(raw) == size and _sha(raw) == digest
    v3_machine = json.loads(V3_MACHINE.read_text("ascii"))
    assert v3_machine["record_sha256"] == V3_SELF
    validator = _load_raw_module("v3_terminal_validator_for_v4", V3_VALIDATOR)
    status = validator.status(ROOT)
    custody = validator.audit_terminal_custody(ROOT)
    assert status["canonical_rehearsal_attempt_count"] == 1
    assert status["canonical_rehearsal_retry_count"] == 0
    assert status["child_launch_count"] is None
    assert status["retry_permitted"] is False
    assert custody["v2_preparation_file_count"] == 65
    assert custody["v2_preparation_directory_count"] == 20
    assert custody["v2_capsule"]["file_count"] == 53
    assert custody["v2_capsule"]["directory_count"] == 14
    assert custody["v2_capsule"]["inventory_sha256"] == (
        "c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360"
    )
    assert custody["v2_unresolved_null_count"] == 172
    assert custody["v2_open_blocker_count"] == 12
    assert custody["v2_d1_quarantine_row_count"] == 550


def test_authorization_templates_are_unissued_and_superseded_values_rejected(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    _contracts, authority, _runtime = modules
    _raw, machine = _machine_record()
    assert len(authority.AUTHORIZATION_CONTEXT_TEXT.encode("utf-8")) == 1126
    assert _sha(
        b"heterodiff-a1-r1-activation-preparation-v4-authorization-context-v1\0"
        + authority.AUTHORIZATION_CONTEXT_TEXT.encode("utf-8")
    ) == authority.AUTHORIZATION_CONTEXT_SHA256
    assert _sha(
        b"heterodiff-a1-r1-activation-preparation-v4-visible-user-authorization-v1\0"
        + authority.VISIBLE_ASSENT_TEXT.encode("utf-8")
    ) == authority.VISIBLE_ASSENT_SHA256
    expected_superseded = {
        "b9dcb7c6f48a743a0b9977ff55fd8646dd077f1e39b7b1a0eb383bcfbb551f4e",
        "a96eccdbe23b5314cd8eb09f666389d84c6171b43124c9410b15ddef30f663c2",
        "4f8e2bffb835e0cb9966c74b4b527d014ef9a7f0e47b6b9a10a545bc18cfa7b1",
        "228867a3116d4a3e37c9b292907391ffd300a245a614eb8acdd0102cce600470",
    }
    assert set(machine["future_execution_authorization"]["superseded_digest_roster"]) == expected_superseded
    assert machine["future_execution_authorization"]["fresh_execution_authorization_observed"] is False
    assert machine["future_execution_authorization"]["execution_authorization_record_present"] is False
    assert machine["future_execution_authorization"]["live_rehearsal_authorized"] is False
    assert machine["future_execution_authorization"]["scientific_execution_authorized"] is False


def test_contracts_accept_every_frozen_nonchild_terminal_branch(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, _runtime = modules
    failed = _base_chain(contracts, authority, admitted=False)
    contracts.validate_full_prefix(
        failed["marker"],
        failed["marker_raw"],
        failed["authorization"],
        failed["registration"]["record_sha256"],
        _sha(failed["registration_raw"]),
        failed["genesis"],
        failed["genesis_raw"],
        [failed["event_zero"], failed["event_one"]],
        [failed["event_zero_raw"], failed["event_one_raw"]],
    )
    projection = authority._make_terminal_projection(
        failed["marker_raw"],
        failed["marker"],
        failed["registration_raw"],
        failed["event_one_raw"],
        failed["event_one"],
    )
    projection_raw = _file_bytes(projection)
    result = authority._make_published_result(
        failed["registration"], failed["marker"], projection_raw, projection
    )
    contracts.validate_published_result_against_full_prefix(
        result,
        failed["marker"],
        failed["marker_raw"],
        failed["authorization"],
        failed["registration"]["record_sha256"],
        _sha(failed["registration_raw"]),
        failed["genesis"],
        failed["genesis_raw"],
        [failed["event_zero"], failed["event_one"]],
        [failed["event_zero_raw"], failed["event_one_raw"]],
        projection,
        projection_raw,
    )
    old_live = authority._LIVE_CUSTODY
    authority._LIVE_CUSTODY = {
        "marker_raw": failed["marker_raw"],
        "marker": failed["marker"],
        "registration_raw": failed["registration_raw"],
        "registration": failed["registration"],
        "authorization_raw": failed["authorization_raw"],
        "authorization": failed["authorization"],
    }
    try:
        authority._validate_local_prechild_failure_publication_prefix(
            failed["marker_raw"],
            failed["marker"],
            failed["registration_raw"],
            failed["registration"],
            failed["authorization"],
            failed["genesis_raw"],
            [failed["event_zero_raw"], failed["event_one_raw"]],
            projection_raw,
            projection,
            result,
        )
    finally:
        authority._LIVE_CUSTODY = old_live


def test_canonical_json_gate_order_is_not_mapping_order_dependent(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, runtime = modules
    failed = _base_chain(contracts, authority, admitted=False)
    parsed = json.loads(failed["event_one_raw"].decode("ascii"))
    gates = parsed["gate_vector"]
    assert tuple(gates) != authority.PRECHILD_GATE_ORDER
    assert set(gates) == set(authority.PRECHILD_GATE_ORDER)
    assert authority._prechild_failure_code(gates) == "V4_SOURCE_CLOSURE"
    assert set(gates) == set(runtime.PRECHILD_GATE_ORDER)


def _passing_observation(
    contracts: types.ModuleType,
    authority: types.ModuleType,
    runtime: types.ModuleType,
    request_raw: bytes,
    request: dict[str, object],
) -> dict[str, object]:
    uid = 12345
    environment = dict(runtime.REQUESTED_ENVIRONMENT)
    environment[runtime.DARWIN_KEY] = "0x%X:0x0:0x0" % uid
    snapshot = {
        "parent_linked_static_closure_exact": True,
        "environment": environment,
        "uid": uid,
        "euid": uid,
        "gid": 12346,
        "egid": 12346,
        "supplemental_root_group_absent": True,
        "process_taint_absent": True,
        "name": "__main__",
        "spec_is_none": True,
        "python_argv": [str(runtime.MODULE_PATH), "--emit-child-observation"],
        "native_argv": [
            "/synthetic/python-app-launcher",
            *runtime.PYTHON_FLAGS,
            str(runtime.MODULE_PATH),
            "--emit-child-observation",
        ],
        "cwd": str(runtime.WORKSPACE_ROOT),
        "implementation": "CPython",
        "version_info": [3, 11, 5],
        "platform": ["Darwin", "arm64"],
        "executable": str(runtime.PYTHON_PATH),
        "executable_realpath": str(runtime.PYTHON_REALPATH),
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
        "hash_probe_sha256": runtime.HASH_PROBE_SHA256,
        "sys_path": list(runtime.EXPECTED_SYS_PATH),
        "site_imported": False,
        "entropy_contacted": False,
        "network_contacted": False,
        "workspace_write_performed": False,
        "temporary_write_performed": False,
        "scientific_import_or_execution_performed": False,
        "darwin_key_removed_from_actual_environment": True,
        "actual_environment_equals_requested16": True,
    }
    observation = runtime.evaluate_snapshot(
        snapshot, _sha(request_raw), request["request_sha256"]
    )
    return contracts.validate_child_observation(observation)


def _admitted_chain(
    contracts: types.ModuleType,
    authority: types.ModuleType,
) -> dict[str, object]:
    chain = _base_chain(contracts, authority, admitted=True)
    request = authority._make_runtime_request(
        contracts,
        chain["marker"],
        chain["registration_raw"],
        chain["authorization_raw"],
        chain["authorization"],
        chain["event_one"],
    )
    request_raw = contracts.canonical_file_bytes(request)
    claim = authority._make_child_claim(
        contracts,
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_one_raw"],
        chain["event_one"],
        request,
    )
    post_admission_failure = authority._make_post_admission_failure(
        contracts,
        "REQUEST_CONSTRUCTION",
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_one_raw"],
        chain["event_one"],
    )
    chain.update(
        {
            "request": request,
            "request_raw": request_raw,
            "child_claim": claim,
            "child_claim_raw": contracts.canonical_file_bytes(claim),
            "post_admission_failure": post_admission_failure,
            "post_admission_failure_raw": contracts.canonical_file_bytes(
                post_admission_failure
            ),
        }
    )
    return chain


def _transport_case(
    case: str,
    request_raw: bytes,
    observation: dict[str, object],
    observation_raw: bytes,
) -> tuple[dict[str, object], bool]:
    transport: dict[str, object] = {
        "child_spawn_succeeded": True,
        "child_stdin_captured_write_byte_count_observed": True,
        "child_stdin_captured_write_byte_count": len(request_raw),
        "child_stdin_request_fully_written": True,
        "child_timeout_observed": False,
        "child_stdout_captured_byte_count_observed": True,
        "child_stdout_captured_byte_count": len(observation_raw),
        "child_stdout_eof_observed": True,
        "child_stdout_overflow_observed": False,
        "child_stderr_captured_byte_count_observed": True,
        "child_stderr_captured_byte_count": 0,
        "child_stderr_eof_observed": True,
        "child_stderr_overflow_observed": False,
        "child_process_reap_observed": True,
        "child_exit_code_observed": True,
        "child_exit_code": 0,
        "child_observation": observation,
    }
    postflight = True
    if case == "PASS":
        return transport, postflight
    if case == "SPAWN":
        transport.update(
            {
                "child_spawn_succeeded": False,
                "child_stdin_captured_write_byte_count_observed": False,
                "child_stdin_captured_write_byte_count": None,
                "child_stdin_request_fully_written": False,
                "child_timeout_observed": False,
                "child_stdout_captured_byte_count_observed": False,
                "child_stdout_captured_byte_count": None,
                "child_stdout_eof_observed": False,
                "child_stderr_captured_byte_count_observed": False,
                "child_stderr_captured_byte_count": None,
                "child_stderr_eof_observed": False,
                "child_process_reap_observed": False,
                "child_exit_code_observed": False,
                "child_exit_code": None,
                "child_observation": None,
            }
        )
    elif case == "STDIN":
        transport["child_stdin_captured_write_byte_count"] = len(request_raw) - 1
        transport["child_stdin_request_fully_written"] = False
        transport["child_observation"] = None
        transport["child_stdout_captured_byte_count"] = 0
    elif case == "TIMEOUT":
        transport["child_timeout_observed"] = True
        transport["child_stdout_captured_byte_count_observed"] = False
        transport["child_stdout_captured_byte_count"] = None
        transport["child_stdout_eof_observed"] = False
        transport["child_stderr_captured_byte_count_observed"] = False
        transport["child_stderr_captured_byte_count"] = None
        transport["child_stderr_eof_observed"] = False
        transport["child_exit_code"] = -9
        transport["child_observation"] = None
    elif case == "STDOUT":
        transport["child_stdout_captured_byte_count"] = 65537
        transport["child_stdout_eof_observed"] = False
        transport["child_stdout_overflow_observed"] = True
        transport["child_exit_code"] = -9
        transport["child_observation"] = None
    elif case == "STDERR":
        transport["child_stderr_captured_byte_count"] = 1
        transport["child_observation"] = None
        transport["child_stdout_captured_byte_count"] = 0
    elif case == "EXIT":
        transport["child_exit_code"] = 3
        transport["child_observation"] = None
        transport["child_stdout_captured_byte_count"] = 0
    elif case == "CONTRACT":
        transport["child_observation"] = None
        transport["child_stdout_captured_byte_count"] = 1
    elif case == "CUSTODY":
        postflight = False
    else:
        raise AssertionError(case)
    return transport, postflight


def _terminal_chain(
    contracts: types.ModuleType,
    authority: types.ModuleType,
    runtime: types.ModuleType,
    case: str,
) -> dict[str, object]:
    chain = _admitted_chain(contracts, authority)
    observation = _passing_observation(
        contracts,
        authority,
        runtime,
        chain["request_raw"],
        chain["request"],
    )
    observation_raw = contracts.canonical_file_bytes(observation)
    transport, postflight = _transport_case(
        case, chain["request_raw"], observation, observation_raw
    )
    terminal = authority._make_terminal_outcome(
        contracts,
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["child_claim_raw"],
        chain["child_claim"],
        transport,
        postflight,
    )
    chain.update(
        {
            "child_observation": observation,
            "transport": transport,
            "event_three": terminal,
            "event_three_raw": contracts.canonical_file_bytes(terminal),
        }
    )
    return chain


def _registered_chain(
    contracts: types.ModuleType,
    authority: types.ModuleType,
    *,
    admitted: bool,
) -> dict[str, object]:
    registration_raw, registration = authority._load_registration()
    authorization_body = authority._authorization_expected_fields()
    authorization_body.update(
        {
            "v4_registration_record_sha256": registration["record_sha256"],
            "v4_registration_raw_sha256": _sha(registration_raw),
        }
    )
    authorization = authority._attach(authorization_body, "record_sha256")
    authorization_raw = _file_bytes(authorization)
    marker = authority._make_marker(
        registration_raw, registration, authorization_raw, authorization
    )
    marker_raw = _file_bytes(marker)
    genesis = authority._make_genesis(
        marker_raw, marker, registration_raw, authorization_raw, authorization
    )
    genesis_raw = _file_bytes(genesis)
    event_zero = authority._make_event_zero(
        marker_raw, marker, registration_raw, genesis_raw, genesis
    )
    event_zero_raw = _file_bytes(event_zero)
    gates = {name: True for name in authority.PRECHILD_GATE_ORDER}
    if not admitted:
        gates["v4_source_closure_exact"] = False
    event_one = authority._make_prechild_event(
        contracts if admitted else None,
        admitted,
        gates,
        marker_raw,
        marker,
        registration_raw,
        event_zero_raw,
        event_zero,
    )
    return {
        "registration": registration,
        "registration_raw": registration_raw,
        "authorization": authorization,
        "authorization_raw": authorization_raw,
        "marker": marker,
        "marker_raw": marker_raw,
        "genesis": genesis,
        "genesis_raw": genesis_raw,
        "event_zero": event_zero,
        "event_zero_raw": event_zero_raw,
        "event_one": event_one,
        "event_one_raw": _file_bytes(event_one),
    }


def _materialize_registered_prefix(
    root: Path,
    authority: types.ModuleType,
    chain: dict[str, object],
    event_raws: list[bytes],
    *,
    terminal_raw: bytes | None = None,
    result_raw: bytes | None = None,
) -> dict[str, Path]:
    root.chmod(0o700)
    paths = authority._operational_paths(root)
    _put(paths["authorization"], chain["authorization_raw"], 0o644)
    _put(paths["marker"], chain["marker_raw"], 0o600)
    for directory in (paths["root"], paths["ledger"], paths["events"]):
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)
    _put(paths["lock"], b"", 0o600)
    _put(paths["genesis"], chain["genesis_raw"], 0o600)
    for ordinal, raw in enumerate(event_raws):
        _put(paths["events"] / f"{ordinal:020d}.json", raw, 0o600)
    if terminal_raw is not None:
        _put(paths["terminal"], terminal_raw, 0o600)
    if result_raw is not None:
        _put(paths["result"], result_raw, 0o644)
    return paths


def _registered_admitted_chain(
    contracts: types.ModuleType,
    authority: types.ModuleType,
    runtime: types.ModuleType,
    terminal_case: str | None = None,
) -> dict[str, object]:
    chain = _registered_chain(contracts, authority, admitted=True)
    request = authority._make_runtime_request(
        contracts,
        chain["marker"],
        chain["registration_raw"],
        chain["authorization_raw"],
        chain["authorization"],
        chain["event_one"],
    )
    claim = authority._make_child_claim(
        contracts,
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_one_raw"],
        chain["event_one"],
        request,
    )
    post_failure = authority._make_post_admission_failure(
        contracts,
        "REQUEST_CONSTRUCTION",
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_one_raw"],
        chain["event_one"],
    )
    request_raw = contracts.canonical_file_bytes(request)
    claim_raw = contracts.canonical_file_bytes(claim)
    chain.update(
        {
            "request": request,
            "request_raw": request_raw,
            "child_claim": claim,
            "child_claim_raw": claim_raw,
            "post_admission_failure": post_failure,
            "post_admission_failure_raw": contracts.canonical_file_bytes(post_failure),
        }
    )
    if terminal_case is not None:
        observation = _passing_observation(
            contracts, authority, runtime, request_raw, request
        )
        transport, postflight = _transport_case(
            terminal_case,
            request_raw,
            observation,
            contracts.canonical_file_bytes(observation),
        )
        event_three = authority._make_terminal_outcome(
            contracts,
            chain["marker_raw"],
            chain["marker"],
            chain["registration_raw"],
            claim_raw,
            claim,
            transport,
            postflight,
        )
        chain["event_three"] = event_three
        chain["event_three_raw"] = contracts.canonical_file_bytes(event_three)
    return chain


def _runtime_claim_fixture(
    root: Path,
    contracts: types.ModuleType,
    authority: types.ModuleType,
    runtime: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, object], dict[str, Path]]:
    root.chmod(0o700)
    module_relative = Path(
        "research/production/finite_association_r1_activation_preparation_"
        "rehearsal_runtime_v4.py"
    )
    machine_relative = Path(
        "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
        "transition_safe_live_host_environment_rehearsal_freeze_v1.json"
    )
    authorization_relative = Path(
        "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
        "execution_authorization_v1.json"
    )
    module_path = root / module_relative
    module_raw = RUNTIME.read_bytes()
    _put(module_path, module_raw, 0o644)
    root_status = root.lstat()
    registration_body = {
        "schema_version": contracts.REGISTRATION_SCHEMA,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "workspace_anchor": {
            "device": root_status.st_dev,
            "inode": root_status.st_ino,
            "type_code": "DIRECTORY",
            "mode_octal": "0700",
            "uid": root_status.st_uid,
            "gid": root_status.st_gid,
        },
        "registration_bindings": [
            {
                "ordinal": 0,
                "role": "ENVIRONMENT_CHILD",
                "path": str(module_relative),
                "raw_sha256": _sha(module_raw),
                "bytes": len(module_raw),
                "mode_octal": "0644",
                "nlink": 1,
            }
        ],
    }
    registration = authority._attach(registration_body, "record_sha256")
    registration_raw = _file_bytes(registration)
    machine_path = root / machine_relative
    _put(machine_path, registration_raw, 0o644)
    authorization_body = authority._authorization_expected_fields()
    authorization_body.update(
        {
            "v4_registration_record_sha256": registration["record_sha256"],
            "v4_registration_raw_sha256": _sha(registration_raw),
        }
    )
    authorization = authority._attach(authorization_body, "record_sha256")
    authorization_raw = _file_bytes(authorization)
    authorization_path = root / authorization_relative
    _put(authorization_path, authorization_raw, 0o644)
    marker = authority._make_marker(
        registration_raw, registration, authorization_raw, authorization
    )
    marker_raw = _file_bytes(marker)
    genesis = authority._make_genesis(
        marker_raw, marker, registration_raw, authorization_raw, authorization
    )
    genesis_raw = _file_bytes(genesis)
    event_zero = authority._make_event_zero(
        marker_raw, marker, registration_raw, genesis_raw, genesis
    )
    event_zero_raw = _file_bytes(event_zero)
    gates = {name: True for name in authority.PRECHILD_GATE_ORDER}
    admission = authority._make_prechild_event(
        contracts,
        True,
        gates,
        marker_raw,
        marker,
        registration_raw,
        event_zero_raw,
        event_zero,
    )
    admission_raw = _file_bytes(admission)
    request = authority._make_runtime_request(
        contracts,
        marker,
        registration_raw,
        authorization_raw,
        authorization,
        admission,
    )
    request_raw = contracts.canonical_file_bytes(request)
    claim = authority._make_child_claim(
        contracts,
        marker_raw,
        marker,
        registration_raw,
        admission_raw,
        admission,
        request,
    )
    claim_raw = contracts.canonical_file_bytes(claim)
    marker_path = root / "artifacts/a1_r1_activation_preparation_v4.attempt.json"
    preparation = root / "artifacts/a1_r1_activation_preparation_v4"
    ledger = preparation / "ledger"
    events = ledger / "events"
    lock = ledger / "writer.lock"
    genesis_path = ledger / "genesis.json"
    terminal = ledger / "terminal.json"
    result = root / (
        "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
        "transition_safe_live_host_environment_rehearsal_result_v1.json"
    )
    _put(marker_path, marker_raw, 0o600)
    for directory in (preparation, ledger, events):
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)
    _put(lock, b"", 0o600)
    _put(genesis_path, genesis_raw, 0o600)
    for ordinal, raw in enumerate((event_zero_raw, admission_raw, claim_raw)):
        _put(events / f"{ordinal:020d}.json", raw, 0o600)
    monkeypatch.setattr(runtime, "WORKSPACE_ROOT", root)
    monkeypatch.setattr(runtime, "MODULE_PATH", module_path)
    monkeypatch.setattr(runtime, "MACHINE_PATH", machine_path)
    monkeypatch.setattr(runtime, "AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(runtime, "MARKER_PATH", marker_path)
    monkeypatch.setattr(runtime, "PREPARATION_ROOT", preparation)
    monkeypatch.setattr(runtime, "LEDGER_PATH", ledger)
    monkeypatch.setattr(runtime, "EVENTS_PATH", events)
    monkeypatch.setattr(runtime, "LOCK_PATH", lock)
    monkeypatch.setattr(runtime, "GENESIS_PATH", genesis_path)
    monkeypatch.setattr(runtime, "TERMINAL_PATH", terminal)
    monkeypatch.setattr(runtime, "RESULT_PATH", result)
    return {
        "registration": registration,
        "registration_raw": registration_raw,
        "authorization": authorization,
        "authorization_raw": authorization_raw,
        "marker": marker,
        "marker_raw": marker_raw,
        "genesis": genesis,
        "genesis_raw": genesis_raw,
        "event_zero": event_zero,
        "event_zero_raw": event_zero_raw,
        "admission": admission,
        "admission_raw": admission_raw,
        "request": request,
        "request_raw": request_raw,
        "claim": claim,
        "claim_raw": claim_raw,
    }, {
        "machine": machine_path,
        "authorization": authorization_path,
        "marker": marker_path,
        "root": preparation,
        "ledger": ledger,
        "events": events,
        "lock": lock,
        "genesis": genesis_path,
        "terminal": terminal,
        "result": result,
        "module": module_path,
    }


def test_truthful_transport_pass_and_hostile_contradictions(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, runtime = modules
    chain = _base_chain(contracts, authority, admitted=True)
    request = authority._make_runtime_request(
        contracts,
        chain["marker"],
        chain["registration_raw"],
        chain["authorization_raw"],
        chain["authorization"],
        chain["event_one"],
    )
    request_raw = contracts.canonical_file_bytes(request)
    claim = authority._make_child_claim(
        contracts,
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_one_raw"],
        chain["event_one"],
        request,
    )
    claim_raw = _file_bytes(claim)
    observation = _passing_observation(
        contracts, authority, runtime, request_raw, request
    )
    observation_raw = contracts.canonical_file_bytes(observation)
    transport = {
        "child_spawn_succeeded": True,
        "child_stdin_captured_write_byte_count_observed": True,
        "child_stdin_captured_write_byte_count": len(request_raw),
        "child_stdin_request_fully_written": True,
        "child_timeout_observed": False,
        "child_stdout_captured_byte_count_observed": True,
        "child_stdout_captured_byte_count": len(observation_raw),
        "child_stdout_eof_observed": True,
        "child_stdout_overflow_observed": False,
        "child_stderr_captured_byte_count_observed": True,
        "child_stderr_captured_byte_count": 0,
        "child_stderr_eof_observed": True,
        "child_stderr_overflow_observed": False,
        "child_process_reap_observed": True,
        "child_exit_code_observed": True,
        "child_exit_code": 0,
        "child_observation": observation,
    }
    terminal = authority._make_terminal_outcome(
        contracts,
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        claim_raw,
        claim,
        transport,
        True,
    )
    assert terminal["outcome"] == "PASS"
    assert terminal["transport_failure_code"] == "NONE"
    contracts.validate_event_chain(
        terminal,
        chain["marker"],
        chain["authorization"],
        chain["registration"]["record_sha256"],
        _sha(chain["registration_raw"]),
        chain["marker_raw"],
        chain["genesis"],
        chain["genesis_raw"],
        claim,
        claim_raw,
    )
    bad = dict(terminal)
    bad["child_process_reap_observed"] = False
    bad["child_exit_code_observed"] = False
    bad["child_exit_code"] = None
    bad["transport_gate_vector"] = dict(bad["transport_gate_vector"])
    bad["transport_gate_vector"]["child_process_reap_observed"] = False
    bad["transport_gate_vector_sha256"] = _sha(_canonical(bad["transport_gate_vector"]))
    bad["transport_failure_code"] = "CHILD_REAP"
    bad["outcome"] = "FAIL"
    bad["terminal_state"] = contracts.FAIL_STATE
    bad.pop("event_sha256")
    bad = contracts.attach_digest(bad, "event_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_terminal_outcome(bad)
    bad_stdin = dict(terminal)
    bad_stdin["child_stdin_captured_write_byte_count"] -= 1
    bad_stdin.pop("event_sha256")
    bad_stdin = contracts.attach_digest(bad_stdin, "event_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_event_chain(
            bad_stdin,
            chain["marker"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["marker_raw"],
            chain["genesis"],
            chain["genesis_raw"],
            claim,
            claim_raw,
        )


def test_runtime_imported_paths_refuse_before_stdin_or_environment_mutation(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contracts, _authority, runtime = modules
    class BombInput:
        @property
        def buffer(self) -> object:
            raise AssertionError("stdin was touched before direct dispatch refusal")
    before = dict(os.environ)
    monkeypatch.setattr(sys, "argv", [str(runtime.MODULE_PATH), "--emit-child-observation"])
    monkeypatch.setattr(sys, "stdin", BombInput())
    assert runtime._canonical_live_dispatch_exact() is False
    assert runtime.main() == 64
    assert dict(os.environ) == before
    assert "build_live_observation" not in runtime.__all__
    assert "live_snapshot" not in runtime.__all__
    assert "main" not in runtime.__all__


def test_runtime_request_rejects_bool_as_ordinal(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, runtime = modules
    chain = _base_chain(contracts, authority, admitted=True)
    request = authority._make_runtime_request(
        contracts,
        chain["marker"],
        chain["registration_raw"],
        chain["authorization_raw"],
        chain["authorization"],
        chain["event_one"],
    )
    bad = dict(request)
    bad["child_launch_ordinal"] = False
    bad.pop("request_sha256")
    bad["request_sha256"] = _sha(_canonical(bad))
    with pytest.raises(runtime.ChildError):
        runtime._parse_request(_file_bytes(bad))


def test_execute_once_imported_route_cannot_write_or_launch(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    _contracts, authority, _runtime = modules
    paths = (
        authority.AUTHORIZATION_PATH,
        authority.MARKER_PATH,
        authority.PREPARATION_ROOT,
        authority.RESULT_PATH,
    )
    before = tuple(authority._lstat(path) for path in paths)
    with pytest.raises(authority.AuthorityError):
        authority.execute_once()
    assert tuple(authority._lstat(path) for path in paths) == before


def test_marker_is_first_operational_action_under_synthetic_spy(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contracts, authority, _runtime = modules
    chain = _base_chain(_contracts, authority, admitted=False)
    calls: list[str] = []
    monkeypatch.setattr(authority, "_dispatch_scope_exact", lambda: True)
    monkeypatch.setattr(
        authority,
        "_load_bootstrap_closure",
        lambda: (
            chain["registration_raw"],
            chain["registration"],
            chain["authorization_raw"],
            chain["authorization"],
        ),
    )
    def stop_at_marker(*_args: object, **_kwargs: object) -> None:
        calls.append("MARKER_RESERVATION")
        raise authority.AuthorityError("synthetic stop")
    monkeypatch.setattr(authority, "_reserve_and_publish_marker", stop_at_marker)
    monkeypatch.setattr(
        authority,
        "_profile_gate_vector",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("profile before marker")),
    )
    with pytest.raises(authority.AuthorityError, match="synthetic stop"):
        authority.execute_once()
    assert calls == ["MARKER_RESERVATION"]


def test_synthetic_status_transitions_without_invalidating_static_freeze(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
) -> None:
    contracts, authority, _runtime = modules
    tmp_path.chmod(0o700)
    capability = authority.SyntheticStateRoot(tmp_path)
    paths = authority._operational_paths(tmp_path)
    registration_raw, registration = authority._load_registration()
    authorization_body = authority._authorization_expected_fields()
    authorization_body.update(
        {
            "v4_registration_record_sha256": registration["record_sha256"],
            "v4_registration_raw_sha256": _sha(registration_raw),
        }
    )
    authorization = authority._attach(authorization_body, "record_sha256")
    authorization_raw = _file_bytes(authorization)
    assert authority.status(capability)["milestone_state"] == authority.STATIC_STATE
    _put(paths["authorization"], authorization_raw, 0o644)
    assert authority.status(capability)["milestone_state"] == authority.AUTH_RECORDED_STATE
    marker = authority._make_marker(
        registration_raw, registration, authorization_raw, authorization
    )
    marker_raw = _file_bytes(marker)
    _put(paths["marker"], marker_raw, 0o600)
    marker_status = authority.status(capability)
    assert marker_status["milestone_state"] == authority.MARKER_FALLBACK_STATE
    assert marker_status["attempt_spent"] is True
    chain = {
        "genesis": authority._make_genesis(
            marker_raw,
            marker,
            registration_raw,
            authorization_raw,
            authorization,
        )
    }
    chain["genesis_raw"] = _file_bytes(chain["genesis"])
    chain["event_zero"] = authority._make_event_zero(
        marker_raw,
        marker,
        registration_raw,
        chain["genesis_raw"],
        chain["genesis"],
    )
    chain["event_zero_raw"] = _file_bytes(chain["event_zero"])
    gates = {name: True for name in authority.PRECHILD_GATE_ORDER}
    gates["v4_source_closure_exact"] = False
    chain["event_one"] = authority._make_prechild_event(
        None,
        False,
        gates,
        marker_raw,
        marker,
        registration_raw,
        chain["event_zero_raw"],
        chain["event_zero"],
    )
    chain["event_one_raw"] = _file_bytes(chain["event_one"])
    _make_operational_fixture(tmp_path, authority, chain)
    _put(paths["events"] / "00000000000000000000.json", chain["event_zero_raw"], 0o600)
    assert authority.status(capability)["milestone_state"] == authority.EVALUATION_FALLBACK_STATE
    _put(paths["events"] / "00000000000000000001.json", chain["event_one_raw"], 0o600)
    event_status = authority.status(capability)
    assert event_status["milestone_state"] == authority.PRECHILD_FAILURE_STATE
    assert event_status["event_count"] == 2
    projection = authority._make_terminal_projection(
        marker_raw,
        marker,
        registration_raw,
        chain["event_one_raw"],
        chain["event_one"],
    )
    projection_raw = _file_bytes(projection)
    _put(paths["terminal"], projection_raw, 0o600)
    assert authority.status(capability)["local_terminal_projection_exact"] is True
    result = authority._make_published_result(
        registration, marker, projection_raw, projection
    )
    _put(paths["result"], _file_bytes(result), 0o644)
    final = authority.status(capability)
    assert final["milestone_state"] == authority.PRECHILD_FAILURE_STATE
    assert final["external_result_exact"] is True
    assert authority._load_registration() == (registration_raw, registration)


def test_synthetic_invalid_extra_and_broken_symlink_fail_closed(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
) -> None:
    _contracts, authority, _runtime = modules
    tmp_path.chmod(0o700)
    capability = authority.SyntheticStateRoot(tmp_path)
    registration_raw, registration = authority._load_registration()
    body = authority._authorization_expected_fields()
    body.update(
        {
            "v4_registration_record_sha256": registration["record_sha256"],
            "v4_registration_raw_sha256": _sha(registration_raw),
        }
    )
    authorization = authority._attach(body, "record_sha256")
    authorization_raw = _file_bytes(authorization)
    paths = authority._operational_paths(tmp_path)
    _put(paths["authorization"], authorization_raw, 0o644)
    marker = authority._make_marker(
        registration_raw, registration, authorization_raw, authorization
    )
    _put(paths["marker"], _file_bytes(marker), 0o600)
    paths["root"].mkdir(parents=True)
    paths["root"].chmod(0o700)
    (paths["root"] / "unexpected").write_bytes(b"x")
    invalid = authority.status(capability)
    assert invalid["milestone_state"] == authority.INVALID_STATE
    assert invalid["marker_self_valid"] is True
    assert invalid["last_valid_prefix_state"] == authority.MARKER_FALLBACK_STATE
    assert invalid["retry_permitted"] is False
    other = tmp_path / "broken_link_case"
    other.mkdir()
    other.chmod(0o700)
    other_capability = authority.SyntheticStateRoot(other)
    other_paths = authority._operational_paths(other)
    _put(other_paths["authorization"], authorization_raw, 0o644)
    other_paths["result"].parent.mkdir(parents=True, exist_ok=True)
    other_paths["result"].symlink_to(other / "missing")
    assert authority.status(other_capability)["milestone_state"] == authority.INVALID_STATE


def test_source_contains_nonblocking_transport_and_reap_before_event3() -> None:
    source = AUTHORITY.read_text("utf-8")
    run_start = source.index("def _run_child_bounded")
    run_end = source.index("def _make_terminal_outcome", run_start)
    transport = source[run_start:run_end]
    assert "os.set_blocking(input_fd, False)" in transport
    assert transport.index("os.set_blocking(input_fd, False)") < transport.index("os.write(")
    assert "child_process_reap_observed" in transport
    assert "except subprocess.TimeoutExpired" in transport
    execute_start = source.index("def execute_once")
    execute = source[execute_start:]
    assert execute.index("child_process_reap_observed") < execute.index("_make_terminal_outcome")
    assert "`Popen` call itself is not" in HUMAN.read_text("utf-8")


def test_privacy_publication_and_focused_cache_hygiene() -> None:
    six = (HUMAN, MACHINE, CONTRACTS, AUTHORITY, RUNTIME, TEST)
    actual_v2_cf_value = b"0x" + b"1F5" + b":0x0:0x0"
    for path in six:
        raw = path.read_bytes()
        assert b"/" + b"Users" + b"/" not in raw
        assert actual_v2_cf_value not in raw
    machine = json.loads(MACHINE.read_text("ascii"))
    assert machine["scope"]["anonymous_or_public_release_permitted"] is False
    assert machine["nonclaims"]["scientific_execution_performed"] is False
    focused = (
        "finite_association_r1_activation_preparation_rehearsal_contracts_v4",
        "finite_association_r1_activation_preparation_rehearsal_authority_v4",
        "finite_association_r1_activation_preparation_rehearsal_runtime_v4",
        "test_manuscript_v3_a1_r1_activation_preparation_v4_transition_safe",
    )
    pycs = [
        path
        for path in ROOT.rglob("*.pyc")
        if any(token in path.name for token in focused)
    ]
    assert pycs == []


def test_all_frozen_contract_prefixes_projections_and_terminal_derivatives(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, runtime = modules
    failed = _base_chain(contracts, authority, admitted=False)
    admitted = _admitted_chain(contracts, authority)
    terminal_fail = _terminal_chain(contracts, authority, runtime, "SPAWN")
    terminal_pass = _terminal_chain(contracts, authority, runtime, "PASS")
    rows = (
        (failed, [], [], authority.MARKER_FALLBACK_STATE, "INCOMPLETE"),
        (
            failed,
            [failed["event_zero"]],
            [failed["event_zero_raw"]],
            authority.EVALUATION_FALLBACK_STATE,
            "INCOMPLETE",
        ),
        (
            failed,
            [failed["event_zero"], failed["event_one"]],
            [failed["event_zero_raw"], failed["event_one_raw"]],
            authority.PRECHILD_FAILURE_STATE,
            "FAIL",
        ),
        (
            admitted,
            [admitted["event_zero"], admitted["event_one"]],
            [admitted["event_zero_raw"], admitted["event_one_raw"]],
            authority.ADMISSION_FALLBACK_STATE,
            "INCOMPLETE",
        ),
        (
            admitted,
            [
                admitted["event_zero"],
                admitted["event_one"],
                admitted["post_admission_failure"],
            ],
            [
                admitted["event_zero_raw"],
                admitted["event_one_raw"],
                admitted["post_admission_failure_raw"],
            ],
            authority.POST_ADMISSION_FAILURE_STATE,
            "FAIL",
        ),
        (
            admitted,
            [
                admitted["event_zero"],
                admitted["event_one"],
                admitted["child_claim"],
            ],
            [
                admitted["event_zero_raw"],
                admitted["event_one_raw"],
                admitted["child_claim_raw"],
            ],
            authority.CHILD_FALLBACK_STATE,
            "INCOMPLETE",
        ),
        (
            terminal_fail,
            [
                terminal_fail["event_zero"],
                terminal_fail["event_one"],
                terminal_fail["child_claim"],
                terminal_fail["event_three"],
            ],
            [
                terminal_fail["event_zero_raw"],
                terminal_fail["event_one_raw"],
                terminal_fail["child_claim_raw"],
                terminal_fail["event_three_raw"],
            ],
            authority.FAIL_STATE,
            "FAIL",
        ),
        (
            terminal_pass,
            [
                terminal_pass["event_zero"],
                terminal_pass["event_one"],
                terminal_pass["child_claim"],
                terminal_pass["event_three"],
            ],
            [
                terminal_pass["event_zero_raw"],
                terminal_pass["event_one_raw"],
                terminal_pass["child_claim_raw"],
                terminal_pass["event_three_raw"],
            ],
            authority.PASS_STATE,
            "PASS",
        ),
    )
    for chain, events, event_raws, state, outcome in rows:
        checked = contracts.validate_full_prefix(
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["genesis"],
            chain["genesis_raw"],
            events,
            event_raws,
        )
        assert checked["event_count"] == len(events)
        assert checked["expected_terminal_state"] == state
        last = events[-1] if events else None
        last_raw = event_raws[-1] if event_raws else None
        projection = authority._make_terminal_projection(
            chain["marker_raw"],
            chain["marker"],
            chain["registration_raw"],
            last_raw,
            last,
        )
        projection_raw = _file_bytes(projection)
        contracts.validate_terminal_projection_against_prefix(
            projection,
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            last,
            last_raw,
        )
        assert projection["terminal_state"] == state
        assert projection["outcome"] == outcome
        if state in {
            authority.PRECHILD_FAILURE_STATE,
            authority.POST_ADMISSION_FAILURE_STATE,
            authority.PASS_STATE,
            authority.FAIL_STATE,
        }:
            result = authority._make_published_result(
                chain["registration"], chain["marker"], projection_raw, projection
            )
            contracts.validate_published_result_against_full_prefix(
                result,
                chain["marker"],
                chain["marker_raw"],
                chain["authorization"],
                chain["registration"]["record_sha256"],
                _sha(chain["registration_raw"]),
                chain["genesis"],
                chain["genesis_raw"],
                events,
                event_raws,
                projection,
                projection_raw,
            )


@pytest.mark.parametrize(
    ("case", "expected_code"),
    (
        ("SPAWN", "CHILD_SPAWN"),
        ("STDIN", "CHILD_STDIN"),
        ("TIMEOUT", "CHILD_TIMEOUT"),
        ("STDOUT", "CHILD_STDOUT"),
        ("STDERR", "CHILD_STDERR"),
        ("EXIT", "CHILD_EXIT"),
        ("CONTRACT", "CHILD_CONTRACT"),
        ("CUSTODY", "POSTFLIGHT_CUSTODY"),
        ("PASS", "NONE"),
    ),
)
def test_transport_failure_priority_is_behaviorally_recomputed(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    case: str,
    expected_code: str,
) -> None:
    contracts, authority, runtime = modules
    chain = _terminal_chain(contracts, authority, runtime, case)
    event = chain["event_three"]
    assert event["transport_failure_code"] == expected_code
    assert event["outcome"] == ("PASS" if case == "PASS" else "FAIL")
    contracts.validate_full_prefix(
        chain["marker"],
        chain["marker_raw"],
        chain["authorization"],
        chain["registration"]["record_sha256"],
        _sha(chain["registration_raw"]),
        chain["genesis"],
        chain["genesis_raw"],
        [
            chain["event_zero"],
            chain["event_one"],
            chain["child_claim"],
            event,
        ],
        [
            chain["event_zero_raw"],
            chain["event_one_raw"],
            chain["child_claim_raw"],
            chain["event_three_raw"],
        ],
    )


def test_spawned_unreaped_child_cannot_be_finalized(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, runtime = modules
    chain = _admitted_chain(contracts, authority)
    observation = _passing_observation(
        contracts, authority, runtime, chain["request_raw"], chain["request"]
    )
    transport, postflight = _transport_case(
        "PASS",
        chain["request_raw"],
        observation,
        contracts.canonical_file_bytes(observation),
    )
    transport["child_process_reap_observed"] = False
    transport["child_exit_code_observed"] = False
    transport["child_exit_code"] = None
    with pytest.raises(authority.AuthorityError, match="reap is unknown"):
        authority._make_terminal_outcome(
            contracts,
            chain["marker_raw"],
            chain["marker"],
            chain["registration_raw"],
            chain["child_claim_raw"],
            chain["child_claim"],
            transport,
            postflight,
        )


def test_execute_once_stops_at_child_claim_when_reap_is_unobserved(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contracts, authority, _runtime = modules
    chain = _admitted_chain(contracts, authority)
    writes: list[tuple[Path, bytes]] = []

    monkeypatch.setattr(authority, "_dispatch_scope_exact", lambda: True)
    monkeypatch.setattr(
        authority,
        "_load_bootstrap_closure",
        lambda: (
            chain["registration_raw"],
            chain["registration"],
            chain["authorization_raw"],
            chain["authorization"],
        ),
    )
    monkeypatch.setattr(authority, "_make_marker", lambda *_args: chain["marker"])
    monkeypatch.setattr(authority, "_reserve_and_publish_marker", lambda *_args: None)
    monkeypatch.setattr(authority, "_mkdir_live", lambda *_args: None)
    monkeypatch.setattr(authority, "_create_lock", lambda: None)
    monkeypatch.setattr(authority, "_make_genesis", lambda *_args: chain["genesis"])
    monkeypatch.setattr(
        authority, "_make_event_zero", lambda *_args: chain["event_zero"]
    )
    monkeypatch.setattr(authority, "_require_pre_genesis_prefix", lambda: None)
    monkeypatch.setattr(authority, "_require_local_prefix", lambda *_a, **_k: None)
    monkeypatch.setattr(
        authority,
        "_write_new_live",
        lambda path, raw: writes.append((path, raw)),
    )
    monkeypatch.setattr(authority, "_load_contracts", lambda: contracts)
    monkeypatch.setattr(
        authority,
        "_profile_gate_vector",
        lambda *_args: {name: True for name in authority.PRECHILD_GATE_ORDER},
    )
    monkeypatch.setattr(
        authority, "_make_prechild_event", lambda *_args: chain["event_one"]
    )
    monkeypatch.setattr(
        authority, "_make_runtime_request", lambda *_args: chain["request"]
    )
    monkeypatch.setattr(
        authority, "_make_child_claim", lambda *_args: chain["child_claim"]
    )
    monkeypatch.setattr(
        authority,
        "_run_child_bounded",
        lambda *_args: {
            "child_spawn_succeeded": True,
            "child_process_reap_observed": False,
        },
    )

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("post-claim effect reached with child reap unobserved")

    monkeypatch.setattr(authority, "_postflight_custody_exact", forbidden)
    monkeypatch.setattr(authority, "_make_terminal_outcome", forbidden)
    monkeypatch.setattr(authority, "_persist_terminal_projection", forbidden)
    monkeypatch.setattr(authority, "_publish_result_live", forbidden)

    with pytest.raises(authority.AuthorityError, match="reap was not directly observed"):
        authority.execute_once()

    assert writes == [
        (authority.GENESIS_PATH, chain["genesis_raw"]),
        (authority._event_path(0), chain["event_zero_raw"]),
        (authority._event_path(1), chain["event_one_raw"]),
        (authority._event_path(2), chain["child_claim_raw"]),
    ]


def test_anchored_record_crosslinks_exact_types_and_promotions_fail_closed(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    contracts, authority, runtime = modules
    chain = _terminal_chain(contracts, authority, runtime, "PASS")

    def redigest(record: dict[str, object], key: str) -> dict[str, object]:
        body = dict(record)
        body.pop(key)
        return contracts.attach_digest(body, key)

    marker = dict(chain["marker"])
    marker["registration_raw_sha256"] = "f" * 64
    marker = redigest(marker, "marker_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_marker(
            marker,
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
        )

    marker_bool = dict(chain["marker"])
    marker_bool["attempt_ordinal"] = False
    marker_bool = redigest(marker_bool, "marker_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_marker(
            marker_bool,
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
        )

    authorization_extra = dict(chain["authorization"])
    authorization_extra["unexpected"] = False
    authorization_extra = redigest(authorization_extra, "record_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_authorization_record(
            authorization_extra,
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
        )

    genesis = dict(chain["genesis"])
    genesis["marker_raw_sha256"] = "e" * 64
    genesis = redigest(genesis, "genesis_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_full_prefix(
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            genesis,
            _file_bytes(genesis),
            [],
            [],
        )

    event_zero = dict(chain["event_zero"])
    event_zero["previous_record_raw_sha256"] = "d" * 64
    event_zero = redigest(event_zero, "event_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_full_prefix(
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["genesis"],
            chain["genesis_raw"],
            [event_zero],
            [_file_bytes(event_zero)],
        )

    event_one = dict(chain["event_one"])
    event_one["attempt_nonce_sha256"] = "c" * 64
    event_one = redigest(event_one, "event_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_full_prefix(
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["genesis"],
            chain["genesis_raw"],
            [chain["event_zero"], event_one],
            [chain["event_zero_raw"], _file_bytes(event_one)],
        )

    claim = dict(chain["child_claim"])
    nested = dict(claim["runtime_request"])
    nested["execution_authorization_raw_sha256"] = "b" * 64
    nested = redigest(nested, "request_sha256")
    nested_raw = contracts.canonical_file_bytes(nested)
    claim["runtime_request"] = nested
    claim["runtime_request_raw_sha256"] = _sha(nested_raw)
    claim["runtime_request_sha256"] = nested["request_sha256"]
    claim = redigest(claim, "event_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_full_prefix(
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["genesis"],
            chain["genesis_raw"],
            [chain["event_zero"], chain["event_one"], claim],
            [chain["event_zero_raw"], chain["event_one_raw"], _file_bytes(claim)],
        )

    terminal = dict(chain["event_three"])
    terminal["previous_record_raw_sha256"] = "a" * 64
    terminal = redigest(terminal, "event_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_full_prefix(
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["genesis"],
            chain["genesis_raw"],
            [
                chain["event_zero"],
                chain["event_one"],
                chain["child_claim"],
                terminal,
            ],
            [
                chain["event_zero_raw"],
                chain["event_one_raw"],
                chain["child_claim_raw"],
                _file_bytes(terminal),
            ],
        )

    events = [
        chain["event_zero"],
        chain["event_one"],
        chain["child_claim"],
        chain["event_three"],
    ]
    raws = [
        chain["event_zero_raw"],
        chain["event_one_raw"],
        chain["child_claim_raw"],
        chain["event_three_raw"],
    ]
    projection = authority._make_terminal_projection(
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_three_raw"],
        chain["event_three"],
    )
    promoted = dict(projection)
    promoted["terminal_state"] = authority.FAIL_STATE
    promoted["outcome"] = "FAIL"
    promoted = redigest(promoted, "terminal_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_full_prefix(
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["genesis"],
            chain["genesis_raw"],
            events,
            raws,
            promoted,
            _file_bytes(promoted),
        )

    projection_raw = _file_bytes(projection)
    result = authority._make_published_result(
        chain["registration"], chain["marker"], projection_raw, projection
    )
    result["local_terminal_raw_sha256"] = "9" * 64
    result = redigest(result, "record_sha256")
    with pytest.raises(contracts.ContractError):
        contracts.validate_published_result_against_full_prefix(
            result,
            chain["marker"],
            chain["marker_raw"],
            chain["authorization"],
            chain["registration"]["record_sha256"],
            _sha(chain["registration_raw"]),
            chain["genesis"],
            chain["genesis_raw"],
            events,
            raws,
            projection,
            projection_raw,
        )


def test_registered_command_and_direct_dispatch_path_forms_agree(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contracts, authority, _runtime = modules
    _raw, machine = _machine_record()
    vector = machine["registered_future_command"]["vector"]
    python_index = vector.index(".venv-m1/bin/python")
    post_environment = vector[python_index:]
    assert post_environment == [
        ".venv-m1/bin/python",
        "-P",
        "-B",
        "-S",
        "-X",
        "utf8",
        str(authority.AUTHORITY_RELATIVE_PATH),
        "--execute-once",
    ]
    monkeypatch.setattr(authority, "__name__", "__main__")
    monkeypatch.setattr(authority, "__spec__", None)
    monkeypatch.setattr(
        authority,
        "_native_argv",
        lambda: (
            "/synthetic/absolute/python-app-launcher",
            *authority.PYTHON_FLAGS,
            str(authority.AUTHORITY_RELATIVE_PATH),
            "--execute-once",
        ),
    )
    monkeypatch.setattr(
        sys, "argv", [str(authority.AUTHORITY_RELATIVE_PATH), "--execute-once"]
    )
    assert authority._dispatch_scope_exact() is True
    exact_native = authority._native_argv
    monkeypatch.setattr(
        authority,
        "_native_argv",
        lambda: (
            "/synthetic/absolute/python-app-launcher",
            "-c",
            str(authority.AUTHORITY_RELATIVE_PATH),
            "--execute-once",
        ),
    )
    assert authority._dispatch_scope_exact() is False
    monkeypatch.setattr(authority, "_native_argv", exact_native)
    monkeypatch.setattr(authority, "__spec__", object())
    assert authority._dispatch_scope_exact() is False
    monkeypatch.setattr(authority, "__spec__", None)
    monkeypatch.setattr(authority, "__name__", "imported_authority")
    assert authority._dispatch_scope_exact() is False
    monkeypatch.setattr(authority, "__name__", "__main__")
    monkeypatch.setattr(sys, "argv", [str(authority.AUTHORITY_PATH), "--execute-once"])
    assert authority._dispatch_scope_exact() is False
    monkeypatch.setattr(
        sys, "argv", [str(authority.AUTHORITY_RELATIVE_PATH), "--execute-once", "extra"]
    )
    assert authority._dispatch_scope_exact() is False
    assert authority.main(["--execute-once"]) == 64
    assert authority.main([]) == 64


def test_machine_v3_four_row_continuity_workspace_and_assent_domain_are_exact() -> None:
    _raw, machine = _machine_record()
    roster = machine["predecessor_v3_terminal_registration"][
        "four_file_binding_roster"
    ]
    assert len(roster) == 4
    assert [row["ordinal"] for row in roster] == [0, 1, 2, 3]
    assert [row["raw_sha256"] for row in roster] == [
        digest for _path, _size, digest in V3_BINDINGS
    ]
    assert [row["bytes"] for row in roster] == [
        size for _path, size, _digest in V3_BINDINGS
    ]
    expected_keys = {
        "ordinal",
        "role",
        "path",
        "raw_sha256",
        "bytes",
        "mode_octal",
        "nlink",
        "is_regular_file",
        "is_symlink",
        "lf_only",
    }
    assert all(set(row) == expected_keys for row in roster)
    assert machine["workspace_anchor"]["type_code"] == "DIRECTORY"
    provenance = machine["static_freeze_authorization_provenance"]
    domain = bytes.fromhex(provenance["normalized_visible_assent_domain_hex"])
    assert domain.endswith(b"\0")
    assert _sha(
        domain + provenance["normalized_visible_assent_text"].encode("utf-8")
    ) == provenance["normalized_visible_assent_domain_separated_sha256"]


def test_status_materializes_every_event_prefix_and_terminal_adjunct(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
) -> None:
    contracts, authority, runtime = modules
    failed = _registered_chain(contracts, authority, admitted=False)
    admitted = _registered_admitted_chain(contracts, authority, runtime)
    terminal_fail = _registered_admitted_chain(
        contracts, authority, runtime, "SPAWN"
    )
    terminal_pass = _registered_admitted_chain(
        contracts, authority, runtime, "PASS"
    )
    cases = (
        ("marker", failed, [], authority.MARKER_FALLBACK_STATE),
        (
            "event0",
            failed,
            [failed["event_zero_raw"]],
            authority.EVALUATION_FALLBACK_STATE,
        ),
        (
            "prechild_fail",
            failed,
            [failed["event_zero_raw"], failed["event_one_raw"]],
            authority.PRECHILD_FAILURE_STATE,
        ),
        (
            "admission",
            admitted,
            [admitted["event_zero_raw"], admitted["event_one_raw"]],
            authority.ADMISSION_FALLBACK_STATE,
        ),
        (
            "post_admission_fail",
            admitted,
            [
                admitted["event_zero_raw"],
                admitted["event_one_raw"],
                admitted["post_admission_failure_raw"],
            ],
            authority.POST_ADMISSION_FAILURE_STATE,
        ),
        (
            "child_claim",
            admitted,
            [
                admitted["event_zero_raw"],
                admitted["event_one_raw"],
                admitted["child_claim_raw"],
            ],
            authority.CHILD_FALLBACK_STATE,
        ),
        (
            "event3_fail",
            terminal_fail,
            [
                terminal_fail["event_zero_raw"],
                terminal_fail["event_one_raw"],
                terminal_fail["child_claim_raw"],
                terminal_fail["event_three_raw"],
            ],
            authority.FAIL_STATE,
        ),
        (
            "event3_pass",
            terminal_pass,
            [
                terminal_pass["event_zero_raw"],
                terminal_pass["event_one_raw"],
                terminal_pass["child_claim_raw"],
                terminal_pass["event_three_raw"],
            ],
            authority.PASS_STATE,
        ),
    )
    for name, chain, event_raws, expected_state in cases:
        root = tmp_path / name
        root.mkdir()
        root.chmod(0o700)
        _materialize_registered_prefix(root, authority, chain, list(event_raws))
        capability = authority.SyntheticStateRoot(root)
        status = authority.status(capability)
        assert status["milestone_state"] == expected_state
        assert status["event_count"] == len(event_raws)
        assert status["attempt_spent"] is True
        assert status["retry_permitted"] is False

        last = None
        last_raw = None
        if event_raws:
            last_raw = event_raws[-1]
            last = json.loads(last_raw.decode("ascii"))
        if expected_state in {
            authority.PRECHILD_FAILURE_STATE,
            authority.POST_ADMISSION_FAILURE_STATE,
            authority.FAIL_STATE,
            authority.PASS_STATE,
        }:
            projection = authority._make_terminal_projection(
                chain["marker_raw"],
                chain["marker"],
                chain["registration_raw"],
                last_raw,
                last,
            )
            projection_raw = _file_bytes(projection)
            result = authority._make_published_result(
                chain["registration"], chain["marker"], projection_raw, projection
            )
            paths = authority._operational_paths(root)
            _put(paths["terminal"], projection_raw, 0o600)
            status = authority.status(capability)
            assert status["milestone_state"] == expected_state
            assert status["local_terminal_projection_exact"] is True
            assert status["external_result_present"] is False
            _put(paths["result"], _file_bytes(result), 0o644)
            status = authority.status(capability)
            assert status["milestone_state"] == expected_state
            assert status["local_terminal_projection_exact"] is True
            assert status["external_result_exact"] is True


@pytest.mark.parametrize("valid_count", (0, 1, 2, 3))
def test_status_preserves_longest_valid_prefix_before_invalid_trailing_record(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
    valid_count: int,
) -> None:
    contracts, authority, runtime = modules
    chain = _registered_admitted_chain(contracts, authority, runtime)
    valid = [
        chain["event_zero_raw"],
        chain["event_one_raw"],
        chain["child_claim_raw"],
    ][:valid_count]
    root = tmp_path / f"trailing_{valid_count}"
    root.mkdir()
    root.chmod(0o700)
    paths = _materialize_registered_prefix(root, authority, chain, valid)
    _put(paths["events"] / f"{valid_count:020d}.json", b"{\n", 0o600)
    status = authority.status(authority.SyntheticStateRoot(root))
    expected_prefix_state = (
        authority.MARKER_FALLBACK_STATE,
        authority.EVALUATION_FALLBACK_STATE,
        authority.ADMISSION_FALLBACK_STATE,
        authority.CHILD_FALLBACK_STATE,
    )[valid_count]
    assert status["event_count"] == valid_count
    assert status["last_valid_prefix_state"] == expected_prefix_state
    assert status["marker_self_valid"] is True
    assert status["trailing_record_invalid_or_incomplete_event_ordinal"] == valid_count
    assert status["trailing_record_cause_unobserved"] is True
    assert status["retry_permitted"] is False


@pytest.mark.parametrize("valid_count", (0, 1, 2, 3))
def test_status_rejects_canonical_invalid_event_but_retains_proven_prefix(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
    valid_count: int,
) -> None:
    contracts, authority, runtime = modules
    chain = _registered_admitted_chain(contracts, authority, runtime, "PASS")
    complete = [
        chain["event_zero_raw"],
        chain["event_one_raw"],
        chain["child_claim_raw"],
        chain["event_three_raw"],
    ]
    root = tmp_path / f"canonical_invalid_{valid_count}"
    root.mkdir()
    root.chmod(0o700)
    paths = _materialize_registered_prefix(
        root, authority, chain, complete[:valid_count]
    )
    invalid_event = json.loads(complete[valid_count].decode("ascii"))
    invalid_event["previous_record_raw_sha256"] = "f" * 64
    invalid_event.pop("event_sha256")
    invalid_event = authority._attach(invalid_event, "event_sha256")
    _put(
        paths["events"] / f"{valid_count:020d}.json",
        _file_bytes(invalid_event),
        0o600,
    )

    status = authority.status(authority.SyntheticStateRoot(root))
    expected_prefix_state = (
        authority.MARKER_FALLBACK_STATE,
        authority.EVALUATION_FALLBACK_STATE,
        authority.ADMISSION_FALLBACK_STATE,
        authority.CHILD_FALLBACK_STATE,
    )[valid_count]
    assert status["milestone_state"] == authority.INVALID_STATE
    assert status["invalid_reason_code"] == "LEDGER_CLOSED_WORLD_INVALID"
    assert status["event_count"] == valid_count
    assert status["last_valid_prefix_state"] == expected_prefix_state
    assert status["trailing_record_invalid_or_incomplete_kind"] is None
    assert status["trailing_record_cause_unobserved"] is False
    assert status["attempt_spent"] is True
    assert status["retry_permitted"] is False


@pytest.mark.parametrize("corrupt", ("terminal", "result", "result_without_terminal"))
def test_status_adjunct_corruption_never_erases_authoritative_event_state(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
    corrupt: str,
) -> None:
    contracts, authority, runtime = modules
    chain = _registered_admitted_chain(contracts, authority, runtime, "PASS")
    raws = [
        chain["event_zero_raw"],
        chain["event_one_raw"],
        chain["child_claim_raw"],
        chain["event_three_raw"],
    ]
    root = tmp_path / corrupt
    root.mkdir()
    root.chmod(0o700)
    paths = _materialize_registered_prefix(root, authority, chain, raws)
    projection = authority._make_terminal_projection(
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_three_raw"],
        chain["event_three"],
    )
    projection_raw = _file_bytes(projection)
    result = authority._make_published_result(
        chain["registration"], chain["marker"], projection_raw, projection
    )
    if corrupt == "terminal":
        _put(paths["terminal"], b"{\n", 0o600)
    elif corrupt == "result":
        _put(paths["terminal"], projection_raw, 0o600)
        _put(paths["result"], b"{\n", 0o644)
    else:
        _put(paths["result"], _file_bytes(result), 0o644)
    status = authority.status(authority.SyntheticStateRoot(root))
    assert status["milestone_state"] == authority.PASS_STATE
    assert status["event_count"] == 4
    assert status["last_valid_prefix_state"] == authority.PASS_STATE
    assert status["retry_permitted"] is False
    if corrupt == "terminal":
        assert status["local_terminal_projection_exact"] is False
    else:
        assert status["external_result_exact"] is False
    assert status["adjunct_error_code"] is not None


def test_synthetic_closed_world_modes_links_gaps_and_extras_fail_closed(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
) -> None:
    contracts, authority, _runtime = modules
    chain = _registered_chain(contracts, authority, admitted=False)
    base_raws = [chain["event_zero_raw"], chain["event_one_raw"]]

    def build(name: str, raws: list[bytes] | None = None) -> tuple[Path, dict[str, Path]]:
        root = tmp_path / name
        root.mkdir()
        root.chmod(0o700)
        paths = _materialize_registered_prefix(
            root, authority, chain, list(base_raws if raws is None else raws)
        )
        return root, paths

    cases: list[tuple[str, object]] = []
    root, paths = build("marker_mode")
    paths["marker"].chmod(0o644)
    cases.append(("marker_mode", root))

    root, paths = build("lock_nonempty")
    paths["lock"].write_bytes(b"x")
    cases.append(("lock_nonempty", root))

    root, paths = build("genesis_hardlink")
    os.link(paths["genesis"], tmp_path / "genesis_second_link")
    cases.append(("genesis_hardlink", root))

    root, paths = build("event_symlink", [])
    target = tmp_path / "event0_target.json"
    _put(target, chain["event_zero_raw"], 0o600)
    (paths["events"] / "00000000000000000000.json").symlink_to(target)
    cases.append(("event_symlink", root))

    root, paths = build("ledger_mode")
    paths["ledger"].chmod(0o755)
    cases.append(("ledger_mode", root))

    root, paths = build("preparation_extra")
    (paths["root"] / "unexpected").write_bytes(b"x")
    cases.append(("preparation_extra", root))

    root, paths = build("event_extra")
    _put(paths["events"] / "00000000000000000004.json", b"{}\n", 0o600)
    cases.append(("event_extra", root))

    root, paths = build("event_gap", [])
    _put(paths["events"] / "00000000000000000001.json", chain["event_one_raw"], 0o600)
    cases.append(("event_gap", root))

    for name, root_value in cases:
        status = authority.status(authority.SyntheticStateRoot(root_value))
        assert status["milestone_state"] == authority.INVALID_STATE, name
        assert status["attempt_spent"] is True, name
        assert status["retry_permitted"] is False, name

    root, paths = build("terminal_wrong_mode")
    projection = authority._make_terminal_projection(
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["event_one_raw"],
        chain["event_one"],
    )
    projection_raw = _file_bytes(projection)
    _put(paths["terminal"], projection_raw, 0o644)
    status = authority.status(authority.SyntheticStateRoot(root))
    assert status["milestone_state"] == authority.PRECHILD_FAILURE_STATE
    assert status["local_terminal_projection_exact"] is False
    assert status["retry_permitted"] is False

    root, paths = build("result_hardlink")
    _put(paths["terminal"], projection_raw, 0o600)
    result = authority._make_published_result(
        chain["registration"], chain["marker"], projection_raw, projection
    )
    _put(paths["result"], _file_bytes(result), 0o644)
    os.link(paths["result"], tmp_path / "result_second_link")
    status = authority.status(authority.SyntheticStateRoot(root))
    assert status["milestone_state"] == authority.PRECHILD_FAILURE_STATE
    assert status["external_result_exact"] is False
    assert status["retry_permitted"] is False


def test_preauth_status_does_not_evaluate_source_profile_or_predecessor(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contracts, authority, _runtime = modules
    registration_raw, registration = authority._load_registration()
    authorization_body = authority._authorization_expected_fields()
    authorization_body.update(
        {
            "v4_registration_record_sha256": registration["record_sha256"],
            "v4_registration_raw_sha256": _sha(registration_raw),
        }
    )
    authorization = authority._attach(authorization_body, "record_sha256")
    authorization_raw = _file_bytes(authorization)
    bomb = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("preauth operational evaluation")
    )
    monkeypatch.setattr(authority, "_audit_v4_source_closure", bomb)
    monkeypatch.setattr(authority, "_audit_v3_terminal", bomb)
    monkeypatch.setattr(authority, "_profile_gate_vector", bomb)
    monkeypatch.setattr(authority, "_load_contracts", bomb)

    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    empty_root.chmod(0o700)
    static = authority.status(authority.SyntheticStateRoot(empty_root))
    assert static["milestone_state"] == authority.STATIC_STATE
    assert static["source_closure_evaluated_by_status"] is False
    assert static["prechild_admission_ready_claimed"] is False

    auth_root = tmp_path / "auth"
    auth_root.mkdir()
    auth_root.chmod(0o700)
    paths = authority._operational_paths(auth_root)
    _put(paths["authorization"], authorization_raw, 0o644)
    authorized = authority.status(authority.SyntheticStateRoot(auth_root))
    assert authorized["milestone_state"] == authority.AUTH_RECORDED_STATE
    assert authorized["live_rehearsal_authorized_by_certificate"] is True
    assert authorized["source_closure_evaluated_by_status"] is False
    assert authorized["prechild_admission_ready_claimed"] is False


def test_contracts_unavailable_controlled_failure_still_persists_and_publishes(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contracts, authority, _runtime = modules
    chain = _base_chain(contracts, authority, admitted=False)
    old_live = authority._LIVE_CUSTODY
    authority._LIVE_CUSTODY = {
        "marker_raw": chain["marker_raw"],
        "marker": chain["marker"],
        "registration_raw": chain["registration_raw"],
        "registration": chain["registration"],
        "authorization_raw": chain["authorization_raw"],
        "authorization": chain["authorization"],
    }
    writes: list[tuple[str, bytes]] = []
    storage: dict[Path, bytes] = {}

    def write_new(path: Path, raw: bytes) -> None:
        assert path == authority.TERMINAL_PATH
        assert path not in storage
        storage[path] = raw
        writes.append(("terminal", raw))

    def stable_read(path: Path, _mode: int, **_kwargs: object) -> bytes:
        return storage[path]

    def publish(
        raw: bytes,
        _genesis_raw: bytes,
        _event_raws: object,
        terminal_raw: bytes,
    ) -> bytes:
        assert storage[authority.TERMINAL_PATH] == terminal_raw
        writes.append(("result", raw))
        return raw

    monkeypatch.setattr(authority, "_require_local_prefix", lambda *_a, **_k: None)
    monkeypatch.setattr(authority, "_write_new_live", write_new)
    monkeypatch.setattr(authority, "_stable_read", stable_read)
    monkeypatch.setattr(authority, "_publish_result_live", publish)
    try:
        result = authority._persist_terminal_projection(
            None,
            chain["marker_raw"],
            chain["marker"],
            chain["registration_raw"],
            chain["registration"],
            chain["authorization"],
            chain["genesis_raw"],
            [chain["event_zero_raw"], chain["event_one_raw"]],
            chain["event_one"],
        )
        assert [kind for kind, _raw in writes] == ["terminal", "result"]
        assert _file_bytes(result) == writes[1][1]
        assert result["terminal_state"] == authority.PRECHILD_FAILURE_STATE

        projection_raw = writes[0][1]
        projection = json.loads(projection_raw.decode("ascii"))
        with pytest.raises(authority.AuthorityError):
            authority._validate_local_prechild_failure_publication_prefix(
                chain["marker_raw"],
                chain["marker"],
                chain["registration_raw"],
                chain["registration"],
                chain["authorization"],
                chain["genesis_raw"],
                [chain["event_zero_raw"]],
                projection_raw,
                projection,
                result,
            )
        admitted = _base_chain(contracts, authority, admitted=True)
        admitted_projection = authority._make_terminal_projection(
            admitted["marker_raw"],
            admitted["marker"],
            admitted["registration_raw"],
            admitted["event_one_raw"],
            admitted["event_one"],
        )
        admitted_projection_raw = _file_bytes(admitted_projection)
        admitted_result = authority._make_published_result(
            admitted["registration"],
            admitted["marker"],
            admitted_projection_raw,
            admitted_projection,
        )
        with pytest.raises(authority.AuthorityError):
            authority._validate_local_prechild_failure_publication_prefix(
                admitted["marker_raw"],
                admitted["marker"],
                admitted["registration_raw"],
                admitted["registration"],
                admitted["authorization"],
                admitted["genesis_raw"],
                [admitted["event_zero_raw"], admitted["event_one_raw"]],
                admitted_projection_raw,
                admitted_projection,
                admitted_result,
            )
    finally:
        authority._LIVE_CUSTODY = old_live


def test_result_publication_is_o_excl_prefix_rechecked_and_no_clobber(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contracts, authority, _runtime = modules
    root = tmp_path / "publication"
    result_parent = root / "research" / "fixtures"
    result_parent.mkdir(parents=True)
    root.chmod(0o700)
    result_parent.parent.chmod(0o700)
    result_parent.chmod(0o700)
    result_path = result_parent / "result.json"
    monkeypatch.setattr(authority, "WORKSPACE_ROOT", root)
    monkeypatch.setattr(authority, "RESULT_PATH", result_path)
    monkeypatch.setattr(authority, "_require_live_write_scope", lambda **_kwargs: None)
    checks: list[tuple[bytes, tuple[bytes, ...], bytes | None, bytes | None]] = []

    def prefix(
        genesis_raw: bytes,
        event_raws: object,
        terminal_raw: bytes | None = None,
        result_raw: bytes | None = None,
    ) -> None:
        checks.append((genesis_raw, tuple(event_raws), terminal_raw, result_raw))

    monkeypatch.setattr(authority, "_require_local_prefix", prefix)
    result_raw = b'{"privacy_safe":true}\n'
    terminal_raw = b'{"terminal":true}\n'
    reopened = authority._publish_result_live(
        result_raw, b"genesis\n", [b"event0\n", b"event1\n"], terminal_raw
    )
    assert reopened == result_raw
    assert result_path.read_bytes() == result_raw
    status = result_path.lstat()
    assert stat.S_IMODE(status.st_mode) == 0o644 and status.st_nlink == 1
    assert len(checks) == 3
    assert checks[0][2] == terminal_raw and checks[0][3] is None
    assert checks[1][2] == terminal_raw and checks[1][3] == b""
    assert checks[2][2] == terminal_raw and checks[2][3] == result_raw

    output = io.BytesIO()
    monkeypatch.setattr(
        authority.sys, "stdout", types.SimpleNamespace(buffer=output)
    )
    monkeypatch.setattr(authority.sys, "argv", ["authority", "--execute-once"])
    monkeypatch.setattr(
        authority, "execute_once", lambda: json.loads(reopened.decode("ascii"))
    )
    assert authority.main() == 0
    assert output.getvalue() == reopened

    with pytest.raises(authority.AuthorityError, match="not pristine"):
        authority._publish_result_live(
            b"replacement\n", b"genesis\n", [b"event0\n"], terminal_raw
        )
    assert result_path.read_bytes() == result_raw

    race_path = result_parent / "race.json"
    monkeypatch.setattr(authority, "RESULT_PATH", race_path)
    real_open = os.open
    injected = {"done": False}

    def race_open(path: str, flags: int, mode: int = 0o777) -> int:
        if Path(path) == race_path and flags & os.O_EXCL and not injected["done"]:
            injected["done"] = True
            descriptor = real_open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            os.write(descriptor, b"racer\n")
            os.close(descriptor)
        return real_open(path, flags, mode)

    monkeypatch.setattr(authority.os, "open", race_open)
    with pytest.raises(FileExistsError):
        authority._publish_result_live(
            result_raw, b"genesis\n", [b"event0\n"], terminal_raw
        )
    assert race_path.read_bytes() == b"racer\n"

    swap_path = result_parent / "swap.json"
    monkeypatch.setattr(authority, "RESULT_PATH", swap_path)
    monkeypatch.setattr(authority.os, "open", real_open)
    swap_checks = {"count": 0}

    def swap_after_reservation(
        _genesis_raw: bytes,
        _event_raws: object,
        terminal_raw: bytes | None = None,
        result_raw: bytes | None = None,
    ) -> None:
        assert terminal_raw is not None
        swap_checks["count"] += 1
        if result_raw == b"":
            swap_path.unlink()
            descriptor = real_open(
                swap_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o644,
            )
            os.write(descriptor, b"foreign\n")
            os.close(descriptor)

    monkeypatch.setattr(authority, "_require_local_prefix", swap_after_reservation)
    with pytest.raises(authority.AuthorityError, match="publication custody invalid"):
        authority._publish_result_live(
            result_raw, b"genesis\n", [b"event0\n"], terminal_raw
        )
    assert swap_checks["count"] == 2
    assert swap_path.read_bytes() == b"foreign\n"

    failed_write_path = result_parent / "failed-write.json"
    monkeypatch.setattr(authority, "RESULT_PATH", failed_write_path)
    monkeypatch.setattr(authority, "_require_local_prefix", lambda *_a, **_k: None)
    monkeypatch.setattr(authority.os, "open", real_open)
    monkeypatch.setattr(authority.os, "write", lambda *_args: 0)
    with pytest.raises(authority.AuthorityError, match="short external result write"):
        authority._publish_result_live(
            result_raw, b"genesis\n", [b"event0\n"], terminal_raw
        )
    assert failed_write_path.read_bytes() == b""
    assert stat.S_IMODE(failed_write_path.lstat().st_mode) == 0o644


def test_terminal_projection_failure_prevents_result_publication_and_stdout_is_exact(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contracts, authority, _runtime = modules
    published: list[bytes] = []
    monkeypatch.setattr(
        authority,
        "_write_new_live",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            authority.AuthorityError("synthetic terminal O_EXCL failure")
        ),
    )
    monkeypatch.setattr(
        authority,
        "_publish_result_live",
        lambda raw, *_args, **_kwargs: published.append(raw),
    )
    monkeypatch.setattr(authority, "_require_local_prefix", lambda *_a, **_k: None)
    chain = _base_chain(_contracts, authority, admitted=False)
    with pytest.raises(authority.AuthorityError, match="terminal O_EXCL"):
        authority._persist_terminal_projection(
            None,
            chain["marker_raw"],
            chain["marker"],
            chain["registration_raw"],
            chain["registration"],
            chain["authorization"],
            chain["genesis_raw"],
            [chain["event_zero_raw"], chain["event_one_raw"]],
            chain["event_one"],
        )
    assert published == []

    persisted = {"privacy_safe": True}
    output = io.BytesIO()
    fake_stdout = types.SimpleNamespace(buffer=output)
    monkeypatch.setattr(authority, "execute_once", lambda: persisted)
    monkeypatch.setattr(authority.sys, "stdout", fake_stdout)
    monkeypatch.setattr(authority.sys, "argv", ["authority", "--execute-once"])
    monkeypatch.setattr(authority, "__name__", "__main__")
    assert authority.main() == 0
    assert output.getvalue() == _file_bytes(persisted)


@pytest.mark.parametrize(
    ("scenario", "expected_code"),
    (
        ("spawn", "CHILD_SPAWN"),
        ("pass", "NONE"),
        ("partial_stdin", "CHILD_STDIN"),
        ("timeout", "CHILD_TIMEOUT"),
        ("stdout_overflow", "CHILD_STDOUT"),
        ("stderr_nonempty", "CHILD_STDERR"),
        ("stderr_overflow", "CHILD_STDERR"),
        ("exit_nonzero", "CHILD_EXIT"),
        ("malformed_stdout", "CHILD_CONTRACT"),
        ("child_fail", "NONE"),
    ),
)
def test_bounded_runner_fake_process_exercises_transport_without_real_child(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    expected_code: str,
) -> None:
    import selectors
    import subprocess
    import time

    contracts, authority, runtime = modules
    chain = _admitted_chain(contracts, authority)
    observation = _passing_observation(
        contracts, authority, runtime, chain["request_raw"], chain["request"]
    )
    expected_observation = observation
    observation_raw = contracts.canonical_file_bytes(observation)
    stdout_data = observation_raw
    stderr_data = b""
    if scenario == "stdout_overflow":
        stdout_data = b"x" * 65537
    elif scenario == "stderr_nonempty":
        stderr_data = b"x"
    elif scenario == "stderr_overflow":
        stderr_data = b"x" * 4097
    elif scenario == "malformed_stdout":
        stdout_data = b"not-json\n"
    elif scenario == "child_fail":
        failed = dict(observation)
        gates = dict(failed["gate_vector"])
        gates["parent_linked_static_closure_exact"] = False
        failed["gate_vector"] = gates
        failed["gate_vector_sha256"] = _sha(_canonical(gates))
        failed["failure_code"] = "REQUEST"
        failed["outcome"] = "FAIL"
        failed.pop("observation_sha256")
        expected_observation = authority._attach(failed, "observation_sha256")
        expected_observation = contracts.validate_child_observation(
            expected_observation
        )
        stdout_data = contracts.canonical_file_bytes(expected_observation)

    class Stream:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor
            self.closed = False

        def fileno(self) -> int:
            return self.descriptor

        def close(self) -> None:
            self.closed = True

    class Process:
        def __init__(self) -> None:
            self.stdin = Stream(10)
            self.stdout = Stream(11)
            self.stderr = Stream(12)
            self.pid = 4242
            self.reaped = False
            self.killed = False

        def poll(self) -> int | None:
            return (-9 if self.killed else 0) if self.reaped else None

        def kill(self) -> None:
            self.killed = True

        def wait(self, timeout: float) -> int:
            assert timeout >= 0
            self.reaped = True
            if scenario == "timeout" or self.killed:
                return -9
            if scenario == "exit_nonzero":
                return 3
            return 0

    class Selector:
        def __init__(self) -> None:
            self.entries: dict[int, types.SimpleNamespace] = {}

        def register(self, value: object, _mask: int, data: object) -> None:
            descriptor = value if type(value) is int else value.fileno()
            self.entries[descriptor] = types.SimpleNamespace(fd=descriptor, data=data)

        def unregister(self, value: object) -> None:
            descriptor = value if type(value) is int else value.fileno()
            self.entries.pop(descriptor, None)

        def get_map(self) -> dict[int, types.SimpleNamespace]:
            return dict(self.entries)

        def select(self, _timeout: float) -> list[tuple[types.SimpleNamespace, int]]:
            if scenario == "stderr_overflow":
                for descriptor in (10, 11, 12):
                    if descriptor in self.entries:
                        return [(self.entries[descriptor], 1)]
            return [(entry, 1) for entry in list(self.entries.values())]

        def close(self) -> None:
            self.entries.clear()

    process = Process()
    popen_calls: list[tuple[object, dict[str, object]]] = []

    def popen(command: object, **kwargs: object) -> Process:
        popen_calls.append((command, kwargs))
        if scenario == "spawn":
            raise OSError("synthetic spawn failure")
        return process

    offsets = {11: 0, 12: 0}
    payloads = {11: stdout_data, 12: stderr_data}
    stdin_calls = {"count": 0}

    def write(descriptor: int, payload: bytes) -> int:
        assert descriptor == 10
        stdin_calls["count"] += 1
        if scenario == "partial_stdin":
            if stdin_calls["count"] == 1:
                return max(1, len(payload) // 2)
            raise BrokenPipeError
        return len(payload)

    def read(descriptor: int, maximum: int) -> bytes:
        payload = payloads[descriptor]
        start = offsets[descriptor]
        chunk = payload[start : start + maximum]
        offsets[descriptor] += len(chunk)
        return chunk

    clock = {"value": 0.0, "calls": 0}

    def monotonic() -> float:
        clock["calls"] += 1
        if scenario == "timeout" and clock["calls"] > 2:
            return 100.0
        clock["value"] += 0.01
        return clock["value"]

    monkeypatch.setattr(authority, "_postflight_custody_exact", lambda *_a, **_k: True)
    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(selectors, "DefaultSelector", Selector)
    monkeypatch.setattr(time, "monotonic", monotonic)
    monkeypatch.setattr(authority.os, "set_blocking", lambda *_args: None)
    monkeypatch.setattr(authority.os, "write", write)
    monkeypatch.setattr(authority.os, "read", read)
    monkeypatch.setattr(authority.os, "killpg", lambda *_args: process.kill())
    transport = authority._run_child_bounded(
        contracts,
        chain["request_raw"],
        chain["genesis_raw"],
        [chain["event_zero_raw"], chain["event_one_raw"], chain["child_claim_raw"]],
        chain["registration_raw"],
        chain["registration"],
    )
    assert len(popen_calls) == 1
    if scenario != "spawn":
        command, kwargs = popen_calls[0]
        assert command == [
            str(authority.PYTHON_PATH),
            *authority.PYTHON_FLAGS,
            str(authority.RUNTIME_PATH),
            "--emit-child-observation",
        ]
        assert kwargs["cwd"] == str(authority.WORKSPACE_ROOT)
        assert kwargs["env"] == authority.REQUESTED_ENVIRONMENT
        assert kwargs["start_new_session"] is True
    if scenario in {"pass", "child_fail"}:
        assert transport["child_observation"] == expected_observation
    else:
        assert transport["child_observation"] is None
    if scenario in {"stdout_overflow", "stderr_overflow"}:
        stream = "stdout" if scenario == "stdout_overflow" else "stderr"
        maximum = (
            authority.MAX_STDOUT_BYTES
            if stream == "stdout"
            else authority.MAX_STDERR_BYTES
        )
        assert transport[f"child_{stream}_captured_byte_count_observed"] is True
        assert transport[f"child_{stream}_captured_byte_count"] == maximum + 1
        assert transport[f"child_{stream}_overflow_observed"] is True
        assert transport[f"child_{stream}_eof_observed"] is False
    terminal = authority._make_terminal_outcome(
        contracts,
        chain["marker_raw"],
        chain["marker"],
        chain["registration_raw"],
        chain["child_claim_raw"],
        chain["child_claim"],
        transport,
        True,
    )
    assert terminal["transport_failure_code"] == expected_code
    assert terminal["outcome"] == ("PASS" if scenario == "pass" else "FAIL")
    if scenario in {"stdout_overflow", "stderr_overflow"}:
        stream = "stdout" if scenario == "stdout_overflow" else "stderr"
        maximum = (
            authority.MAX_STDOUT_BYTES
            if stream == "stdout"
            else authority.MAX_STDERR_BYTES
        )
        assert terminal[f"child_{stream}_captured_byte_count_observed"] is True
        assert terminal[f"child_{stream}_captured_byte_count"] == maximum + 1
        assert terminal[f"child_{stream}_overflow_observed"] is True
        assert terminal[f"child_{stream}_eof_observed"] is False
    assert terminal["raw_child_transport_persisted"] is False
    assert not any(
        isinstance(value, (bytes, bytearray)) for value in terminal.values()
    )


def test_bounded_runner_reap_error_preserves_child_claim_fallback(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    contracts, authority, _runtime = modules
    chain = _admitted_chain(contracts, authority)

    class Stream:
        def fileno(self) -> int:
            return 10

        def close(self) -> None:
            pass

    class Process:
        stdin = Stream()
        stdout = None
        stderr = None
        pid = 4343

        def poll(self) -> None:
            return None

        def kill(self) -> None:
            pass

        def wait(self, timeout: float) -> int:
            raise OSError("synthetic unknown reap")

    monkeypatch.setattr(authority, "_postflight_custody_exact", lambda *_a, **_k: True)
    monkeypatch.setattr(subprocess, "Popen", lambda *_a, **_k: Process())
    monkeypatch.setattr(authority.os, "killpg", lambda *_args: None)
    transport = authority._run_child_bounded(
        contracts,
        chain["request_raw"],
        chain["genesis_raw"],
        [chain["event_zero_raw"], chain["event_one_raw"], chain["child_claim_raw"]],
        chain["registration_raw"],
        chain["registration"],
    )
    assert transport["child_spawn_succeeded"] is True
    assert transport["child_process_reap_observed"] is False
    assert transport["child_exit_code_observed"] is False
    with pytest.raises(authority.AuthorityError, match="reap is unknown"):
        authority._make_terminal_outcome(
            contracts,
            chain["marker_raw"],
            chain["marker"],
            chain["registration_raw"],
            chain["child_claim_raw"],
            chain["child_claim"],
            transport,
            True,
        )


def test_private_runner_requires_exact_claimed_prefix_before_popen(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    contracts, authority, _runtime = modules
    chain = _admitted_chain(contracts, authority)
    popen_calls: list[object] = []
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **_kwargs: popen_calls.append(args) or (_ for _ in ()).throw(
            AssertionError("Popen reached without exact durable claim")
        ),
    )
    monkeypatch.setattr(authority, "_postflight_custody_exact", lambda *_a, **_k: False)
    transport = authority._run_child_bounded(
        contracts,
        chain["request_raw"],
        chain["genesis_raw"],
        [chain["event_zero_raw"], chain["event_one_raw"], chain["child_claim_raw"]],
        chain["registration_raw"],
        chain["registration"],
    )
    assert popen_calls == []
    assert transport["child_spawn_succeeded"] is False
    assert transport["child_process_reap_observed"] is False

    monkeypatch.setattr(authority, "_postflight_custody_exact", lambda *_a, **_k: True)
    bad_claim = bytearray(chain["child_claim_raw"])
    bad_claim[-2] = ord("x")
    transport = authority._run_child_bounded(
        contracts,
        chain["request_raw"],
        chain["genesis_raw"],
        [chain["event_zero_raw"], chain["event_one_raw"], bytes(bad_claim)],
        chain["registration_raw"],
        chain["registration"],
    )
    assert popen_calls == []
    assert transport["child_spawn_succeeded"] is False


@pytest.mark.parametrize(
    "mutation",
    (
        "runtime_source",
        "authorization",
        "marker_mode",
        "marker_semantic_link",
        "genesis_semantic_link",
        "event0_semantic_link",
        "admission_semantic_link",
        "lock_nonempty",
        "event_gap",
        "event_extra",
        "event2_mode",
        "event2_hardlink",
        "nested_bool_ordinal",
        "terminal_broken_symlink",
        "result_present",
    ),
)
def test_runtime_static_and_claimed_child_prefix_negative_matrix(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    contracts, authority, runtime = modules
    root = tmp_path / mutation
    root.mkdir()
    root.chmod(0o700)
    chain, paths = _runtime_claim_fixture(
        root, contracts, authority, runtime, monkeypatch
    )
    assert runtime._static_closure_exact(chain["request"]) is True
    assert runtime._claimed_child_prefix_exact(
        chain["request_raw"], chain["request"]
    ) is True
    if mutation == "runtime_source":
        paths["module"].write_bytes(paths["module"].read_bytes() + b"\n")
        assert runtime._static_closure_exact(chain["request"]) is False
        return
    if mutation == "authorization":
        authorization = json.loads(paths["authorization"].read_text("ascii"))
        authorization["network_authorized"] = True
        authorization.pop("record_sha256")
        authorization = authority._attach(authorization, "record_sha256")
        _put(paths["authorization"], _file_bytes(authorization), 0o644)
        assert runtime._static_closure_exact(chain["request"]) is False
        return
    if mutation == "marker_mode":
        paths["marker"].chmod(0o644)
    elif mutation == "marker_semantic_link":
        marker = json.loads(paths["marker"].read_text("ascii"))
        marker["attempt_nonce_sha256"] = "a" * 64
        marker.pop("marker_sha256")
        marker = authority._attach(marker, "marker_sha256")
        _put(paths["marker"], _file_bytes(marker), 0o600)
    elif mutation == "genesis_semantic_link":
        genesis = json.loads(paths["genesis"].read_text("ascii"))
        genesis["marker_raw_sha256"] = "b" * 64
        genesis.pop("genesis_sha256")
        genesis = authority._attach(genesis, "genesis_sha256")
        _put(paths["genesis"], _file_bytes(genesis), 0o600)
    elif mutation == "event0_semantic_link":
        event0_path = paths["events"] / "00000000000000000000.json"
        event0 = json.loads(event0_path.read_text("ascii"))
        event0["previous_record_raw_sha256"] = "c" * 64
        event0.pop("event_sha256")
        event0 = authority._attach(event0, "event_sha256")
        _put(event0_path, _file_bytes(event0), 0o600)
    elif mutation == "admission_semantic_link":
        admission_path = paths["events"] / "00000000000000000001.json"
        admission = json.loads(admission_path.read_text("ascii"))
        admission["previous_record_sha256"] = "d" * 64
        admission.pop("event_sha256")
        admission = authority._attach(admission, "event_sha256")
        _put(admission_path, _file_bytes(admission), 0o600)
    elif mutation == "lock_nonempty":
        paths["lock"].write_bytes(b"x")
    elif mutation == "event_gap":
        (paths["events"] / "00000000000000000001.json").unlink()
    elif mutation == "event_extra":
        _put(paths["events"] / "00000000000000000003.json", b"{}\n", 0o600)
    elif mutation == "event2_mode":
        (paths["events"] / "00000000000000000002.json").chmod(0o644)
    elif mutation == "event2_hardlink":
        os.link(
            paths["events"] / "00000000000000000002.json",
            root / "claim_second_link.json",
        )
    elif mutation == "nested_bool_ordinal":
        claim = json.loads(
            (paths["events"] / "00000000000000000002.json").read_text("ascii")
        )
        nested = dict(claim["runtime_request"])
        nested["child_launch_ordinal"] = False
        nested.pop("request_sha256")
        nested = authority._attach(nested, "request_sha256")
        nested_raw = _file_bytes(nested)
        claim["runtime_request"] = nested
        claim["runtime_request_raw_sha256"] = _sha(nested_raw)
        claim["runtime_request_sha256"] = nested["request_sha256"]
        claim.pop("event_sha256")
        claim = authority._attach(claim, "event_sha256")
        _put(
            paths["events"] / "00000000000000000002.json",
            _file_bytes(claim),
            0o600,
        )
    elif mutation == "terminal_broken_symlink":
        paths["terminal"].symlink_to(root / "missing_terminal")
    elif mutation == "result_present":
        _put(paths["result"], b"{}\n", 0o644)
    else:
        raise AssertionError(mutation)
    assert runtime._claimed_child_prefix_exact(
        chain["request_raw"], chain["request"]
    ) is False


def test_runtime_live_invocation_rechecks_three_two_two_and_short_circuits(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _contracts, _authority, runtime = modules
    order = ("dispatch", "static", "prefix", "dispatch", "static", "prefix", "dispatch")

    def install(trace: list[str], false_at: int | None) -> None:
        def counted(name: str):
            def call(*_args: object) -> bool:
                trace.append(name)
                return false_at is None or len(trace) - 1 != false_at

            return call

        monkeypatch.setattr(
            runtime, "_canonical_live_dispatch_exact", counted("dispatch")
        )
        monkeypatch.setattr(runtime, "_static_closure_exact", counted("static"))
        monkeypatch.setattr(
            runtime, "_claimed_child_prefix_exact", counted("prefix")
        )

    all_true_trace: list[str] = []
    install(all_true_trace, None)
    assert runtime._live_invocation_exact(b"request\n", {}) is True
    assert tuple(all_true_trace) == order

    for false_at in range(len(order)):
        trace: list[str] = []
        install(trace, false_at)
        assert runtime._live_invocation_exact(b"request\n", {}) is False
        assert tuple(trace) == order[: false_at + 1]


def test_runtime_private_collectors_refuse_before_environment_mutation(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contracts, authority, runtime = modules
    chain = _admitted_chain(contracts, authority)
    before = dict(os.environ)
    monkeypatch.setattr(runtime, "_live_invocation_exact", lambda *_args: False)
    monkeypatch.setattr(
        runtime,
        "evaluate_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("snapshot evaluation reached")
        ),
    )
    with pytest.raises(runtime.ChildError, match="REQUEST"):
        runtime._live_snapshot(chain["request_raw"], chain["request"])
    with pytest.raises(runtime.ChildError, match="REQUEST"):
        runtime._build_live_observation(chain["request_raw"])
    assert dict(os.environ) == before


def test_runtime_direct_dispatch_rejects_runpy_import_and_wrong_native_tail(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _contracts, _authority, runtime = modules
    exact_native = (
        "/synthetic/absolute/python-app-launcher",
        *runtime.PYTHON_FLAGS,
        str(runtime.MODULE_PATH),
        "--emit-child-observation",
    )
    monkeypatch.setattr(runtime, "__name__", "__main__")
    monkeypatch.setattr(runtime, "__spec__", None)
    monkeypatch.setattr(
        runtime.sys,
        "argv",
        [str(runtime.MODULE_PATH), "--emit-child-observation"],
    )
    monkeypatch.setattr(runtime.sys, "executable", str(runtime.PYTHON_PATH))
    monkeypatch.setattr(runtime, "_native_argv", lambda: exact_native)
    monkeypatch.chdir(ROOT)
    assert runtime._canonical_live_dispatch_exact() is True
    monkeypatch.chdir(tmp_path)
    assert runtime._canonical_live_dispatch_exact() is False
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(
        runtime,
        "_native_argv",
        lambda: (
            "/synthetic/absolute/python-app-launcher",
            "-c",
            str(runtime.MODULE_PATH),
            "--emit-child-observation",
        ),
    )
    assert runtime._canonical_live_dispatch_exact() is False
    monkeypatch.setattr(runtime, "_native_argv", lambda: exact_native)
    monkeypatch.setattr(runtime, "__spec__", object())
    assert runtime._canonical_live_dispatch_exact() is False
    monkeypatch.setattr(runtime, "__spec__", None)
    monkeypatch.setattr(runtime, "__name__", "runpy_runtime")
    assert runtime._canonical_live_dispatch_exact() is False


def test_marker_reservation_o_excl_replay_partial_and_namespace_refusal(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contracts, authority, _runtime = modules
    chain = _base_chain(contracts, authority, admitted=False)
    root = tmp_path / "marker_reservation"
    root.mkdir()
    root.chmod(0o700)
    artifacts = root / "artifacts"
    fixtures = root / "research" / "fixtures"
    artifacts.mkdir()
    fixtures.mkdir(parents=True)
    artifacts.chmod(0o700)
    fixtures.parent.chmod(0o700)
    fixtures.chmod(0o700)
    marker = artifacts / "a1_r1_activation_preparation_v4.attempt.json"
    preparation = artifacts / "a1_r1_activation_preparation_v4"
    result = fixtures / "result.json"
    monkeypatch.setattr(authority, "WORKSPACE_ROOT", root)
    monkeypatch.setattr(authority, "MARKER_PATH", marker)
    monkeypatch.setattr(authority, "PREPARATION_ROOT", preparation)
    monkeypatch.setattr(authority, "RESULT_PATH", result)
    monkeypatch.setattr(
        authority, "_require_live_write_scope", lambda *args, **kwargs: None
    )
    old_live = authority._LIVE_CUSTODY
    authority._LIVE_CUSTODY = None
    try:
        authority._reserve_and_publish_marker(
            chain["marker_raw"],
            chain["marker"],
            chain["registration_raw"],
            chain["registration"],
            chain["authorization_raw"],
            chain["authorization"],
        )
        assert marker.read_bytes() == chain["marker_raw"]
        marker_status = marker.lstat()
        assert stat.S_IMODE(marker_status.st_mode) == 0o600
        assert marker_status.st_nlink == 1
        with pytest.raises(authority.AuthorityError, match="not pristine"):
            authority._reserve_and_publish_marker(
                chain["marker_raw"],
                chain["marker"],
                chain["registration_raw"],
                chain["registration"],
                chain["authorization_raw"],
                chain["authorization"],
            )
        assert marker.read_bytes() == chain["marker_raw"]
    finally:
        authority._LIVE_CUSTODY = old_live

    for name, create in (
        ("empty_marker", "marker"),
        ("existing_root", "root"),
        ("existing_result", "result"),
    ):
        case = tmp_path / name
        case.mkdir()
        case.chmod(0o700)
        case_artifacts = case / "artifacts"
        case_fixtures = case / "research" / "fixtures"
        case_artifacts.mkdir()
        case_fixtures.mkdir(parents=True)
        case_artifacts.chmod(0o700)
        case_fixtures.parent.chmod(0o700)
        case_fixtures.chmod(0o700)
        case_marker = case_artifacts / "a1_r1_activation_preparation_v4.attempt.json"
        case_root = case_artifacts / "a1_r1_activation_preparation_v4"
        case_result = case_fixtures / "result.json"
        if create == "marker":
            _put(case_marker, b"", 0o600)
        elif create == "root":
            case_root.mkdir()
            case_root.chmod(0o700)
        else:
            _put(case_result, b"partial\n", 0o644)
        monkeypatch.setattr(authority, "WORKSPACE_ROOT", case)
        monkeypatch.setattr(authority, "MARKER_PATH", case_marker)
        monkeypatch.setattr(authority, "PREPARATION_ROOT", case_root)
        monkeypatch.setattr(authority, "RESULT_PATH", case_result)
        authority._LIVE_CUSTODY = None
        with pytest.raises(authority.AuthorityError, match="not pristine"):
            authority._reserve_and_publish_marker(
                chain["marker_raw"],
                chain["marker"],
                chain["registration_raw"],
                chain["registration"],
                chain["authorization_raw"],
                chain["authorization"],
            )
        if create == "marker":
            assert case_marker.read_bytes() == b""
        else:
            with pytest.raises(FileNotFoundError):
                case_marker.lstat()
    authority._LIVE_CUSTODY = old_live


def test_status_invalid_authorization_marker_and_partial_directory_prefixes(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
) -> None:
    contracts, authority, _runtime = modules
    chain = _registered_chain(contracts, authority, admitted=False)

    auth_root = tmp_path / "bad_auth"
    auth_root.mkdir()
    auth_root.chmod(0o700)
    auth_paths = authority._operational_paths(auth_root)
    bad_auth = bytearray(chain["authorization_raw"])
    bad_auth[-2] = ord("x")
    _put(auth_paths["authorization"], bytes(bad_auth), 0o644)
    status = authority.status(authority.SyntheticStateRoot(auth_root))
    assert status["authorization_record_present"] is True
    assert status["authorization_record_exact"] is False
    assert status["attempt_spent"] is False
    assert status["retry_permitted"] is False

    marker_root = tmp_path / "empty_marker"
    marker_root.mkdir()
    marker_root.chmod(0o700)
    marker_paths = authority._operational_paths(marker_root)
    _put(marker_paths["authorization"], chain["authorization_raw"], 0o644)
    _put(marker_paths["marker"], b"", 0o600)
    status = authority.status(authority.SyntheticStateRoot(marker_root))
    assert status["marker_present"] is True
    assert status["marker_raw_observed"] is True
    assert status["marker_self_valid"] is False
    assert status["attempt_spent"] is True
    assert status["retry_permitted"] is False

    torn_genesis_root = tmp_path / "torn_genesis"
    torn_genesis_root.mkdir()
    torn_genesis_root.chmod(0o700)
    torn_paths = _materialize_registered_prefix(
        torn_genesis_root, authority, chain, []
    )
    _put(torn_paths["genesis"], b"{\n", 0o600)
    status = authority.status(authority.SyntheticStateRoot(torn_genesis_root))
    assert status["milestone_state"] == authority.MARKER_FALLBACK_STATE
    assert status["event_count"] == 0
    assert status["last_valid_prefix_state"] == authority.MARKER_FALLBACK_STATE
    assert status["trailing_record_invalid_or_incomplete_kind"] == "GENESIS"
    assert status["trailing_record_invalid_or_incomplete_event_ordinal"] is None
    assert status["trailing_record_cause_unobserved"] is True
    assert status["marker_self_valid"] is True
    assert status["attempt_spent"] is True
    assert status["retry_permitted"] is False

    layouts = ("root", "ledger", "events", "lock", "genesis")
    for stop in layouts:
        root = tmp_path / f"partial_{stop}"
        root.mkdir()
        root.chmod(0o700)
        paths = authority._operational_paths(root)
        _put(paths["authorization"], chain["authorization_raw"], 0o644)
        _put(paths["marker"], chain["marker_raw"], 0o600)
        paths["root"].mkdir()
        paths["root"].chmod(0o700)
        if stop != "root":
            paths["ledger"].mkdir()
            paths["ledger"].chmod(0o700)
        if stop not in ("root", "ledger"):
            paths["events"].mkdir()
            paths["events"].chmod(0o700)
        if stop in ("lock", "genesis"):
            _put(paths["lock"], b"", 0o600)
        if stop == "genesis":
            _put(paths["genesis"], chain["genesis_raw"], 0o600)
        status = authority.status(authority.SyntheticStateRoot(root))
        assert status["marker_self_valid"] is True
        assert status["attempt_spent"] is True
        assert status["event_count"] == 0
        assert status["last_valid_prefix_state"] == authority.MARKER_FALLBACK_STATE
        assert status["retry_permitted"] is False
        if stop == "genesis":
            assert status["milestone_state"] == authority.MARKER_FALLBACK_STATE


def test_zz_final_canonical_absence_predecessor_and_freeze_preservation(
    modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType]
) -> None:
    _contracts, authority, _runtime = modules
    for path in (
        authority.AUTHORIZATION_PATH,
        authority.MARKER_PATH,
        authority.PREPARATION_ROOT,
        authority.RESULT_PATH,
    ):
        with pytest.raises(FileNotFoundError):
            path.lstat()
    for path, size, digest in V3_BINDINGS:
        raw = path.read_bytes()
        status = path.lstat()
        assert len(raw) == size and _sha(raw) == digest
        assert stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode)
        assert stat.S_IMODE(status.st_mode) == 0o644 and status.st_nlink == 1
    machine_raw, machine = _machine_record()
    assert machine["nonclaims"]["canonical_child_launched"] is False
    assert machine["nonclaims"]["scientific_execution_performed"] is False
    assert machine["current_qualification"]["attempt_spent"] is False
    assert machine["current_qualification"]["execution_authorized"] is False
    assert authority._load_registration() == (machine_raw, machine)
    focused = (
        "finite_association_r1_activation_preparation_rehearsal_contracts_v4",
        "finite_association_r1_activation_preparation_rehearsal_authority_v4",
        "finite_association_r1_activation_preparation_rehearsal_runtime_v4",
        "test_manuscript_v3_a1_r1_activation_preparation_v4_transition_safe",
    )
    assert [
        path
        for path in ROOT.rglob("*.pyc")
        if any(token in path.name for token in focused)
    ] == []
