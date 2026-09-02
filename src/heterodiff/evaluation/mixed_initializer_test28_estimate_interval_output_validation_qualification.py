"""Closed CP70 qualification of the CP69-byte to CP68-output boundary.

This source-independent, standard-library module owns one closed synthetic
32,768-record CP69-equivalent byte stream.  Its private reducer parses one
record at a time directly into fixed sufficient statistics, constructs the
exact 554-record CP68 development estimate/interval body, and passes those
bytes through the sole caller-data surface: a bounded exact-fixture validator.

Nothing here accepts a raw record, stable trace, path, command, production
campaign, receipt, threshold, or decision.  The closed fixture is development
data.  Its four custody strings are opaque sentinels, not authenticated
provenance or admissible evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
from functools import lru_cache
from math import comb
import base64
import hashlib
import hmac
import json
import threading
from typing import Iterator, Mapping, Optional, Tuple, cast
import weakref


CP70_TEST28_SCHEMA_VERSION = (
    "cp70-test28-estimate-interval-output-validation-qualification-v1"
)
CP70_TEST28_SCOPE = (
    "development-only-source-independent-closed-cp69-canonical-compact-"
    "interchange-to-exact-cp68-554-estimate-interval-output-reducer-and-"
    "bounded-output-byte-validation;private-stream-injection-only;sole-"
    "caller-data-api-validates-the-exact-closed-output;no-project-imports;"
    "no-raw-record;no-stable-trace;no-provenance-authentication;no-production;"
    "no-decision;no-test28-closure;no-path-command-writer-shard-campaign-"
    "receipt-evidence-acceptance-threshold-execution-power-confirmatory-or-"
    "manuscript-claim;transient-plain-projection-digest-preimage-mappings-"
    "created-and-discarded"
)
CP70_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP70_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID = (
    "whole_seed_cp69_compact_interchange_to_cp68_estimate_interval_output_"
    "source_independent_reducer_qualification"
)
CP70_TEST28_SEED_COUNT = 2_048
CP70_TEST28_ROW_COUNT = 16
CP70_TEST28_REQUEST_COUNT = 32_768
CP70_TEST28_ESTIMAND_COUNT = 554
CP70_TEST28_OBSERVABLE_ESTIMAND_COUNT = 72
CP70_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT = 170
CP70_TEST28_FEATURE_ESTIMAND_COUNT = 312
CP70_TEST28_BINOMIAL_ESTIMAND_COUNT = 242
CP70_TEST28_COMPUTED_INTERVAL_COUNT = 398
CP70_TEST28_INSUFFICIENT_SELECTION_COUNT = 156
CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES = 65_536
CP70_TEST28_MAXIMUM_STREAM_BYTES = 67_108_864
CP70_TEST28_MAXIMUM_OUTPUT_BYTES = 1_048_576
CP70_TEST28_MAXIMUM_CANONICAL_DEPTH = 8
CP70_TEST28_MAXIMUM_CANONICAL_NODES = 32_768
CP70_TEST28_MAXIMUM_KEY_CHARACTERS = 64
CP70_TEST28_MAXIMUM_TEXT_CHARACTERS = 256
CP70_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS = 155
CP70_TEST28_MAXIMUM_INTEGER_BITS = 512
CP70_TEST28_SELECTED_COUNTS_BY_ROW = (
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

_LEDGER_PREREQUISITE_STATE = (
    "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_" "ARTIFACTS"
)
_CP69_SCHEMA_VERSION = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_COMPACT_SCHEMA_VERSION = "cp63-test28-independent-compact-recomputation-v1"
_CP68_SCHEMA_VERSION = "cp68-test28-compact-projection-aggregation-qualification-v1"
_ZERO_SHA256 = "0" * 64
_MAXIMUM_RECORD_KEY_CHARACTERS = 256
_MAXIMUM_RECORD_TEXT_CHARACTERS = 4_096

_V20_PROTOCOL_SHA256 = (
    "9db40f14eade99cbfedb6d5ad8b28f04cf803f400cf8198629751f2dda46d2b0"
)
_V20_PROTOCOL_BYTES = 189_122
_V20_PROTOCOL_LF_COUNT = 3_228
_V20_MANIFEST_SHA256 = (
    "29b718873e5ea5b3b829b267c1d917f0c6e0cc3ee9b0b1455b2b3142c4bfb909"
)
_V20_MANIFEST_BYTES = 6_084_812
_V20_MANIFEST_LF_COUNT = 119_427
_CP61_SOURCE_SHA256 = "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
_CP61_BUNDLE_RECORD_SHA256 = (
    "8c5e23661cc0ef459e700c2af5239d21ee8aafd4d9dca2ed3db6e3ce2e4a0ca0"
)
_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP61_PROJECTION_CONTRACT_RECORD_SHA256 = (
    "5b7f733e8cd2a8f3ed16915dc77fdf4c059af77ae31a1c5008a2dba9352e7a6d"
)
_CP63_INDEPENDENT_SOURCE_SHA256 = (
    "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc"
)
_CP63_INDEPENDENT_TEST_SHA256 = (
    "9c0144994d690d326b51c27e57f5832489b640a049b64bffd474026a18e64a13"
)
_CP63_INDEPENDENT_BUNDLE_RECORD_SHA256 = (
    "b219de24a17af7c06b503af07110ed863c339bca19c7457c163412ae0e76ddb9"
)
_CP63_SCHEDULE_CONTRACT_RECORD_SHA256 = (
    "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
)
_CP68_SOURCE_SHA256 = "15afd7e4a8fb99c137faea8d57ef2bd2dc3ab3c193481883da4e205b75c16555"
_CP68_TEST_SHA256 = "5587785ad8c5fc3ac526758ce87ad91acbb5b4e1532563ceacc2e1c8d64f32e4"
_CP68_BUNDLE_RECORD_SHA256 = (
    "b301ea4cadb8a67fa238dfa5872c874b4689a08b7baec04f1133bef7191a2a83"
)
_CP68_OUTPUT_SCHEMA_RECORD_SHA256 = (
    "4315375d2dbd5363e2fe57147468cef51b15d074b99fcd03beed5ed004ca4c1e"
)
_CP68_AGGREGATION_EXPECTATION_RECORD_SHA256 = (
    "00e5d9263386bda729b929da898d5c97174fb2606db52dfad1920089e3d3882a"
)
_CP68_QUALIFICATION_RECORD_SHA256 = (
    "881dc5b6539504a3bf42957d7e0b4298484db0cfd637e3fe861ce9847cf81400"
)
_CP68_FIXTURE_SET_SHA256 = (
    "6b8d7db706b94c32ee53efe9969e16560997e0f7b2345960e44ad4f18feb49ce"
)
_CP68_ORDERED_PROJECTION_SHA256 = (
    "f898741b035d59116f6e096a1deab6c642f83dd3ad0417b7995e182584731f42"
)
_CP68_ORDERED_ESTIMAND_RECORD_SHA256S_SHA256 = (
    "c0dbf7e789551510c2cbf0abca77e755959609b11510c6e835d12b999abb6f06"
)
_CP68_OUTPUT_BODY_SHA256 = (
    "03915b689c41c673805b1b46c76ef1dc296e3434522fbb28a153715cdd052fc5"
)
_CP68_OUTPUT_CANONICAL_JSON_BYTES = 660_947
_CP68_OUTPUT_CANONICAL_JSON_SHA256 = (
    "f9e1bf93354af057d08ca722d2cffe1a8188d2f1e823a0173f9b6a937ddc42c3"
)
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
_CP69_FIXTURE_SET_SHA256 = (
    "95a388b634e208b8d7b578a18657289390fe9306e23a4e5ecb3ed084771a8303"
)
_CP69_FIRST_INTERCHANGE_RECORD_SHA256 = (
    "de2237dfb851b4370d25cfa9b72698a73d6ea4c1c4f70b654f509999ecec34b8"
)
_CP69_ORDERED_INTERCHANGE_RECORD_SHA256 = (
    "754b058697dc9324611152b4987925a414520fc98dd764571321c3135d0ecc8d"
)
_CP69_TOTAL_INPUT_BYTES = 51_506_557


class CP70EstimateIntervalOutputValidationQualificationError(RuntimeError):
    """Fail-closed CP70 error carrying a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP70 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP70 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP70 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP70PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    v20_protocol_sha256: str
    v20_protocol_bytes: int
    v20_protocol_lf_count: int
    v20_manifest_sha256: str
    v20_manifest_bytes: int
    v20_manifest_lf_count: int
    cp61_source_sha256: str
    cp61_bundle_record_sha256: str
    cp61_stable_design_sha256: str
    cp61_projection_contract_record_sha256: str
    cp63_independent_source_sha256: str
    cp63_independent_test_sha256: str
    cp63_independent_bundle_record_sha256: str
    cp63_schedule_contract_record_sha256: str
    cp68_source_sha256: str
    cp68_test_sha256: str
    cp68_bundle_record_sha256: str
    cp68_output_schema_record_sha256: str
    cp68_aggregation_expectation_record_sha256: str
    cp68_qualification_record_sha256: str
    cp68_fixture_set_sha256: str
    cp68_ordered_projection_sha256: str
    cp68_ordered_estimand_record_sha256s_sha256: str
    cp68_output_body_sha256: str
    cp68_output_canonical_json_bytes: int
    cp68_output_canonical_json_sha256: str
    cp69_source_sha256: str
    cp69_test_sha256: str
    cp69_bundle_record_sha256: str
    cp69_interchange_contract_record_sha256: str
    cp69_full_stream_expectation_record_sha256: str
    cp69_qualification_record_sha256: str
    cp69_fixture_set_sha256: str
    cp69_first_interchange_record_sha256: str
    cp69_ordered_interchange_record_sha256: str
    cp69_total_input_bytes: int
    cp69_ordered_target_projection_sha256: str
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP70SourceIndependentReducerContractV1(_SealedRecord):
    schema_version: str
    contract_id: str
    source_interchange_schema_version: str
    target_output_schema_version: str
    seed_count: int
    row_count: int
    request_count: int
    estimand_count: int
    logical_request_order: str
    private_stream_injection_only: bool
    public_stream_api_exposed: bool
    source_independent: bool
    stdlib_only: bool
    project_modules_imported: bool
    direct_to_fixed_sufficient_statistics: bool
    cp68_projection_records_created: bool
    interchange_corpus_retained: bool
    output_sufficient_statistic_map_sizes: Tuple[int, ...]
    diagnostic_status_count_map_size: int
    aggregation_update_count: int
    cp_endpoint_table_count: int
    cp_adjacent_boundary_comparison_count: int
    maximum_interchange_bytes: int
    maximum_stream_bytes: int
    maximum_output_bytes: int
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP70OutputValidationContractV1(_SealedRecord):
    schema_version: str
    contract_id: str
    source_output_schema_version: str
    exact_root_keys: Tuple[str, ...]
    exact_estimand_keys: Tuple[str, ...]
    canonical_json_profile: str
    exact_fraction_encoding: str
    estimand_record_digest_domain: str
    output_body_digest_domain: str
    payload_digest_profile: str
    closed_fixture_only: bool
    exact_input_bytes: bool
    raise_or_sealed_return: bool
    partial_result_permitted: bool
    estimand_count: int
    observable_estimand_count: int
    rejection_first_attempt_estimand_count: int
    feature_estimand_count: int
    binomial_estimand_count: int
    computed_interval_count: int
    insufficient_selection_count: int
    maximum_output_bytes: int
    maximum_canonical_depth: int
    maximum_canonical_nodes: int
    maximum_key_characters: int
    maximum_text_characters: int
    maximum_integer_decimal_digits: int
    maximum_integer_bits: int
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP70FullReductionExpectationV1(_SealedRecord):
    schema_version: str
    source_fixture_set_sha256: str
    request_count: int
    total_input_bytes: int
    first_interchange_record_sha256: str
    ordered_interchange_record_sha256: str
    selected_counts_by_row: Tuple[int, ...]
    rejection_selected_count: int
    rejection_exhausted_count: int
    sir_selected_count: int
    refusal_count: int
    failure_count: int
    timeout_count: int
    first_attempt_contribution_count: int
    feature_contribution_count: int
    aggregation_update_count: int
    estimand_count: int
    observable_estimand_count: int
    rejection_first_attempt_estimand_count: int
    feature_estimand_count: int
    binomial_interval_count: int
    feature_interval_count: int
    insufficient_selection_count: int
    computed_interval_count: int
    distinct_binomial_success_count_count: int
    cp_adjacent_boundary_comparison_count: int
    ordered_target_projection_sha256: str
    ordered_estimand_record_sha256s_sha256: str
    output_body_sha256: str
    output_canonical_json_bytes: int
    output_canonical_json_sha256: str
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP70EstimateIntervalOutputValidationV1(_SealedRecord):
    schema_version: str
    source_output_schema_version: str
    fixture_set_sha256: str
    request_count: int
    estimand_count: int
    observable_estimand_count: int
    rejection_first_attempt_estimand_count: int
    feature_estimand_count: int
    binomial_interval_count: int
    feature_interval_count: int
    insufficient_selection_count: int
    computed_interval_count: int
    selected_counts_by_row: Tuple[int, ...]
    ordered_estimand_record_sha256s_sha256: str
    output_body_sha256: str
    output_canonical_json_bytes: int
    output_canonical_json_sha256: str
    canonical_bytes_verified: bool
    record_digests_verified: bool
    estimand_inventory_verified: bool
    family_union_verified: bool
    cross_record_invariants_verified: bool
    exact_arithmetic_verified: bool
    cp_endpoint_table_match_verified: bool
    feature_threshold_and_clipping_verified: bool
    closed_fixture_match: bool
    development_fixture_only: bool
    production_evidence: bool
    decision_path_qualified: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP70EstimateIntervalOutputValidationQualificationV1(_SealedRecord):
    schema_version: str
    source_fixture_set_sha256: str
    request_count: int
    total_input_bytes: int
    logical_ordinals_complete: bool
    streaming_peak_input_payload_count: int
    streaming_peak_parsed_observation_count: int
    interchange_corpus_retained: bool
    cp68_projection_records_created: bool
    aggregation_update_count: int
    estimand_count: int
    output_record_vector_cardinality: int
    output_records_retained_after_runner: bool
    ordered_interchange_record_sha256: str
    ordered_target_projection_sha256: str
    ordered_estimand_record_sha256s_sha256: str
    output_body_sha256: str
    output_canonical_json_bytes: int
    output_canonical_json_sha256: str
    canonical_output_validated: bool
    record_digests_verified: bool
    cp_endpoint_table_independently_certified: bool
    feature_threshold_and_clipping_verified: bool
    target_output_matches_cp68_expectation: bool
    raw_record_parsed: bool
    stable_trace_parsed: bool
    provenance_authenticated: bool
    production_recomputation_performed: bool
    production_estimate_or_interval: bool
    decision_path_qualified: bool
    production_evidence: bool
    production_execution_authorized: bool
    runner_and_recomputation_blocker_closed: bool
    formal_test_28_closed: bool
    all_development_qualification_checks_passed: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP70EstimateIntervalOutputValidationQualificationBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    predecessor_custody: CP70PredecessorCustodyV1
    reducer_contract: CP70SourceIndependentReducerContractV1
    output_validation_contract: CP70OutputValidationContractV1
    full_reduction_expectation: CP70FullReductionExpectationV1
    zero_argument_builder: bool
    builder_parses_reduces_or_validates: bool
    qualification_runner_zero_argument: bool
    bounded_public_closed_output_byte_validator_exposed: bool
    generic_public_stream_reducer_exposed: bool
    closed_module_owned_fixture_only: bool
    source_independent: bool
    stdlib_only_import: bool
    project_modules_imported: bool
    streaming_interchange: bool
    full_interchange_corpus_materialized: bool
    cp68_projection_records_created: bool
    output_record_vector_cardinality: int
    maximum_interchange_bytes: int
    maximum_stream_bytes: int
    maximum_output_bytes: int
    host_filesystem_probed: bool
    clock_read: bool
    rng_used: bool
    network_used: bool
    subprocess_api_exposed: bool
    filesystem_path_api_exposed: bool
    raw_record_api_exposed: bool
    stable_trace_api_exposed: bool
    production_campaign_api_exposed: bool
    production_estimate_or_interval: bool
    decision_path_qualified: bool
    production_qualification_receipt_present: bool
    production_evidence_present_count: int
    production_gate_13_evidence_present: bool
    production_gate_13_state: str
    production_gate_14_evidence_present: bool
    production_gate_14_state: str
    production_execution_authorized: bool
    production_execution_observed: bool
    runner_and_recomputation_blocker_closed: bool
    unconditional_operational_predictions_blocker_closed: bool
    power_and_thresholds_blocker_closed: bool
    confirmatory_custody_blocker_closed: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    ledger_prerequisite_id: str
    ledger_prerequisite_state: str
    ledger_total_count: int
    ledger_satisfied_count: int
    ledger_missing_count: int
    development_qualification_only: bool
    record_sha256: str
    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_RECORD_DOMAINS = {
    CP70PredecessorCustodyV1: b"cp70-test28-predecessor-custody-v1",
    CP70SourceIndependentReducerContractV1: b"cp70-test28-source-independent-reducer-contract-v1",
    CP70OutputValidationContractV1: b"cp70-test28-output-validation-contract-v1",
    CP70FullReductionExpectationV1: b"cp70-test28-full-reduction-expectation-v1",
    CP70EstimateIntervalOutputValidationV1: b"cp70-test28-estimate-interval-output-validation-v1",
    CP70EstimateIntervalOutputValidationQualificationV1: b"cp70-test28-estimate-interval-output-validation-qualification-v1",
    CP70EstimateIntervalOutputValidationQualificationBundleV1: b"cp70-test28-estimate-interval-output-validation-qualification-bundle-v1",
}

_NESTED_RECORD_FIELD_TYPES = {
    CP70EstimateIntervalOutputValidationQualificationBundleV1: (
        ("predecessor_custody", CP70PredecessorCustodyV1),
        ("reducer_contract", CP70SourceIndependentReducerContractV1),
        ("output_validation_contract", CP70OutputValidationContractV1),
        ("full_reduction_expectation", CP70FullReductionExpectationV1),
    ),
}

_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS = cast(
    "weakref.WeakKeyDictionary[_SealedRecord, Tuple[bytes, object, Tuple[_SealedRecord, ...]]]",
    weakref.WeakKeyDictionary(),
)


def _fail(code: str, message: str) -> None:
    raise CP70EstimateIntervalOutputValidationQualificationError(code, message)


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
    if nodes[0] > CP70_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "canonical graph exceeds its node limit")
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        if cast(int, value).bit_length() > CP70_TEST28_MAXIMUM_INTEGER_BITS:
            _fail("CP70_INPUT_RESOURCE_LIMIT", "canonical integer is too large")
        return value
    if type(value) is Fraction:
        fraction = cast(Fraction, value)
        if (
            max(fraction.numerator.bit_length(), fraction.denominator.bit_length())
            > CP70_TEST28_MAXIMUM_INTEGER_BITS
        ):
            _fail("CP70_INPUT_RESOURCE_LIMIT", "canonical fraction is too large")
        return {"$fraction": [str(fraction.numerator), str(fraction.denominator)]}
    if type(value) is str:
        if len(cast(str, value)) > _MAXIMUM_RECORD_TEXT_CHARACTERS:
            _fail("CP70_INPUT_RESOURCE_LIMIT", "canonical text is too large")
        return value
    if depth > CP70_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "canonical graph exceeds its depth limit")
    if type(value) not in (tuple, list, dict) and type(value) not in _RECORD_DOMAINS:
        raise TypeError("value has no CP70 canonical representation")
    identity = id(value)
    if identity in active:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "canonical graph is cyclic")
    active.add(identity)
    try:
        if type(value) in (tuple, list):
            return [
                _plain_json_value(item, depth=depth + 1, nodes=nodes, active=active)
                for item in cast(tuple, value)
            ]
        if type(value) is dict:
            result = {}
            for key, item in cast(dict, value).items():
                if type(key) is not str:
                    raise TypeError("CP70 JSON keys must be exact strings")
                if len(key) > _MAXIMUM_RECORD_KEY_CHARACTERS:
                    _fail("CP70_INPUT_RESOURCE_LIMIT", "canonical key is too large")
                result[key] = _plain_json_value(
                    item, depth=depth + 1, nodes=nodes, active=active
                )
            return result
        return {
            item.name: _plain_json_value(
                getattr(value, item.name), depth=depth + 1, nodes=nodes, active=active
            )
            for item in fields(type(value))
        }
    finally:
        active.remove(identity)


