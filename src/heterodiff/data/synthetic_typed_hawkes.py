"""A small typed, marked, self-exciting point-process benchmark.

The generator deliberately has no dependency on PyTorch.  It produces native
Python records containing NumPy marks, together with enough ground-truth
metadata to evaluate event-type frequencies, mark distributions, conditional
intensities, and recovery of the excitation kernel.

The intensity convention is

    lambda_k(t) = mu_k + sum_i A[k, z_i] * s(z_i, m_i)
                             * exp(-B[k, z_i] * (t - t_i)),

where ``z_i`` is the source event type and ``s`` is a bounded, mark-dependent
multiplier.  Rows of ``A``/``B`` are target types and columns are source types.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import inf, sqrt
from typing import Iterable, Literal, Optional

import numpy as np
from numpy.typing import NDArray

from heterodiff.events import (
    ContinuousField,
    Event,
    EventConfiguration,
    EventTypeSchema,
    FeatureSchema,
    SupportKind,
    TimeMeasureKind,
)


FloatArray = NDArray[np.float64]
Termination = Literal["horizon", "max_events", "max_candidates", "zero_intensity"]


def _readonly_float_array(value: object, shape: tuple[int, ...], name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class MarkFieldSpec:
    """Schema and sampling law for one scalar mark field."""

    name: str
    support: tuple[float, float]
    distribution: Literal["beta", "gamma", "normal", "uniform"]
    parameters: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("mark field names must be non-empty strings")
        allowed = {"beta", "gamma", "normal", "uniform"}
        if self.distribution not in allowed:
            raise ValueError(
                "unknown mark distribution {!r}; expected one of {}".format(
                    self.distribution, sorted(allowed)
                )
            )
        lower, upper = self.support
        if lower >= upper:
            raise ValueError(f"invalid support for {self.name}: {self.support}")
        values = dict(self.parameters)
        if len(values) != len(self.parameters):
            raise ValueError(f"{self.name} has duplicate parameter names")
        required = {
            "beta": {"alpha", "beta"},
            "gamma": {"shape", "scale"},
            "normal": {"loc", "scale"},
            "uniform": {"low", "high"},
        }[self.distribution]
        if set(values) != required:
            raise ValueError(
                f"{self.name} requires parameters {sorted(required)}, got {sorted(values)}"
            )
        if any(not np.isfinite(value) for value in values.values()):
            raise ValueError(f"{self.name} distribution parameters must be finite")
        if self.distribution in {"beta", "gamma"} and any(v <= 0.0 for v in values.values()):
            raise ValueError(f"{self.name} distribution parameters must be positive")
        if self.distribution == "normal" and values["scale"] <= 0.0:
            raise ValueError(f"{self.name} normal scale must be positive")
        if self.distribution == "uniform" and values["low"] >= values["high"]:
            raise ValueError(f"{self.name} uniform bounds must be ordered")

        expected_support = {
            "beta": (0.0, 1.0),
            "gamma": (0.0, inf),
            "normal": (-inf, inf),
            "uniform": (values.get("low", lower), values.get("high", upper)),
        }[self.distribution]
        if self.support != expected_support:
            raise ValueError(
                f"{self.name} support {self.support} disagrees with its "
                f"{self.distribution} sampling law {expected_support}"
            )

    @property
    def parameter_dict(self) -> dict[str, float]:
        return dict(self.parameters)

    def contains(self, value: float) -> bool:
        lower, upper = self.support
        return bool(lower < value < upper)

    def reference_mean_std(self) -> tuple[float, float]:
        """Return analytic moments used to normalize excitation features."""

        p = self.parameter_dict
        if self.distribution == "beta":
            alpha, beta = p["alpha"], p["beta"]
            mean = alpha / (alpha + beta)
            variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0))
            return mean, sqrt(variance)
        if self.distribution == "gamma":
            shape, scale = p["shape"], p["scale"]
            return shape * scale, sqrt(shape) * scale
        if self.distribution == "normal":
            return p["loc"], p["scale"]
        low, high = p["low"], p["high"]
        return 0.5 * (low + high), (high - low) / sqrt(12.0)


@dataclass(frozen=True)
class EventTypeSpec:
    """A discrete event type with its own mark space."""

    type_id: int
    name: str
    fields: tuple[MarkFieldSpec, ...]
    excitation_weights: tuple[float, ...]

    def __post_init__(self) -> None:
        if isinstance(self.type_id, bool) or not isinstance(self.type_id, (int, np.integer)):
            raise TypeError("type_id must be an integer")
        if self.type_id < 0:
            raise ValueError("type_id must be non-negative")
        if not self.name:
            raise ValueError("event type names must be non-empty")
        if len(self.fields) != len(self.excitation_weights):
            raise ValueError(
                f"event type {self.name} has {len(self.fields)} mark fields but "
                f"{len(self.excitation_weights)} excitation weights"
            )
        if not np.all(np.isfinite(np.asarray(self.excitation_weights, dtype=np.float64))):
            raise ValueError(f"event type {self.name} has non-finite excitation weights")

    @property
    def mark_dimension(self) -> int:
        return len(self.fields)

    @property
    def supports(self) -> tuple[tuple[float, float], ...]:
        return tuple(field.support for field in self.fields)


@dataclass(frozen=True)
class HawkesParameters:
    """Ground-truth parameters for the benchmark process."""

    event_types: tuple[EventTypeSpec, ...]
    baseline: FloatArray
    excitation: FloatArray
    decay: FloatArray
    mark_log_strength_clip: float = 0.75

    def __post_init__(self) -> None:
        count = len(self.event_types)
        if count < 3:
            raise ValueError("the typed benchmark requires at least three event types")
        ids = tuple(spec.type_id for spec in self.event_types)
        if ids != tuple(range(count)):
            raise ValueError("event type ids must be contiguous and ordered from zero")
        if len({spec.name for spec in self.event_types}) != count:
            raise ValueError("event type names must be unique")
        baseline = _readonly_float_array(self.baseline, (count,), "baseline")
        excitation = _readonly_float_array(self.excitation, (count, count), "excitation")
        decay = _readonly_float_array(self.decay, (count, count), "decay")
        if np.any(baseline < 0.0):
            raise ValueError("baseline intensities must be non-negative")
        if np.any(excitation < 0.0):
            raise ValueError("excitation jumps must be non-negative")
        if np.any(decay <= 0.0):
            raise ValueError("decay rates must be positive")
        if not np.isfinite(self.mark_log_strength_clip) or self.mark_log_strength_clip <= 0.0:
            raise ValueError("mark_log_strength_clip must be finite and positive")
        object.__setattr__(self, "baseline", baseline)
        object.__setattr__(self, "excitation", excitation)
        object.__setattr__(self, "decay", decay)

    @property
    def num_types(self) -> int:
        return len(self.event_types)

    @property
    def reference_branching_matrix(self) -> FloatArray:
        """Kernel integrals at the reference mark strength ``s=1``."""

        matrix = np.array(self.excitation / self.decay, copy=True)
        matrix.setflags(write=False)
        return matrix

    @property
    def reference_spectral_radius(self) -> float:
        return float(np.max(np.abs(np.linalg.eigvals(self.reference_branching_matrix))))

    @property
    def worst_case_branching_matrix(self) -> FloatArray:
        """Elementwise upper bound using the largest possible mark multiplier."""

        matrix = np.array(
            self.reference_branching_matrix * np.exp(self.mark_log_strength_clip),
            copy=True,
        )
        matrix.setflags(write=False)
        return matrix

    @property
    def worst_case_spectral_radius(self) -> float:
        """Conservative stability certificate for every valid mark realization."""

        return float(
            np.max(np.abs(np.linalg.eigvals(self.worst_case_branching_matrix)))
        )

    def validate_mark(self, event_type: int, mark: object) -> FloatArray:
        if isinstance(event_type, bool) or not isinstance(event_type, (int, np.integer)):
            raise TypeError("event_type must be an integer")
        if not 0 <= int(event_type) < self.num_types:
            raise ValueError(f"unknown event type {event_type}")
        event_type = int(event_type)
        spec = self.event_types[event_type]
        array = np.asarray(mark, dtype=np.float64)
        if array.shape != (spec.mark_dimension,):
            raise ValueError(
                f"mark for {spec.name} must have shape {(spec.mark_dimension,)}, "
                f"got {array.shape}"
            )
        if not np.all(np.isfinite(array)):
            raise ValueError("marks must contain only finite values")
        for value, field in zip(array, spec.fields):
            if not field.contains(float(value)):
                raise ValueError(f"mark field {field.name}={value} is outside {field.support}")
        return array

    def mark_strength(self, event_type: int, mark: object) -> float:
        """Compute the bounded source-strength multiplier for an observed mark."""

        array = self.validate_mark(event_type, mark)
        spec = self.event_types[event_type]
        if spec.mark_dimension == 0:
            return 1.0
        normalized: list[float] = []
        for value, field in zip(array, spec.fields):
            mean, std = field.reference_mean_std()
            normalized.append(float(np.tanh((float(value) - mean) / (2.0 * std))))
        weights = np.asarray(spec.excitation_weights, dtype=np.float64)
        log_strength = float(weights @ np.asarray(normalized) / sqrt(spec.mark_dimension))
        clipped = np.clip(log_strength, -self.mark_log_strength_clip, self.mark_log_strength_clip)
        return float(np.exp(clipped))


@dataclass(frozen=True)
class TypedEvent:
    """One observed event in native continuous time."""

    time: float
    event_type: int
    type_name: str
    mark: FloatArray

    def __post_init__(self) -> None:
        if isinstance(self.time, bool) or not isinstance(
            self.time, (int, float, np.integer, np.floating)
        ):
            raise TypeError("event time must be a real number")
        time = float(self.time)
        if not np.isfinite(time) or time < 0.0:
            raise ValueError("event time must be finite and non-negative")
        object.__setattr__(self, "time", time)
        if isinstance(self.event_type, bool) or not isinstance(
            self.event_type, (int, np.integer)
        ):
            raise TypeError("event_type must be an integer")
        event_type = int(self.event_type)
        if event_type < 0:
            raise ValueError("event_type must be nonnegative")
        object.__setattr__(self, "event_type", event_type)
        if not isinstance(self.type_name, str):
            raise TypeError("type_name must be a string")
        if not self.type_name.strip():
            raise ValueError("type_name must be nonempty")
        mark = np.array(self.mark, dtype=np.float64, copy=True)
        if mark.ndim != 1 or not np.all(np.isfinite(mark)):
            raise ValueError("event marks must be finite one-dimensional arrays")
        mark.setflags(write=False)
        object.__setattr__(self, "mark", mark)

    def as_record(self) -> dict[str, object]:
        """Return a framework-neutral record suitable for adapters or serialization."""

        return {
            "time": self.time,
            "event_type": self.event_type,
            "type_name": self.type_name,
            "mark": self.mark.copy(),
        }


@dataclass(frozen=True)
class SimulationMetadata:
    """Ground truth and provenance accompanying a simulated realization."""

    parameters: HawkesParameters
    seed: int
    horizon: float
    max_events: int
    candidate_count: int
    realized_event_counts: tuple[int, ...]
    terminated_by: Termination
    control_kind: Optional[str] = None
    control_seed: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, HawkesParameters):
            raise TypeError("parameters must be HawkesParameters")
        for name, value, allow_zero in (
            ("seed", self.seed, True),
            ("max_events", self.max_events, False),
            ("candidate_count", self.candidate_count, True),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
                raise TypeError("{} must be an integer".format(name))
            if (allow_zero and value < 0) or (not allow_zero and value <= 0):
                qualifier = "nonnegative" if allow_zero else "positive"
                raise ValueError("{} must be {}".format(name, qualifier))
            object.__setattr__(self, name, int(value))
        if isinstance(self.horizon, bool) or not isinstance(
            self.horizon, (int, float, np.integer, np.floating)
        ):
            raise TypeError("horizon must be a real number")
        horizon = float(self.horizon)
        if not np.isfinite(horizon) or horizon <= 0.0:
            raise ValueError("horizon must be finite and positive")
        object.__setattr__(self, "horizon", horizon)

        counts = tuple(self.realized_event_counts)
        if len(counts) != self.parameters.num_types:
            raise ValueError("realized_event_counts must cover every event type")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, np.integer))
            or value < 0
            for value in counts
        ):
            raise ValueError("realized event counts must be nonnegative integers")
        counts = tuple(int(value) for value in counts)
        if sum(counts) > self.candidate_count:
            raise ValueError("accepted event count cannot exceed candidate count")
        if sum(counts) > self.max_events:
            raise ValueError("realized event count cannot exceed max_events")
        object.__setattr__(self, "realized_event_counts", counts)

        allowed_terminations = {
            "horizon",
            "max_events",
            "max_candidates",
            "zero_intensity",
        }
        if self.terminated_by not in allowed_terminations:
            raise ValueError("terminated_by is not a declared termination reason")
        if self.terminated_by == "max_events" and sum(counts) != self.max_events:
            raise ValueError("max_events termination requires exactly max_events events")

        if (self.control_kind is None) != (self.control_seed is None):
            raise ValueError("control_kind and control_seed must be declared together")
        if self.control_kind is not None:
            if not isinstance(self.control_kind, str) or not self.control_kind.strip():
                raise ValueError("control_kind must be a nonempty string")
            if isinstance(self.control_seed, bool) or not isinstance(
                self.control_seed, (int, np.integer)
            ):
                raise TypeError("control_seed must be an integer")
            object.__setattr__(self, "control_seed", int(self.control_seed))

    @property
    def truncated(self) -> bool:
        return self.terminated_by in {"max_events", "max_candidates"}

    @property
    def acceptance_rate(self) -> float:
        accepted = sum(self.realized_event_counts)
        return accepted / self.candidate_count if self.candidate_count else 0.0


@dataclass(frozen=True)
class SimulationResult:
    """A realization with source-process and optional derived-control provenance."""

    events: tuple[TypedEvent, ...]
    metadata: SimulationMetadata

    def __post_init__(self) -> None:
        events = tuple(self.events)
        if any(not isinstance(event, TypedEvent) for event in events):
            raise TypeError("events must contain only TypedEvent instances")
        if not isinstance(self.metadata, SimulationMetadata):
            raise TypeError("metadata must be SimulationMetadata")
        parameters = self.metadata.parameters
        counts = np.zeros(parameters.num_types, dtype=np.int64)
        previous_time = -np.inf
        for event in events:
            if event.event_type >= parameters.num_types:
                raise ValueError("event uses an unknown type")
            spec = parameters.event_types[event.event_type]
            if event.type_name != spec.name:
                raise ValueError("event type_name disagrees with event_type")
            parameters.validate_mark(event.event_type, event.mark)
            if event.time > self.metadata.horizon:
                raise ValueError("event occurs after the simulation horizon")
            if event.time <= previous_time:
                raise ValueError("synthetic event times must be strictly increasing")
            previous_time = event.time
            counts[event.event_type] += 1
        if tuple(int(value) for value in counts) != self.metadata.realized_event_counts:
            raise ValueError("metadata event counts disagree with the realization")
        object.__setattr__(self, "events", events)

    @property
    def records(self) -> tuple[dict[str, object], ...]:
        return tuple(event.as_record() for event in self.events)

    @property
    def times(self) -> FloatArray:
        return np.asarray([event.time for event in self.events], dtype=np.float64)

    @property
    def event_types(self) -> NDArray[np.int64]:
        return np.asarray([event.event_type for event in self.events], dtype=np.int64)

    def marks_for_type(self, event_type: int) -> FloatArray:
        if isinstance(event_type, bool) or not isinstance(
            event_type, (int, np.integer)
        ):
            raise TypeError("event_type must be an integer")
        event_type = int(event_type)
        if not 0 <= event_type < self.metadata.parameters.num_types:
            raise ValueError("unknown event_type")
        dimension = self.metadata.parameters.event_types[event_type].mark_dimension
        marks = [event.mark for event in self.events if event.event_type == event_type]
        if not marks:
            return np.empty((0, dimension), dtype=np.float64)
        return np.stack(marks).astype(np.float64, copy=False)

    def to_configuration(
        self, *, sample_id: str = "", group_id: str = ""
    ) -> EventConfiguration:
        """Convert this realization to the shared native event representation."""

        schema = feature_schema_from_hawkes(
            self.metadata.parameters, horizon=self.metadata.horizon
        )
        events = []
        for index, event in enumerate(self.events):
            type_spec = self.metadata.parameters.event_types[event.event_type]
            marks = {
                field.name: float(value)
                for field, value in zip(type_spec.fields, event.mark)
            }
            events.append(
                Event(
                    event_time=event.time,
                    event_type=event.event_type,
                    marks=marks,
                    event_id="synthetic-{}".format(index),
                )
            )
        return EventConfiguration(
            schema=schema,
            events=tuple(events),
            sample_id=sample_id,
            group_id=group_id,
        )


def feature_schema_from_hawkes(
    parameters: HawkesParameters, *, horizon: float
) -> FeatureSchema:
    """Translate the benchmark's native fibers into the shared schema API."""

    event_types = []
    for event_type in parameters.event_types:
        fields = []
        for field in event_type.fields:
            lower, upper = field.support
            if np.isneginf(lower) and np.isposinf(upper):
                fields.append(ContinuousField(field.name, support=SupportKind.REAL))
            elif lower == 0.0 and np.isposinf(upper):
                fields.append(ContinuousField(field.name, support=SupportKind.POSITIVE))
            elif np.isfinite(lower) and np.isfinite(upper):
                fields.append(
                    ContinuousField(
                        field.name,
                        support=SupportKind.BOUNDED,
                        lower=lower,
                        upper=upper,
                    )
                )
            else:  # guarded by MarkFieldSpec, retained as a fail-closed check
                raise ValueError(
                    "unsupported synthetic field support {}".format(field.support)
                )
        event_types.append(
            EventTypeSchema(event_type.type_id, event_type.name, tuple(fields))
        )
    return FeatureSchema(
        event_types=tuple(event_types),
        horizon=horizon,
        time_measure=TimeMeasureKind.CONTINUOUS,
        allow_simultaneous=False,
        version="typed-hawkes-v1",
    )


