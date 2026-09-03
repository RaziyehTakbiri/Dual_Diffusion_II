"""Pure publisher-side binding for one frozen oracle-worker case.

This module bridges an already frozen V2 decision-candidate case to the fixed
oracle-worker ABI.  It rebuilds every request payload from exact typed values,
rechecks the golden/archive identity metadata retained by the freezer, and
checks a response against the publisher-typed canonical expected outputs.  It
does not receive raw registry/archive inputs and therefore cannot authenticate
their custody.

It performs no filesystem, network, process, source-loading, adapter-callback,
or gate-decision operation.  A validated result is explicitly not oracle
execution evidence.  A decision-capable verifier must independently
reimplement these checks.
"""

from __future__ import annotations

from enum import Enum
import hashlib
from types import MappingProxyType
from typing import NamedTuple, Tuple

from . import adapter_contract as _contract
from . import adapter_publication_payloads as _payloads
from .adapter_oracle_abi import (
    OracleWorkerABIError,
    OracleWorkerRequestV1,
    OracleWorkerResponseV1,
    ValidatedOracleWorkerResponseIdentityV1,
    build_oracle_worker_request_frame,
    validate_oracle_worker_response_identity,
)
from .adapter_publication_authority import (
    INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN,
    ValidatedIndependentGoldenReceiptV1,
    domain_separated_sha256,
    independent_golden_receipt_bytes,
)
from .adapter_publication_authority_types import (
    ApprovedCaseExpectationV1,
    IndependentGoldenReceiptV1,
)
from .adapter_publication_decision_freeze import (
    FrozenDecisionDetachedCaseV1,
)
from .adapter_source_archive import (
    SOURCE_ARCHIVE_ORACLE_ROLE_ID,
    ValidatedSourceArchiveMembershipV1,
    source_archive_membership_receipt_sha256,
)


ORACLE_CASE_DIRECT_FIELD_DIGEST_DOMAIN_BYTES = (
    b"heterodiff.adapter.oracle-case-direct-field-input.v1"
)
ORACLE_CASE_DIRECT_FIELD_NAMES = (
    b"case_ordinal",
    b"oracle_id",
    b"oracle_source_byte_count",
    b"oracle_source_sha256",
    b"source_bytes",
    b"descriptor_payload_bytes",
    b"partition_payload_bytes",
    b"split_manifest_payload_bytes",
)
ORACLE_CASE_NO_ATTESTED_EXECUTION_STATUS = (
    "PUBLISHER_TYPED_PAYLOAD_BYTES_MATCHED_NO_ATTESTED_ORACLE_EXECUTION"
)


class OracleCaseProtocolCode(str, Enum):
    """Closed, interpolation-free case-protocol failures."""

    INPUT_TYPE = "ORACLE_CASE_INPUT_TYPE"
    CASE_BINDING = "ORACLE_CASE_BINDING_MISMATCH"
    REQUEST_BINDING = "ORACLE_CASE_REQUEST_BINDING_MISMATCH"
    RESPONSE_FRAME = "ORACLE_CASE_RESPONSE_FRAME_INVALID"
    RESPONSE_IDENTITY = "ORACLE_CASE_RESPONSE_IDENTITY_MISMATCH"
    RESPONSE_PAYLOAD_BYTES = (
        "ORACLE_CASE_RESPONSE_PAYLOAD_BYTES_MISMATCH"
    )


_ERROR_MESSAGES = MappingProxyType(
    {
        OracleCaseProtocolCode.INPUT_TYPE: (
            "oracle case protocol input has an invalid exact type"
        ),
        OracleCaseProtocolCode.CASE_BINDING: (
            "oracle case typed and custody bindings do not match"
        ),
        OracleCaseProtocolCode.REQUEST_BINDING: (
            "oracle case request frame does not match its typed input"
        ),
        OracleCaseProtocolCode.RESPONSE_FRAME: (
            "oracle case response frame is invalid"
        ),
        OracleCaseProtocolCode.RESPONSE_IDENTITY: (
            "oracle case response identity does not match its request"
        ),
        OracleCaseProtocolCode.RESPONSE_PAYLOAD_BYTES: (
            "oracle case response does not match publisher-typed expected "
            "payload bytes"
        ),
    }
)


