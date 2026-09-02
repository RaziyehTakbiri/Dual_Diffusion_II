"""Hostile, no-training tests for the finite-A1 V2 recovery runner."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Dict

import pytest

from heterodiff.experiments import (
    finite_association_development_checkpoint_runner_v2 as runner,
)
from heterodiff.experiments.finite_association_production_order import (
    frozen_production_source_manifest,
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = _ROOT / runner.RUNNER_RELATIVE_PATH
_ZERO_SHA256 = "0" * 64


def _probe() -> Dict[str, object]:
    digests = [str(index) * 64 for index in range(1, 6)]
    return {
        "schema": "heterodiff-a1-development-runtime-preflight-v2",
        "lane_id": runner.LANE_ID,
        "python": "3.11.5",
        "machine": "arm64",
        "profile": {
            "system": "Darwin",
            "machine": "arm64",
            "python_implementation": "CPython",
            "python_version": "3.11.5",
            "python_abi": "cpython-311-darwin",
            "pointer_bits": 64,
            "byteorder": "little",
        },
        "macos_version": "15.0",
        "translated": False,
        "distributions": dict(runner.REQUIRED_DISTRIBUTIONS),
        "environment": {
            "python_version": "3.11.5",
            "numpy_version": "2.4.6",
            "scipy_version": "1.17.1",
            "torch_version": "2.12.1",
            "torch_cpu_only": True,
            "torch_threads": 1,
            "torch_interop_threads": 1,
            "deterministic_algorithms": True,
        },
        "native_pools": [
            {
                "user_api": "blas",
                "internal_api": "openblas",
                "num_threads": 1,
                "prefix": "libopenblas",
                "filepath": "/synthetic/libopenblas.dylib",
                "version": "0.3.31",
                "threading_layer": "pthreads",
                "architecture": "ArmV8",
            }
        ],
        "fixture_sha256": runner.TARGET_FIXTURE_SHA256,
        "prerequisite_content_sha256": [
            "69b4bbea518ab816bb1e96952c3ddda5295257f66f0f8c902ba38eec10b6c339",
            "2c9da1e2e4d98e14d91459983a3b8fcbbf4b5409574863f68cba96642a89f08b",
            "09273f6bcee7c1a09165392e6ecf0125157b747d242c1f993a982ce3b2833cc7",
            "d6326ffb38c4c3ccf5aed1002f8cbd75fe5411f60d07172d5511730a63daba45",
            "ff37337476c48fee1c01e812f78cd22c7f2ed69298329f79cd87ab2aab3de937",
        ],
        "source_manifest_sha256": _ZERO_SHA256,
        "training_configuration_sha256": _ZERO_SHA256,
        "preflight": {
            "seed": runner.SEED,
            "budget": runner.BUDGET,
            "method": runner.METHOD,
            "composition_mode": "guided",
            "input_features": 21,
            "hidden_width": 32,
            "updates": runner.EXPECTED_UPDATES,
            "torch_generator_seed": 1,
            "source_sha256": _ZERO_SHA256,
            "configuration_sha256": _ZERO_SHA256,
            "fixture_sha256": runner.TARGET_FIXTURE_SHA256,
            "custody_sha256": "6" * 64,
            "all_dataset_sha256": digests[:3],
            "all_batch_schedule_sha256": digests + ["6" * 64],
            "dataset_sha256": "1" * 64,
            "batch_schedule_sha256": "2" * 64,
            "training_tensor_sha256": "3" * 64,
            "initial_parameter_sha256": "4" * 64,
            "preflight_sha256": "5" * 64,
            "parameter_count": 1793,
            "forward_multiply_add_count": 1728,
        },
    }


def _verified_inner() -> Dict[str, object]:
    runtime: Dict[str, object] = {
        "schema": "heterodiff-a1-isolated-runtime-v3",
        "python": "3.11.5",
        "python_implementation": "CPython",
        "numpy": "2.4.6",
        "scipy": "1.17.1",
        "torch": "2.12.1",
        "threadpoolctl": "3.6.0",
        "system": "Darwin",
        "platform": "macOS-15.0-arm64-arm-64bit",
        "release": "24.0.0",
        "machine": "arm64",
        "processor": "arm",
        "cpu_identity": "arm64",
        "thread_environment": {
            **{name: "1" for name in runner.THREAD_ENVIRONMENT},
            "PYTHONHASHSEED": "0",
            "CUDA_VISIBLE_DEVICES": "",
        },
        "native_pools": _probe()["native_pools"],
        "numpy_configuration": {"synthetic": True},
        "torch_environment": _probe()["environment"],
    }
    runtime_sha256 = hashlib.sha256(runner._canonical_json_bytes(runtime)).hexdigest()
    runtime["sha256"] = runtime_sha256
    return {
        "schema": "heterodiff-a1-development-inner-success-summary-v2",
        "lane_id": runner.LANE_ID,
        "run_key_sha256": "a" * 64,
        "optimizer_steps_taken": runner.EXPECTED_UPDATES,
        "fixture_sha256": runner.TARGET_FIXTURE_SHA256,
        "parent_confirmed_zero_child_exit": True,
        "inner_scientific_decision_eligible": False,
        "certified_maximum_absolute_correction": 1.0,
        "process_peak_rss_bytes": 1024,
        "checkpoint_sha256": "1" * 64,
        "ledger_sha256": "2" * 64,
        "prepared_ledger_sha256": "b" * 64,
        "running_ledger_sha256": "c" * 64,
        "launch_authorization_sha256": "d" * 64,
        "launch_receipt_sha256": "e" * 64,
        "worker_session_sha256": "f" * 64,
        "worker_process_identity_sha256": "7" * 64,
        "worker_process_id": 101,
        "worker_parent_process_id": 4242,
        "campaign_sha256": "8" * 64,
        "success_receipt_sha256": "9" * 64,
        "execution_runtime_sha256": runtime_sha256,
        "execution_runtime_record": runtime,
        "source_manifest_sha256": _ZERO_SHA256,
        "training_configuration_sha256": _ZERO_SHA256,
        "preflight_sha256": "5" * 64,
        "dataset_sha256": "1" * 64,
        "batch_schedule_sha256": "2" * 64,
        "initial_parameter_sha256": "4" * 64,
        "parameter_sha256": "5" * 64,
        "classifier_sha256": "6" * 64,
        "certificate_sha256": "4" * 64,
        "optimizer_transcript_sha256": "5" * 64,
        "completion_receipt_sha256": "8" * 64,
        "checkpoint_file": ("a" * 64) + ".pt",
        "final_empirical_risk": 0.25,
        "maximum_unclipped_gradient_norm": 0.75,
        "optimizer_wall_seconds": 1.0,
        "total_wall_seconds": 2.0,
        "total_cpu_seconds": 1.5,
    }


def _install_synthetic_preflight(
    monkeypatch: pytest.MonkeyPatch,
    workspace: Path,
    *,
    probe_override: Dict[str, object] | None = None,
    verify_override: Dict[str, object] | None = None,
    verify_fails: bool = False,
    json_calls: list[tuple[tuple[object, ...], Dict[str, object]]] | None = None,
) -> Dict[str, object]:
    runner_payload = b"SYNTHETIC_RUNNER = True\n"
    runner_sha256 = hashlib.sha256(runner_payload).hexdigest()
    test_payload = b"SYNTHETIC_HOSTILE_TEST = True\n"
    test_sha256 = hashlib.sha256(test_payload).hexdigest()
    identity_source_payload = b"SYNTHETIC_CANONICAL_IDENTITY = True\n"
    identity_source_sha256 = hashlib.sha256(identity_source_payload).hexdigest()
    identity_test_payload = b"SYNTHETIC_IDENTITY_TEST = True\n"
    identity_test_sha256 = hashlib.sha256(identity_test_payload).hexdigest()
    binding = {
        "source_manifest_sha256": _ZERO_SHA256,
        "training_configuration_sha256": _ZERO_SHA256,
    }
    retained_freeze = runner._read_json(_ROOT / runner.FREEZE_RELATIVE_PATH)
    v1_custody = dict(retained_freeze["v1_failure_custody"])
    semantic_projection = {
        name: retained_freeze.get(name) for name in runner._STATIC_FREEZE_SECTION_NAMES
    }
    monkeypatch.setattr(
        runner,
        "STATIC_FREEZE_SEMANTIC_SHA256",
        hashlib.sha256(runner._canonical_json_bytes(semantic_projection)).hexdigest(),
    )
    retained_freeze["implementation_binding"] = {
        "runner_source_path": runner.RUNNER_RELATIVE_PATH,
        "runner_source_sha256": runner_sha256,
        "runner_test_path": runner.RUNNER_TEST_RELATIVE_PATH,
        "runner_test_sha256": test_sha256,
        "isolated_runner_source_path": runner.ISOLATED_RUNNER_RELATIVE_PATH,
        "isolated_runner_source_sha256": identity_source_sha256,
        "module_identity_test_path": runner.MODULE_IDENTITY_TEST_RELATIVE_PATH,
        "module_identity_test_sha256": identity_test_sha256,
        **binding,
    }
    retained_freeze["authorization"] = {
        "current_state": "FROZEN_EXECUTION_AUTHORIZED",
        "development_checkpoint_execution_authorized": True,
        "execution_conditions": [
            "V1_FAILURE_CUSTODY_REVALIDATED",
            "ZERO_UPDATE_V1_INFRASTRUCTURE_FAILURE_DISCLOSED",
            "RUNNER_SOURCE_AND_TEST_HASH_BOUND",
            "FINAL_SOURCE_MANIFEST_RECOMPUTED",
            "FINAL_TRAINING_CONFIGURATION_RECOMPUTED",
            "CANONICAL_MODULE_IDENTITY_REGRESSION_PASSED",
            "TARGET_RUNTIME_ATTESTED",
            "CAPSULE_ROOT_ABSENT",
            "NO_WARM_START_OR_CACHE_REUSE",
            "SINGLE_USE_PERMIT_ISSUED",
        ],
        "execution_permit_issuance_delegated_to_hash_bound_runner_after_fresh_preflight": True,
        "execution_permit_issued": False,
        "static_parameter_freeze_complete": True,
    }
    retained_freeze_payload = runner._canonical_json_bytes(retained_freeze)
    freeze_sha256 = hashlib.sha256(retained_freeze_payload).hexdigest()
    freeze: Dict[str, object] = retained_freeze
    for relative, payload in (
        (runner.FREEZE_RELATIVE_PATH, retained_freeze_payload),
        (runner.RUNNER_RELATIVE_PATH, runner_payload),
        (runner.RUNNER_TEST_RELATIVE_PATH, test_payload),
        (runner.ISOLATED_RUNNER_RELATIVE_PATH, identity_source_payload),
        (runner.MODULE_IDENTITY_TEST_RELATIVE_PATH, identity_test_payload),
    ):
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    monkeypatch.setattr(runner, "_workspace_root", lambda: workspace)
    monkeypatch.setattr(runner, "_require_authorized_freeze", lambda root: freeze)
    monkeypatch.setattr(
        runner, "_require_v1_failure_custody", lambda root: dict(v1_custody)
    )
    monkeypatch.setattr(runner, "_target_python", lambda root: Path(sys.executable))

    def synthetic_sha256(path: Path, **kwargs: object) -> str:
        if path == workspace / runner.FREEZE_RELATIVE_PATH:
            return freeze_sha256
        if path == workspace / runner.RUNNER_RELATIVE_PATH:
            return runner_sha256
        if path == workspace / runner.RUNNER_TEST_RELATIVE_PATH:
            return test_sha256
        if path == workspace / runner.ISOLATED_RUNNER_RELATIVE_PATH:
            return identity_source_sha256
        if path == workspace / runner.MODULE_IDENTITY_TEST_RELATIVE_PATH:
            return identity_test_sha256
        return _ZERO_SHA256

    monkeypatch.setattr(runner, "_sha256_file", synthetic_sha256)

    def retain_authorization(
        root: Path, destination: Path, *, bindings: object
    ) -> None:
        runner._write_retained_bytes(
            destination / runner.RETAINED_FREEZE_FILE_NAME,
            retained_freeze_payload,
        )
        runner._write_retained_bytes(
            destination / runner.RETAINED_RUNNER_TEST_FILE_NAME,
            test_payload,
        )
        runner._write_retained_bytes(
            destination / runner.RETAINED_MODULE_IDENTITY_TEST_FILE_NAME,
            identity_test_payload,
        )

    monkeypatch.setattr(runner, "_retain_authorization_evidence", retain_authorization)

    def copy_capsule(root: Path, capsule: Path) -> Dict[str, object]:
        marker = capsule / "src/synthetic_marker.py"
        marker.parent.mkdir(parents=True)
        marker_payload = b"SYNTHETIC = True\n"
        marker.write_bytes(marker_payload)
        marker.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        capsule_runner = capsule / runner.RUNNER_RELATIVE_PATH
        capsule_runner.parent.mkdir(parents=True, exist_ok=True)
        capsule_runner.write_bytes(runner_payload)
        capsule_runner.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        capsule_identity_runner = capsule / runner.ISOLATED_RUNNER_RELATIVE_PATH
        capsule_identity_runner.parent.mkdir(parents=True, exist_ok=True)
        capsule_identity_runner.write_bytes(identity_source_payload)
        capsule_identity_runner.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        manifest: Dict[str, object] = {
            "schema": "heterodiff-a1-development-source-capsule-manifest-v2",
            "lane_id": runner.LANE_ID,
            "file_count": 3,
            "files": [
                {
                    "path": runner.RUNNER_RELATIVE_PATH,
                    "bytes": len(runner_payload),
                    "sha256": runner_sha256,
                },
                {
                    "path": runner.ISOLATED_RUNNER_RELATIVE_PATH,
                    "bytes": len(identity_source_payload),
                    "sha256": identity_source_sha256,
                },
                {
                    "path": "src/synthetic_marker.py",
                    "bytes": len(marker_payload),
                    "sha256": hashlib.sha256(marker_payload).hexdigest(),
                },
            ],
        }
        manifest["manifest_sha256"] = hashlib.sha256(
            runner._canonical_json_bytes(manifest)
        ).hexdigest()
        return manifest

    monkeypatch.setattr(runner, "_copy_capsule", copy_capsule)
    calls = {"count": 0}

    def json_child(*args: object, **kwargs: object) -> Dict[str, object]:
        if json_calls is not None:
            json_calls.append((args, kwargs))
        calls["count"] += 1
        if calls["count"] == 1:
            return _probe() if probe_override is None else probe_override
        if verify_fails:
            raise runner.DevelopmentCheckpointRefusal("hostile verifier refusal")
        return _verified_inner() if verify_override is None else verify_override

    monkeypatch.setattr(runner, "_run_json_subprocess", json_child)
    return freeze


class _ZeroExitProcess:
    pid = 4242

    def wait(self, timeout: object = None) -> int:
        return 0


def test_import_surface_is_stdlib_only_and_contract_is_literal() -> None:
    tree = ast.parse(_SOURCE.read_text("utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("heterodiff")
        if isinstance(node, ast.Import):
            assert all(not item.name.startswith("heterodiff") for item in node.names)

    assert (runner.METHOD, runner.SEED, runner.BUDGET) == ("guided", 1729, 32768)
    assert runner.EXPECTED_UPDATES == 3000
    assert runner.MAXIMUM_WALL_SECONDS == 3600
    assert runner.MAXIMUM_PEAK_RSS_BYTES == 8 * 1024**3
    assert runner.MAXIMUM_ARTIFACT_BYTES == 2 * 1024**3
    assert (
        tuple(inspect.signature(runner.execute_development_checkpoint).parameters) == ()
    )


def test_exact_installed_venv_interpreter_is_accepted() -> None:
    expected = _ROOT / ".venv-m1/bin/python"
    assert expected.is_symlink(), "fixture exercises the normal venv symlink layout"
    assert runner._target_python(_ROOT) == expected


@pytest.mark.parametrize(
    ("gate_payload", "expected_returncode"),
    ((runner._LAUNCH_GATE_TOKEN, 0), (b"", 73)),
)
def test_exact_child_bootstrap_requires_the_launch_gate_before_module_entry(
    gate_payload: bytes, expected_returncode: int
) -> None:
    read_fd, write_fd = os.pipe()
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(_ROOT / "src")
    environment[runner._LAUNCH_GATE_ENVIRONMENT_NAME] = str(read_fd)
    child = subprocess.Popen(
        (
            sys.executable,
            "-P",
            "-c",
            runner._ISOLATED_RUNNER_GATE_BOOTSTRAP,
            "--help",
        ),
        env=environment,
        pass_fds=(read_fd,),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if gate_payload:
        assert os.write(write_fd, gate_payload) == len(gate_payload)
    os.close(write_fd)
    os.close(read_fd)
    stdout, _ = child.communicate(timeout=30)
    assert child.returncode == expected_returncode
    assert (b"usage:" in stdout) is (expected_returncode == 0)


def test_runtime_environment_overrides_every_determinism_control() -> None:
    hostile = {name: "99" for name in runner.THREAD_ENVIRONMENT}
    hostile.update({"PYTHONHASHSEED": "random", "CUDA_VISIBLE_DEVICES": "0"})
    observed = runner._runtime_environment(hostile)
    assert {observed[name] for name in runner.THREAD_ENVIRONMENT} == {"1"}
    assert observed["PYTHONHASHSEED"] == "0"
    assert observed["CUDA_VISIBLE_DEVICES"] == ""


def test_capsule_closure_equals_the_inner_training_source_closure() -> None:
    expected = frozen_production_source_manifest(_ROOT)
    rows = runner._source_file_rows(_ROOT)
    normalized = [
        {"path": row["path"], "sha256": row["sha256"], "size_bytes": row["bytes"]}
        for row in rows
    ]
    assert sorted(normalized, key=lambda row: row["path"]) == expected["files"]


def test_copied_capsule_inputs_are_immutable(tmp_path: Path) -> None:
    capsule = tmp_path / "capsule"
    capsule.mkdir()
    manifest = runner._copy_capsule(_ROOT, capsule)
    assert manifest["files"]
    for row in manifest["files"]:
        copied = capsule / str(row["path"])
        assert copied.is_file() and not copied.is_symlink()
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == row["sha256"]
        assert copied.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0


def test_synthetic_success_is_capsule_local_and_single_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    json_calls = []
    _install_synthetic_preflight(monkeypatch, workspace, json_calls=json_calls)
    popen_calls = []

    def popen(command: object, **kwargs: object) -> _ZeroExitProcess:
        popen_calls.append((tuple(command), kwargs))
        return _ZeroExitProcess()

    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    result = runner.execute_development_checkpoint()
    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH

    assert result["state"] == "SUCCESS_DEVELOPMENT_CHECKPOINT"
    assert result["retry_permitted"] is False
    assert result["scientific_result_eligible"] is False
    assert result["production_order_admissible"] is False
    assert result["qualifies_r1"] is result["qualifies_r2"] is False
    assert (
        result["retained_authorized_freeze_sha256"]
        == hashlib.sha256(
            (artifact / runner.RETAINED_FREEZE_FILE_NAME).read_bytes()
        ).hexdigest()
    )
    assert (
        result["retained_runner_test_sha256"]
        == hashlib.sha256(
            (artifact / runner.RETAINED_RUNNER_TEST_FILE_NAME).read_bytes()
        ).hexdigest()
    )
    assert len(popen_calls) == 1
    command, options = popen_calls[0]
    assert command[-6:] == (
        "--seed",
        "1729",
        "--budget",
        "32768",
        "--method",
        "guided",
    )
    assert Path(str(options["cwd"])) == artifact / runner.CAPSULE_DIRECTORY_NAME
    assert options["env"]["PYTHONPATH"] == str(
        artifact / runner.CAPSULE_DIRECTORY_NAME / "src"
    )
    assert options["env"]["PYTHONSAFEPATH"] == "1"
    assert command[1] == "-P"
    assert command[2] == "-c"
    assert command[3] == runner._ISOLATED_RUNNER_GATE_BOOTSTRAP
    gate_fd = int(options["env"][runner._LAUNCH_GATE_ENVIRONMENT_NAME])
    assert options["pass_fds"] == (gate_fd,)
    assert "raise SystemExit(73)" in command[3]
    assert len(json_calls) == 3
    for arguments, keywords in json_calls:
        assert tuple(arguments[0])[1] == "-P"
        assert keywords["environment"]["PYTHONSAFEPATH"] == "1"
    assert options["start_new_session"] is True
    assert not (workspace / runner.INNER_CAMPAIGN_RELATIVE_PATH).exists()
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="retry is forbidden"):
        runner.execute_development_checkpoint()


def test_terminal_custody_returns_all_partial_evidence_digests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / "artifact"
    inner = (
        artifact / runner.CAPSULE_DIRECTORY_NAME / runner.INNER_CAMPAIGN_RELATIVE_PATH
    )
    paths = {
        "retained_authorized_freeze_sha256": (
            artifact / runner.RETAINED_FREEZE_FILE_NAME
        ),
        "retained_runner_test_sha256": (
            artifact / runner.RETAINED_RUNNER_TEST_FILE_NAME
        ),
        "retained_module_identity_test_sha256": (
            artifact / runner.RETAINED_MODULE_IDENTITY_TEST_FILE_NAME
        ),
        "attempt_sha256": artifact / "attempt.json",
        "execution_permit_sha256": artifact / "execution-permit.json",
        "execution_permit_consumption_sha256": artifact
        / "execution-permit-consumption.json",
        "execution_outcome_linkage_sha256": artifact / "execution-outcome-linkage.json",
        "capsule_manifest_file_sha256": artifact / "capsule-source-manifest.json",
        "runtime_preflight_file_sha256": artifact / "runtime-preflight.json",
        "partial_inner_ledger_sha256": inner / "ledger.json",
        "inner_stdout_sha256": artifact / "inner-run.stdout",
        "inner_stderr_sha256": artifact / "inner-run.stderr",
    }
    expected = {}
    for index, (name, path) in enumerate(paths.items()):
        payload = f"evidence-{index}\n".encode("ascii")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        expected[name] = hashlib.sha256(payload).hexdigest()

    v1_custody = runner._read_json(_ROOT / runner.FREEZE_RELATIVE_PATH)[
        "v1_failure_custody"
    ]
    monkeypatch.setattr(
        runner, "_require_v1_failure_custody", lambda root: dict(v1_custody)
    )
    expected["v1_failure_custody_sha256"] = runner._v1_failure_custody_sha256(
        v1_custody
    )

    assert runner._terminal_custody(artifact) == expected


def test_real_v1_failure_custody_matches_the_v2_machine_freeze() -> None:
    expected = runner._read_json(_ROOT / runner.FREEZE_RELATIVE_PATH)[
        "v1_failure_custody"
    ]
    observed = runner._require_v1_failure_custody(_ROOT)
    assert observed == expected
    assert observed["regular_file_count"] == 269
    assert observed["total_regular_file_bytes"] == 16_474_540
    assert observed["artifact_inventory_sha256"] == (
        "c371a749a025527d8f34a305cca29da57f1ecfaf60ffc8d770d8e0c6866adbd9"
    )
    assert observed["failure_receipt_raw_sha256"] == (
        "005772f7dbbe5fc43696bd1f56dca4ec33f15bcc8bc4683558aa597260e4b721"
    )
    assert observed["failure_receipt_record_sha256"] == (
        "fb8019f05982a128fe8a5c5d6bc3d60b6e009eece936afd053b7bbe8025f6e2b"
    )
    assert observed["ledger_raw_sha256"] == (
        "e9df396654a7763157259e4ace1c77eee6e0c1555881cdb1be5e1cab8e6f5016"
    )
    assert observed["inner_stderr_raw_sha256"] == (
        "b1fdeaeec243e4f518930f7f4f2391b491b2c71bd14d3040085fcb459a3d0221"
    )
    assert observed["machine_freeze_raw_sha256"] == (
        "8ba0f406aee1428013d898077aa72e8178aa0d8fc34fb21c15aeb96129985c44"
    )
    assert observed["optimizer_updates"] == 0
    assert observed["checkpoint_file_count"] == 0
    assert observed["checkpoint_present"] is False


def test_v1_custody_change_during_live_child_is_terminal_and_never_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    freeze = _install_synthetic_preflight(monkeypatch, workspace)
    base = dict(freeze["v1_failure_custody"])
    calls = {"count": 0}

    def drifting_v1_custody(root: Path) -> Dict[str, object]:
        calls["count"] += 1
        observed = dict(base)
        if calls["count"] >= 2:
            observed["regular_file_count"] = 270
        return observed

    monkeypatch.setattr(runner, "_require_v1_failure_custody", drifting_v1_custody)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="changed"):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not (artifact / "success-receipt.json").exists()
    failure = runner._read_json(artifact / "failure-receipt.json")
    assert failure["state"] == "REFUSED"
    assert failure["checkpoint_claimed"] is False
    assert failure["scientific_result_eligible"] is False
    assert failure["boundary_drift"]["root_binding_changed"] is True


def test_timeout_kills_the_process_group_and_preserves_terminal_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    waits = []

    class TimeoutProcess:
        pid = 4343

        def wait(self, timeout: object = None) -> int:
            waits.append(timeout)
            if len(waits) == 1:
                raise subprocess.TimeoutExpired("synthetic", timeout)
            return -15

    killed = []
    monotonic_values = iter((0.0, 0.0, 0.0, 0.0, 0.0, 3601.0))
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: TimeoutProcess())
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: killed.append((pid, sig)))

    result = runner.execute_development_checkpoint()
    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    persisted = json.loads((artifact / "failure-receipt.json").read_text("ascii"))
    assert result == persisted
    assert result["state"] == "TIMEOUT"
    assert result["retry_permitted"] is False
    assert result["checkpoint_claimed"] is False
    assert result["confirmatory_execution"] is False
    assert result["closes_c17"] is False
    assert result["real_domain_test_accessed"] is False
    for field in (
        "confirmatory_execution",
        "closes_c17",
        "real_domain_test_accessed",
    ):
        hostile = dict(result)
        hostile[field] = True
        hostile.pop("record_sha256")
        hostile["record_sha256"] = hashlib.sha256(
            runner._canonical_json_bytes(hostile)
        ).hexdigest()
        with pytest.raises(runner.DevelopmentCheckpointRefusal, match="claims"):
            runner._validate_terminal_receipt(hostile)
    assert waits == [runner._PROCESS_MONITOR_INTERVAL_SECONDS, 10]
    assert killed == [(4343, runner.signal.SIGTERM)]
    consumption = runner._read_json(artifact / "execution-permit-consumption.json")
    assert consumption["state"] == "CONSUMED_LAUNCHED"
    assert consumption["outer_sampled_runner_process_id"] == 4343
    assert not (artifact / "execution-outcome-linkage.json").exists()


def test_interrupt_kills_the_live_process_group_and_preserves_terminal_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class InterruptedProcess:
        pid = 4444

        def wait(self, timeout: object = None) -> int:
            raise KeyboardInterrupt

    killed = []
    monkeypatch.setattr(
        runner.subprocess, "Popen", lambda *a, **k: InterruptedProcess()
    )
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: killed.append((pid, sig)))

    with pytest.raises(KeyboardInterrupt):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    failure = runner._read_json(artifact / "failure-receipt.json")
    assert failure["state"] in {"HOLD", "INTERRUPTED"}
    assert failure["retry_permitted"] is False
    assert killed and killed[0] == (4444, runner.signal.SIGTERM)
    consumption = runner._read_json(artifact / "execution-permit-consumption.json")
    assert consumption["state"] == "CONSUMED_LAUNCHED"
    assert consumption["outer_sampled_runner_process_id"] == 4444
    assert not (artifact / "execution-outcome-linkage.json").exists()


def test_interrupt_immediately_after_popen_cannot_escape_process_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class LaunchedProcess:
        pid = 4545

        def wait(self, timeout: object = None) -> int:
            return -15

    time_calls = {"count": 0}

    def interrupted_time_ns() -> int:
        time_calls["count"] += 1
        if time_calls["count"] == 3:
            raise KeyboardInterrupt
        return time_calls["count"]

    killed = []
    monkeypatch.setattr(runner.time, "time_ns", interrupted_time_ns)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: LaunchedProcess())
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: killed.append((pid, sig)))

    with pytest.raises(KeyboardInterrupt):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert killed == [(4545, runner.signal.SIGTERM)]
    assert not (artifact / "execution-permit-consumption.json").exists()
    assert not (artifact / "success-receipt.json").exists()
    failure = runner._read_json(artifact / "failure-receipt.json")
    assert failure["state"] == "INTERRUPTED"
    assert failure["retry_permitted"] is False


def test_popen_constructor_interruption_releases_gate_without_optimizer_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    marker = tmp_path / "optimizer-started"
    hidden_children = []
    original_popen = subprocess.Popen
    helper = (
        "import os,pathlib,sys\n"
        "fd=int(sys.argv[1])\n"
        "payload=bytearray()\n"
        "while True:\n"
        "    chunk=os.read(fd,4096)\n"
        "    if not chunk:\n"
        "        break\n"
        "    payload.extend(chunk)\n"
        "os.close(fd)\n"
        "if bytes(payload)==bytes.fromhex(sys.argv[3]):\n"
        "    pathlib.Path(sys.argv[2]).write_text('started')\n"
    )

    def interrupted_constructor(command: object, **kwargs: object) -> object:
        read_fd = int(tuple(kwargs["pass_fds"])[0])
        hidden_children.append(
            original_popen(
                (
                    sys.executable,
                    "-c",
                    helper,
                    str(read_fd),
                    str(marker),
                    runner._LAUNCH_GATE_TOKEN.hex(),
                ),
                pass_fds=(read_fd,),
            )
        )
        raise KeyboardInterrupt

    monkeypatch.setattr(runner.subprocess, "Popen", interrupted_constructor)

    with pytest.raises(KeyboardInterrupt):
        runner.execute_development_checkpoint()

    assert len(hidden_children) == 1
    assert hidden_children[0].wait(timeout=10) == 0
    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not marker.exists()
    assert not (artifact / "execution-permit-consumption.json").exists()
    assert not (artifact / "success-receipt.json").exists()
    failure = runner._read_json(artifact / "failure-receipt.json")
    assert failure["state"] == "INTERRUPTED"


def test_wrong_architecture_runtime_probe_cannot_reach_optimizer_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hostile_probe = _probe()
    hostile_probe["machine"] = "x86_64"
    hostile_probe["translated"] = True
    hostile_profile = dict(hostile_probe["profile"])
    hostile_profile["machine"] = "x86_64"
    hostile_probe["profile"] = hostile_profile
    _install_synthetic_preflight(monkeypatch, workspace, probe_override=hostile_probe)
    launched = []
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *a, **k: launched.append((a, k)) or _ZeroExitProcess(),
    )

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="runtime"):
        runner.execute_development_checkpoint()
    assert launched == []


def test_preexisting_forbidden_campaign_root_refuses_before_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    forbidden = workspace / runner.INNER_CAMPAIGN_RELATIVE_PATH
    forbidden.mkdir(parents=True)
    _install_synthetic_preflight(monkeypatch, workspace)
    launched = []
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *a, **k: launched.append((a, k)) or _ZeroExitProcess(),
    )

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="forbidden"):
        runner.execute_development_checkpoint()
    assert launched == []
    assert not (workspace / runner.ARTIFACT_RELATIVE_PATH).exists()


def test_post_publication_verifier_refusal_is_terminalized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace, verify_fails=True)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="hostile verifier"):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    failure = runner._read_json(artifact / "failure-receipt.json")
    assert failure["state"] == "REFUSED"
    assert failure["retry_permitted"] is False
    assert failure["checkpoint_claimed"] is False


def test_status_never_advertises_retry_or_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "_workspace_root", lambda: tmp_path)
    v1_custody = runner._read_json(_ROOT / runner.FREEZE_RELATIVE_PATH)[
        "v1_failure_custody"
    ]
    monkeypatch.setattr(
        runner, "_require_v1_failure_custody", lambda root: dict(v1_custody)
    )
    status = runner.development_checkpoint_status()
    assert status["state"] == "NOT_STARTED"
    assert status["retry_permitted"] is False
    assert status["replacement_permitted"] is False


def test_inner_verifier_and_outer_receipt_bind_inner_ledger_bytes() -> None:
    source = _SOURCE.read_text("utf-8")
    assert '"ledger_sha256"' in source


def test_inner_success_source_and_configuration_must_match_frozen_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hostile = _verified_inner()
    hostile["source_manifest_sha256"] = "8" * 64
    hostile["training_configuration_sha256"] = "9" * 64
    _install_synthetic_preflight(monkeypatch, workspace, verify_override=hostile)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())

    result = runner.execute_development_checkpoint()
    assert result["state"] == "REFUSED"
    assert result["checkpoint_claimed"] is False
    assert not (
        workspace / runner.ARTIFACT_RELATIVE_PATH / "success-receipt.json"
    ).exists()


def test_final_size_refusal_cannot_leave_a_success_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())

    def oversized_inventory(artifact_root: Path, **kwargs: object) -> tuple[dict, ...]:
        rows = []
        for relative in (
            runner.RETAINED_FREEZE_FILE_NAME,
            runner.RETAINED_RUNNER_TEST_FILE_NAME,
        ):
            payload = (artifact_root / relative).read_bytes()
            rows.append(
                {
                    "path": relative,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        rows.append(
            {
                "path": "synthetic-oversized-output",
                "bytes": runner.MAXIMUM_ARTIFACT_BYTES,
                "sha256": _ZERO_SHA256,
            }
        )
        return tuple(sorted(rows, key=lambda row: str(row["path"])))

    monkeypatch.setattr(runner, "_artifact_inventory", oversized_inventory)
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="exceeds 2 GiB"):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not (artifact / "success-receipt.json").exists()
    failure = runner._read_json(artifact / "failure-receipt.json")
    assert failure["checkpoint_claimed"] is False
    assert failure["retry_permitted"] is False


def test_status_rejects_a_tampered_success_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())
    runner.execute_development_checkpoint()
    receipt_path = workspace / runner.ARTIFACT_RELATIVE_PATH / "success-receipt.json"
    receipt = runner._read_json(receipt_path)
    receipt["scientific_result_eligible"] = True
    runner._atomic_write_json(receipt_path, receipt)

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="receipt"):
        runner.development_checkpoint_status()


@pytest.mark.parametrize("location", ("outer", "inner"))
def test_status_rejects_a_redigested_extra_claim_field(
    location: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())
    runner.execute_development_checkpoint()
    receipt_path = workspace / runner.ARTIFACT_RELATIVE_PATH / "success-receipt.json"
    receipt = runner._read_json(receipt_path)
    if location == "outer":
        receipt["manuscript_claim_ready"] = True
    else:
        receipt["inner_success"]["manuscript_claim_ready"] = True
    receipt.pop("receipt_sha256")
    receipt["receipt_sha256"] = hashlib.sha256(
        runner._canonical_json_bytes(receipt)
    ).hexdigest()
    runner._atomic_write_json(receipt_path, receipt)

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="fields|receipt"):
        runner.development_checkpoint_status()


def test_status_rejects_a_redigested_terminal_extra_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class FailedProcess:
        pid = 4646

        def wait(self, timeout: object = None) -> int:
            return 7

    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: FailedProcess())
    runner.execute_development_checkpoint()
    failure_path = workspace / runner.ARTIFACT_RELATIVE_PATH / "failure-receipt.json"
    failure = runner._read_json(failure_path)
    failure["manuscript_claim_ready"] = True
    failure.pop("record_sha256")
    failure["record_sha256"] = hashlib.sha256(
        runner._canonical_json_bytes(failure)
    ).hexdigest()
    runner._atomic_write_json(failure_path, failure)

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="fields|receipt"):
        runner.development_checkpoint_status()


def test_inner_summary_exposes_exact_launch_and_running_custody() -> None:
    source = _SOURCE.read_text("utf-8")
    for key in (
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "launch_authorization_sha256",
        "launch_receipt_sha256",
        "worker_session_sha256",
        "worker_process_identity_sha256",
    ):
        assert '"%s"' % key in source


def test_capsule_inputs_are_rehashed_after_child_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class MutatingProcess:
        pid = 4242

        def wait(self, timeout: object = None) -> int:
            marker = (
                workspace
                / runner.ARTIFACT_RELATIVE_PATH
                / runner.CAPSULE_DIRECTORY_NAME
                / "src/synthetic_marker.py"
            )
            marker.chmod(stat.S_IRUSR | stat.S_IWUSR)
            marker.write_bytes(b"SYNTHETIC = False\n")
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: MutatingProcess())
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="capsule source"):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not (artifact / "success-receipt.json").exists()
    assert (artifact / "failure-receipt.json").is_file()


def test_forbidden_main_campaign_appearing_during_child_is_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class LeakingProcess:
        pid = 4242

        def wait(self, timeout: object = None) -> int:
            (workspace / runner.INNER_CAMPAIGN_RELATIVE_PATH).mkdir(
                parents=True, exist_ok=True
            )
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: LeakingProcess())
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="forbidden"):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not (artifact / "success-receipt.json").exists()
    assert (artifact / "failure-receipt.json").is_file()


def test_forbidden_production_root_appearing_during_final_inventory_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())
    original_inventory = runner._artifact_inventory
    calls = []

    def leaking_inventory(*args: object, **kwargs: object) -> object:
        calls.append(True)
        (workspace / runner.PRODUCTION_ORDER_RELATIVE_PATH).mkdir(
            parents=True, exist_ok=True
        )
        return original_inventory(*args, **kwargs)

    monkeypatch.setattr(runner, "_artifact_inventory", leaking_inventory)
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="forbidden"):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert calls
    assert not (artifact / "success-receipt.json").exists()
    assert (artifact / "failure-receipt.json").is_file()


def test_preexisting_production_order_root_refuses_before_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    forbidden = workspace / "artifacts/a1_finite_association_production_order_v1"
    forbidden.mkdir(parents=True)
    _install_synthetic_preflight(monkeypatch, workspace)
    launched = []
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *a, **k: launched.append((a, k)) or _ZeroExitProcess(),
    )

    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="forbidden"):
        runner.execute_development_checkpoint()
    assert launched == []
    assert not (workspace / runner.ARTIFACT_RELATIVE_PATH).exists()


@pytest.mark.parametrize(
    "shadow_name",
    ("sitecustomize.pyc", "json.py", "sitecustomize.so"),
)
def test_capsule_root_shadow_importable_refuses_success(
    shadow_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    json_calls = []
    _install_synthetic_preflight(monkeypatch, workspace, json_calls=json_calls)
    copy_capsule = runner._copy_capsule

    def injecting_copy(root: Path, capsule: Path) -> Dict[str, object]:
        manifest = copy_capsule(root, capsule)
        injected = capsule / shadow_name
        injected.write_bytes(b"HOSTILE\x00SHADOW\n")
        injected.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        return manifest

    monkeypatch.setattr(runner, "_copy_capsule", injecting_copy)
    launched = []
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *a, **k: launched.append((a, k)) or _ZeroExitProcess(),
    )

    with pytest.raises(
        runner.DevelopmentCheckpointRefusal,
        match="shadow|importable|root|source|inventory|outside",
    ):
        runner.execute_development_checkpoint()
    for arguments, keywords in json_calls:
        assert tuple(arguments[0])[1] == "-P"
        assert keywords["environment"]["PYTHONSAFEPATH"] == "1"
    for arguments, keywords in launched:
        assert tuple(arguments[0])[1] == "-P"
        assert keywords["env"]["PYTHONSAFEPATH"] == "1"
    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not (artifact / "success-receipt.json").exists()


@pytest.mark.parametrize(
    "injected_name",
    ("sitecustomize.py", "sitecustomize.pyc", "sitecustomize.so"),
)
def test_capsule_manifest_rejects_an_extra_source_file(
    injected_name: str, tmp_path: Path
) -> None:
    capsule = tmp_path / "capsule"
    expected = capsule / "src/expected.py"
    expected.parent.mkdir(parents=True)
    payload = b"EXPECTED = True\n"
    expected.write_bytes(payload)
    expected.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    manifest: Dict[str, object] = {
        "schema": "heterodiff-a1-development-source-capsule-manifest-v2",
        "lane_id": runner.LANE_ID,
        "file_count": 1,
        "files": [
            {
                "path": "src/expected.py",
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        ],
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        runner._canonical_json_bytes(manifest)
    ).hexdigest()
    injected = capsule / "src" / injected_name
    injected.write_bytes(b"UNBOUND\x00SOURCE\n")
    injected.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    with pytest.raises(
        runner.DevelopmentCheckpointRefusal, match="extra|closure|unbound"
    ):
        runner._verify_capsule_source_manifest(capsule, manifest)


def test_manifest_and_runtime_probe_reject_redigested_extra_fields(
    tmp_path: Path,
) -> None:
    capsule = tmp_path / "capsule"
    capsule.mkdir()
    manifest: Dict[str, object] = {
        "schema": "heterodiff-a1-development-source-capsule-manifest-v2",
        "lane_id": runner.LANE_ID,
        "file_count": 0,
        "files": [],
        "production_authority": True,
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        runner._canonical_json_bytes(manifest)
    ).hexdigest()
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="shape|fields"):
        runner._verify_capsule_source_manifest(capsule, manifest)

    for location in ("outer", "preflight"):
        probe = _probe()
        if location == "outer":
            probe["formal_production_runtime_approval"] = True
        else:
            probe["preflight"]["formal_production_runtime_approval"] = True
        with pytest.raises(
            runner.DevelopmentCheckpointRefusal, match="fields|preflight"
        ):
            runner._validate_runtime_probe(
                probe,
                binding={
                    "source_manifest_sha256": _ZERO_SHA256,
                    "training_configuration_sha256": _ZERO_SHA256,
                },
            )


@pytest.mark.parametrize(
    "relative_path",
    (
        "capsule-source-manifest.json",
        "runtime-preflight.json",
        "execution-permit.json",
        "attempt.json",
    ),
)
def test_saved_prelaunch_custody_is_reopened_after_child(
    relative_path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class TamperingProcess:
        pid = 4242

        def wait(self, timeout: object = None) -> int:
            path = workspace / runner.ARTIFACT_RELATIVE_PATH / relative_path
            runner._atomic_write_json(path, {"tampered": True})
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: TamperingProcess())
    with pytest.raises(
        runner.DevelopmentCheckpointRefusal, match="manifest|preflight|permit|attempt"
    ):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not (artifact / "success-receipt.json").exists()
    assert (artifact / "failure-receipt.json").is_file()


@pytest.mark.parametrize(
    "file_name",
    (runner.RETAINED_FREEZE_FILE_NAME, runner.RETAINED_RUNNER_TEST_FILE_NAME),
)
def test_retained_authorization_is_reopened_before_success(
    file_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class TamperingProcess:
        pid = 4242

        def wait(self, timeout: object = None) -> int:
            path = workspace / runner.ARTIFACT_RELATIVE_PATH / file_name
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            path.write_bytes(b"TAMPERED AUTHORIZATION\n")
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: TamperingProcess())
    with pytest.raises(
        runner.DevelopmentCheckpointRefusal, match="retained|authorization|evidence"
    ):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert not (artifact / "success-receipt.json").exists()
    assert (artifact / "failure-receipt.json").is_file()


@pytest.mark.parametrize(
    "file_name",
    (runner.RETAINED_FREEZE_FILE_NAME, runner.RETAINED_RUNNER_TEST_FILE_NAME),
)
def test_status_reopens_retained_authorization_evidence(
    file_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())
    runner.execute_development_checkpoint()
    retained = workspace / runner.ARTIFACT_RELATIVE_PATH / file_name
    retained.chmod(stat.S_IRUSR | stat.S_IWUSR)
    retained.write_bytes(b"TAMPERED AUTHORIZATION\n")

    with pytest.raises(
        runner.DevelopmentCheckpointRefusal, match="retained|authorization|evidence"
    ):
        runner.development_checkpoint_status()


def test_status_reconciles_a_fresh_inner_verifier_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())
    runner.execute_development_checkpoint()
    calls = []

    def hostile_fresh_summary(*args: object, **kwargs: object) -> Dict[str, object]:
        calls.append((args, kwargs))
        fresh = _verified_inner()
        fresh["checkpoint_sha256"] = "9" * 64
        return fresh

    monkeypatch.setattr(runner, "_run_json_subprocess", hostile_fresh_summary)
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="inner|receipt"):
        runner.development_checkpoint_status()
    assert len(calls) == 1


def test_success_publication_reopens_every_bound_artifact_before_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: _ZeroExitProcess())
    original_atomic_write_json = runner._atomic_write_json

    def tamper_after_success_publication(path: Path, value: object) -> None:
        original_atomic_write_json(path, value)
        if path.name == "success-receipt.json":
            original_atomic_write_json(
                path.parent / "execution-permit-consumption.json",
                {"tampered": True},
            )

    monkeypatch.setattr(runner, "_atomic_write_json", tamper_after_success_publication)

    with pytest.raises(
        runner.DevelopmentCheckpointRefusal,
        match="consumption|durable|evidence|fields",
    ):
        runner.execute_development_checkpoint()

    artifact = workspace / runner.ARTIFACT_RELATIVE_PATH
    assert (artifact / "success-receipt.json").is_file()
    assert (artifact / "failure-receipt.json").is_file()
    status = runner.development_checkpoint_status()
    assert status["state"] == "INCOMPLETE_OR_CONFLICTING_ATTEMPT"
    assert status["retry_permitted"] is False
    assert status["replacement_permitted"] is False


def test_failure_receipt_reports_production_order_boundary_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _install_synthetic_preflight(monkeypatch, workspace)

    class FailingLeakingProcess:
        pid = 4848

        def wait(self, timeout: object = None) -> int:
            (workspace / "artifacts/a1_finite_association_production_order_v1").mkdir(
                parents=True, exist_ok=True
            )
            return 7

    monkeypatch.setattr(
        runner.subprocess, "Popen", lambda *a, **k: FailingLeakingProcess()
    )
    with pytest.raises(runner.DevelopmentCheckpointRefusal, match="forbidden"):
        runner.execute_development_checkpoint()
    persisted = runner._read_json(
        workspace / runner.ARTIFACT_RELATIVE_PATH / "failure-receipt.json"
    )
    assert persisted["state"] == "REFUSED"
    assert persisted["checkpoint_claimed"] is False
    assert persisted["boundary_drift"]["production_order_root_present"] is True
