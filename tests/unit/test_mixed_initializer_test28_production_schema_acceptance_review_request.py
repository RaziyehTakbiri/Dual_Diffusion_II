"""Independent hostile tests for the CP75 external-review request packet."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
import gc
import hashlib
import inspect
import json
import math
import pickle
from pathlib import Path
import subprocess
from typing import Dict, List, Tuple
import weakref

import heterodiff.evaluation.mixed_initializer_test28_production_schema_acceptance_review_request as cp75
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_production_schema_acceptance_review_request.py"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")

_SCHEMA = "cp75-test28-production-schema-acceptance-review-request-v1"
_SUBJECT_SCHEMA = "cp75-test28-production-schema-acceptance-review-subject-v1"
_CRITERION_SCHEMA = "cp75-test28-production-schema-acceptance-review-criterion-v1"
_CONTRACT_SCHEMA = (
    "cp75-test28-production-schema-acceptance-review-response-contract-v1"
)
_ARTIFACT_SCHEMA = "cp75-test28-production-schema-acceptance-review-packet-artifact-v1"
_RESPONSE_SCHEMA = "cp75-test28-production-schema-acceptance-review-response-v1"
_CRITERION_RESULT_SCHEMA = (
    "cp75-test28-production-schema-acceptance-review-criterion-result-v1"
)
_PUBLIC_KEY_SCHEMA = (
    "cp75-test28-production-schema-acceptance-reviewer-public-key-document-v1"
)
_TEMPLATE_SCHEMA = (
    "cp75-test28-production-schema-acceptance-reviewer-unissued-template-v1"
)
_MANIFEST_SCHEMA = "cp75-test28-production-schema-acceptance-review-packet-manifest-v1"
_VECTORS_SCHEMA = (
    "cp75-test28-production-schema-acceptance-review-response-contract-and-"
    "test-vectors-v1"
)
_SIGNATURE_SCHEME = "rsa-pss-sha256-3072-e65537-salt32-v1"
_ZERO = "0" * 64

_ALL = (
    "CP75_TEST28_SCHEMA_VERSION",
    "CP75_TEST28_SCOPE",
    "CP75_TEST28_FORMAL_TEST_28_STATUS",
    "CP75_TEST28_REVIEW_CRITERION_COUNT",
    "CP75_TEST28_REQUIRED_REVIEWER_COUNT",
    "CP75_TEST28_PRE_REQUEST_ARTIFACT_COUNT",
    "CP75_TEST28_MANIFEST_FILE_COUNT",
    "CP75_TEST28_PRODUCTION_GATE_COUNT",
    "CP75_TEST28_BLOCKER_COUNT",
    "CP75_TEST28_REVIEWER_ROLES",
    "CP75_TEST28_CRITERION_IDS",
    "CP75_TEST28_CANDIDATE_DESCRIPTOR_DISPOSITIONS",
    "CP75_TEST28_PRODUCTION_EXECUTABLE_SCHEMA_DISPOSITIONS",
    "CP75_TEST28_ALLOWED_DISPOSITION_PAIRS",
    "CP75_TEST28_CANDIDATE_REVIEW_OUTCOMES",
    "CP75_TEST28_PRODUCTION_SCHEMA_REVIEW_OUTCOMES",
    "CP75_TEST28_SIGNATURE_SCHEME_ID",
    "CP75_TEST28_STATIC_ARTIFACT_PATHS",
    "CP75ReviewSubjectV1",
    "CP75ReviewCriterionV1",
    "CP75ExternalReviewResponseContractV1",
    "CP75ReviewPacketArtifactV1",
    "CP75ProductionSchemaAcceptanceReviewRequestBundleV1",
    "cp75_build_production_schema_acceptance_review_request_bundle",
    "cp75_production_schema_acceptance_review_checklist_bytes",
    "cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes",
    "cp75_production_schema_acceptance_reviewer_unissued_template_bytes",
    "cp75_production_schema_acceptance_review_request_json_bytes",
    "cp75_production_schema_acceptance_review_packet_manifest_json_bytes",
    "cp75_canonical_json_bytes",
    "cp75_record_sha256",
    "cp75_public_record_sha256",
)
_ROLES = (
    "protocol-and-provenance-reviewer",
    "runtime-and-durability-reviewer",
    "statistical-power-and-decision-reviewer",
    "independent-recomputation-reviewer",
)
_CRITERION_IDS = (
    "subject-byte-custody",
    "cp65-lineage-and-alias-custody",
    "scope-authority-and-nonclaim-boundary",
    "artifact-inventory-preservation",
    "lifecycle-branch-exhaustiveness",
    "crash-cut-and-durability-closure",
    "publication-manifest-and-direct-dag-closure",
    "output-envelope-framing-and-cardinality",
    "digest-preimage-and-24-crossbinding-closure",
    "raw-stable-stderr-rng-and-recomputation-semantics",
    "resource-failure-retention-and-independent-validation",
    "power-threshold-and-decision-executability",
)
_ROLE_COVERAGE = (
    (
        _ROLES[0],
        tuple(_CRITERION_IDS[index - 1] for index in (1, 2, 3, 4, 5, 6, 7, 9, 12)),
    ),
    (
        _ROLES[1],
        tuple(_CRITERION_IDS[index - 1] for index in (1, 3, 4, 5, 6, 7, 8, 10, 11, 12)),
    ),
    (_ROLES[2], tuple(_CRITERION_IDS[index - 1] for index in (1, 3, 8, 9, 12))),
    (
        _ROLES[3],
        tuple(_CRITERION_IDS[index - 1] for index in (1, 2, 3, 4, 8, 9, 10, 11, 12)),
    ),
)
_CURRENT_C12 = (
    (_ROLES[0], _CRITERION_IDS[11], "ABSTAIN"),
    (_ROLES[1], _CRITERION_IDS[11], "ABSTAIN"),
    (_ROLES[2], _CRITERION_IDS[11], "DEFER"),
    (_ROLES[3], _CRITERION_IDS[11], "DEFER"),
)
_ALLOWED_PAIRS = (
    ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY", "ACCEPT"),
    ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY", "DEFER"),
    ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY", "REJECT"),
    ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY", "ABSTAIN"),
    ("DEFER", "DEFER"),
    ("DEFER", "REJECT"),
    ("REJECT", "REJECT"),
    ("ABSTAIN", "ABSTAIN"),
    ("ABSTAIN", "DEFER"),
    ("ABSTAIN", "REJECT"),
    ("WITHDRAW", "WITHDRAW"),
)
_OPEN_ITEMS = (
    "primary-threshold-comparison-operator",
    "primary-threshold-comparison-direction",
    "primary-threshold-value-law",
    "primary-selected-count-justification",
    "primary-32-slot-decision-function",
    "decision-timestamp-authority",
)
_STATIC_PATHS = (
    "research/preregistrations/cp75_test28_production_schema_acceptance_review_checklist_v1.md",
    "research/fixtures/cp75_test28_production_schema_acceptance_review_response_contract_and_test_vectors_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_protocol_and_provenance_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_runtime_and_durability_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_statistical_power_and_decision_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_independent_recomputation_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_review_request_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_review_packet_manifest_v1.json",
)

_SUBJECT_FIELDS = (
    "schema_version",
    "subject_id",
    "acceptance_target",
    "v25_protocol_markdown_path",
    "v25_protocol_markdown_sha256",
    "v25_protocol_markdown_bytes",
    "v25_protocol_markdown_lf_count",
    "v25_machine_manifest_path",
    "v25_machine_manifest_sha256",
    "v25_machine_manifest_bytes",
    "v25_machine_manifest_lf_count",
    "cp74_component_ids",
    "cp74_source_and_test_paths",
    "cp74_source_and_test_sha256s",
    "cp74_source_and_test_bytes",
    "cp74_source_and_test_lf_counts",
    "v25_embedded_record_json_pointers",
    "authoritative_bundle_canonical_json_bytes",
    "authoritative_bundle_canonical_json_sha256",
    "authoritative_bundle_record_sha256",
    "authoritative_bundle_public_sha256",
    "authoritative_candidate_schema_semantic_sha256",
    "independent_validator_bundle_canonical_json_bytes",
    "independent_validator_bundle_canonical_json_sha256",
    "independent_validator_bundle_record_sha256",
    "independent_validator_bundle_public_sha256",
    "independent_validation_summary_canonical_json_bytes",
    "independent_validation_summary_canonical_json_sha256",
    "independent_validation_summary_record_sha256",
    "independent_validation_summary_public_sha256",
    "cp65_schema_semantic_sha256",
    "cp65_artifact_id_order_sha256",
    "cp65_artifact_schema_record_order_sha256",
    "cp65_referenced_output_id_order_sha256",
    "cp65_gate_evidence_dag_node_count",
    "cp65_gate_evidence_dag_edge_count",
    "cp65_gate_evidence_dag_semantic_sha256",
    "cp65_gate_evidence_artifact_id_aliases",
    "cp65_typed_graph_vector_lengths",
    "cp65_typed_graph_semantic_sha256",
    "cp65_gate_evidence_dag_is_not_full_typed_graph",
    "cp65_typed_graph_inherited_by_hash_reference_only",
    "cp65_typed_graph_revalidated_by_cp75",
    "artifact_count",
    "referenced_output_count",
    "lifecycle_branch_count",
    "crash_cut_count",
    "output_cross_binding_count",
    "complete_output_instance_count",
    "complete_output_unit_count",
    "focused_test_count",
    "focused_test_duration_seconds",
    "focused_test_exit_code",
    "aggregate_test_count",
    "aggregate_pytest_duration_seconds",
    "aggregate_exit_code",
    "aggregate_real_seconds",
    "aggregate_user_seconds",
    "aggregate_sys_seconds",
    "candidate_descriptor_packet_internally_consistent",
    "candidate_descriptor_definition_complete",
    "candidate_schema_executable",
    "primary_decision_semantics_resolved",
    "primary_decision_semantics_deferred_to_external_power_review",
    "independent_structural_validation",
    "schema_acceptance_independent",
    "candidate_schema_accepted",
    "authoritative_for_production",
    "production_schema_frozen",
    "production_execution_and_output_schema_frozen",
    "production_receipt_schema_frozen",
    "production_artifacts_observed",
    "production_output_bodies_accepted",
    "production_evidence_accepted",
    "production_execution_authorized",
    "formal_test_28_status",
    "production_gate_states",
    "draft_blocker_states",
    "known_open_item_ids",
    "current_subject_candidate_descriptor_acceptance_eligible",
    "current_subject_production_executable_schema_acceptance_eligible",
    "local_candidate_descriptor_pre_review_disposition",
    "local_production_executable_schema_pre_review_disposition",
    "scope_and_nonclaims_sha256",
    "subject_sha256",
)
_CRITERION_FIELDS = (
    "schema_version",
    "criterion_ordinal",
    "criterion_id",
    "assigned_reviewer_roles",
    "review_question",
    "review_question_sha256",
    "acceptance_rule",
    "subject_json_pointers",
    "blocking_for_candidate_descriptor_acceptance",
    "blocking_for_production_executable_schema_acceptance",
    "local_pre_review_disposition",
    "local_pre_review_only",
    "external_reviewer_disposition_present",
    "unexpected_findings_permitted",
    "record_sha256",
)
_CONTRACT_FIELDS = (
    "schema_version",
    "required_reviewer_roles",
    "required_reviewer_count",
    "role_criterion_coverage",
    "current_subject_role_criterion_disposition_requirements",
    "current_subject_role_criterion_payload_requirements",
    "criterion_result_schema_version",
    "criterion_result_exact_keys",
    "response_schema_version",
    "response_exact_keys",
    "reviewer_public_key_schema_version",
    "reviewer_public_key_exact_keys",
    "criterion_disposition_domain",
    "candidate_descriptor_disposition_domain",
    "production_executable_schema_disposition_domain",
    "allowed_disposition_pairs",
    "current_subject_allowed_disposition_pairs",
    "axis_disposition_derivation_precedence",
    "criterion_result_branch_rules",
    "response_relation_and_nullability_branch_rules",
    "finding_change_and_report_binding_rules",
    "candidate_descriptor_review_outcome_domain",
    "production_schema_review_outcome_domain",
    "candidate_conditional_acceptance_maps_to",
    "production_conditional_acceptance_maps_to",
    "distinct_reviewer_identity_required",
    "distinct_reviewer_key_identity_required",
    "external_trust_root_preexists_candidate_required",
    "authority_appointment_required",
    "conflict_of_interest_attestation_required",
    "independence_attestation_required",
    "revocation_check_required",
    "trusted_time_required",
    "signature_scheme_id",
    "reviewer_public_key_identity_formula",
    "key_identity_formula_binds_organization",
    "reviewer_public_key_document_digest_formula",
    "reviewer_public_key_plain_sha256_binding_rule",
    "reviewer_public_key_modulus_and_exponent_grammar",
    "reviewer_public_key_and_response_interval_coherence_rule",
    "criterion_result_digest_formula",
    "ordered_criterion_result_digest_formula",
    "response_signature_preimage_formula",
    "response_signature_sha256_formula",
    "response_record_digest_formula",
    "current_subject_candidate_descriptor_accept_permitted",
    "current_subject_production_schema_accept_permitted",
    "signature_math_implies_authority",
    "supplied_response_validator_performs_trust_or_authority_validation",
    "local_response_issuance_performed",
    "local_key_generation_performed",
    "local_signing_performed",
    "external_review_performed",
    "candidate_descriptor_acceptance_claimed",
    "schema_acceptance_claimed",
    "production_execution_authorized",
    "record_sha256",
)
_ARTIFACT_FIELDS = (
    "schema_version",
    "artifact_ordinal",
    "artifact_id",
    "path",
    "media_kind",
    "canonical_encoding",
    "terminal_newline_rule",
    "dependency_record_sha256s",
    "dependency_artifact_sha256s",
    "content_bytes",
    "lf_count",
    "content_sha256",
    "template_only",
    "issued",
    "external_identity_present",
    "external_key_present",
    "external_signature_present",
    "acceptance_effect",
    "record_sha256",
)
_BUNDLE_FIELDS = (
    "schema_version",
    "request_id",
    "review_round_ordinal",
    "review_context_sha256",
    "review_context_randomness_used",
    "review_context_freshness_claimed",
    "review_context_challenge_claimed",
    "review_context_replay_prevention_claimed",
    "acceptance_target",
    "review_subject",
    "ordered_review_criteria",
    "ordered_review_criterion_record_sha256s",
    "ordered_review_criteria_sha256",
    "response_contract",
    "ordered_packet_artifacts",
    "ordered_packet_artifact_record_sha256s",
    "ordered_packet_artifacts_sha256",
    "review_packet_manifest_path",
    "request_state",
    "response_count",
    "current_candidate_descriptor_review_outcome",
    "current_production_executable_schema_review_outcome",
    "local_review_packet_release_qualified",
    "current_subject_candidate_descriptor_acceptance_eligible",
    "current_subject_production_executable_schema_acceptance_eligible",
    "candidate_descriptor_acceptance_effective",
    "schema_acceptance_independent",
    "schema_acceptance_effective",
    "external_review_performed",
    "external_reviewer_authority_verified",
    "subsequent_candidate_descriptor_development_qualification_construction_permitted",
    "production_execution_authorized",
    "production_gate_states",
    "draft_blocker_states",
    "formal_test_28_status",
    "all_record_digests_valid",
    "builder_validates_internal_definition",
    "record_sha256",
)
_LAYOUTS = (
    (cp75.CP75ReviewSubjectV1, _SUBJECT_FIELDS),
    (cp75.CP75ReviewCriterionV1, _CRITERION_FIELDS),
    (cp75.CP75ExternalReviewResponseContractV1, _CONTRACT_FIELDS),
    (cp75.CP75ReviewPacketArtifactV1, _ARTIFACT_FIELDS),
    (cp75.CP75ProductionSchemaAcceptanceReviewRequestBundleV1, _BUNDLE_FIELDS),
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        _plain(value),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _plain(value: object) -> object:
    if type(value) in {item[0] for item in _LAYOUTS}:
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    return value


def _digest_record(record: object, carrier: str, domain: str) -> str:
    body = dict(_plain(record))
    body[carrier] = _ZERO
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(body)).hexdigest()


def _ordered(domain: str, digests: Tuple[str, ...]) -> str:
    return hashlib.sha256(
        domain.encode("ascii")
        + b"\0"
        + b"".join(bytes.fromhex(item) for item in digests)
    ).hexdigest()


def _json(payload: bytes) -> Dict[str, object]:
    return json.loads(payload.decode("ascii"))


def _mgf1(seed: bytes, length: int) -> bytes:
    output = bytearray()
    for counter in range(math.ceil(length / hashlib.sha256().digest_size)):
        output.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
    return bytes(output[:length])


def _pss_verify(message: bytes, signature_hex: str, modulus_hex: str) -> bool:
    modulus = int(modulus_hex, 16)
    signature = int(signature_hex, 16)
    if signature >= modulus:
        return False
    encoded = pow(signature, 65_537, modulus).to_bytes(384, "big")
    if encoded[-1] != 0xBC:
        return False
    masked_db, h_value = encoded[:351], encoded[351:383]
    db_mask = _mgf1(h_value, 351)
    db_value = bytes(left ^ right for left, right in zip(masked_db, db_mask))
    db_value = bytes([db_value[0] & 0x7F]) + db_value[1:]
    if db_value[:318] != b"\0" * 318 or db_value[318] != 1:
        return False
    salt = db_value[319:]
    expected = hashlib.sha256(
        b"\0" * 8 + hashlib.sha256(message).digest() + salt
    ).digest()
    return h_value == expected


def _import_roots(tree: ast.AST) -> Tuple[str, ...]:
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
    return tuple(roots)


def _unissued_copy(record: object) -> object:
    clone = object.__new__(type(record))
    for item in fields(record):
        object.__setattr__(clone, item.name, getattr(record, item.name))
    return clone


def test_public_surface_constants_and_static_path_order_are_exact() -> None:
    assert cp75.__all__ == _ALL
    assert len(cp75.__all__) == len(set(cp75.__all__)) == 32
    assert cp75.CP75_TEST28_SCHEMA_VERSION == _SCHEMA
    assert cp75.CP75_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert (
        cp75.CP75_TEST28_REVIEW_CRITERION_COUNT,
        cp75.CP75_TEST28_REQUIRED_REVIEWER_COUNT,
        cp75.CP75_TEST28_PRE_REQUEST_ARTIFACT_COUNT,
        cp75.CP75_TEST28_MANIFEST_FILE_COUNT,
        cp75.CP75_TEST28_PRODUCTION_GATE_COUNT,
        cp75.CP75_TEST28_BLOCKER_COUNT,
    ) == (12, 4, 6, 7, 17, 4)
    assert cp75.CP75_TEST28_REVIEWER_ROLES == _ROLES
    assert cp75.CP75_TEST28_CRITERION_IDS == _CRITERION_IDS
    assert cp75.CP75_TEST28_ALLOWED_DISPOSITION_PAIRS == _ALLOWED_PAIRS
    assert cp75.CP75_TEST28_SIGNATURE_SCHEME_ID == _SIGNATURE_SCHEME
    assert cp75.CP75_TEST28_STATIC_ARTIFACT_PATHS == _STATIC_PATHS
    assert len(set(_STATIC_PATHS)) == 8


@pytest.mark.parametrize(("record_type", "expected_fields"), _LAYOUTS)
def test_sealed_record_layouts_are_exact(
    record_type: type, expected_fields: tuple
) -> None:
    assert is_dataclass(record_type)
    assert tuple(item.name for item in fields(record_type)) == expected_fields
    assert record_type.__slots__ == expected_fields
    with pytest.raises(TypeError, match="module-created only"):
        record_type()
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("HostileSubclass", (record_type,), {})


def test_public_signatures_are_narrow_and_zero_io() -> None:
    zero_argument = (
        cp75.cp75_build_production_schema_acceptance_review_request_bundle,
        cp75.cp75_production_schema_acceptance_review_checklist_bytes,
        cp75.cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes,
        cp75.cp75_production_schema_acceptance_reviewer_unissued_template_bytes,
        cp75.cp75_production_schema_acceptance_review_request_json_bytes,
        cp75.cp75_production_schema_acceptance_review_packet_manifest_json_bytes,
    )
    assert all(
        tuple(inspect.signature(function).parameters) == ()
        for function in zero_argument
    )
    for function in (
        cp75.cp75_canonical_json_bytes,
        cp75.cp75_record_sha256,
        cp75.cp75_public_record_sha256,
    ):
        assert tuple(inspect.signature(function).parameters) == ("record",)


def test_source_is_stdlib_only_and_has_no_io_clock_rng_network_or_subprocess() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"), filename=str(_SOURCE))
    assert set(_import_roots(tree)) == {
        "__future__",
        "dataclasses",
        "hashlib",
        "hmac",
        "json",
        "math",
        "threading",
        "typing",
        "weakref",
    }
    forbidden = {
        "open",
        "Path",
        "socket",
        "subprocess",
        "time",
        "datetime",
        "random",
        "secrets",
        "urandom",
        "requests",
        "urllib",
    }
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert forbidden.isdisjoint(called)


def test_builder_is_deterministic_fresh_and_digest_complete() -> None:
    first = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    second = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    assert first is not second
    assert first.review_subject is not second.review_subject
    assert cp75.cp75_canonical_json_bytes(first) == cp75.cp75_canonical_json_bytes(
        second
    )
    assert first.record_sha256 == second.record_sha256
    assert cp75.cp75_public_record_sha256(first) == cp75.cp75_public_record_sha256(
        second
    )
    records = (
        first.review_subject,
        *first.ordered_review_criteria,
        first.response_contract,
        *first.ordered_packet_artifacts,
        first,
    )
    domains = {
        cp75.CP75ReviewSubjectV1: (_SUBJECT_SCHEMA, "subject_sha256"),
        cp75.CP75ReviewCriterionV1: (_CRITERION_SCHEMA, "record_sha256"),
        cp75.CP75ExternalReviewResponseContractV1: (_CONTRACT_SCHEMA, "record_sha256"),
        cp75.CP75ReviewPacketArtifactV1: (_ARTIFACT_SCHEMA, "record_sha256"),
        cp75.CP75ProductionSchemaAcceptanceReviewRequestBundleV1: (
            _SCHEMA,
            "record_sha256",
        ),
    }
    for record in records:
        domain, carrier = domains[type(record)]
        assert getattr(record, carrier) == _digest_record(record, carrier, domain)
        assert cp75.cp75_record_sha256(record) == getattr(record, carrier)
        expected_public = hashlib.sha256(
            b"cp75-public-record-v1\0"
            + type(record).__name__.encode("ascii")
            + b"\0"
            + _canonical(record)
        ).hexdigest()
        assert cp75.cp75_public_record_sha256(record) == expected_public


def test_ordered_record_digests_and_review_context_are_independently_recomputed() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    criterion_digests = tuple(
        item.record_sha256 for item in bundle.ordered_review_criteria
    )
    artifact_digests = tuple(
        item.record_sha256 for item in bundle.ordered_packet_artifacts
    )
    assert criterion_digests == bundle.ordered_review_criterion_record_sha256s
    assert artifact_digests == bundle.ordered_packet_artifact_record_sha256s
    assert bundle.ordered_review_criteria_sha256 == _ordered(
        "cp75-test28-production-schema-acceptance-review-criterion-record-digests-v1",
        criterion_digests,
    )
    assert bundle.ordered_packet_artifacts_sha256 == _ordered(
        "cp75-test28-production-schema-acceptance-review-packet-artifact-record-digests-v1",
        artifact_digests,
    )
    context = hashlib.sha256(
        b"cp75-test28-production-schema-acceptance-review-context-v1\0"
        + _canonical(
            {
                "acceptance_target": bundle.acceptance_target,
                "review_round_ordinal": 1,
                "subject_record_sha256": bundle.review_subject.subject_sha256,
            }
        )
    ).hexdigest()
    assert bundle.review_context_sha256 == context
    assert bundle.review_context_randomness_used is False
    assert bundle.review_context_freshness_claimed is False
    assert bundle.review_context_challenge_claimed is False
    assert bundle.review_context_replay_prevention_claimed is False


def test_scope_nonclaim_digest_is_independent_and_complete() -> None:
    subject = (
        cp75.cp75_build_production_schema_acceptance_review_request_bundle().review_subject
    )
    projection = {
        "acceptance_target": subject.acceptance_target,
        "known_open_item_ids": subject.known_open_item_ids,
        "current_subject_candidate_descriptor_acceptance_eligible": True,
        "current_subject_production_executable_schema_acceptance_eligible": False,
        "local_candidate_descriptor_pre_review_disposition": "UNREVIEWED",
        "local_production_executable_schema_pre_review_disposition": "DEFER_REQUIRED_NONEXECUTABLE_SUBJECT",
        "candidate_only": True,
        "candidate_schema_executable": False,
        "primary_decision_semantics_resolved": False,
        "primary_decision_semantics_deferred_to_external_power_review": True,
        "external_review_performed": False,
        "external_reviewer_authority_verified": False,
        "candidate_descriptor_acceptance_effective": False,
        "schema_acceptance_independent": False,
        "candidate_schema_accepted": False,
        "authoritative_for_production": False,
        "production_schema_frozen": False,
        "production_execution_and_output_schema_frozen": False,
        "production_receipt_schema_frozen": False,
        "production_artifacts_observed": False,
        "production_output_bodies_accepted": False,
        "production_evidence_accepted": False,
        "production_execution_authorized": False,
        "production_gate_states": ("MISSING",) * 17,
        "draft_blocker_states": ("MISSING",) * 4,
        "formal_test_28_status": "OPEN",
    }
    assert (
        subject.scope_and_nonclaims_sha256
        == hashlib.sha256(
            b"cp75-test28-production-schema-acceptance-review-scope-and-nonclaims-v1\0"
            + _canonical(projection)
        ).hexdigest()
    )


def test_subject_exact_pins_counts_and_candidate_only_boundary() -> None:
    subject = (
        cp75.cp75_build_production_schema_acceptance_review_request_bundle().review_subject
    )
    assert subject.schema_version == _SUBJECT_SCHEMA
    assert (
        subject.v25_protocol_markdown_sha256
        == "4f939cca60fe6de9f87422f9cd4060e429f9ce34b43a40607d0946a6b928858f"
    )
    assert (
        subject.v25_protocol_markdown_bytes,
        subject.v25_protocol_markdown_lf_count,
    ) == (276_704, 4_463)
    assert (
        subject.v25_machine_manifest_sha256
        == "5153dbad02fbb20a36a5873e1a14dc93ac9f1560d9f71745fcfc63d22778df76"
    )
    assert (
        subject.v25_machine_manifest_bytes,
        subject.v25_machine_manifest_lf_count,
    ) == (6_971_770, 133_870)
    assert subject.cp74_source_and_test_sha256s == (
        "785f9738ebf168dfdf26c24751066b00a8c90a11b20bf60db8b02d8c9dbab347",
        "7a64ddc59c122ae354ec6442ae6f12f1c3559601ea39136a4279027971fb726d",
        "ccbd88521fc92c373d5795205dc5980d2a1f217c990c1a92fc5e4579647e6b6b",
        "598c3f82c1e65fbc3192e877519d1d09608ead191fd66eb8b152478ce5dc6aa5",
    )
    assert (subject.artifact_count, subject.referenced_output_count) == (64, 15)
    assert (
        subject.lifecycle_branch_count,
        subject.crash_cut_count,
        subject.output_cross_binding_count,
    ) == (11, 6, 24)
    assert (
        subject.complete_output_instance_count,
        subject.complete_output_unit_count,
    ) == (201, 196_617)
    assert (
        subject.focused_test_count,
        subject.focused_test_duration_seconds,
        subject.focused_test_exit_code,
    ) == (194, "36.72", 0)
    assert (
        subject.aggregate_test_count,
        subject.aggregate_pytest_duration_seconds,
        subject.aggregate_exit_code,
    ) == (2_463, "3331.73", 0)
    assert (
        subject.aggregate_real_seconds,
        subject.aggregate_user_seconds,
        subject.aggregate_sys_seconds,
    ) == ("3332.41", "3282.92", "24.84")
    assert subject.known_open_item_ids == _OPEN_ITEMS
    assert subject.current_subject_candidate_descriptor_acceptance_eligible is True
    assert (
        subject.current_subject_production_executable_schema_acceptance_eligible
        is False
    )
    true_fields = (
        "candidate_descriptor_packet_internally_consistent",
        "candidate_descriptor_definition_complete",
        "primary_decision_semantics_deferred_to_external_power_review",
        "independent_structural_validation",
        "cp65_gate_evidence_dag_is_not_full_typed_graph",
        "cp65_typed_graph_inherited_by_hash_reference_only",
    )
    false_fields = (
        "candidate_schema_executable",
        "primary_decision_semantics_resolved",
        "schema_acceptance_independent",
        "candidate_schema_accepted",
        "authoritative_for_production",
        "production_schema_frozen",
        "production_execution_and_output_schema_frozen",
        "production_receipt_schema_frozen",
        "production_artifacts_observed",
        "production_output_bodies_accepted",
        "production_evidence_accepted",
        "production_execution_authorized",
        "cp65_typed_graph_revalidated_by_cp75",
    )
    assert all(getattr(subject, name) is True for name in true_fields)
    assert all(getattr(subject, name) is False for name in false_fields)
    assert subject.production_gate_states == ("MISSING",) * 17
    assert subject.draft_blocker_states == ("MISSING",) * 4
    assert subject.formal_test_28_status == "OPEN"


def test_criterion_inventory_roles_questions_and_blocking_axes_are_exact() -> None:
    criteria = (
        cp75.cp75_build_production_schema_acceptance_review_request_bundle().ordered_review_criteria
    )
    assert tuple(item.criterion_ordinal for item in criteria) == tuple(range(1, 13))
    assert tuple(item.criterion_id for item in criteria) == _CRITERION_IDS
    assert (
        tuple(
            (
                role,
                tuple(
                    item.criterion_id
                    for item in criteria
                    if role in item.assigned_reviewer_roles
                ),
            )
            for role in _ROLES
        )
        == _ROLE_COVERAGE
    )
    for item in criteria:
        assert item.schema_version == _CRITERION_SCHEMA
        assert (
            item.review_question_sha256
            == hashlib.sha256((item.review_question + "\n").encode()).hexdigest()
        )
        assert item.local_pre_review_only is True
        assert item.external_reviewer_disposition_present is False
        assert item.unexpected_findings_permitted is True
        assert item.blocking_for_production_executable_schema_acceptance is True
        if item.criterion_ordinal == 12:
            assert item.blocking_for_candidate_descriptor_acceptance is False
            assert item.local_pre_review_disposition == "PRODUCTION_NONPASS_REQUIRED"
        else:
            assert item.blocking_for_candidate_descriptor_acceptance is True
            assert item.local_pre_review_disposition == "UNREVIEWED"


def test_response_contract_two_axis_matrix_and_current_subject_rules_are_exact() -> None:
    contract = (
        cp75.cp75_build_production_schema_acceptance_review_request_bundle().response_contract
    )
    assert contract.schema_version == _CONTRACT_SCHEMA
    assert contract.required_reviewer_roles == _ROLES
    assert contract.required_reviewer_count == 4
    assert contract.role_criterion_coverage == _ROLE_COVERAGE
    assert (
        contract.current_subject_role_criterion_disposition_requirements == _CURRENT_C12
    )
    assert tuple(
        (role, disposition)
        for role, disposition, _rule in contract.current_subject_role_criterion_payload_requirements
    ) == tuple((role, disposition) for role, _criterion, disposition in _CURRENT_C12)
    for (
        role,
        disposition,
        rule,
    ) in contract.current_subject_role_criterion_payload_requirements:
        assert "acknowledged_subject_open_item_ids=exact-six" in rule
        assert "comment_sha256=nonzero-reason-digest" in rule
        if role in _ROLES[:2]:
            assert disposition == "ABSTAIN"
            assert "finding_ids=empty" in rule
            assert "required_change_ids-contribution=empty" in rule
        else:
            assert disposition == "DEFER"
            assert "finding_ids=exact-six-known-open-item-ids" in rule
            assert "required_change_ids=exact-six-known-open-item-ids" in rule
    assert contract.criterion_disposition_domain == ("PASS", "DEFER", "FAIL", "ABSTAIN")
    assert contract.allowed_disposition_pairs == _ALLOWED_PAIRS
    assert contract.current_subject_allowed_disposition_pairs == tuple(
        pair
        for pair in _ALLOWED_PAIRS
        if pair != ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY", "ACCEPT")
    )
    assert contract.current_subject_candidate_descriptor_accept_permitted is True
    assert contract.current_subject_production_schema_accept_permitted is False
    assert contract.key_identity_formula_binds_organization is False
    assert contract.axis_disposition_derivation_precedence == (
        "if-any-applicable-blocking-result-FAIL-then-axis-disposition-REJECT",
        "else-if-any-applicable-blocking-result-DEFER-then-axis-disposition-DEFER",
        "else-if-any-applicable-blocking-result-ABSTAIN-then-axis-disposition-ABSTAIN",
        "else-all-applicable-blocking-results-PASS-then-candidate-axis-ACCEPT_FOR_CP75_DEVELOPMENT_ONLY-or-production-axis-ACCEPT",
        "WITHDRAW-is-a-separate-empty-result-response-branch-and-both-axes-WITHDRAW",
    )
    assert len(contract.criterion_result_branch_rules) == 5
    assert len(contract.response_relation_and_nullability_branch_rules) == 5
    assert len(contract.finding_change_and_report_binding_rules) == 5
    assert any(
        "WITHDRAW" in rule
        for rule in contract.response_relation_and_nullability_branch_rules
    )
    assert any(
        "not-closed-to-an-allowlist" in rule
        for rule in contract.finding_change_and_report_binding_rules
    )
    assert (
        "document_sha256-set-to-64-zero-hex"
        in contract.reviewer_public_key_document_digest_formula
    )
    assert "plain-SHA256" in contract.reviewer_public_key_plain_sha256_binding_rule
    assert (
        "exact-768-lowercase-hex"
        in contract.reviewer_public_key_modulus_and_exponent_grammar
    )
    assert (
        "coherence-only-no-clock"
        in contract.reviewer_public_key_and_response_interval_coherence_rule
    )
    required_true = (
        "distinct_reviewer_identity_required",
        "distinct_reviewer_key_identity_required",
        "external_trust_root_preexists_candidate_required",
        "authority_appointment_required",
        "conflict_of_interest_attestation_required",
        "independence_attestation_required",
        "revocation_check_required",
        "trusted_time_required",
    )
    required_false = (
        "signature_math_implies_authority",
        "supplied_response_validator_performs_trust_or_authority_validation",
        "local_response_issuance_performed",
        "local_key_generation_performed",
        "local_signing_performed",
        "external_review_performed",
        "candidate_descriptor_acceptance_claimed",
        "schema_acceptance_claimed",
        "production_execution_authorized",
    )
    assert all(getattr(contract, name) is True for name in required_true)
    assert all(getattr(contract, name) is False for name in required_false)


def test_bundle_is_release_ready_but_has_zero_review_or_acceptance_effect() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    assert bundle.request_state == "READY_FOR_EXTERNAL_REVIEW"
    assert bundle.response_count == 0
    assert bundle.current_candidate_descriptor_review_outcome == "UNREVIEWED"
    assert bundle.current_production_executable_schema_review_outcome == "UNREVIEWED"
    assert bundle.local_review_packet_release_qualified is True
    assert bundle.current_subject_candidate_descriptor_acceptance_eligible is True
    assert (
        bundle.current_subject_production_executable_schema_acceptance_eligible is False
    )
    assert bundle.all_record_digests_valid is True
    assert bundle.builder_validates_internal_definition is True
    false_fields = (
        "candidate_descriptor_acceptance_effective",
        "schema_acceptance_independent",
        "schema_acceptance_effective",
        "external_review_performed",
        "external_reviewer_authority_verified",
        "subsequent_candidate_descriptor_development_qualification_construction_permitted",
        "production_execution_authorized",
    )
    assert all(getattr(bundle, name) is False for name in false_fields)
    assert bundle.production_gate_states == ("MISSING",) * 17
    assert bundle.draft_blocker_states == ("MISSING",) * 4
    assert bundle.formal_test_28_status == "OPEN"


def test_static_getters_match_all_eight_materialized_files_exactly() -> None:
    generated = (
        cp75.cp75_production_schema_acceptance_review_checklist_bytes(),
        cp75.cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes(),
        *cp75.cp75_production_schema_acceptance_reviewer_unissued_template_bytes(),
        cp75.cp75_production_schema_acceptance_review_request_json_bytes(),
        cp75.cp75_production_schema_acceptance_review_packet_manifest_json_bytes(),
    )
    assert len(generated) == len(_STATIC_PATHS) == 8
    for path, content in zip(_STATIC_PATHS, generated):
        assert (_ROOT / path).read_bytes() == content
    assert generated[0].endswith(b"\n") and b"\r" not in generated[0]
    assert all(not item.endswith(b"\n") and b"\r" not in item for item in generated[1:])


def test_six_pre_request_artifact_records_bind_exact_static_contents() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    contents = (
        cp75.cp75_production_schema_acceptance_review_checklist_bytes(),
        cp75.cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes(),
        *cp75.cp75_production_schema_acceptance_reviewer_unissued_template_bytes(),
    )
    assert tuple(
        item.artifact_ordinal for item in bundle.ordered_packet_artifacts
    ) == tuple(range(1, 7))
    assert (
        tuple(item.path for item in bundle.ordered_packet_artifacts)
        == _STATIC_PATHS[:6]
    )
    for index, (item, content) in enumerate(
        zip(bundle.ordered_packet_artifacts, contents)
    ):
        assert item.schema_version == _ARTIFACT_SCHEMA
        assert item.content_bytes == len(content)
        assert item.lf_count == content.count(b"\n")
        assert item.content_sha256 == hashlib.sha256(content).hexdigest()
        assert item.template_only is (index >= 2)
        assert item.issued is False
        assert item.external_identity_present is False
        assert item.external_key_present is False
        assert item.external_signature_present is False
        assert item.acceptance_effect == "NONE"


def test_manifest_has_exact_seven_file_inventory_and_no_self_cycle() -> None:
    request = cp75.cp75_production_schema_acceptance_review_request_json_bytes()
    manifest_bytes = (
        cp75.cp75_production_schema_acceptance_review_packet_manifest_json_bytes()
    )
    manifest = _json(manifest_bytes)
    entries = manifest["ordered_packet_files"]
    assert manifest["schema_version"] == _MANIFEST_SCHEMA
    assert manifest["packet_file_count"] == len(entries) == 7
    assert tuple(item["ordinal"] for item in entries) == tuple(range(1, 8))
    assert tuple(item["path"] for item in entries) == _STATIC_PATHS[:7]
    assert _STATIC_PATHS[7] not in {item["path"] for item in entries}
    contents = (
        cp75.cp75_production_schema_acceptance_review_checklist_bytes(),
        cp75.cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes(),
        *cp75.cp75_production_schema_acceptance_reviewer_unissued_template_bytes(),
        request,
    )
    entry_digests = []
    for item, content in zip(entries, contents):
        assert item["content_bytes"] == len(content)
        assert item["lf_count"] == content.count(b"\n")
        assert item["content_sha256"] == hashlib.sha256(content).hexdigest()
        body = dict(item)
        digest = body["entry_sha256"]
        body["entry_sha256"] = _ZERO
        assert (
            digest
            == hashlib.sha256(
                b"cp75-test28-production-schema-acceptance-review-packet-file-v1\0"
                + _canonical(body)
            ).hexdigest()
        )
        entry_digests.append(digest)
    assert manifest["ordered_packet_file_record_sha256s"] == entry_digests
    assert manifest["ordered_packet_files_sha256"] == _ordered(
        "cp75-test28-production-schema-acceptance-review-packet-file-record-digests-v1",
        tuple(entry_digests),
    )
    assert manifest["request_canonical_json_bytes"] == len(request)
    assert (
        manifest["request_canonical_json_sha256"] == hashlib.sha256(request).hexdigest()
    )
    body = dict(manifest)
    digest = body["manifest_sha256"]
    body["manifest_sha256"] = _ZERO
    assert (
        digest
        == hashlib.sha256(
            b"cp75-test28-production-schema-acceptance-review-packet-manifest-v1\0"
            + _canonical(body)
        ).hexdigest()
    )


def test_request_is_exact_canonical_bundle_and_does_not_embed_manifest() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    request = cp75.cp75_production_schema_acceptance_review_request_json_bytes()
    assert request == cp75.cp75_canonical_json_bytes(bundle) == _canonical(bundle)
    decoded = _json(request)
    assert decoded["record_sha256"] == bundle.record_sha256
    assert decoded["review_packet_manifest_path"] == _STATIC_PATHS[7]
    assert "manifest_sha256" not in decoded
    assert _STATIC_PATHS[7].encode("ascii") in request


def test_checklist_contains_exact_question_bytes_and_nonclaim_warnings() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    checklist = cp75.cp75_production_schema_acceptance_review_checklist_bytes()
    for criterion in bundle.ordered_review_criteria:
        begin = (
            "<!-- CP75-CRITERION:%s:QUESTION-BEGIN -->\n" % criterion.criterion_id
        ).encode()
        end = (
            "<!-- CP75-CRITERION:%s:QUESTION-END -->" % criterion.criterion_id
        ).encode()
        left = checklist.index(begin) + len(begin)
        right = checklist.index(end, left)
        assert (
            hashlib.sha256(checklist[left:right]).hexdigest()
            == criterion.review_question_sha256
        )
    required = (
        b"No external review, authority, acceptance, production execution",
        b"Signature mathematics alone is never identity or authority",
        b"Production ACCEPT is forbidden",
        b"does not check external attachment bytes, trust, authority, current time",
        b"does not freeze a production schema",
    )
    assert all(item in checklist for item in required)


@pytest.mark.parametrize("role_index", range(4))
def test_each_unissued_role_template_has_exact_fixed_and_null_branches(
    role_index: int,
) -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    templates = (
        cp75.cp75_production_schema_acceptance_reviewer_unissued_template_bytes()
    )
    template = _json(templates[role_index])
    role = _ROLES[role_index]
    assert template["schema_version"] == _TEMPLATE_SCHEMA
    assert template["template_only"] is True and template["issued"] is False
    assert template["reviewer_role"] == role
    assert tuple(template["assigned_criterion_ids"]) == dict(_ROLE_COVERAGE)[role]
    assert template["subject_record_sha256"] == bundle.review_subject.subject_sha256
    assert template["review_context_sha256"] == bundle.review_context_sha256
    response = template["response_template"]
    fixed_response = {
        "schema_version",
        "request_schema_version",
        "subject_record_sha256",
        "checklist_sha256",
        "response_contract_test_vectors_sha256",
        "review_round_ordinal",
        "review_context_sha256",
        "acceptance_target",
        "scope_and_nonclaims_sha256",
        "reviewer_role",
        "signature_scheme_id",
        "ordered_criterion_results",
    }
    for key, value in response.items():
        if key not in fixed_response:
            assert value is None, (role, key, value)
    assert (
        tuple(item["criterion_id"] for item in response["ordered_criterion_results"])
        == dict(_ROLE_COVERAGE)[role]
    )
    assert all(
        item["disposition"] is None
        and item["finding_ids"] is None
        and item["comment_sha256"] is None
        and item["row_sha256"] is None
        for item in response["ordered_criterion_results"]
    )
    key_template = template["reviewer_public_key_template"]
    assert key_template["schema_version"] == _PUBLIC_KEY_SCHEMA
    assert key_template["reviewer_role"] == role
    assert key_template["signature_scheme_id"] == _SIGNATURE_SCHEME
    assert key_template["public_exponent"] == 65_537
    assert all(
        value is None
        for key, value in key_template.items()
        if key
        not in {
            "schema_version",
            "reviewer_role",
            "signature_scheme_id",
            "public_exponent",
        }
    )
    for name in ("authority_and_trust_template", "reviewer_signoff_template"):
        nested = template[name]
        assert nested["template_only"] is True
        assert nested["issued"] is False
        assert nested["reviewer_role"] == role
    assert template["external_review_performed"] is False
    assert template["external_reviewer_authority_verified"] is False
    assert template["candidate_descriptor_acceptance_effective"] is False
    assert template["schema_acceptance_effective"] is False
    assert (
        template[
            "subsequent_candidate_descriptor_development_qualification_construction_permitted"
        ]
        is False
    )
    assert template["production_execution_authorized"] is False
    assert template["acceptance_effect"] == "NONE"
    body = dict(template)
    digest = body["template_sha256"]
    body["template_sha256"] = _ZERO
    assert (
        digest
        == hashlib.sha256(
            b"cp75-test28-production-schema-acceptance-reviewer-unissued-template-v1\0"
            + _canonical(body)
        ).hexdigest()
    )


def test_templates_are_role_distinct_and_have_no_external_material() -> None:
    templates = (
        cp75.cp75_production_schema_acceptance_reviewer_unissued_template_bytes()
    )
    assert len(templates) == len(set(templates)) == 4
    forbidden_keys = {
        "reviewer_signature_hex",
        "reviewer_signature_sha256",
        "response_sha256",
        "reviewer_identity_sha256",
        "reviewer_organization_sha256",
        "modulus_hex",
        "key_identity_sha256",
        "document_sha256",
        "authority_signature_hex",
        "authority_signature_sha256",
        "signoff_packet_sha256",
    }
    for payload in templates:
        root = _json(payload)
        stack = [root]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in forbidden_keys:
                        assert item is None
                    stack.append(item)
            elif isinstance(value, list):
                stack.extend(value)


def test_contract_vectors_are_nonreviewer_math_only_and_digest_valid() -> None:
    body = _json(
        cp75.cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes()
    )
    assert body["schema_version"] == _VECTORS_SCHEMA
    assert body["test_vector_only"] is True
    assert body["authority_effect"] == "NONE"
    assert body["all_vectors_nonreviewer_test_only"] is True
    assert tuple(map(tuple, body["allowed_disposition_pairs"])) == _ALLOWED_PAIRS
    digest = body["body_sha256"]
    body["body_sha256"] = _ZERO
    assert (
        digest
        == hashlib.sha256(
            b"cp75-test28-production-schema-acceptance-review-response-contract-and-test-vectors-v1\0"
            + _canonical(body)
        ).hexdigest()
    )


def test_all_three_rsa_vectors_match_independent_pss_math_and_domain_claims() -> None:
    body = _json(
        cp75.cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes()
    )
    vectors = body["rsa_pss_math_vectors"]
    assert tuple(item["vector_id"] for item in vectors) == (
        "exact-production-domain-positive-untrusted-math-only",
        "bit-flipped-signature-negative",
        "different-domain-negative",
    )
    for vector in vectors:
        domain = vector["message_domain_id"].encode("ascii") + b"\0"
        message = domain + _canonical(
            vector["unsigned_response_signature_preimage_object"]
        )
        assert (
            _pss_verify(message, vector["signature_hex"], vector["modulus_hex"])
            is vector["expected_signature_math_valid"]
        )
        assert vector["synthetic_untrusted_subject_identity_and_key"] is True
        assert vector["authority_effect"] == "NONE"
        assert vector["trust_or_authority_asserted"] is False
    assert vectors[0]["uses_exact_production_response_signature_domain"] is True
    assert vectors[1]["uses_exact_production_response_signature_domain"] is True
    assert vectors[2]["uses_exact_production_response_signature_domain"] is False


def test_canonical_records_are_ascii_duplicate_free_and_float_free() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    records = (
        bundle.review_subject,
        *bundle.ordered_review_criteria,
        bundle.response_contract,
        *bundle.ordered_packet_artifacts,
        bundle,
    )
    duplicates: List[str] = []

    def hook(pairs: List[Tuple[str, object]]) -> dict:
        names = [name for name, _value in pairs]
        if len(names) != len(set(names)):
            duplicates.extend(names)
        return dict(pairs)

    def reject_float(value: str) -> object:
        raise AssertionError("float in CP75 canonical JSON: %s" % value)

    for record in records:
        payload = cp75.cp75_canonical_json_bytes(record)
        assert payload == _canonical(record)
        assert payload.isascii()
        json.loads(
            payload.decode("ascii"),
            object_pairs_hook=hook,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
    for path in _STATIC_PATHS[1:]:
        payload = (_ROOT / path).read_bytes()
        json.loads(
            payload.decode("ascii"),
            object_pairs_hook=hook,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
    assert duplicates == []


@pytest.mark.parametrize("value", ({}, [], (), b"", "", 0, False, None, object()))
def test_record_apis_reject_wrong_types(value: object) -> None:
    for function in (
        cp75.cp75_canonical_json_bytes,
        cp75.cp75_record_sha256,
        cp75.cp75_public_record_sha256,
    ):
        with pytest.raises(TypeError, match="CP75_RECORD_TYPE_MISMATCH"):
            function(value)


def test_record_apis_reject_unissued_records_and_pickle() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    unissued = _unissued_copy(bundle.response_contract)
    for function in (
        cp75.cp75_canonical_json_bytes,
        cp75.cp75_record_sha256,
        cp75.cp75_public_record_sha256,
    ):
        with pytest.raises(TypeError, match="CP75_RECORD_NOT_ISSUED"):
            function(unissued)
    with pytest.raises(TypeError, match="not pickle"):
        pickle.dumps(bundle)
    alien = object.__new__(cp75._SealedRecord)
    with pytest.raises(TypeError, match="CP75_RECORD_TYPE_MISMATCH"):
        cp75.cp75_canonical_json_bytes(alien)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("request_state", "TAMPERED"),
        ("production_gate_states", ["MISSING"] * 17),
        ("review_subject", None),
        ("ordered_review_criteria", ()),
    ),
)
def test_record_apis_reject_value_type_and_nested_identity_tamper(
    field: str, replacement: object
) -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    original = getattr(bundle, field)
    object.__setattr__(bundle, field, replacement)
    try:
        for function in (
            cp75.cp75_canonical_json_bytes,
            cp75.cp75_record_sha256,
            cp75.cp75_public_record_sha256,
        ):
            with pytest.raises(TypeError, match="CP75_RECORD_TAMPERED"):
                function(bundle)
    finally:
        object.__setattr__(bundle, field, original)


def test_record_apis_reject_deleted_and_serialization_breaking_tamper() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    subject = bundle.review_subject
    original_schema = subject.schema_version
    object.__delattr__(subject, "schema_version")
    try:
        with pytest.raises(TypeError, match="CP75_RECORD_TAMPERED"):
            cp75.cp75_canonical_json_bytes(subject)
    finally:
        object.__setattr__(subject, "schema_version", original_schema)
    original_state = bundle.request_state
    object.__setattr__(bundle, "request_state", object())
    try:
        with pytest.raises(TypeError, match="CP75_RECORD_TAMPERED"):
            cp75.cp75_canonical_json_bytes(bundle)
    finally:
        object.__setattr__(bundle, "request_state", original_state)


def test_nested_record_replacement_with_equal_primitive_mapping_is_tamper() -> None:
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    original = bundle.review_subject
    replacement = _plain(original)
    object.__setattr__(bundle, "review_subject", replacement)
    try:
        with pytest.raises(TypeError, match="CP75_RECORD_TAMPERED"):
            cp75.cp75_canonical_json_bytes(bundle)
    finally:
        object.__setattr__(bundle, "review_subject", original)


def test_weak_registry_releases_complete_bundle_graph() -> None:
    gc.collect()
    with cp75._ISSUED_LOCK:
        baseline = len(cp75._ISSUED)
    bundle = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    bundle_ref = weakref.ref(bundle)
    subject_ref = weakref.ref(bundle.review_subject)
    criterion_ref = weakref.ref(bundle.ordered_review_criteria[0])
    del bundle
    gc.collect()
    assert bundle_ref() is None
    assert subject_ref() is None
    assert criterion_ref() is None
    with cp75._ISSUED_LOCK:
        assert len(cp75._ISSUED) == baseline


def test_builder_failure_issues_no_bundle_and_leaves_no_dynamic_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gc.collect()
    with cp75._ISSUED_LOCK:
        baseline = len(cp75._ISSUED)

    def fail(*_args: object) -> None:
        raise RuntimeError("injected-definition-drift")

    monkeypatch.setattr(cp75, "_validate_internal_definition", fail)
    with pytest.raises(RuntimeError, match="injected-definition-drift"):
        cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    gc.collect()
    with cp75._ISSUED_LOCK:
        assert len(cp75._ISSUED) == baseline


def test_builder_actually_runs_deep_rsa_vector_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def fail() -> None:
        calls.append("called")
        raise RuntimeError("injected-rsa-vector-drift")

    monkeypatch.setattr(cp75, "_validate_rsa_math_vectors_internal", fail)
    with pytest.raises(RuntimeError, match="injected-rsa-vector-drift"):
        cp75.cp75_build_production_schema_acceptance_review_request_bundle()
    assert calls == ["called"]


@pytest.mark.parametrize(
    "exception", (MemoryError(), KeyboardInterrupt(), SystemExit(), GeneratorExit())
)
def test_builder_does_not_swallow_memory_or_control_flow(
    monkeypatch: pytest.MonkeyPatch, exception: BaseException
) -> None:
    def fail() -> object:
        raise exception

    monkeypatch.setattr(cp75, "_build_components", fail)
    with pytest.raises(type(exception)):
        cp75.cp75_build_production_schema_acceptance_review_request_bundle()


def test_builder_and_record_registry_are_thread_safe() -> None:
    with ThreadPoolExecutor(max_workers=8) as executor:
        bundles = list(
            executor.map(
                lambda _index: cp75.cp75_build_production_schema_acceptance_review_request_bundle(),
                range(24),
            )
        )
        canonical = list(executor.map(cp75.cp75_canonical_json_bytes, bundles))
        public = list(executor.map(cp75.cp75_public_record_sha256, bundles))
    assert len({id(item) for item in bundles}) == 24
    assert len({item.record_sha256 for item in bundles}) == 1
    assert len(set(canonical)) == 1
    assert len(set(public)) == 1


def test_source_has_no_duplicate_literal_mapping_keys() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"), filename=str(_SOURCE))
    duplicates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        names = [
            key.value
            for key in node.keys
            if isinstance(key, ast.Constant) and type(key.value) is str
        ]
        if len(names) != len(set(names)):
            duplicates.append(names)
    assert duplicates == []


def test_locked_python39_import_build_and_static_getters() -> None:
    if not _PYTHON39.is_file():
        pytest.skip("locked Python 3.9 executable is unavailable")
    script = r"""
import heterodiff.evaluation.mixed_initializer_test28_production_schema_acceptance_review_request as cp75
b = cp75.cp75_build_production_schema_acceptance_review_request_bundle()
assert len(cp75.__all__) == 32
assert len(b.ordered_review_criteria) == 12
assert len(b.ordered_packet_artifacts) == 6
assert len(cp75.cp75_production_schema_acceptance_reviewer_unissued_template_bytes()) == 4
assert b.current_subject_production_executable_schema_acceptance_eligible is False
assert b.production_execution_authorized is False
print("cp75-authoritative-python39-ok")
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
    assert result.stdout.strip() == "cp75-authoritative-python39-ok"
