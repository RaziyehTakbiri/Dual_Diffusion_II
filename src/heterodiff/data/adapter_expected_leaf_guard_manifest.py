"""Write-free preparation of an authority-bound expected-leaf V2 guard.

This module validates raw base and expected-leaf authority inputs, snapshots
the five execution-invocation byte manifests, reconstructs the exact V2
execution-input set, and only then builds the separately versioned pre-run
guard manifest.  It has no adapter, oracle, receipt, path, process, write, or
decision surface.

Successful preparation proves deterministic consistency relative to the
supplied anchors and policy bytes.  It does not prove external provenance,
manifest or input consumption, execution, containment, semantic truth, or a
gate decision.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import NamedTuple

from . import adapter_expected_leaf_authority as _leaf_authority
from . import adapter_expected_leaf_execution_input as _execution_input
from . import adapter_publication_decision_manifest as _base_manifest
from .adapter_expected_leaf_authority_types import (
    MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES,
    MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES,
    ApprovedExpectedLeafAuthorityInputV1,
)
from .adapter_expected_leaf_guard_types import (
    EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_ARTIFACT_TYPE,
    EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_DIGEST_DOMAIN,
    EXPECTED_LEAF_DECISION_INPUT_SET_V2_ARTIFACT_TYPE,
    MAXIMUM_EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_BYTES,
    MAXIMUM_EXPECTED_LEAF_DECISION_INPUT_SET_V2_BYTES,
    ExpectedLeafDecisionExecutionGuardRunManifestV2,
)
from .adapter_publication_authority import (
    PublicationAuthorityError,
    ValidatedPublicationBindingAuthorityV1,
    domain_separated_sha256,
)
from .adapter_publication_authority_types import (
    ApprovedPublicationAuthorityInputV1,
    DecisionExecutionInvocationV1,
)
from .adapter_expected_leaf_authority import (
    ValidatedApprovedExpectedLeafAuthorityV1,
)
from .adapter_expected_leaf_execution_input import (
    PreparedDecisionExecutionInputSetV2,
)
from .adapter_publication_prepare import PublicationPreparationError
from .adapter_publication_types import (
    PublicIdentifierRegistryV1,
    PublicationBindingInputV1,
)


class PreparedExpectedLeafDecisionGuardManifestV2(NamedTuple):
    """Immutable local preparation transport; never execution evidence.

    ``execution_invocation`` is an exact clone made before preparation.  A
    later backend can therefore receive the five validated byte manifests
    without consulting a caller-owned dataclass again.
    """

    binding_authority: ValidatedPublicationBindingAuthorityV1
    expected_leaf_authority: ValidatedApprovedExpectedLeafAuthorityV1
    prepared_execution_input_set: PreparedDecisionExecutionInputSetV2
    execution_invocation: DecisionExecutionInvocationV1
    manifest: ExpectedLeafDecisionExecutionGuardRunManifestV2
    manifest_bytes: bytes
    manifest_sha256: str


class ExpectedLeafGuardManifestCode(str, Enum):
    """Closed preparation failures without attacker-controlled interpolation."""

    INPUT_TYPE = "EXPECTED_LEAF_GUARD_INPUT_TYPE"
    INPUT_RESOURCE = "EXPECTED_LEAF_GUARD_INPUT_RESOURCE"
    BASE_AUTHORITY_OR_INVOCATION = (
        "EXPECTED_LEAF_GUARD_BASE_AUTHORITY_OR_INVOCATION"
    )
    LEAF_AUTHORITY = "EXPECTED_LEAF_GUARD_LEAF_AUTHORITY"
    V2_INPUT_SET = "EXPECTED_LEAF_GUARD_V2_INPUT_SET"
    MANIFEST = "EXPECTED_LEAF_GUARD_MANIFEST"
    INTERNAL = "EXPECTED_LEAF_GUARD_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExpectedLeafGuardManifestCode.INPUT_TYPE: (
            "expected-leaf guard input has an invalid exact type"
        ),
        ExpectedLeafGuardManifestCode.INPUT_RESOURCE: (
            "expected-leaf guard input exceeds a resource ceiling"
        ),
        ExpectedLeafGuardManifestCode.BASE_AUTHORITY_OR_INVOCATION: (
            "base authority or execution invocation does not match"
        ),
        ExpectedLeafGuardManifestCode.LEAF_AUTHORITY: (
            "expected-leaf authority does not match"
        ),
        ExpectedLeafGuardManifestCode.V2_INPUT_SET: (
            "expected-leaf V2 execution input does not match"
        ),
        ExpectedLeafGuardManifestCode.MANIFEST: (
            "expected-leaf V2 guard manifest is invalid"
        ),
        ExpectedLeafGuardManifestCode.INTERNAL: (
            "expected-leaf V2 guard preparation failed internally"
        ),
    }
)


class ExpectedLeafGuardManifestError(ValueError):
    """One fixed, coded V2 guard-preparation failure."""

    def __init__(self, code: ExpectedLeafGuardManifestCode) -> None:
        if type(code) is not ExpectedLeafGuardManifestCode:
            raise TypeError("expected-leaf guard error code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


_MANIFEST_KEYS = (
    "adapter_child_case_identity_mode_id",
    "adapter_child_expected_material_visibility_id",
    "adapter_child_input_profile_id",
    "adapter_child_source_load_mode_id",
    "adapter_child_v2_digest_visibility_id",
    "adapter_child_v2_visibility_id",
    "address_space_limit_bytes",
    "address_space_limit_method_id",
    "allowed_execution_status_ids",
    "argv_sha256",
    "artifact_type",
    "authorized_write_root_sha256",
    "case_dispatch_after_v2_validation_required",
    "clock_method_id",
    "containment_policy_sha256",
    "cwd_launch_method_id",
    "decision_eligible_required",
    "dependency_lock_sha256",
    "environment_manifest_sha256",
    "environment_sha256",
    "execution_backend_id",
    "execution_guard_source_sha256",
    "execution_input_set_artifact_type",
    "execution_input_set_byte_count",
    "execution_input_set_consumption_required",
    "execution_input_set_file_sha256",
    "execution_input_set_sha256",
    "execution_topology_requirement_id",
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
    "postrun_containment_receipt_required",
    "process_containment_id",
    "publication_binding_set_sha256",
    "separate_address_space_required",
    "source_binding_format_id",
    "source_tree_archive_sha256",
    "source_tree_manifest_sha256",
    "test_inventory_sha256",
    "v2_input_consumer_role_id",
    "wall_time_limit_nanoseconds",
    "working_directory_sha256",
)


def _fail(code: ExpectedLeafGuardManifestCode) -> None:
    raise ExpectedLeafGuardManifestError(code) from None


def _snapshot_execution_invocation(
    value: object,
) -> DecisionExecutionInvocationV1:
    if type(value) is not DecisionExecutionInvocationV1:
        _fail(ExpectedLeafGuardManifestCode.INPUT_TYPE)
    try:
        DecisionExecutionInvocationV1.__post_init__(value)
        return DecisionExecutionInvocationV1(
            argv_bytes=value.argv_bytes,
            authorized_write_root_bytes=value.authorized_write_root_bytes,
            containment_policy_bytes=value.containment_policy_bytes,
            environment_bytes=value.environment_bytes,
            working_directory_bytes=value.working_directory_bytes,
        )
    except ExpectedLeafGuardManifestError:
        raise
    except ValueError:
        _fail(ExpectedLeafGuardManifestCode.INPUT_RESOURCE)
    except (AttributeError, TypeError):
        _fail(ExpectedLeafGuardManifestCode.INPUT_TYPE)


def expected_leaf_decision_guard_manifest_v2_tree(
    value: ExpectedLeafDecisionExecutionGuardRunManifestV2,
) -> dict:
    """Return the exact 49-field V2 guard-manifest projection."""

    if type(value) is not ExpectedLeafDecisionExecutionGuardRunManifestV2:
        raise TypeError("expected-leaf V2 guard manifest must be exact")
    ExpectedLeafDecisionExecutionGuardRunManifestV2.__post_init__(value)
    return {
        name: (
            list(value.allowed_execution_status_ids)
            if name == "allowed_execution_status_ids"
            else getattr(value, name)
        )
        for name in _MANIFEST_KEYS
    }


def expected_leaf_decision_guard_manifest_v2_bytes(
    value: ExpectedLeafDecisionExecutionGuardRunManifestV2,
) -> bytes:
    """Serialize one exact V2 guard manifest as canonical ASCII JSON."""

    try:
        result = json.dumps(
            expected_leaf_decision_guard_manifest_v2_tree(value),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        raise ExpectedLeafGuardManifestError(
            ExpectedLeafGuardManifestCode.MANIFEST
        ) from None
    if (
        not result
        or len(result)
        > MAXIMUM_EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_BYTES
    ):
        _fail(ExpectedLeafGuardManifestCode.MANIFEST)
    return result


def expected_leaf_decision_guard_manifest_v2_sha256(
    value: ExpectedLeafDecisionExecutionGuardRunManifestV2,
) -> str:
    """Return the V2 manifest's domain-separated digest."""

    return domain_separated_sha256(
        EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_DIGEST_DOMAIN,
        expected_leaf_decision_guard_manifest_v2_bytes(value),
    )


