"""Differential evidence for :mod:`heterodiff.data.midi_raw` using Mido.

The validator deliberately imports Mido only when a validation function is
called.  The production parser therefore remains dependency-free, and an
environment without Mido can still import all of :mod:`heterodiff`.

Agreement is checked on the exact bytes reconstructed by the immutable raw
parse result.  The comparison covers the SMF header, decoded track partition,
event count in each track, every delta and absolute tick, exact channel status
and data bytes, exact meta type byte and payload, and the SysEx payload that
Mido exposes.  Mido 1.3.3 discards whether an SMF SysEx event used status F0 or
F7 and strips an optional leading F0 and trailing F7 from its payload.  Those
status bytes are consequently reported as *not compared*; the remaining
payload is compared after reproducing Mido's documented decoder behavior.

This module is an evidence oracle, not a second ingestion path.  It must never
be used to repair, normalize, or silently accept a file rejected by the raw
parser.
"""

from __future__ import annotations

import importlib
import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple, Union

from heterodiff.data.midi_raw import (
    DEFAULT_MIDI_PARSE_LIMITS,
    MidiChannelEvent,
    MidiFile,
    MidiMetaEvent,
    MidiParseLimits,
    MidiSysExEvent,
    load_midi_file,
    parse_midi_bytes,
)


MIDO_ORACLE_VERSION = "1.3.3"

_MIDO_CHANNEL_NAMES = {
    0x80: "note_off",
    0x90: "note_on",
    0xA0: "polytouch",
    0xB0: "control_change",
    0xC0: "program_change",
    0xD0: "aftertouch",
    0xE0: "pitchwheel",
}


class MidoUnavailableError(ImportError):
    """Raised when the optional Mido oracle cannot be imported."""


class MidoVersionError(RuntimeError):
    """Raised when the installed oracle is not the pinned Mido release."""


class MidoDifferentialError(AssertionError):
    """Raised on the first decoded disagreement with the Mido oracle."""


@dataclass(frozen=True)
class MidoDifferentialReport:
    """Audit counts returned only after every available comparison passes."""

    source_sha256: str
    source_byte_length: int
    mido_version: str
    format_type: int
    ticks_per_quarter_note: int
    track_count: int
    track_event_counts: Tuple[int, ...]
    track_end_ticks: Tuple[int, ...]
    timing_events_compared: int
    channel_events_compared: int
    meta_events_compared: int
    sysex_payloads_compared: int
    sysex_status_fields_unavailable_from_mido: int

    @property
    def total_events_compared(self) -> int:
        return self.timing_events_compared


def _load_pinned_mido(expected_version: str) -> Tuple[Any, str]:
    if not isinstance(expected_version, str):
        raise TypeError("expected_version must be a string")
    if not expected_version:
        raise ValueError("expected_version must not be empty")
    try:
        mido = importlib.import_module("mido")
    except (ImportError, ModuleNotFoundError) as exc:
        raise MidoUnavailableError(
            "Mido {} is required only for this differential audit".format(
                expected_version
            )
        ) from exc
    version_info = getattr(mido, "version_info", None)
    if version_info is None:
        raise MidoVersionError("installed Mido does not expose version_info")
    actual_version = str(version_info)
    if actual_version != expected_version:
        raise MidoVersionError(
            "differential oracle requires Mido {}, found {}".format(
                expected_version, actual_version
            )
        )
    return mido, actual_version


def _reconstruct_exact_bytes(midi: MidiFile) -> bytes:
    header = (
        b"MThd"
        + (6).to_bytes(4, byteorder="big", signed=False)
        + midi.format_type.to_bytes(2, byteorder="big", signed=False)
        + midi.track_count.to_bytes(2, byteorder="big", signed=False)
        + midi.ticks_per_quarter_note.to_bytes(2, byteorder="big", signed=False)
    )
    chunks = [header]
    for track in midi.tracks:
        payload = b"".join(event.encoded_bytes for event in track.events)
        chunks.append(
            b"MTrk"
            + len(payload).to_bytes(4, byteorder="big", signed=False)
            + payload
        )
    reconstructed = b"".join(chunks)
    if len(reconstructed) != midi.byte_length:
        raise MidoDifferentialError(
            "raw parse result no longer reconstructs its declared byte length"
        )
    return reconstructed


def _fail(location: str, field: str, expected: object, actual: object) -> None:
    raise MidoDifferentialError(
        "{} {} mismatch: raw={!r}, Mido={!r}".format(
            location, field, expected, actual
        )
    )


def _read_oracle_vlq(data: bytes, offset: int, *, location: str) -> Tuple[int, int]:
    value = 0
    for _ in range(4):
        if offset >= len(data):
            raise MidoDifferentialError(
                "{}: Mido emitted a truncated variable-length quantity".format(
                    location
                )
            )
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if byte < 0x80:
            return value, offset
    raise MidoDifferentialError(
        "{}: Mido emitted a variable-length quantity longer than four bytes".format(
            location
        )
    )


