"""Conservative finite-resolution decisions over checkpoint-36 preparations.

Checkpoint thirty-six materializes a fixed proposal-and-score batch and keeps
one uint64 word per attempt uninterpreted.  This additive checkpoint converts
the exact rational score gap ``delta = q - U <= 0`` to the conservative quota

``K(delta) = floor(2**64 * exp(delta))``

and accepts exactly when the inherited word is smaller than ``K``.  Every
quota is certified before the first word is interpreted.  The first accepted
attempt is selected; if none is accepted, bounded exhaustion is a valid
result.  Validation or numerical ambiguity is an operational failure and
returns no result.

For nonzero rational ``delta``, ``exp(delta)`` is generally non-dyadic, so one
uniform uint64 word cannot realize an exact Bernoulli with that probability.
This module therefore certifies the finite-resolution rule, for which

``0 <= exp(delta) - K(delta) / 2**64 < 2**-64``.

The probabilistic formulas recorded here are conditional on the separate
abstract iid-uniform decision-word premise and on fixed proposal/score data.
They are not laws for the live counter-keyed Philox trace.  The live operation
is deterministic fixed-address replay.  It does not admit an initializer,
identify an analytic target, assign lineage, or construct a sampler.

Hashes and identities are process-local custody witnesses under a trusted,
unchanged runtime, not cryptographic authentication.
"""

from __future__ import annotations

from dataclasses import dataclass
import decimal
from decimal import Context, Decimal, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import json
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initial_tilt_rejection_preparation as _prep,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "counter-keyed rejection decisions require the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.theory.configuration_reference import TransformedConfiguration


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-decision-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_POLICY = (
    "exact-checkpoint36-owner-certificate-result-and-attempt-binding;"
    "all-attempt-thresholds-before-first-word-interpretation;"
    "exact-dyadic-gap-to-adaptive-directed-decimal-exp-enclosure;"
    "conservative-floor-uint64-quota;exact-half-open-word-comparison;"
    "first-accepted-prefix-selection-or-bounded-exhaustion;"
    "conditional-abstract-iid-decision-word-formulas;"
    "no-extra-words-rng-retry-fallback-or-rollback-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_ALGORITHM = (
    "delta-zero-quota-2^64;delta-at-most-minus64-quota-zero;"
    "delta-between-minus-2^-64-and-zero-quota-2^64-minus-1;"
    "otherwise-exact-dyadic-decimal-conversion;"
    "adaptive-rne-exp-and-adjacent-or-strict-unity-clamped-decimal-enclosure-"
    "192-384-768-1536-3072;"
    "nested-enclosures;unique-scaled-floor;word-strictly-less-than-quota-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCOPE = (
    "bounded-finite-resolution-initial-tilt-rejection-decision;"
    "exact-conservative-dyadic-quota-and-first-success-or-exhaustion;"
    "conditional-on-fixed-proposal-score-data-and-abstract-iid-decision-words;"
    "live-fixed-address-result-is-deterministic;"
    "not-exact-exp-bernoulli-or-ideal-rejection;"
    "not-normalized-plugin-tilt-or-analytic-conditional-target;"
    "not-live-uniformity-independence-randomness-or-one-shot-use;"
    "not-failure-probability-success-liveness-or-initializer-admission;"
    "not-lineage-tag3-brownian-drift-path-or-sampler;"
    "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
)

INITIAL_TILT_REJECTION_DECISION_DYADIC_DENOMINATOR = 1 << 64
INITIAL_TILT_REJECTION_DECISION_RAW_WORD_BITS = 64
INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION = 192
INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION = 384
INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION = 3_072
INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF = -64
INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS = 16_384
INITIAL_TILT_REJECTION_DECISION_MAX_EXACT_INTEGER_BITS = 131_072
INITIAL_TILT_REJECTION_DECISION_MAX_TEXT_LENGTH = 16_384
INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS = 64
INITIAL_TILT_REJECTION_DECISION_OUTCOMES = ("selected", "exhausted")
INITIAL_TILT_REJECTION_DECISION_CONDITIONAL_THEOREM = (
    "P(J=j|proposal-score-data)=p_j*product_{i<j}(1-p_i);"
    "P(Exhausted|proposal-score-data)=product_i(1-p_i);p_i=K_i/2^64"
)
INITIAL_TILT_REJECTION_DECISION_APPROXIMATION_THEOREM = (
    "0<=exp(delta)-K(delta)/2^64<2^-64;"
    "finite-budget-outcome-discrepancy-from-ideal-is-less-than-A/2^64"
)

_SCHEMA_VERSION = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCHEMA_VERSION
)
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_POLICY
_ALGORITHM = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_ALGORITHM
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCOPE
_D = INITIAL_TILT_REJECTION_DECISION_DYADIC_DENOMINATOR
_DECIMAL_MIN_EXPONENT = -999_999
_DECIMAL_MAX_EXPONENT = 999_999
_ZERO_SHA256 = "0" * 64

_CERTIFICATE_TOKEN = object()
_THRESHOLD_TOKEN = object()
_DECISION_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

_PREP_OWNER_TYPE = _prep.CounterKeyedInitialTiltRejectionPreparationOwner
_PREP_CERT_TYPE = _prep.CounterKeyedInitialTiltRejectionPreparationCertificate
_PREP_ATTEMPT_TYPE = _prep.CounterKeyedInitialTiltRejectionAttempt
_PREP_RESULT_TYPE = _prep.CounterKeyedInitialTiltRejectionPreparationResult
_PREP_OWNER_SNAPSHOT = _PREP_OWNER_TYPE._owner_snapshot
_PREP_REQUIRE_OWNER_SNAPSHOT = _PREP_OWNER_TYPE._require_owner_snapshot
_PREP_LIVE_CERTIFICATE = _PREP_OWNER_TYPE._live_certificate
_PREP_PREPARE = _PREP_OWNER_TYPE.prepare
_PREP_VALIDATE_RESULT = _PREP_OWNER_TYPE.validate_result
_PREP_CERTIFICATE_PROPERTY = _PREP_OWNER_TYPE.certificate
_PREP_VALIDATE_CERTIFICATE = _prep._validate_certificate
_PREP_CERTIFICATE_SNAPSHOT = _prep._preparation_certificate_operation_snapshot
_PREP_REQUIRE_CERTIFICATE_UNCHANGED = (
    _prep._require_preparation_certificate_operation_unchanged
)
_PREP_RESULT_SNAPSHOT = _prep._result_tree_snapshot
_PREP_REQUIRE_RESULT_UNCHANGED = _prep._require_result_tree_unchanged
_PREP_PREFLIGHT_RESULT_VALUES = _prep._preflight_result_values
_PREP_VALIDATE_RESULT_VALUES = _prep._validate_result_values
_CONFIGURATION_SHA256 = _prep._CP28_CONFIGURATION_SHA256


class PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(ArithmeticError):
    """Fail-closed finite-resolution rejection-decision error."""