class OracleCaseProtocolError(ValueError):
    """One fixed coded failure without lower-layer or attacker text."""

    def __init__(self, code: OracleCaseProtocolCode) -> None:
        if type(code) is not OracleCaseProtocolCode:
            raise TypeError("oracle case protocol code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: OracleCaseProtocolCode) -> None:
    raise OracleCaseProtocolError(code) from None


def _exact_sha256(value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    return value


class PreparedOracleCaseRequestV1(tuple):
    """Immutable request plus custody and direct-field commitments."""

    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object):
        del cls, args, kwargs
        raise TypeError(
            "prepared oracle case requests are created only by validation"
        )

    @property
    def request(self) -> OracleWorkerRequestV1:
        return self[0]

    @property
    def request_frame_bytes(self) -> bytes:
        return self[1]

    @property
    def request_frame_sha256(self) -> str:
        return self[2]

    @property
    def direct_field_input_sha256(self) -> str:
        return self[3]

    @property
    def independent_golden_receipt_sha256(self) -> str:
        return self[4]

    @property
    def oracle_registry_sha256(self) -> str:
        return self[5]

    @property
    def source_archive_membership_sha256(self) -> str:
        return self[6]


class ValidatedOracleCaseResponseV1(tuple):
    """Publisher-typed payload byte match; never execution evidence."""

    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object):
        del cls, args, kwargs
        raise TypeError(
            "validated oracle case responses are created only by validation"
        )

    @property
    def prepared_request(self) -> PreparedOracleCaseRequestV1:
        return self[0]

    @property
    def validated_identity(self) -> ValidatedOracleWorkerResponseIdentityV1:
        return self[1]

    @property
    def response_frame_bytes(self) -> bytes:
        return self[2]

    @property
    def response_frame_sha256(self) -> str:
        return self[3]

    @property
    def response(self) -> OracleWorkerResponseV1:
        return self.validated_identity.response

    @property
    def oracle_execution_status(self) -> str:
        return ORACLE_CASE_NO_ATTESTED_EXECUTION_STATUS


class _CaseMaterial(NamedTuple):
    request: OracleWorkerRequestV1
    expected_configuration_payload_bytes: bytes
    expected_evidence_payload_bytes: bytes
    expected_native_observation_sha256: str
    independent_golden_receipt_sha256: str
    oracle_registry_sha256: str
    source_archive_membership_sha256: str


def _direct_field_values(
    value: OracleWorkerRequestV1,
) -> Tuple[bytes, ...]:
    return (
        value.case_ordinal.to_bytes(8, "big"),
        value.oracle_id.encode("ascii"),
        value.oracle_source_byte_count.to_bytes(8, "big"),
        value.oracle_source_sha256.encode("ascii"),
        value.source_bytes,
        value.descriptor_payload_bytes,
        value.partition_payload_bytes,
        value.split_manifest_payload_bytes,
    )


def _direct_field_preimage(value: OracleWorkerRequestV1) -> bytes:
    if type(value) is not OracleWorkerRequestV1:
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    try:
        build_oracle_worker_request_frame(value)
        values = _direct_field_values(value)
        parts = [
            ORACLE_CASE_DIRECT_FIELD_DIGEST_DOMAIN_BYTES,
            b"\x00",
            len(ORACLE_CASE_DIRECT_FIELD_NAMES).to_bytes(8, "big"),
        ]
        for name, raw in zip(
            ORACLE_CASE_DIRECT_FIELD_NAMES,
            values,
        ):
            parts.extend(
                (
                    len(name).to_bytes(8, "big"),
                    name,
                    len(raw).to_bytes(8, "big"),
                    raw,
                )
            )
        return b"".join(parts)
    except OracleCaseProtocolError:
        raise
    except Exception:
        _fail(OracleCaseProtocolCode.CASE_BINDING)


def oracle_case_direct_field_input_sha256(
    value: OracleWorkerRequestV1,
) -> str:
    """Commit direct request fields other than the execution-set digest.

    This excludes direct expected-output fields and payload bytes. It is not
    transitively output-independent: the V1 case ordinal is inherited from a
    profile order that currently depends on output-derived commitments.
    """

    return hashlib.sha256(_direct_field_preimage(value)).hexdigest()


