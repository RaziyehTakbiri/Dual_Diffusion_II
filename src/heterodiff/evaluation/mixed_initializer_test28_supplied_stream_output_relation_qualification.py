"""Relate one caller CP69 development stream to one canonical CP71 output.

CP73 is a thin, project-dependent composition of two frozen public predecessor
APIs.  It first completes CP72 validation of the supplied output bytes.  Only
after that succeeds does it pass the caller stream exactly once to CP71.  The
recomputed and supplied output bytes must match exactly, and the sealed CP71 and
CP72 scalar summaries must agree across a frozen 32-field crosswalk.

The returned sealed CP73 record is scalar-only.  It establishes only that this
call's supplied development stream regenerated these supplied canonical bytes.
It does not authenticate authorship, provenance, seed or runtime custody, a
source law, a production attempt, coverage, a primary threshold, a decision,
evidence, a production gate, execution authority, or Formal Test 28 closure.

Only this module's direct I/O, clock, RNG, network, and subprocess behavior is
described.  CP71 owns iteration after output validation; caller iterator side
effects, retention, and next-call liveness remain unqualified.  Predecessor
summaries are transiently issued and can remain reachable through exception
tracebacks.  Successful calls discard module-owned references to caller and
recomputed output bytes and both predecessor summaries before CP73 issuance.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import hmac
import json
import threading
from typing import Mapping, Optional, Tuple, cast
import weakref

from heterodiff.evaluation.mixed_initializer_test28_supplied_development_output_validation_qualification import (
    CP72_TEST28_ERROR_CODES,
    CP72_TEST28_SCHEMA_VERSION,
    CP72SuppliedDevelopmentOutputValidationQualificationError,
    CP72SuppliedDevelopmentOutputValidationSummaryV1,
    cp72_validate_supplied_cp71_development_output_bytes,
    cp72_canonical_json_bytes,
    cp72_sha256,
)
from heterodiff.evaluation.mixed_initializer_test28_supplied_interchange_recomputation_qualification import (
    CP71_TEST28_ERROR_CODES,
    CP71_TEST28_SCHEMA_VERSION,
    CP71SuppliedDevelopmentReductionSummaryV1,
    CP71SuppliedInterchangeRecomputationQualificationError,
    cp71_reduce_supplied_cp69_interchange_byte_stream,
    cp71_canonical_json_bytes,
    cp71_sha256,
)


CP73_TEST28_SCHEMA_VERSION = (
    "cp73-test28-supplied-stream-output-relation-qualification-v1"
)
CP73_TEST28_SCOPE = (
    "development-only-project-dependent-thin-composition-of-frozen-cp72-"
    "output-validation-and-cp71-stream-recomputation;output-first-zero-stream-"
    "touch-on-output-failure;one-cp71-reduction;exact-output-byte-relation-and-"
    "32-field-sealed-summary-crosscheck;scalar-relation-summary-only;no-input-"
    "authorship-provenance-source-law-runtime-request-trace-seed-custody-"
    "production-attempt-coverage-recomputation-operational-prediction-primary-"
    "threshold-decision-receipt-evidence-gate-authorization-or-test28-closure-"
    "claim;no-public-parser-reducer-output-validator-summary-input-path-writer-"
    "runner-or-production-api;project-modules-imported;source-independent-"
    "false;stdlib-only-beyond-exact-predecessor-modules;module-direct-io-clock-"
    "rng-network-subprocess-absence-only;caller-iterator-side-effects-retention-"
    "and-next-liveness-unqualified;successful-return-data-and-predecessor-"
    "summary-nonretention-only;exception-traceback-locals-unqualified;"
    "predecessor-summary-issuance-before-late-failure-possible;no-cp73-partial-"
    "summary-or-dynamic-cache-on-failure"
)
CP73_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP73_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID = (
    "whole_seed_supplied_cp69_interchange_to_cp71_development_output_exact_"
    "relation_qualification"
)
CP73_TEST28_SEED_COUNT = 2_048
CP73_TEST28_ROW_COUNT = 16
CP73_TEST28_REQUEST_COUNT = 32_768
CP73_TEST28_ESTIMAND_COUNT = 554
CP73_TEST28_PREDECESSOR_PROJECT_MODULES = (
    "heterodiff.evaluation.mixed_initializer_test28_supplied_development_"
    "output_validation_qualification",
    "heterodiff.evaluation.mixed_initializer_test28_supplied_interchange_"
    "recomputation_qualification",
)
CP73_TEST28_PREDECESSOR_PUBLIC_APIS = (
    "cp72_validate_supplied_cp71_development_output_bytes",
    "cp72_canonical_json_bytes",
    "cp72_sha256",
    "cp71_reduce_supplied_cp69_interchange_byte_stream",
    "cp71_canonical_json_bytes",
    "cp71_sha256",
)
CP73_TEST28_SUMMARY_CROSSCHECK_FIELDS = (
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
    ("rejection_first_attempt_row_sums", "rejection_first_attempt_row_sums"),
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
CP73_TEST28_SUMMARY_CROSSCHECK_FIELD_COUNT = 32
CP73_TEST28_MAXIMUM_INTERCHANGE_BYTES = 65_536
CP73_TEST28_MAXIMUM_STREAM_BYTES = 268_435_456
CP73_TEST28_MAXIMUM_OUTPUT_BYTES = 8_388_608
CP73_TEST28_MINIMUM_DECLARED_TOTAL_INPUT_BYTES = 32_768
CP73_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES = 268_435_456
CP73_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY = 554
CP73_TEST28_MAXIMUM_NEXT_CALLS = 32_769
CP73_TEST28_MAXIMUM_SEALED_RECORD_BYTES = 1_048_576
CP73_TEST28_ERROR_CODES = (
    "CP73_OUTPUT_VALIDATION_FAILED",
    "CP73_STREAM_RECOMPUTATION_FAILED",
    "CP73_OUTPUT_RELATION_MISMATCH",
    "CP73_RESOURCE_EXHAUSTED",
    "CP73_RECORD_TYPE_MISMATCH",
    "CP73_RECORD_NOT_ISSUED",
    "CP73_RECORD_TAMPERED",
    "CP73_INTERNAL_INVARIANT_FAILED",
)

_LEDGER_PREREQUISITE_STATE = (
    "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_" "ARTIFACTS"
)
_CP69_SCHEMA_VERSION = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_SEMANTIC_SCHEMA_VERSION = "cp63-test28-independent-compact-recomputation-v1"
_CP71_OUTPUT_SCHEMA_VERSION = (
    "cp71-test28-supplied-development-estimate-interval-output-v1"
)
_CP72_CP61_CROSSWALK_SHA256 = (
    "6861002c492af9f0a9f0212d954e4a0008bbeaa5749c23ec9ad5cb60c2c3da77"
)
_SUMMARY_CROSSCHECK_DOMAIN = b"cp73-test28-supplied-stream-output-summary-crosscheck-v1"
_SUMMARY_CROSSCHECK_PREIMAGE = (
    "domain||NUL||canonical-json({field_pairs:[[cp71-field,cp72-field],...],"
    "values:[cp71-value,...]});tuple-values-as-json-arrays"
)
_PREDECESSOR_ERROR_NORMALIZATION = (
    "cp72-input-codes-to-cp73-output-validation-failed",
    "cp72-resource-exhausted-to-cp73-resource-exhausted",
    "cp72-internal-record-unknown-or-invalid-return-to-cp73-internal-"
    "invariant-failed",
    "cp71-caller-stream-input-aggregate-and-output-limit-codes-to-cp73-"
    "stream-recomputation-failed",
    "cp71-resource-exhausted-to-cp73-resource-exhausted",
    "cp71-internal-record-unknown-or-invalid-return-to-cp73-internal-"
    "invariant-failed",
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
_ZERO_SHA256 = "0" * 64
_MAXIMUM_CANONICAL_DEPTH = 16
_MAXIMUM_CANONICAL_NODES = 32_768
_MAXIMUM_KEY_CHARACTERS = 256
_MAXIMUM_TEXT_CHARACTERS = 4_096

_V23_PROTOCOL_SHA256 = (
    "8b75852101a3849a22e50d66fa50c17353de18a77e34f381d56198926f6ed4f8"
)
_V23_PROTOCOL_BYTES = 246_105
_V23_PROTOCOL_LF_COUNT = 4_046
_V23_MANIFEST_SHA256 = (
    "8217f0d8ba14d241d2f8eb863c1372a46d7e99c352fe595b617b00afb163ea44"
)
_V23_MANIFEST_BYTES = 6_201_962
_V23_MANIFEST_LF_COUNT = 121_172
_CP69_SOURCE_SHA256 = "69f2ac19c37697f8c68dd8b4b312a12e0efc46c7df05f0157c310cf97e221dac"
_CP69_TEST_SHA256 = "c8179496c3986fcc6130ebccf9371b59956630cb8eada6e343f216adea13938c"
_CP69_BUNDLE_RECORD_SHA256 = (
    "39c937d3d78913fb7f91b777bc676648eddac6e38696b26973eb55a55becfe26"
)
_CP69_INTERCHANGE_CONTRACT_RECORD_SHA256 = (
    "6b64acc21209a7d32a1ddadcc45e0ced2f13eb94b87d571bd32f1d007b906caa"
)
_CP69_FULL_STREAM_EXPECTATION_RECORD_SHA256 = (
    "6043a6241ffc74ac14b395b052f87f22627beae43e2132992b2bb0e6a156289f"
)
_CP69_QUALIFICATION_RECORD_SHA256 = (
    "88dd43071ecf0545c9496e80b5de682ea9b7b0a5980a5fabe5b0f46f83586ab1"
)
_CP71_SOURCE_SHA256 = "9be57c44592b5cb80bf68e876de335c8e253ffc1a11aa14fed2ad82213a49078"
_CP71_TEST_SHA256 = "7eaefe615325a76c16f8bb0b843bde82337c7f72d8686a4bcbcc7a8f7fb38352"
_CP71_BUNDLE_RECORD_SHA256 = (
    "c49b4396c06f1ff792d2860176a2e318612bd12ad89ba3cf6f8804e2dc82169f"
)
_CP71_STREAM_CONTRACT_RECORD_SHA256 = (
    "5aca44ab2240dfd9040ca3323b7306b12bbe6ee47a2c0af3128002b387f3236c"
)
_CP71_OUTPUT_CONTRACT_RECORD_SHA256 = (
    "13a76a7ce7b0c665ef33aa6e55c122c87bf61aa676530c984ce2fdaf63e345a3"
)
_CP71_QUALIFICATION_RECORD_SHA256 = (
    "aa25726473f54c17b3179ebabbaace3671e9815a6d3b4eec834ad6c1b8490611"
)
_CP71_FIXTURE_SET_SHA256 = (
    "bb4347afaca9e0ea41cb5b38ac74a3186b63fd95da9b4546b50de6aa1ffa83af"
)
_CP72_SOURCE_SHA256 = "78f0558f318e45032b06856d21986d84fe53937185d9d005e395c2874df5167c"
_CP72_TEST_SHA256 = "ab4b2c5a74157863a621b59061b3ea38c872cbe1a9d30129c9ffc5922b5d4641"
_CP72_BUNDLE_RECORD_SHA256 = (
    "ecbe0e07e02d7d1ee930fc65b558bd4a5f655da78b950cc8df616e2cc410fc70"
)
_CP72_VALIDATION_CONTRACT_RECORD_SHA256 = (
    "3768a8c5a70b137bc37553dd8e66fc3a9b66b51073c13a2a5d53b5ed8ae70b13"
)
_CP72_QUALIFICATION_RECORD_SHA256 = (
    "2202dc80acf16f0b7a59582979483bed60f19d6f57b2e86d044b68224518ac27"
)
_CP72_FIXTURE_SET_SHA256 = (
    "58ca1ff512558ca10fc4bdc447474aaf0ee04decd272954a85fff3e56c89941d"
)


class CP73SuppliedStreamOutputRelationQualificationError(RuntimeError):
    """Fail-closed CP73 error with stable phase and predecessor codes."""

    def __init__(
        self,
        code: str,
        message: str,
        predecessor_error_code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.predecessor_error_code = predecessor_error_code


_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP73 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP73 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP73 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP73PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    v23_protocol_sha256: str
    v23_protocol_bytes: int
    v23_protocol_lf_count: int
    v23_manifest_sha256: str
    v23_manifest_bytes: int
    v23_manifest_lf_count: int
    cp69_source_sha256: str
    cp69_test_sha256: str
    cp69_bundle_record_sha256: str
    cp69_interchange_contract_record_sha256: str
    cp69_full_stream_expectation_record_sha256: str
    cp69_qualification_record_sha256: str
    cp71_source_sha256: str
    cp71_test_sha256: str
    cp71_bundle_record_sha256: str
    cp71_stream_contract_record_sha256: str
    cp71_output_contract_record_sha256: str
    cp71_qualification_record_sha256: str
    cp71_fixture_set_sha256: str
    cp72_source_sha256: str
    cp72_test_sha256: str
    cp72_bundle_record_sha256: str
    cp72_validation_contract_record_sha256: str
    cp72_qualification_record_sha256: str
    cp72_fixture_set_sha256: str
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP73SuppliedStreamOutputRelationContractV1(_SealedRecord):
    schema_version: str
    contract_id: str
    source_interchange_schema_version: str
    source_semantic_schema_version: str
    source_output_schema_version: str
    cp71_reduction_summary_schema_version: str
    cp72_validation_summary_schema_version: str
    output_payload_exact_type: str
    interchange_payloads_consumption: str
    phase_order: Tuple[str, ...]
    predecessor_error_normalization: Tuple[str, ...]
    failure_precedence: Tuple[str, ...]
    project_module_names: Tuple[str, ...]
    predecessor_public_api_names: Tuple[str, ...]
    project_modules_imported: bool
    source_independent: bool
    stdlib_only: bool
    stdlib_only_beyond_exact_predecessor_modules: bool
    third_party_modules_imported: bool
    public_api_uses_predecessor_public_apis_only: bool
    output_validation_completes_before_stream_iteration: bool
    invalid_output_iter_calls: int
    invalid_output_next_calls: int
    invalid_output_close_calls: int
    cp72_validator_exact_call_count: int
    cp71_reducer_maximum_call_count: int
    cp71_reducer_exact_call_count_after_output_validation: int
    exact_output_byte_relation_required: bool
    exact_output_byte_comparison: str
    summary_crosscheck_fields: Tuple[Tuple[str, str], ...]
    summary_crosscheck_field_count: int
    summary_crosscheck_required: bool
    cp71_fixed_nonclaims_checked: bool
    cp71_stream_coherence_claims_checked: bool
    cp72_validation_claims_checked: bool
    relation_verified_meaning: str
    caller_iterable_side_effects_qualified: bool
    caller_iterable_retention_qualified: bool
    caller_next_liveness_qualified: bool
    iterator_close_called: bool
    maximum_next_calls: int
    maximum_interchange_bytes: int
    maximum_stream_bytes: int
    maximum_output_bytes: int
    minimum_declared_total_input_bytes: int
    maximum_declared_total_input_bytes: int
    maximum_output_vector_cardinality: int
    maximum_sealed_record_bytes: int
    caller_output_bytes_returned: bool
    recomputed_output_bytes_returned: bool
    caller_summary_accepted: bool
    predecessor_summary_returned: bool
    scalar_summary_only: bool
    caller_output_retained_after_successful_return: bool
    recomputed_output_retained_after_successful_return: bool
    module_owned_predecessor_summary_references_retained_after_successful_return: bool
    predecessor_summary_issuance_on_late_failure_possible: bool
    predecessor_weak_registry_entries_recoverable_after_all_strong_references_released: bool
    exception_traceback_retention_qualified: bool
    no_cp73_record_issued_before_relation_complete: bool
    cp73_partial_return_on_failure: bool
    dynamic_input_payload_or_output_body_cached: bool
    sealed_summary_snapshot_retained_while_summary_live: bool
    module_direct_filesystem_read: bool
    module_direct_filesystem_write: bool
    module_direct_clock_read: bool
    module_direct_rng_used: bool
    module_direct_network_used: bool
    module_direct_subprocess_used: bool
    input_provenance_authenticated: bool
    runtime_lock_authenticated: bool
    request_instance_sha256_authenticated: bool
    stable_trace_sha256_authenticated: bool
    external_seed_source_verified: bool
    source_law_verified: bool
    production_attempt_validity_evaluated: bool
    production_recomputation_qualified: bool
    operational_prediction: bool
    power_review_present: bool
    primary_thresholds_present: bool
    decision_made: bool
    production_evidence: bool
    confirmatory_custody_present: bool
    production_gate_13_state: str
    production_gate_14_state: str
    formal_test_28_status: str
    summary_crosscheck_digest_domain: str
    summary_crosscheck_digest_preimage: str
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP73SuppliedStreamOutputRelationSummaryV1(_SealedRecord):
    schema_version: str
    source_interchange_schema_version: str
    source_semantic_schema_version: str
    source_output_schema_version: str
    request_count: int
    total_input_bytes: int
    input_stream_commitment_sha256: str
    ordered_interchange_record_sha256: str
    ordered_projection_sha256: str
    ordered_seed_ordinal_plan_seed_sha256: str
    ordered_request_instance_sha256: str
    ordered_stable_trace_sha256: str
    runtime_lock_sha256: str
    runtime_lock_authenticated: bool
    request_instance_sha256_authenticated: bool
    stable_trace_sha256_authenticated: bool
    feature_estimate_present_count: int
    feature_estimate_absent_count: int
    binomial_interval_count: int
    feature_interval_count: int
    computed_interval_count: int
    insufficient_selection_count: int
    distinct_binomial_success_count_count: int
    ordered_estimand_record_sha256s_sha256: str
    output_body_sha256: str
    output_canonical_json_bytes: int
    output_canonical_json_sha256: str
    cp71_reduction_summary_record_sha256: str
    cp71_reduction_summary_public_sha256: str
    cp72_validation_summary_record_sha256: str
    cp72_validation_summary_public_sha256: str
    cp72_ordered_cp61_inventory_crosswalk_sha256: str
    cp72_exact_endpoint_boundary_comparison_count: int
    summary_crosscheck_field_count: int
    summary_crosscheck_sha256: str
    output_validated_before_stream_iteration: bool
    stream_recomputed_once: bool
    output_bytes_exact_match: bool
    summary_crosscheck_verified: bool
    input_stream_relation_verified: bool
    external_seed_source_verified: bool
    production_recomputation: bool
    input_provenance_authenticated: bool
    source_law_verified: bool
    production_attempt_validity_evaluated: bool
    operational_prediction: bool
    power_review_present: bool
    primary_thresholds_present: bool
    decision_made: bool
    production_evidence: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP73SuppliedStreamOutputRelationQualificationBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    blocker_ledger_prerequisite_id: str
    blocker_ledger_prerequisite_state: str
    blocker_ledger_total_count: int
    blocker_ledger_satisfied_count: int
    blocker_ledger_missing_count: int
    predecessor_custody: CP73PredecessorCustodyV1
    relation_contract: CP73SuppliedStreamOutputRelationContractV1
    zero_argument_builder: bool
    builder_validates: bool
    qualification_runner_exposed: bool
    module_owned_fixture_count: int
    module_owned_stream_body_count: int
    module_owned_output_body_count: int
    external_test_qualification_required: bool
    public_supplied_stream_output_relation_validator_exposed: bool
    public_caller_data_api_count: int
    public_parser_exposed: bool
    public_stream_reducer_exposed: bool
    public_output_validator_exposed: bool
    public_summary_input_api_exposed: bool
    public_output_bytes_returned: bool
    public_path_api_exposed: bool
    public_writer_api_exposed: bool
    public_runner_api_exposed: bool
    public_primary_decision_threshold_api_exposed: bool
    public_decision_api_exposed: bool
    public_receipt_or_evidence_api_exposed: bool
    project_modules_imported: bool
    project_module_count: int
    source_independent: bool
    stdlib_only: bool
    stdlib_only_beyond_exact_predecessor_modules: bool
    third_party_modules_imported: bool
    predecessor_public_apis_only: bool
    module_direct_filesystem_read: bool
    module_direct_filesystem_write: bool
    module_direct_clock_read: bool
    module_direct_rng_used: bool
    module_direct_network_used: bool
    module_direct_subprocess_used: bool
    production_execution_authorized: bool
    production_recomputation_qualified: bool
    unconditional_operational_predictions_produced: bool
    power_review_present: bool
    primary_thresholds_present: bool
    confirmatory_custody_present: bool
    runtime_lock_authenticated: bool
    request_instance_sha256_authenticated: bool
    stable_trace_sha256_authenticated: bool
    production_gate_13_state: str
    production_gate_14_state: str
    runner_and_recomputation_blocker_closed: bool
    unconditional_operational_predictions_blocker_closed: bool
    power_and_thresholds_blocker_closed: bool
    confirmatory_custody_blocker_closed: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_RECORD_DOMAINS = {
    CP73PredecessorCustodyV1: b"cp73-test28-predecessor-custody-v1",
    CP73SuppliedStreamOutputRelationContractV1: (
        b"cp73-test28-supplied-stream-output-relation-contract-v1"
    ),
    CP73SuppliedStreamOutputRelationSummaryV1: (
        b"cp73-test28-supplied-stream-output-relation-summary-v1"
    ),
    CP73SuppliedStreamOutputRelationQualificationBundleV1: (
        b"cp73-test28-supplied-stream-output-relation-qualification-bundle-v1"
    ),
}
_NESTED_RECORD_FIELD_TYPES = {
    CP73SuppliedStreamOutputRelationQualificationBundleV1: (
        ("predecessor_custody", CP73PredecessorCustodyV1),
        ("relation_contract", CP73SuppliedStreamOutputRelationContractV1),
    )
}
_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS = cast(
    "weakref.WeakKeyDictionary[_SealedRecord, Tuple[bytes, object, Tuple[_SealedRecord, ...]]]",
    weakref.WeakKeyDictionary(),
)


def _fail(
    code: str,
    message: str,
    predecessor_error_code: Optional[str] = None,
) -> None:
    raise CP73SuppliedStreamOutputRelationQualificationError(
        code, message, predecessor_error_code
    )


def _plain_json_value(
    value: object,
    *,
    depth: int = 1,
    nodes: Optional[list[int]] = None,
    active: Optional[set[int]] = None,
) -> object:
    if nodes is None:
        nodes = [0]
    if active is None:
        active = set()
    nodes[0] += 1
    if nodes[0] > _MAXIMUM_CANONICAL_NODES:
        raise ValueError("canonical graph exceeds node cap")
    if depth > _MAXIMUM_CANONICAL_DEPTH:
        raise ValueError("canonical graph exceeds depth cap")
    if value is None or type(value) is bool or type(value) is int:
        return value
    if type(value) is str:
        if len(cast(str, value)) > _MAXIMUM_TEXT_CHARACTERS:
            raise ValueError("canonical text exceeds character cap")
        return value
    if type(value) in _RECORD_DOMAINS:
        identity = id(value)
        if identity in active:
            raise ValueError("canonical graph contains a cycle")
        active.add(identity)
        try:
            return {
                item.name: _plain_json_value(
                    getattr(value, item.name),
                    depth=depth + 1,
                    nodes=nodes,
                    active=active,
                )
                for item in fields(type(value))
            }
        finally:
            active.remove(identity)
    if type(value) is tuple or type(value) is list:
        identity = id(value)
        if identity in active:
            raise ValueError("canonical graph contains a cycle")
        active.add(identity)
        try:
            return [
                _plain_json_value(item, depth=depth + 1, nodes=nodes, active=active)
                for item in cast(object, value)
            ]
        finally:
            active.remove(identity)
    if type(value) is dict:
        identity = id(value)
        if identity in active:
            raise ValueError("canonical graph contains a cycle")
        active.add(identity)
        try:
            result = {}
            for key, item in cast(dict, value).items():
                if type(key) is not str or len(key) > _MAXIMUM_KEY_CHARACTERS:
                    raise TypeError("canonical mapping key is invalid")
                result[key] = _plain_json_value(
                    item, depth=depth + 1, nodes=nodes, active=active
                )
            return result
        finally:
            active.remove(identity)
    raise TypeError("unsupported canonical value type")


def _plain_json_bytes(
    value: object,
    maximum_bytes: int = CP73_TEST28_MAXIMUM_SEALED_RECORD_BYTES,
) -> bytes:
    payload = json.dumps(
        _plain_json_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if len(payload) > maximum_bytes:
        raise ValueError("canonical bytes exceed cap")
    return payload


def _typed_shape(
    value: object,
    *,
    depth: int,
    nodes: list[int],
    active: set[int],
    nested_records: list[_SealedRecord],
) -> object:
    nodes[0] += 1
    if nodes[0] > _MAXIMUM_CANONICAL_NODES or depth > _MAXIMUM_CANONICAL_DEPTH:
        raise ValueError("typed graph exceeds cap")
    if value is None:
        return ("none",)
    if type(value) is bool:
        return ("bool", value)
    if type(value) is int:
        return ("int", value)
    if type(value) is str:
        return ("str", value)
    if type(value) in _RECORD_DOMAINS:
        nested_records.append(cast(_SealedRecord, value))
        return ("record", type(value).__name__, id(value))
    if type(value) is tuple or type(value) is list:
        identity = id(value)
        if identity in active:
            raise ValueError("typed graph contains a cycle")
        active.add(identity)
        try:
            return (
                "tuple" if type(value) is tuple else "list",
                tuple(
                    _typed_shape(
                        item,
                        depth=depth + 1,
                        nodes=nodes,
                        active=active,
                        nested_records=nested_records,
                    )
                    for item in cast(object, value)
                ),
            )
        finally:
            active.remove(identity)
    if type(value) is dict:
        identity = id(value)
        if identity in active:
            raise ValueError("typed graph contains a cycle")
        active.add(identity)
        try:
            entries = []
            for key, item in cast(dict, value).items():
                if type(key) is not str:
                    raise TypeError("typed mapping key is invalid")
                entries.append(
                    (
                        key,
                        _typed_shape(
                            item,
                            depth=depth + 1,
                            nodes=nodes,
                            active=active,
                            nested_records=nested_records,
                        ),
                    )
                )
            return ("dict", tuple(sorted(entries, key=lambda entry: entry[0])))
        finally:
            active.remove(identity)
    return ("unsupported", type(value).__module__, type(value).__qualname__)


def _typed_record_state(
    record: _SealedRecord,
) -> Tuple[object, Tuple[_SealedRecord, ...]]:
    nested_records: list[_SealedRecord] = []
    nodes = [1]
    shape = (
        "record-root",
        type(record).__name__,
        tuple(
            (
                item.name,
                _typed_shape(
                    getattr(record, item.name),
                    depth=2,
                    nodes=nodes,
                    active={id(record)},
                    nested_records=nested_records,
                ),
            )
            for item in fields(type(record))
        ),
    )
    return shape, tuple(nested_records)


def _validate_nested_record_field_types(record: _SealedRecord) -> None:
    for name, expected_type in _NESTED_RECORD_FIELD_TYPES.get(type(record), ()):
        if type(getattr(record, name)) is not expected_type:
            raise TypeError("nested sealed-record field has wrong exact type")


def _record(cls: type, values: Mapping[str, object]) -> object:
    if cls not in _RECORD_DOMAINS:
        raise TypeError("unsupported CP73 record class")
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP73 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(complete)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    sealed = cast(_SealedRecord, result)
    snapshot = _plain_json_bytes(sealed)
    typed_snapshot, nested_records = _typed_record_state(sealed)
    _validate_nested_record_field_types(sealed)
    for nested_record in nested_records:
        _require_issued_record(nested_record)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[sealed] = (
            snapshot,
            typed_snapshot,
            nested_records,
        )
    return result


def _require_issued_record_inner(
    value: object, *, active: set[int], nodes: list[int]
) -> Tuple[_SealedRecord, bytes]:
    if type(value) not in _RECORD_DOMAINS:
        _fail("CP73_RECORD_TYPE_MISMATCH", "record has unsupported exact type")
    record = cast(_SealedRecord, value)
    with _ISSUED_RECORD_LOCK:
        issued = _ISSUED_RECORD_SNAPSHOTS.get(record)
    if issued is None:
        _fail("CP73_RECORD_NOT_ISSUED", "record was not issued by CP73")
    identity = id(record)
    nodes[0] += 1
    if (
        nodes[0] > _MAXIMUM_CANONICAL_NODES
        or len(active) >= _MAXIMUM_CANONICAL_DEPTH
        or identity in active
    ):
        _fail("CP73_RECORD_TAMPERED", "issued-record graph is not bounded")
    active.add(identity)
    try:
        snapshot, typed_snapshot, issued_nested = issued
        try:
            current_typed, nested = _typed_record_state(record)
            _validate_nested_record_field_types(record)
        except MemoryError:
            raise
        except Exception as exc:
            raise CP73SuppliedStreamOutputRelationQualificationError(
                "CP73_RECORD_TAMPERED", "issued record typed shape is invalid"
            ) from exc
        if (
            current_typed != typed_snapshot
            or len(nested) != len(issued_nested)
            or any(
                current is not original
                for current, original in zip(nested, issued_nested)
            )
        ):
            _fail("CP73_RECORD_TAMPERED", "issued record typed state was mutated")
        for child in nested:
            try:
                _require_issued_record_inner(child, active=active, nodes=nodes)
            except MemoryError:
                raise
            except CP73SuppliedStreamOutputRelationQualificationError as exc:
                if exc.code == "CP73_RESOURCE_EXHAUSTED":
                    raise
                raise CP73SuppliedStreamOutputRelationQualificationError(
                    "CP73_RECORD_TAMPERED", "nested issued record is invalid"
                ) from exc
        try:
            current = _plain_json_bytes(record)
            body = {
                item.name: getattr(record, item.name) for item in fields(type(record))
            }
            supplied = body["record_sha256"]
            body["record_sha256"] = _ZERO_SHA256
            expected = hashlib.sha256(
                _RECORD_DOMAINS[type(record)] + b"\0" + _plain_json_bytes(body)
            ).hexdigest()
        except MemoryError:
            raise
        except Exception as exc:
            raise CP73SuppliedStreamOutputRelationQualificationError(
                "CP73_RECORD_TAMPERED", "issued record cannot be reserialized"
            ) from exc
        if not hmac.compare_digest(snapshot, current):
            _fail("CP73_RECORD_TAMPERED", "issued record bytes were mutated")
        if type(supplied) is not str or not hmac.compare_digest(
            cast(str, supplied), expected
        ):
            _fail("CP73_RECORD_TAMPERED", "issued record digest differs")
        return record, snapshot
    finally:
        active.remove(identity)


def _require_issued_record(value: object) -> Tuple[_SealedRecord, bytes]:
    try:
        return _require_issued_record_inner(value, active=set(), nodes=[0])
    except CP73SuppliedStreamOutputRelationQualificationError:
        raise
    except MemoryError as exc:
        raise CP73SuppliedStreamOutputRelationQualificationError(
            "CP73_RESOURCE_EXHAUSTED", "issued-record validation exhausted memory"
        ) from exc
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        raise CP73SuppliedStreamOutputRelationQualificationError(
            "CP73_RECORD_TAMPERED", "issued-record validation failed closed"
        ) from exc


def cp73_canonical_json_bytes(value: object) -> bytes:
    """Return canonical bytes for one unchanged CP73-issued record."""

    return _require_issued_record(value)[1]


def cp73_sha256(value: object) -> str:
    """Return the tagged public digest of one unchanged CP73-issued record."""

    record, snapshot = _require_issued_record(value)
    return hashlib.sha256(
        b"cp73-public-record-v1\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + snapshot
    ).hexdigest()


_CP72_VALIDATE = cp72_validate_supplied_cp71_development_output_bytes
_CP72_CANONICAL_JSON_BYTES = cp72_canonical_json_bytes
_CP72_SHA256 = cp72_sha256
_CP71_REDUCE = cp71_reduce_supplied_cp69_interchange_byte_stream
_CP71_CANONICAL_JSON_BYTES = cp71_canonical_json_bytes
_CP71_SHA256 = cp71_sha256


def _raise_wrapped_predecessor(
    code: str,
    message: str,
    predecessor_error_code: Optional[str],
    cause: BaseException,
) -> None:
    raise CP73SuppliedStreamOutputRelationQualificationError(
        code, message, predecessor_error_code
    ) from cause


def _normalize_cp72_error(
    error: CP72SuppliedDevelopmentOutputValidationQualificationError,
) -> None:
    predecessor_code = error.code if type(error.code) is str else None
    if predecessor_code == "CP72_RESOURCE_EXHAUSTED":
        _raise_wrapped_predecessor(
            "CP73_RESOURCE_EXHAUSTED",
            "output validation exhausted bounded resources",
            predecessor_code,
            error,
        )
    if (
        predecessor_code not in CP72_TEST28_ERROR_CODES
        or predecessor_code == "CP72_INTERNAL_INVARIANT_FAILED"
        or cast(str, predecessor_code).startswith("CP72_RECORD_")
    ):
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "output validator failed its frozen internal contract",
            predecessor_code,
            error,
        )
    _raise_wrapped_predecessor(
        "CP73_OUTPUT_VALIDATION_FAILED",
        "supplied output failed bounded CP72 validation",
        predecessor_code,
        error,
    )


def _normalize_cp71_error(
    error: CP71SuppliedInterchangeRecomputationQualificationError,
) -> None:
    predecessor_code = error.code if type(error.code) is str else None
    if predecessor_code == "CP71_RESOURCE_EXHAUSTED":
        _raise_wrapped_predecessor(
            "CP73_RESOURCE_EXHAUSTED",
            "stream recomputation exhausted bounded resources",
            predecessor_code,
            error,
        )
    if (
        predecessor_code not in CP71_TEST28_ERROR_CODES
        or predecessor_code == "CP71_INTERNAL_INVARIANT_FAILED"
        or cast(str, predecessor_code).startswith("CP71_RECORD_")
    ):
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "stream reducer failed its frozen internal contract",
            predecessor_code,
            error,
        )
    _raise_wrapped_predecessor(
        "CP73_STREAM_RECOMPUTATION_FAILED",
        "supplied stream failed bounded CP71 recomputation",
        predecessor_code,
        error,
    )


def _is_exact_nonnegative_int(value: object) -> bool:
    return type(value) is int and cast(int, value) >= 0


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(cast(str, value)) == 64
        and all(character in "0123456789abcdef" for character in cast(str, value))
    )


def _is_bounded_int_tuple(
    value: object, *, length: int, minimum: int, maximum: int
) -> bool:
    return (
        type(value) is tuple
        and len(cast(tuple, value)) == length
        and all(
            type(item) is int and minimum <= cast(int, item) <= maximum
            for item in cast(tuple, value)
        )
    )


def _validate_cp72_return(
    summary: object, output_payload: object
) -> Tuple[CP72SuppliedDevelopmentOutputValidationSummaryV1, str]:
    if type(summary) is not CP72SuppliedDevelopmentOutputValidationSummaryV1:
        _fail(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "output validator returned an unexpected summary type",
        )
    typed = cast(CP72SuppliedDevelopmentOutputValidationSummaryV1, summary)
    try:
        _CP72_CANONICAL_JSON_BYTES(typed)
        public_sha256 = _CP72_SHA256(typed)
    except CP72SuppliedDevelopmentOutputValidationQualificationError as exc:
        predecessor_code = exc.code if type(exc.code) is str else None
        if predecessor_code == "CP72_RESOURCE_EXHAUSTED":
            _raise_wrapped_predecessor(
                "CP73_RESOURCE_EXHAUSTED",
                "output summary validation exhausted bounded resources",
                predecessor_code,
                exc,
            )
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "output validator returned an invalid sealed summary",
            predecessor_code,
            exc,
        )
    except MemoryError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "output summary validation failed closed",
            None,
            exc,
        )
    if type(output_payload) is not bytes:
        _fail(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "output validator admitted a non-byte payload",
        )
    expected_true = (
        "stream_commitment_coherence_verified",
        "canonical_json_verified",
        "schema_verified",
        "estimand_inventory_and_order_verified",
        "record_digests_verified",
        "cross_record_arithmetic_verified",
        "exact_interval_arithmetic_verified",
    )
    expected_false = (
        "input_stream_relation_verified",
        "input_provenance_authenticated",
        "source_law_verified",
        "production_attempt_validity_evaluated",
        "operational_prediction",
        "power_review_present",
        "primary_thresholds_present",
        "decision_made",
        "production_evidence",
    )
    if (
        typed.schema_version != CP72_TEST28_SCHEMA_VERSION
        or typed.source_output_schema_version != _CP71_OUTPUT_SCHEMA_VERSION
        or typed.request_count != CP73_TEST28_REQUEST_COUNT
        or typed.estimand_count != CP73_TEST28_ESTIMAND_COUNT
        or typed.observable_estimand_count != 72
        or typed.rejection_first_attempt_estimand_count != 170
        or typed.feature_estimand_count != 312
        or typed.binomial_estimand_count != 242
        or not _is_exact_nonnegative_int(typed.declared_total_input_bytes)
        or not CP73_TEST28_MINIMUM_DECLARED_TOTAL_INPUT_BYTES
        <= typed.declared_total_input_bytes
        <= CP73_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES
        or typed.output_canonical_json_bytes != len(cast(bytes, output_payload))
        or typed.output_canonical_json_bytes <= 0
        or typed.output_canonical_json_bytes > CP73_TEST28_MAXIMUM_OUTPUT_BYTES
        or not hmac.compare_digest(
            typed.output_canonical_json_sha256,
            hashlib.sha256(cast(bytes, output_payload)).hexdigest(),
        )
        or not hmac.compare_digest(
            typed.ordered_cp61_inventory_crosswalk_sha256,
            _CP72_CP61_CROSSWALK_SHA256,
        )
        or not all(
            _is_sha256(value)
            for value in (
                typed.declared_input_stream_commitment_sha256,
                typed.declared_ordered_interchange_record_sha256,
                typed.declared_ordered_projection_sha256,
                typed.declared_ordered_seed_ordinal_plan_seed_sha256,
                typed.declared_ordered_request_instance_sha256,
                typed.declared_ordered_stable_trace_sha256,
                typed.declared_runtime_lock_sha256,
                typed.ordered_estimand_record_sha256s_sha256,
                typed.output_body_sha256,
                typed.output_canonical_json_sha256,
            )
        )
        or not _is_bounded_int_tuple(
            typed.selected_counts_by_row,
            length=CP73_TEST28_ROW_COUNT,
            minimum=0,
            maximum=CP73_TEST28_SEED_COUNT,
        )
        or not _is_bounded_int_tuple(
            typed.observable_row_sums,
            length=CP73_TEST28_ROW_COUNT,
            minimum=CP73_TEST28_SEED_COUNT,
            maximum=CP73_TEST28_SEED_COUNT,
        )
        or not _is_bounded_int_tuple(
            typed.rejection_first_attempt_row_sums,
            length=8,
            minimum=0,
            maximum=CP73_TEST28_SEED_COUNT,
        )
        or not all(
            _is_exact_nonnegative_int(value)
            for value in (
                typed.feature_estimate_present_count,
                typed.feature_estimate_absent_count,
                typed.binomial_interval_count,
                typed.feature_interval_count,
                typed.computed_interval_count,
                typed.insufficient_selection_count,
                typed.distinct_binomial_success_count_count,
            )
        )
        or typed.feature_estimate_present_count + typed.feature_estimate_absent_count
        != 312
        or typed.binomial_interval_count != 242
        or typed.computed_interval_count
        != typed.binomial_interval_count + typed.feature_interval_count
        or typed.insufficient_selection_count != 312 - typed.feature_interval_count
        or not 1 <= typed.distinct_binomial_success_count_count <= 2_049
        or not _is_exact_nonnegative_int(typed.exact_endpoint_boundary_comparison_count)
        or any(getattr(typed, name) is not True for name in expected_true)
        or any(getattr(typed, name) is not False for name in expected_false)
        or not _is_sha256(typed.record_sha256)
        or not _is_sha256(public_sha256)
    ):
        _fail(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "output validation summary differs from its frozen contract",
        )
    return typed, public_sha256


def _complete_output_validation_before_stream_touch(
    output_payload: object,
) -> Tuple[CP72SuppliedDevelopmentOutputValidationSummaryV1, str]:
    try:
        summary = _CP72_VALIDATE(output_payload)
    except CP72SuppliedDevelopmentOutputValidationQualificationError as exc:
        _normalize_cp72_error(exc)
    except MemoryError as exc:
        _raise_wrapped_predecessor(
            "CP73_RESOURCE_EXHAUSTED",
            "output validation exhausted bounded resources",
            None,
            exc,
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "output validation failed closed",
            None,
            exc,
        )
    return _validate_cp72_return(summary, output_payload)


def _validate_cp71_return(
    result: object,
) -> Tuple[bytes, CP71SuppliedDevelopmentReductionSummaryV1, str]:
    if type(result) is not tuple or len(cast(tuple, result)) != 2:
        _fail(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "stream reducer returned an unexpected outer value",
        )
    recomputed_output, summary = cast(tuple, result)
    if type(recomputed_output) is not bytes:
        _fail(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "stream reducer returned a non-byte output",
        )
    if type(summary) is not CP71SuppliedDevelopmentReductionSummaryV1:
        _fail(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "stream reducer returned an unexpected summary type",
        )
    typed = cast(CP71SuppliedDevelopmentReductionSummaryV1, summary)
    try:
        _CP71_CANONICAL_JSON_BYTES(typed)
        public_sha256 = _CP71_SHA256(typed)
    except CP71SuppliedInterchangeRecomputationQualificationError as exc:
        predecessor_code = exc.code if type(exc.code) is str else None
        if predecessor_code == "CP71_RESOURCE_EXHAUSTED":
            _raise_wrapped_predecessor(
                "CP73_RESOURCE_EXHAUSTED",
                "reduction summary validation exhausted bounded resources",
                predecessor_code,
                exc,
            )
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "stream reducer returned an invalid sealed summary",
            predecessor_code,
            exc,
        )
    except MemoryError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "reduction summary validation failed closed",
            None,
            exc,
        )
    expected_true = (
        "plan_seed_row_group_coherence_verified",
        "row_seed_free_request_sha256s_matched",
        "runtime_lock_stream_coherence_verified",
    )
    expected_false = (
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
    )
    if (
        typed.schema_version != CP71_TEST28_SCHEMA_VERSION
        or typed.source_interchange_schema_version != _CP69_SCHEMA_VERSION
        or typed.source_semantic_schema_version != _CP63_SEMANTIC_SCHEMA_VERSION
        or typed.output_schema_version != _CP71_OUTPUT_SCHEMA_VERSION
        or typed.request_count != CP73_TEST28_REQUEST_COUNT
        or typed.seed_count != CP73_TEST28_SEED_COUNT
        or typed.row_count != CP73_TEST28_ROW_COUNT
        or not _is_exact_nonnegative_int(typed.total_input_bytes)
        or not CP73_TEST28_MINIMUM_DECLARED_TOTAL_INPUT_BYTES
        <= typed.total_input_bytes
        <= CP73_TEST28_MAXIMUM_STREAM_BYTES
        or typed.output_canonical_json_bytes != len(recomputed_output)
        or typed.output_canonical_json_bytes <= 0
        or typed.output_canonical_json_bytes > CP73_TEST28_MAXIMUM_OUTPUT_BYTES
        or not hmac.compare_digest(
            typed.output_canonical_json_sha256,
            hashlib.sha256(recomputed_output).hexdigest(),
        )
        or not all(
            _is_sha256(value)
            for value in (
                typed.input_stream_commitment_sha256,
                typed.ordered_interchange_record_sha256,
                typed.ordered_projection_sha256,
                typed.ordered_seed_ordinal_plan_seed_sha256,
                typed.ordered_request_instance_sha256,
                typed.ordered_stable_trace_sha256,
                typed.runtime_lock_sha256,
                typed.ordered_estimand_record_sha256s_sha256,
                typed.output_body_sha256,
                typed.output_canonical_json_sha256,
            )
        )
        or not _is_bounded_int_tuple(
            typed.selected_counts_by_row,
            length=CP73_TEST28_ROW_COUNT,
            minimum=0,
            maximum=CP73_TEST28_SEED_COUNT,
        )
        or not _is_bounded_int_tuple(
            typed.observable_row_sums,
            length=CP73_TEST28_ROW_COUNT,
            minimum=CP73_TEST28_SEED_COUNT,
            maximum=CP73_TEST28_SEED_COUNT,
        )
        or not _is_bounded_int_tuple(
            typed.rejection_first_attempt_row_sums,
            length=8,
            minimum=0,
            maximum=CP73_TEST28_SEED_COUNT,
        )
        or not _is_bounded_int_tuple(
            typed.status_counts,
            length=6,
            minimum=0,
            maximum=CP73_TEST28_REQUEST_COUNT,
        )
        or sum(typed.status_counts) != CP73_TEST28_REQUEST_COUNT
        or not all(
            _is_exact_nonnegative_int(value)
            for value in (
                typed.feature_estimate_present_count,
                typed.feature_estimate_absent_count,
                typed.binomial_interval_count,
                typed.feature_interval_count,
                typed.computed_interval_count,
                typed.insufficient_selection_count,
                typed.distinct_cp_success_count_count,
            )
        )
        or typed.feature_estimate_present_count + typed.feature_estimate_absent_count
        != 312
        or typed.binomial_interval_count != 242
        or typed.computed_interval_count
        != typed.binomial_interval_count + typed.feature_interval_count
        or typed.insufficient_selection_count != 312 - typed.feature_interval_count
        or not 1 <= typed.distinct_cp_success_count_count <= 2_049
        or any(getattr(typed, name) is not True for name in expected_true)
        or any(getattr(typed, name) is not False for name in expected_false)
        or not _is_sha256(typed.record_sha256)
        or not _is_sha256(public_sha256)
    ):
        _fail(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "stream reduction summary differs from its frozen contract",
        )
    return recomputed_output, typed, public_sha256


def _recompute_stream_once(
    interchange_payloads: object,
) -> Tuple[bytes, CP71SuppliedDevelopmentReductionSummaryV1, str]:
    try:
        result = _CP71_REDUCE(interchange_payloads)
    except CP71SuppliedInterchangeRecomputationQualificationError as exc:
        _normalize_cp71_error(exc)
    except MemoryError as exc:
        _raise_wrapped_predecessor(
            "CP73_RESOURCE_EXHAUSTED",
            "stream recomputation exhausted bounded resources",
            None,
            exc,
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        _raise_wrapped_predecessor(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "stream recomputation failed closed",
            None,
            exc,
        )
    return _validate_cp71_return(result)


def _exact_typed_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is str:
        return hmac.compare_digest(cast(str, left), cast(str, right))
    if type(left) is tuple:
        left_tuple = cast(tuple, left)
        right_tuple = cast(tuple, right)
        return len(left_tuple) == len(right_tuple) and all(
            _exact_typed_equal(left_item, right_item)
            for left_item, right_item in zip(left_tuple, right_tuple)
        )
    return left == right


def _summary_crosscheck_sha256(
    cp71_summary: CP71SuppliedDevelopmentReductionSummaryV1,
    cp72_summary: CP72SuppliedDevelopmentOutputValidationSummaryV1,
) -> str:
    values = []
    for cp71_name, cp72_name in CP73_TEST28_SUMMARY_CROSSCHECK_FIELDS:
        left = getattr(cp71_summary, cp71_name)
        right = getattr(cp72_summary, cp72_name)
        if not _exact_typed_equal(left, right):
            _fail(
                "CP73_INTERNAL_INVARIANT_FAILED",
                "predecessor summaries differ after exact output equality",
            )
        values.append(left)
    return hashlib.sha256(
        _SUMMARY_CROSSCHECK_DOMAIN
        + b"\0"
        + _plain_json_bytes(
            {
                "field_pairs": CP73_TEST28_SUMMARY_CROSSCHECK_FIELDS,
                "values": tuple(values),
            }
        )
    ).hexdigest()


def _relation_summary_values(
    cp71_summary: CP71SuppliedDevelopmentReductionSummaryV1,
    cp71_public_sha256: str,
    cp72_summary: CP72SuppliedDevelopmentOutputValidationSummaryV1,
    cp72_public_sha256: str,
    crosscheck_sha256: str,
) -> Mapping[str, object]:
    return {
        "schema_version": CP73_TEST28_SCHEMA_VERSION,
        "source_interchange_schema_version": _CP69_SCHEMA_VERSION,
        "source_semantic_schema_version": _CP63_SEMANTIC_SCHEMA_VERSION,
        "source_output_schema_version": _CP71_OUTPUT_SCHEMA_VERSION,
        "request_count": CP73_TEST28_REQUEST_COUNT,
        "total_input_bytes": cp71_summary.total_input_bytes,
        "input_stream_commitment_sha256": cp71_summary.input_stream_commitment_sha256,
        "ordered_interchange_record_sha256": cp71_summary.ordered_interchange_record_sha256,
        "ordered_projection_sha256": cp71_summary.ordered_projection_sha256,
        "ordered_seed_ordinal_plan_seed_sha256": cp71_summary.ordered_seed_ordinal_plan_seed_sha256,
        "ordered_request_instance_sha256": cp71_summary.ordered_request_instance_sha256,
        "ordered_stable_trace_sha256": cp71_summary.ordered_stable_trace_sha256,
        "runtime_lock_sha256": cp71_summary.runtime_lock_sha256,
        "runtime_lock_authenticated": False,
        "request_instance_sha256_authenticated": False,
        "stable_trace_sha256_authenticated": False,
        "feature_estimate_present_count": cp71_summary.feature_estimate_present_count,
        "feature_estimate_absent_count": cp71_summary.feature_estimate_absent_count,
        "binomial_interval_count": cp71_summary.binomial_interval_count,
        "feature_interval_count": cp71_summary.feature_interval_count,
        "computed_interval_count": cp71_summary.computed_interval_count,
        "insufficient_selection_count": cp71_summary.insufficient_selection_count,
        "distinct_binomial_success_count_count": cp72_summary.distinct_binomial_success_count_count,
        "ordered_estimand_record_sha256s_sha256": cp71_summary.ordered_estimand_record_sha256s_sha256,
        "output_body_sha256": cp71_summary.output_body_sha256,
        "output_canonical_json_bytes": cp71_summary.output_canonical_json_bytes,
        "output_canonical_json_sha256": cp71_summary.output_canonical_json_sha256,
        "cp71_reduction_summary_record_sha256": cp71_summary.record_sha256,
        "cp71_reduction_summary_public_sha256": cp71_public_sha256,
        "cp72_validation_summary_record_sha256": cp72_summary.record_sha256,
        "cp72_validation_summary_public_sha256": cp72_public_sha256,
        "cp72_ordered_cp61_inventory_crosswalk_sha256": cp72_summary.ordered_cp61_inventory_crosswalk_sha256,
        "cp72_exact_endpoint_boundary_comparison_count": cp72_summary.exact_endpoint_boundary_comparison_count,
        "summary_crosscheck_field_count": CP73_TEST28_SUMMARY_CROSSCHECK_FIELD_COUNT,
        "summary_crosscheck_sha256": crosscheck_sha256,
        "output_validated_before_stream_iteration": True,
        "stream_recomputed_once": True,
        "output_bytes_exact_match": True,
        "summary_crosscheck_verified": True,
        "input_stream_relation_verified": True,
        "external_seed_source_verified": False,
        "production_recomputation": False,
        "input_provenance_authenticated": False,
        "source_law_verified": False,
        "production_attempt_validity_evaluated": False,
        "operational_prediction": False,
        "power_review_present": False,
        "primary_thresholds_present": False,
        "decision_made": False,
        "production_evidence": False,
    }


def cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream(
    output_payload: object,
    interchange_payloads: object,
) -> CP73SuppliedStreamOutputRelationSummaryV1:
    """Verify one exact development stream-to-output byte relation."""

    try:
        (
            cp72_summary,
            cp72_public_sha256,
        ) = _complete_output_validation_before_stream_touch(output_payload)
        recomputed_output, cp71_summary, cp71_public_sha256 = _recompute_stream_once(
            interchange_payloads
        )
        exact_length = len(recomputed_output) == len(cast(bytes, output_payload))
        exact_bytes = hmac.compare_digest(
            recomputed_output, cast(bytes, output_payload)
        )
        if not exact_length or not exact_bytes:
            _fail(
                "CP73_OUTPUT_RELATION_MISMATCH",
                "supplied output differs from recomputed output",
            )
        crosscheck_sha256 = _summary_crosscheck_sha256(cp71_summary, cp72_summary)
        values = _relation_summary_values(
            cp71_summary,
            cp71_public_sha256,
            cp72_summary,
            cp72_public_sha256,
            crosscheck_sha256,
        )
        del (
            output_payload,
            interchange_payloads,
            recomputed_output,
            cp71_summary,
            cp72_summary,
            cp71_public_sha256,
            cp72_public_sha256,
            crosscheck_sha256,
        )
        candidate = _record(CP73SuppliedStreamOutputRelationSummaryV1, values)
        if type(candidate) is not CP73SuppliedStreamOutputRelationSummaryV1:
            _fail(
                "CP73_INTERNAL_INVARIANT_FAILED",
                "relation summary issuance returned an unexpected type",
            )
        return cast(CP73SuppliedStreamOutputRelationSummaryV1, candidate)
    except CP73SuppliedStreamOutputRelationQualificationError:
        raise
    except MemoryError as exc:
        raise CP73SuppliedStreamOutputRelationQualificationError(
            "CP73_RESOURCE_EXHAUSTED",
            "bounded relation qualification exhausted memory",
        ) from exc
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        raise CP73SuppliedStreamOutputRelationQualificationError(
            "CP73_INTERNAL_INVARIANT_FAILED",
            "bounded relation qualification failed closed",
        ) from exc


def _predecessor_custody() -> CP73PredecessorCustodyV1:
    return cast(
        CP73PredecessorCustodyV1,
        _record(
            CP73PredecessorCustodyV1,
            {
                "schema_version": CP73_TEST28_SCHEMA_VERSION,
                "v23_protocol_sha256": _V23_PROTOCOL_SHA256,
                "v23_protocol_bytes": _V23_PROTOCOL_BYTES,
                "v23_protocol_lf_count": _V23_PROTOCOL_LF_COUNT,
                "v23_manifest_sha256": _V23_MANIFEST_SHA256,
                "v23_manifest_bytes": _V23_MANIFEST_BYTES,
                "v23_manifest_lf_count": _V23_MANIFEST_LF_COUNT,
                "cp69_source_sha256": _CP69_SOURCE_SHA256,
                "cp69_test_sha256": _CP69_TEST_SHA256,
                "cp69_bundle_record_sha256": _CP69_BUNDLE_RECORD_SHA256,
                "cp69_interchange_contract_record_sha256": _CP69_INTERCHANGE_CONTRACT_RECORD_SHA256,
                "cp69_full_stream_expectation_record_sha256": _CP69_FULL_STREAM_EXPECTATION_RECORD_SHA256,
                "cp69_qualification_record_sha256": _CP69_QUALIFICATION_RECORD_SHA256,
                "cp71_source_sha256": _CP71_SOURCE_SHA256,
                "cp71_test_sha256": _CP71_TEST_SHA256,
                "cp71_bundle_record_sha256": _CP71_BUNDLE_RECORD_SHA256,
                "cp71_stream_contract_record_sha256": _CP71_STREAM_CONTRACT_RECORD_SHA256,
                "cp71_output_contract_record_sha256": _CP71_OUTPUT_CONTRACT_RECORD_SHA256,
                "cp71_qualification_record_sha256": _CP71_QUALIFICATION_RECORD_SHA256,
                "cp71_fixture_set_sha256": _CP71_FIXTURE_SET_SHA256,
                "cp72_source_sha256": _CP72_SOURCE_SHA256,
                "cp72_test_sha256": _CP72_TEST_SHA256,
                "cp72_bundle_record_sha256": _CP72_BUNDLE_RECORD_SHA256,
                "cp72_validation_contract_record_sha256": _CP72_VALIDATION_CONTRACT_RECORD_SHA256,
                "cp72_qualification_record_sha256": _CP72_QUALIFICATION_RECORD_SHA256,
                "cp72_fixture_set_sha256": _CP72_FIXTURE_SET_SHA256,
            },
        ),
    )


def _relation_contract() -> CP73SuppliedStreamOutputRelationContractV1:
    return cast(
        CP73SuppliedStreamOutputRelationContractV1,
        _record(
            CP73SuppliedStreamOutputRelationContractV1,
            {
                "schema_version": CP73_TEST28_SCHEMA_VERSION,
                "contract_id": "bounded-cp71-development-output-to-supplied-cp69-stream-exact-relation-v1",
                "source_interchange_schema_version": _CP69_SCHEMA_VERSION,
                "source_semantic_schema_version": _CP63_SEMANTIC_SCHEMA_VERSION,
                "source_output_schema_version": _CP71_OUTPUT_SCHEMA_VERSION,
                "cp71_reduction_summary_schema_version": CP71_TEST28_SCHEMA_VERSION,
                "cp72_validation_summary_schema_version": CP72_TEST28_SCHEMA_VERSION,
                "output_payload_exact_type": "exact-built-in-bytes",
                "interchange_payloads_consumption": "caller-object-consumed-only-by-one-cp71-public-reducer-call-after-complete-cp72-output-validation",
                "phase_order": (
                    "cp72-output-validation-completes-before-any-stream-touch",
                    "cp71-stream-recomputation-exactly-once",
                    "exact-canonical-output-byte-comparison",
                    "sealed-summary-32-field-crosscheck",
                    "cp73-scalar-summary-issuance",
                ),
                "predecessor_error_normalization": _PREDECESSOR_ERROR_NORMALIZATION,
                "failure_precedence": _FAILURE_PRECEDENCE,
                "project_module_names": CP73_TEST28_PREDECESSOR_PROJECT_MODULES,
                "predecessor_public_api_names": CP73_TEST28_PREDECESSOR_PUBLIC_APIS,
                "project_modules_imported": True,
                "source_independent": False,
                "stdlib_only": False,
                "stdlib_only_beyond_exact_predecessor_modules": True,
                "third_party_modules_imported": False,
                "public_api_uses_predecessor_public_apis_only": True,
                "output_validation_completes_before_stream_iteration": True,
                "invalid_output_iter_calls": 0,
                "invalid_output_next_calls": 0,
                "invalid_output_close_calls": 0,
                "cp72_validator_exact_call_count": 1,
                "cp71_reducer_maximum_call_count": 1,
                "cp71_reducer_exact_call_count_after_output_validation": 1,
                "exact_output_byte_relation_required": True,
                "exact_output_byte_comparison": "exact-length-and-hmac.compare_digest-on-built-in-bytes",
                "summary_crosscheck_fields": CP73_TEST28_SUMMARY_CROSSCHECK_FIELDS,
                "summary_crosscheck_field_count": CP73_TEST28_SUMMARY_CROSSCHECK_FIELD_COUNT,
                "summary_crosscheck_required": True,
                "cp71_fixed_nonclaims_checked": True,
                "cp71_stream_coherence_claims_checked": True,
                "cp72_validation_claims_checked": True,
                "relation_verified_meaning": "this-call-supplied-cp69-semantic-cp71-bounded-development-stream-exactly-regenerated-this-supplied-canonical-cp71-development-output",
                "caller_iterable_side_effects_qualified": False,
                "caller_iterable_retention_qualified": False,
                "caller_next_liveness_qualified": False,
                "iterator_close_called": False,
                "maximum_next_calls": CP73_TEST28_MAXIMUM_NEXT_CALLS,
                "maximum_interchange_bytes": CP73_TEST28_MAXIMUM_INTERCHANGE_BYTES,
                "maximum_stream_bytes": CP73_TEST28_MAXIMUM_STREAM_BYTES,
                "maximum_output_bytes": CP73_TEST28_MAXIMUM_OUTPUT_BYTES,
                "minimum_declared_total_input_bytes": CP73_TEST28_MINIMUM_DECLARED_TOTAL_INPUT_BYTES,
                "maximum_declared_total_input_bytes": CP73_TEST28_MAXIMUM_DECLARED_TOTAL_INPUT_BYTES,
                "maximum_output_vector_cardinality": CP73_TEST28_MAXIMUM_OUTPUT_VECTOR_CARDINALITY,
                "maximum_sealed_record_bytes": CP73_TEST28_MAXIMUM_SEALED_RECORD_BYTES,
                "caller_output_bytes_returned": False,
                "recomputed_output_bytes_returned": False,
                "caller_summary_accepted": False,
                "predecessor_summary_returned": False,
                "scalar_summary_only": True,
                "caller_output_retained_after_successful_return": False,
                "recomputed_output_retained_after_successful_return": False,
                "module_owned_predecessor_summary_references_retained_after_successful_return": False,
                "predecessor_summary_issuance_on_late_failure_possible": True,
                "predecessor_weak_registry_entries_recoverable_after_all_strong_references_released": True,
                "exception_traceback_retention_qualified": False,
                "no_cp73_record_issued_before_relation_complete": True,
                "cp73_partial_return_on_failure": False,
                "dynamic_input_payload_or_output_body_cached": False,
                "sealed_summary_snapshot_retained_while_summary_live": True,
                "module_direct_filesystem_read": False,
                "module_direct_filesystem_write": False,
                "module_direct_clock_read": False,
                "module_direct_rng_used": False,
                "module_direct_network_used": False,
                "module_direct_subprocess_used": False,
                "input_provenance_authenticated": False,
                "runtime_lock_authenticated": False,
                "request_instance_sha256_authenticated": False,
                "stable_trace_sha256_authenticated": False,
                "external_seed_source_verified": False,
                "source_law_verified": False,
                "production_attempt_validity_evaluated": False,
                "production_recomputation_qualified": False,
                "operational_prediction": False,
                "power_review_present": False,
                "primary_thresholds_present": False,
                "decision_made": False,
                "production_evidence": False,
                "confirmatory_custody_present": False,
                "production_gate_13_state": "MISSING",
                "production_gate_14_state": "MISSING",
                "formal_test_28_status": CP73_TEST28_FORMAL_TEST_28_STATUS,
                "summary_crosscheck_digest_domain": _SUMMARY_CROSSCHECK_DOMAIN.decode(
                    "ascii"
                ),
                "summary_crosscheck_digest_preimage": _SUMMARY_CROSSCHECK_PREIMAGE,
            },
        ),
    )


_BUNDLE_LOCK = threading.RLock()
_BUNDLE_CACHE: Optional[CP73SuppliedStreamOutputRelationQualificationBundleV1] = None


def cp73_supplied_stream_output_relation_qualification_bundle() -> CP73SuppliedStreamOutputRelationQualificationBundleV1:
    """Return the zero-execution declarative CP73 contract bundle."""

    global _BUNDLE_CACHE
    with _BUNDLE_LOCK:
        if _BUNDLE_CACHE is None:
            try:
                candidate = cast(
                    CP73SuppliedStreamOutputRelationQualificationBundleV1,
                    _record(
                        CP73SuppliedStreamOutputRelationQualificationBundleV1,
                        {
                            "schema_version": CP73_TEST28_SCHEMA_VERSION,
                            "scope": CP73_TEST28_SCOPE,
                            "blocker_ledger_prerequisite_id": CP73_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID,
                            "blocker_ledger_prerequisite_state": _LEDGER_PREREQUISITE_STATE,
                            "blocker_ledger_total_count": 28,
                            "blocker_ledger_satisfied_count": 24,
                            "blocker_ledger_missing_count": 4,
                            "predecessor_custody": _predecessor_custody(),
                            "relation_contract": _relation_contract(),
                            "zero_argument_builder": True,
                            "builder_validates": False,
                            "qualification_runner_exposed": False,
                            "module_owned_fixture_count": 0,
                            "module_owned_stream_body_count": 0,
                            "module_owned_output_body_count": 0,
                            "external_test_qualification_required": True,
                            "public_supplied_stream_output_relation_validator_exposed": True,
                            "public_caller_data_api_count": 1,
                            "public_parser_exposed": False,
                            "public_stream_reducer_exposed": False,
                            "public_output_validator_exposed": False,
                            "public_summary_input_api_exposed": False,
                            "public_output_bytes_returned": False,
                            "public_path_api_exposed": False,
                            "public_writer_api_exposed": False,
                            "public_runner_api_exposed": False,
                            "public_primary_decision_threshold_api_exposed": False,
                            "public_decision_api_exposed": False,
                            "public_receipt_or_evidence_api_exposed": False,
                            "project_modules_imported": True,
                            "project_module_count": 2,
                            "source_independent": False,
                            "stdlib_only": False,
                            "stdlib_only_beyond_exact_predecessor_modules": True,
                            "third_party_modules_imported": False,
                            "predecessor_public_apis_only": True,
                            "module_direct_filesystem_read": False,
                            "module_direct_filesystem_write": False,
                            "module_direct_clock_read": False,
                            "module_direct_rng_used": False,
                            "module_direct_network_used": False,
                            "module_direct_subprocess_used": False,
                            "production_execution_authorized": False,
                            "production_recomputation_qualified": False,
                            "unconditional_operational_predictions_produced": False,
                            "power_review_present": False,
                            "primary_thresholds_present": False,
                            "confirmatory_custody_present": False,
                            "runtime_lock_authenticated": False,
                            "request_instance_sha256_authenticated": False,
                            "stable_trace_sha256_authenticated": False,
                            "production_gate_13_state": "MISSING",
                            "production_gate_14_state": "MISSING",
                            "runner_and_recomputation_blocker_closed": False,
                            "unconditional_operational_predictions_blocker_closed": False,
                            "power_and_thresholds_blocker_closed": False,
                            "confirmatory_custody_blocker_closed": False,
                            "formal_test_28_status": CP73_TEST28_FORMAL_TEST_28_STATUS,
                            "formal_test_28_closed": False,
                        },
                    ),
                )
            except CP73SuppliedStreamOutputRelationQualificationError:
                raise
            except MemoryError as exc:
                raise CP73SuppliedStreamOutputRelationQualificationError(
                    "CP73_RESOURCE_EXHAUSTED",
                    "declarative bundle construction exhausted memory",
                ) from exc
            except (KeyboardInterrupt, SystemExit, GeneratorExit):
                raise
            except Exception as exc:
                raise CP73SuppliedStreamOutputRelationQualificationError(
                    "CP73_INTERNAL_INVARIANT_FAILED",
                    "declarative bundle construction failed closed",
                ) from exc
            _BUNDLE_CACHE = candidate
        return _BUNDLE_CACHE


__all__ = (
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
    "cp73_validate_supplied_cp71_development_output_relation_to_cp69_interchange_stream",
    "cp73_supplied_stream_output_relation_qualification_bundle",
)
