"""Independent hostile tests for the bounded CP72 development-output boundary."""

from __future__ import annotations

import ast
import builtins
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
from fractions import Fraction
from functools import lru_cache
import gc
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import pickle
import socket
import subprocess
import types
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple, cast
import weakref

import heterodiff.evaluation.mixed_initializer_test28_supplied_development_output_validation_qualification as cp72
import heterodiff.evaluation.mixed_initializer_test28_supplied_interchange_recomputation_qualification as cp71
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_supplied_development_output_validation_qualification.py"
)
_V22_PROTOCOL = _ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v22.md"
_V22_MANIFEST = _ROOT / "research/fixtures/cp50_test28_mixed_initializer_v22.json"
_CP71_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_supplied_interchange_recomputation_qualification.py"
)
_CP71_TEST = (
    _ROOT
    / "tests"
    / "unit"
    / "test_mixed_initializer_test28_supplied_interchange_recomputation_qualification.py"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")

_SCHEMA = "cp72-test28-supplied-development-output-validation-qualification-v1"
_SCOPE = (
    "development-only-source-independent-bounded-exact-cp71-development-output-"
    "byte-internal-validation;one-public-output-validator;cp72-validator-resource-"
    "subset;exact-554-estimand-inventory-record-digests-cross-record-identities-and-"
    "interval-arithmetic;stream-commitment-internal-preimage-coherence-only;ordered-"
    "and-runtime-digests-opaque;no-input-stream-relation-authorship-provenance-"
    "authentication-source-law-coverage-production-attempt-validity-operational-"
    "prediction-primary-threshold-decision-custody-receipt-evidence-gate-authorization-"
    "or-test28-closure-claim;no-public-parser-stream-reducer-raw-stable-path-writer-"
    "command-shard-or-campaign-api;no-project-imports;module-direct-io-clock-rng-"
    "network-subprocess-absence-only;successful-return-caller-payload-nonretention-"
    "only;exception-traceback-locals-unqualified;no-caller-output-body-cache;issued-"
    "summary-snapshot-retained-while-live"
)
_CP71_OUTPUT_SCHEMA = "cp71-test28-supplied-development-estimate-interval-output-v1"
_CP69_SCHEMA = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_SCHEMA = "cp63-test28-independent-compact-recomputation-v1"
_INPUT_CLASSIFICATION = (
    "caller-supplied-cp69-valid-and-cp71-resource-bounded-development-byte-stream"
)
_ZERO_SHA256 = "0" * 64
_OUTPUT_RECORD_DOMAIN = b"cp71-test28-supplied-estimand-estimate-interval-v1"
_ORDERED_RECORD_DOMAIN = b"cp71-test28-ordered-estimand-record-digests-v1"
_OUTPUT_BODY_DOMAIN = (
    b"cp71-test28-supplied-interchange-estimate-interval-output-body-v1"
)
_STREAM_COMMITMENT_DOMAIN = b"cp71-test28-supplied-interchange-stream-commitment-v1"
_CP61_CROSSWALK_DOMAIN = b"cp72-test28-ordered-cp61-estimand-inventory-crosswalk-v1"
_CP61_CROSSWALK_SHA256 = (
    "6861002c492af9f0a9f0212d954e4a0008bbeaa5749c23ec9ad5cb60c2c3da77"
)
_N = 2_048
_ROW_COUNT = 16
_REQUEST_COUNT = 32_768
_ESTIMAND_COUNT = 554
_OBSERVABLE_COUNT = 72
_FIRST_ATTEMPT_COUNT = 170
_FEATURE_COUNT = 312
_BINOMIAL_COUNT = 242
_TAIL_RECIPROCAL = 110_800
_CP_DENOMINATOR = 1 << 256
_ROW_SHAPES = tuple(
    (fixture, strategy, budget)
    for fixture in ("T28-M1-Q", "T28-M2-Q")
    for strategy, budgets in (
        ("bounded-rejection", (1, 4, 16, 64)),
        ("fixed-budget-sir", (8, 32, 128, 512)),
    )
    for budget in budgets
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

_FIXTURE_IDS = (
    "cp69-closed-baseline",
    "all-selected-duplicate-pair-plan-seeds",
    "all-nonselected-cyclic-statuses",
    "novel-k-mixed-selection",
    "cp72-nonfixture-novel-success-counts",
)
_CP71_FIXTURE_BYTES = (708_081, 724_245, 678_667, 718_937)
_CP71_FIXTURE_SHA256S = (
    "b910b776d16cfe97813c821cc6358f88c068240e5d62fe26a1b30ff96937f1a7",
    "f9096b3c15cea651567bd436715a90c7c381a69de4688023def289d96798d505",
    "751bcd5ee2cca38be9edf88a94a54b60195b7c042838976b1987f5e9886b8239",
    "277476d47ada68c122173b8d1e8f9d871ae6fcb63802931800c00553657dc7b1",
)
_QUALIFICATION_OUTPUT_BYTES = _CP71_FIXTURE_BYTES + (696_156,)
_QUALIFICATION_OUTPUT_SHA256S = _CP71_FIXTURE_SHA256S + (
    "8411f6657d0b689e1c6c7be3ff9f54fb2aeb0db19d166310574c4a3ec7ac2607",
)
_QUALIFICATION_FIXTURE_SET_DOMAIN = (
    b"cp72-test28-supplied-development-output-validation-qualification-fixture-set-v1"
)
_QUALIFICATION_SUMMARY_RECORD_SHA256S = (
    "ff8b5294298cf38ccafbaf58691338ff0f1b83a286a91adcd1cf307989122d38",
    "127f5628410f2516d7a0dd57071234bb4a96940be13710c5c30b822b9254e56c",
    "0e9a1e71e3f5fab294ed00cb87aff1ee34406c4618cc89d98a124c0e3a0b2a1c",
    "4c85890555732f7ce0c62b99eb0b69249584bf919c2afa68b835f9fd6f103b35",
    "ae0a8f22ab672cf2e9ff39fc31c18db25f66c0be0240b2664dbbad0192fde32f",
)
_QUALIFICATION_FIXTURE_SET_SHA256 = (
    "58ca1ff512558ca10fc4bdc447474aaf0ee04decd272954a85fff3e56c89941d"
)
_QUALIFICATION_RECORD_SHA256 = (
    "2202dc80acf16f0b7a59582979483bed60f19d6f57b2e86d044b68224518ac27"
)
_QUALIFICATION_PUBLIC_SHA256 = (
    "12b99a75d4ef04745fdc86f4f25c0658e37ca14e5fb43f1acf1587661f36c931"
)
_SELECTED_COUNTS = (
    (
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
    ),
    (2_048,) * 16,
    (0,) * 16,
    (1, 1_024, 2_047, 777) * 4,
    (
        2,
        17,
        257,
        513,
        769,
        1_038,
        1_041,
        1_283,
        1_537,
        1_793,
        2_046,
        3,
        511,
        778,
        1_023,
        2_045,
    ),
)
_COMPUTED_COUNTS = (398, 554, 242, 320, 386)
_INSUFFICIENT_COUNTS = (156, 0, 312, 234, 168)

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
_ESTIMAND_KEYS = (
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
_STREAM_PREIMAGE_KEYS = (
    "request_count",
    "total_input_bytes",
    "ordered_interchange_record_sha256",
    "ordered_projection_sha256",
    "ordered_seed_ordinal_plan_seed_sha256",
    "ordered_request_instance_sha256",
    "ordered_stable_trace_sha256",
    "runtime_lock_sha256",
)

_ERROR_CODES = (
    "CP72_INPUT_TYPE_MISMATCH",
    "CP72_INPUT_BYTE_LIMIT",
    "CP72_INPUT_ENCODING_INVALID",
    "CP72_INPUT_JSON_INVALID",
    "CP72_INPUT_RESOURCE_LIMIT",
    "CP72_INPUT_CANONICAL_MISMATCH",
    "CP72_INPUT_FIELD_SET_MISMATCH",
    "CP72_INPUT_FIELD_TYPE_MISMATCH",
    "CP72_INPUT_SCHEMA_MISMATCH",
    "CP72_INPUT_INVENTORY_MISMATCH",
    "CP72_INPUT_DIGEST_MISMATCH",
    "CP72_INPUT_COMMITMENT_MISMATCH",
    "CP72_INPUT_ARITHMETIC_MISMATCH",
    "CP72_INPUT_INTERVAL_MISMATCH",
    "CP72_RESOURCE_EXHAUSTED",
    "CP72_RECORD_TYPE_MISMATCH",
    "CP72_RECORD_NOT_ISSUED",
    "CP72_RECORD_TAMPERED",
    "CP72_INTERNAL_INVARIANT_FAILED",
)
_EXPECTED_ALL = (
    "CP72_TEST28_SCHEMA_VERSION",
    "CP72_TEST28_SCOPE",
    "CP72_TEST28_FORMAL_TEST_28_STATUS",
    "CP72_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP72_TEST28_SEED_COUNT",
    "CP72_TEST28_ROW_COUNT",
    "CP72_TEST28_REQUEST_COUNT",
    "CP72_TEST28_ESTIMAND_COUNT",
    "CP72_TEST28_OBSERVABLE_ESTIMAND_COUNT",
    "CP72_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
    "CP72_TEST28_FEATURE_ESTIMAND_COUNT",
    "CP72_TEST28_BINOMIAL_ESTIMAND_COUNT",
    "CP72_TEST28_FAMILYWISE_ERROR_BUDGET",
    "CP72_TEST28_PER_ESTIMATOR_ERROR_BUDGET",
    "CP72_TEST28_PER_TAIL_ERROR_BUDGET",
    "CP72_TEST28_CP_BISECTION_STEPS",
    "CP72_TEST28_MINIMUM_SELECTED_COUNT",
    "CP72_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER",
    "CP72_TEST28_MAXIMUM_OUTPUT_BYTES",
    "CP72_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES",
    "CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES",
    "CP72_TEST28_MAXIMUM_CANONICAL_DEPTH",
    "CP72_TEST28_MAXIMUM_CANONICAL_NODES",
    "CP72_TEST28_MAXIMUM_KEY_CHARACTERS",
    "CP72_TEST28_MAXIMUM_TEXT_CHARACTERS",
    "CP72_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS",
    "CP72_TEST28_MAXIMUM_FRACTION_DECIMAL_DIGITS",
    "CP72_TEST28_MAXIMUM_INTEGER_BITS",
    "CP72_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT",
    "CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY",
    "CP72_TEST28_QUALIFICATION_FIXTURE_IDS",
    "CP72_TEST28_ERROR_CODES",
    "CP72SuppliedDevelopmentOutputValidationQualificationError",
    "CP72PredecessorCustodyV1",
    "CP72SuppliedDevelopmentOutputValidationContractV1",
    "CP72SuppliedDevelopmentOutputValidationSummaryV1",
    "CP72SuppliedDevelopmentOutputValidationQualificationV1",
    "CP72SuppliedDevelopmentOutputValidationQualificationBundleV1",
    "cp72_canonical_json_bytes",
    "cp72_sha256",
    "cp72_validate_supplied_cp71_development_output_bytes",
    "cp72_supplied_development_output_validation_qualification_bundle",
    "cp72_run_supplied_development_output_validation_qualification",
)

_RECORD_FIELDS = {
    "CP72PredecessorCustodyV1": (
        "schema_version",
        "v22_protocol_sha256",
        "v22_protocol_bytes",
        "v22_protocol_lf_count",
        "v22_manifest_sha256",
        "v22_manifest_bytes",
        "v22_manifest_lf_count",
        "cp71_source_sha256",
        "cp71_test_sha256",
        "cp71_bundle_record_sha256",
        "cp71_stream_contract_record_sha256",
        "cp71_output_contract_record_sha256",
        "cp71_qualification_record_sha256",
        "cp71_fixture_set_sha256",
        "cp71_fixture_output_canonical_json_bytes",
        "cp71_fixture_output_canonical_json_sha256s",
        "record_sha256",
    ),
    "CP72SuppliedDevelopmentOutputValidationContractV1": (
        "schema_version",
        "contract_id",
        "source_output_schema_version",
        "source_interchange_schema_version",
        "source_semantic_schema_version",
        "input_type",
        "canonical_json_profile",
        "exact_output_root_keys",
        "exact_estimand_record_keys",
        "exact_stream_commitment_preimage_keys",
        "request_count",
        "seed_count",
        "row_count",
        "estimand_count",
        "observable_estimand_count",
        "rejection_first_attempt_estimand_count",
        "feature_estimand_count",
        "binomial_estimand_count",
        "exact_cp61_inventory_crosswalk_required",
        "exact_estimand_order_required",
        "record_digest_recomputed",
        "ordered_estimand_digest_computed",
        "output_body_digest_computed",
        "stream_commitment_internal_preimage_recomputed",
        "cross_record_arithmetic_validated",
        "exact_cp_endpoint_boundaries_validated",
        "feature_arithmetic_validated",
        "input_stream_relation_verified",
        "input_provenance_authenticated",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "operational_coverage_claimed",
        "primary_thresholds_present",
        "decision_fields_present",
        "production_evidence_accepted",
        "maximum_output_bytes",
        "maximum_declared_total_input_bytes",
        "maximum_output_record_bytes",
        "maximum_canonical_depth",
        "maximum_canonical_nodes",
        "maximum_key_characters",
        "maximum_text_characters",
        "maximum_integer_decimal_digits",
        "maximum_fraction_decimal_digits",
        "maximum_integer_bits",
        "maximum_cp_endpoint_cache_count",
        "maximum_output_vector_cardinality",
        "ordered_cp61_inventory_crosswalk_digest_domain",
        "estimand_record_digest_domain",
        "ordered_estimand_digest_domain",
        "output_body_digest_domain",
        "stream_commitment_digest_domain",
        "record_sha256",
    ),
    "CP72SuppliedDevelopmentOutputValidationSummaryV1": (
        "schema_version",
        "source_output_schema_version",
        "request_count",
        "estimand_count",
        "observable_estimand_count",
        "rejection_first_attempt_estimand_count",
        "feature_estimand_count",
        "binomial_estimand_count",
        "declared_total_input_bytes",
        "declared_input_stream_commitment_sha256",
        "declared_ordered_interchange_record_sha256",
        "declared_ordered_projection_sha256",
        "declared_ordered_seed_ordinal_plan_seed_sha256",
        "declared_ordered_request_instance_sha256",
        "declared_ordered_stable_trace_sha256",
        "declared_runtime_lock_sha256",
        "stream_commitment_coherence_verified",
        "ordered_cp61_inventory_crosswalk_sha256",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
        "canonical_json_verified",
        "schema_verified",
        "estimand_inventory_and_order_verified",
        "record_digests_verified",
        "cross_record_arithmetic_verified",
        "exact_interval_arithmetic_verified",
        "selected_counts_by_row",
        "observable_row_sums",
        "rejection_first_attempt_row_sums",
        "feature_estimate_present_count",
        "feature_estimate_absent_count",
        "binomial_interval_count",
        "feature_interval_count",
        "computed_interval_count",
        "insufficient_selection_count",
        "distinct_binomial_success_count_count",
        "exact_endpoint_boundary_comparison_count",
        "input_stream_relation_verified",
        "input_provenance_authenticated",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_made",
        "production_evidence",
        "record_sha256",
    ),
    "CP72SuppliedDevelopmentOutputValidationQualificationV1": (
        "schema_version",
        "fixture_set_sha256",
        "fixture_ids",
        "fixture_validation_summary_record_sha256s",
        "fixture_output_canonical_json_bytes",
        "fixture_output_canonical_json_sha256s",
        "fixture_selected_counts_by_row",
        "fixture_computed_interval_counts",
        "fixture_insufficient_selection_counts",
        "fixture_count",
        "module_owned_total_output_bytes",
        "module_owned_peak_input_payload_count",
        "module_owned_peak_parsed_output_count",
        "maximum_simultaneously_materialized_estimand_record_count",
        "module_owned_output_payload_or_body_cached",
        "caller_output_retained_after_successful_return",
        "sealed_summary_snapshot_retained_while_summary_live",
        "module_direct_filesystem_read",
        "module_direct_filesystem_write",
        "module_direct_clock_read",
        "module_direct_rng_used",
        "module_direct_network_used",
        "module_direct_subprocess_used",
        "source_independent",
        "stdlib_only",
        "input_stream_relation_verified",
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
    "CP72SuppliedDevelopmentOutputValidationQualificationBundleV1": (
        "schema_version",
        "scope",
        "blocker_ledger_prerequisite_id",
        "blocker_ledger_prerequisite_state",
        "blocker_ledger_total_count",
        "blocker_ledger_satisfied_count",
        "blocker_ledger_missing_count",
        "predecessor_custody",
        "validation_contract",
        "qualification_fixture_ids",
        "qualification_fixture_specifications",
        "zero_argument_builder",
        "builder_validates",
        "qualification_runner_zero_argument",
        "public_supplied_output_validator_exposed",
        "public_caller_data_api_count",
        "public_parser_exposed",
        "public_stream_reducer_exposed",
        "public_raw_record_api_exposed",
        "public_stable_trace_api_exposed",
        "public_path_api_exposed",
        "public_writer_api_exposed",
        "public_primary_decision_threshold_api_exposed",
        "public_decision_api_exposed",
        "public_receipt_or_evidence_api_exposed",
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

_RECORD_DOMAINS = {
    "CP72PredecessorCustodyV1": b"cp72-test28-predecessor-custody-v1",
    "CP72SuppliedDevelopmentOutputValidationContractV1": (
        b"cp72-test28-supplied-development-output-validation-contract-v1"
    ),
    "CP72SuppliedDevelopmentOutputValidationSummaryV1": (
        b"cp72-test28-supplied-development-output-validation-summary-v1"
    ),
    "CP72SuppliedDevelopmentOutputValidationQualificationV1": (
        b"cp72-test28-supplied-development-output-validation-qualification-v1"
    ),
    "CP72SuppliedDevelopmentOutputValidationQualificationBundleV1": (
        b"cp72-test28-supplied-development-output-validation-qualification-bundle-v1"
    ),
}


def _to_plain(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is Fraction:
        item = cast(Fraction, value)
        return {"$fraction": [str(item.numerator), str(item.denominator)]}
    if type(value) in (tuple, list):
        return [_to_plain(item) for item in cast(Iterable[object], value)]
    if type(value) is dict:
        return {
            cast(str, key): _to_plain(item)
            for key, item in cast(Mapping[str, object], value).items()
        }
    if is_dataclass(value):
        return {
            item.name: _to_plain(getattr(value, item.name)) for item in fields(value)
        }
    raise TypeError("unsupported independent canonical value")


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


def _decode(payload: bytes) -> dict:
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
    assert type(value) is dict and tuple(cast(dict, value)) == ("$fraction",)
    pair = cast(dict, value)["$fraction"]
    assert type(pair) is list and len(pair) == 2
    assert type(pair[0]) is type(pair[1]) is str
    return Fraction(int(pair[0]), int(pair[1]))


def _tagged_sha(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _canonical(value)).hexdigest()


def _repair_estimand(record: dict) -> None:
    record["record_sha256"] = _ZERO_SHA256
    record["record_sha256"] = _tagged_sha(_OUTPUT_RECORD_DOMAIN, record)


def _stream_commitment(root: Mapping[str, object]) -> str:
    return _tagged_sha(
        _STREAM_COMMITMENT_DOMAIN,
        {key: root[key] for key in _STREAM_PREIMAGE_KEYS},
    )


def _repair_stream_commitment(root: dict) -> None:
    root["input_stream_commitment_sha256"] = _stream_commitment(root)


def _error_code(call: Callable[[], object], expected: str) -> None:
    with pytest.raises(
        cp72.CP72SuppliedDevelopmentOutputValidationQualificationError
    ) as caught:
        call()
    assert caught.value.code == "CP72_" + expected
    assert str(caught.value)


def _assert_record_digest(record: object) -> None:
    record_type = type(record)
    body = {item.name: getattr(record, item.name) for item in fields(record_type)}
    supplied = body["record_sha256"]
    body["record_sha256"] = _ZERO_SHA256
    assert supplied == _tagged_sha(cp72._RECORD_DOMAINS[record_type], body)
    assert cp72.cp72_canonical_json_bytes(record) == _canonical(record)


@lru_cache(maxsize=None)
def _cp71_fixture_output(fixture_id: str) -> bytes:
    """Obtain predecessor bytes while keeping the CP72 oracle independent."""

    if fixture_id == "cp69-closed-baseline":
        payload = cp71._cp71_reduce_private_cp68_baseline_with_details()[0]
    else:
        payload = cp71._cp71_reduce_with_details(cp71._cp71_iter_fixture(fixture_id))[0]
    assert type(payload) is bytes
    return payload


@lru_cache(maxsize=None)
def _cp72_qualification_fixture_output(fixture_id: str) -> bytes:
    """Expose only the source-owned qualification body to the independent oracle."""

    payload = cp72._build_qualification_fixture_output(
        fixture_id,
        cp72._qualification_cp_endpoints(),
        cp72._qualification_cp61_record_sha256s(),
    )
    assert type(payload) is bytes
    return payload


@lru_cache(maxsize=1)
def _cp71_nonfixture_output() -> bytes:
    """Build an actual CP71 output whose bytes are outside all frozen fixtures."""

    input_domain = b"cp69-test28-compact-interchange-observation-v1"

    def records() -> Iterable[bytes]:
        for index, payload in enumerate(
            cp71._cp71_iter_fixture("all-nonselected-cyclic-statuses")
        ):
            if index:
                yield payload
                continue
            value = _decode(payload)
            value["request_instance_sha256"] = "a" * 64
            value["stable_trace_sha256"] = "b" * 64
            value["record_sha256"] = _ZERO_SHA256
            value["record_sha256"] = _tagged_sha(input_domain, value)
            yield _canonical(value)

    payload, summary = cp71.cp71_reduce_supplied_cp69_interchange_byte_stream(records())
    assert summary.input_provenance_authenticated is False
    assert hashlib.sha256(payload).hexdigest() not in _CP71_FIXTURE_SHA256S
    return payload


@lru_cache(maxsize=1)
def _cp61_specs() -> Tuple[object, ...]:
    """Reconstruct the frozen compact CP61 inventory without importing CP61."""

    def row_key(row: int) -> str:
        fixture, strategy, budget = _ROW_SHAPES[row - 1]
        return "row-%02d/%s/%s/budget-%d" % (row, fixture, strategy, budget)

    def projections(fixture: str) -> Tuple[Tuple[int, str], ...]:
        if fixture == "T28-M1-Q":
            return ((1, "axis0"),)
        return (
            (0, "axis0"),
            (1, "axis0"),
            (1, "axis1"),
            (1, "diag-plus-3-4"),
            (1, "diag-minus-3-4"),
        )

    def feature_ids(fixture: str) -> Tuple[str, ...]:
        cap = 1 if fixture == "T28-M1-Q" else 2
        dimensions = 2
        projection_items = projections(fixture)
        result = ["count/eq/%d" % count for count in range(cap + 1)]
        result.extend("type/%d/occupancy" % index for index in range(dimensions))
        for type_index, projection in projection_items:
            result.extend(
                (
                    "coordinate/%d/%s/odd" % (type_index, projection),
                    "coordinate/%d/%s/even" % (type_index, projection),
                )
            )
        if cap == 2:
            by_type = {
                type_index: tuple(
                    item for item in projection_items if item[0] == type_index
                )
                for type_index in range(dimensions)
            }
            for left_type in range(dimensions):
                for right_type in range(left_type, dimensions):
                    result.append("pair-type/%d/%d" % (left_type, right_type))
            for left_type in range(dimensions):
                for right_type in range(left_type, dimensions):
                    for left_position, left in enumerate(by_type[left_type]):
                        for right_position, right in enumerate(by_type[right_type]):
                            if (
                                left_type == right_type
                                and right_position < left_position
                            ):
                                continue
                            result.append(
                                "pair-projection/%d/%s/%d/%s"
                                % (left_type, left[1], right_type, right[1])
                            )
        assert len(result) == (6 if fixture == "T28-M1-Q" else 33)
        return tuple(result)

    def bounds(feature_id: str) -> Tuple[Fraction, Fraction]:
        lower = (
            Fraction(-1)
            if feature_id.endswith("/odd") or feature_id.startswith("pair-projection/")
            else Fraction(0)
        )
        return lower, Fraction(1)

    result: List[object] = []
    ordinal = 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        for cell in cells:
            result.append(
                types.SimpleNamespace(
                    estimand_ordinal=ordinal,
                    estimand_id="cp61/observable/%s/%s" % (row_key(row), cell),
                    estimand_family="observable-cell",
                    row_ordinal=row,
                    fixture_id=fixture,
                    strategy=strategy,
                    budget=budget,
                    observable_cell_label=cell,
                    first_attempt_one_based=None,
                    feature_id=None,
                    feature_lower_bound=None,
                    feature_upper_bound=None,
                    denominator_mode="all-2048-supplied-seed-ordinal-groups",
                )
            )
            ordinal += 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        if strategy != "bounded-rejection":
            continue
        for attempt in range(1, budget + 1):
            result.append(
                types.SimpleNamespace(
                    estimand_ordinal=ordinal,
                    estimand_id="cp61/rejection-first-attempt/%s/attempt-%d"
                    % (row_key(row), attempt),
                    estimand_family="rejection-first-attempt",
                    row_ordinal=row,
                    fixture_id=fixture,
                    strategy=strategy,
                    budget=budget,
                    observable_cell_label=None,
                    first_attempt_one_based=attempt,
                    feature_id=None,
                    feature_lower_bound=None,
                    feature_upper_bound=None,
                    denominator_mode="all-2048-supplied-seed-ordinal-groups",
                )
            )
            ordinal += 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        for feature_id in feature_ids(fixture):
            lower, upper = bounds(feature_id)
            result.append(
                types.SimpleNamespace(
                    estimand_ordinal=ordinal,
                    estimand_id="cp61/selected-feature/%s/%s"
                    % (row_key(row), feature_id),
                    estimand_family="selected-conditional-feature",
                    row_ordinal=row,
                    fixture_id=fixture,
                    strategy=strategy,
                    budget=budget,
                    observable_cell_label=None,
                    first_attempt_one_based=None,
                    feature_id=feature_id,
                    feature_lower_bound=lower,
                    feature_upper_bound=upper,
                    denominator_mode="predeadline-selected-count-in-this-row",
                )
            )
            ordinal += 1
    assert ordinal == 555 and len(result) == 554
    return tuple(result)


_CP_POWER = 1 << (256 * _N)


@lru_cache(maxsize=None)
def _upper_tail_compare(success_count: int, numerator: int) -> int:
    if success_count <= 0:
        return 1
    if success_count > _N or numerator == 0:
        return -1
    if numerator == _CP_DENOMINATOR:
        return 1
    complement = _CP_DENOMINATOR - numerator
    term = (
        math.comb(_N, success_count)
        * numerator**success_count
        * complement ** (_N - success_count)
    )
    partial = term
    index = success_count
    while True:
        left = partial * _TAIL_RECIPROCAL
        if left > _CP_POWER:
            return 1
        if index == _N:
            return (left > _CP_POWER) - (left < _CP_POWER)
        ratio_numerator = (_N - index) * numerator
        ratio_denominator = (index + 1) * complement
        if ratio_numerator < ratio_denominator:
            gap = ratio_denominator - ratio_numerator
            bounded_left = (partial * gap + term * ratio_numerator) * _TAIL_RECIPROCAL
            if bounded_left < _CP_POWER * gap:
                return -1
        term, remainder = divmod(term * ratio_numerator, ratio_denominator)
        assert remainder == 0
        partial += term
        index += 1


@lru_cache(maxsize=None)
def _certify_interval(success: int, lower: Fraction, upper: Fraction) -> int:
    comparisons = 0
    assert Fraction(0) <= lower <= upper <= Fraction(1)
    if success == 0:
        assert lower == 0
    else:
        scaled = lower * _CP_DENOMINATOR
        assert scaled.denominator == 1
        numerator = scaled.numerator
        assert _upper_tail_compare(success, numerator) < 0
        assert _upper_tail_compare(success, numerator + 1) >= 0
        comparisons += 2
    if success == _N:
        assert upper == 1
    else:
        scaled = (1 - upper) * _CP_DENOMINATOR
        assert scaled.denominator == 1
        numerator = scaled.numerator
        complement_success = _N - success
        assert _upper_tail_compare(complement_success, numerator) < 0
        assert _upper_tail_compare(complement_success, numerator + 1) >= 0
        comparisons += 2
    return comparisons


def _assert_output_and_summary(
    payload: bytes,
    summary: object,
    expected_selected: Optional[Tuple[int, ...]] = None,
) -> None:
    root = _decode(payload)
    assert (
        tuple(
            cp72.cp72_supplied_development_output_validation_qualification_bundle().validation_contract.exact_output_root_keys
        )
        == _ROOT_KEYS
    )
    assert tuple(root) == tuple(sorted(_ROOT_KEYS))
    assert set(root) == set(_ROOT_KEYS)
    assert root["schema_version"] == _CP71_OUTPUT_SCHEMA
    assert root["source_interchange_schema_version"] == _CP69_SCHEMA
    assert root["source_semantic_schema_version"] == _CP63_SCHEMA
    assert root["input_stream_classification"] == _INPUT_CLASSIFICATION
    fixed_root_claims = {
        "input_provenance_authenticated": False,
        "source_law_verified": False,
        "external_seed_source_verified": False,
        "runtime_lock_authenticated": False,
        "request_instance_sha256_authenticated": False,
        "stable_trace_sha256_authenticated": False,
        "cp61_estimand_digest_is_inventory_reference_only": True,
        "cp61_estimand_semantics_realized": False,
        "production_attempt_validity_evaluated": False,
        "production_recomputation": False,
        "arithmetic_transform_only": True,
        "request_count": _REQUEST_COUNT,
        "estimand_count": _ESTIMAND_COUNT,
    }
    for key, value in fixed_root_claims.items():
        assert root[key] == value
        assert type(root[key]) is type(value)
    assert _REQUEST_COUNT <= root["total_input_bytes"] <= 268_435_456
    assert root["input_stream_commitment_sha256"] == _stream_commitment(root)
    assert "ordered_estimand_record_sha256s_sha256" not in root
    assert "output_body_sha256" not in root
    for key in (
        "input_stream_commitment_sha256",
        "ordered_interchange_record_sha256",
        "ordered_projection_sha256",
        "ordered_seed_ordinal_plan_seed_sha256",
        "ordered_request_instance_sha256",
        "ordered_stable_trace_sha256",
        "runtime_lock_sha256",
    ):
        assert type(root[key]) is str
        assert len(root[key]) == 64
        assert root[key] == root[key].lower()
        bytes.fromhex(root[key])

    specs = _cp61_specs()
    records = root["estimand_estimate_intervals"]
    assert type(records) is list and len(records) == len(specs) == _ESTIMAND_COUNT
    ordered = hashlib.sha256(_ORDERED_RECORD_DOMAIN + b"\0")
    crosswalk = hashlib.sha256(_CP61_CROSSWALK_DOMAIN + b"\0")
    observable_by_row = [0] * _ROW_COUNT
    first_by_row = [0] * _ROW_COUNT
    selected_by_row: List[Optional[int]] = [None] * _ROW_COUNT
    feature_present = 0
    feature_intervals = 0
    success_counts = set()
    endpoint_comparisons = 0
    for ordinal, (spec, record) in enumerate(zip(specs, records), 1):
        assert type(record) is dict
        assert tuple(record) == tuple(sorted(_ESTIMAND_KEYS))
        assert set(record) == set(_ESTIMAND_KEYS)
        assert record["schema_version"] == _CP71_OUTPUT_SCHEMA
        assert record["estimand_ordinal"] == ordinal == spec.estimand_ordinal
        assert record["estimand_id"] == spec.estimand_id
        assert type(record["cp61_estimand_record_sha256"]) is str
        assert len(record["cp61_estimand_record_sha256"]) == 64
        crosswalk.update(bytes.fromhex(record["cp61_estimand_record_sha256"]))
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
        assert _fraction(record["feature_lower_bound"]) == spec.feature_lower_bound
        assert _fraction(record["feature_upper_bound"]) == spec.feature_upper_bound
        assert record["development_supplied_input_only"] is True
        assert record["input_provenance_authenticated"] is False
        assert record["arithmetic_transform_only"] is True
        body = dict(record)
        supplied_digest = body["record_sha256"]
        body["record_sha256"] = _ZERO_SHA256
        assert supplied_digest == _tagged_sha(_OUTPUT_RECORD_DOMAIN, body)
        assert len(_canonical(record)) <= 65_536
        ordered.update(bytes.fromhex(supplied_digest))

        family = record["estimand_family"]
        row = record["row_ordinal"] - 1
        denominator = record["denominator_count"]
        assert type(denominator) is int and denominator >= 0
        if family in ("observable-cell", "rejection-first-attempt"):
            assert record["denominator_mode"] == (
                "all-2048-supplied-seed-ordinal-groups"
            )
            assert denominator == _N
            success = record["success_count"]
            assert type(success) is int and 0 <= success <= _N
            assert _fraction(record["exact_feature_sum"]) is None
            assert _fraction(record["estimate"]) == Fraction(success, _N)
            assert record["interval_method"] == (
                "clopper-pearson-exact-rational-certified-equivalent-outward-"
                "endpoint-on-2^-256-grid-n2048"
            )
            assert record["interval_state"] == "computed"
            lower = cast(Fraction, _fraction(record["interval_lower"]))
            upper = cast(Fraction, _fraction(record["interval_upper"]))
            if success not in success_counts:
                endpoint_comparisons += _certify_interval(success, lower, upper)
                success_counts.add(success)
            if family == "observable-cell":
                observable_by_row[row] += success
            else:
                first_by_row[row] += success
        else:
            assert family == "selected-conditional-feature"
            assert record["denominator_mode"] == spec.denominator_mode
            assert record["success_count"] is None
            if selected_by_row[row] is None:
                selected_by_row[row] = denominator
            assert selected_by_row[row] == denominator
            total = _fraction(record["exact_feature_sum"])
            estimate = _fraction(record["estimate"])
            lower_bound = cast(Fraction, spec.feature_lower_bound)
            upper_bound = cast(Fraction, spec.feature_upper_bound)
            assert record["interval_method"] == (
                "bounded-feature-fixed-range-halfwidth-clipped-to-bounds"
            )
            if denominator == 0:
                assert total is estimate is None
                assert record["interval_state"] == "insufficient-selection"
                assert record["interval_lower"] is record["interval_upper"] is None
            else:
                feature_present += 1
                assert total is not None and estimate == total / denominator
                assert lower_bound <= estimate <= upper_bound
                if denominator < 1_040:
                    assert record["interval_state"] == "insufficient-selection"
                    assert record["interval_lower"] is record["interval_upper"] is None
                else:
                    feature_intervals += 1
                    halfwidth = (upper_bound - lower_bound) * Fraction(3, 40)
                    assert record["interval_state"] == "computed"
                    assert _fraction(record["interval_lower"]) == max(
                        lower_bound, estimate - halfwidth
                    )
                    assert _fraction(record["interval_upper"]) == min(
                        upper_bound, estimate + halfwidth
                    )

    selected = tuple(cast(int, value) for value in selected_by_row)
    assert tuple(observable_by_row) == (_N,) * _ROW_COUNT
    if expected_selected is not None:
        assert selected == expected_selected
    assert crosswalk.hexdigest() == _CP61_CROSSWALK_SHA256
    assert summary.ordered_cp61_inventory_crosswalk_sha256 == _CP61_CROSSWALK_SHA256
    assert summary.ordered_estimand_record_sha256s_sha256 == ordered.hexdigest()
    assert (
        summary.output_body_sha256
        == hashlib.sha256(_OUTPUT_BODY_DOMAIN + b"\0" + payload).hexdigest()
    )
    assert summary.output_canonical_json_bytes == len(payload)
    assert summary.output_canonical_json_sha256 == hashlib.sha256(payload).hexdigest()
    assert summary.declared_total_input_bytes == root["total_input_bytes"]
    assert (
        summary.declared_input_stream_commitment_sha256
        == root["input_stream_commitment_sha256"]
    )
    assert (
        summary.declared_ordered_interchange_record_sha256
        == root["ordered_interchange_record_sha256"]
    )
    assert (
        summary.declared_ordered_projection_sha256 == root["ordered_projection_sha256"]
    )
    assert (
        summary.declared_ordered_seed_ordinal_plan_seed_sha256
        == root["ordered_seed_ordinal_plan_seed_sha256"]
    )
    assert (
        summary.declared_ordered_request_instance_sha256
        == root["ordered_request_instance_sha256"]
    )
    assert (
        summary.declared_ordered_stable_trace_sha256
        == root["ordered_stable_trace_sha256"]
    )
    assert summary.declared_runtime_lock_sha256 == root["runtime_lock_sha256"]
    assert summary.stream_commitment_coherence_verified is True
    assert summary.selected_counts_by_row == selected
    assert summary.observable_row_sums == (_N,) * _ROW_COUNT
    assert summary.rejection_first_attempt_row_sums == tuple(
        first_by_row[index] for index in (0, 1, 2, 3, 8, 9, 10, 11)
    )
    assert summary.feature_estimate_present_count == feature_present
    assert summary.feature_estimate_absent_count == _FEATURE_COUNT - feature_present
    assert summary.binomial_interval_count == _BINOMIAL_COUNT
    assert summary.feature_interval_count == feature_intervals
    assert summary.computed_interval_count == _BINOMIAL_COUNT + feature_intervals
    assert summary.insufficient_selection_count == _FEATURE_COUNT - feature_intervals
    assert summary.distinct_binomial_success_count_count == len(success_counts)
    assert summary.exact_endpoint_boundary_comparison_count == endpoint_comparisons
    for name in (
        "canonical_json_verified",
        "schema_verified",
        "estimand_inventory_and_order_verified",
        "record_digests_verified",
        "cross_record_arithmetic_verified",
        "exact_interval_arithmetic_verified",
    ):
        assert getattr(summary, name) is True
    for name in (
        "input_stream_relation_verified",
        "input_provenance_authenticated",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_made",
        "production_evidence",
    ):
        assert getattr(summary, name) is False
    _assert_record_digest(summary)


def test_cp72_frozen_constants_exports_and_signatures_are_exact() -> None:
    assert cp72.CP72_TEST28_SCHEMA_VERSION == _SCHEMA
    assert cp72.CP72_TEST28_SCOPE == _SCOPE
    assert cp72.CP72_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert cp72.CP72_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID == (
        "whole_seed_supplied_cp71_development_output_internal_validation_qualification"
    )
    assert cp72.CP72_TEST28_SEED_COUNT == 2_048
    assert cp72.CP72_TEST28_ROW_COUNT == 16
    assert cp72.CP72_TEST28_REQUEST_COUNT == 32_768
    assert cp72.CP72_TEST28_ESTIMAND_COUNT == 554
    assert cp72.CP72_TEST28_OBSERVABLE_ESTIMAND_COUNT == 72
    assert cp72.CP72_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT == 170
    assert cp72.CP72_TEST28_FEATURE_ESTIMAND_COUNT == 312
    assert cp72.CP72_TEST28_BINOMIAL_ESTIMAND_COUNT == 242
    assert cp72.CP72_TEST28_FAMILYWISE_ERROR_BUDGET == Fraction(1, 100)
    assert cp72.CP72_TEST28_PER_ESTIMATOR_ERROR_BUDGET == Fraction(1, 55_400)
    assert cp72.CP72_TEST28_PER_TAIL_ERROR_BUDGET == Fraction(1, 110_800)
    assert cp72.CP72_TEST28_CP_BISECTION_STEPS == 256
    assert cp72.CP72_TEST28_MINIMUM_SELECTED_COUNT == 1_040
    assert cp72.CP72_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER == Fraction(3, 40)
    assert cp72.CP72_TEST28_MAXIMUM_OUTPUT_BYTES == 8_388_608
    assert cp72.CP72_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES == 268_435_456
    assert cp72.CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES == 65_536
    assert cp72.CP72_TEST28_MAXIMUM_CANONICAL_DEPTH == 8
    assert cp72.CP72_TEST28_MAXIMUM_CANONICAL_NODES == 32_768
    assert cp72.CP72_TEST28_MAXIMUM_KEY_CHARACTERS == 64
    assert cp72.CP72_TEST28_MAXIMUM_TEXT_CHARACTERS == 4_096
    assert cp72.CP72_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS == 1_234
    assert cp72.CP72_TEST28_MAXIMUM_FRACTION_DECIMAL_DIGITS == 1_234
    assert cp72.CP72_TEST28_MAXIMUM_INTEGER_BITS == 4_096
    assert cp72.CP72_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT == 2_049
    assert cp72.CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY == 554
    assert (
        cp72.CP72_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY
        == cp72.CP72_TEST28_ESTIMAND_COUNT
    )
    assert cp72.CP72_TEST28_QUALIFICATION_FIXTURE_IDS == _FIXTURE_IDS
    assert cp72.CP72_TEST28_ERROR_CODES == _ERROR_CODES
    assert cp72.__all__ == _EXPECTED_ALL
    assert len(cp72.__all__) == len(set(cp72.__all__))
    assert all(hasattr(cp72, name) for name in cp72.__all__)
    assert tuple(
        inspect.signature(
            cp72.cp72_validate_supplied_cp71_development_output_bytes
        ).parameters
    ) == ("payload",)
    assert not any(
        token in name.lower()
        for name in cp72.__all__
        for token in (
            "path",
            "writer",
            "parser",
            "stream_reducer",
            "decision",
            "evidence",
        )
    )


def test_cp72_five_record_field_orders_and_domains_are_exact() -> None:
    for name, expected in _RECORD_FIELDS.items():
        cls = getattr(cp72, name)
        assert tuple(item.name for item in fields(cls)) == expected
        assert cls.__slots__ == expected
        assert cp72._RECORD_DOMAINS[cls] == _RECORD_DOMAINS[name]
    assert set(cp72._RECORD_DOMAINS) == {getattr(cp72, name) for name in _RECORD_FIELDS}


def test_cp72_source_is_stdlib_only_python39_and_has_one_public_data_api() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    compile(source, str(_SOURCE), "exec", ast.PyCF_ONLY_AST, optimize=0)
    try:
        compile(
            source,
            str(_SOURCE),
            "exec",
            ast.PyCF_ONLY_AST,
            dont_inherit=True,
            optimize=0,
            _feature_version=9,
        )
    except TypeError:
        pass
    imports = {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module not in (None, "__future__")
    }
    imports.update(
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert imports <= {
        "base64",
        "dataclasses",
        "fractions",
        "functools",
        "math",
        "hashlib",
        "hmac",
        "json",
        "threading",
        "typing",
        "weakref",
        "zlib",
    }
    assert "heterodiff" not in source
    assert "numpy" not in source
    public_defs = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("cp72_")
    ]
    assert public_defs == [
        "cp72_canonical_json_bytes",
        "cp72_sha256",
        "cp72_validate_supplied_cp71_development_output_bytes",
        "cp72_supplied_development_output_validation_qualification_bundle",
        "cp72_run_supplied_development_output_validation_qualification",
    ]
    forbidden_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "input",
    }
    assert (
        not {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        & forbidden_calls
    )


def test_cp72_bundle_contract_and_predecessor_pins_are_exact() -> None:
    bundle = cp72.cp72_supplied_development_output_validation_qualification_bundle()
    contract = bundle.validation_contract
    predecessor = bundle.predecessor_custody
    assert bundle.schema_version == _SCHEMA
    assert bundle.scope == _SCOPE
    assert bundle.blocker_ledger_prerequisite_id == (
        "whole_seed_supplied_cp71_development_output_internal_validation_qualification"
    )
    assert bundle.blocker_ledger_prerequisite_state == (
        "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS"
    )
    assert (
        bundle.blocker_ledger_total_count,
        bundle.blocker_ledger_satisfied_count,
        bundle.blocker_ledger_missing_count,
    ) == (27, 23, 4)
    assert bundle.qualification_fixture_ids == _FIXTURE_IDS
    assert bundle.qualification_fixture_specifications == (
        "exact-cp71-output-for-cp69-closed-baseline",
        "exact-cp71-output-for-all-selected-duplicate-pair-plan-seeds",
        "exact-cp71-output-for-all-nonselected-cyclic-statuses",
        "exact-cp71-output-for-novel-k-mixed-selection",
        "cp72-owned-internally-valid-nonfixture-output-with-sixteen-new-success-counts",
    )
    assert bundle.zero_argument_builder is True
    assert bundle.builder_validates is False
    assert bundle.qualification_runner_zero_argument is True
    assert bundle.public_supplied_output_validator_exposed is True
    assert bundle.public_caller_data_api_count == 1
    assert bundle.source_independent is bundle.stdlib_only is True
    for name in (
        "builder_validates",
        "public_parser_exposed",
        "public_stream_reducer_exposed",
        "public_raw_record_api_exposed",
        "public_stable_trace_api_exposed",
        "public_path_api_exposed",
        "public_writer_api_exposed",
        "public_primary_decision_threshold_api_exposed",
        "public_decision_api_exposed",
        "public_receipt_or_evidence_api_exposed",
        "project_modules_imported",
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
        "formal_test_28_closed",
    ):
        assert getattr(bundle, name) is False
    assert bundle.formal_test_28_status == "OPEN"

    assert contract.schema_version == _SCHEMA
    assert (
        contract.contract_id == "bounded-cp71-development-output-internal-validation-v1"
    )
    assert contract.source_output_schema_version == _CP71_OUTPUT_SCHEMA
    assert contract.source_interchange_schema_version == _CP69_SCHEMA
    assert contract.source_semantic_schema_version == _CP63_SCHEMA
    assert contract.input_type == "exact-built-in-bytes"
    assert contract.canonical_json_profile == (
        "ASCII-RFC8259-sort-keys-no-whitespace-no-float-no-duplicate-key-exact-bytes"
    )
    assert contract.exact_output_root_keys == _ROOT_KEYS
    assert contract.exact_estimand_record_keys == _ESTIMAND_KEYS
    assert contract.exact_stream_commitment_preimage_keys == _STREAM_PREIMAGE_KEYS
    assert (
        contract.request_count,
        contract.seed_count,
        contract.row_count,
        contract.estimand_count,
        contract.observable_estimand_count,
        contract.rejection_first_attempt_estimand_count,
        contract.feature_estimand_count,
        contract.binomial_estimand_count,
    ) == (32_768, 2_048, 16, 554, 72, 170, 312, 242)
    for name in (
        "exact_cp61_inventory_crosswalk_required",
        "exact_estimand_order_required",
        "record_digest_recomputed",
        "ordered_estimand_digest_computed",
        "output_body_digest_computed",
        "stream_commitment_internal_preimage_recomputed",
        "cross_record_arithmetic_validated",
        "exact_cp_endpoint_boundaries_validated",
        "feature_arithmetic_validated",
    ):
        assert getattr(contract, name) is True
    for name in (
        "input_stream_relation_verified",
        "input_provenance_authenticated",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "operational_coverage_claimed",
        "primary_thresholds_present",
        "decision_fields_present",
        "production_evidence_accepted",
    ):
        assert getattr(contract, name) is False
    assert contract.maximum_output_bytes == 8_388_608
    assert contract.maximum_declared_total_input_bytes == 268_435_456
    assert contract.maximum_output_record_bytes == 65_536
    assert contract.maximum_canonical_depth == 8
    assert contract.maximum_canonical_nodes == 32_768
    assert contract.maximum_key_characters == 64
    assert contract.maximum_text_characters == 4_096
    assert contract.maximum_integer_decimal_digits == 1_234
    assert contract.maximum_fraction_decimal_digits == 1_234
    assert contract.maximum_integer_bits == 4_096
    assert contract.maximum_cp_endpoint_cache_count == 2_049
    assert contract.maximum_output_vector_cardinality == 554
    assert contract.ordered_cp61_inventory_crosswalk_digest_domain == (
        _CP61_CROSSWALK_DOMAIN.decode("ascii")
    )
    assert contract.estimand_record_digest_domain == _OUTPUT_RECORD_DOMAIN.decode(
        "ascii"
    )
    assert contract.ordered_estimand_digest_domain == _ORDERED_RECORD_DOMAIN.decode(
        "ascii"
    )
    assert contract.output_body_digest_domain == _OUTPUT_BODY_DOMAIN.decode("ascii")
    assert contract.stream_commitment_digest_domain == _STREAM_COMMITMENT_DOMAIN.decode(
        "ascii"
    )

    protocol = _V22_PROTOCOL.read_bytes()
    manifest = _V22_MANIFEST.read_bytes()
    assert (
        predecessor.v22_protocol_sha256,
        predecessor.v22_protocol_bytes,
        predecessor.v22_protocol_lf_count,
    ) == (hashlib.sha256(protocol).hexdigest(), len(protocol), protocol.count(b"\n"))
    assert (
        predecessor.v22_manifest_sha256,
        predecessor.v22_manifest_bytes,
        predecessor.v22_manifest_lf_count,
    ) == (hashlib.sha256(manifest).hexdigest(), len(manifest), manifest.count(b"\n"))
    assert (
        predecessor.cp71_source_sha256
        == hashlib.sha256(_CP71_SOURCE.read_bytes()).hexdigest()
    )
    assert (
        predecessor.cp71_test_sha256
        == hashlib.sha256(_CP71_TEST.read_bytes()).hexdigest()
    )
    assert predecessor.cp71_bundle_record_sha256 == (
        "c49b4396c06f1ff792d2860176a2e318612bd12ad89ba3cf6f8804e2dc82169f"
    )
    assert predecessor.cp71_stream_contract_record_sha256 == (
        "5aca44ab2240dfd9040ca3323b7306b12bbe6ee47a2c0af3128002b387f3236c"
    )
    assert predecessor.cp71_output_contract_record_sha256 == (
        "13a76a7ce7b0c665ef33aa6e55c122c87bf61aa676530c984ce2fdaf63e345a3"
    )
    assert predecessor.cp71_qualification_record_sha256 == (
        "aa25726473f54c17b3179ebabbaace3671e9815a6d3b4eec834ad6c1b8490611"
    )
    assert predecessor.cp71_fixture_set_sha256 == (
        "bb4347afaca9e0ea41cb5b38ac74a3186b63fd95da9b4546b50de6aa1ffa83af"
    )
    assert predecessor.cp71_fixture_output_canonical_json_bytes == _CP71_FIXTURE_BYTES
    assert (
        predecessor.cp71_fixture_output_canonical_json_sha256s == _CP71_FIXTURE_SHA256S
    )
    for record in (predecessor, contract, bundle):
        _assert_record_digest(record)


@pytest.mark.parametrize(
    "fixture_id,expected_bytes,expected_sha,expected_selected,computed,insufficient",
    tuple(
        zip(
            _FIXTURE_IDS[:4],
            _CP71_FIXTURE_BYTES,
            _CP71_FIXTURE_SHA256S,
            _SELECTED_COUNTS[:4],
            _COMPUTED_COUNTS[:4],
            _INSUFFICIENT_COUNTS[:4],
        )
    ),
)
def test_cp72_accepts_and_independently_checks_all_four_cp71_dynamic_outputs(
    fixture_id: str,
    expected_bytes: int,
    expected_sha: str,
    expected_selected: Tuple[int, ...],
    computed: int,
    insufficient: int,
) -> None:
    payload = _cp71_fixture_output(fixture_id)
    assert len(payload) == expected_bytes
    assert hashlib.sha256(payload).hexdigest() == expected_sha
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
    assert summary.computed_interval_count == computed
    assert summary.insufficient_selection_count == insufficient
    _assert_output_and_summary(payload, summary, expected_selected)


def test_cp72_accepts_actual_nonfixture_cp71_output_without_hash_allowlisting() -> None:
    payload = _cp71_nonfixture_output()
    digest = hashlib.sha256(payload).hexdigest()
    assert digest not in _CP71_FIXTURE_SHA256S
    assert (
        digest
        not in cp72.cp72_supplied_development_output_validation_qualification_bundle().predecessor_custody.cp71_fixture_output_canonical_json_sha256s
    )
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
    assert summary.input_stream_relation_verified is False
    assert summary.input_provenance_authenticated is False
    _assert_output_and_summary(payload, summary, (0,) * 16)


def test_cp72_qualification_builder_exactly_reconstructs_four_cp71_outputs_and_fifth() -> None:
    for fixture_id in _FIXTURE_IDS[:4]:
        assert _cp72_qualification_fixture_output(fixture_id) == _cp71_fixture_output(
            fixture_id
        )

    payload = _cp72_qualification_fixture_output(_FIXTURE_IDS[-1])
    assert len(payload) == _QUALIFICATION_OUTPUT_BYTES[-1]
    assert hashlib.sha256(payload).hexdigest() == _QUALIFICATION_OUTPUT_SHA256S[-1]
    assert hashlib.sha256(payload).hexdigest() not in _CP71_FIXTURE_SHA256S
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
    _assert_output_and_summary(payload, summary, _SELECTED_COUNTS[-1])
    assert summary.computed_interval_count == _COMPUTED_COUNTS[-1]
    assert summary.insufficient_selection_count == _INSUFFICIENT_COUNTS[-1]
    assert summary.input_stream_relation_verified is False


def test_cp72_zero_argument_qualification_receipt_is_exact_bounded_and_nonclaiming(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("qualification reached host I/O or nondeterminism")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "urandom", forbidden)
    qualification = cp72.cp72_run_supplied_development_output_validation_qualification()
    assert (
        cp72.cp72_run_supplied_development_output_validation_qualification()
        is qualification
    )
    assert qualification.schema_version == _SCHEMA
    assert qualification.fixture_ids == _FIXTURE_IDS
    assert qualification.fixture_output_canonical_json_bytes == (
        _QUALIFICATION_OUTPUT_BYTES
    )
    assert qualification.fixture_output_canonical_json_sha256s == (
        _QUALIFICATION_OUTPUT_SHA256S
    )
    assert qualification.fixture_selected_counts_by_row == _SELECTED_COUNTS
    assert qualification.fixture_computed_interval_counts == _COMPUTED_COUNTS
    assert qualification.fixture_insufficient_selection_counts == (_INSUFFICIENT_COUNTS)
    assert qualification.fixture_count == 5
    assert qualification.module_owned_total_output_bytes == 3_526_086
    assert qualification.module_owned_peak_input_payload_count == 1
    assert qualification.module_owned_peak_parsed_output_count == 1
    assert (
        qualification.maximum_simultaneously_materialized_estimand_record_count == 1_108
    )
    assert qualification.sealed_summary_snapshot_retained_while_summary_live is True
    assert qualification.source_independent is qualification.stdlib_only is True
    assert qualification.production_gate_13_state == "MISSING"
    assert qualification.production_gate_14_state == "MISSING"
    assert qualification.production_evidence_present_count == 0
    assert qualification.all_development_qualification_checks_passed is True
    for name in (
        "module_owned_output_payload_or_body_cached",
        "caller_output_retained_after_successful_return",
        "module_direct_filesystem_read",
        "module_direct_filesystem_write",
        "module_direct_clock_read",
        "module_direct_rng_used",
        "module_direct_network_used",
        "module_direct_subprocess_used",
        "input_stream_relation_verified",
        "provenance_authenticated",
        "production_recomputation_performed",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_path_qualified",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
    ):
        assert getattr(qualification, name) is False
    assert qualification.fixture_validation_summary_record_sha256s == (
        _QUALIFICATION_SUMMARY_RECORD_SHA256S
    )
    for digest in qualification.fixture_validation_summary_record_sha256s:
        assert type(digest) is str and len(digest) == 64
        assert bytes.fromhex(digest).hex() == digest
    fixture_set_body = {
        "fixture_ids": qualification.fixture_ids,
        "fixture_validation_summary_record_sha256s": (
            qualification.fixture_validation_summary_record_sha256s
        ),
        "fixture_output_canonical_json_bytes": (
            qualification.fixture_output_canonical_json_bytes
        ),
        "fixture_output_canonical_json_sha256s": (
            qualification.fixture_output_canonical_json_sha256s
        ),
        "fixture_selected_counts_by_row": qualification.fixture_selected_counts_by_row,
        "fixture_computed_interval_counts": qualification.fixture_computed_interval_counts,
        "fixture_insufficient_selection_counts": (
            qualification.fixture_insufficient_selection_counts
        ),
    }
    assert qualification.fixture_set_sha256 == _tagged_sha(
        _QUALIFICATION_FIXTURE_SET_DOMAIN, fixture_set_body
    )
    assert qualification.fixture_set_sha256 == _QUALIFICATION_FIXTURE_SET_SHA256
    assert qualification.record_sha256 == _QUALIFICATION_RECORD_SHA256
    assert len(cp72.cp72_canonical_json_bytes(qualification)) == 2_860
    assert cp72.cp72_sha256(qualification) == _QUALIFICATION_PUBLIC_SHA256
    _assert_record_digest(qualification)
    assert not any(
        type(value) is bytes and len(value) in _QUALIFICATION_OUTPUT_BYTES
        for value in vars(cp72).values()
    )
    gc.collect()
    assert not any(
        type(record) is cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1
        for record in cp72._ISSUED_RECORD_SNAPSHOTS
    )


def test_cp72_qualification_failure_is_atomic_and_memoryerror_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = len(cp72._ISSUED_RECORD_SNAPSHOTS)
    monkeypatch.setattr(cp72, "_QUALIFICATION_CACHE", None)

    def exhausted(*_args: object, **_kwargs: object) -> object:
        raise MemoryError("hostile")

    monkeypatch.setattr(cp72, "_build_qualification_fixture_output", exhausted)
    _error_code(
        cp72.cp72_run_supplied_development_output_validation_qualification,
        "RESOURCE_EXHAUSTED",
    )
    assert cp72._QUALIFICATION_CACHE is None
    gc.collect()
    assert len(cp72._ISSUED_RECORD_SNAPSHOTS) == before


def test_cp72_cold_qualification_cache_is_serialized_and_issues_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    qualification = cp72.cp72_run_supplied_development_output_validation_qualification()
    calls: List[int] = []

    def build_once() -> object:
        calls.append(1)
        return qualification

    monkeypatch.setattr(cp72, "_QUALIFICATION_CACHE", None)
    monkeypatch.setattr(cp72, "_run_qualification_uncached", build_once)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda _index: cp72.cp72_run_supplied_development_output_validation_qualification(),
                range(32),
            )
        )
    assert calls == [1]
    assert all(result is qualification for result in results)


@pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit, GeneratorExit))
def test_cp72_qualification_control_flow_exceptions_are_never_normalized(
    monkeypatch: pytest.MonkeyPatch, exception: type
) -> None:
    monkeypatch.setattr(cp72, "_QUALIFICATION_CACHE", None)

    def interrupted() -> object:
        raise exception()

    monkeypatch.setattr(cp72, "_run_qualification_uncached", interrupted)
    with pytest.raises(exception):
        cp72.cp72_run_supplied_development_output_validation_qualification()
    assert cp72._QUALIFICATION_CACHE is None


def test_cp72_qualification_unexpected_exception_has_stable_code_and_no_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cp72, "_QUALIFICATION_CACHE", None)

    def broken() -> object:
        raise RuntimeError("hostile")

    monkeypatch.setattr(cp72, "_run_qualification_uncached", broken)
    _error_code(
        cp72.cp72_run_supplied_development_output_validation_qualification,
        "INTERNAL_INVARIANT_FAILED",
    )
    assert cp72._QUALIFICATION_CACHE is None


@pytest.mark.parametrize(
    "payload,code",
    (
        (bytearray(b"{}"), "INPUT_TYPE_MISMATCH"),
        (memoryview(b"{}"), "INPUT_TYPE_MISMATCH"),
        ("{}", "INPUT_TYPE_MISMATCH"),
        (b"", "INPUT_BYTE_LIMIT"),
        (b"\xef\xbb\xbf{}", "INPUT_ENCODING_INVALID"),
        (b"\xff", "INPUT_ENCODING_INVALID"),
        (b"{", "INPUT_JSON_INVALID"),
        (b'{"x":1,"x":2}', "INPUT_JSON_INVALID"),
        (b'{"x":1.0}', "INPUT_JSON_INVALID"),
        (b'{"x":NaN}', "INPUT_JSON_INVALID"),
        (rb'{"x":"\ud800"}', "INPUT_ENCODING_INVALID"),
        (rb'{"\ud800":0}', "INPUT_ENCODING_INVALID"),
        (b" {}", "INPUT_CANONICAL_MISMATCH"),
        (b'{"z":0,"a":0}', "INPUT_CANONICAL_MISMATCH"),
        (rb'{"x":"\u0061"}', "INPUT_CANONICAL_MISMATCH"),
    ),
)
def test_cp72_lexical_and_exact_bytes_fail_with_stable_precedence(
    payload: object, code: str
) -> None:
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(payload),
        code,
    )


def test_cp72_byte_cap_precedes_decoding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cp72, "CP72_TEST28_MAXIMUM_OUTPUT_BYTES", 2)

    def forbidden_decode(_payload: object) -> object:
        raise AssertionError("decoder reached past byte cap")

    monkeypatch.setattr(cp72, "_scan_json_lexical", forbidden_decode)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(b"xxx"),
        "INPUT_BYTE_LIMIT",
    )


