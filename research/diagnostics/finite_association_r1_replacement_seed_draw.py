"""One-shot, outcome-independent R1-A1 replacement-seed draw.

Import, ``--status``, and ``--audit-freeze`` are read-only and never contact
the entropy source.  ``--execute-one-shot`` is the sole public execution
route.  It consumes the attempt marker before its single entropy contact.

This module does not import or launch any project experiment, rank, training,
or production-order implementation.  Its only selectable value is a safe
JSON integer derived from one 256-bit operating-system draw by exact rejection
and deterministic unranking.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import sys
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "heterodiff-r1-a1-replacement-seed-draw-v1"
FREEZE_SCHEMA_VERSION = "heterodiff-manuscript-v3-a1-r1-replacement-seed-draw-freeze-v1"
FREEZE_DOMAIN = b"heterodiff-manuscript-v3-a1-r1-replacement-seed-draw-freeze-v1\0"
ATTEMPT_DOMAIN = b"heterodiff-r1-a1-replacement-seed-draw-attempt-v1\0"
DRAW_DOMAIN = b"heterodiff-r1-a1-replacement-seed-draw-record-v1\0"
REGISTRY_DOMAIN = b"heterodiff-r1-a1-replacement-seed-registry-v1\0"
SUCCESS_DOMAIN = b"heterodiff-r1-a1-replacement-seed-draw-success-v1\0"
FAILURE_DOMAIN = b"heterodiff-r1-a1-replacement-seed-draw-failure-v1\0"

USER_DECISION_TEXT = "Please move forward with your recommended option above."
USER_DECISION_SHA256 = (
    "0a8ee5fc5192bd9e2a6c11150e01b26418896eba08eb01af23eb6a210359e301"
)
USER_RECOMMENDATION_TEXT = (
    "One material statistical choice prevents an executable R1 freeze: should we "
    "preserve eight paired seeds by generating a new outcome-independent replacement "
    "for 1729—recommended—or proceed with seven clean seeds?"
)
USER_RECOMMENDATION_SHA256 = (
    "c15926195485cf8f6245fc57aca0c6951d408a7f33844551e596db061caacbb2"
)
USER_DECISION_INTERPRETATION = "ONE_REPLACEMENT_KEEP_EIGHT"

UNIVERSE_SIZE = 1 << 53
ORIGINAL_SEEDS = (1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
EXCLUDED_SEEDS = ORIGINAL_SEEDS
ALLOWED_COUNT = UNIVERSE_SIZE - len(EXCLUDED_SEEDS)
ENTROPY_BYTES = 32
ENTROPY_SPACE = 1 << (8 * ENTROPY_BYTES)
REJECTION_REMAINDER = 64
ACCEPTANCE_LIMIT = ENTROPY_SPACE - REJECTION_REMAINDER
REPLACED_ORDINAL = 0

ATTEMPT_RELATIVE_PATH = (
    "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1.attempt.json"
)
PENDING_RELATIVE_PATH = (
    "artifacts/.manuscript_v3_a1_r1_replacement_seed_draw_v1.pending"
)
OUTPUT_RELATIVE_PATH = "artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1"
FREEZE_RELATIVE_PATH = (
    "research/fixtures/" "manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.json"
)
HUMAN_FREEZE_RELATIVE_PATH = "manuscript_v3/a1_r1_replacement_seed_draw_freeze_v1.md"
MODULE_RELATIVE_PATH = (
    "research/diagnostics/finite_association_r1_replacement_seed_draw.py"
)
TEST_RELATIVE_PATH = (
    "tests/unit/" "test_manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.py"
)
CHECKED_PRODUCTION_ROOTS = (
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
)
PROTECTED_PRODUCTION_ROOTS = (
    "artifacts/a1_campaign_v4",
    "artifacts/a1_finite_association_production_order_v1",
)
FORMAL_RUNTIME_IDENTITY_RELATIVE_PATH = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
)
CANONICAL_WORKSPACE_ROOT = Path(
    "/Users/mahtab/.codex/.chatgpt-projects/" "g-p-6a5f91c1e79c819183983ba0010bb151"
)
CANONICAL_PYTHON_RELATIVE_PATH = ".venv-m1/bin/python"
CANONICAL_EXECUTION_ARGV = (
    MODULE_RELATIVE_PATH,
    "--execute-one-shot",
)
CANONICAL_ORIG_ARGV = (
    "/Library/Frameworks/Python.framework/Versions/3.11/Resources/"
    "Python.app/Contents/MacOS/Python",
    "-I",
    "-S",
    "-B",
    MODULE_RELATIVE_PATH,
    "--execute-one-shot",
)
CANONICAL_NATIVE_PROCESS_ARGV = CANONICAL_ORIG_ARGV
NATIVE_PROCESS_ARGV_METHOD = "DARWIN_LIBC__NSGETARGC__NSGETARGV_UTF8_STRICT"
CANONICAL_INTERPRETER_REALPATH = (
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
CANONICAL_EXECUTION_COMMAND = (
    ".venv-m1/bin/python -I -S -B "
    "research/diagnostics/finite_association_r1_replacement_seed_draw.py "
    "--execute-one-shot"
)

EXPECTED_BASELINE_BINDINGS = {
    "a1_specification": (
        "research/62_a1_association_guided_residual_falsification_spec.md",
        "475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c",
        None,
    ),
    "claim_ledger": (
        "manuscript_v3/claim_ledger.md",
        "793f7fbda938f66d771af3dc480d13dc784862a439ee65452b79c776d78e8245",
        None,
    ),
    "cp76_readiness_manifest": (
        "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json",
        "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06",
        None,
    ),
    "cp76_readiness_test": (
        "tests/unit/test_manuscript_v3_submission_readiness.py",
        "410a20e9444e5005481c2bb7c8acef0135061a86ce5bf3ad546fe3fffe83dcbc",
        None,
    ),
    "execution_preregistration_human": (
        "manuscript_v3/execution_preregistration.md",
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
        None,
    ),
    "execution_preregistration_machine": (
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        None,
    ),
    "scientific_route_test": (
        "tests/unit/test_manuscript_v3_scientific_route.py",
        "a76b2b7390999d2f43c1a7406f83f8347951d43b9762f3960410de3b188b01ae",
        None,
    ),
}

EXPECTED_CLOSURE_BINDINGS = {
    "closure_v2_human": (
        "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
        "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
        None,
    ),
    "closure_v2_machine": (
        "research/fixtures/"
        "manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    ),
    "closure_v2_qualification": (
        "research/diagnostics/"
        "finite_association_r1_rank_prefix_binder_qualification.py",
        "f5a71c17a2e6144c1ca82722d2eb1324bc614ad2d14dc565edf57b0c4586d799",
        None,
    ),
    "closure_v2_test": (
        "tests/unit/"
        "test_manuscript_v3_execution_preregistration_preexecution_closure_v2.py",
        "238e008326846d68246cf8e375cbb3aeb4132d2f52b178354713f35e9b387f59",
        None,
    ),
}

EXPECTED_D1_BINDINGS = {
    "d1_diagnostic_record": (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/"
        "diagnostic-record.json",
        "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10",
        "68434890dbd3157b70e700d6a649000dbc9ee60e297b9196af46e312beba07e6",
    ),
    "e_a1_d1_registration": (
        "research/fixtures/"
        "manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json",
        "b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0",
        "d1c52907ba0bbb6b17cb2cb4e930d983623f39c161ad8a116afa43dccbbfa1b9",
    ),
}

EXPECTED_ENVIRONMENT_BINDINGS = {
    "environment_lock": (
        "requirements/m1-reference-macos-arm64-py311.lock",
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d",
        None,
    ),
}

EXPECTED_HISTORICAL_SOURCE_BINDINGS = {
    "exact_population": (
        "src/heterodiff/experiments/finite_association_exact_population_torch.py",
        "699c609807d5f68a1f36a76eeac5b36b06fa6eef52e6e74cf318acb0faf194c9",
        None,
    ),
    "exact_population_isolated_runner": (
        "src/heterodiff/experiments/"
        "finite_association_exact_population_isolated_runner.py",
        "e9ab2ee47d0ccc8ff615187405c948bb5927ffc95ff08607e42e4ed095d662ef",
        None,
    ),
    "production_order": (
        "src/heterodiff/experiments/finite_association_production_order.py",
        "be2b4134672fc2895242d8cbb68d8c540345574f1b31ed8b04a50b88793235e1",
        None,
    ),
    "residual_data": (
        "src/heterodiff/experiments/finite_association_residual_data.py",
        "30c5d002c2e88238b840b3685f614d9ad42eda48782d655fabc859d6f4f82ac3",
        None,
    ),
    "residual_training": (
        "src/heterodiff/experiments/finite_association_residual_training_torch.py",
        "44876731d31705c8c815cd586bf2b03b0490777db6a13ad8679e5199b794f115",
        None,
    ),
    "sampled_isolated_runner": (
        "src/heterodiff/experiments/finite_association_isolated_runner.py",
        "13e0d042e9bb509e11c4ffc9d2381565f2a939def7a0add38380bfedce63240f",
        None,
    ),
    "test_only_execution_order": (
        "src/heterodiff/experiments/finite_association_execution_order.py",
        "e31753485aad2d5dc57ab0c5dfa80697ac4a11ab7937c62b4c8875d3038c0185",
        None,
    ),
}

EXPECTED_REGISTRATION_PATHS = {
    "human_freeze": HUMAN_FREEZE_RELATIVE_PATH,
    "orchestration_module": MODULE_RELATIVE_PATH,
    "hostile_test": TEST_RELATIVE_PATH,
}

EXPECTED_DECISION_BINDING = {
    "normalized_recommendation_text": USER_RECOMMENDATION_TEXT,
    "normalized_recommendation_text_utf8_sha256": USER_RECOMMENDATION_SHA256,
    "normalized_assent_text": USER_DECISION_TEXT,
    "normalized_assent_text_utf8_sha256": USER_DECISION_SHA256,
    "normalization_policy": (
        "REMOVE_UI_FORMATTING_AND_TRAILING_WHITESPACE_PRESERVE_UNICODE_TEXT_UTF8"
    ),
    "interpretation": USER_DECISION_INTERPRETATION,
    "decision_selects_replacement_value": False,
    "decision_is_entropy": False,
}

EXPECTED_SELECTION_CONTRACT = {
    "universe_size_u": UNIVERSE_SIZE,
    "safe_seed_domain": "INTEGER_0_LE_SEED_LT_2_POW_53",
    "original_excluded_seeds_e": list(ORIGINAL_SEEDS),
    "excluded_count": len(EXCLUDED_SEEDS),
    "allowed_count_m": ALLOWED_COUNT,
    "entropy_bytes": ENTROPY_BYTES,
    "entropy_integer_byte_order": "BIG_ENDIAN_UNSIGNED",
    "entropy_space": str(ENTROPY_SPACE),
    "rejection_remainder": REJECTION_REMAINDER,
    "acceptance_limit_l": str(ACCEPTANCE_LIMIT),
    "accept_if": "X<L",
    "reject_if": "X>=L",
    "accepted_rank_formula": "X%M",
    "unrank_order": "ASCENDING_EXCLUDED_SEEDS",
    "replacement_ordinal": REPLACED_ORDINAL,
    "registry_length": 8,
    "draw_count": 1,
    "redraw_permitted": False,
    "rejection_burns_attempt": True,
    "mapping_is_outcome_independent": True,
}

EXPECTED_D1_EXPOSURE_BOUNDARY = {
    "exposed_seed": 1729,
    "whole_seed_exposure_scope": (
        "ALL_METHODS_LANES_AND_BUDGETS_WITH_BUDGET_WILDCARD_WHERE_NOT_APPLICABLE"
    ),
    "disposition": "PILOT_NONCONFIRMATORY_EXPOSED",
    "d1_is_prior_observed_development_knowledge": True,
    "d1_metric_bytes_used_in_selection": False,
    "d1_checkpoint_bytes_used_in_selection": False,
    "d1_hashes_used_in_selection": False,
    "d1_timestamps_used_in_selection": False,
    "d1_process_metadata_used_in_selection": False,
    "d1_runtime_metadata_used_in_selection": False,
    "d1_metric_direction_used_in_selection": False,
    "d1_used_to_define_success_rule": False,
    "d1_used_to_change_overflow_policy": False,
    "d1_admissible_as_r1_execution_input": False,
    "d1_admissible_as_production_evidence": False,
}

EXPECTED_CUSTODY_PROTOCOL = {
    "attempt_marker_path": ATTEMPT_RELATIVE_PATH,
    "pending_terminal_path": PENDING_RELATIVE_PATH,
    "terminal_output_path": OUTPUT_RELATIVE_PATH,
    "attempt_marker_state": "ATTEMPT_CONSUMED_BEFORE_ENTROPY",
    "marker_is_durable_before_entropy": True,
    "marker_file_open_flags": ["O_EXCL", "O_NOFOLLOW"],
    "artifacts_parent_must_be_nonsymlink_directory": True,
    "file_fsync_required": True,
    "directory_fsync_required": True,
    "one_attempt_only": True,
    "concurrent_launch_fails_closed": True,
    "rejection_burns_attempt": True,
    "post_marker_crash_burns_attempt": True,
    "recovery_policy": "NO_REEXECUTION_NO_RESELECTION_FORENSIC_AUDIT_ONLY",
    "atomic_publication": "KERNEL_NOCLOBBER_DIRECTORY_RENAME",
    "target_replacement_permitted": False,
    "static_inputs_revalidated_before_publication": True,
    "static_inputs_revalidated_after_publication": True,
    "terminal_deep_reopen_before_return": True,
    "candidate_stdout_permitted": False,
    "dynamic_absence_checked_production_root_count": 11,
    "dynamic_absence_formal_runtime_manifest_checked": True,
    "dynamic_absence_gates_checked_before_marker": True,
    "dynamic_absence_gates_checked_before_publication": True,
    "dynamic_absence_gates_checked_after_publication": True,
    "dynamic_absence_gates_checked_by_terminal_and_status_audit": True,
    "live_execution_interface": "CANONICAL_DIRECT_FILE_CLI_ONLY_ZERO_SUPPLIED_ROOT",
    "canonical_workspace_root": CANONICAL_WORKSPACE_ROOT.as_posix(),
    "canonical_python_relative_path": CANONICAL_PYTHON_RELATIVE_PATH,
    "canonical_execution_argv": list(CANONICAL_EXECUTION_ARGV),
    "canonical_orig_argv": list(CANONICAL_ORIG_ARGV),
    "native_process_argv_method": NATIVE_PROCESS_ARGV_METHOD,
    "canonical_native_process_argv": list(CANONICAL_NATIVE_PROCESS_ARGV),
    "canonical_interpreter_realpath": CANONICAL_INTERPRETER_REALPATH,
    "canonical_execution_command": CANONICAL_EXECUTION_COMMAND,
    "required_python_flags": {
        "isolated": 1,
        "no_site": 1,
        "dont_write_bytecode": 1,
        "safe_path": True,
    },
    "imported_execution_permitted": False,
    "alternate_workspace_execution_permitted": False,
    "supplied_root_execution_permitted": False,
    "ordinary_import_or_runpy_monkeypatched_entropy_execution_permitted": False,
    "readable_live_execution_capability_key_present": False,
    "actual_main_module_identity_required": True,
    "canonical_writers_recheck_complete_live_cli_boundary": True,
    "canonical_writers_recheck_native_process_argv": True,
    "python_argv_vectors_alone_are_authoritative": False,
    "native_process_argv_is_immutable_against_same_process_memory_mutation": False,
    "procedural_honest_host_process_boundary": True,
    "hostile_same_user_process_sandbox_claimed": False,
    "same_process_memory_tamper_resistance_claimed": False,
    "module_global_tamper_resistance_claimed": False,
    "registered_file_tamper_resistance_claimed": False,
    "ordinary_import_runpy_python_vector_only_forgery_refuses": True,
    "runpy_forged_argv_execution_permitted": False,
    "forged_python_argv_vectors_from_dash_c_permitted": False,
}

EXPECTED_FUTURE_OUTPUT_CONTRACT = {
    "success_regular_files": [
        "replacement-seed-registry.json",
        "seed-draw-record.json",
        "success-receipt.json",
    ],
    "tail_rejection_regular_files": [
        "failure-receipt.json",
        "seed-draw-record.json",
    ],
    "entropy_source_failure_regular_files": ["failure-receipt.json"],
    "draw_record_contains_entropy_hex": True,
    "separate_entropy_receipt_required": False,
    "hash_chain": "ATTEMPT_TO_DRAW_TO_REGISTRY_TO_SUCCESS",
    "success_state": "R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE",
    "failure_state": "INCOMPLETE_NO_REDRAW",
    "replacement_substitutes_ordinal_zero_only": True,
    "preserved_nonzero_ordinals": list(ORIGINAL_SEEDS[1:]),
    "confirmatory_seed_count_after_success": 8,
    "production_execution_authorized_after_success": False,
    "downstream_coordinate_projection": {
        "exact_population_coordinate_count": 24,
        "primary_coordinate_count": 48,
        "control_coordinate_count": 72,
        "complete_sampled_coordinate_count": 120,
        "all_coordinates_including_exact_count": 144,
        "replacement_applies_to_ordinal_zero_across_every_method_lane_budget": True,
        "numeric_registry_resort_permitted": False,
        "post_draw_grid_pruning_permitted": False,
        "partial_lane_substitution_permitted": False,
    },
}

EXPECTED_CURRENT_PRE_DRAW_STATE = {
    "attempt_marker_present": False,
    "pending_terminal_present": False,
    "terminal_output_present": False,
    "attempt_consumed": False,
    "entropy_contacted": False,
    "draw_performed": False,
    "replacement_seed": None,
    "replacement_registry": None,
    "execution_performed": False,
}

EXPECTED_ANTI_SELECTION_BOUNDARY = {
    "only_entropy_bytes_enter_mapping": True,
    "user_decision_bytes_used_in_mapping": False,
    "user_decision_hash_used_in_mapping": False,
    "d1_bytes_or_metadata_used_in_mapping": False,
    "source_hashes_used_in_mapping": False,
    "filesystem_metadata_used_in_mapping": False,
    "runtime_metadata_used_in_mapping": False,
    "clock_or_timestamp_used_in_mapping": False,
    "process_or_host_identity_used_in_mapping": False,
    "candidate_screening_permitted": False,
    "candidate_top_up_permitted": False,
    "candidate_redraw_permitted": False,
    "candidate_quality_evaluation_permitted": False,
    "metric_selection_performed": False,
    "threshold_selection_performed": False,
    "checkpoint_selection_performed": False,
    "seed_count_selected_from_d1": False,
    "success_rule_selected_from_d1": False,
    "overflow_policy_selected_from_d1": False,
}

EXPECTED_STATE_PRESERVATION = {
    "historical_sources_mutated": False,
    "historical_sources_imported_by_draw_module": False,
    "historical_sources_used_for_execution": False,
    "production_order_mutated": False,
    "production_order_admissible": False,
    "closure_v2_mutated": False,
    "d1_artifacts_mutated": False,
    "claim_ledger_mutated": False,
    "execution_preregistration_mutated": False,
    "cp76_snapshot_mutated": False,
    "readiness_transition": "NONE",
    "r1_result_slot_changed": False,
    "r2_result_slot_changed": False,
    "claim_row_changed": False,
    "all_checked_production_roots": list(CHECKED_PRODUCTION_ROOTS),
    "any_checked_production_root_present": False,
    "formal_runtime_identity_manifest_path": FORMAL_RUNTIME_IDENTITY_RELATIVE_PATH,
    "formal_runtime_identity_manifest_present": False,
    "historical_sources_remain_immutable_through_draw_publication": True,
    "separate_registry_integration_source_amendment_milestone_required": True,
    "registry_integration_required_before_any_r1_runner_or_production_execution": True,
    "registry_integration_or_source_amendment_authorized_here": False,
}

EXPECTED_PUBLICATION_ANONYMITY_BOUNDARY = {
    "internal_freeze_not_submission_artifact": True,
    "raw_new_artifacts_are_internal_only": True,
    "raw_new_artifact_paths": [
        HUMAN_FREEZE_RELATIVE_PATH,
        FREEZE_RELATIVE_PATH,
        MODULE_RELATIVE_PATH,
        TEST_RELATIVE_PATH,
    ],
    "future_raw_custody_paths": [
        ATTEMPT_RELATIVE_PATH,
        PENDING_RELATIVE_PATH,
        PENDING_RELATIVE_PATH + "/seed-draw-record.json",
        PENDING_RELATIVE_PATH + "/replacement-seed-registry.json",
        PENDING_RELATIVE_PATH + "/success-receipt.json",
        PENDING_RELATIVE_PATH + "/failure-receipt.json",
        OUTPUT_RELATIVE_PATH,
        OUTPUT_RELATIVE_PATH + "/seed-draw-record.json",
        OUTPUT_RELATIVE_PATH + "/replacement-seed-registry.json",
        OUTPUT_RELATIVE_PATH + "/success-receipt.json",
        OUTPUT_RELATIVE_PATH + "/failure-receipt.json",
    ],
    "future_raw_custody_contains_entropy_hex": True,
    "future_raw_custody_anonymous_submission_inclusion_permitted": False,
    "future_raw_custody_public_release_inclusion_permitted": False,
    "future_custody_directory_owner_only_mode_required": "0700_NO_GROUP_OTHER_BITS",
    "future_custody_file_owner_only_mode_required": "0600_NO_GROUP_OTHER_BITS",
    "anonymous_submission_inclusion_permitted": False,
    "public_release_inclusion_permitted": False,
    "publication_safe_derivative_required": True,
    "publication_safe_derivative_path": None,
    "in_place_sanitization_permitted": False,
    "submission_include_exclude_roster_frozen": False,
    "fresh_publication_anonymity_audit_required": True,
}

EXPECTED_NONCLAIMS = {
    "confirmatory_execution_authorized": False,
    "production_execution_authorized": False,
    "rank_execution_authorized": False,
    "training_execution_authorized": False,
    "replacement_seed_selected": False,
    "entropy_contacted": False,
    "draw_performed": False,
    "attempt_consumed": False,
    "scientific_result_eligible": False,
    "r1_qualified": False,
    "r2_qualified": False,
    "c17_proved": False,
    "claim_promoted": False,
    "submission_ready": False,
}


class FreezeError(RuntimeError):
    """Static freeze or custody mismatch."""


class AttemptSpentError(RuntimeError):
    """A marker exists, so this one-shot attempt cannot run again."""


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


def _record_digest(value: Mapping[str, Any], domain: bytes) -> str:
    body = dict(value)
    body["record_sha256"] = None
    return _sha256(domain + _canonical_json(body))


def _with_record_digest(value: Mapping[str, Any], domain: bytes) -> Dict[str, Any]:
    record = dict(value)
    record["record_sha256"] = None
    record["record_sha256"] = _record_digest(record, domain)
    return record


def _require_exact(actual: Any, expected: Any, label: str) -> None:
    """Require canonical equality so bool/int aliases and extras cannot pass."""

    if type(actual) is not type(expected):
        raise FreezeError("%s type mismatch" % label)
    try:
        matches = _canonical_json(actual) == _canonical_json(expected)
    except (TypeError, ValueError) as error:
        raise FreezeError("%s is not canonicalizable" % label) from error
    if not matches:
        raise FreezeError("%s mismatch" % label)


def _safe_relative_path(relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise FreezeError("unsafe relative path")
    return relative


def _stable_stat_identity(info: os.stat_result) -> Tuple[int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _regular_file_bytes(root: Path, relative_path: str) -> bytes:
    path = root / _safe_relative_path(relative_path)
    try:
        info = path.lstat()
    except FileNotFoundError as error:
        raise FreezeError("required file is absent: %s" % relative_path) from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise FreezeError("required path is not a regular file: %s" % relative_path)
    payload = path.read_bytes()
    if _stable_stat_identity(path.lstat()) != _stable_stat_identity(info):
        raise FreezeError("required file changed while being read: %s" % relative_path)
    return payload


def _file_row(root: Path, relative_path: str) -> Dict[str, Any]:
    payload = _regular_file_bytes(root, relative_path)
    return {
        "path": relative_path,
        "raw_sha256": _sha256(payload),
        "bytes": len(payload),
        "lf_count": payload.count(b"\n"),
        "terminal_lf": payload.endswith(b"\n"),
        "semantic_sha256": None,
    }


def _load_canonical_freeze(root: Path) -> Tuple[bytes, Dict[str, Any]]:
    payload = _regular_file_bytes(root, FREEZE_RELATIVE_PATH)
    if not payload.endswith(b"\n") or payload.count(b"\n") != 1:
        raise FreezeError("machine freeze is not one-line terminal-LF JSON")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FreezeError("machine freeze is not canonical ASCII JSON") from error
    if type(value) is not dict or payload != _canonical_json(value) + b"\n":
        raise FreezeError("machine freeze bytes are not canonical")
    if value.get("record_sha256") != _record_digest(value, FREEZE_DOMAIN):
        raise FreezeError("machine freeze self digest is invalid")
    return payload, value


def _assert_binding_group(
    root: Path,
    actual: Any,
    expected: Mapping[str, Tuple[str, str, Optional[str]]],
) -> None:
    if type(actual) is not dict or set(actual) != set(expected):
        raise FreezeError("binding group is not closed-world")
    for role, (relative_path, raw_sha256, semantic_sha256) in expected.items():
        row = actual[role]
        if type(row) is not dict or set(row) != {
            "path",
            "raw_sha256",
            "bytes",
            "lf_count",
            "terminal_lf",
            "semantic_sha256",
        }:
            raise FreezeError("binding row is not closed-world: %s" % role)
        observed = _file_row(root, relative_path)
        observed["semantic_sha256"] = semantic_sha256
        try:
            _require_exact(row, observed, "binding row %s" % role)
        except FreezeError as error:
            raise FreezeError("binding mismatch: %s" % role) from error
        if row["raw_sha256"] != raw_sha256:
            raise FreezeError("binding mismatch: %s" % role)


def _assert_freeze_contract(root: Path, freeze: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "freeze_id",
        "registration_mode",
        "scope",
        "global_state",
        "milestone_state",
        "decision_binding",
        "selection_contract",
        "d1_exposure_boundary",
        "baseline_bindings",
        "closure_v2_bindings",
        "d1_bindings",
        "environment_bindings",
        "historical_source_bindings",
        "custody_protocol",
        "future_output_contract",
        "current_pre_draw_state",
        "anti_selection_boundary",
        "state_preservation",
        "publication_anonymity_boundary",
        "nonclaims",
        "registration_bindings",
        "record_sha256",
    }
    if set(freeze) != required:
        raise FreezeError("machine freeze top-level schema is not closed-world")
    _require_exact(freeze["schema_version"], FREEZE_SCHEMA_VERSION, "schema")
    _require_exact(
        freeze["freeze_id"],
        "A1-R1-REPLACEMENT-SEED-DRAW-FREEZE-V1",
        "freeze id",
    )
    _require_exact(
        freeze["registration_mode"],
        "ADDITIVE_PRE_DRAW_FREEZE_NEW_FILES_ONLY",
        "registration mode",
    )
    _require_exact(
        freeze["scope"],
        "PRE_DRAW_FREEZE_ZERO_ENTROPY_ZERO_EXECUTION",
        "scope",
    )
    _require_exact(freeze["global_state"], "DRAFT_NOT_EXECUTABLE", "global state")
    _require_exact(
        freeze["milestone_state"],
        "R1_A1_SEED_DRAW_AUTHORIZED_NOT_YET_CONSUMED",
        "milestone state",
    )
    _require_exact(
        freeze["decision_binding"], EXPECTED_DECISION_BINDING, "decision binding"
    )
    _require_exact(
        freeze["selection_contract"],
        EXPECTED_SELECTION_CONTRACT,
        "selection contract",
    )
    _require_exact(
        freeze["d1_exposure_boundary"],
        EXPECTED_D1_EXPOSURE_BOUNDARY,
        "D1 exposure boundary",
    )
    _assert_binding_group(root, freeze["baseline_bindings"], EXPECTED_BASELINE_BINDINGS)
    _assert_binding_group(
        root, freeze["closure_v2_bindings"], EXPECTED_CLOSURE_BINDINGS
    )
    _assert_binding_group(root, freeze["d1_bindings"], EXPECTED_D1_BINDINGS)
    _assert_binding_group(
        root, freeze["environment_bindings"], EXPECTED_ENVIRONMENT_BINDINGS
    )
    _assert_binding_group(
        root,
        freeze["historical_source_bindings"],
        EXPECTED_HISTORICAL_SOURCE_BINDINGS,
    )
    registrations = freeze["registration_bindings"]
    if type(registrations) is not dict or set(registrations) != set(
        EXPECTED_REGISTRATION_PATHS
    ):
        raise FreezeError("registration bindings are not closed-world")
    for role, relative_path in EXPECTED_REGISTRATION_PATHS.items():
        try:
            _require_exact(
                registrations[role],
                _file_row(root, relative_path),
                "registration binding %s" % role,
            )
        except FreezeError as error:
            raise FreezeError("registration binding mismatch: %s" % role) from error
    _require_exact(
        freeze["custody_protocol"], EXPECTED_CUSTODY_PROTOCOL, "custody protocol"
    )
    _require_exact(
        freeze["future_output_contract"],
        EXPECTED_FUTURE_OUTPUT_CONTRACT,
        "future output contract",
    )
    _require_exact(
        freeze["current_pre_draw_state"],
        EXPECTED_CURRENT_PRE_DRAW_STATE,
        "current pre-draw state",
    )
    _require_exact(
        freeze["anti_selection_boundary"],
        EXPECTED_ANTI_SELECTION_BOUNDARY,
        "anti-selection boundary",
    )
    _require_exact(
        freeze["state_preservation"],
        EXPECTED_STATE_PRESERVATION,
        "state preservation",
    )
    _require_exact(
        freeze["publication_anonymity_boundary"],
        EXPECTED_PUBLICATION_ANONYMITY_BOUNDARY,
        "publication anonymity boundary",
    )
    _require_exact(freeze["nonclaims"], EXPECTED_NONCLAIMS, "nonclaims")


def audit_freeze(workspace_root: os.PathLike) -> Dict[str, Any]:
    """Reopen the complete pre-draw freeze without contacting entropy."""

    root = Path(workspace_root).resolve(strict=True)
    payload, freeze = _load_canonical_freeze(root)
    _assert_freeze_contract(root, freeze)
    _assert_dynamic_absence_gates(root)
    return {
        "schema": "heterodiff-r1-a1-replacement-seed-draw-freeze-audit-v1",
        "status": "PASS_ZERO_ENTROPY_ZERO_EXECUTION",
        "freeze_raw_sha256": _sha256(payload),
        "freeze_record_sha256": freeze["record_sha256"],
        "global_state": freeze["global_state"],
        "milestone_state": freeze["milestone_state"],
        "entropy_contacted": False,
        "execution_performed": False,
    }


def _unrank_allowed_seed(rank: int) -> int:
    if type(rank) is not int or rank < 0 or rank >= ALLOWED_COUNT:
        raise ValueError("rank is outside the allowed seed domain")
    seed = rank
    for excluded in EXCLUDED_SEEDS:
        if seed >= excluded:
            seed += 1
    if seed >= UNIVERSE_SIZE or seed in EXCLUDED_SEEDS:
        raise RuntimeError("unranking invariant failed")
    return seed


def _select_replacement_seed(entropy: bytes) -> Dict[str, Any]:
    """Pure exact rejection and unranking from entropy bytes alone."""

    if type(entropy) is not bytes or len(entropy) != ENTROPY_BYTES:
        raise ValueError("entropy must be exactly 32 bytes")
    entropy_integer = int.from_bytes(entropy, byteorder="big", signed=False)
    if entropy_integer >= ACCEPTANCE_LIMIT:
        return {
            "accepted": False,
            "entropy_integer": entropy_integer,
            "rank": None,
            "replacement_seed": None,
        }
    rank = entropy_integer % ALLOWED_COUNT
    return {
        "accepted": True,
        "entropy_integer": entropy_integer,
        "rank": rank,
        "replacement_seed": _unrank_allowed_seed(rank),
    }


def _independent_audit_selection(entropy: bytes) -> Dict[str, Any]:
    """Independent divmod/binary-search oracle used only for terminal audit."""

    if type(entropy) is not bytes or len(entropy) != 32:
        raise FreezeError("audited entropy is not exactly 32 bytes")
    entropy_integer = int.from_bytes(entropy, "big", signed=False)
    if entropy_integer >= 2**256 - 64:
        return {
            "accepted": False,
            "entropy_integer": entropy_integer,
            "rank": None,
            "replacement_seed": None,
        }
    _, rank = divmod(entropy_integer, 2**53 - 8)
    lower = 0
    upper = 2**53 - 1
    while lower < upper:
        midpoint = (lower + upper) // 2
        excluded_through_midpoint = sum(
            1 for excluded in ORIGINAL_SEEDS if excluded <= midpoint
        )
        allowed_through_midpoint = midpoint + 1 - excluded_through_midpoint
        if allowed_through_midpoint >= rank + 1:
            upper = midpoint
        else:
            lower = midpoint + 1
    candidate = lower
    excluded_before_candidate = sum(
        1 for excluded in ORIGINAL_SEEDS if excluded < candidate
    )
    if candidate in ORIGINAL_SEEDS or candidate - excluded_before_candidate != rank:
        raise FreezeError("independent audited unranking invariant failed")
    return {
        "accepted": True,
        "entropy_integer": entropy_integer,
        "rank": rank,
        "replacement_seed": candidate,
    }


def _independent_expected_draw(
    freeze: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    entropy: bytes,
) -> Dict[str, Any]:
    selection = _independent_audit_selection(entropy)
    return _with_record_digest(
        {
            "schema": "heterodiff-r1-a1-replacement-seed-draw-record-v1",
            "freeze_record_sha256": freeze["record_sha256"],
            "attempt_marker_raw_sha256": _sha256(marker_payload),
            "attempt_marker_record_sha256": marker["record_sha256"],
            "entropy_source": "PYTHON_SECRETS_TOKEN_BYTES_OS_CSPRNG",
            "entropy_bytes": 32,
            "entropy_hex": entropy.hex(),
            "entropy_integer_decimal": str(selection["entropy_integer"]),
            "universe_size_u": 2**53,
            "original_excluded_seeds_e": list(ORIGINAL_SEEDS),
            "allowed_count_m": 2**53 - 8,
            "acceptance_limit_l": str(2**256 - 64),
            "accepted": selection["accepted"],
            "accepted_rank_decimal": (
                None if selection["rank"] is None else str(selection["rank"])
            ),
            "unrank_algorithm": "ASCENDING_EXCLUDED_SEEDS_INCREMENT_ON_GE",
            "replacement_seed": selection["replacement_seed"],
            "d1_bytes_used_as_entropy_or_selection_input": False,
            "decision_bytes_used_as_entropy_or_selection_input": False,
            "record_sha256": None,
        },
        DRAW_DOMAIN,
    )


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW
    descriptor = os.open(str(path), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_new_file(path: Path, payload: bytes) -> None:
    _require_path_write_scope(path)
    parent_info = path.parent.lstat()
    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
        raise FreezeError("output parent is not a nonsymlink directory")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = os.open(str(path), flags, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError("zero-length write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if path.read_bytes() != payload:
        raise FreezeError("exclusive file did not reopen byte-identically")


def _write_new_record(path: Path, record: Mapping[str, Any]) -> bytes:
    payload = _canonical_json(record)
    _write_new_file(path, payload)
    return payload


def _load_canonical_record(path: Path, domain: bytes) -> Tuple[bytes, Dict[str, Any]]:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise FreezeError("custody record is not a regular nonsymlink file")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise FreezeError("custody record has group or other permission bits")
    payload = path.read_bytes()
    if _stable_stat_identity(path.lstat()) != _stable_stat_identity(info):
        raise FreezeError("custody record changed while being read")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FreezeError("custody record is not ASCII JSON") from error
    if type(value) is not dict or payload != _canonical_json(value):
        raise FreezeError("custody record is not canonical JSON")
    if value.get("record_sha256") != _record_digest(value, domain):
        raise FreezeError("custody record self digest is invalid")
    return payload, value


def _path_exists_without_follow(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _require_absent(path: Path, label: str) -> None:
    if _path_exists_without_follow(path):
        raise AttemptSpentError("%s already exists" % label)


def _require_artifacts_parent(root: Path) -> Path:
    artifacts = root / "artifacts"
    try:
        info = artifacts.lstat()
    except FileNotFoundError as error:
        raise FreezeError("workspace artifacts directory is absent") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise FreezeError("workspace artifacts path is not a nonsymlink directory")
    if artifacts.resolve(strict=True) != root / "artifacts":
        raise FreezeError("workspace artifacts directory resolves outside its root")
    return artifacts


def _assert_dynamic_absence_gates(root: Path) -> None:
    _require_artifacts_parent(root)
    for relative_path in CHECKED_PRODUCTION_ROOTS:
        if _path_exists_without_follow(root / relative_path):
            raise FreezeError(
                "dynamic production-root absence gate violated: %s" % relative_path
            )
    if _path_exists_without_follow(root / FORMAL_RUNTIME_IDENTITY_RELATIVE_PATH):
        raise FreezeError("dynamic formal-runtime-manifest absence gate violated")


def _require_canonical_workspace(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    if resolved != CANONICAL_WORKSPACE_ROOT:
        raise FreezeError("live draw refuses an alternate workspace root")
    if Path.cwd().resolve(strict=True) != CANONICAL_WORKSPACE_ROOT:
        raise FreezeError(
            "live draw requires the canonical workspace working directory"
        )
    module_path = Path(__file__).resolve(strict=True)
    if module_path != CANONICAL_WORKSPACE_ROOT / MODULE_RELATIVE_PATH:
        raise FreezeError("live draw module is not the canonical bound file")
    return resolved


def _require_live_runtime_flags(flags: Any) -> None:
    expected = {
        "isolated": 1,
        "no_site": 1,
        "dont_write_bytecode": 1,
        "safe_path": True,
    }
    observed = {
        "isolated": getattr(flags, "isolated", None),
        "no_site": getattr(flags, "no_site", None),
        "dont_write_bytecode": getattr(flags, "dont_write_bytecode", None),
        "safe_path": getattr(flags, "safe_path", None),
    }
    _require_exact(observed, expected, "live Python isolation flags")


def _native_process_argv() -> Tuple[str, ...]:
    """Read Darwin process argv independently of Python's mutable copies."""

    if sys.platform != "darwin":
        raise FreezeError("live draw requires the frozen Darwin native-argv API")
    try:
        libc = ctypes.CDLL(None)
        get_argc = libc._NSGetArgc
        get_argv = libc._NSGetArgv
        get_argc.argtypes = []
        get_argc.restype = ctypes.POINTER(ctypes.c_int)
        get_argv.argtypes = []
        get_argv.restype = ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
        argc_pointer = get_argc()
        argv_pointer_pointer = get_argv()
        if not argc_pointer or not argv_pointer_pointer:
            raise FreezeError("Darwin native process argv pointer is null")
        argc = argc_pointer.contents.value
        if type(argc) is not int or argc < 1 or argc > 64:
            raise FreezeError("Darwin native process argc is outside the frozen bound")
        argv_pointer = argv_pointer_pointer.contents
        observed = []
        for index in range(argc):
            raw = argv_pointer[index]
            if raw is None:
                raise FreezeError("Darwin native process argv contains a null entry")
            observed.append(raw.decode("utf-8", errors="strict"))
    except FreezeError:
        raise
    except (AttributeError, OSError, UnicodeDecodeError, ValueError) as error:
        raise FreezeError("Darwin native process argv could not be reopened") from error
    return tuple(observed)


