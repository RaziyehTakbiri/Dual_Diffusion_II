from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import secrets
import socket
import subprocess
import sys
from pathlib import Path

import pytest


WORKSPACE = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    WORKSPACE / "research/diagnostics/finite_association_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "finite_association_r1_activation_preparation_v2_terminal_failure_"
    "registration_v1",
    VALIDATOR_PATH,
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
    raise AssertionError("forbidden side effect reached during postmortem test")


@pytest.fixture(autouse=True)
def _forbid_entropy_process_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secrets, "token_bytes", _fail)
    monkeypatch.setattr(subprocess, "Popen", _fail)
    monkeypatch.setattr(subprocess, "run", _fail)
    monkeypatch.setattr(subprocess, "call", _fail)
    monkeypatch.setattr(subprocess, "check_call", _fail)
    monkeypatch.setattr(subprocess, "check_output", _fail)
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


def _read_json(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    value = json.loads(payload.decode("ascii"))
    assert type(value) is dict
    assert payload == _canonical(value) + b"\n"
    return value


def _finish_registration(value: dict[str, object]) -> bytes:
    body = copy.deepcopy(value)
    body["record_sha256"] = None
    body["record_sha256"] = _sha256(POST.REGISTRATION_DOMAIN + _canonical(body))
    return _canonical(body) + b"\n"


def test_four_paths_are_additive_and_all_frozen_v2_bytes_remain_exact() -> None:
    owned = (HUMAN, MACHINE, VALIDATOR_PATH, TEST)
    assert all(path.is_file() and not path.is_symlink() for path in owned)
    for row in POST.FROZEN_V2_BINDINGS:
        path = WORKSPACE / row["path"]
        payload = path.read_bytes()
        assert len(payload) == row["bytes"]
        assert _sha256(payload) == row["raw_sha256"]
    assert (WORKSPACE / POST.MARKER_PATH).is_file()
    assert (WORKSPACE / POST.PREPARATION_ROOT).is_dir()


def test_machine_registration_is_canonical_closed_and_self_digested() -> None:
    payload = MACHINE.read_bytes()
    record = _read_json(MACHINE)
    checked = POST._validate_machine_registration_payload(WORKSPACE, payload)
    assert checked == record
    expected_keys = set(POST._expected_fixed_registration()) | {
        "registration_bindings",
        "record_sha256",
    }
    assert set(record) == expected_keys
    body = copy.deepcopy(record)
    claimed = body["record_sha256"]
    body["record_sha256"] = None
    assert claimed == _sha256(POST.REGISTRATION_DOMAIN + _canonical(body))
    assert record["terminal_state"] == POST.TERMINAL_STATE
    assert record["global_state"] == "DRAFT_NOT_EXECUTABLE"


def test_read_only_loader_reopens_exact_terminal_prefix_and_capsule() -> None:
    custody = POST.audit_terminal_custody()
    assert custody == {
        "schema": POST.QUALIFICATION_SCHEMA,
        "terminal_state": POST.TERMINAL_STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "marker_attempt_spent": True,
        "retry_permitted": False,
        "validated_preparation_event_count": 3,
        "validated_current_head_sha256": (
            "4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5"
        ),
        "capture_a_launch_claim_spent": True,
        "capture_a_binding_present": False,
        "capture_b_launch_claim_present": False,
        "capture_b_binding_present": False,
        "runtime_candidate_present": False,
        "typed_terminal_ledger_event_present": False,
        "raw_runtime_envelopes_persisted": False,
        "capsule": {
            "file_count": 53,
            "directory_count": 14,
            "inventory_sha256": (
                "c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360"
            ),
            "all_rows_reopened_twice": True,
            "closed_world_verified": True,
        },
        "preparation_file_count": 65,
        "preparation_directory_count": 20,
        "frozen_test_failure_count": 2,
        "unresolved_null_count": 172,
        "open_blocker_count": 12,
        "d1_quarantine_row_count": 550,
        "d1_quarantine_roster_sha256": (
            "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
        ),
        "execution_authorized": False,
    }
    observed = POST.status()
    assert observed["marker_attempt_spent"] is True
    assert observed["retry_permitted"] is False
    assert observed["validated_preparation_event_count"] == 3
    assert observed["capture_a_binding_present"] is False
    assert observed["capture_b_launch_claim_present"] is False
    assert observed["runtime_candidate_present"] is False
    assert observed["v3_authorized"] is False
    assert observed["execution_authorized"] is False


def test_exact_twelve_record_rows_and_terminal_absences_are_bound() -> None:
    machine = _read_json(MACHINE)
    custody = machine["observed_terminal_custody"]
    assert type(custody) is dict
    assert custody["records"] == list(POST.RECORD_ROWS)
    assert custody["record_count"] == 12
    assert [row["ordinal"] for row in POST.RECORD_ROWS] == list(range(12))
    for row in POST.RECORD_ROWS:
        payload = (WORKSPACE / row["path"]).read_bytes()
        record = POST._parse_canonical_record(payload, row)
        assert record[row["terminal_digest_key"]] == row["record_sha256"]
    for row in POST.ABSENT_V2_ROWS:
        assert not POST._path_has_entry(WORKSPACE / row["path"])
    assert custody["event_3_nonce_claim_present"] is False
    assert custody["event_3_present"] is False
    assert custody["event_4_nonce_claim_present"] is False
    assert custody["event_4_present"] is False
    assert list((WORKSPACE / POST.RUNTIME_CANDIDATE_ROOT).iterdir()) == []


def test_marker_binds_context_and_sidecar_registers_conversation_assent() -> None:
    machine = _read_json(MACHINE)
    authorization = machine["authorization"]
    assert authorization == POST._expected_fixed_registration()["authorization"]
    assert POST._normalized_assent(POST.USER_ASSENT_TEXT) == POST.USER_ASSENT_TEXT
    assert authorization["user_assent_sha256"] == POST.user_assent_sha256()
    assert authorization["user_assent_source"] == "CONVERSATION_VISIBLE_TEXT"
    assert authorization["user_message_envelope_bound_as_workspace_artifact"] is False
    marker_row = POST.RECORD_ROWS[0]
    marker = POST._parse_canonical_record(
        (WORKSPACE / marker_row["path"]).read_bytes(), marker_row
    )
    assert marker["operator_authorization_context"] == (
        authorization["operator_authorization_context"]
    )
    assert marker["operator_authorization_sha256"] == (
        authorization["operator_authorization_sha256"]
    )
    assert authorization["runtime_approval_authorized"] is False
    assert authorization["rank_training_production_science_authorized"] is False


def test_failure_diagnosis_is_precise_private_and_does_not_claim_raw_stderr() -> None:
    machine = _read_json(MACHINE)
    diagnosis = machine["failure_diagnosis"]
    assert diagnosis["frozen_requested_environment"] == {
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
    }
    assert diagnosis["equivalent_profile_probe_effective_environment_internal"] == {
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
        "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x0",
    }
    assert diagnosis["exact_environment_equality_result"] is False
    assert diagnosis["deterministic_first_failing_check"] == (
        "runtime child environment is not exact"
    )
    assert diagnosis["raw_child_stderr_persisted"] is False
    assert diagnosis["raw_child_stderr_surfaced"] is False
    assert diagnosis["reported_canonical_action_exit_code"] == 1
    assert diagnosis["child_exit_code_directly_observed"] is False
    assert diagnosis["reported_canonical_action_wall_time_seconds"] == "1.99"
    assert diagnosis["failed_child_environment_directly_observed"] is False
    assert diagnosis["cause_is_frozen_control_flow_inference"] is True
    assert (
        diagnosis["canonical_action_raw_command_receipt_bound_as_workspace_artifact"]
        is False
    )
    assert (
        diagnosis["equivalent_profile_probe_raw_receipt_bound_as_workspace_artifact"]
        is False
    )
    assert diagnosis["verbatim_child_exception_claimed"] is False
    assert diagnosis["downstream_runtime_checks_reached"] is False
    assert diagnosis["additional_downstream_failure_absence_claimed"] is False
    assert diagnosis["future_v3_value_derivation"] == ("0x%X:0x0:0x0 % os.getuid()")
    human = HUMAN.read_text(encoding="utf-8")
    assert "0x1F5:0x0:0x0" not in human
    assert "<DARWIN_USER_TEXT_ENCODING>" in human
    assert "/Users/" not in human


def test_public_status_collapse_and_two_stale_frozen_tests_are_registered() -> None:
    machine = _read_json(MACHINE)
    defect = machine["public_status_defect"]
    assert (
        defect["orchestrator_reported_immediate_post_failure_live_transition"]
        == POST.EXPECTED_PUBLIC_STATUS
    )
    assert defect["status_raw_receipt_bound_as_workspace_artifact"] is False
    assert (
        defect[
            "status_fallback_independently_reconstructed_from_frozen_source_and_terminal_custody"
        ]
        is True
    )
    assert defect["status_reported_preparation_event_count"] == 0
    assert defect["independently_validated_preparation_event_count"] == 3
    assert defect["valid_prefix_collapsed_on_terminal_exception"] is True
    frozen_test = machine["frozen_test_defect"]
    assert frozen_test["targeted_test_count"] == 2
    assert frozen_test["targeted_pass_count"] == 0
    assert frozen_test["targeted_failure_count"] == 2
    assert frozen_test["targeted_exit_code"] == 1
    assert frozen_test["targeted_test_raw_receipt_bound_as_workspace_artifact"] is False
    assert frozen_test["failure_conditions_independently_reopened"] is True
    assert frozen_test["failures"] == list(POST.FROZEN_TEST_FAILURES)
    assert frozen_test["claimed_transition_awareness_is_durable"] is False
    assert POST._path_has_entry(WORKSPACE / POST.MARKER_PATH)
    assert POST.EXPECTED_PUBLIC_STATUS["live_state"] != (
        "AWAITING_EXPLICIT_MARKER_AUTHORIZATION"
    )


def test_state_preservation_d1_and_capsule_nonadmission_are_exact() -> None:
    machine = _read_json(MACHINE)
    assert machine["state_preservation"] == {
        "projection_source": "FROZEN_V2_STATIC_QUALIFICATION_SNAPSHOT",
        "projection_values_reopened_from_frozen_snapshot": True,
        "postmortem_underlying_rosters_recomputed": False,
        "unresolved_null_count": 172,
        "open_blocker_count": 12,
        "d1_quarantine_row_count": 550,
        "d1_quarantine_roster_sha256": (
            "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
        ),
        "d1_execution_admissible": False,
        "global_state": "DRAFT_NOT_EXECUTABLE",
    }
    custody = machine["observed_terminal_custody"]
    assert custody["capsule_admission_is_preparation_custody_only"] is True
    assert custody["capsule_admission_is_scientific_execution_evidence"] is False
    assert custody["capsule_execution_admissible"] is False
    nonclaims = machine["nonclaims"]
    assert nonclaims["postmortem_network_contacted"] is False
    assert all(value is False for value in nonclaims.values())


def test_next_gate_is_disjoint_v3_and_authorizes_nothing() -> None:
    machine = _read_json(MACHINE)
    gate = machine["next_gate"]
    assert gate == POST._expected_fixed_registration()["next_gate"]
    assert gate["v2_terminal_artifacts_must_remain_immutable"] is True
    assert gate["v2_retry_delete_repair_forbidden"] is True
    assert gate["additive_disjoint_v3_registration_required"] is True
    assert gate["v3_marker_and_root_must_not_reuse_v2_paths"] is True
    assert gate["v3_darwin_value_must_derive_from_os_getuid_not_geteuid"] is True
    assert gate["v3_currently_authorized"] is False
    assert gate["runtime_approval_rank_training_production_science_authorized"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "extra_top_level",
        "remove_nonclaim",
        "bool_to_int_alias",
        "status_event_count",
        "effective_environment",
        "remove_test_failure",
        "binding_mode",
        "v3_authorized",
    ],
)
def test_rehashed_machine_hostiles_are_rejected(mutation: str) -> None:
    value = _read_json(MACHINE)
    if mutation == "extra_top_level":
        value["extra"] = False
    elif mutation == "remove_nonclaim":
        del value["nonclaims"]["postmortem_network_contacted"]
    elif mutation == "bool_to_int_alias":
        value["nonclaims"]["capture_a_binding_created"] = 0
    elif mutation == "status_event_count":
        value["public_status_defect"]["status_reported_preparation_event_count"] = 3
    elif mutation == "effective_environment":
        del value["failure_diagnosis"][
            "equivalent_profile_probe_effective_environment_internal"
        ]["__CF_USER_TEXT_ENCODING"]
    elif mutation == "remove_test_failure":
        value["frozen_test_defect"]["failures"].pop()
    elif mutation == "binding_mode":
        value["registration_bindings"][0]["mode_octal"] = "0600"
    elif mutation == "v3_authorized":
        value["next_gate"]["v3_currently_authorized"] = True
    forged = _finish_registration(value)
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._validate_machine_registration_payload(WORKSPACE, forged)


