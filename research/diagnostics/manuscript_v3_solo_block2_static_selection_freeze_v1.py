"""Read-only validator for the Solo Block 2 static selection package.

The validator reads only the four package files and a fixed immutable input
roster.  It never opens historical mutable snapshots, data, remote sources, or
future protocol instances.  It has no writer, network, connector, subprocess,
entropy, training, runtime, production, or scientific route.  Its guarantees
are procedural on an honest host, not malicious-host resistance.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-solo-block2-static-selection-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "SOLO_BLOCK2_STATIC_SELECTIONS_FROZEN_NO_EXTERNAL_CONTACT_AUTHORITY"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"

HUMAN_PATH = "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/" "manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)
TEST_PATH = "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py"
PREREGISTRATION_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
CLOSURE_PATH = (
    "research/fixtures/"
    "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
SEAL_HUMAN_PATH = "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
SEAL_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json"
)
SEAL_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
SEAL_TEST_PATH = (
    "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)

NORMALIZED_AUTHORITY_TEXT = (
    "Alright, sounds good. I think that the next step is to cover the second "
    "week's tasks."
)
AUTHORITY_TEXT_SHA256 = (
    "d2e6bf99d8ba4f1f385f1d77d841a5393fc73c0bdb05229db9e5eab88c124d0b"
)
C17_ROUTE = "FORK_B_DIRECT_SIMULTANEOUS_TARGET_OCCUPATION_CERTIFICATES"
SUPPORT_POLICY = (
    "ACQUISITION_JUSTIFIED_POSITIVE_DOMINATED_MIXTURE_WITH_SHARED_BASE_"
    "STRUCTURAL_ZEROS_AND_FAIL_CLOSED_NONADMISSION"
)
CKS_ROUTE = "CKS_PROOF_ROUTE_SELECTED_FOR_DEVELOPMENT"
CKS_VARIANT = (
    "EXPLICIT_ORTHOGONAL_COUNT_CHANNEL_PLUS_CHARACTERISTIC_NORMALIZED_"
    "EVENT_MEASURE_CHANNEL"
)

PHYSIONET_URL = "https://physionet.org/content/challenge-2012/1.0.0/"
RETAIL_URL = "https://archive.ics.uci.edu/dataset/502/online+retail+ii"


class ValidationError(ValueError):
    """Raised when the static package fails closed."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def _self_digest(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("input self schema invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256((schema + "\0").encode("ascii") + _canonical_payload_bytes(payload))


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for index, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("path type invalid")
    rel = Path(relative_path)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise ValidationError("unsafe path")
    return root.joinpath(*rel.parts)


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    ancestors: List[Tuple[Any, ...]] = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("unsafe ancestor")
        ancestors.append(
            (
                str(current),
                status.st_dev,
                status.st_ino,
                stat.S_IFMT(status.st_mode),
                stat.S_IMODE(status.st_mode),
                status.st_uid,
                status.st_gid,
            )
        )
        if current == root:
            break
        if root not in current.parents:
            raise ValidationError("path escaped root")
        current = current.parent
    return tuple(reversed(ancestors))


def _leaf_fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(root: Path, relative_path: str) -> bytes:
    path = _safe_relative_path(root, relative_path)
    ancestors = _ancestor_snapshot(root, path)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("file custody invalid: " + relative_path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    raw = b"".join(chunks)
    fingerprint = _leaf_fingerprint(before_path)
    if not (
        fingerprint
        == _leaf_fingerprint(before_fd)
        == _leaf_fingerprint(after_fd)
        == _leaf_fingerprint(after_path)
    ):
        raise ValidationError("file changed during read: " + relative_path)
    if len(raw) != before_fd.st_size:
        raise ValidationError("short read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during read")
    return raw


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    record_digest: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": raw.endswith(b"\n"),
        "raw_sha256": _sha256(raw),
    }
    if record_digest is not None:
        result["record_sha256"] = record_digest
    return result


LIVE_IMMUTABLE_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {
        "ordinal": 0,
        "role": "EXECUTION_PREREGISTRATION",
        "path": PREREGISTRATION_PATH,
        "bytes": 39771,
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
        "raw_sha256": (
            "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"
        ),
    },
    {
        "ordinal": 1,
        "role": "PREEXECUTION_CLOSURE_V2",
        "path": CLOSURE_PATH,
        "bytes": 24571,
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
        "raw_sha256": (
            "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db"
        ),
        "record_sha256": (
            "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"
        ),
    },
    {
        "ordinal": 2,
        "role": "PROSPECTIVE_NO_ACQUISITION_SEAL_HUMAN",
        "path": SEAL_HUMAN_PATH,
        "bytes": 7078,
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
        "raw_sha256": (
            "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2"
        ),
    },
    {
        "ordinal": 3,
        "role": "PROSPECTIVE_NO_ACQUISITION_SEAL_MACHINE",
        "path": SEAL_MACHINE_PATH,
        "bytes": 8461,
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
        "raw_sha256": (
            "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8"
        ),
        "record_sha256": (
            "d11d5336f1ede024ab56f92bc64e620681e53fc406fd954aa3da36b7861485a6"
        ),
    },
    {
        "ordinal": 4,
        "role": "PROSPECTIVE_NO_ACQUISITION_SEAL_VALIDATOR",
        "path": SEAL_VALIDATOR_PATH,
        "bytes": 32156,
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
        "raw_sha256": (
            "3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258"
        ),
    },
    {
        "ordinal": 5,
        "role": "PROSPECTIVE_NO_ACQUISITION_SEAL_HOSTILE_TEST",
        "path": SEAL_TEST_PATH,
        "bytes": 16698,
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
        "raw_sha256": (
            "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403"
        ),
    },
)


