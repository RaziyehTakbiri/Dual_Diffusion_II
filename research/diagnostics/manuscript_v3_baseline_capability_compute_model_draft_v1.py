"""Exact calculator and read-only validator for the baseline/compute draft.

This administrative module imports no project science, contacts no external
source, observes no data, draws no entropy, launches no subprocess, and writes
nothing.  Its calculator uses only integers and :class:`fractions.Fraction`.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-baseline-capability-compute-model-draft-v1"
STATE = (
    "BASELINE_CAPABILITY_COMPUTE_MODEL_DRAFT_FROZEN_AWAITING_REPOSITORY_COMMIT_"
    "LICENSE_CONFIG_CAPACITY_AND_INDEPENDENT_REVIEW"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "STATIC_BASELINE_CAPABILITY_AND_COMPUTE_MODEL_DRAFT_NO_SCIENTIFIC_EFFECT"
CONTROL_PREDICATE = (
    "BASELINE_FAMILIES_LICENSE_CAPABILITY_AND_COMPUTE_MODEL_DRAFT_VALIDATED"
)
REPORTED_DATE = "2026-08-30"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")

HUMAN_PATH = "PROJECT_BASELINE_CAPABILITY_COMPUTE_MODEL_DRAFT.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_baseline_capability_compute_model_draft_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_baseline_capability_compute_model_draft_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_baseline_capability_compute_model_draft_v1.py"
)

PREREG_HUMAN_PATH = "manuscript_v3/execution_preregistration.md"
PREREG_MACHINE_PATH = "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
CLOSURE_HUMAN_PATH = "manuscript_v3/execution_preregistration_preexecution_closure_v2.md"
CLOSURE_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
STATIC_HUMAN_PATH = "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md"
STATIC_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)
POWER_HUMAN_PATH = "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md"
POWER_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json"
)

NORMALIZED_AUTHORITY_TEXT = (
    "Sounds great. Go ahead and finish them in parallel. "
    "Mark all the completed tasks as the end."
)
AUTHORITY_TEXT_SHA256 = (
    "465aa47a0714b7914e33b6b6772afbfad3a56959cb6eb9f10b8e98f39c0f8d38"
)

PRIMARY_METHOD_IDS = (
    "association-aware-guide-plus-residual",
    "unified-direct-conditioner",
)
CONTROL_IDS = (
    "analytic-guide-only-residual-removed",
    "direct-or-residual-only-analytic-guide-removed",
    "association-destroyed-or-factorized-eventwise",
    "unconditional-base-sanity-reference",
)
COMPARATOR_FAMILY_IDS = (
    "ngdb-style-auxiliary-guide-plus-correction",
    "deft-style-generalized-h-frozen-base-correction",
    "task-compatible-same-base-smc-or-feynman-kac",
    "closest-variable-cardinality-point-or-edit-generator",
)
DOMAIN_IDS = ("physionet-challenge-2012", "online-retail-ii")

CAPABILITY_AXES = (
    "VARIABLE_CARDINALITY_UNORDERED_CONFIGURATION",
    "DOMAIN_PHYSICAL_TIME",
    "SIMULTANEOUS_EVENTS_AND_MULTIPLICITY",
    "TYPED_EVENTS_AND_CONTINUOUS_MARKS",
    "MISSING_OR_PARTIALLY_OBSERVED_MARKS",
    "UNORDERED_SUBSET_AND_ASSOCIATION_AMBIGUITY",
    "HORIZON_CAP_SEGMENTATION_OVERFLOW_AND_STRUCTURAL_ZEROS",
    "CONDITIONAL_SAMPLING_INTERFACE",
    "SHARED_BASE_COMPATIBILITY",
    "TRAINING_TUNING_AND_INFERENCE_INTERFACES",
    "NATIVE_VERSUS_AUTHOR_EXTENSION_BOUNDARY",
)
CAPABILITY_STATES = (
    "NATIVE",
    "AUTHOR_EXTENSION",
    "INAPPLICABLE_WITH_PROOF",
    "UNSUPPORTED",
    "UNKNOWN",
)
ADMISSIBLE_FINAL_CAPABILITY_STATES = (
    "NATIVE",
    "AUTHOR_EXTENSION",
    "INAPPLICABLE_WITH_PROOF",
)

PHASES = ("PILOT", "TUNING", "FINAL_TRAINING", "CONFIRMATORY_INFERENCE")
RESOURCE_EVENTS = (
    "BASE_FORWARD",
    "BASE_BACKWARD",
    "CONDITIONER_FORWARD",
    "CONDITIONER_BACKWARD",
    "GUIDE_EVALUATION",
    "RESAMPLING_STEP",
    "ODE_OR_SDE_STEP",
    "DATA_ADAPTER_RECORD",
    "METRIC_DRAW_EVALUATION",
    "OTHER_DECLARED_OPERATION",
)
MAX_RATIONAL_COMPONENT_BITS = 4096
MAX_ACCUMULATED_COMPONENT_BITS = 8192


class ValidationError(ValueError):
    """Raised when exact arithmetic, custody, or semantics fail."""


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


def _object_without_duplicate_keys(
    pairs: Sequence[Tuple[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _strict_json(raw: bytes, label: str) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError(label + " must be ASCII JSON") from exc
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicate_keys)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValidationError(label + " is invalid strict JSON") from exc
    if type(value) is not dict:
        raise ValidationError(label + " top level must be an object")
    return value


def _fraction(value: Any, label: str, *, positive: bool) -> Fraction:
    if type(value) is int:
        result = Fraction(value, 1)
    elif type(value) is Fraction:
        result = value
    else:
        raise ValidationError(label + " must be an exact int or Fraction")
    if positive and result <= 0:
        raise ValidationError(label + " must be strictly positive")
    if not positive and result < 0:
        raise ValidationError(label + " must be nonnegative")
    if (
        result.numerator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
        or result.denominator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
    ):
        raise ValidationError(label + " exceeds the normalized component bit bound")
    return result


def _count(value: Any, label: str) -> int:
    if type(value) is not int:
        raise ValidationError(label + " must be an exact nonnegative integer")
    if value < 0:
        raise ValidationError(label + " must be nonnegative")
    if value.bit_length() > MAX_RATIONAL_COMPONENT_BITS:
        raise ValidationError(label + " exceeds the count bit bound")
    return value


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def exact_compute_cost(
    counts_by_phase: Mapping[str, Mapping[str, int]],
    weights: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return exact phase and total cost for one method/domain ledger.

    Both mappings must provide the complete frozen key rosters.  Counts are
    nonnegative exact integers and every calibration weight is strictly
    positive.  Binary floats and booleans are refused.
    """

    if type(counts_by_phase) is not dict:
        raise ValidationError("counts_by_phase must be an exact dictionary")
    if tuple(counts_by_phase) != PHASES:
        raise ValidationError("phase key roster or order mismatch")
    if type(weights) is not dict:
        raise ValidationError("weights must be an exact dictionary")
    if tuple(weights) != RESOURCE_EVENTS:
        raise ValidationError("weight key roster or order mismatch")
    exact_weights = {
        event: _fraction(weights[event], "weight " + event, positive=True)
        for event in RESOURCE_EVENTS
    }
    phase_costs: Dict[str, Dict[str, int]] = {}
    total = Fraction(0, 1)
    for phase in PHASES:
        counts = counts_by_phase[phase]
        if type(counts) is not dict or tuple(counts) != RESOURCE_EVENTS:
            raise ValidationError("resource count key roster or order mismatch: " + phase)
        phase_cost = Fraction(0, 1)
        for event in RESOURCE_EVENTS:
            phase_cost += _count(counts[event], phase + " " + event) * exact_weights[event]
        if (
            phase_cost.numerator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
            or phase_cost.denominator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
        ):
            raise ValidationError("phase cost exceeds accumulated bit bound")
        phase_costs[phase] = _fraction_record(phase_cost)
        total += phase_cost
    if (
        total.numerator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
        or total.denominator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
    ):
        raise ValidationError("total cost exceeds accumulated bit bound")
    return {
        "calculator_id": "EXACT_WEIGHTED_RESOURCE_LEDGER_V1",
        "phase_costs": phase_costs,
        "total_cost": _fraction_record(total),
        "binary_float_used": False,
    }


