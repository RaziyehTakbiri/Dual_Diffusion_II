"""Differentiable bounded-size reference guide and numerical initial sampler.

New CPU float64 prototype, not an old finite-type certificate. The analytic
h_tilde propagates the observation through the uncapped auxiliary reference;
it is not the capped process's exact propagated likelihood. The posterior
targets Pi_N*h_tilde, not a learned-base or Q0 posterior. Exact mathematical
formulas, finite binary64/PCG64 sampling, and resource refusals are distinct.
No probability floor, vocabulary truncation, scientific setting, or data
admission is introduced here.
"""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math

import numpy as np
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, TrainInformedMetadataReference,
)
from heterodiff.theory.factorized_smooth_amendment import (
    FactorizedSmoothOracle, SmoothAmendmentError, _logsum,
    _normal_log_ratio, poisson_log_survival,
)


class FactorizedGuideError(SmoothAmendmentError):
    pass


def _need(condition, code):
    if not condition:
        raise FactorizedGuideError(code)


def _constant(value):
    return torch.tensor(value, dtype=torch.float64, device="cpu")


def _torch_logsum(values, zero):
    # All-impossible logsumexp has undefined gradients. Remove structural -inf
    # branches before logsumexp, and attach a true zero derivative if none remain.
    finite = []
    for value in values:
        number = float(value.detach())
        _need(not math.isnan(number) and number != math.inf,
              "NONFINITE_DIFFERENTIABLE_LOG_VALUE")
        if number != -math.inf:
            finite.append(value)
    return torch.logsumexp(torch.stack(finite), 0) if finite else zero + _constant(-math.inf)


def _binomial_log(n, k, probability):
    if not 0 <= k <= n:
        return -math.inf
    if probability == 0:
        return 0.0 if k == 0 else -math.inf
    if probability == 1:
        return 0.0 if k == n else -math.inf
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
            + k * math.log(probability) + (n - k) * math.log1p(-probability))


def _poisson_logs(cap, mean):
    _need(math.isfinite(mean) and mean >= 0, "INVALID_POISSON_MEAN")
    if mean == 0:
        return [0.0] + [-math.inf] * cap
    return [-mean + j * math.log(mean) - math.lgamma(j + 1) for j in range(cap + 1)]


def _sample_log_weights(log_weights, rng):
    """Log exponential race: never exponentiate/floor small input masses.

    This uses finite RNG exponential variates, not exact ideal continuous
    entropy. A zero/nonfinite variate refuses rather than redrawing.
    """
    best, winner = -math.inf, None
    for index, weight in enumerate(log_weights):
        _need(not math.isnan(weight) and weight != math.inf, "INVALID_SAMPLING_LOG_WEIGHT")
        if weight == -math.inf:
            continue
        draw = float(rng.exponential())
        _need(math.isfinite(draw) and draw > 0, "EXPONENTIAL_RNG_ENDPOINT_NO_REDRAW")
        score = weight - math.log(draw)
        _need(math.isfinite(score), "SAMPLING_SCORE_NUMERIC_RANGE")
        if winner is None or score > best:
            best, winner = score, index
    _need(winner is not None, "IMPOSSIBLE_POSTERIOR_COMPONENT")
    return winner