HISTORICAL_SNAPSHOT_INPUTS: Tuple[Mapping[str, Any], ...] = (
    {
        "ordinal": 0,
        "role": "C17_THEOREM_TARGET_SNAPSHOT",
        "path": "manuscript_v3/c17_hybrid_path_error_theorem.md",
        "bytes": 34923,
        "raw_sha256": "d11dc3a98d19a52e7ab653aca1e06598490ad098a450b526870508b4499b9d8d",
    },
    {
        "ordinal": 1,
        "role": "C17_FORK_B_CONTRACT_SNAPSHOT",
        "path": "manuscript_v3/c17_fork_b_direct_certificate_contract.md",
        "bytes": 7109,
        "raw_sha256": "80c00dd62106e9fd4743fd6999c1e642f0ef31b063cf9ae3c84822b7a68deae4",
    },
    {
        "ordinal": 2,
        "role": "EXECUTABLE_METHOD_SPEC_SNAPSHOT",
        "path": "manuscript_v3/executable_method_spec.md",
        "bytes": 442123,
        "raw_sha256": "58bdfd689caa1698a07e415074e98bd3a80e9d69467d9ddec8f8471aba36c34d",
    },
    {
        "ordinal": 3,
        "role": "EXECUTABLE_METHOD_AUDIT_SNAPSHOT",
        "path": "manuscript_v3/executable_method_audit.md",
        "bytes": 186715,
        "raw_sha256": "4dbfe7ec57973dcac1dcaae4a03f46e60f66d828d6b75d1c77dd1b8776d35da0",
    },
    {
        "ordinal": 4,
        "role": "CLAIM_LEDGER_SNAPSHOT",
        "path": "manuscript_v3/claim_ledger.md",
        "bytes": 130915,
        "raw_sha256": "793f7fbda938f66d771af3dc480d13dc784862a439ee65452b79c776d78e8245",
    },
    {
        "ordinal": 5,
        "role": "MANUSCRIPT_SNAPSHOT",
        "path": "manuscript_v3/manuscript_v3.md",
        "bytes": 66023,
        "raw_sha256": "0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8",
    },
    {
        "ordinal": 6,
        "role": "PROJECT_EVIDENCE_LEDGER_SNAPSHOT",
        "path": "PROJECT_EVIDENCE_LEDGER.md",
        "bytes": 37084,
        "raw_sha256": "f799c17f9b25c91f9e95f5eb1b97f7606056d323aafb1c656a3b608ed88f3b9c",
    },
    {
        "ordinal": 7,
        "role": "CP50_TEST28_V26_SNAPSHOT",
        "path": "research/fixtures/cp50_test28_mixed_initializer_v26.json",
        "bytes": 7087027,
        "raw_sha256": "7faed3c5b07415fbc45fec02d026e36d465819a38e9187369bf0a42a91c29f68",
    },
    {
        "ordinal": 8,
        "role": "FINITE_ASSOCIATION_FORK_B_SOURCE_SNAPSHOT",
        "path": "src/heterodiff/evaluation/finite_association_fork_b_diagnostic.py",
        "bytes": 57731,
        "raw_sha256": "a7279bd83a0e7cc65c132a9f5f73c18fd7bd15a896ceb86788aa4194650ac94d",
    },
    {
        "ordinal": 9,
        "role": "FINITE_BRIDGE_PATH_CONTROL_SOURCE_SNAPSHOT",
        "path": "src/heterodiff/theory/finite_bridge_path_control.py",
        "bytes": 45529,
        "raw_sha256": "1cdb2cf82016ad0979fff3ef7451fe6116904cca772b017e6e605b78b476c502",
    },
    {
        "ordinal": 10,
        "role": "MIXED_PATH_KL_SOURCE_SNAPSHOT",
        "path": "src/heterodiff/evaluation/mixed_ctmc_ou_path_kl_diagnostic.py",
        "bytes": 31393,
        "raw_sha256": "448f50ebde693aa6f7141fcbd91541b781fba4efde92eaf8e0674d8537ca7d7f",
    },
    {
        "ordinal": 11,
        "role": "CAP_DEFECT_SOURCE_SNAPSHOT",
        "path": "src/heterodiff/evaluation/mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py",
        "bytes": 28528,
        "raw_sha256": "50b9748a50982f10f289cba94c8ace9adab6ea003e57da091958fda8844f6ef9",
    },
)


def _historical_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in HISTORICAL_SNAPSHOT_INPUTS:
        row = dict(item)
        row.update(
            {
                "historical_snapshot_only": True,
                "live_custody_validated": False,
                "future_mutation_expected": True,
            }
        )
        rows.append(row)
    return rows


def _f_range(first: int, last: int) -> List[str]:
    return ["F" + str(value).zfill(3) for value in range(first, last + 1)]


def _pair_paths(prefixes: Sequence[str], fields: Sequence[str]) -> List[str]:
    return [prefix + "/" + field for prefix in prefixes for field in fields]


