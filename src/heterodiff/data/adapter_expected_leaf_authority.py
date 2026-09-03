"""Write-free authority validation for expected-evidence leaf bundles.

This additive boundary authenticates exact authority-profile bytes against a
separately supplied byte anchor and reconciles the profile with the already
validated V1 publication authority, raw source-archive bytes, raw
expected-leaf-archive bytes, and independent-golden material.  It performs no
filesystem access, process execution, network access, adapter invocation,
publication, or gate decision.

An anchor authorizes only the supplied profile bytes.  It is not evidence of
profile authorship, custody, contained execution, or semantic truth.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import NamedTuple, Tuple

from . import adapter_expected_leaf_archive as _leaf_archive
from . import adapter_expected_leaf_authority_types as _types
from . import adapter_publication_authority as _base_authority
from . import adapter_source_archive as _source_archive
from .adapter_publication_authority_types import ApprovedCaseExpectationV1
from .adapter_publication_types import PublicIdentifierRegistryV1


MAXIMUM_EXPECTED_LEAF_AUTHORITY_JSON_DEPTH = 32
MAXIMUM_EXPECTED_LEAF_AUTHORITY_JSON_NODES = 200_000
MAXIMUM_EXPECTED_LEAF_AUTHORITY_STRING_BYTES = 512 * 1024
_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1

APPROVED_CASE_EXPECTATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.approved-case-expectation.v1"
)
APPROVED_EXPECTED_LEAF_CASE_EXPECTATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.approved-expected-leaf-case-expectation.v1"
)
EXPECTED_LEAF_CASE_AUTHORITY_ID_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-leaf-case-authority-id.v1"
)


class ValidatedExpectedLeafVerifierClosureV1(NamedTuple):
    """Exact two-source closure reconciled with supplied parent archive bytes."""

    closure: _types.ExpectedLeafVerifierClosureV1
    closure_bytes: bytes
    closure_sha256: str
    verifier_source_inputs: Tuple[
        _types.ExpectedLeafVerifierSourceInputV1, ...
    ]
    source_archive: _source_archive.ValidatedSourceArchiveV1


class ValidatedApprovedExpectedLeafAuthorityV1(NamedTuple):
    """Anchored leaf profile plus structurally revalidated raw dependencies."""

    profile: _types.ApprovedExpectedLeafAuthorityProfileV1
    profile_bytes: bytes
    profile_file_sha256: str
    profile_sha256: str
    parent_authority: (
        _base_authority.ValidatedApprovedPublicationAuthorityV1
    )
    verifier_closure: ValidatedExpectedLeafVerifierClosureV1
    expected_leaf_archive: _leaf_archive.ValidatedExpectedLeafArchiveV1


class ValidatedIndependentGoldenExpectedLeafExtensionV1(NamedTuple):
    """Canonical extension bound to one approved case and archived bundle."""

    receipt: _types.IndependentGoldenExpectedLeafExtensionV1
    receipt_bytes: bytes
    receipt_sha256: str
    base_golden: _base_authority.ValidatedIndependentGoldenReceiptV1
    approved_case: _types.ApprovedExpectedLeafCaseExpectationV1
    archived_bundle: _leaf_archive.ResolvedExpectedLeafArchiveObjectV1


class ExpectedLeafAuthorityCode(str, Enum):
    """Closed, interpolation-free expected-leaf authority failures."""

    INPUT_TYPE = "EXPECTED_LEAF_AUTHORITY_INPUT_TYPE"
    RESOURCE = "EXPECTED_LEAF_AUTHORITY_RESOURCE"
    JSON_INVALID = "EXPECTED_LEAF_AUTHORITY_JSON_INVALID"
    NONCANONICAL = "EXPECTED_LEAF_AUTHORITY_NONCANONICAL"
    SCHEMA = "EXPECTED_LEAF_AUTHORITY_SCHEMA"
    ANCHOR_MISMATCH = "EXPECTED_LEAF_AUTHORITY_ANCHOR_MISMATCH"
    PARENT_MISMATCH = "EXPECTED_LEAF_AUTHORITY_PARENT_MISMATCH"
    REGISTRY_MISMATCH = "EXPECTED_LEAF_AUTHORITY_REGISTRY_MISMATCH"
    SEMANTIC_PROFILE_MISMATCH = (
        "EXPECTED_LEAF_AUTHORITY_SEMANTIC_PROFILE_MISMATCH"
    )
    VERIFIER_CLOSURE_MISMATCH = (
        "EXPECTED_LEAF_AUTHORITY_VERIFIER_CLOSURE_MISMATCH"
    )
    ARCHIVE_MISMATCH = "EXPECTED_LEAF_AUTHORITY_ARCHIVE_MISMATCH"
    CASE_MISMATCH = "EXPECTED_LEAF_AUTHORITY_CASE_MISMATCH"
    GOLDEN_MISMATCH = "EXPECTED_LEAF_AUTHORITY_GOLDEN_MISMATCH"
    BUNDLE_MISMATCH = "EXPECTED_LEAF_AUTHORITY_BUNDLE_MISMATCH"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExpectedLeafAuthorityCode.INPUT_TYPE: (
            "expected-leaf authority input is invalid"
        ),
        ExpectedLeafAuthorityCode.RESOURCE: (
            "expected-leaf authority input exceeds a resource ceiling"
        ),
        ExpectedLeafAuthorityCode.JSON_INVALID: (
            "expected-leaf authority JSON is invalid"
        ),
        ExpectedLeafAuthorityCode.NONCANONICAL: (
            "expected-leaf authority JSON is not canonical"
        ),
        ExpectedLeafAuthorityCode.SCHEMA: (
            "expected-leaf authority schema is invalid"
        ),
        ExpectedLeafAuthorityCode.ANCHOR_MISMATCH: (
            "expected-leaf authority does not match its byte anchor"
        ),
        ExpectedLeafAuthorityCode.PARENT_MISMATCH: (
            "expected-leaf authority does not match its parent authority"
        ),
        ExpectedLeafAuthorityCode.REGISTRY_MISMATCH: (
            "expected-leaf reason registry does not match approved categories"
        ),
        ExpectedLeafAuthorityCode.SEMANTIC_PROFILE_MISMATCH: (
            "expected-leaf semantic profile differs from the closed profile"
        ),
        ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH: (
            "expected-leaf verifier source closure does not match"
        ),
        ExpectedLeafAuthorityCode.ARCHIVE_MISMATCH: (
            "expected-leaf archive authority does not match"
        ),
        ExpectedLeafAuthorityCode.CASE_MISMATCH: (
            "expected-leaf case authority does not match"
        ),
        ExpectedLeafAuthorityCode.GOLDEN_MISMATCH: (
            "expected-leaf golden extension does not match"
        ),
        ExpectedLeafAuthorityCode.BUNDLE_MISMATCH: (
            "expected-leaf bundle authority does not match"
        ),
    }
)


class ExpectedLeafAuthorityError(ValueError):
    """One fixed coded failure without untrusted interpolation."""

    def __init__(self, code: ExpectedLeafAuthorityCode) -> None:
        if type(code) is not ExpectedLeafAuthorityCode:
            raise TypeError("expected-leaf authority code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class _SemanticProfileMismatch(ValueError):
    pass


class _AuthorityResourceError(ValueError):
    pass


def _fail(code: ExpectedLeafAuthorityCode) -> None:
    raise ExpectedLeafAuthorityError(code) from None


def domain_separated_sha256(domain: str, payload: bytes) -> str:
    """Hash exact bounded bytes under the repository's framed domain format."""

    if type(domain) is not str or type(payload) is not bytes:
        raise TypeError("domain digest inputs must have exact types")
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        raise TypeError("digest domain must be ASCII") from None
    if not domain_bytes or len(domain_bytes) > 256 or b"\x00" in domain_bytes:
        raise ValueError("digest domain is outside its exact bound")
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _validate_tree(
    value: object,
    *,
    allow_null: bool = False,
    allow_signed_integers: bool = False,
    allow_unicode_values: bool = False,
    allow_unicode_keys: bool = False,
    count_object_keys: bool = True,
) -> None:
    nodes = 0
    stack = [(value, 0, False)]
    while stack:
        current, depth, is_object_key = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_EXPECTED_LEAF_AUTHORITY_JSON_NODES:
            raise _AuthorityResourceError
        if depth > MAXIMUM_EXPECTED_LEAF_AUTHORITY_JSON_DEPTH:
            raise ValueError("authority JSON is too deeply nested")
        if current is None or type(current) in (bool, int, str):
            if current is None:
                if not allow_null:
                    raise ValueError("authority JSON does not admit null")
                continue
            if type(current) is int:
                invalid_integer = (
                    abs(current) > _MAXIMUM_SAFE_INTEGER
                    if allow_signed_integers
                    else (
                        current < 0
                        or current > _MAXIMUM_SAFE_INTEGER
                    )
                )
                if invalid_integer:
                    raise ValueError(
                        "authority integer is outside its exact range"
                    )
            if type(current) is str:
                try:
                    encoded = current.encode(
                        (
                            "utf-8"
                            if (
                                allow_unicode_values
                                and not is_object_key
                            )
                            or (
                                allow_unicode_keys
                                and is_object_key
                            )
                            else "ascii"
                        ),
                        "strict",
                    )
                except UnicodeError:
                    raise ValueError(
                        "authority text is outside its exact profile"
                    ) from None
                if len(encoded) > MAXIMUM_EXPECTED_LEAF_AUTHORITY_STRING_BYTES:
                    raise _AuthorityResourceError
            continue
        if type(current) is list:
            stack.extend(
                (item, depth + 1, False) for item in reversed(current)
            )
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    raise ValueError("authority object key must be text")
                try:
                    encoded_key = key.encode(
                        "utf-8" if allow_unicode_keys else "ascii",
                        "strict",
                    )
                except UnicodeError:
                    raise ValueError(
                        "authority object key is outside its exact profile"
                    ) from None
                if (
                    len(encoded_key)
                    > MAXIMUM_EXPECTED_LEAF_AUTHORITY_STRING_BYTES
                ):
                    raise _AuthorityResourceError
                stack.append((item, depth + 1, False))
                if count_object_keys:
                    stack.append((key, depth + 1, True))
            continue
        raise ValueError("authority JSON contains an invalid value type")


