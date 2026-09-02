from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = (
    ROOT
    / "research/diagnostics/finite_association_r1_v4_terminal_pass_hash_first_v1.py"
)
CURRENT_HOLD_PATHS = [
    (
        "research/production/__pycache__/"
        "finite_association_r1_activation_preparation_rehearsal_authority_v3."
        "cpython-39.pyc"
    ),
    (
        "research/production/__pycache__/"
        "finite_association_r1_activation_preparation_rehearsal_contracts_v3."
        "cpython-39.pyc"
    ),
    (
        "research/production/__pycache__/"
        "finite_association_r1_activation_preparation_rehearsal_runtime_v3."
        "cpython-39.pyc"
    ),
    (
        "tests/unit/__pycache__/"
        "test_manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
        "environment_rehearsal_freeze_v1.cpython-39-pytest-7.1.2.pyc"
    ),
]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def wrapper():
    return _load(WRAPPER, "_finite_association_r1_v4_hash_first_wrapper")


def _copy_validators(wrapper, target: Path) -> None:
    for relative, _size, _digest in wrapper.VALIDATOR_PINS:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
        destination.chmod(0o644)


def test_wrapper_reports_current_state_without_operational_effect(wrapper, monkeypatch):
    monkeypatch.chdir("/private/tmp")
    result = wrapper.validate(ROOT)
    assert result["status"] == "HOLD"
    assert result["chain_integrity_state"] == wrapper.CHAIN_INTEGRITY_STATE
    assert result["compiled_from_captured_bytes_only"] is True
    assert result["inherited_pathname_loaders_replaced"] is True
    assert result["validator_identities_stable"] is True
    assert result["validator_count"] == 3
    assert (
        result["network_actions"],
        result["subprocess_actions"],
        result["filesystem_writes"],
        result["operational_receipts"],
        result["scientific_executions"],
        result["tracker_files_edited"],
    ) == (0, 0, 0, 0, 0, 0)
    assert result["state"] == wrapper.CURRENT_CUSTODY_HOLD_STATE
    assert result["current_v3_custody_pass"] is False
    assert result["current_custody_hold_reason"] == (
        wrapper.CURRENT_CUSTODY_HOLD_REASON
    )
    assert result["current_custody_hold_paths"] == CURRENT_HOLD_PATHS
    assert result["current_custody_hold_roster_sha256"] == (
        "e2266e13638e78a326bd74c0e1376b47f1699c6bef892024959d6f3ce322dbdc"
    )
    assert result["historical_registration_revalidated"] is False
    assert result["historical_pass_status"] is None
    assert result["current_custody_sha256"] is None


def test_cli_exit_is_fail_closed_for_current_hold(wrapper, capsys):
    exit_code = wrapper.main(["--root", str(ROOT)])
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["status"] == "HOLD"
    assert parsed["current_custody_hold_paths"] == CURRENT_HOLD_PATHS
    assert exit_code == 2


@pytest.mark.parametrize("ordinal", [0, 1, 2])
def test_hostile_validator_drift_refuses_before_any_compile(
    wrapper, tmp_path, ordinal
):
    _copy_validators(wrapper, tmp_path)
    marker = tmp_path / f"executed-{ordinal}"
    relative = wrapper.VALIDATOR_PINS[ordinal][0]
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    (tmp_path / relative).write_bytes(hostile)
    (tmp_path / relative).chmod(0o644)
    with pytest.raises(
        wrapper.HashFirstR1ValidationError,
        match="validator pin mismatch before execution",
    ):
        wrapper._capture_all(tmp_path)
    assert not marker.exists()