def _zero_counts() -> Dict[str, Dict[str, int]]:
    return {
        phase: {event: 0 for event in RESOURCE_EVENTS}
        for phase in PHASES
    }


SYNTHETIC_WEIGHTS: Dict[str, Fraction] = {
    "BASE_FORWARD": Fraction(3, 2),
    "BASE_BACKWARD": Fraction(3, 1),
    "CONDITIONER_FORWARD": Fraction(1, 1),
    "CONDITIONER_BACKWARD": Fraction(2, 1),
    "GUIDE_EVALUATION": Fraction(1, 4),
    "RESAMPLING_STEP": Fraction(1, 2),
    "ODE_OR_SDE_STEP": Fraction(1, 3),
    "DATA_ADAPTER_RECORD": Fraction(1, 10),
    "METRIC_DRAW_EVALUATION": Fraction(2, 5),
    "OTHER_DECLARED_OPERATION": Fraction(1, 1),
}
SYNTHETIC_COUNTS = _zero_counts()
SYNTHETIC_COUNTS["PILOT"]["BASE_FORWARD"] = 2
SYNTHETIC_COUNTS["PILOT"]["GUIDE_EVALUATION"] = 4
SYNTHETIC_COUNTS["TUNING"]["BASE_FORWARD"] = 4
SYNTHETIC_COUNTS["TUNING"]["BASE_BACKWARD"] = 2
SYNTHETIC_COUNTS["TUNING"]["CONDITIONER_FORWARD"] = 4
SYNTHETIC_COUNTS["TUNING"]["CONDITIONER_BACKWARD"] = 2
SYNTHETIC_COUNTS["FINAL_TRAINING"]["BASE_FORWARD"] = 6
SYNTHETIC_COUNTS["FINAL_TRAINING"]["BASE_BACKWARD"] = 3
SYNTHETIC_COUNTS["FINAL_TRAINING"]["CONDITIONER_FORWARD"] = 6
SYNTHETIC_COUNTS["FINAL_TRAINING"]["CONDITIONER_BACKWARD"] = 3
SYNTHETIC_COUNTS["FINAL_TRAINING"]["DATA_ADAPTER_RECORD"] = 10
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["BASE_FORWARD"] = 8
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["CONDITIONER_FORWARD"] = 8
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["GUIDE_EVALUATION"] = 8
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["RESAMPLING_STEP"] = 4
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["ODE_OR_SDE_STEP"] = 6
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["METRIC_DRAW_EVALUATION"] = 10
SYNTHETIC_QUALIFICATION = exact_compute_cost(SYNTHETIC_COUNTS, SYNTHETIC_WEIGHTS)


