"""Read-only validator for the exact B06 baseline/matched-compute freeze."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any, Dict, List, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]
SOURCE_ROOT = WORKSPACE_ROOT / "src"
if os.fspath(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(SOURCE_ROOT))

from heterodiff.experiments import matched_total_compute as f104  # noqa: E402
from heterodiff.experiments import two_domain_baseline_registry as registry  # noqa: E402


SCHEMA = "heterodiff-manuscript-v3-b06-baseline-identity-matched-compute-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
REGISTRY_DOMAIN = b"HETERODIFF-B06-FROZEN-REGISTRY-V1\0"
STATE = "B06_BASELINE_IDENTITIES_CONFIGS_CAPABILITIES_AND_MATCHED_COMPUTE_FROZEN_PREOUTCOME"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_EXACT_42_FIELD_AND_B06_BLOCKER_CLOSURE"
CONTROL_PREDICATE = "B06_BASELINE_IDENTITIES_AND_MATCHED_COMPUTE_CLOSED_PREOUTCOME"
REPORTED_DATE = "2026-09-01"

MATCHED_SOURCE_PATH = "src/heterodiff/experiments/matched_total_compute.py"
MATCHED_TEST_PATH = "tests/unit/test_matched_total_compute.py"
REGISTRY_SOURCE_PATH = "src/heterodiff/experiments/two_domain_baseline_registry.py"
REGISTRY_TEST_PATH = "tests/unit/test_two_domain_baseline_registry.py"
ADAPTER_SOURCE_PATH = "src/heterodiff/experiments/two_domain_baseline_adapter_contract.py"
ADAPTER_TEST_PATH = "tests/unit/test_two_domain_baseline_adapter_contract.py"
CSDI_LICENSE_PATH = "research/fixtures/b06_upstream_receipts/csdi_7f24a436_LICENSE"
EDITPP_LICENSE_PATH = "research/fixtures/b06_upstream_receipts/editpp_3113d2ee_LICENSE"
HUMAN_PATH = "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md"
MACHINE_PATH = "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json"
VALIDATOR_PATH = "research/diagnostics/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py"
VALIDATOR_TEST_PATH = "tests/unit/test_manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.py"

PACKAGE_ROSTER = (
    MATCHED_SOURCE_PATH,
    MATCHED_TEST_PATH,
    REGISTRY_SOURCE_PATH,
    REGISTRY_TEST_PATH,
    ADAPTER_SOURCE_PATH,
    ADAPTER_TEST_PATH,
    CSDI_LICENSE_PATH,
    EDITPP_LICENSE_PATH,
    HUMAN_PATH,
    MACHINE_PATH,
    VALIDATOR_PATH,
    VALIDATOR_TEST_PATH,
)
PACKAGE_BINDING_ROLES = (
    (MATCHED_SOURCE_PATH, "f104_production_compute_contract"),
    (MATCHED_TEST_PATH, "f104_hostile_tests"),
    (REGISTRY_SOURCE_PATH, "b06_frozen_registry"),
    (REGISTRY_TEST_PATH, "b06_registry_hostile_tests"),
    (ADAPTER_SOURCE_PATH, "b06_to_b12_adapter_contract"),
    (ADAPTER_TEST_PATH, "adapter_contract_hostile_tests"),
    (CSDI_LICENSE_PATH, "csdi_retrieved_license_receipt"),
    (EDITPP_LICENSE_PATH, "editpp_retrieved_license_receipt"),
    (HUMAN_PATH, "human_freeze_contract"),
    (VALIDATOR_PATH, "read_only_validator"),
    (VALIDATOR_TEST_PATH, "package_hostile_tests"),
)

PREDECESSOR_BINDINGS = (
    ("manuscript_v3/execution_preregistration.md", "accepted_preregistration", 22491, "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e"),
    ("research/fixtures/manuscript_v3_execution_preregistration_v1.json", "accepted_preregistration_machine", 39771, "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"),
    ("manuscript_v3/execution_preregistration_preexecution_closure_v2.md", "accepted_preexecution_closure", 14938, "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d"),
    ("research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json", "accepted_preexecution_closure_machine", 24571, "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db"),
    ("PROJECT_BASELINE_CAPABILITY_COMPUTE_MODEL_DRAFT.md", "accepted_b06_draft", 10754, "33c9df737f45411861f2a60a9ed99220f61e4ac66461999ed0367c482b5dbe3d"),
    ("research/fixtures/manuscript_v3_baseline_capability_compute_model_draft_v1.json", "accepted_b06_draft_machine", 24004, "be7a96ab4898e89cf0167fcce48204142143bf071a194b24d480091a6c60530a"),
    ("PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md", "accepted_f104_contract", 9596, "4d73909714e5227175b8c0f250876ffeddcd25ad9cc4d54b27d02499c562edfb"),
    ("research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json", "accepted_f104_machine", 12639, "c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54"),
    ("PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md", "accepted_f104_review", 10230, "7694694d7fe2b0c2dd17f79b9e0f9d2f44c14c59c3f0568902e3cad7d75ae402"),
    ("PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md", "accepted_f105_contract", 15242, "5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef"),
    ("research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json", "accepted_f105_machine", 23899, "560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9"),
    ("PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE_INDEPENDENT_REVIEW.md", "accepted_f105_review", 5932, "368fd5444b958c5eef1a62b25ad45062415a6c396863e33864f63a81356171a3"),
    ("PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md", "accepted_theory_statistics_contract", 17299, "bb4438887f54710b0445e0b713ee086abc2523b2bf34b4a08d42ee586515d721"),
    ("research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json", "accepted_theory_statistics_machine", 20936, "2ff92ac1b4b6df75931791cd16ce7ade461c70b29042a17486bc2804f35295f1"),
    ("PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE_INDEPENDENT_REVIEW.md", "accepted_theory_statistics_review", 3270, "ede11cff876c96cafe5734cee59ffae347b001dc8e16c3b3b71437d6cb4a0b64"),
    ("PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md", "accepted_governance_contract", 15756, "e2ab4740c530460e0b6352e33cd7c129ea80e928a7a2da7a8be2f40ef668a19c"),
    ("research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json", "accepted_governance_machine", 17729, "340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c"),
    ("PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS_INDEPENDENT_REVIEW.md", "accepted_governance_review", 10999, "951efca8ae87a6aab80c6dbd9e07bb42769fcf0424eb544e6d90c4cb94cdffa3"),
)

FIELD_IDS = tuple("F%03d" % ordinal for ordinal in range(62, 104))
FIELD_POINTERS = (
    "/method_and_baseline_plan/primary_method/repository",
    "/method_and_baseline_plan/primary_method/commit",
    "/method_and_baseline_plan/primary_method/config_sha256",
    "/method_and_baseline_plan/primary_method/parameter_count",
    "/method_and_baseline_plan/primary_method/training_compute_budget",
    "/method_and_baseline_plan/primary_method/inference_compute_budget",
    "/method_and_baseline_plan/primary_comparator/repository",
    "/method_and_baseline_plan/primary_comparator/commit",
    "/method_and_baseline_plan/primary_comparator/config_sha256",
    "/method_and_baseline_plan/primary_comparator/parameter_count",
    "/method_and_baseline_plan/primary_comparator/training_compute_budget",
    "/method_and_baseline_plan/primary_comparator/inference_compute_budget",
    "/method_and_baseline_plan/required_controls/0/implementation",
    "/method_and_baseline_plan/required_controls/0/config_sha256",
    "/method_and_baseline_plan/required_controls/1/implementation",
    "/method_and_baseline_plan/required_controls/1/config_sha256",
    "/method_and_baseline_plan/required_controls/2/implementation",
    "/method_and_baseline_plan/required_controls/2/config_sha256",
    "/method_and_baseline_plan/required_controls/3/implementation",
    "/method_and_baseline_plan/required_controls/3/config_sha256",
    "/method_and_baseline_plan/required_literature_comparator_families/0/implementation_by_domain",
    "/method_and_baseline_plan/required_literature_comparator_families/0/inapplicability_or_equivalence_justification_by_domain",
    "/method_and_baseline_plan/required_literature_comparator_families/1/implementation_by_domain",
    "/method_and_baseline_plan/required_literature_comparator_families/1/inapplicability_or_equivalence_justification_by_domain",
    "/method_and_baseline_plan/required_literature_comparator_families/2/implementation_by_domain",
    "/method_and_baseline_plan/required_literature_comparator_families/2/inapplicability_or_equivalence_justification_by_domain",
    "/method_and_baseline_plan/required_literature_comparator_families/3/implementation_by_domain",
    "/method_and_baseline_plan/required_literature_comparator_families/3/inapplicability_or_equivalence_justification_by_domain",
    "/method_and_baseline_plan/external_domain_baselines/0/method_id",
    "/method_and_baseline_plan/external_domain_baselines/0/repository",
    "/method_and_baseline_plan/external_domain_baselines/0/commit",
    "/method_and_baseline_plan/external_domain_baselines/0/license",
    "/method_and_baseline_plan/external_domain_baselines/0/config_sha256",
    "/method_and_baseline_plan/external_domain_baselines/0/native_capability_and_extension_statement",
    "/method_and_baseline_plan/external_domain_baselines/0/tuning_budget",
    "/method_and_baseline_plan/external_domain_baselines/1/method_id",
    "/method_and_baseline_plan/external_domain_baselines/1/repository",
    "/method_and_baseline_plan/external_domain_baselines/1/commit",
    "/method_and_baseline_plan/external_domain_baselines/1/license",
    "/method_and_baseline_plan/external_domain_baselines/1/config_sha256",
    "/method_and_baseline_plan/external_domain_baselines/1/native_capability_and_extension_statement",
    "/method_and_baseline_plan/external_domain_baselines/1/tuning_budget",
)

ACCEPTED_SEMANTIC_BINDINGS = {
    "preexecution_closure_v2_semantic_sha256": "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    "baseline_draft_semantic_sha256": "4cad447dca7896d45c424ee16594cddf3cd83e8497ed0cb3ec875ced03dd5840",
    "f104_semantic_sha256": "ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b",
    "f105_semantic_sha256": "14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52",
    "theory_statistics_semantic_sha256": "335879da927b14de0f2ab0cb69b531ea51f24d9734777cb33cdf1e90fb81a491",
    "governance_semantic_sha256": "8d39354b7d6d119c593b7943ebf5b78828f6810c91195e4ac50b0f4424036313",
}


class ValidationError(RuntimeError):
    """Raised when any canonical package fact differs."""


def canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ValidationError("value is not canonical ASCII JSON") from error


def canonical_machine_bytes(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def record_sha256(value: Dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("record_sha256", None)
    return hashlib.sha256(RECORD_DOMAIN + canonical_json_bytes(payload)).hexdigest()


def registry_sha256(value: object) -> str:
    return hashlib.sha256(REGISTRY_DOMAIN + canonical_json_bytes(value)).hexdigest()


def _reject_float(_: str) -> None:
    raise ValidationError("binary floating point is forbidden in the machine record")


def _object_no_duplicates(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate machine-record key")
        result[key] = value
    return result


def strict_json(raw: bytes) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_object_no_duplicates,
            parse_float=_reject_float,
            parse_constant=_reject_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is not strict ASCII JSON") from error
    if type(value) is not dict:
        raise ValidationError("machine record must be an exact object")
    return value


def _fingerprint(value: os.stat_result) -> Tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
    )


def _safe_read(root: Path, relative: str) -> Tuple[bytes, os.stat_result]:
    if type(relative) is not str:
        raise ValidationError("relative path must be an exact string")
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(
        part in ("", ".", "..") for part in parts
    ):
        raise ValidationError("unsafe relative path")
    if root.is_symlink() or not root.is_dir():
        raise ValidationError("workspace root must be a real directory")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptors: List[int] = []
    try:
        current = os.open(os.fspath(root), directory_flags)
        descriptors.append(current)
        for part in parts[:-1]:
            current = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(current)
        leaf = os.open(parts[-1], file_flags, dir_fd=current)
        descriptors.append(leaf)
        before = os.fstat(leaf)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError("package member is not a regular file")
        chunks: List[bytes] = []
        while True:
            chunk = os.read(leaf, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(leaf)
        if _fingerprint(before) != _fingerprint(after):
            raise ValidationError("file changed during stable read")
        return b"".join(chunks), after
    except OSError as error:
        raise ValidationError("safe package read failed") from error
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _binding(root: Path, relative: str, role: str) -> Dict[str, Any]:
    raw, metadata = _safe_read(root, relative)
    if stat.S_IMODE(metadata.st_mode) != 0o644:
        raise ValidationError("package member mode must be 0644")
    if metadata.st_nlink != 1:
        raise ValidationError("package member must have one hard link")
    if not raw.endswith(b"\n"):
        raise ValidationError("package member must have a terminal LF")
    return {
        "path": relative,
        "role": role,
        "bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
    }


def _predecessor_bindings(root: Path) -> List[Dict[str, Any]]:
    rows = []
    for path, role, expected_bytes, expected_sha256 in PREDECESSOR_BINDINGS:
        row = _binding(root, path, role)
        if row["bytes"] != expected_bytes or row["raw_sha256"] != expected_sha256:
            raise ValidationError("accepted predecessor bytes differ")
        rows.append(row)
    return rows


def _field_values(value: Dict[str, Any]) -> List[object]:
    primary, comparator = value["primary_pair"]
    values: List[object] = [
        primary["repository"],
        primary["commit_or_release"],
        primary["config_sha256"],
        primary["parameter_count"],
        primary["training_compute_budget"],
        primary["inference_compute_budget"],
        comparator["repository"],
        comparator["commit_or_release"],
        comparator["config_sha256"],
        comparator["parameter_count"],
        comparator["training_compute_budget"],
        comparator["inference_compute_budget"],
    ]
    for control in value["controls"]:
        values.extend((control["implementation"], control["config_sha256"]))
    for family in value["literature_families"]:
        values.extend(
            (
                family["implementation_by_domain"],
                family["inapplicability_or_equivalence_justification_by_domain"],
            )
        )
    for external in value["external_baselines"]:
        values.extend(
            (
                external["method_id"],
                external["repository"],
                external["commit"],
                external["license"],
                external["config_sha256"],
                external["native_capability_and_extension_statement"],
                external["tuning_budget"],
            )
        )
    if len(values) != len(FIELD_IDS):
        raise ValidationError("field-value projection does not contain 42 values")
    return values


def field_closures(value: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "field_id": field_id,
            "json_pointer": pointer,
            "status": "CLOSED_BY_B06_ADDITIVE_PREOUTCOME_FREEZE",
            "value": field_value,
        }
        for field_id, pointer, field_value in zip(
            FIELD_IDS, FIELD_POINTERS, _field_values(value)
        )
    ]


def _license_receipts(root: Path) -> List[Dict[str, Any]]:
    csdi = _binding(root, CSDI_LICENSE_PATH, "csdi_retrieved_license_receipt")
    editpp = _binding(root, EDITPP_LICENSE_PATH, "editpp_retrieved_license_receipt")
    if (csdi["bytes"], csdi["raw_sha256"]) != (
        registry.CSDI_LICENSE_BYTES,
        registry.CSDI_LICENSE_SHA256,
    ):
        raise ValidationError("CSDI license receipt differs")
    if (editpp["bytes"], editpp["raw_sha256"]) != (
        registry.EDITPP_LICENSE_BYTES,
        registry.EDITPP_LICENSE_SHA256,
    ):
        raise ValidationError("EditPP license receipt differs")
    return [
        {
            "method_id": "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1",
            "repository": registry.CSDI_REPOSITORY,
            "commit": registry.CSDI_COMMIT,
            "upstream_path": "LICENSE",
            "spdx": "MIT",
            "receipt_binding": csdi,
        },
        {
            "method_id": "EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1",
            "repository": registry.EDITPP_REPOSITORY,
            "commit": registry.EDITPP_COMMIT,
            "upstream_path": "LICENSE",
            "spdx": "MIT",
            "receipt_binding": editpp,
        },
    ]


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    frozen = registry.validate_registry(registry.FROZEN_REGISTRY)
    package_bindings = [
        _binding(root, path, role) for path, role in PACKAGE_BINDING_ROLES
    ]
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "reported_date": REPORTED_DATE,
        "package_kind": PACKAGE_KIND,
        "control_predicate": CONTROL_PREDICATE,
        "accepted_predecessor_bindings": _predecessor_bindings(root),
        "accepted_semantic_bindings": dict(ACCEPTED_SEMANTIC_BINDINGS),
        "registry": frozen,
        "registry_sha256": registry_sha256(frozen),
        "external_license_receipts": _license_receipts(root),
        "field_closures": field_closures(frozen),
        "field_delta": {
            "field_ids": list(FIELD_IDS),
            "pre_execution": 42,
            "post_execution": 0,
            "total": 42,
            "blockers_closed": 1,
            "blocker_ids": ["B06"],
        },
        "additive_count_transition": {
            "before": {
                "pre_execution_open": 76,
                "pre_execution_closed": 90,
                "post_execution_open": 1,
                "post_execution_closed": 5,
                "total_open": 77,
                "total_closed": 95,
            },
            "after": {
                "pre_execution_open": 34,
                "pre_execution_closed": 132,
                "post_execution_open": 1,
                "post_execution_closed": 5,
                "total_open": 35,
                "total_closed": 137,
            },
        },
        "blocker_transition": {
            "before": {"open": 8, "closed": 4, "execution_open": 6},
            "after": {"open": 7, "closed": 5, "execution_open": 5},
            "closed_now": ["B06"],
            "remaining_open": ["B02", "B03", "B08", "B09", "B10", "B11", "B12"],
        },
        "gate_a_transition": {"before": "4/8", "after": "5/8"},
        "timetable_transition": {
            "before": {"checked": 51, "open": 108, "total": 159},
            "after": {"checked": 54, "open": 105, "total": 159},
            "checkboxes_closed": [
                "B06_BASELINE_IDENTITIES_AND_MATCHED_COMPUTE",
                "GATE_A_BASELINE_FAMILIES_AND_LICENSES_FIXED",
                "SOLO_BLOCK6_BASELINE_REPOSITORIES_COMMITS_CONFIG_INTERFACES_AND_MATCHED_COMPUTE",
            ],
        },
        "qualification_boundary": {
            "independent_acceptance_required_before_tracker_registration": True,
            "bounded_external_selection_not_universal_sota": True,
            "identity_config_capability_and_prospective_budget_only": True,
            "actual_external_or_family_execution_owned_by_B12": True,
            "hardware_weights_capacity_and_reservations_owned_by_B08": True,
        },
        "project_effects_and_nonclaims": {
            "tracker_or_evidence_ledger_edited_by_package_construction": False,
            "external_repository_cloned_only_for_read_only_identity_license_and_config_audit": True,
            "external_package_installed_or_executed": False,
            "external_model_transformation_or_adapter_execution_performed": False,
            "data_acquired_opened_parsed_or_split": False,
            "hardware_selected_or_capacity_reserved": False,
            "calibration_weight_or_hard_ceiling_value_assigned": False,
            "scientific_entropy_training_inference_or_result_inspection_performed": False,
            "formal_test_result_or_claim_created": False,
            "b08_closed": False,
            "b12_closed": False,
            "submission_ready": False,
        },
        "remaining_open_requirements": {
            "B08": [
                "HARDWARE_AND_RUNTIME_IDENTITY",
                "CALIBRATION_WEIGHTS",
                "SCALAR_AND_HARD_AXIS_CEILING_VALUES",
                "CAPACITY_RESERVATION_RECEIPT",
            ],
            "B12": [
                "DOMAIN_SCALE_PRIMARY_RUNTIME",
                "CONTROL_AND_FAMILY_EXECUTABLE_ADAPTERS",
                "CSDI_AND_EDITPP_AUTHOR_EXTENSION_IMPLEMENTATIONS",
                "END_TO_END_RUNNER_AND_WHOLE_METHOD_QUALIFICATION",
            ],
        },
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_bindings_excluding_machine_self": package_bindings,
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "raw_self_hash_embedded": False,
            "semantic_self_digest_field": "record_sha256",
        },
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _validate_compute_bindings(frozen: Dict[str, Any]) -> None:
    primary, comparator = frozen["primary_pair"]
    for domain_id in registry.DOMAIN_IDS:
        if primary["parameter_count"][domain_id] != comparator["parameter_count"][domain_id]:
            raise ValidationError("primary parameter counts differ")
        if primary["training_compute_budget"][domain_id] != comparator["training_compute_budget"][domain_id]:
            raise ValidationError("primary training budgets differ")
        if primary["inference_compute_budget"][domain_id] != comparator["inference_compute_budget"][domain_id]:
            raise ValidationError("primary inference budgets differ")
        match = f104.validate_primary_pair_equality(
            primary["prospective_matched_compute_record"][domain_id],
            comparator["prospective_matched_compute_record"][domain_id],
        )
        if match["equal_prospective_ceiling_and_selection_opportunity"] is not True:
            raise ValidationError("F104 prospective match failed")
        if match["b08_resource_values_assigned"] is not False:
            raise ValidationError("B08 values were assigned")


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    raw, metadata = _safe_read(root, MACHINE_PATH)
    if stat.S_IMODE(metadata.st_mode) != 0o644 or metadata.st_nlink != 1:
        raise ValidationError("machine-record custody differs")
    record = strict_json(raw)
    if raw != canonical_machine_bytes(record):
        raise ValidationError("machine record is not canonical")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine semantic digest differs")
    expected = expected_record(root)
    if record != expected:
        raise ValidationError("machine record differs from the exact expected package")
    if tuple(row["field_id"] for row in record["field_closures"]) != FIELD_IDS:
        raise ValidationError("field closure roster differs")
    if tuple(row["json_pointer"] for row in record["field_closures"]) != FIELD_POINTERS:
        raise ValidationError("field pointer roster differs")
    if record["registry_sha256"] != registry_sha256(record["registry"]):
        raise ValidationError("registry semantic digest differs")
    # Canonical JSON sorts object keys recursively, while the F104 validator
    # deliberately requires its in-memory construction order.  Equality with
    # ``expected`` above has already bound every serialized registry value, so
    # replay the order-sensitive compute check on the freshly reconstructed
    # authoritative registry rather than on the sorted JSON carrier.
    _validate_compute_bindings(expected["registry"])
    audit = record["registry"]["external_selection_audit"]
    if audit["universal_state_of_the_art_claimed"] is not False:
        raise ValidationError("universal external-baseline claim is forbidden")
    if record["field_delta"]["total"] != 42:
        raise ValidationError("field delta differs")
    if record["blocker_transition"]["closed_now"] != ["B06"]:
        raise ValidationError("blocker delta differs")
    nonclaims = record["project_effects_and_nonclaims"]
    for key in (
        "external_package_installed_or_executed",
        "external_model_transformation_or_adapter_execution_performed",
        "data_acquired_opened_parsed_or_split",
        "hardware_selected_or_capacity_reserved",
        "calibration_weight_or_hard_ceiling_value_assigned",
        "scientific_entropy_training_inference_or_result_inspection_performed",
        "formal_test_result_or_claim_created",
        "b08_closed",
        "b12_closed",
        "submission_ready",
    ):
        if nonclaims[key] is not False:
            raise ValidationError("a required nonclaim was promoted")
    return {
        "validation": "PASS",
        "state": STATE,
        "record_sha256": record["record_sha256"],
        "registry_sha256": record["registry_sha256"],
        "fields_closed": list(FIELD_IDS),
        "pre_execution_fields_closed": 42,
        "blockers_closed": ["B06"],
        "pre_execution_open_after": 34,
        "total_open_after": 35,
        "b08_closed": False,
        "b12_closed": False,
    }


def main() -> int:
    try:
        result = validate(WORKSPACE_ROOT)
    except (ValidationError, registry.BaselineRegistryError, f104.MatchedTotalComputeError) as error:
        print("HOLD: %s" % error)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
