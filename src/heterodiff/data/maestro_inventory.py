"""Policy-free MAESTRO v3.0.0 metadata and MIDI-file inventory.

This module establishes an acquisition boundary only.  It verifies the exact
metadata table and the byte identity of every referenced MIDI file, while
retaining the release's source split labels unchanged.  It does not open MIDI
content, require audio, infer notes, construct model events, or choose new
train/validation/test assignments.

Composer, title, and file-path strings are needed in the local manifest to
audit exact-composition overlap.  They are deliberately omitted from
``public_summary`` so malformed source strings cannot be copied into a
release-facing report by accident.
"""

from __future__ import annotations

import csv
import os
import re
import stat
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

from heterodiff.artifacts.manifest import (
    ArtifactChecksum,
    DatasetProvenance,
    canonical_json_dumps,
    sha256_bytes,
)


PathLike = Union[str, os.PathLike]

MAESTRO_V3_METADATA_FILENAME = "maestro-v3.0.0.csv"
MAESTRO_V3_EXPECTED_MIDI_FILES = 1276
MAESTRO_V3_METADATA_HEADER = (
    "canonical_composer",
    "canonical_title",
    "split",
    "year",
    "midi_filename",
    "audio_filename",
    "duration",
)
MAESTRO_V3_SOURCE_SPLITS = ("test", "train", "validation")

_SOURCE_SPLIT_SET = frozenset(MAESTRO_V3_SOURCE_SPLITS)
_YEAR_PATTERN = re.compile(r"[0-9]{4}\Z")
_DURATION_PATTERN = re.compile(r"[0-9]+(?:\.[0-9]+)?\Z")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_DATASET_NAME = "maestro-v3.0.0-policy-free-midi-inventory"
_SPLIT_DIGEST_DOMAIN = b"heterodiff-maestro-v3-source-split-v1\0"


class MaestroInventoryError(ValueError):
    """Raised when the declared MAESTRO acquisition violates this boundary."""


def _positive_integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{} must be an integer".format(name))
    if value <= 0:
        raise ValueError("{} must be positive".format(name))
    return value


def _strict_source_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(field_name))
    if not value:
        raise MaestroInventoryError("{} must not be empty".format(field_name))
    if unicodedata.normalize("NFC", value) != value:
        raise MaestroInventoryError("{} must use NFC Unicode".format(field_name))
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise MaestroInventoryError(
            "{} must contain valid Unicode".format(field_name)
        ) from error
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise MaestroInventoryError(
            "{} must not contain NUL or newlines".format(field_name)
        )
    return value


def _relative_source_path(
    value: object,
    *,
    field_name: str,
    suffix: str,
    max_components: Optional[int] = None,
) -> str:
    path = _strict_source_text(value, field_name=field_name)
    if "\\" in path:
        raise MaestroInventoryError(
            "{} must use POSIX '/' separators".format(field_name)
        )
    if path.startswith("/"):
        raise MaestroInventoryError("{} must be relative".format(field_name))
    components = path.split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise MaestroInventoryError(
            "{} must not contain empty, '.' or '..' components".format(field_name)
        )
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or str(parsed) != path:
        raise MaestroInventoryError(
            "{} must be a canonical relative POSIX path".format(field_name)
        )
    if parsed.suffix != suffix:
        raise MaestroInventoryError(
            "{} must end in {!r}".format(field_name, suffix)
        )
    if max_components is not None and len(components) > max_components:
        raise MaestroInventoryError(
            "{} exceeds max_path_components".format(field_name)
        )
    return path


