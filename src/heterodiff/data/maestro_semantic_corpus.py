"""Deterministic full-corpus semantic census for verified MAESTRO v3 MIDI.

This is a census and a fail-closed gate, not a tensor adapter.  It joins an
exact :class:`MaestroArchiveInventory` to its oracle-checked
:class:`MaestroRawMidiAudit`, reopens every file under the audited raw parser
limits, and applies the frozen semantic policy one piece at a time.  A
``MaestroSemanticError`` is retained as structured HOLD evidence so one
policy failure cannot silently remove a piece.  Any byte-identity, raw-audit,
filesystem-mutation, or unexpected implementation failure aborts the whole
census.

Every semantic pass is immediately replayed through the immutable pairing
sensitivity sidecar while the parsed MIDI and primary FIFO piece are still in
memory.  LIFO and retrigger results remain diagnostics: they cannot replace
the primary policy or affect ``PRIMARY_PASS``.  A semantic pass without a
digest-bound, complete sidecar is structurally impossible in this schema.

Every primary ``ORPHAN_NOTE_CLOSURE`` failure is likewise replayed through
the narrow, inventory-bound orphan-closure sensitivity.  Its admitted or
rejected status is separately committed and aggregated, but the source row
remains a primary semantic failure in either case.

The per-file evidence is deliberately compact: it retains a private logical
path and aggregate semantic facts, but no note rows or note IDs.  The public
summary contains split aggregates and canonical digests only.  In particular,
this module never emits a lossy grid tensor and never labels its output
training-ready.
"""

from __future__ import annotations

import os
import stat
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

from heterodiff.artifacts.manifest import canonical_json_dumps, sha256_bytes

from .maestro_inventory import (
    MAESTRO_V3_EXPECTED_MIDI_FILES,
    MaestroArchiveInventory,
    MaestroMidiInventory,
)
from .maestro_orphan_closure_sensitivity import (
    MaestroOrphanClosureSensitivityAudit,
    MaestroOrphanClosureSensitivityError,
    audit_maestro_orphan_closure_sensitivity_for_inventory_record,
)
from .maestro_pairing_sensitivity import (
    MaestroNotePairingSensitivityAudit,
    MaestroPairingSensitivityError,
    audit_maestro_note_pairing_sensitivities,
)
from .maestro_raw_audit import (
    PINNED_MIDO_ORACLE_VERSION,
    MaestroRawMidiAudit,
    MaestroRawMidiFileEvidence,
)
from .maestro_semantics import (
    MaestroSemanticError,
    MaestroSemanticLimits,
    MaestroSemanticPiece,
    build_maestro_semantics_for_inventory_record,
)
from .midi_raw import (
    MidiChannelEvent,
    MidiFile,
    MidiFormatError,
    MidiMetaEvent,
    MidiSysExEvent,
    load_midi_file,
)


PathLike = Union[str, os.PathLike]

MAESTRO_WINDOW_LENGTH = 256
MAESTRO_SEMANTIC_CORPUS_SCHEMA_VERSION = 3
MAESTRO_SEMANTIC_CORPUS_GATE = "full-corpus-midi-clock-semantic-census-v3"
MAESTRO_SEMANTIC_PUBLIC_DIGEST_DOMAIN = (
    b"heterodiff-maestro-semantic-corpus-public-v3\0"
)
MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN = (
    b"heterodiff-maestro-orphan-closure-sensitivity-audit-manifests-v1\0"
)
MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_SPLIT_DIGEST_DOMAIN = (
    b"heterodiff-maestro-orphan-closure-sensitivity-audit-split-v1\0"
)

_SOURCE_SPLITS = ("test", "train", "validation")
_SOURCE_SPLIT_SET = frozenset(_SOURCE_SPLITS)
_PEDAL_CONTROLLERS = frozenset((64, 66, 67))
_SEMANTIC_FAILURE_CODES = frozenset(
    (
        "CONFLICTING_TEMPO_VALUES",
        "DANGLING_NOTE_ONSETS",
        "FORMAT_NOT_0_OR_1",
        "LIMIT_ATOMIC_NOTE_EVENTS",
        "LIMIT_CONTROL_CHANGES",
        "LIMIT_MAXIMUM_TOTAL_EVENTS",
        "LIMIT_MAXIMUM_TRACKS",
        "LIMIT_MIDI_PORT_EVENTS",
        "LIMIT_NOTE_EVENTS",
        "LIMIT_NOTE_ONSETS",
        "LIMIT_OPEN_NOTES",
        "LIMIT_TEMPO_EVENTS",
        "LIMIT_TEMPO_POINTS",
        "LIMIT_TIME_SIGNATURES",
        "NONPOSITIVE_NOTE_DURATION",
        "NONPOSITIVE_TEMPO",
        "ORPHAN_NOTE_CLOSURE",
        "PPQN_NOT_DIVISIBLE_BY_FOUR",
    )
)
_SHA256_CHARACTERS = frozenset("0123456789abcdef")
_PRIVATE_DIGEST_DOMAIN = b"heterodiff-maestro-semantic-corpus-private-v3\0"
_SEMANTIC_DIGEST_DOMAIN = b"heterodiff-maestro-semantic-manifests-v1\0"
_SPLIT_DIGEST_DOMAIN = b"heterodiff-maestro-semantic-split-v1\0"
_PAIRING_DIGEST_DOMAIN = b"heterodiff-maestro-pairing-manifests-v1\0"
_PAIRING_SPLIT_DIGEST_DOMAIN = b"heterodiff-maestro-pairing-split-v1\0"
_ORPHAN_SENSITIVITY_DIGEST_DOMAIN = (
    MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN
)
_ORPHAN_SENSITIVITY_SPLIT_DIGEST_DOMAIN = (
    MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_SPLIT_DIGEST_DOMAIN
)
_PUBLIC_DIGEST_DOMAIN = MAESTRO_SEMANTIC_PUBLIC_DIGEST_DOMAIN
_SCHEMA_VERSION = MAESTRO_SEMANTIC_CORPUS_SCHEMA_VERSION


class MaestroSemanticCorpusAuditError(ValueError):
    """Raised when corpus or raw evidence fails outside semantic policy."""


def _plain_nonnegative_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{} must be an integer".format(name))
    if value < 0:
        raise ValueError("{} must be nonnegative".format(name))
    return value


def _sha256(value: object, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _SHA256_CHARACTERS for character in value)
    ):
        raise ValueError("{} must be a lowercase SHA-256 digest".format(name))
    return value


def _logical_midi_path(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("midi_path must be a string")
    parsed = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or value.startswith("/")
        or parsed.is_absolute()
        or str(parsed) != value
        or parsed.suffix != ".midi"
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise ValueError("midi_path must be a canonical relative .midi path")
    return value


def _named_counts(
    value: object,
    *,
    name: str,
    allowed_keys: Optional[frozenset] = None,
) -> Tuple[Tuple[str, int], ...]:
    if not isinstance(value, tuple):
        raise TypeError("{} must be a tuple".format(name))
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("{} entries must be pairs".format(name))
        key, count = item
        if not isinstance(key, str) or not key:
            raise TypeError("{} keys must be nonempty strings".format(name))
        if allowed_keys is not None and key not in allowed_keys:
            raise ValueError("{} contains an unsupported key".format(name))
        _plain_nonnegative_int(count, name="{} count".format(name))
        if count == 0:
            raise ValueError("{} must omit zero counts".format(name))
        result.append((key, count))
    if tuple(result) != tuple(sorted(result)) or len({item[0] for item in result}) != len(
        result
    ):
        raise ValueError("{} must be sorted and unique".format(name))
    return tuple(result)


def _pedal_counts(value: object) -> Tuple[Tuple[int, int], ...]:
    if not isinstance(value, tuple):
        raise TypeError("pedal_controller_counts must be a tuple")
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("pedal_controller_counts entries must be pairs")
        controller, count = item
        if controller not in _PEDAL_CONTROLLERS:
            raise ValueError("pedal controller keys must be 64, 66, or 67")
        _plain_nonnegative_int(count, name="pedal controller count")
        if count == 0:
            raise ValueError("pedal_controller_counts must omit zero counts")
        result.append((controller, count))
    if tuple(result) != tuple(sorted(result)) or len({item[0] for item in result}) != len(
        result
    ):
        raise ValueError("pedal_controller_counts must be sorted and unique")
    return tuple(result)


def _pitch_collision_counts(
    value: object,
) -> Tuple[Tuple[int, int, int, int], ...]:
    """Validate ``(pitch, cells, events, excess_events)`` aggregates."""

    if not isinstance(value, tuple):
        raise TypeError("projection_collision_by_pitch must be a tuple")
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 4:
            raise TypeError("pitch-collision entries must be four-tuples")
        pitch, cells, events, excess = item
        if isinstance(pitch, bool) or not isinstance(pitch, int) or not 0 <= pitch <= 127:
            raise ValueError("collision pitch must be in 0..127")
        for name, count in (
            ("collision cells", cells),
            ("collision events", events),
            ("collision excess events", excess),
        ):
            _plain_nonnegative_int(count, name=name)
        if cells == 0:
            raise ValueError("pitch-collision entries must omit zero cells")
        if events < 2 * cells or excess != events - cells:
            raise ValueError("pitch-collision counts are arithmetically inconsistent")
        result.append((pitch, cells, events, excess))
    if tuple(result) != tuple(sorted(result)) or len({item[0] for item in result}) != len(
        result
    ):
        raise ValueError("pitch-collision entries must be sorted and unique")
    return tuple(result)


def _positive_histogram(
    value: object, *, name: str
) -> Tuple[Tuple[int, int], ...]:
    if not isinstance(value, tuple):
        raise TypeError("{} must be a tuple".format(name))
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("{} entries must be pairs".format(name))
        key, count = item
        _plain_nonnegative_int(key, name="{} key".format(name))
        _plain_nonnegative_int(count, name="{} count".format(name))
        if key == 0 or count == 0:
            raise ValueError("{} must omit zero keys and counts".format(name))
        result.append((key, count))
    if tuple(result) != tuple(sorted(result)) or len({item[0] for item in result}) != len(
        result
    ):
        raise ValueError("{} must be sorted and unique".format(name))
    return tuple(result)


def _collision_multiplicity_histogram(
    value: object,
) -> Tuple[Tuple[int, int], ...]:
    """Validate ``(events_in_cell, cell_count)`` collision multiplicities."""

    result = _positive_histogram(
        value, name="projection_collision_multiplicity_histogram"
    )
    if result and result[0][0] < 2:
        raise ValueError("collision multiplicities must be at least two")
    return result


def _largest_collision_cell_capacity(
    histogram: Tuple[Tuple[int, int], ...], cell_limit: int
) -> int:
    """Return the event capacity of the largest ``cell_limit`` cells."""

    remaining = cell_limit
    capacity = 0
    for multiplicity, count in reversed(histogram):
        taken = min(remaining, count)
        capacity += multiplicity * taken
        remaining -= taken
        if remaining == 0:
            break
    return capacity


def _collision_pitch_multiplicity_histogram(
    value: object,
) -> Tuple[Tuple[int, int, int], ...]:
    """Validate ``(pitch, events_in_cell, cell_count)`` joint counts."""

    if not isinstance(value, tuple):
        raise TypeError("projection_collision_pitch_multiplicity_histogram must be a tuple")
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 3:
            raise TypeError("pitch-multiplicity entries must be triples")
        pitch, multiplicity, count = item
        if isinstance(pitch, bool) or not isinstance(pitch, int) or not 0 <= pitch <= 127:
            raise ValueError("pitch-multiplicity pitch must be in 0..127")
        _plain_nonnegative_int(multiplicity, name="collision multiplicity")
        _plain_nonnegative_int(count, name="pitch-multiplicity cell count")
        if multiplicity < 2 or count == 0:
            raise ValueError(
                "pitch-multiplicity entries require multiplicity at least two and positive counts"
            )
        result.append((pitch, multiplicity, count))
    if tuple(result) != tuple(sorted(result)) or len(
        {(pitch, multiplicity) for pitch, multiplicity, _ in result}
    ) != len(result):
        raise ValueError("pitch-multiplicity entries must be sorted and unique")
    return tuple(result)


def _collision_piece_profile_histogram(
    value: object,
) -> Tuple[Tuple[Tuple[Tuple[int, int, int], ...], int, int], ...]:
    """Validate per-piece multiplicity signatures and collision windows.

    Each entry is ``(pitch_multiplicity_histogram, collision_windows,
    piece_count)``.  Retaining the full per-piece joint signature is necessary:
    scalar cell/event/excess profiles, and even pitch-free multiplicity
    profiles, do not prove that aggregate pitch and multiplicity margins can
    actually be partitioned across the claimed pieces.
    """

    if not isinstance(value, tuple):
        raise TypeError("projection_collision_piece_profile_histogram must be a tuple")
    result = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 3:
            raise TypeError("collision piece-profile entries must be triples")
        pitch_multiplicities, collision_windows, piece_count = item
        pitch_multiplicities = _collision_pitch_multiplicity_histogram(
            pitch_multiplicities
        )
        for name, count in (
            ("profile collision windows", collision_windows),
            ("profile piece count", piece_count),
        ):
            _plain_nonnegative_int(count, name=name)
        cells = sum(count for _, _, count in pitch_multiplicities)
        if cells == 0 or piece_count == 0:
            raise ValueError(
                "collision piece profiles must retain a nonempty multiplicity "
                "signature and positive piece count"
            )
        if not 1 <= collision_windows <= cells:
            raise ValueError("collision piece-profile windows must lie in 1..cells")
        result.append((pitch_multiplicities, collision_windows, piece_count))
    if tuple(result) != tuple(sorted(result)) or len(
        {
            (pitch_multiplicities, collision_windows)
            for pitch_multiplicities, collision_windows, _ in result
        }
    ) != len(result):
        raise ValueError("collision piece profiles must be sorted and unique")
    return tuple(result)


def _pitch_support_is_feasible(
    *,
    note_count: int,
    pitch_minimum: int,
    pitch_maximum: int,
    out_of_88_key_note_count: int,
    projection_collision_by_pitch: Tuple[Tuple[int, int, int, int], ...],
) -> bool:
    """Check existence of a pitch histogram consistent with retained margins."""

    collision_events = {
        pitch: events for pitch, _, events, _ in projection_collision_by_pitch
    }
    if any(
        pitch < pitch_minimum or pitch > pitch_maximum
        for pitch in collision_events
    ):
        return False
    collision_total = sum(collision_events.values())
    if collision_total > note_count:
        return False
    collision_outside = sum(
        count
        for pitch, count in collision_events.items()
        if pitch < 21 or pitch > 108
    )
    collision_inside = collision_total - collision_outside
    target_inside = note_count - out_of_88_key_note_count
    if (
        collision_outside > out_of_88_key_note_count
        or collision_inside > target_inside
    ):
        return False

    remaining = note_count - collision_total
    missing_extrema = {
        pitch
        for pitch in (pitch_minimum, pitch_maximum)
        if collision_events.get(pitch, 0) == 0
    }
    if len(missing_extrema) > remaining:
        return False
    extrema_outside = sum(pitch < 21 or pitch > 108 for pitch in missing_extrema)
    extrema_inside = len(missing_extrema) - extrema_outside
    needed_outside = (
        out_of_88_key_note_count - collision_outside - extrema_outside
    )
    needed_inside = target_inside - collision_inside - extrema_inside
    if needed_outside < 0 or needed_inside < 0:
        return False
    if needed_outside + needed_inside != remaining - len(missing_extrema):
        return False
    inside_available = max(pitch_minimum, 21) <= min(pitch_maximum, 108)
    outside_available = pitch_minimum <= min(pitch_maximum, 20) or max(
        pitch_minimum, 109
    ) <= pitch_maximum
    if needed_inside and not inside_available:
        return False
    if needed_outside and not outside_available:
        return False
    return True


def _streams(value: object) -> Tuple[Tuple[int, int], ...]:
    if not isinstance(value, tuple):
        raise TypeError("note_producing_streams must be a tuple")
    result = []
    for item in value:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or any(isinstance(part, bool) or not isinstance(part, int) for part in item)
            or not 0 <= item[0] <= 127
            or not 0 <= item[1] <= 15
        ):
            raise ValueError("note-producing streams must be (port, channel) pairs")
        result.append(item)
    if tuple(result) != tuple(sorted(set(result))):
        raise ValueError("note_producing_streams must be sorted and unique")
    return tuple(result)


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


