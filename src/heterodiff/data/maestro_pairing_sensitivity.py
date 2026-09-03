"""Bounded note-pairing sensitivities for admitted MAESTRO semantics.

The primary semantic adapter remains FIFO.  This module neither mutates that
table nor emits a replacement table.  It binds an independently replayed LIFO
association and a close-at-retrigger *duration* sensitivity to the primary
semantic manifest and the source MIDI digest.

The retrigger convention is deliberately narrow.  For each primary FIFO note,
the candidate trigger is the earliest strictly later atomic tick containing at
least one positive onset of the same ``(port, channel, pitch)`` identity.  Its
effective release is the earlier of the raw FIFO release and that trigger tick.
A raw close tied with a trigger wins, simultaneous onsets do not close one
another, and the complete same-tick trigger group is retained in canonical raw
provenance order.  The raw FIFO close and its exact provenance are never
deleted or reassigned; a shortened release is an inferred audit-only duration.

All constructors are fail-closed, all collections are immutable tuples, and
the supplied :class:`MaestroSemanticLimits` bound both replay and evidence
size.  Official corpus callers must use the inventory-record wrapper so the
split cannot be supplied independently of the verified inventory row.
"""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Mapping, Optional, Tuple

from heterodiff.artifacts.manifest import canonical_json_dumps, sha256_bytes

from .maestro_inventory import MaestroMidiInventory
from .maestro_semantics import (
    DEFAULT_MAESTRO_SEMANTIC_LIMITS,
    ChannelEventProvenance,
    MaestroSemanticLimits,
    MaestroSemanticPiece,
    build_maestro_semantics,
    build_maestro_semantics_for_inventory_record,
)
from .midi_raw import MidiChannelEvent, MidiFile, MidiMetaEvent


__all__ = [
    "MaestroNotePairingSensitivityAudit",
    "MaestroPairingSensitivityError",
    "NotePairingAssignment",
    "RetriggerDurationSensitivity",
    "audit_maestro_note_pairing_sensitivities",
    "build_maestro_note_pairing_sensitivity",
    "build_maestro_note_pairing_sensitivity_for_inventory_record",
]


_SOURCE_SPLITS = frozenset(("train", "validation", "test"))
_SHA256_CHARACTERS = frozenset("0123456789abcdef")
_NOTE_ID_DOMAIN = b"heterodiff-maestro-semantic-note-v1\0"
_MANIFEST_DOMAIN = b"heterodiff-maestro-note-pairing-sensitivity-v1\0"
_MANIFEST_SCHEMA_VERSION = 1


class MaestroPairingSensitivityError(ValueError):
    """Raised when the primary table and raw MIDI cannot be bound exactly."""


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


def _semantic_limits_dict(limits: MaestroSemanticLimits) -> Dict[str, int]:
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


def _stable_note_id(
    source_sha256: str,
    provenance: ChannelEventProvenance,
) -> str:
    if provenance.track_index > 0xFFFFFFFF:
        raise ValueError("onset track_index exceeds the note-ID field")
    if provenance.event_index > 0xFFFFFFFFFFFFFFFF:
        raise ValueError("onset event_index exceeds the note-ID field")
    payload = (
        _NOTE_ID_DOMAIN
        + bytes.fromhex(source_sha256)
        + provenance.track_index.to_bytes(4, "big", signed=False)
        + provenance.event_index.to_bytes(8, "big", signed=False)
    )
    return hashlib.sha256(payload).hexdigest()


def _provenance_key(
    provenance: ChannelEventProvenance,
) -> Tuple[object, ...]:
    return (
        provenance.track_index,
        provenance.event_index,
        provenance.delta_ticks,
        provenance.absolute_tick,
        provenance.track_byte_offset,
        provenance.status,
        provenance.used_running_status,
        provenance.message_type,
        provenance.data,
        provenance.encoded_bytes,
    )


