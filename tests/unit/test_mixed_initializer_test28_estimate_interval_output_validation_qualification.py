"""Independent hostile tests for the development-only CP70 output boundary."""

from __future__ import annotations

import ast
import builtins
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
import gc
import hashlib
import inspect
import json
from math import comb
import os
from pathlib import Path
import pickle
import random
import secrets
import socket
from statistics import NormalDist
import subprocess
import sys
import time
import tracemalloc
import types
import weakref

import heterodiff.evaluation.mixed_initializer_test28_estimate_interval_output_validation_qualification as cp70
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_estimate_interval_output_validation_qualification.py"
)
_V20_PROTOCOL = _ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v20.md"
_V20_MANIFEST = _ROOT / "research/fixtures/cp50_test28_mixed_initializer_v20.json"

_SCHEMA = "cp70-test28-estimate-interval-output-validation-qualification-v1"
_CP69_SCHEMA = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_SCHEMA = "cp63-test28-independent-compact-recomputation-v1"
_CP68_SCHEMA = "cp68-test28-compact-projection-aggregation-qualification-v1"
_CP61_SCHEMA = "cp61-test28-whole-seed-mc-design-v1"
_ZERO_SHA256 = "0" * 64
_N = 2_048
_ROW_COUNT = 16
_REQUEST_COUNT = 32_768
_OBSERVABLE_COUNT = 72
_FIRST_ATTEMPT_COUNT = 170
_FEATURE_COUNT = 312
_ESTIMAND_COUNT = 554
_BINOMIAL_COUNT = 242
_TAIL_RECIPROCAL = 110_800
_K_MIN = 1_040
_HALFWIDTH = Fraction(3, 40)
_CP_STEPS = 256
_CP_DENOMINATOR = 1 << _CP_STEPS
_EXPECTED_OUTPUT_BYTES = 660_947
_EXPECTED_OUTPUT_SHA256 = (
    "f9e1bf93354af057d08ca722d2cffe1a8188d2f1e823a0173f9b6a937ddc42c3"
)
_EXPECTED_OUTPUT_BODY_SHA256 = (
    "03915b689c41c673805b1b46c76ef1dc296e3434522fbb28a153715cdd052fc5"
)
_EXPECTED_ORDERED_RECORD_SHA256 = (
    "c0dbf7e789551510c2cbf0abca77e755959609b11510c6e835d12b999abb6f06"
)
_EXPECTED_CP68_FIXTURE_SHA256 = (
    "6b8d7db706b94c32ee53efe9969e16560997e0f7b2345960e44ad4f18feb49ce"
)
_EXPECTED_CP69_FIRST_INPUT_SHA256 = (
    "de2237dfb851b4370d25cfa9b72698a73d6ea4c1c4f70b654f509999ecec34b8"
)
_EXPECTED_CP69_ORDERED_INPUT_SHA256 = (
    "754b058697dc9324611152b4987925a414520fc98dd764571321c3135d0ecc8d"
)
_EXPECTED_CP68_FIRST_PROJECTION_SHA256 = (
    "b40854463d8f441614621319f2e7a774059cd757d75284750906f84222744796"
)
_EXPECTED_CP68_ORDERED_PROJECTION_SHA256 = (
    "f898741b035d59116f6e096a1deab6c642f83dd3ad0417b7995e182584731f42"
)
_V20_PROTOCOL_SHA256 = (
    "9db40f14eade99cbfedb6d5ad8b28f04cf803f400cf8198629751f2dda46d2b0"
)
_V20_MANIFEST_SHA256 = (
    "29b718873e5ea5b3b829b267c1d917f0c6e0cc3ee9b0b1455b2b3142c4bfb909"
)
_CP68_SOURCE_SHA256 = "15afd7e4a8fb99c137faea8d57ef2bd2dc3ab3c193481883da4e205b75c16555"
_CP68_TEST_SHA256 = "5587785ad8c5fc3ac526758ce87ad91acbb5b4e1532563ceacc2e1c8d64f32e4"
_CP69_SOURCE_SHA256 = "69f2ac19c37697f8c68dd8b4b312a12e0efc46c7df05f0157c310cf97e221dac"
_CP69_TEST_SHA256 = "c8179496c3986fcc6130ebccf9371b59956630cb8eada6e343f216adea13938c"
_CP61_PROJECTION_CONTRACT_SHA256 = (
    "5b7f733e8cd2a8f3ed16915dc77fdf4c059af77ae31a1c5008a2dba9352e7a6d"
)
_M1_FEATURE_REGISTRY_SHA256 = (
    "314a54638d17f8dcb4b4313a92594306643254ab4a958aeb9d81efd5786a0406"
)
_M2_FEATURE_REGISTRY_SHA256 = (
    "e740e5927d2242aa0d945f4a252a638cae6aa4757f31ed24094c188b715929e8"
)
_COMPACT_ESTIMAND_PROJECTION_SEMANTICS = (
    "fixture-id-strategy-budget-row-key",
    "deadline-scoped-observable-cell-tag-with-timeout-at-deadline",
    "optional-one-based-rejection-first-attempt",
    "optional-cp58-feature-id-bounds-and-exact-selected-feature-value",
)

