from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import pytest


WORKSPACE = Path(__file__).resolve().parents[2]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from research.production import (
    finite_association_r1_activation_preparation_authority_v2 as authority,
)
from research.production import (
    finite_association_r1_activation_preparation_contracts_v2 as contracts,
)
from research.production import (
    finite_association_r1_activation_preparation_runtime_v2 as runtime,
)


HUMAN = WORKSPACE / authority.HUMAN_PATH
MACHINE = WORKSPACE / authority.MACHINE_PATH
CONTRACTS = WORKSPACE / authority.CONTRACTS_PATH
AUTHORITY = WORKSPACE / authority.AUTHORITY_PATH
RUNTIME = WORKSPACE / authority.RUNTIME_PATH
TEST = WORKSPACE / authority.TEST_PATH
OWNED_PATHS = (HUMAN, MACHINE, CONTRACTS, AUTHORITY, RUNTIME, TEST)
SHA = "a" * 64


@pytest.fixture(autouse=True)
def _zero_live_entropy_or_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("focused suite must not contact entropy or launch a child")

    monkeypatch.setattr(authority.secrets, "token_bytes", forbidden)
    monkeypatch.setattr(authority.subprocess, "Popen", forbidden)


def _canonical(value: object) -> bytes:
    return contracts.canonical_json(value)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    value = json.loads(payload.decode("ascii"))
    assert type(value) is dict
    assert payload == _canonical(value) + b"\n"
    return value


def _all_existing_relative_files(value: object) -> set[str]:
    result: set[str] = set()
    if type(value) is dict:
        for key, item in value.items():
            result.update(_all_existing_relative_files(key))
            result.update(_all_existing_relative_files(item))
    elif type(value) is list:
        for item in value:
            result.update(_all_existing_relative_files(item))
    elif type(value) is str and value and not value.startswith("/"):
        candidate = Path(value)
        allowed_roots = {
            "artifacts",
            "manuscript_v3",
            "research",
            "src",
            "requirements",
            "tests",
            "pyproject.toml",
        }
        if (
            candidate.parts
            and ".." not in candidate.parts
            and candidate.parts[0] in allowed_roots
        ):
            absolute = WORKSPACE / candidate
            try:
                if absolute.is_file() and not absolute.is_symlink():
                    result.add(candidate.as_posix())
            except OSError:
                pass
    return result


def _replica(tmp_path: Path) -> Path:
    root = tmp_path / "replica"
    root.mkdir(mode=0o700, parents=True)
    predecessor = _read_json(WORKSPACE / authority.PREDECESSOR_MACHINE_PATH)
    current = _read_json(MACHINE)
    relative_files = _all_existing_relative_files(predecessor)
    relative_files.update(_all_existing_relative_files(current))
    relative_files.update(
        path.relative_to(WORKSPACE).as_posix() for path in OWNED_PATHS
    )
    relative_files.update(authority.PREDECESSOR_RAW_SHA256)
    relative_files.update(authority.v1_authority.PREDECESSOR_RAW_SHA256)
    relative_files.update(authority.v1_authority.D1_REQUIRED_RAW_SHA256)
    relative_files.update(
        {
            authority.v1_authority.D1_ATTEMPT_PATH,
            authority.v1_authority.D1_SUCCESS_PATH,
            authority.v1_authority.V2_SUCCESS_PATH,
        }
    )
    inspected_json: set[str] = set()
    while True:
        json_paths = {
            relative
            for relative in relative_files
            if relative.endswith(".json") and relative not in inspected_json
        }
        if not json_paths:
            break
        for relative in sorted(json_paths):
            inspected_json.add(relative)
            path = WORKSPACE / relative
            if not path.is_file() or path.is_symlink():
                continue
            try:
                value = json.loads(path.read_text())
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            relative_files.update(_all_existing_relative_files(value))
    for relative in sorted(relative_files):
        source = WORKSPACE / relative
        if not source.is_file() or source.is_symlink():
            continue
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=False)
    (root / "artifacts").mkdir(mode=0o700, exist_ok=True)
    _refresh_replica_registration(root)
    return root


def _refresh_replica_registration(root: Path) -> None:
    machine = root / authority.MACHINE_PATH
    record = json.loads(machine.read_text())
    snapshot = authority.static_qualification_snapshot(root)
    bindings = []
    expected = (
        ("HUMAN_REGISTRATION", authority.HUMAN_PATH),
        ("CONTRACTS_MODULE", authority.CONTRACTS_PATH),
        ("AUTHORITY_MODULE", authority.AUTHORITY_PATH),
        ("RUNTIME_MODULE", authority.RUNTIME_PATH),
        ("HOSTILE_TEST", authority.TEST_PATH),
    )
    for ordinal, (role, relative) in enumerate(expected):
        path = root / relative
        payload = path.read_bytes()
        bindings.append(
            {
                "ordinal": ordinal,
                "role": role,
                "path": relative,
                "bytes": len(payload),
                "raw_sha256": _sha256(payload),
                "lf_only": b"\r" not in payload,
                "is_regular_file": True,
                "is_symlink": False,
            }
        )
    record["static_qualification_snapshot"] = snapshot
    record["nonclaims"] = authority.NONCLAIMS
    record["publication_anonymity_boundary"] = authority.PUBLICATION_ANONYMITY_BOUNDARY
    record["next_gate"] = authority.next_gate(snapshot)
    record["registration_bindings"] = bindings
    record["record_sha256"] = None
    record["record_sha256"] = _sha256(
        authority.REGISTRATION_DOMAIN + _canonical(record)
    )
    machine.write_bytes(_canonical(record) + b"\n")


