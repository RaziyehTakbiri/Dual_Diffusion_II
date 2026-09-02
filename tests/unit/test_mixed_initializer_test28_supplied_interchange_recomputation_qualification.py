"""Independent and hostile tests for the CP71 supplied-stream reducer."""

from __future__ import annotations

import ast
import gc
import hashlib
import inspect
import json
import math
import subprocess
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    cast,
)

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_supplied_interchange_recomputation_qualification as cp71,
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_supplied_interchange_recomputation_qualification.py"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")

_ZERO_SHA256 = "0" * 64
_CP69_SCHEMA = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_COMPACT_SCHEMA = "cp63-test28-independent-compact-recomputation-v1"
_CP68_SCHEMA = "cp68-test28-compact-projection-aggregation-qualification-v1"
_CP71_PROJECTION_SCHEMA = "cp71-test28-supplied-compact-projection-v1"
_INPUT_RECORD_DOMAIN = b"cp69-test28-compact-interchange-observation-v1"
_PROJECTION_DOMAIN = b"cp71-test28-supplied-compact-projection-record-v1"
_ORDERED_INPUT_DOMAIN = b"cp69-test28-ordered-interchange-record-digests-v1"
_ORDERED_PROJECTION_DOMAIN = (
    b"cp71-test28-ordered-supplied-compact-projection-record-digests-v1"
)
_OUTPUT_RECORD_DOMAIN = b"cp71-test28-supplied-estimand-estimate-interval-v1"
_STREAM_COMMITMENT_DOMAIN = b"cp71-test28-supplied-interchange-stream-commitment-v1"
_OUTPUT_BODY_DOMAIN = (
    b"cp71-test28-supplied-interchange-estimate-interval-output-body-v1"
)

_SEED_COUNT = 2_048
_ROW_COUNT = 16
_REQUEST_COUNT = 32_768
_ESTIMAND_COUNT = 554
_BINOMIAL_COUNT = 242
_FEATURE_COUNT = 312
_RUNTIME_SHA256 = "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"

_ROW_SHAPES = (
    ("T28-M1-Q", "bounded-rejection", 1),
    ("T28-M1-Q", "bounded-rejection", 4),
    ("T28-M1-Q", "bounded-rejection", 16),
    ("T28-M1-Q", "bounded-rejection", 64),
    ("T28-M1-Q", "fixed-budget-sir", 8),
    ("T28-M1-Q", "fixed-budget-sir", 32),
    ("T28-M1-Q", "fixed-budget-sir", 128),
    ("T28-M1-Q", "fixed-budget-sir", 512),
    ("T28-M2-Q", "bounded-rejection", 1),
    ("T28-M2-Q", "bounded-rejection", 4),
    ("T28-M2-Q", "bounded-rejection", 16),
    ("T28-M2-Q", "bounded-rejection", 64),
    ("T28-M2-Q", "fixed-budget-sir", 8),
    ("T28-M2-Q", "fixed-budget-sir", 32),
    ("T28-M2-Q", "fixed-budget-sir", 128),
    ("T28-M2-Q", "fixed-budget-sir", 512),
)
_REJECTION_CELLS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_SIR_CELLS = (
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)

_INPUT_KEYS = (
    "schema_version",
    "source_semantic_schema_version",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "seed_free_request_sha256",
    "request_instance_sha256",
    "runtime_lock_sha256",
    "stable_trace_sha256",
    "observable_cell_label",
    "observable_contribution_ordinal",
    "first_selected_attempt_one_based",
    "selected",
    "selected_feature_ids",
    "selected_feature_values",
    "record_sha256",
)

_ROOT_KEYS = (
    "schema_version",
    "source_interchange_schema_version",
    "source_semantic_schema_version",
    "input_stream_classification",
    "input_stream_commitment_sha256",
    "input_provenance_authenticated",
    "source_law_verified",
    "external_seed_source_verified",
    "runtime_lock_authenticated",
    "request_instance_sha256_authenticated",
    "stable_trace_sha256_authenticated",
    "cp61_estimand_digest_is_inventory_reference_only",
    "cp61_estimand_semantics_realized",
    "production_attempt_validity_evaluated",
    "production_recomputation",
    "arithmetic_transform_only",
    "request_count",
    "total_input_bytes",
    "estimand_count",
    "ordered_interchange_record_sha256",
    "ordered_projection_sha256",
    "ordered_seed_ordinal_plan_seed_sha256",
    "ordered_request_instance_sha256",
    "ordered_stable_trace_sha256",
    "runtime_lock_sha256",
    "estimand_estimate_intervals",
)

_OUTPUT_RECORD_KEYS = (
    "schema_version",
    "estimand_ordinal",
    "estimand_id",
    "cp61_estimand_record_sha256",
    "estimand_family",
    "row_ordinal",
    "fixture_id",
    "strategy",
    "budget",
    "observable_cell_label",
    "first_attempt_one_based",
    "feature_id",
    "feature_lower_bound",
    "feature_upper_bound",
    "denominator_mode",
    "denominator_count",
    "success_count",
    "exact_feature_sum",
    "estimate",
    "interval_method",
    "interval_state",
    "interval_lower",
    "interval_upper",
    "development_supplied_input_only",
    "input_provenance_authenticated",
    "arithmetic_transform_only",
    "record_sha256",
)

_RECORD_FIELDS = {
    "CP71PredecessorCustodyV1": (
        "schema_version",
        "v21_protocol_sha256",
        "v21_protocol_bytes",
        "v21_protocol_lf_count",
        "v21_manifest_sha256",
        "v21_manifest_bytes",
        "v21_manifest_lf_count",
        "cp61_source_sha256",
        "cp61_bundle_record_sha256",
        "cp61_stable_design_sha256",
        "cp61_projection_contract_record_sha256",
        "cp63_independent_source_sha256",
        "cp63_independent_test_sha256",
        "cp63_independent_bundle_record_sha256",
        "cp63_schedule_contract_record_sha256",
        "cp68_source_sha256",
        "cp68_test_sha256",
        "cp68_output_schema_record_sha256",
        "cp68_aggregation_expectation_record_sha256",
        "cp68_output_canonical_json_sha256",
        "cp69_source_sha256",
        "cp69_test_sha256",
        "cp69_bundle_record_sha256",
        "cp69_interchange_contract_record_sha256",
        "cp69_full_stream_expectation_record_sha256",
        "cp69_ordered_interchange_record_sha256",
        "cp70_source_sha256",
        "cp70_test_sha256",
        "cp70_bundle_record_sha256",
        "cp70_reducer_contract_record_sha256",
        "cp70_output_validation_contract_record_sha256",
        "cp70_full_reduction_expectation_record_sha256",
        "cp70_output_canonical_json_sha256",
        "record_sha256",
    ),
    "CP71SuppliedInterchangeStreamContractV1": (
        "schema_version",
        "contract_id",
        "source_interchange_schema_version",
        "source_semantic_schema_version",
        "exact_input_keys",
        "canonical_json_profile",
        "exact_fraction_encoding",
        "interchange_record_digest_domain",
        "projection_digest_domain",
        "seed_count",
        "row_count",
        "request_count",
        "logical_request_order",
        "logical_request_ordinal_formula",
        "same_plan_seed_across_row_group_required",
        "duplicate_plan_seed_values_across_seed_ordinals_allowed",
        "exact_row_specific_seed_free_request_sha256s",
        "single_stream_runtime_lock_sha256_required",
        "runtime_lock_authenticated",
        "request_instance_sha256_authenticated",
        "stable_trace_sha256_authenticated",
        "source_provenance_authenticated",
        "accepted_input_scope",
        "caller_iterable_invoked",
        "caller_iterable_side_effects_qualified",
        "caller_iterable_retention_qualified",
        "caller_next_liveness_qualified",
        "iterator_close_called",
        "maximum_next_calls",
        "module_direct_filesystem_api_exposed",
        "module_direct_clock_api_exposed",
        "module_direct_rng_api_exposed",
        "module_direct_network_api_exposed",
        "module_direct_subprocess_api_exposed",
        "maximum_interchange_bytes",
        "maximum_stream_bytes",
        "maximum_input_depth",
        "maximum_input_nodes",
        "maximum_input_text_bytes",
        "maximum_input_integer_decimal_digits",
        "maximum_input_integer_bits",
        "maximum_aggregate_integer_bits",
        "record_sha256",
    ),
    "CP71DevelopmentEstimateIntervalOutputContractV1": (
        "schema_version",
        "contract_id",
        "output_schema_version",
        "source_interchange_schema_version",
        "source_semantic_schema_version",
        "cp68_scientific_compatibility_schema_version",
        "exact_output_root_keys",
        "exact_estimand_record_keys",
        "input_stream_classification",
        "estimand_count",
        "binomial_estimand_count",
        "feature_estimand_count",
        "numeric_estimand_arithmetic_compatible_with_cp68",
        "cp61_estimand_digest_is_inventory_reference_only",
        "cp61_estimand_semantics_realized",
        "cp68_closed_fixture_set_sha256_field_present",
        "dynamic_input_stream_commitment_required",
        "binomial_interval_method",
        "binomial_trial_count",
        "familywise_error_budget",
        "per_estimator_error_budget",
        "per_tail_error_budget",
        "cp_bisection_steps",
        "all_success_counts_admitted",
        "precomputed_closed_endpoint_table_required",
        "feature_interval_method",
        "minimum_selected_count",
        "feature_halfwidth_range_multiplier",
        "computed_interval_states",
        "feature_sum_absent_when_no_selection",
        "estimate_present_when_positive_selection",
        "interval_absent_below_minimum_selection",
        "strict_discriminated_union",
        "primary_thresholds_present",
        "decision_fields_present",
        "intervals_are_arithmetic_transforms_only",
        "iid_source_law_or_coverage_claimed",
        "production_attempt_validity_evaluated",
        "estimand_record_digest_domain",
        "ordered_estimand_digest_domain",
        "ordered_seed_plan_digest_domain",
        "ordered_request_instance_digest_domain",
        "ordered_stable_trace_digest_domain",
        "stream_commitment_digest_domain",
        "output_body_digest_domain",
        "maximum_aggregate_integer_bits",
        "maximum_output_record_bytes",
        "maximum_output_bytes",
        "record_sha256",
    ),
    "CP71SuppliedDevelopmentReductionSummaryV1": (
        "schema_version",
        "source_interchange_schema_version",
        "source_semantic_schema_version",
        "output_schema_version",
        "request_count",
        "seed_count",
        "row_count",
        "total_input_bytes",
        "input_stream_commitment_sha256",
        "first_interchange_record_sha256",
        "ordered_interchange_record_sha256",
        "ordered_projection_sha256",
        "ordered_seed_ordinal_plan_seed_sha256",
        "ordered_request_instance_sha256",
        "ordered_stable_trace_sha256",
        "runtime_lock_sha256",
        "distinct_plan_seed_count",
        "duplicate_plan_seed_count",
        "plan_seed_row_group_coherence_verified",
        "row_seed_free_request_sha256s_matched",
        "runtime_lock_stream_coherence_verified",
        "selected_counts_by_row",
        "status_counts",
        "observable_row_sums",
        "rejection_first_attempt_row_sums",
        "first_attempt_contribution_count",
        "feature_contribution_count",
        "aggregation_update_count",
        "feature_estimate_present_count",
        "feature_estimate_absent_count",
        "binomial_interval_count",
        "feature_interval_count",
        "computed_interval_count",
        "insufficient_selection_count",
        "distinct_cp_success_count_count",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
        "input_provenance_authenticated",
        "external_seed_source_verified",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "production_recomputation",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_made",
        "production_evidence",
        "record_sha256",
    ),
    "CP71SuppliedInterchangeRecomputationQualificationV1": (
        "schema_version",
        "fixture_set_sha256",
        "fixture_ids",
        "fixture_stream_commitment_sha256s",
        "fixture_summary_record_sha256s",
        "fixture_output_canonical_json_bytes",
        "fixture_output_canonical_json_sha256s",
        "baseline_cp68_compatibility_output_canonical_json_sha256",
        "baseline_cp68_compatibility_projection_exact_match",
        "dynamic_fixture_count",
        "dynamic_cp68_fixture_custody_claimed",
        "novel_success_counts",
        "encountered_success_counts",
        "encountered_success_count_count",
        "exact_endpoint_boundary_comparison_count",
        "approximate_candidate_decides_endpoint",
        "module_owned_total_request_count",
        "module_owned_total_input_bytes",
        "module_owned_peak_input_payload_count",
        "module_owned_peak_parsed_observation_count",
        "module_owned_plan_seed_value_maximum_retained_count",
        "module_owned_full_input_corpus_materialized",
        "module_owned_input_records_retained_after_successful_return",
        "dynamic_input_payload_or_output_body_cached",
        "sealed_summary_snapshot_retained_while_summary_live",
        "output_record_vector_cardinality",
        "maximum_simultaneously_materialized_output_record_count",
        "caller_iterable_side_effects_qualified",
        "caller_next_liveness_qualified",
        "module_direct_filesystem_read",
        "module_direct_filesystem_write",
        "module_direct_clock_read",
        "module_direct_rng_used",
        "module_direct_network_used",
        "module_direct_subprocess_used",
        "raw_record_parsed",
        "stable_trace_parsed",
        "provenance_authenticated",
        "production_recomputation_performed",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_path_qualified",
        "production_gate_13_state",
        "production_gate_14_state",
        "production_evidence_present_count",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
        "all_development_qualification_checks_passed",
        "record_sha256",
    ),
    "CP71SuppliedInterchangeRecomputationQualificationBundleV1": (
        "schema_version",
        "scope",
        "blocker_ledger_prerequisite_id",
        "blocker_ledger_prerequisite_state",
        "blocker_ledger_total_count",
        "blocker_ledger_satisfied_count",
        "blocker_ledger_missing_count",
        "predecessor_custody",
        "supplied_interchange_stream_contract",
        "development_estimate_interval_output_contract",
        "qualification_fixture_ids",
        "qualification_fixture_specifications",
        "zero_argument_builder",
        "builder_reduces_or_validates",
        "qualification_runner_zero_argument",
        "public_supplied_stream_reducer_exposed",
        "public_caller_data_api_count",
        "public_parser_exposed",
        "public_output_validator_exposed",
        "public_projection_mapper_exposed",
        "public_raw_record_api_exposed",
        "public_stable_trace_api_exposed",
        "public_path_api_exposed",
        "public_writer_api_exposed",
        "public_primary_decision_threshold_api_exposed",
        "public_decision_api_exposed",
        "public_evidence_api_exposed",
        "project_modules_imported",
        "source_independent",
        "stdlib_only",
        "production_execution_authorized",
        "production_recomputation_qualified",
        "unconditional_operational_predictions_produced",
        "power_review_present",
        "primary_thresholds_present",
        "confirmatory_custody_present",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "formal_test_28_status",
        "formal_test_28_closed",
        "record_sha256",
    ),
}