def _mido_meta_wire_fields(message: Any, *, location: str) -> Tuple[int, bytes]:
    try:
        encoded = bytes(message.bytes())
    except Exception as exc:
        raise MidoDifferentialError(
            "{}: Mido could not re-encode its decoded meta event: {}: {}".format(
                location, type(exc).__name__, exc
            )
        ) from exc
    if len(encoded) < 3 or encoded[0] != 0xFF or encoded[1] >= 0x80:
        raise MidoDifferentialError(
            "{}: Mido emitted an invalid meta-event encoding {!r}".format(
                location, encoded
            )
        )
    payload_length, payload_start = _read_oracle_vlq(
        encoded, 2, location=location
    )
    payload = encoded[payload_start:]
    if len(payload) != payload_length:
        raise MidoDifferentialError(
            "{}: Mido meta length {} does not cover {} payload bytes".format(
                location, payload_length, len(payload)
            )
        )
    return encoded[1], payload


def _mido_channel_bytes(message: Any, *, location: str) -> bytes:
    try:
        encoded = bytes(message.bytes())
    except Exception as exc:
        raise MidoDifferentialError(
            "{}: Mido could not re-encode its decoded channel event: {}: {}".format(
                location, type(exc).__name__, exc
            )
        ) from exc
    if not encoded or not 0x80 <= encoded[0] <= 0xEF:
        raise MidoDifferentialError(
            "{}: Mido emitted an invalid channel-event encoding {!r}".format(
                location, encoded
            )
        )
    return encoded


def _normalized_sysex_payload_for_mido(event: MidiSysExEvent) -> bytes:
    payload = event.payload
    if payload.startswith(b"\xf0"):
        payload = payload[1:]
    if payload.endswith(b"\xf7"):
        payload = payload[:-1]
    return payload


def _compare_parsed_to_oracle(
    raw: MidiFile,
    oracle: Any,
    *,
    mido_version: str,
) -> MidoDifferentialReport:
    if raw.format_type != getattr(oracle, "type", None):
        _fail("header", "format type", raw.format_type, getattr(oracle, "type", None))
    if raw.ticks_per_quarter_note != getattr(oracle, "ticks_per_beat", None):
        _fail(
            "header",
            "ticks per quarter note",
            raw.ticks_per_quarter_note,
            getattr(oracle, "ticks_per_beat", None),
        )
    oracle_tracks = tuple(getattr(oracle, "tracks", ()))
    if raw.track_count != len(oracle_tracks):
        _fail("header", "track count", raw.track_count, len(oracle_tracks))

    channel_count = 0
    meta_count = 0
    sysex_count = 0
    timing_count = 0
    event_counts = []
    end_ticks = []

    for track_index, (raw_track, oracle_track) in enumerate(
        zip(raw.tracks, oracle_tracks)
    ):
        oracle_events = tuple(oracle_track)
        location = "track {}".format(track_index)
        if len(raw_track.events) != len(oracle_events):
            _fail(
                location,
                "decoded event boundary/count",
                len(raw_track.events),
                len(oracle_events),
            )
        absolute_ticks = 0
        for event_index, (raw_event, oracle_event) in enumerate(
            zip(raw_track.events, oracle_events)
        ):
            event_location = "track {} event {}".format(track_index, event_index)
            oracle_delta = getattr(oracle_event, "time", None)
            if isinstance(oracle_delta, bool) or not isinstance(oracle_delta, int):
                raise MidoDifferentialError(
                    "{}: Mido delta tick is not an integer: {!r}".format(
                        event_location, oracle_delta
                    )
                )
            if raw_event.delta_ticks != oracle_delta:
                _fail(
                    event_location,
                    "delta tick",
                    raw_event.delta_ticks,
                    oracle_delta,
                )
            absolute_ticks += oracle_delta
            if raw_event.absolute_ticks != absolute_ticks:
                _fail(
                    event_location,
                    "absolute tick",
                    raw_event.absolute_ticks,
                    absolute_ticks,
                )
            timing_count += 1

            oracle_is_meta = bool(getattr(oracle_event, "is_meta", False))
            oracle_type = getattr(oracle_event, "type", None)
            if isinstance(raw_event, MidiChannelEvent):
                if oracle_is_meta or oracle_type == "sysex":
                    _fail(
                        event_location,
                        "event category",
                        "channel",
                        "meta" if oracle_is_meta else "sysex",
                    )
                expected_name = _MIDO_CHANNEL_NAMES[raw_event.status & 0xF0]
                if oracle_type != expected_name:
                    _fail(
                        event_location,
                        "channel message type",
                        expected_name,
                        oracle_type,
                    )
                raw_wire = bytes((raw_event.status,)) + raw_event.data
                oracle_wire = _mido_channel_bytes(
                    oracle_event, location=event_location
                )
                if raw_wire != oracle_wire:
                    _fail(
                        event_location,
                        "channel status/data bytes",
                        raw_wire,
                        oracle_wire,
                    )
                channel_count += 1
                continue

            if isinstance(raw_event, MidiMetaEvent):
                if not oracle_is_meta:
                    actual_category = "sysex" if oracle_type == "sysex" else "channel"
                    _fail(
                        event_location,
                        "event category",
                        "meta",
                        actual_category,
                    )
                oracle_meta_type, oracle_payload = _mido_meta_wire_fields(
                    oracle_event, location=event_location
                )
                if raw_event.meta_type != oracle_meta_type:
                    _fail(
                        event_location,
                        "meta type byte",
                        raw_event.meta_type,
                        oracle_meta_type,
                    )
                if raw_event.payload != oracle_payload:
                    _fail(
                        event_location,
                        "meta payload",
                        raw_event.payload,
                        oracle_payload,
                    )
                meta_count += 1
                continue

            if not isinstance(raw_event, MidiSysExEvent):
                raise MidoDifferentialError(
                    "{}: unsupported raw event class {}".format(
                        event_location, type(raw_event).__name__
                    )
                )
            if oracle_is_meta or oracle_type != "sysex":
                actual_category = "meta" if oracle_is_meta else "channel"
                _fail(
                    event_location,
                    "event category",
                    "sysex",
                    actual_category,
                )
            try:
                oracle_payload = bytes(oracle_event.data)
            except Exception as exc:
                raise MidoDifferentialError(
                    "{}: Mido exposed an invalid SysEx payload: {}: {}".format(
                        event_location, type(exc).__name__, exc
                    )
                ) from exc
            expected_payload = _normalized_sysex_payload_for_mido(raw_event)
            if expected_payload != oracle_payload:
                _fail(
                    event_location,
                    "normalized SysEx payload",
                    expected_payload,
                    oracle_payload,
                )
            sysex_count += 1

        if raw_track.end_tick != absolute_ticks:
            _fail(location, "end tick", raw_track.end_tick, absolute_ticks)
        event_counts.append(len(raw_track.events))
        end_ticks.append(raw_track.end_tick)

    return MidoDifferentialReport(
        source_sha256=raw.sha256,
        source_byte_length=raw.byte_length,
        mido_version=mido_version,
        format_type=raw.format_type,
        ticks_per_quarter_note=raw.ticks_per_quarter_note,
        track_count=raw.track_count,
        track_event_counts=tuple(event_counts),
        track_end_ticks=tuple(end_ticks),
        timing_events_compared=timing_count,
        channel_events_compared=channel_count,
        meta_events_compared=meta_count,
        sysex_payloads_compared=sysex_count,
        sysex_status_fields_unavailable_from_mido=sysex_count,
    )


