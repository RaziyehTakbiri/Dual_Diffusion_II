"""Certified rate-space domination for the totalized operational jump target.

Checkpoint seventeen defines an exact rational operational point-potential
edge ``Delta_Q Phi_op`` for one process-valid candidate.  This module consumes
that exact edge, rather than its rounded binary64 display value, and certifies
the rate-space quantities

``I = Lambda_ref * exp(Delta_Q Phi_op)``

and

``E = Lambda_ref * exp(D_Phi)``,

where ``D_Phi`` is the checkpoint-seventeen global operational edge-magnitude
bound and ``Lambda_ref`` is the no-RNG normalized-reference candidate
intensity.  A preflighted ``E`` is a pointwise dominating candidate-clock rate
and therefore an upper bound on the operational controlled total exit.  It is
not the exact controlled total exit.

Exponentials are enclosed with correctly rounded high-precision Decimal
arithmetic and adjacent Decimal values, then converted outward to binary64.
The no-RNG envelope is available before a route is sampled.  This module does
not draw a waiting time, make an acceptance decision, consume randomness,
differentiate a potential, construct a path, or admit a sampler.
"""

from __future__ import annotations

from dataclasses import dataclass
import decimal
from decimal import Context, Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
from fractions import Fraction
import math
import platform
import sys
from typing import Dict, Mapping, Tuple