_EXPECTED_EXPORTS = (
    "CP71_TEST28_SCHEMA_VERSION",
    "CP71_TEST28_SCOPE",
    "CP71_TEST28_FORMAL_TEST_28_STATUS",
    "CP71_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP71_TEST28_SEED_COUNT",
    "CP71_TEST28_ROW_COUNT",
    "CP71_TEST28_REQUEST_COUNT",
    "CP71_TEST28_ESTIMAND_COUNT",
    "CP71_TEST28_OBSERVABLE_ESTIMAND_COUNT",
    "CP71_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
    "CP71_TEST28_FEATURE_ESTIMAND_COUNT",
    "CP71_TEST28_BINOMIAL_ESTIMAND_COUNT",
    "CP71_TEST28_FAMILYWISE_ERROR_BUDGET",
    "CP71_TEST28_PER_ESTIMATOR_ERROR_BUDGET",
    "CP71_TEST28_PER_TAIL_ERROR_BUDGET",
    "CP71_TEST28_CP_BISECTION_STEPS",
    "CP71_TEST28_MINIMUM_SELECTED_COUNT",
    "CP71_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER",
    "CP71_TEST28_MAXIMUM_INTERCHANGE_BYTES",
    "CP71_TEST28_MAXIMUM_STREAM_BYTES",
    "CP71_TEST28_MAXIMUM_INPUT_DEPTH",
    "CP71_TEST28_MAXIMUM_INPUT_NODES",
    "CP71_TEST28_MAXIMUM_INPUT_TEXT_BYTES",
    "CP71_TEST28_MAXIMUM_INPUT_INTEGER_DECIMAL_DIGITS",
    "CP71_TEST28_MAXIMUM_INPUT_INTEGER_BITS",
    "CP71_TEST28_MAXIMUM_AGGREGATE_INTEGER_BITS",
    "CP71_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES",
    "CP71_TEST28_MAXIMUM_OUTPUT_BYTES",
    "CP71_TEST28_MAXIMUM_SEALED_RECORD_BYTES",
    "CP71_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT",
    "CP71_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY",
    "CP71_TEST28_STATUS_ORDER",
    "CP71_TEST28_QUALIFICATION_FIXTURE_IDS",
    "CP71_TEST28_ERROR_CODES",
    "CP71SuppliedInterchangeRecomputationQualificationError",
    "CP71PredecessorCustodyV1",
    "CP71SuppliedInterchangeStreamContractV1",
    "CP71DevelopmentEstimateIntervalOutputContractV1",
    "CP71SuppliedDevelopmentReductionSummaryV1",
    "CP71SuppliedInterchangeRecomputationQualificationV1",
    "CP71SuppliedInterchangeRecomputationQualificationBundleV1",
    "cp71_canonical_json_bytes",
    "cp71_sha256",
    "cp71_reduce_supplied_cp69_interchange_byte_stream",
    "cp71_supplied_interchange_recomputation_qualification_bundle",
    "cp71_run_supplied_interchange_recomputation_qualification",
)

_ERROR_CODES = tuple(
    "CP71_" + suffix
    for suffix in (
        "STREAM_ITERABLE_INVALID",
        "STREAM_ITERATION_FAILED",
        "STREAM_COUNT_MISMATCH",
        "STREAM_RESOURCE_LIMIT",
        "INPUT_TYPE_MISMATCH",
        "INPUT_BYTE_LIMIT",
        "INPUT_ENCODING_INVALID",
        "INPUT_JSON_INVALID",
        "INPUT_CANONICAL_MISMATCH",
        "INPUT_RESOURCE_LIMIT",
        "INPUT_FIELD_SET_MISMATCH",
        "INPUT_FIELD_TYPE_MISMATCH",
        "INPUT_SCHEMA_MISMATCH",
        "INPUT_ORDINAL_MISMATCH",
        "INPUT_ROW_MISMATCH",
        "INPUT_OUTCOME_MISMATCH",
        "INPUT_CONTRIBUTION_ORDINAL_MISMATCH",
        "INPUT_FRACTION_MISMATCH",
        "INPUT_FEATURE_MISMATCH",
        "INPUT_DIGEST_MISMATCH",
        "INPUT_GROUP_COHERENCE_MISMATCH",
        "AGGREGATE_RESOURCE_LIMIT",
        "OUTPUT_RESOURCE_LIMIT",
        "RESOURCE_EXHAUSTED",
        "RECORD_TYPE_MISMATCH",
        "RECORD_NOT_ISSUED",
        "RECORD_TAMPERED",
        "INTERNAL_INVARIANT_FAILED",
    )
)

_SEED_FREE_SHA256S = (
    "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a",
    "f9f2d4f1d8aad14bbe5075b4febd763af4652fb4dda337e7a8d295b3a6045ec2",
    "4413d707c0165dbf18e88df043edd760a75d4eed44d039a611402e06de9c4eb8",
    "29f1f28fb222d258746cb7956a9ca0d65a6e97d398eddb1612720a9339eed338",
    "71701768f889fee219b854217de255f3d034202a3a66875ceade1cd55955896a",
    "bd7c4fd661bda70f29b8582c0db52d91d68fc703ae8838295a21cf9e6e55f23a",
    "801f600536240a2f6f3de0dcac8d4092c2121fd17dc14fb0ca0bfc3b0260acb8",
    "8e5458a8dfca1e49875cad53deff7447274ce3055960a0031cc07c4ec4de33e0",
    "7d32b4e85d39504864268b7ba39189f17c3171d11079638e37a6614b97a543bf",
    "17f11b448585709ef35a172e86665c83b2ea50a907caacdd400dbd8ce625771b",
    "57937405e7302fcd9b9935050050a74e4b2c2818e17d720cde1ee2a56352bcf3",
    "878797b61ec628ae5db0e882d6f3c34531468fbbc35fd92325063a3b017c1bd8",
    "bc7b374f072aa402264634bcf520834a71609af5f6705b9b8ac3079884cd0376",
    "1b60b917c4fba30085678101276fe2a210aaa82f34deb6ad4f9440a38cc3b074",
    "a88491906e47ec4f5483b638ce411b8afd4ce7b5d73f19e372ab68a405f6d81c",
    "0667c6c19a9b54db91f2167f685abdcaafcab73cbc4bcfaebcb420511ecc89c8",
)

_M1_FEATURES = (
    ("count/eq/0", Fraction(0), Fraction(1)),
    ("count/eq/1", Fraction(0), Fraction(1)),
    ("type/0/occupancy", Fraction(0), Fraction(1)),
    ("type/1/occupancy", Fraction(0), Fraction(1)),
    ("coordinate/1/axis0/odd", Fraction(-1), Fraction(1)),
    ("coordinate/1/axis0/even", Fraction(0), Fraction(1)),
)
_M2_FEATURE_IDS = (
    "count/eq/0",
    "count/eq/1",
    "count/eq/2",
    "type/0/occupancy",
    "type/1/occupancy",
    "coordinate/0/axis0/odd",
    "coordinate/0/axis0/even",
    "coordinate/1/axis0/odd",
    "coordinate/1/axis0/even",
    "coordinate/1/axis1/odd",
    "coordinate/1/axis1/even",
    "coordinate/1/diag-plus-3-4/odd",
    "coordinate/1/diag-plus-3-4/even",
    "coordinate/1/diag-minus-3-4/odd",
    "coordinate/1/diag-minus-3-4/even",
    "pair-type/0/0",
    "pair-type/0/1",
    "pair-type/1/1",
    "pair-projection/0/axis0/0/axis0",
    "pair-projection/0/axis0/1/axis0",
    "pair-projection/0/axis0/1/axis1",
    "pair-projection/0/axis0/1/diag-plus-3-4",
    "pair-projection/0/axis0/1/diag-minus-3-4",
    "pair-projection/1/axis0/1/axis0",
    "pair-projection/1/axis0/1/axis1",
    "pair-projection/1/axis0/1/diag-plus-3-4",
    "pair-projection/1/axis0/1/diag-minus-3-4",
    "pair-projection/1/axis1/1/axis1",
    "pair-projection/1/axis1/1/diag-plus-3-4",
    "pair-projection/1/axis1/1/diag-minus-3-4",
    "pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
)


def _m2_bounds(feature_id: str) -> Tuple[Fraction, Fraction]:
    if (
        feature_id.startswith("count/")
        or feature_id.startswith("type/")
        or feature_id.startswith("pair-type/")
        or feature_id.endswith("/even")
    ):
        return Fraction(0), Fraction(1)
    return Fraction(-1), Fraction(1)


_M2_FEATURES = tuple(
    (feature_id,) + _m2_bounds(feature_id) for feature_id in _M2_FEATURE_IDS
)


def _features(fixture_id: str) -> Tuple[Tuple[str, Fraction, Fraction], ...]:
    return _M1_FEATURES if fixture_id == "T28-M1-Q" else _M2_FEATURES


def _row_key(row: int) -> str:
    fixture, strategy, budget = _ROW_SHAPES[row - 1]
    return f"row-{row:02d}/{fixture}/{strategy}/budget-{budget}"


def _cells(row: int) -> Tuple[str, ...]:
    return (
        _REJECTION_CELLS
        if _ROW_SHAPES[row - 1][1] == "bounded-rejection"
        else _SIR_CELLS
    )


def _observable_ordinal(row: int, status: str) -> int:
    offset = sum(len(_cells(candidate)) for candidate in range(1, row))
    return offset + _cells(row).index(status) + 1


