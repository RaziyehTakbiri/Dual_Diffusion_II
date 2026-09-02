"""Hostile qualification for the additive F137 formula-only closure."""

from __future__ import annotations

import ast
from fractions import Fraction
import importlib.util
import itertools
import json
import os
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    ROOT
    / "research/diagnostics/"
    "manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py"
)
SPEC = importlib.util.spec_from_file_location("f137_formula_freeze", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def _row(domain, seed, group, case, draw, conditioning, score):
    return {
        "domain_id": domain,
        "seed_id": seed,
        "group_id": group,
        "case_id": case,
        "draw_id": draw,
        "conditioning_id": conditioning,
        "score": score,
    }


def _base_inputs():
    domain = "R3-PHYS"
    seeds = ("SEED-A", "SEED-B")
    groups = ("GROUP-A", "GROUP-B")
    cases = (("CASE-A0",), ("CASE-B0", "CASE-B1"))
    draws = ((("DRAW-A00",),), (("DRAW-B00",), ("DRAW-B10",)))
    # Reuse across different groups is deliberately allowed; within-group IDs differ.
    conditioning = (("COND-0",), ("COND-0", "COND-1"))
    values = (
        (((Fraction(1),),), ((Fraction(3),), (Fraction(5),))),
        (((Fraction(2),),), ((Fraction(4),), (Fraction(6),))),
    )
    direct = []
    guide = []
    for seed_index, seed in enumerate(seeds):
        for group_index, group in enumerate(groups):
            for case_index, case in enumerate(cases[group_index]):
                condition = conditioning[group_index][case_index]
                for draw_index, draw in enumerate(draws[group_index][case_index]):
                    direct.append(
                        _row(
                            domain,
                            seed,
                            group,
                            case,
                            draw,
                            condition,
                            values[seed_index][group_index][case_index][draw_index],
                        )
                    )
                    guide.append(
                        _row(domain, seed, group, case, draw, condition, Fraction(0))
                    )
    return {
        "domain_id": domain,
        "seed_ids": seeds,
        "group_ids": groups,
        "case_ids_by_group": cases,
        "draw_ids_by_group_case": draws,
        "conditioning_ids_by_group_case": conditioning,
        "direct_rows": tuple(direct),
        "guide_rows": tuple(guide),
        "group_weights": (Fraction(1, 4), Fraction(3, 4)),
        "case_weights": ((Fraction(1),), (Fraction(1, 3), Fraction(2, 3))),
    }


def _plan(seed=(0, 1), group=(0, 1), cases=((0,), (0, 1))):
    return {
        "seed_indices": tuple(seed),
        "group_indices": tuple(group),
        "case_indices_by_group_occurrence": tuple(tuple(row) for row in cases),
    }


def _evaluate(inputs=None, plans=None):
    values = _base_inputs() if inputs is None else inputs
    return M.exact_hierarchical_paired_analysis(
        **values,
        bootstrap_plans=(_plan(),) if plans is None else plans,
    )


def _multidraw_inputs():
    """Return an exact fixture with heterogeneous R_{d,g,c}."""

    values = _base_inputs()
    draws = ((('DRAW-A00', 'DRAW-A01'),), values["draw_ids_by_group_case"][1])
    score_by_address = {
        tuple(row[key] for key in M.ROW_KEYS[:-1]): row["score"]
        for row in values["direct_rows"]
    }
    score_by_address.update(
        {
            (values["domain_id"], "SEED-A", "GROUP-A", "CASE-A0", "DRAW-A00", "COND-0"): Fraction(0),
            (values["domain_id"], "SEED-A", "GROUP-A", "CASE-A0", "DRAW-A01", "COND-0"): Fraction(4),
            (values["domain_id"], "SEED-B", "GROUP-A", "CASE-A0", "DRAW-A00", "COND-0"): Fraction(1),
            (values["domain_id"], "SEED-B", "GROUP-A", "CASE-A0", "DRAW-A01", "COND-0"): Fraction(5),
        }
    )
    direct = []
    guide = []
    for seed in values["seed_ids"]:
        for group_index, group in enumerate(values["group_ids"]):
            for case_index, case in enumerate(values["case_ids_by_group"][group_index]):
                condition = values["conditioning_ids_by_group_case"][group_index][case_index]
                for draw in draws[group_index][case_index]:
                    address = (values["domain_id"], seed, group, case, draw, condition)
                    direct.append(_row(*address, score_by_address[address]))
                    guide.append(_row(*address, Fraction(0)))
    values["draw_ids_by_group_case"] = draws
    values["direct_rows"] = tuple(direct)
    values["guide_rows"] = tuple(guide)
    return values


def _singleton_inputs():
    domain = "R3-PHYS"
    seeds = ("SEED-A", "SEED-B")
    groups = ("GROUP-A",)
    cases = (("CASE-A0",),)
    draws = ((("DRAW-A00",),),)
    conditioning = (("COND-0",),)
    direct = tuple(
        _row(domain, seed, groups[0], cases[0][0], draws[0][0][0], conditioning[0][0], score)
        for seed, score in zip(seeds, (Fraction(1), Fraction(3)))
    )
    guide = tuple(dict(row, score=Fraction(0)) for row in direct)
    return {
        "domain_id": domain,
        "seed_ids": seeds,
        "group_ids": groups,
        "case_ids_by_group": cases,
        "draw_ids_by_group_case": draws,
        "conditioning_ids_by_group_case": conditioning,
        "direct_rows": direct,
        "guide_rows": guide,
        "group_weights": (Fraction(1),),
        "case_weights": ((Fraction(1),),),
    }


def _as_fraction(record):
    return Fraction(record["numerator"], record["denominator"])


def _mutated_row(rows, index, key, value):
    result = list(rows)
    row = dict(result[index])
    row[key] = value
    result[index] = row
    return tuple(result)


def _shifted_rows(rows, shift):
    return tuple(dict(row, score=row["score"] + shift) for row in rows)


def _copy_bound_tree(tmp_path: Path) -> Path:
    paths = {M.HUMAN_PATH, M.MACHINE_PATH, M.VALIDATOR_PATH, M.TEST_PATH}
    paths.update(spec[2] for spec in M.PREDECESSOR_SPECS)
    for relative in sorted(paths):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        target.chmod(0o644)
    return tmp_path


def _machine(root: Path):
    return json.loads((root / M.MACHINE_PATH).read_text(encoding="ascii"))


def _write_resigned_machine(root: Path, record):
    record["record_sha256"] = M.record_sha256(record)
    (root / M.MACHINE_PATH).write_bytes(M.canonical_machine_bytes(record))


def _reordered_inputs(values):
    old_rows = {
        tuple(row[key] for key in M.ROW_KEYS[:-1]): row["score"]
        for row in values["direct_rows"]
    }
    old_guide = {
        tuple(row[key] for key in M.ROW_KEYS[:-1]): row["score"]
        for row in values["guide_rows"]
    }
    seeds = tuple(reversed(values["seed_ids"]))
    group_order = (1, 0)
    groups = tuple(values["group_ids"][index] for index in group_order)
    case_orders = {0: (0,), 1: (1, 0)}
    cases = tuple(
        tuple(values["case_ids_by_group"][old_group][index] for index in case_orders[old_group])
        for old_group in group_order
    )
    draws = tuple(
        tuple(
            values["draw_ids_by_group_case"][old_group][old_case]
            for old_case in case_orders[old_group]
        )
        for old_group in group_order
    )
    conditioning = tuple(
        tuple(
            values["conditioning_ids_by_group_case"][old_group][old_case]
            for old_case in case_orders[old_group]
        )
        for old_group in group_order
    )
    direct = []
    guide = []
    for seed in seeds:
        for group_index, group in enumerate(groups):
            for case_index, case in enumerate(cases[group_index]):
                condition = conditioning[group_index][case_index]
                for draw in draws[group_index][case_index]:
                    address = (values["domain_id"], seed, group, case, draw, condition)
                    direct.append(_row(*address, old_rows[address]))
                    guide.append(_row(*address, old_guide[address]))
    return {
        "domain_id": values["domain_id"],
        "seed_ids": seeds,
        "group_ids": groups,
        "case_ids_by_group": cases,
        "draw_ids_by_group_case": draws,
        "conditioning_ids_by_group_case": conditioning,
        "direct_rows": tuple(direct),
        "guide_rows": tuple(guide),
        "group_weights": tuple(values["group_weights"][index] for index in group_order),
        "case_weights": tuple(
            tuple(values["case_weights"][old_group][index] for index in case_orders[old_group])
            for old_group in group_order
        ),
    }


def test_canonical_package_validates():
    receipt = M.validate(ROOT)
    assert receipt["validation"] == "PASS"
    assert receipt["F137_closed"] is True
    assert receipt["B07_open"] is True
    assert receipt["F112_open"] is True
    assert receipt["F138_open"] is True
    assert receipt["effective_pre_execution_open"] == 144
    assert receipt["effective_pre_execution_closed"] == 22
    assert receipt["effective_post_execution_open"] == 3
    assert receipt["effective_post_execution_closed"] == 3
    assert receipt["scientific_execution"] is False


def test_validator_and_expected_record_are_cwd_independent(monkeypatch, tmp_path):
    expected = M.expected_record(ROOT)
    monkeypatch.chdir(tmp_path)
    assert M.expected_record(ROOT) == expected
    assert M.validate(ROOT)["validation"] == "PASS"


def test_machine_is_canonical_duplicate_free_ascii_json():
    raw = (ROOT / M.MACHINE_PATH).read_bytes()
    actual = M._parse_json(raw, "machine")
    assert raw == M.canonical_machine_bytes(actual)
    assert actual["record_sha256"] == M.record_sha256(actual)


def test_exact_known_answer_point_and_vector():
    result = _evaluate(plans=(_plan(), _plan()))
    assert _as_fraction(result["point_estimate"]) == 4
    assert [_as_fraction(row) for row in result["bootstrap_replicates"]] == [
        Fraction(3),
        Fraction(3),
    ]
    assert result["dimensions"] == {
        "training_seeds": 2,
        "natural_groups": 2,
        "cases_by_group": [1, 2],
        "draws_by_group_case": [[1], [1, 1]],
    }
    assert result["zero_empirical_bootstrap_spread"] is True
    assert "ZERO_EMPIRICAL_BOOTSTRAP_SPREAD" in result["flags"]
    assert "SINGLETON_CASE_LAYER_PRESENT" in result["flags"]
    assert "SINGLETON_DRAW_LAYER_PRESENT" in result["flags"]
    assert "SINGLETON_NATURAL_GROUP_LAYER" not in result["flags"]
    assert "caller_supplied_plan_count" not in result
    assert result["plan_count_chosen_recommended_defaulted_or_reported"] is False
    assert result["confidence_interval_or_decision_produced"] is False


def test_heterogeneous_multidraw_known_answer_and_draw_order_invariance():
    values = _multidraw_inputs()
    result = _evaluate(values, plans=(_plan(),))
    assert result["dimensions"]["draws_by_group_case"] == [[2], [1, 1]]
    assert _as_fraction(result["point_estimate"]) == Fraction(17, 4)
    assert _as_fraction(result["bootstrap_replicates"][0]) == Fraction(7, 2)

    reordered = _multidraw_inputs()
    reordered["draw_ids_by_group_case"] = (
        (("DRAW-A01", "DRAW-A00"),),
        reordered["draw_ids_by_group_case"][1],
    )
    old_direct = {
        tuple(row[key] for key in M.ROW_KEYS[:-1]): row["score"]
        for row in reordered["direct_rows"]
    }
    old_guide = {
        tuple(row[key] for key in M.ROW_KEYS[:-1]): row["score"]
        for row in reordered["guide_rows"]
    }
    direct = []
    guide = []
    for seed in reordered["seed_ids"]:
        for group_index, group in enumerate(reordered["group_ids"]):
            for case_index, case in enumerate(reordered["case_ids_by_group"][group_index]):
                condition = reordered["conditioning_ids_by_group_case"][group_index][case_index]
                for draw in reordered["draw_ids_by_group_case"][group_index][case_index]:
                    address = (reordered["domain_id"], seed, group, case, draw, condition)
                    direct.append(_row(*address, old_direct[address]))
                    guide.append(_row(*address, old_guide[address]))
    reordered["direct_rows"] = tuple(direct)
    reordered["guide_rows"] = tuple(guide)
    reordered_result = _evaluate(reordered, plans=(_plan(),))
    assert reordered_result["point_estimate"] == result["point_estimate"]
    assert reordered_result["bootstrap_replicates"] == result["bootstrap_replicates"]


def test_all_singleton_layer_degeneracies_are_explicitly_flagged():
    plan = _plan(seed=(0, 1), group=(0,), cases=((0,),))
    result = _evaluate(_singleton_inputs(), plans=(plan,))
    assert _as_fraction(result["point_estimate"]) == 2
    assert set(result["flags"]) == {
        "SINGLETON_NATURAL_GROUP_LAYER",
        "SINGLETON_CASE_LAYER_PRESENT",
        "SINGLETON_DRAW_LAYER_PRESENT",
        "ZERO_EMPIRICAL_BOOTSTRAP_SPREAD",
    }


def test_nonzero_spread_is_algebraic_only():
    result = _evaluate(
        plans=(
            _plan(seed=(0, 0), group=(0, 0), cases=((0,), (0,))),
            _plan(seed=(1, 1), group=(1, 1), cases=((1, 1), (1, 1))),
        )
    )
    assert result["zero_empirical_bootstrap_spread"] is False
    assert "ZERO_EMPIRICAL_BOOTSTRAP_SPREAD" not in result["flags"]
    assert result["confidence_interval_or_decision_produced"] is False


def test_exact_bootstrap_expectation_equals_weighted_point_estimator():
    values = _base_inputs()
    point = _as_fraction(_evaluate(values)["point_estimate"])
    expectation = Fraction(0)
    probability_total = Fraction(0)
    weights = values["group_weights"]
    case_weights = values["case_weights"]
    case_counts = tuple(len(row) for row in values["case_ids_by_group"])
    for seed_indices in itertools.product(range(2), repeat=2):
        seed_probability = Fraction(1, 2) ** 2
        for group_indices in itertools.product(range(2), repeat=2):
            group_probability = weights[group_indices[0]] * weights[group_indices[1]]
            map_options = [
                tuple(itertools.product(range(case_counts[group]), repeat=case_counts[group]))
                for group in group_indices
            ]
            for case_maps in itertools.product(*map_options):
                case_probability = Fraction(1)
                for occurrence, group in enumerate(group_indices):
                    for case in case_maps[occurrence]:
                        case_probability *= case_weights[group][case]
                probability = seed_probability * group_probability * case_probability
                plan = _plan(seed_indices, group_indices, case_maps)
                replicate = _as_fraction(
                    _evaluate(values, plans=(plan,))["bootstrap_replicates"][0]
                )
                expectation += probability * replicate
                probability_total += probability
    assert probability_total == 1
    assert expectation == point


def test_direct_guide_swap_reverses_point_and_replicates():
    values = _base_inputs()
    plans = (_plan(), _plan(seed=(1, 1), group=(1, 1), cases=((1, 1), (0, 0))))
    forward = _evaluate(values, plans)
    reverse_values = dict(values)
    reverse_values["direct_rows"] = values["guide_rows"]
    reverse_values["guide_rows"] = values["direct_rows"]
    reverse = _evaluate(reverse_values, plans)
    assert _as_fraction(reverse["point_estimate"]) == -_as_fraction(
        forward["point_estimate"]
    )
    assert [_as_fraction(row) for row in reverse["bootstrap_replicates"]] == [
        -_as_fraction(row) for row in forward["bootstrap_replicates"]
    ]


def test_common_shift_cancels_exactly():
    values = _base_inputs()
    shifted = dict(values)
    shifted["direct_rows"] = _shifted_rows(values["direct_rows"], Fraction(17, 5))
    shifted["guide_rows"] = _shifted_rows(values["guide_rows"], Fraction(17, 5))
    assert _evaluate(shifted) == _evaluate(values)


def test_joint_seed_group_case_order_permutation_is_invariant():
    values = _base_inputs()
    original_plan = _plan((0, 1), (0, 1), ((0,), (0, 1)))
    original = _evaluate(values, (original_plan,))
    reordered = _reordered_inputs(values)
    transformed_plan = _plan((1, 0), (1, 0), ((0,), (1, 0)))
    transformed = _evaluate(reordered, (transformed_plan,))
    assert transformed["point_estimate"] == original["point_estimate"]
    assert transformed["bootstrap_replicates"] == original["bootstrap_replicates"]


def test_identity_renaming_without_reordering_is_invariant():
    values = _base_inputs()
    renamed = dict(values)
    replacements = {
        "SEED-A": "S-X",
        "SEED-B": "S-Y",
        "GROUP-A": "G-X",
        "GROUP-B": "G-Y",
        "CASE-A0": "C-X0",
        "CASE-B0": "C-Y0",
        "CASE-B1": "C-Y1",
        "DRAW-A00": "D-X0",
        "DRAW-B00": "D-Y0",
        "DRAW-B10": "D-Y1",
        "COND-0": "K-0",
        "COND-1": "K-1",
    }
    renamed["seed_ids"] = tuple(replacements[value] for value in values["seed_ids"])
    renamed["group_ids"] = tuple(replacements[value] for value in values["group_ids"])
    renamed["case_ids_by_group"] = tuple(
        tuple(replacements[value] for value in row) for row in values["case_ids_by_group"]
    )
    renamed["draw_ids_by_group_case"] = tuple(
        tuple(tuple(replacements[value] for value in row) for row in group)
        for group in values["draw_ids_by_group_case"]
    )
    renamed["conditioning_ids_by_group_case"] = tuple(
        tuple(replacements[value] for value in row)
        for row in values["conditioning_ids_by_group_case"]
    )
    for key in ("direct_rows", "guide_rows"):
        rows = []
        for row in values[key]:
            updated = dict(row)
            for address_key in M.ROW_KEYS[1:-1]:
                updated[address_key] = replacements[updated[address_key]]
            rows.append(updated)
        renamed[key] = tuple(rows)
    assert _evaluate(renamed) == _evaluate(values)


def test_domain_identity_is_separate_and_cross_domain_pooling_absent():
    values = _base_inputs()
    retail = dict(values)
    retail["domain_id"] = "R4-RETAIL"
    retail["direct_rows"] = tuple(dict(row, domain_id="R4-RETAIL") for row in values["direct_rows"])
    retail["guide_rows"] = tuple(dict(row, domain_id="R4-RETAIL") for row in values["guide_rows"])
    result = _evaluate(retail)
    assert result["domain_id"] == "R4-RETAIL"
    assert result["point_estimate"] == _evaluate(values)["point_estimate"]
    assert "cross_domain" not in result


def test_cross_group_conditioning_label_reuse_is_allowed():
    assert _base_inputs()["conditioning_ids_by_group_case"][0][0] == "COND-0"
    assert _base_inputs()["conditioning_ids_by_group_case"][1][0] == "COND-0"
    assert _evaluate()["direct_guide_pairing_validated"] is True


@pytest.mark.parametrize(
    "key,value,message",
    [
        ("domain_id", "R5-OTHER", "two-domain roster"),
        ("seed_ids", ("SEED-A", "SEED-A"), "duplicate or aliased"),
        ("seed_ids", ("SEED-A",), "too few"),
        ("group_ids", tuple(), "too few"),
        ("group_ids", ("GROUP-A", "GROUP-A"), "duplicate or aliased"),
        ("case_ids_by_group", (("CASE",), ("CASE", "CASE")), "duplicate or aliased"),
        ("case_ids_by_group", (("CASE",), tuple()), "too few"),
        ("case_ids_by_group", (("CASE",),), "group roster mismatch"),
        ("seed_ids", ("SEED A", "SEED-B"), "without whitespace"),
        ("seed_ids", ("SEED\tA", "SEED-B"), "without whitespace"),
        ("seed_ids", ("SÉED-A", "SEED-B"), "canonical ASCII"),
    ],
)
def test_invalid_identity_rosters_fail_closed(key, value, message):
    inputs = _base_inputs()
    inputs[key] = value
    with pytest.raises(M.ValidationError, match=message):
        _evaluate(inputs)


def test_duplicate_draw_identity_within_case_fails_closed():
    inputs = _base_inputs()
    inputs["draw_ids_by_group_case"] = (
        (("DUP", "DUP"),),
        inputs["draw_ids_by_group_case"][1],
    )
    with pytest.raises(M.ValidationError, match="duplicate or aliased"):
        _evaluate(inputs)


@pytest.mark.parametrize(
    "key,value,message",
    [
        (
            "draw_ids_by_group_case",
            ((tuple(),), (("DRAW-B00",), ("DRAW-B10",))),
            "too few identities",
        ),
        (
            "draw_ids_by_group_case",
            ((("DRAW-A00",),),),
            "group roster mismatch",
        ),
        (
            "conditioning_ids_by_group_case",
            (("COND-0",),),
            "group roster mismatch",
        ),
        (
            "draw_ids_by_group_case",
            ((("DRAW-A00",),), (("DRAW-B00",),)),
            "case roster mismatch",
        ),
        (
            "conditioning_ids_by_group_case",
            (("COND-0",), ("COND-0",)),
            "case roster mismatch",
        ),
    ],
)
def test_empty_or_misaligned_nested_draw_and_conditioning_rosters_fail(
    key, value, message
):
    inputs = _base_inputs()
    inputs[key] = value
    with pytest.raises(M.ValidationError, match=message):
        _evaluate(inputs)


def test_duplicate_conditioning_identity_within_group_fails_closed():
    inputs = _base_inputs()
    inputs["conditioning_ids_by_group_case"] = (
        inputs["conditioning_ids_by_group_case"][0],
        ("DUP-COND", "DUP-COND"),
    )
    with pytest.raises(M.ValidationError, match="unique within each natural group"):
        _evaluate(inputs)


@pytest.mark.parametrize(
    "target,key,value,message",
    [
        ("direct_rows", "domain_id", "R4-RETAIL", "direct row address"),
        ("guide_rows", "domain_id", "R4-RETAIL", "pairing mismatch"),
        ("guide_rows", "seed_id", "SEED-B", "pairing mismatch"),
        ("guide_rows", "group_id", "GROUP-B", "pairing mismatch"),
        ("guide_rows", "case_id", "CASE-B1", "pairing mismatch"),
        ("guide_rows", "draw_id", "OTHER-DRAW", "pairing mismatch"),
        ("guide_rows", "conditioning_id", "OTHER-COND", "pairing mismatch"),
    ],
)
def test_cross_domain_or_direct_guide_pairing_mismatch_fails(
    target, key, value, message
):
    inputs = _base_inputs()
    inputs[target] = _mutated_row(inputs[target], 0, key, value)
    with pytest.raises(M.ValidationError, match=message):
        _evaluate(inputs)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "reordered"])