def _plain_json_bytes(
    value: object, maximum: int = CP70_TEST28_MAXIMUM_OUTPUT_BYTES
) -> bytes:
    try:
        encoded = json.dumps(
            _plain_json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except CP70EstimateIntervalOutputValidationQualificationError:
        raise
    except (OverflowError, RecursionError, TypeError, ValueError) as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_INPUT_RESOURCE_LIMIT", "canonical encoding failed closed"
        ) from exc
    if len(encoded) > maximum:
        _fail("CP70_INPUT_BYTE_LIMIT", "canonical bytes exceed their bound")
    return encoded


def _typed_shape(
    value: object,
    *,
    depth: int,
    nodes: list[int],
    active: set[int],
    nested_records: list[_SealedRecord],
) -> object:
    nodes[0] += 1
    if nodes[0] > CP70_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "typed record graph exceeds its node limit")
    if value is None:
        return ("none",)
    if type(value) is bool:
        return ("bool", cast(bool, value))
    if type(value) is int:
        return ("int", cast(int, value))
    if type(value) is str:
        return ("str", cast(str, value))
    if type(value) is Fraction:
        fraction = cast(Fraction, value)
        return ("fraction", fraction.numerator, fraction.denominator)
    if depth > CP70_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "typed record graph exceeds its depth limit")
    exact_type = type(value)
    if exact_type in _RECORD_DOMAINS:
        nested = cast(_SealedRecord, value)
        nested_records.append(nested)
        return ("sealed-record", exact_type.__name__)
    if exact_type not in (tuple, list, dict):
        raise TypeError("typed record graph contains an unsupported exact type")
    identity = id(value)
    if identity in active:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "typed record graph is cyclic")
    active.add(identity)
    try:
        if exact_type in (tuple, list):
            return (
                "tuple" if exact_type is tuple else "list",
                tuple(
                    _typed_shape(
                        item,
                        depth=depth + 1,
                        nodes=nodes,
                        active=active,
                        nested_records=nested_records,
                    )
                    for item in cast(tuple, value)
                ),
            )
        entries = []
        for key, item in cast(dict, value).items():
            if type(key) is not str:
                raise TypeError("typed record mapping key is not an exact string")
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


def _typed_record_state(
    record: _SealedRecord,
) -> Tuple[object, Tuple[_SealedRecord, ...]]:
    nodes = [1]
    active = {id(record)}
    nested_records = []
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
                    active=active,
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
            raise TypeError("nested sealed-record field has the wrong exact type")


def _record(cls: type, values: Mapping[str, object]) -> object:
    if cls not in _RECORD_DOMAINS:
        raise TypeError("unsupported CP70 record class")
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP70 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(complete)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _plain_json_bytes(result)
    typed_snapshot, nested_records = _typed_record_state(cast(_SealedRecord, result))
    _validate_nested_record_field_types(cast(_SealedRecord, result))
    for nested_record in nested_records:
        _require_issued_record(nested_record)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = (
            snapshot,
            typed_snapshot,
            nested_records,
        )
    return result


def _require_issued_record_inner(
    value: object,
    *,
    record_active: set[int],
    record_nodes: list[int],
) -> Tuple[_SealedRecord, bytes]:
    if type(value) not in _RECORD_DOMAINS:
        _fail("CP70_RECORD_TYPE_MISMATCH", "record has an unsupported exact type")
    record = cast(_SealedRecord, value)
    with _ISSUED_RECORD_LOCK:
        issued_snapshot = _ISSUED_RECORD_SNAPSHOTS.get(record)
    if issued_snapshot is None:
        _fail("CP70_RECORD_NOT_ISSUED", "record was not issued by CP70")
    identity = id(record)
    record_nodes[0] += 1
    if (
        record_nodes[0] > CP70_TEST28_MAXIMUM_CANONICAL_NODES
        or len(record_active) >= CP70_TEST28_MAXIMUM_CANONICAL_DEPTH
        or identity in record_active
    ):
        _fail("CP70_RECORD_TAMPERED", "nested issued-record graph is not bounded")
    record_active.add(identity)
    try:
        snapshot, typed_snapshot, issued_nested_records = issued_snapshot
        try:
            current_typed_snapshot, nested_records = _typed_record_state(record)
            _validate_nested_record_field_types(record)
        except MemoryError:
            raise
        except Exception as exc:
            raise CP70EstimateIntervalOutputValidationQualificationError(
                "CP70_RECORD_TAMPERED", "issued record has an invalid typed shape"
            ) from exc
        if current_typed_snapshot != typed_snapshot:
            _fail("CP70_RECORD_TAMPERED", "issued record typed shape was mutated")
        if len(nested_records) != len(issued_nested_records) or any(
            current is not issued
            for current, issued in zip(nested_records, issued_nested_records)
        ):
            _fail("CP70_RECORD_TAMPERED", "nested issued-record identity was mutated")
        for nested_record in nested_records:
            try:
                _require_issued_record_inner(
                    nested_record,
                    record_active=record_active,
                    record_nodes=record_nodes,
                )
            except MemoryError:
                raise
            except CP70EstimateIntervalOutputValidationQualificationError as exc:
                if exc.code == "CP70_RESOURCE_EXHAUSTED":
                    raise
                raise CP70EstimateIntervalOutputValidationQualificationError(
                    "CP70_RECORD_TAMPERED",
                    "nested issued record failed its issuance check",
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
            raise CP70EstimateIntervalOutputValidationQualificationError(
                "CP70_RECORD_TAMPERED", "issued record cannot be reserialized"
            ) from exc
        if not hmac.compare_digest(snapshot, current):
            _fail("CP70_RECORD_TAMPERED", "issued record canonical bytes were mutated")
        if type(supplied) is not str or not hmac.compare_digest(
            cast(str, supplied), expected
        ):
            _fail("CP70_RECORD_TAMPERED", "issued record digest differs")
        return record, snapshot
    finally:
        record_active.remove(identity)


def _require_issued_record(value: object) -> Tuple[_SealedRecord, bytes]:
    try:
        return _require_issued_record_inner(
            value,
            record_active=set(),
            record_nodes=[0],
        )
    except CP70EstimateIntervalOutputValidationQualificationError:
        raise
    except MemoryError as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_RESOURCE_EXHAUSTED", "issued-record validation exhausted memory"
        ) from exc


def cp70_canonical_json_bytes(value: object) -> bytes:
    """Return canonical bytes for one unchanged module-issued record."""

    return _require_issued_record(value)[1]


def cp70_sha256(value: object) -> str:
    """Return the tagged public digest of one unchanged CP70 record."""

    record, snapshot = _require_issued_record(value)
    return hashlib.sha256(
        b"cp70-public-record-v1\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + snapshot
    ).hexdigest()