def _canonical_bytes(
    value: object,
    *,
    maximum: int,
    allow_null: bool = False,
    allow_signed_integers: bool = False,
    allow_unicode_values: bool = False,
    allow_unicode_keys: bool = False,
    count_object_keys: bool = True,
) -> bytes:
    _validate_tree(
        value,
        allow_null=allow_null,
        allow_signed_integers=allow_signed_integers,
        allow_unicode_values=allow_unicode_values,
        allow_unicode_keys=allow_unicode_keys,
        count_object_keys=count_object_keys,
    )
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValueError("authority value is not canonically encodable") from error
    if not result or len(result) > maximum:
        raise ValueError("authority bytes exceed their exact ceiling")
    return result


def _strict_tree(
    value: bytes,
    *,
    maximum: int,
    allow_null: bool = False,
    allow_signed_integers: bool = False,
    allow_unicode_values: bool = False,
    allow_unicode_keys: bool = False,
    count_object_keys: bool = True,
) -> object:
    if type(value) is not bytes:
        _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
    if not value or len(value) > maximum:
        _fail(ExpectedLeafAuthorityCode.RESOURCE)
    if any(byte >= 0x80 for byte in value):
        _fail(ExpectedLeafAuthorityCode.JSON_INVALID)
    depth = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            if escaped:
                string_bytes += 1
                escaped = False
            elif byte == 0x5C:
                string_bytes += 1
                escaped = True
            elif byte == 0x22:
                in_string = False
            else:
                string_bytes += 1
            if (
                string_bytes
                > MAXIMUM_EXPECTED_LEAF_AUTHORITY_STRING_BYTES
            ):
                _fail(ExpectedLeafAuthorityCode.RESOURCE)
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > MAXIMUM_EXPECTED_LEAF_AUTHORITY_JSON_DEPTH:
                _fail(ExpectedLeafAuthorityCode.JSON_INVALID)
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _fail(ExpectedLeafAuthorityCode.JSON_INVALID)
    if in_string or depth != 0:
        _fail(ExpectedLeafAuthorityCode.JSON_INVALID)
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(ExpectedLeafAuthorityCode.JSON_INVALID)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise ValueError("integer token is too long")
        result = int(token, 10)
        invalid_integer = (
            abs(result) > _MAXIMUM_SAFE_INTEGER
            if allow_signed_integers
            else (
                result < 0
                or result > _MAXIMUM_SAFE_INTEGER
            )
        )
        if invalid_integer:
            raise ValueError("integer is outside its exact range")
        return result

    def reject_number(_token):
        raise ValueError("only integers are admitted")

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
        _validate_tree(
            tree,
            allow_null=allow_null,
            allow_signed_integers=allow_signed_integers,
            allow_unicode_values=allow_unicode_values,
            allow_unicode_keys=allow_unicode_keys,
            count_object_keys=count_object_keys,
        )
    except _AuthorityResourceError:
        _fail(ExpectedLeafAuthorityCode.RESOURCE)
    except (TypeError, ValueError, RecursionError):
        _fail(ExpectedLeafAuthorityCode.JSON_INVALID)
    try:
        canonical = _canonical_bytes(
            tree,
            maximum=maximum,
            allow_null=allow_null,
            allow_signed_integers=allow_signed_integers,
            allow_unicode_values=allow_unicode_values,
            allow_unicode_keys=allow_unicode_keys,
            count_object_keys=count_object_keys,
        )
    except ValueError:
        _fail(ExpectedLeafAuthorityCode.JSON_INVALID)
    if canonical != value:
        _fail(ExpectedLeafAuthorityCode.NONCANONICAL)
    return tree


def _keys(value: object, expected: Tuple[str, ...]) -> dict:
    if type(value) is not dict or tuple(sorted(value)) != tuple(sorted(expected)):
        raise ValueError("authority object has a nonexact key set")
    return value


_BASE_CASE_KEYS = (
    "adapter_id",
    "adapter_version",
    "case_ordinal",
    "complete_sample_commitment_sha256",
    "conformance_run_sha256",
    "descriptor_sha256",
    "expected_configuration_sha256",
    "expected_evidence_sha256",
    "independent_golden_receipt_sha256",
    "native_observation_sha256",
    "sample_root_sha256",
    "source_sha256",
    "split_manifest_sha256",
)


def approved_case_expectation_tree(
    value: ApprovedCaseExpectationV1,
) -> dict:
    """Project one existing V1 case without changing its frozen schema."""

    if type(value) is not ApprovedCaseExpectationV1:
        raise TypeError("approved case expectation must be exact")
    ApprovedCaseExpectationV1.__post_init__(value)
    return {name: getattr(value, name) for name in _BASE_CASE_KEYS}


def approved_case_expectation_bytes(
    value: ApprovedCaseExpectationV1,
) -> bytes:
    """Serialize one existing V1 case as exact canonical ASCII JSON."""

    return _canonical_bytes(
        approved_case_expectation_tree(value),
        maximum=4 * 1024 * 1024,
    )


def approved_case_expectation_sha256(
    value: ApprovedCaseExpectationV1,
) -> str:
    """Return the isolated domain digest of one frozen V1 case projection."""

    return domain_separated_sha256(
        APPROVED_CASE_EXPECTATION_DIGEST_DOMAIN,
        approved_case_expectation_bytes(value),
    )


def expected_leaf_case_authority_id(
    value: ApprovedCaseExpectationV1,
) -> str:
    """Derive a stable leaf-custody ID from one exact approved V1 case."""

    return domain_separated_sha256(
        EXPECTED_LEAF_CASE_AUTHORITY_ID_DIGEST_DOMAIN,
        approved_case_expectation_bytes(value),
    )