def default_hawkes_parameters() -> HawkesParameters:
    """Return a stable four-type process with heterogeneous mark spaces."""

    event_types = (
        EventTypeSpec(
            type_id=0,
            name="impulse",
            fields=(
                MarkFieldSpec("amplitude", (0.0, inf), "gamma", (("shape", 2.0), ("scale", 0.75))),
            ),
            excitation_weights=(0.55,),
        ),
        EventTypeSpec(
            type_id=1,
            name="context",
            fields=(
                MarkFieldSpec("confidence", (0.0, 1.0), "beta", (("alpha", 2.0), ("beta", 3.0))),
                MarkFieldSpec("offset", (-inf, inf), "normal", (("loc", 0.0), ("scale", 0.7))),
            ),
            excitation_weights=(-0.35, 0.30),
        ),
        EventTypeSpec(
            type_id=2,
            name="alarm",
            fields=(
                MarkFieldSpec("severity", (0.0, 1.0), "beta", (("alpha", 3.0), ("beta", 1.8))),
                MarkFieldSpec("duration", (0.0, inf), "gamma", (("shape", 2.5), ("scale", 0.5))),
                MarkFieldSpec("polarity", (-1.0, 1.0), "uniform", (("low", -1.0), ("high", 1.0))),
            ),
            excitation_weights=(0.40, 0.25, -0.30),
        ),
        EventTypeSpec(
            type_id=3,
            name="recovery",
            fields=(),
            excitation_weights=(),
        ),
    )
    return HawkesParameters(
        event_types=event_types,
        baseline=np.asarray([0.18, 0.15, 0.12, 0.10]),
        excitation=np.asarray(
            [
                [0.16, 0.05, 0.04, 0.06],
                [0.08, 0.14, 0.05, 0.04],
                [0.05, 0.08, 0.13, 0.06],
                [0.04, 0.05, 0.09, 0.12],
            ]
        ),
        decay=np.asarray(
            [
                [1.40, 1.50, 1.60, 1.45],
                [1.35, 1.30, 1.55, 1.50],
                [1.50, 1.40, 1.25, 1.45],
                [1.55, 1.50, 1.35, 1.30],
            ]
        ),
    )