def _source_split(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("source_split must be a string")
    if value not in _SOURCE_SPLIT_SET:
        raise MaestroInventoryError(
            "source split must be one of {} and must not be relabeled".format(
                ", ".join(MAESTRO_V3_SOURCE_SPLITS)
            )
        )
    return value


def _year_text(value: object) -> str:
    if not isinstance(value, str) or _YEAR_PATTERN.fullmatch(value) is None:
        raise MaestroInventoryError("year must be exactly four ASCII digits")
    return value


def _duration_text(value: object) -> str:
    if not isinstance(value, str) or _DURATION_PATTERN.fullmatch(value) is None:
        raise MaestroInventoryError(
            "duration must be a nonnegative base-10 integer or decimal string"
        )
    return value


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


@dataclass(frozen=True)
class MaestroInventoryLimits:
    """Explicit bounds for metadata parsing and MIDI checksumming."""

    max_metadata_bytes: int = 64 * 1024 * 1024
    max_metadata_rows: int = 10_000
    max_midi_files: int = 10_000
    max_midi_file_bytes: int = 64 * 1024 * 1024
    max_total_midi_bytes: int = 8 * 1024 * 1024 * 1024
    max_field_characters: int = 16_384
    max_path_components: int = 64

    def __post_init__(self) -> None:
        for name in (
            "max_metadata_bytes",
            "max_metadata_rows",
            "max_midi_files",
            "max_midi_file_bytes",
            "max_total_midi_bytes",
            "max_field_characters",
            "max_path_components",
        ):
            _positive_integer(getattr(self, name), name=name)


@dataclass(frozen=True)
class MaestroV3InventoryInput:
    """One trusted root plus the exact metadata CSV selected by the caller."""

    root: PathLike
    metadata_csv: PathLike

    def __post_init__(self) -> None:
        if not isinstance(self.root, (str, os.PathLike)):
            raise TypeError("root must be a string or path-like object")
        if not isinstance(self.metadata_csv, (str, os.PathLike)):
            raise TypeError("metadata_csv must be a string or path-like object")
        root = Path(self.root)
        metadata_csv = Path(self.metadata_csv)
        if not root.is_absolute():
            raise MaestroInventoryError("root must be an absolute trusted path")
        if not metadata_csv.is_absolute():
            raise MaestroInventoryError("metadata_csv must be an absolute exact path")
        try:
            relative = metadata_csv.relative_to(root)
        except ValueError as error:
            raise MaestroInventoryError(
                "metadata_csv must be located within the trusted root"
            ) from error
        if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
            raise MaestroInventoryError(
                "metadata_csv must be a canonical child of the trusted root"
            )
        if metadata_csv.name != MAESTRO_V3_METADATA_FILENAME:
            raise MaestroInventoryError(
                "metadata_csv must be the explicit {!r} table".format(
                    MAESTRO_V3_METADATA_FILENAME
                )
            )
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "metadata_csv", metadata_csv)


@dataclass(frozen=True)
class MaestroMidiInventory:
    """Private row/file evidence; source strings must not be published directly."""

    metadata_row_number: int
    canonical_composer: str
    canonical_title: str
    source_split: str
    year: str
    midi_path: str
    audio_path: str
    duration: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.metadata_row_number, bool)
            or not isinstance(self.metadata_row_number, int)
            or self.metadata_row_number < 2
        ):
            raise ValueError("metadata_row_number must be an integer of at least 2")
        object.__setattr__(
            self,
            "canonical_composer",
            _strict_source_text(
                self.canonical_composer, field_name="canonical_composer"
            ),
        )
        object.__setattr__(
            self,
            "canonical_title",
            _strict_source_text(self.canonical_title, field_name="canonical_title"),
        )
        object.__setattr__(self, "source_split", _source_split(self.source_split))
        object.__setattr__(self, "year", _year_text(self.year))
        object.__setattr__(
            self,
            "midi_path",
            _relative_source_path(
                self.midi_path, field_name="midi_filename", suffix=".midi"
            ),
        )
        object.__setattr__(
            self,
            "audio_path",
            _relative_source_path(
                self.audio_path, field_name="audio_filename", suffix=".wav"
            ),
        )
        object.__setattr__(self, "duration", _duration_text(self.duration))
        if not isinstance(self.sha256, str) or _SHA256_PATTERN.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be a lowercase 64-character digest")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise TypeError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be nonnegative")

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "metadata_row_number": self.metadata_row_number,
            "canonical_composer": self.canonical_composer,
            "canonical_title": self.canonical_title,
            "source_split": self.source_split,
            "year": self.year,
            "midi_path": self.midi_path,
            "audio_path": self.audio_path,
            "duration": self.duration,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class MaestroCompositionCollision:
    """An exact canonical-composer/title key observed in multiple source splits."""

    canonical_composer: str
    canonical_title: str
    source_splits: Tuple[str, ...]
    midi_paths: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_composer",
            _strict_source_text(
                self.canonical_composer, field_name="canonical_composer"
            ),
        )
        object.__setattr__(
            self,
            "canonical_title",
            _strict_source_text(self.canonical_title, field_name="canonical_title"),
        )
        splits = tuple(_source_split(value) for value in self.source_splits)
        if splits != tuple(sorted(set(splits))) or len(splits) < 2:
            raise ValueError("source_splits must be sorted, unique, and cross-split")
        paths = tuple(
            _relative_source_path(value, field_name="midi_filename", suffix=".midi")
            for value in self.midi_paths
        )
        if paths != tuple(sorted(set(paths))) or len(paths) < 2:
            raise ValueError("midi_paths must be sorted and unique")
        object.__setattr__(self, "source_splits", splits)
        object.__setattr__(self, "midi_paths", paths)

    def to_private_dict(self) -> Dict[str, object]:
        return {
            "canonical_composer": self.canonical_composer,
            "canonical_title": self.canonical_title,
            "source_splits": list(self.source_splits),
            "midi_paths": list(self.midi_paths),
        }


