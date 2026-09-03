import base64
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import socket
import stat
import subprocess
import tempfile
import venv

import pytest


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    ROOT
    / "databricks"
    / "notebooks"
    / "b08_n1_isolated_overlay_lock_candidate.py"
)
PARAMETER_ENVIRONMENT_NAMES = (
    "HETERODIFF_REPO_ROOT_OVERRIDE",
    "HETERODIFF_B08_N1_DURABLE_OUTPUT_DIRECTORY",
    "HETERODIFF_B08_N1_EXECUTION_MODE",
    "HETERODIFF_B08_N1_NETWORK_BUILD_AUTHORIZED",
    "HETERODIFF_B08_N1_ONE_SHOT_ACKNOWLEDGEMENT",
)
BUILDER_RELATIVE_PATH = Path(
    "databricks/notebooks/b08_n1_isolated_overlay_lock_candidate.py"
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


def _load_namespace(capsys):
    namespace = runpy.run_path(str(NOTEBOOK))
    capsys.readouterr()
    return namespace


def _record_hash(payload):
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest())
    return "sha256=" + encoded.rstrip(b"=").decode("ascii")


def _record_row(path, payload):
    return f"{path},{_record_hash(payload)},{len(payload)}"


def _write_distribution(site, name, version, payloads, record_extras=()):
    dist_info = site / f"{name}-{version}.dist-info"
    dist_info.mkdir(parents=True)
    metadata = f"Name: {name}\nVersion: {version}\n".encode("ascii")
    metadata_path = dist_info / "METADATA"
    metadata_path.write_bytes(metadata)
    record_relative = f"{name}-{version}.dist-info/RECORD"
    rows = [
        _record_row(f"{name}-{version}.dist-info/METADATA", metadata),
    ]
    for relative, payload in payloads:
        target = site / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        rows.append(_record_row(relative, payload))
    rows.extend(record_extras)
    rows.append(f"{record_relative},,")
    (dist_info / "RECORD").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _local_ancestor_binding(parent):
    observed = parent.stat()
    return [
        {
            "path": parent.as_posix(),
            "device": observed.st_dev,
            "inode": observed.st_ino,
            "mode": observed.st_mode,
        }
    ]


def _allow_local_test_ancestor(namespace, monkeypatch):
    monkeypatch.setitem(
        namespace["start_durable_attempt"].__globals__,
        "require_ancestor_binding_unchanged",
        lambda destination, expected: expected,
    )


def _initialize_tracked_source_repo(repo):
    (repo / "src" / "heterodiff").mkdir(parents=True)
    (repo / BUILDER_RELATIVE_PATH).parent.mkdir(parents=True)
    (repo / "README.md").write_text("source repo\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        "[build-system]\nrequires=[]\nbuild-backend='demo'\n",
        encoding="utf-8",
    )
    (repo / "src" / "heterodiff" / "__init__.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    (repo / BUILDER_RELATIVE_PATH).write_text(
        "# tracked construction notebook\n",
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text(
        "src/heterodiff/ignored.py\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "source",
        ],
        check=True,
    )


def test_default_widget_path_is_hold_with_no_network_subprocess_or_write(
    monkeypatch, capsys
):
    for name in PARAMETER_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    source_before = NOTEBOOK.read_bytes()
    fake_dbutils = _Dbutils()

    monkeypatch.setattr(socket, "socket", _forbidden("network attempted"))
    monkeypatch.setattr(subprocess, "run", _forbidden("subprocess attempted"))
    monkeypatch.setattr(tempfile, "mkdtemp", _forbidden("tempdir write attempted"))
    monkeypatch.setattr(venv.EnvBuilder, "create", _forbidden("venv attempted"))
    monkeypatch.setattr(os, "open", _forbidden("exclusive write attempted"))
    monkeypatch.setattr(Path, "write_bytes", _forbidden("write_bytes attempted"))
    monkeypatch.setattr(Path, "write_text", _forbidden("write_text attempted"))
    monkeypatch.setattr(Path, "touch", _forbidden("touch attempted"))
    monkeypatch.setattr(Path, "mkdir", _forbidden("mkdir attempted"))
    monkeypatch.setattr(shutil, "copyfile", _forbidden("copy attempted"))
    monkeypatch.setattr(shutil, "rmtree", _forbidden("delete attempted"))

    runpy.run_path(str(NOTEBOOK), init_globals={"dbutils": fake_dbutils})
    result = json.loads(capsys.readouterr().out)

    assert result["construction_authorized"] is False
    assert result["decision"].startswith("HOLD_")
    assert result["safety"] == {
        "base_runtime_install_executed": False,
        "bounded_widget_input_accessed": True,
        "calibration_training_or_inference_executed": False,
        "databricks_rest_api_accessed": False,
        "files_written": False,
        "network_or_contact_accessed": False,
        "package_resolution_executed": False,
        "project_wheel_build_executed": False,
        "spark_accessed": False,
        "study_or_test_data_accessed": False,
    }
    assert fake_dbutils.widgets.defaults == {
        "b08_n1_durable_output_directory": "",
        "b08_n1_execution_mode": "PREFLIGHT_ONLY",
        "b08_n1_network_build_authorized": "false",
        "b08_n1_one_shot_acknowledgement": "NOT_AUTHORIZED",
    }
    assert NOTEBOOK.read_bytes() == source_before


def test_widget_parameters_do_not_require_tracked_notebook_edits(capsys):
    source_before = NOTEBOOK.read_bytes()
    supplied = {
        "b08_n1_durable_output_directory": (
            "/Volumes/catalog/schema/volume/candidate-0001"
        ),
        "b08_n1_execution_mode": "PREFLIGHT_ONLY",
        "b08_n1_network_build_authorized": "false",
        "b08_n1_one_shot_acknowledgement": "NOT_AUTHORIZED",
    }
    namespace = runpy.run_path(
        str(NOTEBOOK),
        init_globals={"dbutils": _Dbutils(supplied)},
    )
    capsys.readouterr()

    assert namespace["DURABLE_OUTPUT_DIRECTORY"] == supplied[
        "b08_n1_durable_output_directory"
    ]
    assert namespace["EXECUTION_MODE"] == "PREFLIGHT_ONLY"
    assert namespace["NETWORK_AND_BUILD_AUTHORIZED"] is False
    assert NOTEBOOK.read_bytes() == source_before


def test_notebook_path_finds_repo_from_unrelated_working_directory(
    monkeypatch, tmp_path, capsys
):
    for name in PARAMETER_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(NOTEBOOK), init_globals={"dbutils": _Dbutils()})
    result = json.loads(capsys.readouterr().out)

    assert result["decision"] in {
        "HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE",
        "HOLD_RUNTIME_PROFILE_MISMATCH_REQUIRES_REVIEW",
    }
    assert result["construction_authorized"] is False
    assert result["profile_validation"]["valid"] is True
    assert result["runtime"] is not None
    assert result["environment"] is not None
    assert result["safety"]["files_written"] is False
    assert result["safety"]["network_or_contact_accessed"] is False


