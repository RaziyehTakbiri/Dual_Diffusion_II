"""Independent hostile tests for the CP73 supplied stream/output relation."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
from functools import lru_cache
import gc
import hashlib
import inspect
import json
from pathlib import Path
import pickle
import subprocess
from typing import Callable, Iterable, Iterator, List, Mapping, Tuple, cast
import weakref

import heterodiff.evaluation.mixed_initializer_test28_supplied_development_output_validation_qualification as cp72
import heterodiff.evaluation.mixed_initializer_test28_supplied_interchange_recomputation_qualification as cp71
import heterodiff.evaluation.mixed_initializer_test28_supplied_stream_output_relation_qualification as cp73
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_supplied_stream_output_relation_qualification.py"
)
_V23_PROTOCOL = _ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v23.md"
_V23_MANIFEST = _ROOT / "research/fixtures/cp50_test28_mixed_initializer_v23.json"
_CP69_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_compact_projection_interchange_qualification.py"
)
_CP69_TEST = (
    _ROOT
    / "tests"
    / "unit"
    / "test_mixed_initializer_test28_compact_projection_interchange_qualification.py"
)
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
_CP72_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_supplied_development_output_validation_qualification.py"
)
_CP72_TEST = (
    _ROOT
    / "tests"
    / "unit"
    / "test_mixed_initializer_test28_supplied_development_output_validation_qualification.py"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")

_SCHEMA = "cp73-test28-supplied-stream-output-relation-qualification-v1"
_CP69_SCHEMA = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_SCHEMA = "cp63-test28-independent-compact-recomputation-v1"
_CP71_OUTPUT_SCHEMA = "cp71-test28-supplied-development-estimate-interval-output-v1"
_CP71_SUMMARY_SCHEMA = "cp71-test28-supplied-interchange-recomputation-qualification-v1"
_CP72_SUMMARY_SCHEMA = (
    "cp72-test28-supplied-development-output-validation-qualification-v1"
)
_PREREQUISITE_ID = (
    "whole_seed_supplied_cp69_interchange_to_cp71_development_output_exact_"
    "relation_qualification"
)
_PREREQUISITE_STATE = (
    "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_" "ARTIFACTS"
)
_PROJECT_MODULES = (
    "heterodiff.evaluation.mixed_initializer_test28_supplied_development_"
    "output_validation_qualification",
    "heterodiff.evaluation.mixed_initializer_test28_supplied_interchange_"
    "recomputation_qualification",
)
_PUBLIC_APIS = (
    "cp72_validate_supplied_cp71_development_output_bytes",
    "cp72_canonical_json_bytes",
    "cp72_sha256",
    "cp71_reduce_supplied_cp69_interchange_byte_stream",
    "cp71_canonical_json_bytes",
    "cp71_sha256",
)
_ERROR_NORMALIZATION = (
    "cp72-input-codes-to-cp73-output-validation-failed",
    "cp72-resource-exhausted-to-cp73-resource-exhausted",
    "cp72-internal-record-unknown-or-invalid-return-to-cp73-internal-invariant-failed",
    "cp71-caller-stream-input-aggregate-and-output-limit-codes-to-cp73-stream-recomputation-failed",
    "cp71-resource-exhausted-to-cp73-resource-exhausted",
    "cp71-internal-record-unknown-or-invalid-return-to-cp73-internal-invariant-failed",
    "direct-memoryerror-to-cp73-resource-exhausted",
    "keyboardinterrupt-systemexit-generatorexit-reraised",
    "unexpected-exception-to-cp73-internal-invariant-failed",
)
_FAILURE_PRECEDENCE = (
    "cp72-output-validation-error-before-any-stream-touch",
    "cp72-return-type-issuance-and-fixed-claim-invariant",
    "cp71-stream-recomputation-error",
    "cp71-return-type-issuance-and-fixed-claim-invariant",
    "exact-output-byte-relation-mismatch",
    "32-field-summary-crosscheck-and-fixed-claim-invariant",
    "cp73-summary-issuance",
)
_CROSSCHECK_FIELDS = (
    ("output_schema_version", "source_output_schema_version"),
    ("request_count", "request_count"),
    ("total_input_bytes", "declared_total_input_bytes"),
    (
        "input_stream_commitment_sha256",
        "declared_input_stream_commitment_sha256",
    ),
    (
        "ordered_interchange_record_sha256",
        "declared_ordered_interchange_record_sha256",
    ),
    ("ordered_projection_sha256", "declared_ordered_projection_sha256"),
    (
        "ordered_seed_ordinal_plan_seed_sha256",
        "declared_ordered_seed_ordinal_plan_seed_sha256",
    ),
    (
        "ordered_request_instance_sha256",
        "declared_ordered_request_instance_sha256",
    ),
    (
        "ordered_stable_trace_sha256",
        "declared_ordered_stable_trace_sha256",
    ),
    ("runtime_lock_sha256", "declared_runtime_lock_sha256"),
    ("selected_counts_by_row", "selected_counts_by_row"),
    ("observable_row_sums", "observable_row_sums"),
    (
        "rejection_first_attempt_row_sums",
        "rejection_first_attempt_row_sums",
    ),
    ("feature_estimate_present_count", "feature_estimate_present_count"),
    ("feature_estimate_absent_count", "feature_estimate_absent_count"),
    ("binomial_interval_count", "binomial_interval_count"),
    ("feature_interval_count", "feature_interval_count"),
    ("computed_interval_count", "computed_interval_count"),
    ("insufficient_selection_count", "insufficient_selection_count"),
    (
        "distinct_cp_success_count_count",
        "distinct_binomial_success_count_count",
    ),
    (
        "ordered_estimand_record_sha256s_sha256",
        "ordered_estimand_record_sha256s_sha256",
    ),
    ("output_body_sha256", "output_body_sha256"),
    ("output_canonical_json_bytes", "output_canonical_json_bytes"),
    ("output_canonical_json_sha256", "output_canonical_json_sha256"),
    ("input_provenance_authenticated", "input_provenance_authenticated"),
    ("source_law_verified", "source_law_verified"),
    (
        "production_attempt_validity_evaluated",
        "production_attempt_validity_evaluated",
    ),
    ("operational_prediction", "operational_prediction"),
    ("power_review_present", "power_review_present"),
    ("primary_thresholds_present", "primary_thresholds_present"),
    ("decision_made", "decision_made"),
    ("production_evidence", "production_evidence"),
)
_ERROR_CODES = (
    "CP73_OUTPUT_VALIDATION_FAILED",
    "CP73_STREAM_RECOMPUTATION_FAILED",
    "CP73_OUTPUT_RELATION_MISMATCH",
    "CP73_RESOURCE_EXHAUSTED",
    "CP73_RECORD_TYPE_MISMATCH",
    "CP73_RECORD_NOT_ISSUED",
    "CP73_RECORD_TAMPERED",
    "CP73_INTERNAL_INVARIANT_FAILED",
)
_ALL = (
    "CP73_TEST28_SCHEMA_VERSION",
    "CP73_TEST28_SCOPE",
    "CP73_TEST28_FORMAL_TEST_28_STATUS",
    "CP73_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP73_TEST28_SEED_COUNT",
    "CP73_TEST28_ROW_COUNT",
    "CP73_TEST28_REQUEST_COUNT",
    "CP73_TEST28_ESTIMAND_COUNT",
    "CP73_TEST28_PREDECESSOR_PROJECT_MODULES",
    "CP73_TEST28_PREDECESSOR_PUBLIC_APIS",
    "CP73_TEST28_SUMMARY_CROSSCHECK_FIELDS",
    "CP73_TEST28_SUMMARY_CROSSCHECK_FIELD_COUNT",
    "CP73_TEST28_MAXIMUM_INTERCHANGE_BYTES",
    "CP73_TEST28_MAXIMUM_STREAM_BYTES",
    "CP73_TEST28_MAXIMUM_OUTPUT_BYTES",
    "CP73_TEST28_MINIMUM_DECLARED_TOTAL_INPUT_BYTES",
    "CP73_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES",
    "CP73_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY",
    "CP73_TEST28_MAXIMUM_NEXT_CALLS",
    "CP73_TEST28_MAXIMUM_SEALED_RECORD_BYTES",
    "CP73_TEST28_ERROR_CODES",
    "CP73SuppliedStreamOutputRelationQualificationError",
    "CP73PredecessorCustodyV1",
    "CP73SuppliedStreamOutputRelationContractV1",
    "CP73SuppliedStreamOutputRelationSummaryV1",
    "CP73SuppliedStreamOutputRelationQualificationBundleV1",
    "cp73_canonical_json_bytes",
    "cp73_sha256",
    "cp73_validate_supplied_cp71_development_output_relation_to_cp69_"
    "interchange_stream",
    "cp73_supplied_stream_output_relation_qualification_bundle",
)

_PREDECESSOR_FIELDS = (
    "schema_version",
    "v23_protocol_sha256",
    "v23_protocol_bytes",
    "v23_protocol_lf_count",
    "v23_manifest_sha256",
    "v23_manifest_bytes",
    "v23_manifest_lf_count",
    "cp69_source_sha256",
    "cp69_test_sha256",
    "cp69_bundle_record_sha256",
    "cp69_interchange_contract_record_sha256",
    "cp69_full_stream_expectation_record_sha256",
    "cp69_qualification_record_sha256",
    "cp71_source_sha256",
    "cp71_test_sha256",
    "cp71_bundle_record_sha256",
    "cp71_stream_contract_record_sha256",
    "cp71_output_contract_record_sha256",
    "cp71_qualification_record_sha256",
    "cp71_fixture_set_sha256",
    "cp72_source_sha256",
    "cp72_test_sha256",
    "cp72_bundle_record_sha256",
    "cp72_validation_contract_record_sha256",
    "cp72_qualification_record_sha256",
    "cp72_fixture_set_sha256",
    "record_sha256",
)
_CONTRACT_FIELDS = (
    "schema_version",
    "contract_id",
    "source_interchange_schema_version",
    "source_semantic_schema_version",
    "source_output_schema_version",
    "cp71_reduction_summary_schema_version",
    "cp72_validation_summary_schema_version",
    "output_payload_exact_type",
    "interchange_payloads_consumption",
    "phase_order",
    "predecessor_error_normalization",
    "failure_precedence",
    "project_module_names",
    "predecessor_public_api_names",
    "project_modules_imported",
    "source_independent",
    "stdlib_only",
    "stdlib_only_beyond_exact_predecessor_modules",
    "third_party_modules_imported",
    "public_api_uses_predecessor_public_apis_only",
    "output_validation_completes_before_stream_iteration",
    "invalid_output_iter_calls",
    "invalid_output_next_calls",
    "invalid_output_close_calls",
    "cp72_validator_exact_call_count",
    "cp71_reducer_maximum_call_count",
    "cp71_reducer_exact_call_count_after_output_validation",
    "exact_output_byte_relation_required",
    "exact_output_byte_comparison",
    "summary_crosscheck_fields",
    "summary_crosscheck_field_count",
    "summary_crosscheck_required",
    "cp71_fixed_nonclaims_checked",
    "cp71_stream_coherence_claims_checked",
    "cp72_validation_claims_checked",
    "relation_verified_meaning",
    "caller_iterable_side_effects_qualified",
    "caller_iterable_retention_qualified",
    "caller_next_liveness_qualified",
    "iterator_close_called",
    "maximum_next_calls",
    "maximum_interchange_bytes",
    "maximum_stream_bytes",
    "maximum_output_bytes",
    "minimum_declared_total_input_bytes",
    "maximum_declared_total_input_bytes",
    "maximum_output_vector_cardinality",
    "maximum_sealed_record_bytes",
    "caller_output_bytes_returned",
    "recomputed_output_bytes_returned",
    "caller_summary_accepted",
    "predecessor_summary_returned",
    "scalar_summary_only",
    "caller_output_retained_after_successful_return",
    "recomputed_output_retained_after_successful_return",
    "module_owned_predecessor_summary_references_retained_after_successful_return",
    "predecessor_summary_issuance_on_late_failure_possible",
    "predecessor_weak_registry_entries_recoverable_after_all_strong_references_released",
    "exception_traceback_retention_qualified",
    "no_cp73_record_issued_before_relation_complete",
    "cp73_partial_return_on_failure",
    "dynamic_input_payload_or_output_body_cached",
    "sealed_summary_snapshot_retained_while_summary_live",
    "module_direct_filesystem_read",
    "module_direct_filesystem_write",
    "module_direct_clock_read",
    "module_direct_rng_used",
    "module_direct_network_used",
    "module_direct_subprocess_used",
    "input_provenance_authenticated",
    "runtime_lock_authenticated",
    "request_instance_sha256_authenticated",
    "stable_trace_sha256_authenticated",
    "external_seed_source_verified",
    "source_law_verified",
    "production_attempt_validity_evaluated",
    "production_recomputation_qualified",
    "operational_prediction",
    "power_review_present",
    "primary_thresholds_present",
    "decision_made",
    "production_evidence",
    "confirmatory_custody_present",
    "production_gate_13_state",
    "production_gate_14_state",
    "formal_test_28_status",
    "summary_crosscheck_digest_domain",
    "summary_crosscheck_digest_preimage",
    "record_sha256",
)
_SUMMARY_FIELDS = (
    "schema_version",
    "source_interchange_schema_version",
    "source_semantic_schema_version",
    "source_output_schema_version",
    "request_count",
    "total_input_bytes",
    "input_stream_commitment_sha256",
    "ordered_interchange_record_sha256",
    "ordered_projection_sha256",
    "ordered_seed_ordinal_plan_seed_sha256",
    "ordered_request_instance_sha256",
    "ordered_stable_trace_sha256",
    "runtime_lock_sha256",
    "runtime_lock_authenticated",
    "request_instance_sha256_authenticated",
    "stable_trace_sha256_authenticated",
    "feature_estimate_present_count",
    "feature_estimate_absent_count",
    "binomial_interval_count",
    "feature_interval_count",
    "computed_interval_count",
    "insufficient_selection_count",
    "distinct_binomial_success_count_count",
    "ordered_estimand_record_sha256s_sha256",
    "output_body_sha256",
    "output_canonical_json_bytes",
    "output_canonical_json_sha256",
    "cp71_reduction_summary_record_sha256",
    "cp71_reduction_summary_public_sha256",
    "cp72_validation_summary_record_sha256",
    "cp72_validation_summary_public_sha256",
    "cp72_ordered_cp61_inventory_crosswalk_sha256",
    "cp72_exact_endpoint_boundary_comparison_count",
    "summary_crosscheck_field_count",
    "summary_crosscheck_sha256",
    "output_validated_before_stream_iteration",
    "stream_recomputed_once",
    "output_bytes_exact_match",
    "summary_crosscheck_verified",
    "input_stream_relation_verified",
    "external_seed_source_verified",
    "production_recomputation",
    "input_provenance_authenticated",
    "source_law_verified",
    "production_attempt_validity_evaluated",
    "operational_prediction",
    "power_review_present",
    "primary_thresholds_present",
    "decision_made",
    "production_evidence",
    "record_sha256",
)
_BUNDLE_FIELDS = (
    "schema_version",
    "scope",
    "blocker_ledger_prerequisite_id",
    "blocker_ledger_prerequisite_state",
    "blocker_ledger_total_count",
    "blocker_ledger_satisfied_count",
    "blocker_ledger_missing_count",
    "predecessor_custody",
    "relation_contract",
    "zero_argument_builder",
    "builder_validates",
    "qualification_runner_exposed",
    "module_owned_fixture_count",
    "module_owned_stream_body_count",
    "module_owned_output_body_count",
    "external_test_qualification_required",
    "public_supplied_stream_output_relation_validator_exposed",
    "public_caller_data_api_count",
    "public_parser_exposed",
    "public_stream_reducer_exposed",
    "public_output_validator_exposed",
    "public_summary_input_api_exposed",
    "public_output_bytes_returned",
    "public_path_api_exposed",
    "public_writer_api_exposed",
    "public_runner_api_exposed",
    "public_primary_decision_threshold_api_exposed",
    "public_decision_api_exposed",
    "public_receipt_or_evidence_api_exposed",
    "project_modules_imported",
    "project_module_count",
    "source_independent",
    "stdlib_only",
    "stdlib_only_beyond_exact_predecessor_modules",
    "third_party_modules_imported",
    "predecessor_public_apis_only",
    "module_direct_filesystem_read",
    "module_direct_filesystem_write",
    "module_direct_clock_read",
    "module_direct_rng_used",
    "module_direct_network_used",
    "module_direct_subprocess_used",
    "production_execution_authorized",
    "production_recomputation_qualified",
    "unconditional_operational_predictions_produced",
    "power_review_present",
    "primary_thresholds_present",
    "confirmatory_custody_present",
    "runtime_lock_authenticated",
    "request_instance_sha256_authenticated",
    "stable_trace_sha256_authenticated",
    "production_gate_13_state",
    "production_gate_14_state",
    "runner_and_recomputation_blocker_closed",
    "unconditional_operational_predictions_blocker_closed",
    "power_and_thresholds_blocker_closed",
    "confirmatory_custody_blocker_closed",
    "formal_test_28_status",
    "formal_test_28_closed",
    "record_sha256",
)

_RECORD_DOMAINS = {
    "CP73PredecessorCustodyV1": b"cp73-test28-predecessor-custody-v1",
    "CP73SuppliedStreamOutputRelationContractV1": (
        b"cp73-test28-supplied-stream-output-relation-contract-v1"
    ),
    "CP73SuppliedStreamOutputRelationSummaryV1": (
        b"cp73-test28-supplied-stream-output-relation-summary-v1"
    ),
    "CP73SuppliedStreamOutputRelationQualificationBundleV1": (
        b"cp73-test28-supplied-stream-output-relation-qualification-bundle-v1"
    ),
}
_CROSSCHECK_DOMAIN = b"cp73-test28-supplied-stream-output-summary-crosscheck-v1"
_PUBLIC_DOMAIN = b"cp73-public-record-v1"
_ZERO_SHA256 = "0" * 64
_CP61_CROSSWALK_SHA256 = (
    "6861002c492af9f0a9f0212d954e4a0008bbeaa5749c23ec9ad5cb60c2c3da77"
)

_FIXTURE_IDS = (
    "cp69-closed-baseline",
    "all-selected-duplicate-pair-plan-seeds",
    "all-nonselected-cyclic-statuses",
    "novel-k-mixed-selection",
)
_FIXTURE_OUTPUT_BYTES = (708_081, 724_245, 678_667, 718_937)
_FIXTURE_OUTPUT_SHA256S = (
    "b910b776d16cfe97813c821cc6358f88c068240e5d62fe26a1b30ff96937f1a7",
    "f9096b3c15cea651567bd436715a90c7c381a69de4688023def289d96798d505",
    "751bcd5ee2cca38be9edf88a94a54b60195b7c042838976b1987f5e9886b8239",
    "277476d47ada68c122173b8d1e8f9d871ae6fcb63802931800c00553657dc7b1",
)
_CP71_SUMMARY_SHA256S = (
    "638d0450373f1f8b62df27af8106dba81a141999c5124f3830109723bbe575a6",
    "449deac5eeffa209cb2a93485374bec0b38cc3c05a1922c891866880c967328e",
    "908100bc0df23f8ea5811541b107c607ab6de9c1990738400787d375cb218a78",
    "6bd7c35ed3aaa7e540ec853d11dd0a87f156978c051e47ba0eac54f7f02f07d3",
)
_CP72_SUMMARY_SHA256S = (
    "ff8b5294298cf38ccafbaf58691338ff0f1b83a286a91adcd1cf307989122d38",
    "127f5628410f2516d7a0dd57071234bb4a96940be13710c5c30b822b9254e56c",
    "0e9a1e71e3f5fab294ed00cb87aff1ee34406c4618cc89d98a124c0e3a0b2a1c",
    "4c85890555732f7ce0c62b99eb0b69249584bf919c2afa68b835f9fd6f103b35",
)
_REAL_RELATION_SET_DOMAIN = b"cp73-test28-external-real-relation-summary-set-v1"
_REAL_RELATION_RECORD_SHA256S = (
    "91359483a9114844d2acc6a48effd71de5a8deacbe59aebf77fb2e35b5cc7f36",
    "ba7d49c58a872e240c5d50038dd7f6471abc2b20525a78cfd7b8c96cccccb374",
    "8ab074c208c1dc51abfcd95a4fd77cc4d911d944ebb1d73aa49e81fd639461d6",
    "4203a928b175b9b9c350af3b8616345665b93cbb217535ecdb6d761d66762fc4",
)
_REAL_RELATION_PUBLIC_SHA256S = (
    "436a8e94233218aaf8d745d63c3e09a363f4307d4e3b990cba317ad9c71c21fa",
    "0e05d7e3343b5bebf74c57f4370a62854d2a92c42da0f409a4f2fc76212428dd",
    "571a0bccbc4b2fdaebc24c73c6ecd2d7874117643169c35a267cf0977493e8f6",
    "adfcbc9658347f0ec317c315904f2191ee0d0f1b0c06cd6f2511015ee9013268",
)
_REAL_RELATION_CANONICAL_BYTES = (3_110, 3_106, 3_106, 3_108)
_REAL_RELATION_SET_SHA256 = (
    "701c6f0cb54c11ab52d1e85bf84f9ee75c7222fbd5ea3e89c807eab6555c2dda"
)

_PHASE_ORDER = (
    "cp72-output-validation-completes-before-any-stream-touch",
    "cp71-stream-recomputation-exactly-once",
    "exact-canonical-output-byte-comparison",
    "sealed-summary-32-field-crosscheck",
    "cp73-scalar-summary-issuance",
)
_CROSSCHECK_PREIMAGE = (
    "domain||NUL||canonical-json({field_pairs:[[cp71-field,cp72-field],...],"
    "values:[cp71-value,...]});tuple-values-as-json-arrays"
)


def _to_plain(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
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
    raise TypeError("unsupported independent canonical type: %r" % (type(value),))


def _canonical(value: object) -> bytes:
    return json.dumps(
        _to_plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _tagged(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _canonical(value)).hexdigest()


def _record_body(record: object) -> dict:
    return {item.name: getattr(record, item.name) for item in fields(type(record))}


def _assert_record(record: object) -> None:
    body = _record_body(record)
    supplied = body["record_sha256"]
    body["record_sha256"] = _ZERO_SHA256
    domain = _RECORD_DOMAINS[type(record).__name__]
    assert supplied == _tagged(domain, body)
    canonical = cp73.cp73_canonical_json_bytes(record)
    assert canonical == _canonical(record)
    expected_public = hashlib.sha256(
        _PUBLIC_DOMAIN
        + b"\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + canonical
    ).hexdigest()
    assert cp73.cp73_sha256(record) == expected_public


@lru_cache(maxsize=None)
def _fixture_output(fixture_id: str) -> bytes:
    payload = cp72._build_qualification_fixture_output(
        fixture_id,
        cp72._qualification_cp_endpoints(),
        cp72._qualification_cp61_record_sha256s(),
    )
    assert type(payload) is bytes
    index = _FIXTURE_IDS.index(fixture_id)
    assert len(payload) == _FIXTURE_OUTPUT_BYTES[index]
    assert hashlib.sha256(payload).hexdigest() == _FIXTURE_OUTPUT_SHA256S[index]
    return payload


@lru_cache(maxsize=1)
def _unrelated_cp72_valid_nonfixture_output() -> bytes:
    payload = cp72._build_qualification_fixture_output(
        "cp72-nonfixture-novel-success-counts",
        cp72._qualification_cp_endpoints(),
        cp72._qualification_cp61_record_sha256s(),
    )
    assert type(payload) is bytes
    assert len(payload) == 696_156
    assert hashlib.sha256(payload).hexdigest() == (
        "8411f6657d0b689e1c6c7be3ff9f54fb2aeb0db19d166310574c4a3ec7ac2607"
    )
    return payload


def _fixture_stream(fixture_id: str) -> Iterator[bytes]:
    yield from cp71._cp71_iter_fixture(fixture_id)


@lru_cache(maxsize=None)
def _fixture_cp72_summary(
    fixture_id: str,
) -> cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1:
    summary = cp72.cp72_validate_supplied_cp71_development_output_bytes(
        _fixture_output(fixture_id)
    )
    index = _FIXTURE_IDS.index(fixture_id)
    assert summary.record_sha256 == _CP72_SUMMARY_SHA256S[index]
    return summary


@lru_cache(maxsize=None)
def _real_fixture_relation(
    fixture_id: str,
) -> Tuple[cp73.CP73SuppliedStreamOutputRelationSummaryV1, Tuple[int, int, int]]:
    output = _fixture_output(fixture_id)
    stream = _StreamProbe(_fixture_stream(fixture_id))
    summary = cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
        output, stream
    )
    return summary, (stream.iter_calls, stream.next_calls, stream.close_calls)


def _error_code(call: Callable[[], object], expected: str) -> object:
    with pytest.raises(
        cp73.CP73SuppliedStreamOutputRelationQualificationError
    ) as caught:
        call()
    assert caught.value.code == expected
    assert str(caught.value)
    return caught.value


def _class_fields(cls: type) -> Tuple[str, ...]:
    return tuple(item.name for item in fields(cls))


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _issued_cp72_summary(
    output_payload: bytes = b"x", **overrides: object
) -> cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1:
    values = {
        "schema_version": _CP72_SUMMARY_SCHEMA,
        "source_output_schema_version": _CP71_OUTPUT_SCHEMA,
        "request_count": 32_768,
        "estimand_count": 554,
        "observable_estimand_count": 72,
        "rejection_first_attempt_estimand_count": 170,
        "feature_estimand_count": 312,
        "binomial_estimand_count": 242,
        "declared_total_input_bytes": 32_768,
        "declared_input_stream_commitment_sha256": "1" * 64,
        "declared_ordered_interchange_record_sha256": "2" * 64,
        "declared_ordered_projection_sha256": "3" * 64,
        "declared_ordered_seed_ordinal_plan_seed_sha256": "4" * 64,
        "declared_ordered_request_instance_sha256": "5" * 64,
        "declared_ordered_stable_trace_sha256": "6" * 64,
        "declared_runtime_lock_sha256": "7" * 64,
        "stream_commitment_coherence_verified": True,
        "ordered_cp61_inventory_crosswalk_sha256": _CP61_CROSSWALK_SHA256,
        "ordered_estimand_record_sha256s_sha256": "8" * 64,
        "output_body_sha256": "9" * 64,
        "output_canonical_json_bytes": len(output_payload),
        "output_canonical_json_sha256": hashlib.sha256(output_payload).hexdigest(),
        "canonical_json_verified": True,
        "schema_verified": True,
        "estimand_inventory_and_order_verified": True,
        "record_digests_verified": True,
        "cross_record_arithmetic_verified": True,
        "exact_interval_arithmetic_verified": True,
        "selected_counts_by_row": (0,) * 16,
        "observable_row_sums": (2_048,) * 16,
        "rejection_first_attempt_row_sums": (0,) * 8,
        "feature_estimate_present_count": 0,
        "feature_estimate_absent_count": 312,
        "binomial_interval_count": 242,
        "feature_interval_count": 0,
        "computed_interval_count": 242,
        "insufficient_selection_count": 312,
        "distinct_binomial_success_count_count": 1,
        "exact_endpoint_boundary_comparison_count": 0,
        "input_stream_relation_verified": False,
        "input_provenance_authenticated": False,
        "source_law_verified": False,
        "production_attempt_validity_evaluated": False,
        "operational_prediction": False,
        "power_review_present": False,
        "primary_thresholds_present": False,
        "decision_made": False,
        "production_evidence": False,
    }
    values.update(overrides)
    return cast(
        cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1,
        cp72._record(cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1, values),
    )


def _issued_cp71_summary(
    cp72_summary: cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1,
    output_payload: bytes = b"x",
    **overrides: object,
) -> cp71.CP71SuppliedDevelopmentReductionSummaryV1:
    values = {
        "schema_version": _CP71_SUMMARY_SCHEMA,
        "source_interchange_schema_version": _CP69_SCHEMA,
        "source_semantic_schema_version": _CP63_SCHEMA,
        "output_schema_version": _CP71_OUTPUT_SCHEMA,
        "request_count": 32_768,
        "seed_count": 2_048,
        "row_count": 16,
        "total_input_bytes": cp72_summary.declared_total_input_bytes,
        "input_stream_commitment_sha256": (
            cp72_summary.declared_input_stream_commitment_sha256
        ),
        "first_interchange_record_sha256": "a" * 64,
        "ordered_interchange_record_sha256": (
            cp72_summary.declared_ordered_interchange_record_sha256
        ),
        "ordered_projection_sha256": (cp72_summary.declared_ordered_projection_sha256),
        "ordered_seed_ordinal_plan_seed_sha256": (
            cp72_summary.declared_ordered_seed_ordinal_plan_seed_sha256
        ),
        "ordered_request_instance_sha256": (
            cp72_summary.declared_ordered_request_instance_sha256
        ),
        "ordered_stable_trace_sha256": (
            cp72_summary.declared_ordered_stable_trace_sha256
        ),
        "runtime_lock_sha256": cp72_summary.declared_runtime_lock_sha256,
        "distinct_plan_seed_count": 2_048,
        "duplicate_plan_seed_count": 0,
        "plan_seed_row_group_coherence_verified": True,
        "row_seed_free_request_sha256s_matched": True,
        "runtime_lock_stream_coherence_verified": True,
        "selected_counts_by_row": cp72_summary.selected_counts_by_row,
        "status_counts": (0, 4_096, 0, 9_560, 9_560, 9_552),
        "observable_row_sums": cp72_summary.observable_row_sums,
        "rejection_first_attempt_row_sums": (
            cp72_summary.rejection_first_attempt_row_sums
        ),
        "first_attempt_contribution_count": 0,
        "feature_contribution_count": 0,
        "aggregation_update_count": 32_768,
        "feature_estimate_present_count": (cp72_summary.feature_estimate_present_count),
        "feature_estimate_absent_count": (cp72_summary.feature_estimate_absent_count),
        "binomial_interval_count": cp72_summary.binomial_interval_count,
        "feature_interval_count": cp72_summary.feature_interval_count,
        "computed_interval_count": cp72_summary.computed_interval_count,
        "insufficient_selection_count": cp72_summary.insufficient_selection_count,
        "distinct_cp_success_count_count": (
            cp72_summary.distinct_binomial_success_count_count
        ),
        "ordered_estimand_record_sha256s_sha256": (
            cp72_summary.ordered_estimand_record_sha256s_sha256
        ),
        "output_body_sha256": cp72_summary.output_body_sha256,
        "output_canonical_json_bytes": len(output_payload),
        "output_canonical_json_sha256": hashlib.sha256(output_payload).hexdigest(),
        "input_provenance_authenticated": False,
        "external_seed_source_verified": False,
        "source_law_verified": False,
        "production_attempt_validity_evaluated": False,
        "production_recomputation": False,
        "operational_prediction": False,
        "power_review_present": False,
        "primary_thresholds_present": False,
        "decision_made": False,
        "production_evidence": False,
    }
    values.update(overrides)
    return cast(
        cp71.CP71SuppliedDevelopmentReductionSummaryV1,
        cp71._record(cp71.CP71SuppliedDevelopmentReductionSummaryV1, values),
    )


def _install_synthetic_success(
    monkeypatch: pytest.MonkeyPatch, output_payload: bytes = b"x"
) -> Tuple[
    cp71.CP71SuppliedDevelopmentReductionSummaryV1,
    cp72.CP72SuppliedDevelopmentOutputValidationSummaryV1,
]:
    cp72_summary = _issued_cp72_summary(output_payload)
    cp71_summary = _issued_cp71_summary(cp72_summary, output_payload)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(
        cp73,
        "_CP71_REDUCE",
        lambda _payloads: (output_payload, cp71_summary),
    )
    return cp71_summary, cp72_summary


class _StreamProbe:
    def __init__(self, payloads: Iterable[bytes] = ()) -> None:
        self.payloads = iter(payloads)
        self.iter_calls = 0
        self.next_calls = 0
        self.close_calls = 0

    def __iter__(self) -> "_StreamProbe":
        self.iter_calls += 1
        return self

    def __next__(self) -> bytes:
        self.next_calls += 1
        return next(self.payloads)

    def close(self) -> None:
        self.close_calls += 1


def _raising(error: BaseException) -> Callable[..., object]:
    def call(*_args: object, **_kwargs: object) -> object:
        raise error

    return call


def _assert_wrapped_error(
    call: Callable[[], object],
    expected: str,
    predecessor_code: object,
    cause_type: type,
) -> None:
    with pytest.raises(
        cp73.CP73SuppliedStreamOutputRelationQualificationError
    ) as caught:
        call()
    assert caught.value.code == expected
    assert caught.value.predecessor_error_code == predecessor_code
    assert type(caught.value.__cause__) is cause_type
    assert "hostile" not in str(caught.value)


def _unissued_copy(record: object) -> object:
    clone = object.__new__(type(record))
    for item in fields(type(record)):
        object.__setattr__(clone, item.name, getattr(record, item.name))
    return clone


def test_cp73_public_surface_constants_and_exact_record_fields() -> None:
    assert cp73.__all__ == _ALL
    assert len(cp73.__all__) == 30
    assert cp73.CP73_TEST28_SCHEMA_VERSION == _SCHEMA
    assert cp73.CP73_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert cp73.CP73_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID == _PREREQUISITE_ID
    assert cp73.CP73_TEST28_SEED_COUNT == 2_048
    assert cp73.CP73_TEST28_ROW_COUNT == 16
    assert cp73.CP73_TEST28_REQUEST_COUNT == 32_768
    assert cp73.CP73_TEST28_ESTIMAND_COUNT == 554
    assert cp73.CP73_TEST28_PREDECESSOR_PROJECT_MODULES == _PROJECT_MODULES
    assert cp73.CP73_TEST28_PREDECESSOR_PUBLIC_APIS == _PUBLIC_APIS
    assert cp73.CP73_TEST28_SUMMARY_CROSSCHECK_FIELDS == _CROSSCHECK_FIELDS
    assert cp73.CP73_TEST28_SUMMARY_CROSSCHECK_FIELD_COUNT == 32
    assert cp73.CP73_TEST28_MAXIMUM_INTERCHANGE_BYTES == 65_536
    assert cp73.CP73_TEST28_MAXIMUM_STREAM_BYTES == 268_435_456
    assert cp73.CP73_TEST28_MAXIMUM_OUTPUT_BYTES == 8_388_608
    assert cp73.CP73_TEST28_MINIMUM_DECLARED_TOTAL_INPUT_BYTES == 32_768
    assert cp73.CP73_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES == 268_435_456
    assert cp73.CP73_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY == 554
    assert cp73.CP73_TEST28_MAXIMUM_NEXT_CALLS == 32_769
    assert cp73.CP73_TEST28_MAXIMUM_SEALED_RECORD_BYTES == 1_048_576
    assert cp73.CP73_TEST28_ERROR_CODES == _ERROR_CODES
    assert _class_fields(cp73.CP73PredecessorCustodyV1) == _PREDECESSOR_FIELDS
    assert (
        _class_fields(cp73.CP73SuppliedStreamOutputRelationContractV1)
        == _CONTRACT_FIELDS
    )
    assert (
        _class_fields(cp73.CP73SuppliedStreamOutputRelationSummaryV1) == _SUMMARY_FIELDS
    )
    assert (
        _class_fields(cp73.CP73SuppliedStreamOutputRelationQualificationBundleV1)
        == _BUNDLE_FIELDS
    )


def test_cp73_api_signature_is_output_first_and_exact() -> None:
    function = (
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == ("output_payload", "interchange_payloads")
    assert all(
        parameter.annotation in (object, "object")
        for parameter in signature.parameters.values()
    )
    assert signature.return_annotation in (
        cp73.CP73SuppliedStreamOutputRelationSummaryV1,
        "CP73SuppliedStreamOutputRelationSummaryV1",
    )


def test_cp73_classes_are_module_created_sealed_identity_records() -> None:
    bundle = cp73.cp73_supplied_stream_output_relation_qualification_bundle()
    records = (bundle.predecessor_custody, bundle.relation_contract, bundle)
    for record in records:
        assert is_dataclass(record)
        assert type(record).__dataclass_params__.frozen is True
        assert type(record).__dataclass_params__.eq is False
        assert record == record
        with pytest.raises(TypeError):
            type(record)()
        with pytest.raises(TypeError):
            pickle.dumps(record)
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, "record_sha256", _ZERO_SHA256)
        _assert_record(record)
    with pytest.raises(TypeError):
        type("Hostile", (cp73.CP73SuppliedStreamOutputRelationSummaryV1,), {})


def test_cp73_bundle_is_zero_execution_and_has_no_runner_or_fixture_bodies() -> None:
    bundle = cp73.cp73_supplied_stream_output_relation_qualification_bundle()
    assert bundle.schema_version == _SCHEMA
    assert bundle.blocker_ledger_prerequisite_id == _PREREQUISITE_ID
    assert bundle.blocker_ledger_prerequisite_state == _PREREQUISITE_STATE
    assert (
        bundle.blocker_ledger_total_count,
        bundle.blocker_ledger_satisfied_count,
        bundle.blocker_ledger_missing_count,
    ) == (28, 24, 4)
    assert bundle.zero_argument_builder is True
    assert bundle.builder_validates is False
    assert bundle.qualification_runner_exposed is False
    assert bundle.module_owned_fixture_count == 0
    assert bundle.module_owned_stream_body_count == 0
    assert bundle.module_owned_output_body_count == 0
    assert bundle.external_test_qualification_required is True
    assert bundle.public_supplied_stream_output_relation_validator_exposed is True
    assert bundle.public_caller_data_api_count == 1
    assert bundle.public_output_bytes_returned is False
    assert bundle.project_modules_imported is True
    assert bundle.project_module_count == 2
    assert bundle.source_independent is False
    assert bundle.stdlib_only is False
    assert bundle.stdlib_only_beyond_exact_predecessor_modules is True
    assert bundle.third_party_modules_imported is False
    assert bundle.predecessor_public_apis_only is True
    false_fields = (
        "public_parser_exposed",
        "public_stream_reducer_exposed",
        "public_output_validator_exposed",
        "public_summary_input_api_exposed",
        "public_path_api_exposed",
        "public_writer_api_exposed",
        "public_runner_api_exposed",
        "public_primary_decision_threshold_api_exposed",
        "public_decision_api_exposed",
        "public_receipt_or_evidence_api_exposed",
        "module_direct_filesystem_read",
        "module_direct_filesystem_write",
        "module_direct_clock_read",
        "module_direct_rng_used",
        "module_direct_network_used",
        "module_direct_subprocess_used",
        "production_execution_authorized",
        "production_recomputation_qualified",
        "unconditional_operational_predictions_produced",
        "power_review_present",
        "primary_thresholds_present",
        "confirmatory_custody_present",
        "runtime_lock_authenticated",
        "request_instance_sha256_authenticated",
        "stable_trace_sha256_authenticated",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "formal_test_28_closed",
    )
    assert all(getattr(bundle, name) is False for name in false_fields)
    assert bundle.production_gate_13_state == "MISSING"
    assert bundle.production_gate_14_state == "MISSING"
    assert bundle.formal_test_28_status == "OPEN"


def test_cp73_cold_bundle_builder_never_calls_dynamic_predecessor_apis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cp73, "_BUNDLE_CACHE", None)
    for private_name in (
        "_CP72_VALIDATE",
        "_CP72_CANONICAL_JSON_BYTES",
        "_CP72_SHA256",
        "_CP71_REDUCE",
        "_CP71_CANONICAL_JSON_BYTES",
        "_CP71_SHA256",
    ):
        monkeypatch.setattr(
            cp73,
            private_name,
            lambda *_args, private_name=private_name: pytest.fail(
                "%s called during bundle build" % private_name
            ),
        )
    bundle = cp73.cp73_supplied_stream_output_relation_qualification_bundle()
    assert type(bundle) is cp73.CP73SuppliedStreamOutputRelationQualificationBundleV1
    assert bundle.builder_validates is False


def test_cp73_predecessor_custody_pins_live_exact_bytes_and_records() -> None:
    custody = (
        cp73.cp73_supplied_stream_output_relation_qualification_bundle().predecessor_custody
    )
    expected_files = (
        (
            _V23_PROTOCOL,
            "8b75852101a3849a22e50d66fa50c17353de18a77e34f381d56198926f6ed4f8",
            246_105,
            4_046,
        ),
        (
            _V23_MANIFEST,
            "8217f0d8ba14d241d2f8eb863c1372a46d7e99c352fe595b617b00afb163ea44",
            6_201_962,
            121_172,
        ),
        (
            _CP69_SOURCE,
            "69f2ac19c37697f8c68dd8b4b312a12e0efc46c7df05f0157c310cf97e221dac",
            None,
            None,
        ),
        (
            _CP69_TEST,
            "c8179496c3986fcc6130ebccf9371b59956630cb8eada6e343f216adea13938c",
            None,
            None,
        ),
        (
            _CP71_SOURCE,
            "9be57c44592b5cb80bf68e876de335c8e253ffc1a11aa14fed2ad82213a49078",
            None,
            None,
        ),
        (
            _CP71_TEST,
            "7eaefe615325a76c16f8bb0b843bde82337c7f72d8686a4bcbcc7a8f7fb38352",
            None,
            None,
        ),
        (
            _CP72_SOURCE,
            "78f0558f318e45032b06856d21986d84fe53937185d9d005e395c2874df5167c",
            None,
            None,
        ),
        (
            _CP72_TEST,
            "ab4b2c5a74157863a621b59061b3ea38c872cbe1a9d30129c9ffc5922b5d4641",
            None,
            None,
        ),
    )
    for path, expected_sha, expected_bytes, expected_lf in expected_files:
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == expected_sha
        if expected_bytes is not None:
            assert len(payload) == expected_bytes
            assert payload.count(b"\n") == expected_lf
            assert payload.endswith(b"\n")
            assert b"\r" not in payload

    expected = {
        "schema_version": _SCHEMA,
        "v23_protocol_sha256": expected_files[0][1],
        "v23_protocol_bytes": 246_105,
        "v23_protocol_lf_count": 4_046,
        "v23_manifest_sha256": expected_files[1][1],
        "v23_manifest_bytes": 6_201_962,
        "v23_manifest_lf_count": 121_172,
        "cp69_source_sha256": expected_files[2][1],
        "cp69_test_sha256": expected_files[3][1],
        "cp69_bundle_record_sha256": "39c937d3d78913fb7f91b777bc676648eddac6e38696b26973eb55a55becfe26",
        "cp69_interchange_contract_record_sha256": "6b64acc21209a7d32a1ddadcc45e0ced2f13eb94b87d571bd32f1d007b906caa",
        "cp69_full_stream_expectation_record_sha256": "6043a6241ffc74ac14b395b052f87f22627beae43e2132992b2bb0e6a156289f",
        "cp69_qualification_record_sha256": "88dd43071ecf0545c9496e80b5de682ea9b7b0a5980a5fabe5b0f46f83586ab1",
        "cp71_source_sha256": expected_files[4][1],
        "cp71_test_sha256": expected_files[5][1],
        "cp71_bundle_record_sha256": "c49b4396c06f1ff792d2860176a2e318612bd12ad89ba3cf6f8804e2dc82169f",
        "cp71_stream_contract_record_sha256": "5aca44ab2240dfd9040ca3323b7306b12bbe6ee47a2c0af3128002b387f3236c",
        "cp71_output_contract_record_sha256": "13a76a7ce7b0c665ef33aa6e55c122c87bf61aa676530c984ce2fdaf63e345a3",
        "cp71_qualification_record_sha256": "aa25726473f54c17b3179ebabbaace3671e9815a6d3b4eec834ad6c1b8490611",
        "cp71_fixture_set_sha256": "bb4347afaca9e0ea41cb5b38ac74a3186b63fd95da9b4546b50de6aa1ffa83af",
        "cp72_source_sha256": expected_files[6][1],
        "cp72_test_sha256": expected_files[7][1],
        "cp72_bundle_record_sha256": "ecbe0e07e02d7d1ee930fc65b558bd4a5f655da78b950cc8df616e2cc410fc70",
        "cp72_validation_contract_record_sha256": "3768a8c5a70b137bc37553dd8e66fc3a9b66b51073c13a2a5d53b5ed8ae70b13",
        "cp72_qualification_record_sha256": "2202dc80acf16f0b7a59582979483bed60f19d6f57b2e86d044b68224518ac27",
        "cp72_fixture_set_sha256": "58ca1ff512558ca10fc4bdc447474aaf0ee04decd272954a85fff3e56c89941d",
    }
    actual = _record_body(custody)
    actual.pop("record_sha256")
    assert actual == expected


def test_cp73_contract_exact_phase_bounds_retention_and_nonclaims() -> None:
    contract = (
        cp73.cp73_supplied_stream_output_relation_qualification_bundle().relation_contract
    )
    assert contract.schema_version == _SCHEMA
    assert contract.contract_id == (
        "bounded-cp71-development-output-to-supplied-cp69-stream-exact-" "relation-v1"
    )
    assert contract.source_interchange_schema_version == _CP69_SCHEMA
    assert contract.source_semantic_schema_version == _CP63_SCHEMA
    assert contract.source_output_schema_version == _CP71_OUTPUT_SCHEMA
    assert contract.cp71_reduction_summary_schema_version == _CP71_SUMMARY_SCHEMA
    assert contract.cp72_validation_summary_schema_version == _CP72_SUMMARY_SCHEMA
    assert contract.output_payload_exact_type == "exact-built-in-bytes"
    assert contract.phase_order == _PHASE_ORDER
    assert contract.predecessor_error_normalization == _ERROR_NORMALIZATION
    assert contract.failure_precedence == _FAILURE_PRECEDENCE
    assert contract.project_module_names == _PROJECT_MODULES
    assert contract.predecessor_public_api_names == _PUBLIC_APIS
    assert contract.summary_crosscheck_fields == _CROSSCHECK_FIELDS
    assert contract.summary_crosscheck_field_count == 32
    assert contract.summary_crosscheck_digest_domain == _CROSSCHECK_DOMAIN.decode()
    assert contract.summary_crosscheck_digest_preimage == _CROSSCHECK_PREIMAGE
    assert contract.invalid_output_iter_calls == 0
    assert contract.invalid_output_next_calls == 0
    assert contract.invalid_output_close_calls == 0
    assert contract.cp72_validator_exact_call_count == 1
    assert contract.cp71_reducer_maximum_call_count == 1
    assert contract.cp71_reducer_exact_call_count_after_output_validation == 1
    assert contract.maximum_next_calls == 32_769
    assert contract.maximum_interchange_bytes == 65_536
    assert contract.maximum_stream_bytes == 268_435_456
    assert contract.maximum_output_bytes == 8_388_608
    assert contract.minimum_declared_total_input_bytes == 32_768
    assert contract.maximum_declared_total_input_bytes == 268_435_456
    assert contract.maximum_output_vector_cardinality == 554
    assert contract.maximum_sealed_record_bytes == 1_048_576
    expected_true = (
        "project_modules_imported",
        "stdlib_only_beyond_exact_predecessor_modules",
        "public_api_uses_predecessor_public_apis_only",
        "output_validation_completes_before_stream_iteration",
        "exact_output_byte_relation_required",
        "summary_crosscheck_required",
        "cp71_fixed_nonclaims_checked",
        "cp71_stream_coherence_claims_checked",
        "cp72_validation_claims_checked",
        "scalar_summary_only",
        "predecessor_summary_issuance_on_late_failure_possible",
        "predecessor_weak_registry_entries_recoverable_after_all_strong_references_released",
        "no_cp73_record_issued_before_relation_complete",
        "sealed_summary_snapshot_retained_while_summary_live",
    )
    expected_false = (
        "source_independent",
        "stdlib_only",
        "third_party_modules_imported",
        "caller_iterable_side_effects_qualified",
        "caller_iterable_retention_qualified",
        "caller_next_liveness_qualified",
        "iterator_close_called",
        "caller_output_bytes_returned",
        "recomputed_output_bytes_returned",
        "caller_summary_accepted",
        "predecessor_summary_returned",
        "caller_output_retained_after_successful_return",
        "recomputed_output_retained_after_successful_return",
        "module_owned_predecessor_summary_references_retained_after_successful_return",
        "exception_traceback_retention_qualified",
        "cp73_partial_return_on_failure",
        "dynamic_input_payload_or_output_body_cached",
        "module_direct_filesystem_read",
        "module_direct_filesystem_write",
        "module_direct_clock_read",
        "module_direct_rng_used",
        "module_direct_network_used",
        "module_direct_subprocess_used",
        "input_provenance_authenticated",
        "runtime_lock_authenticated",
        "request_instance_sha256_authenticated",
        "stable_trace_sha256_authenticated",
        "external_seed_source_verified",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "production_recomputation_qualified",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_made",
        "production_evidence",
        "confirmatory_custody_present",
    )
    assert all(getattr(contract, name) is True for name in expected_true)
    assert all(getattr(contract, name) is False for name in expected_false)
    assert contract.production_gate_13_state == "MISSING"
    assert contract.production_gate_14_state == "MISSING"
    assert contract.formal_test_28_status == "OPEN"
    assert "this-call-supplied" in contract.relation_verified_meaning
    assert "production" not in contract.relation_verified_meaning


def test_cp73_fast_success_has_independent_crosscheck_and_scalar_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = b"x"
    cp71_summary, cp72_summary = _install_synthetic_success(monkeypatch, output)
    summary = cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
        output, object()
    )
    _assert_record(summary)
    values = [
        getattr(cp71_summary, cp71_name) for cp71_name, _cp72_name in _CROSSCHECK_FIELDS
    ]
    expected_crosscheck = hashlib.sha256(
        _CROSSCHECK_DOMAIN
        + b"\0"
        + _canonical({"field_pairs": _CROSSCHECK_FIELDS, "values": values})
    ).hexdigest()
    assert summary.summary_crosscheck_sha256 == expected_crosscheck
    assert summary.summary_crosscheck_field_count == 32
    assert summary.cp71_reduction_summary_record_sha256 == cp71_summary.record_sha256
    assert summary.cp71_reduction_summary_public_sha256 == cp71.cp71_sha256(
        cp71_summary
    )
    assert summary.cp72_validation_summary_record_sha256 == cp72_summary.record_sha256
    assert summary.cp72_validation_summary_public_sha256 == cp72.cp72_sha256(
        cp72_summary
    )
    assert summary.cp72_ordered_cp61_inventory_crosswalk_sha256 == (
        _CP61_CROSSWALK_SHA256
    )
    assert summary.cp72_exact_endpoint_boundary_comparison_count == 0
    assert summary.output_canonical_json_bytes == 1
    assert summary.output_canonical_json_sha256 == hashlib.sha256(output).hexdigest()
    assert summary.request_count == 32_768
    assert (
        summary.output_validated_before_stream_iteration,
        summary.stream_recomputed_once,
        summary.output_bytes_exact_match,
        summary.summary_crosscheck_verified,
        summary.input_stream_relation_verified,
    ) == (True, True, True, True, True)
    assert all(
        getattr(summary, name) is False
        for name in (
            "external_seed_source_verified",
            "production_recomputation",
            "input_provenance_authenticated",
            "runtime_lock_authenticated",
            "request_instance_sha256_authenticated",
            "stable_trace_sha256_authenticated",
            "source_law_verified",
            "production_attempt_validity_evaluated",
            "operational_prediction",
            "power_review_present",
            "primary_thresholds_present",
            "decision_made",
            "production_evidence",
        )
    )
    body = _record_body(summary)
    assert all(type(value) not in (bytes, list, dict) for value in body.values())
    assert "selected_counts_by_row" not in body
    assert "observable_row_sums" not in body


@pytest.mark.parametrize(
    "output_payload",
    (None, True, 1, "{}", bytearray(b"{}"), memoryview(b"{}"), b"", b"{}"),
)
def test_cp73_invalid_real_output_never_touches_stream(
    output_payload: object,
) -> None:
    stream = _StreamProbe((b"must-not-be-read",))
    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output_payload, stream
        ),
        "CP73_OUTPUT_VALIDATION_FAILED",
    )
    assert type(getattr(error, "predecessor_error_code")) is str
    assert cast(str, getattr(error, "predecessor_error_code")).startswith("CP72_INPUT_")
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


def test_cp73_actual_output_cap_fails_before_stream_touch() -> None:
    stream = _StreamProbe((b"must-not-be-read",))
    output = b"0" * (cp73.CP73_TEST28_MAXIMUM_OUTPUT_BYTES + 1)
    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, stream
        ),
        "CP73_OUTPUT_VALIDATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == "CP72_INPUT_BYTE_LIMIT"
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


@pytest.mark.parametrize("predecessor_code", cp72.CP72_TEST28_ERROR_CODES)
def test_cp73_cp72_error_normalization_precedes_all_stream_touch(
    monkeypatch: pytest.MonkeyPatch, predecessor_code: str
) -> None:
    predecessor = cp72.CP72SuppliedDevelopmentOutputValidationQualificationError(
        predecessor_code, "hostile predecessor detail"
    )
    stream = _StreamProbe((b"must-not-be-read",))
    cp71_calls = []
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", _raising(predecessor))
    monkeypatch.setattr(
        cp73, "_CP71_REDUCE", lambda payloads: cp71_calls.append(payloads)
    )
    if predecessor_code == "CP72_RESOURCE_EXHAUSTED":
        expected = "CP73_RESOURCE_EXHAUSTED"
    elif (
        predecessor_code == "CP72_INTERNAL_INVARIANT_FAILED"
        or predecessor_code.startswith("CP72_RECORD_")
    ):
        expected = "CP73_INTERNAL_INVARIANT_FAILED"
    else:
        expected = "CP73_OUTPUT_VALIDATION_FAILED"
    _assert_wrapped_error(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", stream
        ),
        expected,
        predecessor_code,
        cp72.CP72SuppliedDevelopmentOutputValidationQualificationError,
    )
    assert cp71_calls == []
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


def test_cp73_unknown_cp72_error_is_internal_and_redacts_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    predecessor = cp72.CP72SuppliedDevelopmentOutputValidationQualificationError(
        "CP72_HOSTILE_UNKNOWN", "hostile secret detail"
    )
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", _raising(predecessor))
    _assert_wrapped_error(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", _StreamProbe()
        ),
        "CP73_INTERNAL_INVARIANT_FAILED",
        "CP72_HOSTILE_UNKNOWN",
        cp72.CP72SuppliedDevelopmentOutputValidationQualificationError,
    )


@pytest.mark.parametrize(
    "exception,expected",
    (
        (MemoryError("hostile"), "CP73_RESOURCE_EXHAUSTED"),
        (ValueError("hostile"), "CP73_INTERNAL_INVARIANT_FAILED"),
    ),
)
def test_cp73_direct_cp72_memory_and_unexpected_errors_are_normalized_first(
    monkeypatch: pytest.MonkeyPatch, exception: BaseException, expected: str
) -> None:
    stream = _StreamProbe()
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", _raising(exception))
    _assert_wrapped_error(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", stream
        ),
        expected,
        None,
        type(exception),
    )
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


@pytest.mark.parametrize(
    "exception_type", (KeyboardInterrupt, SystemExit, GeneratorExit)
)
def test_cp73_cp72_control_flow_is_reraised_without_stream_touch(
    monkeypatch: pytest.MonkeyPatch, exception_type: type
) -> None:
    stream = _StreamProbe()
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", _raising(exception_type("hostile")))
    with pytest.raises(exception_type):
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", stream
        )
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


@pytest.mark.parametrize(
    "overrides",
    (
        {"schema_version": "wrong"},
        {"source_output_schema_version": "wrong"},
        {"request_count": 32_767},
        {"estimand_count": 553},
        {"observable_estimand_count": 71},
        {"rejection_first_attempt_estimand_count": 169},
        {"feature_estimand_count": 311},
        {"binomial_estimand_count": 241},
        {"declared_total_input_bytes": 32_767},
        {"declared_total_input_bytes": 268_435_457},
        {"output_canonical_json_bytes": 0},
        {"output_canonical_json_bytes": 2},
        {"output_canonical_json_sha256": "0" * 64},
        {"ordered_cp61_inventory_crosswalk_sha256": "0" * 64},
        {"declared_input_stream_commitment_sha256": "g" * 64},
        {"declared_ordered_interchange_record_sha256": "0" * 63},
        {"ordered_estimand_record_sha256s_sha256": "G" * 64},
        {"output_body_sha256": "-" * 64},
        {"selected_counts_by_row": (0,) * 15},
        {"selected_counts_by_row": (2_049,) + (0,) * 15},
        {"observable_row_sums": (2_048,) * 15},
        {"observable_row_sums": (2_047,) + (2_048,) * 15},
        {"rejection_first_attempt_row_sums": (0,) * 7},
        {"rejection_first_attempt_row_sums": (2_049,) + (0,) * 7},
        {"feature_estimate_present_count": -1},
        {"feature_estimate_present_count": 1},
        {"binomial_interval_count": 241},
        {"feature_interval_count": 1},
        {"computed_interval_count": 241},
        {"insufficient_selection_count": 311},
        {"distinct_binomial_success_count_count": 0},
        {"distinct_binomial_success_count_count": 2_050},
        {"exact_endpoint_boundary_comparison_count": -1},
        {"stream_commitment_coherence_verified": False},
        {"canonical_json_verified": False},
        {"schema_verified": False},
        {"estimand_inventory_and_order_verified": False},
        {"record_digests_verified": False},
        {"cross_record_arithmetic_verified": False},
        {"exact_interval_arithmetic_verified": False},
        {"input_stream_relation_verified": True},
        {"input_provenance_authenticated": True},
        {"source_law_verified": True},
        {"production_attempt_validity_evaluated": True},
        {"operational_prediction": True},
        {"power_review_present": True},
        {"primary_thresholds_present": True},
        {"decision_made": True},
        {"production_evidence": True},
    ),
)
def test_cp73_cp72_fixed_claim_invariants_fail_before_cp71(
    monkeypatch: pytest.MonkeyPatch, overrides: Mapping[str, object]
) -> None:
    stream = _StreamProbe()
    summary = _issued_cp72_summary(b"x", **dict(overrides))
    cp71_calls = []
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: summary)
    monkeypatch.setattr(
        cp73, "_CP71_REDUCE", lambda payloads: cp71_calls.append(payloads)
    )
    _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", stream
        ),
        "CP73_INTERNAL_INVARIANT_FAILED",
    )
    assert cp71_calls == []
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


def test_cp73_cp72_wrong_return_type_fails_before_cp71(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = _StreamProbe()
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: object())
    monkeypatch.setattr(
        cp73, "_CP71_REDUCE", lambda _payloads: pytest.fail("CP71 called")
    )
    _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", stream
        ),
        "CP73_INTERNAL_INVARIANT_FAILED",
    )
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


@pytest.mark.parametrize("predecessor_code", cp71.CP71_TEST28_ERROR_CODES)
def test_cp73_cp71_error_normalization_after_one_successful_output_validation(
    monkeypatch: pytest.MonkeyPatch, predecessor_code: str
) -> None:
    cp72_summary = _issued_cp72_summary(b"x")
    predecessor = cp71.CP71SuppliedInterchangeRecomputationQualificationError(
        predecessor_code, "hostile predecessor detail"
    )
    validation_calls = []
    stream = object()
    reducer_arguments = []
    monkeypatch.setattr(
        cp73,
        "_CP72_VALIDATE",
        lambda payload: validation_calls.append(payload) or cp72_summary,
    )

    def reduce(payloads: object) -> object:
        reducer_arguments.append(payloads)
        raise predecessor

    monkeypatch.setattr(cp73, "_CP71_REDUCE", reduce)
    if predecessor_code == "CP71_RESOURCE_EXHAUSTED":
        expected = "CP73_RESOURCE_EXHAUSTED"
    elif (
        predecessor_code == "CP71_INTERNAL_INVARIANT_FAILED"
        or predecessor_code.startswith("CP71_RECORD_")
    ):
        expected = "CP73_INTERNAL_INVARIANT_FAILED"
    else:
        expected = "CP73_STREAM_RECOMPUTATION_FAILED"
    _assert_wrapped_error(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", stream
        ),
        expected,
        predecessor_code,
        cp71.CP71SuppliedInterchangeRecomputationQualificationError,
    )
    assert validation_calls == [b"x"]
    assert reducer_arguments == [stream]


def test_cp73_unknown_cp71_error_is_internal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cp72_summary = _issued_cp72_summary(b"x")
    predecessor = cp71.CP71SuppliedInterchangeRecomputationQualificationError(
        "CP71_HOSTILE_UNKNOWN", "hostile secret detail"
    )
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", _raising(predecessor))
    _assert_wrapped_error(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", object()
        ),
        "CP73_INTERNAL_INVARIANT_FAILED",
        "CP71_HOSTILE_UNKNOWN",
        cp71.CP71SuppliedInterchangeRecomputationQualificationError,
    )


@pytest.mark.parametrize(
    "exception,expected",
    (
        (MemoryError("hostile"), "CP73_RESOURCE_EXHAUSTED"),
        (ValueError("hostile"), "CP73_INTERNAL_INVARIANT_FAILED"),
    ),
)
def test_cp73_direct_cp71_memory_and_unexpected_errors_are_normalized(
    monkeypatch: pytest.MonkeyPatch, exception: BaseException, expected: str
) -> None:
    cp72_summary = _issued_cp72_summary(b"x")
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", _raising(exception))
    _assert_wrapped_error(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", object()
        ),
        expected,
        None,
        type(exception),
    )


@pytest.mark.parametrize(
    "exception_type", (KeyboardInterrupt, SystemExit, GeneratorExit)
)
def test_cp73_cp71_control_flow_is_reraised_after_output_validation(
    monkeypatch: pytest.MonkeyPatch, exception_type: type
) -> None:
    cp72_summary = _issued_cp72_summary(b"x")
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", _raising(exception_type("hostile")))
    with pytest.raises(exception_type):
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", object()
        )


@pytest.mark.parametrize(
    "result",
    (
        None,
        (),
        (b"x",),
        (b"x", object(), object()),
        [b"x", object()],
        (bytearray(b"x"), object()),
        (b"x", object()),
    ),
)
def test_cp73_invalid_cp71_outer_return_is_internal(
    monkeypatch: pytest.MonkeyPatch, result: object
) -> None:
    cp72_summary = _issued_cp72_summary(b"x")
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", lambda _payloads: result)
    _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", object()
        ),
        "CP73_INTERNAL_INVARIANT_FAILED",
    )


@pytest.mark.parametrize(
    "overrides",
    (
        {"schema_version": "wrong"},
        {"source_interchange_schema_version": "wrong"},
        {"source_semantic_schema_version": "wrong"},
        {"output_schema_version": "wrong"},
        {"request_count": 32_767},
        {"seed_count": 2_047},
        {"row_count": 15},
        {"total_input_bytes": 32_767},
        {"total_input_bytes": 268_435_457},
        {"output_canonical_json_bytes": 0},
        {"output_canonical_json_bytes": 2},
        {"output_canonical_json_sha256": "0" * 64},
        {"input_stream_commitment_sha256": "g" * 64},
        {"ordered_interchange_record_sha256": "0" * 63},
        {"ordered_estimand_record_sha256s_sha256": "G" * 64},
        {"output_body_sha256": "-" * 64},
        {"selected_counts_by_row": (0,) * 15},
        {"selected_counts_by_row": (2_049,) + (0,) * 15},
        {"observable_row_sums": (0,) * 15},
        {"observable_row_sums": (2_047,) + (2_048,) * 15},
        {"rejection_first_attempt_row_sums": (0,) * 7},
        {"rejection_first_attempt_row_sums": (2_049,) + (0,) * 7},
        {"status_counts": (0,) * 5},
        {"status_counts": (0,) * 6},
        {"status_counts": (32_769, 0, 0, 0, 0, 0)},
        {"feature_estimate_present_count": -1},
        {"feature_estimate_present_count": 1},
        {"binomial_interval_count": 241},
        {"feature_interval_count": 1},
        {"computed_interval_count": 241},
        {"insufficient_selection_count": 311},
        {"distinct_cp_success_count_count": 0},
        {"distinct_cp_success_count_count": 2_050},
        {"plan_seed_row_group_coherence_verified": False},
        {"row_seed_free_request_sha256s_matched": False},
        {"runtime_lock_stream_coherence_verified": False},
        {"input_provenance_authenticated": True},
        {"external_seed_source_verified": True},
        {"source_law_verified": True},
        {"production_attempt_validity_evaluated": True},
        {"production_recomputation": True},
        {"operational_prediction": True},
        {"power_review_present": True},
        {"primary_thresholds_present": True},
        {"decision_made": True},
        {"production_evidence": True},
    ),
)
def test_cp73_cp71_fixed_claim_and_stream_coherence_invariants(
    monkeypatch: pytest.MonkeyPatch, overrides: Mapping[str, object]
) -> None:
    output = b"x"
    cp72_summary = _issued_cp72_summary(output)
    cp71_summary = _issued_cp71_summary(cp72_summary, output, **dict(overrides))
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", lambda _payloads: (output, cp71_summary))
    _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, object()
        ),
        "CP73_INTERNAL_INVARIANT_FAILED",
    )


@pytest.mark.parametrize(
    "supplied,recomputed",
    (
        (b"x", b"y"),
        (b'{"a":1}', b'{"a":1 }'),
        (b"same-prefix", b"same-prefix\0"),
    ),
)
def test_cp73_relation_requires_exact_bytes_not_semantic_or_prefix_equality(
    monkeypatch: pytest.MonkeyPatch, supplied: bytes, recomputed: bytes
) -> None:
    cp72_summary = _issued_cp72_summary(supplied)
    cp71_summary = _issued_cp71_summary(cp72_summary, recomputed)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(
        cp73, "_CP71_REDUCE", lambda _payloads: (recomputed, cp71_summary)
    )
    _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            supplied, object()
        ),
        "CP73_OUTPUT_RELATION_MISMATCH",
    )


@pytest.mark.parametrize(
    "cp71_overrides",
    (
        {"total_input_bytes": 32_769},
        {"input_stream_commitment_sha256": "a" * 64},
        {"ordered_interchange_record_sha256": "a" * 64},
        {"ordered_projection_sha256": "a" * 64},
        {"ordered_seed_ordinal_plan_seed_sha256": "a" * 64},
        {"ordered_request_instance_sha256": "a" * 64},
        {"ordered_stable_trace_sha256": "a" * 64},
        {"runtime_lock_sha256": "a" * 64},
        {"selected_counts_by_row": (1,) + (0,) * 15},
        {"observable_row_sums": (2_047,) + (2_048,) * 15},
        {"rejection_first_attempt_row_sums": (1,) + (0,) * 7},
        {"feature_estimate_present_count": 1},
        {"feature_estimate_absent_count": 311},
        {"binomial_interval_count": 241},
        {"feature_interval_count": 1},
        {"computed_interval_count": 241},
        {"insufficient_selection_count": 311},
        {"distinct_cp_success_count_count": 2},
        {"ordered_estimand_record_sha256s_sha256": "a" * 64},
        {"output_body_sha256": "a" * 64},
    ),
)
def test_cp73_equal_bytes_require_all_dynamic_crosscheck_fields(
    monkeypatch: pytest.MonkeyPatch, cp71_overrides: Mapping[str, object]
) -> None:
    output = b"x"
    cp72_summary = _issued_cp72_summary(output)
    cp71_summary = _issued_cp71_summary(cp72_summary, output, **dict(cp71_overrides))
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", lambda _payloads: (output, cp71_summary))
    _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, object()
        ),
        "CP73_INTERNAL_INVARIANT_FAILED",
    )


@pytest.mark.parametrize("variant", ("unissued", "tampered"))
def test_cp73_rejects_invalid_issued_cp72_summary_before_stream(
    monkeypatch: pytest.MonkeyPatch, variant: str
) -> None:
    issued = _issued_cp72_summary(b"x")
    if variant == "unissued":
        returned = _unissued_copy(issued)
        predecessor_code = "CP72_RECORD_NOT_ISSUED"
    else:
        returned = issued
        object.__setattr__(returned, "record_sha256", "f" * 64)
        predecessor_code = "CP72_RECORD_TAMPERED"
    stream = _StreamProbe()
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: returned)
    with pytest.raises(
        cp73.CP73SuppliedStreamOutputRelationQualificationError
    ) as caught:
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", stream
        )
    assert caught.value.code == "CP73_INTERNAL_INVARIANT_FAILED"
    assert caught.value.predecessor_error_code == predecessor_code
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (0, 0, 0)


@pytest.mark.parametrize("variant", ("unissued", "tampered"))
def test_cp73_rejects_invalid_issued_cp71_summary_after_output_validation(
    monkeypatch: pytest.MonkeyPatch, variant: str
) -> None:
    output = b"x"
    cp72_summary = _issued_cp72_summary(output)
    issued = _issued_cp71_summary(cp72_summary, output)
    if variant == "unissued":
        returned = _unissued_copy(issued)
        predecessor_code = "CP71_RECORD_NOT_ISSUED"
    else:
        returned = issued
        object.__setattr__(returned, "record_sha256", "f" * 64)
        predecessor_code = "CP71_RECORD_TAMPERED"
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", lambda _payloads: (output, returned))
    with pytest.raises(
        cp73.CP73SuppliedStreamOutputRelationQualificationError
    ) as caught:
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, object()
        )
    assert caught.value.code == "CP73_INTERNAL_INVARIANT_FAILED"
    assert caught.value.predecessor_error_code == predecessor_code


def test_cp73_record_apis_reject_wrong_unissued_and_tampered_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for function in (cp73.cp73_canonical_json_bytes, cp73.cp73_sha256):
        _error_code(
            lambda function=function: function(object()), "CP73_RECORD_TYPE_MISMATCH"
        )
        _error_code(
            lambda function=function: function(
                cp72.cp72_supplied_development_output_validation_qualification_bundle()
            ),
            "CP73_RECORD_TYPE_MISMATCH",
        )
    _install_synthetic_success(monkeypatch)
    summary = cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
        b"x", object()
    )
    unissued = _unissued_copy(summary)
    _error_code(
        lambda: cp73.cp73_canonical_json_bytes(unissued), "CP73_RECORD_NOT_ISSUED"
    )
    object.__setattr__(summary, "output_canonical_json_bytes", 2)
    _error_code(lambda: cp73.cp73_canonical_json_bytes(summary), "CP73_RECORD_TAMPERED")
    _error_code(lambda: cp73.cp73_sha256(summary), "CP73_RECORD_TAMPERED")


def test_cp73_calls_each_frozen_predecessor_api_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = b"x"
    cp72_summary = _issued_cp72_summary(output)
    cp71_summary = _issued_cp71_summary(cp72_summary, output)
    calls = {name: 0 for name in _PUBLIC_APIS}

    def cp72_validate(payload: object) -> object:
        calls[_PUBLIC_APIS[0]] += 1
        assert payload is output
        return cp72_summary

    def cp72_canonical(record: object) -> bytes:
        calls[_PUBLIC_APIS[1]] += 1
        return cp72.cp72_canonical_json_bytes(record)

    def cp72_digest(record: object) -> str:
        calls[_PUBLIC_APIS[2]] += 1
        return cp72.cp72_sha256(record)

    stream = object()

    def cp71_reduce(payloads: object) -> object:
        calls[_PUBLIC_APIS[3]] += 1
        assert payloads is stream
        return output, cp71_summary

    def cp71_canonical(record: object) -> bytes:
        calls[_PUBLIC_APIS[4]] += 1
        return cp71.cp71_canonical_json_bytes(record)

    def cp71_digest(record: object) -> str:
        calls[_PUBLIC_APIS[5]] += 1
        return cp71.cp71_sha256(record)

    monkeypatch.setattr(cp73, "_CP72_VALIDATE", cp72_validate)
    monkeypatch.setattr(cp73, "_CP72_CANONICAL_JSON_BYTES", cp72_canonical)
    monkeypatch.setattr(cp73, "_CP72_SHA256", cp72_digest)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", cp71_reduce)
    monkeypatch.setattr(cp73, "_CP71_CANONICAL_JSON_BYTES", cp71_canonical)
    monkeypatch.setattr(cp73, "_CP71_SHA256", cp71_digest)
    cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
        output, stream
    )
    assert calls == {name: 1 for name in _PUBLIC_APIS}


@pytest.mark.parametrize("failure", ("output", "stream", "relation", "crosscheck"))
def test_cp73_failure_never_issues_partial_cp73_record_or_mutates_bundle_cache(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    output = b"x"
    cp72_summary = _issued_cp72_summary(output)
    issued = []
    bundle = cp73.cp73_supplied_stream_output_relation_qualification_bundle()
    monkeypatch.setattr(cp73, "_BUNDLE_CACHE", bundle)
    monkeypatch.setattr(
        cp73,
        "_record",
        lambda cls, values: issued.append((cls, values))
        or pytest.fail("partial CP73 issuance"),
    )
    if failure == "output":
        monkeypatch.setattr(
            cp73,
            "_CP72_VALIDATE",
            _raising(
                cp72.CP72SuppliedDevelopmentOutputValidationQualificationError(
                    "CP72_INPUT_JSON_INVALID", "hostile"
                )
            ),
        )
    else:
        monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
        if failure == "stream":
            monkeypatch.setattr(
                cp73,
                "_CP71_REDUCE",
                _raising(
                    cp71.CP71SuppliedInterchangeRecomputationQualificationError(
                        "CP71_STREAM_ITERATION_FAILED", "hostile"
                    )
                ),
            )
        elif failure == "relation":
            other = b"y"
            relation_summary = _issued_cp71_summary(cp72_summary, other)
            monkeypatch.setattr(
                cp73, "_CP71_REDUCE", lambda _payloads: (other, relation_summary)
            )
        else:
            mismatch = _issued_cp71_summary(
                cp72_summary, output, total_input_bytes=32_769
            )
            monkeypatch.setattr(
                cp73, "_CP71_REDUCE", lambda _payloads: (output, mismatch)
            )
    expected = {
        "output": "CP73_OUTPUT_VALIDATION_FAILED",
        "stream": "CP73_STREAM_RECOMPUTATION_FAILED",
        "relation": "CP73_OUTPUT_RELATION_MISMATCH",
        "crosscheck": "CP73_INTERNAL_INVARIANT_FAILED",
    }[failure]
    _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, object()
        ),
        expected,
    )
    assert issued == []
    assert cp73._BUNDLE_CACHE is bundle


def test_cp73_success_issues_exactly_one_final_record_and_does_not_touch_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_synthetic_success(monkeypatch)
    real_record = cp73._record
    calls = []
    monkeypatch.setattr(cp73, "_BUNDLE_CACHE", None)

    def record(cls: type, values: Mapping[str, object]) -> object:
        calls.append(cls)
        return real_record(cls, values)

    monkeypatch.setattr(cp73, "_record", record)
    result = cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
        b"x", object()
    )
    assert type(result) is cp73.CP73SuppliedStreamOutputRelationSummaryV1
    assert calls == [cp73.CP73SuppliedStreamOutputRelationSummaryV1]
    assert cp73._BUNDLE_CACHE is None


@pytest.mark.parametrize(
    "exception,expected",
    (
        (MemoryError("hostile"), "CP73_RESOURCE_EXHAUSTED"),
        (ValueError("hostile"), "CP73_INTERNAL_INVARIANT_FAILED"),
    ),
)
def test_cp73_final_issuance_memory_and_unexpected_fail_closed(
    monkeypatch: pytest.MonkeyPatch, exception: BaseException, expected: str
) -> None:
    _install_synthetic_success(monkeypatch)
    monkeypatch.setattr(cp73, "_record", _raising(exception))
    _assert_wrapped_error(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", object()
        ),
        expected,
        None,
        type(exception),
    )


@pytest.mark.parametrize(
    "exception_type", (KeyboardInterrupt, SystemExit, GeneratorExit)
)
def test_cp73_final_issuance_control_flow_is_reraised(
    monkeypatch: pytest.MonkeyPatch, exception_type: type
) -> None:
    _install_synthetic_success(monkeypatch)
    monkeypatch.setattr(cp73, "_record", _raising(exception_type("hostile")))
    with pytest.raises(exception_type):
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", object()
        )


def test_cp73_success_does_not_retain_caller_or_predecessor_summaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    weak: dict = {}

    def validate(output: object) -> object:
        summary = _issued_cp72_summary(cast(bytes, output))
        weak["cp72"] = weakref.ref(summary)
        return summary

    def reduce(_stream: object) -> object:
        cp72_summary = weak["cp72"]()
        assert cp72_summary is not None
        summary = _issued_cp71_summary(cp72_summary, b"x")
        weak["cp71"] = weakref.ref(summary)
        return b"x", summary

    monkeypatch.setattr(cp73, "_CP72_VALIDATE", validate)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", reduce)
    stream = _StreamProbe()
    stream_ref = weakref.ref(stream)
    summary = cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
        b"x", stream
    )
    assert type(summary) is cp73.CP73SuppliedStreamOutputRelationSummaryV1
    del stream
    gc.collect()
    assert stream_ref() is None
    assert weak["cp71"]() is None
    assert weak["cp72"]() is None


def test_cp73_late_failure_traceback_can_retain_transient_predecessor_summaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    weak: dict = {}

    def validate(_output: object) -> object:
        summary = _issued_cp72_summary(b"x")
        weak["cp72"] = weakref.ref(summary)
        return summary

    def reduce(_stream: object) -> object:
        cp72_summary = weak["cp72"]()
        assert cp72_summary is not None
        summary = _issued_cp71_summary(cp72_summary, b"y")
        weak["cp71"] = weakref.ref(summary)
        return b"y", summary

    monkeypatch.setattr(cp73, "_CP72_VALIDATE", validate)
    monkeypatch.setattr(cp73, "_CP71_REDUCE", reduce)
    retained = None
    try:
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            b"x", object()
        )
    except cp73.CP73SuppliedStreamOutputRelationQualificationError as exc:
        retained = exc
    assert retained is not None
    assert retained.code == "CP73_OUTPUT_RELATION_MISMATCH"
    assert weak["cp71"]() is not None
    assert weak["cp72"]() is not None
    del retained
    gc.collect()
    assert weak["cp71"]() is None
    assert weak["cp72"]() is None


def test_cp73_relation_and_bundle_are_thread_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_synthetic_success(monkeypatch)
    monkeypatch.setattr(cp73, "_BUNDLE_CACHE", None)
    with ThreadPoolExecutor(max_workers=8) as executor:
        summaries = list(
            executor.map(
                lambda _index: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
                    b"x", object()
                ),
                range(32),
            )
        )
        bundles = list(
            executor.map(
                lambda _index: cp73.cp73_supplied_stream_output_relation_qualification_bundle(),
                range(32),
            )
        )
    assert len({id(summary) for summary in summaries}) == 32
    assert len({summary.record_sha256 for summary in summaries}) == 1
    assert len({cp73.cp73_sha256(summary) for summary in summaries}) == 1
    assert len({id(bundle) for bundle in bundles}) == 1


def test_cp73_canonical_json_is_duplicate_free_float_free_and_bounded() -> None:
    duplicate_keys = []

    def hook(pairs: List[Tuple[str, object]]) -> dict:
        keys = [key for key, _value in pairs]
        if len(keys) != len(set(keys)):
            duplicate_keys.extend(keys)
        return dict(pairs)

    def reject_float(value: str) -> object:
        raise AssertionError("float in canonical CP73 record: %s" % value)

    bundle = cp73.cp73_supplied_stream_output_relation_qualification_bundle()
    records = (bundle.predecessor_custody, bundle.relation_contract, bundle)
    for record in records:
        payload = cp73.cp73_canonical_json_bytes(record)
        assert len(payload) <= cp73.CP73_TEST28_MAXIMUM_SEALED_RECORD_BYTES
        decoded = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=hook,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
        assert payload == _canonical(record)
        assert decoded == _to_plain(record)
    assert duplicate_keys == []


def test_cp73_source_import_and_no_direct_io_boundary() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    project_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported_roots.add(module.split(".")[0])
            if module.startswith("heterodiff."):
                project_imports.append(
                    (module, tuple(alias.name for alias in node.names))
                )
    assert imported_roots == {
        "__future__",
        "dataclasses",
        "hashlib",
        "hmac",
        "json",
        "threading",
        "typing",
        "weakref",
        "heterodiff",
    }
    assert tuple(module for module, _names in project_imports) == _PROJECT_MODULES
    imported_dynamic_apis = tuple(
        name
        for _module, names in project_imports
        for name in names
        if name.startswith("cp7")
    )
    assert imported_dynamic_apis == _PUBLIC_APIS
    forbidden_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "input",
        "system",
        "popen",
        "run",
        "check_call",
        "check_output",
        "urlopen",
    }
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in forbidden_calls
        for node in ast.walk(tree)
    )
    assert (
        cp73._CP72_VALIDATE is cp72.cp72_validate_supplied_cp71_development_output_bytes
    )
    assert cp73._CP72_CANONICAL_JSON_BYTES is cp72.cp72_canonical_json_bytes
    assert cp73._CP72_SHA256 is cp72.cp72_sha256
    assert cp73._CP71_REDUCE is cp71.cp71_reduce_supplied_cp69_interchange_byte_stream
    assert cp73._CP71_CANONICAL_JSON_BYTES is cp71.cp71_canonical_json_bytes
    assert cp73._CP71_SHA256 is cp71.cp71_sha256
    assert "qualification_runner" not in cp73.__all__
    assert not any(
        token in name
        for name in cp73.__all__
        for token in ("path", "writer", "raw_record", "stable_trace", "decision")
    )


def test_cp73_locked_python39_import_bundle_and_output_first_boundary() -> None:
    if not _PYTHON39.is_file():
        pytest.skip("locked Python 3.9 executable is unavailable")
    script = r"""