def _sample_field(field: MarkFieldSpec, rng: np.random.Generator) -> float:
    p = field.parameter_dict
    if field.distribution == "beta":
        value = float(rng.beta(p["alpha"], p["beta"]))
    elif field.distribution == "gamma":
        value = float(rng.gamma(p["shape"], p["scale"]))
    elif field.distribution == "normal":
        value = float(rng.normal(p["loc"], p["scale"]))
    else:
        value = float(rng.uniform(p["low"], p["high"]))

    lower, upper = field.support
    if value <= lower:
        value = float(np.nextafter(lower, upper))
    if value >= upper:
        value = float(np.nextafter(upper, lower))
    if not field.contains(value):
        raise FloatingPointError(
            f"sampled {field.name}={value} outside open support {field.support}"
        )
    return value


def _sample_mark(spec: EventTypeSpec, rng: np.random.Generator) -> FloatArray:
    return np.asarray([_sample_field(field, rng) for field in spec.fields], dtype=np.float64)


def simulate_typed_hawkes(
    *,
    seed: int,
    horizon: float = 100.0,
    max_events: int = 10_000,
    parameters: Optional[HawkesParameters] = None,
    max_candidates: Optional[int] = None,
) -> SimulationResult:
    """Simulate a marked multivariate Hawkes process using Ogata thinning.

    Positive exponential kernels make the current total intensity a valid upper
    bound until the next event.  ``max_events`` and ``max_candidates`` provide
    hard safety limits even for deliberately supercritical custom parameters.
    """

    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    if isinstance(horizon, bool) or not np.isfinite(horizon) or horizon <= 0.0:
        raise ValueError("horizon must be finite and positive")
    if isinstance(max_events, bool) or not isinstance(max_events, (int, np.integer)):
        raise TypeError("max_events must be an integer")
    if max_events <= 0:
        raise ValueError("max_events must be positive")
    if max_candidates is None:
        max_candidates = max(10_000, 100 * max_events)
    if isinstance(max_candidates, bool) or not isinstance(
        max_candidates, (int, np.integer)
    ):
        raise TypeError("max_candidates must be an integer")
    if max_candidates <= 0:
        raise ValueError("max_candidates must be positive")

    params = parameters or default_hawkes_parameters()
    if not isinstance(params, HawkesParameters):
        raise TypeError("parameters must be HawkesParameters or None")
    rng = np.random.default_rng(int(seed))
    events: list[TypedEvent] = []
    # State[target, source] is the decayed excitation currently contributed by
    # all historical events of the given source type.
    state = np.zeros((params.num_types, params.num_types), dtype=np.float64)
    time = 0.0
    candidate_count = 0
    terminated_by: Termination = "horizon"

    while time < horizon and len(events) < max_events:
        if candidate_count >= max_candidates:
            terminated_by = "max_candidates"
            break
        current_intensity = params.baseline + state.sum(axis=1)
        upper_total = float(current_intensity.sum())
        if upper_total <= 0.0:
            terminated_by = "zero_intensity"
            break
        wait = float(rng.exponential(1.0 / upper_total))
        candidate_time = time + wait
        if candidate_time > horizon:
            terminated_by = "horizon"
            break

        candidate_count += 1
        candidate_state = state * np.exp(-params.decay * wait)
        candidate_intensity = params.baseline + candidate_state.sum(axis=1)
        candidate_total = float(candidate_intensity.sum())
        time = candidate_time
        state = candidate_state
        if rng.random() * upper_total > candidate_total:
            continue

        probabilities = candidate_intensity / candidate_total
        event_type = int(rng.choice(params.num_types, p=probabilities))
        spec = params.event_types[event_type]
        mark = _sample_mark(spec, rng)
        strength = params.mark_strength(event_type, mark)
        state[:, event_type] += params.excitation[:, event_type] * strength
        events.append(TypedEvent(time, event_type, spec.name, mark))

    if len(events) >= max_events:
        terminated_by = "max_events"
    counts = np.bincount(
        np.asarray([event.event_type for event in events], dtype=np.int64),
        minlength=params.num_types,
    )
    metadata = SimulationMetadata(
        parameters=params,
        seed=int(seed),
        horizon=float(horizon),
        max_events=int(max_events),
        candidate_count=candidate_count,
        realized_event_counts=tuple(int(value) for value in counts),
        terminated_by=terminated_by,
    )
    return SimulationResult(tuple(events), metadata)


