"""Closed development-only CP67 full-schedule materializer qualification.

The module defines one module-owned synthetic 2,048-seed capsule fixture and
the exact in-memory translation to the CP65 32,768-request schedule shape.
The public definition builder is pure and does not materialize the capsule or
schedule.  The zero-argument qualification runner is the only execution
boundary; it imports CP63 and the two CP65 validators lazily, performs no
filesystem or process activity, discards the large payload, and returns a
compact nonconfirmatory receipt.

Only the Python standard library is imported at module import time.  Nothing
in this module authenticates a seed source, a freeze receipt, a runtime, or a
production schedule, and nothing authorizes or performs production execution.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import hmac
import json
import threading
from typing import Mapping, Optional, Tuple, cast
import weakref


CP67_TEST28_SCHEMA_VERSION = "cp67-test28-full-schedule-materializer-qualification-v1"
CP67_TEST28_SCOPE = (
    "development-only-full-32768-request-schedule-materializer-qualification;"
    "one-module-owned-synthetic-capsule;zero-argument-runner;in-memory-only;"
    "cp63-syntax-and-bound-request-exemplars;dual-cp65-validation;"
    "no-public-input-api;no-filesystem;no-clock;no-rng;no-network;"
    "no-subprocess;no-external-seed-law;no-freeze-authentication;"
    "no-production-schedule;no-runner-or-campaign;no-production-execution;"
    "no-estimate-interval-or-decision;no-evidence-acceptance;"
    "no-gate-or-blocker-closure"
)

CP67_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP67_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID = (
    "whole_seed_full_schedule_materializer_qualification"
)
CP67_TEST28_SEED_COUNT = 2_048
CP67_TEST28_ROW_COUNT = 16
CP67_TEST28_REQUEST_COUNT = 32_768
CP67_TEST28_SEED_CAPSULE_MAX_BYTES = 131_072
CP67_TEST28_SCHEDULE_MAX_BYTES = 67_108_864
CP67_TEST28_EXPECTED_VALIDATED_DIGEST_PREIMAGE_COUNT = 98_307
CP67_TEST28_EXPECTED_UNRESOLVED_DIGEST_PREIMAGE_COUNT = 65_539
CP67_TEST28_EXPECTED_VALIDATED_CROSS_BINDING_COUNT = 0
CP67_TEST28_EXPECTED_UNRESOLVED_CROSS_BINDING_COUNT = 3

_LEDGER_PREREQUISITE_STATE = (
    "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS"
)

_V17_PROTOCOL_SHA256 = (
    "7805865a4e988e0b3de75a702d9310228ac2da999d3413dc53aba2ee01c95516"
)
_V17_MANIFEST_SHA256 = (
    "1129896e5de5858e7d8714bd75d9a32629974b4efbcea6fd13ce9fcedef65339"
)
_CP61_SOURCE_SHA256 = "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_CP62_BUNDLE_RECORD_SHA256 = (
    "0f92f54ce8d451485019f6d697736fd5eb48d2b942e1d3a3f1bd373b50c3ec92"
)
_CP63_SOURCE_SHA256 = "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
_CP63_RUNNER_BUNDLE_RECORD_SHA256 = (
    "442c4b0f134a96efe32b5246b4eb5b05233d61a13c62c0a7d1f21c9bbbd32f85"
)
_CP63_SEED_CAPSULE_CONTRACT_RECORD_SHA256 = (
    "1765adf642962c73b61634dde767fe9d2c2fef5fd71c21305fe43c6d338cf80d"
)
_CP63_SCHEDULE_CONTRACT_RECORD_SHA256 = (
    "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
)
_CP63_RUNTIME_LOCK_RECORD_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_CP65_AUTHORITATIVE_SOURCE_SHA256 = (
    "774cd44ad6aa82ea629ef705bde3bbb7288ccd74bd0d3a5d5c79f552a5f6a06a"
)
_CP65_INDEPENDENT_SOURCE_SHA256 = (
    "503306d1005af2acfe2f77c0bc1dd89d9b1b003e0a35136b5a77efcae81b0c1b"
)
_CP65_BUNDLE_RECORD_SHA256 = (
    "597f2b4b557bffb529d951858fd84e454135220db0c19dcd05fcf7ce93710f89"
)
_CP65_INDEPENDENT_BUNDLE_RECORD_SHA256 = (
    "f34b5e4463a8ab881ac81378b3162b2b73a961be12a1e83d59341a0ff7b6af52"
)
_CP65_SCHEMA_SEMANTIC_SHA256 = (
    "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
)
_CP65_PRODUCTION_SCHEDULE_SCHEMA_RECORD_SHA256 = (
    "96da33ac756d0f66a5bd105deab41fe695bc00337772862578b326d9519d47c4"
)
_CP65_SCHEDULE_REQUEST_ROW_DIGEST_CONTRACT_RECORD_SHA256 = (
    "9f624c3f5701a8343144bf7c2ae150aaee12a4279c1ffe694ae30dc40295c60c"
)
_CP65_SCHEDULE_ORDERED_REQUEST_DIGEST_CONTRACT_RECORD_SHA256 = (
    "c93ef095d30762912f52949fbc08074f0c0f3f93ca5ebe954a36916c8693fb72"
)
_CP66_SOURCE_SHA256 = "54eab1ec63ee280cf6741ffc9611f7012678c633c044d8131138314a6abc2861"
_CP66_BUNDLE_RECORD_SHA256 = (
    "409a3ad764c1f12e0212d1c63de8bf32df36380287f39a81a9f82c4674cecec2"
)
_CP66_TEST_SHA256 = "5913e37c2c3f784b62a091ebdb82745c7d43e1acd85cd7942a68a0780bc1e55c"
_CP66_QUALIFICATION_FIXTURE_SET_SHA256 = (
    "a8a763a14097f2831258c2451df4daab344125d3d48a725758620a7e783920d5"
)

_CP63_SCHEMA_VERSION = "cp63-test28-runner-recomputation-rehearsal-v1"
_CP63_CAPSULE_PURPOSE = "future-production-external-iid-uniform-uint64-with-replacement"
_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP65_SCHEDULE_SCHEMA = "cp65-test28-production-schedule-v1"
_CP65_SCHEDULE_PURPOSE = "production-request-schedule-custody"
_DEVELOPMENT_CASE_ID = "development-seeds-0000-through-07ff"
_DEVELOPMENT_CASE_PURPOSE = (
    "closed-development-full-schedule-materializer-qualification"
)
_DEVELOPMENT_SOURCE_METHOD_ID = "development-synthetic-no-source-law"
_DEVELOPMENT_ATTEMPT_ID = "attempt-cp67-development-only"
_DEVELOPMENT_SOURCE_RECEIPT_SHA256 = (
    "386cdfc1e3bbd5f7246f784fbb96a2a3bc0f917f46cb1034b682f6eb9dff9a5c"
)
_DEVELOPMENT_ACQUISITION_SESSION_SHA256 = (
    "ce410ba7d37f0c2d541f7984c7bbc2891fd644b866e4894476afdfd3e9ca45ce"
)
_DEVELOPMENT_FREEZE_RECEIPT_SHA256 = (
    "40e5b236a608a00a50bade2de14154bb23214abc9d7984e50c6401de4dcb1ed7"
)
_DEVELOPMENT_ORDERED_SEED_VALUES_SHA256 = (
    "cc2f7772823c44e3c417b4aa941268d4ffd464b9fd15a43fb8cc46c7aa531c09"
)
_DEVELOPMENT_CAPSULE_BODY_SHA256 = (
    "f4854575583657c85d912816b6938503c9882fc488ff46f9b2407ba288cb8164"
)
_DEVELOPMENT_CAPSULE_RAW_SHA256 = (
    "48a171ca9e17561830297a96d7a98777266c04e91eccb2db4c7d91111fa62422"
)
_DEVELOPMENT_CAPSULE_BYTES = 48_711
_DEVELOPMENT_SCHEDULE_BODY_SHA256 = (
    "8e9156150a5666e5986d6e71eb0563c6e72aee2faa9bf013e1b47a99e2fda798"
)
_DEVELOPMENT_SCHEDULE_RAW_SHA256 = (
    "c830af2b1ff54e14dd6684d935a45bb1eabcf90abaa3ebe68e38a06c9176b544"
)
_DEVELOPMENT_SCHEDULE_BYTES = 26_749_445
_DEVELOPMENT_ORDERED_REQUESTS_SHA256 = (
    "ef4a97159d9b5e4828f5fc60c314d34ec48eeaa9a02c784c0dba654cd6b17be9"
)
_DEVELOPMENT_FIRST_REQUEST_ROW_SHA256 = (
    "72755276c4acb052d2148a26613d6b0ae4291e91d20c287b74014a9eb267b17f"
)
_DEVELOPMENT_LAST_REQUEST_ROW_SHA256 = (
    "8346f0a5f538d3fc2f065411da2d99f11736d9ae6237b9c5f04cccd6da803512"
)
_QUALIFICATION_FIXTURE_SET_SHA256 = (
    "e5f48b09da24f6a98d1fb3fa0e903dffb306db56233001c1dc6eaa742a2f2a0c"
)
_AUTHORITATIVE_VALIDATION_RECORD_SHA256 = (
    "8b9cc46bf3944f109b602f3a0a4ed2ef2c29bae06f5580d1d48ab833528fae68"
)
_INDEPENDENT_VALIDATION_RECORD_SHA256 = (
    "bc57a8fd08754b97176622f7543cc63725f8c89fa57bb779042e72f1c0d9eefa"
)

_ZERO_SHA256 = "0" * 64
_ALLOW_RECORD_CLASS_DEFINITION = True
_MAXIMUM_CANONICAL_DEPTH = 64
_MAXIMUM_CANONICAL_NODE_COUNT = 1_048_576
_MAXIMUM_CANONICAL_KEY_CHARACTERS = 256
_MAXIMUM_CANONICAL_STRING_CHARACTERS = 131_072
_MAXIMUM_CANONICAL_INTEGER_ABSOLUTE = 2**63 - 1
_MAXIMUM_CANONICAL_BYTES = CP67_TEST28_SCHEDULE_MAX_BYTES
_MAXIMUM_CANONICAL_RECORD_BYTES = CP67_TEST28_SEED_CAPSULE_MAX_BYTES

_CAPSULE_KEYS = (
    "schema",
    "purpose",
    "cp61_stable_design_sha256",
    "seed_count",
    "seed_ordinals",
    "seed_encoding",
    "ordered_seed_values",
    "source_method_id",
    "source_receipt_sha256",
    "acquisition_session_sha256",
    "body_sha256",
)
_REQUEST_KEYS = (
    "schema_version",
    "seed_capsule_body_sha256",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "seed_free_request_sha256",
    "runtime_lock_sha256",
    "request_instance_sha256",
    "request_row_sha256",
)
_SCHEDULE_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "seed_capsule_body_sha256",
    "schedule_contract_sha256",
    "request_count",
    "requests",
    "ordered_request_record_sha256s",
    "ordered_requests_sha256",
    "body_sha256",
)
_CP63_BOUND_REQUEST_CALL_LOGICAL_ORDINALS = tuple(range(1, 18)) + (
    32_752,
    32_753,
    32_768,
)

_ROW_INVENTORY = (
    (
        1,
        "row-01/T28-M1-Q/bounded-rejection/budget-1",
        "T28-M1-Q",
        "bounded-rejection",
        1,
        "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a",
    ),
    (
        2,
        "row-02/T28-M1-Q/bounded-rejection/budget-4",
        "T28-M1-Q",
        "bounded-rejection",
        4,
        "f9f2d4f1d8aad14bbe5075b4febd763af4652fb4dda337e7a8d295b3a6045ec2",
    ),
    (
        3,
        "row-03/T28-M1-Q/bounded-rejection/budget-16",
        "T28-M1-Q",
        "bounded-rejection",
        16,
        "4413d707c0165dbf18e88df043edd760a75d4eed44d039a611402e06de9c4eb8",
    ),
    (
        4,
        "row-04/T28-M1-Q/bounded-rejection/budget-64",
        "T28-M1-Q",
        "bounded-rejection",
        64,
        "29f1f28fb222d258746cb7956a9ca0d65a6e97d398eddb1612720a9339eed338",
    ),
    (
        5,
        "row-05/T28-M1-Q/fixed-budget-sir/budget-8",
        "T28-M1-Q",
        "fixed-budget-sir",
        8,
        "71701768f889fee219b854217de255f3d034202a3a66875ceade1cd55955896a",
    ),
    (
        6,
        "row-06/T28-M1-Q/fixed-budget-sir/budget-32",
        "T28-M1-Q",
        "fixed-budget-sir",
        32,
        "bd7c4fd661bda70f29b8582c0db52d91d68fc703ae8838295a21cf9e6e55f23a",
    ),
    (
        7,
        "row-07/T28-M1-Q/fixed-budget-sir/budget-128",
        "T28-M1-Q",
        "fixed-budget-sir",
        128,
        "801f600536240a2f6f3de0dcac8d4092c2121fd17dc14fb0ca0bfc3b0260acb8",
    ),
    (
        8,
        "row-08/T28-M1-Q/fixed-budget-sir/budget-512",
        "T28-M1-Q",
        "fixed-budget-sir",
        512,
        "8e5458a8dfca1e49875cad53deff7447274ce3055960a0031cc07c4ec4de33e0",
    ),
    (
        9,
        "row-09/T28-M2-Q/bounded-rejection/budget-1",
        "T28-M2-Q",
        "bounded-rejection",
        1,
        "7d32b4e85d39504864268b7ba39189f17c3171d11079638e37a6614b97a543bf",
    ),
    (
        10,
        "row-10/T28-M2-Q/bounded-rejection/budget-4",
        "T28-M2-Q",
        "bounded-rejection",
        4,
        "17f11b448585709ef35a172e86665c83b2ea50a907caacdd400dbd8ce625771b",
    ),
    (
        11,
        "row-11/T28-M2-Q/bounded-rejection/budget-16",
        "T28-M2-Q",
        "bounded-rejection",
        16,
        "57937405e7302fcd9b9935050050a74e4b2c2818e17d720cde1ee2a56352bcf3",
    ),
    (
        12,
        "row-12/T28-M2-Q/bounded-rejection/budget-64",
        "T28-M2-Q",
        "bounded-rejection",
        64,
        "878797b61ec628ae5db0e882d6f3c34531468fbbc35fd92325063a3b017c1bd8",
    ),
    (
        13,
        "row-13/T28-M2-Q/fixed-budget-sir/budget-8",
        "T28-M2-Q",
        "fixed-budget-sir",
        8,
        "bc7b374f072aa402264634bcf520834a71609af5f6705b9b8ac3079884cd0376",
    ),
    (
        14,
        "row-14/T28-M2-Q/fixed-budget-sir/budget-32",
        "T28-M2-Q",
        "fixed-budget-sir",
        32,
        "1b60b917c4fba30085678101276fe2a210aaa82f34deb6ad4f9440a38cc3b074",
    ),
    (
        15,
        "row-15/T28-M2-Q/fixed-budget-sir/budget-128",
        "T28-M2-Q",
        "fixed-budget-sir",
        128,
        "a88491906e47ec4f5483b638ce411b8afd4ce7b5d73f19e372ab68a405f6d81c",
    ),
    (
        16,
        "row-16/T28-M2-Q/fixed-budget-sir/budget-512",
        "T28-M2-Q",
        "fixed-budget-sir",
        512,
        "0667c6c19a9b54db91f2167f685abdcaafcab73cbc4bcfaebcb420511ecc89c8",
    ),
)


class CP67ScheduleMaterializerQualificationError(RuntimeError):
    """Fail-closed CP67 error carrying a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP67 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP67 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP67 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP67PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    v17_protocol_sha256: str
    v17_protocol_bytes: int
    v17_protocol_lf_count: int
    v17_manifest_sha256: str
    v17_manifest_bytes: int
    v17_manifest_lf_count: int
    cp61_source_sha256: str
    cp61_stable_design_sha256: str
    cp62_source_sha256: str
    cp62_bundle_record_sha256: str
    cp62_runtime_lock_record_sha256: str
    cp63_runner_source_sha256: str
    cp63_runner_bundle_record_sha256: str
    cp63_seed_capsule_contract_record_sha256: str
    cp63_schedule_contract_record_sha256: str
    cp65_authoritative_source_sha256: str
    cp65_authoritative_bundle_record_sha256: str
    cp65_independent_source_sha256: str
    cp65_independent_bundle_record_sha256: str
    cp65_schema_semantic_sha256: str
    cp65_production_schedule_schema_record_sha256: str
    cp65_schedule_request_row_digest_contract_record_sha256: str
    cp65_schedule_ordered_request_digest_contract_record_sha256: str
    cp66_source_sha256: str
    cp66_test_sha256: str
    cp66_bundle_record_sha256: str
    cp66_qualification_fixture_set_sha256: str
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP67DevelopmentSeedCapsuleFixtureV1(_SealedRecord):
    schema_version: str
    case_ordinal: int
    case_id: str
    cp61_stable_design_sha256: str
    capsule_schema: str
    capsule_purpose: str
    seed_count: int
    seed_ordinal_min: int
    seed_ordinal_max: int
    seed_encoding: str
    seed_value_formula: str
    minimum_seed_hex: str
    maximum_seed_hex: str
    distinct_seed_value_count: int
    ordered_seed_values_digest_domain: str
    ordered_seed_values_sha256: str
    source_method_id: str
    source_receipt_digest_domain: str
    source_receipt_sha256: str
    acquisition_session_digest_domain: str
    acquisition_session_sha256: str
    capsule_body_digest_domain: str
    seed_capsule_body_sha256: str
    seed_capsule_canonical_json_bytes: int
    seed_capsule_canonical_json_sha256: str
    module_owned_fixture: bool
    caller_supplied_seed_or_capsule_accepted: bool
    external_seed_source_bound: bool
    iid_uniform_with_replacement_verified: bool
    production_seed_capsule: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP67ScheduleMaterializerContractV1(_SealedRecord):
    schema_version: str
    contract_id: str
    development_case_id: str
    cp63_seed_capsule_contract_record_sha256: str
    cp63_schedule_contract_record_sha256: str
    cp65_production_schedule_schema_record_sha256: str
    seed_count: int
    row_count: int
    request_count: int
    logical_request_order: str
    plan_seed_assignment: str
    schedule_schema: str
    schedule_purpose: str
    development_attempt_id: str
    synthetic_freeze_receipt_digest_domain: str
    synthetic_freeze_receipt_sha256: str
    synthetic_freeze_digest_is_receipt: bool
    request_instance_digest_domain: str
    request_row_digest_domain: str
    ordered_requests_digest_domain: str
    schedule_body_digest_domain: str
    seed_capsule_max_bytes: int
    schedule_max_bytes: int
    cp63_direct_seed_capsule_parser_call_count: int
    cp63_effective_seed_capsule_parser_call_count: int
    cp63_bound_request_logical_ordinals: Tuple[int, ...]
    cp63_bound_request_call_count: int
    all_row_shapes_sampled_by_cp63: bool
    all_seed_boundary_shapes_sampled_by_cp63: bool
    remaining_rows_generated_from_frozen_formula: bool
    dual_cp65_validator_required: bool
    in_memory_only: bool
    schedule_bytes_retained: bool
    filesystem_write_permitted: bool
    generic_seed_or_capsule_api_exposed: bool
    production_materialization_api_exposed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP67ScheduleMaterializationExpectationV1(_SealedRecord):
    schema_version: str
    case_id: str
    qualification_fixture_set_digest_domain: str
    qualification_fixture_set_sha256: str
    seed_capsule_canonical_json_bytes: int
    seed_capsule_canonical_json_sha256: str
    schedule_canonical_json_bytes: int
    schedule_canonical_json_sha256: str
    schedule_body_sha256: str
    ordered_requests_sha256: str
    first_request_row_sha256: str
    last_request_row_sha256: str
    request_count: int
    unique_request_instance_sha256_count: int
    unique_request_row_sha256_count: int
    expected_cp65_validated_digest_preimage_count: int
    expected_cp65_unresolved_digest_preimage_count: int
    expected_cp65_validated_cross_binding_count: int
    expected_cp65_unresolved_cross_binding_count: int
    authoritative_cp65_validation_record_sha256: str
    independent_cp65_validation_record_sha256: str
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP67ScheduleMaterializationQualificationV1(_SealedRecord):
    schema_version: str
    case_id: str
    qualification_fixture_set_sha256: str
    cp63_direct_seed_capsule_parser_call_count: int
    cp63_effective_seed_capsule_parser_call_count: int
    cp63_bound_request_logical_ordinals: Tuple[int, ...]
    cp63_bound_request_call_count: int
    cp63_capsule_syntactically_valid: bool
    cp63_source_custody_digest_bound: bool
    cp63_iid_uniform_with_replacement_verified: bool
    cp63_production_execution_authorized: bool
    cp63_bound_request_exemplar_parity_verified: bool
    all_32768_requests_materialized: bool
    seed_major_order_verified: bool
    all_plan_seed_values_unchanged_across_sixteen_rows: bool
    schedule_canonical_json_bytes: int
    schedule_canonical_json_sha256: str
    schedule_body_sha256: str
    ordered_requests_sha256: str
    first_request_row_sha256: str
    last_request_row_sha256: str
    unique_request_instance_sha256_count: int
    unique_request_row_sha256_count: int
    authoritative_cp65_syntax_valid: bool
    authoritative_cp65_intrinsic_digest_preimages_valid: bool
    authoritative_cp65_all_required_digest_preimage_sources_supplied: bool
    authoritative_cp65_validated_digest_preimage_count: int
    authoritative_cp65_unresolved_digest_preimage_count: int
    authoritative_cp65_digest_preimages_valid: bool
    authoritative_cp65_all_required_cross_binding_targets_supplied: bool
    authoritative_cp65_validated_cross_binding_count: int
    authoritative_cp65_unresolved_cross_binding_count: int
    authoritative_cp65_cross_bindings_valid: bool
    authoritative_cp65_production_evidence_accepted: bool
    authoritative_cp65_execution_permitted: bool
    authoritative_cp65_validation_record_sha256: str
    independent_cp65_syntax_valid: bool
    independent_cp65_intrinsic_digest_preimages_valid: bool
    independent_cp65_all_required_digest_preimage_sources_supplied: bool
    independent_cp65_validated_digest_preimage_count: int
    independent_cp65_unresolved_digest_preimage_count: int
    independent_cp65_digest_preimages_valid: bool
    independent_cp65_all_required_cross_binding_targets_supplied: bool
    independent_cp65_validated_cross_binding_count: int
    independent_cp65_unresolved_cross_binding_count: int
    independent_cp65_cross_bindings_valid: bool
    independent_cp65_production_evidence_accepted: bool
    independent_cp65_execution_permitted: bool
    independent_cp65_validation_record_sha256: str
    dual_validator_structural_results_equal: bool
    schedule_matches_frozen_expectation: bool
    production_seed_capsule_present: bool
    production_schedule_instantiated: bool
    production_gate_7_evidence_present: bool
    production_gate_7_state: str
    production_execution_authorized: bool
    runner_and_recomputation_blocker_closed: bool
    formal_test_28_closed: bool
    all_development_qualification_checks_passed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP67FullScheduleMaterializerQualificationBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    predecessor_custody: CP67PredecessorCustodyV1
    development_seed_capsule_fixture: CP67DevelopmentSeedCapsuleFixtureV1
    schedule_materializer_contract: CP67ScheduleMaterializerContractV1
    schedule_materialization_expectation: CP67ScheduleMaterializationExpectationV1
    qualification_fixture_set_sha256: str
    qualification_case_count: int
    zero_argument_builder: bool
    builder_materializes_schedule: bool
    qualification_runner_zero_argument: bool
    closed_module_owned_fixture_only: bool
    stdlib_only_import: bool
    project_modules_imported_by_builder: bool
    cp63_cp65_modules_lazy_imported_by_qualification_runner: bool
    host_filesystem_probed: bool
    clock_read: bool
    rng_used: bool
    network_used: bool
    subprocess_api_exposed: bool
    filesystem_path_api_exposed: bool
    generic_seed_or_capsule_api_exposed: bool
    production_materialization_api_exposed: bool
    production_seed_capsule_present: bool
    external_seed_source_bound: bool
    iid_uniform_with_replacement_verified: bool
    production_schedule_instantiated: bool
    production_gate_7_evidence_present: bool
    production_gate_7_state: str
    production_requests_materialized: bool
    production_campaign_exposed: bool
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
    CP67PredecessorCustodyV1: b"cp67-test28-predecessor-custody-v1",
    CP67DevelopmentSeedCapsuleFixtureV1: (
        b"cp67-test28-development-seed-capsule-fixture-v1"
    ),
    CP67ScheduleMaterializerContractV1: (
        b"cp67-test28-schedule-materializer-contract-v1"
    ),
    CP67ScheduleMaterializationExpectationV1: (
        b"cp67-test28-schedule-materialization-expectation-v1"
    ),
    CP67ScheduleMaterializationQualificationV1: (
        b"cp67-test28-schedule-materialization-qualification-v1"
    ),
    CP67FullScheduleMaterializerQualificationBundleV1: (
        b"cp67-test28-full-schedule-materializer-qualification-bundle-v1"
    ),
}
_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS = cast(
    "weakref.WeakKeyDictionary[_SealedRecord, bytes]",
    weakref.WeakKeyDictionary(),
)


