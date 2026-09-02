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
    WORKSPACE
    / "research/diagnostics/finite_association_r1_activation_preparation_v3_live_"
    "host_environment_rehearsal_terminal_failure_registration_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "finite_association_r1_activation_preparation_v3_live_host_environment_"
    "rehearsal_terminal_failure_registration_v1",
    VALIDATOR,
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
    raise AssertionError("forbidden live operation reached during terminal audit")


@pytest.fixture(autouse=True)
def _forbid_process_entropy_network(monkeypatch: pytest.MonkeyPatch) -> None:
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


def _read_json(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    record = json.loads(payload.decode("ascii"))
    assert type(record) is dict
    assert payload == _canonical(record) + b"\n"
    return record


def _finish_registration(record: dict[str, object]) -> bytes:
    body = copy.deepcopy(record)
    body["record_sha256"] = None
    body["record_sha256"] = _sha256(POST.REGISTRATION_DOMAIN + _canonical(body))
    return _canonical(body) + b"\n"


def test_four_files_are_additive_and_frozen_v3_bytes_remain_exact() -> None:
    owned = (HUMAN, MACHINE, VALIDATOR, TEST)
    assert all(path.is_file() and not path.is_symlink() for path in owned)
    assert all(stat.S_IMODE(path.lstat().st_mode) == 0o644 for path in owned)
    assert all(path.lstat().st_nlink == 1 for path in owned)
    for row in POST.V3_FREEZE_BINDINGS:
        payload = (WORKSPACE / row["path"]).read_bytes()
        assert len(payload) == row["bytes"]
        assert _sha256(payload) == row["raw_sha256"]
    assert _read_json(WORKSPACE / POST.V3_MACHINE_PATH)["record_sha256"] == (
        POST.V3_MACHINE_RECORD_SHA256
    )


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
    assert record["terminal_state"] == POST.TERMINAL_STATE
    assert record["global_state"] == "DRAFT_NOT_EXECUTABLE"


def test_observation_registers_parent_action_without_inventing_streams() -> None:
    observation = _read_json(MACHINE)["execution_observation"]
    assert observation["canonical_rehearsal_invocation_ordinal"] == 0
    assert observation["canonical_rehearsal_attempt_count"] == 1
    assert observation["canonical_rehearsal_retry_count"] == 0
    assert observation["reported_parent_action_exit_code"] == 70
    assert observation["child_exit_code"] is None
    assert observation["reported_wall_time_less_than_0_01_seconds"] is True
    assert (
        observation["exact_wall_time_lexeme_bound_as_registered_workspace_artifact"]
        is False
    )
    assert observation["tool_output_field_byte_count"] == 0
    assert observation["tool_output_field_sha256"] == _sha256(b"")
    assert observation["tool_output_original_token_count"] == 0
    assert observation["os_level_combined_stream_observation_claimed"] is False
    assert observation["stdout_byte_count_separately_observed"] is None
    assert observation["stderr_byte_count_separately_observed"] is None
    assert observation["typed_result_emitted"] is False
    assert observation["durable_v3_attempt_marker_created"] is False
    assert observation["mechanical_one_shot_enforced"] is False
    assert observation["filesystem_state_alone_can_encode_procedural_spend"] is False
    assert observation["attempt_procedurally_spent"] is True
    assert observation["retry_permitted"] is False


def test_collapsed_failure_preserves_all_unobserved_fields() -> None:
    diagnosis = _read_json(MACHINE)["collapsed_failure_diagnosis"]
    assert diagnosis["failure_stage"] == "UNOBSERVED_COLLAPSED_EXCEPTION"
    for field in (
        "exact_failure_stage",
        "failed_gate",
        "supervisor_gate_vector",
        "child_launch_count",
        "child_exit_code",
        "exception_class",
    ):
        assert diagnosis[field] is None
    assert diagnosis["child_launch_count_directly_observed"] is False
    assert diagnosis["no_child_launch_claimed"] is False
    assert diagnosis["first_possible_source_step"] == (
        "_require_live_supervisor_boundary"
    )
    assert (
        diagnosis["timing_is_consistent_with_but_does_not_localize_an_early_failure"]
        is True
    )
    assert diagnosis["timing_supports_failure_stage_localization"] is False
    assert diagnosis["timing_inference_is_direct_observation"] is False
    assert diagnosis["timing_inference_is_causal_proof"] is False
    assert diagnosis["deterministic_darwin_or_native_argv_cause_claimed"] is False
    assert diagnosis["downstream_stage_absence_claimed"] is False


def test_five_contextual_probes_are_exactly_rostered_and_quarantined() -> None:
    context = _read_json(MACHINE)["post_failure_exploratory_context"]
    assert context["initially_reported_process_count"] == 3
    assert context["first_corrected_process_count"] == 4
    assert context["final_transcript_audited_process_count"] == 5
    assert context["count_correction_chain"] == [3, 4, 5]
    assert context["broad_vector_initially_reported_boolean_count"] == 15
    assert context["broad_vector_corrected_boolean_count"] == 16
    assert context["probe_count"] == 5
    assert context["reported_process_exit_code_vector"] == [0, 0, 0, 0, 0]
    assert context["reported_process_exit_codes_source"] == (
        "IMPLEMENTATION_TRANSCRIPT_TOOL_LOG_REPORT"
    )
    assert (
        context["raw_process_commands_bound_as_registered_workspace_artifacts"] is False
    )
    assert (
        context["raw_process_outputs_bound_as_registered_workspace_artifacts"] is False
    )
    assert context["stderr_streams_separately_observed"] is False
    assert context["probe_ordinal_roster_closed"] is True
    assert context["context_is_canonical_failure_evidence"] is False
    assert context["independently_verified_from_durable_raw_receipts"] is False
    assert context["canonical_rehearsal_attempts_added"] == 0
    assert context["canonical_retry_count_added"] == 0
    assert context["further_contextual_probe_permitted"] is False
    assert context["transcript_reported_authority_module_invocation_count"] == 0
    assert context["transcript_reported_runtime_child_invocation_count"] == 0
    assert context["transcript_reported_project_module_import_count"] == 0
    assert (
        context["transcript_reported_explicit_application_entropy_api_call_count"] == 0
    )
    assert (
        context["transcript_reported_explicit_application_network_api_call_count"] == 0
    )
    assert (
        context["transcript_reported_explicit_application_workspace_output_write_count"]
        == 0
    )
    assert context["os_level_entropy_contact_independently_observed"] is None
    assert context["os_level_network_contact_independently_observed"] is None
    assert context["os_level_filesystem_effects_independently_observed"] is None
    assert context["transcript_reported_raw_uid_cf_or_absolute_path_output_count"] == 0
    assert context["transcript_reported_output_shape"] == (
        "BOOLEAN_ONLY_PRIVACY_SAFE_CONTEXT"
    )
    assert (
        context[
            "reported_probe_safety_facts_independently_verified_from_durable_receipts"
        ]
        is False
    )
    assert context["covered_by_frozen_rehearsal_route"] is False
    assert context["separate_exact_user_authorization_bound"] is False
    assert context["authorization_for_contextual_probes_claimed"] is False
    rows = context["probe_roster"]
    assert rows == list(POST.PROBE_ROSTER)
    assert [row["ordinal"] for row in rows] == list(range(5))
    assert len(POST.PROBE_ZERO_FIELD_ROSTER) == 16
    assert len(set(POST.PROBE_ZERO_FIELD_ROSTER)) == 16
    assert rows[0]["reported_fields"] == [
        "cpython_3_11_5",
        "cwd_matches_expected",
        "darwin_arm64",
        "darwin_key_present",
        "darwin_value_matches_uid",
        "effective_environment_count_17",
        "gid_egid_equal",
        "hash_probe_matches",
        "nonroot",
        "normalized_environment_exact16",
        "process_taint_absent",
        "python_flags_exact",
        "site_absent",
        "supplemental_root_group_absent",
        "sys_path_exact",
        "uid_euid_equal",
    ]
    assert all(rows[0]["reported_values"].values())
    for row in rows:
        assert row["reported_process_exit_code"] == 0
        assert list(row["reported_values"]) == row["reported_fields"]
        assert row["cross_process_transfer_permitted"] is False
        assert row["canonical_failure_process_binding"] is False


def test_status_defect_is_inference_only_and_cannot_authorize_retry() -> None:
    defect = _read_json(MACHINE)["frozen_status_defect"]
    assert defect["status_projection_source"] == (
        "FROZEN_SOURCE_PLUS_LSTAT_ABSENCE_INFERENCE"
    )
    assert defect["direct_status_invocation_used_as_postmortem_evidence"] is False
    assert (
        defect["post_failure_status_raw_receipt_bound_as_registered_workspace_artifact"]
        is False
    )
    assert defect["frozen_status_result_state"] == "ABSENT"
    assert defect["frozen_status_milestone_state"] == POST.FROZEN_PRE_RUN_STATE
    assert defect["procedurally_spent_attempt_represented"] is False
    assert defect["empty_tool_output_exit_without_result_represented"] is False
    assert defect["transition_complete_for_no_result_attempt"] is False
    assert defect["absent_v3_filesystem_is_indistinguishable_from_true_pre_run"] is True
    assert defect["frozen_status_must_not_authorize_retry"] is True


def test_terminal_loader_reopens_v3_v2_and_all_absence_gates() -> None:
    custody = POST.audit_terminal_custody()
    assert custody["v3_freeze_binding_count"] == 6
    assert custody["v3_machine_record_sha256"] == POST.V3_MACHINE_RECORD_SHA256
    assert custody["v3_result_lstat_absent"] is True
    assert custody["v3_marker_lstat_absent"] is True
    assert custody["v3_root_lstat_absent"] is True
    assert custody["v2_validated_preparation_event_count"] == 3
    assert custody["v2_validated_current_head_sha256"] == POST.V2_VALIDATED_HEAD_SHA256
    assert custody["v2_terminal_registration_bindings"] == [
        dict(row) for row in POST.V2_POSTMORTEM_BINDINGS
    ]
    projection = custody["v2_terminal_custody_projection"]
    assert projection["preparation_file_count"] == 65
    assert projection["preparation_directory_count"] == 20
    assert projection["capsule"] == custody["v2_capsule"]
    assert projection["validated_preparation_event_count"] == 3
    assert projection["validated_current_head_sha256"] == POST.V2_VALIDATED_HEAD_SHA256
    assert projection["capture_a_launch_claim_spent"] is True
    assert projection["capture_a_binding_present"] is False
    assert projection["capture_b_launch_claim_present"] is False
    assert projection["runtime_candidate_present"] is False
    assert projection["execution_authorized"] is False
    assert custody["v2_attempt_marker_bytes"] == 2171
    assert custody["v2_attempt_marker_raw_sha256"] == (
        POST.V2_ATTEMPT_MARKER_RAW_SHA256
    )
    assert custody["v2_preparation_file_count"] == 65
    assert custody["v2_preparation_directory_count"] == 20
    assert custody["v2_preparation_file_mode_octal"] == "0600"
    assert custody["v2_preparation_directory_mode_octal"] == "0700"
    assert custody["v2_preparation_files_nlink_one"] is True
    assert custody["v2_preparation_symlink_count"] == 0
    assert custody["v2_capsule"] == {
        "all_rows_reopened_twice": True,
        "closed_world_verified": True,
        "directory_count": 14,
        "file_count": 53,
        "inventory_sha256": (
            "c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360"
        ),
    }
    assert custody["v2_marker_attempt_spent"] is True
    assert custody["v2_retry_permitted"] is False
    assert custody["v2_execution_authorized"] is False
    assert custody["frozen_predecessor_pyc_paths"] == []


def test_state_preservation_and_v4_boundary_authorize_nothing() -> None:
    record = _read_json(MACHINE)
    scope = record["scope"]
    assert scope["frozen_v3_files_edited"] is False
    assert scope["v2_custody_edited"] is False
    assert scope["isolated_pytest_temporary_fixture_custody_exercised"] is True
    assert scope["synthetic_fixture_writes_are_noncanonical_and_nonoperational"] is True
    assert scope["synthetic_fixture_operation_roster"] == [
        "CREATE_PAYLOAD",
        "CHMOD",
        "HARDLINK",
        "SYMLINK",
        "UNLINK",
        "FAKE_PYC",
        "SYNTHETIC_FUTURE_SUCCESSOR_ENTRY",
    ]
    assert scope["canonical_v2_or_v3_operational_path_mutated_by_hostiles"] is False
    assert scope["canonical_predecessor_paths_read_for_audit"] is True
    preservation = record["state_preservation"]
    assert preservation["underlying_rosters_recomputed_by_postmortem"] is False
    assert preservation["unresolved_null_count"] == 172
    assert preservation["open_blocker_count"] == 12
    assert preservation["d1_quarantine_row_count"] == 550
    assert preservation["d1_quarantine_roster_sha256"] == (
        "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
    )
    assert preservation["d1_execution_admissible"] is False
    boundary = record["future_v4_boundary"]
    assert boundary["v3_namespace_reuse_permitted"] is False
    assert boundary["future_v3_physical_absence_mechanically_guaranteed"] is False
    assert boundary["exact_future_v4_operational_paths_frozen_here"] is False
    assert boundary["postmortem_defines_or_claims_exact_v4_operational_path"] is False
    assert boundary["durable_loader_revalidates_future_v4_absence"] is False
    assert boundary["future_v4_must_be_wholly_disjoint_from_v2_and_v3"] is True
    assert (
        boundary[
            "future_v4_must_bind_all_four_terminal_registration_files_by_raw_sha256"
        ]
        is True
    )
    assert boundary["future_v4_must_bind_this_registration_record_sha256"] is True
    assert boundary["future_v4_loader_must_revalidate_v3_terminal_custody"] is True
    assert boundary["v3_canonical_attempt_count_to_carry"] == 1
    assert boundary["v3_retry_count_to_carry"] == 0
    assert boundary["v3_terminal_state_to_carry"] == POST.TERMINAL_STATE
    assert boundary["v4_is_new_disjoint_version_attempt_not_v3_retry"] is True
    assert (
        boundary["v3_spent_namespace_must_be_reopened_before_any_v4_authority_route"]
        is True
    )
    assert boundary["fresh_exact_user_authorization_required"] is True
    assert (
        boundary[
            "typed_privacy_safe_supervisor_failure_receipt_required_for_every_prechild_failure"
        ]
        is True
    )
    assert (
        boundary["typed_prechild_admission_receipt_required_before_any_child_launch"]
        is True
    )
    assert (
        boundary["outer_transport_must_preserve_failure_or_admission_typed_outcome"]
        is True
    )
    assert boundary["fresh_disjoint_v4_attempt_identity_and_nonce_required"] is True
    assert (
        boundary[
            "durable_no_clobber_v4_attempt_spend_required_before_any_live_evaluation"
        ]
        is True
    )
    assert boundary["v4_attempt_spend_publication_must_use_o_excl_and_fsync"] is True
    assert (
        boundary[
            "if_v4_nonce_uses_entropy_durable_o_excl_reservation_must_precede_sole_draw"
        ]
        is True
    )
    assert (
        boundary["v4_partial_reservation_or_postdraw_failure_must_be_terminal_spent"]
        is True
    )
    assert boundary["v4_sole_writer_ledger_or_equivalent_required"] is True
    assert (
        boundary[
            "v4_typed_terminal_outcome_must_be_no_clobber_locally_persisted_independent_of_stdout_or_tool_transport"
        ]
        is True
    )
    assert boundary["v4_replay_or_retry_must_fail_closed"] is True
    assert boundary["v4_authorized_at_terminal_registration"] is False
    assert (
        boundary["runtime_approval_rank_training_production_science_authorized"]
        is False
    )
    assert all(value is False for value in record["nonclaims"].values())


def test_loader_only_qualification_and_status_are_terminal() -> None:
    with pytest.raises(TypeError):
        POST.TerminalFailureQualification()
    qualification = POST.load_qualification()
    assert qualification.record_sha256 == _read_json(MACHINE)["record_sha256"]
    with pytest.raises(AttributeError):
        qualification.injected = True
    observed = POST.status()
    assert observed["terminal_state"] == POST.TERMINAL_STATE
    assert observed["canonical_rehearsal_attempt_count"] == 1
    assert observed["canonical_rehearsal_retry_count"] == 0
    assert observed["parent_action_exit_code"] == 70
    assert observed["failure_stage"] == "UNOBSERVED_COLLAPSED_EXCEPTION"
    assert observed["failed_gate"] is None
    assert observed["child_launch_count"] is None
    assert observed["post_failure_context_process_count"] == 5
    assert observed["post_failure_context_admissible_as_canonical_evidence"] is False
    assert observed["retry_permitted"] is False
    assert observed["execution_authorized"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "stage",
        "child_count",
        "wall_time",
        "tool_output",
        "probe_count",
        "probe_value",
        "probe_transfer",
        "count_correction",
        "status_retry",
        "v4_path_freeze",
        "binding",
        "nonclaim",
    ],
)
def test_rehashed_registration_hostiles_are_rejected(mutation: str) -> None:
    record = _read_json(MACHINE)
    if mutation == "stage":
        record["collapsed_failure_diagnosis"][
            "exact_failure_stage"
        ] = "SUPERVISOR_BOUNDARY"
    elif mutation == "child_count":
        record["collapsed_failure_diagnosis"]["child_launch_count"] = 0
    elif mutation == "wall_time":
        record["execution_observation"][
            "reported_wall_time_less_than_0_01_seconds"
        ] = False
    elif mutation == "tool_output":
        record["execution_observation"]["tool_output_field_byte_count"] = 1
    elif mutation == "probe_count":
        record["post_failure_exploratory_context"]["probe_count"] = 4
    elif mutation == "probe_value":
        record["post_failure_exploratory_context"]["probe_roster"][0][
            "reported_values"
        ]["hash_probe_matches"] = False
    elif mutation == "probe_transfer":
        record["post_failure_exploratory_context"]["probe_roster"][4][
            "cross_process_transfer_permitted"
        ] = True
    elif mutation == "count_correction":
        record["post_failure_exploratory_context"]["count_correction_chain"] = [
            3,
            5,
        ]
    elif mutation == "status_retry":
        record["frozen_status_defect"]["frozen_status_must_not_authorize_retry"] = False
    elif mutation == "v4_path_freeze":
        record["future_v4_boundary"][
            "exact_future_v4_operational_paths_frozen_here"
        ] = True
    elif mutation == "binding":
        record["registration_bindings"][0]["nlink"] = 2
    elif mutation == "nonclaim":
        record["nonclaims"]["postmortem_authorized_v4"] = True
    forged = _finish_registration(record)
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._validate_machine_payload(WORKSPACE, forged)


