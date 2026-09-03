import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    REPO_ROOT
    / "databricks/notebooks/b08_n1_uc_volume_write_capability_probe.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "b08_n1_uc_volume_write_capability_probe",
        NOTEBOOK,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def module():
    return load_module()


def exact_runtime():
    return {
        "exact": True,
        "expected": {},
        "mismatches": {},
        "observed": {},
    }


def fake_object_kinds(module, monkeypatch):
    def classify(path):
        if path == module.PROBE_PARENT:
            return "DIRECTORY"
        if path in (module.PRIMARY_LEAF, module.RACE_LEAF):
            return "ABSENT"
        raise AssertionError(path)

    monkeypatch.setattr(module, "object_kind", classify)


def test_fixed_paths_and_bounds_are_exact(module):
    assert str(module.PROBE_PARENT) == (
        "/Volumes/development/team_eds_supplychain/b08_runtime_output"
    )
    assert module.PRIMARY_LEAF.name == (
        "b08-n1-uc-volume-write-capability-probe-001-primary.bin"
    )
    assert module.RACE_LEAF.name == (
        "b08-n1-uc-volume-write-capability-probe-001-race.bin"
    )
    assert module.PAYLOAD_BYTES == 4096
    assert module.EXCLUSIVE_CREATE_CALL_LIMIT == 4
    assert module.MAXIMUM_POSSIBLE_PAYLOAD_BYTES_WRITTEN == 12288


def test_swapped_primary_and_race_roles_are_rejected(module):
    errors = module.validate_fixed_paths(
        module.PROBE_PARENT,
        module.RACE_LEAF,
        module.PRIMARY_LEAF,
    )
    assert "PRIMARY_PROBE_LEAF_NOT_EXACT" in errors
    assert "RACE_PROBE_LEAF_NOT_EXACT" in errors


def test_payload_hashes_are_fixed(module):
    expected = {
        "PRIMARY": (
            "26b7e40be0bcf3e6667020b3acf6e07faa17585b21b2936305dd6c9ad3860b15"
        ),
        "COLLISION": (
            "b23f99e1f653e62fa5bc14cc528a9ec3b6d11be482b2ee51b519d1d6ad8c5466"
        ),
        "RACE_A": (
            "6896d9ea3f73a4434f5832bc65714e7d066f177373f36f34dc8a6f735daa41b1"
        ),
        "RACE_B": (
            "725bcd6c66d02acf6ebeab9c92410e010ea22e336876256aaf05a211f4ce1902"
        ),
    }
    assert {
        label: module.PAYLOAD_BINDINGS[label]["sha256"]
        for label in expected
    } == expected
    for label, digest in expected.items():
        payload = module.fixed_payload(label)
        assert len(payload) == 4096
        assert hashlib.sha256(payload).hexdigest() == digest


def test_default_preflight_is_read_only_hold(module, monkeypatch):
    fake_object_kinds(module, monkeypatch)
    result = module.preflight(
        execution_mode="PREFLIGHT_ONLY",
        write_authorized=False,
        acknowledgement="NOT_AUTHORIZED",
        runtime=exact_runtime(),
        environment=module.EXPECTED_ENVIRONMENT,
    )
    assert result["decision"] == "HOLD_UC_VOLUME_PROBE_AUTHORITY_INCOMPLETE"
    assert result["probe_authorized"] is False
    assert result["errors"] == []
    assert result["safety"]["files_written"] is False
    assert result["safety"][
        "databricks_managed_storage_io_may_have_been_performed"
    ] is True
    assert result["safety"]["unity_catalog_volume_metadata_io_attempted"] is True
    assert result["safety"]["unity_catalog_volume_payload_io_attempted"] is False
    assert len(result["required_inputs"]) == 3