def test_missing_extra_duplicate_or_out_of_order_rows_fail(mutation):
    inputs = _base_inputs()
    rows = list(inputs["direct_rows"])
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(dict(rows[-1]))
    elif mutation == "duplicate":
        rows[1] = dict(rows[0])
    else:
        rows[0], rows[1] = rows[1], rows[0]
    inputs["direct_rows"] = tuple(rows)
    with pytest.raises(M.ValidationError, match="row count|direct row address"):
        _evaluate(inputs)


def test_row_key_roster_and_order_are_exact():
    inputs = _base_inputs()
    rows = list(inputs["direct_rows"])
    row = dict(rows[0])
    row["extra"] = None
    rows[0] = row
    inputs["direct_rows"] = tuple(rows)
    with pytest.raises(M.ValidationError, match="key roster or order"):
        _evaluate(inputs)

    inputs = _base_inputs()
    rows = list(inputs["guide_rows"])
    old = rows[0]
    rows[0] = {key: old[key] for key in reversed(M.ROW_KEYS)}
    inputs["guide_rows"] = tuple(rows)
    with pytest.raises(M.ValidationError, match="key roster or order"):
        _evaluate(inputs)


class _IntSubclass(int):
    pass


@pytest.mark.parametrize(
    "value,message",
    [
        (True, "exact int or Fraction"),
        (1.0, "exact int or Fraction"),
        (_IntSubclass(1), "exact int or Fraction"),
        (1 << M.MAX_EXACT_COMPONENT_BITS, "bit bound"),
    ],
)
def test_invalid_score_type_or_bound_fails(value, message):
    inputs = _base_inputs()
    inputs["direct_rows"] = _mutated_row(inputs["direct_rows"], 0, "score", value)
    with pytest.raises(M.ValidationError, match=message):
        _evaluate(inputs)


