from __future__ import annotations

from fractions import Fraction
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
    / "research/diagnostics/manuscript_v3_pilot_variance_power_strategy_draft_v1.py"
)


def _load_validator() -> types.ModuleType:
    module = types.ModuleType("pilot_variance_power_strategy_validator")
    module.__file__ = str(SOURCE)
    code = compile(SOURCE.read_bytes(), str(SOURCE), "exec")
    exec(code, module.__dict__)
    return module


@pytest.fixture(scope="module")
def validator() -> types.ModuleType:
    return _load_validator()


def _rows() -> list[Dict[str, Any]]:
    return [
        {"domain_id": "R3-PHYS", "seed_id": 7, "paired_seed_mean": Fraction(1, 2)},
        {"domain_id": "R3-PHYS", "seed_id": 3, "paired_seed_mean": Fraction(3, 2)},
        {"domain_id": "R4-RETAIL", "seed_id": 11, "paired_seed_mean": -1},
        {"domain_id": "R4-RETAIL", "seed_id": 5, "paired_seed_mean": 1},
    ]


def test_exact_summary_and_bessel_variance(validator: types.ModuleType) -> None:
    result = validator.summarize_seed_values(_rows())
    assert result == {
        "schema_version": "heterodiff-pilot-seed-summary-synthetic-v1",
        "summaries": [
            {
                "domain_id": "R3-PHYS",
                "seed_ids": [3, 7],
                "seed_count": 2,
                "pilot_mean": {"numerator": 1, "denominator": 1},
                "bessel_sample_variance": {"numerator": 1, "denominator": 2},
            },
            {
                "domain_id": "R4-RETAIL",
                "seed_ids": [5, 11],
                "seed_count": 2,
                "pilot_mean": {"numerator": 0, "denominator": 1},
                "bessel_sample_variance": {"numerator": 2, "denominator": 1},
            },
        ],
        "conditional_on_fixed_development_groups": True,
        "superpopulation_group_variance_claimed": False,
        "scientific_result": False,
    }


def test_input_permutation_invariance(validator: types.ModuleType) -> None:
    rows = _rows()
    assert validator.summarize_seed_values(rows) == validator.summarize_seed_values(
        list(reversed(rows))
    )


def test_translation_changes_mean_not_variance(validator: types.ModuleType) -> None:
    baseline = validator.summarize_seed_values(_rows())
    shifted = []
    for row in _rows():
        item = dict(row)
        item["paired_seed_mean"] = Fraction(item["paired_seed_mean"]) + 5
        shifted.append(item)
    result = validator.summarize_seed_values(shifted)
    for before, after in zip(baseline["summaries"], result["summaries"]):
        assert before["bessel_sample_variance"] == after["bessel_sample_variance"]
        assert after["pilot_mean"] == {
            "numerator": before["pilot_mean"]["numerator"]
            + 5 * before["pilot_mean"]["denominator"],
            "denominator": before["pilot_mean"]["denominator"],
        }


def test_zero_variance(validator: types.ModuleType) -> None:
    rows = [
        {"domain_id": domain, "seed_id": seed, "paired_seed_mean": Fraction(2, 3)}
        for domain in ("R3-PHYS", "R4-RETAIL")
        for seed in (0, 1, 2)
    ]
    result = validator.summarize_seed_values(rows)
    assert all(
        item["bessel_sample_variance"] == {"numerator": 0, "denominator": 1}
        for item in result["summaries"]
    )


@pytest.mark.parametrize(
    "rows,match",
    [
        (None, "list"),
        ([], "at least two"),
        ([{"domain_id": "R3-PHYS", "seed_id": 0}], "schema"),
        (_rows() + [_rows()[0]], "duplicate"),
        ([dict(_rows()[0], domain_id="OTHER")] + _rows()[1:], "domain"),
        ([dict(_rows()[0], seed_id=False)] + _rows()[1:], "seed"),
        ([dict(_rows()[0], seed_id=-1)] + _rows()[1:], "seed"),
        ([dict(_rows()[0], paired_seed_mean=0.5)] + _rows()[1:], "exact"),
        ([dict(_rows()[0], paired_seed_mean=True)] + _rows()[1:], "exact"),
    ],
)
def test_summary_refusals(validator: types.ModuleType, rows: Any, match: str) -> None:
    with pytest.raises(validator.ValidationError, match=match):
        validator.summarize_seed_values(rows)


def test_component_bound_refusal(validator: types.ModuleType) -> None:
    rows = _rows()
    rows[0] = dict(rows[0], paired_seed_mean=1 << 4096)
    with pytest.raises(validator.ValidationError, match="component bound"):
        validator.summarize_seed_values(rows)


def test_live_validator_passes_and_preserves_nonclosure(
    validator: types.ModuleType,
) -> None:
    status = validator.validate(WORKSPACE)
    assert status["validation"] == "PASS"
    assert status["control_predicate_value"] is True
    assert status["scientific_effect"] == 0
    assert status["unresolved_fields_closed"] == 0
    assert status["blockers_closed"] == 0
    assert status["pilot_run"] is False


