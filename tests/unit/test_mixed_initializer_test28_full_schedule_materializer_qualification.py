"""Hostile tests for the zero-production CP67 schedule materializer."""

from __future__ import annotations

import ast
import builtins
from dataclasses import fields, is_dataclass
import hashlib
import inspect
import json
import os
from pathlib import Path
import pickle
import random
import secrets
import socket
import subprocess
import sys
import time
import weakref

import heterodiff.evaluation.mixed_initializer_test28_full_schedule_materializer_qualification as cp67
import pytest

if sys.version_info >= (3, 10):
    from heterodiff.evaluation import (
        mixed_initializer_test28_independent_production_schema_preimage_validator as cp65i,
    )
    from heterodiff.evaluation import (
        mixed_initializer_test28_production_schema_preimage_validator as cp65a,
    )
    from heterodiff.evaluation import (
        mixed_initializer_test28_runner_recomputation_rehearsal as cp63,
    )
else:  # CP63 deliberately requires the post-3.9 dataclass slots API.
    cp63 = None
    cp65a = None
    cp65i = None


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_full_schedule_materializer_qualification.py"
)
_V17_PROTOCOL = _ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v17.md"
_V17_MANIFEST = _ROOT / "research/fixtures/cp50_test28_mixed_initializer_v17.json"

_ZERO_SHA256 = "0" * 64
_V17_PROTOCOL_SHA256 = (
    "7805865a4e988e0b3de75a702d9310228ac2da999d3413dc53aba2ee01c95516"
)
_V17_PROTOCOL_BYTES = 149_739
_V17_PROTOCOL_LF_COUNT = 2_648
_V17_MANIFEST_SHA256 = (
    "1129896e5de5858e7d8714bd75d9a32629974b4efbcea6fd13ce9fcedef65339"
)
_V17_MANIFEST_BYTES = 6_012_833
_V17_MANIFEST_LF_COUNT = 118_501
_CP63_SOURCE_SHA256 = "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
_CP61_SOURCE_SHA256 = "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_CP62_BUNDLE_SHA256 = "0f92f54ce8d451485019f6d697736fd5eb48d2b942e1d3a3f1bd373b50c3ec92"
_CP63_BUNDLE_SHA256 = "442c4b0f134a96efe32b5246b4eb5b05233d61a13c62c0a7d1f21c9bbbd32f85"
_CP63_SEED_CAPSULE_CONTRACT_SHA256 = (
    "1765adf642962c73b61634dde767fe9d2c2fef5fd71c21305fe43c6d338cf80d"
)
_CP63_SCHEDULE_CONTRACT_SHA256 = (
    "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
)
_CP65_AUTHORITATIVE_SOURCE_SHA256 = (
    "774cd44ad6aa82ea629ef705bde3bbb7288ccd74bd0d3a5d5c79f552a5f6a06a"
)
_CP65_INDEPENDENT_SOURCE_SHA256 = (
    "503306d1005af2acfe2f77c0bc1dd89d9b1b003e0a35136b5a77efcae81b0c1b"
)
_CP65_BUNDLE_SHA256 = "597f2b4b557bffb529d951858fd84e454135220db0c19dcd05fcf7ce93710f89"
_CP65_INDEPENDENT_BUNDLE_SHA256 = (
    "f34b5e4463a8ab881ac81378b3162b2b73a961be12a1e83d59341a0ff7b6af52"
)
_CP65_SCHEMA_SEMANTIC_SHA256 = (
    "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
)
_CP65_SCHEDULE_SCHEMA_SHA256 = (
    "96da33ac756d0f66a5bd105deab41fe695bc00337772862578b326d9519d47c4"
)
_CP65_SCHEDULE_ROW_DIGEST_CONTRACT_SHA256 = (
    "9f624c3f5701a8343144bf7c2ae150aaee12a4279c1ffe694ae30dc40295c60c"
)
_CP65_SCHEDULE_ORDERED_DIGEST_CONTRACT_SHA256 = (
    "c93ef095d30762912f52949fbc08074f0c0f3f93ca5ebe954a36916c8693fb72"
)
_CP66_SOURCE_SHA256 = "54eab1ec63ee280cf6741ffc9611f7012678c633c044d8131138314a6abc2861"
_CP66_TEST_SHA256 = "5913e37c2c3f784b62a091ebdb82745c7d43e1acd85cd7942a68a0780bc1e55c"
_CP66_BUNDLE_SHA256 = "409a3ad764c1f12e0212d1c63de8bf32df36380287f39a81a9f82c4674cecec2"
_CP66_FIXTURE_SET_SHA256 = (
    "a8a763a14097f2831258c2451df4daab344125d3d48a725758620a7e783920d5"
)

_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP63_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_DEVELOPMENT_SOURCE_RECEIPT_SHA256 = (
    "386cdfc1e3bbd5f7246f784fbb96a2a3bc0f917f46cb1034b682f6eb9dff9a5c"
)
_DEVELOPMENT_ACQUISITION_SESSION_SHA256 = (
    "ce410ba7d37f0c2d541f7984c7bbc2891fd644b866e4894476afdfd3e9ca45ce"
)
_DEVELOPMENT_FREEZE_NONRECEIPT_SHA256 = (
    "40e5b236a608a00a50bade2de14154bb23214abc9d7984e50c6401de4dcb1ed7"
)
_SEED_VALUE_VECTOR_SHA256 = (
    "cc2f7772823c44e3c417b4aa941268d4ffd464b9fd15a43fb8cc46c7aa531c09"
)
_CAPSULE_BODY_SHA256 = (
    "f4854575583657c85d912816b6938503c9882fc488ff46f9b2407ba288cb8164"
)
_CAPSULE_RAW_SHA256 = "48a171ca9e17561830297a96d7a98777266c04e91eccb2db4c7d91111fa62422"
_CAPSULE_BYTES = 48_711
_FIRST_REQUEST_ROW_SHA256 = (
    "72755276c4acb052d2148a26613d6b0ae4291e91d20c287b74014a9eb267b17f"
)
_LAST_REQUEST_ROW_SHA256 = (
    "8346f0a5f538d3fc2f065411da2d99f11736d9ae6237b9c5f04cccd6da803512"
)
_ORDERED_REQUESTS_SHA256 = (
    "ef4a97159d9b5e4828f5fc60c314d34ec48eeaa9a02c784c0dba654cd6b17be9"
)
_SCHEDULE_BODY_SHA256 = (
    "8e9156150a5666e5986d6e71eb0563c6e72aee2faa9bf013e1b47a99e2fda798"
)
_SCHEDULE_RAW_SHA256 = (
    "c830af2b1ff54e14dd6684d935a45bb1eabcf90abaa3ebe68e38a06c9176b544"
)
_SCHEDULE_BYTES = 26_749_445
_FIXTURE_SET_SHA256 = "e5f48b09da24f6a98d1fb3fa0e903dffb306db56233001c1dc6eaa742a2f2a0c"
_PREDECESSOR_RECORD_SHA256 = (
    "c9c2b82f3bfd598bb4d3ccf97160226a454e8f19f02bf893e3c5240f181e6050"
)
_CASE_RECORD_SHA256 = "455e62e9e98946a75ae00617b5418280700277e0205e3c0bd87cd0e792555ebe"
_CONTRACT_RECORD_SHA256 = (
    "3a3e7f1dbd04360b65e442099e3dcd8a91a6c8dbe0e5b16fde896e86a8372893"
)
_EXPECTATION_RECORD_SHA256 = (
    "283ebec3c3b1bb4c3a18479fdc66e20525a591d9af1f02007869154cf8d041ea"
)
_BUNDLE_RECORD_SHA256 = (
    "12dd4c44682a7db53a65258f146e96f6248755ebf2f2ed1db6aa0f4ad3d99c35"
)
_QUALIFICATION_RECORD_SHA256 = (
    "b7572677e2188ac6fd68534a0ac208b7d806a9929298efac7274119509d2e078"
)
_BUNDLE_PUBLIC_SHA256 = (
    "80cd78507443c1826d0691db3f9857b39ffae356fcf356898d5694eb5cb6d548"
)
_QUALIFICATION_PUBLIC_SHA256 = (
    "874ae10763dfc9d3ae7829c91bb96915f09f10e0944bad6a3cec6c93d0badb17"
)
_AUTHORITATIVE_VALIDATION_RECORD_SHA256 = (
    "8b9cc46bf3944f109b602f3a0a4ed2ef2c29bae06f5580d1d48ab833528fae68"
)
_INDEPENDENT_VALIDATION_RECORD_SHA256 = (
    "bc57a8fd08754b97176622f7543cc63725f8c89fa57bb779042e72f1c0d9eefa"
)
_BUNDLE_CANONICAL_BYTES = 10_695
_QUALIFICATION_CANONICAL_BYTES = 3_452
_CP65_VALIDATED_DIGEST_COUNT = 98_307
_CP65_UNRESOLVED_DIGEST_COUNT = 65_539
_BOUND_CHECK_ORDINALS = tuple(range(1, 18)) + (32_752, 32_753, 32_768)