def expected_method_inventory() -> List[Dict[str, Any]]:
    method_fields = [
        "repository",
        "commit",
        "config_sha256",
        "parameter_count",
        "training_compute_budget",
        "inference_compute_budget",
    ]
    control_prefixes = [
        "/method_and_baseline_plan/required_controls/" + str(index)
        for index in range(4)
    ]
    literature_prefixes = [
        "/method_and_baseline_plan/required_literature_comparator_families/"
        + str(index)
        for index in range(4)
    ]
    baseline_prefixes = [
        "/method_and_baseline_plan/external_domain_baselines/" + str(index)
        for index in range(2)
    ]
    rows: List[Dict[str, Any]] = [
        {
            "ordinal": 0,
            "inventory_id": "PRIMARY_METHOD_AND_COMPARATOR_IDENTITIES",
            "blocker_id": "B06",
            "field_ids": _f_range(62, 73),
            "field_count": 12,
            "json_pointers": _pair_paths(
                [
                    "/method_and_baseline_plan/primary_method",
                    "/method_and_baseline_plan/primary_comparator",
                ],
                method_fields,
            ),
            "dedicated_f_rows_present": True,
            "current_state": "OPEN",
            "minimum_closure": (
                "FROZEN_IDENTITY_CONFIG_COUNT_AND_COMPUTE_MANIFEST_WITH_"
                "VALIDATION_RECEIPT"
            ),
        },
        {
            "ordinal": 1,
            "inventory_id": "FOUR_REQUIRED_CONTROLS",
            "blocker_id": "B06",
            "field_ids": _f_range(74, 81),
            "field_count": 8,
            "json_pointers": _pair_paths(
                control_prefixes, ["implementation", "config_sha256"]
            ),
            "dedicated_f_rows_present": True,
            "current_state": "OPEN",
            "minimum_closure": (
                "FOUR_SEPARATE_FROZEN_CONFIGURATIONS_WITH_IDENTITY_AND_"
                "SEPARATION_TESTS"
            ),
        },
        {
            "ordinal": 2,
            "inventory_id": "FOUR_LITERATURE_COMPARATOR_FAMILIES",
            "blocker_id": "B06",
            "field_ids": _f_range(82, 89),
            "field_count": 8,
            "json_pointers": _pair_paths(
                literature_prefixes,
                [
                    "implementation_by_domain",
                    "inapplicability_or_equivalence_justification_by_domain",
                ],
            ),
            "dedicated_f_rows_present": True,
            "current_state": "OPEN",
            "minimum_closure": (
                "FAMILY_BY_DOMAIN_IMPLEMENTATION_OR_JUSTIFICATION_MATRIX_" "WITH_AUDIT"
            ),
        },
        {
            "ordinal": 3,
            "inventory_id": "TWO_EXTERNAL_DOMAIN_BASELINES",
            "blocker_id": "B06",
            "field_ids": _f_range(90, 103),
            "field_count": 14,
            "json_pointers": _pair_paths(
                baseline_prefixes,
                [
                    "method_id",
                    "repository",
                    "commit",
                    "license",
                    "config_sha256",
                    "native_capability_and_extension_statement",
                    "tuning_budget",
                ],
            ),
            "dedicated_f_rows_present": True,
            "current_state": "OPEN",
            "minimum_closure": (
                "FROZEN_REPOSITORY_LICENSE_CONFIG_CAPABILITY_AND_TUNING_" "RECORDS"
            ),
        },
        {
            "ordinal": 4,
            "inventory_id": "MATCHED_COMPUTE_FORMULA",
            "blocker_id": "B06",
            "field_ids": ["F104"],
            "field_count": 1,
            "json_pointers": [
                "/method_and_baseline_plan/matched_total_compute_formula"
            ],
            "dedicated_f_rows_present": True,
            "current_state": "OPEN",
            "minimum_closure": "FROZEN_FORMULA_CALCULATOR_AND_VALIDATION_RECEIPT",
        },
        {
            "ordinal": 5,
            "inventory_id": "RUNTIME_IDENTITY",
            "blocker_id": "B08",
            "field_ids": _f_range(150, 153),
            "field_count": 4,
            "json_pointers": [
                "/compute_and_fairness_plan/hardware",
                "/compute_and_fairness_plan/software_environment_sha256",
                "/compute_and_fairness_plan/container_or_lockfile_sha256",
                "/compute_and_fairness_plan/deterministic_settings",
            ],
            "dedicated_f_rows_present": True,
            "current_state": "OPEN_RUNTIME_IDENTITY_UNAPPROVED",
            "minimum_closure": (
                "RUNTIME_IDENTITY_MANIFEST_BOUND_TO_HARDWARE_ENVIRONMENT_AND_LOCK"
            ),
        },
        {
            "ordinal": 6,
            "inventory_id": "RESOURCE_CEILINGS_AND_ALLOCATIONS",
            "blocker_id": "B08",
            "field_ids": _f_range(154, 162),
            "field_count": 9,
            "json_pointers": [
                "/compute_and_fairness_plan/per_run_wall_time_ceiling",
                "/compute_and_fairness_plan/per_run_accelerator_hour_ceiling",
                "/compute_and_fairness_plan/per_run_peak_memory_ceiling",
                "/compute_and_fairness_plan/per_run_model_evaluation_ceiling",
                "/compute_and_fairness_plan/pilot_compute_allocation",
                "/compute_and_fairness_plan/tuning_compute_allocation",
                "/compute_and_fairness_plan/final_compute_allocation",
                "/compute_and_fairness_plan/failure_reserve",
                "/compute_and_fairness_plan/total_compute_ceiling",
            ],
            "dedicated_f_rows_present": True,
            "current_state": "OPEN",
            "minimum_closure": (
                "VALIDATED_BUDGET_MANIFEST_CAPACITY_AND_ALLOCATION_RECEIPT_"
                "WITH_NO_TOP_UP_RULE"
            ),
        },
        {
            "ordinal": 7,
            "inventory_id": "TRAINING_AND_CHECKPOINT_POLICY",
            "blocker_id": "B12",
            "field_ids": _f_range(139, 147),
            "field_count": 9,
            "json_pointers": [
                "/training_and_checkpoint_plan/optimizer",
                "/training_and_checkpoint_plan/learning_rate_schedule",
                "/training_and_checkpoint_plan/precision",
                "/training_and_checkpoint_plan/batch_construction",
                "/training_and_checkpoint_plan/maximum_epochs_or_steps",
                "/training_and_checkpoint_plan/validation_metric",
                "/training_and_checkpoint_plan/early_stopping_patience",
                "/training_and_checkpoint_plan/checkpoint_tie_rule",
                "/training_and_checkpoint_plan/maximum_tuning_trials_per_method",
            ],
            "dedicated_f_rows_present": True,
            "current_state": "OPEN",
            "minimum_closure": (
                "FROZEN_TRAINING_PLAN_MANIFEST_AND_CONSISTENCY_VALIDATION"
            ),
        },
        {
            "ordinal": 8,
            "inventory_id": "FORMAL_TEST_28",
            "blocker_id": "B12",
            "field_ids": [],
            "field_count": 0,
            "json_pointers": [],
            "dedicated_f_rows_present": False,
            "current_state": "OPEN_CP50_V26_DRAFT_PREREQUISITE_ONLY",
            "minimum_closure": (
                "GENERIC_RUNNER_AND_TEST28_SCHEDULE_BINDING_CUSTODY_POWER_"
                "THRESHOLDS_32768_REQUEST_CAMPAIGN_554_ESTIMAND_INDEPENDENT_"
                "RECOMPUTATION_AND_TERMINAL_RECEIPT"
            ),
            "exact_missing_blockers": [
                "confirmatory_custody",
                "power_and_thresholds",
                "runner_and_recomputation",
                "unconditional_operational_predictions",
            ],
            "cp75_reviewer_item_revived": False,
        },
        {
            "ordinal": 9,
            "inventory_id": "FORMAL_TEST_29",
            "blocker_id": "B12",
            "field_ids": [],
            "field_count": 0,
            "json_pointers": [],
            "dedicated_f_rows_present": False,
            "current_state": "OPEN",
            "minimum_closure": (
                "EXACT_THINNING_DESTINATION_IMPLEMENTATION_QUADRATURE_"
                "TOLERANCES_TOTALITY_LIVENESS_AND_INDEPENDENT_RECOMPUTATION"
            ),
            "exact_missing_obligations": [
                "EXACT_DESTINATION_LAWS",
                "EXACT_TILTED_RATES",
                "PERSISTENT_LINEAGE",
                "TOTALITY_AND_LIVENESS",
            ],
        },
        {
            "ordinal": 10,
            "inventory_id": "FORMAL_TEST_30",
            "blocker_id": "B12",
            "field_ids": [],
            "field_count": 0,
            "json_pointers": [],
            "dedicated_f_rows_present": False,
            "current_state": "PENDING",
            "minimum_closure": (
                "COUPLED_PATH_COARSE_EQUALS_SUM_FINE_PERSISTENT_LINEAGE_FROZEN_"
                "LEVELS_AND_TOLERANCES_WITH_RECOMPUTATION"
            ),
            "exact_missing_obligations": [
                "TAG4_BROWNIAN_STREAM_CONSUMPTION",
                "TAG5_BROWNIAN_STREAM_CONSUMPTION",
                "PERSISTENT_EDIT_LINEAGE",
                "STEP_HALVING_COUPLING",
            ],
        },
        {
            "ordinal": 11,
            "inventory_id": "WHOLE_METHOD_INTEGRATION",
            "blocker_id": "B12",
            "field_ids": [],
            "field_count": 0,
            "json_pointers": [],
            "dedicated_f_rows_present": False,
            "current_state": "ABSENT_UNQUALIFIED",
            "minimum_closure": (
                "HASH_BOUND_INITIALIZER_JUMP_BROWNIAN_PATH_OUTPUT_INTEGRATION_"
                "WITH_ADVERSARIAL_KNOWN_LAW_AND_WHOLE_METHOD_RECEIPT"
            ),
        },
        {
            "ordinal": 12,
            "inventory_id": "GENERIC_PRODUCTION_RUNNER_AND_CUSTODY",
            "blocker_id": "B12",
            "field_ids": [],
            "field_count": 0,
            "json_pointers": [],
            "dedicated_f_rows_present": False,
            "current_state": "ABSENT_UNAPPROVED",
            "minimum_closure": (
                "TYPED_RUNNER_BINDER_IMMUTABLE_PLAN_RUNTIME_RECORDER_FAILURE_"
                "NO_RETRY_LEDGER_INDEPENDENT_EVALUATOR_AND_AUTHORIZATION_RECEIPT"
            ),
        },
        {
            "ordinal": 13,
            "inventory_id": "FINAL_TEST_ACCESS_FACT",
            "blocker_id": "B12",
            "field_ids": ["F172"],
            "field_count": 1,
            "json_pointers": ["/freeze_predicate/test_data_unopened_before_freeze"],
            "dedicated_f_rows_present": True,
            "current_state": "NULL_OPEN_PROSPECTIVE_SEAL_ONLY",
            "minimum_closure": (
                "FINAL_AUTHORIZED_ACQUISITION_SNAPSHOT_SPLIT_ESCROW_AND_"
                "ACCESS_LOG_RECEIPT_AFTER_ALL_PRECEDING_GATES"
            ),
            "separate_from_65_method_runtime_fields": True,
        },
    ]
    return rows


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "source": "CONVERSATION_VISIBLE_TEXT",
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalization": "ONLY_TRAILING_TRANSPORT_WHITESPACE_OR_ENTITY_UNBOUND",
    "raw_transport_bytes_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "cryptographic_user_authentication": False,
    "static_package_construction_authorized": True,
    "static_package_read_only_audit_authorized": True,
    "user_selected_file_paths_or_count": False,
    "agent_selected_bounded_file_count": 4,
    "user_selected_route_values": False,
    "agent_selected_route_values": True,
    "user_wording_second_week_tasks": True,
    "solo_block2_label_and_sw3_to_sw4_mapping_is_agent_interpretation": True,
    "user_selected_solo_block2_label_or_calendar_mapping": False,
    "authorized_package_paths": [HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH],
    "external_contact_authorized": False,
    "license_or_governance_request_authorized": False,
    "data_access_or_acquisition_authorized": False,
    "snapshot_or_split_authorized": False,
    "escrow_operation_authorized": False,
    "network_or_connector_authorized": False,
    "training_authorized": False,
    "runtime_approval_authorized": False,
    "scientific_execution_authorized": False,
    "formal_test_execution_authorized": False,
    "production_authorized": False,
    "scientific_campaign_or_protocol_entropy_authorized": False,
    "scientific_or_operational_subprocess_route_authorized": False,
    "ordinary_software_qualification_interpreter_processes_performed": True,
    "pytest_temporary_fixtures_used": True,
    "temporary_name_randomness_absence_claimed": False,
    "authority_or_runtime_child_launched": False,
    "scientific_seed_or_protocol_entropy_consumed": False,
    "canonical_operational_or_scientific_effect": False,
    "claim_promotion_authorized": False,
    "submission_authorized": False,
    "honest_host_procedural_only": True,
    "malicious_host_resistance_claimed": False,
    "record_self_digest_is_user_authentication": False,
}


