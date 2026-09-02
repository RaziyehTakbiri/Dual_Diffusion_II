"""Closed CP69 qualification for the CP63-compact to CP68 byte boundary.

CP63 already freezes the scientific reduction from one stable trace to one
compact observation.  CP68 already freezes the downstream compact-projection
semantics and the 32,768-item synthetic aggregation fixture.  This module adds
only a bounded canonical byte interchange between those two frozen semantic
surfaces.  It deliberately does not define a raw-record or stable-trace
schema, authenticate any provenance field, aggregate an estimate or interval,
make a decision, expose a campaign, or execute production work.

The pure bundle builder is definition-only.  The separately named zero-
argument runner streams one closed module-owned 2,048-by-16 synthetic byte
fixture, parses one record at a time, checks the independently reconstructed
CP63 contribution ordinal, maps it to the exact CP68 projection view, and
discards both objects before advancing.  No predecessor or other project
module is imported.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
from functools import lru_cache
import hashlib
import hmac
import json
import threading
from typing import Iterator, Mapping, Optional, Tuple, cast
import weakref


CP69_TEST28_SCHEMA_VERSION = (
    "cp69-test28-compact-projection-interchange-qualification-v1"
)
CP69_TEST28_SCOPE = (
    "development-only-cp63-compact-semantics-to-cp68-projection-canonical-"
    "byte-interchange-and-32768-item-stream-qualification;bounded-public-"
    "single-record-byte-parser-and-sealed-projection-mapper;closed-module-"
    "owned-full-cardinality-synthetic-fixture;transport-only-no-new-"
    "scientific-semantics;no-raw-record-or-stable-trace-schema-or-parser;"
    "no-provenance-authentication;no-filesystem-path-clock-rng-network-or-"
    "subprocess;no-estimate-interval-threshold-decision-production-runner-"
    "writer-shard-campaign-receipt-gate-execution-power-confirmatory-"
    "manuscript-or-test28-closure-claim"
)
CP69_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP69_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID = (
    "whole_seed_cp63_compact_semantics_to_cp68_projection_interchange_" "qualification"
)
CP69_TEST28_SEED_COUNT = 2_048
CP69_TEST28_ROW_COUNT = 16
CP69_TEST28_REQUEST_COUNT = 32_768
CP69_TEST28_OBSERVABLE_ESTIMAND_COUNT = 72
CP69_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT = 170
CP69_TEST28_FEATURE_ESTIMAND_COUNT = 312
CP69_TEST28_ESTIMAND_COUNT = 554
CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES = 65_536
CP69_TEST28_MAXIMUM_CANONICAL_DEPTH = 16
CP69_TEST28_MAXIMUM_CANONICAL_NODES = 512
CP69_TEST28_MAXIMUM_TEXT_BYTES = 4_096
CP69_TEST28_MAXIMUM_INTEGER_BITS = 256
CP69_TEST28_MAXIMUM_STREAM_BYTES = 2_147_483_648
CP69_TEST28_SELECTED_COUNTS_BY_ROW = (
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
_CP63_COMPACT_SCHEMA_VERSION = "cp63-test28-independent-compact-recomputation-v1"
_CP68_PROJECTION_SCHEMA_VERSION = (
    "cp68-test28-compact-projection-aggregation-qualification-v1"
)
_ZERO_SHA256 = "0" * 64

_V19_PROTOCOL_SHA256 = (
    "38558ba7f67f56fb21aa6974ee9a932350ffb703d47fc6b972e22b322a444d08"
)
_V19_PROTOCOL_BYTES = 174_492
_V19_PROTOCOL_LF_COUNT = 3_019
_V19_MANIFEST_SHA256 = (
    "3649c90d3d1ddffa9edae27625246c0f97399c7c60319a5c09d7fa20b365b1ae"
)
_V19_MANIFEST_BYTES = 6_059_388
_V19_MANIFEST_LF_COUNT = 119_095
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
_CP63_RUNNER_SOURCE_SHA256 = (
    "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
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
_CP63_ACCEPTANCE_RECEIPT_SHA256 = (
    "2b2f41f14424ddb164b6db793991ece8b222a4e4295d7e0143c6b6496c50097b"
)
_CP63_SCHEDULE_CONTRACT_RECORD_SHA256 = (
    "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
)
_CP67_SCHEDULE_EXPECTATION_RECORD_SHA256 = (
    "283ebec3c3b1bb4c3a18479fdc66e20525a591d9af1f02007869154cf8d041ea"
)
_CP68_SOURCE_SHA256 = "15afd7e4a8fb99c137faea8d57ef2bd2dc3ab3c193481883da4e205b75c16555"
_CP68_TEST_SHA256 = "5587785ad8c5fc3ac526758ce87ad91acbb5b4e1532563ceacc2e1c8d64f32e4"
_CP68_BUNDLE_RECORD_SHA256 = (
    "b301ea4cadb8a67fa238dfa5872c874b4689a08b7baec04f1133bef7191a2a83"
)
_CP68_QUALIFICATION_RECORD_SHA256 = (
    "881dc5b6539504a3bf42957d7e0b4298484db0cfd637e3fe861ce9847cf81400"
)
_CP68_SYNTHETIC_PROJECTION_CONTRACT_RECORD_SHA256 = (
    "a3fd1bba3bf70e1024e6b264e8ee775357d30094d76e3e7c5bd53d7d41bdd9f1"
)
_CP68_AGGREGATION_EXPECTATION_RECORD_SHA256 = (
    "00e5d9263386bda729b929da898d5c97174fb2606db52dfad1920089e3d3882a"
)
_CP68_FIXTURE_SET_SHA256 = (
    "6b8d7db706b94c32ee53efe9969e16560997e0f7b2345960e44ad4f18feb49ce"
)
_CP68_FIRST_PROJECTION_SHA256 = (
    "b40854463d8f441614621319f2e7a774059cd757d75284750906f84222744796"
)
_CP68_ORDERED_PROJECTION_SHA256 = (
    "f898741b035d59116f6e096a1deab6c642f83dd3ad0417b7995e182584731f42"
)
_CP68_OUTPUT_CANONICAL_JSON_SHA256 = (
    "f9e1bf93354af057d08ca722d2cffe1a8188d2f1e823a0173f9b6a937ddc42c3"
)

_EXPECTED_FIRST_INTERCHANGE_RECORD_SHA256 = (
    "de2237dfb851b4370d25cfa9b72698a73d6ea4c1c4f70b654f509999ecec34b8"
)
_EXPECTED_ORDERED_INTERCHANGE_RECORD_SHA256 = (
    "754b058697dc9324611152b4987925a414520fc98dd764571321c3135d0ecc8d"
)

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
_TARGET_PROJECTION_KEYS = (
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
    "projection_sha256",
)


class CP69CompactProjectionInterchangeQualificationError(RuntimeError):
    """Fail-closed CP69 error carrying one stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP69 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP69 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP69 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP69PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    v19_protocol_sha256: str
    v19_protocol_bytes: int
    v19_protocol_lf_count: int
    v19_manifest_sha256: str
    v19_manifest_bytes: int
    v19_manifest_lf_count: int
    cp61_source_sha256: str
    cp61_bundle_record_sha256: str
    cp61_stable_design_sha256: str
    cp61_projection_contract_record_sha256: str
    cp63_runner_source_sha256: str
    cp63_independent_source_sha256: str
    cp63_independent_test_sha256: str
    cp63_independent_bundle_record_sha256: str
    cp63_acceptance_receipt_sha256: str
    cp63_schedule_contract_record_sha256: str
    cp67_schedule_expectation_record_sha256: str
    cp68_source_sha256: str
    cp68_test_sha256: str
    cp68_bundle_record_sha256: str
    cp68_qualification_record_sha256: str
    cp68_synthetic_projection_contract_record_sha256: str
    cp68_aggregation_expectation_record_sha256: str
    cp68_fixture_set_sha256: str
    cp68_ordered_projection_sha256: str
    cp68_output_canonical_json_sha256: str
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP69CompactInterchangeContractV1(_SealedRecord):
    schema_version: str
    contract_id: str
    source_semantic_schema_version: str
    target_projection_schema_version: str
    exact_input_keys: Tuple[str, ...]
    exact_target_keys: Tuple[str, ...]
    canonical_json_profile: str
    exact_fraction_encoding: str
    record_digest_domain: str
    target_projection_digest_domain: str
    parser_input_exact_bytes: bool
    seed_count: int
    row_count: int
    request_count: int
    logical_request_order: str
    logical_request_ordinal_formula: str
    closed_fixture_plan_seed_formula: str
    observable_contribution_ordinal_recomputed: bool
    cp63_provenance_fields_transported: bool
    provenance_authenticated: bool
    transport_adds_scientific_semantics: bool
    maximum_interchange_bytes: int
    maximum_canonical_depth: int
    maximum_canonical_nodes: int
    maximum_text_bytes: int
    maximum_integer_bits: int
    maximum_stream_bytes: int
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP69CompactInterchangeObservationV1(_SealedRecord):
    schema_version: str
    source_semantic_schema_version: str
    seed_ordinal: int
    row_ordinal: int
    logical_request_ordinal: int
    row_key: str
    fixture_id: str
    strategy: str
    budget: int
    plan_seed_hex: str
    seed_free_request_sha256: str
    request_instance_sha256: str
    runtime_lock_sha256: str
    stable_trace_sha256: str
    observable_cell_label: str
    observable_contribution_ordinal: int
    first_selected_attempt_one_based: Optional[int]
    selected: bool
    selected_feature_ids: Tuple[str, ...]
    selected_feature_values: Tuple[Fraction, ...]
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP69CP68ProjectionViewV1(_SealedRecord):
    schema_version: str
    seed_ordinal: int
    row_ordinal: int
    logical_request_ordinal: int
    row_key: str
    fixture_id: str
    strategy: str
    budget: int
    plan_seed_hex: str
    observable_cell_label: str
    first_selected_attempt_one_based: Optional[int]
    selected: bool
    selected_feature_ids: Tuple[str, ...]
    selected_feature_values: Tuple[Fraction, ...]
    projection_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP69FullStreamExpectationV1(_SealedRecord):
    schema_version: str
    fixture_set_sha256: str
    request_count: int
    selected_counts_by_row: Tuple[int, ...]
    rejection_selected_count: int
    rejection_exhausted_count: int
    sir_selected_count: int
    refusal_count: int
    failure_count: int
    timeout_count: int
    first_attempt_contribution_count: int
    feature_contribution_count: int
    first_interchange_record_sha256: str
    ordered_interchange_record_sha256: str
    first_target_projection_sha256: str
    ordered_target_projection_sha256: str
    cp68_output_canonical_json_sha256: str
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP69CompactProjectionInterchangeQualificationV1(_SealedRecord):
    schema_version: str
    fixture_set_sha256: str
    request_count: int
    logical_ordinals_complete: bool
    streaming_peak_input_payload_count: int
    streaming_peak_parsed_observation_count: int
    streaming_peak_projection_view_count: int
    interchange_corpus_retained: bool
    canonical_bytes_verified: bool
    record_digests_verified: bool
    row_identity_verified: bool
    observable_contribution_ordinals_verified: bool
    outcome_and_attempt_semantics_verified: bool
    selected_feature_semantics_verified: bool
    selected_counts_by_row: Tuple[int, ...]
    first_attempt_contribution_count: int
    feature_contribution_count: int
    first_interchange_record_sha256: str
    ordered_interchange_record_sha256: str
    first_target_projection_sha256: str
    ordered_target_projection_sha256: str
    target_projection_matches_cp68_expectation: bool
    raw_record_parsed: bool
    stable_trace_parsed: bool
    provenance_authenticated: bool
    estimate_or_interval_computed: bool
    decision_path_qualified: bool
    production_evidence: bool
    production_execution_authorized: bool
    runner_and_recomputation_blocker_closed: bool
    formal_test_28_closed: bool
    all_development_qualification_checks_passed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP69CompactProjectionInterchangeQualificationBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    predecessor_custody: CP69PredecessorCustodyV1
    interchange_contract: CP69CompactInterchangeContractV1
    full_stream_expectation: CP69FullStreamExpectationV1
    qualification_fixture_set_sha256: str
    zero_argument_builder: bool
    builder_parses_or_streams: bool
    qualification_runner_zero_argument: bool
    bounded_public_byte_parser_exposed: bool
    sealed_public_projection_mapper_exposed: bool
    closed_module_owned_fixture_only: bool
    stdlib_only_import: bool
    project_modules_imported: bool
    streaming_interchange: bool
    full_interchange_corpus_materialized: bool
    maximum_stream_bytes: int
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
_DIGEST_FIELDS = {
    CP69PredecessorCustodyV1: "record_sha256",
    CP69CompactInterchangeContractV1: "record_sha256",
    CP69CompactInterchangeObservationV1: "record_sha256",
    CP69CP68ProjectionViewV1: "projection_sha256",
    CP69FullStreamExpectationV1: "record_sha256",
    CP69CompactProjectionInterchangeQualificationV1: "record_sha256",
    CP69CompactProjectionInterchangeQualificationBundleV1: "record_sha256",
}
_RECORD_DOMAINS = {
    CP69PredecessorCustodyV1: b"cp69-test28-predecessor-custody-v1",
    CP69CompactInterchangeContractV1: (b"cp69-test28-compact-interchange-contract-v1"),
    CP69CompactInterchangeObservationV1: (
        b"cp69-test28-compact-interchange-observation-v1"
    ),
    CP69CP68ProjectionViewV1: (b"cp68-test28-synthetic-compact-projection-v1"),
    CP69FullStreamExpectationV1: b"cp69-test28-full-stream-expectation-v1",
    CP69CompactProjectionInterchangeQualificationV1: (
        b"cp69-test28-compact-projection-interchange-qualification-v1"
    ),
    CP69CompactProjectionInterchangeQualificationBundleV1: (
        b"cp69-test28-compact-projection-interchange-qualification-bundle-v1"
    ),
}