_REASON_REGISTRY_KEYS = (
    "allowed_censor_reason_codes",
    "allowed_exclusion_reason_codes",
    "artifact_type",
    "binding_mode_id",
    "format_version",
)
_VERIFIER_SOURCE_KEYS = (
    "module_id",
    "source_byte_count",
    "source_sha256",
)
_VERIFIER_CLOSURE_KEYS = (
    "artifact_type",
    "format_version",
    "source_tree_archive_sha256",
    "source_tree_manifest_sha256",
    "sources",
)
_GOLDEN_EXTENSION_KEYS = (
    "adapter_id",
    "adapter_version",
    "artifact_type",
    "base_golden_receipt_sha256",
    "case_authority_id",
    "case_ordinal",
    "censor_reason_registry_sha256",
    "descriptor_sha256",
    "exclusion_reason_registry_sha256",
    "expected_configuration_sha256",
    "expected_evidence_sha256",
    "expected_leaf_archive_byte_count",
    "expected_leaf_archive_inventory_byte_count",
    "expected_leaf_archive_inventory_file_sha256",
    "expected_leaf_archive_inventory_sha256",
    "expected_leaf_archive_object_id",
    "expected_leaf_archive_sha256",
    "expected_leaf_bundle_artifact_type",
    "expected_leaf_bundle_byte_count",
    "expected_leaf_bundle_file_sha256",
    "expected_leaf_bundle_format_version",
    "expected_leaf_bundle_sha256",
    "expected_native_observation_sha256",
    "format_version",
    "reason_registry_sha256",
    "semantic_profile_sha256",
    "source_sha256",
    "split_manifest_sha256",
    "verifier_closure_sha256",
)
_LEAF_CASE_KEYS = (
    "base_case_expectation_sha256",
    "case_authority_id",
    "case_ordinal",
    "censor_reason_registry_sha256",
    "exclusion_reason_registry_sha256",
    "expected_leaf_archive_byte_count",
    "expected_leaf_archive_inventory_byte_count",
    "expected_leaf_archive_inventory_file_sha256",
    "expected_leaf_archive_inventory_sha256",
    "expected_leaf_archive_object_id",
    "expected_leaf_archive_sha256",
    "expected_leaf_bundle_artifact_type",
    "expected_leaf_bundle_byte_count",
    "expected_leaf_bundle_file_sha256",
    "expected_leaf_bundle_format_version",
    "expected_leaf_bundle_sha256",
    "golden_extension_sha256",
    "reason_registry_sha256",
    "semantic_profile_sha256",
    "verifier_closure_sha256",
)
_PROFILE_KEYS = (
    "approval_status_id",
    "artifact_type",
    "case_expectations",
    "expected_leaf_archive_byte_count",
    "expected_leaf_archive_inventory_byte_count",
    "expected_leaf_archive_inventory_file_sha256",
    "expected_leaf_archive_inventory_sha256",
    "expected_leaf_archive_sha256",
    "format_version",
    "parent_approved_profile_file_sha256",
    "parent_approved_profile_sha256",
    "profile_id",
    "reason_registry",
    "semantic_profile",
    "verifier_closure",
)


def expected_leaf_reason_registry_tree(
    value: _types.ExpectedLeafReasonRegistryV1,
) -> dict:
    """Project the complete exact-category reason registry."""

    if type(value) is not _types.ExpectedLeafReasonRegistryV1:
        raise TypeError("expected-leaf reason registry must be exact")
    _types.ExpectedLeafReasonRegistryV1.__post_init__(value)
    return {
        "allowed_censor_reason_codes": list(
            value.allowed_censor_reason_codes
        ),
        "allowed_exclusion_reason_codes": list(
            value.allowed_exclusion_reason_codes
        ),
        "artifact_type": value.artifact_type,
        "binding_mode_id": value.binding_mode_id,
        "format_version": value.format_version,
    }


def expected_leaf_reason_registry_bytes(
    value: _types.ExpectedLeafReasonRegistryV1,
) -> bytes:
    return _canonical_bytes(
        expected_leaf_reason_registry_tree(value),
        maximum=_types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
    )


def expected_leaf_reason_registry_sha256(
    value: _types.ExpectedLeafReasonRegistryV1,
) -> str:
    return domain_separated_sha256(
        _types.EXPECTED_LEAF_REASON_REGISTRY_DIGEST_DOMAIN,
        expected_leaf_reason_registry_bytes(value),
    )


def _reason_category_bytes(value: Tuple[str, ...]) -> bytes:
    if type(value) is not tuple:
        raise TypeError("reason category must be an exact tuple")
    return _canonical_bytes(
        list(value),
        maximum=_types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
    )


def expected_leaf_censor_reason_registry_sha256(
    value: _types.ExpectedLeafReasonRegistryV1,
) -> str:
    """Digest only the exact censor category under its distinct domain."""

    if type(value) is not _types.ExpectedLeafReasonRegistryV1:
        raise TypeError("expected-leaf reason registry must be exact")
    _types.ExpectedLeafReasonRegistryV1.__post_init__(value)
    return domain_separated_sha256(
        _types.EXPECTED_LEAF_CENSOR_REASON_REGISTRY_DIGEST_DOMAIN,
        _reason_category_bytes(value.allowed_censor_reason_codes),
    )


def expected_leaf_exclusion_reason_registry_sha256(
    value: _types.ExpectedLeafReasonRegistryV1,
) -> str:
    """Digest only the exact exclusion category under its distinct domain."""

    if type(value) is not _types.ExpectedLeafReasonRegistryV1:
        raise TypeError("expected-leaf reason registry must be exact")
    _types.ExpectedLeafReasonRegistryV1.__post_init__(value)
    return domain_separated_sha256(
        _types.EXPECTED_LEAF_EXCLUSION_REASON_REGISTRY_DIGEST_DOMAIN,
        _reason_category_bytes(value.allowed_exclusion_reason_codes),
    )


def expected_leaf_semantic_profile_tree(
    value: _types.ExpectedLeafSemanticProfileV1,
) -> dict:
    """Project every fixed parser, resource, and nonclaim field."""

    if type(value) is not _types.ExpectedLeafSemanticProfileV1:
        raise TypeError("expected-leaf semantic profile must be exact")
    _types.ExpectedLeafSemanticProfileV1.__post_init__(value)
    result = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        if name == "member_digest_domains":
            result[name] = [
                {
                    "member_id": member.member_id,
                    "payload_digest_domain": member.payload_digest_domain,
                }
                for member in item
            ]
        elif type(item) is tuple:
            result[name] = list(item)
        else:
            result[name] = item
    return result


def expected_leaf_semantic_profile_bytes(
    value: _types.ExpectedLeafSemanticProfileV1,
) -> bytes:
    return _canonical_bytes(
        expected_leaf_semantic_profile_tree(value),
        maximum=_types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
    )


def expected_leaf_semantic_profile_sha256(
    value: _types.ExpectedLeafSemanticProfileV1,
) -> str:
    return domain_separated_sha256(
        _types.EXPECTED_LEAF_SEMANTIC_PROFILE_DIGEST_DOMAIN,
        expected_leaf_semantic_profile_bytes(value),
    )


def expected_leaf_verifier_closure_tree(
    value: _types.ExpectedLeafVerifierClosureV1,
) -> dict:
    """Project the exact two-module independent-verifier source closure."""

    if type(value) is not _types.ExpectedLeafVerifierClosureV1:
        raise TypeError("expected-leaf verifier closure must be exact")
    _types.ExpectedLeafVerifierClosureV1.__post_init__(value)
    return {
        "artifact_type": value.artifact_type,
        "format_version": value.format_version,
        "source_tree_archive_sha256": value.source_tree_archive_sha256,
        "source_tree_manifest_sha256": value.source_tree_manifest_sha256,
        "sources": [
            {
                "module_id": item.module_id,
                "source_byte_count": item.source_byte_count,
                "source_sha256": item.source_sha256,
            }
            for item in value.sources
        ],
    }


