"""Trusted post-output comparison of adapted and expected evidence receipts.

The comparator deliberately receives raw verifier inputs rather than trusted
receipt objects.  It reruns adapted-side verification first, reruns the
existing expected-leaf verification second, and compares only the resulting
independently reconstructed identities.

This module is a local, write-free comparison surface.  It does not execute an
adapter, enforce output blindness, authenticate source custody, attest
containment, interpret domain semantics, rebuild publication artifacts, or
make a gate decision.  In particular, successful ordering inside this
function does not prove that a caller-supplied in-process adapter could not
obtain expected material through another channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import NamedTuple

from . import adapter_adapted_evidence_bundle_verifier as _actual
from . import adapter_expected_leaf_bundle_verifier as _expected


ADAPTED_EXPECTED_COMPARISON_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.adapted-expected-comparison-receipt.v1"
)
ADAPTED_EXPECTED_COMPARISON_RECEIPT_DIGEST_DOMAIN = (
    ADAPTED_EXPECTED_COMPARISON_RECEIPT_ARTIFACT_TYPE
)
ADAPTED_EXPECTED_COMPARISON_STATUS = (
    "ADAPTED_AND_EXPECTED_LEAF_IDENTITIES_MATCHED_"
    "UNATTESTED_DEVELOPMENT_COMPARISON"
)
ADAPTED_EXPECTED_COMPARISON_DECISION_STATUS = (
    "NOT_MADE_BY_ADAPTED_EXPECTED_COMPARATOR"
)
MAXIMUM_ADAPTED_EXPECTED_COMPARISON_RECEIPT_BYTES = 64 * 1024
MAXIMUM_ADAPTED_EXPECTED_COMPARISON_SOURCE_BYTES = 64 * 1024

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AdaptedExpectedComparisonCode(str, Enum):
    """Closed comparison failures with fixed, nonreflecting messages."""

    INPUT_TYPE = "ADAPTED_EXPECTED_COMPARISON_INPUT_TYPE"
    ACTUAL_VERIFICATION = "ADAPTED_EXPECTED_COMPARISON_ACTUAL_VERIFICATION"
    EXPECTED_VERIFICATION = (
        "ADAPTED_EXPECTED_COMPARISON_EXPECTED_VERIFICATION"
    )
    REASON_REGISTRY = "ADAPTED_EXPECTED_COMPARISON_REASON_REGISTRY"
    EVIDENCE_MISMATCH = "ADAPTED_EXPECTED_COMPARISON_EVIDENCE_MISMATCH"
    RECEIPT = "ADAPTED_EXPECTED_COMPARISON_RECEIPT"
    INTERNAL = "ADAPTED_EXPECTED_COMPARISON_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        AdaptedExpectedComparisonCode.INPUT_TYPE: (
            "adapted-expected comparison input has an invalid exact type"
        ),
        AdaptedExpectedComparisonCode.ACTUAL_VERIFICATION: (
            "adapted-evidence verification did not succeed"
        ),
        AdaptedExpectedComparisonCode.EXPECTED_VERIFICATION: (
            "expected-evidence verification did not succeed"
        ),
        AdaptedExpectedComparisonCode.REASON_REGISTRY: (
            "adapted and expected reason registries differ"
        ),
        AdaptedExpectedComparisonCode.EVIDENCE_MISMATCH: (
            "adapted and expected evidence identities differ"
        ),
        AdaptedExpectedComparisonCode.RECEIPT: (
            "adapted-expected comparison receipt is invalid"
        ),
        AdaptedExpectedComparisonCode.INTERNAL: (
            "adapted-expected comparison failed internally"
        ),
    }
)


class AdaptedExpectedComparisonError(ValueError):
    """One coded comparison failure without attacker-controlled text."""

    def __init__(self, code: AdaptedExpectedComparisonCode) -> None:
        if type(code) is not AdaptedExpectedComparisonCode:
            raise TypeError("adapted-expected comparison code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


@dataclass(frozen=True)
class AdaptedExpectedComparisonInputV1:
    """Raw inputs for both verification layers; no supplied receipt is trusted."""

    actual_verification_input: (
        _actual.IndependentAdaptedEvidenceBundleVerificationInputV1
    )
    expected_verification_input: (
        _expected.IndependentExpectedLeafBundleVerificationInputV1
    )

    def __post_init__(self) -> None:
        if type(self) is not AdaptedExpectedComparisonInputV1:
            raise TypeError("adapted-expected comparison input must be exact")
        if type(self.actual_verification_input) is not (
            _actual.IndependentAdaptedEvidenceBundleVerificationInputV1
        ):
            raise TypeError("actual verification input must be exact")
        if type(self.expected_verification_input) is not (
            _expected.IndependentExpectedLeafBundleVerificationInputV1
        ):
            raise TypeError("expected verification input must be exact")


class AdaptedExpectedComparisonReceiptV1(NamedTuple):
    """Canonical structural equality receipt; permanently nondecision."""

    artifact_type: str
    format_version: str
    status_id: str
    decision_status: str
    actual_verification_receipt_sha256: str
    expected_verification_receipt_sha256: str
    case_input_sha256: str
    adapted_evidence_bundle_sha256: str
    expected_evidence_leaf_bundle_sha256: str
    allowed_exclusion_reason_codes_sha256: str
    allowed_censor_reason_codes_sha256: str
    descriptor_sha256: str
    partition_sha256: str
    source_byte_count: int
    source_sha256: str
    split_manifest_sha256: str
    configuration_sha256: str
    evidence_sha256: str
    native_observation_sha256: str
    source_inventory_sha256: str
    coverage_ledger_sha256: str
    static_context_sha256: str
    evaluation_labels_sha256: str
    private_provenance_sha256: str
    fitted_state_sha256: str
    semantic_reconstruction_sha256: str
    adapter_manifest_sha256: str
    complete_sample_commitment_sha256: str
    raw_reconstruction_sha256: str
    actual_verification_rerun: bool
    expected_verification_rerun_after_actual_verification: bool
    reason_registries_matched: bool
    descriptor_source_split_matched: bool
    configuration_evidence_native_matched: bool
    phase_c_leaf_digests_matched: bool
    raw_reconstruction_policy_recomputed: bool
    actual_expected_leaf_equality_recomputed: bool
    decision_made: bool
    execution_attested: bool
    containment_attested: bool
    output_blind_adapter_child_enforced: bool
    expected_material_nonexposure_attested: bool
    adapter_source_execution_identity_attested: bool
    external_custody_authenticated: bool
    semantic_truth_attested: bool
    format_specific_payload_semantics_attested: bool
    publication_artifacts_rebuilt: bool
    generalization_attested: bool


class AdaptedExpectedComparisonResultV1(NamedTuple):
    """Receipt plus its exact canonical byte and domain identities."""

    receipt: AdaptedExpectedComparisonReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str


_RECEIPT_DIGEST_FIELDS = (
    "actual_verification_receipt_sha256",
    "expected_verification_receipt_sha256",
    "case_input_sha256",
    "adapted_evidence_bundle_sha256",
    "expected_evidence_leaf_bundle_sha256",
    "allowed_exclusion_reason_codes_sha256",
    "allowed_censor_reason_codes_sha256",
    "descriptor_sha256",
    "partition_sha256",
    "source_sha256",
    "split_manifest_sha256",
    "configuration_sha256",
    "evidence_sha256",
    "native_observation_sha256",
    "source_inventory_sha256",
    "coverage_ledger_sha256",
    "static_context_sha256",
    "evaluation_labels_sha256",
    "private_provenance_sha256",
    "fitted_state_sha256",
    "semantic_reconstruction_sha256",
    "adapter_manifest_sha256",
    "complete_sample_commitment_sha256",
    "raw_reconstruction_sha256",
)
_RECEIPT_TRUE_FIELDS = (
    "actual_verification_rerun",
    "expected_verification_rerun_after_actual_verification",
    "reason_registries_matched",
    "descriptor_source_split_matched",
    "configuration_evidence_native_matched",
    "phase_c_leaf_digests_matched",
    "raw_reconstruction_policy_recomputed",
    "actual_expected_leaf_equality_recomputed",
)
_RECEIPT_FALSE_FIELDS = (
    "decision_made",
    "execution_attested",
    "containment_attested",
    "output_blind_adapter_child_enforced",
    "expected_material_nonexposure_attested",
    "adapter_source_execution_identity_attested",
    "external_custody_authenticated",
    "semantic_truth_attested",
    "format_specific_payload_semantics_attested",
    "publication_artifacts_rebuilt",
    "generalization_attested",
)


def _fail(code: AdaptedExpectedComparisonCode) -> None:
    raise AdaptedExpectedComparisonError(code) from None


def _domain_sha256(domain: str, payload: bytes) -> str:
    if type(domain) is not str or type(payload) is not bytes:
        raise TypeError("comparison digest inputs must have exact types")
    domain_bytes = domain.encode("ascii", "strict")
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _receipt_tree(value: AdaptedExpectedComparisonReceiptV1) -> dict:
    if type(value) is not AdaptedExpectedComparisonReceiptV1:
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    _validate_receipt(value)
    return value._asdict()


def adapted_expected_comparison_receipt_bytes(
    value: AdaptedExpectedComparisonReceiptV1,
) -> bytes:
    """Serialize one exact receipt as canonical ASCII JSON."""

    try:
        result = json.dumps(
            _receipt_tree(value),
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except AdaptedExpectedComparisonError:
        raise
    except (TypeError, ValueError, UnicodeError):
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    if (
        not result
        or len(result) > MAXIMUM_ADAPTED_EXPECTED_COMPARISON_RECEIPT_BYTES
    ):
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    return result


def adapted_expected_comparison_receipt_sha256(
    value: AdaptedExpectedComparisonReceiptV1,
) -> str:
    """Return the receipt-domain digest of exact canonical receipt bytes."""

    return _domain_sha256(
        ADAPTED_EXPECTED_COMPARISON_RECEIPT_DIGEST_DOMAIN,
        adapted_expected_comparison_receipt_bytes(value),
    )


def _validate_receipt(
    value: object,
) -> AdaptedExpectedComparisonReceiptV1:
    if type(value) is not AdaptedExpectedComparisonReceiptV1:
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    if (
        type(value.artifact_type) is not str
        or value.artifact_type
        != ADAPTED_EXPECTED_COMPARISON_RECEIPT_ARTIFACT_TYPE
        or type(value.format_version) is not str
        or value.format_version != "1"
        or type(value.status_id) is not str
        or value.status_id != ADAPTED_EXPECTED_COMPARISON_STATUS
        or type(value.decision_status) is not str
        or value.decision_status
        != ADAPTED_EXPECTED_COMPARISON_DECISION_STATUS
        or type(value.source_byte_count) is not int
        or value.source_byte_count <= 0
        or value.source_byte_count
        > MAXIMUM_ADAPTED_EXPECTED_COMPARISON_SOURCE_BYTES
    ):
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    for name in _RECEIPT_DIGEST_FIELDS:
        raw = getattr(value, name)
        if type(raw) is not str or _SHA256_RE.fullmatch(raw) is None:
            _fail(AdaptedExpectedComparisonCode.RECEIPT)
    if any(getattr(value, name) is not True for name in _RECEIPT_TRUE_FIELDS):
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    if any(getattr(value, name) is not False for name in _RECEIPT_FALSE_FIELDS):
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    return AdaptedExpectedComparisonReceiptV1(*value)


def validate_adapted_expected_comparison_receipt(
    value: object,
) -> AdaptedExpectedComparisonReceiptV1:
    """Return an exact revalidated receipt snapshot."""

    return _validate_receipt(value)


def _expected_reason_registries(
    value: _expected.IndependentExpectedLeafBundleVerificationInputV1,
) -> tuple:
    try:
        tree = json.loads(
            value.expected_leaf_bundle_bytes.decode("ascii", "strict")
        )
        exclusions = tree["allowed_exclusion_reason_codes"]
        censors = tree["allowed_censor_reason_codes"]
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError):
        _fail(AdaptedExpectedComparisonCode.EXPECTED_VERIFICATION)
    if type(exclusions) is not list or any(
        type(item) is not str for item in exclusions
    ):
        _fail(AdaptedExpectedComparisonCode.EXPECTED_VERIFICATION)
    if type(censors) is not list or any(
        type(item) is not str for item in censors
    ):
        _fail(AdaptedExpectedComparisonCode.EXPECTED_VERIFICATION)
    return tuple(exclusions), tuple(censors)


def _identity_pairs(actual: object, expected: object) -> tuple:
    return (
        (actual.descriptor_sha256, expected.descriptor_sha256),
        (actual.source_byte_count, expected.source_byte_count),
        (actual.source_sha256, expected.source_sha256),
        (actual.split_manifest_sha256, expected.split_manifest_sha256),
        (
            actual.actual_configuration_sha256,
            expected.expected_configuration_sha256,
        ),
        (actual.actual_evidence_sha256, expected.expected_evidence_sha256),
        (
            actual.actual_native_observation_sha256,
            expected.expected_native_observation_sha256,
        ),
        (actual.source_inventory_sha256, expected.source_inventory_sha256),
        (actual.coverage_ledger_sha256, expected.coverage_ledger_sha256),
        (actual.static_context_sha256, expected.static_context_sha256),
        (
            actual.evaluation_labels_sha256,
            expected.evaluation_labels_sha256,
        ),
        (
            actual.private_provenance_sha256,
            expected.private_provenance_sha256,
        ),
        (actual.fitted_state_sha256, expected.fitted_state_sha256),
        (
            actual.semantic_reconstruction_sha256,
            expected.semantic_reconstruction_sha256,
        ),
    )


def _compare(
    value: AdaptedExpectedComparisonInputV1,
) -> AdaptedExpectedComparisonResultV1:
    try:
        actual_input = _actual._snapshot_input(
            value.actual_verification_input
        )
        actual_result = _actual.verify_independent_adapted_evidence_bundle(
            actual_input
        )
    except _actual.IndependentAdaptedEvidenceBundleVerificationError:
        _fail(AdaptedExpectedComparisonCode.ACTUAL_VERIFICATION)
    except Exception:
        _fail(AdaptedExpectedComparisonCode.ACTUAL_VERIFICATION)

    # Expected material is deliberately opened and validated only after the
    # supplied actual transport has passed its independent structural layer.
    try:
        expected_input = _expected._snapshot_input(
            value.expected_verification_input
        )
        expected_result = _expected.verify_independent_expected_leaf_bundle(
            expected_input
        )
    except _expected.ExpectedLeafBundleVerificationError:
        _fail(AdaptedExpectedComparisonCode.EXPECTED_VERIFICATION)
    except Exception:
        _fail(AdaptedExpectedComparisonCode.EXPECTED_VERIFICATION)

    actual_receipt = actual_result.receipt
    expected_receipt = expected_result.receipt
    exclusions, censors = _expected_reason_registries(
        expected_input
    )
    if (
        actual_input.allowed_exclusion_reason_codes != exclusions
        or actual_input.allowed_censor_reason_codes != censors
    ):
        _fail(AdaptedExpectedComparisonCode.REASON_REGISTRY)
    if any(
        actual_value != expected_value
        for actual_value, expected_value in _identity_pairs(
            actual_receipt, expected_receipt
        )
    ):
        _fail(AdaptedExpectedComparisonCode.EVIDENCE_MISMATCH)

    try:
        receipt = AdaptedExpectedComparisonReceiptV1(
            artifact_type=(
                ADAPTED_EXPECTED_COMPARISON_RECEIPT_ARTIFACT_TYPE
            ),
            format_version="1",
            status_id=ADAPTED_EXPECTED_COMPARISON_STATUS,
            decision_status=ADAPTED_EXPECTED_COMPARISON_DECISION_STATUS,
            actual_verification_receipt_sha256=actual_result.receipt_sha256,
            expected_verification_receipt_sha256=(
                expected_result.receipt_sha256
            ),
            case_input_sha256=actual_receipt.case_input_sha256,
            adapted_evidence_bundle_sha256=(
                actual_receipt.adapted_evidence_bundle_sha256
            ),
            expected_evidence_leaf_bundle_sha256=(
                expected_receipt.expected_leaf_bundle_sha256
            ),
            allowed_exclusion_reason_codes_sha256=(
                actual_receipt.allowed_exclusion_reason_codes_sha256
            ),
            allowed_censor_reason_codes_sha256=(
                actual_receipt.allowed_censor_reason_codes_sha256
            ),
            descriptor_sha256=actual_receipt.descriptor_sha256,
            partition_sha256=actual_receipt.partition_sha256,
            source_byte_count=actual_receipt.source_byte_count,
            source_sha256=actual_receipt.source_sha256,
            split_manifest_sha256=actual_receipt.split_manifest_sha256,
            configuration_sha256=(
                actual_receipt.actual_configuration_sha256
            ),
            evidence_sha256=actual_receipt.actual_evidence_sha256,
            native_observation_sha256=(
                actual_receipt.actual_native_observation_sha256
            ),
            source_inventory_sha256=(
                actual_receipt.source_inventory_sha256
            ),
            coverage_ledger_sha256=actual_receipt.coverage_ledger_sha256,
            static_context_sha256=actual_receipt.static_context_sha256,
            evaluation_labels_sha256=(
                actual_receipt.evaluation_labels_sha256
            ),
            private_provenance_sha256=(
                actual_receipt.private_provenance_sha256
            ),
            fitted_state_sha256=actual_receipt.fitted_state_sha256,
            semantic_reconstruction_sha256=(
                actual_receipt.semantic_reconstruction_sha256
            ),
            adapter_manifest_sha256=actual_receipt.adapter_manifest_sha256,
            complete_sample_commitment_sha256=(
                actual_receipt.complete_sample_commitment_sha256
            ),
            raw_reconstruction_sha256=(
                actual_receipt.raw_reconstruction_sha256
            ),
            actual_verification_rerun=True,
            expected_verification_rerun_after_actual_verification=True,
            reason_registries_matched=True,
            descriptor_source_split_matched=True,
            configuration_evidence_native_matched=True,
            phase_c_leaf_digests_matched=True,
            raw_reconstruction_policy_recomputed=True,
            actual_expected_leaf_equality_recomputed=True,
            decision_made=False,
            execution_attested=False,
            containment_attested=False,
            output_blind_adapter_child_enforced=False,
            expected_material_nonexposure_attested=False,
            adapter_source_execution_identity_attested=False,
            external_custody_authenticated=False,
            semantic_truth_attested=False,
            format_specific_payload_semantics_attested=False,
            publication_artifacts_rebuilt=False,
            generalization_attested=False,
        )
        receipt_bytes = adapted_expected_comparison_receipt_bytes(receipt)
        return AdaptedExpectedComparisonResultV1(
            receipt=receipt,
            receipt_bytes=receipt_bytes,
            receipt_sha256=_domain_sha256(
                ADAPTED_EXPECTED_COMPARISON_RECEIPT_DIGEST_DOMAIN,
                receipt_bytes,
            ),
        )
    except AdaptedExpectedComparisonError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(AdaptedExpectedComparisonCode.INTERNAL)


def compare_adapted_evidence_to_expected(
    value: AdaptedExpectedComparisonInputV1,
) -> AdaptedExpectedComparisonResultV1:
    """Rerun actual then expected verification and compare all leaf identities."""

    if type(value) is not AdaptedExpectedComparisonInputV1:
        _fail(AdaptedExpectedComparisonCode.INPUT_TYPE)
    try:
        AdaptedExpectedComparisonInputV1.__post_init__(value)
        return _compare(value)
    except AdaptedExpectedComparisonError:
        raise
    except (AttributeError, TypeError):
        _fail(AdaptedExpectedComparisonCode.INPUT_TYPE)
    except Exception:
        _fail(AdaptedExpectedComparisonCode.INTERNAL)


def validate_adapted_expected_comparison_result(
    value: AdaptedExpectedComparisonResultV1,
    raw_input: AdaptedExpectedComparisonInputV1,
) -> AdaptedExpectedComparisonResultV1:
    """Recompute comparison from raw inputs and require exact result identity."""

    if type(value) is not AdaptedExpectedComparisonResultV1:
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    try:
        receipt = _validate_receipt(value.receipt)
        receipt_bytes = adapted_expected_comparison_receipt_bytes(receipt)
        if (
            type(value.receipt_bytes) is not bytes
            or type(value.receipt_sha256) is not str
            or value.receipt_bytes != receipt_bytes
            or value.receipt_sha256
            != _domain_sha256(
                ADAPTED_EXPECTED_COMPARISON_RECEIPT_DIGEST_DOMAIN,
                receipt_bytes,
            )
        ):
            _fail(AdaptedExpectedComparisonCode.RECEIPT)
    except AdaptedExpectedComparisonError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    expected = compare_adapted_evidence_to_expected(raw_input)
    if value != expected:
        _fail(AdaptedExpectedComparisonCode.RECEIPT)
    return expected


__all__ = [
    "ADAPTED_EXPECTED_COMPARISON_DECISION_STATUS",
    "ADAPTED_EXPECTED_COMPARISON_RECEIPT_ARTIFACT_TYPE",
    "ADAPTED_EXPECTED_COMPARISON_RECEIPT_DIGEST_DOMAIN",
    "ADAPTED_EXPECTED_COMPARISON_STATUS",
    "AdaptedExpectedComparisonCode",
    "AdaptedExpectedComparisonError",
    "AdaptedExpectedComparisonInputV1",
    "AdaptedExpectedComparisonReceiptV1",
    "AdaptedExpectedComparisonResultV1",
    "MAXIMUM_ADAPTED_EXPECTED_COMPARISON_RECEIPT_BYTES",
    "MAXIMUM_ADAPTED_EXPECTED_COMPARISON_SOURCE_BYTES",
    "adapted_expected_comparison_receipt_bytes",
    "adapted_expected_comparison_receipt_sha256",
    "compare_adapted_evidence_to_expected",
    "validate_adapted_expected_comparison_receipt",
    "validate_adapted_expected_comparison_result",
]
