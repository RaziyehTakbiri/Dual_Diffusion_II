"""Deterministic, policy-free raw-MIDI audit for a verified MAESTRO archive.

The metadata inventory and the MIDI parser deliberately remain separate
boundaries.  This module joins them without introducing note pairing, pedal
interpretation, time-to-seconds conversion, score alignment, quantization, or
windowing.  It re-reads every inventoried byte, verifies size and SHA-256,
parses the complete SMF under caller-supplied limits, and records only raw
protocol counts.

An optional differential oracle checks the lossless parse against exactly
Mido 1.3.3.  The oracle compares headers, track/event order, delta times, raw
channel messages, meta-event bytes, and the normalized SysEx representation
used by Mido.  It is validation-only: no Mido object or interpretation enters
the returned evidence.

``MaestroRawMidiAudit`` is immutable and contains private logical MIDI paths.
Its ``public_summary`` intentionally returns aggregate counts and digests only.
"""

from __future__ import annotations

import hashlib
import os
import stat
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, Mapping, Optional, Sequence, Tuple, Union

from heterodiff.artifacts.manifest import canonical_json_dumps, sha256_bytes
from heterodiff.data.maestro_inventory import (
    MAESTRO_V3_EXPECTED_MIDI_FILES,
    MaestroArchiveInventory,
    MaestroMidiInventory,
)
from heterodiff.data.midi_raw import (
    MidiChannelEvent,
    MidiFile,
    MidiFormatError,
    MidiMetaEvent,
    MidiParseLimits,
    MidiSysExEvent,
    parse_midi_bytes,
)
from heterodiff.validation.mido_oracle import (
    MIDO_ORACLE_VERSION,
    MidoDifferentialError,
    MidoDifferentialReport,
    MidoUnavailableError,
    MidoVersionError,
    validate_parsed_midi_against_mido,
)


PathLike = Union[str, os.PathLike]

PINNED_MIDO_ORACLE_VERSION = MIDO_ORACLE_VERSION
_AUDIT_DIGEST_DOMAIN = b"heterodiff-maestro-v3-raw-midi-audit-v1\0"
_DATASET_NAME = "maestro-v3.0.0"
_GATE_NAME = "policy-free-raw-midi-corpus-audit"
_PEDAL_CONTROLLER_NUMBERS = frozenset((64, 66, 67))


class MaestroRawMidiAuditError(ValueError):
    """Raised when raw corpus evidence fails closed at the audit boundary."""


def _plain_nonnegative_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{} must be an integer".format(name))
    if value < 0:
        raise ValueError("{} must be nonnegative".format(name))
    return value