def expected_leaf_verifier_closure_bytes(
    value: _types.ExpectedLeafVerifierClosureV1,
) -> bytes:
    return _canonical_bytes(
        expected_leaf_verifier_closure_tree(value),
        maximum=_types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
    )


def expected_leaf_verifier_closure_sha256(
    value: _types.ExpectedLeafVerifierClosureV1,
) -> str:
    return domain_separated_sha256(
        _types.EXPECTED_LEAF_VERIFIER_CLOSURE_DIGEST_DOMAIN,
        expected_leaf_verifier_closure_bytes(value),
    )


def independent_golden_expected_leaf_extension_tree(
    value: _types.IndependentGoldenExpectedLeafExtensionV1,
) -> dict:
    """Project one exact independently supplied golden extension."""

    if type(value) is not _types.IndependentGoldenExpectedLeafExtensionV1:
        raise TypeError("independent golden expected-leaf extension must be exact")
    _types.IndependentGoldenExpectedLeafExtensionV1.__post_init__(value)
    return {name: getattr(value, name) for name in _GOLDEN_EXTENSION_KEYS}


def independent_golden_expected_leaf_extension_bytes(
    value: _types.IndependentGoldenExpectedLeafExtensionV1,
) -> bytes:
    return _canonical_bytes(
        independent_golden_expected_leaf_extension_tree(value),
        maximum=(
            _types.MAXIMUM_INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_BYTES
        ),
    )


def independent_golden_expected_leaf_extension_sha256(
    value: _types.IndependentGoldenExpectedLeafExtensionV1,
) -> str:
    return domain_separated_sha256(
        _types.INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_DIGEST_DOMAIN,
        independent_golden_expected_leaf_extension_bytes(value),
    )


def approved_expected_leaf_case_expectation_tree(
    value: _types.ApprovedExpectedLeafCaseExpectationV1,
) -> dict:
    if type(value) is not _types.ApprovedExpectedLeafCaseExpectationV1:
        raise TypeError("approved expected-leaf case must be exact")
    _types.ApprovedExpectedLeafCaseExpectationV1.__post_init__(value)
    return {name: getattr(value, name) for name in _LEAF_CASE_KEYS}


def approved_expected_leaf_case_expectation_bytes(
    value: _types.ApprovedExpectedLeafCaseExpectationV1,
) -> bytes:
    return _canonical_bytes(
        approved_expected_leaf_case_expectation_tree(value),
        maximum=_types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
    )


def approved_expected_leaf_case_expectation_sha256(
    value: _types.ApprovedExpectedLeafCaseExpectationV1,
) -> str:
    return domain_separated_sha256(
        APPROVED_EXPECTED_LEAF_CASE_EXPECTATION_DIGEST_DOMAIN,
        approved_expected_leaf_case_expectation_bytes(value),
    )


def approved_expected_leaf_authority_profile_tree(
    value: _types.ApprovedExpectedLeafAuthorityProfileV1,
) -> dict:
    if type(value) is not _types.ApprovedExpectedLeafAuthorityProfileV1:
        raise TypeError("approved expected-leaf authority profile must be exact")
    _types.ApprovedExpectedLeafAuthorityProfileV1.__post_init__(value)
    return {
        "approval_status_id": value.approval_status_id,
        "artifact_type": value.artifact_type,
        "case_expectations": [
            approved_expected_leaf_case_expectation_tree(item)
            for item in value.case_expectations
        ],
        "expected_leaf_archive_byte_count": (
            value.expected_leaf_archive_byte_count
        ),
        "expected_leaf_archive_inventory_byte_count": (
            value.expected_leaf_archive_inventory_byte_count
        ),
        "expected_leaf_archive_inventory_file_sha256": (
            value.expected_leaf_archive_inventory_file_sha256
        ),
        "expected_leaf_archive_inventory_sha256": (
            value.expected_leaf_archive_inventory_sha256
        ),
        "expected_leaf_archive_sha256": value.expected_leaf_archive_sha256,
        "format_version": value.format_version,
        "parent_approved_profile_file_sha256": (
            value.parent_approved_profile_file_sha256
        ),
        "parent_approved_profile_sha256": (
            value.parent_approved_profile_sha256
        ),
        "profile_id": value.profile_id,
        "reason_registry": expected_leaf_reason_registry_tree(
            value.reason_registry
        ),
        "semantic_profile": expected_leaf_semantic_profile_tree(
            value.semantic_profile
        ),
        "verifier_closure": expected_leaf_verifier_closure_tree(
            value.verifier_closure
        ),
    }


def approved_expected_leaf_authority_profile_bytes(
    value: _types.ApprovedExpectedLeafAuthorityProfileV1,
) -> bytes:
    return _canonical_bytes(
        approved_expected_leaf_authority_profile_tree(value),
        maximum=_types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
    )


def approved_expected_leaf_authority_profile_sha256(
    value: _types.ApprovedExpectedLeafAuthorityProfileV1,
) -> str:
    return domain_separated_sha256(
        _types.APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_DIGEST_DOMAIN,
        approved_expected_leaf_authority_profile_bytes(value),
    )


def _reason_registry_from_tree(
    value: object,
) -> _types.ExpectedLeafReasonRegistryV1:
    tree = _keys(value, _REASON_REGISTRY_KEYS)
    if (
        tree["artifact_type"]
        != _types.EXPECTED_LEAF_REASON_REGISTRY_ARTIFACT_TYPE
        or tree["binding_mode_id"]
        != _types.EXPECTED_LEAF_REASON_REGISTRY_BINDING_MODE_ID
        or tree["format_version"] != "1"
        or type(tree["allowed_censor_reason_codes"]) is not list
        or type(tree["allowed_exclusion_reason_codes"]) is not list
    ):
        raise ValueError("reason registry fixed schema differs")
    return _types.ExpectedLeafReasonRegistryV1(
        allowed_censor_reason_codes=tuple(
            tree["allowed_censor_reason_codes"]
        ),
        allowed_exclusion_reason_codes=tuple(
            tree["allowed_exclusion_reason_codes"]
        ),
    )


def _semantic_profile_from_tree(
    value: object,
) -> _types.ExpectedLeafSemanticProfileV1:
    expected = _types.ExpectedLeafSemanticProfileV1()
    if value != expected_leaf_semantic_profile_tree(expected):
        raise _SemanticProfileMismatch
    return expected


def _verifier_closure_from_tree(
    value: object,
) -> _types.ExpectedLeafVerifierClosureV1:
    tree = _keys(value, _VERIFIER_CLOSURE_KEYS)
    if (
        tree["artifact_type"]
        != _types.EXPECTED_LEAF_VERIFIER_CLOSURE_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or type(tree["sources"]) is not list
    ):
        raise ValueError("verifier closure fixed schema differs")
    sources = tuple(
        _types.ExpectedLeafVerifierSourceExpectationV1(
            **_keys(item, _VERIFIER_SOURCE_KEYS)
        )
        for item in tree["sources"]
    )
    return _types.ExpectedLeafVerifierClosureV1(
        sources=sources,
        source_tree_archive_sha256=tree["source_tree_archive_sha256"],
        source_tree_manifest_sha256=tree["source_tree_manifest_sha256"],
    )


def _golden_extension_from_tree(
    value: object,
) -> _types.IndependentGoldenExpectedLeafExtensionV1:
    tree = _keys(value, _GOLDEN_EXTENSION_KEYS)
    if (
        tree["artifact_type"]
        != _types.INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_ARTIFACT_TYPE
        or tree["format_version"] != "1"
    ):
        raise ValueError("golden extension fixed schema differs")
    return _types.IndependentGoldenExpectedLeafExtensionV1(
        **{
            name: tree[name]
            for name, definition in (
                _types.IndependentGoldenExpectedLeafExtensionV1
                .__dataclass_fields__
                .items()
            )
            if definition.init
        }
    )


def _leaf_case_from_tree(
    value: object,
) -> _types.ApprovedExpectedLeafCaseExpectationV1:
    tree = _keys(value, _LEAF_CASE_KEYS)
    return _types.ApprovedExpectedLeafCaseExpectationV1(
        **{name: tree[name] for name in _LEAF_CASE_KEYS}
    )


