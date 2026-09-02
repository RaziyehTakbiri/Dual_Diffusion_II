"""Hostile tests for the independent CP75 supplied-response validator."""

from __future__ import annotations

import ast
import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
import gc
import hashlib
import inspect
import json
import math
from pathlib import Path
import pickle
import subprocess
from typing import Dict, List, Tuple
import weakref

import heterodiff.evaluation.mixed_initializer_test28_independent_production_schema_acceptance_review_response_validator as cp75i
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_independent_production_schema_acceptance_review_response_validator.py"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")

_SCHEMA = (
    "cp75-test28-independent-production-schema-acceptance-review-response-"
    "validator-v1"
)
_REQUEST_SCHEMA = "cp75-test28-production-schema-acceptance-review-request-v1"
_RESPONSE_SCHEMA = "cp75-test28-production-schema-acceptance-review-response-v1"
_PUBLIC_KEY_SCHEMA = (
    "cp75-test28-production-schema-acceptance-reviewer-public-key-document-v1"
)
_CUSTODY_SCHEMA = "cp75-test28-independent-review-packet-custody-v1"
_SUMMARY_SCHEMA = (
    "cp75-test28-independent-supplied-review-response-validation-summary-v1"
)
_SIGNATURE_SCHEME = "rsa-pss-sha256-3072-e65537-salt32-v1"
_ZERO = "0" * 64