def _ancestor_snapshot(root: Path, leaf: Path) -> Tuple[Tuple[int, int, int], ...]:
    snapshots = []
    current = leaf.parent
    while True:
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValidationError("unsafe ancestor: " + str(current))
        snapshots.append((status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode)))
        if current == root:
            return tuple(snapshots)
        if root not in current.parents:
            raise ValidationError("path escaped workspace")
        current = current.parent


def _stable_read(root: Path, relative_path: str) -> bytes:
    if type(relative_path) is not str or not relative_path:
        raise ValidationError("binding path must be a nonempty string")
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValidationError("binding path must be canonical and relative")
    path = root / candidate
    ancestors = _ancestor_snapshot(root, path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError("binding must be a regular non-symlink file")
    if before.st_nlink != 1:
        raise ValidationError("binding must have exactly one hard link")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_opened = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    fingerprint = lambda item: (
        item.st_dev,
        item.st_ino,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
        stat.S_IFMT(item.st_mode),
        item.st_nlink,
    )
    if not (
        fingerprint(before)
        == fingerprint(opened)
        == fingerprint(after_opened)
        == fingerprint(after)
    ):
        raise ValidationError("file changed during read: " + relative_path)
    raw = b"".join(chunks)
    if len(raw) != before.st_size:
        raise ValidationError("short read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during read")
    return raw


EVIDENCE_SPECS: Tuple[Tuple[str, str], ...] = (
    ("EXECUTION_PREREGISTRATION_HUMAN", PREREG_HUMAN_PATH),
    ("EXECUTION_PREREGISTRATION_MACHINE", PREREG_MACHINE_PATH),
    ("PREEXECUTION_CLOSURE_HUMAN", CLOSURE_HUMAN_PATH),
    ("PREEXECUTION_CLOSURE_MACHINE", CLOSURE_MACHINE_PATH),
    ("SOLO_BLOCK2_STATIC_SELECTION_HUMAN", STATIC_HUMAN_PATH),
    ("SOLO_BLOCK2_STATIC_SELECTION_MACHINE", STATIC_MACHINE_PATH),
    ("POWER_ALLOCATION_ROUTE_HUMAN", POWER_HUMAN_PATH),
    ("POWER_ALLOCATION_ROUTE_MACHINE", POWER_MACHINE_PATH),
)

PACKAGE_SPECS: Tuple[Tuple[str, str], ...] = (
    ("HUMAN_DRAFT", HUMAN_PATH),
    ("EXACT_CALCULATOR_AND_READ_ONLY_VALIDATOR", VALIDATOR_PATH),
    ("HOSTILE_UNIT_TEST", TEST_PATH),
)


def _binding(ordinal: int, role: str, path: str, raw: bytes) -> Dict[str, Any]:
    return {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "terminal_lf": raw.endswith(b"\n"),
    }


def _expected_bindings(
    root: Path, specs: Sequence[Tuple[str, str]]
) -> List[Dict[str, Any]]:
    return [
        _binding(ordinal, role, path, _stable_read(root, path))
        for ordinal, (role, path) in enumerate(specs)
    ]


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_utf8_bytes": 92,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_REMOVED_ONLY",
    "raw_transport_bytes_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "timestamp_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "parallel_block2_block3_draft_work_authorized": True,
    "tracker_edit_authorized_only_after_independent_validation": True,
    "external_repository_license_or_paper_lookup_authorized": False,
    "package_installation_or_procurement_authorized": False,
    "data_access_training_tuning_or_scientific_execution_authorized": False,
    "runtime_approval_or_claim_promotion_authorized": False,
}


