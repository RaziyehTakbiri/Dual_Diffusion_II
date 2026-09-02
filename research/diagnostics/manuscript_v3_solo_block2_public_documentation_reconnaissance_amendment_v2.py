"""Read-only validator for the Solo Block 2 public-documentation amendment v2.

This module performs local byte and semantic validation only.  It deliberately
contains no network, process, entropy, dynamic-execution, or write route.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = (
    "heterodiff-manuscript-v3-solo-block2-public-documentation-"
    "reconnaissance-amendment-v2"
)
PACKAGE_KIND = "STATIC_TWO_ROOT_PAGE_RECONNAISSANCE_AMENDMENT_TRANSCRIPT_SIMULATION_HOLD"
STATE = "PUBLIC_DOCUMENTATION_RECONNAISSANCE_AMENDMENT_FROZEN_FETCH_HOLD"
REPORTED_DATE = "2026-08-31"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.json"
)
HUMAN_PATH = "PROJECT_SOLO_BLOCK2_PUBLIC_DOCUMENTATION_RECONNAISSANCE_AMENDMENT.md"
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py"
)
SIMULATOR_PATH = "src/heterodiff/artifacts/solo_block2_public_documentation_reconnaissance_executor_v2.py"
SIMULATOR_TEST_PATH = "tests/unit/test_solo_block2_public_documentation_reconnaissance_executor_v2.py"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ValidationError(RuntimeError):
    """Raised on the first fail-closed validation defect."""


def _binding(
    ordinal: int,
    path: str,
    role: str,
    byte_count: int,
    raw_sha256: str,
    record_sha256: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "ordinal": ordinal,
        "path": path,
        "role": role,
        "bytes": byte_count,
        "raw_sha256": raw_sha256,
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    }
    if record_sha256 is not None:
        value["record_sha256"] = record_sha256
    return value


LIVE_IMMUTABLE_INPUT_BINDINGS = [
    _binding(0, "manuscript_v3/execution_preregistration.md", "EXECUTION_PREREGISTRATION_HUMAN", 22491, "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e"),
    _binding(1, "research/fixtures/manuscript_v3_execution_preregistration_v1.json", "EXECUTION_PREREGISTRATION_MACHINE", 39771, "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"),
    _binding(2, "manuscript_v3/execution_preregistration_preexecution_closure_v2.md", "PREEXECUTION_CLOSURE_HUMAN", 14938, "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d"),
    _binding(3, "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json", "PREEXECUTION_CLOSURE_MACHINE", 24571, "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db", "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"),
    _binding(4, "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md", "PROSPECTIVE_SEAL_HUMAN", 7078, "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2"),
    _binding(5, "research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json", "PROSPECTIVE_SEAL_MACHINE", 8461, "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8", "d11d5336f1ede024ab56f92bc64e620681e53fc406fd954aa3da36b7861485a6"),
    _binding(6, "research/diagnostics/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py", "PROSPECTIVE_SEAL_VALIDATOR", 32156, "3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258"),
    _binding(7, "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py", "PROSPECTIVE_SEAL_HOSTILE_TEST", 16698, "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403"),
    _binding(8, "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md", "STATIC_SELECTION_HUMAN", 23012, "ab80a009f3d83be4186d3d2da13e3efd5939362e4215477dd2b1a89b870b3126"),
    _binding(9, "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json", "STATIC_SELECTION_MACHINE", 33638, "7ff0bf3bb5d9a03e2212f2f7f1853cde2283694b33e072931d258d98e1882590", "1f02200d524749d6708695072dfbc8b785a6f03d5be908b3563f121d7fcd5b53"),
    _binding(10, "research/diagnostics/manuscript_v3_solo_block2_static_selection_freeze_v1.py", "STATIC_SELECTION_VALIDATOR", 56344, "8843cef229c24cbd25cd00e55697755c8fc7a1247f20044dfe110e182e558ec0"),
    _binding(11, "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py", "STATIC_SELECTION_HOSTILE_TEST", 48158, "801fc7c87f57eb72da6cdfa7b2be93c6edd66b974fefe47dabbe5b91eaa0f005"),
    _binding(12, "PROJECT_SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE.md", "PRECONTACT_CANDIDATE_HUMAN", 17965, "ed211b7bf5aaf45a839e18d15484177fa0c51d7cb95540cdccc61587b2b8250f"),
    _binding(13, "research/fixtures/manuscript_v3_solo_block2_precontact_instance_candidate_v1.json", "PRECONTACT_CANDIDATE_MACHINE", 23932, "95bae0a0ff0d5a199afc23cfc048de04cce28c47300ada301b927c21c60166be", "2c4c068c553bdfab04d49f01163c84923b9108b2f762872ba00015c2fadd9304"),
    _binding(14, "research/diagnostics/manuscript_v3_solo_block2_precontact_instance_candidate_v1.py", "PRECONTACT_CANDIDATE_VALIDATOR", 46460, "6bdfe3c943c8238d88dc5fba908918d9304ab9f377517a483c65cfac887a39dc"),
    _binding(15, "tests/unit/test_manuscript_v3_solo_block2_precontact_instance_candidate_v1.py", "PRECONTACT_CANDIDATE_HOSTILE_TEST", 27389, "40ba6642f81323fb9254520113697785513bb705e72232731657ae1c481d2856"),
    _binding(16, "PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md", "RETAIL_SPLIT_HUMAN", 11226, "49a38fbe8bfdbc2fcb93de766f7280ba8affd18b2ebedbcc004d079550b752d1"),
    _binding(17, "research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json", "RETAIL_SPLIT_MACHINE", 13409, "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b", "0aa3b6e992ade5343b0d840b382e544ecf5140e352b97a508f359a2fa0d0bed2"),
    _binding(18, "research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py", "RETAIL_SPLIT_VALIDATOR", 38492, "c377c87ae74ee3a4bfc0dd8f695e0df3531c3eec2c080f5b81379e852424a22e"),
    _binding(19, "tests/unit/test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py", "RETAIL_SPLIT_HOSTILE_TEST", 24025, "99ecada07b8325b25e7d227bf9bb5c6e38957619115a7040c636dbdc33cb7109"),
    _binding(20, "PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md", "PHYSIONET_SPLIT_HUMAN", 10761, "2d84753fe87032a81d377a469f858f1702b14474371bfd2d147fd87824bb4b7a"),
    _binding(21, "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json", "PHYSIONET_SPLIT_MACHINE", 16543, "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8", "5eb8964685c95d51d67ce92f1ed08e8cc0147a672f91a75990e563e38f261763"),
    _binding(22, "research/diagnostics/manuscript_v3_physionet_patient_disjoint_split_design_v1.py", "PHYSIONET_SPLIT_VALIDATOR", 35894, "429e4e9291bb42172a6de3b664b13938a537a8840e14ab0f8f4d6e963072a91e"),
    _binding(23, "tests/unit/test_manuscript_v3_physionet_patient_disjoint_split_design_v1.py", "PHYSIONET_SPLIT_HOSTILE_TEST", 15720, "10faf21f66129330eef239ca3e561ecbddee78779a4849e5d60df07624c59982"),
    _binding(24, "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md", "REAL_DOMAIN_POWER_HUMAN", 15223, "a8edf99303e30b6ae6ea9912dce6350fadc9e07361fcd25743c03446a2bb0139"),
    _binding(25, "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json", "REAL_DOMAIN_POWER_MACHINE", 15915, "536493388d23aac2cc3aaf6f9bdc34a12fba77103e9546cbf110c1c8223dfd28", "3846714fca604b3a0a5f05702326b8fd6856f08639bda51a1b7a7dad8a44eef4"),
    _binding(26, "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py", "REAL_DOMAIN_POWER_VALIDATOR", 36100, "be5bcf6cde26d1c4eff044f6fad4705c1e87c850c77f38b2a4f7ef670a03b129"),
    _binding(27, "tests/unit/test_manuscript_v3_real_domain_power_allocation_route_v1.py", "REAL_DOMAIN_POWER_HOSTILE_TEST", 19344, "3c0846ecd924f4e39f7a98414755fdc06c2c1e5d60491879fa4190f5730b9926"),
    _binding(28, "PROJECT_PILOT_VARIANCE_POWER_STRATEGY_DRAFT.md", "PILOT_POWER_HUMAN", 11609, "def13998bba651bf3737288079e8a79e1b7221a8aab680cf67ef248f785ed1ba"),
    _binding(29, "research/fixtures/manuscript_v3_pilot_variance_power_strategy_draft_v1.json", "PILOT_POWER_MACHINE", 8423, "4a01541ff60be7b0d5ef875aa7af0d646d24754d4ffb3027fb5eb65f43b7ee58", "883f673d99083cfb0c8aae87a718eb12f2a9c3e3bc7bd92537f725267a86b031"),
    _binding(30, "research/diagnostics/manuscript_v3_pilot_variance_power_strategy_draft_v1.py", "PILOT_POWER_VALIDATOR", 18533, "d55c6cc29bb5905623bf81bc467a35da96a67f9a0c9f7dc767e2eb646fe76c2a"),
    _binding(31, "tests/unit/test_manuscript_v3_pilot_variance_power_strategy_draft_v1.py", "PILOT_POWER_HOSTILE_TEST", 11737, "15b480991c9363d1050952015635f480a75c770ed517a42d5ae9a9f94b106229"),
]


HISTORICAL_SNAPSHOT_INPUTS = [
    {
        "ordinal": 0,
        "path": "PROJECT_COMPLETION_TIMETABLE.md",
        "role": "CURRENT_MUTABLE_TIMETABLE_HISTORICAL_SNAPSHOT",
        "bytes": 50603,
        "raw_sha256": "a1395d4d9bebc61c2dcd5fc95cf297b3f12da04fdfa2970ade0e6ac3719f2f78",
        "checked_boxes": 28,
        "open_boxes": 118,
        "historical_snapshot_only": True,
        "live_custody_validated": False,
        "future_mutation_expected": True,
        "reverse_binding_forbidden": True,
    },
    {
        "ordinal": 1,
        "path": "PROJECT_EVIDENCE_LEDGER.md",
        "role": "CURRENT_MUTABLE_EVIDENCE_LEDGER_HISTORICAL_SNAPSHOT",
        "bytes": 94371,
        "raw_sha256": "aecf7ff53b13a553421ec19460466150ededf84e2810f9d8854eedb8f7316f93",
        "open_fields": 152,
        "closed_fields": 20,
        "historical_snapshot_only": True,
        "live_custody_validated": False,
        "future_mutation_expected": True,
        "reverse_binding_forbidden": True,
    },
]


AUTHORITY_PROVENANCE = {
    "source": "CONVERSATION_VISIBLE_TEXT_IN_PRIOR_DESCRIBED_PREPARATION_CONTEXT",
    "normalized_visible_text": "Sounds good, go through those deferred items in Solo Block 2.",
    "normalized_visible_text_utf8_bytes": 61,
    "normalized_visible_text_sha256": "80bfdee90ba72bfb1de81058945001cbe5aca1931491636b474d419d93c08c6f",
    "normalization": "TRAILING_TRANSPORT_FRAMING_OR_HTML_SPACE_ENTITY_UNBOUND_ONLY",
    "raw_transport_bytes_bound": False,
    "account_identity_bound": False,
    "timestamp_bound": False,
    "conversation_envelope_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "six_file_amendment_transcript_simulator_construction_and_read_only_review_authorized": True,
    "preparation_for_described_read_only_official_source_and_license_verification_authorized": True,
    "current_assent_binds_final_machine_raw_or_package_aggregate_digest": False,
    "current_assent_binds_operational_final_exact_request_digest": False,
    "fetch_execution_authorized_now": False,
    "exact_runtime_admitted": False,
    "fetch_eligible": False,
    "fresh_post_review_exact_authority_required_per_row": True,
    "durable_intent_required_per_row": True,
    "administrative_message_email_ticket_or_form_authorized": False,
    "approval_creation_or_request_authorized": False,
    "authentication_credential_or_cookie_use_authorized": False,
    "archive_file_or_api_download_authorized": False,
    "data_access_authorized": False,
    "escrow_operation_authorized": False,
    "scientific_entropy_authorized": False,
    "runtime_training_or_scientific_execution_authorized": False,
    "result_claim_or_submission_authorized": False,
    "tracker_edit_authorized_by_this_package": False,
    "user_selected_paths_schema_headers_client_or_limits": False,
    "agent_selected_bounded_implementation_details": True,
}


BINDING_POLICY = {
    "live_inputs_are_read_only_exact_byte_dependencies": True,
    "live_input_package_classes": [
        "EXECUTION_PREREGISTRATION_AND_CLOSURE",
        "PROSPECTIVE_NO_ACQUISITION_SEAL",
        "SOLO_BLOCK2_STATIC_SELECTION",
        "SOLO_BLOCK2_PRECONTACT_CANDIDATE",
        "RETAIL_SPLIT_DESIGN",
        "PHYSIONET_SPLIT_DESIGN",
        "REAL_DOMAIN_POWER_ROUTE",
        "PILOT_VARIANCE_POWER_DRAFT",
    ],
    "mutable_trackers_are_historical_snapshot_receipts_only": True,
    "mutable_trackers_reopened_by_validator": False,
    "future_tracker_may_consume_after_independent_go_one_way": True,
    "reverse_binding_from_this_package_to_future_tracker_forbidden": True,
    "package_can_rewrite_predecessor_or_tracker": False,
}


NARROW_SUPERSESSION_CONTRACT = {
    "predecessor_schema_version": "heterodiff-manuscript-v3-solo-block2-precontact-instance-candidate-v1",
    "predecessor_raw_sha256": "95bae0a0ff0d5a199afc23cfc048de04cce28c47300ada301b927c21c60166be",
    "predecessor_record_sha256": "2c4c068c553bdfab04d49f01163c84923b9108b2f762872ba00015c2fadd9304",
    "new_scope_review_occurred_before_any_fetch_contact_or_terminal_event": True,
    "exact_predecessor_predicates": [
        {
            "path": "authority_provenance.dataset_page_browsing_authorized",
            "predecessor_value": False,
            "v2_effect": "CURRENTLY_FALSE_FUTURE_EXACT_ROOT_GET_ONLY_AFTER_LATER_RUNTIME_CLOSURE_NEW_EXECUTOR_GO_INTENT_AND_FRESH_ROW_AUTHORITY",
        },
        {
            "path": "authority_provenance.documentation_license_or_governance_browsing_authorized",
            "predecessor_value": False,
            "v2_effect": "CURRENTLY_FALSE_FUTURE_EXACT_ROOT_GET_ONLY_AFTER_LATER_RUNTIME_CLOSURE_NEW_EXECUTOR_GO_INTENT_AND_FRESH_ROW_AUTHORITY",
        },
        {
            "path": "candidate_selectors.reconnaissance_or_target_amendment_permitted",
            "predecessor_value": False,
            "v2_effect": "NARROWLY_SUPERSEDED_FOR_ONLY_THE_TWO_FROZEN_ROOT_PAGE_TEMPLATES_NO_TARGET_AMENDMENT",
        },
        {
            "path": "gap_inventory.documentation_license_governance_reconnaissance_exception_permitted",
            "predecessor_value": False,
            "v2_effect": "NARROWLY_SUPERSEDED_FOR_ONLY_THE_TWO_FROZEN_ROOT_PAGE_TEMPLATES_AFTER_ALL_NEW_GATES",
        },
        {
            "path": "gap_inventory.target_mismatch_permits_amendment_or_reconnaissance",
            "predecessor_value": False,
            "v2_effect": "UNCHANGED_FALSE",
        },
        {
            "path": "failure_and_state_contract.terminal_no_go_permits_retry_repair_replacement_fallback_deletion_reacquisition_or_amendment",
            "predecessor_value": False,
            "v2_effect": "UNCHANGED_FALSE",
        },
    ],
    "predecessor_bytes_modified": False,
    "current_fetch_authority_created": False,
    "third_target_mirror_fallback_child_search_or_post_failure_amendment_created": False,
    "all_other_predecessor_predicates_unchanged": True,
}


PACKAGE_DIGEST_CONTRACT = {
    "package_aggregate_schema_version": "heterodiff-sb2-public-root-package-aggregate-v2",
    "package_aggregate_key_order": [
        "schema_version", "machine_raw_sha256", "machine_record_sha256",
        "human_raw_sha256", "validator_raw_sha256",
        "amendment_test_raw_sha256", "transcript_simulator_raw_sha256",
        "transcript_simulator_test_raw_sha256",
    ],
    "package_aggregate_canonicalization": "UTF8_SORTED_KEYS_COMPACT_SEPARATORS_NO_NAN_NO_TRAILING_LF",
    "machine_semantic_digest": "TOP_LEVEL_RECORD_SHA256_USING_CANONICAL_RECORD_WITH_RECORD_SHA256_NULL",
    "machine_raw_digest": "SHA256_OF_FINAL_CANONICAL_MACHINE_JSON_BYTES_PLUS_LF_COMPUTED_BY_INDEPENDENT_POST_FREEZE_PACKAGE_REVIEW",
    "package_aggregate_digest": (
        "SHA256_OF_CANONICAL_JSON_NO_LF_WITH_KEYS_SCHEMA_VERSION_MACHINE_RAW_SHA256_"
        "MACHINE_RECORD_SHA256_HUMAN_RAW_SHA256_VALIDATOR_RAW_SHA256_AMENDMENT_TEST_"
        "RAW_SHA256_TRANSCRIPT_SIMULATOR_RAW_SHA256_TRANSCRIPT_SIMULATOR_TEST_RAW_SHA256"
    ),
    "machine_cannot_embed_its_own_raw_digest_without_cycle": True,
    "machine_raw_digest_or_package_aggregate_embedded_here": False,
    "independent_package_review_must_compute_and_bind_both": True,
    "future_operational_go_and_fresh_row_authority_must_bind_machine_raw_semantic_and_package_aggregate_digests": True,
    "term_final_v2_package_digest_is_ambiguous_and_forbidden": True,
}


GLOBAL_SEQUENCE_CONTRACT = {
    "scope": "FUTURE_RUNTIME_CLOSURE_MINIMUM_NOT_CURRENTLY_ELIGIBLE",
    "row_order": [
        "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "SB2-PUBLIC-ROOT-UCI-001",
    ],
    "row0_can_reserve_only_after_all_common_gates": True,
    "row1_requires_row0_terminal_state": "TERMINAL_ROOT_PAGE_OBSERVED_UNVERIFIED_NO_RETRY",
    "row1_intent_must_bind_row0_outcome_sha256": True,
    "row1_go_and_fresh_authority_must_postdate_and_bind_row0_success_outcome": True,
    "row0_any_non_success_or_missing_durable_outcome_preempts_row1": True,
    "row1_preempted_state": "TERMINAL_PREEMPTED_BY_ROW0_NO_REQUEST_NO_INTENT",
    "row1_reservation_before_row0_exact_success_permitted": False,
    "row0_success_alone_authorizes_row1": False,
    "independent_go_or_authority_for_row0_automatically_applies_to_row1": False,
    "parallel_or_out_of_order_reservation_or_fetch_permitted": False,
    "any_terminal_state_authorizes_retry_or_additional_network_operation": False,
}


REVIEW_AND_AUTHORITY_CONTRACT = {
    "transcript_simulation_results_scope": "TRANSCRIPT_SIMULATION_ONLY_NONOPERATIONAL",
    "transcript_simulation_results_can_create_operational_go_authority_intent_or_outcome": False,
    "operational_independent_go_schema_version": None,
    "operational_independent_go_key_order": None,
    "operational_independent_go_types": None,
    "operational_fresh_authority_schema_version": None,
    "operational_fresh_authority_key_order": None,
    "operational_fresh_authority_types": None,
    "operational_exact_affirmative_authority_template": None,
    "operational_go_receipt_path": None,
    "operational_go_receipt_sha256": None,
    "operational_fresh_authority_receipts": [None, None],
    "current_user_text_can_promote_simulation_result_or_fill_operational_schema": False,
    "later_runtime_closure_must_freeze_exact_operational_go_and_authority_schemas": True,
    "later_authority_must_use_exact_rendered_affirmative_equality_not_token_presence": True,
    "digest_presence_without_exact_future_schema_semantics_chronology_and_byte_validation_is_authority": False,
}


RUNTIME_ADMISSION_CONTRACT = {
    "decision": "DORMANT_DESIGN_AND_PURE_TRANSCRIPT_SIMULATION_ONLY",
    "exact_runtime_admitted": False,
    "fetch_eligible": False,
    "production_network_entrypoint_present": False,
    "resolver_socket_tls_connect_send_or_receive_code_present": False,
    "caller_injected_transport_callable_present": False,
    "canonical_or_operational_write_path_present": False,
    "bound_inert_simulator_semantics": {
        "executor_schema_version": "heterodiff-sb2-public-root-dormant-transcript-simulator-v2",
        "inert_transcript_schema_version": "heterodiff-sb2-public-root-inert-transcript-v2",
        "in_memory_intent_model_schema_version": "heterodiff-sb2-public-root-in-memory-intent-model-v2",
        "inert_outcome_and_simulation_result_schema_version": "heterodiff-sb2-public-root-inert-outcome-v2",
        "package_role": "DORMANT_TRANSCRIPT_SIMULATOR",
        "executor_contract_sha256": "0bd86fe3b851603e68ea642619645e71334a8f689be8d97438490d04a51fe9f2",
        "operation_roster_sha256": "5f305448d4032b55dac54057d2d659212dd512e65113c1123409aa3c089b7548",
        "outcome_diagnostic_field_count": 36,
        "outcome_diagnostic_field_types_sha256": "a8fdba4d39e97ac3fbf23d065ae2bd9805cc0513f77d2232c23c7bf4799966dd",
        "binding_is_operational_runtime_client_custody_or_request_admission": False,
    },
    "simulator_input_scope": "EXACT_FROZEN_TRANSCRIPT_VALUE_OBJECT_AND_VALIDATED_BUILTIN_PRIOR_MODEL_ONLY",
    "simulator_input_roster": {
        "row_ordinal": "EXACT_INT_ONE_OF_0_OR_1_NOT_BOOL",
        "transcript_type": "EXACT_FROZEN_INERT_TRANSCRIPT_VALUE_OBJECT",
        "transcript_fields_in_order": [
            ["intent_utc", "STRICT_STRING"],
            ["started_utc", "STRICT_STRING"],
            ["finished_utc", "STRICT_STRING"],
            ["simulated_resolver_host", "STRICT_STRING"],
            ["simulated_resolver_port", "EXACT_INT_NOT_BOOL"],
            ["simulated_resolver_results", "TUPLE_OF_STRICT_STRINGS"],
            ["simulated_selected_address", "STRICT_STRING"],
            ["simulated_socket_instance_count", "EXACT_INT_NOT_BOOL"],
            ["simulated_connect_attempt_count", "EXACT_INT_NOT_BOOL"],
            ["simulated_tls_wrap_count", "EXACT_INT_NOT_BOOL"],
            ["simulated_send_attempt_count", "EXACT_INT_NOT_BOOL"],
            ["simulated_emitted_request_bytes", "STRICT_BYTES_OR_NULL"],
            ["supplied_tls_version", "STRICT_STRING_OR_NULL"],
            ["supplied_alpn", "STRICT_STRING_OR_NULL"],
            ["supplied_cipher_name", "STRICT_STRING_OR_NULL"],
            ["supplied_cipher_protocol", "STRICT_STRING_OR_NULL"],
            ["supplied_cipher_bits", "EXACT_INT_NOT_BOOL_OR_NULL"],
            ["supplied_peer_certificate_bytes", "STRICT_BYTES_OR_NULL"],
            ["response_chunks", "TUPLE_OF_STRICT_BYTES"],
            ["injected_failure_stage", "STRICT_STRING_OR_NULL"],
        ],
        "prior_transcript": "ROW0_EXACT_NULL_ROW1_EXACT_FROZEN_ROW0_TRANSCRIPT_VALUE_OBJECT",
        "prior_outcome": "ROW0_EXACT_NULL_ROW1_RECURSIVE_TYPE_AND_VALUE_EQUALITY_TO_FULL_RECOMPUTED_ROW0_MODELED_OUTCOME_NO_BOOL_INT_FLOAT_ALIAS",
        "prior_outcome_self_digest_alone_is_authentication": False,
        "callable_path_fd_client_or_general_object_permitted": False,
    },
    "simulator_output_scope": "IN_MEMORY_DESIGN_VALIDATION_RESULT_ONLY",
    "simulator_source_or_interpreter_receipts_do_not_constitute_loaded_runtime_admission": True,
    "separate_independently_reviewed_runtime_closure_amendment_required": True,
    "future_runtime_closure_minimum_roster": [
        "EXACT_NON_SYMLINK_INTERPRETER_BYTES_MODE_LINK_COUNT",
        "EXACT_EXECUTOR_AND_IMPORTED_STDLIB_MODULE_BYTES",
        "EXACT_LOADED_SSL_SOCKET_HASHLIB_AND_NATIVE_EXTENSION_BYTES",
        "EXACT_LOADED_TLS_CRYPTO_C_LIBRARIES_AND_DYNAMIC_LOADER_RECEIPTS",
        "EXACT_CA_BUNDLE_BYTES",
        "EXACT_DNS_RESOLVER_CONFIGURATION_AND_POLICY",
        "EXACT_KERNEL_OS_ARCHITECTURE_AND_NETWORK_AFFECTING_ENVIRONMENT",
        "EXACT_PRODUCTION_DEPENDENCY_IDENTITY_WITH_NO_INJECTED_CALLABLES_OR_TEST_SEAMS",
        "EXACT_DURABLE_CUSTODY_ROOT_AND_DIRECTORY_SEMANTICS",
        "INDEPENDENT_STATIC_RUNTIME_AND_RAW_CUSTODY_QUALIFICATION_GO",
    ],
    "runtime_closure_receipt_path": None,
    "runtime_closure_receipt_sha256": None,
    "later_runtime_closure_can_retroactively_authorize_fetch": False,
    "fresh_post_runtime_row_go_and_authority_still_required": True,
}


SCOPE_REVIEW = {
    "physical_file_count": 6,
    "one_validation_package": True,
    "amendment_construction_complete": True,
    "independent_review_complete": True,
    "operation_roster_frozen": True,
    "operation_count": 2,
    "fetches_performed": 0,
    "durable_intents_created": 0,
    "durable_outcomes_created": 0,
    "offline_extractions_created": 0,
    "qualification_filesystem_operational_or_network_artifacts_permitted": False,
    "explicitly_labeled_in_memory_modeled_records_permitted": True,
    "in_memory_transcript_simulation_results_are_canonical_or_operational": False,
    "exact_runtime_admitted": False,
    "fetch_eligible": False,
    "current_fetch_state": "HOLD_PENDING_SEPARATE_RUNTIME_CLOSURE_WITH_NEW_EXECUTOR_AND_FRESH_REVIEW_AUTHORITY_INTENT",
    "amendment_can_create_approval_or_source_selection_success": False,
}


USER_AGENT = "heterodiff-precontact-public-doc-recon-v2/2.0"
ACCEPT = "text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
HOLD_STATE = (
    "HOLD_PENDING_SEPARATE_RUNTIME_CLOSURE_WITH_NEW_EXECUTOR_AND_"
    "FRESH_REVIEW_AUTHORITY_INTENT"
)
COMMON_DESIGN_CONSTRAINTS = {
    "method": "GET",
    "http_version": "HTTP/1.1",
    "https_only": True,
    "future_tls_minimum": "TLSv1.2",
    "future_tls_maximum": "TLSv1.3",
    "future_server_certificate_and_hostname_verification_required": True,
    "request_body_bytes": 0,
    "request_body_sha256": EMPTY_SHA256,
    "future_connect_timeout_ms": 5000,
    "future_total_timeout_ms": 15000,
    "max_raw_status_bytes": 8192,
    "max_raw_header_bytes": 131072,
    "max_raw_response_head_bytes": 139264,
    "max_encoded_body_bytes": 2097152,
    "max_decoded_body_bytes": 2097152,
    "max_raw_metadata_bytes": 8192,
    "max_raw_stderr_bytes": 65536,
    "max_attempts": 1,
    "max_retries": 0,
    "max_redirects": 0,
    "future_implicit_headers_permitted": False,
    "future_automatic_decompression_permitted": False,
    "dns_preflight_or_probe_permitted": False,
    "search_query_permitted": False,
    "alternate_url_host_mirror_or_fallback_permitted": False,
    "child_page_open_permitted": False,
    "head_request_permitted": False,
    "robots_fetch_permitted": False,
    "authentication_permitted": False,
    "credential_client_certificate_or_secret_permitted": False,
    "cookies_permitted": False,
    "forms_permitted": False,
    "range_permitted": False,
    "referer_permitted": False,
    "conditional_request_permitted": False,
    "link_following_permitted": False,
    "scripts_or_subresources_permitted": False,
    "archive_file_api_or_data_access_permitted": False,
}


def _operation(
    ordinal: int,
    operation_id: str,
    domain_id: str,
    url: str,
    host: str,
    request_target: str,
    sequence_prerequisite: dict[str, Any] | None,
) -> dict[str, Any]:
    header_order = [
        {"name": "Host", "value": host},
        {"name": "User-Agent", "value": USER_AGENT},
        {"name": "Accept", "value": ACCEPT},
        {"name": "Accept-Encoding", "value": "identity"},
        {"name": "Cache-Control", "value": "no-cache"},
        {"name": "Pragma", "value": "no-cache"},
        {"name": "Connection", "value": "close"},
    ]
    lines = [f"GET {request_target} HTTP/1.1"]
    lines.extend(f"{item['name']}: {item['value']}" for item in header_order)
    raw_request = ("\r\n".join(lines) + "\r\n\r\n").encode("ascii")
    return {
        "ordinal": ordinal,
        "operation_id": operation_id,
        "domain_id": domain_id,
        "url": url,
        "scheme": "https",
        "host": host,
        "port": 443,
        "request_target": request_target,
        "sequence_prerequisite": sequence_prerequisite,
        "inert_request_design": {
            "schema_version": "heterodiff-sb2-public-root-inert-request-design-v2",
            "request_line": f"GET {request_target} HTTP/1.1",
            "header_order": header_order,
            "raw_request_ascii": raw_request.decode("ascii"),
            "raw_request_bytes": len(raw_request),
            "raw_request_sha256": hashlib.sha256(raw_request).hexdigest(),
            **COMMON_DESIGN_CONSTRAINTS,
        },
        "allowed_response_media_types": [
            "text/html",
            "application/xhtml+xml",
            "text/plain",
        ],
        "current_state": HOLD_STATE,
        "request_design_is_executable": False,
        "request_emission_code_present_in_package": False,
        "operational_final_exact_request_sha256": None,
        "attempts_emitted": 0,
        "retry_permitted": False,
    }


OPERATION_ROSTER = [
    _operation(
        0,
        "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "physionet-challenge-2012",
        "https://physionet.org/content/challenge-2012/1.0.0/",
        "physionet.org",
        "/content/challenge-2012/1.0.0/",
        None,
    ),
    _operation(
        1,
        "SB2-PUBLIC-ROOT-UCI-001",
        "online-retail-ii",
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "archive.ics.uci.edu",
        "/dataset/502/online+retail+ii",
        {
            "prior_ordinal": 0,
            "prior_operation_id": "SB2-PUBLIC-ROOT-PHYSIONET-000",
            "required_terminal_state": "TERMINAL_ROOT_PAGE_OBSERVED_UNVERIFIED_NO_RETRY",
            "prior_outcome_sha256_required_in_go_authority_and_intent": True,
            "any_other_prior_state_disposition": "TERMINAL_PREEMPTED_BY_ROW0_NO_REQUEST_NO_INTENT",
        },
    ),
]


REQUEST_ENVIRONMENT_CONTRACT = {
    "scope": "INERT_REQUEST_DESIGN_ONLY_NO_OPERATIONAL_RUNTIME_OR_REQUEST_DIGEST",
    "exact_runtime_admitted": False,
    "fetch_eligible": False,
    "client_executable_path": None,
    "client_executable_sha256": None,
    "client_version_report_sha256": None,
    "tls_implementation_report_sha256": None,
    "ca_bundle_path": None,
    "ca_bundle_sha256": None,
    "environment_manifest_sha256": None,
    "raw_custody_executor_sha256": None,
    "operational_final_exact_request_sha256_by_row": [None, None],
    "inert_design_request_sha256_by_row": [
        OPERATION_ROSTER[0]["inert_request_design"]["raw_request_sha256"],
        OPERATION_ROSTER[1]["inert_request_design"]["raw_request_sha256"],
    ],
    "inert_design_digests_are_operational_or_executable": False,
    "future_runtime_closure_must_replace_or_explicitly_supersede_design_digests": True,
    "future_runtime_closure_must_bind_exact_loaded_client_tls_ca_environment_and_emitted_request_bytes": True,
    "future_runtime_closure_must_prove_no_implicit_headers_redirects_retries_or_transparent_decoding": True,
    "future_client_must_expose_exact_raw_request_status_headers_transfer_body_and_effective_url": True,
    "browser_abstraction_without_redirect_control_and_raw_receipts_disposition": "HOLD",
}


FUTURE_OPERATIONAL_SCHEMA_BOUNDARY = {
    "operational_go_schema": None,
    "operational_fresh_authority_schema": None,
    "operational_intent_schema": None,
    "operational_outcome_schema": None,
    "operational_extraction_schema": None,
    "operational_contact_roster_schema": None,
    "later_runtime_closure_review_required_before_any_nonnull_schema": True,
    "this_package_can_materialize_operational_record": False,
}


DURABLE_CUSTODY_CONTRACT = {
    "scope": "FUTURE_RUNTIME_CLOSURE_MINIMUM_DESIGN_ONLY_NOT_OPERATIONAL_ADMISSION",
    "future_operational_schema_boundary": FUTURE_OPERATIONAL_SCHEMA_BOUNDARY,
    "transcript_simulator_materializes_filesystem_or_operational_intent_outcome_custody_artifacts": False,
    "transcript_simulator_may_return_explicitly_labeled_in_memory_models": True,
    "custody_invariants_are_modeled_only": True,
    "operational_custody_qualified": False,
    "transcript_simulator_filesystem_side_effects_present": False,
    "operational_intent_schema_version": None,
    "operational_intent_record_key_order": None,
    "operational_intent_record_types": None,
    "operational_outcome_schema_version": None,
    "operational_outcome_record_key_order": None,
    "operational_outcome_record_types": None,
    "later_runtime_closure_must_freeze_exact_operational_schemas": True,
    "canonical_json": "UTF8_SORTED_KEYS_COMPACT_SEPARATORS_NO_NAN_PLUS_ONE_LF",
    "self_digest_rule": "SHA256_OF_CANONICAL_RECORD_WITH_RECORD_SHA256_NULL",
    "intent_create_flags": ["O_WRONLY", "O_CREAT", "O_EXCL", "O_NOFOLLOW"],
    "outcome_create_flags": ["O_WRONLY", "O_CREAT", "O_EXCL", "O_NOFOLLOW"],
    "raw_sidecar_create_flags": ["O_WRONLY", "O_CREAT", "O_EXCL", "O_NOFOLLOW"],
    "custody_root_absolute_path_current": None,
    "custody_root_device_current": None,
    "custody_root_inode_current": None,
    "custody_root_owner_uid_current": None,
    "row_directory_basename_current": None,
    "custody_root_must_be_absolute_preexisting_authority_bound_and_preopened_before_row_directory_creation": True,
    "custody_root_open_flags": ["O_RDONLY", "O_DIRECTORY", "O_NOFOLLOW"],
    "custody_root_expected_mode_octal": "0700",
    "row_directory_basename_must_be_authority_bound_single_component": True,
    "row_directory_create_mode_octal": "0700",
    "row_directory_created_with_mkdirat_against_preopened_root_dirfd": True,
    "row_directory_opened_with_openat_O_RDONLY_O_DIRECTORY_O_NOFOLLOW": True,
    "all_files_created_with_openat_against_preopened_row_dirfd": True,
    "relative_basenames_must_contain_no_slash_dotdot_nul_or_empty_component": True,
    "root_and_row_directory_owner_mode_device_inode_and_nlink_verified": True,
    "symlink_traversal_permitted": False,
    "ambient_pathlib_resolution_after_root_open_permitted": False,
    "exact_relative_path_templates": {
        "intent": "row-{ordinal:03d}.intent.json",
        "raw_request": "row-{ordinal:03d}.raw-request.bin",
        "raw_response_head": "row-{ordinal:03d}.raw-response-head.bin",
        "raw_transfer_body": "row-{ordinal:03d}.raw-transfer-body.bin",
        "raw_metadata": "row-{ordinal:03d}.raw-metadata.bin",
        "raw_stderr": "row-{ordinal:03d}.raw-stderr.bin",
        "decoded_entity_body": "row-{ordinal:03d}.decoded-entity-body.bin",
        "outcome": "row-{ordinal:03d}.outcome.json",
    },
    "modeled_preoutcome_artifact_role_order": [
        "intent",
        "raw_request",
        "raw_response_head",
        "raw_transfer_body",
        "raw_metadata",
        "raw_stderr",
        "decoded_entity_body",
    ],
    "containing_modeled_outcome_can_self_receipt_or_self_hash": False,
    "future_durable_outcome_append_and_link_unimplemented_unqualified": True,
    "all_raw_sidecars_exclusively_created_and_empty_fsynced_before_request": True,
    "all_raw_sidecars_written_only_through_preopened_fds_or_noninjectable_internal_sinks": True,
    "client_reopen_truncate_or_path_based_overwrite_permitted": False,
    "inode_device_owner_mode_and_nlink_verified_before_and_after_client": True,
    "raw_status_and_headers_retained_in_one_head_sidecar_with_exact_offsets": True,
    "raw_transfer_body_retained_before_offline_dechunk": True,
    "decoded_entity_body_is_derived_separate_receipted_sidecar": True,
    "raw_request_bytes_receipted_before_emission": True,
    "raw_metadata_includes_exact_effective_url_status_redirect_count_and_tls_result": True,
    "per_sidecar_caps": {
        "raw_request": 131072,
        "raw_status": 8192,
        "raw_headers": 131072,
        "raw_response_head": 139264,
        "raw_transfer_body": 2097152,
        "raw_metadata": 8192,
        "raw_stderr": 65536,
        "decoded_entity_body": 2097152,
    },
    "cap_exceedance_disposition": "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY",
    "mode_octal": "0600",
    "regular_file_required": True,
    "nlink_required": 1,
    "expected_owner_required": True,
    "file_fsync_required_before_close": True,
    "every_raw_sidecar_fsync_required_before_outcome": True,
    "already_open_parent_directory_fsync_required": True,
    "overwrite_truncate_rename_over_repair_or_replace_permitted": False,
    "append_only_hash_link_required": True,
    "durable_intent_spends_attempt": True,
    "intent_without_outcome_terminal": "TERMINAL_SPENT_INCOMPLETE_NO_RETRY",
    "second_intent_retry_resume_replacement_or_topup_permitted": False,
}


FAILURE_CONTRACT = {
    "scope": "FUTURE_OPERATIONAL_MINIMUM_AND_INERT_TRANSCRIPT_SIMULATION_ONLY",
    "precedence": [
        "TERMINAL_PROTOCOL_VIOLATION_NO_RETRY",
        "TERMINAL_SPENT_INCOMPLETE_NO_RETRY",
        "TERMINAL_SCOPE_VIOLATION_NO_RETRY",
        "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY",
        "TERMINAL_ROOT_PAGE_OBSERVED_UNVERIFIED_NO_RETRY",
    ],
    "success_requires": {
        "emitted_request_count": 1,
        "status_code": 200,
        "effective_url_exact_row_url": True,
        "redirect_count": 0,
        "complete_raw_status_headers_body_and_final_url_custody": True,
        "encoded_body_at_or_below_ceiling": True,
        "body_truncated": False,
        "allowed_media_type": True,
        "content_type_header_count": 1,
        "content_disposition_header_count": 0,
        "location_header_count": 0,
        "content_encoding_valid_absent_or_single_identity": True,
        "transfer_encoding_valid_absent_or_single_chunked": True,
        "decoded_entity_body_receipt_complete": True,
        "login_consent_challenge_robot_or_error_page_detected": False,
        "nonempty_utf8_no_bom_or_prohibited_control_bytes": True,
        "forbidden_magic_detected": False,
    },
    "forbidden_magic_hex_prefixes": [
        "1f8b", "504b0304", "504b0506", "425a68", "fd377a585a00",
        "377abcaf271c", "526172211a0700", "526172211a070100",
        "50415231", "894844460d0a1a0a", "53514c69746520666f726d6174203300",
        "43444601", "43444602", "4152524f5731", "8002", "8003", "8004", "8005",
    ],
    "three_xx_is_terminal_redirect_failure": True,
    "login_consent_challenge_robot_error_or_ambiguous_page_success": False,
    "terminal_outcome_authorizes_followup_network_operation": False,
    "outcome_can_create_approval": False,
    "outcome_can_create_source_selection_success": False,
    "outcome_can_close_tracker_field_box_blocker_test_result_or_science": False,
}


INERT_SIMULATOR_OUTCOME_DIAGNOSTIC_FIELD_TYPES = [
    {"field": "status_code", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "protocol", "exact_type": "EXACT_STRING_OR_NULL"},
    {"field": "framing", "exact_type": "EXACT_STRING_OR_NULL"},
    {"field": "framing_complete", "exact_type": "EXACT_BOOL"},
    {"field": "header_diagnostics_complete", "exact_type": "EXACT_BOOL"},
    {"field": "content_type_header_count", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "content_type_raw_values", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "normalized_media_type", "exact_type": "EXACT_STRING_OR_NULL"},
    {"field": "content_disposition_header_count", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "content_disposition_raw_values", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "location_header_count", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "location_raw_values", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "content_encoding_header_count", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "content_encoding_raw_values", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "content_encoding_normalized_values", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "transfer_encoding_header_count", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "transfer_encoding_raw_values", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "transfer_encoding_normalized_values", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "transfer_encoding_semantics_valid", "exact_type": "EXACT_BOOL"},
    {"field": "dechunk_complete", "exact_type": "EXACT_BOOL"},
    {"field": "decoded_entity_body_receipt_complete", "exact_type": "EXACT_BOOL"},
    {"field": "body_utf8_valid", "exact_type": "EXACT_BOOL"},
    {"field": "forbidden_magic_detected", "exact_type": "EXACT_BOOL"},
    {"field": "forbidden_magic_prefix_matches", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "challenge_page_detected", "exact_type": "EXACT_BOOL"},
    {"field": "login_wall_detected", "exact_type": "EXACT_BOOL"},
    {"field": "consent_wall_detected", "exact_type": "EXACT_BOOL"},
    {"field": "robot_block_detected", "exact_type": "EXACT_BOOL"},
    {"field": "error_page_detected", "exact_type": "EXACT_BOOL"},
    {"field": "rejection_substring_matches", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "title_classifier_matches", "exact_type": "EXACT_LIST_OF_EXACT_STRING"},
    {"field": "raw_status_start", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "raw_status_end_exclusive", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "raw_headers_start", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "raw_headers_end_exclusive", "exact_type": "EXACT_INT_OR_NULL"},
    {"field": "body_truncated", "exact_type": "EXACT_BOOL"},
]
INERT_SIMULATOR_OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256 = (
    "a8fdba4d39e97ac3fbf23d065ae2bd9805cc0513f77d2232c23c7bf4799966dd"
)


PAGE_REJECTION_CONTRACT = {
    "scope": "FUTURE_OPERATIONAL_MINIMUM_AND_INERT_TRANSCRIPT_SIMULATION_ONLY",
    "global_terminal_precedence": "COMPLETE_PROTOCOL_AND_FRAMING_VALIDATION_OF_ALL_SUPPLIED_BYTES_BEFORE_SCOPE_STATUS_OR_CONTENT_CLASSIFICATION",
    "header_parser": "ASCII_RFC7230_FIELD_NAMES_NO_OBS_FOLD_DUPLICATES_COUNTED_SEPARATELY",
    "content_type_header_count_required": 1,
    "content_disposition_header_count_required": 0,
    "any_content_disposition_including_inline_or_attachment_is_terminal": True,
    "location_header_count_required": 0,
    "content_encoding_header_count_allowed": [0, 1],
    "content_encoding_normalized_values_allowed": [[], ["identity"]],
    "content_encoding_raw_values_must_match_normalized_semantics": True,
    "transfer_encoding_header_count_allowed": [0, 1],
    "transfer_encoding_normalized_values_allowed": [[], ["chunked"]],
    "transfer_encoding_raw_values_must_match_normalized_semantics": True,
    "transfer_encoding_handling": "RETAIN_RAW_TRANSFER_BODY_AND_OFFLINE_DECHUNK_TO_SEPARATE_DERIVED_ENTITY_RECEIPT_OR_HOLD",
    "connection_close_requires_exactly_one_final_inert_eof_event": True,
    "dechunk_completion_and_derived_receipt_required_for_success": True,
    "body_truncated_semantics": "TRUE_IFF_SUPPLIED_BODY_OR_DECODED_ENTITY_BYTES_WERE_NOT_FULLY_RETAINED_DUE_TO_A_FROZEN_BYTE_CEILING",
    "body_utf8_valid_semantics": "TRUE_AFTER_SUCCESSFUL_UTF8_DECODE_EVEN_IF_A_LATER_SCOPE_STATUS_OR_CONTENT_CLASSIFIER_REJECTS",
    "semantic_scan_input": "COMPLETE_UTF8_DECODED_ENTITY_BODY_NOT_RAW_CHUNK_STREAM",
    "semantic_scan_normalization": "UTF8_DECODE_THEN_UNICODE_CASEFOLD_THEN_COLLAPSE_ASCII_WHITESPACE_RUNS_TO_ONE_SPACE_THEN_STRIP",
    "terminal_rejection_substrings": [
        "access denied",
        "are you a robot",
        "attention required",
        "authentication required",
        "captcha",
        "cf-chl-",
        "checking your browser",
        "cloudflare ray id",
        "consent required",
        "enable javascript and cookies",
        "error 403",
        "error 404",
        "error 500",
        "internal server error",
        "just a moment",
        "log in",
        "login required",
        "name=\"password\"",
        "name='password'",
        "robot check",
        "sign in",
        "temporarily unavailable",
        "type=\"password\"",
        "type='password'",
        "verify you are human",
    ],
    "exact_inert_simulator_outcome_diagnostic_field_types": INERT_SIMULATOR_OUTCOME_DIAGNOSTIC_FIELD_TYPES,
    "exact_inert_simulator_outcome_diagnostic_field_count": 36,
    "exact_inert_simulator_outcome_diagnostic_field_types_sha256": INERT_SIMULATOR_OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256,
    "inert_simulator_outcome_roster_match_rule": "EXACT_ORDER_FIELD_NAME_AND_STRICT_TYPE_EQUALITY_NO_ALIAS_OMISSION_OR_EXTRA",
    "future_operational_outcome_schema_admitted": False,
    "all_five_page_detection_booleans_required_false_for_success": True,
    "rejection_substring_matches_required_empty_for_success": True,
    "rejection_substring_matches_type": "LIST_OF_UNIQUE_MEMBERS_OF_TERMINAL_REJECTION_SUBSTRINGS",
    "forbidden_magic_prefix_matches_required_empty_for_success": True,
    "forbidden_magic_prefix_matches_type": "LIST_OF_UNIQUE_MEMBERS_OF_FAILURE_CONTRACT_FORBIDDEN_MAGIC_HEX_PREFIXES",
    "title_classifier_matches_required_empty_for_success": True,
    "title_classifier_allowed_values": [
        "captcha",
        "challenge",
        "denied",
        "error",
        "login",
        "sign in",
    ],
    "title_classifier_matches_type": "LIST_OF_UNIQUE_MEMBERS_OF_TITLE_CLASSIFIER_ALLOWED_VALUES",
    "ambiguous_or_unparseable_header_or_framing_disposition": "TERMINAL_PROTOCOL_VIOLATION_NO_RETRY",
    "ambiguous_or_unparseable_page_or_content_detection_disposition": "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY",
}


EXTRACTION_CONTRACT = {
    "scope": "FUTURE_OFFLINE_EXTRACTION_MINIMUM_NO_CURRENT_EXTRACTION_RECORD",
    "current_extraction_schema_admitted": False,
    "execution_location": "OFFLINE_ALREADY_CUSTODIED_BODY_BYTES_ONLY",
    "network_render_script_link_archive_or_external_parser_permitted": False,
    "required_item_keys": [
        "field_name", "raw_utf8_value", "start_byte_offset",
        "end_byte_offset_exclusive", "body_sha256", "status",
    ],
    "offset_convention": "ZERO_BASED_HALF_OPEN_UTF8_BODY_BYTE_OFFSETS",
    "required_status": "UNVERIFIED_CANDIDATE_NOT_CONTACTED",
    "allowed_semantic_fact_fields": [
        "displayed_source_title",
        "displayed_dataset_identifier",
        "displayed_version_or_revision",
        "displayed_publication_or_update_text",
        "displayed_license_label",
        "license_url_candidate",
        "terms_url_candidate",
        "documentation_url_candidate",
        "archive_url_candidate",
        "displayed_access_prerequisite_text",
        "displayed_governance_or_ethics_text",
        "displayed_retention_or_redistribution_text",
        "displayed_schema_metadata_text",
        "displayed_timezone_metadata_text",
        "displayed_contact_name_candidate",
        "displayed_contact_role_candidate",
        "displayed_contact_email_candidate",
        "displayed_contact_url_candidate",
    ],
    "candidate_urls_are_inert_strings_not_targets": True,
    "contact_tokens_are_inert_strings_not_contact_authority_or_roster_admission": True,
    "promotion_to_verified_official_selected_contacted_approved_or_complete_permitted": False,
    "can_fill_preregistration_observed_slots": False,
}


NULL_OPERATION_SLOT = {
    "durable_intent_path": None,
    "durable_intent_sha256": None,
    "amendment_machine_raw_sha256": None,
    "amendment_record_sha256": None,
    "package_aggregate_sha256": None,
    "runtime_closure_receipt_path": None,
    "runtime_closure_receipt_sha256": None,
    "operational_final_exact_request_sha256": None,
    "independent_go_receipt_sha256": None,
    "fresh_post_review_authority_text_sha256": None,
    "fresh_post_review_authority_receipt_sha256": None,
    "custody_root_absolute_path": None,
    "custody_root_device": None,
    "custody_root_inode": None,
    "custody_root_owner_uid": None,
    "row_directory_basename": None,
    "request_emitted": None,
    "outcome_path": None,
    "outcome_sha256": None,
    "terminal_state": None,
    "raw_request_custody_path": None,
    "raw_request_sha256": None,
    "raw_response_head_custody_path": None,
    "raw_response_head_sha256": None,
    "raw_transfer_body_custody_path": None,
    "raw_transfer_body_sha256": None,
    "decoded_entity_body_custody_path": None,
    "decoded_entity_body_sha256": None,
    "raw_metadata_custody_path": None,
    "raw_metadata_sha256": None,
    "raw_stderr_custody_path": None,
    "raw_stderr_sha256": None,
    "effective_url": None,
    "effective_url_sha256": None,
    "status_code": None,
    "normalized_media_type": None,
    "redirect_count": None,
    "offline_extraction_record_path": None,
    "offline_extraction_record_sha256": None,
    "official_source_verified": None,
    "license_verified": None,
    "source_selected": None,
    "approval_created": None,
}
CURRENT_OBSERVATION_SLOTS = [
    {"ordinal": 0, "operation_id": OPERATION_ROSTER[0]["operation_id"], **NULL_OPERATION_SLOT},
    {"ordinal": 1, "operation_id": OPERATION_ROSTER[1]["operation_id"], **NULL_OPERATION_SLOT},
]


CHECKLIST_EFFECTS = {
    "tracker_snapshot_open_fields": 152,
    "tracker_snapshot_closed_fields": 20,
    "effective_open_blocker_count": 12,
    "result_slots_filled": 0,
    "f172_value": None,
    "original_solo_block2_operational_box_count": 7,
    "original_solo_block2_operational_boxes_open": 7,
    "original_solo_block2_operational_boxes_closed_by_amendment": 0,
    "original_solo_block2_operational_box_states": [
        {"ordinal": 0, "box": "POPULATE_EXACT_FINITE_PRECONTACT_INSTANCE", "state": "OPEN"},
        {"ordinal": 1, "box": "INDEPENDENTLY_REVIEW_AND_ADMIT_PRECONTACT_INSTANCE", "state": "OPEN"},
        {"ordinal": 2, "box": "RECORD_FRESH_EXACT_ADMINISTRATIVE_CONTACT_AUTHORITY", "state": "OPEN"},
        {"ordinal": 3, "box": "OPEN_AUTHORIZED_ADMINISTRATIVE_REQUESTS", "state": "OPEN"},
        {"ordinal": 4, "box": "COMPLETE_AND_BIND_REQUIRED_APPROVAL_RECEIPTS", "state": "OPEN"},
        {"ordinal": 5, "box": "POPULATE_REVIEW_AND_ADMIT_DATA_ACCESS_INSTANCE", "state": "OPEN"},
        {"ordinal": 6, "box": "RECORD_FRESH_DATA_ACCESS_AUTHORITY", "state": "OPEN"},
    ],
    "fields_closed_by_amendment": 0,
    "blockers_closed_by_amendment": 0,
    "formal_tests_closed_by_amendment": 0,
    "results_filled_by_amendment": 0,
    "source_selection_success_created": False,
    "approval_created": False,
    "domain_admission_complete": False,
    "populated_precontact_instance_complete": False,
    "independent_precontact_instance_admission_complete": False,
    "administrative_contact_authority_recorded": False,
    "administrative_contact_opened": False,
    "approval_receipts_complete": False,
    "data_access_instance_admitted": False,
    "data_access_authority_recorded": False,
    "scientific_delta": 0,
    "tracker_edit_performed": False,
    "exact_runtime_admitted": False,
    "fetch_eligible": False,
}


EXACT_TOP_LEVEL_KEYS = {
    "authority_provenance",
    "binding_policy",
    "checklist_effects",
    "current_observation_slots",
    "durable_custody_contract",
    "extraction_contract",
    "failure_contract",
    "historical_snapshot_inputs",
    "live_immutable_input_bindings",
    "narrow_supersession_contract",
    "operation_roster",
    "package_bindings",
    "package_digest_contract",
    "package_kind",
    "page_rejection_contract",
    "record_sha256",
    "reported_date",
    "request_environment_contract",
    "review_and_authority_contract",
    "runtime_admission_contract",
    "schema_version",
    "scope_review",
    "state",
    "global_sequence_contract",
}


def expected_record(package_bindings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return the exact semantic record with only its self-digest unfilled."""

    return copy.deepcopy(
        {
            "authority_provenance": AUTHORITY_PROVENANCE,
            "binding_policy": BINDING_POLICY,
            "checklist_effects": CHECKLIST_EFFECTS,
            "current_observation_slots": CURRENT_OBSERVATION_SLOTS,
            "durable_custody_contract": DURABLE_CUSTODY_CONTRACT,
            "extraction_contract": EXTRACTION_CONTRACT,
            "failure_contract": FAILURE_CONTRACT,
            "global_sequence_contract": GLOBAL_SEQUENCE_CONTRACT,
            "historical_snapshot_inputs": HISTORICAL_SNAPSHOT_INPUTS,
            "live_immutable_input_bindings": LIVE_IMMUTABLE_INPUT_BINDINGS,
            "narrow_supersession_contract": NARROW_SUPERSESSION_CONTRACT,
            "operation_roster": OPERATION_ROSTER,
            "package_bindings": list(package_bindings),
            "package_digest_contract": PACKAGE_DIGEST_CONTRACT,
            "package_kind": PACKAGE_KIND,
            "page_rejection_contract": PAGE_REJECTION_CONTRACT,
            "record_sha256": None,
            "reported_date": REPORTED_DATE,
            "request_environment_contract": REQUEST_ENVIRONMENT_CONTRACT,
            "review_and_authority_contract": REVIEW_AND_AUTHORITY_CONTRACT,
            "runtime_admission_contract": RUNTIME_ADMISSION_CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "scope_review": SCOPE_REVIEW,
            "state": STATE,
        }
    )


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def semantic_self_digest(value: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(value))
    clone["record_sha256"] = None
    return hashlib.sha256(canonical_bytes(clone)).hexdigest()