class FactorizedAssociationGuide:
    """Known-reference snapshot with actual per-key differentiable matching.

    Supplied coordinates override the latent coordinate values while the
    state tuple supplies exact keys/dimensions. Each tensor has shape (1,) or
    (0,), dtype float64 and device CPU; returned gradients preserve row order.
    Observations are fixed FactoredEvent tuples; None means explicit overflow.
    """

    def __init__(self, oracle, *, maximum_dp_work=1_000_000,
                 maximum_posterior_work=1_100_000):
        _need(type(oracle) is FactorizedSmoothOracle, "EXACT_SMOOTH_ORACLE_REQUIRED")
        _need(type(oracle.reference) in (FactorizedMetadataReference, TrainInformedMetadataReference),
              "KNOWN_NORMALIZED_FACTORIZED_REFERENCE_REQUIRED")
        _need(all(type(x) is int and x > 0 for x in (maximum_dp_work, maximum_posterior_work)),
              "POSITIVE_GUIDE_WORK_LIMITS_REQUIRED")
        self.oracle = deepcopy(oracle)
        self.maximum_dp_work = maximum_dp_work
        self.maximum_posterior_work = maximum_posterior_work
        reference = self.oracle.reference
        record = {"schema": "factorized-association-guide-torch-v1",
                  "parameters": {key: value.hex() if type(value) is float else value
                                 for key, value in asdict(self.oracle.parameters).items()},
                  "oracle_limits": asdict(self.oracle.limits),
                  "maximum_dp_work": maximum_dp_work,
                  "maximum_posterior_work": maximum_posterior_work,
                  "reference_type": type(reference).__name__, "domain": reference.domain_id}
        if type(reference) is TrainInformedMetadataReference:
            record["reference_beta"] = [hex(reference.beta.numerator), hex(reference.beta.denominator)]
            record["train_key_frequencies"] = [(key.canonical_bytes().hex(), count)
                                               for key, count in reference.key_frequencies]
        self.identity_sha256 = hashlib.sha256(json.dumps(record, sort_keys=True,
                                                        separators=(",", ":")).encode()).hexdigest()

    def _coordinates(self, state, coordinates):
        self.oracle._state(state, self.oracle.parameters.reference_cap)
        if coordinates is None:
            coordinates = tuple(torch.tensor([] if event.coordinate is None else [event.coordinate],
                                             dtype=torch.float64, device="cpu") for event in state)
        _need(type(coordinates) is tuple and len(coordinates) == len(state), "ALIGNED_COORDINATE_TUPLE_REQUIRED")
        zero = _constant(0.0)
        for event, value in zip(state, coordinates):
            _need(type(value) is torch.Tensor and value.dtype == torch.float64
                  and value.device.type == "cpu" and value.layout == torch.strided
                  and tuple(value.shape) == (event.key.dimension,)
                  and bool(torch.isfinite(value).all()), "FINITE_CPU_FLOAT64_FIBER_TENSOR_REQUIRED")
            zero = zero + value.sum() * 0.0
        return coordinates, zero

    def log_value(self, state, observed, coordinates=None, *, jump_clock=0.0, continuous_clock=0.0):
        coordinates, zero = self._coordinates(state, coordinates)
        p, oracle = self.oracle.parameters, self.oracle
        retain, immigrants, contraction, variance = oracle._clocks(jump_clock, continuous_clock)
        if observed is None:
            return zero + _constant(oracle.observation_log_density(
                state, None, jump_clock=jump_clock, continuous_clock=continuous_clock))
        oracle._state(observed, p.observation_cap)
        sources = {}
        for event, value in zip(state, coordinates):
            sources.setdefault(event.key, []).append(value)
        observations = oracle._groups(observed)
        work = 0
        for key, anchors in observations.items():
            k = len(anchors)
            _need(k <= oracle.limits.maximum_anchors_per_key, "PER_KEY_MATCHING_RESOURCE_LIMIT_NO_APPROXIMATION")
            work += max(1, len(sources.get(key, ()))) * (1 << k) * max(k, 1)
            _need(work <= self.maximum_dp_work, "GUIDE_DP_RESOURCE_LIMIT_NO_APPROXIMATION")
        total = zero + _constant(1.0 - immigrants)
        for key, items in sources.items():
            if key not in observations:
                total = total + len(items) * math.log1p(-retain)
        for key, anchors in observations.items():
            k, dp = len(anchors), {0: zero}
            for coordinate in sources.get(key, ()):
                next_dp = {}
                for mask, weight in dp.items():
                    next_dp[mask] = _torch_logsum((next_dp.get(mask, zero + _constant(-math.inf)),
                                                   weight + math.log1p(-retain)), zero)
                    for j, anchor in enumerate(anchors):
                        if mask & (1 << j):
                            continue
                        signal = zero + _constant(-oracle._log_q(key))
                        if key.dimension:
                            mean = contraction * coordinate[0]
                            value = anchor.coordinate
                            quadratic = 0.5 * ((variance - 1) / variance)
                            fixed = quadratic * value * value if quadratic else 0.0
                            signal = signal + fixed + (mean / variance) * value
                            signal = signal - 0.5 * (mean / variance) * mean - 0.5 * math.log(variance)
                            _need(bool(torch.isfinite(signal)), "GAUSSIAN_DIFFERENTIABLE_NUMERIC_RANGE")
                        new_mask = mask | (1 << j)
                        next_dp[new_mask] = _torch_logsum((next_dp.get(new_mask, zero + _constant(-math.inf)),
                                                          weight + math.log(retain) + signal), zero)
                dp = next_dp
            background = []
            for anchor in anchors:
                value = math.log(immigrants) if immigrants else -math.inf
                if key.dimension and immigrants:
                    value += _normal_log_ratio(anchor.coordinate, 0.0, 1 + p.observation_log_value_sd ** 2)
                background.append(value)
            terms = [weight + sum(background[j] for j in range(k) if not mask & (1 << j))
                     for mask, weight in dp.items()]
            total = total + _torch_logsum(terms, zero)
        result = _torch_logsum((_constant(math.log(p.observation_contamination)),
                                total + math.log1p(-p.observation_contamination)), zero)
        _need(bool(torch.isfinite(result)), "NONFINITE_MIXTURE_GUIDE")
        return result + zero

    def upper_log_bound(self, observed):
        p, oracle = self.oracle.parameters, self.oracle
        if observed is None:
            clean = -poisson_log_survival(p.observation_cap, 1.0,
                                          maximum_terms=oracle.limits.maximum_count_terms)
        else:
            oracle._state(observed, p.observation_cap)
            clean = 1.0 + math.lgamma(len(observed) + 1)
            for event in observed:
                clean -= oracle._log_q(event.key)
                if event.key.dimension:
                    clean += 0.5 * event.coordinate * event.coordinate - math.log(p.observation_log_value_sd)
        _need(math.isfinite(clean), "GUIDE_BOUND_NUMERIC_RANGE")
        return _logsum((math.log(p.observation_contamination),
                        math.log1p(-p.observation_contamination) + clean))

    def _reference_events(self, count, rng):
        _need(count <= self.oracle.limits.maximum_events, "LOCAL_EVENT_RESOURCE_LIMIT_NO_DROPPING")
        return tuple(self.oracle.reference.sample_event(rng) for _ in range(count))

    def _reference_count_logs(self):
        n = self.oracle.parameters.reference_cap
        _need(n + 1 <= self.maximum_posterior_work, "POSTERIOR_COUNT_RESOURCE_LIMIT_NO_CAP_CHANGE")
        return [self.oracle.count_log_prob(j) for j in range(n + 1)]

    def _overflow_count_logs(self, retain, immigrants):
        p, oracle = self.oracle.parameters, self.oracle
        n, m = p.reference_cap, p.observation_cap
        prior = self._reference_count_logs()
        if immigrants == 0 and m >= n:
            return prior  # h_epsilon is constant epsilon over every prior count.
        _need((n + 1) * (m + 1) <= self.maximum_posterior_work,
              "OVERFLOW_POSTERIOR_RESOURCE_LIMIT_NO_APPROXIMATION")
        probabilities = _poisson_logs(m, immigrants)
        tail = poisson_log_survival(m, immigrants, maximum_terms=oracle.limits.maximum_count_terms)
        reference_tail = poisson_log_survival(m, 1.0, maximum_terms=oracle.limits.maximum_count_terms)
        result = []
        for count in range(n + 1):
            likelihood = _logsum((math.log(p.observation_contamination),
                                  math.log1p(-p.observation_contamination) + tail - reference_tail))
            result.append(prior[count] + likelihood)
            if count < n:
                tail = _logsum((tail, math.log(retain) + probabilities[-1]))
                probabilities = [probabilities[0] + math.log1p(-retain)] + [
                    _logsum((probabilities[j] + math.log1p(-retain),
                             probabilities[j - 1] + math.log(retain))) for j in range(1, m + 1)]
        return result

    def sample_reference_posterior(self, observed, rng, *, jump_clock=0.0, continuous_clock=0.0):
        _need(type(rng) is np.random.Generator and type(rng.bit_generator) in (np.random.PCG64, np.random.PCG64DXSM),
              "EXPLICIT_PCG64_GENERATOR_REQUIRED")
        p, oracle = self.oracle.parameters, self.oracle
        retain, immigrants, contraction, variance = oracle._clocks(jump_clock, continuous_clock)
        if observed is None:
            count = _sample_log_weights(self._overflow_count_logs(retain, immigrants), rng)
            result = self._reference_events(count, rng)
        else:
            oracle._state(observed, p.observation_cap)
            observed = tuple(sorted(observed, key=lambda event: event.sort_key))
            prior = self._reference_count_logs()
            n, k, ancestry = p.reference_cap, len(observed), 2.0 * retain
            missed_mean = p.reference_count_mean * (1.0 - retain)
            _need(math.isfinite(missed_mean) and missed_mean > 0, "MISSED_POPULATION_MEAN_NOT_REPRESENTABLE")
            poisson = _poisson_logs(n, missed_mean)
            cdf, running = [], -math.inf
            for mass in poisson:
                running = _logsum((running, mass))
                cdf.append(running)
            ancestry_weights = [_binomial_log(k, b, ancestry) + cdf[n - b]
                                for b in range(min(k, n) + 1)]
            cap_probability = _logsum(ancestry_weights)
            observed_mean = 0.5 * p.reference_count_mean
            _need(observed_mean > 0, "OBSERVED_POPULATION_MEAN_NOT_REPRESENTABLE")
            clean_evidence = 1.0 - observed_mean
            clean_evidence += k * math.log(observed_mean)
            for anchor in observed:
                if anchor.key.dimension:
                    clean_evidence += _normal_log_ratio(anchor.coordinate, 0.0, 1 + p.observation_log_value_sd ** 2)
            clean_evidence += cap_probability - (oracle._count_log_normalizer - p.reference_count_mean)
            branch = _sample_log_weights((math.log(p.observation_contamination),
                                          math.log1p(-p.observation_contamination) + clean_evidence), rng)
            if branch == 0:
                result = self._reference_events(_sample_log_weights(prior, rng), rng)
            else:
                ancestors = _sample_log_weights(ancestry_weights, rng)
                missed = _sample_log_weights(poisson[:n - ancestors + 1], rng)
                _need(ancestors + missed <= oracle.limits.maximum_events, "LOCAL_EVENT_RESOURCE_LIMIT_NO_DROPPING")
                selected = sorted(int(index) for index in rng.choice(k, size=ancestors, replace=False))
                result = list(self._reference_events(missed, rng))
                denominator = 1.0 + p.observation_log_value_sd ** 2
                posterior_variance = variance / denominator
                _need(math.isfinite(posterior_variance) and posterior_variance > 0,
                      "ANCESTOR_VARIANCE_NOT_REPRESENTABLE")
                for index in selected:
                    anchor = observed[index]
                    coordinate = None
                    if anchor.key.dimension:
                        mean = (contraction / denominator) * anchor.coordinate
                        coordinate = float(rng.normal(mean, math.sqrt(posterior_variance)))
                        _need(math.isfinite(coordinate), "ANCESTOR_COORDINATE_NOT_REPRESENTABLE")
                    result.append(FactoredEvent(anchor.key, coordinate))
                result = tuple(result)
        oracle._state(result, p.reference_cap)
        return tuple(sorted(result, key=lambda event: event.sort_key))

    def diagnostics(self):
        return {"identity_sha256": self.identity_sha256,
                "scope": "BOUNDED_CPU_FLOAT64_REFERENCE_GUIDE_AND_POSTERIOR_PROTOTYPE",
                "posterior_target": "PI_N_TIMES_INDEPENDENT_REFERENCE_GUIDE",
                "guide_reference": "UNCAPPED_AUXILIARY_BIRTH_DEATH_OU",
                "exact_capped_semigroup_claimed": False,
                "learned_base_or_Q0_posterior_claimed": False,
                "finite_rng_exact_ideal_sampling_claimed": False,
                "interval_or_global_numeric_certificate_claimed": False,
                "probability_floor_or_vocabulary_truncation_used": False,
                "scientific_parameters_adopted": False,
                "overflow_posterior_implemented": True}