_ALL = (
    "CP75_INDEPENDENT_TEST28_SCHEMA_VERSION",
    "CP75_INDEPENDENT_TEST28_SCOPE",
    "CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_REQUEST_BYTES",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_MANIFEST_BYTES",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_RESPONSE_BYTES",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_PUBLIC_KEY_BYTES",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_TOTAL_INPUT_BYTES",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS",
    "CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS",
    "CP75_INDEPENDENT_TEST28_REVIEWER_ROLES",
    "CP75_INDEPENDENT_TEST28_CRITERION_IDS",
    "CP75_INDEPENDENT_TEST28_ERROR_CODES",
    "CP75_INDEPENDENT_TEST28_VALIDATION_PHASE_ORDER",
    "CP75IndependentReviewResponseValidationError",
    "CP75IndependentReviewPacketCustodyV1",
    "CP75IndependentSuppliedReviewResponseValidationSummaryV1",
    "CP75IndependentReviewResponseValidatorBundleV1",
    "cp75_build_independent_review_response_validator_bundle",
    "cp75_validate_supplied_external_review_response",
    "cp75_independent_canonical_json_bytes",
    "cp75_independent_record_sha256",
    "cp75_independent_public_record_sha256",
)
_ERRORS = (
    "CP75_INPUT_TYPE_MISMATCH",
    "CP75_INPUT_BYTE_LIMIT",
    "CP75_INPUT_ENCODING_INVALID",
    "CP75_INPUT_JSON_INVALID",
    "CP75_INPUT_RESOURCE_LIMIT",
    "CP75_INPUT_CANONICAL_MISMATCH",
    "CP75_INPUT_FIELD_SET_MISMATCH",
    "CP75_INPUT_FIELD_TYPE_MISMATCH",
    "CP75_INPUT_SCHEMA_MISMATCH",
    "CP75_INPUT_REQUEST_MISMATCH",
    "CP75_INPUT_MANIFEST_MISMATCH",
    "CP75_INPUT_INVENTORY_MISMATCH",
    "CP75_INPUT_DIGEST_MISMATCH",
    "CP75_INPUT_BINDING_MISMATCH",
    "CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH",
    "CP75_INPUT_SIGNATURE_MISMATCH",
    "CP75_INPUT_RSA_PSS_MISMATCH",
    "CP75_INPUT_DISPOSITION_MISMATCH",
    "CP75_RESOURCE_EXHAUSTED",
    "CP75_RECORD_TYPE_MISMATCH",
    "CP75_RECORD_NOT_ISSUED",
    "CP75_RECORD_TAMPERED",
    "CP75_INTERNAL_INVARIANT_FAILED",
)
_PHASES = (
    "exact-built-in-bytes-input-types",
    "per-input-byte-limits",
    "cumulative-input-byte-limit",
    "utf8-decoding",
    "lexical-depth-and-resource-preflight",
    "json-parsing",
    "canonical-json-byte-equality",
    "root-field-set-and-type-grammar",
    "schema-version-grammar",
    "exact-request-and-seven-entry-manifest-reconstruction",
    "response-public-key-and-criterion-inventories",
    "all-individual-and-ordered-record-digests",
    "request-subject-scope-context-and-attachment-bindings",
    "public-key-identity-organization-and-validity-interval-coherence",
    "signature-length-and-plain-sha256",
    "rsa-pss-sha256-3072-e65537-salt32-mathematics",
    "two-axis-disposition-and-current-subject-scope-rules",
    "sealed-structural-summary-issuance",
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
_OPEN_ITEMS = (
    "primary-threshold-comparison-operator",
    "primary-threshold-comparison-direction",
    "primary-threshold-value-law",
    "primary-selected-count-justification",
    "primary-32-slot-decision-function",
    "decision-timestamp-authority",
)
_PATHS = (
    "research/preregistrations/cp75_test28_production_schema_acceptance_review_checklist_v1.md",
    "research/fixtures/cp75_test28_production_schema_acceptance_review_response_contract_and_test_vectors_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_protocol_and_provenance_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_runtime_and_durability_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_statistical_power_and_decision_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_independent_recomputation_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_review_request_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_review_packet_manifest_v1.json",
)

_CUSTODY_FIELDS = (
    "schema_version",
    "source_request_schema_version",
    "source_response_schema_version",
    "source_public_key_schema_version",
    "request_path",
    "request_canonical_json_bytes",
    "request_canonical_json_sha256",
    "request_record_sha256",
    "subject_record_sha256",
    "checklist_path",
    "checklist_bytes",
    "checklist_lf_count",
    "checklist_sha256",
    "response_contract_test_vectors_path",
    "response_contract_test_vectors_bytes",
    "response_contract_test_vectors_sha256",
    "reviewer_template_paths",
    "reviewer_template_bytes",
    "reviewer_template_sha256s",
    "manifest_path",
    "manifest_canonical_json_bytes",
    "manifest_canonical_json_sha256",
    "manifest_record_sha256",
    "reviewer_roles",
    "criterion_ids",
    "role_criterion_coverage",
    "signature_scheme_id",
    "request_and_manifest_oracle_deeply_reconstructed",
    "project_modules_imported",
    "path_io_performed",
    "record_sha256",
)
_SUMMARY_FIELDS = (
    "schema_version",
    "source_request_schema_version",
    "source_response_schema_version",
    "source_public_key_schema_version",
    "request_input_bytes",
    "request_input_sha256",
    "manifest_input_bytes",
    "manifest_input_sha256",
    "response_input_bytes",
    "response_input_sha256",
    "public_key_input_bytes",
    "public_key_input_sha256",
    "reviewer_role",
    "candidate_descriptor_disposition",
    "production_executable_schema_disposition",
    "acknowledged_subject_open_item_ids",
    "criterion_result_count",
    "request_exactly_reconstructed",
    "manifest_exactly_reconstructed",
    "response_canonical",
    "public_key_canonical",
    "response_field_grammar_valid",
    "public_key_field_grammar_valid",
    "criterion_coverage_complete",
    "criterion_result_digests_valid",
    "response_record_digest_valid",
    "request_subject_scope_context_and_attachment_bindings_valid",
    "public_key_document_sha256_binding_valid",
    "public_key_identity_formula_valid",
    "reviewer_organization_binding_valid",
    "validity_interval_coherence_valid",
    "reviewer_signature_sha256_valid",
    "rsa_pss_signature_math_valid",
    "allowed_disposition_pair_valid",
    "current_subject_scope_rules_valid",
    "full_review_report_bytes_verified",
    "review_method_execution_verified",
    "supersession_relation_verified",
    "withdrawal_relation_verified",
    "conflict_status_verified",
    "reviewer_identity_authenticated",
    "external_trust_root_verified",
    "reviewer_authority_verified",
    "authority_appointment_verified",
    "conflict_of_interest_attestation_verified",
    "independence_attestation_verified",
    "revocation_status_verified",
    "validity_at_trusted_time_verified",
    "external_attachment_bytes_verified",
    "external_review_performed",
    "response_eligible_for_candidate_descriptor_acceptance",
    "response_eligible_for_production_schema_acceptance",
    "candidate_descriptor_acceptance_effective",
    "schema_acceptance_independent",
    "schema_acceptance_effective",
    "subsequent_candidate_descriptor_development_qualification_construction_permitted",
    "production_execution_authorized",
    "production_gate_states",
    "draft_blocker_states",
    "formal_test_28_status",
    "caller_input_bytes_retained_after_successful_return",
    "record_sha256",
)
_BUNDLE_FIELDS = (
    "schema_version",
    "scope",
    "predecessor_custody",
    "maximum_request_bytes",
    "maximum_manifest_bytes",
    "maximum_response_bytes",
    "maximum_public_key_bytes",
    "maximum_total_input_bytes",
    "maximum_json_depth",
    "maximum_json_nodes",
    "maximum_object_members",
    "maximum_array_items",
    "maximum_key_characters",
    "maximum_text_item_characters",
    "maximum_decoded_text_characters",
    "maximum_integer_decimal_digits",
    "error_codes",
    "validation_phase_order",
    "one_response_per_call",
    "exact_request_bytes_required",
    "exact_manifest_bytes_required",
    "response_structure_and_signature_math_validator_available",
    "external_attachment_validator_available",
    "trust_authority_time_revocation_or_aggregation_validator_available",
    "project_modules_imported",
    "path_io_performed",
    "key_generation_performed",
    "signing_performed",
    "response_issuance_performed",
    "external_review_performed",
    "candidate_descriptor_acceptance_effective",
    "schema_acceptance_effective",
    "subsequent_candidate_descriptor_development_qualification_construction_permitted",
    "production_execution_authorized",
    "production_gate_states",
    "draft_blocker_states",
    "formal_test_28_status",
    "builder_validates_internal_definition",
    "record_sha256",
)
_LAYOUTS = (
    (cp75i.CP75IndependentReviewPacketCustodyV1, _CUSTODY_FIELDS),
    (cp75i.CP75IndependentSuppliedReviewResponseValidationSummaryV1, _SUMMARY_FIELDS),
    (cp75i.CP75IndependentReviewResponseValidatorBundleV1, _BUNDLE_FIELDS),
)

_RESPONSE_KEYS = (
    "schema_version",
    "request_schema_version",
    "request_canonical_json_sha256",
    "request_record_sha256",
    "subject_record_sha256",
    "review_packet_manifest_canonical_json_sha256",
    "review_packet_manifest_record_sha256",
    "checklist_sha256",
    "response_contract_test_vectors_sha256",
    "review_round_ordinal",
    "review_context_sha256",
    "acceptance_target",
    "scope_and_nonclaims_sha256",
    "reviewer_role",
    "reviewer_identity_sha256",
    "reviewer_organization_sha256",
    "reviewer_public_key_identity_sha256",
    "reviewer_public_key_document_sha256",
    "signature_scheme_id",
    "trust_policy_id",
    "authority_id",
    "reviewer_authority_attestation_sha256",
    "appointment_evidence_sha256",
    "conflict_of_interest_attestation_sha256",
    "independence_attestation_sha256",
    "revocation_status_receipt_sha256",
    "review_method_ids",
    "review_toolchain_sha256",
    "full_review_report_sha256",
    "ordered_criterion_results",
    "ordered_criterion_result_sha256s",
    "ordered_criterion_results_sha256",
    "open_finding_ids",
    "required_change_ids",
    "acknowledged_subject_open_item_ids",
    "review_notes_sha256",
    "candidate_descriptor_disposition",
    "production_executable_schema_disposition",
    "signed_at_utc",
    "valid_from_utc",
    "valid_until_utc",
    "supersedes_response_sha256",
    "withdraws_response_sha256",
    "reviewer_signature_sha256",
    "reviewer_signature_hex",
    "response_sha256",
)
_PUBLIC_KEY_KEYS = (
    "schema_version",
    "reviewer_role",
    "reviewer_identity_sha256",
    "reviewer_organization_sha256",
    "signature_scheme_id",
    "authority_id",
    "modulus_hex",
    "public_exponent",
    "valid_from_utc",
    "valid_until_utc",
    "key_identity_sha256",
    "document_sha256",
)
_SUMMARY_FIXTURE_PINS = (
    (
        _ROLES[0],
        3_431,
        "334c03ef91c45d345af04d92c9f127cc0dd85276a9fd25e15484daf2d6303d84",
        "311a5e06bd902f518b5218ee0f1d955ec4a8c8dfa33fe27214e0eeaeefe772b5",
    ),
    (
        _ROLES[1],
        3_431,
        "e6050a30cf68d826d06e41b5265a4c44c13aa83518b4fa24a74e71224745c77a",
        "a089a8939d5f4c3d84a5fa01bcae91dac284a787551095c4d54fbc8614221ea4",
    ),
    (
        _ROLES[2],
        3_436,
        "0b7fc41064d5dc4253ab46f6a161752a545fead44d3142e80a7797560136a2b6",
        "b9553e8515609b505414c1e2c582a2008a7a3da001427a992ce138570db46698",
    ),
    (
        _ROLES[3],
        3_431,
        "61c5fefb5ac2c55e056ffe360cf16207f04a98dada3c46b849e68a3a283e5d0f",
        "cb3ba5624b4b7ede6e36c55bd30375ea31ca5c01521ccce1380d4c11d64fafbd",
    ),
    (
        "withdraw",
        3_193,
        "5d3f152370a4d4b8357a546a1ae29992dd1b1c956b590a829254101d960d2d6b",
        "1d0f1c31d7e63829ac6c2b36f2ddb65685655b7c839660cf63d0c49456ad9b5b",
    ),
)
_SUMMARY_FIXTURE_SET_SHA256 = (
    "79ea66d454a5ff8d1fa57e3bf880efa4cd8f5c5daea3f72211b592ae450c9e28"
)

# Test-owned synthetic 3072-bit RSA key.  It is never an authority or trust root.
_RSA_N_HEX = (
    "d0cf33ae007929164127785d96972557300f7fd58c7eebbd3dd670f2d27851e4"
    "de1befdc6c3f2adcbbd72a866335c9ed14fe6edb4ff6ec0a6db8f390bda4c122"
    "76e322628b4065678f8d43711b5ca6b200383abc2415ec3bc476885d61d091729"
    "1b3fb0d0d06a6567ff276a66fc51b5576b777341d39f5b2fe99afa6f4fa2f0d"
    "65927e094e310b6d6a0e20bf2369ddaa0766213895ce559907cbb561cabc45547"
    "de982ffd0dc2dbe9387b970ff4e3d1bd2c4fe6ab7032e167ab38eaf0b79e1a479"
    "90a4cd018939ae9b0a4d149a3df9e58e13180958a030e9cf9a22b34793651acd7"
    "6551baac82dd91e0db73e1599f5a3ea01c1250a167e771a9c9ff287384e041fbe"
    "cdde3cfa78229e3f55b629bcdfc23536e0d241ca0f490e3d838d87fed75147815"
    "413964b6c0ecec5e075274997f5b39fdd1e18c843b287ba3ac143105339838021"
    "3ce30059dbf1ef796039af7d00e63bae9ac3e6b74dc7b552996cc21d9b313c0e4"
    "49f8d97abaa58f8da356ff23a2411ee3e07557399602f76a6fe9b3ff3"
)
_RSA_D_HEX = (
    "340ee4708617aee1a87ec1a87b89d53a667606c5e3d024cfba620328d6c63e8c"
    "93bf5d4e94022f9a768e4f40cfed32199479568400ecabae71ea8176dd80fcd1a"
    "dd834d362aa3c5dd45140b62b3f2f2403a0012cb4c66e6dfc2e1d1342f6afbc6"
    "38cfe9323633c0726c0f949c765d9c9b5de49aec97690c5fe69ac7c30694b5fc"
    "8a9fc182fd1546b03dcdfd7276a16647491c6c887b8b8687da410e57f98eea400"
    "fc3db7af87a533f52e0a529ca411e224eb0e0ee6efb906cbb2866927b04c4bb47"
    "c2dad579835951d99ab3df9f3b2d159decf0d69438f0d12f88079d502008a7deb"
    "6efc919af9541a87192babfb08ee1184e540eebcdb1040706ab5c5c2332e6b028"
    "db847f784a6e809126f3dc5fe145ce08c977d53c9355f8f259235d8e99272af9f"
    "5d3f12017673df3dfa6cd12b657c665b45de1d3433975736175495922358865f83"
    "1e914702e141e81cc8f51c3bd56dfd9c5d1a76ba74d5316dd0ebbd3290173b370"
    "5ed3f1002053bedcc373b97464d927f8a9d6f836c381332230db129"
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _zero_digest(body: Dict[str, object], carrier: str, domain: bytes) -> None:
    body[carrier] = _ZERO
    body[carrier] = hashlib.sha256(domain + _canonical(body)).hexdigest()


def _ordered(domain: bytes, digests: Tuple[str, ...]) -> str:
    return hashlib.sha256(
        domain + b"".join(bytes.fromhex(item) for item in digests)
    ).hexdigest()


def _mgf1(seed: bytes, length: int) -> bytes:
    output = bytearray()
    for counter in range(math.ceil(length / 32)):
        output.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
    return bytes(output[:length])


def _pss_sign(message: bytes, salt_label: str) -> bytes:
    salt = hashlib.sha256(salt_label.encode("ascii")).digest()
    message_hash = hashlib.sha256(message).digest()
    encoded_hash = hashlib.sha256(b"\0" * 8 + message_hash + salt).digest()
    data_block = b"\0" * 318 + b"\x01" + salt
    mask = _mgf1(encoded_hash, 351)
    masked = bytes(left ^ right for left, right in zip(data_block, mask))
    masked = bytes([masked[0] & 0x7F]) + masked[1:]
    encoded = masked + encoded_hash + b"\xbc"
    signature = pow(
        int.from_bytes(encoded, "big"), int(_RSA_D_HEX, 16), int(_RSA_N_HEX, 16)
    )
    return signature.to_bytes(384, "big")


def _packet() -> Tuple[bytes, bytes, Dict[str, object], Dict[str, object]]:
    request_bytes = (_ROOT / _PATHS[6]).read_bytes()
    manifest_bytes = (_ROOT / _PATHS[7]).read_bytes()
    return (
        request_bytes,
        manifest_bytes,
        json.loads(request_bytes.decode("ascii")),
        json.loads(manifest_bytes.decode("ascii")),
    )


def _rebind_packet_after_internal_drift(
    packet: Dict[str, bytes],
) -> Dict[str, bytes]:
    """Keep every enclosing digest coherent so only deep oracle checks can fail."""
    request = json.loads(packet[_PATHS[6]])
    artifacts = request["ordered_packet_artifacts"]
    for artifact, path in zip(artifacts, _PATHS[:6]):
        content = packet[path]
        artifact["content_bytes"] = len(content)
        artifact["lf_count"] = content.count(b"\n")
        artifact["content_sha256"] = hashlib.sha256(content).hexdigest()
        _zero_digest(
            artifact,
            "record_sha256",
            b"cp75-test28-production-schema-acceptance-review-packet-artifact-v1\0",
        )
    subject = request["review_subject"]
    _zero_digest(
        subject,
        "subject_sha256",
        b"cp75-test28-production-schema-acceptance-review-subject-v1\0",
    )
    criteria = request["ordered_review_criteria"]
    for criterion in criteria:
        _zero_digest(
            criterion,
            "record_sha256",
            b"cp75-test28-production-schema-acceptance-review-criterion-v1\0",
        )
    criterion_digests = tuple(item["record_sha256"] for item in criteria)
    request["ordered_review_criterion_record_sha256s"] = list(criterion_digests)
    request["ordered_review_criteria_sha256"] = _ordered(
        b"cp75-test28-production-schema-acceptance-review-criterion-record-digests-v1\0",
        criterion_digests,
    )
    _zero_digest(
        request["response_contract"],
        "record_sha256",
        b"cp75-test28-production-schema-acceptance-review-response-contract-v1\0",
    )
    artifact_digests = tuple(item["record_sha256"] for item in artifacts)
    request["ordered_packet_artifact_record_sha256s"] = list(artifact_digests)
    request["ordered_packet_artifacts_sha256"] = _ordered(
        b"cp75-test28-production-schema-acceptance-review-packet-artifact-record-digests-v1\0",
        artifact_digests,
    )
    _zero_digest(
        request,
        "record_sha256",
        b"cp75-test28-production-schema-acceptance-review-request-v1\0",
    )
    request_bytes = _canonical(request)
    packet[_PATHS[6]] = request_bytes

    manifest = json.loads(packet[_PATHS[7]])
    entries = manifest["ordered_packet_files"]
    for entry, path in zip(entries, _PATHS[:7]):
        content = packet[path]
        entry["content_bytes"] = len(content)
        entry["lf_count"] = content.count(b"\n")
        entry["content_sha256"] = hashlib.sha256(content).hexdigest()
        _zero_digest(
            entry,
            "entry_sha256",
            b"cp75-test28-production-schema-acceptance-review-packet-file-v1\0",
        )
    entry_digests = tuple(item["entry_sha256"] for item in entries)
    manifest["ordered_packet_file_record_sha256s"] = list(entry_digests)
    manifest["ordered_packet_files_sha256"] = _ordered(
        b"cp75-test28-production-schema-acceptance-review-packet-file-record-digests-v1\0",
        entry_digests,
    )
    manifest["request_canonical_json_bytes"] = len(request_bytes)
    manifest["request_canonical_json_sha256"] = hashlib.sha256(
        request_bytes
    ).hexdigest()
    manifest["request_record_sha256"] = request["record_sha256"]
    _zero_digest(
        manifest,
        "manifest_sha256",
        b"cp75-test28-production-schema-acceptance-review-packet-manifest-v1\0",
    )
    packet[_PATHS[7]] = _canonical(manifest)
    return packet


def _coherent_deep_oracle_drift(kind: str) -> Dict[str, bytes]:
    packet = dict(cp75i._packet_oracle())
    if kind == "checklist":
        packet[_PATHS[0]] += b"\n<!-- coherent-but-unauthorized-checklist-drift -->\n"
    elif kind == "vectors":
        vectors = json.loads(packet[_PATHS[1]])
        vectors["all_vectors_nonreviewer_test_only"] = False
        _zero_digest(
            vectors,
            "body_sha256",
            b"cp75-test28-production-schema-acceptance-review-response-contract-and-test-vectors-v1\0",
        )
        packet[_PATHS[1]] = _canonical(vectors)
    elif kind == "template":
        template = json.loads(packet[_PATHS[2]])
        template["response_template"]["reviewer_identity_sha256"] = _sha(
            "unauthorized-template-identity"
        )
        _zero_digest(
            template,
            "template_sha256",
            b"cp75-test28-production-schema-acceptance-reviewer-unissued-template-v1\0",
        )
        packet[_PATHS[2]] = _canonical(template)
    elif kind == "criterion":
        request = json.loads(packet[_PATHS[6]])
        request["ordered_review_criteria"][-1][
            "blocking_for_candidate_descriptor_acceptance"
        ] = True
        packet[_PATHS[6]] = _canonical(request)
    elif kind == "response-contract":
        request = json.loads(packet[_PATHS[6]])
        request["response_contract"]["required_reviewer_count"] = 3
        packet[_PATHS[6]] = _canonical(request)
    else:
        raise AssertionError("unknown CP75 deep-oracle drift")
    return _rebind_packet_after_internal_drift(packet)


def _public_key(role: str) -> Tuple[Dict[str, object], bytes]:
    identity = _sha("cp75-test-reviewer-identity-" + role)
    organization = _sha("cp75-test-reviewer-organization-" + role)
    authority = "synthetic-untrusted-test-authority"
    key_identity_body = {
        "reviewer_role": role,
        "reviewer_identity_sha256": identity,
        "signature_scheme_id": _SIGNATURE_SCHEME,
        "authority_id": authority,
        "modulus_hex": _RSA_N_HEX,
        "public_exponent": 65_537,
    }
    key_identity = hashlib.sha256(
        b"cp65-test28-independent-reviewer-public-key-identity-v1\0"
        + _canonical(key_identity_body)
    ).hexdigest()
    body: Dict[str, object] = {
        "schema_version": _PUBLIC_KEY_SCHEMA,
        "reviewer_role": role,
        "reviewer_identity_sha256": identity,
        "reviewer_organization_sha256": organization,
        "signature_scheme_id": _SIGNATURE_SCHEME,
        "authority_id": authority,
        "modulus_hex": _RSA_N_HEX,
        "public_exponent": 65_537,
        "valid_from_utc": "2025-01-01T00:00:00Z",
        "valid_until_utc": "2030-01-01T00:00:00Z",
        "key_identity_sha256": key_identity,
        "document_sha256": _ZERO,
    }
    _zero_digest(
        body,
        "document_sha256",
        b"cp75-test28-production-schema-acceptance-reviewer-public-key-document-v1\0",
    )
    return body, _canonical(body)


def _refresh_response_digests_and_signature(
    response: Dict[str, object], role: str
) -> bytes:
    rows = response["ordered_criterion_results"]
    for row in rows:
        _zero_digest(
            row,
            "row_sha256",
            b"cp75-test28-production-schema-acceptance-review-criterion-result-v1\0",
        )
    row_digests = tuple(row["row_sha256"] for row in rows)
    response["ordered_criterion_result_sha256s"] = list(row_digests)
    response["ordered_criterion_results_sha256"] = _ordered(
        b"cp75-test28-production-schema-acceptance-review-criterion-result-record-digests-v1\0",
        row_digests,
    )
    response["reviewer_signature_hex"] = ""
    response["reviewer_signature_sha256"] = _ZERO
    response["response_sha256"] = _ZERO
    message = (
        b"cp75-test28-production-schema-acceptance-review-response-signature-preimage-v1\0"
        + _canonical(response)
    )
    signature = _pss_sign(message, "cp75-hostile-suite-salt-" + role)
    response["reviewer_signature_hex"] = signature.hex()
    response["reviewer_signature_sha256"] = hashlib.sha256(signature).hexdigest()
    _zero_digest(
        response,
        "response_sha256",
        b"cp75-test28-production-schema-acceptance-review-response-v1\0",
    )
    return _canonical(response)


def _valid_inputs(
    role: str = _ROLES[0], *, withdrawal: bool = False
) -> Tuple[bytes, bytes, bytes, bytes]:
    request_bytes, manifest_bytes, request, manifest = _packet()
    key, key_bytes = _public_key(role)
    subject = request["review_subject"]
    if withdrawal:
        rows: List[Dict[str, object]] = []
        open_findings: Tuple[str, ...] = ()
        changes: Tuple[str, ...] = ()
        acknowledged: Tuple[str, ...] = ()
        methods: Tuple[str, ...] = ()
        candidate = production = "WITHDRAW"
    else:
        rows = []
        for criterion_id in dict(_ROLE_COVERAGE)[role]:
            if criterion_id == _CRITERION_IDS[11]:
                disposition = "ABSTAIN" if role in _ROLES[:2] else "DEFER"
                findings = () if disposition == "ABSTAIN" else _OPEN_ITEMS
            else:
                disposition = "PASS"
                findings = ()
            rows.append(
                {
                    "criterion_id": criterion_id,
                    "disposition": disposition,
                    "finding_ids": list(findings),
                    "comment_sha256": _sha("cp75-comment-" + role + "-" + criterion_id),
                    "row_sha256": _ZERO,
                }
            )
        open_findings = () if role in _ROLES[:2] else _OPEN_ITEMS
        changes = open_findings
        acknowledged = _OPEN_ITEMS
        methods = ("independent-hostile-review-method",)
        candidate = "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY"
        production = "ABSTAIN" if role in _ROLES[:2] else "DEFER"
    response: Dict[str, object] = {
        "schema_version": _RESPONSE_SCHEMA,
        "request_schema_version": request["schema_version"],
        "request_canonical_json_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "request_record_sha256": request["record_sha256"],
        "subject_record_sha256": subject["subject_sha256"],
        "review_packet_manifest_canonical_json_sha256": hashlib.sha256(
            manifest_bytes
        ).hexdigest(),
        "review_packet_manifest_record_sha256": manifest["manifest_sha256"],
        "checklist_sha256": hashlib.sha256(
            (_ROOT / _PATHS[0]).read_bytes()
        ).hexdigest(),
        "response_contract_test_vectors_sha256": hashlib.sha256(
            (_ROOT / _PATHS[1]).read_bytes()
        ).hexdigest(),
        "review_round_ordinal": request["review_round_ordinal"],
        "review_context_sha256": request["review_context_sha256"],
        "acceptance_target": request["acceptance_target"],
        "scope_and_nonclaims_sha256": subject["scope_and_nonclaims_sha256"],
        "reviewer_role": role,
        "reviewer_identity_sha256": key["reviewer_identity_sha256"],
        "reviewer_organization_sha256": key["reviewer_organization_sha256"],
        "reviewer_public_key_identity_sha256": key["key_identity_sha256"],
        "reviewer_public_key_document_sha256": hashlib.sha256(key_bytes).hexdigest(),
        "signature_scheme_id": _SIGNATURE_SCHEME,
        "trust_policy_id": "synthetic-untrusted-test-policy",
        "authority_id": key["authority_id"],
        "reviewer_authority_attestation_sha256": _sha("authority-attestation-" + role),
        "appointment_evidence_sha256": _sha("appointment-" + role),
        "conflict_of_interest_attestation_sha256": _sha("coi-" + role),
        "independence_attestation_sha256": _sha("independence-" + role),
        "revocation_status_receipt_sha256": _sha("revocation-" + role),
        "review_method_ids": list(methods),
        "review_toolchain_sha256": _sha("toolchain-" + role),
        "full_review_report_sha256": _sha("report-" + role),
        "ordered_criterion_results": rows,
        "ordered_criterion_result_sha256s": [],
        "ordered_criterion_results_sha256": _ZERO,
        "open_finding_ids": list(open_findings),
        "required_change_ids": list(changes),
        "acknowledged_subject_open_item_ids": list(acknowledged),
        "review_notes_sha256": _sha("notes-" + role),
        "candidate_descriptor_disposition": candidate,
        "production_executable_schema_disposition": production,
        "signed_at_utc": "2026-06-01T00:00:01Z",
        "valid_from_utc": "2026-06-01T00:00:00Z",
        "valid_until_utc": "2027-06-01T00:00:00Z",
        "supersedes_response_sha256": None,
        "withdraws_response_sha256": _sha("withdraw-target-" + role)
        if withdrawal
        else None,
        "reviewer_signature_sha256": _ZERO,
        "reviewer_signature_hex": "",
        "response_sha256": _ZERO,
    }
    assert tuple(response) == _RESPONSE_KEYS
    assert tuple(key) == _PUBLIC_KEY_KEYS
    return (
        request_bytes,
        manifest_bytes,
        _refresh_response_digests_and_signature(response, role),
        key_bytes,
    )


def _decode_inputs(
    inputs: Tuple[bytes, bytes, bytes, bytes]
) -> Tuple[Dict[str, object], Dict[str, object]]:
    return json.loads(inputs[2].decode("ascii")), json.loads(inputs[3].decode("ascii"))


def _encode_key_and_rebind(
    response: Dict[str, object], key: Dict[str, object]
) -> Tuple[bytes, bytes]:
    _zero_digest(
        key,
        "document_sha256",
        b"cp75-test28-production-schema-acceptance-reviewer-public-key-document-v1\0",
    )
    key_bytes = _canonical(key)
    response["reviewer_public_key_document_sha256"] = hashlib.sha256(
        key_bytes
    ).hexdigest()
    return (
        _refresh_response_digests_and_signature(response, response["reviewer_role"]),
        key_bytes,
    )


def _assert_error(code: str, inputs: Tuple[object, object, object, object]) -> None:
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        cp75i.cp75_validate_supplied_external_review_response(*inputs)
    assert caught.value.code == code
    assert str(caught.value).startswith(code + ": ")


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


def test_public_surface_schemas_caps_errors_and_phase_order_are_exact() -> None:
    assert cp75i.__all__ == _ALL
    assert len(cp75i.__all__) == len(set(cp75i.__all__)) == 29
    assert cp75i.CP75_INDEPENDENT_TEST28_SCHEMA_VERSION == _SCHEMA
    assert (
        cp75i.CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION == _REQUEST_SCHEMA
    )
    assert cp75i._SOURCE_RESPONSE_SCHEMA_VERSION == _RESPONSE_SCHEMA
    assert cp75i._SOURCE_PUBLIC_KEY_SCHEMA_VERSION == _PUBLIC_KEY_SCHEMA
    assert (
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_REQUEST_BYTES,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_MANIFEST_BYTES,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_RESPONSE_BYTES,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_PUBLIC_KEY_BYTES,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_TOTAL_INPUT_BYTES,
    ) == (1_048_576, 262_144, 1_048_576, 65_536, 2_424_832)
    assert (
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS,
        cp75i.CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS,
    ) == (16, 65_536, 128, 4_096, 128, 65_536, 1_048_576, 20)
    assert cp75i.CP75_INDEPENDENT_TEST28_REVIEWER_ROLES == _ROLES
    assert cp75i.CP75_INDEPENDENT_TEST28_CRITERION_IDS == _CRITERION_IDS
    assert cp75i.CP75_INDEPENDENT_TEST28_ERROR_CODES == _ERRORS
    assert cp75i.CP75_INDEPENDENT_TEST28_VALIDATION_PHASE_ORDER == _PHASES


@pytest.mark.parametrize(("record_type", "expected_fields"), _LAYOUTS)
def test_record_layouts_are_exact(record_type: type, expected_fields: tuple) -> None:
    assert is_dataclass(record_type)
    assert tuple(item.name for item in fields(record_type)) == expected_fields
    assert record_type.__slots__ == expected_fields
    with pytest.raises(TypeError, match="module-created only"):
        record_type()
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("HostileSubclass", (record_type,), {})


def test_public_api_signatures_are_exact_and_narrow() -> None:
    assert (
        tuple(
            inspect.signature(
                cp75i.cp75_build_independent_review_response_validator_bundle
            ).parameters
        )
        == ()
    )
    signature = inspect.signature(cp75i.cp75_validate_supplied_external_review_response)
    assert tuple(signature.parameters) == (
        "request_json_bytes",
        "packet_manifest_json_bytes",
        "response_json_bytes",
        "reviewer_public_key_json_bytes",
    )
    for function in (
        cp75i.cp75_independent_canonical_json_bytes,
        cp75i.cp75_independent_record_sha256,
        cp75i.cp75_independent_public_record_sha256,
    ):
        assert tuple(inspect.signature(function).parameters) == ("record",)


def test_source_is_project_independent_stdlib_only_and_has_no_io_or_effects() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"), filename=str(_SOURCE))
    assert set(_import_roots(tree)) == {
        "__future__",
        "base64",
        "dataclasses",
        "datetime",
        "hashlib",
        "hmac",
        "json",
        "math",
        "re",
        "threading",
        "typing",
        "weakref",
        "zlib",
    }
    forbidden = {
        "open",
        "Path",
        "socket",
        "subprocess",
        "time",
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
    assert "heterodiff" not in _SOURCE.read_text(encoding="utf-8")


def test_static_oracle_exactly_matches_all_eight_external_packet_files() -> None:
    packet = cp75i._packet_oracle()
    assert tuple(packet) == _PATHS
    for path in _PATHS:
        assert packet[path] == (_ROOT / path).read_bytes()


def test_validator_bundle_is_deterministic_sealed_and_truthfully_non_effectful() -> None:
    first = cp75i.cp75_build_independent_review_response_validator_bundle()
    second = cp75i.cp75_build_independent_review_response_validator_bundle()
    assert (
        first is not second
        and first.predecessor_custody is not second.predecessor_custody
    )
    assert first.record_sha256 == second.record_sha256
    assert cp75i.cp75_independent_canonical_json_bytes(
        first
    ) == cp75i.cp75_independent_canonical_json_bytes(second)
    assert first.schema_version == _SCHEMA
    assert first.error_codes == _ERRORS
    assert first.validation_phase_order == _PHASES
    assert first.one_response_per_call is True
    assert first.exact_request_bytes_required is True
    assert first.exact_manifest_bytes_required is True
    assert first.response_structure_and_signature_math_validator_available is True
    assert first.builder_validates_internal_definition is True
    false_fields = (
        "external_attachment_validator_available",
        "trust_authority_time_revocation_or_aggregation_validator_available",
        "project_modules_imported",
        "path_io_performed",
        "key_generation_performed",
        "signing_performed",
        "response_issuance_performed",
        "external_review_performed",
        "candidate_descriptor_acceptance_effective",
        "schema_acceptance_effective",
        "subsequent_candidate_descriptor_development_qualification_construction_permitted",
        "production_execution_authorized",
    )
    assert all(getattr(first, name) is False for name in false_fields)
    assert first.production_gate_states == ("MISSING",) * 17
    assert first.draft_blocker_states == ("MISSING",) * 4
    assert first.formal_test_28_status == "OPEN"


def test_zero_argument_builder_deeply_validates_oracle_and_normalizes_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gc.collect()
    with cp75i._ISSUED_LOCK:
        baseline = len(cp75i._ISSUED)

    def invalid_oracle(*_args: object) -> object:
        raise cp75i.CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_DIGEST_MISMATCH", "injected oracle drift"
        )

    monkeypatch.setattr(cp75i, "_validate_packet_oracle", invalid_oracle)
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        cp75i.cp75_build_independent_review_response_validator_bundle()
    assert caught.value.code == "CP75_INTERNAL_INVARIANT_FAILED"
    gc.collect()
    with cp75i._ISSUED_LOCK:
        assert len(cp75i._ISSUED) == baseline


@pytest.mark.parametrize(
    "kind", ("checklist", "vectors", "template", "criterion", "response-contract")
)
def test_zero_argument_builder_rejects_coherently_rehashed_deep_oracle_drift(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    gc.collect()
    with cp75i._ISSUED_LOCK:
        baseline = len(cp75i._ISSUED)
    packet = _coherent_deep_oracle_drift(kind)
    monkeypatch.setattr(cp75i, "_packet_oracle", lambda: packet)
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        cp75i.cp75_build_independent_review_response_validator_bundle()
    assert caught.value.code == "CP75_INTERNAL_INVARIANT_FAILED"
    gc.collect()
    with cp75i._ISSUED_LOCK:
        assert len(cp75i._ISSUED) == baseline


def test_zero_argument_builder_normalizes_memory_and_reraises_control_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cp75i,
        "_packet_oracle",
        lambda: (_ for _ in ()).throw(MemoryError()),
    )
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        cp75i.cp75_build_independent_review_response_validator_bundle()
    assert caught.value.code == "CP75_RESOURCE_EXHAUSTED"
    for exception in (KeyboardInterrupt(), SystemExit(), GeneratorExit()):
        monkeypatch.setattr(
            cp75i,
            "_packet_oracle",
            lambda exception=exception: (_ for _ in ()).throw(exception),
        )
        with pytest.raises(type(exception)):
            cp75i.cp75_build_independent_review_response_validator_bundle()


def test_zero_argument_builder_final_issuance_failure_leaves_no_partial_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gc.collect()
    with cp75i._ISSUED_LOCK:
        baseline = len(cp75i._ISSUED)
    original = cp75i._record

    def fail_bundle(record_type: type, values: object) -> object:
        if record_type is cp75i.CP75IndependentReviewResponseValidatorBundleV1:
            raise MemoryError()
        return original(record_type, values)

    monkeypatch.setattr(cp75i, "_record", fail_bundle)
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        cp75i.cp75_build_independent_review_response_validator_bundle()
    assert caught.value.code == "CP75_RESOURCE_EXHAUSTED"
    del caught
    gc.collect()
    with cp75i._ISSUED_LOCK:
        assert len(cp75i._ISSUED) == baseline


def test_custody_reconstructs_exact_packet_without_project_import_or_io() -> None:
    custody = (
        cp75i.cp75_build_independent_review_response_validator_bundle().predecessor_custody
    )
    packet = cp75i._packet_oracle()
    request = json.loads(packet[_PATHS[6]])
    manifest = json.loads(packet[_PATHS[7]])
    assert custody.schema_version == _CUSTODY_SCHEMA
    assert custody.request_path == _PATHS[6]
    assert custody.request_canonical_json_bytes == len(packet[_PATHS[6]])
    assert (
        custody.request_canonical_json_sha256
        == hashlib.sha256(packet[_PATHS[6]]).hexdigest()
    )
    assert custody.request_record_sha256 == request["record_sha256"]
    assert custody.subject_record_sha256 == request["review_subject"]["subject_sha256"]
    assert custody.manifest_path == _PATHS[7]
    assert (
        custody.manifest_canonical_json_sha256
        == hashlib.sha256(packet[_PATHS[7]]).hexdigest()
    )
    assert custody.manifest_record_sha256 == manifest["manifest_sha256"]
    assert custody.reviewer_roles == _ROLES
    assert custody.criterion_ids == _CRITERION_IDS
    assert custody.role_criterion_coverage == _ROLE_COVERAGE
    assert custody.request_and_manifest_oracle_deeply_reconstructed is True
    assert custody.project_modules_imported is False
    assert custody.path_io_performed is False


@pytest.mark.parametrize(
    ("role", "expected_production"),
    tuple(zip(_ROLES, ("ABSTAIN", "ABSTAIN", "DEFER", "DEFER"))),
)
def test_valid_test_owned_signed_response_for_each_role_is_structurally_accepted(
    role: str, expected_production: str
) -> None:
    inputs = _valid_inputs(role)
    summary = cp75i.cp75_validate_supplied_external_review_response(*inputs)
    assert summary.schema_version == _SUMMARY_SCHEMA
    assert summary.reviewer_role == role
    assert (
        summary.candidate_descriptor_disposition == "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY"
    )
    assert summary.production_executable_schema_disposition == expected_production
    assert summary.acknowledged_subject_open_item_ids == _OPEN_ITEMS
    assert summary.criterion_result_count == len(dict(_ROLE_COVERAGE)[role])
    true_fields = (
        "request_exactly_reconstructed",
        "manifest_exactly_reconstructed",
        "response_canonical",
        "public_key_canonical",
        "response_field_grammar_valid",
        "public_key_field_grammar_valid",
        "criterion_coverage_complete",
        "criterion_result_digests_valid",
        "response_record_digest_valid",
        "request_subject_scope_context_and_attachment_bindings_valid",
        "public_key_document_sha256_binding_valid",
        "public_key_identity_formula_valid",
        "reviewer_organization_binding_valid",
        "validity_interval_coherence_valid",
        "reviewer_signature_sha256_valid",
        "rsa_pss_signature_math_valid",
        "allowed_disposition_pair_valid",
        "current_subject_scope_rules_valid",
    )
    assert all(getattr(summary, name) is True for name in true_fields)
    false_fields = tuple(
        name
        for name in _SUMMARY_FIELDS
        if name
        in {
            "full_review_report_bytes_verified",
            "review_method_execution_verified",
            "supersession_relation_verified",
            "withdrawal_relation_verified",
            "conflict_status_verified",
            "reviewer_identity_authenticated",
            "external_trust_root_verified",
            "reviewer_authority_verified",
            "authority_appointment_verified",
            "conflict_of_interest_attestation_verified",
            "independence_attestation_verified",
            "revocation_status_verified",
            "validity_at_trusted_time_verified",
            "external_attachment_bytes_verified",
            "external_review_performed",
            "response_eligible_for_candidate_descriptor_acceptance",
            "response_eligible_for_production_schema_acceptance",
            "candidate_descriptor_acceptance_effective",
            "schema_acceptance_independent",
            "schema_acceptance_effective",
            "subsequent_candidate_descriptor_development_qualification_construction_permitted",
            "production_execution_authorized",
            "caller_input_bytes_retained_after_successful_return",
        }
    )
    assert all(getattr(summary, name) is False for name in false_fields)
    assert summary.production_gate_states == ("MISSING",) * 17
    assert summary.draft_blocker_states == ("MISSING",) * 4
    assert summary.formal_test_28_status == "OPEN"
    assert not any(
        isinstance(getattr(summary, item.name), bytes) for item in fields(summary)
    )


def test_valid_signed_withdrawal_is_math_valid_but_has_no_acceptance_effect() -> None:
    summary = cp75i.cp75_validate_supplied_external_review_response(
        *_valid_inputs(withdrawal=True)
    )
    assert summary.candidate_descriptor_disposition == "WITHDRAW"
    assert summary.production_executable_schema_disposition == "WITHDRAW"
    assert summary.criterion_result_count == 0
    assert summary.acknowledged_subject_open_item_ids == ()
    assert summary.criterion_coverage_complete is False
    assert summary.withdrawal_relation_verified is False
    assert summary.external_review_performed is False
    assert summary.candidate_descriptor_acceptance_effective is False


def test_test_owned_structural_summary_fixture_set_is_exact_and_non_authoritative() -> None:
    public_digests = []
    for (
        fixture_id,
        expected_bytes,
        expected_record,
        expected_public,
    ) in _SUMMARY_FIXTURE_PINS:
        inputs = (
            _valid_inputs(withdrawal=True)
            if fixture_id == "withdraw"
            else _valid_inputs(fixture_id)
        )
        summary = cp75i.cp75_validate_supplied_external_review_response(*inputs)
        assert (
            len(cp75i.cp75_independent_canonical_json_bytes(summary)) == expected_bytes
        )
        assert summary.record_sha256 == expected_record
        assert cp75i.cp75_independent_public_record_sha256(summary) == expected_public
        assert summary.external_review_performed is False
        assert summary.reviewer_authority_verified is False
        assert summary.schema_acceptance_effective is False
        assert summary.production_execution_authorized is False
        public_digests.append(expected_public)
    fixture_set = hashlib.sha256(
        b"cp75-test28-independent-hostile-validation-summary-set-v1\0"
        + b"".join(bytes.fromhex(item) for item in public_digests)
    ).hexdigest()
    assert fixture_set == _SUMMARY_FIXTURE_SET_SHA256


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize(
    "alien", (None, b"", bytearray(b"{}"), memoryview(b"{}"), "{}")
)
def test_exact_builtin_bytes_types_and_nonempty_limits_precede_parsing(
    index: int, alien: object
) -> None:
    values = list(_valid_inputs())
    values[index] = alien
    expected = "CP75_INPUT_BYTE_LIMIT" if alien == b"" else "CP75_INPUT_TYPE_MISMATCH"
    _assert_error(expected, tuple(values))


@pytest.mark.parametrize(
    ("index", "cap"),
    (
        (0, 1_048_576),
        (1, 262_144),
        (2, 1_048_576),
        (3, 65_536),
    ),
)
def test_each_per_input_byte_cap_is_live(index: int, cap: int) -> None:
    values = list(_valid_inputs())
    values[index] = b" " * (cap + 1)
    _assert_error("CP75_INPUT_BYTE_LIMIT", tuple(values))


def test_cumulative_byte_cap_is_live(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _valid_inputs()
    monkeypatch.setattr(
        cp75i,
        "CP75_INDEPENDENT_TEST28_MAXIMUM_TOTAL_INPUT_BYTES",
        sum(map(len, inputs)) - 1,
    )
    _assert_error("CP75_INPUT_BYTE_LIMIT", inputs)


@pytest.mark.parametrize("payload", (b"\xff", b"\xef\xbb\xbf{}", b'"\\ud800"'))
def test_encoding_failures_are_stable(payload: bytes) -> None:
    values = list(_valid_inputs())
    values[2] = payload
    _assert_error("CP75_INPUT_ENCODING_INVALID", tuple(values))


@pytest.mark.parametrize(
    "payload", (b"{", b'{"a":1,"a":2}', b'{"x":1.0}', b'{"x":NaN}')
)
def test_json_failures_duplicate_keys_and_floats_are_rejected(payload: bytes) -> None:
    values = list(_valid_inputs())
    values[2] = payload
    _assert_error("CP75_INPUT_JSON_INVALID", tuple(values))


def test_noncanonical_json_is_rejected_before_field_grammar() -> None:
    values = list(_valid_inputs())
    values[2] = values[2] + b" "
    _assert_error("CP75_INPUT_CANONICAL_MISMATCH", tuple(values))


def test_all_four_utf8_phases_complete_before_any_lexical_depth_check() -> None:
    values = list(_valid_inputs())
    values[0] = (b"[" * 17) + b"0" + (b"]" * 17)
    values[2] = b"\xff"
    _assert_error("CP75_INPUT_ENCODING_INVALID", tuple(values))


def test_all_four_lexical_depth_checks_complete_before_any_json_parse() -> None:
    values = list(_valid_inputs())
    values[0] = b"{"
    values[2] = (b"[" * 17) + b"0" + (b"]" * 17)
    _assert_error("CP75_INPUT_RESOURCE_LIMIT", tuple(values))


def test_all_four_json_parses_complete_before_any_canonical_replay_check() -> None:
    values = list(_valid_inputs())
    values[0] = values[0] + b" "
    values[2] = b"{"
    _assert_error("CP75_INPUT_JSON_INVALID", tuple(values))


def test_all_four_canonical_replays_complete_before_any_root_field_check() -> None:
    values = list(_valid_inputs())
    values[0] = _canonical({"wrong": "request-root"})
    values[2] = values[2] + b" "
    _assert_error("CP75_INPUT_CANONICAL_MISMATCH", tuple(values))


@pytest.mark.parametrize(
    "payload",
    (
        (b"[" * 17) + b"0" + (b"]" * 17),
        _canonical({"x": list(range(4_097))}),
        _canonical({"x" * 129: 1}),
        _canonical({"x": "a" * 65_537}),
        b'{"x":123456789012345678901}',
        _canonical({"x": [[0] * 16 for _index in range(4_096)]}),
    ),
)
def test_depth_array_key_text_integer_and_node_resource_caps_are_live(
    payload: bytes,
) -> None:
    values = list(_valid_inputs())
    values[2] = payload
    _assert_error("CP75_INPUT_RESOURCE_LIMIT", tuple(values))


def test_brackets_and_braces_inside_escaped_string_do_not_false_trigger_depth() -> None:
    values = list(_valid_inputs())
    values[2] = _canonical({"x": "[{}]" * 100})
    _assert_error("CP75_INPUT_FIELD_SET_MISMATCH", tuple(values))


def test_decoded_text_total_cap_is_live(monkeypatch: pytest.MonkeyPatch) -> None:
    values = list(_valid_inputs())
    monkeypatch.setattr(
        cp75i, "CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS", 10
    )
    _assert_error("CP75_INPUT_RESOURCE_LIMIT", tuple(values))


def test_root_field_set_precedes_schema() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["schema_version"] = "bad-schema"
    response["extra"] = 1
    values[2] = _canonical(response)
    _assert_error("CP75_INPUT_FIELD_SET_MISMATCH", tuple(values))


def test_schema_precedes_exact_request_mismatch() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["schema_version"] = "bad-schema"
    values[2] = _canonical(response)
    request = json.loads(values[0])
    request["request_state"] = "BAD"
    values[0] = _canonical(request)
    _assert_error("CP75_INPUT_SCHEMA_MISMATCH", tuple(values))


def test_exact_request_and_manifest_bytes_are_required_independently() -> None:
    values = list(_valid_inputs())
    request = json.loads(values[0])
    request["request_state"] = "BAD"
    values[0] = _canonical(request)
    _assert_error("CP75_INPUT_REQUEST_MISMATCH", tuple(values))
    values = list(_valid_inputs())
    manifest = json.loads(values[1])
    manifest["packet_file_count"] = 6
    values[1] = _canonical(manifest)
    _assert_error("CP75_INPUT_MANIFEST_MISMATCH", tuple(values))


def test_inventory_precedes_individual_record_digest() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["ordered_criterion_results"][0]["comment_sha256"] = _sha("stale-digest")
    response["ordered_criterion_results"].reverse()
    values[2] = _canonical(response)
    _assert_error("CP75_INPUT_INVENTORY_MISMATCH", tuple(values))


def test_record_digest_precedes_request_binding() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["ordered_criterion_results"][0]["comment_sha256"] = _sha("stale-digest")
    response["request_record_sha256"] = _sha("wrong-request-binding")
    values[2] = _canonical(response)
    _assert_error("CP75_INPUT_DIGEST_MISMATCH", tuple(values))


def test_binding_precedes_key_identity_and_signature() -> None:
    values = list(_valid_inputs())
    response, key = _decode_inputs(tuple(values))
    response["request_record_sha256"] = _sha("wrong-request-binding")
    key["key_identity_sha256"] = _sha("wrong-key-identity")
    response["reviewer_public_key_identity_sha256"] = key["key_identity_sha256"]
    values[2], values[3] = _encode_key_and_rebind(response, key)
    _assert_error("CP75_INPUT_BINDING_MISMATCH", tuple(values))


def test_public_key_identity_formula_precedes_signature() -> None:
    values = list(_valid_inputs())
    response, key = _decode_inputs(tuple(values))
    key["key_identity_sha256"] = _sha("wrong-key-identity")
    response["reviewer_public_key_identity_sha256"] = key["key_identity_sha256"]
    values[2], values[3] = _encode_key_and_rebind(response, key)
    _assert_error("CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH", tuple(values))


@pytest.mark.parametrize(
    ("key_field", "replacement"),
    (
        ("reviewer_role", _ROLES[1]),
        ("reviewer_identity_sha256", _sha("other-identity")),
        ("reviewer_organization_sha256", _sha("other-org")),
        ("authority_id", "other-untrusted-authority"),
    ),
)
def test_response_and_key_shared_fields_are_cross_bound(
    key_field: str, replacement: object
) -> None:
    values = list(_valid_inputs())
    response, key = _decode_inputs(tuple(values))
    key[key_field] = replacement
    values[2], values[3] = _encode_key_and_rebind(response, key)
    _assert_error("CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH", tuple(values))


@pytest.mark.parametrize(
    ("key_from", "key_until", "response_from", "signed", "response_until"),
    (
        (
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:01Z",
            "2027-01-01T00:00:00Z",
        ),
        (
            "2025-01-01T00:00:00Z",
            "2030-01-01T00:00:00Z",
            "2024-01-01T00:00:00Z",
            "2026-01-01T00:00:01Z",
            "2027-01-01T00:00:00Z",
        ),
        (
            "2025-01-01T00:00:00Z",
            "2030-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
            "2027-01-01T00:00:00Z",
            "2027-01-01T00:00:00Z",
        ),
        (
            "2025-01-01T00:00:00Z",
            "2030-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:01Z",
            "2031-01-01T00:00:00Z",
        ),
    ),
)
def test_interval_coherence_rejects_invalid_or_uncontained_ranges(
    key_from: str, key_until: str, response_from: str, signed: str, response_until: str
) -> None:
    values = list(_valid_inputs())
    response, key = _decode_inputs(tuple(values))
    key["valid_from_utc"] = key_from
    key["valid_until_utc"] = key_until
    response["valid_from_utc"] = response_from
    response["signed_at_utc"] = signed
    response["valid_until_utc"] = response_until
    values[2], values[3] = _encode_key_and_rebind(response, key)
    _assert_error("CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH", tuple(values))


@pytest.mark.parametrize(
    "value",
    ("2026-1-01T00:00:00Z", "2026-02-30T00:00:00Z", "2026-01-01T00:00:00+00:00"),
)
def test_utc_syntax_and_calendar_values_are_exact(value: str) -> None:
    values = list(_valid_inputs())
    response, key = _decode_inputs(tuple(values))
    response["signed_at_utc"] = value
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_FIELD_TYPE_MISMATCH", tuple(values))


def test_signature_plain_digest_precedes_pss_and_disposition() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["reviewer_signature_sha256"] = _sha("wrong-signature-digest")
    _zero_digest(
        response,
        "response_sha256",
        b"cp75-test28-production-schema-acceptance-review-response-v1\0",
    )
    values[2] = _canonical(response)
    _assert_error("CP75_INPUT_SIGNATURE_MISMATCH", tuple(values))


def test_pss_math_precedes_disposition_rules() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    signature = bytearray.fromhex(response["reviewer_signature_hex"])
    signature[0] ^= 1
    response["reviewer_signature_hex"] = bytes(signature).hex()
    response["reviewer_signature_sha256"] = hashlib.sha256(signature).hexdigest()
    response["candidate_descriptor_disposition"] = "REJECT"
    _zero_digest(
        response,
        "response_sha256",
        b"cp75-test28-production-schema-acceptance-review-response-v1\0",
    )
    values[2] = _canonical(response)
    _assert_error("CP75_INPUT_RSA_PSS_MISMATCH", tuple(values))


def test_invalid_allowed_pair_fails_only_after_valid_signature_math() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["candidate_descriptor_disposition"] = "DEFER"
    response["production_executable_schema_disposition"] = "ABSTAIN"
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))


def test_current_subject_production_accept_is_rejected_after_signature_math() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["ordered_criterion_results"][-1]["disposition"] = "PASS"
    response["candidate_descriptor_disposition"] = "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY"
    response["production_executable_schema_disposition"] = "ACCEPT"
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))