def _validate_sha256(value: object, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("{} must be a lowercase SHA-256 digest".format(name))
    return value


def _validated_named_counts(
    value: object, *, name: str
) -> Tuple[Tuple[str, int], ...]:
    if not isinstance(value, tuple):
        raise TypeError("{} must be a tuple".format(name))
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("{} entries must be (name, count) tuples".format(name))
        key, count = item
        if not isinstance(key, str) or not key:
            raise TypeError("{} keys must be nonempty strings".format(name))
        _plain_nonnegative_int(count, name="{} count".format(name))
        if count == 0:
            raise ValueError("{} must omit zero counts".format(name))
        result.append((key, count))
    if tuple(result) != tuple(sorted(result)) or len({key for key, _ in result}) != len(
        result
    ):
        raise ValueError("{} must be sorted and unique".format(name))
    return tuple(result)


def _validated_numeric_counts(
    value: object, *, name: str, minimum_key: int = 0, maximum_key: Optional[int] = None
) -> Tuple[Tuple[int, int], ...]:
    if not isinstance(value, tuple):
        raise TypeError("{} must be a tuple".format(name))
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("{} entries must be (value, count) tuples".format(name))
        key, count = item
        if isinstance(key, bool) or not isinstance(key, int):
            raise TypeError("{} keys must be integers".format(name))
        if key < minimum_key or (maximum_key is not None and key > maximum_key):
            raise ValueError("{} key is outside its admitted range".format(name))
        _plain_nonnegative_int(count, name="{} count".format(name))
        if count == 0:
            raise ValueError("{} must omit zero counts".format(name))
        result.append((key, count))
    if tuple(result) != tuple(sorted(result)) or len({key for key, _ in result}) != len(
        result
    ):
        raise ValueError("{} must be sorted and unique".format(name))
    return tuple(result)


def _validated_controller_value_counts(
    value: object,
) -> Tuple[Tuple[int, int, int], ...]:
    if not isinstance(value, tuple):
        raise TypeError("pedal_controller_value_counts must be a tuple")
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 3:
            raise TypeError(
                "pedal_controller_value_counts entries must be triples"
            )
        controller, controller_value, count = item
        if controller not in _PEDAL_CONTROLLER_NUMBERS:
            raise ValueError("only raw controller numbers 64, 66, and 67 are admitted")
        if (
            isinstance(controller_value, bool)
            or not isinstance(controller_value, int)
            or not 0 <= controller_value <= 127
        ):
            raise ValueError("controller values must be integers in 0..127")
        _plain_nonnegative_int(count, name="controller-value count")
        if count == 0:
            raise ValueError("zero controller-value counts must be omitted")
        result.append((controller, controller_value, count))
    if tuple(result) != tuple(sorted(result)) or len(
        {(controller, value) for controller, value, _ in result}
    ) != len(result):
        raise ValueError("pedal_controller_value_counts must be sorted and unique")
    return tuple(result)


def _counter_pairs(counter: Counter) -> Tuple[Tuple[object, int], ...]:
    return tuple(sorted((key, count) for key, count in counter.items() if count))


def _counts_as_named_dict(counts: Sequence[Tuple[str, int]]) -> Dict[str, int]:
    return {key: count for key, count in counts}


def _counts_as_numeric_dict(counts: Sequence[Tuple[int, int]]) -> Dict[str, int]:
    return {str(key): count for key, count in counts}


def _meta_counts_as_dict(counts: Sequence[Tuple[int, int]]) -> Dict[str, int]:
    return {"0x{:02x}".format(key): count for key, count in counts}


def _status_counts_as_dict(counts: Sequence[Tuple[int, int]]) -> Dict[str, int]:
    return {"0x{:02x}".format(key): count for key, count in counts}


def _limits_dict(limits: MidiParseLimits) -> Dict[str, int]:
    return {
        "maximum_file_bytes": limits.maximum_file_bytes,
        "maximum_tracks": limits.maximum_tracks,
        "maximum_track_bytes": limits.maximum_track_bytes,
        "maximum_event_payload_bytes": limits.maximum_event_payload_bytes,
        "maximum_events_per_track": limits.maximum_events_per_track,
        "maximum_total_events": limits.maximum_total_events,
        "maximum_absolute_tick": limits.maximum_absolute_tick,
        "maximum_ticks_per_quarter_note": limits.maximum_ticks_per_quarter_note,
    }


@dataclass(frozen=True)
class MaestroRawMidiFileEvidence:
    """Private, policy-free evidence for one exact inventoried MIDI file."""

    metadata_row_number: int
    midi_path: str
    source_split: str
    sha256: str
    size_bytes: int
    format_type: int
    ticks_per_quarter_note: int
    track_event_counts: Tuple[int, ...]
    track_byte_lengths: Tuple[int, ...]
    track_end_ticks: Tuple[int, ...]
    event_category_counts: Tuple[Tuple[str, int], ...]
    channel_message_counts: Tuple[Tuple[str, int], ...]
    meta_type_counts: Tuple[Tuple[int, int], ...]
    controller_counts: Tuple[Tuple[int, int], ...]
    pedal_controller_value_counts: Tuple[Tuple[int, int, int], ...]
    sysex_status_counts: Tuple[Tuple[int, int], ...]
    running_status_event_count: int
    note_on_velocity_zero_count: int
    maximum_delta_ticks: int
    maximum_absolute_ticks: int
    maximum_event_payload_bytes: int
    oracle_passed: bool

    def __post_init__(self) -> None:
        if (
            isinstance(self.metadata_row_number, bool)
            or not isinstance(self.metadata_row_number, int)
            or self.metadata_row_number < 2
        ):
            raise ValueError("metadata_row_number must be an integer of at least 2")
        if not isinstance(self.midi_path, str):
            raise TypeError("midi_path must be a string")
        parsed_path = PurePosixPath(self.midi_path)
        if (
            "\\" in self.midi_path
            or self.midi_path.startswith("/")
            or parsed_path.is_absolute()
            or str(parsed_path) != self.midi_path
            or parsed_path.suffix != ".midi"
            or any(part in {"", ".", ".."} for part in parsed_path.parts)
        ):
            raise ValueError("midi_path must be a canonical relative .midi path")
        if self.source_split not in ("test", "train", "validation"):
            raise ValueError("source_split must retain an official MAESTRO label")
        _validate_sha256(self.sha256, name="sha256")
        _plain_nonnegative_int(self.size_bytes, name="size_bytes")
        if self.size_bytes == 0:
            raise ValueError("size_bytes must be positive for an admitted SMF")
        if isinstance(self.format_type, bool) or not isinstance(self.format_type, int):
            raise TypeError("format_type must be an integer")
        if self.format_type not in (0, 1, 2):
            raise ValueError("format_type must be 0, 1, or 2")
        if (
            isinstance(self.ticks_per_quarter_note, bool)
            or not isinstance(self.ticks_per_quarter_note, int)
            or not 1 <= self.ticks_per_quarter_note <= 0x7FFF
        ):
            raise ValueError("ticks_per_quarter_note must be in 1..32767")
        for name in ("track_event_counts", "track_byte_lengths", "track_end_ticks"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not values:
                raise TypeError("{} must be a nonempty tuple".format(name))
            for value in values:
                _plain_nonnegative_int(value, name=name)
        if not (
            len(self.track_event_counts)
            == len(self.track_byte_lengths)
            == len(self.track_end_ticks)
        ):
            raise ValueError("per-track evidence lengths must agree")
        if self.format_type == 0 and len(self.track_event_counts) != 1:
            raise ValueError("format 0 evidence must contain exactly one track")
        if any(value == 0 for value in self.track_event_counts):
            raise ValueError("every parsed track must contain end-of-track")
        if any(value == 0 for value in self.track_byte_lengths):
            raise ValueError("every parsed track must contain bytes")
        object.__setattr__(
            self,
            "event_category_counts",
            _validated_named_counts(
                self.event_category_counts, name="event_category_counts"
            ),
        )
        object.__setattr__(
            self,
            "channel_message_counts",
            _validated_named_counts(
                self.channel_message_counts, name="channel_message_counts"
            ),
        )
        object.__setattr__(
            self,
            "meta_type_counts",
            _validated_numeric_counts(
                self.meta_type_counts,
                name="meta_type_counts",
                maximum_key=0x7F,
            ),
        )
        object.__setattr__(
            self,
            "controller_counts",
            _validated_numeric_counts(
                self.controller_counts,
                name="controller_counts",
                maximum_key=127,
            ),
        )
        object.__setattr__(
            self,
            "pedal_controller_value_counts",
            _validated_controller_value_counts(self.pedal_controller_value_counts),
        )
        object.__setattr__(
            self,
            "sysex_status_counts",
            _validated_numeric_counts(
                self.sysex_status_counts,
                name="sysex_status_counts",
                minimum_key=0xF0,
                maximum_key=0xF7,
            ),
        )
        for name in (
            "running_status_event_count",
            "note_on_velocity_zero_count",
            "maximum_delta_ticks",
            "maximum_absolute_ticks",
            "maximum_event_payload_bytes",
        ):
            _plain_nonnegative_int(getattr(self, name), name=name)
        if not isinstance(self.oracle_passed, bool):
            raise TypeError("oracle_passed must be a boolean")
        observed_total = sum(count for _, count in self.event_category_counts)
        if observed_total != sum(self.track_event_counts):
            raise ValueError("event-category counts must equal per-track event counts")
        if self.running_status_event_count > observed_total:
            raise ValueError("running-status count exceeds total events")
        if self.note_on_velocity_zero_count > dict(self.channel_message_counts).get(
            "note_on", 0
        ):
            raise ValueError("zero-velocity note-on count exceeds note-on count")

    @property
    def track_count(self) -> int:
        return len(self.track_event_counts)

    @property
    def total_events(self) -> int:
        return sum(self.track_event_counts)

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "metadata_row_number": self.metadata_row_number,
            "midi_path": self.midi_path,
            "source_split": self.source_split,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "format_type": self.format_type,
            "ticks_per_quarter_note": self.ticks_per_quarter_note,
            "track_event_counts": list(self.track_event_counts),
            "track_byte_lengths": list(self.track_byte_lengths),
            "track_end_ticks": list(self.track_end_ticks),
            "event_category_counts": [
                {"category": key, "count": count}
                for key, count in self.event_category_counts
            ],
            "channel_message_counts": [
                {"message_type": key, "count": count}
                for key, count in self.channel_message_counts
            ],
            "meta_type_counts": [
                {"meta_type": key, "count": count}
                for key, count in self.meta_type_counts
            ],
            "controller_counts": [
                {"controller": key, "count": count}
                for key, count in self.controller_counts
            ],
            "pedal_controller_value_counts": [
                {"controller": controller, "value": value, "count": count}
                for controller, value, count in self.pedal_controller_value_counts
            ],
            "sysex_status_counts": [
                {"status": key, "count": count}
                for key, count in self.sysex_status_counts
            ],
            "running_status_event_count": self.running_status_event_count,
            "note_on_velocity_zero_count": self.note_on_velocity_zero_count,
            "maximum_delta_ticks": self.maximum_delta_ticks,
            "maximum_absolute_ticks": self.maximum_absolute_ticks,
            "maximum_event_payload_bytes": self.maximum_event_payload_bytes,
            "oracle_passed": self.oracle_passed,
        }


def _file_evidence(
    record: MaestroMidiInventory,
    parsed: MidiFile,
    *,
    oracle_passed: bool,
) -> MaestroRawMidiFileEvidence:
    categories = Counter()
    channel_messages = Counter()
    meta_types = Counter()
    controllers = Counter()
    pedal_values = Counter()
    sysex_statuses = Counter()
    running_status_count = 0
    zero_velocity_note_ons = 0
    maximum_delta = 0
    maximum_absolute = 0
    maximum_payload = 0

    for track in parsed.tracks:
        for event in track.events:
            maximum_delta = max(maximum_delta, event.delta_ticks)
            maximum_absolute = max(maximum_absolute, event.absolute_ticks)
            if isinstance(event, MidiChannelEvent):
                categories["channel"] += 1
                channel_messages[event.message_type] += 1
                maximum_payload = max(maximum_payload, len(event.data))
                if event.used_running_status:
                    running_status_count += 1
                if event.message_type == "note_on" and event.velocity == 0:
                    zero_velocity_note_ons += 1
                if event.message_type == "control_change":
                    controller = event.controller
                    controller_value = event.controller_value
                    if controller is None or controller_value is None:
                        raise AssertionError("control-change fields were not retained")
                    controllers[controller] += 1
                    if controller in _PEDAL_CONTROLLER_NUMBERS:
                        pedal_values[(controller, controller_value)] += 1
            elif isinstance(event, MidiMetaEvent):
                categories["meta"] += 1
                meta_types[event.meta_type] += 1
                maximum_payload = max(maximum_payload, len(event.payload))
            elif isinstance(event, MidiSysExEvent):
                categories["sysex"] += 1
                sysex_statuses[event.status] += 1
                maximum_payload = max(maximum_payload, len(event.payload))
            else:
                raise AssertionError("raw parser returned an unknown event class")

    return MaestroRawMidiFileEvidence(
        metadata_row_number=record.metadata_row_number,
        midi_path=record.midi_path,
        source_split=record.source_split,
        sha256=record.sha256,
        size_bytes=record.size_bytes,
        format_type=parsed.format_type,
        ticks_per_quarter_note=parsed.ticks_per_quarter_note,
        track_event_counts=tuple(len(track.events) for track in parsed.tracks),
        track_byte_lengths=tuple(track.byte_length for track in parsed.tracks),
        track_end_ticks=tuple(track.end_tick for track in parsed.tracks),
        event_category_counts=_counter_pairs(categories),  # type: ignore[arg-type]
        channel_message_counts=_counter_pairs(channel_messages),  # type: ignore[arg-type]
        meta_type_counts=_counter_pairs(meta_types),  # type: ignore[arg-type]
        controller_counts=_counter_pairs(controllers),  # type: ignore[arg-type]
        pedal_controller_value_counts=tuple(
            (controller, value, count)
            for (controller, value), count in sorted(pedal_values.items())
        ),
        sysex_status_counts=_counter_pairs(sysex_statuses),  # type: ignore[arg-type]
        running_status_event_count=running_status_count,
        note_on_velocity_zero_count=zero_velocity_note_ons,
        maximum_delta_ticks=maximum_delta,
        maximum_absolute_ticks=maximum_absolute,
        maximum_event_payload_bytes=maximum_payload,
        oracle_passed=oracle_passed,
    )


@dataclass(frozen=True)
class MaestroRawMidiAggregate:
    """Immutable aggregate of raw protocol evidence across all MIDI files."""

    file_count: int
    file_size_bytes: int
    parse_pass_count: int
    oracle_required: bool
    oracle_pass_count: int
    format_type_counts: Tuple[Tuple[int, int], ...]
    ticks_per_quarter_note_counts: Tuple[Tuple[int, int], ...]
    track_count_counts: Tuple[Tuple[int, int], ...]
    total_track_count: int
    total_event_count: int
    event_category_counts: Tuple[Tuple[str, int], ...]
    channel_message_counts: Tuple[Tuple[str, int], ...]
    meta_type_counts: Tuple[Tuple[int, int], ...]
    controller_counts: Tuple[Tuple[int, int], ...]
    pedal_controller_value_counts: Tuple[Tuple[int, int, int], ...]
    sysex_status_counts: Tuple[Tuple[int, int], ...]
    running_status_event_count: int
    note_on_velocity_zero_count: int
    maximum_file_size_bytes: int
    maximum_tracks_per_file: int
    maximum_events_per_file: int
    maximum_events_per_track: int
    maximum_track_size_bytes: int
    maximum_track_end_tick: int
    maximum_delta_ticks: int
    maximum_absolute_ticks: int
    maximum_event_payload_bytes: int

    def __post_init__(self) -> None:
        for name in (
            "file_count",
            "file_size_bytes",
            "parse_pass_count",
            "oracle_pass_count",
            "total_track_count",
            "total_event_count",
            "running_status_event_count",
            "note_on_velocity_zero_count",
            "maximum_file_size_bytes",
            "maximum_tracks_per_file",
            "maximum_events_per_file",
            "maximum_events_per_track",
            "maximum_track_size_bytes",
            "maximum_track_end_tick",
            "maximum_delta_ticks",
            "maximum_absolute_ticks",
            "maximum_event_payload_bytes",
        ):
            _plain_nonnegative_int(getattr(self, name), name=name)
        if not isinstance(self.oracle_required, bool):
            raise TypeError("oracle_required must be a boolean")
        object.__setattr__(
            self,
            "format_type_counts",
            _validated_numeric_counts(
                self.format_type_counts,
                name="format_type_counts",
                maximum_key=2,
            ),
        )
        object.__setattr__(
            self,
            "ticks_per_quarter_note_counts",
            _validated_numeric_counts(
                self.ticks_per_quarter_note_counts,
                name="ticks_per_quarter_note_counts",
                minimum_key=1,
                maximum_key=0x7FFF,
            ),
        )
        object.__setattr__(
            self,
            "track_count_counts",
            _validated_numeric_counts(
                self.track_count_counts,
                name="track_count_counts",
                minimum_key=1,
            ),
        )
        for name in ("event_category_counts", "channel_message_counts"):
            object.__setattr__(
                self,
                name,
                _validated_named_counts(getattr(self, name), name=name),
            )
        object.__setattr__(
            self,
            "meta_type_counts",
            _validated_numeric_counts(
                self.meta_type_counts,
                name="meta_type_counts",
                maximum_key=0x7F,
            ),
        )
        object.__setattr__(
            self,
            "controller_counts",
            _validated_numeric_counts(
                self.controller_counts,
                name="controller_counts",
                maximum_key=127,
            ),
        )
        object.__setattr__(
            self,
            "pedal_controller_value_counts",
            _validated_controller_value_counts(self.pedal_controller_value_counts),
        )
        object.__setattr__(
            self,
            "sysex_status_counts",
            _validated_numeric_counts(
                self.sysex_status_counts,
                name="sysex_status_counts",
                minimum_key=0xF0,
                maximum_key=0xF7,
            ),
        )
        if self.parse_pass_count != self.file_count:
            raise ValueError("a successful audit must parse every file")
        expected_oracle = self.file_count if self.oracle_required else 0
        if self.oracle_pass_count != expected_oracle:
            raise ValueError("oracle pass count is inconsistent with oracle mode")
        if sum(count for _, count in self.format_type_counts) != self.file_count:
            raise ValueError("format-type counts must equal file_count")
        if sum(count for _, count in self.ticks_per_quarter_note_counts) != self.file_count:
            raise ValueError("PPQ counts must equal file_count")
        if sum(count for _, count in self.track_count_counts) != self.file_count:
            raise ValueError("track-count distribution must equal file_count")
        if sum(count for _, count in self.event_category_counts) != self.total_event_count:
            raise ValueError("event-category counts must equal total_event_count")

    def to_dict(self) -> Dict[str, object]:
        return {
            "file_count": self.file_count,
            "file_size_bytes": self.file_size_bytes,
            "parse_pass_count": self.parse_pass_count,
            "oracle_required": self.oracle_required,
            "oracle_pass_count": self.oracle_pass_count,
            "format_type_counts": [list(item) for item in self.format_type_counts],
            "ticks_per_quarter_note_counts": [
                list(item) for item in self.ticks_per_quarter_note_counts
            ],
            "track_count_counts": [list(item) for item in self.track_count_counts],
            "total_track_count": self.total_track_count,
            "total_event_count": self.total_event_count,
            "event_category_counts": [list(item) for item in self.event_category_counts],
            "channel_message_counts": [list(item) for item in self.channel_message_counts],
            "meta_type_counts": [list(item) for item in self.meta_type_counts],
            "controller_counts": [list(item) for item in self.controller_counts],
            "pedal_controller_value_counts": [
                list(item) for item in self.pedal_controller_value_counts
            ],
            "sysex_status_counts": [list(item) for item in self.sysex_status_counts],
            "running_status_event_count": self.running_status_event_count,
            "note_on_velocity_zero_count": self.note_on_velocity_zero_count,
            "maximum_file_size_bytes": self.maximum_file_size_bytes,
            "maximum_tracks_per_file": self.maximum_tracks_per_file,
            "maximum_events_per_file": self.maximum_events_per_file,
            "maximum_events_per_track": self.maximum_events_per_track,
            "maximum_track_size_bytes": self.maximum_track_size_bytes,
            "maximum_track_end_tick": self.maximum_track_end_tick,
            "maximum_delta_ticks": self.maximum_delta_ticks,
            "maximum_absolute_ticks": self.maximum_absolute_ticks,
            "maximum_event_payload_bytes": self.maximum_event_payload_bytes,
        }


def _aggregate_records(
    records: Sequence[MaestroRawMidiFileEvidence],
    *,
    oracle_required: bool,
) -> MaestroRawMidiAggregate:
    formats = Counter(record.format_type for record in records)
    ppqs = Counter(record.ticks_per_quarter_note for record in records)
    track_counts = Counter(record.track_count for record in records)
    categories = Counter()
    channel_messages = Counter()
    meta_types = Counter()
    controllers = Counter()
    pedal_values = Counter()
    sysex_statuses = Counter()
    for record in records:
        categories.update(dict(record.event_category_counts))
        channel_messages.update(dict(record.channel_message_counts))
        meta_types.update(dict(record.meta_type_counts))
        controllers.update(dict(record.controller_counts))
        pedal_values.update(
            {
                (controller, value): count
                for controller, value, count in record.pedal_controller_value_counts
            }
        )
        sysex_statuses.update(dict(record.sysex_status_counts))

    def maximum(values: Sequence[int]) -> int:
        return max(values) if values else 0

    return MaestroRawMidiAggregate(
        file_count=len(records),
        file_size_bytes=sum(record.size_bytes for record in records),
        parse_pass_count=len(records),
        oracle_required=oracle_required,
        oracle_pass_count=sum(record.oracle_passed for record in records),
        format_type_counts=_counter_pairs(formats),  # type: ignore[arg-type]
        ticks_per_quarter_note_counts=_counter_pairs(ppqs),  # type: ignore[arg-type]
        track_count_counts=_counter_pairs(track_counts),  # type: ignore[arg-type]
        total_track_count=sum(record.track_count for record in records),
        total_event_count=sum(record.total_events for record in records),
        event_category_counts=_counter_pairs(categories),  # type: ignore[arg-type]
        channel_message_counts=_counter_pairs(channel_messages),  # type: ignore[arg-type]
        meta_type_counts=_counter_pairs(meta_types),  # type: ignore[arg-type]
        controller_counts=_counter_pairs(controllers),  # type: ignore[arg-type]
        pedal_controller_value_counts=tuple(
            (controller, value, count)
            for (controller, value), count in sorted(pedal_values.items())
        ),
        sysex_status_counts=_counter_pairs(sysex_statuses),  # type: ignore[arg-type]
        running_status_event_count=sum(
            record.running_status_event_count for record in records
        ),
        note_on_velocity_zero_count=sum(
            record.note_on_velocity_zero_count for record in records
        ),
        maximum_file_size_bytes=maximum([record.size_bytes for record in records]),
        maximum_tracks_per_file=maximum([record.track_count for record in records]),
        maximum_events_per_file=maximum([record.total_events for record in records]),
        maximum_events_per_track=maximum(
            [value for record in records for value in record.track_event_counts]
        ),
        maximum_track_size_bytes=maximum(
            [value for record in records for value in record.track_byte_lengths]
        ),
        maximum_track_end_tick=maximum(
            [value for record in records for value in record.track_end_ticks]
        ),
        maximum_delta_ticks=maximum([record.maximum_delta_ticks for record in records]),
        maximum_absolute_ticks=maximum(
            [record.maximum_absolute_ticks for record in records]
        ),
        maximum_event_payload_bytes=maximum(
            [record.maximum_event_payload_bytes for record in records]
        ),
    )


@dataclass(frozen=True)
class MaestroRawMidiAudit:
    """Immutable private corpus evidence plus a release-safe aggregate view."""

    inventory_manifest_sha256: str
    limits: MidiParseLimits
    oracle_required: bool
    oracle_version: Optional[str]
    records: Tuple[MaestroRawMidiFileEvidence, ...]
    aggregate: MaestroRawMidiAggregate = field(init=False)
    audit_sha256: str = field(init=False)
    schema_version: int = field(default=1, init=False)

    def __post_init__(self) -> None:
        _validate_sha256(
            self.inventory_manifest_sha256, name="inventory_manifest_sha256"
        )
        if not isinstance(self.limits, MidiParseLimits):
            raise TypeError("limits must be a MidiParseLimits instance")
        if not isinstance(self.oracle_required, bool):
            raise TypeError("oracle_required must be a boolean")
        if self.oracle_required:
            if self.oracle_version != PINNED_MIDO_ORACLE_VERSION:
                raise ValueError("required oracle version must equal the pinned version")
        elif self.oracle_version is not None:
            raise ValueError("oracle_version must be absent when the oracle is disabled")
        if not isinstance(self.records, tuple):
            raise TypeError("records must be a tuple")
        if len(self.records) != MAESTRO_V3_EXPECTED_MIDI_FILES:
            raise ValueError(
                "raw audit must contain exactly {} file records".format(
                    MAESTRO_V3_EXPECTED_MIDI_FILES
                )
            )
        if any(not isinstance(value, MaestroRawMidiFileEvidence) for value in self.records):
            raise TypeError("records must contain MaestroRawMidiFileEvidence values")
        records = tuple(sorted(self.records, key=lambda value: value.midi_path))
        if len({value.midi_path for value in records}) != len(records):
            raise ValueError("raw audit MIDI paths must be unique")
        if {value.metadata_row_number for value in records} != set(
            range(2, MAESTRO_V3_EXPECTED_MIDI_FILES + 2)
        ):
            raise ValueError("raw audit metadata row numbers must be exact")
        if any(value.oracle_passed != self.oracle_required for value in records):
            raise ValueError("per-file oracle status is inconsistent with oracle mode")
        object.__setattr__(self, "records", records)
        aggregate = _aggregate_records(records, oracle_required=self.oracle_required)
        object.__setattr__(self, "aggregate", aggregate)
        private_json = canonical_json_dumps(self._private_payload())
        object.__setattr__(
            self,
            "audit_sha256",
            sha256_bytes(_AUDIT_DIGEST_DOMAIN + private_json.encode("utf-8")),
        )

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset": _DATASET_NAME,
            "gate": _GATE_NAME,
            "inventory_manifest_sha256": self.inventory_manifest_sha256,
            "midi_parse_limits": _limits_dict(self.limits),
            "oracle": {
                "required": self.oracle_required,
                "distribution": "mido" if self.oracle_required else None,
                "version": self.oracle_version,
            },
            "records": [record.to_private_dict() for record in self.records],
            "aggregate": self.aggregate.to_dict(),
        }

    def to_private_dict(self) -> Dict[str, object]:
        """Return a fresh dictionary containing private logical MIDI paths."""

        return self._private_payload()

    def to_private_json(self) -> str:
        """Return deterministic canonical private evidence (without its digest)."""

        return canonical_json_dumps(self._private_payload())

    def public_summary(self) -> Mapping[str, object]:
        """Return release-safe aggregate evidence with all source paths removed."""

        aggregate = self.aggregate
        return {
            "schema_version": self.schema_version,
            "dataset": _DATASET_NAME,
            "gate": _GATE_NAME,
            "inventory_manifest_sha256": self.inventory_manifest_sha256,
            "audit_sha256": self.audit_sha256,
            "midi_parse_limits": _limits_dict(self.limits),
            "file_verification": {
                "expected_file_count": MAESTRO_V3_EXPECTED_MIDI_FILES,
                "verified_file_count": aggregate.file_count,
                "verified_size_bytes": aggregate.file_size_bytes,
                "sha256_and_size_rechecked": True,
                "parse_pass_count": aggregate.parse_pass_count,
            },
            "oracle": {
                "required": self.oracle_required,
                "distribution": "mido" if self.oracle_required else None,
                "pinned_version": (
                    PINNED_MIDO_ORACLE_VERSION if self.oracle_required else None
                ),
                "pass_count": aggregate.oracle_pass_count,
            },
            "headers": {
                "format_type_counts": _counts_as_numeric_dict(
                    aggregate.format_type_counts
                ),
                "ticks_per_quarter_note_counts": _counts_as_numeric_dict(
                    aggregate.ticks_per_quarter_note_counts
                ),
            },
            "tracks": {
                "track_count_distribution": _counts_as_numeric_dict(
                    aggregate.track_count_counts
                ),
                "total_track_count": aggregate.total_track_count,
            },
            "events": {
                "total_event_count": aggregate.total_event_count,
                "category_counts": _counts_as_named_dict(
                    aggregate.event_category_counts
                ),
                "channel_message_counts": _counts_as_named_dict(
                    aggregate.channel_message_counts
                ),
                "meta_type_counts": _meta_counts_as_dict(
                    aggregate.meta_type_counts
                ),
                "sysex_status_counts": _status_counts_as_dict(
                    aggregate.sysex_status_counts
                ),
                "running_status_channel_event_count": (
                    aggregate.running_status_event_count
                ),
                "note_on_velocity_zero_count": (
                    aggregate.note_on_velocity_zero_count
                ),
            },
            "raw_controllers": {
                "controller_number_counts": _counts_as_numeric_dict(
                    aggregate.controller_counts
                ),
                "controller_64_66_67_value_counts": [
                    {
                        "controller": controller,
                        "value": value,
                        "count": count,
                    }
                    for controller, value, count in (
                        aggregate.pedal_controller_value_counts
                    )
                ],
                "controller_values_interpreted_as_pedal_state": False,
            },
            "maxima": {
                "file_size_bytes": aggregate.maximum_file_size_bytes,
                "tracks_per_file": aggregate.maximum_tracks_per_file,
                "events_per_file": aggregate.maximum_events_per_file,
                "events_per_track": aggregate.maximum_events_per_track,
                "track_size_bytes": aggregate.maximum_track_size_bytes,
                "track_end_tick": aggregate.maximum_track_end_tick,
                "delta_ticks": aggregate.maximum_delta_ticks,
                "absolute_ticks": aggregate.maximum_absolute_ticks,
                "event_payload_bytes": aggregate.maximum_event_payload_bytes,
            },
            "privacy": {
                "trusted_root_included": False,
                "midi_paths_included": False,
                "composer_strings_included": False,
                "title_strings_included": False,
            },
            "claim_boundary": {
                "raw_midi_bytes_verified": True,
                "raw_midi_events_parsed": True,
                "note_on_velocity_zero_rewritten": False,
                "note_events_paired": False,
                "pedal_state_inferred": False,
                "tempo_converted_to_seconds": False,
                "score_alignment_inferred": False,
                "grid_quantization_applied": False,
                "model_windows_constructed": False,
            },
        }


