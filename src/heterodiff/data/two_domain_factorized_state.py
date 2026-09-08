"""Full factorized metadata reference PROPOSAL, not a scientific admission.

Metadata stay exact: no finite type table, learned vocabulary, rounding, or
projection of F105 vectors. Ordinary positive magnitudes have a one-dimensional
log chart. MechVent and GCS values are *atomic*, including every nonnegative
rational accepted by the frozen semantic map; clinical validity is not claimed.

The mathematical prior uses independent ideal fair bits and a standard normal.
The supplied finite-state RNG is only a numerical implementation. Exhausting a
resource bound or exp/log representability fails without redraw or clipping;
the law conditioned on successful execution is NOT claimed to be the ideal law.
F105 raw decimal/binary64 input origin, observation common support, production
architecture, a configuration-count law, and scientific adoption remain open.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction
import json
import math
import random

import numpy as np

from heterodiff.data.two_domain_generative_chart_proposal import (
    PhysioSemanticEvent, RetailSemanticEvent, decode_metric_event,
    STRICT_FLOAT_POLICY, REPORTED_FLOAT_POLICY,
)
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks


ATOMIC_PHYSIO_PARAMETERS = ("GCS", "MechVent")
_EPOCH = datetime(2009, 12, 1)
_LN2 = math.log(2.0)


class FactorizedStateError(ValueError):
    pass


def _need(condition, code):
    if not condition:
        raise FactorizedStateError(code)


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _ratio(value):
    return None if value is None else [hex(value.numerator), hex(value.denominator)]


@dataclass(frozen=True)
class PhysioStateKey:
    elapsed_minutes: int
    parameter: str
    branch: str
    atomic_value: Fraction | None = None

    def __post_init__(self):
        PhysioSemanticEvent(self.elapsed_minutes, self.parameter, Fraction(0)).to_metric_event()
        if self.parameter in ATOMIC_PHYSIO_PARAMETERS:
            _need(self.branch in ("MISSING", "ATOMIC"), "ATOMIC_PHYSIO_BRANCH_REQUIRED")
        else:
            _need(self.branch in ("MISSING", "ZERO", "POSITIVE"), "INVALID_PHYSIO_BRANCH")
        if self.branch == "ATOMIC":
            _need(type(self.atomic_value) is Fraction and self.atomic_value >= 0,
                  "NONNEGATIVE_EXACT_ATOMIC_RATIONAL_REQUIRED")
        else:
            _need(self.atomic_value is None, "UNUSED_ATOMIC_PAYLOAD_FORBIDDEN")

    @property
    def domain_id(self):
        return cks.PHYSIONET_DOMAIN_ID

    @property
    def dimension(self):
        return int(self.branch == "POSITIVE")

    def canonical_bytes(self):
        return _json_bytes(["factorized-key-v1", self.domain_id,
                            hex(self.elapsed_minutes), self.parameter,
                            self.branch, _ratio(self.atomic_value)])


@dataclass(frozen=True)
class RetailStateKey:
    invoice_no: str
    stock_code: str
    description: str | None
    quantity: int
    invoice_calendar: tuple[int, ...]
    country: str | None
    branch: str

    def __post_init__(self):
        _need(type(self.invoice_calendar) is tuple, "IMMUTABLE_CALENDAR_REQUIRED")
        self.semantic(Fraction(0)).to_metric_event()
        _need(self.branch in ("NEGATIVE", "ZERO", "POSITIVE"), "INVALID_RETAIL_BRANCH")

    @property
    def domain_id(self):
        return cks.RETAIL_DOMAIN_ID

    @property
    def dimension(self):
        return int(self.branch != "ZERO")

    def semantic(self, price):
        return RetailSemanticEvent(self.invoice_no, self.stock_code,
                                   self.description, self.quantity,
                                   self.invoice_calendar, price, self.country)

    def canonical_bytes(self):
        return _json_bytes(["factorized-key-v1", self.domain_id, self.invoice_no,
                            self.stock_code, self.description, hex(self.quantity),
                            [hex(value) for value in self.invoice_calendar],
                            self.country, self.branch])


@dataclass(frozen=True)
class FactoredEvent:
    key: PhysioStateKey | RetailStateKey
    coordinate: float | None = None

    def __post_init__(self):
        _need(type(self.key) in (PhysioStateKey, RetailStateKey), "EXACT_STATE_KEY_REQUIRED")
        if self.key.dimension:
            _need(type(self.coordinate) is float and math.isfinite(self.coordinate),
                  "FINITE_BINARY64_SCALAR_COORDINATE_REQUIRED")
        else:
            _need(self.coordinate is None, "ZERO_DIMENSIONAL_ATOM_HAS_NO_COORDINATE")

    @property
    def sort_key(self):
        return (self.key.canonical_bytes(),
                "" if self.coordinate is None else self.coordinate.hex())

    def to_semantic_event(self):
        key = self.key
        if key.branch == "MISSING":
            value = None
        elif key.branch == "ATOMIC":
            value = key.atomic_value
        elif key.branch == "ZERO":
            value = Fraction(0)
        else:
            try:
                magnitude = math.exp(self.coordinate)
            except OverflowError as error:
                raise FactorizedStateError("LOG_CHART_OVERFLOW_NO_CLIPPING") from error
            _need(math.isfinite(magnitude) and magnitude > 0,
                  "LOG_CHART_UNDERFLOW_OR_NONFINITE_NO_CLIPPING")
            value = Fraction.from_float(-magnitude if key.branch == "NEGATIVE" else magnitude)
        if type(key) is PhysioStateKey:
            return PhysioSemanticEvent(key.elapsed_minutes, key.parameter, value)
        return key.semantic(value)

    def to_metric_event(self):
        return self.to_semantic_event().to_metric_event()


@dataclass(frozen=True)
class EventEncoding:
    event: FactoredEvent
    source_value: Fraction | None
    exact_binary64_conversion_error: Fraction | None
    decoded_native_roundtrip_error: Fraction | None
    conversion_policy: str

    def diagnostics(self):
        return {"scope": "NUMERIC_ENCODING_PROPOSAL_NOT_DATA_ADMISSION",
                "key_hex": self.event.key.canonical_bytes().hex(),
                "coordinate_hex": None if self.event.coordinate is None else self.event.coordinate.hex(),
                "source_value": _ratio(self.source_value),
                "exact_binary64_conversion_error": _ratio(self.exact_binary64_conversion_error),
                "decoded_native_roundtrip_error": _ratio(self.decoded_native_roundtrip_error),
                "conversion_policy": self.conversion_policy,
                "discrete_metadata_rounded": False,
                "raw_decimal_or_binary64_origin_proven": False,
                "clinical_validity_claimed": False}


def encode_semantic_event(semantic, *, conversion_policy=STRICT_FLOAT_POLICY):
    """Keep atoms exactly; scalar log/exp conversion has explicit error evidence."""
    _need(type(semantic) in (PhysioSemanticEvent, RetailSemanticEvent), "EXACT_SEMANTIC_EVENT_REQUIRED")
    _need(conversion_policy in (STRICT_FLOAT_POLICY, REPORTED_FLOAT_POLICY),
          "EXPLICIT_CONVERSION_POLICY_REQUIRED")
    semantic.to_metric_event()  # Frozen structural grammar; never repair fields.
    value = semantic.value if type(semantic) is PhysioSemanticEvent else semantic.unit_price
    if type(semantic) is PhysioSemanticEvent:
        branch = ("MISSING" if value is None else "ATOMIC"
                  if semantic.parameter in ATOMIC_PHYSIO_PARAMETERS else
                  "ZERO" if value == 0 else "POSITIVE")
        key = PhysioStateKey(semantic.elapsed_minutes, semantic.parameter, branch,
                             value if branch == "ATOMIC" else None)
    else:
        branch = "NEGATIVE" if value < 0 else "ZERO" if value == 0 else "POSITIVE"
        key = RetailStateKey(semantic.invoice_no, semantic.stock_code, semantic.description,
                             semantic.quantity, semantic.invoice_calendar, semantic.country, branch)
    if not key.dimension:
        zero = None if value is None else Fraction(0)
        return EventEncoding(FactoredEvent(key), value, zero, zero, conversion_policy)
    try:
        native = float(value)
    except OverflowError as error:
        raise FactorizedStateError("NATIVE_BINARY64_OVERFLOW_NO_CLIPPING") from error
    _need(math.isfinite(native) and native != 0.0, "NATIVE_BINARY64_UNDERFLOW_OR_NONFINITE")
    conversion_error = Fraction.from_float(native) - value
    _need(conversion_policy != STRICT_FLOAT_POLICY or conversion_error == 0,
          "EXACT_BINARY64_CONVERSION_REQUIRED")
    event = FactoredEvent(key, math.log(abs(native)))
    decoded = event.to_semantic_event()
    decoded_value = decoded.value if type(decoded) is PhysioSemanticEvent else decoded.unit_price
    return EventEncoding(event, value, conversion_error, decoded_value - value, conversion_policy)


def encode_metric_event(event, *, conversion_policy=STRICT_FLOAT_POLICY):
    return encode_semantic_event(decode_metric_event(event), conversion_policy=conversion_policy)


@dataclass(frozen=True)
class DyadicMass:
    """Positive exact n/2**e without binary64 underflow or a probability floor."""
    numerator: int = 1
    denominator_exponent: int = 0

    def __post_init__(self):
        n, e = self.numerator, self.denominator_exponent
        _need(type(n) is int and n > 0 and type(e) is int and e >= 0, "INVALID_DYADIC_MASS")
        shift = min((n & -n).bit_length() - 1, e)
        n, e = n >> shift, e - shift
        _need(n.bit_length() <= e + 1 and (n.bit_length() != e + 1 or n == 1 << e),
              "PROBABILITY_EXCEEDS_ONE")
        object.__setattr__(self, "numerator", n)
        object.__setattr__(self, "denominator_exponent", e)

    def __mul__(self, other):
        _need(type(other) is DyadicMass, "EXACT_DYADIC_MASS_REQUIRED")
        return DyadicMass(self.numerator * other.numerator,
                          self.denominator_exponent + other.denominator_exponent)

    def log(self):
        try:
            result = math.log(self.numerator) - self.denominator_exponent * _LN2
        except OverflowError as error:
            raise FactorizedStateError("LOG_MASS_REPRESENTABILITY_LIMIT_NO_PROBABILITY_FLOOR") from error
        _need(math.isfinite(result), "LOG_MASS_REPRESENTABILITY_LIMIT_NO_PROBABILITY_FLOOR")
        return result

    def as_fraction(self, *, maximum_denominator_bits=1_000_000):
        _need(type(maximum_denominator_bits) is int and maximum_denominator_bits > 0,
              "INVALID_EXACT_MATERIALIZATION_BOUND")
        _need(self.denominator_exponent + 1 <= maximum_denominator_bits,
              "EXACT_MATERIALIZATION_RESOURCE_LIMIT_NO_RENORMALIZATION")
        return Fraction(self.numerator, 1 << self.denominator_exponent)


def ordinal_mass(index, size):
    """Map k fair bits modulo n; declared dyadic bias, not a uniform claim."""
    _need(type(size) is int and size > 0 and type(index) is int and 0 <= index < size,
          "INVALID_FINITE_ORDINAL")
    bits = (size - 1).bit_length()
    return DyadicMass(2 if index < (1 << bits) - size else 1, bits)


def nonnegative_integer_mass(value):
    _need(type(value) is int and value >= 0, "NONNEGATIVE_INTEGER_REQUIRED")
    return DyadicMass(1, 1) if value == 0 else DyadicMass(3, 3 * value.bit_length())


def signed_integer_mass(value):
    _need(type(value) is int, "EXACT_SIGNED_INTEGER_REQUIRED")
    mass = nonnegative_integer_mass(abs(value))
    return mass if value == 0 else mass * DyadicMass(1, 1)


def canonical_continued_fraction(value):
    _need(type(value) is Fraction and value >= 0, "NONNEGATIVE_EXACT_RATIONAL_REQUIRED")
    result = []
    numerator, denominator = value.numerator, value.denominator
    while denominator:
        term, remainder = divmod(numerator, denominator)
        result.append(term)
        numerator, denominator = denominator, remainder
    return tuple(result)


def nonnegative_rational_mass(value):
    terms = canonical_continued_fraction(value)
    result = nonnegative_integer_mass(terms[0]) * DyadicMass(1, 1)
    if len(terms) == 1:
        return result
    # Noninteger branch 1/2; P(tail length L)=2**-L. Last term >=2
    # makes this a unique representation, not an ambiguous fraction mixture.
    result = result * DyadicMass(1, len(terms) - 1)
    for term in terms[1:-1]:
        result = result * nonnegative_integer_mass(term - 1)
    return result * nonnegative_integer_mass(terms[-1] - 2)


def _scalar_width(codepoint):
    if codepoint <= 0x7F:
        return 1, codepoint, 128
    if codepoint <= 0x7FF:
        return 2, codepoint - 0x80, 1920
    if codepoint <= 0xFFFF:
        _need(not 0xD800 <= codepoint <= 0xDFFF, "INVALID_UTF8_SCALAR")
        return 3, codepoint - 0x800 - (2048 if codepoint > 0xDFFF else 0), 61440
    return 4, codepoint - 0x10000, 1048576


def _width_mass(width, remaining):
    maximum = min(4, remaining)
    _need(1 <= width <= maximum, "UTF8_WIDTH_EXCEEDS_BUDGET")
    return DyadicMass(1, min(width, maximum - 1))


def utf8_string_mass(value, *, maximum_bytes, allow_empty):
    _need(type(value) is str and type(maximum_bytes) is int and maximum_bytes > 0,
          "EXACT_UTF8_STRING_AND_BOUND_REQUIRED")
    _need(type(allow_empty) is bool and (allow_empty or value != ""), "EMPTY_REQUIRED_STRING")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise FactorizedStateError("INVALID_UTF8_SCALAR") from error
    _need(len(encoded) <= maximum_bytes, "FROZEN_UTF8_BOUND_EXCEEDED")
    result, remaining = DyadicMass(), maximum_bytes
    for index, character in enumerate(value):
        if allow_empty or index > 0:
            result = result * DyadicMass(1, 1)  # continue
        width, ordinal, size = _scalar_width(ord(character))
        result = result * _width_mass(width, remaining) * ordinal_mass(ordinal, size)
        remaining -= width
    if remaining:
        result = result * DyadicMass(1, 1)  # stop; at bound stop is forced
    return result


@dataclass(frozen=True)
class SamplingLimits:
    maximum_entropy_bits: int = 1_000_000
    maximum_integer_bits: int = 65536
    maximum_continued_fraction_terms: int = 1024

    def __post_init__(self):
        _need(all(type(value) is int and value > 0 for value in (
            self.maximum_entropy_bits, self.maximum_integer_bits,
            self.maximum_continued_fraction_terms)), "POSITIVE_SAMPLING_LIMITS_REQUIRED")


class _Entropy:
    def __init__(self, rng, limits):
        self.rng, self.limits, self.used = rng, limits, 0
        self.word, self.available = 0, 0

    def bits(self, count):
        _need(self.used + count <= self.limits.maximum_entropy_bits,
              "ENTROPY_RESOURCE_LIMIT_NO_REDRAW")
        self.used += count
        result, filled = 0, 0
        while filled < count:
            if not self.available:
                if hasattr(self.rng, "getrandbits"):
                    self.word = self.rng.getrandbits(64)
                else:
                    self.word = int(self.rng.bit_generator.random_raw())
                _need(type(self.word) is int and 0 <= self.word < 2**64,
                      "UNSIGNED_64BIT_RNG_WORD_REQUIRED")
                self.available = 64
            take = min(self.available, count - filled)
            result |= (self.word & ((1 << take) - 1)) << filled
            self.word >>= take
            self.available -= take
            filled += take
        return result

    def ordinal(self, size):
        return self.bits((size - 1).bit_length()) % size

    def nonnegative_integer(self):
        if self.bits(1) == 0:
            return 0
        length = 1
        while self.bits(2) == 3:
            length += 1
            _need(length <= self.limits.maximum_integer_bits,
                  "INTEGER_RESOURCE_LIMIT_NO_REDRAW")
        return (1 << (length - 1)) + self.bits(length - 1)

    def signed_integer(self):
        value = self.nonnegative_integer()
        return -value if value and self.bits(1) else value

    def rational(self):
        terms = [self.nonnegative_integer()]
        if self.bits(1) == 0:
            return Fraction(terms[0])
        tail_length = 1
        while self.bits(1):
            tail_length += 1
            _need(tail_length + 1 <= self.limits.maximum_continued_fraction_terms,
                  "CONTINUED_FRACTION_RESOURCE_LIMIT_NO_REDRAW")
        _need(tail_length + 1 <= self.limits.maximum_continued_fraction_terms,
              "CONTINUED_FRACTION_RESOURCE_LIMIT_NO_REDRAW")
        terms.extend(1 + self.nonnegative_integer() for _ in range(tail_length - 1))
        terms.append(2 + self.nonnegative_integer())
        result = Fraction(terms[-1])
        for term in reversed(terms[:-1]):
            result = term + 1 / result
        return result

    def text(self, maximum_bytes, allow_empty):
        remaining, characters = maximum_bytes, []
        while remaining:
            if (allow_empty or characters) and self.bits(1) == 0:
                break
            maximum_width = min(4, remaining)
            width = 1
            while width < maximum_width and self.bits(1):
                width += 1
            size = (128, 1920, 61440, 1048576)[width - 1]
            ordinal = self.ordinal(size)
            codepoint = ordinal + (0, 0x80, 0x800, 0x10000)[width - 1]
            if width == 3 and codepoint >= 0xD800:
                codepoint += 2048
            characters.append(chr(codepoint))
            remaining -= width
        return "".join(characters)


def _validate_sampling_inputs(rng, limits):
    _need(type(limits) is SamplingLimits, "EXACT_SAMPLING_LIMITS_REQUIRED")
    _need(type(rng) is random.Random or
          (type(rng) is np.random.Generator and
           type(rng.bit_generator) in (np.random.PCG64, np.random.PCG64DXSM)),
          "EXPLICIT_RANDOM_OR_PCG64_GENERATOR_REQUIRED")


@dataclass(frozen=True)
class FactorizedMetadataReference:
    domain_id: str

    def __post_init__(self):
        _need(self.domain_id in (cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID),
              "UNKNOWN_FACTORIZED_DOMAIN")

    def mass(self, key):
        _need(type(key) in (PhysioStateKey, RetailStateKey) and key.domain_id == self.domain_id,
              "EXACT_SAME_DOMAIN_KEY_REQUIRED")
        if type(key) is PhysioStateKey:
            result = ordinal_mass(key.elapsed_minutes, cks.PHYSIONET_HORIZON_MINUTES + 1)
            result = result * ordinal_mass(cks.PHYSIONET_PARAMETERS.index(key.parameter), 37)
            if key.parameter in ATOMIC_PHYSIO_PARAMETERS:
                result = result * DyadicMass(1, 1)
                return result if key.branch == "MISSING" else result * nonnegative_rational_mass(key.atomic_value)
            return result * DyadicMass(1, 1 if key.branch == "POSITIVE" else 2)
        prefix = key.invoice_no[0] if key.invoice_no[0] in "Cc" else ""
        result = ordinal_mass(int(key.invoice_no[-6:]), 1_000_000)
        result = result * DyadicMass(1, 1 if prefix == "" else 2)
        result = result * utf8_string_mass(key.stock_code, maximum_bytes=256, allow_empty=False)
        for value, bound in ((key.description, 4096), (key.country, 256)):
            result = result * DyadicMass(1, 1)
            if value is not None:
                result = result * utf8_string_mass(value, maximum_bytes=bound, allow_empty=True)
        result = result * signed_integer_mass(key.quantity)
        instant = datetime(*key.invoice_calendar)
        delta = instant - _EPOCH
        micros = ((delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds)
        result = result * ordinal_mass(micros, cks.RETAIL_HORIZON_MICROSECONDS)
        return result * DyadicMass(1, 1 if key.branch == "ZERO" else 2)

    def log_prob(self, key):
        """Metadata probability, not the coordinate's Gaussian density."""
        return self.mass(key).log()

    def event_log_density(self, event):
        _need(type(event) is FactoredEvent, "EXACT_FACTORED_EVENT_REQUIRED")
        value = self.log_prob(event.key)
        if event.key.dimension:
            value -= 0.5 * (math.log(2 * math.pi) + event.coordinate * event.coordinate)
        _need(math.isfinite(value), "LOG_DENSITY_REPRESENTABILITY_LIMIT_NO_PROBABILITY_FLOOR")
        return value

    def sample_key(self, rng, *, limits=SamplingLimits()):
        _validate_sampling_inputs(rng, limits)
        return self._sample_key(_Entropy(rng, limits))

    def _sample_key(self, entropy):
        if self.domain_id == cks.PHYSIONET_DOMAIN_ID:
            minute = entropy.ordinal(cks.PHYSIONET_HORIZON_MINUTES + 1)
            parameter = cks.PHYSIONET_PARAMETERS[entropy.ordinal(37)]
            if parameter in ATOMIC_PHYSIO_PARAMETERS:
                if entropy.bits(1) == 0:
                    return PhysioStateKey(minute, parameter, "MISSING")
                return PhysioStateKey(minute, parameter, "ATOMIC", entropy.rational())
            choice = entropy.bits(2)
            return PhysioStateKey(minute, parameter, ("MISSING", "ZERO", "POSITIVE", "POSITIVE")[choice])
        invoice = f"{entropy.ordinal(1_000_000):06d}"
        prefix = ("", "", "C", "c")[entropy.bits(2)]
        stock = entropy.text(256, False)
        description = None if entropy.bits(1) == 0 else entropy.text(4096, True)
        country = None if entropy.bits(1) == 0 else entropy.text(256, True)
        quantity = entropy.signed_integer()
        micros = entropy.ordinal(cks.RETAIL_HORIZON_MICROSECONDS)
        instant = _EPOCH + timedelta(microseconds=micros)
        calendar = (instant.year, instant.month, instant.day, instant.hour,
                    instant.minute, instant.second, instant.microsecond)
        branch = ("ZERO", "ZERO", "NEGATIVE", "POSITIVE")[entropy.bits(2)]
        return RetailStateKey(prefix + invoice, stock, description, quantity, calendar, country, branch)

    def sample_event(self, rng, *, limits=SamplingLimits()):
        key = self.sample_key(rng, limits=limits)
        if not key.dimension:
            return FactoredEvent(key)
        if hasattr(rng, "normal"):
            coordinate = float(rng.normal())
        else:
            coordinate = float(rng.gauss(0.0, 1.0))
        return FactoredEvent(key, coordinate)

    def diagnostics(self):
        return {"schema_version": "two-domain-factorized-metadata-reference-proposal-v1",
                "domain_id": self.domain_id,
                "ideal_law_full_metadata_support": True,
                "finite_rng_exact_ideal_law_claimed": False,
                "joint_probability_floor": None,
                "finite_type_table_or_observed_vocabulary_used": False,
                "atomic_physio_parameters": ATOMIC_PHYSIO_PARAMETERS,
                "atomic_numeric_support": "ALL_NONNEGATIVE_RATIONALS_NOT_CLINICAL_ADMISSION",
                "magnitude_fiber": "SIGNED_EXP_STANDARD_NORMAL_WITH_SEPARATE_ZERO_MISSING_ATOMS",
                "configuration_count_law_selected": False,
                "clinical_validity_claimed": False,
                "raw_decimal_or_binary64_origin_proven": False,
                "observation_kernel_common_support_proven": False,
                "production_adoption": False,
                "resource_failure_policy": "REFUSE_NO_REDRAW_NO_CONDITIONED_LAW_CLAIM"}


