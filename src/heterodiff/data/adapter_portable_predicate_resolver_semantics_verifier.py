"""Independent verifier for one static resolver-reference sidecar.

Checkpoint 56E closes only a selected-profile-bound, static description of
source references, authority requirements, and locator references.  It does not
accept source or credential bytes, execute a locator, authenticate evidence,
construct an official nonempty input bundle, or authorize promotion.

This module deliberately depends only on verifier-lane contracts.  It never
imports the source Checkpoint-56E compiler, its constants, helpers, result
type, or result values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Final

from heterodiff.data import (
    adapter_portable_predicate_context_input_verifier as _quarantine,
)
from heterodiff.data import (
    adapter_portable_predicate_language_core_verifier as _core,
)
from heterodiff.data import (
    adapter_portable_predicate_runtime_artifacts_verifier as _runtime,
)


__all__ = (
    "PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_IDENTITY_DOMAIN",
    "PORTABLE_PREDICATE_RESOLVER_REFERENCE_VALIDATION_SCOPE_ID",
    "PortablePredicateResolverReferenceVerificationCode",
    "PortablePredicateResolverReferenceVerificationError",
    "VerifiedPortablePredicateResolverReferenceV1",
    "verify_portable_predicate_resolver_reference_contract_v1",
)


PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.portable-predicate.resolver-reference-contract.v1"
)
PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_IDENTITY_DOMAIN: Final = (
    "heterodiff.portable-predicate."
    "resolver-reference-contract.identity.v1"
)
PORTABLE_PREDICATE_RESOLVER_REFERENCE_VALIDATION_SCOPE_ID: Final = (
    "STATIC_PROFILE_BOUND_RESOLVER_REFERENCE_CLOSURE_ONLY_V1"
)

_MAXIMUM_CONTRACT_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_JSON_INTEGER_DIGITS: Final = 20
_MAXIMUM_IDENTIFIER_BYTES: Final = 512
_MAXIMUM_SOURCE_KIND_ROWS: Final = 256
_MAXIMUM_AUTHORITY_ROWS: Final = 256
_MAXIMUM_LOCATOR_ROWS: Final = 256
_MAXIMUM_ROW_REFERENCES: Final = 65536
_MAXIMUM_REFERENCES_PER_ROW: Final = 256
_MAXIMUM_TRUST_SUBJECT_COUNT: Final = 32

_IDENTIFIER_RE: Final = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$"
)
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")

_SOURCE_MODE_IDS: Final = (
    "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED",
    "PRIOR_SIBLING_REFERENCE_REQUIRED",
)
_FRESHNESS_MODE_IDS: Final = (
    "ARCHIVAL_IMMUTABILITY_REQUIRED",
    "CONTEXT_BOUND_FRESHNESS_REQUIRED",
    "NOT_APPLICABLE",
)
_AUTHORITY_MODE_IDS: Final = (
    "DEPLOYMENT_TRUST_REQUIRED",
    "STATIC_REFERENCE_BLOCKED",
)
_REFERENCE_REQUIREMENT_MODE_IDS: Final = (
    "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED",
    "PRIOR_SIBLING_REFERENCE_REQUIRED",
    "STATIC_REFERENCE_BLOCKED",
)
_LOCATOR_PRIMITIVE_IDS: Final = (
    "bounded-artifact-path",
    "direct-bound-value",
    "ordered-index",
    "composite-key",
    "sibling-resolved-value",
)
_SOURCE_BACKED_PRIMITIVE_IDS: Final = _LOCATOR_PRIMITIVE_IDS[:4]
_STATIC_BLOCKING_REASON_ID: Final = (
    "OPAQUE_ANCHOR_CONTRACT_NOT_INTERPRETED"
)
_ANCHOR_FIELD_SEMANTIC_ROLE_IDS: Final = (
    "anchor-artifact-type-for-role",
    "anchor-contract-sha256-for-role",
)

_TOP_LEVEL_FIELDS: Final = (
    "artifact_type",
    "format_version",
    "semantic_core_contract_sha256",
    "profile_contract_artifact_type",
    "profile_contract_sha256",
    "ordered_source_kind_rows",
    "ordered_authority_requirement_rows",
    "ordered_locator_reference_rows",
    "nonclaim_state",
)
_SOURCE_ROW_FIELDS: Final = (
    "source_artifact_kind_id",
    "source_reference_mode_id",
    "source_snapshot_artifact_type_id",
    "source_identity_domain_id",
    "freshness_requirement_id",
)
_AUTHORITY_ROW_FIELDS: Final = (
    "authority_class_id",
    "authority_requirement_mode_id",
    "ordered_admitted_source_artifact_kind_ids",
    "minimum_distinct_trust_subject_count",
)
_LOCATOR_ROW_FIELDS: Final = (
    "locator_kind_id",
    "locator_primitive_id",
    "reference_requirement_mode_id",
    "source_artifact_kind_id",
    "ordered_minimum_authority_class_ids",
    "static_blocking_reason_id",
)
_NONCLAIM_FIELDS: Final = (
    "authority_credentials_authenticated",
    "deployment_trust_root_bound",
    "locator_interpreter_defined",
    "locator_executed",
    "official_input_bundle_constructed",
    "program_resolution_compatibility_validated",
    "replay_protection_established",
    "resolver_evidence_authenticated",
    "resolver_outcome_derived",
    "source_artifact_authenticated",
    "source_payload_decoded",
    "source_snapshot_schema_bound",
    "typed_leaf_binding_bound",
)


class PortablePredicateResolverReferenceVerificationCode(str, Enum):
    """Closed ordinary failures for the independent Checkpoint-56E lane."""

    INPUT_TYPE = "INPUT_TYPE"
    COMPILED_PROFILE_INVALID = "COMPILED_PROFILE_INVALID"
    CONTRACT_INPUT_RESOURCE = "CONTRACT_INPUT_RESOURCE"
    CONTRACT_JSON_INVALID = "CONTRACT_JSON_INVALID"
    CONTRACT_JSON_TREE_INVALID = "CONTRACT_JSON_TREE_INVALID"
    CONTRACT_CANONICAL_MISMATCH = "CONTRACT_CANONICAL_MISMATCH"
    CONTRACT_SCHEMA_INVALID = "CONTRACT_SCHEMA_INVALID"
    CONTRACT_BINDING_MISMATCH = "CONTRACT_BINDING_MISMATCH"
    CONTRACT_IDENTITY_MISMATCH = "CONTRACT_IDENTITY_MISMATCH"
    SOURCE_KIND_REGISTRY_INVALID = "SOURCE_KIND_REGISTRY_INVALID"
    AUTHORITY_REGISTRY_INVALID = "AUTHORITY_REGISTRY_INVALID"
    LOCATOR_REFERENCE_INVALID = "LOCATOR_REFERENCE_INVALID"
    PROFILE_COVERAGE_MISMATCH = "PROFILE_COVERAGE_MISMATCH"
    NAMESPACE_COLLISION = "NAMESPACE_COLLISION"
    RESULT_INVALID = "RESULT_INVALID"
    INTERNAL = "INTERNAL"


_ERROR_MESSAGES: Final = {
    code: (
        "portable predicate resolver reference verification "
        + code.value.lower().replace("_", " ")
    )
    for code in PortablePredicateResolverReferenceVerificationCode
}


class PortablePredicateResolverReferenceVerificationError(ValueError):
    """A fixed-message independent-verifier failure."""

    def __init__(
        self,
        code: PortablePredicateResolverReferenceVerificationCode,
    ):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True, repr=False)
class VerifiedPortablePredicateResolverReferenceV1:
    """Immutable receipt for one static profile-bound sidecar."""

    __slots__ = (
        "canonical_contract_bytes",
        "contract_artifact_type",
        "contract_identity_sha256",
        "contract_byte_count",
        "semantic_core_contract_sha256",
        "profile_contract_artifact_type",
        "profile_contract_sha256",
        "source_kind_bindings",
        "authority_requirement_bindings",
        "locator_reference_bindings",
        "snapshot_authentication_required_locator_count",
        "prior_sibling_reference_required_locator_count",
        "statically_blocked_locator_count",
        "validation_scope_id",
        "profile_locator_coverage_complete",
        "profile_authority_coverage_complete",
        "static_reference_closure_validated",
        "source_artifacts_validated",
        "authority_credentials_validated",
        "deployment_trust_bound",
        "resolver_executed",
        "official_input_bundle_constructed",
        "source_snapshot_schema_validated",
        "typed_leaf_binding_validated",
        "locator_interpreter_defined",
        "program_resolution_compatibility_validated",
        "resolver_outcomes_derived",
    )

    canonical_contract_bytes: bytes
    contract_artifact_type: str
    contract_identity_sha256: str
    contract_byte_count: int
    semantic_core_contract_sha256: str
    profile_contract_artifact_type: str
    profile_contract_sha256: str
    source_kind_bindings: tuple
    authority_requirement_bindings: tuple
    locator_reference_bindings: tuple
    snapshot_authentication_required_locator_count: int
    prior_sibling_reference_required_locator_count: int
    statically_blocked_locator_count: int
    validation_scope_id: str
    profile_locator_coverage_complete: bool
    profile_authority_coverage_complete: bool
    static_reference_closure_validated: bool
    source_artifacts_validated: bool
    authority_credentials_validated: bool
    deployment_trust_bound: bool
    resolver_executed: bool
    official_input_bundle_constructed: bool
    source_snapshot_schema_validated: bool
    typed_leaf_binding_validated: bool
    locator_interpreter_defined: bool
    program_resolution_compatibility_validated: bool
    resolver_outcomes_derived: bool

    def __repr__(self) -> str:
        return (
            "VerifiedPortablePredicateResolverReferenceV1("
            f"contract_byte_count={self.contract_byte_count}, "
            "snapshot_authentication_required_locator_count="
            f"{self.snapshot_authentication_required_locator_count}, "
            "prior_sibling_reference_required_locator_count="
            f"{self.prior_sibling_reference_required_locator_count}, "
            "statically_blocked_locator_count="
            f"{self.statically_blocked_locator_count}, "
            f"validation_scope_id={self.validation_scope_id!r}, "
            f"resolver_executed={self.resolver_executed})"
        )


def _reject(
    code: PortablePredicateResolverReferenceVerificationCode,
) -> None:
    raise PortablePredicateResolverReferenceVerificationError(code) from None


def _identifier(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        return False
    return (
        1 <= len(encoded) <= _MAXIMUM_IDENTIFIER_BYTES
        and _IDENTIFIER_RE.fullmatch(value) is not None
    )


def _empty_or_identifier(value: object) -> bool:
    return type(value) is str and (value == "" or _identifier(value))


def _sha256(value: object) -> bool:
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _exact_keys(value: object, expected: tuple) -> bool:
    return type(value) is dict and set(value) == set(expected)


def _bounded_integer(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if not digits or len(digits) > _MAXIMUM_JSON_INTEGER_DIGITS:
        raise ValueError("bounded JSON integer")
    return int(value, 10)


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii", "strict"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _revalidate_profile(compiled_profile: object) -> object:
    profile = None
    failure_code = None
    try:
        profile = _runtime._revalidate_profile_snapshot(compiled_profile)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError as error:
        failure_code = error.code
    if failure_code == (
        _runtime.PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL.value
    ):
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    if failure_code is not None:
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .COMPILED_PROFILE_INVALID
        )
    if profile is None:
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    return profile


def _decode_trusted_profile(profile: object) -> dict:
    try:
        decoded = json.loads(
            profile.canonical_profile_bytes.decode("ascii", "strict")
        )
    except (
        AttributeError,
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    if type(decoded) is not dict:
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    return decoded


def _decode_contract(raw: bytes) -> dict:
    try:
        preflight = _runtime._preflight_json(raw)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    if preflight == "syntax-invalid":
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_JSON_INVALID
        )
    if preflight != "valid":
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_INPUT_RESOURCE
        )
    try:
        decoded = json.loads(
            raw.decode("ascii", "strict"),
            object_pairs_hook=_runtime._unique_object,
            parse_constant=_runtime._reject_constant,
            parse_float=_runtime._reject_float,
            parse_int=_bounded_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_JSON_INVALID
        )
    try:
        status = _runtime._bounded_tree_status(decoded)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    if status == "resource-invalid":
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_INPUT_RESOURCE
        )
    if status != "valid":
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_JSON_TREE_INVALID
        )
    try:
        canonical = _runtime._encode_canonical(decoded)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    if raw != canonical:
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_CANONICAL_MISMATCH
        )
    if type(decoded) is not dict:
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_SCHEMA_INVALID
        )
    return decoded


def _validate_exact_schema(tree: dict) -> tuple:
    schema_code = (
        PortablePredicateResolverReferenceVerificationCode
        .CONTRACT_SCHEMA_INVALID
    )
    if not _exact_keys(tree, _TOP_LEVEL_FIELDS):
        _reject(schema_code)
    sources = tree["ordered_source_kind_rows"]
    authorities = tree["ordered_authority_requirement_rows"]
    locators = tree["ordered_locator_reference_rows"]
    nonclaims = tree["nonclaim_state"]
    if (
        tree["artifact_type"]
        != PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE
        or type(tree["artifact_type"]) is not str
        or tree["format_version"] != "1"
        or type(tree["format_version"]) is not str
        or not _sha256(tree["semantic_core_contract_sha256"])
        or not _identifier(tree["profile_contract_artifact_type"])
        or not _sha256(tree["profile_contract_sha256"])
        or type(sources) is not list
        or type(authorities) is not list
        or type(locators) is not list
        or not _exact_keys(nonclaims, _NONCLAIM_FIELDS)
        or any(
            type(nonclaims[field]) is not bool
            or nonclaims[field] is not False
            for field in _NONCLAIM_FIELDS
        )
    ):
        _reject(schema_code)
    if (
        len(sources) > _MAXIMUM_SOURCE_KIND_ROWS
        or len(authorities) > _MAXIMUM_AUTHORITY_ROWS
        or len(locators) > _MAXIMUM_LOCATOR_ROWS
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_INPUT_RESOURCE
        )
    for row in sources:
        if (
            not _exact_keys(row, _SOURCE_ROW_FIELDS)
            or not _identifier(row["source_artifact_kind_id"])
            or type(row["source_reference_mode_id"]) is not str
            or row["source_reference_mode_id"] not in _SOURCE_MODE_IDS
            or not _empty_or_identifier(
                row["source_snapshot_artifact_type_id"]
            )
            or not _empty_or_identifier(row["source_identity_domain_id"])
            or type(row["freshness_requirement_id"]) is not str
            or row["freshness_requirement_id"] not in _FRESHNESS_MODE_IDS
        ):
            _reject(schema_code)
    for row in authorities:
        admitted = (
            row.get("ordered_admitted_source_artifact_kind_ids")
            if type(row) is dict
            else None
        )
        if (
            not _exact_keys(row, _AUTHORITY_ROW_FIELDS)
            or not _identifier(row["authority_class_id"])
            or type(row["authority_requirement_mode_id"]) is not str
            or row["authority_requirement_mode_id"]
            not in _AUTHORITY_MODE_IDS
            or type(admitted) is not list
            or type(row["minimum_distinct_trust_subject_count"]) is not int
        ):
            _reject(schema_code)
        if any(not _identifier(item) for item in admitted):
            _reject(schema_code)
        if (
            len(admitted) > _MAXIMUM_REFERENCES_PER_ROW
            or row["minimum_distinct_trust_subject_count"]
            > _MAXIMUM_TRUST_SUBJECT_COUNT
        ):
            _reject(
                PortablePredicateResolverReferenceVerificationCode
                .CONTRACT_INPUT_RESOURCE
            )
    for row in locators:
        minimum = (
            row.get("ordered_minimum_authority_class_ids")
            if type(row) is dict
            else None
        )
        if (
            not _exact_keys(row, _LOCATOR_ROW_FIELDS)
            or not _identifier(row["locator_kind_id"])
            or type(row["locator_primitive_id"]) is not str
            or row["locator_primitive_id"] not in _LOCATOR_PRIMITIVE_IDS
            or type(row["reference_requirement_mode_id"]) is not str
            or row["reference_requirement_mode_id"]
            not in _REFERENCE_REQUIREMENT_MODE_IDS
            or not _empty_or_identifier(row["source_artifact_kind_id"])
            or type(minimum) is not list
            or not _empty_or_identifier(
                row["static_blocking_reason_id"]
            )
            or (
                row["static_blocking_reason_id"]
                not in ("", _STATIC_BLOCKING_REASON_ID)
            )
        ):
            _reject(schema_code)
        if any(not _identifier(item) for item in minimum):
            _reject(schema_code)
        if len(minimum) > _MAXIMUM_REFERENCES_PER_ROW:
            _reject(
                PortablePredicateResolverReferenceVerificationCode
                .CONTRACT_INPUT_RESOURCE
            )
    aggregate_references = (
        sum(
            len(row["ordered_admitted_source_artifact_kind_ids"])
            for row in authorities
        )
        + sum(
            len(row["ordered_minimum_authority_class_ids"])
            for row in locators
        )
        + sum(bool(row["source_artifact_kind_id"]) for row in locators)
    )
    if aggregate_references > _MAXIMUM_ROW_REFERENCES:
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_INPUT_RESOURCE
        )
    return sources, authorities, locators


def _validate_profile_binding(
    tree: dict,
    profile: object,
) -> None:
    if (
        tree["semantic_core_contract_sha256"]
        != profile.semantic_core_contract_sha256
        or tree["profile_contract_artifact_type"]
        != profile.profile_artifact_type
        or tree["profile_contract_sha256"]
        != profile.profile_contract_sha256
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_BINDING_MISMATCH
        )


def _validate_expected_identity(
    canonical: bytes,
    expected_identity: str,
) -> str:
    identity = _domain_sha256(
        PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_IDENTITY_DOMAIN,
        canonical,
    )
    if not _sha256(expected_identity) or identity != expected_identity:
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_IDENTITY_MISMATCH
        )
    return identity


def _validate_source_registry(sources: list) -> dict:
    source_code = (
        PortablePredicateResolverReferenceVerificationCode
        .SOURCE_KIND_REGISTRY_INVALID
    )
    source_ids = [row["source_artifact_kind_id"] for row in sources]
    if len(source_ids) != len(set(source_ids)):
        _reject(source_code)
    snapshot_types = []
    identity_domains = []
    for row in sources:
        mode = row["source_reference_mode_id"]
        if mode == "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED":
            if (
                not _identifier(row["source_snapshot_artifact_type_id"])
                or not _identifier(row["source_identity_domain_id"])
                or row["freshness_requirement_id"]
                not in (
                    "ARCHIVAL_IMMUTABILITY_REQUIRED",
                    "CONTEXT_BOUND_FRESHNESS_REQUIRED",
                )
            ):
                _reject(source_code)
            snapshot_types.append(
                row["source_snapshot_artifact_type_id"]
            )
            identity_domains.append(row["source_identity_domain_id"])
        elif mode == "PRIOR_SIBLING_REFERENCE_REQUIRED":
            if (
                row["source_snapshot_artifact_type_id"] != ""
                or row["source_identity_domain_id"] != ""
                or row["freshness_requirement_id"] != "NOT_APPLICABLE"
            ):
                _reject(source_code)
        else:
            _reject(source_code)
    if (
        len(snapshot_types) != len(set(snapshot_types))
        or len(identity_domains) != len(set(identity_domains))
    ):
        _reject(source_code)
    return {row["source_artifact_kind_id"]: row for row in sources}


def _validate_source_reference_closure(
    sources: list,
    locators: list,
    source_by_id: dict,
) -> None:
    referenced_source_ids = [
        row["source_artifact_kind_id"]
        for row in locators
        if row["source_artifact_kind_id"]
    ]
    if any(
        source_id not in source_by_id
        for source_id in referenced_source_ids
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .SOURCE_KIND_REGISTRY_INVALID
        )
    first_use_source_ids = []
    for source_id in referenced_source_ids:
        if source_id not in first_use_source_ids:
            first_use_source_ids.append(source_id)
    if [
        row["source_artifact_kind_id"] for row in sources
    ] != first_use_source_ids:
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .SOURCE_KIND_REGISTRY_INVALID
        )


def _validate_authority_registry(
    authorities: list,
    source_by_id: dict,
) -> dict:
    authority_code = (
        PortablePredicateResolverReferenceVerificationCode
        .AUTHORITY_REGISTRY_INVALID
    )
    authority_ids = [row["authority_class_id"] for row in authorities]
    if len(authority_ids) != len(set(authority_ids)):
        _reject(authority_code)
    source_order = {
        source_id: index for index, source_id in enumerate(source_by_id)
    }
    for row in authorities:
        admitted = row["ordered_admitted_source_artifact_kind_ids"]
        if len(admitted) != len(set(admitted)):
            _reject(authority_code)
        if any(source_id not in source_by_id for source_id in admitted):
            _reject(authority_code)
        if [source_order[source_id] for source_id in admitted] != sorted(
            source_order[source_id] for source_id in admitted
        ):
            _reject(authority_code)
        threshold = row["minimum_distinct_trust_subject_count"]
        if (
            row["authority_requirement_mode_id"]
            == "DEPLOYMENT_TRUST_REQUIRED"
        ):
            if (
                not admitted
                or threshold < 1
                or any(
                    source_by_id[source_id]["source_reference_mode_id"]
                    != "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
                    for source_id in admitted
                )
            ):
                _reject(authority_code)
        elif (
            row["authority_requirement_mode_id"]
            == "STATIC_REFERENCE_BLOCKED"
        ):
            if admitted or threshold != 0:
                _reject(authority_code)
        else:
            _reject(authority_code)
    return {row["authority_class_id"]: row for row in authorities}


def _validate_locator_registry(
    locators: list,
    source_by_id: dict,
    authority_by_id: dict,
    profile_tree: dict,
) -> None:
    locator_code = (
        PortablePredicateResolverReferenceVerificationCode
        .LOCATOR_REFERENCE_INVALID
    )
    locator_ids = [row["locator_kind_id"] for row in locators]
    if len(locator_ids) != len(set(locator_ids)):
        _reject(locator_code)
    profile_primitive_by_locator = {
        row["locator_kind_id"]: row["locator_primitive_id"]
        for row in profile_tree["locator_extension_rows"]
    }
    profile_locator_by_id = {
        row["locator_kind_id"]: row
        for row in profile_tree["locator_extension_rows"]
    }
    field_semantic_roles = {
        row["field_id"]: row["semantic_role_id"]
        for row in profile_tree["profile_field_schema_rows"]
    }
    authority_order = {
        authority_id: index
        for index, authority_id in enumerate(
            profile_tree["authority_class_ids"]
        )
    }
    for row in locators:
        if (
            row["locator_kind_id"] in profile_primitive_by_locator
            and row["locator_primitive_id"]
            != profile_primitive_by_locator[row["locator_kind_id"]]
        ):
            _reject(locator_code)
        source_id = row["source_artifact_kind_id"]
        minimum = row["ordered_minimum_authority_class_ids"]
        mode = row["reference_requirement_mode_id"]
        profile_locator = profile_locator_by_id.get(
            row["locator_kind_id"]
        )
        anchor_bearing = (
            profile_locator is not None
            and any(
                field_semantic_roles.get(field_id)
                in _ANCHOR_FIELD_SEMANTIC_ROLE_IDS
                for field_id in profile_locator[
                    "exact_configuration_field_ids"
                ]
            )
        )
        if profile_locator is not None and (
            anchor_bearing != (mode == "STATIC_REFERENCE_BLOCKED")
        ):
            _reject(locator_code)
        if len(minimum) != len(set(minimum)):
            _reject(locator_code)
        if any(authority_id not in authority_by_id for authority_id in minimum):
            _reject(locator_code)
        if any(authority_id not in authority_order for authority_id in minimum):
            _reject(locator_code)
        if [authority_order[item] for item in minimum] != sorted(
            authority_order[item] for item in minimum
        ):
            _reject(locator_code)
        if mode == "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED":
            if (
                row["locator_primitive_id"]
                not in _SOURCE_BACKED_PRIMITIVE_IDS
                or source_id not in source_by_id
                or source_by_id[source_id]["source_reference_mode_id"]
                != "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
                or row["static_blocking_reason_id"] != ""
                or not minimum
            ):
                _reject(locator_code)
            for authority_id in minimum:
                authority = authority_by_id[authority_id]
                if (
                    authority["authority_requirement_mode_id"]
                    != "DEPLOYMENT_TRUST_REQUIRED"
                    or source_id
                    not in authority[
                        "ordered_admitted_source_artifact_kind_ids"
                    ]
                ):
                    _reject(locator_code)
        elif mode == "PRIOR_SIBLING_REFERENCE_REQUIRED":
            if (
                row["locator_primitive_id"] != "sibling-resolved-value"
                or source_id not in source_by_id
                or source_by_id[source_id]["source_reference_mode_id"]
                != "PRIOR_SIBLING_REFERENCE_REQUIRED"
                or minimum
                or row["static_blocking_reason_id"] != ""
            ):
                _reject(locator_code)
        elif mode == "STATIC_REFERENCE_BLOCKED":
            if (
                source_id != ""
                or minimum
                or row["static_blocking_reason_id"]
                != _STATIC_BLOCKING_REASON_ID
            ):
                _reject(locator_code)
        else:
            _reject(locator_code)


def _validate_profile_coverage_and_closure(
    authorities: list,
    locators: list,
    profile_tree: dict,
) -> None:
    coverage_code = (
        PortablePredicateResolverReferenceVerificationCode
        .PROFILE_COVERAGE_MISMATCH
    )
    if [
        row["authority_class_id"] for row in authorities
    ] != profile_tree["authority_class_ids"]:
        _reject(coverage_code)
    profile_locators = profile_tree["locator_extension_rows"]
    if [
        (row["locator_kind_id"], row["locator_primitive_id"])
        for row in locators
    ] != [
        (row["locator_kind_id"], row["locator_primitive_id"])
        for row in profile_locators
    ]:
        _reject(coverage_code)



def _validate_namespace(
    sources: list,
    profile_tree: dict,
) -> None:
    source_kind_ids = {
        row["source_artifact_kind_id"] for row in sources
    }
    snapshot_types = {
        row["source_snapshot_artifact_type_id"]
        for row in sources
        if row["source_reference_mode_id"]
        == "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
    }
    identity_domains = {
        row["source_identity_domain_id"]
        for row in sources
        if row["source_reference_mode_id"]
        == "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
    }
    authority_ids = set(profile_tree["authority_class_ids"])
    locator_ids = {
        row["locator_kind_id"]
        for row in profile_tree["locator_extension_rows"]
    }
    try:
        interface = (
            _core
            .portable_predicate_language_core_verifier_profile_interface_tree()
        )
        profile_artifact_namespaces = {
            namespace
            for row in profile_tree["artifact_domain_rows"]
            for namespace in (
                row["artifact_type_id"],
                row["digest_domain_id"],
            )
        }
        profile_anchor_artifact_namespaces = {
            row["artifact_type_id"]
            for row in profile_tree["anchor_contract_rows"]
        }
        profile_and_meta_namespaces = (
            profile_artifact_namespaces
            | profile_anchor_artifact_namespaces
            | {
            profile_tree["artifact_type"],
            profile_tree["profile_verification_result_artifact_type"],
            *interface["reserved_core_metadata_artifact_type_ids"],
            }
        )
        quarantine_namespaces = {
            (
                _quarantine
                .PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE
            ),
            (
                _quarantine
                .PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN
            ),
        }
    except (
        AttributeError,
        IndexError,
        KeyError,
        TypeError,
        _core.PortablePredicateLanguageCoreVerificationError,
    ):
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
    reference_namespaces = {
        PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE,
        PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_IDENTITY_DOMAIN,
    }
    framework_sets = (
        quarantine_namespaces,
        reference_namespaces,
        profile_and_meta_namespaces,
    )
    new_reference_sets = (
        source_kind_ids,
        snapshot_types,
        identity_domains,
    )
    profile_registry_ids = authority_ids | locator_ids
    framework_reserved = set().union(*framework_sets)
    framework_collision = any(
        left.intersection(right)
        for index, left in enumerate(framework_sets)
        for right in framework_sets[index + 1 :]
    )
    new_reference_collision = any(
        left.intersection(right)
        for index, left in enumerate(new_reference_sets)
        for right in new_reference_sets[index + 1 :]
    )
    if (
        framework_collision
        or new_reference_collision
        or any(
            namespace_set.intersection(
                framework_reserved | profile_registry_ids
            )
            for namespace_set in new_reference_sets
        )
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .NAMESPACE_COLLISION
        )


def _result_inventory(
    sources: list,
    authorities: list,
    locators: list,
) -> tuple:
    source_bindings = tuple(
        (
            row["source_artifact_kind_id"],
            row["source_reference_mode_id"],
            row["source_snapshot_artifact_type_id"],
            row["source_identity_domain_id"],
            row["freshness_requirement_id"],
        )
        for row in sources
    )
    authority_bindings = tuple(
        (
            row["authority_class_id"],
            row["authority_requirement_mode_id"],
            tuple(row["ordered_admitted_source_artifact_kind_ids"]),
            row["minimum_distinct_trust_subject_count"],
        )
        for row in authorities
    )
    locator_reference_bindings = tuple(
        (
            row["locator_kind_id"],
            row["locator_primitive_id"],
            row["reference_requirement_mode_id"],
            row["source_artifact_kind_id"],
            tuple(row["ordered_minimum_authority_class_ids"]),
            row["static_blocking_reason_id"],
        )
        for row in locators
    )
    return (
        source_bindings,
        authority_bindings,
        locator_reference_bindings,
    )


def _validate_result(
    result: VerifiedPortablePredicateResolverReferenceV1,
    *,
    expected_contract: bytes,
    expected_identity: str,
    expected_semantic_core_contract_sha256: str,
    expected_profile_contract_artifact_type: str,
    expected_profile_contract_sha256: str,
    source_bindings: tuple,
    authority_bindings: tuple,
    locator_reference_bindings: tuple,
) -> VerifiedPortablePredicateResolverReferenceV1:
    if type(result) is not VerifiedPortablePredicateResolverReferenceV1:
        _reject(
            PortablePredicateResolverReferenceVerificationCode.RESULT_INVALID
        )
    expected_types = (
        bytes,
        str,
        str,
        int,
        str,
        str,
        str,
        tuple,
        tuple,
        tuple,
        int,
        int,
        int,
        str,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
    )
    try:
        values = tuple(
            getattr(result, field_id)
            for field_id in result.__slots__
        )
    except (AttributeError, TypeError):
        _reject(
            PortablePredicateResolverReferenceVerificationCode.RESULT_INVALID
        )
    if (
        len(values) != len(expected_types)
        or any(
            type(value) is not expected_type
            for value, expected_type in zip(values, expected_types)
        )
        or any(
            type(row) is not tuple
            or len(row) != 5
            or any(type(item) is not str for item in row)
            for row in result.source_kind_bindings
        )
        or any(
            type(row) is not tuple
            or len(row) != 4
            or type(row[0]) is not str
            or type(row[1]) is not str
            or type(row[2]) is not tuple
            or any(type(item) is not str for item in row[2])
            or type(row[3]) is not int
            for row in result.authority_requirement_bindings
        )
        or any(
            type(row) is not tuple
            or len(row) != 6
            or any(
                type(row[index]) is not str
                for index in (0, 1, 2, 3, 5)
            )
            or type(row[4]) is not tuple
            or any(type(item) is not str for item in row[4])
            for row in result.locator_reference_bindings
        )
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode.RESULT_INVALID
        )
    if (
        result.canonical_contract_bytes != expected_contract
        or result.contract_artifact_type
        != PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE
        or result.contract_identity_sha256 != expected_identity
        or result.contract_byte_count != len(expected_contract)
        or result.semantic_core_contract_sha256
        != expected_semantic_core_contract_sha256
        or result.profile_contract_artifact_type
        != expected_profile_contract_artifact_type
        or result.profile_contract_sha256
        != expected_profile_contract_sha256
        or result.source_kind_bindings != source_bindings
        or result.authority_requirement_bindings != authority_bindings
        or result.locator_reference_bindings
        != locator_reference_bindings
        or result.snapshot_authentication_required_locator_count
        != sum(
            row[2] == "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED"
            for row in locator_reference_bindings
        )
        or result.prior_sibling_reference_required_locator_count
        != sum(
            row[2] == "PRIOR_SIBLING_REFERENCE_REQUIRED"
            for row in locator_reference_bindings
        )
        or result.statically_blocked_locator_count
        != sum(
            row[2] == "STATIC_REFERENCE_BLOCKED"
            for row in locator_reference_bindings
        )
        or result.validation_scope_id
        != PORTABLE_PREDICATE_RESOLVER_REFERENCE_VALIDATION_SCOPE_ID
        or result.profile_locator_coverage_complete is not True
        or result.profile_authority_coverage_complete is not True
        or result.static_reference_closure_validated is not True
        or result.source_artifacts_validated is not False
        or result.authority_credentials_validated is not False
        or result.deployment_trust_bound is not False
        or result.resolver_executed is not False
        or result.official_input_bundle_constructed is not False
        or result.source_snapshot_schema_validated is not False
        or result.typed_leaf_binding_validated is not False
        or result.locator_interpreter_defined is not False
        or result.program_resolution_compatibility_validated is not False
        or result.resolver_outcomes_derived is not False
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode.RESULT_INVALID
        )
    return result


def _verify(
    resolver_reference_contract_bytes: object,
    *,
    compiled_profile: object,
    expected_resolver_reference_contract_sha256: object,
) -> VerifiedPortablePredicateResolverReferenceV1:
    if (
        type(resolver_reference_contract_bytes) is not bytes
        or type(expected_resolver_reference_contract_sha256) is not str
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode.INPUT_TYPE
        )
    profile = _revalidate_profile(compiled_profile)
    if (
        not resolver_reference_contract_bytes
        or len(resolver_reference_contract_bytes)
        > _MAXIMUM_CONTRACT_BYTES
    ):
        _reject(
            PortablePredicateResolverReferenceVerificationCode
            .CONTRACT_INPUT_RESOURCE
        )
    profile_tree = _decode_trusted_profile(profile)
    tree = _decode_contract(resolver_reference_contract_bytes)
    sources, authorities, locators = _validate_exact_schema(tree)
    _validate_profile_binding(tree, profile)
    identity = _validate_expected_identity(
        resolver_reference_contract_bytes,
        expected_resolver_reference_contract_sha256,
    )
    source_by_id = _validate_source_registry(sources)
    _validate_source_reference_closure(
        sources,
        locators,
        source_by_id,
    )
    authority_by_id = _validate_authority_registry(
        authorities,
        source_by_id,
    )
    _validate_locator_registry(
        locators,
        source_by_id,
        authority_by_id,
        profile_tree,
    )
    _validate_profile_coverage_and_closure(
        authorities,
        locators,
        profile_tree,
    )
    _validate_namespace(sources, profile_tree)
    source_bindings, authority_bindings, locator_reference_bindings = (
        _result_inventory(sources, authorities, locators)
    )
    result = VerifiedPortablePredicateResolverReferenceV1(
        canonical_contract_bytes=resolver_reference_contract_bytes,
        contract_artifact_type=(
            PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE
        ),
        contract_identity_sha256=identity,
        contract_byte_count=len(resolver_reference_contract_bytes),
        semantic_core_contract_sha256=(
            tree["semantic_core_contract_sha256"]
        ),
        profile_contract_artifact_type=(
            tree["profile_contract_artifact_type"]
        ),
        profile_contract_sha256=tree["profile_contract_sha256"],
        source_kind_bindings=source_bindings,
        authority_requirement_bindings=authority_bindings,
        locator_reference_bindings=locator_reference_bindings,
        snapshot_authentication_required_locator_count=sum(
            row["reference_requirement_mode_id"]
            == "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED"
            for row in locators
        ),
        prior_sibling_reference_required_locator_count=sum(
            row["reference_requirement_mode_id"]
            == "PRIOR_SIBLING_REFERENCE_REQUIRED"
            for row in locators
        ),
        statically_blocked_locator_count=sum(
            row["reference_requirement_mode_id"]
            == "STATIC_REFERENCE_BLOCKED"
            for row in locators
        ),
        validation_scope_id=(
            PORTABLE_PREDICATE_RESOLVER_REFERENCE_VALIDATION_SCOPE_ID
        ),
        profile_locator_coverage_complete=True,
        profile_authority_coverage_complete=True,
        static_reference_closure_validated=True,
        source_artifacts_validated=False,
        authority_credentials_validated=False,
        deployment_trust_bound=False,
        resolver_executed=False,
        official_input_bundle_constructed=False,
        source_snapshot_schema_validated=False,
        typed_leaf_binding_validated=False,
        locator_interpreter_defined=False,
        program_resolution_compatibility_validated=False,
        resolver_outcomes_derived=False,
    )
    return _validate_result(
        result,
        expected_contract=resolver_reference_contract_bytes,
        expected_identity=identity,
        expected_semantic_core_contract_sha256=(
            tree["semantic_core_contract_sha256"]
        ),
        expected_profile_contract_artifact_type=(
            tree["profile_contract_artifact_type"]
        ),
        expected_profile_contract_sha256=tree["profile_contract_sha256"],
        source_bindings=source_bindings,
        authority_bindings=authority_bindings,
        locator_reference_bindings=locator_reference_bindings,
    )


def verify_portable_predicate_resolver_reference_contract_v1(
    resolver_reference_contract_bytes: bytes,
    *,
    compiled_profile: object,
    expected_resolver_reference_contract_sha256: str,
) -> VerifiedPortablePredicateResolverReferenceV1:
    """Independently verify one canonical static resolver-reference sidecar.

    The expected identity is only an exact caller-supplied consistency pin.
    Acceptance authenticates no deployment root, source, credential, or
    resolver evidence and constructs no official input bundle.
    """

    try:
        return _verify(
            resolver_reference_contract_bytes,
            compiled_profile=compiled_profile,
            expected_resolver_reference_contract_sha256=(
                expected_resolver_reference_contract_sha256
            ),
        )
    except PortablePredicateResolverReferenceVerificationError:
        raise
    except (MemoryError, KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        _reject(PortablePredicateResolverReferenceVerificationCode.INTERNAL)
