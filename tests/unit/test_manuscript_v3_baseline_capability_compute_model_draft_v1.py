"""Hostile tests for the static baseline/capability/compute-model draft.

Canonical inputs are read only.  All mutations use pytest temporary replicas.
No test contacts a repository or license source, accesses data, or runs science.
"""

from __future__ import annotations

import ast
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, List

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/manuscript_v3_baseline_capability_compute_model_draft_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_baseline_capability_compute_model_draft_v1.json"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "baseline_capability_compute_model_validator", ROOT / VALIDATOR_REL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _closed_roster(module: ModuleType) -> List[str]:
    return [
        module.HUMAN_PATH,
        module.MACHINE_PATH,
        module.VALIDATOR_PATH,
        module.TEST_PATH,
        *[path for _, path in module.EVIDENCE_SPECS],
    ]


def _copy_closed_roster(module: ModuleType, target: Path) -> Path:
    for relative in _closed_roster(module):
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    return target


def _read_record(root: Path) -> Dict[str, Any]:
    return json.loads((root / MACHINE_REL).read_text(encoding="ascii"))


def _write_record(
    module: ModuleType,
    root: Path,
    record: Dict[str, Any],
    *,
    recompute_digest: bool = True,
) -> None:
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    (root / MACHINE_REL).write_text(
        json.dumps(record, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="ascii",
    )


def _mutate_record(
    module: ModuleType,
    root: Path,
    mutation: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
) -> None:
    record = _read_record(root)
    mutation(record)
    _write_record(module, root, record, recompute_digest=recompute_digest)


def _replace(record: Dict[str, Any], pointer: str, value: Any) -> None:
    current: Any = record
    tokens = pointer.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def _refresh_binding(
    module: ModuleType,
    root: Path,
    record: Dict[str, Any],
    section: str,
    relative_path: str,
) -> None:
    raw = (root / relative_path).read_bytes()
    for row in record[section]:
        if row["path"] == relative_path:
            row["bytes"] = len(raw)
            row["raw_sha256"] = hashlib.sha256(raw).hexdigest()
            row["terminal_lf"] = raw.endswith(b"\n")
            return
    raise AssertionError("binding not found")


def _zero_counts(module: ModuleType) -> Dict[str, Dict[str, int]]:
    return {
        phase: {event: 0 for event in module.RESOURCE_EVENTS}
        for phase in module.PHASES
    }


def _unit_weights(module: ModuleType) -> Dict[str, Fraction]:
    return {event: Fraction(1, 1) for event in module.RESOURCE_EVENTS}


def test_canonical_package_validates_without_closing_b06_or_b08(
    validator: ModuleType,
) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "BASELINE_FAMILIES_LICENSE_CAPABILITY_AND_COMPUTE_MODEL_DRAFT_VALIDATED"
        ),
        "control_predicate_value": True,
        "draft_complete": True,
        "primary_pair_count": 2,
        "local_control_count": 4,
        "comparator_family_count": 4,
        "family_domain_row_count": 8,
        "external_domain_baseline_count": 2,
        "synthetic_exact_total_cost": 85,
        "B06_open": True,
        "B08_open": True,
        "dependency_open_field_count": 56,
        "scientific_effect": 0,
        "validation": "PASS",
    }


def test_synthetic_exact_cost_has_expected_phase_decomposition(
    validator: ModuleType,
) -> None:
    observed = validator.exact_compute_cost(
        validator.SYNTHETIC_COUNTS, validator.SYNTHETIC_WEIGHTS
    )
    assert observed == {
        "calculator_id": "EXACT_WEIGHTED_RESOURCE_LEDGER_V1",
        "phase_costs": {
            "PILOT": {"numerator": 4, "denominator": 1},
            "TUNING": {"numerator": 20, "denominator": 1},
            "FINAL_TRAINING": {"numerator": 31, "denominator": 1},
            "CONFIRMATORY_INFERENCE": {"numerator": 30, "denominator": 1},
        },
        "total_cost": {"numerator": 85, "denominator": 1},
        "binary_float_used": False,
    }