def _rehashed(record: dict[str, object], contract_id: str) -> dict[str, object]:
    value = copy.deepcopy(record)
    digest_key = contracts.CONTRACTS[contract_id][1]
    value[digest_key] = None
    schema = contracts.CONTRACTS[contract_id][0]
    value[digest_key] = _sha256(schema.encode("ascii") + b"\0" + _canonical(value))
    return value


def _patch_runtime_replica(monkeypatch: pytest.MonkeyPatch, root: Path) -> Path:
    venv = root / ".venv-m1"
    site_packages = root / runtime.SITE_PACKAGES_RELATIVE_PATH
    site_packages.mkdir(parents=True, mode=0o700)
    (site_packages / "synthetic-runtime-row.txt").write_bytes(b"frozen\n")
    system_roots = tuple(
        row
        for row in runtime.APPROVED_PATH_ROOTS
        if row[0] not in {"<WORKSPACE>", "<VENV>"}
    )
    monkeypatch.setattr(runtime, "HOST_WORKSPACE_ROOT", root)
    monkeypatch.setattr(runtime, "WORKSPACE_ROOT", root)
    monkeypatch.setattr(
        runtime,
        "APPROVED_PATH_ROOTS",
        (("<WORKSPACE>", root), ("<VENV>", venv), *system_roots),
    )
    return site_packages


def _synthetic_raw_envelope(
    root: Path,
    request: dict[str, object],
    ordinal: int,
    *,
    platform_release: str = "SYNTHETIC_STABLE_RELEASE",
) -> bytes:
    capsule_inventory = runtime._closed_file_roster(
        root / authority.CAPSULE_ROOT, runtime.CAPSULE_FILE_ROSTER_DOMAIN
    )
    installed_inventory = runtime._closed_file_roster(
        root / runtime.SITE_PACKAGES_RELATIVE_PATH,
        runtime.INSTALLED_FILE_ROSTER_DOMAIN,
    )
    distributions = runtime._distribution_roster(
        root / runtime.SITE_PACKAGES_RELATIVE_PATH
    )
    observation = {
        "schema": runtime.RAW_OBSERVATION_SCHEMA,
        "request_sha256": request["request_sha256"],
        "capture_ordinal": ordinal,
        "target_profile_id": runtime.TARGET_PROFILE_ID,
        "python": {
            "executable": (root / runtime.PYTHON_RELATIVE_PATH).as_posix(),
            "executable_realpath": runtime.EXPECTED_INTERPRETER_REALPATH,
            "implementation": "CPython",
            "version": "3.11.0",
            "version_info": [3, 11, 0, "final", 0],
            "flags": {
                "isolated": 1,
                "no_site": 1,
                "dont_write_bytecode": 1,
                "safe_path": True,
                "utf8_mode": 1,
                "ignore_environment": 1,
                "no_user_site": 1,
            },
            "sys_path": list(runtime.EXPECTED_ISOLATED_SYS_PATH),
        },
        "platform": {
            "system": "Darwin",
            "release": platform_release,
            "machine": "arm64",
            "python_compiler": "Clang synthetic",
        },
        "environment": dict(runtime.CAPTURE_ENVIRONMENT),
        "source_capsule_manifest_sha256": request["source_capsule_manifest_sha256"],
        "source_capsule_inventory": capsule_inventory,
        "installed_files_inventory": installed_inventory,
        "installed_distributions": distributions,
        "complete_installed_file_verification": True,
        "network_contacted": False,
        "scientific_compute_executed": False,
        "approved": False,
        "observation_sha256": None,
    }
    observation["observation_sha256"] = _sha256(
        runtime.RAW_OBSERVATION_DOMAIN + _canonical(observation)
    )
    envelope = {
        "schema": runtime.RAW_ENVELOPE_SCHEMA,
        "request_sha256": request["request_sha256"],
        "capture_ordinal": ordinal,
        "observation": observation,
        "observation_raw_sha256": _sha256(_canonical(observation) + b"\n"),
        "observation_record_sha256": observation["observation_sha256"],
        "raw_envelope_persisted": False,
        "envelope_sha256": None,
    }
    envelope["envelope_sha256"] = _sha256(
        runtime.RAW_ENVELOPE_DOMAIN + _canonical(envelope)
    )
    return _canonical(envelope) + b"\n"


def _synthetic_child_receipt(
    root: Path, payload: bytes, ordinal: int
) -> dict[str, object]:
    return {
        "child_process_id": 41001 + ordinal,
        "child_exit_code": 0,
        "child_stdout_byte_count": len(payload),
        "child_stderr_byte_count": 0,
        "child_oracle_raw_sha256": _sha256(
            (root / authority.RUNTIME_PATH).read_bytes()
        ),
        "child_oracle_api_sha256": authority.RUNTIME_ORACLE_API_SHA256,
    }


def _prepare_capsule(root: Path, nonce: bytes = b"p" * 32) -> None:
    authority._test_publish_marker(root, nonce)
    authority._execute_capsule_at_root(root)


def test_owned_paths_are_exactly_additive_and_no_operational_output_exists() -> None:
    assert all(path.is_file() and not path.is_symlink() for path in OWNED_PATHS)
    assert not authority._path_has_entry(WORKSPACE / authority.MARKER_PATH)
    assert not authority._path_has_entry(WORKSPACE / authority.PREPARATION_ROOT)
    for relative in authority.DORMANT_V1_PATHS:
        assert not authority._path_has_entry(WORKSPACE / relative)
    assert not authority._path_has_entry(
        WORKSPACE / authority.PERMANENTLY_ABSENT_V1_SRC_ADAPTER
    )