def _require_text(value: object, expected: str, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > INITIAL_TILT_REJECTION_DECISION_MAX_TEXT_LENGTH:
        raise ValueError("%s exceeds the text resource limit" % name)
    if value != expected:
        raise ValueError("%s differs" % name)
    return value


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise TypeError("%s must be exact SHA-256 text" % name)
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("%s is not lowercase hexadecimal" % name)
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact Boolean" % name)
    if value is not expected:
        raise ValueError("%s must remain %s" % (name, expected))
    return value


def _exact_integer(
    value: object,
    *,
    name: str,
    minimum: int = 0,
    maximum: int,
) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s is outside the frozen range" % name)
    if value.bit_length() > INITIAL_TILT_REJECTION_DECISION_MAX_EXACT_INTEGER_BITS:
        raise ValueError("%s exceeds the exact-integer resource limit" % name)
    return value


def _signed_integer(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value.bit_length() > INITIAL_TILT_REJECTION_DECISION_MAX_EXACT_INTEGER_BITS:
        raise ValueError("%s exceeds the exact-integer resource limit" % name)
    return value


def _fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    checked_numerator = _signed_integer(numerator, name=name + " numerator")
    checked_denominator = _exact_integer(
        denominator,
        name=name + " denominator",
        minimum=1,
        maximum=(1 << INITIAL_TILT_REJECTION_DECISION_MAX_EXACT_INTEGER_BITS) - 1,
    )
    value = Fraction(checked_numerator, checked_denominator)
    if value.numerator != checked_numerator or value.denominator != checked_denominator:
        raise ValueError("%s must be stored in reduced form" % name)
    return value


def _exact_tuple(
    value: object,
    *,
    name: str,
    maximum: int,
    length: Optional[int] = None,
) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) > maximum:
        raise ValueError("%s exceeds the tuple resource limit" % name)
    if length is not None and len(value) != length:
        raise ValueError("%s has the wrong length" % name)
    return value


def _integer_projection(value: int) -> Tuple[str, str]:
    checked = _signed_integer(value, name="digest integer")
    return ("negative" if checked < 0 else "nonnegative", format(abs(checked), "x"))


def _typed_digest_value(value: object) -> object:
    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-hex-v1", *_integer_projection(value)]
    if type(value) is str:
        if len(value) > INITIAL_TILT_REJECTION_DECISION_MAX_TEXT_LENGTH:
            raise ValueError("digest text exceeds the resource limit")
        return ["string-v1", value]
    if type(value) is tuple:
        if len(value) > 4_096:
            raise ValueError("digest tuple exceeds the resource limit")
        return ["tuple-v1", [_typed_digest_value(item) for item in value]]
    if isinstance(value, Mapping):
        if len(value) > 512:
            raise ValueError("digest mapping exceeds the resource limit")
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("digest mappings require exact text keys")
            items.append((key, _typed_digest_value(item)))
        items.sort(key=lambda pair: pair[0])
        return ["mapping-v1", items]
    raise TypeError("unsupported digest value of type %s" % type(value).__name__)


def _semantic_digest(value: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _typed_digest_value(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-initial-tilt-rejection-decision-v1\x00")
    digest.update(encoded)
    return digest.hexdigest()


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


def _decimal_context(precision: int) -> Context:
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


def _precision_schedule() -> Tuple[int, ...]:
    values = []
    precision = INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION
    while precision < INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION:
        values.append(precision)
        precision *= 2
    values.append(INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION)
    return tuple(values)


def _nonnegative_integer_decimal_digits(
    value: int,
    *,
    name: str,
) -> Tuple[int, ...]:
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise TypeError("%s coefficient must be a nonnegative exact integer" % name)
    if value == 0:
        return (0,)
    radix = 1_000_000_000
    blocks = []
    remaining = value
    while remaining:
        remaining, block = divmod(remaining, radix)
        blocks.append(block)
    blocks.reverse()
    first_digits = []
    first = blocks[0]
    while first:
        first, digit = divmod(first, 10)
        first_digits.append(digit)
    first_digits.reverse()
    digit_count = len(first_digits) + 9 * (len(blocks) - 1)
    if digit_count > INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS:
        raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
            "%s exact decimal coefficient exceeds the work limit" % name
        )
    digits = list(first_digits)
    for block in blocks[1:]:
        divisor = 100_000_000
        while divisor:
            digit, block = divmod(block, divisor)
            digits.append(digit)
            divisor //= 10
    return tuple(digits)


def _exact_dyadic_decimal(value: Fraction, *, name: str) -> Decimal:
    denominator = value.denominator
    if denominator <= 0 or denominator & (denominator - 1):
        raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
            "%s denominator is not an exact power of two" % name
        )
    if value == 0:
        return Decimal(0)
    exponent = denominator.bit_length() - 1
    coefficient = value.numerator * (5**exponent)
    digits = _nonnegative_integer_decimal_digits(abs(coefficient), name=name)
    return Decimal((1 if coefficient < 0 else 0, digits, -exponent))


@dataclass(frozen=True)
class _QuotaData:
    branch: str
    precision: int
    ideal_lower: Fraction
    ideal_upper: Fraction
    ideal_upper_strict: bool
    quota: int


def _floor_exp_uint64_quota(delta: Fraction) -> _QuotaData:
    """Certify ``floor(2**64 * exp(delta))`` without binary64 exp."""

    if type(delta) is not Fraction:
        raise TypeError("delta must be an exact Fraction")
    _fraction_parts(delta.numerator, delta.denominator, name="delta")
    if delta.denominator & (delta.denominator - 1):
        raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
            "delta must be an exact dyadic rational"
        )
    if delta > 0:
        raise ValueError("delta must be nonpositive")
    if delta == 0:
        return _QuotaData("unity", 0, Fraction(1), Fraction(1), False, _D)
    if delta <= INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF:
        return _QuotaData(
            "below_uint64_resolution",
            0,
            Fraction(0),
            Fraction(1, _D),
            True,
            0,
        )
    if delta > Fraction(-1, _D):
        return _QuotaData(
            "below_one_uint64_cell",
            0,
            Fraction(_D - 1, _D),
            Fraction(1),
            True,
            _D - 1,
        )

    exact_decimal = _exact_dyadic_decimal(delta, name="decision log gap")
    previous: Optional[Tuple[Fraction, Fraction]] = None
    for precision in _precision_schedule():
        context = _decimal_context(precision)
        try:
            rounded = context.exp(exact_decimal)
            lower_decimal = context.next_minus(rounded)
            upper_decimal = context.next_plus(rounded)
        except decimal.DecimalException as error:
            raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
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
            raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
                "Decimal exponential enclosure is invalid"
            )
        lower = Fraction(lower_decimal)
        upper = Fraction(upper_decimal)
        _fraction_parts(lower.numerator, lower.denominator, name="exp lower")
        _fraction_parts(upper.numerator, upper.denominator, name="exp upper")
        if previous is not None and not (previous[0] <= lower <= upper <= previous[1]):
            raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
                "adaptive Decimal exponential enclosures are not nested"
            )
        previous = (lower, upper)
        scaled_lower = _D * lower
        scaled_upper = _D * upper
        quota = scaled_lower.numerator // scaled_lower.denominator
        upper_is_strict = True
        if quota <= scaled_lower and (
            scaled_upper < quota + 1 or (upper_is_strict and scaled_upper == quota + 1)
        ):
            if not 0 <= quota < _D:
                raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
                    "certified nonunity quota escaped the uint64 domain"
                )
            return _QuotaData(
                "adaptive_decimal",
                precision,
                lower,
                upper,
                upper_is_strict,
                quota,
            )
    raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
        "finite-resolution rejection quota is precision-ambiguous"
    )