@dataclass(frozen=True)
class MaestroSemanticFileEvidence:
    """Compact private evidence for one inventory row; never contains note IDs."""

    metadata_row_number: int
    midi_path: str
    source_split: str
    sha256: str
    size_bytes: int
    status: str
    failure_code: Optional[str] = None
    failure_detail: Optional[str] = None
    failure_detail_sha256: Optional[str] = None
    semantic_manifest_sha256: Optional[str] = None
    pairing_sensitivity_manifest_sha256: Optional[str] = None
    pairing_comparison_status: Optional[str] = None
    orphan_closure_sensitivity_status: Optional[str] = None
    orphan_closure_sensitivity_rejection_code: Optional[str] = None
    orphan_closure_sensitivity_failure_detail_sha256: Optional[str] = None
    orphan_closure_sensitivity_manifest_sha256: Optional[str] = None
    note_count: int = 0
    pairing_note_count: int = 0
    fifo_lifo_changed_pair_count: int = 0
    fifo_lifo_changed_release_tick_count: int = 0
    fifo_lifo_total_absolute_release_tick_difference: int = 0
    retrigger_candidate_note_count: int = 0
    retrigger_truncated_note_count: int = 0
    retrigger_total_removed_duration_ticks: int = 0
    raw_close_same_tick_precedence_count: int = 0
    simultaneous_same_identity_open_group_count: int = 0
    simultaneous_same_identity_open_event_count: int = 0
    simultaneous_same_identity_open_excess_count: int = 0
    closure_spelling_counts: Tuple[Tuple[str, int], ...] = ()
    controller_count: int = 0
    pedal_controller_counts: Tuple[Tuple[int, int], ...] = ()
    tempo_point_count: int = 0
    explicit_tempo_event_count: int = 0
    midi_port_event_count: int = 0
    time_signature_count: int = 0
    pitch_minimum: Optional[int] = None
    pitch_maximum: Optional[int] = None
    out_of_88_key_note_count: int = 0
    note_producing_streams: Tuple[Tuple[int, int], ...] = ()
    projection_collision_cell_count: int = 0
    projection_collision_event_count: int = 0
    projection_collision_excess_event_count: int = 0
    projection_collision_by_pitch: Tuple[Tuple[int, int, int, int], ...] = ()
    projection_collision_pitch_multiplicity_histogram: Tuple[
        Tuple[int, int, int], ...
    ] = ()
    projection_collision_multiplicity_histogram: Tuple[Tuple[int, int], ...] = ()
    maximum_projection_collision_cell_multiplicity: int = 0
    projection_collision_window_count: int = 0
    maximum_grid_index: Optional[int] = None
    window_count: int = 0
    tail_retained_window_count: int = 0
    window_ineligible: bool = False
    projection_admitted: bool = False

    def __post_init__(self) -> None:
        if (
            isinstance(self.metadata_row_number, bool)
            or not isinstance(self.metadata_row_number, int)
            or self.metadata_row_number < 2
        ):
            raise ValueError("metadata_row_number must be an integer of at least 2")
        object.__setattr__(self, "midi_path", _logical_midi_path(self.midi_path))
        if self.source_split not in _SOURCE_SPLIT_SET:
            raise ValueError("source_split must retain an official MAESTRO label")
        _sha256(self.sha256, name="sha256")
        _plain_nonnegative_int(self.size_bytes, name="size_bytes")
        if self.size_bytes == 0:
            raise ValueError("size_bytes must be positive")
        if self.status not in ("pass", "semantic_failure"):
            raise ValueError("status must be pass or semantic_failure")
        for name in (
            "note_count",
            "pairing_note_count",
            "fifo_lifo_changed_pair_count",
            "fifo_lifo_changed_release_tick_count",
            "fifo_lifo_total_absolute_release_tick_difference",
            "retrigger_candidate_note_count",
            "retrigger_truncated_note_count",
            "retrigger_total_removed_duration_ticks",
            "raw_close_same_tick_precedence_count",
            "simultaneous_same_identity_open_group_count",
            "simultaneous_same_identity_open_event_count",
            "simultaneous_same_identity_open_excess_count",
            "controller_count",
            "tempo_point_count",
            "explicit_tempo_event_count",
            "midi_port_event_count",
            "time_signature_count",
            "out_of_88_key_note_count",
            "projection_collision_cell_count",
            "projection_collision_event_count",
            "projection_collision_excess_event_count",
            "maximum_projection_collision_cell_multiplicity",
            "projection_collision_window_count",
            "window_count",
            "tail_retained_window_count",
        ):
            _plain_nonnegative_int(getattr(self, name), name=name)
        object.__setattr__(
            self,
            "closure_spelling_counts",
            _named_counts(
                self.closure_spelling_counts,
                name="closure_spelling_counts",
                allowed_keys=frozenset(("note_off", "note_on_velocity_zero")),
            ),
        )
        object.__setattr__(
            self, "pedal_controller_counts", _pedal_counts(self.pedal_controller_counts)
        )
        object.__setattr__(
            self, "note_producing_streams", _streams(self.note_producing_streams)
        )
        object.__setattr__(
            self,
            "projection_collision_by_pitch",
            _pitch_collision_counts(self.projection_collision_by_pitch),
        )
        object.__setattr__(
            self,
            "projection_collision_pitch_multiplicity_histogram",
            _collision_pitch_multiplicity_histogram(
                self.projection_collision_pitch_multiplicity_histogram
            ),
        )
        object.__setattr__(
            self,
            "projection_collision_multiplicity_histogram",
            _collision_multiplicity_histogram(
                self.projection_collision_multiplicity_histogram
            ),
        )
        if not isinstance(self.window_ineligible, bool) or not isinstance(
            self.projection_admitted, bool
        ):
            raise TypeError("window/projection flags must be booleans")

        sensitivity_values = (
            self.orphan_closure_sensitivity_status,
            self.orphan_closure_sensitivity_rejection_code,
            self.orphan_closure_sensitivity_failure_detail_sha256,
            self.orphan_closure_sensitivity_manifest_sha256,
        )
        if self.orphan_closure_sensitivity_status is None:
            if any(value is not None for value in sensitivity_values[1:]):
                raise ValueError(
                    "an absent orphan-closure sensitivity cannot contain evidence"
                )
        elif self.orphan_closure_sensitivity_status == "sensitivity_admitted":
            if any(value is not None for value in sensitivity_values[1:3]):
                raise ValueError(
                    "an admitted orphan-closure sensitivity cannot claim rejection evidence"
                )
            _sha256(
                self.orphan_closure_sensitivity_manifest_sha256,
                name="orphan_closure_sensitivity_manifest_sha256",
            )
        elif self.orphan_closure_sensitivity_status == "sensitivity_rejected":
            if (
                not isinstance(
                    self.orphan_closure_sensitivity_rejection_code, str
                )
                or not self.orphan_closure_sensitivity_rejection_code
            ):
                raise ValueError(
                    "a rejected orphan-closure sensitivity requires a rejection code"
                )
            _sha256(
                self.orphan_closure_sensitivity_failure_detail_sha256,
                name="orphan_closure_sensitivity_failure_detail_sha256",
            )
            _sha256(
                self.orphan_closure_sensitivity_manifest_sha256,
                name="orphan_closure_sensitivity_manifest_sha256",
            )
        else:
            raise ValueError("unsupported orphan-closure sensitivity status")

        if self.status == "semantic_failure":
            if not isinstance(self.failure_code, str) or not self.failure_code:
                raise ValueError("a semantic failure requires a failure_code")
            if any(
                not (
                    character == "_"
                    or character.isupper()
                    or character.isdigit()
                )
                for character in self.failure_code
            ):
                raise ValueError("failure_code must use uppercase snake case")
            if self.failure_code not in _SEMANTIC_FAILURE_CODES:
                raise ValueError("unsupported failure_code")
            if not isinstance(self.failure_detail, str) or not self.failure_detail:
                raise ValueError("a semantic failure requires private failure_detail")
            _sha256(self.failure_detail_sha256, name="failure_detail_sha256")
            expected = sha256_bytes(self.failure_detail.encode("utf-8"))
            if self.failure_detail_sha256 != expected:
                raise ValueError("failure_detail_sha256 does not match failure_detail")
            if self.failure_code == "ORPHAN_NOTE_CLOSURE":
                if self.orphan_closure_sensitivity_status is None:
                    raise ValueError(
                        "an orphan-note-closure failure requires its named sensitivity audit"
                    )
            elif self.orphan_closure_sensitivity_status is not None:
                raise ValueError(
                    "only an orphan-note-closure failure can contain its named sensitivity audit"
                )
            if (
                self.semantic_manifest_sha256 is not None
                or self.pairing_sensitivity_manifest_sha256 is not None
                or self.pairing_comparison_status is not None
            ):
                raise ValueError(
                    "a failed conversion cannot have semantic or pairing evidence"
                )
            scalar_metrics = (
                self.note_count,
                self.pairing_note_count,
                self.fifo_lifo_changed_pair_count,
                self.fifo_lifo_changed_release_tick_count,
                self.fifo_lifo_total_absolute_release_tick_difference,
                self.retrigger_candidate_note_count,
                self.retrigger_truncated_note_count,
                self.retrigger_total_removed_duration_ticks,
                self.raw_close_same_tick_precedence_count,
                self.simultaneous_same_identity_open_group_count,
                self.simultaneous_same_identity_open_event_count,
                self.simultaneous_same_identity_open_excess_count,
                self.controller_count,
                self.tempo_point_count,
                self.explicit_tempo_event_count,
                self.midi_port_event_count,
                self.time_signature_count,
                self.out_of_88_key_note_count,
                self.projection_collision_cell_count,
                self.projection_collision_event_count,
                self.projection_collision_excess_event_count,
                self.maximum_projection_collision_cell_multiplicity,
                self.projection_collision_window_count,
                self.window_count,
                self.tail_retained_window_count,
            )
            if (
                any(scalar_metrics)
                or self.closure_spelling_counts
                or self.pedal_controller_counts
                or self.note_producing_streams
                or self.projection_collision_by_pitch
                or self.projection_collision_pitch_multiplicity_histogram
                or self.projection_collision_multiplicity_histogram
                or self.pitch_minimum is not None
                or self.pitch_maximum is not None
                or self.maximum_grid_index is not None
                or self.window_ineligible
                or self.projection_admitted
            ):
                raise ValueError("a failed conversion cannot claim semantic metrics")
            return

        if any(
            value is not None
            for value in (
                self.failure_code,
                self.failure_detail,
                self.failure_detail_sha256,
            )
        ):
            raise ValueError("a passing conversion cannot contain failure evidence")
        if self.orphan_closure_sensitivity_status is not None:
            raise ValueError(
                "a passing conversion cannot contain orphan-closure sensitivity evidence"
            )
        _sha256(self.semantic_manifest_sha256, name="semantic_manifest_sha256")
        _sha256(
            self.pairing_sensitivity_manifest_sha256,
            name="pairing_sensitivity_manifest_sha256",
        )
        if self.pairing_comparison_status not in (
            "pairing_invariant",
            "representation_sensitive",
        ):
            raise ValueError("a passing conversion requires pairing comparison status")
        if self.pairing_note_count != self.note_count:
            raise ValueError("completed pairing evidence must cover every semantic note")
        if not 0 <= self.fifo_lifo_changed_pair_count <= self.note_count:
            raise ValueError("changed FIFO/LIFO pairs cannot exceed note_count")
        if self.fifo_lifo_changed_pair_count == 1:
            raise ValueError("a one-to-one closure permutation cannot change one pair")
        if not (
            0
            <= self.fifo_lifo_changed_release_tick_count
            <= self.fifo_lifo_changed_pair_count
        ):
            raise ValueError("changed release ticks cannot exceed changed pairs")
        if self.fifo_lifo_changed_release_tick_count == 1:
            raise ValueError("a release-tick permutation cannot change one note")
        if self.fifo_lifo_changed_release_tick_count == 0:
            if self.fifo_lifo_total_absolute_release_tick_difference != 0:
                raise ValueError("zero changed release ticks require zero tick difference")
        elif (
            self.fifo_lifo_total_absolute_release_tick_difference
            < self.fifo_lifo_changed_release_tick_count
        ):
            raise ValueError("release-tick difference is too small")
        if self.fifo_lifo_total_absolute_release_tick_difference % 2:
            raise ValueError(
                "release-tick permutation has an even total absolute difference"
            )
        if not (
            0
            <= self.retrigger_truncated_note_count
            <= self.retrigger_candidate_note_count
            <= self.note_count
        ):
            raise ValueError("retrigger counts must nest within note_count")
        if (
            self.raw_close_same_tick_precedence_count
            + self.retrigger_truncated_note_count
            > self.retrigger_candidate_note_count
        ):
            raise ValueError("retrigger ties and truncations cannot exceed candidates")
        if self.retrigger_truncated_note_count == 0:
            if self.retrigger_total_removed_duration_ticks != 0:
                raise ValueError("zero retrigger truncations require zero removed ticks")
        elif (
            self.retrigger_total_removed_duration_ticks
            < self.retrigger_truncated_note_count
        ):
            raise ValueError("retrigger removed-duration total is too small")
        if self.simultaneous_same_identity_open_group_count == 0:
            if (
                self.simultaneous_same_identity_open_event_count
                or self.simultaneous_same_identity_open_excess_count
            ):
                raise ValueError("zero simultaneous groups require zero event counts")
        elif (
            self.simultaneous_same_identity_open_event_count
            < 2 * self.simultaneous_same_identity_open_group_count
            or self.simultaneous_same_identity_open_excess_count
            != self.simultaneous_same_identity_open_event_count
            - self.simultaneous_same_identity_open_group_count
            or self.simultaneous_same_identity_open_event_count > self.note_count
        ):
            raise ValueError("simultaneous same-identity counts are inconsistent")
        if (
            self.simultaneous_same_identity_open_group_count
            and self.fifo_lifo_changed_pair_count < 2
        ):
            raise ValueError(
                "simultaneous same-identity groups require changed FIFO/LIFO pairs"
            )
        expected_pairing_status = (
            "representation_sensitive"
            if self.fifo_lifo_changed_pair_count
            or self.retrigger_truncated_note_count
            else "pairing_invariant"
        )
        if self.pairing_comparison_status != expected_pairing_status:
            raise ValueError("pairing comparison status is inconsistent with counts")
        if sum(count for _, count in self.closure_spelling_counts) != self.note_count:
            raise ValueError("closure spelling counts must equal note_count")
        if sum(count for _, count in self.pedal_controller_counts) > self.controller_count:
            raise ValueError("pedal facts cannot exceed controller_count")
        if not 1 <= self.tempo_point_count <= self.explicit_tempo_event_count + 1:
            raise ValueError("tempo-point count is inconsistent with explicit events")
        if self.out_of_88_key_note_count > self.note_count:
            raise ValueError("out-of-support note count cannot exceed note_count")
        if len(self.note_producing_streams) > self.note_count:
            raise ValueError("note-producing streams cannot exceed note_count")
        if self.projection_collision_event_count > self.note_count:
            raise ValueError("collision events cannot exceed note_count")
        if (self.pitch_minimum is None) != (self.pitch_maximum is None):
            raise ValueError("pitch bounds must both be present or absent")
        if self.note_count == 0:
            if (
                self.pitch_minimum is not None
                or self.note_producing_streams
                or self.maximum_grid_index is not None
                or self.out_of_88_key_note_count
                or self.projection_collision_cell_count
                or self.projection_collision_event_count
                or self.projection_collision_excess_event_count
                or self.projection_collision_by_pitch
                or self.projection_collision_pitch_multiplicity_histogram
                or self.projection_collision_multiplicity_histogram
                or self.maximum_projection_collision_cell_multiplicity
                or self.projection_collision_window_count
                or self.window_count
                or self.tail_retained_window_count
                or not self.window_ineligible
                or self.projection_admitted
            ):
                raise ValueError("empty semantic pieces must remain window-ineligible")
        else:
            if (
                self.pitch_minimum is None
                or self.pitch_maximum is None
                or self.maximum_grid_index is None
                or not self.note_producing_streams
            ):
                raise ValueError("nonempty semantic pieces require support diagnostics")
            if not 0 <= self.pitch_minimum <= self.pitch_maximum <= 127:
                raise ValueError("pitch bounds are outside 0..127")
            if 21 <= self.pitch_minimum and self.pitch_maximum <= 108:
                if self.out_of_88_key_note_count != 0:
                    raise ValueError("88-key support count conflicts with pitch bounds")
            elif self.pitch_maximum < 21 or self.pitch_minimum > 108:
                if self.out_of_88_key_note_count != self.note_count:
                    raise ValueError("all notes outside 88-key bounds must be counted")
            elif self.out_of_88_key_note_count == 0:
                raise ValueError("an out-of-support pitch bound requires an outlier note")
            _plain_nonnegative_int(self.maximum_grid_index, name="maximum_grid_index")
            expected_windows, remainder = divmod(
                self.maximum_grid_index + 1, MAESTRO_WINDOW_LENGTH
            )
            expected_windows += int(bool(remainder))
            if self.window_count != expected_windows:
                raise ValueError("window_count violates the T=256 nonoverlap policy")
            if self.tail_retained_window_count != int(bool(remainder)):
                raise ValueError("tail_retained_window_count is inconsistent")
            if self.window_ineligible:
                raise ValueError("a nonempty semantic piece is window-enumerable")
        if self.projection_collision_cell_count == 0:
            if (
                self.projection_collision_event_count
                or self.projection_collision_excess_event_count
                or self.projection_collision_by_pitch
                or self.projection_collision_pitch_multiplicity_histogram
                or self.projection_collision_multiplicity_histogram
                or self.maximum_projection_collision_cell_multiplicity
                or self.projection_collision_window_count
            ):
                raise ValueError("zero collision cells require zero collision diagnostics")
        elif self.projection_collision_event_count < 2 * self.projection_collision_cell_count:
            raise ValueError("each collision cell must contain at least two events")
        if (
            self.projection_collision_excess_event_count
            != self.projection_collision_event_count
            - self.projection_collision_cell_count
        ):
            raise ValueError("collision excess count is inconsistent")
        if (
            sum(item[1] for item in self.projection_collision_by_pitch)
            != self.projection_collision_cell_count
            or sum(item[2] for item in self.projection_collision_by_pitch)
            != self.projection_collision_event_count
            or sum(item[3] for item in self.projection_collision_by_pitch)
            != self.projection_collision_excess_event_count
        ):
            raise ValueError("pitch-collision counts do not match file totals")
        if self.projection_collision_by_pitch and any(
            pitch < self.pitch_minimum or pitch > self.pitch_maximum
            for pitch, _, _, _ in self.projection_collision_by_pitch
        ):
            raise ValueError("collision pitch is outside the file pitch bounds")
        joint_pitch_cells = Counter()
        joint_pitch_events = Counter()
        joint_pitch_excess = Counter()
        joint_multiplicities = Counter()
        for pitch, multiplicity, count in (
            self.projection_collision_pitch_multiplicity_histogram
        ):
            joint_pitch_cells[pitch] += count
            joint_pitch_events[pitch] += multiplicity * count
            joint_pitch_excess[pitch] += (multiplicity - 1) * count
            joint_multiplicities[multiplicity] += count
        expected_by_pitch = tuple(
            (
                pitch,
                joint_pitch_cells[pitch],
                joint_pitch_events[pitch],
                joint_pitch_excess[pitch],
            )
            for pitch in sorted(joint_pitch_cells)
        )
        if expected_by_pitch != self.projection_collision_by_pitch:
            raise ValueError(
                "pitch and multiplicity collision margins lack one joint witness"
            )
        if tuple(sorted(joint_multiplicities.items())) != (
            self.projection_collision_multiplicity_histogram
        ):
            raise ValueError(
                "collision multiplicity margin disagrees with pitch-multiplicity joint counts"
            )
        if (
            sum(count for _, count in self.projection_collision_multiplicity_histogram)
            != self.projection_collision_cell_count
            or sum(
                multiplicity * count
                for multiplicity, count in self.projection_collision_multiplicity_histogram
            )
            != self.projection_collision_event_count
            or sum(
                (multiplicity - 1) * count
                for multiplicity, count in self.projection_collision_multiplicity_histogram
            )
            != self.projection_collision_excess_event_count
        ):
            raise ValueError("collision multiplicity histogram does not match file totals")
        expected_maximum_multiplicity = max(
            [
                multiplicity
                for multiplicity, _ in self.projection_collision_multiplicity_histogram
            ]
            or [0]
        )
        if (
            self.maximum_projection_collision_cell_multiplicity
            != expected_maximum_multiplicity
        ):
            raise ValueError("maximum collision-cell multiplicity is inconsistent")
        if self.projection_collision_by_pitch and any(
            cells > self.maximum_grid_index + 1
            or cells
            > MAESTRO_WINDOW_LENGTH * self.projection_collision_window_count
            for _, cells, _, _ in self.projection_collision_by_pitch
        ):
            raise ValueError(
                "collision cells at one pitch exceed available grid/window positions"
            )
        if self.note_count and not _pitch_support_is_feasible(
            note_count=self.note_count,
            pitch_minimum=self.pitch_minimum,
            pitch_maximum=self.pitch_maximum,
            out_of_88_key_note_count=self.out_of_88_key_note_count,
            projection_collision_by_pitch=self.projection_collision_by_pitch,
        ):
            raise ValueError("pitch-support margins have no feasible note histogram")
        if (
            self.simultaneous_same_identity_open_event_count
            > self.projection_collision_event_count
            or self.simultaneous_same_identity_open_excess_count
            > self.projection_collision_excess_event_count
        ):
            raise ValueError(
                "simultaneous same-identity onsets require projection collisions"
            )
        if self.simultaneous_same_identity_open_group_count and (
            (
                self.simultaneous_same_identity_open_event_count
                + self.simultaneous_same_identity_open_group_count
                - 1
            )
            // self.simultaneous_same_identity_open_group_count
            > self.maximum_projection_collision_cell_multiplicity
        ):
            raise ValueError(
                "simultaneous same-identity group size exceeds collision-cell capacity"
            )
        if self.simultaneous_same_identity_open_event_count > (
            _largest_collision_cell_capacity(
                self.projection_collision_multiplicity_histogram,
                self.simultaneous_same_identity_open_group_count,
            )
        ):
            raise ValueError(
                "simultaneous groups exceed the largest collision-cell capacities"
            )
        if self.projection_collision_cell_count and self.projection_collision_window_count == 0:
            raise ValueError("a collided file must identify at least one collision window")
        if self.projection_collision_window_count > min(
            self.window_count, self.projection_collision_cell_count
        ):
            raise ValueError("collision windows cannot exceed enumerated windows")
        expected_admitted = (
            self.note_count > 0
            and self.out_of_88_key_note_count == 0
            and len(self.note_producing_streams) == 1
            and self.projection_collision_cell_count == 0
        )
        if self.projection_admitted != expected_admitted:
            raise ValueError("projection_admitted is inconsistent with diagnostics")

    @property
    def pedal_fact_count(self) -> int:
        return sum(count for _, count in self.pedal_controller_counts)

    @property
    def semantic_passed(self) -> bool:
        return self.status == "pass"

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "metadata_row_number": self.metadata_row_number,
            "midi_path": self.midi_path,
            "source_split": self.source_split,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "failure_code": self.failure_code,
            "failure_detail": self.failure_detail,
            "failure_detail_sha256": self.failure_detail_sha256,
            "semantic_manifest_sha256": self.semantic_manifest_sha256,
            "pairing_sensitivity_manifest_sha256": (
                self.pairing_sensitivity_manifest_sha256
            ),
            "pairing_comparison_status": self.pairing_comparison_status,
            "orphan_closure_sensitivity_status": (
                self.orphan_closure_sensitivity_status
            ),
            "orphan_closure_sensitivity_rejection_code": (
                self.orphan_closure_sensitivity_rejection_code
            ),
            "orphan_closure_sensitivity_failure_detail_sha256": (
                self.orphan_closure_sensitivity_failure_detail_sha256
            ),
            "orphan_closure_sensitivity_manifest_sha256": (
                self.orphan_closure_sensitivity_manifest_sha256
            ),
            "note_count": self.note_count,
            "pairing_note_count": self.pairing_note_count,
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
            "simultaneous_same_identity_open_group_count": (
                self.simultaneous_same_identity_open_group_count
            ),
            "simultaneous_same_identity_open_event_count": (
                self.simultaneous_same_identity_open_event_count
            ),
            "simultaneous_same_identity_open_excess_count": (
                self.simultaneous_same_identity_open_excess_count
            ),
            "closure_spelling_counts": [list(item) for item in self.closure_spelling_counts],
            "controller_count": self.controller_count,
            "pedal_controller_counts": [list(item) for item in self.pedal_controller_counts],
            "tempo_point_count": self.tempo_point_count,
            "explicit_tempo_event_count": self.explicit_tempo_event_count,
            "midi_port_event_count": self.midi_port_event_count,
            "time_signature_count": self.time_signature_count,
            "pitch_minimum": self.pitch_minimum,
            "pitch_maximum": self.pitch_maximum,
            "out_of_88_key_note_count": self.out_of_88_key_note_count,
            "note_producing_streams": [list(item) for item in self.note_producing_streams],
            "projection_collision_cell_count": self.projection_collision_cell_count,
            "projection_collision_event_count": self.projection_collision_event_count,
            "projection_collision_excess_event_count": (
                self.projection_collision_excess_event_count
            ),
            "projection_collision_by_pitch": [
                {
                    "pitch": pitch,
                    "cell_count": cells,
                    "event_count": events,
                    "excess_event_count": excess,
                }
                for pitch, cells, events, excess in self.projection_collision_by_pitch
            ],
            "projection_collision_pitch_multiplicity_histogram": [
                {
                    "pitch": pitch,
                    "cell_multiplicity": multiplicity,
                    "cell_count": count,
                }
                for pitch, multiplicity, count in (
                    self.projection_collision_pitch_multiplicity_histogram
                )
            ],
            "projection_collision_multiplicity_histogram": {
                str(multiplicity): count
                for multiplicity, count in (
                    self.projection_collision_multiplicity_histogram
                )
            },
            "maximum_projection_collision_cell_multiplicity": (
                self.maximum_projection_collision_cell_multiplicity
            ),
            "projection_collision_window_count": self.projection_collision_window_count,
            "maximum_grid_index": self.maximum_grid_index,
            "window_count": self.window_count,
            "tail_retained_window_count": self.tail_retained_window_count,
            "window_ineligible": self.window_ineligible,
            "projection_admitted": self.projection_admitted,
        }