_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS: weakref.WeakKeyDictionary[
    _SealedRecord, bytes
] = weakref.WeakKeyDictionary()


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
    (
        (0, (Fraction(-1, 2),)),
        (1, (Fraction(1, 2), Fraction(-1, 2))),
    ),
)


def _fail(code: str, message: str) -> None:
    raise CP69CompactProjectionInterchangeQualificationError(code, message)


def _plain_json_value(
    value: object,
    *,
    depth: int = 0,
    nodes: Optional[list[int]] = None,
) -> object:
    if nodes is None:
        nodes = [0]
    if depth > CP69_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP69_INPUT_RESOURCE_LIMIT", "canonical nesting is too deep")
    nodes[0] += 1
    if nodes[0] > CP69_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP69_INPUT_RESOURCE_LIMIT", "canonical node count is too large")
    if value is None or type(value) is bool:
        return value
    if type(value) is str:
        if len(cast(str, value).encode("utf-8")) > CP69_TEST28_MAXIMUM_TEXT_BYTES:
            _fail("CP69_INPUT_RESOURCE_LIMIT", "canonical text is too large")
        return value
    if type(value) is int:
        if cast(int, value).bit_length() > CP69_TEST28_MAXIMUM_INTEGER_BITS:
            _fail("CP69_INPUT_RESOURCE_LIMIT", "canonical integer is too large")
        return value
    if type(value) is Fraction:
        fraction = cast(Fraction, value)
        if (
            max(fraction.numerator.bit_length(), fraction.denominator.bit_length())
            > CP69_TEST28_MAXIMUM_INTEGER_BITS
        ):
            _fail("CP69_INPUT_RESOURCE_LIMIT", "canonical fraction is too large")
        return {"$fraction": [str(fraction.numerator), str(fraction.denominator)]}
    if type(value) is tuple:
        return [
            _plain_json_value(item, depth=depth + 1, nodes=nodes)
            for item in cast(tuple, value)
        ]
    if isinstance(value, _SealedRecord):
        return {
            item.name: _plain_json_value(
                getattr(value, item.name), depth=depth + 1, nodes=nodes
            )
            for item in fields(type(value))
        }
    if type(value) is dict:
        mapping = cast(dict, value)
        if any(type(key) is not str for key in mapping):
            _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "canonical key is not text")
        return {
            key: _plain_json_value(mapping[key], depth=depth + 1, nodes=nodes)
            for key in sorted(mapping)
        }
    _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "canonical value has an alien type")
    raise AssertionError("unreachable")