@pytest.mark.parametrize("role", _ROLES)
def test_current_role_c12_payload_is_exact(role: str) -> None:
    values = list(_valid_inputs(role))
    response = json.loads(values[2])
    c12 = response["ordered_criterion_results"][-1]
    if role in _ROLES[:2]:
        c12["disposition"] = "DEFER"
        c12["finding_ids"] = list(_OPEN_ITEMS)
        response["open_finding_ids"] = list(_OPEN_ITEMS)
        response["required_change_ids"] = list(_OPEN_ITEMS)
        response["production_executable_schema_disposition"] = "DEFER"
    else:
        c12["disposition"] = "ABSTAIN"
        c12["finding_ids"] = []
        response["open_finding_ids"] = []
        response["required_change_ids"] = []
        response["production_executable_schema_disposition"] = "ABSTAIN"
    values[2] = _refresh_response_digests_and_signature(response, role)
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))


def test_pass_abstain_defer_fail_row_payload_rules_are_closed() -> None:
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["ordered_criterion_results"][0]["finding_ids"] = ["finding-on-pass"]
    response["open_finding_ids"] = ["finding-on-pass"]
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))
    values = list(_valid_inputs(_ROLES[2]))
    response = json.loads(values[2])
    response["ordered_criterion_results"][-1]["finding_ids"] = []
    response["open_finding_ids"] = []
    response["required_change_ids"] = []
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))