@dataclass(frozen=True)
class NotePairingAssignment:
    """One raw positive onset associated with one raw closure."""

    note_id: str
    port: int
    channel: int
    pitch: int
    onset_provenance: ChannelEventProvenance
    closure_provenance: ChannelEventProvenance
    closure_spelling: str

    def __post_init__(self) -> None:
        _sha256(self.note_id, name="note_id")
        for name in ("port", "channel", "pitch"):
            _plain_int(getattr(self, name), name=name)
        if self.port > 127 or self.channel > 15 or self.pitch > 127:
            raise ValueError("port/channel/pitch is outside the MIDI range")
        if not isinstance(self.onset_provenance, ChannelEventProvenance) or not isinstance(
            self.closure_provenance, ChannelEventProvenance
        ):
            raise TypeError("pair endpoints must be ChannelEventProvenance values")
        onset = self.onset_provenance
        closure = self.closure_provenance
        if (
            onset.message_type != "note_on"
            or (onset.status & 0x0F) != self.channel
            or onset.data[0] != self.pitch
            or onset.data[1] == 0
        ):
            raise ValueError("onset provenance is not the declared positive note_on")
        if self.closure_spelling not in ("note_off", "note_on_velocity_zero"):
            raise ValueError("closure_spelling is not admitted")
        expected_type = (
            "note_off"
            if self.closure_spelling == "note_off"
            else "note_on"
        )
        if (
            closure.message_type != expected_type
            or (closure.status & 0x0F) != self.channel
            or closure.data[0] != self.pitch
        ):
            raise ValueError("closure provenance does not match the declared identity")
        if self.closure_spelling == "note_on_velocity_zero" and closure.data[1] != 0:
            raise ValueError("note_on_velocity_zero must retain velocity zero")
        if closure.absolute_tick <= onset.absolute_tick:
            raise ValueError("pairing assignments require positive raw duration")

    @property
    def identity(self) -> Tuple[int, int, int]:
        return (self.port, self.channel, self.pitch)

    @property
    def onset_tick(self) -> int:
        return self.onset_provenance.absolute_tick

    @property
    def release_tick(self) -> int:
        return self.closure_provenance.absolute_tick

    @property
    def onset_order_key(self) -> Tuple[int, int, int]:
        return (
            self.onset_tick,
            self.onset_provenance.track_index,
            self.onset_provenance.event_index,
        )

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "note_id": self.note_id,
            "identity": {
                "port": self.port,
                "channel": self.channel,
                "pitch": self.pitch,
            },
            "onset_provenance": self.onset_provenance.to_private_dict(),
            "closure_provenance": self.closure_provenance.to_private_dict(),
            "closure_spelling": self.closure_spelling,
        }


@dataclass(frozen=True)
class RetriggerDurationSensitivity:
    """Audit-only effective release attached to an unchanged FIFO raw pair."""

    note_id: str
    raw_fifo_release_tick: int
    next_later_onset_tick: Optional[int]
    trigger_note_ids: Tuple[str, ...]
    effective_release_tick: int
    truncated_by_retrigger: bool

    def __post_init__(self) -> None:
        _sha256(self.note_id, name="note_id")
        _plain_int(
            self.raw_fifo_release_tick,
            name="raw_fifo_release_tick",
        )
        if self.next_later_onset_tick is not None:
            _plain_int(
                self.next_later_onset_tick,
                name="next_later_onset_tick",
            )
        if not isinstance(self.trigger_note_ids, tuple):
            raise TypeError("trigger_note_ids must be a tuple")
        for note_id in self.trigger_note_ids:
            _sha256(note_id, name="trigger note_id")
        if len(set(self.trigger_note_ids)) != len(self.trigger_note_ids):
            raise ValueError("trigger_note_ids must be unique")
        if (self.next_later_onset_tick is None) != (not self.trigger_note_ids):
            raise ValueError("a candidate trigger tick requires a nonempty trigger group")
        _plain_int(self.effective_release_tick, name="effective_release_tick")
        if not isinstance(self.truncated_by_retrigger, bool):
            raise TypeError("truncated_by_retrigger must be a boolean")

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "note_id": self.note_id,
            "raw_fifo_release_tick": self.raw_fifo_release_tick,
            "next_later_onset_tick": self.next_later_onset_tick,
            "trigger_note_ids": list(self.trigger_note_ids),
            "effective_release_tick": self.effective_release_tick,
            "truncated_by_retrigger": self.truncated_by_retrigger,
        }


def _pair_onset_fingerprint(pair: NotePairingAssignment) -> Tuple[object, ...]:
    return pair.identity + _provenance_key(pair.onset_provenance)


def _pair_closure_fingerprint(pair: NotePairingAssignment) -> Tuple[object, ...]:
    return (
        pair.port,
        pair.channel,
        pair.pitch,
        pair.closure_spelling,
    ) + _provenance_key(pair.closure_provenance)


