"""Fail-closed uint64 exponential quotas for arbitrary exact rationals.

For an exact :class:`fractions.Fraction` ``delta <= 0``, this module
certifies

``K(delta) = floor(2**64 * exp(delta))``.

The three terminal branches are proved with rational inequalities alone.
The adaptive branch first encloses ``delta`` by exact finite decimals made by
integer ``divmod``.  Monotonicity transfers that enclosure through ``exp``.
Python's documented correctly-rounded ``Decimal.Context.exp`` result is then
padded on both sides by one adjacent context number.  Conversion of those
finite decimals back to ``Fraction`` is exact.  Precision is doubled until
the rational interval lies in one half-open uint64 cell.

For nonzero rational ``delta``, the Hermite--Lindemann theorem implies that
``2**64 * exp(delta)`` is transcendental and therefore not an integer.  Thus
shrinking exact enclosures have no true integer-boundary tie.  The finite
precision cap remains operational: an unusually close boundary still fails
closed instead of turning theoretical eventual separation into a resource
claim.

This is an exact scaled-floor certificate *under the recorded, trusted
Decimal/libmpdec correctly-rounded-exp contract*.  It is not a formal
verification of libmpdec, a portable cross-runtime certificate, or an exact
Bernoulli(exp(delta)) implementation.  Ambiguity, a changed runtime, a
non-nested enclosure, or a resource-limit breach fails closed.  No binary
floating exponential, NumPy, SciPy, or mpmath is used.

This additive module does not import or modify the frozen CP50-v1 decision
implementation.  Kernel-v2 integration is intentionally a separate step.
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
from typing import Dict, Mapping, Tuple


ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCHEMA_VERSION = (
    "arbitrary-rational-uint64-exp-quota-v1"
)
ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_POLICY = (
    "exact-Fraction-nonpositive-gap;terminal-rational-inequalities;"
    "exact-divmod-outward-decimal-input-bracket;monotone-exp-transfer;"
    "trusted-correctly-rounded-Decimal-exp;adjacent-context-outward-padding;"
    "adaptive-nested-rational-exp-enclosures;unique-scaled-half-open-cell;"
    "recompute-every-field-validation;fail-closed-resource-or-ambiguity-v1"
)
ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_PROOF_CONTRACT = (
    "delta=0 is exact unity;delta<=-64 uses e>2;"
    "-2^-64<delta<0 uses 1+delta<exp(delta)<1;"
    "otherwise integer-divmod gives exact finite-decimal x_lo<=delta<=x_hi;"
    "exp monotonicity and documented correctly-rounded Decimal Context.exp,"
    "padded by next_minus/next_plus, give strict rational L<exp(delta)<U;"
    "nested L,U with floor(2^64*L)=k and 2^64*U<=k+1 prove the exact floor;"
    "Hermite-Lindemann excludes an exact scaled integer tie for nonzero "
    "rational delta but finite precision exhaustion still fails closed;"
    "adaptive claims are conditional on the recorded trusted unchanged "
    "Python-Decimal-libmpdec contract and are not formal verification"
)
ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCOPE = (
    "standalone-exact-scaled-floor-certificate-under-frozen-decimal-contract;"
    "arbitrary-bounded-exact-rational-delta;no-binary64-exp;no-external-"
    "numeric-dependency;not-runtime-portable;not-formal-libmpdec-verification;"
    "not-exact-exp-bernoulli;not-rejection-kernel-integration;"
    "not-initializer-target-path-sampler-or-test28-admission"
)

UINT64_EXP_QUOTA_DENOMINATOR = 1 << 64
UINT64_EXP_QUOTA_PRIMARY_PRECISION = 192
UINT64_EXP_QUOTA_MAX_PRECISION = 3_072
UINT64_EXP_QUOTA_ZERO_CUTOFF = -64
UINT64_EXP_QUOTA_MAX_INPUT_INTEGER_BITS = 16_384
UINT64_EXP_QUOTA_MAX_DECIMAL_COEFFICIENT_DIGITS = 16_384
UINT64_EXP_QUOTA_MAX_TEXT_LENGTH = 16_384

_D = UINT64_EXP_QUOTA_DENOMINATOR
_MAX_CERTIFICATE_INTEGER_BITS = 2 * UINT64_EXP_QUOTA_MAX_INPUT_INTEGER_BITS
_DECIMAL_MIN_EXPONENT = -999_999
_DECIMAL_MAX_EXPONENT = 999_999
_CERTIFICATE_TOKEN = object()


class ArbitraryRationalUInt64ExpQuotaError(ArithmeticError):
    """Fail-closed quota certification error."""


def _require_exact_text(value: object, *, name: str, expected: str = "") -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > UINT64_EXP_QUOTA_MAX_TEXT_LENGTH:
        raise ArbitraryRationalUInt64ExpQuotaError(
            "%s exceeds the text resource limit" % name
        )
    if expected and value != expected:
        raise ValueError("%s differs" % name)
    return value


def _require_sha256(value: object, *, name: str) -> str:
    checked = _require_exact_text(value, name=name)
    if len(checked) != 64 or any(c not in "0123456789abcdef" for c in checked):
        raise ValueError("%s must be lowercase SHA-256 text" % name)
    return checked


def _require_certificate_integer(
    value: object,
    *,
    name: str,
    positive: bool = False,
    maximum: int = -1,
) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if positive and value <= 0:
        raise ValueError("%s must be positive" % name)
    if maximum >= 0 and not 0 <= value <= maximum:
        raise ValueError("%s lies outside the certified range" % name)
    if value.bit_length() > _MAX_CERTIFICATE_INTEGER_BITS:
        raise ArbitraryRationalUInt64ExpQuotaError(
            "%s exceeds the certificate-integer resource limit" % name
        )
    return value


def _require_exact_integer_bits(value: object, *, name: str, positive: bool) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if positive and value <= 0:
        raise ValueError("%s must be positive" % name)
    if value.bit_length() > UINT64_EXP_QUOTA_MAX_INPUT_INTEGER_BITS:
        raise ArbitraryRationalUInt64ExpQuotaError(
            "%s exceeds the exact-integer resource limit" % name
        )
    return value


def _require_delta(value: object) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError("delta must be an exact Fraction")
    numerator = _require_exact_integer_bits(
        value.numerator, name="delta numerator", positive=False
    )
    denominator = _require_exact_integer_bits(
        value.denominator, name="delta denominator", positive=True
    )
    if Fraction(numerator, denominator) != value:
        raise ValueError("delta must be stored in reduced form")
    if value > 0:
        raise ValueError("delta must be nonpositive")
    return value


def _precision_schedule() -> Tuple[int, ...]:
    values = []
    precision = UINT64_EXP_QUOTA_PRIMARY_PRECISION
    while precision < UINT64_EXP_QUOTA_MAX_PRECISION:
        values.append(precision)
        precision *= 2
    values.append(UINT64_EXP_QUOTA_MAX_PRECISION)
    return tuple(values)


def _decimal_context(precision: int) -> Context:
    if type(precision) is not int or precision not in _precision_schedule():
        raise ValueError("precision is outside the frozen schedule")
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


def _nonnegative_decimal_digits(value: int, *, name: str) -> Tuple[int, ...]:
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise TypeError("%s must be a nonnegative exact integer" % name)
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
    if digit_count > UINT64_EXP_QUOTA_MAX_DECIMAL_COEFFICIENT_DIGITS:
        raise ArbitraryRationalUInt64ExpQuotaError(
            "%s exceeds the decimal-coefficient resource limit" % name
        )
    digits = list(first_digits)
    for block in blocks[1:]:
        divisor = 100_000_000
        while divisor:
            digit, block = divmod(block, divisor)
            digits.append(digit)
            divisor //= 10
    return tuple(digits)


def _scaled_integer_decimal(coefficient: int, places: int, *, name: str) -> Decimal:
    if type(coefficient) is not int or isinstance(coefficient, bool):
        raise TypeError("%s coefficient must be an exact integer" % name)
    if type(places) is not int or places not in _precision_schedule():
        raise ValueError("%s places differ from the frozen schedule" % name)
    digits = _nonnegative_decimal_digits(abs(coefficient), name=name)
    value = Decimal((1 if coefficient < 0 else 0, digits, -places))
    if not value.is_finite():
        raise ArbitraryRationalUInt64ExpQuotaError(
            "%s finite decimal construction failed" % name
        )
    return value


def _outward_decimal_input_enclosure(
    delta: Fraction, precision: int
) -> Tuple[Decimal, Decimal, Fraction, Fraction]:
    scale = 10**precision
    scaled_numerator = delta.numerator * scale
    lower_coefficient, remainder = divmod(scaled_numerator, delta.denominator)
    upper_coefficient = lower_coefficient if remainder == 0 else lower_coefficient + 1
    lower_decimal = _scaled_integer_decimal(
        lower_coefficient, precision, name="input lower"
    )
    upper_decimal = _scaled_integer_decimal(
        upper_coefficient, precision, name="input upper"
    )
    lower = Fraction(lower_coefficient, scale)
    upper = Fraction(upper_coefficient, scale)
    if not lower <= delta <= upper:
        raise ArbitraryRationalUInt64ExpQuotaError(
            "exact rational input enclosure is invalid"
        )
    if Fraction(lower_decimal) != lower or Fraction(upper_decimal) != upper:
        raise ArbitraryRationalUInt64ExpQuotaError(
            "Decimal input construction changed an exact endpoint"
        )
    return lower_decimal, upper_decimal, lower, upper


def _adaptive_exp_enclosure(
    delta: Fraction, precision: int
) -> Tuple[Fraction, Fraction, Fraction, Fraction]:
    (
        lower_decimal,
        upper_decimal,
        input_lower,
        input_upper,
    ) = _outward_decimal_input_enclosure(delta, precision)
    context = _decimal_context(precision)
    try:
        rounded_lower = context.exp(lower_decimal)
        rounded_upper = context.exp(upper_decimal)
        exp_lower_decimal = context.next_minus(rounded_lower)
        exp_upper_decimal = context.next_plus(rounded_upper)
    except decimal.DecimalException as error:
        raise ArbitraryRationalUInt64ExpQuotaError(
            "Decimal exponential could not be outwardly enclosed"
        ) from error
    values = (
        rounded_lower,
        rounded_upper,
        exp_lower_decimal,
        exp_upper_decimal,
    )
    if any(not value.is_finite() for value in values):
        raise ArbitraryRationalUInt64ExpQuotaError(
            "Decimal exponential enclosure is nonfinite"
        )
    exp_lower = Fraction(exp_lower_decimal)
    exp_upper = Fraction(exp_upper_decimal)
    if not Fraction(0) < exp_lower < exp_upper < Fraction(1):
        raise ArbitraryRationalUInt64ExpQuotaError(
            "Decimal exponential enclosure escaped (0,1)"
        )
    return input_lower, input_upper, exp_lower, exp_upper


def _runtime_sha256() -> str:
    payload = {
        "python_implementation": sys.implementation.name,
        "python_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "decimal_version": getattr(decimal, "__version__", "unknown"),
        "libmpdec_version": getattr(decimal, "__libmpdec_version__", "unknown"),
        "schema": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCHEMA_VERSION,
        "policy": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_POLICY,
        "proof_contract": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_PROOF_CONTRACT,
        "constants": {
            "denominator": _D,
            "primary_precision": UINT64_EXP_QUOTA_PRIMARY_PRECISION,
            "maximum_precision": UINT64_EXP_QUOTA_MAX_PRECISION,
            "zero_cutoff": UINT64_EXP_QUOTA_ZERO_CUTOFF,
            "maximum_input_integer_bits": (UINT64_EXP_QUOTA_MAX_INPUT_INTEGER_BITS),
            "maximum_decimal_coefficient_digits": (
                UINT64_EXP_QUOTA_MAX_DECIMAL_COEFFICIENT_DIGITS
            ),
            "decimal_min_exponent": _DECIMAL_MIN_EXPONENT,
            "decimal_max_exponent": _DECIMAL_MAX_EXPONENT,
            "precision_schedule": _precision_schedule(),
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(
        b"heterodiff-arbitrary-rational-uint64-exp-quota-runtime-v1\x00" + encoded
    ).hexdigest()


def _typed_digest_value(value: object) -> object:
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return [
            "integer-hex-v1",
            "negative" if value < 0 else "nonnegative",
            format(abs(value), "x"),
        ]
    if type(value) is str:
        if len(value) > UINT64_EXP_QUOTA_MAX_TEXT_LENGTH:
            raise ValueError("digest text exceeds the resource limit")
        return ["string-v1", value]
    raise TypeError("unsupported quota digest field type")


def _certificate_sha256(values: Mapping[str, object]) -> str:
    items = [
        (name, _typed_digest_value(value))
        for name, value in sorted(values.items())
        if name != "certificate_sha256"
    ]
    encoded = json.dumps(items, ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )
    return hashlib.sha256(
        b"heterodiff-arbitrary-rational-uint64-exp-quota-certificate-v1\x00" + encoded
    ).hexdigest()


@dataclass(frozen=True, eq=False, init=False)
class ArbitraryRationalUInt64ExpQuotaCertificate:
    """Sealed, replay-validated certificate for one exact uint64 quota."""

    schema_version: str
    certificate_scope: str
    proof_policy: str
    proof_contract: str
    delta_numerator: int
    delta_denominator: int
    branch: str
    precision: int
    adaptive_rounds: int
    decision_denominator: int
    quota: int
    input_lower_numerator: int
    input_lower_denominator: int
    input_upper_numerator: int
    input_upper_denominator: int
    exp_lower_numerator: int
    exp_lower_denominator: int
    exp_upper_numerator: int
    exp_upper_denominator: int
    input_lower_strict: bool
    input_upper_strict: bool
    exp_lower_strict: bool
    exp_upper_strict: bool
    terminal_rational_inequality_certified: bool
    exact_divmod_input_enclosure_certified: bool
    exponential_monotonicity_transfer_certified: bool
    adjacent_decimal_outward_padding_certified: bool
    adaptive_nested_enclosures_certified: bool
    unique_scaled_floor_certified: bool
    exact_scaled_floor_under_stated_contract_certified: bool
    decimal_correct_rounding_contract_required: bool
    decimal_implementation_formally_verified: bool
    independent_transcendental_backend_verified: bool
    binary_float_exp_used: bool
    external_numeric_dependency_used: bool
    exact_exponential_bernoulli_certified: bool
    rejection_kernel_integrated: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    runtime_sha256: str
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("quota certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("quota certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("quota certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate_fields(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("quota certificates are not pickle objects")


def _fraction_fields(prefix: str, value: Fraction) -> Dict[str, int]:
    return {
        prefix + "_numerator": value.numerator,
        prefix + "_denominator": value.denominator,
    }


def _compute_values(delta: Fraction) -> Dict[str, object]:
    checked = _require_delta(delta)
    branch: str
    precision = 0
    adaptive_rounds = 0
    input_lower = checked
    input_upper = checked
    if checked == 0:
        branch = "unity"
        exp_lower = Fraction(1)
        exp_upper = Fraction(1)
        quota = _D
        input_lower_strict = False
        input_upper_strict = False
        exp_lower_strict = False
        exp_upper_strict = False
        decimal_contract_required = False
    elif checked <= UINT64_EXP_QUOTA_ZERO_CUTOFF:
        branch = "below_uint64_resolution"
        exp_lower = Fraction(0)
        exp_upper = Fraction(1, _D)
        quota = 0
        input_lower_strict = False
        input_upper_strict = False
        exp_lower_strict = True
        exp_upper_strict = True
        decimal_contract_required = False
    elif checked > Fraction(-1, _D):
        branch = "below_one_uint64_cell"
        exp_lower = Fraction(_D - 1, _D)
        exp_upper = Fraction(1)
        quota = _D - 1
        input_lower_strict = False
        input_upper_strict = False
        exp_lower_strict = True
        exp_upper_strict = True
        decimal_contract_required = False
    else:
        branch = "adaptive_decimal_rational_input"
        previous = None
        quota = -1
        for adaptive_rounds, precision in enumerate(_precision_schedule(), start=1):
            (
                input_lower,
                input_upper,
                exp_lower,
                exp_upper,
            ) = _adaptive_exp_enclosure(checked, precision)
            if previous is not None and not (
                previous[0] <= exp_lower <= exp_upper <= previous[1]
            ):
                raise ArbitraryRationalUInt64ExpQuotaError(
                    "adaptive exponential enclosures are not nested"
                )
            previous = (exp_lower, exp_upper)
            scaled_lower = _D * exp_lower
            scaled_upper = _D * exp_upper
            candidate = scaled_lower.numerator // scaled_lower.denominator
            if scaled_lower >= candidate and scaled_upper <= candidate + 1:
                if not 0 <= candidate < _D:
                    raise ArbitraryRationalUInt64ExpQuotaError(
                        "adaptive quota escaped the uint64 domain"
                    )
                quota = candidate
                break
        if quota < 0:
            raise ArbitraryRationalUInt64ExpQuotaError(
                "arbitrary-rational exponential quota is precision-ambiguous"
            )
        input_lower_strict = input_lower < checked
        input_upper_strict = checked < input_upper
        exp_lower_strict = True
        exp_upper_strict = True
        decimal_contract_required = True

    values: Dict[str, object] = {
        "schema_version": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCHEMA_VERSION,
        "certificate_scope": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCOPE,
        "proof_policy": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_POLICY,
        "proof_contract": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_PROOF_CONTRACT,
        "delta_numerator": checked.numerator,
        "delta_denominator": checked.denominator,
        "branch": branch,
        "precision": precision,
        "adaptive_rounds": adaptive_rounds,
        "decision_denominator": _D,
        "quota": quota,
        "input_lower_strict": input_lower_strict,
        "input_upper_strict": input_upper_strict,
        "exp_lower_strict": exp_lower_strict,
        "exp_upper_strict": exp_upper_strict,
        "terminal_rational_inequality_certified": (not decimal_contract_required),
        "exact_divmod_input_enclosure_certified": (decimal_contract_required),
        "exponential_monotonicity_transfer_certified": (decimal_contract_required),
        "adjacent_decimal_outward_padding_certified": (decimal_contract_required),
        "adaptive_nested_enclosures_certified": decimal_contract_required,
        "unique_scaled_floor_certified": True,
        "exact_scaled_floor_under_stated_contract_certified": True,
        "decimal_correct_rounding_contract_required": (decimal_contract_required),
        "decimal_implementation_formally_verified": False,
        "independent_transcendental_backend_verified": False,
        "binary_float_exp_used": False,
        "external_numeric_dependency_used": False,
        "exact_exponential_bernoulli_certified": False,
        "rejection_kernel_integrated": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "runtime_sha256": _runtime_sha256(),
    }
    values.update(_fraction_fields("input_lower", input_lower))
    values.update(_fraction_fields("input_upper", input_upper))
    values.update(_fraction_fields("exp_lower", exp_lower))
    values.update(_fraction_fields("exp_upper", exp_upper))
    values["certificate_sha256"] = _certificate_sha256(values)
    return values


def certify_arbitrary_rational_uint64_exp_quota(
    delta: Fraction,
) -> ArbitraryRationalUInt64ExpQuotaCertificate:
    """Return a sealed exact scaled-floor certificate or fail closed."""

    values = _compute_values(delta)
    return ArbitraryRationalUInt64ExpQuotaCertificate(
        _construction_token=_CERTIFICATE_TOKEN, **values
    )


_CERTIFICATE_BOOLEAN_FIELDS = (
    "input_lower_strict",
    "input_upper_strict",
    "exp_lower_strict",
    "exp_upper_strict",
    "terminal_rational_inequality_certified",
    "exact_divmod_input_enclosure_certified",
    "exponential_monotonicity_transfer_certified",
    "adjacent_decimal_outward_padding_certified",
    "adaptive_nested_enclosures_certified",
    "unique_scaled_floor_certified",
    "exact_scaled_floor_under_stated_contract_certified",
    "decimal_correct_rounding_contract_required",
    "decimal_implementation_formally_verified",
    "independent_transcendental_backend_verified",
    "binary_float_exp_used",
    "external_numeric_dependency_used",
    "exact_exponential_bernoulli_certified",
    "rejection_kernel_integrated",
    "runtime_portable",
    "cryptographic_authentication",
)
_CERTIFICATE_ENDPOINT_PREFIXES = (
    "input_lower",
    "input_upper",
    "exp_lower",
    "exp_upper",
)
_CERTIFICATE_BRANCHES = (
    "unity",
    "below_uint64_resolution",
    "below_one_uint64_cell",
    "adaptive_decimal_rational_input",
)


def _preflight_certificate_fields(
    certificate: ArbitraryRationalUInt64ExpQuotaCertificate,
) -> None:
    expected_texts = {
        "schema_version": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCHEMA_VERSION,
        "certificate_scope": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCOPE,
        "proof_policy": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_POLICY,
        "proof_contract": ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_PROOF_CONTRACT,
    }
    for name, expected in expected_texts.items():
        _require_exact_text(
            getattr(certificate, name), name="certificate.%s" % name, expected=expected
        )
    branch = _require_exact_text(certificate.branch, name="certificate.branch")
    if branch not in _CERTIFICATE_BRANCHES:
        raise ValueError("certificate.branch is unknown")
    _require_sha256(certificate.runtime_sha256, name="certificate.runtime_sha256")
    _require_sha256(
        certificate.certificate_sha256, name="certificate.certificate_sha256"
    )
    _require_exact_integer_bits(
        certificate.delta_numerator,
        name="certificate delta numerator",
        positive=False,
    )
    _require_exact_integer_bits(
        certificate.delta_denominator,
        name="certificate delta denominator",
        positive=True,
    )
    precision = _require_certificate_integer(
        certificate.precision, name="certificate.precision", maximum=10_000
    )
    if precision not in (0,) + _precision_schedule():
        raise ValueError("certificate.precision differs from the frozen schedule")
    _require_certificate_integer(
        certificate.adaptive_rounds,
        name="certificate.adaptive_rounds",
        maximum=len(_precision_schedule()),
    )
    denominator = _require_certificate_integer(
        certificate.decision_denominator,
        name="certificate.decision_denominator",
        positive=True,
    )
    if denominator != _D:
        raise ValueError("certificate.decision_denominator differs")
    _require_certificate_integer(
        certificate.quota, name="certificate.quota", maximum=_D
    )
    for prefix in _CERTIFICATE_ENDPOINT_PREFIXES:
        _require_certificate_integer(
            getattr(certificate, prefix + "_numerator"),
            name="certificate.%s_numerator" % prefix,
        )
        _require_certificate_integer(
            getattr(certificate, prefix + "_denominator"),
            name="certificate.%s_denominator" % prefix,
            positive=True,
        )
    for name in _CERTIFICATE_BOOLEAN_FIELDS:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be an exact Boolean" % name)


def _validate_certificate_fields(
    certificate: object,
) -> ArbitraryRationalUInt64ExpQuotaCertificate:
    if type(certificate) is not ArbitraryRationalUInt64ExpQuotaCertificate:
        raise TypeError("certificate has the wrong exact quota type")
    _preflight_certificate_fields(certificate)
    numerator = _require_exact_integer_bits(
        certificate.delta_numerator, name="certificate delta numerator", positive=False
    )
    denominator = _require_exact_integer_bits(
        certificate.delta_denominator,
        name="certificate delta denominator",
        positive=True,
    )
    delta = Fraction(numerator, denominator)
    if delta.numerator != numerator or delta.denominator != denominator:
        raise ValueError("certificate delta is not stored in reduced form")
    expected = _compute_values(delta)
    for name in ArbitraryRationalUInt64ExpQuotaCertificate.__annotations__:
        actual = getattr(certificate, name)
        wanted = expected[name]
        if type(actual) is not type(wanted) or actual != wanted:
            raise ValueError("certificate.%s differs from exact replay" % name)
    return certificate


def validate_arbitrary_rational_uint64_exp_quota_certificate(
    certificate: object,
) -> ArbitraryRationalUInt64ExpQuotaCertificate:
    """Recompute every field under the current runtime and reject tampering."""

    return _validate_certificate_fields(certificate)


__all__ = (
    "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_POLICY",
    "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_PROOF_CONTRACT",
    "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCHEMA_VERSION",
    "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCOPE",
    "ArbitraryRationalUInt64ExpQuotaCertificate",
    "ArbitraryRationalUInt64ExpQuotaError",
    "UINT64_EXP_QUOTA_DENOMINATOR",
    "UINT64_EXP_QUOTA_MAX_DECIMAL_COEFFICIENT_DIGITS",
    "UINT64_EXP_QUOTA_MAX_INPUT_INTEGER_BITS",
    "UINT64_EXP_QUOTA_MAX_PRECISION",
    "UINT64_EXP_QUOTA_PRIMARY_PRECISION",
    "UINT64_EXP_QUOTA_ZERO_CUTOFF",
    "certify_arbitrary_rational_uint64_exp_quota",
    "validate_arbitrary_rational_uint64_exp_quota_certificate",
)