def test_fractional_exact_cost_is_not_rounded(validator: ModuleType) -> None:
    counts = _zero_counts(validator)
    weights = _unit_weights(validator)
    counts["PILOT"]["BASE_FORWARD"] = 1
    counts["TUNING"]["GUIDE_EVALUATION"] = 3
    weights["BASE_FORWARD"] = Fraction(1, 3)
    weights["GUIDE_EVALUATION"] = Fraction(2, 7)
    result = validator.exact_compute_cost(counts, weights)
    assert result["phase_costs"]["PILOT"] == {"numerator": 1, "denominator": 3}
    assert result["phase_costs"]["TUNING"] == {"numerator": 6, "denominator": 7}
    assert result["total_cost"] == {"numerator": 25, "denominator": 21}


def test_zero_counts_are_valid_but_weights_remain_positive(
    validator: ModuleType,
) -> None:
    result = validator.exact_compute_cost(
        _zero_counts(validator), _unit_weights(validator)
    )
    assert result["total_cost"] == {"numerator": 0, "denominator": 1}


def test_exact_cost_result_contains_no_float(validator: ModuleType) -> None:
    result = validator.exact_compute_cost(
        validator.SYNTHETIC_COUNTS, validator.SYNTHETIC_WEIGHTS
    )

    def inspect(value: Any) -> None:
        assert type(value) is not float
        if type(value) is dict:
            for child in value.values():
                inspect(child)
        elif type(value) is list:
            for child in value:
                inspect(child)

    inspect(result)


@pytest.mark.parametrize("bad", [True, 1.0, Fraction(1, 2), "1", None, -1])
def test_invalid_count_types_or_values_are_refused(
    validator: ModuleType, bad: Any
) -> None:
    counts = _zero_counts(validator)
    counts["PILOT"]["BASE_FORWARD"] = bad
    with pytest.raises(validator.ValidationError):
        validator.exact_compute_cost(counts, _unit_weights(validator))


@pytest.mark.parametrize(
    "bad",
    [True, 1.0, "1", None, 0, -1, Fraction(0, 1), Fraction(-1, 2)],
)
def test_invalid_weight_types_or_values_are_refused(
    validator: ModuleType, bad: Any
) -> None:
    weights = _unit_weights(validator)
    weights["BASE_FORWARD"] = bad
    with pytest.raises(validator.ValidationError):
        validator.exact_compute_cost(_zero_counts(validator), weights)


def test_normalized_component_bit_bound_is_inclusive(
    validator: ModuleType,
) -> None:
    boundary = 1 << (validator.MAX_RATIONAL_COMPONENT_BITS - 1)
    weights = _unit_weights(validator)
    weights["BASE_FORWARD"] = Fraction(boundary, 1)
    result = validator.exact_compute_cost(_zero_counts(validator), weights)
    assert result["total_cost"] == {"numerator": 0, "denominator": 1}
    weights["BASE_FORWARD"] = Fraction(1 << validator.MAX_RATIONAL_COMPONENT_BITS, 1)
    with pytest.raises(validator.ValidationError, match="component bit bound"):
        validator.exact_compute_cost(_zero_counts(validator), weights)


def test_count_bit_bound_is_enforced(validator: ModuleType) -> None:
    counts = _zero_counts(validator)
    counts["PILOT"]["BASE_FORWARD"] = 1 << validator.MAX_RATIONAL_COMPONENT_BITS
    with pytest.raises(validator.ValidationError, match="count bit bound"):
        validator.exact_compute_cost(counts, _unit_weights(validator))


@pytest.mark.parametrize("target", ["phase_missing", "phase_extra", "phase_reordered"])
def test_exact_phase_roster_and_order_are_enforced(
    validator: ModuleType, target: str
) -> None:
    counts = _zero_counts(validator)
    if target == "phase_missing":
        counts.pop("PILOT")
    elif target == "phase_extra":
        counts["EXTRA"] = {event: 0 for event in validator.RESOURCE_EVENTS}
    else:
        counts = {phase: counts[phase] for phase in reversed(validator.PHASES)}
    with pytest.raises(validator.ValidationError, match="phase key roster"):
        validator.exact_compute_cost(counts, _unit_weights(validator))


