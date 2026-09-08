"""Executable local numerical successor for learned hybrid trajectories.

The physical scalar is supplied explicitly: V for candidate-base training,
or V + log(h_hat) for a conditional path. A classifier nuisance is NEVER a
sampler argument. The caller must not hide it inside the supplied potential.
Candidate-base pairs always start two independent reference Pi_N draws.
Conditional initializers must separately target Pi_N*h_hat(0), not exp(V)
times that law; this module does not invent such an initializer.

Numerical family: Strang stochastic-Heun / midpoint-frozen reference thinning.
Each active grid interval owns its schedule coefficient, taken in its open
interior. Both Heun endpoint drifts use that coefficient, with potential
gradients at the actual endpoints. This one-sided boundary convention is a
DECLARED NUMERICAL SUCCESSOR, not a change to the reference schedule's public
left-continuous pointwise API. Fully held intervals make no model/RNG calls.

Thinning uses a caller-declared global upper potential bound U. At state y its
envelope is Lambda0(y)*exp(U-Psi(y)). Binary64 nextafter padding is a numerical
guard, NOT an interval proof of exp or certification of the global bound.
Unrepresentable rates/probabilities or exhausted limits stop the path. No
clipping, tau-leap, single-jump substitute, retry, or partial-success return.

PCG64 purpose-keyed replay is not proof of IID streams or exact real-valued
Gaussian/exponential sampling. No coupled-halving qualification, production
admission, real-domain chart, Gaussian K_m adoption, or full F105 qualification
is implied. Outputs live in the transformed Gaussian configuration space.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
from typing import Any, Callable, Protocol

import numpy as np

from heterodiff.processes.plugin_bridge_sampler import ProcessValidReferenceJumpComposer
from heterodiff.processes.reversible_hybrid_reference import ReversibleHybridReference
from heterodiff.theory.configuration_reference import (
    MIN_REFERENCE_CATEGORICAL_PROBABILITY,
    TransformedConfiguration,
    TransformedEvent,
)


class HybridTrainingSamplingError(RuntimeError):
    """A complete trajectory could not be produced under its declared rules."""


class PhysicalPotential(Protocol):
    """Pure deterministic callback; value_grad rows follow canonical events.

    Coordinates and returned gradients are physical transformed coordinates,
    not the network's atan feature coordinates. value and value_grad must
    describe the SAME scalar, with all current weights held fixed during a
    trajectory. Global consistency and the upper bound are caller premises;
    sampled calls are checked but do not prove either premise.
    """

    upper_value_bound: float

    def value(self, reverse_time: float, state: TransformedConfiguration) -> float: ...

    def value_grad(
        self, reverse_time: float, state: TransformedConfiguration
    ) -> tuple[float, tuple[tuple[float, ...], ...]]: ...


def _finite(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.floating)):
        raise HybridTrainingSamplingError(f"{name}: finite real required")
    result = float(value)
    if not math.isfinite(result):
        raise HybridTrainingSamplingError(f"{name}: nonfinite")
    return result


def _key(value: bytes, name: str) -> bytes:
    if type(value) is not bytes or not value or len(value) > 4096:
        raise HybridTrainingSamplingError(f"{name}: nonempty bounded bytes required")
    return value


@dataclass(frozen=True)
class HybridTrajectoryPlan:
    reverse_grid: tuple[float, ...]
    max_jump_candidates: int = 100_000
    max_state_coordinates: int = 4_000_000
    max_recorded_coordinates: int = 4_000_000
    query_refined_from: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if type(self.reverse_grid) is not tuple or not 2 <= len(self.reverse_grid) <= 10_001:
            raise HybridTrainingSamplingError("reverse_grid must contain 2..10001 explicit points")
        grid = tuple(_finite(t, "reverse time") for t in self.reverse_grid)
        if grid[0] != 0.0 or any(b <= a for a, b in zip(grid, grid[1:])):
            raise HybridTrainingSamplingError("reverse_grid must start at zero and increase")
        for field in ("max_jump_candidates", "max_state_coordinates", "max_recorded_coordinates"):
            value = getattr(self, field)
            upper = 100_000 if field == "max_jump_candidates" else 4_000_000
            if type(value) is not int or not 1 <= value <= upper:
                raise HybridTrainingSamplingError(f"{field}: outside implementation bounds")
        object.__setattr__(self, "reverse_grid", grid)
        if self.query_refined_from is not None:
            if type(self.query_refined_from) is not tuple:
                raise HybridTrainingSamplingError("query refinement base must be an explicit tuple")
            base = tuple(_finite(t, "query refinement base time") for t in self.query_refined_from)
            if (len(base) != len(grid) - 1
                    or base[0] != grid[0] or base[-1] != grid[-1]
                    or any(b <= a for a, b in zip(base, base[1:]))
                    or any(t not in grid for t in base)):
                raise HybridTrainingSamplingError("query refinement must add exactly one interior grid point")
            object.__setattr__(self, "query_refined_from", base)

    def refined_for_query(self, reverse_time: float) -> HybridTrajectoryPlan:
        """Explicitly insert u; this CHANGES the numerical path law/work count.

        This is not dense output or preservation of a frozen 256-step method.
        The caller must retain the returned actual grid in its trial record.
        No endpoint snapping or repeated implicit refinement is performed.
        """
        point = _finite(reverse_time, "query refinement time")
        if not self.reverse_grid[0] < point < self.reverse_grid[-1]:
            raise HybridTrainingSamplingError("query refinement requires an interior time")
        if point in self.reverse_grid:
            return self
        if self.query_refined_from is not None:
            raise HybridTrainingSamplingError("a plan can explicitly refine only one query time")
        return replace(self, reverse_grid=tuple(sorted((*self.reverse_grid, point))),
                       query_refined_from=self.reverse_grid)


@dataclass(frozen=True)
class HybridSamplingContext:
    domain_id: str
    task_id: bytes
    context_id: bytes

    def __post_init__(self) -> None:
        if type(self.domain_id) is not str or not self.domain_id or len(self.domain_id.encode()) > 512:
            raise HybridTrainingSamplingError("domain_id must be a nonempty bounded string")
        _key(self.task_id, "task_id")
        _key(self.context_id, "context_id")

    def key(self) -> bytes:
        return _framed((self.domain_id.encode(), self.task_id, self.context_id))


def _framed(parts: tuple[bytes, ...]) -> bytes:
    return b"".join(len(part).to_bytes(8, "big") + part for part in parts)


class _Streams:
    def __init__(self, seed: int, record_id: bytes, branch_id: bytes):
        if type(seed) is not int or not 0 <= seed < 2**64:
            raise HybridTrainingSamplingError("run_seed must be an explicitly supplied uint64")
        self.root = _framed((seed.to_bytes(8, "big"), _key(record_id, "record_id"), _key(branch_id, "branch_id")))
        self.requests = 0

    def rng(self, purpose: str, step: int, ordinal: int = 0) -> np.random.Generator:
        payload = _framed((b"learned-hybrid-numerical-stream-v1", self.root,
                           purpose.encode("ascii"), str(step).encode(), str(ordinal).encode()))
        self.requests += 1
        return np.random.Generator(np.random.PCG64(int.from_bytes(hashlib.sha256(payload).digest(), "big")))


class ReferenceConfigurationInitializer:
    """The candidate-base initial law Pi_N; no energy or observations used."""

    def __call__(self, process: ReversibleHybridReference, rng: np.random.Generator) -> TransformedConfiguration:
        return process.reference.sample_configuration(rng)


@dataclass(frozen=True)
class GaussianFiniteEventObservation:
    """Synthetic full-event Gaussian law, not a real-domain K_m declaration.

    Event count/type are observed exactly. Each transformed coordinate is
    independently perturbed by N(0,sigma^2), then made unlabelled/canonical.
    In labelled coordinates this is a genuine continuous Gaussian kernel;
    its unlabelled pushforward includes permutation multiplicities. No raw
    domain decoding, rounding, clipping or F105 embedding inversion occurs.
    Because count/types are revealed exactly, supports differ across those
    latent configurations. This fixture does NOT satisfy the manuscript's
    positive common-support observation-law premise for a full classifier.
    Supply a separately declared common-support law for that linked task.
    """

    sigma: float
    declaration_id: str = "SYNTHETIC_FULL_EVENT_GAUSSIAN_NOT_REAL_DOMAIN_K_M"

    def __post_init__(self) -> None:
        sigma = _finite(self.sigma, "observation sigma")
        if sigma <= 0 or type(self.declaration_id) is not str or not self.declaration_id:
            raise HybridTrainingSamplingError("positive sigma and explicit observation declaration required")
        object.__setattr__(self, "sigma", sigma)

    def __call__(self, state: TransformedConfiguration, context: HybridSamplingContext,
                 rng: np.random.Generator) -> TransformedConfiguration:
        del context  # This synthetic law is explicitly context-independent.
        observed = []
        for event in state:
            noise = rng.standard_normal(len(event.coordinates))
            values = tuple(_finite(x + self.sigma * float(z), "Gaussian observation")
                           for x, z in zip(event.coordinates, noise))
            observed.append(TransformedEvent(event.event_type, values))
        return tuple(sorted(observed, key=TransformedEvent.model_key))


@dataclass(frozen=True)
class HybridJumpDiagnostic:
    grid_step: int
    candidate_ordinal: int
    frozen_reverse_time: float
    operational_time: float
    kind: str
    accepted: bool
    cardinality_before: int
    cardinality_after: int
    acceptance_probability: float


@dataclass(frozen=True)
class LearnedHybridTrajectory:
    reverse_times: tuple[float, ...]
    states: tuple[TransformedConfiguration, ...]
    jumps: tuple[HybridJumpDiagnostic, ...]
    diagnostics: dict[str, Any]

    @property
    def terminal_state(self) -> TransformedConfiguration:
        return self.states[-1]

    def at_time(self, reverse_time: float) -> TransformedConfiguration:
        point = _finite(reverse_time, "requested reverse time")
        try:
            return self.states[self.reverse_times.index(point)]
        except ValueError as error:
            raise HybridTrainingSamplingError("requested time must be an exact declared grid point") from error


@dataclass(frozen=True)
class ObservedHybridTrajectory:
    trajectory: LearnedHybridTrajectory
    latent_at_u: TransformedConfiguration
    terminal_state: TransformedConfiguration
    observation: Any


@dataclass(frozen=True)
class HybridJointProductSample:
    context: HybridSamplingContext
    reverse_time: float
    branch_one: ObservedHybridTrajectory
    branch_two: ObservedHybridTrajectory

    @property
    def joint_pair(self) -> tuple[TransformedConfiguration, Any]:
        return self.branch_one.latent_at_u, self.branch_one.observation

    @property
    def product_pair(self) -> tuple[TransformedConfiguration, Any]:
        return self.branch_one.latent_at_u, self.branch_two.observation


class LearnedHybridTrainingSampler:
    """A supplied physical potential drives both coordinates and all jump edits.

    The initializer is explicit. Use ReferenceConfigurationInitializer for
    candidate training. A supplied custom initializer is allowed for local
    numerical experiments but is not automatically a valid conditional law.
    Models/callbacks must remain pure/fixed during each call; no graph/weight
    identity or global-bound proof is inferred from this runtime interface.
    """

    def __init__(self, process: ReversibleHybridReference, potential: PhysicalPotential,
                 plan: HybridTrajectoryPlan,
                 initializer: Callable[[ReversibleHybridReference, np.random.Generator], TransformedConfiguration]):
        if type(process) is not ReversibleHybridReference or type(plan) is not HybridTrajectoryPlan:
            raise HybridTrainingSamplingError("exact reference process and trajectory plan required")
        if not callable(initializer) or not callable(getattr(potential, "value", None)) or not callable(getattr(potential, "value_grad", None)):
            raise HybridTrainingSamplingError("explicit initializer and physical value/value_grad callbacks required")
        bound = _finite(potential.upper_value_bound, "global upper potential bound")
        horizon = process.schedule.horizon
        if plan.reverse_grid[-1] != horizon:
            raise HybridTrainingSamplingError("reverse_grid endpoint must equal the process horizon")
        if any(horizon - float(s) not in plan.reverse_grid for s in process.schedule.time_grid):
            raise HybridTrainingSamplingError("reverse_grid must include every reflected schedule breakpoint")
        if process.reference.total_cap * max(process.reference.type_dimensions.values()) > plan.max_state_coordinates:
            raise HybridTrainingSamplingError("worst-case state exceeds the declared coordinate budget")
        self.process, self.potential, self.plan, self.initializer = process, potential, plan, initializer
        self.upper_value_bound = bound
        self._composer = ProcessValidReferenceJumpComposer(process)

    def _state(self, events: TransformedConfiguration) -> TransformedConfiguration:
        try:
            state = self.process.reference.canonicalize(events)
        except (TypeError, ValueError, ArithmeticError) as error:
            raise HybridTrainingSamplingError("invalid transformed configuration; no clipping or repair") from error
        if sum(len(e.coordinates) for e in state) > self.plan.max_state_coordinates:
            raise HybridTrainingSamplingError("state coordinate limit exceeded")
        return state

    def _value(self, reverse_time: float, state: TransformedConfiguration) -> float:
        if _finite(self.potential.upper_value_bound, "live upper bound") != self.upper_value_bound:
            raise HybridTrainingSamplingError("potential upper bound changed during sampling")
        value = _finite(self.potential.value(reverse_time, state), "physical potential")
        if value > self.upper_value_bound:
            raise HybridTrainingSamplingError("physical potential violates declared global upper bound")
        return value

    def _gradient(self, reverse_time: float, state: TransformedConfiguration) -> tuple[np.ndarray, ...]:
        if _finite(self.potential.upper_value_bound, "live upper bound") != self.upper_value_bound:
            raise HybridTrainingSamplingError("potential upper bound changed during sampling")
        value, raw_gradient = self.potential.value_grad(reverse_time, state)
        value = _finite(value, "physical potential with gradient")
        if value > self.upper_value_bound:
            raise HybridTrainingSamplingError("physical potential violates declared global upper bound")
        if type(raw_gradient) is not tuple or len(raw_gradient) != len(state):
            raise HybridTrainingSamplingError("coordinate gradient must follow every canonical occurrence")
        rows = []
        for event, row in zip(state, raw_gradient):
            if type(row) is not tuple or len(row) != len(event.coordinates):
                raise HybridTrainingSamplingError("coordinate gradient dimension mismatch")
            rows.append(np.asarray(tuple(_finite(x, "coordinate gradient") for x in row), dtype=np.float64))
        return tuple(rows)

    def _heun(self, state: TransformedConfiguration, start: float, end: float,
              gamma: float, rng: np.random.Generator) -> TransformedConfiguration:
        if not state:
            return state
        dt = end - start
        if dt <= 0 or gamma <= 0:
            raise HybridTrainingSamplingError("active Heun interval/coefficient must be positive")
        scale = _finite(math.sqrt(gamma * dt), "Brownian scale")
        start_grad = self._gradient(start, state)
        noises, start_drifts, predictors = [], [], []
        with np.errstate(over="ignore", invalid="ignore"):
            for event, grad in zip(state, start_grad):
                x = np.asarray(event.coordinates, dtype=np.float64)
                increment = scale * rng.standard_normal(x.size)
                drift = gamma * (-0.5 * x + grad)
                predicted = x + dt * drift + increment
                if np.any(~np.isfinite(predicted)) or np.any(~np.isfinite(increment)):
                    raise HybridTrainingSamplingError("nonfinite Heun predictor/noise")
                noises.append(increment)
                start_drifts.append(drift)
                predictors.append(TransformedEvent(event.event_type, tuple(float(v) for v in predicted)))
            # Carry occurrence indices through the predictor's canonical sort.
            # Duplicate atoms and crossing coordinates never use value matching.
            permutation = tuple(sorted(range(len(state)), key=lambda i: predictors[i].model_key()))
            canonical_predictor = self._state(tuple(predictors[i] for i in permutation))
            canonical_grad = self._gradient(end, canonical_predictor)
            end_grad = [None] * len(state)
            for position, occurrence in enumerate(permutation):
                end_grad[occurrence] = canonical_grad[position]
            corrected = []
            for i, event in enumerate(state):
                predicted = np.asarray(predictors[i].coordinates, dtype=np.float64)
                end_drift = gamma * (-0.5 * predicted + end_grad[i])
                value = np.asarray(event.coordinates) + 0.5 * dt * (start_drifts[i] + end_drift) + noises[i]
                if np.any(~np.isfinite(value)):
                    raise HybridTrainingSamplingError("nonfinite Heun corrector")
                corrected.append(TransformedEvent(event.event_type, tuple(float(v) for v in value)))
        return self._state(tuple(corrected))

    def _jump_substep(self, state: TransformedConfiguration, reverse_time: float,
                      duration: float, step: int, streams: _Streams,
                      journal: list[HybridJumpDiagnostic], counts: dict[str, int]) -> TransformedConfiguration:
        elapsed = 0.0
        local_ordinal = 0
        while elapsed < duration:
            # The process-owned no-RNG categorical/intensity preflight occurs
            # before ANY clock or normalized candidate draw.
            intensity = self._composer.preflight_candidate_intensity(state, reverse_time=reverse_time)
            if intensity.is_zero:
                return state
            source_value = self._value(reverse_time, state)
            gap = _finite(self.upper_value_bound - source_value, "envelope log multiplier")
            try:
                exact_float_multiplier = math.exp(gap)
            except OverflowError as error:
                raise HybridTrainingSamplingError("tilted envelope overflow; no rescaling fallback") from error
            multiplier = math.nextafter(exact_float_multiplier, math.inf) if gap else 1.0
            rate = intensity.scheduled_reference_exit_rate
            raw_envelope = _finite(rate * multiplier, "tilted envelope")
            envelope = math.nextafter(raw_envelope, math.inf) if gap else raw_envelope
            if not math.isfinite(envelope) or envelope < np.finfo(np.float64).tiny:
                raise HybridTrainingSamplingError("tilted envelope is not finite positive normal")
            counts["waiting_time_draws"] += 1
            wait = float(streams.rng("jump-wait", step, local_ordinal).exponential(1.0 / envelope))
            if not math.isfinite(wait) or wait <= 0.0:
                raise HybridTrainingSamplingError("unrepresentable exponential wait; no redraw")
            remaining = duration - elapsed
            if wait >= remaining:
                return state
            next_elapsed = elapsed + wait
            if next_elapsed <= elapsed:
                raise HybridTrainingSamplingError("waiting time does not advance operational clock")
            if counts["jump_candidates"] >= self.plan.max_jump_candidates:
                raise HybridTrainingSamplingError("jump candidate limit exhausted; no truncated trajectory")
            candidate = self._composer.sample_candidate_from_intensity(
                intensity, rng=streams.rng("jump-route", step, local_ordinal))
            if candidate is None:
                raise HybridTrainingSamplingError("positive reference intensity returned no candidate")
            destination = self._state(candidate.proposal.destination_configuration)
            destination_value = self._value(reverse_time, destination)
            # Algebraically exp(Psi'-Psi)*Lambda/E, arranged without subtracting
            # large logarithms or overflowing an intermediate exp(delta).
            probability = (math.exp(destination_value - self.upper_value_bound)
                           * (exact_float_multiplier / multiplier)
                           * (raw_envelope / envelope))
            if (not math.isfinite(probability) or probability > 1.0
                    or probability < MIN_REFERENCE_CATEGORICAL_PROBABILITY):
                raise HybridTrainingSamplingError("acceptance probability outside supported finite-RNG range")
            accepted = bool(streams.rng("jump-accept", step, local_ordinal).random() < probability)
            counts["jump_candidates"] += 1
            counts["accepted_jumps"] += int(accepted)
            journal.append(HybridJumpDiagnostic(step, local_ordinal, reverse_time, next_elapsed,
                           candidate.proposal.kind.value, accepted, len(state),
                           len(destination) if accepted else len(state), probability))
            if accepted:
                state = destination
            elapsed = next_elapsed
            local_ordinal += 1
        return state

    def sample_path(self, *, run_seed: int, record_id: bytes,
                    branch_id: bytes = b"path") -> LearnedHybridTrajectory:
        streams = _Streams(run_seed, record_id, branch_id)
        state = self._state(self.initializer(self.process, streams.rng("initial", 0)))
        states, journal = [state], []
        recorded = sum(len(e.coordinates) for e in state)
        counts = {"jump_candidates": 0, "accepted_jumps": 0, "waiting_time_draws": 0,
                  "active_grid_intervals": 0, "held_grid_intervals": 0}
        horizon = self.process.schedule.horizon
        hold_start = horizon - self.process.schedule.clean_hold
        for step, (start, end) in enumerate(zip(self.plan.reverse_grid, self.plan.reverse_grid[1:])):
            if start >= hold_start:
                counts["held_grid_intervals"] += 1
                states.append(state)  # Exact copy, no potential/stream request.
            else:
                counts["active_grid_intervals"] += 1
                midpoint = start + 0.5 * (end - start)
                if not start < midpoint < end:
                    raise HybridTrainingSamplingError("unrepresentable grid midpoint")
                gamma = self.process.schedule.continuous_rate(horizon - midpoint)
                state = self._heun(state, start, midpoint, gamma, streams.rng("heun-first", step))
                state = self._jump_substep(state, midpoint, end - start, step, streams, journal, counts)
                state = self._heun(state, midpoint, end, gamma, streams.rng("heun-second", step))
                states.append(state)
            recorded += sum(len(e.coordinates) for e in state)
            if recorded > self.plan.max_recorded_coordinates:
                raise HybridTrainingSamplingError("recorded coordinate limit exhausted; no partial success")
        diagnostics = {**counts, "stream_request_count": streams.requests,
                       "stream_binding_sha256": hashlib.sha256(streams.root).hexdigest(),
                       "reverse_grid_hex": tuple(t.hex() for t in self.plan.reverse_grid),
                       "actual_macrostep_count": len(self.plan.reverse_grid) - 1,
                       "query_refined_numerical_path_law": self.plan.query_refined_from is not None,
                       "base_grid_before_query_refinement_hex": (
                           None if self.plan.query_refined_from is None else
                           tuple(t.hex() for t in self.plan.query_refined_from)),
                       "recorded_coordinate_count": recorded,
                       "scope": "LOCAL_NUMERICAL_HYBRID_SUCCESSOR_NOT_PRODUCTION_QUALIFIED",
                       "initializer_is_reference_pi_n": type(self.initializer) is ReferenceConfigurationInitializer,
                       "one_sided_segment_owned_heun_coefficients": True,
                       "global_potential_bound_certified": False,
                       "frozen_sampler_equivalence_claimed": False,
                       "exact_continuous_or_rng_law_claimed": False,
                       "real_domain_chart_or_observation_law_adopted": False,
                       "partial_trajectory_returned": False}
        return LearnedHybridTrajectory(self.plan.reverse_grid, tuple(states), tuple(journal), diagnostics)

    def sample_pair(self, *, context: HybridSamplingContext, reverse_time: float,
                    run_seed: int, record_id: bytes,
                    observation_law: Callable[[TransformedConfiguration, HybridSamplingContext, np.random.Generator], Any]) -> HybridJointProductSample:
        if type(context) is not HybridSamplingContext or not callable(observation_law):
            raise HybridTrainingSamplingError("explicit context and observation law required")
        if type(self.initializer) is not ReferenceConfigurationInitializer:
            raise HybridTrainingSamplingError("candidate-base classifier pairs must start from reference Pi_N")
        u = _finite(reverse_time, "interior sampling time")
        if not 0.0 < u < self.process.schedule.horizon or u not in self.plan.reverse_grid:
            raise HybridTrainingSamplingError("interior sampling time must be an exact declared grid point")
        pair_record = hashlib.sha256(_framed((context.key(), _key(record_id, "record_id")))).digest()
        branches = []
        for branch_id in (b"candidate-branch-one", b"candidate-branch-two"):
            path = self.sample_path(run_seed=run_seed, record_id=pair_record, branch_id=branch_id)
            observation_rng = _Streams(run_seed, pair_record, branch_id).rng("observation", 0)
            observation = observation_law(path.terminal_state, context, observation_rng)
            branches.append(ObservedHybridTrajectory(path, path.at_time(u), path.terminal_state, observation))
        return HybridJointProductSample(context, u, branches[0], branches[1])