@pytest.mark.parametrize(
    "payload",
    (
        _canonical({"x" * 65: 0}),
        _canonical({"x": "x" * 4_097}),
        _canonical({"x": [0] * 32_768}),
        _canonical([[[[[[[[[0]]]]]]]]]),
        b'{"x":' + b"1" * 1_235 + b"}",
    ),
)
def test_cp72_lexical_structural_resource_caps_are_enforced(payload: bytes) -> None:
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(payload),
        "INPUT_RESOURCE_LIMIT",
    )


def test_cp72_resource_caps_have_exact_monkeypatched_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    monkeypatch.setattr(cp72, "CP72_TEST28_MAXIMUM_OUTPUT_BYTES", len(payload))
    assert cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
    monkeypatch.setattr(cp72, "CP72_TEST28_MAXIMUM_OUTPUT_BYTES", len(payload) - 1)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(payload),
        "INPUT_BYTE_LIMIT",
    )


@pytest.mark.parametrize(
    "mutation,code",
    (
        (lambda root: root.pop("schema_version"), "INPUT_FIELD_SET_MISMATCH"),
        (lambda root: root.update(extra_field=0), "INPUT_FIELD_SET_MISMATCH"),
        (
            lambda root: root.__setitem__("schema_version", 1),
            "INPUT_FIELD_TYPE_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("request_count", True),
            "INPUT_FIELD_TYPE_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("estimand_estimate_intervals", {}),
            "INPUT_FIELD_TYPE_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("schema_version", "cp72-wrong"),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("request_count", 32_767),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("input_provenance_authenticated", True),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("source_law_verified", True),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("external_seed_source_verified", True),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("runtime_lock_authenticated", True),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__(
                "request_instance_sha256_authenticated", True
            ),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("stable_trace_sha256_authenticated", True),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__(
                "cp61_estimand_digest_is_inventory_reference_only", False
            ),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("cp61_estimand_semantics_realized", True),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__(
                "production_attempt_validity_evaluated", True
            ),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("production_recomputation", True),
            "INPUT_SCHEMA_MISMATCH",
        ),
        (
            lambda root: root.__setitem__("arithmetic_transform_only", False),
            "INPUT_SCHEMA_MISMATCH",
        ),
    ),
)
def test_cp72_root_field_types_fixed_claims_and_nonclaims_fail_closed(
    mutation: Callable[[dict], object], code: str
) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    mutation(root)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        code,
    )


