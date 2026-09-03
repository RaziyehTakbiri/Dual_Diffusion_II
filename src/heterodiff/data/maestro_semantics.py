"""Fail-closed semantic conversion for verified MAESTRO-style MIDI.

This module is intentionally downstream of :mod:`heterodiff.data.midi_raw`.
It does not parse bytes and it does not emit a model tensor.  It makes the
musical assumptions frozen in ``research/25_maestro_semantic_policy_gate.md``
executable: exact tempo integration, track-local MIDI-port state, atomic
same-tick note pairing, and an exact MIDI-clock sixteenth grid.

The source :class:`~heterodiff.data.midi_raw.MidiFile` remains the lossless
record.  Every derived note and side-table fact retains raw event provenance,
and the private manifest commits to exact rational values rather than their
convenience float64 views.  ``public_summary`` contains aggregates only.
"""

from __future__ import annotations

import hashlib
from bisect import bisect_right
from collections import deque
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Deque, Dict, List, Mapping, Optional, Tuple

from heterodiff.artifacts.manifest import canonical_json_dumps, sha256_bytes

from .maestro_inventory import MaestroMidiInventory
from .midi_raw import MidiChannelEvent, MidiFile, MidiMetaEvent


_SOURCE_SPLITS = frozenset(("train", "validation", "test"))
_SHA256_CHARACTERS = frozenset("0123456789abcdef")
_DEFAULT_TEMPO = 500_000
_PEDAL_CONTROLLERS = frozenset((64, 66, 67))
_NOTE_ID_DOMAIN = b"heterodiff-maestro-semantic-note-v1\0"
_MANIFEST_SCHEMA_VERSION = 1


