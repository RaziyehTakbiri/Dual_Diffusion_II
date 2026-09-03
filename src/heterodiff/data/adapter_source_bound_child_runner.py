"""Supervisor for one source-selected output-blind adapter child.

The supervisor validates raw closure/archive/dependency-lock bytes before
spawn, constructs the one-field pre-output request, sends the implementation
material on a distinct inherited pipe, and accepts a response only after
bounded duplex completion, empty stderr, zero exit, response identity joins,
source-load-report reconciliation, and independent adapted-bundle
verification.

This local macOS/POSIX development boundary removes caller-supplied complete
samples and same-address-space execution from the actual-output path.  It is
not containment or execution attestation: the child retains host filesystem,
network, native dependency, and process APIs; software receipts are forgeable;
and a fresh process does not prove fresh semantic recomputation.  The schemas
provide no dedicated expected-side, V2, authority, oracle, or decision field;
arbitrary admitted byte or text fields can still encode such material.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
import errno
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import tempfile
import time
from types import MappingProxyType
from typing import NamedTuple, Optional, Tuple

from . import adapter_adapted_evidence_bundle_verifier as _verifier
from . import adapter_evidence as _evidence
from . import adapter_implementation_closure as _closure
from .adapter_output_blind_child_abi import (
    MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES,
    OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_DOMAIN,
    OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_DOMAIN,
    OutputBlindAdapterChildABIError,
    OutputBlindAdapterChildFailureCode,
    OutputBlindAdapterChildRequestV1,
    ValidatedOutputBlindAdapterChildSuccessV1,
    build_output_blind_adapter_child_request_frame,
    validate_output_blind_adapter_child_failure_identity,
    validate_output_blind_adapter_child_success_identity,
)
from .adapter_output_blind_child_bootstrap import (
    MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_ARCHIVE_BYTES,
    MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_BYTES,
    MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_INVENTORY_BYTES,
    OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_BYTES,
    OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256,
    build_output_blind_implementation_closure_pipe_frame,
)
from .adapter_output_blind_trusted_runtime_profile import (
    OUTPUT_BLIND_TRUSTED_RUNTIME_CALLABLE_NAME,
    OUTPUT_BLIND_TRUSTED_RUNTIME_MODULE_NAME,
    OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256,
    OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES,
    TrustedRuntimeSourceModuleV1,
    output_blind_runtime_capture_profile_sha256,
)
from .adapter_output_blind_case_input import (
    MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES,
    parse_output_blind_case_input_v1,
)


SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.source-bound-child-run-receipt.v1"
)
SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_DIGEST_DOMAIN = (
    SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE
)
SOURCE_BOUND_ADAPTER_CHILD_RUN_STATUS = (
    "COMPLETED_RESPONSE_IDENTITY_MATCHED_AND_BUNDLE_INDEPENDENTLY_VERIFIED"
)
SOURCE_BOUND_ADAPTER_CHILD_RUN_DECISION_STATUS = "NOT_MADE_BY_CHILD_RUNNER"

MAXIMUM_SOURCE_BOUND_DEPENDENCY_LOCK_BYTES = 4 * 1024 * 1024
MAXIMUM_SOURCE_BOUND_INTERPRETER_BYTES = 64 * 1024 * 1024
MAXIMUM_SOURCE_BOUND_STDERR_BYTES = 64 * 1024
MAXIMUM_SOURCE_BOUND_AGGREGATE_OUTPUT_BYTES = (
    MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES
    + MAXIMUM_SOURCE_BOUND_STDERR_BYTES
)
MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES = 128 * 1024
SOURCE_BOUND_CHILD_WALL_TIME_LIMIT_NANOSECONDS = 180 * 1_000_000_000
SOURCE_BOUND_CHILD_READ_CHUNK_BYTES = 64 * 1024
SOURCE_BOUND_CHILD_WRITE_CHUNK_BYTES = 64 * 1024
_POLL_SECONDS = 0.05
_TERMINATION_SECONDS = 0.5
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SourceBoundAdapterChildRunCode(str, Enum):
    """Closed supervisor-side failures for the local child boundary."""

    INPUT_TYPE = "SOURCE_BOUND_CHILD_INPUT_TYPE"
    INPUT_RESOURCE = "SOURCE_BOUND_CHILD_INPUT_RESOURCE"
    CASE_INPUT_INVALID = "SOURCE_BOUND_CHILD_CASE_INPUT_INVALID"
    CLOSURE_INVALID = "SOURCE_BOUND_CHILD_CLOSURE_INVALID"
    ARCHIVE_INVALID = "SOURCE_BOUND_CHILD_ARCHIVE_INVALID"
    SOURCE_SELECTION_FAILED = "SOURCE_BOUND_CHILD_SOURCE_SELECTION_FAILED"
    ENTRYPOINT_INVALID = "SOURCE_BOUND_CHILD_ENTRYPOINT_INVALID"
    IMPORT_POLICY_INVALID = "SOURCE_BOUND_CHILD_IMPORT_POLICY_INVALID"
    TRUSTED_RUNTIME_PROFILE_MISMATCH = (
        "SOURCE_BOUND_CHILD_TRUSTED_RUNTIME_PROFILE_MISMATCH"
    )
    INTERPRETER_INVALID = "SOURCE_BOUND_CHILD_INTERPRETER_INVALID"
    REQUEST_INVALID = "SOURCE_BOUND_CHILD_REQUEST_INVALID"
    PLATFORM_UNAVAILABLE = "SOURCE_BOUND_CHILD_PLATFORM_UNAVAILABLE"
    CLOCK_INVALID = "SOURCE_BOUND_CHILD_CLOCK_INVALID"
    SPAWN_FAILED = "SOURCE_BOUND_CHILD_SPAWN_FAILED"
    PROCESS_PROTOCOL_INVALID = "SOURCE_BOUND_CHILD_PROCESS_PROTOCOL_INVALID"
    WALL_TIME_LIMIT = "SOURCE_BOUND_CHILD_WALL_TIME_LIMIT"
    STDOUT_LIMIT = "SOURCE_BOUND_CHILD_STDOUT_LIMIT"
    STDERR_LIMIT = "SOURCE_BOUND_CHILD_STDERR_LIMIT"
    AGGREGATE_OUTPUT_LIMIT = "SOURCE_BOUND_CHILD_AGGREGATE_OUTPUT_LIMIT"
    PARTIAL_INPUT = "SOURCE_BOUND_CHILD_PARTIAL_INPUT"
    SIGNAL_EXIT = "SOURCE_BOUND_CHILD_SIGNAL_EXIT"
    NONZERO_EXIT = "SOURCE_BOUND_CHILD_NONZERO_EXIT"
    NONEMPTY_STDERR = "SOURCE_BOUND_CHILD_NONEMPTY_STDERR"
    INCOMPLETE_OUTPUT = "SOURCE_BOUND_CHILD_INCOMPLETE_OUTPUT"
    INVALID_RESPONSE = "SOURCE_BOUND_CHILD_INVALID_RESPONSE"
    CHILD_REPORTED_FAILURE = "SOURCE_BOUND_CHILD_REPORTED_FAILURE"
    RESPONSE_IDENTITY_MISMATCH = (
        "SOURCE_BOUND_CHILD_RESPONSE_IDENTITY_MISMATCH"
    )
    SOURCE_LOAD_REPORT_MISMATCH = (
        "SOURCE_BOUND_CHILD_SOURCE_LOAD_REPORT_MISMATCH"
    )
    PROCESS_GROUP_NONQUIESCENCE = (
        "SOURCE_BOUND_CHILD_PROCESS_GROUP_NONQUIESCENCE"
    )
    VERIFICATION_FAILED = "SOURCE_BOUND_CHILD_VERIFICATION_FAILED"
    RECEIPT_INVALID = "SOURCE_BOUND_CHILD_RECEIPT_INVALID"
    INTERNAL = "SOURCE_BOUND_CHILD_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        SourceBoundAdapterChildRunCode.INPUT_TYPE: (
            "source-bound child input has an invalid exact type"
        ),
        SourceBoundAdapterChildRunCode.INPUT_RESOURCE: (
            "source-bound child input exceeds a fixed resource bound"
        ),
        SourceBoundAdapterChildRunCode.CASE_INPUT_INVALID: (
            "source-bound child case input is invalid"
        ),
        SourceBoundAdapterChildRunCode.CLOSURE_INVALID: (
            "source-bound child implementation closure is invalid"
        ),
        SourceBoundAdapterChildRunCode.ARCHIVE_INVALID: (
            "source-bound child source archive is invalid"
        ),
        SourceBoundAdapterChildRunCode.SOURCE_SELECTION_FAILED: (
            "source-bound child source selection did not complete"
        ),
        SourceBoundAdapterChildRunCode.ENTRYPOINT_INVALID: (
            "source-bound child entry point is invalid"
        ),
        SourceBoundAdapterChildRunCode.IMPORT_POLICY_INVALID: (
            "source-bound child import policy is invalid"
        ),
        SourceBoundAdapterChildRunCode.TRUSTED_RUNTIME_PROFILE_MISMATCH: (
            "source-bound child trusted runtime source profile differs"
        ),
        SourceBoundAdapterChildRunCode.INTERPRETER_INVALID: (
            "source-bound child interpreter is invalid"
        ),
        SourceBoundAdapterChildRunCode.REQUEST_INVALID: (
            "source-bound child request is invalid"
        ),
        SourceBoundAdapterChildRunCode.PLATFORM_UNAVAILABLE: (
            "source-bound child platform support is unavailable"
        ),
        SourceBoundAdapterChildRunCode.CLOCK_INVALID: (
            "source-bound child monotonic clock is invalid"
        ),
        SourceBoundAdapterChildRunCode.SPAWN_FAILED: (
            "source-bound child process did not start"
        ),
        SourceBoundAdapterChildRunCode.PROCESS_PROTOCOL_INVALID: (
            "source-bound child process transport is invalid"
        ),
        SourceBoundAdapterChildRunCode.WALL_TIME_LIMIT: (
            "source-bound child exceeded its wall-time ceiling"
        ),
        SourceBoundAdapterChildRunCode.STDOUT_LIMIT: (
            "source-bound child stdout exceeded its byte ceiling"
        ),
        SourceBoundAdapterChildRunCode.STDERR_LIMIT: (
            "source-bound child stderr exceeded its byte ceiling"
        ),
        SourceBoundAdapterChildRunCode.AGGREGATE_OUTPUT_LIMIT: (
            "source-bound child aggregate output exceeded its byte ceiling"
        ),
        SourceBoundAdapterChildRunCode.PARTIAL_INPUT: (
            "source-bound child did not consume completely supplied channels"
        ),
        SourceBoundAdapterChildRunCode.SIGNAL_EXIT: (
            "source-bound child exited because of a signal"
        ),
        SourceBoundAdapterChildRunCode.NONZERO_EXIT: (
            "source-bound child exited with a nonzero status"
        ),
        SourceBoundAdapterChildRunCode.NONEMPTY_STDERR: (
            "source-bound child produced stderr bytes"
        ),
        SourceBoundAdapterChildRunCode.INCOMPLETE_OUTPUT: (
            "source-bound child output did not complete"
        ),
        SourceBoundAdapterChildRunCode.INVALID_RESPONSE: (
            "source-bound child response frame is invalid"
        ),
        SourceBoundAdapterChildRunCode.CHILD_REPORTED_FAILURE: (
            "source-bound child returned a closed failure response"
        ),
        SourceBoundAdapterChildRunCode.RESPONSE_IDENTITY_MISMATCH: (
            "source-bound child response identity does not match"
        ),
        SourceBoundAdapterChildRunCode.SOURCE_LOAD_REPORT_MISMATCH: (
            "source-bound child source-load report does not match closure"
        ),
        SourceBoundAdapterChildRunCode.PROCESS_GROUP_NONQUIESCENCE: (
            "source-bound child process group did not remain quiescent"
        ),
        SourceBoundAdapterChildRunCode.VERIFICATION_FAILED: (
            "source-bound child adapted bundle failed independent verification"
        ),
        SourceBoundAdapterChildRunCode.RECEIPT_INVALID: (
            "source-bound child run receipt is invalid"
        ),
        SourceBoundAdapterChildRunCode.INTERNAL: (
            "source-bound child runner failed internally"
        ),
    }
)


class SourceBoundAdapterChildRunError(ValueError):
    """One fixed supervisor failure, optionally carrying a closed child code."""

    def __init__(
        self,
        code: SourceBoundAdapterChildRunCode,
        *,
        child_failure_code: Optional[
            OutputBlindAdapterChildFailureCode
        ] = None,
    ) -> None:
        if type(code) is not SourceBoundAdapterChildRunCode:
            raise TypeError("source-bound child run code must be exact")
        if child_failure_code is not None and (
            type(child_failure_code)
            is not OutputBlindAdapterChildFailureCode
        ):
            raise TypeError("child_failure_code must be closed")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value
        self.child_failure_code = (
            None
            if child_failure_code is None
            else child_failure_code.value
        )


def _fail(
    code: SourceBoundAdapterChildRunCode,
    *,
    child_failure_code: Optional[
        OutputBlindAdapterChildFailureCode
    ] = None,
) -> None:
    raise SourceBoundAdapterChildRunError(
        code,
        child_failure_code=child_failure_code,
    ) from None


@dataclass(frozen=True)
class SourceBoundAdapterChildRunInputV1:
    """Raw-byte supervisor inputs; expected-side artifacts are absent."""

    case_input_bytes: bytes
    implementation_closure_bytes: bytes
    source_archive_inventory_bytes: bytes
    source_archive_bytes: bytes
    dependency_lock_bytes: bytes
    interpreter_path: str
    allowed_exclusion_reason_codes: Tuple[str, ...] = ()
    allowed_censor_reason_codes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self) is not SourceBoundAdapterChildRunInputV1:
            raise TypeError("source-bound child run input must be exact")
        bounded = (
            (self.case_input_bytes, MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES),
            (
                self.implementation_closure_bytes,
                MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_BYTES,
            ),
            (
                self.source_archive_inventory_bytes,
                MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_INVENTORY_BYTES,
            ),
            (
                self.source_archive_bytes,
                MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_ARCHIVE_BYTES,
            ),
            (
                self.dependency_lock_bytes,
                MAXIMUM_SOURCE_BOUND_DEPENDENCY_LOCK_BYTES,
            ),
        )
        if any(
            type(value) is not bytes
            or not value
            or len(value) > maximum
            for value, maximum in bounded
        ):
            raise ValueError("source-bound raw input is outside its bound")
        if (
            type(self.interpreter_path) is not str
            or not self.interpreter_path
            or "\x00" in self.interpreter_path
        ):
            raise TypeError("interpreter_path must be nonempty exact text")
        if (
            type(self.allowed_exclusion_reason_codes) is not tuple
            or type(self.allowed_censor_reason_codes) is not tuple
        ):
            raise TypeError("reason registries must be exact tuples")


@dataclass(frozen=True)
class SourceBoundAdapterChildRunReceiptV1:
    """Forgeable local transcript with exact narrow claims and nonclaims."""

    run_input_sha256: str
    request_frame_sha256: str
    case_input_sha256: str
    implementation_closure_sha256: str
    implementation_closure_validation_receipt_sha256: str
    source_archive_inventory_sha256: str
    source_archive_sha256: str
    dependency_lock_sha256: str
    closure_pipe_frame_sha256: str
    bootstrap_source_sha256: str
    pinned_runtime_capture_profile_sha256: str
    loaded_runtime_capture_profile_sha256: str
    runtime_execution_path_binding_sha256: str
    interpreter_observation_sha256: str
    argv_sha256: str
    spawn_environment_sha256: str
    response_frame_sha256: str
    source_load_report_sha256: str
    adapted_evidence_bundle_sha256: str
    independent_verification_receipt_sha256: str
    adapter_id: str
    adapter_version: str
    child_process_id: int
    elapsed_nanoseconds: int
    request_frame_byte_count: int
    closure_pipe_frame_byte_count: int
    response_frame_byte_count: int
    stderr_byte_count: int
    loaded_project_module_count: int
    pinned_runtime_capture_profile_module_count: int
    adapted_evidence_bundle_byte_count: int
    child_reported_adapt_complete_call_count: int
    child_reported_adapt_call_count: int
    artifact_type: str = field(
        default=SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    status_id: str = field(
        default=SOURCE_BOUND_ADAPTER_CHILD_RUN_STATUS,
        init=False,
    )
    decision_status: str = field(
        default=SOURCE_BOUND_ADAPTER_CHILD_RUN_DECISION_STATUS,
        init=False,
    )
    supplied_archive_revalidated: bool = field(default=True, init=False)
    implementation_closure_reconstructed: bool = field(
        default=True, init=False
    )
    entrypoint_bound_to_adapter_id_version: bool = field(
        default=True, init=False
    )
    protected_project_namespace_host_fallback_denial_configured: bool = field(
        default=True, init=False
    )
    preoutput_only_request_schema_validated: bool = field(
        default=True, init=False
    )
    caller_complete_sample_parameter_absent: bool = field(
        default=True, init=False
    )
    one_fresh_child_process_per_case_locally_observed: bool = field(
        default=True, init=False
    )
    success_response_identity_matched: bool = field(
        default=True, init=False
    )
    pinned_runtime_capture_profile_matched_before_spawn: bool = field(
        default=True, init=False
    )
    child_source_report_matched_pinned_runtime_profile: bool = field(
        default=True, init=False
    )
    child_response_reported_direct_call_counts: bool = field(
        default=True, init=False
    )
    adapted_bundle_independently_verified: bool = field(
        default=True, init=False
    )
    defined_child_channels_have_no_expected_specific_fields: bool = field(
        default=True, init=False
    )
    decision_eligible: bool = field(default=False, init=False)
    guard_manifest_executed: bool = field(default=False, init=False)
    v2_or_guard_consumption_attested: bool = field(
        default=False, init=False
    )
    expected_material_nonexposure_attested: bool = field(
        default=False, init=False
    )
    information_flow_noninterference_attested: bool = field(
        default=False, init=False
    )
    containment_enforced: bool = field(default=False, init=False)
    containment_attested: bool = field(default=False, init=False)
    network_confinement_attested: bool = field(default=False, init=False)
    filesystem_confinement_attested: bool = field(
        default=False, init=False
    )
    process_tree_escape_prevented: bool = field(
        default=False, init=False
    )
    managed_descendant_quiescence_attested: bool = field(
        default=False, init=False
    )
    interpreter_dependency_identity_attested: bool = field(
        default=False, init=False
    )
    interpreter_executable_execution_identity_attested: bool = field(
        default=False, init=False
    )
    adapter_source_execution_identity_attested: bool = field(
        default=False, init=False
    )
    external_custody_authenticated: bool = field(
        default=False, init=False
    )
    actual_output_freshness_attested: bool = field(
        default=False, init=False
    )
    runtime_instruction_execution_attested: bool = field(
        default=False, init=False
    )
    same_process_runtime_mutation_prevented: bool = field(
        default=False, init=False
    )
    protected_namespace_host_fallback_absence_attested: bool = field(
        default=False, init=False
    )
    current_child_method_return_capture_attested: bool = field(
        default=False, init=False
    )
    bootstrap_proxy_call_counts_attested: bool = field(
        default=False, init=False
    )
    loaded_runtime_profile_execution_attested: bool = field(
        default=False, init=False
    )
    recursive_internal_call_counts_observed: bool = field(
        default=False, init=False
    )
    argument_consumption_attested: bool = field(
        default=False, init=False
    )
    semantic_truth_attested: bool = field(default=False, init=False)
    publication_artifacts_rebuilt: bool = field(
        default=False, init=False
    )
    decision_made: bool = field(default=False, init=False)
    generalization_attested: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self) is not SourceBoundAdapterChildRunReceiptV1:
            raise TypeError("source-bound child receipt must be exact")
        digest_names = (
            "run_input_sha256",
            "request_frame_sha256",
            "case_input_sha256",
            "implementation_closure_sha256",
            "implementation_closure_validation_receipt_sha256",
            "source_archive_inventory_sha256",
            "source_archive_sha256",
            "dependency_lock_sha256",
            "closure_pipe_frame_sha256",
            "bootstrap_source_sha256",
            "pinned_runtime_capture_profile_sha256",
            "loaded_runtime_capture_profile_sha256",
            "runtime_execution_path_binding_sha256",
            "interpreter_observation_sha256",
            "argv_sha256",
            "spawn_environment_sha256",
            "response_frame_sha256",
            "source_load_report_sha256",
            "adapted_evidence_bundle_sha256",
            "independent_verification_receipt_sha256",
        )
        if any(
            type(getattr(self, name)) is not str
            or _SHA256_RE.fullmatch(getattr(self, name)) is None
            for name in digest_names
        ):
            raise ValueError("receipt digest is invalid")
        if (
            type(self.adapter_id) is not str
            or not self.adapter_id
            or type(self.adapter_version) is not str
            or not self.adapter_version
        ):
            raise TypeError("receipt adapter identity is invalid")
        positive_names = (
            "child_process_id",
            "request_frame_byte_count",
            "closure_pipe_frame_byte_count",
            "response_frame_byte_count",
            "loaded_project_module_count",
            "pinned_runtime_capture_profile_module_count",
            "adapted_evidence_bundle_byte_count",
        )
        if any(
            type(getattr(self, name)) is not int
            or getattr(self, name) <= 0
            for name in positive_names
        ):
            raise ValueError("receipt positive count is invalid")
        if (
            type(self.elapsed_nanoseconds) is not int
            or self.elapsed_nanoseconds < 0
            or type(self.stderr_byte_count) is not int
            or self.stderr_byte_count != 0
            or self.child_reported_adapt_complete_call_count != 1
            or type(self.child_reported_adapt_complete_call_count)
            is not int
            or self.child_reported_adapt_call_count != 0
            or type(self.child_reported_adapt_call_count) is not int
        ):
            raise ValueError("receipt execution count is invalid")
        if (
            self.artifact_type
            != SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE
            or self.format_version != "1"
            or self.status_id != SOURCE_BOUND_ADAPTER_CHILD_RUN_STATUS
            or self.decision_status
            != SOURCE_BOUND_ADAPTER_CHILD_RUN_DECISION_STATUS
            or self.bootstrap_source_sha256
            != OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256
            or self.pinned_runtime_capture_profile_sha256
            != OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256
            or self.loaded_runtime_capture_profile_sha256
            != self.pinned_runtime_capture_profile_sha256
            or self.pinned_runtime_capture_profile_module_count
            != len(OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES)
            or self.loaded_project_module_count
            < len(OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES)
            or self.spawn_environment_sha256
            != _length_framed_sha256(
                "heterodiff.adapter.empty-spawn-environment.v1",
                (),
            )
            or self.runtime_execution_path_binding_sha256
            != _runtime_execution_path_binding_from_digests(
                bootstrap_source_sha256=self.bootstrap_source_sha256,
                dependency_lock_sha256=self.dependency_lock_sha256,
                implementation_closure_sha256=(
                    self.implementation_closure_sha256
                ),
                request_frame_sha256=self.request_frame_sha256,
                runtime_capture_profile_sha256=(
                    self.pinned_runtime_capture_profile_sha256
                ),
            )
        ):
            raise ValueError("receipt fixed execution binding differs")
        true_names = (
            "supplied_archive_revalidated",
            "implementation_closure_reconstructed",
            "entrypoint_bound_to_adapter_id_version",
            "protected_project_namespace_host_fallback_denial_configured",
            "preoutput_only_request_schema_validated",
            "caller_complete_sample_parameter_absent",
            "one_fresh_child_process_per_case_locally_observed",
            "success_response_identity_matched",
            "pinned_runtime_capture_profile_matched_before_spawn",
            "child_source_report_matched_pinned_runtime_profile",
            "child_response_reported_direct_call_counts",
            "adapted_bundle_independently_verified",
            "defined_child_channels_have_no_expected_specific_fields",
        )
        false_names = (
            "decision_eligible",
            "guard_manifest_executed",
            "v2_or_guard_consumption_attested",
            "expected_material_nonexposure_attested",
            "information_flow_noninterference_attested",
            "containment_enforced",
            "containment_attested",
            "network_confinement_attested",
            "filesystem_confinement_attested",
            "process_tree_escape_prevented",
            "managed_descendant_quiescence_attested",
            "interpreter_dependency_identity_attested",
            "interpreter_executable_execution_identity_attested",
            "adapter_source_execution_identity_attested",
            "external_custody_authenticated",
            "actual_output_freshness_attested",
            "runtime_instruction_execution_attested",
            "same_process_runtime_mutation_prevented",
            "protected_namespace_host_fallback_absence_attested",
            "current_child_method_return_capture_attested",
            "bootstrap_proxy_call_counts_attested",
            "loaded_runtime_profile_execution_attested",
            "recursive_internal_call_counts_observed",
            "argument_consumption_attested",
            "semantic_truth_attested",
            "publication_artifacts_rebuilt",
            "decision_made",
            "generalization_attested",
        )
        if any(getattr(self, name) is not True for name in true_names):
            raise ValueError("receipt narrow claim was weakened")
        if any(getattr(self, name) is not False for name in false_names):
            raise ValueError("receipt strong nonclaim was upgraded")


class SourceBoundAdapterChildRunResultV1(NamedTuple):
    """Accepted actual-side result; expected comparison remains downstream."""

    receipt: SourceBoundAdapterChildRunReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str
    request_frame_bytes: bytes
    response_frame_bytes: bytes
    validated_child_success: ValidatedOutputBlindAdapterChildSuccessV1
    actual_verification_input: (
        _verifier.IndependentAdaptedEvidenceBundleVerificationInputV1
    )
    actual_verification_result: (
        _verifier.IndependentAdaptedEvidenceBundleVerificationResultV1
    )


@dataclass(frozen=True)
class _InterpreterSnapshot:
    path: str
    resolved_path: str
    invocation_identity: Tuple[int, int, int, int, int, int]
    identity: Tuple[int, int, int, int, int, int]
    executable_sha256: str
    observation_sha256: str


@dataclass(frozen=True)
class _PreparedRun:
    input: SourceBoundAdapterChildRunInputV1
    closure_value: object
    closure_tree: dict
    implementation_closure_sha256: str
    request_frame_bytes: bytes
    closure_pipe_frame_bytes: bytes
    interpreter: _InterpreterSnapshot
    run_input_sha256: str


@dataclass(frozen=True)
class _ProcessObservation:
    process_id: int
    returncode: int
    elapsed_nanoseconds: int
    request_written_byte_count: int
    request_complete: bool
    closure_written_byte_count: int
    closure_complete: bool
    stdout_bytes: bytes
    stdout_complete: bool
    stderr_bytes: bytes
    stderr_complete: bool
    output_limit_code: Optional[SourceBoundAdapterChildRunCode]
    wall_limit_triggered: bool
    process_group_nonquiescent: bool


def _domain_sha256(domain: str, raw: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii", "strict"))
    digest.update(b"\x00")
    digest.update(len(raw).to_bytes(8, "big"))
    digest.update(raw)
    return digest.hexdigest()


def _canonical_bytes(value: object, *, maximum: int) -> bytes:
    try:
        raw = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        _fail(SourceBoundAdapterChildRunCode.RECEIPT_INVALID)
    if not raw or len(raw) > maximum:
        _fail(SourceBoundAdapterChildRunCode.RECEIPT_INVALID)
    return raw


def _length_framed_sha256(domain: str, values: Tuple[bytes, ...]) -> str:
    digest = hashlib.sha256()
    domain_bytes = domain.encode("ascii", "strict")
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        if type(value) is not bytes:
            _fail(SourceBoundAdapterChildRunCode.INTERNAL)
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def _reason_registry_bytes(value: Tuple[str, ...]) -> bytes:
    try:
        raw = json.dumps(
            list(value),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        _fail(SourceBoundAdapterChildRunCode.INPUT_TYPE)
    if not raw or len(raw) > MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES:
        _fail(SourceBoundAdapterChildRunCode.INPUT_RESOURCE)
    return raw


def source_bound_adapter_child_run_receipt_bytes(
    value: SourceBoundAdapterChildRunReceiptV1,
) -> bytes:
    """Return exact canonical bytes for the nondecision local transcript."""

    if type(value) is not SourceBoundAdapterChildRunReceiptV1:
        _fail(SourceBoundAdapterChildRunCode.RECEIPT_INVALID)
    try:
        SourceBoundAdapterChildRunReceiptV1.__post_init__(value)
        tree = {item.name: getattr(value, item.name) for item in fields(value)}
    except (AttributeError, TypeError, ValueError):
        _fail(SourceBoundAdapterChildRunCode.RECEIPT_INVALID)
    return _canonical_bytes(tree, maximum=MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES)


def source_bound_adapter_child_run_receipt_sha256(
    value: SourceBoundAdapterChildRunReceiptV1,
) -> str:
    return _domain_sha256(
        SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_DIGEST_DOMAIN,
        source_bound_adapter_child_run_receipt_bytes(value),
    )


def _snapshot_input(
    value: SourceBoundAdapterChildRunInputV1,
) -> SourceBoundAdapterChildRunInputV1:
    if type(value) is not SourceBoundAdapterChildRunInputV1:
        _fail(SourceBoundAdapterChildRunCode.INPUT_TYPE)
    try:
        SourceBoundAdapterChildRunInputV1.__post_init__(value)
        return SourceBoundAdapterChildRunInputV1(
            case_input_bytes=bytes(value.case_input_bytes),
            implementation_closure_bytes=bytes(
                value.implementation_closure_bytes
            ),
            source_archive_inventory_bytes=bytes(
                value.source_archive_inventory_bytes
            ),
            source_archive_bytes=bytes(value.source_archive_bytes),
            dependency_lock_bytes=bytes(value.dependency_lock_bytes),
            interpreter_path=value.interpreter_path,
            allowed_exclusion_reason_codes=tuple(
                value.allowed_exclusion_reason_codes
            ),
            allowed_censor_reason_codes=tuple(
                value.allowed_censor_reason_codes
            ),
        )
    except SourceBoundAdapterChildRunError:
        raise
    except (AttributeError, TypeError):
        _fail(SourceBoundAdapterChildRunCode.INPUT_TYPE)
    except ValueError:
        _fail(SourceBoundAdapterChildRunCode.INPUT_RESOURCE)


def _capture_interpreter(path: str) -> _InterpreterSnapshot:
    try:
        if not os.path.isabs(path):
            raise ValueError()
        invocation = os.path.abspath(path)
        invocation_status = os.lstat(invocation)
        if not (
            stat.S_ISREG(invocation_status.st_mode)
            or stat.S_ISLNK(invocation_status.st_mode)
        ):
            raise ValueError()
        resolved = os.path.realpath(invocation)
        status = os.stat(resolved, follow_symlinks=False)
        if (
            not os.path.isabs(resolved)
            or not stat.S_ISREG(status.st_mode)
            or not os.access(invocation, os.X_OK)
            or status.st_size <= 0
            or status.st_size > MAXIMUM_SOURCE_BOUND_INTERPRETER_BYTES
        ):
            raise ValueError()
        with open(resolved, "rb", buffering=0) as stream:
            opened_status = os.fstat(stream.fileno())
            if (
                opened_status.st_dev != status.st_dev
                or opened_status.st_ino != status.st_ino
                or opened_status.st_mode != status.st_mode
                or opened_status.st_size != status.st_size
                or opened_status.st_mtime_ns != status.st_mtime_ns
                or opened_status.st_ctime_ns != status.st_ctime_ns
            ):
                raise ValueError()
            executable = stream.read(MAXIMUM_SOURCE_BOUND_INTERPRETER_BYTES + 1)
            final_opened_status = os.fstat(stream.fileno())
        if len(executable) != status.st_size:
            raise ValueError()
        invocation_identity = (
            invocation_status.st_dev,
            invocation_status.st_ino,
            invocation_status.st_mode,
            invocation_status.st_size,
            invocation_status.st_mtime_ns,
            invocation_status.st_ctime_ns,
        )
        identity = (
            status.st_dev,
            status.st_ino,
            status.st_mode,
            status.st_size,
            status.st_mtime_ns,
            status.st_ctime_ns,
        )
        executable_sha256 = hashlib.sha256(executable).hexdigest()
        if (
            final_opened_status.st_dev,
            final_opened_status.st_ino,
            final_opened_status.st_mode,
            final_opened_status.st_size,
            final_opened_status.st_mtime_ns,
            final_opened_status.st_ctime_ns,
        ) != identity:
            raise ValueError()
        observation = _length_framed_sha256(
            "heterodiff.adapter.interpreter-observation.v1",
            (
                invocation.encode("utf-8", "strict"),
                repr(invocation_identity).encode("ascii", "strict"),
                resolved.encode("utf-8", "strict"),
                repr(identity).encode("ascii", "strict"),
                executable_sha256.encode("ascii"),
            ),
        )
        return _InterpreterSnapshot(
            path=invocation,
            resolved_path=resolved,
            invocation_identity=invocation_identity,
            identity=identity,
            executable_sha256=executable_sha256,
            observation_sha256=observation,
        )
    except (OSError, TypeError, UnicodeError, ValueError):
        _fail(SourceBoundAdapterChildRunCode.INTERPRETER_INVALID)


def _verify_interpreter(value: _InterpreterSnapshot) -> None:
    try:
        invocation_status = os.lstat(value.path)
        invocation_identity = (
            invocation_status.st_dev,
            invocation_status.st_ino,
            invocation_status.st_mode,
            invocation_status.st_size,
            invocation_status.st_mtime_ns,
            invocation_status.st_ctime_ns,
        )
        resolved = os.path.realpath(value.path)
        with open(resolved, "rb", buffering=0) as stream:
            status = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(status.st_mode)
                or status.st_size <= 0
                or status.st_size
                > MAXIMUM_SOURCE_BOUND_INTERPRETER_BYTES
            ):
                raise ValueError()
            identity = (
                status.st_dev,
                status.st_ino,
                status.st_mode,
                status.st_size,
                status.st_mtime_ns,
                status.st_ctime_ns,
            )
            executable = stream.read(
                MAXIMUM_SOURCE_BOUND_INTERPRETER_BYTES + 1
            )
            final_status = os.fstat(stream.fileno())
        final_identity = (
            final_status.st_dev,
            final_status.st_ino,
            final_status.st_mode,
            final_status.st_size,
            final_status.st_mtime_ns,
            final_status.st_ctime_ns,
        )
    except (OSError, ValueError):
        _fail(SourceBoundAdapterChildRunCode.INTERPRETER_INVALID)
    if (
        invocation_identity != value.invocation_identity
        or resolved != value.resolved_path
        or identity != value.identity
        or final_identity != value.identity
        or len(executable) != value.identity[3]
        or hashlib.sha256(executable).hexdigest()
        != value.executable_sha256
        or not os.access(value.path, os.X_OK)
    ):
        _fail(SourceBoundAdapterChildRunCode.INTERPRETER_INVALID)


def _closure_tree(value: object) -> dict:
    try:
        tree = _closure.adapter_implementation_closure_tree(value)
    except Exception:
        _fail(SourceBoundAdapterChildRunCode.CLOSURE_INVALID)
    if type(tree) is not dict:
        _fail(SourceBoundAdapterChildRunCode.CLOSURE_INVALID)
    return tree


def _validate_trusted_runtime_profile(
    value: _closure.ValidatedAdapterImplementationClosureV1,
) -> None:
    closure = value.closure
    if (
        closure.runtime_entry_point.module_name
        != OUTPUT_BLIND_TRUSTED_RUNTIME_MODULE_NAME
        or closure.runtime_entry_point.callable_name
        != OUTPUT_BLIND_TRUSTED_RUNTIME_CALLABLE_NAME
    ):
        _fail(
            SourceBoundAdapterChildRunCode.TRUSTED_RUNTIME_PROFILE_MISMATCH
        )
    observed = {item.module.module_name: item for item in value.modules}
    expected_names = frozenset(
        item.module_name
        for item in OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES
    )
    for expected in OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES:
        selected = observed.get(expected.module_name)
        if (
            selected is None
            or selected.module.is_package is not expected.is_package
            or selected.module.role_id != expected.role_id
            or selected.module.source_byte_count
            != expected.source_byte_count
            or selected.module.source_object_id
            != expected.source_object_id
            or selected.module.source_sha256 != expected.source_sha256
            or len(selected.source_bytes) != expected.source_byte_count
            or hashlib.sha256(selected.source_bytes).hexdigest()
            != expected.source_sha256
        ):
            _fail(
                SourceBoundAdapterChildRunCode.TRUSTED_RUNTIME_PROFILE_MISMATCH
            )
        if any(
            (
                imported == "heterodiff"
                or imported.startswith("heterodiff.")
            )
            and imported not in expected_names
            for imported in selected.imported_module_names
        ):
            _fail(
                SourceBoundAdapterChildRunCode.TRUSTED_RUNTIME_PROFILE_MISMATCH
            )


def _prepare_run(value: SourceBoundAdapterChildRunInputV1) -> _PreparedRun:
    run_input = _snapshot_input(value)
    try:
        parse_output_blind_case_input_v1(run_input.case_input_bytes)
    except Exception:
        _fail(SourceBoundAdapterChildRunCode.CASE_INPUT_INVALID)
    try:
        exclusions = _evidence._validate_reason_codes(
            run_input.allowed_exclusion_reason_codes,
            name="allowed exclusion reason",
        )
        censors = _evidence._validate_reason_codes(
            run_input.allowed_censor_reason_codes,
            name="allowed censor reason",
        )
        if len(exclusions) + len(censors) > _evidence.MAXIMUM_REASON_CODES:
            raise ValueError()
        run_input = SourceBoundAdapterChildRunInputV1(
            case_input_bytes=run_input.case_input_bytes,
            implementation_closure_bytes=(
                run_input.implementation_closure_bytes
            ),
            source_archive_inventory_bytes=(
                run_input.source_archive_inventory_bytes
            ),
            source_archive_bytes=run_input.source_archive_bytes,
            dependency_lock_bytes=run_input.dependency_lock_bytes,
            interpreter_path=run_input.interpreter_path,
            allowed_exclusion_reason_codes=exclusions,
            allowed_censor_reason_codes=censors,
        )
    except (TypeError, ValueError):
        _fail(SourceBoundAdapterChildRunCode.INPUT_TYPE)
    try:
        validated = _closure.validate_adapter_implementation_closure(
            run_input.implementation_closure_bytes,
            source_archive_inventory_bytes=(
                run_input.source_archive_inventory_bytes
            ),
            source_archive_bytes=run_input.source_archive_bytes,
            dependency_lock_bytes=run_input.dependency_lock_bytes,
        )
    except _closure.ImplementationClosureError as error:
        if error.code in (
            _closure.ImplementationClosureCode.ARCHIVE.value,
            _closure.ImplementationClosureCode.ARCHIVE_MEMBERSHIP.value,
        ):
            _fail(SourceBoundAdapterChildRunCode.ARCHIVE_INVALID)
        if error.code == _closure.ImplementationClosureCode.ENTRY_POINT.value:
            _fail(SourceBoundAdapterChildRunCode.ENTRYPOINT_INVALID)
        if error.code in (
            _closure.ImplementationClosureCode.IMPORT_POLICY.value,
            _closure.ImplementationClosureCode.NAME_POLICY.value,
            _closure.ImplementationClosureCode.PACKAGE_CLOSURE.value,
        ):
            _fail(SourceBoundAdapterChildRunCode.IMPORT_POLICY_INVALID)
        _fail(SourceBoundAdapterChildRunCode.CLOSURE_INVALID)
    except Exception:
        _fail(SourceBoundAdapterChildRunCode.CLOSURE_INVALID)
    tree = _closure_tree(validated.closure)
    if tree.get("protected_namespace_roots") != ["heterodiff"]:
        _fail(SourceBoundAdapterChildRunCode.IMPORT_POLICY_INVALID)
    _validate_trusted_runtime_profile(validated)
    closure_sha256 = validated.closure_sha256
    try:
        request = OutputBlindAdapterChildRequestV1(
            case_input_bytes=run_input.case_input_bytes
        )
        request_frame = build_output_blind_adapter_child_request_frame(request)
    except Exception:
        _fail(SourceBoundAdapterChildRunCode.REQUEST_INVALID)
    try:
        closure_pipe = (
            build_output_blind_implementation_closure_pipe_frame(
                run_input.implementation_closure_bytes,
                run_input.source_archive_inventory_bytes,
                run_input.source_archive_bytes,
            )
        )
    except (TypeError, ValueError):
        _fail(SourceBoundAdapterChildRunCode.INPUT_RESOURCE)
    interpreter = _capture_interpreter(run_input.interpreter_path)
    run_input_sha256 = _length_framed_sha256(
        "heterodiff.adapter.source-bound-child-run-input.v1",
        (
            run_input.case_input_bytes,
            run_input.implementation_closure_bytes,
            run_input.source_archive_inventory_bytes,
            run_input.source_archive_bytes,
            run_input.dependency_lock_bytes,
            interpreter.observation_sha256.encode("ascii"),
            hashlib.sha256(request_frame).hexdigest().encode("ascii"),
            hashlib.sha256(closure_pipe).hexdigest().encode("ascii"),
            OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256.encode(
                "ascii"
            ),
            OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256.encode("ascii"),
            _reason_registry_bytes(
                run_input.allowed_exclusion_reason_codes
            ),
            _reason_registry_bytes(
                run_input.allowed_censor_reason_codes
            ),
        ),
    )
    return _PreparedRun(
        input=run_input,
        closure_value=validated,
        closure_tree=tree,
        implementation_closure_sha256=closure_sha256,
        request_frame_bytes=request_frame,
        closure_pipe_frame_bytes=closure_pipe,
        interpreter=interpreter,
        run_input_sha256=run_input_sha256,
    )


def _clock_ns() -> int:
    try:
        value = time.monotonic_ns()
    except Exception:
        _fail(SourceBoundAdapterChildRunCode.CLOCK_INVALID)
    if type(value) is not int or value < 0:
        _fail(SourceBoundAdapterChildRunCode.CLOCK_INVALID)
    return value


def _process_group_empty(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    except OSError:
        return False
    return False


def _terminate_process_group(process: subprocess.Popen) -> bool:
    if type(process.pid) is not int or process.pid <= 0:
        return False
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError:
        pass
    deadline = time.monotonic() + _TERMINATION_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None and _process_group_empty(process.pid):
            return True
        time.sleep(0.01)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        pass
    try:
        process.wait(timeout=_TERMINATION_SECONDS)
    except (subprocess.SubprocessError, OSError):
        return False
    return process.poll() is not None and _process_group_empty(process.pid)


def _cleanup_process_group_or_fail(process: subprocess.Popen) -> None:
    if type(process.pid) is not int or process.pid <= 0:
        _fail(SourceBoundAdapterChildRunCode.PROCESS_GROUP_NONQUIESCENCE)
    if process.poll() is None or not _process_group_empty(process.pid):
        if not _terminate_process_group(process):
            _fail(
                SourceBoundAdapterChildRunCode.PROCESS_GROUP_NONQUIESCENCE
            )


def _close_selector_file(
    selector: selectors.BaseSelector,
    stream: object,
) -> None:
    try:
        selector.unregister(stream)
    except (KeyError, ValueError):
        pass
    try:
        stream.close()
    except OSError:
        pass


def _run_duplex(prepared: _PreparedRun) -> _ProcessObservation:
    if os.name != "posix":
        _fail(SourceBoundAdapterChildRunCode.PLATFORM_UNAVAILABLE)
    selector = selectors.DefaultSelector()
    process = None
    closure_read_fd = -1
    closure_write_fd = -1
    stdout = bytearray()
    stderr = bytearray()
    request_written = 0
    closure_written = 0
    request_complete = False
    closure_complete = False
    stdout_complete = False
    stderr_complete = False
    output_limit_code = None
    wall_limit_triggered = False
    group_nonquiescent = False
    termination_failed = False
    start = _clock_ns()
    try:
        _verify_interpreter(prepared.interpreter)
        try:
            closure_read_fd, closure_write_fd = os.pipe()
            os.set_inheritable(closure_read_fd, True)
            os.set_blocking(closure_write_fd, False)
            bootstrap_text = (
                OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_BYTES.decode(
                    "utf-8", "strict"
                )
            )
            argv = (
                prepared.interpreter.path,
                "-I",
                "-B",
                "-c",
                bootstrap_text,
                str(closure_read_fd),
            )
            working_directory = os.path.realpath(tempfile.gettempdir())
            process = subprocess.Popen(
                argv,
                cwd=working_directory,
                env={},
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                close_fds=True,
                pass_fds=(closure_read_fd,),
                shell=False,
                start_new_session=True,
            )
        except (OSError, TypeError, UnicodeError, ValueError):
            _fail(SourceBoundAdapterChildRunCode.SPAWN_FAILED)
        try:
            os.close(closure_read_fd)
        except OSError:
            pass
        closure_read_fd = -1
        if (
            process.stdin is None
            or process.stdout is None
            or process.stderr is None
            or type(process.pid) is not int
            or process.pid <= 0
        ):
            _fail(SourceBoundAdapterChildRunCode.PROCESS_PROTOCOL_INVALID)
        for stream in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
        selector.register(process.stdin, selectors.EVENT_WRITE, "request")
        selector.register(closure_write_fd, selectors.EVENT_WRITE, "closure")
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        forced = False
        while True:
            now = _clock_ns()
            if now < start:
                _fail(SourceBoundAdapterChildRunCode.CLOCK_INVALID)
            elapsed = now - start
            returncode = process.poll()
            if (
                not forced
                and elapsed >= SOURCE_BOUND_CHILD_WALL_TIME_LIMIT_NANOSECONDS
            ):
                wall_limit_triggered = True
                forced = True
                termination_failed = not _terminate_process_group(process)
            if forced:
                break
            if (
                returncode is not None
                and stdout_complete
                and stderr_complete
            ):
                break
            if forced and process.poll() is not None:
                break
            try:
                events = selector.select(_POLL_SECONDS)
            except (OSError, ValueError):
                _fail(
                    SourceBoundAdapterChildRunCode.PROCESS_PROTOCOL_INVALID
                )
            for key, mask in events:
                if key.data in ("request", "closure"):
                    if not (mask & selectors.EVENT_WRITE):
                        continue
                    if key.data == "request":
                        stream = key.fileobj
                        raw = prepared.request_frame_bytes
                        offset = request_written
                    else:
                        stream = key.fileobj
                        raw = prepared.closure_pipe_frame_bytes
                        offset = closure_written
                    remaining = raw[offset:]
                    if not remaining:
                        if key.data == "request":
                            request_complete = True
                            _close_selector_file(selector, stream)
                        else:
                            closure_complete = True
                            try:
                                selector.unregister(stream)
                            except (KeyError, ValueError):
                                pass
                            try:
                                os.close(stream)
                            except OSError:
                                pass
                            closure_write_fd = -1
                        continue
                    try:
                        count = os.write(
                            (
                                stream.fileno()
                                if key.data == "request"
                                else stream
                            ),
                            remaining[:SOURCE_BOUND_CHILD_WRITE_CHUNK_BYTES],
                        )
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        if key.data == "request":
                            _close_selector_file(selector, stream)
                        else:
                            try:
                                selector.unregister(stream)
                            except (KeyError, ValueError):
                                pass
                            try:
                                os.close(stream)
                            except OSError:
                                pass
                            closure_write_fd = -1
                        continue
                    except OSError as error:
                        if error.errno in (errno.EAGAIN, errno.EINTR):
                            continue
                        _fail(
                            SourceBoundAdapterChildRunCode
                            .PROCESS_PROTOCOL_INVALID
                        )
                    if type(count) is not int or count <= 0:
                        _fail(
                            SourceBoundAdapterChildRunCode
                            .PROCESS_PROTOCOL_INVALID
                        )
                    if key.data == "request":
                        request_written += count
                        if request_written == len(raw):
                            request_complete = True
                            _close_selector_file(selector, stream)
                    else:
                        closure_written += count
                        if closure_written == len(raw):
                            closure_complete = True
                            try:
                                selector.unregister(stream)
                            except (KeyError, ValueError):
                                pass
                            try:
                                os.close(stream)
                            except OSError:
                                pass
                            closure_write_fd = -1
                    continue
                if not (mask & selectors.EVENT_READ):
                    continue
                stream = key.fileobj
                try:
                    chunk = os.read(
                        stream.fileno(),
                        SOURCE_BOUND_CHILD_READ_CHUNK_BYTES,
                    )
                except BlockingIOError:
                    continue
                except OSError as error:
                    if error.errno in (errno.EAGAIN, errno.EINTR):
                        continue
                    _fail(
                        SourceBoundAdapterChildRunCode
                        .PROCESS_PROTOCOL_INVALID
                    )
                if not chunk:
                    _close_selector_file(selector, stream)
                    if key.data == "stdout":
                        stdout_complete = True
                    else:
                        stderr_complete = True
                    continue
                target = stdout if key.data == "stdout" else stderr
                stream_limit = (
                    MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES
                    if key.data == "stdout"
                    else MAXIMUM_SOURCE_BOUND_STDERR_BYTES
                )
                aggregate_remaining = (
                    MAXIMUM_SOURCE_BOUND_AGGREGATE_OUTPUT_BYTES
                    - len(stdout)
                    - len(stderr)
                )
                stream_remaining = stream_limit - len(target)
                admitted = min(
                    len(chunk),
                    max(0, stream_remaining),
                    max(0, aggregate_remaining),
                )
                target.extend(chunk[:admitted])
                if admitted != len(chunk) and output_limit_code is None:
                    if aggregate_remaining <= stream_remaining:
                        output_limit_code = (
                            SourceBoundAdapterChildRunCode
                            .AGGREGATE_OUTPUT_LIMIT
                        )
                    elif key.data == "stdout":
                        output_limit_code = (
                            SourceBoundAdapterChildRunCode.STDOUT_LIMIT
                        )
                    else:
                        output_limit_code = (
                            SourceBoundAdapterChildRunCode.STDERR_LIMIT
                        )
                    forced = True
                    termination_failed = not _terminate_process_group(process)
            if forced:
                break
            if process.poll() is not None and not (
                stdout_complete and stderr_complete
            ):
                continue
        if process.poll() is None:
            termination_failed = not _terminate_process_group(process)
            if termination_failed and process.poll() is None:
                _fail(
                    SourceBoundAdapterChildRunCode
                    .PROCESS_GROUP_NONQUIESCENCE
                )
        try:
            returncode = process.wait(timeout=_TERMINATION_SECONDS)
        except (OSError, subprocess.SubprocessError):
            _fail(SourceBoundAdapterChildRunCode.PROCESS_PROTOCOL_INVALID)
        if not _process_group_empty(process.pid):
            group_nonquiescent = True
            if not _terminate_process_group(process):
                _fail(
                    SourceBoundAdapterChildRunCode
                    .PROCESS_GROUP_NONQUIESCENCE
                )
        end = _clock_ns()
        if end < start:
            _fail(SourceBoundAdapterChildRunCode.CLOCK_INVALID)
        return _ProcessObservation(
            process_id=process.pid,
            returncode=returncode,
            elapsed_nanoseconds=end - start,
            request_written_byte_count=request_written,
            request_complete=request_complete,
            closure_written_byte_count=closure_written,
            closure_complete=closure_complete,
            stdout_bytes=bytes(stdout),
            stdout_complete=stdout_complete,
            stderr_bytes=bytes(stderr),
            stderr_complete=stderr_complete,
            output_limit_code=output_limit_code,
            wall_limit_triggered=wall_limit_triggered,
            process_group_nonquiescent=group_nonquiescent,
        )
    except SourceBoundAdapterChildRunError:
        if process is not None:
            _cleanup_process_group_or_fail(process)
        raise
    except Exception:
        if process is not None:
            _cleanup_process_group_or_fail(process)
        _fail(SourceBoundAdapterChildRunCode.PROCESS_PROTOCOL_INVALID)
    except BaseException:
        if process is not None:
            _cleanup_process_group_or_fail(process)
        raise
    finally:
        try:
            selector.close()
        except Exception:
            pass
        if closure_read_fd >= 0:
            try:
                os.close(closure_read_fd)
            except OSError:
                pass
        if closure_write_fd >= 0:
            try:
                os.close(closure_write_fd)
            except OSError:
                pass
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    try:
                        stream.close()
                    except OSError:
                        pass


def _check_observation(value: _ProcessObservation) -> None:
    if value.wall_limit_triggered:
        _fail(SourceBoundAdapterChildRunCode.WALL_TIME_LIMIT)
    if value.output_limit_code is not None:
        _fail(value.output_limit_code)
    if value.process_group_nonquiescent:
        _fail(SourceBoundAdapterChildRunCode.PROCESS_GROUP_NONQUIESCENCE)
    if (
        not value.request_complete
        or not value.closure_complete
        or value.request_written_byte_count <= 0
        or value.closure_written_byte_count <= 0
    ):
        _fail(SourceBoundAdapterChildRunCode.PARTIAL_INPUT)
    if value.returncode < 0:
        _fail(SourceBoundAdapterChildRunCode.SIGNAL_EXIT)
    if value.returncode != 0:
        _fail(SourceBoundAdapterChildRunCode.NONZERO_EXIT)
    if not value.stdout_complete or not value.stderr_complete:
        _fail(SourceBoundAdapterChildRunCode.INCOMPLETE_OUTPUT)
    if value.stderr_bytes:
        _fail(SourceBoundAdapterChildRunCode.NONEMPTY_STDERR)
    if not value.stdout_bytes:
        _fail(SourceBoundAdapterChildRunCode.INCOMPLETE_OUTPUT)


def _validate_source_report(
    prepared: _PreparedRun,
    success: ValidatedOutputBlindAdapterChildSuccessV1,
) -> str:
    response = success.response
    report = success.source_load_report
    tree = prepared.closure_tree
    entry = tree["entry_point"]
    runtime = tree["runtime_entry_point"]
    if (
        response.adapter_id != tree["adapter_id"]
        or response.adapter_version != tree["adapter_version"]
        or report.entrypoint_module_name != entry["module_name"]
        or report.entrypoint_callable_name != entry["callable_name"]
        or report.protected_namespace_host_fallback_count != 0
    ):
        _fail(SourceBoundAdapterChildRunCode.SOURCE_LOAD_REPORT_MISMATCH)
    closure_modules = {
        item["module_name"]: item for item in tree["modules"]
    }
    loaded_names = tuple(
        item.module_name for item in report.loaded_project_modules
    )
    if (
        entry["module_name"] not in loaded_names
        or runtime["module_name"] not in loaded_names
        or any(
            item.module_name not in loaded_names
            for item in OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES
        )
    ):
        _fail(SourceBoundAdapterChildRunCode.SOURCE_LOAD_REPORT_MISMATCH)
    for item in report.loaded_project_modules:
        expected = closure_modules.get(item.module_name)
        if (
            expected is None
            or item.source_object_id != expected["source_object_id"]
            or item.source_byte_count != expected["source_byte_count"]
            or item.source_sha256 != expected["source_sha256"]
        ):
            _fail(
                SourceBoundAdapterChildRunCode.SOURCE_LOAD_REPORT_MISMATCH
            )
    loaded_by_name = {
        item.module_name: item for item in report.loaded_project_modules
    }
    try:
        joined_profile = tuple(
            TrustedRuntimeSourceModuleV1(
                module_name=expected.module_name,
                is_package=closure_modules[expected.module_name][
                    "is_package"
                ],
                role_id=closure_modules[expected.module_name]["role_id"],
                source_byte_count=loaded_by_name[
                    expected.module_name
                ].source_byte_count,
                source_object_id=loaded_by_name[
                    expected.module_name
                ].source_object_id,
                source_sha256=loaded_by_name[
                    expected.module_name
                ].source_sha256,
            )
            for expected in OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES
        )
        joined_sha256 = output_blind_runtime_capture_profile_sha256(
            joined_profile
        )
    except (KeyError, TypeError, ValueError):
        _fail(SourceBoundAdapterChildRunCode.SOURCE_LOAD_REPORT_MISMATCH)
    if joined_sha256 != OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256:
        _fail(SourceBoundAdapterChildRunCode.SOURCE_LOAD_REPORT_MISMATCH)
    return joined_sha256


def _argv_sha256(
    prepared: _PreparedRun,
    closure_fd_placeholder: str = "<inherited-closure-fd>",
) -> str:
    values = (
        prepared.interpreter.path,
        "-I",
        "-B",
        "-c",
        OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256,
        closure_fd_placeholder,
    )
    return _length_framed_sha256(
        "heterodiff.adapter.source-bound-child-argv.v1",
        tuple(value.encode("utf-8", "strict") for value in values),
    )


def _runtime_execution_path_binding_from_digests(
    *,
    bootstrap_source_sha256: str,
    dependency_lock_sha256: str,
    implementation_closure_sha256: str,
    request_frame_sha256: str,
    runtime_capture_profile_sha256: str,
) -> str:
    return _length_framed_sha256(
        "heterodiff.adapter.output-blind-runtime-execution-path-binding.v1",
        (
            bootstrap_source_sha256.encode("ascii"),
            dependency_lock_sha256.encode("ascii"),
            implementation_closure_sha256.encode("ascii"),
            request_frame_sha256.encode("ascii"),
            runtime_capture_profile_sha256.encode("ascii"),
        ),
    )


def _runtime_execution_path_binding_sha256(
    prepared: _PreparedRun,
) -> str:
    return _runtime_execution_path_binding_from_digests(
        bootstrap_source_sha256=(
            OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256
        ),
        dependency_lock_sha256=hashlib.sha256(
            prepared.input.dependency_lock_bytes
        ).hexdigest(),
        implementation_closure_sha256=(
            prepared.implementation_closure_sha256
        ),
        request_frame_sha256=hashlib.sha256(
            prepared.request_frame_bytes
        ).hexdigest(),
        runtime_capture_profile_sha256=(
            OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256
        ),
    )


def _run_receipt(
    prepared: _PreparedRun,
    observation: _ProcessObservation,
    success: ValidatedOutputBlindAdapterChildSuccessV1,
    loaded_runtime_capture_profile_sha256: str,
    verification: (
        _verifier.IndependentAdaptedEvidenceBundleVerificationResultV1
    ),
) -> SourceBoundAdapterChildRunReceiptV1:
    response = success.response
    report = success.source_load_report
    receipt = SourceBoundAdapterChildRunReceiptV1(
        run_input_sha256=prepared.run_input_sha256,
        request_frame_sha256=hashlib.sha256(
            prepared.request_frame_bytes
        ).hexdigest(),
        case_input_sha256=response.case_input_sha256,
        implementation_closure_sha256=(
            prepared.implementation_closure_sha256
        ),
        implementation_closure_validation_receipt_sha256=(
            prepared.closure_value.receipt_sha256
        ),
        source_archive_inventory_sha256=hashlib.sha256(
            prepared.input.source_archive_inventory_bytes
        ).hexdigest(),
        source_archive_sha256=hashlib.sha256(
            prepared.input.source_archive_bytes
        ).hexdigest(),
        dependency_lock_sha256=hashlib.sha256(
            prepared.input.dependency_lock_bytes
        ).hexdigest(),
        closure_pipe_frame_sha256=hashlib.sha256(
            prepared.closure_pipe_frame_bytes
        ).hexdigest(),
        bootstrap_source_sha256=(
            OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256
        ),
        pinned_runtime_capture_profile_sha256=(
            OUTPUT_BLIND_TRUSTED_RUNTIME_PROFILE_SHA256
        ),
        loaded_runtime_capture_profile_sha256=(
            loaded_runtime_capture_profile_sha256
        ),
        runtime_execution_path_binding_sha256=(
            _runtime_execution_path_binding_sha256(prepared)
        ),
        interpreter_observation_sha256=(
            prepared.interpreter.observation_sha256
        ),
        argv_sha256=_argv_sha256(prepared),
        spawn_environment_sha256=_length_framed_sha256(
            "heterodiff.adapter.empty-spawn-environment.v1",
            (),
        ),
        response_frame_sha256=hashlib.sha256(
            observation.stdout_bytes
        ).hexdigest(),
        source_load_report_sha256=hashlib.sha256(
            response.source_load_report_bytes
        ).hexdigest(),
        adapted_evidence_bundle_sha256=(
            verification.receipt.adapted_evidence_bundle_sha256
        ),
        independent_verification_receipt_sha256=(
            verification.receipt_sha256
        ),
        adapter_id=response.adapter_id,
        adapter_version=response.adapter_version,
        child_process_id=observation.process_id,
        elapsed_nanoseconds=observation.elapsed_nanoseconds,
        request_frame_byte_count=len(prepared.request_frame_bytes),
        closure_pipe_frame_byte_count=len(
            prepared.closure_pipe_frame_bytes
        ),
        response_frame_byte_count=len(observation.stdout_bytes),
        stderr_byte_count=len(observation.stderr_bytes),
        loaded_project_module_count=len(report.loaded_project_modules),
        pinned_runtime_capture_profile_module_count=len(
            OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES
        ),
        adapted_evidence_bundle_byte_count=len(
            response.adapted_evidence_bundle_bytes
        ),
        child_reported_adapt_complete_call_count=(
            response.runner_direct_adapt_complete_call_count
        ),
        child_reported_adapt_call_count=(
            response.runner_direct_adapt_call_count
        ),
    )
    try:
        SourceBoundAdapterChildRunReceiptV1.__post_init__(receipt)
    except (TypeError, ValueError):
        _fail(SourceBoundAdapterChildRunCode.RECEIPT_INVALID)
    return receipt


def _validate_verified_bundle_identity(
    success: ValidatedOutputBlindAdapterChildSuccessV1,
    verification: (
        _verifier.IndependentAdaptedEvidenceBundleVerificationResultV1
    ),
) -> None:
    response = success.response
    receipt = verification.receipt
    bundle_bytes = response.adapted_evidence_bundle_bytes
    if (
        receipt.case_input_sha256 != response.case_input_sha256
        or receipt.adapter_id != response.adapter_id
        or receipt.adapter_version != response.adapter_version
        or receipt.adapted_evidence_bundle_byte_count != len(bundle_bytes)
        or receipt.adapted_evidence_bundle_sha256
        != _domain_sha256(
            _verifier.ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN,
            bundle_bytes,
        )
    ):
        _fail(SourceBoundAdapterChildRunCode.RESPONSE_IDENTITY_MISMATCH)


def run_source_bound_adapter_child(
    value: SourceBoundAdapterChildRunInputV1,
) -> SourceBoundAdapterChildRunResultV1:
    """Run one fresh local child and independently verify its actual bundle."""

    prepared = _prepare_run(value)
    observation = _run_duplex(prepared)
    _check_observation(observation)
    success_prefix = (
        OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_DOMAIN.encode("ascii")
        + b"\x00"
    )
    failure_prefix = (
        OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_DOMAIN.encode("ascii")
        + b"\x00"
    )
    if observation.stdout_bytes.startswith(failure_prefix):
        try:
            failure = validate_output_blind_adapter_child_failure_identity(
                prepared.request_frame_bytes,
                observation.stdout_bytes,
                implementation_closure_sha256=(
                    prepared.implementation_closure_sha256
                ),
            )
        except OutputBlindAdapterChildABIError:
            _fail(SourceBoundAdapterChildRunCode.INVALID_RESPONSE)
        _fail(
            SourceBoundAdapterChildRunCode.CHILD_REPORTED_FAILURE,
            child_failure_code=failure.response.failure_code,
        )
    if not observation.stdout_bytes.startswith(success_prefix):
        _fail(SourceBoundAdapterChildRunCode.INVALID_RESPONSE)
    try:
        success = validate_output_blind_adapter_child_success_identity(
            prepared.request_frame_bytes,
            observation.stdout_bytes,
            implementation_closure_sha256=(
                prepared.implementation_closure_sha256
            ),
        )
    except OutputBlindAdapterChildABIError as error:
        if error.code.endswith("RESPONSE_BINDING"):
            _fail(
                SourceBoundAdapterChildRunCode.RESPONSE_IDENTITY_MISMATCH
            )
        _fail(SourceBoundAdapterChildRunCode.INVALID_RESPONSE)
    loaded_runtime_capture_profile_sha256 = _validate_source_report(
        prepared,
        success,
    )
    actual_input = (
        _verifier.IndependentAdaptedEvidenceBundleVerificationInputV1(
            case_input_bytes=prepared.input.case_input_bytes,
            adapted_evidence_bundle_bytes=(
                success.response.adapted_evidence_bundle_bytes
            ),
            allowed_exclusion_reason_codes=(
                prepared.input.allowed_exclusion_reason_codes
            ),
            allowed_censor_reason_codes=(
                prepared.input.allowed_censor_reason_codes
            ),
        )
    )
    try:
        verification = _verifier.verify_independent_adapted_evidence_bundle(
            actual_input
        )
    except Exception:
        _fail(SourceBoundAdapterChildRunCode.VERIFICATION_FAILED)
    _validate_verified_bundle_identity(success, verification)
    receipt = _run_receipt(
        prepared,
        observation,
        success,
        loaded_runtime_capture_profile_sha256,
        verification,
    )
    receipt_bytes = source_bound_adapter_child_run_receipt_bytes(receipt)
    return SourceBoundAdapterChildRunResultV1(
        receipt=receipt,
        receipt_bytes=receipt_bytes,
        receipt_sha256=_domain_sha256(
            SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_DIGEST_DOMAIN,
            receipt_bytes,
        ),
        request_frame_bytes=prepared.request_frame_bytes,
        response_frame_bytes=observation.stdout_bytes,
        validated_child_success=success,
        actual_verification_input=actual_input,
        actual_verification_result=verification,
    )


__all__ = [
    "MAXIMUM_SOURCE_BOUND_AGGREGATE_OUTPUT_BYTES",
    "MAXIMUM_SOURCE_BOUND_DEPENDENCY_LOCK_BYTES",
    "MAXIMUM_SOURCE_BOUND_INTERPRETER_BYTES",
    "MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES",
    "MAXIMUM_SOURCE_BOUND_STDERR_BYTES",
    "SOURCE_BOUND_ADAPTER_CHILD_RUN_DECISION_STATUS",
    "SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE",
    "SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_DIGEST_DOMAIN",
    "SOURCE_BOUND_ADAPTER_CHILD_RUN_STATUS",
    "SOURCE_BOUND_CHILD_WALL_TIME_LIMIT_NANOSECONDS",
    "SourceBoundAdapterChildRunCode",
    "SourceBoundAdapterChildRunError",
    "SourceBoundAdapterChildRunInputV1",
    "SourceBoundAdapterChildRunReceiptV1",
    "SourceBoundAdapterChildRunResultV1",
    "run_source_bound_adapter_child",
    "source_bound_adapter_child_run_receipt_bytes",
    "source_bound_adapter_child_run_receipt_sha256",
]