def _require_live_cli_boundary() -> Path:
    if __name__ != "__main__" or __spec__ is not None:
        raise FreezeError("live draw is available only from direct-file __main__")
    root = _require_canonical_workspace(CANONICAL_WORKSPACE_ROOT)
    if sys.argv != list(CANONICAL_EXECUTION_ARGV):
        raise FreezeError("live draw argv is not the frozen canonical vector")
    if getattr(sys, "orig_argv", None) != list(CANONICAL_ORIG_ARGV):
        raise FreezeError("live draw orig_argv is not the frozen process vector")
    if _native_process_argv() != CANONICAL_NATIVE_PROCESS_ARGV:
        raise FreezeError("live draw native process argv is not the frozen vector")
    main_module = sys.modules.get("__main__")
    if (
        main_module is not sys.modules.get(__name__)
        or main_module is None
        or main_module.__dict__ is not globals()
    ):
        raise FreezeError("live draw __main__ module identity is not canonical")
    if sys.executable != (root / CANONICAL_PYTHON_RELATIVE_PATH).as_posix():
        raise FreezeError("live draw interpreter path is not canonical")
    if Path(sys.executable).resolve(strict=True).as_posix() != (
        CANONICAL_INTERPRETER_REALPATH
    ):
        raise FreezeError("live draw interpreter realpath is not canonical")
    _require_live_runtime_flags(sys.flags)
    return root


