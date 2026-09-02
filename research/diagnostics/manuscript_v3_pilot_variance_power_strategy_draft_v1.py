"""Read-only validator for the pilot-variance and power-strategy draft.

Only the small :func:`summarize_seed_values` helper performs arithmetic, and it
is pure.  This module has no network, process-launch, entropy, data-source, training,
or scientific-execution route.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-pilot-variance-power-strategy-draft-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = (
    "PILOT_VARIANCE_AND_POWER_STRATEGY_DRAFT_FROZEN_AWAITING_"
    "METRIC_PILOT_AND_COMPUTE"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
CONTROL_PREDICATE = "PILOT_VARIANCE_AND_POWER_STRATEGY_DRAFT_VALIDATED"
REPORTED_DATE = "2026-08-30"
MAX_COMPONENT_BITS = 4096

HUMAN_PATH = "PROJECT_PILOT_VARIANCE_POWER_STRATEGY_DRAFT.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_pilot_variance_power_strategy_draft_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_pilot_variance_power_strategy_draft_v1.py"
)
TEST_PATH = "tests/unit/test_manuscript_v3_pilot_variance_power_strategy_draft_v1.py"

AUTHORITY_TEXT = (
    "Sounds great. Go ahead and finish them in parallel. Mark all the completed "
    "tasks as the end."
)

EXPECTED_PREDECESSORS = [
    (
        "execution_preregistration_human",
        "manuscript_v3/execution_preregistration.md",
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
    ),
    (
        "execution_preregistration_machine",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
    ),
    (
        "preexecution_closure_human",
        "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
        "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
    ),
    (
        "preexecution_closure_machine",
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
    ),
    (
        "test_seal_human",
        "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md",
        "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2",
    ),
    (
        "test_seal_machine",
        "research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json",
        "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8",
    ),
    (
        "test_seal_validator",
        "research/diagnostics/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py",
        "3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258",
    ),
    (
        "test_seal_test",
        "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py",
        "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403",
    ),
    (
        "power_route_human",
        "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md",
        "a8edf99303e30b6ae6ea9912dce6350fadc9e07361fcd25743c03446a2bb0139",
    ),
    (
        "power_route_machine",
        "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json",
        "536493388d23aac2cc3aaf6f9bdc34a12fba77103e9546cbf110c1c8223dfd28",
    ),
    (
        "power_route_validator",
        "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py",
        "be5bcf6cde26d1c4eff044f6fad4705c1e87c850c77f38b2a4f7ef670a03b129",
    ),
    (
        "power_route_test",
        "tests/unit/test_manuscript_v3_real_domain_power_allocation_route_v1.py",
        "3c0846ecd924f4e39f7a98414755fdc06c2c1e5d60491879fa4190f5730b9926",
    ),
]


class ValidationError(ValueError):
    """Raised when exact semantics or custody do not match."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _payload_bytes(payload))


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