@pytest.mark.parametrize(
    "weights,message",
    [
        ((True, Fraction(0)), "exact int or Fraction"),
        ((1.0, Fraction(0)), "exact int or Fraction"),
        ((Fraction(0), Fraction(1)), "strictly positive"),
        ((Fraction(-1), Fraction(2)), "strictly positive"),
        ((Fraction(1, 2), Fraction(1, 3)), "sum exactly"),
        ((Fraction(1),), "roster mismatch"),
    ],
)
def test_invalid_group_weights_fail_closed(weights, message):
    inputs = _base_inputs()
    inputs["group_weights"] = weights
    with pytest.raises(M.ValidationError, match=message):
        _evaluate(inputs)


@pytest.mark.parametrize(
    "weights,message",
    [
        (((Fraction(1),), (Fraction(1),)), "roster mismatch"),
        (((Fraction(1),), (Fraction(0), Fraction(1))), "strictly positive"),
        (((Fraction(1),), (Fraction(1, 3), Fraction(1, 3))), "sum exactly"),
        (((Fraction(1),), (True, Fraction(0))), "exact int or Fraction"),
    ],
)
def test_invalid_case_weights_fail_closed(weights, message):
    inputs = _base_inputs()
    inputs["case_weights"] = weights
    with pytest.raises(M.ValidationError, match=message):
        _evaluate(inputs)


