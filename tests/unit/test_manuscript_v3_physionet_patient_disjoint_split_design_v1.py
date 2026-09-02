"""Hostile synthetic qualification for the PhysioNet split-design quartet."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import stat
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / (
    "research/diagnostics/"
    "manuscript_v3_physionet_patient_disjoint_split_design_v1.py"
)
MACHINE_PATH = ROOT / (
    "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json"
)
HUMAN_PATH = ROOT / "PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md"

SPEC = importlib.util.spec_from_file_location("physionet_split_design_v1", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def rows_for_patients(*patient_ids: str):
    return [
        {"record_ordinal": ordinal, "patient_id": patient_id}
        for ordinal, patient_id in enumerate(patient_ids)
    ]


def canonical_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def assert_error(code, value):
    with pytest.raises(MODULE.PhysioNetSplitDesignError, match="^{}$".format(code)):
        MODULE.split_physionet_manifest(value)


def test_authority_text_digest_and_length_are_exact():
    raw = MODULE.NORMALIZED_AUTHORITY_TEXT.encode("utf-8")
    assert len(raw) == 92
    assert hashlib.sha256(raw).hexdigest() == MODULE.NORMALIZED_AUTHORITY_SHA256


@pytest.mark.parametrize(
    ("patient_count", "expected"),
    [
        (5, {"TRAIN": 3, "VALIDATION": 1, "TEST": 1}),
        (6, {"TRAIN": 4, "VALIDATION": 1, "TEST": 1}),
        (7, {"TRAIN": 5, "VALIDATION": 1, "TEST": 1}),
        (8, {"TRAIN": 6, "VALIDATION": 1, "TEST": 1}),
        (9, {"TRAIN": 6, "VALIDATION": 2, "TEST": 1}),
        (10, {"TRAIN": 7, "VALIDATION": 2, "TEST": 1}),
        (11, {"TRAIN": 8, "VALIDATION": 2, "TEST": 1}),
    ],
)
def test_hamilton_counts(patient_count, expected):
    assert MODULE._hamilton_counts(patient_count) == expected


def test_constructive_assignment_is_complete_and_disjoint():
    rows = rows_for_patients("1", "2", "3", "4", "5", "6", "7")
    result = MODULE.split_physionet_manifest(rows)
    assert result["outcome"] == "PASS"
    assert result["patient_count"] == 7
    assert result["record_count"] == 7
    assert result["patient_counts"] == {"TRAIN": 5, "VALIDATION": 1, "TEST": 1}
    assert sum(result["record_counts"].values()) == 7
    assert {row["record_ordinal"] for row in result["record_assignments"]} == set(
        range(7)
    )
    split_sets = {
        split: {
            row["patient_id"]
            for row in result["patient_assignments"]
            if row["split"] == split
        }
        for split in MODULE.SPLITS
    }
    assert set.union(*split_sets.values()) == {str(i) for i in range(1, 8)}
    assert all(
        split_sets[a].isdisjoint(split_sets[b])
        for index, a in enumerate(MODULE.SPLITS)
        for b in MODULE.SPLITS[index + 1 :]
    )


def test_multiple_records_for_one_patient_never_cross_splits():
    rows = rows_for_patients("1", "2", "1", "3", "4", "2", "5")
    result = MODULE.split_physionet_manifest(rows)
    observed = {}
    for row in result["record_assignments"]:
        observed.setdefault(row["patient_id"], set()).add(row["split"])
    assert all(len(values) == 1 for values in observed.values())
    assert result["record_count"] == len(rows)


def test_input_list_permutation_does_not_change_output():
    rows = rows_for_patients("11", "2", "7", "4", "9", "1", "8")
    permuted = [rows[index] for index in (5, 2, 6, 0, 4, 1, 3)]
    assert MODULE.split_physionet_manifest(rows) == MODULE.split_physionet_manifest(
        permuted
    )


def test_injected_hash_collision_uses_canonical_patient_bytes(monkeypatch):
    monkeypatch.setattr(MODULE, "_patient_order_digest", lambda _: b"\x00" * 32)
    result = MODULE.split_physionet_manifest(rows_for_patients("5", "2", "4", "1", "3"))
    split_by_patient = {
        row["patient_id"]: row["split"] for row in result["patient_assignments"]
    }
    assert split_by_patient == {
        "1": "TRAIN",
        "2": "TRAIN",
        "3": "TRAIN",
        "4": "VALIDATION",
        "5": "TEST",
    }


def test_patient_order_preimage_is_literal_and_length_prefixed():
    assert len(b"heterodiff/physionet-patient-order/v1") == 37
    assert len(MODULE.PATIENT_ORDER_DOMAIN) == 38
    patient = b"123"
    expected = hashlib.sha256(
        b"heterodiff/physionet-patient-order/v1\x00" + b"\x00\x03" + patient
    ).digest()
    assert MODULE._patient_order_digest(patient) == expected


def test_input_and_assignment_digests_recompute_exactly():
    rows = rows_for_patients("1", "2", "3", "4", "5")
    result = MODULE.split_physionet_manifest(rows)
    normalized = sorted(rows, key=lambda row: row["record_ordinal"])
    assert (
        result["input_manifest_sha256"]
        == hashlib.sha256(
            MODULE.INPUT_DIGEST_DOMAIN + canonical_bytes(normalized)
        ).hexdigest()
    )
    payload = dict(result)
    digest = payload.pop("assignment_manifest_sha256")
    assert (
        digest
        == hashlib.sha256(
            MODULE.ASSIGNMENT_DIGEST_DOMAIN + canonical_bytes(payload)
        ).hexdigest()
    )


@pytest.mark.parametrize(
    "value",
    [
        None,
        (),
        {},
        [],
        [None],
        [{"record_ordinal": 0}],
        [{"patient_id": "1"}],
        [{"record_ordinal": 0, "patient_id": "1", "label": 0}],
        [{"record_ordinal": True, "patient_id": "1"}],
        [{"record_ordinal": 0.0, "patient_id": "1"}],
        [{"record_ordinal": -1, "patient_id": "1"}],
        [
            {"record_ordinal": 0, "patient_id": "1"},
            {"record_ordinal": 0, "patient_id": "2"},
        ],
        [
            {"record_ordinal": 0, "patient_id": "1"},
            {"record_ordinal": 2, "patient_id": "2"},
        ],
    ],
)
def test_malformed_row_or_ordinal_is_refused(value):
    assert_error("INVALID_NORMALIZED_MANIFEST", value)


@pytest.mark.parametrize(
    "patient_id",
    [
        None,
        True,
        1,
        "",
        "0",
        "00",
        "01",
        "+1",
        "-1",
        " 1",
        "1 ",
        "1\n",
        "\u0661",
        "abc",
        "1" * 65,
    ],
)
def test_invalid_or_alias_patient_id_is_refused(patient_id):
    rows = rows_for_patients("1", "2", "3", "4", "5")
    rows[0]["patient_id"] = patient_id
    assert_error("INVALID_NORMALIZED_MANIFEST", rows)


@pytest.mark.parametrize(
    "extra", ["label", "outcome", "prediction", "loss", "test_indicator"]
)
def test_outcome_bearing_or_extra_fields_are_refused(extra):
    rows = rows_for_patients("1", "2", "3", "4", "5")
    rows[0][extra] = 0
    assert_error("INVALID_NORMALIZED_MANIFEST", rows)


def test_fewer_than_five_unique_patients_is_terminal_no_go():
    assert_error(
        "INSUFFICIENT_PATIENT_GROUPS",
        rows_for_patients("1", "2", "3", "4", "1", "2"),
    )


def test_splitter_does_not_need_any_file_open(monkeypatch):
    def bomb(*_args, **_kwargs):
        raise AssertionError("splitter attempted filesystem access")

    monkeypatch.setattr(MODULE.os, "open", bomb)
    assert (
        MODULE.split_physionet_manifest(rows_for_patients("1", "2", "3", "4", "5"))[
            "outcome"
        ]
        == "PASS"
    )


def test_expected_record_has_exact_zero_effect_boundary():
    record = MODULE.build_expected_record(ROOT)
    effects = record["checklist_effects"]
    assert effects["project_control_predicate"] == MODULE.CONTROL_PREDICATE
    assert effects["project_control_predicate_value_after_validation"] is True
    assert effects["scientific_effect"] == 0
    assert effects["unresolved_fields_closed"] == 0
    assert effects["blockers_closed"] == 0
    assert effects["formal_tests_closed"] == 0
    assert effects["results_filled"] == 0
    assert effects["F058_closed"] is False and effects["F058_value"] is None
    assert effects["F061_closed"] is False and effects["F061_value"] is None
    assert effects["B02_closed"] is False and effects["B07_closed"] is False
    assert effects["original_populated_instance_checkbox_closed"] is False


def test_scope_and_authority_remain_narrow():
    record = MODULE.build_expected_record(ROOT)
    authority = record["authority_provenance"]
    scope = record["scope_and_nonclaims"]
    assert authority["renewed_scope_review_for_one_bounded_physionet_design_package"]
    assert authority["renewed_scope_review_interpretation_is_agent_adjudication"]
    assert authority["data_access_or_download_authorized"] is False
    assert (
        authority[
            "dataset_documentation_license_governance_or_approval_contact_authorized"
        ]
        is False
    )
    assert authority["escrow_operation_authorized"] is False
    assert authority["runtime_or_scientific_execution_authorized"] is False
    assert authority["scientific_entropy_authorized"] is False
    assert authority["tracker_edit_performed_by_this_package"] is False
    assert scope["populated_precontact_instance_present_or_admitted"] is False
    assert scope["real_split_or_escrow_operation_performed"] is False
    assert scope["tracker_reverse_binding_present"] is False
    assert scope["preexisting_scientific_or_runtime_project_code_imported"] is False
    context = record["local_design_context_provenance"]
    assert context["read_only_text_inspection_performed"] is True
    assert context["preexisting_source_imported_or_executed"] is False
    assert context["official_source_schema_dataset_or_contact_evidence"] is False


def test_exact_predecessor_roster_and_one_way_package_binding():
    record = MODULE.build_expected_record(ROOT)
    assert len(record["live_immutable_input_bindings"]) == 24
    assert [row["ordinal"] for row in record["live_immutable_input_bindings"]] == list(
        range(24)
    )
    assert [row["ordinal"] for row in record["package_bindings"]] == [0, 1, 2]
    assert {row["path"] for row in record["package_bindings"]} == {
        HUMAN_PATH.relative_to(ROOT).as_posix(),
        MODULE_PATH.relative_to(ROOT).as_posix(),
        Path(__file__).resolve().relative_to(ROOT).as_posix(),
    }
    serialized = canonical_bytes(record)
    assert b"PROJECT_COMPLETION_TIMETABLE" not in serialized
    assert b"PROJECT_EVIDENCE_LEDGER" not in serialized


def test_machine_record_is_canonical_closed_and_self_digested():
    raw = MACHINE_PATH.read_bytes()
    assert raw.endswith(b"\n")
    record = json.loads(raw)
    expected = MODULE.validate_record_mapping(record, ROOT)
    assert raw == MODULE._canonical_json_bytes(expected, trailing_lf=True)
    assert record["record_sha256"] == MODULE._record_self_digest(record)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("checklist_effects", "F058_closed"), True),
        (
            ("checklist_effects", "F061_value"),
            {"TRAIN": 70, "VALIDATION": 15, "TEST": 15},
        ),
        (("checklist_effects", "blockers_closed"), False),
        (("authority_provenance", "data_access_or_download_authorized"), True),
        (
            (
                "scope_and_nonclaims",
                "dataset_source_license_governance_or_approval_contacted",
            ),
            True,
        ),
        (("scope_and_nonclaims", "tracker_reverse_binding_present"), True),
        (("design_identity", "real_split_performed"), True),
        (("predecessor_effects", "approval_contact_roster_completed"), True),
    ],
)
def test_machine_record_hostile_mutations_fail_closed(path, value):
    record = MODULE.build_expected_record(ROOT)
    cursor = record
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(MODULE.CustodyError):
        MODULE.validate_record_mapping(record, ROOT)


def test_machine_record_extra_or_missing_key_fails_closed():
    record = MODULE.build_expected_record(ROOT)
    extra = copy.deepcopy(record)
    extra["surprise"] = False
    with pytest.raises(MODULE.CustodyError):
        MODULE.validate_record_mapping(extra, ROOT)
    missing = copy.deepcopy(record)
    del missing["failure_contract"]
    with pytest.raises(MODULE.CustodyError):
        MODULE.validate_record_mapping(missing, ROOT)


def test_full_canonical_audit_passes():
    result = MODULE.audit_canonical_workspace(ROOT)
    assert result["status"] == "PASS_STATIC_DESIGN_ONLY_NO_DATA_ACCESS"
    assert result["control_predicate"] == MODULE.CONTROL_PREDICATE


def test_package_files_are_regular_single_link_ascii_lf():
    for path in (HUMAN_PATH, MACHINE_PATH, MODULE_PATH, Path(__file__).resolve()):
        status = path.lstat()
        assert stat.S_ISREG(status.st_mode)
        assert stat.S_IMODE(status.st_mode) == 0o644
        assert status.st_nlink == 1
        raw = path.read_bytes()
        assert raw.endswith(b"\n")
        raw.decode("ascii")


def test_sources_have_no_network_process_entropy_or_project_imports():
    forbidden_import_roots = {
        "asyncio",
        "http",
        "multiprocessing",
        "random",
        "requests",
        "secrets",
        "socket",
        "subprocess",
        "urllib",
    }
    for path in (MODULE_PATH, Path(__file__).resolve()):
        tree = ast.parse(path.read_text(encoding="ascii"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                assert not roots & forbidden_import_roots
                assert "heterodiff" not in roots
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                assert root not in forbidden_import_roots
                assert root != "heterodiff"


def test_validator_has_no_file_writer_calls_and_os_open_is_read_only():
    source = MODULE_PATH.read_text(encoding="ascii")
    tree = ast.parse(source, filename=str(MODULE_PATH))
    for forbidden_flag in ("O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND"):
        assert forbidden_flag not in source
    assert "flags = os.O_RDONLY" in source
    forbidden_attrs = {
        "chmod",
        "mkdir",
        "open",
        "rename",
        "replace",
        "rmdir",
        "symlink",
        "touch",
        "truncate",
        "unlink",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "exec", "eval", "compile", "__import__"}
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                if node.func.attr == "open":
                    assert len(node.args) >= 2
                    continue
                assert node.func.attr not in forbidden_attrs
            elif node.func.attr in forbidden_attrs:
                pytest.fail(
                    "validator exposes file writer call: {}".format(node.func.attr)
                )


def test_human_record_contains_no_local_absolute_path_or_completion_overclaim():
    text = HUMAN_PATH.read_text(encoding="ascii")
    assert "/Users/" not in text
    assert "F058, F061" in text
    assert "remain open" in text
    assert "Real PhysioNet data or source accessed:** no" in text
    assert "populated-precontact checkbox" in text
