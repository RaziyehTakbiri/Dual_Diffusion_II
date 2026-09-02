from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import socket
import stat
import subprocess
import sys

import pytest


WORKSPACE = Path(__file__).resolve().parents[2]
VALIDATOR = (
    WORKSPACE / "research/diagnostics/finite_association_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_terminal_pass_"
    "registration_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "v4_terminal_pass_registration", VALIDATOR
)
assert SPEC is not None and SPEC.loader is not None
POST = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = POST
SPEC.loader.exec_module(POST)

HUMAN = WORKSPACE / POST.HUMAN_PATH
MACHINE = WORKSPACE / POST.MACHINE_PATH
TEST = WORKSPACE / POST.TEST_PATH


def _fail(*args: object, **kwargs: object) -> object:
    del args, kwargs
    raise AssertionError("forbidden live action reached by custody registration")


@pytest.fixture(autouse=True)
def _forbid_process_entropy_network(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, _fail)
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


def _file_bytes(value: object) -> bytes:
    return _canonical(value) + b"\n"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("ascii"))
    assert type(value) is dict
    assert raw == _file_bytes(value)
    return value


def _operational_records() -> dict[str, object]:
    paths = {
        "authorization": POST.AUTHORIZATION_PATH,
        "marker": POST.MARKER_PATH,
        "genesis": POST.GENESIS_PATH,
        "event0": POST.EVENT_PATHS[0],
        "event1": POST.EVENT_PATHS[1],
        "event2": POST.EVENT_PATHS[2],
        "event3": POST.EVENT_PATHS[3],
        "terminal": POST.TERMINAL_PATH,
        "result": POST.RESULT_PATH,
    }
    return {name: _read_json(WORKSPACE / path) for name, path in paths.items()}


def _attach_plain(record: dict[str, object], key: str) -> None:
    record.pop(key, None)
    record[key] = _sha256(_canonical(record))


def _finish_registration(record: dict[str, object]) -> bytes:
    record["record_sha256"] = None
    record["record_sha256"] = _sha256(POST.REGISTRATION_DOMAIN + _canonical(record))
    return _file_bytes(record)


def test_exact_four_file_package_is_additive_and_closed() -> None:
    owned = (HUMAN, MACHINE, VALIDATOR, TEST)
    assert len(owned) == 4
    for path in owned:
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(info.st_mode) == 0o644
        assert info.st_nlink == 1
    record = _read_json(MACHINE)
    package = record["additive_package"]
    assert package["file_count"] == 4
    assert package["paths_selected_by_agent"] is True
    assert package["paths_or_file_count_selected_by_user"] is False
    assert [row["path"] for row in package["path_roster"]] == [
        POST.HUMAN_PATH,
        POST.MACHINE_PATH,
        POST.VALIDATOR_PATH,
        POST.TEST_PATH,
    ]
    assert record["scope"]["canonical_v4_v3_v2_or_scientific_file_mutated"] is False