_SELECTED_COUNTS = (
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
_SELECTED_CONFIGURATION_ROSTERS = {
    "T28-M1-Q": (
        (),
        ((0, ()),),
        ((1, (Fraction(1),)),),
    ),
    "T28-M2-Q": (
        (),
        ((0, (Fraction(1, 2),)),),
        ((1, (Fraction(0), Fraction(1, 2))),),
        (
            (0, (Fraction(-1, 2),)),
            (1, (Fraction(1, 2), Fraction(-1, 2))),
        ),
    ),
}
_DEVELOPMENT_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
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
_CP60_DEFINITION_SHA256S = (
    "d4d930b46ab39a0f8a0f9cb2e65a896d3361876969fb783456ceee6e2f4d9160",
    "8366db2154dd8e56577653a8c7bf27067bd190bd76d205daab422c55396bb6f8",
    "deff18f198aacc3e70711d6b0f747be62686f181030b47e87beec301554ff782",
    "ce302962eda91df8d8af1b775de48b8fc83ed06b390fd4061e23e309fa553f38",
    "dfbc72991541d23f3cdeeecb3ddba460c839967676ffdc1d3cc92e3a8a57ebc5",
    "7fd96a443a40de0631f785a7b0d2c00611fbe5359185f81164af8e0530b758a3",
    "164690f7b8693f50892be435fd2b7e8c28ba8927209da5c39429469f2e9261f0",
    "b840599e28a1cb4a3197e503e4fe694860eb783ee66a6440d81fa6a1571c6c8b",
    "2ed1233312fde9a35d4dfa88e8bcd7ba654fec4a06e78b7e7222312a372a8a79",
    "fbc8ec85b991e495e8666c3d0a54a60e33195493d7b2365be3f58c627239f775",
    "8696cfe0a24c82af274f98adc3a6fe8ca270123f7f50f0d9595beea1cf3e0cc4",
    "6cacbb2fddcc91ddd24a0a3eac3e5a1173fabc017e1d100babe82bf6a0efa14d",
    "1eb5454bbcfde0274deec91030e22ddecb4ab7eeda164a10eac4547a8259a407",
    "4e1e978e901ef11d644c70a337990f556d0bc7f1251a8ddd27d0069438ff1dc5",
    "0d699f76655f5558788872324adff18ca347a7392428f7a342396176c16ceec2",
    "22027ae08c0a673cba4866656d868102eafc6b336d57225028dfe96bf65fa71b",
)
_M1_FEATURE_DEFINITION_SHA256S = (
    "d8cf3abf8acca4e87a529d00a7e7f0206a886997e83747f050eff27895f477ee",
    "e0e0c87cb30db0f7771729f898cc5228f74e509e62c2c7b7131aaf973ec08cd1",
    "172ac2a5e625b63a27ced9520b4f874debba34884efd08d62056f1de1fa0a278",
    "aa8e57660f7f6cc844b1262da44662af31fd4c575eb931dcda429c095af8ebfa",
    "af78aeefacaeb384bfae608451801508b501519ee582212003a080dba67e2a97",
    "fbb627761ad4e54089e9524df715e8f83b369b17584f62d63e5004c71309512b",
)
_M2_FEATURE_DEFINITION_SHA256S = (
    "d8cf3abf8acca4e87a529d00a7e7f0206a886997e83747f050eff27895f477ee",
    "e0e0c87cb30db0f7771729f898cc5228f74e509e62c2c7b7131aaf973ec08cd1",
    "b046d5d71e9030561355e018c27ebef1edcb3690c58ac4fbdfc9f4361bcde6db",
    "db712cf53aaa76e27207b7afcfc9d3c9585d101df47d2bb6b6a08318fc66cad4",
    "2fa01655462716d00b426334c8008a1673569d7b1d39838b69e3f468d9c472be",
    "58e97de0d09a09d30226fc357b8360acdca0b8e45fd509b9df026648cf802dff",
    "d83044e7f204fd1d49b9136200e959620ff28fb817608d79d1414d9cd9a1a804",
    "a256acde4b5c41c7fed3db1180334208d75445c0fad119fa0698095940d77dfc",
    "769607220a694e2c64bdc2df72ca44cc92eb7d291c71aee98149cb68679c39d8",
    "05b702adf96247be101d1a94b6a63ce2c996e070bf1b63ddeb9991251f3f88e6",
    "22c2b2232df21c580d15c085257bbf62693f449841c6ae359a8d6649d5ac2650",
    "106f66b3bfe087dc187b7802b6a149e337cc3bc092a132389b22cb7e8239f76b",
    "864d0faf9cec2e271a88bba8a476a722ef588082f6040830c040445afb71ee70",
    "c3247f44fbfdbc2fc393d5836dc6dd5b6b6bc548c4f547f4122c1077bb5dfb47",
    "c863829293cadabbf587ba4b34b630577d87017cb6372514cc61c694ea08f919",
    "56b3362c2089a99d614cb479156f02e981fab3430d4eca47ac4f75a01d5983c4",
    "44db786ec46e260b5e55a96f6fa0f01bbe5e9b59a731dd1a30a282c76e2203ce",
    "e01a3e398714b6f372fabc9ea4faf24e09310799bc2c93b33f80cf31664d9627",
    "269c4b95ae31a0ad72fbcf800817b0b6955c70a07f03951219bc600e621fd4f3",
    "f08256103f5b6a6b80dbb9fa1630feca319c9f71b53379164d77eee18195a95c",
    "7b2a560e03401377795c6f6ccd2410807f4fa0e3db7f1ce2c701f429892e931e",
    "f17da42bb42b577b42c6de7766997ea9c39d95abfffc1ae3a0b1f3b01b6598a6",
    "7c668ef4cd806de6b05cc8435b89a181499f8d8f44a4100798bccb01e1e47e10",
    "f2e1968a50c59acac378885c6a9c4a631def23b6bf63d4ad74cb763e87d5a768",
    "cad9200a6a7cfbca3a79167800baf4b8889be18345944916397477df34540968",
    "7cd22043bab94a2950c12b229a72eae6037795779dde3cce293359a8d29c0b37",
    "dae15c9acf9fe1ac5cbaff0d18f1655c915d226b590f01930fcca4edbd7ceb9c",
    "5d3169678ee34228d3a126e8e55b3f6399fb99ebb45395e0663d218a95b0fd1d",
    "9ecb7afe46ce2aad182ea4b9f05497796f5775f6507996505c449b70ec817cae",
    "e15ed152b3890021c8815a1f34e68f0e7a949b75a1386d6b4b9382308974118c",
    "1b506871d99566c407e0d458a6fe49562b3279a85e10d4f94a325b0b80d2d110",
    "1bdb07bf4f34c90d966ef99ca0936e49e3c072e6e86bbcf200800223bb8cb765",
    "61a7a2ea814b8a9c7539f153bed878f78d22846f81a25ce7df3776c7c455464e",
)
_OUTPUT_RECORD_FIELDS = (
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
_OUTPUT_ROOT_FIELDS = (
    "schema_version",
    "fixture_set_sha256",
    "request_count",
    "estimand_count",
    "estimand_estimate_intervals",
)
_INTERCHANGE_FIELDS = (
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
_PROJECTION_DIGEST_PREIMAGE_FIELDS = (
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
_RECORD_FIELDS = {
    "CP70PredecessorCustodyV1": (
        "schema_version",
        "v20_protocol_sha256",
        "v20_protocol_bytes",
        "v20_protocol_lf_count",
        "v20_manifest_sha256",
        "v20_manifest_bytes",
        "v20_manifest_lf_count",
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
        "cp68_bundle_record_sha256",
        "cp68_output_schema_record_sha256",
        "cp68_aggregation_expectation_record_sha256",
        "cp68_qualification_record_sha256",
        "cp68_fixture_set_sha256",
        "cp68_ordered_projection_sha256",
        "cp68_ordered_estimand_record_sha256s_sha256",
        "cp68_output_body_sha256",
        "cp68_output_canonical_json_bytes",
        "cp68_output_canonical_json_sha256",
        "cp69_source_sha256",
        "cp69_test_sha256",
        "cp69_bundle_record_sha256",
        "cp69_interchange_contract_record_sha256",
        "cp69_full_stream_expectation_record_sha256",
        "cp69_qualification_record_sha256",
        "cp69_fixture_set_sha256",
        "cp69_first_interchange_record_sha256",
        "cp69_ordered_interchange_record_sha256",
        "cp69_total_input_bytes",
        "cp69_ordered_target_projection_sha256",
        "record_sha256",
    ),
    "CP70SourceIndependentReducerContractV1": (
        "schema_version",
        "contract_id",
        "source_interchange_schema_version",
        "target_output_schema_version",
        "seed_count",
        "row_count",
        "request_count",
        "estimand_count",
        "logical_request_order",
        "private_stream_injection_only",
        "public_stream_api_exposed",
        "source_independent",
        "stdlib_only",
        "project_modules_imported",
        "direct_to_fixed_sufficient_statistics",
        "cp68_projection_records_created",
        "interchange_corpus_retained",
        "output_sufficient_statistic_map_sizes",
        "diagnostic_status_count_map_size",
        "aggregation_update_count",
        "cp_endpoint_table_count",
        "cp_adjacent_boundary_comparison_count",
        "maximum_interchange_bytes",
        "maximum_stream_bytes",
        "maximum_output_bytes",
        "record_sha256",
    ),
    "CP70OutputValidationContractV1": (
        "schema_version",
        "contract_id",
        "source_output_schema_version",
        "exact_root_keys",
        "exact_estimand_keys",
        "canonical_json_profile",
        "exact_fraction_encoding",
        "estimand_record_digest_domain",
        "output_body_digest_domain",
        "payload_digest_profile",
        "closed_fixture_only",
        "exact_input_bytes",
        "raise_or_sealed_return",
        "partial_result_permitted",
        "estimand_count",
        "observable_estimand_count",
        "rejection_first_attempt_estimand_count",
        "feature_estimand_count",
        "binomial_estimand_count",
        "computed_interval_count",
        "insufficient_selection_count",
        "maximum_output_bytes",
        "maximum_canonical_depth",
        "maximum_canonical_nodes",
        "maximum_key_characters",
        "maximum_text_characters",
        "maximum_integer_decimal_digits",
        "maximum_integer_bits",
        "record_sha256",
    ),
    "CP70FullReductionExpectationV1": (
        "schema_version",
        "source_fixture_set_sha256",
        "request_count",
        "total_input_bytes",
        "first_interchange_record_sha256",
        "ordered_interchange_record_sha256",
        "selected_counts_by_row",
        "rejection_selected_count",
        "rejection_exhausted_count",
        "sir_selected_count",
        "refusal_count",
        "failure_count",
        "timeout_count",
        "first_attempt_contribution_count",
        "feature_contribution_count",
        "aggregation_update_count",
        "estimand_count",
        "observable_estimand_count",
        "rejection_first_attempt_estimand_count",
        "feature_estimand_count",
        "binomial_interval_count",
        "feature_interval_count",
        "insufficient_selection_count",
        "computed_interval_count",
        "distinct_binomial_success_count_count",
        "cp_adjacent_boundary_comparison_count",
        "ordered_target_projection_sha256",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
        "record_sha256",
    ),
    "CP70EstimateIntervalOutputValidationV1": (
        "schema_version",
        "source_output_schema_version",
        "fixture_set_sha256",
        "request_count",
        "estimand_count",
        "observable_estimand_count",
        "rejection_first_attempt_estimand_count",
        "feature_estimand_count",
        "binomial_interval_count",
        "feature_interval_count",
        "insufficient_selection_count",
        "computed_interval_count",
        "selected_counts_by_row",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
        "canonical_bytes_verified",
        "record_digests_verified",
        "estimand_inventory_verified",
        "family_union_verified",
        "cross_record_invariants_verified",
        "exact_arithmetic_verified",
        "cp_endpoint_table_match_verified",
        "feature_threshold_and_clipping_verified",
        "closed_fixture_match",
        "development_fixture_only",
        "production_evidence",
        "decision_path_qualified",
        "record_sha256",
    ),
    "CP70EstimateIntervalOutputValidationQualificationV1": (
        "schema_version",
        "source_fixture_set_sha256",
        "request_count",
        "total_input_bytes",
        "logical_ordinals_complete",
        "streaming_peak_input_payload_count",
        "streaming_peak_parsed_observation_count",
        "interchange_corpus_retained",
        "cp68_projection_records_created",
        "aggregation_update_count",
        "estimand_count",
        "output_record_vector_cardinality",
        "output_records_retained_after_runner",
        "ordered_interchange_record_sha256",
        "ordered_target_projection_sha256",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
        "canonical_output_validated",
        "record_digests_verified",
        "cp_endpoint_table_independently_certified",
        "feature_threshold_and_clipping_verified",
        "target_output_matches_cp68_expectation",
        "raw_record_parsed",
        "stable_trace_parsed",
        "provenance_authenticated",
        "production_recomputation_performed",
        "production_estimate_or_interval",
        "decision_path_qualified",
        "production_evidence",
        "production_execution_authorized",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
        "all_development_qualification_checks_passed",
        "record_sha256",
    ),
    "CP70EstimateIntervalOutputValidationQualificationBundleV1": (
        "schema_version",
        "scope",
        "predecessor_custody",
        "reducer_contract",
        "output_validation_contract",
        "full_reduction_expectation",
        "zero_argument_builder",
        "builder_parses_reduces_or_validates",
        "qualification_runner_zero_argument",
        "bounded_public_closed_output_byte_validator_exposed",
        "generic_public_stream_reducer_exposed",
        "closed_module_owned_fixture_only",
        "source_independent",
        "stdlib_only_import",
        "project_modules_imported",
        "streaming_interchange",
        "full_interchange_corpus_materialized",
        "cp68_projection_records_created",
        "output_record_vector_cardinality",
        "maximum_interchange_bytes",
        "maximum_stream_bytes",
        "maximum_output_bytes",
        "host_filesystem_probed",
        "clock_read",
        "rng_used",
        "network_used",
        "subprocess_api_exposed",
        "filesystem_path_api_exposed",
        "raw_record_api_exposed",
        "stable_trace_api_exposed",
        "production_campaign_api_exposed",
        "production_estimate_or_interval",
        "decision_path_qualified",
        "production_qualification_receipt_present",
        "production_evidence_present_count",
        "production_gate_13_evidence_present",
        "production_gate_13_state",
        "production_gate_14_evidence_present",
        "production_gate_14_state",
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
    "CP70PredecessorCustodyV1": b"cp70-test28-predecessor-custody-v1",
    "CP70SourceIndependentReducerContractV1": (
        b"cp70-test28-source-independent-reducer-contract-v1"
    ),
    "CP70OutputValidationContractV1": (b"cp70-test28-output-validation-contract-v1"),
    "CP70FullReductionExpectationV1": (b"cp70-test28-full-reduction-expectation-v1"),
    "CP70EstimateIntervalOutputValidationV1": (
        b"cp70-test28-estimate-interval-output-validation-v1"
    ),
    "CP70EstimateIntervalOutputValidationQualificationV1": (
        b"cp70-test28-estimate-interval-output-validation-qualification-v1"
    ),
    "CP70EstimateIntervalOutputValidationQualificationBundleV1": (
        b"cp70-test28-estimate-interval-output-validation-qualification-bundle-v1"
    ),
}


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is Fraction:
        fraction = value
        return {"$fraction": [str(fraction.numerator), str(fraction.denominator)]}
    if type(value) in (tuple, list):
        return [_canonical(item) for item in value]
    if type(value) is dict:
        assert all(type(key) is str for key in value)
        return {key: _canonical(value[key]) for key in sorted(value)}
    if is_dataclass(value):
        return {
            item.name: _canonical(getattr(value, item.name))
            for item in fields(type(value))
        }
    raise TypeError("unsupported independent canonical value")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _decode_exact(payload: bytes) -> dict:
    value = json.loads(payload.decode("ascii"))
    assert type(value) is dict
    return value


def _row_key(row_ordinal: int) -> str:
    fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    return "row-%02d/%s/%s/budget-%d" % (
        row_ordinal,
        fixture,
        strategy,
        budget,
    )


def _projection_specs(
    fixture_id: str,
) -> tuple[tuple[int, str, tuple[Fraction, ...]], ...]:
    if fixture_id == "T28-M1-Q":
        return ((1, "axis0", (Fraction(1),)),)
    return (
        (0, "axis0", (Fraction(1),)),
        (1, "axis0", (Fraction(1), Fraction(0))),
        (1, "axis1", (Fraction(0), Fraction(1))),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )


@lru_cache(maxsize=2)
def _feature_ids(fixture_id: str) -> tuple[str, ...]:
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    dimensions = (0, 1) if fixture_id == "T28-M1-Q" else (1, 2)
    projections = tuple(
        (event_type, projection_id)
        for event_type, projection_id, _coefficients in _projection_specs(fixture_id)
    )
    result = ["count/eq/%d" % count for count in range(cap + 1)]
    result.extend("type/%d/occupancy" % index for index in range(len(dimensions)))
    for type_index, projection_id in projections:
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
    assert len(result) == (6 if fixture_id == "T28-M1-Q" else 33)
    return tuple(result)


def _feature_bounds(feature_id: str) -> tuple[Fraction, Fraction]:
    lower = (
        Fraction(-1)
        if feature_id.endswith("/odd") or feature_id.startswith("pair-projection/")
        else Fraction(0)
    )
    return lower, Fraction(1)


def _odd(value: Fraction) -> Fraction:
    return max(Fraction(-1), min(Fraction(1), value))


def _even(value: Fraction) -> Fraction:
    return Fraction(1) if abs(value) >= 1 else value * value


def _project(
    event: tuple[int, tuple[Fraction, ...]], coefficients: tuple[Fraction, ...]
) -> Fraction:
    return sum(
        (
            coefficient * coordinate
            for coefficient, coordinate in zip(coefficients, event[1])
        ),
        Fraction(0),
    )


def _exact_feature_vector(
    fixture_id: str,
    configuration: tuple[tuple[int, tuple[Fraction, ...]], ...],
) -> tuple[tuple[str, Fraction], ...]:
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    dimensions = (0, 1) if fixture_id == "T28-M1-Q" else (1, 2)
    projections = _projection_specs(fixture_id)
    projection_map = {
        (event_type, projection_id): coefficients
        for event_type, projection_id, coefficients in projections
    }
    values = []
    for count in range(cap + 1):
        values.append(Fraction(int(len(configuration) == count)))
    for event_type in range(len(dimensions)):
        values.append(
            Fraction(sum(1 for event in configuration if event[0] == event_type), cap)
        )
    for event_type, _projection_id, coefficients in projections:
        projected = tuple(
            _project(event, coefficients)
            for event in configuration
            if event[0] == event_type
        )
        values.append(sum((_odd(value) for value in projected), Fraction(0)) / cap)
        values.append(sum((_even(value) for value in projected), Fraction(0)) / cap)
    if cap == 2:
        pairs = tuple(
            (configuration[left], configuration[right])
            for left in range(len(configuration))
            for right in range(left + 1, len(configuration))
        )
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                values.append(
                    Fraction(
                        sum(
                            1
                            for left, right in pairs
                            if (left[0], right[0]) == (left_type, right_type)
                        )
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
                        total = Fraction(0)
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
                        values.append(total)
    feature_ids = _feature_ids(fixture_id)
    assert len(feature_ids) == len(values)
    return tuple(zip(feature_ids, values))


@lru_cache(maxsize=32)
def _expected_features(
    row_ordinal: int, selected: bool
) -> tuple[tuple[str, Fraction], ...]:
    if not selected:
        return ()
    fixture = _ROW_SHAPES[row_ordinal - 1][0]
    configuration = _SELECTED_CONFIGURATION_ROSTERS[fixture][
        _SELECTED_CONFIGURATION_INDEX_BY_ROW[row_ordinal - 1]
    ]
    return _exact_feature_vector(fixture, configuration)


def _expected_status(
    seed_ordinal: int, row_ordinal: int
) -> tuple[str, int | None, bool]:
    _fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    selected_count = _SELECTED_COUNTS[row_ordinal - 1]
    if seed_ordinal <= selected_count:
        if strategy == "bounded-rejection":
            return _REJECTION_CELLS[0], (seed_ordinal - 1) % budget + 1, True
        return _SIR_CELLS[0], None, True
    offset = seed_ordinal - selected_count - 1
    if strategy == "bounded-rejection":
        return _REJECTION_CELLS[1 + offset % 4], None, False
    return _SIR_CELLS[1 + offset % 3], None, False


def _observable_contribution_ordinal(row_ordinal: int, cell: str) -> int:
    prior = 0
    for candidate in range(1, row_ordinal):
        strategy = _ROW_SHAPES[candidate - 1][1]
        prior += len(
            _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        )
    strategy = _ROW_SHAPES[row_ordinal - 1][1]
    cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
    return prior + cells.index(cell) + 1


def _cycle_counts(total: int, width: int) -> tuple[int, ...]:
    quotient, remainder = divmod(total, width)
    return tuple(quotient + int(index < remainder) for index in range(width))


def _expected_observable_counts(row_ordinal: int) -> tuple[int, ...]:
    _fixture, strategy, _budget = _ROW_SHAPES[row_ordinal - 1]
    selected = _SELECTED_COUNTS[row_ordinal - 1]
    if strategy == "bounded-rejection":
        return (selected,) + _cycle_counts(_N - selected, 4)
    return (selected,) + _cycle_counts(_N - selected, 3)


def _expected_attempt_counts(selected: int, budget: int) -> tuple[int, ...]:
    quotient, remainder = divmod(selected, budget)
    return tuple(
        quotient + int(attempt <= remainder) for attempt in range(1, budget + 1)
    )


def _cp68_fixture_set_sha256() -> str:
    payload = {
        "schema_version": _CP68_SCHEMA,
        "seed_count": _N,
        "row_shapes": _ROW_SHAPES,
        "selected_counts_by_row": _SELECTED_COUNTS,
        "selected_configuration_index_by_row": _SELECTED_CONFIGURATION_INDEX_BY_ROW,
        "m1_selected_configuration_roster_exact": (
            (),
            ((0, ()),),
            ((1, (Fraction(1),)),),
        ),
        "m2_selected_configuration_roster_exact": (
            (),
            ((0, (Fraction(1, 2),)),),
            ((1, (Fraction(0), Fraction(1, 2))),),
            (
                (0, (Fraction(-1, 2),)),
                (1, (Fraction(1, 2), Fraction(-1, 2))),
            ),
        ),
        "logical_request_order": "seed-major-row-minor;logical=(seed-1)*16+row",
        "selected_status_formula": "selected iff seed_ordinal<=selected_count",
        "rejection_nonselected_status_formula": (
            "(seed-selected_count-1)%4 indexes exhausted,refusal,failure,timeout"
        ),
        "sir_nonselected_status_formula": (
            "(seed-selected_count-1)%3 indexes refusal,failure,timeout"
        ),
        "first_selected_attempt_formula": (
            "(seed_ordinal-1)%budget+1 for selected bounded-rejection"
        ),
        "plan_seed_formula": "lowercase-16-hex(seed_ordinal-1)",
        "feature_value_formula": (
            "complete frozen CP58 registry vector on the row-fixed selected "
            "configuration"
        ),
    }
    return _sha256(
        b"cp68-test28-compact-projection-fixture-set-v1\0"
        + _canonical_json_bytes(payload)
    )


def _upper_tail_compare(success_count: int, probability_numerator: int) -> int:
    """Independently compare the exact binomial upper tail with 1/110800."""

    n = _N
    k = success_count
    a = probability_numerator
    denominator = _CP_DENOMINATOR
    if k <= 0:
        return 1
    if k > n or a == 0:
        return -1
    if a == denominator:
        return 1
    complement = denominator - a
    threshold = denominator**n
    term = comb(n, k) * a**k * complement ** (n - k)
    partial = term
    index = k
    while True:
        left = partial * _TAIL_RECIPROCAL
        if left > threshold:
            return 1
        if index == n:
            return (left > threshold) - (left < threshold)
        ratio_numerator = (n - index) * a
        ratio_denominator = (index + 1) * complement
        if ratio_numerator < ratio_denominator:
            gap = ratio_denominator - ratio_numerator
            bounded_left = (partial * gap + term * ratio_numerator) * _TAIL_RECIPROCAL
            if bounded_left < threshold * gap:
                return -1
        term, remainder = divmod(term * ratio_numerator, ratio_denominator)
        assert remainder == 0
        partial += term
        index += 1


def _decimal_tail_and_derivative(
    success_count: int, probability: Decimal
) -> tuple[Decimal, Decimal]:
    complement = Decimal(1) - probability
    coefficient = Decimal(comb(_N, success_count))
    term = (
        coefficient * probability**success_count * complement ** (_N - success_count)
    )
    total = term
    for index in range(success_count, _N):
        term = (
            term * Decimal(_N - index) * probability / (Decimal(index + 1) * complement)
        )
        total += term
        if not term:
            break
    derivative = (
        Decimal(success_count)
        * coefficient
        * probability ** (success_count - 1)
        * complement ** (_N - success_count)
    )
    return total, derivative


def _candidate_lower_numerator(success_count: int) -> int:
    with localcontext() as context:
        context.prec = 120
        target = Decimal(1) / Decimal(_TAIL_RECIPROCAL)
        sample = success_count / _N
        z = NormalDist().inv_cdf(1.0 - 1.0 / _TAIL_RECIPROCAL)
        z2 = z * z
        center = (sample + z2 / (2 * _N)) / (1 + z2 / _N)
        spread = (
            z / (1 + z2 / _N) * (sample * (1 - sample) / _N + z2 / (4 * _N * _N)) ** 0.5
        )
        low = Decimal(0)
        high = Decimal(success_count) / Decimal(_N)
        probability = Decimal(repr(max(2.0**-256, min(sample, center - spread))))
        if not low < probability < high:
            probability = (low + high) / 2
        for _ in range(40):
            tail, derivative = _decimal_tail_and_derivative(success_count, probability)
            if tail < target:
                low = probability
            else:
                high = probability
            candidate = (
                probability - (tail - target) / derivative
                if derivative
                else (low + high) / 2
            )
            if candidate == probability:
                break
            if not low < candidate < high:
                candidate = (low + high) / 2
            probability = candidate
        return int(probability * Decimal(_CP_DENOMINATOR))


@lru_cache(maxsize=_N)
def _lower_cp_numerator(success_count: int) -> int:
    guess = max(0, min(_CP_DENOMINATOR - 1, _candidate_lower_numerator(success_count)))
    if _upper_tail_compare(success_count, guess) < 0:
        low = guess
        step = 1
        while True:
            high = min(_CP_DENOMINATOR, low + step)
            if _upper_tail_compare(success_count, high) >= 0:
                break
            assert high != _CP_DENOMINATOR
            low = high
            step *= 2
    else:
        high = guess
        step = 1
        while True:
            low = max(0, high - step)
            if _upper_tail_compare(success_count, low) < 0:
                break
            assert low != 0
            high = low
            step *= 2
    while high - low > 1:
        mid = (low + high) // 2
        if _upper_tail_compare(success_count, mid) < 0:
            low = mid
        else:
            high = mid
    assert _upper_tail_compare(success_count, low) < 0
    assert _upper_tail_compare(success_count, low + 1) >= 0
    return low


@lru_cache(maxsize=_N + 1)
def _cp_interval(success_count: int) -> tuple[Fraction, Fraction]:
    lower = 0 if success_count == 0 else _lower_cp_numerator(success_count)
    upper = (
        _CP_DENOMINATOR
        if success_count == _N
        else _CP_DENOMINATOR - _lower_cp_numerator(_N - success_count)
    )
    return Fraction(lower, _CP_DENOMINATOR), Fraction(upper, _CP_DENOMINATOR)


def _feature_interval(
    mean: Fraction, lower: Fraction, upper: Fraction, count: int
) -> tuple[Fraction, Fraction] | None:
    if count < _K_MIN:
        return None
    halfwidth = (upper - lower) * _HALFWIDTH
    return max(lower, mean - halfwidth), min(upper, mean + halfwidth)


@lru_cache(maxsize=1)
def _cp61_estimands() -> tuple[object, ...]:
    result = []
    ordinal = 1
    for row, (fixture, strategy, _budget) in enumerate(_ROW_SHAPES, 1):
        cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        for cell in cells:
            result.append(
                _cp61_estimand(
                    ordinal,
                    row,
                    "observable-cell",
                    observable_cell=cell,
                )
            )
            ordinal += 1
    for row, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        if strategy != "bounded-rejection":
            continue
        for attempt in range(1, budget + 1):
            result.append(
                _cp61_estimand(
                    ordinal,
                    row,
                    "rejection-first-attempt",
                    first_attempt=attempt,
                )
            )
            ordinal += 1
    for row, (fixture, _strategy, _budget) in enumerate(_ROW_SHAPES, 1):
        digests = (
            _M1_FEATURE_DEFINITION_SHA256S
            if fixture == "T28-M1-Q"
            else _M2_FEATURE_DEFINITION_SHA256S
        )
        for feature_id, feature_digest in zip(_feature_ids(fixture), digests):
            result.append(
                _cp61_estimand(
                    ordinal,
                    row,
                    "selected-conditional-feature",
                    feature=(feature_id, feature_digest),
                )
            )
            ordinal += 1
    assert ordinal == _ESTIMAND_COUNT + 1
    assert Counter(item.estimand_family for item in result) == {
        "observable-cell": _OBSERVABLE_COUNT,
        "rejection-first-attempt": _FIRST_ATTEMPT_COUNT,
        "selected-conditional-feature": _FEATURE_COUNT,
    }
    return tuple(result)


def _cp61_canonical(value: object) -> object:
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is int:
        return {
            "cp61_exact_integer_hex": ("-" if value < 0 else "+")
            + format(abs(value), "x")
        }
    if type(value) is Fraction:
        fraction = value
        return {
            "cp61_exact_fraction_v1": {
                "numerator": _cp61_canonical(fraction.numerator),
                "denominator": _cp61_canonical(fraction.denominator),
            }
        }
    if type(value) in (tuple, list):
        return [_cp61_canonical(item) for item in value]
    if type(value) is dict:
        assert all(type(key) is str for key in value)
        return {key: _cp61_canonical(value[key]) for key in sorted(value)}
    raise TypeError("unsupported independent CP61 canonical value")


def _cp61_digest(kind: str, values: dict) -> str:
    payload = dict(values)
    if "record_sha256" in payload:
        payload["record_sha256"] = _ZERO_SHA256
    encoded = json.dumps(
        _cp61_canonical(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return _sha256(
        _CP61_SCHEMA.encode("ascii") + b"\0" + kind.encode("ascii") + b"\0" + encoded
    )


def _cp61_estimand(
    ordinal: int,
    row: int,
    family: str,
    *,
    observable_cell: str | None = None,
    first_attempt: int | None = None,
    feature: tuple[str, str] | None = None,
) -> object:
    fixture, strategy, budget = _ROW_SHAPES[row - 1]
    row_key = "row-%02d/%s/%s/budget-%d" % (row, fixture, strategy, budget)
    feature_id = None
    feature_lower = None
    feature_upper = None
    feature_range = None
    target_halfwidth = None
    feature_registry_digest = None
    feature_definition_digest = None
    if family == "observable-cell":
        assert observable_cell is not None and first_attempt is None and feature is None
        id_family = "observable"
        suffix = observable_cell
        denominator_mode = "all-2048-external-seed-ordinals"
        minimum_count = _N
        uncertainty = "clopper-pearson-exact-rational-outward-bisection"
        conditional = False
    elif family == "rejection-first-attempt":
        assert observable_cell is None and first_attempt is not None and feature is None
        id_family = "rejection-first-attempt"
        suffix = "attempt-%d" % first_attempt
        denominator_mode = "all-2048-external-seed-ordinals"
        minimum_count = _N
        uncertainty = "clopper-pearson-exact-rational-outward-bisection"
        conditional = False
    else:
        assert family == "selected-conditional-feature"
        assert observable_cell is None and first_attempt is None and feature is not None
        id_family = "selected-feature"
        feature_id, feature_definition_digest = feature
        suffix = feature_id
        feature_lower, feature_upper = _feature_bounds(feature_id)
        feature_range = feature_upper - feature_lower
        target_halfwidth = feature_range * _HALFWIDTH
        feature_registry_digest = (
            _M1_FEATURE_REGISTRY_SHA256
            if fixture == "T28-M1-Q"
            else _M2_FEATURE_REGISTRY_SHA256
        )
        denominator_mode = "predeadline-selected-count-in-this-row"
        minimum_count = _K_MIN
        uncertainty = "bounded-feature-hoeffding-fixed-range-halfwidth"
        conditional = True
    is_timeout = observable_cell == "timeout-censored-at-deadline"
    validated_return = family in (
        "rejection-first-attempt",
        "selected-conditional-feature",
    ) or observable_cell in (
        _REJECTION_CELLS[0],
        _REJECTION_CELLS[1],
        _SIR_CELLS[0],
    )
    values = {
        "schema_version": _CP61_SCHEMA,
        "estimand_ordinal": ordinal,
        "estimand_id": "cp61/%s/%s/%s" % (id_family, row_key, suffix),
        "estimand_family": family,
        "row_ordinal": row,
        "fixture_id": fixture,
        "strategy": strategy,
        "budget": budget,
        "observable_cell_label": observable_cell,
        "first_attempt_one_based": first_attempt,
        "feature_id": feature_id,
        "feature_lower_bound": feature_lower,
        "feature_upper_bound": feature_upper,
        "feature_range": feature_range,
        "target_feature_halfwidth": target_halfwidth,
        "cp60_definition_record_sha256": _CP60_DEFINITION_SHA256S[row - 1],
        "cp58_feature_registry_sha256": feature_registry_digest,
        "cp58_feature_definition_sha256": feature_definition_digest,
        "denominator_mode": denominator_mode,
        "minimum_denominator_count": minimum_count,
        "uncertainty_method": uncertainty,
        "deadline_scoped_observation": True,
        "observed_before_deadline_only": not is_timeout,
        "returned_before_deadline_only": validated_return,
        "timeout_censored_at_deadline": is_timeout,
        "validated_return_before_deadline_required": validated_return,
        "timeout_censored_is_semantic_nonreturn": False,
        "conditional_on_selected": conditional,
        "familywise_error_budget": Fraction(1, 100),
        "per_estimator_error_budget": Fraction(1, 55_400),
        "per_tail_error_budget": Fraction(1, 110_800),
        "stable_trace_projection_contract_sha256": _CP61_PROJECTION_CONTRACT_SHA256,
        "estimate_observed": False,
        "interval_computed": False,
        "compact_estimand_semantic_sha256": _ZERO_SHA256,
    }
    compact_names = (
        "schema_version",
        "estimand_ordinal",
        "estimand_id",
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
        "feature_range",
        "target_feature_halfwidth",
        "denominator_mode",
        "minimum_denominator_count",
        "uncertainty_method",
        "deadline_scoped_observation",
        "observed_before_deadline_only",
        "returned_before_deadline_only",
        "timeout_censored_at_deadline",
        "validated_return_before_deadline_required",
        "timeout_censored_is_semantic_nonreturn",
        "conditional_on_selected",
        "familywise_error_budget",
        "per_estimator_error_budget",
        "per_tail_error_budget",
    )
    compact = {name: values[name] for name in compact_names}
    compact["compact_projection_semantics"] = _COMPACT_ESTIMAND_PROJECTION_SEMANTICS
    values["compact_estimand_semantic_sha256"] = _cp61_digest(
        "compact-estimand-semantic", compact
    )
    values["record_sha256"] = _ZERO_SHA256
    values["record_sha256"] = _cp61_digest("estimand", values)
    return types.SimpleNamespace(**values)


def _success_count(spec: object) -> int:
    row = spec.row_ordinal
    if spec.estimand_family == "observable-cell":
        cells = _REJECTION_CELLS if spec.strategy == "bounded-rejection" else _SIR_CELLS
        return _expected_observable_counts(row)[cells.index(spec.observable_cell_label)]
    assert spec.estimand_family == "rejection-first-attempt"
    return _expected_attempt_counts(_SELECTED_COUNTS[row - 1], spec.budget)[
        spec.first_attempt_one_based - 1
    ]


def _output_record(spec: object) -> dict:
    family = spec.estimand_family
    row = spec.row_ordinal
    if family in ("observable-cell", "rejection-first-attempt"):
        successes = _success_count(spec)
        denominator = _N
        exact_sum = None
        estimate = Fraction(successes, denominator)
        lower, upper = _cp_interval(successes)
        method = (
            "clopper-pearson-exact-rational-certified-equivalent-outward-"
            "endpoint-on-2^-256-grid-n2048"
        )
        state = "computed"
    else:
        assert family == "selected-conditional-feature"
        successes = None
        denominator = _SELECTED_COUNTS[row - 1]
        feature_values = dict(_expected_features(row, True))
        value = feature_values[spec.feature_id]
        exact_sum = None if denominator == 0 else denominator * value
        estimate = None if denominator == 0 else value
        method = "bounded-feature-fixed-range-halfwidth-clipped-to-bounds"
        interval = (
            None
            if estimate is None
            else _feature_interval(
                estimate,
                spec.feature_lower_bound,
                spec.feature_upper_bound,
                denominator,
            )
        )
        if interval is None:
            state = "insufficient-selection"
            lower = upper = None
        else:
            state = "computed"
            lower, upper = interval
    values = {
        "schema_version": _CP68_SCHEMA,
        "estimand_ordinal": spec.estimand_ordinal,
        "estimand_id": spec.estimand_id,
        "cp61_estimand_record_sha256": spec.record_sha256,
        "estimand_family": family,
        "row_ordinal": row,
        "fixture_id": spec.fixture_id,
        "strategy": spec.strategy,
        "budget": spec.budget,
        "observable_cell_label": spec.observable_cell_label,
        "first_attempt_one_based": spec.first_attempt_one_based,
        "feature_id": spec.feature_id,
        "feature_lower_bound": spec.feature_lower_bound,
        "feature_upper_bound": spec.feature_upper_bound,
        "denominator_mode": spec.denominator_mode,
        "denominator_count": denominator,
        "success_count": successes,
        "exact_feature_sum": exact_sum,
        "estimate": estimate,
        "interval_method": method,
        "interval_state": state,
        "interval_lower": lower,
        "interval_upper": upper,
        "development_fixture_only": True,
        "record_sha256": _ZERO_SHA256,
    }
    assert tuple(values) == _OUTPUT_RECORD_FIELDS
    values["record_sha256"] = _sha256(
        b"cp68-test28-estimand-estimate-interval-v1\0" + _canonical_json_bytes(values)
    )
    return values


@lru_cache(maxsize=1)
def _independent_output() -> tuple[bytes, dict, tuple[dict, ...]]:
    records = tuple(_output_record(spec) for spec in _cp61_estimands())
    assert len(records) == _ESTIMAND_COUNT
    body = {
        "schema_version": _CP68_SCHEMA,
        "fixture_set_sha256": _cp68_fixture_set_sha256(),
        "request_count": _REQUEST_COUNT,
        "estimand_count": _ESTIMAND_COUNT,
        "estimand_estimate_intervals": records,
    }
    assert tuple(body) == _OUTPUT_ROOT_FIELDS
    payload = _canonical_json_bytes(body)
    assert _cp68_fixture_set_sha256() == _EXPECTED_CP68_FIXTURE_SHA256
    assert len(payload) == _EXPECTED_OUTPUT_BYTES
    assert _sha256(payload) == _EXPECTED_OUTPUT_SHA256
    assert (
        _sha256(b"cp68-test28-estimate-interval-output-body-v1\0" + payload)
        == _EXPECTED_OUTPUT_BODY_SHA256
    )
    assert (
        _sha256(
            b"cp68-test28-ordered-estimand-record-digests-v1\0"
            + b"".join(bytes.fromhex(record["record_sha256"]) for record in records)
        )
        == _EXPECTED_ORDERED_RECORD_SHA256
    )
    return payload, body, records


def _interchange_payload(seed_ordinal: int, row_ordinal: int) -> bytes:
    fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    logical = (seed_ordinal - 1) * _ROW_COUNT + row_ordinal
    status, first_attempt, selected = _expected_status(seed_ordinal, row_ordinal)
    feature_items = _expected_features(row_ordinal, selected)
    request_identity = {
        "purpose": "cp69-synthetic-transport-request-custody-sentinel-only",
        "seed_ordinal": seed_ordinal,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": logical,
        "plan_seed_hex": "%016x" % (seed_ordinal - 1),
        "seed_free_request_sha256": _SEED_FREE_REQUEST_SHA256S[row_ordinal - 1],
    }
    request_digest = _sha256(
        b"cp69-test28-synthetic-request-instance-custody-sentinel-v1\0"
        + _canonical_json_bytes(request_identity)
    )
    stable_digest = _sha256(
        b"cp69-test28-no-stable-trace-synthetic-custody-sentinel-v1\0"
        + _canonical_json_bytes(
            {
                "purpose": "no-stable-trace-present-or-claimed",
                "request_instance_sha256": request_digest,
                "observable_cell_label": status,
                "first_selected_attempt_one_based": first_attempt,
            }
        )
    )
    values = {
        "schema_version": _CP69_SCHEMA,
        "source_semantic_schema_version": _CP63_SCHEMA,
        "seed_ordinal": seed_ordinal,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": logical,
        "row_key": _row_key(row_ordinal),
        "fixture_id": fixture,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": "%016x" % (seed_ordinal - 1),
        "seed_free_request_sha256": _SEED_FREE_REQUEST_SHA256S[row_ordinal - 1],
        "request_instance_sha256": request_digest,
        "runtime_lock_sha256": _DEVELOPMENT_RUNTIME_LOCK_SHA256,
        "stable_trace_sha256": stable_digest,
        "observable_cell_label": status,
        "observable_contribution_ordinal": _observable_contribution_ordinal(
            row_ordinal, status
        ),
        "first_selected_attempt_one_based": first_attempt,
        "selected": selected,
        "selected_feature_ids": tuple(item[0] for item in feature_items),
        "selected_feature_values": tuple(item[1] for item in feature_items),
        "record_sha256": _ZERO_SHA256,
    }
    assert tuple(values) == _INTERCHANGE_FIELDS
    values["record_sha256"] = _sha256(
        b"cp69-test28-compact-interchange-observation-v1\0"
        + _canonical_json_bytes(values)
    )
    return _canonical_json_bytes(values)


def _independent_interchange_stream() -> object:
    for seed_ordinal in range(1, _N + 1):
        for row_ordinal in range(1, _ROW_COUNT + 1):
            yield _interchange_payload(seed_ordinal, row_ordinal)


class _ProtocolBomb:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError("alien protocol accessed: %s" % name)


class _BytesSubclass(bytes):
    pass


class _IntSubclass(int):
    pass


class _IterableBomb:
    def __iter__(self) -> object:
        raise RuntimeError("iterator bomb")


class _BoundaryFailureSource:
    def __init__(self, boundary: str, failure: BaseException, first: bytes) -> None:
        self.boundary = boundary
        self.failure = failure
        self.first = first
        self.iter_calls = 0
        self.next_calls = 0

    def __iter__(self) -> object:
        self.iter_calls += 1
        if self.boundary == "iter":
            raise self.failure
        return self

    def __next__(self) -> bytes:
        self.next_calls += 1
        if self.boundary == "item":
            raise self.failure
        if self.boundary == "terminal":
            if self.next_calls == 1:
                return self.first
            raise self.failure
        raise AssertionError("unknown iterator boundary")


def _forge(record: object, **changes: object) -> object:
    forged = object.__new__(type(record))
    for item in fields(type(record)):
        object.__setattr__(
            forged,
            item.name,
            changes.get(item.name, getattr(record, item.name)),
        )
    return forged


def _mutated_payload(
    *,
    record_ordinal: int | None = None,
    record_changes: dict | None = None,
    root_changes: dict | None = None,
    retag_record: bool = True,
) -> bytes:
    _payload, body, _records = _independent_output()
    mutable = json.loads(_canonical_json_bytes(body).decode("ascii"))
    if root_changes:
        mutable.update(root_changes)
    if record_ordinal is not None:
        record = mutable["estimand_estimate_intervals"][record_ordinal - 1]
        if record_changes:
            record.update(record_changes)
        if retag_record:
            record["record_sha256"] = _ZERO_SHA256
            record["record_sha256"] = _sha256(
                b"cp68-test28-estimand-estimate-interval-v1\0"
                + _canonical_json_bytes(record)
            )
    return _canonical_json_bytes(mutable)


def _validation_error_code(payload: object) -> str:
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(payload)
    return caught.value.code


@lru_cache(maxsize=1)
def _bundle() -> object:
    return cp70.cp70_estimate_interval_output_validation_qualification_bundle()


@lru_cache(maxsize=1)
def _qualification() -> object:
    return cp70.cp70_run_estimate_interval_output_validation_qualification()


def _independent_record_sha256(record: object) -> str:
    name = type(record).__name__
    values = {
        item.name: (
            _ZERO_SHA256 if item.name == "record_sha256" else getattr(record, item.name)
        )
        for item in fields(type(record))
    }
    return _sha256(_RECORD_DOMAINS[name] + b"\0" + _canonical_json_bytes(values))


def _graph_statistics(value: object, depth: int = 0) -> tuple[int, int, int, int]:
    nodes = 1
    maximum_depth = depth
    maximum_key = 0
    maximum_text = len(value) if type(value) is str else 0
    if type(value) is dict:
        for key, item in value.items():
            maximum_key = max(maximum_key, len(key))
            child = _graph_statistics(item, depth + 1)
            nodes += child[0]
            maximum_depth = max(maximum_depth, child[1])
            maximum_key = max(maximum_key, child[2])
            maximum_text = max(maximum_text, child[3])
    elif type(value) is list:
        for item in value:
            child = _graph_statistics(item, depth + 1)
            nodes += child[0]
            maximum_depth = max(maximum_depth, child[1])
            maximum_key = max(maximum_key, child[2])
            maximum_text = max(maximum_text, child[3])
    return nodes, maximum_depth, maximum_key, maximum_text


def _retag_raw_record(record: dict) -> None:
    record["record_sha256"] = _ZERO_SHA256
    record["record_sha256"] = _sha256(
        b"cp68-test28-estimand-estimate-interval-v1\0" + _canonical_json_bytes(record)
    )


def _raw_payload_mutator(mutator: object) -> bytes:
    payload, _body, _records = _independent_output()
    value = json.loads(payload.decode("ascii"))
    mutator(value)
    return _canonical_json_bytes(value)


def _fresh_cp70_module(label: str) -> object:
    module_name = "heterodiff.evaluation._cp70_hostile_%s" % label
    assert module_name not in sys.modules
    module = types.ModuleType(module_name)
    module.__file__ = str(_SOURCE)
    module.__package__ = "heterodiff.evaluation"
    sys.modules[module_name] = module
    try:
        exec(compile(_SOURCE.read_bytes(), str(_SOURCE), "exec"), module.__dict__)
    finally:
        del sys.modules[module_name]
    return module


def _retained_cp70_graph_findings(roots: dict[str, object]) -> dict[str, list[str]]:
    findings = {
        "output_record_dicts": [],
        "output_record_vectors": [],
        "interchange_record_dicts": [],
        "interchange_corpora": [],
        "interchange_payloads": [],
        "projection_digest_preimages": [],
        "exact_output_payloads": [],
    }
    stack = list(roots.items())
    seen = set()
    while stack:
        path, value = stack.pop()
        identity = id(value)
        if identity in seen:
            continue
        seen.add(identity)
        if type(value) is bytes:
            encoded = value
            if len(encoded) == _EXPECTED_OUTPUT_BYTES and _sha256(encoded) == (
                _EXPECTED_OUTPUT_SHA256
            ):
                findings["exact_output_payloads"].append(path)
            if (
                _CP69_SCHEMA.encode("ascii") in encoded
                and b'"logical_request_ordinal"' in encoded
            ):
                findings["interchange_payloads"].append(path)
            continue
        if type(value) is dict:
            mapping = value
            keys = set(mapping)
            if keys == set(_OUTPUT_RECORD_FIELDS):
                findings["output_record_dicts"].append(path)
            if keys == set(_INTERCHANGE_FIELDS):
                findings["interchange_record_dicts"].append(path)
            if keys == set(_PROJECTION_DIGEST_PREIMAGE_FIELDS):
                findings["projection_digest_preimages"].append(path)
            for key, item in mapping.items():
                stack.append(("%s[%r]" % (path, key), item))
            continue
        if type(value) in (tuple, list):
            sequence = value
            if len(sequence) == _ESTIMAND_COUNT and all(
                type(item) is dict and set(item) == set(_OUTPUT_RECORD_FIELDS)
                for item in sequence
            ):
                findings["output_record_vectors"].append(path)
            if len(sequence) == _REQUEST_COUNT:
                findings["interchange_corpora"].append(path)
            for index, item in enumerate(sequence):
                stack.append(("%s[%d]" % (path, index), item))
            continue
        if is_dataclass(value) and type(value).__module__.startswith(
            "heterodiff.evaluation._cp70_hostile_"
        ):
            for item in fields(type(value)):
                stack.append(("%s.%s" % (path, item.name), getattr(value, item.name)))
    return findings


def _record_api_error_codes(
    module: object, record: object, getter: object | None = None
) -> tuple[str, ...]:
    operations = [
        lambda: module.cp70_canonical_json_bytes(record),
        lambda: module.cp70_sha256(record),
    ]
    if getter is not None:
        operations.extend((getter, getter))
    codes = []
    error = module.CP70EstimateIntervalOutputValidationQualificationError
    for operation in operations:
        with pytest.raises(error) as caught:
            operation()
        codes.append(caught.value.code)
    return tuple(codes)


def test_cp70_live_v20_and_predecessor_custody_pins_are_exact() -> None:
    for path, expected_sha, expected_bytes, expected_lf in (
        (_V20_PROTOCOL, _V20_PROTOCOL_SHA256, 189_122, 3_228),
        (_V20_MANIFEST, _V20_MANIFEST_SHA256, 6_084_812, 119_427),
    ):
        payload = path.read_bytes()
        assert _sha256(payload) == expected_sha
        assert len(payload) == expected_bytes
        assert payload.count(b"\n") == expected_lf
        assert payload.endswith(b"\n")

    custody = _bundle().predecessor_custody
    exact = {
        "v20_protocol_sha256": _V20_PROTOCOL_SHA256,
        "v20_protocol_bytes": 189_122,
        "v20_protocol_lf_count": 3_228,
        "v20_manifest_sha256": _V20_MANIFEST_SHA256,
        "v20_manifest_bytes": 6_084_812,
        "v20_manifest_lf_count": 119_427,
        "cp61_source_sha256": (
            "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
        ),
        "cp61_bundle_record_sha256": (
            "8c5e23661cc0ef459e700c2af5239d21ee8aafd4d9dca2ed3db6e3ce2e4a0ca0"
        ),
        "cp61_stable_design_sha256": (
            "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
        ),
        "cp61_projection_contract_record_sha256": (
            "5b7f733e8cd2a8f3ed16915dc77fdf4c059af77ae31a1c5008a2dba9352e7a6d"
        ),
        "cp63_independent_source_sha256": (
            "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc"
        ),
        "cp63_independent_test_sha256": (
            "9c0144994d690d326b51c27e57f5832489b640a049b64bffd474026a18e64a13"
        ),
        "cp63_independent_bundle_record_sha256": (
            "b219de24a17af7c06b503af07110ed863c339bca19c7457c163412ae0e76ddb9"
        ),
        "cp63_schedule_contract_record_sha256": (
            "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
        ),
        "cp68_source_sha256": _CP68_SOURCE_SHA256,
        "cp68_test_sha256": _CP68_TEST_SHA256,
        "cp68_bundle_record_sha256": (
            "b301ea4cadb8a67fa238dfa5872c874b4689a08b7baec04f1133bef7191a2a83"
        ),
        "cp68_output_schema_record_sha256": (
            "4315375d2dbd5363e2fe57147468cef51b15d074b99fcd03beed5ed004ca4c1e"
        ),
        "cp68_aggregation_expectation_record_sha256": (
            "00e5d9263386bda729b929da898d5c97174fb2606db52dfad1920089e3d3882a"
        ),
        "cp68_qualification_record_sha256": (
            "881dc5b6539504a3bf42957d7e0b4298484db0cfd637e3fe861ce9847cf81400"
        ),
        "cp68_fixture_set_sha256": _EXPECTED_CP68_FIXTURE_SHA256,
        "cp68_ordered_projection_sha256": (_EXPECTED_CP68_ORDERED_PROJECTION_SHA256),
        "cp68_ordered_estimand_record_sha256s_sha256": (
            _EXPECTED_ORDERED_RECORD_SHA256
        ),
        "cp68_output_body_sha256": _EXPECTED_OUTPUT_BODY_SHA256,
        "cp68_output_canonical_json_bytes": _EXPECTED_OUTPUT_BYTES,
        "cp68_output_canonical_json_sha256": _EXPECTED_OUTPUT_SHA256,
        "cp69_source_sha256": _CP69_SOURCE_SHA256,
        "cp69_test_sha256": _CP69_TEST_SHA256,
        "cp69_bundle_record_sha256": (
            "39c937d3d78913fb7f91b777bc676648eddac6e38696b26973eb55a55becfe26"
        ),
        "cp69_interchange_contract_record_sha256": (
            "6b64acc21209a7d32a1ddadcc45e0ced2f13eb94b87d571bd32f1d007b906caa"
        ),
        "cp69_full_stream_expectation_record_sha256": (
            "6043a6241ffc74ac14b395b052f87f22627beae43e2132992b2bb0e6a156289f"
        ),
        "cp69_qualification_record_sha256": (
            "88dd43071ecf0545c9496e80b5de682ea9b7b0a5980a5fabe5b0f46f83586ab1"
        ),
        "cp69_fixture_set_sha256": (
            "95a388b634e208b8d7b578a18657289390fe9306e23a4e5ecb3ed084771a8303"
        ),
        "cp69_first_interchange_record_sha256": (_EXPECTED_CP69_FIRST_INPUT_SHA256),
        "cp69_ordered_interchange_record_sha256": (_EXPECTED_CP69_ORDERED_INPUT_SHA256),
        "cp69_total_input_bytes": 51_506_557,
        "cp69_ordered_target_projection_sha256": (
            _EXPECTED_CP68_ORDERED_PROJECTION_SHA256
        ),
    }
    for name, expected in exact.items():
        assert getattr(custody, name) == expected, name


def test_cp70_frozen_constants_signatures_and_export_surface_are_exact() -> None:
    constants = (
        cp70.CP70_TEST28_SCHEMA_VERSION,
        cp70.CP70_TEST28_FORMAL_TEST_28_STATUS,
        cp70.CP70_TEST28_SEED_COUNT,
        cp70.CP70_TEST28_ROW_COUNT,
        cp70.CP70_TEST28_REQUEST_COUNT,
        cp70.CP70_TEST28_ESTIMAND_COUNT,
        cp70.CP70_TEST28_OBSERVABLE_ESTIMAND_COUNT,
        cp70.CP70_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
        cp70.CP70_TEST28_FEATURE_ESTIMAND_COUNT,
        cp70.CP70_TEST28_BINOMIAL_ESTIMAND_COUNT,
        cp70.CP70_TEST28_COMPUTED_INTERVAL_COUNT,
        cp70.CP70_TEST28_INSUFFICIENT_SELECTION_COUNT,
        cp70.CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES,
        cp70.CP70_TEST28_MAXIMUM_STREAM_BYTES,
        cp70.CP70_TEST28_MAXIMUM_OUTPUT_BYTES,
        cp70.CP70_TEST28_MAXIMUM_CANONICAL_DEPTH,
        cp70.CP70_TEST28_MAXIMUM_CANONICAL_NODES,
        cp70.CP70_TEST28_MAXIMUM_KEY_CHARACTERS,
        cp70.CP70_TEST28_MAXIMUM_TEXT_CHARACTERS,
        cp70.CP70_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS,
        cp70.CP70_TEST28_MAXIMUM_INTEGER_BITS,
        cp70.CP70_TEST28_SELECTED_COUNTS_BY_ROW,
    )
    assert constants == (
        _SCHEMA,
        "OPEN",
        2_048,
        16,
        32_768,
        554,
        72,
        170,
        312,
        242,
        398,
        156,
        65_536,
        67_108_864,
        1_048_576,
        8,
        32_768,
        64,
        256,
        155,
        512,
        _SELECTED_COUNTS,
    )
    assert cp70.CP70_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID == (
        "whole_seed_cp69_compact_interchange_to_cp68_estimate_interval_output_"
        "source_independent_reducer_qualification"
    )
    assert list(
        inspect.signature(
            cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes
        ).parameters
    ) == ["payload"]
    assert not inspect.signature(
        cp70.cp70_estimate_interval_output_validation_qualification_bundle
    ).parameters
    assert not inspect.signature(
        cp70.cp70_run_estimate_interval_output_validation_qualification
    ).parameters
    expected_exports = (
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
    assert cp70.__all__ == expected_exports


def test_cp70_record_field_orders_and_digest_domains_are_exact() -> None:
    validation = cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(
        _independent_output()[0]
    )
    bundle = _bundle()
    records = (
        bundle.predecessor_custody,
        bundle.reducer_contract,
        bundle.output_validation_contract,
        bundle.full_reduction_expectation,
        validation,
        _qualification(),
        bundle,
    )
    assert {type(record).__name__ for record in records} == set(_RECORD_FIELDS)
    for record in records:
        name = type(record).__name__
        assert tuple(item.name for item in fields(type(record))) == _RECORD_FIELDS[name]
        assert record.record_sha256 == _independent_record_sha256(record)


def test_cp70_contracts_freeze_only_the_bounded_closed_development_boundary() -> None:
    bundle = _bundle()
    reducer = bundle.reducer_contract
    assert (
        reducer.seed_count,
        reducer.row_count,
        reducer.request_count,
        reducer.estimand_count,
        reducer.output_sufficient_statistic_map_sizes,
        reducer.diagnostic_status_count_map_size,
        reducer.aggregation_update_count,
        reducer.cp_endpoint_table_count,
        reducer.cp_adjacent_boundary_comparison_count,
    ) == (2_048, 16, 32_768, 554, (72, 170, 16, 312), 6, 362_928, 16, 60)
    assert reducer.private_stream_injection_only is True
    assert reducer.public_stream_api_exposed is False
    assert reducer.source_independent is True
    assert reducer.stdlib_only is True
    assert reducer.project_modules_imported is False
    assert reducer.direct_to_fixed_sufficient_statistics is True
    assert reducer.cp68_projection_records_created is False
    assert reducer.interchange_corpus_retained is False
    validator = bundle.output_validation_contract
    assert validator.exact_root_keys == _OUTPUT_ROOT_FIELDS
    assert validator.exact_estimand_keys == _OUTPUT_RECORD_FIELDS
    assert validator.closed_fixture_only is True
    assert validator.exact_input_bytes is True
    assert validator.raise_or_sealed_return is True
    assert validator.partial_result_permitted is False
    assert (
        validator.estimand_count,
        validator.observable_estimand_count,
        validator.rejection_first_attempt_estimand_count,
        validator.feature_estimand_count,
        validator.binomial_estimand_count,
        validator.computed_interval_count,
        validator.insufficient_selection_count,
    ) == (554, 72, 170, 312, 242, 398, 156)
    assert (
        validator.maximum_output_bytes,
        validator.maximum_canonical_depth,
        validator.maximum_canonical_nodes,
        validator.maximum_key_characters,
        validator.maximum_text_characters,
        validator.maximum_integer_decimal_digits,
        validator.maximum_integer_bits,
    ) == (1_048_576, 8, 32_768, 64, 256, 155, 512)


def test_cp70_independent_output_is_exact_and_public_validator_accepts_it() -> None:
    payload, body, records = _independent_output()
    assert tuple(body) == _OUTPUT_ROOT_FIELDS
    assert len(records) == 554
    assert Counter(record["estimand_family"] for record in records) == {
        "observable-cell": 72,
        "rejection-first-attempt": 170,
        "selected-conditional-feature": 312,
    }
    assert sum(record["interval_state"] == "computed" for record in records) == 398
    assert (
        sum(record["interval_state"] == "insufficient-selection" for record in records)
        == 156
    )
    assert _graph_statistics(json.loads(payload.decode("ascii"))) == (
        20_800,
        5,
        27,
        115,
    )
    validation = cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(payload)
    assert type(validation) is cp70.CP70EstimateIntervalOutputValidationV1
    assert validation.source_output_schema_version == _CP68_SCHEMA
    assert validation.fixture_set_sha256 == _EXPECTED_CP68_FIXTURE_SHA256
    assert validation.request_count == 32_768
    assert validation.estimand_count == 554
    assert (
        validation.observable_estimand_count,
        validation.rejection_first_attempt_estimand_count,
        validation.feature_estimand_count,
        validation.binomial_interval_count,
        validation.feature_interval_count,
        validation.insufficient_selection_count,
        validation.computed_interval_count,
    ) == (72, 170, 312, 242, 156, 156, 398)
    assert validation.selected_counts_by_row == _SELECTED_COUNTS
    assert validation.ordered_estimand_record_sha256s_sha256 == (
        _EXPECTED_ORDERED_RECORD_SHA256
    )
    assert validation.output_body_sha256 == _EXPECTED_OUTPUT_BODY_SHA256
    assert validation.output_canonical_json_bytes == _EXPECTED_OUTPUT_BYTES
    assert validation.output_canonical_json_sha256 == _EXPECTED_OUTPUT_SHA256
    for name in (
        "canonical_bytes_verified",
        "record_digests_verified",
        "estimand_inventory_verified",
        "family_union_verified",
        "cross_record_invariants_verified",
        "exact_arithmetic_verified",
        "cp_endpoint_table_match_verified",
        "feature_threshold_and_clipping_verified",
        "closed_fixture_match",
        "development_fixture_only",
    ):
        assert getattr(validation, name) is True, name
    assert validation.production_evidence is False
    assert validation.decision_path_qualified is False


@pytest.mark.parametrize(
    "payload",
    (
        None,
        True,
        False,
        "{}",
        bytearray(b"{}"),
        memoryview(b"{}"),
        _BytesSubclass(b"{}"),
    ),
)
def test_cp70_public_validator_rejects_nonexact_bytes_without_protocol_coercion(
    payload: object,
) -> None:
    assert _validation_error_code(payload) == "CP70_INPUT_TYPE_MISMATCH"


def test_cp70_public_validator_does_not_touch_alien_protocols() -> None:
    assert _validation_error_code(_ProtocolBomb()) == "CP70_INPUT_TYPE_MISMATCH"


@pytest.mark.parametrize(
    ("payload", "expected"),
    (
        (b"", "CP70_INPUT_BYTE_LIMIT"),
        (b"x" * 1_048_577, "CP70_INPUT_BYTE_LIMIT"),
        (b"\xef\xbb\xbf{}", "CP70_INPUT_ENCODING_INVALID"),
        (b'{"x":"\xff"}', "CP70_INPUT_ENCODING_INVALID"),
        (b"{", "CP70_INPUT_JSON_INVALID"),
        (b'{"x":1,"x":1}', "CP70_INPUT_JSON_INVALID"),
        (b'{"x":1.0}', "CP70_INPUT_JSON_INVALID"),
        (b'{"x":1e0}', "CP70_INPUT_JSON_INVALID"),
        (b'{"x":NaN}', "CP70_INPUT_JSON_INVALID"),
        (b'{"x":Infinity}', "CP70_INPUT_JSON_INVALID"),
        (b"[" * 9 + b"0" + b"]" * 9, "CP70_INPUT_RESOURCE_LIMIT"),
        (b"[" * 100 + b"0" + b"]" * 100, "CP70_INPUT_RESOURCE_LIMIT"),
        (b"[" * 1_000 + b"0" + b"]" * 1_000, "CP70_INPUT_RESOURCE_LIMIT"),
        (b"[" * 10_000 + b"0" + b"]" * 10_000, "CP70_INPUT_RESOURCE_LIMIT"),
        (
            ('{"' + "k" * 65 + '":0}').encode("ascii"),
            "CP70_INPUT_RESOURCE_LIMIT",
        ),
        (
            ('{"x":"' + "a" * 257 + '"}').encode("ascii"),
            "CP70_INPUT_RESOURCE_LIMIT",
        ),
        (
            ('{"x":' + "9" * 156 + "}").encode("ascii"),
            "CP70_INPUT_RESOURCE_LIMIT",
        ),
    ),
    ids=(
        "empty",
        "byte-cap",
        "bom",
        "non-ascii",
        "truncated",
        "duplicate-key",
        "decimal-float",
        "exponent-float",
        "nan",
        "infinity",
        "depth-9",
        "depth-100",
        "depth-1000",
        "depth-10000",
        "key-cap",
        "text-cap",
        "integer-digit-cap",
    ),
)
def test_cp70_public_validator_rejects_lexical_and_resource_hostiles(
    payload: bytes, expected: str
) -> None:
    assert _validation_error_code(payload) == expected


def test_cp70_depth_precheck_ignores_containers_and_escaped_quotes_in_strings() -> None:
    payload = json.dumps(
        {"x": '"' + "[{" * 60 + "}]" * 60 + '"'},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    assert b'\\"' in payload
    assert _validation_error_code(payload) == "CP70_INPUT_FIELD_SET_MISMATCH"


def test_cp70_depth_and_node_caps_have_exact_resource_boundaries() -> None:
    module = _fresh_cp70_module("depth_and_nodes")
    error = module.CP70EstimateIntervalOutputValidationQualificationError
    depth_8 = b"[" * 8 + b"0" + b"]" * 8
    depth_9 = b"[" * 9 + b"0" + b"]" * 9
    module._precheck_json_nesting(depth_8)
    module._walk_decoded(json.loads(depth_8.decode("ascii")))
    with pytest.raises(error) as caught:
        module.cp70_validate_closed_cp68_estimate_interval_output_bytes(depth_8)
    assert caught.value.code == "CP70_INPUT_FIELD_TYPE_MISMATCH"
    with pytest.raises(error) as caught:
        module._precheck_json_nesting(depth_9)
    assert caught.value.code == "CP70_INPUT_RESOURCE_LIMIT"

    nodes_32_768 = b'{"x":[' + b"0," * 32_765 + b"0]}"
    nodes_32_769 = b'{"x":[' + b"0," * 32_766 + b"0]}"
    assert len(json.loads(nodes_32_768.decode("ascii"))["x"]) == 32_766
    with pytest.raises(error) as caught:
        module.cp70_validate_closed_cp68_estimate_interval_output_bytes(nodes_32_768)
    assert caught.value.code == "CP70_INPUT_FIELD_SET_MISMATCH"
    with pytest.raises(error) as caught:
        module.cp70_validate_closed_cp68_estimate_interval_output_bytes(nodes_32_769)
    assert caught.value.code == "CP70_INPUT_RESOURCE_LIMIT"
    assert module._CLOSED_OUTPUT_CACHE is None
    assert module._BUNDLE_CACHE is None
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 0


def test_cp70_deep_nesting_rejection_is_bounded_and_cache_neutral() -> None:
    module = _fresh_cp70_module("deep_nesting_resources")
    error = module.CP70EstimateIntervalOutputValidationQualificationError
    payloads = tuple(
        b"[" * depth + b"0" + b"]" * depth for depth in (9, 100, 1_000, 10_000)
    )
    tracemalloc.start()
    started = time.perf_counter()
    try:
        for payload in payloads:
            with pytest.raises(error) as caught:
                module.cp70_validate_closed_cp68_estimate_interval_output_bytes(payload)
            assert caught.value.code == "CP70_INPUT_RESOURCE_LIMIT"
        elapsed = time.perf_counter() - started
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert elapsed < 5.0
    assert peak < 8 * 1_048_576
    assert module._CLOSED_OUTPUT_CACHE is None
    assert module._BUNDLE_CACHE is None
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 0


def test_cp70_public_validator_rejects_noncanonical_equivalent_bytes() -> None:
    payload, body, _records = _independent_output()
    assert _validation_error_code(payload + b" ") == "CP70_INPUT_CANONICAL_MISMATCH"
    canonical_body = _canonical(body)
    assert type(canonical_body) is dict
    reverse = json.dumps(
        {key: canonical_body[key] for key in reversed(tuple(canonical_body))},
        sort_keys=False,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    assert json.loads(reverse) == json.loads(payload)
    assert _validation_error_code(reverse) == "CP70_INPUT_CANONICAL_MISMATCH"
    escaped = payload.replace(b'"schema_version"', b'"\\u0073chema_version"', 1)
    assert json.loads(escaped) == json.loads(payload)
    assert _validation_error_code(escaped) == "CP70_INPUT_CANONICAL_MISMATCH"


def test_cp70_public_validator_rejects_root_field_set_type_schema_and_fixture() -> None:
    def missing(value: dict) -> None:
        del value["request_count"]

    def extra(value: dict) -> None:
        value["alien"] = None

    for mutator in (missing, extra):
        assert _validation_error_code(_raw_payload_mutator(mutator)) == (
            "CP70_INPUT_FIELD_SET_MISMATCH"
        )
    cases = (
        ("request_count", True, "CP70_INPUT_FIELD_TYPE_MISMATCH"),
        ("estimand_count", "554", "CP70_INPUT_FIELD_TYPE_MISMATCH"),
        ("estimand_estimate_intervals", {}, "CP70_INPUT_INVENTORY_MISMATCH"),
        ("schema_version", "cp70-alien", "CP70_INPUT_SCHEMA_MISMATCH"),
        ("fixture_set_sha256", "0" * 64, "CP70_INPUT_SCHEMA_MISMATCH"),
    )
    for name, replacement, expected in cases:
        assert (
            _validation_error_code(
                _raw_payload_mutator(
                    lambda value, n=name, r=replacement: value.__setitem__(n, r)
                )
            )
            == expected
        )


def test_cp70_public_validator_rejects_553_555_reordered_and_replayed_records() -> None:
    def short(value: dict) -> None:
        value["estimand_estimate_intervals"].pop()

    def long(value: dict) -> None:
        value["estimand_estimate_intervals"].append(
            dict(value["estimand_estimate_intervals"][-1])
        )

    def reverse(value: dict) -> None:
        value["estimand_estimate_intervals"].reverse()

    def replay(value: dict) -> None:
        value["estimand_estimate_intervals"][1] = dict(
            value["estimand_estimate_intervals"][0]
        )

    for mutator in (short, long, reverse, replay):
        assert _validation_error_code(_raw_payload_mutator(mutator)) == (
            "CP70_INPUT_INVENTORY_MISMATCH"
        )


def test_cp70_public_validator_rejects_every_estimand_record_field_boundary() -> None:
    def remove(value: dict) -> None:
        del value["estimand_estimate_intervals"][0]["estimate"]

    def add(value: dict) -> None:
        value["estimand_estimate_intervals"][0]["decision"] = False

    for mutator in (remove, add):
        assert _validation_error_code(_raw_payload_mutator(mutator)) == (
            "CP70_INPUT_FIELD_SET_MISMATCH"
        )

    cases = (
        ("estimand_ordinal", True, "CP70_INPUT_INVENTORY_MISMATCH"),
        ("row_ordinal", _IntSubclass(1), "CP70_INPUT_FIELD_TYPE_MISMATCH"),
        ("estimand_id", 1, "CP70_INPUT_DIGEST_MISMATCH"),
        ("record_sha256", None, "CP70_INPUT_DIGEST_MISMATCH"),
        ("development_fixture_only", 1, "CP70_INPUT_DIGEST_MISMATCH"),
    )
    # JSON erases an int subclass to an exact int, so exercise all JSON-visible
    # type confusions and leave subclass rejection to the in-memory serializer.
    for name, replacement, expected in cases:
        if type(replacement) is _IntSubclass:
            continue

        def mutate(value: dict, n: str = name, r: object = replacement) -> None:
            value["estimand_estimate_intervals"][0][n] = r

        assert _validation_error_code(_raw_payload_mutator(mutate)) == expected


@pytest.mark.parametrize(
    "tag",
    (
        {"$fraction": ["00", "1"]},
        {"$fraction": ["+1", "2"]},
        {"$fraction": ["-0", "1"]},
        {"$fraction": ["1", "0"]},
        {"$fraction": ["1", "-2"]},
        {"$fraction": ["2", "2"]},
        {"$fraction": ["1"]},
        {"$fraction": [1, "2"]},
        {"alien": ["1", "2"]},
    ),
)
def test_cp70_public_validator_rejects_noncanonical_fraction_grammar(
    tag: object,
) -> None:
    def mutate(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["estimate"] = tag
        _retag_raw_record(record)

    assert _validation_error_code(_raw_payload_mutator(mutate)) == (
        "CP70_INPUT_FRACTION_MISMATCH"
    )


def test_cp70_public_validator_rejects_oversized_fraction_before_bigint_conversion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutate(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["estimate"] = {"$fraction": ["9" * 156, "1"]}
        _retag_raw_record(record)

    assert _validation_error_code(_raw_payload_mutator(mutate)) == (
        "CP70_INPUT_RESOURCE_LIMIT"
    )

    def forbidden_bigint(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("156-digit fraction reached bigint conversion")

    monkeypatch.setattr(cp70, "int", forbidden_bigint, raising=False)
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70._fraction_from_tag({"$fraction": ["9" * 156, "1"]})
    assert caught.value.code == "CP70_INPUT_RESOURCE_LIMIT"


def test_cp70_public_validator_applies_fraction_bit_cap_after_bounded_conversion() -> None:
    def mutate(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["estimate"] = {"$fraction": ["9" * 155, "1"]}
        _retag_raw_record(record)

    assert _validation_error_code(_raw_payload_mutator(mutate)) == (
        "CP70_INPUT_RESOURCE_LIMIT"
    )


def test_cp70_public_validator_recomputes_record_digests_before_acceptance() -> None:
    def body_tamper(value: dict) -> None:
        value["estimand_estimate_intervals"][0]["success_count"] = 2_047

    assert _validation_error_code(_raw_payload_mutator(body_tamper)) == (
        "CP70_INPUT_DIGEST_MISMATCH"
    )

    def digest_shape(value: dict) -> None:
        value["estimand_estimate_intervals"][0]["record_sha256"] = "A" * 64

    assert _validation_error_code(_raw_payload_mutator(digest_shape)) == (
        "CP70_INPUT_DIGEST_MISMATCH"
    )


def test_cp70_public_validator_rejects_inventory_family_arithmetic_and_interval_tamper() -> None:
    cases = []

    def inventory(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["cp61_estimand_record_sha256"] = "0" * 64
        _retag_raw_record(record)

    cases.append((inventory, "CP70_INPUT_FIXTURE_MISMATCH"))

    def family(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["estimand_family"] = "selected-conditional-feature"
        _retag_raw_record(record)

    cases.append((family, "CP70_INPUT_FAMILY_MISMATCH"))

    def arithmetic(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["success_count"] -= 1
        record["estimate"] = {"$fraction": [str(record["success_count"]), "2048"]}
        _retag_raw_record(record)

    cases.append((arithmetic, "CP70_INPUT_FIXTURE_MISMATCH"))

    def interval(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        numerator, denominator = record["interval_upper"]["$fraction"]
        record["interval_upper"] = {"$fraction": [str(int(numerator) - 1), denominator]}
        _retag_raw_record(record)

    cases.append((interval, "CP70_INPUT_FIXTURE_MISMATCH"))

    for mutator, expected in cases:
        assert _validation_error_code(_raw_payload_mutator(mutator)) == expected


def test_cp70_feature_null_threshold_and_clipping_semantics_fail_closed() -> None:
    _payload, _body, records = _independent_output()
    features = records[_BINOMIAL_COUNT:]
    row_1040 = next(record for record in features if record["row_ordinal"] == 2)
    row_1039 = next(record for record in features if record["row_ordinal"] == 3)
    row_zero = next(record for record in features if record["row_ordinal"] == 4)
    assert row_1040["interval_state"] == "computed"
    assert row_1039["interval_state"] == "insufficient-selection"
    assert row_1039["estimate"] is not None
    assert row_zero["exact_feature_sum"] is None
    assert row_zero["estimate"] is None
    assert row_zero["interval_lower"] is None
    assert row_zero["interval_upper"] is None
    assert any(
        record["interval_lower"] == record["feature_lower_bound"]
        for record in features
        if record["interval_state"] == "computed"
    )
    assert any(
        record["interval_upper"] == record["feature_upper_bound"]
        for record in features
        if record["interval_state"] == "computed"
    )

    def zero_tamper(value: dict) -> None:
        record = next(
            item
            for item in value["estimand_estimate_intervals"][_BINOMIAL_COUNT:]
            if item["row_ordinal"] == 4
        )
        record["estimate"] = {"$fraction": ["0", "1"]}
        _retag_raw_record(record)

    assert _validation_error_code(_raw_payload_mutator(zero_tamper)) == (
        "CP70_INPUT_FIXTURE_MISMATCH"
    )

    def threshold_tamper(value: dict) -> None:
        record = next(
            item
            for item in value["estimand_estimate_intervals"][_BINOMIAL_COUNT:]
            if item["row_ordinal"] == 3
        )
        record["interval_state"] = "computed"
        record["interval_lower"] = record["feature_lower_bound"]
        record["interval_upper"] = record["feature_upper_bound"]
        _retag_raw_record(record)

    assert _validation_error_code(_raw_payload_mutator(threshold_tamper)) == (
        "CP70_INPUT_INTERVAL_MISMATCH"
    )


def test_cp70_cold_validator_rejections_do_not_initialize_or_partially_issue() -> None:
    def oversized_fraction(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["estimate"] = {"$fraction": ["9" * 156, "1"]}
        _retag_raw_record(record)

    def semantic_tamper(value: dict) -> None:
        record = value["estimand_estimate_intervals"][0]
        record["cp61_estimand_record_sha256"] = _ZERO_SHA256
        _retag_raw_record(record)

    def digest_tamper(value: dict) -> None:
        value["estimand_estimate_intervals"][0]["success_count"] -= 1

    hostile_payloads = (
        (_raw_payload_mutator(oversized_fraction), "CP70_INPUT_RESOURCE_LIMIT"),
        (_raw_payload_mutator(semantic_tamper), "CP70_INPUT_FIXTURE_MISMATCH"),
        (_raw_payload_mutator(digest_tamper), "CP70_INPUT_DIGEST_MISMATCH"),
    )
    module = _fresh_cp70_module("cold_validator_cache")
    error = module.CP70EstimateIntervalOutputValidationQualificationError
    for payload, expected in hostile_payloads:
        with pytest.raises(error) as caught:
            module.cp70_validate_closed_cp68_estimate_interval_output_bytes(payload)
        assert caught.value.code == expected
        assert module._CLOSED_OUTPUT_CACHE is None
        assert module._BUNDLE_CACHE is None
        assert len(module._ISSUED_RECORD_SNAPSHOTS) == 0
        assert module._certify_cp_endpoint_table.cache_info().currsize == 0

    canonical_payload = _independent_output()[0]
    caller_payload = bytes(bytearray(canonical_payload))
    assert caller_payload == canonical_payload
    assert caller_payload is not canonical_payload
    validation = module.cp70_validate_closed_cp68_estimate_interval_output_bytes(
        caller_payload
    )
    assert validation.closed_fixture_match is True
    assert validation.cp_endpoint_table_match_verified is True
    assert module._certify_cp_endpoint_table.cache_info().currsize == 0
    cached_payload, summary = module._CLOSED_OUTPUT_CACHE
    assert cached_payload == canonical_payload
    assert cached_payload is not caller_payload
    assert tuple(summary) == (
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
    )
    assert summary == {
        "ordered_estimand_record_sha256s_sha256": _EXPECTED_ORDERED_RECORD_SHA256,
        "output_body_sha256": _EXPECTED_OUTPUT_BODY_SHA256,
        "output_canonical_json_bytes": _EXPECTED_OUTPUT_BYTES,
        "output_canonical_json_sha256": _EXPECTED_OUTPUT_SHA256,
    }
    assert _bundle().closed_module_owned_fixture_only is True
    validation_reference = weakref.ref(validation)
    del validation
    gc.collect()
    assert validation_reference() is None
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 0
    findings = _retained_cp70_graph_findings(
        {"_CLOSED_OUTPUT_CACHE": module._CLOSED_OUTPUT_CACHE}
    )
    assert findings == {
        "output_record_dicts": [],
        "output_record_vectors": [],
        "interchange_record_dicts": [],
        "interchange_corpora": [],
        "interchange_payloads": [],
        "projection_digest_preimages": [],
        "exact_output_payloads": ["_CLOSED_OUTPUT_CACHE[0]"],
    }


def test_cp70_independent_cp_table_has_exact_adjacent_boundary_witnesses() -> None:
    success_counts = (
        0,
        32,
        64,
        65,
        252,
        253,
        259,
        260,
        336,
        337,
        512,
        682,
        683,
        1_039,
        1_040,
        2_048,
    )
    endpoints = {count: _cp_interval(count) for count in success_counts}
    assert len(endpoints) == 16
    assert endpoints[0][0] == 0
    assert endpoints[_N][1] == 1
    assert endpoints[0][1] == 1 - endpoints[_N][0]
    for count in success_counts:
        lower, upper = endpoints[count]
        assert 0 <= lower <= Fraction(count, _N) <= upper <= 1
        assert lower.denominator <= _CP_DENOMINATOR
        assert upper.denominator <= _CP_DENOMINATOR
        if count:
            numerator = int(lower * _CP_DENOMINATOR)
            assert _upper_tail_compare(count, numerator) < 0
            assert _upper_tail_compare(count, numerator + 1) >= 0
        if count < _N:
            mirrored = _N - count
            upper_numerator = int(upper * _CP_DENOMINATOR)
            lower_mirror = _CP_DENOMINATOR - upper_numerator
            assert _upper_tail_compare(mirrored, lower_mirror) < 0
            assert _upper_tail_compare(mirrored, lower_mirror + 1) >= 0


def test_cp70_private_reducer_accepts_independently_generated_full_stream() -> None:
    metrics = cp70._reduce_closed_compact_interchange_stream_details(
        _independent_interchange_stream()
    )
    output, details = cp70._build_estimate_interval_output_bytes(metrics)
    expected, _body, _records = _independent_output()
    assert output == expected
    assert tuple(details) == (
        "records",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
    )
    transient_records = details.pop("records")
    assert type(transient_records) is tuple
    assert len(transient_records) == 554
    assert all(type(record) is dict for record in transient_records)
    assert all(tuple(record) == _OUTPUT_RECORD_FIELDS for record in transient_records)
    del transient_records
    assert tuple(details) == (
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
    )
    assert details["ordered_estimand_record_sha256s_sha256"] == (
        _EXPECTED_ORDERED_RECORD_SHA256
    )
    assert details["output_body_sha256"] == _EXPECTED_OUTPUT_BODY_SHA256
    assert details["output_canonical_json_bytes"] == _EXPECTED_OUTPUT_BYTES
    assert details["output_canonical_json_sha256"] == _EXPECTED_OUTPUT_SHA256
    expected_scalars = {
        "request_count": 32_768,
        "total_input_bytes": 51_506_557,
        "first_interchange_record_sha256": _EXPECTED_CP69_FIRST_INPUT_SHA256,
        "ordered_interchange_record_sha256": _EXPECTED_CP69_ORDERED_INPUT_SHA256,
        "selected_counts_by_row": _SELECTED_COUNTS,
        "first_attempt_contribution_count": 8_254,
        "feature_contribution_count": 321_906,
        "aggregation_update_count": 362_928,
        "ordered_target_projection_sha256": (_EXPECTED_CP68_ORDERED_PROJECTION_SHA256),
    }
    for name, expected_value in expected_scalars.items():
        assert metrics[name] == expected_value, name
    assert (
        len(metrics["observable_counts"]),
        len(metrics["first_attempt_counts"]),
        len(metrics["selected_counts_by_row"]),
        len(metrics["feature_sums"]),
        len(metrics["status_counts"]),
    ) == (72, 170, 16, 312, 6)
    assert metrics["status_counts"] == {
        "rejection-selected": 8_254,
        "rejection-exhausted": 2_034,
        "sir-selected": 8_254,
        "refusal": 4_744,
        "failure": 4_742,
        "timeout": 4_740,
    }


def test_cp70_independent_first_and_ordered_input_digests_match_cp69_pins() -> None:
    ordered = hashlib.sha256(b"cp69-test28-ordered-interchange-record-digests-v1\0")
    total = 0
    first = None
    for ordinal, payload in enumerate(_independent_interchange_stream(), 1):
        raw = _decode_exact(payload)
        assert tuple(raw) == tuple(sorted(_INTERCHANGE_FIELDS))
        assert payload == _canonical_json_bytes(raw)
        if first is None:
            first = raw["record_sha256"]
        ordered.update(bytes.fromhex(raw["record_sha256"]))
        total += len(payload)
        if ordinal in (1, 16, 17, 32_768):
            assert raw["logical_request_ordinal"] == ordinal
    assert ordinal == 32_768
    assert first == _EXPECTED_CP69_FIRST_INPUT_SHA256
    assert ordered.hexdigest() == _EXPECTED_CP69_ORDERED_INPUT_SHA256
    assert total == 51_506_557


def test_cp70_private_reducer_fails_closed_on_iterable_and_count_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = cp70.CP70EstimateIntervalOutputValidationQualificationError
    with pytest.raises(error) as caught:
        cp70._reduce_closed_compact_interchange_stream_details(_IterableBomb())
    assert caught.value.code == "CP70_STREAM_ITERABLE_INVALID"
    with pytest.raises(error) as caught:
        cp70._reduce_closed_compact_interchange_stream_details(())
    assert caught.value.code == "CP70_STREAM_COUNT_MISMATCH"

    first = _interchange_payload(1, 1)
    monkeypatch.setattr(cp70, "CP70_TEST28_REQUEST_COUNT", 1)
    with pytest.raises(error) as caught:
        cp70._reduce_closed_compact_interchange_stream_details((first, None))
    assert caught.value.code == "CP70_STREAM_COUNT_MISMATCH"

    class Infinite:
        def __init__(self) -> None:
            self.calls = 0

        def __iter__(self) -> object:
            return self

        def __next__(self) -> bytes:
            self.calls += 1
            if self.calls > 2:
                raise AssertionError("the reducer read beyond its one-item tail check")
            return first

    infinite = Infinite()
    with pytest.raises(error) as caught:
        cp70._reduce_closed_compact_interchange_stream_details(infinite)
    assert caught.value.code == "CP70_STREAM_COUNT_MISMATCH"
    assert infinite.calls == 2


def test_cp70_private_reducer_distinguishes_iteration_and_resource_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = cp70.CP70EstimateIntervalOutputValidationQualificationError
    first = _interchange_payload(1, 1)
    monkeypatch.setattr(cp70, "CP70_TEST28_REQUEST_COUNT", 1)
    for boundary in ("item", "terminal"):
        source = _BoundaryFailureSource(boundary, RuntimeError("ordinary"), first)
        with pytest.raises(error) as caught:
            cp70._reduce_closed_compact_interchange_stream_details(source)
        assert caught.value.code == "CP70_STREAM_ITERATION_FAILED"
    monkeypatch.setattr(cp70, "CP70_TEST28_MAXIMUM_STREAM_BYTES", len(first) - 1)
    with pytest.raises(error) as caught:
        cp70._reduce_closed_compact_interchange_stream_details((first,))
    assert caught.value.code == "CP70_STREAM_RESOURCE_LIMIT"


@pytest.mark.parametrize("boundary", ("iter", "item", "terminal"))
def test_cp70_public_runner_normalizes_memoryerror_at_every_stream_boundary(
    monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    first = _interchange_payload(1, 1)
    source = _BoundaryFailureSource(boundary, MemoryError("resource"), first)
    monkeypatch.setattr(cp70, "CP70_TEST28_REQUEST_COUNT", 1)
    monkeypatch.setattr(cp70, "_iter_closed_compact_interchange_bytes", lambda: source)
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70.cp70_run_estimate_interval_output_validation_qualification()
    assert caught.value.code == "CP70_RESOURCE_EXHAUSTED"
    assert type(caught.value.__cause__) is MemoryError


def test_cp70_public_validator_normalizes_internal_memoryerror_without_partial_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _independent_output()[0]

    def exhausted(*_args: object, **_kwargs: object) -> object:
        raise MemoryError("resource")

    monkeypatch.setattr(cp70, "_decode_canonical_bytes", exhausted)
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(payload)
    assert caught.value.code == "CP70_RESOURCE_EXHAUSTED"
    assert type(caught.value.__cause__) is MemoryError


def test_cp70_closed_runner_matches_every_frozen_reduction_expectation() -> None:
    qualification = _qualification()
    expected = _bundle().full_reduction_expectation
    assert qualification.source_fixture_set_sha256 == expected.source_fixture_set_sha256
    for name in (
        "request_count",
        "total_input_bytes",
        "aggregation_update_count",
        "estimand_count",
        "ordered_interchange_record_sha256",
        "ordered_target_projection_sha256",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
    ):
        assert getattr(qualification, name) == getattr(expected, name), name
    assert qualification.logical_ordinals_complete is True
    assert qualification.streaming_peak_input_payload_count == 1
    assert qualification.streaming_peak_parsed_observation_count == 1
    assert qualification.interchange_corpus_retained is False
    assert qualification.cp68_projection_records_created is False
    assert qualification.output_record_vector_cardinality == 554
    assert qualification.output_records_retained_after_runner is False
    for name in (
        "canonical_output_validated",
        "record_digests_verified",
        "cp_endpoint_table_independently_certified",
        "feature_threshold_and_clipping_verified",
        "target_output_matches_cp68_expectation",
        "all_development_qualification_checks_passed",
    ):
        assert getattr(qualification, name) is True, name


def test_cp70_cold_runner_never_overlaps_or_retains_output_record_vectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _fresh_cp70_module("cold_runner_retention")
    assert module._CLOSED_OUTPUT_CACHE is None
    assert module._BUNDLE_CACHE is None
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 0
    original_builder = module._build_estimate_interval_output_bytes
    original_decoder = module._decode_canonical_bytes
    original_parser = module._parse_closed_interchange
    original_plain_json = module._plain_json_bytes
    built_vector_ids = []
    events = []
    projection_preimage_count = 0
    interchange_decode_count = 0
    interchange_parse_count = 0
    last_interchange_decoded_identity = None

    def live_gc_identities() -> set[int]:
        return {id(value) for value in gc.get_objects()}

    def observed_builder(metrics: object) -> tuple[bytes, dict]:
        assert not set(built_vector_ids) & live_gc_identities()
        events.append("build-%d" % (len(built_vector_ids) + 1))
        payload, details = original_builder(metrics)
        records = details["records"]
        assert type(records) is tuple and len(records) == _ESTIMAND_COUNT
        assert gc.is_tracked(records)
        assert id(records) in live_gc_identities()
        built_vector_ids.append(id(records))
        return payload, details

    def observed_plain_json(value: object, maximum: int = 1_048_576) -> bytes:
        nonlocal projection_preimage_count
        if type(value) is dict and set(value) == set(
            _PROJECTION_DIGEST_PREIMAGE_FIELDS
        ):
            projection_preimage_count += 1
            if projection_preimage_count == 1:
                events.append("projection-first")
            elif projection_preimage_count == _REQUEST_COUNT:
                events.append("projection-last")
            assert value["schema_version"] == _CP68_SCHEMA
        return original_plain_json(value, maximum)

    def observed_decoder(*args: object, **kwargs: object) -> dict:
        nonlocal interchange_decode_count, last_interchange_decoded_identity
        maximum = (
            args[1]
            if len(args) > 1
            else kwargs.get("maximum", module.CP70_TEST28_MAXIMUM_OUTPUT_BYTES)
        )
        output_payload = maximum == module.CP70_TEST28_MAXIMUM_OUTPUT_BYTES
        if output_payload:
            assert not set(built_vector_ids) & live_gc_identities()
            events.append("decode")
        value = original_decoder(*args, **kwargs)
        if output_payload:
            records = value["estimand_estimate_intervals"]
            assert type(records) is list and len(records) == _ESTIMAND_COUNT
        else:
            assert maximum == module.CP70_TEST28_MAXIMUM_INTERCHANGE_BYTES
            assert set(value) == set(_INTERCHANGE_FIELDS)
            interchange_decode_count += 1
            last_interchange_decoded_identity = id(value)
        return value

    def observed_parser(payload: object, logical_ordinal: int) -> dict:
        nonlocal interchange_parse_count, last_interchange_decoded_identity
        result = original_parser(payload, logical_ordinal)
        assert last_interchange_decoded_identity is not None
        assert id(result) == last_interchange_decoded_identity
        interchange_parse_count += 1
        last_interchange_decoded_identity = None
        return result

    monkeypatch.setattr(
        module, "_build_estimate_interval_output_bytes", observed_builder
    )
    monkeypatch.setattr(module, "_plain_json_bytes", observed_plain_json)
    monkeypatch.setattr(module, "_decode_canonical_bytes", observed_decoder)
    monkeypatch.setattr(module, "_parse_closed_interchange", observed_parser)
    qualification = module.cp70_run_estimate_interval_output_validation_qualification()
    assert qualification.output_record_vector_cardinality == _ESTIMAND_COUNT
    assert qualification.output_records_retained_after_runner is False
    assert qualification.cp68_projection_records_created is False
    assert qualification.streaming_peak_parsed_observation_count == 1
    assert qualification.cp_endpoint_table_independently_certified is True
    assert not hasattr(
        qualification, "maximum_simultaneously_materialized_output_record_count"
    )
    assert len(built_vector_ids) == 2
    assert interchange_decode_count == _REQUEST_COUNT
    assert interchange_parse_count == _REQUEST_COUNT
    assert last_interchange_decoded_identity is None
    assert projection_preimage_count == _REQUEST_COUNT
    assert events == (
        [
            "build-1",
            "projection-first",
            "projection-last",
            "build-2",
            "decode",
        ]
    )
    qualification_reference = weakref.ref(qualification)
    del qualification
    gc.collect()
    assert qualification_reference() is None
    assert not set(built_vector_ids) & live_gc_identities()

    cache_globals = {
        name: value
        for name, value in vars(module).items()
        if name.endswith("_CACHE") or name.endswith("_SNAPSHOTS")
    }
    assert set(cache_globals) == {
        "_CLOSED_OUTPUT_CACHE",
        "_BUNDLE_CACHE",
        "_ISSUED_RECORD_SNAPSHOTS",
    }
    cached_payload, scalar_summary = module._CLOSED_OUTPUT_CACHE
    assert _sha256(cached_payload) == _EXPECTED_OUTPUT_SHA256
    assert tuple(scalar_summary) == (
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
    )
    bundle = module.cp70_estimate_interval_output_validation_qualification_bundle()
    assert bundle is module._BUNDLE_CACHE
    assert bundle.closed_module_owned_fixture_only is True
    assert bundle.output_record_vector_cardinality == _ESTIMAND_COUNT
    assert bundle.cp68_projection_records_created is False
    assert not hasattr(
        bundle, "maximum_simultaneously_materialized_output_record_count"
    )
    issued_snapshot = dict(module._ISSUED_RECORD_SNAPSHOTS.items())
    assert {type(record).__name__ for record in issued_snapshot} == {
        "CP70PredecessorCustodyV1",
        "CP70SourceIndependentReducerContractV1",
        "CP70OutputValidationContractV1",
        "CP70FullReductionExpectationV1",
        "CP70EstimateIntervalOutputValidationQualificationBundleV1",
    }
    lru_wrappers = {
        name: value
        for name, value in vars(module).items()
        if callable(value)
        and hasattr(value, "cache_info")
        and hasattr(value, "cache_clear")
    }
    assert set(lru_wrappers) == {
        "_feature_ids",
        "_row_feature_items",
        "_certify_cp_endpoint_table",
    }
    small_cached_values = (
        tuple(module._feature_ids(fixture) for fixture in ("T28-M1-Q", "T28-M2-Q")),
        tuple(module._row_feature_items(row) for row in range(1, _ROW_COUNT + 1)),
        module._certify_cp_endpoint_table(),
    )
    assert module._feature_ids.cache_info().currsize == 2
    assert module._row_feature_items.cache_info().currsize == _ROW_COUNT
    assert module._certify_cp_endpoint_table.cache_info().currsize == 1
    roots = {
        "_CLOSED_OUTPUT_CACHE": module._CLOSED_OUTPUT_CACHE,
        "_BUNDLE_CACHE": module._BUNDLE_CACHE,
        "_ISSUED_RECORD_SNAPSHOTS": issued_snapshot,
        "lru_cached_values": small_cached_values,
    }
    findings = _retained_cp70_graph_findings(roots)
    assert findings == {
        "output_record_dicts": [],
        "output_record_vectors": [],
        "interchange_record_dicts": [],
        "interchange_corpora": [],
        "interchange_payloads": [],
        "projection_digest_preimages": [],
        "exact_output_payloads": ["_CLOSED_OUTPUT_CACHE[0]"],
    }


def test_cp70_expectation_exact_counts_and_digests_are_not_self_reported() -> None:
    expected = _bundle().full_reduction_expectation
    assert (
        expected.request_count,
        expected.total_input_bytes,
        expected.selected_counts_by_row,
        expected.rejection_selected_count,
        expected.rejection_exhausted_count,
        expected.sir_selected_count,
        expected.refusal_count,
        expected.failure_count,
        expected.timeout_count,
        expected.first_attempt_contribution_count,
        expected.feature_contribution_count,
        expected.aggregation_update_count,
    ) == (
        32_768,
        51_506_557,
        _SELECTED_COUNTS,
        8_254,
        2_034,
        8_254,
        4_744,
        4_742,
        4_740,
        8_254,
        321_906,
        362_928,
    )
    assert (
        expected.estimand_count,
        expected.observable_estimand_count,
        expected.rejection_first_attempt_estimand_count,
        expected.feature_estimand_count,
        expected.binomial_interval_count,
        expected.feature_interval_count,
        expected.insufficient_selection_count,
        expected.computed_interval_count,
        expected.distinct_binomial_success_count_count,
        expected.cp_adjacent_boundary_comparison_count,
    ) == (554, 72, 170, 312, 242, 156, 156, 398, 16, 60)
    assert expected.first_interchange_record_sha256 == (
        _EXPECTED_CP69_FIRST_INPUT_SHA256
    )
    assert expected.ordered_interchange_record_sha256 == (
        _EXPECTED_CP69_ORDERED_INPUT_SHA256
    )
    assert expected.ordered_target_projection_sha256 == (
        _EXPECTED_CP68_ORDERED_PROJECTION_SHA256
    )
    assert expected.ordered_estimand_record_sha256s_sha256 == (
        _EXPECTED_ORDERED_RECORD_SHA256
    )
    assert expected.output_body_sha256 == _EXPECTED_OUTPUT_BODY_SHA256
    assert expected.output_canonical_json_bytes == _EXPECTED_OUTPUT_BYTES
    assert expected.output_canonical_json_sha256 == _EXPECTED_OUTPUT_SHA256


def test_cp70_private_reducer_rejects_wrong_first_record_and_digest_corruption() -> None:
    error = cp70.CP70EstimateIntervalOutputValidationQualificationError
    wrong_ordinal = _interchange_payload(1, 2)
    with pytest.raises(error) as caught:
        cp70._reduce_closed_compact_interchange_stream_details((wrong_ordinal,))
    assert caught.value.code == "CP70_STREAM_CONTENT_MISMATCH"

    raw = _decode_exact(_interchange_payload(1, 1))
    raw["record_sha256"] = "0" * 64
    corrupted = _canonical_json_bytes(raw)
    with pytest.raises(error) as caught:
        cp70._reduce_closed_compact_interchange_stream_details((corrupted,))
    assert caught.value.code == "CP70_STREAM_CONTENT_MISMATCH"


def test_cp70_bundle_validator_and_runner_are_zero_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _independent_output()[0]
    calls = []

    def forbidden(*args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        raise AssertionError("forbidden external operation")

    monkeypatch.setattr(builtins, "open", forbidden)
    for owner, names in (
        (os, ("open", "stat", "lstat", "listdir", "scandir", "walk", "fork")),
        (random, ("random", "getrandbits", "randrange")),
        (secrets, ("token_bytes", "token_hex", "randbits")),
        (socket, ("socket", "create_connection")),
        (subprocess, ("run", "Popen", "call", "check_call", "check_output")),
        (time, ("time", "time_ns", "monotonic", "perf_counter", "sleep")),
    ):
        for name in names:
            if hasattr(owner, name):
                monkeypatch.setattr(owner, name, forbidden)
    assert _bundle().zero_argument_builder is True
    validation = cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(payload)
    assert validation.closed_fixture_match is True
    qualification = cp70.cp70_run_estimate_interval_output_validation_qualification()
    assert qualification.all_development_qualification_checks_passed is True
    assert calls == []


def test_cp70_source_has_no_project_numeric_io_or_dynamic_execution_imports() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {
        "heterodiff",
        "numpy",
        "scipy",
        "os",
        "pathlib",
        "subprocess",
        "socket",
        "random",
        "secrets",
        "time",
        "tempfile",
        "shutil",
        "multiprocessing",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                alias.name.split(".")[0] not in forbidden_roots for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_roots
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "exec", "eval", "compile", "__import__"}
    assert "importlib" not in source


def test_cp70_fresh_module_execution_performs_no_host_io_or_project_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _SOURCE.read_bytes()
    code = compile(source, str(_SOURCE), "exec")
    original_import = builtins.__import__

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("fresh CP70 execution attempted host I/O")

    def guarded_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name.startswith(("heterodiff", "numpy", "scipy")):
            raise AssertionError("fresh CP70 execution imported project/numeric code")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for owner, names in (
        (os, ("open", "stat", "lstat", "listdir", "scandir", "walk", "fork")),
        (random, ("random", "getrandbits", "randrange")),
        (secrets, ("token_bytes", "token_hex", "randbits")),
        (socket, ("socket", "create_connection")),
        (subprocess, ("run", "Popen", "call", "check_call", "check_output")),
        (time, ("time", "time_ns", "monotonic", "perf_counter", "sleep")),
    ):
        for name in names:
            if hasattr(owner, name):
                monkeypatch.setattr(owner, name, forbidden)
    module_name = "heterodiff.evaluation._cp70_hostile_fresh_import"
    module = types.ModuleType(module_name)
    module.__file__ = str(_SOURCE)
    module.__package__ = "heterodiff.evaluation"
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    finally:
        del sys.modules[module_name]
    assert module.CP70_TEST28_REQUEST_COUNT == 32_768


def test_cp70_records_are_sealed_nonconstructible_and_nonpickleable() -> None:
    validation = cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(
        _independent_output()[0]
    )
    bundle = _bundle()
    records = (
        bundle.predecessor_custody,
        bundle.reducer_contract,
        bundle.output_validation_contract,
        bundle.full_reduction_expectation,
        validation,
        _qualification(),
        bundle,
    )
    for record in records:
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)
        with pytest.raises((TypeError, AttributeError)):
            setattr(record, fields(type(record))[0].name, "mutated")
        with pytest.raises(TypeError):
            type("Alien", (type(record),), {})
        assert cp70.cp70_canonical_json_bytes(record) == _canonical_json_bytes(record)
        assert cp70.cp70_sha256(record) == _sha256(
            b"cp70-public-record-v1\0"
            + type(record).__name__.encode("ascii")
            + b"\0"
            + _canonical_json_bytes(record)
        )


def test_cp70_forged_and_mutated_records_fail_closed() -> None:
    validation = cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(
        _independent_output()[0]
    )
    forged = _forge(validation)
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70.cp70_canonical_json_bytes(forged)
    assert caught.value.code == "CP70_RECORD_NOT_ISSUED"
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70.cp70_sha256(forged)
    assert caught.value.code == "CP70_RECORD_NOT_ISSUED"

    fresh = cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes(
        _independent_output()[0]
    )
    object.__setattr__(fresh, "output_canonical_json_bytes", 1)
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70.cp70_canonical_json_bytes(fresh)
    assert caught.value.code == "CP70_RECORD_TAMPERED"
    with pytest.raises(
        cp70.CP70EstimateIntervalOutputValidationQualificationError
    ) as caught:
        cp70.cp70_sha256(fresh)
    assert caught.value.code == "CP70_RECORD_TAMPERED"


@pytest.mark.parametrize(
    "child_name",
    (
        "predecessor_custody",
        "reducer_contract",
        "output_validation_contract",
        "full_reduction_expectation",
    ),
)
def test_cp70_bundle_rejects_every_nested_record_identity_and_type_substitution(
    child_name: str,
) -> None:
    child_names = (
        "predecessor_custody",
        "reducer_contract",
        "output_validation_contract",
        "full_reduction_expectation",
    )
    wrong_child_name = child_names[
        (child_names.index(child_name) + 1) % len(child_names)
    ]
    for kind in ("unissued-clone", "plain-mapping", "wrong-issued-type"):
        module = _fresh_cp70_module(
            "nested_%s_%s" % (child_name, kind.replace("-", "_"))
        )
        bundle = module.cp70_estimate_interval_output_validation_qualification_bundle()
        child = getattr(bundle, child_name)
        assert len(module._ISSUED_RECORD_SNAPSHOTS) == 5
        if kind == "unissued-clone":
            replacement = _forge(child)
            assert _record_api_error_codes(module, replacement) == (
                "CP70_RECORD_NOT_ISSUED",
                "CP70_RECORD_NOT_ISSUED",
            )
        elif kind == "plain-mapping":
            replacement = {
                item.name: getattr(child, item.name) for item in fields(type(child))
            }
            assert _canonical_json_bytes(replacement) == (
                module.cp70_canonical_json_bytes(child)
            )
        else:
            replacement = getattr(bundle, wrong_child_name)
            assert module.cp70_canonical_json_bytes(replacement)
        object.__setattr__(bundle, child_name, replacement)
        assert (
            _record_api_error_codes(
                module,
                bundle,
                module.cp70_estimate_interval_output_validation_qualification_bundle,
            )
            == ("CP70_RECORD_TAMPERED",) * 4
        )
        assert module._BUNDLE_CACHE is bundle
        assert len(module._ISSUED_RECORD_SNAPSHOTS) == 5


def test_cp70_typed_seals_reject_canonical_collisions_and_hostile_values() -> None:
    canonical_payload = _independent_output()[0]

    def validation_record(label: str) -> tuple[object, object]:
        module = _fresh_cp70_module("typed_validation_%s" % label)
        record = module.cp70_validate_closed_cp68_estimate_interval_output_bytes(
            canonical_payload
        )
        assert len(module._ISSUED_RECORD_SNAPSHOTS) == 1
        return module, record

    module, validation = validation_record("tuple_list")
    object.__setattr__(
        validation,
        "selected_counts_by_row",
        list(validation.selected_counts_by_row),
    )
    assert _record_api_error_codes(module, validation) == (
        "CP70_RECORD_TAMPERED",
        "CP70_RECORD_TAMPERED",
    )
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 1

    for label, field_name, replacement in (
        ("bool_to_int", "development_fixture_only", 1),
        ("int_to_bool", "request_count", False),
        ("oversized_text", "fixture_set_sha256", "x" * 4_097),
        ("unsupported_set", "fixture_set_sha256", {"unsupported"}),
    ):
        module, validation = validation_record(label)
        object.__setattr__(validation, field_name, replacement)
        assert _record_api_error_codes(module, validation) == (
            "CP70_RECORD_TAMPERED",
            "CP70_RECORD_TAMPERED",
        )
        assert len(module._ISSUED_RECORD_SNAPSHOTS) == 1

    module, validation = validation_record("deleted_field")
    object.__delattr__(validation, "selected_counts_by_row")
    assert _record_api_error_codes(module, validation) == (
        "CP70_RECORD_TAMPERED",
        "CP70_RECORD_TAMPERED",
    )
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 1

    module = _fresh_cp70_module("typed_reducer_tuple_list")
    bundle = module.cp70_estimate_interval_output_validation_qualification_bundle()
    reducer = bundle.reducer_contract
    object.__setattr__(
        reducer,
        "output_sufficient_statistic_map_sizes",
        list(reducer.output_sufficient_statistic_map_sizes),
    )
    assert _record_api_error_codes(module, reducer) == (
        "CP70_RECORD_TAMPERED",
        "CP70_RECORD_TAMPERED",
    )
    assert (
        _record_api_error_codes(
            module,
            bundle,
            module.cp70_estimate_interval_output_validation_qualification_bundle,
        )
        == ("CP70_RECORD_TAMPERED",) * 4
    )
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 5


@pytest.mark.parametrize("shape", ("cycle", "deep"))
def test_cp70_typed_seal_cycles_and_depth_fail_bounded_without_cache_growth(
    shape: str,
) -> None:
    module = _fresh_cp70_module("typed_shape_%s" % shape)
    bundle = module.cp70_estimate_interval_output_validation_qualification_bundle()
    if shape == "cycle":
        replacement = []
        replacement.append(replacement)
    else:
        replacement = {"leaf": None}
        for _index in range(10_000):
            replacement = {"nested": replacement}
    object.__setattr__(bundle, "predecessor_custody", replacement)
    started = time.perf_counter()
    codes = _record_api_error_codes(
        module,
        bundle,
        module.cp70_estimate_interval_output_validation_qualification_bundle,
    )
    elapsed = time.perf_counter() - started
    assert codes == ("CP70_RECORD_TAMPERED",) * 4
    assert elapsed < 5.0
    assert module._BUNDLE_CACHE is bundle
    assert module._CLOSED_OUTPUT_CACHE is None
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 5


@pytest.mark.parametrize(
    "child_name",
    (
        "predecessor_custody",
        "reducer_contract",
        "output_validation_contract",
        "full_reduction_expectation",
    ),
)
def test_cp70_nested_child_identity_reuse_cannot_bypass_the_typed_seal(
    monkeypatch: pytest.MonkeyPatch,
    child_name: str,
) -> None:
    module = _fresh_cp70_module("nested_identity_reuse_%s" % child_name)
    bundle = module.cp70_estimate_interval_output_validation_qualification_bundle()
    child_names = (
        "predecessor_custody",
        "reducer_contract",
        "output_validation_contract",
        "full_reduction_expectation",
    )
    child_index = child_names.index(child_name)
    child = getattr(bundle, child_name)
    child_type = type(child)
    child_identity = id(child)
    child_reference = weakref.ref(child)
    child_canonical = module.cp70_canonical_json_bytes(child)
    child_values = {
        item.name: getattr(child, item.name)
        for item in fields(child_type)
        if item.name != "record_sha256"
    }
    issued_snapshot = module._ISSUED_RECORD_SNAPSHOTS[bundle]
    assert len(issued_snapshot) == 3
    assert len(issued_snapshot[2]) == len(child_names)
    assert all(
        issued is getattr(bundle, name)
        for issued, name in zip(issued_snapshot[2], child_names)
    )

    object.__setattr__(bundle, child_name, None)
    del child, issued_snapshot
    gc.collect()
    assert child_reference() is not None
    assert id(child_reference()) == child_identity
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 5

    replacement = module._record(child_type, child_values)
    assert type(replacement) is child_type
    assert replacement is not child_reference()
    assert id(replacement) != child_identity
    assert module.cp70_canonical_json_bytes(replacement) == child_canonical
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 6
    object.__setattr__(bundle, child_name, replacement)

    real_identity = builtins.id

    def reused_identity(value: object) -> int:
        if value is replacement:
            return child_identity
        return real_identity(value)

    monkeypatch.setattr(module, "id", reused_identity, raising=False)
    assert (
        _record_api_error_codes(
            module,
            bundle,
            module.cp70_estimate_interval_output_validation_qualification_bundle,
        )
        == ("CP70_RECORD_TAMPERED",) * 4
    )
    retained_children = module._ISSUED_RECORD_SNAPSHOTS[bundle][2]
    assert retained_children[child_index] is child_reference()
    assert retained_children[child_index] is not replacement
    assert module._BUNDLE_CACHE is bundle
    assert module._CLOSED_OUTPUT_CACHE is None
    assert len(module._ISSUED_RECORD_SNAPSHOTS) == 6


def test_cp70_typed_seal_memory_exhaustion_is_normalized_without_cache_damage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _fresh_cp70_module("typed_shape_memory")
    bundle = module.cp70_estimate_interval_output_validation_qualification_bundle()
    issued_before = tuple(module._ISSUED_RECORD_SNAPSHOTS.items())

    def exhausted(_record: object) -> object:
        raise MemoryError("hostile typed-shape allocation")

    monkeypatch.setattr(module, "_typed_record_state", exhausted)
    operations = (
        lambda: module.cp70_canonical_json_bytes(bundle),
        lambda: module.cp70_sha256(bundle),
        module.cp70_estimate_interval_output_validation_qualification_bundle,
        module.cp70_estimate_interval_output_validation_qualification_bundle,
    )
    for operation in operations:
        with pytest.raises(
            module.CP70EstimateIntervalOutputValidationQualificationError
        ) as caught:
            operation()
        assert caught.value.code == "CP70_RESOURCE_EXHAUSTED"
        assert type(caught.value.__cause__) is MemoryError

    assert module._BUNDLE_CACHE is bundle
    assert module._CLOSED_OUTPUT_CACHE is None
    assert tuple(module._ISSUED_RECORD_SNAPSHOTS.items()) == issued_before


def test_cp70_bundle_and_validator_are_concurrently_deterministic() -> None:
    payload = _independent_output()[0]
    with ThreadPoolExecutor(max_workers=8) as executor:
        bundles = tuple(executor.map(lambda _index: _bundle(), range(32)))
        validations = tuple(
            executor.map(
                cp70.cp70_validate_closed_cp68_estimate_interval_output_bytes,
                (payload,) * 16,
            )
        )
    assert all(item is bundles[0] for item in bundles)
    canonical = tuple(cp70.cp70_canonical_json_bytes(item) for item in validations)
    assert canonical == (canonical[0],) * len(canonical)
    assert all(
        item.output_canonical_json_sha256 == _EXPECTED_OUTPUT_SHA256
        for item in validations
    )


def test_cp70_nonclaims_leave_every_production_boundary_fail_closed() -> None:
    bundle = _bundle()
    qualification = _qualification()
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.ledger_total_count == 25
    assert bundle.ledger_satisfied_count == 21
    assert bundle.ledger_missing_count == 4
    assert bundle.ledger_prerequisite_state == (
        "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS"
    )
    assert bundle.zero_argument_builder is True
    assert bundle.builder_parses_reduces_or_validates is False
    assert bundle.qualification_runner_zero_argument is True
    assert bundle.bounded_public_closed_output_byte_validator_exposed is True
    assert bundle.generic_public_stream_reducer_exposed is False
    assert bundle.closed_module_owned_fixture_only is True
    assert bundle.source_independent is True
    assert bundle.stdlib_only_import is True
    assert bundle.streaming_interchange is True
    assert bundle.output_record_vector_cardinality == 554
    assert bundle.development_qualification_only is True
    for name in (
        "project_modules_imported",
        "full_interchange_corpus_materialized",
        "cp68_projection_records_created",
        "host_filesystem_probed",
        "clock_read",
        "rng_used",
        "network_used",
        "subprocess_api_exposed",
        "filesystem_path_api_exposed",
        "raw_record_api_exposed",
        "stable_trace_api_exposed",
        "production_campaign_api_exposed",
        "production_estimate_or_interval",
        "decision_path_qualified",
        "production_qualification_receipt_present",
        "production_gate_13_evidence_present",
        "production_gate_14_evidence_present",
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
        assert getattr(bundle, name) is False, name
    assert bundle.production_evidence_present_count == 0
    assert bundle.production_gate_13_state == "MISSING"
    assert bundle.production_gate_14_state == "MISSING"
    for name in (
        "raw_record_parsed",
        "stable_trace_parsed",
        "provenance_authenticated",
        "production_recomputation_performed",
        "production_estimate_or_interval",
        "decision_path_qualified",
        "production_evidence",
        "production_execution_authorized",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
    ):
        assert getattr(qualification, name) is False, name
    assert qualification.all_development_qualification_checks_passed is True
    scope = cp70.CP70_TEST28_SCOPE
    for fragment in (
        "development-only",
        "closed",
        "no-raw-record",
        "no-stable-trace",
        "no-provenance-authentication",
        "no-production",
        "no-decision",
        "no-test28-closure",
        "transient-plain-projection-digest-preimage-mappings-created-and-discarded",
    ):
        assert fragment in scope


def test_cp70_source_and_bundle_remain_python39_compatible() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    ast.parse(source, filename=str(_SOURCE), feature_version=(3, 9))
    bundle = _bundle()
    assert bundle.stdlib_only_import is True
    assert bundle.project_modules_imported is False