@pytest.mark.parametrize(
    ("role", "field", "replacement"),
    [
        ("ATTEMPT_MARKER", "scientific_campaign_nonce_minted", 0),
        ("EVENT_0", "preparation_event_ordinal", True),
        ("RUNTIME_DOUBLE_CAPTURE_REQUEST", "capture_count", True),
        (
            "RUNTIME_CAPTURE_A_LAUNCH_CLAIM",
            "recovery_policy",
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        ),
    ],
)
def test_rehashed_operational_record_hostiles_are_rejected(
    role: str, field: str, replacement: object
) -> None:
    row = next(row for row in POST.RECORD_ROWS if row["role"] == role)
    value = json.loads((WORKSPACE / row["path"]).read_text(encoding="ascii"))
    value[field] = replacement
    digest_key = row["terminal_digest_key"]
    value[digest_key] = None
    value[digest_key] = _sha256(
        row["schema"].encode("ascii") + b"\0" + _canonical(value)
    )
    forged = _canonical(value) + b"\n"
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._parse_canonical_record(forged, row)


def test_absence_mode_link_and_path_hostiles_fail_closed(tmp_path: Path) -> None:
    broken = tmp_path / "broken"
    broken.symlink_to(tmp_path / "missing")
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._assert_absent(broken, "broken symlink")

    payload = tmp_path / "payload"
    payload.write_bytes(b"x")
    payload.chmod(0o644)
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._read_stable_file(tmp_path, "payload", expected_mode=0o600)
    payload.chmod(0o600)
    hardlink = tmp_path / "hardlink"
    os.link(payload, hardlink)
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._read_stable_file(tmp_path, "payload", expected_nlink=1)

    for unsafe in ("/absolute", "../escape", "a/../b", "a\\b", "./a"):
        with pytest.raises(POST.TerminalFailureRegistrationError):
            POST._safe_capsule_path(unsafe)