def _canonical_resource_violation() -> CP67ScheduleMaterializerQualificationError:
    return CP67ScheduleMaterializerQualificationError(
        "CP67_CANONICAL_RESOURCE_VIOLATION",
        "the CP67 canonical value exceeds its closed graph limits",
    )


def _plain_json_value(
    value: object,
    *,
    _depth: int = 0,
    _node_count: Optional[list] = None,
    _canonical_byte_count: Optional[list] = None,
    _active_container_ids: Optional[set] = None,
    _maximum_bytes: int = _MAXIMUM_CANONICAL_BYTES,
) -> object:
    if _node_count is None:
        _node_count = [0]
    if _canonical_byte_count is None:
        _canonical_byte_count = [0]
    if _active_container_ids is None:
        _active_container_ids = set()
    _node_count[0] += 1
    if (
        _depth > _MAXIMUM_CANONICAL_DEPTH
        or _node_count[0] > _MAXIMUM_CANONICAL_NODE_COUNT
    ):
        raise _canonical_resource_violation()
    if value is None:
        _canonical_byte_count[0] += 4
        if _canonical_byte_count[0] > _maximum_bytes:
            raise _canonical_resource_violation()
        return value
    if type(value) is bool:
        _canonical_byte_count[0] += 4 if value else 5
        if _canonical_byte_count[0] > _maximum_bytes:
            raise _canonical_resource_violation()
        return value
    if type(value) is int:
        if abs(cast(int, value)) > _MAXIMUM_CANONICAL_INTEGER_ABSOLUTE:
            raise _canonical_resource_violation()
        _canonical_byte_count[0] += len(str(value))
        if _canonical_byte_count[0] > _maximum_bytes:
            raise _canonical_resource_violation()
        return value
    if type(value) is str:
        if len(cast(str, value)) > _MAXIMUM_CANONICAL_STRING_CHARACTERS:
            raise _canonical_resource_violation()
        _canonical_byte_count[0] += len(json.dumps(cast(str, value), ensure_ascii=True))
        if _canonical_byte_count[0] > _maximum_bytes:
            raise _canonical_resource_violation()
        return value
    if type(value) in (tuple, list, dict) or isinstance(value, _SealedRecord):
        identity = id(value)
        if identity in _active_container_ids:
            raise _canonical_resource_violation()
        _active_container_ids.add(identity)
        try:
            if type(value) in (tuple, list):
                sequence = cast(tuple, value)
                _canonical_byte_count[0] += 2 + max(0, len(sequence) - 1)
                if _canonical_byte_count[0] > _maximum_bytes:
                    raise _canonical_resource_violation()
                return [
                    _plain_json_value(
                        item,
                        _depth=_depth + 1,
                        _node_count=_node_count,
                        _canonical_byte_count=_canonical_byte_count,
                        _active_container_ids=_active_container_ids,
                        _maximum_bytes=_maximum_bytes,
                    )
                    for item in sequence
                ]
            if type(value) is dict:
                result = {}
                mapping = cast(dict, value)
                _canonical_byte_count[0] += 2 + max(0, len(mapping) - 1)
                if _canonical_byte_count[0] > _maximum_bytes:
                    raise _canonical_resource_violation()
                for key, item in mapping.items():
                    if type(key) is not str:
                        raise TypeError("CP67 JSON object keys must be exact strings")
                    if len(key) > _MAXIMUM_CANONICAL_KEY_CHARACTERS:
                        raise _canonical_resource_violation()
                    _canonical_byte_count[0] += (
                        len(json.dumps(key, ensure_ascii=True)) + 1
                    )
                    if _canonical_byte_count[0] > _maximum_bytes:
                        raise _canonical_resource_violation()
                    result[key] = _plain_json_value(
                        item,
                        _depth=_depth + 1,
                        _node_count=_node_count,
                        _canonical_byte_count=_canonical_byte_count,
                        _active_container_ids=_active_container_ids,
                        _maximum_bytes=_maximum_bytes,
                    )
                return result
            record_fields = fields(type(value))
            _canonical_byte_count[0] += 2 + max(0, len(record_fields) - 1)
            if _canonical_byte_count[0] > _maximum_bytes:
                raise _canonical_resource_violation()
            for item in record_fields:
                if len(item.name) > _MAXIMUM_CANONICAL_KEY_CHARACTERS:
                    raise _canonical_resource_violation()
                _canonical_byte_count[0] += (
                    len(json.dumps(item.name, ensure_ascii=True)) + 1
                )
                if _canonical_byte_count[0] > _maximum_bytes:
                    raise _canonical_resource_violation()
            return {
                item.name: _plain_json_value(
                    getattr(value, item.name),
                    _depth=_depth + 1,
                    _node_count=_node_count,
                    _canonical_byte_count=_canonical_byte_count,
                    _active_container_ids=_active_container_ids,
                    _maximum_bytes=_maximum_bytes,
                )
                for item in record_fields
            }
        finally:
            _active_container_ids.remove(identity)
    raise TypeError("value has no CP67 canonical JSON representation")