@pytest.mark.parametrize(
    "value,code",
    (
        (True, "INPUT_FIELD_TYPE_MISMATCH"),
        (-1, "INPUT_INVENTORY_MISMATCH"),
        (32_767, "INPUT_INVENTORY_MISMATCH"),
        (268_435_457, "INPUT_INVENTORY_MISMATCH"),
    ),
)
def test_cp72_declared_input_byte_range_rejects_impossible_values_even_with_repaired_commitment(
    value: object, code: str
) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    root["total_input_bytes"] = value
    _repair_stream_commitment(root)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        code,
    )


@pytest.mark.parametrize("value", (32_768, 268_435_456))
def test_cp72_declared_input_byte_range_endpoints_are_coherence_only(
    value: int,
) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    root["total_input_bytes"] = value
    _repair_stream_commitment(root)
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(
        _canonical(root)
    )
    assert summary.declared_total_input_bytes == value
    assert summary.stream_commitment_coherence_verified is True
    assert summary.input_stream_relation_verified is False
    assert summary.input_provenance_authenticated is False


def test_cp72_opaque_digest_changes_are_accepted_only_with_coherent_commitment() -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    root = _decode(payload)
    ordinary = cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
    for index, name in enumerate(_STREAM_PREIMAGE_KEYS[2:], 10):
        root[name] = f"{index:064x}"
    broken = _canonical(root)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(broken),
        "INPUT_COMMITMENT_MISMATCH",
    )
    _repair_stream_commitment(root)
    supplied = cp72.cp72_validate_supplied_cp71_development_output_bytes(
        _canonical(root)
    )
    assert (
        supplied.output_canonical_json_sha256 != ordinary.output_canonical_json_sha256
    )
    assert supplied.ordered_estimand_record_sha256s_sha256 == (
        ordinary.ordered_estimand_record_sha256s_sha256
    )
    assert supplied.stream_commitment_coherence_verified is True
    assert supplied.input_stream_relation_verified is False
    assert supplied.input_provenance_authenticated is False


