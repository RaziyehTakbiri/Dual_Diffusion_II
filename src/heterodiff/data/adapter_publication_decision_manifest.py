"""Write-free preparation of an authority-bound decision guard manifest.

This module validates the independently anchored profile and all publication
bindings before constructing an exact pre-run input set and run manifest.  It
does not access paths, invoke adapters or oracles, start a process, accept an
execution receipt, serialize publication artifacts, write files, or decide a
gate.  The eventual verifier must implement the same schemas independently.
"""

from __future__ import annotations

import hashlib
import json
from typing import NamedTuple

from .adapter_publication_authority import (
    PublicationAuthorityCode,
    PublicationAuthorityError,
    ValidatedPublicationBindingAuthorityV1,
    domain_separated_sha256,
    validate_approved_profile_registry,
    validate_publication_binding_authority,
)
from .adapter_publication_authority_types import (
    DECISION_EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE,
    DECISION_EXECUTION_INPUT_SET_ARTIFACT_TYPE,
    MAXIMUM_APPROVED_PROFILE_BYTES,
    MAXIMUM_DECISION_GUARD_MANIFEST_BYTES,
    ApprovedPublicationAuthorityInputV1,
    ApprovedPublicationProfileV1,
    DecisionExecutionGuardRunManifestV1,
    DecisionExecutionInvocationV1,
)
from .adapter_publication_types import (
    PublicIdentifierRegistryV1,
    PublicationBindingInputV1,
    PublicationTypeError,
)
from .adapter_publication_prepare import (
    PublicationPreparationCode,
    PublicationPreparationError,
)