def _null_receipts(names: Sequence[str]) -> Dict[str, Any]:
    return {name: None for name in names}


PRIMARY_RECEIPT_FIELDS = (
    "repository",
    "commit",
    "config_sha256",
    "parameter_count",
    "training_compute_budget",
    "inference_compute_budget",
)
EXTERNAL_RECEIPT_FIELDS = (
    "method_id",
    "repository",
    "commit",
    "license",
    "config_sha256",
    "native_capability_and_extension_statement",
    "tuning_budget",
)

EXPECTED_DRAFT_IDENTITY: Mapping[str, Any] = {
    "route_id": "BASELINE_CAPABILITY_LICENSE_AND_MATCHED_COMPUTE_DRAFT_V1",
    "control_predicate": CONTROL_PREDICATE,
    "control_predicate_value_after_validation": True,
    "draft_complete": True,
    "baseline_matrix_populated": False,
    "compute_capacity_selected_or_reserved": False,
    "B06_closed": False,
    "B08_closed": False,
    "scientific_effect": 0,
}

EXPECTED_PRIMARY_PAIR = [
    {"method_id": method_id, "future_receipts": _null_receipts(PRIMARY_RECEIPT_FIELDS)}
    for method_id in PRIMARY_METHOD_IDS
]
EXPECTED_CONTROLS = [
    {
        "control_id": control_id,
        "row_kind": "LOCAL_INTERPRETATION_CONTROL",
        "implementation": None,
        "config_sha256": None,
        "may_discharge_external_family_row_without_equivalence_proof": False,
    }
    for control_id in CONTROL_IDS
]
EXPECTED_FAMILIES = [
    {
        "comparator_family_id": family_id,
        "row_kind": "EXTERNAL_LITERATURE_FAMILY",
        "required_domains": list(DOMAIN_IDS),
        "domain_rows": [
            {
                "domain_id": domain_id,
                "implementation_receipt": None,
                "inapplicability_or_equivalence_justification": None,
                "capability_matrix": {axis: "UNKNOWN" for axis in CAPABILITY_AXES},
                "admitted": False,
            }
            for domain_id in DOMAIN_IDS
        ],
    }
    for family_id in COMPARATOR_FAMILY_IDS
]
EXPECTED_EXTERNAL_BASELINES = [
    {
        "domain_id": domain_id,
        "row_kind": "STRONGEST_TASK_COMPATIBLE_EXTERNAL_DOMAIN_BASELINE",
        "future_receipts": _null_receipts(EXTERNAL_RECEIPT_FIELDS),
        "capability_matrix": {axis: "UNKNOWN" for axis in CAPABILITY_AXES},
        "admitted": False,
    }
    for domain_id in DOMAIN_IDS
]