@pytest.mark.parametrize("target", ["count_missing", "count_extra", "weight_missing", "weight_extra"])
def test_exact_resource_rosters_are_enforced(
    validator: ModuleType, target: str
) -> None:
    counts = _zero_counts(validator)
    weights = _unit_weights(validator)
    if target == "count_missing":
        counts["PILOT"].pop("BASE_FORWARD")
    elif target == "count_extra":
        counts["PILOT"]["EXTRA"] = 0
    elif target == "weight_missing":
        weights.pop("BASE_FORWARD")
    else:
        weights["EXTRA"] = Fraction(1, 1)
    with pytest.raises(validator.ValidationError, match="key roster"):
        validator.exact_compute_cost(counts, weights)


def test_method_control_family_and_domain_rosters_are_exact(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    assert tuple(row["method_id"] for row in record["primary_pair"]) == validator.PRIMARY_METHOD_IDS
    assert tuple(
        row["control_id"] for row in record["local_interpretation_controls"]
    ) == validator.CONTROL_IDS
    assert tuple(
        row["comparator_family_id"]
        for row in record["literature_comparator_families"]
    ) == validator.COMPARATOR_FAMILY_IDS
    assert tuple(row["domain_id"] for row in record["external_domain_baselines"]) == validator.DOMAIN_IDS


def test_local_controls_cannot_silently_discharge_external_families(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    controls = record["local_interpretation_controls"]
    families = record["literature_comparator_families"]
    assert all(row["row_kind"] == "LOCAL_INTERPRETATION_CONTROL" for row in controls)
    assert all(
        row["may_discharge_external_family_row_without_equivalence_proof"] is False
        for row in controls
    )
    assert all(row["row_kind"] == "EXTERNAL_LITERATURE_FAMILY" for row in families)


def test_every_external_receipt_and_capability_stays_unpopulated(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    for row in record["external_domain_baselines"]:
        assert all(value is None for value in row["future_receipts"].values())
        assert set(row["capability_matrix"].values()) == {"UNKNOWN"}
        assert row["admitted"] is False
    for family in record["literature_comparator_families"]:
        for row in family["domain_rows"]:
            assert row["implementation_receipt"] is None
            assert row["inapplicability_or_equivalence_justification"] is None
            assert set(row["capability_matrix"].values()) == {"UNKNOWN"}
            assert row["admitted"] is False


def test_all_56_dependency_fields_remain_null(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    fields = record["nonclosure"]["open_field_values"]
    assert tuple(fields) == validator.OPEN_FIELD_IDS
    assert len(fields) == 56
    assert all(value is None for value in fields.values())
    assert record["nonclosure"]["blocker_status"] == {"B06": "OPEN", "B08": "OPEN"}


def test_validator_has_no_network_process_project_or_writer_imports() -> None:
    source = (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert not imported & {
        "socket",
        "urllib",
        "requests",
        "httpx",
        "subprocess",
        "random",
        "secrets",
        "numpy",
        "torch",
        "heterodiff",
    }
    assert not called & {
        "write_text",
        "write_bytes",
        "unlink",
        "remove",
        "rename",
        "replace",
        "mkdir",
        "makedirs",
        "system",
        "run",
        "Popen",
    }
    assert "os.O_RDONLY" in source


def test_validation_is_read_only_for_closed_roster(validator: ModuleType) -> None:
    before = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in _closed_roster(validator)
    }
    validator.validate()
    after = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in _closed_roster(validator)
    }
    assert after == before


@pytest.mark.parametrize(
    "pointer,value",
    [
        ("authority_provenance.external_repository_license_or_paper_lookup_authorized", True),
        ("draft_identity.baseline_matrix_populated", True),
        ("draft_identity.compute_capacity_selected_or_reserved", True),
        ("draft_identity.B06_closed", True),
        ("draft_identity.scientific_effect", 1),
        ("local_interpretation_controls.0.may_discharge_external_family_row_without_equivalence_proof", True),
        ("literature_comparator_families.0.domain_rows.0.admitted", True),
        ("external_domain_baselines.0.future_receipts.license", "guessed"),
        ("external_domain_baselines.0.capability_matrix.DOMAIN_PHYSICAL_TIME", "NATIVE"),
        ("license_receipt_contract.current_external_receipts_observed", 1),
        ("capability_contract.unknown_blocks_admission", False),
        ("matched_compute_contract.hardware_calibration_weights_populated", True),
        ("matched_compute_contract.hardware_or_environment_selected", True),
        ("matched_compute_contract.unused_budget_transfer_or_postresult_topup_permitted", True),
        ("matched_compute_contract.real_compute_budget_or_capacity_claimed", True),
        ("nonclosure.open_field_values.F104", "draft formula promoted"),
        ("nonclosure.blocker_status.B06", "CLOSED"),
        ("nonclosure.unresolved_fields_closed", 1),
        ("scope_and_nonclaims.external_current_fact_verified", True),
        ("scope_and_nonclaims.tracker_edited_by_package", True),
    ],
)
def test_overclaims_fail_even_after_self_redigest(
    validator: ModuleType,
    tmp_path: Path,
    pointer: str,
    value: Any,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _mutate_record(validator, root, lambda record: _replace(record, pointer, value))
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_record_tamper_without_redigest_fails(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _mutate_record(
        validator,
        root,
        lambda record: _replace(record, "draft_identity.draft_complete", False),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError, match="self-digest"):
        validator.validate(root)


def test_package_and_evidence_binding_tamper_fail(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _mutate_record(
        validator,
        root,
        lambda record: _replace(record, "package_bindings.0.raw_sha256", "0" * 64),
    )
    with pytest.raises(validator.ValidationError, match="package bindings"):
        validator.validate(root)
    root = _copy_closed_roster(validator, tmp_path / "second")
    _mutate_record(
        validator,
        root,
        lambda record: _replace(record, "evidence_bindings.0.bytes", 1),
    )
    with pytest.raises(validator.ValidationError, match="evidence bindings"):
        validator.validate(root)


def test_populated_prereg_baseline_field_fails_with_refreshed_binding(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / validator.PREREG_MACHINE_PATH
    prereg = json.loads(path.read_text(encoding="ascii"))
    prereg["method_and_baseline_plan"]["external_domain_baselines"][0]["license"] = "guess"
    path.write_text(json.dumps(prereg, sort_keys=True) + "\n", encoding="ascii")
    record = _read_record(root)
    _refresh_binding(validator, root, record, "evidence_bindings", validator.PREREG_MACHINE_PATH)
    _write_record(validator, root, record)
    with pytest.raises(validator.ValidationError, match="receipt no longer open"):
        validator.validate(root)


def test_populated_prereg_compute_field_fails_with_refreshed_binding(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / validator.PREREG_MACHINE_PATH
    prereg = json.loads(path.read_text(encoding="ascii"))
    prereg["compute_and_fairness_plan"]["hardware"] = "unreviewed"
    path.write_text(json.dumps(prereg, sort_keys=True) + "\n", encoding="ascii")
    record = _read_record(root)
    _refresh_binding(validator, root, record, "evidence_bindings", validator.PREREG_MACHINE_PATH)
    _write_record(validator, root, record)
    with pytest.raises(validator.ValidationError, match="compute field no longer open"):
        validator.validate(root)


def test_power_route_compute_claim_fails_with_refreshed_binding(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / validator.POWER_MACHINE_PATH
    power = json.loads(path.read_text(encoding="ascii"))
    power["route_identity"]["compute_budget_selected"] = True
    path.write_text(json.dumps(power, sort_keys=True) + "\n", encoding="ascii")
    record = _read_record(root)
    _refresh_binding(validator, root, record, "evidence_bindings", validator.POWER_MACHINE_PATH)
    _write_record(validator, root, record)
    with pytest.raises(validator.ValidationError, match="power-route compute"):
        validator.validate(root)


def test_duplicate_json_key_is_refused(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / MACHINE_REL
    raw = path.read_text(encoding="ascii")
    path.write_text('{"schema_version":"duplicate",' + raw[1:], encoding="ascii")
    with pytest.raises(validator.ValidationError, match="invalid strict JSON"):
        validator.validate(root)


def test_machine_symlink_and_hardlink_are_refused(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path / "symlink")
    path = root / MACHINE_REL
    saved = path.with_suffix(".saved")
    path.rename(saved)
    path.symlink_to(saved.name)
    with pytest.raises(validator.ValidationError, match="regular non-symlink"):
        validator.validate(root)
    root = _copy_closed_roster(validator, tmp_path / "hardlink")
    path = root / MACHINE_REL
    os.link(path, path.with_suffix(".hardlink"))
    with pytest.raises(validator.ValidationError, match="hard link"):
        validator.validate(root)
