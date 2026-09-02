"""Hostile qualification for the exact B06 closure package."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
from types import ModuleType

import pytest

from heterodiff.experiments import two_domain_baseline_registry as registry


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json"
)


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load(ROOT / VALIDATOR_REL, "b06_closure_validator")


def _record(validator: ModuleType) -> dict:
    return validator.strict_json((ROOT / MACHINE_REL).read_bytes())


def _copy_package(validator: ModuleType, target: Path) -> Path:
    relatives = list(validator.PACKAGE_ROSTER) + [
        row[0] for row in validator.PREDECESSOR_BINDINGS
    ]
    for relative in relatives:
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    return target


def _write_record(validator: ModuleType, root: Path, record: dict) -> None:
    record["record_sha256"] = validator.record_sha256(record)
    (root / MACHINE_REL).write_bytes(validator.canonical_machine_bytes(record))
    (root / MACHINE_REL).chmod(0o644)


def test_canonical_package_validates_exact_bounded_delta(
    validator: ModuleType,
) -> None:
    result = validator.validate(ROOT)
    assert result["validation"] == "PASS"
    assert result["fields_closed"] == list(validator.FIELD_IDS)
    assert result["pre_execution_fields_closed"] == 42
    assert result["blockers_closed"] == ["B06"]
    assert result["pre_execution_open_after"] == 34
    assert result["total_open_after"] == 35
    assert result["b08_closed"] is False
    assert result["b12_closed"] is False


def test_machine_is_canonical_self_bound_and_exact(validator: ModuleType) -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    record = validator.strict_json(raw)
    assert raw == validator.canonical_machine_bytes(record)
    assert record["record_sha256"] == validator.record_sha256(record)
    assert record == validator.expected_record(ROOT)
    assert record["registry"] == registry.FROZEN_REGISTRY
    assert record["registry_sha256"] == validator.registry_sha256(
        registry.FROZEN_REGISTRY
    )


def test_exact_42_field_projection_and_pointers(validator: ModuleType) -> None:
    closures = _record(validator)["field_closures"]
    assert len(closures) == 42
    assert tuple(row["field_id"] for row in closures) == validator.FIELD_IDS
    assert tuple(row["json_pointer"] for row in closures) == (
        validator.FIELD_POINTERS
    )
    assert {row["status"] for row in closures} == {
        "CLOSED_BY_B06_ADDITIVE_PREOUTCOME_FREEZE"
    }
    assert [row["value"] for row in closures] == validator._field_values(
        registry.FROZEN_REGISTRY
    )


def test_count_blocker_gate_and_timetable_transitions_are_exact(
    validator: ModuleType,
) -> None:
    record = _record(validator)
    assert record["field_delta"] == {
        "field_ids": list(validator.FIELD_IDS),
        "pre_execution": 42,
        "post_execution": 0,
        "total": 42,
        "blockers_closed": 1,
        "blocker_ids": ["B06"],
    }
    assert record["additive_count_transition"]["before"] == {
        "pre_execution_open": 76,
        "pre_execution_closed": 90,
        "post_execution_open": 1,
        "post_execution_closed": 5,
        "total_open": 77,
        "total_closed": 95,
    }
    assert record["additive_count_transition"]["after"] == {
        "pre_execution_open": 34,
        "pre_execution_closed": 132,
        "post_execution_open": 1,
        "post_execution_closed": 5,
        "total_open": 35,
        "total_closed": 137,
    }
    assert record["blocker_transition"]["before"] == {
        "open": 8,
        "closed": 4,
        "execution_open": 6,
    }
    assert record["blocker_transition"]["after"] == {
        "open": 7,
        "closed": 5,
        "execution_open": 5,
    }
    assert record["gate_a_transition"] == {"before": "4/8", "after": "5/8"}
    assert record["timetable_transition"]["before"] == {
        "checked": 51,
        "open": 108,
        "total": 159,
    }
    assert record["timetable_transition"]["after"] == {
        "checked": 54,
        "open": 105,
        "total": 159,
    }


def test_external_license_receipts_reproduce_exact_upstream_bytes(
    validator: ModuleType,
) -> None:
    receipts = _record(validator)["external_license_receipts"]
    assert [row["method_id"] for row in receipts] == [
        "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1",
        "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1",
    ]
    for receipt, expected_hash, expected_bytes in (
        (receipts[0], registry.CSDI_LICENSE_SHA256, registry.CSDI_LICENSE_BYTES),
        (
            receipts[1],
            registry.EDITPP_LICENSE_SHA256,
            registry.EDITPP_LICENSE_BYTES,
        ),
    ):
        binding = receipt["receipt_binding"]
        raw = (ROOT / binding["path"]).read_bytes()
        assert receipt["spdx"] == "MIT"
        assert binding["bytes"] == expected_bytes == len(raw)
        assert binding["raw_sha256"] == expected_hash
        assert hashlib.sha256(raw).hexdigest() == expected_hash


def test_every_package_and_predecessor_binding_recomputes(
    validator: ModuleType,
) -> None:
    record = _record(validator)
    assert record["package_file_roster"] == list(validator.PACKAGE_ROSTER)
    bindings = record["package_bindings_excluding_machine_self"]
    assert [(row["path"], row["role"]) for row in bindings] == list(
        validator.PACKAGE_BINDING_ROLES
    )
    for row in bindings + record["accepted_predecessor_bindings"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["raw_sha256"]
        assert row["mode_octal"] == "0644"
        assert row["nlink"] == 1
        assert row["terminal_lf"] is True


def test_external_selection_is_bounded_and_b08_b12_remain_open(
    validator: ModuleType,
) -> None:
    record = _record(validator)
    audit = record["registry"]["external_selection_audit"]
    assert audit["selection_rule_id"].startswith(
        "B06-STRONGEST-ELIGIBLE-WITHIN-FROZEN-AUDIT-ROSTER"
    )
    assert audit["universal_state_of_the_art_claimed"] is False
    boundary = record["qualification_boundary"]
    assert boundary["bounded_external_selection_not_universal_sota"] is True
    assert boundary["actual_external_or_family_execution_owned_by_B12"] is True
    assert boundary["hardware_weights_capacity_and_reservations_owned_by_B08"] is True
    assert record["remaining_open_requirements"]["B08"]
    assert record["remaining_open_requirements"]["B12"]


def test_all_execution_science_and_promotion_nonclaims_remain_false(
    validator: ModuleType,
) -> None:
    nonclaims = _record(validator)["project_effects_and_nonclaims"]
    assert nonclaims[
        "external_repository_cloned_only_for_read_only_identity_license_and_config_audit"
    ] is True
    assert nonclaims[
        "tracker_or_evidence_ledger_edited_by_package_construction"
    ] is False
    for key, value in nonclaims.items():
        if key.endswith("audit") or key.endswith("construction"):
            continue
        assert value is False, key


def test_three_production_surfaces_are_static_and_nonexecuting() -> None:
    forbidden_imports = {
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "random",
        "secrets",
        "numpy",
        "scipy",
        "torch",
        "jax",
    }
    for relative in (
        "src/heterodiff/experiments/matched_total_compute.py",
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
        "src/heterodiff/experiments/two_domain_baseline_adapter_contract.py",
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        imported = set()
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                calls.append(node.func)
        assert imported.isdisjoint(forbidden_imports)
        assert not any(
            isinstance(call, ast.Name) and call.id in {"open", "exec", "eval"}
            for call in calls
        )


@pytest.mark.parametrize(
    ("section", "path", "value"),
    [
        ("field", ("field_closures", 0, "value"), "alien"),
        ("count", ("field_delta", "total"), 41),
        ("blocker", ("blocker_transition", "closed_now"), []),
        ("sota", ("registry", "external_selection_audit", "universal_state_of_the_art_claimed"), True),
        ("b08", ("project_effects_and_nonclaims", "b08_closed"), True),
        ("b12", ("project_effects_and_nonclaims", "b12_closed"), True),
        ("science", ("project_effects_and_nonclaims", "scientific_entropy_training_inference_or_result_inspection_performed"), True),
    ],
)
def test_coherent_machine_mutations_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
    section: str,
    path: tuple,
    value: object,
) -> None:
    root = _copy_package(validator, tmp_path / section)
    record = copy.deepcopy(_record(validator))
    target = record
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = value
    _write_record(validator, root, record)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize(
    "relative",
    [
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
        "src/heterodiff/experiments/two_domain_baseline_adapter_contract.py",
        "src/heterodiff/experiments/matched_total_compute.py",
        "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md",
        "research/fixtures/b06_upstream_receipts/csdi_7f24a436_LICENSE",
        "research/fixtures/b06_upstream_receipts/editpp_3113d2ee_LICENSE",
    ],
)
def test_every_material_source_or_receipt_mutation_fails_closed(
    validator: ModuleType, tmp_path: Path, relative: str
) -> None:
    root = _copy_package(validator, tmp_path / hashlib.sha256(relative.encode()).hexdigest())
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_noncanonical_duplicate_and_float_machine_json_fail_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    for name, raw in (
        ("noncanonical", b'{"x": 1}\n'),
        ("duplicate", b'{"x":1,"x":1}\n'),
        ("float", b'{"x":1.0}\n'),
    ):
        root = _copy_package(validator, tmp_path / name)
        (root / MACHINE_REL).write_bytes(raw)
        (root / MACHINE_REL).chmod(0o644)
        with pytest.raises(validator.ValidationError):
            validator.validate(root)


def test_root_symlink_machine_hardlink_and_mode_substitution_fail_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_package(validator, tmp_path / "real")
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(validator.ValidationError):
        validator.validate(alias)

    hard_root = _copy_package(validator, tmp_path / "hard")
    machine = hard_root / MACHINE_REL
    sibling = hard_root / "machine-sibling.json"
    machine.rename(sibling)
    os.link(sibling, machine)
    with pytest.raises(validator.ValidationError):
        validator.validate(hard_root)

    mode_root = _copy_package(validator, tmp_path / "mode")
    (mode_root / validator.REGISTRY_SOURCE_PATH).chmod(0o600)
    with pytest.raises(validator.ValidationError):
        validator.validate(mode_root)
