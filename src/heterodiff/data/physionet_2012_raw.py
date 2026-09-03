"""Lossless raw ingestion for PhysioNet Challenge 2012 patient records.

This module is deliberately narrower than a model-ready dataset adapter.  It
parses the official three-column ``Time,Parameter,Value`` record format,
retains one immutable object per input row, and reports structural audit
counts.  It does not impute missing-value sentinels, normalize values, sort
rows, collapse simultaneous measurements, or deduplicate repeated rows.

The six default admission descriptors are frozen from the Challenge 2012
record schema.  The official schema gives ``Weight`` a dual role: its first
``00:00`` row is an admission descriptor, while later rows are time-series
measurements.  That exception is declared explicitly rather than inferred;
no other measurement is promoted to static context by a time/name heuristic.
"""

from __future__ import annotations

import csv
import os
import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import FrozenSet, Optional, TextIO, Tuple, Union


DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS: FrozenSet[str] = frozenset(
    {"RecordID", "Age", "Gender", "Height", "ICUType", "Weight"}
)
DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS: FrozenSet[str] = frozenset(
    {"Weight"}
)

_HEADER = ("Time", "Parameter", "Value")
_TIME_PATTERN = re.compile(r"[0-9]{2}:[0-9]{2}\Z")
_RECORD_ID_PATTERN = re.compile(r"[0-9]+\Z")


class PhysioNet2012FormatError(ValueError):
    """Raised when a patient record violates the frozen raw-file contract."""


def _validate_plain_cell(value: object, *, name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(name))
    if not allow_empty and not value:
        raise PhysioNet2012FormatError("{} must not be empty".format(name))
    if value != value.strip():
        raise PhysioNet2012FormatError(
            "{} must not have leading or trailing whitespace".format(name)
        )
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise PhysioNet2012FormatError(
            "{} must not contain NUL or newline characters".format(name)
        )
    return value


def _parse_elapsed_minutes(
    text: str,
    *,
    maximum_elapsed_minutes: int,
    line_number: int,
) -> int:
    if _TIME_PATTERN.fullmatch(text) is None:
        raise PhysioNet2012FormatError(
            "line {} has invalid elapsed time {!r}; expected exact HH:MM".format(
                line_number, text
            )
        )
    hour = int(text[:2])
    minute = int(text[3:])
    if minute >= 60:
        raise PhysioNet2012FormatError(
            "line {} has invalid minute component in {!r}".format(line_number, text)
        )
    elapsed = 60 * hour + minute
    if elapsed > maximum_elapsed_minutes:
        raise PhysioNet2012FormatError(
            "line {} time {!r} exceeds the configured {}-minute horizon".format(
                line_number, text, maximum_elapsed_minutes
            )
        )
    return elapsed


def _parse_decimal(text: str, *, line_number: int) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise PhysioNet2012FormatError(
            "line {} has non-numeric value {!r}".format(line_number, text)
        ) from exc
    if not value.is_finite():
        raise PhysioNet2012FormatError(
            "line {} has non-finite value {!r}".format(line_number, text)
        )
    return value


@dataclass(frozen=True)
class PhysioNet2012IngestionConfig:
    """Frozen policies for the raw Challenge 2012 record boundary.

    Passing a ``frozenset`` is intentional: a mutable or duplicate-containing
    descriptor declaration is rejected instead of silently normalized.  Every
    configured descriptor must have one admission occurrence at ``00:00``.
    Later occurrences are permitted as observations only for an explicitly
    declared dual-role parameter.  ``RecordID`` is mandatory because it is the
    patient/group integrity key.
    """

    admission_descriptors: FrozenSet[str] = (
        DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS
    )
    dual_role_parameters: FrozenSet[str] = (
        DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS
    )
    maximum_elapsed_minutes: int = 48 * 60

    def __post_init__(self) -> None:
        if not isinstance(self.admission_descriptors, frozenset):
            raise TypeError("admission_descriptors must be a frozenset")
        if not self.admission_descriptors:
            raise ValueError("admission_descriptors must not be empty")
        for parameter in self.admission_descriptors:
            _validate_plain_cell(parameter, name="admission descriptor")
        if "RecordID" not in self.admission_descriptors:
            raise ValueError("admission_descriptors must include RecordID")
        if not isinstance(self.dual_role_parameters, frozenset):
            raise TypeError("dual_role_parameters must be a frozenset")
        for parameter in self.dual_role_parameters:
            _validate_plain_cell(parameter, name="dual-role parameter")
        if not self.dual_role_parameters <= self.admission_descriptors:
            raise ValueError(
                "dual_role_parameters must be a subset of admission_descriptors"
            )
        if "RecordID" in self.dual_role_parameters:
            raise ValueError("RecordID cannot be a dual-role parameter")
        if isinstance(self.maximum_elapsed_minutes, bool) or not isinstance(
            self.maximum_elapsed_minutes, int
        ):
            raise TypeError("maximum_elapsed_minutes must be an integer")
        if self.maximum_elapsed_minutes < 0:
            raise ValueError("maximum_elapsed_minutes must be nonnegative")
        if self.maximum_elapsed_minutes > 99 * 60 + 59:
            raise ValueError(
                "maximum_elapsed_minutes cannot exceed the exact two-digit HH:MM range"
            )


