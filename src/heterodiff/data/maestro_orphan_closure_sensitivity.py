"""Explicit sensitivity for one narrow MAESTRO orphan-closure pattern.

The primary MAESTRO semantic policy is unchanged and remains fail-closed.  A
file reaches this module only when that policy raises an orphan-note-closure
error.  This module asks a narrower counterfactual question: would the file be
admitted if every orphan were a source-adjacent, same-tick closure immediately
before a positive onset of the same ``(port, channel, pitch)`` identity?

"Immediately before" is deliberately a track-local wire-order statement.  The
closure and onset must have consecutive event indices in the same track.  The
closure must encounter an empty FIFO queue under the primary policy's atomic
same-tick replay (all closes before all opens).  A closure that consumes an
open note is never dropped.  Different ticks, identities, tracks, intervening
events, or any remaining orphan/dangling condition fail closed.

An admitted result is a named sensitivity, not repaired primary data.  The
source MIDI is deterministically rewritten without the admitted closures and
with all retained channel statuses made explicit, then reparsed and passed to
the unmodified primary builder.  Consequently ``sensitivity_semantics`` is
bound to a distinct transformed MIDI digest.  The immutable private sidecar
binds both source and transformed digests and retains exact source provenance
for each dropped closure and its following onset.  Public summaries contain
counts and commitments only; they contain neither event provenance nor paths.
"""

from __future__ import annotations

from collections import deque
from dataclasses import InitVar, dataclass, field
from typing import Deque, Dict, List, Mapping, Optional, Set, Tuple

from heterodiff.artifacts.manifest import canonical_json_dumps, sha256_bytes

from .maestro_inventory import MaestroMidiInventory
from .maestro_semantics import (
    DEFAULT_MAESTRO_SEMANTIC_LIMITS,
    ChannelEventProvenance,
    MaestroSemanticError,
    MaestroSemanticLimits,
    MaestroSemanticPiece,
    build_maestro_semantics,
)
from .midi_raw import (
    DEFAULT_MIDI_PARSE_LIMITS,
    MidiChannelEvent,
    MidiFile,
    MidiFormatError,
    MidiMetaEvent,
    MidiParseLimits,
    MidiSysExEvent,
    MidiTrack,
    parse_midi_bytes,
)


__all__ = [
    "MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_GATE",
    "MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_AUDIT_GATE",
    "DEFAULT_MAESTRO_ORPHAN_CLOSURE_REWRITE_LIMITS",
    "DroppedRedundantOrphanClosure",
    "MaestroOrphanClosureSensitivity",
    "MaestroOrphanClosureSensitivityAudit",
    "MaestroOrphanClosureSensitivityError",
    "audit_maestro_orphan_closure_sensitivity",
    "audit_maestro_orphan_closure_sensitivity_for_inventory_record",
    "build_maestro_orphan_closure_sensitivity",
    "build_maestro_orphan_closure_sensitivity_for_inventory_record",
    "replay_maestro_orphan_closure_sensitivity_audit",
    "replay_maestro_orphan_closure_sensitivity_audit_for_inventory_record",
]


MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_GATE = (
    "maestro-redundant-pre-onset-orphan-drop-sensitivity-v2"
)
MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_AUDIT_GATE = (
    "maestro-redundant-pre-onset-orphan-drop-audit-v1"
)
_MANIFEST_DOMAIN = b"heterodiff-maestro-orphan-closure-sensitivity-v2\0"
_AUDIT_MANIFEST_DOMAIN = b"heterodiff-maestro-orphan-closure-sensitivity-audit-v1\0"
_FAILURE_DETAIL_DOMAIN = b"heterodiff-maestro-orphan-closure-failure-detail-v1\0"
_MANIFEST_SCHEMA_VERSION = 2
_AUDIT_SCHEMA_VERSION = 1
_PRIMARY_FAILURE_CODE = "ORPHAN_NOTE_CLOSURE"
_SOURCE_SPLITS = frozenset(("train", "validation", "test"))
_SHA256_CHARACTERS = frozenset("0123456789abcdef")
_MAX_VLQ_VALUE = 0x0FFFFFFF
_FACTORY_TOKEN = object()

_REJECTION_CODES = frozenset(
    (
        "ATOMIC_NOTE_EVENT_LIMIT_EXCEEDED",
        "DANGLING_ONSET_AFTER_CANDIDATE_DROP",
        "NO_QUALIFYING_REDUNDANT_ORPHAN_CLOSURE",
        "NONPOSITIVE_NOTE_DURATION",
        "NOTE_EVENT_LIMIT_EXCEEDED",
        "NOTE_ONSET_LIMIT_EXCEEDED",
        "OPEN_NOTE_LIMIT_EXCEEDED",
        "ORPHAN_NOT_ADJACENT_SAME_TICK_PRE_ONSET",
        "PRIMARY_SEMANTICS_ADMITTED",
        "PRIMARY_SEMANTIC_FAILURE_NOT_ORPHAN_NOTE_CLOSURE",
        "REWRITE_DELTA_VLQ_EXCEEDED",
        "REWRITE_EVENT_COUNT_MISMATCH",
        "REWRITE_PARSE_FAILURE",
        "REWRITE_RESOURCE_LIMIT_EXCEEDED",
        "REWRITE_TRACK_EMPTY",
        "TRANSFORMED_SEMANTIC_FAILURE",
    )
)

_PUBLIC_REJECTION_MESSAGES = {
    "ATOMIC_NOTE_EVENT_LIMIT_EXCEEDED": (
        "same-tick note events exceed maximum_atomic_note_events during "
        "sensitivity replay"
    ),
    "DANGLING_ONSET_AFTER_CANDIDATE_DROP": (
        "candidate drop replay still fails: dangling positive note onset(s)"
    ),
    "NO_QUALIFYING_REDUNDANT_ORPHAN_CLOSURE": (
        "no qualifying redundant orphan closure was found"
    ),
    "NONPOSITIVE_NOTE_DURATION": (
        "sensitivity replay produced nonpositive note duration"
    ),
    "NOTE_EVENT_LIMIT_EXCEEDED": (
        "note events exceed maximum_note_events during sensitivity replay"
    ),
    "NOTE_ONSET_LIMIT_EXCEEDED": (
        "positive onsets exceed maximum_note_onsets during sensitivity replay"
    ),
    "OPEN_NOTE_LIMIT_EXCEEDED": (
        "sensitivity replay exceeds maximum_open_notes"
    ),
    "ORPHAN_NOT_ADJACENT_SAME_TICK_PRE_ONSET": (
        "orphan closure is not an adjacent same-tick pre-onset of the same identity"
    ),
    "PRIMARY_SEMANTICS_ADMITTED": (
        "primary semantics already admits the source; sensitivity is inapplicable"
    ),
    "PRIMARY_SEMANTIC_FAILURE_NOT_ORPHAN_NOTE_CLOSURE": (
        "primary semantic failure is not ORPHAN_NOTE_CLOSURE"
    ),
    "REWRITE_DELTA_VLQ_EXCEEDED": (
        "rewritten delta-time exceeds the four-byte VLQ range"
    ),
    "REWRITE_EVENT_COUNT_MISMATCH": (
        "rewritten event count does not match exact omissions"
    ),
    "REWRITE_PARSE_FAILURE": "deterministic rewritten MIDI failed strict parsing",
    "REWRITE_RESOURCE_LIMIT_EXCEEDED": (
        "deterministic rewritten MIDI exceeds the frozen rewrite limits"
    ),
    "REWRITE_TRACK_EMPTY": "rewritten MIDI track unexpectedly became empty",
    "TRANSFORMED_SEMANTIC_FAILURE": (
        "transformed replay is not admitted by the unchanged primary builder"
    ),
}


