"""Exact types for an approved expected-leaf authority extension.

This module is deliberately types-only.  It defines the closed values that a
later byte validator may authenticate, but it performs no JSON parsing,
hashing, archive access, source inspection, verifier execution, or decision.
In particular, constructing these frozen objects does not establish custody
or authority.

Only the Python standard library is imported.  The module is intentionally not
re-exported from :mod:`heterodiff.data`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Tuple


EXPECTED_LEAF_REASON_REGISTRY_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-leaf-reason-registry.v1"
)
EXPECTED_LEAF_SEMANTIC_PROFILE_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-leaf-semantic-profile.v1"
)
EXPECTED_LEAF_VERIFIER_CLOSURE_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-leaf-verifier-closure.v1"
)
INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_ARTIFACT_TYPE = (
    "heterodiff.adapter.independent-golden-expected-leaf-extension.v1"
)
APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ARTIFACT_TYPE = (
    "heterodiff.adapter.approved-expected-leaf-authority-profile.v1"
)

EXPECTED_LEAF_REASON_REGISTRY_DIGEST_DOMAIN = (
    EXPECTED_LEAF_REASON_REGISTRY_ARTIFACT_TYPE
)
EXPECTED_LEAF_CENSOR_REASON_REGISTRY_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-leaf-censor-reason-registry.v1"
)
EXPECTED_LEAF_EXCLUSION_REASON_REGISTRY_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-leaf-exclusion-reason-registry.v1"
)
EXPECTED_LEAF_CASE_AUTHORITY_ID_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-leaf-case-authority-id.v1"
)
EXPECTED_LEAF_SEMANTIC_PROFILE_DIGEST_DOMAIN = (
    EXPECTED_LEAF_SEMANTIC_PROFILE_ARTIFACT_TYPE
)
EXPECTED_LEAF_VERIFIER_CLOSURE_DIGEST_DOMAIN = (
    EXPECTED_LEAF_VERIFIER_CLOSURE_ARTIFACT_TYPE
)
INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_DIGEST_DOMAIN = (
    INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_ARTIFACT_TYPE
)
APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_DIGEST_DOMAIN = (
    APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ARTIFACT_TYPE
)

APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ID = (
    "heterodiff-expected-leaf-authority-v1"
)
APPROVED_EXPECTED_LEAF_AUTHORITY_STATUS = (
    "A9_1_EXPECTED_LEAF_INPUTS_APPROVED_FOR_EXECUTION"
)
EXPECTED_LEAF_REASON_REGISTRY_BINDING_MODE_ID = (
    "exact-category-equality-to-approved-public-id-registry-v1"
)

EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-evidence-leaf-bundle.v1"
)
EXPECTED_LEAF_BUNDLE_FORMAT_VERSION = "1"
EXPECTED_LEAF_CANONICAL_JSON_PROFILE_ID = (
    "rfc8259-ascii-sorted-keys-compact-no-nan-v1"
)
EXPECTED_LEAF_BASE64_PROFILE_ID = (
    "rfc4648-standard-padded-canonical-v1"
)
EXPECTED_LEAF_UNICODE_PROFILE_ID = "ucd-3.2.0"
EXPECTED_LEAF_SEMANTIC_SCOPE_ID = (
    "oracle-worker-abi-v1-supplemental-expected-leaf-preimages-only"
)
EXPECTED_LEAF_FORMAT_PAYLOAD_SCOPE_ID = (
    "opaque-format-payload-bytes-structural-only"
)
EXPECTED_LEAF_TRUTH_SCOPE_ID = (
    "structural-consistency-only-semantic-truth-unattested"
)

EXPECTED_LEAF_ORACLE_VERIFIER_MODULE_ID = (
    "heterodiff-adapter-oracle-independent-verifier-v1"
)
EXPECTED_LEAF_BUNDLE_VERIFIER_MODULE_ID = (
    "heterodiff-adapter-expected-leaf-bundle-verifier-v1"
)
EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS = tuple(
    sorted(
        (
            EXPECTED_LEAF_ORACLE_VERIFIER_MODULE_ID,
            EXPECTED_LEAF_BUNDLE_VERIFIER_MODULE_ID,
        )
    )
)

MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES = 4 * 1024 * 1024
MAXIMUM_INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_BYTES = 256 * 1024
MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES = 128 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES = 4 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_VERIFIER_SOURCE_BYTES = 1024 * 1024
MAXIMUM_EXPECTED_LEAF_CASES = 4096
MAXIMUM_EXPECTED_LEAF_REASON_CODES = 1024
MAXIMUM_SAFE_INTEGER = (1 << 53) - 1

# Every ceiling below is copied into ExpectedLeafSemanticProfileV1.  The names
# and values are the complete resource surface of the checkpoint-44
# supplemental verifier, rather than a looser authority-side approximation.
MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES = 32 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_VERIFICATION_INPUT_BYTES = 160 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_VERIFICATION_RECEIPT_BYTES = 64 * 1024
MAXIMUM_CANONICAL_DEPTH = 32
MAXIMUM_CANONICAL_NODES = 200_000
MAXIMUM_CANONICAL_STRING_BYTES = 512 * 1024
MAXIMUM_PRIVATE_PAYLOAD_BYTES = 16 * 1024 * 1024
MAXIMUM_SINGLE_PAYLOAD_BYTES = 256 * 1024
MAXIMUM_SOURCE_BYTES = 64 * 1024
MAXIMUM_INVENTORY_ITEMS = 4096
MAXIMUM_SEMANTIC_OCCURRENCES = 2048
MAXIMUM_SPLIT_ENTRIES = 4096
MAXIMUM_SPLIT_GROUPS = 128
MAXIMUM_DECLARED_EVENT_TYPES = 1024
MAXIMUM_FIELDS_PER_EVENT_TYPE = 16
MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE = 16
MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE = 16
MAXIMUM_TIME_ATOMS = 4096
MAXIMUM_EVENT_ID_TUPLE_ARITY = 8
MAXIMUM_EVENT_ID_COMPONENT_BYTES = 256
MAXIMUM_EVENT_ID_METADATA_BYTES = 2 * 1024 * 1024
MAXIMUM_KEYED_LEAF_ENTRIES = 4096
MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE = 16
MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE = 4096
MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS = MAXIMUM_INVENTORY_ITEMS
MAXIMUM_SECONDARY_TAGS_PER_ITEM = 64
MAXIMUM_TOTAL_SECONDARY_TAGS = MAXIMUM_INVENTORY_ITEMS
MAXIMUM_REASON_CODES = 1024
MAXIMUM_REPRESENTATION_IDS = 64
MAXIMUM_PUBLIC_TOKEN_BYTES = 128
MAXIMUM_PRIVATE_TEXT_CODEPOINTS = 256

EXPECTED_LEAF_STRUCTURAL_TRUE_CLAIM_IDS = (
    "v1_raw_byte_bindings_validated",
    "response_payload_schema_independently_validated",
    "expected_leaf_cross_relations_independently_validated",
    "expected_leaf_commitments_independently_recomputed",
    "expected_evidence_leaf_complete",
    "expected_private_payload_set_rebuilt",
)
EXPECTED_LEAF_FALSE_CLAIM_IDS = (
    "decision_eligible",
    "execution_attested",
    "containment_attested",
    "custody_authenticated",
    "approved_profile_authenticated",
    "execution_input_set_membership_authenticated",
    "case_authority_authenticated",
    "response_payload_schema_authenticated",
    "semantic_truth_attested",
    "format_specific_payload_semantics_attested",
    "source_policy_semantics_independently_evaluated",
    "interpreter_execution_identity_attested",
    "elapsed_time_authenticated",
    "platform_observations_authenticated",
    "process_observations_authenticated",
    "adapted_evidence_leaf_complete",
    "publication_artifacts_rebuilt",
)

EXPECTED_LEAF_MEMBER_DIGEST_DOMAIN_PAIRS = (
    (
        "coverage_ledger",
        "heterodiff.adapter.private-coverage-ledger.v1",
    ),
    (
        "detached_native_observation",
        "heterodiff.adapter.native-observation.v1",
    ),
    (
        "evaluation_labels",
        "heterodiff.adapter.private-evaluation-labels.v1",
    ),
    (
        "expected_evidence_commitment",
        "heterodiff.adapter.expected-evidence.v1",
    ),
    (
        "fitted_state",
        "heterodiff.adapter.private-fitted-state.v1",
    ),
    (
        "identity_bearing_native_configuration",
        "heterodiff.adapter.private-native-configuration.v1",
    ),
    (
        "private_provenance",
        "heterodiff.adapter.private-provenance-payload.v1",
    ),
    (
        "semantic_reconstruction",
        "heterodiff.adapter.private-semantic-reconstruction.v1",
    ),
    (
        "source_inventory",
        "heterodiff.adapter.private-source-inventory.v1",
    ),
    (
        "static_context",
        "heterodiff.adapter.private-static-context.v1",
    ),
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_ID_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
)
_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")


class ExpectedLeafAuthorityTypeError(ValueError):
    """A value is outside the exact checkpoint-45 type contract."""


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ExpectedLeafAuthorityTypeError(
            name + " must be a lowercase 64-character SHA-256 digest"
        )
    return value


def _public_id(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be an exact string")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        raise ExpectedLeafAuthorityTypeError(
            name + " must contain only ASCII"
        ) from None
    if (
        not encoded
        or len(encoded) > MAXIMUM_PUBLIC_TOKEN_BYTES
        or _PUBLIC_ID_RE.fullmatch(value) is None
    ):
        raise ExpectedLeafAuthorityTypeError(
            name + " is not a canonical public identifier"
        )
    return value


def _adapter_identity(adapter_id: object, adapter_version: object) -> None:
    _public_id(adapter_id, name="adapter_id")
    if (
        type(adapter_version) is not str
        or _VERSION_RE.fullmatch(adapter_version) is None
    ):
        raise ExpectedLeafAuthorityTypeError(
            "adapter_version is not canonical"
        )


def _bounded_integer(
    value: object,
    *,
    name: str,
    maximum: int,
    allow_zero: bool = False,
) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if (
        value < 0
        or value > maximum
        or value > MAXIMUM_SAFE_INTEGER
        or (value == 0 and not allow_zero)
    ):
        raise ExpectedLeafAuthorityTypeError(
            name + " is outside its exact safe-integer bound"
        )
    return value


def _exact_bytes(value: object, *, name: str, maximum: int) -> bytes:
    if type(value) is not bytes:
        raise TypeError(name + " must be exact immutable bytes")
    if not value or len(value) > maximum:
        raise ExpectedLeafAuthorityTypeError(
            name + " is outside its byte bound"
        )
    return value


def _fixed_text(value: object, expected: str, *, name: str) -> None:
    if type(value) is not str or value != expected:
        raise ExpectedLeafAuthorityTypeError(name + " differs from fixed V1")


def _sorted_public_ids(
    value: object,
    *,
    name: str,
) -> Tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    result = tuple(_public_id(item, name=name) for item in value)
    if result != tuple(sorted(set(result))):
        raise ExpectedLeafAuthorityTypeError(
            name + " must be sorted and duplicate-free"
        )
    return result


def _validate_bundle_static_identity(value: object) -> None:
    _fixed_text(
        getattr(value, "expected_leaf_bundle_artifact_type"),
        EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE,
        name="expected_leaf_bundle_artifact_type",
    )
    _fixed_text(
        getattr(value, "expected_leaf_bundle_format_version"),
        EXPECTED_LEAF_BUNDLE_FORMAT_VERSION,
        name="expected_leaf_bundle_format_version",
    )
    _bounded_integer(
        getattr(value, "expected_leaf_bundle_byte_count"),
        name="expected_leaf_bundle_byte_count",
        maximum=MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
    )
    for name in (
        "expected_leaf_bundle_file_sha256",
        "expected_leaf_bundle_sha256",
        "reason_registry_sha256",
        "censor_reason_registry_sha256",
        "exclusion_reason_registry_sha256",
        "semantic_profile_sha256",
        "verifier_closure_sha256",
    ):
        _sha256(getattr(value, name), name=name)


def _validate_archive_identity(value: object) -> None:
    _bounded_integer(
        getattr(value, "expected_leaf_archive_byte_count"),
        name="expected_leaf_archive_byte_count",
        maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES,
    )
    _bounded_integer(
        getattr(value, "expected_leaf_archive_inventory_byte_count"),
        name="expected_leaf_archive_inventory_byte_count",
        maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES,
    )
    for name in (
        "expected_leaf_archive_sha256",
        "expected_leaf_archive_inventory_file_sha256",
        "expected_leaf_archive_inventory_sha256",
    ):
        _sha256(getattr(value, name), name=name)


@dataclass(frozen=True)
class ExpectedLeafReasonRegistryV1:
    """The approved exact category sets, never permissive subsets."""

    allowed_censor_reason_codes: Tuple[str, ...]
    allowed_exclusion_reason_codes: Tuple[str, ...]
    artifact_type: str = field(
        default=EXPECTED_LEAF_REASON_REGISTRY_ARTIFACT_TYPE,
        init=False,
    )
    binding_mode_id: str = field(
        default=EXPECTED_LEAF_REASON_REGISTRY_BINDING_MODE_ID,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafReasonRegistryV1:
            raise TypeError("expected-leaf reason registry must be exact")
        censors = _sorted_public_ids(
            self.allowed_censor_reason_codes,
            name="allowed_censor_reason_codes",
        )
        exclusions = _sorted_public_ids(
            self.allowed_exclusion_reason_codes,
            name="allowed_exclusion_reason_codes",
        )
        if len(censors) + len(exclusions) > MAXIMUM_EXPECTED_LEAF_REASON_CODES:
            raise ExpectedLeafAuthorityTypeError(
                "combined reason registry exceeds its exact bound"
            )
        _fixed_text(
            self.artifact_type,
            EXPECTED_LEAF_REASON_REGISTRY_ARTIFACT_TYPE,
            name="artifact_type",
        )
        _fixed_text(
            self.binding_mode_id,
            EXPECTED_LEAF_REASON_REGISTRY_BINDING_MODE_ID,
            name="binding_mode_id",
        )
        _fixed_text(self.format_version, "1", name="format_version")


@dataclass(frozen=True)
class ExpectedLeafMemberDigestDomainV1:
    """One member identifier and its only admitted payload digest domain."""

    member_id: str
    payload_digest_domain: str

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafMemberDigestDomainV1:
            raise TypeError("expected-leaf member digest domain must be exact")
        _public_id(self.member_id, name="member_id")
        _public_id(self.payload_digest_domain, name="payload_digest_domain")
        if (
            self.member_id,
            self.payload_digest_domain,
        ) not in EXPECTED_LEAF_MEMBER_DIGEST_DOMAIN_PAIRS:
            raise ExpectedLeafAuthorityTypeError(
                "member digest-domain pair is not admitted"
            )


EXPECTED_LEAF_MEMBER_DIGEST_DOMAINS = tuple(
    ExpectedLeafMemberDigestDomainV1(member_id, digest_domain)
    for member_id, digest_domain in EXPECTED_LEAF_MEMBER_DIGEST_DOMAIN_PAIRS
)


@dataclass(frozen=True)
class ExpectedLeafSemanticProfileV1:
    """Closed checkpoint-44 parser, resource, and nonclaim semantics."""

    artifact_type: str = field(
        default=EXPECTED_LEAF_SEMANTIC_PROFILE_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    expected_leaf_bundle_artifact_type: str = field(
        default=EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE,
        init=False,
    )
    expected_leaf_bundle_format_version: str = field(
        default=EXPECTED_LEAF_BUNDLE_FORMAT_VERSION,
        init=False,
    )
    member_digest_domains: Tuple[
        ExpectedLeafMemberDigestDomainV1, ...
    ] = field(default=EXPECTED_LEAF_MEMBER_DIGEST_DOMAINS, init=False)
    canonical_json_profile_id: str = field(
        default=EXPECTED_LEAF_CANONICAL_JSON_PROFILE_ID,
        init=False,
    )
    base64_profile_id: str = field(
        default=EXPECTED_LEAF_BASE64_PROFILE_ID,
        init=False,
    )
    unicode_profile_id: str = field(
        default=EXPECTED_LEAF_UNICODE_PROFILE_ID,
        init=False,
    )
    semantic_scope_id: str = field(
        default=EXPECTED_LEAF_SEMANTIC_SCOPE_ID,
        init=False,
    )
    format_payload_scope_id: str = field(
        default=EXPECTED_LEAF_FORMAT_PAYLOAD_SCOPE_ID,
        init=False,
    )
    truth_scope_id: str = field(
        default=EXPECTED_LEAF_TRUTH_SCOPE_ID,
        init=False,
    )
    structural_true_claim_ids: Tuple[str, ...] = field(
        default=EXPECTED_LEAF_STRUCTURAL_TRUE_CLAIM_IDS,
        init=False,
    )
    false_claim_ids: Tuple[str, ...] = field(
        default=EXPECTED_LEAF_FALSE_CLAIM_IDS,
        init=False,
    )
    maximum_expected_leaf_bundle_bytes: int = field(
        default=MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
        init=False,
    )
    maximum_expected_leaf_verification_input_bytes: int = field(
        default=MAXIMUM_EXPECTED_LEAF_VERIFICATION_INPUT_BYTES,
        init=False,
    )
    maximum_expected_leaf_verification_receipt_bytes: int = field(
        default=MAXIMUM_EXPECTED_LEAF_VERIFICATION_RECEIPT_BYTES,
        init=False,
    )
    maximum_canonical_depth: int = field(
        default=MAXIMUM_CANONICAL_DEPTH,
        init=False,
    )
    maximum_canonical_nodes: int = field(
        default=MAXIMUM_CANONICAL_NODES,
        init=False,
    )
    maximum_canonical_string_bytes: int = field(
        default=MAXIMUM_CANONICAL_STRING_BYTES,
        init=False,
    )
    maximum_private_payload_bytes: int = field(
        default=MAXIMUM_PRIVATE_PAYLOAD_BYTES,
        init=False,
    )
    maximum_single_payload_bytes: int = field(
        default=MAXIMUM_SINGLE_PAYLOAD_BYTES,
        init=False,
    )
    maximum_source_bytes: int = field(
        default=MAXIMUM_SOURCE_BYTES,
        init=False,
    )
    maximum_inventory_items: int = field(
        default=MAXIMUM_INVENTORY_ITEMS,
        init=False,
    )
    maximum_semantic_occurrences: int = field(
        default=MAXIMUM_SEMANTIC_OCCURRENCES,
        init=False,
    )
    maximum_split_entries: int = field(
        default=MAXIMUM_SPLIT_ENTRIES,
        init=False,
    )
    maximum_split_groups: int = field(
        default=MAXIMUM_SPLIT_GROUPS,
        init=False,
    )
    maximum_declared_event_types: int = field(
        default=MAXIMUM_DECLARED_EVENT_TYPES,
        init=False,
    )
    maximum_fields_per_event_type: int = field(
        default=MAXIMUM_FIELDS_PER_EVENT_TYPE,
        init=False,
    )
    maximum_scalar_coordinates_per_event_type: int = field(
        default=MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE,
        init=False,
    )
    maximum_scalar_coordinates_per_occurrence: int = field(
        default=MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE,
        init=False,
    )
    maximum_time_atoms: int = field(
        default=MAXIMUM_TIME_ATOMS,
        init=False,
    )
    maximum_event_id_tuple_arity: int = field(
        default=MAXIMUM_EVENT_ID_TUPLE_ARITY,
        init=False,
    )
    maximum_event_id_component_bytes: int = field(
        default=MAXIMUM_EVENT_ID_COMPONENT_BYTES,
        init=False,
    )
    maximum_event_id_metadata_bytes: int = field(
        default=MAXIMUM_EVENT_ID_METADATA_BYTES,
        init=False,
    )
    maximum_keyed_leaf_entries: int = field(
        default=MAXIMUM_KEYED_LEAF_ENTRIES,
        init=False,
    )
    maximum_field_statuses_per_occurrence: int = field(
        default=MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE,
        init=False,
    )
    maximum_source_links_per_occurrence: int = field(
        default=MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE,
        init=False,
    )
    maximum_total_provenance_source_links: int = field(
        default=MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS,
        init=False,
    )
    maximum_secondary_tags_per_item: int = field(
        default=MAXIMUM_SECONDARY_TAGS_PER_ITEM,
        init=False,
    )
    maximum_total_secondary_tags: int = field(
        default=MAXIMUM_TOTAL_SECONDARY_TAGS,
        init=False,
    )
    maximum_reason_codes: int = field(
        default=MAXIMUM_REASON_CODES,
        init=False,
    )
    maximum_representation_ids: int = field(
        default=MAXIMUM_REPRESENTATION_IDS,
        init=False,
    )
    maximum_public_token_bytes: int = field(
        default=MAXIMUM_PUBLIC_TOKEN_BYTES,
        init=False,
    )
    maximum_private_text_codepoints: int = field(
        default=MAXIMUM_PRIVATE_TEXT_CODEPOINTS,
        init=False,
    )
    maximum_safe_integer: int = field(
        default=MAXIMUM_SAFE_INTEGER,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafSemanticProfileV1:
            raise TypeError("expected-leaf semantic profile must be exact")
        for name in (
            "artifact_type",
            "format_version",
            "expected_leaf_bundle_artifact_type",
            "expected_leaf_bundle_format_version",
            "canonical_json_profile_id",
            "base64_profile_id",
            "unicode_profile_id",
            "semantic_scope_id",
            "format_payload_scope_id",
            "truth_scope_id",
        ):
            if type(getattr(self, name)) is not str:
                raise TypeError(name + " must be an exact string")
        if type(self.member_digest_domains) is not tuple or any(
            type(item) is not ExpectedLeafMemberDigestDomainV1
            for item in self.member_digest_domains
        ):
            raise TypeError(
                "member_digest_domains must contain exact domain records"
            )
        for item in self.member_digest_domains:
            ExpectedLeafMemberDigestDomainV1.__post_init__(item)
        for name in ("structural_true_claim_ids", "false_claim_ids"):
            values = getattr(self, name)
            if type(values) is not tuple or any(
                type(item) is not str for item in values
            ):
                raise TypeError(name + " must be an exact string tuple")
        for name in (
            "maximum_expected_leaf_bundle_bytes",
            "maximum_expected_leaf_verification_input_bytes",
            "maximum_expected_leaf_verification_receipt_bytes",
            "maximum_canonical_depth",
            "maximum_canonical_nodes",
            "maximum_canonical_string_bytes",
            "maximum_private_payload_bytes",
            "maximum_single_payload_bytes",
            "maximum_source_bytes",
            "maximum_inventory_items",
            "maximum_semantic_occurrences",
            "maximum_split_entries",
            "maximum_split_groups",
            "maximum_declared_event_types",
            "maximum_fields_per_event_type",
            "maximum_scalar_coordinates_per_event_type",
            "maximum_scalar_coordinates_per_occurrence",
            "maximum_time_atoms",
            "maximum_event_id_tuple_arity",
            "maximum_event_id_component_bytes",
            "maximum_event_id_metadata_bytes",
            "maximum_keyed_leaf_entries",
            "maximum_field_statuses_per_occurrence",
            "maximum_source_links_per_occurrence",
            "maximum_total_provenance_source_links",
            "maximum_secondary_tags_per_item",
            "maximum_total_secondary_tags",
            "maximum_reason_codes",
            "maximum_representation_ids",
            "maximum_public_token_bytes",
            "maximum_private_text_codepoints",
            "maximum_safe_integer",
        ):
            if type(getattr(self, name)) is not int:
                raise TypeError(name + " must be an exact integer")
        fixed_values = (
            self.artifact_type,
            self.format_version,
            self.expected_leaf_bundle_artifact_type,
            self.expected_leaf_bundle_format_version,
            self.member_digest_domains,
            self.canonical_json_profile_id,
            self.base64_profile_id,
            self.unicode_profile_id,
            self.semantic_scope_id,
            self.format_payload_scope_id,
            self.truth_scope_id,
            self.structural_true_claim_ids,
            self.false_claim_ids,
            self.maximum_expected_leaf_bundle_bytes,
            self.maximum_expected_leaf_verification_input_bytes,
            self.maximum_expected_leaf_verification_receipt_bytes,
            self.maximum_canonical_depth,
            self.maximum_canonical_nodes,
            self.maximum_canonical_string_bytes,
            self.maximum_private_payload_bytes,
            self.maximum_single_payload_bytes,
            self.maximum_source_bytes,
            self.maximum_inventory_items,
            self.maximum_semantic_occurrences,
            self.maximum_split_entries,
            self.maximum_split_groups,
            self.maximum_declared_event_types,
            self.maximum_fields_per_event_type,
            self.maximum_scalar_coordinates_per_event_type,
            self.maximum_scalar_coordinates_per_occurrence,
            self.maximum_time_atoms,
            self.maximum_event_id_tuple_arity,
            self.maximum_event_id_component_bytes,
            self.maximum_event_id_metadata_bytes,
            self.maximum_keyed_leaf_entries,
            self.maximum_field_statuses_per_occurrence,
            self.maximum_source_links_per_occurrence,
            self.maximum_total_provenance_source_links,
            self.maximum_secondary_tags_per_item,
            self.maximum_total_secondary_tags,
            self.maximum_reason_codes,
            self.maximum_representation_ids,
            self.maximum_public_token_bytes,
            self.maximum_private_text_codepoints,
            self.maximum_safe_integer,
        )
        expected_values = (
            EXPECTED_LEAF_SEMANTIC_PROFILE_ARTIFACT_TYPE,
            "1",
            EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE,
            EXPECTED_LEAF_BUNDLE_FORMAT_VERSION,
            EXPECTED_LEAF_MEMBER_DIGEST_DOMAINS,
            EXPECTED_LEAF_CANONICAL_JSON_PROFILE_ID,
            EXPECTED_LEAF_BASE64_PROFILE_ID,
            EXPECTED_LEAF_UNICODE_PROFILE_ID,
            EXPECTED_LEAF_SEMANTIC_SCOPE_ID,
            EXPECTED_LEAF_FORMAT_PAYLOAD_SCOPE_ID,
            EXPECTED_LEAF_TRUTH_SCOPE_ID,
            EXPECTED_LEAF_STRUCTURAL_TRUE_CLAIM_IDS,
            EXPECTED_LEAF_FALSE_CLAIM_IDS,
            MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
            MAXIMUM_EXPECTED_LEAF_VERIFICATION_INPUT_BYTES,
            MAXIMUM_EXPECTED_LEAF_VERIFICATION_RECEIPT_BYTES,
            MAXIMUM_CANONICAL_DEPTH,
            MAXIMUM_CANONICAL_NODES,
            MAXIMUM_CANONICAL_STRING_BYTES,
            MAXIMUM_PRIVATE_PAYLOAD_BYTES,
            MAXIMUM_SINGLE_PAYLOAD_BYTES,
            MAXIMUM_SOURCE_BYTES,
            MAXIMUM_INVENTORY_ITEMS,
            MAXIMUM_SEMANTIC_OCCURRENCES,
            MAXIMUM_SPLIT_ENTRIES,
            MAXIMUM_SPLIT_GROUPS,
            MAXIMUM_DECLARED_EVENT_TYPES,
            MAXIMUM_FIELDS_PER_EVENT_TYPE,
            MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE,
            MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE,
            MAXIMUM_TIME_ATOMS,
            MAXIMUM_EVENT_ID_TUPLE_ARITY,
            MAXIMUM_EVENT_ID_COMPONENT_BYTES,
            MAXIMUM_EVENT_ID_METADATA_BYTES,
            MAXIMUM_KEYED_LEAF_ENTRIES,
            MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE,
            MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE,
            MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS,
            MAXIMUM_SECONDARY_TAGS_PER_ITEM,
            MAXIMUM_TOTAL_SECONDARY_TAGS,
            MAXIMUM_REASON_CODES,
            MAXIMUM_REPRESENTATION_IDS,
            MAXIMUM_PUBLIC_TOKEN_BYTES,
            MAXIMUM_PRIVATE_TEXT_CODEPOINTS,
            MAXIMUM_SAFE_INTEGER,
        )
        if fixed_values != expected_values:
            raise ExpectedLeafAuthorityTypeError(
                "expected-leaf semantic profile is not the closed V1 profile"
            )


@dataclass(frozen=True)
class ExpectedLeafVerifierSourceExpectationV1:
    """Plain source identity for one required independent verifier module."""

    module_id: str
    source_byte_count: int
    source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafVerifierSourceExpectationV1:
            raise TypeError("verifier source expectation must be exact")
        _public_id(self.module_id, name="module_id")
        if self.module_id not in EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS:
            raise ExpectedLeafAuthorityTypeError(
                "verifier source module is not in the exact closure"
            )
        _bounded_integer(
            self.source_byte_count,
            name="source_byte_count",
            maximum=MAXIMUM_EXPECTED_LEAF_VERIFIER_SOURCE_BYTES,
        )
        _sha256(self.source_sha256, name="source_sha256")


@dataclass(frozen=True)
class ExpectedLeafVerifierClosureV1:
    """The exact two-source verifier closure and its parent archive."""

    sources: Tuple[ExpectedLeafVerifierSourceExpectationV1, ...]
    source_tree_archive_sha256: str
    source_tree_manifest_sha256: str
    artifact_type: str = field(
        default=EXPECTED_LEAF_VERIFIER_CLOSURE_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafVerifierClosureV1:
            raise TypeError("expected-leaf verifier closure must be exact")
        if type(self.sources) is not tuple:
            raise TypeError("sources must be an exact tuple")
        if any(
            type(item) is not ExpectedLeafVerifierSourceExpectationV1
            for item in self.sources
        ):
            raise TypeError(
                "sources must contain exact verifier source expectations"
            )
        for item in self.sources:
            ExpectedLeafVerifierSourceExpectationV1.__post_init__(item)
        module_ids = tuple(item.module_id for item in self.sources)
        if module_ids != EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS:
            raise ExpectedLeafAuthorityTypeError(
                "verifier closure must equal the two required modules"
            )
        _sha256(
            self.source_tree_archive_sha256,
            name="source_tree_archive_sha256",
        )
        _sha256(
            self.source_tree_manifest_sha256,
            name="source_tree_manifest_sha256",
        )
        _fixed_text(
            self.artifact_type,
            EXPECTED_LEAF_VERIFIER_CLOSURE_ARTIFACT_TYPE,
            name="artifact_type",
        )
        _fixed_text(self.format_version, "1", name="format_version")


@dataclass(frozen=True)
class ExpectedLeafVerifierSourceInputV1:
    """Exact source bytes separately supplied at the authority boundary."""

    module_id: str
    source_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafVerifierSourceInputV1:
            raise TypeError("verifier source input must be exact")
        _public_id(self.module_id, name="module_id")
        if self.module_id not in EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS:
            raise ExpectedLeafAuthorityTypeError(
                "verifier input module is not in the exact closure"
            )
        _exact_bytes(
            self.source_bytes,
            name="source_bytes",
            maximum=MAXIMUM_EXPECTED_LEAF_VERIFIER_SOURCE_BYTES,
        )


@dataclass(frozen=True)
class IndependentGoldenExpectedLeafExtensionV1:
    """One approved expected-leaf extension to a base golden receipt."""

    base_golden_receipt_sha256: str
    case_authority_id: str
    case_ordinal: int
    adapter_id: str
    adapter_version: str
    descriptor_sha256: str
    source_sha256: str
    split_manifest_sha256: str
    expected_configuration_sha256: str
    expected_evidence_sha256: str
    expected_native_observation_sha256: str
    expected_leaf_bundle_artifact_type: str
    expected_leaf_bundle_format_version: str
    expected_leaf_bundle_byte_count: int
    expected_leaf_bundle_file_sha256: str
    expected_leaf_bundle_sha256: str
    reason_registry_sha256: str
    censor_reason_registry_sha256: str
    exclusion_reason_registry_sha256: str
    semantic_profile_sha256: str
    verifier_closure_sha256: str
    expected_leaf_archive_byte_count: int
    expected_leaf_archive_sha256: str
    expected_leaf_archive_inventory_byte_count: int
    expected_leaf_archive_inventory_file_sha256: str
    expected_leaf_archive_inventory_sha256: str
    expected_leaf_archive_object_id: str
    artifact_type: str = field(
        default=INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not IndependentGoldenExpectedLeafExtensionV1:
            raise TypeError("independent golden expected-leaf extension must be exact")
        _adapter_identity(self.adapter_id, self.adapter_version)
        _bounded_integer(
            self.case_ordinal,
            name="case_ordinal",
            maximum=MAXIMUM_EXPECTED_LEAF_CASES - 1,
            allow_zero=True,
        )
        for name in (
            "base_golden_receipt_sha256",
            "case_authority_id",
            "descriptor_sha256",
            "source_sha256",
            "split_manifest_sha256",
            "expected_configuration_sha256",
            "expected_evidence_sha256",
            "expected_native_observation_sha256",
        ):
            _sha256(getattr(self, name), name=name)
        _validate_bundle_static_identity(self)
        _validate_archive_identity(self)
        _sha256(
            self.expected_leaf_archive_object_id,
            name="expected_leaf_archive_object_id",
        )
        if self.expected_leaf_archive_object_id != self.case_authority_id:
            raise ExpectedLeafAuthorityTypeError(
                "expected-leaf archive object ID must equal case authority ID"
            )
        _fixed_text(
            self.artifact_type,
            INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_ARTIFACT_TYPE,
            name="artifact_type",
        )
        _fixed_text(self.format_version, "1", name="format_version")


@dataclass(frozen=True)
class IndependentGoldenExpectedLeafExtensionInputV1:
    """Typed extension plus its exact independently supplied receipt bytes."""

    receipt: IndependentGoldenExpectedLeafExtensionV1
    receipt_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not IndependentGoldenExpectedLeafExtensionInputV1:
            raise TypeError("independent golden expected-leaf input must be exact")
        if type(self.receipt) is not IndependentGoldenExpectedLeafExtensionV1:
            raise TypeError("expected-leaf extension receipt must be exact")
        IndependentGoldenExpectedLeafExtensionV1.__post_init__(self.receipt)
        _exact_bytes(
            self.receipt_bytes,
            name="receipt_bytes",
            maximum=(
                MAXIMUM_INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_BYTES
            ),
        )


@dataclass(frozen=True)
class ApprovedExpectedLeafCaseExpectationV1:
    """Static authority links for one canonically positioned base case."""

    base_case_expectation_sha256: str
    golden_extension_sha256: str
    case_authority_id: str
    case_ordinal: int
    expected_leaf_bundle_artifact_type: str
    expected_leaf_bundle_format_version: str
    expected_leaf_bundle_byte_count: int
    expected_leaf_bundle_file_sha256: str
    expected_leaf_bundle_sha256: str
    reason_registry_sha256: str
    censor_reason_registry_sha256: str
    exclusion_reason_registry_sha256: str
    semantic_profile_sha256: str
    verifier_closure_sha256: str
    expected_leaf_archive_byte_count: int
    expected_leaf_archive_sha256: str
    expected_leaf_archive_inventory_byte_count: int
    expected_leaf_archive_inventory_file_sha256: str
    expected_leaf_archive_inventory_sha256: str
    expected_leaf_archive_object_id: str

    def __post_init__(self) -> None:
        if type(self) is not ApprovedExpectedLeafCaseExpectationV1:
            raise TypeError("approved expected-leaf case expectation must be exact")
        _bounded_integer(
            self.case_ordinal,
            name="case_ordinal",
            maximum=MAXIMUM_EXPECTED_LEAF_CASES - 1,
            allow_zero=True,
        )
        for name in (
            "base_case_expectation_sha256",
            "golden_extension_sha256",
            "case_authority_id",
        ):
            _sha256(getattr(self, name), name=name)
        _validate_bundle_static_identity(self)
        _validate_archive_identity(self)
        _sha256(
            self.expected_leaf_archive_object_id,
            name="expected_leaf_archive_object_id",
        )
        if self.expected_leaf_archive_object_id != self.case_authority_id:
            raise ExpectedLeafAuthorityTypeError(
                "expected-leaf archive object ID must equal case authority ID"
            )


@dataclass(frozen=True)
class ApprovedExpectedLeafAuthorityProfileV1:
    """Parsed expected-leaf profile; its separate anchor supplies authority."""

    parent_approved_profile_file_sha256: str
    parent_approved_profile_sha256: str
    reason_registry: ExpectedLeafReasonRegistryV1
    semantic_profile: ExpectedLeafSemanticProfileV1
    verifier_closure: ExpectedLeafVerifierClosureV1
    expected_leaf_archive_byte_count: int
    expected_leaf_archive_sha256: str
    expected_leaf_archive_inventory_byte_count: int
    expected_leaf_archive_inventory_file_sha256: str
    expected_leaf_archive_inventory_sha256: str
    case_expectations: Tuple[ApprovedExpectedLeafCaseExpectationV1, ...]
    approval_status_id: str = field(
        default=APPROVED_EXPECTED_LEAF_AUTHORITY_STATUS,
        init=False,
    )
    artifact_type: str = field(
        default=APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    profile_id: str = field(
        default=APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ID,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not ApprovedExpectedLeafAuthorityProfileV1:
            raise TypeError("approved expected-leaf authority profile must be exact")
        _sha256(
            self.parent_approved_profile_file_sha256,
            name="parent_approved_profile_file_sha256",
        )
        _sha256(
            self.parent_approved_profile_sha256,
            name="parent_approved_profile_sha256",
        )
        if type(self.reason_registry) is not ExpectedLeafReasonRegistryV1:
            raise TypeError("reason_registry must be exact")
        ExpectedLeafReasonRegistryV1.__post_init__(self.reason_registry)
        if type(self.semantic_profile) is not ExpectedLeafSemanticProfileV1:
            raise TypeError("semantic_profile must be exact")
        ExpectedLeafSemanticProfileV1.__post_init__(self.semantic_profile)
        if type(self.verifier_closure) is not ExpectedLeafVerifierClosureV1:
            raise TypeError("verifier_closure must be exact")
        ExpectedLeafVerifierClosureV1.__post_init__(self.verifier_closure)
        _validate_archive_identity(self)
        cases = self.case_expectations
        if type(cases) is not tuple or not cases:
            raise TypeError(
                "case_expectations must be a nonempty exact tuple"
            )
        if len(cases) > MAXIMUM_EXPECTED_LEAF_CASES:
            raise ExpectedLeafAuthorityTypeError(
                "too many approved expected-leaf cases"
            )
        if any(
            type(item) is not ApprovedExpectedLeafCaseExpectationV1
            for item in cases
        ):
            raise TypeError(
                "case_expectations must contain exact expected-leaf cases"
            )
        for item in cases:
            ApprovedExpectedLeafCaseExpectationV1.__post_init__(item)
        if tuple(item.case_ordinal for item in cases) != tuple(
            range(len(cases))
        ):
            raise ExpectedLeafAuthorityTypeError(
                "case ordinals must equal base-profile tuple positions"
            )
        authority_ids = tuple(item.case_authority_id for item in cases)
        if len(set(authority_ids)) != len(authority_ids):
            raise ExpectedLeafAuthorityTypeError(
                "case authority IDs must be unique"
            )
        for name in (
            "base_case_expectation_sha256",
            "golden_extension_sha256",
        ):
            identities = tuple(getattr(item, name) for item in cases)
            if len(set(identities)) != len(identities):
                raise ExpectedLeafAuthorityTypeError(
                    name + " values must be unique"
                )
        profile_link_identities = tuple(
            (
                item.reason_registry_sha256,
                item.censor_reason_registry_sha256,
                item.exclusion_reason_registry_sha256,
                item.semantic_profile_sha256,
                item.verifier_closure_sha256,
            )
            for item in cases
        )
        if any(
            identity != profile_link_identities[0]
            for identity in profile_link_identities
        ):
            raise ExpectedLeafAuthorityTypeError(
                "case reason, semantic, or closure identities differ"
            )
        archive_identity = (
            self.expected_leaf_archive_byte_count,
            self.expected_leaf_archive_sha256,
            self.expected_leaf_archive_inventory_byte_count,
            self.expected_leaf_archive_inventory_file_sha256,
            self.expected_leaf_archive_inventory_sha256,
        )
        if any(
            (
                item.expected_leaf_archive_byte_count,
                item.expected_leaf_archive_sha256,
                item.expected_leaf_archive_inventory_byte_count,
                item.expected_leaf_archive_inventory_file_sha256,
                item.expected_leaf_archive_inventory_sha256,
            )
            != archive_identity
            for item in cases
        ):
            raise ExpectedLeafAuthorityTypeError(
                "case archive identities differ from the profile"
            )
        _fixed_text(
            self.approval_status_id,
            APPROVED_EXPECTED_LEAF_AUTHORITY_STATUS,
            name="approval_status_id",
        )
        _fixed_text(
            self.artifact_type,
            APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ARTIFACT_TYPE,
            name="artifact_type",
        )
        _fixed_text(self.format_version, "1", name="format_version")
        _fixed_text(
            self.profile_id,
            APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ID,
            name="profile_id",
        )


@dataclass(frozen=True)
class ApprovedExpectedLeafAuthorityProfileAnchorV1:
    """Out-of-band trust root for exact approved profile bytes."""

    profile_byte_count: int
    profile_file_sha256: str
    profile_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ApprovedExpectedLeafAuthorityProfileAnchorV1:
            raise TypeError("approved expected-leaf profile anchor must be exact")
        _bounded_integer(
            self.profile_byte_count,
            name="profile_byte_count",
            maximum=MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
        )
        _sha256(self.profile_file_sha256, name="profile_file_sha256")
        _sha256(self.profile_sha256, name="profile_sha256")


@dataclass(frozen=True)
class ApprovedExpectedLeafAuthorityInputV1:
    """Separately supplied profile, anchor, and exact verifier source bytes."""

    profile_bytes: bytes
    anchor: ApprovedExpectedLeafAuthorityProfileAnchorV1
    verifier_source_inputs: Tuple[ExpectedLeafVerifierSourceInputV1, ...]

    def __post_init__(self) -> None:
        if type(self) is not ApprovedExpectedLeafAuthorityInputV1:
            raise TypeError("approved expected-leaf authority input must be exact")
        _exact_bytes(
            self.profile_bytes,
            name="profile_bytes",
            maximum=MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
        )
        if type(self.anchor) is not ApprovedExpectedLeafAuthorityProfileAnchorV1:
            raise TypeError("approved expected-leaf profile anchor must be exact")
        ApprovedExpectedLeafAuthorityProfileAnchorV1.__post_init__(
            self.anchor
        )
        values = self.verifier_source_inputs
        if type(values) is not tuple:
            raise TypeError("verifier_source_inputs must be an exact tuple")
        if any(
            type(item) is not ExpectedLeafVerifierSourceInputV1
            for item in values
        ):
            raise TypeError(
                "verifier_source_inputs must contain exact source inputs"
            )
        for item in values:
            ExpectedLeafVerifierSourceInputV1.__post_init__(item)
        if tuple(item.module_id for item in values) != (
            EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS
        ):
            raise ExpectedLeafAuthorityTypeError(
                "verifier source inputs must equal the required closure"
            )


__all__ = [
    "APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ARTIFACT_TYPE",
    "APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_DIGEST_DOMAIN",
    "APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ID",
    "APPROVED_EXPECTED_LEAF_AUTHORITY_STATUS",
    "ApprovedExpectedLeafAuthorityInputV1",
    "ApprovedExpectedLeafAuthorityProfileAnchorV1",
    "ApprovedExpectedLeafAuthorityProfileV1",
    "ApprovedExpectedLeafCaseExpectationV1",
    "EXPECTED_LEAF_BASE64_PROFILE_ID",
    "EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE",
    "EXPECTED_LEAF_BUNDLE_FORMAT_VERSION",
    "EXPECTED_LEAF_BUNDLE_VERIFIER_MODULE_ID",
    "EXPECTED_LEAF_CANONICAL_JSON_PROFILE_ID",
    "EXPECTED_LEAF_CASE_AUTHORITY_ID_DIGEST_DOMAIN",
    "EXPECTED_LEAF_CENSOR_REASON_REGISTRY_DIGEST_DOMAIN",
    "EXPECTED_LEAF_EXCLUSION_REASON_REGISTRY_DIGEST_DOMAIN",
    "EXPECTED_LEAF_FALSE_CLAIM_IDS",
    "EXPECTED_LEAF_FORMAT_PAYLOAD_SCOPE_ID",
    "EXPECTED_LEAF_MEMBER_DIGEST_DOMAINS",
    "EXPECTED_LEAF_MEMBER_DIGEST_DOMAIN_PAIRS",
    "EXPECTED_LEAF_ORACLE_VERIFIER_MODULE_ID",
    "EXPECTED_LEAF_REASON_REGISTRY_ARTIFACT_TYPE",
    "EXPECTED_LEAF_REASON_REGISTRY_BINDING_MODE_ID",
    "EXPECTED_LEAF_REASON_REGISTRY_DIGEST_DOMAIN",
    "EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS",
    "EXPECTED_LEAF_SEMANTIC_PROFILE_ARTIFACT_TYPE",
    "EXPECTED_LEAF_SEMANTIC_PROFILE_DIGEST_DOMAIN",
    "EXPECTED_LEAF_SEMANTIC_SCOPE_ID",
    "EXPECTED_LEAF_STRUCTURAL_TRUE_CLAIM_IDS",
    "EXPECTED_LEAF_TRUTH_SCOPE_ID",
    "EXPECTED_LEAF_UNICODE_PROFILE_ID",
    "EXPECTED_LEAF_VERIFIER_CLOSURE_ARTIFACT_TYPE",
    "EXPECTED_LEAF_VERIFIER_CLOSURE_DIGEST_DOMAIN",
    "ExpectedLeafAuthorityTypeError",
    "ExpectedLeafMemberDigestDomainV1",
    "ExpectedLeafReasonRegistryV1",
    "ExpectedLeafSemanticProfileV1",
    "ExpectedLeafVerifierClosureV1",
    "ExpectedLeafVerifierSourceExpectationV1",
    "ExpectedLeafVerifierSourceInputV1",
    "INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_ARTIFACT_TYPE",
    "INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_DIGEST_DOMAIN",
    "IndependentGoldenExpectedLeafExtensionInputV1",
    "IndependentGoldenExpectedLeafExtensionV1",
    "MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES",
    "MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES",
    "MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES",
    "MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES",
    "MAXIMUM_EXPECTED_LEAF_CASES",
    "MAXIMUM_EXPECTED_LEAF_REASON_CODES",
    "MAXIMUM_EXPECTED_LEAF_VERIFIER_SOURCE_BYTES",
    "MAXIMUM_INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_BYTES",
    "MAXIMUM_SAFE_INTEGER",
]