def test_all_three_exact_gates_are_required(module, monkeypatch):
    fake_object_kinds(module, monkeypatch)
    cases = [
        ("PREFLIGHT_ONLY", True, module.ACKNOWLEDGEMENT_TEXT),
        (module.RUN_MODE, False, module.ACKNOWLEDGEMENT_TEXT),
        (module.RUN_MODE, True, "NOT_AUTHORIZED"),
    ]
    for mode, authority, acknowledgement in cases:
        result = module.preflight(
            execution_mode=mode,
            write_authorized=authority,
            acknowledgement=acknowledgement,
            runtime=exact_runtime(),
            environment=module.EXPECTED_ENVIRONMENT,
        )
        assert result["probe_authorized"] is False

    accepted = module.preflight(
        execution_mode=module.RUN_MODE,
        write_authorized=True,
        acknowledgement=module.ACKNOWLEDGEMENT_TEXT,
        runtime=exact_runtime(),
        environment=module.EXPECTED_ENVIRONMENT,
    )
    assert accepted["probe_authorized"] is True
    assert accepted["decision"] == (
        "PROCEED_ONE_BOUNDED_UC_VOLUME_WRITE_CAPABILITY_PROBE"
    )


@pytest.mark.parametrize("existing", ["primary", "race"])
def test_existing_probe_leaf_blocks_all_authority(
    module,
    monkeypatch,
    existing,
):
    def classify(path):
        if path == module.PROBE_PARENT:
            return "DIRECTORY"
        if path == module.PRIMARY_LEAF:
            return "REGULAR_FILE" if existing == "primary" else "ABSENT"
        if path == module.RACE_LEAF:
            return "REGULAR_FILE" if existing == "race" else "ABSENT"
        raise AssertionError(path)

    monkeypatch.setattr(module, "object_kind", classify)
    result = module.preflight(
        execution_mode=module.RUN_MODE,
        write_authorized=True,
        acknowledgement=module.ACKNOWLEDGEMENT_TEXT,
        runtime=exact_runtime(),
        environment=module.EXPECTED_ENVIRONMENT,
    )
    assert result["probe_authorized"] is False
    assert result["decision"] == "HOLD_UC_VOLUME_PROBE_PREFLIGHT_FAILED"


def test_environment_mismatch_blocks_authority(module, monkeypatch):
    fake_object_kinds(module, monkeypatch)
    environment = dict(module.EXPECTED_ENVIRONMENT)
    environment["OMP_NUM_THREADS"] = "2"
    result = module.preflight(
        execution_mode=module.RUN_MODE,
        write_authorized=True,
        acknowledgement=module.ACKNOWLEDGEMENT_TEXT,
        runtime=exact_runtime(),
        environment=environment,
    )
    assert result["probe_authorized"] is False
    assert "DETERMINISTIC_ENVIRONMENT_MISMATCH" in result["errors"]


def test_volume_visibility_error_is_structured_hold(module, monkeypatch):
    def fail_visibility(path):
        raise PermissionError("injected")

    monkeypatch.setattr(module, "object_kind", fail_visibility)
    result = module.preflight(
        execution_mode=module.RUN_MODE,
        write_authorized=True,
        acknowledgement=module.ACKNOWLEDGEMENT_TEXT,
        runtime=exact_runtime(),
        environment=module.EXPECTED_ENVIRONMENT,
    )
    assert result["probe_authorized"] is False
    assert result["decision"] == "HOLD_UC_VOLUME_PROBE_PREFLIGHT_FAILED"
    assert any("VISIBILITY_FAILED:PermissionError" in item for item in result["errors"])


def test_exclusive_writer_handles_partial_writes(module, tmp_path, monkeypatch):
    state = module.fresh_state()
    payload = module.fixed_payload("PRIMARY")
    original_write = module.os.write

    def partial_write(descriptor, remaining):
        return original_write(descriptor, remaining[:17])

    monkeypatch.setattr(module.os, "write", partial_write)
    module.write_payload_exclusive(
        tmp_path,
        "partial.bin",
        payload,
        state,
        "PARTIAL_WRITE_TEST",
    )
    assert (tmp_path / "partial.bin").read_bytes() == payload
    assert state["exclusive_create_calls_begun_or_may_have_begun"] == 1
    assert state["confirmed_complete_payload_bytes_written"] == 4096


def test_zero_progress_write_is_terminal_for_that_call(
    module,
    tmp_path,
    monkeypatch,
):
    state = module.fresh_state()
    monkeypatch.setattr(module.os, "write", lambda descriptor, payload: 0)
    with pytest.raises(module.ProbeError) as raised:
        module.write_payload_exclusive(
            tmp_path,
            "zero.bin",
            module.fixed_payload("PRIMARY"),
            state,
            "ZERO_PROGRESS_TEST",
        )
    assert raised.value.code == "CONTROL_LEAF_WRITE_MADE_NO_PROGRESS"
    assert state["exclusive_create_calls_begun_or_may_have_begun"] == 1
    assert state["payload_write_begun"] is True


