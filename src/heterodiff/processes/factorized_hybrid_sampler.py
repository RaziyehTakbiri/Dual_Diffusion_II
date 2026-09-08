"""Local CPU numerical sampler for countable exact-key, 0/1-D configurations.

The reference forward transition uses exact OU transitions and the complete
capped birth/death CTMC, up to finite RNG/arithmetic. The learned reverse path
uses Strang/Heun splitting and midpoint-frozen jump rates: it is not an exact
continuous-time learned sampler or a transferred historical certificate.
"""
from dataclasses import dataclass
import hashlib
import math

import numpy as np

from heterodiff.data.two_domain_factorized_state import FactoredEvent
from heterodiff.theory.factorized_smooth_amendment import FactorizedSmoothOracle
from heterodiff.experiments.two_domain_baseline_registry import PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID


class FactorizedSamplingError(RuntimeError):
    pass


def _need(ok, message):
    if not ok:
        raise FactorizedSamplingError(message)


def _finite(x, label):
    _need(type(x) in (float, int) and not isinstance(x, bool), label)
    x = float(x)
    _need(math.isfinite(x), label)
    return x


def _uniform(rng):
    x = float(rng.random())
    _need(0 < x < 1, "finite RNG endpoint: no redraw or silent atom")
    return x


def _log_choice(log_weights, rng):
    """Finite-RNG exponential race, without flooring positive tiny masses."""
    rows = []
    for i, w in enumerate(log_weights):
        _need(w != math.inf and not math.isnan(w), "invalid categorical weight")
        if w != -math.inf:
            rows.append((math.log(-math.log(_uniform(rng))) - w, i))
    _need(bool(rows), "empty categorical law")
    return min(rows)[1]


def canonical(state):
    _need(type(state) is tuple and all(type(e) is FactoredEvent for e in state),
          "exact factored event tuple required")
    return tuple(sorted(state, key=lambda e: e.sort_key))


@dataclass(frozen=True)
class FactorizedSchedule:
    horizon: float
    clean_hold: float
    jump_rate: float
    continuous_rate: float

    def __post_init__(self):
        for name in ("horizon", "clean_hold", "jump_rate", "continuous_rate"):
            _finite(getattr(self, name), name)
        _need(0 <= self.clean_hold < self.horizon, "invalid clean hold/horizon")
        _need(self.jump_rate >= 0 and self.continuous_rate >= 0,
              "negative reference clock rate")

    def forward_clocks(self, s):
        s = _finite(s, "forward time")
        _need(0 <= s <= self.horizon, "forward time out of range")
        active = max(s - self.clean_hold, 0.)
        return self.jump_rate * active, self.continuous_rate * active

    def remaining_clocks(self, u):
        u = _finite(u, "reverse time")
        _need(0 <= u <= self.horizon, "reverse time out of range")
        return self.forward_clocks(self.horizon - u)

    def reverse_jump_rate(self, u):
        self.remaining_clocks(u)
        return self.jump_rate if u < self.horizon-self.clean_hold else 0.

    def reverse_continuous_rate(self, u):
        self.remaining_clocks(u)
        return self.continuous_rate if u < self.horizon-self.clean_hold else 0.


@dataclass(frozen=True)
class FactorizedSamplerLimits:
    maximum_events: int = 128
    maximum_reference_jumps: int = 10000
    maximum_jump_candidates: int = 10000
    maximum_recorded_events: int = 100000
    maximum_initialization_trials: int = 10000

    def __post_init__(self):
        for x in self.__dict__.values():
            _need(type(x) is int and x > 0, "positive integer resource limits required")


