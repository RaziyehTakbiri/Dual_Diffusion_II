"""Bounded exact bridge for unlabelled regional particle configurations.

This is a classical finite-state test oracle, not a proposed neural method,
not a novelty claim, and not the continuous-configuration theorem.  Its only
purpose is to make joint birth, death, migration, noisy observation, and Doob
conditioning identities exactly executable on a small state space.

A latent configuration is the count vector ``n = (n_0, ..., n_{R-1})`` of
indistinguishable particles in ``R`` regions, with the explicit hard cap
``sum(n) <= K``.  The homogeneous CTMC has

* immigration ``n -> n + e_r`` at rate ``beta[r]`` when ``sum(n) < K``;
* death ``n -> n - e_r`` at rate ``n[r] * delta[r]``; and
* migration ``n -> n - e_r + e_s`` at rate ``n[r] * M[r, s]``.

At terminal time, each particle in true region ``r`` is independently missed
with probability ``1-d[r]`` or produces one observed regional anchor ``o``
with probability ``d[r] * C[r, o]``.  ``C`` is row stochastic.  The observed
anchors are an unordered multiset represented by their regional count vector
``y``.  Thus the declared likelihood is the ordinary discrete mass
``g_y(n) = P(Y=y | N=n)``, including all multinomial coefficients induced by
indistinguishable anchors.  It is evaluated by exact log-domain convolution.

There is no clutter in this bounded oracle; adding it would change the
observation model and is outside this validation slice.  Matrix exponentials
and Doob transforms are exact up to floating-point error.  Exact zeros remain
zeros and no epsilon probability floor is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Dict, Iterator, Optional, Sequence, Tuple
import warnings

import numpy as np

from .conditional_bridge import (
    UnreachableObservationStateError,
    ZeroEvidenceError,
)
from .finite_state import (
    generator_from_off_diagonal,
    transition_matrix,
    validate_generator,
    validate_probability_vector,
)


CountVector = Tuple[int, ...]

_MAX_REGIONS = 32
_MAX_CARDINALITY = 64
_DEFAULT_MAX_STATES = 256
_MAX_STATES_HARD = 512
_MAX_SAMPLE_SIZE = 1_000_000
_MAX_SAMPLE_ENTRIES = 10_000_000
_MAX_SEED = int(np.iinfo(np.uint64).max)
_MAX_COUNT = int(np.iinfo(np.int64).max)


def _immutable_float_array(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _reject_boolean_entries(value: object, name: str) -> None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            object_array = np.asarray(value, dtype=object)
    except (TypeError, ValueError, Warning) as error:
        raise ValueError("%s must be a rectangular array" % name) from error
    if any(
        isinstance(entry, (bool, np.bool_)) for entry in object_array.flat
    ):
        raise TypeError("%s must not contain boolean entries" % name)


def _as_numeric_array(
    value: object,
    name: str,
    ndim: int,
    shape: Optional[Tuple[int, ...]] = None,
) -> np.ndarray:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            array = np.asarray(value)
    except (TypeError, ValueError, Warning) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    _reject_boolean_entries(value, name)
    if array.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if array.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = array.astype(float, copy=True)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s cannot be represented as floats" % name) from error
    if result.ndim != ndim:
        raise ValueError("%s must be %d-dimensional" % (name, ndim))
    if shape is not None and result.shape != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    if not np.all(np.isfinite(result)):
        raise ValueError("%s entries must be finite" % name)
    return result


def _nonnegative_array(
    value: object,
    name: str,
    ndim: int,
    shape: Optional[Tuple[int, ...]] = None,
) -> np.ndarray:
    array = _as_numeric_array(value, name, ndim, shape)
    if np.any(array < 0.0):
        raise ValueError("%s entries must be nonnegative" % name)
    return array


def _validate_integer(
    value: int,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError(
            "%s must lie between %d and %d" % (name, minimum, maximum)
        )
    return result


def _validate_time(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("%s must be finite and nonnegative" % name)
    return result


def _validate_seed(seed: Optional[int]) -> Optional[int]:
    if seed is None:
        return None
    return _validate_integer(seed, "seed", 0, _MAX_SEED)


def _validate_size(size: Optional[int]) -> Optional[int]:
    if size is None:
        return None
    return _validate_integer(size, "size", 1, _MAX_SAMPLE_SIZE)


def _logaddexp(first: float, second: float) -> float:
    if first == -math.inf:
        return second
    if second == -math.inf:
        return first
    maximum = max(first, second)
    return maximum + math.log1p(math.exp(-abs(first - second)))


def _logsumexp(values: Sequence[float]) -> float:
    if not values:
        return -math.inf
    maximum = max(values)
    if maximum == -math.inf:
        return -math.inf
    total = math.fsum(math.exp(value - maximum) for value in values)
    result = maximum + math.log(total)
    if not math.isfinite(result):
        raise ArithmeticError("log-sum-exp is outside floating-point range")
    return result


def _compositions(total: int, parts: int) -> Iterator[CountVector]:
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for remainder in _compositions(total - first, parts - 1):
            yield (first,) + remainder


def _normalised_exp(log_weights: np.ndarray, log_normalizer: float) -> np.ndarray:
    probabilities = np.zeros(log_weights.shape, dtype=float)
    finite = np.isfinite(log_weights)
    if np.any(finite):
        probabilities[finite] = np.exp(log_weights[finite] - log_normalizer)
        if np.any(probabilities[finite] == 0.0):
            raise ArithmeticError(
                "a mathematically positive normalized weight underflowed to zero"
            )
    total = float(probabilities.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ArithmeticError("log weights could not be normalized")
    probabilities /= total
    return probabilities


@dataclass(frozen=True)
class FiniteRegionBridge:
    """Exact endpoint-conditioned law on a bounded count-vector state space.

    ``log_evidence`` is the physical log probability of the unordered
    observation.  Ordinary evidence may underflow and is available through
    :attr:`evidence`.  All arrays are bytes-backed and cannot be made writeable.
    """

    log_evidence: float
    likelihood_log_scale: float
    observation_log_likelihood: np.ndarray
    log_backward_information: np.ndarray
    initial_marginal: np.ndarray
    conditional_initial: np.ndarray
    conditional_terminal: np.ndarray
    forward_transition: np.ndarray
    doob_transition: np.ndarray

    def __post_init__(self) -> None:
        for name in (
            "observation_log_likelihood",
            "log_backward_information",
            "initial_marginal",
            "conditional_initial",
            "conditional_terminal",
            "forward_transition",
            "doob_transition",
        ):
            _reject_boolean_entries(getattr(self, name), name)
        if isinstance(self.log_evidence, (bool, np.bool_)) or not isinstance(
            self.log_evidence, Real
        ):
            raise TypeError("log_evidence must be a real non-boolean number")
        log_evidence = float(self.log_evidence)
        if not math.isfinite(log_evidence) or log_evidence > 1.0e-12:
            raise ValueError("log_evidence must be finite and nonpositive")
        if isinstance(self.likelihood_log_scale, (bool, np.bool_)) or not isinstance(
            self.likelihood_log_scale, Real
        ):
            raise TypeError(
                "likelihood_log_scale must be a real non-boolean number"
            )
        log_scale = float(self.likelihood_log_scale)
        if not math.isfinite(log_scale) or log_scale > 1.0e-12:
            raise ValueError(
                "likelihood_log_scale must be finite and nonpositive"
            )

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                observation_log = np.asarray(
                    self.observation_log_likelihood, dtype=float
                )
                log_information = np.asarray(
                    self.log_backward_information, dtype=float
                )
        except (TypeError, ValueError, Warning) as error:
            raise ValueError(
                "log likelihood/information must be rectangular numeric vectors"
            ) from error
        initial_marginal = validate_probability_vector(self.initial_marginal)
        conditional_initial = validate_probability_vector(self.conditional_initial)
        state_count = conditional_initial.size
        if initial_marginal.size != state_count:
            raise ValueError("initial_marginal has wrong shape")
        conditional_terminal = validate_probability_vector(
            self.conditional_terminal, state_count, atol=1.0e-11
        )
        if observation_log.shape != (state_count,) or log_information.shape != (
            state_count,
        ):
            raise ValueError("log likelihood/information vectors have wrong shape")
        for array, name in (
            (observation_log, "observation_log_likelihood"),
            (log_information, "log_backward_information"),
        ):
            if np.any(np.isnan(array)) or np.any(array == math.inf):
                raise ValueError("%s may contain only finite values or -inf" % name)
            if np.any(array > 1.0e-12):
                raise ValueError("%s values must be nonpositive" % name)
        finite_observation = observation_log[np.isfinite(observation_log)]
        if finite_observation.size == 0:
            raise ValueError("observation_log_likelihood must have positive support")
        expected_scale = float(np.max(finite_observation))
        if not math.isclose(
            log_scale, expected_scale, rel_tol=0.0, abs_tol=1.0e-12
        ):
            raise ValueError(
                "likelihood_log_scale must equal the maximum finite log likelihood"
            )

        forward = self._validate_transition(
            self.forward_transition, state_count, "forward_transition"
        )
        doob = self._validate_transition(
            self.doob_transition, state_count, "doob_transition"
        )

        expected_log_information = np.full(state_count, -math.inf, dtype=float)
        expected_doob = np.zeros((state_count, state_count), dtype=float)
        for source in range(state_count):
            terms = []
            for destination in range(state_count):
                probability = forward[source, destination]
                if probability == 0.0 or observation_log[destination] == -math.inf:
                    continue
                terms.append(
                    math.log(probability) + observation_log[destination]
                )
            expected_log_information[source] = _logsumexp(terms)
            if expected_log_information[source] == -math.inf:
                expected_doob[source, source] = 1.0
                continue
            log_row = np.full(state_count, -math.inf, dtype=float)
            for destination in range(state_count):
                probability = forward[source, destination]
                if probability == 0.0 or observation_log[destination] == -math.inf:
                    continue
                log_row[destination] = (
                    math.log(probability)
                    + observation_log[destination]
                    - expected_log_information[source]
                )
            expected_doob[source] = _normalised_exp(log_row, 0.0)

        finite_information = np.isfinite(expected_log_information)
        if not np.array_equal(
            finite_information, np.isfinite(log_information)
        ) or not np.allclose(
            expected_log_information[finite_information],
            log_information[finite_information],
            atol=1.0e-11,
            rtol=1.0e-11,
        ):
            raise ValueError(
                "log_backward_information is inconsistent with forward and likelihood"
            )
        if not np.allclose(doob, expected_doob, atol=2.0e-11, rtol=2.0e-11):
            raise ValueError(
                "doob_transition is inconsistent with forward and likelihood"
            )

        log_initial = np.full(state_count, -math.inf, dtype=float)
        positive_initial = initial_marginal > 0.0
        log_initial[positive_initial] = np.log(initial_marginal[positive_initial])
        expected_log_evidence = _logsumexp(
            tuple(log_initial + expected_log_information)
        )
        if expected_log_evidence == -math.inf or not math.isclose(
            log_evidence,
            expected_log_evidence,
            rel_tol=1.0e-11,
            abs_tol=1.0e-11,
        ):
            raise ValueError(
                "log_evidence is inconsistent with initial, forward, and likelihood"
            )
        expected_conditional_initial = _normalised_exp(
            log_initial + expected_log_information, expected_log_evidence
        )
        if not np.allclose(
            conditional_initial,
            expected_conditional_initial,
            atol=2.0e-11,
            rtol=2.0e-11,
        ):
            raise ValueError("conditional_initial is inconsistent with Bayes' rule")

        recovered = conditional_initial @ doob
        if not np.allclose(
            recovered, conditional_terminal, atol=2.0e-11, rtol=2.0e-11
        ):
            raise ValueError(
                "conditional initial and Doob transition do not recover "
                "the conditional terminal law"
            )

        object.__setattr__(self, "log_evidence", min(log_evidence, 0.0))
        object.__setattr__(
            self, "likelihood_log_scale", min(expected_scale, 0.0)
        )
        for name, array in (
            ("observation_log_likelihood", observation_log),
            ("log_backward_information", log_information),
            ("initial_marginal", initial_marginal),
            ("conditional_initial", conditional_initial),
            ("conditional_terminal", conditional_terminal),
            ("forward_transition", forward),
            ("doob_transition", doob),
        ):
            object.__setattr__(self, name, _immutable_float_array(array))

    @staticmethod
    def _validate_transition(
        value: np.ndarray, state_count: int, name: str
    ) -> np.ndarray:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                matrix = np.asarray(value, dtype=float)
        except (TypeError, ValueError, Warning) as error:
            raise ValueError("%s must be a rectangular numeric matrix" % name) from error
        if matrix.shape != (state_count, state_count):
            raise ValueError("%s has wrong shape" % name)
        if not np.all(np.isfinite(matrix)) or np.any(matrix < 0.0):
            raise ValueError("%s must be finite and nonnegative" % name)
        if not np.allclose(
            matrix.sum(axis=1), 1.0, atol=1.0e-11, rtol=0.0
        ):
            raise ValueError("%s rows must sum to one" % name)
        return matrix.copy()

    @property
    def evidence(self) -> float:
        """Return ordinary evidence, possibly zero after IEEE underflow."""

        return math.exp(self.log_evidence)

    @property
    def scaled_observation_likelihood(self) -> np.ndarray:
        """Return ``exp(log g - max log g)`` as an immutable diagnostic."""

        result = np.zeros(self.observation_log_likelihood.shape, dtype=float)
        finite = np.isfinite(self.observation_log_likelihood)
        result[finite] = np.exp(
            self.observation_log_likelihood[finite] - self.likelihood_log_scale
        )
        return _immutable_float_array(result)


class FiniteRegionConfigurationBridgeOracle:
    """Bounded exact CTMC and unordered-observation bridge on region counts."""

    def __init__(
        self,
        birth_rates: object,
        death_rates: object,
        migration_rates: object,
        detection_probability: object,
        confusion_matrix: object,
        max_cardinality: int,
        max_states: int = _DEFAULT_MAX_STATES,
    ) -> None:
        births = _nonnegative_array(birth_rates, "birth_rates", 1)
        region_count = births.size
        if region_count == 0 or region_count > _MAX_REGIONS:
            raise ValueError(
                "region count must lie between one and %d" % _MAX_REGIONS
            )
        shape = (region_count,)
        deaths = _nonnegative_array(death_rates, "death_rates", 1, shape)
        migration = _nonnegative_array(
            migration_rates,
            "migration_rates",
            2,
            (region_count, region_count),
        )
        if np.any(np.diag(migration) != 0.0):
            raise ValueError("migration_rates diagonal must be exactly zero")
        detection = _as_numeric_array(
            detection_probability, "detection_probability", 1, shape
        )
        if np.any(detection < 0.0) or np.any(detection > 1.0):
            raise ValueError("detection probabilities must lie in [0, 1]")
        confusion = _nonnegative_array(
            confusion_matrix,
            "confusion_matrix",
            2,
            (region_count, region_count),
        )
        if not np.allclose(
            confusion.sum(axis=1), 1.0, atol=1.0e-12, rtol=0.0
        ):
            raise ValueError("confusion_matrix rows must sum to one")
        # Canonicalise only row-sum roundoff accepted by the validation above;
        # this preserves exact stochastic normalization in subsequent DP steps.
        confusion /= confusion.sum(axis=1, keepdims=True)

        cardinality_cap = _validate_integer(
            max_cardinality, "max_cardinality", 0, _MAX_CARDINALITY
        )
        state_limit = _validate_integer(
            max_states, "max_states", 1, _MAX_STATES_HARD
        )
        state_count = math.comb(cardinality_cap + region_count, region_count)
        if state_count > state_limit:
            raise ValueError(
                "count-vector state space has %d states, exceeding max_states=%d"
                % (state_count, state_limit)
            )

        self._region_count = int(region_count)
        self._max_cardinality = cardinality_cap
        self._max_states = state_limit
        self._birth_rates = _immutable_float_array(births)
        self._death_rates = _immutable_float_array(deaths)
        self._migration_rates = _immutable_float_array(migration)
        self._detection_probability = _immutable_float_array(detection)
        self._confusion_matrix = _immutable_float_array(confusion)
        self._states = tuple(
            state
            for cardinality in range(cardinality_cap + 1)
            for state in _compositions(cardinality, region_count)
        )
        if len(self._states) != state_count:
            raise ArithmeticError("count-vector enumeration is incomplete")
        self._state_indices = {
            state: index for index, state in enumerate(self._states)
        }
        self._generator = _immutable_float_array(self._build_generator())
        self._positive_reachability = self._build_positive_reachability()

    @property
    def region_count(self) -> int:
        return self._region_count

    @property
    def max_cardinality(self) -> int:
        return self._max_cardinality

    @property
    def n_states(self) -> int:
        return len(self._states)

    @property
    def states(self) -> Tuple[CountVector, ...]:
        return self._states

    @property
    def birth_rates(self) -> np.ndarray:
        return self._birth_rates

    @property
    def death_rates(self) -> np.ndarray:
        return self._death_rates

    @property
    def migration_rates(self) -> np.ndarray:
        return self._migration_rates

    @property
    def detection_probability(self) -> np.ndarray:
        return self._detection_probability

    @property
    def confusion_matrix(self) -> np.ndarray:
        return self._confusion_matrix

    @property
    def generator(self) -> np.ndarray:
        return self._generator.copy()

    def _validate_count_vector(
        self, value: object, name: str, enforce_cap: bool
    ) -> CountVector:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                array = np.asarray(value)
        except (TypeError, ValueError, Warning) as error:
            raise ValueError("%s must be a finite count vector" % name) from error
        _reject_boolean_entries(value, name)
        if array.shape != (self._region_count,):
            raise ValueError(
                "%s must have shape (%d,)" % (name, self._region_count)
            )
        if array.dtype.kind == "b":
            raise TypeError("%s must not have boolean dtype" % name)
        if array.dtype.kind not in "iu":
            raise TypeError("%s entries must be integers" % name)
        counts = []
        total = 0
        for raw in array:
            count = int(raw)
            if count < 0 or count > _MAX_COUNT:
                raise ValueError("%s entries must be nonnegative int64 counts" % name)
            counts.append(count)
            total += count
        if enforce_cap and total > self._max_cardinality:
            raise ValueError(
                "%s cardinality exceeds max_cardinality=%d"
                % (name, self._max_cardinality)
            )
        return tuple(counts)

    def index_of(self, counts: object) -> int:
        state = self._validate_count_vector(counts, "counts", True)
        return self._state_indices[state]

    def _build_generator(self) -> np.ndarray:
        off_diagonal = np.zeros((self.n_states, self.n_states), dtype=float)
        for source_index, state in enumerate(self._states):
            cardinality = sum(state)
            if cardinality < self._max_cardinality:
                for region, rate in enumerate(self._birth_rates):
                    if rate == 0.0:
                        continue
                    destination = list(state)
                    destination[region] += 1
                    off_diagonal[
                        source_index, self._state_indices[tuple(destination)]
                    ] += rate

            for source_region, count in enumerate(state):
                if count == 0:
                    continue
                death_rate = float(count) * float(
                    self._death_rates[source_region]
                )
                if not math.isfinite(death_rate):
                    raise ValueError("death exit rate exceeds floating-point range")
                if death_rate > 0.0:
                    destination = list(state)
                    destination[source_region] -= 1
                    off_diagonal[
                        source_index, self._state_indices[tuple(destination)]
                    ] += death_rate

                for destination_region in range(self._region_count):
                    if destination_region == source_region:
                        continue
                    migration_rate = float(count) * float(
                        self._migration_rates[source_region, destination_region]
                    )
                    if not math.isfinite(migration_rate):
                        raise ValueError(
                            "migration exit rate exceeds floating-point range"
                        )
                    if migration_rate == 0.0:
                        continue
                    destination = list(state)
                    destination[source_region] -= 1
                    destination[destination_region] += 1
                    off_diagonal[
                        source_index, self._state_indices[tuple(destination)]
                    ] += migration_rate

        for row in off_diagonal:
            try:
                total = math.fsum(float(value) for value in row)
            except OverflowError as error:
                raise ValueError("total CTMC exit rate exceeds floating-point range") from error
            if not math.isfinite(total):
                raise ValueError("total CTMC exit rate exceeds floating-point range")
        generator = generator_from_off_diagonal(off_diagonal)
        try:
            return validate_generator(generator)
        except ValueError as error:
            raise ValueError(
                "rates are outside the numerically stable finite-oracle regime"
            ) from error

    def _build_positive_reachability(self) -> np.ndarray:
        """Return graph reachability implied by strictly positive CTMC rates."""

        adjacency = []
        for source in range(self.n_states):
            adjacency.append(
                tuple(
                    int(destination)
                    for destination in np.flatnonzero(
                        (self._generator[source] > 0.0)
                        & (np.arange(self.n_states) != source)
                    )
                )
            )
        reachability = np.zeros((self.n_states, self.n_states), dtype=bool)
        for source in range(self.n_states):
            stack = [source]
            reachability[source, source] = True
            while stack:
                current = stack.pop()
                for destination in adjacency[current]:
                    if reachability[source, destination]:
                        continue
                    reachability[source, destination] = True
                    stack.append(destination)
        return reachability

    def forward_transition(self, elapsed_time: float) -> np.ndarray:
        elapsed = _validate_time(elapsed_time, "elapsed_time")
        maximum_rate = float(np.max(np.abs(self._generator)))
        if elapsed > 0.0 and maximum_rate > float(np.finfo(float).max) / elapsed:
            raise ArithmeticError("elapsed_time times generator is not representable")
        if elapsed > 0.0 and maximum_rate > 0.0 and elapsed * maximum_rate == 0.0:
            raise ArithmeticError("elapsed_time times generator underflowed to zero")
        transition = transition_matrix(self._generator, elapsed)
        structural_support = (
            np.eye(self.n_states, dtype=bool)
            if elapsed == 0.0
            else self._positive_reachability
        )
        spurious = transition[~structural_support]
        if spurious.size and float(np.max(spurious)) > 1.0e-12:
            raise ArithmeticError(
                "matrix exponential placed material mass outside CTMC graph support"
            )
        transition[~structural_support] = 0.0
        row_mass = transition.sum(axis=1, keepdims=True)
        if np.any(row_mass <= 0.0) or not np.all(np.isfinite(row_mass)):
            raise ArithmeticError(
                "structural-zero projection removed all transition row mass"
            )
        transition /= row_mass
        return transition

    def observation_log_probability(
        self, terminal_counts: object, observed_counts: object
    ) -> float:
        """Return ``log P(Y=y | N=n)`` for unordered regional counts."""

        terminal = self._validate_count_vector(
            terminal_counts, "terminal_counts", True
        )
        observed = self._validate_count_vector(
            observed_counts, "observed_counts", False
        )
        if sum(observed) > sum(terminal):
            return -math.inf

        zero = (0,) * self._region_count
        dynamic: Dict[CountVector, float] = {zero: 0.0}
        for true_region, particle_count in enumerate(terminal):
            detection = self._detection_probability[true_region]
            log_miss = (
                math.log1p(-detection) if detection < 1.0 else -math.inf
            )
            log_detect = math.log(detection) if detection > 0.0 else -math.inf
            outcome_logs = []
            for observed_region in range(self._region_count):
                confusion = self._confusion_matrix[true_region, observed_region]
                if log_detect == -math.inf or confusion == 0.0:
                    outcome_logs.append(-math.inf)
                else:
                    outcome_logs.append(log_detect + math.log(confusion))

            for _ in range(particle_count):
                updated: Dict[CountVector, float] = {}
                for partial, log_prefix in dynamic.items():
                    if log_miss != -math.inf:
                        updated[partial] = _logaddexp(
                            updated.get(partial, -math.inf), log_prefix + log_miss
                        )
                    for observed_region, log_outcome in enumerate(outcome_logs):
                        if log_outcome == -math.inf:
                            continue
                        if partial[observed_region] >= observed[observed_region]:
                            continue
                        destination = list(partial)
                        destination[observed_region] += 1
                        destination_tuple = tuple(destination)
                        updated[destination_tuple] = _logaddexp(
                            updated.get(destination_tuple, -math.inf),
                            log_prefix + log_outcome,
                        )
                dynamic = updated
                if not dynamic:
                    return -math.inf
        result = dynamic.get(observed, -math.inf)
        if result > 1.0e-12:
            raise ArithmeticError("observation log probability became positive")
        return min(result, 0.0)

    def observation_probability(
        self, terminal_counts: object, observed_counts: object
    ) -> float:
        """Return ordinary observation mass, possibly zero after underflow."""

        log_probability = self.observation_log_probability(
            terminal_counts, observed_counts
        )
        if log_probability == -math.inf:
            return 0.0
        return math.exp(log_probability)

    def observation_log_likelihood(self, observed_counts: object) -> np.ndarray:
        """Return the log likelihood over every terminal count-vector state."""

        observed = self._validate_count_vector(
            observed_counts, "observed_counts", False
        )
        return np.asarray(
            [
                self.observation_log_probability(state, observed)
                for state in self._states
            ],
            dtype=float,
        )

    def observation_likelihood(self, observed_counts: object) -> np.ndarray:
        """Return ordinary likelihood masses over terminal states."""

        log_likelihood = self.observation_log_likelihood(observed_counts)
        likelihood = np.zeros(log_likelihood.shape, dtype=float)
        finite = np.isfinite(log_likelihood)
        likelihood[finite] = np.exp(log_likelihood[finite])
        return likelihood

    @staticmethod
    def _log_matvec(
        transition: np.ndarray, log_terminal_weight: np.ndarray
    ) -> np.ndarray:
        log_information = np.full(transition.shape[0], -math.inf, dtype=float)
        for source in range(transition.shape[0]):
            terms = []
            for destination in range(transition.shape[1]):
                probability = transition[source, destination]
                log_weight = log_terminal_weight[destination]
                if probability == 0.0 or log_weight == -math.inf:
                    continue
                terms.append(math.log(probability) + log_weight)
            value = _logsumexp(terms)
            if value > 1.0e-10:
                raise ArithmeticError("backward log information became positive")
            log_information[source] = min(value, 0.0)
        return log_information

    def _checked_log_matvec(
        self,
        transition: np.ndarray,
        log_terminal_weight: np.ndarray,
        elapsed_time: float,
    ) -> np.ndarray:
        """Evaluate log information and detect positive paths lost to underflow."""

        log_information = self._log_matvec(transition, log_terminal_weight)
        terminal_support = np.isfinite(log_terminal_weight)
        if elapsed_time == 0.0:
            expected_pairs = np.eye(self.n_states, dtype=bool)[
                :, terminal_support
            ]
        elif np.any(terminal_support):
            expected_pairs = self._positive_reachability[:, terminal_support]
        else:
            expected_pairs = np.zeros((self.n_states, 0), dtype=bool)
        represented_pairs = transition[:, terminal_support] > 0.0
        if np.any(represented_pairs & ~expected_pairs):
            raise ArithmeticError(
                "matrix exponential violated an exact CTMC structural zero"
            )
        if np.any(expected_pairs & ~represented_pairs):
            raise ArithmeticError(
                "a mathematically positive CTMC transition/evidence path "
                "underflowed in the matrix exponential"
            )
        return log_information

    @staticmethod
    def _doob_transition(
        transition: np.ndarray,
        log_terminal_weight: np.ndarray,
        unreachable_policy: str,
        log_information: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if unreachable_policy not in ("identity", "raise"):
            raise ValueError("unreachable_policy must be 'identity' or 'raise'")
        if log_information is None:
            log_information = FiniteRegionConfigurationBridgeOracle._log_matvec(
                transition, log_terminal_weight
            )
        zero_indices = tuple(
            int(index)
            for index in np.flatnonzero(log_information == -math.inf)
        )
        if zero_indices and unreachable_policy == "raise":
            raise UnreachableObservationStateError(zero_indices)

        transformed = np.zeros_like(transition)
        zero_set = set(zero_indices)
        for source in range(transition.shape[0]):
            if source in zero_set:
                transformed[source, source] = 1.0
                continue
            log_row = np.full(transition.shape[1], -math.inf, dtype=float)
            support = (transition[source] > 0.0) & np.isfinite(
                log_terminal_weight
            )
            log_row[support] = (
                np.log(transition[source, support])
                + log_terminal_weight[support]
                - log_information[source]
            )
            transformed[source] = _normalised_exp(log_row, 0.0)
        if np.any(transformed < 0.0) or not np.allclose(
            transformed.sum(axis=1), 1.0, atol=1.0e-11, rtol=0.0
        ):
            raise ArithmeticError("Doob transition is not stochastic")
        return transformed, log_information

    @staticmethod
    def _validate_interval(
        time: float,
        terminal_time: float,
        future_time: Optional[float] = None,
    ) -> Tuple[float, float, Optional[float]]:
        current = _validate_time(time, "time")
        terminal = _validate_time(terminal_time, "terminal_time")
        if current > terminal:
            raise ValueError("time must not exceed terminal_time")
        if future_time is None:
            return current, terminal, None
        future = _validate_time(future_time, "future_time")
        if future < current or future > terminal:
            raise ValueError(
                "future_time must lie between time and terminal_time"
            )
        return current, terminal, future

    def bridge_transition(
        self,
        time: float,
        future_time: float,
        terminal_time: float,
        observed_counts: object,
        unreachable_policy: str = "identity",
    ) -> np.ndarray:
        """Return the exact finite-step Doob transition for all source states."""

        if unreachable_policy not in ("identity", "raise"):
            raise ValueError("unreachable_policy must be 'identity' or 'raise'")
        current, terminal, future = self._validate_interval(
            time, terminal_time, future_time
        )
        assert future is not None
        log_likelihood = self.observation_log_likelihood(observed_counts)
        future_to_terminal = self.forward_transition(terminal - future)
        log_future_information = self._checked_log_matvec(
            future_to_terminal, log_likelihood, terminal - future
        )
        current_to_future = self.forward_transition(future - current)
        log_current_information = self._checked_log_matvec(
            current_to_future, log_future_information, future - current
        )
        transformed, _ = self._doob_transition(
            current_to_future,
            log_future_information,
            unreachable_policy,
            log_current_information,
        )
        return transformed

    def bridge_generator(
        self,
        time: float,
        terminal_time: float,
        observed_counts: object,
        unreachable_policy: str = "raise",
    ) -> np.ndarray:
        """Return the instantaneous Doob generator strictly before terminal time."""

        current, terminal, _ = self._validate_interval(time, terminal_time)
        if current >= terminal:
            raise ValueError("bridge_generator is defined only before terminal_time")
        if unreachable_policy not in ("identity", "raise"):
            raise ValueError("unreachable_policy must be 'identity' or 'raise'")
        log_likelihood = self.observation_log_likelihood(observed_counts)
        log_information = self._checked_log_matvec(
            self.forward_transition(terminal - current),
            log_likelihood,
            terminal - current,
        )
        zero_indices = tuple(
            int(index)
            for index in np.flatnonzero(log_information == -math.inf)
        )
        if zero_indices and unreachable_policy == "raise":
            raise UnreachableObservationStateError(zero_indices)

        off_diagonal = np.zeros_like(self._generator)
        zero_set = set(zero_indices)
        for source in range(self.n_states):
            if source in zero_set:
                continue
            for destination in range(self.n_states):
                rate = self._generator[source, destination]
                if source == destination or rate == 0.0:
                    continue
                if log_information[destination] == -math.inf:
                    continue
                log_rate = (
                    math.log(rate)
                    + log_information[destination]
                    - log_information[source]
                )
                if log_rate > math.log(float(np.finfo(float).max)):
                    raise ArithmeticError("Doob rate exceeds floating-point range")
                tilted_rate = math.exp(log_rate)
                if tilted_rate == 0.0:
                    raise ArithmeticError("positive Doob rate underflowed to zero")
                off_diagonal[source, destination] = tilted_rate
        for row in off_diagonal:
            try:
                total = math.fsum(float(value) for value in row)
            except OverflowError as error:
                raise ArithmeticError(
                    "total Doob exit rate exceeds floating-point range"
                ) from error
            if not math.isfinite(total):
                raise ArithmeticError(
                    "total Doob exit rate exceeds floating-point range"
                )
        tilted_generator = generator_from_off_diagonal(off_diagonal)
        try:
            return validate_generator(tilted_generator)
        except ValueError as error:
            raise ArithmeticError(
                "Doob generator is numerically nonconservative at this scale"
            ) from error

    def condition(
        self,
        initial_marginal: np.ndarray,
        time: float,
        terminal_time: float,
        observed_counts: object,
        unreachable_policy: str = "identity",
    ) -> FiniteRegionBridge:
        """Condition endpoints on the noisy unordered terminal observation."""

        current, terminal, _ = self._validate_interval(time, terminal_time)
        if unreachable_policy not in ("identity", "raise"):
            raise ValueError("unreachable_policy must be 'identity' or 'raise'")
        initial = validate_probability_vector(initial_marginal, self.n_states)
        log_likelihood = self.observation_log_likelihood(observed_counts)
        if not np.any(np.isfinite(log_likelihood)):
            raise ZeroEvidenceError(
                "terminal observation has zero support in the capped state space"
            )
        forward = self.forward_transition(terminal - current)
        log_information = self._checked_log_matvec(
            forward, log_likelihood, terminal - current
        )
        doob, log_information = self._doob_transition(
            forward,
            log_likelihood,
            unreachable_policy,
            log_information,
        )

        log_initial = np.full(initial.shape, -math.inf, dtype=float)
        positive_initial = initial > 0.0
        log_initial[positive_initial] = np.log(initial[positive_initial])
        log_evidence = _logsumexp(tuple(log_initial + log_information))
        if log_evidence == -math.inf:
            raise ZeroEvidenceError(
                "terminal observation has zero evidence under the forward law"
            )
        if log_evidence > 1.0e-10:
            raise ArithmeticError("observation log evidence became positive")
        conditional_initial = _normalised_exp(
            log_initial + log_information, log_evidence
        )

        log_forward_terminal = np.full(self.n_states, -math.inf, dtype=float)
        for destination in range(self.n_states):
            terms = []
            for source in range(self.n_states):
                probability = forward[source, destination]
                if initial[source] == 0.0 or probability == 0.0:
                    continue
                terms.append(math.log(initial[source]) + math.log(probability))
            log_forward_terminal[destination] = _logsumexp(terms)
        conditional_terminal = _normalised_exp(
            log_forward_terminal + log_likelihood, log_evidence
        )
        recovered = conditional_initial @ doob
        if not np.allclose(
            recovered, conditional_terminal, atol=2.0e-11, rtol=2.0e-11
        ):
            raise ArithmeticError(
                "conditional endpoint laws disagree with the Doob transition"
            )
        finite_likelihood = log_likelihood[np.isfinite(log_likelihood)]
        likelihood_log_scale = float(np.max(finite_likelihood))
        return FiniteRegionBridge(
            log_evidence=min(log_evidence, 0.0),
            likelihood_log_scale=min(likelihood_log_scale, 0.0),
            observation_log_likelihood=log_likelihood,
            log_backward_information=log_information,
            initial_marginal=initial,
            conditional_initial=conditional_initial,
            conditional_terminal=conditional_terminal,
            forward_transition=forward,
            doob_transition=doob,
        )

    def sample_bridge_step(
        self,
        source_counts: object,
        time: float,
        future_time: float,
        terminal_time: float,
        observed_counts: object,
        seed: Optional[int] = None,
        size: Optional[int] = None,
    ) -> np.ndarray:
        """Sample an exact conditional finite step from one reachable state."""

        current, terminal, future = self._validate_interval(
            time, terminal_time, future_time
        )
        assert future is not None
        source_index = self.index_of(source_counts)
        validated_seed = _validate_seed(seed)
        validated_size = _validate_size(size)
        draw_count = 1 if validated_size is None else validated_size
        if draw_count * self._region_count > _MAX_SAMPLE_ENTRIES:
            raise ValueError("requested samples exceed the oracle memory limit")
        log_likelihood = self.observation_log_likelihood(observed_counts)
        source_log_information = self._checked_log_matvec(
            self.forward_transition(terminal - current),
            log_likelihood,
            terminal - current,
        )[source_index]
        if source_log_information == -math.inf:
            raise UnreachableObservationStateError((source_index,))
        transition = self.bridge_transition(
            current,
            future,
            terminal,
            observed_counts,
            unreachable_policy="identity",
        )
        generator = np.random.default_rng(validated_seed)
        selected = generator.choice(
            self.n_states, size=draw_count, p=transition[source_index]
        )
        samples = np.asarray(
            [self._states[int(index)] for index in selected], dtype=np.int64
        )
        if validated_size is None:
            return samples[0]
        return samples


__all__ = [
    "CountVector",
    "FiniteRegionBridge",
    "FiniteRegionConfigurationBridgeOracle",
]