def _profile_from_tree(
    value: object,
) -> _types.ApprovedExpectedLeafAuthorityProfileV1:
    tree = _keys(value, _PROFILE_KEYS)
    if (
        tree["approval_status_id"]
        != _types.APPROVED_EXPECTED_LEAF_AUTHORITY_STATUS
        or tree["artifact_type"]
        != _types.APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["profile_id"]
        != _types.APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_ID
        or type(tree["case_expectations"]) is not list
    ):
        raise ValueError("authority profile fixed schema differs")
    return _types.ApprovedExpectedLeafAuthorityProfileV1(
        parent_approved_profile_file_sha256=(
            tree["parent_approved_profile_file_sha256"]
        ),
        parent_approved_profile_sha256=(
            tree["parent_approved_profile_sha256"]
        ),
        reason_registry=_reason_registry_from_tree(tree["reason_registry"]),
        semantic_profile=_semantic_profile_from_tree(tree["semantic_profile"]),
        verifier_closure=_verifier_closure_from_tree(tree["verifier_closure"]),
        expected_leaf_archive_byte_count=(
            tree["expected_leaf_archive_byte_count"]
        ),
        expected_leaf_archive_sha256=tree["expected_leaf_archive_sha256"],
        expected_leaf_archive_inventory_byte_count=(
            tree["expected_leaf_archive_inventory_byte_count"]
        ),
        expected_leaf_archive_inventory_file_sha256=(
            tree["expected_leaf_archive_inventory_file_sha256"]
        ),
        expected_leaf_archive_inventory_sha256=(
            tree["expected_leaf_archive_inventory_sha256"]
        ),
        case_expectations=tuple(
            _leaf_case_from_tree(item)
            for item in tree["case_expectations"]
        ),
    )


def parse_approved_expected_leaf_authority_profile(
    value: bytes,
) -> _types.ApprovedExpectedLeafAuthorityProfileV1:
    """Strict-parse canonical profile bytes without assigning authority."""

    tree = _strict_tree(
        value,
        maximum=_types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES,
    )
    try:
        profile = _profile_from_tree(tree)
        if approved_expected_leaf_authority_profile_bytes(profile) != value:
            raise ValueError("profile projection differs")
    except _SemanticProfileMismatch:
        _fail(ExpectedLeafAuthorityCode.SEMANTIC_PROFILE_MISMATCH)
    except (TypeError, ValueError, _types.ExpectedLeafAuthorityTypeError):
        _fail(ExpectedLeafAuthorityCode.SCHEMA)
    return profile


def parse_independent_golden_expected_leaf_extension(
    value: bytes,
) -> _types.IndependentGoldenExpectedLeafExtensionV1:
    """Strict-parse canonical golden-extension bytes without trusting them."""

    tree = _strict_tree(
        value,
        maximum=(
            _types.MAXIMUM_INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_BYTES
        ),
    )
    try:
        receipt = _golden_extension_from_tree(tree)
        if independent_golden_expected_leaf_extension_bytes(receipt) != value:
            raise ValueError("golden extension projection differs")
    except (TypeError, ValueError, _types.ExpectedLeafAuthorityTypeError):
        _fail(ExpectedLeafAuthorityCode.SCHEMA)
    return receipt


def _archive_identity(value: object) -> tuple:
    return (
        getattr(value, "expected_leaf_archive_byte_count"),
        getattr(value, "expected_leaf_archive_sha256"),
        getattr(value, "expected_leaf_archive_inventory_byte_count"),
        getattr(value, "expected_leaf_archive_inventory_file_sha256"),
        getattr(value, "expected_leaf_archive_inventory_sha256"),
    )


def _validate_reason_registry(
    value: _types.ExpectedLeafReasonRegistryV1,
    public_ids: PublicIdentifierRegistryV1,
) -> Tuple[str, str, str]:
    if type(public_ids) is not PublicIdentifierRegistryV1:
        _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
    try:
        _types.ExpectedLeafReasonRegistryV1.__post_init__(value)
        PublicIdentifierRegistryV1.__post_init__(public_ids)
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.REGISTRY_MISMATCH)
    if (
        value.allowed_censor_reason_codes != public_ids.censor_reason_ids
        or value.allowed_exclusion_reason_codes
        != public_ids.coverage_exclusion_reason_ids
    ):
        _fail(ExpectedLeafAuthorityCode.REGISTRY_MISMATCH)
    return (
        expected_leaf_reason_registry_sha256(value),
        expected_leaf_censor_reason_registry_sha256(value),
        expected_leaf_exclusion_reason_registry_sha256(value),
    )


def _validate_verifier_closure(
    value: _types.ExpectedLeafVerifierClosureV1,
    source_inputs: Tuple[_types.ExpectedLeafVerifierSourceInputV1, ...],
    *,
    parent_authority: (
        _base_authority.ValidatedApprovedPublicationAuthorityV1
    ),
    source_archive_inventory_bytes: bytes,
    source_archive_bytes: bytes,
) -> ValidatedExpectedLeafVerifierClosureV1:
    if (
        type(source_inputs) is not tuple
        or len(source_inputs)
        != len(_types.EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS)
        or any(
            type(item) is not _types.ExpectedLeafVerifierSourceInputV1
            for item in source_inputs
        )
        or tuple(item.module_id for item in source_inputs)
        != _types.EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS
    ):
        _fail(ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH)
    expected_by_id = {item.module_id: item for item in value.sources}
    if tuple(sorted(expected_by_id)) != (
        _types.EXPECTED_LEAF_REQUIRED_VERIFIER_MODULE_IDS
    ):
        _fail(ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH)
    snapshots = []
    for supplied in source_inputs:
        if type(supplied) is not _types.ExpectedLeafVerifierSourceInputV1:
            _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
        try:
            snapshot = _types.ExpectedLeafVerifierSourceInputV1(
                module_id=supplied.module_id,
                source_bytes=supplied.source_bytes,
            )
        except (TypeError, ValueError):
            _fail(ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH)
        snapshots.append(snapshot)
        expected = expected_by_id.get(snapshot.module_id)
        if (
            expected is None
            or expected.source_byte_count != len(snapshot.source_bytes)
            or expected.source_sha256
            != hashlib.sha256(snapshot.source_bytes).hexdigest()
        ):
            _fail(ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH)
    source_snapshots = tuple(snapshots)

    parent_binding = parent_authority.profile.binding_expectations
    if (
        value.source_tree_archive_sha256
        != parent_binding.source_tree_archive_sha256
        or value.source_tree_manifest_sha256
        != parent_binding.source_tree_manifest_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.PARENT_MISMATCH)
    try:
        membership_set = _source_archive.validate_source_archive_memberships(
            source_archive_inventory_bytes,
            source_archive_bytes,
            tuple(
                _source_archive.SourceArchiveMembershipRequestV1(
                    role_id="verifier-source",
                    source_bytes=item.source_bytes,
                    source_object_id=item.module_id,
                )
                for item in source_snapshots
            ),
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH)
    source_archive = membership_set.source_archive
    if (
        source_archive.archive_sha256
        != value.source_tree_archive_sha256
        or source_archive.inventory_sha256
        != value.source_tree_manifest_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH)
    closure_bytes = expected_leaf_verifier_closure_bytes(value)
    return ValidatedExpectedLeafVerifierClosureV1(
        closure=value,
        closure_bytes=closure_bytes,
        closure_sha256=domain_separated_sha256(
            _types.EXPECTED_LEAF_VERIFIER_CLOSURE_DIGEST_DOMAIN,
            closure_bytes,
        ),
        verifier_source_inputs=source_snapshots,
        source_archive=source_archive,
    )