def _require_write_scope(root: Path) -> None:
    if root.resolve(strict=True) == CANONICAL_WORKSPACE_ROOT:
        _require_live_cli_boundary()


def _require_path_write_scope(path: Path) -> None:
    resolved_parent = path.parent.resolve(strict=True)
    try:
        resolved_parent.relative_to(CANONICAL_WORKSPACE_ROOT)
    except ValueError:
        return
    _require_live_cli_boundary()


def _consume_attempt(
    root: Path, freeze: Mapping[str, Any]
) -> Tuple[bytes, Dict[str, Any]]:
    _require_write_scope(root)
    _assert_dynamic_absence_gates(root)
    attempt = root / ATTEMPT_RELATIVE_PATH
    pending = root / PENDING_RELATIVE_PATH
    output = root / OUTPUT_RELATIVE_PATH
    _require_absent(attempt, "attempt marker")
    _require_absent(pending, "pending terminal directory")
    _require_absent(output, "terminal output directory")
    marker = _with_record_digest(
        {
            "schema": "heterodiff-r1-a1-replacement-seed-draw-attempt-v1",
            "attempt_state": "ATTEMPT_CONSUMED_BEFORE_ENTROPY",
            "freeze_record_sha256": freeze["record_sha256"],
            "recommendation_text_utf8_sha256": USER_RECOMMENDATION_SHA256,
            "assent_text_utf8_sha256": USER_DECISION_SHA256,
            "decision_interpretation": USER_DECISION_INTERPRETATION,
            "draw_count_authorized": 1,
            "entropy_bytes_authorized": ENTROPY_BYTES,
            "entropy_contacted_when_marker_committed": False,
            "retry_permitted": False,
            "candidate_seed": None,
            "record_sha256": None,
        },
        ATTEMPT_DOMAIN,
    )
    payload = _write_new_record(attempt, marker)
    _fsync_directory(attempt.parent)
    if attempt.read_bytes() != payload:
        raise FreezeError("attempt marker changed after directory fsync")
    return payload, marker