@pytest.mark.parametrize("key", _ESTIMAND_KEYS)
def test_cp72_rejects_every_estimand_record_field_deletion(key: str) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    del root["estimand_estimate_intervals"][0][key]
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_FIELD_SET_MISMATCH",
    )


@pytest.mark.parametrize("variant", ("short", "long", "reordered", "replayed"))
def test_cp72_rejects_wrong_vector_cardinality_order_and_replay(variant: str) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    records = root["estimand_estimate_intervals"]
    if variant == "short":
        records.pop()
    elif variant == "long":
        records.append(dict(records[-1]))
    elif variant == "reordered":
        records[0], records[1] = records[1], records[0]
    else:
        records[1] = dict(records[0])
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_RESOURCE_LIMIT" if variant == "long" else "INPUT_INVENTORY_MISMATCH",
    )


@pytest.mark.parametrize(
    "field,value,repair,code",
    (
        ("estimand_ordinal", True, True, "INPUT_FIELD_TYPE_MISMATCH"),
        ("observable_cell_label", 1, True, "INPUT_FIELD_TYPE_MISMATCH"),
        ("record_sha256", "A" * 64, False, "INPUT_DIGEST_MISMATCH"),
        ("cp61_estimand_record_sha256", "g" * 64, True, "INPUT_DIGEST_MISMATCH"),
        ("development_supplied_input_only", False, True, "INPUT_SCHEMA_MISMATCH"),
        ("input_provenance_authenticated", True, True, "INPUT_SCHEMA_MISMATCH"),
        ("arithmetic_transform_only", False, True, "INPUT_SCHEMA_MISMATCH"),
    ),
)
def test_cp72_rejects_record_type_digest_and_claim_boundaries(
    field: str, value: object, repair: bool, code: str
) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    record = root["estimand_estimate_intervals"][0]
    record[field] = value
    if repair:
        _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        code,
    )