def _to_plain(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is Fraction:
        fraction = cast(Fraction, value)
        return {"$fraction": [str(fraction.numerator), str(fraction.denominator)]}
    if type(value) in (tuple, list):
        return [_to_plain(item) for item in cast(Iterable[object], value)]
    if type(value) is dict:
        return {
            cast(str, key): _to_plain(item)
            for key, item in cast(Mapping[str, object], value).items()
        }
    if hasattr(value, "__dataclass_fields__"):
        return {
            item.name: _to_plain(getattr(value, item.name)) for item in fields(value)
        }
    raise TypeError(f"unsupported oracle canonical type: {type(value)!r}")


def _canonical(value: object) -> bytes:
    return json.dumps(
        _to_plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _strict_pairs(pairs: List[Tuple[str, object]]) -> dict:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_float(_value: str) -> object:
    raise ValueError("float forbidden")


def _decode_payload(payload: bytes) -> dict:
    value = json.loads(
        payload.decode("ascii"),
        object_pairs_hook=_strict_pairs,
        parse_float=_reject_float,
        parse_constant=_reject_float,
    )
    assert type(value) is dict
    assert _canonical(value) == payload
    return cast(dict, value)


def _fraction(value: object) -> Optional[Fraction]:
    if value is None:
        return None
    assert type(value) is dict and set(cast(dict, value)) == {"$fraction"}
    pair = cast(dict, value)["$fraction"]
    assert type(pair) is list and len(pair) == 2
    return Fraction(int(pair[0]), int(pair[1]))


def _sha(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _canonical(value)).hexdigest()


def _input_record_sha(values: Mapping[str, object]) -> str:
    body = dict(values)
    body["record_sha256"] = _ZERO_SHA256
    return _sha(_INPUT_RECORD_DOMAIN, body)


def _projection_sha(values: Mapping[str, object]) -> str:
    body = {
        "schema_version": _CP71_PROJECTION_SCHEMA,
        "seed_ordinal": values["seed_ordinal"],
        "row_ordinal": values["row_ordinal"],
        "logical_request_ordinal": values["logical_request_ordinal"],
        "row_key": values["row_key"],
        "fixture_id": values["fixture_id"],
        "strategy": values["strategy"],
        "budget": values["budget"],
        "plan_seed_hex": values["plan_seed_hex"],
        "observable_cell_label": values["observable_cell_label"],
        "first_selected_attempt_one_based": values["first_selected_attempt_one_based"],
        "selected": values["selected"],
        "selected_feature_ids": tuple(values["selected_feature_ids"]),
        "selected_feature_values": tuple(values["selected_feature_values"]),
    }
    return _sha(_PROJECTION_DOMAIN, body)


def _synthetic_sha(domain: bytes, value: object) -> str:
    return _sha(domain, value)


_CP_GRID_DENOMINATOR = 1 << 256
_CP_TAIL_RECIPROCAL = 110_800


@lru_cache(maxsize=None)
def _independent_upper_tail_compare(success_count: int, numerator: int) -> int:
    """Compare one exact Binomial(2048, numerator / 2**256) tail."""

    trial_count = 2_048
    denominator = _CP_GRID_DENOMINATOR
    if success_count <= 0:
        return 1
    if success_count > trial_count or numerator == 0:
        return -1
    if numerator == denominator:
        return 1
    complement = denominator - numerator
    threshold = denominator**trial_count
    term = (
        math.comb(trial_count, success_count)
        * numerator**success_count
        * complement ** (trial_count - success_count)
    )
    partial = term
    index = success_count
    while True:
        left = partial * _CP_TAIL_RECIPROCAL
        if left > threshold:
            return 1
        if index == trial_count:
            return (left > threshold) - (left < threshold)
        ratio_numerator = (trial_count - index) * numerator
        ratio_denominator = (index + 1) * complement
        if ratio_numerator < ratio_denominator:
            gap = ratio_denominator - ratio_numerator
            bounded_left = (
                partial * gap + term * ratio_numerator
            ) * _CP_TAIL_RECIPROCAL
            if bounded_left < threshold * gap:
                return -1
        term, remainder = divmod(term * ratio_numerator, ratio_denominator)
        assert remainder == 0
        partial += term
        index += 1


def _certify_independent_cp_interval(
    success_count: int, lower: Fraction, upper: Fraction
) -> None:
    """Certify both outward endpoints by their exact adjacent grid points."""

    assert Fraction(0) <= lower <= upper <= Fraction(1)
    if success_count == 0:
        assert lower == 0
    else:
        scaled_lower = lower * _CP_GRID_DENOMINATOR
        assert scaled_lower.denominator == 1
        lower_numerator = scaled_lower.numerator
        assert _independent_upper_tail_compare(success_count, lower_numerator) < 0
        assert _independent_upper_tail_compare(success_count, lower_numerator + 1) >= 0
    if success_count == 2_048:
        assert upper == 1
    else:
        scaled_complement = (1 - upper) * _CP_GRID_DENOMINATOR
        assert scaled_complement.denominator == 1
        complement_numerator = scaled_complement.numerator
        complement_successes = 2_048 - success_count
        assert (
            _independent_upper_tail_compare(complement_successes, complement_numerator)
            < 0
        )
        assert (
            _independent_upper_tail_compare(
                complement_successes, complement_numerator + 1
            )
            >= 0
        )


_COPRIME_DENOMINATORS = (
    115792089237316195423570985008687907853269984665640564039457584007913129639747,
    115792089237316195423570985008687907853269984665640564039457584007913129639579,
    115792089237316195423570985008687907853269984665640564039457584007913129639501,
    115792089237316195423570985008687907853269984665640564039457584007913129639349,
    115792089237316195423570985008687907853269984665640564039457584007913129639319,
    115792089237316195423570985008687907853269984665640564039457584007913129639013,
    115792089237316195423570985008687907853269984665640564039457584007913129638883,
    115792089237316195423570985008687907853269984665640564039457584007913129638637,
    115792089237316195423570985008687907853269984665640564039457584007913129638397,
    115792089237316195423570985008687907853269984665640564039457584007913129638053,
    115792089237316195423570985008687907853269984665640564039457584007913129637873,
    115792089237316195423570985008687907853269984665640564039457584007913129637179,
    115792089237316195423570985008687907853269984665640564039457584007913129636801,
    115792089237316195423570985008687907853269984665640564039457584007913129636463,
    115792089237316195423570985008687907853269984665640564039457584007913129636031,
    115792089237316195423570985008687907853269984665640564039457584007913129635919,
    115792089237316195423570985008687907853269984665640564039457584007913129635649,
)
_INTERVAL_CROSSING_DENOMINATORS = _COPRIME_DENOMINATORS[:15] + (
    226156424291633194186662080095093570025917938800079226639565593765455331247,
)


def _large_coprime_denominator(index: int) -> int:
    return _COPRIME_DENOMINATORS[index]


def _variant_shape(
    variant: str, seed: int, row: int
) -> Tuple[str, Optional[int], bool, Tuple[Fraction, ...], str]:
    fixture, strategy, budget = _ROW_SHAPES[row - 1]
    cells = _cells(row)
    plan_seed = f"{seed - 1:016x}"

    if variant == "all-selected-duplicate-pairs":
        selected = True
        status = cells[0]
        attempt = (seed - 1) % budget + 1 if strategy == "bounded-rejection" else None
        feature_values = tuple(lower for _name, lower, _upper in _features(fixture))
        plan_seed = f"{(seed - 1) // 2:016x}"
    elif variant == "all-nonselected-cyclic":
        selected = False
        status = cells[1 + (seed - 1) % (len(cells) - 1)]
        attempt = None
        feature_values = ()
    elif variant == "novel-k":
        selected_count = (1, 1_024, 2_047, 777)[(row - 1) % 4]
        selected = seed <= selected_count
        status = cells[0] if selected else cells[1]
        attempt = 1 if selected and strategy == "bounded-rejection" else None
        feature_values = (
            tuple((lower + upper) / 2 for _name, lower, upper in _features(fixture))
            if selected
            else ()
        )
    elif variant in (
        "aggregate-near-cap",
        "aggregate-over-cap",
        "interval-derived-over-cap",
    ):
        limit = 17 if variant == "aggregate-over-cap" else 16
        selected_limit = 1_040 if variant == "interval-derived-over-cap" else limit
        selected = row == 1 and seed <= selected_limit
        status = cells[0] if selected else cells[1]
        attempt = 1 if selected and strategy == "bounded-rejection" else None
        if selected:
            if variant == "interval-derived-over-cap" and seed > 16:
                feature_values = (Fraction(0),) * 6
            else:
                denominator = (
                    _INTERVAL_CROSSING_DENOMINATORS[seed - 1]
                    if variant == "interval-derived-over-cap"
                    else _large_coprime_denominator(seed - 1)
                )
                feature_values = (Fraction(1, denominator),) + (Fraction(0),) * 5
        else:
            feature_values = ()
    else:
        raise AssertionError(f"unknown independent fixture variant: {variant}")
    return status, attempt, selected, feature_values, plan_seed


def _variant_values(
    variant: str,
    seed: int,
    row: int,
    *,
    overrides: Optional[Mapping[str, object]] = None,
) -> dict:
    fixture, strategy, budget = _ROW_SHAPES[row - 1]
    status, attempt, selected, feature_values, plan_seed = _variant_shape(
        variant, seed, row
    )
    logical = (seed - 1) * 16 + row
    feature_ids = (
        tuple(name for name, _lower, _upper in _features(fixture)) if selected else ()
    )
    request_identity = {
        "purpose": "cp71-independent-test-request-custody-sentinel-only",
        "seed_ordinal": seed,
        "row_ordinal": row,
        "logical_request_ordinal": logical,
        "plan_seed_hex": plan_seed,
        "seed_free_request_sha256": _SEED_FREE_SHA256S[row - 1],
    }
    request_sha = _synthetic_sha(
        b"cp71-independent-test-request-instance-custody-sentinel-v1",
        request_identity,
    )
    stable_sha = _synthetic_sha(
        b"cp71-independent-test-no-stable-trace-custody-sentinel-v1",
        {
            "request_instance_sha256": request_sha,
            "observable_cell_label": status,
            "first_selected_attempt_one_based": attempt,
            "selected_feature_values": feature_values,
        },
    )
    values = {
        "schema_version": _CP69_SCHEMA,
        "source_semantic_schema_version": _CP63_COMPACT_SCHEMA,
        "seed_ordinal": seed,
        "row_ordinal": row,
        "logical_request_ordinal": logical,
        "row_key": _row_key(row),
        "fixture_id": fixture,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": plan_seed,
        "seed_free_request_sha256": _SEED_FREE_SHA256S[row - 1],
        "request_instance_sha256": request_sha,
        "runtime_lock_sha256": _RUNTIME_SHA256,
        "stable_trace_sha256": stable_sha,
        "observable_cell_label": status,
        "observable_contribution_ordinal": _observable_ordinal(row, status),
        "first_selected_attempt_one_based": attempt,
        "selected": selected,
        "selected_feature_ids": feature_ids,
        "selected_feature_values": feature_values,
        "record_sha256": _ZERO_SHA256,
    }
    if overrides:
        values.update(overrides)
    values["record_sha256"] = _input_record_sha(values)
    return values


def _variant_bytes(
    variant: str,
    seed: int,
    row: int,
    *,
    overrides: Optional[Mapping[str, object]] = None,
    recompute_digest: bool = True,
) -> bytes:
    values = _variant_values(variant, seed, row, overrides=overrides)
    if not recompute_digest and overrides and "record_sha256" in overrides:
        values["record_sha256"] = overrides["record_sha256"]
    return _canonical(values)


def _qualification_variant_bytes(fixture_id: str, seed: int, row: int) -> bytes:
    fixture, strategy, budget = _ROW_SHAPES[row - 1]
    logical = (seed - 1) * 16 + row
    if fixture_id == "all-selected-duplicate-pair-plan-seeds":
        selected = True
        plan_seed = (seed - 1) // 2
    elif fixture_id == "all-nonselected-cyclic-statuses":
        selected = False
        plan_seed = seed - 1
    elif fixture_id == "novel-k-mixed-selection":
        selected = seed <= (1, 1_024, 2_047, 777)[(row - 1) % 4]
        plan_seed = (1 << 64) - seed
    else:
        raise AssertionError(f"unknown qualification fixture: {fixture_id}")
    cells = _cells(row)
    if selected:
        status = cells[0]
        attempt = (seed - 1) % budget + 1 if strategy == "bounded-rejection" else None
    elif fixture_id == "all-nonselected-cyclic-statuses":
        status = cells[1 + (seed - 1) % (len(cells) - 1)]
        attempt = None
    else:
        status = cells[1]
        attempt = None
    plan_seed_hex = f"{plan_seed:016x}"
    request_sha = _synthetic_sha(
        b"cp71-test28-qualification-request-instance-sentinel-v1",
        {
            "fixture_id": fixture_id,
            "seed_ordinal": seed,
            "row_ordinal": row,
            "logical_request_ordinal": logical,
            "plan_seed_hex": plan_seed_hex,
        },
    )
    stable_sha = _synthetic_sha(
        b"cp71-test28-qualification-no-stable-trace-sentinel-v1",
        {
            "fixture_id": fixture_id,
            "request_instance_sha256": request_sha,
            "observable_cell_label": status,
            "first_selected_attempt_one_based": attempt,
        },
    )
    feature_ids = (
        tuple(name for name, _lower, _upper in _features(fixture)) if selected else ()
    )
    feature_values = (
        tuple(
            Fraction(((seed + index) % 33) - 16, 16)
            if lower == -1
            else Fraction((seed + index) % 17, 16)
            for index, (_name, lower, _upper) in enumerate(_features(fixture))
        )
        if selected
        else ()
    )
    values = {
        "schema_version": _CP69_SCHEMA,
        "source_semantic_schema_version": _CP63_COMPACT_SCHEMA,
        "seed_ordinal": seed,
        "row_ordinal": row,
        "logical_request_ordinal": logical,
        "row_key": _row_key(row),
        "fixture_id": fixture,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": plan_seed_hex,
        "seed_free_request_sha256": _SEED_FREE_SHA256S[row - 1],
        "request_instance_sha256": request_sha,
        "runtime_lock_sha256": _RUNTIME_SHA256,
        "stable_trace_sha256": stable_sha,
        "observable_cell_label": status,
        "observable_contribution_ordinal": _observable_ordinal(row, status),
        "first_selected_attempt_one_based": attempt,
        "selected": selected,
        "selected_feature_ids": feature_ids,
        "selected_feature_values": feature_values,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _input_record_sha(values)
    return _canonical(values)


def _iter_independent_variant(variant: str) -> Iterator[bytes]:
    for seed in range(1, _SEED_COUNT + 1):
        for row in range(1, _ROW_COUNT + 1):
            yield _variant_bytes(variant, seed, row)


def _iter_qualification_variant(fixture_id: str) -> Iterator[bytes]:
    for seed in range(1, _SEED_COUNT + 1):
        for row in range(1, _ROW_COUNT + 1):
            yield _qualification_variant_bytes(fixture_id, seed, row)


def _iter_baseline() -> Iterator[bytes]:
    # The CP69-owned byte fixture is used only as an immutable predecessor anchor.
    from heterodiff.evaluation import (
        mixed_initializer_test28_compact_projection_interchange_qualification as cp69,
    )

    yield from cp69._iter_closed_interchange_bytes()


def _iter_variant(variant: str) -> Iterator[bytes]:
    if variant == "baseline":
        yield from _iter_baseline()
    elif variant in (
        "all-selected-duplicate-pair-plan-seeds",
        "all-nonselected-cyclic-statuses",
        "novel-k-mixed-selection",
    ):
        yield from _iter_qualification_variant(variant)
    else:
        yield from _iter_independent_variant(variant)


def _decoded_input(payload: bytes) -> dict:
    raw = _decode_payload(payload)
    result = dict(raw)
    result["selected_feature_ids"] = tuple(result["selected_feature_ids"])
    result["selected_feature_values"] = tuple(
        cast(Fraction, _fraction(item)) for item in result["selected_feature_values"]
    )
    return result


@lru_cache(maxsize=None)
def _oracle_details(variant: str) -> dict:
    observable = {(row, cell): 0 for row in range(1, 17) for cell in _cells(row)}
    first = {
        (row, attempt): 0
        for row, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1)
        if strategy == "bounded-rejection"
        for attempt in range(1, budget + 1)
    }
    sums = {
        (row, name): Fraction(0)
        for row, (fixture, _strategy, _budget) in enumerate(_ROW_SHAPES, 1)
        for name, _lower, _upper in _features(fixture)
    }
    selected = [0] * 16
    statuses = {
        "rejection-selected": 0,
        "rejection-exhausted": 0,
        "sir-selected": 0,
        "refusal": 0,
        "failure": 0,
        "timeout": 0,
    }
    ordered_input = hashlib.sha256(_ORDERED_INPUT_DOMAIN + b"\0")
    ordered_projection = hashlib.sha256(_ORDERED_PROJECTION_DOMAIN + b"\0")
    total_bytes = 0
    first_sha = None
    first_contributions = 0
    feature_contributions = 0
    plan_by_seed: Dict[int, str] = {}
    request_digests: List[str] = []
    stable_digests: List[str] = []
    for payload in _iter_variant(variant):
        value = _decoded_input(payload)
        total_bytes += len(payload)
        record_sha = cast(str, value["record_sha256"])
        if first_sha is None:
            first_sha = record_sha
        ordered_input.update(bytes.fromhex(record_sha))
        ordered_projection.update(bytes.fromhex(_projection_sha(value)))
        seed = cast(int, value["seed_ordinal"])
        row = cast(int, value["row_ordinal"])
        plan_by_seed.setdefault(seed, cast(str, value["plan_seed_hex"]))
        assert plan_by_seed[seed] == value["plan_seed_hex"]
        request_digests.append(cast(str, value["request_instance_sha256"]))
        stable_digests.append(cast(str, value["stable_trace_sha256"]))
        status = cast(str, value["observable_cell_label"])
        observable[(row, status)] += 1
        if status == _REJECTION_CELLS[0]:
            statuses["rejection-selected"] += 1
        elif status == _REJECTION_CELLS[1]:
            statuses["rejection-exhausted"] += 1
        elif status == _SIR_CELLS[0]:
            statuses["sir-selected"] += 1
        elif status == "preexecution-refusal-before-deadline":
            statuses["refusal"] += 1
        elif status == "execution-failure-before-deadline":
            statuses["failure"] += 1
        elif status == "timeout-censored-at-deadline":
            statuses["timeout"] += 1
        attempt = value["first_selected_attempt_one_based"]
        if attempt is not None:
            first[(row, cast(int, attempt))] += 1
            first_contributions += 1
        if value["selected"]:
            selected[row - 1] += 1
            for name, fraction in zip(
                value["selected_feature_ids"], value["selected_feature_values"]
            ):
                sums[(row, cast(str, name))] += cast(Fraction, fraction)
                feature_contributions += 1
    seed_plan = hashlib.sha256(b"cp71-test28-ordered-seed-ordinal-plan-seed-v1\0")
    for seed in range(1, 2_049):
        seed_plan.update(seed.to_bytes(2, "big"))
        seed_plan.update(bytes.fromhex(plan_by_seed[seed]))
    request_ordered = hashlib.sha256(
        b"cp71-test28-ordered-request-instance-digests-v1\0"
    )
    stable_ordered = hashlib.sha256(b"cp71-test28-ordered-stable-trace-digests-v1\0")
    for digest in request_digests:
        request_ordered.update(bytes.fromhex(digest))
    for digest in stable_digests:
        stable_ordered.update(bytes.fromhex(digest))
    details = {
        "observable": observable,
        "first": first,
        "feature_sums": sums,
        "selected": tuple(selected),
        "statuses": statuses,
        "total_bytes": total_bytes,
        "first_sha": first_sha,
        "ordered_input": ordered_input.hexdigest(),
        "ordered_projection": ordered_projection.hexdigest(),
        "ordered_seed_plan": seed_plan.hexdigest(),
        "ordered_request": request_ordered.hexdigest(),
        "ordered_stable": stable_ordered.hexdigest(),
        "first_contributions": first_contributions,
        "feature_contributions": feature_contributions,
        "updates": _REQUEST_COUNT + first_contributions + feature_contributions,
        "distinct_plan_count": len(set(plan_by_seed.values())),
        "duplicate_plan_count": _SEED_COUNT - len(set(plan_by_seed.values())),
    }
    commitment_body = {
        "request_count": _REQUEST_COUNT,
        "total_input_bytes": total_bytes,
        "ordered_interchange_record_sha256": details["ordered_input"],
        "ordered_projection_sha256": details["ordered_projection"],
        "ordered_seed_ordinal_plan_seed_sha256": details["ordered_seed_plan"],
        "ordered_request_instance_sha256": details["ordered_request"],
        "ordered_stable_trace_sha256": details["ordered_stable"],
        "runtime_lock_sha256": _RUNTIME_SHA256,
    }
    details["commitment"] = _sha(_STREAM_COMMITMENT_DOMAIN, commitment_body)
    return details


@lru_cache(maxsize=None)
def _reduction(variant: str) -> Tuple[bytes, object]:
    return cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
        _iter_variant(variant)
    )


def _error_code(callable_object: Callable[[], object], expected: str) -> None:
    with pytest.raises(
        cp71.CP71SuppliedInterchangeRecomputationQualificationError
    ) as caught:
        callable_object()
    assert caught.value.code == "CP71_" + expected
    assert str(caught.value)


def _one_then_stop(payload: object) -> Iterator[object]:
    yield payload


def _mutated_first(
    *,
    overrides: Optional[Mapping[str, object]] = None,
    raw_payload: Optional[object] = None,
    recompute_digest: bool = True,
) -> Iterator[object]:
    if raw_payload is not None:
        yield raw_payload
        return
    yield _variant_bytes(
        "all-nonselected-cyclic",
        1,
        1,
        overrides=overrides,
        recompute_digest=recompute_digest,
    )


def _bundle() -> object:
    return cp71.cp71_supplied_interchange_recomputation_qualification_bundle()


def _contract() -> object:
    return _bundle().supplied_interchange_stream_contract


def _output_contract() -> object:
    return _bundle().development_estimate_interval_output_contract


def _hostile_limits(**overrides: int) -> dict:
    limits = {
        "maximum_interchange_bytes": 65_536,
        "maximum_stream_bytes": 268_435_456,
        "maximum_input_depth": 16,
        "maximum_input_nodes": 512,
        "maximum_input_text_bytes": 4_096,
        "maximum_input_integer_decimal_digits": 80,
        "maximum_input_integer_bits": 256,
        "maximum_aggregate_integer_bits": 4_096,
        "maximum_output_record_bytes": 65_536,
        "maximum_output_bytes": 8_388_608,
    }
    assert set(overrides).issubset(limits)
    limits.update(overrides)
    return limits


def test_cp71_public_constants_pin_resources_arithmetic_and_failure_order() -> None:
    assert cp71.CP71_TEST28_SCHEMA_VERSION == (
        "cp71-test28-supplied-interchange-recomputation-qualification-v1"
    )
    assert cp71.CP71_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert cp71.CP71_TEST28_SEED_COUNT == 2_048
    assert cp71.CP71_TEST28_ROW_COUNT == 16
    assert cp71.CP71_TEST28_REQUEST_COUNT == 32_768
    assert cp71.CP71_TEST28_ESTIMAND_COUNT == 554
    assert cp71.CP71_TEST28_OBSERVABLE_ESTIMAND_COUNT == 72
    assert cp71.CP71_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT == 170
    assert cp71.CP71_TEST28_FEATURE_ESTIMAND_COUNT == 312
    assert cp71.CP71_TEST28_BINOMIAL_ESTIMAND_COUNT == 242
    assert cp71.CP71_TEST28_FAMILYWISE_ERROR_BUDGET == Fraction(1, 100)
    assert cp71.CP71_TEST28_PER_ESTIMATOR_ERROR_BUDGET == Fraction(1, 55_400)
    assert cp71.CP71_TEST28_PER_TAIL_ERROR_BUDGET == Fraction(1, 110_800)
    assert cp71.CP71_TEST28_CP_BISECTION_STEPS == 256
    assert cp71.CP71_TEST28_MINIMUM_SELECTED_COUNT == 1_040
    assert cp71.CP71_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER == Fraction(3, 40)
    assert cp71.CP71_TEST28_MAXIMUM_INTERCHANGE_BYTES == 65_536
    assert cp71.CP71_TEST28_MAXIMUM_STREAM_BYTES == 268_435_456
    assert cp71.CP71_TEST28_MAXIMUM_INPUT_DEPTH == 16
    assert cp71.CP71_TEST28_MAXIMUM_INPUT_NODES == 512
    assert cp71.CP71_TEST28_MAXIMUM_INPUT_TEXT_BYTES == 4_096
    assert cp71.CP71_TEST28_MAXIMUM_INPUT_INTEGER_DECIMAL_DIGITS == 80
    assert cp71.CP71_TEST28_MAXIMUM_INPUT_INTEGER_BITS == 256
    assert cp71.CP71_TEST28_MAXIMUM_AGGREGATE_INTEGER_BITS == 4_096
    assert cp71.CP71_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES == 65_536
    assert cp71.CP71_TEST28_MAXIMUM_OUTPUT_BYTES == 8_388_608
    assert cp71.CP71_TEST28_MAXIMUM_SEALED_RECORD_BYTES == 1_048_576
    assert cp71.CP71_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT == 2_049
    assert cp71.CP71_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY == 554
    assert cp71.CP71_TEST28_STATUS_ORDER == (
        "rejection-selected",
        "rejection-exhausted",
        "sir-selected",
        "refusal",
        "failure",
        "timeout",
    )
    assert cp71.CP71_TEST28_ERROR_CODES == _ERROR_CODES


def test_cp71_six_sealed_record_field_orders_are_exact() -> None:
    bundle = _bundle()
    qualification = cp71.cp71_run_supplied_interchange_recomputation_qualification()
    assert bundle.record_sha256 == (
        "c49b4396c06f1ff792d2860176a2e318612bd12ad89ba3cf6f8804e2dc82169f"
    )
    assert len(cp71.cp71_canonical_json_bytes(bundle)) == 14_130
    assert cp71.cp71_sha256(bundle) == (
        "bc387799a9b4bbec015ac20b1a05ab3ac4d355e6542de405e000c8db42c801fd"
    )
    assert qualification.record_sha256 == (
        "aa25726473f54c17b3179ebabbaace3671e9815a6d3b4eec834ad6c1b8490611"
    )
    assert len(cp71.cp71_canonical_json_bytes(qualification)) == 3_305
    assert cp71.cp71_sha256(qualification) == (
        "ec2f8a1f4567bc7e1cb800f1e4c48f8f4b41c09212ea6550042b1e358cc1b92f"
    )
    summary = _reduction("novel-k")[1]
    records = (
        bundle.predecessor_custody,
        bundle.supplied_interchange_stream_contract,
        bundle.development_estimate_interval_output_contract,
        summary,
        qualification,
        bundle,
    )
    assert {type(record).__name__ for record in records} == set(_RECORD_FIELDS)
    record_domains = {
        "CP71PredecessorCustodyV1": b"cp71-test28-predecessor-custody-v1",
        "CP71SuppliedInterchangeStreamContractV1": (
            b"cp71-test28-supplied-interchange-stream-contract-v1"
        ),
        "CP71DevelopmentEstimateIntervalOutputContractV1": (
            b"cp71-test28-development-estimate-interval-output-contract-v1"
        ),
        "CP71SuppliedDevelopmentReductionSummaryV1": (
            b"cp71-test28-supplied-development-reduction-summary-v1"
        ),
        "CP71SuppliedInterchangeRecomputationQualificationV1": (
            b"cp71-test28-supplied-interchange-recomputation-qualification-v1"
        ),
        "CP71SuppliedInterchangeRecomputationQualificationBundleV1": (
            b"cp71-test28-supplied-interchange-recomputation-qualification-bundle-v1"
        ),
    }
    for record in records:
        class_name = type(record).__name__
        expected = _RECORD_FIELDS[class_name]
        assert tuple(item.name for item in fields(type(record))) == expected
        assert type(record).__slots__ == expected
        body = {item.name: getattr(record, item.name) for item in fields(type(record))}
        supplied = body["record_sha256"]
        body["record_sha256"] = _ZERO_SHA256
        assert supplied == _sha(record_domains[class_name], body)
        snapshot = cp71.cp71_canonical_json_bytes(record)
        assert (
            cp71.cp71_sha256(record)
            == hashlib.sha256(
                b"cp71-public-record-v1\0"
                + class_name.encode("ascii")
                + b"\0"
                + snapshot
            ).hexdigest()
        )


def test_cp71_contract_freezes_exact_input_grammar_and_resource_caps() -> None:
    contract = _contract()
    assert contract.exact_input_keys == _INPUT_KEYS
    assert contract.source_interchange_schema_version == _CP69_SCHEMA
    assert contract.source_semantic_schema_version == _CP63_COMPACT_SCHEMA
    assert contract.seed_count == 2_048
    assert contract.row_count == 16
    assert contract.request_count == 32_768
    assert contract.logical_request_order == "seed-major-row-minor"
    assert contract.logical_request_ordinal_formula == "(seed_ordinal-1)*16+row_ordinal"
    assert contract.interchange_record_digest_domain == _INPUT_RECORD_DOMAIN.decode(
        "ascii"
    )
    assert contract.projection_digest_domain == (
        "record="
        + _PROJECTION_DOMAIN.decode("ascii")
        + ";ordered="
        + _ORDERED_PROJECTION_DOMAIN.decode("ascii")
    )
    assert contract.same_plan_seed_across_row_group_required is True
    assert contract.duplicate_plan_seed_values_across_seed_ordinals_allowed is True
    assert contract.exact_row_specific_seed_free_request_sha256s == _SEED_FREE_SHA256S
    assert contract.single_stream_runtime_lock_sha256_required is True
    assert contract.runtime_lock_authenticated is False
    assert contract.request_instance_sha256_authenticated is False
    assert contract.stable_trace_sha256_authenticated is False
    assert contract.source_provenance_authenticated is False
    assert contract.maximum_next_calls == 32_769
    assert contract.maximum_interchange_bytes == 65_536
    assert contract.maximum_stream_bytes == 268_435_456
    assert contract.maximum_input_depth == 16
    assert contract.maximum_input_nodes == 512
    assert contract.maximum_input_text_bytes == 4_096
    assert contract.maximum_input_integer_decimal_digits == 80
    assert contract.maximum_input_integer_bits == 256
    assert contract.maximum_aggregate_integer_bits == 4_096


def test_cp71_output_contract_is_dynamic_and_decision_free() -> None:
    contract = _output_contract()
    assert contract.record_sha256 == (
        "13a76a7ce7b0c665ef33aa6e55c122c87bf61aa676530c984ce2fdaf63e345a3"
    )
    assert len(cp71.cp71_canonical_json_bytes(contract)) == 4_186
    assert cp71.cp71_sha256(contract) == (
        "117cc10b89332309e0108f8231941c4b2cb34aac5f3e0f56159fe528553e7bcb"
    )
    assert contract.exact_output_root_keys == _ROOT_KEYS
    assert contract.exact_estimand_record_keys == _OUTPUT_RECORD_KEYS
    assert contract.estimand_count == 554
    assert contract.binomial_estimand_count == 242
    assert contract.feature_estimand_count == 312
    assert contract.numeric_estimand_arithmetic_compatible_with_cp68 is True
    assert contract.cp61_estimand_digest_is_inventory_reference_only is True
    assert contract.cp61_estimand_semantics_realized is False
    assert contract.output_schema_version == (
        "cp71-test28-supplied-development-estimate-interval-output-v1"
    )
    assert contract.input_stream_classification == (
        "caller-supplied-cp69-valid-and-cp71-resource-bounded-development-byte-stream"
    )
    assert contract.cp68_closed_fixture_set_sha256_field_present is False
    assert contract.dynamic_input_stream_commitment_required is True
    assert contract.all_success_counts_admitted is True
    assert contract.precomputed_closed_endpoint_table_required is False
    assert contract.minimum_selected_count == 1_040
    assert contract.feature_halfwidth_range_multiplier == Fraction(3, 40)
    assert contract.primary_thresholds_present is False
    assert contract.decision_fields_present is False
    assert contract.iid_source_law_or_coverage_claimed is False
    assert contract.production_attempt_validity_evaluated is False
    assert contract.estimand_record_digest_domain == _OUTPUT_RECORD_DOMAIN.decode(
        "ascii"
    )
    assert contract.ordered_estimand_digest_domain == (
        "cp71-test28-ordered-estimand-record-digests-v1"
    )
    assert contract.ordered_seed_plan_digest_domain == (
        "cp71-test28-ordered-seed-ordinal-plan-seed-v1"
    )
    assert contract.ordered_request_instance_digest_domain == (
        "cp71-test28-ordered-request-instance-digests-v1"
    )
    assert contract.ordered_stable_trace_digest_domain == (
        "cp71-test28-ordered-stable-trace-digests-v1"
    )
    assert contract.stream_commitment_digest_domain == _STREAM_COMMITMENT_DOMAIN.decode(
        "ascii"
    )
    assert contract.output_body_digest_domain == _OUTPUT_BODY_DOMAIN.decode("ascii")
    assert contract.maximum_aggregate_integer_bits == 4_096
    assert contract.maximum_output_record_bytes == 65_536
    assert contract.maximum_output_bytes == 8_388_608


@pytest.mark.parametrize(
    "variant,selected,statuses,updates,distinct,duplicates",
    (
        (
            "all-selected-duplicate-pairs",
            (2_048,) * 16,
            (16_384, 0, 16_384, 0, 0, 0),
            688_128,
            1_024,
            1_024,
        ),
        (
            "all-nonselected-cyclic",
            (0,) * 16,
            (0, 4_096, 0, 9_560, 9_560, 9_552),
            32_768,
            2_048,
            0,
        ),
        (
            "novel-k",
            (1, 1_024, 2_047, 777) * 4,
            (7_698, 8_686, 7_698, 8_686, 0, 0),
            340_688,
            2_048,
            0,
        ),
    ),
)
def test_cp71_dynamic_full_stream_summaries(
    variant: str,
    selected: Tuple[int, ...],
    statuses: Tuple[int, ...],
    updates: int,
    distinct: int,
    duplicates: int,
) -> None:
    payload, summary = _reduction(variant)
    oracle = _oracle_details(variant)
    assert type(payload) is bytes and payload
    assert summary.request_count == 32_768
    assert summary.total_input_bytes == oracle["total_bytes"]
    assert summary.selected_counts_by_row == selected == oracle["selected"]
    assert summary.status_counts == statuses == tuple(oracle["statuses"].values())
    assert summary.aggregation_update_count == updates == oracle["updates"]
    assert summary.distinct_plan_seed_count == distinct
    assert summary.duplicate_plan_seed_count == duplicates
    assert summary.input_stream_commitment_sha256 == oracle["commitment"]
    assert summary.ordered_interchange_record_sha256 == oracle["ordered_input"]
    assert summary.ordered_projection_sha256 == oracle["ordered_projection"]
    assert summary.ordered_seed_ordinal_plan_seed_sha256 == oracle["ordered_seed_plan"]
    assert summary.ordered_request_instance_sha256 == oracle["ordered_request"]
    assert summary.ordered_stable_trace_sha256 == oracle["ordered_stable"]
    assert summary.runtime_lock_sha256 == _RUNTIME_SHA256


def test_cp71_novel_k_fixture_exercises_counts_absent_from_cp70_table() -> None:
    payload, summary = _reduction("novel-k")
    assert summary.distinct_cp_success_count_count == 6
    decoded = _decode_payload(payload)
    records = decoded["estimand_estimate_intervals"]
    observed = {
        record["success_count"]
        for record in records
        if record["estimand_family"]
        in (
            "observable-cell",
            "rejection-first-attempt",
        )
    }
    assert {1, 777, 1_024, 1_271, 2_047}.issubset(observed)


def test_cp71_baseline_reproduces_cp70_scientific_record_vector() -> None:
    from heterodiff.evaluation import (
        mixed_initializer_test28_estimate_interval_output_validation_qualification as cp70,
    )

    payload, summary = _reduction("baseline")
    decoded = _decode_payload(payload)
    oracle = _oracle_details("baseline")
    assert summary.ordered_interchange_record_sha256 == (
        "754b058697dc9324611152b4987925a414520fc98dd764571321c3135d0ecc8d"
    )
    assert summary.ordered_projection_sha256 == oracle["ordered_projection"]
    cp68_payload = cp70._closed_expected_output()[0]
    assert hashlib.sha256(cp68_payload).hexdigest() == (
        "f9e1bf93354af057d08ca722d2cffe1a8188d2f1e823a0173f9b6a937ddc42c3"
    )
    cp68_records = _decode_payload(cp68_payload)["estimand_estimate_intervals"]
    cp71_records = decoded["estimand_estimate_intervals"]
    scientific_keys = tuple(
        name for name in _OUTPUT_RECORD_KEYS[1:23] if name != "denominator_mode"
    )
    assert len(cp71_records) == len(cp68_records) == 554
    assert tuple(
        tuple(record[name] for name in scientific_keys) for record in cp71_records
    ) == tuple(
        tuple(record[name] for name in scientific_keys) for record in cp68_records
    )
    for cp71_record, cp68_record in zip(cp71_records, cp68_records):
        if cp71_record["estimand_family"] in (
            "observable-cell",
            "rejection-first-attempt",
        ):
            assert cp71_record["denominator_mode"] == (
                "all-2048-supplied-seed-ordinal-groups"
            )
            assert cp68_record["denominator_mode"] == (
                "all-2048-external-seed-ordinals"
            )
        else:
            assert cp71_record["denominator_mode"] == cp68_record["denominator_mode"]
    assert summary.selected_counts_by_row == (
        2_048,
        1_040,
        1_039,
        0,
        2_048,
        1_040,
        1_039,
        0,
        0,
        1_039,
        1_040,
        2_048,
        0,
        1_039,
        1_040,
        2_048,
    )


def test_cp71_output_root_binds_dynamic_stream_and_nonclaims() -> None:
    payload, summary = _reduction("novel-k")
    root = _decode_payload(payload)
    assert set(root) == set(_ROOT_KEYS)
    assert (
        root["input_stream_commitment_sha256"] == summary.input_stream_commitment_sha256
    )
    assert (
        root["ordered_interchange_record_sha256"]
        == summary.ordered_interchange_record_sha256
    )
    assert root["ordered_projection_sha256"] == summary.ordered_projection_sha256
    assert root["ordered_seed_ordinal_plan_seed_sha256"] == (
        summary.ordered_seed_ordinal_plan_seed_sha256
    )
    assert (
        root["ordered_request_instance_sha256"]
        == summary.ordered_request_instance_sha256
    )
    assert root["ordered_stable_trace_sha256"] == summary.ordered_stable_trace_sha256
    assert root["runtime_lock_sha256"] == _RUNTIME_SHA256
    assert root["input_provenance_authenticated"] is False
    assert root["source_law_verified"] is False
    assert root["external_seed_source_verified"] is False
    assert root["runtime_lock_authenticated"] is False
    assert root["request_instance_sha256_authenticated"] is False
    assert root["stable_trace_sha256_authenticated"] is False
    assert root["cp61_estimand_digest_is_inventory_reference_only"] is True
    assert root["cp61_estimand_semantics_realized"] is False
    assert root["production_attempt_validity_evaluated"] is False
    assert root["production_recomputation"] is False
    assert root["arithmetic_transform_only"] is True
    assert "fixture_set_sha256" not in root
    assert "decision" not in root


def test_cp71_opaque_request_and_stable_digests_bind_but_do_not_authenticate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def source() -> Iterator[bytes]:
        for seed in range(1, _SEED_COUNT + 1):
            for row in range(1, _ROW_COUNT + 1):
                overrides = (
                    {
                        "request_instance_sha256": "a" * 64,
                        "stable_trace_sha256": "b" * 64,
                    }
                    if (seed, row) == (1, 1)
                    else None
                )
                yield _variant_bytes(
                    "all-nonselected-cyclic", seed, row, overrides=overrides
                )

    ordinary_payload, ordinary_summary = _reduction("all-nonselected-cyclic")
    real_sha256 = hashlib.sha256
    real_details = cp71._reduce_supplied_cp69_interchange_byte_stream_details
    captured_metrics: Dict[str, object] = {}

    def domain_guard(payload: bytes = b"") -> object:
        assert not payload.startswith(b"cp68-test28-synthetic-compact-projection-v1")
        assert not payload.startswith(b"cp68-test28-ordered-projection-digests-v1")
        return real_sha256(payload)

    def capture(payloads: object, *, limits: object = None) -> dict:
        result = real_details(payloads, limits=limits)
        captured_metrics.update(result)
        return result

    monkeypatch.setattr(cp71.hashlib, "sha256", domain_guard)
    monkeypatch.setattr(
        cp71, "_reduce_supplied_cp69_interchange_byte_stream_details", capture
    )
    (
        supplied_payload,
        supplied_summary,
    ) = cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(source())
    assert not any("cp68" in name.lower() for name in captured_metrics)
    ordinary = _decode_payload(ordinary_payload)
    supplied = _decode_payload(supplied_payload)
    assert (
        supplied["estimand_estimate_intervals"]
        == ordinary["estimand_estimate_intervals"]
    )
    assert supplied_summary.ordered_projection_sha256 == (
        ordinary_summary.ordered_projection_sha256
    )
    assert supplied_summary.runtime_lock_sha256 == ordinary_summary.runtime_lock_sha256
    assert supplied_summary.ordered_interchange_record_sha256 != (
        ordinary_summary.ordered_interchange_record_sha256
    )
    assert supplied_summary.ordered_request_instance_sha256 != (
        ordinary_summary.ordered_request_instance_sha256
    )
    assert supplied_summary.ordered_stable_trace_sha256 != (
        ordinary_summary.ordered_stable_trace_sha256
    )
    assert supplied_summary.input_stream_commitment_sha256 != (
        ordinary_summary.input_stream_commitment_sha256
    )
    assert supplied["input_provenance_authenticated"] is False


def test_cp71_summary_output_hashes_and_body_domain_are_independent() -> None:
    payload, summary = _reduction("novel-k")
    assert summary.output_canonical_json_bytes == len(payload)
    assert summary.output_canonical_json_sha256 == hashlib.sha256(payload).hexdigest()
    assert (
        summary.output_body_sha256
        == hashlib.sha256(_OUTPUT_BODY_DOMAIN + b"\0" + payload).hexdigest()
    )


def test_cp71_every_output_record_has_valid_cp71_digest_and_nonclaims() -> None:
    payload, summary = _reduction("novel-k")
    root = _decode_payload(payload)
    records = root["estimand_estimate_intervals"]
    ordered = hashlib.sha256(
        _output_contract().ordered_estimand_digest_domain.encode("ascii") + b"\0"
    )
    assert len(records) == 554
    for ordinal, record in enumerate(records, 1):
        assert set(record) == set(_OUTPUT_RECORD_KEYS)
        assert record["estimand_ordinal"] == ordinal
        assert record["development_supplied_input_only"] is True
        assert record["input_provenance_authenticated"] is False
        assert record["arithmetic_transform_only"] is True
        body = dict(record)
        supplied = body["record_sha256"]
        body["record_sha256"] = _ZERO_SHA256
        assert supplied == _sha(_OUTPUT_RECORD_DOMAIN, body)
        ordered.update(bytes.fromhex(supplied))
    assert ordered.hexdigest() == summary.ordered_estimand_record_sha256s_sha256


def test_cp71_output_records_match_cp61_inventory_and_exact_arithmetic() -> None:
    from heterodiff.evaluation import (
        mixed_initializer_test28_whole_seed_mc_design as cp61,
    )

    payload, summary = _reduction("novel-k")
    oracle = _oracle_details("novel-k")
    records = _decode_payload(payload)["estimand_estimate_intervals"]
    design = cp61.cp61_whole_seed_mc_design_bundle()
    specs = (
        design.observable_estimands
        + design.rejection_first_attempt_estimands
        + design.selected_conditional_feature_estimands
    )
    assert len(specs) == len(records) == 554
    for spec, record in zip(specs, records):
        assert record["estimand_ordinal"] == spec.estimand_ordinal
        assert record["estimand_id"] == spec.estimand_id
        assert record["cp61_estimand_record_sha256"] == spec.record_sha256
        for name in (
            "estimand_family",
            "row_ordinal",
            "fixture_id",
            "strategy",
            "budget",
            "observable_cell_label",
            "first_attempt_one_based",
            "feature_id",
        ):
            assert record[name] == getattr(spec, name)
        expected_denominator_mode = (
            "all-2048-supplied-seed-ordinal-groups"
            if spec.estimand_family in ("observable-cell", "rejection-first-attempt")
            else spec.denominator_mode
        )
        assert record["denominator_mode"] == expected_denominator_mode
        assert _fraction(record["feature_lower_bound"]) == spec.feature_lower_bound
        assert _fraction(record["feature_upper_bound"]) == spec.feature_upper_bound
        row = spec.row_ordinal
        if spec.estimand_family == "observable-cell":
            success = oracle["observable"][(row, spec.observable_cell_label)]
            denominator = 2_048
            total = None
        elif spec.estimand_family == "rejection-first-attempt":
            success = oracle["first"][(row, spec.first_attempt_one_based)]
            denominator = 2_048
            total = None
        else:
            success = None
            denominator = oracle["selected"][row - 1]
            total = oracle["feature_sums"][(row, spec.feature_id)]
        assert record["success_count"] == success
        assert record["denominator_count"] == denominator
        if spec.estimand_family != "selected-conditional-feature":
            assert _fraction(record["exact_feature_sum"]) is None
            assert _fraction(record["estimate"]) == Fraction(success, denominator)
            interval_lower = cast(Fraction, _fraction(record["interval_lower"]))
            interval_upper = cast(Fraction, _fraction(record["interval_upper"]))
            _certify_independent_cp_interval(
                cast(int, success), interval_lower, interval_upper
            )
            assert record["interval_state"] == "computed"
        elif denominator == 0:
            assert _fraction(record["exact_feature_sum"]) is None
            assert _fraction(record["estimate"]) is None
            assert _fraction(record["interval_lower"]) is None
            assert _fraction(record["interval_upper"]) is None
            assert record["interval_state"] == "insufficient-selection"
        else:
            estimate = total / denominator
            assert _fraction(record["exact_feature_sum"]) == total
            assert _fraction(record["estimate"]) == estimate
            if denominator < 1_040:
                assert _fraction(record["interval_lower"]) is None
                assert _fraction(record["interval_upper"]) is None
                assert record["interval_state"] == "insufficient-selection"
            else:
                halfwidth = (
                    spec.feature_upper_bound - spec.feature_lower_bound
                ) * Fraction(3, 40)
                assert _fraction(record["interval_lower"]) == max(
                    spec.feature_lower_bound, estimate - halfwidth
                )
                assert _fraction(record["interval_upper"]) == min(
                    spec.feature_upper_bound, estimate + halfwidth
                )
                assert record["interval_state"] == "computed"


def test_cp71_untrusted_cp_candidate_never_decides_an_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    success_counts = (1, 777, 1_024, 2_047, 2_048)
    reference = {
        success: cp71._cp71_cp_interval(success, {}, [0]) for success in success_counts
    }
    for proposed in (None, -(1 << 2_048), 1 << 2_048):
        with monkeypatch.context() as guarded:
            guarded.setattr(
                cp71,
                "_cp71_approximate_lower_numerator",
                lambda _success, proposed=proposed: proposed,
            )
            for success in success_counts:
                comparisons = [0]
                actual = cp71._cp71_cp_interval(success, {}, comparisons)
                assert actual == reference[success]
                _certify_independent_cp_interval(success, actual[0], actual[1])
                assert comparisons[0] in (2, 4)


def test_cp71_novel_k_feature_state_counts_cover_positive_below_threshold() -> None:
    payload, summary = _reduction("novel-k")
    records = _decode_payload(payload)["estimand_estimate_intervals"]
    feature_records = [
        record
        for record in records
        if record["estimand_family"] == "selected-conditional-feature"
    ]
    assert summary.feature_estimate_present_count == 312
    assert summary.feature_estimate_absent_count == 0
    assert summary.feature_interval_count == 78
    assert summary.computed_interval_count == 242 + 78
    assert summary.insufficient_selection_count == 234
    assert any(
        record["denominator_count"] == 1
        and record["estimate"] is not None
        and record["interval_lower"] is None
        for record in feature_records
    )


def test_cp71_all_nonselected_has_no_feature_sums_or_estimates() -> None:
    payload, summary = _reduction("all-nonselected-cyclic")
    records = _decode_payload(payload)["estimand_estimate_intervals"]
    feature_records = [
        record
        for record in records
        if record["estimand_family"] == "selected-conditional-feature"
    ]
    assert summary.feature_estimate_present_count == 0
    assert summary.feature_estimate_absent_count == 312
    assert summary.feature_interval_count == 0
    assert summary.computed_interval_count == 242
    assert summary.insufficient_selection_count == 312
    assert all(record["exact_feature_sum"] is None for record in feature_records)
    assert all(record["estimate"] is None for record in feature_records)


def test_cp71_all_selected_clips_every_feature_interval_at_lower_bound() -> None:
    payload, summary = _reduction("all-selected-duplicate-pairs")
    records = _decode_payload(payload)["estimand_estimate_intervals"]
    feature_records = [
        record
        for record in records
        if record["estimand_family"] == "selected-conditional-feature"
    ]
    assert summary.feature_interval_count == 312
    assert summary.computed_interval_count == 554
    assert summary.insufficient_selection_count == 0
    for record in feature_records:
        lower = cast(Fraction, _fraction(record["feature_lower_bound"]))
        upper = cast(Fraction, _fraction(record["feature_upper_bound"]))
        assert _fraction(record["estimate"]) == lower
        assert _fraction(record["interval_lower"]) == lower
        assert _fraction(record["interval_upper"]) == lower + (
            upper - lower
        ) * Fraction(3, 40)


@pytest.mark.parametrize(
    "raw_payload,code",
    (
        (bytearray(b"{}"), "INPUT_TYPE_MISMATCH"),
        (memoryview(b"{}"), "INPUT_TYPE_MISMATCH"),
        (b"", "INPUT_BYTE_LIMIT"),
        (b"\xef\xbb\xbf{}", "INPUT_ENCODING_INVALID"),
        (b"\xff", "INPUT_ENCODING_INVALID"),
        (b"{", "INPUT_JSON_INVALID"),
        (b'{"x":1,"x":2}', "INPUT_JSON_INVALID"),
        (b'{"x":1.0}', "INPUT_JSON_INVALID"),
        (rb'{"x":"\ud800"}', "INPUT_ENCODING_INVALID"),
        (rb'{"\ud800":0}', "INPUT_ENCODING_INVALID"),
        (b" " + b"{}", "INPUT_CANONICAL_MISMATCH"),
        (b"{" + b'"x":' + b"1" * 81 + b"}", "INPUT_RESOURCE_LIMIT"),
        (_canonical({"x": "x" * 4_097}), "INPUT_RESOURCE_LIMIT"),
        (_canonical({"x": [0] * 513}), "INPUT_RESOURCE_LIMIT"),
        (_canonical([[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]]), "INPUT_RESOURCE_LIMIT"),
        (_canonical({"x": 1 << 256}), "INPUT_RESOURCE_LIMIT"),
    ),
)
def test_cp71_input_lexical_failures_have_stable_codes(
    raw_payload: object, code: str
) -> None:
    issued_before = len(cp71._ISSUED_RECORD_SNAPSHOTS)
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _mutated_first(raw_payload=raw_payload)
        ),
        code,
    )
    gc.collect()
    assert len(cp71._ISSUED_RECORD_SNAPSHOTS) == issued_before