def _validate_expected_leaf_archive_authority(
    profile: _types.ApprovedExpectedLeafAuthorityProfileV1,
    *,
    inventory_bytes: bytes,
    archive_bytes: bytes,
) -> _leaf_archive.ValidatedExpectedLeafArchiveV1:
    try:
        validated = _leaf_archive.validate_expected_leaf_archive(
            inventory_bytes,
            archive_bytes,
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.ARCHIVE_MISMATCH)
    observed_identity = (
        len(validated.archive_bytes),
        validated.archive_sha256,
        len(validated.inventory_bytes),
        validated.inventory_file_sha256,
        validated.inventory_sha256,
    )
    if observed_identity != _archive_identity(profile):
        _fail(ExpectedLeafAuthorityCode.ARCHIVE_MISMATCH)
    objects = {
        item.case_authority_id: item
        for item in validated.inventory.expected_leaf_objects
    }
    case_ids = tuple(item.case_authority_id for item in profile.case_expectations)
    if set(objects) != set(case_ids) or len(objects) != len(case_ids):
        _fail(ExpectedLeafAuthorityCode.ARCHIVE_MISMATCH)
    for case in profile.case_expectations:
        item = objects.get(case.case_authority_id)
        if (
            item is None
            or item.role_id != _leaf_archive.EXPECTED_LEAF_ARCHIVE_ROLE_ID
            or item.case_authority_id
            != case.expected_leaf_archive_object_id
            or item.bundle_byte_count
            != case.expected_leaf_bundle_byte_count
            or item.bundle_plain_sha256
            != case.expected_leaf_bundle_file_sha256
            or item.bundle_domain_sha256
            != case.expected_leaf_bundle_sha256
            or _archive_identity(case) != observed_identity
        ):
            _fail(ExpectedLeafAuthorityCode.ARCHIVE_MISMATCH)
    return validated


def _validate_profile_cases(
    profile: _types.ApprovedExpectedLeafAuthorityProfileV1,
    parent_authority: (
        _base_authority.ValidatedApprovedPublicationAuthorityV1
    ),
    *,
    reason_digests: Tuple[str, str, str],
    semantic_profile_sha256: str,
    verifier_closure_sha256: str,
) -> None:
    base_cases = parent_authority.profile.case_expectations
    if len(profile.case_expectations) != len(base_cases):
        _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)
    if len(
        {item.golden_extension_sha256 for item in profile.case_expectations}
    ) != len(profile.case_expectations):
        _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)
    for leaf_case, base_case in zip(profile.case_expectations, base_cases):
        if (
            leaf_case.case_ordinal != base_case.case_ordinal
            or leaf_case.base_case_expectation_sha256
            != approved_case_expectation_sha256(base_case)
            or leaf_case.case_authority_id
            != expected_leaf_case_authority_id(base_case)
            or leaf_case.expected_leaf_archive_object_id
            != leaf_case.case_authority_id
            or leaf_case.reason_registry_sha256 != reason_digests[0]
            or leaf_case.censor_reason_registry_sha256 != reason_digests[1]
            or leaf_case.exclusion_reason_registry_sha256
            != reason_digests[2]
            or leaf_case.semantic_profile_sha256
            != semantic_profile_sha256
            or leaf_case.verifier_closure_sha256
            != verifier_closure_sha256
            or _archive_identity(leaf_case) != _archive_identity(profile)
        ):
            _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)