def _safe_path(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative or relative.startswith("/"):
        raise ValidationError("relative path invalid")
    if ".." in Path(relative).parts:
        raise ValidationError("parent traversal forbidden")
    target = root.joinpath(relative)
    if target.resolve(strict=False) != root.resolve().joinpath(relative):
        raise ValidationError("path resolution mismatch")
    return target


def _fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
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


def _stable_read(root: Path, relative: str) -> bytes:
    target = _safe_path(root, relative)
    cursor = root.resolve()
    for part in Path(relative).parts[:-1]:
        cursor = cursor.joinpath(part)
        status = os.lstat(cursor)
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValidationError("unsafe ancestor")
    before_path = os.lstat(target)
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("leaf custody invalid")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = os.lstat(target)
    if not (
        _fingerprint(before_path)
        == _fingerprint(before_fd)
        == _fingerprint(after_fd)
        == _fingerprint(after_path)
    ):
        raise ValidationError("leaf changed during read")
    raw = b"".join(chunks)
    if len(raw) != before_fd.st_size:
        raise ValidationError("read size mismatch")
    return raw


def _exact_fraction(value: Any, label: str) -> Fraction:
    if type(value) is int:
        result = Fraction(value, 1)
    elif type(value) is Fraction:
        result = value
    else:
        raise ValidationError(label + " must be exact int or Fraction")
    if (
        result.numerator.bit_length() > MAX_COMPONENT_BITS
        or result.denominator.bit_length() > MAX_COMPONENT_BITS
    ):
        raise ValidationError(label + " exceeds exact component bound")
    return result


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def summarize_seed_values(rows: Any) -> Dict[str, Any]:
    """Return exact per-domain pilot mean and Bessel sample variance."""

    if type(rows) is not list:
        raise ValidationError("rows must be a list")
    grouped: Dict[str, Dict[int, Fraction]] = {"R3-PHYS": {}, "R4-RETAIL": {}}
    for ordinal, row in enumerate(rows):
        if type(row) is not dict or set(row) != {
            "domain_id",
            "seed_id",
            "paired_seed_mean",
        }:
            raise ValidationError("row schema invalid")
        domain = row["domain_id"]
        seed = row["seed_id"]
        if type(domain) is not str or domain not in grouped:
            raise ValidationError("domain invalid")
        if type(seed) is not int or seed < 0 or seed > (1 << 63) - 1:
            raise ValidationError("seed identifier invalid")
        if seed in grouped[domain]:
            raise ValidationError("duplicate domain-seed row")
        grouped[domain][seed] = _exact_fraction(
            row["paired_seed_mean"], "rows[" + str(ordinal) + "].paired_seed_mean"
        )
    summaries: List[Dict[str, Any]] = []
    for domain in ("R3-PHYS", "R4-RETAIL"):
        values = grouped[domain]
        if len(values) < 2:
            raise ValidationError("each domain requires at least two seeds")
        ordered = sorted(values.items())
        count = len(ordered)
        mean = sum((value for _, value in ordered), Fraction(0, 1)) / count
        variance = sum(
            ((value - mean) ** 2 for _, value in ordered), Fraction(0, 1)
        ) / (count - 1)
        summaries.append(
            {
                "domain_id": domain,
                "seed_ids": [seed for seed, _ in ordered],
                "seed_count": count,
                "pilot_mean": _fraction_record(mean),
                "bessel_sample_variance": _fraction_record(variance),
            }
        )
    return {
        "schema_version": "heterodiff-pilot-seed-summary-synthetic-v1",
        "summaries": summaries,
        "conditional_on_fixed_development_groups": True,
        "superpopulation_group_variance_claimed": False,
        "scientific_result": False,
    }


def _binding(
    root: Path, role: str, path: str, expected_sha: Optional[str] = None
) -> Dict[str, Any]:
    raw = _stable_read(root, path)
    digest = _sha256(raw)
    if expected_sha is not None and digest != expected_sha:
        raise ValidationError(role + " predecessor digest mismatch")
    return {"role": role, "path": path, "raw_sha256": digest, "bytes": len(raw)}


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    predecessors = [
        _binding(workspace, role, path, digest)
        for role, path, digest in EXPECTED_PREDECESSORS
    ]
    package = [
        _binding(workspace, "human", HUMAN_PATH),
        _binding(workspace, "validator", VALIDATOR_PATH),
        _binding(workspace, "test", TEST_PATH),
    ]
    dependency_keys = ["B07", "F060", "F061", "F110"] + [
        "F" + str(index) for index in range(128, 139)
    ]
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": "SOLO_BLOCK3_DRAFT_NO_SCIENTIFIC_EFFECT",
        "reported_date": REPORTED_DATE,
        "authority_provenance": {
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_sha256": _sha256(AUTHORITY_TEXT.encode("utf-8")),
            "raw_transport_or_trailing_html_space_bound": False,
            "local_block2_block3_drafting_authorized": True,
            "tracker_marking_after_independent_validation_authorized": True,
            "external_contact_data_entropy_runtime_training_or_science_authorized": False,
            "agent_selected_paths_schema_formulas_and_refusal_rules": True,
        },
        "project_control_effects": {
            "project_control_predicate": CONTROL_PREDICATE,
            "value_after_validation": True,
            "solo_block3_draft_checkbox_may_close_after_independent_review": True,
            "unresolved_fields_closed": 0,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
            "scientific_scorecard_effect": 0,
            "tracker_edit_performed_by_package": False,
        },
        "dependency_audit": {
            key: {"status": "OPEN", "value": None} for key in dependency_keys
        },
        "pilot_contract": {
            "train_validation_only": True,
            "test_material_or_outcomes_permitted": False,
            "pilot_excluded_from_confirmatory_estimation": True,
            "pilot_seed_registry_disjoint_from_confirmatory_and_simulation_registries": True,
            "pilot_seed_iid_or_exchangeability_law_matched_to_confirmatory_required": True,
            "inference_stream_independence_across_seeds_and_confirmatory_match_required": True,
            "disjoint_registry_or_addresses_alone_prove_independence_or_transportability": False,
            "metric_bound_delta0_delta1_snapshot_split_rosters_weights_and_addresses_required_before_pilot": True,
            "paired_seed_statistic_bound_not_unpaired_metric_width_required": True,
            "delta0_project_field": "F110",
            "delta1_project_field": "F130",
            "delta1_strictly_greater_than_delta0_required": True,
            "minimum_complete_seed_count_per_domain": 2,
            "noncomplete_cell_disposition_until_metric_failure_rule_exists": "PILOT_VARIANCE_UNAVAILABLE_TERMINAL_NO_GO",
            "drop_impute_replace_retry_topup_or_select_permitted": False,
        },
        "aggregation_contract": {
            "difference": "SCORE_DIRECT_MINUS_SCORE_GUIDE",
            "pairing_address": ["seed", "natural_group", "case", "draw"],
            "order": ["DRAWS_WITHIN_CASE", "CASES_WITHIN_GROUP", "GROUPS_WITHIN_SEED"],
            "training_seed_is_independent_model_replication_unit": True,
            "draw_case_group_or_seed_group_cell_is_independent_seed_replication_unit": False,
            "pilot_seed_variance": "SUM((SEED_MEAN-PILOT_MEAN)^2)/(S-1)",
            "conditional_on_fixed_development_groups": True,
            "superpopulation_group_variance_claimed": False,
            "crossed_residual_components_are_algebraic_not_independence_claims": True,
            "case_and_group_weights_exact_positive_rational_and_sum_to_one_required": True,
            "paired_statistic_bound": "L_PAIR_LE_Y_AND_CONVEX_AGGREGATES_LE_U_PAIR",
            "power_width": "W_PAIR_EQUALS_U_PAIR_MINUS_L_PAIR",
            "complete_Y_case_means_and_group_cells_retained_for_case_draw_grid": True,
            "group_cells_alone_identify_case_or_draw_variation": False,
            "unsupported_case_or_draw_extrapolation_permitted": False,
        },
        "future_power_route": {
            "candidate_familywise_alpha": {"numerator": 1, "denominator": 20},
            "candidate_joint_power": {"numerator": 9, "denominator": 10},
            "candidate_values_are_preregistration_values": False,
            "finite_grid_required": True,
            "exact_holm_decision_rule_required": True,
            "within_condition_independent_bernoulli_trials_required": True,
            "disjoint_immutable_simulation_trial_registry_required": True,
            "simultaneous_clopper_pearson_bounds_required": True,
            "composite_null_proof_or_frozen_nuisance_grid_required": True,
            "minimum_compute_then_frozen_lexicographic_tie_rule": True,
            "capacity_proof_required": True,
            "case_draw_grid_requires_frozen_hierarchical_resampling_or_generation_law": True,
            "grid_beyond_retained_nonparametric_support_requires_prevalidated_parametric_law": True,
            "unidentified_case_or_draw_allocation_disposition": "TERMINAL_NO_GO",
            "grid_expansion_topup_retry_replacement_selection_or_sequential_stopping_permitted": False,
        },
        "synthetic_qualification": {
            "pure_exact_seed_summary_present": True,
            "exact_numeric_types": ["INT", "FRACTION"],
            "binary_float_or_bool_accepted": False,
            "normalized_component_maximum_bit_length": MAX_COMPONENT_BITS,
            "real_pilot_run": False,
            "real_data_opened": False,
            "real_power_design_selected": False,
            "seed_stream_transport_law_qualified": False,
            "case_draw_variance_identification_qualified": False,
            "weight_normalization_qualified": False,
        },
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_and_fresh_anonymity_audit_required": True,
            "absolute_user_path_credentials_person_or_dataset_rows_present": False,
        },
        "predecessor_bindings": predecessors,
        "package_bindings": package,
        "record_sha256": "",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    raw = _stable_read(workspace, MACHINE_PATH)
    record = json.loads(raw.decode("ascii"))
    if type(record) is not dict:
        raise ValidationError("machine record must be object")
    if canonical_machine_bytes(record) != raw:
        raise ValidationError("machine record is not canonical")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine self digest invalid")
    _strict_equal(record, expected_record(workspace), "record")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value": True,
        "scientific_effect": 0,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "pilot_run": False,
        "validation": "PASS",
    }


__all__ = [
    "ValidationError",
    "canonical_machine_bytes",
    "expected_record",
    "record_sha256",
    "summarize_seed_values",
    "validate",
]
