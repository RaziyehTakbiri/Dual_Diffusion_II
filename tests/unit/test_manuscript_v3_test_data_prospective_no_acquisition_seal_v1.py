"""Hostile tests for the prospective no-test-data-acquisition seal.

All mutations are confined to pytest temporary directories.  The canonical
validator is read-only and never imports a scientific project module.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json"
)
EXPECTED_ITEM_5 = (
    "5- What are the canonical test-data locations, or has test data not yet "
    "been acquired? No test has been acquired. For what purpose de we need it "
    "at all?"
)
EXPECTED_ANSWER = (
    "No test has been acquired. For what purpose de we need it at all?"
)


def _load_validator() -> ModuleType:
    path = ROOT / VALIDATOR_REL
    spec = importlib.util.spec_from_file_location(
        "test_data_prospective_no_acquisition_seal_validator", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _copy_closed_manifest(module: ModuleType, tmp_path: Path) -> Path:
    for rel in module.CLOSED_FILE_ROSTER:
        source = ROOT / rel
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    path.write_bytes(module.canonical_machine_bytes(record))


def test_canonical_registration_validates_and_preserves_null(validator: ModuleType) -> None:
    result = validator.validate()
    assert result["state"] == (
        "NO_TEST_DATA_ACQUIRED_USER_REPORTED_PROSPECTIVE_SEAL_ACTIVE"
    )
    assert result["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert result["effective_unresolved_null_count"] == 172
    assert result["open_blocker_count"] == 12
    assert result["final_test_secrecy_predicate"] is None
    assert result["user_reported"] is True
    assert result["independently_verified"] is False
    assert result["internal_evidence_only"] is True
    assert result["anonymous_or_public_submission_inclusion_permitted"] is False
    assert result["publication_safe_derivative_required"] is True


def test_exact_visible_item_5_and_answer_are_bound(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    item = record["visible_user_item_5"]
    assert item["normalized_question_and_answer"] == EXPECTED_ITEM_5
    assert item["normalized_answer"] == EXPECTED_ANSWER
    assert item["question_and_answer_sha256"] == hashlib.sha256(
        EXPECTED_ITEM_5.encode("utf-8")
    ).hexdigest()
    assert item["answer_sha256"] == hashlib.sha256(
        EXPECTED_ANSWER.encode("utf-8")
    ).hexdigest()
    assert item["normalization"] == (
        "ONLY_TRAILING_TRANSPORT_WHITESPACE_OR_ENTITY_UNBOUND"
    )
    assert item["raw_transport_bytes_bound"] is False
    assert item["cryptographic_user_authentication"] is False


def test_validator_uses_read_only_opens_and_changes_no_bound_byte(
    validator: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = {
        rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel in validator.CLOSED_FILE_ROSTER
    }
    real_open = validator.os.open
    write_mask = (
        os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
    )
    observed = []

    def guarded_open(path: object, flags: int, *args: object) -> int:
        assert flags & write_mask == 0
        observed.append(os.fspath(path))
        return real_open(path, flags, *args)

    monkeypatch.setattr(validator.os, "open", guarded_open)
    validator.validate()
    assert observed
    after = {
        rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel in validator.CLOSED_FILE_ROSTER
    }
    assert after == before


def test_validator_imports_only_standard_library(validator: ModuleType) -> None:
    tree = ast.parse((ROOT / VALIDATOR_REL).read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots <= {
        "__future__",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "stat",
        "typing",
    }


@pytest.mark.parametrize(
    "relative_path",
    [
        "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        (
            "research/fixtures/"
            "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
        ),
        str(VALIDATOR_REL),
        "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py",
    ],
)
def test_any_bound_file_byte_mutation_is_rejected(
    validator: ModuleType, tmp_path: Path, relative_path: str
) -> None:
    root = _copy_closed_manifest(validator, tmp_path)
    target = root / relative_path
    target.write_bytes(target.read_bytes() + b"X")
    with pytest.raises(validator.SealValidationError):
        validator.validate(root)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("visible_user_item_5", "user_reported"), False),
        (("visible_user_item_5", "independently_verified"), True),
        (("custody_projection", "final_test_secrecy_predicate"), False),
        (("custody_projection", "effective_unresolved_null_count"), 171),
        (("observation_boundary", "global_absence_claimed"), True),
        (("observation_boundary", "canonical_test_data_locations"), ["/fake"]),
        (("authority_boundary", "test_data_access_authorized"), True),
        (("authority_boundary", "scientific_execution_authorized"), True),
        (
            (
                "publication_anonymity_boundary",
                "anonymous_or_public_submission_inclusion_permitted",
            ),
            True,
        ),
        (
            ("publication_anonymity_boundary", "internal_evidence_only"),
            False,
        ),
        (("test_data_definition", "unit_test_fixtures_in_scope"), True),
        (
            (
                "required_precontact_protocol",
                "must_be_frozen_and_authorized_before_any_source_contact",
            ),
            False,
        ),
        (("violation_rule", "repair_or_retry_permitted"), True),
    ],
)
def test_semantic_escalations_fail_even_with_recomputed_self_digest(
    validator: ModuleType,
    tmp_path: Path,
    path: tuple[str, str],
    value: Any,
) -> None:
    root = _copy_closed_manifest(validator, tmp_path)

    def mutate(record: Dict[str, Any]) -> None:
        record[path[0]][path[1]] = value

    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.SealValidationError):
        validator.validate(root)


def test_self_digest_tamper_is_rejected(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_manifest(validator, tmp_path)

    def mutate(record: Dict[str, Any]) -> None:
        record["state"] = "TAMPERED"

    _rewrite_machine(validator, root, mutate, recompute_digest=False)
    with pytest.raises(validator.SealValidationError):
        validator.validate(root)


def test_duplicate_key_and_noncanonical_serialization_are_rejected(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_manifest(validator, tmp_path)
    path = root / MACHINE_REL
    original = path.read_bytes()
    path.write_bytes(b'{"schema_version":"duplicate",' + original[1:])
    with pytest.raises(validator.SealValidationError):
        validator.validate(root)

    root = _copy_closed_manifest(validator, tmp_path / "second")
    path = root / MACHINE_REL
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(validator.SealValidationError):
        validator.validate(root)


def test_symlink_and_hardlink_substitution_are_rejected(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_manifest(validator, tmp_path / "symlink")
    target = root / "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
    target.unlink()
    target.symlink_to(ROOT / "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md")
    with pytest.raises(validator.SealValidationError):
        validator.validate(root)


def test_wrong_mode_ancestor_symlink_and_path_swap_are_rejected(
    validator: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_closed_manifest(validator, tmp_path / "mode")
    target = root / "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
    target.chmod(0o600)
    with pytest.raises(validator.SealValidationError, match="mode-not-0644"):
        validator.validate(root)

    root = _copy_closed_manifest(validator, tmp_path / "ancestor")
    research = root / "research"
    real_research = root / "research-real"
    research.rename(real_research)
    research.symlink_to(real_research, target_is_directory=True)
    with pytest.raises(
        validator.SealValidationError, match="ancestor-not-direct-directory"
    ):
        validator.validate(root)

    root = _copy_closed_manifest(validator, tmp_path / "swap")
    target = root / MACHINE_REL
    replacement_bytes = target.read_bytes()
    real_read = validator.os.read
    swapped = False

    def swapping_read(descriptor: int, size: int) -> bytes:
        nonlocal swapped
        if not swapped:
            swapped = True
            target.replace(target.with_name(target.name + ".old"))
            target.write_bytes(replacement_bytes)
            target.chmod(0o644)
        return real_read(descriptor, size)

    monkeypatch.setattr(validator.os, "read", swapping_read)
    with pytest.raises(
        validator.SealValidationError,
        match="path-swap|path-fd-identity-mismatch",
    ):
        validator.validate(root)

    root = _copy_closed_manifest(validator, tmp_path / "hardlink")
    target = root / "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
    os.link(target, root / "extra-link.md")
    with pytest.raises(validator.SealValidationError):
        validator.validate(root)


def test_prospective_protocol_order_and_terminal_violation_are_closed(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    protocol = record["required_precontact_protocol"]
    assert protocol["required_order"] == [
        "FREEZE_AND_AUTHORIZE_PROTOCOL",
        "CONTACT_AND_ACQUIRE_AUTHORIZED_SOURCE",
        "FIX_CONTENT_ADDRESSED_SNAPSHOT",
        "DETERMINISTICALLY_ASSIGN_PARTITIONS_BEFORE_DEVELOPMENT_EXPOSURE",
        "ESCROW_HELD_OUT_PARTITIONS_AND_OUTCOMES",
        "RECORD_EVERY_CONTACT_AND_ACCESS_EVENT",
        "OPEN_ONLY_AFTER_FINAL_SEALED_FREEZE_AUTHORIZATION",
    ]
    assert protocol["access_log_required"] is True
    violation = record["violation_rule"]
    assert violation["terminal_state"] == (
        "PROSPECTIVE_TEST_DATA_SEAL_VIOLATION_TERMINAL"
    )
    assert violation["repair_or_retry_permitted"] is False
    assert violation["evidence_admission_permitted"] is False
    assert violation["claim_promotion_or_submission_permitted"] is False


def test_scientific_test_data_definition_and_publication_boundary_are_closed(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    definition = record["test_data_definition"]
    assert definition["scope"] == (
        "SCIENTIFIC_HELD_OUT_PHYSIONET_AND_RETAIL_MATERIAL_AND_DERIVED_OUTCOMES"
    )
    assert definition["unit_test_fixtures_in_scope"] is False
    assert definition["synthetic_pytest_temporary_files_in_scope"] is False
    assert definition["software_test_material_changes_scientific_custody"] is False

    publication = record["publication_anonymity_boundary"]
    assert publication["internal_evidence_only"] is True
    assert (
        publication["anonymous_or_public_submission_inclusion_permitted"]
        is False
    )
    assert publication["publication_safe_derivative_required"] is True
    assert publication["raw_visible_user_text_in_public_derivative_permitted"] is False
    assert publication["raw_custody_provenance_in_public_derivative_permitted"] is False
    assert publication["fresh_anonymity_audit_required"] is True
    assert set(publication["excluded_from_public_derivative"]) == {
        "VISIBLE_USER_ITEM_5_QUESTION_AND_ANSWER",
        "VISIBLE_USER_ITEM_5_ANSWER",
        "EXACT_CONVERSATION_PROVENANCE",
        "INTERNAL_SOURCE_AND_PACKAGE_PATHS",
        "RAW_AND_RECORD_SHA256_VALUES",
        "BYTE_AND_LF_COUNTS",
        "HISTORICAL_TRACKER_PROVENANCE",
    }


def test_mutable_trackers_are_historical_provenance_not_live_custody(
    validator: ModuleType, tmp_path: Path
) -> None:
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in validator.CLOSED_FILE_ROSTER
    assert "PROJECT_EVIDENCE_LEDGER.md" not in validator.CLOSED_FILE_ROSTER
    root = _copy_closed_manifest(validator, tmp_path)
    result = validator.validate(root)
    assert result["validation"] == "PASS"
    record = json.loads((root / MACHINE_REL).read_text(encoding="ascii"))
    provenance = record["historical_tracker_provenance"]
    assert provenance["live_custody_validated"] is False
    assert provenance["future_tracker_mutation_expected"] is True
    assert provenance["trackers_consume_seal_one_way"] is True


def test_null_and_blocker_counts_are_directly_derived_with_hostiles(
    validator: ModuleType,
) -> None:
    preregistration = json.loads(
        (ROOT / validator.PREREGISTRATION_PATH).read_text(encoding="ascii")
    )
    closure = json.loads(
        (ROOT / validator.CLOSURE_PATH).read_text(encoding="ascii")
    )
    derived = validator.derive_projection(preregistration, closure)
    assert derived["historical_total_null_count"] == 174
    assert derived["historical_preexecution_null_count"] == 168
    assert derived["historical_deferred_postexecution_null_count"] == 6
    assert derived["resolved_pre_d1_pointers"] == [
        "/theory_and_known_law_plan/a1_fixture_parameters",
        "/theory_and_known_law_plan/a1_evaluation_grid",
    ]
    assert derived["effective_preexecution_unresolved_null_count"] == 166
    assert derived["effective_deferred_postexecution_unresolved_null_count"] == 6
    assert derived["effective_total_unresolved_null_count"] == 172
    assert derived["open_confirmatory_execution_blocker_count"] == 10
    assert derived["open_submission_blocker_count"] == 2

    hostile_preregistration = copy.deepcopy(preregistration)
    hostile_preregistration["schema_version"] = None
    with pytest.raises(
        validator.SealValidationError, match="historical-null-count"
    ):
        validator.derive_projection(hostile_preregistration, closure)

    hostile_closure = copy.deepcopy(closure)
    hostile_closure["resolved_pre_d1_fields"].reverse()
    with pytest.raises(
        validator.SealValidationError, match="resolved-pre-d1-pointer-roster"
    ):
        validator.derive_projection(preregistration, hostile_closure)

    hostile_closure = copy.deepcopy(closure)
    hostile_closure["null_projection"][
        "effective_preexecution_unresolved_null_count"
    ] = 165
    with pytest.raises(
        validator.SealValidationError, match="closure-derived-null-mismatch"
    ):
        validator.derive_projection(preregistration, hostile_closure)

    hostile_closure = copy.deepcopy(closure)
    hostile_closure["blocker_projection"]["effective_stage_counts"] = {
        "CONFIRMATORY_EXECUTION": 9,
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 3,
    }
    with pytest.raises(
        validator.SealValidationError, match="blocker-stage-count"
    ):
        validator.derive_projection(preregistration, hostile_closure)
