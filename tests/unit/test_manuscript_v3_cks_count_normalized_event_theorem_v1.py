from __future__ import annotations

from fractions import Fraction
from itertools import product
import json
import os
from pathlib import Path
import shutil
import stat
import types
from typing import Any, Dict

import pytest


WORKSPACE = Path(__file__).resolve().parents[2]
SOURCE = (
    WORKSPACE
    / "research/diagnostics/manuscript_v3_cks_count_normalized_event_theorem_v1.py"
)


def _load_validator() -> types.ModuleType:
    module = types.ModuleType("cks_count_normalized_event_theorem_validator")
    module.__file__ = str(SOURCE)
    code = compile(SOURCE.read_bytes(), str(SOURCE), "exec")
    exec(code, module.__dict__)
    return module


@pytest.fixture(scope="module")
def validator() -> types.ModuleType:
    return _load_validator()


def test_empty_configuration_is_totalized(validator: types.ModuleType) -> None:
    result = validator.finite_categorical_separation([], [], cap=4)
    assert result == {
        "schema_version": "heterodiff-cks-finite-categorical-separation-v1",
        "left_count": 0,
        "right_count": 0,
        "count_term": {"numerator": 0, "denominator": 1},
        "event_term": {"numerator": 0, "denominator": 1},
        "distance_squared": {"numerator": 0, "denominator": 1},
        "same_counting_measure": True,
        "separated": False,
        "scientific_result": False,
    }


def test_empty_and_nonempty_are_separated_by_count(
    validator: types.ModuleType,
) -> None:
    result = validator.finite_categorical_separation([], ["a"], cap=4)
    assert result["count_term"] == {"numerator": 1, "denominator": 1}
    assert result["event_term"] == {"numerator": 1, "denominator": 1}
    assert result["distance_squared"] == {"numerator": 2, "denominator": 1}
    assert result["separated"] is True


def test_unequal_mass_with_same_normalized_measure_uses_count_channel(
    validator: types.ModuleType,
) -> None:
    result = validator.finite_categorical_separation(["a"], ["a", "a"], cap=4)
    assert result["count_term"] == {"numerator": 1, "denominator": 1}
    assert result["event_term"] == {"numerator": 0, "denominator": 1}
    assert result["separated"] is True


def test_equal_count_duplicate_multiplicities_use_event_channel(
    validator: types.ModuleType,
) -> None:
    result = validator.finite_categorical_separation(
        ["a", "a", "b"], ["a", "b", "b"], cap=4
    )
    assert result["count_term"] == {"numerator": 0, "denominator": 1}
    assert result["event_term"] == {"numerator": 2, "denominator": 9}
    assert result["distance_squared"] == {"numerator": 2, "denominator": 9}
    assert result["separated"] is True


def test_proportional_duplicates_still_use_count_channel(
    validator: types.ModuleType,
) -> None:
    result = validator.finite_categorical_separation(
        ["a", "b"], ["a", "a", "b", "b"], cap=4
    )
    assert result["count_term"] == {"numerator": 4, "denominator": 1}
    assert result["event_term"] == {"numerator": 0, "denominator": 1}
    assert result["separated"] is True


def test_permutation_invariance_and_input_preservation(
    validator: types.ModuleType,
) -> None:
    left = ["c", "a", "a", "b"]
    before = list(left)
    result = validator.finite_categorical_separation(
        left, ["a", "b", "a", "c"], cap=4
    )
    assert result["distance_squared"] == {"numerator": 0, "denominator": 1}
    assert result["same_counting_measure"] is True
    assert left == before


def test_positive_exact_scales(validator: types.ModuleType) -> None:
    result = validator.finite_categorical_separation(
        ["a", "a", "b"],
        ["a", "b", "b"],
        cap=4,
        count_scale_squared=Fraction(7, 3),
        event_scale_squared=Fraction(5, 2),
    )
    assert result["count_term"] == {"numerator": 0, "denominator": 1}
    assert result["event_term"] == {"numerator": 5, "denominator": 9}


