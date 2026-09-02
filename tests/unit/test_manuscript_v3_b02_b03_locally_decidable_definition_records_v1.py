"""Qualification and hostile tests for the locally decidable records."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from heterodiff.data import two_domain_precontact_definition_records as records

ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC = ROOT / (
    "research/diagnostics/"
    "manuscript_v3_b02_b03_locally_decidable_definition_records_v1.py"
)
SPEC = importlib.util.spec_from_file_location("definition_record_validator", DIAGNOSTIC)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def test_exact_three_domain_separated_records_recompute() -> None:
    values = records.definition_records()
    assert tuple(name for name, _, _ in values) == (
        "held_out_material_definition", "final_opening_rule", "append_only_log_schema",
    )
    assert len({digest for _, _, digest in values}) == 3
    for name, record, digest in values:
        assert records.record_sha256(name, record) == digest


def test_active_split_lineage_and_no_material_claim() -> None:
    held = records.held_out_material_definition()
    assert held["material_or_manifest_claimed_present"] is False
    assert held["domain_split_lineage"] == [
        {"domain_id": "physionet-challenge-2012",
         "split_contract_id": records.PHYSIONET_SPLIT_CONTRACT_ID,
         "split_contract_sha256": records.PHYSIONET_SPLIT_CONTRACT_SHA256},
        {"domain_id": "online-retail-ii",
         "split_contract_id": records.RETAIL_SPLIT_CONTRACT_ID,
         "split_contract_sha256": records.RETAIL_SPLIT_CONTRACT_SHA256},
    ]


def test_every_semantic_mutation_changes_digest() -> None:
    for name, record, digest in records.definition_records():
        mutated = copy.deepcopy(record)
        first = next(iter(mutated))
        mutated[first] = "FOREIGN"
        assert records.record_sha256(name, mutated) != digest


def test_exact_types_and_unknown_domains_rejected() -> None:
    with pytest.raises(TypeError):
        records.record_sha256("held_out_material_definition", [])
    with pytest.raises(TypeError):
        records.record_sha256("unknown", {})
    class Dict(dict):
        pass
    with pytest.raises(TypeError):
        records.record_sha256("held_out_material_definition", Dict())


def test_all_blocked_and_operational_state_remains_empty() -> None:
    state = records.unresolved_operational_state()
    assert len(state["blocked_non_f061_slots"]) == 8
    assert all(value is None for value in state["blocked_non_f061_slots"].values())
    assert state[records.SEPARATELY_BLOCKED_SLOT] is None
    assert state["owner_principals"] == [None] * 9
    assert state["owner_acceptance_sha256s"] == [None] * 9
    assert all(value == 0 and type(value) is int for value in state["budgets"].values())
    assert all(
        value == 0 and type(value) is int
        for value in state["closures"].values()
    )
    for key in ("authority", "network_or_contact", "data_opened",
                "escrow_activated", "scientific_execution"):
        assert state[key] is False


def test_read_only_validator_passes_exact_package() -> None:
    assert validator.validate(ROOT) == {
        "decision": "PASS_OFFLINE_DEFINITIONS_ONLY", "definition_count": 3,
        "operational_authority_present": False, "independent_review_present": False,
    }


def _copy_package(tmp_path: Path) -> Path:
    fixture = json.loads((ROOT / validator.FIXTURE).read_text(encoding="ascii"))
    paths = [validator.FIXTURE] + [Path(item["path"]) for item in fixture["bindings"]]
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
        target.chmod(0o644)
    return tmp_path / validator.FIXTURE


@pytest.mark.parametrize("field,value", [
    ("authority", True),
    ("independent_review_receipt_sha256", "1" * 64),
    ("conflict_of_interest_determination_sha256", "2" * 64),
])
def test_hostile_state_population_rejected(tmp_path: Path, field: str, value) -> None:
    fixture_path = _copy_package(tmp_path)
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))
    fixture[field] = value
    fixture_path.write_text(json.dumps(fixture), encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(tmp_path)


@pytest.mark.parametrize("surface", ["budgets", "closures"])
def test_boolean_cannot_alias_nested_integer_zero(
    tmp_path: Path, surface: str,
) -> None:
    fixture_path = _copy_package(tmp_path)
    raw = fixture_path.read_text(encoding="ascii")
    fixture = json.loads(raw)
    first = next(iter(fixture[surface]))
    fixture[surface][first] = False
    fixture_path.write_text(json.dumps(fixture), encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(tmp_path)


@pytest.mark.parametrize("roster", ["bindings", "definition_records"])
def test_boolean_cannot_alias_roster_ordinal(
    tmp_path: Path, roster: str,
) -> None:
    fixture_path = _copy_package(tmp_path)
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))
    fixture[roster][0]["ordinal"] = False
    fixture_path.write_text(json.dumps(fixture), encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(tmp_path)


def test_log_schema_freezes_immutable_event_and_head_protocol() -> None:
    schema = records.append_only_log_schema()
    names = [item["name"] for item in schema["entry_schema"]]
    assert "event_kind" in names and "intent_entry_sha256" in names
    assert schema["head_storage_layout"] == "heads/{ordinal:020d}.json"
    assert "O_CREAT_O_EXCL_MODE_0600" in schema["head_update_rule"]
    assert schema["entry_digest_domain_is_nul_terminated"] is True
    label = schema["entry_digest_domain_display_label"].encode("ascii") + b"\0"
    assert label.hex() == schema["entry_digest_domain_hex"]


def test_hostile_outcome_start_time_mismatch_rejected() -> None:
    schema = records.append_only_log_schema()
    assert schema["outcome_start_time_binding_rule"] == (
        "OUTCOME_OPERATION_STARTED_TIME_EXACTLY_EQUALS_BOUND_INTENT_"
        "OPERATION_STARTED_TIME"
    )
    intent_start = "2026-09-01T00:00:00.000000000Z"
    assert records.outcome_start_time_matches_bound_intent(
        intent_start, intent_start
    ) is True
    assert records.outcome_start_time_matches_bound_intent(
        intent_start, "2026-09-01T00:00:00.000000001Z"
    ) is False
    assert records.outcome_start_time_matches_bound_intent(
        intent_start, None
    ) is False


def test_duplicate_json_key_rejected(tmp_path: Path) -> None:
    fixture_path = _copy_package(tmp_path)
    raw = fixture_path.read_text(encoding="ascii")
    duplicate = raw.replace(
        '{\n  "schema_version":',
        '{\n  "authority": false,\n  "schema_version":',
        1,
    )
    fixture_path.write_text(duplicate, encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="duplicate JSON key"):
        validator.validate(tmp_path)


def test_absolute_or_alternate_fixture_path_rejected() -> None:
    with pytest.raises(validator.ValidationError, match="fixture path"):
        validator.validate(ROOT, ROOT / validator.FIXTURE)


def test_hostile_binding_path_and_digest_rejected(tmp_path: Path) -> None:
    fixture_path = _copy_package(tmp_path)
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))
    fixture["bindings"][0]["path"] = "../outside"
    fixture_path.write_text(json.dumps(fixture), encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(tmp_path)


@pytest.mark.parametrize(
    ("surface", "value"),
    [("state", "OPERATIONAL"), ("binding_role", "foreign-role")],
)
def test_hostile_state_or_binding_role_rejected(
    tmp_path: Path, surface: str, value: str,
) -> None:
    fixture_path = _copy_package(tmp_path)
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))
    if surface == "state":
        fixture["state"] = value
    else:
        fixture["bindings"][0]["role"] = value
    fixture_path.write_text(json.dumps(fixture), encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(tmp_path)


def test_hostile_binding_custody_rejected(tmp_path: Path) -> None:
    fixture_path = _copy_package(tmp_path)
    fixture = json.loads(fixture_path.read_text(encoding="ascii"))
    bound = tmp_path / fixture["bindings"][0]["path"]
    bound.chmod(0o600)
    with pytest.raises(validator.ValidationError, match="0644"):
        validator.validate(tmp_path)


def test_symlinked_binding_ancestor_rejected(tmp_path: Path) -> None:
    _copy_package(tmp_path)
    source_dir = tmp_path / "src"
    real_dir = tmp_path / "real-src"
    source_dir.rename(real_dir)
    source_dir.symlink_to(real_dir, target_is_directory=True)
    with pytest.raises((validator.ValidationError, OSError)):
        validator.validate(tmp_path)


def test_no_io_network_or_execution_imports_in_definition_module() -> None:
    text = (
        ROOT / "src/heterodiff/data/two_domain_precontact_definition_records.py"
    ).read_text()
    for forbidden in ("import os", "socket", "subprocess", "requests", "urllib"):
        assert forbidden not in text
