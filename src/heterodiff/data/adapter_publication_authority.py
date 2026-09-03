"""Write-free validation of independently custodied publication authority.

This is the publisher-side authority implementation.  It strict-parses exact
profile, oracle-registry, and golden-receipt bytes and authenticates profile
bytes against an out-of-band anchor.  It does not access paths, invoke an
adapter or oracle, serialize publication artifacts, write files, or decide the
adapter gate.  A future verifier must implement these schemas independently.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import NamedTuple, Tuple

from .adapter_publication_authority_types import (
    APPROVED_PUBLICATION_PROFILE_ARTIFACT_TYPE,
    APPROVED_PUBLICATION_PROFILE_ID,
    APPROVED_PUBLICATION_STATUS,
    DECISION_EXECUTION_GUARD_RECEIPT_ARTIFACT_TYPE,
    DECISION_EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE,
    DECISION_EXECUTION_INPUT_SET_ARTIFACT_TYPE,
    GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE,
    INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE,
    ApprovedCaseExpectationV1,
    ApprovedExecutionPolicyV1,
    ApprovedPublicationAuthorityInputV1,
    ApprovedPublicationProfileV1,
    GoldenOracleRegistryEntryV1,
    GoldenOracleRegistryV1,
    HostileControlRequirementV1,
    IndependentGoldenReceiptInputV1,
    IndependentGoldenReceiptV1,
    MAXIMUM_APPROVED_PROFILE_BYTES,
    MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES,
    PublicationBindingExpectationV1,
    PublicationBindingSetV1,
)
from . import adapter_publication_payloads as _payloads
from .adapter_publication_types import (
    PublicIdentifierRegistryV1,
    PublicationBindingInputV1,
    PublicationTypeError,
)


APPROVED_PUBLICATION_PROFILE_DIGEST_DOMAIN = (
    APPROVED_PUBLICATION_PROFILE_ARTIFACT_TYPE
)
PUBLICATION_BINDINGS_DIGEST_DOMAIN = (
    "heterodiff.adapter.publication-bindings.v1"
)
INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN = (
    INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE
)

MAXIMUM_AUTHORITY_JSON_DEPTH = 32
MAXIMUM_AUTHORITY_JSON_TOKENS = 200_000
MAXIMUM_AUTHORITY_STRING_TOKEN_BYTES = 512 * 1024
_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1


class PublicationAuthorityCode(str, Enum):
    """Closed, interpolation-free authority validation failures."""

    AUTH_INPUT_TYPE = "AUTH_INPUT_TYPE"
    AUTH_PROFILE_SIZE = "AUTH_PROFILE_SIZE"
    AUTH_PROFILE_JSON = "AUTH_PROFILE_JSON"
    AUTH_PROFILE_NONCANONICAL = "AUTH_PROFILE_NONCANONICAL"
    AUTH_PROFILE_SCHEMA = "AUTH_PROFILE_SCHEMA"
    AUTH_ANCHOR_MISMATCH = "AUTH_ANCHOR_MISMATCH"
    AUTH_BINDING_MISMATCH = "AUTH_BINDING_MISMATCH"
    AUTH_EXECUTION_INVOCATION_MISMATCH = (
        "AUTH_EXECUTION_INVOCATION_MISMATCH"
    )
    AUTH_GOLDEN_MISMATCH = "AUTH_GOLDEN_MISMATCH"
    AUTH_ORACLE_REGISTRY_MISMATCH = "AUTH_ORACLE_REGISTRY_MISMATCH"


_ERROR_MESSAGES = MappingProxyType(
    {
        PublicationAuthorityCode.AUTH_INPUT_TYPE: (
            "publication authority input is invalid"
        ),
        PublicationAuthorityCode.AUTH_PROFILE_SIZE: (
            "publication authority bytes exceed their ceiling"
        ),
        PublicationAuthorityCode.AUTH_PROFILE_JSON: (
            "publication authority JSON is invalid"
        ),
        PublicationAuthorityCode.AUTH_PROFILE_NONCANONICAL: (
            "publication authority JSON is not canonical"
        ),
        PublicationAuthorityCode.AUTH_PROFILE_SCHEMA: (
            "publication authority schema is invalid"
        ),
        PublicationAuthorityCode.AUTH_ANCHOR_MISMATCH: (
            "publication authority does not match its external anchor"
        ),
        PublicationAuthorityCode.AUTH_BINDING_MISMATCH: (
            "publication bindings do not match approved authority"
        ),
        PublicationAuthorityCode.AUTH_EXECUTION_INVOCATION_MISMATCH: (
            "execution invocation does not match approved authority"
        ),
        PublicationAuthorityCode.AUTH_GOLDEN_MISMATCH: (
            "independent golden receipt does not match its typed input"
        ),
        PublicationAuthorityCode.AUTH_ORACLE_REGISTRY_MISMATCH: (
            "independent golden oracle does not match its registry"
        ),
    }
)


class PublicationAuthorityError(ValueError):
    """One fixed coded authority failure with no untrusted interpolation."""

    def __init__(self, code: PublicationAuthorityCode) -> None:
        if type(code) is not PublicationAuthorityCode:
            raise TypeError("publication authority code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class ValidatedApprovedPublicationAuthorityV1(NamedTuple):
    """Validated exact profile and the two independently checked digests."""

    profile: ApprovedPublicationProfileV1
    profile_bytes: bytes
    profile_file_sha256: str
    profile_sha256: str


class ValidatedIndependentGoldenReceiptV1(NamedTuple):
    """Canonical golden receipt whose exact oracle source is registry-bound."""

    receipt: IndependentGoldenReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str
    oracle_source_bytes: bytes


class ValidatedPublicationBindingAuthorityV1(NamedTuple):
    """Authenticated profile plus its exact final 19-field binding set."""

    authority: ValidatedApprovedPublicationAuthorityV1
    binding_set: PublicationBindingSetV1
    binding_set_bytes: bytes
    binding_set_sha256: str


def _fail(code: PublicationAuthorityCode) -> None:
    raise PublicationAuthorityError(code) from None


def domain_separated_sha256(domain: str, payload: bytes) -> str:
    if type(domain) is not str or type(payload) is not bytes:
        raise TypeError("domain digest inputs must have exact types")
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        raise TypeError("digest domain must be ASCII") from None
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _validate_tree(value: object) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_AUTHORITY_JSON_TOKENS:
            raise PublicationTypeError("authority tree has too many values")
        if depth > MAXIMUM_AUTHORITY_JSON_DEPTH:
            raise PublicationTypeError("authority tree is too deeply nested")
        if current is None or type(current) in (bool, int, str):
            if current is None:
                raise PublicationTypeError("authority tree does not admit null")
            if type(current) is int and (
                current < 0 or current > _MAXIMUM_SAFE_INTEGER
            ):
                raise PublicationTypeError(
                    "authority integer is outside the exact range"
                )
            if type(current) is str:
                try:
                    encoded = current.encode("utf-8", "strict")
                except UnicodeError:
                    raise PublicationTypeError(
                        "authority string is invalid Unicode"
                    ) from None
                if len(encoded) > MAXIMUM_AUTHORITY_STRING_TOKEN_BYTES:
                    raise PublicationTypeError(
                        "authority string exceeds its token ceiling"
                    )
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    raise PublicationTypeError(
                        "authority object key must be a string"
                    )
                stack.append((item, depth + 1))
                stack.append((key, depth + 1))
            continue
        raise PublicationTypeError("authority tree contains an invalid type")


def _canonical_bytes(value: object, *, maximum: int) -> bytes:
    _validate_tree(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise PublicationTypeError(
            "authority tree cannot be encoded canonically"
        ) from error
    if not encoded or len(encoded) > maximum:
        raise PublicationTypeError("authority bytes exceed their ceiling")
    return encoded


def _lexical_preflight(value: bytes, *, maximum: int) -> None:
    if type(value) is not bytes:
        raise TypeError("authority bytes must be exact")
    if not value or len(value) > maximum:
        _fail(PublicationAuthorityCode.AUTH_PROFILE_SIZE)
    if any(byte >= 0x80 for byte in value):
        _fail(PublicationAuthorityCode.AUTH_PROFILE_JSON)
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            string_bytes += 1
            if string_bytes > MAXIMUM_AUTHORITY_STRING_TOKEN_BYTES:
                _fail(PublicationAuthorityCode.AUTH_PROFILE_SIZE)
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
            tokens += 1
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAXIMUM_AUTHORITY_JSON_DEPTH:
                _fail(PublicationAuthorityCode.AUTH_PROFILE_JSON)
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _fail(PublicationAuthorityCode.AUTH_PROFILE_JSON)
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAXIMUM_AUTHORITY_JSON_TOKENS:
            _fail(PublicationAuthorityCode.AUTH_PROFILE_SIZE)
    if in_string or depth != 0:
        _fail(PublicationAuthorityCode.AUTH_PROFILE_JSON)


def _strict_tree(value: bytes, *, maximum: int) -> object:
    _lexical_preflight(value, maximum=maximum)
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(PublicationAuthorityCode.AUTH_PROFILE_JSON)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise PublicationTypeError("duplicate authority key")
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise PublicationTypeError("authority integer token is too large")
        result = int(token, 10)
        if result < 0 or result > _MAXIMUM_SAFE_INTEGER:
            raise PublicationTypeError("authority integer is outside range")
        return result

    def reject_number(_token):
        raise PublicationTypeError("authority JSON admits integers only")

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
        _validate_tree(tree)
    except (PublicationTypeError, TypeError, ValueError, RecursionError):
        _fail(PublicationAuthorityCode.AUTH_PROFILE_JSON)
    try:
        canonical = _canonical_bytes(tree, maximum=maximum)
    except (PublicationTypeError, TypeError):
        _fail(PublicationAuthorityCode.AUTH_PROFILE_JSON)
    if canonical != value:
        _fail(PublicationAuthorityCode.AUTH_PROFILE_NONCANONICAL)
    return tree


def _keys(value: object, expected: Tuple[str, ...]) -> dict:
    if type(value) is not dict or tuple(sorted(value)) != tuple(sorted(expected)):
        raise PublicationTypeError("authority object has an invalid key set")
    return value


_BINDING_KEYS = (
    "a9_1_sha256",
    "contract_core_sha256",
    "contract_id",
    "dependency_lock_sha256",
    "environment_manifest_sha256",
    "execution_guard_source_sha256",
    "gate_id",
    "gate_spec_sha256",
    "interpreter_executable_sha256",
    "oracle_registry_sha256",
    "phase_c_report_sha256",
    "phase_d_spec_sha256",
    "public_id_registry_sha256",
    "publisher_source_sha256",
    "source_tree_archive_sha256",
    "source_tree_manifest_sha256",
    "test_inventory_sha256",
    "verifier_source_sha256",
)
_CASE_KEYS = (
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
_HOSTILE_KEYS = (
    "attack_kind_id",
    "control_id",
    "error_code",
    "expected_stage_id",
    "hostile_control_receipt_sha256",
    "input_sha256",
    "origin_class_id",
    "sink_field_id",
    "status_id",
    "test_node_sha256",
)
_POLICY_KEYS = (
    "address_space_limit_bytes",
    "address_space_limit_method_id",
    "allowed_execution_status_ids",
    "argv_sha256",
    "authorized_write_root_sha256",
    "clock_method_id",
    "containment_policy_sha256",
    "cwd_launch_method_id",
    "decision_eligible_required",
    "environment_sha256",
    "execution_backend_id",
    "filesystem_confinement_id",
    "guard_implementation_status_id",
    "managed_process_group_quiescence_required",
    "output_capture_method_id",
    "output_complete_required",
    "output_limit_bytes",
    "peak_rss_limit_bytes",
    "peak_rss_method_id",
    "process_containment_id",
    "source_binding_format_id",
    "wall_time_limit_nanoseconds",
    "working_directory_sha256",
)
_PROFILE_KEYS = (
    "a9_1_byte_count",
    "approval_status_id",
    "artifact_type",
    "binding_expectations",
    "case_expectations",
    "execution_policy",
    "format_version",
    "hostile_control_expectations",
    "profile_id",
)
_GOLDEN_KEYS = (
    "adapter_id",
    "adapter_version",
    "artifact_type",
    "descriptor_sha256",
    "expected_configuration_payload_byte_count",
    "expected_configuration_sha256",
    "expected_evidence_sha256",
    "expected_native_observation_sha256",
    "format_version",
    "oracle_id",
    "oracle_registry_sha256",
    "oracle_source_byte_count",
    "oracle_source_sha256",
    "source_byte_count",
    "source_sha256",
    "split_manifest_sha256",
)
_ORACLE_ENTRY_KEYS = (
    "forbidden_import_ids",
    "forbidden_name_ids",
    "oracle_id",
    "oracle_source_byte_count",
    "oracle_source_sha256",
)
_ORACLE_REGISTRY_KEYS = ("artifact_type", "format_version", "oracles")


def binding_expectation_tree(value: PublicationBindingExpectationV1) -> dict:
    if type(value) is not PublicationBindingExpectationV1:
        raise TypeError("binding expectation must be exact")
    return {name: getattr(value, name) for name in _BINDING_KEYS}


def publication_binding_set_tree(value: PublicationBindingSetV1) -> dict:
    if type(value) is not PublicationBindingSetV1:
        raise TypeError("publication binding set must be exact")
    result = {name: getattr(value, name) for name in _BINDING_KEYS}
    result["approved_profile_sha256"] = value.approved_profile_sha256
    return result


def _case_tree(value: ApprovedCaseExpectationV1) -> dict:
    if type(value) is not ApprovedCaseExpectationV1:
        raise TypeError("case expectation must be exact")
    return {name: getattr(value, name) for name in _CASE_KEYS}


def _hostile_tree(value: HostileControlRequirementV1) -> dict:
    if type(value) is not HostileControlRequirementV1:
        raise TypeError("hostile expectation must be exact")
    return {name: getattr(value, name) for name in _HOSTILE_KEYS}


def _policy_tree(value: ApprovedExecutionPolicyV1) -> dict:
    if type(value) is not ApprovedExecutionPolicyV1:
        raise TypeError("execution policy must be exact")
    return {
        name: (
            list(value.allowed_execution_status_ids)
            if name == "allowed_execution_status_ids"
            else getattr(value, name)
        )
        for name in _POLICY_KEYS
    }


def approved_profile_tree(value: ApprovedPublicationProfileV1) -> dict:
    if type(value) is not ApprovedPublicationProfileV1:
        raise TypeError("approved profile must be exact")
    return {
        "a9_1_byte_count": value.a9_1_byte_count,
        "approval_status_id": value.approval_status_id,
        "artifact_type": value.artifact_type,
        "binding_expectations": binding_expectation_tree(
            value.binding_expectations
        ),
        "case_expectations": [_case_tree(item) for item in value.case_expectations],
        "execution_policy": _policy_tree(value.execution_policy),
        "format_version": value.format_version,
        "hostile_control_expectations": [
            _hostile_tree(item) for item in value.hostile_control_expectations
        ],
        "profile_id": value.profile_id,
    }


def independent_golden_receipt_tree(
    value: IndependentGoldenReceiptV1,
) -> dict:
    if type(value) is not IndependentGoldenReceiptV1:
        raise TypeError("independent golden receipt must be exact")
    return {name: getattr(value, name) for name in _GOLDEN_KEYS}


def golden_oracle_registry_tree(value: GoldenOracleRegistryV1) -> dict:
    if type(value) is not GoldenOracleRegistryV1:
        raise TypeError("golden oracle registry must be exact")
    return {
        "artifact_type": value.artifact_type,
        "format_version": value.format_version,
        "oracles": [
            {
                "forbidden_import_ids": list(item.forbidden_import_ids),
                "forbidden_name_ids": list(item.forbidden_name_ids),
                "oracle_id": item.oracle_id,
                "oracle_source_byte_count": item.oracle_source_byte_count,
                "oracle_source_sha256": item.oracle_source_sha256,
            }
            for item in value.oracles
        ],
    }


def approved_profile_bytes(value: ApprovedPublicationProfileV1) -> bytes:
    return _canonical_bytes(
        approved_profile_tree(value),
        maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
    )


def publication_binding_set_bytes(value: PublicationBindingSetV1) -> bytes:
    return _canonical_bytes(
        publication_binding_set_tree(value),
        maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
    )


def independent_golden_receipt_bytes(
    value: IndependentGoldenReceiptV1,
) -> bytes:
    return _canonical_bytes(
        independent_golden_receipt_tree(value),
        maximum=MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES,
    )


def golden_oracle_registry_bytes(value: GoldenOracleRegistryV1) -> bytes:
    return _canonical_bytes(
        golden_oracle_registry_tree(value),
        maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
    )


def _binding_from_tree(value: object) -> PublicationBindingExpectationV1:
    tree = _keys(value, _BINDING_KEYS)
    return PublicationBindingExpectationV1(**tree)


def _case_from_tree(value: object) -> ApprovedCaseExpectationV1:
    tree = _keys(value, _CASE_KEYS)
    return ApprovedCaseExpectationV1(**tree)


def _hostile_from_tree(value: object) -> HostileControlRequirementV1:
    tree = _keys(value, _HOSTILE_KEYS)
    return HostileControlRequirementV1(**tree)


def _policy_from_tree(value: object) -> ApprovedExecutionPolicyV1:
    tree = _keys(value, _POLICY_KEYS)
    if tree["decision_eligible_required"] is not True:
        raise PublicationTypeError("decision eligibility must be required")
    if tree["managed_process_group_quiescence_required"] is not True:
        raise PublicationTypeError("process quiescence must be required")
    if tree["output_complete_required"] is not True:
        raise PublicationTypeError("complete output must be required")
    fixed = ApprovedExecutionPolicyV1(
        **{
            name: (
                tuple(tree[name])
                if name == "allowed_execution_status_ids"
                and type(tree[name]) is list
                else tree[name]
            )
            for name in ApprovedExecutionPolicyV1.__dataclass_fields__
            if ApprovedExecutionPolicyV1.__dataclass_fields__[name].init
        }
    )
    for name in (
        "output_limit_bytes",
        "peak_rss_limit_bytes",
        "wall_time_limit_nanoseconds",
    ):
        if tree[name] != getattr(fixed, name):
            raise PublicationTypeError("execution policy fixed ceiling differs")
    return fixed


def _profile_from_tree(value: object) -> ApprovedPublicationProfileV1:
    tree = _keys(value, _PROFILE_KEYS)
    if tree["approval_status_id"] != APPROVED_PUBLICATION_STATUS:
        raise PublicationTypeError("profile approval status differs")
    if tree["artifact_type"] != APPROVED_PUBLICATION_PROFILE_ARTIFACT_TYPE:
        raise PublicationTypeError("profile artifact type differs")
    if tree["format_version"] != "1":
        raise PublicationTypeError("profile format version differs")
    if tree["profile_id"] != APPROVED_PUBLICATION_PROFILE_ID:
        raise PublicationTypeError("profile identifier differs")
    if type(tree["case_expectations"]) is not list:
        raise PublicationTypeError("case expectations must be a list")
    if type(tree["hostile_control_expectations"]) is not list:
        raise PublicationTypeError("hostile expectations must be a list")
    return ApprovedPublicationProfileV1(
        a9_1_byte_count=tree["a9_1_byte_count"],
        binding_expectations=_binding_from_tree(tree["binding_expectations"]),
        case_expectations=tuple(
            _case_from_tree(item) for item in tree["case_expectations"]
        ),
        execution_policy=_policy_from_tree(tree["execution_policy"]),
        hostile_control_expectations=tuple(
            _hostile_from_tree(item)
            for item in tree["hostile_control_expectations"]
        ),
    )


def _golden_from_tree(value: object) -> IndependentGoldenReceiptV1:
    tree = _keys(value, _GOLDEN_KEYS)
    if tree["artifact_type"] != INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE:
        raise PublicationTypeError("golden artifact type differs")
    if tree["format_version"] != "1":
        raise PublicationTypeError("golden format version differs")
    return IndependentGoldenReceiptV1(
        **{
            name: tree[name]
            for name in IndependentGoldenReceiptV1.__dataclass_fields__
            if IndependentGoldenReceiptV1.__dataclass_fields__[name].init
        }
    )


def _oracle_registry_from_tree(value: object) -> GoldenOracleRegistryV1:
    tree = _keys(value, _ORACLE_REGISTRY_KEYS)
    if tree["artifact_type"] != GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE:
        raise PublicationTypeError("oracle registry artifact type differs")
    if tree["format_version"] != "1":
        raise PublicationTypeError("oracle registry format version differs")
    if type(tree["oracles"]) is not list:
        raise PublicationTypeError("oracle entries must be a list")
    entries = []
    for value in tree["oracles"]:
        entry = _keys(value, _ORACLE_ENTRY_KEYS)
        if type(entry["forbidden_import_ids"]) is not list:
            raise PublicationTypeError("forbidden imports must be a list")
        if type(entry["forbidden_name_ids"]) is not list:
            raise PublicationTypeError("forbidden names must be a list")
        entries.append(
            GoldenOracleRegistryEntryV1(
                oracle_id=entry["oracle_id"],
                oracle_source_byte_count=entry["oracle_source_byte_count"],
                oracle_source_sha256=entry["oracle_source_sha256"],
                forbidden_import_ids=tuple(entry["forbidden_import_ids"]),
                forbidden_name_ids=tuple(entry["forbidden_name_ids"]),
            )
        )
    return GoldenOracleRegistryV1(tuple(entries))


def validate_approved_publication_authority(
    value: ApprovedPublicationAuthorityInputV1,
) -> ValidatedApprovedPublicationAuthorityV1:
    """Authenticate exact canonical profile bytes against an external anchor."""

    if type(value) is not ApprovedPublicationAuthorityInputV1:
        _fail(PublicationAuthorityCode.AUTH_INPUT_TYPE)
    profile_bytes = value.profile_bytes
    anchor = value.anchor
    if len(profile_bytes) != anchor.profile_byte_count:
        _fail(PublicationAuthorityCode.AUTH_ANCHOR_MISMATCH)
    file_sha256 = hashlib.sha256(profile_bytes).hexdigest()
    profile_sha256 = domain_separated_sha256(
        APPROVED_PUBLICATION_PROFILE_DIGEST_DOMAIN,
        profile_bytes,
    )
    if (
        file_sha256 != anchor.profile_file_sha256
        or profile_sha256 != anchor.profile_sha256
    ):
        _fail(PublicationAuthorityCode.AUTH_ANCHOR_MISMATCH)
    tree = _strict_tree(
        profile_bytes,
        maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
    )
    try:
        profile = _profile_from_tree(tree)
        if approved_profile_bytes(profile) != profile_bytes:
            raise PublicationTypeError("profile projection differs")
    except (PublicationTypeError, TypeError, ValueError):
        _fail(PublicationAuthorityCode.AUTH_PROFILE_SCHEMA)
    return ValidatedApprovedPublicationAuthorityV1(
        profile=profile,
        profile_bytes=profile_bytes,
        profile_file_sha256=file_sha256,
        profile_sha256=profile_sha256,
    )


def validate_golden_oracle_registry(value: bytes) -> GoldenOracleRegistryV1:
    """Strict-parse exact canonical oracle-registry bytes."""

    tree = _strict_tree(value, maximum=MAXIMUM_APPROVED_PROFILE_BYTES)
    try:
        registry = _oracle_registry_from_tree(tree)
        if golden_oracle_registry_bytes(registry) != value:
            raise PublicationTypeError("oracle registry projection differs")
    except (PublicationTypeError, TypeError, ValueError):
        _fail(PublicationAuthorityCode.AUTH_ORACLE_REGISTRY_MISMATCH)
    return registry


def validate_independent_golden_receipt(
    value: IndependentGoldenReceiptInputV1,
    *,
    oracle_registry_bytes: bytes,
) -> ValidatedIndependentGoldenReceiptV1:
    """Validate receipt bytes and bind its exact oracle source to the registry."""

    if type(value) is not IndependentGoldenReceiptInputV1:
        _fail(PublicationAuthorityCode.AUTH_INPUT_TYPE)
    tree = _strict_tree(
        value.receipt_bytes,
        maximum=MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES,
    )
    try:
        parsed = _golden_from_tree(tree)
        expected_bytes = independent_golden_receipt_bytes(value.receipt)
        if parsed != value.receipt or expected_bytes != value.receipt_bytes:
            raise PublicationTypeError("golden receipt projection differs")
    except (PublicationTypeError, TypeError, ValueError):
        _fail(PublicationAuthorityCode.AUTH_GOLDEN_MISMATCH)
    registry = validate_golden_oracle_registry(oracle_registry_bytes)
    if parsed.oracle_registry_sha256 != hashlib.sha256(
        oracle_registry_bytes
    ).hexdigest():
        _fail(PublicationAuthorityCode.AUTH_ORACLE_REGISTRY_MISMATCH)
    entries = tuple(
        item for item in registry.oracles if item.oracle_id == parsed.oracle_id
    )
    if len(entries) != 1:
        _fail(PublicationAuthorityCode.AUTH_ORACLE_REGISTRY_MISMATCH)
    entry = entries[0]
    source_sha256 = hashlib.sha256(value.oracle_source_bytes).hexdigest()
    if (
        len(value.oracle_source_bytes) != parsed.oracle_source_byte_count
        or source_sha256 != parsed.oracle_source_sha256
        or entry.oracle_source_byte_count != parsed.oracle_source_byte_count
        or entry.oracle_source_sha256 != parsed.oracle_source_sha256
    ):
        _fail(PublicationAuthorityCode.AUTH_ORACLE_REGISTRY_MISMATCH)
    receipt_sha256 = domain_separated_sha256(
        INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN,
        value.receipt_bytes,
    )
    return ValidatedIndependentGoldenReceiptV1(
        receipt=parsed,
        receipt_bytes=value.receipt_bytes,
        receipt_sha256=receipt_sha256,
        oracle_source_bytes=value.oracle_source_bytes,
    )


def publication_binding_set(
    expectation: PublicationBindingExpectationV1,
    *,
    approved_profile_sha256: str,
) -> PublicationBindingSetV1:
    """Add only a validated external profile digest to the 18 expectations."""

    if type(expectation) is not PublicationBindingExpectationV1:
        raise TypeError("binding expectation must be exact")
    return PublicationBindingSetV1(
        approved_profile_sha256=approved_profile_sha256,
        **{
            name: getattr(expectation, name)
            for name in PublicationBindingExpectationV1.__dataclass_fields__
        },
    )


def publication_binding_set_sha256(value: PublicationBindingSetV1) -> str:
    """Return the domain digest of the exact final 19-field binding set."""

    return domain_separated_sha256(
        PUBLICATION_BINDINGS_DIGEST_DOMAIN,
        publication_binding_set_bytes(value),
    )


def validate_approved_profile_registry(
    profile: ApprovedPublicationProfileV1,
    public_ids: PublicIdentifierRegistryV1,
) -> None:
    """Require every profile-selected V1 value in its bound ID category."""

    if type(profile) is not ApprovedPublicationProfileV1:
        _fail(PublicationAuthorityCode.AUTH_INPUT_TYPE)
    if type(public_ids) is not PublicIdentifierRegistryV1:
        _fail(PublicationAuthorityCode.AUTH_INPUT_TYPE)
    required_artifacts = (
        APPROVED_PUBLICATION_PROFILE_ARTIFACT_TYPE,
        DECISION_EXECUTION_GUARD_RECEIPT_ARTIFACT_TYPE,
        DECISION_EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE,
        DECISION_EXECUTION_INPUT_SET_ARTIFACT_TYPE,
        GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE,
        INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE,
    )
    policy = profile.execution_policy
    policy_categories = (
        (
            policy.address_space_limit_method_id,
            public_ids.address_space_limit_method_ids,
        ),
        (policy.clock_method_id, public_ids.wall_time_method_ids),
        (policy.cwd_launch_method_id, public_ids.cwd_launch_method_ids),
        (policy.execution_backend_id, public_ids.execution_backend_ids),
        (
            policy.filesystem_confinement_id,
            public_ids.filesystem_confinement_ids,
        ),
        (
            policy.guard_implementation_status_id,
            public_ids.guard_implementation_status_ids,
        ),
        (
            policy.output_capture_method_id,
            public_ids.output_capture_method_ids,
        ),
        (policy.peak_rss_method_id, public_ids.peak_rss_method_ids),
        (
            policy.process_containment_id,
            public_ids.process_containment_ids,
        ),
        (
            policy.source_binding_format_id,
            public_ids.source_binding_format_ids,
        ),
    )
    adapter_identities = {
        (item.adapter_id, item.adapter_version)
        for item in public_ids.adapter_identities
    }
    invalid = (
        any(item not in public_ids.artifact_ids for item in required_artifacts)
        or any(
            item not in public_ids.execution_status_ids
            for item in policy.allowed_execution_status_ids
        )
        or any(item not in category for item, category in policy_categories)
        or any(
            (item.adapter_id, item.adapter_version) not in adapter_identities
            for item in profile.case_expectations
        )
        or any(
            item.control_id not in public_ids.hostile_control_ids
            or item.error_code not in public_ids.rejection_code_ids
            or item.status_id not in public_ids.hostile_status_ids
            for item in profile.hostile_control_expectations
        )
    )
    if invalid:
        _fail(PublicationAuthorityCode.AUTH_BINDING_MISMATCH)


def validate_publication_binding_authority(
    bindings: PublicationBindingInputV1,
    public_ids: PublicIdentifierRegistryV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
) -> ValidatedPublicationBindingAuthorityV1:
    """Authenticate all 18 request-derived bindings before any callback."""

    if type(bindings) is not PublicationBindingInputV1:
        _fail(PublicationAuthorityCode.AUTH_INPUT_TYPE)
    if type(public_ids) is not PublicIdentifierRegistryV1:
        _fail(PublicationAuthorityCode.AUTH_INPUT_TYPE)
    authority = validate_approved_publication_authority(authority_input)
    try:
        registry_payload = _payloads.public_identifier_registry_payload(
            public_ids
        )
        if registry_payload.canonical_json_bytes != bindings.public_id_registry_bytes:
            raise PublicationTypeError("registry bytes differ")
        if len(public_ids.contract_ids) != 1 or len(public_ids.gate_ids) != 1:
            raise PublicationTypeError("selected IDs are not singular")
        expectation = PublicationBindingExpectationV1(
            a9_1_sha256=hashlib.sha256(bindings.a9_1_bytes).hexdigest(),
            contract_core_sha256=hashlib.sha256(
                bindings.contract_core_bytes
            ).hexdigest(),
            contract_id=public_ids.contract_ids[0],
            dependency_lock_sha256=hashlib.sha256(
                bindings.dependency_lock_bytes
            ).hexdigest(),
            environment_manifest_sha256=hashlib.sha256(
                bindings.environment_manifest_bytes
            ).hexdigest(),
            execution_guard_source_sha256=hashlib.sha256(
                bindings.execution_guard_source_bytes
            ).hexdigest(),
            gate_id=public_ids.gate_ids[0],
            gate_spec_sha256=hashlib.sha256(
                bindings.gate_spec_bytes
            ).hexdigest(),
            interpreter_executable_sha256=hashlib.sha256(
                bindings.interpreter_executable_bytes
            ).hexdigest(),
            oracle_registry_sha256=hashlib.sha256(
                bindings.oracle_registry_bytes
            ).hexdigest(),
            phase_c_report_sha256=hashlib.sha256(
                bindings.phase_c_report_bytes
            ).hexdigest(),
            phase_d_spec_sha256=hashlib.sha256(
                bindings.phase_d_spec_bytes
            ).hexdigest(),
            public_id_registry_sha256=registry_payload.payload_sha256,
            publisher_source_sha256=hashlib.sha256(
                bindings.publisher_source_bytes
            ).hexdigest(),
            source_tree_archive_sha256=hashlib.sha256(
                bindings.source_tree_archive_bytes
            ).hexdigest(),
            source_tree_manifest_sha256=hashlib.sha256(
                bindings.source_tree_manifest_bytes
            ).hexdigest(),
            test_inventory_sha256=domain_separated_sha256(
                "heterodiff.adapter.test-inventory.v1",
                bindings.test_inventory_bytes,
            ),
            verifier_source_sha256=hashlib.sha256(
                bindings.verifier_source_bytes
            ).hexdigest(),
        )
    except (PublicationTypeError, TypeError, ValueError):
        _fail(PublicationAuthorityCode.AUTH_BINDING_MISMATCH)
    if (
        authority.profile.a9_1_byte_count != len(bindings.a9_1_bytes)
        or authority.profile.binding_expectations != expectation
    ):
        _fail(PublicationAuthorityCode.AUTH_BINDING_MISMATCH)
    binding_set = publication_binding_set(
        expectation,
        approved_profile_sha256=authority.profile_sha256,
    )
    encoded = publication_binding_set_bytes(binding_set)
    return ValidatedPublicationBindingAuthorityV1(
        authority=authority,
        binding_set=binding_set,
        binding_set_bytes=encoded,
        binding_set_sha256=domain_separated_sha256(
            PUBLICATION_BINDINGS_DIGEST_DOMAIN,
            encoded,
        ),
    )


__all__ = [
    "APPROVED_PUBLICATION_PROFILE_DIGEST_DOMAIN",
    "INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN",
    "MAXIMUM_AUTHORITY_JSON_DEPTH",
    "MAXIMUM_AUTHORITY_JSON_TOKENS",
    "MAXIMUM_AUTHORITY_STRING_TOKEN_BYTES",
    "PUBLICATION_BINDINGS_DIGEST_DOMAIN",
    "PublicationAuthorityCode",
    "PublicationAuthorityError",
    "ValidatedApprovedPublicationAuthorityV1",
    "ValidatedIndependentGoldenReceiptV1",
    "ValidatedPublicationBindingAuthorityV1",
    "approved_profile_bytes",
    "approved_profile_tree",
    "binding_expectation_tree",
    "domain_separated_sha256",
    "golden_oracle_registry_bytes",
    "golden_oracle_registry_tree",
    "independent_golden_receipt_bytes",
    "independent_golden_receipt_tree",
    "publication_binding_set",
    "publication_binding_set_bytes",
    "publication_binding_set_sha256",
    "publication_binding_set_tree",
    "validate_approved_publication_authority",
    "validate_approved_profile_registry",
    "validate_golden_oracle_registry",
    "validate_independent_golden_receipt",
    "validate_publication_binding_authority",
]