def _prepare_expected_leaf_decision_guard_manifest_v2(
    bindings: PublicationBindingInputV1,
    public_ids: PublicIdentifierRegistryV1,
    base_authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    execution_invocation: DecisionExecutionInvocationV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> PreparedExpectedLeafDecisionGuardManifestV2:
    if (
        type(bindings) is not PublicationBindingInputV1
        or type(public_ids) is not PublicIdentifierRegistryV1
        or type(base_authority_input)
        is not ApprovedPublicationAuthorityInputV1
        or type(leaf_authority_input)
        is not ApprovedExpectedLeafAuthorityInputV1
        or type(expected_leaf_archive_inventory_bytes) is not bytes
        or type(expected_leaf_archive_bytes) is not bytes
    ):
        _fail(ExpectedLeafGuardManifestCode.INPUT_TYPE)
    if (
        not expected_leaf_archive_inventory_bytes
        or len(expected_leaf_archive_inventory_bytes)
        > MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES
        or not expected_leaf_archive_bytes
        or len(expected_leaf_archive_bytes) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES
    ):
        _fail(ExpectedLeafGuardManifestCode.INPUT_RESOURCE)

    invocation_snapshot = _snapshot_execution_invocation(execution_invocation)
    try:
        prepared_base = _base_manifest.prepare_decision_guard_manifest(
            bindings,
            public_ids,
            base_authority_input,
            invocation_snapshot,
        )
    except PublicationPreparationError:
        _fail(ExpectedLeafGuardManifestCode.BASE_AUTHORITY_OR_INVOCATION)
    except Exception:
        _fail(ExpectedLeafGuardManifestCode.BASE_AUTHORITY_OR_INVOCATION)
    if type(prepared_base) is not _base_manifest.PreparedDecisionGuardManifestV1:
        _fail(ExpectedLeafGuardManifestCode.BASE_AUTHORITY_OR_INVOCATION)

    try:
        leaf_authority = (
            _leaf_authority.validate_approved_expected_leaf_authority(
                leaf_authority_input,
                parent_authority=prepared_base.binding_authority.authority,
                public_identifier_registry=public_ids,
                source_archive_inventory_bytes=(
                    bindings.source_tree_manifest_bytes
                ),
                source_archive_bytes=bindings.source_tree_archive_bytes,
                expected_leaf_archive_inventory_bytes=(
                    expected_leaf_archive_inventory_bytes
                ),
                expected_leaf_archive_bytes=expected_leaf_archive_bytes,
            )
        )
    except PublicationAuthorityError:
        _fail(ExpectedLeafGuardManifestCode.LEAF_AUTHORITY)
    except Exception:
        _fail(ExpectedLeafGuardManifestCode.LEAF_AUTHORITY)
    if type(leaf_authority) is not ValidatedApprovedExpectedLeafAuthorityV1:
        _fail(ExpectedLeafGuardManifestCode.LEAF_AUTHORITY)

    try:
        prepared_input = (
            _execution_input.prepare_decision_execution_input_set_v2(
                prepared_base.binding_authority.authority,
                leaf_authority,
            )
        )
    except Exception:
        _fail(ExpectedLeafGuardManifestCode.V2_INPUT_SET)
    if type(prepared_input) is not PreparedDecisionExecutionInputSetV2:
        _fail(ExpectedLeafGuardManifestCode.V2_INPUT_SET)

    if (
        prepared_input.base_authority
        != prepared_base.binding_authority.authority
        or prepared_input.expected_leaf_authority != leaf_authority
        or prepared_input.base_execution_input_set_bytes
        != prepared_base.execution_input_set_bytes
        or prepared_input.base_execution_input_set_sha256
        != prepared_base.execution_input_set_sha256
    ):
        _fail(ExpectedLeafGuardManifestCode.V2_INPUT_SET)
    try:
        v2_bytes = prepared_input.execution_input_set_bytes
        if (
            type(v2_bytes) is not bytes
            or not v2_bytes
            or len(v2_bytes)
            > MAXIMUM_EXPECTED_LEAF_DECISION_INPUT_SET_V2_BYTES
            or _execution_input.decision_execution_input_set_v2_sha256(
                v2_bytes
            )
            != prepared_input.execution_input_set_sha256
        ):
            _fail(ExpectedLeafGuardManifestCode.V2_INPUT_SET)
    except ExpectedLeafGuardManifestError:
        raise
    except Exception:
        _fail(ExpectedLeafGuardManifestCode.V2_INPUT_SET)

    base = prepared_base.manifest
    try:
        manifest = ExpectedLeafDecisionExecutionGuardRunManifestV2(
            address_space_limit_bytes=base.address_space_limit_bytes,
            address_space_limit_method_id=base.address_space_limit_method_id,
            allowed_execution_status_ids=base.allowed_execution_status_ids,
            argv_sha256=base.argv_sha256,
            authorized_write_root_sha256=base.authorized_write_root_sha256,
            clock_method_id=base.clock_method_id,
            containment_policy_sha256=base.containment_policy_sha256,
            cwd_launch_method_id=base.cwd_launch_method_id,
            dependency_lock_sha256=base.dependency_lock_sha256,
            environment_manifest_sha256=base.environment_manifest_sha256,
            environment_sha256=base.environment_sha256,
            execution_backend_id=base.execution_backend_id,
            execution_guard_source_sha256=base.execution_guard_source_sha256,
            execution_input_set_byte_count=len(v2_bytes),
            execution_input_set_file_sha256=hashlib.sha256(
                v2_bytes
            ).hexdigest(),
            execution_input_set_sha256=(
                prepared_input.execution_input_set_sha256
            ),
            filesystem_confinement_id=base.filesystem_confinement_id,
            guard_implementation_status_id=(
                base.guard_implementation_status_id
            ),
            interpreter_executable_sha256=(
                base.interpreter_executable_sha256
            ),
            output_capture_method_id=base.output_capture_method_id,
            peak_rss_method_id=base.peak_rss_method_id,
            process_containment_id=base.process_containment_id,
            publication_binding_set_sha256=(
                base.publication_binding_set_sha256
            ),
            source_binding_format_id=base.source_binding_format_id,
            source_tree_archive_sha256=base.source_tree_archive_sha256,
            source_tree_manifest_sha256=base.source_tree_manifest_sha256,
            test_inventory_sha256=base.test_inventory_sha256,
            working_directory_sha256=base.working_directory_sha256,
        )
        manifest_bytes = expected_leaf_decision_guard_manifest_v2_bytes(
            manifest
        )
        manifest_sha256 = domain_separated_sha256(
            EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_DIGEST_DOMAIN,
            manifest_bytes,
        )
    except ExpectedLeafGuardManifestError:
        raise
    except Exception:
        _fail(ExpectedLeafGuardManifestCode.MANIFEST)

    return PreparedExpectedLeafDecisionGuardManifestV2(
        binding_authority=prepared_base.binding_authority,
        expected_leaf_authority=leaf_authority,
        prepared_execution_input_set=prepared_input,
        execution_invocation=invocation_snapshot,
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        manifest_sha256=manifest_sha256,
    )


def prepare_expected_leaf_decision_guard_manifest_v2(
    bindings: PublicationBindingInputV1,
    public_ids: PublicIdentifierRegistryV1,
    base_authority_input: ApprovedPublicationAuthorityInputV1,
    leaf_authority_input: ApprovedExpectedLeafAuthorityInputV1,
    execution_invocation: DecisionExecutionInvocationV1,
    *,
    expected_leaf_archive_inventory_bytes: bytes,
    expected_leaf_archive_bytes: bytes,
) -> PreparedExpectedLeafDecisionGuardManifestV2:
    """Prepare exact V2 guard bytes through the closed public error surface."""

    try:
        return _prepare_expected_leaf_decision_guard_manifest_v2(
            bindings,
            public_ids,
            base_authority_input,
            leaf_authority_input,
            execution_invocation,
            expected_leaf_archive_inventory_bytes=(
                expected_leaf_archive_inventory_bytes
            ),
            expected_leaf_archive_bytes=expected_leaf_archive_bytes,
        )
    except ExpectedLeafGuardManifestError:
        raise
    except Exception:
        _fail(ExpectedLeafGuardManifestCode.INTERNAL)


__all__ = [
    "EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_ARTIFACT_TYPE",
    "EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_DIGEST_DOMAIN",
    "EXPECTED_LEAF_DECISION_INPUT_SET_V2_ARTIFACT_TYPE",
    "ExpectedLeafDecisionExecutionGuardRunManifestV2",
    "ExpectedLeafGuardManifestCode",
    "ExpectedLeafGuardManifestError",
    "MAXIMUM_EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_BYTES",
    "PreparedExpectedLeafDecisionGuardManifestV2",
    "expected_leaf_decision_guard_manifest_v2_bytes",
    "expected_leaf_decision_guard_manifest_v2_sha256",
    "expected_leaf_decision_guard_manifest_v2_tree",
    "prepare_expected_leaf_decision_guard_manifest_v2",
]
