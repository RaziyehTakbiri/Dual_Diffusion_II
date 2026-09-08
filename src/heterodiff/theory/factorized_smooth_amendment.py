"""Bounded numerical oracle for the mixed-domain scientific amendment.

Not a production sampler, source-admission rule, or old finite-type certificate.
The ideal law has countable full-support keys; these routines explicitly refuse
oversized computations, never truncate a scientific state or renormalize a
reference vocabulary. All scientific parameters must be supplied explicitly.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math

import numpy as np

from heterodiff.data.two_domain_factorized_state import FactoredEvent


class SmoothAmendmentError(ValueError):
    pass


def _need(condition, code):
    if not condition:
        raise SmoothAmendmentError(code)


def _logsum(values):
    values = tuple(values)
    _need(all(not math.isnan(x) and x != math.inf for x in values), "INVALID_LOG_VALUE_NO_SILENT_ZERO")
    maximum = max(values, default=-math.inf)
    if maximum == -math.inf:
        return maximum
    _need(math.isfinite(maximum), "NONFINITE_LOG_VALUE")
    return maximum + math.log(math.fsum(math.exp(x - maximum) for x in values))


def _normal_log_ratio(value, mean, variance):
    _need(all(math.isfinite(x) for x in (value, mean, variance)) and variance > 0,
          "FINITE_POSITIVE_GAUSSIAN_PARAMETERS_REQUIRED")
    try:
        # Expanded coefficients avoid cancellation of two huge value**2 terms,
        # especially the exact variance=1 case. This remains binary64 arithmetic,
        # not an interval-certified log-density computation at arbitrary scales.
        quadratic = 0.5 * ((variance - 1) / variance)
        result = math.fsum((quadratic * value * value if quadratic else 0.0,
                            (mean / variance) * value,
                            -0.5 * (mean / variance) * mean,
                            -0.5 * math.log(variance)))
    except (OverflowError, ValueError) as error:
        raise SmoothAmendmentError("GAUSSIAN_NUMERIC_RANGE_NO_SILENT_ZERO") from error
    _need(math.isfinite(result), "GAUSSIAN_NUMERIC_RANGE_NO_SILENT_ZERO")
    return result


@dataclass(frozen=True)
class AmendmentParameters:
    reference_count_mean: float
    reference_cap: int
    observation_cap: int
    death_rate: float
    target_contamination: float
    target_log_value_sd: float
    observation_contamination: float
    observation_log_value_sd: float

    def __post_init__(self):
        for name in ("reference_count_mean", "death_rate", "observation_log_value_sd"):
            value = getattr(self, name)
            _need(type(value) is float and math.isfinite(value) and value > 0, name + "_MUST_BE_POSITIVE")
        for name in ("target_contamination", "target_log_value_sd", "observation_contamination"):
            value = getattr(self, name)
            _need(type(value) is float and math.isfinite(value) and 0 < value < 1, name + "_MUST_BE_IN_0_1")
        for name in ("reference_cap", "observation_cap"):
            value = getattr(self, name)
            _need(type(value) is int and value >= 0, name + "_MUST_BE_NONNEGATIVE_INTEGER")
        for sd in (self.target_log_value_sd, self.observation_log_value_sd):
            _need(math.isfinite(sd * sd) and sd * sd > 0, "GAUSSIAN_VARIANCE_NOT_REPRESENTABLE")


@dataclass(frozen=True)
class OracleLimits:
    maximum_events: int = 128
    maximum_anchors_per_key: int = 12
    maximum_count_terms: int = 1_100_000
    maximum_reference_draws: int = 10_000

    def __post_init__(self):
        _need(all(type(x) is int and x > 0 for x in self.__dict__.values()), "POSITIVE_ORACLE_LIMITS_REQUIRED")


def poisson_log_survival(cap, mean, *, maximum_terms=1_100_000):
    """log P(Pois(mean)>cap), retaining very small positive tail probabilities."""
    _need(type(cap) is int and math.isfinite(mean) and mean >= 0, "INVALID_POISSON_ARGUMENT")
    if cap < 0:
        return 0.0
    if mean == 0:
        return -math.inf
    if cap < mean:
        _need(cap + 1 <= maximum_terms, "POISSON_RESOURCE_LIMIT_NO_TRUNCATION")
        log_cdf = _logsum(-mean + j * math.log(mean) - math.lgamma(j + 1) for j in range(cap + 1))
        _need(log_cdf < 0, "POISSON_CDF_NUMERIC_RESOLUTION")
        return math.log(-math.expm1(log_cdf))
    first = -mean + (cap + 1) * math.log(mean) - math.lgamma(cap + 2)
    term, total = 1.0, 1.0
    for j in range(1, maximum_terms + 1):
        term *= mean / (cap + 1 + j)
        total += term
        # Remaining geometric envelope is an absolute tail-series error bound.
        next_ratio = mean / (cap + 2 + j)
        if term * next_ratio / (1 - next_ratio) <= 2e-16 * total:
            return first + math.log(total)
    raise SmoothAmendmentError("POISSON_RESOURCE_LIMIT_NO_TRUNCATION")


class FactorizedSmoothOracle:
    """Exact-formula/log-space numerical checks at explicitly bounded sizes.

    ``reference`` supplies log_prob(key) and sample_event(numpy_rng). Its ideal
    normalization/full-support argument is separate from finite-RNG sampling.
    ``None`` denotes the observation overflow symbol, not an empty observation.
    """

    def __init__(self, reference, parameters, *, limits=OracleLimits()):
        _need(type(parameters) is AmendmentParameters and type(limits) is OracleLimits, "EXACT_PARAMETER_TYPES_REQUIRED")
        self.reference, self.parameters, self.limits = reference, parameters, limits
        _need(parameters.reference_cap + 1 <= limits.maximum_count_terms, "REFERENCE_COUNT_RESOURCE_LIMIT_NO_CAP_CHANGE")
        theta = parameters.reference_count_mean
        self._count_log_normalizer = _logsum(j * math.log(theta) - math.lgamma(j + 1)
                                            for j in range(parameters.reference_cap + 1))

    def _state(self, events, cap):
        _need(type(events) is tuple and all(type(x) is FactoredEvent for x in events), "EXACT_EVENT_TUPLE_REQUIRED")
        _need(len(events) <= cap, "SCIENTIFIC_COUNT_CAP_EXCEEDED")
        _need(len(events) <= self.limits.maximum_events, "LOCAL_EVENT_RESOURCE_LIMIT_NO_DROPPING")
        domains = {x.key.domain_id for x in events}
        _need(len(domains) <= 1, "MIXED_DOMAIN_STATE_FORBIDDEN")
        for event in events:
            self._log_q(event.key)

    def _log_q(self, key):
        value = self.reference.log_prob(key)
        _need(math.isfinite(value) and value <= 1e-12, "POSITIVE_FINITE_REFERENCE_KEY_LOG_MASS_REQUIRED")
        return value

    def count_log_prob(self, count):
        _need(type(count) is int and 0 <= count <= self.parameters.reference_cap, "REFERENCE_COUNT_OUT_OF_RANGE")
        return count * math.log(self.parameters.reference_count_mean) - math.lgamma(count + 1) - self._count_log_normalizer

    @staticmethod
    def _groups(events):
        result = defaultdict(list)
        for event in events:
            result[event.key].append(event)
        return result

    def lift_log_density(self, source, target):
        """RN derivative of unordered occurrence-preserving Gaussian lift / Pi_N.

        Summation over all bijections (including duplicate occurrences) and the
        n! denominator are both essential; no matching maximization is used.
        """
        p = self.parameters
        self._state(source, p.reference_cap)
        self._state(target, p.reference_cap)
        if Counter(x.key for x in source) != Counter(x.key for x in target):
            return -math.inf
        target_groups = self._groups(target)
        total = -self.count_log_prob(len(target)) - math.lgamma(len(target) + 1)
        for key, sources in self._groups(source).items():
            targets = target_groups[key]
            k = len(targets)
            _need(k <= self.limits.maximum_anchors_per_key, "PER_KEY_PERMANENT_RESOURCE_LIMIT_NO_APPROXIMATION")
            dp = {0: 0.0}
            for item in sources:
                next_dp = {}
                for mask, weight in dp.items():
                    for j, other in enumerate(targets):
                        if mask & (1 << j):
                            continue
                        ratio = -self._log_q(key)
                        if key.dimension:
                            ratio += _normal_log_ratio(other.coordinate, item.coordinate, p.target_log_value_sd ** 2)
                        new_mask = mask | (1 << j)
                        next_dp[new_mask] = _logsum((next_dp.get(new_mask, -math.inf), weight + ratio))
                dp = next_dp
            total += dp[(1 << k) - 1]
        return total

    def target_log_density(self, train_sources, target):
        _need(type(train_sources) is tuple and len(train_sources) > 0, "NONEMPTY_EXPLICIT_TRAIN_SOURCE_ROSTER_REQUIRED")
        alpha = self.parameters.target_contamination
        lift = _logsum(self.lift_log_density(source, target) for source in train_sources) - math.log(len(train_sources))
        return _logsum((math.log(alpha), math.log1p(-alpha) + lift))

    def _clocks(self, jump_clock, continuous_clock):
        _need(all(type(x) is float and math.isfinite(x) and x >= 0 for x in (jump_clock, continuous_clock)), "NONNEGATIVE_INTEGRATED_CLOCKS_REQUIRED")
        exponent = self.parameters.death_rate * jump_clock
        _need(math.isfinite(exponent), "CLOCK_PRODUCT_NOT_REPRESENTABLE")
        survival = math.exp(-exponent)
        retain = 0.5 * survival
        immigrant_mean = 0.5 * self.parameters.reference_count_mean * -math.expm1(-exponent)
        contraction = math.exp(-continuous_clock / 2)
        variance = self.parameters.observation_log_value_sd ** 2 + -math.expm1(-continuous_clock)
        _need(retain > 0 and contraction > 0, "CLOCK_UNDERFLOW_NO_BRANCH_DELETION")
        _need(math.isfinite(immigrant_mean) and math.isfinite(variance) and variance > 0,
              "PROPAGATED_GAUSSIAN_NOT_REPRESENTABLE")
        _need(jump_clock == 0 or exponent > 0 and immigrant_mean > 0, "CLOCK_UNDERFLOW_NO_BRANCH_DELETION")
        return retain, immigrant_mean, contraction, variance

    def clean_observation_log_density(self, state, observed, *, jump_clock=0.0, continuous_clock=0.0):
        """Terminal K or uncapped auxiliary propagated K; never the capped h."""
        p = self.parameters
        self._state(state, p.reference_cap)
        retain, immigrant_mean, contraction, variance = self._clocks(jump_clock, continuous_clock)
        if observed is None:
            n = len(state)
            terms = []
            for j in range(n + 1):
                log_binomial = (math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
                                + (j * math.log(retain) if j and retain else 0.0)
                                + (n - j) * math.log1p(-retain))
                if j and retain == 0:
                    continue
                log_tail = poisson_log_survival(p.observation_cap - j, immigrant_mean,
                                               maximum_terms=self.limits.maximum_count_terms)
                terms.append(log_binomial + log_tail)
            numerator = _logsum(terms)
            return numerator - poisson_log_survival(p.observation_cap, 1.0,
                                                    maximum_terms=self.limits.maximum_count_terms)
        self._state(observed, p.observation_cap)
        sources = self._groups(state)
        observations = self._groups(observed)
        total = 1.0 - immigrant_mean  # Poisson Janossy / unit-Poisson reference
        for key, items in sources.items():
            if key not in observations:
                total += len(items) * math.log1p(-retain)
        for key, anchors in observations.items():
            k = len(anchors)
            _need(k <= self.limits.maximum_anchors_per_key, "PER_KEY_MATCHING_RESOURCE_LIMIT_NO_APPROXIMATION")
            dp = {0: 0.0}
            for item in sources.get(key, ()):
                next_dp = {}
                for mask, weight in dp.items():
                    next_dp[mask] = _logsum((next_dp.get(mask, -math.inf), weight + math.log1p(-retain)))
                    if retain == 0:
                        continue
                    for j, anchor in enumerate(anchors):
                        if mask & (1 << j):
                            continue
                        signal = -self._log_q(key)
                        if key.dimension:
                            signal += _normal_log_ratio(anchor.coordinate, contraction * item.coordinate, variance)
                        new_mask = mask | (1 << j)
                        next_dp[new_mask] = _logsum((next_dp.get(new_mask, -math.inf), weight + math.log(retain) + signal))
                dp = next_dp
            clutter = []
            for anchor in anchors:
                value = math.log(immigrant_mean) if immigrant_mean else -math.inf
                if key.dimension and immigrant_mean:
                    value += _normal_log_ratio(anchor.coordinate, 0.0, 1 + p.observation_log_value_sd ** 2)
                clutter.append(value)
            total += _logsum(weight + sum(clutter[j] for j in range(k) if not mask & (1 << j))
                             for mask, weight in dp.items())
        return total

    def observation_log_density(self, state, observed, *, jump_clock=0.0, continuous_clock=0.0):
        epsilon = self.parameters.observation_contamination
        clean = self.clean_observation_log_density(state, observed, jump_clock=jump_clock,
                                                   continuous_clock=continuous_clock)
        return _logsum((math.log(epsilon), math.log1p(-epsilon) + clean))

    def sample_training_target(self, train_sources, rng):
        """Finite-RNG implementation; refusal is not a conditional ideal sample."""
        _need(type(rng) is np.random.Generator, "EXPLICIT_NUMPY_GENERATOR_REQUIRED")
        _need(type(train_sources) is tuple and len(train_sources) > 0, "EXPLICIT_TRAIN_ROSTER_REQUIRED")
        for source in train_sources:
            self._state(source, self.parameters.reference_cap)
        if rng.random() < self.parameters.target_contamination:
            for _ in range(self.limits.maximum_reference_draws):
                count = int(rng.poisson(self.parameters.reference_count_mean))
                if count <= self.parameters.reference_cap:
                    break
            else:
                raise SmoothAmendmentError("CAPPED_POISSON_DRAW_RESOURCE_LIMIT")
            _need(count <= self.limits.maximum_events, "LOCAL_EVENT_RESOURCE_LIMIT_NO_DROPPING")
            result = tuple(self.reference.sample_event(rng) for _ in range(count))
        else:
            source = train_sources[int(rng.integers(len(train_sources)))]
            result = tuple(FactoredEvent(x.key, float(x.coordinate + self.parameters.target_log_value_sd * rng.normal()))
                           if x.key.dimension else x for x in source)
        self._state(result, self.parameters.reference_cap)
        return result

    def sample_observation(self, state, rng):
        _need(type(rng) is np.random.Generator, "EXPLICIT_NUMPY_GENERATOR_REQUIRED")
        self._state(state, self.parameters.reference_cap)
        if rng.random() < self.parameters.observation_contamination:
            count = int(rng.poisson(1.0))
            if count > self.parameters.observation_cap:
                return None
            _need(count <= self.limits.maximum_events, "LOCAL_EVENT_RESOURCE_LIMIT_NO_DROPPING")
            result = tuple(self.reference.sample_event(rng) for _ in range(count))
        else:
            retained = tuple(x for x in state if rng.random() < 0.5)
            if len(retained) > self.parameters.observation_cap:
                return None
            result = tuple(FactoredEvent(x.key, float(x.coordinate + self.parameters.observation_log_value_sd * rng.normal()))
                           if x.key.dimension else x for x in retained)
        self._state(result, self.parameters.observation_cap)
        return result


def f105_unconditional_target_mmd_bound(*, alpha, tau, continuous_fraction=1.0,
                                      event_lengthscale=1.0, outer_lengthscale=1.0, event_scale=1.0):
    """Ideal-real F105 bound, NOT a posterior/sample/finite-precision guarantee.

    continuous_fraction is E[n_cont/n; n>0]. The frozen two-domain kernel has
    all three scale parameters equal to one. Float encoding error is additional.
    """
    _need(all(math.isfinite(x) for x in (alpha, tau, continuous_fraction, event_lengthscale, outer_lengthscale, event_scale)), "FINITE_BOUND_PARAMETERS_REQUIRED")
    _need(0 < alpha < 1 and 0 < tau < 1 and 0 <= continuous_fraction <= 1, "INVALID_TARGET_BOUND_ARGUMENT")
    _need(event_lengthscale > 0 and outer_lengthscale > 0 and event_scale > 0, "POSITIVE_KERNEL_SCALES_REQUIRED")
    lift = tau * math.sqrt(2 / math.pi) * continuous_fraction * event_scale / (4 * event_lengthscale * outer_lengthscale)
    return min(math.sqrt(2), (1 - alpha) * lift + alpha * math.sqrt(2))