class ExactFactorizedReference:
    def __init__(self, oracle, schedule, limits=FactorizedSamplerLimits()):
        _need(type(oracle) is FactorizedSmoothOracle, "exact amendment oracle required")
        _need(type(schedule) is FactorizedSchedule and type(limits) is FactorizedSamplerLimits,
              "exact schedule/limits required")
        self.oracle, self.schedule, self.limits = oracle, schedule, limits
        self.parameters = oracle.parameters
        self.reference = oracle.reference
        self.birth_rate = self.parameters.reference_count_mean*self.parameters.death_rate
        _need(math.isfinite(self.birth_rate) and self.birth_rate > 0,
              "unrepresentable positive reference birth rate")

    def state(self, events):
        self.oracle._state(events, self.parameters.reference_cap)
        _need(len(events) <= self.limits.maximum_events,
              "local event resource limit: scientific cap not reduced")
        return canonical(events)

    def sample_state(self, rng):
        n = _log_choice([self.oracle.count_log_prob(i)
                         for i in range(self.parameters.reference_cap+1)], rng)
        _need(n <= self.limits.maximum_events and n <= self.oracle.limits.maximum_events,
              "sampled count exceeds local resource limit: no redraw")
        return self.state(tuple(self.reference.sample_event(rng) for _ in range(n)))

    def exit_rate(self, state):
        state = self.state(state)
        return ((self.birth_rate if len(state) < self.parameters.reference_cap else 0.)
                + self.parameters.death_rate*len(state))

    def proposal(self, state, rng):
        state = self.state(state)
        total = self.exit_rate(state)
        if total == 0:
            return None
        birth = self.birth_rate if len(state) < self.parameters.reference_cap else 0.
        death = self.parameters.death_rate*len(state)
        p = birth/total
        _need(not (birth and death) or 0 < p < 1, "unrepresentable jump route mass")
        is_birth = not death or (bool(birth) and _uniform(rng) < p)
        if is_birth:
            dest = state + (self.reference.sample_event(rng),)
            kind = "birth"
        else:
            i = int(rng.integers(len(state)))
            dest = state[:i] + state[i+1:]
            kind = "death"
        return self.state(dest), total, kind

    def _ou(self, state, clock, rng):
        if clock == 0 or not any(e.key.dimension for e in state):
            return state
        _need(clock > 0 and math.isfinite(clock), "invalid OU clock")
        a = math.exp(-clock/2)
        _need(a > 0, "OU survival underflow: no limiting-law substitution")
        sd = math.sqrt(-math.expm1(-clock))
        result = []
        for e in state:
            r = (float(a*e.coordinate + sd*float(rng.standard_normal()))
                 if e.key.dimension else None)
            _need(r is None or math.isfinite(r), "nonfinite OU coordinate")
            result.append(FactoredEvent(e.key, r))
        return self.state(tuple(result))

    def sample_forward(self, state, s, rng):
        """Q0 -> reference at physical s; no learned potential or Heun error."""
        self.schedule.forward_clocks(s)
        state = self.state(state)
        t = min(s, self.schedule.clean_hold)
        jumps = 0
        while t < s:
            rate = self.schedule.jump_rate*self.exit_rate(state)
            _need(math.isfinite(rate), "nonfinite reference exit rate")
            wait = math.inf if rate == 0 else -math.log(_uniform(rng))/rate
            _need(wait > 0, "reference waiting time cannot advance")
            dt = min(s-t, wait)
            _need(t+dt > t, "reference clock cannot advance")
            state = self._ou(state, self.schedule.continuous_rate*dt, rng)
            t += dt
            if t < s:  # wait==dt for every realized jump before the endpoint
                _need(jumps < self.limits.maximum_reference_jumps,
                      "reference jump resource limit: no truncated path")
                proposal = self.proposal(state, rng)
                _need(proposal is not None, "positive reference rate with no proposal")
                state = proposal[0]
                jumps += 1
        return state


def _gradient(potential, u, state):
    value, rows = potential.value_grad(u, state)
    value = _finite(value, "physical potential")
    bound = _finite(potential.upper_value_bound, "physical upper bound")
    _need(value <= bound, "physical upper bound violated")
    _need(type(rows) is tuple and len(rows) == len(state), "gradient occurrence mismatch")
    for e, row in zip(state, rows):
        _need(type(row) is tuple and len(row) == e.key.dimension,
              "gradient fiber dimension mismatch")
        for x in row:
            _finite(x, "gradient")
    return rows