def test_open_finding_union_order_and_required_change_subset_are_enforced() -> None:
    values = list(_valid_inputs(_ROLES[2]))
    response = json.loads(values[2])
    response["open_finding_ids"] = list(reversed(_OPEN_ITEMS))
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))
    values = list(_valid_inputs(_ROLES[2]))
    response = json.loads(values[2])
    response["required_change_ids"].append("unbound-change")
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))


def test_withdrawal_branch_requires_empty_vectors_and_exact_relation_nullability() -> None:
    values = list(_valid_inputs(withdrawal=True))
    response = json.loads(values[2])
    response["review_method_ids"] = ["method-not-allowed-on-withdrawal"]
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))
    values = list(_valid_inputs(withdrawal=True))
    response = json.loads(values[2])
    response["supersedes_response_sha256"] = _sha("cannot-supersede-and-withdraw")
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))


def test_success_summary_record_digest_and_public_digest_are_independent() -> None:
    summary = cp75i.cp75_validate_supplied_external_review_response(*_valid_inputs())
    body = {item.name: getattr(summary, item.name) for item in fields(summary)}
    supplied = body["record_sha256"]
    body["record_sha256"] = _ZERO
    assert (
        supplied
        == hashlib.sha256(
            _SUMMARY_SCHEMA.encode("ascii") + b"\0" + _canonical(body)
        ).hexdigest()
    )
    assert cp75i.cp75_independent_record_sha256(summary) == supplied
    expected_public = hashlib.sha256(
        b"cp75-independent-public-record-v1\0"
        + type(summary).__name__.encode("ascii")
        + b"\0"
        + cp75i.cp75_independent_canonical_json_bytes(summary)
    ).hexdigest()
    assert cp75i.cp75_independent_public_record_sha256(summary) == expected_public