def _validate_pairing_replay(
    pairs: Tuple[NotePairingAssignment, ...],
    *,
    discipline: str,
    limits: MaestroSemanticLimits,
) -> None:
    if discipline not in ("fifo", "lifo"):
        raise AssertionError("unsupported replay discipline")
    if len(pairs) > limits.maximum_note_onsets:
        raise ValueError("pair evidence exceeds maximum_note_onsets")
    if 2 * len(pairs) > limits.maximum_note_events:
        raise ValueError("pair evidence exceeds maximum_note_events")
    if pairs and (
        1
        + max(
            max(
                pair.onset_provenance.track_index,
                pair.closure_provenance.track_index,
            )
            for pair in pairs
        )
        > limits.maximum_tracks
    ):
        raise ValueError("pair evidence exceeds maximum_tracks")

    events = []
    raw_keys = []
    for pair in pairs:
        events.append(
            (
                pair.onset_tick,
                pair.onset_provenance.track_index,
                pair.onset_provenance.event_index,
                True,
                pair,
            )
        )
        events.append(
            (
                pair.release_tick,
                pair.closure_provenance.track_index,
                pair.closure_provenance.event_index,
                False,
                pair,
            )
        )
        raw_keys.extend(
            (
                (
                    pair.onset_provenance.track_index,
                    pair.onset_provenance.event_index,
                ),
                (
                    pair.closure_provenance.track_index,
                    pair.closure_provenance.event_index,
                ),
            )
        )
    if len(set(raw_keys)) != len(raw_keys):
        raise ValueError("a raw note event appears in more than one pair endpoint")
    events.sort(key=lambda item: item[:3])

    open_notes: Dict[
        Tuple[int, int, int],
        Deque[NotePairingAssignment],
    ] = {}
    open_count = 0
    cursor = 0
    while cursor < len(events):
        tick = events[cursor][0]
        end = cursor + 1
        while end < len(events) and events[end][0] == tick:
            end += 1
        atomic = events[cursor:end]
        if len(atomic) > limits.maximum_atomic_note_events:
            raise ValueError("pair evidence exceeds maximum_atomic_note_events")
        for _, _, _, is_open, pair in atomic:
            if is_open:
                continue
            queue = open_notes.get(pair.identity)
            if not queue:
                raise ValueError("pair evidence contains an orphan closure")
            expected = queue.popleft() if discipline == "fifo" else queue.pop()
            if not queue:
                del open_notes[pair.identity]
            open_count -= 1
            if expected.note_id != pair.note_id:
                raise ValueError(
                    "pair evidence does not retain {} association".format(
                        discipline.upper()
                    )
                )
        for _, _, _, is_open, pair in atomic:
            if not is_open:
                continue
            open_notes.setdefault(pair.identity, deque()).append(pair)
            open_count += 1
            if open_count > limits.maximum_open_notes:
                raise ValueError("pair evidence exceeds maximum_open_notes")
        cursor = end
    if open_notes or open_count:
        raise ValueError("pair evidence contains a dangling onset")


def _onset_tick_groups_and_successors(
    pairs: Tuple[NotePairingAssignment, ...],
) -> Tuple[
    Dict[Tuple[int, int, int], Dict[int, Tuple[str, ...]]],
    Dict[Tuple[int, int, int], Dict[int, int]],
]:
    """Index same-tick onset groups and each strictly later successor tick.

    Constructing the successor map once keeps retrigger construction and
    validation linear in the number of FIFO notes. Repeatedly scanning every
    later onset tick for every note is quadratic for long same-pitch passages.
    """

    mutable: Dict[Tuple[int, int, int], Dict[int, List[str]]] = {}
    for pair in pairs:
        mutable.setdefault(pair.identity, {}).setdefault(
            pair.onset_tick,
            [],
        ).append(pair.note_id)
    groups: Dict[Tuple[int, int, int], Dict[int, Tuple[str, ...]]] = {}
    successors: Dict[Tuple[int, int, int], Dict[int, int]] = {}
    for identity, by_tick in mutable.items():
        ticks = tuple(sorted(by_tick))
        groups[identity] = {
            tick: tuple(by_tick[tick])
            for tick in ticks
        }
        successors[identity] = {
            tick: following
            for tick, following in zip(ticks, ticks[1:])
        }
    return groups, successors


