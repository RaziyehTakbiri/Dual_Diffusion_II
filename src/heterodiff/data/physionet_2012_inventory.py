"""Policy-free archive inventory for PhysioNet Challenge 2012 records.

This module is an acquisition boundary, not a model-ready dataset adapter.
Callers declare an explicit list of record files for each *source* partition;
the inventory then checks patient/group disjointness, hashes exact files, and
aggregates the lossless structural audits produced by
``physionet_2012_raw``.  It never discovers files by a broad glob, interprets
clinical values, joins outcomes, creates a model vocabulary, or assigns
train/validation/test roles.

Record identifiers and logical paths are needed locally to prove that one
patient cannot cross source partitions.  They therefore appear only in the
private manifest.  ``public_summary`` deliberately omits all record-level
identifiers, paths, raw values, and source-derived parameter-name strings.
Observed parameter names remain local structural diagnostics only and must
never be reused as an archive-wide model codebook.
"""

from __future__ import annotations

import os
import re
import stat
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple, Union

from heterodiff.artifacts.manifest import (
    ArtifactChecksum,
    DatasetProvenance,
    canonical_json_dumps,
    sha256_bytes,
)

from .physionet_2012_raw import (
    PhysioNet2012Audit,
    load_physionet_2012_record,
)


PathLike = Union[str, os.PathLike]

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_RECORD_ID_PATTERN = re.compile(r"[0-9]+\Z")
_SOURCE_LABEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_MODELING_ROLE_LABELS = frozenset(
    {"train", "training", "val", "valid", "validation", "test", "testing"}
)
_PARTITION_DIGEST_DOMAIN = b"heterodiff-physionet-2012-source-partition-v1\0"
_DATASET_NAME = "physionet-challenge-2012-structural-inventory"

_AUDIT_FIELDS = (
    "total_rows",
    "admission_descriptor_rows",
    "observation_rows",
    "unique_observation_times",
    "tied_time_groups",
    "rows_at_tied_times",
    "tied_row_excess",
    "exact_duplicate_groups",
    "exact_duplicate_rows",
    "exact_duplicate_row_excess",
)


class PhysioNet2012InventoryError(ValueError):
    """Raised when an archive declaration violates the inventory contract."""