@pytest.mark.parametrize("value", ({}, [], (), b"", "", 0, False, None, object()))
def test_record_helpers_reject_wrong_types(value: object) -> None:
    for function in (
        cp75i.cp75_independent_canonical_json_bytes,
        cp75i.cp75_independent_record_sha256,
        cp75i.cp75_independent_public_record_sha256,
    ):
        with pytest.raises(
            cp75i.CP75IndependentReviewResponseValidationError
        ) as caught:
            function(value)
        assert caught.value.code == "CP75_RECORD_TYPE_MISMATCH"


def test_record_helpers_reject_unissued_pickle_and_alien_base_record() -> None:
    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    unissued = _unissued_copy(bundle)
    for function in (
        cp75i.cp75_independent_canonical_json_bytes,
        cp75i.cp75_independent_record_sha256,
        cp75i.cp75_independent_public_record_sha256,
    ):
        with pytest.raises(
            cp75i.CP75IndependentReviewResponseValidationError
        ) as caught:
            function(unissued)
        assert caught.value.code == "CP75_RECORD_NOT_ISSUED"
    with pytest.raises(TypeError, match="not pickle"):
        pickle.dumps(bundle)
    alien = object.__new__(cp75i._SealedRecord)
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        cp75i.cp75_independent_canonical_json_bytes(alien)
    assert caught.value.code == "CP75_RECORD_TYPE_MISMATCH"


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("formal_test_28_status", "TAMPERED"),
        ("production_gate_states", ["MISSING"] * 17),
        ("predecessor_custody", None),
        ("scope", object()),
        ("scope", "x" * 1_048_577),
    ),
)
def test_issued_record_value_type_nested_serialization_and_resource_tamper_is_rejected(
    field: str, replacement: object
) -> None:
    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    original = getattr(bundle, field)
    object.__setattr__(bundle, field, replacement)
    try:
        with pytest.raises(
            cp75i.CP75IndependentReviewResponseValidationError
        ) as caught:
            cp75i.cp75_independent_canonical_json_bytes(bundle)
        assert caught.value.code == "CP75_RECORD_TAMPERED"
    finally:
        object.__setattr__(bundle, field, original)


