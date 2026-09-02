from __future__ import annotations

import base64
import dataclasses
import hashlib
import importlib.util
import os
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = (
    ROOT
    / "research/diagnostics/"
    "formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py"
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
    return _load(WRAPPER, "_two_macrostep_parent_custody_wrapper")


def _copy_sources(wrapper, target: Path) -> None:
    for relative, _size, _digest in wrapper.SOURCE_PINS:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
        destination.chmod(0o644)


def test_parent_custody_wrapper_passes_exact_frozen_qualification(
    wrapper, monkeypatch
):
    module_names = (
        "_two_macrostep_bound_single",
        "_two_macrostep_bound_test29",
        "_two_macrostep_bound_test30",
        "_two_macrostep_bound_candidate",
    )
    module_registry_before = {
        name: (name in sys.modules, sys.modules.get(name)) for name in module_names
    }
    monkeypatch.chdir("/private/tmp")
    result = wrapper.validate(ROOT)
    assert result["status"] == "PASS"
    assert result["ordered_word_pair_cases_checked"] == 1024
    assert result["report_sha256"] == wrapper.EXPECTED_REPORT_SHA256
    assert result["candidate_report_parent_custody_authenticated"] is False
    assert result["envelope_parent_source_custody_authenticated"] is True
    assert result["compiled_from_captured_bytes_only"] is True
    assert result["source_identities_stable"] is True
    assert result["source_count"] == 4
    assert (
        result["formal_tests_closed"],
        result["fields_closed"],
        result["blockers_closed"],
        result["result_slots_filled"],
        result["tracker_files_edited"],
    ) == (0, 0, 0, 0, 0)
    assert {
        name: (name in sys.modules, sys.modules.get(name)) for name in module_names
    } == module_registry_before


@pytest.mark.parametrize("ordinal", [0, 1, 2, 3])
def test_hostile_source_drift_is_rejected_before_any_compile(
    wrapper, tmp_path, ordinal
):
    _copy_sources(wrapper, tmp_path)
    marker = tmp_path / f"executed-{ordinal}"
    relative = wrapper.SOURCE_PINS[ordinal][0]
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    (tmp_path / relative).write_bytes(hostile)
    (tmp_path / relative).chmod(0o644)
    with pytest.raises(
        wrapper.ParentCustodyError,
        match="source pin mismatch before execution",
    ):
        wrapper._capture_all(tmp_path)
    assert not marker.exists()


def test_post_capture_substitution_cannot_change_compiled_modules(
    wrapper, tmp_path
):
    _copy_sources(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    marker = tmp_path / "post-capture-executed"
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    (tmp_path / wrapper.SINGLE_PARENT).write_bytes(hostile)
    (tmp_path / wrapper.SINGLE_PARENT).chmod(0o644)
    candidate, single, test29, test30 = wrapper._compile_modules(
        tmp_path, captured
    )
    assert candidate.SCHEMA_VERSION == (
        "heterodiff-test29-test30-two-macrostep-path-v1"
    )
    assert single.SCHEMA_VERSION == (
        "heterodiff-test29-test30-single-macrostep-integration-v1"
    )
    assert test29.FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION == (
        "formal-test29-finite-acyclic-route-oracle-v1"
    )
    assert test30.SCHEMA_VERSION == (
        "heterodiff-formal-test30-synthetic-coupled-path-v1"
    )
    assert not marker.exists()


def test_forged_captured_mapping_is_rejected_before_compile(wrapper, tmp_path):
    _copy_sources(wrapper, tmp_path)
    captured = wrapper._capture_all(tmp_path)
    marker = tmp_path / "forged-capture-executed"
    hostile = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
    ).encode()
    original = captured[wrapper.TEST29_PARENT]
    captured[wrapper.TEST29_PARENT] = dataclasses.replace(
        original,
        raw=hostile,
        size=len(hostile),
        sha256=hashlib.sha256(hostile).hexdigest(),
    )
    with pytest.raises(
        wrapper.ParentCustodyError, match="captured source pin mismatch"
    ):
        wrapper._compile_modules(tmp_path, captured)
    assert not marker.exists()


def test_self_restoring_schema_compatible_parent_never_executes(
    wrapper, tmp_path
):
    _copy_sources(wrapper, tmp_path)
    relative = wrapper.SINGLE_PARENT
    path = tmp_path / relative
    canonical = path.read_bytes()
    marker = tmp_path / "self-restoring-parent-executed"
    hostile = (
        "from pathlib import Path\n"
        "from types import ModuleType\n"
        "import base64\n"
        f"Path({str(marker)!r}).write_bytes(b'executed')\n"
        f"Path({str(path)!r}).write_bytes(base64.b64decode({base64.b64encode(canonical)!r}))\n"
        "SCHEMA_VERSION='heterodiff-test29-test30-single-macrostep-integration-v1'\n"
        "_addressed_increment=lambda *a,**k: None\n"
        "_validate_increment_roster=lambda *a,**k: None\n"
        "_validate_central_word=lambda *a,**k: None\n"
        "_strict_compare_dataclass_fields=lambda *a,**k: None\n"
    ).encode()
    path.write_bytes(hostile)
    path.chmod(0o644)
    with pytest.raises(
        wrapper.ParentCustodyError,
        match="source pin mismatch before execution",
    ):
        wrapper._capture_all(tmp_path)
    assert not marker.exists()
    assert path.read_bytes() == hostile


@pytest.mark.parametrize("custody", ["mode", "nlink"])
def test_unsafe_source_custody_is_rejected(wrapper, tmp_path, custody):
    _copy_sources(wrapper, tmp_path)
    relative = wrapper.CANDIDATE
    path = tmp_path / relative
    if custody == "mode":
        path.chmod(0o600)
    else:
        os.link(path, tmp_path / "hardlink-to-candidate")
    with pytest.raises(
        wrapper.ParentCustodyError, match="unsafe source custody"
    ):
        wrapper._capture_all(tmp_path)


def test_pin_roster_matches_independent_review(wrapper):
    expected = {
        wrapper.CANDIDATE: (
            59_285,
            "d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176",
        ),
        wrapper.SINGLE_PARENT: (
            61_434,
            "e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7",
        ),
        wrapper.TEST29_PARENT: (
            52_186,
            "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089",
        ),
        wrapper.TEST30_PARENT: (
            42_349,
            "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0",
        ),
    }
    assert {
        relative: (size, digest)
        for relative, size, digest in wrapper.SOURCE_PINS
    } == expected