def test_variable_case_cardinality_controls_each_selected_case_map():
    valid = _plan(group=(0, 1), cases=((0,), (0, 1)))
    assert _evaluate(plans=(valid,))["dimensions"]["cases_by_group"] == [1, 2]
    wrong_first = _plan(group=(0, 1), cases=((0, 0), (0, 1)))
    with pytest.raises(M.ValidationError, match="selected C_g"):
        _evaluate(plans=(wrong_first,))
    wrong_second = _plan(group=(1, 0), cases=((0,), (0,)))
    with pytest.raises(M.ValidationError, match="selected C_g"):
        _evaluate(plans=(wrong_second,))


def test_duplicate_group_occurrences_have_independent_case_maps_shared_across_seeds():
    result = _evaluate(
        plans=(
            _plan(
                seed=(0, 1),
                group=(1, 1),
                cases=((0, 0), (1, 1)),
            ),
        )
    )
    # First group occurrence selects B0 twice, second selects B1 twice.
    assert _as_fraction(result["bootstrap_replicates"][0]) == Fraction(9, 2)


@pytest.mark.parametrize(
    "plan,message",
    [
        ({"group_indices": (0, 1), "seed_indices": (0, 1), "case_indices_by_group_occurrence": ((0,), (0, 1))}, "key roster or order"),
        ({"seed_indices": (0, 1), "group_indices": (0, 1)}, "key roster or order"),
        ({"seed_indices": (0, 1), "group_indices": (0, 1), "case_indices_by_group_occurrence": ((0,), (0, 1)), "draw_indices": ()}, "key roster or order"),
        (_plan(seed=(0,)), "seed occurrence"),
        (_plan(group=(0,)), "group occurrence"),
        (_plan(cases=((0,),)), "one case map"),
        (_plan(seed=(0, True)), "exact built-in integer"),
        (_plan(seed=(0, 2)), "out of range"),
        (_plan(group=(0, -1)), "out of range"),
        (_plan(cases=((0,), (0, 2))), "out of range"),
        (_plan(cases=(((0,),), (0, 1))), "exact built-in integer"),
    ],
)
def test_invalid_bootstrap_plans_fail_closed(plan, message):
    with pytest.raises(M.ValidationError, match=message):
        _evaluate(plans=(plan,))