def test_issued_record_deleted_slot_and_equal_nested_mapping_are_tamper() -> None:
    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    custody = bundle.predecessor_custody
    original = custody.schema_version
    object.__delattr__(custody, "schema_version")
    try:
        with pytest.raises(
            cp75i.CP75IndependentReviewResponseValidationError
        ) as caught:
            cp75i.cp75_independent_canonical_json_bytes(custody)
        assert caught.value.code == "CP75_RECORD_TAMPERED"
    finally:
        object.__setattr__(custody, "schema_version", original)
    primitive = {item.name: getattr(custody, item.name) for item in fields(custody)}
    object.__setattr__(bundle, "predecessor_custody", primitive)
    try:
        with pytest.raises(
            cp75i.CP75IndependentReviewResponseValidationError
        ) as caught:
            cp75i.cp75_independent_canonical_json_bytes(bundle)
        assert caught.value.code == "CP75_RECORD_TAMPERED"
    finally:
        object.__setattr__(bundle, "predecessor_custody", custody)


def test_equal_tuple_subclass_is_not_an_exact_typed_sealed_snapshot() -> None:
    class HostileTuple(tuple):
        pass

    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    original = bundle.production_gate_states
    object.__setattr__(bundle, "production_gate_states", HostileTuple(original))
    try:
        with pytest.raises(
            cp75i.CP75IndependentReviewResponseValidationError
        ) as caught:
            cp75i.cp75_independent_canonical_json_bytes(bundle)
        assert caught.value.code == "CP75_RECORD_TAMPERED"
    finally:
        object.__setattr__(bundle, "production_gate_states", original)