def test_machine_registration_is_canonical_self_digested_and_exactly_bound() -> None:
    record = _read_json(MACHINE)
    assert set(record) == {
        "schema_version",
        "registration_id",
        "registration_mode",
        "scope",
        "milestone_state",
        "global_state",
        "static_qualification_snapshot",
        "nonclaims",
        "publication_anonymity_boundary",
        "next_gate",
        "registration_bindings",
        "record_sha256",
    }
    body = copy.deepcopy(record)
    claimed = body["record_sha256"]
    body["record_sha256"] = None
    assert claimed == _sha256(authority.REGISTRATION_DOMAIN + _canonical(body))
    authority._load_registration(WORKSPACE)
    assert record["milestone_state"] == contracts.MILESTONE_STATE
    assert record["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert record["nonclaims"] == authority.NONCLAIMS
    assert record["publication_anonymity_boundary"] == (
        authority.PUBLICATION_ANONYMITY_BOUNDARY
    )
    expected_paths = [HUMAN, CONTRACTS, AUTHORITY, RUNTIME, TEST]
    rows = record["registration_bindings"]
    assert len(rows) == len(expected_paths)
    for ordinal, (row, path) in enumerate(zip(rows, expected_paths)):
        payload = path.read_bytes()
        assert row["ordinal"] == ordinal
        assert row["path"] == path.relative_to(WORKSPACE).as_posix()
        assert row["bytes"] == len(payload)
        assert row["raw_sha256"] == _sha256(payload)
        assert row["lf_only"] is True and b"\r" not in payload
        assert row["is_regular_file"] is True
        assert row["is_symlink"] is False


def test_static_snapshot_reopens_predecessor_capsule_and_d1_custody() -> None:
    snapshot = authority.static_qualification_snapshot(WORKSPACE)
    assert snapshot["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert snapshot["current_unresolved_null_count"] == 172
    assert snapshot["current_open_blocker_count"] == 12
    assert snapshot["capsule_content_plan"]["row_count"] == 53
    assert snapshot["capsule_content_plan"]["local_package_source_count"] == 47
    assert snapshot["capsule_content_plan"]["nonpackage_input_count"] == 3
    assert snapshot["capsule_content_plan"]["protocol_copy_count"] == 3
    assert snapshot["d1_quarantine"]["row_count"] == 550
    assert snapshot["d1_quarantine"]["roster_sha256"] == (
        "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
    )
    assert (
        snapshot["runtime_protocol"][
            "runtime_inspection_oracle_is_outside_scientific_capsule"
        ]
        is True
    )
    assert snapshot["runtime_protocol"]["capture_count"] == 2
    assert snapshot["nonclaims_scope"] == "CANONICAL_LIVE_WORKSPACE_AT_FREEZE"
    assert snapshot["synthetic_temp_replica_testing_disclosed"] is True
    assert (
        snapshot["synthetic_temp_replica_testing_contacted_entropy_or_child_process"]
        is False
    )
    assert snapshot["implemented_writer_routes"] == {
        "precreation_marker_and_nonce": True,
        "deterministic_capsule_materialization_and_admission": True,
        "privacy_safe_runtime_double_capture_candidate": True,
        "preparation_ledger": True,
        "scientific_authority_ledger": False,
    }


def test_status_is_zero_write_transition_aware_and_initially_awaiting_authorization() -> None:
    before = {
        path: path.lstat() if authority._path_has_entry(path) else None
        for path in (
            WORKSPACE / authority.MARKER_PATH,
            WORKSPACE / authority.PREPARATION_ROOT,
        )
    }
    observed = authority.status(WORKSPACE)
    after = {
        path: path.lstat() if authority._path_has_entry(path) else None
        for path in before
    }
    assert before == after
    assert observed["live_transition"] == {
        "live_state": "AWAITING_EXPLICIT_MARKER_AUTHORIZATION",
        "marker_present": False,
        "marker_attempt_spent": False,
        "preparation_event_count": 0,
        "closed": False,
        "retry_permitted": False,
        "execution_authorized": False,
    }
    assert observed["current_unresolved_null_count"] == 172
    assert observed["current_open_blocker_count"] == 12
    assert observed["execution_authorized"] is False


def test_contract_catalog_has_exact_nine_closed_type_strict_records() -> None:
    catalog = contracts.contract_catalog()
    assert catalog["record_count"] == 9
    assert catalog["issued_record_count"] == 0
    assert [row["ordinal"] for row in catalog["records"]] == list(range(9))
    assert len({row["schema"] for row in catalog["records"]}) == 9
    marker = {name: None for name in contracts.MARKER_FIELDS}
    for name, specification in contracts.MARKER_FIELDS.items():
        kind, argument = specification
        if kind == "literal":
            marker[name] = copy.deepcopy(argument)
        elif kind == "sha256":
            marker[name] = SHA
        elif kind == "string":
            marker[name] = "x"
    marker["marker_sha256"] = None
    checked = contracts.finish_record(marker, "ATTEMPT_MARKER")
    hostile = dict(checked)
    hostile["entropy_byte_count"] = True
    hostile = _rehashed(hostile, "ATTEMPT_MARKER")
    with pytest.raises(contracts.ContractError):
        contracts.validate_record(hostile, "ATTEMPT_MARKER")
    hostile = dict(checked)
    hostile["extra"] = False
    with pytest.raises(contracts.ContractError):
        contracts.validate_record(hostile, "ATTEMPT_MARKER")


def test_runtime_request_preimage_policy_and_type_strictness() -> None:
    marker = {
        "marker_sha256": SHA,
        "preparation_instance_nonce_sha256": "b" * 64,
    }
    genesis = {"genesis_sha256": "c" * 64}
    manifest = {"manifest_sha256": "d" * 64}
    admission = {"admission_sha256": "e" * 64}
    request = authority._runtime_request(marker, genesis, manifest, admission)
    assert runtime.validate_runtime_request(request) == request
    assert request["launch_binding_preimage_sha256"] not in {
        request["launch_binding_a_sha256"],
        request["launch_binding_b_sha256"],
    }
    assert request["launch_binding_a_sha256"] != request["launch_binding_b_sha256"]
    hostile = dict(request)
    hostile["capture_count"] = True
    hostile = _rehashed(hostile, "RUNTIME_REQUEST")
    with pytest.raises(contracts.ContractError):
        runtime.validate_runtime_request(hostile)
    hostile = dict(request)
    hostile["launch_binding_preimage_sha256"] = "f" * 64
    hostile = _rehashed(hostile, "RUNTIME_REQUEST")
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.validate_runtime_request(hostile)


def test_runtime_environment_policy_and_small_inventory_roundtrip(
    tmp_path: Path,
) -> None:
    policy = runtime.environment_policy()
    body = dict(policy)
    claimed = body.pop("policy_sha256")
    assert claimed == _sha256(runtime.ENVIRONMENT_POLICY_DOMAIN + _canonical(body))
    assert policy["replacement_environment"] == runtime.CAPTURE_ENVIRONMENT
    assert "PYTHONPATH" not in policy["replacement_environment"]
    assert "PYTHONHOME" not in policy["replacement_environment"]
    root = tmp_path / "inventory"
    root.mkdir()
    child = root / "child"
    child.mkdir()
    (child / "row.bin").write_bytes(b"abc")
    roster = runtime._closed_file_roster(root, runtime.CAPSULE_FILE_ROSTER_DOMAIN)
    assert (
        runtime._validate_inventory(roster, runtime.CAPSULE_FILE_ROSTER_DOMAIN, root)
        == roster
    )
    hostile = copy.deepcopy(roster)
    hostile["directories"].append("empty-extra")
    body = dict(hostile)
    body.pop("manifest_sha256")
    hostile["manifest_sha256"] = _sha256(
        runtime.CAPSULE_FILE_ROSTER_DOMAIN + _canonical(body)
    )
    with pytest.raises(runtime.RuntimePreparationError):
        runtime._validate_inventory(hostile, runtime.CAPSULE_FILE_ROSTER_DOMAIN, root)


def test_runtime_path_tokenizer_rejects_unclassified_and_noncanonical_paths() -> None:
    workspace_value = (runtime.HOST_WORKSPACE_ROOT / "x").as_posix()
    assert runtime._tokenize_absolute_path(workspace_value) == "<WORKSPACE>/x"
    with pytest.raises(runtime.RuntimePreparationError):
        runtime._tokenize_absolute_path("/unexpected-root/private-value")
    with pytest.raises(runtime.RuntimePreparationError):
        runtime._tokenize_absolute_path(
            runtime.HOST_WORKSPACE_ROOT.as_posix() + "/child/../secret"
        )


def test_source_ast_has_one_entropy_call_and_no_public_injection_or_scientific_route() -> None:
    authority_tree = ast.parse(AUTHORITY.read_text())
    entropy_calls = [
        node
        for node in ast.walk(authority_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "secrets"
        and node.func.attr == "token_bytes"
    ]
    assert len(entropy_calls) == 1
    call = entropy_calls[0]
    assert len(call.args) == 1 and isinstance(call.args[0], ast.Constant)
    assert call.args[0].value == 32
    functions = {
        node.name: node
        for node in authority_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    live = functions["_execute_marker_live"]
    source = ast.get_source_segment(AUTHORITY.read_text(), live)
    assert source is not None
    assert source.index("_reserve_marker_inode") < source.index(
        "secrets.token_bytes(32)"
    )
    assert "raw_nonce" not in [argument.arg for argument in live.args.args]
    reserve_source = ast.get_source_segment(
        AUTHORITY.read_text(), functions["_reserve_marker_inode"]
    )
    assert reserve_source is not None
    assert reserve_source.index("os.fsync(descriptor)") < reserve_source.index(
        "_fsync_directory(marker.parent)"
    )
    runtime_tree = ast.parse(RUNTIME.read_text())
    runtime_imports = {
        alias.name.split(".")[0]
        for node in ast.walk(runtime_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert runtime_imports.isdisjoint({"subprocess", "socket", "urllib", "requests"})
    assert "authority" not in RUNTIME.read_text()
    forbidden_scientific = ("rank_stress", "isolated_runner", "residual_training")
    assert all(value not in AUTHORITY.read_text() for value in forbidden_scientific)
    assert all(value not in RUNTIME.read_text() for value in forbidden_scientific)


def test_imported_aliases_and_synthetic_nonce_routes_refuse_canonical_workspace(
    tmp_path: Path,
) -> None:
    alias = WORKSPACE / "research" / ".."
    marker = WORKSPACE / authority.MARKER_PATH
    assert not authority._path_has_entry(marker)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._reserve_marker_inode(alias)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._reserve_marker_inode(WORKSPACE)
    assert not authority._path_has_entry(marker)
    descriptor_path = tmp_path / "fd"
    descriptor = os.open(descriptor_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with pytest.raises(authority.PreparationAuthorityError):
            authority._complete_reserved_marker_synthetic(
                alias, descriptor, b"x", {}, {}, b"z" * 32
            )
    finally:
        os.close(descriptor)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._write_new_file(alias / "artifacts" / "alias-bypass.json", b"{}\n")
    with pytest.raises(authority.PreparationAuthorityError):
        authority._ensure_genesis(alias, b"", {}, b"", {})
    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_capsule_at_root(alias)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_runtime_at_root(alias, lambda *_: None)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._ensure_genesis(WORKSPACE, b"", {}, b"", {})
    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_capsule_at_root(WORKSPACE)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_runtime_at_root(WORKSPACE, lambda *_: None)
    assert not authority._path_has_entry(marker)


def test_import_runpy_python_vector_and_native_vector_forgeries_cannot_enter_live_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import runpy
    import sys

    marker = WORKSPACE / authority.MARKER_PATH
    original_name = authority.__name__
    assert not authority._path_has_entry(marker)
    for action in authority.LIVE_ACTIONS:
        with pytest.raises(authority.PreparationAuthorityError):
            authority.main([action])
    assert not authority._path_has_entry(marker)

    action = "--create-marker-after-explicit-authorization"
    expected = (
        authority.NATIVE_PYTHON_ARGV0,
        "-I",
        "-S",
        "-B",
        authority.AUTHORITY_PATH,
        action,
    )
    monkeypatch.setattr(authority, "__name__", "__main__")
    monkeypatch.setattr(authority, "__spec__", None)
    monkeypatch.setitem(sys.modules, "__main__", authority)
    monkeypatch.setattr(sys, "argv", [authority.AUTHORITY_PATH, action])
    monkeypatch.setattr(sys, "orig_argv", list(expected))
    monkeypatch.chdir(WORKSPACE)
    native_calls: list[bool] = []

    def forged_native_vector() -> tuple[str, ...]:
        native_calls.append(True)
        return (*expected[:-1], "--different-action")

    monkeypatch.setattr(authority, "_native_process_argv", forged_native_vector)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._require_live_cli_boundary(action)
    assert native_calls == [True]
    assert not authority._path_has_entry(marker)

    monkeypatch.setattr(authority, "__name__", original_name)
    monkeypatch.setitem(sys.modules, "__main__", sys.modules[__name__])
    monkeypatch.setattr(sys, "argv", [authority.AUTHORITY_PATH, action])
    with pytest.raises((RuntimeError, SystemExit)):
        runpy.run_path(AUTHORITY, run_name="__main__")
    assert not authority._path_has_entry(marker)


@pytest.mark.parametrize(
    "kind",
    (
        "empty",
        "partial",
        "wrong_mode",
        "directory",
        "symlink",
        "broken_symlink",
        "hardlink",
        "oversized",
    ),
)
def test_every_invalid_marker_entry_is_spent_terminal_without_retry(
    tmp_path: Path, kind: str
) -> None:
    root = _replica(tmp_path)
    marker = root / authority.MARKER_PATH
    marker.parent.mkdir(parents=True, exist_ok=True)
    if kind == "directory":
        marker.mkdir()
    elif kind == "symlink":
        target = root / "target"
        target.write_bytes(b"x")
        marker.symlink_to(target)
    elif kind == "broken_symlink":
        marker.symlink_to(root / "missing")
    elif kind == "hardlink":
        target = root / "hardlinked-marker-source"
        target.write_bytes(b"x")
        os.chmod(target, 0o600)
        os.link(target, marker)
    elif kind == "oversized":
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.ftruncate(descriptor, contracts.MAXIMUM_RECORD_BYTES + 1)
        finally:
            os.close(descriptor)
    else:
        marker.write_bytes(b"" if kind == "empty" else b"{broken")
        os.chmod(marker, 0o644 if kind == "wrong_mode" else 0o600)
    observed = authority.status(root)["live_transition"]
    assert observed["marker_attempt_spent"] is True
    assert observed["retry_permitted"] is False
    assert observed["closed"] is True
    assert "TERMINAL" in observed["live_state"]


def test_synthetic_marker_and_capsule_follow_exact_prefix_and_freeze_after_admission(
    tmp_path: Path,
) -> None:
    root = _replica(tmp_path)
    marker = authority._test_publish_marker(root, bytes(range(32)))
    assert marker["scientific_campaign_nonce_minted"] is False
    initial = authority.status(root)["live_transition"]
    assert initial["live_state"] == "CAPSULE_OPEN_RECORD_PUBLICATION_RESUMABLE"
    plan = authority.static_qualification_snapshot(root)["capsule_content_plan"]
    before_source_hashes = {
        row["source_path"]: _sha256((root / row["source_path"]).read_bytes())
        for row in plan["rows"]
        if row["source_path"] is not None
    }
    admission = authority._execute_capsule_at_root(root)
    assert before_source_hashes == {
        row["source_path"]: _sha256((root / row["source_path"]).read_bytes())
        for row in plan["rows"]
        if row["source_path"] is not None
    }
    assert admission["execution_admissible"] is False
    assert admission["file_count"] == 53
    assert admission["all_rows_reopened_twice"] is True
    observed = authority.status(root)["live_transition"]
    assert observed["live_state"] == "RUNTIME_OPEN_RECORD_PUBLICATION_RESUMABLE"
    overlay_rows = [
        row for row in plan["rows"] if row["payload_kind"] == "ONE_LITERAL_OVERLAY"
    ]
    assert len(overlay_rows) == 5
    for row in overlay_rows:
        payload = (
            root / authority.CAPSULE_ROOT / row["capsule_relative_path"]
        ).read_text()
        tree = ast.parse(payload)
        assignments = [
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == row["overlay_rule"]["constant_name"]
                for target in node.targets
            )
        ]
        assert len(assignments) == 1 and isinstance(assignments[0], ast.Tuple)
        assert tuple(element.value for element in assignments[0].elts) == (
            authority.FROZEN_REGISTRY
        )
    victim = root / authority.CAPSULE_ROOT / plan["rows"][0]["capsule_relative_path"]
    victim.unlink()
    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_capsule_at_root(root)
    assert not victim.exists()
    terminal = authority.status(root)["live_transition"]
    assert (
        terminal["live_state"] == "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID"
    )
    assert terminal["retry_permitted"] is False


def test_extra_capsule_file_directory_link_and_pyc_are_closed_world_hostiles(
    tmp_path: Path,
) -> None:
    root = _replica(tmp_path)
    authority._test_publish_marker(root, b"1" * 32)
    authority._execute_capsule_at_root(root)
    extra = root / authority.CAPSULE_ROOT / "__pycache__"
    extra.mkdir()
    (extra / "forbidden.pyc").write_bytes(b"x")
    observed = authority.status(root)["live_transition"]
    assert (
        observed["live_state"] == "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID"
    )
    assert observed["retry_permitted"] is False


@pytest.mark.parametrize("mismatch", (False, True))
def test_synthetic_runtime_double_capture_has_exact_success_or_rejection_branch_and_no_third_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mismatch: bool,
) -> None:
    root = _replica(tmp_path)
    _patch_runtime_replica(monkeypatch, root)
    _prepare_capsule(root, b"r" * 32)
    launched: list[int] = []

    def oracle(request_payload: bytes, ordinal: int) -> tuple[bytes, dict[str, object]]:
        request = contracts.parse_record(request_payload, "RUNTIME_REQUEST")
        launched.append(ordinal)
        release = (
            "SYNTHETIC_MISMATCH_RELEASE"
            if mismatch and ordinal == 1
            else "SYNTHETIC_STABLE_RELEASE"
        )
        payload = _synthetic_raw_envelope(
            root, request, ordinal, platform_release=release
        )
        return payload, _synthetic_child_receipt(root, payload, ordinal)

    candidate = authority._execute_runtime_at_root(root, oracle)
    assert launched == [0, 1]
    assert candidate["approved"] is False
    assert candidate["runtime_admitted"] is False
    assert candidate["execution_admissible"] is False
    assert candidate["raw_capture_envelopes_persisted"] is False
    observed = authority.status(root)["live_transition"]
    if mismatch:
        assert candidate["candidate_state"] == "REJECTED_DOUBLE_CAPTURE_MISMATCH"
        assert candidate["double_capture_semantically_stable"] is False
        assert observed["live_state"] == (
            "PREPARATION_CLOSED_RUNTIME_CANDIDATE_REJECTED"
        )
        assert observed["preparation_event_count"] == 4
        assert not authority._path_has_entry(root / authority._event_path(4))
    else:
        assert candidate["candidate_state"] == "UNAPPROVED_PREPARATION_CANDIDATE"
        assert candidate["double_capture_semantically_stable"] is True
        assert observed["live_state"] == (
            "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL"
        )
        assert observed["preparation_event_count"] == 5
    assert observed["closed"] is True
    assert observed["execution_authorized"] is False
    names = [path.name for path in (root / authority.PREPARATION_ROOT).rglob("*")]
    assert all("envelope" not in name for name in names)
    assert sorted(
        path.name for path in (root / authority.RUNTIME_CANDIDATE_ROOT).iterdir()
    ) == ["candidate.json"]
    repeated = authority._execute_runtime_at_root(root, oracle)
    assert repeated == candidate
    assert launched == [0, 1]


def test_runtime_launch_claim_without_binding_is_terminal_and_cannot_relaunch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _replica(tmp_path)
    _patch_runtime_replica(monkeypatch, root)
    _prepare_capsule(root, b"s" * 32)
    launched: list[int] = []

    def crash_after_claim(
        request_payload: bytes, ordinal: int
    ) -> tuple[bytes, dict[str, object]]:
        del request_payload
        launched.append(ordinal)
        raise RuntimeError("synthetic child crash after durable claim")

    with pytest.raises(RuntimeError):
        authority._execute_runtime_at_root(root, crash_after_claim)
    assert launched == [0]
    assert authority._audit_preparation_prefix(root, 0)["live_state"] == (
        "RUNTIME_CAPTURE_A_CLAIMED_ACTIVE_PROCESS_ONLY"
    )
    terminal = authority.status(root)["live_transition"]
    assert terminal["live_state"] == (
        "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID"
    )
    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_runtime_at_root(root, crash_after_claim)
    assert launched == [0]


def test_persisted_runtime_binding_rejects_profile_privacy_request_and_candidate_crosslinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _replica(tmp_path)
    _patch_runtime_replica(monkeypatch, root)
    _prepare_capsule(root, b"t" * 32)

    def oracle(request_payload: bytes, ordinal: int) -> tuple[bytes, dict[str, object]]:
        request = contracts.parse_record(request_payload, "RUNTIME_REQUEST")
        payload = _synthetic_raw_envelope(root, request, ordinal)
        return payload, _synthetic_child_receipt(root, payload, ordinal)

    authority._execute_runtime_at_root(root, oracle)
    request = _read_json(root / authority.RUNTIME_REQUEST_PATH)
    binding = _read_json(root / authority.RUNTIME_BINDING_A_PATH)

    profile_hostile = copy.deepcopy(binding)
    semantic = profile_hostile["privacy_safe_projection"]["semantic_projection"]
    semantic["python"]["implementation"] = "PyPy"
    semantic_sha = _sha256(runtime.SEMANTIC_MANIFEST_DOMAIN + _canonical(semantic))
    profile_hostile["semantic_manifest_sha256"] = semantic_sha
    profile_hostile["privacy_safe_projection"][
        "semantic_manifest_sha256"
    ] = semantic_sha
    profile_hostile["privacy_projection_sha256"] = _sha256(
        runtime.PRIVACY_PROJECTION_DOMAIN
        + _canonical(profile_hostile["privacy_safe_projection"])
    )
    profile_hostile = _rehashed(profile_hostile, "RUNTIME_ENVELOPE_BINDING")
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.validate_persisted_binding(profile_hostile, request)

    privacy_hostile = copy.deepcopy(binding)
    semantic = privacy_hostile["privacy_safe_projection"]["semantic_projection"]
    semantic["python"]["version"] = "/unclassified/private/value"
    semantic_sha = _sha256(runtime.SEMANTIC_MANIFEST_DOMAIN + _canonical(semantic))
    privacy_hostile["semantic_manifest_sha256"] = semantic_sha
    privacy_hostile["privacy_safe_projection"][
        "semantic_manifest_sha256"
    ] = semantic_sha
    privacy_hostile["privacy_projection_sha256"] = _sha256(
        runtime.PRIVACY_PROJECTION_DOMAIN
        + _canonical(privacy_hostile["privacy_safe_projection"])
    )
    privacy_hostile = _rehashed(privacy_hostile, "RUNTIME_ENVELOPE_BINDING")
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.validate_persisted_binding(privacy_hostile, request)

    request_hostile = dict(binding)
    request_hostile["request_sha256"] = "f" * 64
    request_hostile = _rehashed(request_hostile, "RUNTIME_ENVELOPE_BINDING")
    with pytest.raises(runtime.RuntimePreparationError):
        runtime.validate_persisted_binding(request_hostile, request)

    candidate_path = root / authority.RUNTIME_CANDIDATE_PATH
    candidate = _read_json(candidate_path)
    candidate["binding_a_sha256"] = "e" * 64
    candidate = _rehashed(candidate, "RUNTIME_CANDIDATE")
    candidate_path.write_bytes(_canonical(candidate) + b"\n")
    assert authority.status(root)["live_transition"]["live_state"] == (
        "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "extra_file",
        "extra_directory",
        "symlink",
        "broken_symlink",
        "hardlink",
        "wrong_file_mode",
        "wrong_directory_mode",
        "lock_payload",
        "gapped_claim",
        "payload_without_claim",
        "event_without_claim",
        "binding_without_capture_claim",
    ),
)
def test_full_preparation_tree_scanner_rejects_links_modes_extras_and_orphaned_gaps(
    tmp_path: Path, mutation: str
) -> None:
    root = _replica(tmp_path)
    _prepare_capsule(root, ("u-" + mutation).encode("ascii").ljust(32, b"x"))
    preparation = root / authority.PREPARATION_ROOT
    if mutation == "extra_file":
        target = preparation / "ledger/unexpected.json"
        target.write_bytes(b"{}\n")
        os.chmod(target, 0o600)
    elif mutation == "extra_directory":
        (preparation / "ledger/unexpected-empty").mkdir(mode=0o700)
    elif mutation == "symlink":
        (preparation / "ledger/unexpected-link").symlink_to(
            preparation / "ledger/genesis.json"
        )
    elif mutation == "broken_symlink":
        (preparation / "ledger/unexpected-link").symlink_to(preparation / "missing")
    elif mutation == "hardlink":
        os.link(
            root / authority.LEDGER_GENESIS_PATH,
            preparation / "ledger/unexpected-hardlink.json",
        )
    elif mutation == "wrong_file_mode":
        os.chmod(root / authority.LEDGER_GENESIS_PATH, 0o644)
    elif mutation == "wrong_directory_mode":
        os.chmod(root / authority.LEDGER_RECEIPTS_ROOT, 0o755)
    elif mutation == "lock_payload":
        (root / authority.LEDGER_LOCK_PATH).write_bytes(b"not-empty")
    elif mutation == "gapped_claim":
        source = root / authority._event_claim_path(1)
        target = root / authority._event_claim_path(3)
        shutil.copyfile(source, target)
        os.chmod(target, 0o600)
    elif mutation == "payload_without_claim":
        source = root / authority.CAPSULE_ADMISSION_PATH
        target = root / authority.RUNTIME_REQUEST_PATH
        shutil.copyfile(source, target)
        os.chmod(target, 0o600)
    elif mutation == "event_without_claim":
        source = root / authority._event_path(1)
        target = root / authority._event_path(2)
        shutil.copyfile(source, target)
        os.chmod(target, 0o600)
    else:
        source = root / authority.CAPSULE_ADMISSION_PATH
        target = root / authority.RUNTIME_BINDING_A_PATH
        shutil.copyfile(source, target)
        os.chmod(target, 0o600)
    observed = authority.status(root)["live_transition"]
    assert observed["live_state"] == (
        "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID"
    )
    assert observed["retry_permitted"] is False


def test_writer_lock_refuses_contention_and_detects_path_replacement_during_flock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _replica(tmp_path)
    authority._test_publish_marker(root, b"v" * 32)
    first = authority._acquire_writer_lock(root)
    try:
        with pytest.raises(authority.PreparationAuthorityError):
            authority._acquire_writer_lock(root)
    finally:
        os.close(first)

    original_flock = authority.fcntl.flock
    replaced = False

    def replace_during_flock(descriptor: int, operation: int) -> None:
        nonlocal replaced
        if not replaced and operation & authority.fcntl.LOCK_EX:
            replaced = True
            lock = root / authority.LEDGER_LOCK_PATH
            lock.unlink()
            lock.write_bytes(b"")
            os.chmod(lock, 0o600)
        original_flock(descriptor, operation)

    monkeypatch.setattr(authority.fcntl, "flock", replace_during_flock)
    with pytest.raises(authority.PreparationAuthorityError):
        authority._acquire_writer_lock(root)
    assert replaced is True


def test_full_prefix_scan_rejects_an_entry_added_after_semantic_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _replica(tmp_path)
    authority._test_publish_marker(root, b"y" * 32)
    original = authority._strict_valid_marker_prefix
    injected = False

    def inject_after_semantic_scan(
        *args: object, **kwargs: object
    ) -> dict[str, object]:
        nonlocal injected
        result = original(*args, **kwargs)
        if not injected:
            injected = True
            path = root / authority.PREPARATION_ROOT / "ledger/post-scan-extra.json"
            path.write_bytes(b"{}\n")
            os.chmod(path, 0o600)
        return result

    monkeypatch.setattr(
        authority, "_strict_valid_marker_prefix", inject_after_semantic_scan
    )
    observed = authority.status(root)["live_transition"]
    assert injected is True
    assert observed["live_state"] == (
        "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID"
    )


def test_dormant_v1_namespace_races_are_detected_before_capsule_or_binding_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    capsule_root = _replica(tmp_path / "capsule-race")
    authority._test_publish_marker(capsule_root, b"w" * 32)
    original_materialize = authority._materialize_missing_capsule_rows
    dormant_capsule_path = capsule_root / authority.DORMANT_V1_PATHS[0]

    def materialize_then_violate(
        root: Path, static: dict[str, object], live_action: str | None = None
    ) -> None:
        original_materialize(root, static, live_action)
        dormant_capsule_path.parent.mkdir(parents=True, exist_ok=True)
        dormant_capsule_path.symlink_to(capsule_root / "missing-dormant-target")

    monkeypatch.setattr(
        authority, "_materialize_missing_capsule_rows", materialize_then_violate
    )
    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_capsule_at_root(capsule_root)
    assert not authority._path_has_entry(capsule_root / authority._event_claim_path(1))
    assert not authority._path_has_entry(
        capsule_root / authority.CAPSULE_ADMISSION_PATH
    )

    monkeypatch.setattr(
        authority, "_materialize_missing_capsule_rows", original_materialize
    )
    runtime_root = _replica(tmp_path / "runtime-race")
    _patch_runtime_replica(monkeypatch, runtime_root)
    _prepare_capsule(runtime_root, b"x" * 32)
    dormant_runtime_path = runtime_root / authority.DORMANT_V1_PATHS[0]
    launched: list[int] = []

    def violate_during_capture(
        request_payload: bytes, ordinal: int
    ) -> tuple[bytes, dict[str, object]]:
        request = contracts.parse_record(request_payload, "RUNTIME_REQUEST")
        launched.append(ordinal)
        payload = _synthetic_raw_envelope(runtime_root, request, ordinal)
        dormant_runtime_path.parent.mkdir(parents=True, exist_ok=True)
        dormant_runtime_path.symlink_to(runtime_root / "missing-dormant-target")
        return payload, _synthetic_child_receipt(runtime_root, payload, ordinal)

    with pytest.raises(authority.PreparationAuthorityError):
        authority._execute_runtime_at_root(runtime_root, violate_during_capture)
    assert launched == [0]
    assert not authority._path_has_entry(
        runtime_root / authority.RUNTIME_BINDING_A_PATH
    )


def test_full_d1_quarantine_and_seed_1729_are_rejected_only_as_scientific_carriers() -> None:
    qualification = authority.v1_authority.load_dormant_protocol_qualification(
        WORKSPACE
    )
    quarantine = qualification.snapshot()["completion_evidence_protocol"][
        "d1_execution_lineage_quarantine"
    ]
    assert quarantine["row_count"] == 550
    rows = [row["sha256"] for row in quarantine["rows"]]
    assert len(rows) == len(set(rows)) == 550
    for value in rows:
        with pytest.raises(authority.PreparationAuthorityError):
            authority._scientific_carrier_digest_rejected(
                {"typed_output_evidence_sha256": value}, rows
            )
    with pytest.raises(authority.PreparationAuthorityError):
        authority._scientific_carrier_digest_rejected(
            {"seed_registry": list(authority.FROZEN_REGISTRY) + [1729]}, rows
        )
    assert authority.validate_future_scientific_carrier(
        WORKSPACE,
        {"seed_registry": list(authority.FROZEN_REGISTRY), "receipt_sha256": "f" * 64},
    )


def test_event_matrix_and_operation_nonce_are_disjoint_from_scientific_ledger() -> None:
    protocol = authority._event_protocol()
    assert protocol["maximum_success_event_count"] == 5
    assert protocol["rejection_terminal_event_count"] == 4
    assert protocol["namespace"] == "PREPARATION_ONLY"
    assert protocol["genesis_has_event_ordinal"] is False
    assert protocol["separate_from_scientific_authority_ordinals_0_through_589"] is True
    assert authority.EVENT_MATRIX[3]["allowed_kinds"] == (
        "RUNTIME_CANDIDATE_ADMITTED",
        "RUNTIME_DOUBLE_CAPTURE_REJECTED",
    )
    assert authority.EVENT_MATRIX[4]["allowed_kinds"] == (
        "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL",
    )
    first = authority._operation_nonce(SHA, "CAPSULE_ADMITTED")
    second = authority._operation_nonce(SHA, "RUNTIME_DOUBLE_CAPTURE_OPENED")
    assert first != second


def test_human_registration_has_required_nonclaims_and_no_local_identity_literal() -> None:
    text = HUMAN.read_text()
    required = (
        "172 unresolved null values",
        "12 blockers",
        "DRAFT_NOT_EXECUTABLE",
        "preparation-instance nonce",
        "scientific campaign nonce",
        "ADMITTED_PREPARATION_CUSTODY_ONLY",
        "outside the 53-file future-scientific capsule",
        "fresh formal recapture",
        "No canonical/live v2 marker or root was created",
        "deterministic synthetic marker, capsule, and runtime-candidate custody",
        authority.OPERATOR_AUTHORIZATION_CONTEXT,
    )
    assert all(value in text for value in required)
    assert "/Users/" not in text
    assert "raw capture envelopes are memory-only" not in text.lower() or (
        "never persisted" in text.lower()
    )


def test_no_focused_bytecode_cache_exists() -> None:
    stems = (
        CONTRACTS.stem,
        AUTHORITY.stem,
        RUNTIME.stem,
        TEST.stem,
    )
    for path in WORKSPACE.rglob("*.pyc"):
        assert not any(path.name.startswith(stem + ".") for stem in stems)