def _object_no_duplicates(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_equal(actual: Any, expected: Any, path: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(
            f"{path}: type {type(actual).__name__} != {type(expected).__name__}"
        )
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            missing = sorted(set(expected) - set(actual))
            extra = sorted(set(actual) - set(expected))
            raise ValidationError(f"{path}: key mismatch missing={missing} extra={extra}")
        for key in expected:
            _strict_equal(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValidationError(f"{path}: list length {len(actual)} != {len(expected)}")
        for index, (got, want) in enumerate(zip(actual, expected)):
            _strict_equal(got, want, f"{path}[{index}]")
    elif actual != expected:
        raise ValidationError(f"{path}: {actual!r} != {expected!r}")


def _rooted_path(root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or not relative_path.parts:
        raise ValidationError(f"non-relative package path: {relative}")
    if any(part in {"", ".", ".."} for part in relative_path.parts):
        raise ValidationError(f"unsafe package path component: {relative}")
    candidate = root
    for part in relative_path.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValidationError(f"symlink component forbidden: {relative}")
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (FileNotFoundError, ValueError) as exc:
        raise ValidationError(f"missing or escaped path: {relative}") from exc
    return candidate


def _check_file_receipt(root: Path, receipt: Mapping[str, Any]) -> None:
    path = _rooted_path(root, receipt["path"])
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValidationError(f"not regular: {receipt['path']}")
    if stat.S_IMODE(info.st_mode) != int(receipt["mode_octal"], 8):
        raise ValidationError(f"mode mismatch: {receipt['path']}")
    if info.st_nlink != receipt["nlink"]:
        raise ValidationError(f"link-count mismatch: {receipt['path']}")
    raw = path.read_bytes()
    if len(raw) != receipt["bytes"]:
        raise ValidationError(f"byte-count mismatch: {receipt['path']}")
    if hashlib.sha256(raw).hexdigest() != receipt["raw_sha256"]:
        raise ValidationError(f"raw digest mismatch: {receipt['path']}")
    if receipt["trailing_lf"] is not True or not raw.endswith(b"\n"):
        raise ValidationError(f"terminal LF mismatch: {receipt['path']}")
    if b"\r" in raw:
        raise ValidationError(f"CR byte forbidden: {receipt['path']}")
    expected_self = receipt.get("record_sha256")
    if expected_self is not None:
        try:
            parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_no_duplicates)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"bound JSON invalid: {receipt['path']}") from exc
        if parsed.get("record_sha256") != expected_self:
            raise ValidationError(f"bound semantic digest mismatch: {receipt['path']}")


def _validate_package_bindings(root: Path, bindings: Any) -> None:
    expected_shape = [
        {"ordinal": 0, "path": HUMAN_PATH, "role": "HUMAN_AMENDMENT"},
        {"ordinal": 1, "path": VALIDATOR_PATH, "role": "READ_ONLY_VALIDATOR"},
        {"ordinal": 2, "path": TEST_PATH, "role": "AMENDMENT_HOSTILE_TEST"},
        {"ordinal": 3, "path": SIMULATOR_PATH, "role": "DORMANT_TRANSCRIPT_SIMULATOR"},
        {"ordinal": 4, "path": SIMULATOR_TEST_PATH, "role": "TRANSCRIPT_SIMULATOR_HOSTILE_TEST"},
    ]
    if type(bindings) is not list or len(bindings) != 5:
        raise ValidationError("package_bindings: exact five-receipt six-file roster required")
    for index, (receipt, skeleton) in enumerate(zip(bindings, expected_shape)):
        if type(receipt) is not dict:
            raise ValidationError(f"package_bindings[{index}]: object required")
        expected_keys = {
            "ordinal", "path", "role", "bytes", "raw_sha256",
            "mode_octal", "nlink", "trailing_lf",
        }
        if set(receipt) != expected_keys:
            raise ValidationError(f"package_bindings[{index}]: exact keys required")
        for key, value in skeleton.items():
            _strict_equal(receipt[key], value, f"package_bindings[{index}].{key}")
        if type(receipt["bytes"]) is not int or receipt["bytes"] <= 0:
            raise ValidationError(f"package_bindings[{index}].bytes invalid")
        if type(receipt["raw_sha256"]) is not str or not HEX64.fullmatch(receipt["raw_sha256"]):
            raise ValidationError(f"package_bindings[{index}].raw_sha256 invalid")
        _strict_equal(receipt["mode_octal"], "0644", f"package_bindings[{index}].mode_octal")
        _strict_equal(receipt["nlink"], 1, f"package_bindings[{index}].nlink")
        _strict_equal(receipt["trailing_lf"], True, f"package_bindings[{index}].trailing_lf")
        _check_file_receipt(root, receipt)


class _SourceSafetyVisitor(ast.NodeVisitor):
    BANNED_IMPORT_ROOTS = {
        "socket", "ssl", "urllib", "http", "requests", "httpx", "aiohttp",
        "ftplib", "subprocess", "multiprocessing", "asyncio", "secrets",
        "random", "webbrowser", "selenium", "playwright", "paramiko", "ctypes",
    }
    BANNED_CALL_NAMES = {
        "open", "urlopen", "request", "post", "put", "head",
        "connect", "socket", "system", "popen", "fork", "spawn", "run",
        "call", "check_call", "check_output", "eval", "exec",
        "__import__", "input", "callable",
    }
    BANNED_ATTRIBUTES = {
        "write_text", "write_bytes", "touch", "mkdir", "unlink", "rename",
        "rmdir", "chmod", "symlink_to", "hardlink_to", "truncate",
        "send", "sendall", "recv", "recvfrom", "download", "fetch",
    }

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for item in node.names:
            if item.name.split(".", 1)[0] in self.BANNED_IMPORT_ROOTS:
                self.errors.append(f"banned import {item.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module and node.module.split(".", 1)[0] in self.BANNED_IMPORT_ROOTS:
            self.errors.append(f"banned import {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name) and node.func.id == "compile":
            self.errors.append("banned call compile")
        if isinstance(node.func, ast.Name) and node.func.id in self.BANNED_CALL_NAMES:
            self.errors.append(f"banned call {node.func.id}")
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            self.BANNED_CALL_NAMES | self.BANNED_ATTRIBUTES
        ):
            self.errors.append(f"banned call attribute {node.func.attr}")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if node.id in {"Callable", "Protocol"}:
            self.errors.append(f"banned callable transport surface {node.id}")
        self.generic_visit(node)


class _SimulatorSafetyVisitor(_SourceSafetyVisitor):
    ALLOWED_IMPORT_ROOTS = {
        "__future__", "copy", "datetime", "hashlib", "json", "re",
        "dataclasses", "typing",
    }
    BANNED_IMPORT_ROOTS = _SourceSafetyVisitor.BANNED_IMPORT_ROOTS | {
        "os", "pathlib", "tempfile", "shutil",
    }
    BANNED_PARAMETER_TOKENS = {
        "callable", "callback", "connector", "fetcher", "opener", "resolver",
        "sender", "socket", "transport", "writer",
    }
    BANNED_DEFINITION_TOKENS = {
        "connect", "execute", "fetch", "mkdir", "open", "recv", "resolve",
        "send", "socket", "write",
    }
    BANNED_ATTRIBUTES = _SourceSafetyVisitor.BANNED_ATTRIBUTES | {
        "now", "utcnow", "today",
    }

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for item in node.names:
            root = item.name.split(".", 1)[0]
            if root not in self.ALLOWED_IMPORT_ROOTS:
                self.errors.append(f"non-allowlisted simulator import {item.name}")
        super().visit_Import(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module:
            root = node.module.split(".", 1)[0]
            if root not in self.ALLOWED_IMPORT_ROOTS:
                self.errors.append(f"non-allowlisted simulator import {node.module}")
        super().visit_ImportFrom(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        lowered_name = node.name.casefold()
        if any(token in lowered_name for token in self.BANNED_DEFINITION_TOKENS):
            self.errors.append(f"banned simulator definition {node.name}")
        arguments = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
        if node.args.vararg is not None:
            arguments.append(node.args.vararg)
        if node.args.kwarg is not None:
            arguments.append(node.args.kwarg)
        for argument in arguments:
            lowered = argument.arg.casefold()
            if any(token in lowered for token in self.BANNED_PARAMETER_TOKENS):
                self.errors.append(f"banned simulator parameter {argument.arg}")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._check_function(node)
        self.generic_visit(node)


class _HostileTestSafetyVisitor(ast.NodeVisitor):
    BANNED_IMPORT_ROOTS = {
        "_socket", "_ssl", "aiohttp", "asyncio", "ctypes", "ftplib",
        "http", "httpx", "multiprocessing", "paramiko", "playwright",
        "random", "requests", "secrets", "selenium", "socket", "ssl",
        "subprocess", "urllib", "webbrowser",
    }
    BANNED_CALL_NAMES = {
        "__import__", "call", "check_call", "check_output", "compile",
        "connect", "eval", "exec", "fork", "getaddrinfo", "popen", "recv",
        "recvfrom", "run", "send", "sendall", "socket", "spawn", "system",
        "urlopen",
    }

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for item in node.names:
            if item.name.split(".", 1)[0] in self.BANNED_IMPORT_ROOTS:
                self.errors.append(f"banned test import {item.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module and node.module.split(".", 1)[0] in self.BANNED_IMPORT_ROOTS:
            self.errors.append(f"banned test import {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name) and node.func.id in self.BANNED_CALL_NAMES:
            self.errors.append(f"banned test call {node.func.id}")
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in self.BANNED_CALL_NAMES
        ):
            self.errors.append(f"banned test call attribute {node.func.attr}")
        self.generic_visit(node)


def _validate_source_safety(root: Path) -> None:
    for relative, label, visitor_type in [
        (VALIDATOR_PATH, "validator", _SourceSafetyVisitor),
        (SIMULATOR_PATH, "transcript simulator", _SimulatorSafetyVisitor),
    ]:
        source = _rooted_path(root, relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        visitor = visitor_type()
        visitor.visit(tree)
        if visitor.errors:
            raise ValidationError(
                f"{label} source safety: " + "; ".join(visitor.errors)
            )
    for relative, label in [
        (TEST_PATH, "amendment hostile test"),
        (SIMULATOR_TEST_PATH, "transcript simulator hostile test"),
    ]:
        source = _rooted_path(root, relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        visitor = _HostileTestSafetyVisitor()
        visitor.visit(tree)
        if visitor.errors:
            raise ValidationError(
                f"{label} source safety: " + "; ".join(visitor.errors)
            )


def _validate_simulator_outcome_diagnostic_roster(root: Path) -> None:
    """Bind the simulator's public literal roster without executing its source."""

    relative = SIMULATOR_PATH
    source = _rooted_path(root, relative).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=relative)
    assignments: list[Any] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name)
            and target.id == "OUTCOME_DIAGNOSTIC_FIELD_TYPES"
            for target in node.targets
        ):
            try:
                assignments.append(ast.literal_eval(node.value))
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    "simulator diagnostic roster must be one exact literal"
                ) from exc
    if len(assignments) != 1:
        raise ValidationError("simulator diagnostic roster assignment count must be one")
    actual = assignments[0]
    expected = tuple(
        (item["field"], item["exact_type"])
        for item in INERT_SIMULATOR_OUTCOME_DIAGNOSTIC_FIELD_TYPES
    )
    if (
        type(actual) is not tuple
        or any(
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
            for item in actual
        )
        or actual != expected
    ):
        raise ValidationError(
            "simulator outcome diagnostic roster differs by order, field, type, alias, omission, or extra"
        )
    digest = hashlib.sha256(
        json.dumps(
            INERT_SIMULATOR_OUTCOME_DIAGNOSTIC_FIELD_TYPES,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if digest != INERT_SIMULATOR_OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256:
        raise ValidationError("simulator outcome diagnostic roster digest mismatch")


def _assert_all_observed_slots_null(slots: Any) -> None:
    _strict_equal(slots, CURRENT_OBSERVATION_SLOTS, "current_observation_slots")
    for index, slot in enumerate(slots):
        for key, value in slot.items():
            if key not in {"ordinal", "operation_id"} and value is not None:
                raise ValidationError(f"current_observation_slots[{index}].{key}: null required")


def _validate_semantics(record: Mapping[str, Any]) -> None:
    _strict_equal(record["schema_version"], SCHEMA_VERSION, "schema_version")
    _strict_equal(record["package_kind"], PACKAGE_KIND, "package_kind")
    _strict_equal(record["state"], STATE, "state")
    _strict_equal(record["reported_date"], REPORTED_DATE, "reported_date")
    for key, expected in [
        ("authority_provenance", AUTHORITY_PROVENANCE),
        ("binding_policy", BINDING_POLICY),
        ("narrow_supersession_contract", NARROW_SUPERSESSION_CONTRACT),
        ("package_digest_contract", PACKAGE_DIGEST_CONTRACT),
        ("global_sequence_contract", GLOBAL_SEQUENCE_CONTRACT),
        ("review_and_authority_contract", REVIEW_AND_AUTHORITY_CONTRACT),
        ("runtime_admission_contract", RUNTIME_ADMISSION_CONTRACT),
        ("scope_review", SCOPE_REVIEW),
        ("live_immutable_input_bindings", LIVE_IMMUTABLE_INPUT_BINDINGS),
        ("historical_snapshot_inputs", HISTORICAL_SNAPSHOT_INPUTS),
        ("operation_roster", OPERATION_ROSTER),
        ("request_environment_contract", REQUEST_ENVIRONMENT_CONTRACT),
        ("durable_custody_contract", DURABLE_CUSTODY_CONTRACT),
        ("failure_contract", FAILURE_CONTRACT),
        ("page_rejection_contract", PAGE_REJECTION_CONTRACT),
        ("extraction_contract", EXTRACTION_CONTRACT),
        ("checklist_effects", CHECKLIST_EFFECTS),
    ]:
        _strict_equal(record[key], expected, key)
    _assert_all_observed_slots_null(record["current_observation_slots"])

    roster = record["operation_roster"]
    if [row["ordinal"] for row in roster] != [0, 1]:
        raise ValidationError("operation ordinals must be exactly [0, 1]")
    if len({row["url"] for row in roster}) != 2:
        raise ValidationError("exactly two distinct URLs required")
    if any(row["inert_request_design"]["max_retries"] != 0 for row in roster):
        raise ValidationError("retry must remain zero")
    if any(row["inert_request_design"]["max_redirects"] != 0 for row in roster):
        raise ValidationError("redirect limit must remain zero")
    if any(row["operational_final_exact_request_sha256"] is not None for row in roster):
        raise ValidationError("operational request digests must remain null")
    if any(row["request_design_is_executable"] is not False for row in roster):
        raise ValidationError("inert request designs must remain non-executable")
    if any(row["request_emission_code_present_in_package"] is not False for row in roster):
        raise ValidationError("request emission code must remain absent")
    for index, row in enumerate(roster):
        design = row["inert_request_design"]
        raw_design = design["raw_request_ascii"].encode("ascii")
        if b"\r\n" not in raw_design or b"\\r\\n" in raw_design:
            raise ValidationError(f"operation_roster[{index}]: exact CRLF bytes required")
        if not raw_design.endswith(b"\r\n\r\n"):
            raise ValidationError(f"operation_roster[{index}]: terminal CRLF pair required")
        if len(raw_design) != design["raw_request_bytes"]:
            raise ValidationError(f"operation_roster[{index}]: design byte count mismatch")
        if hashlib.sha256(raw_design).hexdigest() != design["raw_request_sha256"]:
            raise ValidationError(f"operation_roster[{index}]: design digest mismatch")
    if record["authority_provenance"]["fetch_execution_authorized_now"] is not False:
        raise ValidationError("fetch execution must remain unauthorized")
    if record["runtime_admission_contract"]["exact_runtime_admitted"] is not False:
        raise ValidationError("exact runtime must remain unadmitted")
    if record["runtime_admission_contract"]["fetch_eligible"] is not False:
        raise ValidationError("fetch must remain ineligible")
    if record["checklist_effects"]["scientific_delta"] != 0:
        raise ValidationError("scientific delta must remain zero")
    if record["checklist_effects"]["original_solo_block2_operational_boxes_open"] != 7:
        raise ValidationError("all seven original Solo Block 2 boxes must remain open")


def validate(root: Path | None = None, machine_path: Path | None = None) -> dict[str, Any]:
    repo = (root if root is not None else Path(__file__).resolve().parents[2]).resolve()
    target = machine_path if machine_path is not None else repo / MACHINE_PATH
    raw = target.read_bytes()
    try:
        record = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("machine record is not unique-key UTF-8 JSON") from exc
    if type(record) is not dict:
        raise ValidationError("machine record root must be an object")
    if set(record) != EXACT_TOP_LEVEL_KEYS:
        missing = sorted(EXACT_TOP_LEVEL_KEYS - set(record))
        extra = sorted(set(record) - EXACT_TOP_LEVEL_KEYS)
        raise ValidationError(f"top-level key mismatch missing={missing} extra={extra}")
    if raw != canonical_bytes(record):
        raise ValidationError("machine record is not exact canonical JSON plus LF")
    digest = record["record_sha256"]
    if type(digest) is not str or not HEX64.fullmatch(digest):
        raise ValidationError("record_sha256 must be lowercase hex64")
    if digest != semantic_self_digest(record):
        raise ValidationError("record_sha256 mismatch")
    _validate_semantics(record)
    _validate_package_bindings(repo, record["package_bindings"])
    for receipt in record["live_immutable_input_bindings"]:
        _check_file_receipt(repo, receipt)
    _validate_source_safety(repo)
    _validate_simulator_outcome_diagnostic_roster(repo)
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "operation_count": 2,
        "fetches_performed": 0,
        "durable_intents_created": 0,
        "open_solo_block2_operational_boxes": 7,
        "open_fields": 152,
        "closed_fields": 20,
        "scientific_delta": 0,
        "record_sha256": digest,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--machine", type=Path, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = validate(args.root, args.machine)
    except (OSError, ValidationError) as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
