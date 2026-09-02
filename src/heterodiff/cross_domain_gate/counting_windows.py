"""Torch-free conditioning views for the generated atomic-counting gate.

This module performs one deliberately small job: it constructs the two
pre-registered conditioning tasks ``U`` (unconditional) and ``A`` (one
time/type anchor), converts each aligned :class:`ObservationPattern` through
``ObservationPattern.to_model_view``, and rasterizes only that redacted view.

Clean targets and conditioning inputs remain separate.  Source-observation
masks live in :class:`EncodedCountingReference`; conditioning mark masks in
this module are always false.  Event identifiers are used transiently to
select and validate the unique anchored occurrence, but are absent from every
task object, array, digest, and manifest.  This is a bounded representation
control, not a probability model, training result, clinical claim, or evidence
of cross-domain generalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Integral
from typing import Hashable, Mapping, Optional, Protocol, Tuple

import numpy as np

from heterodiff.data.atomic_counting_reference import (
    CountingReferenceLayout,
    EncodedCountingReference,
)
from heterodiff.data.cross_domain_counting_fixtures import (
    CountingFixtureDomain,
    CountingFixtureResourceError,
    CountingFixtureResult,
    M_ACG_1_ID,
    M_ACG_1_RESOURCE_LIMITS,
    M_ACG_1_SHA256,
    P_ACG_1_ID,
    P_ACG_1_RESOURCE_LIMITS,
    P_ACG_1_SHA256,
    build_m_acg_1,
    build_p_acg_1,
)
from heterodiff.events.configuration import EventConfiguration
from heterodiff.events.observations import (
    EventObservation,
    ObservationPattern,
    ObservationView,
    ObservedAnchor,
)
from heterodiff.events.schema import FeatureSchema


_RASTER_SCHEMA_VERSION = "heterodiff-counting-anchor-raster-v1"
_TASK_SCHEMA_VERSION = "heterodiff-counting-task-view-v1"
_TASK_SET_SCHEMA_VERSION = "heterodiff-counting-domain-task-set-v1"
_POLICY_SCHEMA_VERSION = "heterodiff-counting-task-policy-v1"
_SLOT_CAPACITY = 2
_TASK_IDS = ("U", "A")


class CountingTaskError(ValueError):
    """Raised when a conditioning task violates the frozen gate semantics."""


class CountingTaskResourceError(CountingFixtureResourceError):
    """Raised before a task/layout allocation would exceed a frozen ceiling."""


class CountingTaskId(str, Enum):
    """The complete task vocabulary for the pre-registered smoke gate."""

    UNCONDITIONAL = "U"
    ANCHORED = "A"


@dataclass(frozen=True)
class CountingTaskPolicy:
    """Exact domain policy used before any view or reference allocation."""

    domain: CountingFixtureDomain
    fixture_id: str
    source_sha256: str
    target_state_digest: str
    schema_version: str
    reference_length: int
    anchor_time: float
    anchor_type_id: int
    anchor_type_name: str

    def __post_init__(self) -> None:
        if type(self.domain) is not CountingFixtureDomain:
            raise TypeError("domain must be an exact CountingFixtureDomain value")
        for name in (
            "fixture_id",
            "source_sha256",
            "target_state_digest",
            "schema_version",
            "anchor_type_name",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise TypeError("{} must be a nonempty exact string".format(name))
        for name in ("source_sha256", "target_state_digest"):
            digest = getattr(self, name)
            if (
                len(digest) != 64
                or digest.lower() != digest
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError(
                    "{} must be a lowercase SHA-256 digest".format(name)
                )
        object.__setattr__(
            self,
            "reference_length",
            _plain_integer(self.reference_length, name="reference_length", minimum=2),
        )
        if type(self.anchor_time) is not float or not math.isfinite(self.anchor_time):
            raise TypeError("anchor_time must be a finite canonical float")
        if self.anchor_time < 0.0:
            raise ValueError("anchor_time must be nonnegative")
        object.__setattr__(
            self,
            "anchor_type_id",
            _plain_integer(self.anchor_type_id, name="anchor_type_id", minimum=0),
        )

    @property
    def policy_digest(self) -> str:
        return _domain_digest(
            "heterodiff.counting-task-policy.v1",
            {
                "anchor_marks_visible": False,
                "anchor_time": self.anchor_time,
                "anchor_type_id": self.anchor_type_id,
                "anchor_type_name": self.anchor_type_name,
                "cardinality_visible": False,
                "domain": self.domain.value,
                "fixture_id": self.fixture_id,
                "reference_length": self.reference_length,
                "schema_version": _POLICY_SCHEMA_VERSION,
                "source_sha256": self.source_sha256,
                "target_state_digest": self.target_state_digest,
                "target_schema_version": self.schema_version,
                "task_ids": list(_TASK_IDS),
            },
        )

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        return (
            CountingTaskPolicy,
            (
                self.domain,
                self.fixture_id,
                self.source_sha256,
                self.target_state_digest,
                self.schema_version,
                self.reference_length,
                self.anchor_time,
                self.anchor_type_id,
                self.anchor_type_name,
            ),
        )


def _plain_integer(value: object, *, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer".format(name))
    result = int(value)
    if result < minimum:
        raise ValueError("{} must be at least {}".format(name, minimum))
    return result


M_ACG_1_TASK_POLICY = CountingTaskPolicy(
    domain=CountingFixtureDomain.MUSIC,
    fixture_id=M_ACG_1_ID,
    source_sha256=M_ACG_1_SHA256,
    target_state_digest="9c8cdf5ab62fa722f6a0ac0d3a16e447bc16bc9da3b2bf34d3c628fe965f0789",
    schema_version="maestro-midi-clock-counting-fixture-v1",
    reference_length=256,
    anchor_time=1.0,
    anchor_type_id=67,
    anchor_type_name="midi_pitch_67",
)

P_ACG_1_TASK_POLICY = CountingTaskPolicy(
    domain=CountingFixtureDomain.CLINICAL_STYLE,
    fixture_id=P_ACG_1_ID,
    source_sha256=P_ACG_1_SHA256,
    target_state_digest="04b0865267f8c6b76e6b6dfd4c5d309f3c82d2d5bfe1ccf45adc9ec64787adde",
    schema_version="physionet-2012-counting-fixture-v1",
    reference_length=2881,
    anchor_time=5.0,
    anchor_type_id=1,
    anchor_type_name="Temp",
)


def _canonical_json_bytes(value: object) -> bytes:
    try:
        payload = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise TypeError("value is not canonical-JSON serializable") from exc
    return payload.encode("utf-8")


def _domain_digest(domain: str, value: object) -> str:
    payload = _canonical_json_bytes(value)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


class _HashWriter(Protocol):
    def update(self, data: bytes) -> object:
        ...


def _update_array_digest(digest: _HashWriter, name: str, value: np.ndarray) -> None:
    metadata = _canonical_json_bytes(
        {"dtype": value.dtype.str, "name": name, "shape": list(value.shape)}
    )
    digest.update(len(metadata).to_bytes(8, "big"))
    digest.update(metadata)
    raw = value.tobytes(order="C")
    digest.update(len(raw).to_bytes(8, "big"))
    digest.update(raw)


def _immutable_array(
    value: object,
    *,
    name: str,
    dtype: np.dtype,
    shape: Tuple[int, ...],
) -> np.ndarray:
    if type(value) is not np.ndarray:
        raise TypeError("{} must be an exact NumPy array".format(name))
    if value.dtype != dtype:
        raise TypeError(
            "{} must have dtype {}; got {}".format(name, dtype.name, value.dtype)
        )
    if value.shape != shape:
        raise ValueError("{} has shape {}; expected {}".format(name, value.shape, shape))
    copied = np.array(value, dtype=dtype, copy=True, order="C")
    if dtype.kind == "f":
        if np.any(~np.isfinite(copied)):
            raise ValueError("{} must contain only finite values".format(name))
        copied[copied == 0.0] = 0.0
    return np.frombuffer(copied.tobytes(order="C"), dtype=dtype).reshape(shape)


def _safe_identifier(value: object, *, name: str) -> Optional[Hashable]:
    """Admit only deterministic, recursively immutable built-in identifiers."""

    if value is None:
        return None
    if type(value) in (str, bytes, int, bool):
        return value  # type: ignore[return-value]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("{} cannot contain a nonfinite float".format(name))
        return 0.0 if value == 0.0 else value
    if type(value) is tuple:
        return tuple(
            _safe_identifier(item, name=name) for item in value
        )  # type: ignore[return-value]
    if type(value) is frozenset:
        return frozenset(
            _safe_identifier(item, name=name) for item in value
        )  # type: ignore[return-value]
    raise TypeError(
        "{} must use recursively immutable built-in identifiers".format(name)
    )


def _copy_layout(layout: CountingReferenceLayout) -> CountingReferenceLayout:
    if type(layout) is not CountingReferenceLayout:
        raise TypeError("layout must be an exact CountingReferenceLayout instance")
    return CountingReferenceLayout(
        layout.schema, layout.reference_length, layout.slot_capacity
    )


def _copy_encoded_reference(
    target: EncodedCountingReference,
) -> EncodedCountingReference:
    """Re-run the complete reference constructor at a consumer boundary."""

    if type(target) is not EncodedCountingReference:
        raise TypeError("target must be an exact EncodedCountingReference instance")
    return EncodedCountingReference(
        layout=target.layout,
        exact_counts=target.exact_counts,
        occurrence_present=target.occurrence_present,
        clean_presence=target.clean_presence,
        native_mark_values=target.native_mark_values,
        transformed_mark_values=target.transformed_mark_values,
        structural_applicability=target.structural_applicability,
        source_observed=target.source_observed,
        transformed_clean_presence=target.transformed_clean_presence,
        transformed_structural_applicability=(
            target.transformed_structural_applicability
        ),
        transformed_source_observed=target.transformed_source_observed,
        time_observed=target.time_observed,
        type_observed=target.type_observed,
        cardinality_observed=target.cardinality_observed,
        valid_time_mask=target.valid_time_mask,
        position_coordinates=target.position_coordinates,
        event_ids=target.event_ids,
        sample_id=target.sample_id,
        group_id=target.group_id,
    )


@dataclass(frozen=True, eq=False)
class CountingAnchorRaster:
    """Immutable native and padded arrays derived only from an ObservationView."""

    layout: CountingReferenceLayout
    native_anchor_count: np.ndarray
    native_anchor_count_observed: np.ndarray
    anchor_count: np.ndarray
    anchor_count_observed: np.ndarray
    native_anchor_mark_values: np.ndarray
    native_anchor_mark_observed: np.ndarray
    anchor_mark_values: np.ndarray
    anchor_mark_observed: np.ndarray
    anchor_cardinality_observed: bool = False

    def __post_init__(self) -> None:
        layout = _copy_layout(self.layout)
        object.__setattr__(self, "layout", layout)
        a = layout.native_atom_count
        r = layout.reference_length
        k = layout.number_of_types
        s = layout.slot_capacity
        f = len(layout.field_coordinates)
        int_dtype = np.dtype(np.int64)
        bool_dtype = np.dtype(np.bool_)
        float_dtype = np.dtype(np.float64)
        for name, dtype, shape in (
            ("native_anchor_count", int_dtype, (a, k)),
            ("native_anchor_count_observed", bool_dtype, (a, k)),
            ("anchor_count", int_dtype, (r, k)),
            ("anchor_count_observed", bool_dtype, (r, k)),
            ("native_anchor_mark_values", float_dtype, (a, k, s, f)),
            ("native_anchor_mark_observed", bool_dtype, (a, k, s, f)),
            ("anchor_mark_values", float_dtype, (r, k, s, f)),
            ("anchor_mark_observed", bool_dtype, (r, k, s, f)),
        ):
            object.__setattr__(
                self,
                name,
                _immutable_array(
                    getattr(self, name), name=name, dtype=dtype, shape=shape
                ),
            )
        if type(self.anchor_cardinality_observed) is not bool:
            raise TypeError("anchor_cardinality_observed must be a boolean")
        self._validate()

    def _validate(self) -> None:
        a = self.layout.native_atom_count
        if self.anchor_cardinality_observed:
            raise CountingTaskError("conditioning cardinality must remain hidden")
        if np.any((self.native_anchor_count < 0) | (self.native_anchor_count > 1)):
            raise CountingTaskError("native anchor counts must lie in {0,1}")
        if not np.array_equal(
            self.native_anchor_count_observed, self.native_anchor_count == 1
        ):
            raise CountingTaskError(
                "an observed anchor count must be exactly one and vice versa"
            )
        if int(self.native_anchor_count_observed.sum()) > 1:
            raise CountingTaskError("the frozen tasks allow at most one anchor")
        if not np.array_equal(self.anchor_count[:a], self.native_anchor_count):
            raise CountingTaskError("padded anchor counts disagree with native counts")
        if not np.array_equal(
            self.anchor_count_observed[:a], self.native_anchor_count_observed
        ):
            raise CountingTaskError(
                "padded anchor observation mask disagrees with the native mask"
            )
        if np.any(self.anchor_count[a:] != 0) or np.any(
            self.anchor_count_observed[a:]
        ):
            raise CountingTaskError("padding cannot contain an anchor")
        if np.any(self.native_anchor_mark_values != 0.0) or np.any(
            self.anchor_mark_values != 0.0
        ):
            raise CountingTaskError("hidden anchor mark values must be canonical zero")
        if np.any(self.native_anchor_mark_observed) or np.any(
            self.anchor_mark_observed
        ):
            raise CountingTaskError("all anchor marks must remain hidden")
        if not np.array_equal(
            self.anchor_mark_values[:a], self.native_anchor_mark_values
        ) or not np.array_equal(
            self.anchor_mark_observed[:a], self.native_anchor_mark_observed
        ):
            raise CountingTaskError("padded anchor marks disagree with native marks")

    @property
    def number_of_anchors(self) -> int:
        return int(self.native_anchor_count_observed.sum())

    @property
    def array_digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(b"heterodiff.counting-anchor-raster.arrays.v1\x00")
        header = _canonical_json_bytes(
            {
                "anchor_cardinality_observed": self.anchor_cardinality_observed,
                "layout_digest": self.layout.layout_digest,
                "schema_version": _RASTER_SCHEMA_VERSION,
            }
        )
        digest.update(len(header).to_bytes(8, "big"))
        digest.update(header)
        for name in (
            "native_anchor_count",
            "native_anchor_count_observed",
            "anchor_count",
            "anchor_count_observed",
            "native_anchor_mark_values",
            "native_anchor_mark_observed",
            "anchor_mark_values",
            "anchor_mark_observed",
        ):
            _update_array_digest(digest, name, getattr(self, name))
        return digest.hexdigest()

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        return (
            CountingAnchorRaster,
            (
                self.layout,
                self.native_anchor_count,
                self.native_anchor_count_observed,
                self.anchor_count,
                self.anchor_count_observed,
                self.native_anchor_mark_values,
                self.native_anchor_mark_observed,
                self.anchor_mark_values,
                self.anchor_mark_observed,
                self.anchor_cardinality_observed,
            ),
        )

    def validate(self) -> None:
        """Re-run construction, including dtype/shape/immutability checks."""

        CountingAnchorRaster(
            self.layout,
            self.native_anchor_count,
            self.native_anchor_count_observed,
            self.anchor_count,
            self.anchor_count_observed,
            self.native_anchor_mark_values,
            self.native_anchor_mark_observed,
            self.anchor_mark_values,
            self.anchor_mark_observed,
            self.anchor_cardinality_observed,
        )


def rasterize_counting_observation_view(
    observation_view: ObservationView,
    layout: CountingReferenceLayout,
) -> CountingAnchorRaster:
    """Rasterize only a redacted time/type view; target rows are not accepted."""

    if type(observation_view) is not ObservationView:
        raise TypeError("observation_view must be an exact ObservationView instance")
    frozen_layout = _copy_layout(layout)
    if observation_view.cardinality is not None:
        raise CountingTaskError("conditioning cardinality must be hidden")
    if len(observation_view.anchors) > 1:
        raise CountingTaskError("the frozen tasks permit at most one visible anchor")

    a = frozen_layout.native_atom_count
    r = frozen_layout.reference_length
    k = frozen_layout.number_of_types
    s = frozen_layout.slot_capacity
    f = len(frozen_layout.field_coordinates)
    native_count = np.zeros((a, k), dtype=np.int64)
    native_observed = np.zeros((a, k), dtype=np.bool_)
    assert frozen_layout.schema.time_reference is not None
    atoms = frozen_layout.schema.time_reference.atoms
    type_ids = frozen_layout.type_ids

    seen_cells = set()
    for anchor in observation_view.anchors:
        if type(anchor) is not ObservedAnchor:
            raise TypeError("view anchors must be exact ObservedAnchor instances")
        if anchor.event_time is None or anchor.event_type is None:
            raise CountingTaskError(
                "a count anchor must expose both time and type"
            )
        if anchor.marks:
            raise CountingTaskError("the frozen tasks expose no anchor marks")
        atom_matches = tuple(
            index for index, value in enumerate(atoms) if value == anchor.event_time
        )
        if len(atom_matches) != 1:
            raise CountingTaskError("anchor time is absent or nonunique on the atomic grid")
        type_matches = tuple(
            index for index, value in enumerate(type_ids) if value == anchor.event_type
        )
        if len(type_matches) != 1:
            raise CountingTaskError("anchor type is absent or nonunique in the schema")
        cell = (atom_matches[0], type_matches[0])
        if cell in seen_cells:
            raise CountingTaskError("duplicate visible anchors are not permitted")
        seen_cells.add(cell)
        native_count[cell] = 1
        native_observed[cell] = True

    padded_count = np.zeros((r, k), dtype=np.int64)
    padded_observed = np.zeros((r, k), dtype=np.bool_)
    padded_count[:a] = native_count
    padded_observed[:a] = native_observed
    return CountingAnchorRaster(
        layout=frozen_layout,
        native_anchor_count=native_count,
        native_anchor_count_observed=native_observed,
        anchor_count=padded_count,
        anchor_count_observed=padded_observed,
        native_anchor_mark_values=np.zeros((a, k, s, f), dtype=np.float64),
        native_anchor_mark_observed=np.zeros((a, k, s, f), dtype=np.bool_),
        anchor_mark_values=np.zeros((r, k, s, f), dtype=np.float64),
        anchor_mark_observed=np.zeros((r, k, s, f), dtype=np.bool_),
        anchor_cardinality_observed=False,
    )


def _copy_observation_view(view: ObservationView) -> ObservationView:
    if type(view) is not ObservationView:
        raise TypeError("observation_view must be an exact ObservationView instance")
    anchors = []
    for anchor in view.anchors:
        if type(anchor) is not ObservedAnchor:
            raise TypeError("view anchors must be exact ObservedAnchor instances")
        anchors.append(
            ObservedAnchor(
                event_time=anchor.event_time,
                event_type=anchor.event_type,
                marks=dict(anchor.marks),
            )
        )
    return ObservationView(anchors=tuple(anchors), cardinality=view.cardinality)


@dataclass(frozen=True, eq=False)
class CountingTaskView:
    """One ID-free redacted view and its exact deterministic raster."""

    task_id: CountingTaskId
    observation_view: ObservationView
    raster: CountingAnchorRaster
    target_state_digest: str

    def __post_init__(self) -> None:
        if type(self.task_id) is not CountingTaskId:
            raise TypeError("task_id must be an exact CountingTaskId value")
        view = _copy_observation_view(self.observation_view)
        object.__setattr__(self, "observation_view", view)
        if type(self.raster) is not CountingAnchorRaster:
            raise TypeError("raster must be an exact CountingAnchorRaster instance")
        raster = CountingAnchorRaster(
            self.raster.layout,
            self.raster.native_anchor_count,
            self.raster.native_anchor_count_observed,
            self.raster.anchor_count,
            self.raster.anchor_count_observed,
            self.raster.native_anchor_mark_values,
            self.raster.native_anchor_mark_observed,
            self.raster.anchor_mark_values,
            self.raster.anchor_mark_observed,
            self.raster.anchor_cardinality_observed,
        )
        object.__setattr__(self, "raster", raster)
        if (
            type(self.target_state_digest) is not str
            or len(self.target_state_digest) != 64
            or self.target_state_digest.lower() != self.target_state_digest
            or any(
                character not in "0123456789abcdef"
                for character in self.target_state_digest
            )
        ):
            raise ValueError("target_state_digest must be a lowercase SHA-256 digest")
        rebuilt = rasterize_counting_observation_view(view, self.raster.layout)
        if rebuilt.array_digest != self.raster.array_digest:
            raise CountingTaskError("raster is not the exact image of its redacted view")
        expected = 0 if self.task_id is CountingTaskId.UNCONDITIONAL else 1
        if self.raster.number_of_anchors != expected:
            raise CountingTaskError(
                "task {} requires exactly {} anchors".format(self.task_id.value, expected)
            )

    @property
    def task_digest(self) -> str:
        anchors = [
            {
                "event_time": anchor.event_time,
                "event_type": anchor.event_type,
                "marks": [],
            }
            for anchor in self.observation_view.anchors
        ]
        return _domain_digest(
            "heterodiff.counting-task-view.v1",
            {
                "anchors": anchors,
                "cardinality": None,
                "raster_digest": self.raster.array_digest,
                "schema_version": _TASK_SCHEMA_VERSION,
                "target_state_digest": self.target_state_digest,
                "task_id": self.task_id.value,
            },
        )

    def public_manifest(self) -> Mapping[str, object]:
        return {
            "anchor_count": self.raster.number_of_anchors,
            "cardinality_observed": False,
            "raster_digest": self.raster.array_digest,
            "schema_version": _TASK_SCHEMA_VERSION,
            "target_state_digest": self.target_state_digest,
            "task_digest": self.task_digest,
            "task_id": self.task_id.value,
            "visible_mark_count": 0,
        }

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        anchor_payload = tuple(
            (anchor.event_time, anchor.event_type, tuple(anchor.marks.items()))
            for anchor in self.observation_view.anchors
        )
        return (
            _restore_counting_task_view,
            (
                self.task_id,
                anchor_payload,
                self.observation_view.cardinality,
                self.raster,
                self.target_state_digest,
            ),
        )

    def validate(self) -> None:
        """Re-run redacted-view and nested-raster construction checks."""

        CountingTaskView(
            self.task_id,
            self.observation_view,
            self.raster,
            self.target_state_digest,
        )


def _restore_counting_task_view(
    task_id: CountingTaskId,
    anchors: Tuple[
        Tuple[
            Optional[float],
            Optional[int],
            Tuple[Tuple[str, Tuple[float, ...]], ...],
        ],
        ...,
    ],
    cardinality: Optional[int],
    raster: CountingAnchorRaster,
    target_state_digest: str,
) -> CountingTaskView:
    view = ObservationView(
        anchors=tuple(
            ObservedAnchor(event_time=time, event_type=event_type, marks=dict(marks))
            for time, event_type, marks in anchors
        ),
        cardinality=cardinality,
    )
    return CountingTaskView(task_id, view, raster, target_state_digest)


def _policy_for_domain(domain: CountingFixtureDomain) -> CountingTaskPolicy:
    if type(domain) is not CountingFixtureDomain:
        raise TypeError("domain must be an exact CountingFixtureDomain value")
    if domain is CountingFixtureDomain.MUSIC:
        return M_ACG_1_TASK_POLICY
    return P_ACG_1_TASK_POLICY


def _validate_configuration_identifiers(configuration: EventConfiguration) -> None:
    seen = set()
    for event in configuration.events:
        event_id = _safe_identifier(event.event_id, name="event_id")
        if event_id is None:
            raise CountingTaskError(
                "every gate occurrence needs a private identifier before redaction"
            )
        if event_id in seen:
            raise CountingTaskError("event identifiers must be unique before redaction")
        seen.add(event_id)


def _copy_configuration(configuration: EventConfiguration) -> EventConfiguration:
    """Reconstruct the exact public tree instead of trusting a frozen shell."""

    if type(configuration) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration instance")
    if type(configuration.schema) is not FeatureSchema:
        raise TypeError("configuration schema must be an exact FeatureSchema instance")
    if type(configuration.events) is not tuple:
        raise TypeError("configuration events must be an exact tuple")
    if type(configuration.observed) is not ObservationPattern:
        raise TypeError(
            "configuration observed must be an exact ObservationPattern instance"
        )
    return EventConfiguration(
        schema=configuration.schema,
        events=configuration.events,
        observed=configuration.observed,
        sample_id=configuration.sample_id,
        group_id=configuration.group_id,
    )


def _validate_target_alignment(
    configuration: EventConfiguration,
    target: EncodedCountingReference,
) -> None:
    if type(configuration) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration instance")
    if type(target) is not EncodedCountingReference:
        raise TypeError("target must be an exact EncodedCountingReference instance")
    target._validate_semantics()
    try:
        candidate_layout = CountingReferenceLayout(
            configuration.schema,
            target.layout.reference_length,
            target.layout.slot_capacity,
        )
    except ValueError as exc:
        raise CountingTaskError(
            "configuration schema does not match the padded target"
        ) from exc
    if candidate_layout.schema_digest != target.schema_digest:
        raise CountingTaskError("configuration schema does not match the padded target")
    decoded = target.to_configuration()
    if decoded.state_key() != configuration.state_key():
        raise CountingTaskError("configuration state does not match the padded target")
    if decoded.observed != configuration.observed:
        raise CountingTaskError(
            "configuration source-observation masks do not match the padded target"
        )
    # Exact duplicate model atoms with equal source-observation signatures have
    # no intrinsic occurrence order.  Bind each private id to that complete
    # equivalence class so provenance may permute only within such a class,
    # never across a different time/type/mark atom or observation signature.
    def provenance_bindings(value: EventConfiguration) -> Mapping[
        Hashable, Tuple[object, ...]
    ]:
        assert value.observed is not None
        result = {}
        for event, observation in zip(value.events, value.observed.events):
            event_id = _safe_identifier(event.event_id, name="event_id")
            if event_id is None or event_id in result:
                raise CountingTaskError(
                    "configuration occurrence sidecars must be unique and non-null"
                )
            result[event_id] = (
                event.model_key(),
                observation.signature_key(),
            )
        return result

    if provenance_bindings(decoded) != provenance_bindings(configuration):
        raise CountingTaskError(
            "configuration occurrence sidecars are attached to different model atoms"
        )
    if decoded.sample_id != configuration.sample_id or decoded.group_id != configuration.group_id:
        raise CountingTaskError("configuration sample/group sidecars do not match target")


def build_counting_task_views(
    configuration: EventConfiguration,
    target: EncodedCountingReference,
    *,
    domain: CountingFixtureDomain,
) -> Tuple[CountingTaskView, CountingTaskView]:
    """Build exactly ``(U, A)`` through the public observation redaction API."""

    configuration = _copy_configuration(configuration)
    target = _copy_encoded_reference(target)
    _validate_target_alignment(configuration, target)
    policy = _policy_for_domain(domain)
    if target.schema.version != policy.schema_version:
        raise CountingTaskError("target schema is not the frozen domain schema")
    if target.layout.reference_length != policy.reference_length:
        raise CountingTaskError("target reference length is not frozen for the domain")
    if target.layout.slot_capacity != _SLOT_CAPACITY:
        raise CountingTaskResourceError("the gate requires slot capacity exactly two")
    assert configuration.observed is not None
    if not configuration.observed.cardinality_observed or not target.cardinality_observed:
        raise CountingTaskError(
            "source cardinality must be observed before conditioning redaction"
        )
    _validate_configuration_identifiers(configuration)

    event_type = configuration.schema.event_type(policy.anchor_type_id)
    if event_type.name != policy.anchor_type_name:
        raise CountingTaskError("anchored event type name disagrees with frozen policy")
    candidates = tuple(
        index
        for index, event in enumerate(configuration.events)
        if event.event_time == policy.anchor_time
        and event.event_type == policy.anchor_type_id
    )
    if len(candidates) != 1:
        raise CountingTaskError("the anchored time/type atom must contain one occurrence")
    anchor_index = candidates[0]
    source_observation = configuration.observed.events[anchor_index]
    if not source_observation.time_observed or not source_observation.type_observed:
        raise CountingTaskError("the frozen anchor time and type must be source-observed")
    assert configuration.schema.time_reference is not None
    atom_matches = tuple(
        index
        for index, value in enumerate(configuration.schema.time_reference.atoms)
        if value == policy.anchor_time
    )
    type_matches = tuple(
        index
        for index, value in enumerate(target.layout.type_ids)
        if value == policy.anchor_type_id
    )
    if len(atom_matches) != 1 or len(type_matches) != 1:
        raise CountingTaskError("the frozen anchor is nonunique or outside the grid")
    if int(target.exact_counts[atom_matches[0], type_matches[0]]) != 1:
        raise CountingTaskError("the frozen anchored cell must have clean count one")

    # U is built with the canonical helper and then redacted.  A uses the
    # selected private id only to construct the aligned mask; the returned view
    # contains values but no identifier or target alignment.
    unconditional_pattern = ObservationPattern.fully_hidden(configuration)
    unconditional_view = unconditional_pattern.to_model_view(configuration)
    anchor_event_id = configuration.events[anchor_index].event_id
    anchored_observations = tuple(
        EventObservation(
            time_observed=(event.event_id == anchor_event_id),
            type_observed=(event.event_id == anchor_event_id),
            observed_marks=frozenset(),
        )
        for event in configuration.events
    )
    anchored_pattern = ObservationPattern(
        events=anchored_observations,
        cardinality_observed=False,
    )
    anchored_view = anchored_pattern.to_model_view(configuration)
    if (
        len(anchored_view.anchors) != 1
        or anchored_view.anchors[0].event_time != policy.anchor_time
        or anchored_view.anchors[0].event_type != policy.anchor_type_id
        or anchored_view.anchors[0].marks
        or anchored_view.cardinality is not None
    ):
        raise CountingTaskError("ObservationPattern redaction did not produce policy A")

    tasks = (
        CountingTaskView(
            task_id=CountingTaskId.UNCONDITIONAL,
            observation_view=unconditional_view,
            raster=rasterize_counting_observation_view(
                unconditional_view, target.layout
            ),
            target_state_digest=target.state_digest,
        ),
        CountingTaskView(
            task_id=CountingTaskId.ANCHORED,
            observation_view=anchored_view,
            raster=rasterize_counting_observation_view(anchored_view, target.layout),
            target_state_digest=target.state_digest,
        ),
    )
    return tasks


def _identifier_free_target(
    target: EncodedCountingReference,
) -> EncodedCountingReference:
    """Detach clean arrays while removing every occurrence/sample/group id."""

    if type(target) is not EncodedCountingReference:
        raise TypeError("target must be an exact EncodedCountingReference instance")
    r = target.layout.reference_length
    k = target.layout.number_of_types
    s = target.layout.slot_capacity
    empty_ids = tuple(
        tuple(tuple(None for _ in range(s)) for _ in range(k)) for _ in range(r)
    )
    result = EncodedCountingReference(
        layout=target.layout,
        exact_counts=target.exact_counts,
        occurrence_present=target.occurrence_present,
        clean_presence=target.clean_presence,
        native_mark_values=target.native_mark_values,
        transformed_mark_values=target.transformed_mark_values,
        structural_applicability=target.structural_applicability,
        source_observed=target.source_observed,
        transformed_clean_presence=target.transformed_clean_presence,
        transformed_structural_applicability=target.transformed_structural_applicability,
        transformed_source_observed=target.transformed_source_observed,
        time_observed=target.time_observed,
        type_observed=target.type_observed,
        cardinality_observed=target.cardinality_observed,
        valid_time_mask=target.valid_time_mask,
        position_coordinates=target.position_coordinates,
        event_ids=empty_ids,
        sample_id="",
        group_id="",
    )
    if result.state_digest != target.state_digest:
        raise CountingTaskError("identifier redaction changed the numerical target")
    return result


@dataclass(frozen=True, eq=False)
class CountingDomainTaskSet:
    """One generated train group, one ID-free target, and exactly tasks U/A."""

    domain: CountingFixtureDomain
    fixture_id: str
    source_sha256: str
    source_split: str
    source_sample_id: str
    source_group_id: str
    target: EncodedCountingReference
    tasks: Tuple[CountingTaskView, CountingTaskView]

    def __post_init__(self) -> None:
        policy = _policy_for_domain(self.domain)
        for name in (
            "fixture_id",
            "source_sha256",
            "source_split",
            "source_sample_id",
            "source_group_id",
        ):
            if type(getattr(self, name)) is not str:
                raise TypeError("{} must be an exact string".format(name))
        if self.fixture_id != policy.fixture_id or self.source_sha256 != policy.source_sha256:
            raise CountingTaskError("task set is not bound to the frozen source fixture")
        if self.source_split != "train":
            raise CountingTaskError("the gate task set must originate from train")
        expected_sample_id, expected_group_id = (
            ("M-ACG-1", "synthetic-maestro-group-1")
            if self.domain is CountingFixtureDomain.MUSIC
            else ("900001", "900001")
        )
        if (
            self.source_sample_id != expected_sample_id
            or self.source_group_id != expected_group_id
        ):
            raise CountingTaskError(
                "sample and natural group sidecars must match the frozen fixture"
            )
        if type(self.target) is not EncodedCountingReference:
            raise TypeError("target must be an exact EncodedCountingReference instance")
        target = _copy_encoded_reference(self.target)
        object.__setattr__(self, "target", target)
        if self.target.state_digest != policy.target_state_digest:
            raise CountingTaskError(
                "task-set target is not the exact conversion bound to the source fixture"
            )
        if self.target.sample_id or self.target.group_id:
            raise CountingTaskError("the training target must discard sample/group ids")
        if any(
            event_id is not None
            for row in self.target.event_ids
            for cell in row
            for event_id in cell
        ):
            raise CountingTaskError("the training target must discard event ids")
        if type(self.tasks) is not tuple or len(self.tasks) != 2:
            raise CountingTaskError("tasks must be the exact tuple (U, A)")
        if any(type(task) is not CountingTaskView for task in self.tasks):
            raise TypeError("tasks must contain exact CountingTaskView instances")
        tasks = tuple(
            CountingTaskView(
                task.task_id,
                task.observation_view,
                task.raster,
                task.target_state_digest,
            )
            for task in self.tasks
        )
        object.__setattr__(self, "tasks", tasks)
        if tuple(task.task_id.value for task in self.tasks) != _TASK_IDS:
            raise CountingTaskError("tasks must be ordered exactly as (U, A)")
        for task in self.tasks:
            if task.raster.layout.layout_digest != self.target.layout_digest:
                raise CountingTaskError("task layout does not match the target layout")
            if task.target_state_digest != self.target.state_digest:
                raise CountingTaskError("task does not bind the target state")
        anchored = self.tasks[1].raster
        assert self.target.schema.time_reference is not None
        atom_index = self.target.schema.time_reference.atoms.index(
            policy.anchor_time
        )
        type_index = self.target.layout.type_ids.index(policy.anchor_type_id)
        if int(self.target.exact_counts[atom_index, type_index]) != 1:
            raise CountingTaskError("the anchored target cell is not count one")
        if not anchored.native_anchor_count_observed[atom_index, type_index]:
            raise CountingTaskError("task A does not expose the frozen anchor cell")

    @property
    def policy_digest(self) -> str:
        return _policy_for_domain(self.domain).policy_digest

    @property
    def task_set_digest(self) -> str:
        """Identifier/provenance-free binding for the trainer-facing objects."""

        return _domain_digest(
            "heterodiff.counting-domain-task-set.v1",
            {
                "domain": self.domain.value,
                "layout_digest": self.target.layout_digest,
                "policy_digest": self.policy_digest,
                "schema_version": _TASK_SET_SCHEMA_VERSION,
                "target_state_digest": self.target.state_digest,
                "task_digests": [task.task_digest for task in self.tasks],
            },
        )

    @property
    def task_group_ids(self) -> Tuple[str, str]:
        """Sidecar proof that task expansion happens inside one natural group."""

        return (self.source_group_id, self.source_group_id)

    def public_manifest(self) -> Mapping[str, object]:
        """Return generated-fixture metadata and no event/sample/group identifier."""

        return {
            "domain": self.domain.value,
            "fixture_id": self.fixture_id,
            "group_integrity": len(set(self.task_group_ids)) == 1,
            "policy_digest": self.policy_digest,
            "schema_version": _TASK_SET_SCHEMA_VERSION,
            "source_sha256": self.source_sha256,
            "target": self.target.public_manifest(),
            "task_set_digest": self.task_set_digest,
            "tasks": [task.public_manifest() for task in self.tasks],
        }

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        return (
            CountingDomainTaskSet,
            (
                self.domain,
                self.fixture_id,
                self.source_sha256,
                self.source_split,
                self.source_sample_id,
                self.source_group_id,
                self.target,
                self.tasks,
            ),
        )

    def validate(self) -> None:
        """Re-run the complete trainer-facing boundary after unsafe mutation."""

        CountingDomainTaskSet(
            self.domain,
            self.fixture_id,
            self.source_sha256,
            self.source_split,
            self.source_sample_id,
            self.source_group_id,
            self.target,
            self.tasks,
        )


def _preflight_fixture_layout(
    fixture: CountingFixtureResult,
    *,
    policy: CountingTaskPolicy,
    reference_length: int,
    slot_capacity: int,
) -> None:
    """Run all known static/count checks before constructing dense grid arrays."""

    if fixture.fixture_id != policy.fixture_id or fixture.source_sha256 != policy.source_sha256:
        raise CountingTaskError("fixture identity is not the frozen gate source")
    if fixture.domain is not policy.domain:
        raise CountingTaskError("fixture domain disagrees with task policy")
    if fixture.source_split != "train":
        raise CountingTaskError("task expansion is permitted only after train grouping")
    if fixture.configuration.schema.version != policy.schema_version:
        raise CountingTaskError("fixture schema version disagrees with task policy")
    if reference_length != policy.reference_length:
        raise CountingTaskResourceError(
            "reference length must equal the pre-registered domain length"
        )
    if slot_capacity != _SLOT_CAPACITY:
        raise CountingTaskResourceError("slot capacity must equal two; no truncation allowed")
    limits = fixture.resource_limits
    schema = fixture.configuration.schema
    assert schema.time_reference is not None
    if reference_length > limits.maximum_reference_time_positions:
        raise CountingTaskResourceError("reference time-axis ceiling would be exceeded")
    if len(schema.time_reference.atoms) > limits.maximum_atomic_time_positions:
        raise CountingTaskResourceError("native atomic time-axis ceiling was exceeded")
    if len(schema.event_types) > limits.maximum_declared_event_types:
        raise CountingTaskResourceError("declared event-type ceiling was exceeded")
    required_capacity = max(fixture.occupied_cell_counts.values(), default=0)
    if required_capacity > slot_capacity:
        raise CountingTaskResourceError("requested capacity would truncate a cell")
    maximum_dimension = max(
        sum(field.dimension for field in event_type.fields)
        for event_type in schema.event_types
    )
    if maximum_dimension > limits.maximum_mark_scalar_dimensions_per_occurrence:
        raise CountingTaskResourceError("per-occurrence mark ceiling was exceeded")


def build_counting_domain_task_set(
    fixture: CountingFixtureResult,
    *,
    reference_length: Optional[int] = None,
    slot_capacity: int = _SLOT_CAPACITY,
) -> CountingDomainTaskSet:
    """Convert one exact generated train fixture into target plus tasks U/A."""

    if type(fixture) is not CountingFixtureResult:
        raise TypeError("fixture must be an exact CountingFixtureResult instance")
    fixture = CountingFixtureResult(
        fixture_id=fixture.fixture_id,
        domain=fixture.domain,
        source_format=fixture.source_format,
        source_split=fixture.source_split,
        source_sha256=fixture.source_sha256,
        source_byte_length=fixture.source_byte_length,
        configuration=fixture.configuration,
        private_provenance=fixture.private_provenance,
        resource_limits=fixture.resource_limits,
        public_notice=fixture.public_notice,
    )
    policy = _policy_for_domain(fixture.domain)
    resolved_length = (
        policy.reference_length
        if reference_length is None
        else _plain_integer(reference_length, name="reference_length", minimum=2)
    )
    resolved_capacity = _plain_integer(
        slot_capacity, name="slot_capacity", minimum=1
    )
    _preflight_fixture_layout(
        fixture,
        policy=policy,
        reference_length=resolved_length,
        slot_capacity=resolved_capacity,
    )
    configuration = fixture.configuration
    if not configuration.sample_id or not configuration.group_id:
        raise CountingTaskError("fixture must have a sample and natural group before tasks")
    grid = fixture.to_atomic_counting_grid(
        max_occurrences_per_cell=resolved_capacity
    )
    layout = CountingReferenceLayout.from_tensor(
        grid,
        reference_length=resolved_length,
        slot_capacity=resolved_capacity,
    )
    private_target = layout.encode(grid)
    tasks = build_counting_task_views(
        configuration,
        private_target,
        domain=fixture.domain,
    )
    target = _identifier_free_target(private_target)
    return CountingDomainTaskSet(
        domain=fixture.domain,
        fixture_id=fixture.fixture_id,
        source_sha256=fixture.source_sha256,
        source_split=fixture.source_split,
        source_sample_id=configuration.sample_id,
        source_group_id=configuration.group_id,
        target=target,
        tasks=tasks,
    )


def build_m_acg_1_task_set(
    *,
    reference_length: int = 256,
    slot_capacity: int = _SLOT_CAPACITY,
) -> CountingDomainTaskSet:
    """Build the exact generated music target and its tasks U/A."""

    # Reject altered bounds before parsing the embedded bytes.
    resolved_length = _plain_integer(
        reference_length, name="reference_length", minimum=2
    )
    resolved_capacity = _plain_integer(
        slot_capacity, name="slot_capacity", minimum=1
    )
    if (
        resolved_length != 256
        or resolved_length
        > M_ACG_1_RESOURCE_LIMITS.maximum_reference_time_positions
    ):
        raise CountingTaskResourceError("M-ACG-1 reference length must equal 256")
    if resolved_capacity != _SLOT_CAPACITY:
        raise CountingTaskResourceError("M-ACG-1 slot capacity must equal two")
    return build_counting_domain_task_set(
        build_m_acg_1(),
        reference_length=resolved_length,
        slot_capacity=resolved_capacity,
    )


def build_p_acg_1_task_set(
    *,
    reference_length: int = 2881,
    slot_capacity: int = _SLOT_CAPACITY,
) -> CountingDomainTaskSet:
    """Build the exact generated clinical-style target and its tasks U/A."""

    # Reject altered bounds before parsing the embedded bytes.
    resolved_length = _plain_integer(
        reference_length, name="reference_length", minimum=2
    )
    resolved_capacity = _plain_integer(
        slot_capacity, name="slot_capacity", minimum=1
    )
    if (
        resolved_length != 2881
        or resolved_length
        > P_ACG_1_RESOURCE_LIMITS.maximum_reference_time_positions
    ):
        raise CountingTaskResourceError("P-ACG-1 reference length must equal 2881")
    if resolved_capacity != _SLOT_CAPACITY:
        raise CountingTaskResourceError("P-ACG-1 slot capacity must equal two")
    return build_counting_domain_task_set(
        build_p_acg_1(),
        reference_length=resolved_length,
        slot_capacity=resolved_capacity,
    )


__all__ = [
    "CountingAnchorRaster",
    "CountingDomainTaskSet",
    "CountingTaskError",
    "CountingTaskId",
    "CountingTaskPolicy",
    "CountingTaskResourceError",
    "CountingTaskView",
    "M_ACG_1_TASK_POLICY",
    "P_ACG_1_TASK_POLICY",
    "build_counting_domain_task_set",
    "build_counting_task_views",
    "build_m_acg_1_task_set",
    "build_p_acg_1_task_set",
    "rasterize_counting_observation_view",
]