def test_cp71_input_byte_limit_precedes_json_parsing() -> None:
    payload = b"{" + b"x" * 65_535 + b"}"
    assert len(payload) == 65_537
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _mutated_first(raw_payload=payload)
        ),
        "INPUT_BYTE_LIMIT",
    )


@pytest.mark.parametrize(
    "overrides,code",
    (
        ({"schema_version": "wrong"}, "INPUT_SCHEMA_MISMATCH"),
        ({"seed_ordinal": True}, "INPUT_FIELD_TYPE_MISMATCH"),
        ({"seed_ordinal": 0}, "INPUT_ORDINAL_MISMATCH"),
        ({"row_ordinal": 17}, "INPUT_ORDINAL_MISMATCH"),
        ({"logical_request_ordinal": 17}, "INPUT_ORDINAL_MISMATCH"),
        ({"row_key": "row-wrong"}, "INPUT_ROW_MISMATCH"),
        ({"fixture_id": "T28-M2-Q"}, "INPUT_ROW_MISMATCH"),
        (
            {"observable_cell_label": "returned-sir-selected-before-deadline"},
            "INPUT_OUTCOME_MISMATCH",
        ),
        ({"observable_contribution_ordinal": 1}, "INPUT_CONTRIBUTION_ORDINAL_MISMATCH"),
        ({"selected": True}, "INPUT_OUTCOME_MISMATCH"),
        ({"first_selected_attempt_one_based": 1}, "INPUT_OUTCOME_MISMATCH"),
        ({"selected_feature_ids": ("count/eq/0",)}, "INPUT_FEATURE_MISMATCH"),
        ({"selected_feature_values": (Fraction(2),)}, "INPUT_FEATURE_MISMATCH"),
    ),
)
def test_cp71_semantic_input_failures_have_stable_codes(
    overrides: Mapping[str, object], code: str
) -> None:
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _mutated_first(overrides=overrides)
        ),
        code,
    )