_PUBLIC_API = (
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

# Kept literal and source-independent so a matching bug in CP63/CP65 cannot
# define the CP67 acceptance oracle.
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

# Final field order is part of the issued-record wire contract.  This table is
# intentionally duplicated rather than inferred from CP67.
_FIELDS = {
    "CP67PredecessorCustodyV1": (
        "schema_version",
        "v17_protocol_sha256",
        "v17_protocol_bytes",
        "v17_protocol_lf_count",
        "v17_manifest_sha256",
        "v17_manifest_bytes",
        "v17_manifest_lf_count",
        "cp61_source_sha256",
        "cp61_stable_design_sha256",
        "cp62_source_sha256",
        "cp62_bundle_record_sha256",
        "cp62_runtime_lock_record_sha256",
        "cp63_runner_source_sha256",
        "cp63_runner_bundle_record_sha256",
        "cp63_seed_capsule_contract_record_sha256",
        "cp63_schedule_contract_record_sha256",
        "cp65_authoritative_source_sha256",
        "cp65_authoritative_bundle_record_sha256",
        "cp65_independent_source_sha256",
        "cp65_independent_bundle_record_sha256",
        "cp65_schema_semantic_sha256",
        "cp65_production_schedule_schema_record_sha256",
        "cp65_schedule_request_row_digest_contract_record_sha256",
        "cp65_schedule_ordered_request_digest_contract_record_sha256",
        "cp66_source_sha256",
        "cp66_test_sha256",
        "cp66_bundle_record_sha256",
        "cp66_qualification_fixture_set_sha256",
        "record_sha256",
    ),
    "CP67DevelopmentSeedCapsuleFixtureV1": (
        "schema_version",
        "case_ordinal",
        "case_id",
        "cp61_stable_design_sha256",
        "capsule_schema",
        "capsule_purpose",
        "seed_count",
        "seed_ordinal_min",
        "seed_ordinal_max",
        "seed_encoding",
        "seed_value_formula",
        "minimum_seed_hex",
        "maximum_seed_hex",
        "distinct_seed_value_count",
        "ordered_seed_values_digest_domain",
        "ordered_seed_values_sha256",
        "source_method_id",
        "source_receipt_digest_domain",
        "source_receipt_sha256",
        "acquisition_session_digest_domain",
        "acquisition_session_sha256",
        "capsule_body_digest_domain",
        "seed_capsule_body_sha256",
        "seed_capsule_canonical_json_bytes",
        "seed_capsule_canonical_json_sha256",
        "module_owned_fixture",
        "caller_supplied_seed_or_capsule_accepted",
        "external_seed_source_bound",
        "iid_uniform_with_replacement_verified",
        "production_seed_capsule",
        "record_sha256",
    ),
    "CP67ScheduleMaterializerContractV1": (
        "schema_version",
        "contract_id",
        "development_case_id",
        "cp63_seed_capsule_contract_record_sha256",
        "cp63_schedule_contract_record_sha256",
        "cp65_production_schedule_schema_record_sha256",
        "seed_count",
        "row_count",
        "request_count",
        "logical_request_order",
        "plan_seed_assignment",
        "schedule_schema",
        "schedule_purpose",
        "development_attempt_id",
        "synthetic_freeze_receipt_digest_domain",
        "synthetic_freeze_receipt_sha256",
        "synthetic_freeze_digest_is_receipt",
        "request_instance_digest_domain",
        "request_row_digest_domain",
        "ordered_requests_digest_domain",
        "schedule_body_digest_domain",
        "seed_capsule_max_bytes",
        "schedule_max_bytes",
        "cp63_direct_seed_capsule_parser_call_count",
        "cp63_effective_seed_capsule_parser_call_count",
        "cp63_bound_request_logical_ordinals",
        "cp63_bound_request_call_count",
        "all_row_shapes_sampled_by_cp63",
        "all_seed_boundary_shapes_sampled_by_cp63",
        "remaining_rows_generated_from_frozen_formula",
        "dual_cp65_validator_required",
        "in_memory_only",
        "schedule_bytes_retained",
        "filesystem_write_permitted",
        "generic_seed_or_capsule_api_exposed",
        "production_materialization_api_exposed",
        "record_sha256",
    ),
    "CP67ScheduleMaterializationExpectationV1": (
        "schema_version",
        "case_id",
        "qualification_fixture_set_digest_domain",
        "qualification_fixture_set_sha256",
        "seed_capsule_canonical_json_bytes",
        "seed_capsule_canonical_json_sha256",
        "schedule_canonical_json_bytes",
        "schedule_canonical_json_sha256",
        "schedule_body_sha256",
        "ordered_requests_sha256",
        "first_request_row_sha256",
        "last_request_row_sha256",
        "request_count",
        "unique_request_instance_sha256_count",
        "unique_request_row_sha256_count",
        "expected_cp65_validated_digest_preimage_count",
        "expected_cp65_unresolved_digest_preimage_count",
        "expected_cp65_validated_cross_binding_count",
        "expected_cp65_unresolved_cross_binding_count",
        "authoritative_cp65_validation_record_sha256",
        "independent_cp65_validation_record_sha256",
        "record_sha256",
    ),
    "CP67ScheduleMaterializationQualificationV1": (
        "schema_version",
        "case_id",
        "qualification_fixture_set_sha256",
        "cp63_direct_seed_capsule_parser_call_count",
        "cp63_effective_seed_capsule_parser_call_count",
        "cp63_bound_request_logical_ordinals",
        "cp63_bound_request_call_count",
        "cp63_capsule_syntactically_valid",
        "cp63_source_custody_digest_bound",
        "cp63_iid_uniform_with_replacement_verified",
        "cp63_production_execution_authorized",
        "cp63_bound_request_exemplar_parity_verified",
        "all_32768_requests_materialized",
        "seed_major_order_verified",
        "all_plan_seed_values_unchanged_across_sixteen_rows",
        "schedule_canonical_json_bytes",
        "schedule_canonical_json_sha256",
        "schedule_body_sha256",
        "ordered_requests_sha256",
        "first_request_row_sha256",
        "last_request_row_sha256",
        "unique_request_instance_sha256_count",
        "unique_request_row_sha256_count",
        "authoritative_cp65_syntax_valid",
        "authoritative_cp65_intrinsic_digest_preimages_valid",
        "authoritative_cp65_all_required_digest_preimage_sources_supplied",
        "authoritative_cp65_validated_digest_preimage_count",
        "authoritative_cp65_unresolved_digest_preimage_count",
        "authoritative_cp65_digest_preimages_valid",
        "authoritative_cp65_all_required_cross_binding_targets_supplied",
        "authoritative_cp65_validated_cross_binding_count",
        "authoritative_cp65_unresolved_cross_binding_count",
        "authoritative_cp65_cross_bindings_valid",
        "authoritative_cp65_production_evidence_accepted",
        "authoritative_cp65_execution_permitted",
        "authoritative_cp65_validation_record_sha256",
        "independent_cp65_syntax_valid",
        "independent_cp65_intrinsic_digest_preimages_valid",
        "independent_cp65_all_required_digest_preimage_sources_supplied",
        "independent_cp65_validated_digest_preimage_count",
        "independent_cp65_unresolved_digest_preimage_count",
        "independent_cp65_digest_preimages_valid",
        "independent_cp65_all_required_cross_binding_targets_supplied",
        "independent_cp65_validated_cross_binding_count",
        "independent_cp65_unresolved_cross_binding_count",
        "independent_cp65_cross_bindings_valid",
        "independent_cp65_production_evidence_accepted",
        "independent_cp65_execution_permitted",
        "independent_cp65_validation_record_sha256",
        "dual_validator_structural_results_equal",
        "schedule_matches_frozen_expectation",
        "production_seed_capsule_present",
        "production_schedule_instantiated",
        "production_gate_7_evidence_present",
        "production_gate_7_state",
        "production_execution_authorized",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
        "all_development_qualification_checks_passed",
        "record_sha256",
    ),
    "CP67FullScheduleMaterializerQualificationBundleV1": (
        "schema_version",
        "scope",
        "predecessor_custody",
        "development_seed_capsule_fixture",
        "schedule_materializer_contract",
        "schedule_materialization_expectation",
        "qualification_fixture_set_sha256",
        "qualification_case_count",
        "zero_argument_builder",
        "builder_materializes_schedule",
        "qualification_runner_zero_argument",
        "closed_module_owned_fixture_only",
        "stdlib_only_import",
        "project_modules_imported_by_builder",
        "cp63_cp65_modules_lazy_imported_by_qualification_runner",
        "host_filesystem_probed",
        "clock_read",
        "rng_used",
        "network_used",
        "subprocess_api_exposed",
        "filesystem_path_api_exposed",
        "generic_seed_or_capsule_api_exposed",
        "production_materialization_api_exposed",
        "production_seed_capsule_present",
        "external_seed_source_bound",
        "iid_uniform_with_replacement_verified",
        "production_schedule_instantiated",
        "production_gate_7_evidence_present",
        "production_gate_7_state",
        "production_requests_materialized",
        "production_campaign_exposed",
        "production_execution_authorized",
        "production_execution_observed",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_status",
        "formal_test_28_closed",
        "ledger_prerequisite_id",
        "ledger_prerequisite_state",
        "ledger_total_count",
        "ledger_satisfied_count",
        "ledger_missing_count",
        "development_qualification_only",
        "record_sha256",
    ),
}

_RECORD_DOMAINS = {
    "CP67PredecessorCustodyV1": b"cp67-test28-predecessor-custody-v1\0",
    "CP67DevelopmentSeedCapsuleFixtureV1": b"cp67-test28-development-seed-capsule-fixture-v1\0",
    "CP67ScheduleMaterializerContractV1": b"cp67-test28-schedule-materializer-contract-v1\0",
    "CP67ScheduleMaterializationExpectationV1": b"cp67-test28-schedule-materialization-expectation-v1\0",
    "CP67ScheduleMaterializationQualificationV1": b"cp67-test28-schedule-materialization-qualification-v1\0",
    "CP67FullScheduleMaterializerQualificationBundleV1": b"cp67-test28-full-schedule-materializer-qualification-bundle-v1\0",
}


def _plain(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _plain(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if type(value) in (str, int, bool) or value is None:
        return value
    raise TypeError("test oracle cannot encode value")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _record_digest(record: object) -> str:
    body = _plain(record)
    assert isinstance(body, dict)
    body["record_sha256"] = _ZERO_SHA256
    return _sha256(_RECORD_DOMAINS[type(record).__name__] + _canonical(body))


def _file_metrics(path: Path) -> tuple[str, int, int]:
    payload = path.read_bytes()
    return _sha256(payload), len(payload), payload.count(b"\n")


def _bundle() -> cp67.CP67FullScheduleMaterializerQualificationBundleV1:
    return cp67.cp67_full_schedule_materializer_qualification_bundle()


def _clone(record: object, **updates: object) -> object:
    result = object.__new__(type(record))
    for field in fields(record):
        object.__setattr__(
            result,
            field.name,
            updates.get(field.name, getattr(record, field.name)),
        )
    return result


def _development_capsule(case: object) -> bytes:
    values = [f"{value:016x}" for value in range(2_048)]
    document = {
        "schema": "cp63-test28-runner-recomputation-rehearsal-v1",
        "purpose": "future-production-external-iid-uniform-uint64-with-replacement",
        "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
        "seed_count": 2_048,
        "seed_ordinals": list(range(1, 2_049)),
        "seed_encoding": "uint64-16-lowercase-hex-big-endian",
        "ordered_seed_values": values,
        "source_method_id": case.source_method_id,
        "source_receipt_sha256": case.source_receipt_sha256,
        "acquisition_session_sha256": case.acquisition_session_sha256,
        "body_sha256": _ZERO_SHA256,
    }
    document["body_sha256"] = _sha256(
        b"cp63-test28-seed-capsule-v1\0" + _canonical(document)
    )
    return _canonical(document)


def _independent_schedule_payload(
    bundle: cp67.CP67FullScheduleMaterializerQualificationBundleV1,
) -> tuple[bytes, list[dict], list[str]]:
    case = bundle.development_seed_capsule_fixture
    contract = bundle.schedule_materializer_contract
    values = [f"{value:016x}" for value in range(2_048)]
    rows: list[dict] = []
    row_digests: list[str] = []
    for logical in range(1, 32_769):
        seed_ordinal = (logical - 1) // 16 + 1
        row_ordinal = (logical - 1) % 16 + 1
        inventory = _ROW_INVENTORY[row_ordinal - 1]
        row = {
            "schema_version": "cp63-test28-runner-recomputation-rehearsal-v1",
            "seed_capsule_body_sha256": case.seed_capsule_body_sha256,
            "seed_ordinal": seed_ordinal,
            "row_ordinal": row_ordinal,
            "logical_request_ordinal": logical,
            "row_key": inventory[1],
            "fixture_id": inventory[2],
            "strategy": inventory[3],
            "budget": inventory[4],
            "plan_seed_hex": values[seed_ordinal - 1],
            "seed_free_request_sha256": inventory[5],
            "runtime_lock_sha256": _CP63_RUNTIME_LOCK_SHA256,
        }
        row["request_instance_sha256"] = _sha256(
            b"cp63-test28-bound-request-v1\0" + _canonical(row)
        )
        row["request_row_sha256"] = _ZERO_SHA256
        row["request_row_sha256"] = _sha256(
            b"cp65-test28-production-schedule-request-row-v1\0" + _canonical(row)
        )
        rows.append(row)
        row_digests.append(row["request_row_sha256"])
    ordered = _sha256(
        b"cp65-test28-production-schedule-ordered-requests-v1\0"
        + _canonical(row_digests)
    )
    schedule = {
        "schema": "cp65-test28-production-schedule-v1",
        "purpose": "production-request-schedule-custody",
        "attempt_id": contract.development_attempt_id,
        "freeze_receipt_sha256": contract.synthetic_freeze_receipt_sha256,
        "seed_capsule_body_sha256": case.seed_capsule_body_sha256,
        "schedule_contract_sha256": _CP63_SCHEDULE_CONTRACT_SHA256,
        "request_count": 32_768,
        "requests": rows,
        "ordered_request_record_sha256s": row_digests,
        "ordered_requests_sha256": ordered,
        "body_sha256": _ZERO_SHA256,
    }
    schedule["body_sha256"] = _sha256(
        b"cp65-test28-production-schedule-v1\0" + _canonical(schedule)
    )
    return _canonical(schedule), rows, row_digests


@pytest.fixture(scope="session")
def qualification_observation() -> tuple[object, dict[str, object]]:
    """Run once with every prohibited side effect converted to a hard failure."""

    if cp63 is None or cp65a is None or cp65i is None:
        pytest.skip("the CP63/CP65 runtime qualification requires Python 3.10+")
    calls: dict[str, object] = {
        "parse_direct": 0,
        "parse_effective": 0,
        "inside_bound": False,
        "bound_ordinals": [],
        "authoritative": 0,
        "independent": 0,
    }
    original_parse = cp63.cp63_validate_seed_capsule_bytes
    original_bound = cp63.cp63_bound_request
    original_authoritative = cp65a.cp65_validate_supplied_artifact_bytes
    original_independent = cp65i.cp65_independently_validate_supplied_artifact_bytes

    def parse(payload: object) -> object:
        calls["parse_effective"] = int(calls["parse_effective"]) + 1
        if calls["inside_bound"] is False:
            calls["parse_direct"] = int(calls["parse_direct"]) + 1
        assert type(payload) is bytes
        calls["capsule_raw_sha256"] = _sha256(payload)
        calls["capsule_bytes"] = len(payload)
        return original_parse(payload)

    def bound(capsule: object, logical_request_ordinal: object) -> object:
        assert type(logical_request_ordinal) is int
        cast_ordinals = calls["bound_ordinals"]
        assert isinstance(cast_ordinals, list)
        cast_ordinals.append(logical_request_ordinal)
        assert calls["inside_bound"] is False
        calls["inside_bound"] = True
        try:
            return original_bound(capsule, logical_request_ordinal)
        finally:
            calls["inside_bound"] = False

    def authoritative(
        artifact_id: object, relative_path: object, payload: object
    ) -> object:
        calls["authoritative"] = int(calls["authoritative"]) + 1
        assert artifact_id == "production-schedule"
        assert relative_path == "production_schedule.json"
        assert type(payload) is bytes
        calls["schedule_raw_sha256"] = _sha256(payload)
        calls["schedule_bytes"] = len(payload)
        return original_authoritative(artifact_id, relative_path, payload)

    def independent(
        artifact_id: object, relative_path: object, payload: object
    ) -> object:
        calls["independent"] = int(calls["independent"]) + 1
        assert artifact_id == "production-schedule"
        assert relative_path == "production_schedule.json"
        assert type(payload) is bytes
        assert calls["schedule_raw_sha256"] == _sha256(payload)
        assert calls["schedule_bytes"] == len(payload)
        return original_independent(artifact_id, relative_path, payload)

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("CP67 qualification attempted a prohibited side effect")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(cp63, "cp63_validate_seed_capsule_bytes", parse)
        monkeypatch.setattr(cp63, "cp63_bound_request", bound)
        monkeypatch.setattr(
            cp65a, "cp65_validate_supplied_artifact_bytes", authoritative
        )
        monkeypatch.setattr(
            cp65i,
            "cp65_independently_validate_supplied_artifact_bytes",
            independent,
        )
        monkeypatch.setattr(builtins, "open", forbidden)
        for name in ("open", "read_bytes", "read_text", "write_bytes", "write_text"):
            monkeypatch.setattr(Path, name, forbidden, raising=False)
        for name in (
            "open",
            "system",
            "fork",
            "posix_spawn",
            "posix_spawnp",
            "urandom",
            "getrandom",
            "stat",
            "lstat",
            "listdir",
            "scandir",
            "walk",
            "popen",
        ):
            monkeypatch.setattr(os, name, forbidden, raising=False)
        for name in (
            "run",
            "call",
            "check_call",
            "check_output",
            "getoutput",
            "getstatusoutput",
            "Popen",
        ):
            monkeypatch.setattr(subprocess, name, forbidden, raising=False)
        for name in ("time", "time_ns", "monotonic", "monotonic_ns", "perf_counter"):
            monkeypatch.setattr(time, name, forbidden, raising=False)
        for name in (
            "random",
            "getrandbits",
            "randbytes",
            "randint",
            "randrange",
            "choice",
            "choices",
            "shuffle",
            "sample",
            "uniform",
            "seed",
        ):
            monkeypatch.setattr(random, name, forbidden, raising=False)
        monkeypatch.setattr(random, "Random", forbidden)
        monkeypatch.setattr(random, "SystemRandom", forbidden)
        for name in (
            "token_bytes",
            "token_hex",
            "token_urlsafe",
            "randbelow",
            "choice",
        ):
            monkeypatch.setattr(secrets, name, forbidden, raising=False)
        monkeypatch.setattr(socket, "socket", forbidden)
        for name in (
            "create_connection",
            "create_server",
            "getaddrinfo",
            "gethostbyname",
        ):
            monkeypatch.setattr(socket, name, forbidden, raising=False)
        qualification = cp67.cp67_run_full_schedule_materializer_qualification()
    return qualification, calls


def test_cp67_live_predecessor_bytes_and_exact_custody_pins() -> None:
    assert _file_metrics(_V17_PROTOCOL) == (
        _V17_PROTOCOL_SHA256,
        _V17_PROTOCOL_BYTES,
        _V17_PROTOCOL_LF_COUNT,
    )
    assert _file_metrics(_V17_MANIFEST) == (
        _V17_MANIFEST_SHA256,
        _V17_MANIFEST_BYTES,
        _V17_MANIFEST_LF_COUNT,
    )
    custody = _bundle().predecessor_custody
    assert (
        custody.v17_protocol_sha256,
        custody.v17_protocol_bytes,
        custody.v17_protocol_lf_count,
    ) == (_V17_PROTOCOL_SHA256, _V17_PROTOCOL_BYTES, _V17_PROTOCOL_LF_COUNT)
    assert (
        custody.v17_manifest_sha256,
        custody.v17_manifest_bytes,
        custody.v17_manifest_lf_count,
    ) == (_V17_MANIFEST_SHA256, _V17_MANIFEST_BYTES, _V17_MANIFEST_LF_COUNT)
    source_pins = {
        "cp61_source_sha256": (
            _ROOT
            / "src/heterodiff/evaluation/mixed_initializer_test28_whole_seed_mc_design.py",
            _CP61_SOURCE_SHA256,
        ),
        "cp62_source_sha256": (
            _ROOT
            / "src/heterodiff/evaluation/mixed_initializer_test28_execution_capsule.py",
            _CP62_SOURCE_SHA256,
        ),
        "cp63_runner_source_sha256": (
            _ROOT
            / "src/heterodiff/evaluation/mixed_initializer_test28_runner_recomputation_rehearsal.py",
            _CP63_SOURCE_SHA256,
        ),
        "cp65_authoritative_source_sha256": (
            _ROOT
            / "src/heterodiff/evaluation/mixed_initializer_test28_production_schema_preimage_validator.py",
            _CP65_AUTHORITATIVE_SOURCE_SHA256,
        ),
        "cp65_independent_source_sha256": (
            _ROOT
            / "src/heterodiff/evaluation/mixed_initializer_test28_independent_production_schema_preimage_validator.py",
            _CP65_INDEPENDENT_SOURCE_SHA256,
        ),
        "cp66_source_sha256": (
            _ROOT
            / "src/heterodiff/evaluation/mixed_initializer_test28_runner_supervisor_classifier_qualification.py",
            _CP66_SOURCE_SHA256,
        ),
    }
    for field_name, (path, expected) in source_pins.items():
        assert _sha256(path.read_bytes()) == expected == getattr(custody, field_name)
    assert (
        _sha256(
            (
                _ROOT
                / "tests/unit/test_mixed_initializer_test28_runner_supervisor_classifier_qualification.py"
            ).read_bytes()
        )
        == _CP66_TEST_SHA256
        == custody.cp66_test_sha256
    )
    assert custody.cp61_stable_design_sha256 == _CP61_STABLE_DESIGN_SHA256
    assert custody.cp62_bundle_record_sha256 == _CP62_BUNDLE_SHA256
    assert custody.cp62_runtime_lock_record_sha256 == _CP63_RUNTIME_LOCK_SHA256
    assert custody.cp63_runner_bundle_record_sha256 == _CP63_BUNDLE_SHA256
    assert (
        custody.cp63_seed_capsule_contract_record_sha256
        == _CP63_SEED_CAPSULE_CONTRACT_SHA256
    )
    assert (
        custody.cp63_schedule_contract_record_sha256 == _CP63_SCHEDULE_CONTRACT_SHA256
    )
    assert custody.cp65_authoritative_bundle_record_sha256 == _CP65_BUNDLE_SHA256
    assert (
        custody.cp65_independent_bundle_record_sha256 == _CP65_INDEPENDENT_BUNDLE_SHA256
    )
    assert custody.cp65_schema_semantic_sha256 == _CP65_SCHEMA_SEMANTIC_SHA256
    assert (
        custody.cp65_production_schedule_schema_record_sha256
        == _CP65_SCHEDULE_SCHEMA_SHA256
    )
    assert (
        custody.cp65_schedule_request_row_digest_contract_record_sha256
        == _CP65_SCHEDULE_ROW_DIGEST_CONTRACT_SHA256
    )
    assert (
        custody.cp65_schedule_ordered_request_digest_contract_record_sha256
        == _CP65_SCHEDULE_ORDERED_DIGEST_CONTRACT_SHA256
    )
    assert custody.cp66_test_sha256 == _CP66_TEST_SHA256
    assert custody.cp66_bundle_record_sha256 == _CP66_BUNDLE_SHA256
    assert custody.cp66_qualification_fixture_set_sha256 == _CP66_FIXTURE_SET_SHA256


def test_cp67_public_surface_and_zero_argument_boundary_are_exact() -> None:
    assert tuple(cp67.__all__) == _PUBLIC_API
    assert cp67.CP67_TEST28_SCHEMA_VERSION == (
        "cp67-test28-full-schedule-materializer-qualification-v1"
    )
    assert cp67.CP67_TEST28_SCOPE == (
        "development-only-full-32768-request-schedule-materializer-qualification;"
        "one-module-owned-synthetic-capsule;zero-argument-runner;in-memory-only;"
        "cp63-syntax-and-bound-request-exemplars;dual-cp65-validation;"
        "no-public-input-api;no-filesystem;no-clock;no-rng;no-network;"
        "no-subprocess;no-external-seed-law;no-freeze-authentication;"
        "no-production-schedule;no-runner-or-campaign;no-production-execution;"
        "no-estimate-interval-or-decision;no-evidence-acceptance;"
        "no-gate-or-blocker-closure"
    )
    assert cp67.CP67_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert cp67.CP67_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID == (
        "whole_seed_full_schedule_materializer_qualification"
    )
    assert (
        cp67.CP67_TEST28_SEED_COUNT,
        cp67.CP67_TEST28_ROW_COUNT,
        cp67.CP67_TEST28_REQUEST_COUNT,
    ) == (2_048, 16, 32_768)
    assert (
        cp67.CP67_TEST28_SEED_CAPSULE_MAX_BYTES,
        cp67.CP67_TEST28_SCHEDULE_MAX_BYTES,
    ) == (131_072, 67_108_864)
    assert (
        cp67.CP67_TEST28_EXPECTED_VALIDATED_DIGEST_PREIMAGE_COUNT,
        cp67.CP67_TEST28_EXPECTED_UNRESOLVED_DIGEST_PREIMAGE_COUNT,
        cp67.CP67_TEST28_EXPECTED_VALIDATED_CROSS_BINDING_COUNT,
        cp67.CP67_TEST28_EXPECTED_UNRESOLVED_CROSS_BINDING_COUNT,
    ) == (98_307, 65_539, 0, 3)
    assert issubclass(cp67.CP67ScheduleMaterializerQualificationError, RuntimeError)
    assert inspect.signature(cp67.cp67_schedule_fixture_set_sha256).parameters == {}
    assert (
        inspect.signature(
            cp67.cp67_full_schedule_materializer_qualification_bundle
        ).parameters
        == {}
    )
    assert (
        inspect.signature(
            cp67.cp67_run_full_schedule_materializer_qualification
        ).parameters
        == {}
    )
    assert tuple(inspect.signature(cp67.cp67_canonical_json_bytes).parameters) == (
        "value",
    )
    assert tuple(inspect.signature(cp67.cp67_sha256).parameters) == ("value",)
    forbidden = (
        "path",
        "seed_ingest",
        "capsule_bytes",
        "request_input",
        "campaign",
        "writer",
        "authorize",
        "execute",
        "production_materialize",
        "sign_",
    )
    assert all(
        not any(fragment in name.lower() for fragment in forbidden)
        for name in cp67.__all__
    )


def test_cp67_ast_has_only_lazy_narrow_project_imports_and_no_side_effect_calls() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    top_level_import_roots: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_import_roots.update(
                alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_import_roots.add(node.module.split(".")[0])
    assert top_level_import_roots == {
        "__future__",
        "dataclasses",
        "hashlib",
        "hmac",
        "json",
        "threading",
        "typing",
        "weakref",
    }
    project_imports = {
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith("heterodiff")
        for alias in node.names
    }
    assert project_imports == {
        (
            "heterodiff.evaluation",
            "mixed_initializer_test28_runner_recomputation_rehearsal",
        ),
        (
            "heterodiff.evaluation",
            "mixed_initializer_test28_production_schema_preimage_validator",
        ),
        (
            "heterodiff.evaluation",
            "mixed_initializer_test28_independent_production_schema_preimage_validator",
        ),
    }
    all_import_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert all_import_roots == top_level_import_roots | {"heterodiff"}
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert public_functions == {
        name for name in _PUBLIC_API if name.startswith("cp67_")
    }
    forbidden_names = {
        "open",
        "read",
        "read_bytes",
        "read_text",
        "write",
        "write_bytes",
        "write_text",
        "stat",
        "lstat",
        "listdir",
        "scandir",
        "walk",
        "glob",
        "rglob",
        "exists",
        "is_file",
        "is_dir",
        "resolve",
        "eval",
        "exec",
        "compile",
        "system",
        "fork",
        "posix_spawn",
        "posix_spawnp",
        "popen",
        "Popen",
        "run",
        "call",
        "check_call",
        "check_output",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "time",
        "time_ns",
        "monotonic",
        "monotonic_ns",
        "perf_counter",
        "process_time",
        "now",
        "utcnow",
        "today",
        "urandom",
        "random",
        "getrandbits",
        "randbytes",
        "randint",
        "randrange",
        "choice",
        "choices",
        "shuffle",
        "sample",
        "uniform",
        "seed",
        "token_bytes",
        "token_hex",
        "token_urlsafe",
        "randbelow",
        "socket",
        "connect",
        "create_connection",
        "urlopen",
        "urlretrieve",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_names
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_names
    assert "if __name__" not in source
    assert "shell=True" not in source


@pytest.mark.parametrize("class_name,expected", tuple(_FIELDS.items()))
def test_cp67_exact_record_field_order_slots_and_subclass_seal(
    class_name: str, expected: tuple[str, ...]
) -> None:
    cls = getattr(cp67, class_name)
    assert tuple(field.name for field in fields(cls)) == expected
    assert cls.__slots__ == expected
    with pytest.raises(TypeError):
        type("ForbiddenSubclass", (cls,), {})


def test_cp67_records_are_issued_sealed_nonpickleable_and_independently_digested(
    qualification_observation: tuple[object, dict[str, object]],
) -> None:
    qualification, _calls = qualification_observation
    bundle = _bundle()
    records = (
        bundle.predecessor_custody,
        bundle.development_seed_capsule_fixture,
        bundle.schedule_materializer_contract,
        bundle.schedule_materialization_expectation,
        bundle,
        qualification,
    )
    assert tuple(record.record_sha256 for record in records) == (
        _PREDECESSOR_RECORD_SHA256,
        _CASE_RECORD_SHA256,
        _CONTRACT_RECORD_SHA256,
        _EXPECTATION_RECORD_SHA256,
        _BUNDLE_RECORD_SHA256,
        _QUALIFICATION_RECORD_SHA256,
    )
    assert len(cp67.cp67_canonical_json_bytes(bundle)) == _BUNDLE_CANONICAL_BYTES
    assert len(cp67.cp67_canonical_json_bytes(qualification)) == (
        _QUALIFICATION_CANONICAL_BYTES
    )
    assert cp67.cp67_sha256(bundle) == _BUNDLE_PUBLIC_SHA256
    assert cp67.cp67_sha256(qualification) == _QUALIFICATION_PUBLIC_SHA256
    for record in records:
        assert is_dataclass(record)
        assert not hasattr(record, "__dict__")
        assert weakref.ref(record)() is record
        with pytest.raises(TypeError):
            type(record)()
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, "record_sha256", _ZERO_SHA256)
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)
        assert record.record_sha256 == _record_digest(record)
        canonical = _canonical(_plain(record))
        assert cp67.cp67_canonical_json_bytes(record) == canonical
        assert cp67.cp67_sha256(record) == _sha256(
            b"cp67-public-record-v1\0"
            + type(record).__name__.encode("ascii")
            + b"\0"
            + canonical
        )


def test_cp67_builder_is_pure_deterministic_and_does_not_load_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported: list[str] = []
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if "mixed_initializer_test28_" in name:
            imported.append(name)
            raise AssertionError("the CP67 builder imported a project dependency")
        return original_import(name, *args, **kwargs)

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("the CP67 builder performed an impure operation")

    # Exercise construction, not merely retrieval of a cache populated by an
    # earlier test.
    monkeypatch.setattr(cp67, "_BUNDLE_CACHE", None)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(time, "time", forbidden)
    monkeypatch.setattr(time, "monotonic", forbidden)
    monkeypatch.setattr(os, "urandom", forbidden)
    monkeypatch.setattr(random, "random", forbidden)
    monkeypatch.setattr(random, "getrandbits", forbidden)
    monkeypatch.setattr(secrets, "token_bytes", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    first = _bundle()
    second = _bundle()
    assert imported == []
    assert cp67.cp67_canonical_json_bytes(first) == cp67.cp67_canonical_json_bytes(
        second
    )
    assert first.record_sha256 == second.record_sha256
    assert first.zero_argument_builder is True
    assert first.builder_materializes_schedule is False


def test_cp67_closed_fixture_is_exact_and_retains_no_seed_vector() -> None:
    bundle = _bundle()
    case = bundle.development_seed_capsule_fixture
    assert case.case_ordinal == 1
    assert case.case_id == "development-seeds-0000-through-07ff"
    assert case.cp61_stable_design_sha256 == _CP61_STABLE_DESIGN_SHA256
    assert case.capsule_schema == "cp63-test28-runner-recomputation-rehearsal-v1"
    assert case.capsule_purpose == (
        "future-production-external-iid-uniform-uint64-with-replacement"
    )
    assert case.source_method_id == "development-synthetic-no-source-law"
    assert case.seed_value_formula == (
        "seed-value-equals-seed-ordinal-minus-one-encoded-as-uint64-16-"
        "lowercase-hex-big-endian"
    )
    assert (case.seed_count, case.seed_ordinal_min, case.seed_ordinal_max) == (
        2_048,
        1,
        2_048,
    )
    assert case.seed_encoding == "uint64-16-lowercase-hex-big-endian"
    assert case.minimum_seed_hex == "0000000000000000"
    assert case.maximum_seed_hex == "00000000000007ff"
    assert case.distinct_seed_value_count == 2_048
    assert case.ordered_seed_values_digest_domain == (
        "cp67-test28-development-ordered-seed-values-v1\\0"
    )
    assert case.ordered_seed_values_sha256 == _SEED_VALUE_VECTOR_SHA256
    assert case.source_receipt_sha256 == _DEVELOPMENT_SOURCE_RECEIPT_SHA256
    assert case.source_receipt_digest_domain == (
        "cp67-test28-development-synthetic-source-receipt-v1\\0"
    )
    assert case.acquisition_session_sha256 == _DEVELOPMENT_ACQUISITION_SESSION_SHA256
    assert case.acquisition_session_digest_domain == (
        "cp67-test28-development-synthetic-acquisition-session-v1\\0"
    )
    assert case.capsule_body_digest_domain == "cp63-test28-seed-capsule-v1\\0"
    assert case.seed_capsule_body_sha256 == _CAPSULE_BODY_SHA256
    assert case.seed_capsule_canonical_json_bytes == _CAPSULE_BYTES
    assert case.seed_capsule_canonical_json_sha256 == _CAPSULE_RAW_SHA256
    assert case.module_owned_fixture is True
    assert case.caller_supplied_seed_or_capsule_accepted is False
    assert case.external_seed_source_bound is False
    assert case.iid_uniform_with_replacement_verified is False
    assert case.production_seed_capsule is False
    assert (
        _sha256(b"cp67-test28-development-synthetic-source-receipt-v1\0")
        == _DEVELOPMENT_SOURCE_RECEIPT_SHA256
    )
    assert (
        _sha256(b"cp67-test28-development-synthetic-acquisition-session-v1\0")
        == _DEVELOPMENT_ACQUISITION_SESSION_SHA256
    )
    values = [f"{value:016x}" for value in range(2_048)]
    assert (
        _sha256(
            b"cp67-test28-development-ordered-seed-values-v1\0" + _canonical(values)
        )
        == _SEED_VALUE_VECTOR_SHA256
    )
    capsule = _development_capsule(case)
    assert (len(capsule), _sha256(capsule)) == (_CAPSULE_BYTES, _CAPSULE_RAW_SHA256)
    assert json.loads(capsule)["body_sha256"] == _CAPSULE_BODY_SHA256
    assert bundle.qualification_case_count == 1
    assert bundle.qualification_fixture_set_sha256 == _FIXTURE_SET_SHA256
    assert cp67.cp67_schedule_fixture_set_sha256() == _FIXTURE_SET_SHA256
    assert (
        _sha256(
            b"cp67-test28-full-schedule-qualification-fixture-set-v1\0"
            + bytes.fromhex(_CAPSULE_RAW_SHA256)
            + bytes.fromhex(_SCHEDULE_RAW_SHA256)
        )
        == _FIXTURE_SET_SHA256
    )
    plain = _plain(bundle)
    assert isinstance(plain, dict)
    serialized = _canonical(plain)
    assert b'"ordered_seed_values"' not in serialized
    assert not any(
        isinstance(value, (list, tuple)) and len(value) == 2_048
        for value in plain.values()
    )


def test_cp67_materializer_contract_is_exact_and_still_nonproduction() -> None:
    contract = _bundle().schedule_materializer_contract
    assert contract.contract_id == "cp67-development-full-schedule-materializer-v1"
    assert contract.development_case_id == "development-seeds-0000-through-07ff"
    assert (
        contract.cp63_seed_capsule_contract_record_sha256
        == _CP63_SEED_CAPSULE_CONTRACT_SHA256
    )
    assert (
        contract.cp63_schedule_contract_record_sha256 == _CP63_SCHEDULE_CONTRACT_SHA256
    )
    assert (
        contract.cp65_production_schedule_schema_record_sha256
        == _CP65_SCHEDULE_SCHEMA_SHA256
    )
    assert (contract.seed_count, contract.row_count, contract.request_count) == (
        2_048,
        16,
        32_768,
    )
    assert contract.logical_request_order == "(seed_ordinal-1)*16+row_ordinal"
    assert contract.plan_seed_assignment == "external-seed-value-unchanged"
    assert contract.schedule_schema == "cp65-test28-production-schedule-v1"
    assert contract.schedule_purpose == "production-request-schedule-custody"
    assert contract.development_attempt_id == "attempt-cp67-development-only"
    assert (
        contract.synthetic_freeze_receipt_sha256
        == _DEVELOPMENT_FREEZE_NONRECEIPT_SHA256
    )
    assert contract.synthetic_freeze_receipt_digest_domain == (
        "cp67-test28-development-no-freeze-receipt-v1\\0"
    )
    assert (
        _sha256(b"cp67-test28-development-no-freeze-receipt-v1\0")
        == _DEVELOPMENT_FREEZE_NONRECEIPT_SHA256
    )
    assert contract.synthetic_freeze_digest_is_receipt is False
    assert contract.seed_capsule_max_bytes == 131_072
    assert contract.schedule_max_bytes == 67_108_864
    assert contract.request_instance_digest_domain == "cp63-test28-bound-request-v1\\0"
    assert contract.request_row_digest_domain == (
        "cp65-test28-production-schedule-request-row-v1\\0"
    )
    assert contract.ordered_requests_digest_domain == (
        "cp65-test28-production-schedule-ordered-requests-v1\\0"
    )
    assert (
        contract.schedule_body_digest_domain == "cp65-test28-production-schedule-v1\\0"
    )
    assert contract.cp63_direct_seed_capsule_parser_call_count == 1
    assert contract.cp63_effective_seed_capsule_parser_call_count == 21
    assert contract.cp63_bound_request_logical_ordinals == _BOUND_CHECK_ORDINALS
    assert contract.cp63_bound_request_call_count == 20
    assert contract.all_row_shapes_sampled_by_cp63 is True
    assert contract.all_seed_boundary_shapes_sampled_by_cp63 is True
    assert contract.remaining_rows_generated_from_frozen_formula is True
    assert contract.dual_cp65_validator_required is True
    assert contract.in_memory_only is True
    assert contract.schedule_bytes_retained is False
    assert contract.filesystem_write_permitted is False
    assert contract.generic_seed_or_capsule_api_exposed is False
    assert contract.production_materialization_api_exposed is False


def test_cp67_frozen_expectation_pins_every_full_schedule_metric() -> None:
    expectation = _bundle().schedule_materialization_expectation
    assert expectation.case_id == "development-seeds-0000-through-07ff"
    assert expectation.qualification_fixture_set_digest_domain == (
        "cp67-test28-full-schedule-qualification-fixture-set-v1\\0"
    )
    assert expectation.qualification_fixture_set_sha256 == _FIXTURE_SET_SHA256
    assert (
        expectation.seed_capsule_canonical_json_bytes,
        expectation.seed_capsule_canonical_json_sha256,
    ) == (_CAPSULE_BYTES, _CAPSULE_RAW_SHA256)
    assert (
        expectation.schedule_canonical_json_bytes,
        expectation.schedule_canonical_json_sha256,
        expectation.schedule_body_sha256,
        expectation.ordered_requests_sha256,
        expectation.first_request_row_sha256,
        expectation.last_request_row_sha256,
    ) == (
        _SCHEDULE_BYTES,
        _SCHEDULE_RAW_SHA256,
        _SCHEDULE_BODY_SHA256,
        _ORDERED_REQUESTS_SHA256,
        _FIRST_REQUEST_ROW_SHA256,
        _LAST_REQUEST_ROW_SHA256,
    )
    assert (
        expectation.request_count,
        expectation.unique_request_instance_sha256_count,
        expectation.unique_request_row_sha256_count,
    ) == (32_768, 32_768, 32_768)
    assert (
        expectation.expected_cp65_validated_digest_preimage_count,
        expectation.expected_cp65_unresolved_digest_preimage_count,
        expectation.expected_cp65_validated_cross_binding_count,
        expectation.expected_cp65_unresolved_cross_binding_count,
    ) == (98_307, 65_539, 0, 3)
    assert expectation.authoritative_cp65_validation_record_sha256 == (
        _AUTHORITATIVE_VALIDATION_RECORD_SHA256
    )
    assert expectation.independent_cp65_validation_record_sha256 == (
        _INDEPENDENT_VALIDATION_RECORD_SHA256
    )


def test_cp67_run_calls_exact_lazy_dependencies_and_has_no_side_effects(
    qualification_observation: tuple[object, dict[str, object]],
) -> None:
    qualification, calls = qualification_observation
    assert isinstance(qualification, cp67.CP67ScheduleMaterializationQualificationV1)
    assert calls["parse_direct"] == 1
    assert calls["parse_effective"] == 21
    assert calls["bound_ordinals"] == list(_BOUND_CHECK_ORDINALS)
    assert calls["authoritative"] == 1
    assert calls["independent"] == 1
    assert calls["capsule_raw_sha256"] == _CAPSULE_RAW_SHA256
    assert calls["capsule_bytes"] == _CAPSULE_BYTES
    assert calls["schedule_raw_sha256"] == _SCHEDULE_RAW_SHA256
    assert calls["schedule_bytes"] == _SCHEDULE_BYTES


def test_cp67_full_schedule_matches_independent_32768_row_digest_oracle_and_cp65(
    qualification_observation: tuple[object, dict[str, object]],
) -> None:
    qualification, _calls = qualification_observation
    bundle = _bundle()
    payload, rows, row_digests = _independent_schedule_payload(bundle)
    assert len(payload) == _SCHEDULE_BYTES
    assert _sha256(payload) == _SCHEDULE_RAW_SHA256
    assert len(rows) == len(row_digests) == 32_768
    assert len({row["request_instance_sha256"] for row in rows}) == 32_768
    assert len(set(row_digests)) == 32_768
    assert row_digests[0] == _FIRST_REQUEST_ROW_SHA256
    assert row_digests[-1] == _LAST_REQUEST_ROW_SHA256
    assert all(tuple(row) == _REQUEST_KEYS for row in rows)
    for index, row in enumerate(rows, 1):
        seed_ordinal = (index - 1) // 16 + 1
        row_ordinal = (index - 1) % 16 + 1
        inventory = _ROW_INVENTORY[row_ordinal - 1]
        assert row["logical_request_ordinal"] == index
        assert row["seed_ordinal"] == seed_ordinal
        assert row["row_ordinal"] == row_ordinal
        assert row["plan_seed_hex"] == f"{seed_ordinal - 1:016x}"
        assert (
            row["row_key"],
            row["fixture_id"],
            row["strategy"],
            row["budget"],
            row["seed_free_request_sha256"],
        ) == inventory[1:]
        instance = {key: row[key] for key in _REQUEST_KEYS[:12]}
        assert row["request_instance_sha256"] == _sha256(
            b"cp63-test28-bound-request-v1\0" + _canonical(instance)
        )
        zeroed = dict(row)
        zeroed["request_row_sha256"] = _ZERO_SHA256
        assert row["request_row_sha256"] == _sha256(
            b"cp65-test28-production-schedule-request-row-v1\0" + _canonical(zeroed)
        )
    document = json.loads(payload)
    assert tuple(document) == tuple(sorted(_SCHEDULE_KEYS))
    assert document["ordered_request_record_sha256s"] == row_digests
    assert document["ordered_requests_sha256"] == _ORDERED_REQUESTS_SHA256
    assert document["body_sha256"] == _SCHEDULE_BODY_SHA256
    assert document["freeze_receipt_sha256"] == _DEVELOPMENT_FREEZE_NONRECEIPT_SHA256
    assert document["seed_capsule_body_sha256"] == _CAPSULE_BODY_SHA256
    assert document["schedule_contract_sha256"] == _CP63_SCHEDULE_CONTRACT_SHA256

    authoritative = cp65a.cp65_validate_supplied_artifact_bytes(
        "production-schedule", "production_schedule.json", payload
    )
    independent = cp65i.cp65_independently_validate_supplied_artifact_bytes(
        "production-schedule", "production_schedule.json", payload
    )
    for result in (authoritative, independent):
        assert result.syntax_valid is True
        assert result.intrinsic_digest_preimages_valid is True
        assert result.input_sha256s == (_SCHEDULE_RAW_SHA256,)
        assert result.input_byte_lengths == (_SCHEDULE_BYTES,)
        assert result.validated_body_sha256s == (_SCHEDULE_BODY_SHA256,)
        assert result.validated_digest_preimage_count == _CP65_VALIDATED_DIGEST_COUNT
        assert result.unresolved_digest_preimage_count == _CP65_UNRESOLVED_DIGEST_COUNT
        assert result.validated_cross_binding_count == 0
        assert result.unresolved_cross_binding_count == 3
        assert result.digest_preimages_valid is False
        assert result.cross_bindings_valid is False
        assert result.parser_input_resource_limits_satisfied is True
        assert result.production_evidence_accepted is False
        assert result.gate_transition_permitted is False
        assert result.launch_authorized is False
        assert result.execution_permitted is False
        assert result.definition_only is True
    assert authoritative.record_sha256 == _AUTHORITATIVE_VALIDATION_RECORD_SHA256
    assert independent.record_sha256 == _INDEPENDENT_VALIDATION_RECORD_SHA256
    structural_fields = (
        "input_artifact_ids",
        "input_relative_paths",
        "input_sha256s",
        "input_byte_lengths",
        "validated_artifact_ids",
        "validated_relative_paths",
        "validated_body_sha256s",
        "syntax_valid",
        "intrinsic_digest_preimages_valid",
        "all_required_digest_preimage_sources_supplied",
        "validated_digest_preimage_count",
        "unresolved_digest_preimage_count",
        "digest_preimages_valid",
        "all_required_cross_binding_targets_supplied",
        "validated_cross_binding_count",
        "unresolved_cross_binding_count",
        "cross_bindings_valid",
        "parser_input_resource_limits_satisfied",
        "production_evidence_accepted",
        "gate_transition_permitted",
        "launch_authorized",
        "execution_permitted",
        "definition_only",
    )
    assert tuple(getattr(authoritative, name) for name in structural_fields) == tuple(
        getattr(independent, name) for name in structural_fields
    )
    assert qualification.schedule_canonical_json_sha256 == _SCHEDULE_RAW_SHA256
    assert qualification.schedule_body_sha256 == _SCHEDULE_BODY_SHA256
    assert qualification.schedule_canonical_json_bytes == _SCHEDULE_BYTES
    assert qualification.first_request_row_sha256 == _FIRST_REQUEST_ROW_SHA256
    assert qualification.last_request_row_sha256 == _LAST_REQUEST_ROW_SHA256
    assert qualification.ordered_requests_sha256 == _ORDERED_REQUESTS_SHA256
    assert qualification.authoritative_cp65_validation_record_sha256 == (
        authoritative.record_sha256
    )
    assert qualification.independent_cp65_validation_record_sha256 == (
        independent.record_sha256
    )


def test_cp67_compact_qualification_receipt_has_exact_parity_and_no_payload(
    qualification_observation: tuple[object, dict[str, object]],
) -> None:
    qualification, _calls = qualification_observation
    expectation = _bundle().schedule_materialization_expectation
    assert qualification.case_id == expectation.case_id
    assert qualification.qualification_fixture_set_sha256 == _FIXTURE_SET_SHA256
    assert qualification.cp63_direct_seed_capsule_parser_call_count == 1
    assert qualification.cp63_effective_seed_capsule_parser_call_count == 21
    assert qualification.cp63_bound_request_logical_ordinals == _BOUND_CHECK_ORDINALS
    assert qualification.cp63_bound_request_call_count == 20
    assert qualification.schedule_canonical_json_bytes == _SCHEDULE_BYTES
    assert qualification.authoritative_cp65_validated_digest_preimage_count == 98_307
    assert qualification.independent_cp65_validated_digest_preimage_count == 98_307
    assert qualification.authoritative_cp65_unresolved_digest_preimage_count == 65_539
    assert qualification.independent_cp65_unresolved_digest_preimage_count == 65_539
    expected_true = (
        "cp63_capsule_syntactically_valid",
        "cp63_source_custody_digest_bound",
        "cp63_bound_request_exemplar_parity_verified",
        "all_32768_requests_materialized",
        "seed_major_order_verified",
        "all_plan_seed_values_unchanged_across_sixteen_rows",
        "authoritative_cp65_syntax_valid",
        "authoritative_cp65_intrinsic_digest_preimages_valid",
        "independent_cp65_syntax_valid",
        "independent_cp65_intrinsic_digest_preimages_valid",
        "dual_validator_structural_results_equal",
        "schedule_matches_frozen_expectation",
        "all_development_qualification_checks_passed",
    )
    assert all(getattr(qualification, name) is True for name in expected_true)
    assert qualification.cp63_iid_uniform_with_replacement_verified is False
    assert qualification.cp63_production_execution_authorized is False
    assert (
        qualification.authoritative_cp65_all_required_digest_preimage_sources_supplied
        is False
    )
    assert (
        qualification.independent_cp65_all_required_digest_preimage_sources_supplied
        is False
    )
    assert qualification.authoritative_cp65_digest_preimages_valid is False
    assert qualification.independent_cp65_digest_preimages_valid is False
    assert (
        qualification.authoritative_cp65_all_required_cross_binding_targets_supplied
        is False
    )
    assert (
        qualification.independent_cp65_all_required_cross_binding_targets_supplied
        is False
    )
    assert qualification.authoritative_cp65_validated_cross_binding_count == 0
    assert qualification.independent_cp65_validated_cross_binding_count == 0
    assert qualification.authoritative_cp65_unresolved_cross_binding_count == 3
    assert qualification.independent_cp65_unresolved_cross_binding_count == 3
    assert qualification.authoritative_cp65_cross_bindings_valid is False
    assert qualification.independent_cp65_cross_bindings_valid is False
    assert qualification.authoritative_cp65_production_evidence_accepted is False
    assert qualification.independent_cp65_production_evidence_accepted is False
    assert qualification.authoritative_cp65_execution_permitted is False
    assert qualification.independent_cp65_execution_permitted is False
    assert qualification.production_seed_capsule_present is False
    assert qualification.production_schedule_instantiated is False
    assert qualification.production_gate_7_evidence_present is False
    assert qualification.production_gate_7_state == "MISSING"
    assert qualification.production_execution_authorized is False
    assert qualification.runner_and_recomputation_blocker_closed is False
    assert qualification.formal_test_28_closed is False
    payload = cp67.cp67_canonical_json_bytes(qualification)
    assert len(payload) < 16_384
    assert b'"ordered_seed_values"' not in payload
    assert b'"requests"' not in payload
    assert b'"plan_seed_hex"' not in payload
    for name, value in vars(cp67).items():
        if name.startswith("__"):
            continue
        assert not (isinstance(value, bytes) and len(value) >= _CAPSULE_BYTES)
        assert not (isinstance(value, (list, tuple)) and len(value) >= 2_048)
        assert not (
            isinstance(value, dict)
            and ("ordered_seed_values" in value or "requests" in value)
        )


def test_cp67_canonical_encoder_and_public_hash_reject_forgery_and_resources(
    qualification_observation: tuple[object, dict[str, object]],
) -> None:
    qualification, _calls = qualification_observation
    bundle = _bundle()
    for value in (None, True, 1, "x", b"x", {}, [], object()):
        with pytest.raises((TypeError, ValueError)):
            cp67.cp67_canonical_json_bytes(value)
        with pytest.raises((TypeError, ValueError)):
            cp67.cp67_sha256(value)
    for record in (
        bundle.development_seed_capsule_fixture,
        bundle.schedule_materialization_expectation,
        bundle,
        qualification,
    ):
        forged = _clone(record)
        with pytest.raises(TypeError):
            cp67.cp67_canonical_json_bytes(forged)
        with pytest.raises(TypeError):
            cp67.cp67_sha256(forged)
    assert len(cp67.cp67_canonical_json_bytes(bundle)) < 131_072


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="hostile dependency injection requires the importable CP63 runtime",
)
def test_cp67_error_surface_is_stable_fail_closed_and_normalizes_dependencies() -> None:
    sentinel = cp67.CP67ScheduleMaterializerQualificationError(
        "CP67_TEST_SENTINEL", "sentinel message"
    )
    assert sentinel.code == "CP67_TEST_SENTINEL"
    assert sentinel.args == ("sentinel message",)

    def import_failure(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        del globals, locals, level
        if name == "heterodiff.evaluation" and fromlist:
            raise ImportError("hostile predecessor import failure")
        return original_import(name, None, None, fromlist, 0)

    original_import = builtins.__import__
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(builtins, "__import__", import_failure)
        with pytest.raises(cp67.CP67ScheduleMaterializerQualificationError) as caught:
            cp67.cp67_run_full_schedule_materializer_qualification()
        assert caught.value.code == "CP67_PREDECESSOR_IMPORT_FAILED"
        assert isinstance(caught.value.__cause__, ImportError)

    def fail_with(error: BaseException) -> object:
        raise error

    cases = (
        (
            ValueError("hostile predecessor value"),
            "CP67_PREDECESSOR_OR_VALIDATION_FAILURE",
        ),
        (MemoryError("hostile resource exhaustion"), "CP67_RESOURCE_EXHAUSTED"),
        (sentinel, "CP67_TEST_SENTINEL"),
    )
    for error, expected_code in cases:
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(
                cp63,
                "cp63_runner_recomputation_rehearsal_bundle",
                lambda error=error: fail_with(error),
            )
            with pytest.raises(
                cp67.CP67ScheduleMaterializerQualificationError
            ) as caught:
                cp67.cp67_run_full_schedule_materializer_qualification()
            assert caught.value.code == expected_code
            if error is sentinel:
                assert caught.value is sentinel
            else:
                assert caught.value.__cause__ is error

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            cp67, "_DEVELOPMENT_ORDERED_SEED_VALUES_SHA256", _ZERO_SHA256
        )
        with pytest.raises(cp67.CP67ScheduleMaterializerQualificationError) as caught:
            cp67.cp67_run_full_schedule_materializer_qualification()
        assert caught.value.code == "CP67_SEED_VECTOR_PIN_MISMATCH"

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(cp67, "CP67_TEST28_SEED_CAPSULE_MAX_BYTES", 1)
        with pytest.raises(cp67.CP67ScheduleMaterializerQualificationError) as caught:
            cp67.cp67_run_full_schedule_materializer_qualification()
        assert caught.value.code == "CP67_CAPSULE_RESOURCE_LIMIT"


def test_cp67_case_contract_bundle_and_qualification_tamper_break_custody(
    qualification_observation: tuple[object, dict[str, object]],
) -> None:
    qualification, _calls = qualification_observation
    bundle = _bundle()
    case = bundle.development_seed_capsule_fixture
    forged_case = _clone(case, maximum_seed_hex="0000000000000800")
    assert forged_case.record_sha256 != _record_digest(forged_case)
    assert _record_digest(forged_case) != case.record_sha256
    forged_contract = _clone(
        bundle.schedule_materializer_contract, request_count=32_767
    )
    assert forged_contract.record_sha256 != _record_digest(forged_contract)
    forged_bundle = _clone(bundle, production_gate_7_state="PASS")
    assert forged_bundle.record_sha256 != _record_digest(forged_bundle)
    forged_qualification = _clone(
        qualification, schedule_canonical_json_sha256="f" * 64
    )
    assert forged_qualification.record_sha256 != _record_digest(forged_qualification)
    for forged in (forged_case, forged_contract, forged_bundle, forged_qualification):
        with pytest.raises(TypeError):
            cp67.cp67_canonical_json_bytes(forged)


def test_cp67_cyclic_cached_bundle_mutation_isolated_process_stays_fail_closed() -> None:
    source_root = str(_ROOT / "src")
    program = f"""
import sys
sys.path.insert(0, {source_root!r})
import heterodiff.evaluation.mixed_initializer_test28_full_schedule_materializer_qualification as cp67

bundle = cp67.cp67_full_schedule_materializer_qualification_bundle()
cycle = []
cycle.append(cycle)
object.__setattr__(bundle, "scope", cycle)

operations = (
    ("canonical", lambda: cp67.cp67_canonical_json_bytes(bundle)),
    ("public-hash", lambda: cp67.cp67_sha256(bundle)),
    ("cached-retrieval-1", cp67.cp67_full_schedule_materializer_qualification_bundle),
    ("cached-retrieval-2", cp67.cp67_full_schedule_materializer_qualification_bundle),
)
for label, operation in operations:
    try:
        operation()
    except cp67.CP67ScheduleMaterializerQualificationError as exc:
        assert type(exc) is cp67.CP67ScheduleMaterializerQualificationError, label
        assert exc.code == "CP67_CANONICAL_RESOURCE_VIOLATION", label
        assert str(exc) == "the CP67 canonical value exceeds its closed graph limits", label
        assert not isinstance(exc, RecursionError), label
    except RecursionError as exc:
        raise AssertionError(label + " leaked raw RecursionError") from exc
    except BaseException as exc:
        raise AssertionError(label + " raised " + type(exc).__name__) from exc
    else:
        raise AssertionError(label + " accepted a cyclic issued record")
print("cp67-cycle-hostile-ok")
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", program],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "cp67-cycle-hostile-ok\n"
    assert completed.stderr == ""


@pytest.mark.parametrize(
    "case_id",
    (
        "depth",
        "node-count",
        "key-length",
        "string-length",
        "integer-magnitude",
        "public-record-bytes",
        "internal-schedule-bytes",
    ),
)
def test_cp67_canonical_graph_limits_isolated_process_fail_closed(
    case_id: str,
) -> None:
    source_root = str(_ROOT / "src")
    program = f"""
import json
import sys
sys.path.insert(0, {source_root!r})
import heterodiff.evaluation.mixed_initializer_test28_full_schedule_materializer_qualification as cp67

case_id = {case_id!r}
assert cp67._MAXIMUM_CANONICAL_DEPTH == 64
assert cp67._MAXIMUM_CANONICAL_NODE_COUNT == 1_048_576
assert cp67._MAXIMUM_CANONICAL_KEY_CHARACTERS == 256
assert cp67._MAXIMUM_CANONICAL_STRING_CHARACTERS == 131_072
assert cp67._MAXIMUM_CANONICAL_INTEGER_ABSOLUTE == 2**63 - 1
assert cp67._MAXIMUM_CANONICAL_RECORD_BYTES == 131_072
assert cp67._MAXIMUM_CANONICAL_BYTES == 67_108_864

def require_resource_violation(label, operation):
    try:
        operation()
    except cp67.CP67ScheduleMaterializerQualificationError as exc:
        assert type(exc) is cp67.CP67ScheduleMaterializerQualificationError, label
        assert exc.code == "CP67_CANONICAL_RESOURCE_VIOLATION", label
        assert str(exc) == "the CP67 canonical value exceeds its closed graph limits", label
        assert not isinstance(exc, RecursionError), label
    except RecursionError as exc:
        raise AssertionError(label + " leaked raw RecursionError") from exc
    except BaseException as exc:
        raise AssertionError(label + " raised " + type(exc).__name__) from exc
    else:
        raise AssertionError(label + " accepted an oversized canonical graph")

def exact_ascii_string_list(canonical_bytes):
    full_count = (canonical_bytes - 4) // 1_027
    tail_characters = canonical_bytes - (1_027 * full_count + 4)
    value = ["x" * 1_024] * full_count + ["x" * tail_characters]
    assert max(map(len, value)) < cp67._MAXIMUM_CANONICAL_STRING_CHARACTERS
    assert 3 * len(value) + sum(map(len, value)) + 1 == canonical_bytes
    return value

if case_id == "node-count":
    value = [None] * cp67._MAXIMUM_CANONICAL_NODE_COUNT
    operations = (
        ("node-count-1", lambda: cp67._plain_json_bytes(value)),
        ("node-count-2", lambda: cp67._plain_json_bytes(value)),
    )
elif case_id == "internal-schedule-bytes":
    value = exact_ascii_string_list(cp67._MAXIMUM_CANONICAL_BYTES + 1)
    assert len(value) < cp67._MAXIMUM_CANONICAL_NODE_COUNT
    operations = (
        ("internal-schedule-bytes-1", lambda: cp67._plain_json_bytes(value)),
        ("internal-schedule-bytes-2", lambda: cp67._plain_json_bytes(value)),
    )
else:
    bundle = cp67.cp67_full_schedule_materializer_qualification_bundle()
    if case_id == "depth":
        value = "leaf"
        for _ in range(cp67._MAXIMUM_CANONICAL_DEPTH):
            value = [value]
    elif case_id == "key-length":
        value = {{"k" * (cp67._MAXIMUM_CANONICAL_KEY_CHARACTERS + 1): None}}
    elif case_id == "string-length":
        value = "s" * (cp67._MAXIMUM_CANONICAL_STRING_CHARACTERS + 1)
    elif case_id == "integer-magnitude":
        value = cp67._MAXIMUM_CANONICAL_INTEGER_ABSOLUTE + 1
    elif case_id == "public-record-bytes":
        baseline_bytes = len(cp67.cp67_canonical_json_bytes(bundle))
        old_scope_bytes = len(json.dumps(bundle.scope, ensure_ascii=True))
        value_bytes = cp67._MAXIMUM_CANONICAL_RECORD_BYTES + 1 - (
            baseline_bytes - old_scope_bytes
        )
        value = exact_ascii_string_list(value_bytes)
        assert len(value) < cp67._MAXIMUM_CANONICAL_NODE_COUNT
    else:
        raise AssertionError("unknown hostile case")
    object.__setattr__(bundle, "scope", value)
    operations = (
        ("canonical", lambda: cp67.cp67_canonical_json_bytes(bundle)),
        ("public-hash", lambda: cp67.cp67_sha256(bundle)),
        ("cached-retrieval-1", cp67.cp67_full_schedule_materializer_qualification_bundle),
        ("cached-retrieval-2", cp67.cp67_full_schedule_materializer_qualification_bundle),
    )

for label, operation in operations:
    require_resource_violation(label, operation)
print("cp67-canonical-resource-hostile-ok:" + case_id)
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", program],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == f"cp67-canonical-resource-hostile-ok:{case_id}\n"
    assert completed.stderr == ""


def test_cp67_run_is_deterministic_and_returns_no_schedule_payload(
    qualification_observation: tuple[object, dict[str, object]],
) -> None:
    first, _calls = qualification_observation
    second = cp67.cp67_run_full_schedule_materializer_qualification()
    assert cp67.cp67_canonical_json_bytes(first) == cp67.cp67_canonical_json_bytes(
        second
    )
    assert first.record_sha256 == second.record_sha256
    assert not hasattr(first, "requests")
    assert not hasattr(first, "ordered_seed_values")


def test_cp67_nonclaims_and_ledger_22_18_4_remain_fail_closed() -> None:
    bundle = _bundle()
    expected_false = (
        "builder_materializes_schedule",
        "project_modules_imported_by_builder",
        "host_filesystem_probed",
        "clock_read",
        "rng_used",
        "network_used",
        "subprocess_api_exposed",
        "filesystem_path_api_exposed",
        "generic_seed_or_capsule_api_exposed",
        "production_materialization_api_exposed",
        "production_seed_capsule_present",
        "external_seed_source_bound",
        "iid_uniform_with_replacement_verified",
        "production_schedule_instantiated",
        "production_gate_7_evidence_present",
        "production_requests_materialized",
        "production_campaign_exposed",
        "production_execution_authorized",
        "production_execution_observed",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_closed",
    )
    assert all(getattr(bundle, name) is False for name in expected_false)
    assert bundle.zero_argument_builder is True
    assert bundle.qualification_runner_zero_argument is True
    assert bundle.closed_module_owned_fixture_only is True
    assert bundle.stdlib_only_import is True
    assert bundle.cp63_cp65_modules_lazy_imported_by_qualification_runner is True
    assert bundle.production_gate_7_state == "MISSING"
    assert bundle.development_qualification_only is True
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.ledger_prerequisite_id == (
        "whole_seed_full_schedule_materializer_qualification"
    )
    assert bundle.ledger_prerequisite_state == (
        "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS"
    )
    assert (
        bundle.ledger_total_count,
        bundle.ledger_satisfied_count,
        bundle.ledger_missing_count,
    ) == (22, 18, 4)


def test_cp67_source_and_public_records_remain_python39_compatible() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, feature_version=(3, 9))
    assert isinstance(tree, ast.Module)
    assert "dataclass(slots=True" not in source.replace(" ", "")
    match_node = getattr(ast, "Match", ())
    assert all(not isinstance(node, match_node) for node in ast.walk(tree))
    assert "except*" not in source
    assert sys.version_info >= (3, 9)
    bundle = cp67.cp67_full_schedule_materializer_qualification_bundle()
    assert bundle.record_sha256 == _BUNDLE_RECORD_SHA256
    assert cp67.cp67_sha256(bundle) == _BUNDLE_PUBLIC_SHA256
    if sys.version_info < (3, 10):
        with pytest.raises(cp67.CP67ScheduleMaterializerQualificationError) as caught:
            cp67.cp67_run_full_schedule_materializer_qualification()
        assert caught.value.code == "CP67_PREDECESSOR_OR_VALIDATION_FAILURE"
        assert isinstance(caught.value.__cause__, TypeError)
