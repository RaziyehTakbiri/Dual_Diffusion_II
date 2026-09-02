"""Finite acyclic qualification oracle for Formal Test 29.

Formal Test 29 requires a certified thinning construction to recover exact
tilted total rates, edit-family probabilities, and continuous destination
laws.  Checkpoints nineteen through twenty-four deliberately stop at a
finite-resolution, bounded-successful-return execution boundary.  This module
adds a pure exact-arithmetic qualification layer for a narrower class of
fixtures without modifying those frozen parents.

For a finite acyclic fixture it provides four deliberately separated objects:

* an exact rational tilted-rate and route/source disintegration;
* an ideal Gaussian destination descriptor, with exact polynomial moments;
* the exact pushforward of one uniformly distributed uint64 word into route,
  source-index, and normal-quantile *cells*; and
* a CP24-layout-compatible address-consuming lineage execution that reaches a
  terminal state in at most the initial rank for every supplied word tape.

The normal cell is not a real-valued Gaussian sample.  A bounded finite word
has finite support and therefore cannot have a non-atomic Gaussian law.  The
module makes that obstruction an explicit negative certificate flag.  It
closes only the finite-acyclic route/cell/lineage/completion qualification
predicate; it does not close Formal Test 29 or admit a production sampler.

No entropy, NumPy generator, model, data, filesystem, network, clock, or
scientific execution is used.  All stochastic statements are pushforward
statements under explicitly stated abstract uniform-word or ideal-Gaussian
premises.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from statistics import NormalDist
from typing import Dict, Mapping, Optional, Sequence, Tuple


FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION = (
    "formal-test29-finite-acyclic-route-oracle-v1"
)
FORMAL_TEST29_FINITE_ACYCLIC_POLICY = (
    "4096-bit-exact-fraction-component-guard;"
    "exact-rational-tilted-rates;dyadic-route-and-source-partitions;"
    "one-uint64-word-per-accepted-fixture-jump;fixed-normal-quantile-cells;"
    "cp24-tag6-direct-address-layout;fresh-monotone-lineage;"
    "strict-rank-decrease-unconditional-bounded-completion-v1"
)
FORMAL_TEST29_FINITE_ACYCLIC_SCOPE = (
    "finite-declared-acyclic-quadrature-fixtures;abstract-uniform-uint64-law;"
    "ideal-gaussian-disintegration-separated-from-finite-word-pushforward;"
    "exact-route-family-source-and-normal-cell-laws;"
    "not-continuous-gaussian-from-bounded-words;not-cp24-live-philox;"
    "not-waiting-clock;not-acceptance-thinning;not-cyclic-liveness;"
    "not-production-path;not-formal-test29-closure;not-scientific-execution"
)

CP24_OPERATIONAL_EPOCH_DOMAIN_TAG = 6
CP24_OPERATIONAL_EPOCH_MAX_PROPOSALS = 64
UINT64_MODULUS = 1 << 64
MAX_ENUMERATED_LOW_WORD_BITS = 16
MAX_EXACT_FRACTION_COMPONENT_BITS = 4_096
MAX_FIXTURE_STATES = 128
MAX_FIXTURE_ROUTES_PER_STATE = 64
MAX_FIXTURE_RANK = 64
MAX_FIXTURE_LINEAGES = 128
MAX_GAUSSIAN_DIMENSION = 16

FAMILY_BIRTH = "birth"
FAMILY_DEATH = "death"
FAMILY_REPLACEMENT = "replacement"
EDIT_FAMILIES = (FAMILY_BIRTH, FAMILY_DEATH, FAMILY_REPLACEMENT)


class FormalTest29FiniteAcyclicError(ValueError):
    """Raised when a finite qualification fixture is outside its contract."""


def _exact_int(value: object, *, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s must lie in [%d, %d]" % (name, minimum, maximum))
    return value


def _exact_fraction(
    value: object,
    *,
    name: str,
    positive: bool = False,
    nonnegative: bool = False,
) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError("%s must be an exact Fraction" % name)
    if (
        value.numerator.bit_length() > MAX_EXACT_FRACTION_COMPONENT_BITS
        or value.denominator.bit_length() > MAX_EXACT_FRACTION_COMPONENT_BITS
    ):
        raise ValueError(
            "%s numerator or denominator exceeds the %d-bit exact-component guard"
            % (name, MAX_EXACT_FRACTION_COMPONENT_BITS)
        )
    if positive and value <= 0:
        raise ValueError("%s must be positive" % name)
    if nonnegative and value < 0:
        raise ValueError("%s must be nonnegative" % name)
    return value


def _bounded_fraction_result(value: Fraction, *, name: str) -> Fraction:
    """Guard every derived exact numerator and denominator before reuse."""

    return _exact_fraction(value, name=name)


def _fraction_add(left: Fraction, right: Fraction, *, name: str) -> Fraction:
    _exact_fraction(left, name=name + "_left")
    _exact_fraction(right, name=name + "_right")
    return _bounded_fraction_result(left + right, name=name)


def _fraction_multiply(left: Fraction, right: Fraction, *, name: str) -> Fraction:
    _exact_fraction(left, name=name + "_left")
    _exact_fraction(right, name=name + "_right")
    return _bounded_fraction_result(left * right, name=name)


def _fraction_divide(left: Fraction, right: Fraction, *, name: str) -> Fraction:
    _exact_fraction(left, name=name + "_left")
    _exact_fraction(right, name=name + "_right", positive=True)
    return _bounded_fraction_result(left / right, name=name)


def _fraction_power(value: Fraction, exponent: int, *, name: str) -> Fraction:
    _exact_fraction(value, name=name + "_base")
    exponent = _exact_int(exponent, name=name + "_exponent", minimum=0, maximum=4)
    result = Fraction(1, 1)
    for index in range(exponent):
        result = _fraction_multiply(result, value, name="%s_step_%d" % (name, index))
    return result


def _fraction_sum(values: Sequence[Fraction], *, name: str) -> Fraction:
    result = Fraction(0, 1)
    for index, value in enumerate(values):
        result = _fraction_add(result, value, name="%s_step_%d" % (name, index))
    return result


def _bounded_identifier(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be a string" % name)
    if not value or len(value) > 96:
        raise ValueError("%s must contain 1--96 characters" % name)
    if any(not (character.isalnum() or character in "-_.") for character in value):
        raise ValueError("%s contains a noncanonical character" % name)
    return value


def _tuple_exact(value: object, *, name: str) -> tuple:
    if type(value) is not tuple:
        raise TypeError("%s must be a tuple" % name)
    return value


def _dyadic_bucket_counts(
    masses: Sequence[Fraction], *, bits: int, name: str
) -> Tuple[int, ...]:
    bits = _exact_int(bits, name=name + "_bits", minimum=0, maximum=64)
    denominator = 1 << bits
    if not masses:
        raise ValueError("%s must be nonempty" % name)
    counts = []
    total = Fraction(0, 1)
    for index, mass in enumerate(masses):
        checked = _exact_fraction(mass, name="%s[%d]" % (name, index), nonnegative=True)
        scaled = _bounded_fraction_result(
            checked * denominator, name="%s[%d]_scaled" % (name, index)
        )
        if scaled.denominator != 1:
            raise ValueError("%s is not representable with %d bits" % (name, bits))
        counts.append(scaled.numerator)
        total = _fraction_add(total, checked, name=name + "_total")
    if total != 1:
        raise ValueError("%s must sum exactly to one" % name)
    if sum(counts) != denominator:
        raise AssertionError("dyadic count conservation failed")
    return tuple(counts)


def _select_bucket(counts: Sequence[int], code: int) -> int:
    if type(code) is not int:
        raise TypeError("bucket code must be an exact integer")
    total = sum(counts)
    if not 0 <= code < total:
        raise ValueError("bucket code lies outside its partition")
    cursor = 0
    for index, count in enumerate(counts):
        cursor += count
        if code < cursor:
            return index
    raise AssertionError("complete bucket partition did not select")


def _sorted_mass_items(values: Mapping[object, Fraction]) -> tuple:
    return tuple(sorted(values.items(), key=lambda item: repr(item[0])))


@dataclass(frozen=True)
class GaussianDestination:
    """An exact diagonal-Gaussian law descriptor.

    ``variance`` stores variance, not standard deviation.  Fractions make the
    first four raw moments exact; no numerical Gaussian draw occurs here.
    """

    mean: Tuple[Fraction, ...]
    variance: Tuple[Fraction, ...]

    def __post_init__(self) -> None:
        means = _tuple_exact(self.mean, name="mean")
        variances = _tuple_exact(self.variance, name="variance")
        if not 1 <= len(means) <= MAX_GAUSSIAN_DIMENSION:
            raise ValueError("Gaussian dimension lies outside the fixture guard")
        if len(variances) != len(means):
            raise ValueError("mean and variance dimensions differ")
        for index, value in enumerate(means):
            _exact_fraction(value, name="mean[%d]" % index)
        for index, value in enumerate(variances):
            _exact_fraction(value, name="variance[%d]" % index, positive=True)

    @property
    def dimension(self) -> int:
        return len(self.mean)

    def raw_moment(self, coordinate: int, order: int) -> Fraction:
        """Return the exact marginal raw moment for order zero through four."""

        coordinate = _exact_int(
            coordinate,
            name="coordinate",
            minimum=0,
            maximum=self.dimension - 1,
        )
        order = _exact_int(order, name="order", minimum=0, maximum=4)
        mean = self.mean[coordinate]
        variance = self.variance[coordinate]
        if order == 0:
            return Fraction(1, 1)
        if order == 1:
            return mean
        if order == 2:
            return _fraction_add(
                _fraction_power(mean, 2, name="gaussian_mean_squared"),
                variance,
                name="gaussian_raw_moment_2",
            )
        if order == 3:
            mean_variance = _fraction_multiply(
                mean, variance, name="gaussian_mean_variance"
            )
            correction = _fraction_multiply(
                Fraction(3), mean_variance, name="gaussian_third_correction"
            )
            return _fraction_add(
                _fraction_power(mean, 3, name="gaussian_mean_cubed"),
                correction,
                name="gaussian_raw_moment_3",
            )
        mean_squared = _fraction_power(mean, 2, name="gaussian_mean_squared")
        mean_squared_variance = _fraction_multiply(
            mean_squared, variance, name="gaussian_mean_squared_variance"
        )
        second_term = _fraction_multiply(
            Fraction(6), mean_squared_variance, name="gaussian_fourth_second_term"
        )
        variance_squared = _fraction_power(
            variance, 2, name="gaussian_variance_squared"
        )
        third_term = _fraction_multiply(
            Fraction(3), variance_squared, name="gaussian_fourth_third_term"
        )
        first_two = _fraction_add(
            _fraction_power(mean, 4, name="gaussian_mean_fourth"),
            second_term,
            name="gaussian_fourth_first_two",
        )
        return _fraction_add(first_two, third_term, name="gaussian_raw_moment_4")


@dataclass(frozen=True)
class NormalQuantileCell:
    """One equiprobable standard-normal quantile cell selected by word bits."""

    index: int
    bits: int

    def __post_init__(self) -> None:
        bits = _exact_int(self.bits, name="bits", minimum=1, maximum=16)
        _exact_int(
            self.index,
            name="index",
            minimum=0,
            maximum=(1 << bits) - 1,
        )

    @property
    def probability(self) -> Fraction:
        return Fraction(1, 1 << self.bits)

    @property
    def lower_probability(self) -> Fraction:
        return Fraction(self.index, 1 << self.bits)

    @property
    def upper_probability(self) -> Fraction:
        return Fraction(self.index + 1, 1 << self.bits)

    def standard_normal_bounds(self) -> Tuple[float, float]:
        """Return numerical quantile bounds for an independent CDF check."""

        distribution = NormalDist()
        lower = (
            -math.inf
            if self.index == 0
            else distribution.inv_cdf(float(self.lower_probability))
        )
        upper = (
            math.inf
            if self.index + 1 == 1 << self.bits
            else distribution.inv_cdf(float(self.upper_probability))
        )
        return lower, upper

    def midpoint_representative(self) -> float:
        """Return a finite binary64 representative, not a Gaussian draw."""

        midpoint = Fraction(2 * self.index + 1, 2 * (1 << self.bits))
        value = NormalDist().inv_cdf(float(midpoint))
        if not math.isfinite(value):
            raise ArithmeticError("normal-cell midpoint is non-finite")
        return value

    def cdf_mass_residual(self) -> float:
        """Numerically cross-check the defining standard-normal cell mass."""

        lower, upper = self.standard_normal_bounds()
        distribution = NormalDist()
        lower_cdf = 0.0 if lower == -math.inf else distribution.cdf(lower)
        upper_cdf = 1.0 if upper == math.inf else distribution.cdf(upper)
        return abs((upper_cdf - lower_cdf) - float(self.probability))


@dataclass(frozen=True)
class WordLayout:
    """Fixed low-bit partition of one consumed uint64 word."""

    route_bits: int
    source_bits: int
    normal_bits: int
    maximum_normal_dimension: int

    def __post_init__(self) -> None:
        route_bits = _exact_int(
            self.route_bits, name="route_bits", minimum=0, maximum=16
        )
        source_bits = _exact_int(
            self.source_bits, name="source_bits", minimum=0, maximum=16
        )
        normal_bits = _exact_int(
            self.normal_bits, name="normal_bits", minimum=1, maximum=16
        )
        dimension = _exact_int(
            self.maximum_normal_dimension,
            name="maximum_normal_dimension",
            minimum=1,
            maximum=MAX_GAUSSIAN_DIMENSION,
        )
        if route_bits + source_bits + normal_bits * dimension > 64:
            raise ValueError("word layout exceeds one uint64 word")

    @property
    def used_bits(self) -> int:
        return (
            self.route_bits
            + self.source_bits
            + self.normal_bits * self.maximum_normal_dimension
        )

    @property
    def low_word_count(self) -> int:
        return 1 << self.used_bits


@dataclass(frozen=True)
class RouteSpec:
    """One edit route with exact base/tilt factors and conditional laws."""

    route_id: str
    family: str
    next_state_id: str
    base_rate: Fraction
    tilt: Fraction
    source_masses: Tuple[Fraction, ...]
    gaussian_destination: Optional[GaussianDestination]

    def __post_init__(self) -> None:
        _bounded_identifier(self.route_id, name="route_id")
        _bounded_identifier(self.next_state_id, name="next_state_id")
        if type(self.family) is not str or self.family not in EDIT_FAMILIES:
            raise ValueError("family must be birth, death, or replacement")
        _exact_fraction(self.base_rate, name="base_rate", positive=True)
        _exact_fraction(self.tilt, name="tilt", positive=True)
        source_masses = _tuple_exact(self.source_masses, name="source_masses")
        for index, mass in enumerate(source_masses):
            _exact_fraction(mass, name="source_masses[%d]" % index, positive=True)
        if self.family == FAMILY_BIRTH:
            if source_masses:
                raise ValueError("birth routes cannot select a source")
        else:
            if (
                not source_masses
                or _fraction_sum(source_masses, name="source_mass_total") != 1
            ):
                raise ValueError("death/replacement source masses must sum to one")
        if self.family == FAMILY_DEATH:
            if self.gaussian_destination is not None:
                raise ValueError("death routes cannot have a Gaussian destination")
        elif type(self.gaussian_destination) is not GaussianDestination:
            raise TypeError("birth/replacement routes require a Gaussian destination")
        _ = self.tilted_rate

    @property
    def tilted_rate(self) -> Fraction:
        return _fraction_multiply(self.base_rate, self.tilt, name="route_tilted_rate")


@dataclass(frozen=True)
class StateSpec:
    """One state in a finite strictly rank-decreasing fixture graph."""

    state_id: str
    rank: int
    lineage_cardinality: int
    routes: Tuple[RouteSpec, ...]

    def __post_init__(self) -> None:
        _bounded_identifier(self.state_id, name="state_id")
        rank = _exact_int(self.rank, name="rank", minimum=0, maximum=MAX_FIXTURE_RANK)
        _exact_int(
            self.lineage_cardinality,
            name="lineage_cardinality",
            minimum=0,
            maximum=MAX_FIXTURE_LINEAGES,
        )
        routes = _tuple_exact(self.routes, name="routes")
        if len(routes) > MAX_FIXTURE_ROUTES_PER_STATE:
            raise ValueError("state route count exceeds the fixture guard")
        if any(type(route) is not RouteSpec for route in routes):
            raise TypeError("routes must contain exact RouteSpec objects")
        route_ids = tuple(route.route_id for route in routes)
        if len(set(route_ids)) != len(route_ids):
            raise ValueError("route identifiers must be unique within a state")
        if rank == 0 and routes:
            raise ValueError("rank-zero states must be terminal")
        if rank > 0 and not routes:
            raise ValueError("positive-rank states must expose a route")

    @property
    def total_tilted_rate(self) -> Fraction:
        return _fraction_sum(
            tuple(route.tilted_rate for route in self.routes),
            name="total_tilted_rate",
        )

    def route_masses(self) -> Tuple[Fraction, ...]:
        total = self.total_tilted_rate
        if total <= 0:
            raise ArithmeticError("active state has nonpositive total tilted rate")
        return tuple(
            _fraction_divide(route.tilted_rate, total, name="normalized_route_mass")
            for route in self.routes
        )


@dataclass(frozen=True)
class FixtureSpec:
    """An immutable finite acyclic frozen-jump qualification fixture."""

    fixture_id: str
    states: Tuple[StateSpec, ...]
    initial_state_id: str
    layout: WordLayout

    def __post_init__(self) -> None:
        _bounded_identifier(self.fixture_id, name="fixture_id")
        states = _tuple_exact(self.states, name="states")
        if not 1 <= len(states) <= MAX_FIXTURE_STATES:
            raise ValueError("fixture state count lies outside the guard")
        if any(type(state) is not StateSpec for state in states):
            raise TypeError("states must contain exact StateSpec objects")
        if type(self.layout) is not WordLayout:
            raise TypeError("layout must be an exact WordLayout")
        ids = tuple(state.state_id for state in states)
        if len(set(ids)) != len(ids):
            raise ValueError("fixture state identifiers must be unique")
        _bounded_identifier(self.initial_state_id, name="initial_state_id")
        by_id = {state.state_id: state for state in states}
        if self.initial_state_id not in by_id:
            raise ValueError("initial_state_id is absent from states")
        for state in states:
            if state.rank == 0:
                continue
            _dyadic_bucket_counts(
                state.route_masses(), bits=self.layout.route_bits, name="route_masses"
            )
            for route in state.routes:
                if route.next_state_id not in by_id:
                    raise ValueError("route destination state is absent")
                destination = by_id[route.next_state_id]
                if destination.rank >= state.rank:
                    raise ValueError("every route must strictly decrease rank")
                expected_cardinality = state.lineage_cardinality
                if route.family == FAMILY_BIRTH:
                    expected_cardinality += 1
                elif route.family == FAMILY_DEATH:
                    expected_cardinality -= 1
                if expected_cardinality < 0:
                    raise ValueError("death route underflows lineage cardinality")
                if destination.lineage_cardinality != expected_cardinality:
                    raise ValueError(
                        "route and destination lineage cardinalities differ"
                    )
                if route.family != FAMILY_BIRTH:
                    if len(route.source_masses) != state.lineage_cardinality:
                        raise ValueError("source masses do not cover current lineages")
                    _dyadic_bucket_counts(
                        route.source_masses,
                        bits=self.layout.source_bits,
                        name="source_masses",
                    )
                gaussian = route.gaussian_destination
                if gaussian is not None:
                    if gaussian.dimension > self.layout.maximum_normal_dimension:
                        raise ValueError("Gaussian dimension exceeds the word layout")

    def state(self, state_id: str) -> StateSpec:
        _bounded_identifier(state_id, name="state_id")
        for state in self.states:
            if state.state_id == state_id:
                return state
        raise ValueError("unknown fixture state")

    @property
    def initial_state(self) -> StateSpec:
        return self.state(self.initial_state_id)


@dataclass(frozen=True)
class IdealRouteSourceAtom:
    """One exact route/source atom with an optional ideal Gaussian fiber."""

    route_id: str
    family: str
    source_index: Optional[int]
    mass: Fraction
    gaussian_destination: Optional[GaussianDestination]


@dataclass(frozen=True)
class IdealOneStepLaw:
    """Exact rational disintegration of one accepted frozen jump."""

    state_id: str
    total_tilted_rate: Fraction
    route_masses: Tuple[Tuple[str, Fraction], ...]
    family_masses: Tuple[Tuple[str, Fraction], ...]
    atoms: Tuple[IdealRouteSourceAtom, ...]


def ideal_one_step_law(fixture: FixtureSpec, state_id: str) -> IdealOneStepLaw:
    """Construct the exact conditional jump law for one active fixture state."""

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    state = fixture.state(state_id)
    if state.rank == 0:
        raise ValueError("a terminal state has no one-step jump law")
    route_masses = state.route_masses()
    family = {name: Fraction(0, 1) for name in EDIT_FAMILIES}
    atoms = []
    for route, route_mass in zip(state.routes, route_masses):
        family[route.family] = _fraction_add(
            family[route.family], route_mass, name="family_mass"
        )
        if route.family == FAMILY_BIRTH:
            atoms.append(
                IdealRouteSourceAtom(
                    route.route_id,
                    route.family,
                    None,
                    route_mass,
                    route.gaussian_destination,
                )
            )
        else:
            for source_index, source_mass in enumerate(route.source_masses):
                atoms.append(
                    IdealRouteSourceAtom(
                        route.route_id,
                        route.family,
                        source_index,
                        _fraction_multiply(
                            route_mass, source_mass, name="route_source_mass"
                        ),
                        route.gaussian_destination,
                    )
                )
    if (
        _fraction_sum(tuple(atom.mass for atom in atoms), name="ideal_atom_mass_total")
        != 1
    ):
        raise AssertionError("ideal route/source disintegration does not normalize")
    return IdealOneStepLaw(
        state_id=state.state_id,
        total_tilted_rate=state.total_tilted_rate,
        route_masses=tuple(
            (route.route_id, mass) for route, mass in zip(state.routes, route_masses)
        ),
        family_masses=tuple((name, family[name]) for name in EDIT_FAMILIES),
        atoms=tuple(atoms),
    )


@dataclass(frozen=True)
class DecodedWord:
    """Total low-bit interpretation of one supplied uint64 word."""

    raw64_word: int
    low_word: int
    route_code: int
    source_code: int
    normal_codes: Tuple[int, ...]


def decode_uint64_word(layout: WordLayout, raw64_word: int) -> DecodedWord:
    """Decode one word without randomness or rejection."""

    if type(layout) is not WordLayout:
        raise TypeError("layout must be an exact WordLayout")
    raw64_word = _exact_int(
        raw64_word, name="raw64_word", minimum=0, maximum=UINT64_MODULUS - 1
    )
    low_mask = (1 << layout.used_bits) - 1
    low_word = raw64_word & low_mask
    cursor = low_word
    route_mask = (1 << layout.route_bits) - 1
    route_code = cursor & route_mask
    cursor >>= layout.route_bits
    source_mask = (1 << layout.source_bits) - 1
    source_code = cursor & source_mask
    cursor >>= layout.source_bits
    normal_mask = (1 << layout.normal_bits) - 1
    normal_codes = []
    for _ in range(layout.maximum_normal_dimension):
        normal_codes.append(cursor & normal_mask)
        cursor >>= layout.normal_bits
    if cursor != 0:
        raise AssertionError("word layout failed to consume its declared low bits")
    return DecodedWord(
        raw64_word=raw64_word,
        low_word=low_word,
        route_code=route_code,
        source_code=source_code,
        normal_codes=tuple(normal_codes),
    )


@dataclass(frozen=True)
class OperationalOneStepSelection:
    """One exact finite-word route/source/normal-cell selection."""

    state_id: str
    route_id: str
    family: str
    next_state_id: str
    source_index: Optional[int]
    normal_cells: Tuple[NormalQuantileCell, ...]
    decoded_word: DecodedWord


def select_one_step(
    fixture: FixtureSpec, state_id: str, raw64_word: int
) -> OperationalOneStepSelection:
    """Apply the exact dyadic one-word map at an active fixture state."""

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    state = fixture.state(state_id)
    if state.rank == 0:
        raise ValueError("a terminal state cannot consume a route word")
    decoded = decode_uint64_word(fixture.layout, raw64_word)
    route_counts = _dyadic_bucket_counts(
        state.route_masses(), bits=fixture.layout.route_bits, name="route_masses"
    )
    route_index = _select_bucket(route_counts, decoded.route_code)
    route = state.routes[route_index]
    source_index = None
    if route.family != FAMILY_BIRTH:
        source_counts = _dyadic_bucket_counts(
            route.source_masses,
            bits=fixture.layout.source_bits,
            name="source_masses",
        )
        source_index = _select_bucket(source_counts, decoded.source_code)
    gaussian = route.gaussian_destination
    normal_cells = ()
    if gaussian is not None:
        normal_cells = tuple(
            NormalQuantileCell(decoded.normal_codes[index], fixture.layout.normal_bits)
            for index in range(gaussian.dimension)
        )
    return OperationalOneStepSelection(
        state_id=state.state_id,
        route_id=route.route_id,
        family=route.family,
        next_state_id=route.next_state_id,
        source_index=source_index,
        normal_cells=normal_cells,
        decoded_word=decoded,
    )


@dataclass(frozen=True)
class OperationalPushforwardLaw:
    """Exact finite pushforward law of the low-word residue map."""

    state_id: str
    total_low_words: int
    route_masses: Tuple[Tuple[str, Fraction], ...]
    source_joint_masses: Tuple[Tuple[Tuple[str, int], Fraction], ...]
    normal_cell_joint_masses: Tuple[Tuple[Tuple[str, int, int], Fraction], ...]
    raw64_words_consumed_per_jump: int


def operational_pushforward_law(
    fixture: FixtureSpec, state_id: str
) -> OperationalPushforwardLaw:
    """Return the exact law induced by a uniform uint64 word.

    The map depends only on ``used_bits`` low bits.  Every low residue has
    exactly ``2**(64-used_bits)`` uint64 preimages, so enumerating low residues
    is an exact proof rather than a Monte Carlo approximation.
    """

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    state = fixture.state(state_id)
    if state.rank == 0:
        raise ValueError("a terminal state has no operational pushforward")
    route_masses = state.route_masses()
    route_values = tuple(
        (route.route_id, mass) for route, mass in zip(state.routes, route_masses)
    )
    source_values: Dict[Tuple[str, int], Fraction] = {}
    normal_values: Dict[Tuple[str, int, int], Fraction] = {}
    normal_cell_mass = Fraction(1, 1 << fixture.layout.normal_bits)
    for route, route_mass in zip(state.routes, route_masses):
        if route.family != FAMILY_BIRTH:
            for source_index, source_mass in enumerate(route.source_masses):
                source_values[(route.route_id, source_index)] = _fraction_multiply(
                    route_mass, source_mass, name="operational_route_source_mass"
                )
        gaussian = route.gaussian_destination
        if gaussian is not None:
            for coordinate in range(gaussian.dimension):
                for cell in range(1 << fixture.layout.normal_bits):
                    normal_values[
                        (route.route_id, coordinate, cell)
                    ] = _fraction_multiply(
                        route_mass,
                        normal_cell_mass,
                        name="operational_route_normal_cell_mass",
                    )
    return OperationalPushforwardLaw(
        state_id=state.state_id,
        total_low_words=fixture.layout.low_word_count,
        route_masses=route_values,
        source_joint_masses=_sorted_mass_items(source_values),
        normal_cell_joint_masses=_sorted_mass_items(normal_values),
        raw64_words_consumed_per_jump=1,
    )


def enumerate_low_word_pushforward(
    fixture: FixtureSpec, state_id: str
) -> OperationalPushforwardLaw:
    """Independently enumerate a small low-word map for hostile-test oracles."""

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    if fixture.layout.used_bits > MAX_ENUMERATED_LOW_WORD_BITS:
        raise ValueError("layout exceeds the independent enumeration guard")
    state = fixture.state(state_id)
    if state.rank == 0:
        raise ValueError("a terminal state has no operational pushforward")
    route_counts: Dict[str, int] = {}
    source_counts: Dict[Tuple[str, int], int] = {}
    normal_counts: Dict[Tuple[str, int, int], int] = {}
    total = fixture.layout.low_word_count
    for word in range(total):
        selection = select_one_step(fixture, state_id, word)
        route_counts[selection.route_id] = route_counts.get(selection.route_id, 0) + 1
        if selection.source_index is not None:
            key = (selection.route_id, selection.source_index)
            source_counts[key] = source_counts.get(key, 0) + 1
        for coordinate, cell in enumerate(selection.normal_cells):
            key = (selection.route_id, coordinate, cell.index)
            normal_counts[key] = normal_counts.get(key, 0) + 1
    return OperationalPushforwardLaw(
        state_id=state.state_id,
        total_low_words=total,
        route_masses=tuple(
            (route.route_id, Fraction(route_counts.get(route.route_id, 0), total))
            for route in state.routes
        ),
        source_joint_masses=_sorted_mass_items(
            {key: Fraction(count, total) for key, count in source_counts.items()}
        ),
        normal_cell_joint_masses=_sorted_mass_items(
            {key: Fraction(count, total) for key, count in normal_counts.items()}
        ),
        raw64_words_consumed_per_jump=1,
    )


@dataclass(frozen=True)
class CP24CompatibleAddress:
    """Direct tag-6 address used by the pure supplied-word fixture run."""

    run_id: int
    step_index: int
    completed_proposals: int

    def __post_init__(self) -> None:
        _exact_int(self.run_id, name="run_id", minimum=0, maximum=UINT64_MODULUS - 1)
        _exact_int(
            self.step_index,
            name="step_index",
            minimum=0,
            maximum=UINT64_MODULUS - 1,
        )
        _exact_int(
            self.completed_proposals,
            name="completed_proposals",
            minimum=0,
            maximum=CP24_OPERATIONAL_EPOCH_MAX_PROPOSALS - 1,
        )

    @property
    def key(self) -> Tuple[int, int]:
        return (self.run_id, CP24_OPERATIONAL_EPOCH_DOMAIN_TAG)

    @property
    def counter(self) -> Tuple[int, int, int, int]:
        return (0, self.step_index, 0, self.completed_proposals)


@dataclass(frozen=True)
class AddressedUint64Word:
    """One supplied word explicitly owned by one CP24-compatible address."""

    address: CP24CompatibleAddress
    raw64_word: int

    def __post_init__(self) -> None:
        if type(self.address) is not CP24CompatibleAddress:
            raise TypeError("address must be an exact CP24CompatibleAddress")
        _exact_int(
            self.raw64_word,
            name="raw64_word",
            minimum=0,
            maximum=UINT64_MODULUS - 1,
        )


def bind_supplied_words_to_addresses(
    fixture: FixtureSpec,
    raw64_words: Tuple[int, ...],
    *,
    run_id: int,
    step_index: int,
) -> Tuple[AddressedUint64Word, ...]:
    """Bind the complete bounded tape before any route interpretation."""

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    words = _tuple_exact(raw64_words, name="raw64_words")
    run_id = _exact_int(run_id, name="run_id", minimum=0, maximum=UINT64_MODULUS - 1)
    step_index = _exact_int(
        step_index, name="step_index", minimum=0, maximum=UINT64_MODULUS - 1
    )
    if len(words) != fixture.initial_state.rank:
        raise ValueError("raw64_words must contain exactly the initial rank")
    bound = []
    for ordinal, word in enumerate(words):
        checked = _exact_int(
            word,
            name="raw64_words[%d]" % ordinal,
            minimum=0,
            maximum=UINT64_MODULUS - 1,
        )
        bound.append(
            AddressedUint64Word(
                CP24CompatibleAddress(run_id, step_index, ordinal), checked
            )
        )
    return tuple(bound)


@dataclass(frozen=True)
class LineageState:
    """Minimal fresh-monotone lineage state for the acyclic fixture."""

    active_serials: Tuple[int, ...]
    retired_serials: Tuple[int, ...]
    next_serial: int

    def __post_init__(self) -> None:
        active = _tuple_exact(self.active_serials, name="active_serials")
        retired = _tuple_exact(self.retired_serials, name="retired_serials")
        if len(active) > MAX_FIXTURE_LINEAGES or len(retired) > MAX_FIXTURE_LINEAGES:
            raise ValueError("lineage state exceeds the fixture guard")
        for name, values in (("active", active), ("retired", retired)):
            for index, serial in enumerate(values):
                _exact_int(
                    serial,
                    name="%s_serials[%d]" % (name, index),
                    minimum=1,
                    maximum=UINT64_MODULUS - 1,
                )
            if tuple(sorted(values)) != values or len(set(values)) != len(values):
                raise ValueError("%s serials must be strictly increasing" % name)
        if set(active).intersection(retired):
            raise ValueError("active and retired lineage serials overlap")
        next_serial = _exact_int(
            self.next_serial,
            name="next_serial",
            minimum=1,
            maximum=UINT64_MODULUS - 1,
        )
        if active or retired:
            if next_serial <= max(active + retired):
                raise ValueError("next_serial must exceed every issued serial")


def initial_lineage(cardinality: int) -> LineageState:
    cardinality = _exact_int(
        cardinality,
        name="cardinality",
        minimum=0,
        maximum=MAX_FIXTURE_LINEAGES,
    )
    return LineageState(tuple(range(1, cardinality + 1)), (), cardinality + 1)


def _advance_lineage(
    lineage: LineageState, selection: OperationalOneStepSelection
) -> Tuple[LineageState, Optional[int], Optional[int]]:
    if type(lineage) is not LineageState:
        raise TypeError("lineage must be an exact LineageState")
    active = list(lineage.active_serials)
    retired = list(lineage.retired_serials)
    source_serial = None
    created_serial = None
    if selection.family == FAMILY_BIRTH:
        created_serial = lineage.next_serial
        active.append(created_serial)
    else:
        if selection.source_index is None:
            raise AssertionError("source-selecting route omitted its source")
        if not 0 <= selection.source_index < len(active):
            raise ValueError("selected source lies outside active lineages")
        source_serial = active.pop(selection.source_index)
        retired.append(source_serial)
        if selection.family == FAMILY_REPLACEMENT:
            created_serial = lineage.next_serial
            active.append(created_serial)
    active.sort()
    retired.sort()
    next_serial = lineage.next_serial + (1 if created_serial is not None else 0)
    return (
        LineageState(tuple(active), tuple(retired), next_serial),
        source_serial,
        created_serial,
    )


@dataclass(frozen=True)
class AcyclicJumpTransition:
    """One address-bound supplied-word transition and lineage edit."""

    ordinal: int
    address: CP24CompatibleAddress
    state_before: str
    state_after: str
    rank_before: int
    rank_after: int
    total_tilted_rate: Fraction
    selection: OperationalOneStepSelection
    lineage_before: LineageState
    lineage_after: LineageState
    source_serial: Optional[int]
    created_serial: Optional[int]


@dataclass(frozen=True)
class AcyclicRunResult:
    """Terminal result for every valid word tape in the finite fixture domain."""

    fixture_id: str
    run_id: int
    step_index: int
    initial_state_id: str
    terminal_state_id: str
    supplied_word_count: int
    consumed_word_count: int
    unused_word_count: int
    maximum_jump_bound: int
    transitions: Tuple[AcyclicJumpTransition, ...]
    terminal_lineage: LineageState
    terminal: bool


def run_acyclic_fixture(
    fixture: FixtureSpec,
    raw64_words: Tuple[int, ...],
    *,
    run_id: int,
    step_index: int,
) -> AcyclicRunResult:
    """Run the supplied-word fixture to a terminal state without a cap failure.

    The caller supplies exactly ``initial_rank`` words.  Strict rank decrease
    proves that every valid tape terminates before those words are exhausted;
    unused words are retained as an explicit count and are never inspected.
    """

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    words = _tuple_exact(raw64_words, name="raw64_words")
    run_id = _exact_int(run_id, name="run_id", minimum=0, maximum=UINT64_MODULUS - 1)
    step_index = _exact_int(
        step_index, name="step_index", minimum=0, maximum=UINT64_MODULUS - 1
    )
    maximum = fixture.initial_state.rank
    if len(words) != maximum:
        raise ValueError("raw64_words must contain exactly the initial rank")
    for index, word in enumerate(words):
        _exact_int(
            word,
            name="raw64_words[%d]" % index,
            minimum=0,
            maximum=UINT64_MODULUS - 1,
        )
    current = fixture.initial_state
    lineage = initial_lineage(current.lineage_cardinality)
    transitions = []
    consumed_addresses = set()
    while current.rank > 0:
        ordinal = len(transitions)
        if ordinal >= len(words):
            raise AssertionError("strict rank bound exhausted a valid word tape")
        address = CP24CompatibleAddress(run_id, step_index, ordinal)
        address_identity = (address.key, address.counter)
        if address_identity in consumed_addresses:
            raise AssertionError("fixture attempted to reuse an address")
        consumed_addresses.add(address_identity)
        selection = select_one_step(fixture, current.state_id, words[ordinal])
        next_state = fixture.state(selection.next_state_id)
        if next_state.rank >= current.rank:
            raise AssertionError("validated fixture did not decrease rank")
        if len(lineage.active_serials) != current.lineage_cardinality:
            raise AssertionError("runtime lineage cardinality drifted from the fixture")
        next_lineage, source_serial, created_serial = _advance_lineage(
            lineage, selection
        )
        if len(next_lineage.active_serials) != next_state.lineage_cardinality:
            raise AssertionError("lineage transition differs from destination state")
        transitions.append(
            AcyclicJumpTransition(
                ordinal=ordinal,
                address=address,
                state_before=current.state_id,
                state_after=next_state.state_id,
                rank_before=current.rank,
                rank_after=next_state.rank,
                total_tilted_rate=current.total_tilted_rate,
                selection=selection,
                lineage_before=lineage,
                lineage_after=next_lineage,
                source_serial=source_serial,
                created_serial=created_serial,
            )
        )
        current = next_state
        lineage = next_lineage
    return AcyclicRunResult(
        fixture_id=fixture.fixture_id,
        run_id=run_id,
        step_index=step_index,
        initial_state_id=fixture.initial_state_id,
        terminal_state_id=current.state_id,
        supplied_word_count=len(words),
        consumed_word_count=len(transitions),
        unused_word_count=len(words) - len(transitions),
        maximum_jump_bound=maximum,
        transitions=tuple(transitions),
        terminal_lineage=lineage,
        terminal=True,
    )


def run_addressed_acyclic_fixture(
    fixture: FixtureSpec,
    addressed_words: Tuple[AddressedUint64Word, ...],
    *,
    run_id: int,
    step_index: int,
) -> AcyclicRunResult:
    """Consume one exact, complete CP24-addressed supplied-word roster.

    Every address is validated before any word is interpreted.  Missing,
    duplicate, reordered, alien-run, alien-step, or wrong-proposal addresses
    fail closed without a partial result.
    """

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    roster = _tuple_exact(addressed_words, name="addressed_words")
    run_id = _exact_int(run_id, name="run_id", minimum=0, maximum=UINT64_MODULUS - 1)
    step_index = _exact_int(
        step_index, name="step_index", minimum=0, maximum=UINT64_MODULUS - 1
    )
    if len(roster) != fixture.initial_state.rank:
        raise ValueError("addressed_words must contain exactly the initial rank")
    words = []
    identities = set()
    for ordinal, item in enumerate(roster):
        if type(item) is not AddressedUint64Word:
            raise TypeError("addressed_words must contain exact addressed records")
        expected = CP24CompatibleAddress(run_id, step_index, ordinal)
        if item.address != expected:
            raise FormalTest29FiniteAcyclicError(
                "addressed word differs from its exact roster position"
            )
        identity = (item.address.key, item.address.counter)
        if identity in identities:
            raise FormalTest29FiniteAcyclicError(
                "addressed word roster reuses an address"
            )
        identities.add(identity)
        words.append(item.raw64_word)
    result = run_acyclic_fixture(
        fixture, tuple(words), run_id=run_id, step_index=step_index
    )
    for transition, addressed in zip(result.transitions, roster):
        if transition.address != addressed.address:
            raise AssertionError("consumed transition address differs from its word")
        if transition.selection.decoded_word.raw64_word != addressed.raw64_word:
            raise AssertionError("consumed transition word differs from its address")
    return result


def validate_acyclic_run_result(
    fixture: FixtureSpec, raw64_words: Tuple[int, ...], result: AcyclicRunResult
) -> AcyclicRunResult:
    """Recompute a run from supplied words and require exact record equality."""

    if type(result) is not AcyclicRunResult:
        raise TypeError("result must be an exact AcyclicRunResult")
    rebuilt = run_acyclic_fixture(
        fixture,
        raw64_words,
        run_id=result.run_id,
        step_index=result.step_index,
    )
    if rebuilt != result:
        raise FormalTest29FiniteAcyclicError("run result differs from reconstruction")
    return result


def validate_addressed_acyclic_run_result(
    fixture: FixtureSpec,
    addressed_words: Tuple[AddressedUint64Word, ...],
    result: AcyclicRunResult,
) -> AcyclicRunResult:
    """Recompute an address-owned run and require exact record equality."""

    if type(result) is not AcyclicRunResult:
        raise TypeError("result must be an exact AcyclicRunResult")
    rebuilt = run_addressed_acyclic_fixture(
        fixture,
        addressed_words,
        run_id=result.run_id,
        step_index=result.step_index,
    )
    if rebuilt != result:
        raise FormalTest29FiniteAcyclicError(
            "addressed run result differs from reconstruction"
        )
    return result


@dataclass(frozen=True)
class FiniteAcyclicQualification:
    """Truthful qualification flags for the additive Test-29 precursor."""

    schema_version: str
    policy: str
    scope: str
    fixture_id: str
    active_state_count: int
    terminal_state_count: int
    maximum_jump_bound: int
    exact_tilted_total_rates_recovered: bool
    exact_edit_family_probabilities_recovered: bool
    exact_categorical_route_law_recovered: bool
    exact_integer_source_law_recovered: bool
    exact_ideal_gaussian_disintegration_recovered: bool
    exact_bounded_normal_cell_pushforward_recovered: bool
    cp24_compatible_address_consumption_defined: bool
    finite_run_persistent_fresh_lineage_defined: bool
    unconditional_bounded_fixture_completion_proved: bool
    exact_continuous_gaussian_from_bounded_words: bool
    production_cp24_execution_integrated: bool
    general_cyclic_liveness_proved: bool
    formal_test29_closed: bool


def qualify_finite_acyclic_fixture(
    fixture: FixtureSpec,
) -> FiniteAcyclicQualification:
    """Verify exact one-step laws and issue the narrow qualification record."""

    if type(fixture) is not FixtureSpec:
        raise TypeError("fixture must be an exact FixtureSpec")
    active = 0
    terminal = 0
    for state in fixture.states:
        if state.rank == 0:
            terminal += 1
            continue
        active += 1
        ideal = ideal_one_step_law(fixture, state.state_id)
        operational = operational_pushforward_law(fixture, state.state_id)
        if ideal.total_tilted_rate != state.total_tilted_rate:
            raise AssertionError("tilted total rate recovery failed")
        if ideal.route_masses != operational.route_masses:
            raise AssertionError("route pushforward differs from exact tilted law")
        ideal_sources = {
            (atom.route_id, atom.source_index): atom.mass
            for atom in ideal.atoms
            if atom.source_index is not None
        }
        if _sorted_mass_items(ideal_sources) != operational.source_joint_masses:
            raise AssertionError("source-index pushforward differs from exact law")
        family_total = _fraction_sum(
            tuple(mass for _, mass in ideal.family_masses),
            name="qualification_family_total",
        )
        if family_total != 1:
            raise AssertionError("edit-family probabilities do not normalize")
        for key, mass in operational.normal_cell_joint_masses:
            route_id, _, _ = key
            route_mass = dict(ideal.route_masses)[route_id]
            expected_cell_mass = _fraction_divide(
                route_mass,
                Fraction(1 << fixture.layout.normal_bits),
                name="qualification_route_normal_cell_mass",
            )
            if mass != expected_cell_mass:
                raise AssertionError("normal-cell pushforward differs")
    if not active or not terminal:
        raise ValueError("qualification fixture needs active and terminal states")
    return FiniteAcyclicQualification(
        schema_version=FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION,
        policy=FORMAL_TEST29_FINITE_ACYCLIC_POLICY,
        scope=FORMAL_TEST29_FINITE_ACYCLIC_SCOPE,
        fixture_id=fixture.fixture_id,
        active_state_count=active,
        terminal_state_count=terminal,
        maximum_jump_bound=fixture.initial_state.rank,
        exact_tilted_total_rates_recovered=True,
        exact_edit_family_probabilities_recovered=True,
        exact_categorical_route_law_recovered=True,
        exact_integer_source_law_recovered=True,
        exact_ideal_gaussian_disintegration_recovered=True,
        exact_bounded_normal_cell_pushforward_recovered=True,
        cp24_compatible_address_consumption_defined=True,
        finite_run_persistent_fresh_lineage_defined=True,
        unconditional_bounded_fixture_completion_proved=True,
        exact_continuous_gaussian_from_bounded_words=False,
        production_cp24_execution_integrated=False,
        general_cyclic_liveness_proved=False,
        formal_test29_closed=False,
    )


def bounded_word_continuous_gaussian_obstruction(
    word_count: int,
) -> Mapping[str, object]:
    """Return the finite-support obstruction for bounded-word Gaussian claims."""

    word_count = _exact_int(
        word_count, name="word_count", minimum=0, maximum=MAX_FIXTURE_RANK
    )
    support_upper_bound = UINT64_MODULUS**word_count
    return {
        "word_count": word_count,
        "finite_support_upper_bound": support_upper_bound,
        "gaussian_is_non_atomic": True,
        "exact_continuous_gaussian_possible": False,
        "reason": (
            "a deterministic image of finitely many uint64 words has finite support, "
            "whereas every nondegenerate Gaussian distribution is non-atomic"
        ),
    }


__all__ = [
    "FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION",
    "FORMAL_TEST29_FINITE_ACYCLIC_POLICY",
    "FORMAL_TEST29_FINITE_ACYCLIC_SCOPE",
    "CP24_OPERATIONAL_EPOCH_DOMAIN_TAG",
    "CP24_OPERATIONAL_EPOCH_MAX_PROPOSALS",
    "UINT64_MODULUS",
    "MAX_ENUMERATED_LOW_WORD_BITS",
    "MAX_EXACT_FRACTION_COMPONENT_BITS",
    "FAMILY_BIRTH",
    "FAMILY_DEATH",
    "FAMILY_REPLACEMENT",
    "EDIT_FAMILIES",
    "FormalTest29FiniteAcyclicError",
    "GaussianDestination",
    "NormalQuantileCell",
    "WordLayout",
    "RouteSpec",
    "StateSpec",
    "FixtureSpec",
    "IdealRouteSourceAtom",
    "IdealOneStepLaw",
    "DecodedWord",
    "OperationalOneStepSelection",
    "OperationalPushforwardLaw",
    "CP24CompatibleAddress",
    "AddressedUint64Word",
    "LineageState",
    "AcyclicJumpTransition",
    "AcyclicRunResult",
    "FiniteAcyclicQualification",
    "ideal_one_step_law",
    "decode_uint64_word",
    "select_one_step",
    "operational_pushforward_law",
    "enumerate_low_word_pushforward",
    "bind_supplied_words_to_addresses",
    "initial_lineage",
    "run_acyclic_fixture",
    "run_addressed_acyclic_fixture",
    "validate_acyclic_run_result",
    "validate_addressed_acyclic_run_result",
    "qualify_finite_acyclic_fixture",
    "bounded_word_continuous_gaussian_obstruction",
]