@dataclass(frozen=True)
class MaestroNotePairingSensitivityAudit:
    """Immutable FIFO/LIFO/retrigger evidence for one admitted MIDI file."""

    source_split: str
    source_midi_sha256: str
    primary_semantic_manifest_sha256: str
    limits: MaestroSemanticLimits
    fifo_pairs: Tuple[NotePairingAssignment, ...]
    lifo_pairs: Tuple[NotePairingAssignment, ...]
    retrigger_durations: Tuple[RetriggerDurationSensitivity, ...]
    schema_version: int = _MANIFEST_SCHEMA_VERSION
    manifest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _source_split(self.source_split)
        _sha256(self.source_midi_sha256, name="source_midi_sha256")
        _sha256(
            self.primary_semantic_manifest_sha256,
            name="primary_semantic_manifest_sha256",
        )
        _plain_int(self.schema_version, name="schema_version", minimum=1)
        if self.schema_version != _MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported pairing-sensitivity schema_version")
        if not isinstance(self.limits, MaestroSemanticLimits):
            raise TypeError("limits must be a MaestroSemanticLimits instance")
        typed_tuples = (
            ("fifo_pairs", self.fifo_pairs, NotePairingAssignment),
            ("lifo_pairs", self.lifo_pairs, NotePairingAssignment),
            (
                "retrigger_durations",
                self.retrigger_durations,
                RetriggerDurationSensitivity,
            ),
        )
        for name, values, expected in typed_tuples:
            if not isinstance(values, tuple) or any(
                not isinstance(value, expected) for value in values
            ):
                raise TypeError(
                    "{} must be a tuple of {} values".format(name, expected.__name__)
                )

        for name, pairs in (("FIFO", self.fifo_pairs), ("LIFO", self.lifo_pairs)):
            order = tuple(pair.onset_order_key for pair in pairs)
            if order != tuple(sorted(order)) or len(set(order)) != len(order):
                raise ValueError("{} pairs must use unique canonical onset order".format(name))
            note_ids = tuple(pair.note_id for pair in pairs)
            if len(set(note_ids)) != len(note_ids):
                raise ValueError("{} note IDs must be unique".format(name))
            for pair in pairs:
                if pair.note_id != _stable_note_id(
                    self.source_midi_sha256,
                    pair.onset_provenance,
                ):
                    raise ValueError("pair note_id does not match source and onset")

        _validate_pairing_replay(
            self.fifo_pairs,
            discipline="fifo",
            limits=self.limits,
        )
        _validate_pairing_replay(
            self.lifo_pairs,
            discipline="lifo",
            limits=self.limits,
        )

        fifo_by_id = {pair.note_id: pair for pair in self.fifo_pairs}
        lifo_by_id = {pair.note_id: pair for pair in self.lifo_pairs}
        if set(fifo_by_id) != set(lifo_by_id):
            raise ValueError("FIFO and LIFO must contain the same note IDs")
        for note_id, fifo in fifo_by_id.items():
            lifo = lifo_by_id[note_id]
            if _pair_onset_fingerprint(fifo) != _pair_onset_fingerprint(lifo):
                raise ValueError("FIFO and LIFO onset facts must be identical")
        fifo_closures = sorted(_pair_closure_fingerprint(pair) for pair in self.fifo_pairs)
        lifo_closures = sorted(_pair_closure_fingerprint(pair) for pair in self.lifo_pairs)
        if fifo_closures != lifo_closures:
            raise ValueError("FIFO and LIFO must use the same raw closures exactly once")

        retrigger_ids = tuple(item.note_id for item in self.retrigger_durations)
        fifo_ids = tuple(pair.note_id for pair in self.fifo_pairs)
        if retrigger_ids != fifo_ids:
            raise ValueError("retrigger rows must follow complete FIFO onset order")
        onset_groups, successor_ticks = _onset_tick_groups_and_successors(
            self.fifo_pairs
        )

        for item, pair in zip(self.retrigger_durations, self.fifo_pairs):
            if item.raw_fifo_release_tick != pair.release_tick:
                raise ValueError("retrigger row does not retain raw FIFO release")
            by_tick = onset_groups[pair.identity]
            expected_tick = successor_ticks[pair.identity].get(pair.onset_tick)
            expected_group = by_tick[expected_tick] if expected_tick is not None else ()
            expected_effective = (
                min(pair.release_tick, expected_tick)
                if expected_tick is not None
                else pair.release_tick
            )
            expected_truncated = (
                expected_tick is not None and expected_tick < pair.release_tick
            )
            if item.next_later_onset_tick != expected_tick:
                raise ValueError("retrigger row does not use the earliest later atomic tick")
            if item.trigger_note_ids != expected_group:
                raise ValueError("retrigger row does not retain the canonical trigger group")
            if item.effective_release_tick != expected_effective:
                raise ValueError("retrigger effective release is inconsistent")
            if item.truncated_by_retrigger != expected_truncated:
                raise ValueError("retrigger truncation flag is inconsistent")
            if item.effective_release_tick <= pair.onset_tick:
                raise ValueError("retrigger sensitivity produced nonpositive duration")

        private_json = canonical_json_dumps(self._private_payload())
        object.__setattr__(
            self,
            "manifest_sha256",
            sha256_bytes(_MANIFEST_DOMAIN + private_json.encode("utf-8")),
        )

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "gate": "maestro-note-pairing-sensitivity-v1",
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "primary_semantic_manifest_sha256": (
                self.primary_semantic_manifest_sha256
            ),
            "limits": _semantic_limits_dict(self.limits),
            "fifo_pairs": [pair.to_private_dict() for pair in self.fifo_pairs],
            "lifo_pairs": [pair.to_private_dict() for pair in self.lifo_pairs],
            "retrigger_durations": [
                item.to_private_dict() for item in self.retrigger_durations
            ],
        }

    def to_private_dict(self) -> Dict[str, object]:
        """Return a fresh provenance-bearing canonical payload."""

        return self._private_payload()

    def to_private_json(self) -> str:
        return canonical_json_dumps(self._private_payload())

    @property
    def fifo_lifo_changed_pair_count(self) -> int:
        return sum(
            _pair_closure_fingerprint(fifo) != _pair_closure_fingerprint(lifo)
            for fifo, lifo in zip(self.fifo_pairs, self.lifo_pairs)
        )

    @property
    def fifo_lifo_changed_release_tick_count(self) -> int:
        return sum(
            fifo.release_tick != lifo.release_tick
            for fifo, lifo in zip(self.fifo_pairs, self.lifo_pairs)
        )

    @property
    def fifo_lifo_total_absolute_release_tick_difference(self) -> int:
        return sum(
            abs(fifo.release_tick - lifo.release_tick)
            for fifo, lifo in zip(self.fifo_pairs, self.lifo_pairs)
        )

    @property
    def retrigger_truncated_note_count(self) -> int:
        return sum(item.truncated_by_retrigger for item in self.retrigger_durations)

    @property
    def retrigger_candidate_note_count(self) -> int:
        return sum(
            item.next_later_onset_tick is not None
            for item in self.retrigger_durations
        )

    @property
    def retrigger_total_removed_duration_ticks(self) -> int:
        return sum(
            item.raw_fifo_release_tick - item.effective_release_tick
            for item in self.retrigger_durations
        )

    @property
    def raw_close_same_tick_precedence_count(self) -> int:
        return sum(
            item.next_later_onset_tick == item.raw_fifo_release_tick
            for item in self.retrigger_durations
            if item.next_later_onset_tick is not None
        )

    def _simultaneous_open_counts(self) -> Tuple[int, int, int]:
        groups: Dict[Tuple[int, int, int, int], int] = {}
        for pair in self.fifo_pairs:
            key = pair.identity + (pair.onset_tick,)
            groups[key] = groups.get(key, 0) + 1
        sizes = [count for count in groups.values() if count > 1]
        return (len(sizes), sum(sizes), sum(count - 1 for count in sizes))

    @property
    def simultaneous_same_identity_open_group_count(self) -> int:
        return self._simultaneous_open_counts()[0]

    @property
    def simultaneous_same_identity_open_event_count(self) -> int:
        return self._simultaneous_open_counts()[1]

    @property
    def simultaneous_same_identity_open_excess_count(self) -> int:
        return self._simultaneous_open_counts()[2]

    @property
    def comparison_status(self) -> str:
        if self.fifo_lifo_changed_pair_count or self.retrigger_truncated_note_count:
            return "representation_sensitive"
        return "pairing_invariant"

    def public_summary(self) -> Mapping[str, object]:
        """Return aggregate sensitivity evidence without raw event provenance."""

        simultaneous_groups, simultaneous_events, simultaneous_excess = (
            self._simultaneous_open_counts()
        )
        return {
            "schema_version": self.schema_version,
            "gate": "maestro-note-pairing-sensitivity-v1",
            "source_split": self.source_split,
            "source_midi_sha256": self.source_midi_sha256,
            "primary_semantic_manifest_sha256": (
                self.primary_semantic_manifest_sha256
            ),
            "manifest_sha256": self.manifest_sha256,
            "note_count": len(self.fifo_pairs),
            "comparison_status": self.comparison_status,
            "fifo_lifo_changed_pair_count": self.fifo_lifo_changed_pair_count,
            "fifo_lifo_changed_release_tick_count": (
                self.fifo_lifo_changed_release_tick_count
            ),
            "fifo_lifo_total_absolute_release_tick_difference": (
                self.fifo_lifo_total_absolute_release_tick_difference
            ),
            "retrigger_candidate_note_count": self.retrigger_candidate_note_count,
            "retrigger_truncated_note_count": self.retrigger_truncated_note_count,
            "retrigger_total_removed_duration_ticks": (
                self.retrigger_total_removed_duration_ticks
            ),
            "raw_close_same_tick_precedence_count": (
                self.raw_close_same_tick_precedence_count
            ),
            "simultaneous_same_identity_open_group_count": simultaneous_groups,
            "simultaneous_same_identity_open_event_count": simultaneous_events,
            "simultaneous_same_identity_open_excess_count": simultaneous_excess,
            "claim_boundary": {
                "primary_fifo_semantics_mutated": False,
                "lifo_uses_same_raw_events_one_to_one": True,
                "retrigger_reassigns_raw_closures": False,
                "retrigger_shortening_is_inferred_duration_only": True,
                "same_tick_onsets_close_one_another": False,
                "raw_close_wins_same_tick_tie": True,
                "lossy_tensor_emitted": False,
            },
            "privacy": {
                "note_ids_included": False,
                "raw_event_provenance_included": False,
                "source_paths_included": False,
            },
        }


