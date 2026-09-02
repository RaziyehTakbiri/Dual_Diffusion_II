from __future__ import annotations

from copy import deepcopy
import ast
import json
from pathlib import Path

import pytest

from heterodiff.experiments import b08_wave2_capacity_preflight as preflight


ROOT = Path(__file__).resolve().parents[2]
MACHINE = ROOT / "research/fixtures/manuscript_v3_b08_wave2_capacity_preflight_v1.json"
SOURCE = ROOT / "src/heterodiff/experiments/b08_wave2_capacity_preflight.py"


def machine_record():
    return json.loads(MACHINE.read_text(encoding="ascii"))


def test_canonical_machine_record_is_exact():
    record = machine_record()
    assert record == preflight.build_machine_record()
    assert preflight.validate_machine_record(record) == record
    assert MACHINE.read_bytes() == preflight.canonical_json_bytes(record) + b"\n"


def test_capacity_arithmetic_is_exact_and_terminal_no_go():
    assert preflight.AVAILABLE_BLOCKS_1024 * 1024 == preflight.AVAILABLE_BYTES
    assert (
        preflight.DESTINATION_RESERVATION_BYTES
        + preflight.AUXILIARY_RESERVATION_BYTES
        == preflight.COMBINED_RESERVATION_BYTES
    )
    assert (
        preflight.COMBINED_RESERVATION_BYTES - preflight.AVAILABLE_BYTES
        == preflight.SHORTFALL_BYTES
    )
    assert preflight.AVAILABILITY_FRACTION.numerator == 799_155
    assert preflight.AVAILABILITY_FRACTION.denominator == 23_068_672
    assert preflight.AVAILABLE_BYTES < preflight.COMBINED_RESERVATION_BYTES


def test_exact_ten_field_residual_roster_and_zero_delta():
    record = machine_record()
    projection = record["supported_projection"]
    assert [row["field_id"] for row in projection["residual_gaps"]] == list(
        preflight.RESIDUAL_FIELD_IDS
    )
    assert len(projection["residual_gaps"]) == 10
    assert projection["project_effects"]["field_ids_closed_now"] == []
    assert projection["project_effects"]["tracker_or_evidence_ledger_edited"] is False
    assert projection["b08_gate"]["B08_close_permitted"] is False
    assert all(
        row["satisfied"] is False for row in projection["b08_gate"]["requirements"]
    )


def test_fresh_data_free_receipt_is_repeat_stable_but_nonpromoting():
    receipt = preflight.fresh_data_free_receipt()
    assert len(set(receipt["sha256_stream"]["output_sha256s"])) == 1
    assert len(set(receipt["matrix_product"]["output_sha256s"])) == 1
    assert receipt["synthetic_non_scientific"] is True
    assert receipt["data_or_entropy_used"] is False
    assert receipt["f104_calibration_weight_claimed"] is False
    assert receipt["production_capacity_or_ceiling_claimed"] is False
    body = dict(receipt)
    digest = body.pop("receipt_sha256")
    assert digest == preflight.sha256_json(body)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["supported_projection"]["capacity_arithmetic"].__setitem__(
            "available_bytes", preflight.COMBINED_RESERVATION_BYTES
        ),
        lambda r: r["supported_projection"]["capacity_arithmetic"].__setitem__(
            "capacity_pass", True
        ),
        lambda r: r["supported_projection"]["project_effects"][
            "field_ids_closed_now"
        ].append("F150"),
        lambda r: r["supported_projection"]["b08_gate"].__setitem__(
            "B08_close_permitted", True
        ),
        lambda r: r["supported_projection"]["residual_gaps"].pop(),
        lambda r: r.__setitem__("record_sha256", "0" * 64),
        lambda r: r.__setitem__("extra", False),
    ],
)
def test_hostile_record_mutations_fail(mutation):
    record = deepcopy(machine_record())
    mutation(record)
    with pytest.raises(ValueError):
        preflight.validate_machine_record(record)


def test_boolean_integer_aliases_fail():
    record = deepcopy(machine_record())
    record["supported_projection"]["capacity_arithmetic"]["available_bytes"] = True
    with pytest.raises(ValueError):
        preflight.validate_machine_record(record)


def test_source_has_no_effect_surface():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots.isdisjoint(
        {"socket", "subprocess", "requests", "urllib", "http", "secrets", "random"}
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called_names.isdisjoint({"open", "exec", "eval", "compile", "__import__"})