def _plain_json_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            _plain_json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except CP69CompactProjectionInterchangeQualificationError:
        raise
    except (OverflowError, RecursionError, TypeError, ValueError) as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_INPUT_RESOURCE_LIMIT",
            "canonical serialization failed closed",
        ) from exc
    if len(encoded) > CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES:
        _fail("CP69_INPUT_BYTE_LIMIT", "canonical record exceeds its byte cap")
    return encoded


def _record(cls: type, values: Mapping[str, object]) -> object:
    if cls not in _RECORD_DOMAINS:
        raise TypeError("CP69 sealed record type is unsupported")
    names = tuple(item.name for item in fields(cls))
    digest_field = _DIGEST_FIELDS[cls]
    if set(values) != set(names) - {digest_field}:
        raise TypeError("CP69 sealed record field set differs")
    complete = dict(values)
    if cls is CP69CP68ProjectionViewV1:
        complete[digest_field] = hashlib.sha256(
            _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(dict(values))
        ).hexdigest()
    else:
        complete[digest_field] = _ZERO_SHA256
        complete[digest_field] = hashlib.sha256(
            _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(complete)
        ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _plain_json_bytes(result)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = snapshot
    return result


def _require_issued_record(value: object) -> Tuple[_SealedRecord, bytes]:
    if type(value) not in _RECORD_DOMAINS:
        _fail("CP69_RECORD_TYPE_MISMATCH", "record has an unsupported exact type")
    record = cast(_SealedRecord, value)
    with _ISSUED_RECORD_LOCK:
        snapshot = _ISSUED_RECORD_SNAPSHOTS.get(record)
    if snapshot is None:
        _fail("CP69_RECORD_NOT_ISSUED", "record was not issued by this module")
    current = _plain_json_bytes(record)
    if not hmac.compare_digest(current, snapshot):
        _fail("CP69_RECORD_TAMPERED", "issued record was mutated")
    cls = type(record)
    digest_field = _DIGEST_FIELDS[cls]
    supplied = getattr(record, digest_field)
    body = {item.name: getattr(record, item.name) for item in fields(cls)}
    if cls is CP69CP68ProjectionViewV1:
        del body[digest_field]
        expected = hashlib.sha256(
            _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(body)
        ).hexdigest()
    else:
        body[digest_field] = _ZERO_SHA256
        expected = hashlib.sha256(
            _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(body)
        ).hexdigest()
    if type(supplied) is not str or not hmac.compare_digest(supplied, expected):
        _fail("CP69_RECORD_TAMPERED", "issued record digest differs")
    return record, snapshot


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("CP69_INPUT_JSON_INVALID", "JSON contains a duplicate key")
        result[key] = value
    return result


def _parse_bounded_integer(text: str) -> int:
    if len(text) > 80:
        _fail("CP69_INPUT_RESOURCE_LIMIT", "JSON integer text is too large")
    try:
        value = int(text, 10)
    except ValueError as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_INPUT_JSON_INVALID", "JSON integer is invalid"
        ) from exc
    if value.bit_length() > CP69_TEST28_MAXIMUM_INTEGER_BITS:
        _fail("CP69_INPUT_RESOURCE_LIMIT", "JSON integer is too large")
    return value


def _reject_json_float(text: str) -> object:
    del text
    _fail("CP69_INPUT_JSON_INVALID", "JSON floating values are forbidden")
    raise AssertionError("unreachable")


def _walk_decoded(
    value: object,
    *,
    depth: int = 0,
    nodes: Optional[list[int]] = None,
) -> None:
    if nodes is None:
        nodes = [0]
    if depth > CP69_TEST28_MAXIMUM_CANONICAL_DEPTH:
        _fail("CP69_INPUT_RESOURCE_LIMIT", "decoded nesting is too deep")
    nodes[0] += 1
    if nodes[0] > CP69_TEST28_MAXIMUM_CANONICAL_NODES:
        _fail("CP69_INPUT_RESOURCE_LIMIT", "decoded node count is too large")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if cast(int, value).bit_length() > CP69_TEST28_MAXIMUM_INTEGER_BITS:
            _fail("CP69_INPUT_RESOURCE_LIMIT", "decoded integer is too large")
        return
    if type(value) is str:
        if len(cast(str, value).encode("utf-8")) > CP69_TEST28_MAXIMUM_TEXT_BYTES:
            _fail("CP69_INPUT_RESOURCE_LIMIT", "decoded text is too large")
        return
    if type(value) is list:
        for item in cast(list, value):
            _walk_decoded(item, depth=depth + 1, nodes=nodes)
        return
    if type(value) is dict:
        for key, item in cast(dict, value).items():
            if type(key) is not str:
                _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "decoded key is not text")
            if len(key.encode("utf-8")) > CP69_TEST28_MAXIMUM_TEXT_BYTES:
                _fail("CP69_INPUT_RESOURCE_LIMIT", "decoded key is too large")
            _walk_decoded(item, depth=depth + 1, nodes=nodes)
        return
    _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "decoded value has an alien type")


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
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_INPUT_RESOURCE_LIMIT", "decoded JSON cannot be canonicalized"
        ) from exc


def _decode_canonical_object(payload: object) -> dict:
    if type(payload) is not bytes:
        _fail("CP69_INPUT_TYPE_MISMATCH", "interchange payload must be exact bytes")
    encoded = cast(bytes, payload)
    if not encoded or len(encoded) > CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES:
        _fail("CP69_INPUT_BYTE_LIMIT", "interchange payload byte length differs")
    if encoded.startswith(b"\xef\xbb\xbf"):
        _fail("CP69_INPUT_ENCODING_INVALID", "interchange payload has a BOM")
    try:
        text = encoded.decode("ascii")
    except UnicodeDecodeError as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_INPUT_ENCODING_INVALID", "interchange payload is not ASCII"
        ) from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_json_float,
            parse_int=_parse_bounded_integer,
            parse_constant=_reject_json_float,
        )
    except CP69CompactProjectionInterchangeQualificationError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_INPUT_JSON_INVALID", "interchange JSON is invalid"
        ) from exc
    _walk_decoded(value)
    if type(value) is not dict:
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "interchange root is not an object")
    if not hmac.compare_digest(_decoded_json_bytes(value), encoded):
        _fail("CP69_INPUT_CANONICAL_MISMATCH", "interchange JSON is not canonical")
    return cast(dict, value)


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(cast(str, value)) == 64
        and all(character in "0123456789abcdef" for character in cast(str, value))
    )


def _is_uint64_hex(value: object) -> bool:
    return (
        type(value) is str
        and len(cast(str, value)) == 16
        and all(character in "0123456789abcdef" for character in cast(str, value))
    )


def _canonical_decimal_integer(text: object, *, positive: bool = False) -> int:
    if type(text) is not str or not text:
        _fail("CP69_INPUT_FEATURE_MISMATCH", "fraction component is not text")
    supplied = cast(str, text)
    if len(supplied.encode("ascii", "ignore")) != len(supplied):
        _fail("CP69_INPUT_FEATURE_MISMATCH", "fraction component is not ASCII")
    negative = supplied.startswith("-")
    digits = supplied[1:] if negative else supplied
    if (
        not digits
        or any(character not in "0123456789" for character in digits)
        or (len(digits) > 1 and digits.startswith("0"))
        or (negative and digits == "0")
    ):
        _fail("CP69_INPUT_FEATURE_MISMATCH", "fraction component is noncanonical")
    value = int(supplied, 10)
    if value.bit_length() > CP69_TEST28_MAXIMUM_INTEGER_BITS:
        _fail("CP69_INPUT_RESOURCE_LIMIT", "fraction component is too large")
    if positive and value <= 0:
        _fail("CP69_INPUT_FEATURE_MISMATCH", "fraction denominator is not positive")
    return value


