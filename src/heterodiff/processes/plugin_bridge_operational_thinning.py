"""Finite-resolution local thinning for the totalized operational jump target.

Checkpoint eighteen supplies a no-RNG, outward-rounded envelope ``E`` and a
correctly rounded candidate integrand ``I`` for checkpoint seventeen's
explicit operational-surrogate target.  This module adds only the local
random decisions needed by one frozen jump subproblem:

* a variable-random-bit inverse-transform waiting clock driven by ``E``;
* a normalized-reference route draw after, and only after, a certified clock
  hit; and
* an exact Bernoulli decision for the rational quotient of the represented
  binary64 values ``I / E``.

The waiting clock interprets successive raw Philox words as the leading bits
of one ideal uniform variate.  Directed Decimal logarithm and division
intervals are refined until the waiting time and absolute proposal timestamp
have unique round-to-nearest-even binary64 images, or the frozen work limit is
reached.  Acceptance never forms a floating-point probability: it samples a
uniform integer with bounded denominator rejection from the exact reduced
ratio of the two represented rates.

This is a successful-return contract for one frozen local thinning decision.
It does not compute the active controlled total exit, prove liveness, certify
an analytic/conditional target, integrate drift, initialize a bridge, manage
lineages, construct a path, or admit the complete split-step sampler.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import decimal
from decimal import Context, Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

import numpy as np

try:
    from heterodiff.models import (
        configuration_totalized_jump_rate_envelope_torch as _rate,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or (
        "jump-rate domination requires the optional PyTorch" in str(error)
    ):
        raise ModuleNotFoundError(
            "operational jump thinning requires the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.processes.plugin_bridge_sampler import (
    ProcessValidReferenceJump,
    ProcessValidReferenceJumpComposer,
    ReferenceCandidateIntensity,
)
from heterodiff.theory.configuration_reference import TransformedConfiguration


ConfigurationTotalizedJumpRateError = _rate.ConfigurationTotalizedJumpRateError
TotalizedConfigurationJumpRateEnvelope = _rate.TotalizedConfigurationJumpRateEnvelope
TotalizedJumpPotentialCandidateEvaluation = (
    _rate.TotalizedJumpPotentialCandidateEvaluation
)
TotalizedJumpRateCandidateEvaluation = _rate.TotalizedJumpRateCandidateEvaluation
TotalizedJumpRateEnvelope = _rate.TotalizedJumpRateEnvelope
TotalizedJumpRateEnvelopeCertificate = _rate.TotalizedJumpRateEnvelopeCertificate

_candidate_sha256 = _rate._candidate_sha256
_configuration_sha256 = _rate._configuration_sha256
_decimal_ceiling_binary64 = _rate._decimal_ceiling_binary64
_decimal_floor_binary64 = _rate._decimal_floor_binary64
_exact_power_two_fraction_decimal = _rate._exact_power_two_fraction_decimal
_field_matches = _rate._field_matches
_fraction = _rate._fraction
_intensity_sha256 = _rate._intensity_sha256
_rate_require_fraction_size = _rate._rate_require_fraction_size
_rate_round_fraction_once = _rate._rate_round_fraction_once
_require_binary64_environment = _rate._require_binary64_environment
_require_sha256 = _rate._require_sha256
_same_float = _rate._same_float
_semantic_digest = _rate._semantic_digest
_validated_float = _rate._validated_float


PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCHEMA_VERSION = (
    "plugin-bridge-operational-thinning-v1"
)
PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY = (
    "checkpoint18-local-envelope;philox-raw64-msb-prefix-uniform;"
    "directed-decimal-inverse-exponential-clock;"
    "unique-rne-binary64-interior-timestamp;"
    "process-owned-post-clock-route;"
    "exact-represented-rate-ratio;"
    "bounded-uniform-integer-denominator-rejection-v1"
)
PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCOPE = (
    "checkpoint17-operational-surrogate-target;"
    "frozen-state-and-generative-time-local-subproblem;"
    "successful-return-wait-route-accept-sequencing;"
    "actual-represented-candidate-over-local-envelope;"
    "trusted-runtime;not-active-total-exit;not-liveness;"
    "not-analytic-target;not-conditional-posterior-or-doob-target;"
    "not-rounded-detailed-balance;not-stationary-target;"
    "not-counter-key-lineage-contract;not-drift;not-initializer;"
    "not-path;not-strang-sampler;not-full-sampler"
)
PLUGIN_BRIDGE_OPERATIONAL_WAITING_POLICY = (
    "ideal-uniform-from-philox-raw64-prefix;"
    "minus-log-over-local-represented-envelope;"
    "directed-decimal-enclosure;inclusive-real-right-end;"
    "strict-represented-interior-or-refuse-v1"
)
PLUGIN_BRIDGE_OPERATIONAL_ACCEPTANCE_POLICY = (
    "exact-fraction-from-binary64-I-over-E;"
    "uniform-integer-denominator-rejection;"
    "whole-raw64-word-consumption;fixed-padding-discard;"
    "bounded-attempt-refusal-v1"
)

OPERATIONAL_THINNING_DECIMAL_PRIMARY_PRECISION = 192
OPERATIONAL_THINNING_DECIMAL_AUDIT_PRECISION = 384
OPERATIONAL_THINNING_DECIMAL_MAX_PRECISION = 1_536
OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS = 64
OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS = 128
OPERATIONAL_THINNING_MAX_RATIO_BITS = 2_098
OPERATIONAL_THINNING_RAW_WORD_BITS = 64

_DECIMAL_MIN_EXPONENT = -999_999
_DECIMAL_MAX_EXPONENT = 999_999
_MAX_RNG_STATE_NODES = 4_096
_MAX_RNG_STATE_DEPTH = 16
_MAX_RNG_STATE_ARRAY_BYTES = 16_384
_CERTIFICATE_TOKEN = object()
_WAITING_TOKEN = object()
_ROUTE_TOKEN = object()
_DECISION_TOKEN = object()
_OWNER_TOKEN = object()


class PluginBridgeOperationalThinningError(ArithmeticError):
    """Raised when a local random decision cannot be certified safely."""


def _canonical_zero(value: float) -> float:
    return 0.0 if value == 0.0 else value


def _clock_float(
    value: object,
    *,
    name: str,
    nonnegative: bool = False,
) -> float:
    try:
        result = _validated_float(
            value,
            name=name,
            nonnegative=nonnegative,
            canonical_zero=True,
        )
    except (TypeError, ValueError, ArithmeticError) as error:
        raise type(error)(str(error)) from error
    return result


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    return value


def _decimal_context(precision: int, rounding: str) -> Context:
    if type(precision) is not int or not 1 <= precision <= 10_000:
        raise ValueError("decimal precision is outside the implementation limit")
    return Context(
        prec=precision,
        rounding=rounding,
        Emin=_DECIMAL_MIN_EXPONENT,
        Emax=_DECIMAL_MAX_EXPONENT,
        clamp=0,
        traps=[
            decimal.InvalidOperation,
            decimal.DivisionByZero,
            decimal.Overflow,
            decimal.Underflow,
        ],
    )


def _precision_schedule() -> Tuple[int, ...]:
    values = []
    precision = OPERATIONAL_THINNING_DECIMAL_PRIMARY_PRECISION
    while precision < OPERATIONAL_THINNING_DECIMAL_MAX_PRECISION:
        values.append(precision)
        precision *= 2
    values.append(OPERATIONAL_THINNING_DECIMAL_MAX_PRECISION)
    return tuple(values)


def _copy_negate(value: Decimal) -> Decimal:
    result = value.copy_negate()
    if result.is_zero():
        return Decimal(0)
    return result


def _ln_interval(value: Decimal, *, precision: int) -> Tuple[Decimal, Decimal]:
    if not value.is_finite() or not Decimal(0) < value <= Decimal(1):
        raise ValueError("logarithm input must lie in (0, 1]")
    context = _decimal_context(precision, ROUND_HALF_EVEN)
    try:
        rounded = context.ln(value)
        lower = context.next_minus(rounded)
        upper = context.next_plus(rounded)
    except decimal.DecimalException as error:
        raise PluginBridgeOperationalThinningError(
            "Decimal logarithm could not be enclosed"
        ) from error
    if not lower.is_finite() or not upper.is_finite() or lower > upper:
        raise PluginBridgeOperationalThinningError(
            "Decimal logarithm interval is invalid"
        )
    return lower, upper


def _waiting_interval_at_precision(
    prefix: int,
    bit_count: int,
    envelope_rate: Fraction,
    clock_start: Fraction,
    *,
    precision: int,
) -> Tuple[Decimal, Optional[Decimal], Decimal, Optional[Decimal]]:
    if type(prefix) is not int or isinstance(prefix, bool) or prefix < 0:
        raise TypeError("uniform prefix must be a nonnegative exact integer")
    if type(bit_count) is not int or bit_count <= 0:
        raise ValueError("uniform bit count must be positive")
    if prefix >= 1 << bit_count:
        raise ValueError("uniform prefix exceeds its bit count")
    denominator = 1 << bit_count
    upper_uniform = Fraction(prefix + 1, denominator)
    upper_decimal = _exact_power_two_fraction_decimal(
        upper_uniform,
        name="waiting uniform upper endpoint",
    )
    upper_log_lower, upper_log_upper = _ln_interval(
        upper_decimal,
        precision=precision,
    )
    hazard_lower = _copy_negate(upper_log_upper)
    if hazard_lower < 0:
        hazard_lower = Decimal(0)

    rate_decimal = _exact_power_two_fraction_decimal(
        envelope_rate,
        name="waiting envelope rate",
    )
    start_decimal = _exact_power_two_fraction_decimal(
        clock_start,
        name="waiting clock start",
    )
    floor_context = _decimal_context(precision, ROUND_FLOOR)
    ceiling_context = _decimal_context(precision, ROUND_CEILING)
    try:
        waiting_lower = floor_context.divide(hazard_lower, rate_decimal)
        absolute_lower = floor_context.add(start_decimal, waiting_lower)
    except decimal.DecimalException as error:
        raise PluginBridgeOperationalThinningError(
            "waiting lower endpoint could not be enclosed"
        ) from error

    if prefix == 0:
        return waiting_lower, None, absolute_lower, None

    lower_uniform = Fraction(prefix, denominator)
    lower_decimal = _exact_power_two_fraction_decimal(
        lower_uniform,
        name="waiting uniform lower endpoint",
    )
    lower_log_lower, _ = _ln_interval(lower_decimal, precision=precision)
    hazard_upper = _copy_negate(lower_log_lower)
    try:
        waiting_upper = ceiling_context.divide(hazard_upper, rate_decimal)
        absolute_upper = ceiling_context.add(start_decimal, waiting_upper)
    except decimal.DecimalException as error:
        raise PluginBridgeOperationalThinningError(
            "waiting upper endpoint could not be enclosed"
        ) from error
    if (
        not waiting_lower.is_finite()
        or not waiting_upper.is_finite()
        or not absolute_lower.is_finite()
        or not absolute_upper.is_finite()
        or waiting_lower < 0
        or waiting_lower > waiting_upper
        or absolute_lower > absolute_upper
    ):
        raise PluginBridgeOperationalThinningError(
            "waiting-time Decimal interval is invalid"
        )
    return waiting_lower, waiting_upper, absolute_lower, absolute_upper


def _same_optional_float(left: object, right: object) -> bool:
    if left is None or right is None:
        return left is right
    return type(left) is float and type(right) is float and _same_float(left, right)


def _waiting_trace(
    envelope_rate: float,
    clock_start: float,
    right_endpoint: float,
    raw_words: Tuple[int, ...],
) -> Optional[Mapping[str, object]]:
    rate_value = _clock_float(
        envelope_rate,
        name="waiting envelope rate",
        nonnegative=True,
    )
    start_value = _clock_float(
        clock_start,
        name="clock_start",
        nonnegative=True,
    )
    end_value = _clock_float(
        right_endpoint,
        name="right_endpoint",
        nonnegative=True,
    )
    if end_value < start_value:
        raise ValueError("right_endpoint must not precede clock_start")
    if type(raw_words) is not tuple:
        raise TypeError("waiting raw words must be an exact tuple")
    if len(raw_words) > OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS:
        raise ValueError("waiting trace exceeds the raw-word limit")
    for word in raw_words:
        if type(word) is not int or isinstance(word, bool):
            raise TypeError("raw Philox words must be exact integers")
        if not 0 <= word < 1 << OPERATIONAL_THINNING_RAW_WORD_BITS:
            raise ValueError("raw Philox word is outside uint64 range")

    zero_rate = rate_value == 0.0
    zero_duration = _same_float(start_value, end_value)
    if zero_rate or zero_duration:
        if raw_words:
            raise ValueError("a deterministic hold must consume no raw words")
        return {
            "candidate_due": False,
            "horizon_exhausted": True,
            "reference_intensity_zero": zero_rate,
            "zero_duration": zero_duration,
            "waiting_time": None,
            "proposal_time": None,
            "waiting_interval_lower_bound": None,
            "waiting_interval_upper_bound": None,
            "proposal_interval_lower_bound": None,
            "proposal_interval_upper_bound": None,
            "decimal_precision_used": 0,
            "raw_words_consumed": 0,
        }
    if rate_value < sys.float_info.min:
        raise ArithmeticError("active waiting envelope must be normal binary64")
    if not raw_words:
        return None

    exact_rate = _rate_require_fraction_size(
        _fraction(rate_value),
        name="waiting envelope rate",
    )
    exact_start = _rate_require_fraction_size(
        _fraction(start_value),
        name="waiting clock start",
    )
    exact_end = _rate_require_fraction_size(
        _fraction(end_value),
        name="waiting right endpoint",
    )
    exact_remaining = _rate_require_fraction_size(
        exact_end - exact_start,
        name="waiting remaining duration",
    )
    remaining_decimal = _exact_power_two_fraction_decimal(
        exact_remaining,
        name="waiting remaining duration",
    )

    prefix = 0
    for word_index, word in enumerate(raw_words, start=1):
        prefix = (prefix << OPERATIONAL_THINNING_RAW_WORD_BITS) | word
        bit_count = word_index * OPERATIONAL_THINNING_RAW_WORD_BITS
        previous = None
        for precision in _precision_schedule():
            interval = _waiting_interval_at_precision(
                prefix,
                bit_count,
                exact_rate,
                exact_start,
                precision=precision,
            )
            waiting_lower, waiting_upper, absolute_lower, absolute_upper = interval
            if previous is not None:
                old_wait_lower, old_wait_upper, old_abs_lower, old_abs_upper = previous
                if waiting_lower < old_wait_lower or absolute_lower < old_abs_lower:
                    raise PluginBridgeOperationalThinningError(
                        "adaptive waiting intervals are not nested"
                    )
                if old_wait_upper is not None and (
                    waiting_upper is None or waiting_upper > old_wait_upper
                ):
                    raise PluginBridgeOperationalThinningError(
                        "adaptive waiting intervals are not nested"
                    )
                if old_abs_upper is not None and (
                    absolute_upper is None or absolute_upper > old_abs_upper
                ):
                    raise PluginBridgeOperationalThinningError(
                        "adaptive waiting intervals are not nested"
                    )
            previous = interval
            if precision < OPERATIONAL_THINNING_DECIMAL_AUDIT_PRECISION:
                continue

            if waiting_lower > remaining_decimal:
                return {
                    "candidate_due": False,
                    "horizon_exhausted": True,
                    "reference_intensity_zero": False,
                    "zero_duration": False,
                    "waiting_time": None,
                    "proposal_time": None,
                    "waiting_interval_lower_bound": None,
                    "waiting_interval_upper_bound": None,
                    "proposal_interval_lower_bound": None,
                    "proposal_interval_upper_bound": None,
                    "decimal_precision_used": precision,
                    "raw_words_consumed": word_index,
                }
            if waiting_upper is None or absolute_upper is None:
                continue
            if waiting_upper > remaining_decimal:
                continue
            try:
                rounded_wait_lower = _rate_round_fraction_once(
                    Fraction(waiting_lower),
                    name="waiting lower rounded endpoint",
                )
                rounded_wait_upper = _rate_round_fraction_once(
                    Fraction(waiting_upper),
                    name="waiting upper rounded endpoint",
                )
                rounded_time_lower = _rate_round_fraction_once(
                    Fraction(absolute_lower),
                    name="proposal-time lower rounded endpoint",
                )
                rounded_time_upper = _rate_round_fraction_once(
                    Fraction(absolute_upper),
                    name="proposal-time upper rounded endpoint",
                )
            except ConfigurationTotalizedJumpRateError:
                continue
            if not _same_float(rounded_wait_lower, rounded_wait_upper):
                continue
            if not _same_float(rounded_time_lower, rounded_time_upper):
                continue
            waiting_time = _canonical_zero(rounded_wait_lower)
            proposal_time = _canonical_zero(rounded_time_lower)
            if waiting_time <= 0.0:
                raise PluginBridgeOperationalThinningError(
                    "positive waiting time rounded to zero"
                )
            if proposal_time <= start_value:
                raise PluginBridgeOperationalThinningError(
                    "proposal timestamp does not advance the operational clock"
                )
            if proposal_time >= end_value:
                raise PluginBridgeOperationalThinningError(
                    "interior proposal timestamp collapsed to a clock boundary"
                )
            return {
                "candidate_due": True,
                "horizon_exhausted": False,
                "reference_intensity_zero": False,
                "zero_duration": False,
                "waiting_time": waiting_time,
                "proposal_time": proposal_time,
                "waiting_interval_lower_bound": _decimal_floor_binary64(
                    waiting_lower,
                    name="waiting interval",
                ),
                "waiting_interval_upper_bound": _decimal_ceiling_binary64(
                    waiting_upper,
                    name="waiting interval",
                ),
                "proposal_interval_lower_bound": _decimal_floor_binary64(
                    absolute_lower,
                    name="proposal-time interval",
                ),
                "proposal_interval_upper_bound": _decimal_ceiling_binary64(
                    absolute_upper,
                    name="proposal-time interval",
                ),
                "decimal_precision_used": precision,
                "raw_words_consumed": word_index,
            }
    return None


def _framed_hash_update(digest: "hashlib._Hash", payload: bytes) -> None:
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)


def _rng_state_sha256(state: object) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-plugin-bridge-philox-state-v1\x00")
    nodes = [0]

    def update(value: object, depth: int) -> None:
        nodes[0] += 1
        if nodes[0] > _MAX_RNG_STATE_NODES or depth > _MAX_RNG_STATE_DEPTH:
            raise ValueError("Philox state exceeds the digest resource limit")
        if value is None:
            digest.update(b"N")
            return
        if type(value) is bool:
            digest.update(b"B1" if value else b"B0")
            return
        if isinstance(value, np.integer):
            value = int(value)
        if type(value) is int:
            digest.update(b"I")
            sign = b"-" if value < 0 else b"+"
            magnitude = abs(value)
            encoded = magnitude.to_bytes(
                max(1, (magnitude.bit_length() + 7) // 8),
                "big",
                signed=False,
            )
            _framed_hash_update(digest, sign + encoded)
            return
        if type(value) is str:
            digest.update(b"S")
            _framed_hash_update(digest, value.encode("utf-8"))
            return
        if type(value) is dict:
            digest.update(b"D")
            keys = tuple(sorted(value))
            for key in keys:
                if type(key) is not str:
                    raise TypeError("Philox state mappings require text keys")
                update(key, depth + 1)
                update(value[key], depth + 1)
            digest.update(b"d")
            return
        if type(value) is tuple:
            digest.update(b"T")
            for item in value:
                update(item, depth + 1)
            digest.update(b"t")
            return
        if type(value) is np.ndarray:
            if value.nbytes > _MAX_RNG_STATE_ARRAY_BYTES:
                raise ValueError("Philox state array exceeds the byte limit")
            if value.dtype.hasobject:
                raise TypeError("Philox state arrays cannot contain objects")
            digest.update(b"A")
            _framed_hash_update(digest, value.dtype.str.encode("ascii"))
            update(tuple(int(dimension) for dimension in value.shape), depth + 1)
            _framed_hash_update(digest, value.tobytes(order="C"))
            return
        raise TypeError(
            "unsupported Philox state value of type %s" % type(value).__name__
        )

    update(state, 0)
    return digest.hexdigest()


def _require_philox_rng(rng: object) -> np.random.Generator:
    if type(rng) is not np.random.Generator:
        raise TypeError("rng must be an exact numpy.random.Generator")
    if type(rng.bit_generator) is not np.random.Philox:
        raise TypeError("rng must use the exact numpy.random.Philox bit generator")
    state = rng.bit_generator.state
    if type(state) is not dict or state.get("bit_generator") != "Philox":
        raise ValueError("rng does not expose the expected Philox state schema")
    _rng_state_sha256(state)
    return rng


def _clone_philox_generator(
    rng: np.random.Generator,
) -> Tuple[np.random.Generator, str]:
    checked = _require_philox_rng(rng)
    state = copy.deepcopy(checked.bit_generator.state)
    before = _rng_state_sha256(state)
    shadow_bit_generator = np.random.Philox(0)
    shadow_bit_generator.state = copy.deepcopy(state)
    return np.random.Generator(shadow_bit_generator), before


class _PhiloxRaw64Session:
    __slots__ = ("rng", "shadow", "state_before_sha256", "words")

    def __init__(self, rng: object) -> None:
        checked = _require_philox_rng(rng)
        shadow, before = _clone_philox_generator(checked)
        self.rng = checked
        self.shadow = shadow
        self.state_before_sha256 = before
        self.words = []

    def draw_word(self) -> int:
        live = int(self.rng.bit_generator.random_raw())
        shadow = int(self.shadow.bit_generator.random_raw())
        if live != shadow:
            raise PluginBridgeOperationalThinningError(
                "Philox stream changed during raw-word consumption"
            )
        if not 0 <= live < 1 << OPERATIONAL_THINNING_RAW_WORD_BITS:
            raise PluginBridgeOperationalThinningError(
                "Philox did not return a full-range uint64 word"
            )
        self.words.append(live)
        return live

    def finish(self) -> str:
        live = _rng_state_sha256(self.rng.bit_generator.state)
        shadow = _rng_state_sha256(self.shadow.bit_generator.state)
        if live != shadow:
            raise PluginBridgeOperationalThinningError(
                "Philox stream changed outside the audited raw-word sequence"
            )
        return live


def _thinning_runtime_sha256() -> str:
    probe = np.random.Generator(np.random.Philox(0))
    probe_word = int(probe.bit_generator.random_raw())
    if not 0 <= probe_word < 1 << OPERATIONAL_THINNING_RAW_WORD_BITS:
        raise RuntimeError("Philox raw64 runtime probe failed")
    decimal_probe = _decimal_context(
        OPERATIONAL_THINNING_DECIMAL_PRIMARY_PRECISION,
        ROUND_HALF_EVEN,
    )
    decimal_traps = tuple(
        sorted(
            signal.__name__
            for signal, enabled in decimal_probe.traps.items()
            if enabled
        )
    )
    return _semantic_digest(
        {
            "domain": "plugin-bridge-operational-thinning-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "philox_type_module": np.random.Philox.__module__,
            "philox_type_name": np.random.Philox.__name__,
            "philox_seed_zero_first_raw64": probe_word,
            "decimal_module_version": getattr(decimal, "__version__", "unknown"),
            "libmpdec_version": getattr(
                decimal,
                "__libmpdec_version__",
                "unknown",
            ),
            "waiting_policy": PLUGIN_BRIDGE_OPERATIONAL_WAITING_POLICY,
            "acceptance_policy": PLUGIN_BRIDGE_OPERATIONAL_ACCEPTANCE_POLICY,
            "decimal_primary_precision": (
                OPERATIONAL_THINNING_DECIMAL_PRIMARY_PRECISION
            ),
            "decimal_audit_precision": (OPERATIONAL_THINNING_DECIMAL_AUDIT_PRECISION),
            "decimal_max_precision": OPERATIONAL_THINNING_DECIMAL_MAX_PRECISION,
            "decimal_precision_schedule": _precision_schedule(),
            "decimal_min_exponent": _DECIMAL_MIN_EXPONENT,
            "decimal_max_exponent": _DECIMAL_MAX_EXPONENT,
            "decimal_clamp": decimal_probe.clamp,
            "decimal_capitals": decimal_probe.capitals,
            "decimal_round_half_even": ROUND_HALF_EVEN,
            "decimal_round_floor": ROUND_FLOOR,
            "decimal_round_ceiling": ROUND_CEILING,
            "decimal_traps": decimal_traps,
            "maximum_waiting_raw64_words": (
                OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS
            ),
            "maximum_bernoulli_trials": (OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS),
            "maximum_ratio_bits": OPERATIONAL_THINNING_MAX_RATIO_BITS,
            "raw_word_bits": OPERATIONAL_THINNING_RAW_WORD_BITS,
            "maximum_rng_state_nodes": _MAX_RNG_STATE_NODES,
            "maximum_rng_state_depth": _MAX_RNG_STATE_DEPTH,
            "maximum_rng_state_array_bytes": _MAX_RNG_STATE_ARRAY_BYTES,
            "binary64_probe": _require_binary64_environment(),
        }
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: value for name, value in values.items() if name != "certificate_sha256"
    }


@dataclass(frozen=True, eq=False, init=False)
class OperationalThinningCertificate:
    """Transitive certificate for one frozen local thinning-decision layer."""

    schema_version: str
    certificate_scope: str
    thinning_policy: str
    waiting_policy: str
    acceptance_policy: str
    thinning_role_sha256: str
    process_parameter_sha256: str
    rate_certificate_sha256: str
    rate_role_sha256: str
    rate_runtime_sha256: str
    target_policy: str
    rate_policy: str
    thinning_runtime_sha256: str
    decimal_primary_precision: int
    decimal_audit_precision: int
    decimal_max_precision: int
    maximum_waiting_raw64_words: int
    maximum_bernoulli_trials: int
    maximum_ratio_bits: int
    raw_word_bits: int
    philox_raw64_required: bool
    ideal_prefix_uniform_waiting_clock_certified: bool
    directed_waiting_interval_certified: bool
    successful_timestamp_correct_rounding_certified: bool
    exact_represented_ratio_authoritative: bool
    variable_bit_exact_bernoulli_certified: bool
    no_rng_structural_hold_certified: bool
    post_clock_reference_route_sequencing_certified: bool
    successful_local_decision_certified: bool
    exact_active_controlled_total_exit_computed: bool
    analytic_target_preserved: bool
    conditional_posterior_or_doob_target: bool
    rounded_detailed_balance_or_stationarity_certified: bool
    all_route_rate_totality_certified: bool
    sampler_liveness_certified: bool
    counter_key_lineage_contract_certified: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalThinningCertificate cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("operational thinning certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational thinning certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "plugin-bridge-operational-thinning-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational thinning certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(OperationalThinningCertificate.__annotations__)


def _validate_certificate(certificate: object) -> OperationalThinningCertificate:
    if type(certificate) is not OperationalThinningCertificate:
        raise TypeError("certificate must be an exact OperationalThinningCertificate")
    expected_text = {
        "schema_version": PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCOPE,
        "thinning_policy": PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY,
        "waiting_policy": PLUGIN_BRIDGE_OPERATIONAL_WAITING_POLICY,
        "acceptance_policy": PLUGIN_BRIDGE_OPERATIONAL_ACCEPTANCE_POLICY,
        "target_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "rate_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("operational thinning certificate %s differs" % name)
    for name in (
        "thinning_role_sha256",
        "process_parameter_sha256",
        "rate_certificate_sha256",
        "rate_role_sha256",
        "rate_runtime_sha256",
        "thinning_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    for name, expected in (
        ("decimal_primary_precision", OPERATIONAL_THINNING_DECIMAL_PRIMARY_PRECISION),
        ("decimal_audit_precision", OPERATIONAL_THINNING_DECIMAL_AUDIT_PRECISION),
        ("decimal_max_precision", OPERATIONAL_THINNING_DECIMAL_MAX_PRECISION),
        (
            "maximum_waiting_raw64_words",
            OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS,
        ),
        ("maximum_bernoulli_trials", OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS),
        ("maximum_ratio_bits", OPERATIONAL_THINNING_MAX_RATIO_BITS),
        ("raw_word_bits", OPERATIONAL_THINNING_RAW_WORD_BITS),
    ):
        value = getattr(certificate, name)
        if type(value) is not int or isinstance(value, bool) or value != expected:
            raise ValueError("operational thinning certificate %s differs" % name)
    true_flags = (
        "philox_raw64_required",
        "ideal_prefix_uniform_waiting_clock_certified",
        "directed_waiting_interval_certified",
        "successful_timestamp_correct_rounding_certified",
        "exact_represented_ratio_authoritative",
        "variable_bit_exact_bernoulli_certified",
        "no_rng_structural_hold_certified",
        "post_clock_reference_route_sequencing_certified",
        "successful_local_decision_certified",
        "passed",
    )
    false_flags = (
        "exact_active_controlled_total_exit_computed",
        "analytic_target_preserved",
        "conditional_posterior_or_doob_target",
        "rounded_detailed_balance_or_stationarity_certified",
        "all_route_rate_totality_certified",
        "sampler_liveness_certified",
        "counter_key_lineage_contract_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "full_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("operational thinning positive flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("operational thinning negative flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    if certificate.certificate_sha256 != _semantic_digest(_certificate_payload(values)):
        raise ValueError("operational thinning certificate digest differs")
    return certificate


def _make_certificate(
    rate_certificate: TotalizedJumpRateEnvelopeCertificate,
    *,
    thinning_role_sha256: str,
) -> OperationalThinningCertificate:
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCOPE,
        "thinning_policy": PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY,
        "waiting_policy": PLUGIN_BRIDGE_OPERATIONAL_WAITING_POLICY,
        "acceptance_policy": PLUGIN_BRIDGE_OPERATIONAL_ACCEPTANCE_POLICY,
        "thinning_role_sha256": thinning_role_sha256,
        "process_parameter_sha256": rate_certificate.process_parameter_sha256,
        "rate_certificate_sha256": rate_certificate.certificate_sha256,
        "rate_role_sha256": rate_certificate.rate_role_sha256,
        "rate_runtime_sha256": rate_certificate.rate_runtime_sha256,
        "target_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "rate_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
        "thinning_runtime_sha256": _thinning_runtime_sha256(),
        "decimal_primary_precision": OPERATIONAL_THINNING_DECIMAL_PRIMARY_PRECISION,
        "decimal_audit_precision": OPERATIONAL_THINNING_DECIMAL_AUDIT_PRECISION,
        "decimal_max_precision": OPERATIONAL_THINNING_DECIMAL_MAX_PRECISION,
        "maximum_waiting_raw64_words": (OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS),
        "maximum_bernoulli_trials": OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS,
        "maximum_ratio_bits": OPERATIONAL_THINNING_MAX_RATIO_BITS,
        "raw_word_bits": OPERATIONAL_THINNING_RAW_WORD_BITS,
        "philox_raw64_required": True,
        "ideal_prefix_uniform_waiting_clock_certified": True,
        "directed_waiting_interval_certified": True,
        "successful_timestamp_correct_rounding_certified": True,
        "exact_represented_ratio_authoritative": True,
        "variable_bit_exact_bernoulli_certified": True,
        "no_rng_structural_hold_certified": True,
        "post_clock_reference_route_sequencing_certified": True,
        "successful_local_decision_certified": True,
        "exact_active_controlled_total_exit_computed": False,
        "analytic_target_preserved": False,
        "conditional_posterior_or_doob_target": False,
        "rounded_detailed_balance_or_stationarity_certified": False,
        "all_route_rate_totality_certified": False,
        "sampler_liveness_certified": False,
        "counter_key_lineage_contract_certified": False,
        "continuous_drift_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "full_sampler_admissible": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return OperationalThinningCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _waiting_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "waiting_draw_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class OperationalWaitingTimeDraw:
    """Sealed resolution of one local envelope clock against a finite interval."""

    certificate: OperationalThinningCertificate
    certificate_sha256: str
    intensity_sha256: str
    envelope_sha256: str
    process_parameter_sha256: str
    source_state_sha256: str
    frozen_reverse_time: float
    frozen_direct_time: float
    clock_start: float
    right_endpoint: float
    envelope_rate: float
    candidate_due: bool
    horizon_exhausted: bool
    reference_intensity_zero: bool
    zero_duration: bool
    waiting_time: Optional[float]
    proposal_time: Optional[float]
    waiting_interval_lower_bound: Optional[float]
    waiting_interval_upper_bound: Optional[float]
    proposal_interval_lower_bound: Optional[float]
    proposal_interval_upper_bound: Optional[float]
    decimal_precision_used: int
    rng_bit_generator: str
    raw_word_bits: int
    raw_words: Tuple[int, ...]
    raw_words_consumed: int
    rng_state_before_sha256: str
    rng_state_after_sha256: str
    candidate_route_draw_admissible: bool
    waiting_draw_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalWaitingTimeDraw cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _WAITING_TOKEN:
            raise TypeError("waiting-time draws are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("waiting-time draw fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("waiting-time certificate digest differs")
        for name in (
            "certificate_sha256",
            "intensity_sha256",
            "envelope_sha256",
            "process_parameter_sha256",
            "source_state_sha256",
            "rng_state_before_sha256",
            "rng_state_after_sha256",
            "waiting_draw_sha256",
        ):
            _require_sha256(values[name], name="waiting.%s" % name)
        if values["process_parameter_sha256"] != certificate.process_parameter_sha256:
            raise ValueError("waiting-time process digest differs")
        for name in (
            "frozen_reverse_time",
            "frozen_direct_time",
            "clock_start",
            "right_endpoint",
            "envelope_rate",
        ):
            _clock_float(
                values[name],
                name="waiting.%s" % name,
                nonnegative=True,
            )
        if values["rng_bit_generator"] != "numpy.random.Philox":
            raise ValueError("waiting-time RNG type differs")
        for name in (
            "decimal_precision_used",
            "raw_word_bits",
            "raw_words_consumed",
        ):
            _exact_nonnegative_integer(
                values[name],
                name="waiting.%s" % name,
            )
        if values["raw_word_bits"] != OPERATIONAL_THINNING_RAW_WORD_BITS:
            raise ValueError("waiting-time raw word width differs")
        if type(values["raw_words"]) is not tuple:
            raise TypeError("waiting-time raw words must be an exact tuple")
        trace = _waiting_trace(
            values["envelope_rate"],
            values["clock_start"],
            values["right_endpoint"],
            values["raw_words"],
        )
        if trace is None:
            raise PluginBridgeOperationalThinningError(
                "waiting-time raw prefix does not resolve a result"
            )
        for name, expected in trace.items():
            supplied = values[name]
            if type(expected) is float or expected is None:
                if not _same_optional_float(supplied, expected):
                    raise ValueError("waiting-time field %s differs" % name)
            elif supplied != expected:
                raise ValueError("waiting-time field %s differs" % name)
        if values["raw_words_consumed"] != len(values["raw_words"]):
            raise ValueError("waiting-time raw-word count differs")
        if values["candidate_route_draw_admissible"] is not trace["candidate_due"]:
            raise ValueError("waiting-time route admission differs")
        for name in (
            "candidate_due",
            "horizon_exhausted",
            "reference_intensity_zero",
            "zero_duration",
            "candidate_route_draw_admissible",
        ):
            if type(values[name]) is not bool:
                raise TypeError("waiting-time %s must be boolean" % name)
        if not values["raw_words"]:
            if values["rng_state_before_sha256"] != values["rng_state_after_sha256"]:
                raise ValueError("no-RNG waiting hold changed the Philox state")
        elif values["rng_state_before_sha256"] == values["rng_state_after_sha256"]:
            raise ValueError("active waiting draw did not advance the Philox state")
        expected_digest = _semantic_digest(_waiting_payload(values))
        if values["waiting_draw_sha256"] != expected_digest:
            raise ValueError("waiting-time draw digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("waiting-time draws are not pickle objects")


def _waiting_fields() -> Tuple[str, ...]:
    return tuple(OperationalWaitingTimeDraw.__annotations__)


def _route_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "candidate", "route_draw_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class OperationalReferenceRouteDraw:
    """One process-owned normalized-reference route drawn after a clock hit."""

    certificate: OperationalThinningCertificate
    certificate_sha256: str
    waiting_draw_sha256: str
    intensity_sha256: str
    envelope_sha256: str
    candidate: ProcessValidReferenceJump
    candidate_sha256: str
    process_parameter_sha256: str
    source_state_sha256: str
    destination_state_sha256: str
    frozen_reverse_time: float
    frozen_direct_time: float
    proposal_time: float
    edit_kind: str
    rng_bit_generator: str
    rng_state_before_sha256: str
    rng_state_after_sha256: str
    route_draw_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalReferenceRouteDraw cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ROUTE_TOKEN:
            raise TypeError("operational route draws are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational route fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("route certificate digest differs")
        for name in (
            "certificate_sha256",
            "waiting_draw_sha256",
            "intensity_sha256",
            "envelope_sha256",
            "candidate_sha256",
            "process_parameter_sha256",
            "source_state_sha256",
            "destination_state_sha256",
            "rng_state_before_sha256",
            "rng_state_after_sha256",
            "route_draw_sha256",
        ):
            _require_sha256(values[name], name="route.%s" % name)
        if values["process_parameter_sha256"] != certificate.process_parameter_sha256:
            raise ValueError("route process digest differs")
        candidate = values["candidate"]
        if type(candidate) is not ProcessValidReferenceJump:
            raise TypeError("route candidate has the wrong exact type")
        if values["candidate_sha256"] != _candidate_sha256(candidate):
            raise ValueError("route candidate digest differs")
        if values["source_state_sha256"] != _configuration_sha256(
            candidate.source_configuration
        ):
            raise ValueError("route source-state digest differs")
        if values["destination_state_sha256"] != _configuration_sha256(
            candidate.destination_configuration
        ):
            raise ValueError("route destination-state digest differs")
        if values["edit_kind"] != candidate.kind.value:
            raise ValueError("route edit kind differs")
        for name, expected in (
            ("frozen_reverse_time", candidate.reverse_time),
            ("frozen_direct_time", candidate.direct_time),
        ):
            supplied = _clock_float(
                values[name],
                name="route.%s" % name,
                nonnegative=True,
            )
            if not _same_float(supplied, expected):
                raise ValueError("route %s differs" % name)
        _clock_float(
            values["proposal_time"],
            name="route.proposal_time",
            nonnegative=True,
        )
        if values["rng_bit_generator"] != "numpy.random.Philox":
            raise ValueError("route RNG type differs")
        if values["rng_state_before_sha256"] == values["rng_state_after_sha256"]:
            raise ValueError("route draw did not advance the Philox state")
        expected_digest = _semantic_digest(_route_payload(values))
        if values["route_draw_sha256"] != expected_digest:
            raise ValueError("route draw digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational route draws are not pickle objects")


def _route_fields() -> Tuple[str, ...]:
    return tuple(OperationalReferenceRouteDraw.__annotations__)


def _exact_acceptance_ratio(
    candidate_rate: float,
    envelope_rate: float,
) -> Fraction:
    candidate = _clock_float(
        candidate_rate,
        name="candidate represented integrand",
        nonnegative=True,
    )
    envelope = _clock_float(
        envelope_rate,
        name="acceptance represented envelope",
        nonnegative=True,
    )
    if candidate < sys.float_info.min or envelope < sys.float_info.min:
        raise ArithmeticError("acceptance rates must be normal positive binary64")
    ratio = Fraction.from_float(candidate) / Fraction.from_float(envelope)
    if not Fraction(0) < ratio <= Fraction(1):
        raise ValueError("exact represented acceptance ratio is outside (0, 1]")
    if (
        ratio.numerator.bit_length() > OPERATIONAL_THINNING_MAX_RATIO_BITS
        or ratio.denominator.bit_length() > OPERATIONAL_THINNING_MAX_RATIO_BITS
    ):
        raise PluginBridgeOperationalThinningError(
            "exact represented acceptance ratio exceeds the bit limit"
        )
    return ratio


def _bernoulli_trace(
    numerator: int,
    denominator: int,
    raw_words: Tuple[int, ...],
) -> Mapping[str, object]:
    if type(numerator) is not int or isinstance(numerator, bool):
        raise TypeError("Bernoulli numerator must be an exact integer")
    if type(denominator) is not int or isinstance(denominator, bool):
        raise TypeError("Bernoulli denominator must be an exact integer")
    if not 0 <= numerator <= denominator or denominator <= 0:
        raise ValueError("Bernoulli ratio must lie in [0, 1]")
    if (
        numerator.bit_length() > OPERATIONAL_THINNING_MAX_RATIO_BITS
        or denominator.bit_length() > OPERATIONAL_THINNING_MAX_RATIO_BITS
    ):
        raise ValueError("Bernoulli ratio exceeds the bit limit")
    ratio = Fraction(numerator, denominator)
    if ratio.numerator != numerator or ratio.denominator != denominator:
        raise ValueError("Bernoulli ratio must be stored in reduced form")
    if type(raw_words) is not tuple:
        raise TypeError("Bernoulli raw words must be an exact tuple")

    if numerator == 0 or numerator == denominator:
        if raw_words:
            raise ValueError("deterministic Bernoulli must consume no words")
        return {
            "bit_width": 0,
            "words_per_trial": 0,
            "trial_count": 0,
            "discarded_low_bits_per_trial": 0,
            "final_uniform_integer": None,
            "accepted": numerator == denominator,
        }

    bit_width = (denominator - 1).bit_length()
    words_per_trial = (
        bit_width + OPERATIONAL_THINNING_RAW_WORD_BITS - 1
    ) // OPERATIONAL_THINNING_RAW_WORD_BITS
    if len(raw_words) == 0 or len(raw_words) % words_per_trial:
        raise ValueError("Bernoulli raw-word trace has an incomplete trial")
    trial_count = len(raw_words) // words_per_trial
    if trial_count > OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS:
        raise ValueError("Bernoulli trace exceeds the trial limit")
    for word in raw_words:
        if type(word) is not int or isinstance(word, bool):
            raise TypeError("Bernoulli raw words must contain exact integers")
        if not 0 <= word < 1 << OPERATIONAL_THINNING_RAW_WORD_BITS:
            raise ValueError("Bernoulli raw word is outside uint64 range")
    discarded = words_per_trial * OPERATIONAL_THINNING_RAW_WORD_BITS - bit_width
    final_value = None
    for trial in range(trial_count):
        combined = 0
        offset = trial * words_per_trial
        for word in raw_words[offset : offset + words_per_trial]:
            combined = (combined << OPERATIONAL_THINNING_RAW_WORD_BITS) | word
        value = combined >> discarded
        if value < denominator:
            if trial != trial_count - 1:
                raise ValueError("Bernoulli trace continued after a resolved trial")
            final_value = value
            break
    if final_value is None:
        raise PluginBridgeOperationalThinningError(
            "Bernoulli raw-word trace does not resolve a decision"
        )
    return {
        "bit_width": bit_width,
        "words_per_trial": words_per_trial,
        "trial_count": trial_count,
        "discarded_low_bits_per_trial": discarded,
        "final_uniform_integer": final_value,
        "accepted": final_value < numerator,
    }


def _draw_exact_bernoulli(
    ratio: Fraction,
    session: _PhiloxRaw64Session,
) -> Mapping[str, object]:
    if ratio <= 0 or ratio > 1:
        raise ValueError("acceptance ratio must lie in (0, 1]")
    if ratio == 1:
        return _bernoulli_trace(1, 1, ())
    denominator = ratio.denominator
    bit_width = (denominator - 1).bit_length()
    words_per_trial = (
        bit_width + OPERATIONAL_THINNING_RAW_WORD_BITS - 1
    ) // OPERATIONAL_THINNING_RAW_WORD_BITS
    discarded = words_per_trial * OPERATIONAL_THINNING_RAW_WORD_BITS - bit_width
    words = []
    for _ in range(OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS):
        combined = 0
        for _ in range(words_per_trial):
            word = session.draw_word()
            words.append(word)
            combined = (combined << OPERATIONAL_THINNING_RAW_WORD_BITS) | word
        value = combined >> discarded
        if value < denominator:
            return _bernoulli_trace(
                ratio.numerator,
                ratio.denominator,
                tuple(words),
            )
    raise PluginBridgeOperationalThinningError(
        "exact Bernoulli exhausted its bounded denominator-rejection trials"
    )


def _configuration_semantic_payload(
    configuration: TransformedConfiguration,
) -> Mapping[str, object]:
    """Return exact plain data for a validated canonical configuration."""

    state_sha256 = _configuration_sha256(configuration)
    return {
        "state_sha256": state_sha256,
        "events": tuple(
            (event.event_type, tuple(event.coordinates)) for event in configuration
        ),
    }


def _decision_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "route_draw", "decision_sha256"}
    payload = {name: value for name, value in values.items() if name not in omitted}
    payload["result_configuration"] = _configuration_semantic_payload(
        values["result_configuration"]  # type: ignore[arg-type]
    )
    return payload


@dataclass(frozen=True, eq=False, init=False)
class OperationalAcceptanceDecision:
    """Exact Bernoulli for the rational quotient of represented ``I`` and ``E``."""

    certificate: OperationalThinningCertificate
    certificate_sha256: str
    waiting_draw_sha256: str
    route_draw: OperationalReferenceRouteDraw
    route_draw_sha256: str
    envelope_sha256: str
    rate_evaluation_sha256: str
    candidate_sha256: str
    source_state_sha256: str
    destination_state_sha256: str
    candidate_measure_integrand: float
    controlled_total_exit_upper_bound: float
    exact_acceptance_numerator: int
    exact_acceptance_denominator: int
    bit_width: int
    words_per_trial: int
    trial_count: int
    discarded_low_bits_per_trial: int
    raw_words: Tuple[int, ...]
    final_uniform_integer: Optional[int]
    accepted: bool
    result_configuration: TransformedConfiguration
    result_state_sha256: str
    envelope_reusable_after_decision: bool
    fresh_envelope_required: bool
    rng_bit_generator: str
    rng_state_before_sha256: str
    rng_state_after_sha256: str
    decision_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalAcceptanceDecision cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _DECISION_TOKEN:
            raise TypeError("operational acceptance decisions are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational acceptance fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("acceptance certificate digest differs")
        route_draw = values["route_draw"]
        if type(route_draw) is not OperationalReferenceRouteDraw:
            raise TypeError("acceptance route draw has the wrong exact type")
        if values["route_draw_sha256"] != route_draw.route_draw_sha256:
            raise ValueError("acceptance route digest differs")
        if values["waiting_draw_sha256"] != route_draw.waiting_draw_sha256:
            raise ValueError("acceptance waiting digest differs from route")
        for name in (
            "certificate_sha256",
            "waiting_draw_sha256",
            "route_draw_sha256",
            "envelope_sha256",
            "rate_evaluation_sha256",
            "candidate_sha256",
            "source_state_sha256",
            "destination_state_sha256",
            "result_state_sha256",
            "rng_state_before_sha256",
            "rng_state_after_sha256",
            "decision_sha256",
        ):
            _require_sha256(values[name], name="acceptance.%s" % name)
        candidate = route_draw.candidate
        if values["candidate_sha256"] != _candidate_sha256(candidate):
            raise ValueError("acceptance candidate digest differs")
        if values["source_state_sha256"] != route_draw.source_state_sha256:
            raise ValueError("acceptance source digest differs")
        if values["destination_state_sha256"] != route_draw.destination_state_sha256:
            raise ValueError("acceptance destination digest differs")
        ratio = _exact_acceptance_ratio(
            values["candidate_measure_integrand"],
            values["controlled_total_exit_upper_bound"],
        )
        for name in (
            "exact_acceptance_numerator",
            "exact_acceptance_denominator",
            "bit_width",
            "words_per_trial",
            "trial_count",
            "discarded_low_bits_per_trial",
        ):
            _exact_nonnegative_integer(
                values[name],
                name="acceptance.%s" % name,
            )
        if values["final_uniform_integer"] is not None:
            _exact_nonnegative_integer(
                values["final_uniform_integer"],
                name="acceptance.final_uniform_integer",
            )
        if (
            values["exact_acceptance_numerator"] != ratio.numerator
            or values["exact_acceptance_denominator"] != ratio.denominator
        ):
            raise ValueError("acceptance exact represented ratio differs")
        trace = _bernoulli_trace(
            ratio.numerator,
            ratio.denominator,
            values["raw_words"],
        )
        for name, expected in trace.items():
            if values[name] != expected:
                raise ValueError("acceptance field %s differs" % name)
        if type(values["accepted"]) is not bool:
            raise TypeError("acceptance decision must be boolean")
        expected_result = (
            candidate.destination_configuration
            if values["accepted"]
            else candidate.source_configuration
        )
        supplied_result_sha256 = _configuration_sha256(
            values["result_configuration"]  # type: ignore[arg-type]
        )
        expected_result_sha256 = _configuration_sha256(expected_result)
        if values["result_configuration"] != expected_result:
            raise ValueError("acceptance result configuration differs")
        if supplied_result_sha256 != expected_result_sha256:
            raise ValueError("acceptance result configuration digest differs")
        if values["result_state_sha256"] != supplied_result_sha256:
            raise ValueError("acceptance result-state digest differs")
        for name, expected in (
            ("envelope_reusable_after_decision", not values["accepted"]),
            ("fresh_envelope_required", values["accepted"]),
        ):
            if type(values[name]) is not bool or values[name] is not expected:
                raise ValueError("acceptance %s differs" % name)
        if values["rng_bit_generator"] != "numpy.random.Philox":
            raise ValueError("acceptance RNG type differs")
        if values["rng_state_before_sha256"] != route_draw.rng_state_after_sha256:
            raise ValueError("acceptance decision does not continue the route stream")
        if not values["raw_words"]:
            if values["rng_state_before_sha256"] != values["rng_state_after_sha256"]:
                raise ValueError("deterministic acceptance changed the Philox state")
        elif values["rng_state_before_sha256"] == values["rng_state_after_sha256"]:
            raise ValueError("random acceptance did not advance the Philox state")
        expected_digest = _semantic_digest(_decision_payload(values))
        if values["decision_sha256"] != expected_digest:
            raise ValueError("acceptance decision digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational acceptance decisions are not pickle objects")


def _decision_fields() -> Tuple[str, ...]:
    return tuple(OperationalAcceptanceDecision.__annotations__)


def _snapshot_fields(record: object, fields: Tuple[str, ...]) -> Mapping[str, object]:
    return {name: getattr(record, name) for name in fields}


def _record_unchanged(
    record: object,
    snapshot: Mapping[str, object],
    *,
    context: str,
) -> None:
    for name, before in snapshot.items():
        if not _field_matches(name, getattr(record, name), before):
            raise ValueError(
                "%s field %s changed during the operation" % (context, name)
            )


def _require_candidate_intensity_binding(
    candidate: ProcessValidReferenceJump,
    intensity: ReferenceCandidateIntensity,
) -> None:
    """Bind a validated candidate to the exact supplied local intensity."""

    if type(candidate) is not ProcessValidReferenceJump:
        raise TypeError("route candidate has the wrong exact type")
    if type(intensity) is not ReferenceCandidateIntensity:
        raise TypeError("route intensity has the wrong exact type")
    if _configuration_sha256(candidate.source_configuration) != (
        _configuration_sha256(intensity.source_configuration)
    ):
        raise ValueError("route candidate source differs from supplied intensity")
    for name in (
        "reverse_time",
        "direct_time",
        "reference_schedule_rate",
        "scheduled_reference_exit_rate",
    ):
        if not _same_float(getattr(candidate, name), getattr(intensity, name)):
            raise ValueError(
                "route candidate %s differs from supplied intensity" % name
            )
    if candidate.proposal.base_rates != intensity.base_rates:
        raise ValueError("route candidate base rates differ from supplied intensity")


class OperationalJumpThinning:
    """Immutable owner of one frozen local waiting/route/acceptance sequence."""

    __slots__ = ("_rate_owner", "_reference_composer", "_role", "_certificate")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalJumpThinning cannot be subclassed")

    def __init__(
        self,
        rate_owner: TotalizedConfigurationJumpRateEnvelope,
        reference_composer: ProcessValidReferenceJumpComposer,
        role: str,
        certificate: OperationalThinningCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("operational thinning owners require certification")
        if type(rate_owner) is not TotalizedConfigurationJumpRateEnvelope:
            raise TypeError("rate_owner has the wrong exact type")
        if type(reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference_composer has the wrong exact type")
        checked_role = _require_sha256(role, name="thinning_role_sha256")
        checked_certificate = _validate_certificate(certificate)
        if checked_certificate.thinning_role_sha256 != checked_role:
            raise ValueError("operational thinning role differs from certificate")
        object.__setattr__(self, "_rate_owner", rate_owner)
        object.__setattr__(self, "_reference_composer", reference_composer)
        object.__setattr__(self, "_role", checked_role)
        object.__setattr__(self, "_certificate", checked_certificate)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("OperationalJumpThinning is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("OperationalJumpThinning is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational thinning owners are not pickle objects")

    @property
    def certificate(self) -> OperationalThinningCertificate:
        return self._certificate

    @property
    def rate_owner(self) -> TotalizedConfigurationJumpRateEnvelope:
        return self._rate_owner

    @property
    def reference_composer(self) -> ProcessValidReferenceJumpComposer:
        return self._reference_composer

    def _require_live_binding(self) -> OperationalThinningCertificate:
        _require_binary64_environment()
        if type(self._rate_owner) is not TotalizedConfigurationJumpRateEnvelope:
            raise TypeError("rate owner has the wrong exact type")
        if type(self._reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference composer has the wrong exact type")
        if self._rate_owner.reference_composer is not self._reference_composer:
            raise ValueError("thinning and rate owners use different references")
        rate_certificate = self._rate_owner._require_live_binding()
        if self.certificate.thinning_runtime_sha256 != _thinning_runtime_sha256():
            raise ValueError("live thinning runtime differs from certificate")
        expected = _make_certificate(
            rate_certificate,
            thinning_role_sha256=self._role,
        )
        for name in _certificate_fields():
            if not _field_matches(
                name,
                getattr(self.certificate, name),
                getattr(expected, name),
            ):
                raise ValueError(
                    "operational thinning certificate field %s differs" % name
                )
        _require_binary64_environment()
        return self.certificate

    def _validate_parents(
        self,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
    ) -> Tuple[ReferenceCandidateIntensity, TotalizedJumpRateEnvelope]:
        checked_intensity = self._reference_composer.validate_candidate_intensity(
            intensity
        )
        checked_envelope = self._rate_owner.validate_envelope(
            envelope,
            checked_intensity,
        )
        return checked_intensity, checked_envelope

    def draw_waiting_time(
        self,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
        *,
        clock_start: object,
        right_endpoint: object,
        rng: np.random.Generator,
    ) -> OperationalWaitingTimeDraw:
        """Resolve one local proposal clock before any route or model work."""

        self._require_live_binding()
        checked_rng = _require_philox_rng(rng)
        checked_intensity, checked_envelope = self._validate_parents(
            intensity,
            envelope,
        )
        start = _clock_float(clock_start, name="clock_start", nonnegative=True)
        end = _clock_float(right_endpoint, name="right_endpoint", nonnegative=True)
        if end < start:
            raise ValueError("right_endpoint must not precede clock_start")
        intensity_sha = _intensity_sha256(checked_intensity)
        envelope_snapshot = _snapshot_fields(checked_envelope, _rate._envelope_fields())
        source_sha = _configuration_sha256(checked_intensity.source_configuration)
        envelope_rate = checked_envelope.controlled_total_exit_upper_bound
        if checked_envelope.reference_intensity_zero != checked_intensity.is_zero:
            raise ValueError("reference intensity and rate envelope zero flags differ")

        session = _PhiloxRaw64Session(checked_rng)
        trace = _waiting_trace(envelope_rate, start, end, ())
        if trace is None:
            for _ in range(OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS):
                session.draw_word()
                trace = _waiting_trace(
                    envelope_rate,
                    start,
                    end,
                    tuple(session.words),
                )
                if trace is not None:
                    break
        if trace is None:
            raise PluginBridgeOperationalThinningError(
                "waiting clock exhausted its raw64 resolution budget"
            )
        state_after = session.finish()

        self._require_live_binding()
        self._validate_parents(intensity, envelope)
        if intensity_sha != _intensity_sha256(intensity):
            raise ValueError("reference intensity changed during waiting draw")
        _record_unchanged(
            envelope,
            envelope_snapshot,
            context="rate envelope",
        )
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "intensity_sha256": intensity_sha,
            "envelope_sha256": checked_envelope.envelope_sha256,
            "process_parameter_sha256": self.certificate.process_parameter_sha256,
            "source_state_sha256": source_sha,
            "frozen_reverse_time": checked_intensity.reverse_time,
            "frozen_direct_time": checked_intensity.direct_time,
            "clock_start": start,
            "right_endpoint": end,
            "envelope_rate": envelope_rate,
            **trace,
            "rng_bit_generator": "numpy.random.Philox",
            "raw_word_bits": OPERATIONAL_THINNING_RAW_WORD_BITS,
            "raw_words": tuple(session.words),
            "rng_state_before_sha256": session.state_before_sha256,
            "rng_state_after_sha256": state_after,
            "candidate_route_draw_admissible": trace["candidate_due"],
            "waiting_draw_sha256": "0" * 64,
        }
        values["waiting_draw_sha256"] = _semantic_digest(_waiting_payload(values))
        result = OperationalWaitingTimeDraw(
            **values,
            _construction_token=_WAITING_TOKEN,
        )
        self.validate_waiting_time(result, intensity, envelope)
        if intensity_sha != _intensity_sha256(intensity):
            raise ValueError("reference intensity changed before waiting-time return")
        _record_unchanged(envelope, envelope_snapshot, context="rate envelope")
        self._require_live_binding()
        if _rng_state_sha256(checked_rng.bit_generator.state) != state_after:
            raise ValueError("Philox state changed before waiting-time return")
        return result

    def validate_waiting_time(
        self,
        waiting_draw: OperationalWaitingTimeDraw,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
    ) -> OperationalWaitingTimeDraw:
        """Replay a waiting-time record without consuming randomness."""

        if type(waiting_draw) is not OperationalWaitingTimeDraw:
            raise TypeError("waiting_draw has the wrong exact type")
        OperationalWaitingTimeDraw(
            **_snapshot_fields(waiting_draw, _waiting_fields()),
            _construction_token=_WAITING_TOKEN,
        )
        if waiting_draw.certificate is not self.certificate:
            raise ValueError("waiting draw belongs to a different thinning owner")
        checked_intensity, checked_envelope = self._validate_parents(
            intensity,
            envelope,
        )
        expected = {
            "intensity_sha256": _intensity_sha256(checked_intensity),
            "envelope_sha256": checked_envelope.envelope_sha256,
            "source_state_sha256": _configuration_sha256(
                checked_intensity.source_configuration
            ),
            "frozen_reverse_time": checked_intensity.reverse_time,
            "frozen_direct_time": checked_intensity.direct_time,
            "envelope_rate": checked_envelope.controlled_total_exit_upper_bound,
        }
        for name, value in expected.items():
            supplied = getattr(waiting_draw, name)
            if type(value) is float:
                if not _same_float(supplied, value):
                    raise ValueError("waiting draw %s differs from parent" % name)
            elif supplied != value:
                raise ValueError("waiting draw %s differs from parent" % name)
        self._require_live_binding()
        return waiting_draw

    def draw_reference_route(
        self,
        waiting_draw: OperationalWaitingTimeDraw,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
        *,
        rng: np.random.Generator,
    ) -> OperationalReferenceRouteDraw:
        """Draw one normalized-reference route after a certified clock hit."""

        self._require_live_binding()
        checked_rng = _require_philox_rng(rng)
        checked_waiting = self.validate_waiting_time(
            waiting_draw,
            intensity,
            envelope,
        )
        if not checked_waiting.candidate_due:
            raise ValueError("a reference route requires an in-interval clock hit")
        before = _rng_state_sha256(checked_rng.bit_generator.state)
        if before != checked_waiting.rng_state_after_sha256:
            raise ValueError("route RNG does not continue the waiting-time stream")
        checked_intensity, checked_envelope = self._validate_parents(
            intensity,
            envelope,
        )
        intensity_sha = _intensity_sha256(checked_intensity)
        envelope_snapshot = _snapshot_fields(checked_envelope, _rate._envelope_fields())
        waiting_snapshot = _snapshot_fields(checked_waiting, _waiting_fields())
        shadow_rng, shadow_before = _clone_philox_generator(checked_rng)
        if shadow_before != before:
            raise RuntimeError("shadow Philox state differs before route draw")
        candidate = self._reference_composer.sample_candidate_from_intensity(
            checked_intensity,
            rng=checked_rng,
        )
        shadow_candidate = self._reference_composer.sample_candidate_from_intensity(
            checked_intensity,
            rng=shadow_rng,
        )
        if candidate is None or shadow_candidate is None:
            raise RuntimeError(
                "a positive admitted route unexpectedly returned no jump"
            )
        candidate_sha = _candidate_sha256(candidate)
        if candidate_sha != _candidate_sha256(shadow_candidate):
            raise PluginBridgeOperationalThinningError(
                "live and shadow Philox route draws differ"
            )
        state_after = _rng_state_sha256(checked_rng.bit_generator.state)
        if state_after != _rng_state_sha256(shadow_rng.bit_generator.state):
            raise PluginBridgeOperationalThinningError(
                "live and shadow Philox route states differ"
            )
        candidate = self._reference_composer.validate_candidate(candidate)
        _require_candidate_intensity_binding(candidate, checked_intensity)
        self.validate_waiting_time(waiting_draw, intensity, envelope)
        self._require_live_binding()
        if intensity_sha != _intensity_sha256(intensity):
            raise ValueError("reference intensity changed during route draw")
        _record_unchanged(envelope, envelope_snapshot, context="rate envelope")
        _record_unchanged(waiting_draw, waiting_snapshot, context="waiting draw")
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "waiting_draw_sha256": waiting_snapshot["waiting_draw_sha256"],
            "intensity_sha256": intensity_sha,
            "envelope_sha256": checked_envelope.envelope_sha256,
            "candidate": candidate,
            "candidate_sha256": candidate_sha,
            "process_parameter_sha256": self.certificate.process_parameter_sha256,
            "source_state_sha256": _configuration_sha256(
                candidate.source_configuration
            ),
            "destination_state_sha256": _configuration_sha256(
                candidate.destination_configuration
            ),
            "frozen_reverse_time": candidate.reverse_time,
            "frozen_direct_time": candidate.direct_time,
            "proposal_time": waiting_snapshot["proposal_time"],
            "edit_kind": candidate.kind.value,
            "rng_bit_generator": "numpy.random.Philox",
            "rng_state_before_sha256": before,
            "rng_state_after_sha256": state_after,
            "route_draw_sha256": "0" * 64,
        }
        values["route_draw_sha256"] = _semantic_digest(_route_payload(values))
        result = OperationalReferenceRouteDraw(
            **values,
            _construction_token=_ROUTE_TOKEN,
        )
        self.validate_reference_route(result, waiting_draw, intensity, envelope)
        if intensity_sha != _intensity_sha256(intensity):
            raise ValueError("reference intensity changed before route return")
        if candidate_sha != _candidate_sha256(candidate):
            raise ValueError("candidate changed before route return")
        _record_unchanged(envelope, envelope_snapshot, context="rate envelope")
        _record_unchanged(waiting_draw, waiting_snapshot, context="waiting draw")
        self._require_live_binding()
        if _rng_state_sha256(checked_rng.bit_generator.state) != state_after:
            raise ValueError("Philox state changed before route return")
        return result

    def validate_reference_route(
        self,
        route_draw: OperationalReferenceRouteDraw,
        waiting_draw: OperationalWaitingTimeDraw,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
    ) -> OperationalReferenceRouteDraw:
        """Replay an admitted post-clock reference route without RNG."""

        if type(route_draw) is not OperationalReferenceRouteDraw:
            raise TypeError("route_draw has the wrong exact type")
        OperationalReferenceRouteDraw(
            **_snapshot_fields(route_draw, _route_fields()),
            _construction_token=_ROUTE_TOKEN,
        )
        if route_draw.certificate is not self.certificate:
            raise ValueError("route draw belongs to a different thinning owner")
        checked_waiting = self.validate_waiting_time(
            waiting_draw,
            intensity,
            envelope,
        )
        if not checked_waiting.candidate_due:
            raise ValueError("route draw has no admitted clock hit")
        if route_draw.waiting_draw_sha256 != checked_waiting.waiting_draw_sha256:
            raise ValueError("route draw belongs to a different waiting draw")
        if route_draw.rng_state_before_sha256 != (
            checked_waiting.rng_state_after_sha256
        ):
            raise ValueError("route draw does not continue the waiting stream")
        checked_intensity, checked_envelope = self._validate_parents(
            intensity,
            envelope,
        )
        if route_draw.intensity_sha256 != _intensity_sha256(checked_intensity):
            raise ValueError("route draw belongs to a different intensity")
        if route_draw.envelope_sha256 != checked_envelope.envelope_sha256:
            raise ValueError("route draw belongs to a different envelope")
        candidate = self._reference_composer.validate_candidate(route_draw.candidate)
        _require_candidate_intensity_binding(candidate, checked_intensity)
        if route_draw.candidate_sha256 != _candidate_sha256(candidate):
            raise ValueError("route draw candidate differs")
        if not _same_float(route_draw.proposal_time, checked_waiting.proposal_time):
            raise ValueError("route proposal time differs from waiting draw")
        self._require_live_binding()
        return route_draw

    def decide_acceptance(
        self,
        route_draw: OperationalReferenceRouteDraw,
        waiting_draw: OperationalWaitingTimeDraw,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
        potential_evaluation: TotalizedJumpPotentialCandidateEvaluation,
        rate_evaluation: TotalizedJumpRateCandidateEvaluation,
        *,
        rng: np.random.Generator,
    ) -> OperationalAcceptanceDecision:
        """Draw exact Bernoulli ``I64 / E64`` after full parent replay."""

        self._require_live_binding()
        checked_rng = _require_philox_rng(rng)
        checked_route = self.validate_reference_route(
            route_draw,
            waiting_draw,
            intensity,
            envelope,
        )
        candidate = checked_route.candidate
        checked_rate = self._rate_owner.validate_candidate_evaluation(
            rate_evaluation,
            candidate,
            potential_evaluation,
            envelope=envelope,
        )
        if checked_rate.envelope_sha256 != envelope.envelope_sha256:
            raise ValueError("candidate rate and acceptance envelope differ")
        if checked_rate.candidate_sha256 != checked_route.candidate_sha256:
            raise ValueError("candidate rate and route draw differ")
        if not _same_float(
            checked_rate.controlled_total_exit_upper_bound,
            envelope.controlled_total_exit_upper_bound,
        ):
            raise ValueError("candidate rate uses a different local envelope")
        before = _rng_state_sha256(checked_rng.bit_generator.state)
        if before != checked_route.rng_state_after_sha256:
            raise ValueError("acceptance RNG does not continue the route stream")
        ratio = _exact_acceptance_ratio(
            checked_rate.candidate_measure_integrand,
            envelope.controlled_total_exit_upper_bound,
        )
        intensity_sha = _intensity_sha256(intensity)
        candidate_sha = _candidate_sha256(candidate)
        route_snapshot = _snapshot_fields(checked_route, _route_fields())
        waiting_snapshot = _snapshot_fields(waiting_draw, _waiting_fields())
        envelope_snapshot = _snapshot_fields(envelope, _rate._envelope_fields())
        potential_snapshot = _snapshot_fields(
            potential_evaluation,
            tuple(TotalizedJumpPotentialCandidateEvaluation.__annotations__),
        )
        rate_snapshot = _snapshot_fields(
            checked_rate,
            _rate._candidate_evaluation_fields(),
        )
        session = _PhiloxRaw64Session(checked_rng)
        if session.state_before_sha256 != before:
            raise RuntimeError("acceptance Philox session started from another state")
        trace = _draw_exact_bernoulli(ratio, session)
        state_after = session.finish()

        self._rate_owner.validate_candidate_evaluation(
            rate_evaluation,
            candidate,
            potential_evaluation,
            envelope=envelope,
        )
        self.validate_reference_route(
            route_draw,
            waiting_draw,
            intensity,
            envelope,
        )
        self._require_live_binding()
        _record_unchanged(route_draw, route_snapshot, context="route draw")
        _record_unchanged(waiting_draw, waiting_snapshot, context="waiting draw")
        _record_unchanged(envelope, envelope_snapshot, context="rate envelope")
        _record_unchanged(rate_evaluation, rate_snapshot, context="rate evaluation")
        accepted = bool(trace["accepted"])
        result_configuration = (
            candidate.destination_configuration
            if accepted
            else candidate.source_configuration
        )
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "waiting_draw_sha256": waiting_draw.waiting_draw_sha256,
            "route_draw": checked_route,
            "route_draw_sha256": checked_route.route_draw_sha256,
            "envelope_sha256": envelope.envelope_sha256,
            "rate_evaluation_sha256": checked_rate.evaluation_sha256,
            "candidate_sha256": checked_route.candidate_sha256,
            "source_state_sha256": checked_route.source_state_sha256,
            "destination_state_sha256": checked_route.destination_state_sha256,
            "candidate_measure_integrand": checked_rate.candidate_measure_integrand,
            "controlled_total_exit_upper_bound": (
                envelope.controlled_total_exit_upper_bound
            ),
            "exact_acceptance_numerator": ratio.numerator,
            "exact_acceptance_denominator": ratio.denominator,
            **trace,
            "raw_words": tuple(session.words),
            "result_configuration": result_configuration,
            "result_state_sha256": _configuration_sha256(result_configuration),
            "envelope_reusable_after_decision": not accepted,
            "fresh_envelope_required": accepted,
            "rng_bit_generator": "numpy.random.Philox",
            "rng_state_before_sha256": before,
            "rng_state_after_sha256": state_after,
            "decision_sha256": "0" * 64,
        }
        values["decision_sha256"] = _semantic_digest(_decision_payload(values))
        result = OperationalAcceptanceDecision(
            **values,
            _construction_token=_DECISION_TOKEN,
        )
        self.validate_acceptance(
            result,
            route_draw,
            waiting_draw,
            intensity,
            envelope,
            potential_evaluation,
            rate_evaluation,
        )
        if intensity_sha != _intensity_sha256(intensity):
            raise ValueError("reference intensity changed before acceptance return")
        if candidate_sha != _candidate_sha256(candidate):
            raise ValueError("candidate changed before acceptance return")
        _record_unchanged(route_draw, route_snapshot, context="route draw")
        _record_unchanged(waiting_draw, waiting_snapshot, context="waiting draw")
        _record_unchanged(envelope, envelope_snapshot, context="rate envelope")
        _record_unchanged(
            potential_evaluation,
            potential_snapshot,
            context="potential evaluation",
        )
        _record_unchanged(rate_evaluation, rate_snapshot, context="rate evaluation")
        self._require_live_binding()
        if _rng_state_sha256(checked_rng.bit_generator.state) != state_after:
            raise ValueError("Philox state changed before acceptance return")
        return result

    def validate_acceptance(
        self,
        decision: OperationalAcceptanceDecision,
        route_draw: OperationalReferenceRouteDraw,
        waiting_draw: OperationalWaitingTimeDraw,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
        potential_evaluation: TotalizedJumpPotentialCandidateEvaluation,
        rate_evaluation: TotalizedJumpRateCandidateEvaluation,
    ) -> OperationalAcceptanceDecision:
        """Replay a local acceptance record without consuming randomness."""

        if type(decision) is not OperationalAcceptanceDecision:
            raise TypeError("decision has the wrong exact type")
        OperationalAcceptanceDecision(
            **_snapshot_fields(decision, _decision_fields()),
            _construction_token=_DECISION_TOKEN,
        )
        if decision.certificate is not self.certificate:
            raise ValueError("decision belongs to a different thinning owner")
        checked_route = self.validate_reference_route(
            route_draw,
            waiting_draw,
            intensity,
            envelope,
        )
        if decision.route_draw is not checked_route:
            raise ValueError("decision belongs to a different route record")
        checked_rate = self._rate_owner.validate_candidate_evaluation(
            rate_evaluation,
            checked_route.candidate,
            potential_evaluation,
            envelope=envelope,
        )
        expected = {
            "waiting_draw_sha256": waiting_draw.waiting_draw_sha256,
            "route_draw_sha256": checked_route.route_draw_sha256,
            "envelope_sha256": envelope.envelope_sha256,
            "rate_evaluation_sha256": checked_rate.evaluation_sha256,
            "candidate_sha256": checked_route.candidate_sha256,
            "candidate_measure_integrand": checked_rate.candidate_measure_integrand,
            "controlled_total_exit_upper_bound": (
                envelope.controlled_total_exit_upper_bound
            ),
            "rng_state_before_sha256": checked_route.rng_state_after_sha256,
        }
        for name, value in expected.items():
            supplied = getattr(decision, name)
            if type(value) is float:
                if not _same_float(supplied, value):
                    raise ValueError("decision %s differs from parent" % name)
            elif supplied != value:
                raise ValueError("decision %s differs from parent" % name)
        self._require_live_binding()
        return decision


def certify_plugin_bridge_operational_thinning(
    rate_owner: TotalizedConfigurationJumpRateEnvelope,
    *,
    thinning_policy: object,
    thinning_role_sha256: object,
) -> OperationalJumpThinning:
    """Certify the local waiting/route/acceptance layer for checkpoint eighteen."""

    if type(thinning_policy) is not str:
        raise TypeError("thinning_policy must be exact text")
    if thinning_policy != PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY:
        raise ValueError("only the exported operational thinning policy is supported")
    role = _require_sha256(thinning_role_sha256, name="thinning_role_sha256")
    if type(rate_owner) is not TotalizedConfigurationJumpRateEnvelope:
        raise TypeError("rate_owner has the wrong exact type")
    rate_certificate = rate_owner._require_live_binding()
    reference_composer = rate_owner.reference_composer
    certificate = _make_certificate(
        rate_certificate,
        thinning_role_sha256=role,
    )
    owner = OperationalJumpThinning(
        rate_owner,
        reference_composer,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_operational_thinning(
    rate_owner: TotalizedConfigurationJumpRateEnvelope,
    owner: OperationalJumpThinning,
    *,
    thinning_policy: object,
    thinning_role_sha256: object,
) -> OperationalJumpThinning:
    """Require exact owner identity and reconstructed transitive custody."""

    if type(thinning_policy) is not str:
        raise TypeError("thinning_policy must be exact text")
    if thinning_policy != PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY:
        raise ValueError("only the exported operational thinning policy is supported")
    role = _require_sha256(thinning_role_sha256, name="thinning_role_sha256")
    if type(owner) is not OperationalJumpThinning:
        raise TypeError("owner must be an exact OperationalJumpThinning")
    if owner.rate_owner is not rate_owner:
        raise ValueError("thinning owner is bound to a different rate owner")
    if owner.certificate.thinning_role_sha256 != role:
        raise ValueError("thinning owner is bound to a different role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_operational_thinning_certificate(
    rate_owner: TotalizedConfigurationJumpRateEnvelope,
    owner: OperationalJumpThinning,
    *,
    thinning_policy: object,
    thinning_role_sha256: object,
) -> OperationalThinningCertificate:
    """Return the reconstructed live checkpoint-nineteen certificate."""

    return require_matching_plugin_bridge_operational_thinning(
        rate_owner,
        owner,
        thinning_policy=thinning_policy,
        thinning_role_sha256=thinning_role_sha256,
    ).certificate


__all__ = [
    "OPERATIONAL_THINNING_DECIMAL_AUDIT_PRECISION",
    "OPERATIONAL_THINNING_DECIMAL_MAX_PRECISION",
    "OPERATIONAL_THINNING_DECIMAL_PRIMARY_PRECISION",
    "OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS",
    "OPERATIONAL_THINNING_MAX_RATIO_BITS",
    "OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS",
    "OPERATIONAL_THINNING_RAW_WORD_BITS",
    "PLUGIN_BRIDGE_OPERATIONAL_ACCEPTANCE_POLICY",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_SCOPE",
    "PLUGIN_BRIDGE_OPERATIONAL_WAITING_POLICY",
    "OperationalAcceptanceDecision",
    "OperationalJumpThinning",
    "OperationalReferenceRouteDraw",
    "OperationalThinningCertificate",
    "OperationalWaitingTimeDraw",
    "PluginBridgeOperationalThinningError",
    "certify_plugin_bridge_operational_thinning",
    "require_matching_plugin_bridge_operational_thinning",
    "validate_plugin_bridge_operational_thinning_certificate",
]