def test_cp71_field_set_and_digest_failures_are_distinct() -> None:
    value = _variant_values("all-nonselected-cyclic", 1, 1)
    del value["stable_trace_sha256"]
    payload = _canonical(value)
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _one_then_stop(payload)
        ),
        "INPUT_FIELD_SET_MISMATCH",
    )
    payload = _variant_bytes(
        "all-nonselected-cyclic",
        1,
        1,
        overrides={"record_sha256": "1" * 64},
        recompute_digest=False,
    )
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _one_then_stop(payload)
        ),
        "INPUT_DIGEST_MISMATCH",
    )


@pytest.mark.parametrize(
    "tag",
    (
        {"$fraction": ["01", "2"]},
        {"$fraction": ["-0", "1"]},
        {"$fraction": ["1", "0"]},
        {"$fraction": ["2", "2"]},
        {"$fraction": ["+1", "2"]},
    ),
)
def test_cp71_fraction_grammar_is_exact(tag: object) -> None:
    value = _variant_values("all-selected-duplicate-pairs", 1, 1)
    plain = cast(dict, _to_plain(value))
    plain["selected_feature_values"][0] = tag
    plain["record_sha256"] = _ZERO_SHA256
    plain["record_sha256"] = _sha(_INPUT_RECORD_DOMAIN, plain)
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _one_then_stop(_canonical(plain))
        ),
        "INPUT_FRACTION_MISMATCH",
    )