def test_path_mode_link_and_ancestor_hostiles_fail_closed(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.write_bytes(b"payload")
    payload.chmod(0o644)
    assert POST._read_stable_file(tmp_path, "payload")[0] == b"payload"
    payload.chmod(0o600)
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._read_stable_file(tmp_path, "payload")
    payload.chmod(0o644)
    hardlink = tmp_path / "hardlink"
    os.link(payload, hardlink)
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._read_stable_file(tmp_path, "payload")
    hardlink.unlink()

    real = tmp_path / "real"
    real.mkdir()
    (real / "row").write_bytes(b"row")
    (real / "row").chmod(0o644)
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(POST.TerminalFailureRegistrationError):
        POST._read_stable_file(tmp_path, "linked/row")

    broken = tmp_path / "broken"
    broken.symlink_to(tmp_path / "missing")
    assert POST._path_has_entry(broken) is True
    for unsafe in ("/absolute", "../escape", "a/../b", "./a", "a//b", "a\\b"):
        with pytest.raises(POST.TerminalFailureRegistrationError):
            POST._normalized_relative_path(unsafe)


def test_disjoint_synthetic_future_successor_entries_do_not_invalidate_v3_terminal_state(
    tmp_path: Path,
) -> None:
    future_root = tmp_path / "artifacts/synthetic_future_successor/root"
    future_root.mkdir(parents=True)
    (tmp_path / "artifacts/synthetic_future_successor.marker.json").write_bytes(
        b"synthetic-future"
    )
    future_result = (
        tmp_path / "research/fixtures/synthetic_future_successor_result.json"
    )
    future_result.parent.mkdir(parents=True)
    future_result.write_bytes(b"synthetic-future")
    absences = POST._v3_terminal_namespace_absences(tmp_path)
    assert set(absences) == {
        "v3_result_lstat_absent",
        "v3_marker_lstat_absent",
        "v3_root_lstat_absent",
    }
    assert all(absences.values())
    assert not any(name.startswith("V4_") for name in vars(POST))
    spent_v3_marker = tmp_path / POST.V3_MARKER_PATH
    spent_v3_marker.write_bytes(b"forbidden-v3-reuse")
    assert (
        POST._v3_terminal_namespace_absences(tmp_path)["v3_marker_lstat_absent"]
        is False
    )


def test_validator_has_no_writer_launcher_probe_or_duplicate_dict_key() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Dict):
            literal_keys = [
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            ]
            assert len(literal_keys) == len(set(literal_keys))
    assert imported_roots <= {
        "__future__",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "stat",
        "types",
        "typing",
    }
    assert "subprocess" not in imported_roots
    assert "secrets" not in imported_roots
    assert "socket" not in imported_roots
    for forbidden in (
        "O_CREAT",
        "os.write",
        "unlink(",
        "remove(",
        "replace(",
        "rename(",
        "mkdir(",
        "makedirs(",
        "token_bytes",
        "Popen",
        "if __name__",
    ):
        assert forbidden not in source