# The 554 CP61 record digests are frozen data, encoded compactly to keep the
# source reviewable without importing any predecessor module.
_CP61_ESTIMAND_RECORD_SHA256_B85 = (
    "`0iJ1iDj%;4JV;rIW`(_$A8r3&EVSy`(77m>#M9ChQKN7U-I0P?h)+N58DUYHd}$9t1~kj>1Qe2uKzT~6@iOV%6jSnqndz}t"
    "rvoRQ1(ExKCXj-II}5VnMX$ISS!EN*&d0I*S(up>WZVe|4FK_1ikNPF)?BNXUy<}1?g-P(~Z~8tTty5aaE8CmRb`<<@#_Kuk"
    "qg?V9WiX1MK>bg|rSIp0*je_=qGmcT2=PJF_H$xff3Iy$2_}@zLozEx6Mu?A;!H-51jGF5I2fq3^$+_}4|4f)G-Z664hTax*"
    "*&M*yrv{5d~0PGD<Mz8~YAkC8E|21cx17|m;n{1>*_5PM5SgrGJtO!>b$16V|a)xhpbogpN`%_Lovj_!M4{%L4a+;vw^;Rg&"
    "s@Q#2!HT{MDp<45pj76DS2Rn)`^Dc`|VI~MEl6L_>K#2m&WL}{h7*q&MX{8nO9Vaf6xRNY$89Iq)U_+)NDLN!C<mi{l5je_l"
    "cZmg-oIK)rWf<F84sogoEd-=5wpsCaFRTWcC9p}K#(!AP1v|n5np*>Bl^+(C*aRA8e=`~&`5+gi6W`o*NrLaEZC076?JPY!x"
    "V@Vq8Vshd4UPGVGr8kSsrd3K4M%+GuDJj^=%EMz^k(zLJv_bSo|1V5P1P~z7PCpkjwPbj8YN7Hv;Q69r#b#mlCn6OG%rvav-"
    "^OVqgqRjoPbhH=7+h%)%yN%ATG*hbwtH_wT|_!Mv8B{FayGPtA>P?_DFNgLw%a|r_((9=ef-8jsPcs(has0{yfkKw9j@uD@U"
    "2l3h5bicWPE0CXl(AE>!ljI~cWR{Ml;ShYqqXH19HC$5hXT<!i|Z=+Dm8qi1s4EQ3}!dxGhT)U@e8rP3mMO67X`e}gm%YY_H"
    "rf?KSls02Ub?sf1TPnst1UZC!P(}ltihaIFgA44z=SA;Y4J^F@s($}JU=<E;aU*Lr;GpnDVE&3`6gWkH<DIiC<&sKX>Nn3N>"
    "ggUHdTia66;8$<-!I3dtnRaVl+u)$@0J7*)bq!&7oQiMNah|e<o?azaKA8Ljgn(CYC&ZMkq|}y?1}|96#cIs1B-MKkhW+PC5"
    "h*$?m|TE$#qi(IVeYNn3A(BwI(0(Vuet(=NmH(y=Zrc-cohBFMhr4j#Oq>=(iXeHBs(^|_W&nZqafo^1wA*0cqnU@$a^m|>n"
    "P)P&}_hv1{?nIRRG7AAo1$6H~-Z5KaHz)aZE)_%TbHs2S?sB%}%9?PqjD58Zh~ueGJol9*pc`e6w;jANs0-QiDS=D$hY?%n^"
    "H=oC<*Z(Lk`<5xo$vW+$Qsrsnc;fra@#kE}}db)4sFzVIShuJMc-7b_;v)1NWEGGrAqKS6(+%TY;W(EMpt2`geAP7}a>e8Pi"
    "$j#S!vGWiXY)@3#6;qX8cyov$ID;E!k7$=7zQrm$>F~Z)c_qaJqPI~VbY9+AxM-`ldV^2=Hr05ZdI?Aeh7g3I@g_dTm4v^si"
    "I@>!KNGec#q$ZAw7A~-*j2lip{&N1er6UqqfSD4!y(!EHP*<!YXI-&|3cgY3y1NR{@*YbE>Che2M_QzebD-HRgS-oZ0kXI({"
    "P;j#^K#|oozfv1m7*X^e5Vw+A^k7Qr6z;^O*pylUDl<?r8-xPHG2X=A(5$`=}=a4px#caAW*&})DMyTMh+NEjU$fj--PQjg$"
    "d?u!8UW3=4RjA(1Qe%)Gu{5qb~QVG`l+EG25nvVt+T~_{<;jTdU}{?RSp$Ps}i20j>2dd=v#lAeRpL5=`J)eae{dbF=yeF#j"
    "^HgE2tJ{%!c%MxzY>KV6(-%ukd*i`%Xkvh1lCP{EzrHZj_ZK2LP!Vj!H3=Ppw+L<uNIKix!1j3jZVp5Re4=7Kj}c8c*W!4;f"
    ";S@RVCUst-OV82^^hqbkQU&1t{loeD*aQQ|!_Q)l_>-RbJxK_{vJ!B~lfm@t=cEpvJh}hsp%+)rnH~lm@Zo(c<mK$E_p+ycG"
    "?n)f2%}CV>@l39wg~g%q*sg`f*v^_MzTMbFG_&jeVhxYL+1J^dD6v=$8?5;aTHzsvWk=`6_*I6_x?OL-e%Vfyf`FzBkFxaZ4"
    "P!fk2Vy@?xcX7gW>leYt37i7h_i<!t?LD+hGuR>P8^z5L4@e;L0!3gv00uax=r4naN7X?+vO_SCUr`1M6ftAAen+`!n|&c#4"
    "@kBxLK4|Lj+*^tw|7dy#w}BY9nI!0(p~{v|RKbyj54#M>{ai?9!1nUflfVnS3~hRh85L1qvRn%%}Zf_?3OpkoWxCHCv!FzW;"
    "*Myu*+KkC9VJjxRMbk!KV{`|^Ybi*1@R%kK=OhOcIrJ02`;nlW)|)Tq}pi(t{p86iInh9`53?L&<^ASHL{#9f!mZzHILvw<H"
    "wBiFl_1Z3Yk1gsBW27ZtN5*^9>5cu|PSoU>ocElqTQVS1+fl~2Hn`f}Wpk99L?vQ_Nk|VF=``;EO?jL(FwLQT%F@vaBB=e`>"
    "b5v_5iZg99M5K3bWC85cEslQ_FC11R+<Yp^tio_fOnjmWb36lVx4dJ49l59=|1a?erxHZ(OZJX<tq(+$B3T1P-L~B<B;{^f*"
    "g7GZ4ISL+uma#Gnto7!d66?g6nS#>a84q6xpu0FKg|j#g3-HM0&^$pdQ27|Ck;hlH$#pT5Dv{hd~C+Z$b=QCfKSQ=3UbxJ`D"
    "^VMCIp#z<ZKeoaz|TI<#$83nhg!&P&5_Cp$7TWT{DRb=vgz6Jhr0kMzx8-oUcZoqj<y~@|!J_lje~*+Re^<yNY4&;vi`fv}q"
    "mf4Dg?ys_V`#6KF#C^)NSRb)RqUvz-wtX8{~B2)!L#*Q7>l;2F{f846jj`dJq`%{p?|5nn+8Z7#!HcA3VdeD-;94FkE7wUq4"
    ";UI1U0E5rc&K||XJX<D>@gI6i`yn5qeU!;SlGxDLAVHOkA<OI>^A<pbPOfw%Tv?A7|?U<Np#{hIsX4_^OS*qy}67_3@B250v"
    "*DAyOayi#BmQ=v<y;_M#e;(p8ex^z*eq5nBm1Vp&ddfRu0ZeaRhL|f5BsZTR7LFbCE(n2~2APoDt_>qS9>Ro6MLo|2-YEsK1"
    "#wUBnyWZa;NVanCf|yyiYH`c_jK&|j{dqr+v?{)M*D$g)u$*LuxjE(zF76yiuKF!6--4Ll(dq@y_#4dn^2M<mD$eFGKp%I)j"
    "fa7E#lP1F6?6gEC$bgYUm%hkG4=L-P)_oHXw6~tRv21n1Mn>#$d!GRjs&j!tyRaz4Qh(QvA0@i6z~vC6uUi>L{cu4O|)k$a;"
    "c7_!%UH$t;5%&7@_j`KEEHo#S;Q`u`1VK-Set6Q4aFTA<UC=$abGK*h#$HpZ9?7nY_P`{}7;x}wv)Ro<na!-*Qt54tP&myt|"
    "SaNsigSwS$Rwc-_Nena(8iKbyTm^kdM-W4w7o^H1X?0-RgGU?UxeUlNprUO;Yn#5Lg!!sQoeWt0d)icO`#k1ybJp^x<L96*J"
    "Df(y|HjTj9KvY}A<S+xFyd`zD4O=)&G-Wu1k1jHS!lCI*_rU^<6C~x}(bgPfTr4++XGEyW)uz}UB+690NDRKJfAbLj*_T40y"
    "UR%}B(%!M{q6n4j8_NMtK}%ZTN8H0%LN7v%O^F4PJ-;ReQGVKbqf-n-;`145}S&+;lko`j`sc$^VImeOa$r)&~K@FzlafBUA"
    "3&FEGNV!!-;|AT*3lO0@}aBR|+S4Le&02d;MA;i^n<;e6sL8?k3+>2N@~hCPvOg45w?xzu-TwTN#1fC4pha;Tt{;dgvlANI}"
    "q}!Y23(mUuWSQ<9WNBA)<h5THO|sg;2mm?YP#N*Lilx(9HDkclSRd{I=@5uFtx*-Fi(2KdDua=f}P#%?e6deHX{qb2;C`PWg"
    "jsfb)PZUO>>m6&}*F@g~+KyITM+>_(NMz=QU)U2MMU#|fFuo%_1TjdEi`MKt-NsR33<&ayo>_d_8rCmt=Iw4>n;=$%^CmOOj"
    "&Z0d%=Mcq%*puh-z%uP5aL>JJnpaXl0#pQCSJ64kQ$GJSY2<i0uKtKqNKMKX%NCcwQpOw`W29|jv@<jqR3iYfyqfc2c5Vc)_"
    "c|GqliY^nhtvA~@QtG)Xv2AnGb;qrH2CK$f2GD0sF2)GkOpS$#Js@)`%N^}q&f~$d{)B~&F3A?VAM`^FheCS3KIsG%ER}5Uo"
    "zKyD*VUaZ}o%Wj0b?*eoTkVm1!`F+2!~B;)anO*8^_~q$`LG15P&Z#zsHDKh}t$c9;@Bn(GLVG9<-r&V|0ZT;!pbti>3gg*#"
    "jR{(Le!HUDoj8o){ERCbY*!`CVb)U=LZ?-t@Nx9YN>-SAoj3NIg6Kc?{nHKKD+e#j0GQi&v{)OB*4o9!`i{Cq@~H=mpcJZwF"
    "&YX->IOtvOp*G*Zc*b#CjjmWVU6-R6UA`;;<yhm^_;fiBMmdjITT9rz-pqB`82rEnoRQU{g5X2T*ImYz<(p96HtOOViux06h"
    "e*eqBx4?lnGcG;JL$RuA=)WI9I99CPx!rbCU<oper}DA8R*W8YMU88S2Y2!g`n79mx<gtP3G(((4~n`M3;Q6mj<z62(tjzcK"
    "6zX7t0<f73Ba#$_I73DE_OSYaEGq;b*`Xq9AuPDC^y3V%>K1+rnFtY^;V_!&tVXb6<m+=)pinS&|K4SthLxrIwZ9}hZ$nCGH"
    "R~JEys}jEL1t!wy4o?Cb!SUTD%ydx3!&^{?=uB%+JQ+NvR||$7L7LoH={CZNk@i<o=PcfhV&-e3HBRWSwppGRfS%aZv&um%("
    "V*rJ1Tvu~C(;n1_V3fwl#j)*3m~*)yfJHUZJQYq?`Ly(@`qF?5WEr!Sv^v94`#8$DCd))%5_Krf&94AABusCV)N<$?CA2M=X"
    "?8Xk&GZ?sr}Kn12u6x)vMp{XOa;@px{I892>M)$Q|&HbHpgf@w4(bw9nD>QP*SQ_EfhNH8b`+wFW9f_AgR|W2KX=06(PK*(Q"
    "mJeDrP~zo~fvbtqos9&`Wb#FH5t4|2t%WH-7!UV8J`SgW4aAD`Fe@AD6hv_u?-YA{tXAB-y+^<uRS&9RIzNAE;i<9ruL>ROH"
    "32wpU9aFp#cC_|kj<hd{un^gDj>w$H9)SS40ebi3C8N%fC4kDs{Ld&jo<%gvCZGeE^a^&vZ-f9lPW|9<m=#W$GLYF1pbNPSs"
    "UtWsFl`??AW-Y5n_r1F^`8LJZX@|{sNzli~uU0B(GAA^Gp~~6Ei@-8n(WQl2Rsg6nFcMSm}0)=78wAwgq~-xz#5WyUBxK)d="
    "s#Vo4VLS|I-Ed?cnUE`eB=0zdTGf;BX}_@3~iHF1BN2a#YCG$4A(SCW_^Vj(Wf^4I~=9ohHg&EH_|h{ukm=YarT@*d>%4?R("
    "QRi)>#uh#<aCK)B{o$F`|n3C_xwe|;%-x+(RRA*J;!@svn*E7#p`<7Z^GlE35yOUo%6&S_|-o#sL6t)S_Sz!V0$}3jpUO&>E"
    "@`pacpH{d@>kJU7xFaPxl&TQ9%0Q}O7eZY=+OovESFgFL;znP<%$H3V-%zF#5z~--_hxEj0Lcn^y$oq#pb(kw6Ft<?8NpU9n"
    "i8Oy&7B$mhj7vx8;@%eBR_n0(nE=J!-W6cI;E#(B{0Fnz)-#L>(eLNcy5|br>Q}v5ZwEHJy=+Lo1>AFbT5pRb2G%X)5vuyEC"
    "9g@9fpR)Yw_uJj-onAW-ce%EM$OkOO+~^ng;)-D@cre=r>8wbkmyT&gllC5Rjidn}a^;L^szCKIZ0^<zgCXj`P3huh)m2zc0"
    "_iEtzZM-WM=KSX@kpcfN#pz)W-HKzQy<qf~J4g4*<_-@P#B^RTb-lO>XK{G;3lSUn1V?rN>`>4O?{Qh|(%1ON*L5=DD2s^R("
    "QRF98vo0hTVaMa0Fs~Q#hSgISF4wlL=gRa%f^MaXu_Cw&l^dPdBq_p#6Ms2{t-)YYtebxMVw&$sA%ugFy<ybIKCsDDX+<iV0"
    "!q}Fm63=<8)m=(5Yd4oTafW+o7%&*-*`l;Ai}2oMYf*&l@7#-hLH&U$G&-Bwg~6QhY2q}xTbpj&Z@KzXM^ScqT{to~iH|sQ6"
    "G)?b*dfCgH$e`|(mW;=>oh`~m|Fo-?x5-!2Xi{OKA1JEL14`;d=)cER<;Zq>Q=RVolJ<rkx~V!d=frrytjxt{i1&he%Dy{@R"
    "A0JsAi<t_}+*Ujl3QionX{Zu@+uAO_ADjr6g%^;zQLX9~_33YqBY+&v1sJrwo5}ez`EbYr1Xf%`v4K6z>e4sm-qMW6$oajPW"
    "Dj<}Z66bU%>-$&|~F66Y*Go15(V^n>$U*a-;pO>}-k;k9%1Ln|h7R*C(Et5T}V^@(WWbc{6m())UMnT3KIYB;Lc+M`hZI=v+"
    "ig)KkF29M@DldK|TcCp`EGp`ZzeikGI&mR`k@qqqiIUM`SLOmnu3TTbRLKltn>eXt|`s81Uu-uHo^&(PC7IF~qc&up2aDvgf"
    "$fU-J>C?^CsjTO&jw-|*`@7st;S+O`;jXca>+=IQ+dhs}>NLJd5T;_NEj@s`M7x)-$Pf;OqvAO<=nHPbz8$b*cfV#E?OF--V"
    "?X?{%J0we=`w1$&h%D2aTlS5oveK3DTOpg(#?~Z>Cp%lPnjRo;VIZq$-kAiO`DMlfiJ#AzMzOkbIX<9M+b3XX(nVu`LUjcqe"
    "(D!br&zJl!ig=01dx|@sU=`k&uPePBwv^X@rgiNa2H`Ms?bZ*tZ^M-Xu+GLr&v~ouZ03!V8=yXN`gSyFDP-w{V<BY|F@(@p@"
    "XZMoYXDD+L2pn3W%sQ+l;h<^fc^)K3ya>tdsrd*?#(hEoj)MPvKiO@Fa@I||}}1ppHd6BNA26)9ev-I*Lo^uULorw~D{V*2D"
    "5WYhu`QI2%H^{uYAyplVb8%SYZwrEn6;a%T6yRfaCxEkE`o@G2Ftr&ZP-@$%gxKiT)kouhI>%jZQ4DVrGIOkBI({POX)R~3>"
    ")AWDKRPAwDnl^CcUX_1q(Vr}?@x-~eCU%NcLxz=}N@;ud7XgNaQOtlLabN{cxt5q~)M++Q;tsj>-OQ#zzn`915p&JdsL7=ic"
    "pj@P6gied8?S$OPayU5gMKv|6Z`x`N{@zDB+ikX{k#MC6xvwU{UT=2YRrj4R^H)HG`Lj%4YCAu2~*)|ytVL?ve-DiF>uc)qS"
    "n*=4WJ<n<=L%e0c=8LgYzCldv&$RxCh*q%y&VK`1hp|hxhXGQJ7kCJZi4m?)v9LG?f&GTYXN9CW!v|9l3DQ72efnC|qU{jrP"
    "Bf?b>tJZ@A&m+m?TCxk_+mrXaTqt5O8OfIM>^3ojaE+ioN_OZ*fY2Z~A`Y#{SF&zxBfMcV68=KfO1pK|sD%zZKLFq>myS)~j"
    "^H>;T!%cewZ4`)x*g-^a~1Yc=g_A~-8Vr8dc+uvy$J#6I}rsE6px<%X8$gPqRX;&C&NxFQt`?s**e?|M<Aj^VLcteeN!Y(UD"
    "QJDqbp&cMD;C@V4wVXPfc^Pu}4{VnM7ze@PbMuL+L4b~zU`x_Ce*`1XM=JjqSu|~Dz`{EK(Od5Zog?1(#d0Hem*w&P3G~XDX"
    "Z0BXiFNFKAcQ@<bB{9`%Yox-nU9w~zH|EO=+P1kZ<rR>3V!&YqfhTZt2iquMhg7-&F8~ztdfk&3iu~m=xu@3nq34(m)&7wSx"
    "<sq0`3-O;irl<mW(7<SANYclhFidnoTOn7cWLBoShX4(26>Du>mA4{`g{Ge9J-%!1X(05we&%_bXYroyiXZJ#EC;%RkF_@+R"
    "EE%|eLLavdtqcu&L?i({T&Rf7lc5qe31O~!n{%IcQPCl)}#UfPtF%Y~ORHd|~?`6+E|2b=pp<Q&u#-4_-4JkX5$TcMpH2qC9"
    "??;q^{0le+T9IJf-%TU)#qf5a9tK_1XCI;i}=~Z9exFo+PC|q8siO=Y!TKlaE;oU!N{9vY82yZ<KGw6iBqtTCz_{#l#F4exS"
    "w-P%qX-TxDutPS6oKv8cIo#k56UN=Ed5O-|790}maO}Fv2G+k212F8aq@B(z;lyu$ui%Yn^7ti-HrQp(+ZTILk&_|?rV2QH<"
    "N@)a>5Fi6X{h3CVg)Pp#>PGIZTd_7jgiTqj=o(36_II7Sf9n|=o7m<++YSAr1klqAC-W<QC|Z_@B*2#)M3_SyzX_*JzRK2=p"
    "|H`y`Dqvd4RTc^25$B4~mqMX4@4su<L!X(E1YCq7W_7QD>B_+=s)ta#wrz9&ohs+CB6WoDzSIyoZeC^#wOEC7XIRnPp`Ft_H"
    "rOvt|8K#BnKoIdAn54yj^pl*A^IF#?6O!$&XY)}j=3sqAUMe3Kr~lN|6IP}~(-^S6SotELsE(G)7mhK?UZ*=d5d#P2>b>K!e"
    "aZP1>cs5Ih4a|K<Bu=|es5tj?FtZ9Z&p?NBx3;<*{XRXy!S7ng}Q2R-2vHQ;l=0QkhZ6OmnyM}Ugo9W?i^98-gK02orCf@Fr"
    "B`bT`FkUB4bkXG}R1;|aOB6P$0zrcxhqUuPpg#nG>Ig=zMKZ8e{V!3GJs+Nc8z~FpVi!9+q=;0_c^-W)HZ$wA{&h1LHDjVs^"
    "vpLCJlqB730hCK!~#r6!6Jav$(BR_oYsMlD7WKC>mOZ(AWk1cTDmmikfKCpQ8sMO{^S5UWMF)RVW64*-_EGg(8(x#+{}<4>P"
    "x!fQKQRso$orMY~hMtsL4lrnjAdR73$hraEPtZ1<Z}|Z=5mO8QOr<AzV1~G)`OfVKj-_WsV@51oj=}cau|)8DomXto=td@B-"
    "mKlD!5Ky)+8R05Qp#QaAqc#{&;<CPvw!+o1;ki%o>~q1A}RVv{T<K>WhvFJo$ozQJ@;rZ4t6O)Hv83^XR+nvu%-(NZ0>|H<B"
    "t1-gtn92nZ?Yc>?8nSv2H8&^wOHpGWx)c&2L(Q@eUgGa4e>XYi=qkBp7)KKD2?ou_~1K*<w?iUv4bUAZJMA5$Px}ER_Tx8Vr"
    "A<2H$qTIy5JViS98@4VG=(Ten@vWc`Xp3^0Kh+)8ou%Kt)5mg%paozoOz~_!^VwD!yg}=QivShp(P>{KQR-Hhpl(QZ9Z8?*c"
    "+Gm_*E@B~5&6Lg2Y{hG-!7z_XsrAR4LO72*7YE!Awdg=I_{lg4-PY!6I1^Lm0~^G?5)dWFIJv$XFqy~4q>9YCu5R*!)#CXF*"
    "b<{@WY0o{k#f8E|oVNX9moofn(?x9895aR~|P%Fgg#*Q{r5QfNahxnX{72%C?mEPM*eGsKwb%7L`@0+<fK`+iMbzZU?25^CY"
    "bkSKTXc4O-7JtZ|`SoQ%4MYAjoADKGl?BQ)>!S3_@&Oa-P9ceHl0u|}twIMU0$EoZ~_O(ypa;ml%O3kCPr4q^ipDfGLw+;Hr"
    "WvckJ~)*C1UkwaEpH<ohhc7^e7aBl~!v^Fm>+j};aovR#xxFJH19;Wj;KB5%Mgt%7R_5=+~r729`QB{fM1Q9eED?jv+iR;V4"
    "ueqQt<F8ruRK3umxf_go9Nl-^zaMdzor6{ni*Z{XLGn5Dl{l~~;z;sJRjf8JpocE&ksJ2jKCNBQFYXEGCNjESp|B{ZY4@}%L"
    "K;@(pjQZ?*QBcswYxq`SMX<Ukv$w!AA82pR@jFcr>~;#G@CsMl%c)u#=q2A*mJu*uQ{S5!s5l&&0+<32J?nzmb2Cqlf{2fOp"
    "6i#G!VoEpm_uW+Ri(Le1ch{X(VxY;>*5XKQrTsej4e$i^snR`eyoOQoeI$E!a<@YwsR{I6!zOZEW6f$mvFNE%A*Nvv6+{#&p"
    "0ox$HQ5*oMWi-H^HZD?#evTv>z31(l?*9G)F{Fk*V>aWJCVD_d0FCHPwhVe0K}?<>6fRD4*@+%u0*u(+wj-Sqe)yc&X7Q1t>"
    "H(1}VzsEJAh$zHhX_xOgwEw3ZK>`d>emb7Ex83}lqC_Q-T8J0V}tmnAk0{*Dh^?UMMm|)!>>gz(MCoGSv-bebn<_wUNjKy^j"
    "bU`N(|MK90GWrs!M|q=(fzycB|5?BToZ)Kh2`B%=0E{J4(IX^rJX)}y8^pm#U7={Zqf=<ZFY!}$M%!>*nj&9<4>KBPq5q2X@"
    "7hgP4I49j^{<@ns~J*8Gg<rx8qKy0;c)5ipmnbAsL}clBNGE0)@q^*C2Acltlp-U9c9TBfWG?A<h;iyjV*PkW0vC8<dj~Ru7"
    "c?1w~A{pCk86!H(uzyQhh$fiv^wHzxMx10(A?qX(F?<6~>&~4!<$pkC6h6VEXE_l3)|Y41td<YR!XAq0+Z>j#hhKfv^rU0M)"
    "OUM9aN76k;V`sE}kTfrE*ajfrXJ%|5$Q-5=j8Xj(I+%pJEbUG|~}(LZ9Zf1<%LWx8{a8UX;`0p(;XaPtinpd&&1(*S<rxw=z"
    "J9okpHHXu|u<cQm#2qbBWWg{;Rwp;td#3zZ_i1amK0KP&=s4>3gs@UMwoxS|lyO~sOuvaQIA4Q>r?Rz6uxXO_ViRnCN5g~0<"
    "6b?x8Ak4%aO?~#^b*vIP1z3zs1KI-|8uNy#PK6ibA0*LCdOj%<hexPfLUFkpxvxE7P)QhK|Bf!LsdySGj5qYU6LQo?=^U1+Y"
    "D^p!Y68Xynj?I)I$ruFkZYXS9V95t0TepJC5qaCns7}qz*U@Q^qgDXmxD67qmo{F$cc*X+~$>d!gG@u#iA-^p1yA7MXqlYvI"
    "F7aNad5IzKJrtz>E560{EEJV#4POnVi*~ORBKqKz-ow`uR(-LMgrq%4z^2qJ!*zZ>`$)3Mx4dYn;KqsOQ`RvScELhdbf7;Xe"
    "$DLqkKsYTiaNG#LPG6qzN|1!f2@w3slUk?b68-F)BLZ3YB+&6-}InQL!HRimSbo}=_3pxSX;b20%;=!YGN1daG+05DXLf9CM"
    "uXXWC|(l(YX*j=wNn4H57>0vm2#FRr!a436xlQnlg`*ieGPZH<;c-eAEs;6AJQ$aDU4!bjOH9#rpChFIqroYqR=!|igNj=#-"
    "t=EMHOH>>tCRa*&!X_Jfpd4!^<gfN7!idw)*%f|lN&)|gLn7yP;Y>7=3Hbo_s~N7Xg7&)np91|hE!fRZE9si}5wY80j_!Klv"
    "sb`$KJH&$Aj}>4oMo^!x9BG9T+A1a{#y!0#_FD!M>>Q8Eb_t%h>_FbQC?9ydaea8-?gP?wml*|ExoAKW<^spn_7K(*6H|dS="
    "d|rCXc(ifCUfRmc}HFB(iZ@YGh8>y_H#^#2hi!a9*aB$EFiCRj3d~&ILa#g%kqG93w*-Uy6H|6BRxkS&V>dT0E1MwfGo9K7c"
    "Ouz!MGfqtyWXl0NWI<<zSwUBE>};Iuv=r90UX`zohI<I?r}ZZD&utC+b!D+R{Y=hEAAi&k<u08TWvd@yCau4DVq0*tHaD}gY"
    "K-tm=7-KeKE<xocCwV+Lh{87Zi#YrAdmr<pq1-qwI-(h1d{$e=^?f?%mSRxy&uwhwhTQiW2i!NbETBwsvXnOUX^g$~NDFUlp"
    "NIaoF)@Z4%1-Y+iIL_8~S;3#*AyhF4vV`VUZM1!Eso`y9q;^&NQ{hJ4qU{r=T3@=lg3Qkdxu0WppILZ+8+WL7>Ms}Dp&c~IS"
    "Gx_}qU^yp7|%OM6u0*iw$g2(Qxz~+g8#H_zNCj;Xz4gu_c2H8;zrn{sr?ND-t-cg{dZ)+FdSq>TYT&Fz^l|Y5Vf;E9S(@m&o"
    "GL2F)?5c9q9L`9(;fAR1ZM#Yf5bzy6ib!>z!28+6B?mt`B&?qs=B3gzR@8<8$CGp5I7fQl$`t@e%9We~4+-pMA07g7zTyH)B"
    "FANN4f$CtKnfh~NH^<H63{Y@8hqw0cH7OA%i3_~lGNeQmlpTDRUT1?Pjno)h4q4t!o)r5d0UuSp${<u329B0R?rS?x@?e5QL"
    "b1gN5E+m$^XduQa5CEcQs<J0p{gor2yGqEjstBu#CJ338W8sve)wWehpj&x`I>63UN)p(?yrFZZFuoJD3$dYVlszsxS5NucC"
    "zx{^bV6lD;a7*hhv#8&d+~<)x$^)cX(qAC1^#i%5O?L7xY7O7yvT29cPl4+evFZ46Nta{>g?$F9plYfQ`Ei$0BvV-Q`aaHLt"
    "HOKRL|MZ`U+&3KhDF-0%`3-_%7>JJm`dBNQWU#iKy+iAFcR6gQpB>yYNV)*4k^U~s<WPWE6g;+?G_s-&<H*`phoI<{kxR**}"
    "3cYzz*-c5LDuvDAO;(JI0(&@L|?%D)NiHW@(ESV#&)LI;04FL)c-dC-ME-tK{=^3TON1Bw-Kwv7CWC@C{)*BX9m{ch4~+kgd"
    "Bj;U>@7E!a*FyJ&{^y#Zt|%^C>=pmyV4QmmeDLu<*Bq@K81m<@;y7f!Vhs?4L1B-f+3-h@cbOO76)+iDxU$;inXILKXF3!~d"
    "W<v`gon!ppR36^Wg6}~JmqJD4%KHjS2r>msoL8Up-nL^bM<{22>33(-<3Go~!2cAU3-!WSu@D5=Z7;^9lZ9{uq*4Ys~TI(#7"
    "ZTw<VURP!%j^i;ZU79MEj={O#A-!1{cU}TQT>4YAd^Yi__Ol%>5B<UDK7Uq9Mx}WRX0f-eX~7H3=5H{NAB*kJ9a|oYEzn}vW"
    "*cfO=?-?RyD5oR;KMu>6<w&Wfrr_M?~b3qS+lQxIzuVA1M<-ey05TJB@*z@sx{lbQcl1^Y3#ps0j31?go7V4dqGvu1_fnsR@"
    "tUT<Uo+<ayG<9Fx{84wx~BsSjaX-4d}poUj&yy?<N2k?!8}T=7>Jpw0i_W_vVd>8zc(Krud^rr&_Dlj}G<$mXf|bTS@HA{Xy"
    "ulsEq&vQt?-ynTUT9t+C1-)49!+hA%?F0ljR+qCe*wz}Ju~n;>reILU-R!TYu=o`-oSL=;ju-UatZa0;!31so!A(+F5<b=ms"
    "mM}A;Yl>cnOK$$V^drSwrIZmD|mj|?SDF#JfZA~>Nw%K>1O?kvGupyI&=u&+gxiH$>^JH+}>~kep=)W~KY<x=nGD*{BiF?C$"
    "7fA5EkZ<*z+*3|g|0%Utg8Od&1WOPZMz;NXN54zN@;_5s`sK@|hEer5$6_~{$oWKSmBbjG*m@<=yHn6F<~!yH1#bM>ASO&EM"
    ";w>^b61dy`Ilkl{x-8^;K=O#{t}}?hX&zE%)ft=9`Ag0`?0d~QNCar;Mx;Rf?mS;OY)0abJ^RxllYGXRxmMkgD`zGpie<%E&"
    "pV9fte%~pXu|MGxwe%)^cv)_a7#`<3WDw!6)+poZG)j5<jzye|A{`9h#vuO!2^E!9^A0$Qoi0LPxy>uvv(a(mL!m1=RypS7b"
    "nXS3<yJe&0a7Hux0e_XrP~n3W!+j4rFio{*_9U2ZEiO@7A_(!z#8y+=bcAPINK=+fiyDZ{Xz3m%}fVO_hQIZ75Bq62bC2^ac"
    "(b@zabK<ktuvbDr&>8F3G)N5jyn$_Y?&M*WkYoRl%kb@34tx2>(Q#HT^y_hj>4WAx`COZoZSf}`WH)=Cmi`D_bm=gMi5Bisc"
    "?0VR+1hAo*oC77a<uw2gJc0$qvh69^BPrs&)}Tqf@m}^m6J>r#aO2lW;Ifv!X`o@DrPM4BS0wKcn{tPM<6-aDljy_QQp)kMm"
    "exm*IJv?Ihw`qT*jrt$KKX+Z9_{t;Y+(~X*9ZQX5WmH(CJGMp6q4E)1&i#2prd%9ksBC@uF9%WssEdmk+t6IZHT+3VxCMw3Y"
    "0z2))3+o`miBHliZ1xtl2-n-+Lr3%fZX*XvoA<@_&yO|K|jRMSbxnGXN%t_&7(|GF}k!!^1By8d4mTYm;))V`cwf+Hn13>><"
    "{Y5uiE@I*)0h<SGsNSloN$RSU1jvKAVK(Xc1Y?gX6H-3JcSATs%x8VJi}m8k<Zo!H5)_139@Yz~BuSo*$#YySH6IXMho=q1A"
    "ta^NBdTvj%Enmz<|Q+t+Pa0MT?4FMy$t<T*&PQ6KLCrH6EY)#5bO~1TzJ=gq5DI-1xkPFPM%7<7l)P`N}h<GabJ>{V>_CJ(p"
    "n=3VCtxRi?2)6|Jb0_gYdm8mJ@Xl}{ptd!#2~u5VF()EqJo_EVGEq;9a0TEi{a+}XT?U!=@jV3pn`m5!T6#o*fGJ|nbZauB<"
    "-YyY=kGw7J?KQ4sLDV(9Od^SD;|wl^xwH_DWZ~?{TB(%2W~<szIh+)f582hTHKYZaFf!Uk7i6W=Kq_2*|}3f%&$^uQt?_f!^"
    "8^U`Gn%n#Nxy9Ngiad!hzFwDv&3UA#&kh{iR-m6IKVlvhx2heXW}AJeU*G-zASDpu{aD)x#{owjfE@a88R8W<n4pYxT(3CDw"
    "{>6cJ;94`$(@yYJJin!>AfOL=Eq1?gv@{HTkgSChzm%XxZPJ(Y=*2qDr2>~6gH%#GRGx)^k2dU7%@jVV4vZn3)Po^OQf%vbr"
    "KEXr#ja1Ea9$#i@G3=#V*YEa7;H{JPr3Nt1sR%%@K>Mq--87$?TVWoFA0V}lOxNBr@0@Wx4sB|!CbuN&`nn5R9gGv$IWz|xo"
    "(yFK6fXqIoO*ccXcrKagBv26C?;Bqn0ZaeAm&#5b>iRv5Xr>o*RjInmmYHhRz+2UkK~fM^cM|NWrfsK8cFLM7gS^ev{^Siia"
    "Hny7vgbXPdtKG#lGDh$x6m@7t}Te+b)X4z{Bzrvh|{%l)na(ZQvq4NVTaVAlEyG}>AETIKpB&6#sqS|q{qzV<EHk2U*S}b?I"
    "W~LVy+bg!tlZ(u+sCH{8Q~=hME0Jk(~y*D%vx7yB6cXfCb22x?-YMGvq*0!2$6XJfUgub{jSOSnEp7CGHsm&S7i+rssa~ig&"
    "c0&%@IJJQ}`=Kcn+ay6SuMihf2N4@6?_EbuspsJ}ItW$yE{!bOq^C?O7(4S*V)BtgSZ_QHVdN`)kBN@Rsz@`#=~4ROOLfys>"
    "KqUV_a(E4E`Tx&Tt!Hr3tgC-o9cqo5IP8eA5TfpJ<+XV2NM6?DCRwm*=FWLCry3!ieE*lCO_9%?*?W88oU~dAZX9bxf1X$Ug"
    "E`>!BIX~g0aXQw=G~t^(Tz4p(>V*~`!80-cb&f&e(3dUSXO%!u|C2?IN|RsSrKW+*|CX9ZuogP*_`v-i4tM~ZRZq?-kTaoUn"
    "jFx}8F46p7BlPa+b)6(WCfqd2C}bXqq=wCvX+B4k$+64OgGBvA{z(`%5ZP$&o}XKR&vNtHn-+U+`hZ-TlZK$w}=ianY^)tzq"
    "=mMNQitRqU$Y4PJGq2bT40d3hp+x0#md--^O{!I<cRSKUf0(*@qnvC~HpyMYjbCZHJjmP9$))RNi~dp8}NdtiQ@Xi2%*iu9("
    "X~8P+;7CbVe%yq^Sv%|@Uks=Z_o^(vQJ1tEIm4(V{HBvh2_Pv!!bkhDw10~K|L1c>qz4T5*xWb~N^WhUQ=zIB==3W$gIOu~v"
    "V;K=>MEV<Sv?k-LfqxA$spa7Y*7`!ih?H;q95?+7PCXCI9>F_v{uXx0={W1>9;+v?WDyQ0Pcq1rgRB%W#?k;orAx#Tn(bX<@"
    "M0=M(go?r@b;9NW*S3$l7-R5yrk{Wz<xS0m9LGUN0^2ibCny8TNw0k59H5Yhp$ls)2N}U914X>uh(?6yLXS`>{bQL}neNx>7"
    "{kb4I0AVHv1#rE4~2njA_-VnKo`Ez@yDfVIZb@&w+JuSu=@iJcLh7h#sb-Xa&ZnE!@c7F7SDW)9jG7lYKXom<{xWK&A#Z<R1"
    "N-qkS3*D*&lZHM5-!I{~zLgo>E|d?W5F2-Z_lI4%8QlCN`-@MG;$28b#^Aky_;I5WGA~Lc#;XE0C(FQt-Kd`4lbkuJ!%OZW4"
    "KTQlnlWanw|+HB91V-eCbcn*l)BU5%xzJe#Qnm_T}E#PehjV{^r27<xM4pFg3H?c?+1-g}=%p_S6(mKX{9ZDn5RuBl%4wMms"
    "Q{l}?TjVmc;BS*T%;>^Z}Zi=K_#LEGg%@|Ta5*!bb$cUBvCMTQ4QzMlOMF~8(q_9?TTD>hikq3(D=9BD?;<7d&W(cgLi&B+="
    ";{leyM?s9jH^v;3ev0)8&OdQuG?<9OSZNhF+Wv=ylkKzwTj`tWcR#0E<!;!gYgZ<XA7(W>B<dReu$c%sMbdfiWQ7qcB;(NHV"
    "~F12Da}4}xv~R!T{i-?o1rt9*K5}BGLp2!%3EhStr7koffbmZnZNf}$BOQiG=sw-Ic~}uqQ5E6Eo7oH;HR1Ec31wm91kkJ1>"
    "`_Q=fcN{QziK&2675dv5sZ+emhcRt`UZVGE~o3%Ogt^5ak|Jh;uBcqt{c=cI>6yMt5IB?hg0a9h)8Buw^Ik>EdXW_f8G(c~J"
    "EgU<rRYv26~Mr_IOrC7iP3cw{5PasbE>dJ=twYAG7rS=|*k5JIC_enAW}oZ`CmR1PiL?5m2K2@8ji<gw=SuZH~1GZy9yO;v$"
    "3gooG<lCw1Y+fWNc|3h5P2TNh!s!Heq+Xm?RA!GyzV4@Lm1#^`+sN{a=$^~wtt*{wVa}Zd+K>Cu~9n$&KHC?CuTN3Q6YSehy"
    "BN)R<HK|O@fR@>{olaRMKVbre+-z`ontj6-KtH`o5`!E*ujkL=oNb%ZYEPB}ze5CLHrDRdO*=NRxhl?pl3kOLe(-L17zV*4V"
    "_A&sSUE>0!@L={3QI%!QNw%v^hXuD+;gubyR57jfp?uR(4-&gs$J$m4YK^P*A;R0g(ronD8853EA_8e?oL0Ud<d%QgY&l92-"
    "t)gFvMh~{Iv`xpf4=Tu1%Z?{<_eU4y{nnoyRenv&`K+1t}YX;g8V9Ld#jNx4DfZ$Qw1QWDKm+@PC4PsLx8#q7ux+L*m#}*lj"
    "Z-`~pY$v<d$#VS#G(PC7R-XbnAk*;o=*E_wmP9|R6_3Z*q^5anGlRRoTbY4>JBDT~9N@31ZX4aK%tK<7HuX!saNvm|EkH8EA"
    ")AonNCF@po23I3b3tA?H%g%bBz9^NSkLuq@ZVrdOF0^?#+<=qtIK4z9k)xmibu^rmNF&dC=P7{3?=dCXPW}wkbB{xZYlHfcM"
    "UYVx(xoBg8W)JAGb0~FnnxoK8qqJAAP;G_=!|f^U9V<zFg-OEcR#0KA^5Li&x*^~Aa=;B>DJO#Ta#ay`wAoNN<FMdGYR6U>U"
    "L~T(B3)K^Z`$ls5m8GPX5;jL1zdbmfHS9wS03*x+cd+@IG@6$AYOs0*S2I@ns5+$OdsdtdTdGaa<N{?{D@Y<=+5EX48#Q&YL"
    "|T!!T0;Pf#uJZ2bEATi)1f2NwKf^-1P;qo67VZOu&+~_Q23@bWzmvd!Bi~9l%rqodP9~Xy`1aGqv||4(EjxC`(;H>X@GL_Vg"
    "+$?TF}1pde%bxTprzLT@>{5Jwd70TvD3+?&4$$v~YXz?8#-3@A|CWRk}4uBaWs{RZkd?*k{nczbpDZR%yGl*-_XbL*8Oofu-"
    "}HQd??W_Ve~SrlOs=!{OGcP>aRF4gvTta1#SdHiWIDawS^*G!GJr&d4i8%YL(YD^r&;6X1526GDfVx)Rk?`MKt7G*5Jw+j3y"
    "+L+?tFBF`SVTW8i<||eKu}i+7I&%@aDrZh;&?LbVWBN>PO*g<yT>3<>R8n0GDx$yn$}25?y~gz*eTySHC^S3iOrGk)7UIWOK"
    "{hC5mpzWKwldyI$hs#6HRhlBD$rr@`N`qG5yx^4i-+f4@|!<PT4Y{jHk=)ixmaRlX|A(cC4M5vkS>Ife~*&xc85we-)zV=H)"
    "2syTl?Md?rgIEWvSk0rBxB@=4re56!37|wa!;v_yovz7aDu{Pc6=#ZXGtoINcb}I3O4)v*L2KiQsL%y7)a9$wt<%E7X!oNwP"
    "ENuJ~7Bf2`3p{O_Qaa*GQXNsbC8<5aP8L2S%wkB`Z%xA)WNPgrLM3h>JWVkRw-DoMM)YLB~Z_K~8~KG{_=r$a1aat?mShjn1"
    "v!>Fec0+kUX#@Wui#%`IH_ZqYQ*!`>U+c8w8aNV1B^@B98su7=Zv`Qj0^S$@A2a9V=i}+r81Ul?F4`h}l^YJ)Any5NYqabfn"
    "9WjF=$tnxW3a4L1OsE26MAue6Q(8R=R@xiDU~Z~hSL*}q<pF^9&?fCp39>_k$T`uZg15-$raopc_ASp!h$g*p(-YyGn<hV-w"
    "S}53ijWo-=vDIr7&rBOnm*MIrr3Q+pPv9;074T@qbJAWsb0@iCt24jSz<W!eNU>%6MKPD&zlTKQe~_x!d|a1Ahb-cd*{s)aJ"
    "DhMa>XT3y13g@%M7)AEM}pzzQAbFkmp_hu<^}59%RmJpTy!WfqnoGMC2$yHztG;G$F|E0?vO2;lN&gqxP%815k3lZ}fI^_XK"
    "Pe*L+qj!N1ccLQ^QT9=%2uqvxK){&UzdLgVplB}(ohhagJhyc^4tv`p5?sUU;Nu`rAhz7WHqI<)&*$X${Cw?jhfQQB4vxOe?"
    "p=)AW_h5@44f~<;-&dHAd3dYFwT%A4dV0ey|4P)}wKm;yE+$eC#LB9)`mW)x8RxW%TzRKA3lNvJ%@x1TbRdVhm(Q7$efN=fB"
    ")UT66ieCtzdG}cnN5KK3?vc@yeLpp-4u)t9rV?1=J8V;zKZ5{=dM_qMR-pzgX>2-B+>H$nn@$v$pt++{R=3fy5pKQR!}?Im6"
    ">;XN{>*n#_8)5TfN*7s92Ht`3efn%vBR?smggY)c{-ji>_JNCI0v>VFV=i=98Z!r6>TRB*7dBIBV-W`_Nhn>GvhH9`8d6n_J"
    "tse?)IJK5NYPKr)#+YeaHt+`h`{y+{XHs%ayE<X*eSQ@_@$uxDxu|Yqm0Zfe0}~UqFpUfp2r49(Hrl?34!3I^csYSUk=Q)*!"
    "U;WEC~W#LCjz=d0MKo;jJr9x)R6okJt~`*uhW1w>0c%iWRKyFY%w1}PqE+l$I779MN*aFCD*y|b*nnd|JfMAcfya>j}&uv6l"
    "+cC++UquS&39CB;<W*Arbp0pPBd2)BQ)Z?_t8Ieb1Nm<oH!8mh8Xq<0ld7~O?g{X&&rtjWyxP<?w!ILUof>K~50RRjbB6NM0"
    "B@|d>J<8uy#*q<789YM+b05?_CU|F$^0$Al!6LSS3d80mP<*D%Fo*hSCV&YgK9MSwumOqqHUqBc^D>5G3mD(hB1r>hFJ5nXe"
    "^3qO7!QA0v$A{1Wv7-X+<^E*r0@ufxaye3;oM^afsSTQDdAXd+#;157;l!f#&YX}mzgP^ed$Ww9j&%9yo)Jb))n5eVusZ?sP"
    "5Jc)X8c+K3B(G7C*zRQV{A`N#g;fouZ%U1R#DDN{F_Iau90><BR9Zt?)CU+L2IS5kF;!=ekD-hhD@cZ7vX#lNtGRB>7pKO@h"
    "Zml(a%Bg~^}6ZIR8X3M<9&4i0%$a{vO9!{g1ANdU0keNeC0)k|!VF4`YwiMP~LxN8?no2Y~Av>EP~8uLox)CcM+)f_;Ync6z"
    "QpkeZLOTyshyi8rH6$bhDX-<LRb0|!G6k1Pk#HZP@MVg?C5E`1e5re2=V143CyplA~syuuq;&0h^6a(o*4}a}}m3X&~J`4IM"
    "edWpq>}DM>ePa(tmKLh1pWoR5rl0<rSKFdi`;M&DnZrS)n_Z28v`b1#WDejJk@*2}FmC>*hc0svVrP*FeC5oDa%}A}hG`0lz"
    "L=PwoIO!pXDsUnmNBFo!{I5y3H+W{4v_A%&=+N^7-FoeA!9(miJ%HTjWA=`fp%8$ci<0inkn!<wk^vc{CjM(ivs?@;m{UunC"
    "(VStniT>v_W>#uFT2uIw(_wta_tZ3g&yRMxUzC$%e&xq&d6FWQLv2M{$+jzGpS)LStOP#GVwzAHcYQ4!V&cq2%!7x-N(t&fE"
    "_A;&X{G5BbSQKwq(NmO>|dCKjN4p~u#=j%HG4pB2GMS!6C$C<!Sy?gCgu{Vc6i!e07zGxtpqN`>BlGkm)^8r)vN`9C&#;BLS"
    ">Ye&pUUNRyq#*$3_Xi3|xE*l*~n2XvzmiTQ84d}rsf{4K9<8d97Ulz>iZP7@eMYDYGkZL7%emHDiYVd>6K>XZJmFbggLh+oe"
    "I(-mHO)^9xUjq6?Ys*sU4dgF-RAOE~K*W#6Nms?~1n{yhS8t-1&lq}l_?<h13c;qWwnBC?7cPDvp8!QPiF>WJt4C<@sC&U9m"
    "dL~ZRaJ*?aS?$I%jSkM6t%3aH;_-BZ^9?LpkmF~ug6JIN-)w=KB<_ohQp9&f|f-t4QW)c(c~QQm_}aT51@q<q;8li0Y78ewk"
    "whv*>sff>f1~VXJI_T;E#%s6qL3r1q8Kvy!^sN4l`e3l+i||2teuk`v#y1`(PuRBfV|?VG0i7@AUFtO%(S|xu2w&9j_0Gs}l"
    "GyExcQle`-4?hz1=qo-Xe=)n+bB?fPU+@qzTv<HHh4UJ|_#n!8~gY^S1PS%7HXllAs4V)GXJAa}kYa?lU8^mZ+xT=g)^(i-v"
    "B79LwwiP)dvB_#cR|3NO|VX5KS#SS1^t~{tShL1tElJ<!LhX(Hi;6}$hBxM|ve_WT5Pq>FxxGETS=bM8$IEtZIr1(!<yCkC^"
    "CIp7_eCFz&4Vow+$$^|x)6`gusaNr}Q^#Fi{}X~0FhVx;*tHs>i$4VxofFg5n-Bg+C1EnA2RX32q(&F2`Y-?H?0ib}2Mf`+u"
    "ZK~H4{c+@*L1eLxP<}kHg5Ep=gqoEA{}xZ$uOx~H((QvelPh^#*EptRdL}kR_~Cb@JU|_N?QdWo4WBTxnH=lpJ8i@0Na|0Ol"
    "|y{GsIiw_0-^~w)IjaLrj6FJ<uNLCA*tF_fUU#xs68`CP5(oDx(PLdzb~xeLyVAPlk-OXVw_sWXf<}x&(m#{Vy0XoGT0F!F9"
    "7)h|XORS+BK`M5>0YRwkmkM!3iHIW<L#r!<mL2n$FE<w(weAUCM*_;9EWSG>5r3!+`|Ubdw!9~?o<SXWs^g+g4R`>N8ZXnLs"
    "R?4n>3F}EjZUX96%@1qy$@#3|z^CNPv^&NWblwlsC+_sfNdDzR3kdY!zcKsRWr1J?b^yu?=m@dGC;v|a)V)fnc6E8;wuIU}W"
    "^ZN0z04X@33Z5?0t#l2VRghXxuH4<Lu$C&KKL;-T(3^Rw(c|krU}oh!+~TTK<X_L8t=r=AWvvmfi7K}`OJGEK3ri2XVtIR0P"
    "M*BKU$gESW~gkK`MtNiiR|xV@d5@*s&(r497N_{f{A-5QWnY=#$^`|B(gVjI`6P?i3)u4kv4O+K|gWVD1I&O3NlbV4cM#hLQ"
    "JqFd@Vhz&cd=0(O4`cS4pEj$Zf@`rW^_K*lnpFi|6>vUvghqNyb|Pt%|-S2x5088WdreN8zcOk=zAmuAIk`q0s(~@if|7lUZ"
    "A-jBlHUdT|te$IaS#R_0Jrm&9xj(-eAvr(?Z-;Y@&DoX?%iIFe}S>%KxMB04}A#p*W0Zr069t#9fF3prHA90P-&b7N>X3<gI"
    "C)8K|*|C&WFKnz=GA^HLD3E<8loZRB4dfDyhtIN@^P!33y>!JDI1$d83e;vPv4d`=mlf(}lHs{J#(h!bzcvAd%V_F;KW2*sH"
    "EN;@#n<oup)g>r9aupjb;|I^G{#kU#s;drMivM!K{(ryT2!1zCNlG#v$gG#47e|TX4zNkQ8G<xaXswhc+vvQ_S;NqO*UK->d"
    "FTjw0!{;{hF=*tjhdy@bfSsgTZJhan1r?0;2Ckklp1;=ar7Q?r~5HFUP85Z5j;P(M~vg+B7hy`-ng>3)*B#XYGo=wM%JW1xv"
    ")_THxjTzKYtYbv0m+{@~VLVi>IeRec6#W*T(2#_$d(}0%!56xE02(#;d_bREsiHJhXz=9^}K&$3#}}q1Wa8eiiZMbWT^v5FR"
    "&?pDmsh+Bl$&8d&rep|;n+u9)@BSE}1qJEqYX(??`<r~dm2JYo3&nEJch?p^)ahUc$hpobPj1LY#tmJ#1sEM(6EK?Ss($hSu"
    "%aU*8q5xdm21O=~9kr#hG+)BIMj%(wc*kwt1GLKcUTC#MX(SeEd)k2<*sjJc#cs+DU`p=il(@s2r=diEcu$XZLa9TxSXiox="
    "3D;Es+`++@d(eQT!*iY@zcsNI=I2+jF+awIG)+qgq^UlZ4|s0{2@l;m^gH$i1gmE9W?AQ`kKR^Cj+k{mIV=NJ(8T+z!aZhYS"
    "^>!3{sElCUt~W@C{?gRZRp?tz&u3OOYy^I&^DVm;9b84g7srzkNcmbCQ;lBnX^RjMC^ZxDo|@vdus-lZgPU&A#OxVZ>E)QxZ"
    "xPQTfNF^ezECA-!<nxH3N*H<TMW3Y5G{&!^^9B!q^0yW8DCIyoI<g#t<{BuhS->^^RSx(19XK9SF$I98(SAmZMlj9VbXaKlB"
    "Nq|9NZb*cwfxk{D;%Ul6m>!3vW?Z&C<#aay9RK%Yww3c>iRYraX@x&jJr6$up%PW$<VGw7v-BD<D#|HIMCZP1+Sw$AbX5)n7"
    "WTF3}<ay*Z7)yS9L1Qix}s~L*x;=2N=N14X&P&qlU8Nn*NL?0~b21dylh^;vOoa^RLPK)kP{M=hPm>wgEERP5N6B+Lae^>#7"
    "QudAh{g5?c56Y+5T|d{CD3U*x%z;1aR&E~!w6#Exy!m7t#-@ubCV<BbOX!}Mu(863H<eiO#?G}<w3O7OBnMdUYm7zJY7q_#i"
    "F2S_P?9mh`D@LW_<)zUOiO8PidD$$?OR7X@{#m$*ajtl2WEnQCh@e}_4#Eef_%o_uG~Ts_R8(CTzSdLgdX@IZ~ae|sX+6Ao-"
    "A|$-D1c0iK8>a=`5gyiTEtl^rSRCyZEfqVC%R@>{miSZi5r&yaxL$F)>sP@ncjRSKqz%$RSM4mR4V>m}`M$E896v&2|Zs`V@"
    "#;n^<cNw`mrVftHtWj^|&1Xw$R)j$`WVEeAorP7Vu^xtHPLq>&`Tw!i}uwL_kG7l;e}CxqHAg6B(iOT;pYvjqM$=W&=qT4Jh"
    "Y!dmv1c^c_ukG1?QI-+w;tRLt#o4-+lvhhSX@f|w{=)Lq=!U>VAz{8q`&<~^f$qBlI>^WUyU0EGc@Y-c*Pr+#8ZU8ilZ7fLU"
    "do{xQ*T--`4)JdjQh%KLjI{(aM+!x$*3j`-<Hd35dfn+qqH;GVh2s8kr-?FW1l!&rwS?tD57QCJ%TzY9"
)
_CP61_ESTIMAND_RECORD_SHA256_HEX = base64.b85decode(
    _CP61_ESTIMAND_RECORD_SHA256_B85.encode("ascii")
).hex()
if len(_CP61_ESTIMAND_RECORD_SHA256_HEX) != 64 * CP70_TEST28_ESTIMAND_COUNT:
    raise AssertionError("CP70 frozen CP61 estimand digest table differs")


