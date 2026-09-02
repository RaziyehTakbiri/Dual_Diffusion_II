from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import base64
import dataclasses
import hashlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = (
    ROOT
    / "research/diagnostics/"
    "manuscript_v3_solo_block2_runtime_custody_closure_v5_hash_first.py"
)
LIVE_ROOT = (
    ROOT
    / "research/custody/solo_block2_public_documentation_runtime_v4"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def wrapper():
    return _load(WRAPPER, "_v5_hash_first_wrapper")


def _copy_validators(wrapper, target: Path) -> None:
    for relative, _size, _digest in wrapper.VALIDATOR_PINS:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
        destination.chmod(0o644)


def test_hash_first_wrapper_passes_and_has_zero_live_effect(wrapper, monkeypatch):
    before = (LIVE_ROOT.stat().st_ino, tuple(LIVE_ROOT.iterdir()))
    monkeypatch.chdir("/private/tmp")
    result = wrapper.validate(ROOT)
    assert result["status"] == result["wrapped_v5_status"] == "PASS"
    assert result["validator_count"] == 3
    assert result["compiled_from_captured_bytes_only"] is True
    assert result["inherited_disk_loaders_replaced"] is True
    assert result["validator_identities_stable"] is True
    assert result["network_actions"] == result["operational_receipts"] == 0
    assert result["activated_budget"] == 0
    assert before == (LIVE_ROOT.stat().st_ino, tuple(LIVE_ROOT.iterdir()))


@pytest.mark.parametrize("ordinal", [0, 1, 2])
def test_hostile_validator_drift_is_rejected_before_any_compile(
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
        wrapper.HashFirstValidationError,
        match="validator pin mismatch before execution",
    ):
        wrapper._capture_all(tmp_path)
    assert not marker.exists()


def test_captured_bytes_defeat_post_capture_path_substitution(wrapper, tmp_path):
    _copy_validators(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    marker = tmp_path / "post-capture-executed"
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    (tmp_path / wrapper.V3_VALIDATOR).write_bytes(hostile)
    (tmp_path / wrapper.V3_VALIDATOR).chmod(0o644)
    v5 = wrapper._compile_chain(tmp_path, captured)
    v4 = v5["_load_v4_validator"](tmp_path)
    v3 = v4["_load_v3_validator"](tmp_path)
    assert callable(v5["validate"])
    assert callable(v4["validate"])
    assert callable(v3["validate"])
    assert not marker.exists()


def test_forged_captured_mapping_is_rejected_before_compile(wrapper, tmp_path):
    _copy_validators(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    marker = tmp_path / "forged-capture-executed"
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    original = captured[wrapper.V3_VALIDATOR]
    captured[wrapper.V3_VALIDATOR] = dataclasses.replace(
        original,
        raw=hostile,
        size=len(hostile),
        sha256=hashlib.sha256(hostile).hexdigest(),
    )
    with pytest.raises(
        wrapper.HashFirstValidationError,
        match="captured validator pin mismatch",
    ):
        wrapper._compile_chain(tmp_path, captured)
    assert not marker.exists()


def test_self_restoring_false_pass_payload_never_executes(wrapper, tmp_path):
    _copy_validators(wrapper, tmp_path)
    relative = wrapper.V4_VALIDATOR
    path = tmp_path / relative
    canonical = path.read_bytes()
    marker = tmp_path / "self-restoring-payload-executed"
    hostile = (
        "from pathlib import Path\n"
        "import base64\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
        f"Path({str(path)!r}).write_bytes(base64.b64decode({base64.b64encode(canonical)!r}))\n"
        "def validate(_root): return {'status': 'PASS'}\n"
    ).encode()
    path.write_bytes(hostile)
    path.chmod(0o644)
    with pytest.raises(
        wrapper.HashFirstValidationError,
        match="validator pin mismatch before execution",
    ):
        wrapper._capture_all(tmp_path)
    assert not marker.exists()
    assert path.read_bytes() == hostile


@pytest.mark.parametrize("custody", ["mode", "nlink"])
def test_unsafe_validator_custody_is_rejected(wrapper, tmp_path, custody):
    _copy_validators(wrapper, tmp_path)
    relative = wrapper.VALIDATOR_PINS[0][0]
    path = tmp_path / relative
    if custody == "mode":
        path.chmod(0o600)
    else:
        os.link(path, tmp_path / "hardlink-to-v5-validator")
    with pytest.raises(
        wrapper.HashFirstValidationError, match="unsafe validator custody"
    ):
        wrapper._capture_all(tmp_path)


def test_pin_roster_is_exact_and_unique(wrapper):
    expected = {
        wrapper.V5_VALIDATOR: (
            23_872,
            "4699e3073ec19b3f82320b70f29d4b9a63169622a9ed042a30262c3fe7d01c96",
        ),
        wrapper.V4_VALIDATOR: (
            20_334,
            "bc32e4775a6ea1ac557bafc66a27411f5cddfeb79e4daa0bd4dfc09e89af7a44",
        ),
        wrapper.V3_VALIDATOR: (
            36_357,
            "53fb7a3afb8f0cf798e9d0cd0970fe370f5e2c0a7ed72bef0ce5c9f414de1153",
        ),
    }
    assert len(wrapper.VALIDATOR_PINS) == len(expected)
    assert {
        relative: (size, digest)
        for relative, size, digest in wrapper.VALIDATOR_PINS
    } == expected