EXPECTED_C17: Mapping[str, Any] = {
    "route": C17_ROUTE,
    "orientation": "KL(P_H || P_HHAT)_TARGET_FIRST",
    "component_order": ["K0", "KC", "K_PLUS", "K_MINUS", "K_REPLACEMENT"],
    "simultaneous_upper_bound_order": [
        "U0",
        "UC",
        "U_PLUS",
        "U_MINUS",
        "U_REPLACEMENT",
    ],
    "target_occupation_or_exact_domination_required": True,
    "exact_radon_nikodym_factors_required_if_dominated": True,
    "every_legal_jump_family_covered_required": True,
    "nce_value_evidence_may_be_retained": True,
    "nce_used_as_path_certificate": False,
    "coercivity_claim_selected": False,
    "a1_through_a12_proved": False,
    "finite_nonvacuous_bounds_present": False,
    "c17_proved": False,
    "c17_claim_promoted": False,
    "confirmatory_execution_authorized": False,
}


EXPECTED_SUPPORT: Mapping[str, Any] = {
    "policy": SUPPORT_POLICY,
    "clean_kernel_kept_separate": True,
    "normalized_observation_reference_required": True,
    "acquisition_justified_full_support_component_required": True,
    "positive_mixture_weight_frozen_before_contact_required": True,
    "theorem_convenience_noise_forbidden": True,
    "clipping_forbidden": True,
    "positive_finite_information_on_all_occupiable_states_required": True,
    "finite_positive_normalizers_required": True,
    "shared_base_generator_required": True,
    "shared_base_structural_zeros_required": True,
    "target_positive_occupied_edge_must_remain_candidate_positive": True,
    "failure_disposition": "DOMAIN_NOT_ADMITTED",
    "structural_zero_extension_selected": False,
    "physionet_route_verified": False,
    "retail_route_verified": False,
    "physionet_prereg_field_remains_null": True,
    "retail_prereg_field_remains_null": True,
    "c19_closed": False,
    "domain_admission_promoted": False,
}