@dataclass(frozen=True)
class MaestroSemanticAggregate:
    """One immutable all-corpus or source-split aggregate."""

    scope: str
    file_count: int
    semantic_pass_count: int
    semantic_failure_count: int
    failure_code_counts: Tuple[Tuple[str, int], ...]
    orphan_closure_sensitivity_attempted_count: int
    orphan_closure_sensitivity_admitted_count: int
    orphan_closure_sensitivity_rejected_count: int
    orphan_closure_sensitivity_rejection_code_counts: Tuple[Tuple[str, int], ...]
    orphan_closure_sensitivity_manifests_sha256: str
    note_count: int
    pairing_evidence_piece_count: int
    pairing_invariant_piece_count: int
    pairing_representation_sensitive_piece_count: int
    pairing_note_count: int
    fifo_lifo_changed_pair_count: int
    fifo_lifo_changed_release_tick_count: int
    fifo_lifo_total_absolute_release_tick_difference: int
    retrigger_candidate_note_count: int
    retrigger_truncated_note_count: int
    retrigger_total_removed_duration_ticks: int
    raw_close_same_tick_precedence_count: int
    simultaneous_same_identity_open_group_count: int
    simultaneous_same_identity_open_event_count: int
    simultaneous_same_identity_open_excess_count: int
    closure_spelling_counts: Tuple[Tuple[str, int], ...]
    controller_count: int
    pedal_controller_counts: Tuple[Tuple[int, int], ...]
    tempo_point_count: int
    explicit_tempo_event_count: int
    midi_port_event_count: int
    time_signature_count: int
    pitch_minimum: Optional[int]
    pitch_maximum: Optional[int]
    out_of_88_key_note_count: int
    out_of_88_key_piece_count: int
    note_producing_stream_count: int
    multiple_note_stream_piece_count: int
    maximum_note_streams_per_piece: int
    projection_collision_cell_count: int
    projection_collision_event_count: int
    projection_collision_excess_event_count: int
    projection_collision_piece_count: int
    projection_collision_by_pitch: Tuple[Tuple[int, int, int, int], ...]
    projection_collision_pitch_multiplicity_histogram: Tuple[
        Tuple[int, int, int], ...
    ]
    projection_collision_multiplicity_histogram: Tuple[Tuple[int, int], ...]
    maximum_projection_collision_cell_multiplicity: int
    projection_collision_piece_histogram: Tuple[Tuple[int, int], ...]
    projection_collision_piece_profile_histogram: Tuple[
        Tuple[Tuple[Tuple[int, int, int], ...], int, int], ...
    ]
    maximum_projection_collision_cells_per_piece: int
    maximum_projection_collision_events_per_piece: int
    maximum_projection_collision_excess_events_per_piece: int
    projection_collision_window_count: int
    maximum_grid_index: Optional[int]
    window_count: int
    tail_retained_window_count: int
    empty_piece_count: int
    window_ineligible_piece_count: int
    projection_admitted_piece_count: int
    semantic_manifests_sha256: str
    pairing_sensitivity_manifests_sha256: str

    def __post_init__(self) -> None:
        if self.scope not in frozenset(("all",) + _SOURCE_SPLITS):
            raise ValueError("scope must be all or an official source split")
        for name in (
            "file_count",
            "semantic_pass_count",
            "semantic_failure_count",
            "orphan_closure_sensitivity_attempted_count",
            "orphan_closure_sensitivity_admitted_count",
            "orphan_closure_sensitivity_rejected_count",
            "note_count",
            "pairing_evidence_piece_count",
            "pairing_invariant_piece_count",
            "pairing_representation_sensitive_piece_count",
            "pairing_note_count",
            "fifo_lifo_changed_pair_count",
            "fifo_lifo_changed_release_tick_count",
            "fifo_lifo_total_absolute_release_tick_difference",
            "retrigger_candidate_note_count",
            "retrigger_truncated_note_count",
            "retrigger_total_removed_duration_ticks",
            "raw_close_same_tick_precedence_count",
            "simultaneous_same_identity_open_group_count",
            "simultaneous_same_identity_open_event_count",
            "simultaneous_same_identity_open_excess_count",
            "controller_count",
            "tempo_point_count",
            "explicit_tempo_event_count",
            "midi_port_event_count",
            "time_signature_count",
            "out_of_88_key_note_count",
            "out_of_88_key_piece_count",
            "note_producing_stream_count",
            "multiple_note_stream_piece_count",
            "maximum_note_streams_per_piece",
            "projection_collision_cell_count",
            "projection_collision_event_count",
            "projection_collision_excess_event_count",
            "projection_collision_piece_count",
            "maximum_projection_collision_cell_multiplicity",
            "maximum_projection_collision_cells_per_piece",
            "maximum_projection_collision_events_per_piece",
            "maximum_projection_collision_excess_events_per_piece",
            "projection_collision_window_count",
            "window_count",
            "tail_retained_window_count",
            "empty_piece_count",
            "window_ineligible_piece_count",
            "projection_admitted_piece_count",
        ):
            _plain_nonnegative_int(getattr(self, name), name=name)
        object.__setattr__(
            self,
            "failure_code_counts",
            _named_counts(self.failure_code_counts, name="failure_code_counts"),
        )
        object.__setattr__(
            self,
            "orphan_closure_sensitivity_rejection_code_counts",
            _named_counts(
                self.orphan_closure_sensitivity_rejection_code_counts,
                name="orphan_closure_sensitivity_rejection_code_counts",
            ),
        )
        object.__setattr__(
            self,
            "closure_spelling_counts",
            _named_counts(
                self.closure_spelling_counts,
                name="closure_spelling_counts",
                allowed_keys=frozenset(("note_off", "note_on_velocity_zero")),
            ),
        )
        object.__setattr__(
            self, "pedal_controller_counts", _pedal_counts(self.pedal_controller_counts)
        )
        object.__setattr__(
            self,
            "projection_collision_by_pitch",
            _pitch_collision_counts(self.projection_collision_by_pitch),
        )
        object.__setattr__(
            self,
            "projection_collision_pitch_multiplicity_histogram",
            _collision_pitch_multiplicity_histogram(
                self.projection_collision_pitch_multiplicity_histogram
            ),
        )
        object.__setattr__(
            self,
            "projection_collision_multiplicity_histogram",
            _collision_multiplicity_histogram(
                self.projection_collision_multiplicity_histogram
            ),
        )
        object.__setattr__(
            self,
            "projection_collision_piece_histogram",
            _positive_histogram(
                self.projection_collision_piece_histogram,
                name="projection_collision_piece_histogram",
            ),
        )
        object.__setattr__(
            self,
            "projection_collision_piece_profile_histogram",
            _collision_piece_profile_histogram(
                self.projection_collision_piece_profile_histogram
            ),
        )
        _sha256(self.semantic_manifests_sha256, name="semantic_manifests_sha256")
        _sha256(
            self.pairing_sensitivity_manifests_sha256,
            name="pairing_sensitivity_manifests_sha256",
        )
        _sha256(
            self.orphan_closure_sensitivity_manifests_sha256,
            name="orphan_closure_sensitivity_manifests_sha256",
        )
        if self.file_count != self.semantic_pass_count + self.semantic_failure_count:
            raise ValueError("file_count must partition into pass and semantic failure")
        if sum(count for _, count in self.failure_code_counts) != self.semantic_failure_count:
            raise ValueError("failure-code counts must equal semantic_failure_count")
        if self.orphan_closure_sensitivity_attempted_count != (
            dict(self.failure_code_counts).get("ORPHAN_NOTE_CLOSURE", 0)
        ):
            raise ValueError(
                "every and only orphan-note-closure failure requires a sensitivity attempt"
            )
        if self.orphan_closure_sensitivity_attempted_count != (
            self.orphan_closure_sensitivity_admitted_count
            + self.orphan_closure_sensitivity_rejected_count
        ):
            raise ValueError(
                "orphan-closure sensitivity outcomes must partition attempts"
            )
        if sum(
            count
            for _, count in self.orphan_closure_sensitivity_rejection_code_counts
        ) != self.orphan_closure_sensitivity_rejected_count:
            raise ValueError(
                "orphan-closure rejection-code counts must equal rejected attempts"
            )
        if self.semantic_pass_count == 0:
            semantic_scalars = (
                self.note_count,
                self.pairing_evidence_piece_count,
                self.pairing_invariant_piece_count,
                self.pairing_representation_sensitive_piece_count,
                self.pairing_note_count,
                self.fifo_lifo_changed_pair_count,
                self.fifo_lifo_changed_release_tick_count,
                self.fifo_lifo_total_absolute_release_tick_difference,
                self.retrigger_candidate_note_count,
                self.retrigger_truncated_note_count,
                self.retrigger_total_removed_duration_ticks,
                self.raw_close_same_tick_precedence_count,
                self.simultaneous_same_identity_open_group_count,
                self.simultaneous_same_identity_open_event_count,
                self.simultaneous_same_identity_open_excess_count,
                self.controller_count,
                self.tempo_point_count,
                self.explicit_tempo_event_count,
                self.midi_port_event_count,
                self.time_signature_count,
                self.out_of_88_key_note_count,
                self.out_of_88_key_piece_count,
                self.note_producing_stream_count,
                self.multiple_note_stream_piece_count,
                self.maximum_note_streams_per_piece,
                self.projection_collision_cell_count,
                self.projection_collision_event_count,
                self.projection_collision_excess_event_count,
                self.projection_collision_piece_count,
                self.maximum_projection_collision_cell_multiplicity,
                self.maximum_projection_collision_cells_per_piece,
                self.maximum_projection_collision_events_per_piece,
                self.maximum_projection_collision_excess_events_per_piece,
                self.projection_collision_window_count,
                self.window_count,
                self.tail_retained_window_count,
                self.empty_piece_count,
                self.window_ineligible_piece_count,
                self.projection_admitted_piece_count,
            )
            semantic_collections = (
                self.closure_spelling_counts,
                self.pedal_controller_counts,
                self.projection_collision_by_pitch,
                self.projection_collision_pitch_multiplicity_histogram,
                self.projection_collision_multiplicity_histogram,
                self.projection_collision_piece_histogram,
                self.projection_collision_piece_profile_histogram,
            )
            if (
                any(semantic_scalars)
                or any(semantic_collections)
                or self.pitch_minimum is not None
                or self.pitch_maximum is not None
                or self.maximum_grid_index is not None
            ):
                raise ValueError("an all-failed aggregate cannot claim semantic metrics")
            return
        if sum(count for _, count in self.closure_spelling_counts) != self.note_count:
            raise ValueError("closure counts must equal note_count")
        if self.pairing_evidence_piece_count != self.semantic_pass_count:
            raise ValueError("every semantic pass requires completed pairing evidence")
        if (
            self.pairing_invariant_piece_count
            + self.pairing_representation_sensitive_piece_count
            != self.pairing_evidence_piece_count
        ):
            raise ValueError("pairing statuses must partition completed evidence")
        if self.pairing_note_count != self.note_count:
            raise ValueError("aggregate pairing evidence must cover every semantic note")
        if not 0 <= self.fifo_lifo_changed_pair_count <= self.note_count:
            raise ValueError("aggregate changed pairs cannot exceed note_count")
        if self.fifo_lifo_changed_pair_count == 1:
            raise ValueError("aggregate one-to-one pairing cannot change one pair")
        if not (
            0
            <= self.fifo_lifo_changed_release_tick_count
            <= self.fifo_lifo_changed_pair_count
        ):
            raise ValueError("aggregate changed release ticks exceed changed pairs")
        if self.fifo_lifo_changed_release_tick_count == 1:
            raise ValueError("aggregate release-tick permutations cannot change one note")
        if self.fifo_lifo_changed_release_tick_count == 0:
            if self.fifo_lifo_total_absolute_release_tick_difference != 0:
                raise ValueError("aggregate zero changed ticks require zero difference")
        elif (
            self.fifo_lifo_total_absolute_release_tick_difference
            < self.fifo_lifo_changed_release_tick_count
        ):
            raise ValueError("aggregate release-tick difference is too small")
        if self.fifo_lifo_total_absolute_release_tick_difference % 2:
            raise ValueError(
                "aggregate release-tick permutation has an even total absolute difference"
            )
        if not (
            0
            <= self.retrigger_truncated_note_count
            <= self.retrigger_candidate_note_count
            <= self.note_count
        ):
            raise ValueError("aggregate retrigger counts must nest within note_count")
        if (
            self.raw_close_same_tick_precedence_count
            + self.retrigger_truncated_note_count
            > self.retrigger_candidate_note_count
        ):
            raise ValueError("aggregate retrigger ties/truncations exceed candidates")
        if self.retrigger_truncated_note_count == 0:
            if self.retrigger_total_removed_duration_ticks != 0:
                raise ValueError("aggregate zero truncations require zero removed ticks")
        elif (
            self.retrigger_total_removed_duration_ticks
            < self.retrigger_truncated_note_count
        ):
            raise ValueError("aggregate retrigger removed-duration total is too small")
        if self.simultaneous_same_identity_open_group_count == 0:
            if (
                self.simultaneous_same_identity_open_event_count
                or self.simultaneous_same_identity_open_excess_count
            ):
                raise ValueError("aggregate zero simultaneous groups require zero counts")
        elif (
            self.simultaneous_same_identity_open_event_count
            < 2 * self.simultaneous_same_identity_open_group_count
            or self.simultaneous_same_identity_open_excess_count
            != self.simultaneous_same_identity_open_event_count
            - self.simultaneous_same_identity_open_group_count
            or self.simultaneous_same_identity_open_event_count > self.note_count
        ):
            raise ValueError("aggregate simultaneous-open counts are inconsistent")
        if (
            self.simultaneous_same_identity_open_group_count
            and self.fifo_lifo_changed_pair_count < 2
        ):
            raise ValueError(
                "aggregate simultaneous-open groups require changed FIFO/LIFO pairs"
            )
        sensitivity_witnesses = (
            self.fifo_lifo_changed_pair_count
            + self.retrigger_truncated_note_count
        )
        if sensitivity_witnesses == 0:
            if self.pairing_representation_sensitive_piece_count != 0:
                raise ValueError("zero pairing differences require invariant pieces")
        elif not (
            1
            <= self.pairing_representation_sensitive_piece_count
            <= min(self.pairing_evidence_piece_count, sensitivity_witnesses)
        ):
            raise ValueError("representation-sensitive piece count lacks witnesses")
        if sum(count for _, count in self.pedal_controller_counts) > self.controller_count:
            raise ValueError("pedal facts cannot exceed controllers")
        if not (
            self.semantic_pass_count
            <= self.tempo_point_count
            <= self.explicit_tempo_event_count + self.semantic_pass_count
        ):
            raise ValueError("aggregate tempo-point count is inconsistent")
        if self.out_of_88_key_note_count > self.note_count:
            raise ValueError("aggregate out-of-support notes exceed note_count")
        if self.note_producing_stream_count > self.note_count:
            raise ValueError("aggregate note-producing streams exceed note_count")
        if self.projection_collision_event_count > self.note_count:
            raise ValueError("aggregate collision events exceed note_count")
        nonempty_piece_count = self.semantic_pass_count - self.empty_piece_count
        if nonempty_piece_count < 0:
            raise ValueError("empty pieces exceed semantic pass count")
        if self.note_count < nonempty_piece_count:
            raise ValueError("every nonempty piece must contain at least one note")
        if self.out_of_88_key_note_count == 0:
            if self.out_of_88_key_piece_count != 0:
                raise ValueError("zero out-of-support notes require zero affected pieces")
        elif not 1 <= self.out_of_88_key_piece_count <= min(
            nonempty_piece_count, self.out_of_88_key_note_count
        ):
            raise ValueError("out-of-support piece count is inconsistent")
        if (self.pitch_minimum is None) != (self.pitch_maximum is None):
            raise ValueError("aggregate pitch bounds must both be present or absent")
        if self.note_count == 0:
            if self.pitch_minimum is not None or self.maximum_grid_index is not None:
                raise ValueError("empty aggregate cannot have pitch/grid bounds")
        else:
            if self.pitch_minimum is None or self.maximum_grid_index is None:
                raise ValueError("nonempty aggregate requires pitch/grid bounds")
            if self.pitch_maximum is None or not (
                0 <= self.pitch_minimum <= self.pitch_maximum <= 127
            ):
                raise ValueError("aggregate pitch bounds are invalid")
            if 21 <= self.pitch_minimum and self.pitch_maximum <= 108:
                if self.out_of_88_key_note_count != 0:
                    raise ValueError("aggregate 88-key count conflicts with pitch bounds")
            elif self.pitch_maximum < 21 or self.pitch_minimum > 108:
                if self.out_of_88_key_note_count != self.note_count:
                    raise ValueError("all aggregate notes outside support must be counted")
                if self.out_of_88_key_piece_count != nonempty_piece_count:
                    raise ValueError("all nonempty pieces outside support must be counted")
            elif self.out_of_88_key_note_count == 0:
                raise ValueError("aggregate out-of-support bound requires an outlier")

        if nonempty_piece_count == 0:
            if (
                self.note_producing_stream_count
                or self.multiple_note_stream_piece_count
                or self.maximum_note_streams_per_piece
                or self.window_count
                or self.tail_retained_window_count
                or self.projection_admitted_piece_count
            ):
                raise ValueError("empty aggregate cannot claim streams or windows")
        else:
            if not (
                nonempty_piece_count
                <= self.note_producing_stream_count
                <= self.maximum_note_streams_per_piece * nonempty_piece_count
            ):
                raise ValueError("aggregate note-stream incidence is inconsistent")
            if self.note_producing_stream_count < (
                nonempty_piece_count + self.multiple_note_stream_piece_count
            ):
                raise ValueError("multi-stream pieces require extra stream incidences")
            if self.note_producing_stream_count > (
                nonempty_piece_count
                + self.multiple_note_stream_piece_count
                * (self.maximum_note_streams_per_piece - 1)
            ):
                raise ValueError(
                    "aggregate stream incidences exceed the multi-stream piece budget"
                )
            if self.maximum_note_streams_per_piece > (
                self.note_producing_stream_count - nonempty_piece_count + 1
            ):
                raise ValueError("maximum stream count exceeds available incidences")
            if self.multiple_note_stream_piece_count == 0:
                if self.maximum_note_streams_per_piece != 1:
                    raise ValueError("single-stream pieces require maximum stream count one")
            elif self.maximum_note_streams_per_piece < 2:
                raise ValueError("multi-stream pieces require maximum stream count at least two")
            if self.window_count < nonempty_piece_count:
                raise ValueError("every nonempty piece requires at least one window")
            if self.tail_retained_window_count > nonempty_piece_count:
                raise ValueError("tail windows cannot exceed nonempty pieces")
            if self.projection_admitted_piece_count > nonempty_piece_count:
                raise ValueError("projection-admitted pieces must be nonempty")
            if self.multiple_note_stream_piece_count > nonempty_piece_count:
                raise ValueError("multi-stream pieces must be nonempty")
            if self.projection_collision_piece_count > nonempty_piece_count:
                raise ValueError("collided pieces must be nonempty")
            clean_piece_count = (
                nonempty_piece_count - self.projection_collision_piece_count
            )
            if self.note_count < (
                self.projection_collision_event_count + clean_piece_count
            ):
                raise ValueError(
                    "collision events and clean nonempty pieces exceed the note budget"
                )
            if self.window_count < (
                self.projection_collision_window_count + clean_piece_count
            ):
                raise ValueError(
                    "collision windows and clean nonempty pieces exceed the window budget"
                )
            if self.maximum_grid_index is None:
                raise ValueError("nonempty aggregate requires a grid maximum")
            maximum_piece_windows = (
                self.maximum_grid_index // MAESTRO_WINDOW_LENGTH + 1
            )
            if not (
                maximum_piece_windows + nonempty_piece_count - 1
                <= self.window_count
                <= maximum_piece_windows * nonempty_piece_count
            ):
                raise ValueError(
                    "aggregate window count is incompatible with the grid maximum"
                )
            if (
                (self.maximum_grid_index + 1) % MAESTRO_WINDOW_LENGTH
                and self.tail_retained_window_count == 0
            ):
                raise ValueError(
                    "a non-boundary aggregate grid maximum requires a retained tail"
                )
        if self.projection_collision_cell_count == 0:
            if (
                self.projection_collision_event_count
                or self.projection_collision_excess_event_count
                or self.projection_collision_piece_count
                or self.projection_collision_by_pitch
                or self.projection_collision_pitch_multiplicity_histogram
                or self.projection_collision_multiplicity_histogram
                or self.maximum_projection_collision_cell_multiplicity
                or self.projection_collision_piece_histogram
                or self.projection_collision_piece_profile_histogram
                or self.maximum_projection_collision_cells_per_piece
                or self.maximum_projection_collision_events_per_piece
                or self.maximum_projection_collision_excess_events_per_piece
                or self.projection_collision_window_count
            ):
                raise ValueError("zero aggregate collision cells require zero diagnostics")
        elif self.projection_collision_event_count < 2 * self.projection_collision_cell_count:
            raise ValueError("aggregate collision event count is too small")
        if (
            self.projection_collision_excess_event_count
            != self.projection_collision_event_count
            - self.projection_collision_cell_count
        ):
            raise ValueError("aggregate collision excess count is inconsistent")
        if (
            sum(item[1] for item in self.projection_collision_by_pitch)
            != self.projection_collision_cell_count
            or sum(item[2] for item in self.projection_collision_by_pitch)
            != self.projection_collision_event_count
            or sum(item[3] for item in self.projection_collision_by_pitch)
            != self.projection_collision_excess_event_count
        ):
            raise ValueError("aggregate pitch-collision counts do not match totals")
        if self.projection_collision_by_pitch and any(
            pitch < self.pitch_minimum or pitch > self.pitch_maximum
            for pitch, _, _, _ in self.projection_collision_by_pitch
        ):
            raise ValueError("aggregate collision pitch is outside pitch bounds")
        if self.maximum_grid_index is not None and any(
            cells
            > self.projection_collision_piece_count * (self.maximum_grid_index + 1)
            or cells
            > MAESTRO_WINDOW_LENGTH * self.projection_collision_window_count
            for _, cells, _, _ in self.projection_collision_by_pitch
        ):
            raise ValueError(
                "aggregate collision cells at one pitch exceed the piece/grid/window capacity"
            )
        joint_pitch_cells = Counter()
        joint_pitch_events = Counter()
        joint_pitch_excess = Counter()
        joint_multiplicities = Counter()
        for pitch, multiplicity, count in (
            self.projection_collision_pitch_multiplicity_histogram
        ):
            joint_pitch_cells[pitch] += count
            joint_pitch_events[pitch] += multiplicity * count
            joint_pitch_excess[pitch] += (multiplicity - 1) * count
            joint_multiplicities[multiplicity] += count
        expected_by_pitch = tuple(
            (
                pitch,
                joint_pitch_cells[pitch],
                joint_pitch_events[pitch],
                joint_pitch_excess[pitch],
            )
            for pitch in sorted(joint_pitch_cells)
        )
        if expected_by_pitch != self.projection_collision_by_pitch:
            raise ValueError(
                "aggregate pitch and multiplicity margins lack one joint witness"
            )
        if tuple(sorted(joint_multiplicities.items())) != (
            self.projection_collision_multiplicity_histogram
        ):
            raise ValueError(
                "aggregate multiplicity margin disagrees with pitch-multiplicity joint counts"
            )
        if (
            sum(count for _, count in self.projection_collision_multiplicity_histogram)
            != self.projection_collision_cell_count
            or sum(
                multiplicity * count
                for multiplicity, count in self.projection_collision_multiplicity_histogram
            )
            != self.projection_collision_event_count
            or sum(
                (multiplicity - 1) * count
                for multiplicity, count in self.projection_collision_multiplicity_histogram
            )
            != self.projection_collision_excess_event_count
        ):
            raise ValueError("aggregate collision multiplicity histogram does not match totals")
        expected_maximum_multiplicity = max(
            [
                multiplicity
                for multiplicity, _ in self.projection_collision_multiplicity_histogram
            ]
            or [0]
        )
        if (
            self.maximum_projection_collision_cell_multiplicity
            != expected_maximum_multiplicity
        ):
            raise ValueError("aggregate maximum collision-cell multiplicity is inconsistent")
        if self.note_count and not _pitch_support_is_feasible(
            note_count=self.note_count,
            pitch_minimum=self.pitch_minimum,
            pitch_maximum=self.pitch_maximum,
            out_of_88_key_note_count=self.out_of_88_key_note_count,
            projection_collision_by_pitch=self.projection_collision_by_pitch,
        ):
            raise ValueError(
                "aggregate pitch-support margins have no feasible note histogram"
            )
        if (
            self.simultaneous_same_identity_open_event_count
            > self.projection_collision_event_count
            or self.simultaneous_same_identity_open_excess_count
            > self.projection_collision_excess_event_count
        ):
            raise ValueError(
                "aggregate simultaneous same-identity onsets require collisions"
            )
        if self.simultaneous_same_identity_open_group_count and (
            (
                self.simultaneous_same_identity_open_event_count
                + self.simultaneous_same_identity_open_group_count
                - 1
            )
            // self.simultaneous_same_identity_open_group_count
            > self.maximum_projection_collision_cell_multiplicity
        ):
            raise ValueError(
                "aggregate simultaneous group size exceeds collision-cell capacity"
            )
        if self.simultaneous_same_identity_open_event_count > (
            _largest_collision_cell_capacity(
                self.projection_collision_multiplicity_histogram,
                self.simultaneous_same_identity_open_group_count,
            )
        ):
            raise ValueError(
                "aggregate simultaneous groups exceed the largest collision-cell capacities"
            )
        profile_piece_count = 0
        profile_cells = 0
        profile_events = 0
        profile_excess = 0
        profile_windows = 0
        profile_multiplicities = Counter()
        profile_pitch_multiplicities = Counter()
        profile_piece_histogram = Counter()
        profile_maxima = [0, 0, 0]
        maximum_piece_windows = (
            self.maximum_grid_index // MAESTRO_WINDOW_LENGTH + 1
            if self.maximum_grid_index is not None
            else 0
        )
        for pitch_multiplicities, collision_windows, piece_count in (
            self.projection_collision_piece_profile_histogram
        ):
            cells = sum(count for _, _, count in pitch_multiplicities)
            events = sum(
                multiplicity * count
                for _, multiplicity, count in pitch_multiplicities
            )
            excess = events - cells
            profile_piece_count += piece_count
            profile_cells += cells * piece_count
            profile_events += events * piece_count
            profile_excess += excess * piece_count
            profile_windows += collision_windows * piece_count
            profile_piece_histogram[cells] += piece_count
            profile_maxima[0] = max(profile_maxima[0], cells)
            profile_maxima[1] = max(profile_maxima[1], events)
            profile_maxima[2] = max(profile_maxima[2], excess)
            per_pitch_cells = Counter()
            for pitch, multiplicity, count in pitch_multiplicities:
                profile_multiplicities[multiplicity] += count * piece_count
                profile_pitch_multiplicities[(pitch, multiplicity)] += (
                    count * piece_count
                )
                per_pitch_cells[pitch] += count
            if any(
                cells_at_pitch > (self.maximum_grid_index or 0) + 1
                or cells_at_pitch
                > MAESTRO_WINDOW_LENGTH * collision_windows
                for cells_at_pitch in per_pitch_cells.values()
            ):
                raise ValueError(
                    "collision piece profile exceeds the per-pitch grid/window capacity"
                )
            if collision_windows > maximum_piece_windows:
                raise ValueError(
                    "collision piece-profile windows exceed the aggregate grid bound"
                )
        if (
            profile_piece_count != self.projection_collision_piece_count
            or profile_cells != self.projection_collision_cell_count
            or profile_events != self.projection_collision_event_count
            or profile_excess != self.projection_collision_excess_event_count
            or profile_windows != self.projection_collision_window_count
        ):
            raise ValueError("collision piece profiles do not match aggregate totals")
        if tuple(sorted(profile_piece_histogram.items())) != (
            self.projection_collision_piece_histogram
        ):
            raise ValueError("collision piece histogram disagrees with piece profiles")
        if tuple(sorted(profile_multiplicities.items())) != (
            self.projection_collision_multiplicity_histogram
        ):
            raise ValueError(
                "aggregate multiplicity histogram cannot be partitioned into "
                "the claimed collision-piece profiles"
            )
        expected_profile_pitch_multiplicities = tuple(
            (pitch, multiplicity, count)
            for (pitch, multiplicity), count in sorted(
                profile_pitch_multiplicities.items()
            )
        )
        if expected_profile_pitch_multiplicities != (
            self.projection_collision_pitch_multiplicity_histogram
        ):
            raise ValueError(
                "aggregate pitch-multiplicity histogram cannot be partitioned "
                "into the claimed collision-piece profiles"
            )
        if self.projection_collision_piece_count:
            claimed_maxima = (
                self.maximum_projection_collision_cells_per_piece,
                self.maximum_projection_collision_events_per_piece,
                self.maximum_projection_collision_excess_events_per_piece,
            )
            if tuple(profile_maxima) != claimed_maxima:
                raise ValueError("collision maxima disagree with piece profiles")
        if (
            sum(count for _, count in self.projection_collision_piece_histogram)
            != self.projection_collision_piece_count
            or sum(cells * count for cells, count in self.projection_collision_piece_histogram)
            != self.projection_collision_cell_count
        ):
            raise ValueError("collision piece histogram does not match totals")
        expected_maximum_cells = max(
            [cells for cells, _ in self.projection_collision_piece_histogram] or [0]
        )
        if self.maximum_projection_collision_cells_per_piece != expected_maximum_cells:
            raise ValueError("maximum collision cells per piece is inconsistent")
        if self.projection_collision_piece_count:
            if (
                self.maximum_projection_collision_cell_multiplicity
                > self.maximum_projection_collision_events_per_piece
            ):
                raise ValueError(
                    "maximum collision-cell multiplicity exceeds the per-piece event maximum"
                )
            if not (
                2 * self.maximum_projection_collision_cells_per_piece
                <= self.maximum_projection_collision_events_per_piece
                <= self.projection_collision_event_count
            ):
                raise ValueError("maximum collision events per piece is inconsistent")
            if not (
                self.maximum_projection_collision_cells_per_piece
                <= self.maximum_projection_collision_excess_events_per_piece
                <= self.projection_collision_excess_event_count
            ):
                raise ValueError("maximum collision excess per piece is inconsistent")
            if not (
                self.maximum_projection_collision_excess_events_per_piece + 1
                <= self.maximum_projection_collision_events_per_piece
                <= self.maximum_projection_collision_cells_per_piece
                + self.maximum_projection_collision_excess_events_per_piece
            ):
                raise ValueError("collision maxima cannot arise from one piece family")
            if (
                self.maximum_projection_collision_events_per_piece
                * self.projection_collision_piece_count
                < self.projection_collision_event_count
            ):
                raise ValueError("maximum collision events cannot cover aggregate total")
            if (
                self.maximum_projection_collision_excess_events_per_piece
                * self.projection_collision_piece_count
                < self.projection_collision_excess_event_count
            ):
                raise ValueError("maximum collision excess cannot cover aggregate total")
        if self.projection_collision_window_count > min(
            self.window_count, self.projection_collision_cell_count
        ):
            raise ValueError("aggregate collision windows exceed cells or windows")
        if self.projection_collision_window_count < self.projection_collision_piece_count:
            raise ValueError("every collided piece requires a collision window")
        for value in (
            self.out_of_88_key_piece_count,
            self.multiple_note_stream_piece_count,
            self.projection_collision_piece_count,
            self.empty_piece_count,
            self.window_ineligible_piece_count,
            self.projection_admitted_piece_count,
        ):
            if value > self.semantic_pass_count:
                raise ValueError("piece diagnostic exceeds semantic pass count")
        if self.window_ineligible_piece_count != self.empty_piece_count:
            raise ValueError("only empty semantic pieces are window-ineligible here")
        for blocker_count, blocker_name in (
            (self.empty_piece_count, "empty"),
            (self.out_of_88_key_piece_count, "out-of-support"),
            (self.multiple_note_stream_piece_count, "multi-stream"),
            (self.projection_collision_piece_count, "collided"),
        ):
            if self.projection_admitted_piece_count + blocker_count > self.semantic_pass_count:
                raise ValueError(
                    "projection-admitted and {} pieces must be disjoint".format(
                        blocker_name
                    )
                )
        nonadmitted_piece_count = (
            self.semantic_pass_count - self.projection_admitted_piece_count
        )
        blocker_total = (
            self.empty_piece_count
            + self.out_of_88_key_piece_count
            + self.multiple_note_stream_piece_count
            + self.projection_collision_piece_count
        )
        if nonadmitted_piece_count > blocker_total:
            raise ValueError(
                "every non-admitted piece requires at least one projection blocker"
            )

    @property
    def pedal_fact_count(self) -> int:
        return sum(count for _, count in self.pedal_controller_counts)

    def to_dict(self) -> Dict[str, object]:
        return {
            "scope": self.scope,
            "file_count": self.file_count,
            "semantic_pass_count": self.semantic_pass_count,
            "semantic_failure_count": self.semantic_failure_count,
            "failure_code_counts": dict(self.failure_code_counts),
            "orphan_closure_sensitivity_attempted_count": (
                self.orphan_closure_sensitivity_attempted_count
            ),
            "orphan_closure_sensitivity_admitted_count": (
                self.orphan_closure_sensitivity_admitted_count
            ),
            "orphan_closure_sensitivity_rejected_count": (
                self.orphan_closure_sensitivity_rejected_count
            ),
            "orphan_closure_sensitivity_rejection_code_counts": dict(
                self.orphan_closure_sensitivity_rejection_code_counts
            ),
            "orphan_closure_sensitivity_manifests_sha256": (
                self.orphan_closure_sensitivity_manifests_sha256
            ),
            "note_count": self.note_count,
            "pairing_evidence_piece_count": self.pairing_evidence_piece_count,
            "pairing_invariant_piece_count": self.pairing_invariant_piece_count,
            "pairing_representation_sensitive_piece_count": (
                self.pairing_representation_sensitive_piece_count
            ),
            "pairing_note_count": self.pairing_note_count,
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
            "simultaneous_same_identity_open_group_count": (
                self.simultaneous_same_identity_open_group_count
            ),
            "simultaneous_same_identity_open_event_count": (
                self.simultaneous_same_identity_open_event_count
            ),
            "simultaneous_same_identity_open_excess_count": (
                self.simultaneous_same_identity_open_excess_count
            ),
            "closure_spelling_counts": dict(self.closure_spelling_counts),
            "controller_count": self.controller_count,
            "pedal_fact_count": self.pedal_fact_count,
            "pedal_controller_counts": {
                str(key): count for key, count in self.pedal_controller_counts
            },
            "tempo_point_count": self.tempo_point_count,
            "explicit_tempo_event_count": self.explicit_tempo_event_count,
            "midi_port_event_count": self.midi_port_event_count,
            "time_signature_count": self.time_signature_count,
            "pitch_minimum": self.pitch_minimum,
            "pitch_maximum": self.pitch_maximum,
            "out_of_88_key_note_count": self.out_of_88_key_note_count,
            "out_of_88_key_piece_count": self.out_of_88_key_piece_count,
            "note_producing_stream_count": self.note_producing_stream_count,
            "multiple_note_stream_piece_count": self.multiple_note_stream_piece_count,
            "maximum_note_streams_per_piece": self.maximum_note_streams_per_piece,
            "projection_collision_cell_count": self.projection_collision_cell_count,
            "projection_collision_event_count": self.projection_collision_event_count,
            "projection_collision_excess_event_count": (
                self.projection_collision_excess_event_count
            ),
            "projection_collision_piece_count": self.projection_collision_piece_count,
            "projection_collision_by_pitch": [
                {
                    "pitch": pitch,
                    "cell_count": cells,
                    "event_count": events,
                    "excess_event_count": excess,
                }
                for pitch, cells, events, excess in self.projection_collision_by_pitch
            ],
            "projection_collision_pitch_multiplicity_histogram": [
                {
                    "pitch": pitch,
                    "cell_multiplicity": multiplicity,
                    "cell_count": count,
                }
                for pitch, multiplicity, count in (
                    self.projection_collision_pitch_multiplicity_histogram
                )
            ],
            "projection_collision_multiplicity_histogram": {
                str(multiplicity): count
                for multiplicity, count in (
                    self.projection_collision_multiplicity_histogram
                )
            },
            "maximum_projection_collision_cell_multiplicity": (
                self.maximum_projection_collision_cell_multiplicity
            ),
            "projection_collision_piece_histogram": {
                str(cells): count
                for cells, count in self.projection_collision_piece_histogram
            },
            "projection_collision_piece_profile_histogram": [
                {
                    "pitch_multiplicity_histogram": [
                        {
                            "pitch": pitch,
                            "cell_multiplicity": multiplicity,
                            "cell_count": count,
                        }
                        for pitch, multiplicity, count in pitch_multiplicities
                    ],
                    "collision_window_count": collision_windows,
                    "piece_count": piece_count,
                }
                for pitch_multiplicities, collision_windows, piece_count in (
                    self.projection_collision_piece_profile_histogram
                )
            ],
            "maximum_projection_collision_cells_per_piece": (
                self.maximum_projection_collision_cells_per_piece
            ),
            "maximum_projection_collision_events_per_piece": (
                self.maximum_projection_collision_events_per_piece
            ),
            "maximum_projection_collision_excess_events_per_piece": (
                self.maximum_projection_collision_excess_events_per_piece
            ),
            "projection_collision_window_count": self.projection_collision_window_count,
            "maximum_grid_index": self.maximum_grid_index,
            "window_count": self.window_count,
            "tail_retained_window_count": self.tail_retained_window_count,
            "empty_piece_count": self.empty_piece_count,
            "window_ineligible_piece_count": self.window_ineligible_piece_count,
            "projection_admitted_piece_count": self.projection_admitted_piece_count,
            "semantic_manifests_sha256": self.semantic_manifests_sha256,
            "pairing_sensitivity_manifests_sha256": (
                self.pairing_sensitivity_manifests_sha256
            ),
        }