EXPECTED_LICENSE: Mapping[str, Any] = {
    "required_receipts": [
        "CANONICAL_METHOD_AND_PACKAGE_IDENTITY",
        "CANONICAL_REPOSITORY_AND_IMMUTABLE_COMMIT_OR_RELEASE_DIGEST",
        "LICENSE_RAW_BYTES_SHA256_AND_DEFENSIBLE_SPDX_EXPRESSION",
        "LICENSE_SCOPE_FOR_CODE_WEIGHTS_CONFIGS_AND_MODIFICATIONS",
        "ENVIRONMENT_AND_EXACT_CONFIG_DIGEST",
        "PARAMETER_COUNT_PROCEDURE_AND_RESULT",
        "NATIVE_CAPABILITY_MATRIX_AND_AUTHOR_EXTENSION_BOUNDARY",
        "FINITE_TRAINING_INFERENCE_AND_TUNING_ALLOCATION",
        "INDEPENDENT_REPRODUCTION_REVIEW_RECEIPT",
    ],
    "current_external_receipts_observed": 0,
    "repository_or_license_inferred_from_family_name": False,
    "missing_ambiguous_conflicting_or_incompatible_disposition": "ROW_NO_GO",
    "post_test_replacement_extension_or_license_guess_permitted": False,
}

EXPECTED_CAPABILITY: Mapping[str, Any] = {
    "axes": list(CAPABILITY_AXES),
    "allowed_draft_states": list(CAPABILITY_STATES),
    "admissible_final_states": list(ADMISSIBLE_FINAL_CAPABILITY_STATES),
    "unknown_blocks_admission": True,
    "author_extension_requires_source_config_license_and_compute_receipts": True,
    "one_implementation_may_fill_multiple_family_rows_without_row_specific_equivalence_proof": False,
    "equivalence_dimensions": [
        "OBJECTIVE",
        "PROPOSAL_OR_CONDITIONING_SEMANTICS",
        "MODEL_CLASS",
        "COMPUTE",
        "TASK_INTERFACE",
    ],
}

