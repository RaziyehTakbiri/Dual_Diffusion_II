"""Explicit, loss-audited conversion of Challenge 2012 rows to event state.

The raw parser is the source-of-truth boundary.  This module converts a
validated :class:`PhysioNet2012Record` only after every semantic choice has
been supplied in a :class:`PhysioNet2012AdapterPolicy`.  There are no implicit
defaults for time, duplicate handling, descriptor roles, missing sentinels,
type/support mappings, horizon, split identity, or schema version.

The native :class:`~heterodiff.events.EventConfiguration` space is simple: two
events cannot have identical model state.  Consequently the only honest
row-preserving duplicate policy is "one row per event or fail".  The adapter
never breaks a collision with timestamp jitter, row order, a synthetic mark,
or deduplication.  Exact and float-induced collisions therefore stop
conversion while the raw record remains losslessly available.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import math
from numbers import Integral
from typing import FrozenSet, Optional, Tuple

from heterodiff.events import (
    ContinuousField,
    Event,
    EventConfiguration,
    EventObservation,
    EventTypeSchema,
    FeatureSchema,
    ObservationPattern,
    SupportKind,
    TimeMeasureKind,
    TimeReference,
)

from .physionet_2012_raw import (
    DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS,
    DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS,
    PhysioNet2012Audit,
    PhysioNet2012Record,
    PhysioNet2012Row,
)


PHYSIONET_2012_HORIZON_MINUTES = 48 * 60
_VALUE_FIELD = "value"
_EVENT_ID_PREFIX = "physionet-2012-row"


class PhysioNet2012PolicyError(ValueError):
    """Raised when an adapter policy is incomplete or internally inconsistent."""


class PhysioNet2012AdapterError(ValueError):
    """Raised when a valid raw record cannot be represented under a policy."""


class PhysioNet2012TimePolicy(str, Enum):
    """Supported physical-time contracts."""

    ATOMIC_MINUTE_GRID_PRESERVE_TIES = "atomic_minute_grid_preserve_ties"


class PhysioNet2012DuplicatePolicy(str, Enum):
    """Supported duplicate contracts for the simple configuration space."""

    PRESERVE_EACH_ROW_OR_REJECT = "preserve_each_row_or_reject"


class PhysioNet2012SplitIdentityPolicy(str, Enum):
    """Supported patient/group identity contracts."""

    EXACT_RECORD_ID = "exact_record_id"


def _parameter_name(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(label))
    if not value or value != value.strip():
        raise ValueError("{} must be a nonempty, whitespace-trimmed string".format(label))
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise ValueError("{} must not contain NUL or newlines".format(label))
    return value


def _sentinel_tuple(value: object, *, label: str) -> Tuple[Decimal, ...]:
    if not isinstance(value, tuple):
        raise TypeError("{} must be an explicit tuple of Decimal values".format(label))
    sentinels = value
    for sentinel in sentinels:
        if not isinstance(sentinel, Decimal):
            raise TypeError("{} must contain only Decimal values".format(label))
        if not sentinel.is_finite():
            raise ValueError("{} must contain only finite values".format(label))
    if len(set(sentinels)) != len(sentinels):
        raise ValueError("{} contains numerically duplicate sentinels".format(label))
    return tuple(sorted(sentinels))


def _enum_or_none(value: object, enum_type: object, *, label: str) -> object:
    if value is None:
        return None
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        valid = ", ".join(item.value for item in enum_type)
        raise ValueError("{} must be one of: {}".format(label, valid)) from exc


def _decimal_to_float(value: Decimal, *, row: PhysioNet2012Row) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise PhysioNet2012AdapterError(
            "line {} parameter {!r} cannot be represented as a finite float".format(
                row.line_number, row.parameter
            )
        )
    return result


@dataclass(frozen=True)
class PhysioNet2012MissingRule:
    """Explicit numeric sentinels for one admission descriptor.

    An empty tuple explicitly declares that the descriptor has no sentinel.
    Sentinel matching uses exact Decimal numeric equality, so ``-1`` and
    ``-1.0`` receive the same declared interpretation while their raw spelling
    remains in the row sidecar.
    """

    parameter: str
    missing_sentinels: Tuple[Decimal, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parameter",
            _parameter_name(self.parameter, label="missing-rule parameter"),
        )
        object.__setattr__(
            self,
            "missing_sentinels",
            _sentinel_tuple(
                self.missing_sentinels,
                label="missing_sentinels for {!r}".format(self.parameter),
            ),
        )

    def is_missing(self, value: Decimal) -> bool:
        if not isinstance(value, Decimal):
            raise TypeError("missing-value checks require a Decimal")
        return value in self.missing_sentinels


@dataclass(frozen=True)
class PhysioNet2012ParameterSpec:
    """Frozen event-type, scalar support, and sentinel mapping for one variable."""

    parameter: str
    type_id: int
    support: SupportKind
    missing_sentinels: Tuple[Decimal, ...]
    lower: Optional[float] = None
    upper: Optional[float] = None
    unit: Optional[str] = None

    def __post_init__(self) -> None:
        parameter = _parameter_name(self.parameter, label="parameter")
        object.__setattr__(self, "parameter", parameter)
        if isinstance(self.type_id, bool) or not isinstance(self.type_id, Integral):
            raise TypeError("type_id must be an integer")
        type_id = int(self.type_id)
        if type_id < 0:
            raise ValueError("type_id must be nonnegative")
        object.__setattr__(self, "type_id", type_id)
        try:
            support = SupportKind(self.support)
        except (TypeError, ValueError) as exc:
            valid = ", ".join(item.value for item in SupportKind)
            raise ValueError("support must be one of: {}".format(valid)) from exc
        object.__setattr__(self, "support", support)
        object.__setattr__(
            self,
            "missing_sentinels",
            _sentinel_tuple(
                self.missing_sentinels,
                label="missing_sentinels for {!r}".format(parameter),
            ),
        )
        # Constructing the field here centralizes support/bound validation.
        self.continuous_field()

    def continuous_field(self) -> ContinuousField:
        return ContinuousField(
            _VALUE_FIELD,
            support=self.support,
            lower=self.lower,
            upper=self.upper,
            unit=self.unit,
        )

    def is_missing(self, value: Decimal) -> bool:
        if not isinstance(value, Decimal):
            raise TypeError("missing-value checks require a Decimal")
        return value in self.missing_sentinels

    def event_type_schema(self) -> EventTypeSchema:
        return EventTypeSchema(
            type_id=self.type_id,
            name=self.parameter,
            fields=(self.continuous_field(),),
        )


@dataclass(frozen=True)
class PhysioNet2012AdapterPolicy:
    """Complete semantics required before conversion is permitted.

    Every field defaults to ``None`` rather than to a convenient scientific
    assumption.  Call :meth:`validate_complete` (also invoked by conversion)
    to obtain a precise list of unresolved choices.
    """

    time_policy: Optional[PhysioNet2012TimePolicy] = None
    duplicate_policy: Optional[PhysioNet2012DuplicatePolicy] = None
    admission_descriptors: Optional[FrozenSet[str]] = None
    dual_role_parameters: Optional[FrozenSet[str]] = None
    admission_missing_rules: Optional[Tuple[PhysioNet2012MissingRule, ...]] = None
    parameter_specs: Optional[Tuple[PhysioNet2012ParameterSpec, ...]] = None
    horizon_minutes: Optional[int] = None
    split_identity_policy: Optional[PhysioNet2012SplitIdentityPolicy] = None
    schema_version: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "time_policy",
            _enum_or_none(
                self.time_policy,
                PhysioNet2012TimePolicy,
                label="time_policy",
            ),
        )
        object.__setattr__(
            self,
            "duplicate_policy",
            _enum_or_none(
                self.duplicate_policy,
                PhysioNet2012DuplicatePolicy,
                label="duplicate_policy",
            ),
        )
        object.__setattr__(
            self,
            "split_identity_policy",
            _enum_or_none(
                self.split_identity_policy,
                PhysioNet2012SplitIdentityPolicy,
                label="split_identity_policy",
            ),
        )

        if self.admission_descriptors is not None:
            if not isinstance(self.admission_descriptors, frozenset):
                raise TypeError("admission_descriptors must be a frozenset or None")
            for name in self.admission_descriptors:
                _parameter_name(name, label="admission descriptor")
            if "RecordID" not in self.admission_descriptors:
                raise PhysioNet2012PolicyError(
                    "admission_descriptors must include RecordID"
                )
            if (
                self.admission_descriptors
                != DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS
            ):
                raise PhysioNet2012PolicyError(
                    "the official Challenge 2012 adapter requires the six frozen "
                    "admission descriptors from the source schema"
                )
        if self.dual_role_parameters is not None:
            if not isinstance(self.dual_role_parameters, frozenset):
                raise TypeError("dual_role_parameters must be a frozenset or None")
            for name in self.dual_role_parameters:
                _parameter_name(name, label="dual-role parameter")
            if "RecordID" in self.dual_role_parameters:
                raise PhysioNet2012PolicyError(
                    "RecordID cannot be a dual-role parameter"
                )
            if (
                self.dual_role_parameters
                != DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS
            ):
                raise PhysioNet2012PolicyError(
                    "the official Challenge 2012 adapter requires Weight as the "
                    "sole frozen dual-role parameter"
                )
        if (
            self.admission_descriptors is not None
            and self.dual_role_parameters is not None
            and not self.dual_role_parameters <= self.admission_descriptors
        ):
            raise PhysioNet2012PolicyError(
                "dual_role_parameters must be a subset of admission_descriptors"
            )

        if self.admission_missing_rules is not None:
            rules = tuple(self.admission_missing_rules)
            if any(not isinstance(rule, PhysioNet2012MissingRule) for rule in rules):
                raise TypeError(
                    "admission_missing_rules must contain PhysioNet2012MissingRule values"
                )
            names = tuple(rule.parameter for rule in rules)
            if len(set(names)) != len(names):
                raise PhysioNet2012PolicyError(
                    "admission_missing_rules contain duplicate parameter names"
                )
            object.__setattr__(
                self,
                "admission_missing_rules",
                tuple(sorted(rules, key=lambda rule: rule.parameter)),
            )

        if self.parameter_specs is not None:
            specs = tuple(self.parameter_specs)
            if any(not isinstance(spec, PhysioNet2012ParameterSpec) for spec in specs):
                raise TypeError(
                    "parameter_specs must contain PhysioNet2012ParameterSpec values"
                )
            names = tuple(spec.parameter for spec in specs)
            type_ids = tuple(spec.type_id for spec in specs)
            if len(set(names)) != len(names):
                raise PhysioNet2012PolicyError(
                    "parameter_specs contain duplicate parameter names"
                )
            if len(set(type_ids)) != len(type_ids):
                raise PhysioNet2012PolicyError(
                    "parameter_specs contain duplicate type_id values"
                )
            object.__setattr__(
                self,
                "parameter_specs",
                tuple(sorted(specs, key=lambda spec: spec.type_id)),
            )

        if self.horizon_minutes is not None:
            if isinstance(self.horizon_minutes, bool) or not isinstance(
                self.horizon_minutes, Integral
            ):
                raise TypeError("horizon_minutes must be an integer or None")
            horizon = int(self.horizon_minutes)
            if horizon != PHYSIONET_2012_HORIZON_MINUTES:
                raise PhysioNet2012PolicyError(
                    "the official Challenge 2012 adapter requires an explicit "
                    "48-hour (2880-minute) horizon; cropping is a separate dataset"
                )
            object.__setattr__(self, "horizon_minutes", horizon)

        if self.schema_version is not None:
            object.__setattr__(
                self,
                "schema_version",
                _parameter_name(self.schema_version, label="schema_version"),
            )

        self._validate_cross_fields()

    def _validate_cross_fields(self) -> None:
        descriptors = self.admission_descriptors
        dual_roles = self.dual_role_parameters
        rules = self.admission_missing_rules
        specs = self.parameter_specs
        if descriptors is not None and rules is not None:
            expected = descriptors - {"RecordID"}
            actual = frozenset(rule.parameter for rule in rules)
            if actual != expected:
                missing = sorted(expected - actual)
                extra = sorted(actual - expected)
                details = []
                if missing:
                    details.append("missing {}".format(", ".join(missing)))
                if extra:
                    details.append("unexpected {}".format(", ".join(extra)))
                raise PhysioNet2012PolicyError(
                    "admission_missing_rules must cover every non-ID descriptor "
                    "exactly: {}".format("; ".join(details))
                )
        if descriptors is not None and dual_roles is not None and specs is not None:
            spec_names = frozenset(spec.parameter for spec in specs)
            invalid = (spec_names & descriptors) - dual_roles
            if invalid:
                raise PhysioNet2012PolicyError(
                    "pure admission descriptors cannot be event parameters: {}".format(
                        ", ".join(sorted(invalid))
                    )
                )
            missing_dual = dual_roles - spec_names
            if missing_dual:
                raise PhysioNet2012PolicyError(
                    "dual-role parameters require event specs: {}".format(
                        ", ".join(sorted(missing_dual))
                    )
                )

    def validate_complete(self) -> None:
        names = (
            "time_policy",
            "duplicate_policy",
            "admission_descriptors",
            "dual_role_parameters",
            "admission_missing_rules",
            "parameter_specs",
            "horizon_minutes",
            "split_identity_policy",
            "schema_version",
        )
        missing = tuple(name for name in names if getattr(self, name) is None)
        if missing:
            raise PhysioNet2012PolicyError(
                "adapter policy is incomplete; explicitly set: {}".format(
                    ", ".join(missing)
                )
            )
        assert self.parameter_specs is not None
        if not self.parameter_specs:
            raise PhysioNet2012PolicyError(
                "parameter_specs must explicitly define a nonempty dataset vocabulary"
            )
        self._validate_cross_fields()

    def feature_schema(self) -> FeatureSchema:
        self.validate_complete()
        assert self.horizon_minutes is not None
        assert self.parameter_specs is not None
        assert self.schema_version is not None
        atoms = tuple(float(minute) for minute in range(self.horizon_minutes + 1))
        return FeatureSchema(
            event_types=tuple(spec.event_type_schema() for spec in self.parameter_specs),
            horizon=float(self.horizon_minutes),
            time_measure=TimeMeasureKind.ATOMIC,
            time_reference=TimeReference.atomic(atoms, (1.0,) * len(atoms)),
            allow_simultaneous=True,
            version=self.schema_version,
        )


@dataclass(frozen=True)
class PhysioNet2012AdmissionValue:
    """One non-ID admission value with missingness kept separate from value."""

    source_row: PhysioNet2012Row
    is_missing: bool
    value: Optional[float]

    def __post_init__(self) -> None:
        if not isinstance(self.source_row, PhysioNet2012Row):
            raise TypeError("source_row must be a PhysioNet2012Row")
        if self.source_row.parameter == "RecordID":
            raise ValueError("RecordID is split identity, not an admission feature")
        if not isinstance(self.is_missing, bool):
            raise TypeError("is_missing must be a boolean")
        if self.is_missing:
            if self.value is not None:
                raise ValueError("a missing admission value must not be imputed")
        else:
            if isinstance(self.value, bool) or not isinstance(self.value, float):
                raise TypeError("a present admission value must be a float")
            if not math.isfinite(self.value):
                raise ValueError("a present admission value must be finite")
            if self.value != float(self.source_row.value):
                raise ValueError("admission value must match its lossless source row")

    @property
    def parameter(self) -> str:
        return self.source_row.parameter


@dataclass(frozen=True)
class PhysioNet2012EventSidecar:
    """Lossless source-row provenance aligned to one canonical event."""

    source_row: PhysioNet2012Row
    value_missing: bool
    event_id: Tuple[str, str, int]

    def __post_init__(self) -> None:
        if not isinstance(self.source_row, PhysioNet2012Row):
            raise TypeError("source_row must be a PhysioNet2012Row")
        if not isinstance(self.value_missing, bool):
            raise TypeError("value_missing must be a boolean")
        if not isinstance(self.event_id, tuple) or len(self.event_id) != 3:
            raise TypeError("event_id must be a three-part tuple")
        prefix, record_id, line_number = self.event_id
        if prefix != _EVENT_ID_PREFIX or not isinstance(record_id, str):
            raise ValueError("event_id has an invalid PhysioNet namespace")
        if line_number != self.source_row.line_number:
            raise ValueError("event_id line number must match source_row")


@dataclass(frozen=True)
class PhysioNet2012AdapterAudit:
    """Conversion counts tied back to the immutable raw audit."""

    source_audit: PhysioNet2012Audit
    converted_event_rows: int
    present_event_values: int
    missing_event_values: int
    present_admission_values: int
    missing_admission_values: int
    preserved_tied_time_groups: int
    preserved_rows_at_tied_times: int

    def __post_init__(self) -> None:
        if not isinstance(self.source_audit, PhysioNet2012Audit):
            raise TypeError("source_audit must be a PhysioNet2012Audit")
        names = (
            "converted_event_rows",
            "present_event_values",
            "missing_event_values",
            "present_admission_values",
            "missing_admission_values",
            "preserved_tied_time_groups",
            "preserved_rows_at_tied_times",
        )
        for name in names:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("{} must be an integer".format(name))
            if value < 0:
                raise ValueError("{} must be nonnegative".format(name))
        if self.converted_event_rows != (
            self.present_event_values + self.missing_event_values
        ):
            raise ValueError("event presence/missingness counts are inconsistent")
        if self.converted_event_rows != self.source_audit.observation_rows:
            raise ValueError("conversion must retain one event per observation row")
        if self.present_admission_values + self.missing_admission_values != (
            self.source_audit.admission_descriptor_rows - 1
        ):
            raise ValueError("admission presence/missingness counts are inconsistent")
        if self.preserved_tied_time_groups != self.source_audit.tied_time_groups:
            raise ValueError("tied-time group count was not preserved")
        if self.preserved_rows_at_tied_times != self.source_audit.rows_at_tied_times:
            raise ValueError("rows at tied times were not preserved")


@dataclass(frozen=True)
class PhysioNet2012AdaptedRecord:
    """Model target plus separate admission, audit, and round-trip sidecars."""

    configuration: EventConfiguration
    admission_values: Tuple[PhysioNet2012AdmissionValue, ...]
    admission_rows: Tuple[PhysioNet2012Row, ...]
    event_sidecars: Tuple[PhysioNet2012EventSidecar, ...]
    audit: PhysioNet2012AdapterAudit
    policy: PhysioNet2012AdapterPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, EventConfiguration):
            raise TypeError("configuration must be an EventConfiguration")
        admission_values = tuple(self.admission_values)
        admission_rows = tuple(self.admission_rows)
        event_sidecars = tuple(self.event_sidecars)
        object.__setattr__(self, "admission_values", admission_values)
        object.__setattr__(self, "admission_rows", admission_rows)
        object.__setattr__(self, "event_sidecars", event_sidecars)
        if any(
            not isinstance(value, PhysioNet2012AdmissionValue)
            for value in admission_values
        ):
            raise TypeError("admission_values contain an invalid value")
        if any(not isinstance(row, PhysioNet2012Row) for row in admission_rows):
            raise TypeError("admission_rows must contain PhysioNet2012Row values")
        if any(
            not isinstance(sidecar, PhysioNet2012EventSidecar)
            for sidecar in event_sidecars
        ):
            raise TypeError("event_sidecars contain an invalid value")
        if not isinstance(self.audit, PhysioNet2012AdapterAudit):
            raise TypeError("audit must be a PhysioNet2012AdapterAudit")
        if not isinstance(self.policy, PhysioNet2012AdapterPolicy):
            raise TypeError("policy must be a PhysioNet2012AdapterPolicy")
        self.policy.validate_complete()
        if self.configuration.schema != self.policy.feature_schema():
            raise ValueError("configuration schema disagrees with the adapter policy")
        if len(self.configuration.events) != len(event_sidecars):
            raise ValueError("every canonical event requires exactly one row sidecar")
        for event, sidecar in zip(self.configuration.events, event_sidecars):
            if event.event_id != sidecar.event_id:
                raise ValueError("event sidecars must align with canonical events")
            if sidecar.event_id[1] != self.configuration.sample_id:
                raise ValueError("event sidecar record ID must match sample_id")
            event_type = self.configuration.schema.event_type(event.event_type)
            if event_type.name != sidecar.source_row.parameter:
                raise ValueError("event type disagrees with its source-row parameter")
            if event.event_time != float(sidecar.source_row.elapsed_minutes):
                raise ValueError("event time disagrees with its source row")
            if sidecar.value_missing != (_VALUE_FIELD not in event.marks):
                raise ValueError("event missingness disagrees with its row sidecar")
            expected_marks = (
                {}
                if sidecar.value_missing
                else {_VALUE_FIELD: (float(sidecar.source_row.value),)}
            )
            if dict(event.marks) != expected_marks:
                raise ValueError("event value disagrees with its lossless source row")
        if len(admission_values) + 1 != len(admission_rows):
            raise ValueError("admission_values must exclude only the RecordID row")
        record_id_rows = tuple(
            row for row in admission_rows if row.parameter == "RecordID"
        )
        if len(record_id_rows) != 1:
            raise ValueError("admission_rows require exactly one RecordID row")
        record_id = record_id_rows[0].value_text
        if self.configuration.sample_id != record_id:
            raise ValueError("sample_id must retain the exact RecordID")
        if self.configuration.group_id != record_id:
            raise ValueError("group_id must retain the exact patient RecordID")
        expected_admission_rows = tuple(
            value.source_row for value in sorted(admission_values, key=lambda x: x.source_row.line_number)
        )
        actual_non_id_rows = tuple(
            row for row in admission_rows if row.parameter != "RecordID"
        )
        if expected_admission_rows != actual_non_id_rows:
            raise ValueError("admission value sidecars do not match admission rows")
        if len(event_sidecars) != self.audit.converted_event_rows:
            raise ValueError("event sidecar count disagrees with the audit")
        if (
            sum(sidecar.value_missing for sidecar in event_sidecars)
            != self.audit.missing_event_values
        ):
            raise ValueError("event missingness sidecars disagree with the audit")
        if (
            sum(value.is_missing for value in admission_values)
            != self.audit.missing_admission_values
        ):
            raise ValueError("admission missingness sidecars disagree with the audit")
        if self.audit.source_audit.admission_descriptor_rows != len(admission_rows):
            raise ValueError("admission row count disagrees with the source audit")
        rows = self.round_trip_rows()
        if len(rows) != self.audit.source_audit.total_rows:
            raise ValueError("round-trip sidecars do not cover every source row")
        line_numbers = tuple(row.line_number for row in rows)
        if len(set(line_numbers)) != len(line_numbers):
            raise ValueError("round-trip sidecars contain duplicate source line numbers")

    def round_trip_rows(self) -> Tuple[PhysioNet2012Row, ...]:
        """Recover every decoded raw row in original physical-line order."""

        rows = self.admission_rows + tuple(
            sidecar.source_row for sidecar in self.event_sidecars
        )
        return tuple(sorted(rows, key=lambda row: row.line_number))

    def round_trip_csv_cells(self) -> Tuple[Tuple[str, str, str], ...]:
        return tuple(row.csv_cells for row in self.round_trip_rows())


def _record_policy_checks(
    record: PhysioNet2012Record,
    policy: PhysioNet2012AdapterPolicy,
) -> None:
    assert policy.admission_descriptors is not None
    assert policy.dual_role_parameters is not None
    assert policy.parameter_specs is not None
    assert policy.horizon_minutes is not None
    if record.admission_descriptors != policy.admission_descriptors:
        raise PhysioNet2012AdapterError(
            "raw and adapter admission_descriptors differ; reparse or fix the policy"
        )
    if record.dual_role_parameters != policy.dual_role_parameters:
        raise PhysioNet2012AdapterError(
            "raw and adapter dual_role_parameters differ; reparse or fix the policy"
        )
    if record.maximum_elapsed_minutes != policy.horizon_minutes:
        raise PhysioNet2012AdapterError(
            "raw ingestion horizon and adapter horizon differ; reparse or fix the policy"
        )
    known = frozenset(spec.parameter for spec in policy.parameter_specs)
    observed = frozenset(row.parameter for row in record.observation_rows)
    unknown = observed - known
    if unknown:
        raise PhysioNet2012AdapterError(
            "record contains parameters absent from the frozen type map: {}".format(
                ", ".join(sorted(unknown))
            )
        )


def adapt_physionet_2012_record(
    record: PhysioNet2012Record,
    *,
    policy: Optional[PhysioNet2012AdapterPolicy] = None,
) -> PhysioNet2012AdaptedRecord:
    """Convert one raw record without imputation, jitter, grouping, or leakage."""

    if not isinstance(record, PhysioNet2012Record):
        raise TypeError("record must be a PhysioNet2012Record")
    if policy is None:
        policy = PhysioNet2012AdapterPolicy()
    if not isinstance(policy, PhysioNet2012AdapterPolicy):
        raise TypeError("policy must be a PhysioNet2012AdapterPolicy")
    policy.validate_complete()
    _record_policy_checks(record, policy)

    assert policy.admission_missing_rules is not None
    assert policy.parameter_specs is not None
    rule_by_name = {
        rule.parameter: rule for rule in policy.admission_missing_rules
    }
    spec_by_name = {spec.parameter: spec for spec in policy.parameter_specs}

    admission_values = []
    for row in record.admission_descriptor_rows:
        if row.parameter == "RecordID":
            continue
        rule = rule_by_name[row.parameter]
        is_missing = rule.is_missing(row.value)
        admission_values.append(
            PhysioNet2012AdmissionValue(
                source_row=row,
                is_missing=is_missing,
                value=None if is_missing else _decimal_to_float(row.value, row=row),
            )
        )

    events = []
    observations = []
    sidecars_by_id = {}
    seen_model_states = {}
    for row in record.observation_rows:
        spec = spec_by_name[row.parameter]
        is_missing = spec.is_missing(row.value)
        marks = (
            {}
            if is_missing
            else {_VALUE_FIELD: (_decimal_to_float(row.value, row=row),)}
        )
        event_id = (_EVENT_ID_PREFIX, record.record_id, row.line_number)
        event = Event(
            event_time=float(row.elapsed_minutes),
            event_type=spec.type_id,
            marks=marks,
            event_id=event_id,
        )
        prior_row = seen_model_states.get(event.model_key())
        if prior_row is not None:
            raise PhysioNet2012AdapterError(
                "rows {} and {} map to identical model state; the declared simple "
                "configuration cannot preserve both, and jitter/deduplication are "
                "forbidden".format(prior_row.line_number, row.line_number)
            )
        seen_model_states[event.model_key()] = row
        events.append(event)
        observations.append(
            EventObservation(
                time_observed=True,
                type_observed=True,
                observed_marks=(frozenset() if is_missing else frozenset({_VALUE_FIELD})),
            )
        )
        sidecars_by_id[event_id] = PhysioNet2012EventSidecar(
            source_row=row,
            value_missing=is_missing,
            event_id=event_id,
        )

    schema = policy.feature_schema()
    try:
        configuration = EventConfiguration(
            schema=schema,
            events=tuple(events),
            observed=ObservationPattern(
                events=tuple(observations),
                cardinality_observed=True,
            ),
            sample_id=record.record_id,
            group_id=record.record_id,
        )
    except (TypeError, ValueError) as exc:
        raise PhysioNet2012AdapterError(
            "record violates the frozen event schema: {}".format(exc)
        ) from exc

    event_sidecars = tuple(
        sidecars_by_id[event.event_id] for event in configuration.events
    )
    time_counts = Counter(event.event_time for event in configuration.events)
    tied_counts = tuple(count for count in time_counts.values() if count > 1)
    missing_event_values = sum(sidecar.value_missing for sidecar in event_sidecars)
    missing_admission_values = sum(value.is_missing for value in admission_values)
    audit = PhysioNet2012AdapterAudit(
        source_audit=record.audit,
        converted_event_rows=len(configuration.events),
        present_event_values=len(configuration.events) - missing_event_values,
        missing_event_values=missing_event_values,
        present_admission_values=len(admission_values) - missing_admission_values,
        missing_admission_values=missing_admission_values,
        preserved_tied_time_groups=len(tied_counts),
        preserved_rows_at_tied_times=sum(tied_counts),
    )
    return PhysioNet2012AdaptedRecord(
        configuration=configuration,
        admission_values=tuple(sorted(admission_values, key=lambda item: item.parameter)),
        admission_rows=record.admission_descriptor_rows,
        event_sidecars=event_sidecars,
        audit=audit,
        policy=policy,
    )


__all__ = [
    "PHYSIONET_2012_HORIZON_MINUTES",
    "PhysioNet2012AdaptedRecord",
    "PhysioNet2012AdapterAudit",
    "PhysioNet2012AdapterError",
    "PhysioNet2012AdapterPolicy",
    "PhysioNet2012AdmissionValue",
    "PhysioNet2012DuplicatePolicy",
    "PhysioNet2012EventSidecar",
    "PhysioNet2012MissingRule",
    "PhysioNet2012ParameterSpec",
    "PhysioNet2012PolicyError",
    "PhysioNet2012SplitIdentityPolicy",
    "PhysioNet2012TimePolicy",
    "adapt_physionet_2012_record",
]