@dataclass(frozen=True)
class PhysioNet2012Row:
    """One uncollapsed data row, with raw cells and exact parsed quantities."""

    line_number: int
    time_text: str
    parameter: str
    value_text: str
    elapsed_minutes: int
    value: Decimal

    def __post_init__(self) -> None:
        if isinstance(self.line_number, bool) or not isinstance(self.line_number, int):
            raise TypeError("line_number must be an integer")
        if self.line_number < 2:
            raise ValueError("data-row line_number must be at least 2")
        _validate_plain_cell(self.time_text, name="time_text")
        _validate_plain_cell(self.parameter, name="parameter")
        _validate_plain_cell(self.value_text, name="value_text")
        if isinstance(self.elapsed_minutes, bool) or not isinstance(
            self.elapsed_minutes, int
        ):
            raise TypeError("elapsed_minutes must be an integer")
        if self.elapsed_minutes < 0:
            raise ValueError("elapsed_minutes must be nonnegative")
        if _TIME_PATTERN.fullmatch(self.time_text) is None:
            raise ValueError("time_text must use exact two-digit HH:MM syntax")
        minute = int(self.time_text[3:])
        if minute >= 60:
            raise ValueError("time_text has an invalid minute component")
        if 60 * int(self.time_text[:2]) + minute != self.elapsed_minutes:
            raise ValueError("elapsed_minutes does not match time_text")
        if not isinstance(self.value, Decimal):
            raise TypeError("value must be a Decimal")
        if not self.value.is_finite():
            raise ValueError("value must be finite")
        try:
            parsed_value = Decimal(self.value_text)
        except InvalidOperation as exc:
            raise ValueError("value_text must be a numeric decimal token") from exc
        if not parsed_value.is_finite() or parsed_value.as_tuple() != self.value.as_tuple():
            raise ValueError("value does not exactly match value_text")

    @property
    def csv_cells(self) -> Tuple[str, str, str]:
        """Return the decoded CSV cells used for exact-row duplicate audits."""

        return (self.time_text, self.parameter, self.value_text)