def test_exhaustive_small_alphabet_injectivity(validator: types.ModuleType) -> None:
    configurations = [[]]
    for size in range(1, 5):
        configurations.extend([list(items) for items in product(("a", "b"), repeat=size)])
    for left in configurations:
        for right in configurations:
            result = validator.finite_categorical_separation(left, right, cap=4)
            same = sorted(left) == sorted(right)
            assert result["same_counting_measure"] is same
            assert (result["distance_squared"]["numerator"] == 0) is same
            assert result["separated"] is (not same)


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"left": (), "right": [], "cap": 2}, "list"),
        ({"left": [], "right": (), "cap": 2}, "list"),
        ({"left": [1], "right": [], "cap": 2}, "token"),
        ({"left": [""], "right": [], "cap": 2}, "token"),
        ({"left": ["\n"], "right": [], "cap": 2}, "printable"),
        ({"left": ["é"], "right": [], "cap": 2}, "ASCII"),
        ({"left": ["a" * 129], "right": [], "cap": 2}, "length"),
        ({"left": ["a", "b", "c"], "right": [], "cap": 2}, "cap"),
        ({"left": [], "right": [], "cap": True}, "cap"),
        ({"left": [], "right": [], "cap": 0}, "cap"),
        (
            {
                "left": [],
                "right": [],
                "cap": 2,
                "count_scale_squared": 0,
            },
            "strictly positive",
        ),
        (
            {
                "left": [],
                "right": [],
                "cap": 2,
                "event_scale_squared": Fraction(-1, 2),
            },
            "strictly positive",
        ),
        (
            {
                "left": [],
                "right": [],
                "cap": 2,
                "count_scale_squared": 0.5,
            },
            "exact",
        ),
        (
            {
                "left": [],
                "right": [],
                "cap": 2,
                "event_scale_squared": True,
            },
            "exact",
        ),
    ],
)
def test_oracle_refusals(
    validator: types.ModuleType, kwargs: Dict[str, Any], match: str
) -> None:
    with pytest.raises(validator.ValidationError, match=match):
        validator.finite_categorical_separation(**kwargs)


def test_exact_component_bound_refusal(validator: types.ModuleType) -> None:
    with pytest.raises(validator.ValidationError, match="component bound"):
        validator.finite_categorical_separation(
            [], [], cap=2, count_scale_squared=1 << 4096
        )


def test_live_validation_and_exact_nonclosure(validator: types.ModuleType) -> None:
    status = validator.validate(WORKSPACE)
    assert status == {
        "validation": "PASS",
        "state": "GENERIC_CKS_THEOREM_PROVED_EXACT_DOMAIN_INSTANCE_PENDING",
        "control_predicate": (
            "GATE_A_CKS_COUNT_NORMALIZED_EVENT_ROUTE_MATHEMATICALLY_VIABLE"
        ),
        "control_predicate_value": True,
        "gate_a_exact_metric_checkbox_closed": False,
        "scientific_fields_closed": 0,
        "blockers_closed": 0,
        "effective_unresolved_fields": 172,
        "tracker_edit_performed": False,
        "network_data_entropy_runtime_or_science_performed": False,
    }


def _copy_roster(validator: types.ModuleType, tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    paths = [path for _, path, _, _ in validator.EXPECTED_PREDECESSORS]
    paths.extend(
        [
            validator.HUMAN_PATH,
            validator.MACHINE_PATH,
            validator.VALIDATOR_PATH,
            validator.TEST_PATH,
        ]
    )
    for relative in paths:
        source = WORKSPACE / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=False)
        os.chmod(target, 0o644)
    return root