@dataclass(frozen=True)
class _AnnotatedNoteEvent:
    provenance: ChannelEventProvenance
    port: int
    is_open: bool
    closure_spelling: Optional[str]

    @property
    def identity(self) -> Tuple[int, int, int]:
        return (
            self.port,
            self.provenance.status & 0x0F,
            self.provenance.data[0],
        )

    @property
    def order_key(self) -> Tuple[int, int, int]:
        return (
            self.provenance.absolute_tick,
            self.provenance.track_index,
            self.provenance.event_index,
        )


def _annotated_note_events(
    midi: MidiFile,
    *,
    limits: MaestroSemanticLimits,
) -> Tuple[_AnnotatedNoteEvent, ...]:
    note_events: List[_AnnotatedNoteEvent] = []
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
            if len(note_events) >= limits.maximum_note_events:
                raise MaestroPairingSensitivityError(
                    "note events exceed maximum_note_events during sensitivity replay"
                )
            velocity = event.velocity
            if velocity is None:
                raise AssertionError("raw note event lacks a velocity")
            is_open = event.message_type == "note_on" and velocity > 0
            closure_spelling = None
            if event.message_type == "note_off":
                closure_spelling = "note_off"
            elif velocity == 0:
                closure_spelling = "note_on_velocity_zero"
            note_events.append(
                _AnnotatedNoteEvent(
                    provenance=ChannelEventProvenance.from_event(event),
                    port=current_port,
                    is_open=is_open,
                    closure_spelling=closure_spelling,
                )
            )
    opening_count = sum(item.is_open for item in note_events)
    if opening_count > limits.maximum_note_onsets:
        raise MaestroPairingSensitivityError(
            "positive onsets exceed maximum_note_onsets during sensitivity replay"
        )
    return tuple(sorted(note_events, key=lambda item: item.order_key))