EXPECTED_CKS: Mapping[str, Any] = {
    "route_status": CKS_ROUTE,
    "proof_variant": CKS_VARIANT,
    "favorable_direction_selected": False,
    "primary_metric_selected": False,
    "primary_metric_proof_gate_passed": False,
    "cks_characteristicness_proved": False,
    "cks_proof_complete": False,
    "b04_closed": False,
    "test_data_access_permitted": False,
    "primary_literature_lookup_performed_by_root": True,
    "dataset_source_license_governance_access_contact_performed_in_cks_audit": False,
    "validator_and_tests_network_access": False,
    "count_and_signed_measure_obligations": [
        "EQUAL_CONFIGURATION_EMBEDDINGS_IMPLY_EQUAL_EVENT_COUNTS",
        "EMPTY_CONFIGURATION_IDENTIFIED_SEPARATELY",
        "EQUAL_POSITIVE_COUNTS_AND_EVENT_EMBEDDINGS_IMPLY_EQUAL_NORMALIZED_EMPIRICAL_MEASURES",
        "EVENT_MULTIPLICITIES_RETAINED",
        "EVERY_NONZERO_ADMISSIBLE_FINITE_SIGNED_DIFFERENCE_MEASURE_DETECTED",
        "EXACT_EVENT_SPACE_AND_ALL_TRANSFORMS_CAP_HORIZON_SEGMENTATION_OVERFLOW_AND_STRUCTURAL_ZEROS_FROZEN",
        "EXACT_NOT_RANDOM_FEATURE_KERNEL_UNLESS_SEPARATE_APPROXIMATION_THEOREM",
        "FINITE_STRICTLY_POSITIVE_TRAINING_ONLY_GAUSSIAN_BANDWIDTH",
        "AT_LEAST_TWO_INDEPENDENT_CONDITIONAL_DRAWS_PER_SCORED_CASE",
        "POSITIVE_GROUP_WEIGHTS_AGGREGATION_AND_NUMERICAL_SAFEGUARDS_FROZEN",
        "SCHEMA_OR_KERNEL_CHANGE_INVALIDATES_PROOF",
        "EXPECTED_CKS_REGRET_EQUALS_SQUARED_MMD_WITH_EQUALITY_ONLY_AT_TARGET",
    ],
    "reference_only_literature": [
        {
            "ordinal": 0,
            "role": "FINITE_SIGNED_MEASURE_EMBEDDINGS_REFERENCE",
            "url": "https://arxiv.org/abs/1003.0887",
            "remote_bytes_custody_bound": False,
            "contacted_by_this_package": False,
            "previously_looked_up_by_root": True,
            "exact_remote_response_receipt_bound": False,
            "proves_exact_project_kernel": False,
        },
        {
            "ordinal": 1,
            "role": "GAUSSIAN_KERNELS_ON_HILBERT_SPACES_REFERENCE",
            "url": "https://arxiv.org/abs/2007.14697",
            "remote_bytes_custody_bound": False,
            "contacted_by_this_package": False,
            "previously_looked_up_by_root": True,
            "exact_remote_response_receipt_bound": False,
            "proves_exact_project_kernel": False,
        },
        {
            "ordinal": 2,
            "role": "CHARACTERISTIC_KERNELS_ON_HILBERT_BANACH_MEASURE_SPACES_REFERENCE",
            "url": "https://arxiv.org/abs/2206.07588",
            "remote_bytes_custody_bound": False,
            "contacted_by_this_package": False,
            "previously_looked_up_by_root": True,
            "exact_remote_response_receipt_bound": False,
            "proves_exact_project_kernel": False,
        },
        {
            "ordinal": 3,
            "role": "STRONG_NEGATIVE_TYPE_FALLBACK_REFERENCE",
            "url": "https://rdlyons.pages.iu.edu/pdf/dcov-published.pdf",
            "remote_bytes_custody_bound": False,
            "contacted_by_this_package": False,
            "previously_looked_up_by_root": True,
            "exact_remote_response_receipt_bound": False,
            "proves_exact_project_kernel": False,
        },
    ],
}


EXPECTED_EXTERNAL_OBSERVATION: Mapping[str, Any] = {
    "kernel_theory_literature_lookup_performed": True,
    "lookup_preceded_package": True,
    "prospective_seal_preceded_kernel_theory_lookup": True,
    "lookup_vs_seal_chronology_provenance": (
        "ORCHESTRATION_ORDERING_NOT_INDEPENDENT_TIMESTAMP_ATTESTATION"
    ),
    "exact_wall_clock_lookup_timestamp_bound": False,
    "lookup_authority_source": "USER_RESEARCH_REQUEST_PLUS_SYSTEM_NICHE_FACT_BROWSE_RULE",
    "lookup_provenance_strength": "ORCHESTRATION_DISCLOSURE_NOT_INDEPENDENT_NETWORK_AUDIT",
    "registered_bibliographic_targets_included": [
        "https://arxiv.org/abs/1003.0887",
        "https://arxiv.org/abs/2007.14697",
        "https://arxiv.org/abs/2206.07588",
        "https://rdlyons.pages.iu.edu/pdf/dcov-published.pdf",
    ],
    "registered_targets_are_complete_http_request_roster": False,
    "exact_http_or_search_request_count_known": False,
    "remote_response_receipts_bound": False,
    "remote_scholarly_bytes_bound": False,
    "registered_dataset_source_contact_performed": False,
    "license_governance_access_request_performed": False,
    "protected_data_or_outcome_accessed": False,
    "global_network_absence_claimed": False,
    "validator_and_tests_network_access": False,
    "prospective_seal_source_contact_interpretation": (
        "REGISTERED_PHYSIONET_RETAIL_DATA_ACQUISITION_LICENSE_GOVERNANCE_"
        "OR_ACCESS_SCOPE"
    ),
    "prospective_seal_interpretation_basis": [
        "PROTECTED_FUTURE_TEST_DATA_DEFINITION",
        "PHYSIONET_RETAIL_DATASET_ROSTER",
        "REQUIRED_PRECONTACT_PROTOCOL",
    ],
    "prospective_seal_bytes_modified": False,
    "retroactive_scope_relaxation_claimed": False,
    "prospective_seal_literal_scope_ambiguity_acknowledged": True,
    "independent_seal_compliance_adjudication_performed": False,
    "lookup_declared_seal_compliant": False,
    "lookup_declared_seal_violation": False,
    "scholarly_lookup_excluded_from_future_dataset_access_log": True,
    "dataset_documentation_license_governance_or_access_pages_excluded_from_future_log": False,
}


