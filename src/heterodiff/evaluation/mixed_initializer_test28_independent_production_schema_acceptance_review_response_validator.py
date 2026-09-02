"""Validate one supplied CP75 external-review response without accepting it.

This standard-library-only module imports no project module and performs no
path I/O.  It reconstructs the exact CP75 request packet from a static oracle,
checks one caller-supplied response and public-key document, and verifies only
their structural, digest, binding, interval-coherence, and RSA-PSS mathematics.
It does not authenticate a reviewer, trust a key, read a clock, verify external
attachments or authority, aggregate responses, accept a schema, authorize a
later qualification or production execution, close a gate or blocker, or close
Formal Test 28.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, fields
from datetime import datetime
import hashlib
import hmac
import json
import math
import re
import threading
from typing import Dict, List, Mapping, Optional, Tuple, Type, cast
import weakref
import zlib


CP75_INDEPENDENT_TEST28_SCHEMA_VERSION = (
    "cp75-test28-independent-production-schema-acceptance-review-response-"
    "validator-v1"
)
CP75_INDEPENDENT_TEST28_SCOPE = (
    "source-independent-stdlib-only-exact-byte-canonical-structure-digest-"
    "binding-key-formula-interval-coherence-and-rsa-pss-mathematics-"
    "validation-of-one-caller-supplied-cp75-external-review-response;exact-"
    "request-and-self-excluding-seven-entry-manifest-required;no-project-"
    "module-import-or-path-io;no-external-attachment-bytes-method-execution-"
    "supersession-withdrawal-conflict-identity-trust-authority-appointment-"
    "conflict-of-interest-independence-revocation-current-or-trusted-time-"
    "external-review-aggregation-candidate-acceptance-broad-schema-acceptance-"
    "subsequent-qualification-construction-production-execution-gate-blocker-"
    "evidence-or-test28-closure;caller-input-bytes-not-retained-after-"
    "successful-return;failure-traceback-local-retention-unqualified"
)
CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION = (
    "cp75-test28-production-schema-acceptance-review-request-v1"
)
_SOURCE_RESPONSE_SCHEMA_VERSION = (
    "cp75-test28-production-schema-acceptance-review-response-v1"
)
_SOURCE_PUBLIC_KEY_SCHEMA_VERSION = (
    "cp75-test28-production-schema-acceptance-reviewer-public-key-document-v1"
)

CP75_INDEPENDENT_TEST28_MAXIMUM_REQUEST_BYTES = 1_048_576
CP75_INDEPENDENT_TEST28_MAXIMUM_MANIFEST_BYTES = 262_144
CP75_INDEPENDENT_TEST28_MAXIMUM_RESPONSE_BYTES = 1_048_576
CP75_INDEPENDENT_TEST28_MAXIMUM_PUBLIC_KEY_BYTES = 65_536
CP75_INDEPENDENT_TEST28_MAXIMUM_TOTAL_INPUT_BYTES = 2_424_832
CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH = 16
CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES = 65_536
CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS = 128
CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS = 4_096
CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS = 128
CP75_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS = 65_536
CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS = 1_048_576
CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS = 20

CP75_INDEPENDENT_TEST28_REVIEWER_ROLES = (
    "protocol-and-provenance-reviewer",
    "runtime-and-durability-reviewer",
    "statistical-power-and-decision-reviewer",
    "independent-recomputation-reviewer",
)
CP75_INDEPENDENT_TEST28_CRITERION_IDS = (
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

CP75_INDEPENDENT_TEST28_ERROR_CODES = (
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
CP75_INDEPENDENT_TEST28_VALIDATION_PHASE_ORDER = (
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

_CHECKLIST_PATH = (
    "research/preregistrations/"
    "cp75_test28_production_schema_acceptance_review_checklist_v1.md"
)
_VECTORS_PATH = (
    "research/fixtures/cp75_test28_production_schema_acceptance_review_"
    "response_contract_and_test_vectors_v1.json"
)
_TEMPLATE_PATHS = (
    "research/fixtures/cp75_test28_production_schema_acceptance_protocol_and_"
    "provenance_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_runtime_and_"
    "durability_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_statistical_"
    "power_and_decision_reviewer_unissued_template_v1.json",
    "research/fixtures/cp75_test28_production_schema_acceptance_independent_"
    "recomputation_reviewer_unissued_template_v1.json",
)
_REQUEST_PATH = (
    "research/fixtures/"
    "cp75_test28_production_schema_acceptance_review_request_v1.json"
)
_MANIFEST_PATH = (
    "research/fixtures/"
    "cp75_test28_production_schema_acceptance_review_packet_manifest_v1.json"
)
_PACKET_PATHS = (
    (_CHECKLIST_PATH, _VECTORS_PATH)
    + _TEMPLATE_PATHS
    + (
        _REQUEST_PATH,
        _MANIFEST_PATH,
    )
)
_SIGNATURE_SCHEME_ID = "rsa-pss-sha256-3072-e65537-salt32-v1"
_ZERO_SHA256 = "0" * 64
_EXPECTED_REQUEST_BYTES = 45_650
_EXPECTED_REQUEST_SHA256 = (
    "7fa8601dc3c058489281509eacab4448560a468d1051a71092f40fe49a04155b"
)
_EXPECTED_MANIFEST_BYTES = 4_347
_EXPECTED_MANIFEST_SHA256 = (
    "2f76e7bbd74f992a4307e7c2b06974c24e31eefbbe7c0237e2d7527ae2039708"
)
_EXPECTED_CHECKLIST_BYTES = 15_966
_EXPECTED_CHECKLIST_LF_COUNT = 202
_EXPECTED_CHECKLIST_SHA256 = (
    "ef5aa6b23c015bdcc05498fc12eafbe00240d1e6e7fef717c39747460d4578b8"
)
_EXPECTED_VECTORS_BYTES = 37_140
_EXPECTED_VECTORS_SHA256 = (
    "ac26babba509771fb9fb692e80b7739628da12b951e9709508ce63871be0196a"
)
_MISSING_GATES = ("MISSING",) * 17
_MISSING_BLOCKERS = ("MISSING",) * 4
_KNOWN_OPEN_ITEM_IDS = (
    "primary-threshold-comparison-operator",
    "primary-threshold-comparison-direction",
    "primary-threshold-value-law",
    "primary-selected-count-justification",
    "primary-32-slot-decision-function",
    "decision-timestamp-authority",
)
_ALLOWED_DISPOSITION_PAIRS = (
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
_ROLE_COVERAGE = (
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[0],
        tuple(
            CP75_INDEPENDENT_TEST28_CRITERION_IDS[index - 1]
            for index in (1, 2, 3, 4, 5, 6, 7, 9, 12)
        ),
    ),
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[1],
        tuple(
            CP75_INDEPENDENT_TEST28_CRITERION_IDS[index - 1]
            for index in (1, 3, 4, 5, 6, 7, 8, 10, 11, 12)
        ),
    ),
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[2],
        tuple(
            CP75_INDEPENDENT_TEST28_CRITERION_IDS[index - 1]
            for index in (1, 3, 8, 9, 12)
        ),
    ),
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[3],
        tuple(
            CP75_INDEPENDENT_TEST28_CRITERION_IDS[index - 1]
            for index in (1, 2, 3, 4, 8, 9, 10, 11, 12)
        ),
    ),
)
_CURRENT_C12_DISPOSITION = {
    CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[0]: "ABSTAIN",
    CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[1]: "ABSTAIN",
    CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[2]: "DEFER",
    CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[3]: "DEFER",
}
_CURRENT_ROLE_C12_REQUIREMENTS = tuple(
    (
        role,
        CP75_INDEPENDENT_TEST28_CRITERION_IDS[11],
        _CURRENT_C12_DISPOSITION[role],
    )
    for role in CP75_INDEPENDENT_TEST28_REVIEWER_ROLES
)
_CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS = (
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[0],
        "ABSTAIN",
        "finding_ids=empty;required_change_ids-contribution=empty;comment_sha256="
        "nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six",
    ),
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[1],
        "ABSTAIN",
        "finding_ids=empty;required_change_ids-contribution=empty;comment_sha256="
        "nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six",
    ),
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[2],
        "DEFER",
        "finding_ids=exact-six-known-open-item-ids;required_change_ids=exact-six-"
        "known-open-item-ids;comment_sha256=nonzero-reason-digest;acknowledged_"
        "subject_open_item_ids=exact-six",
    ),
    (
        CP75_INDEPENDENT_TEST28_REVIEWER_ROLES[3],
        "DEFER",
        "finding_ids=exact-six-known-open-item-ids;required_change_ids=exact-six-"
        "known-open-item-ids;comment_sha256=nonzero-reason-digest;acknowledged_"
        "subject_open_item_ids=exact-six",
    ),
)
_AXIS_DERIVATION_PRECEDENCE = (
    "if-any-applicable-blocking-result-FAIL-then-axis-disposition-REJECT",
    "else-if-any-applicable-blocking-result-DEFER-then-axis-disposition-DEFER",
    "else-if-any-applicable-blocking-result-ABSTAIN-then-axis-disposition-ABSTAIN",
    "else-all-applicable-blocking-results-PASS-then-candidate-axis-ACCEPT_FOR_"
    "CP75_DEVELOPMENT_ONLY-or-production-axis-ACCEPT",
    "WITHDRAW-is-a-separate-empty-result-response-branch-and-both-axes-WITHDRAW",
)
_CRITERION_RESULT_BRANCH_RULES = (
    "PASS=>finding_ids-exact-empty;comment_sha256-exact-nonzero-lowercase-64hex",
    "DEFER=>finding_ids-nonempty-bounded-unique-identifiers;comment_sha256-exact-"
    "nonzero-lowercase-64hex",
    "FAIL=>finding_ids-nonempty-bounded-unique-identifiers;comment_sha256-exact-"
    "nonzero-lowercase-64hex",
    "ABSTAIN=>finding_ids-exact-empty;required-change-contribution-exact-empty;"
    "comment_sha256-exact-nonzero-reason-lowercase-64hex",
    "every-row-has-exact-five-keys-and-row_sha256-is-zero-carrier-domain-digest",
)
_RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES = (
    "substantive-ordinary=>all-exact-response-fields-nonnull-except-supersedes_"
    "response_sha256-and-withdraws_response_sha256-both-null",
    "substantive-replacement=>all-exact-response-fields-nonnull-except-withdraws_"
    "response_sha256-null;supersedes_response_sha256-lowercase-64hex",
    "withdrawal=>both-axis-dispositions-WITHDRAW;ordered-criterion-results-and-"
    "their-digest-vector-and-open-findings-and-required-changes-and-acknowledged-"
    "open-items-and-review-method-ids-exact-empty;withdraws_response_sha256-"
    "lowercase-64hex;supersedes_response_sha256-null",
    "nonwithdrawal=>withdraws_response_sha256-null",
    "template-only-unissued=>all-reviewer-identity-key-authority-report-result-"
    "decision-time-signature-and-response-digest-fields-null;never-an-issued-"
    "response",
)
_FINDING_CHANGE_AND_REPORT_RULES = (
    "open_finding_ids=stable-ordered-unique-union-of-row-finding_ids-in-criterion-"
    "order-and-row-order",
    "required_change_ids=bounded-unique-subset-of-open_finding_ids-and-thus-"
    "resolved-by-full-review-report-pointer",
    "substantive-response-full_review_report_sha256=nonzero-lowercase-64hex-"
    "pointer-only;packet-and-one-response-validator-do-not-verify-report-bytes",
    "unexpected-finding-identifiers-are-nonempty-lowercase-ascii-[a-z0-9][a-z0-9."
    "_:-]{0,127}-unique-and-not-closed-to-an-allowlist",
    "every-nonwithdrawal-response-acknowledges-exact-six-subject-open-item-ids-in-"
    "subject-order",
)


class CP75IndependentReviewResponseValidationError(RuntimeError):
    """Stable validation failure with a closed public code."""

    def __init__(self, code: str, message: str) -> None:
        if code not in CP75_INDEPENDENT_TEST28_ERROR_CODES:
            raise ValueError("unknown independent CP75 error code")
        self.code = code
        super().__init__(code + ": " + message)


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del cls, args, kwargs
        raise TypeError("independent CP75 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("independent CP75 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("independent CP75 records are not pickle objects")


_ALLOW_RECORD_CLASS_DEFINITION = True


@dataclass(frozen=True, eq=False, init=False)
class CP75IndependentReviewPacketCustodyV1(_SealedRecord):
    schema_version: str
    source_request_schema_version: str
    source_response_schema_version: str
    source_public_key_schema_version: str
    request_path: str
    request_canonical_json_bytes: int
    request_canonical_json_sha256: str
    request_record_sha256: str
    subject_record_sha256: str
    checklist_path: str
    checklist_bytes: int
    checklist_lf_count: int
    checklist_sha256: str
    response_contract_test_vectors_path: str
    response_contract_test_vectors_bytes: int
    response_contract_test_vectors_sha256: str
    reviewer_template_paths: Tuple[str, ...]
    reviewer_template_bytes: Tuple[int, ...]
    reviewer_template_sha256s: Tuple[str, ...]
    manifest_path: str
    manifest_canonical_json_bytes: int
    manifest_canonical_json_sha256: str
    manifest_record_sha256: str
    reviewer_roles: Tuple[str, ...]
    criterion_ids: Tuple[str, ...]
    role_criterion_coverage: Tuple[Tuple[str, Tuple[str, ...]], ...]
    signature_scheme_id: str
    request_and_manifest_oracle_deeply_reconstructed: bool
    project_modules_imported: bool
    path_io_performed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP75IndependentSuppliedReviewResponseValidationSummaryV1(_SealedRecord):
    schema_version: str
    source_request_schema_version: str
    source_response_schema_version: str
    source_public_key_schema_version: str
    request_input_bytes: int
    request_input_sha256: str
    manifest_input_bytes: int
    manifest_input_sha256: str
    response_input_bytes: int
    response_input_sha256: str
    public_key_input_bytes: int
    public_key_input_sha256: str
    reviewer_role: str
    candidate_descriptor_disposition: str
    production_executable_schema_disposition: str
    acknowledged_subject_open_item_ids: Tuple[str, ...]
    criterion_result_count: int
    request_exactly_reconstructed: bool
    manifest_exactly_reconstructed: bool
    response_canonical: bool
    public_key_canonical: bool
    response_field_grammar_valid: bool
    public_key_field_grammar_valid: bool
    criterion_coverage_complete: bool
    criterion_result_digests_valid: bool
    response_record_digest_valid: bool
    request_subject_scope_context_and_attachment_bindings_valid: bool
    public_key_document_sha256_binding_valid: bool
    public_key_identity_formula_valid: bool
    reviewer_organization_binding_valid: bool
    validity_interval_coherence_valid: bool
    reviewer_signature_sha256_valid: bool
    rsa_pss_signature_math_valid: bool
    allowed_disposition_pair_valid: bool
    current_subject_scope_rules_valid: bool
    full_review_report_bytes_verified: bool
    review_method_execution_verified: bool
    supersession_relation_verified: bool
    withdrawal_relation_verified: bool
    conflict_status_verified: bool
    reviewer_identity_authenticated: bool
    external_trust_root_verified: bool
    reviewer_authority_verified: bool
    authority_appointment_verified: bool
    conflict_of_interest_attestation_verified: bool
    independence_attestation_verified: bool
    revocation_status_verified: bool
    validity_at_trusted_time_verified: bool
    external_attachment_bytes_verified: bool
    external_review_performed: bool
    response_eligible_for_candidate_descriptor_acceptance: bool
    response_eligible_for_production_schema_acceptance: bool
    candidate_descriptor_acceptance_effective: bool
    schema_acceptance_independent: bool
    schema_acceptance_effective: bool
    subsequent_candidate_descriptor_development_qualification_construction_permitted: bool
    production_execution_authorized: bool
    production_gate_states: Tuple[str, ...]
    draft_blocker_states: Tuple[str, ...]
    formal_test_28_status: str
    caller_input_bytes_retained_after_successful_return: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP75IndependentReviewResponseValidatorBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    predecessor_custody: CP75IndependentReviewPacketCustodyV1
    maximum_request_bytes: int
    maximum_manifest_bytes: int
    maximum_response_bytes: int
    maximum_public_key_bytes: int
    maximum_total_input_bytes: int
    maximum_json_depth: int
    maximum_json_nodes: int
    maximum_object_members: int
    maximum_array_items: int
    maximum_key_characters: int
    maximum_text_item_characters: int
    maximum_decoded_text_characters: int
    maximum_integer_decimal_digits: int
    error_codes: Tuple[str, ...]
    validation_phase_order: Tuple[str, ...]
    one_response_per_call: bool
    exact_request_bytes_required: bool
    exact_manifest_bytes_required: bool
    response_structure_and_signature_math_validator_available: bool
    external_attachment_validator_available: bool
    trust_authority_time_revocation_or_aggregation_validator_available: bool
    project_modules_imported: bool
    path_io_performed: bool
    key_generation_performed: bool
    signing_performed: bool
    response_issuance_performed: bool
    external_review_performed: bool
    candidate_descriptor_acceptance_effective: bool
    schema_acceptance_effective: bool
    subsequent_candidate_descriptor_development_qualification_construction_permitted: bool
    production_execution_authorized: bool
    production_gate_states: Tuple[str, ...]
    draft_blocker_states: Tuple[str, ...]
    formal_test_28_status: str
    builder_validates_internal_definition: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_CUSTODY_SCHEMA = "cp75-test28-independent-review-packet-custody-v1"
_SUMMARY_SCHEMA = (
    "cp75-test28-independent-supplied-review-response-validation-summary-v1"
)
_RECORD_DOMAINS = {
    CP75IndependentReviewPacketCustodyV1: _CUSTODY_SCHEMA.encode("ascii") + b"\0",
    CP75IndependentSuppliedReviewResponseValidationSummaryV1: (
        _SUMMARY_SCHEMA.encode("ascii") + b"\0"
    ),
    CP75IndependentReviewResponseValidatorBundleV1: (
        CP75_INDEPENDENT_TEST28_SCHEMA_VERSION.encode("ascii") + b"\0"
    ),
}
_RECORD_TYPES = tuple(_RECORD_DOMAINS)
_ISSUED: "weakref.WeakKeyDictionary[_SealedRecord, Tuple[bytes, object]]" = (
    weakref.WeakKeyDictionary()
)
_ISSUED_LOCK = threading.RLock()


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        _primitive(value),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _primitive(
    value: object,
    depth: int = 0,
    nodes: Optional[List[int]] = None,
    text_characters: Optional[List[int]] = None,
) -> object:
    if nodes is None:
        nodes = [0]
    if text_characters is None:
        text_characters = [0]
    nodes[0] += 1
    if depth > CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
        raise ValueError("independent CP75 record nesting exceeds its cap")
    if nodes[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES:
        raise ValueError("independent CP75 record node count exceeds its cap")
    if type(value) in _RECORD_DOMAINS:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 record nesting exceeds its cap")
        record_fields = fields(value)
        if len(record_fields) > CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS:
            raise ValueError("independent CP75 record member count exceeds its cap")
        for item in record_fields:
            if len(item.name) > CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS:
                raise ValueError("independent CP75 record key exceeds its cap")
            text_characters[0] += len(item.name)
        if text_characters[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            raise ValueError("independent CP75 record text total exceeds its cap")
        return {
            item.name: _primitive(
                getattr(value, item.name), depth + 1, nodes, text_characters
            )
            for item in record_fields
        }
    if type(value) is tuple:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 record nesting exceeds its cap")
        if len(value) > CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS:
            raise ValueError("independent CP75 record array exceeds its cap")
        return [_primitive(item, depth + 1, nodes, text_characters) for item in value]
    if type(value) is list:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 record nesting exceeds its cap")
        if len(value) > CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS:
            raise ValueError("independent CP75 record array exceeds its cap")
        return [_primitive(item, depth + 1, nodes, text_characters) for item in value]
    if type(value) is dict:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 record nesting exceeds its cap")
        if len(value) > CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS:
            raise ValueError("independent CP75 record object exceeds its cap")
        if any(type(key) is not str for key in value):
            raise TypeError("independent CP75 canonical mapping key is not text")
        for key in value:
            if len(key) > CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS:
                raise ValueError("independent CP75 record key exceeds its cap")
            if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                raise ValueError("independent CP75 record key contains a surrogate")
            text_characters[0] += len(key)
        if text_characters[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            raise ValueError("independent CP75 record text total exceeds its cap")
        return {
            key: _primitive(item, depth + 1, nodes, text_characters)
            for key, item in cast(Mapping[str, object], value).items()
        }
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        if (
            len(str(abs(cast(int, value))))
            > CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS
        ):
            raise ValueError("independent CP75 record integer exceeds its cap")
        return value
    if type(value) is str:
        checked = cast(str, value)
        if len(checked) > CP75_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS:
            raise ValueError("independent CP75 record text item exceeds its cap")
        if any(0xD800 <= ord(character) <= 0xDFFF for character in checked):
            raise ValueError("independent CP75 record text contains a surrogate")
        text_characters[0] += len(checked)
        if text_characters[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            raise ValueError("independent CP75 record text total exceeds its cap")
        return value
    raise TypeError("independent CP75 canonical value has an alien type")


def _typed_snapshot(
    value: object,
    depth: int = 0,
    nodes: Optional[List[int]] = None,
    text_characters: Optional[List[int]] = None,
) -> object:
    if nodes is None:
        nodes = [0]
    if text_characters is None:
        text_characters = [0]
    nodes[0] += 1
    if (
        nodes[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES
        or depth > CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH
    ):
        raise ValueError("independent CP75 sealed snapshot exceeds its cap")
    if type(value) in _RECORD_DOMAINS:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 sealed snapshot exceeds its cap")
        record_fields = fields(value)
        if len(record_fields) > CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS:
            raise ValueError("independent CP75 sealed record has too many members")
        for item in record_fields:
            if len(item.name) > CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS:
                raise ValueError("independent CP75 sealed record key exceeds its cap")
            text_characters[0] += len(item.name)
        if text_characters[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            raise ValueError("independent CP75 sealed text total exceeds its cap")
        return (
            "record",
            type(value).__name__,
            id(value),
            tuple(
                (
                    item.name,
                    _typed_snapshot(
                        getattr(value, item.name),
                        depth + 1,
                        nodes,
                        text_characters,
                    ),
                )
                for item in record_fields
            ),
        )
    if type(value) is tuple:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 sealed snapshot exceeds its cap")
        if len(value) > CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS:
            raise ValueError("independent CP75 sealed array exceeds its cap")
        return (
            "tuple",
            tuple(
                _typed_snapshot(item, depth + 1, nodes, text_characters)
                for item in value
            ),
        )
    if type(value) is list:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 sealed snapshot exceeds its cap")
        if len(value) > CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS:
            raise ValueError("independent CP75 sealed array exceeds its cap")
        return (
            "list",
            tuple(
                _typed_snapshot(item, depth + 1, nodes, text_characters)
                for item in value
            ),
        )
    if type(value) is dict:
        if depth >= CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
            raise ValueError("independent CP75 sealed snapshot exceeds its cap")
        if len(value) > CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS:
            raise ValueError("independent CP75 sealed object exceeds its cap")
        for key in value:
            if type(key) is not str:
                raise TypeError("independent CP75 sealed object key is not text")
            if len(key) > CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS:
                raise ValueError("independent CP75 sealed object key exceeds its cap")
            if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                raise ValueError("independent CP75 sealed key contains a surrogate")
            text_characters[0] += len(key)
        if text_characters[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            raise ValueError("independent CP75 sealed text total exceeds its cap")
        return (
            "dict",
            tuple(
                (
                    key,
                    _typed_snapshot(item, depth + 1, nodes, text_characters),
                )
                for key, item in cast(Mapping[str, object], value).items()
            ),
        )
    if value is None:
        return ("none",)
    if type(value) is str:
        if len(value) > CP75_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS:
            raise ValueError("independent CP75 sealed text exceeds its cap")
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ValueError("independent CP75 sealed text contains a surrogate")
        text_characters[0] += len(value)
        if text_characters[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            raise ValueError("independent CP75 sealed text total exceeds its cap")
        return ("str", value)
    if type(value) is int:
        if (
            len(str(abs(cast(int, value))))
            > CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS
        ):
            raise ValueError("independent CP75 sealed integer exceeds its cap")
        return ("int", value)
    if type(value) is bool:
        return ("bool", value)
    raise TypeError("independent CP75 sealed value has an alien type")


def _record(cls: Type[_SealedRecord], values: Mapping[str, object]) -> _SealedRecord:
    names = tuple(item.name for item in fields(cls))
    if names[-1] != "record_sha256" or tuple(values) != names[:-1]:
        raise RuntimeError("independent CP75 record construction fields differ")
    body = dict(values)
    body["record_sha256"] = _ZERO_SHA256
    body["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls] + _plain_json_bytes(body)
    ).hexdigest()
    instance = object.__new__(cls)
    for name in names:
        object.__setattr__(instance, name, body[name])
    canonical = _plain_json_bytes(instance)
    snapshot = _typed_snapshot(instance)
    with _ISSUED_LOCK:
        _ISSUED[instance] = (canonical, snapshot)
    return instance


def _assert_issued(value: object) -> _SealedRecord:
    if type(value) not in _RECORD_DOMAINS:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RECORD_TYPE_MISMATCH", "record has an unsupported exact type"
        )
    record = cast(_SealedRecord, value)
    with _ISSUED_LOCK:
        issued = _ISSUED.get(record)
    if issued is None:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RECORD_NOT_ISSUED", "record was not issued by this module"
        )
    expected_bytes, expected_snapshot = issued
    try:
        actual_snapshot = _typed_snapshot(record)
        actual_bytes = _plain_json_bytes(record)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except MemoryError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RESOURCE_EXHAUSTED",
            "issued-record validation exhausted memory",
        ) from exc
    except Exception as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RECORD_TAMPERED", "issued record structure was changed"
        ) from exc
    if actual_snapshot != expected_snapshot or actual_bytes != expected_bytes:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RECORD_TAMPERED", "issued record bytes or types were changed"
        )
    for item in fields(record):
        child = getattr(record, item.name)
        if type(child) in _RECORD_DOMAINS:
            _assert_issued(child)
        elif type(child) is tuple:
            for nested in child:
                if type(nested) in _RECORD_DOMAINS:
                    _assert_issued(nested)
    return record


def cp75_independent_canonical_json_bytes(record: object) -> bytes:
    try:
        sealed = _assert_issued(record)
        with _ISSUED_LOCK:
            return bytes(cast(Tuple[bytes, object], _ISSUED[sealed])[0])
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except MemoryError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RESOURCE_EXHAUSTED",
            "issued-record canonical byte retrieval exhausted memory",
        ) from exc


def cp75_independent_record_sha256(record: object) -> str:
    try:
        return cast(str, getattr(_assert_issued(record), "record_sha256"))
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except MemoryError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RESOURCE_EXHAUSTED",
            "issued-record digest retrieval exhausted memory",
        ) from exc


def cp75_independent_public_record_sha256(record: object) -> str:
    try:
        sealed = _assert_issued(record)
        return hashlib.sha256(
            b"cp75-independent-public-record-v1\0"
            + type(sealed).__name__.encode("ascii")
            + b"\0"
            + cp75_independent_canonical_json_bytes(sealed)
        ).hexdigest()
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except MemoryError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RESOURCE_EXHAUSTED",
            "issued-record public digest construction exhausted memory",
        ) from exc


def _fail(code: str, message: str) -> None:
    raise CP75IndependentReviewResponseValidationError(code, message)


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and re.fullmatch(r"[0-9a-f]{64}", cast(str, value)) is not None
    )


def _is_identifier(value: object) -> bool:
    return (
        type(value) is str
        and re.fullmatch(r"[a-z0-9][a-z0-9._:-]{0,127}", cast(str, value)) is not None
    )


def _reject_duplicate_pairs(pairs: list) -> dict:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail("CP75_INPUT_JSON_INVALID", "JSON contains a duplicate key")
        result[key] = value
    return result


def _parse_bounded_integer(text: str) -> int:
    digits = text[1:] if text.startswith("-") else text
    if len(digits) > CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS:
        _fail("CP75_INPUT_RESOURCE_LIMIT", "JSON integer text exceeds its cap")
    try:
        return int(text, 10)
    except ValueError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_JSON_INVALID", "JSON integer text is invalid"
        ) from exc


def _reject_json_float(_text: str) -> object:
    _fail("CP75_INPUT_JSON_INVALID", "JSON floating values are forbidden")
    raise AssertionError("unreachable")


def _preflight_json_nesting(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
                _fail("CP75_INPUT_RESOURCE_LIMIT", "JSON nesting exceeds its cap")
        elif character in "]}" and depth:
            depth -= 1


def _walk_decoded(
    value: object,
    *,
    depth: int = 0,
    nodes: Optional[List[int]] = None,
    text_characters: Optional[List[int]] = None,
) -> None:
    if nodes is None:
        nodes = [0]
    if text_characters is None:
        text_characters = [0]
    nodes[0] += 1
    if depth > CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH:
        _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded JSON depth exceeds its cap")
    if nodes[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES:
        _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded JSON nodes exceed their cap")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if (
            len(str(abs(cast(int, value))))
            > CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS
        ):
            _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded integer exceeds its cap")
        return
    if type(value) is str:
        checked = cast(str, value)
        if any(0xD800 <= ord(character) <= 0xDFFF for character in checked):
            _fail("CP75_INPUT_ENCODING_INVALID", "decoded text contains a surrogate")
        if len(checked) > CP75_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS:
            _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded text item exceeds its cap")
        text_characters[0] += len(checked)
        if text_characters[0] > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded text total exceeds its cap")
        return
    if type(value) is list:
        items = cast(list, value)
        if len(items) > CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS:
            _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded array exceeds its cap")
        for item in items:
            _walk_decoded(
                item,
                depth=depth + 1,
                nodes=nodes,
                text_characters=text_characters,
            )
        return
    if type(value) is dict:
        mapping = cast(dict, value)
        if len(mapping) > CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS:
            _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded object exceeds its cap")
        for key, item in mapping.items():
            if type(key) is not str:
                _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", "JSON key is not text")
            if len(key) > CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS:
                _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded key exceeds its cap")
            if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                _fail("CP75_INPUT_ENCODING_INVALID", "decoded key has a surrogate")
            text_characters[0] += len(key)
            if (
                text_characters[0]
                > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS
            ):
                _fail("CP75_INPUT_RESOURCE_LIMIT", "decoded text total exceeds its cap")
            _walk_decoded(
                item,
                depth=depth + 1,
                nodes=nodes,
                text_characters=text_characters,
            )
        return
    _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", "decoded value has an alien type")


def _decode_payload(payload: bytes, label: str) -> Tuple[dict, bytes]:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("CP75_INPUT_ENCODING_INVALID", label + " contains a BOM")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_ENCODING_INVALID", label + " is not UTF-8"
        ) from exc
    if len(text) > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
        _fail("CP75_INPUT_RESOURCE_LIMIT", label + " decoded text exceeds its cap")
    _preflight_json_nesting(text)
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_json_float,
            parse_int=_parse_bounded_integer,
            parse_constant=_reject_json_float,
        )
    except CP75IndependentReviewResponseValidationError:
        raise
    except RecursionError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_RESOURCE_LIMIT", label + " parser recursion was bounded"
        ) from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_JSON_INVALID", label + " JSON is invalid"
        ) from exc
    _walk_decoded(value)
    if type(value) is not dict:
        _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", label + " root is not an object")
    try:
        replay = _plain_json_bytes(value)
    except (RecursionError, TypeError, ValueError) as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_CANONICAL_MISMATCH", label + " cannot be replayed"
        ) from exc
    if replay != payload:
        _fail("CP75_INPUT_CANONICAL_MISMATCH", label + " is not canonical JSON")
    return cast(dict, value), payload


def _decode_four_payloads_in_phase_order(
    payloads: Tuple[bytes, bytes, bytes, bytes],
) -> Tuple[dict, dict, dict, dict]:
    labels = ("request", "manifest", "response", "public key")
    texts: List[str] = []
    for payload, label in zip(payloads, labels):
        if payload.startswith(b"\xef\xbb\xbf"):
            _fail("CP75_INPUT_ENCODING_INVALID", label + " contains a BOM")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CP75IndependentReviewResponseValidationError(
                "CP75_INPUT_ENCODING_INVALID", label + " is not UTF-8"
            ) from exc
        if len(text) > CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS:
            _fail("CP75_INPUT_RESOURCE_LIMIT", label + " decoded text exceeds its cap")
        texts.append(text)
    for text in texts:
        _preflight_json_nesting(text)
    values: List[object] = []
    for text, label in zip(texts, labels):
        try:
            value = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_pairs,
                parse_float=_reject_json_float,
                parse_int=_parse_bounded_integer,
                parse_constant=_reject_json_float,
            )
        except CP75IndependentReviewResponseValidationError:
            raise
        except RecursionError as exc:
            raise CP75IndependentReviewResponseValidationError(
                "CP75_INPUT_RESOURCE_LIMIT", label + " parser recursion was bounded"
            ) from exc
        except (json.JSONDecodeError, ValueError) as exc:
            raise CP75IndependentReviewResponseValidationError(
                "CP75_INPUT_JSON_INVALID", label + " JSON is invalid"
            ) from exc
        values.append(value)
    for value in values:
        _walk_decoded(value)
    results: List[dict] = []
    for value, payload, label in zip(values, payloads, labels):
        if type(value) is not dict:
            _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", label + " root is not an object")
        try:
            replay = _plain_json_bytes(value)
        except (RecursionError, TypeError, ValueError) as exc:
            raise CP75IndependentReviewResponseValidationError(
                "CP75_INPUT_CANONICAL_MISMATCH", label + " cannot be replayed"
            ) from exc
        if replay != payload:
            _fail("CP75_INPUT_CANONICAL_MISMATCH", label + " is not canonical JSON")
        results.append(cast(dict, value))
    return cast(Tuple[dict, dict, dict, dict], tuple(results))


_PACKET_ORACLE_ZLIB_B64 = (
    "eNrsvWlz4li6Lfxf+ut74x4koLq5EfeDsZAMbYkENCB9qbDBBjTYPmVsQPfPv2vtrRmwnYOrsvpkdFRnJiBpa+9nWM/8//7x"
    "x93z3c0fi/V/3W/22xf8678WT//s/r69e96q//r96Y/H5ctiu3l8+P15sb5Lbn6/WSzunrY3D4u73zcPy7unO/zfw/b3P+4W"
    "j8nTy/ZG/PaPu9fN3e7uj99fHjbPzy93S9wveYpvtne/vyr/O3x+fPjH//nH3WG09lUrXlxN17eJFc9VNwkSN1xeDn8bRt0v"
    "duRsri9H60XbegrUbhzovXCRxK1gPnq6Vbv3N940HYZPt8MHS/Fxd7892foP+H6mhMu51bpVp93hZrfx2xeqNVOeb7xu7HvL"
    "+NrTX4JLZX1rxOvFof7bhWq9Lgxn68/d1o3RO9zMp93s9y94Znhr6E+3M2Vz23ZfAkM/3M2Gz8NEPyyNOPE9q3XtxS/LxH1Z"
    "4tq7mbJbJG6K9ar+fIo1d/g+r8v5dLecT7aB11UDby+eFzyM1re4NjhgXQneQ9UPgRG/+N7+aXkV8broBmtf4B0XV6P4xlPW"
    "gYp1et3o2h7iudbhtm2lfoJ7GOI+WGsvXc5HsXivRG9f4z19b/SM/UmXxjRePAy3i6T7kL3fIfCs19t5X1kaeuvG673g9/Et"
    "vsO7hYsD3vNhFC/UnrLAWV17wfrG2+PvDu7htvAu8hp5r6fbBPc3uEfYi0tF5XsE2X3FeoxeO5gPt0tjfQjm1uOtuo+yayOs"
    "42mhxq+3GyW+M0AP8+ka7/XMsxjGLe431rh+JS3cuT3s1/R+eTVSFm38abjbhbFfLw1nM3543vjz/u5WxZkYSnz7ML0P5sET"
    "1+Sr7v1CXa/N0FFBQy9Lb/8saO2q/wo6ad16WLfeS321twvc3lMAmrx9cJ9vL0FPFdqYq3FUvR5rfbxtj3BmMe4fP9wmeotn"
    "MFfX8d25e0j6Xi+v3AOehWeuse8u6HuyGSdd5dbYNd85BS28gKaw/yffIwStJqDvEO/wGsS9J7x7TFrEv/Ec/L09xR5hj2Pc"
    "yxgcLNuvPIs05O5wpjiLbog1feSadNF2Y+5TkOjPC9UR9IL9O4Bvj3+P75ZJHC+VHtcKnl63sA+Pvj1UrA34P/R3vh2EY2Oi"
    "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"
    "COj24adaO/GdKmx0+guebisywgwhJ9qQm21rk5/5T7bvv9J8fqX5/Erz+ZXm8yvN5xvTfCiDgP/AT7vMN0JfD3HAUSilWQZX"
    "8zM2Qvxnf3dmXa9FKKMt/ILKQhH0EbOk4uT+fUZo7KCUMqYsExOp6nOWe+i9EofO63ImEPy5gg1GW41pOxMF60/GGmxzW18H"
    "oRWBZ9u+PQ3H3uRgpv3Yh21npkPYaSzrWLQCze9Czqi+OsV3uK5MyTld5rkZQSYPtosrK8W7ZXvUSnGvw7UHuWI7qXVQIDP2"
    "LTynFt4TttN82kxx+SvDYQxZpVhXvKiHqE+FHt/2h32rz4vXEg8Y04M/X76dalRNf/hry1Hr/t3jmMXZ+MI7JaIfkSlb6v1b"
    "puQ1SpVLmeZ26Eui7ASfZDT5p/m+v1XOfVo4Ot+Xaw+yfqaUsv6yloL3I/n9m1Peqmls3xsP+JXe8yu952+W3kOabt0Sv2c2"
    "pZAhiftyHGMaVuNXH6PVz4t3Fek7J+NbJf/tcA/s6UnZfzZN5H72M6UxuS85v/1csTxL8YEZaOOSTt8uFXazdi4ZTc9d4pOk"
    "yKOIBbZIGePLS80Zy7r1YvJfTc6UsRr3Hr97vgO98brmd3U7NAJmdWD7OirfY+yZu8DWYVdaGx9WqanFsI+HSqCN1mPDbAeG"
    "vhlrq8NYu+gyJhEAp+K3wHOLHf7rWIbfMQ+j3vel9sgUnt+fbhbR3fb35OZhc4+r6uk7VVOylm1vaTy2JTPmW1hqx0wvDoRQ"
    "QagDrl50QQprQnIz8fd+uNoBhu39dLDH66ljz93A9AYcj9emOtpY9mhjhhciPadSVVywTpDEz2CRI/ISFcYHQmE3AZxPAm26"
    "trRJC5BXsdJRaIqUAjzPNveA+gc/jNpgn4jV26YdsMobm79SxvbkYHnDDknVVwOsbSrSZUwcA90EFmB4ALgRgJUIGWF6KGNv"
    "2La0i71vr7qWpm+wttBPXRz1SjFB2r7HDP3Fju4EkPoB759C1HQE6eJ7K5nGlufARHEggqK95ZktS4sTkgHMGbDHSgUZJAHg"
    "hqk6IIlBy6KLxGCGPswfQFjLXke+3U9Yoe6rhCHDrh/SnTGNxyAlP4zDALDYt/XQUn2YCwHdHTAvBmBJvLMxWluAhUG4Di3N"
    "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"
    "r+CHCkb7D8/Xrcq9rJ/IvfStCho8VROa708s8NWJHMFa/F/k//ZeslnGWe54ZT5R9V7H/d1qtaKnvy/4qJiNV/Zgkr6hcrZ8"
    "lltY81HmmCPDC3ptPtJxTqyI4cGOV7dC1x69y4ncBc5A5FqKvlyl77ZePyB71VfziavvJ+fZA+PWntnoPbBkjwnVbWX5m7Q/"
    "7okb5ipjDXLuypnnF70CqvsisHp1NuaJveNvmnr55BkJHurjPPdPvtLDWcUfunfeLymbuwmZzlqCmv0jckhZWwU6V0TetKTL"
    "OPdjF/aAwd6ZVjf/vFLTUXxWkwu17/WW8PkbJ95RzOQUGFTasGrZS6r+O+q/gGug7ZXMs7pnyStv3f9dTNU809c83znLwVFw"
    "7qTn+Eb4Q0/yEPDf9BH6Stgddf6AblL39H08NZ4l8H9Fn2X4v84zlRmWJ2MAMo5Q5szWYhHtDLNU5yd/5J51Os98R3Xb6k17"
    "6SD56yts5xo/Q+4RszVkx0fj950T2OlcXV2jNkDwflZvAhqY0+co7Bdp82APwOfKPXGH4I2E9ZBTzpBn/WLxOfacmDZl7oyg"
    "ndxucGv7KmJSwdVovWQ+dEWfnOXn2lzcc3JC9DJZi7m1bi+PC55cQ1OPFXris+N4NXvS38/13e7fVX13ua7aWnnsrtQRZcxS"
    "2N+05axwss3sXGHXSptPD7EPsodQIeNkLSRjmsDnT/+eNfQPeOY2lyPZnA7yaYE53F7eF7rmv6CvVfTPeRD90be5LoIt2fsi"
    "+tkUfrTqu9HufaYfmO9+i/vJ3zH/H7bD+3SU1emzD+o6oq1x9nfgqZtLRbxLXpdWXa/wz2B9Mo4y+eY1V2xmWQ9wfGZiDWP2"
    "dmG/AfaUm5+m/7N5AQ/l+/oe8wNGr0tjdTov66GWj/TPih+pVk9RytPCZ8M5DIWNdz3P+jZnvqPMri9rrYuY+nH8P/+u6Xet"
    "+SiZf5X1XMj8QZlOmWylLyuP4+cxhffP/FQ+w8f2vQtbWthGxIClnAIW/GJ335VblesZbyBdMZ9M+Jek/0zWv+JeIj+ugq23"
    "Ja6JRK5CY45V6SPLzqsWo5rLuFtVTmbYv0q/uR+cfijwusgn4Xr/Cbmvcg2+OJOyRjen4dzuqtD058zGruTZZXU+9fOt4rWr"
    "Ucy6HMZVhL9l7j77sx+Sm1yR0RWdMqv1byr8Hr7IyWGO4+6xtn7Kg0ulipVr6ydN5jSdnVUDj+Y01ThH9yN5HE3ZXtONOSaq"
    "79tD1vvItYYTKa9egyIXp5WONenTaexJxdd5HrMLe6IqEzMMuxT+HOv1RmC4k/O/t6471a7dmG2et7bT2k4HU8i01W/4+2+O"
    "Yt2MifFnWQ0/9Dbwz/aLUftMxqW1bZUX6r/XlKLPgj+f/Kt2jjWss/tn9busnhn32sl4JrEuZxkI/7tYQ1aTBhyl0Ue2zudc"
    "ZvNolRfo7VDkxR5E7irjCZyVEOU8nT1fyIVshl3TBtsBX9I+yPyY01e/7WY2xefiGcqM3NbK3re0tS5P80jhLz5/ncQ9XuU9"
    "3sc9BZ45R4Nf46uo+2+c5n5XY1jn7GLI7SV0X/xb4U+uYts6nhWyVMT0ZO13KfeLzxTKUc7euM9z80oblzXwjBvIvoU5vXJG"
    "NmwM3EvYGHVe0IvP37SpA9DlspmnlemCj9jnNfkS53JlLXrtVupBj3tNFT4qJaNtM9OJpa//PH6u+yaur6r11NX4YU5T+7N+"
    "gGujeRb7LfmDPdLnKjHZvuA9xnlEjujD5F1avPVoo+1pX4sYYXkt/t5mb1hlvRC91OrnXsSM7YWKfavFtaQ+wTtxXkBb1MH+"
    "k7kkWC8x3zPe+wFYsWemq9ZYyt8HofNFP8t9DLzWutFaqaktDmN1DbmxEt9B3sdLbfsaGJN/BqoV/dvI12Q+W6GjmOni6Ys9"
    "+Ocpevxi+4plm+1xQ/9IvmM+xKSIHXO+i4gbEDMk8XPwzh4uDMrCkq+O4quzrCdMrsvfkg0n6PzL/C19qHBGLGsbBJ6uyLe3"
    "5JrUlemWteS57mC/iO2p5+f6nL2BxSzKMo9B1CxkfL6WugI2iKEfRPxF5uLmOurlqG+Q3eCpY3l39vpTcgL7JPfyoGAvo3d/"
    "P26fORP69GF33syfmv6pXn1Pux+Ss/XnnKe/xr3PyoLa/ZoyWmvs6dH3VezRfUN3n5BPYfPewqf5ER1Uv/enYPZTMrrU20Uv"
    "GNCEnC0izpXrCG+U0zHdU7lr2ZwgYH3nG3LVRJ5TEZf2H2LaZCF7PEA2dmW/J85FV9jjK2aPz+ye9H2tYcPWfpvNid1W/bzZ"
    "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"
    "ziVlnyfP6IacBQq8LL2UJMobDpfQTTXOZuUsTs5ZShkD5bEy7F3osqKzaq7jPbrm3Muwu+bsSM7IhF6Gvzfg7L1sJoI2az7d"
    "y8D/jZF74G7YGvajO16b3XwzxnB2HAGfreIePXmwMdPqcSbEt5t/SEyvoEf2K0IPVm8ej7MFJ7Ca9nqvp+zKWEfBBtJeksEK"
    "HR7J5G/TsT8cH/xgIxxlI/w0OyKZ0T3Z/fGYXlnM7BvZTh587PtC/P5wrKCQzT/MYDi5UpjnCvlNMJLq47pdybPnGAzJWjI4"
    "+J0M0KweO8AWyOvcE9ihb+cTjrEEfgSTHWEYHGBd/KwqY/VsITsEAJOuYwb8nu9ZZG4mbPLT2DS/LL9wG981tzSfkDKEEvxf"
    "1u/lQLbbufgnsTGgx+KY9z8qd0KWJ+4hGfivkU91cAYwZFDy05GNxmeoo9P5ygp3WMypxH1pmDtY3/E+5WP9R6u3M6/l9kDN"
    "G3G3nO0Bv3XOmZkW56Pp3S2wbaXf4XyMIdkJW/a1F4YtcAr7rfXHLZ2MffakNzl/AHsEHFjtPlZyDIXnvx7+epgtXtZ/3ZGR"
    "8J7eLUJF+BP/Plmu8AUkIATTf/33v7q7hrRQ7nbS9Er3qlyEuldxeKKRCW0PZjyWbkdB/W5Hg2rrPT9cPn0ZRe5Jf9G4GY7a"
    "LUi9FAoPnflo6PT6g9E2CfNfLxr9+10jNUHNRkx2ful2sqm+zSxPttnM8qScRlxEw7Xjs2wTBDPS6b0ANkCdwaR20hbZ183G"
    "98mikYbsoLLiZ4FYvDZnTz72qAP18ckb12YJ8RjPd33TsOOrwb2Rq9Fs2Det1poqsr+4/CVXo7mozEYq/Ps9JXrj3yrzxjXh"
    "jf808wQezzh+BHCYbtNA44iUvtHiyJq5x9EjAUfzDGVkjxk2Vi7b73MUrc4wzqTCUax9jjkBnID7pZmDp3W3lVMjs7hoHGf8"
    "946O33BtmTTNTSOXpoEM5dZ9d2vOYhWoGt801FXveJSH6E7kiU/XM/xGO3c3ZrmQ5E1CCCvIaON5sms83+O7YDaeWZAX/Q7c"
    "DcqbGonVvUooPK88Y6czX2Vee35oNnJmrEs6DmSSRcz36nmknRbO4t1t86+bp34mKtSUuyZ3r7TVPiHydDxaQ1VW8999Ust8"
    "0UEMtbNQmLB8om+/T/MwOcBnk3Vk3RJpbiINjbRNniZQ+9JcmH63nYEcV3R7HJwBYTh1BwuVG5kQdW2Ge01SIMP+X3guMv6w"
    "w7DlJiqkZBtFmJ9gz7R+ypzpHi3rmr9juNo1XI17Fv/HaQUxXe0w004b+6HoRmW0h4wOWLvBhYY7wH2j3jy1sRXeS0Kf4z+M"
    "Lcoxm0LhO2fYx/kT3OJQCJPjOuCUifdaO/eWhdGWljSmyjeRSfQpz/7cplb47NmpF/7umakP6vWTi41w146kCXE/3p2mg327"
    "7eG3vTll5m5c577TjatTziDXgLnePJb7e7bHG1t1nD/W2ttR39w1WUg6n1POCJfv6dLs8L2nNyPj/VMuQASfrsdpQVz8WTU+"
    "g+fXfsx9tnMObRB79cONyPgdToi93PEewoV8vmdIQAi5qiiO+kHJQK6RVeX6VhXjZPSPcs/zunAvBJLR/0r2aSOvznD1YbOP"
    "tNM/8/6fdw64S48q9ZSOmVHvrewsvB82KJzovSh9mS3Wx/6fWehMvVos4pawKmwP3xfpjtP3qwO3yKf9wTln6KcM67i35u+9"
    "o2ekvX9Q9/1w8f+14O+fUXz/AzIxe27T1X24aaiwQkfTxN/gMzcbc+AzuWPA8ZWs/wI3e+Ypm42zH8zSgthl5KswjFgDhk7T"
    "BeK3dMS9Vs0POvgevR75A3XiQGDINH3UVZhyH1u09v2gb81Lv3u1mQ0ylAj5/0zILvZPeC/52ijv0yxwtvC3eM6NP7qtLWmY"
    "gpEyRaEzFXIZzb5dPv9xfVNZ9x836+sb7Y/+orK+tp+Tv/ka39M1WrNvzWP2C791tVpNdpm/204/9tmGo8FMfU+X33MqluF7"
    "6x7wauZvx15FOL7itPD83LOQ+/D+u3nqmgf83dOb02AtD2MnzP7tjOpRw6ppe9hs/NF83Mws/v7pWOrUvdD5e++w36d+b1X2"
    "+OzmLKfu9Yy/D10y3LBZjSf6civn6rHJzlj0l9LPejtKYwsWO/U56nyO8+3Wqc/R2sh+/TBOOfn3tur3fgqmOXUvt+aC6zoT"
    "/4j8179n70mh+RvjBIOBY9n03UeO08Nzy29H+jNtyrVoqOYb1IGPpnp9d7m9Poa5B09fvjZb0HvKh78ekZo6bI+W+G3/+fDn"
    "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"
    "qFYDcWmq+vfJNop3Z9f0wrNwSZ+uksdmZrlefC3l5kQ6MYpBwL/O8ftCclKZ/3Cr5kyNnqRvPJd7MinmT3V8LsOR6145r/d6"
    "7zS7/aPnGp4lvzmflv7kVHz6KAZ8m/jNET+Qvr6UozEekPg4zGczDpGJGcyLcYF4H+I8URRLTGX7pvazclDHY5I/5zfe0rvk"
    "MoaM2an9S5rzpXmEdB2xP0H7HN8HyBpL9LuiB102Ao54yPj978A6PvBFPACRd2flSsyaPGa254BteOwpX1Jy75boUcbDhVvB"
    "UpeFxOuyzx3r52R/CpwL5QPh3Fnul8R7OJL21hH5Uc/Kksw0fsz9gp/77999Jqf6UNHe82ziMyvsJ2NDwl3lsycxM8URj573"
    "MctXaSQx0MjHov3XpaSEe8J9o+7Y38v0LixqP8BnOYIzHs/Mt54Ql0+/T+KDO8rpRDizCuNHupYlbxrO4MWVnMY+T7fbKePp"
    "SgyLPOYdYxOwpd+h+4CBBllOLvM9r9FexrIs/Eras/vby1k2Dl7k8ogM6lvqacafA/7+HX2CTsLXLvCi9zidx2X8zPPM21On"
    "P2yqfYeeyXHNJ7jbnv00i2OZU2UbK4mODi6i+gGH97FouxqDitUetQefCzUaIi9JjCpZZ94uZu1dZh8jHjTzVtr8gRynq7Sk"
    "LfYrYJ+MLA8632aDNkb0qeTyIT+t4chrjyBXw2W7ZzOfDR05GPUgm/h/3JtRR9Zbu2M+reU1bkbC297x/gFj3QxHz+2Bxue8"
    "gCw4O9isEN8ffS/jcD0OYArhk7aHS+emv8MeALNMHqd49lHmt7LvbTehd/BbteL3Kh3DFlFSoibxrizPKuGAu9EzSj4gYNw1"
    "yhVBHgcjyxg6jdE1dNmQeewoHh3poiynX9XVwNdmzPa6muOMRzmZpJnv9zyfupHyHh/NWVxuTh52ypUQ3gYxbWOwskaD0arf"
    "3zUKpbwXESc6yk/mbcj3fb7lod+lb9tOzgG+l5HFKoXaB8ZxX1Q9D+N6EkvM7O3lVumoC80DTjHt1mzUatujXa3IgYvvgdRu"
    "kDPgMvfHfAf23hnXmVsh/mEsMchg9zmxLfUebHNFMJS6MwrTXzlhmvMjvnJe79h65aYRl1oHyvepzQaZWFL8vcOW0xk6rCmK"
    "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"
)


def _packet_oracle() -> Dict[str, bytes]:
    try:
        raw = zlib.decompress(base64.b64decode(_PACKET_ORACLE_ZLIB_B64, validate=True))
        encoded = cast(Dict[str, str], json.loads(raw.decode("ascii")))
        result = {
            path: base64.b64decode(encoded[path].encode("ascii"), validate=True)
            for path in _PACKET_PATHS
        }
    except (KeyError, ValueError, TypeError, zlib.error) as exc:
        raise RuntimeError("independent CP75 packet oracle cannot be decoded") from exc
    if tuple(result) != _PACKET_PATHS:
        raise RuntimeError("independent CP75 packet oracle order differs")
    return result


def _ordered_digest(domain: bytes, digests: Tuple[str, ...]) -> str:
    try:
        raw = b"".join(bytes.fromhex(item) for item in digests)
    except ValueError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_DIGEST_MISMATCH", "ordered digest vector is not hexadecimal"
        ) from exc
    return hashlib.sha256(domain + raw).hexdigest()


def _verify_zero_carrier_digest(
    record: dict,
    carrier: str,
    domain: bytes,
    *,
    code: str = "CP75_INPUT_DIGEST_MISMATCH",
) -> None:
    supplied = record.get(carrier)
    if not _is_sha256(supplied):
        _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", carrier + " is not SHA-256")
    body = dict(record)
    body[carrier] = _ZERO_SHA256
    expected = hashlib.sha256(domain + _plain_json_bytes(body)).hexdigest()
    if supplied != expected:
        _fail(code, carrier + " differs from its exact zero-carrier digest")


def _require_exact_keys(value: dict, keys: Tuple[str, ...], label: str) -> None:
    if tuple(value) != tuple(sorted(keys)):
        _fail("CP75_INPUT_FIELD_SET_MISMATCH", label + " field set differs")


def _require_sha(value: object, label: str) -> str:
    if not _is_sha256(value):
        _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", label + " is not SHA-256")
    return cast(str, value)


def _require_text(value: object, label: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", label + " is not exact text")
    return cast(str, value)


def _require_identifier_vector(value: object, label: str) -> Tuple[str, ...]:
    if type(value) is not list:
        _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", label + " is not an array")
    checked = tuple(cast(List[object], value))
    if any(not _is_identifier(item) for item in checked) or len(set(checked)) != len(
        checked
    ):
        _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", label + " identifiers differ")
    return cast(Tuple[str, ...], checked)


def _verify_request_record_digests(request: dict) -> None:
    subject = cast(dict, request["review_subject"])
    _verify_zero_carrier_digest(
        subject,
        "subject_sha256",
        b"cp75-test28-production-schema-acceptance-review-subject-v1\0",
    )
    criteria = cast(List[dict], request["ordered_review_criteria"])
    for criterion in criteria:
        _verify_zero_carrier_digest(
            criterion,
            "record_sha256",
            b"cp75-test28-production-schema-acceptance-review-criterion-v1\0",
        )
    contract = cast(dict, request["response_contract"])
    _verify_zero_carrier_digest(
        contract,
        "record_sha256",
        b"cp75-test28-production-schema-acceptance-review-response-contract-v1\0",
    )
    artifacts = cast(List[dict], request["ordered_packet_artifacts"])
    for artifact in artifacts:
        _verify_zero_carrier_digest(
            artifact,
            "record_sha256",
            b"cp75-test28-production-schema-acceptance-review-packet-artifact-v1\0",
        )
    criterion_digests = tuple(
        _require_sha(item["record_sha256"], "criterion record digest")
        for item in criteria
    )
    artifact_digests = tuple(
        _require_sha(item["record_sha256"], "artifact record digest")
        for item in artifacts
    )
    if tuple(request["ordered_review_criterion_record_sha256s"]) != criterion_digests:
        _fail("CP75_INPUT_DIGEST_MISMATCH", "criterion digest vector differs")
    if request["ordered_review_criteria_sha256"] != _ordered_digest(
        b"cp75-test28-production-schema-acceptance-review-criterion-record-digests-v1\0",
        criterion_digests,
    ):
        _fail("CP75_INPUT_DIGEST_MISMATCH", "ordered criterion digest differs")
    if tuple(request["ordered_packet_artifact_record_sha256s"]) != artifact_digests:
        _fail("CP75_INPUT_DIGEST_MISMATCH", "artifact digest vector differs")
    if request["ordered_packet_artifacts_sha256"] != _ordered_digest(
        b"cp75-test28-production-schema-acceptance-review-packet-artifact-record-digests-v1\0",
        artifact_digests,
    ):
        _fail("CP75_INPUT_DIGEST_MISMATCH", "ordered artifact digest differs")
    _verify_zero_carrier_digest(
        request,
        "record_sha256",
        CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION.encode("ascii") + b"\0",
    )


def _mgf1_sha256(seed: bytes, output_length: int) -> bytes:
    if type(seed) is not bytes or type(output_length) is not int:
        raise TypeError("independent CP75 MGF1 inputs have wrong exact types")
    if not 0 <= output_length <= 351:
        raise ValueError("independent CP75 MGF1 length is outside the profile")
    result = bytearray()
    counter = 0
    while len(result) < output_length:
        result.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(result[:output_length])


def _verify_rsa_pss_sha256_3072(
    message: bytes, modulus: bytes, signature: bytes
) -> bool:
    if (
        type(message) is not bytes
        or type(modulus) is not bytes
        or type(signature) is not bytes
    ):
        raise TypeError("independent CP75 RSA-PSS inputs must be exact bytes")
    if len(modulus) != 384 or len(signature) != 384:
        return False
    modulus_integer = int.from_bytes(modulus, "big")
    if (
        modulus_integer.bit_length() != 3_072
        or modulus_integer % 2 == 0
        or math.gcd(modulus_integer, 65_537) != 1
    ):
        return False
    signature_integer = int.from_bytes(signature, "big")
    if signature_integer >= modulus_integer:
        return False
    encoded = pow(signature_integer, 65_537, modulus_integer).to_bytes(384, "big")
    if encoded[-1] != 0xBC:
        return False
    masked_db = encoded[:351]
    encoded_hash = encoded[351:383]
    if masked_db[0] & 0x80:
        return False
    mask = _mgf1_sha256(encoded_hash, 351)
    data_block = bytearray(left ^ right for left, right in zip(masked_db, mask))
    data_block[0] &= 0x7F
    if data_block[:318] != b"\0" * 318 or data_block[318] != 0x01:
        return False
    salt = bytes(data_block[319:351])
    message_hash = hashlib.sha256(message).digest()
    expected_hash = hashlib.sha256(b"\0" * 8 + message_hash + salt).digest()
    return hmac.compare_digest(encoded_hash, expected_hash)


def _validate_rsa_vectors(vectors: dict) -> None:
    rows = cast(List[dict], vectors["rsa_pss_math_vectors"])
    if len(rows) != 3:
        raise RuntimeError("independent CP75 RSA vector inventory differs")
    expected_ids = (
        "exact-production-domain-positive-untrusted-math-only",
        "bit-flipped-signature-negative",
        "different-domain-negative",
    )
    if tuple(row["vector_id"] for row in rows) != expected_ids:
        raise RuntimeError("independent CP75 RSA vector order differs")
    for row in rows:
        unsigned = cast(dict, row["unsigned_response_signature_preimage_object"])
        domain_id = cast(str, row["message_domain_id"])
        message = domain_id.encode("ascii") + b"\0" + _plain_json_bytes(unsigned)
        modulus = bytes.fromhex(cast(str, row["modulus_hex"]))
        signature = bytes.fromhex(cast(str, row["signature_hex"]))
        actual = _verify_rsa_pss_sha256_3072(message, modulus, signature)
        if actual is not row["expected_signature_math_valid"]:
            raise RuntimeError("independent CP75 RSA vector result differs")
        if row["authority_effect"] != "NONE" or row["trust_or_authority_asserted"]:
            raise RuntimeError("independent CP75 RSA vector asserts authority")
    if not rows[0]["uses_exact_production_response_signature_domain"]:
        raise RuntimeError("independent CP75 positive vector uses the wrong domain")
    if rows[2]["uses_exact_production_response_signature_domain"]:
        raise RuntimeError("independent CP75 wrong-domain vector is mislabeled")


def _validate_packet_oracle(packet: Mapping[str, bytes]) -> Tuple[dict, dict]:
    if (
        type(packet) is not dict
        or set(packet) != set(_PACKET_PATHS)
        or any(type(item) is not bytes for item in packet.values())
    ):
        raise RuntimeError("independent CP75 packet path/type inventory differs")
    request_bytes = packet[_REQUEST_PATH]
    manifest_bytes = packet[_MANIFEST_PATH]
    if (
        len(request_bytes) != _EXPECTED_REQUEST_BYTES
        or hashlib.sha256(request_bytes).hexdigest() != _EXPECTED_REQUEST_SHA256
        or len(manifest_bytes) != _EXPECTED_MANIFEST_BYTES
        or hashlib.sha256(manifest_bytes).hexdigest() != _EXPECTED_MANIFEST_SHA256
    ):
        raise RuntimeError("independent CP75 request or manifest byte pin differs")
    request, _ = _decode_payload(request_bytes, "embedded request")
    manifest, _ = _decode_payload(manifest_bytes, "embedded manifest")
    if (
        request.get("schema_version")
        != CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION
    ):
        raise RuntimeError("independent CP75 request schema oracle differs")
    if manifest.get("schema_version") != (
        "cp75-test28-production-schema-acceptance-review-packet-manifest-v1"
    ):
        raise RuntimeError("independent CP75 manifest schema oracle differs")
    criteria = cast(List[dict], request.get("ordered_review_criteria"))
    artifacts = cast(List[dict], request.get("ordered_packet_artifacts"))
    contract = cast(dict, request.get("response_contract"))
    subject = cast(dict, request.get("review_subject"))
    if (
        len(criteria) != 12
        or tuple(item["criterion_id"] for item in criteria)
        != CP75_INDEPENDENT_TEST28_CRITERION_IDS
        or tuple(item["criterion_ordinal"] for item in criteria) != tuple(range(1, 13))
    ):
        raise RuntimeError("independent CP75 criterion oracle differs")
    if (
        len(artifacts) != 6
        or tuple(item["path"] for item in artifacts) != _PACKET_PATHS[:6]
        or tuple(item["artifact_ordinal"] for item in artifacts) != tuple(range(1, 7))
    ):
        raise RuntimeError("independent CP75 artifact oracle differs")
    if tuple(
        (item["criterion_id"], tuple(item["assigned_reviewer_roles"]))
        for item in criteria
    ) != tuple(
        (
            criterion_id,
            tuple(role for role, ids in _ROLE_COVERAGE if criterion_id in ids),
        )
        for criterion_id in CP75_INDEPENDENT_TEST28_CRITERION_IDS
    ):
        raise RuntimeError("independent CP75 criterion role coverage differs")
    if _plain_json_bytes(contract) != _plain_json_bytes(_expected_response_contract()):
        raise RuntimeError("independent CP75 complete response contract differs")
    if (
        contract["current_subject_production_schema_accept_permitted"]
        or request["current_subject_production_executable_schema_acceptance_eligible"]
        or subject["candidate_schema_executable"]
        or subject["primary_decision_semantics_resolved"]
        or subject["schema_acceptance_independent"]
        or subject["candidate_schema_accepted"]
        or subject["authoritative_for_production"]
        or request["candidate_descriptor_acceptance_effective"]
        or request["schema_acceptance_effective"]
        or request["production_execution_authorized"]
    ):
        raise RuntimeError("independent CP75 request oracle overclaims acceptance")
    if (
        tuple(request["production_gate_states"]) != _MISSING_GATES
        or tuple(request["draft_blocker_states"]) != _MISSING_BLOCKERS
        or request["formal_test_28_status"] != "OPEN"
    ):
        raise RuntimeError("independent CP75 request oracle closes a gate")
    expected_context = hashlib.sha256(
        b"cp75-test28-production-schema-acceptance-review-context-v1\0"
        + _plain_json_bytes(
            {
                "acceptance_target": request["acceptance_target"],
                "review_round_ordinal": request["review_round_ordinal"],
                "subject_record_sha256": subject["subject_sha256"],
            }
        )
    ).hexdigest()
    if (
        request["review_round_ordinal"] != 1
        or request["review_context_sha256"] != expected_context
        or request["review_context_randomness_used"]
        or request["review_context_freshness_claimed"]
        or request["review_context_challenge_claimed"]
        or request["review_context_replay_prevention_claimed"]
    ):
        raise RuntimeError("independent CP75 review context semantics differ")
    _verify_request_record_digests(request)
    for artifact, path in zip(artifacts, _PACKET_PATHS[:6]):
        content = packet[path]
        if (
            artifact["content_bytes"] != len(content)
            or artifact["lf_count"] != content.count(b"\n")
            or artifact["content_sha256"] != hashlib.sha256(content).hexdigest()
            or artifact["issued"]
            or artifact["external_identity_present"]
            or artifact["external_key_present"]
            or artifact["external_signature_present"]
            or artifact["acceptance_effect"] != "NONE"
        ):
            raise RuntimeError("independent CP75 artifact content oracle differs")
    checklist = packet[_CHECKLIST_PATH]
    _validate_criteria_and_checklist_semantics(tuple(criteria), checklist)
    if (
        len(packet[_VECTORS_PATH]) != _EXPECTED_VECTORS_BYTES
        or hashlib.sha256(packet[_VECTORS_PATH]).hexdigest() != _EXPECTED_VECTORS_SHA256
    ):
        raise RuntimeError("independent CP75 vectors byte custody differs")
    vectors, _ = _decode_payload(packet[_VECTORS_PATH], "embedded vectors")
    _verify_zero_carrier_digest(
        vectors,
        "body_sha256",
        b"cp75-test28-production-schema-acceptance-review-response-contract-and-test-vectors-v1\0",
    )
    _validate_vectors_semantics(vectors, contract, subject)
    _validate_rsa_vectors(vectors)
    _validate_templates_semantics(packet, request, subject)
    entries = cast(List[dict], manifest.get("ordered_packet_files"))
    if (
        manifest.get("packet_file_count") != 7
        or len(entries) != 7
        or tuple(item["ordinal"] for item in entries) != tuple(range(1, 8))
        or tuple(item["path"] for item in entries) != _PACKET_PATHS[:7]
        or any(item["path"] == _MANIFEST_PATH for item in entries)
    ):
        raise RuntimeError("independent CP75 seven-entry manifest differs")
    for entry, path in zip(entries, _PACKET_PATHS[:7]):
        content = packet[path]
        _verify_zero_carrier_digest(
            entry,
            "entry_sha256",
            b"cp75-test28-production-schema-acceptance-review-packet-file-v1\0",
        )
        if (
            entry["content_bytes"] != len(content)
            or entry["lf_count"] != content.count(b"\n")
            or entry["content_sha256"] != hashlib.sha256(content).hexdigest()
        ):
            raise RuntimeError("independent CP75 manifest entry content differs")
    entry_digests = tuple(cast(str, entry["entry_sha256"]) for entry in entries)
    if tuple(manifest["ordered_packet_file_record_sha256s"]) != entry_digests:
        raise RuntimeError("independent CP75 manifest entry vector differs")
    if manifest["ordered_packet_files_sha256"] != _ordered_digest(
        b"cp75-test28-production-schema-acceptance-review-packet-file-record-digests-v1\0",
        entry_digests,
    ):
        raise RuntimeError("independent CP75 manifest ordered digest differs")
    _verify_zero_carrier_digest(
        manifest,
        "manifest_sha256",
        b"cp75-test28-production-schema-acceptance-review-packet-manifest-v1\0",
    )
    if (
        manifest["request_path"] != _REQUEST_PATH
        or manifest["request_canonical_json_bytes"] != len(request_bytes)
        or manifest["request_canonical_json_sha256"]
        != hashlib.sha256(request_bytes).hexdigest()
        or manifest["request_record_sha256"] != request["record_sha256"]
    ):
        raise RuntimeError("independent CP75 manifest request binding differs")
    return request, manifest


_CRITERION_RESULT_KEYS = (
    "criterion_id",
    "disposition",
    "finding_ids",
    "comment_sha256",
    "row_sha256",
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
_RESPONSE_SHA_FIELDS = (
    "request_canonical_json_sha256",
    "request_record_sha256",
    "subject_record_sha256",
    "review_packet_manifest_canonical_json_sha256",
    "review_packet_manifest_record_sha256",
    "checklist_sha256",
    "response_contract_test_vectors_sha256",
    "review_context_sha256",
    "scope_and_nonclaims_sha256",
    "reviewer_identity_sha256",
    "reviewer_organization_sha256",
    "reviewer_public_key_identity_sha256",
    "reviewer_public_key_document_sha256",
    "reviewer_authority_attestation_sha256",
    "appointment_evidence_sha256",
    "conflict_of_interest_attestation_sha256",
    "independence_attestation_sha256",
    "revocation_status_receipt_sha256",
    "review_toolchain_sha256",
    "full_review_report_sha256",
    "ordered_criterion_results_sha256",
    "review_notes_sha256",
    "reviewer_signature_sha256",
    "response_sha256",
)


def _expected_response_contract() -> dict:
    candidate_dispositions = (
        "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY",
        "DEFER",
        "REJECT",
        "ABSTAIN",
        "WITHDRAW",
    )
    production_dispositions = ("ACCEPT", "DEFER", "REJECT", "ABSTAIN", "WITHDRAW")
    candidate_outcomes = (
        "UNREVIEWED",
        "INCOMPLETE",
        "PARTIAL",
        "DEFERRED_PENDING_SPECIFIED_INPUTS",
        "REJECTED",
        "ABSTAINED",
        "WITHDRAWN",
        "REVOKED",
        "CONFLICT",
        "SUPERSEDED",
        "EXPIRED",
        "INVALID",
        "ACCEPTED_AS_NONEXECUTABLE_CANDIDATE_DESCRIPTOR_PACKET_ONLY",
    )
    production_outcomes = (
        "UNREVIEWED",
        "INCOMPLETE",
        "PARTIAL",
        "DEFERRED_PENDING_SPECIFIED_INPUTS",
        "REJECTED",
        "ABSTAINED",
        "WITHDRAWN",
        "REVOKED",
        "CONFLICT",
        "SUPERSEDED",
        "EXPIRED",
        "INVALID",
        "ACCEPTED",
    )
    body: Dict[str, object] = {
        "schema_version": "cp75-test28-production-schema-acceptance-review-response-contract-v1",
        "required_reviewer_roles": CP75_INDEPENDENT_TEST28_REVIEWER_ROLES,
        "required_reviewer_count": 4,
        "role_criterion_coverage": _ROLE_COVERAGE,
        "current_subject_role_criterion_disposition_requirements": (
            _CURRENT_ROLE_C12_REQUIREMENTS
        ),
        "current_subject_role_criterion_payload_requirements": (
            _CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS
        ),
        "criterion_result_schema_version": (
            "cp75-test28-production-schema-acceptance-review-criterion-result-v1"
        ),
        "criterion_result_exact_keys": _CRITERION_RESULT_KEYS,
        "response_schema_version": _SOURCE_RESPONSE_SCHEMA_VERSION,
        "response_exact_keys": _RESPONSE_KEYS,
        "reviewer_public_key_schema_version": _SOURCE_PUBLIC_KEY_SCHEMA_VERSION,
        "reviewer_public_key_exact_keys": _PUBLIC_KEY_KEYS,
        "criterion_disposition_domain": ("PASS", "DEFER", "FAIL", "ABSTAIN"),
        "candidate_descriptor_disposition_domain": candidate_dispositions,
        "production_executable_schema_disposition_domain": production_dispositions,
        "allowed_disposition_pairs": _ALLOWED_DISPOSITION_PAIRS,
        "current_subject_allowed_disposition_pairs": tuple(
            pair
            for pair in _ALLOWED_DISPOSITION_PAIRS
            if pair != ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY", "ACCEPT")
        ),
        "axis_disposition_derivation_precedence": _AXIS_DERIVATION_PRECEDENCE,
        "criterion_result_branch_rules": _CRITERION_RESULT_BRANCH_RULES,
        "response_relation_and_nullability_branch_rules": (
            _RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES
        ),
        "finding_change_and_report_binding_rules": _FINDING_CHANGE_AND_REPORT_RULES,
        "candidate_descriptor_review_outcome_domain": candidate_outcomes,
        "production_schema_review_outcome_domain": production_outcomes,
        "candidate_conditional_acceptance_maps_to": "DEFER",
        "production_conditional_acceptance_maps_to": "DEFER",
        "distinct_reviewer_identity_required": True,
        "distinct_reviewer_key_identity_required": True,
        "external_trust_root_preexists_candidate_required": True,
        "authority_appointment_required": True,
        "conflict_of_interest_attestation_required": True,
        "independence_attestation_required": True,
        "revocation_check_required": True,
        "trusted_time_required": True,
        "signature_scheme_id": _SIGNATURE_SCHEME_ID,
        "reviewer_public_key_identity_formula": (
            "SHA256(cp65-test28-independent-reviewer-public-key-identity-v1\\0"
            "+canonical(reviewer_role,reviewer_identity_sha256,signature_scheme_id,"
            "authority_id,modulus_hex,public_exponent))"
        ),
        "key_identity_formula_binds_organization": False,
        "reviewer_public_key_document_digest_formula": (
            "SHA256(cp75-test28-production-schema-acceptance-reviewer-public-key-"
            "document-v1\\0+canonical(exact-public-key-document-with-document_"
            "sha256-set-to-64-zero-hex))"
        ),
        "reviewer_public_key_plain_sha256_binding_rule": (
            "response.reviewer_public_key_document_sha256=plain-SHA256-of-exact-"
            "supplied-canonical-public-key-document-bytes;the-internal-document_"
            "sha256-zero-carrier-digest-is-validated-separately;response."
            "reviewer_role=public-key.reviewer_role;response.reviewer_identity_"
            "sha256=public-key.reviewer_identity_sha256;response.reviewer_"
            "organization_sha256=public-key.reviewer_organization_sha256;response."
            "signature_scheme_id=public-key.signature_scheme_id;response.authority_"
            "id=public-key.authority_id;response.reviewer_public_key_identity_"
            "sha256=public-key.key_identity_sha256"
        ),
        "reviewer_public_key_modulus_and_exponent_grammar": (
            "modulus_hex=exact-768-lowercase-hex-characters;decoded-length=384;"
            "integer-bit_length=3072;high-bit-set;odd;gcd(modulus,65537)=1;"
            "public_exponent=65537;signature_scheme_id=exact-fixed-profile"
        ),
        "reviewer_public_key_and_response_interval_coherence_rule": (
            "exact-UTC-YYYY-MM-DDTHH:MM:SSZ;key-valid_from<key-valid_until;"
            "response-valid_from<=signed_at<response-valid_until;response-"
            "interval-contained-in-key-interval;coherence-only-no-clock-or-"
            "trusted-time-validity-claim"
        ),
        "criterion_result_digest_formula": (
            "SHA256(cp75-test28-production-schema-acceptance-review-criterion-result-v1\\0"
            "+canonical(exact-row-with-row_sha256-set-to-64-zero-hex))"
        ),
        "ordered_criterion_result_digest_formula": (
            "SHA256(cp75-test28-production-schema-acceptance-review-criterion-result-"
            "record-digests-v1\\0+concatenated-raw32-row-digests-in-role-coverage-"
            "order)"
        ),
        "response_signature_preimage_formula": (
            "cp75-test28-production-schema-acceptance-review-response-signature-"
            "preimage-v1\\0+canonical(response-with-reviewer_signature_hex-empty-"
            "and-signature_sha256-and-response_sha256-set-to-64-zero-hex)"
        ),
        "response_signature_sha256_formula": (
            "plain-SHA256-of-exact-384-raw-signature-bytes"
        ),
        "response_record_digest_formula": (
            "SHA256(cp75-test28-production-schema-acceptance-review-response-v1\\0"
            "+canonical(response-with-response_sha256-set-to-64-zero-hex-and-actual-"
            "signature-retained))"
        ),
        "current_subject_candidate_descriptor_accept_permitted": True,
        "current_subject_production_schema_accept_permitted": False,
        "signature_math_implies_authority": False,
        "supplied_response_validator_performs_trust_or_authority_validation": False,
        "local_response_issuance_performed": False,
        "local_key_generation_performed": False,
        "local_signing_performed": False,
        "external_review_performed": False,
        "candidate_descriptor_acceptance_claimed": False,
        "schema_acceptance_claimed": False,
        "production_execution_authorized": False,
        "record_sha256": _ZERO_SHA256,
    }
    body["record_sha256"] = hashlib.sha256(
        b"cp75-test28-production-schema-acceptance-review-response-contract-v1\0"
        + _plain_json_bytes(body)
    ).hexdigest()
    return body


def _expected_unissued_template(
    role: str,
    assigned: Tuple[str, ...],
    subject: dict,
    request: dict,
) -> dict:
    response: Dict[str, object] = {key: None for key in _RESPONSE_KEYS}
    response.update(
        {
            "schema_version": _SOURCE_RESPONSE_SCHEMA_VERSION,
            "request_schema_version": (
                CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION
            ),
            "subject_record_sha256": subject["subject_sha256"],
            "checklist_sha256": _EXPECTED_CHECKLIST_SHA256,
            "response_contract_test_vectors_sha256": _EXPECTED_VECTORS_SHA256,
            "review_round_ordinal": 1,
            "review_context_sha256": request["review_context_sha256"],
            "acceptance_target": request["acceptance_target"],
            "scope_and_nonclaims_sha256": subject["scope_and_nonclaims_sha256"],
            "reviewer_role": role,
            "signature_scheme_id": _SIGNATURE_SCHEME_ID,
            "ordered_criterion_results": tuple(
                {
                    "criterion_id": criterion_id,
                    "disposition": None,
                    "finding_ids": None,
                    "comment_sha256": None,
                    "row_sha256": None,
                }
                for criterion_id in assigned
            ),
        }
    )
    public_key: Dict[str, object] = {key: None for key in _PUBLIC_KEY_KEYS}
    public_key.update(
        {
            "schema_version": _SOURCE_PUBLIC_KEY_SCHEMA_VERSION,
            "reviewer_role": role,
            "signature_scheme_id": _SIGNATURE_SCHEME_ID,
            "public_exponent": 65_537,
        }
    )
    authority = {
        "schema_version": "cp75-test28-production-schema-acceptance-reviewer-authority-and-trust-template-v1",
        "template_only": True,
        "issued": False,
        "reviewer_role": role,
        "reviewer_identity_sha256": None,
        "reviewer_organization_sha256": None,
        "reviewer_public_key_document_sha256": None,
        "trust_root_id": None,
        "trust_policy_id": None,
        "authority_id": None,
        "subject_record_sha256": subject["subject_sha256"],
        "review_context_sha256": request["review_context_sha256"],
        "appointment_scope_id": None,
        "reviewer_authority_attestation_sha256": None,
        "appointment_evidence_sha256": None,
        "conflict_of_interest_attestation_sha256": None,
        "independence_attestation_sha256": None,
        "revocation_status_receipt_sha256": None,
        "valid_from_utc": None,
        "valid_until_utc": None,
        "authority_signature_scheme_id": None,
        "authority_signature_sha256": None,
        "authority_signature_hex": None,
        "record_sha256": None,
    }
    signoff = {
        "schema_version": "cp75-test28-production-schema-acceptance-reviewer-signoff-template-v1",
        "template_only": True,
        "issued": False,
        "reviewer_role": role,
        "review_response_path": None,
        "review_response_canonical_json_sha256": None,
        "review_response_record_sha256": None,
        "reviewer_public_key_document_path": None,
        "reviewer_public_key_document_sha256": None,
        "reviewer_authority_attestation_path": None,
        "reviewer_authority_attestation_sha256": None,
        "full_review_report_path": None,
        "full_review_report_sha256": None,
        "return_packet_complete": False,
        "external_review_performed": False,
        "candidate_descriptor_acceptance_effective": False,
        "schema_acceptance_effective": False,
        "signoff_packet_sha256": None,
    }
    template: Dict[str, object] = {
        "schema_version": (
            "cp75-test28-production-schema-acceptance-reviewer-unissued-template-v1"
        ),
        "template_only": True,
        "issued": False,
        "reviewer_role": role,
        "assigned_criterion_ids": assigned,
        "subject_record_sha256": subject["subject_sha256"],
        "review_context_sha256": request["review_context_sha256"],
        "checklist_sha256": _EXPECTED_CHECKLIST_SHA256,
        "response_contract_test_vectors_sha256": _EXPECTED_VECTORS_SHA256,
        "response_template": response,
        "reviewer_public_key_template": public_key,
        "authority_and_trust_template": authority,
        "reviewer_signoff_template": signoff,
        "external_review_performed": False,
        "external_reviewer_authority_verified": False,
        "candidate_descriptor_acceptance_effective": False,
        "schema_acceptance_effective": False,
        "subsequent_candidate_descriptor_development_qualification_construction_permitted": False,
        "production_execution_authorized": False,
        "acceptance_effect": "NONE",
        "template_sha256": _ZERO_SHA256,
    }
    template["template_sha256"] = hashlib.sha256(
        b"cp75-test28-production-schema-acceptance-reviewer-unissued-template-v1\0"
        + _plain_json_bytes(template)
    ).hexdigest()
    return template


def _validate_criteria_and_checklist_semantics(
    criteria: Tuple[dict, ...], checklist: bytes
) -> None:
    criterion_keys = (
        "acceptance_rule",
        "assigned_reviewer_roles",
        "blocking_for_candidate_descriptor_acceptance",
        "blocking_for_production_executable_schema_acceptance",
        "criterion_id",
        "criterion_ordinal",
        "external_reviewer_disposition_present",
        "local_pre_review_disposition",
        "local_pre_review_only",
        "record_sha256",
        "review_question",
        "review_question_sha256",
        "schema_version",
        "subject_json_pointers",
        "unexpected_findings_permitted",
    )
    if (
        len(checklist) != _EXPECTED_CHECKLIST_BYTES
        or checklist.count(b"\n") != _EXPECTED_CHECKLIST_LF_COUNT
        or hashlib.sha256(checklist).hexdigest() != _EXPECTED_CHECKLIST_SHA256
    ):
        raise RuntimeError("independent CP75 checklist byte custody differs")
    required_status = (
        b"Status: READY_FOR_EXTERNAL_REVIEW. No external review, authority, "
        b"acceptance, production execution, gate, blocker, evidence, or closure "
        b"is claimed.\n"
    )
    if checklist.count(required_status) != 1:
        raise RuntimeError("independent CP75 checklist nonclaim status differs")
    for ordinal, criterion in enumerate(criteria, 1):
        criterion_id = CP75_INDEPENDENT_TEST28_CRITERION_IDS[ordinal - 1]
        expected_roles = tuple(
            role for role, ids in _ROLE_COVERAGE if criterion_id in ids
        )
        expected_local = (
            "PRODUCTION_NONPASS_REQUIRED" if ordinal == 12 else "UNREVIEWED"
        )
        if (
            tuple(criterion) != tuple(sorted(criterion_keys))
            or criterion["schema_version"]
            != "cp75-test28-production-schema-acceptance-review-criterion-v1"
            or criterion["criterion_ordinal"] != ordinal
            or criterion["criterion_id"] != criterion_id
            or tuple(criterion["assigned_reviewer_roles"]) != expected_roles
            or criterion["blocking_for_candidate_descriptor_acceptance"]
            is (ordinal == 12)
            or criterion["blocking_for_production_executable_schema_acceptance"]
            is not True
            or criterion["local_pre_review_disposition"] != expected_local
            or criterion["local_pre_review_only"] is not True
            or criterion["external_reviewer_disposition_present"] is not False
            or criterion["unexpected_findings_permitted"] is not True
            or type(criterion["acceptance_rule"]) is not str
            or not criterion["acceptance_rule"]
            or type(criterion["review_question"]) is not str
            or not criterion["review_question"]
            or type(criterion["subject_json_pointers"]) is not list
            or not criterion["subject_json_pointers"]
            or any(
                type(pointer) is not str or not pointer.startswith("/")
                for pointer in criterion["subject_json_pointers"]
            )
        ):
            raise RuntimeError("independent CP75 criterion semantics differ")
        begin = (
            "<!-- CP75-CRITERION:" + criterion_id + ":QUESTION-BEGIN -->\n"
        ).encode("utf-8")
        end = ("<!-- CP75-CRITERION:" + criterion_id + ":QUESTION-END -->").encode(
            "utf-8"
        )
        if checklist.count(begin) != 1 or checklist.count(end) != 1:
            raise RuntimeError("independent CP75 checklist marker inventory differs")
        left = checklist.index(begin) + len(begin)
        right = checklist.index(end, left)
        question_bytes = cast(str, criterion["review_question"]).encode("utf-8") + b"\n"
        if (
            checklist[left:right] != question_bytes
            or hashlib.sha256(question_bytes).hexdigest()
            != criterion["review_question_sha256"]
        ):
            raise RuntimeError("independent CP75 checklist question differs")
    for role, ids in _ROLE_COVERAGE:
        role_line = ("- " + role + ": " + ", ".join(ids) + "\n").encode("utf-8")
        if checklist.count(role_line) != 1:
            raise RuntimeError("independent CP75 checklist role coverage differs")
    for ordinal, criterion_id in enumerate(CP75_INDEPENDENT_TEST28_CRITERION_IDS, 1):
        candidate = "no" if ordinal == 12 else "yes"
        local = "PRODUCTION_NONPASS_REQUIRED" if ordinal == 12 else "UNREVIEWED"
        claim_row = (
            "| "
            + str(ordinal)
            + " | "
            + criterion_id
            + " | "
            + candidate
            + " | yes | "
            + local
            + " |\n"
        ).encode("utf-8")
        if checklist.count(claim_row) != 1:
            raise RuntimeError("independent CP75 checklist claim matrix differs")
    for item in (
        _AXIS_DERIVATION_PRECEDENCE
        + _CRITERION_RESULT_BRANCH_RULES
        + _RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES
        + _FINDING_CHANGE_AND_REPORT_RULES
    ):
        if checklist.count(("- " + item + "\n").encode("utf-8")) != 1:
            raise RuntimeError("independent CP75 checklist rule projection differs")


def _validate_vectors_semantics(vectors: dict, contract: dict, subject: dict) -> None:
    expected_keys = (
        "all_vectors_nonreviewer_test_only",
        "allowed_disposition_pairs",
        "authority_effect",
        "axis_disposition_derivation_precedence",
        "body_sha256",
        "criterion_result_branch_rules",
        "criterion_result_exact_keys",
        "current_subject_role_criterion_payload_requirements",
        "digest_preimage_vectors",
        "finding_change_and_report_binding_rules",
        "response_contract",
        "response_contract_record_sha256",
        "response_exact_keys",
        "response_relation_and_nullability_branch_rules",
        "reviewer_public_key_exact_keys",
        "rsa_pss_math_vectors",
        "schema_version",
        "subject_record_sha256",
        "test_vector_only",
    )
    if (
        tuple(vectors) != tuple(sorted(expected_keys))
        or vectors["schema_version"]
        != "cp75-test28-production-schema-acceptance-review-response-contract-and-test-vectors-v1"
        or vectors["test_vector_only"] is not True
        or vectors["all_vectors_nonreviewer_test_only"] is not True
        or vectors["authority_effect"] != "NONE"
        or vectors["subject_record_sha256"] != subject["subject_sha256"]
        or vectors["response_contract_record_sha256"] != contract["record_sha256"]
        or _plain_json_bytes(vectors["response_contract"])
        != _plain_json_bytes(contract)
        or tuple(tuple(item) for item in vectors["allowed_disposition_pairs"])
        != _ALLOWED_DISPOSITION_PAIRS
        or tuple(vectors["axis_disposition_derivation_precedence"])
        != _AXIS_DERIVATION_PRECEDENCE
        or tuple(vectors["criterion_result_branch_rules"])
        != _CRITERION_RESULT_BRANCH_RULES
        or tuple(vectors["criterion_result_exact_keys"]) != _CRITERION_RESULT_KEYS
        or tuple(
            tuple(item)
            for item in vectors["current_subject_role_criterion_payload_requirements"]
        )
        != _CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS
        or tuple(vectors["finding_change_and_report_binding_rules"])
        != _FINDING_CHANGE_AND_REPORT_RULES
        or tuple(vectors["response_exact_keys"]) != _RESPONSE_KEYS
        or tuple(vectors["response_relation_and_nullability_branch_rules"])
        != _RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES
        or tuple(vectors["reviewer_public_key_exact_keys"]) != _PUBLIC_KEY_KEYS
    ):
        raise RuntimeError("independent CP75 vector semantic projection differs")
    digest_vectors = vectors["digest_preimage_vectors"]
    if type(digest_vectors) is not list or len(digest_vectors) != 1:
        raise RuntimeError("independent CP75 digest vector inventory differs")
    row_vector = digest_vectors[0]
    if (
        type(row_vector) is not dict
        or tuple(row_vector)
        != (
            "authority_effect",
            "canonical_record",
            "expected_record_sha256",
            "vector_id",
        )
        or row_vector["vector_id"] != "criterion-result-zero-carrier"
        or row_vector["authority_effect"] != "NONE"
    ):
        raise RuntimeError("independent CP75 digest vector differs")
    row = cast(dict, row_vector["canonical_record"])
    _verify_zero_carrier_digest(
        row,
        "row_sha256",
        b"cp75-test28-production-schema-acceptance-review-criterion-result-v1\0",
    )
    if row_vector["expected_record_sha256"] != row["row_sha256"]:
        raise RuntimeError("independent CP75 digest vector result differs")


def _validate_templates_semantics(
    packet: Mapping[str, bytes], request: dict, subject: dict
) -> None:
    for role, path in zip(CP75_INDEPENDENT_TEST28_REVIEWER_ROLES, _TEMPLATE_PATHS):
        template, _ = _decode_payload(packet[path], "embedded template")
        expected = _expected_unissued_template(
            role, dict(_ROLE_COVERAGE)[role], subject, request
        )
        if _plain_json_bytes(template) != _plain_json_bytes(expected):
            raise RuntimeError("independent CP75 nested template semantics differ")


def _validate_root_field_sets_and_types(
    request: dict,
    expected_request: dict,
    manifest: dict,
    expected_manifest: dict,
    response: dict,
    public_key: dict,
) -> None:
    _require_exact_keys(request, tuple(expected_request), "request")
    _require_exact_keys(manifest, tuple(expected_manifest), "manifest")
    _require_exact_keys(response, _RESPONSE_KEYS, "response")
    _require_exact_keys(public_key, _PUBLIC_KEY_KEYS, "public key")
    _require_text(request["schema_version"], "request/schema_version")
    _require_text(manifest["schema_version"], "manifest/schema_version")
    for name in _RESPONSE_SHA_FIELDS:
        _require_sha(response[name], "response/" + name)
    for name in (
        "schema_version",
        "request_schema_version",
        "acceptance_target",
        "reviewer_role",
        "signature_scheme_id",
        "trust_policy_id",
        "authority_id",
        "candidate_descriptor_disposition",
        "production_executable_schema_disposition",
        "signed_at_utc",
        "valid_from_utc",
        "valid_until_utc",
        "reviewer_signature_hex",
    ):
        _require_text(response[name], "response/" + name)
    if type(response["review_round_ordinal"]) is not int:
        _fail(
            "CP75_INPUT_FIELD_TYPE_MISMATCH",
            "response review round ordinal is not an integer",
        )
    for name in (
        "review_method_ids",
        "ordered_criterion_results",
        "ordered_criterion_result_sha256s",
        "open_finding_ids",
        "required_change_ids",
        "acknowledged_subject_open_item_ids",
    ):
        if type(response[name]) is not list:
            _fail(
                "CP75_INPUT_FIELD_TYPE_MISMATCH",
                "response/" + name + " is not an array",
            )
    for name in ("supersedes_response_sha256", "withdraws_response_sha256"):
        if response[name] is not None and not _is_sha256(response[name]):
            _fail(
                "CP75_INPUT_FIELD_TYPE_MISMATCH",
                "response/" + name + " is neither null nor SHA-256",
            )
    for name in (
        "reviewer_identity_sha256",
        "reviewer_organization_sha256",
        "key_identity_sha256",
        "document_sha256",
    ):
        _require_sha(public_key[name], "public-key/" + name)
    for name in (
        "schema_version",
        "reviewer_role",
        "signature_scheme_id",
        "authority_id",
        "modulus_hex",
        "valid_from_utc",
        "valid_until_utc",
    ):
        _require_text(public_key[name], "public-key/" + name)
    if type(public_key["public_exponent"]) is not int:
        _fail(
            "CP75_INPUT_FIELD_TYPE_MISMATCH",
            "public-key exponent is not an integer",
        )


def _validate_schema_versions(response: dict, public_key: dict) -> None:
    if (
        response["schema_version"] != _SOURCE_RESPONSE_SCHEMA_VERSION
        or response["request_schema_version"]
        != CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION
        or public_key["schema_version"] != _SOURCE_PUBLIC_KEY_SCHEMA_VERSION
        or response["signature_scheme_id"] != _SIGNATURE_SCHEME_ID
        or public_key["signature_scheme_id"] != _SIGNATURE_SCHEME_ID
    ):
        _fail("CP75_INPUT_SCHEMA_MISMATCH", "response or key schema differs")


def _validate_response_inventories(
    response: dict, public_key: dict, request: dict
) -> Tuple[str, Tuple[str, ...], Tuple[dict, ...], bool]:
    role = cast(str, response["reviewer_role"])
    if role not in CP75_INDEPENDENT_TEST28_REVIEWER_ROLES:
        _fail("CP75_INPUT_INVENTORY_MISMATCH", "reviewer role differs")
    if public_key["reviewer_role"] not in CP75_INDEPENDENT_TEST28_REVIEWER_ROLES:
        _fail("CP75_INPUT_INVENTORY_MISMATCH", "public-key reviewer role differs")
    assigned = dict(_ROLE_COVERAGE)[role]
    results_raw = cast(List[object], response["ordered_criterion_results"])
    withdrawal = (
        response["candidate_descriptor_disposition"] == "WITHDRAW"
        or response["production_executable_schema_disposition"] == "WITHDRAW"
    )
    if withdrawal:
        if results_raw:
            _fail("CP75_INPUT_INVENTORY_MISMATCH", "withdrawal has criterion rows")
        results: Tuple[dict, ...] = ()
    else:
        if len(results_raw) != len(assigned) or any(
            type(item) is not dict for item in results_raw
        ):
            _fail("CP75_INPUT_INVENTORY_MISMATCH", "criterion row count differs")
        results = tuple(cast(dict, item) for item in results_raw)
        for row in results:
            _require_exact_keys(row, _CRITERION_RESULT_KEYS, "criterion result")
        if tuple(row["criterion_id"] for row in results) != assigned:
            _fail("CP75_INPUT_INVENTORY_MISMATCH", "criterion result order differs")
    digest_vector = cast(List[object], response["ordered_criterion_result_sha256s"])
    if len(digest_vector) != len(results) or any(
        not _is_sha256(item) for item in digest_vector
    ):
        _fail("CP75_INPUT_INVENTORY_MISMATCH", "criterion digest vector differs")
    contract = cast(dict, request["response_contract"])
    if (
        tuple(contract["criterion_result_exact_keys"]) != _CRITERION_RESULT_KEYS
        or tuple(contract["response_exact_keys"]) != _RESPONSE_KEYS
        or tuple(contract["reviewer_public_key_exact_keys"]) != _PUBLIC_KEY_KEYS
        or tuple(tuple(item) for item in contract["allowed_disposition_pairs"])
        != _ALLOWED_DISPOSITION_PAIRS
    ):
        _fail("CP75_INPUT_INVENTORY_MISMATCH", "request response contract differs")
    return role, assigned, results, withdrawal


def _validate_response_and_key_digests(
    response: dict,
    response_bytes: bytes,
    public_key: dict,
) -> None:
    results = tuple(cast(dict, item) for item in response["ordered_criterion_results"])
    for row in results:
        _verify_zero_carrier_digest(
            row,
            "row_sha256",
            b"cp75-test28-production-schema-acceptance-review-criterion-result-v1\0",
        )
    row_digests = tuple(cast(str, row["row_sha256"]) for row in results)
    if tuple(response["ordered_criterion_result_sha256s"]) != row_digests:
        _fail("CP75_INPUT_DIGEST_MISMATCH", "criterion digest carrier vector differs")
    if response["ordered_criterion_results_sha256"] != _ordered_digest(
        b"cp75-test28-production-schema-acceptance-review-criterion-result-record-digests-v1\0",
        row_digests,
    ):
        _fail("CP75_INPUT_DIGEST_MISMATCH", "ordered criterion digest differs")
    _verify_zero_carrier_digest(
        response,
        "response_sha256",
        b"cp75-test28-production-schema-acceptance-review-response-v1\0",
    )
    _verify_zero_carrier_digest(
        public_key,
        "document_sha256",
        b"cp75-test28-production-schema-acceptance-reviewer-public-key-document-v1\0",
    )
    del response_bytes


def _validate_request_response_bindings(
    response: dict,
    public_key: dict,
    request: dict,
    request_bytes: bytes,
    manifest: dict,
    manifest_bytes: bytes,
    packet: Mapping[str, bytes],
) -> None:
    subject = cast(dict, request["review_subject"])
    expected = {
        "request_schema_version": request["schema_version"],
        "request_canonical_json_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "request_record_sha256": request["record_sha256"],
        "subject_record_sha256": subject["subject_sha256"],
        "review_packet_manifest_canonical_json_sha256": hashlib.sha256(
            manifest_bytes
        ).hexdigest(),
        "review_packet_manifest_record_sha256": manifest["manifest_sha256"],
        "checklist_sha256": hashlib.sha256(packet[_CHECKLIST_PATH]).hexdigest(),
        "response_contract_test_vectors_sha256": hashlib.sha256(
            packet[_VECTORS_PATH]
        ).hexdigest(),
        "review_round_ordinal": request["review_round_ordinal"],
        "review_context_sha256": request["review_context_sha256"],
        "acceptance_target": request["acceptance_target"],
        "scope_and_nonclaims_sha256": subject["scope_and_nonclaims_sha256"],
    }
    for name, value in expected.items():
        if response[name] != value:
            _fail("CP75_INPUT_BINDING_MISMATCH", "response binding differs at " + name)
    if (
        response["reviewer_public_key_document_sha256"]
        != hashlib.sha256(_plain_json_bytes(public_key)).hexdigest()
    ):
        _fail(
            "CP75_INPUT_BINDING_MISMATCH",
            "response public-key plain byte digest differs",
        )


_UTC_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


def _parse_utc(value: object, label: str) -> datetime:
    if type(value) is not str or _UTC_RE.fullmatch(cast(str, value)) is None:
        _fail("CP75_INPUT_FIELD_TYPE_MISMATCH", label + " has invalid UTC syntax")
    try:
        return datetime.strptime(cast(str, value), "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INPUT_FIELD_TYPE_MISMATCH", label + " has an invalid UTC value"
        ) from exc


def _validate_public_key_identity_and_intervals(
    response: dict, public_key: dict
) -> bytes:
    for name in (
        "reviewer_role",
        "reviewer_identity_sha256",
        "reviewer_organization_sha256",
        "signature_scheme_id",
        "authority_id",
    ):
        if response[name] != public_key[name]:
            _fail(
                "CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH",
                "response/public-key coherence differs at " + name,
            )
    modulus_hex = cast(str, public_key["modulus_hex"])
    if re.fullmatch(r"[0-9a-f]{768}", modulus_hex) is None:
        _fail(
            "CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH",
            "public-key modulus grammar differs",
        )
    modulus = bytes.fromhex(modulus_hex)
    modulus_integer = int.from_bytes(modulus, "big")
    if (
        public_key["public_exponent"] != 65_537
        or modulus_integer.bit_length() != 3_072
        or modulus_integer % 2 == 0
        or math.gcd(modulus_integer, 65_537) != 1
    ):
        _fail(
            "CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH",
            "public-key mathematical grammar differs",
        )
    identity_body = {
        "reviewer_role": public_key["reviewer_role"],
        "reviewer_identity_sha256": public_key["reviewer_identity_sha256"],
        "signature_scheme_id": public_key["signature_scheme_id"],
        "authority_id": public_key["authority_id"],
        "modulus_hex": modulus_hex,
        "public_exponent": public_key["public_exponent"],
    }
    identity = hashlib.sha256(
        b"cp65-test28-independent-reviewer-public-key-identity-v1\0"
        + _plain_json_bytes(identity_body)
    ).hexdigest()
    if (
        public_key["key_identity_sha256"] != identity
        or response["reviewer_public_key_identity_sha256"] != identity
    ):
        _fail(
            "CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH",
            "public-key identity formula differs",
        )
    key_from = _parse_utc(public_key["valid_from_utc"], "public-key valid_from")
    key_until = _parse_utc(public_key["valid_until_utc"], "public-key valid_until")
    response_from = _parse_utc(response["valid_from_utc"], "response valid_from")
    response_signed = _parse_utc(response["signed_at_utc"], "response signed_at")
    response_until = _parse_utc(response["valid_until_utc"], "response valid_until")
    if not (
        key_from < key_until
        and response_from <= response_signed < response_until
        and key_from <= response_from
        and response_until <= key_until
    ):
        _fail(
            "CP75_INPUT_PUBLIC_KEY_IDENTITY_MISMATCH",
            "public-key/response interval coherence differs",
        )
    return modulus


def _validate_signature_digest(response: dict) -> bytes:
    signature_hex = cast(str, response["reviewer_signature_hex"])
    if re.fullmatch(r"[0-9a-f]{768}", signature_hex) is None:
        _fail("CP75_INPUT_SIGNATURE_MISMATCH", "signature grammar or length differs")
    signature = bytes.fromhex(signature_hex)
    if response["reviewer_signature_sha256"] != hashlib.sha256(signature).hexdigest():
        _fail("CP75_INPUT_SIGNATURE_MISMATCH", "signature plain SHA-256 differs")
    return signature


def _validate_signature_math(response: dict, modulus: bytes, signature: bytes) -> None:
    preimage = dict(response)
    preimage["reviewer_signature_hex"] = ""
    preimage["reviewer_signature_sha256"] = _ZERO_SHA256
    preimage["response_sha256"] = _ZERO_SHA256
    message = (
        b"cp75-test28-production-schema-acceptance-review-response-signature-preimage-v1\0"
        + _plain_json_bytes(preimage)
    )
    if not _verify_rsa_pss_sha256_3072(message, modulus, signature):
        _fail("CP75_INPUT_RSA_PSS_MISMATCH", "RSA-PSS signature math differs")


def _stable_finding_union(results: Tuple[dict, ...]) -> Tuple[str, ...]:
    result: List[str] = []
    seen = set()
    for row in results:
        for finding_id in cast(List[str], row["finding_ids"]):
            if finding_id not in seen:
                seen.add(finding_id)
                result.append(finding_id)
    return tuple(result)


def _derive_axis_disposition(
    results: Tuple[dict, ...], applicable_ids: Tuple[str, ...], accept_value: str
) -> str:
    dispositions = tuple(
        cast(str, row["disposition"])
        for row in results
        if row["criterion_id"] in applicable_ids
    )
    if len(dispositions) != len(applicable_ids):
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "axis criterion coverage differs")
    if "FAIL" in dispositions:
        return "REJECT"
    if "DEFER" in dispositions:
        return "DEFER"
    if "ABSTAIN" in dispositions:
        return "ABSTAIN"
    if dispositions and all(item == "PASS" for item in dispositions):
        return accept_value
    _fail("CP75_INPUT_DISPOSITION_MISMATCH", "axis disposition cannot be derived")
    raise AssertionError("unreachable")


def _validate_dispositions(
    response: dict,
    role: str,
    assigned: Tuple[str, ...],
    results: Tuple[dict, ...],
    withdrawal: bool,
) -> None:
    candidate = cast(str, response["candidate_descriptor_disposition"])
    production = cast(str, response["production_executable_schema_disposition"])
    if (candidate, production) not in _ALLOWED_DISPOSITION_PAIRS:
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "disposition pair is not allowed")
    if withdrawal:
        if (
            (candidate, production) != ("WITHDRAW", "WITHDRAW")
            or response["withdraws_response_sha256"] is None
            or response["supersedes_response_sha256"] is not None
            or any(
                response[name]
                for name in (
                    "ordered_criterion_result_sha256s",
                    "open_finding_ids",
                    "required_change_ids",
                    "acknowledged_subject_open_item_ids",
                    "review_method_ids",
                )
            )
        ):
            _fail("CP75_INPUT_DISPOSITION_MISMATCH", "withdrawal branch differs")
        return
    if response["withdraws_response_sha256"] is not None:
        _fail(
            "CP75_INPUT_DISPOSITION_MISMATCH", "nonwithdrawal has a withdrawal target"
        )
    methods = _require_identifier_vector(
        response["review_method_ids"], "review methods"
    )
    if not methods:
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "substantive response has no method")
    open_findings = _require_identifier_vector(
        response["open_finding_ids"], "open findings"
    )
    changes = _require_identifier_vector(
        response["required_change_ids"], "required changes"
    )
    if tuple(response["acknowledged_subject_open_item_ids"]) != _KNOWN_OPEN_ITEM_IDS:
        _fail(
            "CP75_INPUT_DISPOSITION_MISMATCH", "subject open items are not acknowledged"
        )
    for row in results:
        disposition = row["disposition"]
        if disposition not in ("PASS", "DEFER", "FAIL", "ABSTAIN"):
            _fail("CP75_INPUT_DISPOSITION_MISMATCH", "criterion disposition differs")
        finding_ids = _require_identifier_vector(
            row["finding_ids"], "criterion finding IDs"
        )
        comment = _require_sha(row["comment_sha256"], "criterion comment digest")
        if comment == _ZERO_SHA256:
            _fail("CP75_INPUT_DISPOSITION_MISMATCH", "criterion reason digest is zero")
        if disposition in ("PASS", "ABSTAIN") and finding_ids:
            _fail("CP75_INPUT_DISPOSITION_MISMATCH", "PASS/ABSTAIN has findings")
        if disposition in ("DEFER", "FAIL") and not finding_ids:
            _fail("CP75_INPUT_DISPOSITION_MISMATCH", "DEFER/FAIL lacks findings")
    if open_findings != _stable_finding_union(results):
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "open finding union differs")
    if not set(changes) <= set(open_findings):
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "required changes lack findings")
    by_id = {cast(str, row["criterion_id"]): row for row in results}
    c12 = by_id[CP75_INDEPENDENT_TEST28_CRITERION_IDS[11]]
    if c12["disposition"] != _CURRENT_C12_DISPOSITION[role]:
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "current-subject C12 result differs")
    if _CURRENT_C12_DISPOSITION[role] == "ABSTAIN":
        if c12["finding_ids"]:
            _fail("CP75_INPUT_DISPOSITION_MISMATCH", "C12 abstention has findings")
    else:
        if (
            tuple(c12["finding_ids"]) != _KNOWN_OPEN_ITEM_IDS
            or changes != _KNOWN_OPEN_ITEM_IDS
        ):
            _fail("CP75_INPUT_DISPOSITION_MISMATCH", "C12 deferral payload differs")
    candidate_ids = tuple(
        criterion_id
        for criterion_id in assigned
        if criterion_id != CP75_INDEPENDENT_TEST28_CRITERION_IDS[11]
    )
    expected_candidate = _derive_axis_disposition(
        results, candidate_ids, "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY"
    )
    expected_production = _derive_axis_disposition(results, assigned, "ACCEPT")
    if candidate != expected_candidate or production != expected_production:
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "derived axis disposition differs")
    if production == "ACCEPT":
        _fail(
            "CP75_INPUT_DISPOSITION_MISMATCH",
            "current nonexecutable subject cannot receive production ACCEPT",
        )
    if response["full_review_report_sha256"] == _ZERO_SHA256:
        _fail("CP75_INPUT_DISPOSITION_MISMATCH", "full report pointer is zero")


def _build_custody(
    packet: Mapping[str, bytes], request: dict, manifest: dict
) -> CP75IndependentReviewPacketCustodyV1:
    templates = tuple(packet[path] for path in _TEMPLATE_PATHS)
    values: Dict[str, object] = {
        "schema_version": _CUSTODY_SCHEMA,
        "source_request_schema_version": (
            CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION
        ),
        "source_response_schema_version": _SOURCE_RESPONSE_SCHEMA_VERSION,
        "source_public_key_schema_version": _SOURCE_PUBLIC_KEY_SCHEMA_VERSION,
        "request_path": _REQUEST_PATH,
        "request_canonical_json_bytes": len(packet[_REQUEST_PATH]),
        "request_canonical_json_sha256": hashlib.sha256(
            packet[_REQUEST_PATH]
        ).hexdigest(),
        "request_record_sha256": request["record_sha256"],
        "subject_record_sha256": request["review_subject"]["subject_sha256"],
        "checklist_path": _CHECKLIST_PATH,
        "checklist_bytes": len(packet[_CHECKLIST_PATH]),
        "checklist_lf_count": packet[_CHECKLIST_PATH].count(b"\n"),
        "checklist_sha256": hashlib.sha256(packet[_CHECKLIST_PATH]).hexdigest(),
        "response_contract_test_vectors_path": _VECTORS_PATH,
        "response_contract_test_vectors_bytes": len(packet[_VECTORS_PATH]),
        "response_contract_test_vectors_sha256": hashlib.sha256(
            packet[_VECTORS_PATH]
        ).hexdigest(),
        "reviewer_template_paths": _TEMPLATE_PATHS,
        "reviewer_template_bytes": tuple(len(item) for item in templates),
        "reviewer_template_sha256s": tuple(
            hashlib.sha256(item).hexdigest() for item in templates
        ),
        "manifest_path": _MANIFEST_PATH,
        "manifest_canonical_json_bytes": len(packet[_MANIFEST_PATH]),
        "manifest_canonical_json_sha256": hashlib.sha256(
            packet[_MANIFEST_PATH]
        ).hexdigest(),
        "manifest_record_sha256": manifest["manifest_sha256"],
        "reviewer_roles": CP75_INDEPENDENT_TEST28_REVIEWER_ROLES,
        "criterion_ids": CP75_INDEPENDENT_TEST28_CRITERION_IDS,
        "role_criterion_coverage": _ROLE_COVERAGE,
        "signature_scheme_id": _SIGNATURE_SCHEME_ID,
        "request_and_manifest_oracle_deeply_reconstructed": True,
        "project_modules_imported": False,
        "path_io_performed": False,
    }
    return cast(
        CP75IndependentReviewPacketCustodyV1,
        _record(CP75IndependentReviewPacketCustodyV1, values),
    )


def cp75_build_independent_review_response_validator_bundle() -> CP75IndependentReviewResponseValidatorBundleV1:
    try:
        packet = _packet_oracle()
        request, manifest = _validate_packet_oracle(packet)
        custody = _build_custody(packet, request, manifest)
        values: Dict[str, object] = {
            "schema_version": CP75_INDEPENDENT_TEST28_SCHEMA_VERSION,
            "scope": CP75_INDEPENDENT_TEST28_SCOPE,
            "predecessor_custody": custody,
            "maximum_request_bytes": CP75_INDEPENDENT_TEST28_MAXIMUM_REQUEST_BYTES,
            "maximum_manifest_bytes": CP75_INDEPENDENT_TEST28_MAXIMUM_MANIFEST_BYTES,
            "maximum_response_bytes": CP75_INDEPENDENT_TEST28_MAXIMUM_RESPONSE_BYTES,
            "maximum_public_key_bytes": CP75_INDEPENDENT_TEST28_MAXIMUM_PUBLIC_KEY_BYTES,
            "maximum_total_input_bytes": CP75_INDEPENDENT_TEST28_MAXIMUM_TOTAL_INPUT_BYTES,
            "maximum_json_depth": CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH,
            "maximum_json_nodes": CP75_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES,
            "maximum_object_members": CP75_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS,
            "maximum_array_items": CP75_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS,
            "maximum_key_characters": CP75_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS,
            "maximum_text_item_characters": CP75_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS,
            "maximum_decoded_text_characters": CP75_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS,
            "maximum_integer_decimal_digits": CP75_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS,
            "error_codes": CP75_INDEPENDENT_TEST28_ERROR_CODES,
            "validation_phase_order": CP75_INDEPENDENT_TEST28_VALIDATION_PHASE_ORDER,
            "one_response_per_call": True,
            "exact_request_bytes_required": True,
            "exact_manifest_bytes_required": True,
            "response_structure_and_signature_math_validator_available": True,
            "external_attachment_validator_available": False,
            "trust_authority_time_revocation_or_aggregation_validator_available": False,
            "project_modules_imported": False,
            "path_io_performed": False,
            "key_generation_performed": False,
            "signing_performed": False,
            "response_issuance_performed": False,
            "external_review_performed": False,
            "candidate_descriptor_acceptance_effective": False,
            "schema_acceptance_effective": False,
            "subsequent_candidate_descriptor_development_qualification_construction_permitted": False,
            "production_execution_authorized": False,
            "production_gate_states": _MISSING_GATES,
            "draft_blocker_states": _MISSING_BLOCKERS,
            "formal_test_28_status": "OPEN",
            "builder_validates_internal_definition": True,
        }
        bundle = cast(
            CP75IndependentReviewResponseValidatorBundleV1,
            _record(CP75IndependentReviewResponseValidatorBundleV1, values),
        )
        _assert_issued(bundle)
        return bundle
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except MemoryError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RESOURCE_EXHAUSTED",
            "independent CP75 validator bundle construction exhausted memory",
        ) from exc
    except CP75IndependentReviewResponseValidationError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INTERNAL_INVARIANT_FAILED",
            "independent CP75 validator bundle definition failed validation",
        ) from exc
    except Exception as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INTERNAL_INVARIANT_FAILED",
            "independent CP75 validator bundle construction failed",
        ) from exc


def _validate_input_types_and_sizes(
    request_json_bytes: object,
    packet_manifest_json_bytes: object,
    response_json_bytes: object,
    reviewer_public_key_json_bytes: object,
) -> Tuple[bytes, bytes, bytes, bytes]:
    values = (
        request_json_bytes,
        packet_manifest_json_bytes,
        response_json_bytes,
        reviewer_public_key_json_bytes,
    )
    if any(type(item) is not bytes for item in values):
        _fail("CP75_INPUT_TYPE_MISMATCH", "all four inputs must be exact bytes")
    checked = cast(Tuple[bytes, bytes, bytes, bytes], values)
    limits = (
        CP75_INDEPENDENT_TEST28_MAXIMUM_REQUEST_BYTES,
        CP75_INDEPENDENT_TEST28_MAXIMUM_MANIFEST_BYTES,
        CP75_INDEPENDENT_TEST28_MAXIMUM_RESPONSE_BYTES,
        CP75_INDEPENDENT_TEST28_MAXIMUM_PUBLIC_KEY_BYTES,
    )
    if any(not item or len(item) > limit for item, limit in zip(checked, limits)):
        _fail("CP75_INPUT_BYTE_LIMIT", "an input byte length is outside its cap")
    if (
        sum(len(item) for item in checked)
        > CP75_INDEPENDENT_TEST28_MAXIMUM_TOTAL_INPUT_BYTES
    ):
        _fail("CP75_INPUT_BYTE_LIMIT", "cumulative input bytes exceed their cap")
    return checked


def cp75_validate_supplied_external_review_response(
    request_json_bytes: object,
    packet_manifest_json_bytes: object,
    response_json_bytes: object,
    reviewer_public_key_json_bytes: object,
) -> CP75IndependentSuppliedReviewResponseValidationSummaryV1:
    """Validate one response's structure and signature math, never authority."""

    try:
        (
            request_bytes,
            manifest_bytes,
            response_bytes,
            public_key_bytes,
        ) = _validate_input_types_and_sizes(
            request_json_bytes,
            packet_manifest_json_bytes,
            response_json_bytes,
            reviewer_public_key_json_bytes,
        )
        request, manifest, response, public_key = _decode_four_payloads_in_phase_order(
            (
                request_bytes,
                manifest_bytes,
                response_bytes,
                public_key_bytes,
            )
        )
        try:
            packet = _packet_oracle()
            expected_request, expected_manifest = _validate_packet_oracle(packet)
        except (KeyboardInterrupt, SystemExit, GeneratorExit, MemoryError):
            raise
        except CP75IndependentReviewResponseValidationError as exc:
            raise CP75IndependentReviewResponseValidationError(
                "CP75_INTERNAL_INVARIANT_FAILED",
                "embedded independent CP75 packet oracle failed validation",
            ) from exc
        _validate_root_field_sets_and_types(
            request,
            expected_request,
            manifest,
            expected_manifest,
            response,
            public_key,
        )
        if (
            request.get("schema_version")
            != CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION
            or manifest.get("schema_version")
            != "cp75-test28-production-schema-acceptance-review-packet-manifest-v1"
        ):
            _fail("CP75_INPUT_SCHEMA_MISMATCH", "request or manifest schema differs")
        _validate_schema_versions(response, public_key)
        if request_bytes != packet[_REQUEST_PATH]:
            _fail("CP75_INPUT_REQUEST_MISMATCH", "request differs from exact oracle")
        if manifest_bytes != packet[_MANIFEST_PATH]:
            _fail("CP75_INPUT_MANIFEST_MISMATCH", "manifest differs from exact oracle")
        role, assigned, results, withdrawal = _validate_response_inventories(
            response, public_key, request
        )
        _validate_response_and_key_digests(response, response_bytes, public_key)
        _validate_request_response_bindings(
            response,
            public_key,
            request,
            request_bytes,
            manifest,
            manifest_bytes,
            packet,
        )
        modulus = _validate_public_key_identity_and_intervals(response, public_key)
        signature = _validate_signature_digest(response)
        _validate_signature_math(response, modulus, signature)
        _validate_dispositions(response, role, assigned, results, withdrawal)
        values: Dict[str, object] = {
            "schema_version": _SUMMARY_SCHEMA,
            "source_request_schema_version": (
                CP75_INDEPENDENT_TEST28_SOURCE_REQUEST_SCHEMA_VERSION
            ),
            "source_response_schema_version": _SOURCE_RESPONSE_SCHEMA_VERSION,
            "source_public_key_schema_version": _SOURCE_PUBLIC_KEY_SCHEMA_VERSION,
            "request_input_bytes": len(request_bytes),
            "request_input_sha256": hashlib.sha256(request_bytes).hexdigest(),
            "manifest_input_bytes": len(manifest_bytes),
            "manifest_input_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "response_input_bytes": len(response_bytes),
            "response_input_sha256": hashlib.sha256(response_bytes).hexdigest(),
            "public_key_input_bytes": len(public_key_bytes),
            "public_key_input_sha256": hashlib.sha256(public_key_bytes).hexdigest(),
            "reviewer_role": role,
            "candidate_descriptor_disposition": response[
                "candidate_descriptor_disposition"
            ],
            "production_executable_schema_disposition": response[
                "production_executable_schema_disposition"
            ],
            "acknowledged_subject_open_item_ids": tuple(
                response["acknowledged_subject_open_item_ids"]
            ),
            "criterion_result_count": len(results),
            "request_exactly_reconstructed": True,
            "manifest_exactly_reconstructed": True,
            "response_canonical": True,
            "public_key_canonical": True,
            "response_field_grammar_valid": True,
            "public_key_field_grammar_valid": True,
            "criterion_coverage_complete": not withdrawal,
            "criterion_result_digests_valid": True,
            "response_record_digest_valid": True,
            "request_subject_scope_context_and_attachment_bindings_valid": True,
            "public_key_document_sha256_binding_valid": True,
            "public_key_identity_formula_valid": True,
            "reviewer_organization_binding_valid": True,
            "validity_interval_coherence_valid": True,
            "reviewer_signature_sha256_valid": True,
            "rsa_pss_signature_math_valid": True,
            "allowed_disposition_pair_valid": True,
            "current_subject_scope_rules_valid": True,
            "full_review_report_bytes_verified": False,
            "review_method_execution_verified": False,
            "supersession_relation_verified": False,
            "withdrawal_relation_verified": False,
            "conflict_status_verified": False,
            "reviewer_identity_authenticated": False,
            "external_trust_root_verified": False,
            "reviewer_authority_verified": False,
            "authority_appointment_verified": False,
            "conflict_of_interest_attestation_verified": False,
            "independence_attestation_verified": False,
            "revocation_status_verified": False,
            "validity_at_trusted_time_verified": False,
            "external_attachment_bytes_verified": False,
            "external_review_performed": False,
            "response_eligible_for_candidate_descriptor_acceptance": False,
            "response_eligible_for_production_schema_acceptance": False,
            "candidate_descriptor_acceptance_effective": False,
            "schema_acceptance_independent": False,
            "schema_acceptance_effective": False,
            "subsequent_candidate_descriptor_development_qualification_construction_permitted": False,
            "production_execution_authorized": False,
            "production_gate_states": _MISSING_GATES,
            "draft_blocker_states": _MISSING_BLOCKERS,
            "formal_test_28_status": "OPEN",
            "caller_input_bytes_retained_after_successful_return": False,
        }
        summary = cast(
            CP75IndependentSuppliedReviewResponseValidationSummaryV1,
            _record(CP75IndependentSuppliedReviewResponseValidationSummaryV1, values),
        )
        _assert_issued(summary)
        del packet, expected_request, expected_manifest
        del request, manifest, response, public_key, results
        del request_bytes, manifest_bytes, response_bytes, public_key_bytes
        return summary
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except MemoryError as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_RESOURCE_EXHAUSTED", "independent CP75 validation ran out of memory"
        ) from exc
    except CP75IndependentReviewResponseValidationError:
        raise
    except Exception as exc:
        raise CP75IndependentReviewResponseValidationError(
            "CP75_INTERNAL_INVARIANT_FAILED",
            "independent CP75 validation reached an internal failure",
        ) from exc


__all__ = (
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
