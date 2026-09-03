"""Additive authority freeze for exact expected-evidence leaf bundles.

This boundary is intentionally layered on top of the frozen V1 publication
authority and candidate freezer.  It authenticates a separately anchored
expected-leaf profile, rebuilds the distinct V2 execution-input set, validates
every raw supplemental verifier input, and only then permits the existing
candidate freezer to invoke an adapter.

The worker request continues to carry an opaque digest.  Matching that digest
to the rebuilt V2 input set is not evidence that the worker parsed or consumed
the input set, and an expected bundle supplied to this boundary is not thereby
an oracle-generated output.  The returned candidate consequently stays on the
development HOLD path, makes no decision, and keeps all execution, custody,
semantic, and generalization claims false.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import NamedTuple, Tuple

from . import adapter_contract as _contract
from . import adapter_expected_leaf_archive as _leaf_archive
from . import adapter_expected_leaf_authority as _leaf_authority
from . import adapter_expected_leaf_authority_types as _leaf_types
from . import adapter_expected_leaf_bundle_verifier as _leaf_verifier
from . import adapter_expected_leaf_execution_input as _execution_input
from . import adapter_oracle_abi as _oracle_abi
from . import adapter_oracle_independent_verifier as _v1_verifier
from . import adapter_publication_authority as _base_authority
from . import adapter_publication_decision_freeze as _base_freeze
from . import adapter_publication_payloads as _payloads
from .adapter_expected_leaf_authority import (
    ValidatedApprovedExpectedLeafAuthorityV1,
    ValidatedIndependentGoldenExpectedLeafExtensionV1,
)
from .adapter_expected_leaf_authority_types import (
    ApprovedExpectedLeafAuthorityInputV1,
    ApprovedExpectedLeafCaseExpectationV1,
    IndependentGoldenExpectedLeafExtensionInputV1,
)
from .adapter_expected_leaf_bundle_verifier import (
    IndependentExpectedLeafBundleVerificationInputV1,
    IndependentExpectedLeafBundleVerificationResultV1,
)
from .adapter_expected_leaf_execution_input import (
    PreparedDecisionExecutionInputSetV2,
)
from .adapter_oracle_abi import OracleWorkerRequestV1
from .adapter_publication_authority import (
    ValidatedIndependentGoldenReceiptV1,
)
from .adapter_publication_authority_types import (
    ApprovedCaseExpectationV1,
    ApprovedPublicationAuthorityInputV1,
    DecisionPublicationFreezeInputV1,
    IndependentGoldenReceiptInputV1,
    VerifiedDetachedCaseInputV2,
)
from .adapter_publication_decision_freeze import (
    FrozenDecisionPublicationInputV1,
)
from .adapter_publication_types import (
    PUBLICATION_DEVELOPMENT_STATUS,
    PublicationBindingInputV1,
)


EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-leaf-authority-freeze-receipt.v1"
)
EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_DIGEST_DOMAIN = (
    EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_ARTIFACT_TYPE
)
EXPECTED_LEAF_AUTHORITY_FREEZE_VALIDATED_CASE_RESULT_SET_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-leaf-authority-freeze-"
    "validated-case-result-set.v1"
)
EXPECTED_LEAF_AUTHORITY_FREEZE_STATUS = (
    "EXPECTED_LEAF_AUTHORITY_AND_V2_INPUT_SET_MATCHED_"
    "UNATTESTED_DEVELOPMENT_EXECUTION"
)
EXPECTED_LEAF_AUTHORITY_FREEZE_DECISION_STATUS = (
    "NOT_MADE_BY_EXPECTED_LEAF_FREEZER"
)
MAXIMUM_EXPECTED_LEAF_FREEZE_CASES = 4096
MAXIMUM_EXPECTED_LEAF_FREEZE_VALIDATION_WORK_BYTES = 512 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_BYTES = 64 * 1024
MAXIMUM_EXPECTED_LEAF_AUTHORITY_FREEZE_CASE_RESULT_SET_BYTES = (
    4 * 1024 * 1024
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_V1_RAW_INPUT_FIELDS = (
    "oracle_registry_bytes",
    "source_archive_inventory_bytes",
    "source_archive_bytes",
    "source_archive_membership_receipt_bytes",
    "source_policy_receipt_bytes",
    "independent_golden_receipt_bytes",
    "request_frame_bytes",
    "response_frame_bytes",
    "stderr_bytes",
    "interpreter_executable_bytes",
    "development_runner_receipt_bytes",
)


class ExpectedLeafAuthorityFreezeCode(str, Enum):
    """Closed, interpolation-free failures at the additive freeze boundary."""

    INPUT_TYPE = "EXPECTED_LEAF_FREEZE_INPUT_TYPE"
    RESOURCE = "EXPECTED_LEAF_FREEZE_RESOURCE"
    BASE_AUTHORITY = "EXPECTED_LEAF_FREEZE_BASE_AUTHORITY"
    LEAF_AUTHORITY = "EXPECTED_LEAF_FREEZE_LEAF_AUTHORITY"
    CASE_INVENTORY = "EXPECTED_LEAF_FREEZE_CASE_INVENTORY"
    BASE_CASE = "EXPECTED_LEAF_FREEZE_BASE_CASE"
    GOLDEN_EXTENSION = "EXPECTED_LEAF_FREEZE_GOLDEN_EXTENSION"
    SUPPLEMENTAL_VERIFICATION = (
        "EXPECTED_LEAF_FREEZE_SUPPLEMENTAL_VERIFICATION"
    )
    REQUEST_BINDING = "EXPECTED_LEAF_FREEZE_REQUEST_BINDING"
    RECEIPT = "EXPECTED_LEAF_FREEZE_RECEIPT"
    POSTMUTATION = "EXPECTED_LEAF_FREEZE_POSTMUTATION"
    BASE_CANDIDATE = "EXPECTED_LEAF_FREEZE_BASE_CANDIDATE"
    INTERNAL = "EXPECTED_LEAF_FREEZE_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExpectedLeafAuthorityFreezeCode.INPUT_TYPE: (
            "expected-leaf freeze input has an invalid exact type"
        ),
        ExpectedLeafAuthorityFreezeCode.RESOURCE: (
            "expected-leaf freeze validation exceeds a resource ceiling"
        ),
        ExpectedLeafAuthorityFreezeCode.BASE_AUTHORITY: (
            "expected-leaf freeze base authority does not validate"
        ),
        ExpectedLeafAuthorityFreezeCode.LEAF_AUTHORITY: (
            "expected-leaf freeze leaf authority does not validate"
        ),
        ExpectedLeafAuthorityFreezeCode.CASE_INVENTORY: (
            "expected-leaf freeze case inventory does not match"
        ),
        ExpectedLeafAuthorityFreezeCode.BASE_CASE: (
            "expected-leaf freeze base case does not match authority"
        ),
        ExpectedLeafAuthorityFreezeCode.GOLDEN_EXTENSION: (
            "expected-leaf freeze golden extension does not match"
        ),
        ExpectedLeafAuthorityFreezeCode.SUPPLEMENTAL_VERIFICATION: (
            "expected-leaf freeze supplemental raw verification failed"
        ),
        ExpectedLeafAuthorityFreezeCode.REQUEST_BINDING: (
            "expected-leaf freeze worker request binding does not match"
        ),
        ExpectedLeafAuthorityFreezeCode.RECEIPT: (
            "expected-leaf freeze receipt is invalid"
        ),
        ExpectedLeafAuthorityFreezeCode.POSTMUTATION: (
            "expected-leaf freeze input changed during adapter validation"
        ),
        ExpectedLeafAuthorityFreezeCode.BASE_CANDIDATE: (
            "expected-leaf freeze base candidate could not be recomputed"
        ),
        ExpectedLeafAuthorityFreezeCode.INTERNAL: (
            "expected-leaf freeze failed internally"
        ),
    }
)


class ExpectedLeafAuthorityFreezeError(ValueError):
    """One fixed coded failure without attacker-controlled interpolation."""

    def __init__(self, code: ExpectedLeafAuthorityFreezeCode) -> None:
        if type(code) is not ExpectedLeafAuthorityFreezeCode:
            raise TypeError("expected-leaf freeze code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


@dataclass(frozen=True)
class ExpectedLeafAuthorityCaseInputV1:
    """One case ID, canonical golden extension, and complete raw verifier input."""

    case_authority_id: str
    golden_extension_input: IndependentGoldenExpectedLeafExtensionInputV1
    supplemental_verification_input: (
        IndependentExpectedLeafBundleVerificationInputV1
    )

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafAuthorityCaseInputV1:
            raise TypeError("expected-leaf authority case input must be exact")
        if (
            type(self.case_authority_id) is not str
            or _SHA256_RE.fullmatch(self.case_authority_id) is None
        ):
            raise ValueError("case authority ID must be a lowercase digest")
        if (
            type(self.golden_extension_input)
            is not IndependentGoldenExpectedLeafExtensionInputV1
        ):
            raise TypeError("golden extension input must be exact")
        if (
            type(self.supplemental_verification_input)
            is not IndependentExpectedLeafBundleVerificationInputV1
        ):
            raise TypeError("supplemental verification input must be exact")


class FrozenExpectedLeafAuthorityCaseV1(NamedTuple):
    """Immutable per-case authority and raw structural-verification result."""

    case_authority_id: str
    approved_case: ApprovedExpectedLeafCaseExpectationV1
    base_case: ApprovedCaseExpectationV1
    golden_extension: ValidatedIndependentGoldenExpectedLeafExtensionV1
    archive_membership: (
        _leaf_archive.ValidatedExpectedLeafArchiveMembershipV1
    )
    supplemental_verification: (
        IndependentExpectedLeafBundleVerificationResultV1
    )
    supplemental_verification_input: (
        IndependentExpectedLeafBundleVerificationInputV1
    )
    worker_request: OracleWorkerRequestV1
    expected_leaf_bundle_bytes: bytes


class ExpectedLeafAuthorityFreezeReceiptV1(NamedTuple):
    """Deterministic narrow receipt; successful validation remains nondecision."""

    artifact_type: str
    format_version: str
    status_id: str
    decision_status: str
    case_count: int
    base_approved_profile_sha256: str
    expected_leaf_authority_profile_sha256: str
    execution_input_set_v2_sha256: str
    expected_leaf_archive_sha256: str
    reason_registry_sha256: str
    semantic_profile_sha256: str
    verifier_closure_sha256: str
    validated_case_result_set_sha256: str
    base_profile_anchor_bytes_matched: bool
    expected_leaf_profile_anchor_bytes_matched: bool
    parent_authority_link_matched: bool
    reason_registry_exact_categories_matched: bool
    semantic_profile_and_verifier_closure_matched: bool
    expected_leaf_archive_membership_recomputed: bool
    golden_extensions_recomputed: bool
    expected_leaf_bundles_deeply_revalidated: bool
    v2_execution_input_set_rebuilt: bool
    worker_request_v2_digest_matched: bool
    base_candidate_recomputed: bool
    decision_made: bool
    execution_attested: bool
    containment_attested: bool
    external_custody_attested: bool
    external_anchor_provenance_attested: bool
    profile_authorship_attested: bool
    execution_input_set_consumption_attested: bool
    oracle_generated_expected_leaf_bundle_attested: bool
    source_policy_semantics_independently_evaluated: bool
    semantic_truth_attested: bool
    format_specific_payload_semantics_attested: bool
    adapted_evidence_leaf_complete: bool
    publication_artifacts_rebuilt: bool
    v2_guard_manifest_built: bool
    generalization_attested: bool


class FrozenExpectedLeafAuthorityDecisionInputV1(NamedTuple):
    """Base candidate plus additive authority, input set, and leaf snapshots."""

    candidate_status: str
    decision_status: str
    base_candidate: FrozenDecisionPublicationInputV1
    prepared_execution_input_set: PreparedDecisionExecutionInputSetV2
    expected_leaf_authority: ValidatedApprovedExpectedLeafAuthorityV1
    cases: Tuple[FrozenExpectedLeafAuthorityCaseV1, ...]
    receipt: ExpectedLeafAuthorityFreezeReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str


_RECEIPT_DIGEST_FIELDS = (
    "base_approved_profile_sha256",
    "expected_leaf_authority_profile_sha256",
    "execution_input_set_v2_sha256",
    "expected_leaf_archive_sha256",
    "reason_registry_sha256",
    "semantic_profile_sha256",
    "verifier_closure_sha256",
    "validated_case_result_set_sha256",
)
_RECEIPT_TRUE_FIELDS = (
    "base_profile_anchor_bytes_matched",
    "expected_leaf_profile_anchor_bytes_matched",
    "parent_authority_link_matched",
    "reason_registry_exact_categories_matched",
    "semantic_profile_and_verifier_closure_matched",
    "expected_leaf_archive_membership_recomputed",
    "golden_extensions_recomputed",
    "expected_leaf_bundles_deeply_revalidated",
    "v2_execution_input_set_rebuilt",
    "worker_request_v2_digest_matched",
    "base_candidate_recomputed",
)
_RECEIPT_FALSE_FIELDS = (
    "decision_made",
    "execution_attested",
    "containment_attested",
    "external_custody_attested",
    "external_anchor_provenance_attested",
    "profile_authorship_attested",
    "execution_input_set_consumption_attested",
    "oracle_generated_expected_leaf_bundle_attested",
    "source_policy_semantics_independently_evaluated",
    "semantic_truth_attested",
    "format_specific_payload_semantics_attested",
    "adapted_evidence_leaf_complete",
    "publication_artifacts_rebuilt",
    "v2_guard_manifest_built",
    "generalization_attested",
)


class _PreparedLeafCase(NamedTuple):
    snapshot: ExpectedLeafAuthorityCaseInputV1
    approved_case: ApprovedExpectedLeafCaseExpectationV1
    base_case: ApprovedCaseExpectationV1
    base_request_case: VerifiedDetachedCaseInputV2
    base_golden: ValidatedIndependentGoldenReceiptV1
    golden_extension: ValidatedIndependentGoldenExpectedLeafExtensionV1
    supplemental_verification: (
        IndependentExpectedLeafBundleVerificationResultV1
    )
    worker_request: OracleWorkerRequestV1


def _fail(code: ExpectedLeafAuthorityFreezeCode) -> None:
    raise ExpectedLeafAuthorityFreezeError(code) from None


def _validate_receipt(
    value: object,
) -> ExpectedLeafAuthorityFreezeReceiptV1:
    if type(value) is not ExpectedLeafAuthorityFreezeReceiptV1:
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    fixed = (
        (
            value.artifact_type,
            EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_ARTIFACT_TYPE,
        ),
        (value.format_version, "1"),
        (value.status_id, EXPECTED_LEAF_AUTHORITY_FREEZE_STATUS),
        (
            value.decision_status,
            EXPECTED_LEAF_AUTHORITY_FREEZE_DECISION_STATUS,
        ),
    )
    if any(
        type(observed) is not str or observed != expected
        for observed, expected in fixed
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    if (
        type(value.case_count) is not int
        or value.case_count < 1
        or value.case_count > MAXIMUM_EXPECTED_LEAF_FREEZE_CASES
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    if any(
        type(getattr(value, name)) is not str
        or _SHA256_RE.fullmatch(getattr(value, name)) is None
        for name in _RECEIPT_DIGEST_FIELDS
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    if any(
        getattr(value, name) is not True
        for name in _RECEIPT_TRUE_FIELDS
    ) or any(
        getattr(value, name) is not False
        for name in _RECEIPT_FALSE_FIELDS
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    return value


def expected_leaf_authority_freeze_receipt_bytes(
    value: ExpectedLeafAuthorityFreezeReceiptV1,
) -> bytes:
    """Serialize one nonauthority receipt as bounded canonical ASCII JSON."""

    receipt = _validate_receipt(value)
    try:
        encoded = json.dumps(
            receipt._asdict(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (AttributeError, TypeError, ValueError, UnicodeError):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    if (
        not encoded
        or len(encoded)
        > MAXIMUM_EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_BYTES
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    return encoded


def expected_leaf_authority_freeze_receipt_sha256(
    value: ExpectedLeafAuthorityFreezeReceiptV1,
) -> str:
    """Hash exact canonical receipt bytes under the receipt artifact domain."""

    encoded = expected_leaf_authority_freeze_receipt_bytes(value)
    try:
        return _leaf_authority.domain_separated_sha256(
            EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_DIGEST_DOMAIN,
            encoded,
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)


def expected_leaf_authority_freeze_validated_case_result_set_bytes(
    values: Tuple[FrozenExpectedLeafAuthorityCaseV1, ...],
) -> bytes:
    """Serialize the ordered post-run case identities behind the receipt."""

    if (
        type(values) is not tuple
        or not values
        or len(values) > MAXIMUM_EXPECTED_LEAF_FREEZE_CASES
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    cases = []
    try:
        for ordinal, item in enumerate(values):
            if (
                type(item) is not FrozenExpectedLeafAuthorityCaseV1
                or type(item.case_authority_id) is not str
                or _SHA256_RE.fullmatch(item.case_authority_id) is None
                or type(item.approved_case)
                is not ApprovedExpectedLeafCaseExpectationV1
                or type(item.base_case) is not ApprovedCaseExpectationV1
                or type(item.golden_extension)
                is not ValidatedIndependentGoldenExpectedLeafExtensionV1
                or type(item.archive_membership)
                is not _leaf_archive.ValidatedExpectedLeafArchiveMembershipV1
                or type(item.supplemental_verification)
                is not IndependentExpectedLeafBundleVerificationResultV1
                or type(item.supplemental_verification_input)
                is not IndependentExpectedLeafBundleVerificationInputV1
                or type(item.worker_request) is not OracleWorkerRequestV1
                or type(item.expected_leaf_bundle_bytes) is not bytes
                or item.approved_case.case_ordinal != ordinal
            ):
                _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
            cases.append(
                {
                    "archive_membership_receipt_sha256": (
                        _leaf_archive
                        .expected_leaf_archive_membership_receipt_sha256(
                            item.archive_membership
                        )
                    ),
                    "base_case_expectation_sha256": (
                        _leaf_authority.approved_case_expectation_sha256(
                            item.base_case
                        )
                    ),
                    # This membership digest was recomputed from the same
                    # snapshot bytes and cross-checked before callbacks.  Reuse
                    # avoids a third complete post-run bundle hashing pass.
                    "bundle_sha256": (
                        item.archive_membership.bundle_domain_sha256
                    ),
                    "case_authority_id": item.case_authority_id,
                    "case_ordinal": ordinal,
                    "golden_extension_sha256": (
                        item.golden_extension.receipt_sha256
                    ),
                    "supplemental_verification_receipt_sha256": (
                        item.supplemental_verification.receipt_sha256
                    ),
                }
            )
        encoded = json.dumps(
            {
                "artifact_type": (
                    EXPECTED_LEAF_AUTHORITY_FREEZE_VALIDATED_CASE_RESULT_SET_DIGEST_DOMAIN
                ),
                "cases": cases,
                "format_version": "1",
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except ExpectedLeafAuthorityFreezeError:
        raise
    except (AttributeError, TypeError, ValueError, UnicodeError):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    if (
        not encoded
        or len(encoded)
        > MAXIMUM_EXPECTED_LEAF_AUTHORITY_FREEZE_CASE_RESULT_SET_BYTES
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)
    return encoded


def expected_leaf_authority_freeze_validated_case_result_set_sha256(
    values: Tuple[FrozenExpectedLeafAuthorityCaseV1, ...],
) -> str:
    """Commit the canonical ordered post-run case set under its own domain."""

    encoded = (
        expected_leaf_authority_freeze_validated_case_result_set_bytes(
            values
        )
    )
    try:
        return _leaf_authority.domain_separated_sha256(
            EXPECTED_LEAF_AUTHORITY_FREEZE_VALIDATED_CASE_RESULT_SET_DIGEST_DOMAIN,
            encoded,
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafAuthorityFreezeCode.RECEIPT)


def _clone_dataclass(value: object, expected_type: type) -> object:
    if type(value) is not expected_type:
        raise TypeError("dataclass input has an invalid exact type")
    return expected_type(
        **{
            item.name: getattr(value, item.name)
            for item in fields(expected_type)
            if item.init
        }
    )


def _snapshot_leaf_authority_input(
    value: object,
) -> ApprovedExpectedLeafAuthorityInputV1:
    if type(value) is not ApprovedExpectedLeafAuthorityInputV1:
        raise TypeError("expected-leaf authority input must be exact")
    anchor = _clone_dataclass(
        value.anchor,
        _leaf_types.ApprovedExpectedLeafAuthorityProfileAnchorV1,
    )
    source_inputs = tuple(
        _leaf_types.ExpectedLeafVerifierSourceInputV1(
            module_id=item.module_id,
            source_bytes=item.source_bytes,
        )
        for item in value.verifier_source_inputs
    )
    return ApprovedExpectedLeafAuthorityInputV1(
        profile_bytes=value.profile_bytes,
        anchor=anchor,
        verifier_source_inputs=source_inputs,
    )


def _snapshot_leaf_case(
    value: object,
) -> ExpectedLeafAuthorityCaseInputV1:
    if type(value) is not ExpectedLeafAuthorityCaseInputV1:
        raise TypeError("expected-leaf case input must be exact")
    golden_input = value.golden_extension_input
    if (
        type(golden_input)
        is not IndependentGoldenExpectedLeafExtensionInputV1
    ):
        raise TypeError("golden extension input must be exact")
    golden_receipt = _clone_dataclass(
        golden_input.receipt,
        _leaf_types.IndependentGoldenExpectedLeafExtensionV1,
    )
    golden_snapshot = IndependentGoldenExpectedLeafExtensionInputV1(
        receipt=golden_receipt,
        receipt_bytes=golden_input.receipt_bytes,
    )
    supplemental = value.supplemental_verification_input
    if (
        type(supplemental)
        is not IndependentExpectedLeafBundleVerificationInputV1
        or type(supplemental.oracle_input)
        is not _v1_verifier.IndependentOracleVerificationInputV1
    ):
        raise TypeError("supplemental verification input must be exact")
    oracle_snapshot = _v1_verifier.IndependentOracleVerificationInputV1(
        **{
            name: getattr(supplemental.oracle_input, name)
            for name in _V1_RAW_INPUT_FIELDS
        }
    )
    supplemental_snapshot = (
        IndependentExpectedLeafBundleVerificationInputV1(
            oracle_input=oracle_snapshot,
            expected_leaf_bundle_bytes=(
                supplemental.expected_leaf_bundle_bytes
            ),
        )
    )
    return ExpectedLeafAuthorityCaseInputV1(
        case_authority_id=value.case_authority_id,
        golden_extension_input=golden_snapshot,
        supplemental_verification_input=supplemental_snapshot,
    )


def _snapshot_leaf_cases(
    values: object,
) -> Tuple[ExpectedLeafAuthorityCaseInputV1, ...]:
    if type(values) is not tuple or not values:
        raise TypeError("expected-leaf cases must be a nonempty exact tuple")
    if len(values) > MAXIMUM_EXPECTED_LEAF_FREEZE_CASES:
        _fail(ExpectedLeafAuthorityFreezeCode.RESOURCE)
    return tuple(_snapshot_leaf_case(item) for item in values)


def _add_work(total: int, amount: object) -> int:
    if type(amount) is not int or amount < 0:
        raise TypeError("validation work amount must be exact")
    result = total + amount
    if result > MAXIMUM_EXPECTED_LEAF_FREEZE_VALIDATION_WORK_BYTES:
        _fail(ExpectedLeafAuthorityFreezeCode.RESOURCE)
    return result


def _preflight_validation_work(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    leaf_cases: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> None:
    total = 0
    if type(expected_leaf_archive_inventory_bytes) is not bytes or type(
        expected_leaf_archive_bytes
    ) is not bytes:
        raise TypeError("expected-leaf archive inputs must be exact bytes")
    total = _add_work(total, len(authority_input.profile_bytes))
    total = _add_work(total, len(leaf_authority_input.profile_bytes))
    for name in PublicationBindingInputV1.__dataclass_fields__:
        value = getattr(request.bindings, name)
        if type(value) is not bytes:
            raise TypeError("publication binding fields must be exact bytes")
        total = _add_work(total, len(value))
    # The leaf authority independently revalidates both archive pairs.
    total = _add_work(
        total,
        len(request.bindings.source_tree_manifest_bytes),
    )
    total = _add_work(total, len(request.bindings.source_tree_archive_bytes))
    total = _add_work(total, len(expected_leaf_archive_inventory_bytes))
    total = _add_work(total, len(expected_leaf_archive_bytes))
    verifier_source_input_bytes = 0
    for item in leaf_authority_input.verifier_source_inputs:
        if (
            type(item) is not _leaf_types.ExpectedLeafVerifierSourceInputV1
            or type(item.source_bytes) is not bytes
        ):
            raise TypeError("verifier source inputs must be exact")
        verifier_source_input_bytes += len(item.source_bytes)
    total = _add_work(total, verifier_source_input_bytes)
    leaf_archive_revalidation = (
        len(expected_leaf_archive_inventory_bytes)
        + len(expected_leaf_archive_bytes)
    )
    source_archive_revalidation = (
        len(request.bindings.source_tree_manifest_bytes)
        + len(request.bindings.source_tree_archive_bytes)
    )
    oracle_registry_revalidation = len(
        request.bindings.oracle_registry_bytes
    )
    for item in leaf_cases:
        total = _add_work(
            total,
            len(item.golden_extension_input.receipt_bytes),
        )
        raw = item.supplemental_verification_input.oracle_input
        for name in _V1_RAW_INPUT_FIELDS:
            value = getattr(raw, name)
            if type(value) is not bytes:
                raise TypeError("raw verifier fields must be exact bytes")
            total = _add_work(total, len(value))
        # Golden-extension validation revalidates the verifier-source closure
        # from the parent archive independently of the supplemental V1 pass
        # already represented by the raw fields above.
        total = _add_work(total, source_archive_revalidation)
        # This wrapper and the existing base freezer each independently
        # validate the case golden receipt against the full oracle registry.
        total = _add_work(total, oracle_registry_revalidation)
        total = _add_work(total, oracle_registry_revalidation)
        # Hardened golden-extension validation reparses both anchored profile
        # byte strings for every case instead of trusting their typed views.
        total = _add_work(total, len(authority_input.profile_bytes))
        total = _add_work(total, len(leaf_authority_input.profile_bytes))
        total = _add_work(total, verifier_source_input_bytes)
        bundle_byte_count = len(
            item.supplemental_verification_input
            .expected_leaf_bundle_bytes
        )
        total = _add_work(
            total,
            bundle_byte_count,
        )
        # The golden envelope parser and the supplemental deep verifier are
        # separate complete bundle passes.
        total = _add_work(total, bundle_byte_count)
        # Golden-extension validation resolves the object from raw archive
        # bytes anew instead of trusting the authority-side archive object.
        total = _add_work(total, leaf_archive_revalidation)
    # The existing base freezer performs another complete binding/case pass.
    total = _add_work(total, len(authority_input.profile_bytes))
    for name in PublicationBindingInputV1.__dataclass_fields__:
        total = _add_work(total, len(getattr(request.bindings, name)))
    for case in request.cases:
        if type(case) is not VerifiedDetachedCaseInputV2:
            raise TypeError("base request cases must have exact V2 types")
        golden = case.independent_golden
        if type(golden) is not IndependentGoldenReceiptInputV1:
            raise TypeError("base independent golden input must be exact")
        total = _add_work(total, len(golden.receipt_bytes))
        total = _add_work(total, len(golden.oracle_source_bytes))


def _validate_initial_types(
    request: object,
    authority_input: object,
    leaf_authority_input: object,
    leaf_case_inputs: object,
    *,
    expected_leaf_archive_inventory_bytes: object,
    expected_leaf_archive_bytes: object,
) -> Tuple[
    ApprovedExpectedLeafAuthorityInputV1,
    Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
]:
    if type(request) is not DecisionPublicationFreezeInputV1:
        _fail(ExpectedLeafAuthorityFreezeCode.INPUT_TYPE)
    if type(authority_input) is not ApprovedPublicationAuthorityInputV1:
        _fail(ExpectedLeafAuthorityFreezeCode.INPUT_TYPE)
    if (
        type(leaf_authority_input)
        is not ApprovedExpectedLeafAuthorityInputV1
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.INPUT_TYPE)
    if type(expected_leaf_archive_inventory_bytes) is not bytes or type(
        expected_leaf_archive_bytes
    ) is not bytes:
        _fail(ExpectedLeafAuthorityFreezeCode.INPUT_TYPE)
    try:
        DecisionPublicationFreezeInputV1.__post_init__(request)
        ApprovedPublicationAuthorityInputV1.__post_init__(authority_input)
        leaf_authority_snapshot = _snapshot_leaf_authority_input(
            leaf_authority_input
        )
        leaf_case_snapshots = _snapshot_leaf_cases(leaf_case_inputs)
    except ExpectedLeafAuthorityFreezeError:
        raise
    except ValueError:
        _fail(ExpectedLeafAuthorityFreezeCode.RESOURCE)
    except (AttributeError, TypeError):
        _fail(ExpectedLeafAuthorityFreezeCode.INPUT_TYPE)
    if (
        len(request.cases) != len(leaf_case_snapshots)
        or len(request.cases) > MAXIMUM_EXPECTED_LEAF_FREEZE_CASES
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.CASE_INVENTORY)
    try:
        _preflight_validation_work(
            request,
            authority_input,
            leaf_authority_snapshot,
            leaf_case_snapshots,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except ExpectedLeafAuthorityFreezeError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(ExpectedLeafAuthorityFreezeCode.INPUT_TYPE)
    return leaf_authority_snapshot, leaf_case_snapshots


def _validate_base_authority(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
) -> _base_authority.ValidatedPublicationBindingAuthorityV1:
    try:
        value = _base_authority.validate_publication_binding_authority(
            request.bindings,
            request.public_ids,
            authority_input,
        )
        _base_authority.validate_approved_profile_registry(
            value.authority.profile,
            request.public_ids,
        )
        return value
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.BASE_AUTHORITY)


def _validate_leaf_authority(
    request: DecisionPublicationFreezeInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    base_authority: _base_authority.ValidatedPublicationBindingAuthorityV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> ValidatedApprovedExpectedLeafAuthorityV1:
    try:
        return _leaf_authority.validate_approved_expected_leaf_authority(
            leaf_authority_input,
            parent_authority=base_authority.authority,
            public_identifier_registry=request.public_ids,
            source_archive_inventory_bytes=(
                request.bindings.source_tree_manifest_bytes
            ),
            source_archive_bytes=request.bindings.source_tree_archive_bytes,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.LEAF_AUTHORITY)


def _static_base_case_expectation(
    value: VerifiedDetachedCaseInputV2,
    golden: ValidatedIndependentGoldenReceiptV1,
    *,
    case_ordinal: int,
) -> ApprovedCaseExpectationV1:
    descriptor = _payloads.adapter_descriptor_payload(value.descriptor)
    split = _payloads.split_manifest_payload(value.split_manifest)
    complete = _payloads.complete_sample_commitment_payload(
        value.descriptor,
        value.complete_sample,
    )
    expected = _payloads.expected_evidence_payload(value.expected_evidence)
    configuration = (
        _payloads.identity_bearing_native_configuration_payload(
            value.expected_configuration
        )
    )
    run = _payloads.conformance_run_payload(value.conformance_run)
    identity = value.descriptor.identity
    return ApprovedCaseExpectationV1(
        adapter_id=identity.adapter_id,
        adapter_version=identity.adapter_version,
        case_ordinal=case_ordinal,
        complete_sample_commitment_sha256=complete.payload_sha256,
        conformance_run_sha256=run.payload_sha256,
        descriptor_sha256=descriptor.payload_sha256,
        expected_configuration_sha256=configuration.payload_sha256,
        expected_evidence_sha256=expected.payload_sha256,
        independent_golden_receipt_sha256=golden.receipt_sha256,
        native_observation_sha256=_contract.native_observation_digest(
            value.expected_configuration
        ),
        sample_root_sha256=value.conformance_run.sample_root_sha256,
        source_sha256=hashlib.sha256(value.source_bytes).hexdigest(),
        split_manifest_sha256=split.payload_sha256,
    )


def _validated_base_cases(
    request: DecisionPublicationFreezeInputV1,
    base_authority: _base_authority.ValidatedPublicationBindingAuthorityV1,
) -> dict:
    profile_cases = base_authority.authority.profile.case_expectations
    provisional = []
    try:
        for case in request.cases:
            golden = _base_authority.validate_independent_golden_receipt(
                case.independent_golden,
                oracle_registry_bytes=request.bindings.oracle_registry_bytes,
            )
            observed = _static_base_case_expectation(
                case,
                golden,
                case_ordinal=0,
            )
            provisional.append((case, golden, observed))
    except ExpectedLeafAuthorityFreezeError:
        raise
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.BASE_CASE)
    provisional.sort(
        key=lambda item: (
            item[2].sample_root_sha256,
            item[2].expected_evidence_sha256,
            item[2].adapter_id,
        )
    )
    keys = tuple(
        (
            item[2].sample_root_sha256,
            item[2].expected_evidence_sha256,
            item[2].adapter_id,
        )
        for item in provisional
    )
    if len(set(keys)) != len(keys) or len(provisional) != len(profile_cases):
        _fail(ExpectedLeafAuthorityFreezeCode.CASE_INVENTORY)
    result = {}
    try:
        for ordinal, (case, golden, _observed) in enumerate(provisional):
            observed = _static_base_case_expectation(
                case,
                golden,
                case_ordinal=ordinal,
            )
            expectation = profile_cases[ordinal]
            if observed != expectation:
                _fail(ExpectedLeafAuthorityFreezeCode.BASE_CASE)
            case_authority_id = (
                _leaf_authority.expected_leaf_case_authority_id(expectation)
            )
            if case_authority_id in result:
                _fail(ExpectedLeafAuthorityFreezeCode.CASE_INVENTORY)
            result[case_authority_id] = (case, expectation, golden)
    except ExpectedLeafAuthorityFreezeError:
        raise
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.BASE_CASE)
    return result


def _validate_raw_case_binding(
    snapshot: ExpectedLeafAuthorityCaseInputV1,
    *,
    approved_case: ApprovedExpectedLeafCaseExpectationV1,
    base_case_input: VerifiedDetachedCaseInputV2,
    base_golden: ValidatedIndependentGoldenReceiptV1,
    request: DecisionPublicationFreezeInputV1,
    execution_input_set_sha256: str,
) -> OracleWorkerRequestV1:
    raw = snapshot.supplemental_verification_input.oracle_input
    try:
        worker_request = _oracle_abi.parse_oracle_worker_request_frame(
            raw.request_frame_bytes
        )
        descriptor = _payloads.adapter_descriptor_payload(
            base_case_input.descriptor
        )
        partition = _payloads.partition_payload(
            base_case_input.complete_sample.sample.manifest.partition
        )
        split = _payloads.split_manifest_payload(
            base_case_input.split_manifest
        )
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.REQUEST_BINDING)
    if (
        raw.oracle_registry_bytes
        != request.bindings.oracle_registry_bytes
        or raw.source_archive_inventory_bytes
        != request.bindings.source_tree_manifest_bytes
        or raw.source_archive_bytes
        != request.bindings.source_tree_archive_bytes
        or raw.independent_golden_receipt_bytes
        != base_golden.receipt_bytes
        or worker_request.execution_input_set_sha256
        != execution_input_set_sha256
        or worker_request.case_ordinal != approved_case.case_ordinal
        or worker_request.oracle_id != base_golden.receipt.oracle_id
        or worker_request.oracle_source_byte_count
        != base_golden.receipt.oracle_source_byte_count
        or worker_request.oracle_source_sha256
        != base_golden.receipt.oracle_source_sha256
        or worker_request.source_bytes != base_case_input.source_bytes
        or worker_request.descriptor_payload_bytes
        != descriptor.canonical_json_bytes
        or worker_request.partition_payload_bytes
        != partition.canonical_json_bytes
        or worker_request.split_manifest_payload_bytes
        != split.canonical_json_bytes
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.REQUEST_BINDING)
    return worker_request


def _validate_supplemental_result_binding(
    value: IndependentExpectedLeafBundleVerificationResultV1,
    *,
    golden_extension: ValidatedIndependentGoldenExpectedLeafExtensionV1,
    base_golden: ValidatedIndependentGoldenReceiptV1,
) -> None:
    receipt = value.receipt
    expected = golden_extension.receipt
    if (
        receipt.oracle_id != base_golden.receipt.oracle_id
        or receipt.expected_leaf_bundle_byte_count
        != expected.expected_leaf_bundle_byte_count
        or receipt.expected_leaf_bundle_sha256
        != expected.expected_leaf_bundle_sha256
        or receipt.descriptor_sha256 != expected.descriptor_sha256
        or receipt.source_sha256 != expected.source_sha256
        or receipt.split_manifest_sha256
        != expected.split_manifest_sha256
        or receipt.expected_configuration_sha256
        != expected.expected_configuration_sha256
        or receipt.expected_evidence_sha256
        != expected.expected_evidence_sha256
        or receipt.expected_native_observation_sha256
        != expected.expected_native_observation_sha256
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.SUPPLEMENTAL_VERIFICATION)


def _prepare_leaf_cases(
    request: DecisionPublicationFreezeInputV1,
    leaf_cases: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
    *,
    base_authority: _base_authority.ValidatedPublicationBindingAuthorityV1,
    leaf_authority: ValidatedApprovedExpectedLeafAuthorityV1,
    execution_input_set_sha256: str,
) -> Tuple[_PreparedLeafCase, ...]:
    base_by_id = _validated_base_cases(request, base_authority)
    supplied_by_id = {item.case_authority_id: item for item in leaf_cases}
    approved_by_id = {
        item.case_authority_id: item
        for item in leaf_authority.profile.case_expectations
    }
    if (
        len(supplied_by_id) != len(leaf_cases)
        or len(approved_by_id)
        != len(leaf_authority.profile.case_expectations)
        or set(supplied_by_id) != set(approved_by_id)
        or set(base_by_id) != set(approved_by_id)
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.CASE_INVENTORY)

    prepared = []
    for approved_case in leaf_authority.profile.case_expectations:
        snapshot = supplied_by_id[approved_case.case_authority_id]
        base_case_input, base_case, base_golden = base_by_id[
            approved_case.case_authority_id
        ]
        if (
            snapshot.golden_extension_input.receipt.case_authority_id
            != snapshot.case_authority_id
            or snapshot.golden_extension_input.receipt.case_ordinal
            != approved_case.case_ordinal
        ):
            _fail(ExpectedLeafAuthorityFreezeCode.CASE_INVENTORY)
        raw = snapshot.supplemental_verification_input
        if (
            raw.oracle_input.independent_golden_receipt_bytes
            != base_golden.receipt_bytes
        ):
            _fail(ExpectedLeafAuthorityFreezeCode.BASE_CASE)
        try:
            golden_extension = (
                _leaf_authority
                .validate_independent_golden_expected_leaf_extension(
                    snapshot.golden_extension_input,
                    base_golden=base_golden,
                    approved_case=approved_case,
                    authority=leaf_authority,
                    expected_leaf_bundle_bytes=(
                        raw.expected_leaf_bundle_bytes
                    ),
                )
            )
        except Exception:
            _fail(ExpectedLeafAuthorityFreezeCode.GOLDEN_EXTENSION)
        worker_request = _validate_raw_case_binding(
            snapshot,
            approved_case=approved_case,
            base_case_input=base_case_input,
            base_golden=base_golden,
            request=request,
            execution_input_set_sha256=execution_input_set_sha256,
        )
        try:
            supplemental = (
                _leaf_verifier.verify_independent_expected_leaf_bundle(raw)
            )
        except Exception:
            _fail(
                ExpectedLeafAuthorityFreezeCode.SUPPLEMENTAL_VERIFICATION
            )
        _validate_supplemental_result_binding(
            supplemental,
            golden_extension=golden_extension,
            base_golden=base_golden,
        )
        prepared.append(
            _PreparedLeafCase(
                snapshot=snapshot,
                approved_case=approved_case,
                base_case=base_case,
                base_request_case=base_case_input,
                base_golden=base_golden,
                golden_extension=golden_extension,
                supplemental_verification=supplemental,
                worker_request=worker_request,
            )
        )
    return tuple(prepared)


def _require_leaf_inputs_unchanged(
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    leaf_case_inputs: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
    *,
    authority_snapshot: ApprovedExpectedLeafAuthorityInputV1,
    case_snapshots: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
) -> None:
    try:
        after_authority = _snapshot_leaf_authority_input(
            leaf_authority_input
        )
        after_cases = _snapshot_leaf_cases(leaf_case_inputs)
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.POSTMUTATION)
    if (
        after_authority != authority_snapshot
        or after_cases != case_snapshots
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.POSTMUTATION)


def _receipt(
    base_authority: _base_authority.ValidatedPublicationBindingAuthorityV1,
    leaf_authority: ValidatedApprovedExpectedLeafAuthorityV1,
    prepared_input: PreparedDecisionExecutionInputSetV2,
    cases: Tuple[FrozenExpectedLeafAuthorityCaseV1, ...],
) -> ExpectedLeafAuthorityFreezeReceiptV1:
    profile = leaf_authority.profile
    return ExpectedLeafAuthorityFreezeReceiptV1(
        artifact_type=EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_ARTIFACT_TYPE,
        format_version="1",
        status_id=EXPECTED_LEAF_AUTHORITY_FREEZE_STATUS,
        decision_status=EXPECTED_LEAF_AUTHORITY_FREEZE_DECISION_STATUS,
        case_count=len(cases),
        base_approved_profile_sha256=base_authority.authority.profile_sha256,
        expected_leaf_authority_profile_sha256=(
            leaf_authority.profile_sha256
        ),
        execution_input_set_v2_sha256=(
            prepared_input.execution_input_set_sha256
        ),
        expected_leaf_archive_sha256=(
            leaf_authority.expected_leaf_archive.archive_sha256
        ),
        reason_registry_sha256=(
            _leaf_authority.expected_leaf_reason_registry_sha256(
                profile.reason_registry
            )
        ),
        semantic_profile_sha256=(
            _leaf_authority.expected_leaf_semantic_profile_sha256(
                profile.semantic_profile
            )
        ),
        verifier_closure_sha256=(
            leaf_authority.verifier_closure.closure_sha256
        ),
        validated_case_result_set_sha256=(
            expected_leaf_authority_freeze_validated_case_result_set_sha256(
                cases
            )
        ),
        base_profile_anchor_bytes_matched=True,
        expected_leaf_profile_anchor_bytes_matched=True,
        parent_authority_link_matched=True,
        reason_registry_exact_categories_matched=True,
        semantic_profile_and_verifier_closure_matched=True,
        expected_leaf_archive_membership_recomputed=True,
        golden_extensions_recomputed=True,
        expected_leaf_bundles_deeply_revalidated=True,
        v2_execution_input_set_rebuilt=True,
        worker_request_v2_digest_matched=True,
        base_candidate_recomputed=True,
        decision_made=False,
        execution_attested=False,
        containment_attested=False,
        external_custody_attested=False,
        external_anchor_provenance_attested=False,
        profile_authorship_attested=False,
        execution_input_set_consumption_attested=False,
        oracle_generated_expected_leaf_bundle_attested=False,
        source_policy_semantics_independently_evaluated=False,
        semantic_truth_attested=False,
        format_specific_payload_semantics_attested=False,
        adapted_evidence_leaf_complete=False,
        publication_artifacts_rebuilt=False,
        v2_guard_manifest_built=False,
        generalization_attested=False,
    )


def _freeze_expected_leaf_authority_candidate(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    leaf_case_inputs: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> FrozenExpectedLeafAuthorityDecisionInputV1:
    authority_snapshot, case_snapshots = _validate_initial_types(
        request,
        authority_input,
        leaf_authority_input,
        leaf_case_inputs,
        expected_leaf_archive_inventory_bytes=(
            expected_leaf_archive_inventory_bytes
        ),
        expected_leaf_archive_bytes=expected_leaf_archive_bytes,
    )
    base_authority = _validate_base_authority(request, authority_input)
    leaf_authority = _validate_leaf_authority(
        request,
        authority_snapshot,
        base_authority,
        expected_leaf_archive_inventory_bytes=(
            expected_leaf_archive_inventory_bytes
        ),
        expected_leaf_archive_bytes=expected_leaf_archive_bytes,
    )
    try:
        prepared_input = (
            _execution_input.prepare_decision_execution_input_set_v2(
                base_authority.authority,
                leaf_authority,
            )
        )
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.LEAF_AUTHORITY)
    prepared_cases = _prepare_leaf_cases(
        request,
        case_snapshots,
        base_authority=base_authority,
        leaf_authority=leaf_authority,
        execution_input_set_sha256=(
            prepared_input.execution_input_set_sha256
        ),
    )

    # This is the first point at which an untrusted adapter can be invoked.
    # Every authority, archive, extension, raw-verifier, and request-digest
    # check above has already completed.
    try:
        base_candidate = _base_freeze.freeze_decision_publication_input(
            request,
            authority_input,
        )
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.BASE_CANDIDATE)
    _require_leaf_inputs_unchanged(
        leaf_authority_input,
        leaf_case_inputs,
        authority_snapshot=authority_snapshot,
        case_snapshots=case_snapshots,
    )
    if (
        base_candidate.binding_authority.authority
        != base_authority.authority
        or base_candidate.public_ids != request.public_ids
        or len(base_candidate.cases) != len(prepared_cases)
        or tuple(
            item.case_expectation for item in base_candidate.cases
        )
        != tuple(item.base_case for item in prepared_cases)
    ):
        _fail(ExpectedLeafAuthorityFreezeCode.POSTMUTATION)

    frozen_cases = tuple(
        FrozenExpectedLeafAuthorityCaseV1(
            case_authority_id=item.snapshot.case_authority_id,
            approved_case=item.approved_case,
            base_case=item.base_case,
            golden_extension=item.golden_extension,
            archive_membership=(
                item.golden_extension.archived_bundle.membership
            ),
            supplemental_verification=item.supplemental_verification,
            supplemental_verification_input=(
                item.snapshot.supplemental_verification_input
            ),
            worker_request=item.worker_request,
            expected_leaf_bundle_bytes=(
                item.snapshot.supplemental_verification_input
                .expected_leaf_bundle_bytes
            ),
        )
        for item in prepared_cases
    )
    receipt = _receipt(
        base_authority,
        leaf_authority,
        prepared_input,
        frozen_cases,
    )
    receipt_bytes = expected_leaf_authority_freeze_receipt_bytes(receipt)
    receipt_sha256 = expected_leaf_authority_freeze_receipt_sha256(receipt)
    return FrozenExpectedLeafAuthorityDecisionInputV1(
        candidate_status=PUBLICATION_DEVELOPMENT_STATUS,
        decision_status=EXPECTED_LEAF_AUTHORITY_FREEZE_DECISION_STATUS,
        base_candidate=base_candidate,
        prepared_execution_input_set=prepared_input,
        expected_leaf_authority=leaf_authority,
        cases=frozen_cases,
        receipt=receipt,
        receipt_bytes=receipt_bytes,
        receipt_sha256=receipt_sha256,
    )


def freeze_expected_leaf_authority_candidate(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    leaf_case_inputs: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> FrozenExpectedLeafAuthorityDecisionInputV1:
    """Freeze an authority-bound expected-leaf candidate without publication."""

    try:
        return _freeze_expected_leaf_authority_candidate(
            request,
            authority_input,
            leaf_authority_input,
            leaf_case_inputs,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except ExpectedLeafAuthorityFreezeError:
        raise
    except Exception:
        _fail(ExpectedLeafAuthorityFreezeCode.INTERNAL)


__all__ = [
    "EXPECTED_LEAF_AUTHORITY_FREEZE_DECISION_STATUS",
    "EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_ARTIFACT_TYPE",
    "EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_DIGEST_DOMAIN",
    "EXPECTED_LEAF_AUTHORITY_FREEZE_STATUS",
    "EXPECTED_LEAF_AUTHORITY_FREEZE_VALIDATED_CASE_RESULT_SET_DIGEST_DOMAIN",
    "ExpectedLeafAuthorityCaseInputV1",
    "ExpectedLeafAuthorityFreezeCode",
    "ExpectedLeafAuthorityFreezeError",
    "ExpectedLeafAuthorityFreezeReceiptV1",
    "FrozenExpectedLeafAuthorityCaseV1",
    "FrozenExpectedLeafAuthorityDecisionInputV1",
    "MAXIMUM_EXPECTED_LEAF_AUTHORITY_FREEZE_CASE_RESULT_SET_BYTES",
    "MAXIMUM_EXPECTED_LEAF_AUTHORITY_FREEZE_RECEIPT_BYTES",
    "MAXIMUM_EXPECTED_LEAF_FREEZE_CASES",
    "MAXIMUM_EXPECTED_LEAF_FREEZE_VALIDATION_WORK_BYTES",
    "expected_leaf_authority_freeze_receipt_bytes",
    "expected_leaf_authority_freeze_receipt_sha256",
    "expected_leaf_authority_freeze_validated_case_result_set_bytes",
    "expected_leaf_authority_freeze_validated_case_result_set_sha256",
    "freeze_expected_leaf_authority_candidate",
]