def _fraction_from_tag(value: object) -> Fraction:
    if type(value) is not dict or tuple(cast(dict, value).keys()) != ("$fraction",):
        _fail("CP69_INPUT_FEATURE_MISMATCH", "feature value lacks a fraction tag")
    pair = cast(dict, value)["$fraction"]
    if type(pair) is not list or len(cast(list, pair)) != 2:
        _fail("CP69_INPUT_FEATURE_MISMATCH", "fraction tag has the wrong shape")
    numerator = _canonical_decimal_integer(cast(list, pair)[0])
    denominator = _canonical_decimal_integer(cast(list, pair)[1], positive=True)
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        _fail("CP69_INPUT_FEATURE_MISMATCH", "fraction tag is not reduced")
    return result


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
    return (
        (0, "axis0", (Fraction(1, 1),)),
        (1, "axis0", (Fraction(1, 1), Fraction(0, 1))),
        (1, "axis1", (Fraction(0, 1), Fraction(1, 1))),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )


@lru_cache(maxsize=2)
def _feature_ids(fixture_id: str) -> Tuple[str, ...]:
    if fixture_id not in ("T28-M1-Q", "T28-M2-Q"):
        raise ValueError("CP69 fixture id is outside the frozen inventory")
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
    frozen = tuple(result)
    expected = 6 if fixture_id == "T28-M1-Q" else 33
    if len(frozen) != expected:
        raise AssertionError("CP69 feature inventory differs")
    return frozen


def _feature_bounds(feature_id: str) -> Tuple[Fraction, Fraction]:
    lower = (
        Fraction(-1, 1)
        if feature_id.endswith("/odd") or feature_id.startswith("pair-projection/")
        else Fraction(0, 1)
    )
    return lower, Fraction(1, 1)


def _observable_contribution_ordinal(row_ordinal: int, cell: str) -> int:
    offset = 0
    for current, (_fixture, strategy, _budget) in enumerate(_ROW_SHAPES, 1):
        cells = (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
        if current == row_ordinal:
            try:
                return offset + cells.index(cell) + 1
            except ValueError as exc:
                raise CP69CompactProjectionInterchangeQualificationError(
                    "CP69_INPUT_OUTCOME_MISMATCH",
                    "observable cell is outside its row family",
                ) from exc
        offset += len(cells)
    _fail("CP69_INPUT_ORDINAL_MISMATCH", "row ordinal is outside the inventory")
    raise AssertionError("unreachable")


def _validate_observation_values(values: Mapping[str, object]) -> None:
    if values["schema_version"] != CP69_TEST28_SCHEMA_VERSION:
        _fail("CP69_INPUT_SCHEMA_MISMATCH", "interchange schema differs")
    if values["source_semantic_schema_version"] != _CP63_COMPACT_SCHEMA_VERSION:
        _fail("CP69_INPUT_SCHEMA_MISMATCH", "source semantic schema differs")
    exact_integer_fields = (
        "seed_ordinal",
        "row_ordinal",
        "logical_request_ordinal",
        "budget",
        "observable_contribution_ordinal",
    )
    exact_text_fields = (
        "schema_version",
        "source_semantic_schema_version",
        "row_key",
        "fixture_id",
        "strategy",
        "plan_seed_hex",
        "seed_free_request_sha256",
        "request_instance_sha256",
        "runtime_lock_sha256",
        "stable_trace_sha256",
        "observable_cell_label",
        "record_sha256",
    )
    if any(type(values[name]) is not int for name in exact_integer_fields) or any(
        type(values[name]) is not str for name in exact_text_fields
    ):
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "interchange scalar type differs")
    first = values["first_selected_attempt_one_based"]
    if first is not None and type(first) is not int:
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "first attempt type differs")
    if type(values["selected"]) is not bool:
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "selected type differs")
    if (
        type(values["selected_feature_ids"]) is not tuple
        or type(values["selected_feature_values"]) is not tuple
    ):
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "feature vector type differs")
    seed = cast(int, values["seed_ordinal"])
    row = cast(int, values["row_ordinal"])
    logical = cast(int, values["logical_request_ordinal"])
    if not 1 <= seed <= CP69_TEST28_SEED_COUNT or not 1 <= row <= 16:
        _fail("CP69_INPUT_ORDINAL_MISMATCH", "seed or row ordinal is out of range")
    expected_logical = (seed - 1) * CP69_TEST28_ROW_COUNT + row
    if logical != expected_logical:
        _fail("CP69_INPUT_ORDINAL_MISMATCH", "logical ordinal breaks seed-major order")
    fixture_id, strategy, budget = _ROW_SHAPES[row - 1]
    if (
        values["row_key"] != _row_key(row)
        or values["fixture_id"] != fixture_id
        or values["strategy"] != strategy
        or values["budget"] != budget
    ):
        _fail("CP69_INPUT_ROW_MISMATCH", "row identity differs")
    if not _is_uint64_hex(values["plan_seed_hex"]):
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "plan seed is not lowercase uint64 hex")
    for name in (
        "seed_free_request_sha256",
        "request_instance_sha256",
        "runtime_lock_sha256",
        "stable_trace_sha256",
        "record_sha256",
    ):
        if not _is_sha256(values[name]):
            _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", name + " is not lowercase SHA-256")
    cells = (
        _REJECTION_OBSERVABLE_CELLS
        if strategy == "bounded-rejection"
        else _SIR_OBSERVABLE_CELLS
    )
    status = cast(str, values["observable_cell_label"])
    if status not in cells:
        _fail("CP69_INPUT_OUTCOME_MISMATCH", "observable status differs by strategy")
    selected = status == cells[0]
    if values["selected"] is not selected:
        _fail("CP69_INPUT_OUTCOME_MISMATCH", "selected flag differs from status")
    if strategy == "bounded-rejection" and selected:
        if type(first) is not int or not 1 <= cast(int, first) <= budget:
            _fail("CP69_INPUT_OUTCOME_MISMATCH", "selected rejection attempt differs")
    elif first is not None:
        _fail("CP69_INPUT_OUTCOME_MISMATCH", "non-rejection selection has an attempt")
    wanted_ordinal = _observable_contribution_ordinal(row, status)
    if values["observable_contribution_ordinal"] != wanted_ordinal:
        _fail(
            "CP69_INPUT_CONTRIBUTION_ORDINAL_MISMATCH",
            "observable contribution ordinal differs",
        )
    feature_ids = cast(tuple, values["selected_feature_ids"])
    feature_values = cast(tuple, values["selected_feature_values"])
    wanted_ids = _feature_ids(fixture_id) if selected else ()
    if (
        feature_ids != wanted_ids
        or any(type(item) is not str for item in feature_ids)
        or len(feature_values) != len(wanted_ids)
        or any(type(item) is not Fraction for item in feature_values)
    ):
        _fail("CP69_INPUT_FEATURE_MISMATCH", "selected feature inventory differs")
    for feature_id, value in zip(feature_ids, feature_values):
        lower, upper = _feature_bounds(feature_id)
        if not lower <= value <= upper:
            _fail(
                "CP69_INPUT_FEATURE_MISMATCH", "selected feature value is out of range"
            )


def _parse_interchange_value(
    value: dict, payload: bytes
) -> CP69CompactInterchangeObservationV1:
    if len(value) != len(_INTERCHANGE_KEYS) or set(value) != set(_INTERCHANGE_KEYS):
        _fail("CP69_INPUT_FIELD_SET_MISMATCH", "interchange field set differs")
    raw_ids = value["selected_feature_ids"]
    raw_values = value["selected_feature_values"]
    if type(raw_ids) is not list or any(type(item) is not str for item in raw_ids):
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "feature id vector type differs")
    if type(raw_values) is not list:
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "feature value vector type differs")
    feature_values = tuple(_fraction_from_tag(item) for item in raw_values)
    semantic = dict(value)
    semantic["selected_feature_ids"] = tuple(raw_ids)
    semantic["selected_feature_values"] = feature_values
    _validate_observation_values(semantic)
    supplied_digest = cast(str, value["record_sha256"])
    digest_body = dict(value)
    digest_body["record_sha256"] = _ZERO_SHA256
    expected_digest = hashlib.sha256(
        _RECORD_DOMAINS[CP69CompactInterchangeObservationV1]
        + b"\0"
        + _decoded_json_bytes(digest_body)
    ).hexdigest()
    if not hmac.compare_digest(supplied_digest, expected_digest):
        _fail("CP69_INPUT_DIGEST_MISMATCH", "interchange record digest differs")
    issued = cast(
        CP69CompactInterchangeObservationV1,
        _record(
            CP69CompactInterchangeObservationV1,
            {name: semantic[name] for name in _INTERCHANGE_KEYS[:-1]},
        ),
    )
    snapshot = cp69_canonical_json_bytes(issued)
    if not hmac.compare_digest(snapshot, payload):
        _fail("CP69_INPUT_CANONICAL_MISMATCH", "issued interchange replay differs")
    return issued


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
    result = []
    for count in range(cap + 1):
        result.append(Fraction(int(len(configuration) == count), 1))
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
    wanted = _feature_ids(fixture_id)
    if len(result) != len(wanted):
        raise AssertionError("CP69 local feature vector count differs")
    return tuple(result)