# Explicit-status expansion can add at most one byte per retained channel
# event.  The source and semantic gates both cap total events at 150,000, so
# this predeclared ceiling admits every rewrite of a default-gated source
# without manufacturing a policy from the observed output size.
DEFAULT_MAESTRO_ORPHAN_CLOSURE_REWRITE_LIMITS = MidiParseLimits(
    maximum_file_bytes=8 * 1024 * 1024 + 150_000,
    maximum_tracks=256,
    maximum_track_bytes=8 * 1024 * 1024 + 150_000,
    maximum_event_payload_bytes=4 * 1024 * 1024,
    maximum_events_per_track=150_000,
    maximum_total_events=150_000,
    maximum_absolute_tick=0x7FFFFFFF,
    maximum_ticks_per_quarter_note=0x7FFF,
)


class MaestroOrphanClosureSensitivityError(ValueError):
    """Raised when the exact sensitivity preconditions are not satisfied."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "ORPHAN_CLOSURE_SENSITIVITY_ERROR",
    ) -> None:
        if not isinstance(message, str) or not message:
            raise TypeError("message must be a nonempty string")
        if not isinstance(code, str) or not code:
            raise TypeError("code must be a nonempty string")
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
        raise ValueError("source_split must be test, train, or validation")
    return value


def _limits_dict(limits: MaestroSemanticLimits) -> Dict[str, int]:
    return {
        "maximum_tracks": limits.maximum_tracks,
        "maximum_total_events": limits.maximum_total_events,
        "maximum_note_events": limits.maximum_note_events,
        "maximum_note_onsets": limits.maximum_note_onsets,
        "maximum_open_notes": limits.maximum_open_notes,
        "maximum_atomic_note_events": limits.maximum_atomic_note_events,
        "maximum_tempo_events": limits.maximum_tempo_events,
        "maximum_tempo_points": limits.maximum_tempo_points,
        "maximum_control_changes": limits.maximum_control_changes,
        "maximum_midi_port_events": limits.maximum_midi_port_events,
        "maximum_time_signatures": limits.maximum_time_signatures,
    }


def _midi_limits_dict(limits: MidiParseLimits) -> Dict[str, int]:
    return {
        "maximum_file_bytes": limits.maximum_file_bytes,
        "maximum_tracks": limits.maximum_tracks,
        "maximum_track_bytes": limits.maximum_track_bytes,
        "maximum_event_payload_bytes": limits.maximum_event_payload_bytes,
        "maximum_events_per_track": limits.maximum_events_per_track,
        "maximum_total_events": limits.maximum_total_events,
        "maximum_absolute_tick": limits.maximum_absolute_tick,
        "maximum_ticks_per_quarter_note": (
            limits.maximum_ticks_per_quarter_note
        ),
    }


def _failure_detail_sha256(detail: Optional[str]) -> Optional[str]:
    if detail is None:
        return None
    return sha256_bytes(_FAILURE_DETAIL_DOMAIN + detail.encode("utf-8"))


def _private_failure_detail(value: object, *, name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise TypeError("{} must be a nonempty string or None".format(name))
    if len(value) > 4096 or "\x00" in value:
        raise ValueError("{} exceeds the private-detail contract".format(name))
    return value


def _exact_source_snapshot(
    midi: MidiFile,
    *,
    source_limits: MidiParseLimits,
) -> MidiFile:
    """Rebuild and reparse one exact base-class source under frozen limits.

    The caller-supplied object is never used after this function returns.  A
    single field snapshot plus a strict byte reconstruction defeats stateful
    subclasses, stale/mutated digest fields, and relaxed-parser objects.
    """

    if type(midi) is not MidiFile:
        raise TypeError("midi must be an exact MidiFile")
    if type(source_limits) is not MidiParseLimits:
        raise TypeError("source_limits must be an exact MidiParseLimits instance")

    format_type = midi.format_type
    ticks_per_quarter_note = midi.ticks_per_quarter_note
    tracks = midi.tracks
    claimed_byte_length = midi.byte_length
    claimed_sha256 = midi.sha256
    if (
        isinstance(format_type, bool)
        or not isinstance(format_type, int)
        or format_type not in (0, 1, 2)
        or isinstance(ticks_per_quarter_note, bool)
        or not isinstance(ticks_per_quarter_note, int)
        or ticks_per_quarter_note < 1
        or isinstance(claimed_byte_length, bool)
        or not isinstance(claimed_byte_length, int)
        or claimed_byte_length < 1
    ):
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI snapshot fields are inconsistent",
            code="SOURCE_SNAPSHOT_MISMATCH",
        )
    try:
        _sha256(claimed_sha256, name="source_midi_sha256")
    except (TypeError, ValueError):
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI snapshot fields are inconsistent",
            code="SOURCE_SNAPSHOT_MISMATCH",
        ) from None
    if not isinstance(tracks, tuple) or any(type(track) is not MidiTrack for track in tracks):
        raise TypeError("midi tracks must be exact MidiTrack values")
    if not tracks or len(tracks) > 0xFFFF or (format_type == 0 and len(tracks) != 1):
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI snapshot fields are inconsistent",
            code="SOURCE_SNAPSHOT_MISMATCH",
        )
    if claimed_byte_length > source_limits.maximum_file_bytes:
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI exceeds the frozen source limits",
            code="SOURCE_RESOURCE_LIMIT_EXCEEDED",
        )
    if len(tracks) > source_limits.maximum_tracks:
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI exceeds the frozen source limits",
            code="SOURCE_RESOURCE_LIMIT_EXCEEDED",
        )
    if ticks_per_quarter_note > source_limits.maximum_ticks_per_quarter_note:
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI exceeds the frozen source limits",
            code="SOURCE_RESOURCE_LIMIT_EXCEEDED",
        )

    track_payloads: List[bytes] = []
    total_events = 0
    expected_file_bytes = 14 + 8 * len(tracks)
    admitted_event_types = (MidiChannelEvent, MidiMetaEvent, MidiSysExEvent)
    for track in tracks:
        events = track.events
        if not isinstance(events, tuple) or any(
            type(event) not in admitted_event_types for event in events
        ):
            raise TypeError("MIDI tracks must contain exact raw-event values")
        if (
            isinstance(track.byte_length, bool)
            or not isinstance(track.byte_length, int)
            or track.byte_length < 1
        ):
            raise MaestroOrphanClosureSensitivityError(
                "source MIDI snapshot fields are inconsistent",
                code="SOURCE_SNAPSHOT_MISMATCH",
            )
        if len(events) > source_limits.maximum_events_per_track:
            raise MaestroOrphanClosureSensitivityError(
                "source MIDI exceeds the frozen source limits",
                code="SOURCE_RESOURCE_LIMIT_EXCEEDED",
            )
        total_events += len(events)
        if total_events > source_limits.maximum_total_events:
            raise MaestroOrphanClosureSensitivityError(
                "source MIDI exceeds the frozen source limits",
                code="SOURCE_RESOURCE_LIMIT_EXCEEDED",
            )
        encoded_length = 0
        for event in events:
            if not isinstance(event.encoded_bytes, bytes) or not event.encoded_bytes:
                raise MaestroOrphanClosureSensitivityError(
                    "source MIDI snapshot fields are inconsistent",
                    code="SOURCE_SNAPSHOT_MISMATCH",
                )
            encoded_length += len(event.encoded_bytes)
            if encoded_length > source_limits.maximum_track_bytes:
                raise MaestroOrphanClosureSensitivityError(
                    "source MIDI exceeds the frozen source limits",
                    code="SOURCE_RESOURCE_LIMIT_EXCEEDED",
                )
        if encoded_length > 0xFFFFFFFF or encoded_length != track.byte_length:
            raise MaestroOrphanClosureSensitivityError(
                "source MIDI snapshot fields are inconsistent",
                code="SOURCE_SNAPSHOT_MISMATCH",
            )
        expected_file_bytes += encoded_length
        if expected_file_bytes > source_limits.maximum_file_bytes:
            raise MaestroOrphanClosureSensitivityError(
                "source MIDI exceeds the frozen source limits",
                code="SOURCE_RESOURCE_LIMIT_EXCEEDED",
            )
        track_payloads.append(b"".join(event.encoded_bytes for event in events))

    if expected_file_bytes != claimed_byte_length:
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI snapshot fields are inconsistent",
            code="SOURCE_SNAPSHOT_MISMATCH",
        )
    header = (
        b"MThd"
        + (6).to_bytes(4, "big")
        + format_type.to_bytes(2, "big")
        + len(track_payloads).to_bytes(2, "big")
        + ticks_per_quarter_note.to_bytes(2, "big")
    )
    encoded = header + b"".join(
        b"MTrk" + len(payload).to_bytes(4, "big") + payload
        for payload in track_payloads
    )
    try:
        snapshot = parse_midi_bytes(encoded, limits=source_limits)
    except (MidiFormatError, OverflowError, ValueError):
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI failed exact snapshot validation",
            code="SOURCE_SNAPSHOT_INVALID",
        ) from None
    if snapshot.sha256 != claimed_sha256 or snapshot.byte_length != claimed_byte_length:
        raise MaestroOrphanClosureSensitivityError(
            "source MIDI snapshot digest or length does not match",
            code="SOURCE_SNAPSHOT_MISMATCH",
        )
    return snapshot


@dataclass(frozen=True)
class DroppedRedundantOrphanClosure:
    """Exact source evidence for one counterfactually omitted closure."""

    port: int
    channel: int
    pitch: int
    closure_spelling: str
    closure_provenance: ChannelEventProvenance
    following_onset_provenance: ChannelEventProvenance
    _factory_token: InitVar[object]

    def __post_init__(self, _factory_token: object) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            raise TypeError(
                "DroppedRedundantOrphanClosure is factory-only; use the "
                "orphan-closure sensitivity audit"
            )
        for name in ("port", "channel", "pitch"):
            _plain_int(getattr(self, name), name=name)
        if self.port > 127 or self.channel > 15 or self.pitch > 127:
            raise ValueError("port/channel/pitch is outside the MIDI range")
        if self.closure_spelling not in (
            "note_off",
            "note_on_velocity_zero",
        ):
            raise ValueError("closure_spelling is not admitted")
        if not isinstance(self.closure_provenance, ChannelEventProvenance):
            raise TypeError("closure_provenance must be ChannelEventProvenance")
        if not isinstance(
            self.following_onset_provenance,
            ChannelEventProvenance,
        ):
            raise TypeError(
                "following_onset_provenance must be ChannelEventProvenance"
            )
        closure = self.closure_provenance
        onset = self.following_onset_provenance
        expected_closure_type = (
            "note_off"
            if self.closure_spelling == "note_off"
            else "note_on"
        )
        if (
            closure.message_type != expected_closure_type
            or (closure.status & 0x0F) != self.channel
            or closure.data[0] != self.pitch
        ):
            raise ValueError("closure provenance does not match its identity")
        if (
            self.closure_spelling == "note_on_velocity_zero"
            and closure.data[1] != 0
        ):
            raise ValueError("zero-velocity note_on closure must retain zero")
        if (
            onset.message_type != "note_on"
            or onset.data[1] == 0
            or (onset.status & 0x0F) != self.channel
            or onset.data[0] != self.pitch
        ):
            raise ValueError("following onset does not match the same identity")
        if closure.track_index != onset.track_index:
            raise ValueError("closure and onset must be in the same source track")
        if onset.event_index != closure.event_index + 1:
            raise ValueError("closure and onset must be source-adjacent")
        if closure.absolute_tick != onset.absolute_tick:
            raise ValueError("closure and onset must have the same absolute tick")

    @property
    def identity(self) -> Tuple[int, int, int]:
        return (self.port, self.channel, self.pitch)

    @property
    def absolute_tick(self) -> int:
        return self.closure_provenance.absolute_tick

    @property
    def source_key(self) -> Tuple[int, int]:
        return (
            self.closure_provenance.track_index,
            self.closure_provenance.event_index,
        )

    @property
    def order_key(self) -> Tuple[int, int, int]:
        return (
            self.absolute_tick,
            self.closure_provenance.track_index,
            self.closure_provenance.event_index,
        )

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "identity": {
                "port": self.port,
                "channel": self.channel,
                "pitch": self.pitch,
            },
            "absolute_tick": self.absolute_tick,
            "closure_spelling": self.closure_spelling,
            "closure_provenance": self.closure_provenance.to_private_dict(),
            "following_onset_provenance": (
                self.following_onset_provenance.to_private_dict()
            ),
            "fifo_open_queue_size_before_closure": 0,
        }


@dataclass(frozen=True)
class MaestroOrphanClosureSensitivity:
    """Immutable source-to-counterfactual semantic sensitivity sidecar."""

    source_split: str
    source_midi_sha256: str
    source_format_type: int
    source_ticks_per_quarter_note: int
    source_event_count: int
    source_byte_length: int
    source_track_sha256s: Tuple[str, ...]
    transformed_midi_sha256: str
    transformed_event_count: int
    transformed_byte_length: int
    transformed_track_sha256s: Tuple[str, ...]
    limits: MaestroSemanticLimits
    source_limits: MidiParseLimits
    rewrite_limits: MidiParseLimits
    dropped_closures: Tuple[DroppedRedundantOrphanClosure, ...]
    sensitivity_semantics: MaestroSemanticPiece
    _factory_token: InitVar[object]
    primary_failure_code: str = _PRIMARY_FAILURE_CODE
    schema_version: int = _MANIFEST_SCHEMA_VERSION
    manifest_sha256: str = field(init=False)

    def __post_init__(self, _factory_token: object) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            raise TypeError(
                "MaestroOrphanClosureSensitivity is factory-only; use "
                "build_maestro_orphan_closure_sensitivity"
            )
        _source_split(self.source_split)
        _sha256(self.source_midi_sha256, name="source_midi_sha256")
        _sha256(self.transformed_midi_sha256, name="transformed_midi_sha256")
        if self.source_midi_sha256 == self.transformed_midi_sha256:
            raise ValueError("source and transformed MIDI digests must differ")
        _plain_int(self.schema_version, name="schema_version", minimum=1)
        if self.schema_version != _MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported orphan-sensitivity schema_version")
        if self.primary_failure_code != _PRIMARY_FAILURE_CODE:
            raise ValueError("primary_failure_code must be ORPHAN_NOTE_CLOSURE")
        _plain_int(self.source_format_type, name="source_format_type")
        if self.source_format_type not in (0, 1):
            raise ValueError("source_format_type must be 0 or 1")
        _plain_int(
            self.source_ticks_per_quarter_note,
            name="source_ticks_per_quarter_note",
            minimum=1,
        )
        _plain_int(self.source_event_count, name="source_event_count", minimum=1)
        _plain_int(self.source_byte_length, name="source_byte_length", minimum=1)
        _plain_int(
            self.transformed_event_count,
            name="transformed_event_count",
            minimum=1,
        )
        _plain_int(
            self.transformed_byte_length,
            name="transformed_byte_length",
            minimum=1,
        )
        for name, values in (
            ("source_track_sha256s", self.source_track_sha256s),
            ("transformed_track_sha256s", self.transformed_track_sha256s),
        ):
            if not isinstance(values, tuple) or not values:
                raise TypeError("{} must be a nonempty tuple".format(name))
            for value in values:
                _sha256(value, name=name)
        if len(self.source_track_sha256s) != len(
            self.transformed_track_sha256s
        ):
            raise ValueError("source and transformed track counts must match")
        if type(self.limits) is not MaestroSemanticLimits:
            raise TypeError("limits must be an exact MaestroSemanticLimits instance")
        if type(self.source_limits) is not MidiParseLimits:
            raise TypeError("source_limits must be an exact MidiParseLimits instance")
        if type(self.rewrite_limits) is not MidiParseLimits:
            raise TypeError("rewrite_limits must be an exact MidiParseLimits instance")
        if (
            not isinstance(self.dropped_closures, tuple)
            or not self.dropped_closures
            or any(
                type(item) is not DroppedRedundantOrphanClosure
                for item in self.dropped_closures
            )
        ):
            raise TypeError(
                "dropped_closures must be a nonempty tuple of exact evidence"
            )
        order = tuple(item.order_key for item in self.dropped_closures)
        if order != tuple(sorted(order)) or len(set(order)) != len(order):
            raise ValueError("dropped closures must use unique canonical order")
        if self.source_event_count - self.transformed_event_count != len(
            self.dropped_closures
        ):
            raise ValueError("event-count difference must equal dropped closure count")
        if type(self.sensitivity_semantics) is not MaestroSemanticPiece:
            raise TypeError("sensitivity_semantics must be an exact MaestroSemanticPiece")
        semantic = self.sensitivity_semantics
        if semantic.source_split != self.source_split:
            raise ValueError("sensitivity semantic split does not match the source")
        if semantic.source_midi_sha256 != self.transformed_midi_sha256:
            raise ValueError("sensitivity semantics is not bound to transformed MIDI")
        if semantic.format_type != self.source_format_type:
            raise ValueError("sensitivity semantic format does not match the source")
        if (
            semantic.ticks_per_quarter_note
            != self.source_ticks_per_quarter_note
        ):
            raise ValueError("sensitivity semantic PPQN does not match the source")
        if self.source_event_count > self.limits.maximum_total_events:
            raise ValueError("source event count exceeds committed semantic limits")
        if self.transformed_event_count > self.limits.maximum_total_events:
            raise ValueError("transformed event count exceeds committed semantic limits")
        if len(semantic.notes) > self.limits.maximum_note_onsets:
            raise ValueError("semantic notes exceed committed semantic limits")
        if len(semantic.controllers) > self.limits.maximum_control_changes:
            raise ValueError("controllers exceed committed semantic limits")
        if len(semantic.midi_ports) > self.limits.maximum_midi_port_events:
            raise ValueError("MIDI-port facts exceed committed semantic limits")
        if len(semantic.time_signatures) > self.limits.maximum_time_signatures:
            raise ValueError("time signatures exceed committed semantic limits")
        if self.source_byte_length > self.source_limits.maximum_file_bytes:
            raise ValueError("source bytes exceed committed source limits")
        if self.transformed_byte_length > self.rewrite_limits.maximum_file_bytes:
            raise ValueError("transformed bytes exceed committed rewrite limits")

        dropped_before_by_track: Dict[int, List[int]] = {}
        for item in self.dropped_closures:
            dropped_before_by_track.setdefault(
                item.closure_provenance.track_index,
                [],
            ).append(item.closure_provenance.event_index)
        semantic_onsets = {
            (
                note.onset_provenance.track_index,
                note.onset_provenance.event_index,
                note.onset_tick,
                note.port,
                note.channel,
                note.pitch,
                note.onset_velocity,
            )
            for note in semantic.notes
        }
        for item in self.dropped_closures:
            source_onset = item.following_onset_provenance
            shifted_event_index = source_onset.event_index - sum(
                dropped_index < source_onset.event_index
                for dropped_index in dropped_before_by_track.get(
                    source_onset.track_index,
                    (),
                )
            )
            expected = (
                source_onset.track_index,
                shifted_event_index,
                source_onset.absolute_tick,
                item.port,
                item.channel,
                item.pitch,
                source_onset.data[1],
            )
            if expected not in semantic_onsets:
                raise ValueError(
                    "dropped evidence does not bind to a transformed semantic onset"
                )

        private_json = canonical_json_dumps(self._private_payload())
        object.__setattr__(
            self,
            "manifest_sha256",
            sha256_bytes(_MANIFEST_DOMAIN + private_json.encode("utf-8")),
        )

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "gate": MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_GATE,
            "primary_failure_code": self.primary_failure_code,
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "source_format_type": self.source_format_type,
            "source_ticks_per_quarter_note": self.source_ticks_per_quarter_note,
            "source_event_count": self.source_event_count,
            "source_byte_length": self.source_byte_length,
            "source_track_sha256s": list(self.source_track_sha256s),
            "transformed_midi_sha256": self.transformed_midi_sha256,
            "transformed_event_count": self.transformed_event_count,
            "transformed_byte_length": self.transformed_byte_length,
            "transformed_track_sha256s": list(
                self.transformed_track_sha256s
            ),
            "limits": _limits_dict(self.limits),
            "source_limits": _midi_limits_dict(self.source_limits),
            "rewrite_limits": _midi_limits_dict(self.rewrite_limits),
            "dropped_closures": [
                item.to_private_dict() for item in self.dropped_closures
            ],
            "sensitivity_semantic_manifest_sha256": (
                self.sensitivity_semantics.manifest_sha256
            ),
            "rewrite_policy": {
                "dropped_events": "listed redundant orphan closures only",
                "retained_absolute_ticks": True,
                "retained_event_payloads": True,
                "channel_status_encoding": "explicit",
                "primary_builder_reused_without_policy_change": True,
            },
        }

    def to_private_dict(self) -> Dict[str, object]:
        """Return a fresh exact, provenance-bearing sidecar payload."""

        return self._private_payload()

    def to_private_json(self) -> str:
        return canonical_json_dumps(self._private_payload())

    def public_summary(self) -> Mapping[str, object]:
        """Return path-free aggregate evidence without event provenance."""

        spelling_counts = {
            "note_off": 0,
            "note_on_velocity_zero": 0,
        }
        for item in self.dropped_closures:
            spelling_counts[item.closure_spelling] += 1
        return {
            "schema_version": self.schema_version,
            "gate": MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_GATE,
            "status": "sensitivity_admitted",
            "primary_failure_code": self.primary_failure_code,
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "transformed_midi_sha256": self.transformed_midi_sha256,
            "manifest_sha256": self.manifest_sha256,
            "sensitivity_semantic_manifest_sha256": (
                self.sensitivity_semantics.manifest_sha256
            ),
            "dropped_closure_count": len(self.dropped_closures),
            "dropped_closure_spelling_counts": spelling_counts,
            "sensitivity_note_count": len(self.sensitivity_semantics.notes),
            "source_byte_length": self.source_byte_length,
            "transformed_byte_length": self.transformed_byte_length,
            "source_limits": _midi_limits_dict(self.source_limits),
            "rewrite_limits": _midi_limits_dict(self.rewrite_limits),
            "semantic_limits": _limits_dict(self.limits),
            "claim_boundary": {
                "primary_semantic_policy_changed": False,
                "source_midi_mutated": False,
                "result_is_primary_semantics": False,
                "result_is_named_counterfactual_sensitivity": True,
                "only_listed_source_adjacent_orphans_dropped": True,
                "unlisted_orphan_or_dangling_events_repaired": False,
                "lossy_tensor_emitted": False,
            },
            "privacy": {
                "event_ticks_included": False,
                "event_identities_included": False,
                "raw_event_provenance_included": False,
                "source_paths_included": False,
            },
        }


@dataclass(frozen=True)
class MaestroOrphanClosureSensitivityAudit:
    """Digest-bearing outcome for every valid source sensitivity attempt."""

    source_split: str
    source_midi_sha256: str
    source_format_type: int
    source_ticks_per_quarter_note: int
    source_event_count: int
    source_byte_length: int
    source_track_sha256s: Tuple[str, ...]
    limits: MaestroSemanticLimits
    source_limits: MidiParseLimits
    rewrite_limits: MidiParseLimits
    status: str
    primary_failure_code: Optional[str]
    primary_failure_detail: Optional[str]
    rejection_code: Optional[str]
    sensitivity_failure_detail: Optional[str]
    admitted_sensitivity: Optional[MaestroOrphanClosureSensitivity]
    _factory_token: InitVar[object]
    schema_version: int = _AUDIT_SCHEMA_VERSION
    manifest_sha256: str = field(init=False)

    def __post_init__(self, _factory_token: object) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            raise TypeError(
                "MaestroOrphanClosureSensitivityAudit is factory-only; use "
                "audit_maestro_orphan_closure_sensitivity"
            )
        _source_split(self.source_split)
        _sha256(self.source_midi_sha256, name="source_midi_sha256")
        _plain_int(self.source_format_type, name="source_format_type")
        if self.source_format_type not in (0, 1, 2):
            raise ValueError("source_format_type must be 0, 1, or 2")
        _plain_int(
            self.source_ticks_per_quarter_note,
            name="source_ticks_per_quarter_note",
            minimum=1,
        )
        _plain_int(self.source_event_count, name="source_event_count", minimum=1)
        _plain_int(self.source_byte_length, name="source_byte_length", minimum=1)
        if (
            not isinstance(self.source_track_sha256s, tuple)
            or not self.source_track_sha256s
        ):
            raise TypeError("source_track_sha256s must be a nonempty tuple")
        for digest in self.source_track_sha256s:
            _sha256(digest, name="source_track_sha256s")
        if type(self.limits) is not MaestroSemanticLimits:
            raise TypeError("limits must be an exact MaestroSemanticLimits instance")
        if type(self.source_limits) is not MidiParseLimits:
            raise TypeError("source_limits must be an exact MidiParseLimits instance")
        if type(self.rewrite_limits) is not MidiParseLimits:
            raise TypeError("rewrite_limits must be an exact MidiParseLimits instance")
        if self.source_event_count > self.source_limits.maximum_total_events:
            raise ValueError("source event count exceeds source limits")
        if self.source_byte_length > self.source_limits.maximum_file_bytes:
            raise ValueError("source byte length exceeds source limits")
        if self.status not in ("sensitivity_admitted", "sensitivity_rejected"):
            raise ValueError("status is not admitted")
        if self.primary_failure_code is not None and (
            not isinstance(self.primary_failure_code, str)
            or not self.primary_failure_code
        ):
            raise TypeError("primary_failure_code must be a nonempty string or None")
        _private_failure_detail(
            self.primary_failure_detail,
            name="primary_failure_detail",
        )
        _private_failure_detail(
            self.sensitivity_failure_detail,
            name="sensitivity_failure_detail",
        )

        if self.status == "sensitivity_admitted":
            if self.primary_failure_code != _PRIMARY_FAILURE_CODE:
                raise ValueError("admitted audit must bind the primary orphan code")
            if self.primary_failure_detail is None:
                raise ValueError("admitted audit must retain primary failure detail")
            if self.rejection_code is not None:
                raise ValueError("admitted audit cannot contain a rejection code")
            if self.sensitivity_failure_detail is not None:
                raise ValueError("admitted audit cannot contain sensitivity failure detail")
            if type(self.admitted_sensitivity) is not MaestroOrphanClosureSensitivity:
                raise TypeError("admitted audit must contain an exact sensitivity")
            admitted = self.admitted_sensitivity
            if (
                admitted.source_split != self.source_split
                or admitted.source_midi_sha256 != self.source_midi_sha256
                or admitted.source_format_type != self.source_format_type
                or admitted.source_ticks_per_quarter_note
                != self.source_ticks_per_quarter_note
                or admitted.source_event_count != self.source_event_count
                or admitted.source_byte_length != self.source_byte_length
                or admitted.source_track_sha256s != self.source_track_sha256s
                or admitted.limits != self.limits
                or admitted.source_limits != self.source_limits
                or admitted.rewrite_limits != self.rewrite_limits
            ):
                raise ValueError("admitted sensitivity is not bound to the audit source")
        else:
            if self.rejection_code not in _REJECTION_CODES:
                raise ValueError("rejected audit must contain a frozen rejection code")
            if self.admitted_sensitivity is not None:
                raise ValueError("rejected audit cannot contain an admitted sensitivity")
            if self.rejection_code == "PRIMARY_SEMANTICS_ADMITTED":
                if (
                    self.primary_failure_code is not None
                    or self.primary_failure_detail is not None
                ):
                    raise ValueError(
                        "primary-admitted rejection cannot claim a primary failure"
                    )
            elif (
                self.primary_failure_code is None
                or self.primary_failure_detail is None
            ):
                raise ValueError("rejected audit must retain its primary failure")
            if self.sensitivity_failure_detail is None:
                raise ValueError("rejected audit must retain sensitivity failure detail")

        if self.schema_version != _AUDIT_SCHEMA_VERSION:
            raise ValueError("unsupported orphan-sensitivity audit schema_version")
        object.__setattr__(
            self,
            "manifest_sha256",
            sha256_bytes(
                _AUDIT_MANIFEST_DOMAIN
                + canonical_json_dumps(self._private_payload()).encode("utf-8")
            ),
        )

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "gate": MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_AUDIT_GATE,
            "status": self.status,
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "source_format_type": self.source_format_type,
            "source_ticks_per_quarter_note": self.source_ticks_per_quarter_note,
            "source_event_count": self.source_event_count,
            "source_byte_length": self.source_byte_length,
            "source_track_sha256s": list(self.source_track_sha256s),
            "semantic_limits": _limits_dict(self.limits),
            "source_limits": _midi_limits_dict(self.source_limits),
            "rewrite_limits": _midi_limits_dict(self.rewrite_limits),
            "primary_failure": {
                "code": self.primary_failure_code,
                "detail": self.primary_failure_detail,
                "detail_sha256": _failure_detail_sha256(
                    self.primary_failure_detail
                ),
            },
            "sensitivity_failure": {
                "code": self.rejection_code,
                "detail": self.sensitivity_failure_detail,
                "detail_sha256": _failure_detail_sha256(
                    self.sensitivity_failure_detail
                ),
            },
            "admitted_sensitivity": (
                None
                if self.admitted_sensitivity is None
                else self.admitted_sensitivity.to_private_dict()
            ),
            "admitted_sensitivity_manifest_sha256": (
                None
                if self.admitted_sensitivity is None
                else self.admitted_sensitivity.manifest_sha256
            ),
        }

    def to_private_dict(self) -> Dict[str, object]:
        return self._private_payload()

    def to_private_json(self) -> str:
        return canonical_json_dumps(self._private_payload())

    def public_summary(self) -> Mapping[str, object]:
        return {
            "schema_version": self.schema_version,
            "gate": MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_AUDIT_GATE,
            "status": self.status,
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "source_event_count": self.source_event_count,
            "source_byte_length": self.source_byte_length,
            "semantic_limits": _limits_dict(self.limits),
            "source_limits": _midi_limits_dict(self.source_limits),
            "rewrite_limits": _midi_limits_dict(self.rewrite_limits),
            "primary_failure_code": self.primary_failure_code,
            "primary_failure_detail_sha256": _failure_detail_sha256(
                self.primary_failure_detail
            ),
            "rejection_code": self.rejection_code,
            "sensitivity_failure_detail_sha256": _failure_detail_sha256(
                self.sensitivity_failure_detail
            ),
            "manifest_sha256": self.manifest_sha256,
            "admitted_sensitivity": (
                None
                if self.admitted_sensitivity is None
                else self.admitted_sensitivity.public_summary()
            ),
            "privacy": {
                "failure_details_included": False,
                "event_ticks_included": False,
                "event_identities_included": False,
                "raw_event_provenance_included": False,
                "source_paths_included": False,
            },
            "claim_boundary": {
                "primary_semantic_policy_changed": False,
                "result_is_primary_semantics": False,
                "result_is_named_counterfactual_sensitivity": True,
                "rejected_outcome_is_digest_committed": (
                    self.status == "sensitivity_rejected"
                ),
            },
        }


@dataclass(frozen=True)
class _AnnotatedNoteEvent:
    event: MidiChannelEvent
    port: int
    closure_spelling: Optional[str]

    @property
    def is_open(self) -> bool:
        velocity = self.event.velocity
        if velocity is None:
            raise AssertionError("annotated note event lacks velocity")
        return self.event.message_type == "note_on" and velocity > 0

    @property
    def identity(self) -> Tuple[int, int, int]:
        pitch = self.event.note
        if pitch is None:
            raise AssertionError("annotated note event lacks pitch")
        return (self.port, self.event.channel, pitch)

    @property
    def order_key(self) -> Tuple[int, int, int]:
        return (
            self.event.absolute_ticks,
            self.event.track_index,
            self.event.event_index,
        )


def _annotated_note_events(
    midi: MidiFile,
    *,
    limits: MaestroSemanticLimits,
) -> Tuple[
    Tuple[_AnnotatedNoteEvent, ...],
    Mapping[Tuple[int, int], _AnnotatedNoteEvent],
]:
    notes: List[_AnnotatedNoteEvent] = []
    by_source_key: Dict[Tuple[int, int], _AnnotatedNoteEvent] = {}
    for track in midi.tracks:
        current_port = 0
        for event in track.events:
            if isinstance(event, MidiMetaEvent) and event.meta_type == 0x21:
                current_port = event.payload[0]
                continue
            if not isinstance(event, MidiChannelEvent) or event.message_type not in (
                "note_on",
                "note_off",
            ):
                continue
            if len(notes) >= limits.maximum_note_events:
                raise MaestroOrphanClosureSensitivityError(
                    "note events exceed maximum_note_events during sensitivity replay",
                    code="NOTE_EVENT_LIMIT_EXCEEDED",
                )
            velocity = event.velocity
            if velocity is None:
                raise AssertionError("raw note event lacks velocity")
            closure_spelling = None
            if event.message_type == "note_off":
                closure_spelling = "note_off"
            elif velocity == 0:
                closure_spelling = "note_on_velocity_zero"
            item = _AnnotatedNoteEvent(
                event=event,
                port=current_port,
                closure_spelling=closure_spelling,
            )
            notes.append(item)
            by_source_key[(event.track_index, event.event_index)] = item
    return tuple(sorted(notes, key=lambda item: item.order_key)), by_source_key


def _following_matching_onset(
    orphan: _AnnotatedNoteEvent,
    by_source_key: Mapping[Tuple[int, int], _AnnotatedNoteEvent],
) -> Optional[_AnnotatedNoteEvent]:
    following = by_source_key.get(
        (orphan.event.track_index, orphan.event.event_index + 1)
    )
    if following is None:
        return None
    if not following.is_open:
        return None
    if following.identity != orphan.identity:
        return None
    if following.event.absolute_ticks != orphan.event.absolute_ticks:
        return None
    return following


def _detect_redundant_orphans(
    midi: MidiFile,
    *,
    limits: MaestroSemanticLimits,
) -> Tuple[DroppedRedundantOrphanClosure, ...]:
    events, by_source_key = _annotated_note_events(midi, limits=limits)
    opening_count = sum(item.is_open for item in events)
    if opening_count > limits.maximum_note_onsets:
        raise MaestroOrphanClosureSensitivityError(
            "positive onsets exceed maximum_note_onsets during sensitivity replay",
            code="NOTE_ONSET_LIMIT_EXCEEDED",
        )

    queues: Dict[Tuple[int, int, int], Deque[_AnnotatedNoteEvent]] = {}
    open_count = 0
    dropped: List[DroppedRedundantOrphanClosure] = []
    cursor = 0
    while cursor < len(events):
        tick = events[cursor].event.absolute_ticks
        end = cursor + 1
        while end < len(events) and events[end].event.absolute_ticks == tick:
            end += 1
        atomic = events[cursor:end]
        if len(atomic) > limits.maximum_atomic_note_events:
            raise MaestroOrphanClosureSensitivityError(
                "same-tick note events exceed maximum_atomic_note_events during sensitivity replay",
                code="ATOMIC_NOTE_EVENT_LIMIT_EXCEEDED",
            )
        for closure in (item for item in atomic if not item.is_open):
            queue = queues.get(closure.identity)
            if queue:
                opening = queue.popleft()
                open_count -= 1
                if not queue:
                    del queues[closure.identity]
                if tick <= opening.event.absolute_ticks:
                    raise MaestroOrphanClosureSensitivityError(
                        "sensitivity replay produced nonpositive note duration",
                        code="NONPOSITIVE_NOTE_DURATION",
                    )
                continue

            following = _following_matching_onset(closure, by_source_key)
            if following is None:
                raise MaestroOrphanClosureSensitivityError(
                    "orphan closure is not an adjacent same-tick pre-onset of the same identity",
                    code="ORPHAN_NOT_ADJACENT_SAME_TICK_PRE_ONSET",
                )
            if closure.closure_spelling is None:
                raise AssertionError("non-open note event lacks closure spelling")
            dropped.append(
                DroppedRedundantOrphanClosure(
                    port=closure.identity[0],
                    channel=closure.identity[1],
                    pitch=closure.identity[2],
                    closure_spelling=closure.closure_spelling,
                    closure_provenance=ChannelEventProvenance.from_event(
                        closure.event
                    ),
                    following_onset_provenance=ChannelEventProvenance.from_event(
                        following.event
                    ),
                    _factory_token=_FACTORY_TOKEN,
                )
            )
        for opening in (item for item in atomic if item.is_open):
            queues.setdefault(opening.identity, deque()).append(opening)
            open_count += 1
            if open_count > limits.maximum_open_notes:
                raise MaestroOrphanClosureSensitivityError(
                    "sensitivity replay exceeds maximum_open_notes",
                    code="OPEN_NOTE_LIMIT_EXCEEDED",
                )
        cursor = end

    if queues or open_count:
        dangling_count = sum(len(queue) for queue in queues.values())
        raise MaestroOrphanClosureSensitivityError(
            "candidate drop replay still fails: dangling: {} positive note onset(s)"
            .format(dangling_count),
            code="DANGLING_ONSET_AFTER_CANDIDATE_DROP",
        )
    if not dropped:
        raise MaestroOrphanClosureSensitivityError(
            "no qualifying redundant orphan closure was found",
            code="NO_QUALIFYING_REDUNDANT_ORPHAN_CLOSURE",
        )
    dropped.sort(key=lambda item: item.order_key)
    return tuple(dropped)


def _encode_vlq(value: int) -> bytes:
    if not 0 <= value <= _MAX_VLQ_VALUE:
        raise MaestroOrphanClosureSensitivityError(
            "rewritten delta-time exceeds the four-byte VLQ range",
            code="REWRITE_DELTA_VLQ_EXCEEDED",
        )
    parts = [value & 0x7F]
    value >>= 7
    while value:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(parts))


def _encode_event_with_explicit_status(
    event: object,
    *,
    delta_ticks: int,
) -> bytes:
    prefix = _encode_vlq(delta_ticks)
    if isinstance(event, MidiChannelEvent):
        return prefix + bytes((event.status,)) + event.data
    if isinstance(event, MidiMetaEvent):
        return (
            prefix
            + b"\xff"
            + bytes((event.meta_type,))
            + _encode_vlq(len(event.payload))
            + event.payload
        )
    if isinstance(event, MidiSysExEvent):
        return (
            prefix
            + bytes((event.status,))
            + _encode_vlq(len(event.payload))
            + event.payload
        )
    raise TypeError("unsupported raw MIDI event type")


def _transformed_midi(
    midi: MidiFile,
    dropped: Tuple[DroppedRedundantOrphanClosure, ...],
    *,
    rewrite_limits: MidiParseLimits,
) -> MidiFile:
    if type(midi) is not MidiFile:
        raise TypeError("midi must be an exact MidiFile snapshot")
    if type(rewrite_limits) is not MidiParseLimits:
        raise TypeError("rewrite_limits must be an exact MidiParseLimits instance")
    dropped_keys: Set[Tuple[int, int]] = {item.source_key for item in dropped}
    track_payloads: List[bytes] = []
    transformed_event_count = 0

    if len(midi.tracks) > rewrite_limits.maximum_tracks:
        raise MaestroOrphanClosureSensitivityError(
            _PUBLIC_REJECTION_MESSAGES["REWRITE_RESOURCE_LIMIT_EXCEEDED"],
            code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
        )
    if (
        midi.ticks_per_quarter_note
        > rewrite_limits.maximum_ticks_per_quarter_note
    ):
        raise MaestroOrphanClosureSensitivityError(
            _PUBLIC_REJECTION_MESSAGES["REWRITE_RESOURCE_LIMIT_EXCEEDED"],
            code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
        )

    for track in midi.tracks:
        retained = tuple(
            event
            for event in track.events
            if (event.track_index, event.event_index) not in dropped_keys
        )
        if not retained:
            raise MaestroOrphanClosureSensitivityError(
                "rewritten MIDI track unexpectedly became empty",
                code="REWRITE_TRACK_EMPTY",
            )
        if len(retained) > rewrite_limits.maximum_events_per_track:
            raise MaestroOrphanClosureSensitivityError(
                _PUBLIC_REJECTION_MESSAGES["REWRITE_RESOURCE_LIMIT_EXCEEDED"],
                code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
            )
        previous_tick = 0
        encoded_events = []
        encoded_track_bytes = 0
        for event in retained:
            if event.absolute_ticks > rewrite_limits.maximum_absolute_tick:
                raise MaestroOrphanClosureSensitivityError(
                    _PUBLIC_REJECTION_MESSAGES[
                        "REWRITE_RESOURCE_LIMIT_EXCEEDED"
                    ],
                    code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
                )
            if isinstance(event, (MidiMetaEvent, MidiSysExEvent)) and len(
                event.payload
            ) > rewrite_limits.maximum_event_payload_bytes:
                raise MaestroOrphanClosureSensitivityError(
                    _PUBLIC_REJECTION_MESSAGES[
                        "REWRITE_RESOURCE_LIMIT_EXCEEDED"
                    ],
                    code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
                )
            delta = event.absolute_ticks - previous_tick
            encoded = _encode_event_with_explicit_status(
                event,
                delta_ticks=delta,
            )
            encoded_track_bytes += len(encoded)
            if encoded_track_bytes > rewrite_limits.maximum_track_bytes:
                raise MaestroOrphanClosureSensitivityError(
                    _PUBLIC_REJECTION_MESSAGES[
                        "REWRITE_RESOURCE_LIMIT_EXCEEDED"
                    ],
                    code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
                )
            encoded_events.append(encoded)
            previous_tick = event.absolute_ticks
        payload = b"".join(encoded_events)
        track_payloads.append(payload)
        transformed_event_count += len(retained)
        if transformed_event_count > rewrite_limits.maximum_total_events:
            raise MaestroOrphanClosureSensitivityError(
                _PUBLIC_REJECTION_MESSAGES["REWRITE_RESOURCE_LIMIT_EXCEEDED"],
                code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
            )

    header = (
        b"MThd"
        + (6).to_bytes(4, "big")
        + midi.format_type.to_bytes(2, "big")
        + len(track_payloads).to_bytes(2, "big")
        + midi.ticks_per_quarter_note.to_bytes(2, "big")
    )
    rewritten_size = 14 + sum(8 + len(payload) for payload in track_payloads)
    if rewritten_size > rewrite_limits.maximum_file_bytes:
        raise MaestroOrphanClosureSensitivityError(
            _PUBLIC_REJECTION_MESSAGES["REWRITE_RESOURCE_LIMIT_EXCEEDED"],
            code="REWRITE_RESOURCE_LIMIT_EXCEEDED",
        )
    chunks = [
        b"MTrk" + len(payload).to_bytes(4, "big") + payload
        for payload in track_payloads
    ]
    rewritten = header + b"".join(chunks)
    try:
        return parse_midi_bytes(rewritten, limits=rewrite_limits)
    except MidiFormatError:
        raise MaestroOrphanClosureSensitivityError(
            _PUBLIC_REJECTION_MESSAGES["REWRITE_PARSE_FAILURE"],
            code="REWRITE_PARSE_FAILURE",
        ) from None


def _audit_maestro_orphan_closure_sensitivity_snapshot(
    midi: MidiFile,
    *,
    source_split: str,
    limits: MaestroSemanticLimits,
    source_limits: MidiParseLimits,
    rewrite_limits: MidiParseLimits,
) -> MaestroOrphanClosureSensitivityAudit:
    if type(midi) is not MidiFile:
        raise TypeError("midi must be an exact validated MidiFile snapshot")
    split = _source_split(source_split)
    source_fields = {
        "source_split": split,
        "source_midi_sha256": midi.sha256,
        "source_format_type": midi.format_type,
        "source_ticks_per_quarter_note": midi.ticks_per_quarter_note,
        "source_event_count": midi.total_events,
        "source_byte_length": midi.byte_length,
        "source_track_sha256s": tuple(track.sha256 for track in midi.tracks),
        "limits": limits,
        "source_limits": source_limits,
        "rewrite_limits": rewrite_limits,
    }

    try:
        build_maestro_semantics(midi, source_split=split, limits=limits)
    except MaestroSemanticError as error:
        primary_failure_code = error.code
        primary_failure_detail = str(error)
    else:
        rejection_code = "PRIMARY_SEMANTICS_ADMITTED"
        return MaestroOrphanClosureSensitivityAudit(
            **source_fields,
            status="sensitivity_rejected",
            primary_failure_code=None,
            primary_failure_detail=None,
            rejection_code=rejection_code,
            sensitivity_failure_detail=_PUBLIC_REJECTION_MESSAGES[rejection_code],
            admitted_sensitivity=None,
            _factory_token=_FACTORY_TOKEN,
        )

    if primary_failure_code != _PRIMARY_FAILURE_CODE:
        rejection_code = "PRIMARY_SEMANTIC_FAILURE_NOT_ORPHAN_NOTE_CLOSURE"
        return MaestroOrphanClosureSensitivityAudit(
            **source_fields,
            status="sensitivity_rejected",
            primary_failure_code=primary_failure_code,
            primary_failure_detail=primary_failure_detail,
            rejection_code=rejection_code,
            sensitivity_failure_detail=_PUBLIC_REJECTION_MESSAGES[rejection_code],
            admitted_sensitivity=None,
            _factory_token=_FACTORY_TOKEN,
        )

    try:
        dropped = _detect_redundant_orphans(midi, limits=limits)
        transformed = _transformed_midi(
            midi,
            dropped,
            rewrite_limits=rewrite_limits,
        )
    except MaestroOrphanClosureSensitivityError as error:
        if error.code not in _REJECTION_CODES:
            raise AssertionError("unregistered sensitivity rejection code")
        return MaestroOrphanClosureSensitivityAudit(
            **source_fields,
            status="sensitivity_rejected",
            primary_failure_code=primary_failure_code,
            primary_failure_detail=primary_failure_detail,
            rejection_code=error.code,
            sensitivity_failure_detail=str(error),
            admitted_sensitivity=None,
            _factory_token=_FACTORY_TOKEN,
        )

    try:
        sensitivity_semantics = build_maestro_semantics(
            transformed,
            source_split=split,
            limits=limits,
        )
    except MaestroSemanticError as error:
        rejection_code = "TRANSFORMED_SEMANTIC_FAILURE"
        return MaestroOrphanClosureSensitivityAudit(
            **source_fields,
            status="sensitivity_rejected",
            primary_failure_code=primary_failure_code,
            primary_failure_detail=primary_failure_detail,
            rejection_code=rejection_code,
            sensitivity_failure_detail="{}: {}".format(error.code, str(error)),
            admitted_sensitivity=None,
            _factory_token=_FACTORY_TOKEN,
        )
    if transformed.total_events != midi.total_events - len(dropped):
        rejection_code = "REWRITE_EVENT_COUNT_MISMATCH"
        return MaestroOrphanClosureSensitivityAudit(
            **source_fields,
            status="sensitivity_rejected",
            primary_failure_code=primary_failure_code,
            primary_failure_detail=primary_failure_detail,
            rejection_code=rejection_code,
            sensitivity_failure_detail=_PUBLIC_REJECTION_MESSAGES[rejection_code],
            admitted_sensitivity=None,
            _factory_token=_FACTORY_TOKEN,
        )

    admitted = MaestroOrphanClosureSensitivity(
        source_split=split,
        source_midi_sha256=midi.sha256,
        source_format_type=midi.format_type,
        source_ticks_per_quarter_note=midi.ticks_per_quarter_note,
        source_event_count=midi.total_events,
        source_byte_length=midi.byte_length,
        source_track_sha256s=tuple(track.sha256 for track in midi.tracks),
        transformed_midi_sha256=transformed.sha256,
        transformed_event_count=transformed.total_events,
        transformed_byte_length=transformed.byte_length,
        transformed_track_sha256s=tuple(
            track.sha256 for track in transformed.tracks
        ),
        limits=limits,
        source_limits=source_limits,
        rewrite_limits=rewrite_limits,
        dropped_closures=dropped,
        sensitivity_semantics=sensitivity_semantics,
        _factory_token=_FACTORY_TOKEN,
    )
    return MaestroOrphanClosureSensitivityAudit(
        **source_fields,
        status="sensitivity_admitted",
        primary_failure_code=primary_failure_code,
        primary_failure_detail=primary_failure_detail,
        rejection_code=None,
        sensitivity_failure_detail=None,
        admitted_sensitivity=admitted,
        _factory_token=_FACTORY_TOKEN,
    )


def audit_maestro_orphan_closure_sensitivity(
    midi: MidiFile,
    *,
    source_split: str,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
    source_limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
    rewrite_limits: MidiParseLimits = (
        DEFAULT_MAESTRO_ORPHAN_CLOSURE_REWRITE_LIMITS
    ),
) -> MaestroOrphanClosureSensitivityAudit:
    """Return a digest-bearing admitted or rejected sensitivity outcome."""

    split = _source_split(source_split)
    if type(limits) is not MaestroSemanticLimits:
        raise TypeError("limits must be an exact MaestroSemanticLimits instance")
    if type(source_limits) is not MidiParseLimits:
        raise TypeError("source_limits must be an exact MidiParseLimits instance")
    if type(rewrite_limits) is not MidiParseLimits:
        raise TypeError("rewrite_limits must be an exact MidiParseLimits instance")
    snapshot = _exact_source_snapshot(midi, source_limits=source_limits)
    return _audit_maestro_orphan_closure_sensitivity_snapshot(
        snapshot,
        source_split=split,
        limits=limits,
        source_limits=source_limits,
        rewrite_limits=rewrite_limits,
    )


def audit_maestro_orphan_closure_sensitivity_for_inventory_record(
    midi: MidiFile,
    record: MaestroMidiInventory,
    *,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
    source_limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
    rewrite_limits: MidiParseLimits = (
        DEFAULT_MAESTRO_ORPHAN_CLOSURE_REWRITE_LIMITS
    ),
) -> MaestroOrphanClosureSensitivityAudit:
    """Return an audit bound to an exact inventory digest, size, and split."""

    if type(record) is not MaestroMidiInventory:
        raise TypeError("record must be an exact MaestroMidiInventory")
    if type(limits) is not MaestroSemanticLimits:
        raise TypeError("limits must be an exact MaestroSemanticLimits instance")
    if type(source_limits) is not MidiParseLimits:
        raise TypeError("source_limits must be an exact MidiParseLimits instance")
    if type(rewrite_limits) is not MidiParseLimits:
        raise TypeError("rewrite_limits must be an exact MidiParseLimits instance")
    snapshot = _exact_source_snapshot(midi, source_limits=source_limits)
    if snapshot.sha256 != record.sha256:
        raise MaestroOrphanClosureSensitivityError(
            "MIDI digest does not match inventory record",
            code="INVENTORY_DIGEST_MISMATCH",
        )
    if snapshot.byte_length != record.size_bytes:
        raise MaestroOrphanClosureSensitivityError(
            "MIDI byte length does not match inventory record",
            code="INVENTORY_SIZE_MISMATCH",
        )
    return _audit_maestro_orphan_closure_sensitivity_snapshot(
        snapshot,
        source_split=record.source_split,
        limits=limits,
        source_limits=source_limits,
        rewrite_limits=rewrite_limits,
    )


def _raise_rejected_audit(
    audit: MaestroOrphanClosureSensitivityAudit,
) -> None:
    rejection_code = audit.rejection_code
    if rejection_code not in _PUBLIC_REJECTION_MESSAGES:
        raise AssertionError("rejected audit has no sanitized public message")
    raise MaestroOrphanClosureSensitivityError(
        _PUBLIC_REJECTION_MESSAGES[rejection_code],
        code=rejection_code,
    ) from None


def build_maestro_orphan_closure_sensitivity(
    midi: MidiFile,
    *,
    source_split: str,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
    source_limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
    rewrite_limits: MidiParseLimits = (
        DEFAULT_MAESTRO_ORPHAN_CLOSURE_REWRITE_LIMITS
    ),
) -> MaestroOrphanClosureSensitivity:
    """Return the admitted sensitivity or raise a sanitized structured error."""

    audit = audit_maestro_orphan_closure_sensitivity(
        midi,
        source_split=source_split,
        limits=limits,
        source_limits=source_limits,
        rewrite_limits=rewrite_limits,
    )
    if audit.status == "sensitivity_rejected":
        _raise_rejected_audit(audit)
    admitted = audit.admitted_sensitivity
    if admitted is None:
        raise AssertionError("admitted audit lacks its sensitivity")
    return admitted


def build_maestro_orphan_closure_sensitivity_for_inventory_record(
    midi: MidiFile,
    record: MaestroMidiInventory,
    *,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
    source_limits: MidiParseLimits = DEFAULT_MIDI_PARSE_LIMITS,
    rewrite_limits: MidiParseLimits = (
        DEFAULT_MAESTRO_ORPHAN_CLOSURE_REWRITE_LIMITS
    ),
) -> MaestroOrphanClosureSensitivity:
    """Return an admitted inventory-bound sensitivity or a sanitized error."""

    audit = audit_maestro_orphan_closure_sensitivity_for_inventory_record(
        midi,
        record,
        limits=limits,
        source_limits=source_limits,
        rewrite_limits=rewrite_limits,
    )
    if audit.status == "sensitivity_rejected":
        _raise_rejected_audit(audit)
    admitted = audit.admitted_sensitivity
    if admitted is None:
        raise AssertionError("admitted audit lacks its sensitivity")
    return admitted


def replay_maestro_orphan_closure_sensitivity_audit(
    midi: MidiFile,
    expected: MaestroOrphanClosureSensitivityAudit,
) -> MaestroOrphanClosureSensitivityAudit:
    """Recompute an audit from source bytes and require exact manifest equality."""

    if type(expected) is not MaestroOrphanClosureSensitivityAudit:
        raise TypeError("expected must be an exact sensitivity audit")
    replay = audit_maestro_orphan_closure_sensitivity(
        midi,
        source_split=expected.source_split,
        limits=expected.limits,
        source_limits=expected.source_limits,
        rewrite_limits=expected.rewrite_limits,
    )
    if (
        replay.manifest_sha256 != expected.manifest_sha256
        or replay.to_private_json() != expected.to_private_json()
    ):
        raise MaestroOrphanClosureSensitivityError(
            "recomputed sensitivity audit does not match the expected manifest",
            code="REPLAY_MISMATCH",
        )
    return replay


def replay_maestro_orphan_closure_sensitivity_audit_for_inventory_record(
    midi: MidiFile,
    record: MaestroMidiInventory,
    expected: MaestroOrphanClosureSensitivityAudit,
) -> MaestroOrphanClosureSensitivityAudit:
    """Recompute an inventory-bound audit and require exact manifest equality."""

    if type(expected) is not MaestroOrphanClosureSensitivityAudit:
        raise TypeError("expected must be an exact sensitivity audit")
    replay = audit_maestro_orphan_closure_sensitivity_for_inventory_record(
        midi,
        record,
        limits=expected.limits,
        source_limits=expected.source_limits,
        rewrite_limits=expected.rewrite_limits,
    )
    if (
        replay.manifest_sha256 != expected.manifest_sha256
        or replay.to_private_json() != expected.to_private_json()
    ):
        raise MaestroOrphanClosureSensitivityError(
            "recomputed sensitivity audit does not match the expected manifest",
            code="REPLAY_MISMATCH",
        )
    return replay