DECISION_EXECUTION_INPUT_SET_DIGEST_DOMAIN = (
    DECISION_EXECUTION_INPUT_SET_ARTIFACT_TYPE
)
DECISION_EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN = (
    DECISION_EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE
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
_MANIFEST_KEYS = (
    "address_space_limit_bytes",
    "address_space_limit_method_id",
    "allowed_execution_status_ids",
    "argv_sha256",
    "artifact_type",
    "authorized_write_root_sha256",
    "clock_method_id",
    "containment_policy_sha256",
    "cwd_launch_method_id",
    "decision_eligible_required",
    "dependency_lock_sha256",
    "environment_manifest_sha256",
    "environment_sha256",
    "execution_backend_id",
    "execution_guard_source_sha256",
    "execution_input_set_sha256",
    "filesystem_confinement_id",
    "format_version",
    "guard_implementation_status_id",
    "interpreter_executable_sha256",
    "managed_process_group_quiescence_required",
    "output_capture_method_id",
    "output_complete_required",
    "output_limit_bytes",
    "peak_rss_limit_bytes",
    "peak_rss_method_id",
    "process_containment_id",
    "publication_binding_set_sha256",
    "source_binding_format_id",
    "source_tree_archive_sha256",
    "source_tree_manifest_sha256",
    "test_inventory_sha256",
    "wall_time_limit_nanoseconds",
    "working_directory_sha256",
)


class PreparedDecisionGuardManifestV1(NamedTuple):
    """Immutable, pre-run bytes plus the authority used to derive them."""

    binding_authority: ValidatedPublicationBindingAuthorityV1
    execution_input_set_bytes: bytes
    execution_input_set_sha256: str
    manifest: DecisionExecutionGuardRunManifestV1
    manifest_bytes: bytes
    manifest_sha256: str


def _canonical_bytes(value: object, *, maximum: int) -> bytes:
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise PublicationTypeError(
            "decision manifest value is not canonically encodable"
        ) from error
    if not result or len(result) > maximum:
        raise PublicationTypeError(
            "decision manifest value exceeds its byte ceiling"
        )
    return result


def decision_execution_input_set_tree(
    profile: ApprovedPublicationProfileV1,
) -> dict:
    """Project only profile-authenticated case and hostile expectations."""

    if type(profile) is not ApprovedPublicationProfileV1:
        raise TypeError("approved publication profile must be exact")
    return {
        "artifact_type": DECISION_EXECUTION_INPUT_SET_ARTIFACT_TYPE,
        "case_expectations": [
            {name: getattr(item, name) for name in _CASE_KEYS}
            for item in profile.case_expectations
        ],
        "format_version": "1",
        "hostile_control_expectations": [
            {name: getattr(item, name) for name in _HOSTILE_KEYS}
            for item in profile.hostile_control_expectations
        ],
    }


def decision_execution_input_set_bytes(
    profile: ApprovedPublicationProfileV1,
) -> bytes:
    return _canonical_bytes(
        decision_execution_input_set_tree(profile),
        maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
    )


def decision_guard_manifest_tree(
    value: DecisionExecutionGuardRunManifestV1,
) -> dict:
    """Return the exact 34-field canonical manifest projection."""

    if type(value) is not DecisionExecutionGuardRunManifestV1:
        raise TypeError("decision execution guard manifest must be exact")
    return {
        name: (
            list(value.allowed_execution_status_ids)
            if name == "allowed_execution_status_ids"
            else getattr(value, name)
        )
        for name in _MANIFEST_KEYS
    }


def decision_guard_manifest_bytes(
    value: DecisionExecutionGuardRunManifestV1,
) -> bytes:
    return _canonical_bytes(
        decision_guard_manifest_tree(value),
        maximum=MAXIMUM_DECISION_GUARD_MANIFEST_BYTES,
    )


def _validate_invocation(
    invocation: DecisionExecutionInvocationV1,
    profile: ApprovedPublicationProfileV1,
) -> None:
    if type(invocation) is not DecisionExecutionInvocationV1:
        raise PublicationAuthorityError(
            PublicationAuthorityCode.AUTH_INPUT_TYPE
        )
    policy = profile.execution_policy
    observed = {
        "argv_sha256": hashlib.sha256(invocation.argv_bytes).hexdigest(),
        "authorized_write_root_sha256": hashlib.sha256(
            invocation.authorized_write_root_bytes
        ).hexdigest(),
        "containment_policy_sha256": hashlib.sha256(
            invocation.containment_policy_bytes
        ).hexdigest(),
        "environment_sha256": hashlib.sha256(
            invocation.environment_bytes
        ).hexdigest(),
        "working_directory_sha256": hashlib.sha256(
            invocation.working_directory_bytes
        ).hexdigest(),
    }
    if any(getattr(policy, name) != digest for name, digest in observed.items()):
        raise PublicationAuthorityError(
            PublicationAuthorityCode.AUTH_EXECUTION_INVOCATION_MISMATCH
        )


def _prepare_decision_guard_manifest(
    bindings: PublicationBindingInputV1,
    public_ids: PublicIdentifierRegistryV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    execution_invocation: DecisionExecutionInvocationV1,
) -> PreparedDecisionGuardManifestV1:
    """Validate external authority and construct exact pre-run guard bytes."""

    validated = validate_publication_binding_authority(
        bindings,
        public_ids,
        authority_input,
    )
    profile = validated.authority.profile
    validate_approved_profile_registry(profile, public_ids)
    _validate_invocation(execution_invocation, profile)

    input_bytes = decision_execution_input_set_bytes(profile)
    input_sha256 = domain_separated_sha256(
        DECISION_EXECUTION_INPUT_SET_DIGEST_DOMAIN,
        input_bytes,
    )
    policy = profile.execution_policy
    binding_set = validated.binding_set
    manifest = DecisionExecutionGuardRunManifestV1(
        address_space_limit_bytes=policy.address_space_limit_bytes,
        address_space_limit_method_id=policy.address_space_limit_method_id,
        allowed_execution_status_ids=policy.allowed_execution_status_ids,
        argv_sha256=policy.argv_sha256,
        authorized_write_root_sha256=policy.authorized_write_root_sha256,
        clock_method_id=policy.clock_method_id,
        containment_policy_sha256=policy.containment_policy_sha256,
        cwd_launch_method_id=policy.cwd_launch_method_id,
        dependency_lock_sha256=binding_set.dependency_lock_sha256,
        environment_manifest_sha256=(
            binding_set.environment_manifest_sha256
        ),
        environment_sha256=policy.environment_sha256,
        execution_backend_id=policy.execution_backend_id,
        execution_guard_source_sha256=(
            binding_set.execution_guard_source_sha256
        ),
        execution_input_set_sha256=input_sha256,
        filesystem_confinement_id=policy.filesystem_confinement_id,
        guard_implementation_status_id=(
            policy.guard_implementation_status_id
        ),
        interpreter_executable_sha256=(
            binding_set.interpreter_executable_sha256
        ),
        output_capture_method_id=policy.output_capture_method_id,
        peak_rss_method_id=policy.peak_rss_method_id,
        process_containment_id=policy.process_containment_id,
        publication_binding_set_sha256=validated.binding_set_sha256,
        source_binding_format_id=policy.source_binding_format_id,
        source_tree_archive_sha256=binding_set.source_tree_archive_sha256,
        source_tree_manifest_sha256=binding_set.source_tree_manifest_sha256,
        test_inventory_sha256=binding_set.test_inventory_sha256,
        working_directory_sha256=policy.working_directory_sha256,
    )
    manifest_bytes = decision_guard_manifest_bytes(manifest)
    manifest_sha256 = domain_separated_sha256(
        DECISION_EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN,
        manifest_bytes,
    )
    return PreparedDecisionGuardManifestV1(
        binding_authority=validated,
        execution_input_set_bytes=input_bytes,
        execution_input_set_sha256=input_sha256,
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        manifest_sha256=manifest_sha256,
    )


def prepare_decision_guard_manifest(
    bindings: PublicationBindingInputV1,
    public_ids: PublicIdentifierRegistryV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    execution_invocation: DecisionExecutionInvocationV1,
) -> PreparedDecisionGuardManifestV1:
    """Return exact pre-run bytes with only the closed public error surface."""

    try:
        return _prepare_decision_guard_manifest(
            bindings,
            public_ids,
            authority_input,
            execution_invocation,
        )
    except PublicationAuthorityError as error:
        if error.code == PublicationAuthorityCode.AUTH_INPUT_TYPE.value:
            code = PublicationPreparationCode.PUB_INPUT_TYPE
        elif error.code in (
            PublicationAuthorityCode.AUTH_BINDING_MISMATCH.value,
            PublicationAuthorityCode.AUTH_EXECUTION_INVOCATION_MISMATCH.value,
        ):
            code = PublicationPreparationCode.PUB_BINDING_MISMATCH
        else:
            code = PublicationPreparationCode.PUB_AUTHORITY_INVALID
        raise PublicationPreparationError(code) from None
    except PublicationTypeError:
        raise PublicationPreparationError(
            PublicationPreparationCode.PUB_CANONICALIZATION
        ) from None
    except Exception:
        raise PublicationPreparationError(
            PublicationPreparationCode.INTERNAL_ERROR
        ) from None


__all__ = [
    "DECISION_EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN",
    "DECISION_EXECUTION_INPUT_SET_DIGEST_DOMAIN",
    "PreparedDecisionGuardManifestV1",
    "decision_execution_input_set_bytes",
    "decision_execution_input_set_tree",
    "decision_guard_manifest_bytes",
    "decision_guard_manifest_tree",
    "prepare_decision_guard_manifest",
]