def _validated_golden_and_membership(
    case: FrozenDecisionDetachedCaseV1,
) -> Tuple[
    ValidatedIndependentGoldenReceiptV1,
    IndependentGoldenReceiptV1,
    ValidatedSourceArchiveMembershipV1,
    str,
]:
    golden = case.independent_golden
    if type(golden) is not ValidatedIndependentGoldenReceiptV1:
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    receipt = golden.receipt
    if type(receipt) is not IndependentGoldenReceiptV1:
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    IndependentGoldenReceiptV1.__post_init__(receipt)
    if (
        type(golden.receipt_bytes) is not bytes
        or type(golden.oracle_source_bytes) is not bytes
    ):
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    canonical_receipt_bytes = independent_golden_receipt_bytes(receipt)
    receipt_sha256 = domain_separated_sha256(
        INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN,
        canonical_receipt_bytes,
    )
    if (
        golden.receipt_bytes != canonical_receipt_bytes
        or golden.receipt_sha256 != receipt_sha256
        or receipt.oracle_source_byte_count
        != len(golden.oracle_source_bytes)
        or receipt.oracle_source_sha256
        != hashlib.sha256(golden.oracle_source_bytes).hexdigest()
    ):
        _fail(OracleCaseProtocolCode.CASE_BINDING)

    membership = case.oracle_source_membership
    if type(membership) is not ValidatedSourceArchiveMembershipV1:
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    ValidatedSourceArchiveMembershipV1.__post_init__(membership)
    if (
        membership.role_id != SOURCE_ARCHIVE_ORACLE_ROLE_ID
        or membership.source_object_id != receipt.oracle_id
        or membership.source_byte_count != receipt.oracle_source_byte_count
        or membership.source_sha256 != receipt.oracle_source_sha256
    ):
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    membership_sha256 = source_archive_membership_receipt_sha256(membership)
    return golden, receipt, membership, membership_sha256


def _case_material(
    case: FrozenDecisionDetachedCaseV1,
    execution_input_set_sha256: str,
) -> _CaseMaterial:
    expectation = case.case_expectation
    if type(expectation) is not ApprovedCaseExpectationV1:
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    ApprovedCaseExpectationV1.__post_init__(expectation)
    if type(case.source_bytes) is not bytes or not case.source_bytes:
        _fail(OracleCaseProtocolCode.CASE_BINDING)

    golden, receipt, _membership, membership_sha256 = (
        _validated_golden_and_membership(case)
    )
    descriptor_payload = _payloads.adapter_descriptor_payload(
        case.descriptor
    )
    partition = case.complete_sample.sample.manifest.partition
    partition_payload = _payloads.partition_payload(partition)
    split_payload = _payloads.split_manifest_payload(case.split_manifest)
    complete_payload = _payloads.complete_sample_commitment_payload(
        case.descriptor,
        case.complete_sample,
    )
    run_payload = _payloads.conformance_run_payload(case.conformance_run)
    expected_configuration_payload = (
        _payloads.identity_bearing_native_configuration_payload(
            case.expected_configuration
        )
    )
    complete_configuration_payload = (
        _payloads.identity_bearing_native_configuration_payload(
            case.complete_sample.sample.configuration
        )
    )
    expected_evidence_payload = _payloads.expected_evidence_payload(
        case.expected_evidence
    )
    native_sha256 = _contract.native_observation_digest(
        case.expected_configuration
    )
    source_sha256 = hashlib.sha256(case.source_bytes).hexdigest()

    try:
        selected_partition = case.split_manifest.partition_for(
            partition.sample_id
        )
    except Exception:
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    manifest = case.complete_sample.sample.manifest
    descriptor_identity = case.descriptor.identity
    recomputed_expectation = ApprovedCaseExpectationV1(
        adapter_id=descriptor_identity.adapter_id,
        adapter_version=descriptor_identity.adapter_version,
        case_ordinal=expectation.case_ordinal,
        complete_sample_commitment_sha256=complete_payload.payload_sha256,
        conformance_run_sha256=run_payload.payload_sha256,
        descriptor_sha256=descriptor_payload.payload_sha256,
        expected_configuration_sha256=(
            expected_configuration_payload.payload_sha256
        ),
        expected_evidence_sha256=expected_evidence_payload.payload_sha256,
        independent_golden_receipt_sha256=golden.receipt_sha256,
        native_observation_sha256=native_sha256,
        sample_root_sha256=case.conformance_run.sample_root_sha256,
        source_sha256=source_sha256,
        split_manifest_sha256=split_payload.payload_sha256,
    )
    if (
        expectation != recomputed_expectation
        or selected_partition != partition
        or complete_configuration_payload.canonical_json_bytes
        != expected_configuration_payload.canonical_json_bytes
        or manifest.partition != partition
        or manifest.source_sha256 != source_sha256
        or manifest.source_size_bytes != len(case.source_bytes)
        or manifest.descriptor_sha256 != descriptor_payload.payload_sha256
        or manifest.split_manifest_sha256 != split_payload.payload_sha256
        or case.expected_evidence.native_observation_sha256 != native_sha256
        or receipt.adapter_id != descriptor_identity.adapter_id
        or receipt.adapter_version != descriptor_identity.adapter_version
        or receipt.descriptor_sha256 != descriptor_payload.payload_sha256
        or receipt.expected_configuration_payload_byte_count
        != expected_configuration_payload.payload_byte_count
        or receipt.expected_configuration_sha256
        != expected_configuration_payload.payload_sha256
        or receipt.expected_evidence_sha256
        != expected_evidence_payload.payload_sha256
        or receipt.expected_native_observation_sha256 != native_sha256
        or receipt.source_byte_count != len(case.source_bytes)
        or receipt.source_sha256 != source_sha256
        or receipt.split_manifest_sha256 != split_payload.payload_sha256
    ):
        _fail(OracleCaseProtocolCode.CASE_BINDING)

    request = OracleWorkerRequestV1(
        execution_input_set_sha256=execution_input_set_sha256,
        case_ordinal=expectation.case_ordinal,
        oracle_id=receipt.oracle_id,
        oracle_source_byte_count=receipt.oracle_source_byte_count,
        oracle_source_sha256=receipt.oracle_source_sha256,
        source_bytes=case.source_bytes,
        descriptor_payload_bytes=descriptor_payload.canonical_json_bytes,
        partition_payload_bytes=partition_payload.canonical_json_bytes,
        split_manifest_payload_bytes=split_payload.canonical_json_bytes,
    )
    return _CaseMaterial(
        request=request,
        expected_configuration_payload_bytes=(
            expected_configuration_payload.canonical_json_bytes
        ),
        expected_evidence_payload_bytes=(
            expected_evidence_payload.canonical_json_bytes
        ),
        expected_native_observation_sha256=native_sha256,
        independent_golden_receipt_sha256=golden.receipt_sha256,
        oracle_registry_sha256=receipt.oracle_registry_sha256,
        source_archive_membership_sha256=membership_sha256,
    )


