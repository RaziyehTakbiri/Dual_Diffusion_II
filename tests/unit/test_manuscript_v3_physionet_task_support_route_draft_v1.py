"""Hostile tests for the static PhysioNet task/support-route draft.

All mutation is confined to pytest temporary directories.  The canonical
package, predecessors, and science sources are read only.  The suite performs
no network, source contact, data access, or scientific execution.
"""

from __future__ import annotations

import ast
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
    "research/diagnostics/manuscript_v3_physionet_task_support_route_draft_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_physionet_task_support_route_draft_v1.json"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "physionet_task_support_route_validator", ROOT / VALIDATOR_REL
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


def test_canonical_package_validates_with_zero_scientific_effect(
    validator: ModuleType,
) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": "PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT_VALIDATED",
        "control_predicate_value": True,
        "draft_complete": True,
        "B02_open": True,
        "B09_open": True,
        "dependency_open_field_count": 23,
        "patient_split_seam_open": True,
        "domain_admitted": False,
        "scientific_effect": 0,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


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


def test_authority_text_hash_and_normalization_are_exact(
    validator: ModuleType,
) -> None:
    assert len(validator.NORMALIZED_AUTHORITY_TEXT.encode("utf-8")) == 92
    assert (
        hashlib.sha256(validator.NORMALIZED_AUTHORITY_TEXT.encode("utf-8")).hexdigest()
        == validator.AUTHORITY_TEXT_SHA256
    )
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    assert record["authority_provenance"] == validator.EXPECTED_AUTHORITY


def test_exact_open_field_roster_remains_null(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    values = record["nonclosure"]["open_field_values"]
    assert tuple(values) == validator.OPEN_FIELD_IDS
    assert len(values) == 23
    assert all(value is None for value in values.values())
    assert set(record["nonclosure"]["blocker_status"]) == {"B02", "B09"}


def test_split_algorithm_is_explicitly_out_of_scope(validator: ModuleType) -> None:
    seam = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))[
        "split_package_seam"
    ]
    assert seam["split_design_implemented_by_this_package"] is False
    assert seam["patient_hash_domain_selected_by_this_package"] is False
    assert seam["canonical_patient_id_encoding_selected_by_this_package"] is False
    assert seam["collision_rule_selected_by_this_package"] is False
    assert seam["allocation_selected_by_this_package"] is False
    assert seam["separate_split_package_must_be_consumed_before_population"] is True


def test_bound_sources_are_parsed_as_inert_ast_receipts(
    validator: ModuleType,
) -> None:
    for path, required in validator.EXPECTED_SOURCE_SYMBOLS.items():
        symbols = validator._defined_top_level_symbols((ROOT / path).read_bytes(), path)
        assert required <= symbols