def _stat_signature(status: os.stat_result) -> Tuple[int, int, int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _validate_root(root: PathLike) -> Tuple[Path, Path]:
    if not isinstance(root, (str, os.PathLike)):
        raise TypeError("trusted_root must be a string or path-like object")
    candidate = Path(root)
    if not candidate.is_absolute():
        raise MaestroRawMidiAuditError("trusted_root must be an absolute path")
    try:
        status = candidate.lstat()
    except FileNotFoundError as error:
        raise MaestroRawMidiAuditError("trusted_root does not exist") from error
    if stat.S_ISLNK(status.st_mode):
        raise MaestroRawMidiAuditError("trusted_root must not be a symlink")
    if not stat.S_ISDIR(status.st_mode):
        raise MaestroRawMidiAuditError("trusted_root must be a directory")
    return candidate, candidate.resolve(strict=True)


def _validated_record_path(
    root: Path,
    resolved_root: Path,
    record: MaestroMidiInventory,
) -> Tuple[Path, os.stat_result]:
    candidate = root
    components = PurePosixPath(record.midi_path).parts
    if not components:
        raise MaestroRawMidiAuditError("inventory contains an empty MIDI path")
    for index, component in enumerate(components):
        candidate = candidate / component
        try:
            status = candidate.lstat()
        except FileNotFoundError as error:
            raise MaestroRawMidiAuditError(
                "inventoried MIDI file is missing at metadata row {}".format(
                    record.metadata_row_number
                )
            ) from error
        if stat.S_ISLNK(status.st_mode):
            raise MaestroRawMidiAuditError(
                "inventoried MIDI path contains a symlink at metadata row {}".format(
                    record.metadata_row_number
                )
            )
        if index < len(components) - 1 and not stat.S_ISDIR(status.st_mode):
            raise MaestroRawMidiAuditError(
                "inventoried MIDI parent is not a directory at metadata row {}".format(
                    record.metadata_row_number
                )
            )
    if not stat.S_ISREG(status.st_mode):
        raise MaestroRawMidiAuditError(
            "inventoried MIDI path is not a regular file at metadata row {}".format(
                record.metadata_row_number
            )
        )
    if status.st_nlink != 1:
        raise MaestroRawMidiAuditError(
            "inventoried MIDI file must not be hard linked at metadata row {}".format(
                record.metadata_row_number
            )
        )
    try:
        candidate.resolve(strict=True).relative_to(resolved_root)
    except ValueError as error:
        raise MaestroRawMidiAuditError(
            "inventoried MIDI file resolves outside trusted_root"
        ) from error
    return candidate, status


def _read_and_verify_record(
    path: Path,
    expected_status: os.stat_result,
    record: MaestroMidiInventory,
    *,
    limits: MidiParseLimits,
) -> Tuple[bytes, Tuple[int, int, int, int, int, int, int]]:
    if expected_status.st_size != record.size_bytes:
        raise MaestroRawMidiAuditError(
            "MIDI size no longer matches inventory at metadata row {}".format(
                record.metadata_row_number
            )
        )
    if record.size_bytes > limits.maximum_file_bytes:
        raise MaestroRawMidiAuditError(
            "inventoried MIDI size exceeds explicit parser limit at metadata row {}".format(
                record.metadata_row_number
            )
        )

    chunks = []
    digest = hashlib.sha256()
    byte_count = 0
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = None
    try:
        descriptor = os.open(os.fspath(path), flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise MaestroRawMidiAuditError("opened MIDI object is not regular")
        if _stat_signature(opened) != _stat_signature(expected_status):
            raise MaestroRawMidiAuditError(
                "MIDI file changed while opening at metadata row {}".format(
                    record.metadata_row_number
                )
            )
        remaining = limits.maximum_file_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            digest.update(chunk)
            byte_count += len(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        if _stat_signature(after) != _stat_signature(opened):
            raise MaestroRawMidiAuditError(
                "MIDI file changed during descriptor read at metadata row {}".format(
                    record.metadata_row_number
                )
            )
    except MaestroRawMidiAuditError:
        raise
    except OSError as error:
        raise MaestroRawMidiAuditError(
            "could not read MIDI at metadata row {}".format(
                record.metadata_row_number
            )
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)

    if byte_count > limits.maximum_file_bytes:
        raise MaestroRawMidiAuditError("MIDI file grew beyond explicit parser limit")

    try:
        path_after = path.lstat()
    except FileNotFoundError as error:
        raise MaestroRawMidiAuditError("MIDI file disappeared during audit") from error
    signature = _stat_signature(expected_status)
    if (
        _stat_signature(opened) != signature
        or _stat_signature(after) != signature
        or _stat_signature(path_after) != signature
        or byte_count != expected_status.st_size
    ):
        raise MaestroRawMidiAuditError(
            "MIDI file changed while reading at metadata row {}".format(
                record.metadata_row_number
            )
        )
    if byte_count != record.size_bytes:
        raise MaestroRawMidiAuditError(
            "MIDI size mismatch at metadata row {}".format(record.metadata_row_number)
        )
    if digest.hexdigest() != record.sha256:
        raise MaestroRawMidiAuditError(
            "MIDI SHA-256 mismatch at metadata row {}".format(
                record.metadata_row_number
            )
        )
    return b"".join(chunks), signature


def _validate_oracle_report(
    parsed: MidiFile,
    report: MidoDifferentialReport,
) -> None:
    """Require the reusable oracle's evidence to cover this exact parse."""

    if not isinstance(report, MidoDifferentialReport):
        raise MaestroRawMidiAuditError(
            "Mido differential oracle returned an invalid report type"
        )
    channel_count = 0
    meta_count = 0
    sysex_count = 0
    for track in parsed.tracks:
        for event in track.events:
            if isinstance(event, MidiChannelEvent):
                channel_count += 1
            elif isinstance(event, MidiMetaEvent):
                meta_count += 1
            elif isinstance(event, MidiSysExEvent):
                sysex_count += 1
            else:
                raise AssertionError("raw parser returned an unknown event class")
    expected = (
        parsed.sha256,
        parsed.byte_length,
        PINNED_MIDO_ORACLE_VERSION,
        parsed.format_type,
        parsed.ticks_per_quarter_note,
        parsed.track_count,
        tuple(len(track.events) for track in parsed.tracks),
        tuple(track.end_tick for track in parsed.tracks),
        parsed.total_events,
        channel_count,
        meta_count,
        sysex_count,
        sysex_count,
    )
    observed = (
        report.source_sha256,
        report.source_byte_length,
        report.mido_version,
        report.format_type,
        report.ticks_per_quarter_note,
        report.track_count,
        report.track_event_counts,
        report.track_end_ticks,
        report.timing_events_compared,
        report.channel_events_compared,
        report.meta_events_compared,
        report.sysex_payloads_compared,
        report.sysex_status_fields_unavailable_from_mido,
    )
    if observed != expected or report.total_events_compared != parsed.total_events:
        raise MaestroRawMidiAuditError(
            "Mido differential report does not cover the exact parsed object"
        )


def audit_maestro_v3_raw_midi(
    inventory: MaestroArchiveInventory,
    trusted_root: PathLike,
    *,
    limits: MidiParseLimits,
    require_mido_oracle: bool = False,
) -> MaestroRawMidiAudit:
    """Verify and audit all 1,276 inventoried MAESTRO v3 MIDI files.

    ``limits`` is deliberately required: widening a parser resource boundary
    must be an explicit, reviewable call-site decision.  On any byte, parser,
    mutation, or requested-oracle mismatch, no partial audit is returned.
    """

    if not isinstance(inventory, MaestroArchiveInventory):
        raise TypeError("inventory must be a MaestroArchiveInventory")
    if not isinstance(limits, MidiParseLimits):
        raise TypeError("limits must be a MidiParseLimits instance")
    if not isinstance(require_mido_oracle, bool):
        raise TypeError("require_mido_oracle must be a boolean")
    root, resolved_root = _validate_root(trusted_root)
    oracle_version = (
        PINNED_MIDO_ORACLE_VERSION if require_mido_oracle else None
    )

    preflight = []
    for record in inventory.records:
        path, status = _validated_record_path(root, resolved_root, record)
        preflight.append((record, path, status))

    evidence = []
    signatures = []
    for record, path, status in preflight:
        data, signature = _read_and_verify_record(
            path,
            status,
            record,
            limits=limits,
        )
        try:
            parsed = parse_midi_bytes(data, limits=limits)
        except MidiFormatError as error:
            raise MaestroRawMidiAuditError(
                "raw MIDI parser failed at metadata row {}".format(
                    record.metadata_row_number
                )
            ) from error
        if parsed.sha256 != record.sha256 or parsed.byte_length != record.size_bytes:
            raise MaestroRawMidiAuditError(
                "raw parser byte identity disagrees with inventory"
            )
        oracle_passed = False
        if require_mido_oracle:
            try:
                oracle_report = validate_parsed_midi_against_mido(
                    parsed,
                    expected_version=PINNED_MIDO_ORACLE_VERSION,
                )
                _validate_oracle_report(parsed, oracle_report)
            except (
                MidoUnavailableError,
                MidoVersionError,
                MidoDifferentialError,
                MaestroRawMidiAuditError,
            ) as error:
                raise MaestroRawMidiAuditError(
                    "Mido differential oracle failed at metadata row {}: {}".format(
                        record.metadata_row_number,
                        error,
                    )
                ) from error
            oracle_passed = True
        evidence.append(
            _file_evidence(record, parsed, oracle_passed=oracle_passed)
        )
        signatures.append((record, path, signature))

    for record, expected_path, signature in signatures:
        final_path, final_status = _validated_record_path(
            root, resolved_root, record
        )
        if final_path != expected_path or _stat_signature(final_status) != signature:
            raise MaestroRawMidiAuditError(
                "MIDI corpus changed during audit at metadata row {}".format(
                    record.metadata_row_number
                )
            )

    return MaestroRawMidiAudit(
        inventory_manifest_sha256=inventory.manifest_sha256,
        limits=limits,
        oracle_required=require_mido_oracle,
        oracle_version=oracle_version,
        records=tuple(evidence),
    )


__all__ = [
    "PINNED_MIDO_ORACLE_VERSION",
    "MaestroRawMidiAggregate",
    "MaestroRawMidiAudit",
    "MaestroRawMidiAuditError",
    "MaestroRawMidiFileEvidence",
    "audit_maestro_v3_raw_midi",
]