def test_missing_repository_root_returns_structured_hold(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setenv("HETERODIFF_REPO_ROOT_OVERRIDE", str(tmp_path))
    runpy.run_path(str(NOTEBOOK), init_globals={"dbutils": _Dbutils()})
    result = json.loads(capsys.readouterr().out)

    assert result["decision"] == "HOLD_PREFLIGHT_FAILED"
    assert result["error_code"] == "REPOSITORY_ROOT_NOT_FOUND"
    assert result["safety"] == {
        "base_runtime_install_executed": False,
        "calibration_training_or_inference_executed": False,
        "databricks_rest_api_accessed": False,
        "files_written": False,
        "network_or_contact_accessed": False,
        "package_resolution_executed": False,
        "project_wheel_build_executed": False,
        "spark_accessed": False,
        "study_or_test_data_accessed": False,
    }


def test_overlay_record_console_script_path_stays_inside_prefix(tmp_path, capsys):
    namespace = _load_namespace(capsys)
    overlay = tmp_path / "overlay"
    site = overlay / "lib" / "python3.12" / "site-packages"
    script = b"#!/usr/bin/env python\n"
    script_path = overlay / "bin" / "demo"
    script_path.parent.mkdir(parents=True)
    script_path.write_bytes(script)
    _write_distribution(
        site,
        "demo",
        "1.0",
        [("demo/__init__.py", b"")],
        [_record_row("../../../bin/demo", script)],
    )

    result = namespace["verify_installed_overlay"](
        overlay,
        [{"normalized_name": "demo", "version": "1.0"}],
    )

    assert result["duplicate_installed_file_ownership"] is False
    assert result["ownership_entry_count"] == result["regular_file_count"]
    assert len(result["ownership_manifest_sha256"]) == 64


def test_overlay_record_rejects_lexical_escape(tmp_path, capsys):
    namespace = _load_namespace(capsys)
    overlay = tmp_path / "overlay"
    site = overlay / "lib" / "python3.12" / "site-packages"
    outside = tmp_path / "outside-script"
    outside.write_bytes(b"outside")
    _write_distribution(
        site,
        "demo",
        "1.0",
        [("demo/__init__.py", b"")],
        [_record_row("../../../../outside-script", outside.read_bytes())],
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["verify_installed_overlay"](
            overlay,
            [{"normalized_name": "demo", "version": "1.0"}],
        )
    assert caught.value.code == "OVERLAY_RECORD_PATH_ESCAPES_OVERLAY"


def test_overlay_record_rejects_duplicate_file_ownership(tmp_path, capsys):
    namespace = _load_namespace(capsys)
    overlay = tmp_path / "overlay"
    site = overlay / "lib" / "python3.12" / "site-packages"
    shared = b"shared"
    _write_distribution(
        site,
        "demo",
        "1.0",
        [("shared.py", shared)],
    )
    _write_distribution(
        site,
        "other",
        "2.0",
        [("other.py", b"other")],
        [_record_row("shared.py", shared)],
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["verify_installed_overlay"](
            overlay,
            [
                {"normalized_name": "demo", "version": "1.0"},
                {"normalized_name": "other", "version": "2.0"},
            ],
        )
    assert caught.value.code == "OVERLAY_DUPLICATE_INSTALLED_FILE_OWNERSHIP"


def test_network_or_build_phase_refuses_to_start_before_durable_intent(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    state = namespace["initial_attempt_state"]()
    monkeypatch.setattr(
        subprocess,
        "run",
        _forbidden("subprocess started before durable intent"),
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["run_tool"](
            [],
            "network_step",
            ["tool", "download"],
            tmp_path,
            {},
            "https://pypi.org/simple",
            "https://download.pytorch.org/whl/cpu",
            state,
            ("network_contact_begun", "package_resolution_begun"),
        )

    assert caught.value.code == "DURABLE_INTENT_REQUIRED_BEFORE_NETWORK_OR_BUILD"
    assert state["network_contact_begun"] is False
    assert state["package_resolution_begun"] is False


def test_attempt_intent_is_committed_before_first_network_step(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    ancestor_binding = _local_ancestor_binding(tmp_path)
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        ancestor_binding,
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_write_begun"] = True
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)
    observed = []

    def fake_run(argv, **kwargs):
        observed.append((destination / "attempt-intent.json").read_bytes())
        return subprocess.CompletedProcess(argv, 0, b"wheel", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = namespace["run_tool"](
        [],
        "network_step",
        ["tool", "download"],
        tmp_path,
        {},
        "https://pypi.org/simple",
        "https://download.pytorch.org/whl/cpu",
        state,
        ("network_contact_begun", "package_resolution_begun"),
        binding,
    )

    assert observed == [intent]
    assert result == b"wheel"
    assert binding["intent"]["sha256"] == hashlib.sha256(intent).hexdigest()
    assert state["network_contact_begun"] is True
    assert state["package_resolution_begun"] is True
    os.close(binding["descriptor"])


def test_renamed_and_replaced_attempt_root_cannot_start_tool_step(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    renamed_destination = tmp_path / "candidate-renamed"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    destination.rename(renamed_destination)
    destination.mkdir()
    monkeypatch.setattr(
        subprocess,
        "run",
        _forbidden("tool step started after custody replacement"),
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["run_tool"](
            [],
            "network_step",
            ["tool", "download"],
            tmp_path,
            {},
            "https://pypi.org/simple",
            "https://download.pytorch.org/whl/cpu",
            state,
            ("network_contact_begun", "package_resolution_begun"),
            binding,
        )

    assert caught.value.code == "DURABLE_DECLARED_PATH_BINDING_CHANGED"
    assert state["network_contact_begun"] is False
    assert state["package_resolution_begun"] is False
    assert not (destination / "attempt-intent.json").exists()
    assert (renamed_destination / "attempt-intent.json").read_bytes() == intent
    os.close(binding["descriptor"])


def test_attempt_root_and_intent_directory_entries_are_fsynced(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    original_fsync = os.fsync
    fsynced_kinds = []

    def track_fsync(descriptor):
        mode = os.fstat(descriptor).st_mode
        fsynced_kinds.append("directory" if stat.S_ISDIR(mode) else "regular")
        return original_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", track_fsync)
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        b'{"state":"spent"}\n',
    )

    assert "regular" in fsynced_kinds
    assert fsynced_kinds.count("directory") >= 2
    os.close(binding["descriptor"])


def test_parent_close_interrupt_after_intent_is_structured_and_bindable(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    original_open_bound = namespace["open_bound_directory"]
    original_close = os.close
    injected = {"descriptor": None, "done": False}

    def track_parent(path, expected_device=None, expected_inode=None):
        descriptor, observed = original_open_bound(
            path,
            expected_device,
            expected_inode,
        )
        if Path(path) == tmp_path:
            injected["descriptor"] = descriptor
        return descriptor, observed

    def close_then_interrupt(descriptor):
        if descriptor == injected["descriptor"] and not injected["done"]:
            injected["done"] = True
            original_close(descriptor)
            raise KeyboardInterrupt()
        return original_close(descriptor)

    monkeypatch.setitem(
        namespace["start_durable_attempt"].__globals__,
        "open_bound_directory",
        track_parent,
    )
    monkeypatch.setattr(os, "close", close_then_interrupt)
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["start_durable_attempt"](
            destination,
            _local_ancestor_binding(tmp_path),
            intent,
        )

    assert (
        caught.value.code
        == "DURABLE_ATTEMPT_PARENT_CLOSE_FAILED_AFTER_ROOT_CREATION"
    )
    telemetry = dict(caught.value.telemetry)
    operational = telemetry.pop("_durable_attempt_operational_binding")
    assert telemetry["durable_attempt_root_created"] is True
    assert telemetry["durable_intent_committed"] is True
    assert (destination / "attempt-intent.json").read_bytes() == intent
    _, failure_binding = namespace["commit_failure_receipt"](
        destination,
        operational,
        hashlib.sha256(intent).hexdigest(),
        caught.value,
        telemetry,
    )
    assert failure_binding["size_bytes"] > 0
    assert (destination / "construction-failure-receipt.json").is_file()
    original_close(operational["descriptor"])


def test_success_receipt_authority_is_retained_root_if_path_is_replaced(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    renamed_destination = tmp_path / "candidate-renamed"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_write = namespace["write_exclusive_at"]

    def write_then_replace(directory_descriptor, name, payload, mode=0o640):
        result = original_write(directory_descriptor, name, payload, mode)
        if name == "construction-receipt.json":
            destination.rename(renamed_destination)
            destination.mkdir()
        return result

    monkeypatch.setitem(
        namespace["commit_success_receipt"].__globals__,
        "write_exclusive_at",
        write_then_replace,
    )
    receipt = b'{"decision":"candidate"}\n'
    receipt_binding = namespace["commit_success_receipt"](
        binding,
        hashlib.sha256(intent).hexdigest(),
        len(intent),
        receipt,
    )

    assert receipt_binding["sha256"] == hashlib.sha256(receipt).hexdigest()
    assert receipt_binding["size_bytes"] == len(receipt)
    assert not (destination / "construction-receipt.json").exists()
    assert (
        renamed_destination / "construction-receipt.json"
    ).read_bytes() == receipt
    assert (renamed_destination / "attempt-intent.json").read_bytes() == intent
    observed_root = renamed_destination.stat()
    assert (observed_root.st_dev, observed_root.st_ino) == (
        binding["device"],
        binding["inode"],
    )
    os.close(binding["descriptor"])


def test_success_receipt_directory_fsync_failure_is_terminally_ambiguous(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_fsync_directory = namespace["fsync_directory"]
    injected = {"done": False}

    def fail_success_directory_fsync_once(descriptor, error_code):
        if (
            error_code == "DURABLE_PARENT_DIRECTORY_FSYNC_FAILED"
            and not injected["done"]
        ):
            injected["done"] = True
            raise namespace["CandidateConstructionError"](
                "INJECTED_SUCCESS_DIRECTORY_FSYNC_FAILURE"
            )
        return original_fsync_directory(descriptor, error_code)

    monkeypatch.setitem(
        namespace["commit_success_receipt"].__globals__,
        "fsync_directory",
        fail_success_directory_fsync_once,
    )
    success_payload = b'{"decision":"candidate"}\n'
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            success_payload,
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert caught.value.telemetry["success_receipt_may_exist"] is True
    assert (
        destination / "construction-receipt.json"
    ).read_bytes() == success_payload
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_success_receipt_preexisting_leaf_is_terminally_ambiguous(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    preexisting = b'{"decision":"preexisting"}\n'
    (destination / "construction-receipt.json").write_bytes(preexisting)

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (
        destination / "construction-receipt.json"
    ).read_bytes() == preexisting
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_success_receipt_post_write_interrupt_is_terminally_ambiguous(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_write = namespace["write_exclusive_at"]
    original_fstat = os.fstat
    injected = {"descriptor": None, "done": False}

    def write_then_arm_interrupt(directory_descriptor, name, payload, mode=0o640):
        result = original_write(directory_descriptor, name, payload, mode)
        if name == "construction-receipt.json":
            injected["descriptor"] = directory_descriptor
        return result

    def interrupt_once(descriptor):
        if (
            descriptor == injected["descriptor"]
            and not injected["done"]
        ):
            injected["done"] = True
            raise KeyboardInterrupt()
        return original_fstat(descriptor)

    monkeypatch.setitem(
        namespace["commit_success_receipt"].__globals__,
        "write_exclusive_at",
        write_then_arm_interrupt,
    )
    monkeypatch.setattr(os, "fstat", interrupt_once)
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_POST_CREATE_AMBIGUOUS"
    assert caught.value.detail == "KeyboardInterrupt"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (destination / "construction-receipt.json").is_file()
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_success_receipt_leaf_close_interrupt_is_terminally_ambiguous(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_open = os.open
    original_close = os.close
    injected = {"descriptor": None, "done": False}

    def track_receipt_leaf(path, *args, **kwargs):
        descriptor = original_open(path, *args, **kwargs)
        if path == "construction-receipt.json" and injected["descriptor"] is None:
            injected["descriptor"] = descriptor
        return descriptor

    def close_then_interrupt(descriptor):
        if descriptor == injected["descriptor"] and not injected["done"]:
            injected["done"] = True
            original_close(descriptor)
            raise KeyboardInterrupt()
        return original_close(descriptor)

    monkeypatch.setattr(os, "open", track_receipt_leaf)
    monkeypatch.setattr(os, "close", close_then_interrupt)
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (destination / "construction-receipt.json").is_file()
    assert not (destination / "construction-failure-receipt.json").exists()
    original_close(binding["descriptor"])


def test_success_receipt_final_directory_close_is_terminally_ambiguous(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_dup = os.dup
    original_close = os.close
    injected = {"descriptor": None, "done": False}

    def track_duplicate(descriptor):
        duplicate = original_dup(descriptor)
        injected["descriptor"] = duplicate
        return duplicate

    def close_then_interrupt(descriptor):
        if descriptor == injected["descriptor"] and not injected["done"]:
            injected["done"] = True
            original_close(descriptor)
            raise KeyboardInterrupt()
        return original_close(descriptor)

    monkeypatch.setattr(os, "dup", track_duplicate)
    monkeypatch.setattr(os, "close", close_then_interrupt)
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert (
        caught.value.code
        == "DURABLE_SUCCESS_RECEIPT_DESCRIPTOR_CLOSE_AMBIGUOUS"
    )
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (destination / "construction-receipt.json").is_file()
    assert not (destination / "construction-failure-receipt.json").exists()
    original_close(binding["descriptor"])


def test_success_receipt_first_fstat_interrupt_is_terminally_ambiguous(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_open = os.open
    original_fstat = os.fstat
    injected = {"descriptor": None, "done": False}

    def arm_after_success_leaf_open(path, *args, **kwargs):
        descriptor = original_open(path, *args, **kwargs)
        if path == "construction-receipt.json":
            injected["descriptor"] = descriptor
        return descriptor

    def interrupt_first_binding(descriptor):
        if (
            descriptor == injected["descriptor"]
            and not injected["done"]
        ):
            injected["done"] = True
            raise KeyboardInterrupt()
        return original_fstat(descriptor)

    monkeypatch.setattr(os, "open", arm_after_success_leaf_open)
    monkeypatch.setattr(os, "fstat", interrupt_first_binding)
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (destination / "construction-receipt.json").is_file()
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_persistent_initial_receipt_binding_failure_preserves_names(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_open = os.open
    original_fstat = os.fstat
    injected = {"descriptor": None}

    def arm_after_success_leaf_open(path, *args, **kwargs):
        descriptor = original_open(path, *args, **kwargs)
        if path == "construction-receipt.json":
            injected["descriptor"] = descriptor
        return descriptor

    def reject_receipt_binding(descriptor):
        if descriptor == injected["descriptor"]:
            raise OSError("injected persistent fstat failure")
        return original_fstat(descriptor)

    monkeypatch.setattr(os, "open", arm_after_success_leaf_open)
    monkeypatch.setattr(os, "fstat", reject_receipt_binding)
    monkeypatch.setattr(os, "rename", _forbidden("mutable-name rename attempted"))
    monkeypatch.setattr(os, "unlink", _forbidden("mutable-name unlink attempted"))
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (destination / "construction-receipt.json").is_file()
    assert not list(destination.glob(".unbound-created-*"))
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_success_receipt_final_binding_detects_post_write_leaf_swap(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    moved_receipt = destination / "owned-receipt-moved.json"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_write = namespace["write_exclusive_at"]
    replacement = b'{"decision":"replacement"}\n'

    def write_then_swap(directory_descriptor, name, payload, mode=0o640):
        result = original_write(directory_descriptor, name, payload, mode)
        if name == "construction-receipt.json":
            (destination / name).rename(moved_receipt)
            (destination / name).write_bytes(replacement)
        return result

    monkeypatch.setitem(
        namespace["commit_success_receipt"].__globals__,
        "write_exclusive_at",
        write_then_swap,
    )
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_POST_CREATE_AMBIGUOUS"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (destination / "construction-receipt.json").read_bytes() == replacement
    assert moved_receipt.is_file()
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_success_receipt_failure_path_never_renames_or_unlinks(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_fsync_directory = namespace["fsync_directory"]

    def fail_receipt_directory_fsync(descriptor, error_code):
        if error_code == "DURABLE_PARENT_DIRECTORY_FSYNC_FAILED":
            raise namespace["CandidateConstructionError"](
                "INJECTED_RECEIPT_DIRECTORY_FSYNC_FAILURE"
            )
        return original_fsync_directory(descriptor, error_code)

    monkeypatch.setitem(
        namespace["commit_success_receipt"].__globals__,
        "fsync_directory",
        fail_receipt_directory_fsync,
    )
    monkeypatch.setattr(os, "rename", _forbidden("mutable-name rename attempted"))
    monkeypatch.setattr(os, "unlink", _forbidden("mutable-name unlink attempted"))
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert caught.value.code == "DURABLE_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert (destination / "construction-receipt.json").is_file()
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_failure_receipt_final_directory_close_is_structured(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_dup = os.dup
    original_close = os.close
    injected = {"descriptor": None, "done": False}

    def track_duplicate(descriptor):
        duplicate = original_dup(descriptor)
        injected["descriptor"] = duplicate
        return duplicate

    def close_then_interrupt(descriptor):
        if descriptor == injected["descriptor"] and not injected["done"]:
            injected["done"] = True
            original_close(descriptor)
            raise KeyboardInterrupt()
        return original_close(descriptor)

    monkeypatch.setattr(os, "dup", track_duplicate)
    monkeypatch.setattr(os, "close", close_then_interrupt)
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_failure_receipt"](
            destination,
            binding,
            hashlib.sha256(intent).hexdigest(),
            namespace["CandidateConstructionError"]("INJECTED_FAILURE"),
            namespace["initial_attempt_state"](),
        )

    assert (
        caught.value.code
        == "DURABLE_FAILURE_RECEIPT_DESCRIPTOR_CLOSE_AMBIGUOUS"
    )
    assert caught.value.telemetry["failure_receipt_may_exist"] is True
    assert (destination / "construction-failure-receipt.json").is_file()
    assert not (destination / "construction-receipt.json").exists()
    original_close(binding["descriptor"])


def test_failure_receipt_preexisting_leaf_is_structured_ambiguity(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    preexisting = b'{"decision":"preexisting-failure"}\n'
    (destination / "construction-failure-receipt.json").write_bytes(
        preexisting
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_failure_receipt"](
            destination,
            binding,
            hashlib.sha256(intent).hexdigest(),
            namespace["CandidateConstructionError"]("INJECTED_FAILURE"),
            namespace["initial_attempt_state"](),
        )

    assert caught.value.code == "DURABLE_FAILURE_RECEIPT_COMMIT_AMBIGUOUS"
    assert caught.value.telemetry["failure_receipt_may_exist"] is True
    assert (
        destination / "construction-failure-receipt.json"
    ).read_bytes() == preexisting
    assert not (destination / "construction-receipt.json").exists()
    os.close(binding["descriptor"])


def test_one_shot_attempt_root_cannot_be_reused(monkeypatch, tmp_path, capsys):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    ancestor_binding = _local_ancestor_binding(tmp_path)
    intent = b'{"state":"spent"}\n'
    first_binding = namespace["start_durable_attempt"](
        destination,
        ancestor_binding,
        intent,
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["start_durable_attempt"](
            destination,
            ancestor_binding,
            intent,
        )

    assert caught.value.code == "DURABLE_ATTEMPT_ALREADY_SPENT_OR_COLLIDED"
    assert (destination / "attempt-intent.json").read_bytes() == intent
    os.close(first_binding["descriptor"])


def test_intent_write_failure_after_root_creation_is_terminally_bindable(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    ancestor_binding = _local_ancestor_binding(tmp_path)
    intent = b'{"state":"spent"}\n'
    original_write = namespace["write_exclusive_at"]

    def fail_intent_write(directory_descriptor, name, payload, mode=0o640):
        assert name == "attempt-intent.json"
        raise OSError("injected")

    monkeypatch.setitem(
        namespace["start_durable_attempt"].__globals__,
        "write_exclusive_at",
        fail_intent_write,
    )
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["start_durable_attempt"](
            destination,
            ancestor_binding,
            intent,
        )

    assert (
        caught.value.code
        == "DURABLE_INTENT_COMMIT_FAILED_AFTER_ROOT_CREATION"
    )
    telemetry = caught.value.telemetry
    assert telemetry["durable_attempt_root_created"] is True
    assert telemetry["durable_intent_expected_sha256"] == hashlib.sha256(
        intent
    ).hexdigest()
    assert telemetry["durable_attempt_root_binding"] == {
        "device": destination.stat().st_dev,
        "inode": destination.stat().st_ino,
    }

    monkeypatch.setitem(
        namespace["start_durable_attempt"].__globals__,
        "write_exclusive_at",
        original_write,
    )
    state = namespace["initial_attempt_state"]()
    state.update(telemetry)
    state["last_failed_step"] = "commit_durable_attempt_intent"
    failure, _ = namespace["commit_failure_receipt"](
        destination,
        telemetry["durable_attempt_root_binding"],
        telemetry["durable_intent_expected_sha256"],
        caught.value,
        state,
    )
    assert failure["decision"].startswith("TERMINAL_NO_GO_")
    assert (destination / "construction-failure-receipt.json").is_file()


def test_partial_publish_is_no_clobber_and_gets_terminal_failure_receipt(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    ancestor_binding = _local_ancestor_binding(tmp_path)
    intent = b'{"state":"spent"}\n'
    destination_binding = namespace["start_durable_attempt"](
        destination,
        ancestor_binding,
        intent,
    )
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "a.txt").write_bytes(b"a")
    (staging / "b.txt").write_bytes(b"b")
    original_write = namespace["write_exclusive_at"]

    def fail_second_write(directory_descriptor, name, payload, mode=0o640):
        if name == "b.txt":
            raise namespace["CandidateConstructionError"](
                "INJECTED_PARTIAL_PUBLISH_FAILURE"
            )
        return original_write(directory_descriptor, name, payload, mode)

    monkeypatch.setitem(
        namespace["copy_tree_no_clobber"].__globals__,
        "write_exclusive_at",
        fail_second_write,
    )
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["copy_tree_no_clobber"](
            staging,
            destination,
            destination_binding,
        )
    assert caught.value.code == "INJECTED_PARTIAL_PUBLISH_FAILURE"

    monkeypatch.setitem(
        namespace["copy_tree_no_clobber"].__globals__,
        "write_exclusive_at",
        original_write,
    )
    state = namespace["initial_attempt_state"]()
    state.update(
        {
            "durable_intent_committed": True,
            "durable_publish_begun": True,
            "last_failed_step": "publish_durable_artifacts",
        }
    )
    failure_receipt, _ = namespace["commit_failure_receipt"](
        destination,
        destination_binding,
        hashlib.sha256(intent).hexdigest(),
        caught.value,
        state,
    )

    assert (destination / "a.txt").read_bytes() == b"a"
    assert not (destination / "b.txt").exists()
    assert not (destination / "construction-receipt.json").exists()
    durable_failure = json.loads(
        (destination / "construction-failure-receipt.json").read_text()
    )
    assert durable_failure == failure_receipt
    assert durable_failure["attempt_state"]["durable_publish_begun"] is True
    os.close(destination_binding["descriptor"])


def test_durable_publish_fsyncs_new_directory_and_file_entries(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    staging = tmp_path / "staging"
    (staging / "nested").mkdir(parents=True)
    (staging / "nested" / "payload.bin").write_bytes(b"payload")
    original_fsync = os.fsync
    fsynced_kinds = []

    def track_fsync(descriptor):
        mode = os.fstat(descriptor).st_mode
        fsynced_kinds.append("directory" if stat.S_ISDIR(mode) else "regular")
        return original_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", track_fsync)
    namespace["copy_tree_no_clobber"](staging, destination, binding)

    assert "regular" in fsynced_kinds
    assert fsynced_kinds.count("directory") >= 2
    assert (destination / "nested" / "payload.bin").read_bytes() == b"payload"
    os.close(binding["descriptor"])


def test_durable_publish_preserves_executable_mode_and_manifest(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    staging = tmp_path / "staging"
    executable = staging / "overlay" / "bin" / "demo"
    executable.parent.mkdir(parents=True)
    payload = b"#!/usr/bin/env python3\n"
    executable.write_bytes(payload)
    executable.chmod(0o755)

    published = namespace["copy_tree_no_clobber"](
        staging,
        destination,
        binding,
    )

    durable = destination / "overlay" / "bin" / "demo"
    observed = durable.stat()
    expected_rows = [
        {
            "relative_path": "overlay/bin/demo",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "device": observed.st_dev,
            "inode": observed.st_ino,
            "mode_octal": "0755",
        }
    ]
    assert durable.read_bytes() == payload
    assert observed.st_mode & 0o777 == 0o755
    assert published["published_file_count"] == 1
    assert published["published_files_manifest_sha256"] == hashlib.sha256(
        namespace["canonical_json_bytes"](expected_rows)
    ).hexdigest()
    os.close(binding["descriptor"])


def test_failure_receipt_refuses_a_tampered_retained_intent(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    (destination / "attempt-intent.json").write_bytes(b"tampered\n")
    error = namespace["CandidateConstructionError"]("INJECTED_FAILURE")

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["commit_failure_receipt"](
            destination,
            binding,
            hashlib.sha256(intent).hexdigest(),
            error,
            namespace["initial_attempt_state"](),
        )

    assert caught.value.code == "DURABLE_INTENT_CUSTODY_MISMATCH"
    assert not (destination / "construction-failure-receipt.json").exists()
    os.close(binding["descriptor"])


def test_failed_tool_step_records_truthful_phase_telemetry(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    def fail_run(*args, **kwargs):
        raise OSError("injected")

    monkeypatch.setattr(subprocess, "run", fail_run)
    journal = []
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["run_tool"](
            journal,
            "resolve_runtime",
            ["tool", "download"],
            tmp_path,
            {},
            "https://pypi.org/simple",
            "https://download.pytorch.org/whl/cpu",
            state,
            ("network_contact_begun", "package_resolution_begun"),
            binding,
        )

    assert caught.value.code == "TOOL_STEP_EXECUTION_FAILED"
    assert caught.value.telemetry["network_contact_begun"] is True
    assert caught.value.telemetry["package_resolution_begun"] is True
    assert caught.value.telemetry["last_failed_step"] == "resolve_runtime"
    assert journal[0]["execution_error"] == "OSError"
    os.close(binding["descriptor"])


def test_failed_bootstrap_install_retains_phase_and_pip_provenance(
    monkeypatch,
    tmp_path,
    capsys,
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)
    state["host_pip_identity"] = {"pip_version": "25.0.1"}
    state["bootstrap_pip_wheel_binding"] = {
        "filename": "pip-25.0.1-py3-none-any.whl",
        "sha256": "a" * 64,
    }

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv,
            1,
            b"",
            b"injected",
        ),
    )
    journal = []
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["run_tool"](
            journal,
            "bootstrap_pip_into_isolated_venv",
            ["host-python", "-m", "pip", "--python", "venv", "install"],
            tmp_path,
            {},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            state,
            ("bootstrap_pip_install_begun", "build_tool_install_begun"),
            binding,
        )

    assert caught.value.code == "TOOL_STEP_FAILED"
    telemetry = caught.value.telemetry
    assert telemetry["bootstrap_pip_install_begun"] is True
    assert telemetry["build_tool_install_begun"] is True
    assert telemetry["project_wheel_build_begun"] is False
    assert telemetry["overlay_install_begun"] is False
    assert telemetry["last_started_step"] == (
        "bootstrap_pip_into_isolated_venv"
    )
    assert telemetry["last_failed_step"] == (
        "bootstrap_pip_into_isolated_venv"
    )
    assert telemetry["host_pip_identity"] == {"pip_version": "25.0.1"}
    assert telemetry["bootstrap_pip_wheel_binding"]["sha256"] == "a" * 64
    assert journal[0]["returncode"] == 1
    os.close(binding["descriptor"])


def test_git_external_execution_config_is_rejected_after_intent(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = tmp_path / "fsmonitor-executed"
    hook = tmp_path / "fsmonitor-hook"
    hook.write_text(
        "#!/bin/sh\nprintf invoked > " + marker.as_posix() + "\n",
        encoding="utf-8",
    )
    hook.chmod(0o700)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "test",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "config",
            "core.fsmonitor",
            hook.as_posix(),
        ],
        check=True,
    )
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["git_identity"](
            repo,
            [],
            {"PATH": os.environ["PATH"]},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            state,
            binding,
        )

    assert (
        caught.value.code
        == "GIT_LOCAL_CONFIG_EXTERNAL_EXECUTION_SURFACE_PRESENT"
    )
    assert state["source_identity_verification_begun"] is True
    assert state["network_contact_begun"] is False
    assert not marker.exists()
    os.close(binding["descriptor"])


def test_git_identity_accepts_exact_tracked_source_manifest(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    _initialize_tracked_source_repo(repo)
    source_manifest = namespace["project_source_manifest"](repo)
    builder_binding = namespace["regular_file_binding"](
        repo,
        BUILDER_RELATIVE_PATH,
        "BUILDER",
    )
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    revision, epoch, provenance = namespace["git_identity"](
        repo,
        [],
        {"PATH": os.environ["PATH"]},
        namespace["PRIMARY_SIMPLE_INDEX_URL"],
        namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
        state,
        binding,
        source_manifest,
        builder_binding,
    )

    assert len(revision) == 40
    assert epoch > 0
    assert provenance[
        "all_manifest_paths_exactly_tracked_in_index_and_head"
    ] is True
    assert provenance["all_worktree_bytes_match_head_blobs"] is True
    assert provenance[
        "construction_notebook_exactly_tracked_in_index_and_head"
    ] is True
    assert provenance["bound_path_count"] == 4
    assert provenance["manifest_path_count"] == 3
    os.close(binding["descriptor"])


def test_git_identity_rejects_ignored_untracked_source_in_manifest(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    _initialize_tracked_source_repo(repo)
    ignored = repo / "src" / "heterodiff" / "ignored.py"
    ignored.write_text("IGNORED = True\n", encoding="utf-8")
    source_manifest = namespace["project_source_manifest"](repo)
    builder_binding = namespace["regular_file_binding"](
        repo,
        BUILDER_RELATIVE_PATH,
        "BUILDER",
    )
    assert any(
        record["relative_path"] == "src/heterodiff/ignored.py"
        for record in source_manifest["files"]
    )
    assert subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout == b""
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["git_identity"](
            repo,
            [],
            {"PATH": os.environ["PATH"]},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            state,
            binding,
            source_manifest,
            builder_binding,
        )

    assert (
        caught.value.code
        == "BOUND_SOURCE_DIFFERS_FROM_GIT_INDEX_PATH_SET"
    )
    assert state["network_contact_begun"] is False
    os.close(binding["descriptor"])


def test_git_identity_rejects_replacement_object_source_substitution(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    _initialize_tracked_source_repo(repo)
    original_revision = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode("ascii").strip()
    source = repo / "src" / "heterodiff" / "__init__.py"
    source.write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", source.relative_to(repo).as_posix()],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "replacement",
        ],
        check=True,
    )
    replacement_revision = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode("ascii").strip()
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "replace",
            original_revision,
            replacement_revision,
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "reset", "--hard", "-q", original_revision],
        check=True,
    )
    assert source.read_text(encoding="utf-8") == "VALUE = 2\n"
    assert subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout == b""

    source_manifest = namespace["project_source_manifest"](repo)
    builder_binding = namespace["regular_file_binding"](
        repo,
        BUILDER_RELATIVE_PATH,
        "BUILDER",
    )
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["git_identity"](
            repo,
            [],
            {"PATH": os.environ["PATH"]},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            state,
            binding,
            source_manifest,
            builder_binding,
        )

    assert caught.value.code == "SOURCE_MANIFEST_CONTENT_OR_IDENTITY_MISMATCH"
    assert state["network_contact_begun"] is False
    os.close(binding["descriptor"])


def test_git_identity_rejects_ignored_untracked_construction_notebook(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    _initialize_tracked_source_repo(repo)
    subprocess.run(
        ["git", "-C", str(repo), "rm", "-q", BUILDER_RELATIVE_PATH.as_posix()],
        check=True,
    )
    with (repo / ".gitignore").open("a", encoding="utf-8") as handle:
        handle.write(BUILDER_RELATIVE_PATH.as_posix() + "\n")
    subprocess.run(
        ["git", "-C", str(repo), "add", ".gitignore"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "ignore construction notebook",
        ],
        check=True,
    )
    notebook = repo / BUILDER_RELATIVE_PATH
    notebook.parent.mkdir(parents=True, exist_ok=True)
    notebook.write_text("# ignored construction notebook\n", encoding="utf-8")
    assert subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout == b""

    source_manifest = namespace["project_source_manifest"](repo)
    builder_binding = namespace["regular_file_binding"](
        repo,
        BUILDER_RELATIVE_PATH,
        "BUILDER",
    )
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["git_identity"](
            repo,
            [],
            {"PATH": os.environ["PATH"]},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            state,
            binding,
            source_manifest,
            builder_binding,
        )

    assert caught.value.code == "BOUND_SOURCE_DIFFERS_FROM_GIT_INDEX_PATH_SET"
    assert state["network_contact_begun"] is False
    os.close(binding["descriptor"])


def test_git_included_external_filter_config_is_rejected_after_intent(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = tmp_path / "filter-executed"
    filter_program = tmp_path / "clean-filter"
    filter_program.write_text(
        "#!/bin/sh\ncat\nprintf invoked > " + marker.as_posix() + "\n",
        encoding="utf-8",
    )
    filter_program.chmod(0o700)
    included_config = tmp_path / "included.gitconfig"
    included_config.write_text(
        '[filter "probe"]\n'
        "\tclean = " + filter_program.as_posix() + "\n"
        "\trequired = true\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitattributes").write_text(
        "tracked.txt filter=probe\n",
        encoding="utf-8",
    )
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", ".gitattributes", "tracked.txt"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "test",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "config",
            "include.path",
            included_config.as_posix(),
        ],
        check=True,
    )
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["git_identity"](
            repo,
            [],
            {"PATH": os.environ["PATH"]},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            state,
            binding,
        )

    assert (
        caught.value.code
        == "GIT_LOCAL_CONFIG_EXTERNAL_EXECUTION_SURFACE_PRESENT"
    )
    assert caught.value.detail == "include.path"
    assert state["source_identity_verification_begun"] is True
    assert state["network_contact_begun"] is False
    assert not marker.exists()
    os.close(binding["descriptor"])


def test_git_worktree_external_filter_config_is_rejected_after_intent(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = tmp_path / "worktree-filter-executed"
    filter_program = tmp_path / "worktree-clean-filter"
    filter_program.write_text(
        "#!/bin/sh\ncat\nprintf invoked > " + marker.as_posix() + "\n",
        encoding="utf-8",
    )
    filter_program.chmod(0o700)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitattributes").write_text(
        "tracked.txt filter=probe\n",
        encoding="utf-8",
    )
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", ".gitattributes", "tracked.txt"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "test",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "config",
            "extensions.worktreeConfig",
            "true",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "config",
            "--worktree",
            "filter.probe.clean",
            filter_program.as_posix(),
        ],
        check=True,
    )
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        tmp_path / "candidate",
        _local_ancestor_binding(tmp_path),
        intent,
    )
    state = namespace["initial_attempt_state"]()
    state["durable_intent_committed"] = True
    state["durable_intent_expected_sha256"] = hashlib.sha256(intent).hexdigest()
    state["durable_intent_expected_size_bytes"] = len(intent)

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["git_identity"](
            repo,
            [],
            {"PATH": os.environ["PATH"]},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            state,
            binding,
        )

    assert (
        caught.value.code
        == "GIT_LOCAL_CONFIG_EXTERNAL_EXECUTION_SURFACE_PRESENT"
    )
    assert caught.value.detail == "extensions.worktreeconfig"
    assert state["source_identity_verification_begun"] is True
    assert state["network_contact_begun"] is False
    assert not marker.exists()
    os.close(binding["descriptor"])


def test_open_relative_directory_closes_fd_on_base_exception(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    root = tmp_path / "root"
    (root / "a" / "b").mkdir(parents=True)
    root_descriptor = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    original_open = os.open
    original_close = os.close
    opened = []
    closed = []

    def interrupting_open(path, *args, **kwargs):
        if path == "b":
            raise KeyboardInterrupt()
        descriptor = original_open(path, *args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def tracking_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    monkeypatch.setattr(os, "open", interrupting_open)
    monkeypatch.setattr(os, "close", tracking_close)
    with pytest.raises(KeyboardInterrupt):
        namespace["open_relative_directory"](root_descriptor, ("a", "b"))

    assert opened
    assert opened[-1] in closed
    original_close(root_descriptor)


def test_open_bound_directory_closes_fd_if_fstat_is_interrupted(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    original_open = os.open
    original_fstat = os.fstat
    original_close = os.close
    opened = []
    closed = []

    def tracking_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def interrupting_fstat(descriptor):
        if opened and descriptor == opened[-1]:
            raise KeyboardInterrupt()
        return original_fstat(descriptor)

    def tracking_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    monkeypatch.setattr(os, "open", tracking_open)
    monkeypatch.setattr(os, "fstat", interrupting_fstat)
    monkeypatch.setattr(os, "close", tracking_close)
    with pytest.raises(KeyboardInterrupt):
        namespace["open_bound_directory"](tmp_path)

    assert opened[-1] in closed


def test_success_commit_closes_duplicated_fd_if_fstat_is_interrupted(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    _allow_local_test_ancestor(namespace, monkeypatch)
    destination = tmp_path / "candidate"
    intent = b'{"state":"spent"}\n'
    binding = namespace["start_durable_attempt"](
        destination,
        _local_ancestor_binding(tmp_path),
        intent,
    )
    original_dup = os.dup
    original_fstat = os.fstat
    original_close = os.close
    duplicated = []
    closed = []

    def tracking_dup(descriptor):
        duplicate = original_dup(descriptor)
        duplicated.append(duplicate)
        return duplicate

    def interrupting_fstat(descriptor):
        if duplicated and descriptor == duplicated[-1]:
            raise KeyboardInterrupt()
        return original_fstat(descriptor)

    def tracking_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    monkeypatch.setattr(os, "dup", tracking_dup)
    monkeypatch.setattr(os, "fstat", interrupting_fstat)
    monkeypatch.setattr(os, "close", tracking_close)
    with pytest.raises(KeyboardInterrupt):
        namespace["commit_success_receipt"](
            binding,
            hashlib.sha256(intent).hexdigest(),
            len(intent),
            b'{"decision":"candidate"}\n',
        )

    assert duplicated[-1] in closed
    original_close(binding["descriptor"])


def test_pre_intent_source_failure_is_structured_and_writes_nothing(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    globals_map = namespace["construct_candidate"].__globals__
    destination = tmp_path / "candidate"
    monkeypatch.setitem(
        globals_map,
        "DURABLE_OUTPUT_DIRECTORY",
        destination.as_posix(),
    )

    def fail_source_manifest(repo_root):
        del repo_root
        raise OSError("injected pre-intent source failure")

    monkeypatch.setitem(
        globals_map,
        "project_source_manifest",
        fail_source_manifest,
    )
    monkeypatch.setitem(
        globals_map,
        "start_durable_attempt",
        _forbidden("durable attempt started after pre-intent failure"),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        _forbidden("subprocess started after pre-intent failure"),
    )
    monkeypatch.setattr(
        tempfile,
        "mkdtemp",
        _forbidden("staging write started after pre-intent failure"),
    )
    preflight = {
        "repo_root": ROOT,
        "profile_validation": {
            "file_sha256": namespace["EXPECTED_PROFILE_FILE_SHA256"],
            "semantic_sha256": namespace[
                "EXPECTED_PROFILE_SEMANTIC_SHA256"
            ],
        },
        "v2_independent_review_binding": {
            "relative_path": namespace["V2_REVIEW_RELATIVE_PATH"].as_posix(),
            "sha256": namespace["EXPECTED_V2_REVIEW_FILE_SHA256"],
            "size_bytes": 1,
        },
        "destination": {"ancestor_binding": _local_ancestor_binding(tmp_path)},
        "primary_index": {"url": namespace["PRIMARY_SIMPLE_INDEX_URL"]},
        "torch_index": {
            "url": namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"]
        },
    }

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["construct_candidate"](preflight)

    assert caught.value.code == "PRE_INTENT_CONSTRUCTION_FAILED"
    assert caught.value.detail == "OSError"
    assert caught.value.telemetry["last_failed_step"] == (
        "construct_pre_intent_bindings"
    )
    assert caught.value.telemetry["durable_write_begun"] is False
    assert caught.value.telemetry["durable_attempt_root_created"] is False
    assert caught.value.telemetry["durable_intent_committed"] is False
    assert caught.value.telemetry["network_contact_begun"] is False
    assert not destination.exists()


def test_pre_intent_intent_hash_interrupt_is_structured_and_writes_nothing(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    globals_map = namespace["construct_candidate"].__globals__
    destination = tmp_path / "candidate"
    monkeypatch.setitem(
        globals_map,
        "DURABLE_OUTPUT_DIRECTORY",
        destination.as_posix(),
    )
    monkeypatch.setitem(
        globals_map,
        "project_source_manifest",
        lambda repo_root: {"record_sha256": "b" * 64, "files": []},
    )
    monkeypatch.setitem(
        globals_map,
        "regular_file_binding",
        lambda *args: {
            "relative_path": namespace[
                "BUILDER_NOTEBOOK_RELATIVE_PATH"
            ].as_posix(),
            "sha256": "c" * 64,
            "size_bytes": 1,
        },
    )
    monkeypatch.setitem(
        globals_map,
        "build_attempt_intent",
        lambda *args: ({"schema_version": "test"}, b'{"state":"ready"}\n'),
    )

    def interrupt_hash(payload):
        del payload
        raise KeyboardInterrupt()

    monkeypatch.setitem(globals_map, "sha256_bytes", interrupt_hash)
    monkeypatch.setitem(
        globals_map,
        "start_durable_attempt",
        _forbidden("durable attempt started after pre-intent interrupt"),
    )
    preflight = {
        "repo_root": ROOT,
        "profile_validation": {
            "file_sha256": namespace["EXPECTED_PROFILE_FILE_SHA256"],
            "semantic_sha256": namespace[
                "EXPECTED_PROFILE_SEMANTIC_SHA256"
            ],
        },
        "v2_independent_review_binding": {
            "relative_path": namespace["V2_REVIEW_RELATIVE_PATH"].as_posix(),
            "sha256": namespace["EXPECTED_V2_REVIEW_FILE_SHA256"],
            "size_bytes": 1,
        },
        "destination": {"ancestor_binding": _local_ancestor_binding(tmp_path)},
        "primary_index": {"url": namespace["PRIMARY_SIMPLE_INDEX_URL"]},
        "torch_index": {
            "url": namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"]
        },
    }

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["construct_candidate"](preflight)

    assert caught.value.code == "PRE_INTENT_CONSTRUCTION_FAILED"
    assert caught.value.detail == "KeyboardInterrupt"
    assert caught.value.telemetry["durable_write_begun"] is False
    assert caught.value.telemetry["durable_attempt_root_created"] is False
    assert caught.value.telemetry["durable_intent_committed"] is False
    assert not destination.exists()


def test_keyboard_interrupt_after_intent_commits_terminal_failure_receipt(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    globals_map = namespace["construct_candidate"].__globals__
    destination = tmp_path / "candidate"
    ancestor_binding = _local_ancestor_binding(tmp_path)
    builder_binding = {
        "relative_path": namespace[
            "BUILDER_NOTEBOOK_RELATIVE_PATH"
        ].as_posix(),
        "sha256": "c" * 64,
        "size_bytes": 1,
    }
    monkeypatch.setitem(
        globals_map,
        "DURABLE_OUTPUT_DIRECTORY",
        destination.as_posix(),
    )
    monkeypatch.setitem(
        globals_map,
        "require_ancestor_binding_unchanged",
        lambda path, expected: expected,
    )
    monkeypatch.setitem(
        globals_map,
        "git_identity",
        lambda *args: ("a" * 40, 1_700_000_000, {"verified": True}),
    )
    monkeypatch.setitem(
        globals_map,
        "project_source_manifest",
        lambda repo_root: {"record_sha256": "b" * 64, "files": []},
    )
    monkeypatch.setitem(
        globals_map,
        "regular_file_binding",
        lambda *args: builder_binding,
    )

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(tempfile, "mkdtemp", interrupt)
    preflight = {
        "repo_root": ROOT,
        "profile_validation": {
            "file_sha256": namespace["EXPECTED_PROFILE_FILE_SHA256"],
            "semantic_sha256": namespace["EXPECTED_PROFILE_SEMANTIC_SHA256"],
        },
        "v2_independent_review_binding": {
            "relative_path": namespace["V2_REVIEW_RELATIVE_PATH"].as_posix(),
            "sha256": namespace["EXPECTED_V2_REVIEW_FILE_SHA256"],
            "size_bytes": 1,
        },
        "destination": {"ancestor_binding": ancestor_binding},
        "primary_index": {"url": namespace["PRIMARY_SIMPLE_INDEX_URL"]},
        "torch_index": {"url": namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"]},
    }

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["construct_candidate"](preflight)

    assert caught.value.code == "UNEXPECTED_CONSTRUCTION_FAILURE"
    assert caught.value.detail == "KeyboardInterrupt"
    assert caught.value.telemetry["durable_intent_committed"] is True
    assert caught.value.telemetry["failure_receipt_committed"] is True
    assert not caught.value.telemetry["network_contact_begun"]
    assert (destination / "attempt-intent.json").is_file()
    assert (destination / "construction-failure-receipt.json").is_file()
    assert not (destination / "construction-receipt.json").exists()
    failure = json.loads(
        (destination / "construction-failure-receipt.json").read_text()
    )
    assert failure["error_detail"] == "KeyboardInterrupt"


def test_terminal_receipt_ambiguity_suppresses_failure_receipt(
    monkeypatch, tmp_path, capsys
):
    namespace = _load_namespace(capsys)
    globals_map = namespace["construct_candidate"].__globals__
    destination = tmp_path / "candidate"
    ancestor_binding = _local_ancestor_binding(tmp_path)
    monkeypatch.setitem(
        globals_map,
        "DURABLE_OUTPUT_DIRECTORY",
        destination.as_posix(),
    )
    monkeypatch.setitem(
        globals_map,
        "require_ancestor_binding_unchanged",
        lambda path, expected: expected,
    )
    monkeypatch.setitem(
        globals_map,
        "git_identity",
        lambda *args: ("a" * 40, 1_700_000_000, {"verified": True}),
    )
    monkeypatch.setitem(
        globals_map,
        "project_source_manifest",
        lambda repo_root: {"record_sha256": "b" * 64, "files": []},
    )
    monkeypatch.setitem(
        globals_map,
        "regular_file_binding",
        lambda *args: {
            "relative_path": namespace[
                "BUILDER_NOTEBOOK_RELATIVE_PATH"
            ].as_posix(),
            "sha256": "c" * 64,
            "size_bytes": 1,
        },
    )

    def ambiguous_terminal_state(*args, **kwargs):
        raise namespace["CandidateConstructionError"](
            "INJECTED_TERMINAL_RECEIPT_AMBIGUITY",
            telemetry={"terminal_receipt_ambiguity": True},
        )

    monkeypatch.setattr(tempfile, "mkdtemp", ambiguous_terminal_state)
    preflight = {
        "repo_root": ROOT,
        "profile_validation": {
            "file_sha256": namespace["EXPECTED_PROFILE_FILE_SHA256"],
            "semantic_sha256": namespace["EXPECTED_PROFILE_SEMANTIC_SHA256"],
        },
        "v2_independent_review_binding": {
            "relative_path": namespace["V2_REVIEW_RELATIVE_PATH"].as_posix(),
            "sha256": namespace["EXPECTED_V2_REVIEW_FILE_SHA256"],
            "size_bytes": 1,
        },
        "destination": {"ancestor_binding": ancestor_binding},
        "primary_index": {"url": namespace["PRIMARY_SIMPLE_INDEX_URL"]},
        "torch_index": {"url": namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"]},
    }

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["construct_candidate"](preflight)

    assert caught.value.code == "INJECTED_TERMINAL_RECEIPT_AMBIGUITY"
    assert caught.value.telemetry["terminal_receipt_ambiguity"] is True
    assert caught.value.telemetry[
        "failure_receipt_skipped_for_terminal_receipt_ambiguity"
    ] is True
    assert (destination / "attempt-intent.json").is_file()
    assert not (destination / "construction-failure-receipt.json").exists()


def test_success_publication_begun_suppresses_post_return_failure_receipt(
    capsys,
):
    namespace = _load_namespace(capsys)
    state = namespace["initial_attempt_state"]()
    state["success_receipt_publish_begun"] = True
    state["terminal_receipt_ambiguity"] = False

    suppressed = namespace[
        "suppress_failure_receipt_if_success_publication_uncertain"
    ](state)

    assert suppressed is True
    assert state["terminal_receipt_ambiguity"] is True
    assert state["success_receipt_may_exist"] is True
    assert state[
        "failure_receipt_skipped_for_terminal_receipt_ambiguity"
    ] is True


def test_v2_profile_review_and_builder_are_bound_in_attempt_intent(capsys):
    namespace = _load_namespace(capsys)
    profile, validation = namespace["validate_profile"](
        ROOT / namespace["PROFILE_RELATIVE_PATH"]
    )
    assert profile is not None
    assert validation == {
        "valid": True,
        "file_sha256": namespace["EXPECTED_PROFILE_FILE_SHA256"],
        "semantic_sha256": namespace["EXPECTED_PROFILE_SEMANTIC_SHA256"],
        "errors": [],
    }
    review = namespace["regular_file_binding"](
        ROOT,
        namespace["V2_REVIEW_RELATIVE_PATH"],
        "V2_REVIEW",
    )
    builder = namespace["regular_file_binding"](
        ROOT,
        namespace["BUILDER_NOTEBOOK_RELATIVE_PATH"],
        "BUILDER",
    )
    record, payload = namespace["build_attempt_intent"](
        validation,
        review,
        namespace["DEFERRED_GIT_REVISION_STATE"],
        {"record_sha256": "b" * 64},
        builder,
        Path("/Volumes/catalog/schema/volume/candidate-0001"),
        [],
        namespace["PRIMARY_SIMPLE_INDEX_URL"],
        namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
    )

    assert review["sha256"] == namespace["EXPECTED_V2_REVIEW_FILE_SHA256"]
    assert record["profile"]["relative_path"] == namespace[
        "PROFILE_RELATIVE_PATH"
    ].as_posix()
    assert record["profile"]["independent_review"] == review
    assert record["source"]["construction_notebook"] == builder
    assert record["source"]["git_revision"] is None
    assert record["source"]["git_revision_verification_state"] == namespace[
        "DEFERRED_GIT_REVISION_STATE"
    ]
    assert payload == namespace["canonical_json_bytes"](record) + b"\n"


@pytest.mark.parametrize(
    ("observed", "accepted"),
    [
        ("24.04.4 LTS", True),
        ("Ubuntu 24.04.4 LTS", True),
        ("Ubuntu 24.04.3 LTS", False),
        ("Debian 24.04.4 LTS", False),
        ("", False),
        (None, False),
    ],
)
def test_operating_system_release_accepts_only_profile_or_pretty_name(
    observed,
    accepted,
    capsys,
):
    namespace = _load_namespace(capsys)
    assert namespace["operating_system_release_matches"](
        "Ubuntu",
        "24.04.4 LTS",
        observed,
    ) is accepted


def test_observe_runtime_preserves_pretty_name_without_false_release_mismatch(
    monkeypatch,
    capsys,
):
    namespace = _load_namespace(capsys)
    profile, validation = namespace["validate_profile"](
        ROOT / namespace["PROFILE_RELATIVE_PATH"]
    )
    assert validation["valid"] is True
    monkeypatch.setitem(
        namespace["observe_runtime"].__globals__,
        "read_os_release",
        lambda: {
            "NAME": "Ubuntu",
            "PRETTY_NAME": "Ubuntu 24.04.4 LTS",
        },
    )

    result = namespace["observe_runtime"](profile)

    assert result["observed"]["operating_system_release"] == (
        "Ubuntu 24.04.4 LTS"
    )
    assert "operating_system_release" not in result["mismatches"]


def test_pip_bootstrap_plan_records_observed_ensurepip_state(
    monkeypatch,
    capsys,
):
    namespace = _load_namespace(capsys)
    globals_map = namespace["pip_bootstrap_plan"].__globals__

    monkeypatch.setattr(
        globals_map["importlib"].util,
        "find_spec",
        lambda name: None,
    )
    absent = namespace["pip_bootstrap_plan"]()
    assert absent["required_pip_version"] == "25.0.1"
    assert absent["ensurepip_observation"] == {
        "available": False,
        "origin": None,
    }

    fake_spec = type("FakeSpec", (), {"origin": "/stdlib/ensurepip/__init__.py"})()
    monkeypatch.setattr(
        globals_map["importlib"].util,
        "find_spec",
        lambda name: fake_spec,
    )
    present = namespace["pip_bootstrap_plan"]()
    assert present["required_pip_version"] == "25.0.1"
    assert present["ensurepip_observation"] == {
        "available": True,
        "origin": "/stdlib/ensurepip/__init__.py",
    }


def test_bind_pip_identity_rechecks_reported_files(
    monkeypatch,
    tmp_path,
    capsys,
):
    namespace = _load_namespace(capsys)
    module_file = tmp_path / "pip" / "__init__.py"
    record_file = tmp_path / "pip-25.0.1.dist-info" / "RECORD"
    module_file.parent.mkdir()
    record_file.parent.mkdir()
    module_file.write_bytes(b"__version__ = '25.0.1'\n")
    record_file.write_bytes(b"pip/__init__.py,,\n")
    python_executable = str(tmp_path / "python")

    def identity_payload():
        return json.dumps(
            {
                "pip_distribution_root": str(tmp_path.resolve()),
                "pip_install_prefix": str(tmp_path.resolve()),
                "pip_module_file": str(module_file.resolve()),
                "pip_module_file_sha256": hashlib.sha256(
                    module_file.read_bytes()
                ).hexdigest(),
                "pip_module_file_size_bytes": module_file.stat().st_size,
                "pip_payload_closure_exact": True,
                "pip_payload_file_count": 2,
                "pip_payload_hashed_record_count": 0,
                "pip_payload_manifest_sha256": "c" * 64,
                "pip_payload_unhashed_record_count": 2,
                "pip_payload_unrecorded_bytecode_count": 0,
                "pip_record_file": str(record_file.resolve()),
                "pip_record_file_sha256": hashlib.sha256(
                    record_file.read_bytes()
                ).hexdigest(),
                "pip_record_file_size_bytes": record_file.stat().st_size,
                "pip_version": "25.0.1",
                "python_executable": str(Path(python_executable).resolve()),
            },
            sort_keys=True,
        ).encode("utf-8")

    frozen_payload = identity_payload()
    identity_commands = []

    def fake_identity_run_tool(*args, **kwargs):
        identity_commands.append(list(args[2]))
        return frozen_payload

    monkeypatch.setitem(
        namespace["bind_pip_identity"].__globals__,
        "run_tool",
        fake_identity_run_tool,
    )
    identity = namespace["bind_pip_identity"](
        [],
        "bind_test_pip",
        python_executable,
        tmp_path,
        {},
        namespace["PRIMARY_SIMPLE_INDEX_URL"],
        namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
        {},
        object(),
        "25.0.1",
        expected_root=tmp_path,
    )
    assert identity["pip_version"] == "25.0.1"
    assert identity_commands == [
        [
            python_executable,
            "-I",
            "-B",
            "-c",
            namespace["PIP_IDENTITY_PROBE"],
        ]
    ]

    invalid_closure = json.loads(frozen_payload)
    invalid_closure["pip_payload_closure_exact"] = False
    monkeypatch.setitem(
        namespace["bind_pip_identity"].__globals__,
        "run_tool",
        lambda *args, **kwargs: json.dumps(invalid_closure).encode("utf-8"),
    )
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["bind_pip_identity"](
            [],
            "bind_test_pip",
            python_executable,
            tmp_path,
            {},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            {},
            object(),
            "25.0.1",
            expected_root=tmp_path,
        )
    assert caught.value.code == "PIP_IDENTITY_PAYLOAD_CLOSURE_INVALID"

    monkeypatch.setitem(
        namespace["bind_pip_identity"].__globals__,
        "run_tool",
        lambda *args, **kwargs: frozen_payload,
    )
    module_file.write_bytes(b"changed\n")
    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["bind_pip_identity"](
            [],
            "bind_test_pip",
            python_executable,
            tmp_path,
            {},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            {},
            object(),
            "25.0.1",
            expected_root=tmp_path,
        )
    assert caught.value.code == "PIP_IDENTITY_FILE_BINDING_MISMATCH"


def test_bootstrap_inspects_retains_and_hash_locks_exact_pip_wheel(
    monkeypatch,
    tmp_path,
    capsys,
):
    namespace = _load_namespace(capsys)
    candidate_root = tmp_path / "candidate"
    tool_wheelhouse = candidate_root / "build-tool-wheelhouse"
    tool_wheelhouse.mkdir(parents=True)
    build_venv = tmp_path / "build-venv"
    venv_python = str(build_venv / "bin" / "python")
    wheel_record = {
        "filename": "pip-25.0.1-py3-none-any.whl",
        "sha256": "a" * 64,
        "size_bytes": 123,
        "distribution_name": "pip",
        "normalized_name": "pip",
        "version": "25.0.1",
        "wheel_tags": ["py3-none-any"],
        "embedded_record_sha256": "b" * 64,
        "embedded_payload_file_count": 9,
    }
    events = []
    commands = []

    def fake_bind(*args, **kwargs):
        step = args[1]
        events.append(step)
        if step == "bind_isolated_venv_pip_identity_after_bootstrap":
            return {"bound_scope": "isolated_venv"}
        return {"bound_scope": "host"}

    def fake_run_tool(
        journal,
        step,
        argv,
        cwd,
        environment,
        primary_url,
        torch_url,
        attempt_state=None,
        phase_flags=(),
        durable_attempt=None,
    ):
        events.append(step)
        commands.append(
            {"step": step, "argv": list(argv), "phase_flags": phase_flags}
        )
        if step == "download_bootstrap_pip_wheel":
            (tool_wheelhouse / wheel_record["filename"]).write_bytes(b"wheel")
        return b""

    def fake_inspect(directory):
        events.append("inspect_bootstrap_pip_wheel")
        assert directory == tool_wheelhouse
        return [wheel_record]

    globals_map = namespace["bootstrap_pip_into_isolated_venv"].__globals__
    monkeypatch.setitem(globals_map, "bind_pip_identity", fake_bind)
    monkeypatch.setitem(globals_map, "run_tool", fake_run_tool)
    monkeypatch.setitem(globals_map, "inspect_wheel_directory", fake_inspect)

    attempt_state = {}
    result = namespace["bootstrap_pip_into_isolated_venv"](
        [],
        tmp_path,
        build_venv,
        venv_python,
        tool_wheelhouse,
        {},
        {},
        namespace["PRIMARY_SIMPLE_INDEX_URL"],
        namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
        attempt_state,
        object(),
    )

    assert events == [
        "bind_host_pip_identity_before_bootstrap",
        "download_bootstrap_pip_wheel",
        "inspect_bootstrap_pip_wheel",
        "rebind_host_pip_identity_before_target_install",
        "bootstrap_pip_into_isolated_venv",
        "bind_isolated_venv_pip_identity_after_bootstrap",
    ]
    assert result["bootstrap_wheel"] == wheel_record
    assert result["host_pip_identity"] == {
        "bound_scope": "host"
    }
    assert result["isolated_venv_pip_identity"] == {
        "bound_scope": "isolated_venv"
    }
    assert result[
        "host_pip_identity_reverified_before_target_install"
    ] is True
    assert attempt_state["host_pip_identity"] == result["host_pip_identity"]
    assert attempt_state[
        "host_pip_identity_reverified_before_target_install"
    ] is True
    assert attempt_state["bootstrap_pip_wheel_binding"] == wheel_record
    assert attempt_state["bootstrap_pip_lock_binding"] == result[
        "bootstrap_lock"
    ]
    assert attempt_state["isolated_venv_pip_identity"] == result[
        "isolated_venv_pip_identity"
    ]
    assert (tool_wheelhouse / wheel_record["filename"]).is_file()
    bootstrap_lock = candidate_root / "bootstrap-pip.lock"
    assert bootstrap_lock.is_file()
    assert result["bootstrap_lock"]["filename"] == bootstrap_lock.name
    assert result["bootstrap_lock"]["sha256"] == hashlib.sha256(
        bootstrap_lock.read_bytes()
    ).hexdigest()
    download = commands[0]
    assert download["argv"][:5] == [
        namespace["sys"].executable,
        "-I",
        "-B",
        "-m",
        "pip",
    ]
    assert download["argv"][-1] == "pip==25.0.1"
    install = commands[1]
    assert install["argv"][:5] == [
        namespace["sys"].executable,
        "-I",
        "-B",
        "-m",
        "pip",
    ]
    assert install["argv"].index("--python") < install["argv"].index("install")
    assert install["argv"][install["argv"].index("--python") + 1] == venv_python
    assert "--require-hashes" in install["argv"]
    assert str(bootstrap_lock) in install["argv"]
    assert install["phase_flags"] == (
        "bootstrap_pip_install_begun",
        "build_tool_install_begun",
    )


def test_bootstrap_rejects_wrong_wheel_before_install(
    monkeypatch,
    tmp_path,
    capsys,
):
    namespace = _load_namespace(capsys)
    candidate_root = tmp_path / "candidate"
    tool_wheelhouse = candidate_root / "build-tool-wheelhouse"
    tool_wheelhouse.mkdir(parents=True)
    steps = []

    def fake_run_tool(
        journal,
        step,
        argv,
        cwd,
        environment,
        primary_url,
        torch_url,
        attempt_state=None,
        phase_flags=(),
        durable_attempt=None,
    ):
        steps.append(step)
        if step == "download_bootstrap_pip_wheel":
            (tool_wheelhouse / "wheel-0.45.1-py3-none-any.whl").write_bytes(
                b"wrong"
            )
        return b""

    globals_map = namespace["bootstrap_pip_into_isolated_venv"].__globals__
    monkeypatch.setitem(
        globals_map,
        "bind_pip_identity",
        lambda *args, **kwargs: {"pip_version": "25.0.1"},
    )
    monkeypatch.setitem(globals_map, "run_tool", fake_run_tool)
    monkeypatch.setitem(
        globals_map,
        "inspect_wheel_directory",
        lambda directory: [
            {
                "filename": "wheel-0.45.1-py3-none-any.whl",
                "normalized_name": "wheel",
                "version": "0.45.1",
            }
        ],
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["bootstrap_pip_into_isolated_venv"](
            [],
            tmp_path,
            tmp_path / "build-venv",
            str(tmp_path / "build-venv" / "bin" / "python"),
            tool_wheelhouse,
            {},
            {},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            {},
            object(),
        )

    assert caught.value.code == "BOOTSTRAP_PIP_WHEEL_IDENTITY_MISMATCH"
    assert steps == ["download_bootstrap_pip_wheel"]


def test_bootstrap_rejects_host_pip_identity_change_before_install(
    monkeypatch,
    tmp_path,
    capsys,
):
    namespace = _load_namespace(capsys)
    candidate_root = tmp_path / "candidate"
    tool_wheelhouse = candidate_root / "build-tool-wheelhouse"
    tool_wheelhouse.mkdir(parents=True)
    steps = []
    identity_steps = []

    def fake_bind(*args, **kwargs):
        step = args[1]
        identity_steps.append(step)
        return {
            "pip_version": "25.0.1",
            "pip_payload_manifest_sha256": (
                "a" * 64
                if step == "bind_host_pip_identity_before_bootstrap"
                else "b" * 64
            ),
        }

    def fake_run_tool(
        journal,
        step,
        argv,
        cwd,
        environment,
        primary_url,
        torch_url,
        attempt_state=None,
        phase_flags=(),
        durable_attempt=None,
    ):
        steps.append(step)
        if step == "download_bootstrap_pip_wheel":
            (tool_wheelhouse / "pip-25.0.1-py3-none-any.whl").write_bytes(
                b"pip-wheel"
            )
        return b""

    globals_map = namespace["bootstrap_pip_into_isolated_venv"].__globals__
    monkeypatch.setitem(globals_map, "bind_pip_identity", fake_bind)
    monkeypatch.setitem(globals_map, "run_tool", fake_run_tool)
    monkeypatch.setitem(
        globals_map,
        "inspect_wheel_directory",
        lambda directory: [
            {
                "filename": "pip-25.0.1-py3-none-any.whl",
                "normalized_name": "pip",
                "version": "25.0.1",
                "sha256": "c" * 64,
            }
        ],
    )

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["bootstrap_pip_into_isolated_venv"](
            [],
            tmp_path,
            tmp_path / "build-venv",
            str(tmp_path / "build-venv" / "bin" / "python"),
            tool_wheelhouse,
            {},
            {},
            namespace["PRIMARY_SIMPLE_INDEX_URL"],
            namespace["PYTORCH_CPU_SIMPLE_INDEX_URL"],
            {},
            object(),
        )

    assert caught.value.code == "HOST_PIP_IDENTITY_CHANGED_DURING_BOOTSTRAP"
    assert identity_steps == [
        "bind_host_pip_identity_before_bootstrap",
        "rebind_host_pip_identity_before_target_install",
    ]
    assert steps == ["download_bootstrap_pip_wheel"]


def test_wheel_only_and_hash_lock_candidate_guards(tmp_path, capsys):
    namespace = _load_namespace(capsys)
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    (wheelhouse / "demo-1.0.tar.gz").write_bytes(b"sdist")

    with pytest.raises(namespace["CandidateConstructionError"]) as caught:
        namespace["inspect_wheel_directory"](wheelhouse)
    assert caught.value.code == "SDIST_OR_NON_WHEEL_ARTIFACT_PRESENT"

    lock = namespace["lock_candidate_bytes"](
        [
            {
                "normalized_name": "torch",
                "version": "2.12.1+cpu",
                "sha256": "1" * 64,
            },
            {
                "normalized_name": "numpy",
                "version": "2.4.6",
                "sha256": "2" * 64,
            },
        ]
    ).decode("ascii")
    assert "numpy==2.4.6 \\\n    --hash=sha256:" + "2" * 64 in lock
    assert "torch==2.12.1+cpu \\\n    --hash=sha256:" + "1" * 64 in lock


def test_success_receipt_is_not_staged_and_is_committed_after_cleanup():
    source = NOTEBOOK.read_text(encoding="utf-8")
    construction = source[source.index("def construct_candidate(") :]
    publish_index = construction.index("publish_binding = copy_tree_no_clobber(")
    cleanup_index = construction.index(
        "shutil.rmtree(staging_root)",
        publish_index,
    )
    success_receipt_index = construction.index(
        "durable_receipt_binding = commit_success_receipt(",
        cleanup_index,
    )

    assert publish_index < cleanup_index < success_receipt_index
    assert "candidate_root / receipt_relative" not in construction
