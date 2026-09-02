"""Exact symbolic two-domain count-normalized-event CKS instance.

This module defines the prospective metric input spaces for the PhysioNet
Challenge 2012 and Online Retail II domains.  It performs no I/O, fitting,
randomness, numerical exponential evaluation, data access, or scientific run.
All Gaussian values remain exact symbolic objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
import math
import re
import unicodedata
from typing import Dict, Mapping, Optional, Sequence, Tuple


PRIMARY_METRIC_ID = "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
PHYSIONET_DOMAIN_ID = "R3-PHYS"
RETAIL_DOMAIN_ID = "R4-RETAIL"

PHYSIONET_HORIZON_MINUTES = 2880
PHYSIONET_CONFIGURATION_CAP = 131072
RETAIL_HORIZON_SECONDS = 63849600
RETAIL_HORIZON_MICROSECONDS = RETAIL_HORIZON_SECONDS * 1_000_000
RETAIL_CONFIGURATION_CAP = 1067371

PHYSIONET_PARAMETERS: Tuple[str, ...] = (
    "Albumin",
    "ALP",
    "ALT",
    "AST",
    "Bilirubin",
    "BUN",
    "Cholesterol",
    "Creatinine",
    "DiasABP",
    "FiO2",
    "GCS",
    "Glucose",
    "HCO3",
    "HCT",
    "HR",
    "K",
    "Lactate",
    "Mg",
    "MAP",
    "MechVent",
    "Na",
    "NIDiasABP",
    "NIMAP",
    "NISysABP",
    "PaCO2",
    "PaO2",
    "pH",
    "Platelets",
    "RespRate",
    "SaO2",
    "SysABP",
    "Temp",
    "TropI",
    "TropT",
    "Urine",
    "WBC",
    "Weight",
)

PHYSIONET_UNITS: Mapping[str, str] = {
    "Albumin": "g/dL",
    "ALP": "IU/L",
    "ALT": "IU/L",
    "AST": "IU/L",
    "Bilirubin": "mg/dL",
    "BUN": "mg/dL",
    "Cholesterol": "mg/dL",
    "Creatinine": "mg/dL",
    "DiasABP": "mmHg",
    "FiO2": "fraction",
    "GCS": "score",
    "Glucose": "mg/dL",
    "HCO3": "mmol/L",
    "HCT": "percent",
    "HR": "bpm",
    "K": "mEq/L",
    "Lactate": "mmol/L",
    "Mg": "mmol/L",
    "MAP": "mmHg",
    "MechVent": "binary",
    "Na": "mEq/L",
    "NIDiasABP": "mmHg",
    "NIMAP": "mmHg",
    "NISysABP": "mmHg",
    "PaCO2": "mmHg",
    "PaO2": "mmHg",
    "pH": "pH",
    "Platelets": "cells/nL",
    "RespRate": "bpm",
    "SaO2": "percent",
    "SysABP": "mmHg",
    "Temp": "degC",
    "TropI": "ug/L",
    "TropT": "ug/L",
    "Urine": "mL",
    "WBC": "cells/nL",
    "Weight": "kg",
}

_PHYSIONET_PARAMETER_INDEX = {
    name: index for index, name in enumerate(PHYSIONET_PARAMETERS)
}
_DECIMAL_TOKEN = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?\Z")
_SIX_DIGITS = re.compile(r"[0-9]{6}\Z")
_CUSTOMER_DIGITS = re.compile(r"[1-9][0-9]{0,4}\Z")
_RETAIL_START = datetime(2009, 12, 1, 0, 0, 0)
_RETAIL_END_EXCLUSIVE = datetime(2011, 12, 10, 0, 0, 0)


class CKSInstanceError(ValueError):
    """Raised when an input is outside the frozen two-domain metric space."""


def _exact_fraction(value: object, *, label: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(f"{label} must be an exact Fraction")
    return value


def _positive_fraction(value: object, *, label: str) -> Fraction:
    result = _exact_fraction(value, label=label)
    if result <= 0:
        raise ValueError(f"{label} must be positive")
    return result


def _plain_token(value: object, *, label: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{label} must be an exact string")
    if not value or value != value.strip():
        raise CKSInstanceError(f"{label} must be nonempty and whitespace-trimmed")
    if unicodedata.normalize("NFC", value) != value:
        raise CKSInstanceError(f"{label} must be NFC-normalized")
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise CKSInstanceError(f"{label} must not contain NUL or newlines")
    return value


def _fraction_from_decimal_token(value: object, *, label: str) -> Fraction:
    if type(value) is not str:
        raise TypeError(f"{label} must be an exact string")
    if len(value) > 256:
        raise CKSInstanceError(f"{label} exceeds the decimal resource bound")
    token = _plain_token(value, label=label)
    if _DECIMAL_TOKEN.fullmatch(token) is None:
        raise CKSInstanceError(f"{label} is not a plain decimal token")
    if len(token) > 256:
        raise CKSInstanceError(f"{label} exceeds the decimal resource bound")
    sign = -1 if token.startswith("-") else 1
    unsigned = token[1:] if token[:1] in "+-" else token
    if "." in unsigned:
        integer, fractional = unsigned.split(".", 1)
        numerator = int(integer + fractional)
        denominator = 10 ** len(fractional)
    else:
        numerator = int(unsigned)
        denominator = 1
    return Fraction(sign * numerator, denominator)


def _fraction_from_binary64(value: object, *, label: str) -> Fraction:
    if type(value) is not float:
        raise TypeError(f"{label} must be an exact binary64 float")
    if not math.isfinite(value):
        raise CKSInstanceError(f"{label} must be finite")
    if value == 0.0:
        value = 0.0
    numerator, denominator = value.as_integer_ratio()
    return Fraction(numerator, denominator)


def _bounded_signed(value: Fraction) -> Fraction:
    """Injectively map an exact real input to the open interval (-1, 1)."""

    return value / (1 + abs(value))


@dataclass(frozen=True)
class DomainCKSSpec:
    domain_id: str
    coordinate_dimension: int
    configuration_cap: int
    event_tau2: Fraction
    count_scale2: Fraction
    event_scale2: Fraction
    outer_sigma2: Fraction

    def __post_init__(self) -> None:
        if self.domain_id not in (PHYSIONET_DOMAIN_ID, RETAIL_DOMAIN_ID):
            raise ValueError("domain_id is not one of the frozen domains")
        for name in ("coordinate_dimension", "configuration_cap"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise TypeError(f"{name} must be a positive exact integer")
        for name in (
            "event_tau2",
            "count_scale2",
            "event_scale2",
            "outer_sigma2",
        ):
            _positive_fraction(getattr(self, name), label=name)


PHYSIONET_SPEC = DomainCKSSpec(
    domain_id=PHYSIONET_DOMAIN_ID,
    coordinate_dimension=112,
    configuration_cap=PHYSIONET_CONFIGURATION_CAP,
    event_tau2=Fraction(1),
    count_scale2=Fraction(1),
    event_scale2=Fraction(1),
    outer_sigma2=Fraction(1),
)
RETAIL_SPEC = DomainCKSSpec(
    domain_id=RETAIL_DOMAIN_ID,
    coordinate_dimension=10,
    configuration_cap=RETAIL_CONFIGURATION_CAP,
    event_tau2=Fraction(1),
    count_scale2=Fraction(1),
    event_scale2=Fraction(1),
    outer_sigma2=Fraction(1),
)
DOMAIN_SPECS: Mapping[str, DomainCKSSpec] = {
    PHYSIONET_DOMAIN_ID: PHYSIONET_SPEC,
    RETAIL_DOMAIN_ID: RETAIL_SPEC,
}


@dataclass(frozen=True, order=True)
class ExactEvent:
    """One exact transformed event with no identifier or provenance state."""

    domain_id: str
    coordinates: Tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if type(self.domain_id) is not str or self.domain_id not in DOMAIN_SPECS:
            raise ValueError("event domain_id is not frozen")
        if type(self.coordinates) is not tuple:
            raise TypeError("coordinates must be an exact tuple")
        spec = DOMAIN_SPECS[self.domain_id]
        if len(self.coordinates) != spec.coordinate_dimension:
            raise ValueError("event coordinate dimension disagrees with its domain")
        for coordinate in self.coordinates:
            _exact_fraction(coordinate, label="event coordinate")


@dataclass(frozen=True)
class ExactConfiguration:
    """A canonical occurrence-expanded finite counting measure."""

    domain_id: str
    events: Tuple[ExactEvent, ...] = ()

    def __post_init__(self) -> None:
        if type(self.domain_id) is not str or self.domain_id not in DOMAIN_SPECS:
            raise ValueError("configuration domain_id is not frozen")
        if type(self.events) is not tuple:
            raise TypeError("events must be an exact tuple")
        if any(type(event) is not ExactEvent for event in self.events):
            raise TypeError("events must contain exact ExactEvent values")
        if any(event.domain_id != self.domain_id for event in self.events):
            raise ValueError("an event belongs to another domain")
        validate_configuration_count(self.domain_id, len(self.events))
        object.__setattr__(self, "events", tuple(sorted(self.events)))


def validate_configuration_count(domain_id: object, count: object) -> int:
    if type(domain_id) is not str or domain_id not in DOMAIN_SPECS:
        raise ValueError("domain_id is not frozen")
    if type(count) is not int:
        raise TypeError("configuration count must be an exact integer")
    if count < 0:
        raise CKSInstanceError("configuration count must be nonnegative")
    if count > DOMAIN_SPECS[domain_id].configuration_cap:
        raise CKSInstanceError("configuration cap exceeded: terminal domain nonadmission")
    return count


def _physionet_coordinates(
    elapsed_minutes: object,
    parameter: object,
    value: Optional[Fraction],
) -> Tuple[Fraction, ...]:
    if type(elapsed_minutes) is not int:
        raise TypeError("elapsed_minutes must be an exact integer")
    if not 0 <= elapsed_minutes <= PHYSIONET_HORIZON_MINUTES:
        raise CKSInstanceError("elapsed_minutes is outside 0..2880")
    if type(parameter) is not str or parameter not in _PHYSIONET_PARAMETER_INDEX:
        raise CKSInstanceError("parameter is outside the frozen 37-variable roster")
    index = _PHYSIONET_PARAMETER_INDEX[parameter]
    one_hot = tuple(
        Fraction(1 if position == index else 0)
        for position in range(len(PHYSIONET_PARAMETERS))
    )
    if value is None:
        present = Fraction(0)
        transformed = Fraction(0)
    else:
        value = _exact_fraction(value, label="PhysioNet value")
        if value < 0:
            raise CKSInstanceError("a present PhysioNet value must be nonnegative")
        present = Fraction(1)
        transformed = value / (1 + value)
    mask_block = tuple(present if position == index else Fraction(0) for position in range(37))
    value_block = tuple(
        transformed if position == index else Fraction(0) for position in range(37)
    )
    return (
        one_hot
        + (Fraction(elapsed_minutes, PHYSIONET_HORIZON_MINUTES),)
        + mask_block
        + value_block
    )


def physionet_event_from_decimal_token(
    *, elapsed_minutes: object, parameter: object, value_text: object
) -> ExactEvent:
    value = _fraction_from_decimal_token(value_text, label="PhysioNet value_text")
    mark = None if value == -1 else value
    return ExactEvent(
        PHYSIONET_DOMAIN_ID,
        _physionet_coordinates(elapsed_minutes, parameter, mark),
    )


def physionet_event_from_binary64(
    *, elapsed_minutes: object, parameter: object, value: object
) -> ExactEvent:
    mark = None if value is None else _fraction_from_binary64(value, label="value")
    return ExactEvent(
        PHYSIONET_DOMAIN_ID,
        _physionet_coordinates(elapsed_minutes, parameter, mark),
    )


def physionet_configuration(events: object) -> ExactConfiguration:
    if type(events) is not tuple:
        raise TypeError("events must be an exact tuple")
    return ExactConfiguration(PHYSIONET_DOMAIN_ID, events)


def retail_source_civil_microseconds(value: object) -> int:
    """Return source-civil microseconds since 2009-12-01 00:00:00.

    Online Retail II publishes a calendar value without a timezone.  This
    carrier therefore makes no UTC, offset, daylight-saving, or instant claim.
    """

    if type(value) is not tuple or len(value) != 7:
        raise TypeError("invoice_calendar must be an exact seven-integer tuple")
    if any(type(component) is not int for component in value):
        raise TypeError("invoice_calendar components must be exact integers")
    try:
        instant = datetime(*value)
    except ValueError as exc:
        raise CKSInstanceError("invoice_calendar is not a valid Gregorian time") from exc
    if not _RETAIL_START <= instant < _RETAIL_END_EXCLUSIVE:
        raise CKSInstanceError("invoice_calendar is outside the frozen Retail horizon")
    offset = instant - _RETAIL_START
    microseconds = (
        (offset.days * 86400 + offset.seconds) * 1_000_000
        + offset.microseconds
    )
    if not 0 <= microseconds < RETAIL_HORIZON_MICROSECONDS:
        raise AssertionError("calendar conversion disagrees with the frozen horizon")
    return microseconds


def _retail_cancellation(invoice_no: object) -> bool:
    if type(invoice_no) is not str:
        raise TypeError("InvoiceNo must be an exact string")
    if len(invoice_no) not in (6, 7):
        raise CKSInstanceError("InvoiceNo has an invalid length")
    token = _plain_token(invoice_no, label="InvoiceNo")
    if _SIX_DIGITS.fullmatch(token) is not None:
        return False
    if len(token) == 7 and token[0] in "cC" and _SIX_DIGITS.fullmatch(token[1:]):
        return True
    raise CKSInstanceError(
        "InvoiceNo must be six digits or ASCII c/C followed by six digits"
    )


def _text_token(
    value: object, *, label: str, allow_empty: bool, maximum_utf8_bytes: int
) -> str:
    if type(value) is not str:
        raise TypeError(f"{label} must be an exact string")
    if not allow_empty and not value:
        raise CKSInstanceError(f"{label} must not be empty")
    if len(value) > maximum_utf8_bytes:
        raise CKSInstanceError(f"{label} exceeds its UTF-8 resource bound")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CKSInstanceError(f"{label} is not UTF-8 encodable") from exc
    if len(encoded) > maximum_utf8_bytes:
        raise CKSInstanceError(f"{label} exceeds its UTF-8 resource bound")
    return value


def _byte_token_coordinate(value: str) -> Fraction:
    """Injectively map one finite UTF-8 byte string into ``[0,1)``."""

    raw = value.encode("utf-8")
    offset = (256 ** len(raw) - 1) // 255
    code = offset
    for index, byte in enumerate(raw):
        code += byte * (256 ** (len(raw) - index - 1))
    return Fraction(code, code + 1)


def retail_event_from_decimal_token(
    *,
    invoice_no: object,
    stock_code: object,
    description: object,
    quantity: object,
    invoice_calendar: object,
    unit_price_text: object,
    country: object,
) -> ExactEvent:
    cancellation = _retail_cancellation(invoice_no)
    invoice = invoice_no
    stock = _text_token(
        stock_code, label="StockCode", allow_empty=False, maximum_utf8_bytes=256
    )
    if description is None:
        description_mask = Fraction(0)
        description_coordinate = Fraction(0)
    else:
        description_value = _text_token(
            description,
            label="Description",
            allow_empty=True,
            maximum_utf8_bytes=4096,
        )
        description_mask = Fraction(1)
        description_coordinate = _byte_token_coordinate(description_value)
    if country is None:
        country_mask = Fraction(0)
        country_coordinate = Fraction(0)
    else:
        country_value = _text_token(
            country, label="Country", allow_empty=True, maximum_utf8_bytes=256
        )
        country_mask = Fraction(1)
        country_coordinate = _byte_token_coordinate(country_value)
    if type(quantity) is not int:
        raise TypeError("Quantity must be an exact integer")
    price = _fraction_from_decimal_token(unit_price_text, label="UnitPrice")
    microseconds = retail_source_civil_microseconds(invoice_calendar)
    coordinates = (
        _byte_token_coordinate(invoice),
        Fraction(1 if cancellation else 0),
        _byte_token_coordinate(stock),
        description_mask,
        description_coordinate,
        Fraction(microseconds, RETAIL_HORIZON_MICROSECONDS),
        _bounded_signed(Fraction(quantity)),
        _bounded_signed(price),
        country_mask,
        country_coordinate,
    )
    return ExactEvent(RETAIL_DOMAIN_ID, coordinates)


def retail_event_from_binary64(
    *,
    invoice_no: object,
    stock_code: object,
    description: object,
    quantity: object,
    invoice_calendar: object,
    unit_price: object,
    country: object,
) -> ExactEvent:
    cancellation = _retail_cancellation(invoice_no)
    invoice = invoice_no
    stock = _text_token(
        stock_code, label="StockCode", allow_empty=False, maximum_utf8_bytes=256
    )
    if description is None:
        description_mask = Fraction(0)
        description_coordinate = Fraction(0)
    else:
        description_value = _text_token(
            description,
            label="Description",
            allow_empty=True,
            maximum_utf8_bytes=4096,
        )
        description_mask = Fraction(1)
        description_coordinate = _byte_token_coordinate(description_value)
    if country is None:
        country_mask = Fraction(0)
        country_coordinate = Fraction(0)
    else:
        country_value = _text_token(
            country, label="Country", allow_empty=True, maximum_utf8_bytes=256
        )
        country_mask = Fraction(1)
        country_coordinate = _byte_token_coordinate(country_value)
    if type(quantity) is not int:
        raise TypeError("Quantity must be an exact integer")
    price = _fraction_from_binary64(unit_price, label="UnitPrice")
    microseconds = retail_source_civil_microseconds(invoice_calendar)
    coordinates = (
        _byte_token_coordinate(invoice),
        Fraction(1 if cancellation else 0),
        _byte_token_coordinate(stock),
        description_mask,
        description_coordinate,
        Fraction(microseconds, RETAIL_HORIZON_MICROSECONDS),
        _bounded_signed(Fraction(quantity)),
        _bounded_signed(price),
        country_mask,
        country_coordinate,
    )
    return ExactEvent(RETAIL_DOMAIN_ID, coordinates)


def validate_retail_customer_context(*, customer_id: object) -> str:
    if type(customer_id) is not str:
        raise TypeError("CustomerID must be an exact string")
    if len(customer_id) > 5:
        raise CKSInstanceError("CustomerID exceeds its resource bound")
    if _CUSTOMER_DIGITS.fullmatch(customer_id) is None:
        raise CKSInstanceError("CustomerID must be one to five ASCII digits")
    if int(customer_id) <= 0:
        raise CKSInstanceError("CustomerID must be positive")
    return customer_id


def retail_customer_key_hex(*, customer_id: object) -> str:
    """Project canonical CustomerID context to F060 opaque-key hex."""

    canonical = validate_retail_customer_context(customer_id=customer_id)
    return canonical.encode("ascii").hex()


def retail_configuration(events: object) -> ExactConfiguration:
    if type(events) is not tuple:
        raise TypeError("events must be an exact tuple")
    return ExactConfiguration(RETAIL_DOMAIN_ID, events)


@dataclass(frozen=True, order=True)
class ConfigurationKernelSymbol:
    """Exact ``exp(-(c + sum_j alpha_j exp(-q_j)))`` descriptor."""

    rational_constant: Fraction
    event_exp_terms: Tuple[Tuple[Fraction, Fraction], ...]

    def __post_init__(self) -> None:
        constant = _exact_fraction(self.rational_constant, label="rational_constant")
        if constant < 0:
            raise ValueError("rational_constant must be nonnegative")
        if type(self.event_exp_terms) is not tuple:
            raise TypeError("event_exp_terms must be an exact tuple")
        previous: Optional[Fraction] = None
        for exponent, coefficient in self.event_exp_terms:
            exponent = _exact_fraction(exponent, label="event exponent")
            coefficient = _exact_fraction(coefficient, label="event coefficient")
            if exponent < 0 or coefficient == 0:
                raise ValueError("event terms require nonnegative exponents and nonzero coefficients")
            if previous is not None and exponent <= previous:
                raise ValueError("event terms must be strictly exponent-sorted")
            previous = exponent


@dataclass(frozen=True)
class FormalCKSScore:
    """Canonical exact rational combination of configuration-kernel symbols."""

    terms: Tuple[Tuple[ConfigurationKernelSymbol, Fraction], ...]

    def __post_init__(self) -> None:
        if type(self.terms) is not tuple:
            raise TypeError("score terms must be an exact tuple")
        previous: Optional[ConfigurationKernelSymbol] = None
        for symbol, coefficient in self.terms:
            if type(symbol) is not ConfigurationKernelSymbol:
                raise TypeError("score symbol must be exact")
            coefficient = _exact_fraction(coefficient, label="score coefficient")
            if coefficient == 0:
                raise ValueError("score coefficients must be nonzero")
            if previous is not None and symbol <= previous:
                raise ValueError("score terms must be strictly symbol-sorted")
            previous = symbol


def _event_kernel_exponent(
    left: ExactEvent, right: ExactEvent, spec: DomainCKSSpec
) -> Fraction:
    squared_distance = sum(
        (left_value - right_value) ** 2
        for left_value, right_value in zip(left.coordinates, right.coordinates)
    )
    return squared_distance / (2 * spec.event_tau2)


def _add_event_mean_terms(
    accumulator: Dict[Fraction, Fraction],
    left: Sequence[ExactEvent],
    right: Sequence[ExactEvent],
    coefficient: Fraction,
    spec: DomainCKSSpec,
) -> None:
    if not left or not right:
        return
    scaled = coefficient / (len(left) * len(right))
    for left_event in left:
        for right_event in right:
            exponent = _event_kernel_exponent(left_event, right_event, spec)
            accumulator[exponent] = accumulator.get(exponent, Fraction(0)) + scaled


def configuration_kernel(
    left: ExactConfiguration, right: ExactConfiguration
) -> ConfigurationKernelSymbol:
    if type(left) is not ExactConfiguration or type(right) is not ExactConfiguration:
        raise TypeError("configuration_kernel requires exact configurations")
    if left.domain_id != right.domain_id:
        raise CKSInstanceError("cross-domain kernel evaluation is forbidden")
    spec = DOMAIN_SPECS[left.domain_id]
    count_term = (
        spec.count_scale2 * (len(left.events) - len(right.events)) ** 2
        / (2 * spec.outer_sigma2)
    )
    event_terms: Dict[Fraction, Fraction] = {}
    _add_event_mean_terms(event_terms, left.events, left.events, Fraction(1), spec)
    _add_event_mean_terms(event_terms, right.events, right.events, Fraction(1), spec)
    _add_event_mean_terms(event_terms, left.events, right.events, Fraction(-2), spec)
    scale = spec.event_scale2 / (2 * spec.outer_sigma2)
    combined = tuple(
        (exponent, coefficient * scale)
        for exponent, coefficient in sorted(event_terms.items())
        if coefficient != 0
    )
    return ConfigurationKernelSymbol(count_term, combined)


def conditional_cks_score(
    draws: object, target: object
) -> FormalCKSScore:
    if type(draws) is not tuple:
        raise TypeError("draws must be an exact tuple")
    if not 2 <= len(draws) <= 128:
        raise CKSInstanceError("the exact score domain requires 2 <= R <= 128")
    if any(type(draw) is not ExactConfiguration for draw in draws):
        raise TypeError("draws must contain exact configurations")
    if type(target) is not ExactConfiguration:
        raise TypeError("target must be an exact configuration")
    if any(draw.domain_id != target.domain_id for draw in draws):
        raise CKSInstanceError("draws and target must belong to one domain")
    coefficients: Dict[ConfigurationKernelSymbol, Fraction] = {}
    pair_weight = Fraction(1, len(draws) * (len(draws) - 1))
    target_weight = Fraction(-2, len(draws))
    for left_index, left in enumerate(draws):
        for right_index, right in enumerate(draws):
            if left_index == right_index:
                continue
            symbol = configuration_kernel(left, right)
            coefficients[symbol] = coefficients.get(symbol, Fraction(0)) + pair_weight
        symbol = configuration_kernel(left, target)
        coefficients[symbol] = coefficients.get(symbol, Fraction(0)) + target_weight
    terms = tuple(
        (symbol, coefficient)
        for symbol, coefficient in sorted(coefficients.items())
        if coefficient != 0
    )
    return FormalCKSScore(terms)


__all__ = [
    "CKSInstanceError",
    "ConfigurationKernelSymbol",
    "DOMAIN_SPECS",
    "DomainCKSSpec",
    "ExactConfiguration",
    "ExactEvent",
    "FormalCKSScore",
    "PHYSIONET_CONFIGURATION_CAP",
    "PHYSIONET_DOMAIN_ID",
    "PHYSIONET_HORIZON_MINUTES",
    "PHYSIONET_PARAMETERS",
    "PHYSIONET_SPEC",
    "PHYSIONET_UNITS",
    "PRIMARY_METRIC_ID",
    "RETAIL_CONFIGURATION_CAP",
    "RETAIL_DOMAIN_ID",
    "RETAIL_HORIZON_MICROSECONDS",
    "RETAIL_HORIZON_SECONDS",
    "RETAIL_SPEC",
    "conditional_cks_score",
    "configuration_kernel",
    "physionet_configuration",
    "physionet_event_from_binary64",
    "physionet_event_from_decimal_token",
    "retail_configuration",
    "retail_event_from_binary64",
    "retail_event_from_decimal_token",
    "retail_customer_key_hex",
    "retail_source_civil_microseconds",
    "validate_configuration_count",
    "validate_retail_customer_context",
]