def _semantic_digest(records: Sequence[MaestroSemanticFileEvidence], domain: bytes) -> str:
    payload = []
    for record in sorted(records, key=lambda item: item.sha256):
        payload.append(
            {
                "source_midi_sha256": record.sha256,
                "source_split": record.source_split,
                "status": record.status,
                "semantic_manifest_sha256": record.semantic_manifest_sha256,
                "failure_code": record.failure_code,
                "failure_detail_sha256": record.failure_detail_sha256,
            }
        )
    return sha256_bytes(domain + canonical_json_dumps(payload).encode("utf-8"))


def _pairing_digest(records: Sequence[MaestroSemanticFileEvidence], domain: bytes) -> str:
    payload = []
    for record in sorted(records, key=lambda item: item.sha256):
        payload.append(
            {
                "source_midi_sha256": record.sha256,
                "source_split": record.source_split,
                "status": record.status,
                "pairing_sensitivity_manifest_sha256": (
                    record.pairing_sensitivity_manifest_sha256
                ),
                "pairing_comparison_status": record.pairing_comparison_status,
                "failure_code": record.failure_code,
                "failure_detail_sha256": record.failure_detail_sha256,
            }
        )
    return sha256_bytes(domain + canonical_json_dumps(payload).encode("utf-8"))