def _split_digest(records: Sequence[MaestroMidiInventory]) -> str:
    payload = [record.to_private_dict() for record in records]
    payload.sort(key=canonical_json_dumps)
    return sha256_bytes(
        _SPLIT_DIGEST_DOMAIN
        + canonical_json_dumps(payload).encode("utf-8")
    )


def _composition_collisions(
    records: Sequence[MaestroMidiInventory],
) -> Tuple[MaestroCompositionCollision, ...]:
    grouped: Dict[Tuple[str, str], List[MaestroMidiInventory]] = {}
    for record in records:
        grouped.setdefault(
            (record.canonical_composer, record.canonical_title), []
        ).append(record)
    collisions = []
    for key in sorted(grouped):
        members = grouped[key]
        splits = tuple(sorted({member.source_split for member in members}))
        if len(splits) < 2:
            continue
        collisions.append(
            MaestroCompositionCollision(
                canonical_composer=key[0],
                canonical_title=key[1],
                source_splits=splits,
                midi_paths=tuple(sorted(member.midi_path for member in members)),
            )
        )
    return tuple(collisions)


@dataclass(frozen=True)
class MaestroArchiveInventory:
    """Deterministic private manifest with a release-safe aggregate view."""

    metadata_checksum: ArtifactChecksum
    records: Tuple[MaestroMidiInventory, ...]
    source_split_digests: Tuple[DatasetProvenance, ...] = field(init=False)
    composition_collisions: Tuple[MaestroCompositionCollision, ...] = field(init=False)
    manifest_sha256: str = field(init=False)
    schema_version: int = field(default=1, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.metadata_checksum, ArtifactChecksum):
            raise TypeError("metadata_checksum must be an ArtifactChecksum")
        if PurePosixPath(self.metadata_checksum.path).name != MAESTRO_V3_METADATA_FILENAME:
            raise ValueError("metadata checksum must identify the v3.0.0 metadata table")
        records = tuple(self.records)
        if len(records) != MAESTRO_V3_EXPECTED_MIDI_FILES:
            raise MaestroInventoryError(
                "inventory must contain exactly {} MIDI records".format(
                    MAESTRO_V3_EXPECTED_MIDI_FILES
                )
            )
        if any(not isinstance(record, MaestroMidiInventory) for record in records):
            raise TypeError("records must contain MaestroMidiInventory values")
        records = tuple(sorted(records, key=lambda record: record.midi_path))

        seen_rows: Dict[int, str] = {}
        seen_midi_paths: Dict[str, str] = {}
        seen_audio_paths: Dict[str, str] = {}
        seen_content: Dict[Tuple[str, int], str] = {}
        for record in records:
            previous_row = seen_rows.get(record.metadata_row_number)
            if previous_row is not None:
                raise MaestroInventoryError(
                    "duplicate metadata row number {}".format(record.metadata_row_number)
                )
            seen_rows[record.metadata_row_number] = record.midi_path
            midi_key = record.midi_path.casefold()
            previous_midi = seen_midi_paths.get(midi_key)
            if previous_midi is not None:
                raise MaestroInventoryError(
                    "MIDI paths collide under Unicode/case normalization: {!r} and {!r}".format(
                        previous_midi, record.midi_path
                    )
                )
            seen_midi_paths[midi_key] = record.midi_path
            audio_key = record.audio_path.casefold()
            previous_audio = seen_audio_paths.get(audio_key)
            if previous_audio is not None:
                raise MaestroInventoryError(
                    "audio paths collide under Unicode/case normalization: {!r} and {!r}".format(
                        previous_audio, record.audio_path
                    )
                )
            seen_audio_paths[audio_key] = record.audio_path
            content_key = (record.sha256, record.size_bytes)
            previous_content = seen_content.get(content_key)
            if previous_content is not None:
                raise MaestroInventoryError(
                    "MIDI files have duplicate exact content digests: {!r} and {!r}".format(
                        previous_content, record.midi_path
                    )
                )
            seen_content[content_key] = record.midi_path

        expected_row_numbers = set(
            range(2, MAESTRO_V3_EXPECTED_MIDI_FILES + 2)
        )
        if set(seen_rows) != expected_row_numbers:
            raise MaestroInventoryError(
                "metadata_row_number values must be exactly 2 through {}".format(
                    MAESTRO_V3_EXPECTED_MIDI_FILES + 1
                )
            )

        observed_splits = {record.source_split for record in records}
        if observed_splits != _SOURCE_SPLIT_SET:
            raise MaestroInventoryError(
                "metadata must retain all three official source split labels"
            )
        object.__setattr__(self, "records", records)

        provenances = []
        for split in MAESTRO_V3_SOURCE_SPLITS:
            members = tuple(record for record in records if record.source_split == split)
            provenances.append(
                DatasetProvenance(
                    name=_DATASET_NAME,
                    split=split,
                    sha256=_split_digest(members),
                )
            )
        object.__setattr__(self, "source_split_digests", tuple(provenances))
        object.__setattr__(self, "composition_collisions", _composition_collisions(records))
        private_json = canonical_json_dumps(self._private_payload())
        object.__setattr__(self, "manifest_sha256", sha256_bytes(private_json.encode("utf-8")))

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset": _DATASET_NAME,
            "gate": "policy-free-maestro-v3-midi-inventory",
            "metadata": {
                "path": self.metadata_checksum.path,
                "sha256": self.metadata_checksum.sha256,
                "size_bytes": self.metadata_checksum.size_bytes,
            },
            "records": [record.to_private_dict() for record in self.records],
            "source_splits": [
                {
                    "source_split": provenance.split,
                    "content_sha256": provenance.sha256,
                }
                for provenance in self.source_split_digests
            ],
            "exact_composition_cross_split_collisions": [
                collision.to_private_dict() for collision in self.composition_collisions
            ],
        }

    def to_private_dict(self) -> Dict[str, object]:
        """Return a fresh local manifest containing source strings and paths."""

        return self._private_payload()

    def to_private_json(self) -> str:
        """Serialize the private manifest as deterministic canonical JSON."""

        return canonical_json_dumps(self._private_payload())

    def public_summary(self) -> Mapping[str, object]:
        """Return aggregate evidence without composer, title, or path values."""

        split_summaries = []
        for provenance in self.source_split_digests:
            members = tuple(
                record for record in self.records if record.source_split == provenance.split
            )
            split_summaries.append(
                {
                    "source_split": provenance.split,
                    "content_sha256": provenance.sha256,
                    "midi_file_count": len(members),
                    "midi_size_bytes": sum(record.size_bytes for record in members),
                }
            )

        pair_counts: Dict[str, int] = {}
        affected_paths = set()
        for collision in self.composition_collisions:
            affected_paths.update(collision.midi_paths)
            for left_index, left in enumerate(collision.source_splits):
                for right in collision.source_splits[left_index + 1 :]:
                    pair = "{}--{}".format(left, right)
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

        return {
            "schema_version": self.schema_version,
            "dataset": _DATASET_NAME,
            "gate": "policy-free-maestro-v3-midi-inventory",
            "metadata_sha256": self.metadata_checksum.sha256,
            "metadata_size_bytes": self.metadata_checksum.size_bytes,
            "manifest_sha256": self.manifest_sha256,
            "midi_file_count": len(self.records),
            "midi_size_bytes": sum(record.size_bytes for record in self.records),
            "source_splits": split_summaries,
            "composition_disjointness": {
                "key_definition": "exact canonical_composer plus canonical_title",
                "is_cross_split_disjoint": not self.composition_collisions,
                "cross_split_collision_count": len(self.composition_collisions),
                "affected_midi_file_count": len(affected_paths),
                "split_pair_collision_counts": {
                    key: pair_counts[key] for key in sorted(pair_counts)
                },
                "source_splits_modified": False,
            },
            "privacy": {
                "source_composer_strings_included": False,
                "source_title_strings_included": False,
                "midi_paths_included": False,
                "audio_paths_included": False,
            },
            "claim_boundary": {
                "audio_files_required_or_verified": False,
                "midi_content_parsed": False,
                "note_events_inferred": False,
                "model_events_constructed": False,
                "source_splits_reassigned": False,
            },
        }