def test_cp71_stream_order_is_checked_before_aggregation() -> None:
    first = _variant_bytes("all-nonselected-cyclic", 1, 2)
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _one_then_stop(first)
        ),
        "INPUT_ORDINAL_MISMATCH",
    )


@pytest.mark.parametrize(
    "field,value",
    (
        ("plan_seed_hex", "0000000000000001"),
        ("seed_free_request_sha256", "1" * 64),
        ("runtime_lock_sha256", "2" * 64),
    ),
)
def test_cp71_group_coherence_rejects_plan_row_and_runtime_drift(
    field: str, value: object
) -> None:
    def source() -> Iterator[bytes]:
        last_row = 16 if field == "plan_seed_hex" else 2
        for row in range(1, last_row + 1):
            overrides = {field: value} if row == 2 else None
            yield _variant_bytes("all-nonselected-cyclic", 1, row, overrides=overrides)

    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(source()),
        "INPUT_GROUP_COHERENCE_MISMATCH",
    )


def test_cp71_current_item_validation_precedes_stream_coherence() -> None:
    def bad_digest() -> Iterator[bytes]:
        yield _variant_bytes("all-nonselected-cyclic", 1, 1)
        yield _variant_bytes(
            "all-nonselected-cyclic",
            1,
            2,
            overrides={
                "runtime_lock_sha256": "2" * 64,
                "record_sha256": "3" * 64,
            },
            recompute_digest=False,
        )

    def bad_row() -> Iterator[bytes]:
        yield _variant_bytes("all-nonselected-cyclic", 1, 1)
        yield _variant_bytes(
            "all-nonselected-cyclic",
            1,
            2,
            overrides={
                "row_key": "row-invalid",
                "runtime_lock_sha256": "2" * 64,
            },
        )

    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(bad_digest()),
        "INPUT_DIGEST_MISMATCH",
    )
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(bad_row()),
        "INPUT_ROW_MISMATCH",
    )