try:
    from heterodiff.models import (
        configuration_totalized_jump_potential_composer_torch as _potential,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or (
        "jump-potential composition requires the optional PyTorch" in str(error)
    ):
        raise ModuleNotFoundError(
            "configuration totalized jump-rate domination requires the "
            "optional PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise

CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY = (
    _potential.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY
)
ConfigurationTotalizedJumpPotentialError = (
    _potential.ConfigurationTotalizedJumpPotentialError
)
TotalizedConfigurationJumpPotentialComposer = (
    _potential.TotalizedConfigurationJumpPotentialComposer
)
TotalizedJumpPotentialCandidateEvaluation = (
    _potential.TotalizedJumpPotentialCandidateEvaluation
)
TotalizedJumpPotentialCompositionCertificate = (
    _potential.TotalizedJumpPotentialCompositionCertificate
)
_candidate_sha256 = _potential._candidate_sha256
_configuration_sha256 = _potential._configuration_sha256
_fraction = _potential._fraction
_outward_nonnegative_fraction = _potential._outward_nonnegative_fraction
_require_binary64_environment = _potential._require_binary64_environment
_require_fraction_size = _potential._require_fraction_size
_require_sha256 = _potential._require_sha256
_round_fraction_once = _potential._round_fraction_once
_same_float = _potential._same_float
_semantic_digest = _potential._semantic_digest
_validated_float = _potential._validated_float
_validated_fraction_parts = _potential._validated_fraction_parts

from heterodiff.processes.plugin_bridge_sampler import (
    ProcessValidReferenceJump,
    ProcessValidReferenceJumpComposer,
    ReferenceCandidateIntensity,
)


CONFIGURATION_TOTALIZED_JUMP_RATE_SCHEMA_VERSION = (
    "configuration-totalized-operational-jump-rate-envelope-v1"
)
CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY = (
    "normalized-reference-candidate-clock;"
    "exact-rational-operational-edge-exponentiation;"
    "global-operational-edge-bound-domination;"
    "outward-binary64-rate-intervals-v1"
)
CONFIGURATION_TOTALIZED_JUMP_RATE_EXPONENTIATION_ALGORITHM = (
    "base1e9-integer-digit-extraction;"
    "exact-power-of-two-rational-to-decimal;"
    "decimal-exp-correct-round-half-even;"
    "adjacent-decimal-enclosure;"
    "directed-decimal-product;outward-binary64-conversion-v1"
)
CONFIGURATION_TOTALIZED_JUMP_RATE_FLOATING_POINT_POLICY = (
    "binary64-rne-gradual-underflow;explicit-decimal-contexts;"
    "finite-upper-envelope-required-v1"
)
CONFIGURATION_TOTALIZED_JUMP_RATE_SCOPE = (
    "checkpoint17-operational-surrogate-target;"
    "no-rng-reference-intensity-preflight;"
    "exact-operational-edge-rate-interval;"
    "pointwise-candidate-clock-domination;"
    "controlled-total-exit-upper-bound;"
    "structural-zero-preserved;trusted-runtime;"
    "not-exact-controlled-total-exit;not-analytic-target;"
    "not-exact-stationary-target;not-rounded-detailed-balance;"
    "not-candidate-route-draw;not-waiting-time;"
    "not-acceptance-decision;not-rng;"
    "not-derivatives;not-drift;not-initializer;not-path;not-sampler"
)

TOTALIZED_JUMP_RATE_DECIMAL_PRIMARY_PRECISION = 192
TOTALIZED_JUMP_RATE_DECIMAL_AUDIT_PRECISION = 384
TOTALIZED_JUMP_RATE_DECIMAL_MAX_PRECISION = 1_536
MAX_TOTALIZED_JUMP_RATE_DECIMAL_COEFFICIENT_DIGITS = 16_384

_DECIMAL_MIN_EXPONENT = -999_999
_DECIMAL_MAX_EXPONENT = 999_999
_CERTIFICATE_TOKEN = object()
_ENVELOPE_TOKEN = object()
_EVALUATION_TOKEN = object()
_OWNER_TOKEN = object()


class ConfigurationTotalizedJumpRateError(ArithmeticError):
    """Raised when a finite certified operational rate cannot be enclosed."""


def _rate_require_fraction_size(value: Fraction, *, name: str) -> Fraction:
    try:
        return _require_fraction_size(value, name=name)
    except ConfigurationTotalizedJumpPotentialError as error:
        raise ConfigurationTotalizedJumpRateError(str(error)) from error


def _rate_round_fraction_once(value: Fraction, *, name: str) -> float:
    try:
        return _round_fraction_once(value, name=name)
    except ConfigurationTotalizedJumpPotentialError as error:
        raise ConfigurationTotalizedJumpRateError(str(error)) from error


def _rate_outward_nonnegative_fraction(value: Fraction, *, name: str) -> float:
    try:
        return _outward_nonnegative_fraction(value, name=name)
    except ConfigurationTotalizedJumpPotentialError as error:
        raise ConfigurationTotalizedJumpRateError(str(error)) from error


def _canonical_zero(value: float) -> float:
    return 0.0 if value == 0.0 else value


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


def _nonnegative_integer_decimal_digits(value: int, *, name: str) -> Tuple[int, ...]:
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
    if digit_count > MAX_TOTALIZED_JUMP_RATE_DECIMAL_COEFFICIENT_DIGITS:
        raise ConfigurationTotalizedJumpRateError(
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


def _exact_power_two_fraction_decimal(value: Fraction, *, name: str) -> Decimal:
    checked = _rate_require_fraction_size(value, name=name)
    denominator = checked.denominator
    if denominator <= 0 or denominator & (denominator - 1):
        raise ConfigurationTotalizedJumpRateError(
            "%s denominator is not an exact power of two" % name
        )
    if checked.numerator == 0:
        return Decimal(0)
    exponent = denominator.bit_length() - 1
    coefficient = checked.numerator * (5**exponent)
    digits = _nonnegative_integer_decimal_digits(abs(coefficient), name=name)
    return Decimal((1 if coefficient < 0 else 0, digits, -exponent))


def _one_precision_exp_interval(
    exact_log: Decimal,
    *,
    precision: int,
) -> Tuple[Decimal, Decimal]:
    context = _decimal_context(precision, ROUND_HALF_EVEN)
    try:
        rounded = context.exp(exact_log)
    except decimal.DecimalException as error:
        raise ConfigurationTotalizedJumpRateError(
            "Decimal exponential is outside the certified work domain"
        ) from error
    if not rounded.is_finite() or rounded <= 0:
        raise ConfigurationTotalizedJumpRateError(
            "Decimal exponential did not return a finite positive value"
        )
    if exact_log.is_zero():
        return Decimal(1), Decimal(1)
    try:
        lower = context.next_minus(rounded)
        upper = context.next_plus(rounded)
    except decimal.DecimalException as error:
        raise ConfigurationTotalizedJumpRateError(
            "Decimal exponential neighbors are outside the work domain"
        ) from error
    if not lower.is_finite() or not upper.is_finite() or not 0 < lower <= upper:
        raise ConfigurationTotalizedJumpRateError(
            "Decimal exponential neighbors do not form a finite interval"
        )
    return lower, upper


def _scale_decimal_interval(
    lower: Decimal,
    upper: Decimal,
    scale: Fraction,
    *,
    name: str,
    precision: int = TOTALIZED_JUMP_RATE_DECIMAL_AUDIT_PRECISION,
) -> Tuple[Decimal, Decimal]:
    checked_scale = _rate_require_fraction_size(scale, name=name + " scale")
    if checked_scale < 0:
        raise ValueError("%s scale must be nonnegative" % name)
    if checked_scale == 0:
        return Decimal(0), Decimal(0)
    exact_scale = _exact_power_two_fraction_decimal(
        checked_scale,
        name=name + " scale",
    )
    lower_context = _decimal_context(
        precision,
        ROUND_FLOOR,
    )
    upper_context = _decimal_context(
        precision,
        ROUND_CEILING,
    )
    try:
        scaled_lower = lower_context.multiply(lower, exact_scale)
        scaled_upper = upper_context.multiply(upper, exact_scale)
    except decimal.DecimalException as error:
        raise ConfigurationTotalizedJumpRateError(
            "%s Decimal product is outside the certified work domain" % name
        ) from error
    if (
        not scaled_lower.is_finite()
        or not scaled_upper.is_finite()
        or not Decimal(0) <= scaled_lower <= scaled_upper
    ):
        raise ConfigurationTotalizedJumpRateError(
            "%s Decimal product interval is invalid" % name
        )
    return scaled_lower, scaled_upper


def _decimal_floor_binary64(value: Decimal, *, name: str) -> float:
    if not value.is_finite() or value < 0:
        raise ValueError("%s lower endpoint must be finite and nonnegative" % name)
    if value.is_zero():
        return 0.0
    exact = Fraction(value)
    result = _rate_round_fraction_once(exact, name=name + " lower endpoint")
    if _fraction(result) > exact:
        result = math.nextafter(result, -math.inf)
    if result < 0.0:
        result = 0.0
    return _canonical_zero(result)


def _decimal_ceiling_binary64(value: Decimal, *, name: str) -> float:
    if not value.is_finite() or value < 0:
        raise ValueError("%s upper endpoint must be finite and nonnegative" % name)
    if value.is_zero():
        return 0.0
    exact = Fraction(value)
    return _rate_outward_nonnegative_fraction(
        exact,
        name=name + " upper endpoint",
    )


def _precision_schedule() -> Tuple[int, ...]:
    values = []
    precision = TOTALIZED_JUMP_RATE_DECIMAL_PRIMARY_PRECISION
    while precision < TOTALIZED_JUMP_RATE_DECIMAL_MAX_PRECISION:
        values.append(precision)
        precision *= 2
    values.append(TOTALIZED_JUMP_RATE_DECIMAL_MAX_PRECISION)
    return tuple(values)


def _scaled_decimal_exp_interval_at_precision(
    exact_log: Fraction,
    scale: Fraction,
    *,
    name: str,
    precision: int,
) -> Tuple[Decimal, Decimal]:
    exact_decimal = _exact_power_two_fraction_decimal(exact_log, name=name)
    lower, upper = _one_precision_exp_interval(
        exact_decimal,
        precision=precision,
    )
    return _scale_decimal_interval(
        lower,
        upper,
        scale,
        name=name,
        precision=precision,
    )


def _scaled_exp_outward_envelope(
    exact_log: Fraction,
    scale: Fraction,
    *,
    name: str,
) -> Tuple[float, float, float, int]:
    checked_scale = _rate_require_fraction_size(scale, name=name + " scale")
    if checked_scale < 0:
        raise ValueError("%s scale must be nonnegative" % name)
    if checked_scale == 0:
        return 0.0, 0.0, 0.0, 0
    if exact_log == 0:
        exact = _rate_round_fraction_once(checked_scale, name=name)
        return exact, exact, exact, 0
    if exact_log > 1_500:
        raise ConfigurationTotalizedJumpRateError(
            "%s exceeds the positive-scale exponent admission limit" % name
        )
    previous = None
    for precision in _precision_schedule():
        lower_decimal, upper_decimal = _scaled_decimal_exp_interval_at_precision(
            exact_log,
            checked_scale,
            name=name,
            precision=precision,
        )
        if previous is not None and not (
            previous[0] <= lower_decimal <= upper_decimal <= previous[1]
        ):
            raise ConfigurationTotalizedJumpRateError(
                "%s adaptive Decimal intervals are not nested" % name
            )
        previous = (lower_decimal, upper_decimal)
        try:
            lower_outward = _decimal_ceiling_binary64(lower_decimal, name=name)
            upper_outward = _decimal_ceiling_binary64(upper_decimal, name=name)
        except ConfigurationTotalizedJumpRateError:
            continue
        if _same_float(lower_outward, upper_outward):
            lower_floor = _decimal_floor_binary64(lower_decimal, name=name)
            return lower_floor, upper_outward, upper_outward, precision
    raise ConfigurationTotalizedJumpRateError(
        "%s outward binary64 envelope is precision-ambiguous" % name
    )


def _scaled_exp_correctly_rounded_rate(
    exact_log: Fraction,
    scale: Fraction,
    *,
    name: str,
) -> Tuple[float, float, float, int]:
    checked_scale = _rate_require_fraction_size(scale, name=name + " scale")
    if checked_scale <= 0:
        raise ValueError("%s scale must be strictly positive" % name)
    if exact_log == 0:
        result = _rate_round_fraction_once(checked_scale, name=name)
        if result < sys.float_info.min:
            raise ConfigurationTotalizedJumpRateError(
                "%s is not a normal positive binary64 rate" % name
            )
        return result, result, result, 0
    if exact_log > 1_500:
        raise ConfigurationTotalizedJumpRateError(
            "%s exceeds the positive-scale exponent admission limit" % name
        )
    previous = None
    for precision in _precision_schedule():
        lower_decimal, upper_decimal = _scaled_decimal_exp_interval_at_precision(
            exact_log,
            checked_scale,
            name=name,
            precision=precision,
        )
        if previous is not None and not (
            previous[0] <= lower_decimal <= upper_decimal <= previous[1]
        ):
            raise ConfigurationTotalizedJumpRateError(
                "%s adaptive Decimal intervals are not nested" % name
            )
        previous = (lower_decimal, upper_decimal)
        try:
            lower_rounded = _rate_round_fraction_once(
                Fraction(lower_decimal),
                name=name + " lower rounded endpoint",
            )
            upper_rounded = _rate_round_fraction_once(
                Fraction(upper_decimal),
                name=name + " upper rounded endpoint",
            )
        except ConfigurationTotalizedJumpRateError:
            continue
        if _same_float(lower_rounded, upper_rounded):
            if lower_rounded < sys.float_info.min:
                raise ConfigurationTotalizedJumpRateError(
                    "%s is not a normal positive binary64 rate" % name
                )
            try:
                lower = _decimal_floor_binary64(lower_decimal, name=name)
                upper = _decimal_ceiling_binary64(upper_decimal, name=name)
            except ConfigurationTotalizedJumpRateError:
                continue
            return lower_rounded, lower, upper, precision
    raise ConfigurationTotalizedJumpRateError(
        "%s correctly rounded binary64 rate is precision-ambiguous" % name
    )


def _rate_runtime_sha256() -> str:
    return _semantic_digest(
        {
            "domain": "configuration-totalized-jump-rate-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "decimal_module_version": getattr(decimal, "__version__", "unknown"),
            "libmpdec_version": getattr(
                decimal,
                "__libmpdec_version__",
                "unknown",
            ),
            "schema_version": CONFIGURATION_TOTALIZED_JUMP_RATE_SCHEMA_VERSION,
            "exponentiation_algorithm": (
                CONFIGURATION_TOTALIZED_JUMP_RATE_EXPONENTIATION_ALGORITHM
            ),
            "primary_precision": TOTALIZED_JUMP_RATE_DECIMAL_PRIMARY_PRECISION,
            "audit_precision": TOTALIZED_JUMP_RATE_DECIMAL_AUDIT_PRECISION,
            "maximum_precision": TOTALIZED_JUMP_RATE_DECIMAL_MAX_PRECISION,
            "minimum_decimal_exponent": _DECIMAL_MIN_EXPONENT,
            "maximum_decimal_exponent": _DECIMAL_MAX_EXPONENT,
            "maximum_decimal_coefficient_digits": (
                MAX_TOTALIZED_JUMP_RATE_DECIMAL_COEFFICIENT_DIGITS
            ),
            "decimal_traps": (
                "InvalidOperation",
                "DivisionByZero",
                "Overflow",
                "Underflow",
            ),
            "binary64_probe": _require_binary64_environment(),
        }
    )


def _intensity_payload(intensity: ReferenceCandidateIntensity) -> Mapping[str, object]:
    base_rates = intensity.base_rates
    return {
        "domain": "configuration-totalized-jump-rate-intensity-v1",
        "schema_version": intensity.schema_version,
        "contract_scope": intensity.contract_scope,
        "source_state_sha256": _configuration_sha256(intensity.source_configuration),
        "reverse_time": intensity.reverse_time,
        "direct_time": intensity.direct_time,
        "reference_schedule_rate": intensity.reference_schedule_rate,
        "scheduled_reference_exit_rate": (intensity.scheduled_reference_exit_rate),
        "base_birth_rate": None if base_rates is None else base_rates.birth,
        "base_death_rate": None if base_rates is None else base_rates.death,
        "base_replacement_rate": (
            None if base_rates is None else base_rates.replacement
        ),
        "base_total_rate": None if base_rates is None else base_rates.total,
    }


def _intensity_sha256(intensity: ReferenceCandidateIntensity) -> str:
    return _semantic_digest(_intensity_payload(intensity))


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: value for name, value in values.items() if name != "certificate_sha256"
    }


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpRateEnvelopeCertificate:
    """Transitive certificate for exact-log rate intervals and domination."""

    schema_version: str
    certificate_scope: str
    target_policy: str
    rate_policy: str
    exponentiation_algorithm: str
    floating_point_environment_policy: str
    rate_role_sha256: str
    process_parameter_sha256: str
    reverse_time_horizon: float
    potential_composition_certificate_sha256: str
    potential_composition_role_sha256: str
    potential_composer_runtime_sha256: str
    base_checkpoint_sha256: str
    guide_totalized_certificate_sha256: str
    residual_totalized_certificate_sha256: str
    rate_runtime_sha256: str
    aggregate_edge_magnitude_bound: float
    exact_log_envelope_bound_numerator: int
    exact_log_envelope_bound_denominator: int
    maximum_reference_exit_rate: float
    global_dominating_exit_rate_upper_bound: float
    decimal_primary_precision: int
    decimal_audit_precision: int
    decimal_max_precision: int
    decimal_min_exponent: int
    decimal_max_exponent: int
    maximum_decimal_coefficient_digits: int
    global_envelope_decimal_precision_used: int
    operational_surrogate_target_consumed: bool
    exact_rational_log_increment_authoritative: bool
    checkpoint17_rounded_increment_exponentiated: bool
    candidate_real_rate_interval_certified: bool
    outward_rate_envelope_certified: bool
    normalized_reference_kernel_required: bool
    pointwise_candidate_domination_certified: bool
    controlled_total_exit_upper_bound_certified: bool
    global_controlled_total_exit_upper_bound_certified: bool
    no_rng_envelope_construction_certified: bool
    structural_zero_preserved: bool
    exact_controlled_total_exit_computed: bool
    exact_analytic_target_preserved: bool
    exact_conditional_or_posterior_target: bool
    successful_candidate_rate_correct_rounding_certified: bool
    full_rate_totality_certified: bool
    candidate_route_draw_admissible: bool
    rounded_rate_reversal_or_detailed_balance_certified: bool
    exact_operational_stationary_target_certified: bool
    waiting_time_admissible: bool
    acceptance_decision_admissible: bool
    randomness_admissible: bool
    coordinate_derivatives_admissible: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    operational_sampler_admissible: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedJumpRateEnvelopeCertificate cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("jump-rate certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("jump-rate certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "configuration-totalized-jump-rate-envelope-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("jump-rate certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(TotalizedJumpRateEnvelopeCertificate.__annotations__)


def _validate_certificate(
    certificate: object,
) -> TotalizedJumpRateEnvelopeCertificate:
    if type(certificate) is not TotalizedJumpRateEnvelopeCertificate:
        raise TypeError(
            "certificate must be an exact TotalizedJumpRateEnvelopeCertificate"
        )
    expected_text = {
        "schema_version": CONFIGURATION_TOTALIZED_JUMP_RATE_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_TOTALIZED_JUMP_RATE_SCOPE,
        "target_policy": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "rate_policy": CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
        "exponentiation_algorithm": (
            CONFIGURATION_TOTALIZED_JUMP_RATE_EXPONENTIATION_ALGORITHM
        ),
        "floating_point_environment_policy": (
            CONFIGURATION_TOTALIZED_JUMP_RATE_FLOATING_POINT_POLICY
        ),
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("jump-rate certificate %s is inconsistent" % name)
    for name in (
        "rate_role_sha256",
        "process_parameter_sha256",
        "potential_composition_certificate_sha256",
        "potential_composition_role_sha256",
        "potential_composer_runtime_sha256",
        "base_checkpoint_sha256",
        "guide_totalized_certificate_sha256",
        "residual_totalized_certificate_sha256",
        "rate_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    _validated_float(
        certificate.reverse_time_horizon,
        name="certificate.reverse_time_horizon",
        strictly_positive=True,
    )
    for name in (
        "aggregate_edge_magnitude_bound",
        "maximum_reference_exit_rate",
        "global_dominating_exit_rate_upper_bound",
    ):
        _validated_float(
            getattr(certificate, name),
            name="certificate.%s" % name,
            nonnegative=True,
        )
    for name, expected in (
        (
            "decimal_primary_precision",
            TOTALIZED_JUMP_RATE_DECIMAL_PRIMARY_PRECISION,
        ),
        (
            "decimal_audit_precision",
            TOTALIZED_JUMP_RATE_DECIMAL_AUDIT_PRECISION,
        ),
        (
            "decimal_max_precision",
            TOTALIZED_JUMP_RATE_DECIMAL_MAX_PRECISION,
        ),
        ("decimal_min_exponent", _DECIMAL_MIN_EXPONENT),
        ("decimal_max_exponent", _DECIMAL_MAX_EXPONENT),
        (
            "maximum_decimal_coefficient_digits",
            MAX_TOTALIZED_JUMP_RATE_DECIMAL_COEFFICIENT_DIGITS,
        ),
    ):
        value = getattr(certificate, name)
        if type(value) is not int or isinstance(value, bool) or value != expected:
            raise ValueError("certificate %s is inconsistent" % name)
    exact_bound = _validated_fraction_parts(
        certificate.exact_log_envelope_bound_numerator,
        certificate.exact_log_envelope_bound_denominator,
        name="certificate exact log envelope bound",
    )
    if exact_bound != _fraction(certificate.aggregate_edge_magnitude_bound):
        raise ValueError("certificate exact log envelope bound is inconsistent")
    _, _, expected_global, expected_global_precision = _scaled_exp_outward_envelope(
        exact_bound,
        _fraction(certificate.maximum_reference_exit_rate),
        name="global dominating exit rate",
    )
    if not _same_float(
        certificate.global_dominating_exit_rate_upper_bound,
        expected_global,
    ):
        raise ValueError("certificate global exit-rate bound is inconsistent")
    if (
        type(certificate.global_envelope_decimal_precision_used) is not int
        or isinstance(certificate.global_envelope_decimal_precision_used, bool)
        or certificate.global_envelope_decimal_precision_used
        != expected_global_precision
    ):
        raise ValueError("certificate global envelope precision is inconsistent")
    if (
        certificate.maximum_reference_exit_rate > 0.0
        and certificate.global_dominating_exit_rate_upper_bound < sys.float_info.min
    ):
        raise ValueError("certificate global envelope must be normal when active")
    true_flags = (
        "operational_surrogate_target_consumed",
        "exact_rational_log_increment_authoritative",
        "candidate_real_rate_interval_certified",
        "successful_candidate_rate_correct_rounding_certified",
        "outward_rate_envelope_certified",
        "normalized_reference_kernel_required",
        "pointwise_candidate_domination_certified",
        "controlled_total_exit_upper_bound_certified",
        "global_controlled_total_exit_upper_bound_certified",
        "no_rng_envelope_construction_certified",
        "structural_zero_preserved",
        "passed",
    )
    false_flags = (
        "checkpoint17_rounded_increment_exponentiated",
        "exact_controlled_total_exit_computed",
        "exact_analytic_target_preserved",
        "exact_conditional_or_posterior_target",
        "full_rate_totality_certified",
        "candidate_route_draw_admissible",
        "rounded_rate_reversal_or_detailed_balance_certified",
        "exact_operational_stationary_target_certified",
        "waiting_time_admissible",
        "acceptance_decision_admissible",
        "randomness_admissible",
        "coordinate_derivatives_admissible",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "operational_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("jump-rate certificate positive flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("jump-rate certificate negative flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    if certificate.certificate_sha256 != _semantic_digest(_certificate_payload(values)):
        raise ValueError("jump-rate certificate digest is inconsistent")
    return certificate


def _make_certificate(
    potential_certificate: TotalizedJumpPotentialCompositionCertificate,
    *,
    maximum_reference_exit_rate: float,
    rate_role_sha256: str,
) -> TotalizedJumpRateEnvelopeCertificate:
    exact_bound = _fraction(potential_certificate.aggregate_edge_magnitude_bound)
    _, _, global_upper, global_precision = _scaled_exp_outward_envelope(
        exact_bound,
        _fraction(maximum_reference_exit_rate),
        name="global dominating exit rate",
    )
    if maximum_reference_exit_rate > 0.0 and global_upper < sys.float_info.min:
        raise ConfigurationTotalizedJumpRateError(
            "global dominating exit rate is not a normal binary64 value"
        )
    values: Dict[str, object] = {
        "schema_version": CONFIGURATION_TOTALIZED_JUMP_RATE_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_TOTALIZED_JUMP_RATE_SCOPE,
        "target_policy": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "rate_policy": CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
        "exponentiation_algorithm": (
            CONFIGURATION_TOTALIZED_JUMP_RATE_EXPONENTIATION_ALGORITHM
        ),
        "floating_point_environment_policy": (
            CONFIGURATION_TOTALIZED_JUMP_RATE_FLOATING_POINT_POLICY
        ),
        "rate_role_sha256": rate_role_sha256,
        "process_parameter_sha256": (potential_certificate.process_parameter_sha256),
        "reverse_time_horizon": potential_certificate.reverse_time_horizon,
        "potential_composition_certificate_sha256": (
            potential_certificate.certificate_sha256
        ),
        "potential_composition_role_sha256": (
            potential_certificate.composition_role_sha256
        ),
        "potential_composer_runtime_sha256": (
            potential_certificate.composer_runtime_sha256
        ),
        "base_checkpoint_sha256": potential_certificate.base_checkpoint_sha256,
        "guide_totalized_certificate_sha256": (
            potential_certificate.guide_totalized_certificate_sha256
        ),
        "residual_totalized_certificate_sha256": (
            potential_certificate.residual_totalized_certificate_sha256
        ),
        "rate_runtime_sha256": _rate_runtime_sha256(),
        "aggregate_edge_magnitude_bound": (
            potential_certificate.aggregate_edge_magnitude_bound
        ),
        "exact_log_envelope_bound_numerator": exact_bound.numerator,
        "exact_log_envelope_bound_denominator": exact_bound.denominator,
        "maximum_reference_exit_rate": maximum_reference_exit_rate,
        "global_dominating_exit_rate_upper_bound": global_upper,
        "decimal_primary_precision": TOTALIZED_JUMP_RATE_DECIMAL_PRIMARY_PRECISION,
        "decimal_audit_precision": TOTALIZED_JUMP_RATE_DECIMAL_AUDIT_PRECISION,
        "decimal_max_precision": TOTALIZED_JUMP_RATE_DECIMAL_MAX_PRECISION,
        "decimal_min_exponent": _DECIMAL_MIN_EXPONENT,
        "decimal_max_exponent": _DECIMAL_MAX_EXPONENT,
        "maximum_decimal_coefficient_digits": (
            MAX_TOTALIZED_JUMP_RATE_DECIMAL_COEFFICIENT_DIGITS
        ),
        "global_envelope_decimal_precision_used": global_precision,
        "operational_surrogate_target_consumed": True,
        "exact_rational_log_increment_authoritative": True,
        "checkpoint17_rounded_increment_exponentiated": False,
        "candidate_real_rate_interval_certified": True,
        "outward_rate_envelope_certified": True,
        "normalized_reference_kernel_required": True,
        "pointwise_candidate_domination_certified": True,
        "controlled_total_exit_upper_bound_certified": True,
        "global_controlled_total_exit_upper_bound_certified": True,
        "no_rng_envelope_construction_certified": True,
        "structural_zero_preserved": True,
        "exact_controlled_total_exit_computed": False,
        "exact_analytic_target_preserved": False,
        "exact_conditional_or_posterior_target": False,
        "successful_candidate_rate_correct_rounding_certified": True,
        "full_rate_totality_certified": False,
        "candidate_route_draw_admissible": False,
        "rounded_rate_reversal_or_detailed_balance_certified": False,
        "exact_operational_stationary_target_certified": False,
        "waiting_time_admissible": False,
        "acceptance_decision_admissible": False,
        "randomness_admissible": False,
        "coordinate_derivatives_admissible": False,
        "continuous_drift_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "operational_sampler_admissible": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return TotalizedJumpRateEnvelopeCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _envelope_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "envelope_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpRateEnvelope:
    """No-RNG instantaneous and global domination record."""

    certificate: TotalizedJumpRateEnvelopeCertificate
    certificate_sha256: str
    intensity_sha256: str
    process_parameter_sha256: str
    source_state_sha256: str
    reverse_time: float
    direct_time: float
    reference_schedule_rate: float
    scheduled_reference_exit_rate: float
    aggregate_edge_magnitude_bound: float
    exact_log_envelope_bound_numerator: int
    exact_log_envelope_bound_denominator: int
    dominating_real_rate_interval_lower_bound: float
    controlled_total_exit_upper_bound: float
    global_dominating_exit_rate_upper_bound: float
    reference_intensity_zero: bool
    controlled_total_exit_exactly_zero: bool
    decimal_precision_used: int
    envelope_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedJumpRateEnvelope cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ENVELOPE_TOKEN:
            raise TypeError("jump-rate envelopes are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("jump-rate envelope fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("envelope certificate digest is inconsistent")
        for name in (
            "certificate_sha256",
            "intensity_sha256",
            "process_parameter_sha256",
            "source_state_sha256",
            "envelope_sha256",
        ):
            _require_sha256(values[name], name="envelope.%s" % name)
        if values["process_parameter_sha256"] != (certificate.process_parameter_sha256):
            raise ValueError("envelope process digest differs from certificate")
        reverse_time = _validated_float(
            values["reverse_time"],
            name="envelope.reverse_time",
            nonnegative=True,
            canonical_zero=True,
        )
        direct_time = _validated_float(
            values["direct_time"],
            name="envelope.direct_time",
            nonnegative=True,
            canonical_zero=True,
        )
        expected_direct = _canonical_zero(
            certificate.reverse_time_horizon - reverse_time
        )
        if not _same_float(direct_time, expected_direct):
            raise ValueError("envelope direct time is not S minus reverse time")
        for name in (
            "reference_schedule_rate",
            "scheduled_reference_exit_rate",
            "aggregate_edge_magnitude_bound",
            "dominating_real_rate_interval_lower_bound",
            "controlled_total_exit_upper_bound",
            "global_dominating_exit_rate_upper_bound",
        ):
            _validated_float(
                values[name],
                name="envelope.%s" % name,
                nonnegative=True,
            )
        if not _same_float(
            values["aggregate_edge_magnitude_bound"],
            certificate.aggregate_edge_magnitude_bound,
        ):
            raise ValueError("envelope aggregate edge bound differs from certificate")
        exact_bound = _validated_fraction_parts(
            values["exact_log_envelope_bound_numerator"],
            values["exact_log_envelope_bound_denominator"],
            name="envelope exact log bound",
        )
        if exact_bound != _fraction(certificate.aggregate_edge_magnitude_bound):
            raise ValueError("envelope exact log bound is inconsistent")
        (
            expected_lower,
            _,
            expected_upper,
            expected_precision,
        ) = _scaled_exp_outward_envelope(
            exact_bound,
            _fraction(values["scheduled_reference_exit_rate"]),
            name="instantaneous controlled total-exit bound",
        )
        for name, expected in (
            ("dominating_real_rate_interval_lower_bound", expected_lower),
            ("controlled_total_exit_upper_bound", expected_upper),
            (
                "global_dominating_exit_rate_upper_bound",
                certificate.global_dominating_exit_rate_upper_bound,
            ),
        ):
            if not _same_float(values[name], expected):
                raise ValueError("envelope %s is inconsistent" % name)
        if values["controlled_total_exit_upper_bound"] > (
            certificate.global_dominating_exit_rate_upper_bound
        ):
            raise ValueError("instantaneous envelope exceeds the global envelope")
        expected_zero = values["scheduled_reference_exit_rate"] == 0.0
        for name in (
            "reference_intensity_zero",
            "controlled_total_exit_exactly_zero",
        ):
            if type(values[name]) is not bool or values[name] is not expected_zero:
                raise ValueError("envelope %s is inconsistent" % name)
        if expected_zero:
            if expected_upper != 0.0 or expected_precision != 0:
                raise ValueError("zero reference intensity did not short-circuit")
        elif expected_upper < sys.float_info.min:
            raise ValueError("active envelope must be a normal binary64 value")
        if (
            type(values["decimal_precision_used"]) is not int
            or isinstance(values["decimal_precision_used"], bool)
            or values["decimal_precision_used"] != expected_precision
        ):
            raise ValueError("envelope decimal precision is inconsistent")
        expected_digest = _semantic_digest(_envelope_payload(values))
        if values["envelope_sha256"] != expected_digest:
            raise ValueError("envelope digest is inconsistent")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    @property
    def pointwise_candidate_domination_certified(self) -> bool:
        return True

    @property
    def exact_controlled_total_exit_computed(self) -> bool:
        return self.controlled_total_exit_exactly_zero

    @property
    def waiting_time_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("jump-rate envelopes are not pickle objects")


def _envelope_fields() -> Tuple[str, ...]:
    return tuple(TotalizedJumpRateEnvelope.__annotations__)


def _candidate_evaluation_payload(
    values: Mapping[str, object],
) -> Mapping[str, object]:
    omitted = {"certificate", "evaluation_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpRateCandidateEvaluation:
    """Correctly rounded active candidate integrand under one sealed envelope."""

    certificate: TotalizedJumpRateEnvelopeCertificate
    certificate_sha256: str
    envelope_sha256: str
    potential_evaluation_sha256: str
    candidate_sha256: str
    process_parameter_sha256: str
    source_state_sha256: str
    destination_state_sha256: str
    base_context_sha256: str
    residual_context_sha256: str
    reverse_time: float
    direct_time: float
    edit_kind: str
    scheduled_reference_exit_rate: float
    exact_log_increment_numerator: int
    exact_log_increment_denominator: int
    checkpoint17_rounded_log_increment: float
    exact_log_envelope_bound_numerator: int
    exact_log_envelope_bound_denominator: int
    candidate_real_rate_interval_lower_bound: float
    candidate_real_rate_interval_upper_bound: float
    candidate_measure_integrand: float
    controlled_total_exit_upper_bound: float
    global_dominating_exit_rate_upper_bound: float
    decimal_precision_used: int
    guide_fallback_used: bool
    residual_fallback_used: bool
    candidate_integrand_is_normal: bool
    candidate_integrand_dominated: bool
    target_policy: str
    rate_policy: str
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedJumpRateCandidateEvaluation cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError("jump-rate evaluations are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("jump-rate evaluation fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("rate evaluation certificate digest is inconsistent")
        for name in (
            "certificate_sha256",
            "envelope_sha256",
            "potential_evaluation_sha256",
            "candidate_sha256",
            "process_parameter_sha256",
            "source_state_sha256",
            "destination_state_sha256",
            "base_context_sha256",
            "residual_context_sha256",
            "evaluation_sha256",
        ):
            _require_sha256(values[name], name="rate evaluation.%s" % name)
        if values["process_parameter_sha256"] != (certificate.process_parameter_sha256):
            raise ValueError("rate evaluation process digest differs")
        reverse_time = _validated_float(
            values["reverse_time"],
            name="rate evaluation.reverse_time",
            nonnegative=True,
            canonical_zero=True,
        )
        direct_time = _validated_float(
            values["direct_time"],
            name="rate evaluation.direct_time",
            nonnegative=True,
            canonical_zero=True,
        )
        if not _same_float(
            direct_time,
            _canonical_zero(certificate.reverse_time_horizon - reverse_time),
        ):
            raise ValueError("rate evaluation direct time is inconsistent")
        if values["edit_kind"] not in ("birth", "death", "replacement"):
            raise ValueError("rate evaluation edit kind is unknown")
        _validated_float(
            values["scheduled_reference_exit_rate"],
            name="rate evaluation scheduled reference exit",
            strictly_positive=True,
        )
        for name in (
            "checkpoint17_rounded_log_increment",
            "candidate_real_rate_interval_lower_bound",
            "candidate_real_rate_interval_upper_bound",
            "candidate_measure_integrand",
            "controlled_total_exit_upper_bound",
            "global_dominating_exit_rate_upper_bound",
        ):
            _validated_float(
                values[name],
                name="rate evaluation.%s" % name,
                nonnegative=name != "checkpoint17_rounded_log_increment",
                canonical_zero=name == "checkpoint17_rounded_log_increment",
            )
        exact_log = _validated_fraction_parts(
            values["exact_log_increment_numerator"],
            values["exact_log_increment_denominator"],
            name="rate evaluation exact log increment",
        )
        exact_bound = _validated_fraction_parts(
            values["exact_log_envelope_bound_numerator"],
            values["exact_log_envelope_bound_denominator"],
            name="rate evaluation exact log envelope bound",
        )
        if exact_bound != _fraction(certificate.aggregate_edge_magnitude_bound):
            raise ValueError("rate evaluation exact log bound is inconsistent")
        if abs(exact_log) > exact_bound:
            raise ValueError("rate evaluation exact log increment exceeds its bound")
        rounded_log = _rate_round_fraction_once(
            exact_log,
            name="rate evaluation rounded log increment",
        )
        if not _same_float(
            values["checkpoint17_rounded_log_increment"],
            rounded_log,
        ):
            raise ValueError("checkpoint-17 rounded log increment is inconsistent")
        (
            expected_rate,
            expected_lower,
            expected_upper,
            expected_precision,
        ) = _scaled_exp_correctly_rounded_rate(
            exact_log,
            _fraction(values["scheduled_reference_exit_rate"]),
            name="candidate operational measure integrand",
        )
        _, _, expected_envelope, _ = _scaled_exp_outward_envelope(
            exact_bound,
            _fraction(values["scheduled_reference_exit_rate"]),
            name="candidate controlled total-exit bound",
        )
        for name, expected in (
            ("candidate_real_rate_interval_lower_bound", expected_lower),
            ("candidate_real_rate_interval_upper_bound", expected_upper),
            ("candidate_measure_integrand", expected_rate),
            ("controlled_total_exit_upper_bound", expected_envelope),
            (
                "global_dominating_exit_rate_upper_bound",
                certificate.global_dominating_exit_rate_upper_bound,
            ),
        ):
            if not _same_float(values[name], expected):
                raise ValueError("rate evaluation %s is inconsistent" % name)
        if values["candidate_real_rate_interval_upper_bound"] > (
            values["controlled_total_exit_upper_bound"]
        ) or values["controlled_total_exit_upper_bound"] > (
            certificate.global_dominating_exit_rate_upper_bound
        ):
            raise ValueError("candidate rate is not dominated by its envelopes")
        if (
            type(values["decimal_precision_used"]) is not int
            or isinstance(values["decimal_precision_used"], bool)
            or values["decimal_precision_used"] != expected_precision
        ):
            raise ValueError("rate evaluation decimal precision is inconsistent")
        for name, expected in (
            ("guide_fallback_used", values["guide_fallback_used"]),
            ("residual_fallback_used", values["residual_fallback_used"]),
        ):
            if type(expected) is not bool:
                raise TypeError("rate evaluation %s must be boolean" % name)
        for name in (
            "candidate_integrand_is_normal",
            "candidate_integrand_dominated",
        ):
            if type(values[name]) is not bool or values[name] is not True:
                raise ValueError("rate evaluation %s must be true" % name)
        if values["candidate_measure_integrand"] < sys.float_info.min:
            raise ValueError("candidate integrand is not normal")
        if (
            values["target_policy"]
            != (CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY)
            or values["rate_policy"] != CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY
        ):
            raise ValueError("rate evaluation policy is inconsistent")
        expected_digest = _semantic_digest(_candidate_evaluation_payload(values))
        if values["evaluation_sha256"] != expected_digest:
            raise ValueError("rate evaluation digest is inconsistent")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    @property
    def exact_controlled_total_exit_computed(self) -> bool:
        return False

    @property
    def acceptance_decision_admissible(self) -> bool:
        return False

    @property
    def waiting_time_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("jump-rate evaluations are not pickle objects")


def _candidate_evaluation_fields() -> Tuple[str, ...]:
    return tuple(TotalizedJumpRateCandidateEvaluation.__annotations__)


def _require_rate_policy(rate_policy: object) -> str:
    if type(rate_policy) is not str:
        raise TypeError("rate_policy must be exact text")
    if rate_policy != CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY:
        raise ValueError("only the exported operational jump-rate policy is supported")
    return rate_policy


def _field_matches(name: str, supplied: object, expected: object) -> bool:
    if name == "certificate":
        return supplied is expected
    if type(supplied) is float and type(expected) is float:
        return _same_float(supplied, expected)
    return supplied == expected


class TotalizedConfigurationJumpRateEnvelope:
    """Immutable owner of no-RNG domination and active candidate rates."""

    __slots__ = (
        "_potential_composer",
        "_reference_composer",
        "_rate_role_sha256",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedConfigurationJumpRateEnvelope cannot be subclassed")

    def __init__(
        self,
        potential_composer: TotalizedConfigurationJumpPotentialComposer,
        reference_composer: ProcessValidReferenceJumpComposer,
        rate_role_sha256: str,
        certificate: TotalizedJumpRateEnvelopeCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("jump-rate owners require certification")
        if type(potential_composer) is not TotalizedConfigurationJumpPotentialComposer:
            raise TypeError("potential_composer has the wrong exact type")
        if type(reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference_composer has the wrong exact type")
        role = _require_sha256(rate_role_sha256, name="rate_role_sha256")
        if certificate.rate_role_sha256 != role:
            raise ValueError("jump-rate certificate has a different role")
        object.__setattr__(self, "_potential_composer", potential_composer)
        object.__setattr__(self, "_reference_composer", reference_composer)
        object.__setattr__(self, "_rate_role_sha256", role)
        object.__setattr__(self, "_certificate", _validate_certificate(certificate))

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("TotalizedConfigurationJumpRateEnvelope is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("TotalizedConfigurationJumpRateEnvelope is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("jump-rate owners are not pickle objects")

    @property
    def certificate(self) -> TotalizedJumpRateEnvelopeCertificate:
        return self._certificate

    @property
    def potential_composer(self) -> TotalizedConfigurationJumpPotentialComposer:
        return self._potential_composer

    @property
    def reference_composer(self) -> ProcessValidReferenceJumpComposer:
        return self._reference_composer

    def _maximum_reference_exit_rate(self) -> float:
        checkpoint = getattr(self._potential_composer, "_base_checkpoint", None)
        snapshot = getattr(checkpoint, "snapshot", None)
        architecture = getattr(snapshot, "architecture", None)
        maximum = getattr(architecture, "maximum_reference_exit_rate", None)
        return _validated_float(
            maximum,
            name="maximum reference exit rate",
            nonnegative=True,
        )

    def _require_live_binding(self) -> TotalizedJumpRateEnvelopeCertificate:
        _require_binary64_environment()
        if type(self._potential_composer) is not (
            TotalizedConfigurationJumpPotentialComposer
        ):
            raise TypeError("potential composer has the wrong exact type")
        if type(self._reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference composer has the wrong exact type")
        if self._potential_composer.reference_composer is not (
            self._reference_composer
        ):
            raise ValueError("potential and rate owners use different references")
        self._reference_composer._require_live_binding()
        self._potential_composer._live_components()
        potential_certificate = self._potential_composer.certificate
        if potential_certificate.target_policy != (
            CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY
        ):
            raise ValueError("potential composer uses a different target policy")
        if self.certificate.rate_runtime_sha256 != _rate_runtime_sha256():
            raise ValueError("live jump-rate runtime differs from its certificate")
        expected = _make_certificate(
            potential_certificate,
            maximum_reference_exit_rate=self._maximum_reference_exit_rate(),
            rate_role_sha256=self._rate_role_sha256,
        )
        for name in _certificate_fields():
            if not _field_matches(
                name,
                getattr(self.certificate, name),
                getattr(expected, name),
            ):
                raise ValueError(
                    "jump-rate certificate field %s differs from live state" % name
                )
        _require_binary64_environment()
        return self.certificate

    def preflight_envelope(
        self,
        intensity: ReferenceCandidateIntensity,
    ) -> TotalizedJumpRateEnvelope:
        """Certify a dominating rate before any normalized route draw."""

        self._require_live_binding()
        checked = self._reference_composer.validate_candidate_intensity(intensity)
        before_intensity_sha = _intensity_sha256(checked)
        before_source_sha = _configuration_sha256(checked.source_configuration)
        reverse_time = float(checked.reverse_time)
        direct_time = float(checked.direct_time)
        schedule_rate = float(checked.reference_schedule_rate)
        reference_exit = float(checked.scheduled_reference_exit_rate)
        if reference_exit > self.certificate.maximum_reference_exit_rate:
            raise ValueError("reference intensity exceeds the global certificate")
        exact_bound = _fraction(self.certificate.aggregate_edge_magnitude_bound)
        lower, _, upper, precision = _scaled_exp_outward_envelope(
            exact_bound,
            _fraction(reference_exit),
            name="instantaneous controlled total-exit bound",
        )
        if reference_exit > 0.0 and upper < sys.float_info.min:
            raise ConfigurationTotalizedJumpRateError(
                "active controlled total-exit bound is not normal binary64"
            )
        self._require_live_binding()
        rechecked = self._reference_composer.validate_candidate_intensity(intensity)
        after_intensity_sha = _intensity_sha256(rechecked)
        after_source_sha = _configuration_sha256(rechecked.source_configuration)
        if (
            before_intensity_sha != after_intensity_sha
            or before_source_sha != after_source_sha
        ):
            raise ValueError("reference intensity changed during envelope preflight")
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "intensity_sha256": before_intensity_sha,
            "process_parameter_sha256": (self.certificate.process_parameter_sha256),
            "source_state_sha256": before_source_sha,
            "reverse_time": reverse_time,
            "direct_time": direct_time,
            "reference_schedule_rate": schedule_rate,
            "scheduled_reference_exit_rate": reference_exit,
            "aggregate_edge_magnitude_bound": (
                self.certificate.aggregate_edge_magnitude_bound
            ),
            "exact_log_envelope_bound_numerator": exact_bound.numerator,
            "exact_log_envelope_bound_denominator": exact_bound.denominator,
            "dominating_real_rate_interval_lower_bound": lower,
            "controlled_total_exit_upper_bound": upper,
            "global_dominating_exit_rate_upper_bound": (
                self.certificate.global_dominating_exit_rate_upper_bound
            ),
            "reference_intensity_zero": reference_exit == 0.0,
            "controlled_total_exit_exactly_zero": reference_exit == 0.0,
            "decimal_precision_used": precision,
            "envelope_sha256": "0" * 64,
        }
        values["envelope_sha256"] = _semantic_digest(_envelope_payload(values))
        result = TotalizedJumpRateEnvelope(
            **values,
            _construction_token=_ENVELOPE_TOKEN,
        )
        _require_binary64_environment()
        final_intensity_sha = _intensity_sha256(intensity)
        final_source_sha = _configuration_sha256(intensity.source_configuration)
        if (
            before_intensity_sha != final_intensity_sha
            or before_source_sha != final_source_sha
        ):
            raise ValueError("reference intensity changed before envelope return")
        return result

    def validate_envelope(
        self,
        envelope: TotalizedJumpRateEnvelope,
        intensity: ReferenceCandidateIntensity,
    ) -> TotalizedJumpRateEnvelope:
        """Recompute a no-RNG envelope under the same live owner."""

        if type(envelope) is not TotalizedJumpRateEnvelope:
            raise TypeError("envelope must be an exact TotalizedJumpRateEnvelope")
        TotalizedJumpRateEnvelope(
            **{name: getattr(envelope, name) for name in _envelope_fields()},
            _construction_token=_ENVELOPE_TOKEN,
        )
        if envelope.certificate is not self.certificate:
            raise ValueError("envelope belongs to a different jump-rate owner")
        expected = self.preflight_envelope(intensity)
        for name in _envelope_fields():
            if not _field_matches(
                name,
                getattr(envelope, name),
                getattr(expected, name),
            ):
                raise ValueError("envelope field %s differs from replay" % name)
        return envelope

    def evaluate_candidate(
        self,
        candidate: ProcessValidReferenceJump,
        potential_evaluation: TotalizedJumpPotentialCandidateEvaluation,
        *,
        envelope: TotalizedJumpRateEnvelope,
    ) -> TotalizedJumpRateCandidateEvaluation:
        """Exponentiate one validated exact operational edge under its preflight."""

        self._require_live_binding()
        checked_candidate = self._reference_composer.validate_candidate(candidate)
        before_candidate_sha = _candidate_sha256(checked_candidate)
        intensity = self._reference_composer.preflight_candidate_intensity(
            checked_candidate.source_configuration,
            reverse_time=checked_candidate.reverse_time,
        )
        checked_envelope = self.validate_envelope(envelope, intensity)
        if checked_envelope.reference_intensity_zero:
            raise ValueError("an active candidate cannot use a zero-rate envelope")
        envelope_snapshot = {
            name: getattr(checked_envelope, name) for name in _envelope_fields()
        }
        checked_potential = self._potential_composer.validate_evaluation(
            potential_evaluation,
            candidate,
        )
        if checked_potential.certificate is not self._potential_composer.certificate:
            raise ValueError("potential evaluation belongs to a different composer")
        if checked_potential.candidate_sha256 != before_candidate_sha:
            raise ValueError("potential evaluation belongs to a different candidate")
        potential_snapshot = {
            name: getattr(checked_potential, name)
            for name in TotalizedJumpPotentialCandidateEvaluation.__annotations__
        }
        if checked_potential.source_state_sha256 != (
            checked_envelope.source_state_sha256
        ):
            raise ValueError("potential evaluation and envelope use different sources")
        for name in (
            "reverse_time",
            "direct_time",
            "scheduled_reference_exit_rate",
        ):
            if not _same_float(
                getattr(checked_potential, name),
                getattr(checked_envelope, name),
            ):
                raise ValueError("potential evaluation and envelope %s differ" % name)
        exact_log = _validated_fraction_parts(
            potential_snapshot["exact_operational_endpoint_difference_numerator"],
            potential_snapshot["exact_operational_endpoint_difference_denominator"],
            name="authoritative exact operational log increment",
        )
        exact_bound = _fraction(self.certificate.aggregate_edge_magnitude_bound)
        if abs(exact_log) > exact_bound:
            raise ValueError("exact operational log increment exceeds its bound")
        rate, lower, upper, precision = _scaled_exp_correctly_rounded_rate(
            exact_log,
            _fraction(checked_candidate.scheduled_reference_exit_rate),
            name="candidate operational measure integrand",
        )
        if upper > envelope_snapshot["controlled_total_exit_upper_bound"]:
            raise ConfigurationTotalizedJumpRateError(
                "candidate integrand exceeds its preflighted envelope"
            )
        self._potential_composer.validate_evaluation(
            potential_evaluation,
            candidate,
        )
        self.validate_envelope(envelope, intensity)
        self._require_live_binding()
        rechecked_candidate = self._reference_composer.validate_candidate(candidate)
        after_candidate_sha = _candidate_sha256(rechecked_candidate)
        if before_candidate_sha != after_candidate_sha:
            raise ValueError("candidate changed during rate evaluation")
        for name, before in potential_snapshot.items():
            if not _field_matches(name, getattr(potential_evaluation, name), before):
                raise ValueError(
                    "potential evaluation field %s changed during rate evaluation"
                    % name
                )
        for name, before in envelope_snapshot.items():
            if not _field_matches(name, getattr(envelope, name), before):
                raise ValueError(
                    "envelope field %s changed during rate evaluation" % name
                )
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "envelope_sha256": envelope_snapshot["envelope_sha256"],
            "potential_evaluation_sha256": potential_snapshot["evaluation_sha256"],
            "candidate_sha256": before_candidate_sha,
            "process_parameter_sha256": (self.certificate.process_parameter_sha256),
            "source_state_sha256": potential_snapshot["source_state_sha256"],
            "destination_state_sha256": potential_snapshot["destination_state_sha256"],
            "base_context_sha256": potential_snapshot["base_context_sha256"],
            "residual_context_sha256": potential_snapshot["residual_context_sha256"],
            "reverse_time": potential_snapshot["reverse_time"],
            "direct_time": potential_snapshot["direct_time"],
            "edit_kind": potential_snapshot["edit_kind"],
            "scheduled_reference_exit_rate": (
                potential_snapshot["scheduled_reference_exit_rate"]
            ),
            "exact_log_increment_numerator": exact_log.numerator,
            "exact_log_increment_denominator": exact_log.denominator,
            "checkpoint17_rounded_log_increment": (
                potential_snapshot["combined_log_increment"]
            ),
            "exact_log_envelope_bound_numerator": exact_bound.numerator,
            "exact_log_envelope_bound_denominator": exact_bound.denominator,
            "candidate_real_rate_interval_lower_bound": lower,
            "candidate_real_rate_interval_upper_bound": upper,
            "candidate_measure_integrand": rate,
            "controlled_total_exit_upper_bound": (
                envelope_snapshot["controlled_total_exit_upper_bound"]
            ),
            "global_dominating_exit_rate_upper_bound": (
                self.certificate.global_dominating_exit_rate_upper_bound
            ),
            "decimal_precision_used": precision,
            "guide_fallback_used": potential_snapshot["guide_fallback_used"],
            "residual_fallback_used": potential_snapshot["residual_fallback_used"],
            "candidate_integrand_is_normal": True,
            "candidate_integrand_dominated": True,
            "target_policy": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
            "rate_policy": CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
            "evaluation_sha256": "0" * 64,
        }
        values["evaluation_sha256"] = _semantic_digest(
            _candidate_evaluation_payload(values)
        )
        result = TotalizedJumpRateCandidateEvaluation(
            **values,
            _construction_token=_EVALUATION_TOKEN,
        )
        _require_binary64_environment()
        final_candidate_sha = _candidate_sha256(candidate)
        if before_candidate_sha != final_candidate_sha:
            raise ValueError("candidate changed before rate-evaluation return")
        for name, before in potential_snapshot.items():
            if not _field_matches(name, getattr(potential_evaluation, name), before):
                raise ValueError(
                    "potential evaluation field %s changed before return" % name
                )
        for name, before in envelope_snapshot.items():
            if not _field_matches(name, getattr(envelope, name), before):
                raise ValueError("envelope field %s changed before return" % name)
        return result

    def validate_candidate_evaluation(
        self,
        evaluation: TotalizedJumpRateCandidateEvaluation,
        candidate: ProcessValidReferenceJump,
        potential_evaluation: TotalizedJumpPotentialCandidateEvaluation,
        *,
        envelope: TotalizedJumpRateEnvelope,
    ) -> TotalizedJumpRateCandidateEvaluation:
        """Fully replay one candidate-rate record and every supplied parent."""

        if type(evaluation) is not TotalizedJumpRateCandidateEvaluation:
            raise TypeError(
                "evaluation must be an exact TotalizedJumpRateCandidateEvaluation"
            )
        TotalizedJumpRateCandidateEvaluation(
            **{
                name: getattr(evaluation, name)
                for name in _candidate_evaluation_fields()
            },
            _construction_token=_EVALUATION_TOKEN,
        )
        if evaluation.certificate is not self.certificate:
            raise ValueError("evaluation belongs to a different jump-rate owner")
        expected = self.evaluate_candidate(
            candidate,
            potential_evaluation,
            envelope=envelope,
        )
        for name in _candidate_evaluation_fields():
            if not _field_matches(
                name,
                getattr(evaluation, name),
                getattr(expected, name),
            ):
                raise ValueError("rate evaluation field %s differs from replay" % name)
        return evaluation


def certify_totalized_configuration_jump_rate_envelope(
    potential_composer: TotalizedConfigurationJumpPotentialComposer,
    *,
    rate_policy: object,
    rate_role_sha256: object,
) -> TotalizedConfigurationJumpRateEnvelope:
    """Certify rate-space domination for the explicit operational target."""

    _require_rate_policy(rate_policy)
    role = _require_sha256(rate_role_sha256, name="rate_role_sha256")
    if type(potential_composer) is not TotalizedConfigurationJumpPotentialComposer:
        raise TypeError(
            "potential_composer must be an exact "
            "TotalizedConfigurationJumpPotentialComposer"
        )
    potential_composer._live_components()
    reference_composer = potential_composer.reference_composer
    checkpoint = getattr(potential_composer, "_base_checkpoint", None)
    snapshot = getattr(checkpoint, "snapshot", None)
    architecture = getattr(snapshot, "architecture", None)
    maximum_reference_exit_rate = _validated_float(
        getattr(architecture, "maximum_reference_exit_rate", None),
        name="maximum reference exit rate",
        nonnegative=True,
    )
    certificate = _make_certificate(
        potential_composer.certificate,
        maximum_reference_exit_rate=maximum_reference_exit_rate,
        rate_role_sha256=role,
    )
    owner = TotalizedConfigurationJumpRateEnvelope(
        potential_composer,
        reference_composer,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_totalized_configuration_jump_rate_envelope(
    potential_composer: TotalizedConfigurationJumpPotentialComposer,
    owner: TotalizedConfigurationJumpRateEnvelope,
    *,
    rate_policy: object,
    rate_role_sha256: object,
) -> TotalizedConfigurationJumpRateEnvelope:
    """Require exact owner identity and reconstructed live transitive custody."""

    _require_rate_policy(rate_policy)
    role = _require_sha256(rate_role_sha256, name="rate_role_sha256")
    if type(owner) is not TotalizedConfigurationJumpRateEnvelope:
        raise TypeError("owner must be an exact TotalizedConfigurationJumpRateEnvelope")
    if owner.potential_composer is not potential_composer:
        raise ValueError("jump-rate owner is bound to a different potential composer")
    if owner.certificate.rate_role_sha256 != role:
        raise ValueError("jump-rate owner is bound to a different rate role")
    owner._require_live_binding()
    return owner


def validate_totalized_jump_rate_envelope_certificate(
    potential_composer: TotalizedConfigurationJumpPotentialComposer,
    owner: TotalizedConfigurationJumpRateEnvelope,
    *,
    rate_policy: object,
    rate_role_sha256: object,
) -> TotalizedJumpRateEnvelopeCertificate:
    """Return the fully reconstructed live checkpoint-18 certificate."""

    return require_matching_totalized_configuration_jump_rate_envelope(
        potential_composer,
        owner,
        rate_policy=rate_policy,
        rate_role_sha256=rate_role_sha256,
    ).certificate


__all__ = [
    "CONFIGURATION_TOTALIZED_JUMP_RATE_EXPONENTIATION_ALGORITHM",
    "CONFIGURATION_TOTALIZED_JUMP_RATE_FLOATING_POINT_POLICY",
    "CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY",
    "CONFIGURATION_TOTALIZED_JUMP_RATE_SCHEMA_VERSION",
    "CONFIGURATION_TOTALIZED_JUMP_RATE_SCOPE",
    "MAX_TOTALIZED_JUMP_RATE_DECIMAL_COEFFICIENT_DIGITS",
    "TOTALIZED_JUMP_RATE_DECIMAL_AUDIT_PRECISION",
    "TOTALIZED_JUMP_RATE_DECIMAL_MAX_PRECISION",
    "TOTALIZED_JUMP_RATE_DECIMAL_PRIMARY_PRECISION",
    "ConfigurationTotalizedJumpRateError",
    "TotalizedConfigurationJumpRateEnvelope",
    "TotalizedJumpRateCandidateEvaluation",
    "TotalizedJumpRateEnvelope",
    "TotalizedJumpRateEnvelopeCertificate",
    "certify_totalized_configuration_jump_rate_envelope",
    "require_matching_totalized_configuration_jump_rate_envelope",
    "validate_totalized_jump_rate_envelope_certificate",
]
