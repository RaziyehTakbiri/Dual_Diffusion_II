"""Child-safe execution of one exact pre-output adapter case.

This module is intended to be loaded from a validated implementation closure
inside the source-bound child.  It accepts only canonical case-input bytes and
an already constructed adapter.  It calls ``adapt_complete`` at one direct
call site, never calls ``adapt``, and builds the private adapted-evidence
bundle with the child-safe codec.

The runtime contains no expected-value, oracle, verifier, comparator,
publisher, authority, guard, or decision logic.  Its local checks do not prove
fresh recomputation, containment, information-flow noninterference, semantic
truth, or execution attestation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from .adapter_child_bundle_codec import (
    ChildSafeAdaptedEvidenceBundleV1,
    build_child_safe_adapted_evidence_bundle,
)
from .adapter_output_blind_case_input import (
    PreparedOutputBlindCaseInputV1,
    build_output_blind_case_input_v1,
    parse_output_blind_case_input_v1,
)


class OutputBlindChildRuntimeCode(str, Enum):
    """Closed failures emitted by the adapter-only child runtime."""

    INPUT_TYPE = "CHILD_RUNTIME_INPUT_TYPE"
    CASE_INPUT_INVALID = "CHILD_RUNTIME_CASE_INPUT_INVALID"
    ADAPTER_PROTOCOL_INVALID = "CHILD_RUNTIME_ADAPTER_PROTOCOL_INVALID"
    DESCRIPTOR_INVALID = "CHILD_RUNTIME_DESCRIPTOR_INVALID"
    ADAPT_COMPLETE_FAILED = "CHILD_RUNTIME_ADAPT_COMPLETE_FAILED"
    OUTPUT_INVALID = "CHILD_RUNTIME_OUTPUT_INVALID"
    BUNDLE_BUILD_FAILED = "CHILD_RUNTIME_BUNDLE_BUILD_FAILED"
    POSTMUTATION = "CHILD_RUNTIME_POSTMUTATION"
    INTERNAL = "CHILD_RUNTIME_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        OutputBlindChildRuntimeCode.INPUT_TYPE: (
            "child runtime input has an invalid exact type"
        ),
        OutputBlindChildRuntimeCode.CASE_INPUT_INVALID: (
            "child runtime case input is invalid"
        ),
        OutputBlindChildRuntimeCode.ADAPTER_PROTOCOL_INVALID: (
            "child runtime adapter protocol is invalid"
        ),
        OutputBlindChildRuntimeCode.DESCRIPTOR_INVALID: (
            "child runtime adapter descriptor is invalid"
        ),
        OutputBlindChildRuntimeCode.ADAPT_COMPLETE_FAILED: (
            "child runtime adapt_complete call did not complete"
        ),
        OutputBlindChildRuntimeCode.OUTPUT_INVALID: (
            "child runtime adapt_complete output is invalid"
        ),
        OutputBlindChildRuntimeCode.BUNDLE_BUILD_FAILED: (
            "child runtime adapted-evidence bundle was not built"
        ),
        OutputBlindChildRuntimeCode.POSTMUTATION: (
            "child runtime input, descriptor, or output changed during capture"
        ),
        OutputBlindChildRuntimeCode.INTERNAL: (
            "child runtime failed internally"
        ),
    }
)


class OutputBlindChildRuntimeError(ValueError):
    """One fixed child-runtime failure without adapter-controlled text."""

    def __init__(self, code: OutputBlindChildRuntimeCode) -> None:
        if type(code) is not OutputBlindChildRuntimeCode:
            raise TypeError("child runtime error code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: OutputBlindChildRuntimeCode) -> None:
    raise OutputBlindChildRuntimeError(code) from None


@dataclass(frozen=True)
class OutputBlindChildRuntimeResultV1:
    """Locally produced result transport handed to the fixed bootstrap."""

    adapter_id: str
    adapter_version: str
    runner_direct_adapt_complete_call_count: int
    runner_direct_adapt_call_count: int
    adapted_evidence_bundle: ChildSafeAdaptedEvidenceBundleV1

    def __post_init__(self) -> None:
        if type(self) is not OutputBlindChildRuntimeResultV1:
            raise TypeError("child runtime result must be exact")
        if type(self.adapter_id) is not str or not self.adapter_id:
            raise TypeError("adapter_id must be nonempty exact text")
        if type(self.adapter_version) is not str or not self.adapter_version:
            raise TypeError("adapter_version must be nonempty exact text")
        if (
            type(self.runner_direct_adapt_complete_call_count) is not int
            or self.runner_direct_adapt_complete_call_count != 1
        ):
            raise ValueError("adapt_complete direct-call count must be one")
        if (
            type(self.runner_direct_adapt_call_count) is not int
            or self.runner_direct_adapt_call_count != 0
        ):
            raise ValueError("adapt direct-call count must be zero")
        if (
            type(self.adapted_evidence_bundle)
            is not ChildSafeAdaptedEvidenceBundleV1
        ):
            raise TypeError("adapted_evidence_bundle must be exact")
        ChildSafeAdaptedEvidenceBundleV1.__post_init__(
            self.adapted_evidence_bundle
        )


def _snapshot_descriptor(adapter: object) -> _contract.AdapterDescriptor:
    try:
        descriptor_method = getattr(adapter, "descriptor")
        if not callable(descriptor_method):
            raise TypeError()
        descriptor = descriptor_method()
        if type(descriptor) is not _contract.AdapterDescriptor:
            raise TypeError()
        return _contract._snapshot_descriptor(descriptor)
    except Exception:
        _fail(OutputBlindChildRuntimeCode.DESCRIPTOR_INVALID)


def _validate_prepared_unchanged(
    prepared: PreparedOutputBlindCaseInputV1,
    original_bytes: bytes,
) -> None:
    try:
        rebuilt = build_output_blind_case_input_v1(prepared.case_input)
        reparsed = parse_output_blind_case_input_v1(original_bytes)
    except Exception:
        _fail(OutputBlindChildRuntimeCode.POSTMUTATION)
    if rebuilt != prepared or reparsed != prepared:
        _fail(OutputBlindChildRuntimeCode.POSTMUTATION)


def _snapshot_complete_output(
    complete: object,
) -> _evidence.CompleteAdaptedEventSample:
    if type(complete) is not _evidence.CompleteAdaptedEventSample:
        _fail(OutputBlindChildRuntimeCode.OUTPUT_INVALID)
    try:
        return _evidence._snapshot_complete(complete)
    except Exception:
        _fail(OutputBlindChildRuntimeCode.OUTPUT_INVALID)


def _validate_complete_unchanged(
    complete: _evidence.CompleteAdaptedEventSample,
    snapshot: _evidence.CompleteAdaptedEventSample,
) -> None:
    try:
        rebuilt = _evidence._snapshot_complete(complete)
    except Exception:
        _fail(OutputBlindChildRuntimeCode.POSTMUTATION)
    if rebuilt != snapshot:
        _fail(OutputBlindChildRuntimeCode.POSTMUTATION)


def run_output_blind_adapter_case(
    case_input_bytes: bytes,
    adapter: object,
) -> OutputBlindChildRuntimeResultV1:
    """Build a bundle after one local ``adapt_complete`` call."""

    if type(case_input_bytes) is not bytes:
        _fail(OutputBlindChildRuntimeCode.INPUT_TYPE)
    try:
        prepared = parse_output_blind_case_input_v1(case_input_bytes)
    except Exception:
        _fail(OutputBlindChildRuntimeCode.CASE_INPUT_INVALID)
    try:
        adapt_complete_method = getattr(adapter, "adapt_complete")
        if not callable(adapt_complete_method):
            raise TypeError()
    except Exception:
        _fail(OutputBlindChildRuntimeCode.ADAPTER_PROTOCOL_INVALID)

    descriptor_before = _snapshot_descriptor(adapter)
    call_count = 0
    try:
        call_count += 1
        complete = adapt_complete_method(
            prepared.case_input.source_bytes,
            prepared.case_input.partition,
            prepared.case_input.split_manifest,
        )
    except Exception:
        _fail(OutputBlindChildRuntimeCode.ADAPT_COMPLETE_FAILED)
    if call_count != 1:
        _fail(OutputBlindChildRuntimeCode.INTERNAL)
    complete_snapshot = _snapshot_complete_output(complete)

    try:
        descriptor_after = _snapshot_descriptor(adapter)
    except OutputBlindChildRuntimeError:
        _fail(OutputBlindChildRuntimeCode.POSTMUTATION)
    if descriptor_before != descriptor_after:
        _fail(OutputBlindChildRuntimeCode.POSTMUTATION)
    _validate_prepared_unchanged(prepared, case_input_bytes)
    _validate_complete_unchanged(complete, complete_snapshot)
    try:
        bundle = build_child_safe_adapted_evidence_bundle(
            prepared,
            descriptor_before,
            complete_snapshot,
        )
    except Exception:
        _fail(OutputBlindChildRuntimeCode.BUNDLE_BUILD_FAILED)
    _validate_prepared_unchanged(prepared, case_input_bytes)
    _validate_complete_unchanged(complete, complete_snapshot)
    try:
        return OutputBlindChildRuntimeResultV1(
            adapter_id=descriptor_before.identity.adapter_id,
            adapter_version=descriptor_before.identity.adapter_version,
            runner_direct_adapt_complete_call_count=1,
            runner_direct_adapt_call_count=0,
            adapted_evidence_bundle=bundle,
        )
    except (TypeError, ValueError):
        _fail(OutputBlindChildRuntimeCode.INTERNAL)


__all__ = [
    "OutputBlindChildRuntimeCode",
    "OutputBlindChildRuntimeError",
    "OutputBlindChildRuntimeResultV1",
    "run_output_blind_adapter_case",
]