class MaestroSemanticError(ValueError):
    """Raised when raw facts do not admit the frozen semantic policy."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "SEMANTIC_POLICY_FAILURE",
    ) -> None:
        if not isinstance(message, str) or not message:
            raise TypeError("message must be a nonempty string")
        if (
            not isinstance(code, str)
            or not code
            or not code[0].isupper()
            or any(
                not (
                    character == "_"
                    or character.isupper()
                    or character.isdigit()
                )
                for character in code
            )
        ):
            raise ValueError("code must use nonempty uppercase snake case")
        super().__init__(message)
        self.code = code


def _plain_int(value: object, *, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{} must be an integer".format(name))
    if value < minimum:
        raise ValueError("{} must be at least {}".format(name, minimum))
    return value


def _sha256(value: object, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _SHA256_CHARACTERS for character in value)
    ):
        raise ValueError("{} must be a lowercase SHA-256 digest".format(name))
    return value


def _source_split(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("source_split must be a string")
    if value not in _SOURCE_SPLITS:
        raise MaestroSemanticError(
            "source_split must retain one of test, train, or validation",
            code="INVALID_SOURCE_SPLIT",
        )
    return value


def _fraction(value: object, *, name: str, minimum: Optional[Fraction] = None) -> Fraction:
    if not isinstance(value, Fraction):
        raise TypeError("{} must be a Fraction".format(name))
    if minimum is not None and value < minimum:
        raise ValueError("{} is below its admitted lower bound".format(name))
    return value


def _fraction_dict(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


@dataclass(frozen=True)
class MaestroSemanticLimits:
    """Explicit ceilings for one raw-to-semantic conversion.

    These bounds supplement, rather than replace, the raw parser's byte and
    event limits.  They constrain every potentially large semantic side table
    and the maximum number of simultaneously open notes.
    """

    maximum_tracks: int = 256
    maximum_total_events: int = 150_000
    maximum_note_events: int = 150_000
    maximum_note_onsets: int = 100_000
    maximum_open_notes: int = 100_000
    maximum_atomic_note_events: int = 20_000
    maximum_tempo_events: int = 20_000
    maximum_tempo_points: int = 20_001
    maximum_control_changes: int = 150_000
    maximum_midi_port_events: int = 20_000
    maximum_time_signatures: int = 20_000

    def __post_init__(self) -> None:
        for name in (
            "maximum_tracks",
            "maximum_total_events",
            "maximum_note_events",
            "maximum_note_onsets",
            "maximum_open_notes",
            "maximum_atomic_note_events",
            "maximum_tempo_events",
            "maximum_tempo_points",
            "maximum_control_changes",
            "maximum_midi_port_events",
            "maximum_time_signatures",
        ):
            _plain_int(getattr(self, name), name=name, minimum=1)
        if self.maximum_note_events > self.maximum_total_events:
            raise ValueError("maximum_note_events cannot exceed maximum_total_events")
        if self.maximum_note_onsets > self.maximum_note_events:
            raise ValueError("maximum_note_onsets cannot exceed maximum_note_events")
        if self.maximum_open_notes > self.maximum_note_onsets:
            raise ValueError("maximum_open_notes cannot exceed maximum_note_onsets")
        if self.maximum_atomic_note_events > self.maximum_note_events:
            raise ValueError(
                "maximum_atomic_note_events cannot exceed maximum_note_events"
            )
        for name in (
            "maximum_tempo_events",
            "maximum_control_changes",
            "maximum_midi_port_events",
            "maximum_time_signatures",
        ):
            if getattr(self, name) > self.maximum_total_events:
                raise ValueError("{} cannot exceed maximum_total_events".format(name))


DEFAULT_MAESTRO_SEMANTIC_LIMITS = MaestroSemanticLimits()


@dataclass(frozen=True)
class ChannelEventProvenance:
    """Exact channel-event fields required to audit a semantic fact."""

    track_index: int
    event_index: int
    delta_ticks: int
    absolute_tick: int
    track_byte_offset: int
    status: int
    used_running_status: bool
    message_type: str
    data: bytes
    encoded_bytes: bytes

    def __post_init__(self) -> None:
        for name in (
            "track_index",
            "event_index",
            "delta_ticks",
            "absolute_tick",
            "track_byte_offset",
        ):
            _plain_int(getattr(self, name), name=name)
        if isinstance(self.status, bool) or not isinstance(self.status, int):
            raise TypeError("status must be an integer")
        if not 0x80 <= self.status <= 0xEF:
            raise ValueError("status must be a MIDI channel status")
        if not isinstance(self.used_running_status, bool):
            raise TypeError("used_running_status must be a boolean")
        if not isinstance(self.message_type, str) or not self.message_type:
            raise TypeError("message_type must be a nonempty string")
        if not isinstance(self.data, bytes) or not isinstance(self.encoded_bytes, bytes):
            raise TypeError("data and encoded_bytes must be bytes")
        if not self.encoded_bytes:
            raise ValueError("encoded_bytes must not be empty")
        # Reuse the raw boundary's complete wire-field validation.  This keeps
        # direct construction as strict as conversion from a parsed event.
        MidiChannelEvent(
            track_index=self.track_index,
            event_index=self.event_index,
            delta_ticks=self.delta_ticks,
            absolute_ticks=self.absolute_tick,
            track_byte_offset=self.track_byte_offset,
            encoded_bytes=self.encoded_bytes,
            status=self.status,
            used_running_status=self.used_running_status,
            message_type=self.message_type,
            channel=self.status & 0x0F,
            data=self.data,
        )

    @classmethod
    def from_event(cls, event: MidiChannelEvent) -> "ChannelEventProvenance":
        if not isinstance(event, MidiChannelEvent):
            raise TypeError("event must be a MidiChannelEvent")
        return cls(
            track_index=event.track_index,
            event_index=event.event_index,
            delta_ticks=event.delta_ticks,
            absolute_tick=event.absolute_ticks,
            track_byte_offset=event.track_byte_offset,
            status=event.status,
            used_running_status=event.used_running_status,
            message_type=event.message_type,
            data=event.data,
            encoded_bytes=event.encoded_bytes,
        )

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "track_index": self.track_index,
            "event_index": self.event_index,
            "delta_ticks": self.delta_ticks,
            "absolute_tick": self.absolute_tick,
            "track_byte_offset": self.track_byte_offset,
            "status": self.status,
            "used_running_status": self.used_running_status,
            "message_type": self.message_type,
            "data_hex": self.data.hex(),
            "encoded_bytes_hex": self.encoded_bytes.hex(),
        }


@dataclass(frozen=True)
class MetaEventProvenance:
    """Exact meta-event fields required to audit a derived map or side table."""

    track_index: int
    event_index: int
    delta_ticks: int
    absolute_tick: int
    track_byte_offset: int
    meta_type: int
    meta_name: str
    payload: bytes
    encoded_bytes: bytes

    def __post_init__(self) -> None:
        for name in (
            "track_index",
            "event_index",
            "delta_ticks",
            "absolute_tick",
            "track_byte_offset",
        ):
            _plain_int(getattr(self, name), name=name)
        if isinstance(self.meta_type, bool) or not isinstance(self.meta_type, int):
            raise TypeError("meta_type must be an integer")
        if not 0 <= self.meta_type <= 0x7F:
            raise ValueError("meta_type must be in 0..127")
        if not isinstance(self.meta_name, str) or not self.meta_name:
            raise TypeError("meta_name must be a nonempty string")
        if not isinstance(self.payload, bytes) or not isinstance(self.encoded_bytes, bytes):
            raise TypeError("payload and encoded_bytes must be bytes")
        if not self.encoded_bytes:
            raise ValueError("encoded_bytes must not be empty")
        MidiMetaEvent(
            track_index=self.track_index,
            event_index=self.event_index,
            delta_ticks=self.delta_ticks,
            absolute_ticks=self.absolute_tick,
            track_byte_offset=self.track_byte_offset,
            encoded_bytes=self.encoded_bytes,
            meta_type=self.meta_type,
            meta_name=self.meta_name,
            payload=self.payload,
        )

    @classmethod
    def from_event(cls, event: MidiMetaEvent) -> "MetaEventProvenance":
        if not isinstance(event, MidiMetaEvent):
            raise TypeError("event must be a MidiMetaEvent")
        return cls(
            track_index=event.track_index,
            event_index=event.event_index,
            delta_ticks=event.delta_ticks,
            absolute_tick=event.absolute_ticks,
            track_byte_offset=event.track_byte_offset,
            meta_type=event.meta_type,
            meta_name=event.meta_name,
            payload=event.payload,
            encoded_bytes=event.encoded_bytes,
        )

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "track_index": self.track_index,
            "event_index": self.event_index,
            "delta_ticks": self.delta_ticks,
            "absolute_tick": self.absolute_tick,
            "track_byte_offset": self.track_byte_offset,
            "meta_type": self.meta_type,
            "meta_name": self.meta_name,
            "payload_hex": self.payload.hex(),
            "encoded_bytes_hex": self.encoded_bytes.hex(),
        }


@dataclass(frozen=True)
class TempoPoint:
    """One effective tempo-map point with exact elapsed microseconds."""

    tick: int
    microseconds_per_quarter_note: int
    elapsed_microseconds: Fraction
    source_events: Tuple[MetaEventProvenance, ...]
    is_implicit_default: bool

    def __post_init__(self) -> None:
        _plain_int(self.tick, name="tick")
        _plain_int(
            self.microseconds_per_quarter_note,
            name="microseconds_per_quarter_note",
            minimum=1,
        )
        if self.microseconds_per_quarter_note > 0xFFFFFF:
            raise ValueError("tempo exceeds the three-byte MIDI field")
        _fraction(
            self.elapsed_microseconds,
            name="elapsed_microseconds",
            minimum=Fraction(0),
        )
        if not isinstance(self.source_events, tuple) or any(
            not isinstance(item, MetaEventProvenance) for item in self.source_events
        ):
            raise TypeError("source_events must be a tuple of MetaEventProvenance")
        if not isinstance(self.is_implicit_default, bool):
            raise TypeError("is_implicit_default must be a boolean")
        if self.is_implicit_default:
            if self.tick != 0 or self.microseconds_per_quarter_note != _DEFAULT_TEMPO:
                raise ValueError("the implicit tempo must be 500000 at tick zero")
            if self.source_events:
                raise ValueError("an implicit tempo point cannot have source events")
        elif not self.source_events:
            raise ValueError("an explicit tempo point must retain source provenance")
        if not self.is_implicit_default:
            source_order = tuple(
                (source.track_index, source.event_index)
                for source in self.source_events
            )
            if source_order != tuple(sorted(set(source_order))):
                raise ValueError("tempo source provenance must be sorted and unique")
            for source in self.source_events:
                if source.meta_type != 0x51 or source.meta_name != "set_tempo":
                    raise ValueError("tempo provenance must identify set_tempo events")
                if source.absolute_tick != self.tick:
                    raise ValueError("tempo provenance tick does not match its map point")
                value = int.from_bytes(source.payload, byteorder="big", signed=False)
                if value != self.microseconds_per_quarter_note:
                    raise ValueError("tempo provenance payload does not match map value")

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "tick": self.tick,
            "microseconds_per_quarter_note": self.microseconds_per_quarter_note,
            "elapsed_microseconds": _fraction_dict(self.elapsed_microseconds),
            "is_implicit_default": self.is_implicit_default,
            "source_events": [item.to_private_dict() for item in self.source_events],
        }


@dataclass(frozen=True)
class MaestroTempoMap:
    """A piecewise-constant, exact PPQ tempo map."""

    ticks_per_quarter_note: int
    points: Tuple[TempoPoint, ...]
    _ticks: Tuple[int, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        _plain_int(
            self.ticks_per_quarter_note,
            name="ticks_per_quarter_note",
            minimum=1,
        )
        if not isinstance(self.points, tuple) or not self.points:
            raise ValueError("points must be a nonempty tuple")
        previous: Optional[TempoPoint] = None
        for point in self.points:
            if not isinstance(point, TempoPoint):
                raise TypeError("points must contain TempoPoint values")
            if previous is None:
                if point.tick != 0 or point.elapsed_microseconds != 0:
                    raise ValueError("tempo map must begin at tick zero and time zero")
            else:
                if point.tick <= previous.tick:
                    raise ValueError("tempo-map ticks must be strictly increasing")
                expected = previous.elapsed_microseconds + Fraction(
                    (point.tick - previous.tick)
                    * previous.microseconds_per_quarter_note,
                    self.ticks_per_quarter_note,
                )
                if point.elapsed_microseconds != expected:
                    raise ValueError("tempo-map elapsed time is inconsistent")
            previous = point
        object.__setattr__(self, "_ticks", tuple(point.tick for point in self.points))

    @property
    def explicit_event_count(self) -> int:
        return sum(len(point.source_events) for point in self.points)

    def time_microseconds_at(self, tick: int) -> Fraction:
        _plain_int(tick, name="tick")
        point = self.points[bisect_right(self._ticks, tick) - 1]
        return point.elapsed_microseconds + Fraction(
            (tick - point.tick) * point.microseconds_per_quarter_note,
            self.ticks_per_quarter_note,
        )

    def time_seconds_at(self, tick: int) -> float:
        """Return the sole convenience float conversion of the exact map."""

        return float(self.time_microseconds_at(tick) / 1_000_000)

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "ticks_per_quarter_note": self.ticks_per_quarter_note,
            "points": [point.to_private_dict() for point in self.points],
        }


@dataclass(frozen=True)
class MidiPortFact:
    port: int
    time_microseconds: Fraction
    time_seconds: float
    provenance: MetaEventProvenance

    def __post_init__(self) -> None:
        _plain_int(self.port, name="port")
        if self.port > 127:
            raise ValueError("port must be in 0..127")
        _fraction(self.time_microseconds, name="time_microseconds", minimum=Fraction(0))
        if not isinstance(self.time_seconds, float):
            raise TypeError("time_seconds must be a float")
        if not isinstance(self.provenance, MetaEventProvenance):
            raise TypeError("provenance must be MetaEventProvenance")
        if self.time_seconds != float(self.time_microseconds / 1_000_000):
            raise ValueError("time_seconds does not match exact microseconds")
        if (
            self.provenance.meta_type != 0x21
            or self.provenance.meta_name != "midi_port"
            or self.provenance.payload != bytes((self.port,))
        ):
            raise ValueError("MIDI-port provenance does not match the fact")

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "port": self.port,
            "time_microseconds": _fraction_dict(self.time_microseconds),
            "provenance": self.provenance.to_private_dict(),
        }


@dataclass(frozen=True)
class ControllerFact:
    port: int
    channel: int
    controller: int
    value: int
    time_microseconds: Fraction
    time_seconds: float
    provenance: ChannelEventProvenance

    def __post_init__(self) -> None:
        for name in ("port", "channel", "controller", "value"):
            _plain_int(getattr(self, name), name=name)
        if self.port > 127 or self.channel > 15:
            raise ValueError("port/channel is outside the MIDI range")
        if self.controller > 127 or self.value > 127:
            raise ValueError("controller/value is outside the MIDI range")
        _fraction(self.time_microseconds, name="time_microseconds", minimum=Fraction(0))
        if not isinstance(self.time_seconds, float):
            raise TypeError("time_seconds must be a float")
        if not isinstance(self.provenance, ChannelEventProvenance):
            raise TypeError("provenance must be ChannelEventProvenance")
        if self.time_seconds != float(self.time_microseconds / 1_000_000):
            raise ValueError("time_seconds does not match exact microseconds")
        if (
            self.provenance.message_type != "control_change"
            or (self.provenance.status & 0x0F) != self.channel
            or self.provenance.data != bytes((self.controller, self.value))
        ):
            raise ValueError("controller provenance does not match the fact")

    @property
    def is_pedal(self) -> bool:
        return self.controller in _PEDAL_CONTROLLERS

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "port": self.port,
            "channel": self.channel,
            "controller": self.controller,
            "value": self.value,
            "time_microseconds": _fraction_dict(self.time_microseconds),
            "provenance": self.provenance.to_private_dict(),
        }


@dataclass(frozen=True)
class TimeSignatureFact:
    fields: Tuple[int, int, int, int]
    time_microseconds: Fraction
    time_seconds: float
    provenance: MetaEventProvenance

    def __post_init__(self) -> None:
        if (
            not isinstance(self.fields, tuple)
            or len(self.fields) != 4
            or any(isinstance(item, bool) or not isinstance(item, int) for item in self.fields)
            or any(not 0 <= item <= 255 for item in self.fields)
        ):
            raise ValueError("fields must be four MIDI meta-payload byte integers")
        _fraction(self.time_microseconds, name="time_microseconds", minimum=Fraction(0))
        if not isinstance(self.time_seconds, float):
            raise TypeError("time_seconds must be a float")
        if not isinstance(self.provenance, MetaEventProvenance):
            raise TypeError("provenance must be MetaEventProvenance")
        if self.time_seconds != float(self.time_microseconds / 1_000_000):
            raise ValueError("time_seconds does not match exact microseconds")
        if (
            self.provenance.meta_type != 0x58
            or self.provenance.meta_name != "time_signature"
            or tuple(self.provenance.payload) != self.fields
        ):
            raise ValueError("time-signature provenance does not match the fact")

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "fields": list(self.fields),
            "time_microseconds": _fraction_dict(self.time_microseconds),
            "provenance": self.provenance.to_private_dict(),
        }


@dataclass(frozen=True)
class MaestroNoteOnset:
    """One paired positive onset with exact clock-grid marks."""

    note_id: str
    source_split: str
    source_midi_sha256: str
    port: int
    channel: int
    pitch: int
    onset_tick: int
    release_tick: int
    onset_velocity: int
    release_velocity: int
    onset_spelling: str
    closure_spelling: str
    onset_provenance: ChannelEventProvenance
    closure_provenance: ChannelEventProvenance
    onset_time_microseconds: Fraction
    release_time_microseconds: Fraction
    onset_time_seconds: float
    release_time_seconds: float
    grid_index: int
    velocity_normalized_exact: Fraction
    velocity_normalized: float
    midi_clock_onset_offset_exact: Fraction
    midi_clock_onset_offset: float

    def __post_init__(self) -> None:
        _sha256(self.note_id, name="note_id")
        _source_split(self.source_split)
        _sha256(self.source_midi_sha256, name="source_midi_sha256")
        for name in (
            "port",
            "channel",
            "pitch",
            "onset_tick",
            "release_tick",
            "onset_velocity",
            "release_velocity",
            "grid_index",
        ):
            _plain_int(getattr(self, name), name=name)
        if self.port > 127 or self.channel > 15 or self.pitch > 127:
            raise ValueError("port/channel/pitch is outside the MIDI range")
        if not 1 <= self.onset_velocity <= 127:
            raise ValueError("onset_velocity must be in 1..127")
        if self.release_velocity > 127:
            raise ValueError("release_velocity must be in 0..127")
        if self.release_tick <= self.onset_tick:
            raise ValueError("paired note duration must be positive")
        if self.onset_spelling != "note_on_positive_velocity":
            raise ValueError("onset_spelling must identify a positive note_on")
        if self.closure_spelling not in ("note_off", "note_on_velocity_zero"):
            raise ValueError("closure_spelling is not admitted")
        if not isinstance(self.onset_provenance, ChannelEventProvenance) or not isinstance(
            self.closure_provenance, ChannelEventProvenance
        ):
            raise TypeError("note provenance values must be ChannelEventProvenance")
        onset_time = _fraction(
            self.onset_time_microseconds,
            name="onset_time_microseconds",
            minimum=Fraction(0),
        )
        release_time = _fraction(
            self.release_time_microseconds,
            name="release_time_microseconds",
            minimum=Fraction(0),
        )
        if release_time <= onset_time:
            raise ValueError("release time must be after onset time")
        for name in (
            "onset_time_seconds",
            "release_time_seconds",
            "velocity_normalized",
            "midi_clock_onset_offset",
        ):
            if not isinstance(getattr(self, name), float):
                raise TypeError("{} must be a float".format(name))
        if self.onset_time_seconds != float(onset_time / 1_000_000):
            raise ValueError("onset_time_seconds does not match exact microseconds")
        if self.release_time_seconds != float(release_time / 1_000_000):
            raise ValueError("release_time_seconds does not match exact microseconds")
        velocity = _fraction(
            self.velocity_normalized_exact,
            name="velocity_normalized_exact",
        )
        if velocity != Fraction(self.onset_velocity, 127):
            raise ValueError("velocity_normalized_exact is inconsistent")
        if self.velocity_normalized != float(velocity):
            raise ValueError("velocity_normalized does not match its exact value")
        offset = _fraction(
            self.midi_clock_onset_offset_exact,
            name="midi_clock_onset_offset_exact",
        )
        if not Fraction(-1) <= offset <= Fraction(1):
            raise ValueError("midi_clock_onset_offset_exact is outside [-1, 1]")
        if self.midi_clock_onset_offset != float(offset):
            raise ValueError("midi_clock_onset_offset does not match its exact value")
        onset = self.onset_provenance
        closure = self.closure_provenance
        if (
            onset.absolute_tick != self.onset_tick
            or onset.message_type != "note_on"
            or (onset.status & 0x0F) != self.channel
            or onset.data != bytes((self.pitch, self.onset_velocity))
        ):
            raise ValueError("onset provenance does not match the note row")
        expected_closure_type = (
            "note_off" if self.closure_spelling == "note_off" else "note_on"
        )
        if (
            closure.absolute_tick != self.release_tick
            or closure.message_type != expected_closure_type
            or (closure.status & 0x0F) != self.channel
            or closure.data != bytes((self.pitch, self.release_velocity))
        ):
            raise ValueError("closure provenance does not match the note row")
        if self.closure_spelling == "note_on_velocity_zero" and self.release_velocity != 0:
            raise ValueError("zero-velocity note_on closure must have velocity zero")
        if self.note_id != _stable_note_id_from_indices(
            self.source_midi_sha256,
            onset.track_index,
            onset.event_index,
        ):
            raise ValueError("note_id does not match source and onset provenance")

    @property
    def identity(self) -> Tuple[int, int, int]:
        return (self.port, self.channel, self.pitch)

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "note_id": self.note_id,
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "identity": {
                "port": self.port,
                "channel": self.channel,
                "pitch": self.pitch,
            },
            "onset_tick": self.onset_tick,
            "release_tick": self.release_tick,
            "onset_velocity": self.onset_velocity,
            "release_velocity": self.release_velocity,
            "onset_spelling": self.onset_spelling,
            "closure_spelling": self.closure_spelling,
            "onset_provenance": self.onset_provenance.to_private_dict(),
            "closure_provenance": self.closure_provenance.to_private_dict(),
            "onset_time_microseconds": _fraction_dict(self.onset_time_microseconds),
            "release_time_microseconds": _fraction_dict(self.release_time_microseconds),
            "grid_index": self.grid_index,
            "velocity_normalized_exact": _fraction_dict(
                self.velocity_normalized_exact
            ),
            "midi_clock_onset_offset_exact": _fraction_dict(
                self.midi_clock_onset_offset_exact
            ),
        }


@dataclass(frozen=True)
class ProjectionCollision:
    grid_index: int
    pitch: int
    note_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        _plain_int(self.grid_index, name="grid_index")
        _plain_int(self.pitch, name="pitch")
        if self.pitch > 127:
            raise ValueError("pitch must be in 0..127")
        if not isinstance(self.note_ids, tuple) or len(self.note_ids) < 2:
            raise ValueError("a collision must contain at least two note IDs")
        for note_id in self.note_ids:
            _sha256(note_id, name="note_id")
        if self.note_ids != tuple(sorted(set(self.note_ids))):
            raise ValueError("collision note_ids must be sorted and unique")

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "grid_index": self.grid_index,
            "pitch": self.pitch,
            "note_ids": list(self.note_ids),
        }


@dataclass(frozen=True)
class MaestroSemanticDiagnostics:
    pitch_minimum: Optional[int]
    pitch_maximum: Optional[int]
    out_of_88_key_note_count: int
    note_producing_streams: Tuple[Tuple[int, int], ...]
    projection_collisions: Tuple[ProjectionCollision, ...]

    def __post_init__(self) -> None:
        if (self.pitch_minimum is None) != (self.pitch_maximum is None):
            raise ValueError("pitch bounds must both be present or both be absent")
        if self.pitch_minimum is not None:
            _plain_int(self.pitch_minimum, name="pitch_minimum")
            _plain_int(self.pitch_maximum, name="pitch_maximum")
            if self.pitch_maximum is None or self.pitch_maximum < self.pitch_minimum:
                raise ValueError("pitch bounds are inconsistent")
            if self.pitch_maximum > 127:
                raise ValueError("pitch bounds exceed the MIDI range")
        _plain_int(self.out_of_88_key_note_count, name="out_of_88_key_note_count")
        if not isinstance(self.note_producing_streams, tuple):
            raise TypeError("note_producing_streams must be a tuple")
        if self.note_producing_streams != tuple(sorted(set(self.note_producing_streams))):
            raise ValueError("note_producing_streams must be sorted and unique")
        for stream in self.note_producing_streams:
            if (
                not isinstance(stream, tuple)
                or len(stream) != 2
                or any(isinstance(item, bool) or not isinstance(item, int) for item in stream)
                or not 0 <= stream[0] <= 127
                or not 0 <= stream[1] <= 15
            ):
                raise ValueError("note-producing streams must be (port, channel) pairs")
        if not isinstance(self.projection_collisions, tuple) or any(
            not isinstance(item, ProjectionCollision)
            for item in self.projection_collisions
        ):
            raise TypeError("projection_collisions must contain ProjectionCollision values")
        collision_keys = tuple(
            (item.grid_index, item.pitch) for item in self.projection_collisions
        )
        if collision_keys != tuple(sorted(set(collision_keys))):
            raise ValueError("projection collisions must be unique and sorted")
        if self.pitch_minimum is None:
            if (
                self.out_of_88_key_note_count
                or self.note_producing_streams
                or self.projection_collisions
            ):
                raise ValueError("empty pitch bounds require empty diagnostics")
        else:
            if not self.note_producing_streams:
                raise ValueError("nonempty pitch bounds require a note-producing stream")
            for collision in self.projection_collisions:
                if not self.pitch_minimum <= collision.pitch <= self.pitch_maximum:
                    raise ValueError("collision pitch is outside diagnostic bounds")

    @property
    def has_out_of_88_key_support(self) -> bool:
        return self.out_of_88_key_note_count > 0

    @property
    def has_multiple_note_streams(self) -> bool:
        return len(self.note_producing_streams) > 1

    @property
    def has_projection_collisions(self) -> bool:
        return bool(self.projection_collisions)

    @property
    def manuscript_projection_admitted(self) -> bool:
        return self.pitch_minimum is not None and len(self.note_producing_streams) == 1 and not (
            self.has_out_of_88_key_support
            or self.has_multiple_note_streams
            or self.has_projection_collisions
        )

    @property
    def collision_event_count(self) -> int:
        return sum(len(item.note_ids) for item in self.projection_collisions)

    @property
    def collision_excess_event_count(self) -> int:
        return sum(len(item.note_ids) - 1 for item in self.projection_collisions)

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "pitch_minimum": self.pitch_minimum,
            "pitch_maximum": self.pitch_maximum,
            "out_of_88_key_note_count": self.out_of_88_key_note_count,
            "note_producing_streams": [list(item) for item in self.note_producing_streams],
            "projection_collisions": [
                item.to_private_dict() for item in self.projection_collisions
            ],
            "manuscript_projection_admitted": self.manuscript_projection_admitted,
        }


@dataclass(frozen=True)
class MaestroSemanticPiece:
    """Immutable semantic table, exact side tables, and projection diagnostics."""

    source_split: str
    source_midi_sha256: str
    format_type: int
    ticks_per_quarter_note: int
    grid_spacing_ticks: int
    tempo_map: MaestroTempoMap
    notes: Tuple[MaestroNoteOnset, ...]
    controllers: Tuple[ControllerFact, ...]
    midi_ports: Tuple[MidiPortFact, ...]
    time_signatures: Tuple[TimeSignatureFact, ...]
    diagnostics: MaestroSemanticDiagnostics
    schema_version: int = _MANIFEST_SCHEMA_VERSION
    manifest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _source_split(self.source_split)
        _sha256(self.source_midi_sha256, name="source_midi_sha256")
        _plain_int(self.schema_version, name="schema_version", minimum=1)
        _plain_int(self.format_type, name="format_type")
        if self.format_type not in (0, 1):
            raise ValueError("format_type must be 0 or 1")
        _plain_int(
            self.ticks_per_quarter_note,
            name="ticks_per_quarter_note",
            minimum=1,
        )
        _plain_int(self.grid_spacing_ticks, name="grid_spacing_ticks", minimum=1)
        if self.ticks_per_quarter_note % 4 != 0:
            raise ValueError("ticks_per_quarter_note must be divisible by four")
        if self.grid_spacing_ticks != self.ticks_per_quarter_note // 4:
            raise ValueError("grid_spacing_ticks must equal PPQN/4")
        if not isinstance(self.tempo_map, MaestroTempoMap):
            raise TypeError("tempo_map must be MaestroTempoMap")
        if self.tempo_map.ticks_per_quarter_note != self.ticks_per_quarter_note:
            raise ValueError("tempo map PPQN is inconsistent")
        typed_tuples = (
            ("notes", self.notes, MaestroNoteOnset),
            ("controllers", self.controllers, ControllerFact),
            ("midi_ports", self.midi_ports, MidiPortFact),
            ("time_signatures", self.time_signatures, TimeSignatureFact),
        )
        for name, values, expected_type in typed_tuples:
            if not isinstance(values, tuple) or any(
                not isinstance(value, expected_type) for value in values
            ):
                raise TypeError("{} must be a tuple of {}".format(name, expected_type.__name__))
        if not isinstance(self.diagnostics, MaestroSemanticDiagnostics):
            raise TypeError("diagnostics must be MaestroSemanticDiagnostics")
        note_order = tuple(
            (note.onset_tick, note.onset_provenance.track_index, note.onset_provenance.event_index)
            for note in self.notes
        )
        if note_order != tuple(sorted(note_order)):
            raise ValueError("notes must use canonical onset/provenance order")
        note_ids = tuple(note.note_id for note in self.notes)
        if len(set(note_ids)) != len(note_ids):
            raise ValueError("note IDs must be unique")
        note_event_keys = tuple(
            (note.onset_provenance.track_index, note.onset_provenance.event_index)
            for note in self.notes
        ) + tuple(
            (note.closure_provenance.track_index, note.closure_provenance.event_index)
            for note in self.notes
        )
        if len(set(note_event_keys)) != len(note_event_keys):
            raise ValueError("one raw note event cannot appear in multiple note rows")
        for note in self.notes:
            if note.source_split != self.source_split or note.source_midi_sha256 != self.source_midi_sha256:
                raise ValueError("note source identity is inconsistent with its piece")
            expected_grid_index = (
                2 * note.onset_tick + self.grid_spacing_ticks - 1
            ) // (2 * self.grid_spacing_ticks)
            expected_offset = Fraction(
                2
                * (
                    note.onset_tick
                    - expected_grid_index * self.grid_spacing_ticks
                ),
                self.grid_spacing_ticks,
            )
            if note.grid_index != expected_grid_index:
                raise ValueError("note grid_index is inconsistent with the frozen grid")
            if note.midi_clock_onset_offset_exact != expected_offset:
                raise ValueError("note onset offset is inconsistent with the frozen grid")
            if note.onset_time_microseconds != self.tempo_map.time_microseconds_at(
                note.onset_tick
            ):
                raise ValueError("note onset time is inconsistent with the tempo map")
            if note.release_time_microseconds != self.tempo_map.time_microseconds_at(
                note.release_tick
            ):
                raise ValueError("note release time is inconsistent with the tempo map")

        controller_order = tuple(
            (
                item.provenance.absolute_tick,
                item.provenance.track_index,
                item.provenance.event_index,
            )
            for item in self.controllers
        )
        if controller_order != tuple(sorted(controller_order)):
            raise ValueError("controllers must use canonical tick/provenance order")
        if len(set(controller_order)) != len(controller_order):
            raise ValueError("controller provenance must be unique")
        for item in self.controllers:
            if item.time_microseconds != self.tempo_map.time_microseconds_at(
                item.provenance.absolute_tick
            ):
                raise ValueError("controller time is inconsistent with the tempo map")

        port_order = tuple(
            (
                item.provenance.absolute_tick,
                item.provenance.track_index,
                item.provenance.event_index,
            )
            for item in self.midi_ports
        )
        if port_order != tuple(sorted(port_order)):
            raise ValueError("MIDI-port facts must use canonical tick/provenance order")
        if len(set(port_order)) != len(port_order):
            raise ValueError("MIDI-port provenance must be unique")
        for item in self.midi_ports:
            if item.time_microseconds != self.tempo_map.time_microseconds_at(
                item.provenance.absolute_tick
            ):
                raise ValueError("MIDI-port time is inconsistent with the tempo map")

        signature_order = tuple(
            (
                item.provenance.absolute_tick,
                item.provenance.track_index,
                item.provenance.event_index,
            )
            for item in self.time_signatures
        )
        if signature_order != tuple(sorted(signature_order)):
            raise ValueError("time signatures must use canonical tick/provenance order")
        if len(set(signature_order)) != len(signature_order):
            raise ValueError("time-signature provenance must be unique")
        for item in self.time_signatures:
            if item.time_microseconds != self.tempo_map.time_microseconds_at(
                item.provenance.absolute_tick
            ):
                raise ValueError("time-signature time is inconsistent with the tempo map")

        # Direct construction must not be able to rewrite the global FIFO
        # association or a track-local MIDI-port history while retaining
        # locally plausible rows.  The complete builder already enforces these
        # facts from the raw stream; replaying the retained provenance here
        # makes the immutable public value fail closed under dataclasses.replace
        # as well.  Completeness still belongs to the raw builder because a
        # standalone semantic value cannot prove that omitted raw events never
        # existed.
        channel_fact_keys = note_event_keys + tuple(
            (item.provenance.track_index, item.provenance.event_index)
            for item in self.controllers
        )
        if len(set(channel_fact_keys)) != len(channel_fact_keys):
            raise ValueError("channel-event provenance must be globally unique")

        tempo_sources = tuple(
            source
            for point in self.tempo_map.points
            for source in point.source_events
        )
        meta_fact_keys = tuple(
            (source.track_index, source.event_index) for source in tempo_sources
        ) + tuple(
            (item.provenance.track_index, item.provenance.event_index)
            for item in self.midi_ports
        ) + tuple(
            (item.provenance.track_index, item.provenance.event_index)
            for item in self.time_signatures
        )
        if len(set(meta_fact_keys)) != len(meta_fact_keys):
            raise ValueError("semantic meta-event provenance must be globally unique")
        all_semantic_fact_keys = channel_fact_keys + meta_fact_keys
        if len(set(all_semantic_fact_keys)) != len(all_semantic_fact_keys):
            raise ValueError("semantic raw-event provenance must be globally unique")

        port_changes: Dict[int, List[Tuple[int, int]]] = {}
        for fact in self.midi_ports:
            port_changes.setdefault(fact.provenance.track_index, []).append(
                (fact.provenance.event_index, fact.port)
            )

        def port_before(provenance: ChannelEventProvenance) -> int:
            current = 0
            for event_index, port in port_changes.get(provenance.track_index, []):
                if event_index >= provenance.event_index:
                    break
                current = port
            return current

        for note in self.notes:
            if port_before(note.onset_provenance) != note.port:
                raise ValueError("note onset port is inconsistent with MIDI-port history")
            if port_before(note.closure_provenance) != note.port:
                raise ValueError("note closure port is inconsistent with MIDI-port history")
        for controller in self.controllers:
            if port_before(controller.provenance) != controller.port:
                raise ValueError(
                    "controller port is inconsistent with MIDI-port history"
                )

        pairing_events = []
        for note in self.notes:
            pairing_events.append(
                (
                    note.onset_tick,
                    note.onset_provenance.track_index,
                    note.onset_provenance.event_index,
                    True,
                    note,
                )
            )
            pairing_events.append(
                (
                    note.release_tick,
                    note.closure_provenance.track_index,
                    note.closure_provenance.event_index,
                    False,
                    note,
                )
            )
        pairing_events.sort(key=lambda item: item[:3])
        queues: Dict[Tuple[int, int, int], Deque[MaestroNoteOnset]] = {}
        cursor = 0
        while cursor < len(pairing_events):
            tick = pairing_events[cursor][0]
            end = cursor + 1
            while end < len(pairing_events) and pairing_events[end][0] == tick:
                end += 1
            atomic = pairing_events[cursor:end]
            for _, _, _, is_open, note in atomic:
                if is_open:
                    continue
                queue = queues.get(note.identity)
                if not queue:
                    raise ValueError("semantic note rows contain an orphan closure")
                expected = queue.popleft()
                if not queue:
                    del queues[note.identity]
                if expected.note_id != note.note_id:
                    raise ValueError("semantic note rows do not retain FIFO pairing")
            for _, _, _, is_open, note in atomic:
                if is_open:
                    queues.setdefault(note.identity, deque()).append(note)
            cursor = end
        if queues:
            raise ValueError("semantic note rows contain a dangling onset")

        pitches = [note.pitch for note in self.notes]
        members: Dict[Tuple[int, int], List[str]] = {}
        for note in self.notes:
            members.setdefault((note.grid_index, note.pitch), []).append(note.note_id)
        expected_diagnostics = MaestroSemanticDiagnostics(
            pitch_minimum=min(pitches) if pitches else None,
            pitch_maximum=max(pitches) if pitches else None,
            out_of_88_key_note_count=sum(
                not 21 <= pitch <= 108 for pitch in pitches
            ),
            note_producing_streams=tuple(
                sorted({(note.port, note.channel) for note in self.notes})
            ),
            projection_collisions=tuple(
                ProjectionCollision(
                    grid_index=key[0],
                    pitch=key[1],
                    note_ids=tuple(sorted(ids)),
                )
                for key, ids in sorted(members.items())
                if len(ids) > 1
            ),
        )
        if self.diagnostics != expected_diagnostics:
            raise ValueError("semantic diagnostics do not exactly match note rows")
        if self.schema_version != _MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported semantic manifest schema_version")
        private_json = canonical_json_dumps(self._private_payload())
        object.__setattr__(
            self,
            "manifest_sha256",
            sha256_bytes(private_json.encode("utf-8")),
        )

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "gate": "maestro-midi-clock-onset-semantics-v1",
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "format_type": self.format_type,
            "ticks_per_quarter_note": self.ticks_per_quarter_note,
            "grid_spacing_ticks": self.grid_spacing_ticks,
            "tempo_map": self.tempo_map.to_private_dict(),
            "notes": [note.to_private_dict() for note in self.notes],
            "controllers": [item.to_private_dict() for item in self.controllers],
            "midi_ports": [item.to_private_dict() for item in self.midi_ports],
            "time_signatures": [item.to_private_dict() for item in self.time_signatures],
            "diagnostics": self.diagnostics.to_private_dict(),
        }

    def to_private_dict(self) -> Dict[str, object]:
        """Return a fresh exact, provenance-bearing local manifest."""

        return self._private_payload()

    def to_private_json(self) -> str:
        return canonical_json_dumps(self._private_payload())

    def grid_predecessor_duration_microseconds(self, grid_index: int) -> Fraction:
        """Return exact physical time from the preceding global grid point.

        Global grid index zero has no predecessor and is defined as zero.  A
        later window layer must call this with the global index; it must not
        reset the first frame of every window to zero.
        """

        _plain_int(grid_index, name="grid_index")
        if grid_index == 0:
            return Fraction(0)
        end_tick = grid_index * self.grid_spacing_ticks
        start_tick = end_tick - self.grid_spacing_ticks
        return self.tempo_map.time_microseconds_at(
            end_tick
        ) - self.tempo_map.time_microseconds_at(start_tick)

    def grid_predecessor_duration_seconds(self, grid_index: int) -> float:
        return float(
            self.grid_predecessor_duration_microseconds(grid_index) / 1_000_000
        )

    def public_summary(self) -> Mapping[str, object]:
        """Return release-safe counts without notes or event provenance."""

        closure_counts = {"note_off": 0, "note_on_velocity_zero": 0}
        for note in self.notes:
            closure_counts[note.closure_spelling] += 1
        return {
            "schema_version": self.schema_version,
            "gate": "maestro-midi-clock-onset-semantics-v1",
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "manifest_sha256": self.manifest_sha256,
            "format_type": self.format_type,
            "ticks_per_quarter_note": self.ticks_per_quarter_note,
            "grid_spacing_ticks": self.grid_spacing_ticks,
            "note_count": len(self.notes),
            "closure_spelling_counts": closure_counts,
            "controller_count": len(self.controllers),
            "pedal_fact_count": sum(item.is_pedal for item in self.controllers),
            "midi_port_event_count": len(self.midi_ports),
            "time_signature_count": len(self.time_signatures),
            "tempo_point_count": len(self.tempo_map.points),
            "explicit_tempo_event_count": self.tempo_map.explicit_event_count,
            "pitch_minimum": self.diagnostics.pitch_minimum,
            "pitch_maximum": self.diagnostics.pitch_maximum,
            "out_of_88_key_note_count": self.diagnostics.out_of_88_key_note_count,
            "note_producing_stream_count": len(
                self.diagnostics.note_producing_streams
            ),
            "projection_collision_cell_count": len(
                self.diagnostics.projection_collisions
            ),
            "projection_collision_event_count": self.diagnostics.collision_event_count,
            "projection_collision_excess_event_count": (
                self.diagnostics.collision_excess_event_count
            ),
            "manuscript_projection_admitted": (
                self.diagnostics.manuscript_projection_admitted
            ),
            "claim_boundary": {
                "midi_clock_grid_not_score_grid": True,
                "pedal_applied_to_duration": False,
                "lossy_tensor_emitted": False,
                "source_split_reassigned": False,
            },
            "privacy": {
                "note_rows_included": False,
                "raw_event_provenance_included": False,
                "source_paths_included": False,
            },
        }


@dataclass(frozen=True)
class _AnnotatedNoteEvent:
    event: MidiChannelEvent
    port: int
    is_open: bool
    closure_spelling: Optional[str]

    @property
    def identity(self) -> Tuple[int, int, int]:
        note = self.event.note
        if note is None:
            raise AssertionError("annotated note event has no MIDI note")
        return (self.port, self.event.channel, note)


@dataclass(frozen=True)
class _AnnotatedController:
    event: MidiChannelEvent
    port: int


def _build_tempo_map(
    midi: MidiFile,
    tempo_events: Tuple[MidiMetaEvent, ...],
    *,
    limits: MaestroSemanticLimits,
) -> MaestroTempoMap:
    by_tick: Dict[int, List[MidiMetaEvent]] = {}
    for event in tempo_events:
        value = event.microseconds_per_quarter_note
        if value is None:
            raise AssertionError("non-tempo event reached tempo-map construction")
        if value == 0:
            raise MaestroSemanticError(
                "tempo must be positive", code="NONPOSITIVE_TEMPO"
            )
        by_tick.setdefault(event.absolute_ticks, []).append(event)
    effective_point_count = len(by_tick) + int(0 not in by_tick)
    if effective_point_count > limits.maximum_tempo_points:
        raise MaestroSemanticError(
            "distinct tempo ticks exceed maximum_tempo_points",
            code="LIMIT_TEMPO_POINTS",
        )

    effective: List[Tuple[int, int, Tuple[MetaEventProvenance, ...], bool]] = []
    if 0 not in by_tick:
        effective.append((0, _DEFAULT_TEMPO, (), True))
    for tick in sorted(by_tick):
        events = sorted(by_tick[tick], key=lambda item: (item.track_index, item.event_index))
        values = {event.microseconds_per_quarter_note for event in events}
        if len(values) != 1:
            raise MaestroSemanticError(
                "conflicting tempo values occur at tick {}".format(tick),
                code="CONFLICTING_TEMPO_VALUES",
            )
        value = next(iter(values))
        if value is None or value <= 0:
            raise MaestroSemanticError(
                "tempo must be positive", code="NONPOSITIVE_TEMPO"
            )
        effective.append(
            (
                tick,
                value,
                tuple(MetaEventProvenance.from_event(event) for event in events),
                False,
            )
        )

    points: List[TempoPoint] = []
    elapsed = Fraction(0)
    previous_tick = 0
    previous_tempo = effective[0][1]
    for index, (tick, tempo, sources, implicit) in enumerate(effective):
        if index:
            elapsed += Fraction(
                (tick - previous_tick) * previous_tempo,
                midi.ticks_per_quarter_note,
            )
        points.append(
            TempoPoint(
                tick=tick,
                microseconds_per_quarter_note=tempo,
                elapsed_microseconds=elapsed,
                source_events=sources,
                is_implicit_default=implicit,
            )
        )
        previous_tick = tick
        previous_tempo = tempo
    return MaestroTempoMap(
        ticks_per_quarter_note=midi.ticks_per_quarter_note,
        points=tuple(points),
    )


def _stable_note_id_from_indices(
    source_sha256: str,
    track_index: int,
    event_index: int,
) -> str:
    payload = (
        _NOTE_ID_DOMAIN
        + bytes.fromhex(source_sha256)
        + track_index.to_bytes(4, "big", signed=False)
        + event_index.to_bytes(8, "big", signed=False)
    )
    return hashlib.sha256(payload).hexdigest()


def _stable_note_id(source_sha256: str, event: MidiChannelEvent) -> str:
    return _stable_note_id_from_indices(
        source_sha256,
        event.track_index,
        event.event_index,
    )


def build_maestro_semantics(
    midi: MidiFile,
    *,
    source_split: str,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
) -> MaestroSemanticPiece:
    """Convert one verified SMF into the frozen lossless onset semantics.

    Pairing queues are global to the declared identity ``(port, channel,
    pitch)``; track is provenance, not part of note identity.  All close events
    in one absolute-tick slice are processed before any opens in that slice.
    No orphan, dangling, nonpositive-duration, support, stream, or collision
    condition is repaired.  The latter three are retained as diagnostics
    because this function deliberately stops before tensor projection.  A
    syntactically valid file with no positive onset is retained as an empty
    semantic fact; Section 7's later window adapter must reject it rather than
    fabricating a frame or event.
    """

    if not isinstance(midi, MidiFile):
        raise TypeError("midi must be a MidiFile")
    split = _source_split(source_split)
    if not isinstance(limits, MaestroSemanticLimits):
        raise TypeError("limits must be a MaestroSemanticLimits instance")
    if midi.format_type not in (0, 1):
        raise MaestroSemanticError(
            "semantic adapter admits only SMF format 0 or 1",
            code="FORMAT_NOT_0_OR_1",
        )
    if midi.ticks_per_quarter_note % 4:
        raise MaestroSemanticError(
            "PPQN must be exactly divisible by four",
            code="PPQN_NOT_DIVISIBLE_BY_FOUR",
        )
    if midi.track_count > limits.maximum_tracks:
        raise MaestroSemanticError(
            "track count exceeds maximum_tracks", code="LIMIT_MAXIMUM_TRACKS"
        )
    if midi.total_events > limits.maximum_total_events:
        raise MaestroSemanticError(
            "event count exceeds maximum_total_events",
            code="LIMIT_MAXIMUM_TOTAL_EVENTS",
        )

    note_events: List[_AnnotatedNoteEvent] = []
    controller_events: List[_AnnotatedController] = []
    tempo_events: List[MidiMetaEvent] = []
    port_events: List[MidiMetaEvent] = []
    signature_events: List[MidiMetaEvent] = []

    for track in midi.tracks:
        current_port = 0
        for event in track.events:
            if isinstance(event, MidiMetaEvent):
                if event.meta_type == 0x21:
                    if len(port_events) >= limits.maximum_midi_port_events:
                        raise MaestroSemanticError(
                            "MIDI Port events exceed maximum_midi_port_events",
                            code="LIMIT_MIDI_PORT_EVENTS",
                        )
                    current_port = event.payload[0]
                    port_events.append(event)
                elif event.meta_type == 0x51:
                    if len(tempo_events) >= limits.maximum_tempo_events:
                        raise MaestroSemanticError(
                            "tempo events exceed maximum_tempo_events",
                            code="LIMIT_TEMPO_EVENTS",
                        )
                    tempo_events.append(event)
                elif event.meta_type == 0x58:
                    if len(signature_events) >= limits.maximum_time_signatures:
                        raise MaestroSemanticError(
                            "time signatures exceed maximum_time_signatures",
                            code="LIMIT_TIME_SIGNATURES",
                        )
                    signature_events.append(event)
                continue
            if not isinstance(event, MidiChannelEvent):
                continue
            if event.message_type in ("note_on", "note_off"):
                if len(note_events) >= limits.maximum_note_events:
                    raise MaestroSemanticError(
                        "note events exceed maximum_note_events",
                        code="LIMIT_NOTE_EVENTS",
                    )
                velocity = event.velocity
                if velocity is None:
                    raise AssertionError("note event lacks a velocity")
                is_open = event.message_type == "note_on" and velocity > 0
                closure = None
                if event.message_type == "note_off":
                    closure = "note_off"
                elif velocity == 0:
                    closure = "note_on_velocity_zero"
                note_events.append(
                    _AnnotatedNoteEvent(
                        event=event,
                        port=current_port,
                        is_open=is_open,
                        closure_spelling=closure,
                    )
                )
            elif event.message_type == "control_change":
                if len(controller_events) >= limits.maximum_control_changes:
                    raise MaestroSemanticError(
                        "control changes exceed maximum_control_changes",
                        code="LIMIT_CONTROL_CHANGES",
                    )
                controller_events.append(
                    _AnnotatedController(event=event, port=current_port)
                )

    opening_count = sum(item.is_open for item in note_events)
    if opening_count > limits.maximum_note_onsets:
        raise MaestroSemanticError(
            "positive note onsets exceed maximum_note_onsets",
            code="LIMIT_NOTE_ONSETS",
        )

    tempo_map = _build_tempo_map(
        midi,
        tuple(tempo_events),
        limits=limits,
    )

    sorted_notes = sorted(
        note_events,
        key=lambda item: (
            item.event.absolute_ticks,
            item.event.track_index,
            item.event.event_index,
        ),
    )
    open_queues: Dict[Tuple[int, int, int], Deque[_AnnotatedNoteEvent]] = {}
    open_count = 0
    pairs: List[Tuple[_AnnotatedNoteEvent, _AnnotatedNoteEvent]] = []
    cursor = 0
    while cursor < len(sorted_notes):
        tick = sorted_notes[cursor].event.absolute_ticks
        end = cursor + 1
        while end < len(sorted_notes) and sorted_notes[end].event.absolute_ticks == tick:
            end += 1
        atomic = sorted_notes[cursor:end]
        if len(atomic) > limits.maximum_atomic_note_events:
            raise MaestroSemanticError(
                "same-tick note events exceed maximum_atomic_note_events",
                code="LIMIT_ATOMIC_NOTE_EVENTS",
            )
        closes = [item for item in atomic if not item.is_open]
        opens = [item for item in atomic if item.is_open]
        for close in closes:
            queue = open_queues.get(close.identity)
            if not queue:
                raise MaestroSemanticError(
                    "orphan note closure at tick {} for identity {}".format(
                        tick, close.identity
                    ),
                    code="ORPHAN_NOTE_CLOSURE",
                )
            opening = queue.popleft()
            open_count -= 1
            if not queue:
                del open_queues[close.identity]
            if tick <= opening.event.absolute_ticks:
                raise MaestroSemanticError(
                    "paired note duration must be positive",
                    code="NONPOSITIVE_NOTE_DURATION",
                )
            pairs.append((opening, close))
        for opening in opens:
            queue = open_queues.setdefault(opening.identity, deque())
            queue.append(opening)
            open_count += 1
            if open_count > limits.maximum_open_notes:
                raise MaestroSemanticError(
                    "simultaneously open notes exceed maximum_open_notes",
                    code="LIMIT_OPEN_NOTES",
                )
        cursor = end

    if open_queues:
        dangling_count = sum(len(queue) for queue in open_queues.values())
        raise MaestroSemanticError(
            "{} positive note onset(s) remain dangling at end of file".format(
                dangling_count
            ),
            code="DANGLING_NOTE_ONSETS",
        )
    if len(pairs) != opening_count:
        raise AssertionError("paired-note count does not equal opening count")

    grid_spacing = midi.ticks_per_quarter_note // 4
    rows: List[MaestroNoteOnset] = []
    for opening, close in pairs:
        event = opening.event
        closure_event = close.event
        onset_tick = event.absolute_ticks
        release_tick = closure_event.absolute_ticks
        grid_index = (2 * onset_tick + grid_spacing - 1) // (2 * grid_spacing)
        offset = Fraction(
            2 * (onset_tick - grid_index * grid_spacing),
            grid_spacing,
        )
        onset_time = tempo_map.time_microseconds_at(onset_tick)
        release_time = tempo_map.time_microseconds_at(release_tick)
        onset_velocity = event.velocity
        release_velocity = closure_event.velocity
        pitch = event.note
        if onset_velocity is None or release_velocity is None or pitch is None:
            raise AssertionError("paired channel event is missing note fields")
        rows.append(
            MaestroNoteOnset(
                note_id=_stable_note_id(midi.sha256, event),
                source_split=split,
                source_midi_sha256=midi.sha256,
                port=opening.port,
                channel=event.channel,
                pitch=pitch,
                onset_tick=onset_tick,
                release_tick=release_tick,
                onset_velocity=onset_velocity,
                release_velocity=release_velocity,
                onset_spelling="note_on_positive_velocity",
                closure_spelling=close.closure_spelling or "",
                onset_provenance=ChannelEventProvenance.from_event(event),
                closure_provenance=ChannelEventProvenance.from_event(closure_event),
                onset_time_microseconds=onset_time,
                release_time_microseconds=release_time,
                onset_time_seconds=float(onset_time / 1_000_000),
                release_time_seconds=float(release_time / 1_000_000),
                grid_index=grid_index,
                velocity_normalized_exact=Fraction(onset_velocity, 127),
                velocity_normalized=float(Fraction(onset_velocity, 127)),
                midi_clock_onset_offset_exact=offset,
                midi_clock_onset_offset=float(offset),
            )
        )
    rows.sort(
        key=lambda note: (
            note.onset_tick,
            note.onset_provenance.track_index,
            note.onset_provenance.event_index,
        )
    )

    controllers: List[ControllerFact] = []
    for annotated in sorted(
        controller_events,
        key=lambda item: (
            item.event.absolute_ticks,
            item.event.track_index,
            item.event.event_index,
        ),
    ):
        event = annotated.event
        controller = event.controller
        value = event.controller_value
        if controller is None or value is None:
            raise AssertionError("control-change event lacks controller fields")
        exact_time = tempo_map.time_microseconds_at(event.absolute_ticks)
        controllers.append(
            ControllerFact(
                port=annotated.port,
                channel=event.channel,
                controller=controller,
                value=value,
                time_microseconds=exact_time,
                time_seconds=float(exact_time / 1_000_000),
                provenance=ChannelEventProvenance.from_event(event),
            )
        )

    midi_ports: List[MidiPortFact] = []
    for event in sorted(
        port_events,
        key=lambda item: (item.absolute_ticks, item.track_index, item.event_index),
    ):
        exact_time = tempo_map.time_microseconds_at(event.absolute_ticks)
        midi_ports.append(
            MidiPortFact(
                port=event.payload[0],
                time_microseconds=exact_time,
                time_seconds=float(exact_time / 1_000_000),
                provenance=MetaEventProvenance.from_event(event),
            )
        )

    time_signatures: List[TimeSignatureFact] = []
    for event in sorted(
        signature_events,
        key=lambda item: (item.absolute_ticks, item.track_index, item.event_index),
    ):
        exact_time = tempo_map.time_microseconds_at(event.absolute_ticks)
        time_signatures.append(
            TimeSignatureFact(
                fields=tuple(event.payload),  # type: ignore[arg-type]
                time_microseconds=exact_time,
                time_seconds=float(exact_time / 1_000_000),
                provenance=MetaEventProvenance.from_event(event),
            )
        )

    pitches = [note.pitch for note in rows]
    streams = tuple(sorted({(note.port, note.channel) for note in rows}))
    collision_members: Dict[Tuple[int, int], List[str]] = {}
    for note in rows:
        collision_members.setdefault((note.grid_index, note.pitch), []).append(
            note.note_id
        )
    collisions = tuple(
        ProjectionCollision(
            grid_index=key[0],
            pitch=key[1],
            note_ids=tuple(sorted(note_ids)),
        )
        for key, note_ids in sorted(collision_members.items())
        if len(note_ids) > 1
    )
    diagnostics = MaestroSemanticDiagnostics(
        pitch_minimum=min(pitches) if pitches else None,
        pitch_maximum=max(pitches) if pitches else None,
        out_of_88_key_note_count=sum(not 21 <= pitch <= 108 for pitch in pitches),
        note_producing_streams=streams,
        projection_collisions=collisions,
    )
    return MaestroSemanticPiece(
        source_split=split,
        source_midi_sha256=midi.sha256,
        format_type=midi.format_type,
        ticks_per_quarter_note=midi.ticks_per_quarter_note,
        grid_spacing_ticks=grid_spacing,
        tempo_map=tempo_map,
        notes=tuple(rows),
        controllers=tuple(controllers),
        midi_ports=tuple(midi_ports),
        time_signatures=tuple(time_signatures),
        diagnostics=diagnostics,
    )


def build_maestro_semantics_for_inventory_record(
    midi: MidiFile,
    record: MaestroMidiInventory,
    *,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
) -> MaestroSemanticPiece:
    """Build semantics with source identity inherited from one inventory row.

    The lower-level :func:`build_maestro_semantics` accepts an explicit split
    so generated fixtures can exercise every admitted label.  Official corpus
    code must use this joined entry point: it rejects a byte-length or digest
    mismatch and obtains the split from the immutable inventory record rather
    than from a caller-supplied label.
    """

    if not isinstance(midi, MidiFile):
        raise TypeError("midi must be a MidiFile")
    if not isinstance(record, MaestroMidiInventory):
        raise TypeError("record must be a MaestroMidiInventory")
    if midi.sha256 != record.sha256:
        raise MaestroSemanticError(
            "MIDI digest does not match inventory record",
            code="INVENTORY_DIGEST_MISMATCH",
        )
    if midi.byte_length != record.size_bytes:
        raise MaestroSemanticError(
            "MIDI byte length does not match inventory record",
            code="INVENTORY_SIZE_MISMATCH",
        )
    return build_maestro_semantics(
        midi,
        source_split=record.source_split,
        limits=limits,
    )
