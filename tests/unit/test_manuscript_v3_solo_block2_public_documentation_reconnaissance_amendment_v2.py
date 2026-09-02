"""Hostile qualification for the Solo Block 2 reconnaissance amendment v2."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT
    / "research/diagnostics/"
    "manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py"
)
MACHINE = (
    ROOT
    / "research/fixtures/"
    "manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.json"
)
SPEC = importlib.util.spec_from_file_location("sb2_recon_v2_validator", VALIDATOR)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
SIMULATOR_SOURCE = (
    ROOT
    / "src/heterodiff/artifacts/"
    "solo_block2_public_documentation_reconnaissance_executor_v2.py"
)
SIMULATOR_SPEC = importlib.util.spec_from_file_location(
    "sb2_recon_v2_inert_simulator", SIMULATOR_SOURCE
)
assert SIMULATOR_SPEC is not None and SIMULATOR_SPEC.loader is not None
simulator = importlib.util.module_from_spec(SIMULATOR_SPEC)
sys.modules[SIMULATOR_SPEC.name] = simulator
SIMULATOR_SPEC.loader.exec_module(simulator)


def _load() -> dict[str, Any]:
    value = json.loads(MACHINE.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _set_path(value: Any, dotted: str, replacement: Any) -> None:
    parts = dotted.split(".")
    cursor = value
    for part in parts[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    final = parts[-1]
    if isinstance(cursor, list):
        cursor[int(final)] = replacement
    else:
        cursor[final] = replacement


def _write_canonical(tmp_path: Path, value: dict[str, Any]) -> Path:
    value["record_sha256"] = validator.semantic_self_digest(value)
    path = tmp_path / "candidate.json"
    path.write_bytes(validator.canonical_bytes(value))
    return path


def _must_hold(tmp_path: Path, value: dict[str, Any]) -> None:
    candidate = _write_canonical(tmp_path, value)
    with pytest.raises(validator.ValidationError):
        validator.validate(ROOT, candidate)


def _simulated_success_outcome() -> dict[str, Any]:
    body = (
        b"<!doctype html><html><title>Official root</title>"
        b"<body>public documentation</body></html>"
    )
    head = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    ).encode("ascii")
    operation = simulator.operation_spec(0)
    transcript = simulator.InertTranscript(
        intent_utc="2030-01-01T00:00:05Z",
        started_utc="2030-01-01T00:00:06Z",
        finished_utc="2030-01-01T00:00:07Z",
        simulated_resolver_host=operation["host"],
        simulated_resolver_port=443,
        simulated_resolver_results=("192.0.2.10:443", "[2001:db8::10]:443"),
        simulated_selected_address="192.0.2.10:443",
        simulated_socket_instance_count=1,
        simulated_connect_attempt_count=1,
        simulated_tls_wrap_count=1,
        simulated_send_attempt_count=1,
        simulated_emitted_request_bytes=simulator.exact_request_bytes(0),
        supplied_tls_version="TLSv1.3",
        supplied_alpn="http/1.1",
        supplied_cipher_name="TLS_AES_256_GCM_SHA384",
        supplied_cipher_protocol="TLSv1.3",
        supplied_cipher_bits=256,
        supplied_peer_certificate_bytes=b"inert-supplied-der-certificate",
        response_chunks=(head + body, b""),
        injected_failure_stage=None,
    )
    return simulator.qualify_row_from_inert_transcript(0, transcript=transcript)


def test_owner_record_passes_and_is_zero_effect() -> None:
    result = validator.validate(ROOT, MACHINE)
    assert result["status"] == "PASS"
    assert result["operation_count"] == 2
    assert result["fetches_performed"] == 0
    assert result["durable_intents_created"] == 0
    assert result["open_solo_block2_operational_boxes"] == 7
    assert result["open_fields"] == 152
    assert result["closed_fields"] == 20
    assert result["scientific_delta"] == 0


def test_record_is_unique_key_canonical_self_digested_json() -> None:
    raw = MACHINE.read_bytes()
    record = _load()
    assert raw == validator.canonical_bytes(record)
    assert record["record_sha256"] == validator.semantic_self_digest(record)
    assert raw.endswith(b"\n") and b"\r" not in raw
    expected = validator.expected_record(record["package_bindings"])
    expected["record_sha256"] = validator.semantic_self_digest(expected)
    assert record == expected


def test_authority_is_exact_and_fetch_is_hold() -> None:
    authority = _load()["authority_provenance"]
    text = "Sounds good, go through those deferred items in Solo Block 2."
    assert authority["normalized_visible_text"] == text
    assert len(text.encode("utf-8")) == 61
    assert authority["normalized_visible_text_sha256"] == (
        "80bfdee90ba72bfb1de81058945001cbe5aca1931491636b474d419d93c08c6f"
    )
    assert authority["fetch_execution_authorized_now"] is False
    assert authority["exact_runtime_admitted"] is False
    assert authority["fetch_eligible"] is False
    assert authority["administrative_message_email_ticket_or_form_authorized"] is False
    assert authority["data_access_authorized"] is False


def test_two_rows_exact_urls_order_and_nonexecutable_templates() -> None:
    rows = _load()["operation_roster"]
    assert [row["ordinal"] for row in rows] == [0, 1]
    assert [row["url"] for row in rows] == [
        "https://physionet.org/content/challenge-2012/1.0.0/",
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
    ]
    assert rows[0]["sequence_prerequisite"] is None
    assert rows[1]["sequence_prerequisite"]["prior_ordinal"] == 0
    for row in rows:
        design = row["inert_request_design"]
        assert design["method"] == "GET"
        assert design["max_attempts"] == 1
        assert design["max_retries"] == 0
        assert design["max_redirects"] == 0
        assert row["request_design_is_executable"] is False
        assert row["request_emission_code_present_in_package"] is False
        assert row["operational_final_exact_request_sha256"] is None
        assert validator.HEX64.fullmatch(design["raw_request_sha256"])
        raw_design = design["raw_request_ascii"].encode("ascii")
        assert b"\r\n" in raw_design
        assert b"\\r\\n" not in raw_design
        assert raw_design.endswith(b"\r\n\r\n")


def test_all_operational_observation_slots_are_null() -> None:
    slots = _load()["current_observation_slots"]
    assert len(slots) == 2
    for slot in slots:
        for key, value in slot.items():
            if key not in {"ordinal", "operation_id"}:
                assert value is None


def test_narrow_supersession_is_explicit_and_no_fallback() -> None:
    contract = _load()["narrow_supersession_contract"]
    paths = {item["path"]: item for item in contract["exact_predecessor_predicates"]}
    assert paths["candidate_selectors.reconnaissance_or_target_amendment_permitted"]["predecessor_value"] is False
    assert paths["gap_inventory.target_mismatch_permits_amendment_or_reconnaissance"]["v2_effect"] == "UNCHANGED_FALSE"
    assert contract["third_target_mirror_fallback_child_search_or_post_failure_amendment_created"] is False


def test_row_one_is_preempted_on_any_row_zero_nonsuccess() -> None:
    sequence = _load()["global_sequence_contract"]
    assert sequence["row1_requires_row0_terminal_state"] == "TERMINAL_ROOT_PAGE_OBSERVED_UNVERIFIED_NO_RETRY"
    assert sequence["row0_any_non_success_or_missing_durable_outcome_preempts_row1"] is True
    assert sequence["row1_preempted_state"] == "TERMINAL_PREEMPTED_BY_ROW0_NO_REQUEST_NO_INTENT"
    assert sequence["row0_success_alone_authorizes_row1"] is False


def test_operational_go_and_authority_are_deliberately_unpopulated() -> None:
    contract = _load()["review_and_authority_contract"]
    assert contract["transcript_simulation_results_scope"] == "TRANSCRIPT_SIMULATION_ONLY_NONOPERATIONAL"
    assert contract["transcript_simulation_results_can_create_operational_go_authority_intent_or_outcome"] is False
    assert contract["operational_independent_go_schema_version"] is None
    assert contract["operational_fresh_authority_schema_version"] is None
    assert contract["operational_exact_affirmative_authority_template"] is None
    assert contract["current_user_text_can_promote_simulation_result_or_fill_operational_schema"] is False
    assert contract["later_runtime_closure_must_freeze_exact_operational_go_and_authority_schemas"] is True
    assert contract["later_authority_must_use_exact_rendered_affirmative_equality_not_token_presence"] is True


def test_digest_derivations_are_noncircular_and_unambiguous() -> None:
    contract = _load()["package_digest_contract"]
    assert contract["machine_cannot_embed_its_own_raw_digest_without_cycle"] is True
    assert contract["machine_raw_digest_or_package_aggregate_embedded_here"] is False
    assert contract["independent_package_review_must_compute_and_bind_both"] is True
    assert contract["term_final_v2_package_digest_is_ambiguous_and_forbidden"] is True


def test_runtime_is_explicitly_dormant_and_ineligible() -> None:
    runtime = _load()["runtime_admission_contract"]
    assert runtime["decision"] == "DORMANT_DESIGN_AND_PURE_TRANSCRIPT_SIMULATION_ONLY"
    assert runtime["exact_runtime_admitted"] is False
    assert runtime["fetch_eligible"] is False
    assert runtime["production_network_entrypoint_present"] is False
    assert runtime["resolver_socket_tls_connect_send_or_receive_code_present"] is False
    assert runtime["caller_injected_transport_callable_present"] is False
    assert runtime["canonical_or_operational_write_path_present"] is False
    semantic = runtime["bound_inert_simulator_semantics"]
    assert semantic == {
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
    }
    assert runtime["simulator_input_scope"] == (
        "EXACT_FROZEN_TRANSCRIPT_VALUE_OBJECT_AND_VALIDATED_BUILTIN_PRIOR_MODEL_ONLY"
    )
    assert runtime["simulator_input_roster"]["callable_path_fd_client_or_general_object_permitted"] is False
    assert runtime["simulator_input_roster"]["prior_outcome_self_digest_alone_is_authentication"] is False
    assert runtime["separate_independently_reviewed_runtime_closure_amendment_required"] is True
    assert runtime["runtime_closure_receipt_path"] is None
    assert runtime["runtime_closure_receipt_sha256"] is None
    assert _load()["scope_review"]["independent_review_complete"] is True


def test_operational_runtime_request_and_record_schemas_are_strict_null() -> None:
    record = _load()
    environment = record["request_environment_contract"]
    assert environment["scope"] == "INERT_REQUEST_DESIGN_ONLY_NO_OPERATIONAL_RUNTIME_OR_REQUEST_DIGEST"
    assert environment["client_executable_path"] is None
    assert environment["ca_bundle_path"] is None
    assert environment["environment_manifest_sha256"] is None
    assert environment["operational_final_exact_request_sha256_by_row"] == [None, None]
    boundary = record["durable_custody_contract"]["future_operational_schema_boundary"]
    assert all(
        value is None
        for key, value in boundary.items()
        if key.startswith("operational_")
    )
    assert boundary["this_package_can_materialize_operational_record"] is False


def test_raw_custody_is_exclusive_fsynced_and_capped() -> None:
    custody = _load()["durable_custody_contract"]
    assert custody["custody_invariants_are_modeled_only"] is True
    assert custody["operational_custody_qualified"] is False
    assert custody["transcript_simulator_filesystem_side_effects_present"] is False
    assert custody["raw_sidecar_create_flags"] == ["O_WRONLY", "O_CREAT", "O_EXCL", "O_NOFOLLOW"]
    assert custody["mode_octal"] == "0600"
    assert custody["all_raw_sidecars_exclusively_created_and_empty_fsynced_before_request"] is True
    assert custody["all_raw_sidecars_written_only_through_preopened_fds_or_noninjectable_internal_sinks"] is True
    assert custody["client_reopen_truncate_or_path_based_overwrite_permitted"] is False
    assert custody["every_raw_sidecar_fsync_required_before_outcome"] is True
    assert custody["per_sidecar_caps"]["raw_response_head"] == 139264
    assert custody["per_sidecar_caps"]["raw_transfer_body"] == 2097152
    assert custody["modeled_preoutcome_artifact_role_order"] == [
        "intent",
        "raw_request",
        "raw_response_head",
        "raw_transfer_body",
        "raw_metadata",
        "raw_stderr",
        "decoded_entity_body",
    ]
    assert custody["containing_modeled_outcome_can_self_receipt_or_self_hash"] is False
    assert custody["future_durable_outcome_append_and_link_unimplemented_unqualified"] is True


def test_success_rejects_attachment_duplicate_type_and_challenge_pages() -> None:
    record = _load()
    success = record["failure_contract"]["success_requires"]
    rejection = record["page_rejection_contract"]
    assert success["content_type_header_count"] == 1
    assert success["content_disposition_header_count"] == 0
    assert success["location_header_count"] == 0
    assert success["content_encoding_valid_absent_or_single_identity"] is True
    assert success["transfer_encoding_valid_absent_or_single_chunked"] is True
    assert success["decoded_entity_body_receipt_complete"] is True
    assert rejection["any_content_disposition_including_inline_or_attachment_is_terminal"] is True
    assert rejection["semantic_scan_input"] == "COMPLETE_UTF8_DECODED_ENTITY_BODY_NOT_RAW_CHUNK_STREAM"
    assert rejection["global_terminal_precedence"] == (
        "COMPLETE_PROTOCOL_AND_FRAMING_VALIDATION_OF_ALL_SUPPLIED_BYTES_"
        "BEFORE_SCOPE_STATUS_OR_CONTENT_CLASSIFICATION"
    )
    assert rejection[
        "connection_close_requires_exactly_one_final_inert_eof_event"
    ] is True
    assert rejection["body_truncated_semantics"] == (
        "TRUE_IFF_SUPPLIED_BODY_OR_DECODED_ENTITY_BYTES_WERE_NOT_FULLY_"
        "RETAINED_DUE_TO_A_FROZEN_BYTE_CEILING"
    )
    assert rejection["body_utf8_valid_semantics"] == (
        "TRUE_AFTER_SUCCESSFUL_UTF8_DECODE_EVEN_IF_A_LATER_SCOPE_STATUS_"
        "OR_CONTENT_CLASSIFIER_REJECTS"
    )
    assert rejection["content_encoding_header_count_allowed"] == [0, 1]
    assert rejection["transfer_encoding_header_count_allowed"] == [0, 1]
    assert rejection["rejection_substring_matches_type"] == "LIST_OF_UNIQUE_MEMBERS_OF_TERMINAL_REJECTION_SUBSTRINGS"
    assert rejection["forbidden_magic_prefix_matches_type"] == (
        "LIST_OF_UNIQUE_MEMBERS_OF_FAILURE_CONTRACT_FORBIDDEN_MAGIC_HEX_PREFIXES"
    )
    assert rejection["title_classifier_matches_type"] == (
        "LIST_OF_UNIQUE_MEMBERS_OF_TITLE_CLASSIFIER_ALLOWED_VALUES"
    )
    assert rejection["all_five_page_detection_booleans_required_false_for_success"] is True
    assert "verify you are human" in rejection["terminal_rejection_substrings"]
    assert rejection["ambiguous_or_unparseable_header_or_framing_disposition"] == (
        "TERMINAL_PROTOCOL_VIOLATION_NO_RETRY"
    )
    assert rejection["ambiguous_or_unparseable_page_or_content_detection_disposition"] == (
        "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"
    )


def test_machine_diagnostic_roster_exactly_matches_emitted_simulator_subset() -> None:
    record = _load()
    rejection = record["page_rejection_contract"]
    machine_roster = rejection[
        "exact_inert_simulator_outcome_diagnostic_field_types"
    ]
    exported_roster = [
        {"field": field, "exact_type": exact_type}
        for field, exact_type in simulator.OUTCOME_DIAGNOSTIC_FIELD_TYPES
    ]
    response_predicates = simulator.executor_contract()["response_predicates"]
    assert rejection["global_terminal_precedence"] == response_predicates[
        "global_terminal_precedence"
    ]
    assert rejection[
        "connection_close_requires_exactly_one_final_inert_eof_event"
    ] == response_predicates[
        "connection_close_requires_exactly_one_final_inert_eof_event"
    ]
    assert rejection["body_truncated_semantics"] == response_predicates[
        "body_truncated_semantics"
    ]
    assert rejection["body_utf8_valid_semantics"] == response_predicates[
        "body_utf8_valid_semantics"
    ]
    assert machine_roster == exported_roster
    assert rejection["exact_inert_simulator_outcome_diagnostic_field_count"] == 36
    digest = hashlib.sha256(
        json.dumps(
            exported_roster,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert digest == simulator.OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
    assert digest == rejection[
        "exact_inert_simulator_outcome_diagnostic_field_types_sha256"
    ]
    assert digest == record["runtime_admission_contract"][
        "bound_inert_simulator_semantics"
    ]["outcome_diagnostic_field_types_sha256"]
    outcome = _simulated_success_outcome()
    fields = [item["field"] for item in machine_roster]
    assert fields == [field for field, _exact_type in simulator.OUTCOME_DIAGNOSTIC_FIELD_TYPES]
    assert set(fields) == simulator.OUTCOME_DIAGNOSTIC_FIELDS
    assert set(outcome) & simulator.OUTCOME_DIAGNOSTIC_FIELDS == set(fields)
    assert all(field in outcome for field in fields)
    assert {
        "content_type_count",
        "content_encoding_count",
        "content_encoding_raw",
        "content_encoding_normalized",
        "transfer_encoding_count",
        "transfer_encoding_raw",
        "transfer_encoding_normalized",
        "content_disposition_count",
        "challenge_detected",
        "login_detected",
        "consent_detected",
        "robot_detected",
    }.isdisjoint(outcome)


def test_extraction_is_offline_offset_bound_inert_and_contact_capable() -> None:
    extraction = _load()["extraction_contract"]
    assert extraction["required_status"] == "UNVERIFIED_CANDIDATE_NOT_CONTACTED"
    assert extraction["offset_convention"] == "ZERO_BASED_HALF_OPEN_UTF8_BODY_BYTE_OFFSETS"
    assert extraction["network_render_script_link_archive_or_external_parser_permitted"] is False
    fields = set(extraction["allowed_semantic_fact_fields"])
    assert {
        "displayed_contact_name_candidate",
        "displayed_contact_role_candidate",
        "displayed_contact_email_candidate",
        "displayed_contact_url_candidate",
    } <= fields
    assert extraction["contact_tokens_are_inert_strings_not_contact_authority_or_roster_admission"] is True
    assert extraction["promotion_to_verified_official_selected_contacted_approved_or_complete_permitted"] is False


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        ("authority_provenance.fetch_execution_authorized_now", True),
        ("authority_provenance.exact_runtime_admitted", True),
        ("authority_provenance.fetch_eligible", True),
        ("runtime_admission_contract.exact_runtime_admitted", True),
        ("runtime_admission_contract.fetch_eligible", True),
        ("runtime_admission_contract.production_network_entrypoint_present", True),
        ("runtime_admission_contract.resolver_socket_tls_connect_send_or_receive_code_present", True),
        ("runtime_admission_contract.caller_injected_transport_callable_present", True),
        ("runtime_admission_contract.canonical_or_operational_write_path_present", True),
        ("runtime_admission_contract.simulator_input_roster.callable_path_fd_client_or_general_object_permitted", True),
        ("durable_custody_contract.operational_custody_qualified", True),
        ("durable_custody_contract.transcript_simulator_filesystem_side_effects_present", True),
        ("request_environment_contract.client_executable_path", "/usr/bin/curl"),
        ("request_environment_contract.ca_bundle_path", "/etc/ssl/cert.pem"),
        ("durable_custody_contract.future_operational_schema_boundary.operational_go_schema", {}),
        ("authority_provenance.administrative_message_email_ticket_or_form_authorized", True),
        ("authority_provenance.approval_creation_or_request_authorized", True),
        ("authority_provenance.authentication_credential_or_cookie_use_authorized", True),
        ("authority_provenance.archive_file_or_api_download_authorized", True),
        ("authority_provenance.data_access_authorized", True),
        ("authority_provenance.scientific_entropy_authorized", True),
        ("authority_provenance.runtime_training_or_scientific_execution_authorized", True),
        ("authority_provenance.tracker_edit_authorized_by_this_package", True),
        ("scope_review.independent_review_complete", False),
        ("scope_review.fetches_performed", 1),
        ("scope_review.durable_intents_created", 1),
        ("scope_review.amendment_can_create_approval_or_source_selection_success", True),
        ("checklist_effects.original_solo_block2_operational_boxes_open", 6),
        ("checklist_effects.original_solo_block2_operational_boxes_closed_by_amendment", 1),
        ("checklist_effects.fields_closed_by_amendment", 1),
        ("checklist_effects.blockers_closed_by_amendment", 1),
        ("checklist_effects.formal_tests_closed_by_amendment", 1),
        ("checklist_effects.results_filled_by_amendment", 1),
        ("checklist_effects.source_selection_success_created", True),
        ("checklist_effects.approval_created", True),
        ("checklist_effects.scientific_delta", 1),
    ],
)
def test_authority_promotion_tracker_and_science_hostiles_hold(
    tmp_path: Path, path: str, replacement: Any
) -> None:
    record = _load()
    _set_path(record, path, replacement)
    _must_hold(tmp_path, record)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        ("operation_roster.0.url", "https://physionet.org/search?q=challenge"),
        ("operation_roster.0.inert_request_design.method", "HEAD"),
        ("operation_roster.0.inert_request_design.max_attempts", 2),
        ("operation_roster.0.inert_request_design.max_retries", 1),
        ("operation_roster.0.inert_request_design.max_redirects", 1),
        ("operation_roster.0.inert_request_design.search_query_permitted", True),
        ("operation_roster.0.inert_request_design.alternate_url_host_mirror_or_fallback_permitted", True),
        ("operation_roster.0.inert_request_design.child_page_open_permitted", True),
        ("operation_roster.0.inert_request_design.head_request_permitted", True),
        ("operation_roster.0.inert_request_design.robots_fetch_permitted", True),
        ("operation_roster.0.inert_request_design.authentication_permitted", True),
        ("operation_roster.0.inert_request_design.credential_client_certificate_or_secret_permitted", True),
        ("operation_roster.0.inert_request_design.cookies_permitted", True),
        ("operation_roster.0.inert_request_design.forms_permitted", True),
        ("operation_roster.0.inert_request_design.range_permitted", True),
        ("operation_roster.0.inert_request_design.referer_permitted", True),
        ("operation_roster.0.inert_request_design.link_following_permitted", True),
        ("operation_roster.0.inert_request_design.scripts_or_subresources_permitted", True),
        ("operation_roster.0.inert_request_design.archive_file_api_or_data_access_permitted", True),
        ("operation_roster.0.inert_request_design.request_body_bytes", 1),
        ("operation_roster.0.request_design_is_executable", True),
        ("operation_roster.0.request_emission_code_present_in_package", True),
        ("operation_roster.0.operational_final_exact_request_sha256", "0" * 64),
        ("operation_roster.1.sequence_prerequisite", None),
        ("global_sequence_contract.row0_success_alone_authorizes_row1", True),
        ("global_sequence_contract.parallel_or_out_of_order_reservation_or_fetch_permitted", True),
        ("durable_custody_contract.client_reopen_truncate_or_path_based_overwrite_permitted", True),
        ("durable_custody_contract.second_intent_retry_resume_replacement_or_topup_permitted", True),
        ("failure_contract.outcome_can_create_approval", True),
        ("failure_contract.outcome_can_create_source_selection_success", True),
        ("page_rejection_contract.content_type_header_count_required", 2),
        ("page_rejection_contract.content_disposition_header_count_required", 1),
        ("page_rejection_contract.content_encoding_header_count_allowed", [0, 2]),
        ("page_rejection_contract.dechunk_completion_and_derived_receipt_required_for_success", False),
        ("page_rejection_contract.connection_close_requires_exactly_one_final_inert_eof_event", False),
        ("page_rejection_contract.body_truncated_semantics", "TRUE_ON_ANY_REJECTION"),
        ("page_rejection_contract.exact_inert_simulator_outcome_diagnostic_field_count", 35),
        ("page_rejection_contract.exact_inert_simulator_outcome_diagnostic_field_types_sha256", "0" * 64),
        ("page_rejection_contract.exact_inert_simulator_outcome_diagnostic_field_types.0.field", "status"),
        ("extraction_contract.promotion_to_verified_official_selected_contacted_approved_or_complete_permitted", True),
    ],
)
def test_request_sequence_custody_outcome_and_extraction_hostiles_hold(
    tmp_path: Path, path: str, replacement: Any
) -> None:
    record = _load()
    _set_path(record, path, replacement)
    _must_hold(tmp_path, record)


def test_third_url_or_row_holds(tmp_path: Path) -> None:
    record = _load()
    third = copy.deepcopy(record["operation_roster"][1])
    third["ordinal"] = 2
    third["operation_id"] = "THIRD"
    third["url"] = "https://example.invalid/"
    record["operation_roster"].append(third)
    _must_hold(tmp_path, record)


def test_extra_top_level_field_holds(tmp_path: Path) -> None:
    record = _load()
    record["extra"] = False
    _must_hold(tmp_path, record)


def test_extra_nested_field_holds(tmp_path: Path) -> None:
    record = _load()
    record["authority_provenance"]["extra"] = False
    _must_hold(tmp_path, record)


def test_boolean_cannot_substitute_for_integer(tmp_path: Path) -> None:
    record = _load()
    record["scope_review"]["operation_count"] = True
    _must_hold(tmp_path, record)


def test_null_observation_promotion_holds(tmp_path: Path) -> None:
    record = _load()
    record["current_observation_slots"][0]["status_code"] = 200
    _must_hold(tmp_path, record)


def test_request_digest_mutation_holds(tmp_path: Path) -> None:
    record = _load()
    record["operation_roster"][0]["inert_request_design"]["raw_request_sha256"] = "0" * 64
    _must_hold(tmp_path, record)


def test_bound_input_hash_mutation_holds(tmp_path: Path) -> None:
    record = _load()
    record["live_immutable_input_bindings"][0]["raw_sha256"] = "0" * 64
    _must_hold(tmp_path, record)


def test_package_hash_mutation_holds(tmp_path: Path) -> None:
    record = _load()
    record["package_bindings"][0]["raw_sha256"] = "0" * 64
    _must_hold(tmp_path, record)


def test_historical_tracker_cannot_be_reverse_live_bound(tmp_path: Path) -> None:
    record = _load()
    record["historical_snapshot_inputs"][0]["live_custody_validated"] = True
    _must_hold(tmp_path, record)


def test_bad_self_digest_holds(tmp_path: Path) -> None:
    record = _load()
    record["record_sha256"] = "0" * 64
    candidate = tmp_path / "bad-self.json"
    candidate.write_bytes(validator.canonical_bytes(record))
    with pytest.raises(validator.ValidationError):
        validator.validate(ROOT, candidate)


def test_noncanonical_json_holds(tmp_path: Path) -> None:
    record = _load()
    candidate = tmp_path / "pretty.json"
    candidate.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(validator.ValidationError):
        validator.validate(ROOT, candidate)


def test_duplicate_json_key_holds(tmp_path: Path) -> None:
    raw = MACHINE.read_text(encoding="utf-8")
    candidate = tmp_path / "duplicate.json"
    candidate.write_text('{"schema_version":"x",' + raw[1:], encoding="utf-8")
    with pytest.raises(validator.ValidationError):
        validator.validate(ROOT, candidate)


@pytest.mark.parametrize(
    "snippet",
    [
        "import socket\nsocket.socket()",
        "from urllib.request import urlopen\nurlopen('https://example.invalid')",
        "import subprocess\nsubprocess.run(['true'])",
        "from pathlib import Path\nPath('x').write_bytes(b'x')",
        "open('x', 'wb')",
        "eval('1')",
        "from typing import Callable\nx: Callable[..., object]",
        "callable(object())",
    ],
)
def test_source_execution_network_process_and_write_hostiles_are_detected(snippet: str) -> None:
    visitor = validator._SourceSafetyVisitor()
    visitor.visit(ast.parse(snippet))
    assert visitor.errors


@pytest.mark.parametrize(
    "snippet",
    [
        "import os\ndef model(): os.open('x', 0)",
        "import sqlite3\ndef model(): return None",
        "from pathlib import Path\ndef model(): Path('x').touch()",
        "def qualify(transport): return transport",
        "def execute_row(transcript): return transcript",
        "def model(callback): return callback",
        "import datetime\ndef model(): return datetime.datetime.now()",
    ],
)
def test_transcript_simulator_transport_and_filesystem_seams_are_detected(
    snippet: str,
) -> None:
    visitor = validator._SimulatorSafetyVisitor()
    visitor.visit(ast.parse(snippet))
    assert visitor.errors


@pytest.mark.parametrize(
    "snippet",
    [
        "import socket\nsocket.socket()",
        "import subprocess\nsubprocess.run(['true'])",
        "from urllib.request import urlopen\nurlopen('https://example.invalid')",
        "eval('1')",
    ],
)
def test_hostile_test_network_process_and_dynamic_routes_are_detected(
    snippet: str,
) -> None:
    visitor = validator._HostileTestSafetyVisitor()
    visitor.visit(ast.parse(snippet))
    assert visitor.errors


def test_validator_and_transcript_simulator_sources_are_safe() -> None:
    validator._validate_source_safety(ROOT)


def test_package_and_live_receipts_have_exact_rosters() -> None:
    record = _load()
    assert len(record["package_bindings"]) == 5
    assert [item["role"] for item in record["package_bindings"]] == [
        "HUMAN_AMENDMENT",
        "READ_ONLY_VALIDATOR",
        "AMENDMENT_HOSTILE_TEST",
        "DORMANT_TRANSCRIPT_SIMULATOR",
        "TRANSCRIPT_SIMULATOR_HOSTILE_TEST",
    ]
    assert len(record["live_immutable_input_bindings"]) == 32
    assert [item["ordinal"] for item in record["live_immutable_input_bindings"]] == list(range(32))


def test_contact_roster_and_every_original_gate_remain_open() -> None:
    effects = _load()["checklist_effects"]
    assert len(effects["original_solo_block2_operational_box_states"]) == 7
    assert all(item["state"] == "OPEN" for item in effects["original_solo_block2_operational_box_states"])
    assert effects["populated_precontact_instance_complete"] is False
    assert effects["independent_precontact_instance_admission_complete"] is False
    assert effects["administrative_contact_authority_recorded"] is False
    assert effects["administrative_contact_opened"] is False
    assert effects["approval_receipts_complete"] is False
    assert effects["data_access_instance_admitted"] is False
    assert effects["data_access_authority_recorded"] is False