def _selected_configuration(row_ordinal: int) -> tuple:
    index = _SELECTED_CONFIGURATION_INDEX_BY_ROW[row_ordinal - 1]
    roster = (
        _M1_SELECTED_CONFIGURATION_ROSTER
        if row_ordinal <= 8
        else _M2_SELECTED_CONFIGURATION_ROSTER
    )
    return roster[index]


@lru_cache(maxsize=CP69_TEST28_ROW_COUNT)
def _row_feature_items(
    row_ordinal: int,
) -> Tuple[Tuple[str, Fraction], ...]:
    fixture_id = _ROW_SHAPES[row_ordinal - 1][0]
    return tuple(
        zip(
            _feature_ids(fixture_id),
            _local_feature_vector(fixture_id, _selected_configuration(row_ordinal)),
        )
    )


def _closed_projection_status(
    seed_ordinal: int, row_ordinal: int
) -> Tuple[str, Optional[int], bool]:
    _fixture_id, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    selected_count = CP69_TEST28_SELECTED_COUNTS_BY_ROW[row_ordinal - 1]
    if seed_ordinal <= selected_count:
        if strategy == "bounded-rejection":
            return (
                _REJECTION_OBSERVABLE_CELLS[0],
                (seed_ordinal - 1) % budget + 1,
                True,
            )
        return _SIR_OBSERVABLE_CELLS[0], None, True
    offset = seed_ordinal - selected_count - 1
    if strategy == "bounded-rejection":
        return _REJECTION_OBSERVABLE_CELLS[1 + offset % 4], None, False
    return _SIR_OBSERVABLE_CELLS[1 + offset % 3], None, False


def _synthetic_custody_sha256(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _plain_json_bytes(value)).hexdigest()


def _closed_interchange_values(seed_ordinal: int, row_ordinal: int) -> dict:
    if (
        type(seed_ordinal) is not int
        or type(row_ordinal) is not int
        or not 1 <= seed_ordinal <= CP69_TEST28_SEED_COUNT
        or not 1 <= row_ordinal <= CP69_TEST28_ROW_COUNT
    ):
        _fail("CP69_INPUT_ORDINAL_MISMATCH", "closed fixture ordinal is out of range")
    fixture_id, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    status, first_attempt, selected = _closed_projection_status(
        seed_ordinal, row_ordinal
    )
    logical_ordinal = (seed_ordinal - 1) * CP69_TEST28_ROW_COUNT + row_ordinal
    plan_seed_hex = "%016x" % (seed_ordinal - 1)
    seed_free_sha256 = _SEED_FREE_REQUEST_SHA256S[row_ordinal - 1]
    request_identity = {
        "purpose": "cp69-synthetic-transport-request-custody-sentinel-only",
        "seed_ordinal": seed_ordinal,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": logical_ordinal,
        "plan_seed_hex": plan_seed_hex,
        "seed_free_request_sha256": seed_free_sha256,
    }
    request_sha256 = _synthetic_custody_sha256(
        b"cp69-test28-synthetic-request-instance-custody-sentinel-v1",
        request_identity,
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
        "schema_version": CP69_TEST28_SCHEMA_VERSION,
        "source_semantic_schema_version": _CP63_COMPACT_SCHEMA_VERSION,
        "seed_ordinal": seed_ordinal,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": logical_ordinal,
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


def _interchange_bytes_from_values(values: object) -> bytes:
    """Private anchor/fixture encoder with the same checks as the public parser."""

    if type(values) is not dict:
        _fail("CP69_INPUT_FIELD_TYPE_MISMATCH", "interchange values are not an object")
    supplied = cast(dict, values)
    if set(supplied) != set(_INTERCHANGE_KEYS[:-1]):
        _fail("CP69_INPUT_FIELD_SET_MISMATCH", "interchange value field set differs")
    semantic = dict(supplied)
    semantic["record_sha256"] = _ZERO_SHA256
    _validate_observation_values(semantic)
    record = cast(
        CP69CompactInterchangeObservationV1,
        _record(CP69CompactInterchangeObservationV1, supplied),
    )
    return cp69_canonical_json_bytes(record)


def _closed_interchange_bytes(seed_ordinal: int, row_ordinal: int) -> bytes:
    return _interchange_bytes_from_values(
        _closed_interchange_values(seed_ordinal, row_ordinal)
    )


def _iter_closed_interchange_bytes() -> Iterator[bytes]:
    """Yield the closed byte fixture in seed-major, row-minor order."""

    for seed_ordinal in range(1, CP69_TEST28_SEED_COUNT + 1):
        for row_ordinal in range(1, CP69_TEST28_ROW_COUNT + 1):
            yield _closed_interchange_bytes(seed_ordinal, row_ordinal)


def cp69_parse_compact_interchange_bytes(
    payload: object,
) -> CP69CompactInterchangeObservationV1:
    """Parse one bounded canonical CP69 transport record."""

    try:
        value = _decode_canonical_object(payload)
        return _parse_interchange_value(value, cast(bytes, payload))
    except CP69CompactProjectionInterchangeQualificationError:
        raise
    except MemoryError as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_RESOURCE_EXHAUSTED",
            "the bounded CP69 parser exhausted memory",
        ) from exc
    except Exception as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_INPUT_JSON_INVALID",
            "the bounded CP69 parser failed closed",
        ) from exc


def _require_observation(
    observation: object,
) -> CP69CompactInterchangeObservationV1:
    if type(observation) is not CP69CompactInterchangeObservationV1:
        _fail("CP69_OBSERVATION_TYPE_MISMATCH", "mapper input has the wrong type")
    try:
        issued, _snapshot = _require_issued_record(observation)
    except CP69CompactProjectionInterchangeQualificationError as exc:
        if exc.code == "CP69_RECORD_NOT_ISSUED":
            _fail("CP69_OBSERVATION_NOT_ISSUED", "mapper input was not issued")
        if exc.code == "CP69_RECORD_TAMPERED":
            _fail("CP69_OBSERVATION_TAMPERED", "mapper input was mutated")
        raise
    checked = cast(CP69CompactInterchangeObservationV1, issued)
    values = {item.name: getattr(checked, item.name) for item in fields(type(checked))}
    _validate_observation_values(values)
    return checked


def cp69_to_cp68_projection_view(
    observation: object,
) -> CP69CP68ProjectionViewV1:
    """Map one issued transport observation to the exact CP68 field view."""

    checked = _require_observation(observation)
    return cast(
        CP69CP68ProjectionViewV1,
        _record(
            CP69CP68ProjectionViewV1,
            {
                "schema_version": _CP68_PROJECTION_SCHEMA_VERSION,
                "seed_ordinal": checked.seed_ordinal,
                "row_ordinal": checked.row_ordinal,
                "logical_request_ordinal": checked.logical_request_ordinal,
                "row_key": checked.row_key,
                "fixture_id": checked.fixture_id,
                "strategy": checked.strategy,
                "budget": checked.budget,
                "plan_seed_hex": checked.plan_seed_hex,
                "observable_cell_label": checked.observable_cell_label,
                "first_selected_attempt_one_based": (
                    checked.first_selected_attempt_one_based
                ),
                "selected": checked.selected,
                "selected_feature_ids": checked.selected_feature_ids,
                "selected_feature_values": checked.selected_feature_values,
            },
        ),
    )


