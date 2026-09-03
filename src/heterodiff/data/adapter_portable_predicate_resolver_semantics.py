"""Compile one profile-bound portable-predicate resolver-reference contract.

Checkpoint 56E closes only a canonical static inventory of source references,
authority requirements, and locator references against one completely
revalidated selected profile.  It does not interpret a locator, validate a
source schema or typed-leaf binding, derive a resolver outcome, or construct
an official input bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Final

from heterodiff.data import (
    adapter_portable_predicate_context_input as _context_input,
)
from heterodiff.data import (
    adapter_portable_predicate_language_core as _core,
)
from heterodiff.data import (
    adapter_portable_predicate_runtime_artifacts as _runtime,
)


__all__ = (
    "PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_IDENTITY_DOMAIN",
    "PORTABLE_PREDICATE_RESOLVER_REFERENCE_VALIDATION_SCOPE_ID",
    "PortablePredicateResolverReferenceCode",
    "PortablePredicateResolverReferenceError",
    "CompiledPortablePredicateResolverReferenceV1",
    "compile_portable_predicate_resolver_reference_contract_v1",
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
_MAXIMUM_IDENTIFIER_BYTES: Final = 512
_MAXIMUM_SOURCE_ROWS: Final = 256
_MAXIMUM_AUTHORITY_ROWS: Final = 256
_MAXIMUM_LOCATOR_ROWS: Final = 256
_MAXIMUM_REFERENCES_PER_ROW: Final = 256
_MAXIMUM_AGGREGATE_REFERENCES: Final = 65536
_MAXIMUM_TRUST_SUBJECTS: Final = 32

_IDENTIFIER_RE: Final = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$"
)
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")

_SOURCE_MODE_IDS: Final = frozenset(
    {
        "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED",
        "PRIOR_SIBLING_REFERENCE_REQUIRED",
    }
)
_FRESHNESS_MODE_IDS: Final = frozenset(
    {
        "ARCHIVAL_IMMUTABILITY_REQUIRED",
        "CONTEXT_BOUND_FRESHNESS_REQUIRED",
        "NOT_APPLICABLE",
    }
)
_AUTHORITY_MODE_IDS: Final = frozenset(
    {
        "DEPLOYMENT_TRUST_REQUIRED",
        "STATIC_REFERENCE_BLOCKED",
    }
)
_REFERENCE_REQUIREMENT_MODE_IDS: Final = frozenset(
    {
        "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED",
        "PRIOR_SIBLING_REFERENCE_REQUIRED",
        "STATIC_REFERENCE_BLOCKED",
    }
)
_LOCATOR_PRIMITIVE_IDS: Final = frozenset(
    {
        "bounded-artifact-path",
        "direct-bound-value",
        "ordered-index",
        "composite-key",
        "sibling-resolved-value",
    }
)
_SOURCE_BACKED_PRIMITIVE_IDS: Final = frozenset(
    {
        "bounded-artifact-path",
        "direct-bound-value",
        "ordered-index",
        "composite-key",
    }
)
_STATIC_BLOCKING_REASON_ID: Final = (
    "OPAQUE_ANCHOR_CONTRACT_NOT_INTERPRETED"
)
_ANCHOR_FIELD_SEMANTIC_ROLE_IDS: Final = frozenset(
    {
        "anchor-artifact-type-for-role",
        "anchor-contract-sha256-for-role",
    }
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


class PortablePredicateResolverReferenceCode(str, Enum):
    """Closed ordinary failures for the Checkpoint-56E compiler."""

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
        "portable predicate resolver reference "
        + code.value.lower().replace("_", " ")
    )
    for code in PortablePredicateResolverReferenceCode
}


class PortablePredicateResolverReferenceError(ValueError):
    """One fixed-message Checkpoint-56E compilation failure."""

    def __init__(self, code: PortablePredicateResolverReferenceCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True, repr=False)
class CompiledPortablePredicateResolverReferenceV1:
    """Immutable receipt for one statically validated 56E sidecar."""

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
            "CompiledPortablePredicateResolverReferenceV1("
            f"contract_identity_sha256={self.contract_identity_sha256!r}, "
            f"contract_byte_count={self.contract_byte_count!r}, "
            f"validation_scope_id={self.validation_scope_id!r})"
        )


class _DuplicateKeyError(ValueError):
    pass


def _reject(code: PortablePredicateResolverReferenceCode) -> None:
    raise PortablePredicateResolverReferenceError(code) from None


def _object_without_duplicates(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_json_constant(_: str) -> None:
    raise ValueError


def _reject_json_float(_: str) -> None:
    raise ValueError


def _bounded_json_integer(value: str) -> int:
    if len(value.lstrip("-")) > 20:
        raise ValueError
    return int(value)


def _is_identifier(value: object) -> bool:
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


def _is_empty_or_identifier(value: object) -> bool:
    return type(value) is str and (
        value == "" or _is_identifier(value)
    )


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and _SHA256_RE.fullmatch(value) is not None
    )


def _exact_keys(value: object, fields: tuple) -> bool:
    return type(value) is dict and set(value) == set(fields)


def _canonical_json(value: object) -> bytes:
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _reject(PortablePredicateResolverReferenceCode.INTERNAL)
    if len(result) > _MAXIMUM_CONTRACT_BYTES:
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_INPUT_RESOURCE
        )
    return result


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii", "strict"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _strict_contract_json(value: bytes) -> object:
    if not value or len(value) > _MAXIMUM_CONTRACT_BYTES:
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_INPUT_RESOURCE
        )
    preflight = _runtime._bounded_json_preflight_status(value)
    if preflight == "syntax-invalid":
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_JSON_INVALID
        )
    if preflight != "valid":
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_INPUT_RESOURCE
        )
    try:
        decoded = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_json_constant,
            parse_float=_reject_json_float,
            parse_int=_bounded_json_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_JSON_INVALID
        )
    status = _runtime._bounded_exact_json_status(decoded)
    if status == "resource-invalid":
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_INPUT_RESOURCE
        )
    if status != "valid":
        _reject(
            PortablePredicateResolverReferenceCode
            .CONTRACT_JSON_TREE_INVALID
        )
    return decoded


def _revalidate_profile(compiled_profile: object) -> object:
    failure_code = None
    try:
        profile = _runtime._revalidate_compiled_profile(compiled_profile)
    except _runtime.PortablePredicateRuntimeEnvelopeError as error:
        failure_code = error.code
    if failure_code == (
        _runtime.PortablePredicateRuntimeEnvelopeCode.INTERNAL.value
    ):
        _reject(PortablePredicateResolverReferenceCode.INTERNAL)
    if failure_code is not None:
        _reject(
            PortablePredicateResolverReferenceCode.COMPILED_PROFILE_INVALID
        )
    return profile


def _trusted_profile_tree(profile: object) -> dict:
    try:
        tree = json.loads(
            profile.canonical_profile_bytes.decode("ascii", "strict")
        )
    except (AttributeError, UnicodeError, ValueError, TypeError):
        _reject(PortablePredicateResolverReferenceCode.INTERNAL)
    if type(tree) is not dict:
        _reject(PortablePredicateResolverReferenceCode.INTERNAL)
    return tree


def _validate_schema(tree: object) -> tuple:
    code = PortablePredicateResolverReferenceCode.CONTRACT_SCHEMA_INVALID
    if not _exact_keys(tree, _TOP_LEVEL_FIELDS):
        _reject(code)
    if (
        tree["artifact_type"]
        != PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE
        or type(tree["format_version"]) is not str
        or tree["format_version"] != "1"
        or not _is_sha256(tree["semantic_core_contract_sha256"])
        or not _is_identifier(tree["profile_contract_artifact_type"])
        or not _is_sha256(tree["profile_contract_sha256"])
        or type(tree["ordered_source_kind_rows"]) is not list
        or type(tree["ordered_authority_requirement_rows"]) is not list
        or type(tree["ordered_locator_reference_rows"]) is not list
        or not _exact_keys(tree["nonclaim_state"], _NONCLAIM_FIELDS)
        or any(
            type(tree["nonclaim_state"][field]) is not bool
            or tree["nonclaim_state"][field] is not False
            for field in _NONCLAIM_FIELDS
        )
    ):
        _reject(code)

    source_rows = tree["ordered_source_kind_rows"]
    authority_rows = tree["ordered_authority_requirement_rows"]
    locator_rows = tree["ordered_locator_reference_rows"]
    if (
        len(source_rows) > _MAXIMUM_SOURCE_ROWS
        or len(authority_rows) > _MAXIMUM_AUTHORITY_ROWS
        or len(locator_rows) > _MAXIMUM_LOCATOR_ROWS
    ):
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_INPUT_RESOURCE
        )

    for row in source_rows:
        if (
            not _exact_keys(row, _SOURCE_ROW_FIELDS)
            or not _is_identifier(row["source_artifact_kind_id"])
            or type(row["source_reference_mode_id"]) is not str
            or row["source_reference_mode_id"] not in _SOURCE_MODE_IDS
            or not _is_empty_or_identifier(
                row["source_snapshot_artifact_type_id"]
            )
            or not _is_empty_or_identifier(
                row["source_identity_domain_id"]
            )
            or type(row["freshness_requirement_id"]) is not str
            or row["freshness_requirement_id"] not in _FRESHNESS_MODE_IDS
        ):
            _reject(code)

    aggregate_references = 0
    for row in authority_rows:
        admitted = row.get(
            "ordered_admitted_source_artifact_kind_ids"
        ) if type(row) is dict else None
        if (
            not _exact_keys(row, _AUTHORITY_ROW_FIELDS)
            or not _is_identifier(row["authority_class_id"])
            or type(row["authority_requirement_mode_id"]) is not str
            or row["authority_requirement_mode_id"]
            not in _AUTHORITY_MODE_IDS
            or type(admitted) is not list
            or any(not _is_identifier(item) for item in admitted)
            or type(row["minimum_distinct_trust_subject_count"]) is not int
        ):
            _reject(code)
        if (
            len(admitted) > _MAXIMUM_REFERENCES_PER_ROW
            or row["minimum_distinct_trust_subject_count"]
            > _MAXIMUM_TRUST_SUBJECTS
        ):
            _reject(
                PortablePredicateResolverReferenceCode
                .CONTRACT_INPUT_RESOURCE
            )
        aggregate_references += len(admitted)

    for row in locator_rows:
        authorities = row.get(
            "ordered_minimum_authority_class_ids"
        ) if type(row) is dict else None
        if (
            not _exact_keys(row, _LOCATOR_ROW_FIELDS)
            or not _is_identifier(row["locator_kind_id"])
            or type(row["locator_primitive_id"]) is not str
            or row["locator_primitive_id"] not in _LOCATOR_PRIMITIVE_IDS
            or type(row["reference_requirement_mode_id"]) is not str
            or row["reference_requirement_mode_id"]
            not in _REFERENCE_REQUIREMENT_MODE_IDS
            or not _is_empty_or_identifier(
                row["source_artifact_kind_id"]
            )
            or type(authorities) is not list
            or any(not _is_identifier(item) for item in authorities)
            or not _is_empty_or_identifier(
                row["static_blocking_reason_id"]
            )
            or row["static_blocking_reason_id"]
            not in ("", _STATIC_BLOCKING_REASON_ID)
        ):
            _reject(code)
        if len(authorities) > _MAXIMUM_REFERENCES_PER_ROW:
            _reject(
                PortablePredicateResolverReferenceCode
                .CONTRACT_INPUT_RESOURCE
            )
        aggregate_references += len(authorities)
        aggregate_references += bool(row["source_artifact_kind_id"])

    if aggregate_references > _MAXIMUM_AGGREGATE_REFERENCES:
        _reject(
            PortablePredicateResolverReferenceCode.CONTRACT_INPUT_RESOURCE
        )
    return source_rows, authority_rows, locator_rows


def _indices_in_registry_order(values: list, registry_ids: tuple) -> bool:
    positions = {value: index for index, value in enumerate(registry_ids)}
    if any(value not in positions for value in values):
        return False
    indices = [positions[value] for value in values]
    return indices == sorted(indices) and len(indices) == len(set(indices))


def _validate_source_registry(
    source_rows: list,
    locator_rows: list,
) -> tuple:
    code = PortablePredicateResolverReferenceCode.SOURCE_KIND_REGISTRY_INVALID
    source_ids = tuple(row["source_artifact_kind_id"] for row in source_rows)
    if len(source_ids) != len(set(source_ids)):
        _reject(code)

    snapshot_types = []
    identity_domains = []
    for row in source_rows:
        if (
            row["source_reference_mode_id"]
            == "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
        ):
            if (
                not row["source_snapshot_artifact_type_id"]
                or not row["source_identity_domain_id"]
                or row["freshness_requirement_id"]
                not in {
                    "ARCHIVAL_IMMUTABILITY_REQUIRED",
                    "CONTEXT_BOUND_FRESHNESS_REQUIRED",
                }
            ):
                _reject(code)
            snapshot_types.append(
                row["source_snapshot_artifact_type_id"]
            )
            identity_domains.append(row["source_identity_domain_id"])
        elif (
            row["source_snapshot_artifact_type_id"] != ""
            or row["source_identity_domain_id"] != ""
            or row["freshness_requirement_id"] != "NOT_APPLICABLE"
        ):
            _reject(code)
    if (
        len(snapshot_types) != len(set(snapshot_types))
        or len(identity_domains) != len(set(identity_domains))
    ):
        _reject(code)

    first_use = []
    seen = set()
    for row in locator_rows:
        source_id = row["source_artifact_kind_id"]
        if source_id and source_id not in seen:
            first_use.append(source_id)
            seen.add(source_id)
    if any(source_id not in source_ids for source_id in first_use):
        _reject(code)
    if tuple(first_use) != source_ids:
        _reject(code)
    return source_ids


def _validate_authority_registry(
    authority_rows: list,
    source_rows: list,
    source_ids: tuple,
) -> tuple:
    code = PortablePredicateResolverReferenceCode.AUTHORITY_REGISTRY_INVALID
    authority_ids = tuple(
        row["authority_class_id"] for row in authority_rows
    )
    if len(authority_ids) != len(set(authority_ids)):
        _reject(code)
    source_by_id = {
        row["source_artifact_kind_id"]: row for row in source_rows
    }
    for row in authority_rows:
        admitted = row["ordered_admitted_source_artifact_kind_ids"]
        threshold = row["minimum_distinct_trust_subject_count"]
        if (
            row["authority_requirement_mode_id"]
            == "DEPLOYMENT_TRUST_REQUIRED"
        ):
            if (
                not admitted
                or not _indices_in_registry_order(admitted, source_ids)
                or not (1 <= threshold <= _MAXIMUM_TRUST_SUBJECTS)
                or any(
                    source_by_id[source_id]["source_reference_mode_id"]
                    != "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
                    for source_id in admitted
                )
            ):
                _reject(code)
        elif admitted or threshold != 0:
            _reject(code)
    return authority_ids


def _validate_locator_registry(
    locator_rows: list,
    *,
    source_rows: list,
    authority_rows: list,
    profile_tree: dict,
) -> tuple:
    code = PortablePredicateResolverReferenceCode.LOCATOR_REFERENCE_INVALID
    locator_ids = tuple(row["locator_kind_id"] for row in locator_rows)
    if len(locator_ids) != len(set(locator_ids)):
        _reject(code)

    source_by_id = {
        row["source_artifact_kind_id"]: row for row in source_rows
    }
    authority_by_id = {
        row["authority_class_id"]: row for row in authority_rows
    }
    profile_authority_ids = tuple(profile_tree["authority_class_ids"])
    profile_locator_by_id = {
        row["locator_kind_id"]: row
        for row in profile_tree["locator_extension_rows"]
    }
    field_role_by_id = {
        row["field_id"]: row["semantic_role_id"]
        for row in profile_tree["profile_field_schema_rows"]
    }

    for row in locator_rows:
        locator_id = row["locator_kind_id"]
        profile_locator = profile_locator_by_id.get(locator_id)
        if (
            profile_locator is not None
            and row["locator_primitive_id"]
            != profile_locator["locator_primitive_id"]
        ):
            _reject(code)

        source_id = row["source_artifact_kind_id"]
        authorities = row["ordered_minimum_authority_class_ids"]
        blocking_reason = row["static_blocking_reason_id"]
        mode = row["reference_requirement_mode_id"]
        anchor_bearing = (
            profile_locator is not None
            and any(
                field_role_by_id.get(field_id)
                in _ANCHOR_FIELD_SEMANTIC_ROLE_IDS
                for field_id in profile_locator[
                    "exact_configuration_field_ids"
                ]
            )
        )
        if profile_locator is not None and (
            anchor_bearing != (mode == "STATIC_REFERENCE_BLOCKED")
        ):
            _reject(code)
        if mode == "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED":
            if (
                row["locator_primitive_id"]
                not in _SOURCE_BACKED_PRIMITIVE_IDS
                or source_id not in source_by_id
                or source_by_id[source_id]["source_reference_mode_id"]
                != "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
                or blocking_reason != ""
                or not authorities
                or not _indices_in_registry_order(
                    authorities,
                    profile_authority_ids,
                )
                or any(
                    authority_id not in authority_by_id
                    or authority_by_id[authority_id][
                        "authority_requirement_mode_id"
                    ]
                    != "DEPLOYMENT_TRUST_REQUIRED"
                    or source_id
                    not in authority_by_id[authority_id][
                        "ordered_admitted_source_artifact_kind_ids"
                    ]
                    for authority_id in authorities
                )
            ):
                _reject(code)
        elif mode == "PRIOR_SIBLING_REFERENCE_REQUIRED":
            if (
                row["locator_primitive_id"]
                != "sibling-resolved-value"
                or source_id not in source_by_id
                or source_by_id[source_id]["source_reference_mode_id"]
                != "PRIOR_SIBLING_REFERENCE_REQUIRED"
                or authorities
                or blocking_reason != ""
            ):
                _reject(code)
        elif (
            source_id != ""
            or authorities
            or blocking_reason != _STATIC_BLOCKING_REASON_ID
        ):
            _reject(code)
    return locator_ids


def _validate_profile_coverage(
    *,
    authority_ids: tuple,
    locator_ids: tuple,
    profile_tree: dict,
) -> None:
    profile_authorities = tuple(profile_tree["authority_class_ids"])
    profile_locators = tuple(
        row["locator_kind_id"]
        for row in profile_tree["locator_extension_rows"]
    )
    if (
        authority_ids != profile_authorities
        or locator_ids != profile_locators
    ):
        _reject(
            PortablePredicateResolverReferenceCode
            .PROFILE_COVERAGE_MISMATCH
        )


def _validate_namespaces(
    source_rows: list,
    profile_tree: dict,
) -> None:
    source_kind_ids = {
        row["source_artifact_kind_id"] for row in source_rows
    }
    snapshot_types = {
        row["source_snapshot_artifact_type_id"]
        for row in source_rows
        if row["source_reference_mode_id"]
        == "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
    }
    identity_domains = {
        row["source_identity_domain_id"]
        for row in source_rows
        if row["source_reference_mode_id"]
        == "NORMALIZED_SNAPSHOT_AUTHENTICATION_REQUIRED"
    }
    authority_ids = set(profile_tree["authority_class_ids"])
    locator_ids = {
        row["locator_kind_id"]
        for row in profile_tree["locator_extension_rows"]
    }
    interface = (
        _core.portable_predicate_language_core_profile_interface_tree()
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
            _context_input
            .PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE
        ),
        (
            _context_input
            .PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN
        ),
    }
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
            PortablePredicateResolverReferenceCode.NAMESPACE_COLLISION
        )


def _binding_tuples(
    source_rows: list,
    authority_rows: list,
    locator_rows: list,
) -> tuple:
    source_bindings = tuple(
        (
            row["source_artifact_kind_id"],
            row["source_reference_mode_id"],
            row["source_snapshot_artifact_type_id"],
            row["source_identity_domain_id"],
            row["freshness_requirement_id"],
        )
        for row in source_rows
    )
    authority_bindings = tuple(
        (
            row["authority_class_id"],
            row["authority_requirement_mode_id"],
            tuple(row["ordered_admitted_source_artifact_kind_ids"]),
            row["minimum_distinct_trust_subject_count"],
        )
        for row in authority_rows
    )
    locator_bindings = tuple(
        (
            row["locator_kind_id"],
            row["locator_primitive_id"],
            row["reference_requirement_mode_id"],
            row["source_artifact_kind_id"],
            tuple(row["ordered_minimum_authority_class_ids"]),
            row["static_blocking_reason_id"],
        )
        for row in locator_rows
    )
    return source_bindings, authority_bindings, locator_bindings


def _validate_result(
    result: CompiledPortablePredicateResolverReferenceV1,
    *,
    expected_contract: bytes,
    expected_identity: str,
    expected_semantic_core_contract_sha256: str,
    expected_profile_contract_artifact_type: str,
    expected_profile_contract_sha256: str,
    expected_source_bindings: tuple,
    expected_authority_bindings: tuple,
    expected_locator_reference_bindings: tuple,
) -> CompiledPortablePredicateResolverReferenceV1:
    code = PortablePredicateResolverReferenceCode.RESULT_INVALID
    if type(result) is not CompiledPortablePredicateResolverReferenceV1:
        _reject(code)
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
            getattr(result, field_id) for field_id in result.__slots__
        )
    except (AttributeError, TypeError):
        _reject(code)
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
            or any(type(row[index]) is not str for index in (0, 1, 2, 3, 5))
            or type(row[4]) is not tuple
            or any(type(item) is not str for item in row[4])
            for row in result.locator_reference_bindings
        )
    ):
        _reject(code)
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
        or result.source_kind_bindings != expected_source_bindings
        or result.authority_requirement_bindings
        != expected_authority_bindings
        or result.locator_reference_bindings
        != expected_locator_reference_bindings
        or result.snapshot_authentication_required_locator_count
        != sum(
            row[2] == "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED"
            for row in expected_locator_reference_bindings
        )
        or result.prior_sibling_reference_required_locator_count
        != sum(
            row[2] == "PRIOR_SIBLING_REFERENCE_REQUIRED"
            for row in expected_locator_reference_bindings
        )
        or result.statically_blocked_locator_count
        != sum(
            row[2] == "STATIC_REFERENCE_BLOCKED"
            for row in expected_locator_reference_bindings
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
        _reject(code)
    return result


def _compile(
    contract_bytes: bytes,
    *,
    compiled_profile: object,
    expected_identity: str,
) -> CompiledPortablePredicateResolverReferenceV1:
    profile = _revalidate_profile(compiled_profile)
    profile_tree = _trusted_profile_tree(profile)
    decoded = _strict_contract_json(contract_bytes)
    canonical = _canonical_json(decoded)
    if canonical != contract_bytes:
        _reject(
            PortablePredicateResolverReferenceCode
            .CONTRACT_CANONICAL_MISMATCH
        )
    source_rows, authority_rows, locator_rows = _validate_schema(decoded)
    if (
        decoded["semantic_core_contract_sha256"]
        != profile.semantic_core_contract_sha256
        or decoded["profile_contract_artifact_type"]
        != profile.profile_artifact_type
        or decoded["profile_contract_sha256"]
        != profile.profile_contract_sha256
    ):
        _reject(
            PortablePredicateResolverReferenceCode
            .CONTRACT_BINDING_MISMATCH
        )
    identity = _domain_sha256(
        PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_IDENTITY_DOMAIN,
        canonical,
    )
    if not _is_sha256(expected_identity) or identity != expected_identity:
        _reject(
            PortablePredicateResolverReferenceCode
            .CONTRACT_IDENTITY_MISMATCH
        )

    source_ids = _validate_source_registry(source_rows, locator_rows)
    authority_ids = _validate_authority_registry(
        authority_rows,
        source_rows,
        source_ids,
    )
    locator_ids = _validate_locator_registry(
        locator_rows,
        source_rows=source_rows,
        authority_rows=authority_rows,
        profile_tree=profile_tree,
    )
    _validate_profile_coverage(
        authority_ids=authority_ids,
        locator_ids=locator_ids,
        profile_tree=profile_tree,
    )
    _validate_namespaces(source_rows, profile_tree)

    source_bindings, authority_bindings, locator_reference_bindings = (
        _binding_tuples(source_rows, authority_rows, locator_rows)
    )
    modes = tuple(row[2] for row in locator_reference_bindings)
    result = CompiledPortablePredicateResolverReferenceV1(
        canonical_contract_bytes=canonical,
        contract_artifact_type=(
            PORTABLE_PREDICATE_RESOLVER_REFERENCE_CONTRACT_ARTIFACT_TYPE
        ),
        contract_identity_sha256=identity,
        contract_byte_count=len(canonical),
        semantic_core_contract_sha256=(
            profile.semantic_core_contract_sha256
        ),
        profile_contract_artifact_type=profile.profile_artifact_type,
        profile_contract_sha256=profile.profile_contract_sha256,
        source_kind_bindings=source_bindings,
        authority_requirement_bindings=authority_bindings,
        locator_reference_bindings=locator_reference_bindings,
        snapshot_authentication_required_locator_count=modes.count(
            "SOURCE_SNAPSHOT_AUTHENTICATION_REQUIRED"
        ),
        prior_sibling_reference_required_locator_count=modes.count(
            "PRIOR_SIBLING_REFERENCE_REQUIRED"
        ),
        statically_blocked_locator_count=modes.count(
            "STATIC_REFERENCE_BLOCKED"
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
        expected_contract=canonical,
        expected_identity=identity,
        expected_semantic_core_contract_sha256=(
            profile.semantic_core_contract_sha256
        ),
        expected_profile_contract_artifact_type=profile.profile_artifact_type,
        expected_profile_contract_sha256=profile.profile_contract_sha256,
        expected_source_bindings=source_bindings,
        expected_authority_bindings=authority_bindings,
        expected_locator_reference_bindings=locator_reference_bindings,
    )


def compile_portable_predicate_resolver_reference_contract_v1(
    resolver_reference_contract_bytes: bytes,
    *,
    compiled_profile: _runtime.CompiledPortablePredicateRuntimeProfileV1,
    expected_resolver_reference_contract_sha256: str,
) -> CompiledPortablePredicateResolverReferenceV1:
    """Compile one exact static resolver-reference sidecar.

    Acceptance proves only static profile-bound reference closure.  No source
    schema, typed-leaf binding, credential, trust root, locator interpreter,
    resolver outcome, or official input bundle is validated or constructed.
    """

    if (
        type(resolver_reference_contract_bytes) is not bytes
        or type(expected_resolver_reference_contract_sha256) is not str
    ):
        _reject(PortablePredicateResolverReferenceCode.INPUT_TYPE)
    try:
        return _compile(
            resolver_reference_contract_bytes,
            compiled_profile=compiled_profile,
            expected_identity=(
                expected_resolver_reference_contract_sha256
            ),
        )
    except PortablePredicateResolverReferenceError:
        raise
    except (MemoryError, KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        _reject(PortablePredicateResolverReferenceCode.INTERNAL)