def heun_step(state, u, dt, potential, rate, brownian_increments):
    """One additive-noise step with explicit ΔW (variance dt), for coupling tests.

    Coefficients are owned by this active segment even at its held endpoint.
    Predictor sorting carries occurrence indices; duplicates are not matched by
    value. A zero rate is an exact copy and makes no potential call.
    """
    ordered_state = canonical(state)
    _need(state == ordered_state, "explicit Brownian increments require canonical input order")
    state = ordered_state
    _need(dt > 0 and math.isfinite(dt) and rate >= 0 and math.isfinite(rate),
          "invalid Heun segment")
    if rate == 0 or not any(e.key.dimension for e in state):
        return state
    _need(type(brownian_increments) is tuple and len(brownian_increments) == len(state),
          "Brownian occurrence mismatch")
    g0 = _gradient(potential, u, state)
    predictors, drifts, noises = [], [], []
    for e, g, row in zip(state, g0, brownian_increments):
        _need(type(row) is tuple and len(row) == e.key.dimension, "Brownian fiber mismatch")
        if e.key.dimension:
            noise = math.sqrt(rate)*_finite(row[0], "Brownian increment")
            drift = rate*(-e.coordinate/2+g[0])
            x = float(e.coordinate+dt*drift+noise)
            _need(math.isfinite(x), "nonfinite Heun predictor")
        else:
            x, drift, noise = None, 0., 0.
        predictors.append(FactoredEvent(e.key, x))
        drifts.append(drift)
        noises.append(noise)
    permutation = sorted(range(len(state)), key=lambda i: predictors[i].sort_key)
    ordered = tuple(predictors[i] for i in permutation)
    g1 = _gradient(potential, u+dt, ordered)
    restored = [None]*len(state)
    for j, i in enumerate(permutation):
        restored[i] = g1[j]
    result = []
    for i, e in enumerate(state):
        x = None
        if e.key.dimension:
            d1 = rate*(-predictors[i].coordinate/2+restored[i][0])
            x = float(e.coordinate+dt*(drifts[i]+d1)/2+noises[i])
            _need(math.isfinite(x), "nonfinite Heun corrector")
        result.append(FactoredEvent(e.key, x))
    return canonical(tuple(result))


class _Streams:
    def __init__(self, seed, record_id, branch_id):
        _need(type(seed) is int and 0 <= seed < 2**64, "uint64 seed required")
        _need(type(record_id) is bytes and bool(record_id) and
              type(branch_id) is bytes and bool(branch_id), "explicit stream keys required")
        self.root = hashlib.sha256(seed.to_bytes(8, "big")+len(record_id).to_bytes(8, "big")
                                   +record_id+branch_id).digest()
        self.requests = 0

    def rng(self, purpose, step=0, ordinal=0):
        self.requests += 1
        data = self.root+purpose.encode("ascii")+step.to_bytes(8, "big")+ordinal.to_bytes(8, "big")
        return np.random.Generator(np.random.PCG64(int.from_bytes(hashlib.sha256(data).digest(), "big")))


@dataclass(frozen=True)
class FactorizedTrajectory:
    reverse_grid: tuple
    states: tuple
    diagnostics: dict

    @property
    def terminal_state(self):
        return self.states[-1]

    def at_time(self, u):
        _need(u in self.reverse_grid, "query must be an explicit numerical grid point")
        return self.states[self.reverse_grid.index(u)]