class _BadIterable:
    def __iter__(self) -> Iterator[bytes]:
        raise RuntimeError("iter failed")


class _MemoryIterable:
    def __iter__(self) -> Iterator[bytes]:
        raise MemoryError("iter exhausted memory")


def _failing_iterator() -> Iterator[bytes]:
    yield _variant_bytes("all-nonselected-cyclic", 1, 1)
    raise RuntimeError("next failed")


def _memory_iterator() -> Iterator[bytes]:
    yield _variant_bytes("all-nonselected-cyclic", 1, 1)
    raise MemoryError("next exhausted memory")


def test_cp71_iterator_failures_and_memory_exhaustion_are_separate() -> None:
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(_BadIterable()),
        "STREAM_ITERABLE_INVALID",
    )
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _failing_iterator()
        ),
        "STREAM_ITERATION_FAILED",
    )
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _MemoryIterable()
        ),
        "RESOURCE_EXHAUSTED",
    )
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _memory_iterator()
        ),
        "RESOURCE_EXHAUSTED",
    )


def test_cp71_decoder_memory_exhaustion_has_the_resource_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exhausted(*_args: object, **_kwargs: object) -> object:
        raise MemoryError("decoder allocation failed")

    monkeypatch.setattr(cp71.json, "loads", exhausted)
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _mutated_first(raw_payload=b"{}")
        ),
        "RESOURCE_EXHAUSTED",
    )


def test_cp71_stream_early_end_is_count_mismatch() -> None:
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(iter(())),
        "STREAM_COUNT_MISMATCH",
    )


def test_cp71_stream_extra_item_is_count_mismatch() -> None:
    def source() -> Iterator[bytes]:
        yield from _iter_independent_variant("all-nonselected-cyclic")
        yield _variant_bytes("all-nonselected-cyclic", 1, 1)

    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(source()),
        "STREAM_COUNT_MISMATCH",
    )


def test_cp71_stream_resource_limit_is_enforced_without_large_allocation() -> None:
    first = _variant_bytes("all-nonselected-cyclic", 1, 1)
    _error_code(
        lambda: cp71._reduce_supplied_cp69_interchange_byte_stream_details(
            _one_then_stop(first),
            limits=_hostile_limits(maximum_stream_bytes=len(first) - 1),
        ),
        "STREAM_RESOURCE_LIMIT",
    )


def test_cp71_aggregate_cap_is_checked_after_every_update() -> None:
    running = Fraction(0)
    for index in range(16):
        running += Fraction(1, _large_coprime_denominator(index))
    assert running.numerator.bit_length() <= 4_096
    assert running.denominator.bit_length() <= 4_096
    seventeenth = running + Fraction(1, _large_coprime_denominator(16))
    assert (
        max(seventeenth.numerator.bit_length(), seventeenth.denominator.bit_length())
        > 4_096
    )
    consumed = 0

    def source() -> Iterator[bytes]:
        nonlocal consumed
        for payload in _iter_independent_variant("aggregate-over-cap"):
            consumed += 1
            yield payload

    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(source()),
        "AGGREGATE_RESOURCE_LIMIT",
    )
    assert consumed == 257


def test_cp71_aggregate_cap_is_rechecked_for_the_derived_mean() -> None:
    running = sum(
        (Fraction(1, _large_coprime_denominator(index)) for index in range(16)),
        Fraction(0),
    )
    assert running.denominator.bit_length() == 4_096
    assert (running / 16).denominator.bit_length() == 4_097
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _iter_independent_variant("aggregate-near-cap")
        ),
        "AGGREGATE_RESOURCE_LIMIT",
    )


def test_cp71_aggregate_cap_is_rechecked_for_the_derived_interval() -> None:
    running = sum(
        (Fraction(1, denominator) for denominator in _INTERVAL_CROSSING_DENOMINATORS),
        Fraction(0),
    )
    mean = running / 1_040
    upper = mean + Fraction(3, 40)
    assert running.denominator.bit_length() == 4_087
    assert mean.denominator.bit_length() == 4_095
    assert upper.denominator.bit_length() == 4_097
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _iter_independent_variant("interval-derived-over-cap")
        ),
        "AGGREGATE_RESOURCE_LIMIT",
    )


def test_cp71_output_limit_is_enforced_with_a_lowered_hostile_seam() -> None:
    metrics = cp71._reduce_supplied_cp69_interchange_byte_stream_details(
        _iter_independent_variant("all-nonselected-cyclic")
    )
    for override in (
        {"maximum_output_record_bytes": 1},
        {"maximum_output_bytes": 1},
    ):
        hostile = dict(metrics)
        hostile["limits"] = _hostile_limits(**override)
        _error_code(
            lambda hostile=hostile: cp71._cp71_build_output(hostile),
            "OUTPUT_RESOURCE_LIMIT",
        )


class _CountingIterator:
    def __init__(self, source: Iterable[bytes]) -> None:
        self._iterator = iter(source)
        self.next_calls = 0
        self.close_calls = 0

    def __iter__(self) -> "_CountingIterator":
        return self

    def __next__(self) -> bytes:
        self.next_calls += 1
        return next(self._iterator)

    def close(self) -> None:
        self.close_calls += 1


class _ExplodingTerminalIterator(_CountingIterator):
    def __next__(self) -> bytes:
        self.next_calls += 1
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise RuntimeError("terminal next failed instead of stopping") from exc


def test_cp71_invokes_exactly_32769_next_calls_and_never_calls_close() -> None:
    iterator = _CountingIterator(_iter_independent_variant("all-nonselected-cyclic"))
    payload, summary = cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(iterator)
    assert payload
    assert summary.request_count == 32_768
    assert iterator.next_calls == 32_769
    assert iterator.close_calls == 0
    iterator_ref = weakref.ref(iterator)
    del iterator
    gc.collect()
    assert iterator_ref() is None


def test_cp71_terminal_32769th_next_exception_is_iteration_failure() -> None:
    iterator = _ExplodingTerminalIterator(
        _iter_independent_variant("all-nonselected-cyclic")
    )
    _error_code(
        lambda: cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(iterator),
        "STREAM_ITERATION_FAILED",
    )
    assert iterator.next_calls == 32_769
    assert iterator.close_calls == 0


def test_cp71_caller_iterator_boundary_is_truthfully_scoped() -> None:
    contract = _contract()
    assert contract.caller_iterable_invoked is True
    assert contract.caller_iterable_side_effects_qualified is False
    assert contract.caller_iterable_retention_qualified is False
    assert contract.caller_next_liveness_qualified is False
    assert contract.iterator_close_called is False
    assert contract.module_direct_filesystem_api_exposed is False
    assert contract.module_direct_clock_api_exposed is False
    assert contract.module_direct_rng_api_exposed is False
    assert contract.module_direct_network_api_exposed is False
    assert contract.module_direct_subprocess_api_exposed is False


def test_cp71_records_are_sealed_and_unissued_clones_are_refused() -> None:
    bundle = _bundle()
    summary_type = cp71.CP71SuppliedDevelopmentReductionSummaryV1
    _error_code(lambda: cp71.cp71_canonical_json_bytes({}), "RECORD_TYPE_MISMATCH")
    clone = object.__new__(summary_type)
    _error_code(lambda: cp71.cp71_canonical_json_bytes(clone), "RECORD_NOT_ISSUED")
    with pytest.raises((TypeError, AttributeError)):
        bundle.scope = "tampered"
    with pytest.raises(TypeError):
        type("CP71Subclass", (summary_type,), {})
    assert not hasattr(bundle, "__dict__")
    assert weakref.ref(bundle)() is bundle


def test_cp71_private_hostile_limit_seam_is_exact_and_fail_closed() -> None:
    _error_code(
        lambda: cp71._reduce_supplied_cp69_interchange_byte_stream_details(
            iter(()), limits={}
        ),
        "INTERNAL_INVARIANT_FAILED",
    )
    invalid = _hostile_limits()
    invalid["maximum_input_bits"] = invalid.pop("maximum_input_integer_bits")
    _error_code(
        lambda: cp71._reduce_supplied_cp69_interchange_byte_stream_details(
            iter(()), limits=invalid
        ),
        "INTERNAL_INVARIANT_FAILED",
    )


def test_cp71_summary_retains_no_input_payload_or_fraction_graph() -> None:
    payload, summary = _reduction("novel-k")
    assert all(
        type(getattr(summary, item.name)) is not bytes for item in fields(summary)
    )
    assert all(
        type(getattr(summary, item.name)) is not Fraction for item in fields(summary)
    )
    assert len(payload) < _output_contract().maximum_output_bytes