def test_cp72_rejects_cp61_crosswalk_and_record_digest_tamper_distinctly() -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    record = root["estimand_estimate_intervals"][0]
    record["record_sha256"] = "1" * 64
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_DIGEST_MISMATCH",
    )
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    record = root["estimand_estimate_intervals"][0]
    record["cp61_estimand_record_sha256"] = "1" * 64
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )


def test_cp72_rejects_binomial_estimate_and_exact_endpoint_tamper() -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    root = _decode(payload)
    record = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "observable-cell"
        and 0 < item["success_count"] < _N
    )
    record["estimate"] = {"$fraction": ["0", "1"]}
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_ARITHMETIC_MISMATCH",
    )

    root = _decode(payload)
    record = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "observable-cell"
        and 0 < item["success_count"] < _N
    )
    lower = cast(Fraction, _fraction(record["interval_lower"]))
    record["interval_lower"] = _to_plain(lower + Fraction(1, _CP_DENOMINATOR))
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_INTERVAL_MISMATCH",
    )


def test_cp72_rejects_feature_union_estimate_interval_and_cross_row_tamper() -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    record = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "selected-conditional-feature"
    )
    record["exact_feature_sum"] = {"$fraction": ["0", "1"]}
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_ARITHMETIC_MISMATCH",
    )

    root = _decode(_cp71_fixture_output("novel-k-mixed-selection"))
    record = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "selected-conditional-feature"
        and 0 < item["denominator_count"] < 1_040
    )
    record["interval_lower"] = record["feature_lower_bound"]
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_INTERVAL_MISMATCH",
    )

    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    record = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "selected-conditional-feature"
    )
    record.update(
        denominator_count=1,
        exact_feature_sum={"$fraction": ["0", "1"]},
        estimate={"$fraction": ["0", "1"]},
    )
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_ARITHMETIC_MISMATCH",
    )