def test_parent_open_failure_does_not_claim_leaf_create_call(
    module,
    tmp_path,
    monkeypatch,
):
    state = module.fresh_state()

    def fail_parent(parent):
        raise OSError("injected parent-open failure")

    monkeypatch.setattr(module, "open_parent_descriptor", fail_parent)
    with pytest.raises(OSError, match="injected parent-open failure"):
        module.write_payload_exclusive(
            tmp_path,
            "never-opened.bin",
            module.fixed_payload("PRIMARY"),
            state,
            "PARENT_OPEN_FAILURE_TEST",
        )
    assert state["direct_exclusive_create_calls_begun"] == 0
    assert state["exclusive_create_calls_begun_or_may_have_begun"] == 0


def test_close_failure_does_not_confirm_complete_payload(
    module,
    tmp_path,
    monkeypatch,
):
    state = module.fresh_state()
    original_close = module.os.close
    calls = {"count": 0}

    def fail_first_close(descriptor):
        calls["count"] += 1
        original_close(descriptor)
        if calls["count"] == 1:
            raise OSError("injected close failure")

    monkeypatch.setattr(module.os, "close", fail_first_close)
    with pytest.raises(OSError, match="injected close failure"):
        module.write_payload_exclusive(
            tmp_path,
            "close-failure.bin",
            module.fixed_payload("PRIMARY"),
            state,
            "CLOSE_FAILURE_TEST",
        )
    assert state["payload_write_begun"] is True
    assert state["confirmed_complete_payload_bytes_written"] == 0


def test_intentional_collision_does_not_clobber(module, tmp_path):
    state = module.fresh_state()
    primary = module.fixed_payload("PRIMARY")
    collision = module.fixed_payload("COLLISION")
    module.write_payload_exclusive(
        tmp_path,
        "primary.bin",
        primary,
        state,
        "PRIMARY",
    )
    with pytest.raises(FileExistsError):
        module.write_payload_exclusive(
            tmp_path,
            "primary.bin",
            collision,
            state,
            "COLLISION",
            write_payload=False,
        )
    assert module.require_binding(tmp_path, "primary.bin", primary)[
        "sha256"
    ] == module.PAYLOAD_BINDINGS["PRIMARY"]["sha256"]
    assert state["exclusive_create_calls_begun_or_may_have_begun"] == 2
    assert state["confirmed_successful_create_count"] == 1


def test_two_process_race_has_one_winner_and_one_collision(module, tmp_path):
    state = module.fresh_state()
    result = module.run_two_process_race(tmp_path, "race.bin", state)
    statuses = [item["status"] for item in result["child_results"]]
    assert sorted(statuses) == ["COLLISION", "CREATED"]
    winner = result["winner"]["label"]
    assert winner in ("RACE_A", "RACE_B")
    assert module.require_binding(
        tmp_path,
        "race.bin",
        module.fixed_payload(winner),
    )["sha256"] == module.PAYLOAD_BINDINGS[winner]["sha256"]
    assert state["exclusive_create_calls_begun_or_may_have_begun"] == 2


def race_created(module, label):
    return {
        "label": label,
        "open_succeeded": True,
        "sha256": module.PAYLOAD_BINDINGS[label]["sha256"],
        "size_bytes": 4096,
        "status": "CREATED",
    }


