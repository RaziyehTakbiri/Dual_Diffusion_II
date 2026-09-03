"""Additive V2 execution-input binding for expected-evidence leaf authority.

The frozen V1 decision input set is left byte-for-byte unchanged.  This module
builds a distinct V2 artifact that contains its digest, the exact authenticated
expected-leaf profile projection, and an ordinal-preserving join between every
V1 case and its expected-leaf authority record.

The resulting digest can be carried by the existing opaque
``execution_input_set_sha256`` worker field.  That establishes request-digest
membership only; it does not attest that the worker parsed or consumed this
artifact and it does not make expected leaf bundles worker-generated outputs.

The low-level ``prepare`` helper composes already-validated transport objects.
Because those public NamedTuples are constructible, this module cannot by
itself authenticate the absent raw anchors, archives, or source dependencies.
The public freeze boundary is the raw-input-authenticating entry point.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import NamedTuple

from . import adapter_expected_leaf_authority as _leaf_authority
from . import adapter_publication_authority as _base_authority
from .adapter_expected_leaf_authority import (
    ValidatedApprovedExpectedLeafAuthorityV1,
)
from .adapter_expected_leaf_authority_types import (
    ApprovedExpectedLeafAuthorityProfileV1,
)
from .adapter_publication_authority import (
    ValidatedApprovedPublicationAuthorityV1,
)
from .adapter_publication_authority_types import (
    ApprovedPublicationProfileV1,
)
from .adapter_publication_decision_manifest import (
    DECISION_EXECUTION_INPUT_SET_DIGEST_DOMAIN,
    decision_execution_input_set_bytes,
)


DECISION_EXECUTION_INPUT_SET_V2_ARTIFACT_TYPE = (
    "heterodiff.adapter.decision-execution-input-set.v2"
)
DECISION_EXECUTION_INPUT_SET_V2_DIGEST_DOMAIN = (
    DECISION_EXECUTION_INPUT_SET_V2_ARTIFACT_TYPE
)
MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_BYTES = 4 * 1024 * 1024
MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_JSON_DEPTH = 32
MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_JSON_NODES = 200_000
MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_STRING_BYTES = 512 * 1024
_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1


class ExpectedLeafExecutionInputCode(str, Enum):
    """Closed failures for the additive V2 input-set projection."""

    INPUT_TYPE = "EXPECTED_LEAF_EXECUTION_INPUT_TYPE"
    AUTHORITY_MISMATCH = "EXPECTED_LEAF_EXECUTION_INPUT_AUTHORITY_MISMATCH"
    PARENT_MISMATCH = "EXPECTED_LEAF_EXECUTION_INPUT_PARENT_MISMATCH"
    CASE_MISMATCH = "EXPECTED_LEAF_EXECUTION_INPUT_CASE_MISMATCH"
    RESOURCE = "EXPECTED_LEAF_EXECUTION_INPUT_RESOURCE"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExpectedLeafExecutionInputCode.INPUT_TYPE: (
            "expected-leaf execution input has an invalid exact type"
        ),
        ExpectedLeafExecutionInputCode.AUTHORITY_MISMATCH: (
            "expected-leaf execution input authority is inconsistent"
        ),
        ExpectedLeafExecutionInputCode.PARENT_MISMATCH: (
            "expected-leaf execution input parent link does not match"
        ),
        ExpectedLeafExecutionInputCode.CASE_MISMATCH: (
            "expected-leaf execution input case join does not match"
        ),
        ExpectedLeafExecutionInputCode.RESOURCE: (
            "expected-leaf execution input exceeds a resource ceiling"
        ),
    }
)


class ExpectedLeafExecutionInputError(ValueError):
    """One fixed coded failure without interpolation of untrusted values."""

    def __init__(self, code: ExpectedLeafExecutionInputCode) -> None:
        if type(code) is not ExpectedLeafExecutionInputCode:
            raise TypeError("expected-leaf execution input code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class PreparedDecisionExecutionInputSetV2(NamedTuple):
    """Immutable V1 and additive V2 bytes plus their validated authorities."""

    base_authority: ValidatedApprovedPublicationAuthorityV1
    expected_leaf_authority: ValidatedApprovedExpectedLeafAuthorityV1
    base_execution_input_set_bytes: bytes
    base_execution_input_set_sha256: str
    execution_input_set_bytes: bytes
    execution_input_set_sha256: str


def _fail(code: ExpectedLeafExecutionInputCode) -> None:
    raise ExpectedLeafExecutionInputError(code) from None


def _sha256_text(value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    return value


def _validate_tree(value: object) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_JSON_NODES:
            _fail(ExpectedLeafExecutionInputCode.RESOURCE)
        if depth > MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_JSON_DEPTH:
            _fail(ExpectedLeafExecutionInputCode.RESOURCE)
        if current is None:
            _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
        if type(current) in (bool, int, str):
            if type(current) is int and (
                current < 0 or current > _MAXIMUM_SAFE_INTEGER
            ):
                _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
            if type(current) is str:
                try:
                    encoded = current.encode("ascii", "strict")
                except UnicodeError:
                    _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
                if (
                    len(encoded)
                    > MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_STRING_BYTES
                ):
                    _fail(ExpectedLeafExecutionInputCode.RESOURCE)
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
                stack.append((item, depth + 1))
                stack.append((key, depth + 1))
            continue
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)


def _canonical_bytes(value: object) -> bytes:
    _validate_tree(value)
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    if (
        not result
        or len(result) > MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_BYTES
    ):
        _fail(ExpectedLeafExecutionInputCode.RESOURCE)
    return result


def _base_case_tree(value: object) -> dict:
    return _leaf_authority.approved_case_expectation_tree(value)


def _hostile_tree(value: object) -> dict:
    names = (
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
    return {name: getattr(value, name) for name in names}


def _validate_profile_join(
    base_profile: ApprovedPublicationProfileV1,
    expected_leaf_profile: ApprovedExpectedLeafAuthorityProfileV1,
    *,
    base_profile_file_sha256: str,
    base_profile_sha256: str,
) -> None:
    if (
        expected_leaf_profile.parent_approved_profile_file_sha256
        != base_profile_file_sha256
        or expected_leaf_profile.parent_approved_profile_sha256
        != base_profile_sha256
    ):
        _fail(ExpectedLeafExecutionInputCode.PARENT_MISMATCH)
    base_cases = base_profile.case_expectations
    leaf_cases = expected_leaf_profile.case_expectations
    if len(base_cases) != len(leaf_cases):
        _fail(ExpectedLeafExecutionInputCode.CASE_MISMATCH)
    for ordinal, (base_case, leaf_case) in enumerate(
        zip(base_cases, leaf_cases)
    ):
        try:
            base_case_sha256 = (
                _leaf_authority.approved_case_expectation_sha256(base_case)
            )
            case_authority_id = (
                _leaf_authority.expected_leaf_case_authority_id(base_case)
            )
        except (TypeError, ValueError):
            _fail(ExpectedLeafExecutionInputCode.CASE_MISMATCH)
        if (
            base_case.case_ordinal != ordinal
            or leaf_case.case_ordinal != ordinal
            or leaf_case.base_case_expectation_sha256
            != base_case_sha256
            or leaf_case.case_authority_id != case_authority_id
            or leaf_case.expected_leaf_archive_object_id
            != case_authority_id
        ):
            _fail(ExpectedLeafExecutionInputCode.CASE_MISMATCH)


def decision_execution_input_set_v2_tree(
    base_profile: ApprovedPublicationProfileV1,
    expected_leaf_profile: ApprovedExpectedLeafAuthorityProfileV1,
    *,
    base_profile_file_sha256: str,
    base_profile_sha256: str,
    base_execution_input_set_sha256: str,
    expected_leaf_profile_file_sha256: str,
    expected_leaf_profile_sha256: str,
) -> dict:
    """Build the exact additive V2 projection from authenticated profiles."""

    if type(base_profile) is not ApprovedPublicationProfileV1:
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    if (
        type(expected_leaf_profile)
        is not ApprovedExpectedLeafAuthorityProfileV1
    ):
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    try:
        ApprovedPublicationProfileV1.__post_init__(base_profile)
        ApprovedExpectedLeafAuthorityProfileV1.__post_init__(
            expected_leaf_profile
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    for digest in (
        base_profile_file_sha256,
        base_profile_sha256,
        base_execution_input_set_sha256,
        expected_leaf_profile_file_sha256,
        expected_leaf_profile_sha256,
    ):
        _sha256_text(digest)
    try:
        base_profile_bytes = _base_authority.approved_profile_bytes(
            base_profile
        )
        leaf_profile_bytes = (
            _leaf_authority.approved_expected_leaf_authority_profile_bytes(
                expected_leaf_profile
            )
        )
        base_input_bytes = decision_execution_input_set_bytes(base_profile)
        observed = (
            hashlib.sha256(base_profile_bytes).hexdigest(),
            _base_authority.domain_separated_sha256(
                _base_authority.APPROVED_PUBLICATION_PROFILE_DIGEST_DOMAIN,
                base_profile_bytes,
            ),
            _base_authority.domain_separated_sha256(
                DECISION_EXECUTION_INPUT_SET_DIGEST_DOMAIN,
                base_input_bytes,
            ),
            hashlib.sha256(leaf_profile_bytes).hexdigest(),
            (
                _leaf_authority
                .approved_expected_leaf_authority_profile_sha256(
                    expected_leaf_profile
                )
            ),
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafExecutionInputCode.AUTHORITY_MISMATCH)
    if observed != (
        base_profile_file_sha256,
        base_profile_sha256,
        base_execution_input_set_sha256,
        expected_leaf_profile_file_sha256,
        expected_leaf_profile_sha256,
    ):
        _fail(ExpectedLeafExecutionInputCode.AUTHORITY_MISMATCH)
    _validate_profile_join(
        base_profile,
        expected_leaf_profile,
        base_profile_file_sha256=base_profile_file_sha256,
        base_profile_sha256=base_profile_sha256,
    )
    return {
        "artifact_type": DECISION_EXECUTION_INPUT_SET_V2_ARTIFACT_TYPE,
        "base_approved_profile_file_sha256": base_profile_file_sha256,
        "base_approved_profile_sha256": base_profile_sha256,
        "base_execution_input_set_sha256": base_execution_input_set_sha256,
        "case_expectations": [
            {
                "base_case_expectation": _base_case_tree(base_case),
                "expected_leaf_case_expectation": (
                    _leaf_authority
                    .approved_expected_leaf_case_expectation_tree(leaf_case)
                ),
            }
            for base_case, leaf_case in zip(
                base_profile.case_expectations,
                expected_leaf_profile.case_expectations,
            )
        ],
        "expected_leaf_authority_profile": (
            _leaf_authority.approved_expected_leaf_authority_profile_tree(
                expected_leaf_profile
            )
        ),
        "expected_leaf_authority_profile_file_sha256": (
            expected_leaf_profile_file_sha256
        ),
        "expected_leaf_authority_profile_sha256": (
            expected_leaf_profile_sha256
        ),
        "format_version": "2",
        "hostile_control_expectations": [
            _hostile_tree(item)
            for item in base_profile.hostile_control_expectations
        ],
    }


def decision_execution_input_set_v2_bytes(
    base_profile: ApprovedPublicationProfileV1,
    expected_leaf_profile: ApprovedExpectedLeafAuthorityProfileV1,
    *,
    base_profile_file_sha256: str,
    base_profile_sha256: str,
    base_execution_input_set_sha256: str,
    expected_leaf_profile_file_sha256: str,
    expected_leaf_profile_sha256: str,
) -> bytes:
    """Serialize the exact V2 input set as bounded canonical ASCII JSON."""

    return _canonical_bytes(
        decision_execution_input_set_v2_tree(
            base_profile,
            expected_leaf_profile,
            base_profile_file_sha256=base_profile_file_sha256,
            base_profile_sha256=base_profile_sha256,
            base_execution_input_set_sha256=(
                base_execution_input_set_sha256
            ),
            expected_leaf_profile_file_sha256=(
                expected_leaf_profile_file_sha256
            ),
            expected_leaf_profile_sha256=expected_leaf_profile_sha256,
        )
    )


def decision_execution_input_set_v2_sha256(value: bytes) -> str:
    """Return the framed digest of exact already-serialized V2 bytes."""

    if type(value) is not bytes:
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_BYTES
    ):
        _fail(ExpectedLeafExecutionInputCode.RESOURCE)
    return _base_authority.domain_separated_sha256(
        DECISION_EXECUTION_INPUT_SET_V2_DIGEST_DOMAIN,
        value,
    )


def prepare_decision_execution_input_set_v2(
    base_authority: ValidatedApprovedPublicationAuthorityV1,
    expected_leaf_authority: ValidatedApprovedExpectedLeafAuthorityV1,
) -> PreparedDecisionExecutionInputSetV2:
    """Recheck authenticated transports and prepare immutable V1/V2 bytes.

    This composition helper checks internal profile-byte and digest coherence;
    it does not authenticate raw anchors or dependency archives that are not
    arguments.  Callers requiring authority must use the expected-leaf freeze
    boundary, which performs those validations before invoking this helper.
    """

    if type(base_authority) is not ValidatedApprovedPublicationAuthorityV1:
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    if (
        type(expected_leaf_authority)
        is not ValidatedApprovedExpectedLeafAuthorityV1
    ):
        _fail(ExpectedLeafExecutionInputCode.INPUT_TYPE)
    try:
        base_profile_bytes = _base_authority.approved_profile_bytes(
            base_authority.profile
        )
        expected_leaf_profile_bytes = (
            _leaf_authority.approved_expected_leaf_authority_profile_bytes(
                expected_leaf_authority.profile
            )
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafExecutionInputCode.AUTHORITY_MISMATCH)
    base_file_sha256 = hashlib.sha256(base_profile_bytes).hexdigest()
    base_profile_sha256 = _base_authority.domain_separated_sha256(
        _base_authority.APPROVED_PUBLICATION_PROFILE_DIGEST_DOMAIN,
        base_profile_bytes,
    )
    leaf_file_sha256 = hashlib.sha256(
        expected_leaf_profile_bytes
    ).hexdigest()
    leaf_profile_sha256 = (
        _leaf_authority.approved_expected_leaf_authority_profile_sha256(
            expected_leaf_authority.profile
        )
    )
    if (
        base_authority.profile_bytes != base_profile_bytes
        or base_authority.profile_file_sha256 != base_file_sha256
        or base_authority.profile_sha256 != base_profile_sha256
        or expected_leaf_authority.profile_bytes
        != expected_leaf_profile_bytes
        or expected_leaf_authority.profile_file_sha256
        != leaf_file_sha256
        or expected_leaf_authority.profile_sha256
        != leaf_profile_sha256
        or expected_leaf_authority.parent_authority != base_authority
    ):
        _fail(ExpectedLeafExecutionInputCode.AUTHORITY_MISMATCH)

    try:
        base_input_bytes = decision_execution_input_set_bytes(
            base_authority.profile
        )
        base_input_sha256 = _base_authority.domain_separated_sha256(
            DECISION_EXECUTION_INPUT_SET_DIGEST_DOMAIN,
            base_input_bytes,
        )
        input_bytes = decision_execution_input_set_v2_bytes(
            base_authority.profile,
            expected_leaf_authority.profile,
            base_profile_file_sha256=base_file_sha256,
            base_profile_sha256=base_profile_sha256,
            base_execution_input_set_sha256=base_input_sha256,
            expected_leaf_profile_file_sha256=leaf_file_sha256,
            expected_leaf_profile_sha256=leaf_profile_sha256,
        )
        input_sha256 = decision_execution_input_set_v2_sha256(input_bytes)
    except ExpectedLeafExecutionInputError:
        raise
    except (TypeError, ValueError):
        _fail(ExpectedLeafExecutionInputCode.AUTHORITY_MISMATCH)
    return PreparedDecisionExecutionInputSetV2(
        base_authority=base_authority,
        expected_leaf_authority=expected_leaf_authority,
        base_execution_input_set_bytes=base_input_bytes,
        base_execution_input_set_sha256=base_input_sha256,
        execution_input_set_bytes=input_bytes,
        execution_input_set_sha256=input_sha256,
    )


__all__ = [
    "DECISION_EXECUTION_INPUT_SET_V2_ARTIFACT_TYPE",
    "DECISION_EXECUTION_INPUT_SET_V2_DIGEST_DOMAIN",
    "ExpectedLeafExecutionInputCode",
    "ExpectedLeafExecutionInputError",
    "MAXIMUM_DECISION_EXECUTION_INPUT_SET_V2_BYTES",
    "PreparedDecisionExecutionInputSetV2",
    "decision_execution_input_set_v2_bytes",
    "decision_execution_input_set_v2_sha256",
    "decision_execution_input_set_v2_tree",
    "prepare_decision_execution_input_set_v2",
]