# The closed scientific inventory and reducer implementation follow below.

_ROW_SHAPES = tuple(
    (fixture_id, strategy, budget)
    for fixture_id in ("T28-M1-Q", "T28-M2-Q")
    for strategy, budgets in (
        ("bounded-rejection", (1, 4, 16, 64)),
        ("fixed-budget-sir", (8, 32, 128, 512)),
    )
    for budget in budgets
)
_REJECTION_OBSERVABLE_CELLS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_SIR_OBSERVABLE_CELLS = (
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_INTERCHANGE_KEYS = (
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
_OUTPUT_ROOT_KEYS = (
    "schema_version",
    "fixture_set_sha256",
    "request_count",
    "estimand_count",
    "estimand_estimate_intervals",
)
_OUTPUT_ESTIMAND_KEYS = (
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
    "development_fixture_only",
    "record_sha256",
)
_SEED_FREE_REQUEST_SHA256S = (
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
_DEVELOPMENT_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_SELECTED_CONFIGURATION_INDEX_BY_ROW = (
    0,
    1,
    0,
    2,
    0,
    1,
    0,
    2,
    0,
    1,
    0,
    3,
    0,
    1,
    0,
    3,
)
_M1_SELECTED_CONFIGURATION_ROSTER = (
    (),
    ((0, ()),),
    ((1, (Fraction(1, 1),)),),
)
_M2_SELECTED_CONFIGURATION_ROSTER = (
    (),
    ((0, (Fraction(1, 2),)),),
    ((1, (Fraction(0, 1), Fraction(1, 2))),),
    ((0, (Fraction(-1, 2),)), (1, (Fraction(1, 2), Fraction(-1, 2)))),
)


def _row_key(row_ordinal: int) -> str:
    fixture_id, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    return "row-%02d/%s/%s/budget-%d" % (
        row_ordinal,
        fixture_id,
        strategy,
        budget,
    )


def _feature_projections(
    fixture_id: str,
) -> Tuple[Tuple[int, str, Tuple[Fraction, ...]], ...]:
    if fixture_id == "T28-M1-Q":
        return ((1, "axis0", (Fraction(1, 1),)),)
    if fixture_id != "T28-M2-Q":
        raise AssertionError("CP70 feature fixture differs")
    return (
        (0, "axis0", (Fraction(1, 1),)),
        (1, "axis0", (Fraction(1, 1), Fraction(0, 1))),
        (1, "axis1", (Fraction(0, 1), Fraction(1, 1))),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )


@lru_cache(maxsize=2)
def _feature_ids(fixture_id: str) -> Tuple[str, ...]:
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    dimensions = (0, 1) if fixture_id == "T28-M1-Q" else (1, 2)
    projections = _feature_projections(fixture_id)
    result = ["count/eq/%d" % count for count in range(cap + 1)]
    result.extend("type/%d/occupancy" % index for index in range(len(dimensions)))
    for type_index, projection_id, _coefficients in projections:
        result.extend(
            (
                "coordinate/%d/%s/odd" % (type_index, projection_id),
                "coordinate/%d/%s/even" % (type_index, projection_id),
            )
        )
    if cap == 2:
        by_type = {
            type_index: tuple(item for item in projections if item[0] == type_index)
            for type_index in range(len(dimensions))
        }
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                result.append("pair-type/%d/%d" % (left_type, right_type))
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left in enumerate(by_type[left_type]):
                    for right_position, right in enumerate(by_type[right_type]):
                        if left_type == right_type and right_position < left_position:
                            continue
                        result.append(
                            "pair-projection/%d/%s/%d/%s"
                            % (left_type, left[1], right_type, right[1])
                        )
    expected = 6 if fixture_id == "T28-M1-Q" else 33
    if len(result) != expected:
        raise AssertionError("CP70 feature identifier inventory differs")
    return tuple(result)


def _feature_bounds(feature_id: str) -> Tuple[Fraction, Fraction]:
    lower = (
        Fraction(-1, 1)
        if (feature_id.endswith("/odd") or feature_id.startswith("pair-projection/"))
        else Fraction(0, 1)
    )
    return lower, Fraction(1, 1)


def _odd(value: Fraction) -> Fraction:
    return max(Fraction(-1, 1), min(Fraction(1, 1), value))


def _even(value: Fraction) -> Fraction:
    return Fraction(1, 1) if abs(value) >= 1 else value * value


def _project(event: tuple, coefficients: Tuple[Fraction, ...]) -> Fraction:
    return sum(
        (
            coefficient * coordinate
            for coefficient, coordinate in zip(coefficients, event[1])
        ),
        Fraction(0, 1),
    )


def _local_feature_vector(
    fixture_id: str, configuration: tuple
) -> Tuple[Fraction, ...]:
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    dimensions = (0, 1) if fixture_id == "T28-M1-Q" else (1, 2)
    projections = _feature_projections(fixture_id)
    projection_map = {(item[0], item[1]): item[2] for item in projections}
    result = [Fraction(int(len(configuration) == count), 1) for count in range(cap + 1)]
    for event_type in range(len(dimensions)):
        result.append(
            Fraction(sum(1 for event in configuration if event[0] == event_type), cap)
        )
    for event_type, _projection_id, coefficients in projections:
        values = tuple(
            _project(event, coefficients)
            for event in configuration
            if event[0] == event_type
        )
        result.append(sum((_odd(value) for value in values), Fraction(0, 1)) / cap)
        result.append(sum((_even(value) for value in values), Fraction(0, 1)) / cap)
    if cap == 2:
        pairs = tuple(
            (configuration[left], configuration[right])
            for left in range(len(configuration))
            for right in range(left + 1, len(configuration))
        )
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                result.append(
                    Fraction(
                        sum(
                            1
                            for left, right in pairs
                            if (left[0], right[0]) == (left_type, right_type)
                        ),
                        1,
                    )
                )
        by_type = {
            event_type: tuple(item for item in projections if item[0] == event_type)
            for event_type in range(len(dimensions))
        }
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left_projection in enumerate(by_type[left_type]):
                    for right_position, right_projection in enumerate(
                        by_type[right_type]
                    ):
                        if left_type == right_type and right_position < left_position:
                            continue
                        total = Fraction(0, 1)
                        for left, right in pairs:
                            if (left[0], right[0]) != (left_type, right_type):
                                continue
                            direct = _odd(
                                _project(
                                    left,
                                    projection_map[(left_type, left_projection[1])],
                                )
                            ) * _odd(
                                _project(
                                    right,
                                    projection_map[(right_type, right_projection[1])],
                                )
                            )
                            if (
                                left_type == right_type
                                and left_projection[1] != right_projection[1]
                            ):
                                reverse = _odd(
                                    _project(
                                        left,
                                        projection_map[
                                            (left_type, right_projection[1])
                                        ],
                                    )
                                ) * _odd(
                                    _project(
                                        right,
                                        projection_map[
                                            (right_type, left_projection[1])
                                        ],
                                    )
                                )
                                direct = (direct + reverse) / 2
                            total += direct
                        result.append(total)
    if len(result) != len(_feature_ids(fixture_id)):
        raise AssertionError("CP70 local feature vector count differs")
    return tuple(result)


def _selected_configuration(row_ordinal: int) -> tuple:
    roster = (
        _M1_SELECTED_CONFIGURATION_ROSTER
        if row_ordinal <= 8
        else _M2_SELECTED_CONFIGURATION_ROSTER
    )
    return roster[_SELECTED_CONFIGURATION_INDEX_BY_ROW[row_ordinal - 1]]


@lru_cache(maxsize=CP70_TEST28_ROW_COUNT)
def _row_feature_items(row_ordinal: int) -> Tuple[Tuple[str, Fraction], ...]:
    fixture_id = _ROW_SHAPES[row_ordinal - 1][0]
    return tuple(
        zip(
            _feature_ids(fixture_id),
            _local_feature_vector(fixture_id, _selected_configuration(row_ordinal)),
        )
    )


def _closed_status(
    seed_ordinal: int, row_ordinal: int
) -> Tuple[str, Optional[int], bool]:
    _fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    selected_count = CP70_TEST28_SELECTED_COUNTS_BY_ROW[row_ordinal - 1]
    if seed_ordinal <= selected_count:
        if strategy == "bounded-rejection":
            return _REJECTION_OBSERVABLE_CELLS[0], (seed_ordinal - 1) % budget + 1, True
        return _SIR_OBSERVABLE_CELLS[0], None, True
    offset = seed_ordinal - selected_count - 1
    if strategy == "bounded-rejection":
        return _REJECTION_OBSERVABLE_CELLS[1 + offset % 4], None, False
    return _SIR_OBSERVABLE_CELLS[1 + offset % 3], None, False


def _observable_contribution_ordinal(row_ordinal: int, cell: str) -> int:
    offset = 0
    for current, (_fixture, strategy, _budget) in enumerate(_ROW_SHAPES, 1):
        cells = (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
        if current == row_ordinal:
            return offset + cells.index(cell) + 1
        offset += len(cells)
    raise AssertionError("CP70 observable row differs")


def _synthetic_custody_sha256(domain: bytes, value: object) -> str:
    return hashlib.sha256(
        domain + b"\0" + _plain_json_bytes(value, CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES)
    ).hexdigest()


def _closed_interchange_body(seed_ordinal: int, row_ordinal: int) -> dict:
    fixture_id, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    status, first_attempt, selected = _closed_status(seed_ordinal, row_ordinal)
    logical = (seed_ordinal - 1) * CP70_TEST28_ROW_COUNT + row_ordinal
    plan_seed_hex = "%016x" % (seed_ordinal - 1)
    seed_free_sha256 = _SEED_FREE_REQUEST_SHA256S[row_ordinal - 1]
    request_sha256 = _synthetic_custody_sha256(
        b"cp69-test28-synthetic-request-instance-custody-sentinel-v1",
        {
            "purpose": "cp69-synthetic-transport-request-custody-sentinel-only",
            "seed_ordinal": seed_ordinal,
            "row_ordinal": row_ordinal,
            "logical_request_ordinal": logical,
            "plan_seed_hex": plan_seed_hex,
            "seed_free_request_sha256": seed_free_sha256,
        },
    )
    stable_sha256 = _synthetic_custody_sha256(
        b"cp69-test28-no-stable-trace-synthetic-custody-sentinel-v1",
        {
            "purpose": "no-stable-trace-present-or-claimed",
            "request_instance_sha256": request_sha256,
            "observable_cell_label": status,
            "first_selected_attempt_one_based": first_attempt,
        },
    )
    feature_items = _row_feature_items(row_ordinal) if selected else ()
    return {
        "schema_version": _CP69_SCHEMA_VERSION,
        "source_semantic_schema_version": _CP63_COMPACT_SCHEMA_VERSION,
        "seed_ordinal": seed_ordinal,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": logical,
        "row_key": _row_key(row_ordinal),
        "fixture_id": fixture_id,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": plan_seed_hex,
        "seed_free_request_sha256": seed_free_sha256,
        "request_instance_sha256": request_sha256,
        "runtime_lock_sha256": _DEVELOPMENT_RUNTIME_LOCK_SHA256,
        "stable_trace_sha256": stable_sha256,
        "observable_cell_label": status,
        "observable_contribution_ordinal": _observable_contribution_ordinal(
            row_ordinal, status
        ),
        "first_selected_attempt_one_based": first_attempt,
        "selected": selected,
        "selected_feature_ids": tuple(item[0] for item in feature_items),
        "selected_feature_values": tuple(item[1] for item in feature_items),
    }


def _closed_interchange_record(seed_ordinal: int, row_ordinal: int) -> dict:
    body = _closed_interchange_body(seed_ordinal, row_ordinal)
    provisional = {**body, "record_sha256": _ZERO_SHA256}
    digest = hashlib.sha256(
        b"cp69-test28-compact-interchange-observation-v1\0"
        + _plain_json_bytes(provisional, CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES)
    ).hexdigest()
    return {**body, "record_sha256": digest}


def _closed_interchange_bytes(seed_ordinal: int, row_ordinal: int) -> bytes:
    return _plain_json_bytes(
        _closed_interchange_record(seed_ordinal, row_ordinal),
        CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES,
    )


def _iter_closed_compact_interchange_bytes() -> Iterator[bytes]:
    for seed_ordinal in range(1, CP70_TEST28_SEED_COUNT + 1):
        for row_ordinal in range(1, CP70_TEST28_ROW_COUNT + 1):
            yield _closed_interchange_bytes(seed_ordinal, row_ordinal)


def _duplicate_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("CP70_INPUT_JSON_INVALID", "JSON contains a duplicate key")
        result[key] = value
    return result


def _parse_bounded_json_integer(text: str) -> int:
    negative = text.startswith("-")
    digits = text[1:] if negative else text
    if not digits or len(digits) > CP70_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "JSON integer text is too large")
    try:
        value = int(text, 10)
    except ValueError as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_INPUT_JSON_INVALID", "JSON integer is invalid"
        ) from exc
    if value.bit_length() > CP70_TEST28_MAXIMUM_INTEGER_BITS:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "JSON integer is too large")
    return value


def _reject_json_float(text: str) -> object:
    del text
    _fail("CP70_INPUT_JSON_INVALID", "JSON floating values are forbidden")
    raise AssertionError("unreachable")


def _precheck_json_nesting(encoded: bytes) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in encoded:
        if in_string:
            if escaped:
                escaped = False
            elif character == 0x5C:
                escaped = True
            elif character == 0x22:
                in_string = False
            continue
        if character == 0x22:
            in_string = True
        elif character in (0x5B, 0x7B):
            depth += 1
            if depth > CP70_TEST28_MAXIMUM_CANONICAL_DEPTH:
                _fail(
                    "CP70_INPUT_RESOURCE_LIMIT",
                    "JSON nesting exceeds the canonical depth limit",
                )
        elif character in (0x5D, 0x7D) and depth:
            depth -= 1


def _walk_decoded(
    value: object, *, depth: int = 1, nodes: Optional[list[int]] = None
) -> None:
    if nodes is None:
        nodes = [0]
    nodes[0] += 1
    if nodes[0] > CP70_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "decoded graph exceeds its node limit")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if cast(int, value).bit_length() > CP70_TEST28_MAXIMUM_INTEGER_BITS:
            _fail("CP70_INPUT_RESOURCE_LIMIT", "decoded integer is too large")
        return
    if type(value) is str:
        if len(cast(str, value)) > CP70_TEST28_MAXIMUM_TEXT_CHARACTERS:
            _fail("CP70_INPUT_RESOURCE_LIMIT", "decoded text is too large")
        return
    if depth > CP70_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP70_INPUT_RESOURCE_LIMIT", "decoded graph exceeds its depth limit")
    if type(value) is list:
        for item in cast(list, value):
            _walk_decoded(item, depth=depth + 1, nodes=nodes)
        return
    if type(value) is dict:
        for key, item in cast(dict, value).items():
            if type(key) is not str:
                _fail("CP70_INPUT_FIELD_TYPE_MISMATCH", "decoded key type differs")
            if len(key) > CP70_TEST28_MAXIMUM_KEY_CHARACTERS:
                _fail("CP70_INPUT_RESOURCE_LIMIT", "decoded key is too large")
            _walk_decoded(item, depth=depth + 1, nodes=nodes)
        return
    _fail("CP70_INPUT_FIELD_TYPE_MISMATCH", "decoded value type differs")


