"""Exact types for the additive expected-leaf V2 guard-manifest surface.

The types in this module describe pre-run policy bytes only.  Constructing one
does not prove that a backend consumed the manifest or its V2 input set, that
execution occurred, that a process was contained, or that a gate decision was
made.

This module is deliberately types-only: it performs no JSON, filesystem,
process, adapter, or oracle work and is not re-exported from the package root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .adapter_publication_authority_types import (
    MAXIMUM_DECISION_GUARD_MANIFEST_BYTES,
    DecisionExecutionGuardRunManifestV1,
)


EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_ARTIFACT_TYPE = (
    "heterodiff.adapter.decision-execution-guard-run-manifest.v2"
)
EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_DIGEST_DOMAIN = (
    EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_ARTIFACT_TYPE
)
EXPECTED_LEAF_DECISION_INPUT_SET_V2_ARTIFACT_TYPE = (
    "heterodiff.adapter.decision-execution-input-set.v2"
)
MAXIMUM_EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_BYTES = (
    MAXIMUM_DECISION_GUARD_MANIFEST_BYTES
)
MAXIMUM_EXPECTED_LEAF_DECISION_INPUT_SET_V2_BYTES = 4 * 1024 * 1024

EXPECTED_LEAF_EXECUTION_TOPOLOGY_REQUIREMENT_ID = (
    "trusted-v2-supervisor-separate-adapter-child-v1"
)
EXPECTED_LEAF_V2_INPUT_CONSUMER_ROLE_ID = "trusted-supervisor-only"
EXPECTED_LEAF_ADAPTER_CHILD_INPUT_PROFILE_ID = (
    "heterodiff.adapter.output-blind-case-input.v1"
)
EXPECTED_LEAF_ADAPTER_CHILD_V2_VISIBILITY_ID = "forbidden"
EXPECTED_LEAF_ADAPTER_CHILD_V2_DIGEST_VISIBILITY_ID = "forbidden"
EXPECTED_LEAF_ADAPTER_CHILD_EXPECTED_MATERIAL_VISIBILITY_ID = "forbidden"
EXPECTED_LEAF_ADAPTER_CHILD_CASE_IDENTITY_MODE_ID = (
    "pre-output-case-input-domain-sha256-v1"
)
EXPECTED_LEAF_ADAPTER_CHILD_SOURCE_LOAD_MODE_ID = (
    "archive-selected-exact-module-closure-v1"
)


@dataclass(frozen=True)
class ExpectedLeafDecisionExecutionGuardRunManifestV2:
    """Exact V2 pre-run manifest; it contains no outcome or receipt.

    The policy and binding fields intentionally retain the frozen V1 guard
    vocabulary.  The distinct artifact/format versions and fixed
    ``execution_input_set_artifact_type`` make it impossible to silently treat
    a V2 input-set digest as a V1 guard-manifest commitment.
    """

    address_space_limit_bytes: int
    address_space_limit_method_id: str
    allowed_execution_status_ids: Tuple[str, ...]
    argv_sha256: str
    authorized_write_root_sha256: str
    clock_method_id: str
    containment_policy_sha256: str
    cwd_launch_method_id: str
    dependency_lock_sha256: str
    environment_manifest_sha256: str
    environment_sha256: str
    execution_backend_id: str
    execution_guard_source_sha256: str
    execution_input_set_byte_count: int
    execution_input_set_file_sha256: str
    execution_input_set_sha256: str
    filesystem_confinement_id: str
    guard_implementation_status_id: str
    interpreter_executable_sha256: str
    output_capture_method_id: str
    peak_rss_method_id: str
    process_containment_id: str
    publication_binding_set_sha256: str
    source_binding_format_id: str
    source_tree_archive_sha256: str
    source_tree_manifest_sha256: str
    test_inventory_sha256: str
    working_directory_sha256: str
    artifact_type: str = field(
        default=EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_ARTIFACT_TYPE,
        init=False,
    )
    adapter_child_case_identity_mode_id: str = field(
        default=EXPECTED_LEAF_ADAPTER_CHILD_CASE_IDENTITY_MODE_ID,
        init=False,
    )
    adapter_child_expected_material_visibility_id: str = field(
        default=EXPECTED_LEAF_ADAPTER_CHILD_EXPECTED_MATERIAL_VISIBILITY_ID,
        init=False,
    )
    adapter_child_input_profile_id: str = field(
        default=EXPECTED_LEAF_ADAPTER_CHILD_INPUT_PROFILE_ID,
        init=False,
    )
    adapter_child_source_load_mode_id: str = field(
        default=EXPECTED_LEAF_ADAPTER_CHILD_SOURCE_LOAD_MODE_ID,
        init=False,
    )
    adapter_child_v2_digest_visibility_id: str = field(
        default=EXPECTED_LEAF_ADAPTER_CHILD_V2_DIGEST_VISIBILITY_ID,
        init=False,
    )
    adapter_child_v2_visibility_id: str = field(
        default=EXPECTED_LEAF_ADAPTER_CHILD_V2_VISIBILITY_ID,
        init=False,
    )
    case_dispatch_after_v2_validation_required: bool = field(
        default=True,
        init=False,
    )
    decision_eligible_required: bool = field(default=True, init=False)
    execution_topology_requirement_id: str = field(
        default=EXPECTED_LEAF_EXECUTION_TOPOLOGY_REQUIREMENT_ID,
        init=False,
    )
    execution_input_set_artifact_type: str = field(
        default=EXPECTED_LEAF_DECISION_INPUT_SET_V2_ARTIFACT_TYPE,
        init=False,
    )
    execution_input_set_consumption_required: bool = field(
        default=True,
        init=False,
    )
    format_version: str = field(default="2", init=False)
    managed_process_group_quiescence_required: bool = field(
        default=True,
        init=False,
    )
    output_complete_required: bool = field(default=True, init=False)
    output_limit_bytes: int = field(
        default=2 * 1024 * 1024,
        init=False,
    )
    peak_rss_limit_bytes: int = field(
        default=2 * 1024 * 1024 * 1024,
        init=False,
    )
    postrun_containment_receipt_required: bool = field(
        default=True,
        init=False,
    )
    separate_address_space_required: bool = field(default=True, init=False)
    v2_input_consumer_role_id: str = field(
        default=EXPECTED_LEAF_V2_INPUT_CONSUMER_ROLE_ID,
        init=False,
    )
    wall_time_limit_nanoseconds: int = field(
        default=180 * 1_000_000_000,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafDecisionExecutionGuardRunManifestV2:
            raise TypeError("expected-leaf V2 guard manifest must be exact")

        # Reuse the already frozen validation policy for every inherited field.
        # The temporary V1 value is validation machinery only; it is never
        # serialized or returned as the operative guard artifact.
        validated = DecisionExecutionGuardRunManifestV1(
            address_space_limit_bytes=self.address_space_limit_bytes,
            address_space_limit_method_id=self.address_space_limit_method_id,
            allowed_execution_status_ids=self.allowed_execution_status_ids,
            argv_sha256=self.argv_sha256,
            authorized_write_root_sha256=self.authorized_write_root_sha256,
            clock_method_id=self.clock_method_id,
            containment_policy_sha256=self.containment_policy_sha256,
            cwd_launch_method_id=self.cwd_launch_method_id,
            dependency_lock_sha256=self.dependency_lock_sha256,
            environment_manifest_sha256=self.environment_manifest_sha256,
            environment_sha256=self.environment_sha256,
            execution_backend_id=self.execution_backend_id,
            execution_guard_source_sha256=self.execution_guard_source_sha256,
            execution_input_set_sha256=self.execution_input_set_sha256,
            filesystem_confinement_id=self.filesystem_confinement_id,
            guard_implementation_status_id=(
                self.guard_implementation_status_id
            ),
            interpreter_executable_sha256=(
                self.interpreter_executable_sha256
            ),
            output_capture_method_id=self.output_capture_method_id,
            peak_rss_method_id=self.peak_rss_method_id,
            process_containment_id=self.process_containment_id,
            publication_binding_set_sha256=(
                self.publication_binding_set_sha256
            ),
            source_binding_format_id=self.source_binding_format_id,
            source_tree_archive_sha256=self.source_tree_archive_sha256,
            source_tree_manifest_sha256=self.source_tree_manifest_sha256,
            test_inventory_sha256=self.test_inventory_sha256,
            working_directory_sha256=self.working_directory_sha256,
        )
        object.__setattr__(
            self,
            "allowed_execution_status_ids",
            validated.allowed_execution_status_ids,
        )
        if (
            type(self.execution_input_set_byte_count) is not int
            or self.execution_input_set_byte_count <= 0
            or self.execution_input_set_byte_count
            > MAXIMUM_EXPECTED_LEAF_DECISION_INPUT_SET_V2_BYTES
        ):
            raise ValueError(
                "expected-leaf V2 input byte count is outside its exact bound"
            )
        if (
            type(self.execution_input_set_file_sha256) is not str
            or len(self.execution_input_set_file_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.execution_input_set_file_sha256
            )
        ):
            raise ValueError(
                "expected-leaf V2 input file digest is not canonical"
            )
        if (
            self.artifact_type
            != EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_ARTIFACT_TYPE
            or self.adapter_child_case_identity_mode_id
            != EXPECTED_LEAF_ADAPTER_CHILD_CASE_IDENTITY_MODE_ID
            or self.adapter_child_expected_material_visibility_id
            != EXPECTED_LEAF_ADAPTER_CHILD_EXPECTED_MATERIAL_VISIBILITY_ID
            or self.adapter_child_input_profile_id
            != EXPECTED_LEAF_ADAPTER_CHILD_INPUT_PROFILE_ID
            or self.adapter_child_source_load_mode_id
            != EXPECTED_LEAF_ADAPTER_CHILD_SOURCE_LOAD_MODE_ID
            or self.adapter_child_v2_digest_visibility_id
            != EXPECTED_LEAF_ADAPTER_CHILD_V2_DIGEST_VISIBILITY_ID
            or self.adapter_child_v2_visibility_id
            != EXPECTED_LEAF_ADAPTER_CHILD_V2_VISIBILITY_ID
            or self.case_dispatch_after_v2_validation_required is not True
            or self.execution_topology_requirement_id
            != EXPECTED_LEAF_EXECUTION_TOPOLOGY_REQUIREMENT_ID
            or self.execution_input_set_artifact_type
            != EXPECTED_LEAF_DECISION_INPUT_SET_V2_ARTIFACT_TYPE
            or self.execution_input_set_consumption_required is not True
            or self.format_version != "2"
            or self.decision_eligible_required is not True
            or self.managed_process_group_quiescence_required is not True
            or self.output_complete_required is not True
            or self.output_limit_bytes != validated.output_limit_bytes
            or self.peak_rss_limit_bytes != validated.peak_rss_limit_bytes
            or self.postrun_containment_receipt_required is not True
            or self.separate_address_space_required is not True
            or self.v2_input_consumer_role_id
            != EXPECTED_LEAF_V2_INPUT_CONSUMER_ROLE_ID
            or self.wall_time_limit_nanoseconds
            != validated.wall_time_limit_nanoseconds
        ):
            raise TypeError("expected-leaf V2 guard constants differ")


__all__ = [
    "EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_ARTIFACT_TYPE",
    "EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_DIGEST_DOMAIN",
    "EXPECTED_LEAF_DECISION_INPUT_SET_V2_ARTIFACT_TYPE",
    "EXPECTED_LEAF_EXECUTION_TOPOLOGY_REQUIREMENT_ID",
    "EXPECTED_LEAF_V2_INPUT_CONSUMER_ROLE_ID",
    "EXPECTED_LEAF_ADAPTER_CHILD_INPUT_PROFILE_ID",
    "EXPECTED_LEAF_ADAPTER_CHILD_V2_VISIBILITY_ID",
    "EXPECTED_LEAF_ADAPTER_CHILD_V2_DIGEST_VISIBILITY_ID",
    "EXPECTED_LEAF_ADAPTER_CHILD_EXPECTED_MATERIAL_VISIBILITY_ID",
    "EXPECTED_LEAF_ADAPTER_CHILD_CASE_IDENTITY_MODE_ID",
    "EXPECTED_LEAF_ADAPTER_CHILD_SOURCE_LOAD_MODE_ID",
    "ExpectedLeafDecisionExecutionGuardRunManifestV2",
    "MAXIMUM_EXPECTED_LEAF_DECISION_GUARD_MANIFEST_V2_BYTES",
    "MAXIMUM_EXPECTED_LEAF_DECISION_INPUT_SET_V2_BYTES",
]