def test_cp71_concurrent_reductions_are_deterministic_and_isolated() -> None:
    def run() -> Tuple[str, str, object]:
        payload, summary = cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(
            _iter_independent_variant("novel-k")
        )
        return (
            hashlib.sha256(payload).hexdigest(),
            cp71.cp71_sha256(summary),
            summary,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = tuple(executor.map(lambda _index: run(), range(2)))
    assert first[:2] == second[:2]
    second_ref = weakref.ref(second[2])
    del second
    gc.collect()
    assert second_ref() is None
    object.__setattr__(first[2], "request_count", 0)
    _error_code(lambda: cp71.cp71_canonical_json_bytes(first[2]), "RECORD_TAMPERED")


def test_cp71_source_is_stdlib_only_and_does_not_import_predecessors() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_SOURCE), feature_version=(3, 9))
    forbidden = (
        "numpy",
        "scipy",
        "torch",
        "heterodiff",
        "os",
        "pathlib",
        "random",
        "secrets",
        "socket",
        "subprocess",
        "time",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(not alias.name.startswith(forbidden) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is None or not node.module.startswith(forbidden)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in ("open", "exec", "eval", "compile", "__import__")
        for node in ast.walk(tree)
    )


def test_cp71_source_defines_each_public_api_once_and_has_no_legacy_public_names() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_SOURCE))
    assert ast.get_docstring(tree, clean=False) == (
        "Bounded development recomputation from caller-supplied CP69 bytes.\n\n"
        "The sole data-processing API consumes exactly 32,768 canonical compact\n"
        "interchange byte records in seed-major order, validates their frozen CP69\n"
        "semantics plus CP71 stream coherence, reduces directly into fixed sufficient\n"
        "statistics, and returns a new CP71 554-estimand arithmetic output with a sealed\n"
        "scalar summary.  The output's numeric estimand arithmetic is compatible with\n"
        "CP68, but it\n"
        "has a new dynamic-input commitment and makes no CP68 fixture-custody claim.\n\n"
        "Only this module's direct filesystem, path, clock, RNG, network, and subprocess\n"
        "behavior is qualified.  Iterating caller code can have side effects, retain\n"
        "data, or fail to terminate.  Successful calls retain no input record or output\n"
        "body in a module cache; issued-summary snapshot metadata remains while its weak\n"
        "key is live.  Exception tracebacks can retain call locals.  No provenance,\n"
        "source law, production-attempt validity, operational prediction, coverage,\n"
        "primary decision threshold, decision, custody, evidence, or closure is claimed.\n"
    )
    definitions = tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )
    required_once = _EXPECTED_EXPORTS[34:]
    for name in required_once:
        assert definitions.count(name) == 1, name
    legacy_public_names = {
        "CP71EstimateIntervalOutputValidationQualificationError",
        "CP71SourceIndependentReducerContractV1",
        "CP71OutputValidationContractV1",
        "CP71FullReductionExpectationV1",
        "CP71EstimateIntervalOutputValidationV1",
        "CP71EstimateIntervalOutputValidationQualificationV1",
        "CP71EstimateIntervalOutputValidationQualificationBundleV1",
        "cp71_validate_closed_cp68_estimate_interval_output_bytes",
        "cp71_estimate_interval_output_validation_qualification_bundle",
        "cp71_run_estimate_interval_output_validation_qualification",
    }
    assert legacy_public_names.isdisjoint(definitions)
    ordinary_reducer_source = inspect.getsource(cp71._cp71_reduce_details_impl)
    assert "CP68" not in ordinary_reducer_source
    assert "ordered_cp68_projection" not in ordinary_reducer_source
    private_baseline_source = inspect.getsource(
        cp71._cp71_reduce_private_cp68_baseline_with_details
    )
    assert "_CP71_CP68_ORDERED_PROJECTION_DOMAIN" in private_baseline_source
    assert "private_baseline_ordered_cp68_projection_sha256" in private_baseline_source
    assert source.count("_cp71_reduce_private_cp68_baseline_with_details(") == 2
    assert source.count("_cp71_cp68_projection_digest(") == 2


def test_cp71_source_and_public_records_remain_python39_compatible() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_SOURCE), feature_version=(3, 9))
    assert isinstance(tree, ast.Module)
    assert "dataclass(slots=True" not in source.replace(" ", "")
    assert "except*" not in source
    assert _bundle().stdlib_only is True
    assert _bundle().project_modules_imported is False


def test_cp71_locked_python39_import_builder_and_sealing_are_deterministic() -> None:
    assert _PYTHON39.is_file()
    expected = (
        _bundle().record_sha256,
        cp71.cp71_sha256(_bundle()),
        hashlib.sha256(cp71.cp71_canonical_json_bytes(_bundle())).hexdigest(),
    )
    script = "\n".join(
        (
            "import hashlib, sys, weakref",
            f"sys.path.insert(0, {str(_ROOT / 'src')!r})",
            "from heterodiff.evaluation import "
            "mixed_initializer_test28_supplied_interchange_recomputation_qualification "
            "as c",
            "assert sys.version_info[:2] == (3, 9)",
            "b = " "c.cp71_supplied_interchange_recomputation_qualification_bundle()",
            "assert not hasattr(b, '__dict__')",
            "assert weakref.ref(b)() is b",
            "try:\n b.scope = 'forged'\n "
            "raise AssertionError('mutation accepted')\n"
            "except (AttributeError, TypeError):\n pass",
            "f = object.__new__(c.CP71SuppliedDevelopmentReductionSummaryV1)",
            "try:\n c.cp71_canonical_json_bytes(f)\n "
            "raise AssertionError('forgery accepted')\n"
            "except c.CP71SuppliedInterchangeRecomputationQualificationError "
            "as e:\n assert e.code == 'CP71_RECORD_NOT_ISSUED'",
            "print(b.record_sha256)",
            "print(c.cp71_sha256(b))",
            "print(hashlib.sha256(c.cp71_canonical_json_bytes(b)).hexdigest())",
        )
    )
    completed = subprocess.run(
        (str(_PYTHON39), "-I", "-c", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert tuple(completed.stdout.splitlines()) == expected
    assert completed.stderr == ""


def test_cp71_public_surface_is_narrow() -> None:
    assert cp71.__all__ == _EXPECTED_EXPORTS
    public = set(cp71.__all__)
    assert "cp71_reduce_supplied_cp69_interchange_byte_stream" in public
    assert "cp71_supplied_interchange_recomputation_qualification_bundle" in public
    assert "cp71_run_supplied_interchange_recomputation_qualification" in public
    forbidden_fragments = (
        "raw",
        "stable_trace_parser",
        "path",
        "writer",
        "decision",
        "production",
        "authorization",
        "evidence_accept",
    )
    assert not any(
        fragment in name for name in public for fragment in forbidden_fragments
    )
    assert tuple(
        inspect.signature(
            cp71.cp71_reduce_supplied_cp69_interchange_byte_stream
        ).parameters
    ) == ("payloads",)
    assert tuple(inspect.signature(cp71.cp71_canonical_json_bytes).parameters) == (
        "value",
    )
    assert tuple(inspect.signature(cp71.cp71_sha256).parameters) == ("value",)
    assert not inspect.signature(
        cp71.cp71_supplied_interchange_recomputation_qualification_bundle
    ).parameters
    assert not inspect.signature(
        cp71.cp71_run_supplied_interchange_recomputation_qualification
    ).parameters


def test_cp71_bundle_and_qualification_keep_every_production_claim_false() -> None:
    bundle = _bundle()
    qualification = cp71.cp71_run_supplied_interchange_recomputation_qualification()
    for record in (bundle, qualification):
        for name in (
            "input_provenance_authenticated",
            "external_seed_source_verified",
            "source_law_verified",
            "production_attempt_validity_evaluated",
            "production_recomputation",
            "operational_prediction",
            "power_review_present",
            "primary_thresholds_present",
            "decision_made",
            "production_evidence",
            "production_execution_authorized",
            "production_execution_observed",
            "runner_and_recomputation_blocker_closed",
            "unconditional_operational_predictions_blocker_closed",
            "power_and_thresholds_blocker_closed",
            "confirmatory_custody_blocker_closed",
            "confirmatory_evidence",
            "manuscript_claim",
            "formal_test_28_closed",
        ):
            if hasattr(record, name):
                assert getattr(record, name) is False, name
    assert bundle.blocker_ledger_total_count == 26
    assert bundle.blocker_ledger_satisfied_count == 22
    assert bundle.blocker_ledger_missing_count == 4
    assert bundle.formal_test_28_status == "OPEN"


def test_cp71_bundle_and_four_fixture_qualification_are_exactly_scoped() -> None:
    fixture_ids = (
        "cp69-closed-baseline",
        "all-selected-duplicate-pair-plan-seeds",
        "all-nonselected-cyclic-statuses",
        "novel-k-mixed-selection",
    )
    bundle = _bundle()
    qualification = cp71.cp71_run_supplied_interchange_recomputation_qualification()
    assert bundle.qualification_fixture_ids == fixture_ids
    assert type(bundle.qualification_fixture_specifications) is tuple
    assert len(bundle.qualification_fixture_specifications) == 4
    assert all(
        type(item) is str and item
        for item in bundle.qualification_fixture_specifications
    )
    assert bundle.zero_argument_builder is True
    assert bundle.builder_reduces_or_validates is False
    assert bundle.qualification_runner_zero_argument is True
    assert bundle.public_supplied_stream_reducer_exposed is True
    assert bundle.public_caller_data_api_count == 1
    for name in (
        "public_parser_exposed",
        "public_output_validator_exposed",
        "public_projection_mapper_exposed",
        "public_raw_record_api_exposed",
        "public_stable_trace_api_exposed",
        "public_path_api_exposed",
        "public_writer_api_exposed",
        "public_primary_decision_threshold_api_exposed",
        "public_decision_api_exposed",
        "public_evidence_api_exposed",
    ):
        assert getattr(bundle, name) is False
    assert qualification.fixture_ids == fixture_ids
    assert qualification.fixture_set_sha256 == (
        "bb4347afaca9e0ea41cb5b38ac74a3186b63fd95da9b4546b50de6aa1ffa83af"
    )
    assert qualification.fixture_stream_commitment_sha256s == (
        "ae84c3690749ec9d1c3926809604c12fb882eea33088eaff0e75e6f8c9f14ec9",
        "50d761fd6f69e48a99af2eef9f6ace38e3215be712021addfb788ae223321ad5",
        "93b88afc2089ff298dd1c4f07f471709c30a191ccf74dbfe86be123c73624fb7",
        "4a511d091f6fc8078996a120ac6ce28f8c31a2847347c8507d332f8a63f6410a",
    )
    assert qualification.fixture_summary_record_sha256s == (
        "638d0450373f1f8b62df27af8106dba81a141999c5124f3830109723bbe575a6",
        "449deac5eeffa209cb2a93485374bec0b38cc3c05a1922c891866880c967328e",
        "908100bc0df23f8ea5811541b107c607ab6de9c1990738400787d375cb218a78",
        "6bd7c35ed3aaa7e540ec853d11dd0a87f156978c051e47ba0eac54f7f02f07d3",
    )
    assert qualification.fixture_output_canonical_json_bytes == (
        708_081,
        724_245,
        678_667,
        718_937,
    )
    assert qualification.fixture_output_canonical_json_sha256s == (
        "b910b776d16cfe97813c821cc6358f88c068240e5d62fe26a1b30ff96937f1a7",
        "f9096b3c15cea651567bd436715a90c7c381a69de4688023def289d96798d505",
        "751bcd5ee2cca38be9edf88a94a54b60195b7c042838976b1987f5e9886b8239",
        "277476d47ada68c122173b8d1e8f9d871ae6fcb63802931800c00553657dc7b1",
    )
    assert qualification.baseline_cp68_compatibility_output_canonical_json_sha256 == (
        "f9e1bf93354af057d08ca722d2cffe1a8188d2f1e823a0173f9b6a937ddc42c3"
    )
    assert qualification.baseline_cp68_compatibility_projection_exact_match is True
    assert qualification.dynamic_fixture_count == 3
    assert qualification.dynamic_cp68_fixture_custody_claimed is False
    assert qualification.novel_success_counts == (1, 777, 1_024, 2_047)
    assert qualification.encountered_success_counts == (
        0,
        1,
        12,
        13,
        32,
        64,
        65,
        127,
        128,
        252,
        253,
        256,
        259,
        260,
        336,
        337,
        512,
        682,
        683,
        777,
        1_024,
        1_039,
        1_040,
        1_271,
        2_047,
        2_048,
    )
    assert qualification.encountered_success_count_count == len(
        qualification.encountered_success_counts
    )
    assert qualification.exact_endpoint_boundary_comparison_count == 132
    assert qualification.approximate_candidate_decides_endpoint is False
    assert qualification.module_owned_total_request_count == 131_072
    assert qualification.module_owned_total_input_bytes == 205_410_227
    independent_qualification = tuple(
        _oracle_details(variant)
        for variant in (
            "baseline",
            "all-selected-duplicate-pair-plan-seeds",
            "all-nonselected-cyclic-statuses",
            "novel-k-mixed-selection",
        )
    )
    assert qualification.fixture_stream_commitment_sha256s == tuple(
        details["commitment"] for details in independent_qualification
    )
    assert qualification.module_owned_total_input_bytes == sum(
        details["total_bytes"] for details in independent_qualification
    )
    assert qualification.module_owned_peak_input_payload_count == 1
    assert qualification.module_owned_peak_parsed_observation_count == 1
    assert qualification.module_owned_plan_seed_value_maximum_retained_count == 2_048
    assert qualification.module_owned_full_input_corpus_materialized is False
    assert (
        qualification.module_owned_input_records_retained_after_successful_return
        is False
    )
    assert qualification.dynamic_input_payload_or_output_body_cached is False
    assert qualification.sealed_summary_snapshot_retained_while_summary_live is True
    assert qualification.output_record_vector_cardinality == 554
    assert (
        qualification.maximum_simultaneously_materialized_output_record_count == 1_108
    )
    assert qualification.caller_iterable_side_effects_qualified is False
    assert qualification.caller_next_liveness_qualified is False
    for name in (
        "module_direct_filesystem_read",
        "module_direct_filesystem_write",
        "module_direct_clock_read",
        "module_direct_rng_used",
        "module_direct_network_used",
        "module_direct_subprocess_used",
        "raw_record_parsed",
        "stable_trace_parsed",
        "provenance_authenticated",
        "production_recomputation_performed",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_path_qualified",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
    ):
        assert getattr(qualification, name) is False, name
    assert qualification.production_gate_13_state == "MISSING"
    assert qualification.production_gate_14_state == "MISSING"
    assert qualification.production_evidence_present_count == 0
    assert qualification.all_development_qualification_checks_passed is True
