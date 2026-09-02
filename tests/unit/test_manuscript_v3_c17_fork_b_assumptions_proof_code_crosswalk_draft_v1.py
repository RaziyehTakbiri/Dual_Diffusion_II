"""Hostile tests for the additive C17 Fork-B draft package.

All mutations are confined to pytest temporary replicas.  The suite loads
only the read-only administrative validator; it does not import project
science, execute a theorem diagnostic, contact a source, inspect data, draw
scientific entropy, or modify a canonical evidence file.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1.json"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "c17_fork_b_assumptions_crosswalk_validator", ROOT / VALIDATOR_REL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _standard_roster(module: ModuleType) -> List[str]:
    return [
        module.HUMAN_PATH,
        module.MACHINE_PATH,
        module.VALIDATOR_PATH,
        module.TEST_PATH,
        *[row["path"] for row in module.LIVE_IMMUTABLE_BINDINGS],
    ]


def _historical_roster(module: ModuleType) -> List[str]:
    return [
        *[row["path"] for row in module.HISTORICAL_DOCUMENT_BINDINGS],
        *[row["path"] for row in module.HISTORICAL_SOURCE_BINDINGS],
    ]


def _copy_paths(paths: Iterable[str], tmp_path: Path) -> Path:
    for relative in paths:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _copy_standard(module: ModuleType, tmp_path: Path) -> Path:
    return _copy_paths(_standard_roster(module), tmp_path)


def _copy_with_historical(module: ModuleType, tmp_path: Path) -> Path:
    return _copy_paths(
        [*_standard_roster(module), *_historical_roster(module)], tmp_path
    )


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = module.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


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


def _binding_for_source(module: ModuleType, row: Mapping[str, Any], raw: bytes) -> Dict[str, Any]:
    rebound = module._binding(row["ordinal"], row["role"], row["path"], raw)
    rebound["expected_symbols"] = list(row["expected_symbols"])
    return rebound


def test_canonical_package_validates_with_exact_nonclosure(validator: ModuleType) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "C17_FORK_B_ASSUMPTIONS_AND_PROOF_CODE_CROSSWALK_DRAFT_VALIDATED"
        ),
        "control_predicate_value": True,
        "route": "FORK_B_DIRECT_SIMULTANEOUS_TARGET_OCCUPATION_CERTIFICATES",
        "viability": (
            "CONDITIONALLY_VIABLE_PROOF_PROGRAM_NOT_CURRENTLY_DISCHARGED_"
            "OR_NONVACUOUS"
        ),
        "c17_status": "UNPROVED",
        "assumption_count": 12,
        "assumptions_proved": 0,
        "proof_obligation_count": 18,
        "proof_obligations_discharged": 0,
        "certificate_component_count": 5,
        "finite_nonvacuous_certificate_count": 0,
        "B01_open": True,
        "F001_through_F006_open_count": 6,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "scientific_effect": 0,
        "historical_snapshot_reopened_by_standard_validation": False,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_historical_snapshot_audit_is_explicit_and_complete(validator: ModuleType) -> None:
    audit = validator.audit_historical_snapshot_at_freeze()
    assert audit == {
        "snapshot_date": "2026-08-30",
        "document_count": 6,
        "source_count": 15,
        "expected_symbol_count": sum(
            len(row["expected_symbols"])
            for row in validator.HISTORICAL_SOURCE_BINDINGS
        ),
        "historically_absent_path_count": 4,
        "method_spec_live_source_crosswalk_conflict": "UNRESOLVED",
        "standard_validation_permanent_absence_gate": False,
        "audit": "PASS",
    }


def test_authority_is_exact_and_narrow(validator: ModuleType) -> None:
    record = validator.expected_record()
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == (
        "Sounds great. Go ahead and finish them in parallel. "
        "Mark all the completed tasks as the end."
    )
    assert authority["normalized_visible_text_utf8_bytes"] == 92
    assert authority["normalized_visible_text_sha256"] == (
        "465aa47a0714b7914e33b6b6772afbfad3a56959cb6eb9f10b8e98f39c0f8d38"
    )
    assert authority["raw_transport_bytes_bound"] is False
    assert authority["tracker_modified_by_this_package"] is False
    assert authority["external_contact_or_browsing_authorized"] is False
    assert authority["data_access_or_download_authorized"] is False
    assert authority["runtime_approval_authorized"] is False
    assert authority["scientific_execution_authorized"] is False
    assert authority["claim_promotion_or_submission_authorized"] is False


def test_route_and_common_support_are_exactly_predecessor_selected(validator: ModuleType) -> None:
    route = validator.expected_record()["route_selection"]
    assert route["route"] == validator.ROUTE
    assert route["orientation"] == "KL(P_H || P_HHAT)_TARGET_FIRST"
    assert route["component_order"] == [
        "K0", "KC", "K_PLUS", "K_MINUS", "K_REPLACEMENT"
    ]
    assert route["simultaneous_upper_bound_order"] == [
        "U0", "UC", "U_PLUS", "U_MINUS", "U_REPLACEMENT"
    ]
    assert route["common_support_policy"] == validator.COMMON_SUPPORT_POLICY
    assert route["c17_status"] == "UNPROVED"
    assert route["finite_nonvacuous_bounds_present"] is False
    assert route["target_occupation_available"] is False
    assert route["dominating_measure_and_exact_radon_nikodym_factors_available"] is False


def test_all_twelve_assumptions_are_uniform_ordered_and_open(validator: ModuleType) -> None:
    rows = validator.expected_record()["assumption_inventory"]
    assert [row["assumption_id"] for row in rows] == [
        "A" + str(index) for index in range(1, 13)
    ]
    assert [row["ordinal"] for row in rows] == list(range(12))
    assert all(type(row["ordinal"]) is int for row in rows)
    assert len({tuple(sorted(row)) for row in rows}) == 1
    for row in rows:
        assert row["required_for_current_c17_target"] is True
        assert row["verified_for_general_c17"] is False
        assert row["verified_for_physionet"] is False
        assert row["verified_for_retail"] is False
        assert row["closed_by_this_package"] is False


def test_all_eighteen_proof_obligations_remain_open(validator: ModuleType) -> None:
    rows = validator.expected_record()["proof_obligation_register"]
    assert [row["proof_obligation_id"] for row in rows] == [
        "PO" + str(index).zfill(2) for index in range(1, 19)
    ]
    assert [row["ordinal"] for row in rows] == list(range(18))
    for row in rows:
        assert row["status"] == "OPEN"
        assert row["discharged"] is False
        assert row["real_domain_discharged"] is False
        assert row["code_evidence_sufficient"] is False
        assert row["closed_by_this_package"] is False


def test_assumption_references_resolve_to_known_crosswalk_and_obligations(validator: ModuleType) -> None:
    record = validator.expected_record()
    symbol_ids = {row["symbol_id"] for row in record["proof_code_crosswalk"]}
    obligation_ids = {
        row["proof_obligation_id"] for row in record["proof_obligation_register"]
    }
    for row in record["assumption_inventory"]:
        assert set(row["code_symbol_ids"]) <= symbol_ids
        assert set(row["proof_obligation_ids"]) <= obligation_ids


def test_five_direct_certificates_are_typed_null_and_nonvacuous_false(validator: ModuleType) -> None:
    rows = validator.expected_record()["direct_certificate_register"]
    assert [row["component_id"] for row in rows] == [
        "K0", "KC", "K_PLUS", "K_MINUS", "K_REPLACEMENT"
    ]
    assert [row["upper_bound_id"] for row in rows] == [
        "U0", "UC", "U_PLUS", "U_MINUS", "U_REPLACEMENT"
    ]
    for row in rows:
        for field in (
            "bound_value", "certificate_path", "occupation_receipt",
            "dominating_measure_receipt", "radon_nikodym_factor_receipt",
            "simultaneous_event_receipt", "nonvacuity_threshold",
        ):
            assert row[field] is None
        assert row["finite"] is False
        assert row["nonvacuous"] is False
        assert row["certificate_present"] is False
        assert row["closed_by_this_package"] is False


def test_code_crosswalk_never_promotes_partial_interfaces(validator: ModuleType) -> None:
    rows = validator.expected_record()["proof_code_crosswalk"]
    assert len(rows) == 15
    assert [row["source_ordinal"] for row in rows] == list(range(15))
    assert all(row["sufficient_for_c17"] is False for row in rows)
    assert rows[13]["strength"] == "OPERATIONAL_SURROGATE_NOT_ANALYTIC_H"
    assert rows[14]["strength"] == "PREFLIGHT_ONLY_NOT_COMPLETE_SAMPLER"


def test_historical_absence_is_observation_not_permanent_gate(validator: ModuleType) -> None:
    rows = validator.expected_record()["historical_snapshot_inputs"][
        "absent_paths_at_snapshot"
    ]
    assert len(rows) == 4
    assert all(row["historically_absent"] is True for row in rows)
    assert all(row["permanent_absence_gate"] is False for row in rows)
    assert validator.expected_record()["historical_snapshot_inputs"][
        "future_materialization_or_refactor_permitted"
    ] is True


def test_future_historical_source_materialization_does_not_break_standard_validation(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_with_historical(validator, tmp_path)
    future = root / validator.HISTORICAL_ABSENCE_OBSERVATIONS[0]["path"]
    future.parent.mkdir(parents=True, exist_ok=True)
    future.write_text("def future_implementation():\n    return None\n", encoding="ascii")
    future.chmod(0o644)
    assert validator.validate(root)["validation"] == "PASS"
    with pytest.raises(validator.ValidationError, match="historically absent path"):
        validator.audit_historical_snapshot_at_freeze(root)


def test_historical_source_byte_change_does_not_break_standard_validation_but_breaks_audit(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_with_historical(validator, tmp_path)
    path = root / validator.HISTORICAL_SOURCE_BINDINGS[0]["path"]
    path.write_bytes(path.read_bytes() + b"# historical drift\n")
    path.chmod(0o644)
    assert validator.validate(root)["validation"] == "PASS"
    with pytest.raises(validator.ValidationError, match="historical source binding"):
        validator.audit_historical_snapshot_at_freeze(root)


def test_historical_ast_symbol_check_is_semantic_not_only_hash(
    validator: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_with_historical(validator, tmp_path)
    original = validator.HISTORICAL_SOURCE_BINDINGS[0]
    path = root / original["path"]
    raw = path.read_bytes().replace(
        b"class CappedPoissonConfigurationReference",
        b"class RemovedCappedPoissonReference",
        1,
    )
    assert raw != path.read_bytes()
    path.write_bytes(raw)
    path.chmod(0o644)
    rebound = _binding_for_source(validator, original, raw)
    rows = (rebound, *validator.HISTORICAL_SOURCE_BINDINGS[1:])
    monkeypatch.setattr(validator, "HISTORICAL_SOURCE_BINDINGS", rows)
    with pytest.raises(validator.ValidationError, match="expected symbol absent"):
        validator.audit_historical_snapshot_at_freeze(root)


def test_b01_and_f001_through_f006_remain_open_and_null(validator: ModuleType) -> None:
    effects = validator.expected_record()["field_and_blocker_effects"]
    assert set(effects) == {
        "B01", "F001", "F002", "F003", "F004", "F005", "F006"
    }
    assert effects["B01"] == {"status": "OPEN", "closed_by_this_package": False}
    for identifier in ("F001", "F002", "F003", "F004", "F005", "F006"):
        assert effects[identifier]["status"] == "OPEN"
        assert effects[identifier]["value"] is None
        assert effects[identifier]["closed_by_this_package"] is False


def test_scope_counts_and_nonclaims_are_exact(validator: ModuleType) -> None:
    scope = validator.expected_record()["scope_and_nonclaims"]
    assert scope["unresolved_field_count"] == 172
    assert scope["effective_open_blocker_count"] == 12
    assert scope["unresolved_fields_closed"] == 0
    assert scope["blockers_closed"] == 0
    assert scope["formal_tests_closed"] == 0
    assert scope["scientific_results_produced"] == 0
    assert scope["tracker_edited"] is False
    assert scope["c17_claim_promoted"] is False
    assert scope["common_support_domain_admission_promoted"] is False
    assert scope["confirmatory_execution_authorized"] is False


@pytest.mark.parametrize(
    ("pointer", "bad_value"),
    [
        ("route_selection.route", "FORK_A"),
        ("route_selection.orientation", "KL(P_HHAT || P_H)"),
        ("route_selection.viability", "PROVED"),
        ("route_selection.c17_status", "PROVED"),
        ("route_selection.a1_through_a12_proved", True),
        ("route_selection.finite_nonvacuous_bounds_present", True),
        ("route_selection.target_occupation_available", True),
        ("route_selection.dominating_measure_and_exact_radon_nikodym_factors_available", True),
        ("route_selection.nce_used_as_path_certificate", True),
        ("route_selection.cap_or_reference_defect_added_as_sixth_kl_term", True),
        ("route_selection.manuscript_claim_promoted", True),
        ("route_selection.scientific_effect", False),
        ("assumption_inventory.0.verified_for_general_c17", True),
        ("assumption_inventory.3.verified_for_physionet", True),
        ("assumption_inventory.8.verified_for_retail", True),
        ("assumption_inventory.11.closed_by_this_package", True),
        ("proof_obligation_register.0.status", "CLOSED"),
        ("proof_obligation_register.8.discharged", True),
        ("proof_obligation_register.17.code_evidence_sufficient", True),
        ("direct_certificate_register.0.bound_value", 0),
        ("direct_certificate_register.1.certificate_present", True),
        ("direct_certificate_register.2.finite", True),
        ("direct_certificate_register.3.nonvacuous", True),
        ("direct_certificate_register.4.simultaneous_event_receipt", "invented"),
        ("proof_code_crosswalk.0.sufficient_for_c17", True),
        ("field_and_blocker_effects.B01.status", "CLOSED"),
        ("field_and_blocker_effects.F001.value", "invented theorem"),
        ("field_and_blocker_effects.F002.status", "CLOSED"),
        ("field_and_blocker_effects.F004.value", "this package"),
        ("scope_and_nonclaims.unresolved_fields_closed", 1),
        ("scope_and_nonclaims.blockers_closed", 1),
        ("scope_and_nonclaims.tracker_edited", True),
        ("scope_and_nonclaims.c17_claim_promoted", True),
        ("scope_and_nonclaims.confirmatory_execution_authorized", True),
    ],
)
def test_every_overclaim_and_nonclosure_flip_fails_closed(
    validator: ModuleType, tmp_path: Path, pointer: str, bad_value: Any
) -> None:
    root = _copy_standard(validator, tmp_path)
    _rewrite_machine(
        validator, root, lambda record: _replace(record, pointer, bad_value)
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize(
    ("pointer", "bad_value"),
    [
        ("assumption_inventory.0.ordinal", False),
        ("proof_obligation_register.0.ordinal", False),
        ("direct_certificate_register.0.ordinal", False),
        ("scope_and_nonclaims.unresolved_field_count", True),
        ("scope_and_nonclaims.effective_open_blocker_count", False),
        ("route_selection.scientific_effect", False),
    ],
)
def test_bool_for_int_is_rejected(
    validator: ModuleType, tmp_path: Path, pointer: str, bad_value: Any
) -> None:
    root = _copy_standard(validator, tmp_path)
    _rewrite_machine(
        validator, root, lambda record: _replace(record, pointer, bad_value)
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_assumption_reorder_and_proof_gap_are_rejected(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_standard(validator, tmp_path)

    def mutate(record: Dict[str, Any]) -> None:
        rows = record["assumption_inventory"]
        rows[0], rows[1] = rows[1], rows[0]

    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)

    root2 = _copy_standard(validator, tmp_path / "gap")
    _rewrite_machine(
        validator, root2,
        lambda record: record["proof_obligation_register"].pop(9),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root2)


def test_component_reorder_or_uncovered_family_is_rejected(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_standard(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: record["direct_certificate_register"].pop(4),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_machine_extra_missing_and_noncanonical_records_fail(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_standard(validator, tmp_path / "extra")
    _rewrite_machine(validator, root, lambda record: record.update({"extra": 1}))
    with pytest.raises(validator.ValidationError, match="schema mismatch"):
        validator.validate(root)

    root = _copy_standard(validator, tmp_path / "missing")
    _rewrite_machine(validator, root, lambda record: record.pop("unresolved_gap_register"))
    with pytest.raises(validator.ValidationError, match="schema mismatch"):
        validator.validate(root)

    root = _copy_standard(validator, tmp_path / "pretty")
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError, match="not canonical"):
        validator.validate(root)


def test_machine_self_digest_and_package_binding_fail_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_standard(validator, tmp_path / "self")
    _rewrite_machine(
        validator,
        root,
        lambda record: record["authority_provenance"].update(
            {"raw_transport_bytes_bound": True}
        ),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError, match="self digest"):
        validator.validate(root)

    root = _copy_standard(validator, tmp_path / "binding")
    human = root / validator.HUMAN_PATH
    human.write_bytes(human.read_bytes() + b"drift\n")
    human.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize("relative_index", [0, 1, 2, 3, 4, 5])
def test_each_immutable_input_binding_is_live(
    validator: ModuleType, tmp_path: Path, relative_index: int
) -> None:
    root = _copy_standard(validator, tmp_path)
    path = root / validator.LIVE_IMMUTABLE_BINDINGS[relative_index]["path"]
    path.write_bytes(path.read_bytes() + b"drift\n")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize("attack", ["wrong_mode", "hardlink", "symlink"])
def test_machine_leaf_custody_rejects_mode_link_and_symlink(
    validator: ModuleType, tmp_path: Path, attack: str
) -> None:
    root = _copy_standard(validator, tmp_path)
    target = root / validator.MACHINE_PATH
    if attack == "wrong_mode":
        target.chmod(0o600)
    elif attack == "hardlink":
        os.link(target, root / "machine-hardlink")
    else:
        saved = root / "saved-machine"
        target.rename(saved)
        target.symlink_to(saved)
    with pytest.raises(validator.ValidationError, match="custody invalid"):
        validator.validate(root)


def test_historical_bindings_are_exact_but_not_live_reverse_dependencies(
    validator: ModuleType
) -> None:
    record = validator.expected_record()
    snapshot = record["historical_snapshot_inputs"]
    assert snapshot["documents"] == [
        dict(row) for row in validator.HISTORICAL_DOCUMENT_BINDINGS
    ]
    assert snapshot["sources"] == [
        dict(row) for row in validator.HISTORICAL_SOURCE_BINDINGS
    ]
    assert snapshot["standard_validation_reopens_snapshot"] is False
    assert snapshot["new_one_way_audit_required_after_change"] is True


def test_machine_contains_no_local_absolute_paths(validator: ModuleType) -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    assert str(ROOT).encode("utf-8") not in raw
    assert b"/Users/" not in raw
    record = json.loads(raw.decode("ascii"))
    for row in (
        record["live_immutable_input_bindings"]
        + record["package_bindings"]
        + record["historical_snapshot_inputs"]["documents"]
        + record["historical_snapshot_inputs"]["sources"]
        + record["historical_snapshot_inputs"]["absent_paths_at_snapshot"]
    ):
        assert not Path(row["path"]).is_absolute()


def test_validator_source_is_read_only_stdlib_and_has_no_project_science_import(
    validator: ModuleType
) -> None:
    raw = (ROOT / VALIDATOR_REL).read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    imports = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                calls.add(node.func.value.id + "." + node.func.attr)
    assert imports <= {
        "__future__", "ast", "hashlib", "json", "os", "pathlib", "stat", "typing"
    }
    assert imports.isdisjoint(
        {"heterodiff", "subprocess", "socket", "ssl", "http", "urllib", "requests", "multiprocessing"}
    )
    forbidden_calls = {
        "os.write", "os.mkdir", "os.makedirs", "os.unlink", "os.remove",
        "os.rename", "os.replace", "os.system", "os.popen", "os.fork",
        "os.posix_spawn", "os.execv", "os.spawnv",
    }
    assert calls.isdisjoint(forbidden_calls)
    assert "os.open" in calls
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr == "open"
        ):
            assert len(node.args) >= 2
            assert isinstance(node.args[1], ast.Name)
            assert node.args[1].id == "flags"


def test_hostile_test_source_has_no_process_network_or_canonical_writer_target() -> None:
    raw = Path(__file__).read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    imports = set()
    qualified_calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            qualified_calls.add(node.func.value.id + "." + node.func.attr)
    assert imports.isdisjoint(
        {"heterodiff", "subprocess", "socket", "ssl", "http", "urllib", "requests", "multiprocessing"}
    )
    assert "tmp_path" in raw.decode("utf-8")
    assert qualified_calls.isdisjoint(
        {
            "os.system", "os.popen", "os.fork", "os.posix_spawn",
            "os.execv", "os.spawnv", "subprocess.run", "subprocess.Popen",
        }
    )


def test_package_files_are_regular_0644_nlink1_lf_and_no_focused_pyc(
    validator: ModuleType
) -> None:
    for relative in (
        validator.HUMAN_PATH,
        validator.MACHINE_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ):
        path = ROOT / relative
        status = path.lstat()
        assert path.is_file() and not path.is_symlink()
        assert status.st_mode & 0o777 == 0o644
        assert status.st_nlink == 1
        assert path.read_bytes().endswith(b"\n")
    assert not list(
        (ROOT / "research/diagnostics/__pycache__").glob(
            "manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1*.pyc"
        )
    )
    assert not list(
        (ROOT / "tests/unit/__pycache__").glob(
            "test_manuscript_v3_c17_fork_b_assumptions_proof_code_crosswalk_draft_v1*.pyc"
        )
    )