def cp69_canonical_json_bytes(value: object) -> bytes:
    """Return canonical bytes for one issued sealed CP69 record."""

    _record_value, snapshot = _require_issued_record(value)
    return snapshot


def cp69_sha256(value: object) -> str:
    """Return the tagged public digest of one issued sealed CP69 record."""

    record, snapshot = _require_issued_record(value)
    return hashlib.sha256(
        b"cp69-public-record-v1\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + snapshot
    ).hexdigest()


def _fixture_digest_payload() -> dict:
    return {
        "schema_version": CP69_TEST28_SCHEMA_VERSION,
        "source_semantic_schema_version": _CP63_COMPACT_SCHEMA_VERSION,
        "target_projection_schema_version": _CP68_PROJECTION_SCHEMA_VERSION,
        "seed_count": CP69_TEST28_SEED_COUNT,
        "row_count": CP69_TEST28_ROW_COUNT,
        "request_count": CP69_TEST28_REQUEST_COUNT,
        "row_shapes": _ROW_SHAPES,
        "rejection_observable_cells": _REJECTION_OBSERVABLE_CELLS,
        "sir_observable_cells": _SIR_OBSERVABLE_CELLS,
        "selected_counts_by_row": CP69_TEST28_SELECTED_COUNTS_BY_ROW,
        "selected_configuration_index_by_row": (_SELECTED_CONFIGURATION_INDEX_BY_ROW),
        "m1_selected_configuration_roster": _M1_SELECTED_CONFIGURATION_ROSTER,
        "m2_selected_configuration_roster": _M2_SELECTED_CONFIGURATION_ROSTER,
        "m1_feature_ids": _feature_ids("T28-M1-Q"),
        "m2_feature_ids": _feature_ids("T28-M2-Q"),
        "interchange_keys": _INTERCHANGE_KEYS,
        "target_projection_keys": _TARGET_PROJECTION_KEYS,
        "seed_free_request_sha256s": _SEED_FREE_REQUEST_SHA256S,
        "development_runtime_lock_sha256": _DEVELOPMENT_RUNTIME_LOCK_SHA256,
        "closed_fixture_plan_seed_formula": "lowercase-16-hex(seed_ordinal-1)",
        "request_custody_is_synthetic_sentinel": True,
        "stable_trace_custody_is_synthetic_no-trace-sentinel": True,
        "provenance_authenticated": False,
        "cp68_fixture_set_sha256": _CP68_FIXTURE_SET_SHA256,
        "cp68_ordered_projection_sha256": _CP68_ORDERED_PROJECTION_SHA256,
    }


@lru_cache(maxsize=1)
def cp69_compact_interchange_fixture_set_sha256() -> str:
    """Return the domain-separated digest of the closed fixture definition."""

    return hashlib.sha256(
        b"cp69-test28-compact-interchange-fixture-set-v1\0"
        + _plain_json_bytes(_fixture_digest_payload())
    ).hexdigest()


def _predecessor_custody() -> CP69PredecessorCustodyV1:
    return cast(
        CP69PredecessorCustodyV1,
        _record(
            CP69PredecessorCustodyV1,
            {
                "schema_version": CP69_TEST28_SCHEMA_VERSION,
                "v19_protocol_sha256": _V19_PROTOCOL_SHA256,
                "v19_protocol_bytes": _V19_PROTOCOL_BYTES,
                "v19_protocol_lf_count": _V19_PROTOCOL_LF_COUNT,
                "v19_manifest_sha256": _V19_MANIFEST_SHA256,
                "v19_manifest_bytes": _V19_MANIFEST_BYTES,
                "v19_manifest_lf_count": _V19_MANIFEST_LF_COUNT,
                "cp61_source_sha256": _CP61_SOURCE_SHA256,
                "cp61_bundle_record_sha256": _CP61_BUNDLE_RECORD_SHA256,
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "cp61_projection_contract_record_sha256": (
                    _CP61_PROJECTION_CONTRACT_RECORD_SHA256
                ),
                "cp63_runner_source_sha256": _CP63_RUNNER_SOURCE_SHA256,
                "cp63_independent_source_sha256": (_CP63_INDEPENDENT_SOURCE_SHA256),
                "cp63_independent_test_sha256": _CP63_INDEPENDENT_TEST_SHA256,
                "cp63_independent_bundle_record_sha256": (
                    _CP63_INDEPENDENT_BUNDLE_RECORD_SHA256
                ),
                "cp63_acceptance_receipt_sha256": (_CP63_ACCEPTANCE_RECEIPT_SHA256),
                "cp63_schedule_contract_record_sha256": (
                    _CP63_SCHEDULE_CONTRACT_RECORD_SHA256
                ),
                "cp67_schedule_expectation_record_sha256": (
                    _CP67_SCHEDULE_EXPECTATION_RECORD_SHA256
                ),
                "cp68_source_sha256": _CP68_SOURCE_SHA256,
                "cp68_test_sha256": _CP68_TEST_SHA256,
                "cp68_bundle_record_sha256": _CP68_BUNDLE_RECORD_SHA256,
                "cp68_qualification_record_sha256": (_CP68_QUALIFICATION_RECORD_SHA256),
                "cp68_synthetic_projection_contract_record_sha256": (
                    _CP68_SYNTHETIC_PROJECTION_CONTRACT_RECORD_SHA256
                ),
                "cp68_aggregation_expectation_record_sha256": (
                    _CP68_AGGREGATION_EXPECTATION_RECORD_SHA256
                ),
                "cp68_fixture_set_sha256": _CP68_FIXTURE_SET_SHA256,
                "cp68_ordered_projection_sha256": (_CP68_ORDERED_PROJECTION_SHA256),
                "cp68_output_canonical_json_sha256": (
                    _CP68_OUTPUT_CANONICAL_JSON_SHA256
                ),
            },
        ),
    )


def _interchange_contract() -> CP69CompactInterchangeContractV1:
    return cast(
        CP69CompactInterchangeContractV1,
        _record(
            CP69CompactInterchangeContractV1,
            {
                "schema_version": CP69_TEST28_SCHEMA_VERSION,
                "contract_id": "cp63-compact-semantics-to-cp68-projection-v1",
                "source_semantic_schema_version": _CP63_COMPACT_SCHEMA_VERSION,
                "target_projection_schema_version": (_CP68_PROJECTION_SCHEMA_VERSION),
                "exact_input_keys": _INTERCHANGE_KEYS,
                "exact_target_keys": _TARGET_PROJECTION_KEYS,
                "canonical_json_profile": (
                    "ascii-rfc8259-sort-keys-no-whitespace-no-bom-no-duplicate-"
                    "keys-no-float-no-nonfinite-exact-types-v1"
                ),
                "exact_fraction_encoding": (
                    "one-key-$fraction-object-containing-two-canonical-"
                    "base10-integer-strings-reduced-positive-denominator"
                ),
                "record_digest_domain": (
                    "cp69-test28-compact-interchange-observation-v1"
                ),
                "target_projection_digest_domain": (
                    "cp68-test28-synthetic-compact-projection-v1"
                ),
                "parser_input_exact_bytes": True,
                "seed_count": CP69_TEST28_SEED_COUNT,
                "row_count": CP69_TEST28_ROW_COUNT,
                "request_count": CP69_TEST28_REQUEST_COUNT,
                "logical_request_order": "seed-major-row-minor",
                "logical_request_ordinal_formula": ("(seed_ordinal-1)*16+row_ordinal"),
                "closed_fixture_plan_seed_formula": (
                    "lowercase-16-hex(seed_ordinal-1)"
                ),
                "observable_contribution_ordinal_recomputed": True,
                "cp63_provenance_fields_transported": True,
                "provenance_authenticated": False,
                "transport_adds_scientific_semantics": False,
                "maximum_interchange_bytes": (CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES),
                "maximum_canonical_depth": CP69_TEST28_MAXIMUM_CANONICAL_DEPTH,
                "maximum_canonical_nodes": CP69_TEST28_MAXIMUM_CANONICAL_NODES,
                "maximum_text_bytes": CP69_TEST28_MAXIMUM_TEXT_BYTES,
                "maximum_integer_bits": CP69_TEST28_MAXIMUM_INTEGER_BITS,
                "maximum_stream_bytes": CP69_TEST28_MAXIMUM_STREAM_BYTES,
            },
        ),
    )