def _prepared_from_material(
    material: _CaseMaterial,
) -> PreparedOracleCaseRequestV1:
    request_frame_bytes = build_oracle_worker_request_frame(material.request)
    return tuple.__new__(
        PreparedOracleCaseRequestV1,
        (
            material.request,
            request_frame_bytes,
            hashlib.sha256(request_frame_bytes).hexdigest(),
            oracle_case_direct_field_input_sha256(material.request),
            material.independent_golden_receipt_sha256,
            material.oracle_registry_sha256,
            material.source_archive_membership_sha256,
        ),
    )


def prepare_oracle_case_request(
    case: FrozenDecisionDetachedCaseV1,
    execution_input_set_sha256: str,
) -> PreparedOracleCaseRequestV1:
    """Rebuild one exact request without executing an oracle or callback."""

    if type(case) is not FrozenDecisionDetachedCaseV1:
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    _exact_sha256(execution_input_set_sha256)
    try:
        return _prepared_from_material(
            _case_material(case, execution_input_set_sha256)
        )
    except OracleCaseProtocolError:
        raise
    except Exception:
        _fail(OracleCaseProtocolCode.CASE_BINDING)


def validate_prepared_oracle_case_request(
    value: PreparedOracleCaseRequestV1,
    case: FrozenDecisionDetachedCaseV1,
    execution_input_set_sha256: str,
) -> PreparedOracleCaseRequestV1:
    """Deep-revalidate a transport and return a fresh canonical request."""

    if (
        type(value) is not PreparedOracleCaseRequestV1
        or type(case) is not FrozenDecisionDetachedCaseV1
        or len(value) != 7
    ):
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    if (
        type(value[0]) is not OracleWorkerRequestV1
        or type(value[1]) is not bytes
        or any(type(value[index]) is not str for index in range(2, 7))
    ):
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    _exact_sha256(execution_input_set_sha256)
    for index in range(2, 7):
        _exact_sha256(value[index])
    try:
        OracleWorkerRequestV1.__post_init__(value[0])
        expected = prepare_oracle_case_request(
            case,
            execution_input_set_sha256,
        )
    except OracleCaseProtocolError:
        raise
    except Exception:
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    if tuple(value) != tuple(expected):
        _fail(OracleCaseProtocolCode.REQUEST_BINDING)
    return expected