def _raw_event_fingerprint(event: _AnnotatedNoteEvent) -> Tuple[object, ...]:
    return (
        event.port,
        event.is_open,
        event.closure_spelling,
    ) + _provenance_key(event.provenance)


def _pair_event_fingerprints(
    pairs: Tuple[NotePairingAssignment, ...],
) -> Tuple[Tuple[object, ...], ...]:
    result = []
    for pair in pairs:
        result.append(
            (pair.port, True, None) + _provenance_key(pair.onset_provenance)
        )
        result.append(
            (pair.port, False, pair.closure_spelling)
            + _provenance_key(pair.closure_provenance)
        )
    return tuple(sorted(result))


def _primary_fifo_pairs(
    primary: MaestroSemanticPiece,
) -> Tuple[NotePairingAssignment, ...]:
    return tuple(
        NotePairingAssignment(
            note_id=note.note_id,
            port=note.port,
            channel=note.channel,
            pitch=note.pitch,
            onset_provenance=note.onset_provenance,
            closure_provenance=note.closure_provenance,
            closure_spelling=note.closure_spelling,
        )
        for note in primary.notes
    )


def _lifo_pairs(
    events: Tuple[_AnnotatedNoteEvent, ...],
    *,
    source_sha256: str,
    limits: MaestroSemanticLimits,
) -> Tuple[NotePairingAssignment, ...]:
    stacks: Dict[Tuple[int, int, int], List[_AnnotatedNoteEvent]] = {}
    pairs: List[NotePairingAssignment] = []
    open_count = 0
    cursor = 0
    while cursor < len(events):
        tick = events[cursor].provenance.absolute_tick
        end = cursor + 1
        while end < len(events) and events[end].provenance.absolute_tick == tick:
            end += 1
        atomic = events[cursor:end]
        if len(atomic) > limits.maximum_atomic_note_events:
            raise MaestroPairingSensitivityError(
                "same-tick note events exceed maximum_atomic_note_events during LIFO replay"
            )
        for close in (item for item in atomic if not item.is_open):
            stack = stacks.get(close.identity)
            if not stack:
                raise MaestroPairingSensitivityError(
                    "LIFO replay found an orphan closure at tick {}".format(tick)
                )
            opening = stack.pop()
            if not stack:
                del stacks[close.identity]
            open_count -= 1
            if tick <= opening.provenance.absolute_tick:
                raise MaestroPairingSensitivityError(
                    "LIFO replay produced nonpositive raw duration"
                )
            if close.closure_spelling is None:
                raise AssertionError("closure event lacks a spelling")
            pairs.append(
                NotePairingAssignment(
                    note_id=_stable_note_id(source_sha256, opening.provenance),
                    port=opening.port,
                    channel=opening.identity[1],
                    pitch=opening.identity[2],
                    onset_provenance=opening.provenance,
                    closure_provenance=close.provenance,
                    closure_spelling=close.closure_spelling,
                )
            )
        for opening in (item for item in atomic if item.is_open):
            stacks.setdefault(opening.identity, []).append(opening)
            open_count += 1
            if open_count > limits.maximum_open_notes:
                raise MaestroPairingSensitivityError(
                    "LIFO replay exceeds maximum_open_notes"
                )
        cursor = end
    if stacks or open_count:
        raise MaestroPairingSensitivityError("LIFO replay found dangling onsets")
    pairs.sort(key=lambda pair: pair.onset_order_key)
    return tuple(pairs)