EXPECTED_PROTOCOL: Mapping[str, Any] = {
    "protocol_kind": "STATIC_PRECONTACT_DESIGN_NOT_POPULATED_INSTANCE",
    "current_state": "DESIGN_FROZEN_AWAITING_POPULATED_PRECONTACT_INSTANCE",
    "populated_instance_present": False,
    "populated_instance_admitted": False,
    "independent_review_present": False,
    "administrative_contact_authority_record_present": False,
    "data_access_authority_record_present": False,
    "future_instance_path_selected": None,
    "external_contact_performed_by_this_package": False,
    "registered_sources": [
        {
            "ordinal": 0,
            "domain_id": "physionet-challenge-2012",
            "source_url": PHYSIONET_URL,
            "url_contacted_by_this_package": False,
        },
        {
            "ordinal": 1,
            "domain_id": "online-retail-ii",
            "source_url": RETAIL_URL,
            "url_contacted_by_this_package": False,
        },
    ],
    "populated_instance_required_fields": [
        "STATIC_PACKAGE_RAW_AND_RECORD_SHA256",
        "EXACT_REGISTERED_SOURCE_URLS",
        "FINITE_ORDERED_ADMIN_AND_DATA_OPERATION_ROSTER",
        "EXACT_CONTACT_TARGETS_AND_PERMITTED_REQUEST_KINDS",
        "EXACT_SUCCESS_PREDICATE_AND_TERMINAL_DISPOSITION_PER_OPERATION",
        "ACQUISITION_SELECTORS_AND_SNAPSHOT_VERSION_SELECTION_RULES",
        "EXACT_SPLIT_PROPORTIONS_OR_COUNTS",
        "PHYSIONET_PATIENT_GROUP_SPLIT_AND_LEAKAGE_RULES",
        "RETAIL_TEMPORAL_CUTOFF_WINDOW_CUSTOMER_GROUP_AND_LEAKAGE_RULES",
        "DETERMINISTIC_SPLIT_ALGORITHM_AND_ALL_INPUTS",
        "ESCROW_IDENTITIES_ACCESS_CONTROL_AND_FINAL_OPENING_RULE",
        "LICENSE_GOVERNANCE_ETHICS_REQUIREMENTS_AND_RECEIPT_GATES",
        "APPEND_ONLY_HASH_LINKED_CONTACT_AND_ACCESS_LOG_SCHEMA",
        "TERMINAL_VIOLATION_AND_NO_REPAIR_DISPOSITION",
    ],
    "operation_contract": {
        "operation_rows_present": False,
        "finite_roster_required": True,
        "unique_global_ordinal_required": True,
        "domain_phase_target_and_request_kind_required": True,
        "success_predicate_required_per_operation": True,
        "terminal_disposition_required_per_operation": True,
        "operation_row_required_fields": [
            "GLOBAL_ORDINAL",
            "DOMAIN_ID",
            "PHASE",
            "EXACT_TARGET",
            "EXACT_PERMITTED_REQUEST_KIND",
            "MAXIMUM_ATTEMPT_COUNT",
            "AUTHORIZED_RETRY_COUNT",
            "EXACT_SUCCESS_PREDICATE",
            "EXACT_TERMINAL_DISPOSITION",
        ],
        "maximum_attempt_count_per_operation": 1,
        "authorized_retry_count_per_operation": 0,
        "undeclared_operation_permitted": False,
        "intent_claim_method": "O_EXCL_0600_FILE_FSYNC_PARENT_FSYNC",
        "intent_before_effect_required": True,
        "outcome_hash_linked_required": True,
        "operation_states": ["PLANNED", "INTENT_CLAIMED", "OUTCOME_RECORDED"],
        "outcome_kinds": ["SUCCESS", "DENIED", "FAILED", "CANCELLED"],
        "intent_without_outcome_disposition": "TERMINAL_SPENT_INCOMPLETE_NO_RETRY",
        "named_failure_disposition_map": {
            "ADMIN_DENIED": "ADMIN_CONTACT_TERMINAL_NO_GO",
            "ADMIN_FAILED": "ADMIN_CONTACT_TERMINAL_NO_GO",
            "ADMIN_CANCELLED": "ADMIN_CONTACT_TERMINAL_NO_GO",
            "REQUIRED_APPROVALS_INCOMPLETE": "APPROVALS_INCOMPLETE_TERMINAL_NO_GO",
            "SELECTED_VERSION_UNAVAILABLE": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
            "ACQUISITION_SELECTOR_MISMATCH": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
            "SNAPSHOT_IDENTITY_OR_HASH_MISMATCH": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
            "DATA_ACCESS_DENIED": "DATA_ACCESS_TERMINAL_NO_GO",
            "DATA_ACCESS_FAILED": "DATA_ACCESS_TERMINAL_NO_GO",
            "DATA_ACCESS_CANCELLED": "DATA_ACCESS_TERMINAL_NO_GO",
        },
        "unknown_or_omitted_outcome_may_count_as_success": False,
        "success_marker_without_full_predicate_may_advance": False,
        "failure_mapping_total_nonoverlapping_and_precedence_ordered_required": True,
        "phase_advances_only_after_all_declared_rows_terminal": True,
        "credentials_tokens_cookies_or_raw_secrets_in_log_permitted": False,
    },
    "phase_boundary": {
        "administrative_contact_phase_requires_approvals_already_complete": False,
        "administrative_contact_requires_populated_instance_review_authority_and_intent": True,
        "administrative_contact_scope": "ADMIN_METADATA_OR_APPROVAL_REQUEST_ONLY",
        "data_access_requires_completed_approval_receipts": True,
        "data_access_requires_separately_reviewed_instance_and_fresh_authority": True,
        "data_access_scope": "DATA_AUTHENTICATION_OR_DOWNLOAD",
    },
    "state_machine": [
        "DESIGN_FROZEN_AWAITING_POPULATED_PRECONTACT_INSTANCE",
        "PRECONTACT_INSTANCE_POPULATED_AWAITING_INDEPENDENT_REVIEW",
        "PRECONTACT_INSTANCE_REVIEWED_AWAITING_FRESH_ADMIN_CONTACT_AUTHORITY",
        "ADMIN_CONTACT_AUTHORIZED_AWAITING_DURABLE_INTENT",
        "ADMIN_CONTACT_INTENT_RESERVED_AWAITING_CONTACT",
        "ADMIN_CONTACT_OUTCOME_RECORDED_AWAITING_REQUIRED_APPROVALS",
        "APPROVALS_COMPLETE_AWAITING_REVIEWED_DATA_ACCESS_INSTANCE",
        "DATA_ACCESS_INSTANCE_REVIEWED_AWAITING_FRESH_DATA_ACCESS_AUTHORITY",
        "DATA_ACCESS_AUTHORIZED_AWAITING_DURABLE_INTENT",
        "DATA_ACCESS_INTENT_RESERVED_AWAITING_ACCESS",
        "SNAPSHOT_OBSERVED_AND_CUSTODIED_AWAITING_DETERMINISTIC_SPLIT",
        "SPLIT_ASSIGNED_AND_HELD_OUT_ESCROW_ACTIVE",
        "FINAL_OPENING_AWAITING_SEPARATE_AUTHORITY",
    ],
    "terminal_no_go_states": [
        "ADMIN_CONTACT_TERMINAL_NO_GO",
        "APPROVALS_INCOMPLETE_TERMINAL_NO_GO",
        "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
        "DATA_ACCESS_TERMINAL_NO_GO",
    ],
    "only_exact_success_predicate_may_advance": True,
    "terminal_no_go_permits_replacement_source_selector_operation_or_retry": False,
    "future_observed_slots": {
        "observed_snapshot_versions": None,
        "raw_snapshot_sha256_by_domain": None,
        "snapshot_byte_counts_by_domain": None,
        "etag_or_equivalent_by_domain": None,
        "license_text_receipts": None,
        "governance_approval_receipts": None,
        "ethics_approval_receipts": None,
        "administrative_contact_outcomes": None,
        "data_access_outcomes": None,
        "split_manifest_sha256": None,
        "split_counts": None,
        "escrow_receipts": None,
        "access_log_head_sha256": None,
    },
    "violation_rule": {
        "terminal_state": "SOLO_BLOCK2_PRECONTACT_PROTOCOL_VIOLATION_TERMINAL",
        "conditions": [
            "CONTACT_BEFORE_POPULATED_INSTANCE_REVIEW_FRESH_AUTHORITY_OR_DURABLE_INTENT",
            "DATA_ACCESS_BEFORE_APPROVALS_REVIEWED_ACCESS_INSTANCE_FRESH_AUTHORITY_OR_DURABLE_INTENT",
            "UNDECLARED_OPERATION_OR_RETRY",
            "UNLOGGED_CONTACT_OR_ACCESS_ATTEMPT",
        ],
        "repair_by_deletion_resplit_or_reacquisition_permitted": False,
        "claim_promotion_or_evidence_admission_permitted": False,
    },
}