def validate_oracle_case_response(
    case: FrozenDecisionDetachedCaseV1,
    request_frame_bytes: bytes,
    response_frame_bytes: bytes,
    execution_input_set_sha256: str,
) -> ValidatedOracleCaseResponseV1:
    """Byte-match publisher-typed outputs; this does not prove execution."""

    if (
        type(case) is not FrozenDecisionDetachedCaseV1
        or type(request_frame_bytes) is not bytes
        or type(response_frame_bytes) is not bytes
    ):
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    _exact_sha256(execution_input_set_sha256)
    try:
        material = _case_material(case, execution_input_set_sha256)
        prepared = _prepared_from_material(material)
    except OracleCaseProtocolError:
        raise
    except Exception:
        _fail(OracleCaseProtocolCode.CASE_BINDING)
    if request_frame_bytes != prepared.request_frame_bytes:
        _fail(OracleCaseProtocolCode.REQUEST_BINDING)
    try:
        identity = validate_oracle_worker_response_identity(
            request_frame_bytes,
            response_frame_bytes,
        )
    except OracleWorkerABIError as error:
        if error.code == "ABI_RESPONSE_IDENTITY":
            _fail(OracleCaseProtocolCode.RESPONSE_IDENTITY)
        _fail(OracleCaseProtocolCode.RESPONSE_FRAME)
    except Exception:
        _fail(OracleCaseProtocolCode.RESPONSE_FRAME)
    response = identity.response
    if (
        response.expected_configuration_payload_bytes
        != material.expected_configuration_payload_bytes
        or response.expected_evidence_payload_bytes
        != material.expected_evidence_payload_bytes
        or response.expected_native_observation_sha256
        != material.expected_native_observation_sha256
    ):
        _fail(OracleCaseProtocolCode.RESPONSE_PAYLOAD_BYTES)
    return tuple.__new__(
        ValidatedOracleCaseResponseV1,
        (
            prepared,
            identity,
            response_frame_bytes,
            hashlib.sha256(response_frame_bytes).hexdigest(),
        ),
    )


def validate_validated_oracle_case_response(
    value: ValidatedOracleCaseResponseV1,
    case: FrozenDecisionDetachedCaseV1,
    execution_input_set_sha256: str,
) -> ValidatedOracleCaseResponseV1:
    """Deep-revalidate a response transport and return a fresh result."""

    if (
        type(value) is not ValidatedOracleCaseResponseV1
        or type(case) is not FrozenDecisionDetachedCaseV1
        or len(value) != 4
        or type(value[0]) is not PreparedOracleCaseRequestV1
        or type(value[1])
        is not ValidatedOracleWorkerResponseIdentityV1
        or type(value[2]) is not bytes
        or type(value[3]) is not str
    ):
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    _exact_sha256(execution_input_set_sha256)
    _exact_sha256(value[3])
    try:
        ValidatedOracleWorkerResponseIdentityV1.__post_init__(value[1])
    except Exception:
        _fail(OracleCaseProtocolCode.INPUT_TYPE)
    prepared = validate_prepared_oracle_case_request(
        value[0],
        case,
        execution_input_set_sha256,
    )
    expected = validate_oracle_case_response(
        case,
        prepared.request_frame_bytes,
        value[2],
        execution_input_set_sha256,
    )
    if tuple(value) != tuple(expected):
        _fail(OracleCaseProtocolCode.RESPONSE_PAYLOAD_BYTES)
    return expected


__all__ = [
    "ORACLE_CASE_DIRECT_FIELD_DIGEST_DOMAIN_BYTES",
    "ORACLE_CASE_DIRECT_FIELD_NAMES",
    "ORACLE_CASE_NO_ATTESTED_EXECUTION_STATUS",
    "OracleCaseProtocolCode",
    "OracleCaseProtocolError",
    "PreparedOracleCaseRequestV1",
    "ValidatedOracleCaseResponseV1",
    "oracle_case_direct_field_input_sha256",
    "prepare_oracle_case_request",
    "validate_oracle_case_response",
    "validate_prepared_oracle_case_request",
    "validate_validated_oracle_case_response",
]