def _metadata_logical_path(declared: MaestroV3InventoryInput) -> str:
    relative = declared.metadata_csv.relative_to(declared.root).as_posix()
    return _relative_source_path(
        relative,
        field_name="metadata_csv",
        suffix=".csv",
    )


def _validated_regular_file(
    root: Path,
    logical_path: str,
    *,
    description: str,
) -> Tuple[Path, os.stat_result]:
    try:
        root_status = root.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError("trusted root does not exist: {}".format(root)) from error
    if stat.S_ISLNK(root_status.st_mode):
        raise MaestroInventoryError("trusted root must not be a symlink: {}".format(root))
    if not stat.S_ISDIR(root_status.st_mode):
        raise MaestroInventoryError("trusted root must be a directory: {}".format(root))
    resolved_root = root.resolve(strict=True)

    candidate = root
    components = PurePosixPath(logical_path).parts
    for index, component in enumerate(components):
        candidate = candidate / component
        try:
            status = candidate.lstat()
        except FileNotFoundError as error:
            raise FileNotFoundError(
                "declared {} does not exist: {}".format(description, candidate)
            ) from error
        if stat.S_ISLNK(status.st_mode):
            raise MaestroInventoryError(
                "declared {} path must not contain symlinks: {}".format(
                    description, candidate
                )
            )
        if index < len(components) - 1 and not stat.S_ISDIR(status.st_mode):
            raise MaestroInventoryError(
                "declared {} parent must be a directory: {}".format(
                    description, candidate
                )
            )
    if not stat.S_ISREG(status.st_mode):
        raise MaestroInventoryError(
            "declared {} must be a regular file: {}".format(description, candidate)
        )
    if status.st_nlink != 1:
        raise MaestroInventoryError(
            "declared {} must not be a hard link: {}".format(description, candidate)
        )
    try:
        candidate.resolve(strict=True).relative_to(resolved_root)
    except ValueError as error:
        raise MaestroInventoryError(
            "declared {} resolves outside the trusted root: {}".format(
                description, candidate
            )
        ) from error
    return candidate, status