def _plain_json_bytes(
    value: object, *, maximum_bytes: int = _MAXIMUM_CANONICAL_BYTES
) -> bytes:
    try:
        node_count = [0]
        canonical_byte_count = [0]
        plain = _plain_json_value(
            value,
            _node_count=node_count,
            _canonical_byte_count=canonical_byte_count,
            _maximum_bytes=maximum_bytes,
        )
        encoded = json.dumps(
            plain,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        if len(encoded) != canonical_byte_count[0] or len(encoded) > maximum_bytes:
            raise _canonical_resource_violation()
        return encoded
    except RecursionError as exc:
        raise _canonical_resource_violation() from exc


def _record(cls: type, values: Mapping[str, object]) -> object:
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP67 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    provisional = object.__new__(cls)
    for name in names:
        object.__setattr__(provisional, name, complete[name])
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls]
        + b"\0"
        + _plain_json_bytes(provisional, maximum_bytes=_MAXIMUM_CANONICAL_RECORD_BYTES)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _plain_json_bytes(result, maximum_bytes=_MAXIMUM_CANONICAL_RECORD_BYTES)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = snapshot
    return result


def _require_issued_record(value: object) -> _SealedRecord:
    if type(value) not in _RECORD_DOMAINS:
        raise TypeError("value must be an exact CP67 sealed record")
    record = cast(_SealedRecord, value)
    with _ISSUED_RECORD_LOCK:
        snapshot = _ISSUED_RECORD_SNAPSHOTS.get(record)
    if snapshot is None:
        raise TypeError("CP67 record was not module-created")
    if not hmac.compare_digest(
        snapshot,
        _plain_json_bytes(record, maximum_bytes=_MAXIMUM_CANONICAL_RECORD_BYTES),
    ):
        raise ValueError("CP67 record was mutated after issue")
    return record