def test_plan_vector_must_be_nonempty_exact_tuple():
    with pytest.raises(M.ValidationError, match="exact tuple"):
        _evaluate(plans=[_plan()])
    with pytest.raises(M.ValidationError, match="at least one"):
        _evaluate(plans=())


def test_formula_contract_has_no_F112_F138_or_operand_value():
    boundary = M.FORMULA_VALUE["parameterization_boundary"]
    assert boundary["primary_metric_selected"] is False
    assert boundary["confidence_method_F112_selected"] is False
    assert boundary["resample_count_F138_selected"] is False
    assert boundary["weights_cardinalities_or_seed_values_populated"] is False
    law = M.FORMULA_VALUE["one_plan_bootstrap_law"]
    assert law["weights_reapplied_after_selection"] is False
    assert law["draw_sampling"].startswith("NEVER")
    assert law["plan_count_chosen_recommended_defaulted_or_reported"] is False


def test_exact_field_rosters_and_b11_aware_count_delta():
    expected = M.expected_record(ROOT)
    sweep = expected["comprehensive_field_sweep"]
    transition = expected["count_transition"]
    assert len(M.PRE_FIELDS) == 166
    assert len(M.POST_FIELDS) == 6
    assert len(M.CLOSED_BEFORE) == 21
    assert len(M.CLOSED_AFTER) == 22
    assert len(M.OPEN_BEFORE) == 145
    assert len(M.OPEN_AFTER) == 144
    assert sweep["eligible_now_ids"] == ["F137"]
    assert sweep["closed_post_execution_ids_preserved"] == ["F168", "F170", "F171"]
    assert sweep["open_post_execution_ids_preserved"] == ["F164", "F165", "F169"]
    assert transition["before"] == {
        "pre_execution_open": 145,
        "pre_execution_closed": 21,
        "post_execution_open": 3,
        "post_execution_closed": 3,
        "total_open": 148,
        "total_closed": 24,
    }
    assert transition["after"] == {
        "pre_execution_open": 144,
        "pre_execution_closed": 22,
        "post_execution_open": 3,
        "post_execution_closed": 3,
        "total_open": 147,
        "total_closed": 25,
    }