@pytest.mark.parametrize(
    "kind",
    (
        "depth",
        "nodes",
        "members",
        "array",
        "key",
        "text-item",
        "text-total",
        "integer",
    ),
)
def test_issued_snapshot_exported_resource_caps_precede_json_materialization(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    if kind == "depth":
        # The sealed record itself is the root object.  Sixteen nested empty
        # tuples below it would serialize as 17 simultaneously open containers.
        replacement: object = ()
        for _index in range(15):
            replacement = (replacement,)
    elif kind == "nodes":
        replacement = tuple(
            {"k%02d" % index: 0 for index in range(16)} for _item in range(4_096)
        )
    elif kind == "members":
        replacement = {"k%03d" % index: None for index in range(129)}
    elif kind == "array":
        replacement = (None,) * 4_097
    elif kind == "key":
        replacement = {"k" * 129: None}
    elif kind == "text-item":
        replacement = "x" * 65_537
    elif kind == "text-total":
        replacement = ("x" * 65_536,) * 17
    elif kind == "integer":
        replacement = 10**20
    else:
        raise AssertionError("unknown issued-snapshot cap hostile")

    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    original = bundle.scope
    object.__setattr__(bundle, "scope", replacement)
    monkeypatch.setattr(
        cp75i,
        "_plain_json_bytes",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("JSON materialization ran before the typed cap")
        ),
    )
    try:
        with pytest.raises(
            cp75i.CP75IndependentReviewResponseValidationError
        ) as caught:
            cp75i.cp75_independent_canonical_json_bytes(bundle)
        assert caught.value.code == "CP75_RECORD_TAMPERED"
        assert type(caught.value.__cause__) is ValueError
    finally:
        object.__setattr__(bundle, "scope", original)