def cp67_canonical_json_bytes(value: object) -> bytes:
    """Return canonical JSON bytes for one unchanged module-issued record."""

    return _plain_json_bytes(
        _require_issued_record(value),
        maximum_bytes=_MAXIMUM_CANONICAL_RECORD_BYTES,
    )


def cp67_sha256(value: object) -> str:
    """Return the public type-separated digest of an issued CP67 record."""

    record = _require_issued_record(value)
    return hashlib.sha256(
        b"cp67-public-record-v1\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + cp67_canonical_json_bytes(record)
    ).hexdigest()


def _row_inventory_sha256() -> str:
    return hashlib.sha256(
        b"cp67-test28-request-row-inventory-v1\0" + _plain_json_bytes(_ROW_INVENTORY)
    ).hexdigest()


def cp67_schedule_fixture_set_sha256() -> str:
    """Return the closed capsule-and-schedule qualification fixture digest."""

    result = hashlib.sha256(
        b"cp67-test28-full-schedule-qualification-fixture-set-v1\0"
        + bytes.fromhex(_DEVELOPMENT_CAPSULE_RAW_SHA256)
        + bytes.fromhex(_DEVELOPMENT_SCHEDULE_RAW_SHA256)
    ).hexdigest()
    if result != _QUALIFICATION_FIXTURE_SET_SHA256:
        raise RuntimeError("CP67 fixture-set pin is internally inconsistent")
    return result


def _predecessor_custody() -> CP67PredecessorCustodyV1:
    return cast(
        CP67PredecessorCustodyV1,
        _record(
            CP67PredecessorCustodyV1,
            {
                "schema_version": CP67_TEST28_SCHEMA_VERSION,
                "v17_protocol_sha256": _V17_PROTOCOL_SHA256,
                "v17_protocol_bytes": 149_739,
                "v17_protocol_lf_count": 2_648,
                "v17_manifest_sha256": _V17_MANIFEST_SHA256,
                "v17_manifest_bytes": 6_012_833,
                "v17_manifest_lf_count": 118_501,
                "cp61_source_sha256": _CP61_SOURCE_SHA256,
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "cp62_source_sha256": _CP62_SOURCE_SHA256,
                "cp62_bundle_record_sha256": _CP62_BUNDLE_RECORD_SHA256,
                "cp62_runtime_lock_record_sha256": (_CP63_RUNTIME_LOCK_RECORD_SHA256),
                "cp63_runner_source_sha256": _CP63_SOURCE_SHA256,
                "cp63_runner_bundle_record_sha256": (_CP63_RUNNER_BUNDLE_RECORD_SHA256),
                "cp63_seed_capsule_contract_record_sha256": (
                    _CP63_SEED_CAPSULE_CONTRACT_RECORD_SHA256
                ),
                "cp63_schedule_contract_record_sha256": (
                    _CP63_SCHEDULE_CONTRACT_RECORD_SHA256
                ),
                "cp65_authoritative_source_sha256": (_CP65_AUTHORITATIVE_SOURCE_SHA256),
                "cp65_authoritative_bundle_record_sha256": (_CP65_BUNDLE_RECORD_SHA256),
                "cp65_independent_source_sha256": _CP65_INDEPENDENT_SOURCE_SHA256,
                "cp65_independent_bundle_record_sha256": (
                    _CP65_INDEPENDENT_BUNDLE_RECORD_SHA256
                ),
                "cp65_schema_semantic_sha256": _CP65_SCHEMA_SEMANTIC_SHA256,
                "cp65_production_schedule_schema_record_sha256": (
                    _CP65_PRODUCTION_SCHEDULE_SCHEMA_RECORD_SHA256
                ),
                "cp65_schedule_request_row_digest_contract_record_sha256": (
                    _CP65_SCHEDULE_REQUEST_ROW_DIGEST_CONTRACT_RECORD_SHA256
                ),
                "cp65_schedule_ordered_request_digest_contract_record_sha256": (
                    _CP65_SCHEDULE_ORDERED_REQUEST_DIGEST_CONTRACT_RECORD_SHA256
                ),
                "cp66_source_sha256": _CP66_SOURCE_SHA256,
                "cp66_test_sha256": _CP66_TEST_SHA256,
                "cp66_bundle_record_sha256": _CP66_BUNDLE_RECORD_SHA256,
                "cp66_qualification_fixture_set_sha256": (
                    _CP66_QUALIFICATION_FIXTURE_SET_SHA256
                ),
            },
        ),
    )