def _checksum_file(path: Path, *, logical_path: str) -> ArtifactChecksum:
    """Small indirection retained so mutation checks can be fault-injected."""

    return ArtifactChecksum.from_file(path, logical_path=logical_path)


@dataclass(frozen=True)
class _MetadataRow:
    row_number: int
    canonical_composer: str
    canonical_title: str
    source_split: str
    year: str
    midi_path: str
    audio_path: str
    duration: str


def _parse_metadata_rows(
    metadata_path: Path,
    *,
    limits: MaestroInventoryLimits,
) -> Tuple[_MetadataRow, ...]:
    parsed: List[_MetadataRow] = []
    seen_exact_rows: Dict[Tuple[str, ...], int] = {}
    seen_midi_paths: Dict[str, str] = {}
    seen_audio_paths: Dict[str, str] = {}
    try:
        with metadata_path.open("r", encoding="utf-8", errors="strict", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            try:
                header = next(reader)
            except StopIteration as error:
                raise MaestroInventoryError("metadata CSV is empty") from error
            if tuple(header) != MAESTRO_V3_METADATA_HEADER:
                raise MaestroInventoryError(
                    "metadata CSV header must exactly equal the frozen v3.0.0 schema"
                )
            for values in reader:
                row_number = reader.line_num
                if len(parsed) >= limits.max_metadata_rows:
                    raise MaestroInventoryError("metadata rows exceed max_metadata_rows")
                if len(values) != len(MAESTRO_V3_METADATA_HEADER):
                    raise MaestroInventoryError(
                        "metadata row {} must contain exactly {} fields".format(
                            row_number, len(MAESTRO_V3_METADATA_HEADER)
                        )
                    )
                row_tuple = tuple(values)
                previous_row = seen_exact_rows.get(row_tuple)
                if previous_row is not None:
                    raise MaestroInventoryError(
                        "metadata rows {} and {} are exact duplicates".format(
                            previous_row, row_number
                        )
                    )
                seen_exact_rows[row_tuple] = row_number
                for field_name, value in zip(MAESTRO_V3_METADATA_HEADER, values):
                    if len(value) > limits.max_field_characters:
                        raise MaestroInventoryError(
                            "metadata field {!r} exceeds max_field_characters at row {}".format(
                                field_name, row_number
                            )
                        )
                composer = _strict_source_text(
                    values[0], field_name="canonical_composer"
                )
                title = _strict_source_text(values[1], field_name="canonical_title")
                split = _source_split(values[2])
                year = _year_text(values[3])
                midi_path = _relative_source_path(
                    values[4],
                    field_name="midi_filename",
                    suffix=".midi",
                    max_components=limits.max_path_components,
                )
                audio_path = _relative_source_path(
                    values[5],
                    field_name="audio_filename",
                    suffix=".wav",
                    max_components=limits.max_path_components,
                )
                duration = _duration_text(values[6])

                midi_key = midi_path.casefold()
                previous_midi = seen_midi_paths.get(midi_key)
                if previous_midi is not None:
                    raise MaestroInventoryError(
                        "MIDI paths collide under Unicode/case normalization: {!r} and {!r}".format(
                            previous_midi, midi_path
                        )
                    )
                seen_midi_paths[midi_key] = midi_path
                audio_key = audio_path.casefold()
                previous_audio = seen_audio_paths.get(audio_key)
                if previous_audio is not None:
                    raise MaestroInventoryError(
                        "audio paths collide under Unicode/case normalization: {!r} and {!r}".format(
                            previous_audio, audio_path
                        )
                    )
                seen_audio_paths[audio_key] = audio_path
                parsed.append(
                    _MetadataRow(
                        row_number=row_number,
                        canonical_composer=composer,
                        canonical_title=title,
                        source_split=split,
                        year=year,
                        midi_path=midi_path,
                        audio_path=audio_path,
                        duration=duration,
                    )
                )
    except UnicodeDecodeError as error:
        raise MaestroInventoryError("metadata CSV must be strict UTF-8") from error
    except csv.Error as error:
        raise MaestroInventoryError("metadata CSV syntax is invalid") from error

    if len(parsed) != MAESTRO_V3_EXPECTED_MIDI_FILES:
        raise MaestroInventoryError(
            "metadata CSV must contain exactly {} data rows".format(
                MAESTRO_V3_EXPECTED_MIDI_FILES
            )
        )
    return tuple(parsed)


def inventory_maestro_v3(
    declared: MaestroV3InventoryInput,
    *,
    limits: Optional[MaestroInventoryLimits] = None,
) -> MaestroArchiveInventory:
    """Inventory one explicit MAESTRO v3.0.0 root without parsing MIDI/audio.

    Exact source split values are retained.  Cross-split overlap under the
    exact ``(canonical_composer, canonical_title)`` metadata key is reported,
    not repaired.  File signatures and hashes are checked before and after the
    complete pass to detect ordinary changes in a trusted local acquisition.
    """

    if not isinstance(declared, MaestroV3InventoryInput):
        raise TypeError("declared must be a MaestroV3InventoryInput")
    if limits is None:
        limits = MaestroInventoryLimits()
    if not isinstance(limits, MaestroInventoryLimits):
        raise TypeError("limits must be a MaestroInventoryLimits record")
    if MAESTRO_V3_EXPECTED_MIDI_FILES > limits.max_midi_files:
        raise MaestroInventoryError("expected MIDI count exceeds max_midi_files")
    if MAESTRO_V3_EXPECTED_MIDI_FILES > limits.max_metadata_rows:
        raise MaestroInventoryError("expected metadata rows exceed max_metadata_rows")

    metadata_logical = _metadata_logical_path(declared)
    metadata_path, metadata_status = _validated_regular_file(
        declared.root,
        metadata_logical,
        description="metadata CSV",
    )
    if metadata_path != declared.metadata_csv:
        raise MaestroInventoryError("metadata_csv path changed during declaration")
    if metadata_status.st_size > limits.max_metadata_bytes:
        raise MaestroInventoryError("metadata CSV exceeds max_metadata_bytes")
    metadata_signature = _stat_signature(metadata_status)
    metadata_checksum = _checksum_file(
        metadata_path,
        logical_path=metadata_logical,
    )
    if _stat_signature(metadata_path.lstat()) != metadata_signature:
        raise RuntimeError("metadata CSV changed while it was being checksummed")

    rows = _parse_metadata_rows(metadata_path, limits=limits)
    metadata_after_parse = _checksum_file(
        metadata_path,
        logical_path=metadata_logical,
    )
    if (
        metadata_after_parse != metadata_checksum
        or _stat_signature(metadata_path.lstat()) != metadata_signature
    ):
        raise RuntimeError("metadata CSV changed while it was being parsed")

    preflight = []
    total_bytes = 0
    physical_files: Dict[Tuple[int, int], str] = {
        (metadata_status.st_dev, metadata_status.st_ino): metadata_logical
    }
    for row in rows:
        midi_path, midi_status = _validated_regular_file(
            declared.root,
            row.midi_path,
            description="MIDI file",
        )
        if midi_status.st_size > limits.max_midi_file_bytes:
            raise MaestroInventoryError(
                "MIDI file exceeds max_midi_file_bytes: {}".format(row.midi_path)
            )
        total_bytes += midi_status.st_size
        if total_bytes > limits.max_total_midi_bytes:
            raise MaestroInventoryError("MIDI bytes exceed max_total_midi_bytes")
        physical_key = (midi_status.st_dev, midi_status.st_ino)
        previous_path = physical_files.get(physical_key)
        if previous_path is not None:
            raise MaestroInventoryError(
                "one physical file was declared more than once: {!r} and {!r}".format(
                    previous_path, row.midi_path
                )
            )
        physical_files[physical_key] = row.midi_path
        preflight.append(
            (row, midi_path, _stat_signature(midi_status))
        )

    records = []
    content_digests: Dict[Tuple[str, int], str] = {}
    checksums: Dict[str, ArtifactChecksum] = {}
    for row, midi_path, signature in preflight:
        checksum = _checksum_file(midi_path, logical_path=row.midi_path)
        if _stat_signature(midi_path.lstat()) != signature:
            raise RuntimeError(
                "MIDI file changed while it was being checksummed: {}".format(
                    row.midi_path
                )
            )
        content_key = (checksum.sha256, checksum.size_bytes)
        previous_content = content_digests.get(content_key)
        if previous_content is not None:
            raise MaestroInventoryError(
                "MIDI files have duplicate exact content digests: {!r} and {!r}".format(
                    previous_content, row.midi_path
                )
            )
        content_digests[content_key] = row.midi_path
        checksums[row.midi_path] = checksum
        records.append(
            MaestroMidiInventory(
                metadata_row_number=row.row_number,
                canonical_composer=row.canonical_composer,
                canonical_title=row.canonical_title,
                source_split=row.source_split,
                year=row.year,
                midi_path=row.midi_path,
                audio_path=row.audio_path,
                duration=row.duration,
                sha256=checksum.sha256,
                size_bytes=checksum.size_bytes,
            )
        )

    for row, midi_path, signature in preflight:
        final_path, final_status = _validated_regular_file(
            declared.root,
            row.midi_path,
            description="MIDI file",
        )
        final_checksum = _checksum_file(final_path, logical_path=row.midi_path)
        if (
            final_path != midi_path
            or _stat_signature(final_status) != signature
            or final_checksum != checksums[row.midi_path]
            or _stat_signature(final_path.lstat()) != signature
        ):
            raise RuntimeError(
                "MIDI file changed during inventory: {}".format(row.midi_path)
            )

    final_metadata_path, final_metadata_status = _validated_regular_file(
        declared.root,
        metadata_logical,
        description="metadata CSV",
    )
    final_metadata_checksum = _checksum_file(
        final_metadata_path,
        logical_path=metadata_logical,
    )
    if (
        final_metadata_path != metadata_path
        or _stat_signature(final_metadata_status) != metadata_signature
        or final_metadata_checksum != metadata_checksum
        or _stat_signature(final_metadata_path.lstat()) != metadata_signature
    ):
        raise RuntimeError("metadata CSV changed during inventory")

    return MaestroArchiveInventory(
        metadata_checksum=metadata_checksum,
        records=tuple(records),
    )


__all__ = [
    "MAESTRO_V3_EXPECTED_MIDI_FILES",
    "MAESTRO_V3_METADATA_FILENAME",
    "MAESTRO_V3_METADATA_HEADER",
    "MAESTRO_V3_SOURCE_SPLITS",
    "MaestroArchiveInventory",
    "MaestroCompositionCollision",
    "MaestroInventoryError",
    "MaestroInventoryLimits",
    "MaestroMidiInventory",
    "MaestroV3InventoryInput",
    "inventory_maestro_v3",
]
