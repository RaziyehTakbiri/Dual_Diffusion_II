"""Complete generated adapters for the domain-neutral conformance harness.

All domain-specific parsing and semantic decisions for the four generated
families live in this module.  The shared contract and shared runner can
therefore dispatch exclusively from declared capabilities.  The adapters are
bounded generated-fixture wrappers; they are not official-data adapters and do
not establish model quality or cross-domain generalization.

This module composes the frozen H-CONT-1, M-ACG-1, and P-ACG-1 builders and the
generated R-ACG-1 transaction builder.  It never changes their source objects.
Production-path inventory and semantic-reconstruction cross-checks are kept
separate from adapter leaf construction. They deliberately reuse production
parsers/builders and are therefore correlated development checks, not the
decision-capable independent oracle. The hand-authored source-bound goldens
live only in :mod:`generated_conformance_oracles`.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import StringIO
import json
from typing import Dict, Mapping, Optional, Tuple

from heterodiff.events import (
    EventConfiguration,
    FeatureSchema,
    MultiplicityMode,
    TimeMeasureKind,
)

from .adapter_contract import (
    ATOMIC_COUNTING_GRID_REPRESENTATION_ID,
    NO_FITTED_STATE_SHA256,
    AdapterCapabilities,
    AdapterDescriptor,
    AdapterIdentity,
    AdaptedEventSample,
    SamplePartition,
    SplitManifest,
    build_adapter_manifest,
    feature_schema_digest,
    native_observation_digest,
    rebuild_exact_schema,
)
from .adapter_evidence import (
    CompleteAdaptedEventSample,
    CoverageDisposition,
    CoverageEntry,
    EvaluationLabelEntry,
    EvaluationLabels,
    OccurrenceProvenance,
    PrivateProvenance,
    SemanticReconstruction,
    SourceCoverageLedger,
    SourceFieldStatus,
    SourceInventory,
    SourceInventoryItem,
    SourceValueStatus,
    StaticContext,
    StaticContextEntry,
    evaluation_labels_digest,
    native_occurrence_digests,
    private_provenance_digest,
    semantic_reconstruction_digest,
    source_coverage_ledger_digest,
    source_inventory_digest,
    static_context_digest,
)
from .atomic_counting_grid import AtomicCountingGridTensor
from .cross_domain_counting_fixtures import (
    M_ACG_1_BYTES,
    M_ACG_1_ID,
    M_ACG_1_MAESTRO_SEMANTIC_LIMITS,
    M_ACG_1_MIDI_PARSE_LIMITS,
    P_ACG_1_BYTES,
    P_ACG_1_ID,
    CountingFixtureResult,
    build_m_acg_1,
    build_p_acg_1,
)
from .generated_hawkes_fixture import (
    H_CONT_1_BYTES,
    H_CONT_1_ID,
    build_h_cont_1,
    parse_generated_hawkes_source,
)
from .generated_transaction_fixture import (
    R_ACG_1_A_BYTES,
    R_ACG_1_A_ID,
    R_ACG_1_A_INVOICE_ID,
    R_ACG_1_B_BYTES,
    R_ACG_1_B_ID,
    R_ACG_1_B_INVOICE_ID,
    R_ACG_1_CUSTOMER_ID,
    R_ACG_1_SPLIT,
    TransactionFixtureResult,
    build_r_acg_1_a,
    build_r_acg_1_b,
    parse_transaction_fixture_source,
    transaction_fixture_schema,
)
from .maestro_semantics import build_maestro_semantics
from .midi_raw import (
    MidiChannelEvent,
    MidiMetaEvent,
    MidiSysExEvent,
    parse_midi_bytes,
)
from .physionet_2012_raw import (
    DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS,
    DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS,
    PhysioNet2012IngestionConfig,
    parse_physionet_2012_record,
)


H_ADAPTER_ID = "generated.native.family-a"
M_ADAPTER_ID = "generated.native.family-b"
P_ADAPTER_ID = "generated.native.family-c"
R_ADAPTER_ID = "generated.native.family-d"
GENERATED_ADAPTER_VERSION = "1"

H_GROUP_ID = "generated-process-group-1"
M_GROUP_ID = "synthetic-maestro-group-1"
P_SAMPLE_ID = "900001"
P_GROUP_ID = "900001"

END_OF_STREAM_EXCLUSION_REASON = "structural-terminator"
PARTITION_IDENTITY_EXCLUSION_REASON = "partition-identity"
GENERATED_EXCLUSION_REASON_CODES = tuple(
    sorted(
        (
            END_OF_STREAM_EXCLUSION_REASON,
            PARTITION_IDENTITY_EXCLUSION_REASON,
        )
    )
)
GENERATED_CENSOR_REASON_CODES: Tuple[str, ...] = ()

H_PARTITION = SamplePartition(H_CONT_1_ID, H_GROUP_ID, "train")
M_PARTITION = SamplePartition(M_ACG_1_ID, M_GROUP_ID, "train")
P_PARTITION = SamplePartition(P_SAMPLE_ID, P_GROUP_ID, "train")
R_A_PARTITION = SamplePartition(
    R_ACG_1_A_INVOICE_ID, R_ACG_1_CUSTOMER_ID, R_ACG_1_SPLIT
)
R_B_PARTITION = SamplePartition(
    R_ACG_1_B_INVOICE_ID, R_ACG_1_CUSTOMER_ID, R_ACG_1_SPLIT
)


def generated_conformance_split_manifest() -> SplitManifest:
    """Return a fresh snapshot of the one five-sample generated split."""

    return SplitManifest(
        (H_PARTITION, M_PARTITION, P_PARTITION, R_A_PARTITION, R_B_PARTITION)
    )


GENERATED_CONFORMANCE_SPLIT_MANIFEST = generated_conformance_split_manifest()


class GeneratedConformanceAdapterError(ValueError):
    """A generated adapter input or domain hook violates its exact policy."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _policy_digest(value: object) -> str:
    payload = _canonical_bytes(value)
    digest = hashlib.sha256()
    digest.update(b"heterodiff.generated-adapter-policy.v1\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


H_POLICY_SHA256 = _policy_digest(
    {
        "family": "continuous-simple-0-1-2",
        "fixture": H_CONT_1_ID,
        "labels": "frozen-process-parameters",
        "source_observation": "all-present-values",
    }
)
M_POLICY_SHA256 = _policy_digest(
    {
        "family": "atomic-counting-a",
        "fixture": M_ACG_1_ID,
        "note_pairing": "frozen-fifo",
        "projection": "midi-clock-onset",
        "raw_reconstruction": True,
    }
)
P_POLICY_SHA256 = _policy_digest(
    {
        "family": "atomic-counting-b",
        "fixture": P_ACG_1_ID,
        "missingness": "parameter-specific-minus-one",
        "row_policy": "one-dynamic-observation-row-one-occurrence",
        "static_context": "admission-descriptors",
    }
)
R_POLICY_SHA256 = _policy_digest(
    {
        "cancellation": "explicit-field",
        "family": "atomic-counting-c",
        "group": "customer",
        "sample": "invoice",
        "type_vocabulary": "frozen-product-by-cancellation",
    }
)


def _descriptor(
    adapter_id: str,
    policy_sha256: str,
    *,
    time_measure: TimeMeasureKind,
    multiplicity: MultiplicityMode,
    atomic_grid: bool,
    raw: bool,
    static: bool,
    labels: bool,
) -> AdapterDescriptor:
    representations = (
        (ATOMIC_COUNTING_GRID_REPRESENTATION_ID,) if atomic_grid else ()
    )
    return AdapterDescriptor(
        AdapterIdentity(adapter_id, GENERATED_ADAPTER_VERSION, policy_sha256),
        AdapterCapabilities(
            time_measure=time_measure,
            multiplicity_mode=multiplicity,
            semantic_reconstruction=True,
            raw_byte_reconstruction=raw,
            fitted_state=False,
            supported_representation_ids=representations,
            static_context=static,
            evaluation_labels=labels,
            private_provenance=True,
        ),
    )


def _empty_static(source_sha256: str, policy_sha256: str) -> StaticContext:
    return StaticContext(
        source_sha256,
        policy_sha256,
        "generated.empty-static.v1",
        (),
    )


def _empty_labels(source_sha256: str, policy_sha256: str) -> EvaluationLabels:
    return EvaluationLabels(
        source_sha256,
        policy_sha256,
        "generated.empty-labels.v1",
        (),
    )


def _require_partition(
    partition: SamplePartition,
    expected: SamplePartition,
    split_manifest: SplitManifest,
) -> None:
    if type(partition) is not SamplePartition:
        raise TypeError("partition must be an exact SamplePartition")
    if type(split_manifest) is not SplitManifest:
        raise TypeError("split_manifest must be an exact SplitManifest")
    split = SplitManifest(split_manifest.entries)
    if partition != expected:
        raise GeneratedConformanceAdapterError(
            "partition differs from the frozen generated source identity"
        )
    if not split.contains_exactly(partition):
        raise GeneratedConformanceAdapterError(
            "partition is absent from the shared generated split"
        )


def _assert_configuration_exact(
    actual: EventConfiguration, expected: EventConfiguration
) -> None:
    if type(actual) is not EventConfiguration or type(expected) is not EventConfiguration:
        raise TypeError("domain validation requires exact EventConfiguration values")
    if rebuild_exact_schema(actual.schema) != rebuild_exact_schema(expected.schema):
        raise GeneratedConformanceAdapterError("domain schema differs")
    if actual.events != expected.events:
        raise GeneratedConformanceAdapterError("domain event occurrences differ")
    if tuple(event.event_id for event in actual.events) != tuple(
        event.event_id for event in expected.events
    ):
        raise GeneratedConformanceAdapterError("domain event identifiers differ")
    if actual.observed != expected.observed:
        raise GeneratedConformanceAdapterError("domain observations differ")
    if actual.state_key() != expected.state_key():
        raise GeneratedConformanceAdapterError("domain model state differs")
    if (
        actual.sample_id != expected.sample_id
        or actual.group_id != expected.group_id
    ):
        raise GeneratedConformanceAdapterError("domain private identities differ")


def _pack_complete(
    *,
    descriptor: AdapterDescriptor,
    partition: SamplePartition,
    source_bytes: bytes,
    split_manifest: SplitManifest,
    configuration: EventConfiguration,
    inventory: SourceInventory,
    coverage: SourceCoverageLedger,
    static_context: StaticContext,
    evaluation_labels: EvaluationLabels,
    provenance: PrivateProvenance,
    reconstruction: SemanticReconstruction,
    raw_reconstruction_bytes: Optional[bytes],
) -> CompleteAdaptedEventSample:
    manifest = build_adapter_manifest(
        descriptor=descriptor,
        partition=partition,
        source_bytes=source_bytes,
        split_manifest=split_manifest,
        configuration=configuration,
        static_context_sha256=static_context_digest(static_context),
        evaluation_labels_sha256=evaluation_labels_digest(evaluation_labels),
        coverage_ledger_sha256=source_coverage_ledger_digest(coverage),
        fitted_state_sha256=NO_FITTED_STATE_SHA256,
        private_provenance_sha256=private_provenance_digest(provenance),
        semantic_reconstruction_sha256=semantic_reconstruction_digest(
            reconstruction
        ),
    )
    return CompleteAdaptedEventSample(
        sample=AdaptedEventSample(configuration, manifest),
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted_state=None,
        reconstruction=reconstruction,
        raw_reconstruction_bytes=raw_reconstruction_bytes,
    )


def _inventory(
    source_bytes: bytes,
    policy_sha256: str,
    item_format_id: str,
    items: Tuple[Tuple[str, bytes], ...],
) -> SourceInventory:
    return SourceInventory(
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_size_bytes=len(source_bytes),
        policy_sha256=policy_sha256,
        item_format_id=item_format_id,
        items=tuple(SourceInventoryItem(key, payload) for key, payload in items),
    )


def _coverage(
    source_bytes: bytes,
    policy_sha256: str,
    inventory: SourceInventory,
    entries: Tuple[CoverageEntry, ...],
) -> SourceCoverageLedger:
    return SourceCoverageLedger(
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_size_bytes=len(source_bytes),
        policy_sha256=policy_sha256,
        source_inventory_sha256=source_inventory_digest(inventory),
        entries=entries,
    )


def _semantic_reconstruction(
    source_bytes: bytes,
    schema: FeatureSchema,
    policy_sha256: str,
    format_id: str,
    record_count: int,
    payload: bytes,
) -> SemanticReconstruction:
    return SemanticReconstruction(
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        schema_sha256=feature_schema_digest(schema),
        policy_sha256=policy_sha256,
        semantic_format_id=format_id,
        record_count=record_count,
        canonical_payload_bytes=payload,
    )


def _hawkes_event_payload(event: object) -> Mapping[str, object]:
    return {
        "event_type": event.event_type,
        "marks": [float(value).hex().lower() for value in event.mark],
        "time": event.time.hex().lower(),
        "type_name": event.type_name,
    }


def _hawkes_metadata_payload(simulation: object) -> Mapping[str, object]:
    metadata = simulation.metadata
    return {
        "candidate_count": metadata.candidate_count,
        "horizon": metadata.horizon.hex().lower(),
        "max_candidates": 1000,
        "max_events": metadata.max_events,
        "parameter_id": "heterodiff.generated-hawkes-parameters.v1",
        "realized_event_counts": list(metadata.realized_event_counts),
        "seed": metadata.seed,
        "terminated_by": metadata.terminated_by,
    }


def _hawkes_semantic_bytes(simulation: object) -> bytes:
    return _canonical_bytes(
        {
            "events": [_hawkes_event_payload(event) for event in simulation.events],
            "format": "heterodiff.generated-hawkes-semantic-record.v1",
        }
    )


def production_h_inventory_crosscheck(source_bytes: bytes) -> SourceInventory:
    """Reparse H source bytes without consuming adapter-built evidence leaves."""

    simulation = parse_generated_hawkes_source(source_bytes)
    items = (("metadata", _canonical_bytes(_hawkes_metadata_payload(simulation))),) + tuple(
        (
            "event.{:04d}".format(index),
            _canonical_bytes(_hawkes_event_payload(event)),
        )
        for index, event in enumerate(simulation.events)
    )
    return _inventory(
        source_bytes,
        H_POLICY_SHA256,
        "generated.hawkes-item.v1",
        tuple(sorted(items)),
    )


def production_h_reconstruction_crosscheck(
    source_bytes: bytes,
) -> SemanticReconstruction:
    simulation = parse_generated_hawkes_source(source_bytes)
    configuration = simulation.to_configuration(
        sample_id=H_PARTITION.sample_id, group_id=H_PARTITION.group_id
    )
    return _semantic_reconstruction(
        source_bytes,
        configuration.schema,
        H_POLICY_SHA256,
        "generated.hawkes-semantic.v1",
        len(simulation.events),
        _hawkes_semantic_bytes(simulation),
    )


def _midi_item_key(track_index: int, event_index: int) -> str:
    return "track.{:04d}.event.{:04d}".format(track_index, event_index)


def _midi_event_payload(event: object) -> bytes:
    common: Dict[str, object] = {
        "absolute_ticks": event.absolute_ticks,
        "delta_ticks": event.delta_ticks,
        "encoded_hex": event.encoded_bytes.hex(),
        "event_index": event.event_index,
        "track_byte_offset": event.track_byte_offset,
        "track_index": event.track_index,
    }
    if isinstance(event, MidiChannelEvent):
        common.update(
            {
                "channel": event.channel,
                "data_hex": event.data.hex(),
                "kind": "channel",
                "message_type": event.message_type,
                "status": event.status,
                "used_running_status": event.used_running_status,
            }
        )
    elif isinstance(event, MidiMetaEvent):
        common.update(
            {
                "kind": "meta",
                "meta_name": event.meta_name,
                "meta_type": event.meta_type,
                "payload_hex": event.payload.hex(),
            }
        )
    elif isinstance(event, MidiSysExEvent):
        common.update(
            {
                "kind": "sysex",
                "payload_hex": event.payload.hex(),
                "status": event.status,
            }
        )
    else:  # pragma: no cover - the frozen parser has a closed event union
        raise TypeError("unsupported MIDI event type")
    return _canonical_bytes(common)


def _m_inventory_from_fixture(fixture: CountingFixtureResult) -> SourceInventory:
    items = tuple(
        (
            _midi_item_key(event.track_index, event.event_index),
            _midi_event_payload(event),
        )
        for track in fixture.private_provenance.raw_midi.tracks
        for event in track.events
    )
    return _inventory(
        M_ACG_1_BYTES,
        M_POLICY_SHA256,
        "generated.midi-event.v1",
        items,
    )


def production_m_inventory_crosscheck(source_bytes: bytes) -> SourceInventory:
    if source_bytes != M_ACG_1_BYTES:
        raise GeneratedConformanceAdapterError("M source bytes differ")
    midi = parse_midi_bytes(source_bytes, limits=M_ACG_1_MIDI_PARSE_LIMITS)
    items = tuple(
        (
            _midi_item_key(event.track_index, event.event_index),
            _midi_event_payload(event),
        )
        for track in midi.tracks
        for event in track.events
    )
    return _inventory(
        source_bytes,
        M_POLICY_SHA256,
        "generated.midi-event.v1",
        items,
    )


def _m_semantic_bytes(fixture: CountingFixtureResult) -> bytes:
    return _canonical_bytes(fixture.private_provenance.semantic_piece.to_private_dict())


def production_m_reconstruction_crosscheck(
    source_bytes: bytes,
) -> SemanticReconstruction:
    if source_bytes != M_ACG_1_BYTES:
        raise GeneratedConformanceAdapterError("M source bytes differ")
    midi = parse_midi_bytes(source_bytes, limits=M_ACG_1_MIDI_PARSE_LIMITS)
    semantics = build_maestro_semantics(
        midi,
        source_split="train",
        limits=M_ACG_1_MAESTRO_SEMANTIC_LIMITS,
    )
    fixture = build_m_acg_1()
    return _semantic_reconstruction(
        source_bytes,
        fixture.configuration.schema,
        M_POLICY_SHA256,
        "generated.note-semantics.v1",
        len(semantics.notes),
        _canonical_bytes(semantics.to_private_dict()),
    )


def _p_row_key(line_number: int) -> str:
    return "row.{:04d}".format(line_number)


def _p_row_payload(row: object) -> bytes:
    return _canonical_bytes(
        {
            "cells": list(row.csv_cells),
            "elapsed_minutes": row.elapsed_minutes,
            "line_number": row.line_number,
        }
    )


def _p_inventory_from_fixture(fixture: CountingFixtureResult) -> SourceInventory:
    items = tuple(
        (_p_row_key(row.line_number), _p_row_payload(row))
        for row in fixture.private_provenance.raw_record.rows
    )
    return _inventory(
        P_ACG_1_BYTES,
        P_POLICY_SHA256,
        "generated.clinical-row.v1",
        items,
    )


def _production_p_record(source_bytes: bytes):
    if source_bytes != P_ACG_1_BYTES:
        raise GeneratedConformanceAdapterError("P source bytes differ")
    text = source_bytes.decode("utf-8")
    return parse_physionet_2012_record(
        StringIO(text),
        config=PhysioNet2012IngestionConfig(
            admission_descriptors=(
                DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS
            ),
            dual_role_parameters=DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS,
            maximum_elapsed_minutes=2880,
        ),
    )


def production_p_inventory_crosscheck(source_bytes: bytes) -> SourceInventory:
    record = _production_p_record(source_bytes)
    items = tuple(
        (_p_row_key(row.line_number), _p_row_payload(row))
        for row in record.rows
    )
    return _inventory(
        source_bytes,
        P_POLICY_SHA256,
        "generated.clinical-row.v1",
        items,
    )


def _p_semantic_bytes(fixture: CountingFixtureResult) -> bytes:
    return _canonical_bytes(
        {
            "format": "generated-clinical-row-semantics-v1",
            "rows": [
                {
                    "cells": list(row.csv_cells),
                    "elapsed_minutes": row.elapsed_minutes,
                    "line_number": row.line_number,
                }
                for row in fixture.private_provenance.raw_record.rows
            ],
        }
    )


def production_p_reconstruction_crosscheck(
    source_bytes: bytes,
) -> SemanticReconstruction:
    record = _production_p_record(source_bytes)
    schema = build_p_acg_1().configuration.schema
    payload = _canonical_bytes(
        {
            "format": "generated-clinical-row-semantics-v1",
            "rows": [
                {
                    "cells": list(row.csv_cells),
                    "elapsed_minutes": row.elapsed_minutes,
                    "line_number": row.line_number,
                }
                for row in record.rows
            ],
        }
    )
    return _semantic_reconstruction(
        source_bytes,
        schema,
        P_POLICY_SHA256,
        "generated.clinical-row-semantics.v1",
        len(record.rows),
        payload,
    )


def _r_item_key(line_number: int) -> str:
    return "line.{:04d}".format(line_number)


def _r_row_payload(row: object) -> bytes:
    return _canonical_bytes(
        {
            "line_number": row.line_number,
            "raw_cells": list(row.raw_cells),
            "semantic_fields": [list(pair) for pair in row.semantic.ordered_fields()],
        }
    )


def _r_policy_source(source_bytes: bytes) -> TransactionFixtureResult:
    if source_bytes == R_ACG_1_A_BYTES:
        return build_r_acg_1_a()
    if source_bytes == R_ACG_1_B_BYTES:
        return build_r_acg_1_b()
    raise GeneratedConformanceAdapterError("R source bytes are not registered")


def _r_inventory_from_fixture(fixture: TransactionFixtureResult) -> SourceInventory:
    items = tuple(
        (_r_item_key(row.line_number), _r_row_payload(row))
        for row in fixture.private_provenance.source_rows
    )
    source = (
        R_ACG_1_A_BYTES
        if fixture.fixture_id == R_ACG_1_A_ID
        else R_ACG_1_B_BYTES
    )
    return _inventory(
        source,
        R_POLICY_SHA256,
        "generated.transaction-row.v1",
        items,
    )


def production_r_inventory_crosscheck(source_bytes: bytes) -> SourceInventory:
    if source_bytes not in (R_ACG_1_A_BYTES, R_ACG_1_B_BYTES):
        raise GeneratedConformanceAdapterError("R source bytes are not registered")
    rows = parse_transaction_fixture_source(
        source_bytes, expected_sha256=hashlib.sha256(source_bytes).hexdigest()
    )
    items = tuple(
        (_r_item_key(row.line_number), _r_row_payload(row)) for row in rows
    )
    return _inventory(
        source_bytes,
        R_POLICY_SHA256,
        "generated.transaction-row.v1",
        items,
    )


def _r_semantic_bytes(fixture: TransactionFixtureResult) -> bytes:
    return _canonical_bytes(
        {
            "format": "generated-transaction-row-multiset-v1",
            "rows": [
                [list(pair) for pair in row]
                for row in fixture.reconstruct_semantic_row_multiset()
            ],
        }
    )


def production_r_reconstruction_crosscheck(
    source_bytes: bytes,
) -> SemanticReconstruction:
    if source_bytes not in (R_ACG_1_A_BYTES, R_ACG_1_B_BYTES):
        raise GeneratedConformanceAdapterError("R source bytes are not registered")
    rows = parse_transaction_fixture_source(
        source_bytes, expected_sha256=hashlib.sha256(source_bytes).hexdigest()
    )
    semantic_rows = tuple(
        semantic.ordered_fields()
        for semantic in sorted(
            (row.semantic for row in rows), key=lambda value: value.sort_key()
        )
    )
    payload = _canonical_bytes(
        {
            "format": "generated-transaction-row-multiset-v1",
            "rows": [
                [list(pair) for pair in row] for row in semantic_rows
            ],
        }
    )
    return _semantic_reconstruction(
        source_bytes,
        transaction_fixture_schema(),
        R_POLICY_SHA256,
        "generated.transaction-multiset.v1",
        len(rows),
        payload,
    )


class _GeneratedAdapterBase:
    """Capability-selected representation methods shared by all families."""

    _descriptor_value: AdapterDescriptor

    def descriptor(self) -> AdapterDescriptor:
        return self._descriptor_value

    def encode_representation(
        self,
        representation_id: str,
        configuration: EventConfiguration,
    ) -> object:
        if type(representation_id) is not str:
            raise TypeError("representation_id must be an exact string")
        if type(configuration) is not EventConfiguration:
            raise TypeError("configuration must be an exact EventConfiguration")
        if representation_id not in (
            self.descriptor().capabilities.supported_representation_ids
        ):
            raise GeneratedConformanceAdapterError(
                "representation is not declared by adapter capabilities"
            )
        if representation_id != ATOMIC_COUNTING_GRID_REPRESENTATION_ID:
            raise GeneratedConformanceAdapterError("unsupported representation")
        if feature_schema_digest(configuration.schema) != feature_schema_digest(
            self.schema()
        ):
            raise GeneratedConformanceAdapterError(
                "configuration schema does not match adapter schema"
            )
        return AtomicCountingGridTensor.from_configuration(configuration)

    def decode_representation(
        self,
        representation_id: str,
        payload: object,
        *,
        schema: FeatureSchema,
    ) -> EventConfiguration:
        if type(representation_id) is not str:
            raise TypeError("representation_id must be an exact string")
        if type(schema) is not FeatureSchema:
            raise TypeError("schema must be an exact FeatureSchema")
        if representation_id not in (
            self.descriptor().capabilities.supported_representation_ids
        ):
            raise GeneratedConformanceAdapterError(
                "representation is not declared by adapter capabilities"
            )
        if representation_id != ATOMIC_COUNTING_GRID_REPRESENTATION_ID:
            raise GeneratedConformanceAdapterError("unsupported representation")
        if type(payload) is not AtomicCountingGridTensor:
            raise TypeError("payload must be an exact AtomicCountingGridTensor")
        adapter_schema_sha256 = feature_schema_digest(self.schema())
        if feature_schema_digest(schema) != adapter_schema_sha256:
            raise GeneratedConformanceAdapterError(
                "requested schema does not match adapter schema"
            )
        if feature_schema_digest(payload.schema) != adapter_schema_sha256:
            raise GeneratedConformanceAdapterError(
                "representation payload schema does not match requested schema"
            )
        return payload.to_configuration()

    def adapt(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> AdaptedEventSample:
        return self.adapt_complete(source_bytes, partition, split_manifest).sample


class GeneratedHAdapter(_GeneratedAdapterBase):
    def __init__(self) -> None:
        self._descriptor_value = _descriptor(
            H_ADAPTER_ID,
            H_POLICY_SHA256,
            time_measure=TimeMeasureKind.CONTINUOUS,
            multiplicity=MultiplicityMode.SIMPLE,
            atomic_grid=False,
            raw=False,
            static=False,
            labels=True,
        )

    def schema(self) -> FeatureSchema:
        return build_h_cont_1().configuration.schema

    def adapt_complete(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> CompleteAdaptedEventSample:
        if source_bytes != H_CONT_1_BYTES:
            raise GeneratedConformanceAdapterError("H source bytes differ")
        _require_partition(partition, H_PARTITION, split_manifest)
        fixture = build_h_cont_1(
            sample_id=partition.sample_id, group_id=partition.group_id
        )
        inventory = _inventory(
            source_bytes,
            H_POLICY_SHA256,
            "generated.hawkes-item.v1",
            fixture.inventory_items,
        )
        occurrence_digests = native_occurrence_digests(fixture.configuration)
        coverage_entries = [
            CoverageEntry(
                "metadata",
                CoverageDisposition.EVALUATION_ONLY_LABEL,
                "process-parameters",
            )
        ]
        provenance_entries = []
        for index, (event, digest) in enumerate(
            zip(fixture.configuration.events, occurrence_digests)
        ):
            item_key = "event.{:04d}".format(index)
            target = "occurrence.event.{:04d}".format(index)
            coverage_entries.append(
                CoverageEntry(item_key, CoverageDisposition.EVENT_OCCURRENCE, target)
            )
            applicable = fixture.configuration.schema.event_type(
                event.event_type
            ).field_names
            provenance_entries.append(
                OccurrenceProvenance(
                    target,
                    digest,
                    (item_key,),
                    tuple(
                        SourceFieldStatus(name, SourceValueStatus.PRESENT)
                        for name in applicable
                    ),
                    "generated.hawkes-provenance.v1",
                    fixture.private_event_payloads[item_key],
                )
            )
        coverage = _coverage(
            source_bytes,
            H_POLICY_SHA256,
            inventory,
            tuple(coverage_entries),
        )
        labels = EvaluationLabels(
            fixture.source_sha256,
            H_POLICY_SHA256,
            "generated.process-parameters.v1",
            (
                EvaluationLabelEntry(
                    "process-parameters", fixture.evaluation_parameter_bytes
                ),
            ),
        )
        provenance = PrivateProvenance(
            fixture.source_sha256,
            native_observation_digest(fixture.configuration),
            H_POLICY_SHA256,
            tuple(provenance_entries),
        )
        reconstruction = _semantic_reconstruction(
            source_bytes,
            fixture.configuration.schema,
            H_POLICY_SHA256,
            "generated.hawkes-semantic.v1",
            len(fixture.configuration.events),
            fixture.semantic_payload_bytes,
        )
        return _pack_complete(
            descriptor=self.descriptor(),
            partition=partition,
            source_bytes=source_bytes,
            split_manifest=split_manifest,
            configuration=fixture.configuration,
            inventory=inventory,
            coverage=coverage,
            static_context=_empty_static(fixture.source_sha256, H_POLICY_SHA256),
            evaluation_labels=labels,
            provenance=provenance,
            reconstruction=reconstruction,
            raw_reconstruction_bytes=None,
        )

    def validate_domain_sample(self, sample: AdaptedEventSample) -> None:
        if type(sample) is not AdaptedEventSample:
            raise TypeError("sample must be exact AdaptedEventSample")
        expected = build_h_cont_1(
            sample_id=sample.manifest.partition.sample_id,
            group_id=sample.manifest.partition.group_id,
        ).configuration
        _assert_configuration_exact(sample.configuration, expected)


class GeneratedMAdapter(_GeneratedAdapterBase):
    def __init__(self) -> None:
        self._descriptor_value = _descriptor(
            M_ADAPTER_ID,
            M_POLICY_SHA256,
            time_measure=TimeMeasureKind.ATOMIC,
            multiplicity=MultiplicityMode.FINITE_COUNTING,
            atomic_grid=True,
            raw=True,
            static=True,
            labels=False,
        )

    def schema(self) -> FeatureSchema:
        return build_m_acg_1().configuration.schema

    def adapt_complete(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> CompleteAdaptedEventSample:
        if source_bytes != M_ACG_1_BYTES:
            raise GeneratedConformanceAdapterError("M source bytes differ")
        _require_partition(partition, M_PARTITION, split_manifest)
        fixture = build_m_acg_1()
        inventory = _m_inventory_from_fixture(fixture)
        semantic_piece = fixture.private_provenance.semantic_piece
        coverage_entries = []
        occurrence_digests = native_occurrence_digests(fixture.configuration)
        provenance_entries = []
        for note, digest in zip(
            fixture.private_provenance.event_notes, occurrence_digests
        ):
            target = "note.{}".format(note.note_id)
            onset_key = _midi_item_key(
                note.onset_provenance.track_index,
                note.onset_provenance.event_index,
            )
            closure_key = _midi_item_key(
                note.closure_provenance.track_index,
                note.closure_provenance.event_index,
            )
            coverage_entries.extend(
                (
                    CoverageEntry(
                        onset_key,
                        CoverageDisposition.EVENT_OCCURRENCE,
                        target,
                        secondary_tags=("note-onset",),
                    ),
                    CoverageEntry(
                        closure_key,
                        CoverageDisposition.EVENT_OCCURRENCE,
                        target,
                        secondary_tags=("note-closure",),
                    ),
                )
            )
            provenance_entries.append(
                OccurrenceProvenance(
                    target,
                    digest,
                    tuple(sorted((onset_key, closure_key))),
                    (
                        SourceFieldStatus(
                            "midi_clock_onset_offset", SourceValueStatus.PRESENT
                        ),
                        SourceFieldStatus(
                            "velocity_normalized", SourceValueStatus.PRESENT
                        ),
                    ),
                    "generated.note-provenance.v1",
                    _canonical_bytes(note.to_private_dict()),
                )
            )
        tempo_sources = tuple(
            source
            for point in semantic_piece.tempo_map.points
            for source in point.source_events
        )
        if len(tempo_sources) != 1:
            raise GeneratedConformanceAdapterError(
                "M fixture requires exactly one explicit tempo source"
            )
        tempo_source = tempo_sources[0]
        coverage_entries.append(
            CoverageEntry(
                _midi_item_key(
                    tempo_source.track_index, tempo_source.event_index
                ),
                CoverageDisposition.STATIC_CONTEXT,
                "tempo-map",
            )
        )
        end_event = fixture.private_provenance.raw_midi.tracks[0].events[-1]
        if not isinstance(end_event, MidiMetaEvent) or not end_event.is_end_of_track:
            raise GeneratedConformanceAdapterError("M terminal event differs")
        coverage_entries.append(
            CoverageEntry(
                _midi_item_key(end_event.track_index, end_event.event_index),
                CoverageDisposition.EXCLUDED_WITH_REASON,
                exclusion_reason_code=END_OF_STREAM_EXCLUSION_REASON,
                secondary_tags=("container-structure",),
            )
        )
        coverage = _coverage(
            source_bytes,
            M_POLICY_SHA256,
            inventory,
            tuple(coverage_entries),
        )
        static = StaticContext(
            fixture.source_sha256,
            M_POLICY_SHA256,
            "generated.tempo-map.v1",
            (
                StaticContextEntry(
                    "tempo-map",
                    _canonical_bytes(semantic_piece.tempo_map.to_private_dict()),
                ),
            ),
        )
        provenance = PrivateProvenance(
            fixture.source_sha256,
            native_observation_digest(fixture.configuration),
            M_POLICY_SHA256,
            tuple(provenance_entries),
        )
        reconstruction = _semantic_reconstruction(
            source_bytes,
            fixture.configuration.schema,
            M_POLICY_SHA256,
            "generated.note-semantics.v1",
            len(fixture.configuration.events),
            _m_semantic_bytes(fixture),
        )
        return _pack_complete(
            descriptor=self.descriptor(),
            partition=partition,
            source_bytes=source_bytes,
            split_manifest=split_manifest,
            configuration=fixture.configuration,
            inventory=inventory,
            coverage=coverage,
            static_context=static,
            evaluation_labels=_empty_labels(fixture.source_sha256, M_POLICY_SHA256),
            provenance=provenance,
            reconstruction=reconstruction,
            raw_reconstruction_bytes=fixture.reconstruct_source_bytes(),
        )

    def validate_domain_sample(self, sample: AdaptedEventSample) -> None:
        if type(sample) is not AdaptedEventSample:
            raise TypeError("sample must be exact AdaptedEventSample")
        _assert_configuration_exact(sample.configuration, build_m_acg_1().configuration)


class GeneratedPAdapter(_GeneratedAdapterBase):
    def __init__(self) -> None:
        self._descriptor_value = _descriptor(
            P_ADAPTER_ID,
            P_POLICY_SHA256,
            time_measure=TimeMeasureKind.ATOMIC,
            multiplicity=MultiplicityMode.FINITE_COUNTING,
            atomic_grid=True,
            raw=False,
            static=True,
            labels=False,
        )

    def schema(self) -> FeatureSchema:
        return build_p_acg_1().configuration.schema

    def adapt_complete(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> CompleteAdaptedEventSample:
        if source_bytes != P_ACG_1_BYTES:
            raise GeneratedConformanceAdapterError("P source bytes differ")
        _require_partition(partition, P_PARTITION, split_manifest)
        fixture = build_p_acg_1()
        inventory = _p_inventory_from_fixture(fixture)
        coverage_entries = []
        static_entries = []
        record = fixture.private_provenance.raw_record
        record_id_row = next(
            row for row in record.rows if row.parameter == "RecordID"
        )
        coverage_entries.append(
            CoverageEntry(
                _p_row_key(record_id_row.line_number),
                CoverageDisposition.EXCLUDED_WITH_REASON,
                exclusion_reason_code=PARTITION_IDENTITY_EXCLUSION_REASON,
                secondary_tags=("private-identity",),
            )
        )
        admission_by_parameter = {
            value.parameter: value
            for value in fixture.private_provenance.admission_values
        }
        for parameter in sorted(admission_by_parameter):
            value = admission_by_parameter[parameter]
            target = "context.{}".format(parameter.lower())
            coverage_entries.append(
                CoverageEntry(
                    _p_row_key(value.source_row.line_number),
                    CoverageDisposition.STATIC_CONTEXT,
                    target,
                )
            )
            static_entries.append(
                StaticContextEntry(
                    target,
                    _canonical_bytes(
                        {
                            "is_missing": value.is_missing,
                            "parameter": parameter,
                            "raw_cells": list(value.source_row.csv_cells),
                            "value": (
                                None
                                if value.value is None
                                else value.value.hex().lower()
                            ),
                        }
                    ),
                )
            )
        occurrence_digests = native_occurrence_digests(fixture.configuration)
        provenance_entries = []
        for sidecar, digest in zip(
            fixture.private_provenance.event_sidecars, occurrence_digests
        ):
            item_key = _p_row_key(sidecar.source_row.line_number)
            target = "occurrence.row.{:04d}".format(sidecar.source_row.line_number)
            coverage_entries.append(
                CoverageEntry(item_key, CoverageDisposition.EVENT_OCCURRENCE, target)
            )
            status = (
                SourceValueStatus.SOURCE_MISSING
                if sidecar.value_missing
                else SourceValueStatus.PRESENT
            )
            provenance_entries.append(
                OccurrenceProvenance(
                    target,
                    digest,
                    (item_key,),
                    (SourceFieldStatus("value", status),),
                    "generated.row-provenance.v1",
                    _canonical_bytes(
                        {
                            "event_id": list(sidecar.event_id),
                            "raw_cells": list(sidecar.source_row.csv_cells),
                            "source_line": sidecar.source_row.line_number,
                            "value_missing": sidecar.value_missing,
                        }
                    ),
                )
            )
        coverage = _coverage(
            source_bytes,
            P_POLICY_SHA256,
            inventory,
            tuple(coverage_entries),
        )
        static = StaticContext(
            fixture.source_sha256,
            P_POLICY_SHA256,
            "generated.admission-context.v1",
            tuple(static_entries),
        )
        provenance = PrivateProvenance(
            fixture.source_sha256,
            native_observation_digest(fixture.configuration),
            P_POLICY_SHA256,
            tuple(provenance_entries),
        )
        reconstruction = _semantic_reconstruction(
            source_bytes,
            fixture.configuration.schema,
            P_POLICY_SHA256,
            "generated.clinical-row-semantics.v1",
            len(record.rows),
            _p_semantic_bytes(fixture),
        )
        return _pack_complete(
            descriptor=self.descriptor(),
            partition=partition,
            source_bytes=source_bytes,
            split_manifest=split_manifest,
            configuration=fixture.configuration,
            inventory=inventory,
            coverage=coverage,
            static_context=static,
            evaluation_labels=_empty_labels(fixture.source_sha256, P_POLICY_SHA256),
            provenance=provenance,
            reconstruction=reconstruction,
            raw_reconstruction_bytes=None,
        )

    def validate_domain_sample(self, sample: AdaptedEventSample) -> None:
        if type(sample) is not AdaptedEventSample:
            raise TypeError("sample must be exact AdaptedEventSample")
        _assert_configuration_exact(sample.configuration, build_p_acg_1().configuration)


class GeneratedRAdapter(_GeneratedAdapterBase):
    def __init__(self) -> None:
        self._descriptor_value = _descriptor(
            R_ADAPTER_ID,
            R_POLICY_SHA256,
            time_measure=TimeMeasureKind.ATOMIC,
            multiplicity=MultiplicityMode.FINITE_COUNTING,
            atomic_grid=True,
            raw=False,
            static=False,
            labels=False,
        )

    def schema(self) -> FeatureSchema:
        return transaction_fixture_schema()

    def _fixture_and_partition(
        self, source_bytes: bytes
    ) -> Tuple[TransactionFixtureResult, SamplePartition]:
        if source_bytes == R_ACG_1_A_BYTES:
            return build_r_acg_1_a(), R_A_PARTITION
        if source_bytes == R_ACG_1_B_BYTES:
            return build_r_acg_1_b(), R_B_PARTITION
        raise GeneratedConformanceAdapterError("R source bytes are not registered")

    def adapt_complete(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> CompleteAdaptedEventSample:
        fixture, expected_partition = self._fixture_and_partition(source_bytes)
        _require_partition(partition, expected_partition, split_manifest)
        inventory = _r_inventory_from_fixture(fixture)
        occurrence_digests = native_occurrence_digests(fixture.configuration)
        coverage_entries = []
        provenance_entries = []
        for row, digest in zip(
            fixture.private_provenance.event_rows, occurrence_digests
        ):
            item_key = _r_item_key(row.line_number)
            target = "occurrence.line.{:04d}".format(row.line_number)
            coverage_entries.append(
                CoverageEntry(item_key, CoverageDisposition.EVENT_OCCURRENCE, target)
            )
            provenance_entries.append(
                OccurrenceProvenance(
                    target,
                    digest,
                    (item_key,),
                    (
                        SourceFieldStatus("quantity", SourceValueStatus.PRESENT),
                        SourceFieldStatus("unit_price", SourceValueStatus.PRESENT),
                    ),
                    "generated.transaction-provenance.v1",
                    _r_row_payload(row),
                )
            )
        coverage = _coverage(
            source_bytes,
            R_POLICY_SHA256,
            inventory,
            tuple(coverage_entries),
        )
        provenance = PrivateProvenance(
            fixture.source_sha256,
            native_observation_digest(fixture.configuration),
            R_POLICY_SHA256,
            tuple(provenance_entries),
        )
        reconstruction = _semantic_reconstruction(
            source_bytes,
            fixture.configuration.schema,
            R_POLICY_SHA256,
            "generated.transaction-multiset.v1",
            len(fixture.configuration.events),
            _r_semantic_bytes(fixture),
        )
        return _pack_complete(
            descriptor=self.descriptor(),
            partition=partition,
            source_bytes=source_bytes,
            split_manifest=split_manifest,
            configuration=fixture.configuration,
            inventory=inventory,
            coverage=coverage,
            static_context=_empty_static(fixture.source_sha256, R_POLICY_SHA256),
            evaluation_labels=_empty_labels(fixture.source_sha256, R_POLICY_SHA256),
            provenance=provenance,
            reconstruction=reconstruction,
            raw_reconstruction_bytes=None,
        )

    def validate_domain_sample(self, sample: AdaptedEventSample) -> None:
        if type(sample) is not AdaptedEventSample:
            raise TypeError("sample must be exact AdaptedEventSample")
        sample_id = sample.manifest.partition.sample_id
        if sample_id == R_A_PARTITION.sample_id:
            expected = build_r_acg_1_a().configuration
        elif sample_id == R_B_PARTITION.sample_id:
            expected = build_r_acg_1_b().configuration
        else:
            raise GeneratedConformanceAdapterError("unknown R sample identity")
        _assert_configuration_exact(sample.configuration, expected)


def build_h_complete_sample(
    split_manifest: SplitManifest = GENERATED_CONFORMANCE_SPLIT_MANIFEST,
) -> CompleteAdaptedEventSample:
    return GeneratedHAdapter().adapt_complete(
        H_CONT_1_BYTES, H_PARTITION, split_manifest
    )


def build_m_complete_sample(
    split_manifest: SplitManifest = GENERATED_CONFORMANCE_SPLIT_MANIFEST,
) -> CompleteAdaptedEventSample:
    return GeneratedMAdapter().adapt_complete(
        M_ACG_1_BYTES, M_PARTITION, split_manifest
    )


def build_p_complete_sample(
    split_manifest: SplitManifest = GENERATED_CONFORMANCE_SPLIT_MANIFEST,
) -> CompleteAdaptedEventSample:
    return GeneratedPAdapter().adapt_complete(
        P_ACG_1_BYTES, P_PARTITION, split_manifest
    )


def build_r_a_complete_sample(
    split_manifest: SplitManifest = GENERATED_CONFORMANCE_SPLIT_MANIFEST,
) -> CompleteAdaptedEventSample:
    return GeneratedRAdapter().adapt_complete(
        R_ACG_1_A_BYTES, R_A_PARTITION, split_manifest
    )


def build_r_b_complete_sample(
    split_manifest: SplitManifest = GENERATED_CONFORMANCE_SPLIT_MANIFEST,
) -> CompleteAdaptedEventSample:
    return GeneratedRAdapter().adapt_complete(
        R_ACG_1_B_BYTES, R_B_PARTITION, split_manifest
    )


@dataclass(frozen=True)
class GeneratedCompleteCase:
    family_id: str
    adapter: object
    source_bytes: bytes
    partition: SamplePartition
    complete: CompleteAdaptedEventSample

    def __post_init__(self) -> None:
        if type(self.family_id) is not str or not self.family_id:
            raise TypeError("family_id must be nonempty exact text")
        if type(self.source_bytes) is not bytes:
            raise TypeError("source_bytes must be exact bytes")
        if type(self.partition) is not SamplePartition:
            raise TypeError("partition must be exact SamplePartition")
        if type(self.complete) is not CompleteAdaptedEventSample:
            raise TypeError("complete must be exact CompleteAdaptedEventSample")


def build_all_generated_complete_cases(
    split_manifest: SplitManifest = GENERATED_CONFORMANCE_SPLIT_MANIFEST,
) -> Tuple[GeneratedCompleteCase, ...]:
    h_adapter = GeneratedHAdapter()
    m_adapter = GeneratedMAdapter()
    p_adapter = GeneratedPAdapter()
    r_adapter = GeneratedRAdapter()
    values = (
        (H_CONT_1_ID, h_adapter, H_CONT_1_BYTES, H_PARTITION),
        (M_ACG_1_ID, m_adapter, M_ACG_1_BYTES, M_PARTITION),
        (P_ACG_1_ID, p_adapter, P_ACG_1_BYTES, P_PARTITION),
        (R_ACG_1_A_ID, r_adapter, R_ACG_1_A_BYTES, R_A_PARTITION),
        (R_ACG_1_B_ID, r_adapter, R_ACG_1_B_BYTES, R_B_PARTITION),
    )
    return tuple(
        GeneratedCompleteCase(
            family_id,
            adapter,
            source,
            partition,
            adapter.adapt_complete(source, partition, split_manifest),
        )
        for family_id, adapter, source, partition in values
    )


def production_inventory_crosscheck(
    adapter: object, source_bytes: bytes
) -> SourceInventory:
    if type(adapter) is GeneratedHAdapter:
        return production_h_inventory_crosscheck(source_bytes)
    if type(adapter) is GeneratedMAdapter:
        return production_m_inventory_crosscheck(source_bytes)
    if type(adapter) is GeneratedPAdapter:
        return production_p_inventory_crosscheck(source_bytes)
    if type(adapter) is GeneratedRAdapter:
        return production_r_inventory_crosscheck(source_bytes)
    raise TypeError("adapter is not an exact generated adapter")


def production_reconstruction_crosscheck(
    adapter: object, source_bytes: bytes
) -> SemanticReconstruction:
    if type(adapter) is GeneratedHAdapter:
        return production_h_reconstruction_crosscheck(source_bytes)
    if type(adapter) is GeneratedMAdapter:
        return production_m_reconstruction_crosscheck(source_bytes)
    if type(adapter) is GeneratedPAdapter:
        return production_p_reconstruction_crosscheck(source_bytes)
    if type(adapter) is GeneratedRAdapter:
        return production_r_reconstruction_crosscheck(source_bytes)
    raise TypeError("adapter is not an exact generated adapter")


__all__ = [
    "END_OF_STREAM_EXCLUSION_REASON",
    "GENERATED_ADAPTER_VERSION",
    "GENERATED_CENSOR_REASON_CODES",
    "GENERATED_CONFORMANCE_SPLIT_MANIFEST",
    "GENERATED_EXCLUSION_REASON_CODES",
    "GeneratedCompleteCase",
    "GeneratedConformanceAdapterError",
    "GeneratedHAdapter",
    "GeneratedMAdapter",
    "GeneratedPAdapter",
    "GeneratedRAdapter",
    "H_ADAPTER_ID",
    "H_GROUP_ID",
    "H_PARTITION",
    "H_POLICY_SHA256",
    "M_ADAPTER_ID",
    "M_GROUP_ID",
    "M_PARTITION",
    "M_POLICY_SHA256",
    "P_ADAPTER_ID",
    "P_GROUP_ID",
    "P_PARTITION",
    "P_POLICY_SHA256",
    "PARTITION_IDENTITY_EXCLUSION_REASON",
    "R_ADAPTER_ID",
    "R_A_PARTITION",
    "R_B_PARTITION",
    "R_POLICY_SHA256",
    "build_all_generated_complete_cases",
    "build_h_complete_sample",
    "build_m_complete_sample",
    "build_p_complete_sample",
    "build_r_a_complete_sample",
    "build_r_b_complete_sample",
    "generated_conformance_split_manifest",
    "production_h_inventory_crosscheck",
    "production_h_reconstruction_crosscheck",
    "production_inventory_crosscheck",
    "production_m_inventory_crosscheck",
    "production_m_reconstruction_crosscheck",
    "production_p_inventory_crosscheck",
    "production_p_reconstruction_crosscheck",
    "production_r_inventory_crosscheck",
    "production_r_reconstruction_crosscheck",
    "production_reconstruction_crosscheck",
]