def test_machine_is_canonical_closed_self_digested_and_rebuildable() -> None:
    payload = MACHINE.read_bytes()
    record = _read_json(MACHINE)
    assert POST._validate_machine_payload(WORKSPACE, payload) == record
    assert POST._build_registration_payload() == payload
    assert set(record) == set(POST._expected_fixed_registration()) | {
        "registration_bindings",
        "record_sha256",
    }
    body = copy.deepcopy(record)
    claimed = body["record_sha256"]
    body["record_sha256"] = None
    assert claimed == _sha256(POST.REGISTRATION_DOMAIN + _canonical(body))
    assert record["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert record["terminal_state"] == POST.TERMINAL_STATE


def test_visible_item_four_authorization_is_exact_and_narrow() -> None:
    provenance = _read_json(MACHINE)["authorization_provenance"]
    assert provenance["visible_item_prefix"] == "4-"
    assert provenance["antecedent_visible_text"] == POST.AUTHORIZATION_QUESTION
    assert provenance["visible_assent_text"] == "Yes."
    assert provenance["normalized_combined_visible_text"] == (
        "4- Do you authorize an additive V4 terminal-PASS custody registration "
        "only—no rerun, runtime approval, or science? Yes."
    )
    assert provenance["antecedent_utf8_bytes"] == 113
    assert provenance["visible_assent_utf8_bytes"] == 4
    assert provenance["normalized_combined_utf8_bytes"] == 121
    assert _sha256(POST.AUTHORIZATION_QUESTION.encode("utf-8")) == (
        provenance["antecedent_sha256"]
    )
    assert _sha256(b"Yes.") == provenance["visible_assent_sha256"]
    combined = provenance["normalized_combined_visible_text"].encode("utf-8")
    assert _sha256(combined) == provenance["normalized_combined_sha256"]
    domain = bytes.fromhex(provenance["domain_hex"])
    assert domain == POST.VISIBLE_AUTHORIZATION_DOMAIN
    assert domain.endswith(b"\x00")
    assert _sha256(domain + combined) == (
        provenance["domain_plus_normalized_combined_sha256"]
    )
    authorization_object = {
        "antecedent_visible_text": POST.AUTHORIZATION_QUESTION,
        "normalized_combined_visible_text": POST.AUTHORIZATION_COMBINED,
        "visible_assent_text": POST.AUTHORIZATION_ANSWER,
        "visible_item_prefix": "4-",
    }
    assert _sha256(domain + _canonical(authorization_object)) == (
        provenance["domain_plus_canonical_authorization_object_sha256"]
    )
    assert provenance["raw_transport_bytes_bound"] is False
    assert provenance["conversation_envelope_bound"] is False
    assert provenance["cryptographic_user_authentication"] is False
    assert provenance["user_selected_filenames_paths_schema_or_file_count"] is False
    assert (
        provenance[
            "rerun_runtime_approval_rank_training_production_science_or_claim_promotion_authorized"
        ]
        is False
    )


def test_thirteen_entry_inventory_is_exact_closed_world_and_reopened() -> None:
    record = _read_json(MACHINE)
    rows = POST._inventory_rows(WORKSPACE)
    assert rows == record["terminal_custody"]["inventory"]
    assert len(rows) == 13
    assert [row["ordinal"] for row in rows] == list(range(13))
    assert _sha256(POST.INVENTORY_DOMAIN + _canonical(rows)) == POST.INVENTORY_SHA256
    assert record["terminal_custody"]["inventory_canonical_preimage_bytes"] == 3634
    assert {row["entry_type"] for row in rows} == {"REGULAR_FILE", "DIRECTORY"}
    assert all(row["is_symlink"] is False for row in rows)
    assert all(row["nlink"] == 1 for row in rows if row["entry_type"] == "REGULAR_FILE")
    assert [row["mode_octal"] for row in rows if row["entry_type"] == "DIRECTORY"] == [
        "0700",
        "0700",
        "0700",
    ]
    assert tuple(
        sorted(path.name for path in (WORKSPACE / POST.EVENTS_PATH).iterdir())
    ) == tuple(f"{ordinal:020d}.json" for ordinal in range(4))


def test_event_three_is_sole_authority_and_projections_are_derivative() -> None:
    records = _operational_records()
    result = POST._validate_operational_semantics(records)
    assert result["event3_sha256"] == (
        "3335688ef062c5f3d6815b35db025dc84c5abf0cf2f10866e52c2a91eb37058a"
    )
    event3 = records["event3"]
    terminal = records["terminal"]
    published = records["result"]
    assert event3["event_ordinal"] == 3
    assert event3["event_kind"] == "TERMINAL_OUTCOME"
    assert event3["outcome"] == "PASS"
    assert terminal["authoritative_event_raw_sha256"] == _sha256(_file_bytes(event3))
    assert terminal["authoritative_event_sha256"] == event3["event_sha256"]
    assert published["local_terminal_raw_sha256"] == _sha256(_file_bytes(terminal))
    assert published["local_terminal_sha256"] == terminal["terminal_sha256"]
    boundary = _read_json(MACHINE)["terminal_custody"]
    assert boundary["local_terminal_is_projection"] is True
    assert boundary["published_result_is_derivative"] is True
    assert boundary["projection_or_derivative_can_promote_or_replace_event3"] is False


def test_all_supervisor_transport_and_child_gates_pass_with_truthful_counts() -> None:
    records = _operational_records()
    admission = records["event1"]
    event3 = records["event3"]
    observation = event3["child_observation"]
    assert set(admission["gate_vector"]) == set(POST.PRECHILD_GATE_ORDER)
    assert len(admission["gate_vector"]) == 22
    assert all(
        type(value) is bool and value for value in admission["gate_vector"].values()
    )
    assert set(event3["transport_gate_vector"]) == set(POST.TRANSPORT_GATE_ORDER)
    assert len(event3["transport_gate_vector"]) == 9
    assert all(event3["transport_gate_vector"].values())
    assert set(observation["gate_vector"]) == set(POST.CHILD_GATE_ORDER)
    assert len(observation["gate_vector"]) == 16
    assert all(observation["gate_vector"].values())
    assert event3["child_launch_claim_count"] == 1
    assert event3["child_process_start_count"] == 1
    assert event3["child_process_reap_observed"] is True
    assert event3["child_exit_code_observed"] is True
    assert type(event3["child_exit_code"]) is int and event3["child_exit_code"] == 0
    assert event3["child_stdin_captured_write_byte_count"] == 1332
    assert event3["child_stdout_captured_byte_count"] == 1795
    assert event3["child_stderr_captured_byte_count"] == 0
    assert event3["raw_child_transport_persisted"] is False
    assert observation["application_effect_claim_basis"] == (
        "STATIC_CHILD_SOURCE_AND_ROUTE_CONTRACT_NOT_OS_INSTRUMENTATION"
    )
    for key in (
        "entropy_contacted",
        "network_contacted",
        "temporary_write_performed",
        "workspace_write_performed",
        "scientific_import_or_execution_performed",
        "raw_absolute_path_emitted",
        "raw_argv_emitted",
        "raw_environment_emitted",
        "raw_identity_emitted",
        "raw_stderr_emitted",
    ):
        assert observation[key] is False


def test_v3_v2_continuity_and_probe_quarantine_are_reopened() -> None:
    result = POST._audit_predecessor_custody(WORKSPACE)
    status = result["v3_status"]
    custody = result["v3_custody"]
    assert status["terminal_state"] == POST.V3_TERMINAL_STATE
    assert status["canonical_rehearsal_attempt_count"] == 1
    assert status["canonical_rehearsal_retry_count"] == 0
    assert status["child_launch_count"] is None
    assert custody["v2_terminal_registration_record_sha256"] == (
        POST.V2_TERMINAL_RECORD_SHA256
    )
    assert custody["v2_preparation_file_count"] == 65
    assert custody["v2_preparation_directory_count"] == 20
    assert custody["v2_capsule"]["file_count"] == 53
    assert custody["v2_capsule"]["directory_count"] == 14
    v3_machine = _read_json(WORKSPACE / POST.V3_MACHINE_PATH)
    probes = v3_machine["post_failure_exploratory_context"]
    assert probes["probe_count"] == 5
    assert probes["context_is_canonical_failure_evidence"] is False
    assert probes["independently_verified_from_durable_raw_receipts"] is False
    assert (
        probes["raw_process_commands_bound_as_registered_workspace_artifacts"] is False
    )
    assert (
        probes["raw_process_outputs_bound_as_registered_workspace_artifacts"] is False
    )


def test_172_nulls_12_blockers_d1_and_test_data_unknown_are_preserved() -> None:
    state = POST._audit_scientific_state(WORKSPACE)
    assert state == {
        "historical_null_count": 174,
        "effective_unresolved_null_count": 172,
        "preexecution_unresolved_null_count": 166,
        "postexecution_unresolved_null_count": 6,
        "open_blocker_count": 12,
        "confirmatory_blocker_count": 10,
        "promotion_blocker_count": 2,
        "blockers_closed": 0,
        "test_data_unopened_before_freeze": None,
    }
    machine = _read_json(MACHINE)
    science = machine["scientific_state"]
    assert science["d1_quarantine_row_count"] == 550
    assert science["d1_quarantine_roster_sha256"] == POST.D1_QUARANTINE_ROSTER_SHA256
    assert science["d1_admissible_as_production_evidence"] is False
    assert science["confirmatory_execution_authorized"] is False
    assert science["scientific_result_eligible"] is False


@pytest.mark.parametrize(
    "case",
    [
        "authorization_science",
        "marker_bool_ordinal",
        "marker_registration",
        "genesis_marker_link",
        "event0_previous_link",
        "event1_gate",
        "event2_request_bool_ordinal",
        "event2_auth_link",
        "event3_previous_link",
        "event3_scientific_effect",
        "event3_transport_gate",
        "event3_child_gate",
        "terminal_event_link",
        "terminal_promotes_fail_to_pass",
        "result_terminal_link",
        "result_raw_path_publication",
    ],
)
def test_re_self_digested_semantic_mutations_fail_closed(case: str) -> None:
    records = copy.deepcopy(_operational_records())
    if case == "authorization_science":
        records["authorization"]["scientific_execution_authorized"] = True
        _attach_plain(records["authorization"], "record_sha256")
    elif case == "marker_bool_ordinal":
        records["marker"]["attempt_ordinal"] = False
        _attach_plain(records["marker"], "marker_sha256")
    elif case == "marker_registration":
        records["marker"]["registration_record_sha256"] = "0" * 64
        _attach_plain(records["marker"], "marker_sha256")
    elif case == "genesis_marker_link":
        records["genesis"]["marker_raw_sha256"] = "0" * 64
        _attach_plain(records["genesis"], "genesis_sha256")
    elif case == "event0_previous_link":
        records["event0"]["previous_record_sha256"] = "0" * 64
        _attach_plain(records["event0"], "event_sha256")
    elif case == "event1_gate":
        records["event1"]["gate_vector"][POST.PRECHILD_GATE_ORDER[-1]] = False
        records["event1"]["gate_vector_sha256"] = _sha256(
            _canonical(records["event1"]["gate_vector"])
        )
        _attach_plain(records["event1"], "event_sha256")
    elif case == "event2_request_bool_ordinal":
        request = records["event2"]["runtime_request"]
        request["child_launch_ordinal"] = False
        _attach_plain(request, "request_sha256")
        records["event2"]["runtime_request_sha256"] = request["request_sha256"]
        records["event2"]["runtime_request_raw_sha256"] = _sha256(_file_bytes(request))
        _attach_plain(records["event2"], "event_sha256")
    elif case == "event2_auth_link":
        records["event2"]["runtime_request"]["execution_authorization_raw_sha256"] = (
            "0" * 64
        )
        _attach_plain(records["event2"]["runtime_request"], "request_sha256")
        request = records["event2"]["runtime_request"]
        records["event2"]["runtime_request_sha256"] = request["request_sha256"]
        records["event2"]["runtime_request_raw_sha256"] = _sha256(_file_bytes(request))
        _attach_plain(records["event2"], "event_sha256")
    elif case == "event3_previous_link":
        records["event3"]["previous_record_raw_sha256"] = "0" * 64
        _attach_plain(records["event3"], "event_sha256")
    elif case == "event3_scientific_effect":
        observation = records["event3"]["child_observation"]
        observation["scientific_import_or_execution_performed"] = True
        _attach_plain(observation, "observation_sha256")
        records["event3"]["child_observation_sha256"] = observation[
            "observation_sha256"
        ]
        records["event3"]["child_observation_raw_sha256"] = _sha256(
            _file_bytes(observation)
        )
        _attach_plain(records["event3"], "event_sha256")
    elif case == "event3_transport_gate":
        records["event3"]["transport_gate_vector"][POST.TRANSPORT_GATE_ORDER[0]] = False
        records["event3"]["transport_gate_vector_sha256"] = _sha256(
            _canonical(records["event3"]["transport_gate_vector"])
        )
        _attach_plain(records["event3"], "event_sha256")
    elif case == "event3_child_gate":
        observation = records["event3"]["child_observation"]
        observation["gate_vector"][POST.CHILD_GATE_ORDER[0]] = False
        observation["gate_vector_sha256"] = _sha256(
            _canonical(observation["gate_vector"])
        )
        _attach_plain(observation, "observation_sha256")
        records["event3"]["child_observation_sha256"] = observation[
            "observation_sha256"
        ]
        records["event3"]["child_observation_raw_sha256"] = _sha256(
            _file_bytes(observation)
        )
        _attach_plain(records["event3"], "event_sha256")
    elif case == "terminal_event_link":
        records["terminal"]["authoritative_event_sha256"] = "0" * 64
        _attach_plain(records["terminal"], "terminal_sha256")
    elif case == "terminal_promotes_fail_to_pass":
        records["event3"]["outcome"] = "FAIL"
        _attach_plain(records["event3"], "event_sha256")
    elif case == "result_terminal_link":
        records["result"]["local_terminal_raw_sha256"] = "0" * 64
        _attach_plain(records["result"], "record_sha256")
    elif case == "result_raw_path_publication":
        records["result"]["raw_path_or_argv_published"] = True
        _attach_plain(records["result"], "record_sha256")
    with pytest.raises(POST.TerminalPassRegistrationError):
        POST._validate_operational_semantics(records)


def test_machine_hostiles_reject_extra_missing_type_alias_and_binding_changes() -> None:
    original = _read_json(MACHINE)
    mutations = []
    extra = copy.deepcopy(original)
    extra["extra"] = False
    mutations.append(extra)
    missing = copy.deepcopy(original)
    missing.pop("nonclaims")
    mutations.append(missing)
    alias = copy.deepcopy(original)
    alias["terminal_custody"]["authoritative_record"]["event_ordinal"] = 3.0
    mutations.append(alias)
    binding = copy.deepcopy(original)
    binding["registration_bindings"][0]["path"] = POST.TEST_PATH
    mutations.append(binding)
    nonclaim = copy.deepcopy(original)
    nonclaim["nonclaims"]["registration_authorizes_v4_rerun"] = True
    mutations.append(nonclaim)
    for mutation in mutations:
        payload = _finish_registration(mutation)
        with pytest.raises(POST.TerminalPassRegistrationError):
            POST._validate_machine_payload(WORKSPACE, payload)


def test_no_follow_mode_nlink_and_directory_roster_hostiles(tmp_path: Path) -> None:
    relative = "nested/record.json"
    (tmp_path / "nested").mkdir(mode=0o700)
    target = tmp_path / relative
    target.write_bytes(b"{}\n")
    target.chmod(0o644)
    assert POST._read_stable_file(tmp_path, relative)[0] == b"{}\n"
    target.chmod(0o600)
    with pytest.raises(POST.TerminalPassRegistrationError):
        POST._read_stable_file(tmp_path, relative)
    target.chmod(0o644)
    hardlink = tmp_path / "nested/hardlink.json"
    os.link(target, hardlink)
    with pytest.raises(POST.TerminalPassRegistrationError):
        POST._read_stable_file(tmp_path, relative)
    hardlink.unlink()
    target.unlink()
    target.symlink_to("missing.json")
    with pytest.raises(POST.TerminalPassRegistrationError):
        POST._read_stable_file(tmp_path, relative)
    target.unlink()
    (tmp_path / "closed").mkdir(mode=0o700)
    assert POST._read_directory(tmp_path, "closed", 0o700, 2, ()) is not None
    (tmp_path / "closed/extra").write_bytes(b"")
    with pytest.raises(POST.TerminalPassRegistrationError):
        POST._read_directory(tmp_path, "closed", 0o700, 2, ())


def test_validator_source_has_no_live_or_scientific_import_route() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {
        "__future__",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "stat",
        "types",
        "typing",
    }
    assert imported.isdisjoint(
        {"subprocess", "socket", "secrets", "urllib", "requests"}
    )
    for forbidden_module in (
        "finite_association_r1_activation_preparation_rehearsal_authority_v4",
        "finite_association_r1_activation_preparation_rehearsal_runtime_v4",
        "src.heterodiff",
    ):
        assert forbidden_module not in source
    assert "os.write(" not in source
    assert ".write_bytes(" not in source
    assert ".write_text(" not in source
    assert "O_WRONLY" not in source
    assert "O_RDWR" not in source
    assert "O_CREAT" not in source


def test_qualification_is_immutable_and_status_is_non_authorizing() -> None:
    qualification = POST.load_qualification()
    with pytest.raises(TypeError):
        POST.TerminalPassQualification()
    with pytest.raises(AttributeError):
        qualification._record_sha256 = "0" * 64
    status = POST.status()
    assert status["outcome"] == "PASS"
    assert status["authoritative_event_ordinal"] == 3
    assert status["attempt_spent"] is True
    assert status["retry_permitted"] is False
    assert status["runtime_approval_created"] is False
    assert status["scientific_execution_performed"] is False
    assert status["effective_unresolved_null_count"] == 172
    assert status["open_blocker_count"] == 12
    assert status["test_data_unopened_before_freeze"] is None
    assert status["execution_authorized"] is False
    assert status["claim_promotion_permitted"] is False


def test_stdout_provenance_and_publication_boundary_are_not_overclaimed() -> None:
    record = _read_json(MACHINE)
    stdout = record["stdout_provenance"]
    assert (
        stdout["orchestrator_transcript_reports_single_stdout_canonical_result"] is True
    )
    assert (
        stdout["authority_invariant_requires_reopened_persisted_result_bytes"] is True
    )
    assert stdout["independent_raw_stdout_receipt_bound"] is False
    assert stdout["independent_stdout_digest_claimed"] is False
    assert (
        stdout["transcript_comparison_promoted_to_separate_custody_evidence"] is False
    )
    assert record["scope"]["anonymous_or_public_release_permitted"] is False
    assert record["scope"]["publication_safe_derivative_required"] is True
    assert record["scope"]["raw_operational_custody_publication_permitted"] is False


def test_no_focused_bytecode_cache_and_canonical_custody_remain_unchanged() -> None:
    stems = (VALIDATOR.stem, TEST.stem)
    found = []
    for relative in ("research/diagnostics/__pycache__", "tests/unit/__pycache__"):
        directory = WORKSPACE / relative
        if directory.exists():
            found.extend(
                path.relative_to(WORKSPACE).as_posix()
                for path in directory.iterdir()
                if any(stem in path.name for stem in stems)
            )
    assert found == []
    for role, path, size, digest, mode in POST.OPERATIONAL_FILE_EXPECTATIONS:
        del role
        raw = (WORKSPACE / path).read_bytes()
        info = (WORKSPACE / path).lstat()
        assert len(raw) == size
        assert _sha256(raw) == digest
        assert stat.S_IMODE(info.st_mode) == mode
        assert info.st_nlink == 1
        assert not (WORKSPACE / path).is_symlink()
    assert (
        POST._inventory_rows(WORKSPACE)
        == _read_json(MACHINE)["terminal_custody"]["inventory"]
    )