def _decoded_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (OverflowError, RecursionError, TypeError, ValueError) as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_INPUT_RESOURCE_LIMIT", "decoded JSON cannot be canonicalized"
        ) from exc


def _decode_canonical_bytes(
    payload: object, maximum: int = CP70_TEST28_MAXIMUM_OUTPUT_BYTES
) -> dict:
    if type(payload) is not bytes:
        _fail("CP70_INPUT_TYPE_MISMATCH", "payload must be exact bytes")
    encoded = cast(bytes, payload)
    if not encoded or len(encoded) > maximum:
        _fail("CP70_INPUT_BYTE_LIMIT", "payload byte length is outside its bound")
    if encoded.startswith(b"\xef\xbb\xbf"):
        _fail("CP70_INPUT_ENCODING_INVALID", "payload has a BOM")
    try:
        text = encoded.decode("ascii")
    except UnicodeDecodeError as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_INPUT_ENCODING_INVALID", "payload is not ASCII"
        ) from exc
    _precheck_json_nesting(encoded)
    try:
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_pairs,
            parse_int=_parse_bounded_json_integer,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_float,
        )
    except CP70EstimateIntervalOutputValidationQualificationError:
        raise
    except RecursionError as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_INPUT_RESOURCE_LIMIT", "JSON decoding exceeded its recursion bound"
        ) from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_INPUT_JSON_INVALID", "payload JSON is invalid"
        ) from exc
    _walk_decoded(value)
    if type(value) is not dict:
        _fail("CP70_INPUT_FIELD_TYPE_MISMATCH", "payload root is not an object")
    if not hmac.compare_digest(_decoded_json_bytes(value), encoded):
        _fail("CP70_INPUT_CANONICAL_MISMATCH", "payload is not canonical JSON")
    return cast(dict, value)