def _full_stream_expectation() -> CP69FullStreamExpectationV1:
    return cast(
        CP69FullStreamExpectationV1,
        _record(
            CP69FullStreamExpectationV1,
            {
                "schema_version": CP69_TEST28_SCHEMA_VERSION,
                "fixture_set_sha256": cp69_compact_interchange_fixture_set_sha256(),
                "request_count": CP69_TEST28_REQUEST_COUNT,
                "selected_counts_by_row": CP69_TEST28_SELECTED_COUNTS_BY_ROW,
                "rejection_selected_count": 8_254,
                "rejection_exhausted_count": 2_034,
                "sir_selected_count": 8_254,
                "refusal_count": 4_744,
                "failure_count": 4_742,
                "timeout_count": 4_740,
                "first_attempt_contribution_count": 8_254,
                "feature_contribution_count": 321_906,
                "first_interchange_record_sha256": (
                    _EXPECTED_FIRST_INTERCHANGE_RECORD_SHA256
                ),
                "ordered_interchange_record_sha256": (
                    _EXPECTED_ORDERED_INTERCHANGE_RECORD_SHA256
                ),
                "first_target_projection_sha256": (_CP68_FIRST_PROJECTION_SHA256),
                "ordered_target_projection_sha256": (_CP68_ORDERED_PROJECTION_SHA256),
                "cp68_output_canonical_json_sha256": (
                    _CP68_OUTPUT_CANONICAL_JSON_SHA256
                ),
            },
        ),
    )


_BUNDLE_LOCK = threading.RLock()
_BUNDLE_CACHE: Optional[CP69CompactProjectionInterchangeQualificationBundleV1] = None


def cp69_compact_projection_interchange_qualification_bundle() -> CP69CompactProjectionInterchangeQualificationBundleV1:
    """Return the pure definition-only CP69 qualification bundle."""

    global _BUNDLE_CACHE
    with _BUNDLE_LOCK:
        if _BUNDLE_CACHE is not None:
            return cast(
                CP69CompactProjectionInterchangeQualificationBundleV1,
                _require_issued_record(_BUNDLE_CACHE)[0],
            )
        _BUNDLE_CACHE = cast(
            CP69CompactProjectionInterchangeQualificationBundleV1,
            _record(
                CP69CompactProjectionInterchangeQualificationBundleV1,
                {
                    "schema_version": CP69_TEST28_SCHEMA_VERSION,
                    "scope": CP69_TEST28_SCOPE,
                    "predecessor_custody": _predecessor_custody(),
                    "interchange_contract": _interchange_contract(),
                    "full_stream_expectation": _full_stream_expectation(),
                    "qualification_fixture_set_sha256": (
                        cp69_compact_interchange_fixture_set_sha256()
                    ),
                    "zero_argument_builder": True,
                    "builder_parses_or_streams": False,
                    "qualification_runner_zero_argument": True,
                    "bounded_public_byte_parser_exposed": True,
                    "sealed_public_projection_mapper_exposed": True,
                    "closed_module_owned_fixture_only": True,
                    "stdlib_only_import": True,
                    "project_modules_imported": False,
                    "streaming_interchange": True,
                    "full_interchange_corpus_materialized": False,
                    "maximum_stream_bytes": CP69_TEST28_MAXIMUM_STREAM_BYTES,
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
                    "formal_test_28_status": CP69_TEST28_FORMAL_TEST_28_STATUS,
                    "formal_test_28_closed": False,
                    "ledger_prerequisite_id": (
                        CP69_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID
                    ),
                    "ledger_prerequisite_state": _LEDGER_PREREQUISITE_STATE,
                    "ledger_total_count": 24,
                    "ledger_satisfied_count": 20,
                    "ledger_missing_count": 4,
                    "development_qualification_only": True,
                },
            ),
        )
        return _BUNDLE_CACHE


def _closed_values_match_observation(
    observation: CP69CompactInterchangeObservationV1,
    seed_ordinal: int,
    row_ordinal: int,
) -> bool:
    expected = _closed_interchange_values(seed_ordinal, row_ordinal)
    return all(getattr(observation, name) == value for name, value in expected.items())


def _reduce_interchange_stream_details(
    payloads: object = None,
    *,
    enforce_frozen_expectation: bool = True,
) -> dict:
    source = _iter_closed_interchange_bytes() if payloads is None else payloads
    try:
        iterator = iter(source)
    except MemoryError:
        raise
    except Exception as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_STREAM_ITERABLE_INVALID",
            "the private interchange source is not iterable",
        ) from exc
    selected_counts = [0] * CP69_TEST28_ROW_COUNT
    status_counts = {
        "rejection-selected": 0,
        "rejection-exhausted": 0,
        "sir-selected": 0,
        "refusal": 0,
        "failure": 0,
        "timeout": 0,
    }
    observable_counts = {
        (row, cell): 0
        for row, (_fixture, strategy, _budget) in enumerate(_ROW_SHAPES, 1)
        for cell in (
            _REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else _SIR_OBSERVABLE_CELLS
        )
    }
    first_attempt_count = 0
    feature_contribution_count = 0
    total_input_bytes = 0
    first_input_sha256: Optional[str] = None
    first_target_sha256: Optional[str] = None
    ordered_input_digest = hashlib.sha256(
        b"cp69-test28-ordered-interchange-record-digests-v1\0"
    )
    ordered_target_digest = hashlib.sha256(
        b"cp68-test28-ordered-projection-digests-v1\0"
    )
    for logical_ordinal in range(1, CP69_TEST28_REQUEST_COUNT + 1):
        try:
            payload = next(iterator)
        except StopIteration as exc:
            raise CP69CompactProjectionInterchangeQualificationError(
                "CP69_STREAM_COUNT_MISMATCH",
                "the interchange stream ended before request 32768",
            ) from exc
        except MemoryError:
            raise
        except Exception as exc:
            raise CP69CompactProjectionInterchangeQualificationError(
                "CP69_STREAM_ITERATION_FAILED",
                "the interchange iterator failed during reduction",
            ) from exc
        observation = cp69_parse_compact_interchange_bytes(payload)
        seed_ordinal = (logical_ordinal - 1) // CP69_TEST28_ROW_COUNT + 1
        row_ordinal = (logical_ordinal - 1) % CP69_TEST28_ROW_COUNT + 1
        if not _closed_values_match_observation(observation, seed_ordinal, row_ordinal):
            _fail(
                "CP69_STREAM_CONTENT_MISMATCH",
                "an interchange record differs from the closed fixture",
            )
        projection = cp69_to_cp68_projection_view(observation)
        if first_input_sha256 is None:
            first_input_sha256 = observation.record_sha256
            first_target_sha256 = projection.projection_sha256
        ordered_input_digest.update(bytes.fromhex(observation.record_sha256))
        ordered_target_digest.update(bytes.fromhex(projection.projection_sha256))
        total_input_bytes += len(cast(bytes, payload))
        if total_input_bytes > CP69_TEST28_MAXIMUM_STREAM_BYTES:
            _fail("CP69_STREAM_RESOURCE_LIMIT", "interchange stream byte cap exceeded")
        status = observation.observable_cell_label
        observable_counts[(row_ordinal, status)] += 1
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
        if observation.first_selected_attempt_one_based is not None:
            first_attempt_count += 1
        if observation.selected:
            selected_counts[row_ordinal - 1] += 1
            feature_contribution_count += len(observation.selected_feature_values)
        del payload, observation, projection
    sentinel = object()
    try:
        extra = next(iterator)
    except StopIteration:
        extra = sentinel
    except MemoryError:
        raise
    except Exception as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_STREAM_ITERATION_FAILED",
            "the interchange iterator failed at its terminal boundary",
        ) from exc
    if extra is not sentinel:
        _fail("CP69_STREAM_COUNT_MISMATCH", "the interchange stream has extra items")
    selected_counts_tuple = tuple(selected_counts)
    observable_row_sums = tuple(
        sum(
            count
            for (candidate_row, _cell), count in observable_counts.items()
            if candidate_row == row
        )
        for row in range(1, CP69_TEST28_ROW_COUNT + 1)
    )
    first_input = cast(str, first_input_sha256)
    first_target = cast(str, first_target_sha256)
    ordered_input = ordered_input_digest.hexdigest()
    ordered_target = ordered_target_digest.hexdigest()
    fixed_totals_match = (
        selected_counts_tuple == CP69_TEST28_SELECTED_COUNTS_BY_ROW
        and observable_row_sums == (CP69_TEST28_SEED_COUNT,) * CP69_TEST28_ROW_COUNT
        and status_counts
        == {
            "rejection-selected": 8_254,
            "rejection-exhausted": 2_034,
            "sir-selected": 8_254,
            "refusal": 4_744,
            "failure": 4_742,
            "timeout": 4_740,
        }
        and first_attempt_count == 8_254
        and feature_contribution_count == 321_906
        and first_target == _CP68_FIRST_PROJECTION_SHA256
        and ordered_target == _CP68_ORDERED_PROJECTION_SHA256
    )
    if not fixed_totals_match:
        _fail(
            "CP69_PROJECTION_EXPECTATION_MISMATCH",
            "the mapped stream differs from frozen CP68 semantics",
        )
    if enforce_frozen_expectation and (
        first_input != _EXPECTED_FIRST_INTERCHANGE_RECORD_SHA256
        or ordered_input != _EXPECTED_ORDERED_INTERCHANGE_RECORD_SHA256
    ):
        _fail(
            "CP69_STREAM_EXPECTATION_MISMATCH",
            "the interchange stream differs from its frozen CP69 pins",
        )
    return {
        "request_count": CP69_TEST28_REQUEST_COUNT,
        "logical_ordinals_complete": True,
        "selected_counts_by_row": selected_counts_tuple,
        "status_counts": status_counts,
        "observable_row_sums": observable_row_sums,
        "first_attempt_contribution_count": first_attempt_count,
        "feature_contribution_count": feature_contribution_count,
        "total_input_bytes": total_input_bytes,
        "first_interchange_record_sha256": first_input,
        "ordered_interchange_record_sha256": ordered_input,
        "first_target_projection_sha256": first_target,
        "ordered_target_projection_sha256": ordered_target,
    }