def test_loader_pyc_does_not_self_invalidate_but_predecessor_pyc_is_custody(
    tmp_path: Path,
) -> None:
    own_cache = tmp_path / "research/diagnostics/__pycache__"
    own_cache.mkdir(parents=True)
    own_cache.joinpath(Path(POST.VALIDATOR_PATH).stem + ".cpython-311.pyc").write_bytes(
        b"cache"
    )
    assert POST._frozen_predecessor_pyc_paths(tmp_path) == ()
    frozen_cache = tmp_path / "research/production/__pycache__"
    frozen_cache.mkdir(parents=True)
    name = Path(POST.V3_AUTHORITY_PATH).stem + ".cpython-311.pyc"
    frozen_cache.joinpath(name).write_bytes(b"cache")
    assert POST._frozen_predecessor_pyc_paths(tmp_path) == (
        "research/production/__pycache__/" + name,
    )


def test_stable_checkpoint_has_no_focused_pyc_and_no_private_carriers() -> None:
    stems = {
        Path(POST.V3_CONTRACTS_PATH).stem,
        Path(POST.V3_AUTHORITY_PATH).stem,
        Path(POST.V3_RUNTIME_PATH).stem,
        Path(POST.V3_TEST_PATH).stem,
        Path(POST.VALIDATOR_PATH).stem,
        Path(POST.TEST_PATH).stem,
    }
    focused_pycs = [
        path
        for path in WORKSPACE.rglob("*.pyc")
        if any(stem in path.name for stem in stems)
    ]
    assert focused_pycs == []
    user_path_prefix = b"/" + b"Users" + b"/"
    darwin_key = b"__CF_USER_" + b"TEXT_ENCODING"
    for path in (HUMAN, MACHINE, VALIDATOR, TEST):
        payload = path.read_bytes()
        assert user_path_prefix not in payload
        assert darwin_key not in payload
