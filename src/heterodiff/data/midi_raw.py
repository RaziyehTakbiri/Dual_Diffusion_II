"""Strict, bounded, lossless Standard MIDI File ingestion.

This module parses the binary container and event grammar of Standard MIDI
Files (SMF) without turning events into notes, seconds, score positions, or a
model grid.  In particular, note-on events with velocity zero remain note-on
events, sustain-pedal controller values remain ordinary controller data, and
tempo events are retained in their original tracks and order.

The admitted boundary is deliberately narrow:

* header lengths and track counts must be exact;
* only PPQ time division is accepted (SMPTE division is rejected);
* every variable-length quantity is canonical and at most four bytes;
* running status is confined to channel events and is cancelled by SysEx and
  meta events, as required by the SMF grammar;
* every track ends with exactly one zero-length end-of-track event and has no
  bytes after it; and
* explicit resource limits are checked before large payloads or event streams
  are admitted.

This is a strict container and wire-grammar boundary, not a validator for the
musical domain of every defined meta-event field.  For example, key-signature
payload bytes are retained exactly but not interpreted here.  Python event
objects also occupy substantially more memory than their encoded bytes;
corpus callers must process files sequentially and release each parse.

Each event retains its exact encoded bytes (including delta-time and whether a
channel status byte was omitted), and file/track SHA-256 digests provide stable
byte-level audit identities.  Text and manufacturer-specific payloads stay as
bytes; no character encoding or device semantics are guessed.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union


_HEADER_CHUNK_ID = b"MThd"
_TRACK_CHUNK_ID = b"MTrk"
_HEADER_LENGTH = 6
_MAX_VLQ_VALUE = 0x0FFFFFFF

_CHANNEL_MESSAGE_NAMES = {
    0x80: "note_off",
    0x90: "note_on",
    0xA0: "polyphonic_key_pressure",
    0xB0: "control_change",
    0xC0: "program_change",
    0xD0: "channel_pressure",
    0xE0: "pitch_bend",
}
_CHANNEL_DATA_LENGTHS = {
    0x80: 2,
    0x90: 2,
    0xA0: 2,
    0xB0: 2,
    0xC0: 1,
    0xD0: 1,
    0xE0: 2,
}
_META_EVENT_NAMES = {
    0x00: "sequence_number",
    0x01: "text",
    0x02: "copyright",
    0x03: "track_name",
    0x04: "instrument_name",
    0x05: "lyric",
    0x06: "marker",
    0x07: "cue_point",
    0x08: "program_name",
    0x09: "device_name",
    0x20: "channel_prefix",
    0x21: "midi_port",
    0x2F: "end_of_track",
    0x51: "set_tempo",
    0x54: "smpte_offset",
    0x58: "time_signature",
    0x59: "key_signature",
    0x7F: "sequencer_specific",
}
_FIXED_META_LENGTHS = {
    0x00: 2,
    0x20: 1,
    0x21: 1,
    0x2F: 0,
    0x51: 3,
    0x54: 5,
    0x58: 4,
    0x59: 2,
}


class MidiFormatError(ValueError):
    """Raised when bytes violate the admitted Standard MIDI File contract."""


def _require_plain_int(value: object, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{} must be an integer".format(name))
    if value < minimum:
        qualifier = "positive" if minimum == 1 else "at least {}".format(minimum)
        raise ValueError("{} must be {}".format(name, qualifier))
    return value


def _validate_sha256(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(name))
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("{} must be a lowercase SHA-256 hex digest".format(name))
    return value


def _encode_vlq(value: int) -> bytes:
    if not 0 <= value <= _MAX_VLQ_VALUE:
        raise ValueError("VLQ value must be in 0..0x0fffffff")
    parts = [value & 0x7F]
    value >>= 7
    while value:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(parts))


@dataclass(frozen=True)
class MidiParseLimits:
    """Explicit resource ceiling for one parsed SMF object.

    The defaults admit the verified MAESTRO v3 maxima with margin but remain
    bounded well below arbitrary container sizes.  They bound encoded bytes
    and event count, not exact Python heap usage.  Callers may make a gate
    tighter; widening it is an explicit, inspectable decision.
    """

    # These defaults deliberately target sequential parsing of performance
    # MIDI, not arbitrary multimedia containers.  The verified MAESTRO v3
    # maximum is below 0.5 MiB; the byte limits retain substantial margin
    # while constraining payload copies and exact-byte reconstruction.
    maximum_file_bytes: int = 8 * 1024 * 1024
    maximum_tracks: int = 256
    maximum_track_bytes: int = 8 * 1024 * 1024
    maximum_event_payload_bytes: int = 4 * 1024 * 1024
    # The verified MAESTRO v3.0.0 release contains accepted tracks above
    # 123,000 events.  This ceiling admits that frozen corpus with margin
    # while remaining at the independent whole-file event ceiling.
    maximum_events_per_track: int = 150_000
    maximum_total_events: int = 150_000
    maximum_absolute_tick: int = 0x7FFFFFFF
    maximum_ticks_per_quarter_note: int = 0x7FFF

    def __post_init__(self) -> None:
        names = (
            "maximum_file_bytes",
            "maximum_tracks",
            "maximum_track_bytes",
            "maximum_event_payload_bytes",
            "maximum_events_per_track",
            "maximum_total_events",
            "maximum_absolute_tick",
            "maximum_ticks_per_quarter_note",
        )
        for name in names:
            _require_plain_int(getattr(self, name), name=name, minimum=1)
        if self.maximum_track_bytes > self.maximum_file_bytes:
            raise ValueError("maximum_track_bytes cannot exceed maximum_file_bytes")
        if self.maximum_event_payload_bytes > self.maximum_track_bytes:
            raise ValueError(
                "maximum_event_payload_bytes cannot exceed maximum_track_bytes"
            )
        if self.maximum_events_per_track > self.maximum_total_events:
            raise ValueError(
                "maximum_events_per_track cannot exceed maximum_total_events"
            )
        if self.maximum_absolute_tick > 0x7FFFFFFFFFFFFFFF:
            raise ValueError("maximum_absolute_tick exceeds signed 64-bit range")
        if self.maximum_ticks_per_quarter_note > 0x7FFF:
            raise ValueError(
                "maximum_ticks_per_quarter_note exceeds the PPQ field range"
            )


DEFAULT_MIDI_PARSE_LIMITS = MidiParseLimits()


def _validate_common_event(
    *,
    track_index: object,
    event_index: object,
    delta_ticks: object,
    absolute_ticks: object,
    track_byte_offset: object,
    encoded_bytes: object,
) -> None:
    _require_plain_int(track_index, name="track_index", minimum=0)
    _require_plain_int(event_index, name="event_index", minimum=0)
    _require_plain_int(delta_ticks, name="delta_ticks", minimum=0)
    _require_plain_int(absolute_ticks, name="absolute_ticks", minimum=0)
    _require_plain_int(track_byte_offset, name="track_byte_offset", minimum=0)
    if absolute_ticks < delta_ticks:
        raise ValueError("absolute_ticks cannot be smaller than delta_ticks")
    if delta_ticks > _MAX_VLQ_VALUE:
        raise ValueError("delta_ticks exceeds the four-byte VLQ range")
    if not isinstance(encoded_bytes, bytes):
        raise TypeError("encoded_bytes must be bytes")
    if not encoded_bytes:
        raise ValueError("encoded_bytes must not be empty")


@dataclass(frozen=True)
class MidiChannelEvent:
    """One MIDI channel event, with running-status encoding preserved."""

    track_index: int
    event_index: int
    delta_ticks: int
    absolute_ticks: int
    track_byte_offset: int
    encoded_bytes: bytes
    status: int
    used_running_status: bool
    message_type: str
    channel: int
    data: bytes

    def __post_init__(self) -> None:
        _validate_common_event(
            track_index=self.track_index,
            event_index=self.event_index,
            delta_ticks=self.delta_ticks,
            absolute_ticks=self.absolute_ticks,
            track_byte_offset=self.track_byte_offset,
            encoded_bytes=self.encoded_bytes,
        )
        if isinstance(self.status, bool) or not isinstance(self.status, int):
            raise TypeError("status must be an integer")
        if not 0x80 <= self.status <= 0xEF:
            raise ValueError("channel-event status must be in 0x80..0xEF")
        if not isinstance(self.used_running_status, bool):
            raise TypeError("used_running_status must be a boolean")
        command = self.status & 0xF0
        expected_name = _CHANNEL_MESSAGE_NAMES[command]
        if self.message_type != expected_name:
            raise ValueError("message_type does not match status")
        if isinstance(self.channel, bool) or not isinstance(self.channel, int):
            raise TypeError("channel must be an integer")
        if self.channel != (self.status & 0x0F):
            raise ValueError("channel does not match status")
        if not isinstance(self.data, bytes):
            raise TypeError("data must be bytes")
        if len(self.data) != _CHANNEL_DATA_LENGTHS[command]:
            raise ValueError("channel-event data length does not match status")
        if any(value >= 0x80 for value in self.data):
            raise ValueError("channel-event data bytes must be below 0x80")
        expected_encoding = _encode_vlq(self.delta_ticks)
        if not self.used_running_status:
            expected_encoding += bytes((self.status,))
        expected_encoding += self.data
        if self.encoded_bytes != expected_encoding:
            raise ValueError("encoded_bytes do not match the channel-event fields")

    @property
    def note(self) -> Optional[int]:
        """Return the protocol note number for note/key-pressure messages."""

        if (self.status & 0xF0) in (0x80, 0x90, 0xA0):
            return self.data[0]
        return None

    @property
    def velocity(self) -> Optional[int]:
        """Return the raw velocity for note-on/off, without reinterpretation."""

        if (self.status & 0xF0) in (0x80, 0x90):
            return self.data[1]
        return None

    @property
    def controller(self) -> Optional[int]:
        if (self.status & 0xF0) == 0xB0:
            return self.data[0]
        return None

    @property
    def controller_value(self) -> Optional[int]:
        if (self.status & 0xF0) == 0xB0:
            return self.data[1]
        return None

    @property
    def pitch_bend_value(self) -> Optional[int]:
        """Return the unsigned 14-bit wire value; no cent mapping is imposed."""

        if (self.status & 0xF0) == 0xE0:
            return self.data[0] | (self.data[1] << 7)
        return None


@dataclass(frozen=True)
class MidiMetaEvent:
    """One SMF meta event with uninterpreted payload bytes retained."""

    track_index: int
    event_index: int
    delta_ticks: int
    absolute_ticks: int
    track_byte_offset: int
    encoded_bytes: bytes
    meta_type: int
    meta_name: str
    payload: bytes

    def __post_init__(self) -> None:
        _validate_common_event(
            track_index=self.track_index,
            event_index=self.event_index,
            delta_ticks=self.delta_ticks,
            absolute_ticks=self.absolute_ticks,
            track_byte_offset=self.track_byte_offset,
            encoded_bytes=self.encoded_bytes,
        )
        if isinstance(self.meta_type, bool) or not isinstance(self.meta_type, int):
            raise TypeError("meta_type must be an integer")
        if not 0 <= self.meta_type <= 0x7F:
            raise ValueError("meta_type must be a data byte in 0x00..0x7F")
        expected_name = _META_EVENT_NAMES.get(self.meta_type, "unknown_meta")
        if self.meta_name != expected_name:
            raise ValueError("meta_name does not match meta_type")
        if not isinstance(self.payload, bytes):
            raise TypeError("payload must be bytes")
        expected_length = _FIXED_META_LENGTHS.get(self.meta_type)
        if expected_length is not None and len(self.payload) != expected_length:
            raise ValueError("fixed-length meta payload has the wrong length")
        expected_encoding = (
            _encode_vlq(self.delta_ticks)
            + b"\xff"
            + bytes((self.meta_type,))
            + _encode_vlq(len(self.payload))
            + self.payload
        )
        if self.encoded_bytes != expected_encoding:
            raise ValueError("encoded_bytes do not match the meta-event fields")

    @property
    def microseconds_per_quarter_note(self) -> Optional[int]:
        if self.meta_type == 0x51:
            return int.from_bytes(self.payload, byteorder="big", signed=False)
        return None

    @property
    def time_signature_fields(self) -> Optional[Tuple[int, int, int, int]]:
        """Return ``(numerator, denominator_power, clocks, 32nds)`` verbatim."""

        if self.meta_type == 0x58:
            return tuple(self.payload)  # type: ignore[return-value]
        return None

    @property
    def is_end_of_track(self) -> bool:
        return self.meta_type == 0x2F


@dataclass(frozen=True)
class MidiSysExEvent:
    """One F0 or F7 SMF event; packet joining is deliberately not attempted."""

    track_index: int
    event_index: int
    delta_ticks: int
    absolute_ticks: int
    track_byte_offset: int
    encoded_bytes: bytes
    status: int
    payload: bytes

    def __post_init__(self) -> None:
        _validate_common_event(
            track_index=self.track_index,
            event_index=self.event_index,
            delta_ticks=self.delta_ticks,
            absolute_ticks=self.absolute_ticks,
            track_byte_offset=self.track_byte_offset,
            encoded_bytes=self.encoded_bytes,
        )
        if self.status not in (0xF0, 0xF7):
            raise ValueError("SysEx status must be 0xF0 or 0xF7")
        if not isinstance(self.payload, bytes):
            raise TypeError("payload must be bytes")
        expected_encoding = (
            _encode_vlq(self.delta_ticks)
            + bytes((self.status,))
            + _encode_vlq(len(self.payload))
            + self.payload
        )
        if self.encoded_bytes != expected_encoding:
            raise ValueError("encoded_bytes do not match the SysEx-event fields")

    @property
    def event_type(self) -> str:
        if self.status == 0xF0:
            return "sysex_start"
        return "sysex_escape_or_continuation"


MidiEvent = Union[MidiChannelEvent, MidiMetaEvent, MidiSysExEvent]


@dataclass(frozen=True)
class MidiTrack:
    """One track chunk in source order."""

    index: int
    byte_length: int
    sha256: str
    events: Tuple[MidiEvent, ...]

    def __post_init__(self) -> None:
        _require_plain_int(self.index, name="index", minimum=0)
        _require_plain_int(self.byte_length, name="byte_length", minimum=1)
        if self.byte_length > 0xFFFFFFFF:
            raise ValueError("byte_length exceeds the MTrk length field range")
        _validate_sha256(self.sha256, name="sha256")
        if not isinstance(self.events, tuple):
            raise TypeError("events must be a tuple")
        if not self.events:
            raise ValueError("a MIDI track must contain end-of-track")
        if any(
            not isinstance(event, (MidiChannelEvent, MidiMetaEvent, MidiSysExEvent))
            for event in self.events
        ):
            raise TypeError("events must contain MIDI event values")
        expected_offset = 0
        expected_tick = 0
        running_status = None  # type: Optional[int]
        for event_index, event in enumerate(self.events):
            if event.track_index != self.index or event.event_index != event_index:
                raise ValueError("event track/event index is inconsistent")
            if event.track_byte_offset != expected_offset:
                raise ValueError("event byte offsets do not exactly cover the track")
            expected_offset += len(event.encoded_bytes)
            expected_tick += event.delta_ticks
            if event.absolute_ticks != expected_tick:
                raise ValueError("event absolute tick does not match accumulated deltas")
            if isinstance(event, MidiChannelEvent):
                if event.used_running_status:
                    if running_status != event.status:
                        raise ValueError(
                            "running-status event does not match preceding channel status"
                        )
                else:
                    running_status = event.status
            else:
                running_status = None
                if (
                    isinstance(event, MidiMetaEvent)
                    and event.is_end_of_track
                    and event_index != len(self.events) - 1
                ):
                    raise ValueError("end-of-track must be the final track event")
        final_event = self.events[-1]
        if not isinstance(final_event, MidiMetaEvent) or not final_event.is_end_of_track:
            raise ValueError("final track event must be end-of-track")
        if expected_offset != self.byte_length:
            raise ValueError("event bytes do not exactly cover the track payload")
        encoded_track = b"".join(event.encoded_bytes for event in self.events)
        if hashlib.sha256(encoded_track).hexdigest() != self.sha256:
            raise ValueError("sha256 does not match the exact track payload bytes")

    @property
    def end_tick(self) -> int:
        return self.events[-1].absolute_ticks


@dataclass(frozen=True)
class MidiFile:
    """An immutable, byte-audited Standard MIDI File parse result."""

    format_type: int
    ticks_per_quarter_note: int
    tracks: Tuple[MidiTrack, ...]
    byte_length: int
    sha256: str

    def __post_init__(self) -> None:
        if isinstance(self.format_type, bool) or not isinstance(self.format_type, int):
            raise TypeError("format_type must be an integer")
        if self.format_type not in (0, 1, 2):
            raise ValueError("format_type must be 0, 1, or 2")
        _require_plain_int(
            self.ticks_per_quarter_note,
            name="ticks_per_quarter_note",
            minimum=1,
        )
        if self.ticks_per_quarter_note > 0x7FFF:
            raise ValueError("ticks_per_quarter_note exceeds the PPQ field range")
        if not isinstance(self.tracks, tuple):
            raise TypeError("tracks must be a tuple")
        if not self.tracks:
            raise ValueError("tracks must not be empty")
        if any(not isinstance(track, MidiTrack) for track in self.tracks):
            raise TypeError("tracks must contain MidiTrack values")
        if len(self.tracks) > 0xFFFF:
            raise ValueError("track count exceeds the MThd field range")
        if self.format_type == 0 and len(self.tracks) != 1:
            raise ValueError("format 0 must contain exactly one track")
        for track_index, track in enumerate(self.tracks):
            if track.index != track_index:
                raise ValueError("track indices must be contiguous and ordered")
        _require_plain_int(self.byte_length, name="byte_length", minimum=1)
        _validate_sha256(self.sha256, name="sha256")
        file_chunks = [
            _HEADER_CHUNK_ID
            + _HEADER_LENGTH.to_bytes(4, byteorder="big", signed=False)
            + self.format_type.to_bytes(2, byteorder="big", signed=False)
            + len(self.tracks).to_bytes(2, byteorder="big", signed=False)
            + self.ticks_per_quarter_note.to_bytes(2, byteorder="big", signed=False)
        ]
        for track in self.tracks:
            payload = b"".join(event.encoded_bytes for event in track.events)
            file_chunks.append(
                _TRACK_CHUNK_ID
                + track.byte_length.to_bytes(4, byteorder="big", signed=False)
                + payload
            )
        encoded_file = b"".join(file_chunks)
        if len(encoded_file) != self.byte_length:
            raise ValueError("byte_length does not match the reconstructed SMF bytes")
        if hashlib.sha256(encoded_file).hexdigest() != self.sha256:
            raise ValueError("sha256 does not match the reconstructed SMF bytes")

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def total_events(self) -> int:
        return sum(len(track.events) for track in self.tracks)


def _read_u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], byteorder="big", signed=False)


def _read_u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], byteorder="big", signed=False)


def _file_stat_signature(status: os.stat_result) -> Tuple[int, ...]:
    """Fields used to detect ordinary replacement or mutation during a read."""

    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _read_vlq(data: bytes, offset: int, *, context: str) -> Tuple[int, int]:
    start = offset
    value = 0
    for index in range(4):
        if offset >= len(data):
            raise MidiFormatError("truncated {} variable-length quantity".format(context))
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if byte < 0x80:
            if offset - start > 1 and (data[start] & 0x7F) == 0:
                raise MidiFormatError(
                    "noncanonical {} variable-length quantity".format(context)
                )
            return value, offset
        if index == 3:
            raise MidiFormatError(
                "{} variable-length quantity exceeds four bytes".format(context)
            )
    raise AssertionError("unreachable VLQ parser state")


def _slice_payload(
    data: bytes,
    offset: int,
    length: int,
    *,
    limits: MidiParseLimits,
    context: str,
) -> Tuple[bytes, int]:
    if length > limits.maximum_event_payload_bytes:
        raise MidiFormatError(
            "{} payload length {} exceeds configured limit {}".format(
                context, length, limits.maximum_event_payload_bytes
            )
        )
    end = offset + length
    if end > len(data):
        raise MidiFormatError("truncated {} payload".format(context))
    return data[offset:end], end


def _parse_track(
    data: bytes,
    *,
    track_index: int,
    limits: MidiParseLimits,
    remaining_total_events: int,
) -> MidiTrack:
    events = []  # type: list[MidiEvent]
    offset = 0
    absolute_ticks = 0
    running_status = None  # type: Optional[int]

    while offset < len(data):
        event_index = len(events)
        if event_index >= limits.maximum_events_per_track:
            raise MidiFormatError(
                "track {} exceeds maximum_events_per_track {}".format(
                    track_index, limits.maximum_events_per_track
                )
            )
        if event_index >= remaining_total_events:
            raise MidiFormatError(
                "file exceeds maximum_total_events {}".format(
                    limits.maximum_total_events
                )
            )

        event_start = offset
        delta_ticks, offset = _read_vlq(data, offset, context="delta-time")
        if delta_ticks > _MAX_VLQ_VALUE:
            raise AssertionError("VLQ parser admitted an out-of-range value")
        if absolute_ticks > limits.maximum_absolute_tick - delta_ticks:
            raise MidiFormatError(
                "track {} absolute tick exceeds configured limit {}".format(
                    track_index, limits.maximum_absolute_tick
                )
            )
        absolute_ticks += delta_ticks

        if offset >= len(data):
            raise MidiFormatError("track event is missing a status or data byte")
        candidate = data[offset]

        if candidate < 0x80:
            if running_status is None:
                raise MidiFormatError("channel data encountered without running status")
            status = running_status
            used_running_status = True
        else:
            status = candidate
            used_running_status = False
            offset += 1

        if 0x80 <= status <= 0xEF:
            command = status & 0xF0
            running_status = status
            data_length = _CHANNEL_DATA_LENGTHS[command]
            data_end = offset + data_length
            if data_end > len(data):
                raise MidiFormatError("truncated MIDI channel event")
            event_data = data[offset:data_end]
            if any(value >= 0x80 for value in event_data):
                raise MidiFormatError("illegal status byte inside channel-event data")
            offset = data_end
            events.append(
                MidiChannelEvent(
                    track_index=track_index,
                    event_index=event_index,
                    delta_ticks=delta_ticks,
                    absolute_ticks=absolute_ticks,
                    track_byte_offset=event_start,
                    encoded_bytes=data[event_start:offset],
                    status=status,
                    used_running_status=used_running_status,
                    message_type=_CHANNEL_MESSAGE_NAMES[command],
                    channel=status & 0x0F,
                    data=event_data,
                )
            )
            continue

        if used_running_status:
            raise AssertionError("running status cannot resolve to a system event")
        running_status = None

        if status == 0xFF:
            if offset >= len(data):
                raise MidiFormatError("truncated meta event before type byte")
            meta_type = data[offset]
            offset += 1
            if meta_type >= 0x80:
                raise MidiFormatError("meta-event type must be below 0x80")
            payload_length, offset = _read_vlq(
                data, offset, context="meta-event length"
            )
            payload, offset = _slice_payload(
                data,
                offset,
                payload_length,
                limits=limits,
                context="meta-event",
            )
            expected_length = _FIXED_META_LENGTHS.get(meta_type)
            if expected_length is not None and payload_length != expected_length:
                raise MidiFormatError(
                    "meta event 0x{:02x} requires payload length {}, got {}".format(
                        meta_type, expected_length, payload_length
                    )
                )
            event = MidiMetaEvent(
                track_index=track_index,
                event_index=event_index,
                delta_ticks=delta_ticks,
                absolute_ticks=absolute_ticks,
                track_byte_offset=event_start,
                encoded_bytes=data[event_start:offset],
                meta_type=meta_type,
                meta_name=_META_EVENT_NAMES.get(meta_type, "unknown_meta"),
                payload=payload,
            )
            events.append(event)
            if event.is_end_of_track:
                if offset != len(data):
                    raise MidiFormatError("track contains bytes after end-of-track")
                break
            continue

        if status in (0xF0, 0xF7):
            payload_length, offset = _read_vlq(
                data, offset, context="SysEx-event length"
            )
            payload, offset = _slice_payload(
                data,
                offset,
                payload_length,
                limits=limits,
                context="SysEx-event",
            )
            events.append(
                MidiSysExEvent(
                    track_index=track_index,
                    event_index=event_index,
                    delta_ticks=delta_ticks,
                    absolute_ticks=absolute_ticks,
                    track_byte_offset=event_start,
                    encoded_bytes=data[event_start:offset],
                    status=status,
                    payload=payload,
                )
            )
            continue

        raise MidiFormatError(
            "status byte 0x{:02x} is illegal in a Standard MIDI File track".format(
                status
            )
        )

    if not events:
        raise MidiFormatError("track is empty and missing end-of-track")
    final_event = events[-1]
    if not isinstance(final_event, MidiMetaEvent) or not final_event.is_end_of_track:
        raise MidiFormatError("track is missing a final end-of-track event")
    return MidiTrack(
        index=track_index,
        byte_length=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        events=tuple(events),
    )


def parse_midi_bytes(
    data: bytes,
    *,
    limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
) -> MidiFile:
    """Parse one complete Standard MIDI File from immutable bytes.

    No trailing bytes, RIFF/RMID wrapper, unknown chunks, or SMPTE division are
    admitted by this first raw-data gate.
    """

    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if not isinstance(limits, MidiParseLimits):
        raise TypeError("limits must be a MidiParseLimits instance")
    if len(data) > limits.maximum_file_bytes:
        raise MidiFormatError(
            "file length {} exceeds configured limit {}".format(
                len(data), limits.maximum_file_bytes
            )
        )
    if len(data) < 14:
        raise MidiFormatError("truncated MIDI header chunk")
    if data[:4] != _HEADER_CHUNK_ID:
        raise MidiFormatError("file must begin with an MThd chunk")
    header_length = _read_u32(data, 4)
    if header_length != _HEADER_LENGTH:
        raise MidiFormatError(
            "MThd payload length must be exactly 6, got {}".format(header_length)
        )

    format_type = _read_u16(data, 8)
    declared_track_count = _read_u16(data, 10)
    division = _read_u16(data, 12)
    if format_type not in (0, 1, 2):
        raise MidiFormatError("unsupported SMF format {}".format(format_type))
    if declared_track_count == 0:
        raise MidiFormatError("SMF must declare at least one track")
    if format_type == 0 and declared_track_count != 1:
        raise MidiFormatError("SMF format 0 must declare exactly one track")
    if declared_track_count > limits.maximum_tracks:
        raise MidiFormatError(
            "declared track count {} exceeds configured limit {}".format(
                declared_track_count, limits.maximum_tracks
            )
        )
    if division & 0x8000:
        raise MidiFormatError("SMPTE time division is not admitted; PPQ is required")
    ticks_per_quarter_note = division
    if ticks_per_quarter_note == 0:
        raise MidiFormatError("PPQ time division must be positive")
    if ticks_per_quarter_note > limits.maximum_ticks_per_quarter_note:
        raise MidiFormatError(
            "PPQ {} exceeds configured limit {}".format(
                ticks_per_quarter_note, limits.maximum_ticks_per_quarter_note
            )
        )

    offset = 14
    tracks = []  # type: list[MidiTrack]
    total_events = 0
    for track_index in range(declared_track_count):
        if len(data) - offset < 8:
            raise MidiFormatError(
                "truncated track chunk header for track {}".format(track_index)
            )
        if data[offset : offset + 4] != _TRACK_CHUNK_ID:
            raise MidiFormatError(
                "expected MTrk chunk for track {}".format(track_index)
            )
        track_length = _read_u32(data, offset + 4)
        if track_length > limits.maximum_track_bytes:
            raise MidiFormatError(
                "track {} length {} exceeds configured limit {}".format(
                    track_index, track_length, limits.maximum_track_bytes
                )
            )
        payload_start = offset + 8
        payload_end = payload_start + track_length
        if payload_end > len(data):
            raise MidiFormatError(
                "truncated payload for track {}".format(track_index)
            )
        remaining = limits.maximum_total_events - total_events
        track = _parse_track(
            data[payload_start:payload_end],
            track_index=track_index,
            limits=limits,
            remaining_total_events=remaining,
        )
        tracks.append(track)
        total_events += len(track.events)
        offset = payload_end

    if offset != len(data):
        raise MidiFormatError("trailing bytes remain after declared track chunks")
    return MidiFile(
        format_type=format_type,
        ticks_per_quarter_note=ticks_per_quarter_note,
        tracks=tuple(tracks),
        byte_length=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def load_midi_file(
    path: Union[str, os.PathLike],
    *,
    limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
) -> MidiFile:
    """Read and parse one SMF path with a bounded read.

    Symlinks (including persistent symlinked ancestors) and non-regular files
    are rejected.  The descriptor identity is checked before and after the
    bounded read, and the path is checked again afterwards.  This protects a
    trusted, quiescent acquisition against ordinary replacement; it is not a
    proof against a malicious filesystem actor capable of transient directory
    swaps and metadata restoration.
    """

    if not isinstance(limits, MidiParseLimits):
        raise TypeError("limits must be a MidiParseLimits instance")
    if not isinstance(path, (str, os.PathLike)):
        raise TypeError("path must be a string or path-like object")
    midi_path = Path(path)
    absolute_path = Path(os.path.abspath(os.fspath(midi_path)))

    def reject_symlinked_ancestors() -> None:
        ancestors = tuple(absolute_path.parents)
        for ancestor in reversed(ancestors[:-1]):
            try:
                ancestor_status = ancestor.lstat()
            except OSError as exc:
                raise MidiFormatError(
                    "could not inspect MIDI path ancestor {!s}".format(ancestor)
                ) from exc
            if stat.S_ISLNK(ancestor_status.st_mode):
                raise MidiFormatError("MIDI path ancestors must not be symbolic links")
            if not stat.S_ISDIR(ancestor_status.st_mode):
                raise MidiFormatError("MIDI path ancestors must be directories")

    reject_symlinked_ancestors()
    try:
        metadata = absolute_path.lstat()
    except OSError as exc:
        raise MidiFormatError("could not inspect MIDI path {!s}".format(absolute_path)) from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise MidiFormatError("MIDI path must not be a symbolic link")
    if not stat.S_ISREG(metadata.st_mode):
        raise MidiFormatError("MIDI path must be a regular file")
    if metadata.st_size > limits.maximum_file_bytes:
        raise MidiFormatError(
            "file length {} exceeds configured limit {}".format(
                metadata.st_size, limits.maximum_file_bytes
            )
        )
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = None
    try:
        descriptor = os.open(absolute_path, flags)
        descriptor_before = os.fstat(descriptor)
        if not stat.S_ISREG(descriptor_before.st_mode):
            raise MidiFormatError("opened MIDI path must be a regular file")
        if _file_stat_signature(descriptor_before) != _file_stat_signature(metadata):
            raise MidiFormatError("MIDI file identity changed before the bounded read")
        chunks = []
        remaining = limits.maximum_file_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        descriptor_after = os.fstat(descriptor)
        if _file_stat_signature(descriptor_after) != _file_stat_signature(
            descriptor_before
        ):
            raise MidiFormatError("MIDI file changed during the bounded read")
    except MidiFormatError:
        raise
    except OSError as exc:
        raise MidiFormatError("could not read MIDI path {!s}".format(absolute_path)) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(data) > limits.maximum_file_bytes:
        raise MidiFormatError("MIDI file grew beyond the configured read limit")
    if len(data) != metadata.st_size:
        raise MidiFormatError("MIDI file size changed during the bounded read")
    reject_symlinked_ancestors()
    try:
        metadata_after = absolute_path.lstat()
    except OSError as exc:
        raise MidiFormatError(
            "could not re-inspect MIDI path {!s}".format(absolute_path)
        ) from exc
    if _file_stat_signature(metadata_after) != _file_stat_signature(metadata):
        raise MidiFormatError("MIDI file identity changed after the bounded read")
    return parse_midi_bytes(data, limits=limits)


__all__ = [
    "DEFAULT_MIDI_PARSE_LIMITS",
    "MidiChannelEvent",
    "MidiEvent",
    "MidiFile",
    "MidiFormatError",
    "MidiMetaEvent",
    "MidiParseLimits",
    "MidiSysExEvent",
    "MidiTrack",
    "load_midi_file",
    "parse_midi_bytes",
]