def _run_compact_projection_interchange_qualification() -> CP69CompactProjectionInterchangeQualificationV1:
    bundle = cp69_compact_projection_interchange_qualification_bundle()
    expected = bundle.full_stream_expectation
    metrics = _reduce_interchange_stream_details()
    matches = (
        metrics["request_count"] == expected.request_count
        and metrics["selected_counts_by_row"] == expected.selected_counts_by_row
        and metrics["status_counts"]
        == {
            "rejection-selected": expected.rejection_selected_count,
            "rejection-exhausted": expected.rejection_exhausted_count,
            "sir-selected": expected.sir_selected_count,
            "refusal": expected.refusal_count,
            "failure": expected.failure_count,
            "timeout": expected.timeout_count,
        }
        and metrics["first_attempt_contribution_count"]
        == expected.first_attempt_contribution_count
        and metrics["feature_contribution_count"] == expected.feature_contribution_count
        and metrics["first_interchange_record_sha256"]
        == expected.first_interchange_record_sha256
        and metrics["ordered_interchange_record_sha256"]
        == expected.ordered_interchange_record_sha256
        and metrics["first_target_projection_sha256"]
        == expected.first_target_projection_sha256
        and metrics["ordered_target_projection_sha256"]
        == expected.ordered_target_projection_sha256
    )
    if not matches:
        _fail(
            "CP69_QUALIFICATION_EXPECTATION_MISMATCH",
            "the qualification receipt differs from its frozen expectation",
        )
    return cast(
        CP69CompactProjectionInterchangeQualificationV1,
        _record(
            CP69CompactProjectionInterchangeQualificationV1,
            {
                "schema_version": CP69_TEST28_SCHEMA_VERSION,
                "fixture_set_sha256": expected.fixture_set_sha256,
                "request_count": metrics["request_count"],
                "logical_ordinals_complete": metrics["logical_ordinals_complete"],
                "streaming_peak_input_payload_count": 1,
                "streaming_peak_parsed_observation_count": 1,
                "streaming_peak_projection_view_count": 1,
                "interchange_corpus_retained": False,
                "canonical_bytes_verified": True,
                "record_digests_verified": True,
                "row_identity_verified": True,
                "observable_contribution_ordinals_verified": True,
                "outcome_and_attempt_semantics_verified": True,
                "selected_feature_semantics_verified": True,
                "selected_counts_by_row": metrics["selected_counts_by_row"],
                "first_attempt_contribution_count": (
                    metrics["first_attempt_contribution_count"]
                ),
                "feature_contribution_count": metrics["feature_contribution_count"],
                "first_interchange_record_sha256": (
                    metrics["first_interchange_record_sha256"]
                ),
                "ordered_interchange_record_sha256": (
                    metrics["ordered_interchange_record_sha256"]
                ),
                "first_target_projection_sha256": (
                    metrics["first_target_projection_sha256"]
                ),
                "ordered_target_projection_sha256": (
                    metrics["ordered_target_projection_sha256"]
                ),
                "target_projection_matches_cp68_expectation": True,
                "raw_record_parsed": False,
                "stable_trace_parsed": False,
                "provenance_authenticated": False,
                "estimate_or_interval_computed": False,
                "decision_path_qualified": False,
                "production_evidence": False,
                "production_execution_authorized": False,
                "runner_and_recomputation_blocker_closed": False,
                "formal_test_28_closed": False,
                "all_development_qualification_checks_passed": matches,
            },
        ),
    )


_QUALIFICATION_LOCK = threading.RLock()


def cp69_run_compact_projection_interchange_qualification() -> CP69CompactProjectionInterchangeQualificationV1:
    """Run the closed zero-I/O 32,768-item transport qualification."""

    try:
        with _QUALIFICATION_LOCK:
            return _run_compact_projection_interchange_qualification()
    except CP69CompactProjectionInterchangeQualificationError:
        raise
    except MemoryError as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_RESOURCE_EXHAUSTED",
            "the closed CP69 qualification exceeded its memory boundary",
        ) from exc
    except Exception as exc:
        raise CP69CompactProjectionInterchangeQualificationError(
            "CP69_QUALIFICATION_FAILURE",
            "the closed source-independent CP69 qualification failed",
        ) from exc


__all__ = (
    "CP69_TEST28_SCHEMA_VERSION",
    "CP69_TEST28_SCOPE",
    "CP69_TEST28_FORMAL_TEST_28_STATUS",
    "CP69_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP69_TEST28_SEED_COUNT",
    "CP69_TEST28_ROW_COUNT",
    "CP69_TEST28_REQUEST_COUNT",
    "CP69_TEST28_OBSERVABLE_ESTIMAND_COUNT",
    "CP69_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
    "CP69_TEST28_FEATURE_ESTIMAND_COUNT",
    "CP69_TEST28_ESTIMAND_COUNT",
    "CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES",
    "CP69_TEST28_MAXIMUM_CANONICAL_DEPTH",
    "CP69_TEST28_MAXIMUM_CANONICAL_NODES",
    "CP69_TEST28_MAXIMUM_TEXT_BYTES",
    "CP69_TEST28_MAXIMUM_INTEGER_BITS",
    "CP69_TEST28_MAXIMUM_STREAM_BYTES",
    "CP69_TEST28_SELECTED_COUNTS_BY_ROW",
    "CP69CompactProjectionInterchangeQualificationError",
    "CP69PredecessorCustodyV1",
    "CP69CompactInterchangeContractV1",
    "CP69CompactInterchangeObservationV1",
    "CP69CP68ProjectionViewV1",
    "CP69FullStreamExpectationV1",
    "CP69CompactProjectionInterchangeQualificationV1",
    "CP69CompactProjectionInterchangeQualificationBundleV1",
    "cp69_parse_compact_interchange_bytes",
    "cp69_to_cp68_projection_view",
    "cp69_canonical_json_bytes",
    "cp69_sha256",
    "cp69_compact_interchange_fixture_set_sha256",
    "cp69_compact_projection_interchange_qualification_bundle",
    "cp69_run_compact_projection_interchange_qualification",
)