def validate_parsed_midi_against_mido(
    midi: MidiFile,
    *,
    expected_version: str = MIDO_ORACLE_VERSION,
) -> MidoDifferentialReport:
    """Compare one accepted immutable raw parse result with pinned Mido.

    The raw object is reconstructed byte-for-byte before Mido sees it.  A
    report is returned only on complete agreement for every field Mido retains.
    """

    if not isinstance(midi, MidiFile):
        raise TypeError("midi must be a MidiFile")
    mido, actual_version = _load_pinned_mido(expected_version)
    source = _reconstruct_exact_bytes(midi)
    try:
        oracle = mido.MidiFile(
            file=io.BytesIO(source),
            charset="latin1",
            clip=False,
        )
    except Exception as exc:
        raise MidoDifferentialError(
            "Mido {} rejected bytes accepted by the raw parser: {}: {}".format(
                actual_version, type(exc).__name__, exc
            )
        ) from exc
    return _compare_parsed_to_oracle(
        midi,
        oracle,
        mido_version=actual_version,
    )


def validate_midi_bytes_against_mido(
    data: bytes,
    *,
    limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
    expected_version: str = MIDO_ORACLE_VERSION,
) -> MidoDifferentialReport:
    """Strictly parse bytes, then compare the accepted parse with Mido."""

    midi = parse_midi_bytes(data, limits=limits)
    return validate_parsed_midi_against_mido(
        midi, expected_version=expected_version
    )


def validate_midi_file_against_mido(
    path: Union[str, os.PathLike],
    *,
    limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
    expected_version: str = MIDO_ORACLE_VERSION,
) -> MidoDifferentialReport:
    """Strictly load a regular SMF path, then compare it with Mido."""

    if not isinstance(path, (str, os.PathLike)):
        raise TypeError("path must be a string or path-like object")
    midi = load_midi_file(Path(path), limits=limits)
    return validate_parsed_midi_against_mido(
        midi, expected_version=expected_version
    )


__all__ = [
    "MIDO_ORACLE_VERSION",
    "MidoDifferentialError",
    "MidoDifferentialReport",
    "MidoUnavailableError",
    "MidoVersionError",
    "validate_midi_bytes_against_mido",
    "validate_midi_file_against_mido",
    "validate_parsed_midi_against_mido",
]
