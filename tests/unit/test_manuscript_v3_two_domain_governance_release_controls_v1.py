"""Hostile qualification for two-domain governance/release controls."""

from __future__ import annotations

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
SOURCE_REL = Path("src/heterodiff/data/two_domain_governance_release_controls.py")
VALIDATOR_REL = Path("research/diagnostics/manuscript_v3_two_domain_governance_release_controls_v1.py")
MACHINE_REL = Path("research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json")


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def controls() -> ModuleType:
    return _load(ROOT / SOURCE_REL, "two_domain_governance_release_controls")


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load(ROOT / VALIDATOR_REL, "two_domain_governance_release_validator")


def _zero_counts(module: ModuleType) -> Dict[str, int]:
    return {key: 0 for key in module.ADMISSION_COMPONENTS}


def _true_receipts(module: ModuleType) -> Dict[str, bool]:
    return {key: True for key in module.REQUIRED_ADMISSION_RECEIPTS}


def _entry(**updates: Any) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "relative_path": "artifacts/result.json",
        "sha256": "1" * 64,
        "release_class": "PUBLIC_AGGREGATE_RESULT",
        "contains_source_data": False,
        "contains_natural_group_identifier": False,
        "contains_row_level_prediction_or_sample": False,
        "contains_secret_or_credential": False,
        "contains_internal_absolute_path": False,
        "contains_author_identity_or_affiliation": False,
    }
    value.update(updates)
    return value


def _manifest(entries: list[dict[str, Any]], **updates: Any) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "entries": entries,
        "license_attribution_review_passed": True,
        "privacy_review_passed": True,
        "membership_inference_review_passed": True,
        "absolute_path_scan_passed": True,
        "secret_scan_passed": True,
        "identity_scan_passed": True,
        "venue_anonymity_scan_passed": True,
        "final_owner_release_approval_present": True,
    }
    value.update(updates)
    return value


def test_canonical_package_validates_exact_bounded_delta(validator: ModuleType) -> None:
    status = validator.validate(ROOT)
    assert status["validation"] == "PASS"
    assert status["fields_closed"] == list(validator.FIELDS_CLOSED)
    assert status["pre_execution_fields_closed"] == 15
    assert status["post_execution_fields_closed"] == 2
    assert status["blockers_closed"] == 0
    assert status["blockers_remaining_open"] == ["B02", "B03", "B09", "B10", "B11"]
    assert status["data_or_external_action_performed"] is False


def test_machine_is_canonical_self_bound_and_exact(validator: ModuleType) -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert raw == validator.canonical_machine_bytes(record)
    assert record["record_sha256"] == validator.record_sha256(record)
    assert record == validator.expected_record(ROOT)
    assert record["field_delta"] == {
        "field_ids": list(validator.FIELDS_CLOSED),
        "pre_execution": 15,
        "post_execution": 2,
        "total": 17,
        "blockers_closed": 0,
    }
    assert record["additive_count_transition"]["before"] == {"pre_execution_open": 122, "pre_execution_closed": 44, "post_execution_open": 3, "post_execution_closed": 3, "total_open": 125, "total_closed": 47}
    assert record["additive_count_transition"]["after"] == {"pre_execution_open": 107, "pre_execution_closed": 59, "post_execution_open": 1, "post_execution_closed": 5, "total_open": 108, "total_closed": 64}