def _revalidate_static_inputs(
    root: Path, expected_freeze_record_sha256: str
) -> Dict[str, Any]:
    _, current = _load_canonical_freeze(root)
    _assert_freeze_contract(root, current)
    _assert_dynamic_absence_gates(root)
    if current["record_sha256"] != expected_freeze_record_sha256:
        raise FreezeError("freeze identity changed after attempt consumption")
    return current


def _draw_record(
    freeze: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    entropy: bytes,
    selection: Mapping[str, Any],
) -> Dict[str, Any]:
    recomputed = _select_replacement_seed(entropy)
    _require_exact(selection, recomputed, "entropy selection")
    return _with_record_digest(
        {
            "schema": "heterodiff-r1-a1-replacement-seed-draw-record-v1",
            "freeze_record_sha256": freeze["record_sha256"],
            "attempt_marker_raw_sha256": _sha256(marker_payload),
            "attempt_marker_record_sha256": marker["record_sha256"],
            "entropy_source": "PYTHON_SECRETS_TOKEN_BYTES_OS_CSPRNG",
            "entropy_bytes": ENTROPY_BYTES,
            "entropy_hex": entropy.hex(),
            "entropy_integer_decimal": str(selection["entropy_integer"]),
            "universe_size_u": UNIVERSE_SIZE,
            "original_excluded_seeds_e": list(ORIGINAL_SEEDS),
            "allowed_count_m": ALLOWED_COUNT,
            "acceptance_limit_l": str(ACCEPTANCE_LIMIT),
            "accepted": selection["accepted"],
            "accepted_rank_decimal": (
                None if selection["rank"] is None else str(selection["rank"])
            ),
            "unrank_algorithm": "ASCENDING_EXCLUDED_SEEDS_INCREMENT_ON_GE",
            "replacement_seed": selection["replacement_seed"],
            "d1_bytes_used_as_entropy_or_selection_input": False,
            "decision_bytes_used_as_entropy_or_selection_input": False,
            "record_sha256": None,
        },
        DRAW_DOMAIN,
    )