def test_issued_snapshot_depth_cap_accepts_exactly_sixteen_open_containers() -> None:
    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    original = bundle.scope
    replacement: object = ()
    for _index in range(14):
        replacement = (replacement,)
    object.__setattr__(bundle, "scope", replacement)
    try:
        cp75i._typed_snapshot(bundle)
        object.__setattr__(bundle, "scope", (replacement,))
        with pytest.raises(ValueError, match="cap"):
            cp75i._typed_snapshot(bundle)
    finally:
        object.__setattr__(bundle, "scope", original)


@pytest.mark.parametrize(
    "function_name",
    (
        "cp75_independent_canonical_json_bytes",
        "cp75_independent_record_sha256",
        "cp75_independent_public_record_sha256",
    ),
)
def test_issued_record_helpers_normalize_memoryerror_and_reraise_control_flow(
    monkeypatch: pytest.MonkeyPatch, function_name: str
) -> None:
    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    function = getattr(cp75i, function_name)
    monkeypatch.setattr(
        cp75i,
        "_typed_snapshot",
        lambda *_args: (_ for _ in ()).throw(MemoryError()),
    )
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        function(bundle)
    assert caught.value.code == "CP75_RESOURCE_EXHAUSTED"
    for exception in (KeyboardInterrupt(), SystemExit(), GeneratorExit()):
        monkeypatch.setattr(
            cp75i,
            "_typed_snapshot",
            lambda *_args, exception=exception: (_ for _ in ()).throw(exception),
        )
        with pytest.raises(type(exception)):
            function(bundle)


def test_public_record_digest_normalizes_post_validation_hash_memoryerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    monkeypatch.setattr(
        cp75i.hashlib,
        "sha256",
        lambda *_args: (_ for _ in ()).throw(MemoryError()),
    )
    with pytest.raises(cp75i.CP75IndependentReviewResponseValidationError) as caught:
        cp75i.cp75_independent_public_record_sha256(bundle)
    assert caught.value.code == "CP75_RESOURCE_EXHAUSTED"
    for exception in (KeyboardInterrupt(), SystemExit(), GeneratorExit()):
        monkeypatch.setattr(
            cp75i.hashlib,
            "sha256",
            lambda *_args, exception=exception: (_ for _ in ()).throw(exception),
        )
        with pytest.raises(type(exception)):
            cp75i.cp75_independent_public_record_sha256(bundle)


def test_memoryerror_is_normalized_and_control_flow_is_reraised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _valid_inputs()
    original = cp75i._decode_payload
    monkeypatch.setattr(
        cp75i, "_decode_payload", lambda *_args: (_ for _ in ()).throw(MemoryError())
    )
    _assert_error("CP75_RESOURCE_EXHAUSTED", inputs)
    for exception in (KeyboardInterrupt(), SystemExit(), GeneratorExit()):
        monkeypatch.setattr(
            cp75i,
            "_decode_payload",
            lambda *_args, exception=exception: (_ for _ in ()).throw(exception),
        )
        with pytest.raises(type(exception)):
            cp75i.cp75_validate_supplied_external_review_response(*inputs)
    monkeypatch.setattr(cp75i, "_decode_payload", original)


def test_unexpected_exception_is_normalized_internal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cp75i,
        "_decode_payload",
        lambda *_args: (_ for _ in ()).throw(ValueError("unexpected")),
    )
    _assert_error("CP75_INTERNAL_INVARIANT_FAILED", _valid_inputs())


def test_internal_oracle_validation_error_is_not_misattributed_to_caller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid_oracle(*_args: object) -> object:
        raise cp75i.CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_DIGEST_MISMATCH", "injected static oracle drift"
        )

    monkeypatch.setattr(cp75i, "_validate_packet_oracle", invalid_oracle)
    _assert_error("CP75_INTERNAL_INVARIANT_FAILED", _valid_inputs())


def test_late_validation_failure_issues_no_summary_or_dynamic_cache_entry() -> None:
    gc.collect()
    with cp75i._ISSUED_LOCK:
        baseline = len(cp75i._ISSUED)
    values = list(_valid_inputs())
    response = json.loads(values[2])
    response["candidate_descriptor_disposition"] = "DEFER"
    response["production_executable_schema_disposition"] = "ABSTAIN"
    values[2] = _refresh_response_digests_and_signature(
        response, response["reviewer_role"]
    )
    _assert_error("CP75_INPUT_DISPOSITION_MISMATCH", tuple(values))
    gc.collect()
    with cp75i._ISSUED_LOCK:
        assert len(cp75i._ISSUED) == baseline


def test_final_summary_issuance_memoryerror_is_resource_and_atomic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gc.collect()
    with cp75i._ISSUED_LOCK:
        baseline = len(cp75i._ISSUED)
    original = cp75i._record

    def fail_summary(record_type: type, values: object) -> object:
        if (
            record_type
            is cp75i.CP75IndependentSuppliedReviewResponseValidationSummaryV1
        ):
            raise MemoryError()
        return original(record_type, values)

    monkeypatch.setattr(cp75i, "_record", fail_summary)
    _assert_error("CP75_RESOURCE_EXHAUSTED", _valid_inputs())
    gc.collect()
    with cp75i._ISSUED_LOCK:
        assert len(cp75i._ISSUED) == baseline


def test_weak_registry_releases_summaries_and_bundles_without_caller_byte_cache() -> None:
    gc.collect()
    with cp75i._ISSUED_LOCK:
        baseline = len(cp75i._ISSUED)
    summary = cp75i.cp75_validate_supplied_external_review_response(*_valid_inputs())
    bundle = cp75i.cp75_build_independent_review_response_validator_bundle()
    summary_ref = weakref.ref(summary)
    bundle_ref = weakref.ref(bundle)
    custody_ref = weakref.ref(bundle.predecessor_custody)
    del summary, bundle
    gc.collect()
    assert summary_ref() is None and bundle_ref() is None and custody_ref() is None
    with cp75i._ISSUED_LOCK:
        assert len(cp75i._ISSUED) == baseline


def test_validation_and_record_registry_are_thread_safe() -> None:
    inputs = _valid_inputs()
    with ThreadPoolExecutor(max_workers=8) as executor:
        summaries = list(
            executor.map(
                lambda _index: cp75i.cp75_validate_supplied_external_review_response(
                    *inputs
                ),
                range(24),
            )
        )
        canonical = list(
            executor.map(cp75i.cp75_independent_canonical_json_bytes, summaries)
        )
        public = list(
            executor.map(cp75i.cp75_independent_public_record_sha256, summaries)
        )
    assert len({id(item) for item in summaries}) == 24
    assert len({item.record_sha256 for item in summaries}) == 1
    assert len(set(canonical)) == 1
    assert len(set(public)) == 1


def test_locked_python39_import_bundle_and_real_signed_response_validation() -> None:
    if not _PYTHON39.is_file():
        pytest.skip("locked Python 3.9 executable is unavailable")
    inputs = _valid_inputs()
    environment = {"PYTHONPATH": str(_ROOT / "src")}
    for index, payload in enumerate(inputs):
        environment["CP75_INPUT_%d" % index] = base64.b64encode(payload).decode("ascii")
    script = r"""
import base64, os
import heterodiff.evaluation.mixed_initializer_test28_independent_production_schema_acceptance_review_response_validator as cp75i
values = tuple(base64.b64decode(os.environ["CP75_INPUT_%d" % i]) for i in range(4))
summary = cp75i.cp75_validate_supplied_external_review_response(*values)
assert len(cp75i.__all__) == 29
assert summary.rsa_pss_signature_math_valid is True
assert summary.external_review_performed is False
assert summary.production_execution_authorized is False
print("cp75-independent-python39-ok")
"""
    result = subprocess.run(
        [str(_PYTHON39), "-c", script],
        cwd=str(_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "cp75-independent-python39-ok"