@pytest.mark.parametrize(
    "tag,code",
    (
        ({"$fraction": ["01", "2"]}, "INPUT_ARITHMETIC_MISMATCH"),
        ({"$fraction": ["-0", "1"]}, "INPUT_ARITHMETIC_MISMATCH"),
        ({"$fraction": ["1", "0"]}, "INPUT_ARITHMETIC_MISMATCH"),
        ({"$fraction": ["2", "2"]}, "INPUT_ARITHMETIC_MISMATCH"),
        ({"$fraction": [1, "2"]}, "INPUT_ARITHMETIC_MISMATCH"),
        ({"$fraction": ["1"]}, "INPUT_ARITHMETIC_MISMATCH"),
        ({"fraction": ["1", "2"]}, "INPUT_ARITHMETIC_MISMATCH"),
        ({"$fraction": ["1" * 1_235, "2"]}, "INPUT_RESOURCE_LIMIT"),
        ({"$fraction": [str(1 << 4_096), "1"]}, "INPUT_RESOURCE_LIMIT"),
    ),
)
def test_cp72_rejects_noncanonical_or_overlimit_fraction_grammar(
    tag: object, code: str
) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    record = root["estimand_estimate_intervals"][0]
    record["estimate"] = tag
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        code,
    )


def test_cp72_rechecks_derived_fraction_bits_not_only_input_components() -> None:
    root = _decode(_cp71_fixture_output("all-selected-duplicate-pair-plan-seeds"))
    record = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "selected-conditional-feature"
        and _fraction(item["feature_lower_bound"]) == 0
    )
    denominator = (1 << 4_094) - 1
    assert denominator.bit_length() <= 4_096
    assert len(str(denominator)) <= 1_234
    record["exact_feature_sum"] = {"$fraction": ["1", str(denominator)]}
    _repair_estimand(record)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_RESOURCE_LIMIT",
    )