def _development_seed_capsule_fixture() -> CP67DevelopmentSeedCapsuleFixtureV1:
    return cast(
        CP67DevelopmentSeedCapsuleFixtureV1,
        _record(
            CP67DevelopmentSeedCapsuleFixtureV1,
            {
                "schema_version": CP67_TEST28_SCHEMA_VERSION,
                "case_ordinal": 1,
                "case_id": _DEVELOPMENT_CASE_ID,
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "capsule_schema": _CP63_SCHEMA_VERSION,
                "capsule_purpose": _CP63_CAPSULE_PURPOSE,
                "seed_count": CP67_TEST28_SEED_COUNT,
                "seed_ordinal_min": 1,
                "seed_ordinal_max": CP67_TEST28_SEED_COUNT,
                "seed_encoding": "uint64-16-lowercase-hex-big-endian",
                "seed_value_formula": (
                    "seed-value-equals-seed-ordinal-minus-one-encoded-as-"
                    "uint64-16-lowercase-hex-big-endian"
                ),
                "minimum_seed_hex": "0000000000000000",
                "maximum_seed_hex": "00000000000007ff",
                "distinct_seed_value_count": CP67_TEST28_SEED_COUNT,
                "ordered_seed_values_digest_domain": (
                    "cp67-test28-development-ordered-seed-values-v1\\0"
                ),
                "ordered_seed_values_sha256": (_DEVELOPMENT_ORDERED_SEED_VALUES_SHA256),
                "source_method_id": _DEVELOPMENT_SOURCE_METHOD_ID,
                "source_receipt_digest_domain": (
                    "cp67-test28-development-synthetic-source-receipt-v1\\0"
                ),
                "source_receipt_sha256": _DEVELOPMENT_SOURCE_RECEIPT_SHA256,
                "acquisition_session_digest_domain": (
                    "cp67-test28-development-synthetic-acquisition-session-v1\\0"
                ),
                "acquisition_session_sha256": (_DEVELOPMENT_ACQUISITION_SESSION_SHA256),
                "capsule_body_digest_domain": ("cp63-test28-seed-capsule-v1\\0"),
                "seed_capsule_body_sha256": _DEVELOPMENT_CAPSULE_BODY_SHA256,
                "seed_capsule_canonical_json_bytes": _DEVELOPMENT_CAPSULE_BYTES,
                "seed_capsule_canonical_json_sha256": (_DEVELOPMENT_CAPSULE_RAW_SHA256),
                "module_owned_fixture": True,
                "caller_supplied_seed_or_capsule_accepted": False,
                "external_seed_source_bound": False,
                "iid_uniform_with_replacement_verified": False,
                "production_seed_capsule": False,
            },
        ),
    )


def _schedule_materializer_contract() -> CP67ScheduleMaterializerContractV1:
    return cast(
        CP67ScheduleMaterializerContractV1,
        _record(
            CP67ScheduleMaterializerContractV1,
            {
                "schema_version": CP67_TEST28_SCHEMA_VERSION,
                "contract_id": "cp67-development-full-schedule-materializer-v1",
                "development_case_id": _DEVELOPMENT_CASE_ID,
                "cp63_seed_capsule_contract_record_sha256": (
                    _CP63_SEED_CAPSULE_CONTRACT_RECORD_SHA256
                ),
                "cp63_schedule_contract_record_sha256": (
                    _CP63_SCHEDULE_CONTRACT_RECORD_SHA256
                ),
                "cp65_production_schedule_schema_record_sha256": (
                    _CP65_PRODUCTION_SCHEDULE_SCHEMA_RECORD_SHA256
                ),
                "seed_count": CP67_TEST28_SEED_COUNT,
                "row_count": CP67_TEST28_ROW_COUNT,
                "request_count": CP67_TEST28_REQUEST_COUNT,
                "logical_request_order": "(seed_ordinal-1)*16+row_ordinal",
                "plan_seed_assignment": "external-seed-value-unchanged",
                "schedule_schema": _CP65_SCHEDULE_SCHEMA,
                "schedule_purpose": _CP65_SCHEDULE_PURPOSE,
                "development_attempt_id": _DEVELOPMENT_ATTEMPT_ID,
                "synthetic_freeze_receipt_digest_domain": (
                    "cp67-test28-development-no-freeze-receipt-v1\\0"
                ),
                "synthetic_freeze_receipt_sha256": (_DEVELOPMENT_FREEZE_RECEIPT_SHA256),
                "synthetic_freeze_digest_is_receipt": False,
                "request_instance_digest_domain": ("cp63-test28-bound-request-v1\\0"),
                "request_row_digest_domain": (
                    "cp65-test28-production-schedule-request-row-v1\\0"
                ),
                "ordered_requests_digest_domain": (
                    "cp65-test28-production-schedule-ordered-requests-v1\\0"
                ),
                "schedule_body_digest_domain": (
                    "cp65-test28-production-schedule-v1\\0"
                ),
                "seed_capsule_max_bytes": CP67_TEST28_SEED_CAPSULE_MAX_BYTES,
                "schedule_max_bytes": CP67_TEST28_SCHEDULE_MAX_BYTES,
                "cp63_direct_seed_capsule_parser_call_count": 1,
                "cp63_effective_seed_capsule_parser_call_count": 21,
                "cp63_bound_request_logical_ordinals": (
                    _CP63_BOUND_REQUEST_CALL_LOGICAL_ORDINALS
                ),
                "cp63_bound_request_call_count": len(
                    _CP63_BOUND_REQUEST_CALL_LOGICAL_ORDINALS
                ),
                "all_row_shapes_sampled_by_cp63": True,
                "all_seed_boundary_shapes_sampled_by_cp63": True,
                "remaining_rows_generated_from_frozen_formula": True,
                "dual_cp65_validator_required": True,
                "in_memory_only": True,
                "schedule_bytes_retained": False,
                "filesystem_write_permitted": False,
                "generic_seed_or_capsule_api_exposed": False,
                "production_materialization_api_exposed": False,
            },
        ),
    )


def _schedule_materialization_expectation() -> CP67ScheduleMaterializationExpectationV1:
    return cast(
        CP67ScheduleMaterializationExpectationV1,
        _record(
            CP67ScheduleMaterializationExpectationV1,
            {
                "schema_version": CP67_TEST28_SCHEMA_VERSION,
                "case_id": _DEVELOPMENT_CASE_ID,
                "qualification_fixture_set_digest_domain": (
                    "cp67-test28-full-schedule-qualification-fixture-set-v1\\0"
                ),
                "qualification_fixture_set_sha256": (
                    cp67_schedule_fixture_set_sha256()
                ),
                "seed_capsule_canonical_json_bytes": _DEVELOPMENT_CAPSULE_BYTES,
                "seed_capsule_canonical_json_sha256": (_DEVELOPMENT_CAPSULE_RAW_SHA256),
                "schedule_canonical_json_bytes": _DEVELOPMENT_SCHEDULE_BYTES,
                "schedule_canonical_json_sha256": (_DEVELOPMENT_SCHEDULE_RAW_SHA256),
                "schedule_body_sha256": _DEVELOPMENT_SCHEDULE_BODY_SHA256,
                "ordered_requests_sha256": (_DEVELOPMENT_ORDERED_REQUESTS_SHA256),
                "first_request_row_sha256": (_DEVELOPMENT_FIRST_REQUEST_ROW_SHA256),
                "last_request_row_sha256": (_DEVELOPMENT_LAST_REQUEST_ROW_SHA256),
                "request_count": CP67_TEST28_REQUEST_COUNT,
                "unique_request_instance_sha256_count": (CP67_TEST28_REQUEST_COUNT),
                "unique_request_row_sha256_count": CP67_TEST28_REQUEST_COUNT,
                "expected_cp65_validated_digest_preimage_count": (
                    CP67_TEST28_EXPECTED_VALIDATED_DIGEST_PREIMAGE_COUNT
                ),
                "expected_cp65_unresolved_digest_preimage_count": (
                    CP67_TEST28_EXPECTED_UNRESOLVED_DIGEST_PREIMAGE_COUNT
                ),
                "expected_cp65_validated_cross_binding_count": (
                    CP67_TEST28_EXPECTED_VALIDATED_CROSS_BINDING_COUNT
                ),
                "expected_cp65_unresolved_cross_binding_count": (
                    CP67_TEST28_EXPECTED_UNRESOLVED_CROSS_BINDING_COUNT
                ),
                "authoritative_cp65_validation_record_sha256": (
                    _AUTHORITATIVE_VALIDATION_RECORD_SHA256
                ),
                "independent_cp65_validation_record_sha256": (
                    _INDEPENDENT_VALIDATION_RECORD_SHA256
                ),
            },
        ),
    )


_BUNDLE_LOCK = threading.RLock()
_BUNDLE_CACHE: Optional[CP67FullScheduleMaterializerQualificationBundleV1] = None
_QUALIFICATION_LOCK = threading.Lock()