EXPECTED_CHECKLIST: Mapping[str, Any] = {
    "theory_route_selection_frozen": True,
    "metric_route_selection_frozen": True,
    "method_gap_inventory_frozen": True,
    "static_precontact_protocol_design_frozen": True,
    "dataset_source_license_governance_or_access_requests_opened_by_package": False,
    "validator_and_tests_network_access": False,
    "validator_source_process_writer_or_network_api_exposed": False,
    "hostile_test_source_process_or_network_api_exposed": False,
    "hostile_test_writer_scope": "PYTEST_TEMPORARY_REPLICAS_ONLY",
    "canonical_package_or_evidence_file_write_by_package_authored_code": False,
    "pytest_cache_metadata_mutation_observed": True,
    "global_workspace_write_absence_claimed": False,
    "qualification_python_bytecode_disabled": True,
    "qualification_pytest_cacheprovider_disabled": True,
    "source_safety_is_ast_and_runtime_guard_not_malicious_host_proof": True,
    "primary_literature_lookup_performed_by_root": True,
    "global_external_request_absence_independently_verified": False,
    "static_design_control_predicate": "SOLO_BLOCK2_STATIC_DESIGN_PACKAGE_VALIDATED",
    "static_design_control_predicate_value_after_validation": True,
    "static_design_control_is_preregistration_field": False,
    "timetable_checkbox_closed_by_package": False,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_tests_closed": 0,
    "result_slots_filled": 0,
    "effective_unresolved_field_count": 172,
    "effective_open_blocker_count": 12,
    "effective_open_execution_blocker_count": 10,
    "effective_open_submission_blocker_count": 2,
    "method_runtime_open_field_count": 65,
    "b06_open_field_count": 43,
    "b12_training_open_field_count": 9,
    "b08_open_field_count": 13,
    "f172_separate_and_open": True,
    "c17_proved": False,
    "cks_characteristicness_proved": False,
    "primary_metric_selected": False,
    "domain_admission_complete": False,
    "r1_through_r4_executed": False,
    "runtime_approval_authorized": False,
    "scientific_execution_authorized": False,
}


EXPECTED_SCOPE_REVIEW: Mapping[str, Any] = {
    "review_kind": "EXPLICIT_PRE_OUTCOME_FOUR_FILE_SCOPE_REVIEW",
    "physical_file_count": 4,
    "one_validation_package": True,
    "named_project_control_predicates": [
        "THEORY_ROUTE_SELECTION_FROZEN",
        "METRIC_ROUTE_SELECTION_FROZEN",
        "METHOD_GAP_INVENTORY_FROZEN",
        "STATIC_PRECONTACT_PROTOCOL_DESIGN_FROZEN",
    ],
    "targets_single_blocker": False,
    "automatic_two_artifact_exemption_claimed": False,
    "shared_authority_boundary": True,
    "shared_immutable_input_roster": True,
    "shared_self_digested_machine_record": True,
    "shared_hostile_validator_suite": True,
    "fields_closed": 0,
    "blockers_closed": 0,
    "formal_tests_closed": 0,
    "results_filled": 0,
    "operational_instance_proof_implementation_tracker_or_contact_receipt_in_scope": False,
    "tracker_may_consume_one_way_only_after_explicit_rule_adoption": True,
}


EXPECTED_ANONYMITY: Mapping[str, Any] = {
    "internal_evidence_only": True,
    "anonymous_or_public_submission_inclusion_permitted": False,
    "publication_safe_derivative_required": True,
    "fresh_anonymity_audit_required": True,
    "raw_visible_authority_text_in_derivative_permitted": False,
    "raw_or_record_digests_in_derivative_permitted": False,
    "internal_paths_in_derivative_permitted": False,
    "mutable_snapshot_receipts_in_derivative_permitted": False,
    "contact_targets_or_operational_custody_details_in_derivative_permitted": False,
    "excluded_provenance_reconstruction_permitted": False,
    "sanitized_design_selections_and_unresolved_status_only": True,
    "local_absolute_paths_present": False,
}


EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "state",
    "global_state",
    "package_kind",
    "reported_date",
    "authority_provenance",
    "live_immutable_input_bindings",
    "historical_snapshot_inputs",
    "c17_selection",
    "common_support_selection",
    "cks_selection",
    "external_observation_boundary",
    "method_gap_inventory",
    "precontact_protocol_design",
    "checklist_effects",
    "scope_review",
    "publication_anonymity_boundary",
    "package_bindings",
    "record_sha256",
}


def _resolve_pointer(value: Any, pointer: str) -> Any:
    current = value
    if not pointer.startswith("/"):
        raise ValidationError("pointer invalid")
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if type(current) is list:
            if not token.isdigit():
                raise ValidationError("pointer index invalid")
            current = current[int(token)]
        elif type(current) is dict:
            current = current[token]
        else:
            raise ValidationError("pointer traversal invalid")
    return current


def _validate_no_absolute_paths(value: Any, key: str = "") -> None:
    if type(value) is dict:
        for child_key, child in value.items():
            _validate_no_absolute_paths(child, child_key)
    elif type(value) is list:
        for child in value:
            _validate_no_absolute_paths(child, key)
    elif type(value) is str and (key == "path" or key.endswith("_path")):
        if Path(value).is_absolute() or ".." in Path(value).parts:
            raise ValidationError("absolute or unsafe local path")