def _runtime_sha256() -> str:
    expected = {
        "denominator": 1 << 64,
        "raw_word_bits": 64,
        "primary_precision": 192,
        "audit_precision": 384,
        "maximum_precision": 3_072,
        "zero_quota_cutoff": -64,
        "maximum_attempts": 64,
        "maximum_decimal_coefficient_digits": 16_384,
    }
    actual = {
        "denominator": INITIAL_TILT_REJECTION_DECISION_DYADIC_DENOMINATOR,
        "raw_word_bits": INITIAL_TILT_REJECTION_DECISION_RAW_WORD_BITS,
        "primary_precision": INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION,
        "audit_precision": INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION,
        "maximum_precision": INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION,
        "zero_quota_cutoff": (INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF),
        "maximum_attempts": INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS,
        "maximum_decimal_coefficient_digits": (
            INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS
        ),
    }
    if actual != expected:
        raise ValueError("rejection-decision constants changed")
    if _prep.INITIAL_TILT_REJECTION_RESERVED_WORDS_PER_ATTEMPT != 1:
        raise ValueError("checkpoint-36 reserved-word layout changed")
    return _semantic_digest(
        {
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "algorithm": _ALGORITHM,
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "decimal_version": getattr(decimal, "__version__", "unknown"),
            "libmpdec_version": getattr(decimal, "__libmpdec_version__", "unknown"),
            "constants": tuple(sorted(actual.items())),
            "precision_schedule": _precision_schedule(),
            "decimal_min_exponent": _DECIMAL_MIN_EXPONENT,
            "decimal_max_exponent": _DECIMAL_MAX_EXPONENT,
        }
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "preparation_certificate", "certificate_sha256")


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionDecisionCertificate:
    """Sealed conservative-quota and first-success decision certificate."""

    schema_version: str
    certificate_scope: str
    decision_policy: str
    decision_algorithm: str
    decision_role_sha256: str
    preparation_certificate: _PREP_CERT_TYPE
    preparation_certificate_sha256: str
    preparation_runtime_sha256: str
    preparation_owner_runtime_identity: int
    process_parameter_sha256: str
    attempt_budget: int
    dyadic_denominator: int
    raw_word_bits: int
    decimal_primary_precision: int
    decimal_audit_precision: int
    decimal_max_precision: int
    maximum_decimal_coefficient_digits: int
    zero_quota_log_cutoff: int
    conditional_theorem: str
    approximation_theorem: str
    decision_runtime_sha256: str
    exact_checkpoint36_owner_binding_certified: bool
    all_thresholds_before_decisions_certified: bool
    conservative_floor_quota_certified: bool
    adaptive_directed_exp_enclosure_certified: bool
    exact_half_open_comparison_certified: bool
    first_success_or_exhaustion_certified: bool
    conditional_abstract_iid_decision_law_certified: bool
    deterministic_replay_certified: bool
    no_new_words_or_caller_rng_certified: bool
    exact_ideal_exponential_bernoulli_certified: bool
    exact_ideal_rejection_law_certified: bool
    successful_record_conditional_law_certified: bool
    failure_probability_certified: bool
    live_uniformity_certified: bool
    live_independence_certified: bool
    physical_randomness_certified: bool
    global_address_one_shot_use_certified: bool
    normalized_tilted_initializer_certified: bool
    analytic_target_certified: bool
    initializer_admissible: bool
    lineage_certified: bool
    tag3_payload_coordination_certified: bool
    brownian_stream_consumption_certified: bool
    continuous_drift_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    test28_closed: bool
    result_promotion_admissible: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection-decision certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("rejection-decision certificates are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("rejection-decision certificate fields are incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection-decision certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionDecisionCertificate.__annotations__)


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint36_owner_binding_certified",
    "all_thresholds_before_decisions_certified",
    "conservative_floor_quota_certified",
    "adaptive_directed_exp_enclosure_certified",
    "exact_half_open_comparison_certified",
    "first_success_or_exhaustion_certified",
    "conditional_abstract_iid_decision_law_certified",
    "deterministic_replay_certified",
    "no_new_words_or_caller_rng_certified",
    "passed",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "exact_ideal_exponential_bernoulli_certified",
    "exact_ideal_rejection_law_certified",
    "successful_record_conditional_law_certified",
    "failure_probability_certified",
    "live_uniformity_certified",
    "live_independence_certified",
    "physical_randomness_certified",
    "global_address_one_shot_use_certified",
    "normalized_tilted_initializer_certified",
    "analytic_target_certified",
    "initializer_admissible",
    "lineage_certified",
    "tag3_payload_coordination_certified",
    "brownian_stream_consumption_certified",
    "continuous_drift_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
    "test28_closed",
    "result_promotion_admissible",
    "runtime_portable",
    "cryptographic_authentication",
)