def cp67_full_schedule_materializer_qualification_bundle() -> CP67FullScheduleMaterializerQualificationBundleV1:
    """Return the pure definition-only CP67 qualification bundle."""

    global _BUNDLE_CACHE
    with _BUNDLE_LOCK:
        if _BUNDLE_CACHE is not None:
            _require_issued_record(_BUNDLE_CACHE)
            return _BUNDLE_CACHE
        _BUNDLE_CACHE = cast(
            CP67FullScheduleMaterializerQualificationBundleV1,
            _record(
                CP67FullScheduleMaterializerQualificationBundleV1,
                {
                    "schema_version": CP67_TEST28_SCHEMA_VERSION,
                    "scope": CP67_TEST28_SCOPE,
                    "predecessor_custody": _predecessor_custody(),
                    "development_seed_capsule_fixture": (
                        _development_seed_capsule_fixture()
                    ),
                    "schedule_materializer_contract": (
                        _schedule_materializer_contract()
                    ),
                    "schedule_materialization_expectation": (
                        _schedule_materialization_expectation()
                    ),
                    "qualification_fixture_set_sha256": (
                        cp67_schedule_fixture_set_sha256()
                    ),
                    "qualification_case_count": 1,
                    "zero_argument_builder": True,
                    "builder_materializes_schedule": False,
                    "qualification_runner_zero_argument": True,
                    "closed_module_owned_fixture_only": True,
                    "stdlib_only_import": True,
                    "project_modules_imported_by_builder": False,
                    "cp63_cp65_modules_lazy_imported_by_qualification_runner": True,
                    "host_filesystem_probed": False,
                    "clock_read": False,
                    "rng_used": False,
                    "network_used": False,
                    "subprocess_api_exposed": False,
                    "filesystem_path_api_exposed": False,
                    "generic_seed_or_capsule_api_exposed": False,
                    "production_materialization_api_exposed": False,
                    "production_seed_capsule_present": False,
                    "external_seed_source_bound": False,
                    "iid_uniform_with_replacement_verified": False,
                    "production_schedule_instantiated": False,
                    "production_gate_7_evidence_present": False,
                    "production_gate_7_state": "MISSING",
                    "production_requests_materialized": False,
                    "production_campaign_exposed": False,
                    "production_execution_authorized": False,
                    "production_execution_observed": False,
                    "runner_and_recomputation_blocker_closed": False,
                    "unconditional_operational_predictions_blocker_closed": False,
                    "power_and_thresholds_blocker_closed": False,
                    "confirmatory_custody_blocker_closed": False,
                    "confirmatory_evidence": False,
                    "manuscript_claim": False,
                    "formal_test_28_status": CP67_TEST28_FORMAL_TEST_28_STATUS,
                    "formal_test_28_closed": False,
                    "ledger_prerequisite_id": (
                        CP67_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID
                    ),
                    "ledger_prerequisite_state": _LEDGER_PREREQUISITE_STATE,
                    "ledger_total_count": 22,
                    "ledger_satisfied_count": 18,
                    "ledger_missing_count": 4,
                    "development_qualification_only": True,
                },
            ),
        )
        return _BUNDLE_CACHE


