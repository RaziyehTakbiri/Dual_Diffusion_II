"""Build the CP75 external review request for the frozen CP74 descriptor.

This module materializes a development-only review packet.  It creates no
reviewer identity, key, signature, trust decision, review response, schema
acceptance, production authorization, evidence, gate transition, blocker
closure, or Formal Test 28 closure.  Its deterministic zero-argument surface
performs no path I/O and accepts no caller data.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import hmac
import json
import math
import threading
from typing import Dict, List, Mapping, Optional, Tuple, Type, cast
import weakref


CP75_TEST28_SCHEMA_VERSION = (
    "cp75-test28-production-schema-acceptance-review-request-v1"
)
CP75_TEST28_SCOPE = (
    "external-review-ready-request-for-the-exact-v25-bound-cp74-"
    "nonexecutable-candidate-descriptor;local-packet-release-only;four-"
    "external-reviewer-roles;two-axis-candidate-development-and-production-"
    "executable-schema-dispositions;no-local-review-identity-key-trust-"
    "signature-response-aggregation-acceptance-freeze-evidence-gate-blocker-"
    "execution-launch-or-test28-closure;zero-argument-stdlib-only-no-io"
)
CP75_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP75_TEST28_REVIEW_CRITERION_COUNT = 12
CP75_TEST28_REQUIRED_REVIEWER_COUNT = 4
CP75_TEST28_PRE_REQUEST_ARTIFACT_COUNT = 6
CP75_TEST28_MANIFEST_FILE_COUNT = 7
CP75_TEST28_PRODUCTION_GATE_COUNT = 17
CP75_TEST28_BLOCKER_COUNT = 4
CP75_TEST28_REVIEWER_ROLES = (
    "protocol-and-provenance-reviewer",
    "runtime-and-durability-reviewer",
    "statistical-power-and-decision-reviewer",
    "independent-recomputation-reviewer",
)
CP75_TEST28_CRITERION_IDS = (
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
CP75_TEST28_CANDIDATE_DESCRIPTOR_DISPOSITIONS = (
    "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY",
    "DEFER",
    "REJECT",
    "ABSTAIN",
    "WITHDRAW",
)
CP75_TEST28_PRODUCTION_EXECUTABLE_SCHEMA_DISPOSITIONS = (
    "ACCEPT",
    "DEFER",
    "REJECT",
    "ABSTAIN",
    "WITHDRAW",
)
CP75_TEST28_ALLOWED_DISPOSITION_PAIRS = (
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
CP75_TEST28_CANDIDATE_REVIEW_OUTCOMES = (
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
CP75_TEST28_PRODUCTION_SCHEMA_REVIEW_OUTCOMES = (
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
CP75_TEST28_SIGNATURE_SCHEME_ID = "rsa-pss-sha256-3072-e65537-salt32-v1"

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
CP75_TEST28_STATIC_ARTIFACT_PATHS = (
    (
        _CHECKLIST_PATH,
        _VECTORS_PATH,
    )
    + _TEMPLATE_PATHS
    + (_REQUEST_PATH, _MANIFEST_PATH)
)

_SUBJECT_SCHEMA = "cp75-test28-production-schema-acceptance-review-subject-v1"
_CRITERION_SCHEMA = "cp75-test28-production-schema-acceptance-review-criterion-v1"
_RESPONSE_CONTRACT_SCHEMA = (
    "cp75-test28-production-schema-acceptance-review-response-contract-v1"
)
_ARTIFACT_SCHEMA = "cp75-test28-production-schema-acceptance-review-packet-artifact-v1"
_RESPONSE_SCHEMA = "cp75-test28-production-schema-acceptance-review-response-v1"
_CRITERION_RESULT_SCHEMA = (
    "cp75-test28-production-schema-acceptance-review-criterion-result-v1"
)
_PUBLIC_KEY_DOCUMENT_SCHEMA = (
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
_ACCEPTANCE_TARGET = (
    "NONEXECUTABLE_CANDIDATE_DESCRIPTOR_FOR_CP75_DEVELOPMENT_AND_"
    "PRODUCTION_EXECUTABLE_SCHEMA_REVIEW"
)
_REQUEST_ID = "cp75-test28-production-schema-acceptance-review-round-0001"
_KNOWN_OPEN_ITEM_IDS = (
    "primary-threshold-comparison-operator",
    "primary-threshold-comparison-direction",
    "primary-threshold-value-law",
    "primary-selected-count-justification",
    "primary-32-slot-decision-function",
    "decision-timestamp-authority",
)
_ZERO_SHA256 = "0" * 64
_MISSING_GATES = ("MISSING",) * CP75_TEST28_PRODUCTION_GATE_COUNT
_MISSING_BLOCKERS = ("MISSING",) * CP75_TEST28_BLOCKER_COUNT


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del cls, args, kwargs
        raise TypeError("CP75 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP75 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP75 records are not pickle objects")


_ALLOW_RECORD_CLASS_DEFINITION = True


@dataclass(frozen=True, eq=False, init=False)
class CP75ReviewSubjectV1(_SealedRecord):
    schema_version: str
    subject_id: str
    acceptance_target: str
    v25_protocol_markdown_path: str
    v25_protocol_markdown_sha256: str
    v25_protocol_markdown_bytes: int
    v25_protocol_markdown_lf_count: int
    v25_machine_manifest_path: str
    v25_machine_manifest_sha256: str
    v25_machine_manifest_bytes: int
    v25_machine_manifest_lf_count: int
    cp74_component_ids: Tuple[str, ...]
    cp74_source_and_test_paths: Tuple[str, ...]
    cp74_source_and_test_sha256s: Tuple[str, ...]
    cp74_source_and_test_bytes: Tuple[int, ...]
    cp74_source_and_test_lf_counts: Tuple[int, ...]
    v25_embedded_record_json_pointers: Tuple[str, ...]
    authoritative_bundle_canonical_json_bytes: int
    authoritative_bundle_canonical_json_sha256: str
    authoritative_bundle_record_sha256: str
    authoritative_bundle_public_sha256: str
    authoritative_candidate_schema_semantic_sha256: str
    independent_validator_bundle_canonical_json_bytes: int
    independent_validator_bundle_canonical_json_sha256: str
    independent_validator_bundle_record_sha256: str
    independent_validator_bundle_public_sha256: str
    independent_validation_summary_canonical_json_bytes: int
    independent_validation_summary_canonical_json_sha256: str
    independent_validation_summary_record_sha256: str
    independent_validation_summary_public_sha256: str
    cp65_schema_semantic_sha256: str
    cp65_artifact_id_order_sha256: str
    cp65_artifact_schema_record_order_sha256: str
    cp65_referenced_output_id_order_sha256: str
    cp65_gate_evidence_dag_node_count: int
    cp65_gate_evidence_dag_edge_count: int
    cp65_gate_evidence_dag_semantic_sha256: str
    cp65_gate_evidence_artifact_id_aliases: Tuple[Tuple[str, str], ...]
    cp65_typed_graph_vector_lengths: Tuple[int, ...]
    cp65_typed_graph_semantic_sha256: str
    cp65_gate_evidence_dag_is_not_full_typed_graph: bool
    cp65_typed_graph_inherited_by_hash_reference_only: bool
    cp65_typed_graph_revalidated_by_cp75: bool
    artifact_count: int
    referenced_output_count: int
    lifecycle_branch_count: int
    crash_cut_count: int
    output_cross_binding_count: int
    complete_output_instance_count: int
    complete_output_unit_count: int
    focused_test_count: int
    focused_test_duration_seconds: str
    focused_test_exit_code: int
    aggregate_test_count: int
    aggregate_pytest_duration_seconds: str
    aggregate_exit_code: int
    aggregate_real_seconds: str
    aggregate_user_seconds: str
    aggregate_sys_seconds: str
    candidate_descriptor_packet_internally_consistent: bool
    candidate_descriptor_definition_complete: bool
    candidate_schema_executable: bool
    primary_decision_semantics_resolved: bool
    primary_decision_semantics_deferred_to_external_power_review: bool
    independent_structural_validation: bool
    schema_acceptance_independent: bool
    candidate_schema_accepted: bool
    authoritative_for_production: bool
    production_schema_frozen: bool
    production_execution_and_output_schema_frozen: bool
    production_receipt_schema_frozen: bool
    production_artifacts_observed: bool
    production_output_bodies_accepted: bool
    production_evidence_accepted: bool
    production_execution_authorized: bool
    formal_test_28_status: str
    production_gate_states: Tuple[str, ...]
    draft_blocker_states: Tuple[str, ...]
    known_open_item_ids: Tuple[str, ...]
    current_subject_candidate_descriptor_acceptance_eligible: bool
    current_subject_production_executable_schema_acceptance_eligible: bool
    local_candidate_descriptor_pre_review_disposition: str
    local_production_executable_schema_pre_review_disposition: str
    scope_and_nonclaims_sha256: str
    subject_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP75ReviewCriterionV1(_SealedRecord):
    schema_version: str
    criterion_ordinal: int
    criterion_id: str
    assigned_reviewer_roles: Tuple[str, ...]
    review_question: str
    review_question_sha256: str
    acceptance_rule: str
    subject_json_pointers: Tuple[str, ...]
    blocking_for_candidate_descriptor_acceptance: bool
    blocking_for_production_executable_schema_acceptance: bool
    local_pre_review_disposition: str
    local_pre_review_only: bool
    external_reviewer_disposition_present: bool
    unexpected_findings_permitted: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP75ExternalReviewResponseContractV1(_SealedRecord):
    schema_version: str
    required_reviewer_roles: Tuple[str, ...]
    required_reviewer_count: int
    role_criterion_coverage: Tuple[Tuple[str, Tuple[str, ...]], ...]
    current_subject_role_criterion_disposition_requirements: Tuple[
        Tuple[str, str, str], ...
    ]
    current_subject_role_criterion_payload_requirements: Tuple[
        Tuple[str, str, str], ...
    ]
    criterion_result_schema_version: str
    criterion_result_exact_keys: Tuple[str, ...]
    response_schema_version: str
    response_exact_keys: Tuple[str, ...]
    reviewer_public_key_schema_version: str
    reviewer_public_key_exact_keys: Tuple[str, ...]
    criterion_disposition_domain: Tuple[str, ...]
    candidate_descriptor_disposition_domain: Tuple[str, ...]
    production_executable_schema_disposition_domain: Tuple[str, ...]
    allowed_disposition_pairs: Tuple[Tuple[str, str], ...]
    current_subject_allowed_disposition_pairs: Tuple[Tuple[str, str], ...]
    axis_disposition_derivation_precedence: Tuple[str, ...]
    criterion_result_branch_rules: Tuple[str, ...]
    response_relation_and_nullability_branch_rules: Tuple[str, ...]
    finding_change_and_report_binding_rules: Tuple[str, ...]
    candidate_descriptor_review_outcome_domain: Tuple[str, ...]
    production_schema_review_outcome_domain: Tuple[str, ...]
    candidate_conditional_acceptance_maps_to: str
    production_conditional_acceptance_maps_to: str
    distinct_reviewer_identity_required: bool
    distinct_reviewer_key_identity_required: bool
    external_trust_root_preexists_candidate_required: bool
    authority_appointment_required: bool
    conflict_of_interest_attestation_required: bool
    independence_attestation_required: bool
    revocation_check_required: bool
    trusted_time_required: bool
    signature_scheme_id: str
    reviewer_public_key_identity_formula: str
    key_identity_formula_binds_organization: bool
    reviewer_public_key_document_digest_formula: str
    reviewer_public_key_plain_sha256_binding_rule: str
    reviewer_public_key_modulus_and_exponent_grammar: str
    reviewer_public_key_and_response_interval_coherence_rule: str
    criterion_result_digest_formula: str
    ordered_criterion_result_digest_formula: str
    response_signature_preimage_formula: str
    response_signature_sha256_formula: str
    response_record_digest_formula: str
    current_subject_candidate_descriptor_accept_permitted: bool
    current_subject_production_schema_accept_permitted: bool
    signature_math_implies_authority: bool
    supplied_response_validator_performs_trust_or_authority_validation: bool
    local_response_issuance_performed: bool
    local_key_generation_performed: bool
    local_signing_performed: bool
    external_review_performed: bool
    candidate_descriptor_acceptance_claimed: bool
    schema_acceptance_claimed: bool
    production_execution_authorized: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP75ReviewPacketArtifactV1(_SealedRecord):
    schema_version: str
    artifact_ordinal: int
    artifact_id: str
    path: str
    media_kind: str
    canonical_encoding: str
    terminal_newline_rule: str
    dependency_record_sha256s: Tuple[str, ...]
    dependency_artifact_sha256s: Tuple[str, ...]
    content_bytes: int
    lf_count: int
    content_sha256: str
    template_only: bool
    issued: bool
    external_identity_present: bool
    external_key_present: bool
    external_signature_present: bool
    acceptance_effect: str
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP75ProductionSchemaAcceptanceReviewRequestBundleV1(_SealedRecord):
    schema_version: str
    request_id: str
    review_round_ordinal: int
    review_context_sha256: str
    review_context_randomness_used: bool
    review_context_freshness_claimed: bool
    review_context_challenge_claimed: bool
    review_context_replay_prevention_claimed: bool
    acceptance_target: str
    review_subject: CP75ReviewSubjectV1
    ordered_review_criteria: Tuple[CP75ReviewCriterionV1, ...]
    ordered_review_criterion_record_sha256s: Tuple[str, ...]
    ordered_review_criteria_sha256: str
    response_contract: CP75ExternalReviewResponseContractV1
    ordered_packet_artifacts: Tuple[CP75ReviewPacketArtifactV1, ...]
    ordered_packet_artifact_record_sha256s: Tuple[str, ...]
    ordered_packet_artifacts_sha256: str
    review_packet_manifest_path: str
    request_state: str
    response_count: int
    current_candidate_descriptor_review_outcome: str
    current_production_executable_schema_review_outcome: str
    local_review_packet_release_qualified: bool
    current_subject_candidate_descriptor_acceptance_eligible: bool
    current_subject_production_executable_schema_acceptance_eligible: bool
    candidate_descriptor_acceptance_effective: bool
    schema_acceptance_independent: bool
    schema_acceptance_effective: bool
    external_review_performed: bool
    external_reviewer_authority_verified: bool
    subsequent_candidate_descriptor_development_qualification_construction_permitted: bool
    production_execution_authorized: bool
    production_gate_states: Tuple[str, ...]
    draft_blocker_states: Tuple[str, ...]
    formal_test_28_status: str
    all_record_digests_valid: bool
    builder_validates_internal_definition: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False


_RECORD_TYPES = (
    CP75ReviewSubjectV1,
    CP75ReviewCriterionV1,
    CP75ExternalReviewResponseContractV1,
    CP75ReviewPacketArtifactV1,
    CP75ProductionSchemaAcceptanceReviewRequestBundleV1,
)
_RECORD_DOMAINS = {
    CP75ReviewSubjectV1: _SUBJECT_SCHEMA,
    CP75ReviewCriterionV1: _CRITERION_SCHEMA,
    CP75ExternalReviewResponseContractV1: _RESPONSE_CONTRACT_SCHEMA,
    CP75ReviewPacketArtifactV1: _ARTIFACT_SCHEMA,
    CP75ProductionSchemaAcceptanceReviewRequestBundleV1: CP75_TEST28_SCHEMA_VERSION,
}
_ISSUED: "weakref.WeakKeyDictionary[_SealedRecord, Tuple[bytes, object]]" = (
    weakref.WeakKeyDictionary()
)
_ISSUED_LOCK = threading.RLock()


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _primitive(value: object, depth: int = 0) -> object:
    if depth > 32:
        raise ValueError("CP75 record nesting exceeds the sealed bound")
    if type(value) in _RECORD_DOMAINS:
        return {
            item.name: _primitive(getattr(value, item.name), depth + 1)
            for item in fields(value)
        }
    if isinstance(value, tuple):
        return [_primitive(item, depth + 1) for item in value]
    if isinstance(value, list):
        return [_primitive(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise TypeError("CP75 canonical mappings require string keys")
        return {
            key: _primitive(item, depth + 1)
            for key, item in cast(Mapping[str, object], value).items()
        }
    if value is None or type(value) in (str, int, bool):
        return value
    raise TypeError("CP75 canonical value has an unsupported type")


def _typed_snapshot(
    value: object,
    depth: int = 0,
    counter: Optional[List[int]] = None,
) -> object:
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > 100_000 or depth > 32:
        raise ValueError("CP75 sealed snapshot exceeds its resource bound")
    if type(value) in _RECORD_DOMAINS:
        return (
            "record",
            type(value).__name__,
            id(value),
            tuple(
                (
                    item.name,
                    _typed_snapshot(getattr(value, item.name), depth + 1, counter),
                )
                for item in fields(value)
            ),
        )
    if isinstance(value, tuple):
        return (
            "tuple",
            tuple(_typed_snapshot(item, depth + 1, counter) for item in value),
        )
    if isinstance(value, list):
        return (
            "list",
            tuple(_typed_snapshot(item, depth + 1, counter) for item in value),
        )
    if isinstance(value, dict):
        return (
            "dict",
            tuple(
                (key, _typed_snapshot(item, depth + 1, counter))
                for key, item in cast(Mapping[str, object], value).items()
            ),
        )
    if value is None:
        return ("none",)
    if type(value) is str:
        if len(value) > 1_000_000:
            raise ValueError("CP75 sealed text exceeds its resource bound")
        return ("str", value)
    if type(value) is int:
        return ("int", value)
    if type(value) is bool:
        return ("bool", value)
    raise TypeError("CP75 sealed value has an unsupported type")


def _record_values(record: _SealedRecord) -> Dict[str, object]:
    return {item.name: getattr(record, item.name) for item in fields(record)}


def _issue(
    cls: Type[_SealedRecord],
    values: Mapping[str, object],
    digest_field: str,
) -> _SealedRecord:
    names = tuple(item.name for item in fields(cls))
    if tuple(values) != names or digest_field not in values:
        raise RuntimeError("CP75 internal record field order differs")
    mutable = dict(values)
    mutable[digest_field] = _ZERO_SHA256
    domain = _RECORD_DOMAINS[cls].encode("ascii") + b"\0"
    mutable[digest_field] = hashlib.sha256(
        domain + _plain_json_bytes(_primitive(mutable))
    ).hexdigest()
    record = object.__new__(cls)
    for name in names:
        object.__setattr__(record, name, mutable[name])
    canonical = _plain_json_bytes(_primitive(record))
    snapshot = _typed_snapshot(record)
    with _ISSUED_LOCK:
        _ISSUED[record] = (canonical, snapshot)
    return record


def _assert_issued(record: object) -> _SealedRecord:
    if type(record) not in _RECORD_DOMAINS:
        raise TypeError("CP75_RECORD_TYPE_MISMATCH")
    sealed = cast(_SealedRecord, record)
    with _ISSUED_LOCK:
        issued = _ISSUED.get(sealed)
    if issued is None:
        raise TypeError("CP75_RECORD_NOT_ISSUED")
    expected_bytes, expected_snapshot = issued
    try:
        actual_snapshot = _typed_snapshot(sealed)
        actual_bytes = _plain_json_bytes(_primitive(sealed))
    except (MemoryError, KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as exc:
        raise TypeError("CP75_RECORD_TAMPERED") from exc
    if actual_snapshot != expected_snapshot or actual_bytes != expected_bytes:
        raise TypeError("CP75_RECORD_TAMPERED")
    for item in fields(sealed):
        child = getattr(sealed, item.name)
        if type(child) in _RECORD_DOMAINS:
            _assert_issued(child)
        elif isinstance(child, tuple):
            for nested in child:
                if type(nested) in _RECORD_DOMAINS:
                    _assert_issued(nested)
    return sealed


def cp75_canonical_json_bytes(record: object) -> bytes:
    sealed = _assert_issued(record)
    with _ISSUED_LOCK:
        return bytes(cast(Tuple[bytes, object], _ISSUED[sealed])[0])


def cp75_record_sha256(record: object) -> str:
    sealed = _assert_issued(record)
    for name in ("subject_sha256", "record_sha256"):
        if hasattr(sealed, name):
            return cast(str, getattr(sealed, name))
    raise RuntimeError("CP75 record has no digest carrier")


def cp75_public_record_sha256(record: object) -> str:
    sealed = _assert_issued(record)
    return hashlib.sha256(
        b"cp75-public-record-v1\0"
        + type(sealed).__name__.encode("ascii")
        + b"\0"
        + cp75_canonical_json_bytes(sealed)
    ).hexdigest()


_ROLE_COVERAGE = (
    (
        CP75_TEST28_REVIEWER_ROLES[0],
        tuple(
            CP75_TEST28_CRITERION_IDS[index - 1]
            for index in (1, 2, 3, 4, 5, 6, 7, 9, 12)
        ),
    ),
    (
        CP75_TEST28_REVIEWER_ROLES[1],
        tuple(
            CP75_TEST28_CRITERION_IDS[index - 1]
            for index in (1, 3, 4, 5, 6, 7, 8, 10, 11, 12)
        ),
    ),
    (
        CP75_TEST28_REVIEWER_ROLES[2],
        tuple(CP75_TEST28_CRITERION_IDS[index - 1] for index in (1, 3, 8, 9, 12)),
    ),
    (
        CP75_TEST28_REVIEWER_ROLES[3],
        tuple(
            CP75_TEST28_CRITERION_IDS[index - 1]
            for index in (1, 2, 3, 4, 8, 9, 10, 11, 12)
        ),
    ),
)
_FROZEN_CURRENT_ROLE_C12_REQUIREMENTS = (
    (CP75_TEST28_REVIEWER_ROLES[0], CP75_TEST28_CRITERION_IDS[11], "ABSTAIN"),
    (CP75_TEST28_REVIEWER_ROLES[1], CP75_TEST28_CRITERION_IDS[11], "ABSTAIN"),
    (CP75_TEST28_REVIEWER_ROLES[2], CP75_TEST28_CRITERION_IDS[11], "DEFER"),
    (CP75_TEST28_REVIEWER_ROLES[3], CP75_TEST28_CRITERION_IDS[11], "DEFER"),
)
_CURRENT_ROLE_C12_REQUIREMENTS = _FROZEN_CURRENT_ROLE_C12_REQUIREMENTS
_FROZEN_CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS = (
    (
        CP75_TEST28_REVIEWER_ROLES[0],
        "ABSTAIN",
        "finding_ids=empty;required_change_ids-contribution=empty;comment_sha256="
        "nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six",
    ),
    (
        CP75_TEST28_REVIEWER_ROLES[1],
        "ABSTAIN",
        "finding_ids=empty;required_change_ids-contribution=empty;comment_sha256="
        "nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six",
    ),
    (
        CP75_TEST28_REVIEWER_ROLES[2],
        "DEFER",
        "finding_ids=exact-six-known-open-item-ids;required_change_ids="
        "exact-six-known-open-item-ids;comment_sha256=nonzero-reason-digest;"
        "acknowledged_subject_open_item_ids=exact-six",
    ),
    (
        CP75_TEST28_REVIEWER_ROLES[3],
        "DEFER",
        "finding_ids=exact-six-known-open-item-ids;required_change_ids="
        "exact-six-known-open-item-ids;comment_sha256=nonzero-reason-digest;"
        "acknowledged_subject_open_item_ids=exact-six",
    ),
)
_CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS = _FROZEN_CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS
_AXIS_DERIVATION_PRECEDENCE = (
    "if-any-applicable-blocking-result-FAIL-then-axis-disposition-REJECT",
    "else-if-any-applicable-blocking-result-DEFER-then-axis-disposition-DEFER",
    "else-if-any-applicable-blocking-result-ABSTAIN-then-axis-disposition-ABSTAIN",
    "else-all-applicable-blocking-results-PASS-then-candidate-axis-"
    "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY-or-production-axis-ACCEPT",
    "WITHDRAW-is-a-separate-empty-result-response-branch-and-both-axes-WITHDRAW",
)
_CRITERION_RESULT_BRANCH_RULES = (
    "PASS=>finding_ids-exact-empty;comment_sha256-exact-nonzero-lowercase-64hex",
    "DEFER=>finding_ids-nonempty-bounded-unique-identifiers;comment_sha256-"
    "exact-nonzero-lowercase-64hex",
    "FAIL=>finding_ids-nonempty-bounded-unique-identifiers;comment_sha256-"
    "exact-nonzero-lowercase-64hex",
    "ABSTAIN=>finding_ids-exact-empty;required-change-contribution-exact-empty;"
    "comment_sha256-exact-nonzero-reason-lowercase-64hex",
    "every-row-has-exact-five-keys-and-row_sha256-is-zero-carrier-domain-digest",
)
_RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES = (
    "substantive-ordinary=>all-exact-response-fields-nonnull-except-"
    "supersedes_response_sha256-and-withdraws_response_sha256-both-null",
    "substantive-replacement=>all-exact-response-fields-nonnull-except-"
    "withdraws_response_sha256-null;supersedes_response_sha256-lowercase-64hex",
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
    "open_finding_ids=stable-ordered-unique-union-of-row-finding_ids-in-"
    "criterion-order-and-row-order",
    "required_change_ids=bounded-unique-subset-of-open_finding_ids-and-thus-"
    "resolved-by-full-review-report-pointer",
    "substantive-response-full_review_report_sha256=nonzero-lowercase-64hex-"
    "pointer-only;packet-and-one-response-validator-do-not-verify-report-bytes",
    "unexpected-finding-identifiers-are-nonempty-lowercase-ascii-"
    "[a-z0-9][a-z0-9._:-]{0,127}-unique-and-not-closed-to-an-allowlist",
    "every-nonwithdrawal-response-acknowledges-exact-six-subject-open-item-ids-"
    "in-subject-order",
)

_CRITERION_QUESTIONS = (
    "Do the supplied final v25 and CP74 source, test, embedded record, byte-count, line-count, receipt, and SHA-256 pins match the frozen review subject exactly?",
    "Does the subject preserve the CP65 artifact-order, schema-record-order, referenced-output-order, gate-evidence DAG alias, and typed-graph hash-reference lineage without claiming CP75 revalidation of the full typed graph?",
    "Are the candidate-only, nonexecutable, unresolved-decision, unaccepted, unauthoritative, nonevidentiary, nongate, nonblocker, nonexecution, and OPEN scope boundaries complete and immutable under subject change?",
    "Are all 64 CP65 artifact descriptors preserved and are their eleven branch occurrence expressions and conditional occurrence rules closed without optional or open-ended production claims?",
    "Are the eleven lifecycle branches mutually exclusive, collectively exhaustive, and consistent with their required, forbidden, durable-prefix, terminal, and recovery artifacts?",
    "Are all six named crash cuts complete at-cut durable closures with exact forbidden and recovery semantics, including the preallocated empty acquisition journal and post-STARTED recovery boundary?",
    "Are SHA-manifest and COMMITTED exceptions, the exact gate-evidence direct DAG, conditional predecessors, downward closure, and acyclic publication order preserved?",
    "Are all fifteen output envelopes, complete-instance cardinalities, heterogeneous unit counts, final-file framing rules, and abnormal whole-final-shard prefix rules exact?",
    "Are every record, ordered, body, plain-file digest preimage and all twenty-four crossbindings closed, acyclic, and bound to exact carriers and predecessor pointers?",
    "Are the raw-to-stable, stderr, Philox state, CP69 interchange, CP71 recomputation, diagnostic, primary, decision, and ledger candidate semantics exact while production bodies remain unobserved?",
    "Are parser and issued-record resource bounds, stable error precedence, atomic failure, sealing, concurrency, successful-return nonretention, and source-independent reconstruction adequate and nonauthoritative?",
    "Are threshold operator, direction, value law, selected-count justification, the thirty-two-slot decision function, and timestamp authority externally resolved sufficiently for production executability?",
)

_CRITERION_RULES = (
    "exact byte and digest equality for every named subject component and embedded record pointer",
    "all three CP65 order hashes, the 20/44 gate view, two aliases, and hash-only 456/708 typed-graph boundary must match",
    "all fixed nonclaims and six open items must be acknowledged; any subject mutation supersedes this request",
    "all 64 descriptors and every 64-by-11 occurrence cell must match the candidate definition",
    "all eleven branch rows must be disjoint, exhaustive, and dependency-compatible",
    "all six at-cut vectors and recovery-only effects must match the frozen truth table",
    "manifest and COMMITTED exception vectors plus the direct DAG must match exactly",
    "all fifteen envelopes and the 201 final instances and 196617 units must match exactly",
    "all executable digest formulas and twenty-four crossbindings must match exactly",
    "all candidate nested schemas and exact projections must match without a production observation claim",
    "all bounded-parser, sealing, error, concurrency, and nonretention claims must survive hostile reconstruction",
    "current CP74 must not receive production ACCEPT; external power and decision semantics remain unresolved",
)

_CRITERION_POINTERS = (
    ("/v25_protocol_markdown_sha256", "/v25_machine_manifest_sha256"),
    ("/cp65_artifact_id_order_sha256", "/cp65_gate_evidence_dag_semantic_sha256"),
    ("/scope_and_nonclaims_sha256", "/known_open_item_ids"),
    ("/artifact_count", "/authoritative_candidate_schema_semantic_sha256"),
    ("/lifecycle_branch_count",),
    ("/crash_cut_count",),
    ("/cp65_gate_evidence_dag_node_count", "/cp65_gate_evidence_dag_edge_count"),
    (
        "/referenced_output_count",
        "/complete_output_instance_count",
        "/complete_output_unit_count",
    ),
    ("/output_cross_binding_count",),
    ("/authoritative_bundle_record_sha256",),
    ("/independent_validation_summary_record_sha256",),
    (
        "/known_open_item_ids",
        "/candidate_schema_executable",
        "/primary_decision_semantics_resolved",
    ),
)


def _roles_for_criterion(criterion_id: str) -> Tuple[str, ...]:
    return tuple(role for role, ids in _ROLE_COVERAGE if criterion_id in ids)


def _ordered_digest(domain: bytes, digests: Tuple[str, ...]) -> str:
    return hashlib.sha256(
        domain + b"".join(bytes.fromhex(item) for item in digests)
    ).hexdigest()


def _zero_digest_object(
    domain: bytes, body: Dict[str, object], carrier: str
) -> Dict[str, object]:
    result = dict(body)
    result[carrier] = _ZERO_SHA256
    result[carrier] = hashlib.sha256(
        domain + _plain_json_bytes(_primitive(result))
    ).hexdigest()
    return result


def _build_subject() -> CP75ReviewSubjectV1:
    scope_projection = {
        "acceptance_target": _ACCEPTANCE_TARGET,
        "known_open_item_ids": _KNOWN_OPEN_ITEM_IDS,
        "current_subject_candidate_descriptor_acceptance_eligible": True,
        "current_subject_production_executable_schema_acceptance_eligible": False,
        "local_candidate_descriptor_pre_review_disposition": "UNREVIEWED",
        "local_production_executable_schema_pre_review_disposition": (
            "DEFER_REQUIRED_NONEXECUTABLE_SUBJECT"
        ),
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
        "production_gate_states": _MISSING_GATES,
        "draft_blocker_states": _MISSING_BLOCKERS,
        "formal_test_28_status": CP75_TEST28_FORMAL_TEST_28_STATUS,
    }
    scope_digest = hashlib.sha256(
        b"cp75-test28-production-schema-acceptance-review-scope-and-nonclaims-v1\0"
        + _plain_json_bytes(_primitive(scope_projection))
    ).hexdigest()
    values: Dict[str, object] = {
        "schema_version": _SUBJECT_SCHEMA,
        "subject_id": "cp74-exact-v25-bound-production-occurrence-output-schema-candidate",
        "acceptance_target": _ACCEPTANCE_TARGET,
        "v25_protocol_markdown_path": "research/preregistrations/cp50_test28_mixed_initializer_v25.md",
        "v25_protocol_markdown_sha256": "4f939cca60fe6de9f87422f9cd4060e429f9ce34b43a40607d0946a6b928858f",
        "v25_protocol_markdown_bytes": 276_704,
        "v25_protocol_markdown_lf_count": 4_463,
        "v25_machine_manifest_path": "research/fixtures/cp50_test28_mixed_initializer_v25.json",
        "v25_machine_manifest_sha256": "5153dbad02fbb20a36a5873e1a14dc93ac9f1560d9f71745fcfc63d22778df76",
        "v25_machine_manifest_bytes": 6_971_770,
        "v25_machine_manifest_lf_count": 133_870,
        "cp74_component_ids": (
            "authoritative-candidate-builder",
            "authoritative-candidate-hostile-tests",
            "independent-supplied-byte-validator",
            "independent-validator-hostile-tests",
        ),
        "cp74_source_and_test_paths": (
            "src/heterodiff/evaluation/mixed_initializer_test28_production_occurrence_output_schema_candidate.py",
            "tests/unit/test_mixed_initializer_test28_production_occurrence_output_schema_candidate.py",
            "src/heterodiff/evaluation/mixed_initializer_test28_independent_production_occurrence_output_schema_candidate_validator.py",
            "tests/unit/test_mixed_initializer_test28_independent_production_occurrence_output_schema_candidate_validator.py",
        ),
        "cp74_source_and_test_sha256s": (
            "785f9738ebf168dfdf26c24751066b00a8c90a11b20bf60db8b02d8c9dbab347",
            "7a64ddc59c122ae354ec6442ae6f12f1c3559601ea39136a4279027971fb726d",
            "ccbd88521fc92c373d5795205dc5980d2a1f217c990c1a92fc5e4579647e6b6b",
            "598c3f82c1e65fbc3192e877519d1d09608ead191fd66eb8b152478ce5dc6aa5",
        ),
        "cp74_source_and_test_bytes": (251_995, 129_967, 158_494, 65_171),
        "cp74_source_and_test_lf_counts": (5_130, 3_213, 2_591, 1_798),
        "v25_embedded_record_json_pointers": (
            "/draft_blockers/whole_seed_candidate_production_artifact_occurrence_branch_and_execution_output_schema_definition/authoritative_bundle",
            "/draft_blockers/whole_seed_candidate_production_artifact_occurrence_branch_and_execution_output_schema_definition/independent_validator_bundle",
            "/draft_blockers/whole_seed_candidate_production_artifact_occurrence_branch_and_execution_output_schema_definition/independent_validation_summary",
        ),
        "authoritative_bundle_canonical_json_bytes": 512_612,
        "authoritative_bundle_canonical_json_sha256": "a4185be6dcee4b8068445a1d0b158171d03e64a9ba8633d6fdb14ee92ac03366",
        "authoritative_bundle_record_sha256": "1d01714f666bf229a0d7f0c3e0092064a96b71dd11bf4c5268ecbfe611a6904b",
        "authoritative_bundle_public_sha256": "9832a9a98f8c0545c2d42b71061f87b3a6aa959ab64fda74855949b1c5f6300d",
        "authoritative_candidate_schema_semantic_sha256": "111ae93616ff0f5ba825d0d77d2b6790816ffe2974e8a45e1f58917b360a729a",
        "independent_validator_bundle_canonical_json_bytes": 8_430,
        "independent_validator_bundle_canonical_json_sha256": "30325915e79c934962e9e2a7897fa82c99a1793e6564119e169fa288296b948c",
        "independent_validator_bundle_record_sha256": "c56116aacb41d425c2ec0991b7e2298eb31c54a5088e687e0d12fcb1f48913ca",
        "independent_validator_bundle_public_sha256": "d360e9c79d46d09c880d2bfa69bab62668bd38f1538f5e39bce3c195c55e51e1",
        "independent_validation_summary_canonical_json_bytes": 2_612,
        "independent_validation_summary_canonical_json_sha256": "4006cad676d3ee2a70714e0ed4a0124309e6707b1a02e753ad375b219248042f",
        "independent_validation_summary_record_sha256": "bb2b206eae22a49498aed1887d8c916a864e03bea0c4b4f10c14b3ef2e6ec4f0",
        "independent_validation_summary_public_sha256": "f8704b1a4653d4ef72f8a92b17f50b31055b43cb67d30a8733c4e2fe50f3c8d0",
        "cp65_schema_semantic_sha256": "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0",
        "cp65_artifact_id_order_sha256": "cc7cd223d18f59933b0888b1663e3f7de157c010d189c2d46b085fd42d0da808",
        "cp65_artifact_schema_record_order_sha256": "088b09ee42fbd527940032a4dc26b30eee902d6a8cc1334e44c7bbe1698bf2ff",
        "cp65_referenced_output_id_order_sha256": "3d73d68568b7dc14eef9d55571593ef7436b8ccfc362e81138cf3ae907830f1e",
        "cp65_gate_evidence_dag_node_count": 20,
        "cp65_gate_evidence_dag_edge_count": 44,
        "cp65_gate_evidence_dag_semantic_sha256": "eb9a83e70b243882e3579c7361bc3b0dbfed31be90344c5b1f536ac5ef4b9bc2",
        "cp65_gate_evidence_artifact_id_aliases": (
            (
                "independent-full-32768-recomputation-receipt",
                "independent-full-32768-recomputation-qualification-receipt",
            ),
            (
                "independent-554-estimate-interval-decision-path-receipt",
                "independent-554-estimate-interval-decision-path-qualification-receipt",
            ),
        ),
        "cp65_typed_graph_vector_lengths": (456, 708, 708, 708, 708, 456),
        "cp65_typed_graph_semantic_sha256": "a3b5b1511a7fd5abfb99f9c3ce0a413540541ef6899cfc534e8ab93bed8ef185",
        "cp65_gate_evidence_dag_is_not_full_typed_graph": True,
        "cp65_typed_graph_inherited_by_hash_reference_only": True,
        "cp65_typed_graph_revalidated_by_cp75": False,
        "artifact_count": 64,
        "referenced_output_count": 15,
        "lifecycle_branch_count": 11,
        "crash_cut_count": 6,
        "output_cross_binding_count": 24,
        "complete_output_instance_count": 201,
        "complete_output_unit_count": 196_617,
        "focused_test_count": 194,
        "focused_test_duration_seconds": "36.72",
        "focused_test_exit_code": 0,
        "aggregate_test_count": 2_463,
        "aggregate_pytest_duration_seconds": "3331.73",
        "aggregate_exit_code": 0,
        "aggregate_real_seconds": "3332.41",
        "aggregate_user_seconds": "3282.92",
        "aggregate_sys_seconds": "24.84",
        "candidate_descriptor_packet_internally_consistent": True,
        "candidate_descriptor_definition_complete": True,
        "candidate_schema_executable": False,
        "primary_decision_semantics_resolved": False,
        "primary_decision_semantics_deferred_to_external_power_review": True,
        "independent_structural_validation": True,
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
        "formal_test_28_status": CP75_TEST28_FORMAL_TEST_28_STATUS,
        "production_gate_states": _MISSING_GATES,
        "draft_blocker_states": _MISSING_BLOCKERS,
        "known_open_item_ids": _KNOWN_OPEN_ITEM_IDS,
        "current_subject_candidate_descriptor_acceptance_eligible": True,
        "current_subject_production_executable_schema_acceptance_eligible": False,
        "local_candidate_descriptor_pre_review_disposition": "UNREVIEWED",
        "local_production_executable_schema_pre_review_disposition": (
            "DEFER_REQUIRED_NONEXECUTABLE_SUBJECT"
        ),
        "scope_and_nonclaims_sha256": scope_digest,
        "subject_sha256": _ZERO_SHA256,
    }
    return cast(
        CP75ReviewSubjectV1, _issue(CP75ReviewSubjectV1, values, "subject_sha256")
    )


def _build_criteria() -> Tuple[CP75ReviewCriterionV1, ...]:
    result: List[CP75ReviewCriterionV1] = []
    for ordinal, criterion_id in enumerate(CP75_TEST28_CRITERION_IDS, 1):
        question = _CRITERION_QUESTIONS[ordinal - 1]
        values: Dict[str, object] = {
            "schema_version": _CRITERION_SCHEMA,
            "criterion_ordinal": ordinal,
            "criterion_id": criterion_id,
            "assigned_reviewer_roles": _roles_for_criterion(criterion_id),
            "review_question": question,
            "review_question_sha256": hashlib.sha256(
                (question + "\n").encode("utf-8")
            ).hexdigest(),
            "acceptance_rule": _CRITERION_RULES[ordinal - 1],
            "subject_json_pointers": _CRITERION_POINTERS[ordinal - 1],
            "blocking_for_candidate_descriptor_acceptance": ordinal != 12,
            "blocking_for_production_executable_schema_acceptance": True,
            "local_pre_review_disposition": (
                "PRODUCTION_NONPASS_REQUIRED" if ordinal == 12 else "UNREVIEWED"
            ),
            "local_pre_review_only": True,
            "external_reviewer_disposition_present": False,
            "unexpected_findings_permitted": True,
            "record_sha256": _ZERO_SHA256,
        }
        result.append(
            cast(
                CP75ReviewCriterionV1,
                _issue(CP75ReviewCriterionV1, values, "record_sha256"),
            )
        )
    return tuple(result)


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


def _build_response_contract() -> CP75ExternalReviewResponseContractV1:
    values: Dict[str, object] = {
        "schema_version": _RESPONSE_CONTRACT_SCHEMA,
        "required_reviewer_roles": CP75_TEST28_REVIEWER_ROLES,
        "required_reviewer_count": CP75_TEST28_REQUIRED_REVIEWER_COUNT,
        "role_criterion_coverage": _ROLE_COVERAGE,
        "current_subject_role_criterion_disposition_requirements": _CURRENT_ROLE_C12_REQUIREMENTS,
        "current_subject_role_criterion_payload_requirements": (
            _CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS
        ),
        "criterion_result_schema_version": _CRITERION_RESULT_SCHEMA,
        "criterion_result_exact_keys": _CRITERION_RESULT_KEYS,
        "response_schema_version": _RESPONSE_SCHEMA,
        "response_exact_keys": _RESPONSE_KEYS,
        "reviewer_public_key_schema_version": _PUBLIC_KEY_DOCUMENT_SCHEMA,
        "reviewer_public_key_exact_keys": _PUBLIC_KEY_KEYS,
        "criterion_disposition_domain": ("PASS", "DEFER", "FAIL", "ABSTAIN"),
        "candidate_descriptor_disposition_domain": CP75_TEST28_CANDIDATE_DESCRIPTOR_DISPOSITIONS,
        "production_executable_schema_disposition_domain": CP75_TEST28_PRODUCTION_EXECUTABLE_SCHEMA_DISPOSITIONS,
        "allowed_disposition_pairs": CP75_TEST28_ALLOWED_DISPOSITION_PAIRS,
        "current_subject_allowed_disposition_pairs": tuple(
            pair
            for pair in CP75_TEST28_ALLOWED_DISPOSITION_PAIRS
            if pair != ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY", "ACCEPT")
        ),
        "axis_disposition_derivation_precedence": _AXIS_DERIVATION_PRECEDENCE,
        "criterion_result_branch_rules": _CRITERION_RESULT_BRANCH_RULES,
        "response_relation_and_nullability_branch_rules": (
            _RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES
        ),
        "finding_change_and_report_binding_rules": _FINDING_CHANGE_AND_REPORT_RULES,
        "candidate_descriptor_review_outcome_domain": CP75_TEST28_CANDIDATE_REVIEW_OUTCOMES,
        "production_schema_review_outcome_domain": CP75_TEST28_PRODUCTION_SCHEMA_REVIEW_OUTCOMES,
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
        "signature_scheme_id": CP75_TEST28_SIGNATURE_SCHEME_ID,
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
            "SHA256(cp75-test28-production-schema-acceptance-review-criterion-result-record-"
            "digests-v1\\0+concatenated-raw32-row-digests-in-role-coverage-order)"
        ),
        "response_signature_preimage_formula": (
            "cp75-test28-production-schema-acceptance-review-response-signature-preimage-v1\\0"
            "+canonical(response-with-reviewer_signature_hex-empty-and-signature_sha256-and-"
            "response_sha256-set-to-64-zero-hex)"
        ),
        "response_signature_sha256_formula": "plain-SHA256-of-exact-384-raw-signature-bytes",
        "response_record_digest_formula": (
            "SHA256(cp75-test28-production-schema-acceptance-review-response-v1\\0+canonical("
            "response-with-response_sha256-set-to-64-zero-hex-and-actual-signature-retained))"
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
    return cast(
        CP75ExternalReviewResponseContractV1,
        _issue(CP75ExternalReviewResponseContractV1, values, "record_sha256"),
    )


def _review_context_sha256(subject: CP75ReviewSubjectV1) -> str:
    return hashlib.sha256(
        b"cp75-test28-production-schema-acceptance-review-context-v1\0"
        + _plain_json_bytes(
            {
                "acceptance_target": _ACCEPTANCE_TARGET,
                "review_round_ordinal": 1,
                "subject_record_sha256": subject.subject_sha256,
            }
        )
    ).hexdigest()


def _build_checklist_bytes(
    subject: CP75ReviewSubjectV1,
    criteria: Tuple[CP75ReviewCriterionV1, ...],
    contract: CP75ExternalReviewResponseContractV1,
) -> bytes:
    lines = [
        "# CP75 external production-schema review checklist and claim matrix",
        "",
        "Status: READY_FOR_EXTERNAL_REVIEW. No external review, authority, acceptance, production execution, gate, blocker, evidence, or closure is claimed.",
        "",
        "## Frozen subject",
        "",
        "- Subject record SHA-256: " + subject.subject_sha256,
        "- Scope/nonclaim SHA-256: " + subject.scope_and_nonclaims_sha256,
        "- Acceptance target: " + subject.acceptance_target,
        "- Candidate descriptor acceptance is reviewable only for CP75 development.",
        "- Production executable-schema acceptance is ineligible for this exact subject.",
        "- The exact six production open items remain: "
        + ", ".join(_KNOWN_OPEN_ITEM_IDS)
        + ".",
        "",
        "## Reviewer roles and exact criterion coverage",
        "",
    ]
    for role, criterion_ids in _ROLE_COVERAGE:
        lines.append("- " + role + ": " + ", ".join(criterion_ids))
    lines.extend(
        [
            "",
            "Every role must bind a distinct externally governed identity and key. Signature mathematics alone is never identity or authority.",
            "",
            "## Claim matrix",
            "",
            "| # | Criterion | Candidate blocking | Production blocking | Local pre-review state |",
            "|---:|---|:---:|:---:|---|",
        ]
    )
    for criterion in criteria:
        lines.append(
            "| {0} | {1} | {2} | {3} | {4} |".format(
                criterion.criterion_ordinal,
                criterion.criterion_id,
                "yes"
                if criterion.blocking_for_candidate_descriptor_acceptance
                else "no",
                "yes"
                if criterion.blocking_for_production_executable_schema_acceptance
                else "no",
                criterion.local_pre_review_disposition,
            )
        )
    lines.extend(["", "## Criterion questions", ""])
    for criterion in criteria:
        marker = criterion.criterion_id
        lines.extend(
            [
                "### {0}. {1}".format(criterion.criterion_ordinal, marker),
                "",
                "<!-- CP75-CRITERION:{0}:QUESTION-BEGIN -->".format(marker),
                criterion.review_question,
                "<!-- CP75-CRITERION:{0}:QUESTION-END -->".format(marker),
                "",
                "Acceptance rule: " + criterion.acceptance_rule,
                "",
            ]
        )
    lines.extend(
        [
            "## Two-axis response rules",
            "",
            "Criterion dispositions are PASS, DEFER, FAIL, or ABSTAIN. Per axis, FAIL derives REJECT; otherwise DEFER derives DEFER; otherwise ABSTAIN derives ABSTAIN; otherwise all applicable blocking criteria PASS derive scoped ACCEPT.",
            "",
            "For the current subject, protocol/provenance and runtime/durability reviewers record criterion 12 as ABSTAIN; statistical/power and independent/recomputation reviewers record it as DEFER. Candidate acceptance still requires criteria 1 through 11 PASS. Production ACCEPT is forbidden.",
            "",
            "Unexpected findings are permitted and must use bounded unique identifiers. Conditions are DEFER, never acceptance.",
            "",
            "### Exact axis derivation precedence",
            "",
        ]
    )
    lines.extend(
        "- " + rule for rule in contract.axis_disposition_derivation_precedence
    )
    lines.extend(
        [
            "",
            "### Exact current-subject criterion 12 role branches",
            "",
        ]
    )
    for (
        role,
        disposition,
        payload_rule,
    ) in contract.current_subject_role_criterion_payload_requirements:
        lines.append("- " + role + ": " + disposition + "; " + payload_rule)
    lines.extend(["", "### Exact criterion-result branches", ""])
    lines.extend("- " + rule for rule in contract.criterion_result_branch_rules)
    lines.extend(["", "### Exact response and relation branches", ""])
    lines.extend(
        "- " + rule for rule in contract.response_relation_and_nullability_branch_rules
    )
    lines.extend(["", "### Exact finding, change, and report bindings", ""])
    lines.extend(
        "- " + rule for rule in contract.finding_change_and_report_binding_rules
    )
    lines.extend(
        [
            "",
            "### Exact public-key and interval grammar",
            "",
            "- " + contract.reviewer_public_key_identity_formula,
            "- " + contract.reviewer_public_key_document_digest_formula,
            "- " + contract.reviewer_public_key_plain_sha256_binding_rule,
            "- " + contract.reviewer_public_key_modulus_and_exponent_grammar,
            "- " + contract.reviewer_public_key_and_response_interval_coherence_rule,
            "- Mathematical validity never implies identity, trust, appointment, authority, current-time validity, or acceptance.",
            "",
            "## External return requirements",
            "",
            "A substantive response must bind the exact request, manifest, subject, checklist, contract vectors, review context, reviewer identity and organization, public-key document, authority appointment, conflict-of-interest and independence attestations, revocation status, method/toolchain, full report, criterion rows, both dispositions, validity interval, and signature.",
            "",
            "The supplied-response validator checks exact bytes and RSA-PSS mathematics for one response only. It does not check external attachment bytes, trust, authority, current time, revocation, supersession, withdrawal targets, conflicts, aggregation, or acceptance.",
            "",
            "## Non-effect",
            "",
            "Even a future externally accepted nonexecutable candidate descriptor authorizes only construction of a separate development qualification. It does not freeze a production schema, satisfy CP65 gates 15 through 17, close a blocker, authorize execution, accept evidence, or close Formal Test 28.",
        ]
    )
    checklist = ("\n".join(lines) + "\n").encode("utf-8")
    for criterion in criteria:
        begin = (
            "<!-- CP75-CRITERION:{0}:QUESTION-BEGIN -->\n".format(
                criterion.criterion_id
            )
        ).encode("utf-8")
        end = (
            "<!-- CP75-CRITERION:{0}:QUESTION-END -->".format(criterion.criterion_id)
        ).encode("utf-8")
        left = checklist.index(begin) + len(begin)
        right = checklist.index(end, left)
        if (
            hashlib.sha256(checklist[left:right]).hexdigest()
            != criterion.review_question_sha256
        ):
            raise RuntimeError("CP75 checklist question extraction differs")
    if not checklist.endswith(b"\n") or b"\r" in checklist:
        raise RuntimeError("CP75 checklist framing differs")
    if contract.current_subject_production_schema_accept_permitted:
        raise RuntimeError("CP75 checklist contract permits production ACCEPT")
    return checklist


_SYNTHETIC_RSA_MODULUS_HEX = (
    "cba160c5c103454b66116b83d6bcaacdab2b17dec803d79b636a961da35c9d2d"
    "1cde43811a7a5546483683145e9b753e206afdf8ca1d59a5046640ae72741b46e"
    "f6db6602dbad2c1b1d73789ad54ff0d9fff6e9867b318dcb9b31dcad4832de4d"
    "2822d48245a65a241731375c2113a1a36a581272b35508511f7a23cf71ea832b"
    "820a7e53a8c85cb119c86b1cf1b6586ecc84560e9c08dc69f97c051af2ac810b"
    "1bd71b3c22ebb0055e5468ddb0e8577c892f0ece74cd8a80d2bfe6fd64bb6fdd"
    "05ba639b8c20118ae6933fb9357a5fbdbc806e414899a4e90f49dec1ed7c98600"
    "ff4830762e3a79546bca7b7e98978a840d3a07d65a83d7f6cd4493e0e1bcf75e"
    "e23ea277ec4cebb1a86decf7bbd874b5b57251e265d13ac3ed7e5c415a2b1a7c"
    "13bf53531c786afbf4aff71ac232e1f11d4f3f84476aeb855f3cfe5585ccf69b8"
    "5fd540b861b5410bb844ab786363df2ddab47fa078f1cfe426e90b989aa9fd817"
    "bcd5450d5d1a686abeed39e33fc1fb9d567b4f169d92e7b5916368ba0eeb"
)
_SYNTHETIC_RSA_SIGNATURE_HEX = (
    "3da1a7c291c9c8fbd4a56f9c263d19c729ab459376c427e431ff0e7ffde57e0e"
    "60d766222c7cf7459b0df4926bf4b0f37b27110d55e4fd9438d966f033e681aa"
    "c28b6fa0f61d9ab5ddfded79901a1e947352114f754544c068dae5c2f1d7c64d"
    "b86a9de8863fae89a7a060a5449858d2c038ce03a4060749ead30002fc6b29e9"
    "2c15321a44d5d7452f68eff480d6212f828f1d9a1e375be90ccb2da3000c1cbcb"
    "10ead62a2f5d436f327d12b68506c26beb2a9ec91c6455f4ea8e4db0561c774f"
    "2687424c86349c08604bb9c4facf96927db65022eaafd8646a3a62deae3466e28"
    "4810620347d533c0c29625e582b890678d0384bfefd44d5e8589a7d2334756b88"
    "60065d8f5808ea4e64cf22393268e07160033f58546fe2c5fe5190fa537726030"
    "8f697aab62d8c9a1307bccd72224b72c48a7f7c41f71087377e03c7fed9d8ed6"
    "6f45608c03ee68d1994bc548d7d94fe999393512375a956910cdc82d192cadc25"
    "26d364b32b6562b85aa11bfc758e43b22e65ea728f40d2401ed7e5373b1"
)


def _synthetic_unsigned_response_for_rsa_vector() -> Dict[str, object]:
    comment_sha256 = hashlib.sha256(
        b"cp75-synthetic-untrusted-positive-vector-comment"
    ).hexdigest()
    row: Dict[str, object] = {
        "criterion_id": CP75_TEST28_CRITERION_IDS[0],
        "disposition": "PASS",
        "finding_ids": (),
        "comment_sha256": comment_sha256,
        "row_sha256": _ZERO_SHA256,
    }
    row = _zero_digest_object(
        b"cp75-test28-production-schema-acceptance-review-criterion-result-v1\0",
        row,
        "row_sha256",
    )
    row_sha256 = cast(str, row["row_sha256"])
    values: Dict[str, object] = {key: "synthetic" for key in _RESPONSE_KEYS}
    values.update(
        {
            "schema_version": _RESPONSE_SCHEMA,
            "request_schema_version": CP75_TEST28_SCHEMA_VERSION,
            "request_canonical_json_sha256": hashlib.sha256(
                b"synthetic-request"
            ).hexdigest(),
            "request_record_sha256": hashlib.sha256(
                b"synthetic-request-record"
            ).hexdigest(),
            "subject_record_sha256": hashlib.sha256(b"synthetic-subject").hexdigest(),
            "review_packet_manifest_canonical_json_sha256": hashlib.sha256(
                b"synthetic-manifest"
            ).hexdigest(),
            "review_packet_manifest_record_sha256": hashlib.sha256(
                b"synthetic-manifest-record"
            ).hexdigest(),
            "checklist_sha256": hashlib.sha256(b"synthetic-checklist").hexdigest(),
            "response_contract_test_vectors_sha256": hashlib.sha256(
                b"synthetic-vectors"
            ).hexdigest(),
            "review_round_ordinal": 1,
            "review_context_sha256": hashlib.sha256(b"synthetic-context").hexdigest(),
            "acceptance_target": _ACCEPTANCE_TARGET,
            "scope_and_nonclaims_sha256": hashlib.sha256(
                b"synthetic-scope"
            ).hexdigest(),
            "reviewer_role": CP75_TEST28_REVIEWER_ROLES[0],
            "reviewer_identity_sha256": hashlib.sha256(
                b"synthetic-reviewer"
            ).hexdigest(),
            "reviewer_organization_sha256": hashlib.sha256(
                b"synthetic-organization"
            ).hexdigest(),
            "reviewer_public_key_identity_sha256": _ZERO_SHA256,
            "reviewer_public_key_document_sha256": _ZERO_SHA256,
            "signature_scheme_id": CP75_TEST28_SIGNATURE_SCHEME_ID,
            "trust_policy_id": "synthetic-untrusted-policy",
            "authority_id": "synthetic-untrusted-authority",
            "reviewer_authority_attestation_sha256": hashlib.sha256(
                b"synthetic-authority"
            ).hexdigest(),
            "appointment_evidence_sha256": hashlib.sha256(
                b"synthetic-appointment"
            ).hexdigest(),
            "conflict_of_interest_attestation_sha256": hashlib.sha256(
                b"synthetic-coi"
            ).hexdigest(),
            "independence_attestation_sha256": hashlib.sha256(
                b"synthetic-independence"
            ).hexdigest(),
            "revocation_status_receipt_sha256": hashlib.sha256(
                b"synthetic-revocation"
            ).hexdigest(),
            "review_method_ids": ("synthetic-method",),
            "review_toolchain_sha256": hashlib.sha256(
                b"synthetic-toolchain"
            ).hexdigest(),
            "full_review_report_sha256": hashlib.sha256(
                b"synthetic-report"
            ).hexdigest(),
            "ordered_criterion_results": (row,),
            "ordered_criterion_result_sha256s": (row_sha256,),
            "ordered_criterion_results_sha256": _ordered_digest(
                b"cp75-test28-production-schema-acceptance-review-criterion-result-record-digests-v1\0",
                (row_sha256,),
            ),
            "open_finding_ids": (),
            "required_change_ids": (),
            "acknowledged_subject_open_item_ids": _KNOWN_OPEN_ITEM_IDS,
            "review_notes_sha256": hashlib.sha256(b"synthetic-notes").hexdigest(),
            "candidate_descriptor_disposition": ("ACCEPT_FOR_CP75_DEVELOPMENT_ONLY"),
            "production_executable_schema_disposition": "DEFER",
            "signed_at_utc": "2026-01-01T00:00:01Z",
            "valid_from_utc": "2026-01-01T00:00:00Z",
            "valid_until_utc": "2027-01-01T00:00:00Z",
            "supersedes_response_sha256": None,
            "withdraws_response_sha256": None,
            "reviewer_signature_sha256": _ZERO_SHA256,
            "reviewer_signature_hex": "",
            "response_sha256": _ZERO_SHA256,
        }
    )
    if tuple(values) != _RESPONSE_KEYS:
        raise RuntimeError("CP75 synthetic response key order differs")
    return values


def _build_rsa_pss_math_vectors() -> Tuple[Mapping[str, object], ...]:
    unsigned = _synthetic_unsigned_response_for_rsa_vector()
    canonical = _plain_json_bytes(_primitive(unsigned))
    production_domain = (
        b"cp75-test28-production-schema-acceptance-review-response-signature-"
        b"preimage-v1\0"
    )
    message = production_domain + canonical
    if hashlib.sha256(message).hexdigest() != (
        "944ce9cb2101ecc8b51db9c4af156d5612c1bac5463cee75d790e6092f858767"
    ):
        raise RuntimeError("CP75 synthetic RSA vector preimage differs")
    bad_signature = (int(_SYNTHETIC_RSA_SIGNATURE_HEX[:2], 16) ^ 1).to_bytes(
        1, "big"
    ).hex() + _SYNTHETIC_RSA_SIGNATURE_HEX[2:]
    common: Dict[str, object] = {
        "uses_exact_production_response_signature_domain": True,
        "synthetic_untrusted_subject_identity_and_key": True,
        "signature_scheme_id": CP75_TEST28_SIGNATURE_SCHEME_ID,
        "unsigned_response_signature_preimage_object": unsigned,
        "production_signature_message_sha256": hashlib.sha256(message).hexdigest(),
        "modulus_hex": _SYNTHETIC_RSA_MODULUS_HEX,
        "public_exponent": 65_537,
        "authority_effect": "NONE",
        "trust_or_authority_asserted": False,
    }
    return (
        dict(
            common,
            vector_id="exact-production-domain-positive-untrusted-math-only",
            message_domain_id=(
                "cp75-test28-production-schema-acceptance-review-response-"
                "signature-preimage-v1"
            ),
            signature_hex=_SYNTHETIC_RSA_SIGNATURE_HEX,
            expected_signature_math_valid=True,
        ),
        dict(
            common,
            vector_id="bit-flipped-signature-negative",
            message_domain_id=(
                "cp75-test28-production-schema-acceptance-review-response-"
                "signature-preimage-v1"
            ),
            signature_hex=bad_signature,
            expected_signature_math_valid=False,
        ),
        dict(
            common,
            vector_id="different-domain-negative",
            uses_exact_production_response_signature_domain=False,
            message_domain_id=(
                "cp75-test28-production-schema-acceptance-review-response-"
                "signature-preimage-test-only-wrong-domain-v1"
            ),
            signature_hex=_SYNTHETIC_RSA_SIGNATURE_HEX,
            expected_signature_math_valid=False,
        ),
    )


def _mgf1_sha256(seed: bytes, output_length: int) -> bytes:
    if type(seed) is not bytes or type(output_length) is not int:
        raise TypeError("CP75 MGF1 inputs have wrong exact types")
    if not 0 <= output_length <= 351:
        raise ValueError("CP75 MGF1 output length is outside the fixed profile")
    result = bytearray()
    counter = 0
    while len(result) < output_length:
        result.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(result[:output_length])


def _verify_rsa_pss_sha256_3072(
    message: bytes, modulus: bytes, signature: bytes
) -> bool:
    """Verify the fixed math-only profile; never sign or generate a key."""

    if (
        type(message) is not bytes
        or type(modulus) is not bytes
        or type(signature) is not bytes
    ):
        raise TypeError("CP75 RSA-PSS inputs must be exact bytes")
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
    expected_hash = hashlib.sha256(
        b"\0" * 8 + hashlib.sha256(message).digest() + salt
    ).digest()
    return hmac.compare_digest(encoded_hash, expected_hash)


def _validate_rsa_math_vectors_internal() -> None:
    vectors = _build_rsa_pss_math_vectors()
    expected_ids = (
        "exact-production-domain-positive-untrusted-math-only",
        "bit-flipped-signature-negative",
        "different-domain-negative",
    )
    if len(vectors) != 3 or tuple(row["vector_id"] for row in vectors) != expected_ids:
        raise RuntimeError("CP75 RSA-PSS vector inventory differs")
    for row in vectors:
        domain = cast(str, row["message_domain_id"]).encode("ascii") + b"\0"
        message = domain + _plain_json_bytes(
            row["unsigned_response_signature_preimage_object"]
        )
        actual = _verify_rsa_pss_sha256_3072(
            message,
            bytes.fromhex(cast(str, row["modulus_hex"])),
            bytes.fromhex(cast(str, row["signature_hex"])),
        )
        if actual is not row["expected_signature_math_valid"]:
            raise RuntimeError("CP75 RSA-PSS math vector result differs")
        if row["authority_effect"] != "NONE" or row["trust_or_authority_asserted"]:
            raise RuntimeError("CP75 RSA-PSS math vector claims authority")
    if not vectors[0]["uses_exact_production_response_signature_domain"]:
        raise RuntimeError("CP75 positive RSA vector uses the wrong domain")
    if vectors[2]["uses_exact_production_response_signature_domain"]:
        raise RuntimeError("CP75 wrong-domain RSA vector is mislabeled")


def _build_vectors_bytes(
    subject: CP75ReviewSubjectV1,
    contract: CP75ExternalReviewResponseContractV1,
) -> bytes:
    sample_row = {
        "criterion_id": CP75_TEST28_CRITERION_IDS[0],
        "disposition": "PASS",
        "finding_ids": [],
        "comment_sha256": hashlib.sha256(b"cp75-test-vector-pass-comment").hexdigest(),
        "row_sha256": _ZERO_SHA256,
    }
    sample_row = _zero_digest_object(
        b"cp75-test28-production-schema-acceptance-review-criterion-result-v1\0",
        sample_row,
        "row_sha256",
    )
    body: Dict[str, object] = {
        "schema_version": _VECTORS_SCHEMA,
        "test_vector_only": True,
        "authority_effect": "NONE",
        "subject_record_sha256": subject.subject_sha256,
        "response_contract_record_sha256": contract.record_sha256,
        "response_contract": _primitive(contract),
        "criterion_result_exact_keys": _CRITERION_RESULT_KEYS,
        "response_exact_keys": _RESPONSE_KEYS,
        "reviewer_public_key_exact_keys": _PUBLIC_KEY_KEYS,
        "allowed_disposition_pairs": CP75_TEST28_ALLOWED_DISPOSITION_PAIRS,
        "current_subject_role_criterion_payload_requirements": (
            _CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS
        ),
        "axis_disposition_derivation_precedence": _AXIS_DERIVATION_PRECEDENCE,
        "criterion_result_branch_rules": _CRITERION_RESULT_BRANCH_RULES,
        "response_relation_and_nullability_branch_rules": (
            _RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES
        ),
        "finding_change_and_report_binding_rules": _FINDING_CHANGE_AND_REPORT_RULES,
        "digest_preimage_vectors": (
            {
                "vector_id": "criterion-result-zero-carrier",
                "canonical_record": sample_row,
                "expected_record_sha256": sample_row["row_sha256"],
                "authority_effect": "NONE",
            },
        ),
        "rsa_pss_math_vectors": _build_rsa_pss_math_vectors(),
        "all_vectors_nonreviewer_test_only": True,
        "body_sha256": _ZERO_SHA256,
    }
    body = _zero_digest_object(
        b"cp75-test28-production-schema-acceptance-review-response-contract-and-test-vectors-v1\0",
        body,
        "body_sha256",
    )
    return _plain_json_bytes(_primitive(body))


def _assigned_criterion_ids(role: str) -> Tuple[str, ...]:
    return dict(_ROLE_COVERAGE)[role]


def _template_digest(body: Dict[str, object]) -> Dict[str, object]:
    return _zero_digest_object(
        b"cp75-test28-production-schema-acceptance-reviewer-unissued-template-v1\0",
        body,
        "template_sha256",
    )


def _build_template_bytes(
    role: str,
    subject: CP75ReviewSubjectV1,
    criteria: Tuple[CP75ReviewCriterionV1, ...],
    context_sha256: str,
    checklist_sha256: str,
    vectors_sha256: str,
) -> bytes:
    assigned = _assigned_criterion_ids(role)
    result_templates = tuple(
        {
            "criterion_id": criterion_id,
            "disposition": None,
            "finding_ids": None,
            "comment_sha256": None,
            "row_sha256": None,
        }
        for criterion_id in assigned
    )
    response: Dict[str, object] = {key: None for key in _RESPONSE_KEYS}
    response.update(
        {
            "schema_version": _RESPONSE_SCHEMA,
            "request_schema_version": CP75_TEST28_SCHEMA_VERSION,
            "subject_record_sha256": subject.subject_sha256,
            "checklist_sha256": checklist_sha256,
            "response_contract_test_vectors_sha256": vectors_sha256,
            "review_round_ordinal": 1,
            "review_context_sha256": context_sha256,
            "acceptance_target": _ACCEPTANCE_TARGET,
            "scope_and_nonclaims_sha256": subject.scope_and_nonclaims_sha256,
            "reviewer_role": role,
            "signature_scheme_id": CP75_TEST28_SIGNATURE_SCHEME_ID,
            "ordered_criterion_results": result_templates,
        }
    )
    public_key: Dict[str, object] = {key: None for key in _PUBLIC_KEY_KEYS}
    public_key.update(
        {
            "schema_version": _PUBLIC_KEY_DOCUMENT_SCHEMA,
            "reviewer_role": role,
            "signature_scheme_id": CP75_TEST28_SIGNATURE_SCHEME_ID,
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
        "subject_record_sha256": subject.subject_sha256,
        "review_context_sha256": context_sha256,
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
    body: Dict[str, object] = {
        "schema_version": _TEMPLATE_SCHEMA,
        "template_only": True,
        "issued": False,
        "reviewer_role": role,
        "assigned_criterion_ids": assigned,
        "subject_record_sha256": subject.subject_sha256,
        "review_context_sha256": context_sha256,
        "checklist_sha256": checklist_sha256,
        "response_contract_test_vectors_sha256": vectors_sha256,
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
    return _plain_json_bytes(_primitive(_template_digest(body)))


def _issue_artifact(
    ordinal: int,
    artifact_id: str,
    path: str,
    media_kind: str,
    content: bytes,
    dependency_record_sha256s: Tuple[str, ...],
    dependency_artifact_sha256s: Tuple[str, ...],
    template_only: bool,
) -> CP75ReviewPacketArtifactV1:
    values: Dict[str, object] = {
        "schema_version": _ARTIFACT_SCHEMA,
        "artifact_ordinal": ordinal,
        "artifact_id": artifact_id,
        "path": path,
        "media_kind": media_kind,
        "canonical_encoding": "utf-8"
        if media_kind == "text/markdown"
        else "ascii-canonical-json",
        "terminal_newline_rule": "exact-one-lf"
        if media_kind == "text/markdown"
        else "none",
        "dependency_record_sha256s": dependency_record_sha256s,
        "dependency_artifact_sha256s": dependency_artifact_sha256s,
        "content_bytes": len(content),
        "lf_count": content.count(b"\n"),
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "template_only": template_only,
        "issued": False,
        "external_identity_present": False,
        "external_key_present": False,
        "external_signature_present": False,
        "acceptance_effect": "NONE",
        "record_sha256": _ZERO_SHA256,
    }
    return cast(
        CP75ReviewPacketArtifactV1,
        _issue(CP75ReviewPacketArtifactV1, values, "record_sha256"),
    )


def _build_components() -> Tuple[
    CP75ReviewSubjectV1,
    Tuple[CP75ReviewCriterionV1, ...],
    CP75ExternalReviewResponseContractV1,
    Tuple[CP75ReviewPacketArtifactV1, ...],
    str,
]:
    subject = _build_subject()
    criteria = _build_criteria()
    contract = _build_response_contract()
    context = _review_context_sha256(subject)
    checklist = _build_checklist_bytes(subject, criteria, contract)
    vectors = _build_vectors_bytes(subject, contract)
    checklist_sha = hashlib.sha256(checklist).hexdigest()
    vectors_sha = hashlib.sha256(vectors).hexdigest()
    templates = tuple(
        _build_template_bytes(
            role,
            subject,
            criteria,
            context,
            checklist_sha,
            vectors_sha,
        )
        for role in CP75_TEST28_REVIEWER_ROLES
    )
    artifacts: List[CP75ReviewPacketArtifactV1] = []
    artifacts.append(
        _issue_artifact(
            1,
            "human-review-checklist-and-claim-matrix",
            _CHECKLIST_PATH,
            "text/markdown",
            checklist,
            (subject.subject_sha256,)
            + tuple(criterion.record_sha256 for criterion in criteria)
            + (contract.record_sha256,),
            (),
            False,
        )
    )
    artifacts.append(
        _issue_artifact(
            2,
            "response-contract-and-test-vectors",
            _VECTORS_PATH,
            "application/json",
            vectors,
            (subject.subject_sha256, contract.record_sha256),
            (),
            False,
        )
    )
    for offset, (role, path, content) in enumerate(
        zip(CP75_TEST28_REVIEWER_ROLES, _TEMPLATE_PATHS, templates),
        3,
    ):
        assigned_digests = tuple(
            criterion.record_sha256
            for criterion in criteria
            if criterion.criterion_id in _assigned_criterion_ids(role)
        )
        artifacts.append(
            _issue_artifact(
                offset,
                role + "-unissued-template",
                path,
                "application/json",
                content,
                (subject.subject_sha256,) + assigned_digests,
                (checklist_sha, vectors_sha),
                True,
            )
        )
    return subject, criteria, contract, tuple(artifacts), context


def _validate_internal_definition(
    subject: CP75ReviewSubjectV1,
    criteria: Tuple[CP75ReviewCriterionV1, ...],
    contract: CP75ExternalReviewResponseContractV1,
    artifacts: Tuple[CP75ReviewPacketArtifactV1, ...],
    context: str,
) -> None:
    if (
        len(criteria) != 12
        or tuple(item.criterion_id for item in criteria) != CP75_TEST28_CRITERION_IDS
    ):
        raise RuntimeError("CP75 criterion inventory differs")
    if len(artifacts) != 6 or tuple(
        item.artifact_ordinal for item in artifacts
    ) != tuple(range(1, 7)):
        raise RuntimeError("CP75 packet artifact inventory differs")
    if tuple(item.path for item in artifacts) != CP75_TEST28_STATIC_ARTIFACT_PATHS[:6]:
        raise RuntimeError("CP75 packet artifact path order differs")
    if contract.role_criterion_coverage != _ROLE_COVERAGE:
        raise RuntimeError("CP75 role coverage differs")
    if (
        contract.current_subject_role_criterion_disposition_requirements
        != _FROZEN_CURRENT_ROLE_C12_REQUIREMENTS
        or contract.current_subject_role_criterion_payload_requirements
        != _FROZEN_CURRENT_ROLE_C12_PAYLOAD_REQUIREMENTS
    ):
        raise RuntimeError("CP75 current-subject criterion 12 rules differ")
    if (
        contract.axis_disposition_derivation_precedence != _AXIS_DERIVATION_PRECEDENCE
        or contract.criterion_result_branch_rules != _CRITERION_RESULT_BRANCH_RULES
        or contract.response_relation_and_nullability_branch_rules
        != _RESPONSE_RELATION_AND_NULLABILITY_BRANCH_RULES
        or contract.finding_change_and_report_binding_rules
        != _FINDING_CHANGE_AND_REPORT_RULES
    ):
        raise RuntimeError("CP75 response branch rules differ")
    if any(
        item.local_pre_review_disposition
        != (
            "PRODUCTION_NONPASS_REQUIRED"
            if item.criterion_ordinal == 12
            else "UNREVIEWED"
        )
        for item in criteria
    ):
        raise RuntimeError("CP75 local pre-review criterion marker differs")
    if contract.allowed_disposition_pairs != CP75_TEST28_ALLOWED_DISPOSITION_PAIRS:
        raise RuntimeError("CP75 disposition matrix differs")
    if len(contract.allowed_disposition_pairs) != 11:
        raise RuntimeError("CP75 disposition matrix cardinality differs")
    if (
        "ACCEPT_FOR_CP75_DEVELOPMENT_ONLY",
        "ACCEPT",
    ) in contract.current_subject_allowed_disposition_pairs:
        raise RuntimeError("CP75 current subject permits production ACCEPT")
    if context != _review_context_sha256(subject):
        raise RuntimeError("CP75 review context differs")
    if subject.candidate_schema_executable or subject.schema_acceptance_independent:
        raise RuntimeError("CP75 subject overclaims acceptance")
    if any(
        value != "MISSING"
        for value in subject.production_gate_states + subject.draft_blocker_states
    ):
        raise RuntimeError("CP75 subject closes a gate or blocker")
    if subject.formal_test_28_status != "OPEN":
        raise RuntimeError("CP75 subject closes Formal Test 28")
    _validate_rsa_math_vectors_internal()
    for record in (subject,) + criteria + (contract,) + artifacts:
        _assert_issued(record)
    if any(
        artifact.issued
        or artifact.external_identity_present
        or artifact.external_key_present
        or artifact.external_signature_present
        or artifact.acceptance_effect != "NONE"
        for artifact in artifacts
    ):
        raise RuntimeError("CP75 static artifact claims external issuance")


def cp75_build_production_schema_acceptance_review_request_bundle() -> CP75ProductionSchemaAcceptanceReviewRequestBundleV1:
    subject, criteria, contract, artifacts, context = _build_components()
    _validate_internal_definition(subject, criteria, contract, artifacts, context)
    criterion_digests = tuple(item.record_sha256 for item in criteria)
    artifact_digests = tuple(item.record_sha256 for item in artifacts)
    values: Dict[str, object] = {
        "schema_version": CP75_TEST28_SCHEMA_VERSION,
        "request_id": _REQUEST_ID,
        "review_round_ordinal": 1,
        "review_context_sha256": context,
        "review_context_randomness_used": False,
        "review_context_freshness_claimed": False,
        "review_context_challenge_claimed": False,
        "review_context_replay_prevention_claimed": False,
        "acceptance_target": _ACCEPTANCE_TARGET,
        "review_subject": subject,
        "ordered_review_criteria": criteria,
        "ordered_review_criterion_record_sha256s": criterion_digests,
        "ordered_review_criteria_sha256": _ordered_digest(
            b"cp75-test28-production-schema-acceptance-review-criterion-record-digests-v1\0",
            criterion_digests,
        ),
        "response_contract": contract,
        "ordered_packet_artifacts": artifacts,
        "ordered_packet_artifact_record_sha256s": artifact_digests,
        "ordered_packet_artifacts_sha256": _ordered_digest(
            b"cp75-test28-production-schema-acceptance-review-packet-artifact-record-digests-v1\0",
            artifact_digests,
        ),
        "review_packet_manifest_path": _MANIFEST_PATH,
        "request_state": "READY_FOR_EXTERNAL_REVIEW",
        "response_count": 0,
        "current_candidate_descriptor_review_outcome": "UNREVIEWED",
        "current_production_executable_schema_review_outcome": "UNREVIEWED",
        "local_review_packet_release_qualified": True,
        "current_subject_candidate_descriptor_acceptance_eligible": True,
        "current_subject_production_executable_schema_acceptance_eligible": False,
        "candidate_descriptor_acceptance_effective": False,
        "schema_acceptance_independent": False,
        "schema_acceptance_effective": False,
        "external_review_performed": False,
        "external_reviewer_authority_verified": False,
        "subsequent_candidate_descriptor_development_qualification_construction_permitted": False,
        "production_execution_authorized": False,
        "production_gate_states": _MISSING_GATES,
        "draft_blocker_states": _MISSING_BLOCKERS,
        "formal_test_28_status": CP75_TEST28_FORMAL_TEST_28_STATUS,
        "all_record_digests_valid": True,
        "builder_validates_internal_definition": True,
        "record_sha256": _ZERO_SHA256,
    }
    bundle = cast(
        CP75ProductionSchemaAcceptanceReviewRequestBundleV1,
        _issue(
            CP75ProductionSchemaAcceptanceReviewRequestBundleV1,
            values,
            "record_sha256",
        ),
    )
    _assert_issued(bundle)
    if any(
        (
            bundle.candidate_descriptor_acceptance_effective,
            bundle.schema_acceptance_independent,
            bundle.schema_acceptance_effective,
            bundle.external_review_performed,
            bundle.external_reviewer_authority_verified,
            bundle.subsequent_candidate_descriptor_development_qualification_construction_permitted,
            bundle.production_execution_authorized,
        )
    ):
        raise RuntimeError("CP75 request bundle claims an external effect")
    return bundle


def cp75_production_schema_acceptance_review_checklist_bytes() -> bytes:
    subject, criteria, contract, _, _ = _build_components()
    return _build_checklist_bytes(subject, criteria, contract)


def cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes() -> bytes:
    subject, _, contract, _, _ = _build_components()
    return _build_vectors_bytes(subject, contract)


def cp75_production_schema_acceptance_reviewer_unissued_template_bytes() -> Tuple[
    bytes, ...
]:
    subject, criteria, contract, _, context = _build_components()
    checklist = _build_checklist_bytes(subject, criteria, contract)
    vectors = _build_vectors_bytes(subject, contract)
    return tuple(
        _build_template_bytes(
            role,
            subject,
            criteria,
            context,
            hashlib.sha256(checklist).hexdigest(),
            hashlib.sha256(vectors).hexdigest(),
        )
        for role in CP75_TEST28_REVIEWER_ROLES
    )


def cp75_production_schema_acceptance_review_request_json_bytes() -> bytes:
    return cp75_canonical_json_bytes(
        cp75_build_production_schema_acceptance_review_request_bundle()
    )


def _manifest_entry(
    ordinal: int,
    artifact_id: str,
    path: str,
    media_kind: str,
    content: bytes,
) -> Dict[str, object]:
    body: Dict[str, object] = {
        "ordinal": ordinal,
        "artifact_id": artifact_id,
        "path": path,
        "media_kind": media_kind,
        "content_bytes": len(content),
        "lf_count": content.count(b"\n"),
        "terminal_newline_rule": "exact-one-lf"
        if media_kind == "text/markdown"
        else "none",
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "entry_sha256": _ZERO_SHA256,
    }
    return _zero_digest_object(
        b"cp75-test28-production-schema-acceptance-review-packet-file-v1\0",
        body,
        "entry_sha256",
    )


def cp75_production_schema_acceptance_review_packet_manifest_json_bytes() -> bytes:
    bundle = cp75_build_production_schema_acceptance_review_request_bundle()
    request = cp75_canonical_json_bytes(bundle)
    checklist = cp75_production_schema_acceptance_review_checklist_bytes()
    vectors = (
        cp75_production_schema_acceptance_review_response_contract_and_test_vectors_bytes()
    )
    templates = cp75_production_schema_acceptance_reviewer_unissued_template_bytes()
    contents = (checklist, vectors) + templates + (request,)
    ids = tuple(item.artifact_id for item in bundle.ordered_packet_artifacts) + (
        "canonical-review-request",
    )
    paths = CP75_TEST28_STATIC_ARTIFACT_PATHS[:7]
    media = ("text/markdown",) + ("application/json",) * 6
    entries = tuple(
        _manifest_entry(index, artifact_id, path, kind, content)
        for index, (artifact_id, path, kind, content) in enumerate(
            zip(ids, paths, media, contents), 1
        )
    )
    digests = tuple(cast(str, entry["entry_sha256"]) for entry in entries)
    manifest: Dict[str, object] = {
        "schema_version": _MANIFEST_SCHEMA,
        "request_path": _REQUEST_PATH,
        "request_canonical_json_bytes": len(request),
        "request_canonical_json_sha256": hashlib.sha256(request).hexdigest(),
        "request_record_sha256": bundle.record_sha256,
        "packet_file_count": 7,
        "ordered_packet_files": entries,
        "ordered_packet_file_record_sha256s": digests,
        "ordered_packet_files_sha256": _ordered_digest(
            b"cp75-test28-production-schema-acceptance-review-packet-file-record-digests-v1\0",
            digests,
        ),
        "manifest_sha256": _ZERO_SHA256,
    }
    manifest = _zero_digest_object(
        b"cp75-test28-production-schema-acceptance-review-packet-manifest-v1\0",
        manifest,
        "manifest_sha256",
    )
    encoded = _plain_json_bytes(_primitive(manifest))
    decoded = cast(Dict[str, object], json.loads(encoded.decode("ascii")))
    if (
        decoded["packet_file_count"] != 7
        or len(cast(List[object], decoded["ordered_packet_files"])) != 7
    ):
        raise RuntimeError("CP75 manifest cardinality differs")
    if any(
        item["path"] == _MANIFEST_PATH
        for item in cast(List[Dict[str, object]], decoded["ordered_packet_files"])
    ):
        raise RuntimeError("CP75 manifest contains itself")
    return encoded


__all__ = (
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