def _validate_preparation_certificate(
    certificate: object,
) -> _PREP_CERT_TYPE:
    if type(certificate) is not _PREP_CERT_TYPE:
        raise TypeError("preparation certificate has the wrong exact CP36 type")
    snapshot = _PREP_CERTIFICATE_SNAPSHOT(certificate)
    checked = _PREP_VALIDATE_CERTIFICATE(certificate)
    _PREP_REQUIRE_CERTIFICATE_UNCHANGED(certificate, snapshot)
    if checked is not certificate:
        raise ValueError("CP36 validation substituted its certificate")
    return certificate


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    expected_text = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "decision_policy": _POLICY,
        "decision_algorithm": _ALGORITHM,
        "conditional_theorem": (INITIAL_TILT_REJECTION_DECISION_CONDITIONAL_THEOREM),
        "approximation_theorem": (
            INITIAL_TILT_REJECTION_DECISION_APPROXIMATION_THEOREM
        ),
    }
    for name, expected in expected_text.items():
        _require_text(values[name], expected, name="certificate.%s" % name)
    for name in (
        "decision_role_sha256",
        "preparation_certificate_sha256",
        "preparation_runtime_sha256",
        "process_parameter_sha256",
        "decision_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate.%s" % name)
    parent = _validate_preparation_certificate(values["preparation_certificate"])
    expected_scalars = {
        "preparation_certificate_sha256": parent.certificate_sha256,
        "preparation_runtime_sha256": parent.preparation_runtime_sha256,
        "process_parameter_sha256": parent.process_parameter_sha256,
        "attempt_budget": parent.attempt_budget,
        "dyadic_denominator": _D,
        "raw_word_bits": INITIAL_TILT_REJECTION_DECISION_RAW_WORD_BITS,
        "decimal_primary_precision": (
            INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION
        ),
        "decimal_audit_precision": INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION,
        "decimal_max_precision": INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION,
        "maximum_decimal_coefficient_digits": (
            INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS
        ),
        "zero_quota_log_cutoff": (
            INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF
        ),
        "decision_runtime_sha256": _runtime_sha256(),
    }
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("certificate.%s differs" % name)
    _exact_integer(
        values["preparation_owner_runtime_identity"],
        name="certificate.preparation_owner_runtime_identity",
        minimum=1,
        maximum=(1 << 64) - 1,
    )
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate.%s" % name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate.%s" % name)
    expected_digest = _semantic_digest(_certificate_payload(values))
    if values["certificate_sha256"] != expected_digest:
        raise ValueError("rejection-decision certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionDecisionCertificate:
    if type(certificate) is not CounterKeyedInitialTiltRejectionDecisionCertificate:
        raise TypeError("certificate has the wrong exact rejection-decision type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    preparation_owner: _PREP_OWNER_TYPE,
    decision_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionDecisionCertificate:
    parent = _PREP_CERTIFICATE_PROPERTY.__get__(preparation_owner, _PREP_OWNER_TYPE)
    _validate_preparation_certificate(parent)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "decision_policy": _POLICY,
        "decision_algorithm": _ALGORITHM,
        "decision_role_sha256": decision_role_sha256,
        "preparation_certificate": parent,
        "preparation_certificate_sha256": parent.certificate_sha256,
        "preparation_runtime_sha256": parent.preparation_runtime_sha256,
        "preparation_owner_runtime_identity": id(preparation_owner),
        "process_parameter_sha256": parent.process_parameter_sha256,
        "attempt_budget": parent.attempt_budget,
        "dyadic_denominator": _D,
        "raw_word_bits": INITIAL_TILT_REJECTION_DECISION_RAW_WORD_BITS,
        "decimal_primary_precision": (
            INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION
        ),
        "decimal_audit_precision": INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION,
        "decimal_max_precision": INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION,
        "maximum_decimal_coefficient_digits": (
            INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS
        ),
        "zero_quota_log_cutoff": (
            INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF
        ),
        "conditional_theorem": (INITIAL_TILT_REJECTION_DECISION_CONDITIONAL_THEOREM),
        "approximation_theorem": (
            INITIAL_TILT_REJECTION_DECISION_APPROXIMATION_THEOREM
        ),
        "decision_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_POSITIVE_FLAGS},
        **{name: False for name in _CERTIFICATE_NEGATIVE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionDecisionCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


def _threshold_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "preparation_attempt",
        "threshold_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionThreshold:
    """One threshold certified without interpreting its decision word."""

    certificate: CounterKeyedInitialTiltRejectionDecisionCertificate
    certificate_sha256: str
    preparation_attempt: _PREP_ATTEMPT_TYPE
    preparation_attempt_sha256: str
    attempt_index: int
    delta_numerator: int
    delta_denominator: int
    threshold_branch: str
    decimal_precision_used: int
    ideal_probability_lower_numerator: int
    ideal_probability_lower_denominator: int
    ideal_probability_upper_numerator: int
    ideal_probability_upper_denominator: int
    ideal_probability_upper_strict: bool
    acceptance_quota: int
    quota_probability_numerator: int
    quota_probability_denominator: int
    ideal_minus_quota_error_strict_upper_numerator: int
    ideal_minus_quota_error_strict_upper_denominator: int
    quota_certified_before_word_interpretation: bool
    exact_ideal_probability_materialized: bool
    threshold_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection thresholds cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _THRESHOLD_TOKEN:
            raise TypeError("rejection thresholds are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("rejection threshold fields are incomplete")
        _validate_threshold_values(
            values,
            trusted_certificate=values["certificate"],
        )
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection thresholds are not pickle objects")


def _threshold_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionThreshold.__annotations__)


def _preflight_preparation_attempt(attempt: object, *, name: str) -> None:
    if type(attempt) is not _PREP_ATTEMPT_TYPE:
        raise TypeError("%s has the wrong exact CP36 attempt type" % name)
    _require_sha256(attempt.attempt_sha256, name=name + ".attempt_sha256")
    _exact_integer(
        attempt.attempt_index,
        name=name + ".attempt_index",
        maximum=INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS - 1,
    )
    _fraction_parts(
        attempt.q_minus_upper_bound_numerator,
        attempt.q_minus_upper_bound_denominator,
        name=name + ".q_minus_upper_bound",
    )
    _exact_bool(
        attempt.q_minus_upper_bound_nonpositive,
        True,
        name=name + ".q_minus_upper_bound_nonpositive",
    )
    _exact_integer(
        attempt.reserved_decision_raw64_word,
        name=name + ".reserved_decision_raw64_word",
        maximum=_D - 1,
    )


def _validate_threshold_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: object | None = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if type(trusted_certificate) is not (
            CounterKeyedInitialTiltRejectionDecisionCertificate
        ):
            raise TypeError("trusted threshold certificate has the wrong exact type")
        if values["certificate"] is not trusted_certificate:
            raise ValueError("threshold trusted certificate identity differs")
        certificate = trusted_certificate
    _require_sha256(
        values["certificate_sha256"],
        name="threshold.certificate_sha256",
    )
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("threshold certificate digest differs")
    attempt = values["preparation_attempt"]
    _preflight_preparation_attempt(attempt, name="threshold.preparation_attempt")
    if attempt.certificate is not certificate.preparation_certificate:
        raise ValueError("threshold attempt belongs to another CP36 certificate")
    _require_sha256(
        values["preparation_attempt_sha256"],
        name="threshold.preparation_attempt_sha256",
    )
    if values["preparation_attempt_sha256"] != attempt.attempt_sha256:
        raise ValueError("threshold parent-attempt digest differs")
    attempt_index = _exact_integer(
        values["attempt_index"],
        name="threshold.attempt_index",
        maximum=INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS - 1,
    )
    if attempt_index != attempt.attempt_index:
        raise ValueError("threshold attempt index differs")
    delta = _fraction_parts(
        values["delta_numerator"],
        values["delta_denominator"],
        name="threshold.delta",
    )
    expected_delta = Fraction(
        attempt.q_minus_upper_bound_numerator,
        attempt.q_minus_upper_bound_denominator,
    )
    if delta != expected_delta or delta > 0:
        raise ValueError("threshold delta differs from CP36")
    branch = values["threshold_branch"]
    if type(branch) is not str:
        raise TypeError("threshold branch must be exact text")
    if branch not in (
        "unity",
        "below_uint64_resolution",
        "below_one_uint64_cell",
        "adaptive_decimal",
    ):
        raise ValueError("threshold branch is unknown")
    precision = _exact_integer(
        values["decimal_precision_used"],
        name="threshold.decimal_precision_used",
        maximum=INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION,
    )
    lower = _fraction_parts(
        values["ideal_probability_lower_numerator"],
        values["ideal_probability_lower_denominator"],
        name="threshold.ideal_probability_lower",
    )
    upper = _fraction_parts(
        values["ideal_probability_upper_numerator"],
        values["ideal_probability_upper_denominator"],
        name="threshold.ideal_probability_upper",
    )
    if not Fraction(0) <= lower <= upper <= Fraction(1):
        raise ValueError("threshold ideal-probability enclosure is invalid")
    upper_strict = values["ideal_probability_upper_strict"]
    if type(upper_strict) is not bool:
        raise TypeError("threshold upper-strict flag must be exact Boolean")
    quota = _exact_integer(
        values["acceptance_quota"],
        name="threshold.acceptance_quota",
        maximum=_D,
    )
    quota_probability = _fraction_parts(
        values["quota_probability_numerator"],
        values["quota_probability_denominator"],
        name="threshold.quota_probability",
    )
    if quota_probability != Fraction(quota, _D):
        raise ValueError("threshold quota probability differs")
    error_limit = _fraction_parts(
        values["ideal_minus_quota_error_strict_upper_numerator"],
        values["ideal_minus_quota_error_strict_upper_denominator"],
        name="threshold.error_limit",
    )
    if error_limit != Fraction(1, _D):
        raise ValueError("threshold strict error limit differs")
    expected = _floor_exp_uint64_quota(delta)
    if (
        branch != expected.branch
        or precision != expected.precision
        or lower != expected.ideal_lower
        or upper != expected.ideal_upper
        or upper_strict is not expected.ideal_upper_strict
        or quota != expected.quota
    ):
        raise ValueError("threshold arithmetic replay differs")
    _exact_bool(
        values["quota_certified_before_word_interpretation"],
        True,
        name="threshold.quota_certified_before_word_interpretation",
    )
    _exact_bool(
        values["exact_ideal_probability_materialized"],
        False,
        name="threshold.exact_ideal_probability_materialized",
    )
    _require_sha256(values["threshold_sha256"], name="threshold.threshold_sha256")
    if values["threshold_sha256"] != _semantic_digest(_threshold_payload(values)):
        raise ValueError("threshold digest differs")


def _make_threshold(
    certificate: CounterKeyedInitialTiltRejectionDecisionCertificate,
    attempt: _PREP_ATTEMPT_TYPE,
) -> CounterKeyedInitialTiltRejectionThreshold:
    _preflight_preparation_attempt(attempt, name="preparation attempt")
    delta = Fraction(
        attempt.q_minus_upper_bound_numerator,
        attempt.q_minus_upper_bound_denominator,
    )
    data = _floor_exp_uint64_quota(delta)
    probability = Fraction(data.quota, _D)
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "preparation_attempt": attempt,
        "preparation_attempt_sha256": attempt.attempt_sha256,
        "attempt_index": attempt.attempt_index,
        "delta_numerator": delta.numerator,
        "delta_denominator": delta.denominator,
        "threshold_branch": data.branch,
        "decimal_precision_used": data.precision,
        "ideal_probability_lower_numerator": data.ideal_lower.numerator,
        "ideal_probability_lower_denominator": data.ideal_lower.denominator,
        "ideal_probability_upper_numerator": data.ideal_upper.numerator,
        "ideal_probability_upper_denominator": data.ideal_upper.denominator,
        "ideal_probability_upper_strict": data.ideal_upper_strict,
        "acceptance_quota": data.quota,
        "quota_probability_numerator": probability.numerator,
        "quota_probability_denominator": probability.denominator,
        "ideal_minus_quota_error_strict_upper_numerator": 1,
        "ideal_minus_quota_error_strict_upper_denominator": _D,
        "quota_certified_before_word_interpretation": True,
        "exact_ideal_probability_materialized": False,
        "threshold_sha256": _ZERO_SHA256,
    }
    values["threshold_sha256"] = _semantic_digest(_threshold_payload(values))
    return CounterKeyedInitialTiltRejectionThreshold(
        _construction_token=_THRESHOLD_TOKEN,
        **values,
    )


def _decision_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "threshold",
        "preparation_attempt",
        "decision_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionAttemptDecision:
    """One exact half-open comparison for an interpreted prefix attempt."""

    certificate: CounterKeyedInitialTiltRejectionDecisionCertificate
    certificate_sha256: str
    threshold: CounterKeyedInitialTiltRejectionThreshold
    threshold_sha256: str
    preparation_attempt: _PREP_ATTEMPT_TYPE
    preparation_attempt_sha256: str
    attempt_index: int
    decision_word: int
    acceptance_quota: int
    word_below_quota: bool
    accepted: bool
    inherited_reserved_word_interpreted: bool
    exact_half_open_comparison: bool
    extra_word_consumed: bool
    ideal_exponential_bernoulli_claimed: bool
    decision_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection attempt decisions cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _DECISION_TOKEN:
            raise TypeError("rejection attempt decisions are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("rejection attempt decision fields are incomplete")
        _validate_decision_values(
            values,
            trusted_certificate=values["certificate"],
            trusted_threshold=values["threshold"],
        )
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection attempt decisions are not pickle objects")


def _decision_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionAttemptDecision.__annotations__)


def _validate_decision_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: object | None = None,
    trusted_threshold: object | None = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if type(trusted_certificate) is not (
            CounterKeyedInitialTiltRejectionDecisionCertificate
        ):
            raise TypeError("trusted decision certificate has the wrong exact type")
        if values["certificate"] is not trusted_certificate:
            raise ValueError("decision trusted certificate identity differs")
        certificate = trusted_certificate
    _require_sha256(
        values["certificate_sha256"],
        name="decision.certificate_sha256",
    )
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("attempt decision certificate digest differs")
    threshold = values["threshold"]
    if type(threshold) is not CounterKeyedInitialTiltRejectionThreshold:
        raise TypeError("attempt decision threshold has the wrong exact type")
    if trusted_threshold is None:
        _validate_threshold_values(
            {name: getattr(threshold, name) for name in _threshold_fields()},
            trusted_certificate=certificate,
        )
    elif threshold is not trusted_threshold:
        raise ValueError("decision trusted threshold identity differs")
    if threshold.certificate is not certificate:
        raise ValueError("attempt decision threshold belongs elsewhere")
    _require_sha256(
        values["threshold_sha256"],
        name="decision.threshold_sha256",
    )
    if values["threshold_sha256"] != threshold.threshold_sha256:
        raise ValueError("attempt decision threshold digest differs")
    attempt = values["preparation_attempt"]
    _preflight_preparation_attempt(attempt, name="decision.preparation_attempt")
    if attempt is not threshold.preparation_attempt:
        raise ValueError("attempt decision parent identity differs")
    _require_sha256(
        values["preparation_attempt_sha256"],
        name="decision.preparation_attempt_sha256",
    )
    if values["preparation_attempt_sha256"] != attempt.attempt_sha256:
        raise ValueError("attempt decision parent digest differs")
    attempt_index = _exact_integer(
        values["attempt_index"],
        name="decision.attempt_index",
        maximum=INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS - 1,
    )
    if attempt_index != attempt.attempt_index:
        raise ValueError("attempt decision index differs")
    word = _exact_integer(
        values["decision_word"],
        name="attempt decision word",
        maximum=_D - 1,
    )
    if word != attempt.reserved_decision_raw64_word:
        raise ValueError("attempt decision word differs from CP36")
    quota = _exact_integer(
        values["acceptance_quota"],
        name="attempt decision quota",
        maximum=_D,
    )
    if quota != threshold.acceptance_quota:
        raise ValueError("attempt decision quota differs")
    expected = word < quota
    _exact_bool(
        values["word_below_quota"],
        expected,
        name="attempt decision word_below_quota",
    )
    _exact_bool(values["accepted"], expected, name="attempt decision accepted")
    for name, expected_flag in (
        ("inherited_reserved_word_interpreted", True),
        ("exact_half_open_comparison", True),
        ("extra_word_consumed", False),
        ("ideal_exponential_bernoulli_claimed", False),
    ):
        _exact_bool(
            values[name],
            expected_flag,
            name="attempt decision %s" % name,
        )
    _require_sha256(values["decision_sha256"], name="decision.decision_sha256")
    if values["decision_sha256"] != _semantic_digest(_decision_payload(values)):
        raise ValueError("attempt decision digest differs")


def _make_decision(
    threshold: CounterKeyedInitialTiltRejectionThreshold,
) -> CounterKeyedInitialTiltRejectionAttemptDecision:
    attempt = threshold.preparation_attempt
    word = attempt.reserved_decision_raw64_word
    accepted = word < threshold.acceptance_quota
    values: Dict[str, object] = {
        "certificate": threshold.certificate,
        "certificate_sha256": threshold.certificate_sha256,
        "threshold": threshold,
        "threshold_sha256": threshold.threshold_sha256,
        "preparation_attempt": attempt,
        "preparation_attempt_sha256": attempt.attempt_sha256,
        "attempt_index": attempt.attempt_index,
        "decision_word": word,
        "acceptance_quota": threshold.acceptance_quota,
        "word_below_quota": accepted,
        "accepted": accepted,
        "inherited_reserved_word_interpreted": True,
        "exact_half_open_comparison": True,
        "extra_word_consumed": False,
        "ideal_exponential_bernoulli_claimed": False,
        "decision_sha256": _ZERO_SHA256,
    }
    values["decision_sha256"] = _semantic_digest(_decision_payload(values))
    return CounterKeyedInitialTiltRejectionAttemptDecision(
        _construction_token=_DECISION_TOKEN,
        **values,
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "preparation_result",
        "thresholds",
        "decisions",
        "selected_preparation_attempt",
        "selected_configuration",
        "result_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionDecisionResult:
    """First finite-resolution success or valid bounded exhaustion."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionDecisionCertificate
    certificate_sha256: str
    preparation_result: _PREP_RESULT_TYPE
    preparation_result_sha256: str
    run_id: int
    initialization_index: int
    attempt_budget: int
    thresholds: Tuple[CounterKeyedInitialTiltRejectionThreshold, ...]
    threshold_sha256s: Tuple[str, ...]
    decisions: Tuple[CounterKeyedInitialTiltRejectionAttemptDecision, ...]
    decision_sha256s: Tuple[str, ...]
    evaluated_attempt_count: int
    outcome: str
    selected_attempt_index: Optional[int]
    selected_preparation_attempt: Optional[_PREP_ATTEMPT_TYPE]
    selected_preparation_attempt_sha256: Optional[str]
    selected_configuration: Optional[TransformedConfiguration]
    selected_configuration_sha256: Optional[str]
    succeeded: bool
    budget_exhausted: bool
    all_thresholds_certified_before_first_decision: bool
    prior_attempts_rejected: bool
    selected_attempt_is_first_accepted: bool
    suffix_decision_words_uninterpreted: bool
    complete_preparation_prefix_retained: bool
    conditional_outcome_probability_numerator: int
    conditional_outcome_probability_denominator: int
    operational_failure_returned_as_exhaustion: bool
    retry_fallback_or_rollback_claimed: bool
    initializer_output_admitted: bool
    deterministic_fixed_address_replay_only: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection-decision results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("rejection-decision results are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("rejection-decision result fields are incomplete")
        _validate_result_values(values, trusted_construction=True)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection-decision results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionDecisionResult.__annotations__)


def _preflight_preparation_result(
    result: object,
    *,
    certificate: CounterKeyedInitialTiltRejectionDecisionCertificate,
) -> _PREP_RESULT_TYPE:
    if type(result) is not _PREP_RESULT_TYPE:
        raise TypeError("preparation result has the wrong exact CP36 type")
    _PREP_PREFLIGHT_RESULT_VALUES(
        {name: getattr(result, name) for name in _prep._result_fields()}
    )
    if result.certificate is not certificate.preparation_certificate:
        raise ValueError("preparation result belongs to another CP36 certificate")
    return result


def _conditional_probability(
    thresholds: Tuple[CounterKeyedInitialTiltRejectionThreshold, ...],
    selected_index: Optional[int],
) -> Fraction:
    probability = Fraction(1)
    stop = len(thresholds) if selected_index is None else selected_index
    for threshold in thresholds[:stop]:
        probability *= Fraction(_D - threshold.acceptance_quota, _D)
    if selected_index is not None:
        probability *= Fraction(thresholds[selected_index].acceptance_quota, _D)
    return probability


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_construction: bool = False,
) -> None:
    if type(trusted_construction) is not bool:
        raise TypeError("trusted_construction must be an exact Boolean")
    if trusted_construction:
        certificate = values["certificate"]
        if type(certificate) is not (
            CounterKeyedInitialTiltRejectionDecisionCertificate
        ):
            raise TypeError("result certificate has the wrong exact type")
    else:
        certificate = _validate_certificate(values["certificate"])
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="result.schema")
    _require_sha256(values["certificate_sha256"], name="result.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    parent = _preflight_preparation_result(
        values["preparation_result"],
        certificate=certificate,
    )
    _require_sha256(
        values["preparation_result_sha256"],
        name="result.preparation_result_sha256",
    )
    if values["preparation_result_sha256"] != parent.result_sha256:
        raise ValueError("result CP36 digest differs")
    expected_scalars = {
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "attempt_budget": parent.attempt_budget,
    }
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("result.%s differs" % name)
    thresholds = _exact_tuple(
        values["thresholds"],
        name="result.thresholds",
        maximum=INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS,
        length=parent.attempt_budget,
    )
    for position, threshold in enumerate(thresholds):
        if type(threshold) is not CounterKeyedInitialTiltRejectionThreshold:
            raise TypeError("result threshold %d has the wrong exact type" % position)
        _validate_threshold_values(
            {name: getattr(threshold, name) for name in _threshold_fields()},
            trusted_certificate=certificate,
        )
        if threshold.certificate is not certificate:
            raise ValueError("result threshold %d belongs elsewhere" % position)
        if threshold.preparation_attempt is not parent.attempts[position]:
            raise ValueError("result threshold %d parent identity differs" % position)
        if threshold.attempt_index != position:
            raise ValueError("result threshold order differs")
    threshold_sha256s = _exact_tuple(
        values["threshold_sha256s"],
        name="result.threshold_sha256s",
        maximum=INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS,
        length=parent.attempt_budget,
    )
    for position, digest in enumerate(threshold_sha256s):
        _require_sha256(digest, name="result.threshold_sha256s[%d]" % position)
    if threshold_sha256s != tuple(item.threshold_sha256 for item in thresholds):
        raise ValueError("result threshold digest sequence differs")
    decisions = _exact_tuple(
        values["decisions"],
        name="result.decisions",
        maximum=parent.attempt_budget,
    )
    if not decisions:
        raise ValueError("result must interpret at least one decision word")
    for position, decision in enumerate(decisions):
        if type(decision) is not CounterKeyedInitialTiltRejectionAttemptDecision:
            raise TypeError("result decision %d has the wrong exact type" % position)
        _validate_decision_values(
            {name: getattr(decision, name) for name in _decision_fields()},
            trusted_certificate=certificate,
            trusted_threshold=thresholds[position],
        )
        if decision.threshold is not thresholds[position]:
            raise ValueError("result decision %d threshold identity differs" % position)
        if decision.attempt_index != position:
            raise ValueError("result decision order differs")
    decision_sha256s = _exact_tuple(
        values["decision_sha256s"],
        name="result.decision_sha256s",
        maximum=parent.attempt_budget,
        length=len(decisions),
    )
    for position, digest in enumerate(decision_sha256s):
        _require_sha256(digest, name="result.decision_sha256s[%d]" % position)
    if decision_sha256s != tuple(item.decision_sha256 for item in decisions):
        raise ValueError("result decision digest sequence differs")
    evaluated_count = _exact_integer(
        values["evaluated_attempt_count"],
        name="result.evaluated_attempt_count",
        minimum=1,
        maximum=parent.attempt_budget,
    )
    if evaluated_count != len(decisions):
        raise ValueError("result evaluated-attempt count differs")
    accepted_positions = [
        position for position, decision in enumerate(decisions) if decision.accepted
    ]
    outcome = values["outcome"]
    if type(outcome) is not str:
        raise TypeError("result outcome must be exact text")
    if outcome not in INITIAL_TILT_REJECTION_DECISION_OUTCOMES:
        raise ValueError("result outcome is unknown")
    if outcome == "selected":
        if accepted_positions != [len(decisions) - 1]:
            raise ValueError("selected result must end at its first accepted decision")
        selected_index = len(decisions) - 1
        checked_selected_index = _exact_integer(
            values["selected_attempt_index"],
            name="result.selected_attempt_index",
            maximum=parent.attempt_budget - 1,
        )
        if checked_selected_index != selected_index:
            raise ValueError("selected result index differs")
        selected_attempt = parent.attempts[selected_index]
        if type(values["selected_preparation_attempt"]) is not _PREP_ATTEMPT_TYPE:
            raise TypeError("selected parent attempt has the wrong exact CP36 type")
        if values["selected_preparation_attempt"] is not selected_attempt:
            raise ValueError("selected parent-attempt identity differs")
        _require_sha256(
            values["selected_preparation_attempt_sha256"],
            name="result.selected_preparation_attempt_sha256",
        )
        if values["selected_preparation_attempt_sha256"] != (
            selected_attempt.attempt_sha256
        ):
            raise ValueError("selected parent-attempt digest differs")
        selected_configuration = selected_attempt.canonical_configuration
        if type(values["selected_configuration"]) is not tuple:
            raise TypeError("selected configuration must be an exact tuple")
        if values["selected_configuration"] is not selected_configuration:
            raise ValueError("selected configuration identity differs")
        _require_sha256(
            values["selected_configuration_sha256"],
            name="result.selected_configuration_sha256",
        )
        if values["selected_configuration_sha256"] != (
            selected_attempt.canonical_configuration_sha256
        ):
            raise ValueError("selected configuration digest differs")
        if len(decisions) >= parent.attempt_budget:
            expected_suffix = False
        else:
            expected_suffix = True
        expected_flags = {
            "succeeded": True,
            "budget_exhausted": False,
            "selected_attempt_is_first_accepted": True,
            "suffix_decision_words_uninterpreted": expected_suffix,
        }
    else:
        if accepted_positions or len(decisions) != parent.attempt_budget:
            raise ValueError("exhaustion requires every attempt to reject")
        selected_index = None
        for name in (
            "selected_attempt_index",
            "selected_preparation_attempt",
            "selected_preparation_attempt_sha256",
            "selected_configuration",
            "selected_configuration_sha256",
        ):
            if values[name] is not None:
                raise ValueError("exhausted result %s must be absent" % name)
        expected_flags = {
            "succeeded": False,
            "budget_exhausted": True,
            "selected_attempt_is_first_accepted": False,
            "suffix_decision_words_uninterpreted": False,
        }
    for name, expected in expected_flags.items():
        _exact_bool(values[name], expected, name="result.%s" % name)
    for name, expected in (
        ("all_thresholds_certified_before_first_decision", True),
        ("prior_attempts_rejected", True),
        ("complete_preparation_prefix_retained", True),
        ("operational_failure_returned_as_exhaustion", False),
        ("retry_fallback_or_rollback_claimed", False),
        ("initializer_output_admitted", False),
        ("deterministic_fixed_address_replay_only", True),
    ):
        _exact_bool(values[name], expected, name="result.%s" % name)
    probability = _fraction_parts(
        values["conditional_outcome_probability_numerator"],
        values["conditional_outcome_probability_denominator"],
        name="result.conditional_outcome_probability",
    )
    if probability != _conditional_probability(thresholds, selected_index):
        raise ValueError("result conditional outcome probability differs")
    _require_sha256(values["result_sha256"], name="result.result_sha256")
    if values["result_sha256"] != _semantic_digest(_result_payload(values)):
        raise ValueError("rejection-decision result digest differs")


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionDecisionCertificate,
    parent: _PREP_RESULT_TYPE,
    thresholds: Tuple[CounterKeyedInitialTiltRejectionThreshold, ...],
    decisions: Tuple[CounterKeyedInitialTiltRejectionAttemptDecision, ...],
) -> CounterKeyedInitialTiltRejectionDecisionResult:
    selected_index: Optional[int]
    if decisions[-1].accepted:
        outcome = "selected"
        selected_index = len(decisions) - 1
        selected_attempt = parent.attempts[selected_index]
        selected_configuration = selected_attempt.canonical_configuration
        succeeded = True
        exhausted = False
        first = True
        suffix_uninterpreted = len(decisions) < parent.attempt_budget
    else:
        outcome = "exhausted"
        selected_index = None
        selected_attempt = None
        selected_configuration = None
        succeeded = False
        exhausted = True
        first = False
        suffix_uninterpreted = False
    probability = _conditional_probability(thresholds, selected_index)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "preparation_result": parent,
        "preparation_result_sha256": parent.result_sha256,
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "attempt_budget": parent.attempt_budget,
        "thresholds": thresholds,
        "threshold_sha256s": tuple(item.threshold_sha256 for item in thresholds),
        "decisions": decisions,
        "decision_sha256s": tuple(item.decision_sha256 for item in decisions),
        "evaluated_attempt_count": len(decisions),
        "outcome": outcome,
        "selected_attempt_index": selected_index,
        "selected_preparation_attempt": selected_attempt,
        "selected_preparation_attempt_sha256": (
            None if selected_attempt is None else selected_attempt.attempt_sha256
        ),
        "selected_configuration": selected_configuration,
        "selected_configuration_sha256": (
            None
            if selected_attempt is None
            else selected_attempt.canonical_configuration_sha256
        ),
        "succeeded": succeeded,
        "budget_exhausted": exhausted,
        "all_thresholds_certified_before_first_decision": True,
        "prior_attempts_rejected": True,
        "selected_attempt_is_first_accepted": first,
        "suffix_decision_words_uninterpreted": suffix_uninterpreted,
        "complete_preparation_prefix_retained": True,
        "conditional_outcome_probability_numerator": probability.numerator,
        "conditional_outcome_probability_denominator": probability.denominator,
        "operational_failure_returned_as_exhaustion": False,
        "retry_fallback_or_rollback_claimed": False,
        "initializer_output_admitted": False,
        "deterministic_fixed_address_replay_only": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _semantic_digest(_result_payload(values))
    return CounterKeyedInitialTiltRejectionDecisionResult(
        _construction_token=_RESULT_TOKEN,
        **values,
    )


def _record_snapshot(record: object, fields: Tuple[str, ...]) -> Tuple[object, ...]:
    return tuple(getattr(record, name) for name in fields)


def _require_record_unchanged(
    record: object,
    fields: Tuple[str, ...],
    before: Tuple[object, ...],
    *,
    name: str,
) -> None:
    if type(before) is not tuple or len(before) != len(fields):
        raise TypeError("%s snapshot is malformed" % name)
    after = _record_snapshot(record, fields)
    for field, old, new in zip(fields, before, after):
        if new is not old:
            raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
                "%s field %s changed during operation" % (name, field)
            )


class CounterKeyedInitialTiltRejectionDecisionOwner:
    """Immutable owner of one CP36-bound decision pipeline."""

    __slots__ = (
        "_preparation_owner",
        "_preparation_owner_identity",
        "_preparation_certificate",
        "_preparation_certificate_identity",
        "_decision_policy",
        "_decision_policy_identity",
        "_decision_role_sha256",
        "_decision_role_sha256_identity",
        "_certificate",
        "_certificate_identity",
        "_certificate_snapshot",
        "_certificate_snapshot_identity",
        "_preparation_prepare",
        "_preparation_validate_result",
        "_threshold_builder",
        "_decision_builder",
        "_result_builder",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection-decision owners cannot be subclassed")

    def __init__(
        self,
        preparation_owner: _PREP_OWNER_TYPE,
        decision_policy: str,
        decision_role_sha256: str,
        certificate: CounterKeyedInitialTiltRejectionDecisionCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("rejection-decision owners require certification")
        if type(preparation_owner) is not _PREP_OWNER_TYPE:
            raise TypeError("preparation_owner has the wrong exact CP36 type")
        parent = _PREP_CERTIFICATE_PROPERTY.__get__(preparation_owner, _PREP_OWNER_TYPE)
        if parent is not certificate.preparation_certificate:
            raise ValueError("owner CP36 certificate identity differs")
        _require_text(decision_policy, _POLICY, name="decision_policy")
        _require_sha256(decision_role_sha256, name="decision_role_sha256")
        checked = _validate_certificate(certificate)
        if checked.preparation_owner_runtime_identity != id(preparation_owner):
            raise ValueError("certificate CP36 owner runtime identity differs")
        snapshot = tuple(getattr(checked, name) for name in _certificate_fields())
        bindings = (
            ("_preparation_owner", preparation_owner),
            ("_preparation_owner_identity", preparation_owner),
            ("_preparation_certificate", parent),
            ("_preparation_certificate_identity", parent),
            ("_decision_policy", decision_policy),
            ("_decision_policy_identity", decision_policy),
            ("_decision_role_sha256", decision_role_sha256),
            ("_decision_role_sha256_identity", decision_role_sha256),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_certificate_snapshot", snapshot),
            ("_certificate_snapshot_identity", snapshot),
            ("_preparation_prepare", _PREP_PREPARE),
            ("_preparation_validate_result", _PREP_VALIDATE_RESULT),
            ("_threshold_builder", _make_threshold),
            ("_decision_builder", _make_decision),
            ("_result_builder", _make_result),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("rejection-decision owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("rejection-decision owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection-decision owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedInitialTiltRejectionDecisionCertificate:
        return self._certificate

    @property
    def preparation_owner(self) -> _PREP_OWNER_TYPE:
        return self._preparation_owner

    def _owner_snapshot(self) -> Tuple[object, ...]:
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("rejection-decision owner seal differs")
        current = (
            self._preparation_owner,
            self._preparation_certificate,
            self._decision_policy,
            self._decision_role_sha256,
            self._certificate,
            self._certificate_snapshot,
        )
        frozen = (
            self._preparation_owner_identity,
            self._preparation_certificate_identity,
            self._decision_policy_identity,
            self._decision_role_sha256_identity,
            self._certificate_identity,
            self._certificate_snapshot_identity,
        )
        if any(live is not expected for live, expected in zip(current, frozen)):
            raise ValueError("rejection-decision owner identity changed")
        callbacks = (
            (self._preparation_prepare, _PREP_PREPARE),
            (self._preparation_validate_result, _PREP_VALIDATE_RESULT),
            (self._threshold_builder, _make_threshold),
            (self._decision_builder, _make_decision),
            (self._result_builder, _make_result),
        )
        if any(live is not expected for live, expected in callbacks):
            raise ValueError("rejection-decision cached callback changed")
        return current

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 6:
            raise TypeError("rejection-decision owner snapshot is malformed")
        current = self._owner_snapshot()
        if any(live is not expected for live, expected in zip(current, snapshot)):
            raise PluginBridgeCounterKeyedInitialTiltRejectionDecisionError(
                "rejection-decision owner changed during operation"
            )

    def _live_certificate(
        self,
        owner_snapshot: Tuple[object, ...],
    ) -> CounterKeyedInitialTiltRejectionDecisionCertificate:
        self._require_owner_snapshot(owner_snapshot)
        parent_snapshot = _PREP_OWNER_SNAPSHOT(self._preparation_owner)
        live_parent = _PREP_LIVE_CERTIFICATE(
            self._preparation_owner,
            parent_snapshot,
        )
        _PREP_REQUIRE_OWNER_SNAPSHOT(self._preparation_owner, parent_snapshot)
        if live_parent is not self._preparation_certificate:
            raise ValueError("CP36 live binding substituted its certificate")
        certificate = _validate_certificate(self._certificate)
        if certificate.preparation_owner_runtime_identity != id(
            self._preparation_owner
        ):
            raise ValueError("certificate CP36 owner runtime identity differs")
        if tuple(getattr(certificate, name) for name in _certificate_fields()) != (
            self._certificate_snapshot
        ):
            raise ValueError("rejection-decision certificate changed")
        self._require_owner_snapshot(owner_snapshot)
        return certificate

    def decide(
        self,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionDecisionResult:
        """Prepare once, certify all quotas, then select or exhaust."""

        checked_run = _exact_integer(
            run_id,
            name="run_id",
            maximum=(1 << 64) - 1,
        )
        checked_initialization = _exact_integer(
            initialization_index,
            name="initialization_index",
            maximum=(1 << 64) - 1,
        )
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        parent = self._preparation_prepare(
            self._preparation_owner,
            checked_run,
            checked_initialization,
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        parent = _preflight_preparation_result(parent, certificate=certificate)
        parent_snapshot = _PREP_RESULT_SNAPSHOT(parent)
        checked_parent = self._preparation_validate_result(
            self._preparation_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        _PREP_REQUIRE_RESULT_UNCHANGED(
            parent,
            parent_snapshot,
            certificate=certificate.preparation_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        if checked_parent is not parent:
            raise ValueError("CP36 validation substituted its result")

        thresholds = []
        for attempt in parent.attempts:
            threshold = self._threshold_builder(certificate, attempt)
            _PREP_REQUIRE_RESULT_UNCHANGED(
                parent,
                parent_snapshot,
                certificate=certificate.preparation_certificate,
            )
            self._require_owner_snapshot(owner_snapshot)
            thresholds.append(threshold)
        threshold_tuple = tuple(thresholds)

        decisions = []
        for threshold in threshold_tuple:
            decision = self._decision_builder(threshold)
            _PREP_REQUIRE_RESULT_UNCHANGED(
                parent,
                parent_snapshot,
                certificate=certificate.preparation_certificate,
            )
            self._require_owner_snapshot(owner_snapshot)
            decisions.append(decision)
            if decision.accepted:
                break
        result = self._result_builder(
            certificate,
            parent,
            threshold_tuple,
            tuple(decisions),
        )
        _PREP_REQUIRE_RESULT_UNCHANGED(
            parent,
            parent_snapshot,
            certificate=certificate.preparation_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        return result

    def validate_result(
        self,
        result: object,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionDecisionResult:
        """Replay CP36 validation and every finite-resolution decision."""

        checked_run = _exact_integer(
            run_id,
            name="run_id",
            maximum=(1 << 64) - 1,
        )
        checked_initialization = _exact_integer(
            initialization_index,
            name="initialization_index",
            maximum=(1 << 64) - 1,
        )
        if type(result) is not CounterKeyedInitialTiltRejectionDecisionResult:
            raise TypeError("result has the wrong exact rejection-decision type")
        values = {name: getattr(result, name) for name in _result_fields()}
        _validate_result_values(values)
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        if result.certificate is not certificate:
            raise ValueError("result belongs to another rejection-decision owner")
        if result.run_id != checked_run or (
            result.initialization_index != checked_initialization
        ):
            raise ValueError("result request coordinates differ")
        result_before = _record_snapshot(result, _result_fields())
        threshold_befores = tuple(
            _record_snapshot(item, _threshold_fields()) for item in result.thresholds
        )
        decision_befores = tuple(
            _record_snapshot(item, _decision_fields()) for item in result.decisions
        )
        parent = result.preparation_result
        parent_snapshot = _PREP_RESULT_SNAPSHOT(parent)
        checked_parent = self._preparation_validate_result(
            self._preparation_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        _PREP_REQUIRE_RESULT_UNCHANGED(
            parent,
            parent_snapshot,
            certificate=certificate.preparation_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        if checked_parent is not parent:
            raise ValueError("CP36 validation substituted its result")
        expected_thresholds = tuple(
            self._threshold_builder(certificate, attempt) for attempt in parent.attempts
        )
        expected_decisions = []
        for threshold in expected_thresholds:
            decision = self._decision_builder(threshold)
            expected_decisions.append(decision)
            if decision.accepted:
                break
        if tuple(item.threshold_sha256 for item in expected_thresholds) != (
            result.threshold_sha256s
        ):
            raise ValueError("result threshold replay differs")
        if tuple(item.decision_sha256 for item in expected_decisions) != (
            result.decision_sha256s
        ):
            raise ValueError("result decision replay differs")
        expected_result = self._result_builder(
            certificate,
            parent,
            expected_thresholds,
            tuple(expected_decisions),
        )
        if expected_result.result_sha256 != result.result_sha256:
            raise ValueError("result replay digest differs")
        _require_record_unchanged(
            result,
            _result_fields(),
            result_before,
            name="rejection-decision result",
        )
        for position, (item, before) in enumerate(
            zip(result.thresholds, threshold_befores)
        ):
            _require_record_unchanged(
                item,
                _threshold_fields(),
                before,
                name="rejection threshold %d" % position,
            )
        for position, (item, before) in enumerate(
            zip(result.decisions, decision_befores)
        ):
            _require_record_unchanged(
                item,
                _decision_fields(),
                before,
                name="rejection decision %d" % position,
            )
        _PREP_REQUIRE_RESULT_UNCHANGED(
            parent,
            parent_snapshot,
            certificate=certificate.preparation_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        return result


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_decision(
    preparation_owner: object,
    *,
    decision_policy: object,
    decision_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionDecisionOwner:
    """Certify conservative fixed-word rejection decisions over CP36."""

    if type(preparation_owner) is not _PREP_OWNER_TYPE:
        raise TypeError("preparation_owner has the wrong exact CP36 type")
    policy = _require_text(decision_policy, _POLICY, name="decision_policy")
    role = _require_sha256(decision_role_sha256, name="decision_role_sha256")
    parent_snapshot = _PREP_OWNER_SNAPSHOT(preparation_owner)
    parent = _PREP_LIVE_CERTIFICATE(preparation_owner, parent_snapshot)
    _PREP_REQUIRE_OWNER_SNAPSHOT(preparation_owner, parent_snapshot)
    if parent is not _PREP_CERTIFICATE_PROPERTY.__get__(
        preparation_owner, _PREP_OWNER_TYPE
    ):
        raise ValueError("CP36 live binding substituted its certificate")
    certificate = _make_certificate(preparation_owner, role)
    _PREP_REQUIRE_OWNER_SNAPSHOT(preparation_owner, parent_snapshot)
    owner = CounterKeyedInitialTiltRejectionDecisionOwner(
        preparation_owner,
        policy,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    snapshot = owner._owner_snapshot()
    owner._live_certificate(snapshot)
    owner._require_owner_snapshot(snapshot)
    return owner


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_decision(
    preparation_owner: object,
    owner: object,
    *,
    decision_policy: object,
    decision_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionDecisionOwner:
    """Require the exact CP36 parent, policy, role, and live certificate."""

    if type(preparation_owner) is not _PREP_OWNER_TYPE:
        raise TypeError("preparation_owner has the wrong exact CP36 type")
    if type(owner) is not CounterKeyedInitialTiltRejectionDecisionOwner:
        raise TypeError("owner has the wrong exact rejection-decision type")
    policy = _require_text(decision_policy, _POLICY, name="decision_policy")
    role = _require_sha256(decision_role_sha256, name="decision_role_sha256")
    snapshot = owner._owner_snapshot()
    certificate = owner._live_certificate(snapshot)
    if owner.preparation_owner is not preparation_owner:
        raise ValueError("owner uses another CP36 parent")
    if certificate.preparation_owner_runtime_identity != id(preparation_owner):
        raise ValueError("owner certificate uses another CP36 runtime identity")
    if certificate.decision_policy != policy:
        raise ValueError("owner uses another decision policy")
    if certificate.decision_role_sha256 != role:
        raise ValueError("owner uses another decision role")
    owner._require_owner_snapshot(snapshot)
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_decision_certificate(
    preparation_owner: object,
    owner: object,
    *,
    decision_policy: object,
    decision_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionDecisionCertificate:
    """Return the reconstructed live CP37 certificate."""

    return require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_decision(
        preparation_owner,
        owner,
        decision_policy=decision_policy,
        decision_role_sha256=decision_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_ALGORITHM",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCOPE",
    "INITIAL_TILT_REJECTION_DECISION_DYADIC_DENOMINATOR",
    "INITIAL_TILT_REJECTION_DECISION_RAW_WORD_BITS",
    "INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION",
    "INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION",
    "INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION",
    "INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF",
    "INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS",
    "INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS",
    "INITIAL_TILT_REJECTION_DECISION_OUTCOMES",
    "INITIAL_TILT_REJECTION_DECISION_CONDITIONAL_THEOREM",
    "INITIAL_TILT_REJECTION_DECISION_APPROXIMATION_THEOREM",
    "CounterKeyedInitialTiltRejectionDecisionCertificate",
    "CounterKeyedInitialTiltRejectionThreshold",
    "CounterKeyedInitialTiltRejectionAttemptDecision",
    "CounterKeyedInitialTiltRejectionDecisionResult",
    "CounterKeyedInitialTiltRejectionDecisionOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionDecisionError",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_decision",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_decision",
    (
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "decision_certificate"
    ),
]