def _require_qualification(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise CP67ScheduleMaterializerQualificationError(code, message)


def _development_seed_capsule_bytes() -> Tuple[bytes, Tuple[str, ...]]:
    seed_values = tuple(f"{ordinal:016x}" for ordinal in range(CP67_TEST28_SEED_COUNT))
    ordered_seed_values_sha256 = hashlib.sha256(
        b"cp67-test28-development-ordered-seed-values-v1\0"
        + _plain_json_bytes(seed_values)
    ).hexdigest()
    _require_qualification(
        ordered_seed_values_sha256 == _DEVELOPMENT_ORDERED_SEED_VALUES_SHA256,
        "CP67_SEED_VECTOR_PIN_MISMATCH",
        "the module-owned development seed vector differs from its pin",
    )
    document = {
        "schema": _CP63_SCHEMA_VERSION,
        "purpose": _CP63_CAPSULE_PURPOSE,
        "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
        "seed_count": CP67_TEST28_SEED_COUNT,
        "seed_ordinals": list(range(1, CP67_TEST28_SEED_COUNT + 1)),
        "seed_encoding": "uint64-16-lowercase-hex-big-endian",
        "ordered_seed_values": list(seed_values),
        "source_method_id": _DEVELOPMENT_SOURCE_METHOD_ID,
        "source_receipt_sha256": _DEVELOPMENT_SOURCE_RECEIPT_SHA256,
        "acquisition_session_sha256": (_DEVELOPMENT_ACQUISITION_SESSION_SHA256),
        "body_sha256": _ZERO_SHA256,
    }
    _require_qualification(
        set(document) == set(_CAPSULE_KEYS),
        "CP67_CAPSULE_FIELD_SET_MISMATCH",
        "the development seed capsule field set differs",
    )
    document["body_sha256"] = hashlib.sha256(
        b"cp63-test28-seed-capsule-v1\0" + _plain_json_bytes(document)
    ).hexdigest()
    payload = _plain_json_bytes(document)
    _require_qualification(
        len(payload) <= CP67_TEST28_SEED_CAPSULE_MAX_BYTES,
        "CP67_CAPSULE_RESOURCE_LIMIT",
        "the development seed capsule exceeds its byte limit",
    )
    _require_qualification(
        document["body_sha256"] == _DEVELOPMENT_CAPSULE_BODY_SHA256
        and len(payload) == _DEVELOPMENT_CAPSULE_BYTES
        and hashlib.sha256(payload).hexdigest() == _DEVELOPMENT_CAPSULE_RAW_SHA256,
        "CP67_CAPSULE_EXPECTATION_MISMATCH",
        "the development seed capsule differs from its frozen expectation",
    )
    return payload, seed_values


def _request_row(
    logical_request_ordinal: int,
    seed_capsule_body_sha256: str,
    seed_values: Tuple[str, ...],
) -> dict:
    seed_ordinal = (logical_request_ordinal - 1) // CP67_TEST28_ROW_COUNT + 1
    row_ordinal = (logical_request_ordinal - 1) % CP67_TEST28_ROW_COUNT + 1
    inventory = _ROW_INVENTORY[row_ordinal - 1]
    _require_qualification(
        inventory[0] == row_ordinal,
        "CP67_ROW_INVENTORY_ORDER_MISMATCH",
        "the independent CP67 row inventory is not in ordinal order",
    )
    row = {
        "schema_version": _CP63_SCHEMA_VERSION,
        "seed_capsule_body_sha256": seed_capsule_body_sha256,
        "seed_ordinal": seed_ordinal,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": logical_request_ordinal,
        "row_key": inventory[1],
        "fixture_id": inventory[2],
        "strategy": inventory[3],
        "budget": inventory[4],
        "plan_seed_hex": seed_values[seed_ordinal - 1],
        "seed_free_request_sha256": inventory[5],
        "runtime_lock_sha256": _CP63_RUNTIME_LOCK_RECORD_SHA256,
    }
    row["request_instance_sha256"] = hashlib.sha256(
        b"cp63-test28-bound-request-v1\0" + _plain_json_bytes(row)
    ).hexdigest()
    row["request_row_sha256"] = _ZERO_SHA256
    row["request_row_sha256"] = hashlib.sha256(
        b"cp65-test28-production-schedule-request-row-v1\0" + _plain_json_bytes(row)
    ).hexdigest()
    _require_qualification(
        set(row) == set(_REQUEST_KEYS),
        "CP67_REQUEST_FIELD_SET_MISMATCH",
        "a generated request row differs from the frozen field set",
    )
    return row


def _bound_request_matches_row(bound: object, row: dict) -> bool:
    return (
        all(getattr(bound, key, None) == row[key] for key in _REQUEST_KEYS[:-1])
        and getattr(bound, "definition_only", None) is True
        and getattr(bound, "production_execution_authorized", None) is False
    )


def _materialize_schedule_payload(
    cp63: object,
    capsule_observation: object,
    seed_values: Tuple[str, ...],
) -> Tuple[bytes, Mapping[str, object]]:
    requests = []
    ordered_row_sha256s = []
    request_instance_sha256s = set()
    request_row_sha256s = set()
    sampled_rows = {}
    seed_major_order_verified = True
    plan_seed_values_unchanged = True
    for logical in range(1, CP67_TEST28_REQUEST_COUNT + 1):
        row = _request_row(
            logical,
            _DEVELOPMENT_CAPSULE_BODY_SHA256,
            seed_values,
        )
        expected_seed = (logical - 1) // CP67_TEST28_ROW_COUNT + 1
        expected_row = (logical - 1) % CP67_TEST28_ROW_COUNT + 1
        seed_major_order_verified = seed_major_order_verified and (
            row["seed_ordinal"] == expected_seed
            and row["row_ordinal"] == expected_row
            and row["logical_request_ordinal"]
            == (expected_seed - 1) * CP67_TEST28_ROW_COUNT + expected_row
        )
        plan_seed_values_unchanged = plan_seed_values_unchanged and (
            row["plan_seed_hex"] == seed_values[expected_seed - 1]
        )
        requests.append(row)
        ordered_row_sha256s.append(row["request_row_sha256"])
        request_instance_sha256s.add(row["request_instance_sha256"])
        request_row_sha256s.add(row["request_row_sha256"])
        if logical in _CP63_BOUND_REQUEST_CALL_LOGICAL_ORDINALS:
            sampled_rows[logical] = row

    exemplar_parity = True
    for logical in _CP63_BOUND_REQUEST_CALL_LOGICAL_ORDINALS:
        bound = cp63.cp63_bound_request(capsule_observation, logical)
        exemplar_parity = exemplar_parity and _bound_request_matches_row(
            bound, sampled_rows[logical]
        )
    _require_qualification(
        exemplar_parity,
        "CP67_CP63_BOUND_REQUEST_PARITY_MISMATCH",
        "a generated request row differs from its CP63 bound-request exemplar",
    )

    ordered_requests_sha256 = hashlib.sha256(
        b"cp65-test28-production-schedule-ordered-requests-v1\0"
        + _plain_json_bytes(ordered_row_sha256s)
    ).hexdigest()
    schedule = {
        "schema": _CP65_SCHEDULE_SCHEMA,
        "purpose": _CP65_SCHEDULE_PURPOSE,
        "attempt_id": _DEVELOPMENT_ATTEMPT_ID,
        "freeze_receipt_sha256": _DEVELOPMENT_FREEZE_RECEIPT_SHA256,
        "seed_capsule_body_sha256": _DEVELOPMENT_CAPSULE_BODY_SHA256,
        "schedule_contract_sha256": _CP63_SCHEDULE_CONTRACT_RECORD_SHA256,
        "request_count": CP67_TEST28_REQUEST_COUNT,
        "requests": requests,
        "ordered_request_record_sha256s": ordered_row_sha256s,
        "ordered_requests_sha256": ordered_requests_sha256,
        "body_sha256": _ZERO_SHA256,
    }
    _require_qualification(
        set(schedule) == set(_SCHEDULE_KEYS),
        "CP67_SCHEDULE_FIELD_SET_MISMATCH",
        "the generated schedule differs from the frozen field set",
    )
    schedule["body_sha256"] = hashlib.sha256(
        b"cp65-test28-production-schedule-v1\0" + _plain_json_bytes(schedule)
    ).hexdigest()
    payload = _plain_json_bytes(schedule)
    _require_qualification(
        len(payload) <= CP67_TEST28_SCHEDULE_MAX_BYTES,
        "CP67_SCHEDULE_RESOURCE_LIMIT",
        "the generated schedule exceeds its byte limit",
    )
    metrics = {
        "schedule_body_sha256": schedule["body_sha256"],
        "ordered_requests_sha256": ordered_requests_sha256,
        "first_request_row_sha256": ordered_row_sha256s[0],
        "last_request_row_sha256": ordered_row_sha256s[-1],
        "unique_request_instance_sha256_count": len(request_instance_sha256s),
        "unique_request_row_sha256_count": len(request_row_sha256s),
        "seed_major_order_verified": seed_major_order_verified,
        "plan_seed_values_unchanged": plan_seed_values_unchanged,
        "exemplar_parity": exemplar_parity,
    }
    del schedule
    del requests
    del ordered_row_sha256s
    del request_instance_sha256s
    del request_row_sha256s
    del sampled_rows
    return payload, metrics


def _validate_predecessor_contracts(
    cp63: object, authoritative_cp65: object, independent_cp65: object
) -> None:
    cp63_bundle = cp63.cp63_runner_recomputation_rehearsal_bundle()
    _require_qualification(
        cp63_bundle.record_sha256 == _CP63_RUNNER_BUNDLE_RECORD_SHA256
        and cp63_bundle.seed_capsule_contract.record_sha256
        == _CP63_SEED_CAPSULE_CONTRACT_RECORD_SHA256
        and cp63_bundle.schedule_contract.record_sha256
        == _CP63_SCHEDULE_CONTRACT_RECORD_SHA256,
        "CP67_CP63_CUSTODY_MISMATCH",
        "the lazy CP63 bundle differs from the frozen predecessor contract",
    )
    authoritative_bundle = (
        authoritative_cp65.cp65_production_schema_preimage_validator_bundle()
    )
    digest_contracts = {
        item.contract_id: item.record_sha256
        for item in authoritative_bundle.digest_preimage_contracts
    }
    production_schedule_schema = authoritative_cp65.cp65_artifact_schema(
        "production-schedule"
    )
    _require_qualification(
        authoritative_bundle.record_sha256 == _CP65_BUNDLE_RECORD_SHA256
        and authoritative_bundle.schema_semantic_sha256 == _CP65_SCHEMA_SEMANTIC_SHA256
        and production_schedule_schema.record_sha256
        == _CP65_PRODUCTION_SCHEDULE_SCHEMA_RECORD_SHA256
        and digest_contracts.get("production-schedule:requests-row-digest")
        == _CP65_SCHEDULE_REQUEST_ROW_DIGEST_CONTRACT_RECORD_SHA256
        and digest_contracts.get("production-schedule:ordered-request-records")
        == _CP65_SCHEDULE_ORDERED_REQUEST_DIGEST_CONTRACT_RECORD_SHA256,
        "CP67_AUTHORITATIVE_CP65_CUSTODY_MISMATCH",
        "the authoritative CP65 catalog differs from its frozen pins",
    )
    independent_bundle = independent_cp65.cp65_independent_validator_bundle()
    _require_qualification(
        independent_bundle.record_sha256 == _CP65_INDEPENDENT_BUNDLE_RECORD_SHA256
        and independent_bundle.schema_semantic_sha256 == _CP65_SCHEMA_SEMANTIC_SHA256,
        "CP67_INDEPENDENT_CP65_CUSTODY_MISMATCH",
        "the independent CP65 catalog differs from its frozen pins",
    )


def _validation_structural_view(value: object) -> tuple:
    return (
        value.input_artifact_ids,
        value.input_relative_paths,
        value.input_sha256s,
        value.input_byte_lengths,
        value.validated_artifact_ids,
        value.validated_relative_paths,
        value.validated_body_sha256s,
        value.syntax_valid,
        value.intrinsic_digest_preimages_valid,
        value.all_required_digest_preimage_sources_supplied,
        value.validated_digest_preimage_count,
        value.unresolved_digest_preimage_count,
        value.digest_preimages_valid,
        value.all_required_cross_binding_targets_supplied,
        value.validated_cross_binding_count,
        value.unresolved_cross_binding_count,
        value.cross_bindings_valid,
        value.parser_input_resource_limits_satisfied,
        value.production_evidence_accepted,
        value.gate_transition_permitted,
        value.launch_authorized,
        value.execution_permitted,
        value.definition_only,
    )


def _validate_cp65_result(value: object, expected_record_sha256: str) -> None:
    _require_qualification(
        value.input_artifact_ids == ("production-schedule",)
        and value.input_relative_paths == ("production_schedule.json",)
        and value.input_sha256s == (_DEVELOPMENT_SCHEDULE_RAW_SHA256,)
        and value.input_byte_lengths == (_DEVELOPMENT_SCHEDULE_BYTES,)
        and value.validated_artifact_ids == ("production-schedule",)
        and value.validated_relative_paths == ("production_schedule.json",)
        and value.validated_body_sha256s == (_DEVELOPMENT_SCHEDULE_BODY_SHA256,)
        and value.syntax_valid is True
        and value.intrinsic_digest_preimages_valid is True
        and value.all_required_digest_preimage_sources_supplied is False
        and value.validated_digest_preimage_count
        == CP67_TEST28_EXPECTED_VALIDATED_DIGEST_PREIMAGE_COUNT
        and value.unresolved_digest_preimage_count
        == CP67_TEST28_EXPECTED_UNRESOLVED_DIGEST_PREIMAGE_COUNT
        and value.digest_preimages_valid is False
        and value.all_required_cross_binding_targets_supplied is False
        and value.validated_cross_binding_count
        == CP67_TEST28_EXPECTED_VALIDATED_CROSS_BINDING_COUNT
        and value.unresolved_cross_binding_count
        == CP67_TEST28_EXPECTED_UNRESOLVED_CROSS_BINDING_COUNT
        and value.cross_bindings_valid is False
        and value.parser_input_resource_limits_satisfied is True
        and value.production_evidence_accepted is False
        and value.gate_transition_permitted is False
        and value.launch_authorized is False
        and value.execution_permitted is False
        and value.definition_only is True
        and value.record_sha256 == expected_record_sha256,
        "CP67_CP65_VALIDATION_RESULT_MISMATCH",
        "a CP65 schedule validation result differs from the frozen expectation",
    )


def _run_full_schedule_materializer_qualification(
    cp63: object, authoritative_cp65: object, independent_cp65: object
) -> CP67ScheduleMaterializationQualificationV1:
    _validate_predecessor_contracts(cp63, authoritative_cp65, independent_cp65)
    capsule_payload, seed_values = _development_seed_capsule_bytes()
    capsule_observation = cp63.cp63_validate_seed_capsule_bytes(capsule_payload)
    _require_qualification(
        capsule_observation.body_sha256 == _DEVELOPMENT_CAPSULE_BODY_SHA256
        and capsule_observation.canonical_byte_count == _DEVELOPMENT_CAPSULE_BYTES
        and capsule_observation.syntactically_valid is True
        and capsule_observation.source_custody_digest_bound is True
        and capsule_observation.iid_uniform_with_replacement_verified is False
        and capsule_observation.production_execution_authorized is False
        and capsule_observation.ordered_seed_values == seed_values,
        "CP67_CP63_CAPSULE_OBSERVATION_MISMATCH",
        "the CP63 capsule observation differs from the closed fixture",
    )
    schedule_payload, metrics = _materialize_schedule_payload(
        cp63, capsule_observation, seed_values
    )
    schedule_sha256 = hashlib.sha256(schedule_payload).hexdigest()
    _require_qualification(
        len(schedule_payload) == _DEVELOPMENT_SCHEDULE_BYTES
        and schedule_sha256 == _DEVELOPMENT_SCHEDULE_RAW_SHA256
        and metrics["schedule_body_sha256"] == _DEVELOPMENT_SCHEDULE_BODY_SHA256
        and metrics["ordered_requests_sha256"] == _DEVELOPMENT_ORDERED_REQUESTS_SHA256
        and metrics["first_request_row_sha256"] == _DEVELOPMENT_FIRST_REQUEST_ROW_SHA256
        and metrics["last_request_row_sha256"] == _DEVELOPMENT_LAST_REQUEST_ROW_SHA256
        and metrics["unique_request_instance_sha256_count"] == CP67_TEST28_REQUEST_COUNT
        and metrics["unique_request_row_sha256_count"] == CP67_TEST28_REQUEST_COUNT
        and metrics["seed_major_order_verified"] is True
        and metrics["plan_seed_values_unchanged"] is True
        and metrics["exemplar_parity"] is True,
        "CP67_SCHEDULE_EXPECTATION_MISMATCH",
        "the materialized schedule differs from the frozen expectation",
    )
    authoritative_result = authoritative_cp65.cp65_validate_supplied_artifact_bytes(
        "production-schedule",
        "production_schedule.json",
        schedule_payload,
    )
    independent_result = (
        independent_cp65.cp65_independently_validate_supplied_artifact_bytes(
            "production-schedule",
            "production_schedule.json",
            schedule_payload,
        )
    )
    _validate_cp65_result(authoritative_result, _AUTHORITATIVE_VALIDATION_RECORD_SHA256)
    _validate_cp65_result(independent_result, _INDEPENDENT_VALIDATION_RECORD_SHA256)
    structural_results_equal = _validation_structural_view(
        authoritative_result
    ) == _validation_structural_view(independent_result)
    _require_qualification(
        structural_results_equal,
        "CP67_DUAL_CP65_PARITY_MISMATCH",
        "authoritative and independent CP65 structural results differ",
    )

    qualification_values = {
        "schema_version": CP67_TEST28_SCHEMA_VERSION,
        "case_id": _DEVELOPMENT_CASE_ID,
        "qualification_fixture_set_sha256": (cp67_schedule_fixture_set_sha256()),
        "cp63_direct_seed_capsule_parser_call_count": 1,
        "cp63_effective_seed_capsule_parser_call_count": 21,
        "cp63_bound_request_logical_ordinals": (
            _CP63_BOUND_REQUEST_CALL_LOGICAL_ORDINALS
        ),
        "cp63_bound_request_call_count": len(_CP63_BOUND_REQUEST_CALL_LOGICAL_ORDINALS),
        "cp63_capsule_syntactically_valid": (capsule_observation.syntactically_valid),
        "cp63_source_custody_digest_bound": (
            capsule_observation.source_custody_digest_bound
        ),
        "cp63_iid_uniform_with_replacement_verified": (
            capsule_observation.iid_uniform_with_replacement_verified
        ),
        "cp63_production_execution_authorized": (
            capsule_observation.production_execution_authorized
        ),
        "cp63_bound_request_exemplar_parity_verified": True,
        "all_32768_requests_materialized": True,
        "seed_major_order_verified": True,
        "all_plan_seed_values_unchanged_across_sixteen_rows": True,
        "schedule_canonical_json_bytes": len(schedule_payload),
        "schedule_canonical_json_sha256": schedule_sha256,
        "schedule_body_sha256": metrics["schedule_body_sha256"],
        "ordered_requests_sha256": metrics["ordered_requests_sha256"],
        "first_request_row_sha256": metrics["first_request_row_sha256"],
        "last_request_row_sha256": metrics["last_request_row_sha256"],
        "unique_request_instance_sha256_count": metrics[
            "unique_request_instance_sha256_count"
        ],
        "unique_request_row_sha256_count": metrics["unique_request_row_sha256_count"],
        "authoritative_cp65_syntax_valid": authoritative_result.syntax_valid,
        "authoritative_cp65_intrinsic_digest_preimages_valid": (
            authoritative_result.intrinsic_digest_preimages_valid
        ),
        "authoritative_cp65_all_required_digest_preimage_sources_supplied": (
            authoritative_result.all_required_digest_preimage_sources_supplied
        ),
        "authoritative_cp65_validated_digest_preimage_count": (
            authoritative_result.validated_digest_preimage_count
        ),
        "authoritative_cp65_unresolved_digest_preimage_count": (
            authoritative_result.unresolved_digest_preimage_count
        ),
        "authoritative_cp65_digest_preimages_valid": (
            authoritative_result.digest_preimages_valid
        ),
        "authoritative_cp65_all_required_cross_binding_targets_supplied": (
            authoritative_result.all_required_cross_binding_targets_supplied
        ),
        "authoritative_cp65_validated_cross_binding_count": (
            authoritative_result.validated_cross_binding_count
        ),
        "authoritative_cp65_unresolved_cross_binding_count": (
            authoritative_result.unresolved_cross_binding_count
        ),
        "authoritative_cp65_cross_bindings_valid": (
            authoritative_result.cross_bindings_valid
        ),
        "authoritative_cp65_production_evidence_accepted": (
            authoritative_result.production_evidence_accepted
        ),
        "authoritative_cp65_execution_permitted": (
            authoritative_result.execution_permitted
        ),
        "authoritative_cp65_validation_record_sha256": (
            authoritative_result.record_sha256
        ),
        "independent_cp65_syntax_valid": independent_result.syntax_valid,
        "independent_cp65_intrinsic_digest_preimages_valid": (
            independent_result.intrinsic_digest_preimages_valid
        ),
        "independent_cp65_all_required_digest_preimage_sources_supplied": (
            independent_result.all_required_digest_preimage_sources_supplied
        ),
        "independent_cp65_validated_digest_preimage_count": (
            independent_result.validated_digest_preimage_count
        ),
        "independent_cp65_unresolved_digest_preimage_count": (
            independent_result.unresolved_digest_preimage_count
        ),
        "independent_cp65_digest_preimages_valid": (
            independent_result.digest_preimages_valid
        ),
        "independent_cp65_all_required_cross_binding_targets_supplied": (
            independent_result.all_required_cross_binding_targets_supplied
        ),
        "independent_cp65_validated_cross_binding_count": (
            independent_result.validated_cross_binding_count
        ),
        "independent_cp65_unresolved_cross_binding_count": (
            independent_result.unresolved_cross_binding_count
        ),
        "independent_cp65_cross_bindings_valid": (
            independent_result.cross_bindings_valid
        ),
        "independent_cp65_production_evidence_accepted": (
            independent_result.production_evidence_accepted
        ),
        "independent_cp65_execution_permitted": (
            independent_result.execution_permitted
        ),
        "independent_cp65_validation_record_sha256": (independent_result.record_sha256),
        "dual_validator_structural_results_equal": structural_results_equal,
        "schedule_matches_frozen_expectation": True,
        "production_seed_capsule_present": False,
        "production_schedule_instantiated": False,
        "production_gate_7_evidence_present": False,
        "production_gate_7_state": "MISSING",
        "production_execution_authorized": False,
        "runner_and_recomputation_blocker_closed": False,
        "formal_test_28_closed": False,
        "all_development_qualification_checks_passed": True,
    }
    del schedule_payload
    del capsule_payload
    del seed_values
    del capsule_observation
    del authoritative_result
    del independent_result
    del metrics
    return cast(
        CP67ScheduleMaterializationQualificationV1,
        _record(
            CP67ScheduleMaterializationQualificationV1,
            qualification_values,
        ),
    )


def cp67_run_full_schedule_materializer_qualification() -> CP67ScheduleMaterializationQualificationV1:
    """Run the closed in-memory qualification and return a compact receipt."""

    try:
        from heterodiff.evaluation import (
            mixed_initializer_test28_independent_production_schema_preimage_validator as independent_cp65,
        )
        from heterodiff.evaluation import (
            mixed_initializer_test28_production_schema_preimage_validator as authoritative_cp65,
        )
        from heterodiff.evaluation import (
            mixed_initializer_test28_runner_recomputation_rehearsal as cp63,
        )

        with _QUALIFICATION_LOCK:
            return _run_full_schedule_materializer_qualification(
                cp63, authoritative_cp65, independent_cp65
            )
    except CP67ScheduleMaterializerQualificationError:
        raise
    except MemoryError as exc:
        raise CP67ScheduleMaterializerQualificationError(
            "CP67_RESOURCE_EXHAUSTED",
            "the closed CP67 qualification exceeded its memory boundary",
        ) from exc
    except ImportError as exc:
        raise CP67ScheduleMaterializerQualificationError(
            "CP67_PREDECESSOR_IMPORT_FAILED",
            "a frozen CP63 or CP65 predecessor module could not be imported",
        ) from exc
    except Exception as exc:
        raise CP67ScheduleMaterializerQualificationError(
            "CP67_PREDECESSOR_OR_VALIDATION_FAILURE",
            "the closed CP67 qualification failed predecessor validation",
        ) from exc


__all__ = (
    "CP67_TEST28_SCHEMA_VERSION",
    "CP67_TEST28_SCOPE",
    "CP67_TEST28_FORMAL_TEST_28_STATUS",
    "CP67_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP67_TEST28_SEED_COUNT",
    "CP67_TEST28_ROW_COUNT",
    "CP67_TEST28_REQUEST_COUNT",
    "CP67_TEST28_SEED_CAPSULE_MAX_BYTES",
    "CP67_TEST28_SCHEDULE_MAX_BYTES",
    "CP67_TEST28_EXPECTED_VALIDATED_DIGEST_PREIMAGE_COUNT",
    "CP67_TEST28_EXPECTED_UNRESOLVED_DIGEST_PREIMAGE_COUNT",
    "CP67_TEST28_EXPECTED_VALIDATED_CROSS_BINDING_COUNT",
    "CP67_TEST28_EXPECTED_UNRESOLVED_CROSS_BINDING_COUNT",
    "CP67ScheduleMaterializerQualificationError",
    "CP67PredecessorCustodyV1",
    "CP67DevelopmentSeedCapsuleFixtureV1",
    "CP67ScheduleMaterializerContractV1",
    "CP67ScheduleMaterializationExpectationV1",
    "CP67ScheduleMaterializationQualificationV1",
    "CP67FullScheduleMaterializerQualificationBundleV1",
    "cp67_canonical_json_bytes",
    "cp67_sha256",
    "cp67_schedule_fixture_set_sha256",
    "cp67_full_schedule_materializer_qualification_bundle",
    "cp67_run_full_schedule_materializer_qualification",
)