def test_exact_predecessor_roster_and_group_counts():
    assert len(M.PREDECESSOR_SPECS) == 35
    assert sum(
        value for key, value in M.PREDECESSOR_GROUP_COUNTS.items() if key != "total"
    ) == 35
    assert M.PREDECESSOR_GROUP_COUNTS["POWER_ALLOCATION_ROUTE_V1"] == 4
    assert M.PREDECESSOR_GROUP_COUNTS["PILOT_VARIANCE_STRATEGY_V1"] == 4
    assert M.PREDECESSOR_GROUP_COUNTS["F104_COUNT_ANCHOR_V1"] == 5
    assert M.PREDECESSOR_GROUP_COUNTS["B11_POSTEXECUTION_COUNT_ANCHOR_V1"] == 5


def test_physionet_custom_digest_is_raw_bound_without_false_generic_claim():
    expected = M.expected_record(ROOT)
    rows = {
        row["path"]: row for row in expected["predecessor_bindings"]
    }
    phys = rows[
        "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json"
    ]
    assert phys["raw_sha256"] == "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8"
    assert "record_sha256" not in phys
    assert expected["predecessor_projection_receipt"]["natural_group_carriers"]["R3-PHYS"] == "PATIENT"


def test_source_effect_surface_is_read_only_and_entropy_free():
    source = (ROOT / M.VALIDATOR_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed_import_roots = {
        "__future__",
        "fractions",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "stat",
        "typing",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert {alias.name.split(".")[0] for alias in node.names} <= allowed_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "write",
                    "write_bytes",
                    "write_text",
                    "mkdir",
                    "unlink",
                    "rename",
                    "replace",
                    "socket",
                    "connect",
                    "sendall",
                    "urlopen",
                    "run",
                    "Popen",
                    "fork",
                    "urandom",
                }
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "exec", "eval", "compile"}
    assert "random" not in source
    assert "numpy" not in source
    assert "scipy" not in source
    assert "heterodiff." not in source