def test_cp72_record_and_endpoint_cache_caps_are_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    first = _decode(payload)["estimand_estimate_intervals"][0]
    monkeypatch.setattr(
        cp72, "CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES", len(_canonical(first)) - 1
    )
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(payload),
        "INPUT_RESOURCE_LIMIT",
    )
    monkeypatch.setattr(cp72, "CP72_TEST28_MAXIMUM_OUTPUT_RECORD_BYTES", 65_536)
    monkeypatch.setattr(cp72, "CP72_TEST28_MAXIMUM_CP_ENDPOINT_CACHE_COUNT", 0)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(payload),
        "INPUT_RESOURCE_LIMIT",
    )


def test_cp72_combined_hostiles_obey_global_failure_precedence() -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    root["runtime_lock_sha256"] = "G" * 64
    root["estimand_estimate_intervals"].pop()
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_DIGEST_MISMATCH",
    )

    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    root["runtime_lock_sha256"] = "1" * 64
    root["estimand_estimate_intervals"].pop()
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_COMMITMENT_MISMATCH",
    )

    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    early = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "observable-cell"
        and 0 < item["success_count"] < _N
    )
    lower = cast(Fraction, _fraction(early["interval_lower"]))
    early["interval_lower"] = _to_plain(lower + Fraction(1, _CP_DENOMINATOR))
    _repair_estimand(early)
    late = root["estimand_estimate_intervals"][-1]
    late["estimand_id"] = "cp61/wrong"
    _repair_estimand(late)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )

    # The full identity/order pass and CP61 crosswalk precede every CP71
    # estimand-body digest check, including a bad digest in the first record.
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    root["estimand_estimate_intervals"][0]["record_sha256"] = "1" * 64
    late = root["estimand_estimate_intervals"][-1]
    late["estimand_id"] = "cp61/wrong"
    _repair_estimand(late)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )

    # A complete CP61 crosswalk mismatch likewise precedes an earlier valid-
    # grammar but incorrect CP71 estimand-body digest.
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    root["estimand_estimate_intervals"][0]["record_sha256"] = "1" * 64
    late = root["estimand_estimate_intervals"][-1]
    late["cp61_estimand_record_sha256"] = "2" * 64
    _repair_estimand(late)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )

    # Every record and cross-record arithmetic identity precedes any exact
    # interval witness, even when the interval defect occurs first in order.
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    early = next(
        item
        for item in root["estimand_estimate_intervals"]
        if item["estimand_family"] == "observable-cell"
        and 0 < item["success_count"] < _N
    )
    early_lower = cast(Fraction, _fraction(early["interval_lower"]))
    early["interval_lower"] = _to_plain(early_lower + Fraction(1, _CP_DENOMINATOR))
    _repair_estimand(early)
    late = root["estimand_estimate_intervals"][-1]
    late_lower = cast(Fraction, _fraction(late["feature_lower_bound"]))
    late.update(
        denominator_count=1,
        exact_feature_sum=_to_plain(late_lower),
        estimate=_to_plain(late_lower),
    )
    _repair_estimand(late)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_ARITHMETIC_MISMATCH",
    )


