"""Exact generated fixtures for the cross-domain atomic-counting gate.

This module deliberately stops at a lossless representation boundary.  MIDI
and CSV have separate raw parsers and semantic policies; both produce the same
small :class:`CountingFixtureResult` contract only after their domain-specific
checks pass.  The objects here are generated test fixtures.  They are not
official MAESTRO or PhysioNet records, training data, empirical results, or
evidence of clinical validity or cross-domain generalization.

Private provenance objects retain the information needed to reconstruct every
source byte.  They must not be confused with model inputs.  Event identifiers,
raw rows, MIDI event provenance, sample identifiers, group identifiers, and
split labels are excluded from :meth:`EventConfiguration.state_key` and from
the numerical model arrays of :class:`AtomicCountingGridTensor`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import hashlib
from numbers import Integral
from typing import Dict, Optional, Sequence, Tuple, Union

from heterodiff.events import (
    ContinuousField,
    Event,
    EventConfiguration,
    EventObservation,
    EventTypeSchema,
    FeatureSchema,
    MultiplicityMode,
    ObservationPattern,
    SupportKind,
    TimeMeasureKind,
    TimeReference,
)

from .atomic_counting_grid import AtomicCountingGridTensor
from .maestro_semantics import (
    MaestroNoteOnset,
    MaestroSemanticLimits,
    MaestroSemanticPiece,
    build_maestro_semantics,
)
from .midi_raw import MidiChannelEvent, MidiFile, MidiParseLimits, parse_midi_bytes
from .physionet_2012_adapter import (
    PhysioNet2012AdmissionValue,
    PhysioNet2012EventSidecar,
    PhysioNet2012MissingRule,
    PhysioNet2012ParameterSpec,
)
from .physionet_2012_raw import (
    DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS,
    DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS,
    PhysioNet2012IngestionConfig,
    PhysioNet2012Record,
    PhysioNet2012Row,
    parse_physionet_2012_record,
)


M_ACG_1_ID = "M-ACG-1"
M_ACG_1_HEX = (
    "4d546864000000060000000101e04d54726b0000002b00ff510307a12000903c400090"
    "3c400090406078803c0000803c00008040003c90437f3c80430000ff2f00"
)
M_ACG_1_BYTES = bytes.fromhex(M_ACG_1_HEX)
M_ACG_1_SHA256 = "5526627c28764a13534549c46353dc15f65fde3b00e7b91e1cc4a1cd1b38457d"

P_ACG_1_ID = "P-ACG-1"
P_ACG_1_TEXT = (
    "Time,Parameter,Value\n"
    "00:00,RecordID,900001\n"
    "00:00,Age,54\n"
    "00:00,Gender,0\n"
    "00:00,Height,-1\n"
    "00:00,ICUType,4\n"
    "00:00,Weight,-1\n"
    "00:05,HR,80\n"
    "00:05,HR,80.0\n"
    "00:05,Temp,37.0\n"
    "00:06,Urine,120\n"
    "00:07,Weight,81.5\n"
    "00:08,HR,-1\n"
)
P_ACG_1_BYTES = P_ACG_1_TEXT.encode("utf-8")
P_ACG_1_SHA256 = "f75b1604bed422d4af8290bb5356ec4212f18c3020d772f7022611aa9c551ad4"


PUBLIC_GENERATED_FIXTURE_NOTICE = (
    "M-ACG-1 and P-ACG-1 are generated representation fixtures only. "
    "P-ACG-1 identifier 900001 is synthetic and must never be matched to or "
    "represented as an official patient. No official PhysioNet record, patient "
    "value, outcome, path, or converted tensor is included. A fixture check is "
    "not a clinical result, an official-data experiment, a model-quality result, "
    "or evidence of cross-domain generalization."
)


class CountingFixtureError(ValueError):
    """Raised when a generated source violates its frozen fixture policy."""


class CountingFixtureResourceError(CountingFixtureError):
    """Raised before a predeclared fixture resource ceiling is exceeded."""


class CountingFixtureDomain(str, Enum):
    MUSIC = "music"
    CLINICAL_STYLE = "clinical_style"


def _positive_plain_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer".format(name))
    result = int(value)
    if result <= 0:
        raise ValueError("{} must be positive".format(name))
    return result


@dataclass(frozen=True)
class CountingFixtureResourceLimits:
    """Static and streaming ceilings frozen before parsing one fixture.

    The names match the resource table in the pre-registration.  Byte and
    declared-axis checks run before the corresponding parser or allocation;
    parsed-item and semantic-occurrence checks are enforced as stream/output
    counters.  These are fixture limits, not recommendations for official
    datasets.
    """

    maximum_source_bytes: int
    maximum_source_tracks_or_records: int
    maximum_parsed_source_items: int
    maximum_semantic_target_occurrences: int
    maximum_atomic_time_positions: int
    maximum_declared_event_types: int
    maximum_occurrences_per_cell: int
    maximum_mark_scalar_dimensions_per_occurrence: int
    maximum_reference_time_positions: int

    def __post_init__(self) -> None:
        for name in (
            "maximum_source_bytes",
            "maximum_source_tracks_or_records",
            "maximum_parsed_source_items",
            "maximum_semantic_target_occurrences",
            "maximum_atomic_time_positions",
            "maximum_declared_event_types",
            "maximum_occurrences_per_cell",
            "maximum_mark_scalar_dimensions_per_occurrence",
            "maximum_reference_time_positions",
        ):
            object.__setattr__(
                self,
                name,
                _positive_plain_int(getattr(self, name), name=name),
            )
        if self.maximum_atomic_time_positions > self.maximum_reference_time_positions:
            raise ValueError(
                "maximum_atomic_time_positions cannot exceed "
                "maximum_reference_time_positions"
            )
        if (
            self.maximum_occurrences_per_cell
            > self.maximum_semantic_target_occurrences
        ):
            raise ValueError(
                "maximum_occurrences_per_cell cannot exceed the occurrence ceiling"
            )
        if (
            self.maximum_semantic_target_occurrences
            > self.maximum_parsed_source_items
        ):
            raise ValueError(
                "maximum_semantic_target_occurrences cannot exceed the parsed-item "
                "ceiling"
            )

    def as_dict(self) -> Dict[str, int]:
        return {
            name: getattr(self, name)
            for name in (
                "maximum_source_bytes",
                "maximum_source_tracks_or_records",
                "maximum_parsed_source_items",
                "maximum_semantic_target_occurrences",
                "maximum_atomic_time_positions",
                "maximum_declared_event_types",
                "maximum_occurrences_per_cell",
                "maximum_mark_scalar_dimensions_per_occurrence",
                "maximum_reference_time_positions",
            )
        }


M_ACG_1_RESOURCE_LIMITS = CountingFixtureResourceLimits(
    maximum_source_bytes=128,
    maximum_source_tracks_or_records=1,
    maximum_parsed_source_items=16,
    maximum_semantic_target_occurrences=8,
    maximum_atomic_time_positions=16,
    maximum_declared_event_types=88,
    maximum_occurrences_per_cell=2,
    maximum_mark_scalar_dimensions_per_occurrence=2,
    maximum_reference_time_positions=256,
)

P_ACG_1_RESOURCE_LIMITS = CountingFixtureResourceLimits(
    maximum_source_bytes=512,
    maximum_source_tracks_or_records=1,
    maximum_parsed_source_items=32,
    maximum_semantic_target_occurrences=16,
    maximum_atomic_time_positions=2881,
    maximum_declared_event_types=4,
    maximum_occurrences_per_cell=2,
    maximum_mark_scalar_dimensions_per_occurrence=1,
    maximum_reference_time_positions=2881,
)


M_ACG_1_MIDI_PARSE_LIMITS = MidiParseLimits(
    maximum_file_bytes=128,
    maximum_tracks=1,
    maximum_track_bytes=128,
    maximum_event_payload_bytes=128,
    maximum_events_per_track=16,
    maximum_total_events=16,
    maximum_absolute_tick=2880,
    maximum_ticks_per_quarter_note=480,
)

M_ACG_1_MAESTRO_SEMANTIC_LIMITS = MaestroSemanticLimits(
    maximum_tracks=1,
    maximum_total_events=16,
    maximum_note_events=16,
    maximum_note_onsets=8,
    maximum_open_notes=8,
    maximum_atomic_note_events=8,
    maximum_tempo_events=4,
    maximum_tempo_points=5,
    maximum_control_changes=16,
    maximum_midi_port_events=4,
    maximum_time_signatures=4,
)


P_ACG_1_ADMISSION_MISSING_RULES = tuple(
    PhysioNet2012MissingRule(parameter, (Decimal("-1"),))
    for parameter in sorted(
        DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS - {"RecordID"}
    )
)

P_ACG_1_PARAMETER_SPECS = (
    PhysioNet2012ParameterSpec(
        "HR",
        0,
        SupportKind.POSITIVE,
        (Decimal("-1"),),
        unit="beats/minute",
    ),
    PhysioNet2012ParameterSpec(
        "Temp",
        1,
        SupportKind.REAL,
        (Decimal("-1"),),
        unit="degC",
    ),
    PhysioNet2012ParameterSpec(
        "Urine",
        2,
        SupportKind.POSITIVE,
        (Decimal("-1"),),
        unit="mL",
    ),
    PhysioNet2012ParameterSpec(
        "Weight",
        3,
        SupportKind.POSITIVE,
        (Decimal("-1"),),
        unit="kg",
    ),
)


def _validate_text_identity(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(name))
    if not value or value != value.strip():
        raise ValueError("{} must be a nonempty, whitespace-trimmed string".format(name))
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise ValueError("{} must not contain NUL or newlines".format(name))
    return value


def _validate_source_split(value: object) -> str:
    split = _validate_text_identity(value, name="source_split")
    if split not in {"train", "validation", "test"}:
        raise ValueError("source_split must be train, validation, or test")
    return split


def _validate_sha256(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(name))
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("{} must be a lowercase SHA-256 digest".format(name))
    return value


def _preflight_source_bytes(
    source_bytes: object,
    *,
    limits: CountingFixtureResourceLimits,
    expected_sha256: Optional[str],
) -> Tuple[bytes, str]:
    if type(source_bytes) is not bytes:
        raise TypeError("source_bytes must be exact bytes")
    if type(limits) is not CountingFixtureResourceLimits:
        raise TypeError("limits must be an exact CountingFixtureResourceLimits instance")
    if len(source_bytes) > limits.maximum_source_bytes:
        raise CountingFixtureResourceError(
            "source byte length {} exceeds predeclared ceiling {}".format(
                len(source_bytes), limits.maximum_source_bytes
            )
        )
    digest = hashlib.sha256(source_bytes).hexdigest()
    if expected_sha256 is not None:
        expected = _validate_sha256(expected_sha256, name="expected_sha256")
        if digest != expected:
            raise CountingFixtureError(
                "source SHA-256 mismatch: expected {}, got {}".format(expected, digest)
            )
    return source_bytes, digest


def _validate_event_order(
    value: Optional[Sequence[int]], number_of_events: int
) -> Tuple[int, ...]:
    if value is None:
        return tuple(range(number_of_events))
    if isinstance(value, (str, bytes)):
        raise TypeError("source_event_order must be a sequence of integer indices")
    try:
        order = tuple(value)
    except TypeError as exc:
        raise TypeError(
            "source_event_order must be a sequence of integer indices"
        ) from exc
    if any(isinstance(index, bool) or not isinstance(index, Integral) for index in order):
        raise TypeError("source_event_order must contain only integer indices")
    normalized = tuple(int(index) for index in order)
    if sorted(normalized) != list(range(number_of_events)):
        raise ValueError("source_event_order must be a complete event permutation")
    return normalized


def _reconstruct_midi_bytes(midi: MidiFile) -> bytes:
    chunks = [
        b"MThd"
        + (6).to_bytes(4, "big")
        + midi.format_type.to_bytes(2, "big")
        + len(midi.tracks).to_bytes(2, "big")
        + midi.ticks_per_quarter_note.to_bytes(2, "big")
    ]
    for track in midi.tracks:
        payload = b"".join(event.encoded_bytes for event in track.events)
        chunks.append(b"MTrk" + len(payload).to_bytes(4, "big") + payload)
    return b"".join(chunks)


def _reconstruct_clinical_bytes(record: PhysioNet2012Record) -> bytes:
    lines = ["Time,Parameter,Value"]
    lines.extend(",".join(row.csv_cells) for row in record.rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


@dataclass(frozen=True)
class MusicFixturePrivateProvenance:
    """Private exact MIDI parse and semantic sidecars for one music result."""

    raw_midi: MidiFile
    semantic_piece: MaestroSemanticPiece
    event_notes: Tuple[MaestroNoteOnset, ...]

    def __post_init__(self) -> None:
        if type(self.raw_midi) is not MidiFile:
            raise TypeError("raw_midi must be an exact MidiFile instance")
        if type(self.semantic_piece) is not MaestroSemanticPiece:
            raise TypeError(
                "semantic_piece must be an exact MaestroSemanticPiece instance"
            )
        notes = tuple(self.event_notes)
        if any(type(note) is not MaestroNoteOnset for note in notes):
            raise TypeError("event_notes must contain exact MaestroNoteOnset values")
        object.__setattr__(self, "event_notes", notes)
        if self.semantic_piece.source_midi_sha256 != self.raw_midi.sha256:
            raise ValueError("semantic source digest disagrees with the parsed MIDI")
        rebuilt_semantics = build_maestro_semantics(
            self.raw_midi,
            source_split=self.semantic_piece.source_split,
            limits=M_ACG_1_MAESTRO_SEMANTIC_LIMITS,
        )
        if self.semantic_piece != rebuilt_semantics:
            raise ValueError(
                "semantic_piece must be the exact frozen-policy reconstruction "
                "of raw_midi"
            )
        semantic_ids = tuple(note.note_id for note in self.semantic_piece.notes)
        event_ids = tuple(note.note_id for note in notes)
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("music event provenance note ids must be unique")
        if set(event_ids) != set(semantic_ids) or len(event_ids) != len(semantic_ids):
            raise ValueError("music event provenance must cover every semantic note")
        semantic_by_id = {
            note.note_id: note for note in self.semantic_piece.notes
        }
        if any(note != semantic_by_id[note.note_id] for note in notes):
            raise ValueError(
                "music event provenance must contain the exact semantic note rows"
            )

    def reconstruct_source_bytes(self) -> bytes:
        return _reconstruct_midi_bytes(self.raw_midi)


@dataclass(frozen=True)
class ClinicalFixturePrivateProvenance:
    """Private exact CSV rows, admission context, and event sidecars."""

    raw_record: PhysioNet2012Record
    admission_values: Tuple[PhysioNet2012AdmissionValue, ...]
    event_sidecars: Tuple[PhysioNet2012EventSidecar, ...]

    def __post_init__(self) -> None:
        if type(self.raw_record) is not PhysioNet2012Record:
            raise TypeError("raw_record must be an exact PhysioNet2012Record instance")
        admission_values = tuple(self.admission_values)
        event_sidecars = tuple(self.event_sidecars)
        if any(type(value) is not PhysioNet2012AdmissionValue for value in admission_values):
            raise TypeError(
                "admission_values must contain exact PhysioNet2012AdmissionValue values"
            )
        if any(type(value) is not PhysioNet2012EventSidecar for value in event_sidecars):
            raise TypeError(
                "event_sidecars must contain exact PhysioNet2012EventSidecar values"
            )
        object.__setattr__(self, "admission_values", admission_values)
        object.__setattr__(self, "event_sidecars", event_sidecars)

        expected_admission_lines = {
            row.line_number
            for row in self.raw_record.admission_descriptor_rows
            if row.parameter != "RecordID"
        }
        actual_admission_lines = {
            value.source_row.line_number for value in admission_values
        }
        if (
            len(actual_admission_lines) != len(admission_values)
            or actual_admission_lines != expected_admission_lines
        ):
            raise ValueError(
                "admission sidecars must cover every non-ID context row exactly once"
            )
        raw_rows_by_line = {
            row.line_number: row for row in self.raw_record.rows
        }
        if any(
            raw_rows_by_line.get(value.source_row.line_number) != value.source_row
            for value in admission_values
        ):
            raise ValueError(
                "admission sidecars must contain the exact rows from raw_record"
            )
        expected_event_lines = {
            row.line_number for row in self.raw_record.observation_rows
        }
        actual_event_lines = {
            sidecar.source_row.line_number for sidecar in event_sidecars
        }
        if len(actual_event_lines) != len(event_sidecars):
            raise ValueError("clinical event sidecars repeat a physical line")
        if actual_event_lines != expected_event_lines:
            raise ValueError("clinical event sidecars do not cover every event row")
        if any(
            raw_rows_by_line.get(sidecar.source_row.line_number)
            != sidecar.source_row
            for sidecar in event_sidecars
        ):
            raise ValueError(
                "clinical event sidecars must contain the exact rows from raw_record"
            )

        rule_by_name = {
            rule.parameter: rule for rule in P_ACG_1_ADMISSION_MISSING_RULES
        }
        for value in admission_values:
            expected_missing = rule_by_name[value.parameter].is_missing(
                value.source_row.value
            )
            if value.is_missing != expected_missing:
                raise ValueError(
                    "admission sidecar disagrees with the frozen sentinel policy"
                )
        spec_by_name = {
            spec.parameter: spec for spec in P_ACG_1_PARAMETER_SPECS
        }
        for sidecar in event_sidecars:
            spec = spec_by_name.get(sidecar.source_row.parameter)
            if spec is None:
                raise ValueError(
                    "event sidecar parameter is absent from the frozen codebook"
                )
            if sidecar.value_missing != spec.is_missing(sidecar.source_row.value):
                raise ValueError(
                    "event sidecar disagrees with the frozen sentinel policy"
                )
            expected_event_id = (
                "physionet-2012-row",
                self.raw_record.record_id,
                sidecar.source_row.line_number,
            )
            if sidecar.event_id != expected_event_id:
                raise ValueError(
                    "clinical event sidecar id must bind the raw record and line"
                )

    @property
    def admission_rows(self) -> Tuple[PhysioNet2012Row, ...]:
        return self.raw_record.admission_descriptor_rows

    def round_trip_rows(self) -> Tuple[PhysioNet2012Row, ...]:
        rows = self.raw_record.admission_descriptor_rows + tuple(
            sidecar.source_row for sidecar in self.event_sidecars
        )
        return tuple(sorted(rows, key=lambda row: row.line_number))

    def reconstruct_source_bytes(self) -> bytes:
        return _reconstruct_clinical_bytes(self.raw_record)


PrivateFixtureProvenance = Union[
    MusicFixturePrivateProvenance, ClinicalFixturePrivateProvenance
]


@dataclass(frozen=True)
class CountingFixtureResult:
    """Shared validated output of the two separate generated-source adapters."""

    fixture_id: str
    domain: CountingFixtureDomain
    source_format: str
    source_split: str
    source_sha256: str
    source_byte_length: int
    configuration: EventConfiguration
    private_provenance: PrivateFixtureProvenance
    resource_limits: CountingFixtureResourceLimits
    public_notice: str = PUBLIC_GENERATED_FIXTURE_NOTICE

    def __post_init__(self) -> None:
        fixture_id = _validate_text_identity(self.fixture_id, name="fixture_id")
        object.__setattr__(self, "fixture_id", fixture_id)
        if type(self.domain) is not CountingFixtureDomain:
            raise TypeError("domain must be an exact CountingFixtureDomain value")
        object.__setattr__(
            self,
            "source_format",
            _validate_text_identity(self.source_format, name="source_format"),
        )
        object.__setattr__(self, "source_split", _validate_source_split(self.source_split))
        object.__setattr__(
            self,
            "source_sha256",
            _validate_sha256(self.source_sha256, name="source_sha256"),
        )
        if isinstance(self.source_byte_length, bool) or not isinstance(
            self.source_byte_length, Integral
        ):
            raise TypeError("source_byte_length must be an integer")
        source_byte_length = int(self.source_byte_length)
        if source_byte_length <= 0:
            raise ValueError("source_byte_length must be positive")
        object.__setattr__(self, "source_byte_length", source_byte_length)
        if type(self.configuration) is not EventConfiguration:
            raise TypeError(
                "configuration must be an exact EventConfiguration instance"
            )
        if type(self.resource_limits) is not CountingFixtureResourceLimits:
            raise TypeError(
                "resource_limits must be an exact CountingFixtureResourceLimits instance"
            )
        if self.public_notice != PUBLIC_GENERATED_FIXTURE_NOTICE:
            raise ValueError("public_notice must retain the frozen generated-fixture boundary")

        configuration = self.configuration
        configuration.validate()
        if (
            configuration.observed is None
            or not configuration.observed.cardinality_observed
        ):
            raise ValueError(
                "fixture source cardinality must remain explicitly observed"
            )
        schema = configuration.schema
        if source_byte_length > self.resource_limits.maximum_source_bytes:
            raise CountingFixtureResourceError("source byte ceiling was exceeded")
        if schema.time_measure is not TimeMeasureKind.ATOMIC:
            raise ValueError("fixture configuration must use atomic time")
        if schema.multiplicity_mode is not MultiplicityMode.FINITE_COUNTING:
            raise ValueError("fixture configuration must use FINITE_COUNTING")
        assert schema.time_reference is not None
        if len(schema.time_reference.atoms) > self.resource_limits.maximum_atomic_time_positions:
            raise CountingFixtureResourceError("atomic time-axis ceiling was exceeded")
        if len(schema.event_types) > self.resource_limits.maximum_declared_event_types:
            raise CountingFixtureResourceError("declared event-type ceiling was exceeded")
        if len(configuration.events) > self.resource_limits.maximum_semantic_target_occurrences:
            raise CountingFixtureResourceError("semantic occurrence ceiling was exceeded")
        maximum_dimension = max(
            sum(field.dimension for field in event_type.fields)
            for event_type in schema.event_types
        )
        if (
            maximum_dimension
            > self.resource_limits.maximum_mark_scalar_dimensions_per_occurrence
        ):
            raise CountingFixtureResourceError("mark-dimension ceiling was exceeded")
        maximum_multiplicity = max(self.occupied_cell_counts.values(), default=0)
        if maximum_multiplicity > self.resource_limits.maximum_occurrences_per_cell:
            raise CountingFixtureResourceError("per-cell occurrence ceiling was exceeded")

        if self.domain is CountingFixtureDomain.MUSIC:
            if type(self.private_provenance) is not MusicFixturePrivateProvenance:
                raise TypeError("music result requires MusicFixturePrivateProvenance")
            self._validate_music_alignment(self.private_provenance)
        else:
            if type(self.private_provenance) is not ClinicalFixturePrivateProvenance:
                raise TypeError(
                    "clinical-style result requires ClinicalFixturePrivateProvenance"
                )
            self._validate_clinical_alignment(self.private_provenance)

        reserved_identity = {
            M_ACG_1_ID: {
                "domain": CountingFixtureDomain.MUSIC,
                "source_format": "standard-midi-file-format-0-ppq",
                "source_split": "train",
                "source_sha256": M_ACG_1_SHA256,
                "source_byte_length": len(M_ACG_1_BYTES),
                "sample_id": M_ACG_1_ID,
                "group_id": "synthetic-maestro-group-1",
                "resource_limits": M_ACG_1_RESOURCE_LIMITS,
            },
            P_ACG_1_ID: {
                "domain": CountingFixtureDomain.CLINICAL_STYLE,
                "source_format": "physionet-2012-style-utf8-lf-csv",
                "source_split": "train",
                "source_sha256": P_ACG_1_SHA256,
                "source_byte_length": len(P_ACG_1_BYTES),
                "sample_id": "900001",
                "group_id": "900001",
                "resource_limits": P_ACG_1_RESOURCE_LIMITS,
            },
        }.get(self.fixture_id)
        if reserved_identity is not None:
            actual_identity = {
                "domain": self.domain,
                "source_format": self.source_format,
                "source_split": self.source_split,
                "source_sha256": self.source_sha256,
                "source_byte_length": self.source_byte_length,
                "sample_id": self.configuration.sample_id,
                "group_id": self.configuration.group_id,
                "resource_limits": self.resource_limits,
            }
            if actual_identity != reserved_identity:
                raise ValueError(
                    "reserved fixture id {!r} requires its exact frozen source, "
                    "domain, split, sample, and group identity".format(
                        self.fixture_id
                    )
                )

        reconstructed = self.reconstruct_source_bytes()
        if len(reconstructed) != source_byte_length:
            raise ValueError("source_byte_length disagrees with private reconstruction")
        if hashlib.sha256(reconstructed).hexdigest() != self.source_sha256:
            raise ValueError("source_sha256 disagrees with private reconstruction")

    def _validate_music_alignment(
        self, provenance: MusicFixturePrivateProvenance
    ) -> None:
        if self.source_format != "standard-midi-file-format-0-ppq":
            raise ValueError("music source_format is not the frozen format")
        if self.configuration.schema != _music_schema(self.resource_limits):
            raise ValueError("music configuration schema is not the frozen fixture schema")
        if provenance.semantic_piece.source_split != self.source_split:
            raise ValueError("music semantic split disagrees with the result split")
        if (
            provenance.raw_midi.track_count
            > self.resource_limits.maximum_source_tracks_or_records
        ):
            raise CountingFixtureResourceError("parsed MIDI track ceiling was exceeded")
        if (
            provenance.raw_midi.total_events
            > self.resource_limits.maximum_parsed_source_items
        ):
            raise CountingFixtureResourceError("parsed MIDI event ceiling was exceeded")
        note_by_id = {note.note_id: note for note in provenance.event_notes}
        configuration_ids = tuple(
            event.event_id for event in self.configuration.events
        )
        if len(configuration_ids) != len(provenance.event_notes) or set(
            configuration_ids
        ) != set(note_by_id):
            raise ValueError("music configuration must contain every semantic onset once")
        if tuple(note.note_id for note in provenance.event_notes) != configuration_ids:
            raise ValueError(
                "music event provenance must align exactly with configuration order"
            )
        assert self.configuration.observed is not None
        for event, observation in zip(
            self.configuration.events, self.configuration.observed.events
        ):
            note = note_by_id.get(event.event_id)
            if note is None:
                raise ValueError("music event lacks exact note provenance")
            expected_marks = {
                "midi_clock_onset_offset": (note.midi_clock_onset_offset,),
                "velocity_normalized": (note.velocity_normalized,),
            }
            if (
                event.event_time != float(note.grid_index)
                or event.event_type != note.pitch
                or dict(event.marks) != expected_marks
            ):
                raise ValueError("music event disagrees with its semantic note")
            if observation != EventObservation(
                time_observed=True,
                type_observed=True,
                observed_marks=frozenset(expected_marks),
            ):
                raise ValueError("music source-observation mask is not exact")

    def _validate_clinical_alignment(
        self, provenance: ClinicalFixturePrivateProvenance
    ) -> None:
        if self.source_format != "physionet-2012-style-utf8-lf-csv":
            raise ValueError("clinical source_format is not the frozen format")
        if self.configuration.schema != _clinical_schema(self.resource_limits):
            raise ValueError(
                "clinical configuration schema is not the frozen fixture schema"
            )
        if (
            len(provenance.raw_record.rows)
            > self.resource_limits.maximum_parsed_source_items
        ):
            raise CountingFixtureResourceError("parsed CSV data-row ceiling was exceeded")
        sidecar_by_id = {
            sidecar.event_id: sidecar for sidecar in provenance.event_sidecars
        }
        configuration_ids = tuple(
            event.event_id for event in self.configuration.events
        )
        if len(configuration_ids) != len(provenance.event_sidecars) or set(
            configuration_ids
        ) != set(sidecar_by_id):
            raise ValueError("clinical configuration must contain every event row once")
        if (
            tuple(sidecar.event_id for sidecar in provenance.event_sidecars)
            != configuration_ids
        ):
            raise ValueError(
                "clinical event sidecars must align exactly with configuration order"
            )
        assert self.configuration.observed is not None
        for event, observation in zip(
            self.configuration.events, self.configuration.observed.events
        ):
            sidecar = sidecar_by_id.get(event.event_id)
            if sidecar is None:
                raise ValueError("clinical event lacks exact row provenance")
            row = sidecar.source_row
            event_type = self.configuration.schema.event_type(event.event_type)
            expected_marks = {} if sidecar.value_missing else {"value": (float(row.value),)}
            if (
                event.event_time != float(row.elapsed_minutes)
                or event_type.name != row.parameter
                or dict(event.marks) != expected_marks
            ):
                raise ValueError("clinical event disagrees with its exact source row")
            expected_observation = EventObservation(
                time_observed=True,
                type_observed=True,
                observed_marks=(
                    frozenset() if sidecar.value_missing else frozenset({"value"})
                ),
            )
            if observation != expected_observation:
                raise ValueError("clinical source-observation mask is not exact")

    @property
    def observation_pattern(self) -> ObservationPattern:
        assert self.configuration.observed is not None
        return self.configuration.observed

    @property
    def event_provenance(self) -> Tuple[object, ...]:
        if self.domain is CountingFixtureDomain.MUSIC:
            assert type(self.private_provenance) is MusicFixturePrivateProvenance
            return tuple(self.private_provenance.event_notes)
        assert type(self.private_provenance) is ClinicalFixturePrivateProvenance
        return tuple(self.private_provenance.event_sidecars)

    @property
    def admission_context(self) -> Tuple[object, ...]:
        if self.domain is CountingFixtureDomain.MUSIC:
            return ()
        assert type(self.private_provenance) is ClinicalFixturePrivateProvenance
        return tuple(self.private_provenance.admission_values)

    @property
    def occupied_cell_counts(self) -> Dict[Tuple[float, int], int]:
        counts = Counter(
            (event.event_time, event.event_type)
            for event in self.configuration.events
        )
        return dict(sorted(counts.items()))

    @property
    def occupied_cell_multiplicity_histogram(self) -> Dict[int, int]:
        return dict(sorted(Counter(self.occupied_cell_counts.values()).items()))

    def reconstruct_source_bytes(self) -> bytes:
        return self.private_provenance.reconstruct_source_bytes()

    def to_atomic_counting_grid(
        self, *, max_occurrences_per_cell: Optional[int] = None
    ) -> AtomicCountingGridTensor:
        capacity = (
            self.resource_limits.maximum_occurrences_per_cell
            if max_occurrences_per_cell is None
            else _positive_plain_int(
                max_occurrences_per_cell, name="max_occurrences_per_cell"
            )
        )
        required = max(self.occupied_cell_counts.values(), default=0)
        if capacity < required:
            raise CountingFixtureResourceError(
                "fixture requires {} occurrences in one cell; capacity {} would "
                "truncate it".format(required, capacity)
            )
        if capacity > self.resource_limits.maximum_occurrences_per_cell:
            raise CountingFixtureResourceError(
                "requested capacity {} exceeds predeclared ceiling {}".format(
                    capacity,
                    self.resource_limits.maximum_occurrences_per_cell,
                )
            )
        return AtomicCountingGridTensor.from_configuration(
            self.configuration,
            max_occurrences_per_cell=capacity,
        )


def _music_schema(limits: CountingFixtureResourceLimits) -> FeatureSchema:
    required_time_positions = 2
    required_event_types = 88
    required_mark_dimensions = 2
    if required_time_positions > limits.maximum_atomic_time_positions:
        raise CountingFixtureResourceError(
            "music atomic time-axis exceeds the predeclared ceiling"
        )
    if required_event_types > limits.maximum_declared_event_types:
        raise CountingFixtureResourceError(
            "music event-type axis exceeds the predeclared ceiling"
        )
    if (
        required_mark_dimensions
        > limits.maximum_mark_scalar_dimensions_per_occurrence
    ):
        raise CountingFixtureResourceError(
            "music per-occurrence mark dimension exceeds the predeclared ceiling"
        )
    if 256 > limits.maximum_reference_time_positions:
        raise CountingFixtureResourceError(
            "music reference time-axis exceeds the predeclared ceiling"
        )
    velocity = ContinuousField(
        "velocity_normalized",
        support=SupportKind.POSITIVE,
        unit="midi-velocity/127",
    )
    offset = ContinuousField(
        "midi_clock_onset_offset",
        support=SupportKind.REAL,
        unit="midi-clock-grid-width",
    )
    return FeatureSchema(
        event_types=tuple(
            EventTypeSchema(
                pitch,
                "midi_pitch_{}".format(pitch),
                (velocity, offset),
            )
            for pitch in range(21, 109)
        ),
        horizon=1.0,
        time_measure=TimeMeasureKind.ATOMIC,
        time_reference=TimeReference.atomic((0.0, 1.0), (1.0, 1.0)),
        allow_simultaneous=True,
        multiplicity_mode=MultiplicityMode.FINITE_COUNTING,
        version="maestro-midi-clock-counting-fixture-v1",
    )


def _music_parser_limits(
    limits: CountingFixtureResourceLimits,
) -> MidiParseLimits:
    return MidiParseLimits(
        maximum_file_bytes=limits.maximum_source_bytes,
        maximum_tracks=limits.maximum_source_tracks_or_records,
        maximum_track_bytes=limits.maximum_source_bytes,
        maximum_event_payload_bytes=limits.maximum_source_bytes,
        maximum_events_per_track=limits.maximum_parsed_source_items,
        maximum_total_events=limits.maximum_parsed_source_items,
        maximum_absolute_tick=M_ACG_1_MIDI_PARSE_LIMITS.maximum_absolute_tick,
        maximum_ticks_per_quarter_note=(
            M_ACG_1_MIDI_PARSE_LIMITS.maximum_ticks_per_quarter_note
        ),
    )


def _music_semantic_limits(
    limits: CountingFixtureResourceLimits,
) -> MaestroSemanticLimits:
    semantic_cap = limits.maximum_semantic_target_occurrences
    event_cap = limits.maximum_parsed_source_items
    atomic_cap = min(event_cap, semantic_cap)
    return MaestroSemanticLimits(
        maximum_tracks=limits.maximum_source_tracks_or_records,
        maximum_total_events=event_cap,
        maximum_note_events=event_cap,
        maximum_note_onsets=semantic_cap,
        maximum_open_notes=semantic_cap,
        maximum_atomic_note_events=atomic_cap,
        maximum_tempo_events=min(event_cap, 4),
        maximum_tempo_points=min(event_cap + 1, 5),
        maximum_control_changes=event_cap,
        maximum_midi_port_events=min(event_cap, 4),
        maximum_time_signatures=min(event_cap, 4),
    )


def build_music_counting_fixture(
    source_bytes: bytes,
    *,
    fixture_id: str,
    expected_sha256: Optional[str],
    source_split: str,
    sample_id: str,
    group_id: str,
    limits: CountingFixtureResourceLimits = M_ACG_1_RESOURCE_LIMITS,
    source_event_order: Optional[Sequence[int]] = None,
) -> CountingFixtureResult:
    """Parse MIDI, apply frozen FIFO note semantics, and retain all onsets."""

    source, source_sha256 = _preflight_source_bytes(
        source_bytes,
        limits=limits,
        expected_sha256=expected_sha256,
    )
    fixture_id = _validate_text_identity(fixture_id, name="fixture_id")
    split = _validate_source_split(source_split)
    sample_id = _validate_text_identity(sample_id, name="sample_id")
    group_id = _validate_text_identity(group_id, name="group_id")

    midi = parse_midi_bytes(source, limits=_music_parser_limits(limits))
    if midi.track_count != 1 or midi.format_type != 0:
        raise CountingFixtureError("music fixture requires exactly one SMF format-0 track")
    if midi.ticks_per_quarter_note != 480:
        raise CountingFixtureError("music fixture requires exactly PPQN 480")
    if midi.total_events > limits.maximum_parsed_source_items:
        raise CountingFixtureResourceError("parsed MIDI event ceiling was exceeded")
    positive_onsets = 0
    for track in midi.tracks:
        for event in track.events:
            if (
                isinstance(event, MidiChannelEvent)
                and event.message_type == "note_on"
                and event.velocity is not None
                and event.velocity > 0
            ):
                positive_onsets += 1
                if positive_onsets > limits.maximum_semantic_target_occurrences:
                    raise CountingFixtureResourceError(
                        "semantic onset count exceeds the predeclared ceiling"
                    )
    semantics = build_maestro_semantics(
        midi,
        source_split=split,
        limits=_music_semantic_limits(limits),
    )
    if len(semantics.notes) > limits.maximum_semantic_target_occurrences:
        raise CountingFixtureResourceError("semantic onset ceiling was exceeded")
    if any(not 21 <= note.pitch <= 108 for note in semantics.notes):
        raise CountingFixtureError("music fixture contains a pitch outside the 88-key axis")
    if any(note.grid_index not in (0, 1) for note in semantics.notes):
        raise CountingFixtureError("music onset lies outside the two declared time atoms")

    order = _validate_event_order(source_event_order, len(semantics.notes))
    enumerated_notes = tuple(semantics.notes[index] for index in order)
    events = tuple(
        Event(
            event_time=float(note.grid_index),
            event_type=note.pitch,
            marks={
                "velocity_normalized": note.velocity_normalized,
                "midi_clock_onset_offset": note.midi_clock_onset_offset,
            },
            event_id=note.note_id,
        )
        for note in enumerated_notes
    )
    observations = tuple(
        EventObservation(
            time_observed=True,
            type_observed=True,
            observed_marks=frozenset(
                {"velocity_normalized", "midi_clock_onset_offset"}
            ),
        )
        for _ in events
    )
    configuration = EventConfiguration(
        schema=_music_schema(limits),
        events=events,
        observed=ObservationPattern(
            events=observations,
            cardinality_observed=True,
        ),
        sample_id=sample_id,
        group_id=group_id,
    )
    note_by_id = {note.note_id: note for note in enumerated_notes}
    event_notes = tuple(note_by_id[event.event_id] for event in configuration.events)
    provenance = MusicFixturePrivateProvenance(
        raw_midi=midi,
        semantic_piece=semantics,
        event_notes=event_notes,
    )
    return CountingFixtureResult(
        fixture_id=fixture_id,
        domain=CountingFixtureDomain.MUSIC,
        source_format="standard-midi-file-format-0-ppq",
        source_split=split,
        source_sha256=source_sha256,
        source_byte_length=len(source),
        configuration=configuration,
        private_provenance=provenance,
        resource_limits=limits,
    )


class _BoundedCsvTextStream:
    """Line iterator that enforces the row cap while csv.reader consumes it."""

    def __init__(self, text: str, maximum_data_rows: int) -> None:
        self._lines = iter(text.splitlines(keepends=True))
        self._line_number = 0
        self._maximum_data_rows = maximum_data_rows

    def __iter__(self) -> "_BoundedCsvTextStream":
        return self

    def __next__(self) -> str:
        line = next(self._lines)
        self._line_number += 1
        if self._line_number - 1 > self._maximum_data_rows:
            raise CountingFixtureResourceError(
                "CSV data-row count exceeds predeclared ceiling {}".format(
                    self._maximum_data_rows
                )
            )
        return line

    def read(self, size: int = -1) -> str:
        # parse_physionet_2012_record checks for a text-stream read method;
        # csv.reader consumes this object's bounded iterator instead.
        raise RuntimeError("bounded fixture stream supports iterator reads only")


def _clinical_schema(limits: CountingFixtureResourceLimits) -> FeatureSchema:
    required_time_positions = 2881
    required_event_types = len(P_ACG_1_PARAMETER_SPECS)
    if required_time_positions > limits.maximum_atomic_time_positions:
        raise CountingFixtureResourceError(
            "clinical atomic time-axis exceeds the predeclared ceiling"
        )
    if required_time_positions > limits.maximum_reference_time_positions:
        raise CountingFixtureResourceError(
            "clinical reference time-axis exceeds the predeclared ceiling"
        )
    if required_event_types > limits.maximum_declared_event_types:
        raise CountingFixtureResourceError(
            "clinical event-type axis exceeds the predeclared ceiling"
        )
    if 1 > limits.maximum_mark_scalar_dimensions_per_occurrence:
        raise CountingFixtureResourceError(
            "clinical mark dimension exceeds the predeclared ceiling"
        )
    atoms = tuple(float(minute) for minute in range(required_time_positions))
    return FeatureSchema(
        event_types=tuple(
            spec.event_type_schema() for spec in P_ACG_1_PARAMETER_SPECS
        ),
        horizon=2880.0,
        time_measure=TimeMeasureKind.ATOMIC,
        time_reference=TimeReference.atomic(atoms, (1.0,) * len(atoms)),
        allow_simultaneous=True,
        multiplicity_mode=MultiplicityMode.FINITE_COUNTING,
        version="physionet-2012-counting-fixture-v1",
    )


def _decode_clinical_source(source: bytes) -> str:
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CountingFixtureError("clinical source must be strict UTF-8") from exc
    if text.startswith("\ufeff"):
        raise CountingFixtureError("clinical generated fixture does not admit a BOM")
    if "\r" in text:
        raise CountingFixtureError("clinical generated fixture requires LF line endings")
    if not text.endswith("\n"):
        raise CountingFixtureError("clinical generated fixture requires a final LF")
    return text


def build_clinical_counting_fixture(
    source_bytes: bytes,
    *,
    fixture_id: str,
    expected_sha256: Optional[str],
    source_split: str,
    sample_id: Optional[str] = None,
    group_id: Optional[str] = None,
    limits: CountingFixtureResourceLimits = P_ACG_1_RESOURCE_LIMITS,
    source_event_order: Optional[Sequence[int]] = None,
) -> CountingFixtureResult:
    """Parse the generated CSV and preserve every observation as a count atom."""

    source, source_sha256 = _preflight_source_bytes(
        source_bytes,
        limits=limits,
        expected_sha256=expected_sha256,
    )
    fixture_id = _validate_text_identity(fixture_id, name="fixture_id")
    split = _validate_source_split(source_split)
    text = _decode_clinical_source(source)
    stream = _BoundedCsvTextStream(text, limits.maximum_parsed_source_items)
    record = parse_physionet_2012_record(
        stream,
        expected_record_id=None,
        config=PhysioNet2012IngestionConfig(
            admission_descriptors=DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS,
            dual_role_parameters=DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS,
            maximum_elapsed_minutes=2880,
        ),
    )
    if len(record.rows) > limits.maximum_parsed_source_items:
        raise CountingFixtureResourceError("parsed CSV data-row ceiling was exceeded")
    if _reconstruct_clinical_bytes(record) != source:
        raise CountingFixtureError(
            "clinical source is not the canonical UTF-8/LF three-cell fixture encoding"
        )
    for occurrence_index, _ in enumerate(record.observation_rows, start=1):
        if occurrence_index > limits.maximum_semantic_target_occurrences:
            raise CountingFixtureResourceError(
                "clinical event-row count exceeds the predeclared ceiling"
            )

    frozen_names = {spec.parameter for spec in P_ACG_1_PARAMETER_SPECS}
    observed_names = {row.parameter for row in record.observation_rows}
    unknown = observed_names - frozen_names
    if unknown:
        raise CountingFixtureError(
            "clinical source contains parameters absent from the train-frozen "
            "codebook: {}".format(", ".join(sorted(unknown)))
        )

    sample = record.record_id if sample_id is None else _validate_text_identity(
        sample_id, name="sample_id"
    )
    group = record.record_id if group_id is None else _validate_text_identity(
        group_id, name="group_id"
    )
    spec_by_name = {spec.parameter: spec for spec in P_ACG_1_PARAMETER_SPECS}
    rule_by_name = {
        rule.parameter: rule for rule in P_ACG_1_ADMISSION_MISSING_RULES
    }

    admission_values = []
    for row in record.admission_descriptor_rows:
        if row.parameter == "RecordID":
            continue
        is_missing = rule_by_name[row.parameter].is_missing(row.value)
        admission_values.append(
            PhysioNet2012AdmissionValue(
                source_row=row,
                is_missing=is_missing,
                value=None if is_missing else float(row.value),
            )
        )

    order = _validate_event_order(source_event_order, len(record.observation_rows))
    enumerated_rows = tuple(record.observation_rows[index] for index in order)
    events = []
    observations = []
    sidecars = []
    cell_counts = Counter()
    for row in enumerated_rows:
        spec = spec_by_name[row.parameter]
        is_missing = spec.is_missing(row.value)
        event_id = ("physionet-2012-row", record.record_id, row.line_number)
        marks = {} if is_missing else {"value": float(row.value)}
        event = Event(
            event_time=float(row.elapsed_minutes),
            event_type=spec.type_id,
            marks=marks,
            event_id=event_id,
        )
        events.append(event)
        observations.append(
            EventObservation(
                time_observed=True,
                type_observed=True,
                observed_marks=(
                    frozenset() if is_missing else frozenset({"value"})
                ),
            )
        )
        sidecars.append(
            PhysioNet2012EventSidecar(
                source_row=row,
                value_missing=is_missing,
                event_id=event_id,
            )
        )
        cell_counts[(event.event_time, event.event_type)] += 1
        if (
            cell_counts[(event.event_time, event.event_type)]
            > limits.maximum_occurrences_per_cell
        ):
            raise CountingFixtureResourceError(
                "clinical cell multiplicity exceeds the predeclared ceiling"
            )

    configuration = EventConfiguration(
        schema=_clinical_schema(limits),
        events=tuple(events),
        observed=ObservationPattern(
            events=tuple(observations),
            cardinality_observed=True,
        ),
        sample_id=sample,
        group_id=group,
    )
    sidecar_by_id = {sidecar.event_id: sidecar for sidecar in sidecars}
    aligned_sidecars = tuple(
        sidecar_by_id[event.event_id] for event in configuration.events
    )
    provenance = ClinicalFixturePrivateProvenance(
        raw_record=record,
        admission_values=tuple(
            sorted(admission_values, key=lambda value: value.parameter)
        ),
        event_sidecars=aligned_sidecars,
    )
    return CountingFixtureResult(
        fixture_id=fixture_id,
        domain=CountingFixtureDomain.CLINICAL_STYLE,
        source_format="physionet-2012-style-utf8-lf-csv",
        source_split=split,
        source_sha256=source_sha256,
        source_byte_length=len(source),
        configuration=configuration,
        private_provenance=provenance,
        resource_limits=limits,
    )


def build_m_acg_1(
    *,
    limits: CountingFixtureResourceLimits = M_ACG_1_RESOURCE_LIMITS,
    source_event_order: Optional[Sequence[int]] = None,
) -> CountingFixtureResult:
    """Build the exact, digest-locked 65-byte ``M-ACG-1`` fixture."""

    return build_music_counting_fixture(
        M_ACG_1_BYTES,
        fixture_id=M_ACG_1_ID,
        expected_sha256=M_ACG_1_SHA256,
        source_split="train",
        sample_id=M_ACG_1_ID,
        group_id="synthetic-maestro-group-1",
        limits=limits,
        source_event_order=source_event_order,
    )


def build_p_acg_1(
    *,
    limits: CountingFixtureResourceLimits = P_ACG_1_RESOURCE_LIMITS,
    source_event_order: Optional[Sequence[int]] = None,
) -> CountingFixtureResult:
    """Build the exact, digest-locked 207-byte ``P-ACG-1`` fixture."""

    return build_clinical_counting_fixture(
        P_ACG_1_BYTES,
        fixture_id=P_ACG_1_ID,
        expected_sha256=P_ACG_1_SHA256,
        source_split="train",
        sample_id="900001",
        group_id="900001",
        limits=limits,
        source_event_order=source_event_order,
    )


if len(M_ACG_1_BYTES) != 65 or hashlib.sha256(M_ACG_1_BYTES).hexdigest() != M_ACG_1_SHA256:
    raise RuntimeError("M-ACG-1 embedded bytes do not match their frozen identity")
if len(P_ACG_1_BYTES) != 207 or hashlib.sha256(P_ACG_1_BYTES).hexdigest() != P_ACG_1_SHA256:
    raise RuntimeError("P-ACG-1 embedded bytes do not match their frozen identity")


__all__ = [
    "ClinicalFixturePrivateProvenance",
    "CountingFixtureDomain",
    "CountingFixtureError",
    "CountingFixtureResourceError",
    "CountingFixtureResourceLimits",
    "CountingFixtureResult",
    "M_ACG_1_BYTES",
    "M_ACG_1_HEX",
    "M_ACG_1_ID",
    "M_ACG_1_MAESTRO_SEMANTIC_LIMITS",
    "M_ACG_1_MIDI_PARSE_LIMITS",
    "M_ACG_1_RESOURCE_LIMITS",
    "M_ACG_1_SHA256",
    "MusicFixturePrivateProvenance",
    "P_ACG_1_ADMISSION_MISSING_RULES",
    "P_ACG_1_BYTES",
    "P_ACG_1_ID",
    "P_ACG_1_PARAMETER_SPECS",
    "P_ACG_1_RESOURCE_LIMITS",
    "P_ACG_1_SHA256",
    "P_ACG_1_TEXT",
    "PUBLIC_GENERATED_FIXTURE_NOTICE",
    "build_clinical_counting_fixture",
    "build_m_acg_1",
    "build_music_counting_fixture",
    "build_p_acg_1",
]