def test_static_snapshot_digest_uses_field_absence_not_null() -> None:
    machine = _read_json(WORKSPACE / POST.V2_MACHINE_PATH)
    snapshot = copy.deepcopy(machine["static_qualification_snapshot"])
    claimed = snapshot.pop("snapshot_sha256")
    expected = _sha256(
        b"heterodiff-a1-r1-activation-preparation-static-qualification-v2\0"
        + _canonical(snapshot)
    )
    assert claimed == POST.V2_STATIC_SNAPSHOT_SHA256 == expected
    snapshot["snapshot_sha256"] = None
    assert (
        _sha256(
            b"heterodiff-a1-r1-activation-preparation-static-qualification-v2\0"
            + _canonical(snapshot)
        )
        != claimed
    )


def test_qualification_is_loader_only_immutable_and_reopens_sidecar() -> None:
    with pytest.raises(TypeError):
        POST.TerminalFailureQualification()
    qualification = POST.load_qualification()
    assert qualification.record_sha256 == _read_json(MACHINE)["record_sha256"]
    assert qualification.custody()["retry_permitted"] is False
    with pytest.raises(AttributeError):
        qualification.injected = True


def test_validator_is_stdlib_read_only_and_has_no_writer_or_launcher_route() -> None:
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots <= {
        "__future__",
        "hashlib",
        "json",
        "os",
        "stat",
        "unicodedata",
        "pathlib",
        "typing",
    }
    assert "subprocess" not in imported_roots
    assert "secrets" not in imported_roots
    assert "socket" not in imported_roots
    assert "O_CREAT" not in source
    assert "os.write" not in source
    assert "unlink(" not in source
    assert "remove(" not in source
    assert "replace(" not in source
    assert "rename(" not in source
    assert "mkdir(" not in source
    assert "makedirs(" not in source
    assert "if __name__" not in source
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(token in node.name for token in ("write", "launch", "execute", "retry"))
        for node in ast.walk(tree)
    )


def test_publication_boundary_and_no_focused_pyc_are_exact() -> None:
    machine = _read_json(MACHINE)
    boundary = machine["publication_anonymity_boundary"]
    assert (
        boundary
        == POST._expected_fixed_registration()["publication_anonymity_boundary"]
    )
    assert boundary["internal_only"] is True
    assert boundary["anonymous_submission_inclusion_permitted"] is False
    assert boundary["public_release_inclusion_permitted"] is False
    assert boundary["uid_like_effective_environment_value_publication_safe"] is False
    assert boundary["fresh_anonymity_audit_required"] is True
    stems = {
        Path(POST.VALIDATOR_PATH).stem,
        Path(POST.TEST_PATH).stem,
    }
    pycs = [
        path
        for path in WORKSPACE.rglob("*.pyc")
        if any(stem in path.name for stem in stems)
    ]
    assert pycs == []