def _copy_roster(validator: types.ModuleType, tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    paths = [path for _, path, _ in validator.EXPECTED_PREDECESSORS]
    paths += [
        validator.HUMAN_PATH,
        validator.MACHINE_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ]
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
        lambda r: r["project_control_effects"].__setitem__(
            "scientific_scorecard_effect", 1
        ),
        lambda r: r["project_control_effects"].__setitem__(
            "unresolved_fields_closed", 1
        ),
        lambda r: r["dependency_audit"]["F131"].__setitem__("value", "pilot"),
        lambda r: r["pilot_contract"].__setitem__(
            "test_material_or_outcomes_permitted", True
        ),
        lambda r: r["pilot_contract"].__setitem__(
            "drop_impute_replace_retry_topup_or_select_permitted", True
        ),
        lambda r: r["pilot_contract"].__setitem__(
            "pilot_seed_iid_or_exchangeability_law_matched_to_confirmatory_required",
            False,
        ),
        lambda r: r["pilot_contract"].__setitem__(
            "disjoint_registry_or_addresses_alone_prove_independence_or_transportability",
            True,
        ),
        lambda r: r["pilot_contract"].__setitem__(
            "paired_seed_statistic_bound_not_unpaired_metric_width_required", False
        ),
        lambda r: r["aggregation_contract"].__setitem__(
            "training_seed_is_independent_model_replication_unit", False
        ),
        lambda r: r["aggregation_contract"].__setitem__(
            "draw_case_group_or_seed_group_cell_is_independent_seed_replication_unit",
            True,
        ),
        lambda r: r["aggregation_contract"].__setitem__(
            "case_and_group_weights_exact_positive_rational_and_sum_to_one_required",
            False,
        ),
        lambda r: r["aggregation_contract"].__setitem__(
            "complete_Y_case_means_and_group_cells_retained_for_case_draw_grid", False
        ),
        lambda r: r["aggregation_contract"].__setitem__(
            "group_cells_alone_identify_case_or_draw_variation", True
        ),
        lambda r: r["future_power_route"].__setitem__(
            "candidate_values_are_preregistration_values", True
        ),
        lambda r: r["future_power_route"].__setitem__(
            "case_draw_grid_requires_frozen_hierarchical_resampling_or_generation_law",
            False,
        ),
        lambda r: r["future_power_route"].__setitem__(
            "unidentified_case_or_draw_allocation_disposition", "CONTINUE"
        ),
        lambda r: r["future_power_route"].__setitem__(
            "grid_expansion_topup_retry_replacement_selection_or_sequential_stopping_permitted",
            True,
        ),
        lambda r: r["synthetic_qualification"].__setitem__("real_pilot_run", True),
        lambda r: r["synthetic_qualification"].__setitem__(
            "seed_stream_transport_law_qualified", True
        ),
        lambda r: r["publication_boundary"].__setitem__(
            "anonymous_or_public_inclusion_permitted", True
        ),
    ],
)
def test_semantic_mutations_fail(
    validator: types.ModuleType, tmp_path: Path, mutate: Any
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_predecessor_drift_fails(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.EXPECTED_PREDECESSORS[0][1]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError, match="predecessor digest"):
        validator.validate(root)


def test_machine_mode_and_hardlink_fail(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    machine = root / validator.MACHINE_PATH
    os.chmod(machine, 0o600)
    with pytest.raises(validator.ValidationError, match="custody|resolution"):
        validator.validate(root)
    os.chmod(machine, 0o644)
    alias = machine.with_name("machine-alias.json")
    os.link(machine, alias)
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)


def test_machine_symlink_fails(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    machine = root / validator.MACHINE_PATH
    target = machine.with_name("real-machine.json")
    machine.rename(target)
    machine.symlink_to(target.name)
    with pytest.raises(validator.ValidationError, match="custody|resolution"):
        validator.validate(root)


def test_source_has_no_effectful_import_or_calls() -> None:
    text = SOURCE.read_text("utf-8")
    for forbidden in (
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "secrets",
        "random",
        "os.system",
        "os.popen",
        "os.exec",
        "os.spawn",
        "urlopen",
        "Popen",
    ):
        assert forbidden not in text
    assert "os.O_RDONLY" in text
    assert "os.open" in text
    assert "os.write" not in text


def test_human_draft_states_identification_and_transport_limits() -> None:
    text = (WORKSPACE / "PROJECT_PILOT_VARIANCE_POWER_STRATEGY_DRAFT.md").read_text(
        "utf-8"
    )
    assert "group-cell object alone does not identify" in text
    assert "distinct addresses or a disjoint registry alone do not establish" in text
    assert "weights are exact positive rationals and sum exactly to one" in text
    assert "W_pair = U_pair - L_pair" in text


def test_package_files_are_regular_0644_single_link(
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