class LearnedFactorizedSampler:
    def __init__(self, reference, potential, reverse_grid, *, initializer=None):
        _need(type(reference) is ExactFactorizedReference, "exact factorized reference required")
        _need(type(reverse_grid) is tuple and len(reverse_grid) >= 2, "explicit grid tuple required")
        grid = tuple(_finite(u, "grid") for u in reverse_grid)
        _need(grid[0] == 0 and grid[-1] == reference.schedule.horizon and
              all(a < b for a, b in zip(grid, grid[1:])), "invalid reverse grid")
        _need(reference.schedule.horizon-reference.schedule.clean_hold in grid,
              "grid must include reflected clean-hold breakpoint")
        _finite(potential.upper_value_bound, "global physical upper bound")
        self.reference, self.potential, self.grid = reference, potential, grid
        self.initializer = initializer
        self.upper_value_bound = float(potential.upper_value_bound)

    def _value(self, u, state):
        _need(self.potential.upper_value_bound == self.upper_value_bound, "changed physical bound")
        x = _finite(self.potential.value(u, state), "physical value")
        _need(x <= self.upper_value_bound, "physical bound violated")
        return x

    def _heun(self, state, u, dt, rate, rng):
        if rate == 0 or not any(e.key.dimension for e in state):
            return state
        noise = tuple((float(math.sqrt(dt)*rng.standard_normal()),) if e.key.dimension else ()
                      for e in state)
        return self.reference.state(heun_step(state, u, dt, self.potential, rate, noise))

    def _jumps(self, state, midpoint, duration, step, streams, counts, journal):
        elapsed, ordinal = 0., 0
        gamma = self.reference.schedule.reverse_jump_rate(midpoint)
        while elapsed < duration:
            rate = gamma*self.reference.exit_rate(state)
            if rate == 0:
                break
            _need(math.isfinite(rate), "nonfinite scheduled jump rate")
            source = self._value(midpoint, state)
            log_envelope = math.nextafter(math.log(rate)+self.upper_value_bound-source, math.inf)
            log_wait = math.log(-math.log(_uniform(streams.rng("jump-wait", step, ordinal))))-log_envelope
            if log_wait >= math.log(duration-elapsed):
                break
            wait = math.exp(log_wait)
            _need(wait > 0 and elapsed+wait > elapsed, "tilted jump clock cannot advance")
            _need(counts["jump_candidates"] < self.reference.limits.maximum_jump_candidates,
                  "jump candidate resource limit: no partial trajectory")
            proposal = self.reference.proposal(state, streams.rng("jump-route", step, ordinal))
            _need(proposal is not None, "positive exit rate returned no proposal")
            dest, _, kind = proposal
            destination = self._value(midpoint, dest)
            log_accept = destination-source+math.log(rate)-log_envelope
            _need(math.isfinite(log_accept) and log_accept <= 0, "invalid log acceptance")
            accepted = math.log(_uniform(streams.rng("jump-accept", step, ordinal))) < log_accept
            counts["jump_candidates"] += 1
            counts["accepted_jumps"] += int(accepted)
            counts["accepted_"+kind] += int(accepted)
            journal.append((step, kind, accepted, len(state), len(dest), log_accept))
            if accepted:
                state = dest
            elapsed += wait
            ordinal += 1
        return state

    def sample_path(self, *, run_seed, record_id, branch_id=b"path"):
        streams = _Streams(run_seed, record_id, branch_id)
        initial_rng = streams.rng("initial")
        state = (self.reference.sample_state(initial_rng) if self.initializer is None
                 else self.initializer(initial_rng))
        state = self.reference.state(state)
        states, journal = [state], []
        recorded = len(state)
        counts = dict(jump_candidates=0, accepted_jumps=0, accepted_birth=0,
                      accepted_death=0, active_intervals=0, held_intervals=0)
        for step, (start, end) in enumerate(zip(self.grid, self.grid[1:])):
            if start >= self.reference.schedule.horizon-self.reference.schedule.clean_hold:
                counts["held_intervals"] += 1
                states.append(state)  # No potential, noise, or stream request.
                recorded += len(state)
            else:
                counts["active_intervals"] += 1
                mid = start+(end-start)/2
                _need(start < mid < end, "unrepresentable midpoint")
                rate = self.reference.schedule.reverse_continuous_rate(mid)
                state = self._heun(state, start, mid-start, rate, streams.rng("heun-first", step))
                state = self._jumps(state, mid, end-start, step, streams, counts, journal)
                state = self._heun(state, mid, end-mid, rate, streams.rng("heun-second", step))
                states.append(state)
                recorded += len(state)
            _need(recorded <= self.reference.limits.maximum_recorded_events,
                  "recorded occurrence resource limit: no partial trajectory")
        diagnostics = {**counts, "stream_requests": streams.requests,
                       "stream_binding_sha256": hashlib.sha256(streams.root).hexdigest(),
                       "jump_journal": tuple(journal), "recorded_events": recorded,
                       "reference_pi_n_initializer": self.initializer is None,
                       "exact_learned_path_or_finite_rng_law_claimed": False,
                       "nuisance_in_physical_potential": False,
                       "scope": "LOCAL_SYNTHETIC_NUMERICAL_QUALIFICATION_ONLY"}
        return FactorizedTrajectory(self.grid, tuple(states), diagnostics)


def conditional_initializer(guide, potential, observed, schedule, method_id, *, maximum_trials=10000):
    """Pi_N × guide/g × bounded residual, excluding BASE and nuisance."""
    _need(method_id in (PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID), "unknown conditional method")
    _need(type(maximum_trials) is int and maximum_trials > 0, "initializer trial limit")
    clocks = schedule.remaining_clocks(0.) if method_id == PRIMARY_METHOD_ID else (0., 0.)
    bound = _finite(potential.initialization_residual_upper_bound, "residual initializer bound")

    def draw(rng):
        for _ in range(maximum_trials):
            state = guide.sample_reference_posterior(observed, rng, jump_clock=clocks[0],
                                                     continuous_clock=clocks[1])
            tilt = _finite(potential.initialization_residual_log_tilt(state), "residual initializer tilt")
            _need(tilt <= bound, "residual initializer bound violated")
            if math.log(_uniform(rng)) < tilt-bound:
                return state
        raise FactorizedSamplingError("conditional initialization resource limit: no fallback law")
    return draw