def _rewrite_machine(validator: types.ModuleType, root: Path, mutate: Any) -> None:
    path = root / validator.MACHINE_PATH
    record = json.loads(path.read_text("ascii"))
    mutate(record)
    record["record_sha256"] = validator.record_sha256(record)
    path.write_bytes(validator.canonical_machine_bytes(record))
    os.chmod(path, 0o644)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["theorem_identity"].__setitem__("status", "CONJECTURE"),
        lambda r: r["assumptions"].__setitem__("event_kernel_characteristic", False),
        lambda r: r["assumptions"].__setitem__("count_scale_strictly_positive", False),
        lambda r: r["assumptions"].__setitem__("event_scale_strictly_positive", False),
        lambda r: r["assumptions"].__setitem__("outer_bandwidth_finite_positive", False),
        lambda r: r["assumptions"].__setitem__("hilbert_rkhs_separable", False),
        lambda r: r["embedding_contract"].__setitem__(
            "empty_event_channel", "NORMALIZE_EMPTY"
        ),
        lambda r: r["embedding_contract"].__setitem__("multiplicity_retained", False),
        lambda r: r["proof_conclusions"].__setitem__(
            "configuration_embedding_injective", False
        ),
        lambda r: r["proof_conclusions"].__setitem__(
            "outer_gaussian_characteristic_on_separable_hilbert", False
        ),
        lambda r: r["proof_conclusions"].__setitem__("cks_strictly_proper", False),
        lambda r: r["strict_propriety"].__setitem__(
            "expected_regret", "NOT_MMD_SQUARED"
        ),
        lambda r: r["strict_propriety"].__setitem__("lower_is_better", False),
        lambda r: r["edge_case_audit"].__setitem__(
            "unequal_mass_detected_by_count", False
        ),
        lambda r: r["edge_case_audit"].__setitem__(
            "duplicates_retained_by_empirical_mass", False
        ),
        lambda r: r["preliminary_formula_disposition"].__setitem__(
            "raw_unnormalized_formula_covered_by_theorem", True
        ),
        lambda r: r["project_effects"].__setitem__(
            "gate_a_exact_metric_checkbox_closed", True
        ),
        lambda r: r["project_effects"].__setitem__("scientific_fields_closed", 1),
        lambda r: r["project_effects"]["F106"].__setitem__("status", "CLOSED"),
        lambda r: r["project_effects"].__setitem__("blockers_closed", 1),
        lambda r: r["project_effects"].__setitem__("tracker_edit_performed", True),
        lambda r: r["nonclaims"].__setitem__("production_metric_implemented", True),
        lambda r: r["nonclaims"].__setitem__("data_opened", True),
        lambda r: r["nonclaims"].__setitem__("scientific_execution_performed", True),
    ],
)
def test_semantic_mutations_fail(
    validator: types.ModuleType, tmp_path: Path, mutate: Any
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_predecessor_drift_fails(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.EXPECTED_PREDECESSORS[0][1]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError, match="predecessor"):
        validator.validate(root)


def test_human_drift_fails(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.HUMAN_PATH
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError, match="package binding"):
        validator.validate(root)


def test_record_self_hash_refusal(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.MACHINE_PATH
    record = json.loads(path.read_text("ascii"))
    record["record_sha256"] = "0" * 64
    path.write_bytes(validator.canonical_machine_bytes(record))
    with pytest.raises(validator.ValidationError, match="record digest"):
        validator.validate(root)


def test_noncanonical_machine_bytes_refused(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.MACHINE_PATH
    record = json.loads(path.read_text("ascii"))
    path.write_text(json.dumps(record), encoding="ascii")
    with pytest.raises(validator.ValidationError, match="canonical"):
        validator.validate(root)


def test_duplicate_json_key_refused(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.MACHINE_PATH
    path.write_text('{"schema_version":"x","schema_version":"y"}\n', "ascii")
    with pytest.raises(validator.ValidationError, match="duplicate|roster|JSON"):
        validator.validate(root)


def test_machine_mode_and_hardlink_refused(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    machine = root / validator.MACHINE_PATH
    os.chmod(machine, 0o600)
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)
    os.chmod(machine, 0o644)
    os.link(machine, tmp_path / "alias.json")
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)


def test_symlink_leaf_refused(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    human = root / validator.HUMAN_PATH
    target = tmp_path / "human.md"
    human.rename(target)
    human.symlink_to(target)
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)


def test_validation_is_cwd_independent_and_read_only(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    tracked = [
        WORKSPACE / path
        for path in [
            validator.HUMAN_PATH,
            validator.MACHINE_PATH,
            validator.VALIDATOR_PATH,
            validator.TEST_PATH,
        ]
    ]
    before = [(path.stat().st_mtime_ns, path.read_bytes()) for path in tracked]
    old = Path.cwd()
    os.chdir(tmp_path)
    try:
        assert validator.validate(WORKSPACE)["validation"] == "PASS"
    finally:
        os.chdir(old)
    after = [(path.stat().st_mtime_ns, path.read_bytes()) for path in tracked]
    assert before == after


def test_validator_source_excludes_active_surfaces(validator: types.ModuleType) -> None:
    source = (WORKSPACE / validator.VALIDATOR_PATH).read_text("utf-8")
    forbidden = (
        "import socket",
        "import subprocess",
        "import requests",
        "import urllib",
        "import random",
        "import secrets",
        "import numpy",
        "import torch",
        "os.urandom",
        "urlopen(",
        "Popen(",
    )
    assert not any(token in source for token in forbidden)


def test_all_package_files_are_regular_single_link_mode_0644(
    validator: types.ModuleType,
) -> None:
    for relative in (
        validator.HUMAN_PATH,
        validator.MACHINE_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ):
        status = os.lstat(WORKSPACE / relative)
        assert stat.S_ISREG(status.st_mode)
        assert not stat.S_ISLNK(status.st_mode)
        assert stat.S_IMODE(status.st_mode) == 0o644
        assert status.st_nlink == 1