def _validate_live_inputs(root: Path, record: Mapping[str, Any]) -> Dict[str, bytes]:
    _strict_equal(
        record.get("live_immutable_input_bindings"),
        [dict(item) for item in LIVE_IMMUTABLE_BINDINGS],
        "live immutable bindings",
    )
    raws: Dict[str, bytes] = {}
    for template in LIVE_IMMUTABLE_BINDINGS:
        raw = _stable_read(root, template["path"])
        raws[template["path"]] = raw
        observed = _binding(
            template["ordinal"],
            template["role"],
            template["path"],
            raw,
            record_digest=template.get("record_sha256"),
        )
        _strict_equal(observed, dict(template), "live binding bytes")

    prereg = json.loads(raws[PREREGISTRATION_PATH].decode("ascii"))
    if type(prereg) is not dict:
        raise ValidationError("preregistration type invalid")
    if prereg.get("state") != GLOBAL_STATE:
        raise ValidationError("preregistration state changed")
    if prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("preregistration authority changed")
    if [domain.get("source_url") for domain in prereg.get("domains", [])] != [
        PHYSIONET_URL,
        RETAIL_URL,
    ]:
        raise ValidationError("registered source URL changed")
    if [
        domain.get("positive_or_common_support_route")
        for domain in prereg.get("domains", [])
    ] != [None, None]:
        raise ValidationError("domain support route no longer null")

    closure = json.loads(raws[CLOSURE_PATH].decode("ascii"))
    if type(closure) is not dict:
        raise ValidationError("closure type invalid")
    if closure.get("record_sha256") != LIVE_IMMUTABLE_BINDINGS[1]["record_sha256"]:
        raise ValidationError("closure self carrier mismatch")
    if _self_digest(closure) != closure["record_sha256"]:
        raise ValidationError("closure self digest invalid")
    nulls = closure.get("null_projection", {})
    blockers = closure.get("blocker_projection", {})
    if (
        type(nulls) is not dict
        or type(blockers) is not dict
        or nulls.get("effective_total_unresolved_null_count") != 172
        or nulls.get("effective_preexecution_unresolved_null_count") != 166
        or nulls.get("effective_deferred_postexecution_unresolved_null_count") != 6
        or blockers.get("effective_unresolved_blocker_count") != 12
        or blockers.get("blockers_closed_by_closure") != 0
    ):
        raise ValidationError("closure projection changed")

    seal = json.loads(raws[SEAL_MACHINE_PATH].decode("ascii"))
    if type(seal) is not dict:
        raise ValidationError("seal type invalid")
    if seal.get("record_sha256") != LIVE_IMMUTABLE_BINDINGS[3]["record_sha256"]:
        raise ValidationError("seal self carrier mismatch")
    if _self_digest(seal) != seal["record_sha256"]:
        raise ValidationError("seal self digest invalid")
    if (
        seal.get("state")
        != "NO_TEST_DATA_ACQUIRED_USER_REPORTED_PROSPECTIVE_SEAL_ACTIVE"
    ):
        raise ValidationError("seal state changed")
    boundary = seal.get("authority_boundary", {})
    custody = seal.get("custody_projection", {})
    if (
        type(boundary) is not dict
        or type(custody) is not dict
        or boundary.get("connector_contact_authorized") is not False
        or boundary.get("network_access_authorized") is not False
        or boundary.get("test_data_acquisition_authorized") is not False
        or custody.get("effective_unresolved_null_count") != 172
        or custody.get("open_blocker_count") != 12
        or custody.get("unresolved_fields_closed_by_seal") != 0
    ):
        raise ValidationError("seal nonclaim changed")
    return raws


def _validate_inventory_against_prereg(
    inventory: Sequence[Mapping[str, Any]], prereg: Mapping[str, Any]
) -> None:
    field_ids: List[str] = []
    pointers: List[str] = []
    for row in inventory:
        field_ids.extend(row["field_ids"])
        pointers.extend(row["json_pointers"])
        for pointer in row["json_pointers"]:
            if _resolve_pointer(prereg, pointer) is not None:
                raise ValidationError("inventory field is not null: " + pointer)
    if len(field_ids) != len(set(field_ids)):
        raise ValidationError("field ID overlap")
    if len(pointers) != len(set(pointers)):
        raise ValidationError("JSON pointer overlap")
    method_runtime_ids = [item for item in field_ids if item != "F172"]
    if len(method_runtime_ids) != 65:
        raise ValidationError("method/runtime field total mismatch")
    if field_ids.count("F172") != 1:
        raise ValidationError("F172 separation mismatch")


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate exact static-package custody and return a privacy-safe status."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    machine_raw = _stable_read(workspace, MACHINE_PATH)
    record = json.loads(machine_raw.decode("ascii"))
    if type(record) is not dict:
        raise ValidationError("machine record must be exact dict")
    if set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("top-level field roster mismatch")
    if canonical_machine_bytes(record) != machine_raw:
        raise ValidationError("machine record not canonical")
    if type(record.get("record_sha256")) is not str:
        raise ValidationError("record self digest type invalid")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("record self digest invalid")

    _strict_equal(record["schema_version"], SCHEMA, "schema")
    _strict_equal(record["state"], STATE, "state")
    _strict_equal(record["global_state"], GLOBAL_STATE, "global state")
    _strict_equal(record["package_kind"], "STATIC_DESIGN_SELECTION_FREEZE_ONLY", "kind")
    _strict_equal(record["reported_date"], "2026-08-30", "date")
    _strict_equal(record["authority_provenance"], dict(EXPECTED_AUTHORITY), "authority")
    _strict_equal(record["historical_snapshot_inputs"], _historical_rows(), "snapshots")
    _strict_equal(record["c17_selection"], dict(EXPECTED_C17), "C17")
    _strict_equal(record["common_support_selection"], dict(EXPECTED_SUPPORT), "support")
    _strict_equal(record["cks_selection"], dict(EXPECTED_CKS), "CKS")
    _strict_equal(
        record["external_observation_boundary"],
        dict(EXPECTED_EXTERNAL_OBSERVATION),
        "external observation",
    )
    inventory = expected_method_inventory()
    _strict_equal(record["method_gap_inventory"], inventory, "method inventory")
    _strict_equal(
        record["precontact_protocol_design"], dict(EXPECTED_PROTOCOL), "protocol"
    )
    _strict_equal(record["checklist_effects"], dict(EXPECTED_CHECKLIST), "checklist")
    _strict_equal(record["scope_review"], dict(EXPECTED_SCOPE_REVIEW), "scope review")
    _strict_equal(
        record["publication_anonymity_boundary"],
        dict(EXPECTED_ANONYMITY),
        "anonymity",
    )
    _validate_no_absolute_paths(record)

    live_raws = _validate_live_inputs(workspace, record)
    prereg = json.loads(live_raws[PREREGISTRATION_PATH].decode("ascii"))
    _validate_inventory_against_prereg(inventory, prereg)

    expected_package_bindings: List[Dict[str, Any]] = []
    for ordinal, role, path in (
        (0, "HUMAN_FREEZE", HUMAN_PATH),
        (1, "READ_ONLY_VALIDATOR", VALIDATOR_PATH),
        (2, "HOSTILE_TEST", TEST_PATH),
    ):
        expected_package_bindings.append(
            _binding(ordinal, role, path, _stable_read(workspace, path))
        )
    _strict_equal(
        record["package_bindings"],
        expected_package_bindings,
        "package bindings",
    )

    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "static_design_control_predicate": True,
        "theory_route_selection_frozen": True,
        "metric_route_selection_frozen": True,
        "method_gap_inventory_frozen": True,
        "static_precontact_protocol_design_frozen": True,
        "dataset_source_license_governance_or_access_requests_opened_by_package": False,
        "validator_and_tests_network_access": False,
        "primary_literature_lookup_performed_by_root": True,
        "global_external_request_absence_independently_verified": False,
        "populated_instance_present": False,
        "external_contact_authorized": False,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "formal_tests_closed": 0,
        "result_slots_filled": 0,
        "effective_unresolved_field_count": 172,
        "effective_open_blocker_count": 12,
        "validation": "PASS",
    }


__all__ = [
    "ValidationError",
    "canonical_machine_bytes",
    "expected_method_inventory",
    "record_sha256",
    "validate",
]