EXPECTED_COMPUTE: Mapping[str, Any] = {
    "calculator_id": "EXACT_WEIGHTED_RESOURCE_LEDGER_V1",
    "formula": "C_M_D_EQUALS_SUM_OVER_PHASE_AND_RESOURCE_OF_INTEGER_COUNT_TIMES_EXACT_RATIONAL_WEIGHT",
    "phases": list(PHASES),
    "resource_events": list(RESOURCE_EVENTS),
    "accepted_count_type": "EXACT_NONNEGATIVE_PYTHON_INT_NOT_BOOL",
    "accepted_weight_type": "STRICTLY_POSITIVE_EXACT_INT_OR_FRACTIONS_FRACTION_NOT_BOOL_OR_FLOAT",
    "normalized_component_bit_bound": MAX_RATIONAL_COMPONENT_BITS,
    "accumulated_component_bit_bound": MAX_ACCUMULATED_COMPONENT_BITS,
    "hardware_calibration_weights_populated": False,
    "hardware_or_environment_selected": False,
    "prospective_equal_ceiling_required_for_primary_pair_within_domain": True,
    "same_base_groups_cases_draws_precision_and_metric_workload_required": True,
    "failed_attempts_author_extensions_and_unique_preprocessing_charged": True,
    "unused_budget_transfer_or_postresult_topup_permitted": False,
    "scalar_cost_sufficient_without_hard_axis_ceilings": False,
    "additional_hard_axes": [
        "WALL_TIME",
        "ACCELERATOR_TIME",
        "PEAK_DEVICE_MEMORY",
        "PEAK_HOST_MEMORY",
        "MODEL_EVALUATION_COUNT",
        "PERSISTENT_BYTES",
        "FAILURE_COUNT",
        "PARAMETER_COUNT",
    ],
    "fairness_interpretation": "EQUAL_PROSPECTIVE_CEILING_AND_SELECTION_OPPORTUNITY_WITH_ALL_REALIZED_USE_REPORTED",
    "real_compute_budget_or_capacity_claimed": False,
}

OPEN_FIELD_IDS = tuple(
    ["F{:03d}".format(index) for index in range(62, 105)]
    + ["F{:03d}".format(index) for index in range(150, 163)]
)

EXPECTED_NONCLOSURE: Mapping[str, Any] = {
    "blocker_status": {"B06": "OPEN", "B08": "OPEN"},
    "open_field_values": {field_id: None for field_id in OPEN_FIELD_IDS},
    "open_field_count_in_this_dependency_view": 56,
    "effective_project_unresolved_field_count": 172,
    "effective_project_open_blocker_count": 12,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_scientific_tests_closed": 0,
    "scientific_results_produced": 0,
    "matched_total_compute_formula_written_to_preregistration": False,
    "hardware_or_capacity_fields_written_to_preregistration": False,
}

EXPECTED_SCOPE: Mapping[str, Any] = {
    "static_draft_and_synthetic_exact_arithmetic_only": True,
    "web_network_connector_repository_paper_or_license_contact_used": False,
    "external_current_fact_verified": False,
    "package_installed_or_environment_mutated": False,
    "hardware_capacity_reserved_or_purchased": False,
    "data_or_test_outcome_accessed": False,
    "project_science_imported_or_invoked": False,
    "training_tuning_pilot_or_scientific_execution_performed": False,
    "scientific_seed_or_protocol_entropy_consumed": False,
    "runtime_approved_or_claim_promoted": False,
    "tracker_edited_by_package": False,
    "existing_predecessor_modified": False,
    "synthetic_vector_is_scientific_budget_or_capacity_evidence": False,
    "package_internal_only": True,
    "publication_safe_derivative_required": True,
}

EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "state",
    "global_state",
    "package_kind",
    "reported_date",
    "authority_provenance",
    "draft_identity",
    "primary_pair",
    "local_interpretation_controls",
    "literature_comparator_families",
    "external_domain_baselines",
    "license_receipt_contract",
    "capability_contract",
    "matched_compute_contract",
    "synthetic_qualification",
    "nonclosure",
    "scope_and_nonclaims",
    "evidence_bindings",
    "package_bindings",
    "record_sha256",
}


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
    elif type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for ordinal, (left, right) in enumerate(zip(actual, expected)):
            _strict_equal(left, right, label + "[" + str(ordinal) + "]")
    elif actual != expected:
        raise ValidationError(label + " value mismatch")