@dataclass(frozen=True)
class PhysioNet2012Audit:
    """Unambiguous structural counts for time-series observation rows.

    A tied-time group is a distinct elapsed minute containing at least two
    time-series rows.  ``rows_at_tied_times`` counts all rows in such groups;
    ``tied_row_excess`` counts rows beyond one representative per group.

    Exact duplicates are cell-identical ``(Time, Parameter, Value)``
    observations after CSV decoding.  Numeric-equivalent spellings such as
    ``80`` and ``80.0`` are not exact duplicates.  No rows are removed.
    """

    total_rows: int
    admission_descriptor_rows: int
    observation_rows: int
    unique_observation_times: int
    tied_time_groups: int
    rows_at_tied_times: int
    tied_row_excess: int
    exact_duplicate_groups: int
    exact_duplicate_rows: int
    exact_duplicate_row_excess: int

    def __post_init__(self) -> None:
        names = (
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
        for name in names:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("{} must be an integer".format(name))
            if value < 0:
                raise ValueError("{} must be nonnegative".format(name))
        if self.total_rows != self.admission_descriptor_rows + self.observation_rows:
            raise ValueError("total_rows must equal descriptor plus observation rows")
        if self.unique_observation_times > self.observation_rows:
            raise ValueError("unique_observation_times exceeds observation_rows")
        if self.tied_time_groups > self.unique_observation_times:
            raise ValueError("tied_time_groups exceeds unique_observation_times")
        if self.rows_at_tied_times > self.observation_rows:
            raise ValueError("rows_at_tied_times exceeds observation_rows")
        if self.rows_at_tied_times < 2 * self.tied_time_groups:
            raise ValueError("every tied_time_group must contain at least two rows")
        if self.tied_row_excess != self.rows_at_tied_times - self.tied_time_groups:
            raise ValueError("tied_row_excess is inconsistent")
        if self.exact_duplicate_rows > self.observation_rows:
            raise ValueError("exact_duplicate_rows exceeds observation_rows")
        if self.exact_duplicate_rows < 2 * self.exact_duplicate_groups:
            raise ValueError("every exact_duplicate_group must contain at least two rows")
        if self.exact_duplicate_row_excess != (
            self.exact_duplicate_rows - self.exact_duplicate_groups
        ):
            raise ValueError("exact_duplicate_row_excess is inconsistent")


@dataclass(frozen=True)
class PhysioNet2012Record:
    """A validated raw record whose row order and multiplicities are intact."""

    record_id: str
    rows: Tuple[PhysioNet2012Row, ...]
    admission_descriptor_rows: Tuple[PhysioNet2012Row, ...]
    observation_rows: Tuple[PhysioNet2012Row, ...]
    admission_descriptors: FrozenSet[str]
    dual_role_parameters: FrozenSet[str]
    maximum_elapsed_minutes: int
    audit: PhysioNet2012Audit

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or _RECORD_ID_PATTERN.fullmatch(
            self.record_id
        ) is None:
            raise ValueError("record_id must contain only ASCII decimal digits")
        if int(self.record_id) <= 0:
            raise ValueError("record_id must be positive")
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.admission_descriptor_rows, tuple):
            raise TypeError("admission_descriptor_rows must be a tuple")
        if not isinstance(self.observation_rows, tuple):
            raise TypeError("observation_rows must be a tuple")
        if not isinstance(self.admission_descriptors, frozenset):
            raise TypeError("admission_descriptors must be a frozenset")
        if "RecordID" not in self.admission_descriptors:
            raise ValueError("admission_descriptors must include RecordID")
        if not isinstance(self.dual_role_parameters, frozenset):
            raise TypeError("dual_role_parameters must be a frozenset")
        if not self.dual_role_parameters <= self.admission_descriptors:
            raise ValueError(
                "dual_role_parameters must be a subset of admission_descriptors"
            )
        if isinstance(self.maximum_elapsed_minutes, bool) or not isinstance(
            self.maximum_elapsed_minutes, int
        ):
            raise TypeError("maximum_elapsed_minutes must be an integer")
        if not 0 <= self.maximum_elapsed_minutes <= 99 * 60 + 59:
            raise ValueError("maximum_elapsed_minutes is outside the HH:MM range")
        if any(not isinstance(row, PhysioNet2012Row) for row in self.rows):
            raise TypeError("rows must contain PhysioNet2012Row values")
        if len({row.line_number for row in self.rows}) != len(self.rows):
            raise ValueError("row line numbers must be unique")
        if tuple(row.line_number for row in self.rows) != tuple(
            sorted(row.line_number for row in self.rows)
        ):
            raise ValueError("rows must preserve source line order")
        if any(
            row.elapsed_minutes > self.maximum_elapsed_minutes for row in self.rows
        ):
            raise ValueError("a row exceeds maximum_elapsed_minutes")
        if len(self.admission_descriptor_rows) + len(self.observation_rows) != len(
            self.rows
        ):
            raise ValueError("descriptor and observation partitions must cover all rows")
        descriptor_lines = {row.line_number for row in self.admission_descriptor_rows}
        observation_lines = {row.line_number for row in self.observation_rows}
        if descriptor_lines & observation_lines:
            raise ValueError("descriptor and observation partitions must be disjoint")
        if descriptor_lines | observation_lines != {
            row.line_number for row in self.rows
        }:
            raise ValueError("descriptor and observation partitions must preserve rows")
        expected_descriptors, expected_observations = _partition_rows(
            self.rows,
            self.admission_descriptors,
            self.dual_role_parameters,
        )
        if self.admission_descriptor_rows != expected_descriptors:
            raise ValueError("admission_descriptor_rows disagrees with frozen names")
        if self.observation_rows != expected_observations:
            raise ValueError("observation_rows disagrees with frozen names")
        record_id_rows = tuple(
            row for row in self.admission_descriptor_rows if row.parameter == "RecordID"
        )
        if len(record_id_rows) != 1 or record_id_rows[0].value_text != self.record_id:
            raise ValueError("record_id must match the unique RecordID row")
        if not isinstance(self.audit, PhysioNet2012Audit):
            raise TypeError("audit must be a PhysioNet2012Audit")
        expected_audit = _build_audit(
            self.rows, self.admission_descriptor_rows, self.observation_rows
        )
        if self.audit != expected_audit:
            raise ValueError("audit counts do not match the preserved rows")