def _registry_record(
    freeze: Mapping[str, Any],
    draw_payload: bytes,
    draw: Mapping[str, Any],
) -> Dict[str, Any]:
    replacement = draw["replacement_seed"]
    if type(replacement) is not int:
        raise FreezeError("accepted draw lacks an integer replacement")
    registry = [replacement] + list(ORIGINAL_SEEDS[1:])
    if (
        len(registry) != 8
        or len(set(registry)) != 8
        or replacement in ORIGINAL_SEEDS
        or registry[1:] != list(ORIGINAL_SEEDS[1:])
    ):
        raise FreezeError("replacement registry invariant failed")
    return _with_record_digest(
        {
            "schema": "heterodiff-r1-a1-replacement-seed-registry-v1",
            "registry_state": "IMMUTABLE_REPLACEMENT_SEED_REGISTERED",
            "freeze_record_sha256": freeze["record_sha256"],
            "seed_draw_record_raw_sha256": _sha256(draw_payload),
            "seed_draw_record_sha256": draw["record_sha256"],
            "original_seed_registry": list(ORIGINAL_SEEDS),
            "exposed_seed": ORIGINAL_SEEDS[0],
            "exposure_scope": "ALL_METHODS_LANES_AND_BUDGETS",
            "replacement_ordinal": REPLACED_ORDINAL,
            "replacement_seed": replacement,
            "replacement_seed_registry": registry,
            "registry_length": len(registry),
            "registry_unique": len(set(registry)) == len(registry),
            "confirmatory_seed_count": 8,
            "historical_sources_mutated": False,
            "production_order_mutated": False,
            "r1_execution_authorized": False,
            "record_sha256": None,
        },
        REGISTRY_DOMAIN,
    )


