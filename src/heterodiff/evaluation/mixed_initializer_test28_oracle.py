"""Independent known-law oracle for the CP50 / Formal-Test-28 initializer gate.

This module contains only closed-form fixture definitions and deterministic
evaluation utilities.  It deliberately does not import the production
initializer, score composer, counter-keyed source layer, or any learned model.
The primary fixtures separate:

* an exactly enumerable multiplicative-factor target (``T28-A0-H``);
* an exact-rational-quadratic cap-one mixed target (``T28-M1-Q``); and
* an exact-rational-quadratic cap-two heterogeneous target (``T28-M2-Q``).

The Q fixtures exercise the production contract ``weight = exp(q)`` with an
exact rational score ``q``.  Their analytic laws are ideal real-coordinate
laws.  The represented-coordinate helpers separately expose (a) the exact
rational score induced by a binary64 coordinate, (b) its binary64 conversion,
and (c) a direct binary64 formula evaluation.  Those three objects must not be
silently identified.

The continuous helpers evaluate densities and CDFs under the mathematical
Lebesgue laws.  Empirical diagnostics use finite categorical total variation,
Kolmogorov--Smirnov/DKW bounds, binomial intervals, and bounded SIR weight
summaries.  No function in this module interprets a finite empirical measure
as having finite TV or KL distance from a continuous target.

SciPy quadrature error values are numerical estimates, not rigorous interval
certificates.  The exact A0-H rational-factor lane is not a claim that the
composer represents the logarithms of its factors.  Seeded PRNG output,
backend uniformity, IID behavior, learned-potential correctness, cross-domain
generality, and sampler admission are all outside this oracle.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple

from scipy.integrate import quad
from scipy.special import betaincinv

CP50_TEST28_ORACLE_SCHEMA_VERSION = "cp50-test28-mixed-initializer-oracle-v1"
CP50_TEST28_ORACLE_SCOPE = (
    "independent-closed-form-a0-h-m1-q-m2-q-known-law-fixtures;"
    "exact-a0-h-rational-factor-target;exact-rational-q-mixed-gaussian-"
    "composer-lanes;ideal-real-laws-separated-from-represented-coordinate-"
    "exact-rational-and-binary64-score-evaluation;m1-analytic-cdf-and-"
    "quadrature;m2-analytic-count-type-and-projection-moments;"
    "finite-categorical-tv-ks-dkw-binomial-exhaustion-and-ess-utilities;"
    "not-production-initializer-not-rng-law-not-continuous-tv-or-kl-"
    "not-test28-closure-not-scientific-or-generality-evidence"
)

CP50_TEST28_FAMILYWISE_ALPHA = 0.01
CP50_TEST28_GATE_SLOTS = 32
CP50_TEST28_PER_GATE_ALPHA = CP50_TEST28_FAMILYWISE_ALPHA / CP50_TEST28_GATE_SLOTS

_MAX_CATEGORIES = 256
_MAX_SAMPLES = 1_000_000
_MAX_PARTICLES = 1_000_000
_MAX_REJECTION_ATTEMPTS = 1_000_000
_MAX_BINOMIAL_TRIALS = 10_000_000
_MAX_ABSOLUTE_COORDINATE = 1.0e6
_MIN_QUADRATURE_TOLERANCE = 1.0e-15
_MAX_QUADRATURE_TOLERANCE = 1.0e-4
_MIN_QUADRATURE_LIMIT = 32
_MAX_QUADRATURE_LIMIT = 4_096
_DEFAULT_QUADRATURE_ABSOLUTE_TOLERANCE = 1.0e-12
_DEFAULT_QUADRATURE_RELATIVE_TOLERANCE = 1.0e-12
_DEFAULT_QUADRATURE_LIMIT = 256
_SQRT_TWO_PI = math.sqrt(2.0 * math.pi)

_M1_CONTINUOUS_INTEGRATED_WEIGHT = math.sqrt(2.0 / 3.0)
_M1_CONTINUOUS_VARIANCE = 2.0 / 3.0
_M2_TYPE1_INTEGRATED_WEIGHT = math.sqrt(2.0 / 3.0)
_M2_TYPE2_INTEGRATED_WEIGHT = math.sqrt(3.0 / 5.0)
_M2_TYPE1_VARIANCE = 2.0 / 3.0
_M2_TYPE2_VARIANCES = (4.0 / 5.0, 3.0 / 4.0)


def _exact_integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < minimum or value > maximum:
        raise ValueError("%s must lie between %d and %d" % (name, minimum, maximum))
    return value


def _exact_float(
    value: object,
    *,
    name: str,
    finite: bool = True,
) -> float:
    if type(value) is not float:
        raise TypeError(name + " must be an exact built-in float")
    if math.isnan(value):
        raise ValueError(name + " must not be NaN")
    if finite and not math.isfinite(value):
        raise ValueError(name + " must be finite")
    return value


def _probability(
    value: object,
    *,
    name: str,
    strictly_inside: bool = False,
) -> float:
    result = _exact_float(value, name=name)
    if strictly_inside:
        if not 0.0 < result < 1.0:
            raise ValueError(name + " must lie strictly inside (0, 1)")
    elif result < 0.0 or result > 1.0:
        raise ValueError(name + " must lie in [0, 1]")
    return result


def _positive_float(value: object, *, name: str) -> float:
    result = _exact_float(value, name=name)
    if result <= 0.0:
        raise ValueError(name + " must be strictly positive")
    return result


def _coordinate(value: object, *, name: str) -> float:
    result = _exact_float(value, name=name)
    if abs(result) > _MAX_ABSOLUTE_COORDINATE:
        raise ValueError(name + " exceeds the frozen coordinate magnitude bound")
    return result


def _canonical_score_coordinate(value: object, *, name: str) -> float:
    result = _coordinate(value, name=name)
    if result == 0.0 and math.copysign(1.0, result) < 0.0:
        raise ValueError(name + " must use canonical positive zero")
    return result


def _exact_tuple(
    value: object,
    *,
    name: str,
    maximum: int,
    minimum: int = 0,
) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(
            "%s must contain between %d and %d values" % (name, minimum, maximum)
        )
    return value


def _alpha(value: object, *, name: str = "alpha") -> float:
    return _probability(value, name=name, strictly_inside=True)


def _quadrature_controls(
    absolute_tolerance: object,
    relative_tolerance: object,
    subdivision_limit: object,
) -> Tuple[float, float, int]:
    absolute = _positive_float(absolute_tolerance, name="absolute_tolerance")
    relative = _positive_float(relative_tolerance, name="relative_tolerance")
    for name, value in (
        ("absolute_tolerance", absolute),
        ("relative_tolerance", relative),
    ):
        if value < _MIN_QUADRATURE_TOLERANCE:
            raise ValueError(name + " is below the frozen reliability floor")
        if value > _MAX_QUADRATURE_TOLERANCE:
            raise ValueError(name + " exceeds the oracle accuracy ceiling")
    limit = _exact_integer(
        subdivision_limit,
        name="subdivision_limit",
        minimum=_MIN_QUADRATURE_LIMIT,
        maximum=_MAX_QUADRATURE_LIMIT,
    )
    return absolute, relative, limit


def _probability_table(
    values: object,
    *,
    name: str,
) -> Tuple[float, ...]:
    items = _exact_tuple(
        values,
        name=name,
        minimum=1,
        maximum=_MAX_CATEGORIES,
    )
    if all(type(item) is Fraction for item in items):
        if any(item < 0 for item in items):
            raise ValueError(name + " must be nonnegative")
        if sum(items, Fraction(0, 1)) != 1:
            raise ValueError(name + " must normalize exactly")
        return tuple(float(item) for item in items)
    if not all(type(item) is float for item in items):
        raise TypeError(name + " entries must be all Fractions or all floats")
    checked = tuple(
        _probability(item, name="%s[%d]" % (name, index))
        for index, item in enumerate(items)
    )
    total = math.fsum(checked)
    tolerance = 64.0 * sys.float_info.epsilon * len(checked)
    if abs(total - 1.0) > tolerance:
        raise ValueError(name + " must normalize within the float64 audit bound")
    return checked


def _count_tuple(values: object, *, name: str) -> Tuple[int, ...]:
    items = _exact_tuple(
        values,
        name=name,
        minimum=1,
        maximum=_MAX_CATEGORIES,
    )
    return tuple(
        _exact_integer(
            item,
            name="%s[%d]" % (name, index),
            minimum=0,
            maximum=_MAX_BINOMIAL_TRIALS,
        )
        for index, item in enumerate(items)
    )


@dataclass(frozen=True)
class AtomicA0Fixture:
    """Exact six-state all-atomic multiplicative-factor fixture."""

    fixture_id: str
    state_labels: Tuple[str, ...]
    base_probabilities: Tuple[Fraction, ...]
    tilt_values: Tuple[Fraction, ...]
    unnormalized_target_masses: Tuple[Fraction, ...]
    target_numerators: Tuple[int, ...]
    target_denominator: int
    target_probabilities: Tuple[Fraction, ...]
    normalizer: Fraction
    rejection_envelope: Fraction
    rejection_acceptance_probability: Fraction

    def __post_init__(self) -> None:
        if type(self.fixture_id) is not str or self.fixture_id != "T28-A0-H":
            raise ValueError("A0 fixture identifier differs")
        labels = _exact_tuple(
            self.state_labels,
            name="state_labels",
            minimum=6,
            maximum=6,
        )
        if labels != ("empty", "a", "b", "aa", "ab", "bb"):
            raise ValueError("A0 state order differs")
        if not all(type(label) is str for label in labels):
            raise TypeError("A0 state labels must be exact strings")
        for name, values in (
            ("base_probabilities", self.base_probabilities),
            ("tilt_values", self.tilt_values),
            ("unnormalized_target_masses", self.unnormalized_target_masses),
            ("target_probabilities", self.target_probabilities),
        ):
            items = _exact_tuple(values, name=name, minimum=6, maximum=6)
            if not all(type(item) is Fraction for item in items):
                raise TypeError(name + " must contain exact Fractions")
        if sum(self.base_probabilities, Fraction(0, 1)) != 1:
            raise ValueError("A0 base probabilities do not normalize")
        expected_masses = tuple(
            base * tilt for base, tilt in zip(self.base_probabilities, self.tilt_values)
        )
        if self.unnormalized_target_masses != expected_masses:
            raise ValueError("A0 unnormalized target masses differ")
        if type(self.normalizer) is not Fraction:
            raise TypeError("A0 normalizer must be an exact Fraction")
        if self.normalizer != sum(expected_masses, Fraction(0, 1)):
            raise ValueError("A0 normalizer differs")
        numerators = _exact_tuple(
            self.target_numerators,
            name="target_numerators",
            minimum=6,
            maximum=6,
        )
        if not all(type(value) is int and value > 0 for value in numerators):
            raise TypeError("A0 target numerators must be positive exact integers")
        if type(self.target_denominator) is not int:
            raise TypeError("A0 target denominator must be an exact integer")
        expected_probabilities = tuple(
            mass / self.normalizer for mass in expected_masses
        )
        if self.target_probabilities != expected_probabilities:
            raise ValueError("A0 target probabilities differ")
        if self.target_probabilities != tuple(
            Fraction(value, self.target_denominator) for value in numerators
        ):
            raise ValueError("A0 numerator representation differs")
        if sum(self.target_probabilities, Fraction(0, 1)) != 1:
            raise ValueError("A0 target probabilities do not normalize")
        if type(self.rejection_envelope) is not Fraction:
            raise TypeError("A0 rejection envelope must be an exact Fraction")
        if self.rejection_envelope < max(self.tilt_values):
            raise ValueError("A0 rejection envelope is invalid")
        expected_acceptance = self.normalizer / self.rejection_envelope
        if type(self.rejection_acceptance_probability) is not Fraction:
            raise TypeError(
                "A0 rejection acceptance probability must be an exact Fraction"
            )
        if self.rejection_acceptance_probability != expected_acceptance:
            raise ValueError("A0 rejection acceptance probability differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("AtomicA0Fixture cannot be subclassed")


@dataclass(frozen=True)
class MixedM1Fixture:
    """Cap-one atom/continuous exact-rational-quadratic fixture."""

    fixture_id: str
    category_labels: Tuple[str, ...]
    base_category_probabilities: Tuple[Fraction, ...]
    ideal_score_formula: str
    represented_coordinate_score_policy: str
    continuous_quadratic_coefficient: Fraction
    score_upper_bound: Fraction
    ideal_weight_envelope: Fraction
    continuous_integrated_weight: float
    unnormalized_target_category_masses: Tuple[float, ...]
    target_normalizer: float
    target_category_probabilities: Tuple[float, ...]
    continuous_target_variance: Fraction
    rejection_acceptance_probability: float

    def __post_init__(self) -> None:
        if type(self.fixture_id) is not str or self.fixture_id != "T28-M1-Q":
            raise ValueError("M1 fixture identifier differs")
        if self.category_labels != ("empty", "atomic-a", "continuous-b"):
            raise ValueError("M1 category order differs")
        if type(self.category_labels) is not tuple or not all(
            type(label) is str for label in self.category_labels
        ):
            raise TypeError("M1 category labels must be an exact tuple of strings")
        if self.base_category_probabilities != (
            Fraction(1, 2),
            Fraction(1, 5),
            Fraction(3, 10),
        ):
            raise ValueError("M1 base category probabilities differ")
        if type(self.base_category_probabilities) is not tuple or not all(
            type(value) is Fraction for value in self.base_category_probabilities
        ):
            raise TypeError("M1 base probabilities must be exact Fractions")
        if type(self.ideal_score_formula) is not str or self.ideal_score_formula != (
            "q(empty)=q(atomic-a)=0;" "q(continuous-b,x)=-x^2/4 for ideal real x"
        ):
            raise ValueError("M1 ideal score formula differs")
        if type(self.represented_coordinate_score_policy) is not str or (
            self.represented_coordinate_score_policy
        ) != (
            "Fraction.from_float(x);q=-x*x/4 exactly;"
            "binary64 formula and display remain separate"
        ):
            raise ValueError("M1 represented-coordinate score policy differs")
        for name in (
            "continuous_quadratic_coefficient",
            "score_upper_bound",
            "ideal_weight_envelope",
            "continuous_target_variance",
        ):
            if type(getattr(self, name)) is not Fraction:
                raise TypeError("M1 " + name + " must be an exact Fraction")
        if self.continuous_quadratic_coefficient != Fraction(1, 4):
            raise ValueError("M1 quadratic coefficient differs")
        if self.score_upper_bound != Fraction(0, 1):
            raise ValueError("M1 score upper bound differs")
        if self.ideal_weight_envelope != Fraction(1, 1):
            raise ValueError("M1 ideal weight envelope differs")
        expected_continuous = _M1_CONTINUOUS_INTEGRATED_WEIGHT
        integrated_weight = _exact_float(
            self.continuous_integrated_weight,
            name="M1 continuous_integrated_weight",
        )
        if integrated_weight.hex() != expected_continuous.hex():
            raise ValueError("M1 integrated continuous weight differs")
        expected_masses = (
            0.5,
            0.2,
            0.3 * expected_continuous,
        )
        masses = _exact_tuple(
            self.unnormalized_target_category_masses,
            name="M1 unnormalized_target_category_masses",
            minimum=3,
            maximum=3,
        )
        checked_masses = tuple(
            _exact_float(value, name="M1 target mass[%d]" % index)
            for index, value in enumerate(masses)
        )
        actual_mass_hex = tuple(value.hex() for value in checked_masses)
        if actual_mass_hex != tuple(value.hex() for value in expected_masses):
            raise ValueError("M1 target category masses differ")
        expected_normalizer = math.fsum(expected_masses)
        target_normalizer = _exact_float(
            self.target_normalizer,
            name="M1 target_normalizer",
        )
        if target_normalizer.hex() != expected_normalizer.hex():
            raise ValueError("M1 target normalizer differs")
        expected_probabilities = tuple(
            value / expected_normalizer for value in expected_masses
        )
        checked_probabilities = _probability_table(
            self.target_category_probabilities,
            name="M1 target_category_probabilities",
        )
        actual_probability_hex = tuple(value.hex() for value in checked_probabilities)
        if actual_probability_hex != tuple(
            value.hex() for value in expected_probabilities
        ):
            raise ValueError("M1 target category probabilities differ")
        if self.continuous_target_variance != Fraction(2, 3):
            raise ValueError("M1 target variance differs")
        expected_acceptance = expected_normalizer
        acceptance = _exact_float(
            self.rejection_acceptance_probability,
            name="M1 rejection_acceptance_probability",
        )
        if acceptance.hex() != expected_acceptance.hex():
            raise ValueError("M1 rejection acceptance probability differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("MixedM1Fixture cannot be subclassed")


@dataclass(frozen=True)
class MixedM2Fixture:
    """Cap-two heterogeneous exact-rational-quadratic fixture."""

    fixture_id: str
    count_labels: Tuple[str, ...]
    configuration_category_labels: Tuple[str, ...]
    type_labels: Tuple[str, ...]
    event_dimensions: Tuple[int, ...]
    base_count_probabilities: Tuple[Fraction, ...]
    base_configuration_category_probabilities: Tuple[Fraction, ...]
    base_type_probabilities: Tuple[Fraction, ...]
    count_score_penalties: Tuple[Fraction, ...]
    type_quadratic_coefficients: Tuple[Tuple[Fraction, ...], ...]
    ideal_score_formula: str
    represented_coordinate_score_policy: str
    score_upper_bound: Fraction
    ideal_weight_envelope: Fraction
    type_event_integrated_weights: Tuple[float, ...]
    mean_event_integrated_weight: float
    unnormalized_target_configuration_category_masses: Tuple[float, ...]
    target_configuration_category_probabilities: Tuple[float, ...]
    unnormalized_target_count_masses: Tuple[float, ...]
    target_normalizer: float
    target_count_probabilities: Tuple[float, ...]
    target_type_probabilities: Tuple[float, ...]
    type_coordinate_variances: Tuple[Tuple[Fraction, ...], ...]
    rejection_acceptance_probability: float

    def __post_init__(self) -> None:
        if type(self.fixture_id) is not str or self.fixture_id != "T28-M2-Q":
            raise ValueError("M2 fixture identifier differs")
        if self.count_labels != ("count-0", "count-1", "count-2"):
            raise ValueError("M2 count order differs")
        if type(self.count_labels) is not tuple or not all(
            type(label) is str for label in self.count_labels
        ):
            raise TypeError("M2 count labels must be an exact tuple of strings")
        if self.configuration_category_labels != (
            "empty",
            "one-type-1d",
            "one-type-2d",
            "two-type-1d",
            "one-each",
            "two-type-2d",
        ):
            raise ValueError("M2 configuration category order differs")
        if type(self.configuration_category_labels) is not tuple or not all(
            type(label) is str for label in self.configuration_category_labels
        ):
            raise TypeError("M2 configuration labels must be an exact tuple of strings")
        if self.type_labels != ("type-1d", "type-2d"):
            raise ValueError("M2 type order differs")
        if type(self.type_labels) is not tuple or not all(
            type(label) is str for label in self.type_labels
        ):
            raise TypeError("M2 type labels must be an exact tuple of strings")
        if self.event_dimensions != (1, 2):
            raise ValueError("M2 event dimensions differ")
        if type(self.event_dimensions) is not tuple or not all(
            type(value) is int for value in self.event_dimensions
        ):
            raise TypeError("M2 event dimensions must be exact integers")
        if self.base_count_probabilities != (
            Fraction(2, 5),
            Fraction(2, 5),
            Fraction(1, 5),
        ):
            raise ValueError("M2 base count probabilities differ")
        if type(self.base_count_probabilities) is not tuple or not all(
            type(value) is Fraction for value in self.base_count_probabilities
        ):
            raise TypeError("M2 base count probabilities must be exact Fractions")
        expected_base_categories = (
            Fraction(2, 5),
            Fraction(4, 25),
            Fraction(6, 25),
            Fraction(4, 125),
            Fraction(12, 125),
            Fraction(9, 125),
        )
        if self.base_configuration_category_probabilities != expected_base_categories:
            raise ValueError("M2 base configuration category probabilities differ")
        if type(self.base_configuration_category_probabilities) is not tuple or not all(
            type(value) is Fraction
            for value in self.base_configuration_category_probabilities
        ):
            raise TypeError(
                "M2 base configuration probabilities must be exact Fractions"
            )
        if self.base_type_probabilities != (Fraction(2, 5), Fraction(3, 5)):
            raise ValueError("M2 base type probabilities differ")
        if type(self.base_type_probabilities) is not tuple or not all(
            type(value) is Fraction for value in self.base_type_probabilities
        ):
            raise TypeError("M2 base type probabilities must be exact Fractions")
        if self.count_score_penalties != (
            Fraction(0, 1),
            Fraction(0, 1),
            Fraction(-1, 4),
        ):
            raise ValueError("M2 count score penalties differ")
        if type(self.count_score_penalties) is not tuple or not all(
            type(value) is Fraction for value in self.count_score_penalties
        ):
            raise TypeError("M2 count score penalties must be exact Fractions")
        if self.type_quadratic_coefficients != (
            (Fraction(1, 4),),
            (Fraction(1, 8), Fraction(1, 6)),
        ):
            raise ValueError("M2 quadratic coefficients differ")
        if type(self.type_quadratic_coefficients) is not tuple or any(
            type(event) is not tuple
            or any(type(value) is not Fraction for value in event)
            for event in self.type_quadratic_coefficients
        ):
            raise TypeError("M2 quadratic coefficients must be nested Fractions")
        if type(self.ideal_score_formula) is not str or self.ideal_score_formula != (
            "q=c_count[n]-sum_events(sum_j a[type,j]*x_j^2);"
            "c_count=(0,0,-1/4);a=((1/4),(1/8,1/6)) over real x"
        ):
            raise ValueError("M2 ideal score formula differs")
        if type(self.represented_coordinate_score_policy) is not str or (
            self.represented_coordinate_score_policy
        ) != (
            "Fraction.from_float(x_j);evaluate q exactly in Q;"
            "binary64 formula and display remain separate"
        ):
            raise ValueError("M2 represented-coordinate score policy differs")
        for name in ("score_upper_bound", "ideal_weight_envelope"):
            if type(getattr(self, name)) is not Fraction:
                raise TypeError("M2 " + name + " must be an exact Fraction")
        if self.score_upper_bound != Fraction(0, 1):
            raise ValueError("M2 score upper bound differs")
        if self.ideal_weight_envelope != Fraction(1, 1):
            raise ValueError("M2 ideal weight envelope differs")
        mu1 = _M2_TYPE1_INTEGRATED_WEIGHT
        mu2 = _M2_TYPE2_INTEGRATED_WEIGHT
        mean_mu = 0.4 * mu1 + 0.6 * mu2
        integrated_weights = _exact_tuple(
            self.type_event_integrated_weights,
            name="M2 type_event_integrated_weights",
            minimum=2,
            maximum=2,
        )
        checked_integrated_weights = tuple(
            _exact_float(value, name="M2 integrated weight[%d]" % index)
            for index, value in enumerate(integrated_weights)
        )
        if tuple(value.hex() for value in checked_integrated_weights) != (
            mu1.hex(),
            mu2.hex(),
        ):
            raise ValueError("M2 event integrated weights differ")
        mean_integrated_weight = _exact_float(
            self.mean_event_integrated_weight,
            name="M2 mean_event_integrated_weight",
        )
        if mean_integrated_weight.hex() != mean_mu.hex():
            raise ValueError("M2 mean event integrated weight differs")
        count_two_factor = math.exp(-0.25)
        expected_configuration_masses = (
            0.4,
            0.16 * mu1,
            0.24 * mu2,
            0.032 * count_two_factor * mu1 * mu1,
            0.096 * count_two_factor * mu1 * mu2,
            0.072 * count_two_factor * mu2 * mu2,
        )
        configuration_masses = _exact_tuple(
            self.unnormalized_target_configuration_category_masses,
            name="M2 unnormalized_target_configuration_category_masses",
            minimum=6,
            maximum=6,
        )
        checked_configuration_masses = tuple(
            _exact_float(value, name="M2 configuration mass[%d]" % index)
            for index, value in enumerate(configuration_masses)
        )
        if tuple(value.hex() for value in checked_configuration_masses) != tuple(
            value.hex() for value in expected_configuration_masses
        ):
            raise ValueError("M2 target configuration category masses differ")
        expected_normalizer = math.fsum(expected_configuration_masses)
        target_normalizer = _exact_float(
            self.target_normalizer,
            name="M2 target_normalizer",
        )
        if target_normalizer.hex() != expected_normalizer.hex():
            raise ValueError("M2 target normalizer differs")
        expected_configuration_probabilities = tuple(
            value / expected_normalizer for value in expected_configuration_masses
        )
        configuration_probabilities = _probability_table(
            self.target_configuration_category_probabilities,
            name="M2 target_configuration_category_probabilities",
        )
        if tuple(value.hex() for value in configuration_probabilities) != tuple(
            value.hex() for value in expected_configuration_probabilities
        ):
            raise ValueError("M2 target configuration probabilities differ")
        expected_count_masses = (
            0.4,
            0.4 * mean_mu,
            0.2 * count_two_factor * mean_mu * mean_mu,
        )
        count_masses = _exact_tuple(
            self.unnormalized_target_count_masses,
            name="M2 unnormalized_target_count_masses",
            minimum=3,
            maximum=3,
        )
        checked_count_masses = tuple(
            _exact_float(value, name="M2 count mass[%d]" % index)
            for index, value in enumerate(count_masses)
        )
        if tuple(value.hex() for value in checked_count_masses) != tuple(
            value.hex() for value in expected_count_masses
        ):
            raise ValueError("M2 target count masses differ")
        if math.fsum(expected_count_masses).hex() != expected_normalizer.hex():
            raise ValueError("M2 count/configuration normalizers disagree")
        expected_count = tuple(
            value / expected_normalizer for value in expected_count_masses
        )
        count_probabilities = _probability_table(
            self.target_count_probabilities,
            name="M2 target_count_probabilities",
        )
        if tuple(value.hex() for value in count_probabilities) != tuple(
            value.hex() for value in expected_count
        ):
            raise ValueError("M2 target count probabilities differ")
        expected_type = (0.4 * mu1 / mean_mu, 0.6 * mu2 / mean_mu)
        type_probabilities = _probability_table(
            self.target_type_probabilities,
            name="M2 target_type_probabilities",
        )
        if tuple(value.hex() for value in type_probabilities) != tuple(
            value.hex() for value in expected_type
        ):
            raise ValueError("M2 target type probabilities differ")
        if self.type_coordinate_variances != (
            (Fraction(2, 3),),
            (Fraction(4, 5), Fraction(3, 4)),
        ):
            raise ValueError("M2 target coordinate variances differ")
        if type(self.type_coordinate_variances) is not tuple or any(
            type(event) is not tuple
            or any(type(value) is not Fraction for value in event)
            for event in self.type_coordinate_variances
        ):
            raise TypeError("M2 coordinate variances must be nested Fractions")
        acceptance = _exact_float(
            self.rejection_acceptance_probability,
            name="M2 rejection_acceptance_probability",
        )
        if acceptance.hex() != expected_normalizer.hex():
            raise ValueError("M2 rejection acceptance probability differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("MixedM2Fixture cannot be subclassed")


@dataclass(frozen=True)
class QuadratureCDFResult:
    """Independent numerical cross-check of an analytic Gaussian CDF."""

    query: float
    distribution_id: str
    target_variance: float
    value: float
    analytic_reference_value: float
    absolute_discrepancy: float
    absolute_error_estimate: float
    evaluation_count: int
    integrated_tail: str
    absolute_tolerance: float
    relative_tolerance: float
    subdivision_limit: int

    def __post_init__(self) -> None:
        query = _exact_float(self.query, name="query", finite=False)
        if type(self.distribution_id) is not str or self.distribution_id not in (
            "T28-M1-Q:continuous-b",
            "T28-M2-Q:type-1d",
            "T28-M2-Q:type-2d-coordinate-0",
            "T28-M2-Q:type-2d-coordinate-1",
        ):
            raise ValueError("quadrature distribution_id is invalid")
        variance = _positive_float(self.target_variance, name="target_variance")
        expected_variances = {
            "T28-M1-Q:continuous-b": _M1_CONTINUOUS_VARIANCE,
            "T28-M2-Q:type-1d": _M2_TYPE1_VARIANCE,
            "T28-M2-Q:type-2d-coordinate-0": _M2_TYPE2_VARIANCES[0],
            "T28-M2-Q:type-2d-coordinate-1": _M2_TYPE2_VARIANCES[1],
        }
        if variance.hex() != expected_variances[self.distribution_id].hex():
            raise ValueError("quadrature target variance differs")
        value = _probability(self.value, name="value")
        analytic = _probability(
            self.analytic_reference_value,
            name="analytic_reference_value",
        )
        expected_analytic = _zero_mean_gaussian_cdf(query, variance)
        if analytic.hex() != expected_analytic.hex():
            raise ValueError("quadrature analytic reference value differs")
        discrepancy = _exact_float(
            self.absolute_discrepancy,
            name="absolute_discrepancy",
        )
        if discrepancy < 0.0:
            raise ValueError("absolute_discrepancy must be nonnegative")
        if discrepancy.hex() != abs(value - analytic).hex():
            raise ValueError("quadrature absolute discrepancy differs")
        error = _exact_float(
            self.absolute_error_estimate,
            name="absolute_error_estimate",
        )
        if error < 0.0:
            raise ValueError("absolute_error_estimate must be nonnegative")
        evaluations = _exact_integer(
            self.evaluation_count,
            name="evaluation_count",
            minimum=0,
            maximum=100_000_000,
        )
        if type(self.integrated_tail) is not str or self.integrated_tail not in (
            "closed-lower",
            "lower",
            "upper",
            "closed-upper",
        ):
            raise ValueError("integrated_tail is invalid")
        if query == -math.inf:
            expected_tail = "closed-lower"
        elif query == math.inf:
            expected_tail = "closed-upper"
        elif query < 0.0:
            expected_tail = "lower"
        else:
            expected_tail = "upper"
        if self.integrated_tail != expected_tail:
            raise ValueError("integrated_tail differs from the query")
        if math.isfinite(query) and evaluations == 0:
            raise ValueError("finite-query quadrature must report evaluations")
        if not math.isfinite(query) and evaluations != 0:
            raise ValueError("closed-tail quadrature must report zero evaluations")
        _quadrature_controls(
            self.absolute_tolerance,
            self.relative_tolerance,
            self.subdivision_limit,
        )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("QuadratureCDFResult cannot be subclassed")


@dataclass(frozen=True)
class ExactRationalQuadraticScoreEvaluation:
    """Separated score layers for one represented-coordinate Q-fixture state."""

    fixture_id: str
    event_type_indices: Tuple[int, ...]
    represented_coordinates: Tuple[Tuple[float, ...], ...]
    quadratic_coefficients: Tuple[Tuple[Fraction, ...], ...]
    count_penalty: Fraction
    exact_rational_score: Fraction
    exact_rational_score_as_binary64: float
    binary64_formula_score: float

    def __post_init__(self) -> None:
        if type(self.fixture_id) is not str or self.fixture_id not in (
            "T28-M1-Q",
            "T28-M2-Q",
        ):
            raise ValueError("score evaluation fixture_id is invalid")
        indices = _exact_tuple(
            self.event_type_indices,
            name="event_type_indices",
            maximum=2,
        )
        coordinates = _exact_tuple(
            self.represented_coordinates,
            name="represented_coordinates",
            maximum=2,
        )
        coefficients = _exact_tuple(
            self.quadratic_coefficients,
            name="quadratic_coefficients",
            maximum=2,
        )
        if not len(indices) == len(coordinates) == len(coefficients):
            raise ValueError("score evaluation event tuple lengths differ")
        for index, event_type in enumerate(indices):
            _exact_integer(
                event_type,
                name="event_type_indices[%d]" % index,
                minimum=0,
                maximum=1,
            )
        checked_coordinates = []
        for event_index, event in enumerate(coordinates):
            values = _exact_tuple(
                event,
                name="represented_coordinates[%d]" % event_index,
                maximum=2,
            )
            checked_coordinates.append(
                tuple(
                    _canonical_score_coordinate(
                        value,
                        name="represented_coordinates[%d][%d]"
                        % (event_index, coordinate_index),
                    )
                    for coordinate_index, value in enumerate(values)
                )
            )
        for event_index, event in enumerate(coefficients):
            values = _exact_tuple(
                event,
                name="quadratic_coefficients[%d]" % event_index,
                maximum=2,
            )
            if not all(type(value) is Fraction and value > 0 for value in values):
                raise TypeError("quadratic coefficients must be positive Fractions")
        if type(self.count_penalty) is not Fraction:
            raise TypeError("count_penalty must be an exact Fraction")
        if type(self.exact_rational_score) is not Fraction:
            raise TypeError("exact_rational_score must be an exact Fraction")
        exact = self.count_penalty
        rounded = float(self.count_penalty)
        for event_coefficients, event_coordinates in zip(
            coefficients,
            checked_coordinates,
        ):
            if len(event_coefficients) != len(event_coordinates):
                raise ValueError("score coefficient/coordinate dimensions differ")
            for coefficient, coordinate in zip(
                event_coefficients,
                event_coordinates,
            ):
                exact -= coefficient * Fraction.from_float(coordinate) ** 2
                rounded -= float(coefficient) * (coordinate * coordinate)
        if self.exact_rational_score != exact:
            raise ValueError("exact rational score differs")
        exact_as_binary64 = _exact_float(
            self.exact_rational_score_as_binary64,
            name="exact_rational_score_as_binary64",
        )
        rounded_score = _exact_float(
            self.binary64_formula_score,
            name="binary64_formula_score",
        )
        if exact_as_binary64.hex() != float(exact).hex():
            raise ValueError("exact-rational binary64 conversion differs")
        if rounded_score.hex() != rounded.hex():
            raise ValueError("direct binary64 formula score differs")
        if self.fixture_id == "T28-M1-Q":
            allowed = ((), (0,), (1,))
            if indices not in allowed:
                raise ValueError("M1 score event type pattern differs")
            expected_dimensions = {
                (): (),
                (0,): (0,),
                (1,): (1,),
            }[indices]
            expected_coefficients = {
                (): (),
                (0,): ((),),
                (1,): ((Fraction(1, 4),),),
            }[indices]
            if tuple(len(event) for event in coordinates) != expected_dimensions:
                raise ValueError("M1 score coordinate dimensions differ")
            if coefficients != expected_coefficients:
                raise ValueError("M1 score coefficients differ")
            if self.count_penalty != Fraction(0, 1):
                raise ValueError("M1 score count penalty differs")
        else:
            if tuple(indices) != tuple(sorted(indices)):
                raise ValueError("M2 event types must be in canonical order")
            model_keys = tuple(zip(indices, checked_coordinates))
            if model_keys != tuple(sorted(model_keys)):
                raise ValueError("M2 represented events must be in canonical order")
            expected_coefficients = tuple(
                ((Fraction(1, 4),), (Fraction(1, 8), Fraction(1, 6)))[event_type]
                for event_type in indices
            )
            if coefficients != expected_coefficients:
                raise ValueError("M2 score coefficients differ")
            if (
                self.count_penalty
                != (
                    Fraction(0, 1),
                    Fraction(0, 1),
                    Fraction(-1, 4),
                )[len(indices)]
            ):
                raise ValueError("M2 score count penalty differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ExactRationalQuadraticScoreEvaluation cannot be subclassed")


@dataclass(frozen=True)
class M2CountTypeMoments:
    """Analytic first and second count/type-count moments for T28-M2-Q."""

    count_mean: float
    count_second_moment: float
    count_variance: float
    expected_type_counts: Tuple[float, float]
    type_count_variances: Tuple[float, float]
    type_count_covariance: float

    def __post_init__(self) -> None:
        fixture = mixed_m2_fixture()
        p0, p1, p2 = fixture.target_count_probabilities
        del p0
        mean = p1 + 2.0 * p2
        second = p1 + 4.0 * p2
        variance = second - mean * mean
        type1, type2 = fixture.target_type_probabilities
        count_variances = (
            mean * type1 * (1.0 - type1) + variance * type1 * type1,
            mean * type2 * (1.0 - type2) + variance * type2 * type2,
        )
        covariance = (variance - mean) * type1 * type2
        expected_values = (
            ("count_mean", self.count_mean, mean),
            ("count_second_moment", self.count_second_moment, second),
            ("count_variance", self.count_variance, variance),
            (
                "type_count_covariance",
                self.type_count_covariance,
                covariance,
            ),
        )
        for name, actual, expected in expected_values:
            checked = _exact_float(actual, name=name)
            if checked.hex() != expected.hex():
                raise ValueError(name + " differs")
        expected_type_counts = _exact_tuple(
            self.expected_type_counts,
            name="expected_type_counts",
            minimum=2,
            maximum=2,
        )
        checked_type_counts = tuple(
            _exact_float(value, name="expected_type_counts[%d]" % index)
            for index, value in enumerate(expected_type_counts)
        )
        if tuple(value.hex() for value in checked_type_counts) != (
            (mean * type1).hex(),
            (mean * type2).hex(),
        ):
            raise ValueError("expected type counts differ")
        type_count_variances = _exact_tuple(
            self.type_count_variances,
            name="type_count_variances",
            minimum=2,
            maximum=2,
        )
        checked_count_variances = tuple(
            _exact_float(value, name="type_count_variances[%d]" % index)
            for index, value in enumerate(type_count_variances)
        )
        if tuple(value.hex() for value in checked_count_variances) != tuple(
            value.hex() for value in count_variances
        ):
            raise ValueError("type count variances differ")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("M2CountTypeMoments cannot be subclassed")


@dataclass(frozen=True)
class ProjectionMoment:
    """Closed-form mean and second moment for one M2 type-2 projection."""

    projection: Tuple[float, float]
    squared_norm: float
    mean: float
    second_moment: float
    variance: float

    def __post_init__(self) -> None:
        projection = _exact_tuple(
            self.projection,
            name="projection",
            minimum=2,
            maximum=2,
        )
        for index, value in enumerate(projection):
            _coordinate(value, name="projection[%d]" % index)
        squared_norm = _positive_float(self.squared_norm, name="squared_norm")
        expected_norm = math.fsum(value * value for value in projection)
        if squared_norm.hex() != expected_norm.hex():
            raise ValueError("projection squared norm differs")
        mean = _exact_float(self.mean, name="mean")
        second = _exact_float(self.second_moment, name="second_moment")
        variance = _exact_float(self.variance, name="variance")
        if second < 0.0 or variance < 0.0:
            raise ValueError("projection moments must be nonnegative")
        expected_variance = second - mean * mean
        if variance.hex() != expected_variance.hex():
            raise ValueError("projection variance differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ProjectionMoment cannot be subclassed")


@dataclass(frozen=True)
class FiniteCategoricalTVBound:
    """Empirical finite-category TV with a simultaneous Hoeffding radius."""

    category_count: int
    sample_size: int
    expected_probabilities: Tuple[float, ...]
    observed_counts: Tuple[int, ...]
    empirical_probabilities: Tuple[float, ...]
    empirical_total_variation: float
    alpha: float
    simultaneous_linf_radius: float
    total_variation_radius: float
    total_variation_upper_bound: float

    def __post_init__(self) -> None:
        category_count = _exact_integer(
            self.category_count,
            name="category_count",
            minimum=1,
            maximum=_MAX_CATEGORIES,
        )
        sample_size = _exact_integer(
            self.sample_size,
            name="sample_size",
            minimum=1,
            maximum=_MAX_BINOMIAL_TRIALS,
        )
        expected = _probability_table(
            self.expected_probabilities, name="expected_probabilities"
        )
        counts = _count_tuple(self.observed_counts, name="observed_counts")
        empirical = _probability_table(
            self.empirical_probabilities, name="empirical_probabilities"
        )
        if len(expected) != category_count or len(counts) != category_count:
            raise ValueError("categorical category count differs")
        if len(empirical) != category_count or sum(counts) != sample_size:
            raise ValueError("categorical sample size differs")
        checked_alpha = _alpha(self.alpha)
        for name in (
            "empirical_total_variation",
            "simultaneous_linf_radius",
            "total_variation_radius",
            "total_variation_upper_bound",
        ):
            value = _exact_float(getattr(self, name), name=name)
            if value < 0.0 or value > 1.0:
                raise ValueError(name + " must lie in [0, 1]")
        expected_empirical = tuple(value / sample_size for value in counts)
        if tuple(value.hex() for value in empirical) != tuple(
            value.hex() for value in expected_empirical
        ):
            raise ValueError("categorical empirical probabilities differ")
        expected_tv = 0.5 * math.fsum(
            abs(actual - target) for actual, target in zip(expected_empirical, expected)
        )
        expected_radius = min(
            1.0,
            math.sqrt(
                math.log(2.0 * category_count / checked_alpha) / (2.0 * sample_size)
            ),
        )
        expected_tv_radius = min(1.0, 0.5 * category_count * expected_radius)
        expected_upper = min(1.0, expected_tv + expected_tv_radius)
        for name, expected_value in (
            ("empirical_total_variation", expected_tv),
            ("simultaneous_linf_radius", expected_radius),
            ("total_variation_radius", expected_tv_radius),
            ("total_variation_upper_bound", expected_upper),
        ):
            if getattr(self, name).hex() != expected_value.hex():
                raise ValueError(name + " differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("FiniteCategoricalTVBound cannot be subclassed")


@dataclass(frozen=True)
class KSDKWBound:
    """Two-sided empirical KS discrepancy plus the DKW sampling radius."""

    sample_size: int
    empirical_ks: float
    alpha: float
    dkw_radius: float
    cdf_distance_upper_bound: float

    def __post_init__(self) -> None:
        sample_size = _exact_integer(
            self.sample_size,
            name="sample_size",
            minimum=1,
            maximum=_MAX_SAMPLES,
        )
        for name in ("empirical_ks", "dkw_radius", "cdf_distance_upper_bound"):
            value = _exact_float(getattr(self, name), name=name)
            if value < 0.0 or value > 1.0:
                raise ValueError(name + " must lie in [0, 1]")
        checked_alpha = _alpha(self.alpha)
        expected_radius = min(
            1.0,
            math.sqrt(math.log(2.0 / checked_alpha) / (2.0 * sample_size)),
        )
        if self.dkw_radius.hex() != expected_radius.hex():
            raise ValueError("DKW radius differs")
        expected_upper = min(1.0, self.empirical_ks + expected_radius)
        if self.cdf_distance_upper_bound.hex() != expected_upper.hex():
            raise ValueError("CDF distance upper bound differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("KSDKWBound cannot be subclassed")


@dataclass(frozen=True)
class BinomialConfidenceInterval:
    """Equal-tailed two-sided Clopper--Pearson interval."""

    successes: int
    trials: int
    alpha: float
    estimate: float
    lower: float
    upper: float

    def __post_init__(self) -> None:
        trials = _exact_integer(
            self.trials,
            name="trials",
            minimum=1,
            maximum=_MAX_BINOMIAL_TRIALS,
        )
        successes = _exact_integer(
            self.successes,
            name="successes",
            minimum=0,
            maximum=trials,
        )
        alpha = _alpha(self.alpha)
        estimate = _probability(self.estimate, name="estimate")
        lower = _probability(self.lower, name="lower")
        upper = _probability(self.upper, name="upper")
        if estimate.hex() != (successes / trials).hex():
            raise ValueError("binomial estimate differs")
        if lower > estimate or estimate > upper:
            raise ValueError("binomial interval does not contain its estimate")
        if alpha != self.alpha:
            raise ValueError("binomial alpha differs")
        half_alpha = 0.5 * alpha
        expected_lower = (
            0.0
            if successes == 0
            else float(
                betaincinv(
                    successes,
                    trials - successes + 1,
                    half_alpha,
                )
            )
        )
        expected_upper = (
            1.0
            if successes == trials
            else float(
                betaincinv(
                    successes + 1,
                    trials - successes,
                    1.0 - half_alpha,
                )
            )
        )
        if lower.hex() != expected_lower.hex() or upper.hex() != expected_upper.hex():
            raise ValueError("Clopper-Pearson interval endpoints differ")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("BinomialConfidenceInterval cannot be subclassed")


@dataclass(frozen=True)
class RejectionExhaustionCheck:
    """Observed bounded-rejection exhaustion versus its ideal prediction."""

    attempt_cap: int
    request_count: int
    exhaustion_count: int
    acceptance_probability: float
    expected_exhaustion_probability: float
    confidence_interval: BinomialConfidenceInterval
    expected_probability_inside_interval: bool

    def __post_init__(self) -> None:
        attempt_cap = _exact_integer(
            self.attempt_cap,
            name="attempt_cap",
            minimum=1,
            maximum=_MAX_REJECTION_ATTEMPTS,
        )
        request_count = _exact_integer(
            self.request_count,
            name="request_count",
            minimum=1,
            maximum=_MAX_BINOMIAL_TRIALS,
        )
        exhaustion_count = _exact_integer(
            self.exhaustion_count,
            name="exhaustion_count",
            minimum=0,
            maximum=request_count,
        )
        acceptance = _probability(
            self.acceptance_probability,
            name="acceptance_probability",
        )
        expected = _probability(
            self.expected_exhaustion_probability,
            name="expected_exhaustion_probability",
        )
        if (
            expected.hex()
            != rejection_exhaustion_probability(acceptance, attempt_cap).hex()
        ):
            raise ValueError("rejection exhaustion probability differs")
        interval = self.confidence_interval
        if type(interval) is not BinomialConfidenceInterval:
            raise TypeError("confidence_interval has the wrong exact type")
        if interval.successes != exhaustion_count or interval.trials != request_count:
            raise ValueError("rejection confidence interval has different counts")
        if type(self.expected_probability_inside_interval) is not bool:
            raise TypeError("expected_probability_inside_interval must be bool")
        inside = interval.lower <= expected <= interval.upper
        if self.expected_probability_inside_interval is not inside:
            raise ValueError("rejection interval decision differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("RejectionExhaustionCheck cannot be subclassed")


@dataclass(frozen=True)
class ESSSummary:
    """Scale-stable deterministic summary of one positive SIR weight tuple."""

    particle_count: int
    minimum_weight: float
    maximum_weight: float
    effective_sample_size: float
    effective_sample_size_fraction: float
    maximum_normalized_weight: float
    normalized_weight_entropy: float
    perplexity: float

    def __post_init__(self) -> None:
        particle_count = _exact_integer(
            self.particle_count,
            name="particle_count",
            minimum=1,
            maximum=_MAX_PARTICLES,
        )
        minimum = _positive_float(self.minimum_weight, name="minimum_weight")
        maximum = _positive_float(self.maximum_weight, name="maximum_weight")
        if minimum > maximum:
            raise ValueError("ESS minimum weight exceeds maximum")
        ess = _positive_float(self.effective_sample_size, name="effective_sample_size")
        if ess < 1.0 or ess > particle_count:
            raise ValueError("ESS lies outside [1, particle_count]")
        fraction = _probability(
            self.effective_sample_size_fraction,
            name="effective_sample_size_fraction",
        )
        if fraction.hex() != (ess / particle_count).hex():
            raise ValueError("ESS fraction differs")
        maximum_normalized = _probability(
            self.maximum_normalized_weight,
            name="maximum_normalized_weight",
        )
        if maximum_normalized <= 0.0:
            raise ValueError("maximum normalized weight must be positive")
        if maximum_normalized < 1.0 / particle_count:
            raise ValueError("maximum normalized weight is below 1 / particle_count")
        entropy = _exact_float(
            self.normalized_weight_entropy,
            name="normalized_weight_entropy",
        )
        if entropy < 0.0 or entropy > math.log(particle_count) + 1.0e-12:
            raise ValueError("normalized weight entropy is invalid")
        perplexity = _positive_float(self.perplexity, name="perplexity")
        if perplexity < 1.0 or perplexity > particle_count * (1.0 + 1.0e-12):
            raise ValueError("weight perplexity lies outside its analytic bounds")
        if perplexity.hex() != math.exp(entropy).hex():
            raise ValueError("weight perplexity differs from exp(entropy)")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ESSSummary cannot be subclassed")


def atomic_a0_fixture() -> AtomicA0Fixture:
    """Return the immutable exact ``T28-A0-H`` factor fixture."""

    base = (
        Fraction(2, 5),
        Fraction(4, 25),
        Fraction(6, 25),
        Fraction(4, 125),
        Fraction(12, 125),
        Fraction(9, 125),
    )
    tilt = (
        Fraction(1, 1),
        Fraction(2, 1),
        Fraction(1, 2),
        Fraction(3, 1),
        Fraction(3, 2),
        Fraction(1, 4),
    )
    masses = tuple(left * right for left, right in zip(base, tilt))
    normalizer = Fraction(549, 500)
    target_numerators = (200, 160, 60, 48, 72, 9)
    target = tuple(Fraction(value, 549) for value in target_numerators)
    envelope = Fraction(3, 1)
    return AtomicA0Fixture(
        fixture_id="T28-A0-H",
        state_labels=("empty", "a", "b", "aa", "ab", "bb"),
        base_probabilities=base,
        tilt_values=tilt,
        unnormalized_target_masses=masses,
        target_numerators=target_numerators,
        target_denominator=549,
        target_probabilities=target,
        normalizer=normalizer,
        rejection_envelope=envelope,
        rejection_acceptance_probability=normalizer / envelope,
    )


def mixed_m1_fixture() -> MixedM1Fixture:
    """Return the immutable direct-composer ``T28-M1-Q`` fixture."""

    continuous_weight = _M1_CONTINUOUS_INTEGRATED_WEIGHT
    masses = (0.5, 0.2, 0.3 * continuous_weight)
    normalizer = math.fsum(masses)
    probabilities = tuple(value / normalizer for value in masses)
    return MixedM1Fixture(
        fixture_id="T28-M1-Q",
        category_labels=("empty", "atomic-a", "continuous-b"),
        base_category_probabilities=(
            Fraction(1, 2),
            Fraction(1, 5),
            Fraction(3, 10),
        ),
        ideal_score_formula=(
            "q(empty)=q(atomic-a)=0;" "q(continuous-b,x)=-x^2/4 for ideal real x"
        ),
        represented_coordinate_score_policy=(
            "Fraction.from_float(x);q=-x*x/4 exactly;"
            "binary64 formula and display remain separate"
        ),
        continuous_quadratic_coefficient=Fraction(1, 4),
        score_upper_bound=Fraction(0, 1),
        ideal_weight_envelope=Fraction(1, 1),
        continuous_integrated_weight=continuous_weight,
        unnormalized_target_category_masses=masses,
        target_normalizer=normalizer,
        target_category_probabilities=probabilities,
        continuous_target_variance=Fraction(2, 3),
        rejection_acceptance_probability=normalizer,
    )


def mixed_m2_fixture() -> MixedM2Fixture:
    """Return the immutable direct-composer ``T28-M2-Q`` fixture."""

    mu1 = _M2_TYPE1_INTEGRATED_WEIGHT
    mu2 = _M2_TYPE2_INTEGRATED_WEIGHT
    mean_mu = 0.4 * mu1 + 0.6 * mu2
    count_two_factor = math.exp(-0.25)
    configuration_masses = (
        0.4,
        0.16 * mu1,
        0.24 * mu2,
        0.032 * count_two_factor * mu1 * mu1,
        0.096 * count_two_factor * mu1 * mu2,
        0.072 * count_two_factor * mu2 * mu2,
    )
    normalizer = math.fsum(configuration_masses)
    configuration_probabilities = tuple(
        value / normalizer for value in configuration_masses
    )
    count_masses = (
        0.4,
        0.4 * mean_mu,
        0.2 * count_two_factor * mean_mu * mean_mu,
    )
    count_probabilities = tuple(value / normalizer for value in count_masses)
    type_probabilities = (0.4 * mu1 / mean_mu, 0.6 * mu2 / mean_mu)
    return MixedM2Fixture(
        fixture_id="T28-M2-Q",
        count_labels=("count-0", "count-1", "count-2"),
        configuration_category_labels=(
            "empty",
            "one-type-1d",
            "one-type-2d",
            "two-type-1d",
            "one-each",
            "two-type-2d",
        ),
        type_labels=("type-1d", "type-2d"),
        event_dimensions=(1, 2),
        base_count_probabilities=(
            Fraction(2, 5),
            Fraction(2, 5),
            Fraction(1, 5),
        ),
        base_configuration_category_probabilities=(
            Fraction(2, 5),
            Fraction(4, 25),
            Fraction(6, 25),
            Fraction(4, 125),
            Fraction(12, 125),
            Fraction(9, 125),
        ),
        base_type_probabilities=(Fraction(2, 5), Fraction(3, 5)),
        count_score_penalties=(
            Fraction(0, 1),
            Fraction(0, 1),
            Fraction(-1, 4),
        ),
        type_quadratic_coefficients=(
            (Fraction(1, 4),),
            (Fraction(1, 8), Fraction(1, 6)),
        ),
        ideal_score_formula=(
            "q=c_count[n]-sum_events(sum_j a[type,j]*x_j^2);"
            "c_count=(0,0,-1/4);a=((1/4),(1/8,1/6)) over real x"
        ),
        represented_coordinate_score_policy=(
            "Fraction.from_float(x_j);evaluate q exactly in Q;"
            "binary64 formula and display remain separate"
        ),
        score_upper_bound=Fraction(0, 1),
        ideal_weight_envelope=Fraction(1, 1),
        type_event_integrated_weights=(mu1, mu2),
        mean_event_integrated_weight=mean_mu,
        unnormalized_target_configuration_category_masses=configuration_masses,
        target_configuration_category_probabilities=configuration_probabilities,
        unnormalized_target_count_masses=count_masses,
        target_normalizer=normalizer,
        target_count_probabilities=count_probabilities,
        target_type_probabilities=type_probabilities,
        type_coordinate_variances=(
            (Fraction(2, 3),),
            (Fraction(4, 5), Fraction(3, 4)),
        ),
        rejection_acceptance_probability=normalizer,
    )


def _score_layers(
    coordinates: Tuple[Tuple[float, ...], ...],
    coefficients: Tuple[Tuple[Fraction, ...], ...],
    count_penalty: Fraction,
) -> Tuple[Fraction, float, float]:
    exact = count_penalty
    binary64_formula = float(count_penalty)
    for event_coordinates, event_coefficients in zip(coordinates, coefficients):
        for coordinate, coefficient in zip(
            event_coordinates,
            event_coefficients,
        ):
            exact -= coefficient * Fraction.from_float(coordinate) ** 2
            binary64_formula -= float(coefficient) * (coordinate * coordinate)
    return exact, float(exact), binary64_formula


def m1_exact_rational_score(
    category: object,
    coordinates: object,
) -> ExactRationalQuadraticScoreEvaluation:
    """Evaluate T28-M1-Q score layers at represented binary64 coordinates.

    ``coordinates`` is empty for ``empty`` and ``atomic-a`` and is a one-float
    tuple for ``continuous-b``.  This is not an evaluation at an unspecified
    ideal real; it is explicitly an exact rational evaluation of represented
    binary64 input plus a separately recorded direct-binary64 calculation.
    """

    if type(category) is not str or category not in (
        "empty",
        "atomic-a",
        "continuous-b",
    ):
        raise ValueError("category must be a frozen M1 category label")
    values = _exact_tuple(
        coordinates,
        name="coordinates",
        maximum=1,
    )
    if category == "empty":
        if values:
            raise ValueError("empty M1 category must have no coordinates")
        indices: Tuple[int, ...] = ()
        represented: Tuple[Tuple[float, ...], ...] = ()
        coefficients: Tuple[Tuple[Fraction, ...], ...] = ()
    elif category == "atomic-a":
        if values:
            raise ValueError("atomic M1 category must have no coordinates")
        indices = (0,)
        represented = ((),)
        coefficients = ((),)
    else:
        if len(values) != 1:
            raise ValueError("continuous M1 category requires one coordinate")
        coordinate = _canonical_score_coordinate(values[0], name="coordinates[0]")
        indices = (1,)
        represented = ((coordinate,),)
        coefficients = ((Fraction(1, 4),),)
    penalty = Fraction(0, 1)
    exact, exact_as_binary64, binary64_formula = _score_layers(
        represented,
        coefficients,
        penalty,
    )
    return ExactRationalQuadraticScoreEvaluation(
        fixture_id="T28-M1-Q",
        event_type_indices=indices,
        represented_coordinates=represented,
        quadratic_coefficients=coefficients,
        count_penalty=penalty,
        exact_rational_score=exact,
        exact_rational_score_as_binary64=exact_as_binary64,
        binary64_formula_score=binary64_formula,
    )


def m2_exact_rational_score(
    event_type_indices: object,
    represented_coordinates: object,
) -> ExactRationalQuadraticScoreEvaluation:
    """Evaluate T28-M2-Q score layers for a canonical represented state."""

    raw_indices = _exact_tuple(
        event_type_indices,
        name="event_type_indices",
        maximum=2,
    )
    indices = tuple(
        _exact_integer(
            value,
            name="event_type_indices[%d]" % index,
            minimum=0,
            maximum=1,
        )
        for index, value in enumerate(raw_indices)
    )
    if indices != tuple(sorted(indices)):
        raise ValueError("event_type_indices must be in canonical order")
    raw_coordinates = _exact_tuple(
        represented_coordinates,
        name="represented_coordinates",
        maximum=2,
    )
    if len(raw_coordinates) != len(indices):
        raise ValueError("M2 event types and coordinate events differ in length")
    coefficient_table = (
        (Fraction(1, 4),),
        (Fraction(1, 8), Fraction(1, 6)),
    )
    coefficients = tuple(coefficient_table[event_type] for event_type in indices)
    checked_coordinates = []
    for event_index, (raw_event, event_coefficients) in enumerate(
        zip(raw_coordinates, coefficients)
    ):
        event = _exact_tuple(
            raw_event,
            name="represented_coordinates[%d]" % event_index,
            minimum=len(event_coefficients),
            maximum=len(event_coefficients),
        )
        checked_coordinates.append(
            tuple(
                _canonical_score_coordinate(
                    value,
                    name="represented_coordinates[%d][%d]"
                    % (event_index, coordinate_index),
                )
                for coordinate_index, value in enumerate(event)
            )
        )
    coordinates = tuple(checked_coordinates)
    model_keys = tuple(zip(indices, coordinates))
    if model_keys != tuple(sorted(model_keys)):
        raise ValueError("represented events must be in canonical model-key order")
    penalty = (
        Fraction(0, 1),
        Fraction(0, 1),
        Fraction(-1, 4),
    )[len(indices)]
    exact, exact_as_binary64, binary64_formula = _score_layers(
        coordinates,
        coefficients,
        penalty,
    )
    return ExactRationalQuadraticScoreEvaluation(
        fixture_id="T28-M2-Q",
        event_type_indices=indices,
        represented_coordinates=coordinates,
        quadratic_coefficients=coefficients,
        count_penalty=penalty,
        exact_rational_score=exact,
        exact_rational_score_as_binary64=exact_as_binary64,
        binary64_formula_score=binary64_formula,
    )


def _zero_mean_gaussian_density(value: float, variance: float) -> float:
    result = math.exp(-0.5 * value * value / variance) / (
        _SQRT_TWO_PI * math.sqrt(variance)
    )
    if not math.isfinite(result) or result < 0.0:
        raise ArithmeticError("Gaussian density evaluation is invalid")
    return result


def _zero_mean_gaussian_cdf(value: float, variance: float) -> float:
    if value == -math.inf:
        return 0.0
    if value == math.inf:
        return 1.0
    result = 0.5 * math.erfc(-value / math.sqrt(2.0 * variance))
    if not math.isfinite(result) or result < 0.0 or result > 1.0:
        raise ArithmeticError("Gaussian CDF evaluation is invalid")
    return result


def _gaussian_cdf_quadrature(
    value: object,
    *,
    distribution_id: str,
    variance: float,
    absolute_tolerance: object,
    relative_tolerance: object,
    subdivision_limit: object,
) -> QuadratureCDFResult:
    query = _exact_float(value, name="value", finite=False)
    absolute, relative, limit = _quadrature_controls(
        absolute_tolerance,
        relative_tolerance,
        subdivision_limit,
    )
    analytic = _zero_mean_gaussian_cdf(query, variance)
    if query == -math.inf:
        return QuadratureCDFResult(
            query=query,
            distribution_id=distribution_id,
            target_variance=variance,
            value=0.0,
            analytic_reference_value=analytic,
            absolute_discrepancy=0.0,
            absolute_error_estimate=0.0,
            evaluation_count=0,
            integrated_tail="closed-lower",
            absolute_tolerance=absolute,
            relative_tolerance=relative,
            subdivision_limit=limit,
        )
    if query == math.inf:
        return QuadratureCDFResult(
            query=query,
            distribution_id=distribution_id,
            target_variance=variance,
            value=1.0,
            analytic_reference_value=analytic,
            absolute_discrepancy=0.0,
            absolute_error_estimate=0.0,
            evaluation_count=0,
            integrated_tail="closed-upper",
            absolute_tolerance=absolute,
            relative_tolerance=relative,
            subdivision_limit=limit,
        )

    def integrand(argument: float) -> float:
        return _zero_mean_gaussian_density(argument, variance)

    if query < 0.0:
        lower = -math.inf
        upper = query
        tail = "lower"
        complement = False
    else:
        lower = query
        upper = math.inf
        tail = "upper"
        complement = True
    output = quad(
        integrand,
        lower,
        upper,
        epsabs=absolute,
        epsrel=relative,
        limit=limit,
        full_output=1,
    )
    if len(output) != 3:
        message = str(output[3]) if len(output) > 3 else "unknown failure"
        raise ArithmeticError("Gaussian CDF quadrature failed: " + message)
    integral, error, information = output
    checked_integral = float(integral)
    checked_error = float(error)
    if not math.isfinite(checked_integral) or not math.isfinite(checked_error):
        raise ArithmeticError("Gaussian CDF quadrature is nonfinite")
    result = 1.0 - checked_integral if complement else checked_integral
    if result < 0.0 or result > 1.0 or not math.isfinite(result):
        raise ArithmeticError("Gaussian CDF quadrature escaped [0, 1]")
    evaluations = int(information.get("neval", -1))
    if evaluations < 0:
        raise ArithmeticError("Gaussian CDF quadrature lost its evaluation count")
    return QuadratureCDFResult(
        query=query,
        distribution_id=distribution_id,
        target_variance=variance,
        value=result,
        analytic_reference_value=analytic,
        absolute_discrepancy=abs(result - analytic),
        absolute_error_estimate=checked_error,
        evaluation_count=evaluations,
        integrated_tail=tail,
        absolute_tolerance=absolute,
        relative_tolerance=relative,
        subdivision_limit=limit,
    )


def m1_continuous_target_density(value: object) -> float:
    """Ideal-real conditional density N(0, 2/3) for T28-M1-Q."""

    checked = _coordinate(value, name="value")
    return _zero_mean_gaussian_density(checked, _M1_CONTINUOUS_VARIANCE)


def m1_continuous_target_cdf(value: object) -> float:
    """Analytic ideal-real conditional CDF N(0, 2/3) for T28-M1-Q."""

    checked = _exact_float(value, name="value", finite=False)
    return _zero_mean_gaussian_cdf(checked, _M1_CONTINUOUS_VARIANCE)


def m1_continuous_target_cdf_quadrature(
    value: object,
    *,
    absolute_tolerance: object = _DEFAULT_QUADRATURE_ABSOLUTE_TOLERANCE,
    relative_tolerance: object = _DEFAULT_QUADRATURE_RELATIVE_TOLERANCE,
    subdivision_limit: object = _DEFAULT_QUADRATURE_LIMIT,
) -> QuadratureCDFResult:
    """Numerically cross-check the analytic T28-M1-Q conditional CDF."""

    return _gaussian_cdf_quadrature(
        value,
        distribution_id="T28-M1-Q:continuous-b",
        variance=_M1_CONTINUOUS_VARIANCE,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        subdivision_limit=subdivision_limit,
    )


def m2_type1_target_density(value: object) -> float:
    """Ideal-real conditional density of the T28-M2-Q one-dimensional type."""

    checked = _coordinate(value, name="value")
    return _zero_mean_gaussian_density(checked, _M2_TYPE1_VARIANCE)


def m2_type1_target_cdf(value: object) -> float:
    """Analytic conditional CDF of the T28-M2-Q one-dimensional type."""

    checked = _exact_float(value, name="value", finite=False)
    return _zero_mean_gaussian_cdf(checked, _M2_TYPE1_VARIANCE)


def m2_type1_target_cdf_quadrature(
    value: object,
    *,
    absolute_tolerance: object = _DEFAULT_QUADRATURE_ABSOLUTE_TOLERANCE,
    relative_tolerance: object = _DEFAULT_QUADRATURE_RELATIVE_TOLERANCE,
    subdivision_limit: object = _DEFAULT_QUADRATURE_LIMIT,
) -> QuadratureCDFResult:
    """Numerically cross-check the T28-M2-Q type-1 conditional CDF."""

    return _gaussian_cdf_quadrature(
        value,
        distribution_id="T28-M2-Q:type-1d",
        variance=_M2_TYPE1_VARIANCE,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        subdivision_limit=subdivision_limit,
    )


def _m2_type2_variance(coordinate_index: object) -> Tuple[int, float]:
    index = _exact_integer(
        coordinate_index,
        name="coordinate_index",
        minimum=0,
        maximum=1,
    )
    return index, _M2_TYPE2_VARIANCES[index]


def m2_type2_coordinate_target_density(
    value: object,
    *,
    coordinate_index: object,
) -> float:
    """Ideal-real density for one specified T28-M2-Q type-2 coordinate."""

    checked = _coordinate(value, name="value")
    _, variance = _m2_type2_variance(coordinate_index)
    return _zero_mean_gaussian_density(checked, variance)


def m2_type2_coordinate_target_cdf(
    value: object,
    *,
    coordinate_index: object,
) -> float:
    """Analytic CDF for one specified T28-M2-Q type-2 coordinate."""

    checked = _exact_float(value, name="value", finite=False)
    _, variance = _m2_type2_variance(coordinate_index)
    return _zero_mean_gaussian_cdf(checked, variance)


def m2_type2_coordinate_target_cdf_quadrature(
    value: object,
    *,
    coordinate_index: object,
    absolute_tolerance: object = _DEFAULT_QUADRATURE_ABSOLUTE_TOLERANCE,
    relative_tolerance: object = _DEFAULT_QUADRATURE_RELATIVE_TOLERANCE,
    subdivision_limit: object = _DEFAULT_QUADRATURE_LIMIT,
) -> QuadratureCDFResult:
    """Numerically cross-check one T28-M2-Q type-2 coordinate CDF."""

    index, variance = _m2_type2_variance(coordinate_index)
    return _gaussian_cdf_quadrature(
        value,
        distribution_id="T28-M2-Q:type-2d-coordinate-%d" % index,
        variance=variance,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        subdivision_limit=subdivision_limit,
    )


def m2_count_type_moments() -> M2CountTypeMoments:
    """Return analytic T28-M2-Q count and type-count moments."""

    fixture = mixed_m2_fixture()
    _, probability_one, probability_two = fixture.target_count_probabilities
    mean = probability_one + 2.0 * probability_two
    second = probability_one + 4.0 * probability_two
    variance = second - mean * mean
    type1, type2 = fixture.target_type_probabilities
    return M2CountTypeMoments(
        count_mean=mean,
        count_second_moment=second,
        count_variance=variance,
        expected_type_counts=(mean * type1, mean * type2),
        type_count_variances=(
            mean * type1 * (1.0 - type1) + variance * type1 * type1,
            mean * type2 * (1.0 - type2) + variance * type2 * type2,
        ),
        type_count_covariance=(variance - mean) * type1 * type2,
    )


def m2_type2_projection_moment(projection: object) -> ProjectionMoment:
    """Closed-form first two moments for a linear M2 type-2 projection."""

    values = _exact_tuple(
        projection,
        name="projection",
        minimum=2,
        maximum=2,
    )
    checked = tuple(
        _coordinate(value, name="projection[%d]" % index)
        for index, value in enumerate(values)
    )
    squared_norm = math.fsum(value * value for value in checked)
    if squared_norm <= 0.0 or not math.isfinite(squared_norm):
        raise ValueError("projection must be finite and nonzero")
    variance = math.fsum(
        coefficient * coefficient * coordinate_variance
        for coefficient, coordinate_variance in zip(
            checked,
            _M2_TYPE2_VARIANCES,
        )
    )
    return ProjectionMoment(
        projection=(checked[0], checked[1]),
        squared_norm=squared_norm,
        mean=0.0,
        second_moment=variance,
        variance=variance,
    )


def finite_categorical_tv_bound(
    expected_probabilities: object,
    observed_counts: object,
    *,
    alpha: object = CP50_TEST28_PER_GATE_ALPHA,
) -> FiniteCategoricalTVBound:
    """Return empirical TV and a simultaneous finite-category upper bound.

    Coverage requires the external premise that the observations are IID draws
    from one fixed categorical law; this utility neither tests nor certifies
    that premise.

    The coordinate-wise Hoeffding union bound gives

    ``max_i |p_hat_i - p_i| <= sqrt(log(2K/alpha)/(2n))``.

    Consequently the unknown-law-to-target TV is at most the empirical TV
    plus ``K/2`` times that radius, capped at one.  This is intended only for
    finite categories, never continuous empirical measures.
    """

    expected = _probability_table(expected_probabilities, name="expected_probabilities")
    counts = _count_tuple(observed_counts, name="observed_counts")
    if len(expected) != len(counts):
        raise ValueError("expected probabilities and counts differ in length")
    sample_size = sum(counts)
    _exact_integer(
        sample_size,
        name="sample_size",
        minimum=1,
        maximum=_MAX_BINOMIAL_TRIALS,
    )
    checked_alpha = _alpha(alpha)
    empirical = tuple(value / sample_size for value in counts)
    empirical_tv = 0.5 * math.fsum(
        abs(actual - target) for actual, target in zip(empirical, expected)
    )
    radius = min(
        1.0,
        math.sqrt(math.log(2.0 * len(expected) / checked_alpha) / (2.0 * sample_size)),
    )
    tv_radius = min(1.0, 0.5 * len(expected) * radius)
    upper = min(1.0, empirical_tv + tv_radius)
    return FiniteCategoricalTVBound(
        category_count=len(expected),
        sample_size=sample_size,
        expected_probabilities=expected,
        observed_counts=counts,
        empirical_probabilities=empirical,
        empirical_total_variation=empirical_tv,
        alpha=checked_alpha,
        simultaneous_linf_radius=radius,
        total_variation_radius=tv_radius,
        total_variation_upper_bound=upper,
    )


def dkw_radius(
    sample_size: object,
    *,
    alpha: object = CP50_TEST28_PER_GATE_ALPHA,
) -> float:
    """Return the two-sided Dvoretzky--Kiefer--Wolfowitz radius."""

    count = _exact_integer(
        sample_size,
        name="sample_size",
        minimum=1,
        maximum=_MAX_SAMPLES,
    )
    checked_alpha = _alpha(alpha)
    return min(1.0, math.sqrt(math.log(2.0 / checked_alpha) / (2.0 * count)))


def ks_dkw_bound(
    samples: object,
    target_cdf: object,
    *,
    alpha: object = CP50_TEST28_PER_GATE_ALPHA,
) -> KSDKWBound:
    """Evaluate a one-dimensional empirical KS discrepancy and DKW bound.

    DKW coverage requires IID samples from one fixed law.  The callable must
    return an exact built-in float from an analytic CDF.  Numerical-quadrature
    records are rejected because their error estimate is not propagated here.
    """

    values = _exact_tuple(
        samples,
        name="samples",
        minimum=1,
        maximum=_MAX_SAMPLES,
    )
    checked_samples = tuple(
        _exact_float(value, name="samples[%d]" % index)
        for index, value in enumerate(values)
    )
    if not callable(target_cdf):
        raise TypeError("target_cdf must be callable")
    ordered = tuple(sorted(checked_samples))
    sample_size = len(ordered)
    maximum = 0.0
    for index, value in enumerate(ordered, start=1):
        raw_cdf = target_cdf(value)  # type: ignore[operator]
        cdf = _probability(raw_cdf, name="target_cdf return")
        lower_jump = (index - 1) / sample_size
        upper_jump = index / sample_size
        maximum = max(maximum, cdf - lower_jump, upper_jump - cdf)
    if maximum < 0.0 or maximum > 1.0 or not math.isfinite(maximum):
        raise ArithmeticError("empirical KS discrepancy is invalid")
    checked_alpha = _alpha(alpha)
    radius = dkw_radius(sample_size, alpha=checked_alpha)
    return KSDKWBound(
        sample_size=sample_size,
        empirical_ks=maximum,
        alpha=checked_alpha,
        dkw_radius=radius,
        cdf_distance_upper_bound=min(1.0, maximum + radius),
    )


def clopper_pearson_interval(
    successes: object,
    trials: object,
    *,
    alpha: object = CP50_TEST28_PER_GATE_ALPHA,
) -> BinomialConfidenceInterval:
    """Return an equal-tailed two-sided Clopper--Pearson interval.

    Its coverage statement requires the external fixed-probability independent
    Bernoulli-trial premise; the arithmetic does not establish that premise.
    """

    checked_trials = _exact_integer(
        trials,
        name="trials",
        minimum=1,
        maximum=_MAX_BINOMIAL_TRIALS,
    )
    checked_successes = _exact_integer(
        successes,
        name="successes",
        minimum=0,
        maximum=checked_trials,
    )
    checked_alpha = _alpha(alpha)
    half_alpha = 0.5 * checked_alpha
    if checked_successes == 0:
        lower = 0.0
    else:
        lower = float(
            betaincinv(
                checked_successes,
                checked_trials - checked_successes + 1,
                half_alpha,
            )
        )
    if checked_successes == checked_trials:
        upper = 1.0
    else:
        upper = float(
            betaincinv(
                checked_successes + 1,
                checked_trials - checked_successes,
                1.0 - half_alpha,
            )
        )
    if not (
        math.isfinite(lower) and math.isfinite(upper) and 0.0 <= lower <= upper <= 1.0
    ):
        raise ArithmeticError("Clopper-Pearson interval is invalid")
    return BinomialConfidenceInterval(
        successes=checked_successes,
        trials=checked_trials,
        alpha=checked_alpha,
        estimate=checked_successes / checked_trials,
        lower=lower,
        upper=upper,
    )


def rejection_exhaustion_probability(
    acceptance_probability: object,
    attempt_cap: object,
) -> float:
    """Return ``(1 - acceptance_probability) ** attempt_cap`` stably."""

    acceptance = _probability(
        acceptance_probability,
        name="acceptance_probability",
    )
    attempts = _exact_integer(
        attempt_cap,
        name="attempt_cap",
        minimum=1,
        maximum=_MAX_REJECTION_ATTEMPTS,
    )
    if acceptance == 0.0:
        return 1.0
    if acceptance == 1.0:
        return 0.0
    log_result = attempts * math.log1p(-acceptance)
    result = math.exp(log_result)
    if result == 0.0:
        raise ArithmeticError(
            "positive rejection exhaustion probability underflowed to zero"
        )
    if not math.isfinite(result) or result < 0.0 or result > 1.0:
        raise ArithmeticError("rejection exhaustion probability is invalid")
    return result


def rejection_exhaustion_binomial_check(
    *,
    attempt_cap: object,
    request_count: object,
    exhaustion_count: object,
    acceptance_probability: object,
    alpha: object = CP50_TEST28_PER_GATE_ALPHA,
) -> RejectionExhaustionCheck:
    """Compare observed exhaustion with the ideal bounded-rejection law.

    The ideal prediction presumes IID proposals, independent decision
    uniforms, an exact envelope, and exact comparisons.  Operational uint64
    thresholding needs a separately supplied prediction and is not certified
    by this helper.
    """

    attempts = _exact_integer(
        attempt_cap,
        name="attempt_cap",
        minimum=1,
        maximum=_MAX_REJECTION_ATTEMPTS,
    )
    requests = _exact_integer(
        request_count,
        name="request_count",
        minimum=1,
        maximum=_MAX_BINOMIAL_TRIALS,
    )
    exhausted = _exact_integer(
        exhaustion_count,
        name="exhaustion_count",
        minimum=0,
        maximum=requests,
    )
    acceptance = _probability(
        acceptance_probability,
        name="acceptance_probability",
    )
    interval = clopper_pearson_interval(
        exhausted,
        requests,
        alpha=alpha,
    )
    expected = rejection_exhaustion_probability(acceptance, attempts)
    return RejectionExhaustionCheck(
        attempt_cap=attempts,
        request_count=requests,
        exhaustion_count=exhausted,
        acceptance_probability=acceptance,
        expected_exhaustion_probability=expected,
        confidence_interval=interval,
        expected_probability_inside_interval=(
            interval.lower <= expected <= interval.upper
        ),
    )


def ess_summary(weights: object) -> ESSSummary:
    """Return a scale-stable ESS/entropy summary for positive SIR weights."""

    values = _exact_tuple(
        weights,
        name="weights",
        minimum=1,
        maximum=_MAX_PARTICLES,
    )
    checked = tuple(
        _positive_float(value, name="weights[%d]" % index)
        for index, value in enumerate(values)
    )
    maximum = max(checked)
    minimum = min(checked)
    scaled = tuple(value / maximum for value in checked)
    if any(value <= 0.0 for value in scaled):
        raise ArithmeticError("scaled SIR weight underflowed to zero")
    total = math.fsum(scaled)
    squared = math.fsum(value * value for value in scaled)
    if not math.isfinite(total) or not math.isfinite(squared):
        raise ArithmeticError("scaled SIR weight sums are nonfinite")
    if total <= 0.0 or squared <= 0.0:
        raise ArithmeticError("scaled SIR weight sums are nonpositive")
    probabilities = tuple(value / total for value in scaled)
    if any(probability <= 0.0 for probability in probabilities):
        raise ArithmeticError("normalized SIR probability underflowed to zero")
    raw_ess = total * total / squared
    tolerance = 64.0 * sys.float_info.epsilon * len(checked)
    if raw_ess > len(checked) * (1.0 + tolerance):
        raise ArithmeticError("computed ESS exceeds its analytic bound")
    ess = min(float(len(checked)), raw_ess)
    entropy = -math.fsum(
        probability * math.log(probability) for probability in probabilities
    )
    perplexity = math.exp(entropy)
    return ESSSummary(
        particle_count=len(checked),
        minimum_weight=minimum,
        maximum_weight=maximum,
        effective_sample_size=ess,
        effective_sample_size_fraction=ess / len(checked),
        maximum_normalized_weight=max(probabilities),
        normalized_weight_entropy=entropy,
        perplexity=perplexity,
    )


__all__ = [
    "CP50_TEST28_ORACLE_SCHEMA_VERSION",
    "CP50_TEST28_ORACLE_SCOPE",
    "CP50_TEST28_FAMILYWISE_ALPHA",
    "CP50_TEST28_GATE_SLOTS",
    "CP50_TEST28_PER_GATE_ALPHA",
    "AtomicA0Fixture",
    "MixedM1Fixture",
    "MixedM2Fixture",
    "QuadratureCDFResult",
    "ExactRationalQuadraticScoreEvaluation",
    "M2CountTypeMoments",
    "ProjectionMoment",
    "FiniteCategoricalTVBound",
    "KSDKWBound",
    "BinomialConfidenceInterval",
    "RejectionExhaustionCheck",
    "ESSSummary",
    "atomic_a0_fixture",
    "mixed_m1_fixture",
    "mixed_m2_fixture",
    "m1_exact_rational_score",
    "m2_exact_rational_score",
    "m1_continuous_target_density",
    "m1_continuous_target_cdf",
    "m1_continuous_target_cdf_quadrature",
    "m2_type1_target_density",
    "m2_type1_target_cdf",
    "m2_type1_target_cdf_quadrature",
    "m2_type2_coordinate_target_density",
    "m2_type2_coordinate_target_cdf",
    "m2_type2_coordinate_target_cdf_quadrature",
    "m2_count_type_moments",
    "m2_type2_projection_moment",
    "finite_categorical_tv_bound",
    "dkw_radius",
    "ks_dkw_bound",
    "clopper_pearson_interval",
    "rejection_exhaustion_probability",
    "rejection_exhaustion_binomial_check",
    "ess_summary",
]