def _validate_preregistration(raw: bytes) -> None:
    prereg = _strict_json(raw, "execution preregistration")
    if prereg.get("state") != GLOBAL_STATE:
        raise ValidationError("preregistration state changed")
    if prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("preregistration authority changed")
    plan = prereg.get("method_and_baseline_plan")
    if type(plan) is not dict:
        raise ValidationError("method and baseline plan missing")
    if plan.get("same_frozen_unconditional_base_within_domain_required") is not True:
        raise ValidationError("shared-base requirement changed")
    primary = plan.get("primary_method")
    comparator = plan.get("primary_comparator")
    if type(primary) is not dict or type(comparator) is not dict:
        raise ValidationError("primary pair missing")
    for row, method_id in zip((primary, comparator), PRIMARY_METHOD_IDS):
        if row.get("method_id") != method_id:
            raise ValidationError("primary method ID changed")
        for field in PRIMARY_RECEIPT_FIELDS:
            if row.get(field) is not None:
                raise ValidationError("primary receipt no longer open: " + field)
    controls = plan.get("required_controls")
    if type(controls) is not list or tuple(row.get("control_id") for row in controls) != CONTROL_IDS:
        raise ValidationError("control roster changed")
    for row in controls:
        if row.get("implementation") is not None or row.get("config_sha256") is not None:
            raise ValidationError("control receipt no longer open")
    families = plan.get("required_literature_comparator_families")
    if (
        type(families) is not list
        or tuple(row.get("comparator_family_id") for row in families)
        != COMPARATOR_FAMILY_IDS
    ):
        raise ValidationError("comparator-family roster changed")
    for row in families:
        if row.get("required_domains") != list(DOMAIN_IDS):
            raise ValidationError("family required-domain roster changed")
        if (
            row.get("implementation_by_domain") is not None
            or row.get("inapplicability_or_equivalence_justification_by_domain") is not None
        ):
            raise ValidationError("comparator-family receipt no longer open")
    baselines = plan.get("external_domain_baselines")
    if type(baselines) is not list or tuple(row.get("domain_id") for row in baselines) != DOMAIN_IDS:
        raise ValidationError("external-domain baseline roster changed")
    for row in baselines:
        for field in EXTERNAL_RECEIPT_FIELDS:
            if row.get(field) is not None:
                raise ValidationError("external baseline receipt no longer open: " + field)
    if plan.get("matched_total_compute_formula") is not None:
        raise ValidationError("matched-compute field no longer open")
    if plan.get("post_test_baseline_or_ablation_change_permitted") is not False:
        raise ValidationError("post-test baseline boundary changed")

    compute = prereg.get("compute_and_fairness_plan")
    if type(compute) is not dict:
        raise ValidationError("compute and fairness plan missing")
    for field in (
        "hardware",
        "software_environment_sha256",
        "container_or_lockfile_sha256",
        "deterministic_settings",
        "per_run_wall_time_ceiling",
        "per_run_accelerator_hour_ceiling",
        "per_run_peak_memory_ceiling",
        "per_run_model_evaluation_ceiling",
        "pilot_compute_allocation",
        "tuning_compute_allocation",
        "final_compute_allocation",
        "failure_reserve",
        "total_compute_ceiling",
    ):
        if compute.get(field) is not None:
            raise ValidationError("compute field no longer open: " + field)
    if (
        compute.get("primary_training_and_inference_compute_matched") is not True
        or compute.get("realized_compute_report_required") is not True
        or compute.get("post_result_compute_topup_permitted") is not False
    ):
        raise ValidationError("compute fairness boundary changed")


def _validate_other_predecessors(raws: Mapping[str, bytes]) -> None:
    closure = _strict_json(raws[CLOSURE_MACHINE_PATH], "preexecution closure")
    projection = closure.get("blocker_projection")
    if type(projection) is not dict or projection.get("blockers_closed_by_closure") != 0:
        raise ValidationError("closure blocker projection changed")
    static = _strict_json(raws[STATIC_MACHINE_PATH], "static selection")
    inventory = static.get("method_gap_inventory")
    if type(inventory) is not list or len(inventory) != 14:
        raise ValidationError("method gap inventory changed")
    if any(type(row) is not dict for row in inventory):
        raise ValidationError("method gap inventory row type changed")
    if tuple(row.get("ordinal") for row in inventory) != tuple(range(14)):
        raise ValidationError("method gap inventory incomplete")
    if tuple(row.get("inventory_id") for row in inventory[:5]) != (
        "PRIMARY_METHOD_AND_COMPARATOR_IDENTITIES",
        "FOUR_REQUIRED_CONTROLS",
        "FOUR_LITERATURE_COMPARATOR_FAMILIES",
        "TWO_EXTERNAL_DOMAIN_BASELINES",
        "MATCHED_COMPUTE_FORMULA",
    ):
        raise ValidationError("B06 gap inventory roster changed")
    checklist = static.get("checklist_effects")
    if (
        type(checklist) is not dict
        or checklist.get("method_runtime_open_field_count") != 65
        or checklist.get("runtime_approval_authorized") is not False
    ):
        raise ValidationError("static method/runtime nonclosure changed")
    power = _strict_json(raws[POWER_MACHINE_PATH], "power allocation route")
    identity = power.get("route_identity")
    if (
        type(identity) is not dict
        or identity.get("compute_budget_selected") is not False
        or identity.get("real_domain_allocation_selected") is not False
        or identity.get("scientific_effect") != 0
    ):
        raise ValidationError("power-route compute nonclosure changed")


