"""Precommitted initial-tilt kernels over a mixed-support reference interface.

For a fixed certified :class:`ConfigurationInitialTiltComposer`, context
``c``, and exact represented score

``q_repr(x) = exact_initial_log_factor_numerator /
              exact_initial_log_factor_denominator``,

the score is defined only on canonical binary64-represented configurations.
Let ``P_ref^op`` denote the otherwise unspecified finite-precision law induced
by the frozen process-owned reference-sampling interface under an external
probabilistic model for its operational backend.  The representation-level
target is

``rho_repr(dx) = exp(q_repr(x)) P_ref^op(dx) / Z_repr``.

This module binds the process-owned analytic ``Pi_N`` object and uses its
sampling interface, but it does not certify that NumPy/Philox outputs have the
analytic ``Pi_N`` law or any particular ``P_ref^op`` law.  Binary64 points are
a null subset of a positive-dimensional analytic Gaussian fiber, so
``q_repr`` alone cannot define a density with respect to analytic ``Pi_N``.
No finite coordinate codebook, CP28 proposal, or CP49 source-law assumption
occurs here.  A sealed plan chooses exactly one strategy before execution:

* ``finite-atomic-enumeration`` visits the complete oracle support, and is
  available only when every declared fiber has dimension zero;
* ``bounded-rejection`` makes exactly ``A`` representation-support-faithful
  calls to the process-owned reference sampler and exactly ``A``
  role-separated decision draws, scores every returned configuration, and
  applies the conservative uint64 quota ``floor(2**64 exp(q_repr-U))``;
* ``fixed-budget-sir`` makes exactly ``J`` such interface calls and one
  operational categorical draw from a separately derived, ``J``-bound Philox
  stream.

There is a separate generic ideal theorem: if an external proof supplies the
analytic proposal law ``Pi_N`` and a measurable bounded real-fiber extension
``qbar`` of ``q_repr``, ideal rejection conditional on success targets
``exp(qbar) Pi_N / Z_qbar``.  Those antecedents are not established here.  The
implemented uint64 rule is not that exact Bernoulli kernel: each attempt has a
strict probability deficit below ``2**-64`` under an *abstract* uniform-word
premise.  Finite-``J`` SIR also has only its generic self-normalized law and
convergence theorem under externally supplied IID proposal antecedents.

Returned seeded executions therefore are interface traces, not certified
samples from an exact live law.  Equality to an analytic conditional density
``h``, model adequacy, continuous empirical TV/KL, sequence independence,
path/sampler admission, generalization, and Formal Test 28 closure remain
unproved.  Certificate hashes and object identities are local custody records
under a trusted unchanged runtime, not code authentication or portable
reproducibility identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
import decimal
from decimal import Context, Decimal, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import json
import math
import platform
import struct
from typing import Mapping, Optional, Tuple, Union

import numpy as np

try:
    from heterodiff.models import configuration_initial_tilt_composer_torch as _tilt
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "mixed-support initial-tilt kernels require the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.theory.association_preconditioner import _plain_key_sha256
from heterodiff.theory import configuration_reference as _reference
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedConfiguration,
    TransformedEvent,
)


MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCHEMA_VERSION = (
    "mixed-support-initial-tilt-initializer-kernel-v1"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_TARGET_POLICY = (
    "representation-level-rho_repr(dx)=exp(q_repr(x))*P_ref^op(dx)/Z_repr;"
    "q_repr=exact-rational-score-on-canonical-binary64-configurations;"
    "P_ref^op=unspecified-finite-precision-law-induced-by-frozen-process-owned-"
    "reference-sampling-interface-under-external-backend-law;"
    "no-exact-live-proposal-or-target-law-certified-v1"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_STRATEGIES = (
    "finite-atomic-enumeration",
    "bounded-rejection",
    "fixed-budget-sir",
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCOPE = (
    "one-exact-configuration-initial-tilt-composer-certificate;"
    "one-fixed-residual-context;one-process-owned-capped-poisson-Pi_N-object-"
    "and-reference-sampling-interface-custody-only;"
    "one-preselected-enumeration-rejection-or-SIR-plan;"
    "exact-rational-point-score-q;global-certified-bounds-L-U;"
    "finite-atomic-complete-support-or-representation-support-faithful-"
    "reference-interface-returns;bounded-preflighted-operational-work;"
    "explicit-rejection-exhaustion;"
    "structural-nonreplaying-result-validation;trusted-runtime;"
    "not-analytic-Pi_N-live-proposal-law-or-real-fiber-q-extension;"
    "not-analytic-h-equality-or-exact-posterior;"
    "not-live-Philox-law-independence-IID-or-random-oracle;"
    "not-finite-J-SIR-exactness-or-exact-operational-rejection-Bernoulli;"
    "not-continuous-empirical-TV-KL;not-path-or-sampler-admission;"
    "not-model-quality-generality-or-Formal-Test-28-closure"
)
MIXED_SUPPORT_INITIAL_TILT_IDEAL_REJECTION_THEOREM = (
    "generic-external-analytic-theorem-only;if-an-external-proof-supplies-"
    "Y_i-iid-analytic-Pi_N-independent-V_i-iid-Unif[0,1]-and-a-measurable-"
    "real-fiber-extension-qbar-of-q_repr-with-L<=qbar<=U;accept-i-iff-"
    "V_i<=exp(qbar(Y_i)-U);the-first-accepted-Y-conditional-on-at-least-one-"
    "acceptance-has-rho_qbar(dx)=exp(qbar(x))*Pi_N(dx)/Z_qbar;"
    "P(exhausted)=(1-Z_qbar/exp(U))^A;none-of-these-live-law-or-extension-"
    "antecedents-is-certified-here"
)
MIXED_SUPPORT_INITIAL_TILT_DYADIC_REJECTION_CAVEAT = (
    "implemented-K=floor(2^64*exp(q_repr-U));under-an-abstract-independent-"
    "uniform-uint64-word-premise-acceptance-is-K/2^64;"
    "0<=exp(q_repr-U)-K/2^64<2^-64;"
    "under-a-coupling-that-holds-the-identical-represented-proposal-and-score-"
    "batch-fixed-and-couples-each-dyadic-word-to-an-independent-ideal-uniform-"
    "the-finite-budget-augmented-outcome-discrepancy-is-less-than-A/2^64;"
    "this-bound-excludes-reference-sampler-law-PRNG-independence-score-law-and-"
    "real-fiber-extension-error;the-live-Philox-premise-is-not-verified"
)
MIXED_SUPPORT_INITIAL_TILT_SIR_THEOREM = (
    "generic-external-theorem-only;for-Y_1:J-iid-from-a-specified-proposal-P-"
    "and-a-specified-measurable-bounded-score-qbar-with-w_j=exp(qbar(Y_j));"
    "Q_J(B)=E[sum_j(w_j*1{Y_j-in-B})/sum_l(w_l)];"
    "finite-J-Q_J-need-not-equal-rho_qbar;global-finite-L-U-give-bounded-"
    "strictly-positive-weights-and-Q_J-converges-to-rho_qbar-proportional-to-"
    "exp(qbar)*P-in-TV-as-J-to-infinity;the-required-live-proposal-Philox-"
    "independence-and-float64-categorical-laws-are-not-certified"
)
MIXED_SUPPORT_INITIAL_TILT_ANALYTIC_BRIDGE = (
    "if-a-separate-proof-establishes-a-measurable-real-fiber-qbar-and-"
    "Delta=qbar-log(h)-and-omega=esssup(Delta)-essinf(Delta);then-"
    "TV(rho_qbar,rho_h)<=tanh(omega/4)-"
    "and-both-directed-KL-values-are-at-most-omega;"
    "this-module-does-not-establish-h-or-omega"
)
MIXED_SUPPORT_INITIAL_TILT_METRIC_BOUNDARY = (
    "exact-or-float64-discrete-mass-metrics-are-permitted-on-finite-atomic-"
    "support;for-positive-dimensional-strata-use-weak-sample-metrics-such-as-"
    "MMD-energy-or-sliced-Wasserstein-with-uncertainty;empirical-TV-or-KL-"
    "between-finite-samples-and-an-atomless-target-is-not-valid"
)
MIXED_SUPPORT_INITIAL_TILT_FORMAL_TEST_28_STATUS = "OPEN"
MIXED_SUPPORT_INITIAL_TILT_REFERENCE_OBJECT_CUSTODY_SCOPE = (
    "process_owned_reference_object_bound-means-exact-composer-owned-"
    "reference-object-identity-custody-only;it-does-not-certify-the-analytic-"
    "Pi_N-law-an-operational-proposal-law-or-correspondence-between-them"
)
MIXED_SUPPORT_INITIAL_TILT_RESOURCE_PREFLIGHT_POLICY = (
    "stochastic-before-any-execution-stream-construction-require-"
    "budget*total_cap<=MAX_REFERENCE_BATCH_OCCURRENCES-and-budget*total_cap*"
    "max_type_dimension<=MAX_REFERENCE_BATCH_COORDINATES;retain-reference-"
    "per-configuration-sampling-gates;finite-atomic-enumeration-requires-"
    "successful-finite_atomic_oracle-construction-v1"
)

MAX_MIXED_SUPPORT_INITIALIZER_BUDGET = 4_096
MIXED_SUPPORT_INITIALIZER_RAW_WORD_BITS = 64
MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS = 53
MIXED_SUPPORT_INITIALIZER_DEFAULT_ESS_WARNING_FRACTION = 0.25

_SCHEMA_VERSION = MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCHEMA_VERSION
_TARGET_POLICY = MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_TARGET_POLICY
_STRATEGIES = MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_STRATEGIES
_SCOPE = MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCOPE
_UINT64_DENOMINATOR = 1 << MIXED_SUPPORT_INITIALIZER_RAW_WORD_BITS
_MAX_RUNTIME_IDENTITY = (1 << 64) - 1
_MAX_REPRESENTED_SCORE_INTEGER_BITS = 16_384
_ZERO_SHA256 = "0" * 64

_PLAN_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_SCORED_TOKEN = object()
_ATTEMPT_TOKEN = object()
_PARTICLE_TOKEN = object()
_ATOM_TOKEN = object()
_REJECTION_RESULT_TOKEN = object()
_SIR_RESULT_TOKEN = object()
_ENUMERATION_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

_COMPOSER_TYPE = _tilt.ConfigurationInitialTiltComposer
_COMPOSER_CERTIFICATE_TYPE = _tilt.InitialTiltCompositionCertificate
_EVALUATION_TYPE = _tilt.InitialTiltPointEvaluation
_COMPOSER_VALIDATE_CERTIFICATE = _tilt._validate_certificate
_EVALUATION_FIELDS = _tilt._evaluation_fields
_EVALUATION_TOKEN = _tilt._EVALUATION_TOKEN
_COMPOSER_OWNER_SNAPSHOT = _COMPOSER_TYPE._owner_snapshot
_COMPOSER_LIVE_COMPONENTS = _COMPOSER_TYPE._live_components
_COMPOSER_EVALUATE = _COMPOSER_TYPE.evaluate
_CONFIGURATION_SHA256 = _tilt._configuration_sha256
_CONTEXT_SHA256 = _tilt._context_sha256
_VALIDATED_CONTEXT = _tilt._validated_context
_RESOLUTION_SAFE_CDF = _reference._resolution_safe_cdf

_DECIMAL_MIN_EXPONENT = -999_999
_DECIMAL_MAX_EXPONENT = 999_999
_QUOTA_PRIMARY_PRECISION = 192
_QUOTA_MAX_PRECISION = 3_072
_QUOTA_MAX_DECIMAL_DIGITS = 16_384
_QUOTA_MAX_EXACT_INTEGER_BITS = 16_384


class MixedSupportInitialTiltInitializerError(ArithmeticError):
    """Raised when a precommitted initializer operation must fail closed."""


@dataclass(frozen=True)
class MixedSupportInitialTiltRejectionQuota:
    """Certified conservative uint64 quota for one exact dyadic log gap."""

    branch: str
    precision: int
    ideal_lower: Fraction
    ideal_upper: Fraction
    ideal_upper_strict: bool
    quota: int


def _quota_decimal_context(precision: int) -> Context:
    if type(precision) is not int or not 1 <= precision <= 10_000:
        raise ValueError("decimal precision is outside the implementation limit")
    return Context(
        prec=precision,
        rounding=ROUND_HALF_EVEN,
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


def _quota_precision_schedule() -> Tuple[int, ...]:
    values = []
    precision = _QUOTA_PRIMARY_PRECISION
    while precision < _QUOTA_MAX_PRECISION:
        values.append(precision)
        precision *= 2
    values.append(_QUOTA_MAX_PRECISION)
    return tuple(values)


def _integer_decimal_digits(value: int, *, name: str) -> Tuple[int, ...]:
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise TypeError("%s coefficient must be a nonnegative exact integer" % name)
    if value == 0:
        return (0,)
    blocks = []
    remaining = value
    while remaining:
        remaining, block = divmod(remaining, 1_000_000_000)
        blocks.append(block)
    blocks.reverse()
    first_digits = tuple(int(character) for character in str(blocks[0]))
    digit_count = len(first_digits) + 9 * (len(blocks) - 1)
    if digit_count > _QUOTA_MAX_DECIMAL_DIGITS:
        raise MixedSupportInitialTiltInitializerError(
            "%s exact decimal coefficient exceeds the work limit" % name
        )
    digits = list(first_digits)
    for block in blocks[1:]:
        digits.extend(int(character) for character in "%09d" % block)
    return tuple(digits)


def _exact_dyadic_decimal(value: Fraction, *, name: str) -> Decimal:
    if type(value) is not Fraction:
        raise TypeError("%s must be an exact Fraction" % name)
    denominator = value.denominator
    if (
        value.numerator.bit_length() > _QUOTA_MAX_EXACT_INTEGER_BITS
        or denominator.bit_length() > _QUOTA_MAX_EXACT_INTEGER_BITS
    ):
        raise MixedSupportInitialTiltInitializerError(
            "%s exceeds the exact-dyadic work limit" % name
        )
    if denominator <= 0 or denominator & (denominator - 1):
        raise MixedSupportInitialTiltInitializerError(
            "%s denominator is not a power of two" % name
        )
    if value == 0:
        return Decimal(0)
    exponent = denominator.bit_length() - 1
    coefficient = value.numerator * (5**exponent)
    return Decimal(
        (
            1 if coefficient < 0 else 0,
            _integer_decimal_digits(abs(coefficient), name=name),
            -exponent,
        )
    )


def certify_mixed_support_rejection_quota(
    delta: Fraction,
) -> MixedSupportInitialTiltRejectionQuota:
    """Return ``floor(2**64 exp(delta))`` with an enclosing Decimal proof.

    ``delta`` must be an exact nonpositive dyadic rational.  This pure helper
    is independently testable and consumes neither a composer nor randomness.
    """

    if type(delta) is not Fraction:
        raise TypeError("delta must be an exact Fraction")
    if (
        delta.numerator.bit_length() > _QUOTA_MAX_EXACT_INTEGER_BITS
        or delta.denominator.bit_length() > _QUOTA_MAX_EXACT_INTEGER_BITS
    ):
        raise MixedSupportInitialTiltInitializerError(
            "delta exceeds the exact-dyadic work limit"
        )
    if delta.denominator & (delta.denominator - 1):
        raise MixedSupportInitialTiltInitializerError(
            "delta must be an exact dyadic rational"
        )
    if delta > 0:
        raise ValueError("delta must be nonpositive")
    if delta == 0:
        return MixedSupportInitialTiltRejectionQuota(
            "unity",
            0,
            Fraction(1),
            Fraction(1),
            False,
            _UINT64_DENOMINATOR,
        )
    if delta <= -64:
        return MixedSupportInitialTiltRejectionQuota(
            "below_uint64_resolution",
            0,
            Fraction(0),
            Fraction(1, _UINT64_DENOMINATOR),
            True,
            0,
        )
    if delta > Fraction(-1, _UINT64_DENOMINATOR):
        return MixedSupportInitialTiltRejectionQuota(
            "below_one_uint64_cell",
            0,
            Fraction(_UINT64_DENOMINATOR - 1, _UINT64_DENOMINATOR),
            Fraction(1),
            True,
            _UINT64_DENOMINATOR - 1,
        )

    exact_decimal = _exact_dyadic_decimal(delta, name="rejection log gap")
    previous: Optional[Tuple[Fraction, Fraction]] = None
    for precision in _quota_precision_schedule():
        context = _quota_decimal_context(precision)
        try:
            rounded = context.exp(exact_decimal)
            lower_decimal = context.next_minus(rounded)
            upper_decimal = context.next_plus(rounded)
        except decimal.DecimalException as error:
            raise MixedSupportInitialTiltInitializerError(
                "Decimal exponential could not be enclosed"
            ) from error
        if upper_decimal >= Decimal(1):
            upper_decimal = Decimal(1)
        if (
            not rounded.is_finite()
            or not lower_decimal.is_finite()
            or not upper_decimal.is_finite()
            or not Decimal(0) < lower_decimal <= rounded <= upper_decimal <= Decimal(1)
        ):
            raise MixedSupportInitialTiltInitializerError(
                "Decimal exponential enclosure is invalid"
            )
        lower = Fraction(lower_decimal)
        upper = Fraction(upper_decimal)
        if previous is not None and not (previous[0] <= lower <= upper <= previous[1]):
            raise MixedSupportInitialTiltInitializerError(
                "adaptive Decimal exponential enclosures are not nested"
            )
        previous = (lower, upper)
        scaled_lower = _UINT64_DENOMINATOR * lower
        scaled_upper = _UINT64_DENOMINATOR * upper
        quota = scaled_lower.numerator // scaled_lower.denominator
        if quota <= scaled_lower and scaled_upper <= quota + 1:
            if not 0 <= quota < _UINT64_DENOMINATOR:
                raise MixedSupportInitialTiltInitializerError(
                    "certified quota escaped the uint64 domain"
                )
            return MixedSupportInitialTiltRejectionQuota(
                "adaptive_decimal",
                precision,
                lower,
                upper,
                True,
                quota,
            )
    raise MixedSupportInitialTiltInitializerError(
        "finite-resolution rejection quota is precision-ambiguous"
    )


def _same_float(left: object, right: object) -> bool:
    return (
        type(left) is float
        and type(right) is float
        and struct.pack(">d", left) == struct.pack(">d", right)
    )


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be lowercase SHA-256 text" % name)
    return value


def _require_runtime_identity(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if not 1 <= value <= _MAX_RUNTIME_IDENTITY:
        raise ValueError("%s is outside the unsigned 64-bit range" % name)
    return value


def _require_integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s must lie in [%d, %d]" % (name, minimum, maximum))
    return value


def _validated_fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    if type(numerator) is not int or isinstance(numerator, bool):
        raise TypeError("%s numerator must be an exact integer" % name)
    if type(denominator) is not int or isinstance(denominator, bool):
        raise TypeError("%s denominator must be an exact integer" % name)
    if denominator <= 0:
        raise ValueError("%s denominator must be positive" % name)
    if (
        numerator.bit_length() > _MAX_REPRESENTED_SCORE_INTEGER_BITS
        or denominator.bit_length() > _MAX_REPRESENTED_SCORE_INTEGER_BITS
    ):
        raise ValueError("%s exceeds the exact-integer resource limit" % name)
    value = Fraction(numerator, denominator)
    if value.numerator != numerator or value.denominator != denominator:
        raise ValueError("%s must be stored in reduced form" % name)
    return value


def _require_finite_float(value: object, *, name: str) -> float:
    if type(value) is not float:
        raise TypeError("%s must be an exact float" % name)
    if not math.isfinite(value):
        raise ValueError("%s must be finite" % name)
    return value


def _typed_digest_value(value: object) -> object:
    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-decimal-v1", str(value)]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("digest floats must be finite")
        return ["float64-hex-v1", value.hex()]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is tuple:
        return ["tuple-v1", [_typed_digest_value(item) for item in value]]
    raise TypeError("unsupported semantic-digest value %s" % type(value).__name__)


def _semantic_digest(payload: Mapping[str, object], *, domain: bytes) -> str:
    if type(payload) is not dict:
        payload = dict(payload)
    encoded = json.dumps(
        {name: _typed_digest_value(payload[name]) for name in sorted(payload)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(encoded)
    return digest.hexdigest()


def _immutable_float_array(value: object, *, name: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as error:
        raise TypeError("%s must be a float64-compatible array" % name) from error
    if array.ndim != 1:
        raise ValueError("%s must be one-dimensional" % name)
    if np.any(~np.isfinite(array)):
        raise ValueError("%s must contain only finite entries" % name)
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64)


def _same_float_array(left: object, right: object) -> bool:
    return (
        type(left) is np.ndarray
        and type(right) is np.ndarray
        and left.dtype == np.dtype(np.float64)
        and right.dtype == np.dtype(np.float64)
        and left.shape == right.shape
        and left.tobytes(order="C") == right.tobytes(order="C")
    )


def _exact_log_weight_tuple(
    exact_log_weights: object,
    *,
    name: str,
) -> Tuple[Fraction, ...]:
    if type(exact_log_weights) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if not 1 <= len(exact_log_weights) <= MAX_MIXED_SUPPORT_INITIALIZER_BUDGET:
        raise ValueError("%s has an unsupported length" % name)
    checked = []
    for value in exact_log_weights:
        if type(value) is not Fraction:
            raise TypeError("%s entries must be exact Fraction values" % name)
        rounded = float(value)
        if not math.isfinite(rounded):
            raise ArithmeticError("%s contains a nonrepresentable value" % name)
        checked.append(value)
    return tuple(checked)


def normalize_mixed_support_sir_exact_log_weights(
    exact_log_weights: Tuple[Fraction, ...],
) -> np.ndarray:
    """Stably normalize exact SIR log weights into immutable float64 values."""

    checked = _exact_log_weight_tuple(
        exact_log_weights,
        name="exact_log_weights",
    )
    logs = np.asarray([float(value) for value in checked], dtype=np.float64)
    maximum = float(np.max(logs))
    shifted = np.exp(logs - maximum)
    if np.any(~np.isfinite(shifted)) or np.any(shifted <= 0.0):
        raise MixedSupportInitialTiltInitializerError(
            "positive SIR weights underflowed or became nonfinite"
        )
    normalizer = math.fsum(float(value) for value in shifted)
    if not math.isfinite(normalizer) or normalizer <= 0.0:
        raise MixedSupportInitialTiltInitializerError("SIR weight normalization failed")
    probabilities = shifted / normalizer
    if np.any(~np.isfinite(probabilities)) or np.any(probabilities <= 0.0):
        raise MixedSupportInitialTiltInitializerError(
            "normalized SIR weights are not strictly positive finite values"
        )
    return _immutable_float_array(probabilities, name="normalized SIR weights")


def select_mixed_support_sir_index(
    normalized_weights: object,
    raw_word: int,
) -> int:
    """Apply the frozen resolution-gated 53-bit categorical transform."""

    weights = _immutable_float_array(normalized_weights, name="normalized_weights")
    if not 1 <= len(weights) <= MAX_MIXED_SUPPORT_INITIALIZER_BUDGET:
        raise ValueError("normalized_weights has an unsupported length")
    if np.any(weights <= 0.0):
        raise ValueError("normalized_weights must be strictly positive")
    if abs(math.fsum(float(value) for value in weights) - 1.0) > (
        32.0 * len(weights) * np.finfo(np.float64).eps
    ):
        raise ValueError("normalized_weights must sum to one")
    word = _require_integer(
        raw_word,
        name="raw_word",
        minimum=0,
        maximum=_UINT64_DENOMINATOR - 1,
    )
    cdf = _RESOLUTION_SAFE_CDF(weights)
    if cdf is None:
        raise MixedSupportInitialTiltInitializerError(
            "categorical weights fail the frozen float64 resolution gate"
        )
    uniform53 = word >> (
        MIXED_SUPPORT_INITIALIZER_RAW_WORD_BITS
        - MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS
    )
    uniform = uniform53 * (2.0**-MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS)
    selected = int(np.searchsorted(cdf, uniform, side="right"))
    if not 0 <= selected < len(weights):
        raise MixedSupportInitialTiltInitializerError(
            "categorical transform escaped the weight range"
        )
    return selected


def normalize_mixed_support_atomic_exact_log_weights(
    base_masses: object,
    exact_log_weights: Tuple[Fraction, ...],
) -> Tuple[np.ndarray, float]:
    """Normalize a finite atomic base PMF times exact exponential tilts."""

    checked_q = _exact_log_weight_tuple(
        exact_log_weights,
        name="exact_log_weights",
    )
    masses = _immutable_float_array(base_masses, name="base_masses")
    if len(masses) != len(checked_q):
        raise ValueError("base_masses and exact_log_weights lengths differ")
    if np.any(masses <= 0.0):
        raise ValueError("base_masses must be strictly positive")
    if abs(math.fsum(float(value) for value in masses) - 1.0) > (
        32.0 * len(masses) * np.finfo(np.float64).eps
    ):
        raise ValueError("base_masses must sum to one")
    logs = np.asarray(
        [
            math.log(float(masses[index])) + float(q)
            for index, q in enumerate(checked_q)
        ],
        dtype=np.float64,
    )
    if np.any(~np.isfinite(logs)):
        raise MixedSupportInitialTiltInitializerError(
            "finite-atomic log target contains a nonfinite value"
        )
    maximum = float(np.max(logs))
    shifted = np.exp(logs - maximum)
    if np.any(~np.isfinite(shifted)) or np.any(shifted <= 0.0):
        raise MixedSupportInitialTiltInitializerError(
            "a positive finite-atomic target mass underflowed"
        )
    shifted_sum = math.fsum(float(value) for value in shifted)
    if not math.isfinite(shifted_sum) or shifted_sum <= 0.0:
        raise MixedSupportInitialTiltInitializerError(
            "finite-atomic target normalization failed"
        )
    probabilities = _immutable_float_array(
        shifted / shifted_sum,
        name="finite-atomic target probabilities",
    )
    if np.any(probabilities <= 0.0):
        raise MixedSupportInitialTiltInitializerError(
            "normalization erased a positive finite-atomic support mass"
        )
    if abs(math.fsum(float(value) for value in probabilities) - 1.0) > (
        32.0 * len(probabilities) * np.finfo(np.float64).eps
    ):
        raise MixedSupportInitialTiltInitializerError(
            "finite-atomic target probabilities do not sum to one"
        )
    return probabilities, maximum + math.log(shifted_sum)


def _fraction_from_evaluation(evaluation: _EVALUATION_TYPE) -> Fraction:
    return _validated_fraction_parts(
        evaluation.exact_initial_log_factor_numerator,
        evaluation.exact_initial_log_factor_denominator,
        name="evaluation exact represented score",
    )


def _structural_evaluation(
    evaluation: object,
    *,
    composer_certificate: _COMPOSER_CERTIFICATE_TYPE,
    residual_context: Tuple[float, ...],
    configuration: TransformedConfiguration,
) -> _EVALUATION_TYPE:
    if type(evaluation) is not _EVALUATION_TYPE:
        raise TypeError("evaluation must be an exact InitialTiltPointEvaluation")
    _EVALUATION_TYPE(
        **{name: getattr(evaluation, name) for name in _EVALUATION_FIELDS()},
        _construction_token=_EVALUATION_TOKEN,
    )
    if evaluation.certificate is not composer_certificate:
        raise ValueError("evaluation belongs to a different composer certificate")
    if evaluation.residual_context != residual_context:
        raise ValueError("evaluation has a different residual context")
    if evaluation.configuration != configuration:
        raise ValueError("evaluation has a different configuration")
    if evaluation.residual_context_sha256 != _CONTEXT_SHA256(residual_context):
        raise ValueError("evaluation residual-context digest differs")
    if evaluation.configuration_sha256 != _CONFIGURATION_SHA256(configuration):
        raise ValueError("evaluation configuration digest differs")
    return evaluation


def _rng_state_sha256(state: object) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-mixed-support-initializer-philox-state-v1\x00")
    nodes = [0]

    def update(value: object, depth: int) -> None:
        nodes[0] += 1
        if nodes[0] > 4_096 or depth > 16:
            raise ValueError("Philox state exceeds the digest resource limit")
        if value is None:
            digest.update(b"N")
        elif type(value) is bool:
            digest.update(b"B1" if value else b"B0")
        elif isinstance(value, np.integer) or type(value) is int:
            integer = int(value)
            digest.update(b"I")
            encoded = abs(integer).to_bytes(
                max(1, (abs(integer).bit_length() + 7) // 8),
                "big",
                signed=False,
            )
            digest.update(b"-" if integer < 0 else b"+")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
        elif type(value) is str:
            encoded = value.encode("utf-8")
            digest.update(b"S")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
        elif type(value) is dict:
            digest.update(b"D")
            for key in sorted(value):
                if type(key) is not str:
                    raise TypeError("Philox state mappings require text keys")
                update(key, depth + 1)
                update(value[key], depth + 1)
            digest.update(b"d")
        elif type(value) is tuple:
            digest.update(b"T")
            for item in value:
                update(item, depth + 1)
            digest.update(b"t")
        elif type(value) is np.ndarray:
            if value.nbytes > 16_384 or value.dtype.hasobject:
                raise ValueError("Philox state array is unsupported")
            digest.update(b"A")
            update(value.dtype.str, depth + 1)
            update(tuple(int(item) for item in value.shape), depth + 1)
            raw = value.tobytes(order="C")
            digest.update(len(raw).to_bytes(8, "big"))
            digest.update(raw)
        else:
            raise TypeError("unsupported Philox state value %s" % type(value).__name__)

    update(state, 0)
    return digest.hexdigest()


def _new_philox(seed: int) -> np.random.Generator:
    checked = _require_integer(
        seed,
        name="Philox seed",
        minimum=0,
        maximum=(1 << 64) - 1,
    )
    rng = np.random.Generator(np.random.Philox(checked))
    if type(rng.bit_generator) is not np.random.Philox:
        raise RuntimeError("NumPy did not construct the exact Philox bit generator")
    _rng_state_sha256(rng.bit_generator.state)
    return rng


def _derive_stream_seed(
    seed: int,
    stream_role: str,
    role_sha256: str,
    context_sha256: str,
    *,
    strategy: str,
    sir_particle_budget: Optional[int] = None,
) -> int:
    if type(strategy) is not str or strategy not in (
        "bounded-rejection",
        "fixed-budget-sir",
    ):
        raise ValueError("initializer stochastic strategy is unknown")
    if stream_role not in ("proposal", "rejection-decision", "sir-resampling"):
        raise ValueError("initializer stream role is unknown")
    if stream_role == "rejection-decision" and strategy != "bounded-rejection":
        raise ValueError("the rejection-decision stream requires bounded-rejection")
    if stream_role == "sir-resampling" and strategy != "fixed-budget-sir":
        raise ValueError("the sir-resampling stream requires fixed-budget-sir")
    if stream_role == "sir-resampling":
        bound_budget = _require_integer(
            sir_particle_budget,
            name="SIR resampling particle-budget binding",
            minimum=1,
            maximum=MAX_MIXED_SUPPORT_INITIALIZER_BUDGET,
        )
    else:
        if sir_particle_budget is not None:
            raise ValueError(
                "only the SIR resampling stream may bind a particle budget"
            )
        bound_budget = None
    digest = hashlib.sha256()
    digest.update(b"heterodiff-mixed-support-initializer-derived-stream-v1\x00")
    digest.update(strategy.encode("ascii"))
    digest.update(b"\x00")
    digest.update(stream_role.encode("ascii"))
    digest.update(b"\x00")
    digest.update(seed.to_bytes(8, "big", signed=False))
    digest.update(bytes.fromhex(role_sha256))
    digest.update(bytes.fromhex(context_sha256))
    if bound_budget is None:
        digest.update(b"no-particle-budget\x00")
    else:
        digest.update(b"sir-particle-budget\x00")
        digest.update(bound_budget.to_bytes(8, "big", signed=False))
    result = int.from_bytes(digest.digest()[:8], "big", signed=False)
    if result == seed:
        result ^= 1 << 63
    return result


def _planned_stream_seeds(
    plan: MixedSupportInitialTiltInitializerPlan,
) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    if plan.strategy == "finite-atomic-enumeration":
        return None, None, None
    proposal = _derive_stream_seed(
        plan.seed,
        "proposal",
        plan.initializer_role_sha256,
        plan.residual_context_sha256,
        strategy=plan.strategy,
    )
    used = {plan.seed, proposal}

    def unique(candidate: int) -> int:
        while candidate in used:
            candidate = (candidate + 1) % (1 << 64)
        used.add(candidate)
        return candidate

    if plan.strategy == "bounded-rejection":
        decision = unique(
            _derive_stream_seed(
                plan.seed,
                "rejection-decision",
                plan.initializer_role_sha256,
                plan.residual_context_sha256,
                strategy=plan.strategy,
            )
        )
        return proposal, decision, None
    resampling = unique(
        _derive_stream_seed(
            plan.seed,
            "sir-resampling",
            plan.initializer_role_sha256,
            plan.residual_context_sha256,
            strategy=plan.strategy,
            sir_particle_budget=plan.budget,
        )
    )
    return proposal, None, resampling


def _runtime_sha256() -> str:
    probe = _new_philox(0)
    first_word = int(probe.bit_generator.random_raw())
    if not 0 <= first_word < _UINT64_DENOMINATOR:
        raise RuntimeError("Philox runtime probe did not return a uint64 word")
    return _semantic_digest(
        {
            "schema": _SCHEMA_VERSION,
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "philox_module": np.random.Philox.__module__,
            "philox_name": np.random.Philox.__name__,
            "seed_zero_first_word": first_word,
            "raw_word_bits": MIXED_SUPPORT_INITIALIZER_RAW_WORD_BITS,
            "sir_uniform_bits": MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS,
            "maximum_budget": MAX_MIXED_SUPPORT_INITIALIZER_BUDGET,
        },
        domain=b"heterodiff-mixed-support-initializer-runtime-v1\x00",
    )


_CACHED_RUNTIME_SHA256 = _runtime_sha256()


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltInitializerPlan:
    """Sealed, strategy-complete plan fixed before any proposal is drawn."""

    schema_version: str
    composer: _COMPOSER_TYPE
    composer_certificate: _COMPOSER_CERTIFICATE_TYPE
    composer_certificate_sha256: str
    composer_runtime_identity: int
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    initializer_role_sha256: str
    strategy: str
    seed: Optional[int]
    budget: int
    ess_warning_fraction: Optional[float]
    adaptive_fallback_permitted: bool
    plan_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("MixedSupportInitialTiltInitializerPlan cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _PLAN_TOKEN:
            raise TypeError("initializer plans are created by the public plan factory")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer plan fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_plan(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer plans are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return ("mixed-support-initializer-plan-v1", self.plan_sha256)


def _plan_payload(plan: MixedSupportInitialTiltInitializerPlan) -> Mapping[str, object]:
    return {
        "schema_version": plan.schema_version,
        "composer_certificate_sha256": plan.composer_certificate_sha256,
        "composer_runtime_identity": plan.composer_runtime_identity,
        "residual_context_sha256": plan.residual_context_sha256,
        "initializer_role_sha256": plan.initializer_role_sha256,
        "strategy": plan.strategy,
        "seed": plan.seed,
        "budget": plan.budget,
        "ess_warning_fraction": plan.ess_warning_fraction,
        "adaptive_fallback_permitted": plan.adaptive_fallback_permitted,
    }


def _plan_payload_values(values: Mapping[str, object]) -> Mapping[str, object]:
    names = (
        "schema_version",
        "composer_certificate_sha256",
        "composer_runtime_identity",
        "residual_context_sha256",
        "initializer_role_sha256",
        "strategy",
        "seed",
        "budget",
        "ess_warning_fraction",
        "adaptive_fallback_permitted",
    )
    return {name: values[name] for name in names}


def _validate_plan(plan: object) -> MixedSupportInitialTiltInitializerPlan:
    if type(plan) is not MixedSupportInitialTiltInitializerPlan:
        raise TypeError("plan must be an exact MixedSupportInitialTiltInitializerPlan")
    if plan.schema_version != _SCHEMA_VERSION:
        raise ValueError("plan schema version differs")
    if type(plan.composer) is not _COMPOSER_TYPE:
        raise TypeError("plan composer has the wrong exact type")
    composer_certificate = _COMPOSER_VALIDATE_CERTIFICATE(plan.composer_certificate)
    if plan.composer.certificate is not composer_certificate:
        raise ValueError("plan composer certificate identity differs")
    _require_sha256(
        plan.composer_certificate_sha256,
        name="plan.composer_certificate_sha256",
    )
    if plan.composer_certificate_sha256 != composer_certificate.certificate_sha256:
        raise ValueError("plan composer certificate digest differs")
    _require_runtime_identity(
        plan.composer_runtime_identity,
        name="plan.composer_runtime_identity",
    )
    if plan.composer_runtime_identity != id(plan.composer):
        raise ValueError("plan composer runtime identity differs")
    if type(plan.residual_context) is not tuple:
        raise TypeError("plan residual_context must be an exact tuple")
    context = _VALIDATED_CONTEXT(
        plan.residual_context,
        dimension=composer_certificate.residual_context_dimension,
        name="plan.residual_context",
    )
    if context != plan.residual_context:
        raise ValueError("plan residual context is noncanonical")
    _require_sha256(plan.residual_context_sha256, name="plan residual-context digest")
    if plan.residual_context_sha256 != _CONTEXT_SHA256(context):
        raise ValueError("plan residual-context digest differs")
    _require_sha256(plan.initializer_role_sha256, name="initializer_role_sha256")
    if type(plan.strategy) is not str or plan.strategy not in _STRATEGIES:
        raise ValueError("plan strategy is unknown")
    if type(plan.adaptive_fallback_permitted) is not bool:
        raise TypeError("plan adaptive fallback flag must be boolean")
    if plan.adaptive_fallback_permitted:
        raise ValueError("adaptive fallback is forbidden")
    if plan.strategy == "finite-atomic-enumeration":
        if plan.seed is not None or plan.budget != 0:
            raise ValueError("enumeration must have no seed and zero budget")
        if plan.ess_warning_fraction is not None:
            raise ValueError("enumeration must have no ESS warning fraction")
    else:
        _require_integer(
            plan.seed,
            name="plan.seed",
            minimum=0,
            maximum=(1 << 64) - 1,
        )
        _require_integer(
            plan.budget,
            name="plan.budget",
            minimum=1,
            maximum=MAX_MIXED_SUPPORT_INITIALIZER_BUDGET,
        )
        if plan.strategy == "bounded-rejection":
            if plan.ess_warning_fraction is not None:
                raise ValueError("rejection must have no ESS warning fraction")
        else:
            fraction = _require_finite_float(
                plan.ess_warning_fraction,
                name="plan.ess_warning_fraction",
            )
            if not 0.0 < fraction <= 1.0:
                raise ValueError("SIR ESS warning fraction must lie in (0, 1]")
    _require_sha256(plan.plan_sha256, name="plan.plan_sha256")
    expected = _semantic_digest(
        _plan_payload(plan),
        domain=b"heterodiff-mixed-support-initializer-plan-v1\x00",
    )
    if plan.plan_sha256 != expected:
        raise ValueError("plan digest differs")
    return plan


def make_mixed_support_initial_tilt_initializer_plan(
    composer: _COMPOSER_TYPE,
    *,
    strategy: object,
    residual_context: object,
    initializer_role_sha256: object,
    seed: Optional[object] = None,
    budget: Optional[object] = None,
    ess_warning_fraction: Optional[object] = None,
) -> MixedSupportInitialTiltInitializerPlan:
    """Freeze the full strategy and resource plan before kernel execution."""

    if type(composer) is not _COMPOSER_TYPE:
        raise TypeError("composer must be an exact ConfigurationInitialTiltComposer")
    if type(strategy) is not str or strategy not in _STRATEGIES:
        raise ValueError("strategy must be one of the exported strategies")
    role = _require_sha256(initializer_role_sha256, name="initializer_role_sha256")
    if strategy == "finite-atomic-enumeration":
        if seed is not None:
            raise ValueError("finite-atomic enumeration accepts no seed")
        if budget is not None:
            _require_integer(
                budget,
                name="enumeration budget",
                minimum=0,
                maximum=0,
            )
        checked_seed = None
        checked_budget = 0
        checked_ess = None
    else:
        checked_seed = _require_integer(
            seed,
            name="seed",
            minimum=0,
            maximum=(1 << 64) - 1,
        )
        checked_budget = _require_integer(
            budget,
            name="budget",
            minimum=1,
            maximum=MAX_MIXED_SUPPORT_INITIALIZER_BUDGET,
        )
        if strategy == "fixed-budget-sir":
            raw_ess = (
                MIXED_SUPPORT_INITIALIZER_DEFAULT_ESS_WARNING_FRACTION
                if ess_warning_fraction is None
                else ess_warning_fraction
            )
            if type(raw_ess) is not float:
                raise TypeError("ess_warning_fraction must be an exact float")
            checked_ess = _require_finite_float(
                raw_ess,
                name="ess_warning_fraction",
            )
            if not 0.0 < checked_ess <= 1.0:
                raise ValueError("ess_warning_fraction must lie in (0, 1]")
        else:
            if ess_warning_fraction is not None:
                raise ValueError("bounded rejection accepts no ESS warning fraction")
            checked_ess = None
    snapshot = _COMPOSER_OWNER_SNAPSHOT(composer)
    _COMPOSER_LIVE_COMPONENTS(composer, snapshot)
    certificate = _COMPOSER_VALIDATE_CERTIFICATE(composer.certificate)
    context = _VALIDATED_CONTEXT(
        residual_context,
        dimension=certificate.residual_context_dimension,
        name="residual_context",
    )
    values = {
        "schema_version": _SCHEMA_VERSION,
        "composer": composer,
        "composer_certificate": certificate,
        "composer_certificate_sha256": certificate.certificate_sha256,
        "composer_runtime_identity": id(composer),
        "residual_context": context,
        "residual_context_sha256": _CONTEXT_SHA256(context),
        "initializer_role_sha256": role,
        "strategy": strategy,
        "seed": checked_seed,
        "budget": checked_budget,
        "ess_warning_fraction": checked_ess,
        "adaptive_fallback_permitted": False,
        "plan_sha256": _ZERO_SHA256,
    }
    values["plan_sha256"] = _semantic_digest(
        _plan_payload_values(values),
        domain=b"heterodiff-mixed-support-initializer-plan-v1\x00",
    )
    return MixedSupportInitialTiltInitializerPlan(
        **values,
        _construction_token=_PLAN_TOKEN,
    )


def _preflight_reference_resources(
    reference: CappedPoissonConfigurationReference,
    *,
    strategy: str,
    budget: int,
) -> Tuple[str, int, int, int, int]:
    """Refuse aggregate work before any execution stream is constructed."""

    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("resource preflight reference has the wrong exact type")
    if type(strategy) is not str or strategy not in _STRATEGIES:
        raise ValueError("resource preflight strategy is unknown")
    occurrence_limit = _require_integer(
        _reference.MAX_REFERENCE_BATCH_OCCURRENCES,
        name="reference occurrence-allocation limit",
        minimum=1,
        maximum=(1 << 63) - 1,
    )
    coordinate_limit = _require_integer(
        _reference.MAX_REFERENCE_BATCH_COORDINATES,
        name="reference coordinate-allocation limit",
        minimum=1,
        maximum=(1 << 63) - 1,
    )
    if strategy == "finite-atomic-enumeration":
        if budget != 0:
            raise ValueError("finite-atomic preflight requires zero stochastic budget")
        reference.finite_atomic_oracle()
        return (
            "finite-atomic-oracle",
            occurrence_limit,
            coordinate_limit,
            0,
            0,
        )
    checked_budget = _require_integer(
        budget,
        name="resource preflight budget",
        minimum=1,
        maximum=MAX_MIXED_SUPPORT_INITIALIZER_BUDGET,
    )
    worst_occurrences = checked_budget * reference.total_cap
    worst_coordinates = worst_occurrences * max(reference.type_dimensions.values())
    if worst_occurrences > occurrence_limit:
        raise ValueError(
            "planned stochastic worst-case occurrences exceed "
            "MAX_REFERENCE_BATCH_OCCURRENCES"
        )
    if worst_coordinates > coordinate_limit:
        raise ValueError(
            "planned stochastic worst-case coordinates exceed "
            "MAX_REFERENCE_BATCH_COORDINATES"
        )
    return (
        "stochastic-worst-case",
        occurrence_limit,
        coordinate_limit,
        worst_occurrences,
        worst_coordinates,
    )


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltInitializerCertificate:
    """Sealed ancestry, target, strategy, theorem, and nonclaim boundary."""

    schema_version: str
    certificate_scope: str
    target_policy: str
    ideal_rejection_theorem: str
    dyadic_rejection_caveat: str
    sir_theorem: str
    analytic_bridge: str
    metric_boundary: str
    resource_preflight_policy: str
    composer: _COMPOSER_TYPE
    composer_certificate: _COMPOSER_CERTIFICATE_TYPE
    composer_certificate_sha256: str
    composer_runtime_identity: int
    reference: CappedPoissonConfigurationReference
    reference_runtime_identity: int
    reference_parameter_key: Tuple[object, ...]
    reference_parameter_sha256: str
    plan: MixedSupportInitialTiltInitializerPlan
    plan_sha256: str
    residual_context_sha256: str
    initializer_role_sha256: str
    strategy: str
    seed: Optional[int]
    budget: int
    proposal_seed: Optional[int]
    rejection_decision_seed: Optional[int]
    resampling_seed: Optional[int]
    exact_log_weight_lower_bound: float
    exact_log_weight_upper_bound: float
    resource_preflight_mode: str
    reference_batch_occurrence_limit: int
    reference_batch_coordinate_limit: int
    planned_worst_case_occurrences: int
    planned_worst_case_coordinates: int
    runtime_sha256: str
    process_owned_reference_object_bound_scope: str
    process_owned_reference_object_bound: bool
    process_owned_reference_sampling_interface_used: bool
    represented_exact_rational_q_point_score_bound: bool
    strategy_preselected: bool
    aggregate_resource_preflight_passed: bool
    reference_per_configuration_sampling_gates_preserved: bool
    finite_atomic_oracle_limits_preserved: bool
    adaptive_fallback_permitted: bool
    structural_validation_replays_model_or_rng: bool
    live_philox_law_verified: bool
    operational_reference_sampling_law_verified: bool
    iid_sequence_law_verified: bool
    exact_operational_rejection_bernoulli: bool
    finite_j_sir_equals_target: bool
    analytic_pi_n_proposal_law_verified: bool
    ideal_real_fiber_q_extension_verified: bool
    analytic_h_equality_verified: bool
    continuous_empirical_tv_kl_valid: bool
    path_or_sampler_admitted: bool
    formal_test_28_closed: bool
    certificate_structural_contract_passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "MixedSupportInitialTiltInitializerCertificate cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("initializer certificates require certification")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer certificates are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return ("mixed-support-initializer-certificate-v1", self.certificate_sha256)


def _certificate_payload(
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> Mapping[str, object]:
    omitted = {"composer", "composer_certificate", "reference", "plan"}
    return {
        name: getattr(certificate, name)
        for name in certificate.__annotations__
        if name not in omitted and name != "certificate_sha256"
    }


def _certificate_payload_values(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {
        "composer",
        "composer_certificate",
        "reference",
        "plan",
        "certificate_sha256",
    }
    return {name: values[name] for name in values if name not in omitted}


def _validate_certificate(
    certificate: object,
) -> MixedSupportInitialTiltInitializerCertificate:
    if type(certificate) is not MixedSupportInitialTiltInitializerCertificate:
        raise TypeError(
            "certificate must be an exact "
            "MixedSupportInitialTiltInitializerCertificate"
        )
    expected_text = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "target_policy": _TARGET_POLICY,
        "ideal_rejection_theorem": (MIXED_SUPPORT_INITIAL_TILT_IDEAL_REJECTION_THEOREM),
        "dyadic_rejection_caveat": (MIXED_SUPPORT_INITIAL_TILT_DYADIC_REJECTION_CAVEAT),
        "sir_theorem": MIXED_SUPPORT_INITIAL_TILT_SIR_THEOREM,
        "analytic_bridge": MIXED_SUPPORT_INITIAL_TILT_ANALYTIC_BRIDGE,
        "metric_boundary": MIXED_SUPPORT_INITIAL_TILT_METRIC_BOUNDARY,
        "resource_preflight_policy": (
            MIXED_SUPPORT_INITIAL_TILT_RESOURCE_PREFLIGHT_POLICY
        ),
        "process_owned_reference_object_bound_scope": (
            MIXED_SUPPORT_INITIAL_TILT_REFERENCE_OBJECT_CUSTODY_SCOPE
        ),
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("certificate %s differs" % name)
    if type(certificate.composer) is not _COMPOSER_TYPE:
        raise TypeError("certificate composer has the wrong exact type")
    composer_certificate = _COMPOSER_VALIDATE_CERTIFICATE(
        certificate.composer_certificate
    )
    if certificate.composer.certificate is not composer_certificate:
        raise ValueError("certificate composer certificate identity differs")
    _require_sha256(
        certificate.composer_certificate_sha256,
        name="certificate.composer_certificate_sha256",
    )
    if (
        certificate.composer_certificate_sha256
        != composer_certificate.certificate_sha256
    ):
        raise ValueError("certificate composer digest differs")
    _require_runtime_identity(
        certificate.composer_runtime_identity,
        name="certificate.composer_runtime_identity",
    )
    if certificate.composer_runtime_identity != id(certificate.composer):
        raise ValueError("certificate composer runtime identity differs")
    if type(certificate.reference) is not CappedPoissonConfigurationReference:
        raise TypeError("certificate reference has the wrong exact type")
    if certificate.composer.reference_composer.process.reference is not (
        certificate.reference
    ):
        raise ValueError(
            "certificate reference is not the exact composer-owned reference object"
        )
    _require_runtime_identity(
        certificate.reference_runtime_identity,
        name="certificate.reference_runtime_identity",
    )
    if certificate.reference_runtime_identity != id(certificate.reference):
        raise ValueError("certificate reference runtime identity differs")
    if type(certificate.reference_parameter_key) is not tuple:
        raise TypeError("certificate reference parameter key must be an exact tuple")
    if certificate.reference_parameter_key != certificate.reference.parameter_key():
        raise ValueError("certificate reference parameter key differs")
    _require_sha256(
        certificate.reference_parameter_sha256,
        name="certificate.reference_parameter_sha256",
    )
    expected_reference_sha = _plain_key_sha256(
        certificate.reference_parameter_key,
        domain=b"heterodiff-mixed-support-initializer-reference-object-v1\x00",
    )
    if certificate.reference_parameter_sha256 != expected_reference_sha:
        raise ValueError("certificate reference parameter digest differs")
    plan = _validate_plan(certificate.plan)
    if plan.composer is not certificate.composer:
        raise ValueError("certificate plan belongs to a different composer")
    _require_sha256(certificate.plan_sha256, name="certificate.plan_sha256")
    if certificate.plan_sha256 != plan.plan_sha256:
        raise ValueError("certificate plan digest differs")
    for name in (
        "residual_context_sha256",
        "initializer_role_sha256",
    ):
        if getattr(certificate, name) != getattr(plan, name):
            raise ValueError("certificate %s differs from plan" % name)
    for name in ("strategy", "seed", "budget"):
        if getattr(certificate, name) != getattr(plan, name):
            raise ValueError("certificate %s differs from plan" % name)
    (
        expected_proposal_seed,
        expected_rejection_decision_seed,
        expected_resampling_seed,
    ) = _planned_stream_seeds(plan)
    if certificate.proposal_seed != expected_proposal_seed:
        raise ValueError("certificate proposal seed differs")
    if certificate.rejection_decision_seed != expected_rejection_decision_seed:
        raise ValueError("certificate rejection-decision seed differs")
    if certificate.resampling_seed != expected_resampling_seed:
        raise ValueError("certificate resampling seed differs")
    for name in ("proposal_seed", "rejection_decision_seed", "resampling_seed"):
        value = getattr(certificate, name)
        if value is not None:
            _require_integer(
                value,
                name="certificate.%s" % name,
                minimum=0,
                maximum=(1 << 64) - 1,
            )
    (
        expected_preflight_mode,
        expected_occurrence_limit,
        expected_coordinate_limit,
        expected_worst_occurrences,
        expected_worst_coordinates,
    ) = _preflight_reference_resources(
        certificate.reference,
        strategy=certificate.strategy,
        budget=certificate.budget,
    )
    for name, expected in (
        ("resource_preflight_mode", expected_preflight_mode),
        ("reference_batch_occurrence_limit", expected_occurrence_limit),
        ("reference_batch_coordinate_limit", expected_coordinate_limit),
        ("planned_worst_case_occurrences", expected_worst_occurrences),
        ("planned_worst_case_coordinates", expected_worst_coordinates),
    ):
        supplied = getattr(certificate, name)
        if type(expected) is int:
            _require_integer(
                supplied,
                name="certificate.%s" % name,
                minimum=0,
                maximum=(1 << 63) - 1,
            )
        elif type(supplied) is not str:
            raise TypeError("certificate.%s must be exact text" % name)
        if supplied != expected:
            raise ValueError("certificate %s differs from resource preflight" % name)
    lower = _require_finite_float(
        certificate.exact_log_weight_lower_bound,
        name="certificate exact-log-weight lower bound",
    )
    upper = _require_finite_float(
        certificate.exact_log_weight_upper_bound,
        name="certificate exact-log-weight upper bound",
    )
    if not _same_float(lower, composer_certificate.initial_log_factor_lower_bound):
        raise ValueError("certificate lower bound differs from composer")
    if not _same_float(upper, composer_certificate.initial_log_factor_upper_bound):
        raise ValueError("certificate upper bound differs from composer")
    if lower > upper:
        raise ValueError("certificate exact-log-weight bounds are empty")
    _require_sha256(certificate.runtime_sha256, name="certificate.runtime_sha256")
    if certificate.runtime_sha256 != _CACHED_RUNTIME_SHA256:
        raise ValueError("certificate runtime digest differs")
    true_flags = (
        "process_owned_reference_object_bound",
        "represented_exact_rational_q_point_score_bound",
        "strategy_preselected",
        "aggregate_resource_preflight_passed",
        "reference_per_configuration_sampling_gates_preserved",
        "finite_atomic_oracle_limits_preserved",
        "certificate_structural_contract_passed",
    )
    false_flags = (
        "adaptive_fallback_permitted",
        "structural_validation_replays_model_or_rng",
        "live_philox_law_verified",
        "operational_reference_sampling_law_verified",
        "iid_sequence_law_verified",
        "exact_operational_rejection_bernoulli",
        "finite_j_sir_equals_target",
        "analytic_pi_n_proposal_law_verified",
        "ideal_real_fiber_q_extension_verified",
        "analytic_h_equality_verified",
        "continuous_empirical_tv_kl_valid",
        "path_or_sampler_admitted",
        "formal_test_28_closed",
    )
    if type(certificate.process_owned_reference_sampling_interface_used) is not bool:
        raise TypeError(
            "certificate.process_owned_reference_sampling_interface_used must be boolean"
        )
    if certificate.process_owned_reference_sampling_interface_used != (
        certificate.strategy != "finite-atomic-enumeration"
    ):
        raise ValueError("certificate reference-sampling-interface use flag differs")
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("certificate positive claim flags differ")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("certificate negative claim flags differ")
    _require_sha256(certificate.certificate_sha256, name="certificate digest")
    expected_digest = _semantic_digest(
        _certificate_payload(certificate),
        domain=b"heterodiff-mixed-support-initializer-certificate-v1\x00",
    )
    if certificate.certificate_sha256 != expected_digest:
        raise ValueError("certificate digest differs")
    return certificate


def validate_mixed_support_initial_tilt_initializer_certificate(
    certificate: object,
) -> MixedSupportInitialTiltInitializerCertificate:
    """Structurally validate a certificate without replaying model or RNG work."""

    return _validate_certificate(certificate)


def _make_certificate(
    composer: _COMPOSER_TYPE,
    plan: MixedSupportInitialTiltInitializerPlan,
) -> MixedSupportInitialTiltInitializerCertificate:
    reference = composer.reference_composer.process.reference
    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("composer reference object has the wrong exact type")
    composer_certificate = _COMPOSER_VALIDATE_CERTIFICATE(composer.certificate)
    reference_key = reference.parameter_key()
    proposal_seed, rejection_decision_seed, resampling_seed = _planned_stream_seeds(
        plan
    )
    (
        preflight_mode,
        occurrence_limit,
        coordinate_limit,
        worst_occurrences,
        worst_coordinates,
    ) = _preflight_reference_resources(
        reference,
        strategy=plan.strategy,
        budget=plan.budget,
    )
    values = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "target_policy": _TARGET_POLICY,
        "ideal_rejection_theorem": (MIXED_SUPPORT_INITIAL_TILT_IDEAL_REJECTION_THEOREM),
        "dyadic_rejection_caveat": (MIXED_SUPPORT_INITIAL_TILT_DYADIC_REJECTION_CAVEAT),
        "sir_theorem": MIXED_SUPPORT_INITIAL_TILT_SIR_THEOREM,
        "analytic_bridge": MIXED_SUPPORT_INITIAL_TILT_ANALYTIC_BRIDGE,
        "metric_boundary": MIXED_SUPPORT_INITIAL_TILT_METRIC_BOUNDARY,
        "resource_preflight_policy": (
            MIXED_SUPPORT_INITIAL_TILT_RESOURCE_PREFLIGHT_POLICY
        ),
        "composer": composer,
        "composer_certificate": composer_certificate,
        "composer_certificate_sha256": composer_certificate.certificate_sha256,
        "composer_runtime_identity": id(composer),
        "reference": reference,
        "reference_runtime_identity": id(reference),
        "reference_parameter_key": reference_key,
        "reference_parameter_sha256": _plain_key_sha256(
            reference_key,
            domain=b"heterodiff-mixed-support-initializer-reference-object-v1\x00",
        ),
        "plan": plan,
        "plan_sha256": plan.plan_sha256,
        "residual_context_sha256": plan.residual_context_sha256,
        "initializer_role_sha256": plan.initializer_role_sha256,
        "strategy": plan.strategy,
        "seed": plan.seed,
        "budget": plan.budget,
        "proposal_seed": proposal_seed,
        "rejection_decision_seed": rejection_decision_seed,
        "resampling_seed": resampling_seed,
        "exact_log_weight_lower_bound": (
            composer_certificate.initial_log_factor_lower_bound
        ),
        "exact_log_weight_upper_bound": (
            composer_certificate.initial_log_factor_upper_bound
        ),
        "resource_preflight_mode": preflight_mode,
        "reference_batch_occurrence_limit": occurrence_limit,
        "reference_batch_coordinate_limit": coordinate_limit,
        "planned_worst_case_occurrences": worst_occurrences,
        "planned_worst_case_coordinates": worst_coordinates,
        "runtime_sha256": _CACHED_RUNTIME_SHA256,
        "process_owned_reference_object_bound_scope": (
            MIXED_SUPPORT_INITIAL_TILT_REFERENCE_OBJECT_CUSTODY_SCOPE
        ),
        "process_owned_reference_object_bound": True,
        "process_owned_reference_sampling_interface_used": (
            plan.strategy != "finite-atomic-enumeration"
        ),
        "represented_exact_rational_q_point_score_bound": True,
        "strategy_preselected": True,
        "aggregate_resource_preflight_passed": True,
        "reference_per_configuration_sampling_gates_preserved": True,
        "finite_atomic_oracle_limits_preserved": True,
        "adaptive_fallback_permitted": False,
        "structural_validation_replays_model_or_rng": False,
        "live_philox_law_verified": False,
        "operational_reference_sampling_law_verified": False,
        "iid_sequence_law_verified": False,
        "exact_operational_rejection_bernoulli": False,
        "finite_j_sir_equals_target": False,
        "analytic_pi_n_proposal_law_verified": False,
        "ideal_real_fiber_q_extension_verified": False,
        "analytic_h_equality_verified": False,
        "continuous_empirical_tv_kl_valid": False,
        "path_or_sampler_admitted": False,
        "formal_test_28_closed": False,
        "certificate_structural_contract_passed": True,
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _semantic_digest(
        _certificate_payload_values(values),
        domain=b"heterodiff-mixed-support-initializer-certificate-v1\x00",
    )
    return MixedSupportInitialTiltInitializerCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltScoredConfiguration:
    """One reference-interface configuration and its represented exact score."""

    index: int
    configuration: TransformedConfiguration
    configuration_sha256: str
    evaluation: _EVALUATION_TYPE
    evaluation_sha256: str
    exact_log_weight_numerator: int
    exact_log_weight_denominator: int
    operational_log_weight: float
    scored_configuration_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _SCORED_TOKEN:
            raise TypeError("scored configurations are kernel-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("scored configuration fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("scored configurations are not pickle objects")


def _scored_payload(record: MixedSupportInitialTiltScoredConfiguration) -> dict:
    return {
        "index": record.index,
        "configuration_sha256": record.configuration_sha256,
        "evaluation_sha256": record.evaluation_sha256,
        "exact_log_weight_numerator": record.exact_log_weight_numerator,
        "exact_log_weight_denominator": record.exact_log_weight_denominator,
        "operational_log_weight": record.operational_log_weight,
    }


def _validate_scored(
    record: object,
    *,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltScoredConfiguration:
    if type(record) is not MixedSupportInitialTiltScoredConfiguration:
        raise TypeError("record must be an exact scored configuration")
    _require_integer(
        record.index,
        name="scored.index",
        minimum=0,
        maximum=MAX_MIXED_SUPPORT_INITIALIZER_BUDGET,
    )
    if type(record.configuration) is not tuple:
        raise TypeError("scored configuration must be an exact tuple")
    configuration_sha = _CONFIGURATION_SHA256(record.configuration)
    _require_sha256(record.configuration_sha256, name="configuration digest")
    if record.configuration_sha256 != configuration_sha:
        raise ValueError("scored configuration digest differs")
    evaluation = _structural_evaluation(
        record.evaluation,
        composer_certificate=certificate.composer_certificate,
        residual_context=certificate.plan.residual_context,
        configuration=record.configuration,
    )
    _require_sha256(record.evaluation_sha256, name="evaluation digest")
    if record.evaluation_sha256 != evaluation.evaluation_sha256:
        raise ValueError("scored evaluation digest differs")
    q = _validated_fraction_parts(
        record.exact_log_weight_numerator,
        record.exact_log_weight_denominator,
        name="scored exact log weight",
    )
    if q != _fraction_from_evaluation(evaluation):
        raise ValueError("scored exact log weight differs from evaluation")
    lower = Fraction.from_float(certificate.exact_log_weight_lower_bound)
    upper = Fraction.from_float(certificate.exact_log_weight_upper_bound)
    if not lower <= q <= upper:
        raise ValueError("scored exact log weight lies outside certified bounds")
    operational = _require_finite_float(
        record.operational_log_weight,
        name="scored operational log weight",
    )
    if not _same_float(operational, float(q)):
        raise ValueError("scored operational log weight is not rounded exact q")
    _require_sha256(
        record.scored_configuration_sha256,
        name="scored-configuration digest",
    )
    expected = _semantic_digest(
        _scored_payload(record),
        domain=b"heterodiff-mixed-support-scored-configuration-v1\x00",
    )
    if record.scored_configuration_sha256 != expected:
        raise ValueError("scored-configuration digest differs")
    return record


def _make_scored(
    *,
    index: int,
    configuration: TransformedConfiguration,
    evaluation: _EVALUATION_TYPE,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltScoredConfiguration:
    q = _fraction_from_evaluation(evaluation)
    values = {
        "index": index,
        "configuration": configuration,
        "configuration_sha256": _CONFIGURATION_SHA256(configuration),
        "evaluation": evaluation,
        "evaluation_sha256": evaluation.evaluation_sha256,
        "exact_log_weight_numerator": q.numerator,
        "exact_log_weight_denominator": q.denominator,
        "operational_log_weight": float(q),
        "scored_configuration_sha256": _ZERO_SHA256,
    }
    provisional = MixedSupportInitialTiltScoredConfiguration(
        **values,
        _construction_token=_SCORED_TOKEN,
    )
    values["scored_configuration_sha256"] = _semantic_digest(
        _scored_payload(provisional),
        domain=b"heterodiff-mixed-support-scored-configuration-v1\x00",
    )
    result = MixedSupportInitialTiltScoredConfiguration(
        **values,
        _construction_token=_SCORED_TOKEN,
    )
    return _validate_scored(result, certificate=certificate)


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltRejectionAttempt:
    """One proposal and its conservative uint64 acceptance decision."""

    scored: MixedSupportInitialTiltScoredConfiguration
    delta_numerator: int
    delta_denominator: int
    quota_branch: str
    quota_precision: int
    quota: int
    decision_word: int
    accepted: bool
    attempt_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ATTEMPT_TOKEN:
            raise TypeError("rejection attempts are kernel-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("rejection attempt fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection attempts are not pickle objects")


def _attempt_payload(attempt: MixedSupportInitialTiltRejectionAttempt) -> dict:
    return {
        "scored_configuration_sha256": attempt.scored.scored_configuration_sha256,
        "delta_numerator": attempt.delta_numerator,
        "delta_denominator": attempt.delta_denominator,
        "quota_branch": attempt.quota_branch,
        "quota_precision": attempt.quota_precision,
        "quota": attempt.quota,
        "decision_word": attempt.decision_word,
        "accepted": attempt.accepted,
    }


def _validate_attempt(
    attempt: object,
    *,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltRejectionAttempt:
    if type(attempt) is not MixedSupportInitialTiltRejectionAttempt:
        raise TypeError("attempt has the wrong exact type")
    scored = _validate_scored(attempt.scored, certificate=certificate)
    delta = _validated_fraction_parts(
        attempt.delta_numerator,
        attempt.delta_denominator,
        name="attempt rejection log gap",
    )
    expected_delta = _fraction_from_evaluation(scored.evaluation) - Fraction.from_float(
        certificate.exact_log_weight_upper_bound
    )
    if delta != expected_delta or delta > 0:
        raise ValueError("attempt rejection log gap differs")
    quota_data = certify_mixed_support_rejection_quota(delta)
    if type(attempt.quota_branch) is not str:
        raise TypeError("attempt quota branch must be exact text")
    _require_integer(
        attempt.quota_precision,
        name="attempt.quota_precision",
        minimum=0,
        maximum=_QUOTA_MAX_PRECISION,
    )
    _require_integer(
        attempt.quota,
        name="attempt.quota",
        minimum=0,
        maximum=_UINT64_DENOMINATOR,
    )
    if attempt.quota_branch != quota_data.branch:
        raise ValueError("attempt quota branch differs")
    if attempt.quota_precision != quota_data.precision:
        raise ValueError("attempt quota precision differs")
    if attempt.quota != quota_data.quota:
        raise ValueError("attempt quota differs")
    word = _require_integer(
        attempt.decision_word,
        name="attempt.decision_word",
        minimum=0,
        maximum=_UINT64_DENOMINATOR - 1,
    )
    if type(attempt.accepted) is not bool:
        raise TypeError("attempt accepted flag must be boolean")
    if attempt.accepted != (word < attempt.quota):
        raise ValueError("attempt acceptance flag differs from quota comparison")
    _require_sha256(attempt.attempt_sha256, name="attempt digest")
    expected = _semantic_digest(
        _attempt_payload(attempt),
        domain=b"heterodiff-mixed-support-rejection-attempt-v1\x00",
    )
    if attempt.attempt_sha256 != expected:
        raise ValueError("attempt digest differs")
    return attempt


def _make_attempt(
    scored: MixedSupportInitialTiltScoredConfiguration,
    word: int,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltRejectionAttempt:
    delta = _fraction_from_evaluation(scored.evaluation) - Fraction.from_float(
        certificate.exact_log_weight_upper_bound
    )
    quota_data = certify_mixed_support_rejection_quota(delta)
    values = {
        "scored": scored,
        "delta_numerator": delta.numerator,
        "delta_denominator": delta.denominator,
        "quota_branch": quota_data.branch,
        "quota_precision": quota_data.precision,
        "quota": quota_data.quota,
        "decision_word": word,
        "accepted": word < quota_data.quota,
        "attempt_sha256": _ZERO_SHA256,
    }
    provisional = MixedSupportInitialTiltRejectionAttempt(
        **values,
        _construction_token=_ATTEMPT_TOKEN,
    )
    values["attempt_sha256"] = _semantic_digest(
        _attempt_payload(provisional),
        domain=b"heterodiff-mixed-support-rejection-attempt-v1\x00",
    )
    return _validate_attempt(
        MixedSupportInitialTiltRejectionAttempt(
            **values,
            _construction_token=_ATTEMPT_TOKEN,
        ),
        certificate=certificate,
    )


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltSIRParticle:
    """One fixed-budget SIR particle and its float64 normalized weight."""

    scored: MixedSupportInitialTiltScoredConfiguration
    normalized_weight: float
    particle_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _PARTICLE_TOKEN:
            raise TypeError("SIR particles are kernel-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("SIR particle fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("SIR particles are not pickle objects")


def _particle_digest(
    scored_sha256: str,
    normalized_weight: float,
) -> str:
    return _semantic_digest(
        {
            "scored_configuration_sha256": scored_sha256,
            "normalized_weight": normalized_weight,
        },
        domain=b"heterodiff-mixed-support-SIR-particle-v1\x00",
    )


def _validate_particle(
    particle: object,
    *,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltSIRParticle:
    if type(particle) is not MixedSupportInitialTiltSIRParticle:
        raise TypeError("particle has the wrong exact type")
    scored = _validate_scored(particle.scored, certificate=certificate)
    weight = _require_finite_float(
        particle.normalized_weight,
        name="particle normalized weight",
    )
    if not 0.0 < weight <= 1.0:
        raise ValueError("particle normalized weight must lie in (0, 1]")
    _require_sha256(particle.particle_sha256, name="particle digest")
    if particle.particle_sha256 != _particle_digest(
        scored.scored_configuration_sha256,
        weight,
    ):
        raise ValueError("particle digest differs")
    return particle


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltEnumerationAtom:
    """One complete finite-atomic support state and normalized target mass."""

    count_state: Tuple[int, ...]
    base_mass: float
    scored: MixedSupportInitialTiltScoredConfiguration
    normalized_probability: float
    atom_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ATOM_TOKEN:
            raise TypeError("enumeration atoms are kernel-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("enumeration atom fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("enumeration atoms are not pickle objects")


def _atom_digest(
    state: Tuple[int, ...],
    base_mass: float,
    scored_sha256: str,
    normalized_probability: float,
) -> str:
    return _semantic_digest(
        {
            "count_state": state,
            "base_mass": base_mass,
            "scored_configuration_sha256": scored_sha256,
            "normalized_probability": normalized_probability,
        },
        domain=b"heterodiff-mixed-support-enumeration-atom-v1\x00",
    )


def _validate_atom(
    atom: object,
    *,
    certificate: MixedSupportInitialTiltInitializerCertificate,
    expected_type_count: int,
) -> MixedSupportInitialTiltEnumerationAtom:
    if type(atom) is not MixedSupportInitialTiltEnumerationAtom:
        raise TypeError("enumeration atom has the wrong exact type")
    if (
        type(atom.count_state) is not tuple
        or len(atom.count_state) != expected_type_count
    ):
        raise ValueError("enumeration count state has the wrong shape")
    for count in atom.count_state:
        _require_integer(
            count,
            name="enumeration count",
            minimum=0,
            maximum=certificate.reference.total_cap,
        )
    if sum(atom.count_state) > certificate.reference.total_cap:
        raise ValueError("enumeration count state exceeds the cap")
    base_mass = _require_finite_float(atom.base_mass, name="enumeration base mass")
    probability = _require_finite_float(
        atom.normalized_probability,
        name="enumeration normalized probability",
    )
    if not 0.0 < base_mass <= 1.0 or not 0.0 < probability <= 1.0:
        raise ValueError("enumeration masses must lie in (0, 1]")
    scored = _validate_scored(atom.scored, certificate=certificate)
    _require_sha256(atom.atom_sha256, name="enumeration atom digest")
    if atom.atom_sha256 != _atom_digest(
        atom.count_state,
        base_mass,
        scored.scored_configuration_sha256,
        probability,
    ):
        raise ValueError("enumeration atom digest differs")
    return atom


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltRejectionResult:
    """Selected or explicitly exhausted bounded rejection execution."""

    certificate: MixedSupportInitialTiltInitializerCertificate
    certificate_sha256: str
    status: str
    attempts: Tuple[MixedSupportInitialTiltRejectionAttempt, ...]
    selected_index: Optional[int]
    selected_configuration: Optional[TransformedConfiguration]
    selected_configuration_sha256: Optional[str]
    proposal_stream_initial_state_sha256: str
    proposal_stream_final_state_sha256: str
    decision_stream_initial_state_sha256: str
    decision_stream_final_state_sha256: str
    result_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _REJECTION_RESULT_TOKEN:
            raise TypeError("rejection results are kernel-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("rejection result fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection results are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltSIRResult:
    """One fixed-``J`` operational self-normalized resampling result."""

    certificate: MixedSupportInitialTiltInitializerCertificate
    certificate_sha256: str
    status: str
    particles: Tuple[MixedSupportInitialTiltSIRParticle, ...]
    normalized_weights: np.ndarray
    effective_sample_size: float
    maximum_normalized_weight: float
    ess_warning: bool
    selected_index: int
    selected_configuration: TransformedConfiguration
    selected_configuration_sha256: str
    proposal_stream_initial_state_sha256: str
    proposal_stream_final_state_sha256: str
    resampling_stream_initial_state_sha256: str
    resampling_stream_final_state_sha256: str
    resampling_word: int
    resampling_uniform_53: int
    result_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _SIR_RESULT_TOKEN:
            raise TypeError("SIR results are kernel-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("SIR result fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("SIR results are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltEnumerationResult:
    """Complete all-atomic support enumeration with float64 normalization."""

    certificate: MixedSupportInitialTiltInitializerCertificate
    certificate_sha256: str
    status: str
    atoms: Tuple[MixedSupportInitialTiltEnumerationAtom, ...]
    base_masses: np.ndarray
    normalized_probabilities: np.ndarray
    operational_log_normalizer: float
    result_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ENUMERATION_RESULT_TOKEN:
            raise TypeError("enumeration results are kernel-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("enumeration result fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("enumeration results are not pickle objects")


MixedSupportInitialTiltInitializerResult = Union[
    MixedSupportInitialTiltRejectionResult,
    MixedSupportInitialTiltSIRResult,
    MixedSupportInitialTiltEnumerationResult,
]


def _rejection_result_payload(result: MixedSupportInitialTiltRejectionResult) -> dict:
    return {
        "certificate_sha256": result.certificate_sha256,
        "status": result.status,
        "attempt_digests": tuple(attempt.attempt_sha256 for attempt in result.attempts),
        "selected_index": result.selected_index,
        "selected_configuration_sha256": result.selected_configuration_sha256,
        "proposal_stream_initial_state_sha256": (
            result.proposal_stream_initial_state_sha256
        ),
        "proposal_stream_final_state_sha256": (
            result.proposal_stream_final_state_sha256
        ),
        "decision_stream_initial_state_sha256": (
            result.decision_stream_initial_state_sha256
        ),
        "decision_stream_final_state_sha256": (
            result.decision_stream_final_state_sha256
        ),
    }


def _sir_result_payload(result: MixedSupportInitialTiltSIRResult) -> dict:
    return {
        "certificate_sha256": result.certificate_sha256,
        "status": result.status,
        "particle_digests": tuple(
            particle.particle_sha256 for particle in result.particles
        ),
        "normalized_weights": tuple(
            float(value) for value in result.normalized_weights
        ),
        "effective_sample_size": result.effective_sample_size,
        "maximum_normalized_weight": result.maximum_normalized_weight,
        "ess_warning": result.ess_warning,
        "selected_index": result.selected_index,
        "selected_configuration_sha256": result.selected_configuration_sha256,
        "proposal_stream_initial_state_sha256": (
            result.proposal_stream_initial_state_sha256
        ),
        "proposal_stream_final_state_sha256": (
            result.proposal_stream_final_state_sha256
        ),
        "resampling_stream_initial_state_sha256": (
            result.resampling_stream_initial_state_sha256
        ),
        "resampling_stream_final_state_sha256": (
            result.resampling_stream_final_state_sha256
        ),
        "resampling_word": result.resampling_word,
        "resampling_uniform_53": result.resampling_uniform_53,
    }


def _enumeration_result_payload(
    result: MixedSupportInitialTiltEnumerationResult,
) -> dict:
    return {
        "certificate_sha256": result.certificate_sha256,
        "status": result.status,
        "atom_digests": tuple(atom.atom_sha256 for atom in result.atoms),
        "base_masses": tuple(float(value) for value in result.base_masses),
        "normalized_probabilities": tuple(
            float(value) for value in result.normalized_probabilities
        ),
        "operational_log_normalizer": result.operational_log_normalizer,
    }


def _validate_rejection_result(
    result: object,
    *,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltRejectionResult:
    if type(result) is not MixedSupportInitialTiltRejectionResult:
        raise TypeError("result has the wrong rejection-result type")
    if result.certificate is not certificate:
        raise ValueError("result belongs to a different certificate")
    if result.certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    if certificate.strategy != "bounded-rejection":
        raise ValueError("rejection result has the wrong planned strategy")
    if type(result.status) is not str or result.status not in (
        "selected",
        "exhausted",
    ):
        raise ValueError("rejection result status is unknown")
    if type(result.attempts) is not tuple or len(result.attempts) != certificate.budget:
        raise ValueError("rejection result must retain the full fixed attempt budget")
    accepted_indices = []
    for index, attempt in enumerate(result.attempts):
        checked = _validate_attempt(attempt, certificate=certificate)
        if checked.scored.index != index:
            raise ValueError("rejection attempt indices are not consecutive")
        if checked.accepted:
            accepted_indices.append(index)
    if result.status == "selected":
        selected_index = _require_integer(
            result.selected_index,
            name="rejection selected_index",
            minimum=0,
            maximum=certificate.budget - 1,
        )
        if not accepted_indices or selected_index != accepted_indices[0]:
            raise ValueError("selected rejection index differs")
        selected = result.attempts[selected_index].scored.configuration
        if result.selected_configuration != selected:
            raise ValueError("selected rejection configuration differs")
        expected_sha = _CONFIGURATION_SHA256(selected)
        if result.selected_configuration_sha256 != expected_sha:
            raise ValueError("selected rejection configuration digest differs")
    else:
        if accepted_indices:
            raise ValueError("exhaustion requires every planned attempt to reject")
        if (
            result.selected_index is not None
            or result.selected_configuration is not None
            or result.selected_configuration_sha256 is not None
        ):
            raise ValueError("exhaustion cannot retain a selected configuration")
    for name in (
        "proposal_stream_initial_state_sha256",
        "proposal_stream_final_state_sha256",
        "decision_stream_initial_state_sha256",
        "decision_stream_final_state_sha256",
        "result_sha256",
    ):
        _require_sha256(getattr(result, name), name="rejection result %s" % name)
    expected_result_sha = _semantic_digest(
        _rejection_result_payload(result),
        domain=b"heterodiff-mixed-support-rejection-result-v1\x00",
    )
    if result.result_sha256 != expected_result_sha:
        raise ValueError("rejection result digest differs")
    return result


def _validate_sir_result(
    result: object,
    *,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltSIRResult:
    if type(result) is not MixedSupportInitialTiltSIRResult:
        raise TypeError("result has the wrong SIR-result type")
    if result.certificate is not certificate:
        raise ValueError("result belongs to a different certificate")
    if result.certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    if (
        certificate.strategy != "fixed-budget-sir"
        or type(result.status) is not str
        or result.status != "selected"
    ):
        raise ValueError("SIR result has the wrong strategy or status")
    if (
        type(result.particles) is not tuple
        or len(result.particles) != certificate.budget
    ):
        raise ValueError("SIR result does not contain the fixed particle budget")
    checked_weights = []
    exact_log_weights = []
    for index, particle in enumerate(result.particles):
        checked = _validate_particle(particle, certificate=certificate)
        if checked.scored.index != index:
            raise ValueError("SIR particle indices are not consecutive")
        checked_weights.append(checked.normalized_weight)
        exact_log_weights.append(_fraction_from_evaluation(checked.scored.evaluation))
    weights = _immutable_float_array(result.normalized_weights, name="SIR weights")
    retained_weights = _immutable_float_array(checked_weights, name="particle weights")
    expected_weights = normalize_mixed_support_sir_exact_log_weights(
        tuple(exact_log_weights)
    )
    if not _same_float_array(retained_weights, expected_weights):
        raise ValueError("SIR particle weights differ from retained exact q values")
    if not _same_float_array(weights, expected_weights):
        raise ValueError("SIR result weights differ from particle records")
    total = math.fsum(float(value) for value in weights)
    if abs(total - 1.0) > 32.0 * len(weights) * np.finfo(np.float64).eps:
        raise ValueError("SIR normalized weights do not sum to one")
    expected_ess = 1.0 / math.fsum(float(value * value) for value in weights)
    expected_maximum = float(np.max(weights))
    if not _same_float(result.effective_sample_size, expected_ess):
        raise ValueError("SIR effective sample size differs")
    if not _same_float(result.maximum_normalized_weight, expected_maximum):
        raise ValueError("SIR maximum normalized weight differs")
    if type(result.ess_warning) is not bool:
        raise TypeError("SIR ESS warning must be boolean")
    expected_warning = expected_ess < (
        certificate.plan.ess_warning_fraction * certificate.budget
    )
    if result.ess_warning != expected_warning:
        raise ValueError("SIR ESS warning differs")
    selected_index = _require_integer(
        result.selected_index,
        name="SIR selected_index",
        minimum=0,
        maximum=certificate.budget - 1,
    )
    selected = result.particles[selected_index].scored.configuration
    if result.selected_configuration != selected:
        raise ValueError("SIR selected configuration differs")
    if result.selected_configuration_sha256 != _CONFIGURATION_SHA256(selected):
        raise ValueError("SIR selected configuration digest differs")
    for name in (
        "proposal_stream_initial_state_sha256",
        "proposal_stream_final_state_sha256",
        "resampling_stream_initial_state_sha256",
        "resampling_stream_final_state_sha256",
        "result_sha256",
    ):
        _require_sha256(getattr(result, name), name="SIR result %s" % name)
    word = _require_integer(
        result.resampling_word,
        name="SIR resampling word",
        minimum=0,
        maximum=_UINT64_DENOMINATOR - 1,
    )
    uniform53 = _require_integer(
        result.resampling_uniform_53,
        name="SIR 53-bit uniform",
        minimum=0,
        maximum=(1 << MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS) - 1,
    )
    if uniform53 != word >> (
        MIXED_SUPPORT_INITIALIZER_RAW_WORD_BITS
        - MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS
    ):
        raise ValueError("SIR 53-bit uniform differs from the raw word")
    expected_index = select_mixed_support_sir_index(weights, word)
    if selected_index != expected_index:
        raise ValueError("SIR selected index differs from categorical transform")
    expected_result_sha = _semantic_digest(
        _sir_result_payload(result),
        domain=b"heterodiff-mixed-support-SIR-result-v1\x00",
    )
    if result.result_sha256 != expected_result_sha:
        raise ValueError("SIR result digest differs")
    return result


def _validate_enumeration_result(
    result: object,
    *,
    certificate: MixedSupportInitialTiltInitializerCertificate,
) -> MixedSupportInitialTiltEnumerationResult:
    if type(result) is not MixedSupportInitialTiltEnumerationResult:
        raise TypeError("result has the wrong enumeration-result type")
    if result.certificate is not certificate:
        raise ValueError("result belongs to a different certificate")
    if result.certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    if (
        certificate.strategy != "finite-atomic-enumeration"
        or type(result.status) is not str
        or result.status != "enumerated"
    ):
        raise ValueError("enumeration result has the wrong strategy or status")
    if any(
        dimension != 0 for dimension in certificate.reference.type_dimensions.values()
    ):
        raise ValueError("enumeration result requires all-zero-dimensional fibers")
    space, _, oracle_masses = certificate.reference.finite_atomic_oracle()
    if type(result.atoms) is not tuple or len(result.atoms) != len(space.states):
        raise ValueError("enumeration result does not contain the complete support")
    probabilities = []
    base_masses = []
    exact_log_weights = []
    for index, (atom, state) in enumerate(zip(result.atoms, space.states)):
        checked = _validate_atom(
            atom,
            certificate=certificate,
            expected_type_count=len(certificate.reference.type_ids),
        )
        if checked.scored.index != index or checked.count_state != state:
            raise ValueError("enumeration atom order differs from the oracle")
        expected_configuration = certificate.reference.canonicalize(
            tuple(
                TransformedEvent(type_id, ())
                for type_id, count in zip(certificate.reference.type_ids, state)
                for _ in range(count)
            )
        )
        if checked.scored.configuration != expected_configuration:
            raise ValueError(
                "enumeration atom configuration differs from its count state"
            )
        if checked.scored.configuration_sha256 != _CONFIGURATION_SHA256(
            expected_configuration
        ):
            raise ValueError(
                "enumeration atom configuration digest differs from its count state"
            )
        if not _same_float(checked.base_mass, float(oracle_masses[index])):
            raise ValueError("enumeration base mass differs from the oracle")
        base_masses.append(checked.base_mass)
        probabilities.append(checked.normalized_probability)
        exact_log_weights.append(_fraction_from_evaluation(checked.scored.evaluation))
    supplied_base = _immutable_float_array(result.base_masses, name="base masses")
    expected_base = _immutable_float_array(base_masses, name="atom base masses")
    if not _same_float_array(supplied_base, expected_base):
        raise ValueError("enumeration base-mass array differs")
    supplied_probabilities = _immutable_float_array(
        result.normalized_probabilities,
        name="enumeration probabilities",
    )
    retained_probabilities = _immutable_float_array(
        probabilities,
        name="atom probabilities",
    )
    (
        expected_probabilities,
        expected_log_normalizer,
    ) = normalize_mixed_support_atomic_exact_log_weights(
        expected_base,
        tuple(exact_log_weights),
    )
    if not _same_float_array(retained_probabilities, expected_probabilities):
        raise ValueError("enumeration atom probabilities differ from exact q values")
    if not _same_float_array(supplied_probabilities, expected_probabilities):
        raise ValueError("enumeration probability array differs")
    if abs(math.fsum(probabilities) - 1.0) > (
        32.0 * len(probabilities) * np.finfo(np.float64).eps
    ):
        raise ValueError("enumeration probabilities do not sum to one")
    log_normalizer = _require_finite_float(
        result.operational_log_normalizer,
        name="enumeration operational log normalizer",
    )
    if not _same_float(log_normalizer, expected_log_normalizer):
        raise ValueError("enumeration operational log normalizer differs")
    _require_sha256(result.result_sha256, name="enumeration result digest")
    expected_sha = _semantic_digest(
        _enumeration_result_payload(result),
        domain=b"heterodiff-mixed-support-enumeration-result-v1\x00",
    )
    if result.result_sha256 != expected_sha:
        raise ValueError("enumeration result digest differs")
    return result


class MixedSupportInitialTiltInitializerKernel:
    """Immutable owner of one precommitted mixed-support initializer kernel."""

    __slots__ = (
        "_composer",
        "_composer_identity",
        "_reference",
        "_reference_identity",
        "_plan",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("MixedSupportInitialTiltInitializerKernel cannot be subclassed")

    def __init__(
        self,
        *,
        composer: _COMPOSER_TYPE,
        reference: CappedPoissonConfigurationReference,
        plan: MixedSupportInitialTiltInitializerPlan,
        certificate: MixedSupportInitialTiltInitializerCertificate,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("initializer kernels require certification")
        object.__setattr__(self, "_composer", composer)
        object.__setattr__(self, "_composer_identity", composer)
        object.__setattr__(self, "_reference", reference)
        object.__setattr__(self, "_reference_identity", reference)
        object.__setattr__(self, "_plan", _validate_plan(plan))
        object.__setattr__(self, "_certificate", _validate_certificate(certificate))
        self._require_snapshot(self._snapshot())

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("MixedSupportInitialTiltInitializerKernel is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("MixedSupportInitialTiltInitializerKernel is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer kernels are not pickle objects")

    @property
    def composer(self) -> _COMPOSER_TYPE:
        return self._composer

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        return self._reference

    @property
    def plan(self) -> MixedSupportInitialTiltInitializerPlan:
        return self._plan

    @property
    def certificate(self) -> MixedSupportInitialTiltInitializerCertificate:
        return self._certificate

    def parameter_key(self) -> Tuple[object, ...]:
        return ("mixed-support-initializer-kernel-v1", self.certificate.parameter_key())

    def _snapshot(self) -> tuple:
        return (self._composer, self._reference, self._plan, self._certificate)

    def _require_snapshot(self, snapshot: object) -> tuple:
        if type(snapshot) is not tuple or len(snapshot) != 4:
            raise TypeError("kernel snapshot must be an exact four-item tuple")
        composer, reference, plan, certificate = snapshot
        if self._composer is not composer or self._composer_identity is not composer:
            raise ValueError("kernel composer identity changed")
        if (
            self._reference is not reference
            or self._reference_identity is not reference
        ):
            raise ValueError("kernel reference identity changed")
        if self._plan is not plan or self._certificate is not certificate:
            raise ValueError("kernel plan or certificate identity changed")
        _validate_plan(plan)
        _validate_certificate(certificate)
        if plan.composer is not composer or certificate.composer is not composer:
            raise ValueError("kernel ancestry differs")
        if certificate.reference is not reference:
            raise ValueError("kernel certificate reference differs")
        return snapshot

    def revalidate_live_components(
        self,
    ) -> MixedSupportInitialTiltInitializerCertificate:
        """Explicitly replay the live composer ancestry and runtime binding."""

        snapshot = self._require_snapshot(self._snapshot())
        composer_snapshot = _COMPOSER_OWNER_SNAPSHOT(self._composer)
        _COMPOSER_LIVE_COMPONENTS(self._composer, composer_snapshot)
        self._require_snapshot(snapshot)
        if self._reference is not self._composer.reference_composer.process.reference:
            raise ValueError("live composer reference identity changed")
        _preflight_reference_resources(
            self._reference,
            strategy=self._plan.strategy,
            budget=self._plan.budget,
        )
        if (
            self._plan.strategy != "finite-atomic-enumeration"
            and _runtime_sha256() != _CACHED_RUNTIME_SHA256
        ):
            raise ValueError("live initializer runtime differs from certification")
        expected = _make_certificate(self._composer, self._plan)
        for name in self._certificate.__annotations__:
            supplied = getattr(self._certificate, name)
            wanted = getattr(expected, name)
            if name in ("composer", "composer_certificate", "reference", "plan"):
                matches = supplied is wanted
            elif type(supplied) is float and type(wanted) is float:
                matches = _same_float(supplied, wanted)
            else:
                matches = supplied == wanted
            if not matches:
                raise ValueError("live initializer certificate field %s differs" % name)
        self._require_snapshot(snapshot)
        return self._certificate

    def _evaluate(
        self,
        index: int,
        configuration: TransformedConfiguration,
    ) -> MixedSupportInitialTiltScoredConfiguration:
        evaluation = _COMPOSER_EVALUATE(
            self._composer,
            configuration,
            residual_context=self._plan.residual_context,
        )
        return _make_scored(
            index=index,
            configuration=evaluation.configuration,
            evaluation=evaluation,
            certificate=self._certificate,
        )

    def _execute_rejection(self) -> MixedSupportInitialTiltRejectionResult:
        proposal_rng = _new_philox(self._certificate.proposal_seed)
        proposal_before = _rng_state_sha256(proposal_rng.bit_generator.state)
        configurations = tuple(
            self._reference.sample_configuration(proposal_rng)
            for _ in range(self._plan.budget)
        )
        proposal_after = _rng_state_sha256(proposal_rng.bit_generator.state)

        decision_rng = _new_philox(self._certificate.rejection_decision_seed)
        decision_before = _rng_state_sha256(decision_rng.bit_generator.state)
        words = tuple(
            int(decision_rng.bit_generator.random_raw())
            for _ in range(self._plan.budget)
        )
        if any(not 0 <= word < _UINT64_DENOMINATOR for word in words):
            raise MixedSupportInitialTiltInitializerError(
                "Philox did not return a full batch of uint64 rejection words"
            )
        decision_after = _rng_state_sha256(decision_rng.bit_generator.state)

        scored = tuple(
            self._evaluate(index, configuration)
            for index, configuration in enumerate(configurations)
        )
        attempts = tuple(
            _make_attempt(record, words[index], self._certificate)
            for index, record in enumerate(scored)
        )
        selected = next((attempt for attempt in attempts if attempt.accepted), None)
        values = {
            "certificate": self._certificate,
            "certificate_sha256": self._certificate.certificate_sha256,
            "status": "selected" if selected is not None else "exhausted",
            "attempts": attempts,
            "selected_index": None if selected is None else selected.scored.index,
            "selected_configuration": (
                None if selected is None else selected.scored.configuration
            ),
            "selected_configuration_sha256": (
                None if selected is None else selected.scored.configuration_sha256
            ),
            "proposal_stream_initial_state_sha256": proposal_before,
            "proposal_stream_final_state_sha256": proposal_after,
            "decision_stream_initial_state_sha256": decision_before,
            "decision_stream_final_state_sha256": decision_after,
            "result_sha256": _ZERO_SHA256,
        }
        provisional = MixedSupportInitialTiltRejectionResult(
            **values,
            _construction_token=_REJECTION_RESULT_TOKEN,
        )
        values["result_sha256"] = _semantic_digest(
            _rejection_result_payload(provisional),
            domain=b"heterodiff-mixed-support-rejection-result-v1\x00",
        )
        return _validate_rejection_result(
            MixedSupportInitialTiltRejectionResult(
                **values,
                _construction_token=_REJECTION_RESULT_TOKEN,
            ),
            certificate=self._certificate,
        )

    def _execute_sir(self) -> MixedSupportInitialTiltSIRResult:
        proposal_rng = _new_philox(self._certificate.proposal_seed)
        proposal_before = _rng_state_sha256(proposal_rng.bit_generator.state)
        scored = tuple(
            self._evaluate(index, self._reference.sample_configuration(proposal_rng))
            for index in range(self._plan.budget)
        )
        proposal_after = _rng_state_sha256(proposal_rng.bit_generator.state)
        weights = normalize_mixed_support_sir_exact_log_weights(
            tuple(_fraction_from_evaluation(record.evaluation) for record in scored)
        )
        resampling_rng = _new_philox(self._certificate.resampling_seed)
        resampling_before = _rng_state_sha256(resampling_rng.bit_generator.state)
        word = int(resampling_rng.bit_generator.random_raw())
        if not 0 <= word < _UINT64_DENOMINATOR:
            raise MixedSupportInitialTiltInitializerError(
                "Philox did not return a uint64 resampling word"
            )
        uniform53 = word >> (
            MIXED_SUPPORT_INITIALIZER_RAW_WORD_BITS
            - MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS
        )
        selected_index = select_mixed_support_sir_index(weights, word)
        resampling_after = _rng_state_sha256(resampling_rng.bit_generator.state)
        particles = tuple(
            MixedSupportInitialTiltSIRParticle(
                scored=record,
                normalized_weight=float(weights[index]),
                particle_sha256=_particle_digest(
                    record.scored_configuration_sha256,
                    float(weights[index]),
                ),
                _construction_token=_PARTICLE_TOKEN,
            )
            for index, record in enumerate(scored)
        )
        for particle in particles:
            _validate_particle(particle, certificate=self._certificate)
        ess = 1.0 / math.fsum(float(value * value) for value in weights)
        maximum_weight = float(np.max(weights))
        selected = scored[selected_index]
        values = {
            "certificate": self._certificate,
            "certificate_sha256": self._certificate.certificate_sha256,
            "status": "selected",
            "particles": particles,
            "normalized_weights": weights,
            "effective_sample_size": ess,
            "maximum_normalized_weight": maximum_weight,
            "ess_warning": ess < (self._plan.ess_warning_fraction * self._plan.budget),
            "selected_index": selected_index,
            "selected_configuration": selected.configuration,
            "selected_configuration_sha256": selected.configuration_sha256,
            "proposal_stream_initial_state_sha256": proposal_before,
            "proposal_stream_final_state_sha256": proposal_after,
            "resampling_stream_initial_state_sha256": resampling_before,
            "resampling_stream_final_state_sha256": resampling_after,
            "resampling_word": word,
            "resampling_uniform_53": uniform53,
            "result_sha256": _ZERO_SHA256,
        }
        provisional = MixedSupportInitialTiltSIRResult(
            **values,
            _construction_token=_SIR_RESULT_TOKEN,
        )
        values["result_sha256"] = _semantic_digest(
            _sir_result_payload(provisional),
            domain=b"heterodiff-mixed-support-SIR-result-v1\x00",
        )
        return _validate_sir_result(
            MixedSupportInitialTiltSIRResult(
                **values,
                _construction_token=_SIR_RESULT_TOKEN,
            ),
            certificate=self._certificate,
        )

    def _execute_enumeration(self) -> MixedSupportInitialTiltEnumerationResult:
        if any(
            dimension != 0 for dimension in self._reference.type_dimensions.values()
        ):
            raise ValueError(
                "finite-atomic-enumeration requires every reference fiber dimension "
                "to be zero"
            )
        space, _, oracle_masses = self._reference.finite_atomic_oracle()
        scored = []
        states = []
        for index, state in enumerate(space.states):
            events = tuple(
                TransformedEvent(type_id, ())
                for type_id, count in zip(self._reference.type_ids, state)
                for _ in range(count)
            )
            configuration = self._reference.canonicalize(events)
            scored.append(self._evaluate(index, configuration))
            states.append(state)
        base_masses = _immutable_float_array(oracle_masses, name="oracle base masses")
        (
            probabilities,
            operational_log_normalizer,
        ) = normalize_mixed_support_atomic_exact_log_weights(
            base_masses,
            tuple(_fraction_from_evaluation(record.evaluation) for record in scored),
        )
        atoms = []
        for index, record in enumerate(scored):
            state = states[index]
            base_mass = float(base_masses[index])
            probability = float(probabilities[index])
            atom = MixedSupportInitialTiltEnumerationAtom(
                count_state=state,
                base_mass=base_mass,
                scored=record,
                normalized_probability=probability,
                atom_sha256=_atom_digest(
                    state,
                    base_mass,
                    record.scored_configuration_sha256,
                    probability,
                ),
                _construction_token=_ATOM_TOKEN,
            )
            atoms.append(
                _validate_atom(
                    atom,
                    certificate=self._certificate,
                    expected_type_count=len(self._reference.type_ids),
                )
            )
        values = {
            "certificate": self._certificate,
            "certificate_sha256": self._certificate.certificate_sha256,
            "status": "enumerated",
            "atoms": tuple(atoms),
            "base_masses": base_masses,
            "normalized_probabilities": probabilities,
            "operational_log_normalizer": operational_log_normalizer,
            "result_sha256": _ZERO_SHA256,
        }
        provisional = MixedSupportInitialTiltEnumerationResult(
            **values,
            _construction_token=_ENUMERATION_RESULT_TOKEN,
        )
        values["result_sha256"] = _semantic_digest(
            _enumeration_result_payload(provisional),
            domain=b"heterodiff-mixed-support-enumeration-result-v1\x00",
        )
        return _validate_enumeration_result(
            MixedSupportInitialTiltEnumerationResult(
                **values,
                _construction_token=_ENUMERATION_RESULT_TOKEN,
            ),
            certificate=self._certificate,
        )

    def execute(self) -> MixedSupportInitialTiltInitializerResult:
        """Execute exactly the sealed strategy; refusals return no result."""

        snapshot = self._require_snapshot(self._snapshot())
        self.revalidate_live_components()
        if self._plan.strategy == "bounded-rejection":
            result = self._execute_rejection()
        elif self._plan.strategy == "fixed-budget-sir":
            result = self._execute_sir()
        elif self._plan.strategy == "finite-atomic-enumeration":
            result = self._execute_enumeration()
        else:  # pragma: no cover - protected by sealed plan validation
            raise RuntimeError("sealed initializer strategy escaped validation")
        self._require_snapshot(snapshot)
        self.validate_result(result)
        return result

    def validate_result(
        self,
        result: object,
    ) -> MixedSupportInitialTiltInitializerResult:
        """Structurally validate a result without model or RNG replay."""

        snapshot = self._require_snapshot(self._snapshot())
        if type(result) is MixedSupportInitialTiltRejectionResult:
            checked = _validate_rejection_result(result, certificate=self._certificate)
        elif type(result) is MixedSupportInitialTiltSIRResult:
            checked = _validate_sir_result(result, certificate=self._certificate)
        elif type(result) is MixedSupportInitialTiltEnumerationResult:
            checked = _validate_enumeration_result(
                result, certificate=self._certificate
            )
        else:
            raise TypeError("result has no supported exact initializer-result type")
        self._require_snapshot(snapshot)
        return checked


def certify_mixed_support_initial_tilt_initializer_kernel(
    composer: _COMPOSER_TYPE,
    *,
    plan: MixedSupportInitialTiltInitializerPlan,
) -> MixedSupportInitialTiltInitializerKernel:
    """Certify one representation-level reference-interface kernel."""

    if type(composer) is not _COMPOSER_TYPE:
        raise TypeError("composer must be an exact ConfigurationInitialTiltComposer")
    checked_plan = _validate_plan(plan)
    if checked_plan.composer is not composer:
        raise ValueError("plan belongs to a different composer")
    composer_snapshot = _COMPOSER_OWNER_SNAPSHOT(composer)
    _COMPOSER_LIVE_COMPONENTS(composer, composer_snapshot)
    reference = composer.reference_composer.process.reference
    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError(
            "composer-owned reference object has the wrong capped-Poisson type"
        )
    if checked_plan.strategy == "finite-atomic-enumeration" and any(
        dimension != 0 for dimension in reference.type_dimensions.values()
    ):
        raise ValueError(
            "finite-atomic-enumeration cannot be certified for a continuous fiber"
        )
    _preflight_reference_resources(
        reference,
        strategy=checked_plan.strategy,
        budget=checked_plan.budget,
    )
    certificate = _make_certificate(composer, checked_plan)
    owner = MixedSupportInitialTiltInitializerKernel(
        composer=composer,
        reference=reference,
        plan=checked_plan,
        certificate=certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner.revalidate_live_components()
    return owner


def require_matching_mixed_support_initial_tilt_initializer_kernel(
    composer: _COMPOSER_TYPE,
    kernel: MixedSupportInitialTiltInitializerKernel,
    *,
    plan: MixedSupportInitialTiltInitializerPlan,
) -> MixedSupportInitialTiltInitializerKernel:
    """Require exact owner identities and fully revalidate live ancestry."""

    if type(kernel) is not MixedSupportInitialTiltInitializerKernel:
        raise TypeError("kernel has the wrong exact type")
    checked_plan = _validate_plan(plan)
    if kernel.composer is not composer:
        raise ValueError("kernel belongs to a different composer")
    if kernel.plan is not checked_plan:
        raise ValueError("kernel belongs to a different sealed plan")
    kernel.revalidate_live_components()
    return kernel


def validate_mixed_support_initial_tilt_initializer_kernel_certificate(
    composer: _COMPOSER_TYPE,
    kernel: MixedSupportInitialTiltInitializerKernel,
    *,
    plan: MixedSupportInitialTiltInitializerPlan,
) -> MixedSupportInitialTiltInitializerCertificate:
    """Return the fully reconstructed live kernel certificate."""

    return require_matching_mixed_support_initial_tilt_initializer_kernel(
        composer,
        kernel,
        plan=plan,
    ).certificate


__all__ = (
    "MAX_MIXED_SUPPORT_INITIALIZER_BUDGET",
    "MIXED_SUPPORT_INITIALIZER_DEFAULT_ESS_WARNING_FRACTION",
    "MIXED_SUPPORT_INITIALIZER_RAW_WORD_BITS",
    "MIXED_SUPPORT_INITIALIZER_SIR_UNIFORM_BITS",
    "MIXED_SUPPORT_INITIAL_TILT_ANALYTIC_BRIDGE",
    "MIXED_SUPPORT_INITIAL_TILT_DYADIC_REJECTION_CAVEAT",
    "MIXED_SUPPORT_INITIAL_TILT_FORMAL_TEST_28_STATUS",
    "MIXED_SUPPORT_INITIAL_TILT_IDEAL_REJECTION_THEOREM",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCHEMA_VERSION",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCOPE",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_STRATEGIES",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_TARGET_POLICY",
    "MIXED_SUPPORT_INITIAL_TILT_METRIC_BOUNDARY",
    "MIXED_SUPPORT_INITIAL_TILT_REFERENCE_OBJECT_CUSTODY_SCOPE",
    "MIXED_SUPPORT_INITIAL_TILT_RESOURCE_PREFLIGHT_POLICY",
    "MIXED_SUPPORT_INITIAL_TILT_SIR_THEOREM",
    "MixedSupportInitialTiltEnumerationAtom",
    "MixedSupportInitialTiltEnumerationResult",
    "MixedSupportInitialTiltInitializerCertificate",
    "MixedSupportInitialTiltInitializerError",
    "MixedSupportInitialTiltInitializerKernel",
    "MixedSupportInitialTiltInitializerPlan",
    "MixedSupportInitialTiltInitializerResult",
    "MixedSupportInitialTiltRejectionAttempt",
    "MixedSupportInitialTiltRejectionQuota",
    "MixedSupportInitialTiltRejectionResult",
    "MixedSupportInitialTiltSIRParticle",
    "MixedSupportInitialTiltSIRResult",
    "MixedSupportInitialTiltScoredConfiguration",
    "certify_mixed_support_initial_tilt_initializer_kernel",
    "certify_mixed_support_rejection_quota",
    "make_mixed_support_initial_tilt_initializer_plan",
    "normalize_mixed_support_atomic_exact_log_weights",
    "normalize_mixed_support_sir_exact_log_weights",
    "require_matching_mixed_support_initial_tilt_initializer_kernel",
    "select_mixed_support_sir_index",
    "validate_mixed_support_initial_tilt_initializer_certificate",
    "validate_mixed_support_initial_tilt_initializer_kernel_certificate",
)