@pytest.mark.parametrize(
    "relative",
    ["../escape", "/absolute/path", "a/../b", "a/./b", "a//b", "a\\b"],
)
def test_stable_reader_rejects_noncanonical_or_escaping_paths(relative):
    with pytest.raises(M.ValidationError):
        M._stable_read(ROOT, relative)


def test_stable_reader_requires_absolute_root(tmp_path):
    relative_root = Path(os.path.relpath(tmp_path, Path.cwd()))
    with pytest.raises(M.ValidationError, match="absolute"):
        M._stable_read(relative_root, M.HUMAN_PATH)


@pytest.mark.parametrize("kind", ["mode", "hardlink", "symlink"])
def test_custody_substitutions_fail_closed(tmp_path, kind):
    clone = _copy_bound_tree(tmp_path)
    target = clone / M.HUMAN_PATH
    if kind == "mode":
        target.chmod(0o755)
    elif kind == "hardlink":
        os.link(target, clone / "extra-hardlink")
    else:
        original = clone / "human-original"
        target.rename(original)
        target.symlink_to(original.name)
    with pytest.raises(M.ValidationError):
        M.validate(clone)


def test_symlinked_ancestor_fails_closed(tmp_path):
    clone = _copy_bound_tree(tmp_path / "clone")
    real_research = clone / "research-real"
    (clone / "research").rename(real_research)
    (clone / "research").symlink_to(real_research.name)
    with pytest.raises(M.ValidationError):
        M.validate(clone)


def test_mid_read_chmod_race_is_detected(tmp_path, monkeypatch):
    clone = _copy_bound_tree(tmp_path)
    target = clone / M.HUMAN_PATH
    original_read = M.os.read
    fired = False

    def racing_read(descriptor, count):
        nonlocal fired
        result = original_read(descriptor, count)
        if not fired:
            fired = True
            target.chmod(0o600)
        return result

    monkeypatch.setattr(M.os, "read", racing_read)
    with pytest.raises(M.ValidationError, match="after-descriptor|changed"):
        M._stable_read(clone, M.HUMAN_PATH)


def test_mid_read_inode_substitution_race_is_detected(tmp_path, monkeypatch):
    clone = _copy_bound_tree(tmp_path)
    target = clone / M.HUMAN_PATH
    backup = clone / "human-race-backup"
    original_read = M.os.read
    fired = False

    def racing_read(descriptor, count):
        nonlocal fired
        result = original_read(descriptor, count)
        if not fired:
            fired = True
            target.rename(backup)
            target.write_bytes(backup.read_bytes())
            target.chmod(0o644)
        return result

    monkeypatch.setattr(M.os, "read", racing_read)
    with pytest.raises(M.ValidationError, match="descriptor read|namespace changed"):
        M._stable_read(clone, M.HUMAN_PATH)


def test_fingerprint_includes_permission_mode(tmp_path):
    path = tmp_path / "mode.txt"
    path.write_text("x", encoding="ascii")
    path.chmod(0o644)
    before = M._fingerprint(path.stat())
    path.chmod(0o600)
    assert M._fingerprint(path.stat()) != before


def test_noncanonical_and_duplicate_key_machine_fail_closed(tmp_path):
    clone = _copy_bound_tree(tmp_path / "space")
    machine_path = clone / M.MACHINE_PATH
    raw = machine_path.read_bytes()
    machine_path.write_bytes(raw[:-1] + b" \n")
    with pytest.raises(M.ValidationError, match="canonical"):
        M.validate(clone)

    clone = _copy_bound_tree(tmp_path / "duplicate")
    machine_path = clone / M.MACHINE_PATH
    raw = machine_path.read_bytes()
    machine_path.write_bytes(b'{"schema_version":"duplicate",' + raw[1:])
    with pytest.raises(M.ValidationError, match="strict JSON"):
        M.validate(clone)