def conditional_intensity(
    events: Iterable[TypedEvent],
    query_time: float,
    parameters: Optional[HawkesParameters] = None,
) -> FloatArray:
    """Evaluate the exact ground-truth intensity immediately before ``query_time``."""

    if not np.isfinite(query_time) or query_time < 0.0:
        raise ValueError("query_time must be finite and non-negative")
    params = parameters or default_hawkes_parameters()
    intensity = np.array(params.baseline, copy=True)
    for event in events:
        if event.time >= query_time:
            continue
        if not 0 <= event.event_type < params.num_types:
            raise ValueError(f"unknown event type {event.event_type}")
        params.validate_mark(event.event_type, event.mark)
        elapsed = query_time - event.time
        strength = params.mark_strength(event.event_type, event.mark)
        intensity += (
            params.excitation[:, event.event_type]
            * strength
            * np.exp(-params.decay[:, event.event_type] * elapsed)
        )
    return intensity


def _nonidentity_permutation(rng: np.random.Generator, size: int) -> NDArray[np.int64]:
    permutation = rng.permutation(size)
    if size > 1 and np.array_equal(permutation, np.arange(size)):
        permutation = np.roll(permutation, 1)
    return permutation.astype(np.int64, copy=False)


def temporal_permutation_control(result: SimulationResult, *, seed: int) -> SimulationResult:
    """Randomize temporal alignment while preserving empirical marginals exactly.

    The transformation independently permutes (1) the observed pre-event gaps
    and (2) complete ``(type, mark)`` payloads.  It therefore preserves the exact
    multiset of gaps, type counts, and every per-type mark vector, while
    randomizing their finite-sample order and alignment. It is not claimed to
    eliminate every dependence statistic: permutation without replacement has
    global constraints and may retain accidental lag structure. The final event
    time is unchanged.
    """

    count = len(result.events)
    if count == 0:
        metadata = replace(
            result.metadata,
            control_kind="gap_payload_alignment_permutation",
            control_seed=int(seed),
        )
        return SimulationResult((), metadata)

    rng = np.random.default_rng(seed)
    times = result.times
    gaps = np.diff(np.concatenate((np.asarray([0.0]), times)))
    gap_order = _nonidentity_permutation(rng, count)
    payload_order = _nonidentity_permutation(rng, count)
    controlled_times = np.cumsum(gaps[gap_order])

    controlled: list[TypedEvent] = []
    for time, payload_index in zip(controlled_times, payload_order):
        original = result.events[int(payload_index)]
        controlled.append(
            TypedEvent(float(time), original.event_type, original.type_name, original.mark)
        )
    metadata = replace(
        result.metadata,
        control_kind="gap_payload_alignment_permutation",
        control_seed=int(seed),
    )
    return SimulationResult(tuple(controlled), metadata)