def _fraction_from_tag(value: object) -> Fraction:
    if type(value) is not dict or tuple(cast(dict, value)) != ("$fraction",):
        _fail("CP70_INPUT_FRACTION_MISMATCH", "fraction tag shape differs")
    pair = cast(dict, value)["$fraction"]
    if type(pair) is not list or len(cast(list, pair)) != 2:
        _fail("CP70_INPUT_FRACTION_MISMATCH", "fraction component pair differs")
    integers = []
    for index, component in enumerate(cast(list, pair)):
        if type(component) is not str or not component:
            _fail("CP70_INPUT_FRACTION_MISMATCH", "fraction component type differs")
        supplied = cast(str, component)
        negative = supplied.startswith("-")
        digits = supplied[1:] if negative else supplied
        if len(digits) > CP70_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS:
            _fail(
                "CP70_INPUT_RESOURCE_LIMIT",
                "fraction component decimal text is too large",
            )
        if (
            not digits
            or any(character not in "0123456789" for character in digits)
            or (len(digits) > 1 and digits.startswith("0"))
            or (negative and digits == "0")
            or supplied.startswith("+")
        ):
            _fail("CP70_INPUT_FRACTION_MISMATCH", "fraction component is noncanonical")
        number = int(supplied, 10)
        if number.bit_length() > CP70_TEST28_MAXIMUM_INTEGER_BITS:
            _fail("CP70_INPUT_RESOURCE_LIMIT", "fraction component is too large")
        if index == 1 and number <= 0:
            _fail(
                "CP70_INPUT_FRACTION_MISMATCH", "fraction denominator is not positive"
            )
        integers.append(number)
    fraction = Fraction(integers[0], integers[1])
    if (fraction.numerator, fraction.denominator) != tuple(integers):
        _fail("CP70_INPUT_FRACTION_MISMATCH", "fraction is not reduced")
    return fraction


def _parse_closed_interchange(payload: object, logical_ordinal: int) -> dict:
    seed_ordinal = (logical_ordinal - 1) // CP70_TEST28_ROW_COUNT + 1
    row_ordinal = (logical_ordinal - 1) % CP70_TEST28_ROW_COUNT + 1
    expected_payload = _closed_interchange_bytes(seed_ordinal, row_ordinal)
    value = _decode_canonical_bytes(payload, CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES)
    if tuple(sorted(value)) != tuple(sorted(_INTERCHANGE_KEYS)):
        _fail("CP70_STREAM_CONTENT_MISMATCH", "interchange field set differs")
    if not hmac.compare_digest(cast(bytes, payload), expected_payload):
        _fail(
            "CP70_STREAM_CONTENT_MISMATCH",
            "interchange record differs from the closed fixture",
        )
    del expected_payload
    value["selected_feature_ids"] = tuple(value["selected_feature_ids"])
    value["selected_feature_values"] = tuple(
        _fraction_from_tag(item) for item in value["selected_feature_values"]
    )
    return value


def _projection_sha256(observation: Mapping[str, object]) -> str:
    body = {
        name: observation[name]
        for name in (
            "schema_version",
            "seed_ordinal",
            "row_ordinal",
            "logical_request_ordinal",
            "row_key",
            "fixture_id",
            "strategy",
            "budget",
            "plan_seed_hex",
            "observable_cell_label",
            "first_selected_attempt_one_based",
            "selected",
            "selected_feature_ids",
            "selected_feature_values",
        )
    }
    body["schema_version"] = _CP68_SCHEMA_VERSION
    return hashlib.sha256(
        b"cp68-test28-synthetic-compact-projection-v1\0"
        + _plain_json_bytes(body, CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES)
    ).hexdigest()


def _reduce_closed_compact_interchange_stream_details(payloads: object = None) -> dict:
    source = _iter_closed_compact_interchange_bytes() if payloads is None else payloads
    try:
        iterator = iter(source)
    except MemoryError:
        raise
    except Exception as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_STREAM_ITERABLE_INVALID", "private interchange source is not iterable"
        ) from exc
    observable_counts = {
        (row, cell): 0
        for row, (_fixture, strategy, _budget) in enumerate(_ROW_SHAPES, 1)
        for cell in (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
    }
    first_attempt_counts = {
        (row, attempt): 0
        for row, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1)
        if strategy == "bounded-rejection"
        for attempt in range(1, budget + 1)
    }
    feature_sums = {
        (row, feature_id): Fraction(0, 1)
        for row, (fixture, _strategy, _budget) in enumerate(_ROW_SHAPES, 1)
        for feature_id in _feature_ids(fixture)
    }
    selected_counts = [0] * CP70_TEST28_ROW_COUNT
    status_counts = {
        name: 0
        for name in (
            "rejection-selected",
            "rejection-exhausted",
            "sir-selected",
            "refusal",
            "failure",
            "timeout",
        )
    }
    ordered_input = hashlib.sha256(
        b"cp69-test28-ordered-interchange-record-digests-v1\0"
    )
    ordered_projection = hashlib.sha256(b"cp68-test28-ordered-projection-digests-v1\0")
    first_record_sha256 = None
    total_input_bytes = 0
    first_attempt_contribution_count = 0
    feature_contribution_count = 0
    for logical_ordinal in range(1, CP70_TEST28_REQUEST_COUNT + 1):
        try:
            payload = next(iterator)
        except StopIteration as exc:
            raise CP70EstimateIntervalOutputValidationQualificationError(
                "CP70_STREAM_COUNT_MISMATCH", "interchange stream ended early"
            ) from exc
        except MemoryError:
            raise
        except Exception as exc:
            raise CP70EstimateIntervalOutputValidationQualificationError(
                "CP70_STREAM_ITERATION_FAILED", "interchange iterator failed"
            ) from exc
        if type(payload) is bytes:
            total_input_bytes += len(payload)
            if total_input_bytes > CP70_TEST28_MAXIMUM_STREAM_BYTES:
                _fail(
                    "CP70_STREAM_RESOURCE_LIMIT", "cumulative stream byte cap exceeded"
                )
        observation = _parse_closed_interchange(payload, logical_ordinal)
        row = cast(int, observation["row_ordinal"])
        status = cast(str, observation["observable_cell_label"])
        observable_counts[(row, status)] += 1
        record_sha256 = cast(str, observation["record_sha256"])
        if first_record_sha256 is None:
            first_record_sha256 = record_sha256
        ordered_input.update(bytes.fromhex(record_sha256))
        ordered_projection.update(bytes.fromhex(_projection_sha256(observation)))
        selected = cast(bool, observation["selected"])
        if status == _REJECTION_OBSERVABLE_CELLS[0]:
            status_counts["rejection-selected"] += 1
        elif status == _REJECTION_OBSERVABLE_CELLS[1]:
            status_counts["rejection-exhausted"] += 1
        elif status == _SIR_OBSERVABLE_CELLS[0]:
            status_counts["sir-selected"] += 1
        elif status == "preexecution-refusal-before-deadline":
            status_counts["refusal"] += 1
        elif status == "execution-failure-before-deadline":
            status_counts["failure"] += 1
        elif status == "timeout-censored-at-deadline":
            status_counts["timeout"] += 1
        first = observation["first_selected_attempt_one_based"]
        if first is not None:
            first_attempt_counts[(row, cast(int, first))] += 1
            first_attempt_contribution_count += 1
        if selected:
            selected_counts[row - 1] += 1
            for feature_id, value in zip(
                cast(tuple, observation["selected_feature_ids"]),
                cast(tuple, observation["selected_feature_values"]),
            ):
                feature_sums[(row, feature_id)] += value
                feature_contribution_count += 1
        del payload, observation
    sentinel = object()
    try:
        extra = next(iterator)
    except StopIteration:
        extra = sentinel
    except MemoryError:
        raise
    except Exception as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_STREAM_ITERATION_FAILED",
            "interchange iterator failed at terminal boundary",
        ) from exc
    if extra is not sentinel:
        _fail("CP70_STREAM_COUNT_MISMATCH", "interchange stream has extra items")
    selected_tuple = tuple(selected_counts)
    metrics = {
        "request_count": CP70_TEST28_REQUEST_COUNT,
        "total_input_bytes": total_input_bytes,
        "first_interchange_record_sha256": cast(str, first_record_sha256),
        "ordered_interchange_record_sha256": ordered_input.hexdigest(),
        "ordered_target_projection_sha256": ordered_projection.hexdigest(),
        "selected_counts_by_row": selected_tuple,
        "status_counts": status_counts,
        "observable_counts": observable_counts,
        "first_attempt_counts": first_attempt_counts,
        "feature_sums": feature_sums,
        "first_attempt_contribution_count": first_attempt_contribution_count,
        "feature_contribution_count": feature_contribution_count,
        "aggregation_update_count": (
            CP70_TEST28_REQUEST_COUNT
            + first_attempt_contribution_count
            + feature_contribution_count
        ),
        "logical_ordinals_complete": True,
    }
    if not (
        total_input_bytes == _CP69_TOTAL_INPUT_BYTES
        and metrics["first_interchange_record_sha256"]
        == _CP69_FIRST_INTERCHANGE_RECORD_SHA256
        and metrics["ordered_interchange_record_sha256"]
        == _CP69_ORDERED_INTERCHANGE_RECORD_SHA256
        and metrics["ordered_target_projection_sha256"]
        == _CP68_ORDERED_PROJECTION_SHA256
        and selected_tuple == CP70_TEST28_SELECTED_COUNTS_BY_ROW
        and status_counts
        == {
            "rejection-selected": 8_254,
            "rejection-exhausted": 2_034,
            "sir-selected": 8_254,
            "refusal": 4_744,
            "failure": 4_742,
            "timeout": 4_740,
        }
        and first_attempt_contribution_count == 8_254
        and feature_contribution_count == 321_906
        and metrics["aggregation_update_count"] == 362_928
    ):
        _fail(
            "CP70_STREAM_CONTENT_MISMATCH",
            "reduced stream differs from its frozen expectation",
        )
    return metrics