@pytest.mark.parametrize(
    "results,error_code",
    [
        ([], "RACE_CHILD_RESULT_ROSTER_INVALID"),
        (
            [
                {"label": "RACE_A", "status": "COLLISION"},
                {"label": "RACE_A", "status": "COLLISION"},
            ],
            "RACE_CHILD_LABEL_ROSTER_INVALID",
        ),
        (
            [
                {"status": "COLLISION"},
                {"label": 7, "status": "COLLISION"},
            ],
            "RACE_CHILD_LABEL_ROSTER_INVALID",
        ),
        (
            [
                {"label": "RACE_A", "status": "COLLISION"},
                {"label": "RACE_B", "status": "COLLISION"},
            ],
            "RACE_DID_NOT_HAVE_EXACTLY_ONE_WINNER",
        ),
        (
            ["BOTH_CREATED_PLACEHOLDER"],
            "EXPAND_BOTH_CREATED",
        ),
        (
            ["WINNER_HASH_PLACEHOLDER"],
            "EXPAND_WINNER_HASH",
        ),
        (
            ["COLLISION_PAYLOAD_PLACEHOLDER"],
            "EXPAND_COLLISION_PAYLOAD",
        ),
    ],
)
def test_race_result_matrix_rejects_nonpassing_outcomes(
    module,
    results,
    error_code,
):
    if error_code == "EXPAND_BOTH_CREATED":
        results = [
            race_created(module, "RACE_A"),
            race_created(module, "RACE_B"),
        ]
        error_code = "RACE_DID_NOT_HAVE_EXACTLY_ONE_WINNER"
    elif error_code == "EXPAND_WINNER_HASH":
        bad = race_created(module, "RACE_A")
        bad["sha256"] = "0" * 64
        results = [
            bad,
            {
                "label": "RACE_B",
                "open_succeeded": False,
                "status": "COLLISION",
            },
        ]
        error_code = "RACE_WINNER_REPORT_BINDING_INVALID"
    elif error_code == "EXPAND_COLLISION_PAYLOAD":
        results = [
            race_created(module, "RACE_A"),
            {
                "label": "RACE_B",
                "open_succeeded": False,
                "sha256": "0" * 64,
                "status": "COLLISION",
            },
        ]
        error_code = "RACE_COLLISION_REPORT_INVALID"
    state = module.fresh_state()
    with pytest.raises(module.ProbeError) as raised:
        module.validate_race_results(results, state)
    assert raised.value.code == error_code
    assert state["confirmed_successful_create_count"] == 0
    assert state["confirmed_complete_payload_bytes_written"] == 0


def test_race_result_matrix_accepts_either_exact_winner(module):
    for winner_label, loser_label in (
        ("RACE_A", "RACE_B"),
        ("RACE_B", "RACE_A"),
    ):
        state = module.fresh_state()
        winner = module.validate_race_results(
            [
                race_created(module, winner_label),
                {
                    "label": loser_label,
                    "open_succeeded": False,
                    "status": "COLLISION",
                },
            ],
            state,
        )
        assert winner["label"] == winner_label
        assert state["confirmed_successful_create_count"] == 1
        assert state["confirmed_complete_payload_bytes_written"] == 4096


