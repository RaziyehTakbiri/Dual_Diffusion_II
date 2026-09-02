"""Exact immigration--death count-process and bridge oracle.

For immigration rate ``beta > 0`` and per-particle death rate ``delta > 0``,
the transition over an elapsed interval ``dt`` is

``N(t + dt) = Binomial(N(t), exp(-delta*dt))
             + Poisson((beta/delta) * (1 - exp(-delta*dt)))``.

This module evaluates that known law, its finite-set terminal information
function, and the corresponding Doob-tilted birth and death rates.  It is a
classical analytic oracle for testing bridge implementations.  It is not a
novel generative method and it does not yet cover spatial, typed, or marked
configurations.

Log-domain APIs distinguish structural zero (returned as ``-inf``) from a
positive probability that merely underflows when exponentiated.  No epsilon
flooring is used anywhere.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import FrozenSet, Optional, Tuple, Union

import numpy as np


_MAX_COUNT = int(np.iinfo(np.int64).max)
_LOG_MAX_FLOAT = math.log(float(np.finfo(float).max))
_MAX_EXACT_COUNT = 100_000
_MAX_BRIDGE_WORK = 1_000_000
_MAX_ALLOWED_COUNTS = 10_000
_MAX_SAMPLE_SIZE = 1_000_000
_MAX_SEED = int(np.iinfo(np.uint64).max)


class UnreachableCountBridgeStateError(ValueError):
    """Raised when terminal evidence is exactly zero from a source state."""

    def __init__(self, time: float, count: int) -> None:
        self.time = time
        self.count = count
        super().__init__(
            "the terminal count observation is unreachable from count %d "
            "at time %r" % (count, time)
        )


@dataclass(frozen=True)
class CountMoments:
    """Analytic conditional mean and variance after an elapsed interval."""

    mean: float
    variance: float


def _logsumexp(values: Tuple[float, ...]) -> float:
    """Small scalar log-sum-exp implementation with exact empty-set zero."""

    if not values:
        return -math.inf
    maximum = max(values)
    if maximum == -math.inf:
        return -math.inf
    total = math.fsum(math.exp(value - maximum) for value in values)
    result = maximum + math.log(total)
    if not math.isfinite(result):
        raise ArithmeticError("log-sum-exp did not produce a finite value")
    return result


class ImmigrationDeathOracle:
    """Closed-form transition and terminal bridge for a count process."""

    def __init__(self, beta: float, delta: float) -> None:
        self._beta = self._validate_positive_real(beta, "beta")
        self._delta = self._validate_positive_real(delta, "delta")
        stationary_mean = self._beta / self._delta
        if not math.isfinite(stationary_mean) or stationary_mean <= 0.0:
            raise ValueError(
                "beta/delta must be representable as a finite positive float"
            )
        self._stationary_mean = stationary_mean

    @staticmethod
    def _validate_positive_real(value: float, name: str) -> float:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise TypeError("%s must be a real non-boolean number" % name)
        scalar = float(value)
        if not math.isfinite(scalar) or scalar <= 0.0:
            raise ValueError("%s must be finite and strictly positive" % name)
        return scalar

    @staticmethod
    def _validate_time(value: float, name: str) -> float:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise TypeError("%s must be a real non-boolean number" % name)
        scalar = float(value)
        if not math.isfinite(scalar) or scalar < 0.0:
            raise ValueError("%s must be finite and nonnegative" % name)
        return scalar

    @staticmethod
    def _validate_count(value: int, name: str = "count") -> int:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
            raise TypeError("%s must be an integer non-boolean count" % name)
        count = int(value)
        if count < 0 or count > _MAX_COUNT:
            raise ValueError(
                "%s must lie between zero and the int64 maximum" % name
            )
        return count

    @classmethod
    def _validate_allowed_counts(
        cls, allowed_counts: Collection[int]
    ) -> FrozenSet[int]:
        if isinstance(allowed_counts, (str, bytes)) or not isinstance(
            allowed_counts, Collection
        ):
            raise TypeError("allowed_counts must be a finite collection of counts")
        if len(allowed_counts) > _MAX_ALLOWED_COUNTS:
            raise ValueError(
                "allowed_counts exceeds the exact bridge set-size limit of %d"
                % _MAX_ALLOWED_COUNTS
            )
        return frozenset(
            cls._validate_exact_count(value, "allowed count")
            for value in allowed_counts
        )

    @classmethod
    def _validate_exact_count(cls, value: int, name: str) -> int:
        """Validate a count for floating-point exact-law evaluation.

        Counts beyond this explicit oracle budget are rejected rather than
        entering an unbounded convolution or returning a cancellation-damaged
        ``lgamma`` difference. Sampling and moment APIs retain the full int64
        count range.
        """

        count = cls._validate_count(value, name)
        if count > _MAX_EXACT_COUNT:
            raise ValueError(
                "%s exceeds the exact-law count limit of %d"
                % (name, _MAX_EXACT_COUNT)
            )
        return count

    @staticmethod
    def _validate_seed(seed: Optional[int]) -> Optional[int]:
        if seed is None:
            return None
        if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral):
            raise TypeError("seed must be a nonnegative integer or None")
        value = int(seed)
        if value < 0 or value > _MAX_SEED:
            raise ValueError("seed must lie in the uint64 range")
        return value

    @staticmethod
    def _validate_size(size: Optional[int]) -> Optional[int]:
        if size is None:
            return None
        if isinstance(size, (bool, np.bool_)) or not isinstance(size, Integral):
            raise TypeError("size must be a strictly positive integer or None")
        value = int(size)
        if value <= 0:
            raise ValueError("size must be strictly positive")
        if value > _MAX_SAMPLE_SIZE:
            raise ValueError(
                "size exceeds the sampling safety limit of %d"
                % _MAX_SAMPLE_SIZE
            )
        return value

    @staticmethod
    def _validate_bridge_times(
        time: float, terminal_time: float
    ) -> Tuple[float, float]:
        current = ImmigrationDeathOracle._validate_time(time, "time")
        terminal = ImmigrationDeathOracle._validate_time(
            terminal_time, "terminal_time"
        )
        if current > terminal:
            raise ValueError("time must not exceed terminal_time")
        return current, terminal

    @property
    def beta(self) -> float:
        return self._beta

    @property
    def delta(self) -> float:
        return self._delta

    @property
    def stationary_mean(self) -> float:
        return self._stationary_mean

    def _transition_components(
        self, elapsed_time: float
    ) -> Tuple[float, float, float, float]:
        """Return survival, death, immigrant mean, and log survival."""

        elapsed = self._validate_time(elapsed_time, "elapsed_time")
        if elapsed == 0.0:
            return 1.0, 0.0, 0.0, 0.0

        if elapsed > float(np.finfo(float).max) / self._delta:
            scaled_time = math.inf
        else:
            scaled_time = self._delta * elapsed
        if scaled_time == 0.0:
            raise ArithmeticError(
                "delta*elapsed_time underflowed; the transition is not "
                "representable at this time scale"
            )

        log_survival = -scaled_time
        survival = 0.0 if scaled_time == math.inf else math.exp(log_survival)
        death = 1.0 if scaled_time == math.inf else -math.expm1(-scaled_time)
        immigrant_mean = self._stationary_mean * death
        if (
            not math.isfinite(immigrant_mean)
            or immigrant_mean <= 0.0
            or death <= 0.0
            or death > 1.0
        ):
            raise ArithmeticError("transition parameters are not representable")
        return survival, death, immigrant_mean, log_survival

    @staticmethod
    def _poisson_log_pmf(count: int, mean: float) -> float:
        if mean == 0.0:
            return 0.0 if count == 0 else -math.inf
        return count * math.log(mean) - mean - math.lgamma(count + 1.0)

    @staticmethod
    def _binomial_log_pmf(
        successes: int,
        trials: int,
        log_survival: float,
        death: float,
    ) -> float:
        if successes < 0 or successes > trials:
            return -math.inf
        if log_survival == 0.0:
            return 0.0 if successes == trials else -math.inf
        if log_survival == -math.inf:
            return 0.0 if successes == 0 else -math.inf
        log_combination = (
            math.lgamma(trials + 1.0)
            - math.lgamma(successes + 1.0)
            - math.lgamma(trials - successes + 1.0)
        )
        return (
            log_combination
            + successes * log_survival
            + (trials - successes) * math.log(death)
        )

    def transition_log_pmf(
        self, source_count: int, destination_count: int, elapsed_time: float
    ) -> float:
        """Return the stable log transition mass between two counts.

        Structural zeros, including unequal counts at zero elapsed time, are
        returned exactly as ``-math.inf``.
        """

        source = self._validate_exact_count(source_count, "source_count")
        destination = self._validate_exact_count(
            destination_count, "destination_count"
        )
        elapsed = self._validate_time(elapsed_time, "elapsed_time")
        if elapsed == 0.0:
            return 0.0 if source == destination else -math.inf

        _, death, immigrant_mean, log_survival = self._transition_components(
            elapsed
        )
        terms = []
        for survivors in range(min(source, destination) + 1):
            log_binomial = self._binomial_log_pmf(
                survivors, source, log_survival, death
            )
            if log_binomial == -math.inf:
                continue
            immigrants = destination - survivors
            terms.append(
                log_binomial
                + self._poisson_log_pmf(immigrants, immigrant_mean)
            )
        result = _logsumexp(tuple(terms))
        if result > 0.0:
            raise ArithmeticError("transition log mass is positive")
        return result

    def transition_pmf(
        self, source_count: int, destination_count: int, elapsed_time: float
    ) -> float:
        """Return transition mass, allowing positive tiny values to underflow.

        Use :meth:`transition_log_pmf` whenever rare-event magnitude or the
        distinction between underflow and structural zero matters.
        """

        log_probability = self.transition_log_pmf(
            source_count, destination_count, elapsed_time
        )
        return 0.0 if log_probability == -math.inf else math.exp(log_probability)

    def moments(self, source_count: int, elapsed_time: float) -> CountMoments:
        """Return the exact conditional mean and variance of the transition."""

        source = self._validate_count(source_count, "source_count")
        elapsed = self._validate_time(elapsed_time, "elapsed_time")
        survival, death, immigrant_mean, _ = self._transition_components(elapsed)
        mean = source * survival + immigrant_mean
        variance = source * survival * death + immigrant_mean
        if not math.isfinite(mean) or not math.isfinite(variance):
            raise ArithmeticError("transition moments are not finite")
        return CountMoments(mean=mean, variance=variance)

    def sample_transition(
        self,
        source_count: int,
        elapsed_time: float,
        *,
        size: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> Union[int, np.ndarray]:
        """Draw exact transition samples from a local NumPy generator."""

        source = self._validate_count(source_count, "source_count")
        elapsed = self._validate_time(elapsed_time, "elapsed_time")
        sample_size = self._validate_size(size)
        rng = np.random.default_rng(self._validate_seed(seed))
        if elapsed == 0.0:
            if sample_size is None:
                return source
            return np.full(sample_size, source, dtype=np.int64)

        survival, death, immigrant_mean, _ = self._transition_components(elapsed)
        try:
            if death <= survival:
                deaths = rng.binomial(source, death, size=sample_size)
                survivors = source - deaths
            else:
                survivors = rng.binomial(source, survival, size=sample_size)
            immigrants = rng.poisson(immigrant_mean, size=sample_size)
        except ValueError as error:
            raise ArithmeticError(
                "NumPy cannot sample the requested representable transition"
            ) from error
        if np.any(survivors > _MAX_COUNT - immigrants):
            raise ArithmeticError("sampled count exceeds the int64 count range")
        samples = survivors + immigrants
        if sample_size is None:
            return int(samples)
        return np.asarray(samples, dtype=np.int64)

    def bridge_log_information(
        self,
        time: float,
        count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return ``log P(N_T in B | N_t=count)`` for finite ``B``."""

        current, terminal = self._validate_bridge_times(time, terminal_time)
        source = self._validate_exact_count(count, "count")
        allowed = self._validate_allowed_counts(allowed_counts)
        if not allowed:
            return -math.inf
        if current == terminal:
            return 0.0 if source in allowed else -math.inf
        elapsed = terminal - current
        work = math.fsum(min(source, destination) + 1 for destination in allowed)
        if work > _MAX_BRIDGE_WORK:
            raise ValueError(
                "finite-set bridge exceeds the exact-evaluation work limit of %d"
                % _MAX_BRIDGE_WORK
            )
        result = _logsumexp(
            tuple(
                self.transition_log_pmf(source, destination, elapsed)
                for destination in allowed
            )
        )
        if result > 0.0:
            raise ArithmeticError("bridge log information is positive")
        return result

    def bridge_information(
        self,
        time: float,
        count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return terminal finite-set probability with no epsilon floor."""

        log_information = self.bridge_log_information(
            time, count, terminal_time, allowed_counts
        )
        return (
            0.0
            if log_information == -math.inf
            else math.exp(log_information)
        )

    def _bridge_log_rate(
        self,
        base_rate: float,
        time: float,
        source: int,
        destination: int,
        terminal_time: float,
        allowed: FrozenSet[int],
    ) -> float:
        denominator = self.bridge_log_information(
            time, source, terminal_time, allowed
        )
        if denominator == -math.inf:
            raise UnreachableCountBridgeStateError(time, source)
        numerator = self.bridge_log_information(
            time, destination, terminal_time, allowed
        )
        if numerator == -math.inf or base_rate == 0.0:
            return -math.inf
        result = math.log(base_rate) + numerator - denominator
        if not math.isfinite(result):
            raise ArithmeticError("tilted log rate is not finite")
        return result

    @staticmethod
    def _exp_rate(log_rate: float) -> float:
        if log_rate == -math.inf:
            return 0.0
        if log_rate > _LOG_MAX_FLOAT:
            raise ArithmeticError("tilted rate exceeds floating-point range")
        rate = math.exp(log_rate)
        if rate == 0.0:
            raise ArithmeticError(
                "positive tilted rate underflowed; use the log-rate API"
            )
        return rate

    def bridge_birth_log_rate(
        self,
        time: float,
        count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return ``log(beta*h(t,n+1)/h(t,n))`` without flooring."""

        current, terminal = self._validate_bridge_times(time, terminal_time)
        if current == terminal:
            raise ValueError("tilted rates are defined only before terminal_time")
        source = self._validate_exact_count(count, "count")
        if source == _MAX_COUNT:
            raise ValueError("birth destination exceeds the int64 count range")
        allowed = self._validate_allowed_counts(allowed_counts)
        return self._bridge_log_rate(
            self._beta,
            current,
            source,
            source + 1,
            terminal,
            allowed,
        )

    def bridge_birth_rate(
        self,
        time: float,
        count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return exact Doob-tilted birth rate ``beta*h(n+1)/h(n)``."""

        return self._exp_rate(
            self.bridge_birth_log_rate(
                time, count, terminal_time, allowed_counts
            )
        )

    def bridge_death_log_rate(
        self,
        time: float,
        count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return ``log(delta*n*h(t,n-1)/h(t,n))`` without flooring."""

        current, terminal = self._validate_bridge_times(time, terminal_time)
        if current == terminal:
            raise ValueError("tilted rates are defined only before terminal_time")
        source = self._validate_exact_count(count, "count")
        allowed = self._validate_allowed_counts(allowed_counts)
        destination = source - 1 if source > 0 else source
        return self._bridge_log_rate(
            self._delta * source,
            current,
            source,
            destination,
            terminal,
            allowed,
        )

    def bridge_death_rate(
        self,
        time: float,
        count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return exact Doob-tilted death rate ``delta*n*h(n-1)/h(n)``."""

        return self._exp_rate(
            self.bridge_death_log_rate(
                time, count, terminal_time, allowed_counts
            )
        )

    def bridge_terminal_log_pmf(
        self,
        time: float,
        source_count: int,
        terminal_count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return the terminal count law conditioned on membership in ``B``."""

        current, terminal = self._validate_bridge_times(time, terminal_time)
        source = self._validate_exact_count(source_count, "source_count")
        destination = self._validate_exact_count(
            terminal_count, "terminal_count"
        )
        allowed = self._validate_allowed_counts(allowed_counts)
        denominator = self.bridge_log_information(
            current, source, terminal, allowed
        )
        if denominator == -math.inf:
            raise UnreachableCountBridgeStateError(current, source)
        if destination not in allowed:
            return -math.inf
        numerator = self.transition_log_pmf(
            source, destination, terminal - current
        )
        result = numerator - denominator
        if result > 0.0:
            raise ArithmeticError("bridge terminal log mass is positive")
        return result

    def bridge_terminal_pmf(
        self,
        time: float,
        source_count: int,
        terminal_count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return terminal conditional mass for one destination count."""

        log_probability = self.bridge_terminal_log_pmf(
            time,
            source_count,
            terminal_count,
            terminal_time,
            allowed_counts,
        )
        return 0.0 if log_probability == -math.inf else math.exp(log_probability)

    def bridge_transition_log_pmf(
        self,
        start_time: float,
        source_count: int,
        end_time: float,
        destination_count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return an exact finite-step bridge transition log mass.

        The value is
        ``log P_{s-t}(n,m) + log h(s,m) - log h(t,n)``.
        """

        start, terminal = self._validate_bridge_times(start_time, terminal_time)
        end, checked_terminal = self._validate_bridge_times(
            end_time, terminal_time
        )
        if checked_terminal != terminal:
            raise ArithmeticError("terminal time validation disagreed")
        if end < start:
            raise ValueError("end_time must not precede start_time")
        source = self._validate_exact_count(source_count, "source_count")
        destination = self._validate_exact_count(
            destination_count, "destination_count"
        )
        allowed = self._validate_allowed_counts(allowed_counts)
        denominator = self.bridge_log_information(
            start, source, terminal, allowed
        )
        if denominator == -math.inf:
            raise UnreachableCountBridgeStateError(start, source)
        transition = self.transition_log_pmf(source, destination, end - start)
        if transition == -math.inf:
            return -math.inf
        numerator = self.bridge_log_information(
            end, destination, terminal, allowed
        )
        if numerator == -math.inf:
            return -math.inf
        result = transition + numerator - denominator
        if result > 0.0:
            raise ArithmeticError("bridge transition log mass is positive")
        return result

    def bridge_transition_pmf(
        self,
        start_time: float,
        source_count: int,
        end_time: float,
        destination_count: int,
        terminal_time: float,
        allowed_counts: Collection[int],
    ) -> float:
        """Return exact finite-step bridge transition mass."""

        log_probability = self.bridge_transition_log_pmf(
            start_time,
            source_count,
            end_time,
            destination_count,
            terminal_time,
            allowed_counts,
        )
        return 0.0 if log_probability == -math.inf else math.exp(log_probability)


__all__ = [
    "CountMoments",
    "ImmigrationDeathOracle",
    "UnreachableCountBridgeStateError",
]
