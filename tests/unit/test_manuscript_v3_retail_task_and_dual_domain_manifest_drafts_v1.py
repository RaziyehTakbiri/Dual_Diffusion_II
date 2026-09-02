"""Hostile tests for the stopped Retail/dual-domain manifest draft package."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("dual_domain_manifest_validator", ROOT / VALIDATOR_REL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


@pytest.fixture(scope="module")
def source(validator: ModuleType) -> ModuleType:
    return validator.load_qualified_source()


def _phys_rows() -> List[Dict[str, Any]]:
    return [
        {"record_ordinal": 0, "patient_id": "1"},
        {"record_ordinal": 1, "patient_id": "2"},
        {"record_ordinal": 2, "patient_id": "3"},
        {"record_ordinal": 3, "patient_id": "4"},
        {"record_ordinal": 4, "patient_id": "5"},
        {"record_ordinal": 5, "patient_id": "6"},
        {"record_ordinal": 6, "patient_id": "1"},
    ]


def _retail_rows() -> List[Dict[str, Any]]:
    return [
        {
            "row_ordinal": index,
            "customer_key_hex": format(index + 1, "02x"),
            "timestamp_utc_microseconds": (index + 1) * 10,
        }
        for index in range(10)
    ]


def _pair(source: ModuleType, domain: str, rows: Any, label: str):
    snapshot = source.build_synthetic_snapshot_manifest(domain, rows, label)
    split = source.build_split_manifest(snapshot, rows)
    return snapshot, split


def _roster(validator: ModuleType) -> List[str]:
    return [
        validator.SOURCE_PATH,
        validator.HUMAN_PATH,
        validator.MACHINE_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
        *[spec["path"] for spec in validator.INPUT_SPECS],
    ]


def _copy_paths(paths: Iterable[str], tmp_path: Path) -> Path:
    for relative in paths:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _copy_package(validator: ModuleType, tmp_path: Path) -> Path:
    return _copy_paths(_roster(validator), tmp_path)


def _rewrite_machine(
    validator: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute:
        record["record_sha256"] = validator.record_sha256(record)
    raw = validator.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def test_canonical_package_validates_with_only_narrow_effect(validator: ModuleType):
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "RETAIL_TASK_SCHEMA_AND_DUAL_DOMAIN_SNAPSHOT_SPLIT_MANIFEST_DRAFTS_VALIDATED"
        ),
        "eligible_after_independent_audit": True,
        "solo_block5_draft_milestone_only": True,
        "existing_fields_closed": 0,
        "blockers_closed": 0,
        "formal_tests_closed": 0,
        "results_filled": 0,
        "scientific_effect": 0,
        "validation": "PASS",
    }


def test_exact_authority_and_internal_renewed_scope_review(validator: ModuleType):
    record = validator.build_expected_record()
    row = record["authority_provenance"]
    raw = row["normalized_visible_text"].encode("utf-8")
    assert len(raw) == 207
    assert hashlib.sha256(raw).hexdigest() == validator.AUTHORITY_SHA256
    assert row["internal_renewed_scope_review_performed"] is True
    assert row["renewed_scope_review_is_agent_adjudication"] is True
    assert row["sole_justification"].startswith("CLOSE_NAMED_SOLO_BLOCK5")
    for key in (
        "external_contact_or_browsing_authorized",
        "data_access_or_download_authorized",
        "entropy_or_live_randomness_authorized",
        "runtime_approval_authorized",
        "scientific_execution_authorized",
        "training_authorized",
        "claim_promotion_or_submission_authorized",
        "tracker_edit_authorized_by_package",
    ):
        assert row[key] is False


def test_all_predecessors_are_hard_pinned_before_source_execution(validator: ModuleType):
    record = validator.build_expected_record()
    assert len(record["input_bindings"]) == 20
    assert record["scope_review"]["hard_pinned_predecessor_file_count"] == 20
    assert record["scope_review"]["hard_pinned_source_before_in_memory_execution"] is True
    assert record["scope_review"]["pathname_loader_used_for_verified_source"] is False
    assert record["scope_review"]["bytecode_loader_used_for_verified_source"] is False


def test_mutable_trackers_are_neither_bound_nor_edited(validator: ModuleType):
    record = validator.build_expected_record()
    paths = [row["path"] for row in record["input_bindings"] + record["package_bindings"]]
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in paths
    assert "PROJECT_EVIDENCE_LEDGER.md" not in paths
    assert record["scope_review"]["mutable_tracker_input_or_reverse_binding_present"] is False
    assert record["scope_review"]["tracker_edited_by_package"] is False


def test_retail_task_fields_are_all_future_typed_and_null(source: ModuleType):
    route = source.retail_task_schema_route_draft()
    fields = route["future_typed_receipts"]
    assert [row["field_id"] for row in fields] == [
        *("F" + str(index).zfill(3) for index in range(38, 58)),
        "F059",
        "F060",
        "F061",
    ]
    assert all(row["state"] == "OPEN_FUTURE_TYPED_RECEIPT_REQUIRED" for row in fields)
    assert all(row["value"] is None for row in fields)
    assert route["source_field_schema_or_semantics_verified"] is False
    assert route["domain_admitted"] is False


def test_exact_nonclosure_rosters(validator: ModuleType):
    row = validator.build_expected_record()["nonclosure"]
    assert row["open_field_roster"] == ["F" + str(index).zfill(3) for index in range(19, 62)]
    assert row["f038_through_f061_all_open_and_null"] is True
    assert row["blocker_roster_remaining_open"] == ["B" + str(index).zfill(2) for index in range(1, 13)]
    assert row["formal_test_states"] == {
        "FORMAL_TEST_28": "OPEN",
        "FORMAL_TEST_29": "OPEN",
        "FORMAL_TEST_30": "OPEN",
    }
    assert row["result_slots_remaining_open"] == ["R1", "R2", "R3", "R4"]
    assert row["mutable_project_totals_asserted_or_bound"] is False


@pytest.mark.parametrize(
    "domain,rows,label",
    [
        ("physionet-challenge-2012", _phys_rows(), "PHYS-B"),
        ("online-retail-ii", _retail_rows(), "RETAIL-B"),
    ],
)
def test_synthetic_snapshot_and_split_pair_is_content_addressed_and_crosslinked(
    source: ModuleType, domain: str, rows: Any, label: str
):
    snapshot, split = _pair(source, domain, rows, label)
    result = source.validate_manifest_pair(snapshot, split)
    assert result["crosslink_valid"] is True
    assert result["all_rows_preserved"] is True
    assert result["structural_validation_only"] is True
    assert result["source_license_governance_custody_or_admission_verified"] is False
    assert result["allocation_power_approved"] is False
    assert result["allocation_power_receipt_independently_verified"] is False
    assert result["F061_closed"] is False
    assert result["domain_admitted"] is False
    assert snapshot["snapshot_manifest_sha256"] == source._snapshot_digest(snapshot)
    assert split["split_manifest_sha256"] == source._split_digest(split)
    assert split["snapshot_manifest_sha256"] == snapshot["snapshot_manifest_sha256"]


def test_assignments_match_exact_stopped_contract_receipts(source: ModuleType):
    phys_snapshot, phys_split = _pair(source, "physionet-challenge-2012", _phys_rows(), "PHYS-C")
    retail_snapshot, retail_split = _pair(source, "online-retail-ii", _retail_rows(), "RETAIL-C")
    assert phys_split["assignment_output"]["algorithm_id"] == "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1"
    assert phys_split["assignment_output"]["patient_counts"] == {"TRAIN": 4, "VALIDATION": 1, "TEST": 1}
    assert retail_split["assignment_output"]["algorithm_id"] == "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1"
    assert retail_split["assignment_output"]["customer_counts"] == {"TRAIN": 7, "VALIDATION": 2, "TEST": 1}
    assert phys_snapshot["splitter_machine_sha256"] == "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8"
    assert retail_snapshot["splitter_machine_sha256"] == "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b"


def test_hard_pinned_parent_splitters_are_differentially_equivalent(
    validator: ModuleType, source: ModuleType
):
    phys_parent, retail_parent = validator.load_qualified_parent_splitters()
    receipt = validator._splitter_equivalence_receipt(source, phys_parent, retail_parent)
    assert receipt["total_case_count"] == 396
    assert receipt["constructive_case_count"] == 14
    assert receipt["permutation_case_count"] == 14
    assert receipt["small_exhaustive_case_count"] == 363
    assert receipt["refusal_case_count"] == 5
    assert receipt["successful_outputs_equal_exactly"] is True
    assert receipt["failure_codes_equal_exactly"] is True
    assert receipt["universal_equivalence_claimed"] is False


def test_parent_semantic_drift_is_detected(
    validator: ModuleType, source: ModuleType
):
    phys_parent, retail_parent = validator.load_qualified_parent_splitters()
    original = phys_parent.split_physionet_manifest

    def drifted(rows: Any) -> Dict[str, Any]:
        result = original(rows)
        result = copy.deepcopy(result)
        result["record_count"] += 1
        return result

    phys_parent.split_physionet_manifest = drifted
    with pytest.raises(validator.ValidationError, match="semantic drift"):
        validator._splitter_equivalence_receipt(source, phys_parent, retail_parent)


def test_input_permutations_produce_same_snapshot_projection_and_assignment(source: ModuleType):
    for domain, rows in (
        ("physionet-challenge-2012", _phys_rows()),
        ("online-retail-ii", _retail_rows()),
    ):
        reversed_rows = list(reversed(rows))
        first = source.exact_assignment(domain, rows)
        second = source.exact_assignment(domain, reversed_rows)
        assert first == second
        assert source.normalized_projection_sha256(domain, rows) == source.normalized_projection_sha256(domain, reversed_rows)


def test_snapshot_rejects_extra_missing_digest_and_anti_selection_fields(source: ModuleType):
    snapshot, _ = _pair(source, "physionet-challenge-2012", _phys_rows(), "PHYS-D")
    for mutate in (
        lambda row: row.__setitem__("extra", 1),
        lambda row: row.pop("archive_inventory_sha256"),
        lambda row: row.__setitem__("snapshot_manifest_sha256", "0" * 64),
        lambda row: row.__setitem__("post_snapshot_exclusion_count", 1),
        lambda row: row.__setitem__("retry_resplit_topup_count", 1),
    ):
        hostile = copy.deepcopy(snapshot)
        mutate(hostile)
        with pytest.raises(source.ManifestDraftError):
            source.validate_snapshot_manifest(hostile)


def test_split_rejects_crosslink_assignment_and_all_anti_selection_counts(source: ModuleType):
    snapshot, split = _pair(source, "online-retail-ii", _retail_rows(), "RETAIL-D")
    mutators = [
        lambda row: row.__setitem__("snapshot_manifest_sha256", "0" * 64),
        lambda row: row["assignment_output"]["row_assignments"][0].__setitem__("split", "TEST"),
        lambda row: row.__setitem__("splitter_algorithm_id", "OTHER"),
    ] + [lambda row, key=key: row.__setitem__(key, 1) for key in ("exclusion_count", "retry_count", "resplit_count", "top_up_count")]
    for mutate in mutators:
        hostile = copy.deepcopy(split)
        mutate(hostile)
        hostile["split_manifest_sha256"] = source._split_digest(hostile)
        with pytest.raises(source.ManifestDraftError):
            source.validate_split_manifest(hostile, snapshot)


class _StringSubclass(str):
    pass


class _IntegerSubclass(int):
    pass


class _ListSubclass(list):
    pass


class _DictSubclass(dict):
    pass


def test_recursive_exact_builtin_json_types_reject_subclass_impostors(source: ModuleType):
    snapshot, split = _pair(source, "online-retail-ii", _retail_rows(), "RETAIL-E")
    hostile_snapshots = []
    row = copy.deepcopy(snapshot)
    row["schema_version"] = _StringSubclass(row["schema_version"])
    hostile_snapshots.append(row)
    row = _DictSubclass(copy.deepcopy(snapshot))
    hostile_snapshots.append(row)
    row = copy.deepcopy(snapshot)
    row[_StringSubclass("extra")] = None
    hostile_snapshots.append(row)
    for hostile in hostile_snapshots:
        with pytest.raises(source.ManifestDraftError):
            source.validate_snapshot_manifest(hostile)

    hostile_splits = []
    row = copy.deepcopy(split)
    row["allocation_numerators"] = _ListSubclass(row["allocation_numerators"])
    hostile_splits.append(row)
    row = copy.deepcopy(split)
    row["normalized_projection"][0]["row_ordinal"] = _IntegerSubclass(0)
    hostile_splits.append(row)
    row = copy.deepcopy(split)
    row["assignment_output"]["row_assignments"][0]["split"] = _StringSubclass("TRAIN")
    hostile_splits.append(row)
    for hostile in hostile_splits:
        with pytest.raises(source.ManifestDraftError):
            source.validate_split_manifest(hostile, snapshot)


def test_boolean_as_integer_is_rejected_at_every_relevant_seam(source: ModuleType):
    rows = _retail_rows()
    for key in ("row_ordinal", "timestamp_utc_microseconds"):
        hostile = copy.deepcopy(rows)
        hostile[0][key] = True
        with pytest.raises(source.ManifestDraftError):
            source.normalize_projection("online-retail-ii", hostile)
    snapshot, split = _pair(source, "online-retail-ii", rows, "RETAIL-F")
    for target, key in ((snapshot, "raw_snapshot_bytes"), (split, "allocation_denominator"), (split, "retry_count")):
        hostile = copy.deepcopy(target)
        hostile[key] = True
        with pytest.raises(source.ManifestDraftError):
            if target is snapshot:
                source.validate_snapshot_manifest(hostile)
            else:
                source.validate_split_manifest(hostile, snapshot)
    nested = copy.deepcopy(split)
    nested["assignment_output"]["customer_counts"]["TEST"] = True
    with pytest.raises(source.ManifestDraftError):
        source.validate_split_manifest(nested, snapshot)


def test_power_review_state_and_receipt_are_fail_closed(source: ModuleType):
    snapshot, split = _pair(source, "online-retail-ii", _retail_rows(), "RETAIL-G")
    assert split["allocation_power_review_state"] == "NOT_POWER_APPROVED"
    assert split["allocation_power_review_receipt_sha256"] is None
    mutators = (
        lambda row: row.pop("allocation_power_review_state"),
        lambda row: row.__setitem__("allocation_power_review_state", "POWER_APPROVED"),
        lambda row: row.__setitem__("allocation_power_review_receipt_sha256", "1" * 64),
    )
    for mutate in mutators:
        hostile = copy.deepcopy(split)
        mutate(hostile)
        if "split_manifest_sha256" in hostile:
            hostile["split_manifest_sha256"] = source._split_digest(hostile)
        with pytest.raises(source.ManifestDraftError):
            source.validate_split_manifest(hostile, snapshot)


def test_future_structural_record_binds_power_receipt_but_proves_nothing(source: ModuleType):
    snapshot, split = _pair(source, "online-retail-ii", _retail_rows(), "RETAIL-H")
    future_snapshot = copy.deepcopy(snapshot)
    future_snapshot["receipt_state"] = "FUTURE_POPULATED_AFTER_SEPARATE_AUTHORITY"
    future_snapshot["receipt_verification_state"] = "STRUCTURAL_ONLY_NOT_INDEPENDENTLY_VERIFIED"
    future_snapshot["snapshot_version"] = "FUTURE-STRUCTURAL-V1"
    future_snapshot["snapshot_manifest_sha256"] = source._snapshot_digest(future_snapshot)
    source.validate_snapshot_manifest(future_snapshot)

    future_split = copy.deepcopy(split)
    future_split["receipt_state"] = future_snapshot["receipt_state"]
    future_split["receipt_verification_state"] = future_snapshot["receipt_verification_state"]
    future_split["snapshot_manifest_sha256"] = future_snapshot["snapshot_manifest_sha256"]
    future_split["allocation_power_review_state"] = "STRUCTURALLY_BOUND_NOT_INDEPENDENTLY_VERIFIED"
    future_split["allocation_power_review_receipt_sha256"] = "2" * 64
    future_split["split_manifest_sha256"] = source._split_digest(future_split)
    result = source.validate_manifest_pair(future_snapshot, future_split)
    assert result["structural_validation_only"] is True
    assert result["source_license_governance_custody_or_admission_verified"] is False
    assert result["allocation_power_approved"] is False
    assert result["allocation_power_receipt_independently_verified"] is False
    assert result["F061_closed"] is False
    assert result["domain_admitted"] is False

    missing = copy.deepcopy(future_split)
    missing["allocation_power_review_receipt_sha256"] = None
    missing["split_manifest_sha256"] = source._split_digest(missing)
    with pytest.raises(source.ManifestDraftError):
        source.validate_split_manifest(missing, future_snapshot)
    with pytest.raises(source.ManifestDraftError):
        source.build_split_manifest(future_snapshot, _retail_rows())


@pytest.mark.parametrize(
    "domain,rows",
    [
        ("physionet-challenge-2012", [{"record_ordinal": 0, "patient_id": "01"}] * 5),
        ("online-retail-ii", [{"row_ordinal": 0, "customer_key_hex": "A0", "timestamp_utc_microseconds": 0}] * 5),
    ],
)
def test_malformed_normalized_projections_fail_closed(source: ModuleType, domain: str, rows: Any):
    with pytest.raises(source.ManifestDraftError):
        source.normalize_projection(domain, rows)


def test_retail_infeasible_customer_intervals_are_terminal_no_go(source: ModuleType):
    rows = []
    ordinal = 0
    for customer in range(5):
        for timestamp in (0, 100):
            rows.append({"row_ordinal": ordinal, "customer_key_hex": format(customer + 1, "02x"), "timestamp_utc_microseconds": timestamp})
            ordinal += 1
    with pytest.raises(source.ManifestDraftError, match="NO_FEASIBLE"):
        source.exact_assignment("online-retail-ii", rows)


def test_machine_self_digest_noncanonical_and_semantic_mutations_fail(
    validator: ModuleType, tmp_path: Path
):
    root = _copy_package(validator, tmp_path / "package")
    _rewrite_machine(validator, root, lambda row: row["nonclosure"].__setitem__("B03_open", False))
    with pytest.raises(validator.ValidationError):
        validator.validate(root)

    root = _copy_package(validator, tmp_path / "self")
    _rewrite_machine(validator, root, lambda row: row["scope_and_nonclaims"].__setitem__("data_acquired_opened_parsed_snapshotted_or_split", True), recompute=False)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)

    root = _copy_package(validator, tmp_path / "noncanonical")
    _rewrite_machine(validator, root, lambda row: None, canonical=False)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_predecessor_mutation_fails_before_source_execution(validator: ModuleType, tmp_path: Path):
    root = _copy_package(validator, tmp_path / "predecessor")
    target = root / validator.INPUT_SPECS[-1]["path"]
    target.write_bytes(target.read_bytes() + b"# mutation\n")
    target.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="immutable predecessor mismatch"):
        validator.load_qualified_source(root)


def test_effectful_source_substitution_is_rejected_before_execution(validator: ModuleType, tmp_path: Path):
    root = _copy_package(validator, tmp_path / "source")
    sentinel = tmp_path / "must-not-exist"
    malicious = ("from pathlib import Path\nPath(" + repr(str(sentinel)) + ").write_text('bad')\n").encode("utf-8")
    target = root / validator.SOURCE_PATH
    target.write_bytes(malicious)
    target.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="hard-pinned source differs before execution"):
        validator.load_qualified_source(root)
    assert not sentinel.exists()


def test_alternate_pyc_is_ignored_and_never_executed(validator: ModuleType, tmp_path: Path):
    root = _copy_package(validator, tmp_path / "pyc")
    alternate = root / "src/heterodiff/data/__pycache__/dual_domain_snapshot_split_manifest_drafts.cpython-311.pyc"
    alternate.parent.mkdir(parents=True, exist_ok=True)
    alternate.write_bytes(b"not executable and not consulted")
    alternate.chmod(0o644)
    assert validator.validate(root)["validation"] == "PASS"


def test_source_ast_has_no_effectful_route(validator: ModuleType):
    raw = (ROOT / validator.SOURCE_PATH).read_bytes()
    validator._scan_source(raw)
    text = raw.decode("utf-8")
    for token in ("subprocess", "socket", "urllib", "requests", "pathlib", "random", "secrets"):
        assert token not in text


def test_publication_boundary_is_explicitly_internal_only(validator: ModuleType):
    row = validator.build_expected_record()["publication_boundary"]
    assert row["internal_evidence_only"] is True
    assert row["anonymous_or_public_inclusion_permitted"] is False
    assert row["publication_safe_derivative_required"] is True
    assert row["fresh_anonymity_license_and_governance_review_required"] is True
    assert row["real_patient_customer_identifier_timestamp_or_row_present"] is False
    assert row["credentials_tokens_cookies_or_secrets_present"] is False
    assert row["protected_outcome_or_scientific_result_present"] is False