def test_post_capture_substitution_cannot_change_compiled_chain(wrapper, tmp_path):
    _copy_validators(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    marker = tmp_path / "post-capture-executed"
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    (tmp_path / wrapper.V3_VALIDATOR).write_bytes(hostile)
    (tmp_path / wrapper.V3_VALIDATOR).chmod(0o644)
    v4, v3, v2 = wrapper._compile_chain(tmp_path, captured)
    assert v4.SCHEMA.startswith("heterodiff-manuscript-v3-a1-r1-")
    assert v3.SCHEMA.startswith("heterodiff-manuscript-v3-a1-r1-")
    assert v2.SCHEMA.startswith("heterodiff-manuscript-v3-a1-r1-")
    assert not marker.exists()


def test_forged_captured_mapping_refuses_before_compile(wrapper, tmp_path):
    _copy_validators(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    marker = tmp_path / "forged-capture-executed"
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    original = captured[wrapper.V2_VALIDATOR]
    captured[wrapper.V2_VALIDATOR] = dataclasses.replace(
        original,
        raw=hostile,
        size=len(hostile),
        sha256=hashlib.sha256(hostile).hexdigest(),
    )
    with pytest.raises(
        wrapper.HashFirstR1ValidationError,
        match="captured validator pin mismatch",
    ):
        wrapper._compile_chain(tmp_path, captured)
    assert not marker.exists()


@pytest.mark.parametrize("custody", ["mode", "nlink"])
def test_unsafe_validator_custody_refuses(wrapper, tmp_path, custody):
    _copy_validators(wrapper, tmp_path)
    path = tmp_path / wrapper.V4_VALIDATOR
    if custody == "mode":
        path.chmod(0o600)
    else:
        os.link(path, tmp_path / "hardlink-to-v4-validator")
    with pytest.raises(
        wrapper.HashFirstR1ValidationError, match="unsafe validator custody"
    ):
        wrapper._capture_all(tmp_path)


@pytest.mark.parametrize("substitution", ["leaf", "ancestor"])
def test_symlink_substitution_refuses(wrapper, tmp_path, substitution):
    _copy_validators(wrapper, tmp_path)
    if substitution == "leaf":
        path = tmp_path / wrapper.V4_VALIDATOR
        path.unlink()
        path.symlink_to(ROOT / wrapper.V4_VALIDATOR)
    else:
        directory = tmp_path / "research/diagnostics"
        real_directory = tmp_path / "research/real-diagnostics"
        directory.rename(real_directory)
        directory.symlink_to(real_directory, target_is_directory=True)
    with pytest.raises(OSError):
        wrapper._capture_all(tmp_path)


def test_inherited_loaders_return_only_captured_modules_and_bind_root(
    wrapper, tmp_path
):
    _copy_validators(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    v4, v3, v2 = wrapper._compile_chain(tmp_path, captured)
    assert v4._load_exact_v3_validator(tmp_path) is v3
    assert v3._load_exact_v2_postmortem(tmp_path) is v2
    with pytest.raises(
        wrapper.HashFirstR1ValidationError,
        match="inherited validator requested a different root",
    ):
        v4._load_exact_v3_validator(tmp_path / "other")
    with pytest.raises(
        wrapper.HashFirstR1ValidationError,
        match="inherited validator requested a different root",
    ):
        v3._load_exact_v2_postmortem(tmp_path / "other")


def test_module_registry_restored_on_success_and_compile_exception(wrapper, tmp_path):
    _copy_validators(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    sentinel = object()
    before = {}
    for name in wrapper._MODULE_NAMES:
        before[name] = sys.modules.get(name, sentinel)
    wrapper._compile_chain(tmp_path, captured)
    for name in wrapper._MODULE_NAMES:
        assert sys.modules.get(name, sentinel) is before[name]

    bound = captured[wrapper.V2_VALIDATOR]
    broken = dataclasses.replace(bound, raw=b"def broken(:\n")
    with pytest.raises(SyntaxError):
        wrapper._exec_captured_module(broken, tmp_path, wrapper._MODULE_NAMES[0])
    assert sys.modules.get(wrapper._MODULE_NAMES[0], sentinel) is before[
        wrapper._MODULE_NAMES[0]
    ]


def test_explicit_none_module_registry_entries_restore_on_success_and_exception(
    wrapper, tmp_path
):
    _copy_validators(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    sentinel = object()
    before = {name: sys.modules.get(name, sentinel) for name in wrapper._MODULE_NAMES}
    try:
        for name in wrapper._MODULE_NAMES:
            sys.modules[name] = None
        wrapper._compile_chain(tmp_path, captured)
        assert all(sys.modules.get(name, sentinel) is None for name in wrapper._MODULE_NAMES)

        bound = captured[wrapper.V2_VALIDATOR]
        broken = dataclasses.replace(bound, raw=b"def broken(:\n")
        with pytest.raises(SyntaxError):
            wrapper._exec_captured_module(
                broken, tmp_path, wrapper._MODULE_NAMES[0]
            )
        assert sys.modules.get(wrapper._MODULE_NAMES[0], sentinel) is None
    finally:
        for name, value in before.items():
            if value is sentinel:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


def test_pin_roster_is_exact_and_unique(wrapper):
    expected = {
        wrapper.V4_VALIDATOR: (
            69_164,
            "573ac885e449a0203d4c0b78dfa833fb4269c1fc94aeb2289c9dd8e507460fb0",
        ),
        wrapper.V3_VALIDATOR: (
            44_262,
            "2ae995d7609778f9201e3a90a2861c74898dfdc357b3f0b6f75b46bc68ce78bd",
        ),
        wrapper.V2_VALIDATOR: (
            62_047,
            "ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671",
        ),
    }
    assert len(wrapper.VALIDATOR_PINS) == len(expected)
    assert {
        relative: (size, digest)
        for relative, size, digest in wrapper.VALIDATOR_PINS
    } == expected
