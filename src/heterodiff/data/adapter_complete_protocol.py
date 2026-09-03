"""Additive protocol for adapters that return complete evidence.

The Phase-B :class:`NativeEventAdapter` contract intentionally returns only an
adapted sample.  This module adds the smallest structural surface needed by an
actual-output boundary to request the Phase-C evidence leaves from the adapter
itself.  It performs no adapter call, source loading, serialization, execution
isolation, expected-value comparison, or gate decision.

The protocol is deliberately not re-exported from the package root.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .adapter_contract import (
    NativeEventAdapter,
    SamplePartition,
    SplitManifest,
)
from .adapter_evidence import CompleteAdaptedEventSample


@runtime_checkable
class CompleteEvidenceAdapterV1(NativeEventAdapter, Protocol):
    """A native-event adapter that exposes one complete evidence return."""

    def adapt_complete(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> CompleteAdaptedEventSample:
        ...


__all__ = ["CompleteEvidenceAdapterV1"]