def validate_approved_expected_leaf_authority(
    value: _types.ApprovedExpectedLeafAuthorityInputV1,
    *,
    parent_authority: (
        _base_authority.ValidatedApprovedPublicationAuthorityV1
    ),
    public_identifier_registry: PublicIdentifierRegistryV1,
    source_archive_inventory_bytes: bytes,
    source_archive_bytes: bytes,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> ValidatedApprovedExpectedLeafAuthorityV1:
    """Authenticate a profile byte anchor and reconcile every raw dependency.

    The separate anchor authorizes only ``profile_bytes``.  Successful return
    does not attest who produced the anchor, any execution, containment,
    custody history, payload semantics, or a publication decision.
    """

    if (
        type(value) is not _types.ApprovedExpectedLeafAuthorityInputV1
        or type(parent_authority)
        is not _base_authority.ValidatedApprovedPublicationAuthorityV1
        or type(public_identifier_registry) is not PublicIdentifierRegistryV1
        or type(source_archive_inventory_bytes) is not bytes
        or type(source_archive_bytes) is not bytes
        or type(expected_leaf_archive_inventory_bytes) is not bytes
        or type(expected_leaf_archive_bytes) is not bytes
    ):
        _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
    profile_bytes = value.profile_bytes
    anchor = value.anchor
    if (
        type(profile_bytes) is not bytes
        or not profile_bytes
        or len(profile_bytes)
        > _types.MAXIMUM_APPROVED_EXPECTED_LEAF_PROFILE_BYTES
    ):
        _fail(ExpectedLeafAuthorityCode.RESOURCE)
    if type(anchor) is not _types.ApprovedExpectedLeafAuthorityProfileAnchorV1:
        _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
    try:
        _types.ApprovedExpectedLeafAuthorityProfileAnchorV1.__post_init__(
            anchor
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
    try:
        rebuilt_parent_bytes = _base_authority.approved_profile_bytes(
            parent_authority.profile
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.PARENT_MISMATCH)
    if (
        rebuilt_parent_bytes != parent_authority.profile_bytes
        or hashlib.sha256(rebuilt_parent_bytes).hexdigest()
        != parent_authority.profile_file_sha256
        or _base_authority.domain_separated_sha256(
            _base_authority.APPROVED_PUBLICATION_PROFILE_DIGEST_DOMAIN,
            rebuilt_parent_bytes,
        )
        != parent_authority.profile_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.PARENT_MISMATCH)
    file_sha256 = hashlib.sha256(profile_bytes).hexdigest()
    profile_sha256 = domain_separated_sha256(
        _types.APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_DIGEST_DOMAIN,
        profile_bytes,
    )
    if (
        len(profile_bytes) != anchor.profile_byte_count
        or file_sha256 != anchor.profile_file_sha256
        or profile_sha256 != anchor.profile_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.ANCHOR_MISMATCH)
    profile = parse_approved_expected_leaf_authority_profile(profile_bytes)
    if (
        profile.parent_approved_profile_file_sha256
        != parent_authority.profile_file_sha256
        or profile.parent_approved_profile_sha256
        != parent_authority.profile_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.PARENT_MISMATCH)

    reason_digests = _validate_reason_registry(
        profile.reason_registry,
        public_identifier_registry,
    )
    expected_semantic = _types.ExpectedLeafSemanticProfileV1()
    if profile.semantic_profile != expected_semantic:
        _fail(ExpectedLeafAuthorityCode.SEMANTIC_PROFILE_MISMATCH)
    semantic_sha256 = expected_leaf_semantic_profile_sha256(
        profile.semantic_profile
    )
    verifier_closure = _validate_verifier_closure(
        profile.verifier_closure,
        value.verifier_source_inputs,
        parent_authority=parent_authority,
        source_archive_inventory_bytes=source_archive_inventory_bytes,
        source_archive_bytes=source_archive_bytes,
    )
    _validate_profile_cases(
        profile,
        parent_authority,
        reason_digests=reason_digests,
        semantic_profile_sha256=semantic_sha256,
        verifier_closure_sha256=verifier_closure.closure_sha256,
    )
    expected_leaf_archive = _validate_expected_leaf_archive_authority(
        profile,
        inventory_bytes=expected_leaf_archive_inventory_bytes,
        archive_bytes=expected_leaf_archive_bytes,
    )
    return ValidatedApprovedExpectedLeafAuthorityV1(
        profile=profile,
        profile_bytes=profile_bytes,
        profile_file_sha256=file_sha256,
        profile_sha256=profile_sha256,
        parent_authority=parent_authority,
        verifier_closure=verifier_closure,
        expected_leaf_archive=expected_leaf_archive,
    )


_EXPECTED_LEAF_BUNDLE_KEYS = (
    "allowed_censor_reason_codes",
    "allowed_exclusion_reason_codes",
    "artifact_type",
    "descriptor_sha256",
    "expected",
    "format_version",
    "source_byte_count",
    "source_sha256",
    "split_manifest_sha256",
)
_EXPECTED_LEAF_MEMBER_IDS = (
    "coverage_ledger",
    "detached_native_observation",
    "evaluation_labels",
    "expected_evidence_commitment",
    "fitted_state",
    "identity_bearing_native_configuration",
    "private_provenance",
    "semantic_reconstruction",
    "source_inventory",
    "static_context",
)
_EXPECTED_LEAF_WRAPPER_KEYS = (
    "payload",
    "payload_byte_count",
    "payload_sha256",
)


def _validate_bundle_envelope(
    bundle_bytes: bytes,
    receipt: _types.IndependentGoldenExpectedLeafExtensionV1,
    reason_registry: _types.ExpectedLeafReasonRegistryV1,
    *,
    source_byte_count: int,
) -> None:
    if (
        type(bundle_bytes) is not bytes
        or not bundle_bytes
        or len(bundle_bytes) > _types.MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES
    ):
        _fail(ExpectedLeafAuthorityCode.BUNDLE_MISMATCH)
    if (
        len(bundle_bytes) != receipt.expected_leaf_bundle_byte_count
        or hashlib.sha256(bundle_bytes).hexdigest()
        != receipt.expected_leaf_bundle_file_sha256
        or _leaf_archive.expected_leaf_archive_bundle_domain_sha256(
            bundle_bytes
        )
        != receipt.expected_leaf_bundle_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.BUNDLE_MISMATCH)
    try:
        tree = _strict_tree(
            bundle_bytes,
            maximum=_types.MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
            allow_null=True,
            allow_signed_integers=True,
            allow_unicode_values=True,
            allow_unicode_keys=True,
            count_object_keys=False,
        )
        tree = _keys(tree, _EXPECTED_LEAF_BUNDLE_KEYS)
        if (
            tree["artifact_type"]
            != receipt.expected_leaf_bundle_artifact_type
            or tree["format_version"]
            != receipt.expected_leaf_bundle_format_version
            or tree["descriptor_sha256"] != receipt.descriptor_sha256
            or tree["source_byte_count"] != source_byte_count
            or tree["source_sha256"] != receipt.source_sha256
            or tree["split_manifest_sha256"]
            != receipt.split_manifest_sha256
            or tree["allowed_censor_reason_codes"]
            != list(reason_registry.allowed_censor_reason_codes)
            or tree["allowed_exclusion_reason_codes"]
            != list(reason_registry.allowed_exclusion_reason_codes)
        ):
            raise ValueError("bundle envelope differs")
        expected = _keys(tree["expected"], _EXPECTED_LEAF_MEMBER_IDS)
        evidence = _keys(
            expected["expected_evidence_commitment"],
            _EXPECTED_LEAF_WRAPPER_KEYS,
        )
        native = _keys(
            expected["detached_native_observation"],
            _EXPECTED_LEAF_WRAPPER_KEYS,
        )
        if (
            evidence["payload_sha256"] != receipt.expected_evidence_sha256
            or native["payload_sha256"]
            != receipt.expected_native_observation_sha256
        ):
            raise ValueError("bundle committed leaf differs")
    except (ExpectedLeafAuthorityError, TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.BUNDLE_MISMATCH)


def validate_independent_golden_expected_leaf_extension(
    value: _types.IndependentGoldenExpectedLeafExtensionInputV1,
    *,
    base_golden: _base_authority.ValidatedIndependentGoldenReceiptV1,
    approved_case: _types.ApprovedExpectedLeafCaseExpectationV1,
    authority: ValidatedApprovedExpectedLeafAuthorityV1,
    expected_leaf_bundle_bytes: bytes,
) -> ValidatedIndependentGoldenExpectedLeafExtensionV1:
    """Validate one canonical extension against V1, profile, and archive bytes."""

    if (
        type(value)
        is not _types.IndependentGoldenExpectedLeafExtensionInputV1
        or type(base_golden)
        is not _base_authority.ValidatedIndependentGoldenReceiptV1
        or type(approved_case)
        is not _types.ApprovedExpectedLeafCaseExpectationV1
        or type(authority) is not ValidatedApprovedExpectedLeafAuthorityV1
        or type(expected_leaf_bundle_bytes) is not bytes
    ):
        _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
    if (
        type(authority.profile)
        is not _types.ApprovedExpectedLeafAuthorityProfileV1
        or type(authority.parent_authority)
        is not _base_authority.ValidatedApprovedPublicationAuthorityV1
        or type(authority.verifier_closure)
        is not ValidatedExpectedLeafVerifierClosureV1
        or type(authority.verifier_closure.source_archive)
        is not _source_archive.ValidatedSourceArchiveV1
        or type(authority.expected_leaf_archive)
        is not _leaf_archive.ValidatedExpectedLeafArchiveV1
    ):
        _fail(ExpectedLeafAuthorityCode.INPUT_TYPE)
    try:
        _types.IndependentGoldenExpectedLeafExtensionInputV1.__post_init__(
            value
        )
        _types.ApprovedExpectedLeafCaseExpectationV1.__post_init__(
            approved_case
        )
        parsed_profile = parse_approved_expected_leaf_authority_profile(
            authority.profile_bytes
        )
        parent_profile_bytes = _base_authority.approved_profile_bytes(
            authority.parent_authority.profile
        )
    except ExpectedLeafAuthorityError:
        _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)
    if (
        parsed_profile != authority.profile
        or hashlib.sha256(authority.profile_bytes).hexdigest()
        != authority.profile_file_sha256
        or domain_separated_sha256(
            _types.APPROVED_EXPECTED_LEAF_AUTHORITY_PROFILE_DIGEST_DOMAIN,
            authority.profile_bytes,
        )
        != authority.profile_sha256
        or parent_profile_bytes
        != authority.parent_authority.profile_bytes
        or hashlib.sha256(parent_profile_bytes).hexdigest()
        != authority.parent_authority.profile_file_sha256
        or _base_authority.domain_separated_sha256(
            _base_authority.APPROVED_PUBLICATION_PROFILE_DIGEST_DOMAIN,
            parent_profile_bytes,
        )
        != authority.parent_authority.profile_sha256
        or parsed_profile.parent_approved_profile_file_sha256
        != authority.parent_authority.profile_file_sha256
        or parsed_profile.parent_approved_profile_sha256
        != authority.parent_authority.profile_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.PARENT_MISMATCH)
    revalidated_closure = _validate_verifier_closure(
        authority.profile.verifier_closure,
        authority.verifier_closure.verifier_source_inputs,
        parent_authority=authority.parent_authority,
        source_archive_inventory_bytes=(
            authority.verifier_closure.source_archive.inventory_bytes
        ),
        source_archive_bytes=(
            authority.verifier_closure.source_archive.archive_bytes
        ),
    )
    if revalidated_closure != authority.verifier_closure:
        _fail(ExpectedLeafAuthorityCode.VERIFIER_CLOSURE_MISMATCH)
    receipt = parse_independent_golden_expected_leaf_extension(
        value.receipt_bytes
    )
    if receipt != value.receipt:
        _fail(ExpectedLeafAuthorityCode.GOLDEN_MISMATCH)
    receipt_sha256 = domain_separated_sha256(
        _types.INDEPENDENT_GOLDEN_EXPECTED_LEAF_EXTENSION_DIGEST_DOMAIN,
        value.receipt_bytes,
    )
    if (
        approved_case.case_ordinal >= len(
            authority.profile.case_expectations
        )
        or authority.profile.case_expectations[
            approved_case.case_ordinal
        ]
        != approved_case
        or receipt_sha256 != approved_case.golden_extension_sha256
        or receipt.case_ordinal != approved_case.case_ordinal
        or receipt.case_authority_id != approved_case.case_authority_id
        or receipt.expected_leaf_archive_object_id
        != approved_case.expected_leaf_archive_object_id
    ):
        _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)

    base_cases = authority.parent_authority.profile.case_expectations
    if receipt.case_ordinal >= len(base_cases):
        _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)
    base_case = base_cases[receipt.case_ordinal]
    golden = base_golden.receipt
    try:
        rebuilt_base_golden_bytes = (
            _base_authority.independent_golden_receipt_bytes(golden)
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.GOLDEN_MISMATCH)
    if (
        rebuilt_base_golden_bytes != base_golden.receipt_bytes
        or _base_authority.domain_separated_sha256(
            _base_authority.INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN,
            rebuilt_base_golden_bytes,
        )
        != base_golden.receipt_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.GOLDEN_MISMATCH)
    if (
        approved_case.base_case_expectation_sha256
        != approved_case_expectation_sha256(base_case)
        or approved_case.case_authority_id
        != expected_leaf_case_authority_id(base_case)
        or receipt.base_golden_receipt_sha256
        != base_golden.receipt_sha256
        or base_case.independent_golden_receipt_sha256
        != base_golden.receipt_sha256
        or receipt.adapter_id != base_case.adapter_id
        or receipt.adapter_version != base_case.adapter_version
        or receipt.adapter_id != golden.adapter_id
        or receipt.adapter_version != golden.adapter_version
        or receipt.descriptor_sha256 != base_case.descriptor_sha256
        or receipt.descriptor_sha256 != golden.descriptor_sha256
        or receipt.source_sha256 != base_case.source_sha256
        or receipt.source_sha256 != golden.source_sha256
        or receipt.split_manifest_sha256
        != base_case.split_manifest_sha256
        or receipt.split_manifest_sha256
        != golden.split_manifest_sha256
        or receipt.expected_configuration_sha256
        != base_case.expected_configuration_sha256
        or receipt.expected_configuration_sha256
        != golden.expected_configuration_sha256
        or receipt.expected_evidence_sha256
        != base_case.expected_evidence_sha256
        or receipt.expected_evidence_sha256
        != golden.expected_evidence_sha256
        or receipt.expected_native_observation_sha256
        != base_case.native_observation_sha256
        or receipt.expected_native_observation_sha256
        != golden.expected_native_observation_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.GOLDEN_MISMATCH)

    reason_registry = authority.profile.reason_registry
    reason_digests = (
        expected_leaf_reason_registry_sha256(reason_registry),
        expected_leaf_censor_reason_registry_sha256(reason_registry),
        expected_leaf_exclusion_reason_registry_sha256(reason_registry),
    )
    semantic_sha256 = expected_leaf_semantic_profile_sha256(
        authority.profile.semantic_profile
    )
    closure_sha256 = expected_leaf_verifier_closure_sha256(
        authority.profile.verifier_closure
    )
    if (
        receipt.reason_registry_sha256 != reason_digests[0]
        or receipt.censor_reason_registry_sha256 != reason_digests[1]
        or receipt.exclusion_reason_registry_sha256 != reason_digests[2]
        or receipt.semantic_profile_sha256 != semantic_sha256
        or receipt.verifier_closure_sha256 != closure_sha256
        or approved_case.reason_registry_sha256 != reason_digests[0]
        or approved_case.censor_reason_registry_sha256
        != reason_digests[1]
        or approved_case.exclusion_reason_registry_sha256
        != reason_digests[2]
        or approved_case.semantic_profile_sha256 != semantic_sha256
        or approved_case.verifier_closure_sha256 != closure_sha256
        or _archive_identity(receipt) != _archive_identity(approved_case)
        or _archive_identity(receipt) != _archive_identity(authority.profile)
    ):
        _fail(ExpectedLeafAuthorityCode.CASE_MISMATCH)

    for name in (
        "expected_leaf_bundle_artifact_type",
        "expected_leaf_bundle_format_version",
        "expected_leaf_bundle_byte_count",
        "expected_leaf_bundle_file_sha256",
        "expected_leaf_bundle_sha256",
    ):
        if getattr(receipt, name) != getattr(approved_case, name):
            _fail(ExpectedLeafAuthorityCode.BUNDLE_MISMATCH)
    _validate_bundle_envelope(
        expected_leaf_bundle_bytes,
        receipt,
        reason_registry,
        source_byte_count=golden.source_byte_count,
    )
    try:
        archived_bundle = _leaf_archive.resolve_expected_leaf_archive_object(
            authority.expected_leaf_archive.inventory_bytes,
            authority.expected_leaf_archive.archive_bytes,
            role_id=_leaf_archive.EXPECTED_LEAF_ARCHIVE_ROLE_ID,
            case_authority_id=receipt.case_authority_id,
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityCode.ARCHIVE_MISMATCH)
    membership = archived_bundle.membership
    if (
        archived_bundle.expected_leaf_archive
        != authority.expected_leaf_archive
        or archived_bundle.bundle_bytes != expected_leaf_bundle_bytes
        or membership.case_authority_id != receipt.case_authority_id
        or membership.bundle_byte_count
        != receipt.expected_leaf_bundle_byte_count
        or membership.bundle_plain_sha256
        != receipt.expected_leaf_bundle_file_sha256
        or membership.bundle_domain_sha256
        != receipt.expected_leaf_bundle_sha256
        or membership.archive_sha256
        != receipt.expected_leaf_archive_sha256
        or membership.inventory_file_sha256
        != receipt.expected_leaf_archive_inventory_file_sha256
        or membership.inventory_sha256
        != receipt.expected_leaf_archive_inventory_sha256
    ):
        _fail(ExpectedLeafAuthorityCode.ARCHIVE_MISMATCH)
    return ValidatedIndependentGoldenExpectedLeafExtensionV1(
        receipt=receipt,
        receipt_bytes=value.receipt_bytes,
        receipt_sha256=receipt_sha256,
        base_golden=base_golden,
        approved_case=approved_case,
        archived_bundle=archived_bundle,
    )


