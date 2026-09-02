"""Synthetic hostiles for the exact Retail temporal split design.

All manifests are invented in memory.  Filesystem mutations are confined to
pytest temporary replicas.  No source, documentation, license, data, network,
connector, authority/runtime, entropy, or scientific route is invoked.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, List, Set, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json"
)
TEST_REL = Path(
    "tests/unit/"
    "test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py"
)
AUTHORITY_TEXT = "Alright, sounds good. Go ahead then."


def _load_validator() -> ModuleType:
    path = ROOT / VALIDATOR_REL
    spec = importlib.util.spec_from_file_location("retail_split_design_validator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _row(ordinal: int, customer: str, timestamp: int) -> Dict[str, Any]:
    return {
        "row_ordinal": ordinal,
        "customer_key_hex": customer.encode("ascii").hex(),
        "timestamp_utc_microseconds": timestamp,
    }


def _single_row_customers(timestamps: List[int]) -> List[Dict[str, Any]]:
    return [_row(index, "c" + str(index), timestamp) for index, timestamp in enumerate(timestamps)]


def _error_code(module: ModuleType, rows: Any) -> str:
    with pytest.raises(module.SplitDesignError) as caught:
        module.split_retail_rows(rows)
    return caught.value.code


def _closed_read_roster(module: ModuleType) -> List[str]:
    return [
        module.HUMAN_PATH,
        module.MACHINE_PATH,
        module.VALIDATOR_PATH,
        module.TEST_PATH,
        *[row["path"] for row in module.LIVE_IMMUTABLE_BINDINGS],
    ]


def _require_tmp_target(root: Path, target: Path) -> None:
    resolved_root = root.resolve()
    resolved_target = target.resolve(strict=False)
    assert resolved_target != ROOT.resolve()
    assert ROOT.resolve() not in resolved_target.parents
    assert resolved_target == resolved_root or resolved_root in resolved_target.parents


def _copy_closed_roster(module: ModuleType, tmp_path: Path) -> Path:
    for relative in _closed_read_roster(module):
        source = ROOT / relative
        target = tmp_path / relative
        _require_tmp_target(tmp_path, target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


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


def _mutation(pointer: str, value: Any) -> Callable[[Dict[str, Any]], None]:
    return lambda record: _replace(record, pointer, value)


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    _require_tmp_target(root, path)
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = module.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def test_canonical_static_package_validates_exact_nonclosure(
    validator: ModuleType,
) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "project_control_predicate": True,
        "pure_split_design_frozen": True,
        "synthetic_qualification_present": True,
        "real_data_accessed": False,
        "real_split_performed": False,
        "real_feasibility_observed": False,
        "all_row_preservation_required": True,
        "row_exclusion_or_quarantine_permitted": False,
        "outcome_or_label_used": False,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "effective_unresolved_field_count": 172,
        "effective_open_blocker_count": 12,
        "precontact_population_blocked": True,
        "validation": "PASS",
    }


def test_authority_and_exact_project_control_scope(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == AUTHORITY_TEXT
    assert authority["normalized_visible_text_utf8_bytes"] == 36
    assert authority["normalized_visible_text_sha256"] == hashlib.sha256(
        AUTHORITY_TEXT.encode("utf-8")
    ).hexdigest()
    assert authority["raw_transport_bytes_bound"] is False
    assert authority["conversation_envelope_bound"] is False
    assert authority["retail_static_design_and_synthetic_qualification_authorized"] is True
    assert authority["external_contact_or_browsing_authorized"] is False
    assert authority["data_access_or_real_split_authorized"] is False
    assert authority["tracker_edit_authorized"] is False
    checklist = record["checklist_effects"]
    assert checklist["project_control_predicate"] == validator.CONTROL_PREDICATE
    assert checklist["targeted_project_location"] == (
        "B03_F060_F061_RETAIL_TEMPORAL_AND_ALLOCATION_SPLIT_DESIGN"
    )
    assert checklist["f060_value_written_into_immutable_preregistration"] is False
    assert checklist["f061_value_written_into_immutable_preregistration"] is False
    assert checklist["unresolved_fields_closed"] == 0
    assert checklist["blockers_closed"] == 0
    assert record["scope_review"][
        "separately_authorized_b03_f060_f061_design_artifact"
    ] is True


@pytest.mark.parametrize(
    ("customer_count", "expected"),
    [
        (5, {"TRAIN": 3, "VALIDATION": 1, "TEST": 1}),
        (6, {"TRAIN": 4, "VALIDATION": 1, "TEST": 1}),
        (7, {"TRAIN": 5, "VALIDATION": 1, "TEST": 1}),
        (8, {"TRAIN": 6, "VALIDATION": 1, "TEST": 1}),
        (9, {"TRAIN": 6, "VALIDATION": 2, "TEST": 1}),
        (10, {"TRAIN": 7, "VALIDATION": 2, "TEST": 1}),
        (11, {"TRAIN": 8, "VALIDATION": 2, "TEST": 1}),
        (12, {"TRAIN": 8, "VALIDATION": 2, "TEST": 2}),
    ],
)
def test_exact_hamilton_counts_and_tie_priority(
    validator: ModuleType,
    customer_count: int,
    expected: Dict[str, int],
) -> None:
    assert validator.hamilton_customer_counts(customer_count) == expected


@pytest.mark.parametrize("value", [False, True, 0, 1, 2, 3, 4, 5.0, "5", None])
def test_hamilton_rejects_bool_alias_and_insufficient_or_noninteger(
    validator: ModuleType,
    value: Any,
) -> None:
    with pytest.raises(validator.SplitDesignError) as caught:
        validator.hamilton_customer_counts(value)
    assert caught.value.code == "INSUFFICIENT_CUSTOMER_GROUPS"


def test_constructive_feasible_case_exact_boundary_and_counts(
    validator: ModuleType,
) -> None:
    rows = _single_row_customers(list(range(10)))
    result = validator.split_retail_rows(rows)
    assert result["algorithm_id"] == validator.ALGORITHM_ID
    assert result["outcome"] == "PASS"
    assert result["row_count"] == 10
    assert result["customer_count"] == 10
    assert result["customer_counts"] == {"TRAIN": 7, "VALIDATION": 2, "TEST": 1}
    assert result["row_counts"] == {"TRAIN": 7, "VALIDATION": 2, "TEST": 1}
    assert result["boundary"] == {
        "train_last_timestamp_utc_microseconds": 6,
        "validation_first_timestamp_utc_microseconds": 7,
        "validation_last_timestamp_utc_microseconds": 8,
        "test_first_timestamp_utc_microseconds": 9,
    }
    assert [row["row_ordinal"] for row in result["row_assignments"]] == list(range(10))
    assert len(result["customer_assignments"]) == 10


def test_multirow_customers_are_complete_and_every_row_is_preserved(
    validator: ModuleType,
) -> None:
    triples = [
        ("a", 0),
        ("a", 1),
        ("b", 2),
        ("b", 3),
        ("c", 4),
        ("d", 10),
        ("d", 11),
        ("e", 20),
        ("e", 21),
    ]
    rows = [_row(index, customer, timestamp) for index, (customer, timestamp) in enumerate(triples)]
    result = validator.split_retail_rows(rows)
    assert result["row_count"] == len(rows)
    assert {item["row_ordinal"] for item in result["row_assignments"]} == set(range(len(rows)))
    customer_to_splits: Dict[str, Set[str]] = {}
    for row, assignment in zip(rows, result["row_assignments"]):
        customer_to_splits.setdefault(row["customer_key_hex"], set()).add(assignment["split"])
    assert all(len(values) == 1 for values in customer_to_splits.values())
    assert sum(result["row_counts"].values()) == len(rows)
    assert result["boundary"] == {
        "train_last_timestamp_utc_microseconds": 4,
        "validation_first_timestamp_utc_microseconds": 10,
        "validation_last_timestamp_utc_microseconds": 11,
        "test_first_timestamp_utc_microseconds": 20,
    }


def test_input_list_permutation_cannot_change_output(validator: ModuleType) -> None:
    rows = _single_row_customers(list(range(10)))
    baseline = validator.split_retail_rows(rows)
    assert validator.split_retail_rows(list(reversed(rows))) == baseline
    assert validator.split_retail_rows(rows[::2] + rows[1::2]) == baseline


def test_interleaved_customer_interval_has_terminal_no_go_without_exclusion(
    validator: ModuleType,
) -> None:
    triples = [
        ("a", 0),
        ("a", 100),
        ("b", 1),
        ("c", 2),
        ("d", 3),
        ("e", 4),
    ]
    rows = [_row(index, customer, timestamp) for index, (customer, timestamp) in enumerate(triples)]
    assert _error_code(validator, rows) == (
        "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
    )
    assert len(rows) == 6


def test_equal_timestamp_at_required_customer_boundary_is_no_go(
    validator: ModuleType,
) -> None:
    rows = _single_row_customers([0, 1, 2, 2, 3])
    assert _error_code(validator, rows) == (
        "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
    )


@pytest.mark.parametrize(
    "rows",
    [
        None,
        (),
        [],
        [{"row_ordinal": 0, "customer_key_hex": "61"}],
        [{"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": 0, "label": 1}],
        [{"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": 0, "outcome": 1}],
        [{"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": 0, "test_indicator": True}],
        [{"row_ordinal": False, "customer_key_hex": "61", "timestamp_utc_microseconds": 0}],
        [{"row_ordinal": 0, "customer_key_hex": "", "timestamp_utc_microseconds": 0}],
        [{"row_ordinal": 0, "customer_key_hex": "6", "timestamp_utc_microseconds": 0}],
        [{"row_ordinal": 0, "customer_key_hex": "6A", "timestamp_utc_microseconds": 0}],
        [{"row_ordinal": 0, "customer_key_hex": "zz", "timestamp_utc_microseconds": 0}],
        [{"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": False}],
        [{"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": 2**63}],
        [{"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": -(2**63) - 1}],
        [
            {"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": 0},
            {"row_ordinal": 0, "customer_key_hex": "62", "timestamp_utc_microseconds": 1},
        ],
        [
            {"row_ordinal": 0, "customer_key_hex": "61", "timestamp_utc_microseconds": 0},
            {"row_ordinal": 2, "customer_key_hex": "62", "timestamp_utc_microseconds": 1},
        ],
    ],
)
def test_every_invalid_row_rejects_whole_manifest_never_quarantines(
    validator: ModuleType,
    rows: Any,
) -> None:
    assert _error_code(validator, rows) == "INVALID_NORMALIZED_MANIFEST"


def test_fewer_than_five_customers_is_no_go(validator: ModuleType) -> None:
    rows = _single_row_customers([0, 1, 2, 3])
    assert _error_code(validator, rows) == "INSUFFICIENT_CUSTOMER_GROUPS"


def test_assignment_digest_binds_exact_payload(validator: ModuleType) -> None:
    result = validator.split_retail_rows(_single_row_customers(list(range(10))))
    digest = result.pop("assignment_manifest_sha256")
    assert digest == hashlib.sha256(
        validator.ASSIGNMENT_DOMAIN + validator._canonical_json_bytes(result)
    ).hexdigest()


def _reference_feasible(intervals: List[Tuple[int, int]]) -> bool:
    timestamps = sorted({timestamp for interval in intervals for timestamp in interval})
    if len(timestamps) < 3:
        return False
    for first_gap in range(len(timestamps) - 2):
        for second_gap in range(first_gap + 1, len(timestamps) - 1):
            counts = {"TRAIN": 0, "VALIDATION": 0, "TEST": 0}
            valid = True
            for minimum, maximum in intervals:
                if maximum <= timestamps[first_gap]:
                    counts["TRAIN"] += 1
                elif minimum >= timestamps[first_gap + 1] and maximum <= timestamps[second_gap]:
                    counts["VALIDATION"] += 1
                elif minimum >= timestamps[second_gap + 1]:
                    counts["TEST"] += 1
                else:
                    valid = False
                    break
            if valid and counts == {"TRAIN": 3, "VALIDATION": 1, "TEST": 1}:
                return True
    return False


def test_exhaustive_small_interval_model_matches_independent_feasibility_oracle(
    validator: ModuleType,
) -> None:
    patterns = ((0, 0), (1, 1), (2, 2), (0, 2))
    for intervals in itertools.product(patterns, repeat=5):
        rows: List[Dict[str, Any]] = []
        ordinal = 0
        for customer_index, (minimum, maximum) in enumerate(intervals):
            customer = "c" + str(customer_index)
            rows.append(_row(ordinal, customer, minimum))
            ordinal += 1
            if maximum != minimum:
                rows.append(_row(ordinal, customer, maximum))
                ordinal += 1
        expected = _reference_feasible(list(intervals))
        try:
            result = validator.split_retail_rows(rows)
            observed = result["outcome"] == "PASS"
        except validator.SplitDesignError as error:
            assert error.code == "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
            observed = False
        assert observed is expected


@pytest.mark.parametrize(
    ("pointer", "value"),
    [
        ("authority_provenance.normalized_visible_text", AUTHORITY_TEXT + " "),
        ("authority_provenance.raw_transport_bytes_bound", True),
        ("authority_provenance.external_contact_or_browsing_authorized", True),
        ("authority_provenance.data_access_or_real_split_authorized", True),
        ("design_identity.real_retail_snapshot_opened", True),
        ("design_identity.real_retail_feasibility_observed", True),
        ("design_identity.real_split_performed", True),
        ("design_identity.power_justified", True),
        ("normalized_manifest_contract.future_manifest_must_cover_every_snapshot_row", False),
        ("normalized_manifest_contract.row_quarantine_censoring_exclusion_repair_or_reassignment_permitted", True),
        ("normalized_manifest_contract.real_manifest_present", True),
        ("hamilton_allocation_contract.minimum_customer_count", 4),
        ("hamilton_allocation_contract.seed_or_entropy_used", True),
        ("temporal_boundary_contract.boundary_spanning_customer_makes_pair_infeasible", False),
        ("temporal_boundary_contract.outcome_label_or_model_result_used", True),
        ("temporal_boundary_contract.fallback_relaxation_retry_exclusion_censoring_quarantine_or_reassignment_permitted", True),
        ("output_contract.all_rows_preserved", False),
        ("output_contract.real_output_present", True),
        ("failure_contract.failure_is_terminal_no_go_for_this_rule", False),
        ("failure_contract.fallback_retry_boundary_relaxation_resplit_customer_migration_or_row_exclusion_permitted", True),
        ("synthetic_qualification_contract.real_snapshot_contract_satisfied", True),
        ("synthetic_qualification_contract.real_feasible_boundary_pair_exists", True),
        ("predecessor_effects.candidate_predecessor_modified", True),
        ("predecessor_effects.candidate_approval_roster_seam_closed", True),
        ("predecessor_effects.candidate_power_seam_closed", True),
        ("checklist_effects.f060_value_written_into_immutable_preregistration", True),
        ("checklist_effects.f061_value_written_into_immutable_preregistration", True),
        ("checklist_effects.unresolved_fields_closed", 1),
        ("checklist_effects.blockers_closed", 1),
        ("checklist_effects.precontact_population_blocked", False),
        ("scope_review.separately_authorized_b03_f060_f061_design_artifact", False),
        ("scope_review.characterized_as_third_precontact_micro_layer", True),
        ("publication_anonymity_boundary.real_customer_key_timestamp_or_row_present", True),
    ],
)
def test_static_overclaim_and_exact_type_mutations_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
    pointer: str,
    value: Any,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(validator, root, _mutation(pointer, value))
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_machine_self_canonical_roster_and_package_binding_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
) -> None:
    cases = [tmp_path / name for name in ("self", "pretty", "extra", "binding")]
    for root in cases:
        root.mkdir()
        _copy_closed_roster(validator, root)
    _rewrite_machine(
        validator,
        cases[0],
        _mutation("design_identity.design_frozen", False),
        recompute_digest=False,
    )
    _rewrite_machine(validator, cases[1], lambda record: None, canonical=False)
    _rewrite_machine(validator, cases[2], lambda record: record.update({"extra": False}))
    _rewrite_machine(
        validator,
        cases[3],
        _mutation("package_bindings.0.raw_sha256", "0" * 64),
    )
    for root in cases:
        with pytest.raises(validator.ValidationError):
            validator.validate(root)


@pytest.mark.parametrize("kind", ["mode", "hardlink", "symlink", "bytes"])
def test_immutable_predecessor_custody_mutations_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
    kind: str,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    path = root / validator.CANDIDATE_MACHINE_PATH
    _require_tmp_target(root, path)
    if kind == "mode":
        path.chmod(0o600)
    elif kind == "hardlink":
        link = root / "candidate_link"
        _require_tmp_target(root, link)
        os.link(path, link)
    elif kind == "symlink":
        copy = root / "candidate_copy"
        _require_tmp_target(root, copy)
        shutil.copyfile(path, copy)
        path.unlink()
        path.symlink_to(copy)
    else:
        raw = path.read_bytes()
        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
        path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_name(node.value)
        return prefix + "." + node.attr if prefix else node.attr
    return ""


def test_validator_and_test_sources_have_no_process_network_or_canonical_effect_routes(
    validator: ModuleType,
) -> None:
    sources = {
        "validator": (ROOT / VALIDATOR_REL).read_text(encoding="utf-8"),
        "test": (ROOT / TEST_REL).read_text(encoding="utf-8"),
    }
    expected_imports = {
        "validator": {"__future__", "hashlib", "json", "os", "pathlib", "stat", "typing"},
        "test": {"__future__", "ast", "hashlib", "importlib.util", "itertools", "json", "os", "pathlib", "pytest", "shutil", "types", "typing"},
    }
    forbidden_prefixes = (
        "subprocess.",
        "multiprocessing.",
        "socket.",
        "ssl.",
        "http.",
        "urllib.",
        "requests.",
        "os.system",
        "os.popen",
        "os.fork",
        "os.exec",
        "os.spawn",
        "os.posix_spawn",
        "os.write",
    )
    for label, source in sources.items():
        tree = ast.parse(source)
        imports: Set[str] = set()
        calls: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                calls.append(_qualified_name(node.func))
        assert imports == expected_imports[label]
        assert not any(
            call == prefix or call.startswith(prefix)
            for call in calls
            for prefix in forbidden_prefixes
        )
        if label == "validator":
            assert "write_bytes" not in calls
            assert "write_text" not in calls
            assert "mkdir" not in calls
    validator_tree = ast.parse(sources["validator"])
    open_calls = [
        node
        for node in ast.walk(validator_tree)
        if isinstance(node, ast.Call) and _qualified_name(node.func) == "os.open"
    ]
    assert len(open_calls) == 1
    assert "flags = os.O_RDONLY" in sources["validator"]
    assert "_require_tmp_target" in sources["test"]
    assert "ROOT.resolve() not in resolved_target.parents" in sources["test"]


def test_validator_reads_only_fixed_package_and_predecessor_roster(
    validator: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: List[str] = []
    original = validator._stable_read

    def tracking(root: Path, relative: str) -> bytes:
        observed.append(relative)
        return original(root, relative)

    monkeypatch.setattr(validator, "_stable_read", tracking)
    assert validator.validate()["validation"] == "PASS"
    assert set(observed) == set(_closed_read_roster(validator))


def test_package_has_no_local_absolute_path_real_row_or_secret(
    validator: ModuleType,
) -> None:
    raw_files = [
        (ROOT / validator.HUMAN_PATH).read_bytes(),
        (ROOT / validator.MACHINE_PATH).read_bytes(),
    ]
    for raw in raw_files:
        assert b"/Users/" not in raw
        assert b"BEGIN PRIVATE KEY" not in raw
        assert b'"real_customer_key_timestamp_or_row_present":true' not in raw
    machine_raw = raw_files[1]
    assert validator.canonical_machine_bytes(json.loads(machine_raw)) == machine_raw


def test_no_focused_bytecode_cache_exists(validator: ModuleType) -> None:
    stems = (
        "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1",
        "test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1",
    )
    found = [
        path
        for path in ROOT.rglob("*.pyc")
        if any(stem in path.name for stem in stems)
    ]
    assert found == []