import heterodiff.evaluation.mixed_initializer_test28_supplied_stream_output_relation_qualification as cp73

class Bomb(object):
    calls = 0
    def __iter__(self):
        self.calls += 1
        raise AssertionError("stream touched")

stream = Bomb()
try:
    cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(b"", stream)
except cp73.CP73SuppliedStreamOutputRelationQualificationError as exc:
    assert exc.code == "CP73_OUTPUT_VALIDATION_FAILED"
    assert exc.predecessor_error_code.startswith("CP72_INPUT_")
else:
    raise AssertionError("invalid output accepted")
assert stream.calls == 0
bundle = cp73.cp73_supplied_stream_output_relation_qualification_bundle()
assert bundle.formal_test_28_status == "OPEN"
assert bundle.project_module_count == 2
assert len(cp73.__all__) == 30
print("cp73-python39-ok")
"""
    result = subprocess.run(
        [str(_PYTHON39), "-c", script],
        cwd=str(_ROOT),
        env={"PYTHONPATH": str(_ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "cp73-python39-ok"


@pytest.mark.parametrize("fixture_id", _FIXTURE_IDS, ids=_FIXTURE_IDS)
def test_cp73_real_cp71_fixture_stream_output_pairs(
    fixture_id: str,
) -> None:
    index = _FIXTURE_IDS.index(fixture_id)
    summary, stream_calls = _real_fixture_relation(fixture_id)
    _assert_record(summary)
    assert summary.cp71_reduction_summary_record_sha256 == _CP71_SUMMARY_SHA256S[index]
    assert summary.cp72_validation_summary_record_sha256 == _CP72_SUMMARY_SHA256S[index]
    assert summary.output_canonical_json_bytes == _FIXTURE_OUTPUT_BYTES[index]
    assert summary.output_canonical_json_sha256 == _FIXTURE_OUTPUT_SHA256S[index]
    assert summary.cp72_ordered_cp61_inventory_crosswalk_sha256 == (
        _CP61_CROSSWALK_SHA256
    )
    assert summary.summary_crosscheck_field_count == 32
    assert summary.output_validated_before_stream_iteration is True
    assert summary.stream_recomputed_once is True
    assert summary.output_bytes_exact_match is True
    assert summary.summary_crosscheck_verified is True
    assert summary.input_stream_relation_verified is True
    assert all(
        getattr(summary, name) is False
        for name in (
            "runtime_lock_authenticated",
            "request_instance_sha256_authenticated",
            "stable_trace_sha256_authenticated",
            "external_seed_source_verified",
            "production_recomputation",
            "input_provenance_authenticated",
            "source_law_verified",
            "production_attempt_validity_evaluated",
            "operational_prediction",
            "power_review_present",
            "primary_thresholds_present",
            "decision_made",
            "production_evidence",
        )
    )
    assert stream_calls == (1, 32_769, 0)


def test_cp73_real_relation_summary_set_is_ordered_and_digestible() -> None:
    summaries = tuple(
        _real_fixture_relation(fixture_id)[0] for fixture_id in _FIXTURE_IDS
    )
    record_sha256s = tuple(summary.record_sha256 for summary in summaries)
    public_sha256s = tuple(cp73.cp73_sha256(summary) for summary in summaries)
    canonical_bytes = tuple(
        len(cp73.cp73_canonical_json_bytes(summary)) for summary in summaries
    )
    relation_set_sha256 = hashlib.sha256(
        _REAL_RELATION_SET_DOMAIN
        + b"\0"
        + b"".join(bytes.fromhex(value) for value in record_sha256s)
    ).hexdigest()
    assert record_sha256s == _REAL_RELATION_RECORD_SHA256S
    assert public_sha256s == _REAL_RELATION_PUBLIC_SHA256S
    assert canonical_bytes == _REAL_RELATION_CANONICAL_BYTES
    assert relation_set_sha256 == _REAL_RELATION_SET_SHA256


def test_cp73_cp72_valid_nonfixture_output_is_not_related_to_fixture_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = _unrelated_cp72_valid_nonfixture_output()
    stream = _StreamProbe(_fixture_stream(_FIXTURE_IDS[0]))
    issued = []
    real_record = cp73._record

    def record(cls: type, values: Mapping[str, object]) -> object:
        issued.append(cls)
        return real_record(cls, values)

    monkeypatch.setattr(cp73, "_record", record)
    with pytest.raises(
        cp73.CP73SuppliedStreamOutputRelationQualificationError
    ) as caught:
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, stream
        )
    assert caught.value.code == "CP73_OUTPUT_RELATION_MISMATCH"
    assert caught.value.predecessor_error_code is None
    assert issued == []
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (
        1,
        32_769,
        0,
    )


def test_cp73_cross_pair_mismatch_rejects_two_individually_valid_fixture_artifacts() -> None:
    output = _fixture_output(_FIXTURE_IDS[0])
    with pytest.raises(
        cp73.CP73SuppliedStreamOutputRelationQualificationError
    ) as caught:
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, _fixture_stream(_FIXTURE_IDS[1])
        )
    assert caught.value.code == "CP73_OUTPUT_RELATION_MISMATCH"
    assert caught.value.predecessor_error_code is None


def test_cp73_actual_stream_mutation_is_rejected_by_cp71(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)

    def mutated() -> Iterator[bytes]:
        source = _fixture_stream(fixture_id)
        first = next(source)
        yield b"[" + first[1:]
        yield from source

    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, mutated()
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code in {
        "CP71_INPUT_JSON_INVALID",
        "CP71_INPUT_FIELD_TYPE_MISMATCH",
        "CP71_INPUT_FIELD_SET_MISMATCH",
    }


def test_cp73_canonical_stream_mutation_with_repaired_record_digest_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)

    def repaired_mutation() -> Iterator[bytes]:
        source = _fixture_stream(fixture_id)
        body = json.loads(next(source).decode("ascii"))
        assert type(body) is dict
        body["plan_seed_hex"] = "ffffffffffffffff"
        body["record_sha256"] = _ZERO_SHA256
        body["record_sha256"] = hashlib.sha256(
            b"cp69-test28-compact-interchange-observation-v1\0" + _canonical(body)
        ).hexdigest()
        yield _canonical(body)
        yield from source

    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, repaired_mutation()
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == (
        "CP71_INPUT_GROUP_COHERENCE_MISMATCH"
    )


def test_cp73_actual_stream_order_swap_is_rejected_by_cp71(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)

    def swapped() -> Iterator[bytes]:
        source = _fixture_stream(fixture_id)
        first = next(source)
        second = next(source)
        yield second
        yield first
        yield from source

    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, swapped()
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == "CP71_INPUT_ORDINAL_MISMATCH"


def test_cp73_actual_short_stream_count_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    stream = _StreamProbe(())
    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, stream
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == "CP71_STREAM_COUNT_MISMATCH"
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (1, 1, 0)


@pytest.mark.parametrize(
    "item,predecessor_code",
    (
        (b"", "CP71_INPUT_BYTE_LIMIT"),
        (b"0" * 65_537, "CP71_INPUT_BYTE_LIMIT"),
        (bytearray(b"{}"), "CP71_INPUT_TYPE_MISMATCH"),
    ),
)
def test_cp73_actual_per_item_type_and_byte_caps(
    monkeypatch: pytest.MonkeyPatch, item: object, predecessor_code: str
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    stream = _StreamProbe(cast(Iterable[bytes], (item,)))
    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, stream
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == predecessor_code
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (1, 1, 0)


def test_cp73_actual_long_stream_count_is_rejected_at_bounded_terminal_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)

    def long_stream() -> Iterator[bytes]:
        yield from _fixture_stream(fixture_id)
        yield next(_fixture_stream(fixture_id))

    stream = _StreamProbe(long_stream())
    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, stream
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == "CP71_STREAM_COUNT_MISMATCH"
    assert (stream.iter_calls, stream.next_calls, stream.close_calls) == (
        1,
        32_769,
        0,
    )


def test_cp73_actual_noniterable_and_iterator_exception_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)
    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, None
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == "CP71_STREAM_ITERABLE_INVALID"

    def failed_next() -> Iterator[bytes]:
        raise ValueError("hostile iterator detail")
        yield b"unreachable"

    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, failed_next()
        ),
        "CP73_STREAM_RECOMPUTATION_FAILED",
    )
    assert cast(object, error).predecessor_error_code == "CP71_STREAM_ITERATION_FAILED"


@pytest.mark.parametrize("at_iter", (True, False))
def test_cp73_actual_iterator_memoryerror_is_resource_exhaustion(
    monkeypatch: pytest.MonkeyPatch, at_iter: bool
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)

    class MemoryIterator:
        def __iter__(self) -> "MemoryIterator":
            if at_iter:
                raise MemoryError("hostile")
            return self

        def __next__(self) -> bytes:
            raise MemoryError("hostile")

    error = _error_code(
        lambda: cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, MemoryIterator()
        ),
        "CP73_RESOURCE_EXHAUSTED",
    )
    assert cast(object, error).predecessor_error_code == "CP71_RESOURCE_EXHAUSTED"


@pytest.mark.parametrize(
    "exception_type", (KeyboardInterrupt, SystemExit, GeneratorExit)
)
@pytest.mark.parametrize("at_iter", (True, False))
def test_cp73_actual_iterator_control_flow_is_reraised(
    monkeypatch: pytest.MonkeyPatch, exception_type: type, at_iter: bool
) -> None:
    fixture_id = _FIXTURE_IDS[0]
    output = _fixture_output(fixture_id)
    cp72_summary = _fixture_cp72_summary(fixture_id)
    monkeypatch.setattr(cp73, "_CP72_VALIDATE", lambda _payload: cp72_summary)

    class ControlIterator:
        def __iter__(self) -> "ControlIterator":
            if at_iter:
                raise exception_type("hostile")
            return self

        def __next__(self) -> bytes:
            raise exception_type("hostile")

    with pytest.raises(exception_type):
        cp73.cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
            output, ControlIterator()
        )