__all__ = [
    "APPROVED_CASE_EXPECTATION_DIGEST_DOMAIN",
    "APPROVED_EXPECTED_LEAF_CASE_EXPECTATION_DIGEST_DOMAIN",
    "EXPECTED_LEAF_CASE_AUTHORITY_ID_DIGEST_DOMAIN",
    "ExpectedLeafAuthorityCode",
    "ExpectedLeafAuthorityError",
    "MAXIMUM_EXPECTED_LEAF_AUTHORITY_JSON_DEPTH",
    "MAXIMUM_EXPECTED_LEAF_AUTHORITY_JSON_NODES",
    "MAXIMUM_EXPECTED_LEAF_AUTHORITY_STRING_BYTES",
    "ValidatedApprovedExpectedLeafAuthorityV1",
    "ValidatedExpectedLeafVerifierClosureV1",
    "ValidatedIndependentGoldenExpectedLeafExtensionV1",
    "approved_case_expectation_bytes",
    "approved_case_expectation_sha256",
    "approved_case_expectation_tree",
    "approved_expected_leaf_authority_profile_bytes",
    "approved_expected_leaf_authority_profile_sha256",
    "approved_expected_leaf_authority_profile_tree",
    "approved_expected_leaf_case_expectation_bytes",
    "approved_expected_leaf_case_expectation_sha256",
    "approved_expected_leaf_case_expectation_tree",
    "domain_separated_sha256",
    "expected_leaf_case_authority_id",
    "expected_leaf_censor_reason_registry_sha256",
    "expected_leaf_exclusion_reason_registry_sha256",
    "expected_leaf_reason_registry_bytes",
    "expected_leaf_reason_registry_sha256",
    "expected_leaf_reason_registry_tree",
    "expected_leaf_semantic_profile_bytes",
    "expected_leaf_semantic_profile_sha256",
    "expected_leaf_semantic_profile_tree",
    "expected_leaf_verifier_closure_bytes",
    "expected_leaf_verifier_closure_sha256",
    "expected_leaf_verifier_closure_tree",
    "independent_golden_expected_leaf_extension_bytes",
    "independent_golden_expected_leaf_extension_sha256",
    "independent_golden_expected_leaf_extension_tree",
    "parse_approved_expected_leaf_authority_profile",
    "parse_independent_golden_expected_leaf_extension",
    "validate_approved_expected_leaf_authority",
    "validate_independent_golden_expected_leaf_extension",
]
