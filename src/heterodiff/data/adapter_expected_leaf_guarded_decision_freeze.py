"""Guard-first wrapper for the expected-leaf authority candidate freezer.

This additive boundary prepares and validates the exact V2 pre-run guard
manifest before it permits the existing local adapter-callback path to run.
After that path returns, it independently rechecks the guard/candidate
authority join, exact V2 input-set transport, inner receipt, and canonical
validated-case result set.

The resulting outer receipt records only deterministic local consistency.
Preparing a manifest is not evidence that a backend consumed it.  The wrapped
candidate still uses uncontained in-process adapter callbacks, so execution,
containment, source loading, expected-material nonexposure, fresh adapted-side
reconstruction, publication, decision, and generalization claims remain
false.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import NamedTuple, Tuple

from . import adapter_expected_leaf_authority as _leaf_authority
from . import adapter_expected_leaf_decision_freeze as _leaf_freeze
from . import adapter_expected_leaf_execution_input as _execution_input
from . import adapter_expected_leaf_guard_manifest as _guard_manifest
from . import adapter_publication_authority as _base_authority
from .adapter_expected_leaf_authority_types import (
    ApprovedExpectedLeafAuthorityInputV1,
)
from .adapter_expected_leaf_authority import (
    ValidatedApprovedExpectedLeafAuthorityV1,
)
from .adapter_expected_leaf_decision_freeze import (
    ExpectedLeafAuthorityCaseInputV1,
    FrozenExpectedLeafAuthorityDecisionInputV1,
)
from .adapter_expected_leaf_guard_manifest import (
    PreparedExpectedLeafDecisionGuardManifestV2,
)
from .adapter_expected_leaf_guard_types import (
    ExpectedLeafDecisionExecutionGuardRunManifestV2,
)
from .adapter_expected_leaf_execution_input import (
    PreparedDecisionExecutionInputSetV2,
)
from .adapter_publication_authority_types import (
    ApprovedPublicationAuthorityInputV1,
    DecisionExecutionInvocationV1,
    DecisionPublicationFreezeInputV1,
)
from .adapter_publication_authority import (
    ValidatedPublicationBindingAuthorityV1,
)
from .adapter_publication_types import PUBLICATION_DEVELOPMENT_STATUS


EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-leaf-guarded-decision-freeze-receipt.v1"
)
EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_DIGEST_DOMAIN = (
    EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_ARTIFACT_TYPE
)
EXPECTED_LEAF_GUARDED_DECISION_FREEZE_STATUS = (
    "EXPECTED_LEAF_V2_GUARD_MANIFEST_AND_LOCAL_CANDIDATE_MATCHED_"
    "UNATTESTED_DEVELOPMENT_EXECUTION"
)
EXPECTED_LEAF_GUARDED_DECISION_FREEZE_DECISION_STATUS = (
    "NOT_MADE_BY_EXPECTED_LEAF_GUARDED_FREEZER"
)
MAXIMUM_EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_BYTES = 64 * 1024
MAXIMUM_EXPECTED_LEAF_GUARDED_DECISION_FREEZE_CASES = 4096

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ExpectedLeafGuardedDecisionFreezeCode(str, Enum):
    """Closed outer-freezer failures with fixed nonreflecting messages."""

    INPUT_TYPE = "EXPECTED_LEAF_GUARDED_FREEZE_INPUT_TYPE"
    GUARD_PREPARATION = "EXPECTED_LEAF_GUARDED_FREEZE_GUARD_PREPARATION"
    CANDIDATE_FREEZE = "EXPECTED_LEAF_GUARDED_FREEZE_CANDIDATE"
    POSTMUTATION = "EXPECTED_LEAF_GUARDED_FREEZE_POSTMUTATION"
    AUTHORITY_MISMATCH = "EXPECTED_LEAF_GUARDED_FREEZE_AUTHORITY_MISMATCH"
    V2_INPUT_SET_MISMATCH = (
        "EXPECTED_LEAF_GUARDED_FREEZE_V2_INPUT_SET_MISMATCH"
    )
    RESULT_SET_MISMATCH = (
        "EXPECTED_LEAF_GUARDED_FREEZE_RESULT_SET_MISMATCH"
    )
    RECEIPT = "EXPECTED_LEAF_GUARDED_FREEZE_RECEIPT"
    INTERNAL = "EXPECTED_LEAF_GUARDED_FREEZE_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExpectedLeafGuardedDecisionFreezeCode.INPUT_TYPE: (
            "guarded expected-leaf freeze input has an invalid exact type"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION: (
            "expected-leaf V2 guard preparation did not complete"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.CANDIDATE_FREEZE: (
            "expected-leaf local candidate freeze did not complete"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.POSTMUTATION: (
            "guarded expected-leaf freeze input changed during validation"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.AUTHORITY_MISMATCH: (
            "guard and local candidate authorities differ"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.V2_INPUT_SET_MISMATCH: (
            "guard and local candidate V2 input sets differ"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.RESULT_SET_MISMATCH: (
            "guarded expected-leaf validated case result set differs"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.RECEIPT: (
            "guarded expected-leaf freeze receipt is invalid"
        ),
        ExpectedLeafGuardedDecisionFreezeCode.INTERNAL: (
            "guarded expected-leaf freeze failed internally"
        ),
    }
)


class ExpectedLeafGuardedDecisionFreezeError(ValueError):
    """One coded outer-freezer failure with no attacker text."""

    def __init__(self, code: ExpectedLeafGuardedDecisionFreezeCode) -> None:
        if type(code) is not ExpectedLeafGuardedDecisionFreezeCode:
            raise TypeError("guarded expected-leaf freeze code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class ExpectedLeafGuardedDecisionFreezeReceiptV1(NamedTuple):
    """Canonical postcallback consistency receipt; permanently nondecision."""

    artifact_type: str
    format_version: str
    status_id: str
    decision_status: str
    case_count: int
    base_approved_profile_sha256: str
    expected_leaf_authority_profile_sha256: str
    execution_input_set_v2_sha256: str
    guard_manifest_v2_sha256: str
    inner_authority_freeze_receipt_sha256: str
    validated_case_result_set_sha256: str
    base_profile_anchor_bytes_matched: bool
    expected_leaf_profile_anchor_bytes_matched: bool
    guard_and_candidate_authorities_matched: bool
    v2_execution_input_set_rebuilt: bool
    guard_and_candidate_v2_input_set_matched: bool
    validated_case_result_set_recomputed: bool
    inner_candidate_receipt_revalidated: bool
    execution_invocation_snapshot_unchanged: bool
    v2_guard_manifest_built: bool
    v2_guard_manifest_built_before_local_adapter_callbacks: bool
    decision_made: bool
    execution_attested: bool
    containment_enforced: bool
    containment_attested: bool
    external_custody_attested: bool
    external_anchor_provenance_attested: bool
    profile_authorship_attested: bool
    guard_manifest_executed: bool
    guard_manifest_consumption_attested: bool
    execution_input_set_consumption_attested: bool
    output_blind_adapter_child_enforced: bool
    expected_material_nonexposure_attested: bool
    adapter_source_loaded: bool
    adapter_source_execution_identity_attested: bool
    oracle_generated_expected_leaf_bundle_attested: bool
    source_policy_semantics_independently_evaluated: bool
    semantic_truth_attested: bool
    format_specific_payload_semantics_attested: bool
    fresh_adapted_evidence_reconstructed: bool
    adapted_evidence_leaf_complete: bool
    publication_artifacts_rebuilt: bool
    generalization_attested: bool


class FrozenGuardedExpectedLeafAuthorityDecisionInputV1(NamedTuple):
    """Guard preparation, local candidate, and immutable outer commitments."""

    candidate_status: str
    decision_status: str
    prepared_guard_manifest: PreparedExpectedLeafDecisionGuardManifestV2
    authority_candidate: FrozenExpectedLeafAuthorityDecisionInputV1
    validated_case_result_set_bytes: bytes
    receipt: ExpectedLeafGuardedDecisionFreezeReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str


_RECEIPT_DIGEST_FIELDS = (
    "base_approved_profile_sha256",
    "expected_leaf_authority_profile_sha256",
    "execution_input_set_v2_sha256",
    "guard_manifest_v2_sha256",
    "inner_authority_freeze_receipt_sha256",
    "validated_case_result_set_sha256",
)
_RECEIPT_TRUE_FIELDS = (
    "base_profile_anchor_bytes_matched",
    "expected_leaf_profile_anchor_bytes_matched",
    "guard_and_candidate_authorities_matched",
    "v2_execution_input_set_rebuilt",
    "guard_and_candidate_v2_input_set_matched",
    "validated_case_result_set_recomputed",
    "inner_candidate_receipt_revalidated",
    "execution_invocation_snapshot_unchanged",
    "v2_guard_manifest_built",
    "v2_guard_manifest_built_before_local_adapter_callbacks",
)
_RECEIPT_FALSE_FIELDS = (
    "decision_made",
    "execution_attested",
    "containment_enforced",
    "containment_attested",
    "external_custody_attested",
    "external_anchor_provenance_attested",
    "profile_authorship_attested",
    "guard_manifest_executed",
    "guard_manifest_consumption_attested",
    "execution_input_set_consumption_attested",
    "output_blind_adapter_child_enforced",
    "expected_material_nonexposure_attested",
    "adapter_source_loaded",
    "adapter_source_execution_identity_attested",
    "oracle_generated_expected_leaf_bundle_attested",
    "source_policy_semantics_independently_evaluated",
    "semantic_truth_attested",
    "format_specific_payload_semantics_attested",
    "fresh_adapted_evidence_reconstructed",
    "adapted_evidence_leaf_complete",
    "publication_artifacts_rebuilt",
    "generalization_attested",
)


def _fail(code: ExpectedLeafGuardedDecisionFreezeCode) -> None:
    raise ExpectedLeafGuardedDecisionFreezeError(code) from None


def _validate_receipt(
    value: object,
) -> ExpectedLeafGuardedDecisionFreezeReceiptV1:
    if type(value) is not ExpectedLeafGuardedDecisionFreezeReceiptV1:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    fixed = (
        (
            value.artifact_type,
            EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_ARTIFACT_TYPE,
        ),
        (value.format_version, "1"),
        (value.status_id, EXPECTED_LEAF_GUARDED_DECISION_FREEZE_STATUS),
        (
            value.decision_status,
            EXPECTED_LEAF_GUARDED_DECISION_FREEZE_DECISION_STATUS,
        ),
    )
    if any(
        type(observed) is not str or observed != expected
        for observed, expected in fixed
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    if (
        type(value.case_count) is not int
        or value.case_count < 1
        or value.case_count
        > MAXIMUM_EXPECTED_LEAF_GUARDED_DECISION_FREEZE_CASES
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    if any(
        type(getattr(value, name)) is not str
        or _SHA256_RE.fullmatch(getattr(value, name)) is None
        for name in _RECEIPT_DIGEST_FIELDS
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    if any(
        getattr(value, name) is not True for name in _RECEIPT_TRUE_FIELDS
    ) or any(
        getattr(value, name) is not False for name in _RECEIPT_FALSE_FIELDS
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    return value


def expected_leaf_guarded_decision_freeze_receipt_bytes(
    value: ExpectedLeafGuardedDecisionFreezeReceiptV1,
) -> bytes:
    """Serialize the exact outer receipt as bounded canonical ASCII JSON."""

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
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    if (
        not encoded
        or len(encoded)
        > MAXIMUM_EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_BYTES
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    return encoded


def expected_leaf_guarded_decision_freeze_receipt_sha256(
    value: ExpectedLeafGuardedDecisionFreezeReceiptV1,
) -> str:
    """Domain-hash the exact canonical outer receipt."""

    encoded = expected_leaf_guarded_decision_freeze_receipt_bytes(value)
    try:
        return _leaf_authority.domain_separated_sha256(
            EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_DIGEST_DOMAIN,
            encoded,
        )
    except (TypeError, ValueError):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)


def _frozen_tree_key(value: object) -> object:
    """Snapshot one types-only guard input into immutable scalar structure."""

    if value is None or type(value) in (bool, int, str, bytes):
        return value
    if type(value) is tuple:
        return tuple(_frozen_tree_key(item) for item in value)
    if is_dataclass(value) and type(value).__module__.startswith(
        "heterodiff.data."
    ):
        return (
            type(value),
            tuple(
                (item.name, _frozen_tree_key(getattr(value, item.name)))
                for item in fields(value)
            ),
        )
    _fail(ExpectedLeafGuardedDecisionFreezeCode.INPUT_TYPE)


def _guard_input_key(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    execution_invocation: DecisionExecutionInvocationV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> object:
    return _frozen_tree_key(
        (
            request.bindings,
            request.public_ids,
            authority_input,
            leaf_authority_input,
            execution_invocation,
            expected_leaf_archive_inventory_bytes,
            expected_leaf_archive_bytes,
        )
    )


def _validate_initial_types(
    request: object,
    authority_input: object,
    leaf_authority_input: object,
    leaf_case_inputs: object,
    execution_invocation: object,
    *,
    expected_leaf_archive_inventory_bytes: object,
    expected_leaf_archive_bytes: object,
) -> object:
    if (
        type(request) is not DecisionPublicationFreezeInputV1
        or type(authority_input) is not ApprovedPublicationAuthorityInputV1
        or type(leaf_authority_input)
        is not ApprovedExpectedLeafAuthorityInputV1
        or type(execution_invocation) is not DecisionExecutionInvocationV1
        or type(leaf_case_inputs) is not tuple
        or not leaf_case_inputs
        or len(leaf_case_inputs)
        > MAXIMUM_EXPECTED_LEAF_GUARDED_DECISION_FREEZE_CASES
        or any(
            type(item) is not ExpectedLeafAuthorityCaseInputV1
            for item in leaf_case_inputs
        )
        or type(expected_leaf_archive_inventory_bytes) is not bytes
        or type(expected_leaf_archive_bytes) is not bytes
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.INPUT_TYPE)
    try:
        DecisionPublicationFreezeInputV1.__post_init__(request)
        ApprovedPublicationAuthorityInputV1.__post_init__(authority_input)
        ApprovedExpectedLeafAuthorityInputV1.__post_init__(
            leaf_authority_input
        )
        for item in leaf_case_inputs:
            ExpectedLeafAuthorityCaseInputV1.__post_init__(item)
        DecisionExecutionInvocationV1.__post_init__(execution_invocation)
        return _guard_input_key(
            request,
            authority_input,
            leaf_authority_input,
            execution_invocation,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except ExpectedLeafGuardedDecisionFreezeError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.INPUT_TYPE)


def _require_guard_input_unchanged(
    expected_key: object,
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    execution_invocation: DecisionExecutionInvocationV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> None:
    try:
        observed = _guard_input_key(
            request,
            authority_input,
            leaf_authority_input,
            execution_invocation,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.POSTMUTATION)
    if observed != expected_key:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.POSTMUTATION)


def _validate_prepared_guard(
    value: object,
    *,
    expected_binding_authority: ValidatedPublicationBindingAuthorityV1,
    expected_leaf_authority: ValidatedApprovedExpectedLeafAuthorityV1,
) -> PreparedExpectedLeafDecisionGuardManifestV2:
    if (
        type(value) is not PreparedExpectedLeafDecisionGuardManifestV2
        or type(expected_binding_authority)
        is not ValidatedPublicationBindingAuthorityV1
        or type(expected_leaf_authority)
        is not ValidatedApprovedExpectedLeafAuthorityV1
        or type(value.binding_authority)
        is not ValidatedPublicationBindingAuthorityV1
        or type(value.expected_leaf_authority)
        is not ValidatedApprovedExpectedLeafAuthorityV1
        or type(value.manifest)
        is not ExpectedLeafDecisionExecutionGuardRunManifestV2
        or type(value.prepared_execution_input_set)
        is not PreparedDecisionExecutionInputSetV2
        or type(value.execution_invocation)
        is not DecisionExecutionInvocationV1
        or type(value.manifest_bytes) is not bytes
        or type(value.manifest_sha256) is not str
        or value.prepared_execution_input_set.base_authority
        != value.binding_authority.authority
        or value.prepared_execution_input_set.expected_leaf_authority
        != value.expected_leaf_authority
        or value.binding_authority != expected_binding_authority
        or value.expected_leaf_authority != expected_leaf_authority
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)
    try:
        rebuilt_input = (
            _execution_input.prepare_decision_execution_input_set_v2(
                expected_binding_authority.authority,
                expected_leaf_authority,
            )
        )
        manifest_bytes = (
            _guard_manifest.expected_leaf_decision_guard_manifest_v2_bytes(
                value.manifest
            )
        )
        manifest_sha256 = (
            _guard_manifest.expected_leaf_decision_guard_manifest_v2_sha256(
                value.manifest
            )
        )
        input_bytes = value.prepared_execution_input_set.execution_input_set_bytes
        input_sha256 = _execution_input.decision_execution_input_set_v2_sha256(
            input_bytes
        )
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)
    if (
        type(rebuilt_input) is not PreparedDecisionExecutionInputSetV2
        or rebuilt_input != value.prepared_execution_input_set
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)
    invocation = value.execution_invocation
    invocation_digests = (
        (value.manifest.argv_sha256, invocation.argv_bytes),
        (
            value.manifest.authorized_write_root_sha256,
            invocation.authorized_write_root_bytes,
        ),
        (
            value.manifest.containment_policy_sha256,
            invocation.containment_policy_bytes,
        ),
        (
            value.manifest.environment_sha256,
            invocation.environment_bytes,
        ),
        (
            value.manifest.working_directory_sha256,
            invocation.working_directory_bytes,
        ),
    )
    policy = expected_binding_authority.authority.profile.execution_policy
    binding_set = expected_binding_authority.binding_set
    inherited_bindings = (
        (value.manifest.argv_sha256, policy.argv_sha256),
        (
            value.manifest.authorized_write_root_sha256,
            policy.authorized_write_root_sha256,
        ),
        (
            value.manifest.containment_policy_sha256,
            policy.containment_policy_sha256,
        ),
        (
            value.manifest.environment_sha256,
            policy.environment_sha256,
        ),
        (
            value.manifest.working_directory_sha256,
            policy.working_directory_sha256,
        ),
        (
            value.manifest.address_space_limit_bytes,
            policy.address_space_limit_bytes,
        ),
        (
            value.manifest.address_space_limit_method_id,
            policy.address_space_limit_method_id,
        ),
        (
            value.manifest.allowed_execution_status_ids,
            policy.allowed_execution_status_ids,
        ),
        (value.manifest.clock_method_id, policy.clock_method_id),
        (value.manifest.cwd_launch_method_id, policy.cwd_launch_method_id),
        (
            value.manifest.dependency_lock_sha256,
            binding_set.dependency_lock_sha256,
        ),
        (
            value.manifest.environment_manifest_sha256,
            binding_set.environment_manifest_sha256,
        ),
        (value.manifest.execution_backend_id, policy.execution_backend_id),
        (
            value.manifest.execution_guard_source_sha256,
            binding_set.execution_guard_source_sha256,
        ),
        (
            value.manifest.filesystem_confinement_id,
            policy.filesystem_confinement_id,
        ),
        (
            value.manifest.guard_implementation_status_id,
            policy.guard_implementation_status_id,
        ),
        (
            value.manifest.interpreter_executable_sha256,
            binding_set.interpreter_executable_sha256,
        ),
        (
            value.manifest.output_capture_method_id,
            policy.output_capture_method_id,
        ),
        (value.manifest.peak_rss_method_id, policy.peak_rss_method_id),
        (
            value.manifest.process_containment_id,
            policy.process_containment_id,
        ),
        (
            value.manifest.publication_binding_set_sha256,
            expected_binding_authority.binding_set_sha256,
        ),
        (
            value.manifest.source_binding_format_id,
            policy.source_binding_format_id,
        ),
        (
            value.manifest.source_tree_archive_sha256,
            binding_set.source_tree_archive_sha256,
        ),
        (
            value.manifest.source_tree_manifest_sha256,
            binding_set.source_tree_manifest_sha256,
        ),
        (
            value.manifest.test_inventory_sha256,
            binding_set.test_inventory_sha256,
        ),
    )
    if (
        value.manifest_bytes != manifest_bytes
        or value.manifest_sha256 != manifest_sha256
        or value.manifest.execution_input_set_byte_count
        != len(input_bytes)
        or value.manifest.execution_input_set_file_sha256
        != hashlib.sha256(input_bytes).hexdigest()
        or value.manifest.execution_input_set_sha256
        != value.prepared_execution_input_set.execution_input_set_sha256
        or value.manifest.execution_input_set_sha256 != input_sha256
        or any(
            observed != hashlib.sha256(raw).hexdigest()
            for observed, raw in invocation_digests
        )
        or any(observed != expected for observed, expected in inherited_bindings)
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)
    return value


def _validate_raw_guard_authorities(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> Tuple[
    ValidatedPublicationBindingAuthorityV1,
    ValidatedApprovedExpectedLeafAuthorityV1,
]:
    try:
        binding_authority = (
            _base_authority.validate_publication_binding_authority(
                request.bindings,
                request.public_ids,
                authority_input,
            )
        )
        _base_authority.validate_approved_profile_registry(
            binding_authority.authority.profile,
            request.public_ids,
        )
        leaf_authority = (
            _leaf_authority.validate_approved_expected_leaf_authority(
                leaf_authority_input,
                parent_authority=binding_authority.authority,
                public_identifier_registry=request.public_ids,
                source_archive_inventory_bytes=(
                    request.bindings.source_tree_manifest_bytes
                ),
                source_archive_bytes=(
                    request.bindings.source_tree_archive_bytes
                ),
                expected_leaf_archive_inventory_bytes=(
                    expected_leaf_archive_inventory_bytes
                ),
                expected_leaf_archive_bytes=expected_leaf_archive_bytes,
            )
        )
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)
    if (
        type(binding_authority)
        is not ValidatedPublicationBindingAuthorityV1
        or type(leaf_authority)
        is not ValidatedApprovedExpectedLeafAuthorityV1
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)
    return binding_authority, leaf_authority


def _validated_case_result_set(
    candidate: FrozenExpectedLeafAuthorityDecisionInputV1,
) -> Tuple[bytes, str]:
    try:
        encoded = (
            _leaf_freeze
            .expected_leaf_authority_freeze_validated_case_result_set_bytes(
                candidate.cases
            )
        )
        digest = (
            _leaf_freeze
            .expected_leaf_authority_freeze_validated_case_result_set_sha256(
                candidate.cases
            )
        )
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RESULT_SET_MISMATCH)
    if candidate.receipt.validated_case_result_set_sha256 != digest:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RESULT_SET_MISMATCH)
    return encoded, digest


def _validate_inner_candidate(
    candidate: object,
) -> FrozenExpectedLeafAuthorityDecisionInputV1:
    if type(candidate) is not FrozenExpectedLeafAuthorityDecisionInputV1:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.CANDIDATE_FREEZE)
    try:
        receipt_bytes = _leaf_freeze.expected_leaf_authority_freeze_receipt_bytes(
            candidate.receipt
        )
        receipt_sha256 = (
            _leaf_freeze.expected_leaf_authority_freeze_receipt_sha256(
                candidate.receipt
            )
        )
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    if (
        candidate.candidate_status != PUBLICATION_DEVELOPMENT_STATUS
        or candidate.decision_status
        != _leaf_freeze.EXPECTED_LEAF_AUTHORITY_FREEZE_DECISION_STATUS
        or candidate.receipt_bytes != receipt_bytes
        or candidate.receipt_sha256 != receipt_sha256
        or candidate.receipt.v2_guard_manifest_built is not False
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    return candidate


def _crosscheck_guard_and_candidate(
    prepared: PreparedExpectedLeafDecisionGuardManifestV2,
    candidate: FrozenExpectedLeafAuthorityDecisionInputV1,
) -> Tuple[bytes, str]:
    base_cases = prepared.binding_authority.authority.profile.case_expectations
    leaf_cases = prepared.expected_leaf_authority.profile.case_expectations
    if (
        candidate.base_candidate.binding_authority
        != prepared.binding_authority
        or candidate.expected_leaf_authority
        != prepared.expected_leaf_authority
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.AUTHORITY_MISMATCH)
    if (
        candidate.prepared_execution_input_set
        != prepared.prepared_execution_input_set
        or candidate.prepared_execution_input_set.base_authority
        != prepared.binding_authority.authority
        or candidate.prepared_execution_input_set.expected_leaf_authority
        != prepared.expected_leaf_authority
        or candidate.receipt.execution_input_set_v2_sha256
        != prepared.prepared_execution_input_set.execution_input_set_sha256
        or prepared.manifest.execution_input_set_sha256
        != prepared.prepared_execution_input_set.execution_input_set_sha256
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.V2_INPUT_SET_MISMATCH)
    if (
        candidate.receipt.base_approved_profile_sha256
        != prepared.binding_authority.authority.profile_sha256
        or candidate.receipt.expected_leaf_authority_profile_sha256
        != prepared.expected_leaf_authority.profile_sha256
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.AUTHORITY_MISMATCH)
    if (
        len(candidate.cases) != len(base_cases)
        or len(candidate.cases) != len(leaf_cases)
        or tuple(item.base_case for item in candidate.cases) != base_cases
        or tuple(item.approved_case for item in candidate.cases) != leaf_cases
        or tuple(item.case_authority_id for item in candidate.cases)
        != tuple(item.case_authority_id for item in leaf_cases)
        or tuple(
            item.case_expectation for item in candidate.base_candidate.cases
        )
        != base_cases
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RESULT_SET_MISMATCH)
    result_set_bytes, result_set_sha256 = _validated_case_result_set(candidate)
    try:
        expected_v2_sha256 = (
            prepared.prepared_execution_input_set.execution_input_set_sha256
        )
        if any(
            item.worker_request.execution_input_set_sha256
            != expected_v2_sha256
            for item in candidate.cases
        ):
            _fail(
                ExpectedLeafGuardedDecisionFreezeCode.V2_INPUT_SET_MISMATCH
            )
        profile = prepared.expected_leaf_authority.profile
        receipt_bindings = (
            (candidate.receipt.case_count, len(candidate.cases)),
            (
                candidate.receipt.base_approved_profile_sha256,
                prepared.binding_authority.authority.profile_sha256,
            ),
            (
                candidate.receipt.expected_leaf_authority_profile_sha256,
                prepared.expected_leaf_authority.profile_sha256,
            ),
            (
                candidate.receipt.execution_input_set_v2_sha256,
                expected_v2_sha256,
            ),
            (
                candidate.receipt.expected_leaf_archive_sha256,
                (
                    prepared.expected_leaf_authority.expected_leaf_archive
                    .archive_sha256
                ),
            ),
            (
                candidate.receipt.reason_registry_sha256,
                _leaf_authority.expected_leaf_reason_registry_sha256(
                    profile.reason_registry
                ),
            ),
            (
                candidate.receipt.semantic_profile_sha256,
                _leaf_authority.expected_leaf_semantic_profile_sha256(
                    profile.semantic_profile
                ),
            ),
            (
                candidate.receipt.verifier_closure_sha256,
                prepared.expected_leaf_authority.verifier_closure.closure_sha256,
            ),
            (
                candidate.receipt.validated_case_result_set_sha256,
                result_set_sha256,
            ),
        )
    except ExpectedLeafGuardedDecisionFreezeError:
        raise
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    if any(
        observed != expected for observed, expected in receipt_bindings
    ):
        _fail(ExpectedLeafGuardedDecisionFreezeCode.RECEIPT)
    return result_set_bytes, result_set_sha256


def _outer_receipt(
    prepared: PreparedExpectedLeafDecisionGuardManifestV2,
    candidate: FrozenExpectedLeafAuthorityDecisionInputV1,
    *,
    validated_case_result_set_sha256: str,
) -> ExpectedLeafGuardedDecisionFreezeReceiptV1:
    return ExpectedLeafGuardedDecisionFreezeReceiptV1(
        artifact_type=(
            EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_ARTIFACT_TYPE
        ),
        format_version="1",
        status_id=EXPECTED_LEAF_GUARDED_DECISION_FREEZE_STATUS,
        decision_status=(
            EXPECTED_LEAF_GUARDED_DECISION_FREEZE_DECISION_STATUS
        ),
        case_count=len(candidate.cases),
        base_approved_profile_sha256=(
            prepared.binding_authority.authority.profile_sha256
        ),
        expected_leaf_authority_profile_sha256=(
            prepared.expected_leaf_authority.profile_sha256
        ),
        execution_input_set_v2_sha256=(
            prepared.prepared_execution_input_set.execution_input_set_sha256
        ),
        guard_manifest_v2_sha256=prepared.manifest_sha256,
        inner_authority_freeze_receipt_sha256=candidate.receipt_sha256,
        validated_case_result_set_sha256=(
            validated_case_result_set_sha256
        ),
        base_profile_anchor_bytes_matched=True,
        expected_leaf_profile_anchor_bytes_matched=True,
        guard_and_candidate_authorities_matched=True,
        v2_execution_input_set_rebuilt=True,
        guard_and_candidate_v2_input_set_matched=True,
        validated_case_result_set_recomputed=True,
        inner_candidate_receipt_revalidated=True,
        execution_invocation_snapshot_unchanged=True,
        v2_guard_manifest_built=True,
        v2_guard_manifest_built_before_local_adapter_callbacks=True,
        decision_made=False,
        execution_attested=False,
        containment_enforced=False,
        containment_attested=False,
        external_custody_attested=False,
        external_anchor_provenance_attested=False,
        profile_authorship_attested=False,
        guard_manifest_executed=False,
        guard_manifest_consumption_attested=False,
        execution_input_set_consumption_attested=False,
        output_blind_adapter_child_enforced=False,
        expected_material_nonexposure_attested=False,
        adapter_source_loaded=False,
        adapter_source_execution_identity_attested=False,
        oracle_generated_expected_leaf_bundle_attested=False,
        source_policy_semantics_independently_evaluated=False,
        semantic_truth_attested=False,
        format_specific_payload_semantics_attested=False,
        fresh_adapted_evidence_reconstructed=False,
        adapted_evidence_leaf_complete=False,
        publication_artifacts_rebuilt=False,
        generalization_attested=False,
    )


def _freeze_guarded_expected_leaf_authority_candidate(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    leaf_case_inputs: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
    execution_invocation: DecisionExecutionInvocationV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> FrozenGuardedExpectedLeafAuthorityDecisionInputV1:
    guard_input_key = _validate_initial_types(
        request,
        authority_input,
        leaf_authority_input,
        leaf_case_inputs,
        execution_invocation,
        expected_leaf_archive_inventory_bytes=(
            expected_leaf_archive_inventory_bytes
        ),
        expected_leaf_archive_bytes=expected_leaf_archive_bytes,
    )

    # This complete preparation is deliberately before the only wrapped
    # surface that can enter an untrusted local adapter callback.
    try:
        prepared = _guard_manifest.prepare_expected_leaf_decision_guard_manifest_v2(
            request.bindings,
            request.public_ids,
            authority_input,
            leaf_authority_input,
            execution_invocation,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)
    expected_binding_authority, expected_leaf_authority = (
        _validate_raw_guard_authorities(
            request,
            authority_input,
            leaf_authority_input,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    )
    prepared = _validate_prepared_guard(
        prepared,
        expected_binding_authority=expected_binding_authority,
        expected_leaf_authority=expected_leaf_authority,
    )
    _require_guard_input_unchanged(
        guard_input_key,
        request,
        authority_input,
        leaf_authority_input,
        execution_invocation,
        expected_leaf_archive_inventory_bytes=(
            expected_leaf_archive_inventory_bytes
        ),
        expected_leaf_archive_bytes=expected_leaf_archive_bytes,
    )
    if prepared.execution_invocation != execution_invocation:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.GUARD_PREPARATION)

    try:
        candidate = _leaf_freeze.freeze_expected_leaf_authority_candidate(
            request,
            authority_input,
            leaf_authority_input,
            leaf_case_inputs,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.CANDIDATE_FREEZE)
    try:
        prepared = _validate_prepared_guard(
            prepared,
            expected_binding_authority=expected_binding_authority,
            expected_leaf_authority=expected_leaf_authority,
        )
    except ExpectedLeafGuardedDecisionFreezeError:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.POSTMUTATION)
    _require_guard_input_unchanged(
        guard_input_key,
        request,
        authority_input,
        leaf_authority_input,
        execution_invocation,
        expected_leaf_archive_inventory_bytes=(
            expected_leaf_archive_inventory_bytes
        ),
        expected_leaf_archive_bytes=expected_leaf_archive_bytes,
    )
    if prepared.execution_invocation != execution_invocation:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.POSTMUTATION)
    candidate = _validate_inner_candidate(candidate)
    result_set_bytes, result_set_sha256 = _crosscheck_guard_and_candidate(
        prepared,
        candidate,
    )
    receipt = _outer_receipt(
        prepared,
        candidate,
        validated_case_result_set_sha256=result_set_sha256,
    )
    receipt_bytes = expected_leaf_guarded_decision_freeze_receipt_bytes(
        receipt
    )
    receipt_sha256 = expected_leaf_guarded_decision_freeze_receipt_sha256(
        receipt
    )
    return FrozenGuardedExpectedLeafAuthorityDecisionInputV1(
        candidate_status=PUBLICATION_DEVELOPMENT_STATUS,
        decision_status=(
            EXPECTED_LEAF_GUARDED_DECISION_FREEZE_DECISION_STATUS
        ),
        prepared_guard_manifest=prepared,
        authority_candidate=candidate,
        validated_case_result_set_bytes=result_set_bytes,
        receipt=receipt,
        receipt_bytes=receipt_bytes,
        receipt_sha256=receipt_sha256,
    )


def freeze_guarded_expected_leaf_authority_candidate(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    leaf_case_inputs: Tuple[ExpectedLeafAuthorityCaseInputV1, ...],
    execution_invocation: DecisionExecutionInvocationV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> FrozenGuardedExpectedLeafAuthorityDecisionInputV1:
    """Prepare the V2 guard first, then freeze and cross-check the candidate."""

    try:
        return _freeze_guarded_expected_leaf_authority_candidate(
            request,
            authority_input,
            leaf_authority_input,
            leaf_case_inputs,
            execution_invocation,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except ExpectedLeafGuardedDecisionFreezeError:
        raise
    except Exception:
        _fail(ExpectedLeafGuardedDecisionFreezeCode.INTERNAL)


__all__ = [
    "EXPECTED_LEAF_GUARDED_DECISION_FREEZE_DECISION_STATUS",
    "EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_ARTIFACT_TYPE",
    "EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_DIGEST_DOMAIN",
    "EXPECTED_LEAF_GUARDED_DECISION_FREEZE_STATUS",
    "ExpectedLeafGuardedDecisionFreezeCode",
    "ExpectedLeafGuardedDecisionFreezeError",
    "ExpectedLeafGuardedDecisionFreezeReceiptV1",
    "FrozenGuardedExpectedLeafAuthorityDecisionInputV1",
    "MAXIMUM_EXPECTED_LEAF_GUARDED_DECISION_FREEZE_CASES",
    "MAXIMUM_EXPECTED_LEAF_GUARDED_DECISION_FREEZE_RECEIPT_BYTES",
    "expected_leaf_guarded_decision_freeze_receipt_bytes",
    "expected_leaf_guarded_decision_freeze_receipt_sha256",
    "freeze_guarded_expected_leaf_authority_candidate",
]