def _fraction_log(value):
    _need(type(value) is Fraction and value > 0, "POSITIVE_EXACT_FRACTION_REQUIRED")
    result = math.log(value.numerator) - math.log(value.denominator)
    _need(math.isfinite(result), "FRACTION_LOG_REPRESENTABILITY_LIMIT")
    return result


@dataclass(frozen=True)
class TrainMixtureMass:
    """Compact exact expression beta*universal + (1-beta)*empirical."""
    beta: Fraction
    universal: DyadicMass
    empirical: Fraction

    def __post_init__(self):
        _need(type(self.beta) is Fraction and 0 < self.beta < 1,
              "EXACT_BETA_STRICTLY_BETWEEN_ZERO_AND_ONE_REQUIRED")
        _need(type(self.universal) is DyadicMass and type(self.empirical) is Fraction
              and 0 <= self.empirical <= 1, "EXACT_MIXTURE_COMPONENTS_REQUIRED")

    def log(self):
        first = _fraction_log(self.beta) + self.universal.log()
        if self.empirical == 0:
            return first
        second = _fraction_log(1 - self.beta) + _fraction_log(self.empirical)
        maximum = max(first, second)
        result = maximum + math.log1p(math.exp(min(first, second) - maximum))
        _need(math.isfinite(result), "MIXTURE_LOG_REPRESENTABILITY_LIMIT")
        return result

    def as_fraction(self, *, maximum_denominator_bits=1_000_000):
        _need(type(maximum_denominator_bits) is int and maximum_denominator_bits > 0,
              "INVALID_EXACT_MATERIALIZATION_BOUND")
        estimated_bits = (self.beta.denominator.bit_length() + self.universal.denominator_exponent
                          + self.empirical.denominator.bit_length())
        _need(estimated_bits <= maximum_denominator_bits,
              "MIXTURE_EXACT_MATERIALIZATION_RESOURCE_LIMIT_NO_RENORMALIZATION")
        return (self.beta * self.universal.as_fraction(maximum_denominator_bits=maximum_denominator_bits)
                + (1 - self.beta) * self.empirical)