def _build_audit(
    rows: Tuple[PhysioNet2012Row, ...],
    descriptor_rows: Tuple[PhysioNet2012Row, ...],
    observation_rows: Tuple[PhysioNet2012Row, ...],
) -> PhysioNet2012Audit:
    time_counts = Counter(row.elapsed_minutes for row in observation_rows)
    tied_counts = tuple(count for count in time_counts.values() if count > 1)
    row_counts = Counter(row.csv_cells for row in observation_rows)
    duplicate_counts = tuple(count for count in row_counts.values() if count > 1)
    return PhysioNet2012Audit(
        total_rows=len(rows),
        admission_descriptor_rows=len(descriptor_rows),
        observation_rows=len(observation_rows),
        unique_observation_times=len(time_counts),
        tied_time_groups=len(tied_counts),
        rows_at_tied_times=sum(tied_counts),
        tied_row_excess=sum(count - 1 for count in tied_counts),
        exact_duplicate_groups=len(duplicate_counts),
        exact_duplicate_rows=sum(duplicate_counts),
        exact_duplicate_row_excess=sum(count - 1 for count in duplicate_counts),
    )


def _partition_rows(
    rows: Tuple[PhysioNet2012Row, ...],
    admission_descriptors: FrozenSet[str],
    dual_role_parameters: FrozenSet[str],
) -> Tuple[Tuple[PhysioNet2012Row, ...], Tuple[PhysioNet2012Row, ...]]:
    """Partition rows under the declared dual-role admission convention.

    The first occurrence of every admission name remains in the descriptor
    partition so that its required ``00:00`` placement can be checked.  A
    repeated dual-role name is a time-series observation; a repeated ordinary
    descriptor stays in the descriptor partition and is rejected by the
    exactly-once integrity check.
    """

    descriptors = []
    observations = []
    seen_admission_names = set()
    for row in rows:
        if row.parameter not in admission_descriptors:
            observations.append(row)
        elif (
            row.parameter in dual_role_parameters
            and row.parameter in seen_admission_names
        ):
            observations.append(row)
        else:
            descriptors.append(row)
            seen_admission_names.add(row.parameter)
    return tuple(descriptors), tuple(observations)