def _orphan_sensitivity_digest(
    records: Sequence[MaestroSemanticFileEvidence], domain: bytes
) -> str:
    payload = []
    for record in sorted(
        records,
        key=lambda item: (
            item.sha256,
            item.source_split,
            item.metadata_row_number,
        ),
    ):
        if record.orphan_closure_sensitivity_status is None:
            continue
        payload.append(
            {
                "source_midi_sha256": record.sha256,
                "source_split": record.source_split,
                "status": record.orphan_closure_sensitivity_status,
                "rejection_code": (
                    record.orphan_closure_sensitivity_rejection_code
                ),
                "failure_detail_sha256": (
                    record.orphan_closure_sensitivity_failure_detail_sha256
                ),
                "manifest_sha256": (
                    record.orphan_closure_sensitivity_manifest_sha256
                ),
            }
        )
    return sha256_bytes(domain + canonical_json_dumps(payload).encode("utf-8"))


def _aggregate(
    records: Sequence[MaestroSemanticFileEvidence], *, scope: str
) -> MaestroSemanticAggregate:
    passed = [record for record in records if record.semantic_passed]
    pitches_min = [record.pitch_minimum for record in passed if record.pitch_minimum is not None]
    pitches_max = [record.pitch_maximum for record in passed if record.pitch_maximum is not None]
    grid_maxima = [
        record.maximum_grid_index
        for record in passed
        if record.maximum_grid_index is not None
    ]
    failures = Counter(
        record.failure_code for record in records if record.failure_code is not None
    )
    orphan_sensitivity_attempts = [
        record
        for record in records
        if record.orphan_closure_sensitivity_status is not None
    ]
    orphan_sensitivity_rejections = Counter(
        record.orphan_closure_sensitivity_rejection_code
        for record in orphan_sensitivity_attempts
        if record.orphan_closure_sensitivity_rejection_code is not None
    )
    closures = Counter()
    pedals = Counter()
    collision_cells_by_pitch = Counter()
    collision_events_by_pitch = Counter()
    collision_excess_by_pitch = Counter()
    collision_multiplicities = Counter()
    collision_pitch_multiplicities = Counter()
    for record in passed:
        closures.update(dict(record.closure_spelling_counts))
        pedals.update(dict(record.pedal_controller_counts))
        for pitch, cells, events, excess in record.projection_collision_by_pitch:
            collision_cells_by_pitch[pitch] += cells
            collision_events_by_pitch[pitch] += events
            collision_excess_by_pitch[pitch] += excess
        collision_multiplicities.update(
            dict(record.projection_collision_multiplicity_histogram)
        )
        for pitch, multiplicity, count in (
            record.projection_collision_pitch_multiplicity_histogram
        ):
            collision_pitch_multiplicities[(pitch, multiplicity)] += count
    collision_pieces = [
        record for record in passed if record.projection_collision_cell_count > 0
    ]
    collision_piece_histogram = Counter(
        record.projection_collision_cell_count for record in collision_pieces
    )
    collision_piece_profiles = Counter(
        (
            record.projection_collision_pitch_multiplicity_histogram,
            record.projection_collision_window_count,
        )
        for record in collision_pieces
    )
    return MaestroSemanticAggregate(
        scope=scope,
        file_count=len(records),
        semantic_pass_count=len(passed),
        semantic_failure_count=len(records) - len(passed),
        failure_code_counts=tuple(sorted(failures.items())),
        orphan_closure_sensitivity_attempted_count=len(
            orphan_sensitivity_attempts
        ),
        orphan_closure_sensitivity_admitted_count=sum(
            record.orphan_closure_sensitivity_status == "sensitivity_admitted"
            for record in orphan_sensitivity_attempts
        ),
        orphan_closure_sensitivity_rejected_count=sum(
            record.orphan_closure_sensitivity_status == "sensitivity_rejected"
            for record in orphan_sensitivity_attempts
        ),
        orphan_closure_sensitivity_rejection_code_counts=tuple(
            sorted(orphan_sensitivity_rejections.items())
        ),
        orphan_closure_sensitivity_manifests_sha256=_orphan_sensitivity_digest(
            records,
            _ORPHAN_SENSITIVITY_DIGEST_DOMAIN
            if scope == "all"
            else _ORPHAN_SENSITIVITY_SPLIT_DIGEST_DOMAIN
            + scope.encode("ascii")
            + b"\0",
        ),
        note_count=sum(record.note_count for record in passed),
        pairing_evidence_piece_count=sum(
            record.pairing_sensitivity_manifest_sha256 is not None
            for record in passed
        ),
        pairing_invariant_piece_count=sum(
            record.pairing_comparison_status == "pairing_invariant"
            for record in passed
        ),
        pairing_representation_sensitive_piece_count=sum(
            record.pairing_comparison_status == "representation_sensitive"
            for record in passed
        ),
        pairing_note_count=sum(record.pairing_note_count for record in passed),
        fifo_lifo_changed_pair_count=sum(
            record.fifo_lifo_changed_pair_count for record in passed
        ),
        fifo_lifo_changed_release_tick_count=sum(
            record.fifo_lifo_changed_release_tick_count for record in passed
        ),
        fifo_lifo_total_absolute_release_tick_difference=sum(
            record.fifo_lifo_total_absolute_release_tick_difference
            for record in passed
        ),
        retrigger_candidate_note_count=sum(
            record.retrigger_candidate_note_count for record in passed
        ),
        retrigger_truncated_note_count=sum(
            record.retrigger_truncated_note_count for record in passed
        ),
        retrigger_total_removed_duration_ticks=sum(
            record.retrigger_total_removed_duration_ticks for record in passed
        ),
        raw_close_same_tick_precedence_count=sum(
            record.raw_close_same_tick_precedence_count for record in passed
        ),
        simultaneous_same_identity_open_group_count=sum(
            record.simultaneous_same_identity_open_group_count for record in passed
        ),
        simultaneous_same_identity_open_event_count=sum(
            record.simultaneous_same_identity_open_event_count for record in passed
        ),
        simultaneous_same_identity_open_excess_count=sum(
            record.simultaneous_same_identity_open_excess_count for record in passed
        ),
        closure_spelling_counts=tuple(sorted(closures.items())),
        controller_count=sum(record.controller_count for record in passed),
        pedal_controller_counts=tuple(sorted(pedals.items())),
        tempo_point_count=sum(record.tempo_point_count for record in passed),
        explicit_tempo_event_count=sum(
            record.explicit_tempo_event_count for record in passed
        ),
        midi_port_event_count=sum(record.midi_port_event_count for record in passed),
        time_signature_count=sum(record.time_signature_count for record in passed),
        pitch_minimum=min(pitches_min) if pitches_min else None,
        pitch_maximum=max(pitches_max) if pitches_max else None,
        out_of_88_key_note_count=sum(
            record.out_of_88_key_note_count for record in passed
        ),
        out_of_88_key_piece_count=sum(
            record.out_of_88_key_note_count > 0 for record in passed
        ),
        note_producing_stream_count=sum(
            len(record.note_producing_streams) for record in passed
        ),
        multiple_note_stream_piece_count=sum(
            len(record.note_producing_streams) > 1 for record in passed
        ),
        maximum_note_streams_per_piece=max(
            [len(record.note_producing_streams) for record in passed] or [0]
        ),
        projection_collision_cell_count=sum(
            record.projection_collision_cell_count for record in passed
        ),
        projection_collision_event_count=sum(
            record.projection_collision_event_count for record in passed
        ),
        projection_collision_excess_event_count=sum(
            record.projection_collision_excess_event_count for record in passed
        ),
        projection_collision_piece_count=sum(
            record.projection_collision_cell_count > 0 for record in passed
        ),
        projection_collision_by_pitch=tuple(
            (
                pitch,
                collision_cells_by_pitch[pitch],
                collision_events_by_pitch[pitch],
                collision_excess_by_pitch[pitch],
            )
            for pitch in sorted(collision_cells_by_pitch)
        ),
        projection_collision_pitch_multiplicity_histogram=tuple(
            (pitch, multiplicity, collision_pitch_multiplicities[(pitch, multiplicity)])
            for pitch, multiplicity in sorted(collision_pitch_multiplicities)
        ),
        projection_collision_multiplicity_histogram=tuple(
            sorted(collision_multiplicities.items())
        ),
        maximum_projection_collision_cell_multiplicity=max(
            collision_multiplicities.keys(), default=0
        ),
        projection_collision_piece_histogram=tuple(
            sorted(collision_piece_histogram.items())
        ),
        projection_collision_piece_profile_histogram=tuple(
            (pitch_multiplicities, collision_windows, piece_count)
            for (pitch_multiplicities, collision_windows), piece_count in sorted(
                collision_piece_profiles.items()
            )
        ),
        maximum_projection_collision_cells_per_piece=max(
            [record.projection_collision_cell_count for record in collision_pieces]
            or [0]
        ),
        maximum_projection_collision_events_per_piece=max(
            [record.projection_collision_event_count for record in collision_pieces]
            or [0]
        ),
        maximum_projection_collision_excess_events_per_piece=max(
            [
                record.projection_collision_excess_event_count
                for record in collision_pieces
            ]
            or [0]
        ),
        projection_collision_window_count=sum(
            record.projection_collision_window_count for record in passed
        ),
        maximum_grid_index=max(grid_maxima) if grid_maxima else None,
        window_count=sum(record.window_count for record in passed),
        tail_retained_window_count=sum(
            record.tail_retained_window_count for record in passed
        ),
        empty_piece_count=sum(record.note_count == 0 for record in passed),
        window_ineligible_piece_count=sum(record.window_ineligible for record in passed),
        projection_admitted_piece_count=sum(
            record.projection_admitted for record in passed
        ),
        semantic_manifests_sha256=_semantic_digest(
            records, _SPLIT_DIGEST_DOMAIN + scope.encode("ascii") + b"\0"
        ),
        pairing_sensitivity_manifests_sha256=_pairing_digest(
            records,
            _PAIRING_SPLIT_DIGEST_DOMAIN + scope.encode("ascii") + b"\0",
        ),
    )