def _exact_bernoulli(entropy, probability):
    """Successive fair-bit intervals; no float threshold or rejected record."""
    numerator, denominator = probability.numerator, probability.denominator
    while True:
        numerator *= 2
        if entropy.bits(1) == 0:
            if numerator >= denominator:
                return True
        else:
            if numerator <= denominator:
                return False
            numerator -= denominator


def _uniform_occurrence_index(entropy, size):
    """Exact ideal U partition into N equal intervals, not biased modulo N."""
    prefix, denominator = 0, 1
    while True:
        low = prefix * size // denominator
        high = ((prefix + 1) * size - 1) // denominator
        if low == high:
            return low
        prefix = 2 * prefix + entropy.bits(1)
        denominator *= 2


@dataclass(frozen=True)
class TrainInformedMetadataReference:
    """Explicit TRAIN-labelled occurrence-key mixture, not an admission proof.

    Only immutable complete keys are retained. Continuous coordinates of the
    supplied occurrences are NOT fit or reused: every 1D reference fiber stays
    independent standard normal. Repeated keys contribute occurrence counts.
    The caller's TRAIN declaration is not independently authenticated here.
    """
    universal: FactorizedMetadataReference
    beta: Fraction
    train_keys: tuple[PhysioStateKey | RetailStateKey, ...]
    key_frequencies: tuple[tuple[PhysioStateKey | RetailStateKey, int], ...]

    def __init__(self, universal, train_occurrences, *, beta):
        _need(type(universal) is FactorizedMetadataReference, "EXACT_UNIVERSAL_REFERENCE_REQUIRED")
        _need(type(beta) is Fraction and 0 < beta < 1,
              "EXACT_BETA_STRICTLY_BETWEEN_ZERO_AND_ONE_REQUIRED")
        _need(type(train_occurrences) is tuple and len(train_occurrences) > 0
              and all(type(event) is FactoredEvent for event in train_occurrences),
              "NONEMPTY_EXPLICIT_TRAIN_OCCURRENCE_TUPLE_REQUIRED")
        keys = tuple(event.key for event in train_occurrences)
        frequencies = {}
        for key in keys:
            _need(key.domain_id == universal.domain_id, "CROSS_DOMAIN_TRAIN_ROSTER_FORBIDDEN")
            frequencies[key] = frequencies.get(key, 0) + 1
        object.__setattr__(self, "universal", universal)
        object.__setattr__(self, "beta", beta)
        object.__setattr__(self, "train_keys", keys)
        object.__setattr__(self, "key_frequencies", tuple(sorted(frequencies.items(), key=lambda item: item[0].canonical_bytes())))

    @property
    def domain_id(self):
        return self.universal.domain_id

    def mass(self, key):
        base = self.universal.mass(key)
        count = next((count for candidate, count in self.key_frequencies if candidate == key), 0)
        return TrainMixtureMass(self.beta, base, Fraction(count, len(self.train_keys)))

    def log_prob(self, key):
        return self.mass(key).log()

    def event_log_density(self, event):
        _need(type(event) is FactoredEvent, "EXACT_FACTORED_EVENT_REQUIRED")
        value = self.log_prob(event.key)
        if event.key.dimension:
            value -= .5 * (math.log(2 * math.pi) + event.coordinate * event.coordinate)
        _need(math.isfinite(value), "LOG_DENSITY_REPRESENTABILITY_LIMIT_NO_PROBABILITY_FLOOR")
        return value

    def sample_key(self, rng, *, limits=SamplingLimits()):
        _validate_sampling_inputs(rng, limits)
        entropy = _Entropy(rng, limits)
        if _exact_bernoulli(entropy, self.beta):
            return self.universal._sample_key(entropy)
        return self.train_keys[_uniform_occurrence_index(entropy, len(self.train_keys))]

    def sample_event(self, rng, *, limits=SamplingLimits()):
        key = self.sample_key(rng, limits=limits)
        if not key.dimension:
            return FactoredEvent(key)
        coordinate = float(rng.normal()) if hasattr(rng, "normal") else float(rng.gauss(0.0, 1.0))
        return FactoredEvent(key, coordinate)

    def diagnostics(self):
        return {"schema_version": "train-informed-factorized-metadata-reference-proposal-v1",
                "domain_id": self.domain_id, "beta_exact": _ratio(self.beta),
                "train_occurrences": len(self.train_keys),
                "train_unique_keys": len(self.key_frequencies),
                "reference_fiber": "INDEPENDENT_STANDARD_NORMAL_ONLY_FOR_1D",
                "ideal_law_full_metadata_support": True,
                "empirical_only_support": False,
                "train_split_or_no_leakage_independently_verified": False,
                "heldout_unseen_key_mass_improvement_claimed": False,
                "finite_rng_exact_ideal_law_claimed": False,
                "source_values_or_continuous_coordinates_fit": False,
                "production_adoption": False}