def _positive_limit(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{} must be an integer".format(name))
    if value <= 0:
        raise ValueError("{} must be positive".format(name))
    return value


def _source_label(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("source_label must be a string")
    normalized = unicodedata.normalize("NFC", value)
    if value != normalized:
        raise PhysioNet2012InventoryError("source_label must use NFC Unicode")
    if _SOURCE_LABEL_PATTERN.fullmatch(value) is None:
        raise PhysioNet2012InventoryError(
            "source_label must contain only ASCII letters, digits, '.', '_' or '-'"
        )
    if value.casefold() in _MODELING_ROLE_LABELS:
        raise PhysioNet2012InventoryError(
            "source_label must name a source partition, not a modeling split role"
        )
    return value


def _logical_record_path(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("record paths must be strings")
    normalized = unicodedata.normalize("NFC", value)
    if value != normalized:
        raise PhysioNet2012InventoryError("record paths must use NFC Unicode")
    if not value or "\x00" in value or "\\" in value:
        raise PhysioNet2012InventoryError(
            "record paths must be nonempty relative POSIX paths"
        )
    if any(character in value for character in ("\r", "\n")):
        raise PhysioNet2012InventoryError("record paths must not contain newlines")
    if value.startswith("/"):
        raise PhysioNet2012InventoryError("record paths must be relative")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PhysioNet2012InventoryError(
            "record paths must not contain empty, '.' or '..' components"
        )
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or str(parsed) != value:
        raise PhysioNet2012InventoryError(
            "record paths must be canonical relative POSIX paths"
        )
    if parsed.suffix != ".txt":
        raise PhysioNet2012InventoryError(
            "declared PhysioNet 2012 record paths must end in '.txt'"
        )
    stem = parsed.stem
    if _RECORD_ID_PATTERN.fullmatch(stem) is None or int(stem) <= 0:
        raise PhysioNet2012InventoryError(
            "record filename stems must be positive ASCII decimal RecordIDs"
        )
    return value


def _audit_to_dict(audit: PhysioNet2012Audit) -> Dict[str, int]:
    return {name: getattr(audit, name) for name in _AUDIT_FIELDS}


def _sum_audits(audits: Iterable[PhysioNet2012Audit]) -> PhysioNet2012Audit:
    totals = {name: 0 for name in _AUDIT_FIELDS}
    for audit in audits:
        if not isinstance(audit, PhysioNet2012Audit):
            raise TypeError("audits must contain PhysioNet2012Audit records")
        for name in _AUDIT_FIELDS:
            totals[name] += getattr(audit, name)
    return PhysioNet2012Audit(**totals)


@dataclass(frozen=True)
class PhysioNet2012InventoryLimits:
    """Explicit resource bounds applied before or during archive parsing."""

    max_partitions: int = 16
    max_files: int = 100_000
    max_file_bytes: int = 16 * 1024 * 1024
    max_total_bytes: int = 4 * 1024 * 1024 * 1024
    max_rows_per_record: int = 1_000_000
    max_total_rows: int = 1_000_000_000

    def __post_init__(self) -> None:
        for name in (
            "max_partitions",
            "max_files",
            "max_file_bytes",
            "max_total_bytes",
            "max_rows_per_record",
            "max_total_rows",
        ):
            _positive_limit(getattr(self, name), name=name)


@dataclass(frozen=True)
class PhysioNet2012PartitionInput:
    """One explicit source partition and its allowlisted record files.

    ``record_paths`` are relative to ``root``.  Directory scanning is
    intentionally absent: an outcome table, license, or other neighboring
    file cannot become a patient record merely because it shares a directory.
    """

    source_label: str
    root: PathLike
    record_paths: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_label", _source_label(self.source_label))
        if not isinstance(self.root, (str, os.PathLike)):
            raise TypeError("root must be a string or path-like object")
        root = Path(self.root)
        if not root.is_absolute():
            raise PhysioNet2012InventoryError("partition roots must be absolute paths")
        object.__setattr__(self, "root", root)
        if isinstance(self.record_paths, (str, bytes)):
            raise TypeError("record_paths must be an iterable of relative paths")
        try:
            paths = tuple(_logical_record_path(path) for path in self.record_paths)
        except TypeError:
            raise
        if not paths:
            raise PhysioNet2012InventoryError(
                "each source partition must declare at least one record"
            )
        portable: Dict[str, str] = {}
        for path in paths:
            key = path.casefold()
            previous = portable.get(key)
            if previous is not None:
                raise PhysioNet2012InventoryError(
                    "record paths collide under Unicode/case normalization: "
                    "{!r} and {!r}".format(previous, path)
                )
            portable[key] = path
        object.__setattr__(self, "record_paths", tuple(sorted(paths)))


@dataclass(frozen=True)
class PhysioNet2012RecordInventory:
    """Local record-level evidence; do not publish this object as a dataset card."""

    source_label: str
    logical_path: str
    record_id: str
    sha256: str
    size_bytes: int
    audit: PhysioNet2012Audit
    observed_parameters: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_label", _source_label(self.source_label))
        object.__setattr__(self, "logical_path", _logical_record_path(self.logical_path))
        if not isinstance(self.record_id, str):
            raise TypeError("record_id must be a string")
        if _RECORD_ID_PATTERN.fullmatch(self.record_id) is None or int(self.record_id) <= 0:
            raise ValueError("record_id must be a positive ASCII decimal integer")
        if PurePosixPath(self.logical_path).stem != self.record_id:
            raise ValueError("logical_path filename stem must equal record_id")
        if not isinstance(self.sha256, str) or _SHA256_PATTERN.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be a lowercase 64-character digest")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise TypeError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be nonnegative")
        if not isinstance(self.audit, PhysioNet2012Audit):
            raise TypeError("audit must be a PhysioNet2012Audit")
        if not isinstance(self.observed_parameters, tuple):
            raise TypeError("observed_parameters must be a tuple")
        if any(not isinstance(parameter, str) or not parameter for parameter in self.observed_parameters):
            raise TypeError("observed_parameters must contain nonempty strings")
        if self.observed_parameters != tuple(sorted(set(self.observed_parameters))):
            raise ValueError("observed_parameters must be sorted and unique")

    def to_private_dict(self) -> Dict[str, object]:
        """Return a fresh row-level mapping containing local patient identity."""

        return {
            "source_label": self.source_label,
            "logical_path": self.logical_path,
            "record_id": self.record_id,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "audit": _audit_to_dict(self.audit),
            "observed_parameters": list(self.observed_parameters),
        }


def _partition_digest(records: Sequence[PhysioNet2012RecordInventory]) -> str:
    """Commit to partition content without serializing record paths or IDs."""

    payload = []
    for record in records:
        payload.append(
            {
                "sha256": record.sha256,
                "size_bytes": record.size_bytes,
                "audit": _audit_to_dict(record.audit),
                "observed_parameters": list(record.observed_parameters),
            }
        )
    payload.sort(key=canonical_json_dumps)
    encoded = canonical_json_dumps(payload).encode("utf-8")
    return sha256_bytes(_PARTITION_DIGEST_DOMAIN + encoded)


@dataclass(frozen=True)
class PhysioNet2012ArchiveInventory:
    """Canonical structural inventory with a privacy-reduced public view."""

    records: Tuple[PhysioNet2012RecordInventory, ...]
    aggregate_audit: PhysioNet2012Audit = field(init=False)
    source_partition_digests: Tuple[DatasetProvenance, ...] = field(init=False)
    observed_parameters: Tuple[str, ...] = field(init=False)
    manifest_sha256: str = field(init=False)
    schema_version: int = field(default=1, init=False)

    def __post_init__(self) -> None:
        if isinstance(self.records, (str, bytes)):
            raise TypeError("records must be an iterable of record inventories")
        records = tuple(self.records)
        if not records:
            raise PhysioNet2012InventoryError("inventory must contain at least one record")
        if any(not isinstance(record, PhysioNet2012RecordInventory) for record in records):
            raise TypeError("records must contain PhysioNet2012RecordInventory values")
        records = tuple(sorted(records, key=lambda item: (item.source_label, item.logical_path)))

        seen_paths: Dict[Tuple[str, str], str] = {}
        seen_record_ids: Dict[str, str] = {}
        seen_labels: Dict[str, str] = {}
        for record in records:
            label_key = record.source_label.casefold()
            previous_label = seen_labels.get(label_key)
            if previous_label is not None and previous_label != record.source_label:
                raise PhysioNet2012InventoryError(
                    "source labels collide under case normalization: {!r} and {!r}".format(
                        previous_label, record.source_label
                    )
                )
            seen_labels[label_key] = record.source_label
            portable_key = (record.source_label.casefold(), record.logical_path.casefold())
            previous_path = seen_paths.get(portable_key)
            if previous_path is not None:
                raise PhysioNet2012InventoryError(
                    "record inventory contains duplicate logical path {!r}".format(
                        previous_path
                    )
                )
            seen_paths[portable_key] = record.logical_path
            previous_partition = seen_record_ids.get(record.record_id)
            if previous_partition is not None:
                raise PhysioNet2012InventoryError(
                    "RecordID {} occurs more than once (source partitions {!r} and {!r})".format(
                        record.record_id, previous_partition, record.source_label
                    )
                )
            seen_record_ids[record.record_id] = record.source_label

        object.__setattr__(self, "records", records)
        object.__setattr__(self, "aggregate_audit", _sum_audits(record.audit for record in records))
        object.__setattr__(
            self,
            "observed_parameters",
            tuple(sorted({parameter for record in records for parameter in record.observed_parameters})),
        )

        labels = tuple(sorted({record.source_label for record in records}))
        provenances = []
        for label in labels:
            partition_records = tuple(record for record in records if record.source_label == label)
            provenances.append(
                DatasetProvenance(
                    name=_DATASET_NAME,
                    split=label,
                    sha256=_partition_digest(partition_records),
                )
            )
        object.__setattr__(self, "source_partition_digests", tuple(provenances))
        private_json = canonical_json_dumps(self._private_payload())
        object.__setattr__(self, "manifest_sha256", sha256_bytes(private_json.encode("utf-8")))

    def _private_payload(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset": _DATASET_NAME,
            "gate": "policy-free-structural-inventory",
            "records": [record.to_private_dict() for record in self.records],
            "source_partitions": [
                {
                    "source_label": provenance.split,
                    "content_sha256": provenance.sha256,
                }
                for provenance in self.source_partition_digests
            ],
            "aggregate_audit": _audit_to_dict(self.aggregate_audit),
            "observed_parameters": list(self.observed_parameters),
        }

    def to_private_dict(self) -> Dict[str, object]:
        """Return a fresh local manifest containing RecordIDs and paths.

        This result is necessary for a patient-disjoint audit but is not a
        publication artifact.  It contains no raw measurement values.
        """

        return self._private_payload()

    def to_private_json(self) -> str:
        """Return the local manifest in deterministic canonical JSON."""

        return canonical_json_dumps(self._private_payload())

    def public_summary(self) -> Mapping[str, object]:
        """Return aggregate evidence with source-derived strings redacted.

        Parameter names are source cells and could be malformed even when a
        file satisfies the three-column syntax.  They therefore remain in the
        local private manifest.  A separately reviewed dataset card may state
        official variable names, but this method does not publish them.
        """

        partition_summaries = []
        for provenance in self.source_partition_digests:
            partition_records = tuple(
                record for record in self.records if record.source_label == provenance.split
            )
            partition_summaries.append(
                {
                    "source_label": provenance.split,
                    "content_sha256": provenance.sha256,
                    "record_count": len(partition_records),
                    "size_bytes": sum(record.size_bytes for record in partition_records),
                    "audit": _audit_to_dict(
                        _sum_audits(record.audit for record in partition_records)
                    ),
                    "unique_observed_parameter_count": len(
                        {
                            parameter
                            for record in partition_records
                            for parameter in record.observed_parameters
                        }
                    ),
                }
            )
        return {
            "schema_version": self.schema_version,
            "dataset": _DATASET_NAME,
            "gate": "policy-free-structural-inventory",
            "manifest_sha256": self.manifest_sha256,
            "record_count": len(self.records),
            "size_bytes": sum(record.size_bytes for record in self.records),
            "source_partitions": partition_summaries,
            "aggregate_audit": _audit_to_dict(self.aggregate_audit),
            "unique_observed_parameter_count": len(self.observed_parameters),
            "privacy": {
                "record_level_identifiers_included": False,
                "record_level_paths_included": False,
                "raw_measurement_values_included": False,
                "source_parameter_names_included": False,
            },
            "claim_boundary": {
                "modeling_split_roles_assigned": False,
                "model_vocabulary_defined": False,
                "clinical_value_semantics_defined": False,
                "outcomes_joined": False,
            },
            "parameter_name_reporting": (
                "local diagnostics only; publication requires a separately reviewed allowlist"
            ),
        }


def _validated_regular_record(root: Path, logical_path: str) -> Tuple[Path, os.stat_result]:
    try:
        root_status = root.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError("partition root does not exist: {}".format(root)) from error
    if stat.S_ISLNK(root_status.st_mode):
        raise PhysioNet2012InventoryError(
            "partition root must not be a symlink: {}".format(root)
        )
    if not stat.S_ISDIR(root_status.st_mode):
        raise PhysioNet2012InventoryError(
            "partition root must be a directory: {}".format(root)
        )
    resolved_root = root.resolve(strict=True)
    candidate = root
    parts = PurePosixPath(logical_path).parts
    for index, component in enumerate(parts):
        candidate = candidate / component
        try:
            status = candidate.lstat()
        except FileNotFoundError as error:
            raise FileNotFoundError(
                "declared record does not exist: {}".format(candidate)
            ) from error
        if stat.S_ISLNK(status.st_mode):
            raise PhysioNet2012InventoryError(
                "declared record path must not contain symlinks: {}".format(candidate)
            )
        if index < len(parts) - 1 and not stat.S_ISDIR(status.st_mode):
            raise PhysioNet2012InventoryError(
                "record path parent must be a directory: {}".format(candidate)
            )
    if not stat.S_ISREG(status.st_mode):
        raise PhysioNet2012InventoryError(
            "declared record must be a regular file: {}".format(candidate)
        )
    try:
        candidate.resolve(strict=True).relative_to(resolved_root)
    except ValueError as error:
        raise PhysioNet2012InventoryError(
            "declared record resolves outside its partition root: {}".format(candidate)
        ) from error
    return candidate, status


def inventory_physionet_2012_partitions(
    partitions: Sequence[PhysioNet2012PartitionInput],
    *,
    limits: Optional[PhysioNet2012InventoryLimits] = None,
) -> PhysioNet2012ArchiveInventory:
    """Build a deterministic policy-free inventory from synthetic or acquired files.

    Source files are hashed before and after raw parsing.  On a trusted local
    archive this detects ordinary mutation that would pair a checksum with an
    audit of different bytes.  Because parsing re-opens the path, this is not
    a security proof against a malicious concurrent filesystem adversary.
    Model semantics remain unavailable until a separate, fully explicit
    ``PhysioNet2012AdapterPolicy`` has been reviewed and frozen.
    """

    if isinstance(partitions, (str, bytes)):
        raise TypeError("partitions must be an iterable of partition inputs")
    try:
        declared = tuple(partitions)
    except TypeError as error:
        raise TypeError("partitions must be an iterable of partition inputs") from error
    if not declared:
        raise PhysioNet2012InventoryError("at least one source partition is required")
    if any(not isinstance(item, PhysioNet2012PartitionInput) for item in declared):
        raise TypeError("partitions must contain PhysioNet2012PartitionInput values")
    if limits is None:
        limits = PhysioNet2012InventoryLimits()
    if not isinstance(limits, PhysioNet2012InventoryLimits):
        raise TypeError("limits must be a PhysioNet2012InventoryLimits record")
    if len(declared) > limits.max_partitions:
        raise PhysioNet2012InventoryError("source partition count exceeds max_partitions")

    labels: Dict[str, str] = {}
    for item in declared:
        key = item.source_label.casefold()
        previous = labels.get(key)
        if previous is not None:
            raise PhysioNet2012InventoryError(
                "source labels collide under case normalization: {!r} and {!r}".format(
                    previous, item.source_label
                )
            )
        labels[key] = item.source_label
    declared = tuple(sorted(declared, key=lambda item: item.source_label))

    file_count = sum(len(item.record_paths) for item in declared)
    if file_count > limits.max_files:
        raise PhysioNet2012InventoryError("declared record count exceeds max_files")

    preflight = []
    total_bytes = 0
    file_identities: Dict[Tuple[int, int], str] = {}
    for item in declared:
        for logical_path in item.record_paths:
            candidate, status = _validated_regular_record(item.root, logical_path)
            if status.st_size > limits.max_file_bytes:
                raise PhysioNet2012InventoryError(
                    "record {} exceeds max_file_bytes".format(logical_path)
                )
            total_bytes += status.st_size
            if total_bytes > limits.max_total_bytes:
                raise PhysioNet2012InventoryError(
                    "declared record bytes exceed max_total_bytes"
                )
            identity = (status.st_dev, status.st_ino)
            previous = file_identities.get(identity)
            if previous is not None:
                raise PhysioNet2012InventoryError(
                    "one physical file was declared more than once: {!r} and {!r}".format(
                        previous, logical_path
                    )
                )
            file_identities[identity] = logical_path
            preflight.append((item.source_label, logical_path, candidate, status.st_size))

    inventories = []
    total_rows = 0
    for source_label, logical_path, candidate, expected_size in preflight:
        artifact_path = "{}/{}".format(source_label, logical_path)
        before = ArtifactChecksum.from_file(candidate, logical_path=artifact_path)
        if before.size_bytes != expected_size:
            raise RuntimeError("record changed after inventory preflight: {}".format(candidate))
        expected_record_id = PurePosixPath(logical_path).stem
        record = load_physionet_2012_record(
            candidate,
            expected_record_id=expected_record_id,
        )
        after = ArtifactChecksum.from_file(candidate, logical_path=artifact_path)
        if after != before:
            raise RuntimeError("record changed while it was being parsed: {}".format(candidate))
        if record.audit.total_rows > limits.max_rows_per_record:
            raise PhysioNet2012InventoryError(
                "record {} exceeds max_rows_per_record".format(logical_path)
            )
        total_rows += record.audit.total_rows
        if total_rows > limits.max_total_rows:
            raise PhysioNet2012InventoryError("parsed rows exceed max_total_rows")
        inventories.append(
            PhysioNet2012RecordInventory(
                source_label=source_label,
                logical_path=logical_path,
                record_id=record.record_id,
                sha256=before.sha256,
                size_bytes=before.size_bytes,
                audit=record.audit,
                observed_parameters=tuple(sorted({row.parameter for row in record.rows})),
            )
        )
    return PhysioNet2012ArchiveInventory(records=tuple(inventories))


__all__ = [
    "PhysioNet2012ArchiveInventory",
    "PhysioNet2012InventoryError",
    "PhysioNet2012InventoryLimits",
    "PhysioNet2012PartitionInput",
    "PhysioNet2012RecordInventory",
    "inventory_physionet_2012_partitions",
]