@dataclass(frozen=True)
class MaestroSemanticCorpusAudit:
    """Immutable private census and its canonical release-safe aggregate."""

    inventory_manifest_sha256: str
    raw_audit_sha256: str
    raw_oracle_version: str
    limits: MaestroSemanticLimits
    records: Tuple[MaestroSemanticFileEvidence, ...]
    aggregate: MaestroSemanticAggregate = field(init=False)
    source_split_aggregates: Tuple[MaestroSemanticAggregate, ...] = field(init=False)
    semantic_manifests_sha256: str = field(init=False)
    pairing_sensitivity_manifests_sha256: str = field(init=False)
    gate_status: str = field(init=False)
    census_sha256: str = field(init=False)
    public_summary_sha256: str = field(init=False)
    schema_version: int = field(default=_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        _sha256(self.inventory_manifest_sha256, name="inventory_manifest_sha256")
        _sha256(self.raw_audit_sha256, name="raw_audit_sha256")
        if self.raw_oracle_version != PINNED_MIDO_ORACLE_VERSION:
            raise ValueError("raw_oracle_version must equal the pinned version")
        if not isinstance(self.limits, MaestroSemanticLimits):
            raise TypeError("limits must be a MaestroSemanticLimits instance")
        if not isinstance(self.records, tuple):
            raise TypeError("records must be a tuple")
        if len(self.records) != MAESTRO_V3_EXPECTED_MIDI_FILES:
            raise ValueError(
                "semantic census must contain exactly {} records".format(
                    MAESTRO_V3_EXPECTED_MIDI_FILES
                )
            )
        if any(not isinstance(item, MaestroSemanticFileEvidence) for item in self.records):
            raise TypeError("records must contain MaestroSemanticFileEvidence values")
        records = tuple(sorted(self.records, key=lambda item: item.midi_path))
        if len({item.midi_path for item in records}) != len(records):
            raise ValueError("semantic census paths must be unique")
        if {item.metadata_row_number for item in records} != set(
            range(2, MAESTRO_V3_EXPECTED_MIDI_FILES + 2)
        ):
            raise ValueError("semantic census metadata rows must be exact")
        if {item.source_split for item in records} != _SOURCE_SPLIT_SET:
            raise ValueError("semantic census must retain all source splits")
        object.__setattr__(self, "records", records)
        aggregate = _aggregate(records, scope="all")
        splits = tuple(
            _aggregate(
                tuple(item for item in records if item.source_split == split),
                scope=split,
            )
            for split in _SOURCE_SPLITS
        )
        object.__setattr__(self, "aggregate", aggregate)
        object.__setattr__(self, "source_split_aggregates", splits)
        object.__setattr__(
            self,
            "semantic_manifests_sha256",
            _semantic_digest(records, _SEMANTIC_DIGEST_DOMAIN),
        )
        object.__setattr__(
            self,
            "pairing_sensitivity_manifests_sha256",
            _pairing_digest(records, _PAIRING_DIGEST_DOMAIN),
        )
        status = (
            "PRIMARY_PASS"
            if aggregate.semantic_failure_count == 0
            and aggregate.projection_admitted_piece_count == aggregate.file_count
            else "HOLD"
        )
        object.__setattr__(self, "gate_status", status)
        private_json = canonical_json_dumps(self._private_payload())
        object.__setattr__(
            self,
            "census_sha256",
            sha256_bytes(_PRIVATE_DIGEST_DOMAIN + private_json.encode("utf-8")),
        )
        public_json = canonical_json_dumps(self._public_payload())
        object.__setattr__(
            self,
            "public_summary_sha256",
            sha256_bytes(_PUBLIC_DIGEST_DOMAIN + public_json.encode("utf-8")),
        )

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset": "maestro-v3.0.0",
            "gate": MAESTRO_SEMANTIC_CORPUS_GATE,
            "inventory_manifest_sha256": self.inventory_manifest_sha256,
            "raw_audit_sha256": self.raw_audit_sha256,
            "raw_oracle_version": self.raw_oracle_version,
            "semantic_limits": _semantic_limits_dict(self.limits),
            "window_policy": {
                "length": MAESTRO_WINDOW_LENGTH,
                "stride": MAESTRO_WINDOW_LENGTH,
                "piece_concatenation": False,
                "tail_retained": True,
            },
            "records": [item.to_private_dict() for item in self.records],
            "aggregate": self.aggregate.to_dict(),
            "source_splits": [item.to_dict() for item in self.source_split_aggregates],
            "semantic_manifests_sha256": self.semantic_manifests_sha256,
            "pairing_sensitivity_manifests_sha256": (
                self.pairing_sensitivity_manifests_sha256
            ),
            "gate_status": self.gate_status,
        }

    def to_private_dict(self) -> Dict[str, object]:
        return self._private_payload()

    def to_private_json(self) -> str:
        return canonical_json_dumps(self._private_payload())

    def _public_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset": "maestro-v3.0.0",
            "gate": MAESTRO_SEMANTIC_CORPUS_GATE,
            "gate_status": self.gate_status,
            "inventory_manifest_sha256": self.inventory_manifest_sha256,
            "raw_audit_sha256": self.raw_audit_sha256,
            "semantic_manifests_sha256": self.semantic_manifests_sha256,
            "pairing_sensitivity_manifests_sha256": (
                self.pairing_sensitivity_manifests_sha256
            ),
            "raw_oracle": {
                "required": True,
                "distribution": "mido",
                "pinned_version": self.raw_oracle_version,
                "pass_count": MAESTRO_V3_EXPECTED_MIDI_FILES,
            },
            "semantic_limits": _semantic_limits_dict(self.limits),
            "window_policy": {
                "length": MAESTRO_WINDOW_LENGTH,
                "stride": MAESTRO_WINDOW_LENGTH,
                "piece_concatenation": False,
                "tail_retained": True,
                "grid": "exact PPQN/4 MIDI-clock grid, not a score grid",
            },
            "aggregate": self.aggregate.to_dict(),
            "source_splits": [item.to_dict() for item in self.source_split_aggregates],
            "privacy": {
                "trusted_root_included": False,
                "midi_paths_included": False,
                "composer_or_title_strings_included": False,
                "note_ids_included": False,
                "failure_details_included": False,
                "orphan_closure_sensitivity_failure_details_included": False,
                "per_file_rows_included": False,
                "pairing_assignments_included": False,
            },
            "claim_boundary": {
                "status_scope_is_primary_census_only": True,
                "overall_semantic_projection_gate_closed": False,
                "semantic_policy_failures_repaired_or_excluded": False,
                "pairing_sensitivity_completed_for_semantic_passes": True,
                "pairing_sensitivity_selected_as_primary_policy": False,
                "orphan_closure_sensitivity_attempted_for_each_primary_orphan_failure": True,
                "orphan_closure_sensitivity_selected_as_primary_policy": False,
                "orphan_closure_sensitivity_outcomes_change_primary_status": False,
                "projection_collisions_dropped_or_resolved": False,
                "lossy_tensor_emitted": False,
                "model_windows_materialized": False,
                "source_splits_reassigned": False,
                "training_ready_claimed": False,
            },
        }

    def public_summary(self) -> Mapping[str, object]:
        payload = self._public_payload()
        payload["public_summary_sha256"] = self.public_summary_sha256
        return payload


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
        raise MaestroSemanticCorpusAuditError("trusted_root must be absolute")
    try:
        status = candidate.lstat()
    except FileNotFoundError as error:
        raise MaestroSemanticCorpusAuditError("trusted_root does not exist") from error
    if stat.S_ISLNK(status.st_mode):
        raise MaestroSemanticCorpusAuditError("trusted_root must not be a symlink")
    if not stat.S_ISDIR(status.st_mode):
        raise MaestroSemanticCorpusAuditError("trusted_root must be a directory")
    return candidate, candidate.resolve(strict=True)