def _normalize_expected_record_id(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError(
            "expected_record_id must not be boolean; use a positive integer or digit string"
        )
    if isinstance(value, int):
        if value <= 0:
            raise ValueError("expected_record_id must be positive")
        return str(value)
    if isinstance(value, str):
        if _RECORD_ID_PATTERN.fullmatch(value) is None or int(value) <= 0:
            raise ValueError(
                "expected_record_id strings must contain a positive ASCII decimal integer"
            )
        return value
    raise TypeError("expected_record_id must be a positive integer or digit string")


def parse_physionet_2012_record(
    stream: TextIO,
    *,
    expected_record_id: Optional[Union[int, str]] = None,
    config: Optional[PhysioNet2012IngestionConfig] = None,
) -> PhysioNet2012Record:
    """Parse and audit one open text stream without any row transformation.

    Rows must be chronological in their original order, while equal timestamps
    are retained exactly.  The ``-1`` convention used by the source remains an
    ordinary raw numeric token here; later code must assign variable-specific
    missingness semantics explicitly.
    """

    if not hasattr(stream, "read"):
        raise TypeError("stream must be an open text stream")
    if config is None:
        config = PhysioNet2012IngestionConfig()
    if not isinstance(config, PhysioNet2012IngestionConfig):
        raise TypeError("config must be a PhysioNet2012IngestionConfig")
    expected = _normalize_expected_record_id(expected_record_id)

    reader = csv.reader(stream, strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise PhysioNet2012FormatError("record is empty") from exc
    except (csv.Error, UnicodeError) as exc:
        raise PhysioNet2012FormatError("could not parse CSV header") from exc
    if tuple(header) != _HEADER:
        raise PhysioNet2012FormatError(
            "header must be exactly Time,Parameter,Value; got {!r}".format(
                tuple(header)
            )
        )

    parsed_rows = []
    previous_elapsed = -1
    try:
        for cells in reader:
            line_number = reader.line_num
            if len(cells) != 3:
                raise PhysioNet2012FormatError(
                    "line {} has {} columns; expected exactly 3".format(
                        line_number, len(cells)
                    )
                )
            time_text, parameter, value_text = cells
            _validate_plain_cell(time_text, name="line {} Time".format(line_number))
            _validate_plain_cell(
                parameter, name="line {} Parameter".format(line_number)
            )
            _validate_plain_cell(value_text, name="line {} Value".format(line_number))
            elapsed = _parse_elapsed_minutes(
                time_text,
                maximum_elapsed_minutes=config.maximum_elapsed_minutes,
                line_number=line_number,
            )
            if elapsed < previous_elapsed:
                raise PhysioNet2012FormatError(
                    "line {} time {} precedes the prior row; rows are not sorted".format(
                        line_number, time_text
                    )
                )
            previous_elapsed = elapsed
            parsed_rows.append(
                PhysioNet2012Row(
                    line_number=line_number,
                    time_text=time_text,
                    parameter=parameter,
                    value_text=value_text,
                    elapsed_minutes=elapsed,
                    value=_parse_decimal(value_text, line_number=line_number),
                )
            )
    except (csv.Error, UnicodeError) as exc:
        raise PhysioNet2012FormatError("could not parse CSV data rows") from exc

    rows = tuple(parsed_rows)
    descriptor_rows, observation_rows = _partition_rows(
        rows,
        config.admission_descriptors,
        config.dual_role_parameters,
    )

    descriptor_counts = Counter(row.parameter for row in descriptor_rows)
    for parameter in sorted(config.admission_descriptors):
        count = descriptor_counts[parameter]
        if count != 1:
            raise PhysioNet2012FormatError(
                "admission descriptor {!r} must occur exactly once; found {}".format(
                    parameter, count
                )
            )
    for row in descriptor_rows:
        if row.elapsed_minutes != 0:
            raise PhysioNet2012FormatError(
                "admission descriptor {!r} on line {} must be at 00:00".format(
                    row.parameter, row.line_number
                )
            )

    record_id_row = next(
        row for row in descriptor_rows if row.parameter == "RecordID"
    )
    record_id = record_id_row.value_text
    if _RECORD_ID_PATTERN.fullmatch(record_id) is None or int(record_id) <= 0:
        raise PhysioNet2012FormatError(
            "RecordID must be a positive ASCII decimal integer; got {!r}".format(
                record_id
            )
        )
    if expected is not None and record_id != expected:
        raise PhysioNet2012FormatError(
            "RecordID {!r} does not match expected identifier {!r}".format(
                record_id, expected
            )
        )

    audit = _build_audit(rows, descriptor_rows, observation_rows)
    return PhysioNet2012Record(
        record_id=record_id,
        rows=rows,
        admission_descriptor_rows=descriptor_rows,
        observation_rows=observation_rows,
        admission_descriptors=config.admission_descriptors,
        dual_role_parameters=config.dual_role_parameters,
        maximum_elapsed_minutes=config.maximum_elapsed_minutes,
        audit=audit,
    )


def load_physionet_2012_record(
    path: Union[str, os.PathLike],
    *,
    expected_record_id: Optional[Union[int, str]] = None,
    config: Optional[PhysioNet2012IngestionConfig] = None,
) -> PhysioNet2012Record:
    """Load one record, checking a numeric filename stem when not overridden."""

    if not isinstance(path, (str, os.PathLike)):
        raise TypeError("path must be a string or path-like object")
    record_path = Path(path)
    inferred = expected_record_id
    if inferred is None and _RECORD_ID_PATTERN.fullmatch(record_path.stem) is not None:
        inferred = record_path.stem
    try:
        with record_path.open("r", encoding="utf-8-sig", newline="") as stream:
            return parse_physionet_2012_record(
                stream,
                expected_record_id=inferred,
                config=config,
            )
    except UnicodeError as exc:
        raise PhysioNet2012FormatError("record is not valid UTF-8 text") from exc


__all__ = [
    "DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS",
    "DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS",
    "PhysioNet2012Audit",
    "PhysioNet2012FormatError",
    "PhysioNet2012IngestionConfig",
    "PhysioNet2012Record",
    "PhysioNet2012Row",
    "load_physionet_2012_record",
    "parse_physionet_2012_record",
]