def test_validator_has_no_risky_imports_or_writers() -> None:
    tree = ast.parse((ROOT / VALIDATOR_REL).read_text(encoding="utf-8"))
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
    # ``os.open`` is the validator's descriptor-level, read-only stable reader.
    assert "os.O_RDONLY" in (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "pointer,value",
    [
        ("authority_provenance.external_contact_or_browsing_authorized", True),
        ("authority_provenance.data_access_or_opening_authorized", True),
        ("draft_identity.domain_admitted", True),
        ("draft_identity.scientific_effect", 1),
        ("representation_route.missing_value_imputation_permitted", True),
        ("representation_route.event_vocabulary_support_units_sentinels_and_type_ids_populated", True),
        ("population_pipeline.row_or_patient_quarantine_exclusion_resplit_or_postoutcome_repair_permitted", True),
        ("common_support_route.noise_or_clipping_for_theorem_convenience_permitted", True),
        ("common_support_route.common_support_proved_for_physionet", True),
        ("admission_route.statistic_selected", True),
        ("admission_route.threshold_selected", True),
        ("admission_route.validation_or_test_feedback_permitted", True),
        ("split_package_seam.split_design_implemented_by_this_package", True),
        ("split_package_seam.patient_hash_domain_selected_by_this_package", True),
        ("nonclosure.open_field_values.F023", "invented endpoint"),
        ("nonclosure.blocker_status.B02", "CLOSED"),
        ("nonclosure.unresolved_fields_closed", 1),
        ("scope_and_nonclaims.data_acquired_opened_parsed_inventoried_or_split", True),
        ("scope_and_nonclaims.tracker_edited_by_package", True),
    ],
)
def test_semantic_overclaims_fail_even_after_self_redigest(
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


def test_package_binding_tamper_fails_after_redigest(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _mutate_record(
        validator,
        root,
        lambda record: _replace(record, "package_bindings.0.bytes", 1),
    )
    with pytest.raises(validator.ValidationError, match="package bindings"):
        validator.validate(root)


def test_evidence_binding_tamper_fails_after_redigest(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _mutate_record(
        validator,
        root,
        lambda record: _replace(record, "evidence_bindings.0.raw_sha256", "0" * 64),
    )
    with pytest.raises(validator.ValidationError, match="evidence bindings"):
        validator.validate(root)


def test_missing_bound_source_symbol_fails_even_with_refreshed_binding(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / validator.RAW_SOURCE_PATH
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        "def parse_physionet_2012_record(", "def removed_parse_physionet_2012_record("
    )
    path.write_text(source, encoding="utf-8")
    record = _read_record(root)
    _refresh_binding(
        validator, root, record, "evidence_bindings", validator.RAW_SOURCE_PATH
    )
    _write_record(validator, root, record)
    with pytest.raises(validator.ValidationError, match="source symbol receipt"):
        validator.validate(root)


def test_populated_preregistration_field_fails_even_with_refreshed_binding(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    prereg_path = root / validator.PREREG_MACHINE_PATH
    prereg = json.loads(prereg_path.read_text(encoding="ascii"))
    prereg["domains"][0]["generated_endpoint_semantics"] = "unreviewed"
    prereg_path.write_text(json.dumps(prereg, sort_keys=True) + "\n", encoding="ascii")
    record = _read_record(root)
    _refresh_binding(
        validator, root, record, "evidence_bindings", validator.PREREG_MACHINE_PATH
    )
    _write_record(validator, root, record)
    with pytest.raises(validator.ValidationError, match="no longer open"):
        validator.validate(root)


def test_relaxed_prospective_seal_fails_even_with_refreshed_binding(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    seal_path = root / validator.SEAL_MACHINE_PATH
    seal = json.loads(seal_path.read_text(encoding="ascii"))
    seal["authority_boundary"]["test_data_opening_authorized"] = True
    seal_path.write_text(json.dumps(seal, sort_keys=True) + "\n", encoding="ascii")
    record = _read_record(root)
    _refresh_binding(
        validator, root, record, "evidence_bindings", validator.SEAL_MACHINE_PATH
    )
    _write_record(validator, root, record)
    with pytest.raises(validator.ValidationError, match="seal authority"):
        validator.validate(root)


def test_duplicate_json_key_fails_strict_loading(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / MACHINE_REL
    raw = path.read_text(encoding="ascii")
    assert raw.startswith("{")
    path.write_text('{"schema_version":"duplicate",' + raw[1:], encoding="ascii")
    with pytest.raises(validator.ValidationError, match="invalid strict JSON"):
        validator.validate(root)


def test_machine_record_symlink_is_refused(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / MACHINE_REL
    saved = path.with_suffix(".saved")
    path.rename(saved)
    path.symlink_to(saved.name)
    with pytest.raises(validator.ValidationError, match="regular non-symlink"):
        validator.validate(root)


def test_machine_record_hardlink_is_refused(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / MACHINE_REL
    os.link(path, path.with_suffix(".hardlink"))
    with pytest.raises(validator.ValidationError, match="hard link"):
        validator.validate(root)
