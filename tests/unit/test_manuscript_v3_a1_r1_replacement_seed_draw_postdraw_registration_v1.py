"""Closed-world hostile audit for the A1 R1 post-draw seed registration."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
from typing import Any, Dict, Mapping, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
HUMAN_RELATIVE_PATH = (
    "manuscript_v3/a1_r1_replacement_seed_draw_postdraw_registration_v1.md"
)
MACHINE_RELATIVE_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_replacement_seed_draw_postdraw_registration_v1.json"
)
TEST_RELATIVE_PATH = (
    "tests/unit/"
    "test_manuscript_v3_a1_r1_replacement_seed_draw_postdraw_registration_v1.py"
)
PRE_DRAW_HUMAN = "manuscript_v3/a1_r1_replacement_seed_draw_freeze_v1.md"
PRE_DRAW_MACHINE = (
    "research/fixtures/manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.json"
)
PRE_DRAW_MODULE = "research/diagnostics/finite_association_r1_replacement_seed_draw.py"
PRE_DRAW_TEST = "tests/unit/test_manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.py"
ATTEMPT_PATH = "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1.attempt.json"
TERMINAL_PATH = "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1"
PENDING_PATH = "artifacts/.manuscript_v3_a1_r1_replacement_seed_draw_v1.pending"
DRAW_PATH = TERMINAL_PATH + "/seed-draw-record.json"
REGISTRY_PATH = TERMINAL_PATH + "/replacement-seed-registry.json"
SUCCESS_PATH = TERMINAL_PATH + "/success-receipt.json"
FAILURE_PATH = TERMINAL_PATH + "/failure-receipt.json"
RUNTIME_MANIFEST_PATH = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
)

SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-replacement-seed-draw-" "postdraw-registration-v1"
)
REGISTRATION_DOMAIN = (SCHEMA + "\0").encode("ascii")
RECORD_DOMAINS = {
    ATTEMPT_PATH: b"heterodiff-r1-a1-replacement-seed-draw-attempt-v1\0",
    DRAW_PATH: b"heterodiff-r1-a1-replacement-seed-draw-record-v1\0",
    REGISTRY_PATH: b"heterodiff-r1-a1-replacement-seed-registry-v1\0",
    SUCCESS_PATH: b"heterodiff-r1-a1-replacement-seed-draw-success-v1\0",
}
EXPECTED_RAW_SELF = {
    ATTEMPT_PATH: (
        "fa9047433d62620d145fda0a9f56aabf4296003356d9c3b4336b455d1e4de76b",
        "ec5984402ee5f9dbde658713bfa43d4026e32851b8a7dff53ef703a7ac1d47d5",
    ),
    DRAW_PATH: (
        "63cff401182cf6502cd51d9d732eaccb0bec4c63ddbb4ff308b0d968a56dbd0f",
        "51702215c41e7832e12685cde8e8a1674c106956afb872d2e428a181be6c912b",
    ),
    REGISTRY_PATH: (
        "d2854c9b1bbc7fb668d5741c3544b4b47adef340bcf58e74db33ba461f9b378b",
        "2be16cc37b6e046c95538679b05e334b0f299e08eed5c1ac67be1a5077f18f05",
    ),
    SUCCESS_PATH: (
        "89705733ba5c26967981223fd760198be9844f5c38c7e793821bdda82aa37056",
        "d4f36bdf4a6fd6c1a363b80a98f25efbda5ec5faddcd04fe1dc330be4b67df65",
    ),
}
EXPECTED_PRE_DRAW_RAW = {
    PRE_DRAW_HUMAN: "c657d9276dccc28b2b826968c376925a23368683cdccea2cf948b92ffa4277d5",
    PRE_DRAW_MACHINE: "39b4b26a95b7ee867f53981638902d4b5ae00d7e58dbdc203bce6b3177b3cf56",
    PRE_DRAW_MODULE: "124d9e41cad3dc3a63c34e165a3d4bcfa380181f5efb83abd490ad61c9c99a9b",
    PRE_DRAW_TEST: "a3ebf3315f32c5765461cc92b1098fe065a5e681df7cd6faa6417fc58851b968",
}
PRE_DRAW_SELF = "79e285045a1b99cd22121b51b92746cc2027abd8ff31351ae182bb71da5154b6"

UNIVERSE = 1 << 53
EXCLUDED = [1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011]
ALLOWED_COUNT = UNIVERSE - len(EXCLUDED)
ENTROPY_SPACE = 1 << 256
ACCEPTANCE_LIMIT = ENTROPY_SPACE - 64
EXPECTED_RANK = 4052249444591748
REPLACEMENT = 4052249444591756
REGISTRY = [REPLACEMENT, 3253, 5003, 7411, 10007, 13007, 16001, 20011]
ENTROPY_SHA256 = "e0d75d1d1dc42748910d56d031205a431e2d619491b69eea2ae0ce4c9eaf2982"

PRODUCTION_ROOTS = [
    "artifacts/a1_finite_association_production_order_v1",
    "artifacts/a1_rank_stress_gate_v1.json",
    "artifacts/a1_rank_stress_gate_v1.json.prepared.json",
    "artifacts/a1_rank_stress_gate_v1.json.parent-exit.json",
    "artifacts/a1_exact_population_campaign_v4",
    "artifacts/a1_campaign_v4",
    "artifacts/a1_primary_metrics_v1",
    "artifacts/a1_primary_metrics_v2",
    "artifacts/a1_candidate_decision_v1",
    "artifacts/a1_independent_audit_v1",
    "artifacts/a1_publication_decision_v1",
]
PREDECESSOR_GROUPS = [
    "baseline_bindings",
    "closure_v2_bindings",
    "d1_bindings",
    "environment_bindings",
    "historical_source_bindings",
    "registration_bindings",
]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _semantic_digest(value: Mapping[str, Any], domain: bytes) -> str:
    body = dict(value)
    body["record_sha256"] = None
    return _sha256(domain + _canonical_json(body))


def _require_exact(observed: Any, expected: Any) -> None:
    """Compare canonical bytes so Python bool/int aliases cannot pass."""

    assert _canonical_json(observed) == _canonical_json(expected)


def _load_json(relative_path: str) -> Tuple[bytes, Dict[str, Any]]:
    payload = (ROOT / relative_path).read_bytes()
    value = json.loads(payload.decode("ascii"))
    assert type(value) is dict
    return payload, value


def _path_is_absent_no_entry(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return True
    return False


def _reopen_terminal_status_without_entropy() -> str:
    module_path = ROOT / PRE_DRAW_MODULE
    specification = importlib.util.spec_from_file_location(
        "postdraw_status_deep_reopen", module_path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    calls = []

    def forbidden_entropy(_: int) -> bytes:
        calls.append(True)
        raise AssertionError("post-draw status audit contacted entropy")

    original = module.secrets.token_bytes
    module.secrets.token_bytes = forbidden_entropy
    try:
        observed = module.status(ROOT)
    finally:
        module.secrets.token_bytes = original
    assert calls == []
    _require_exact(
        observed,
        {
            "schema": "heterodiff-r1-a1-replacement-seed-draw-status-v1",
            "state": "ATTEMPT_SPENT_TERMINAL_SUCCESS",
            "attempt_marker_present": True,
            "pending_terminal_present": False,
            "terminal_output_present": True,
            "validated_terminal_kind": "SUCCESS",
            "entropy_contacted_by_status": False,
            "candidate_seed_reported": False,
            "first_attempt_available": False,
            "retry_permitted": False,
        },
    )
    return observed["state"]


def _file_row(relative_path: str, semantic_sha256: Any = None) -> Dict[str, Any]:
    payload = (ROOT / relative_path).read_bytes()
    return {
        "path": relative_path,
        "raw_sha256": _sha256(payload),
        "bytes": len(payload),
        "lf_count": payload.count(b"\n"),
        "terminal_lf": payload.endswith(b"\n"),
        "semantic_sha256": semantic_sha256,
    }


def _custody_row(relative_path: str) -> Dict[str, Any]:
    path = ROOT / relative_path
    information = path.lstat()
    payload, record = _load_json(relative_path)
    raw_expected, self_expected = EXPECTED_RAW_SELF[relative_path]
    assert stat.S_ISREG(information.st_mode)
    assert not stat.S_ISLNK(information.st_mode)
    assert stat.S_IMODE(information.st_mode) == 0o600
    if payload != _canonical_json(record):
        raise AssertionError("raw custody record is not canonical JSON")
    assert _sha256(payload) == raw_expected
    assert record["record_sha256"] == self_expected
    assert _semantic_digest(record, RECORD_DOMAINS[relative_path]) == self_expected
    return {
        "path": relative_path,
        "raw_sha256": raw_expected,
        "record_sha256": self_expected,
        "schema": record["schema"],
        "bytes": len(payload),
        "lf_count": payload.count(b"\n"),
        "terminal_lf": payload.endswith(b"\n"),
        "canonical_json": True,
        "mode_octal": "0600",
        "is_regular_file": True,
        "is_symlink": False,
    }


def _flatten_predecessor_rows() -> Dict[str, Any]:
    payload, freeze = _load_json(PRE_DRAW_MACHINE)
    assert _sha256(payload) == EXPECTED_PRE_DRAW_RAW[PRE_DRAW_MACHINE]
    assert freeze["record_sha256"] == PRE_DRAW_SELF
    rows = {}
    for group in PREDECESSOR_GROUPS:
        assert type(freeze[group]) is dict
        for role, row in freeze[group].items():
            key = group + "." + role
            assert key not in rows
            rows[key] = row
            observed = _file_row(row["path"], row["semantic_sha256"])
            assert row == observed
            if row["semantic_sha256"] is not None:
                _, bound_record = _load_json(row["path"])
                semantic_key = (
                    "record_sha256"
                    if "record_sha256" in bound_record
                    else "diagnostic_record_sha256"
                )
                assert bound_record[semantic_key] == row["semantic_sha256"]
    assert len(rows) == 24
    return rows


def _expected_pre_draw_package() -> Dict[str, Any]:
    roles = {
        "human_freeze": PRE_DRAW_HUMAN,
        "machine_freeze": PRE_DRAW_MACHINE,
        "draw_module": PRE_DRAW_MODULE,
        "hostile_test": PRE_DRAW_TEST,
    }
    bindings = {}
    for role, path in roles.items():
        semantic = PRE_DRAW_SELF if path == PRE_DRAW_MACHINE else None
        row = _file_row(path, semantic)
        assert row["raw_sha256"] == EXPECTED_PRE_DRAW_RAW[path]
        bindings[role] = row
    return {
        "pre_draw_registration_id": "A1-R1-REPLACEMENT-SEED-DRAW-FREEZE-V1",
        "pre_draw_machine_record_sha256": PRE_DRAW_SELF,
        "pre_draw_files_mutated": False,
        "bindings": bindings,
    }


def _expected_predecessor_reopen() -> Dict[str, Any]:
    return {
        "source_sidecar_path": PRE_DRAW_MACHINE,
        "source_sidecar_record_sha256": PRE_DRAW_SELF,
        "binding_groups": PREDECESSOR_GROUPS,
        "binding_group_count": 6,
        "binding_row_count": 24,
        "all_rows_reopened_against_current_bytes": True,
        "rows": _flatten_predecessor_rows(),
    }


def _expected_custody() -> Dict[str, Any]:
    terminal = ROOT / TERMINAL_PATH
    info = terminal.lstat()
    assert stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
    assert stat.S_IMODE(info.st_mode) == 0o700
    children = sorted(path.name for path in terminal.iterdir())
    assert children == [
        "replacement-seed-registry.json",
        "seed-draw-record.json",
        "success-receipt.json",
    ]
    assert _path_is_absent_no_entry(ROOT / PENDING_PATH)
    assert _path_is_absent_no_entry(ROOT / FAILURE_PATH)
    return {
        "status_audit_state": _reopen_terminal_status_without_entropy(),
        "attempt_marker": _custody_row(ATTEMPT_PATH),
        "seed_draw_record": _custody_row(DRAW_PATH),
        "replacement_seed_registry": _custody_row(REGISTRY_PATH),
        "success_receipt": _custody_row(SUCCESS_PATH),
        "terminal_inventory": {
            "attempt_marker_present": True,
            "attempt_marker_is_nonsymlink_regular_file": True,
            "attempt_marker_mode_octal": "0600",
            "terminal_directory_path": TERMINAL_PATH,
            "terminal_directory_present": True,
            "terminal_directory_is_nonsymlink_directory": True,
            "terminal_directory_mode_octal": "0700",
            "terminal_regular_file_count": 3,
            "terminal_child_names": children,
            "all_terminal_files_mode_octal": "0600",
            "all_terminal_files_nonsymlink_regular": True,
            "unexpected_terminal_children": [],
            "pending_path": PENDING_PATH,
            "pending_present": False,
            "failure_receipt_path": FAILURE_PATH,
            "failure_receipt_present": False,
            "absence_checks_use_lstat_no_entry_semantics": True,
        },
    }


EXPECTED_MAPPING = {
    "universe_size_u_decimal": str(UNIVERSE),
    "original_excluded_seeds_e": EXCLUDED,
    "excluded_count": 8,
    "allowed_count_m_decimal": str(ALLOWED_COUNT),
    "entropy_space_decimal": str(ENTROPY_SPACE),
    "rejection_remainder": 64,
    "acceptance_limit_l_decimal": str(ACCEPTANCE_LIMIT),
    "acceptance_predicate": "X<L",
    "accepted": True,
    "x_less_than_l": True,
    "accepted_rank_formula": "X%M",
    "accepted_rank_decimal": str(EXPECTED_RANK),
    "unrank_order": "ASCENDING_EXCLUDED_SEEDS",
    "replacement_seed": REPLACEMENT,
    "replacement_ordinal": 0,
    "mapping_independently_recomputed": True,
}
EXPECTED_ENTROPY_BOUNDARY = {
    "entropy_source": "PYTHON_SECRETS_TOKEN_BYTES_OS_CSPRNG",
    "entropy_bytes": 32,
    "entropy_contact_count": 1,
    "entropy_byte_sha256": ENTROPY_SHA256,
    "fingerprint_is_postdraw_custody_only": True,
    "fingerprint_used_in_selection": False,
    "raw_entropy_hex_copied_into_human_registration": False,
    "raw_entropy_hex_copied_into_machine_registration": False,
    "entropy_integer_copied_into_human_registration": False,
    "entropy_integer_copied_into_machine_registration": False,
    "raw_entropy_remains_internal_draw_record_only": True,
    "second_entropy_contact_permitted": False,
}
EXPECTED_REGISTRY = {
    "registry_state": "IMMUTABLE_REPLACEMENT_SEED_REGISTERED",
    "original_seed_registry": EXCLUDED,
    "exposed_seed": 1729,
    "exposed_seed_disposition": "PILOT_NONCONFIRMATORY_EXPOSED",
    "exposure_scope": (
        "ALL_METHODS_LANES_AND_BUDGETS_WITH_BUDGET_WILDCARD_WHERE_NOT_APPLICABLE"
    ),
    "replacement_ordinal": 0,
    "replacement_seed": REPLACEMENT,
    "replacement_seed_registry": REGISTRY,
    "registry_length": 8,
    "registry_unique": True,
    "preserved_nonzero_ordinals": EXCLUDED[1:],
    "numeric_registry_resort_permitted": False,
    "partial_lane_substitution_permitted": False,
    "postdraw_grid_pruning_permitted": False,
    "different_replacements_by_lane_permitted": False,
}
EXPECTED_PROJECTION = {
    "exact_population_coordinate_count": 24,
    "primary_sampled_coordinate_count": 48,
    "control_sampled_coordinate_count": 72,
    "complete_sampled_coordinate_count": 120,
    "all_coordinates_including_exact_count": 144,
    "replacement_applies_to_ordinal_zero_across_every_method_lane_budget": True,
    "coordinates_executed": 0,
}
EXPECTED_STATE = {
    "attempt_consumed": True,
    "attempt_spent": True,
    "entropy_contacted": True,
    "entropy_contact_count": 1,
    "draw_performed": True,
    "draw_accepted": True,
    "replacement_seed_selected": True,
    "replacement_registry_frozen": True,
    "terminal_success_reopened": True,
    "current_state": "R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE",
    "global_state": "DRAFT_NOT_EXECUTABLE",
}
EXPECTED_REGISTRATION_ACTIVITY = {
    "draw_rerun": False,
    "entropy_contacted_by_registration": False,
    "rank_execution_performed": False,
    "training_execution_performed": False,
    "confirmatory_execution_performed": False,
    "production_execution_performed": False,
    "experiment_execution_performed": False,
    "registry_integration_performed": False,
    "source_amendment_performed": False,
    "runtime_capsule_created": False,
}
EXPECTED_NONCLAIMS = {
    "retry_permitted": False,
    "redraw_permitted": False,
    "top_up_permitted": False,
    "candidate_screening_permitted": False,
    "candidate_replacement_permitted": False,
    "second_entropy_contact_permitted": False,
    "registry_integration_complete": False,
    "source_amendment_complete": False,
    "runner_integration_complete": False,
    "execution_capsule_frozen": False,
    "runtime_identity_manifest_present": False,
    "rank_execution_authorized": False,
    "training_execution_authorized": False,
    "confirmatory_execution_authorized": False,
    "production_execution_authorized": False,
    "scientific_result_eligible": False,
    "r1_qualified": False,
    "r2_qualified": False,
    "c17_proved": False,
    "claim_promoted": False,
    "submission_ready": False,
    "checkpoint_selection_performed": False,
    "metric_selection_performed": False,
    "threshold_selection_performed": False,
    "success_rule_selection_performed": False,
    "overflow_policy_selection_performed": False,
    "rank_execution_performed": False,
    "training_execution_performed": False,
    "confirmatory_execution_performed": False,
    "production_execution_performed": False,
    "scientific_result_produced": False,
}
EXPECTED_NEXT_GATE = {
    "next_required_milestone": (
        "ADDITIVE_VERSIONED_REGISTRY_AWARE_SOURCE_AND_EXECUTION_CAPSULE_FREEZE"
    ),
    "historical_source_in_place_edit_permitted": False,
    "new_registry_aware_adapter_or_successor_required": True,
    "successful_registry_must_be_bound": True,
    "ordinal_zero_all_lane_projection_must_be_enforced": True,
    "formal_runtime_identity_manifest_required": True,
    "closed_execution_capsule_required": True,
    "launch_plan_phase_consumption_and_receipts_must_be_frozen": True,
    "fresh_zero_execution_hostile_audit_required": True,
    "completion_status": "NOT_STARTED",
    "execution_authorized_by_this_registration": False,
}
EXPECTED_ANONYMITY = {
    "internal_registration_not_submission_artifact": True,
    "raw_new_registration_paths": [
        HUMAN_RELATIVE_PATH,
        MACHINE_RELATIVE_PATH,
        TEST_RELATIVE_PATH,
    ],
    "raw_custody_paths": [
        ATTEMPT_PATH,
        TERMINAL_PATH,
        DRAW_PATH,
        REGISTRY_PATH,
        SUCCESS_PATH,
    ],
    "raw_draw_contains_entropy_hex": True,
    "raw_entropy_disclosed_in_registration": False,
    "entropy_fingerprint_disclosed_for_custody": True,
    "anonymous_submission_inclusion_permitted": False,
    "public_release_inclusion_permitted": False,
    "raw_custody_anonymous_submission_inclusion_permitted": False,
    "raw_custody_public_release_inclusion_permitted": False,
    "in_place_sanitization_permitted": False,
    "publication_safe_derivative_required": True,
    "publication_safe_derivative_path": None,
    "submission_include_exclude_roster_frozen": False,
    "fresh_publication_anonymity_audit_required": True,
    "human_contains_absolute_local_identity_path": False,
}
EXPECTED_TRUST = {
    "boundary": "PROCEDURAL_HONEST_HOST_AND_WORKSPACE_NOT_SECURITY_SANDBOX",
    "hostile_same_user_process_sandbox_claimed": False,
    "same_process_memory_tamper_resistance_claimed": False,
    "module_global_tamper_resistance_claimed": False,
    "registered_file_tamper_resistance_claimed": False,
}


def _expected_anti_selection_boundary() -> Dict[str, Any]:
    _, freeze = _load_json(PRE_DRAW_MACHINE)
    return freeze["anti_selection_boundary"]


def _expected_d1_exposure_boundary() -> Dict[str, Any]:
    _, freeze = _load_json(PRE_DRAW_MACHINE)
    return freeze["d1_exposure_boundary"]


def _expected_state_preservation() -> Dict[str, Any]:
    historical = _load_json(PRE_DRAW_MACHINE)[1]["historical_source_bindings"]
    hashes = {role: row["raw_sha256"] for role, row in historical.items()}
    for row in historical.values():
        assert _sha256((ROOT / row["path"]).read_bytes()) == row["raw_sha256"]
    for path in PRODUCTION_ROOTS:
        assert _path_is_absent_no_entry(ROOT / path)
    assert _path_is_absent_no_entry(ROOT / RUNTIME_MANIFEST_PATH)
    assert _path_is_absent_no_entry(ROOT / PENDING_PATH)
    return {
        "pre_draw_package_mutated": False,
        "draw_custody_artifacts_mutated": False,
        "historical_source_count": 7,
        "historical_sources_mutated": False,
        "historical_source_raw_sha256": hashes,
        "claim_ledger_mutated": False,
        "execution_preregistration_mutated": False,
        "closure_v2_mutated": False,
        "d1_artifacts_mutated": False,
        "cp76_snapshot_mutated": False,
        "production_order_mutated": False,
        "checked_production_roots": PRODUCTION_ROOTS,
        "checked_production_root_count": 11,
        "all_checked_production_roots_absent": True,
        "formal_runtime_identity_manifest_path": RUNTIME_MANIFEST_PATH,
        "formal_runtime_identity_manifest_present": False,
        "pending_draw_directory_present": False,
        "absence_gates_use_lstat_no_entry_semantics": True,
        "readiness_transition": "NONE",
        "claim_transition": "NONE",
    }


def _expected_registration_bindings() -> Dict[str, Any]:
    return {
        "human_registration": _file_row(HUMAN_RELATIVE_PATH),
        "hostile_test": _file_row(TEST_RELATIVE_PATH),
    }


def _assert_contract(record: Mapping[str, Any]) -> None:
    expected_keys = {
        "schema_version",
        "registration_id",
        "registration_mode",
        "scope",
        "global_state",
        "milestone_state",
        "pre_draw_package_bindings",
        "pre_draw_predecessor_reopen",
        "draw_custody",
        "entropy_boundary",
        "mapping_verification",
        "anti_selection_boundary",
        "d1_exposure_boundary",
        "replacement_registry",
        "downstream_coordinate_projection",
        "registered_state",
        "registration_activity",
        "state_preservation",
        "next_gate",
        "publication_anonymity_boundary",
        "trust_boundary",
        "nonclaims",
        "registration_bindings",
        "record_sha256",
    }
    assert type(record) is dict and set(record) == expected_keys
    _require_exact(record["schema_version"], SCHEMA)
    _require_exact(
        record["registration_id"],
        "A1-R1-REPLACEMENT-SEED-DRAW-POSTDRAW-REGISTRATION-V1",
    )
    _require_exact(
        record["registration_mode"],
        "ADDITIVE_POSTDRAW_CUSTODY_REGISTRATION_NEW_FILES_ONLY",
    )
    _require_exact(record["scope"], "SUCCESSFUL_SEED_DRAW_REGISTRATION_ZERO_EXECUTION")
    _require_exact(record["global_state"], "DRAFT_NOT_EXECUTABLE")
    _require_exact(
        record["milestone_state"], "R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE"
    )
    _require_exact(record["pre_draw_package_bindings"], _expected_pre_draw_package())
    _require_exact(
        record["pre_draw_predecessor_reopen"], _expected_predecessor_reopen()
    )
    _require_exact(record["draw_custody"], _expected_custody())
    _require_exact(record["entropy_boundary"], EXPECTED_ENTROPY_BOUNDARY)
    _require_exact(record["mapping_verification"], EXPECTED_MAPPING)
    _require_exact(
        record["anti_selection_boundary"], _expected_anti_selection_boundary()
    )
    _require_exact(record["d1_exposure_boundary"], _expected_d1_exposure_boundary())
    _require_exact(record["replacement_registry"], EXPECTED_REGISTRY)
    _require_exact(record["downstream_coordinate_projection"], EXPECTED_PROJECTION)
    _require_exact(record["registered_state"], EXPECTED_STATE)
    _require_exact(record["registration_activity"], EXPECTED_REGISTRATION_ACTIVITY)
    _require_exact(record["state_preservation"], _expected_state_preservation())
    _require_exact(record["next_gate"], EXPECTED_NEXT_GATE)
    _require_exact(record["publication_anonymity_boundary"], EXPECTED_ANONYMITY)
    _require_exact(record["trust_boundary"], EXPECTED_TRUST)
    _require_exact(record["nonclaims"], EXPECTED_NONCLAIMS)
    _require_exact(record["registration_bindings"], _expected_registration_bindings())


def test_machine_registration_is_canonical_self_digested_and_closed_world() -> None:
    payload, record = _load_json(MACHINE_RELATIVE_PATH)
    assert payload == _canonical_json(record) + b"\n"
    assert record["record_sha256"] == _semantic_digest(record, REGISTRATION_DOMAIN)
    _assert_contract(record)


def test_draw_mapping_is_independently_recomputed_without_disclosing_entropy(
    capsys,
) -> None:
    _, draw = _load_json(DRAW_PATH)
    entropy = bytes.fromhex(draw["entropy_hex"])
    assert len(entropy) == 32
    assert _sha256(entropy) == ENTROPY_SHA256
    entropy_integer = int.from_bytes(entropy, "big", signed=False)
    assert (entropy_integer < ACCEPTANCE_LIMIT) is True
    rank = entropy_integer % ALLOWED_COUNT
    assert rank == EXPECTED_RANK
    lower = 0
    upper = UNIVERSE - 1
    while lower < upper:
        midpoint = (lower + upper) // 2
        allowed_at_or_below = (
            midpoint + 1 - sum(1 for excluded in EXCLUDED if excluded <= midpoint)
        )
        if allowed_at_or_below <= rank:
            lower = midpoint + 1
        else:
            upper = midpoint
    candidate = lower
    assert candidate == REPLACEMENT
    assert candidate not in EXCLUDED
    assert capsys.readouterr().out == ""


def test_registry_chain_and_projection_are_exact() -> None:
    _, draw = _load_json(DRAW_PATH)
    _, registry = _load_json(REGISTRY_PATH)
    _, success = _load_json(SUCCESS_PATH)
    assert draw["accepted"] is True
    assert draw["accepted_rank_decimal"] == str(EXPECTED_RANK)
    assert draw["replacement_seed"] == REPLACEMENT
    assert registry["replacement_seed_registry"] == REGISTRY
    assert registry["replacement_ordinal"] == 0
    assert registry["registry_unique"] is True
    assert success["status"] == "SUCCESS"
    assert success["post_draw_state"] == ("R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE")
    assert success["production_execution_authorized"] is False
    assert success["rank_execution_authorized"] is False
    assert success["training_execution_authorized"] is False
    assert success["scientific_result_eligible"] is False


def test_registration_never_copies_raw_entropy_or_local_identity() -> None:
    _, draw = _load_json(DRAW_PATH)
    raw_entropy = draw["entropy_hex"].encode("ascii")
    entropy_integer = draw["entropy_integer_decimal"].encode("ascii")
    for relative_path in (
        HUMAN_RELATIVE_PATH,
        MACHINE_RELATIVE_PATH,
        TEST_RELATIVE_PATH,
    ):
        payload = (ROOT / relative_path).read_bytes()
        if raw_entropy in payload:
            raise AssertionError("raw entropy was copied into a registration file")
        if entropy_integer in payload:
            raise AssertionError("entropy integer was copied into a registration file")
    human = (ROOT / HUMAN_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "/Users/" not in human
    assert "file://" not in human
    assert ENTROPY_SHA256 in human


def test_closed_inventory_modes_and_all_execution_roots_remain_absent() -> None:
    _, record = _load_json(MACHINE_RELATIVE_PATH)
    assert record["draw_custody"] == _expected_custody()
    assert record["state_preservation"] == _expected_state_preservation()
    assert all(value is False for value in record["nonclaims"].values())


def test_status_deep_reopens_terminal_success_with_zero_entropy() -> None:
    assert _reopen_terminal_status_without_entropy() == (
        "ATTEMPT_SPENT_TERMINAL_SUCCESS"
    )


def test_lstat_absence_helper_rejects_broken_symlink(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    broken = tmp_path / "broken"
    assert _path_is_absent_no_entry(missing) is True
    broken.symlink_to(tmp_path / "does-not-exist")
    assert broken.exists() is False
    assert _path_is_absent_no_entry(broken) is False


@pytest.mark.parametrize(
    ("section", "field", "hostile"),
    [
        ("mapping_verification", "accepted", False),
        ("mapping_verification", "replacement_seed", 1729),
        ("replacement_registry", "replacement_ordinal", False),
        ("replacement_registry", "postdraw_grid_pruning_permitted", True),
        ("entropy_boundary", "second_entropy_contact_permitted", True),
        ("anti_selection_boundary", "d1_bytes_or_metadata_used_in_mapping", True),
        ("d1_exposure_boundary", "d1_admissible_as_production_evidence", True),
        ("registered_state", "entropy_contact_count", True),
        ("registration_activity", "draw_rerun", True),
        ("nonclaims", "rank_execution_authorized", True),
        ("nonclaims", "scientific_result_eligible", True),
        ("next_gate", "execution_authorized_by_this_registration", True),
        ("publication_anonymity_boundary", "public_release_inclusion_permitted", True),
        ("trust_boundary", "hostile_same_user_process_sandbox_claimed", True),
    ],
)
def test_semantically_rehashed_hostile_flips_are_rejected(
    section: str, field: str, hostile: Any
) -> None:
    _, record = _load_json(MACHINE_RELATIVE_PATH)
    forged = deepcopy(record)
    forged[section][field] = hostile
    forged["record_sha256"] = _semantic_digest(forged, REGISTRATION_DOMAIN)
    with pytest.raises(AssertionError):
        _assert_contract(forged)


@pytest.mark.parametrize(
    "section",
    [
        "draw_custody",
        "entropy_boundary",
        "mapping_verification",
        "anti_selection_boundary",
        "d1_exposure_boundary",
        "replacement_registry",
        "registration_activity",
        "state_preservation",
        "next_gate",
        "publication_anonymity_boundary",
        "trust_boundary",
        "nonclaims",
    ],
)
def test_unknown_nested_permissions_are_rejected(section: str) -> None:
    _, record = _load_json(MACHINE_RELATIVE_PATH)
    forged = deepcopy(record)
    forged[section]["hostile_unknown_permission"] = True
    forged["record_sha256"] = _semantic_digest(forged, REGISTRATION_DOMAIN)
    with pytest.raises(AssertionError):
        _assert_contract(forged)


def test_pre_draw_and_draw_custody_bytes_are_preserved() -> None:
    _, record = _load_json(MACHINE_RELATIVE_PATH)
    assert record["pre_draw_package_bindings"] == _expected_pre_draw_package()
    assert record["pre_draw_predecessor_reopen"] == _expected_predecessor_reopen()
    assert record["draw_custody"] == _expected_custody()