def _validated_path(
    root: Path,
    resolved_root: Path,
    record: MaestroMidiInventory,
) -> Tuple[Path, Tuple[int, int, int, int, int, int, int]]:
    candidate = root
    for index, component in enumerate(PurePosixPath(record.midi_path).parts):
        candidate = candidate / component
        try:
            status = candidate.lstat()
        except FileNotFoundError as error:
            raise MaestroSemanticCorpusAuditError(
                "inventoried MIDI file is missing at metadata row {}".format(
                    record.metadata_row_number
                )
            ) from error
        if stat.S_ISLNK(status.st_mode):
            raise MaestroSemanticCorpusAuditError(
                "inventoried MIDI path contains a symlink at metadata row {}".format(
                    record.metadata_row_number
                )
            )
        if index < len(PurePosixPath(record.midi_path).parts) - 1:
            if not stat.S_ISDIR(status.st_mode):
                raise MaestroSemanticCorpusAuditError(
                    "inventoried MIDI parent is not a directory"
                )
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        raise MaestroSemanticCorpusAuditError(
            "inventoried MIDI must be a singly-linked regular file at metadata row {}".format(
                record.metadata_row_number
            )
        )
    try:
        candidate.resolve(strict=True).relative_to(resolved_root)
    except ValueError as error:
        raise MaestroSemanticCorpusAuditError(
            "inventoried MIDI resolves outside trusted_root"
        ) from error
    return candidate, _stat_signature(status)


def _counter_pairs(counter: Counter) -> Tuple[Tuple[object, int], ...]:
    return tuple(sorted((key, value) for key, value in counter.items() if value))


def _assert_parsed_matches_raw(
    midi: MidiFile,
    inventory_record: MaestroMidiInventory,
    raw_record: MaestroRawMidiFileEvidence,
) -> None:
    if (
        midi.sha256 != inventory_record.sha256
        or midi.sha256 != raw_record.sha256
        or midi.byte_length != inventory_record.size_bytes
        or midi.byte_length != raw_record.size_bytes
    ):
        raise MaestroSemanticCorpusAuditError(
            "MIDI byte identity disagrees with inventory/raw evidence at metadata row {}".format(
                inventory_record.metadata_row_number
            )
        )
    direct = (
        midi.format_type,
        midi.ticks_per_quarter_note,
        tuple(len(track.events) for track in midi.tracks),
        tuple(track.byte_length for track in midi.tracks),
        tuple(track.end_tick for track in midi.tracks),
    )
    expected = (
        raw_record.format_type,
        raw_record.ticks_per_quarter_note,
        raw_record.track_event_counts,
        raw_record.track_byte_lengths,
        raw_record.track_end_ticks,
    )
    if direct != expected:
        raise MaestroSemanticCorpusAuditError(
            "raw header/track evidence disagrees at metadata row {}".format(
                inventory_record.metadata_row_number
            )
        )

    categories = Counter()
    channels = Counter()
    meta_types = Counter()
    controllers = Counter()
    pedal_values = Counter()
    sysex_statuses = Counter()
    running_status = 0
    zero_velocity = 0
    maximum_delta = 0
    maximum_absolute = 0
    maximum_payload = 0
    for track in midi.tracks:
        for event in track.events:
            maximum_delta = max(maximum_delta, event.delta_ticks)
            maximum_absolute = max(maximum_absolute, event.absolute_ticks)
            if isinstance(event, MidiChannelEvent):
                categories["channel"] += 1
                channels[event.message_type] += 1
                maximum_payload = max(maximum_payload, len(event.data))
                running_status += int(event.used_running_status)
                zero_velocity += int(event.message_type == "note_on" and event.velocity == 0)
                if event.message_type == "control_change":
                    if event.controller is None or event.controller_value is None:
                        raise AssertionError("control-change raw fields are absent")
                    controllers[event.controller] += 1
                    if event.controller in _PEDAL_CONTROLLERS:
                        pedal_values[(event.controller, event.controller_value)] += 1
            elif isinstance(event, MidiMetaEvent):
                categories["meta"] += 1
                meta_types[event.meta_type] += 1
                maximum_payload = max(maximum_payload, len(event.payload))
            elif isinstance(event, MidiSysExEvent):
                categories["sysex"] += 1
                sysex_statuses[event.status] += 1
                maximum_payload = max(maximum_payload, len(event.payload))
            else:
                raise AssertionError("unknown raw MIDI event class")
    observed = (
        _counter_pairs(categories),
        _counter_pairs(channels),
        _counter_pairs(meta_types),
        _counter_pairs(controllers),
        tuple(
            (controller, value, count)
            for (controller, value), count in sorted(pedal_values.items())
        ),
        _counter_pairs(sysex_statuses),
        running_status,
        zero_velocity,
        maximum_delta,
        maximum_absolute,
        maximum_payload,
    )
    expected_counts = (
        raw_record.event_category_counts,
        raw_record.channel_message_counts,
        raw_record.meta_type_counts,
        raw_record.controller_counts,
        raw_record.pedal_controller_value_counts,
        raw_record.sysex_status_counts,
        raw_record.running_status_event_count,
        raw_record.note_on_velocity_zero_count,
        raw_record.maximum_delta_ticks,
        raw_record.maximum_absolute_ticks,
        raw_record.maximum_event_payload_bytes,
    )
    if observed != expected_counts:
        raise MaestroSemanticCorpusAuditError(
            "raw event evidence disagrees at metadata row {}".format(
                inventory_record.metadata_row_number
            )
        )