def _validate_semantics(record: Mapping[str, Any]) -> None:
    if set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("machine record top-level key roster mismatch")
    if record["schema_version"] != SCHEMA:
        raise ValidationError("schema mismatch")
    if record["state"] != STATE or record["global_state"] != GLOBAL_STATE:
        raise ValidationError("state mismatch")
    if record["package_kind"] != PACKAGE_KIND or record["reported_date"] != REPORTED_DATE:
        raise ValidationError("package identity mismatch")
    for key, expected in (
        ("authority_provenance", EXPECTED_AUTHORITY),
        ("draft_identity", EXPECTED_DRAFT_IDENTITY),
        ("primary_pair", EXPECTED_PRIMARY_PAIR),
        ("local_interpretation_controls", EXPECTED_CONTROLS),
        ("literature_comparator_families", EXPECTED_FAMILIES),
        ("external_domain_baselines", EXPECTED_EXTERNAL_BASELINES),
        ("license_receipt_contract", EXPECTED_LICENSE),
        ("capability_contract", EXPECTED_CAPABILITY),
        ("matched_compute_contract", EXPECTED_COMPUTE),
        ("synthetic_qualification", SYNTHETIC_QUALIFICATION),
        ("nonclosure", EXPECTED_NONCLOSURE),
        ("scope_and_nonclaims", EXPECTED_SCOPE),
    ):
        expected_copy = list(expected) if type(expected) is list else dict(expected)
        _strict_equal(record[key], expected_copy, key)
    if list(record["nonclosure"]["open_field_values"]) != list(OPEN_FIELD_IDS):
        raise ValidationError("open field order changed")
    if record["synthetic_qualification"]["total_cost"] != {
        "numerator": 85,
        "denominator": 1,
    }:
        raise ValidationError("synthetic exact-cost vector changed")


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate exact custody and return a non-scientific draft status."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    raw = _stable_read(workspace, MACHINE_PATH)
    record = _strict_json(raw, "baseline capability compute machine record")
    if type(record.get("record_sha256")) is not str:
        raise ValidationError("record self-digest must be a string")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("record self-digest mismatch")
    _validate_semantics(record)

    expected_evidence = _expected_bindings(workspace, EVIDENCE_SPECS)
    expected_package = _expected_bindings(workspace, PACKAGE_SPECS)
    _strict_equal(record["evidence_bindings"], expected_evidence, "evidence bindings")
    _strict_equal(record["package_bindings"], expected_package, "package bindings")
    raws = {
        row["path"]: _stable_read(workspace, row["path"])
        for row in record["evidence_bindings"]
    }
    _validate_preregistration(raws[PREREG_MACHINE_PATH])
    _validate_other_predecessors(raws)

    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value": True,
        "draft_complete": True,
        "primary_pair_count": 2,
        "local_control_count": 4,
        "comparator_family_count": 4,
        "family_domain_row_count": 8,
        "external_domain_baseline_count": 2,
        "synthetic_exact_total_cost": 85,
        "B06_open": True,
        "B08_open": True,
        "dependency_open_field_count": 56,
        "scientific_effect": 0,
        "validation": "PASS",
    }


__all__ = ["ValidationError", "exact_compute_cost", "record_sha256", "validate"]
