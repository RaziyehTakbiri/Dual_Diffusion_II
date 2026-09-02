#!/usr/bin/env python3
"""Read-only validator for the B02 PhysioNet public-documentation gap package."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import sys
from typing import Any, Dict, Iterable, Tuple


SCHEMA = "heterodiff-manuscript-v3-b02-physionet-public-documentation-gap-v1"
STATUS = "CANDIDATE_PUBLIC_DOCUMENTATION_AND_EXACT_FUTURE_RECEIPT_CHECKLIST_ONLY"
MACHINE_PATH = "research/fixtures/manuscript_v3_b02_physionet_public_documentation_gap_v1.json"
HUMAN_PATH = "PROJECT_B02_PHYSIONET_PUBLIC_DOCUMENTATION_GAP.md"
SOURCE_PATH = "src/heterodiff/data/physionet_2012_admission_preflight.py"
SOURCE_TEST_PATH = "tests/unit/test_physionet_2012_admission_preflight.py"

FILE_BINDINGS = {
    HUMAN_PATH: (9442, "7f08e2f09bfe83e3daf28ba3dd6b736e095e235bead90fcba559dcde6fc33c75"),
    MACHINE_PATH: (11977, "e83e1c65855b1f32c374bbc8941b9f4e623918cc5f21d76b4afddc9bfe50715f"),
    SOURCE_PATH: (136305, "bf5c12dcb5debe99533d00a813d7b522c42b588f5431803a8c2bac99b0f2bf07"),
    SOURCE_TEST_PATH: (67299, "25786cf1d2bc971c8b8f08c2aabc18fa192ed7b75fd67944486238fb83c8d57c"),
    "src/heterodiff/data/two_domain_external_evidence_intake.py": (
        68846,
        "ede0c1890d1e1f39a522a064fe94a78ab65fe5618687ca525c05b4cba7001d85",
    ),
    "research/fixtures/manuscript_v3_b02_b03_b09_external_evidence_intake_v1.json": (
        11920,
        "af4d46e652d24d71382a746e3a043491c2f978275098e266e6f77f4286906a9f",
    ),
    "src/heterodiff/data/two_domain_governance_release_controls.py": (
        9720,
        "8c5a1d74194a5cd1dbae1784360df2bffe392430bd48d74b1846fba6de802cef",
    ),
    "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json": (
        1924,
        "906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d",
    ),
}

EXPECTED_RECORD_SHA256 = "1ea241dcfeddbdefe6eb390e128e41ddcc972c25c0850f0dcc8ced6d0689d12c"
EXPECTED_FROZEN_FIELDS = (
    "F021", "F023", "F024", "F025", "F026", "F027", "F028",
    "F029", "F030", "F031", "F032", "F035", "F036", "F037",
)
EXPECTED_PLAN_FIELDS = ("F163", "F166", "F167")

EXPECTED_PUBLIC_OBSERVATION = {
    "observation_date_local_unattested": "2026-09-02",
    "official_root_url": "https://physionet.org/content/challenge-2012/1.0.0/",
    "official_file_metadata_url": "https://physionet.org/content/challenge-2012/1.0.0/set-a.tar.gz",
    "official_license_url": "https://physionet.org/content/challenge-2012/view-license/1.0.0/",
    "dataset_title": "Predicting Mortality of ICU Patients: The PhysioNet/Computing in Cardiology Challenge 2012",
    "displayed_version": "1.0.0",
    "displayed_published_date": "2012-01-20",
    "displayed_access_class": "Challenge Open Access",
    "displayed_access_policy": "Anyone can access the files, as long as they conform to the terms of the specified license.",
    "displayed_file_license": "Open Data Commons Attribution License v1.0",
    "displayed_set_a_archive_relative_path": "set-a.tar.gz",
    "displayed_set_a_archive_byte_count": 6632372,
    "displayed_set_a_record_count": 4000,
    "displayed_set_a_outcomes_available": True,
    "observed_page_published_raw_archive_sha256": None,
    "raw_page_bytes_captured": False,
    "raw_page_sha256": None,
    "dataset_archive_downloaded": False,
    "dataset_archive_sha256_computed": False,
    "governance_approval_authenticated": False,
    "accountable_owner_acceptance_authenticated": False,
    "field_closure_supported_by_this_observation": [],
}

EXPECTED_OPEN_FIELDS: Tuple[Tuple[str, str, str], ...] = (
    (
        "F019",
        "/domains/0/snapshot_version",
        "EXACT_ACQUIRED_ALLOWLISTED_SNAPSHOT_VERSION_RECEIPT_BOUND_TO_ONE_ARCHIVE_AND_MANIFEST",
    ),
    (
        "F020",
        "/domains/0/raw_snapshot_sha256",
        "SHA256_OF_THE_EXACT_ACQUIRED_RAW_ALLOWLISTED_SNAPSHOT_WITH_BYTE_COUNT_AND_INDEPENDENT_VERIFICATION",
    ),
    (
        "F022",
        "/domains/0/governance_approval_record",
        "AUTHENTICATED_APPLICABLE_GOVERNANCE_DETERMINATION_AND_ACCOUNTABLE_OWNER_ACCEPTANCE",
    ),
    (
        "F033",
        "/domains/0/observation_reference",
        "CONTENT_ADDRESSED_OBSERVATION_REFERENCE_AND_ACQUISITION_JUSTIFICATION_RECEIPT",
    ),
    (
        "F034",
        "/domains/0/positive_or_common_support_route",
        "FULL_SUPPORT_COMPONENT_PROOF_IMPLEMENTATION_CERTIFICATE_AND_INDEPENDENT_REVIEW_BOUND_TO_THE_EXACT_OBSERVATION_REFERENCE",
    ),
    (
        "F058",
        "/split_and_leakage_plan/physionet_split_manifest_path",
        "PRIVATE_CONTENT_ADDRESSED_COMPLETE_PATIENT_DISJOINT_SPLIT_MANIFEST_FROM_THE_EXACT_VERIFIED_SNAPSHOT",
    ),
)

EXPECTED_CHECKLIST: Tuple[Tuple[str, str, str], ...] = (
    (
        "PHYS-E01-EXTERNAL-PRINCIPALS",
        "EXTERNAL_INTAKE",
        "ASSIGN_NINE_PAIRWISE_DISTINCT_REAL_OPAQUE_PRINCIPALS_AND_OBTAIN_NINE_EXTERNALLY_AUTHENTICATED_ROLE_ACCEPTANCES",
    ),
    (
        "PHYS-E02-DEFINITION-AND-CUSTODY-RECORDS",
        "EXTERNAL_INTAKE",
        "AUTHENTICATE_SELECTOR_CONTACT_APPROVAL_VALIDATOR_CONFLICT_ESCROW_KEY_AND_ACL_RECORDS_UNDER_THE_ACCEPTED_INTAKE_CONTRACT",
    ),
    (
        "PHYS-A01-POPULATED-PRECONTACT-REVIEW",
        "PRECONTACT",
        "POPULATE_INDEPENDENTLY_REVIEW_AND_ADMIT_THE_EXACT_FINITE_PRECONTACT_INSTANCE",
    ),
    (
        "PHYS-A02-FRESH-ADMIN-AUTHORITY",
        "PRECONTACT",
        "RECORD_FRESH_EXACT_AUTHORITY_FOR_THE_ADMITTED_ADMINISTRATIVE_CONTACT_ROSTER_BEFORE_ANY_OPERATION",
    ),
    (
        "PHYS-R01-ADMIN-AND-APPROVAL-RECEIPTS",
        "ADMINISTRATIVE_EVIDENCE",
        "OBTAIN_AUTHENTICATED_VERSION_ARCHIVE_LICENSE_GOVERNANCE_REQUIREMENT_AND_EVERY_APPLICABLE_APPROVAL_RECEIPT_WITH_NO_DATA_DOWNLOAD",
    ),
    (
        "PHYS-A03-DATA-ACCESS-INSTANCE",
        "DATA_ACCESS",
        "POPULATE_INDEPENDENTLY_REVIEW_AND_ADMIT_A_SEPARATE_DATA_ACCESS_INSTANCE_THEN_RECORD_FRESH_EXACT_DATA_ACCESS_AUTHORITY",
    ),
    (
        "PHYS-R02-SNAPSHOT",
        "DATA_ACCESS",
        "ACQUIRE_EXACTLY_ONE_ALLOWLISTED_OPEN_ACCESS_SNAPSHOT_AND_BIND_VERSION_BYTE_COUNT_RAW_SHA256_SCHEMA_TOOLCHAIN_AND_PRIVATE_CUSTODY_RECEIPTS",
    ),
    (
        "PHYS-R03-SUPPORT",
        "DOMAIN_EVIDENCE",
        "CERTIFY_F033_AND_F034_WITH_OBSERVATION_REFERENCE_ACQUISITION_JUSTIFICATION_FULL_SUPPORT_COMPONENT_PROOF_IMPLEMENTATION_AND_INDEPENDENT_REVIEW",
    ),
    (
        "PHYS-R04-RESOLVED-F061-REVIEW",
        "DOMAIN_EVIDENCE",
        "BIND_THE_OBSERVED_NATURAL_GROUP_TOTAL_TO_THE_ACCEPTED_70_15_15_POLICY_AND_OBTAIN_A_DISTINCT_PHYSIONET_RESOLVED_COUNT_REVIEW",
    ),
    (
        "PHYS-R05-SPLIT-AND-DUPLICATE-AUDIT",
        "DOMAIN_EVIDENCE",
        "CREATE_AND_INDEPENDENTLY_VERIFY_THE_COMPLETE_PATIENT_DISJOINT_MANIFEST_AND_COMPLETE_METHOD_BLIND_CROSS_SPLIT_DUPLICATE_AND_NEAR_DUPLICATE_AUDIT",
    ),
    (
        "PHYS-R06-STRUCTURAL-PREFLIGHT",
        "ADMISSION",
        "RUN_THE_ACCEPTED_FAIL_CLOSED_PREFLIGHT_WITH_ALL_THIRTEEN_TRAIN_ONLY_VIOLATION_COUNTS_AND_ALL_SIX_RECEIPT_FLAGS_EXACTLY_PASSING",
    ),
    (
        "PHYS-R07-INDEPENDENT-ADMISSION",
        "ADMISSION",
        "OBTAIN_A_SEPARATE_INDEPENDENT_DOMAIN_ADMISSION_DECISION_BOUND_TO_THE_EXACT_EVIDENCE_AGGREGATE",
    ),
)


class ValidationError(ValueError):
    """Package content, binding, or closure-boundary failure."""


def _fail(message: str) -> None:
    raise ValidationError(message)


def _strict_object(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            _fail("duplicate or non-string JSON object key")
        result[key] = value
    return result


def strict_loads(raw: bytes) -> Dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("machine JSON is not strict UTF-8 JSON") from exc
    if type(value) is not dict:
        _fail("machine root must be an exact object")
    return value


def semantic_sha256(value: Dict[str, Any]) -> str:
    projection = dict(value)
    projection.pop("record_sha256", None)
    raw = json.dumps(
        projection, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _deep_exact(actual: Any, expected: Any, name: str) -> None:
    if type(actual) is not type(expected):
        _fail(name + " type mismatch")
    if type(expected) is dict:
        if tuple(actual.keys()) != tuple(expected.keys()):
            _fail(name + " key/order mismatch")
        for key in expected:
            _deep_exact(actual[key], expected[key], name + "." + key)
    elif type(expected) is list:
        if len(actual) != len(expected):
            _fail(name + " length mismatch")
        for index, (left, right) in enumerate(zip(actual, expected)):
            _deep_exact(left, right, f"{name}[{index}]")
    elif actual != expected:
        _fail(name + " value mismatch")


def _exact_keys(value: Any, keys: Tuple[str, ...], name: str) -> Dict[str, Any]:
    if type(value) is not dict or tuple(value.keys()) != keys:
        _fail(name + " exact keys/order mismatch")
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_bound(root: Path, relative: str) -> bytes:
    path = root / relative
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValidationError("bound file missing: " + relative) from exc
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        _fail("bound path must be a regular non-symlink file: " + relative)
    raw = path.read_bytes()
    expected_bytes, expected_sha = FILE_BINDINGS[relative]
    if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
        _fail("bound file bytes changed: " + relative)
    return raw


def validate_record(record: Dict[str, Any]) -> None:
    top = _exact_keys(
        record,
        (
            "schema_version",
            "record_sha256",
            "reported_date",
            "package_status",
            "scope",
            "public_documentation_observation",
            "accepted_local_predecessors",
            "existing_fail_closed_preflight",
            "open_field_evidence_map",
            "exact_next_authority_and_receipt_checklist",
            "closure_projection",
        ),
        "record",
    )
    if top["schema_version"] != SCHEMA or type(top["schema_version"]) is not str:
        _fail("schema mismatch")
    if top["record_sha256"] != EXPECTED_RECORD_SHA256:
        _fail("semantic digest carrier mismatch")
    if semantic_sha256(top) != EXPECTED_RECORD_SHA256:
        _fail("semantic digest mismatch")
    if top["reported_date"] != "2026-09-02" or top["package_status"] != STATUS:
        _fail("date or package status mismatch")

    expected_scope = {
        "read_only_public_documentation_inspection": True,
        "dataset_bytes_downloaded": False,
        "restricted_or_private_data_accessed": False,
        "authentication_attempted": False,
        "person_or_institution_contacted": False,
        "approval_created_or_inferred": False,
        "scientific_execution_performed": False,
        "tracker_or_ledger_edited": False,
        "transport_request_count_claimed": False,
        "raw_http_response_custody_claimed": False,
        "external_identity_or_time_attestation_claimed": False,
    }
    _deep_exact(top["scope"], expected_scope, "scope")
    _deep_exact(
        top["public_documentation_observation"],
        EXPECTED_PUBLIC_OBSERVATION,
        "public observation",
    )

    predecessor = _exact_keys(
        top["accepted_local_predecessors"],
        (
            "license_and_access_field_already_closed",
            "license_observation_adds_no_new_field_delta",
            "frozen_physionet_fields",
            "frozen_governance_plan_fields",
            "accepted_f061_definition_sha256",
            "accepted_f061_review_raw_sha256",
            "accepted_f061_policy",
            "exact_control_bindings",
        ),
        "accepted_local_predecessors",
    )
    if predecessor["license_and_access_field_already_closed"] != "F021":
        _fail("F021 predecessor mismatch")
    if predecessor["license_observation_adds_no_new_field_delta"] is not True:
        _fail("license observation delta promoted")
    if tuple(predecessor["frozen_physionet_fields"]) != EXPECTED_FROZEN_FIELDS:
        _fail("frozen PhysioNet roster mismatch")
    if tuple(predecessor["frozen_governance_plan_fields"]) != EXPECTED_PLAN_FIELDS:
        _fail("frozen governance-plan roster mismatch")
    if predecessor["accepted_f061_definition_sha256"] != (
        "6c7beda87ccf1b9b60b0787619fc637eeb3ab34d5f68e09608d46b4dcf11f946"
    ):
        _fail("F061 definition binding mismatch")
    if predecessor["accepted_f061_review_raw_sha256"] != FILE_BINDINGS[
        "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json"
    ][1]:
        _fail("F061 review binding mismatch")
    expected_policy = {
        "allocation": [70, 15, 15],
        "denominator": 100,
        "minimum_counts": [1, 128, 128],
        "exact_validation_count": 128,
        "exact_test_count": 128,
        "admissible_natural_group_totals": [852, 853, 854, 855],
    }
    _deep_exact(predecessor["accepted_f061_policy"], expected_policy, "F061 policy")
    expected_controls = [
        {"path": path, "bytes": FILE_BINDINGS[path][0], "raw_sha256": FILE_BINDINGS[path][1]}
        for path in (
            "src/heterodiff/data/two_domain_external_evidence_intake.py",
            "research/fixtures/manuscript_v3_b02_b03_b09_external_evidence_intake_v1.json",
            "src/heterodiff/data/two_domain_governance_release_controls.py",
            "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json",
        )
    ]
    _deep_exact(predecessor["exact_control_bindings"], expected_controls, "control bindings")

    preflight = _exact_keys(
        top["existing_fail_closed_preflight"],
        (
            "source_path", "source_bytes", "source_raw_sha256", "test_path",
            "test_bytes", "test_raw_sha256", "focused_tests_passed",
            "focused_tests_failed", "synthetic_state_can_claim_real_authority",
            "real_shaped_receipts_can_self_authenticate",
            "structural_preflight_can_claim_final_domain_admission",
            "positive_structural_result", "final_domain_admission_reserved_to_separate_review",
        ),
        "existing_fail_closed_preflight",
    )
    expected_preflight = {
        "source_path": SOURCE_PATH,
        "source_bytes": FILE_BINDINGS[SOURCE_PATH][0],
        "source_raw_sha256": FILE_BINDINGS[SOURCE_PATH][1],
        "test_path": SOURCE_TEST_PATH,
        "test_bytes": FILE_BINDINGS[SOURCE_TEST_PATH][0],
        "test_raw_sha256": FILE_BINDINGS[SOURCE_TEST_PATH][1],
        "focused_tests_passed": 127,
        "focused_tests_failed": 0,
        "synthetic_state_can_claim_real_authority": False,
        "real_shaped_receipts_can_self_authenticate": False,
        "structural_preflight_can_claim_final_domain_admission": False,
        "positive_structural_result": "ELIGIBLE_FOR_INDEPENDENT_ADMISSION",
        "final_domain_admission_reserved_to_separate_review": True,
    }
    _deep_exact(preflight, expected_preflight, "preflight binding")

    rows = top["open_field_evidence_map"]
    if type(rows) is not list or len(rows) != len(EXPECTED_OPEN_FIELDS):
        _fail("open-field evidence roster length mismatch")
    row_keys = (
        "ordinal", "field_id", "json_pointer", "required_evidence",
        "public_documentation_alone_sufficient", "currently_present",
    )
    for ordinal, (row, expected) in enumerate(zip(rows, EXPECTED_OPEN_FIELDS)):
        item = _exact_keys(row, row_keys, f"open_field[{ordinal}]")
        if type(item["ordinal"]) is not int or item["ordinal"] != ordinal:
            _fail("open-field ordinal mismatch")
        if (item["field_id"], item["json_pointer"], item["required_evidence"]) != expected:
            _fail("open-field identity or requirement mismatch")
        if item["public_documentation_alone_sufficient"] is not False:
            _fail("public documentation promoted to sufficient evidence")
        if item["currently_present"] is not False:
            _fail("absent real field evidence promoted")

    checklist = top["exact_next_authority_and_receipt_checklist"]
    if type(checklist) is not list or len(checklist) != len(EXPECTED_CHECKLIST):
        _fail("authority/receipt checklist length mismatch")
    check_keys = (
        "ordinal", "check_id", "phase", "requirement", "required_before_next",
        "currently_satisfied", "satisfied_by_this_package",
    )
    for ordinal, (row, expected) in enumerate(zip(checklist, EXPECTED_CHECKLIST)):
        item = _exact_keys(row, check_keys, f"checklist[{ordinal}]")
        if type(item["ordinal"]) is not int or item["ordinal"] != ordinal:
            _fail("checklist ordinal mismatch")
        if (item["check_id"], item["phase"], item["requirement"]) != expected:
            _fail("checklist identity/order/requirement mismatch")
        if item["required_before_next"] is not True:
            _fail("checklist prerequisite weakened")
        if item["currently_satisfied"] is not False or item["satisfied_by_this_package"] is not False:
            _fail("external checklist item falsely promoted")

    expected_closure = {
        "field_ids_closed": [],
        "field_count_delta": 0,
        "blocker_ids_closed": [],
        "blocker_count_delta": 0,
        "operational_tasks_closed": [],
        "timetable_checkbox_delta": 0,
        "formal_test_delta": 0,
        "result_slot_delta": 0,
        "b02_status": "OPEN",
        "b09_status": "OPEN",
        "physionet_domain_admitted": False,
        "wave3_physionet_complete": False,
        "next_state": "HOLD_EXTERNAL_PRINCIPALS_APPROVALS_AUTHORITY_SNAPSHOT_SUPPORT_SPLIT_AND_INDEPENDENT_ADMISSION",
    }
    _deep_exact(top["closure_projection"], expected_closure, "closure projection")


def _validate_preflight_api(root: Path) -> None:
    source = root / SOURCE_PATH
    module_name = "_heterodiff_physionet_preflight_gap_validation"
    specification = importlib.util.spec_from_file_location(module_name, source)
    if specification is None or specification.loader is None:
        _fail("preflight module could not be loaded")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
        activation = module.synthetic_activation("PUBLIC-DOC-GAP")
        if activation.real_instance_structurally_enabled is not False:
            _fail("synthetic activation gained real authority")
        activation_record = activation.to_dict()
        if activation_record.get("authority_authenticated_by_this_module") is not False:
            _fail("module claims to authenticate authority")
        support = module.unresolved_observation_support(activation)
        if support.certified is not False:
            _fail("unresolved support became certified")
        if support.f033_state != "UNRESOLVED" or support.f034_state != "UNRESOLVED":
            _fail("unresolved F033/F034 state changed")
        zero = module.ViolationCountVector((0,) * len(module.ADMISSION_COMPONENTS))
        decision = module.AdmissionPreflightDecision(
            activation_id=activation.activation_id,
            statistic_id=module.ADMISSION_STATISTIC_ID,
            threshold_id=module.ADMISSION_THRESHOLD_ID,
            snapshot_receipt_sha256="0" * 64,
            split_manifest_sha256="1" * 64,
            governance_receipt_sha256="2" * 64,
            support_receipt_sha256="3" * 64,
            duplicate_audit_receipt_sha256="4" * 64,
            violation_counts=zero,
            receipt_flags=tuple((name, False) for name in module.REQUIRED_RECEIPT_FLAGS),
            duplicate_audit_findings=(0, 0),
            decision="NO_GO",
            domain_admitted=False,
            independent_admission_required=True,
        )
        if decision.domain_admitted is not False or decision.decision != "NO_GO":
            _fail("minimal unresolved decision did not fail closed")
    finally:
        sys.modules.pop(module_name, None)


def validate_package(root: Path) -> Dict[str, Any]:
    root = root.resolve()
    raws = {relative: _read_bound(root, relative) for relative in FILE_BINDINGS}
    record = strict_loads(raws[MACHINE_PATH])
    validate_record(record)
    _validate_preflight_api(root)
    return {
        "status": "PASS",
        "schema_version": SCHEMA,
        "record_sha256": record["record_sha256"],
        "open_fields": [row[0] for row in EXPECTED_OPEN_FIELDS],
        "checklist_items": len(EXPECTED_CHECKLIST),
        "field_delta": 0,
        "blocker_delta": 0,
        "b02": "OPEN",
        "b09": "OPEN",
    }


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=default_root())
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = validate_package(args.root)
    except (OSError, ValidationError, ValueError, TypeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