def test_select_failure_terminates_reaps_and_closes_children(
    module,
    tmp_path,
    monkeypatch,
):
    processes = []
    original_popen = module.subprocess.Popen

    def recording_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        processes.append(process)
        return process

    def fail_select(*args, **kwargs):
        raise OSError("injected select failure")

    monkeypatch.setattr(module.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(module.select, "select", fail_select)
    with pytest.raises(OSError, match="injected select failure"):
        module.run_two_process_race(
            tmp_path,
            "race-select-failure.bin",
            module.fresh_state(),
        )
    assert len(processes) == 2
    assert all(process.poll() is not None for process in processes)
    assert all(process.stdout.closed for process in processes)
    assert all(process.stderr.closed for process in processes)


def test_signal_failure_terminates_every_released_child(
    module,
    tmp_path,
    monkeypatch,
):
    processes = []
    original_popen = module.subprocess.Popen

    class FailingInput:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        @property
        def closed(self):
            return self.wrapped.closed

        def write(self, value):
            raise OSError("injected signal failure")

        def flush(self):
            return self.wrapped.flush()

        def close(self):
            return self.wrapped.close()

    def recording_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        processes.append(process)
        if len(processes) == 2:
            process.stdin = FailingInput(process.stdin)
        return process

    monkeypatch.setattr(module.subprocess, "Popen", recording_popen)
    state = module.fresh_state()
    with pytest.raises(OSError, match="injected signal failure"):
        module.run_two_process_race(
            tmp_path,
            "race-signal-failure.bin",
            state,
        )
    assert len(processes) == 2
    assert all(process.poll() is not None for process in processes)
    assert all(process.stdout.closed for process in processes)
    assert all(process.stderr.closed for process in processes)
    assert state["race_create_releases_or_calls_may_have_begun"] == 2


def test_validation_failure_closes_all_child_pipes(
    module,
    tmp_path,
    monkeypatch,
):
    processes = []
    original_popen = module.subprocess.Popen

    def recording_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        processes.append(process)
        return process

    def fail_validation(results, state):
        raise module.ProbeError("INJECTED_VALIDATION_FAILURE")

    monkeypatch.setattr(module.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(module, "validate_race_results", fail_validation)
    with pytest.raises(module.ProbeError) as raised:
        module.run_two_process_race(
            tmp_path,
            "race-validation-failure.bin",
            module.fresh_state(),
        )
    assert raised.value.code == "INJECTED_VALIDATION_FAILURE"
    assert all(process.poll() is not None for process in processes)
    assert all(process.stdout.closed for process in processes)
    assert all(process.stderr.closed for process in processes)


def test_generic_communicate_failure_cleans_every_child(
    module,
    tmp_path,
    monkeypatch,
):
    processes = []
    original_popen = module.subprocess.Popen

    def recording_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        processes.append(process)
        if len(processes) == 1:
            def fail_communicate(*call_args, **call_kwargs):
                raise OSError("injected communicate failure")

            process.communicate = fail_communicate
        return process

    monkeypatch.setattr(module.subprocess, "Popen", recording_popen)
    with pytest.raises(OSError, match="injected communicate failure"):
        module.run_two_process_race(
            tmp_path,
            "race-communicate-failure.bin",
            module.fresh_state(),
        )
    assert len(processes) == 2
    assert all(process.poll() is not None for process in processes)
    assert all(process.stdout.closed for process in processes)
    assert all(process.stderr.closed for process in processes)


def test_unconfirmed_child_quiescence_is_reported(module):
    class StuckProcess:
        def poll(self):
            return None

        def kill(self):
            return None

        def wait(self, timeout):
            raise module.subprocess.TimeoutExpired(["fake"], timeout)

    result = module.terminate_children([StuckProcess()])
    assert result["all_children_quiescent"] is False
    assert result["termination_requested"] is True
    assert result["children"] == [
        {
            "ordinal": 0,
            "quiescence_confirmed": False,
            "returncode": None,
        }
    ]


def test_complete_probe_passes_with_exact_bounds(module, tmp_path):
    primary = tmp_path / module.PRIMARY_LEAF.name
    race = tmp_path / module.RACE_LEAF.name
    result = module.run_probe(tmp_path, primary, race)
    assert result["decision"] == (
        "PASS_UC_VOLUME_EXCLUSIVE_CREATE_AND_REPEATABLE_READBACK_CAPABILITY"
    )
    assert (
        result["attempt_state"][
            "exclusive_create_calls_begun_or_may_have_begun"
        ]
        == 4
    )
    assert result["attempt_state"]["confirmed_successful_create_count"] == 2
    assert (
        result["bounds"]["confirmed_complete_payload_bytes_written"] == 8192
    )
    assert result["primary"]["collision_result"] == "FILE_EXISTS_ERROR"
    assert result["race"]["readback_1"] == result["race"]["readback_2"]
    assert primary.is_file()
    assert race.is_file()
    assert result["project_delta"]["b08_closed"] is False
    assert result["safety"]["databricks_managed_storage_io_performed"] is True
    assert result["safety"]["direct_external_network_endpoint_accessed"] is False
    assert result["attempt_state"]["race_child_cleanup"][
        "all_children_quiescent"
    ] is True


def test_preexisting_core_path_returns_unspent_no_go(module, tmp_path):
    primary = tmp_path / module.PRIMARY_LEAF.name
    race = tmp_path / module.RACE_LEAF.name
    primary.write_bytes(b"existing")
    result = module.run_probe(tmp_path, primary, race)
    assert result["decision"] == "NO_GO_UNSPENT_UC_VOLUME_CAPABILITY_PROBE"
    assert result["attempt_state"]["attempt_spent"] is False
    assert (
        result["attempt_state"][
            "exclusive_create_calls_begun_or_may_have_begun"
        ]
        == 0
    )
    assert primary.read_bytes() == b"existing"
    assert not race.exists()


def test_post_primary_failure_suppresses_race(module, tmp_path, monkeypatch):
    primary = tmp_path / module.PRIMARY_LEAF.name
    race = tmp_path / module.RACE_LEAF.name

    def fail_race(*args, **kwargs):
        raise module.ProbeError("INJECTED_RACE_FAILURE")

    monkeypatch.setattr(module, "run_two_process_race", fail_race)
    result = module.run_probe(tmp_path, primary, race)
    assert result["decision"] == (
        "TERMINAL_NO_GO_SPENT_UC_VOLUME_CAPABILITY_PROBE_REVIEW_REQUIRED"
    )
    assert result["error_code"] == "INJECTED_RACE_FAILURE"
    assert result["attempt_state"]["attempt_spent"] is True
    assert primary.is_file()
    assert not race.exists()


def test_read_binding_rejects_oversized_leaf(module, tmp_path):
    leaf = tmp_path / "oversized.bin"
    leaf.write_bytes(b"X" * (module.MAX_CONTROL_LEAF_BYTES + 1))
    with pytest.raises(module.ProbeError) as raised:
        module.read_binding(tmp_path, leaf.name)
    assert raised.value.code == "CONTROL_LEAF_SIZE_EXCEEDS_BOUND"


def test_invalid_leaf_names_are_rejected(module, tmp_path):
    for name in ("", ".", "..", "a/b", "a\\b"):
        with pytest.raises(module.ProbeError):
            module.read_binding(tmp_path, name)


def test_child_source_is_valid_and_uses_ready_newline(module):
    compile(module.RACE_CHILD_SOURCE, "<race-child>", "exec")
    assert 'sys.stdout.write("READY\\n")' in module.RACE_CHILD_SOURCE


def test_child_treats_file_exists_as_collision_only_at_leaf_open(module):
    tree = ast.parse(module.RACE_CHILD_SOURCE)
    guarded = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if any(
            isinstance(handler.type, ast.Name)
            and handler.type.id == "FileExistsError"
            for handler in node.handlers
        ):
            guarded.append(node)
    assert len(guarded) == 1
    assert len(guarded[0].body) == 1
    assignment = guarded[0].body[0]
    assert isinstance(assignment, ast.Assign)
    assert isinstance(assignment.value, ast.Call)
    assert isinstance(assignment.value.func, ast.Attribute)
    assert isinstance(assignment.value.func.value, ast.Name)
    assert assignment.value.func.value.id == "os"
    assert assignment.value.func.attr == "open"
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write"
        for node in ast.walk(assignment)
    )


def test_child_file_exists_during_write_is_error_not_collision(module, tmp_path):
    injected = module.RACE_CHILD_SOURCE.replace(
        "import sys\n\nlabel =",
        (
            "import sys\n\n"
            "def injected_write(descriptor, payload):\n"
            "    raise FileExistsError('injected write EEXIST')\n\n"
            "os.write = injected_write\n\n"
            "label ="
        ),
    )
    assert injected != module.RACE_CHILD_SOURCE
    process = module.subprocess.Popen(
        [
            module.sys.executable,
            "-c",
            injected,
            "RACE_A",
            str(tmp_path),
            "write-eexist.bin",
            str(module.PAYLOAD_BYTES),
        ],
        stdin=module.subprocess.PIPE,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
    )
    assert process.stdout.readline() == b"READY\n"
    process.stdin.write(b"G")
    process.stdin.flush()
    process.stdin.close()
    process.stdin = None
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0
    assert stderr == b""
    result = json.loads(stdout.decode("ascii"))
    assert result["status"] == "ERROR"
    assert result["open_succeeded"] is True
    assert result["error_phase"] == "WRITE"
    assert result["error_type"] == "FileExistsError"


def test_source_has_no_forbidden_mutating_or_external_calls():
    source = NOTEBOOK.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_attributes = {
        "chmod",
        "chown",
        "fchmod",
        "fsync",
        "mkdir",
        "rename",
        "replace",
        "rmdir",
        "unlink",
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called_attributes.isdisjoint(forbidden_attributes)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "remove"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in ("os", "shutil")
        for node in ast.walk(tree)
    )
    assert "O_TRUNC" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
    assert "dbutils.fs" not in source
    assert "spark." not in source


def test_preflight_json_surface_is_serializable(module, monkeypatch):
    fake_object_kinds(module, monkeypatch)
    result = module.preflight(
        execution_mode="PREFLIGHT_ONLY",
        write_authorized=False,
        acknowledgement="NOT_AUTHORIZED",
        runtime=exact_runtime(),
        environment=module.EXPECTED_ENVIRONMENT,
    )
    encoded = module.canonical_json_bytes(result)
    assert json.loads(encoded.decode("ascii"))["probe_authorized"] is False
