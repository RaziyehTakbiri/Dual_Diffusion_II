"""Identity-free capability plan for complete adapter conformance.

The plan is deliberately smaller than the conformance runner.  It converts one
exact :class:`AdapterCapabilities` value into an immutable ordered check
inventory without receiving an adapter identity, class, parser, source format,
or dataset label.  Phase-C runners may branch on this object; they must not
reconstruct domain-specific dispatch around it.

This is development infrastructure.  Exact test IDs and inapplicability
reasons remain subject to the mandatory A9.1 freeze before a decision-bearing
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional, Tuple

from heterodiff.events import MultiplicityMode, TimeMeasureKind

from .adapter_contract import (
    ATOMIC_COUNTING_GRID_REPRESENTATION_ID,
    AdapterCapabilities,
)


NO_ATOMIC_GRID_REASON = (
    "NOT_APPLICABLE:v1.capability.atomic_grid_not_advertised"
)
NO_RAW_RECONSTRUCTION_REASON = (
    "NOT_APPLICABLE:v1.capability.raw_byte_reconstruction_not_advertised"
)
NO_FITTED_PREPROCESSING_REASON = (
    "NOT_APPLICABLE:v1.capability.fitted_preprocessing_not_advertised"
)
NO_FITTED_COUNTERFACTUAL_PROTOCOL_REASON = (
    "NOT_APPLICABLE:v1.runner.fit_counterfactual_protocol_not_frozen"
)

_CHECK_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_MAX_CHECK_ID_BYTES = 128
_MAX_REASON_BYTES = 256
MAXIMUM_REPRESENTATION_IDS = 64


class CheckMode(str, Enum):
    """How the shared runner treats one capability-controlled check."""

    REQUIRED = "required"
    ASSERT_EMPTY = "assert_empty"
    ASSERT_NO_FIT = "assert_no_fit"
    NOT_APPLICABLE = "not_applicable"


def _check_id(value: object) -> str:
    if type(value) is not str:
        raise TypeError("check_id must be an exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("check_id must contain only ASCII") from exc
    if len(encoded) > _MAX_CHECK_ID_BYTES or _CHECK_ID_RE.fullmatch(value) is None:
        raise ValueError("check_id is not canonical")
    return value


def _representation_id(value: object) -> str:
    if type(value) is not str:
        raise TypeError("representation_id must be an exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("representation_id must contain only ASCII") from exc
    if len(encoded) > 128 or _CHECK_ID_RE.fullmatch(value) is None:
        raise ValueError("representation_id is not canonical")
    return value


def _reason(value: object) -> str:
    if type(value) is not str:
        raise TypeError("reason must be an exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("reason must contain only ASCII") from exc
    if not encoded or len(encoded) > _MAX_REASON_BYTES:
        raise ValueError("reason is outside its byte bound")
    if any(byte < 0x20 or byte == 0x7F for byte in encoded):
        raise ValueError("reason contains an ASCII control character")
    return value


@dataclass(frozen=True)
class PlanCheck:
    """One ordered check selected only from declared capabilities."""

    check_id: str
    mode: CheckMode
    reason: Optional[str] = None
    representation_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "check_id", _check_id(self.check_id))
        if type(self.mode) is not CheckMode:
            raise TypeError("mode must be an exact CheckMode")
        if self.mode is CheckMode.NOT_APPLICABLE:
            if self.reason is None:
                raise ValueError("NOT_APPLICABLE checks require an exact reason")
            object.__setattr__(self, "reason", _reason(self.reason))
        elif self.reason is not None:
            raise ValueError("only NOT_APPLICABLE checks may carry a reason")
        if self.representation_id is not None:
            object.__setattr__(
                self,
                "representation_id",
                _representation_id(self.representation_id),
            )


@dataclass(frozen=True)
class ConformancePlan:
    """Complete identity-free plan used by a shared Phase-C runner."""

    time_measure: TimeMeasureKind
    multiplicity_mode: MultiplicityMode
    native: CheckMode
    semantic_reconstruction: CheckMode
    coverage: CheckMode
    atomic_grid: CheckMode
    raw_reconstruction: CheckMode
    static_context: CheckMode
    evaluation_labels: CheckMode
    provenance: CheckMode
    fitted_state: CheckMode
    representation_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.time_measure) is not TimeMeasureKind:
            raise TypeError("time_measure must be an exact TimeMeasureKind")
        if type(self.multiplicity_mode) is not MultiplicityMode:
            raise TypeError("multiplicity_mode must be an exact MultiplicityMode")
        for name in (
            "native",
            "semantic_reconstruction",
            "coverage",
            "atomic_grid",
            "raw_reconstruction",
            "static_context",
            "evaluation_labels",
            "provenance",
            "fitted_state",
        ):
            if type(getattr(self, name)) is not CheckMode:
                raise TypeError("{} must be an exact CheckMode".format(name))
        if self.native is not CheckMode.REQUIRED:
            raise ValueError("native conformance is always required")
        if self.semantic_reconstruction is not CheckMode.REQUIRED:
            raise ValueError("semantic reconstruction is always required")
        if self.coverage is not CheckMode.REQUIRED:
            raise ValueError("coverage reconciliation is always required")
        if self.atomic_grid not in (CheckMode.REQUIRED, CheckMode.NOT_APPLICABLE):
            raise ValueError("atomic_grid has an invalid mode")
        if self.raw_reconstruction not in (
            CheckMode.REQUIRED,
            CheckMode.NOT_APPLICABLE,
        ):
            raise ValueError("raw_reconstruction has an invalid mode")
        for name in ("static_context", "evaluation_labels", "provenance"):
            if getattr(self, name) not in (
                CheckMode.REQUIRED,
                CheckMode.ASSERT_EMPTY,
            ):
                raise ValueError("{} has an invalid mode".format(name))
        if self.fitted_state not in (
            CheckMode.REQUIRED,
            CheckMode.ASSERT_NO_FIT,
        ):
            raise ValueError("fitted_state has an invalid mode")
        if type(self.representation_ids) is not tuple:
            raise TypeError("representation_ids must be an exact tuple")
        if len(self.representation_ids) > MAXIMUM_REPRESENTATION_IDS:
            raise ValueError("representation_ids exceed the resource ceiling")
        identifiers = tuple(
            _representation_id(value) for value in self.representation_ids
        )
        if identifiers != tuple(sorted(set(identifiers))):
            raise ValueError("representation_ids must be sorted and unique")
        object.__setattr__(self, "representation_ids", identifiers)
        has_atomic_grid = (
            ATOMIC_COUNTING_GRID_REPRESENTATION_ID in self.representation_ids
        )
        if has_atomic_grid != (self.atomic_grid is CheckMode.REQUIRED):
            raise ValueError("atomic-grid mode disagrees with representation_ids")
        if has_atomic_grid and self.time_measure is not TimeMeasureKind.ATOMIC:
            raise ValueError("atomic-grid mode requires atomic time")

    @property
    def generic_representation_ids(self) -> Tuple[str, ...]:
        return tuple(
            value
            for value in self.representation_ids
            if value != ATOMIC_COUNTING_GRID_REPRESENTATION_ID
        )

    @property
    def capability_control_trace(self) -> Tuple[str, ...]:
        """Return an identity-free trace suitable for label-mutation checks."""

        return (
            "time_measure={}".format(self.time_measure.value),
            "multiplicity_mode={}".format(self.multiplicity_mode.value),
            "atomic_grid={}".format(self.atomic_grid.value),
            "raw_reconstruction={}".format(self.raw_reconstruction.value),
            "static_context={}".format(self.static_context.value),
            "evaluation_labels={}".format(self.evaluation_labels.value),
            "provenance={}".format(self.provenance.value),
            "fitted_state={}".format(self.fitted_state.value),
            "representations={}".format(
                ",".join(self.representation_ids) if self.representation_ids else "-"
            ),
        )

    def ordered_checks(self) -> Tuple[PlanCheck, ...]:
        checks = [
            PlanCheck("core.native", self.native),
            PlanCheck("leaf.coverage", self.coverage),
            PlanCheck(
                "leaf.semantic_reconstruction", self.semantic_reconstruction
            ),
            PlanCheck("leaf.static_context", self.static_context),
            PlanCheck("leaf.evaluation_labels", self.evaluation_labels),
            PlanCheck("leaf.private_provenance", self.provenance),
            PlanCheck("leaf.fitted_state", self.fitted_state),
        ]
        if self.atomic_grid is CheckMode.REQUIRED:
            checks.append(
                PlanCheck(
                    "representation.atomic_counting_grid",
                    CheckMode.REQUIRED,
                    representation_id=ATOMIC_COUNTING_GRID_REPRESENTATION_ID,
                )
            )
        else:
            checks.append(
                PlanCheck(
                    "representation.atomic_counting_grid",
                    CheckMode.NOT_APPLICABLE,
                    reason=NO_ATOMIC_GRID_REASON,
                    representation_id=ATOMIC_COUNTING_GRID_REPRESENTATION_ID,
                )
            )
        for index, representation_id in enumerate(
            self.generic_representation_ids
        ):
            checks.append(
                PlanCheck(
                    "representation.generic.{:04d}".format(index),
                    CheckMode.REQUIRED,
                    representation_id=representation_id,
                )
            )
        if self.raw_reconstruction is CheckMode.REQUIRED:
            checks.append(
                PlanCheck("reconstruction.raw_bytes", CheckMode.REQUIRED)
            )
        else:
            checks.append(
                PlanCheck(
                    "reconstruction.raw_bytes",
                    CheckMode.NOT_APPLICABLE,
                    reason=NO_RAW_RECONSTRUCTION_REASON,
                )
            )
        if self.fitted_state is CheckMode.ASSERT_NO_FIT:
            checks.append(
                PlanCheck(
                    "counterfactual.fitted_preprocessing",
                    CheckMode.NOT_APPLICABLE,
                    reason=NO_FITTED_PREPROCESSING_REASON,
                )
            )
        else:
            checks.append(
                PlanCheck(
                    "counterfactual.fitted_preprocessing",
                    CheckMode.NOT_APPLICABLE,
                    reason=NO_FITTED_COUNTERFACTUAL_PROTOCOL_REASON,
                )
            )
        return tuple(checks)


def plan_from_capabilities(capabilities: AdapterCapabilities) -> ConformancePlan:
    """Build a complete plan without accepting adapter identity information."""

    if type(capabilities) is not AdapterCapabilities:
        raise TypeError("capabilities must be an exact AdapterCapabilities")
    if (
        len(capabilities.supported_representation_ids)
        > MAXIMUM_REPRESENTATION_IDS
    ):
        raise ValueError("representation_ids exceed the resource ceiling")
    snapshot = AdapterCapabilities(
        time_measure=capabilities.time_measure,
        multiplicity_mode=capabilities.multiplicity_mode,
        semantic_reconstruction=capabilities.semantic_reconstruction,
        raw_byte_reconstruction=capabilities.raw_byte_reconstruction,
        fitted_state=capabilities.fitted_state,
        supported_representation_ids=capabilities.supported_representation_ids,
        static_context=capabilities.static_context,
        evaluation_labels=capabilities.evaluation_labels,
        private_provenance=capabilities.private_provenance,
    )
    return ConformancePlan(
        time_measure=snapshot.time_measure,
        multiplicity_mode=snapshot.multiplicity_mode,
        native=CheckMode.REQUIRED,
        semantic_reconstruction=CheckMode.REQUIRED,
        coverage=CheckMode.REQUIRED,
        atomic_grid=(
            CheckMode.REQUIRED
            if ATOMIC_COUNTING_GRID_REPRESENTATION_ID
            in snapshot.supported_representation_ids
            else CheckMode.NOT_APPLICABLE
        ),
        raw_reconstruction=(
            CheckMode.REQUIRED
            if snapshot.raw_byte_reconstruction
            else CheckMode.NOT_APPLICABLE
        ),
        static_context=(
            CheckMode.REQUIRED
            if snapshot.static_context
            else CheckMode.ASSERT_EMPTY
        ),
        evaluation_labels=(
            CheckMode.REQUIRED
            if snapshot.evaluation_labels
            else CheckMode.ASSERT_EMPTY
        ),
        provenance=(
            CheckMode.REQUIRED
            if snapshot.private_provenance
            else CheckMode.ASSERT_EMPTY
        ),
        fitted_state=(
            CheckMode.REQUIRED
            if snapshot.fitted_state
            else CheckMode.ASSERT_NO_FIT
        ),
        representation_ids=snapshot.supported_representation_ids,
    )


__all__ = [
    "CheckMode",
    "ConformancePlan",
    "MAXIMUM_REPRESENTATION_IDS",
    "NO_ATOMIC_GRID_REASON",
    "NO_FITTED_COUNTERFACTUAL_PROTOCOL_REASON",
    "NO_FITTED_PREPROCESSING_REASON",
    "NO_RAW_RECONSTRUCTION_REASON",
    "PlanCheck",
    "plan_from_capabilities",
]