@pytest.mark.parametrize("spec_index", [0, 2, 6, 10, 14, 18, 22, 27, 31])
def test_every_predecessor_group_is_byte_pinned(tmp_path, spec_index):
    clone = _copy_bound_tree(tmp_path)
    path = M.PREDECESSOR_SPECS[spec_index][2]
    target = clone / path
    target.write_bytes(target.read_bytes() + b"mutant\n")
    target.chmod(0o644)
    with pytest.raises(M.ValidationError, match="predecessor exact-byte mismatch"):
        M.validate(clone)


@pytest.mark.parametrize("package_path", [M.HUMAN_PATH, M.VALIDATOR_PATH, M.TEST_PATH])
def test_every_nonmachine_package_byte_is_self_bound(tmp_path, package_path):
    clone = _copy_bound_tree(tmp_path)
    target = clone / package_path
    target.write_bytes(target.read_bytes() + b"mutant\n")
    target.chmod(0o644)
    with pytest.raises(M.ValidationError, match="package machine record"):
        M.validate(clone)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda r: r["field_closures"][0].__setitem__("field_id", "F112"),
        lambda r: r["field_closures"].append(
            {"field_id": "F138", "json_pointer": "/power_and_seed_plan/confidence_interval_resample_count", "status": "CLOSED", "value": 1000}
        ),
        lambda r: r["count_transition"]["after"].__setitem__("pre_execution_open", 143),
        lambda r: r["count_transition"]["after"].__setitem__("post_execution_open", 6),
        lambda r: r["comprehensive_field_sweep"]["eligible_now_ids"].append("F138"),
        lambda r: r["comprehensive_field_sweep"]["closed_post_execution_ids_preserved"].clear(),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("B07_remains_open", False),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("B11_remains_open", False),
        lambda r: r["f137_parameterization_boundary"].__setitem__("F112_confidence_method_selected", True),
        lambda r: r["f137_parameterization_boundary"].__setitem__("F138_resample_count_selected", True),
        lambda r: r["f137_parameterization_boundary"].__setitem__("actual_primary_metric_or_numeric_representation_populated", True),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("domain_instance_admitted", True),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("entropy_training_scientific_or_production_execution_performed", True),
        lambda r: r["field_closures"][0]["value"]["one_plan_bootstrap_law"].__setitem__("weights_reapplied_after_selection", True),
        lambda r: r["field_closures"][0]["value"]["one_plan_bootstrap_law"].__setitem__("draw_sampling", "IID_WITH_REPLACEMENT"),
        lambda r: r["field_closures"][0]["value"]["interpretation"].__setitem__("unseen_group_superpopulation_claimed", True),
        lambda r: r["field_closures"][0]["value"]["one_plan_bootstrap_law"].__setitem__("plan_count_chosen_recommended_defaulted_or_reported", 1000),
        lambda r: r["authority_and_scope"].__setitem__("third_zero_delta_precursor_permitted", True),
    ],
)
def test_fully_resigned_semantic_and_scope_mutants_fail(tmp_path, mutator):
    clone = _copy_bound_tree(tmp_path)
    record = _machine(clone)
    mutator(record)
    _write_resigned_machine(clone, record)
    with pytest.raises(M.ValidationError, match="package machine record"):
        M.validate(clone)


def test_stale_semantic_digest_fails_closed(tmp_path):
    clone = _copy_bound_tree(tmp_path)
    record = _machine(clone)
    record["state"] = "MUTANT"
    (clone / M.MACHINE_PATH).write_bytes(M.canonical_machine_bytes(record))
    with pytest.raises(M.ValidationError, match="semantic digest"):
        M.validate(clone)


def test_current_source_constant_change_breaks_machine_binding(tmp_path):
    clone = _copy_bound_tree(tmp_path)
    source_path = clone / M.VALIDATOR_PATH
    raw = source_path.read_bytes()
    assert b"FULL_CARTESIAN_PRODUCT" in raw
    source_path.write_bytes(raw.replace(b"FULL_CARTESIAN_PRODUCT", b"PAIRWISE_ZIP_ONLY_VALUE"))
    source_path.chmod(0o644)
    with pytest.raises(M.ValidationError, match="package machine record"):
        M.validate(clone)


def test_physionet_raw_binding_tamper_fails_closed(tmp_path):
    clone = _copy_bound_tree(tmp_path)
    path = clone / "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json"
    path.write_bytes(path.read_bytes() + b"mutant\n")
    path.chmod(0o644)
    with pytest.raises(M.ValidationError, match="predecessor exact-byte mismatch"):
        M.validate(clone)


def test_machine_self_binding_excludes_raw_self_hash():
    expected = M.expected_record(ROOT)
    assert expected["machine_self_binding"] == {
        "path": M.MACHINE_PATH,
        "semantic_self_digest_field": "record_sha256",
        "raw_self_hash_embedded": False,
    }
    assert len(expected["predecessor_bindings"]) == 35
    assert expected["predecessor_group_counts"]["total"] == 35