@pytest.mark.parametrize("bound_name", ("feature_lower_bound", "feature_upper_bound"))
def test_cp72_late_raw_feature_bound_inventory_precedes_early_record_digest(
    bound_name: str,
) -> None:
    root = _decode(_cp71_fixture_output("all-nonselected-cyclic-statuses"))
    root["estimand_estimate_intervals"][0]["record_sha256"] = "1" * 64
    late = root["estimand_estimate_intervals"][-1]
    late[bound_name] = {"$fraction": ["1", "10"]}
    _repair_estimand(late)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )


def test_cp72_memoryerror_is_normalized_without_partial_summary_or_cache_damage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    before = len(cp72._ISSUED_RECORD_SNAPSHOTS)
    real_validate = cp72._validate_output_value

    def exhausted(_value: object, _payload: object) -> object:
        raise MemoryError("hostile")

    monkeypatch.setattr(cp72, "_validate_output_value", exhausted)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(payload),
        "RESOURCE_EXHAUSTED",
    )
    gc.collect()
    assert len(cp72._ISSUED_RECORD_SNAPSHOTS) == before
    monkeypatch.setattr(cp72, "_validate_output_value", real_validate)
    assert cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)


@pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit, GeneratorExit))
def test_cp72_control_flow_exceptions_are_never_normalized(
    monkeypatch: pytest.MonkeyPatch, exception: type
) -> None:
    def interrupted(_payload: object) -> object:
        raise exception()

    monkeypatch.setattr(cp72, "_decode_canonical_output_bytes", interrupted)
    with pytest.raises(exception):
        cp72.cp72_validate_supplied_cp71_development_output_bytes(b"{}")


def test_cp72_unexpected_internal_exception_has_stable_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(_payload: object) -> object:
        raise RuntimeError("hostile")

    monkeypatch.setattr(cp72, "_decode_canonical_output_bytes", broken)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(b"{}"),
        "INTERNAL_INVARIANT_FAILED",
    )


def test_cp72_invalid_calls_issue_no_partial_record() -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    root = _decode(payload)
    root["estimand_estimate_intervals"][0]["record_sha256"] = "1" * 64
    gc.collect()
    before = len(cp72._ISSUED_RECORD_SNAPSHOTS)
    _error_code(
        lambda: cp72.cp72_validate_supplied_cp71_development_output_bytes(
            _canonical(root)
        ),
        "INPUT_DIGEST_MISMATCH",
    )
    gc.collect()
    assert len(cp72._ISSUED_RECORD_SNAPSHOTS) == before


def test_cp72_records_are_sealed_nonconstructible_nonpickleable_and_weakly_held() -> None:
    _error_code(lambda: cp72.cp72_canonical_json_bytes({}), "RECORD_TYPE_MISMATCH")
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
    bundle = cp72.cp72_supplied_development_output_validation_qualification_bundle()
    qualification = cp72.cp72_run_supplied_development_output_validation_qualification()
    records = (
        bundle.predecessor_custody,
        bundle.validation_contract,
        summary,
        qualification,
        bundle,
    )
    for record in records:
        assert is_dataclass(record)
        assert not hasattr(record, "__dict__")
        assert weakref.ref(record)() is record
        with pytest.raises((AttributeError, TypeError)):
            record.record_sha256 = _ZERO_SHA256
        with pytest.raises(TypeError):
            type(record)()
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)

    for cls in (
        cp72.CP72PredecessorCustodyV1,
        cp72.CP72SuppliedDevelopmentOutputValidationContractV1,
        cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1,
        cp72.CP72SuppliedDevelopmentOutputValidationQualificationV1,
        cp72.CP72SuppliedDevelopmentOutputValidationQualificationBundleV1,
    ):
        forged = object.__new__(cls)
        _error_code(
            lambda forged=forged: cp72.cp72_canonical_json_bytes(forged),
            "RECORD_NOT_ISSUED",
        )
        with pytest.raises(TypeError):
            type("Hostile", (cls,), {})

    reference = weakref.ref(summary)
    assert reference() is summary
    del summary, records, record
    gc.collect()
    assert reference() is None


def test_cp72_mutation_and_nested_identity_substitution_fail_closed() -> None:
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(
        _cp71_fixture_output("all-nonselected-cyclic-statuses")
    )
    object.__setattr__(summary, "request_count", 0)
    _error_code(lambda: cp72.cp72_canonical_json_bytes(summary), "RECORD_TAMPERED")

    bundle = cp72.cp72_supplied_development_output_validation_qualification_bundle()
    original = bundle.predecessor_custody
    clone = object.__new__(cp72.CP72PredecessorCustodyV1)
    for item in fields(cp72.CP72PredecessorCustodyV1):
        object.__setattr__(clone, item.name, getattr(original, item.name))
    try:
        object.__setattr__(bundle, "predecessor_custody", clone)
        _error_code(lambda: cp72.cp72_canonical_json_bytes(bundle), "RECORD_TAMPERED")
    finally:
        object.__setattr__(bundle, "predecessor_custody", original)
    assert cp72.cp72_canonical_json_bytes(bundle)


def test_cp72_success_summary_retains_only_bounded_scalars_and_tuples() -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
    for item in fields(type(summary)):
        value = getattr(summary, item.name)
        assert type(value) in (bool, int, str, tuple)
        if type(value) is tuple:
            assert all(type(member) in (bool, int, str) for member in value)
    assert not any(
        type(getattr(summary, item.name)) in (bytes, bytearray, dict, list)
        for item in fields(type(summary))
    )
    assert not any(
        value == hashlib.sha256(payload).digest()
        for value in (getattr(summary, item.name) for item in fields(type(summary)))
    )


def test_cp72_validator_and_bundle_are_concurrently_deterministic() -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")

    def validate(_index: int) -> Tuple[bytes, object]:
        summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)
        return cp72.cp72_canonical_json_bytes(summary), summary

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(validate, range(8)))
        bundles = list(
            executor.map(
                lambda _index: cp72.cp72_supplied_development_output_validation_qualification_bundle(),
                range(16),
            )
        )
    assert len({snapshot for snapshot, _summary in results}) == 1
    assert len({id(summary) for _snapshot, summary in results}) == 8
    assert all(bundle is bundles[0] for bundle in bundles)


def test_cp72_bundle_and_validator_are_zero_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _cp71_fixture_output("all-nonselected-cyclic-statuses")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("host I/O or nondeterminism reached")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "urandom", forbidden)
    assert cp72.cp72_supplied_development_output_validation_qualification_bundle()
    assert cp72.cp72_validate_supplied_cp71_development_output_bytes(payload)


def test_cp72_locked_python39_import_builder_and_sealing_are_deterministic() -> None:
    assert _PYTHON39.is_file()
    bundle = cp72.cp72_supplied_development_output_validation_qualification_bundle()
    expected = (
        bundle.record_sha256,
        cp72.cp72_sha256(bundle),
        hashlib.sha256(cp72.cp72_canonical_json_bytes(bundle)).hexdigest(),
    )
    script = "\n".join(
        (
            "import hashlib, sys, weakref",
            "sys.path.insert(0, %r)" % str(_ROOT / "src"),
            "from heterodiff.evaluation import "
            "mixed_initializer_test28_supplied_development_output_validation_qualification as c",
            "assert sys.version_info[:2] == (3, 9)",
            "b = c.cp72_supplied_development_output_validation_qualification_bundle()",
            "assert not hasattr(b, '__dict__')",
            "assert weakref.ref(b)() is b",
            "f = object.__new__(c.CP72SuppliedDevelopmentOutputValidationSummaryV1)",
            "try:\n c.cp72_canonical_json_bytes(f)\n raise AssertionError('forgery accepted')\n"
            "except c.CP72SuppliedDevelopmentOutputValidationQualificationError as e:\n"
            " assert e.code == 'CP72_RECORD_NOT_ISSUED'",
            "p = c._build_qualification_fixture_output("
            "'all-nonselected-cyclic-statuses', c._qualification_cp_endpoints(), "
            "c._qualification_cp61_record_sha256s())",
            "s = c.cp72_validate_supplied_cp71_development_output_bytes(p)",
            "assert s.selected_counts_by_row == (0,) * 16",
            "assert s.computed_interval_count == 242",
            "assert s.input_stream_relation_verified is False",
            "print(b.record_sha256)",
            "print(c.cp72_sha256(b))",
            "print(hashlib.sha256(c.cp72_canonical_json_bytes(b)).hexdigest())",
        )
    )
    completed = subprocess.run(
        (str(_PYTHON39), "-I", "-c", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert tuple(completed.stdout.splitlines()) == expected
    assert completed.stderr == ""