def test_package_bindings_cover_all_nonmachine_files(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    bindings = record["package_bindings_excluding_machine_self"]
    assert [row["role"] for row in bindings] == [
        "pure_source", "human_contract", "validator", "hostile_tests"
    ]
    for row in bindings:
        raw = (ROOT / row["path"]).read_bytes()
        assert row["bytes"] == len(raw)
        assert row["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["mode_octal"] == "0644"
        assert row["nlink"] == 1
        assert row["terminal_lf"] is True


@pytest.mark.parametrize(
    ("source", "observed", "expected"),
    [([], [], 0), ([0], [], 1), ([0], [0], 1), ([0, 2, 9], [0, 9], 3)],
)
def test_half_thinning_exact_mass_exponent(
    controls: ModuleType, source: list[int], observed: list[int], expected: int
) -> None:
    assert controls.half_thinning_mass_exponent(source, observed) == expected


def test_half_thinning_rejects_off_support_without_repair(controls: ModuleType) -> None:
    assert controls.half_thinning_mass_exponent([0, 2], [1]) is None


@pytest.mark.parametrize(
    ("source", "observed"),
    [((0,), []), ([0, 0], []), ([1, 0], []), ([False], []), ([0], [True]), ([0], [0, 0])],
)
def test_half_thinning_strict_carriers(
    controls: ModuleType, source: object, observed: object
) -> None:
    with pytest.raises(controls.ContractError):
        controls.half_thinning_mass_exponent(source, observed)


def test_admission_passes_only_exact_zero_with_all_receipts(controls: ModuleType) -> None:
    result = controls.evaluate_training_admission(
        controls.PHYSIONET_DOMAIN, _zero_counts(controls), _true_receipts(controls)
    )
    assert result == {
        "domain_id": controls.PHYSIONET_DOMAIN,
        "statistic_id": controls.ADMISSION_STATISTIC_ID,
        "threshold_id": controls.ADMISSION_THRESHOLD_ID,
        "maximum_hard_violation_count": 0,
        "nonzero_components": [],
        "missing_required_receipts": [],
        "decision": "ADMIT",
    }


def test_admission_is_no_go_for_any_count_or_missing_receipt(controls: ModuleType) -> None:
    counts = _zero_counts(controls)
    counts["row_exclusions"] = 1
    receipts = _true_receipts(controls)
    receipts["governance_approval_verified"] = False
    result = controls.evaluate_training_admission(
        controls.RETAIL_DOMAIN, counts, receipts
    )
    assert result["decision"] == "NO_GO"
    assert result["maximum_hard_violation_count"] == 1
    assert result["nonzero_components"] == ["row_exclusions"]
    assert result["missing_required_receipts"] == ["governance_approval_verified"]


def test_admission_rejects_extra_reordered_and_boolean_counts(controls: ModuleType) -> None:
    counts = _zero_counts(controls)
    counts["extra"] = 0
    with pytest.raises(controls.ContractError):
        controls.evaluate_training_admission(
            controls.PHYSIONET_DOMAIN, counts, _true_receipts(controls)
        )
    reordered = dict(reversed(list(_zero_counts(controls).items())))
    with pytest.raises(controls.ContractError):
        controls.evaluate_training_admission(
            controls.PHYSIONET_DOMAIN, reordered, _true_receipts(controls)
        )
    boolean = _zero_counts(controls)
    boolean["identity_failures"] = False
    with pytest.raises(controls.ContractError):
        controls.evaluate_training_admission(
            controls.PHYSIONET_DOMAIN, boolean, _true_receipts(controls)
        )


def test_release_manifest_pass_is_eligibility_not_release(controls: ModuleType) -> None:
    result = controls.evaluate_release_manifest(_manifest([_entry()]))
    assert result["decision"] == "RELEASE_ELIGIBLE_FOR_SEPARATE_OWNER_ACTION"
    assert result["release_performed"] is False
    assert result["public_entry_count"] == 1


def test_sensitive_public_entry_and_missing_gate_fail_closed(controls: ModuleType) -> None:
    public = _entry(contains_natural_group_identifier=True)
    result = controls.evaluate_release_manifest(
        _manifest([public], venue_anonymity_scan_passed=False)
    )
    assert result["decision"] == "NO_GO"
    assert result["prohibited_public_entries"] == [{
        "relative_path": "artifacts/result.json",
        "reasons": ["contains_natural_group_identifier"],
    }]
    assert result["failed_gates"] == ["venue_anonymity_scan_passed"]


def test_sensitive_internal_entry_is_not_public_but_still_requires_gates(controls: ModuleType) -> None:
    internal = _entry(
        release_class="INTERNAL_RESTRICTED",
        contains_source_data=True,
        contains_natural_group_identifier=True,
    )
    result = controls.evaluate_release_manifest(_manifest([internal]))
    assert result["decision"] == "RELEASE_ELIGIBLE_FOR_SEPARATE_OWNER_ACTION"
    assert result["public_entry_count"] == 0
    assert result["release_performed"] is False


@pytest.mark.parametrize(
    "entry",
    [
        _entry(relative_path="/tmp/result.json"),
        _entry(relative_path="artifacts/../result.json"),
        _entry(relative_path="artifacts//result.json"),
        _entry(relative_path="artifacts/result json"),
        _entry(sha256="A" * 64),
        _entry(release_class="PUBLIC_RAW_DATA"),
        _entry(contains_source_data=0),
    ],
)
def test_release_manifest_rejects_malformed_entries(
    controls: ModuleType, entry: dict[str, Any]
) -> None:
    with pytest.raises(controls.ContractError):
        controls.evaluate_release_manifest(_manifest([entry]))


def test_release_manifest_rejects_duplicate_paths_and_empty_roster(controls: ModuleType) -> None:
    with pytest.raises(controls.ContractError):
        controls.evaluate_release_manifest(_manifest([_entry(), _entry()]))
    assert controls.evaluate_release_manifest(_manifest([]))["decision"] == "NO_GO"


def _copy_package(validator: ModuleType, target: Path) -> Path:
    for relative in list(validator.PACKAGE_ROSTER) + [row[0] for row in validator.PREDECESSOR_BINDINGS]:
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    return target


def test_root_symlink_is_rejected(validator: ModuleType, tmp_path: Path) -> None:
    root = _copy_package(validator, tmp_path / "replica")
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(validator.ValidationError):
        validator.validate(alias)


def test_machine_hardlink_is_rejected(validator: ModuleType, tmp_path: Path) -> None:
    root = _copy_package(validator, tmp_path / "replica")
    path = root / MACHINE_REL
    sibling = root / "machine-link.json"
    path.rename(sibling)
    os.link(sibling, path)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_leaf_mode_and_predecessor_drift_are_rejected(validator: ModuleType, tmp_path: Path) -> None:
    root = _copy_package(validator, tmp_path / "mode")
    (root / SOURCE_REL).chmod(0o600)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)
    root = _copy_package(validator, tmp_path / "predecessor")
    predecessor = root / validator.PREDECESSOR_BINDINGS[0][0]
    predecessor.write_bytes(predecessor.read_bytes() + b"# drift\n")
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_disguised_effect_source_is_inert_syntax(validator: ModuleType, tmp_path: Path) -> None:
    sentinel = tmp_path / "effect"
    raw = (ROOT / SOURCE_REL).read_bytes() + (
        "\ndef disguised(value=__import__('pathlib').Path(%r).write_text('ran')):\n    return value\n"
        % str(sentinel)
    ).encode()
    constants = validator._load_source_namespace(raw)
    assert constants["OBSERVATION_KERNEL_ID"] == "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1"
    assert not sentinel.exists()


def test_source_is_captured_once_for_literal_extraction(validator: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    original = validator._read_regular_no_follow
    seen = []
    def tracked(root: Path, relative: str):
        if relative == validator.SOURCE_PATH:
            seen.append(relative)
        return original(root, relative)
    monkeypatch.setattr(validator, "_read_regular_no_follow", tracked)
    validator.validate(ROOT)
    assert seen == [validator.SOURCE_PATH]


def test_required_source_constants_reject_duplicate_missing_and_nonliteral(validator: ModuleType) -> None:
    raw = (ROOT / SOURCE_REL).read_bytes()
    with pytest.raises(validator.ValidationError):
        validator._load_source_namespace(raw + b"\nOBSERVATION_KERNEL_ID = 'duplicate'\n")
    with pytest.raises(validator.ValidationError):
        validator._load_source_namespace(raw.replace(b"OBSERVATION_KERNEL_ID =", b"RENAMED_KERNEL_ID =", 1))
    with pytest.raises(validator.ValidationError):
        validator._load_source_namespace(raw.replace(b'OBSERVATION_KERNEL_ID = "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1"', b'OBSERVATION_KERNEL_ID = str("dynamic")', 1))


def _rewrite_machine(
    validator: ModuleType,
    root: Path,
    mutation: Callable[[Dict[str, Any]], None],
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutation(record)
    record["record_sha256"] = validator.record_sha256(record)
    path.write_bytes(validator.canonical_machine_bytes(record))
    path.chmod(0o644)


def test_recomputed_semantic_digest_does_not_authorize_overclaim(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_package(validator, tmp_path / "replica")
    _rewrite_machine(
        validator,
        root,
        lambda record: record["blocker_assessment"].update({"B09": "CLOSED"}),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_source_mutation_is_detected_by_binding(validator: ModuleType, tmp_path: Path) -> None:
    root = _copy_package(validator, tmp_path / "replica")
    source_path = root / SOURCE_REL
    source_path.write_bytes(source_path.read_bytes() + b"# drift\n")
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_intermediate_symlink_traversal_is_rejected(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_package(validator, tmp_path / "replica")
    real_src = root / "real-src"
    shutil.move(str(root / "src"), real_src)
    (root / "src").symlink_to(real_src, target_is_directory=True)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_every_closed_field_has_unique_pointer_and_exact_status(validator: ModuleType) -> None:
    closures = validator.field_closures()
    assert [row["field_id"] for row in closures] == list(validator.FIELDS_CLOSED)
    assert len({row["json_pointer"] for row in closures}) == len(closures)
    assert all(
        row["status"] == "CLOSED_BY_ADDITIVE_PREOUTCOME_CONTROL_FREEZE"
        for row in closures
    )


def test_license_records_do_not_infer_approval_or_page_hash(validator: ModuleType) -> None:
    closures = {row["field_id"]: row["value"] for row in validator.field_closures()}
    for field in ("F021", "F040"):
        assert closures[field]["page_bytes_or_transport_hash_claimed"] is False
        assert closures[field]["governance_approval_inferred"] is False
    assert closures["F021"]["license_short_name"] == "ODC-By-1.0"
    assert closures["F040"]["license_short_name"] == "CC-BY-4.0"


def test_all_event_dependent_blockers_remain_explicitly_open(validator: ModuleType) -> None:
    record = validator.expected_record(ROOT)
    assert record["blocker_assessment"]["closable_now_count"] == 0
    assert set(record["blocker_assessment"]) == {
        "B02", "B03", "B09", "B10", "B11", "closable_now_count"
    }
    assert all(
        record["blocker_assessment"][blocker].startswith("OPEN_")
        for blocker in ("B02", "B03", "B09", "B10", "B11")
    )