_CP_INTERVALS = {
    0: (
        Fraction(0, 1),
        Fraction(
            20464691515764649513018636251773637059592368629132599509687576631530823105,
            3618502788666131106986593281521497120414687020801267626233049500247285301248,
        ),
    ),
    32: (
        Fraction(
            752536336496513183990788286318918463810583453450923277968002067369920229537,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            3569508234670329659873892260174800751442095229535608301424817620493493905749,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
    ),
    64: (
        Fraction(
            2009509374422176809837317565319218415654406645098498369659263517844992218853,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            5905034437517541267160652628981187635910893838058893852041520260350457098045,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
    ),
    65: (
        Fraction(
            2051471098007702678504865861231195500362838708276848877476999165402502335195,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            5975375592268707023091684419158635128855875889666561315342692867498654125127,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
    ),
    252: (
        Fraction(
            2722406052730280682020228204488013472054617007796231797186745752483578754201,
            28948022309329048855892746252171976963317496166410141009864396001978282409984,
        ),
        Fraction(
            9073475907670962337112305522954694818199721749276858943754567497916694525237,
            57896044618658097711785492504343953926634992332820282019728792003956564819968,
        ),
    ),
    253: (
        Fraction(
            2734926937631630058601594709653673479810386713596176366295433449131956342677,
            28948022309329048855892746252171976963317496166410141009864396001978282409984,
        ),
        Fraction(
            18209237372477057754144842710380995678752184283984923274300601083029273215277,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
    ),
    259: (
        Fraction(
            11240588565483359038468713397296979094116923829973891854217132053013525781539,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            4645643161608749594763265937621229674037077248921315818863215086203253698953,
            28948022309329048855892746252171976963317496166410141009864396001978282409984,
        ),
    ),
    260: (
        Fraction(
            11290797792107863355689784267278003380565710967656687335443964255036012048525,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            9322366506680859494273147992066486053928463055893300538019729532082287844887,
            57896044618658097711785492504343953926634992332820282019728792003956564819968,
        ),
    ),
    336: (
        Fraction(
            15152825378904835621659738969943760597104131806284413362979988022745846390637,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            5830739644636787076018831759733189976139610267159053105299559649724447237407,
            28948022309329048855892746252171976963317496166410141009864396001978282409984,
        ),
    ),
    337: (
        Fraction(
            1900523223193844844339730636145241127806508567703089486597993967323518750553,
            14474011154664524427946373126085988481658748083205070504932198000989141204992,
        ),
        Fraction(
            5845992920131146027783860662007687190717676221548654503374669432330455900647,
            28948022309329048855892746252171976963317496166410141009864396001978282409984,
        ),
    ),
    512: (
        Fraction(
            24357805534306805728470528148968597122570568432680876118757730583487996182815,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            16948062050976301354950355318691723828645860749697907484163846709009859943665,
            57896044618658097711785492504343953926634992332820282019728792003956564819968,
        ),
    ),
    682: (
        Fraction(
            33492061434637936868314944478390144787405190519440997844184220520738535449563,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            43866189978860143192065985032909228034522786628619705916134825717913871992325,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
    ),
    683: (
        Fraction(
            33546364891778499841789201734423104184989085746762926824092465191556033366467,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            2745266597510374118590539814321893442327192333207244180339150707411457761865,
            7237005577332262213973186563042994240829374041602535252466099000494570602496,
        ),
    ),
    1039: (
        Fraction(
            53238894354462439822717023325897356710743016939985309337839593724111419183203,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            8029861712584800141452192734155713974510441149759757280764743191060747065613,
            14474011154664524427946373126085988481658748083205070504932198000989141204992,
        ),
    ),
    1040: (
        Fraction(
            53295165038789432261127804232177998379899333806836211076631576866753783819815,
            115792089237316195423570985008687907853269984665640564039457584007913129639936,
        ),
        Fraction(
            32147501468225968662827383984401590680419186907476874903943402552074488406647,
            57896044618658097711785492504343953926634992332820282019728792003956564819968,
        ),
    ),
    2048: (
        Fraction(
            3598038097150366457473574645269723483355094652172135026723361923615754478143,
            3618502788666131106986593281521497120414687020801267626233049500247285301248,
        ),
        Fraction(1, 1),
    ),
}


def _cp61_estimand_sha256(ordinal: int) -> str:
    start = (ordinal - 1) * 64
    return _CP61_ESTIMAND_RECORD_SHA256_HEX[start : start + 64]


def _iter_estimand_specs() -> Iterator[dict]:
    ordinal = 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        cells = (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
        for cell in cells:
            yield {
                "estimand_ordinal": ordinal,
                "estimand_id": "cp61/observable/%s/%s" % (_row_key(row), cell),
                "cp61_estimand_record_sha256": _cp61_estimand_sha256(ordinal),
                "estimand_family": "observable-cell",
                "row_ordinal": row,
                "fixture_id": fixture,
                "strategy": strategy,
                "budget": budget,
                "observable_cell_label": cell,
                "first_attempt_one_based": None,
                "feature_id": None,
                "feature_lower_bound": None,
                "feature_upper_bound": None,
                "denominator_mode": "all-2048-external-seed-ordinals",
            }
            ordinal += 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        if strategy != "bounded-rejection":
            continue
        for attempt in range(1, budget + 1):
            yield {
                "estimand_ordinal": ordinal,
                "estimand_id": "cp61/rejection-first-attempt/%s/attempt-%d"
                % (_row_key(row), attempt),
                "cp61_estimand_record_sha256": _cp61_estimand_sha256(ordinal),
                "estimand_family": "rejection-first-attempt",
                "row_ordinal": row,
                "fixture_id": fixture,
                "strategy": strategy,
                "budget": budget,
                "observable_cell_label": None,
                "first_attempt_one_based": attempt,
                "feature_id": None,
                "feature_lower_bound": None,
                "feature_upper_bound": None,
                "denominator_mode": "all-2048-external-seed-ordinals",
            }
            ordinal += 1
    for row, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        for feature_id in _feature_ids(fixture):
            lower, upper = _feature_bounds(feature_id)
            yield {
                "estimand_ordinal": ordinal,
                "estimand_id": "cp61/selected-feature/%s/%s"
                % (_row_key(row), feature_id),
                "cp61_estimand_record_sha256": _cp61_estimand_sha256(ordinal),
                "estimand_family": "selected-conditional-feature",
                "row_ordinal": row,
                "fixture_id": fixture,
                "strategy": strategy,
                "budget": budget,
                "observable_cell_label": None,
                "first_attempt_one_based": None,
                "feature_id": feature_id,
                "feature_lower_bound": lower,
                "feature_upper_bound": upper,
                "denominator_mode": "predeadline-selected-count-in-this-row",
            }
            ordinal += 1
    if ordinal != CP70_TEST28_ESTIMAND_COUNT + 1:
        raise AssertionError("CP70 estimand inventory count differs")


def _closed_statistics_without_stream() -> dict:
    observable_counts = {
        (row, cell): 0
        for row, (_fixture, strategy, _budget) in enumerate(_ROW_SHAPES, 1)
        for cell in (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
    }
    first_attempt_counts = {
        (row, attempt): 0
        for row, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1)
        if strategy == "bounded-rejection"
        for attempt in range(1, budget + 1)
    }
    feature_sums = {
        (row, feature): Fraction(0, 1)
        for row, (fixture, _strategy, _budget) in enumerate(_ROW_SHAPES, 1)
        for feature in _feature_ids(fixture)
    }
    for seed in range(1, CP70_TEST28_SEED_COUNT + 1):
        for row in range(1, CP70_TEST28_ROW_COUNT + 1):
            status, first, selected = _closed_status(seed, row)
            observable_counts[(row, status)] += 1
            if first is not None:
                first_attempt_counts[(row, first)] += 1
            if selected:
                for feature, value in _row_feature_items(row):
                    feature_sums[(row, feature)] += value
    return {
        "observable_counts": observable_counts,
        "first_attempt_counts": first_attempt_counts,
        "feature_sums": feature_sums,
        "selected_counts_by_row": CP70_TEST28_SELECTED_COUNTS_BY_ROW,
    }


def _build_estimand_record(
    spec: Mapping[str, object], metrics: Mapping[str, object]
) -> dict:
    family = cast(str, spec["estimand_family"])
    row = cast(int, spec["row_ordinal"])
    if family == "observable-cell":
        success = cast(Mapping[tuple, int], metrics["observable_counts"])[
            (row, spec["observable_cell_label"])
        ]
        denominator = CP70_TEST28_SEED_COUNT
        exact_sum = None
        estimate = Fraction(success, denominator)
        lower, upper = _CP_INTERVALS[success]
        method = "clopper-pearson-exact-rational-certified-equivalent-outward-endpoint-on-2^-256-grid-n2048"
        state = "computed"
    elif family == "rejection-first-attempt":
        success = cast(Mapping[tuple, int], metrics["first_attempt_counts"])[
            (row, spec["first_attempt_one_based"])
        ]
        denominator = CP70_TEST28_SEED_COUNT
        exact_sum = None
        estimate = Fraction(success, denominator)
        lower, upper = _CP_INTERVALS[success]
        method = "clopper-pearson-exact-rational-certified-equivalent-outward-endpoint-on-2^-256-grid-n2048"
        state = "computed"
    else:
        success = None
        denominator = cast(Tuple[int, ...], metrics["selected_counts_by_row"])[row - 1]
        total = cast(Mapping[tuple, Fraction], metrics["feature_sums"])[
            (row, spec["feature_id"])
        ]
        exact_sum = total if denominator else None
        estimate = total / denominator if denominator else None
        method = "bounded-feature-fixed-range-halfwidth-clipped-to-bounds"
        if estimate is None or denominator < 1_040:
            lower = upper = None
            state = "insufficient-selection"
        else:
            feature_lower = cast(Fraction, spec["feature_lower_bound"])
            feature_upper = cast(Fraction, spec["feature_upper_bound"])
            halfwidth = (feature_upper - feature_lower) * Fraction(3, 40)
            lower = max(feature_lower, estimate - halfwidth)
            upper = min(feature_upper, estimate + halfwidth)
            state = "computed"
    body = {
        "schema_version": _CP68_SCHEMA_VERSION,
        **dict(spec),
        "denominator_count": denominator,
        "success_count": success,
        "exact_feature_sum": exact_sum,
        "estimate": estimate,
        "interval_method": method,
        "interval_state": state,
        "interval_lower": lower,
        "interval_upper": upper,
        "development_fixture_only": True,
        "record_sha256": _ZERO_SHA256,
    }
    body["record_sha256"] = hashlib.sha256(
        b"cp68-test28-estimand-estimate-interval-v1\0" + _plain_json_bytes(body, 4_096)
    ).hexdigest()
    return body


def _build_estimate_interval_output_bytes(
    metrics: Mapping[str, object]
) -> Tuple[bytes, dict]:
    records = tuple(
        _build_estimand_record(spec, metrics) for spec in _iter_estimand_specs()
    )
    if len(records) != CP70_TEST28_ESTIMAND_COUNT:
        _fail("CP70_INPUT_INVENTORY_MISMATCH", "output record count differs")
    ordered = hashlib.sha256(
        b"cp68-test28-ordered-estimand-record-digests-v1\0"
        + b"".join(bytes.fromhex(item["record_sha256"]) for item in records)
    ).hexdigest()
    body = {
        "schema_version": _CP68_SCHEMA_VERSION,
        "fixture_set_sha256": _CP68_FIXTURE_SET_SHA256,
        "request_count": CP70_TEST28_REQUEST_COUNT,
        "estimand_count": CP70_TEST28_ESTIMAND_COUNT,
        "estimand_estimate_intervals": records,
    }
    payload = _plain_json_bytes(body, CP70_TEST28_MAXIMUM_OUTPUT_BYTES)
    details = {
        "records": records,
        "ordered_estimand_record_sha256s_sha256": ordered,
        "output_body_sha256": hashlib.sha256(
            b"cp68-test28-estimate-interval-output-body-v1\0" + payload
        ).hexdigest(),
        "output_canonical_json_bytes": len(payload),
        "output_canonical_json_sha256": hashlib.sha256(payload).hexdigest(),
    }
    return payload, details


_CLOSED_OUTPUT_LOCK = threading.RLock()
_CLOSED_OUTPUT_CACHE: Optional[Tuple[bytes, dict]] = None


def _closed_expected_output() -> Tuple[bytes, dict]:
    global _CLOSED_OUTPUT_CACHE
    with _CLOSED_OUTPUT_LOCK:
        if _CLOSED_OUTPUT_CACHE is None:
            payload, details = _build_estimate_interval_output_bytes(
                _closed_statistics_without_stream()
            )
            if not (
                len(payload) == _CP68_OUTPUT_CANONICAL_JSON_BYTES
                and details["ordered_estimand_record_sha256s_sha256"]
                == _CP68_ORDERED_ESTIMAND_RECORD_SHA256S_SHA256
                and details["output_body_sha256"] == _CP68_OUTPUT_BODY_SHA256
                and details["output_canonical_json_sha256"]
                == _CP68_OUTPUT_CANONICAL_JSON_SHA256
            ):
                raise AssertionError("CP70 closed output construction differs")
            scalar_summary = {
                "ordered_estimand_record_sha256s_sha256": details[
                    "ordered_estimand_record_sha256s_sha256"
                ],
                "output_body_sha256": details["output_body_sha256"],
                "output_canonical_json_bytes": details["output_canonical_json_bytes"],
                "output_canonical_json_sha256": details["output_canonical_json_sha256"],
            }
            del details
            _CLOSED_OUTPUT_CACHE = (payload, scalar_summary)
        return _CLOSED_OUTPUT_CACHE


def _validate_output_value(value: dict, payload: bytes) -> dict:
    if tuple(sorted(value)) != tuple(sorted(_OUTPUT_ROOT_KEYS)):
        _fail("CP70_INPUT_FIELD_SET_MISMATCH", "output root field set differs")
    if (
        value.get("schema_version") != _CP68_SCHEMA_VERSION
        or value.get("fixture_set_sha256") != _CP68_FIXTURE_SET_SHA256
    ):
        _fail("CP70_INPUT_SCHEMA_MISMATCH", "output schema or fixture differs")
    if (
        type(value.get("request_count")) is not int
        or type(value.get("estimand_count")) is not int
    ):
        _fail("CP70_INPUT_FIELD_TYPE_MISMATCH", "output count type differs")
    if (
        value["request_count"] != CP70_TEST28_REQUEST_COUNT
        or value["estimand_count"] != CP70_TEST28_ESTIMAND_COUNT
    ):
        _fail("CP70_INPUT_INVENTORY_MISMATCH", "output count differs")
    records = value.get("estimand_estimate_intervals")
    if (
        type(records) is not list
        or len(cast(list, records)) != CP70_TEST28_ESTIMAND_COUNT
    ):
        _fail("CP70_INPUT_INVENTORY_MISMATCH", "estimand record vector differs")
    ordered = hashlib.sha256(b"cp68-test28-ordered-estimand-record-digests-v1\0")
    family_counts = {
        "observable-cell": 0,
        "rejection-first-attempt": 0,
        "selected-conditional-feature": 0,
    }
    state_counts = {"computed": 0, "insufficient-selection": 0}
    selected_denominators = [None] * CP70_TEST28_ROW_COUNT
    for ordinal, record in enumerate(cast(list, records), 1):
        if type(record) is not dict or tuple(sorted(record)) != tuple(
            sorted(_OUTPUT_ESTIMAND_KEYS)
        ):
            _fail("CP70_INPUT_FIELD_SET_MISMATCH", "estimand field set differs")
        checked = cast(dict, record)
        if (
            type(checked.get("estimand_ordinal")) is not int
            or checked["estimand_ordinal"] != ordinal
        ):
            _fail("CP70_INPUT_INVENTORY_MISMATCH", "estimand order differs")
        family = checked.get("estimand_family")
        if type(family) is not str or family not in family_counts:
            _fail("CP70_INPUT_FAMILY_MISMATCH", "estimand family differs")
        family_counts[cast(str, family)] += 1
        state = checked.get("interval_state")
        if type(state) is not str or state not in state_counts:
            _fail("CP70_INPUT_INTERVAL_MISMATCH", "interval state differs")
        state_counts[cast(str, state)] += 1
        for name in (
            "feature_lower_bound",
            "feature_upper_bound",
            "exact_feature_sum",
            "estimate",
            "interval_lower",
            "interval_upper",
        ):
            component = checked[name]
            if component is not None:
                _fraction_from_tag(component)
        supplied_digest = checked.get("record_sha256")
        if (
            type(supplied_digest) is not str
            or len(cast(str, supplied_digest)) != 64
            or any(
                character not in "0123456789abcdef"
                for character in cast(str, supplied_digest)
            )
        ):
            _fail("CP70_INPUT_DIGEST_MISMATCH", "estimand record digest type differs")
        digest_body = dict(checked)
        digest_body["record_sha256"] = _ZERO_SHA256
        wanted_digest = hashlib.sha256(
            b"cp68-test28-estimand-estimate-interval-v1\0"
            + _decoded_json_bytes(digest_body)
        ).hexdigest()
        if not hmac.compare_digest(cast(str, supplied_digest), wanted_digest):
            _fail("CP70_INPUT_DIGEST_MISMATCH", "estimand record digest differs")
        ordered.update(bytes.fromhex(cast(str, supplied_digest)))
        if family == "selected-conditional-feature":
            row = checked.get("row_ordinal")
            denominator = checked.get("denominator_count")
            if (
                type(row) is int
                and 1 <= cast(int, row) <= CP70_TEST28_ROW_COUNT
                and type(denominator) is int
            ):
                previous = selected_denominators[cast(int, row) - 1]
                if previous is not None and previous != denominator:
                    _fail(
                        "CP70_INPUT_ARITHMETIC_MISMATCH",
                        "feature denominators disagree",
                    )
                selected_denominators[cast(int, row) - 1] = denominator
    if family_counts != {
        "observable-cell": CP70_TEST28_OBSERVABLE_ESTIMAND_COUNT,
        "rejection-first-attempt": CP70_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
        "selected-conditional-feature": CP70_TEST28_FEATURE_ESTIMAND_COUNT,
    }:
        _fail("CP70_INPUT_FAMILY_MISMATCH", "estimand family counts differ")
    if state_counts != {
        "computed": CP70_TEST28_COMPUTED_INTERVAL_COUNT,
        "insufficient-selection": CP70_TEST28_INSUFFICIENT_SELECTION_COUNT,
    }:
        _fail("CP70_INPUT_INTERVAL_MISMATCH", "interval state counts differ")
    if tuple(selected_denominators) != CP70_TEST28_SELECTED_COUNTS_BY_ROW:
        _fail("CP70_INPUT_ARITHMETIC_MISMATCH", "selected denominators differ")
    ordered_digest = ordered.hexdigest()
    body_digest = hashlib.sha256(
        b"cp68-test28-estimate-interval-output-body-v1\0" + payload
    ).hexdigest()
    payload_digest = hashlib.sha256(payload).hexdigest()
    if not (
        ordered_digest == _CP68_ORDERED_ESTIMAND_RECORD_SHA256S_SHA256
        and body_digest == _CP68_OUTPUT_BODY_SHA256
        and len(payload) == _CP68_OUTPUT_CANONICAL_JSON_BYTES
        and payload_digest == _CP68_OUTPUT_CANONICAL_JSON_SHA256
    ):
        _fail(
            "CP70_INPUT_FIXTURE_MISMATCH",
            "output body differs from its exact frozen bytes",
        )
    expected_payload, expected_details = _closed_expected_output()
    if not (
        hmac.compare_digest(payload, expected_payload)
        and expected_details["ordered_estimand_record_sha256s_sha256"] == ordered_digest
        and expected_details["output_body_sha256"] == body_digest
        and expected_details["output_canonical_json_bytes"] == len(payload)
        and expected_details["output_canonical_json_sha256"] == payload_digest
    ):
        _fail(
            "CP70_INPUT_FIXTURE_MISMATCH",
            "output body differs from its exact frozen fixture",
        )
    return {
        "ordered_estimand_record_sha256s_sha256": ordered_digest,
        "output_body_sha256": body_digest,
        "output_canonical_json_bytes": len(payload),
        "output_canonical_json_sha256": payload_digest,
    }


def cp70_validate_closed_cp68_estimate_interval_output_bytes(
    payload: object,
) -> CP70EstimateIntervalOutputValidationV1:
    """Validate only the exact bounded canonical CP68 development output body."""

    try:
        value = _decode_canonical_bytes(payload)
        details = _validate_output_value(value, cast(bytes, payload))
        return cast(
            CP70EstimateIntervalOutputValidationV1,
            _record(
                CP70EstimateIntervalOutputValidationV1,
                {
                    "schema_version": CP70_TEST28_SCHEMA_VERSION,
                    "source_output_schema_version": _CP68_SCHEMA_VERSION,
                    "fixture_set_sha256": _CP68_FIXTURE_SET_SHA256,
                    "request_count": CP70_TEST28_REQUEST_COUNT,
                    "estimand_count": CP70_TEST28_ESTIMAND_COUNT,
                    "observable_estimand_count": CP70_TEST28_OBSERVABLE_ESTIMAND_COUNT,
                    "rejection_first_attempt_estimand_count": CP70_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
                    "feature_estimand_count": CP70_TEST28_FEATURE_ESTIMAND_COUNT,
                    "binomial_interval_count": CP70_TEST28_BINOMIAL_ESTIMAND_COUNT,
                    "feature_interval_count": 156,
                    "insufficient_selection_count": CP70_TEST28_INSUFFICIENT_SELECTION_COUNT,
                    "computed_interval_count": CP70_TEST28_COMPUTED_INTERVAL_COUNT,
                    "selected_counts_by_row": CP70_TEST28_SELECTED_COUNTS_BY_ROW,
                    "ordered_estimand_record_sha256s_sha256": details[
                        "ordered_estimand_record_sha256s_sha256"
                    ],
                    "output_body_sha256": details["output_body_sha256"],
                    "output_canonical_json_bytes": details[
                        "output_canonical_json_bytes"
                    ],
                    "output_canonical_json_sha256": details[
                        "output_canonical_json_sha256"
                    ],
                    "canonical_bytes_verified": True,
                    "record_digests_verified": True,
                    "estimand_inventory_verified": True,
                    "family_union_verified": True,
                    "cross_record_invariants_verified": True,
                    "exact_arithmetic_verified": True,
                    "cp_endpoint_table_match_verified": True,
                    "feature_threshold_and_clipping_verified": True,
                    "closed_fixture_match": True,
                    "development_fixture_only": True,
                    "production_evidence": False,
                    "decision_path_qualified": False,
                },
            ),
        )
    except CP70EstimateIntervalOutputValidationQualificationError:
        raise
    except MemoryError as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_RESOURCE_EXHAUSTED", "bounded output validation exhausted memory"
        ) from exc
    except Exception as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_INPUT_JSON_INVALID", "bounded output validation failed closed"
        ) from exc


_CP_DENOMINATOR = 1 << 256
_CP_TAIL_RECIPROCAL = 110_800
_CP_COMMON_DENOMINATOR_POWER = 1 << (256 * CP70_TEST28_SEED_COUNT)


def _upper_tail_compare(success_count: int, probability_numerator: int) -> int:
    n = CP70_TEST28_SEED_COUNT
    k = success_count
    a = probability_numerator
    if k <= 0:
        return 1
    if k > n or a == 0:
        return -1
    if a == _CP_DENOMINATOR:
        return 1
    complement = _CP_DENOMINATOR - a
    term = comb(n, k) * a**k * complement ** (n - k)
    partial = term
    index = k
    while True:
        left = partial * _CP_TAIL_RECIPROCAL
        if left > _CP_COMMON_DENOMINATOR_POWER:
            return 1
        if index == n:
            return (left > _CP_COMMON_DENOMINATOR_POWER) - (
                left < _CP_COMMON_DENOMINATOR_POWER
            )
        ratio_numerator = (n - index) * a
        ratio_denominator = (index + 1) * complement
        if ratio_numerator < ratio_denominator:
            gap = ratio_denominator - ratio_numerator
            bounded_left = (
                partial * gap + term * ratio_numerator
            ) * _CP_TAIL_RECIPROCAL
            if bounded_left < _CP_COMMON_DENOMINATOR_POWER * gap:
                return -1
        term, remainder = divmod(term * ratio_numerator, ratio_denominator)
        if remainder:
            raise AssertionError("CP70 exact binomial recurrence differs")
        partial += term
        index += 1


@lru_cache(maxsize=1)
def _certify_cp_endpoint_table() -> bool:
    comparisons = 0
    for success, (lower, upper) in sorted(_CP_INTERVALS.items()):
        if _CP_DENOMINATOR % lower.denominator or _CP_DENOMINATOR % upper.denominator:
            return False
        if success:
            numerator = lower.numerator * (_CP_DENOMINATOR // lower.denominator)
            if not (
                _upper_tail_compare(success, numerator) < 0
                and _upper_tail_compare(success, numerator + 1) >= 0
            ):
                return False
            comparisons += 2
        elif lower != 0:
            return False
        if success < CP70_TEST28_SEED_COUNT:
            upper_numerator = upper.numerator * (_CP_DENOMINATOR // upper.denominator)
            complement_numerator = _CP_DENOMINATOR - upper_numerator
            complement_success = CP70_TEST28_SEED_COUNT - success
            if not (
                _upper_tail_compare(complement_success, complement_numerator) < 0
                and _upper_tail_compare(complement_success, complement_numerator + 1)
                >= 0
            ):
                return False
            comparisons += 2
        elif upper != 1:
            return False
    return comparisons == 60


def _predecessor_custody() -> CP70PredecessorCustodyV1:
    return cast(
        CP70PredecessorCustodyV1,
        _record(
            CP70PredecessorCustodyV1,
            {
                "schema_version": CP70_TEST28_SCHEMA_VERSION,
                "v20_protocol_sha256": _V20_PROTOCOL_SHA256,
                "v20_protocol_bytes": _V20_PROTOCOL_BYTES,
                "v20_protocol_lf_count": _V20_PROTOCOL_LF_COUNT,
                "v20_manifest_sha256": _V20_MANIFEST_SHA256,
                "v20_manifest_bytes": _V20_MANIFEST_BYTES,
                "v20_manifest_lf_count": _V20_MANIFEST_LF_COUNT,
                "cp61_source_sha256": _CP61_SOURCE_SHA256,
                "cp61_bundle_record_sha256": _CP61_BUNDLE_RECORD_SHA256,
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "cp61_projection_contract_record_sha256": _CP61_PROJECTION_CONTRACT_RECORD_SHA256,
                "cp63_independent_source_sha256": _CP63_INDEPENDENT_SOURCE_SHA256,
                "cp63_independent_test_sha256": _CP63_INDEPENDENT_TEST_SHA256,
                "cp63_independent_bundle_record_sha256": _CP63_INDEPENDENT_BUNDLE_RECORD_SHA256,
                "cp63_schedule_contract_record_sha256": _CP63_SCHEDULE_CONTRACT_RECORD_SHA256,
                "cp68_source_sha256": _CP68_SOURCE_SHA256,
                "cp68_test_sha256": _CP68_TEST_SHA256,
                "cp68_bundle_record_sha256": _CP68_BUNDLE_RECORD_SHA256,
                "cp68_output_schema_record_sha256": _CP68_OUTPUT_SCHEMA_RECORD_SHA256,
                "cp68_aggregation_expectation_record_sha256": _CP68_AGGREGATION_EXPECTATION_RECORD_SHA256,
                "cp68_qualification_record_sha256": _CP68_QUALIFICATION_RECORD_SHA256,
                "cp68_fixture_set_sha256": _CP68_FIXTURE_SET_SHA256,
                "cp68_ordered_projection_sha256": _CP68_ORDERED_PROJECTION_SHA256,
                "cp68_ordered_estimand_record_sha256s_sha256": _CP68_ORDERED_ESTIMAND_RECORD_SHA256S_SHA256,
                "cp68_output_body_sha256": _CP68_OUTPUT_BODY_SHA256,
                "cp68_output_canonical_json_bytes": _CP68_OUTPUT_CANONICAL_JSON_BYTES,
                "cp68_output_canonical_json_sha256": _CP68_OUTPUT_CANONICAL_JSON_SHA256,
                "cp69_source_sha256": _CP69_SOURCE_SHA256,
                "cp69_test_sha256": _CP69_TEST_SHA256,
                "cp69_bundle_record_sha256": _CP69_BUNDLE_RECORD_SHA256,
                "cp69_interchange_contract_record_sha256": _CP69_INTERCHANGE_CONTRACT_RECORD_SHA256,
                "cp69_full_stream_expectation_record_sha256": _CP69_FULL_STREAM_EXPECTATION_RECORD_SHA256,
                "cp69_qualification_record_sha256": _CP69_QUALIFICATION_RECORD_SHA256,
                "cp69_fixture_set_sha256": _CP69_FIXTURE_SET_SHA256,
                "cp69_first_interchange_record_sha256": _CP69_FIRST_INTERCHANGE_RECORD_SHA256,
                "cp69_ordered_interchange_record_sha256": _CP69_ORDERED_INTERCHANGE_RECORD_SHA256,
                "cp69_total_input_bytes": _CP69_TOTAL_INPUT_BYTES,
                "cp69_ordered_target_projection_sha256": _CP68_ORDERED_PROJECTION_SHA256,
            },
        ),
    )


def _reducer_contract() -> CP70SourceIndependentReducerContractV1:
    return cast(
        CP70SourceIndependentReducerContractV1,
        _record(
            CP70SourceIndependentReducerContractV1,
            {
                "schema_version": CP70_TEST28_SCHEMA_VERSION,
                "contract_id": "cp70-closed-cp69-to-cp68-output-source-independent-reducer-v1",
                "source_interchange_schema_version": _CP69_SCHEMA_VERSION,
                "target_output_schema_version": _CP68_SCHEMA_VERSION,
                "seed_count": CP70_TEST28_SEED_COUNT,
                "row_count": CP70_TEST28_ROW_COUNT,
                "request_count": CP70_TEST28_REQUEST_COUNT,
                "estimand_count": CP70_TEST28_ESTIMAND_COUNT,
                "logical_request_order": "seed-major-row-minor-one-based",
                "private_stream_injection_only": True,
                "public_stream_api_exposed": False,
                "source_independent": True,
                "stdlib_only": True,
                "project_modules_imported": False,
                "direct_to_fixed_sufficient_statistics": True,
                "cp68_projection_records_created": False,
                "interchange_corpus_retained": False,
                "output_sufficient_statistic_map_sizes": (72, 170, 16, 312),
                "diagnostic_status_count_map_size": 6,
                "aggregation_update_count": 362_928,
                "cp_endpoint_table_count": 16,
                "cp_adjacent_boundary_comparison_count": 60,
                "maximum_interchange_bytes": CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES,
                "maximum_stream_bytes": CP70_TEST28_MAXIMUM_STREAM_BYTES,
                "maximum_output_bytes": CP70_TEST28_MAXIMUM_OUTPUT_BYTES,
            },
        ),
    )


def _output_validation_contract() -> CP70OutputValidationContractV1:
    return cast(
        CP70OutputValidationContractV1,
        _record(
            CP70OutputValidationContractV1,
            {
                "schema_version": CP70_TEST28_SCHEMA_VERSION,
                "contract_id": "cp70-exact-closed-cp68-estimate-interval-output-byte-validator-v1",
                "source_output_schema_version": _CP68_SCHEMA_VERSION,
                "exact_root_keys": _OUTPUT_ROOT_KEYS,
                "exact_estimand_keys": _OUTPUT_ESTIMAND_KEYS,
                "canonical_json_profile": "ASCII RFC8259; lexicographic keys; no whitespace, BOM, duplicate keys, floats, nonfinite values, or nonminimal exact fractions",
                "exact_fraction_encoding": '{"$fraction":["reduced-decimal-numerator","positive-reduced-decimal-denominator"]}',
                "estimand_record_digest_domain": "cp68-test28-estimand-estimate-interval-v1",
                "output_body_digest_domain": "cp68-test28-estimate-interval-output-body-v1",
                "payload_digest_profile": "untagged-sha256-of-exact-canonical-output-bytes",
                "closed_fixture_only": True,
                "exact_input_bytes": True,
                "raise_or_sealed_return": True,
                "partial_result_permitted": False,
                "estimand_count": CP70_TEST28_ESTIMAND_COUNT,
                "observable_estimand_count": CP70_TEST28_OBSERVABLE_ESTIMAND_COUNT,
                "rejection_first_attempt_estimand_count": CP70_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
                "feature_estimand_count": CP70_TEST28_FEATURE_ESTIMAND_COUNT,
                "binomial_estimand_count": CP70_TEST28_BINOMIAL_ESTIMAND_COUNT,
                "computed_interval_count": CP70_TEST28_COMPUTED_INTERVAL_COUNT,
                "insufficient_selection_count": CP70_TEST28_INSUFFICIENT_SELECTION_COUNT,
                "maximum_output_bytes": CP70_TEST28_MAXIMUM_OUTPUT_BYTES,
                "maximum_canonical_depth": CP70_TEST28_MAXIMUM_CANONICAL_DEPTH,
                "maximum_canonical_nodes": CP70_TEST28_MAXIMUM_CANONICAL_NODES,
                "maximum_key_characters": CP70_TEST28_MAXIMUM_KEY_CHARACTERS,
                "maximum_text_characters": CP70_TEST28_MAXIMUM_TEXT_CHARACTERS,
                "maximum_integer_decimal_digits": CP70_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS,
                "maximum_integer_bits": CP70_TEST28_MAXIMUM_INTEGER_BITS,
            },
        ),
    )


def _full_reduction_expectation() -> CP70FullReductionExpectationV1:
    return cast(
        CP70FullReductionExpectationV1,
        _record(
            CP70FullReductionExpectationV1,
            {
                "schema_version": CP70_TEST28_SCHEMA_VERSION,
                "source_fixture_set_sha256": _CP69_FIXTURE_SET_SHA256,
                "request_count": CP70_TEST28_REQUEST_COUNT,
                "total_input_bytes": _CP69_TOTAL_INPUT_BYTES,
                "first_interchange_record_sha256": _CP69_FIRST_INTERCHANGE_RECORD_SHA256,
                "ordered_interchange_record_sha256": _CP69_ORDERED_INTERCHANGE_RECORD_SHA256,
                "selected_counts_by_row": CP70_TEST28_SELECTED_COUNTS_BY_ROW,
                "rejection_selected_count": 8_254,
                "rejection_exhausted_count": 2_034,
                "sir_selected_count": 8_254,
                "refusal_count": 4_744,
                "failure_count": 4_742,
                "timeout_count": 4_740,
                "first_attempt_contribution_count": 8_254,
                "feature_contribution_count": 321_906,
                "aggregation_update_count": 362_928,
                "estimand_count": CP70_TEST28_ESTIMAND_COUNT,
                "observable_estimand_count": CP70_TEST28_OBSERVABLE_ESTIMAND_COUNT,
                "rejection_first_attempt_estimand_count": CP70_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
                "feature_estimand_count": CP70_TEST28_FEATURE_ESTIMAND_COUNT,
                "binomial_interval_count": CP70_TEST28_BINOMIAL_ESTIMAND_COUNT,
                "feature_interval_count": 156,
                "insufficient_selection_count": CP70_TEST28_INSUFFICIENT_SELECTION_COUNT,
                "computed_interval_count": CP70_TEST28_COMPUTED_INTERVAL_COUNT,
                "distinct_binomial_success_count_count": 16,
                "cp_adjacent_boundary_comparison_count": 60,
                "ordered_target_projection_sha256": _CP68_ORDERED_PROJECTION_SHA256,
                "ordered_estimand_record_sha256s_sha256": _CP68_ORDERED_ESTIMAND_RECORD_SHA256S_SHA256,
                "output_body_sha256": _CP68_OUTPUT_BODY_SHA256,
                "output_canonical_json_bytes": _CP68_OUTPUT_CANONICAL_JSON_BYTES,
                "output_canonical_json_sha256": _CP68_OUTPUT_CANONICAL_JSON_SHA256,
            },
        ),
    )


_BUNDLE_LOCK = threading.RLock()
_BUNDLE_CACHE: Optional[
    CP70EstimateIntervalOutputValidationQualificationBundleV1
] = None


def cp70_estimate_interval_output_validation_qualification_bundle() -> CP70EstimateIntervalOutputValidationQualificationBundleV1:
    """Return the pure zero-I/O CP70 definition bundle."""

    global _BUNDLE_CACHE
    with _BUNDLE_LOCK:
        if _BUNDLE_CACHE is None:
            _BUNDLE_CACHE = cast(
                CP70EstimateIntervalOutputValidationQualificationBundleV1,
                _record(
                    CP70EstimateIntervalOutputValidationQualificationBundleV1,
                    {
                        "schema_version": CP70_TEST28_SCHEMA_VERSION,
                        "scope": CP70_TEST28_SCOPE,
                        "predecessor_custody": _predecessor_custody(),
                        "reducer_contract": _reducer_contract(),
                        "output_validation_contract": _output_validation_contract(),
                        "full_reduction_expectation": _full_reduction_expectation(),
                        "zero_argument_builder": True,
                        "builder_parses_reduces_or_validates": False,
                        "qualification_runner_zero_argument": True,
                        "bounded_public_closed_output_byte_validator_exposed": True,
                        "generic_public_stream_reducer_exposed": False,
                        "closed_module_owned_fixture_only": True,
                        "source_independent": True,
                        "stdlib_only_import": True,
                        "project_modules_imported": False,
                        "streaming_interchange": True,
                        "full_interchange_corpus_materialized": False,
                        "cp68_projection_records_created": False,
                        "output_record_vector_cardinality": CP70_TEST28_ESTIMAND_COUNT,
                        "maximum_interchange_bytes": CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES,
                        "maximum_stream_bytes": CP70_TEST28_MAXIMUM_STREAM_BYTES,
                        "maximum_output_bytes": CP70_TEST28_MAXIMUM_OUTPUT_BYTES,
                        "host_filesystem_probed": False,
                        "clock_read": False,
                        "rng_used": False,
                        "network_used": False,
                        "subprocess_api_exposed": False,
                        "filesystem_path_api_exposed": False,
                        "raw_record_api_exposed": False,
                        "stable_trace_api_exposed": False,
                        "production_campaign_api_exposed": False,
                        "production_estimate_or_interval": False,
                        "decision_path_qualified": False,
                        "production_qualification_receipt_present": False,
                        "production_evidence_present_count": 0,
                        "production_gate_13_evidence_present": False,
                        "production_gate_13_state": "MISSING",
                        "production_gate_14_evidence_present": False,
                        "production_gate_14_state": "MISSING",
                        "production_execution_authorized": False,
                        "production_execution_observed": False,
                        "runner_and_recomputation_blocker_closed": False,
                        "unconditional_operational_predictions_blocker_closed": False,
                        "power_and_thresholds_blocker_closed": False,
                        "confirmatory_custody_blocker_closed": False,
                        "confirmatory_evidence": False,
                        "manuscript_claim": False,
                        "formal_test_28_status": CP70_TEST28_FORMAL_TEST_28_STATUS,
                        "formal_test_28_closed": False,
                        "ledger_prerequisite_id": CP70_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID,
                        "ledger_prerequisite_state": _LEDGER_PREREQUISITE_STATE,
                        "ledger_total_count": 25,
                        "ledger_satisfied_count": 21,
                        "ledger_missing_count": 4,
                        "development_qualification_only": True,
                    },
                ),
            )
        return cast(
            CP70EstimateIntervalOutputValidationQualificationBundleV1,
            _require_issued_record(_BUNDLE_CACHE)[0],
        )


_QUALIFICATION_LOCK = threading.RLock()


def _run_estimate_interval_output_validation_qualification() -> CP70EstimateIntervalOutputValidationQualificationV1:
    bundle = cp70_estimate_interval_output_validation_qualification_bundle()
    expectation = bundle.full_reduction_expectation
    _closed_expected_output()
    metrics = _reduce_closed_compact_interchange_stream_details()
    payload, materialized_output = _build_estimate_interval_output_bytes(metrics)
    output = {
        "ordered_estimand_record_sha256s_sha256": materialized_output[
            "ordered_estimand_record_sha256s_sha256"
        ],
        "output_body_sha256": materialized_output["output_body_sha256"],
        "output_canonical_json_bytes": materialized_output[
            "output_canonical_json_bytes"
        ],
        "output_canonical_json_sha256": materialized_output[
            "output_canonical_json_sha256"
        ],
    }
    del materialized_output
    validation = cp70_validate_closed_cp68_estimate_interval_output_bytes(payload)
    endpoints = _certify_cp_endpoint_table()
    matches = (
        metrics["request_count"] == expectation.request_count
        and metrics["total_input_bytes"] == expectation.total_input_bytes
        and metrics["first_interchange_record_sha256"]
        == expectation.first_interchange_record_sha256
        and metrics["ordered_interchange_record_sha256"]
        == expectation.ordered_interchange_record_sha256
        and metrics["ordered_target_projection_sha256"]
        == expectation.ordered_target_projection_sha256
        and metrics["selected_counts_by_row"] == expectation.selected_counts_by_row
        and metrics["aggregation_update_count"] == expectation.aggregation_update_count
        and output["ordered_estimand_record_sha256s_sha256"]
        == expectation.ordered_estimand_record_sha256s_sha256
        and output["output_body_sha256"] == expectation.output_body_sha256
        and output["output_canonical_json_bytes"]
        == expectation.output_canonical_json_bytes
        and output["output_canonical_json_sha256"]
        == expectation.output_canonical_json_sha256
        and validation.closed_fixture_match
        and endpoints
    )
    if not matches:
        _fail(
            "CP70_QUALIFICATION_FAILURE",
            "closed qualification differs from expectation",
        )
    result = cast(
        CP70EstimateIntervalOutputValidationQualificationV1,
        _record(
            CP70EstimateIntervalOutputValidationQualificationV1,
            {
                "schema_version": CP70_TEST28_SCHEMA_VERSION,
                "source_fixture_set_sha256": _CP69_FIXTURE_SET_SHA256,
                "request_count": metrics["request_count"],
                "total_input_bytes": metrics["total_input_bytes"],
                "logical_ordinals_complete": metrics["logical_ordinals_complete"],
                "streaming_peak_input_payload_count": 1,
                "streaming_peak_parsed_observation_count": 1,
                "interchange_corpus_retained": False,
                "cp68_projection_records_created": False,
                "aggregation_update_count": metrics["aggregation_update_count"],
                "estimand_count": CP70_TEST28_ESTIMAND_COUNT,
                "output_record_vector_cardinality": CP70_TEST28_ESTIMAND_COUNT,
                "output_records_retained_after_runner": False,
                "ordered_interchange_record_sha256": metrics[
                    "ordered_interchange_record_sha256"
                ],
                "ordered_target_projection_sha256": metrics[
                    "ordered_target_projection_sha256"
                ],
                "ordered_estimand_record_sha256s_sha256": output[
                    "ordered_estimand_record_sha256s_sha256"
                ],
                "output_body_sha256": output["output_body_sha256"],
                "output_canonical_json_bytes": output["output_canonical_json_bytes"],
                "output_canonical_json_sha256": output["output_canonical_json_sha256"],
                "canonical_output_validated": True,
                "record_digests_verified": True,
                "cp_endpoint_table_independently_certified": endpoints,
                "feature_threshold_and_clipping_verified": True,
                "target_output_matches_cp68_expectation": matches,
                "raw_record_parsed": False,
                "stable_trace_parsed": False,
                "provenance_authenticated": False,
                "production_recomputation_performed": False,
                "production_estimate_or_interval": False,
                "decision_path_qualified": False,
                "production_evidence": False,
                "production_execution_authorized": False,
                "runner_and_recomputation_blocker_closed": False,
                "formal_test_28_closed": False,
                "all_development_qualification_checks_passed": matches,
            },
        ),
    )
    del payload, output, validation, metrics
    return result


def cp70_run_estimate_interval_output_validation_qualification() -> CP70EstimateIntervalOutputValidationQualificationV1:
    """Run the closed zero-I/O CP69-byte to exact CP68-output qualification."""

    try:
        with _QUALIFICATION_LOCK:
            return _run_estimate_interval_output_validation_qualification()
    except CP70EstimateIntervalOutputValidationQualificationError:
        raise
    except MemoryError as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_RESOURCE_EXHAUSTED", "closed CP70 qualification exhausted memory"
        ) from exc
    except Exception as exc:
        raise CP70EstimateIntervalOutputValidationQualificationError(
            "CP70_QUALIFICATION_FAILURE",
            "closed source-independent CP70 qualification failed",
        ) from exc


__all__ = (
    "CP70_TEST28_SCHEMA_VERSION",
    "CP70_TEST28_SCOPE",
    "CP70_TEST28_FORMAL_TEST_28_STATUS",
    "CP70_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP70_TEST28_SEED_COUNT",
    "CP70_TEST28_ROW_COUNT",
    "CP70_TEST28_REQUEST_COUNT",
    "CP70_TEST28_ESTIMAND_COUNT",
    "CP70_TEST28_OBSERVABLE_ESTIMAND_COUNT",
    "CP70_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
    "CP70_TEST28_FEATURE_ESTIMAND_COUNT",
    "CP70_TEST28_BINOMIAL_ESTIMAND_COUNT",
    "CP70_TEST28_COMPUTED_INTERVAL_COUNT",
    "CP70_TEST28_INSUFFICIENT_SELECTION_COUNT",
    "CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES",
    "CP70_TEST28_MAXIMUM_STREAM_BYTES",
    "CP70_TEST28_MAXIMUM_OUTPUT_BYTES",
    "CP70_TEST28_MAXIMUM_CANONICAL_DEPTH",
    "CP70_TEST28_MAXIMUM_CANONICAL_NODES",
    "CP70_TEST28_MAXIMUM_KEY_CHARACTERS",
    "CP70_TEST28_MAXIMUM_TEXT_CHARACTERS",
    "CP70_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS",
    "CP70_TEST28_MAXIMUM_INTEGER_BITS",
    "CP70_TEST28_SELECTED_COUNTS_BY_ROW",
    "CP70EstimateIntervalOutputValidationQualificationError",
    "CP70PredecessorCustodyV1",
    "CP70SourceIndependentReducerContractV1",
    "CP70OutputValidationContractV1",
    "CP70FullReductionExpectationV1",
    "CP70EstimateIntervalOutputValidationV1",
    "CP70EstimateIntervalOutputValidationQualificationV1",
    "CP70EstimateIntervalOutputValidationQualificationBundleV1",
    "cp70_validate_closed_cp68_estimate_interval_output_bytes",
    "cp70_canonical_json_bytes",
    "cp70_sha256",
    "cp70_estimate_interval_output_validation_qualification_bundle",
    "cp70_run_estimate_interval_output_validation_qualification",
)