def _success_receipt(
    freeze: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    draw_payload: bytes,
    draw: Mapping[str, Any],
    registry_payload: bytes,
    registry: Mapping[str, Any],
) -> Dict[str, Any]:
    return _with_record_digest(
        {
            "schema": "heterodiff-r1-a1-replacement-seed-draw-success-v1",
            "status": "SUCCESS",
            "post_draw_state": "R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE",
            "global_state": "DRAFT_NOT_EXECUTABLE",
            "freeze_record_sha256": freeze["record_sha256"],
            "attempt_marker_raw_sha256": _sha256(marker_payload),
            "attempt_marker_record_sha256": marker["record_sha256"],
            "seed_draw_record_raw_sha256": _sha256(draw_payload),
            "seed_draw_record_sha256": draw["record_sha256"],
            "replacement_seed_registry_raw_sha256": _sha256(registry_payload),
            "replacement_seed_registry_sha256": registry["record_sha256"],
            "retry_permitted": False,
            "production_execution_authorized": False,
            "rank_execution_authorized": False,
            "training_execution_authorized": False,
            "scientific_result_eligible": False,
            "record_sha256": None,
        },
        SUCCESS_DOMAIN,
    )


def _failure_receipt(
    freeze: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    failure_code: str,
    draw_payload: Optional[bytes],
    draw: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    return _with_record_digest(
        {
            "schema": "heterodiff-r1-a1-replacement-seed-draw-failure-v1",
            "status": "FAILURE",
            "failure_code": failure_code,
            "post_failure_state": "INCOMPLETE_NO_REDRAW",
            "global_state": "DRAFT_NOT_EXECUTABLE",
            "freeze_record_sha256": freeze["record_sha256"],
            "attempt_marker_raw_sha256": _sha256(marker_payload),
            "attempt_marker_record_sha256": marker["record_sha256"],
            "seed_draw_record_raw_sha256": (
                None if draw_payload is None else _sha256(draw_payload)
            ),
            "seed_draw_record_sha256": (
                None if draw is None else draw["record_sha256"]
            ),
            "replacement_seed": None,
            "replacement_seed_registry_created": False,
            "retry_permitted": False,
            "redraw_permitted": False,
            "production_execution_authorized": False,
            "scientific_result_eligible": False,
            "record_sha256": None,
        },
        FAILURE_DOMAIN,
    )


def _make_pending_directory(root: Path) -> Path:
    _require_write_scope(root)
    _require_artifacts_parent(root)
    pending = root / PENDING_RELATIVE_PATH
    _require_absent(pending, "pending terminal directory")
    pending.mkdir(mode=0o700)
    if not stat.S_ISDIR(pending.lstat().st_mode):
        raise FreezeError("pending path is not a directory")
    if stat.S_IMODE(pending.lstat().st_mode) & 0o077:
        raise FreezeError("pending directory has group or other permission bits")
    return pending


def _rename_directory_noclobber(source: Path, target: Path) -> None:
    """Atomically publish a directory without replacing any target entry."""

    _require_path_write_scope(source)
    _require_path_write_scope(target)
    library = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    target_bytes = os.fsencode(target)
    if hasattr(library, "renameatx_np"):
        function = library.renameatx_np
        function.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        result = function(-2, source_bytes, -2, target_bytes, 0x00000004)
    elif hasattr(library, "renameat2"):
        function = library.renameat2
        function.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        result = function(-100, source_bytes, -100, target_bytes, 0x00000001)
    else:
        raise FreezeError("kernel lacks atomic no-clobber directory rename")
    if result != 0:
        error_number = ctypes.get_errno()
        if error_number in (errno.EEXIST, errno.ENOTEMPTY):
            raise AttemptSpentError("terminal output appeared before publication")
        raise OSError(error_number, os.strerror(error_number))


def _publish_pending(root: Path, pending: Path, freeze: Mapping[str, Any]) -> None:
    _require_write_scope(root)
    output = root / OUTPUT_RELATIVE_PATH
    _require_absent(output, "terminal output directory")
    _fsync_directory(pending)
    _revalidate_static_inputs(root, freeze["record_sha256"])
    _rename_directory_noclobber(pending, output)
    _fsync_directory(output.parent)
    if _path_exists_without_follow(pending):
        raise FreezeError("pending directory remained after publication")
    output_info = output.lstat()
    if stat.S_ISLNK(output_info.st_mode) or not stat.S_ISDIR(output_info.st_mode):
        raise FreezeError("published terminal is not a nonsymlink directory")
    _revalidate_static_inputs(root, freeze["record_sha256"])


def _publish_failure_without_draw(
    root: Path,
    freeze: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    failure_code: str,
) -> str:
    _require_write_scope(root)
    pending = _make_pending_directory(root)
    failure = _failure_receipt(freeze, marker_payload, marker, failure_code, None, None)
    _write_new_record(pending / "failure-receipt.json", failure)
    _publish_pending(root, pending, freeze)
    terminal = _audit_terminal(root, freeze, marker_payload, marker)
    if terminal != "FAILURE":
        raise FreezeError("published failure did not reopen as failure")
    return "FAILURE"


def _publish_selection(
    root: Path,
    freeze: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    entropy: bytes,
) -> str:
    _require_write_scope(root)
    selection = _select_replacement_seed(entropy)
    pending = _make_pending_directory(root)
    draw = _draw_record(freeze, marker_payload, marker, entropy, selection)
    draw_payload = _write_new_record(pending / "seed-draw-record.json", draw)
    if selection["accepted"] is not True:
        failure = _failure_receipt(
            freeze,
            marker_payload,
            marker,
            "ENTROPY_TAIL_REJECTION_ATTEMPT_SPENT",
            draw_payload,
            draw,
        )
        _write_new_record(pending / "failure-receipt.json", failure)
        _publish_pending(root, pending, freeze)
        terminal = _audit_terminal(root, freeze, marker_payload, marker)
        if terminal != "FAILURE":
            raise FreezeError("published rejection did not reopen as failure")
        return "FAILURE"
    registry = _registry_record(freeze, draw_payload, draw)
    registry_payload = _write_new_record(
        pending / "replacement-seed-registry.json", registry
    )
    success = _success_receipt(
        freeze,
        marker_payload,
        marker,
        draw_payload,
        draw,
        registry_payload,
        registry,
    )
    _write_new_record(pending / "success-receipt.json", success)
    _publish_pending(root, pending, freeze)
    terminal = _audit_terminal(root, freeze, marker_payload, marker)
    if terminal != "SUCCESS":
        raise FreezeError("published success did not deeply reopen")
    return "SUCCESS"


def _execute_one_shot_from_canonical_cli() -> str:
    """Consume the sole live draw after the direct-file CLI boundary passes."""

    root = _require_live_cli_boundary()
    _, freeze = _load_canonical_freeze(root)
    _assert_freeze_contract(root, freeze)
    marker_payload, marker = _consume_attempt(root, freeze)
    try:
        entropy = secrets.token_bytes(32)
    except Exception:
        return _publish_failure_without_draw(
            root,
            freeze,
            marker_payload,
            marker,
            "ENTROPY_SOURCE_ERROR_ATTEMPT_SPENT",
        )
    if type(entropy) is not bytes or len(entropy) != ENTROPY_BYTES:
        return _publish_failure_without_draw(
            root,
            freeze,
            marker_payload,
            marker,
            "ENTROPY_LENGTH_INVALID_ATTEMPT_SPENT",
        )
    return _publish_selection(root, freeze, marker_payload, marker, entropy)


def _assert_attempt_marker(
    freeze: Mapping[str, Any], marker_payload: bytes, marker: Mapping[str, Any]
) -> None:
    expected = _with_record_digest(
        {
            "schema": "heterodiff-r1-a1-replacement-seed-draw-attempt-v1",
            "attempt_state": "ATTEMPT_CONSUMED_BEFORE_ENTROPY",
            "freeze_record_sha256": freeze["record_sha256"],
            "recommendation_text_utf8_sha256": USER_RECOMMENDATION_SHA256,
            "assent_text_utf8_sha256": USER_DECISION_SHA256,
            "decision_interpretation": USER_DECISION_INTERPRETATION,
            "draw_count_authorized": 1,
            "entropy_bytes_authorized": ENTROPY_BYTES,
            "entropy_contacted_when_marker_committed": False,
            "retry_permitted": False,
            "candidate_seed": None,
            "record_sha256": None,
        },
        ATTEMPT_DOMAIN,
    )
    _require_exact(marker, expected, "attempt marker contract")
    if marker_payload != _canonical_json(expected):
        raise FreezeError("attempt marker raw bytes mismatch")


def _terminal_inventory(output: Path) -> Dict[str, Path]:
    info = output.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise FreezeError("terminal output is not a nonsymlink directory")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise FreezeError("terminal output has group or other permission bits")
    inventory: Dict[str, Path] = {}
    for path in output.iterdir():
        item = path.lstat()
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise FreezeError("terminal output contains a nonregular entry")
        if stat.S_IMODE(item.st_mode) & 0o077:
            raise FreezeError("terminal record has group or other permission bits")
        inventory[path.name] = path
    return inventory


def _audit_terminal(
    root: Path,
    freeze: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
) -> str:
    _assert_dynamic_absence_gates(root)
    output = root / OUTPUT_RELATIVE_PATH
    inventory = _terminal_inventory(output)
    success_names = {
        "seed-draw-record.json",
        "replacement-seed-registry.json",
        "success-receipt.json",
    }
    rejection_names = {"seed-draw-record.json", "failure-receipt.json"}
    source_failure_names = {"failure-receipt.json"}
    names = set(inventory)
    if names not in (success_names, rejection_names, source_failure_names):
        raise FreezeError("terminal output inventory is not closed-world")
    draw_payload: Optional[bytes] = None
    draw: Optional[Dict[str, Any]] = None
    if "seed-draw-record.json" in inventory:
        draw_payload, draw = _load_canonical_record(
            inventory["seed-draw-record.json"], DRAW_DOMAIN
        )
        try:
            entropy = bytes.fromhex(draw["entropy_hex"])
        except (KeyError, TypeError, ValueError) as error:
            raise FreezeError("draw entropy encoding is invalid") from error
        expected_draw = _independent_expected_draw(
            freeze, marker_payload, marker, entropy
        )
        _require_exact(draw, expected_draw, "independently recomputed draw")
        if draw_payload != _canonical_json(expected_draw):
            raise FreezeError("draw record raw bytes do not recompute")
    if names == success_names:
        if draw_payload is None or draw is None or draw["accepted"] is not True:
            raise FreezeError("success terminal lacks an accepted draw")
        registry_payload, registry = _load_canonical_record(
            inventory["replacement-seed-registry.json"], REGISTRY_DOMAIN
        )
        expected_registry = _registry_record(freeze, draw_payload, draw)
        _require_exact(registry, expected_registry, "replacement registry")
        if registry_payload != _canonical_json(expected_registry):
            raise FreezeError("replacement registry raw bytes do not recompute")
        receipt_payload, receipt = _load_canonical_record(
            inventory["success-receipt.json"], SUCCESS_DOMAIN
        )
        expected_receipt = _success_receipt(
            freeze,
            marker_payload,
            marker,
            draw_payload,
            draw,
            registry_payload,
            registry,
        )
        _require_exact(receipt, expected_receipt, "success receipt hash chain")
        if receipt_payload != _canonical_json(expected_receipt):
            raise FreezeError("success receipt raw bytes are invalid")
        _assert_dynamic_absence_gates(root)
        return "SUCCESS"
    failure_payload, failure = _load_canonical_record(
        inventory["failure-receipt.json"], FAILURE_DOMAIN
    )
    allowed_codes = {
        "ENTROPY_TAIL_REJECTION_ATTEMPT_SPENT",
        "ENTROPY_SOURCE_ERROR_ATTEMPT_SPENT",
        "ENTROPY_LENGTH_INVALID_ATTEMPT_SPENT",
    }
    code = failure.get("failure_code")
    if code not in allowed_codes:
        raise FreezeError("failure code is not frozen")
    if names == rejection_names:
        if (
            code != "ENTROPY_TAIL_REJECTION_ATTEMPT_SPENT"
            or draw_payload is None
            or draw is None
            or draw["accepted"] is not False
        ):
            raise FreezeError("rejection terminal is inconsistent")
    elif code == "ENTROPY_TAIL_REJECTION_ATTEMPT_SPENT":
        raise FreezeError("tail rejection lacks its draw record")
    expected_failure = _failure_receipt(
        freeze, marker_payload, marker, code, draw_payload, draw
    )
    _require_exact(failure, expected_failure, "failure receipt hash chain")
    if failure_payload != _canonical_json(expected_failure):
        raise FreezeError("failure receipt raw bytes are invalid")
    _assert_dynamic_absence_gates(root)
    return "FAILURE"


def status(workspace_root: os.PathLike) -> Dict[str, Any]:
    """Deeply reopen custody state without touching entropy."""

    root = Path(workspace_root).resolve(strict=True)
    attempt = root / ATTEMPT_RELATIVE_PATH
    pending = root / PENDING_RELATIVE_PATH
    output = root / OUTPUT_RELATIVE_PATH
    attempt_present = _path_exists_without_follow(attempt)
    pending_present = _path_exists_without_follow(pending)
    output_present = _path_exists_without_follow(output)
    _, freeze = _load_canonical_freeze(root)
    _assert_freeze_contract(root, freeze)
    _assert_dynamic_absence_gates(root)
    terminal_kind: Optional[str] = None
    if not attempt_present and not pending_present and not output_present:
        state = "R1_A1_SEED_DRAW_AUTHORIZED_NOT_YET_CONSUMED"
    elif attempt_present:
        marker_payload, marker = _load_canonical_record(attempt, ATTEMPT_DOMAIN)
        _assert_attempt_marker(freeze, marker_payload, marker)
        if output_present and not pending_present:
            terminal_kind = _audit_terminal(root, freeze, marker_payload, marker)
            state = "ATTEMPT_SPENT_TERMINAL_%s" % terminal_kind
        elif not output_present:
            state = "ATTEMPT_SPENT_TERMINAL_ABSENT_OR_PENDING_NO_RETRY"
        else:
            state = "INVALID_CUSTODY_STATE_FAIL_CLOSED"
    else:
        state = "INVALID_CUSTODY_STATE_FAIL_CLOSED"
    return {
        "schema": "heterodiff-r1-a1-replacement-seed-draw-status-v1",
        "state": state,
        "attempt_marker_present": attempt_present,
        "pending_terminal_present": pending_present,
        "terminal_output_present": output_present,
        "validated_terminal_kind": terminal_kind,
        "entropy_contacted_by_status": False,
        "candidate_seed_reported": False,
        "first_attempt_available": (
            not attempt_present and not pending_present and not output_present
        ),
        "retry_permitted": False,
    }


def _workspace_root_from_module() -> Path:
    return Path(__file__).resolve(strict=True).parents[2]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--status", action="store_true")
    modes.add_argument("--audit-freeze", action="store_true")
    modes.add_argument("--execute-one-shot", action="store_true")
    arguments = parser.parse_args(argv)
    root = _workspace_root_from_module()
    if arguments.status:
        print(status(root)["state"])
        return 0
    if arguments.audit_freeze:
        print(audit_freeze(root)["status"])
        return 0
    terminal = _execute_one_shot_from_canonical_cli()
    print("DRAW_TERMINAL_PUBLISHED_%s" % terminal)
    return 0 if terminal == "SUCCESS" else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ACCEPTANCE_LIMIT",
    "ALLOWED_COUNT",
    "ENTROPY_BYTES",
    "EXCLUDED_SEEDS",
    "ORIGINAL_SEEDS",
    "REJECTION_REMAINDER",
    "UNIVERSE_SIZE",
    "audit_freeze",
    "status",
]