def _retrigger_durations(
    fifo_pairs: Tuple[NotePairingAssignment, ...],
) -> Tuple[RetriggerDurationSensitivity, ...]:
    groups, successor_ticks = _onset_tick_groups_and_successors(fifo_pairs)
    rows = []
    for pair in fifo_pairs:
        by_tick = groups[pair.identity]
        trigger_tick = successor_ticks[pair.identity].get(pair.onset_tick)
        trigger_ids = by_tick[trigger_tick] if trigger_tick is not None else ()
        effective = (
            min(pair.release_tick, trigger_tick)
            if trigger_tick is not None
            else pair.release_tick
        )
        rows.append(
            RetriggerDurationSensitivity(
                note_id=pair.note_id,
                raw_fifo_release_tick=pair.release_tick,
                next_later_onset_tick=trigger_tick,
                trigger_note_ids=trigger_ids,
                effective_release_tick=effective,
                truncated_by_retrigger=(
                    trigger_tick is not None and trigger_tick < pair.release_tick
                ),
            )
        )
    return tuple(rows)


def audit_maestro_note_pairing_sensitivities(
    midi: MidiFile,
    primary: MaestroSemanticPiece,
    *,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
) -> MaestroNotePairingSensitivityAudit:
    """Audit a prebuilt primary FIFO table without changing it.

    This entry point is useful when a sequential caller already holds the
    semantic piece.  It verifies complete raw note-event identity before
    producing any sensitivity evidence.  Official data should reach it only
    through :func:`build_maestro_note_pairing_sensitivity_for_inventory_record`.
    """

    if not isinstance(midi, MidiFile):
        raise TypeError("midi must be a MidiFile")
    if not isinstance(primary, MaestroSemanticPiece):
        raise TypeError("primary must be a MaestroSemanticPiece")
    if not isinstance(limits, MaestroSemanticLimits):
        raise TypeError("limits must be a MaestroSemanticLimits instance")
    # A prebuilt primary may have been admitted under a looser profile.  The
    # sensitivity audit records the profile supplied here, so every raw and
    # retained semantic collection governed by that profile must be checked
    # again before any replay or evidence allocation.
    if midi.track_count > limits.maximum_tracks:
        raise MaestroPairingSensitivityError(
            "track count exceeds maximum_tracks during sensitivity replay"
        )
    if midi.total_events > limits.maximum_total_events:
        raise MaestroPairingSensitivityError(
            "event count exceeds maximum_total_events during sensitivity replay"
        )
    bounded_primary_collections = (
        (
            primary.tempo_map.explicit_event_count,
            limits.maximum_tempo_events,
            "tempo events exceed maximum_tempo_events during sensitivity replay",
        ),
        (
            len(primary.tempo_map.points),
            limits.maximum_tempo_points,
            "tempo points exceed maximum_tempo_points during sensitivity replay",
        ),
        (
            len(primary.controllers),
            limits.maximum_control_changes,
            "control changes exceed maximum_control_changes during sensitivity replay",
        ),
        (
            len(primary.midi_ports),
            limits.maximum_midi_port_events,
            "MIDI Port events exceed maximum_midi_port_events during sensitivity replay",
        ),
        (
            len(primary.time_signatures),
            limits.maximum_time_signatures,
            "time signatures exceed maximum_time_signatures during sensitivity replay",
        ),
    )
    for observed, maximum, message in bounded_primary_collections:
        if observed > maximum:
            raise MaestroPairingSensitivityError(message)
    if primary.source_midi_sha256 != midi.sha256:
        raise MaestroPairingSensitivityError(
            "primary semantic digest does not match the raw MIDI"
        )
    if primary.format_type != midi.format_type:
        raise MaestroPairingSensitivityError(
            "primary semantic format does not match the raw MIDI"
        )
    if primary.ticks_per_quarter_note != midi.ticks_per_quarter_note:
        raise MaestroPairingSensitivityError(
            "primary semantic PPQN does not match the raw MIDI"
        )

    events = _annotated_note_events(midi, limits=limits)
    fifo_pairs = _primary_fifo_pairs(primary)
    raw_fingerprints = tuple(sorted(_raw_event_fingerprint(item) for item in events))
    if raw_fingerprints != _pair_event_fingerprints(fifo_pairs):
        raise MaestroPairingSensitivityError(
            "primary FIFO table does not retain every raw note event exactly once"
        )
    lifo_pairs = _lifo_pairs(
        events,
        source_sha256=midi.sha256,
        limits=limits,
    )
    return MaestroNotePairingSensitivityAudit(
        source_split=primary.source_split,
        source_midi_sha256=midi.sha256,
        primary_semantic_manifest_sha256=primary.manifest_sha256,
        limits=limits,
        fifo_pairs=fifo_pairs,
        lifo_pairs=lifo_pairs,
        retrigger_durations=_retrigger_durations(fifo_pairs),
    )


def build_maestro_note_pairing_sensitivity(
    midi: MidiFile,
    *,
    source_split: str,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
) -> MaestroNotePairingSensitivityAudit:
    """Build primary FIFO semantics and its sensitivities for local fixtures."""

    primary = build_maestro_semantics(
        midi,
        source_split=source_split,
        limits=limits,
    )
    return audit_maestro_note_pairing_sensitivities(
        midi,
        primary,
        limits=limits,
    )


def build_maestro_note_pairing_sensitivity_for_inventory_record(
    midi: MidiFile,
    record: MaestroMidiInventory,
    *,
    limits: MaestroSemanticLimits = DEFAULT_MAESTRO_SEMANTIC_LIMITS,
) -> MaestroNotePairingSensitivityAudit:
    """Bind an official sensitivity audit to inventory digest, size, and split."""

    primary = build_maestro_semantics_for_inventory_record(
        midi,
        record,
        limits=limits,
    )
    return audit_maestro_note_pairing_sensitivities(
        midi,
        primary,
        limits=limits,
    )