def _pass_evidence(
    record: MaestroMidiInventory,
    piece: MaestroSemanticPiece,
    pairing: MaestroNotePairingSensitivityAudit,
) -> MaestroSemanticFileEvidence:
    if not isinstance(pairing, MaestroNotePairingSensitivityAudit):
        raise TypeError("pairing must be a MaestroNotePairingSensitivityAudit")
    if (
        pairing.source_split != record.source_split
        or pairing.source_midi_sha256 != record.sha256
        or pairing.primary_semantic_manifest_sha256 != piece.manifest_sha256
        or len(pairing.fifo_pairs) != len(piece.notes)
    ):
        raise MaestroSemanticCorpusAuditError(
            "pairing sensitivity does not bind the semantic piece and inventory row"
        )
    closures = Counter(note.closure_spelling for note in piece.notes)
    pedals = Counter(
        item.controller for item in piece.controllers if item.controller in _PEDAL_CONTROLLERS
    )
    maximum_grid_index = max((note.grid_index for note in piece.notes), default=None)
    if maximum_grid_index is None:
        window_count = 0
        tail_count = 0
    else:
        window_count, remainder = divmod(
            maximum_grid_index + 1, MAESTRO_WINDOW_LENGTH
        )
        window_count += int(bool(remainder))
        tail_count = int(bool(remainder))
    collision_windows = {
        collision.grid_index // MAESTRO_WINDOW_LENGTH
        for collision in piece.diagnostics.projection_collisions
    }
    collision_cells_by_pitch = Counter()
    collision_events_by_pitch = Counter()
    collision_multiplicities = Counter()
    collision_pitch_multiplicities = Counter()
    for collision in piece.diagnostics.projection_collisions:
        collision_cells_by_pitch[collision.pitch] += 1
        multiplicity = len(collision.note_ids)
        collision_events_by_pitch[collision.pitch] += multiplicity
        collision_multiplicities[multiplicity] += 1
        collision_pitch_multiplicities[(collision.pitch, multiplicity)] += 1
    collision_by_pitch = tuple(
        (
            pitch,
            collision_cells_by_pitch[pitch],
            collision_events_by_pitch[pitch],
            collision_events_by_pitch[pitch] - collision_cells_by_pitch[pitch],
        )
        for pitch in sorted(collision_cells_by_pitch)
    )
    return MaestroSemanticFileEvidence(
        metadata_row_number=record.metadata_row_number,
        midi_path=record.midi_path,
        source_split=record.source_split,
        sha256=record.sha256,
        size_bytes=record.size_bytes,
        status="pass",
        semantic_manifest_sha256=piece.manifest_sha256,
        pairing_sensitivity_manifest_sha256=pairing.manifest_sha256,
        pairing_comparison_status=pairing.comparison_status,
        note_count=len(piece.notes),
        pairing_note_count=len(pairing.fifo_pairs),
        fifo_lifo_changed_pair_count=pairing.fifo_lifo_changed_pair_count,
        fifo_lifo_changed_release_tick_count=(
            pairing.fifo_lifo_changed_release_tick_count
        ),
        fifo_lifo_total_absolute_release_tick_difference=(
            pairing.fifo_lifo_total_absolute_release_tick_difference
        ),
        retrigger_candidate_note_count=pairing.retrigger_candidate_note_count,
        retrigger_truncated_note_count=pairing.retrigger_truncated_note_count,
        retrigger_total_removed_duration_ticks=(
            pairing.retrigger_total_removed_duration_ticks
        ),
        raw_close_same_tick_precedence_count=(
            pairing.raw_close_same_tick_precedence_count
        ),
        simultaneous_same_identity_open_group_count=(
            pairing.simultaneous_same_identity_open_group_count
        ),
        simultaneous_same_identity_open_event_count=(
            pairing.simultaneous_same_identity_open_event_count
        ),
        simultaneous_same_identity_open_excess_count=(
            pairing.simultaneous_same_identity_open_excess_count
        ),
        closure_spelling_counts=tuple(sorted(closures.items())),
        controller_count=len(piece.controllers),
        pedal_controller_counts=tuple(sorted(pedals.items())),
        tempo_point_count=len(piece.tempo_map.points),
        explicit_tempo_event_count=piece.tempo_map.explicit_event_count,
        midi_port_event_count=len(piece.midi_ports),
        time_signature_count=len(piece.time_signatures),
        pitch_minimum=piece.diagnostics.pitch_minimum,
        pitch_maximum=piece.diagnostics.pitch_maximum,
        out_of_88_key_note_count=piece.diagnostics.out_of_88_key_note_count,
        note_producing_streams=piece.diagnostics.note_producing_streams,
        projection_collision_cell_count=len(piece.diagnostics.projection_collisions),
        projection_collision_event_count=piece.diagnostics.collision_event_count,
        projection_collision_excess_event_count=(
            piece.diagnostics.collision_excess_event_count
        ),
        projection_collision_by_pitch=collision_by_pitch,
        projection_collision_pitch_multiplicity_histogram=tuple(
            (pitch, multiplicity, count)
            for (pitch, multiplicity), count in sorted(
                collision_pitch_multiplicities.items()
            )
        ),
        projection_collision_multiplicity_histogram=tuple(
            sorted(collision_multiplicities.items())
        ),
        maximum_projection_collision_cell_multiplicity=max(
            collision_multiplicities.keys(), default=0
        ),
        projection_collision_window_count=len(collision_windows),
        maximum_grid_index=maximum_grid_index,
        window_count=window_count,
        tail_retained_window_count=tail_count,
        window_ineligible=not piece.notes,
        projection_admitted=piece.diagnostics.manuscript_projection_admitted,
    )


def _failure_evidence(
    record: MaestroMidiInventory,
    error: MaestroSemanticError,
    orphan_sensitivity: Optional[MaestroOrphanClosureSensitivityAudit] = None,
) -> MaestroSemanticFileEvidence:
    detail = str(error)
    failure_code = error.code
    sensitivity_fields: Dict[str, object] = {}
    if orphan_sensitivity is not None:
        if type(orphan_sensitivity) is not MaestroOrphanClosureSensitivityAudit:
            raise TypeError(
                "orphan_sensitivity must be an exact MaestroOrphanClosureSensitivityAudit"
            )
        if (
            failure_code != "ORPHAN_NOTE_CLOSURE"
            or orphan_sensitivity.primary_failure_code != failure_code
            or orphan_sensitivity.primary_failure_detail != detail
            or orphan_sensitivity.source_split != record.source_split
            or orphan_sensitivity.source_midi_sha256 != record.sha256
            or orphan_sensitivity.source_byte_length != record.size_bytes
        ):
            raise MaestroSemanticCorpusAuditError(
                "orphan-closure sensitivity audit does not bind the primary failure"
            )
        public_sensitivity = orphan_sensitivity.public_summary()
        sensitivity_fields = {
            "orphan_closure_sensitivity_status": orphan_sensitivity.status,
            "orphan_closure_sensitivity_rejection_code": (
                orphan_sensitivity.rejection_code
            ),
            "orphan_closure_sensitivity_failure_detail_sha256": (
                public_sensitivity["sensitivity_failure_detail_sha256"]
            ),
            "orphan_closure_sensitivity_manifest_sha256": (
                orphan_sensitivity.manifest_sha256
            ),
        }
    elif failure_code == "ORPHAN_NOTE_CLOSURE":
        raise MaestroSemanticCorpusAuditError(
            "orphan-note-closure failure lacks its named sensitivity audit"
        )
    return MaestroSemanticFileEvidence(
        metadata_row_number=record.metadata_row_number,
        midi_path=record.midi_path,
        source_split=record.source_split,
        sha256=record.sha256,
        size_bytes=record.size_bytes,
        status="semantic_failure",
        failure_code=failure_code,
        failure_detail=detail,
        failure_detail_sha256=sha256_bytes(detail.encode("utf-8")),
        **sensitivity_fields,
    )


def audit_maestro_v3_semantic_corpus(
    inventory: MaestroArchiveInventory,
    raw_audit: MaestroRawMidiAudit,
    trusted_root: PathLike,
    *,
    limits: MaestroSemanticLimits,
) -> MaestroSemanticCorpusAudit:
    """Run the strict sequential semantic census over all 1,276 MIDI files.

    The raw differential oracle is mandatory at this gate.  Semantic-policy
    errors are accumulated; every other mismatch, including a pairing-sidecar
    replay failure, raises and returns no partial result.  ``limits`` has no
    default so every corpus run records an explicit semantic resource policy.
    """

    if not isinstance(inventory, MaestroArchiveInventory):
        raise TypeError("inventory must be a MaestroArchiveInventory")
    if not isinstance(raw_audit, MaestroRawMidiAudit):
        raise TypeError("raw_audit must be a MaestroRawMidiAudit")
    if not isinstance(limits, MaestroSemanticLimits):
        raise TypeError("limits must be a MaestroSemanticLimits instance")
    if raw_audit.inventory_manifest_sha256 != inventory.manifest_sha256:
        raise MaestroSemanticCorpusAuditError(
            "raw audit does not commit to the supplied inventory manifest"
        )
    if (
        not raw_audit.oracle_required
        or raw_audit.oracle_version != PINNED_MIDO_ORACLE_VERSION
        or raw_audit.aggregate.oracle_pass_count != MAESTRO_V3_EXPECTED_MIDI_FILES
        or any(not item.oracle_passed for item in raw_audit.records)
    ):
        raise MaestroSemanticCorpusAuditError(
            "semantic corpus gate requires the pinned full-corpus Mido oracle"
        )

    inventory_by_path = {record.midi_path: record for record in inventory.records}
    raw_by_path = {record.midi_path: record for record in raw_audit.records}
    if set(inventory_by_path) != set(raw_by_path):
        raise MaestroSemanticCorpusAuditError(
            "inventory and raw audit do not identify the same MIDI paths"
        )
    for path in sorted(inventory_by_path):
        record = inventory_by_path[path]
        raw_record = raw_by_path[path]
        if (
            raw_record.metadata_row_number != record.metadata_row_number
            or raw_record.source_split != record.source_split
            or raw_record.sha256 != record.sha256
            or raw_record.size_bytes != record.size_bytes
        ):
            raise MaestroSemanticCorpusAuditError(
                "inventory/raw identity mismatch at metadata row {}".format(
                    record.metadata_row_number
                )
            )

    root, resolved_root = _validate_root(trusted_root)
    preflight = []
    for record in inventory.records:
        path, signature = _validated_path(root, resolved_root, record)
        if signature[4] != record.size_bytes:
            raise MaestroSemanticCorpusAuditError(
                "MIDI size changed after raw audit at metadata row {}".format(
                    record.metadata_row_number
                )
            )
        preflight.append((record, raw_by_path[record.midi_path], path, signature))

    evidence: List[MaestroSemanticFileEvidence] = []
    for record, raw_record, path, signature in preflight:
        try:
            midi = load_midi_file(path, limits=raw_audit.limits)
        except MidiFormatError as error:
            raise MaestroSemanticCorpusAuditError(
                "raw MIDI reopen failed at metadata row {}".format(
                    record.metadata_row_number
                )
            ) from error
        _assert_parsed_matches_raw(midi, record, raw_record)
        try:
            piece = build_maestro_semantics_for_inventory_record(
                midi,
                record,
                limits=limits,
            )
        except MaestroSemanticError as error:
            orphan_sensitivity = None
            if error.code == "ORPHAN_NOTE_CLOSURE":
                try:
                    orphan_sensitivity = (
                        audit_maestro_orphan_closure_sensitivity_for_inventory_record(
                            midi,
                            record,
                            limits=limits,
                            source_limits=raw_audit.limits,
                        )
                    )
                except MaestroOrphanClosureSensitivityError as sensitivity_error:
                    raise MaestroSemanticCorpusAuditError(
                        "orphan-closure sensitivity audit failed at metadata row {}".format(
                            record.metadata_row_number
                        )
                    ) from sensitivity_error
            evidence.append(
                _failure_evidence(record, error, orphan_sensitivity)
            )
        else:
            try:
                pairing = audit_maestro_note_pairing_sensitivities(
                    midi,
                    piece,
                    limits=limits,
                )
            except MaestroPairingSensitivityError as error:
                raise MaestroSemanticCorpusAuditError(
                    "pairing-sensitivity replay failed at metadata row {}".format(
                        record.metadata_row_number
                    )
                ) from error
            evidence.append(_pass_evidence(record, piece, pairing))
            del pairing
            del piece
        del midi
        try:
            after = path.lstat()
        except FileNotFoundError as error:
            raise MaestroSemanticCorpusAuditError(
                "MIDI file disappeared during semantic census"
            ) from error
        if _stat_signature(after) != signature:
            raise MaestroSemanticCorpusAuditError(
                "MIDI file changed during semantic census at metadata row {}".format(
                    record.metadata_row_number
                )
            )

    for record, _raw_record, expected_path, signature in preflight:
        final_path, final_signature = _validated_path(root, resolved_root, record)
        if final_path != expected_path or final_signature != signature:
            raise MaestroSemanticCorpusAuditError(
                "MIDI corpus changed during semantic census at metadata row {}".format(
                    record.metadata_row_number
                )
            )

    return MaestroSemanticCorpusAudit(
        inventory_manifest_sha256=inventory.manifest_sha256,
        raw_audit_sha256=raw_audit.audit_sha256,
        raw_oracle_version=PINNED_MIDO_ORACLE_VERSION,
        limits=limits,
        records=tuple(evidence),
    )


__all__ = [
    "MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_MANIFESTS_DIGEST_DOMAIN",
    "MAESTRO_ORPHAN_CLOSURE_SENSITIVITY_SPLIT_DIGEST_DOMAIN",
    "MAESTRO_WINDOW_LENGTH",
    "MaestroSemanticAggregate",
    "MaestroSemanticCorpusAudit",
    "MaestroSemanticCorpusAuditError",
    "MaestroSemanticFileEvidence",
    "audit_maestro_v3_semantic_corpus",
]
