"""Exact metric-image audit and supplied stratified scalar-chart PROPOSAL.

F105 embeddings are injections, not Euclidean generative charts. This module
never rounds a one-hot, mask, timestamp, quantity or UTF-8 code into validity.
It decodes exact *semantic* records, not source decimal spellings, file bytes,
row provenance, patient/customer context, or admitted scientific support.

The optional scalar-fiber chart fixes ALL discrete fields in explicit stratum
keys. Positive/negative marks use +/-exp(r); zero/missing marks are separate
zero-dimensional atoms. This is a supplied support SUBSET, not a complete
real-domain schema or adoption of continuous-valued measurement semantics.
Floating exp/log are numerical implementations of analytic open-support
bijections; bitwise round trips and valid output for unrepresentable tails
are not claimed. Overflow/underflow fail, with no clipping or retry.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction
import math

from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks
from heterodiff.theory.configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    MAX_CONFIGURATION_EVENT_TYPES,
    TransformedConfiguration,
    TransformedEvent,
)


MAX_AUDIT_EVENTS = 4096
MAX_EXACT_COORDINATE_BITS = 65536
STRICT_FLOAT_POLICY = "REQUIRE_EXACT_BINARY64"
REPORTED_FLOAT_POLICY = "ROUND_TO_BINARY64_WITH_EXACT_ERROR_RECORD"


class GenerativeChartError(ValueError):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(code + (":" + detail if detail else ""))


def _require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise GenerativeChartError(code, detail)


def _signed(value: Fraction) -> Fraction:
    return value / (1 + abs(value))


def _inverse_signed(value: Fraction, name: str) -> Fraction:
    _require(abs(value) < 1, "OUTSIDE_METRIC_IMAGE", name + " outside (-1,1)")
    return value / (1 - abs(value))


def _integer(value: Fraction, name: str) -> int:
    _require(value.denominator == 1, "OUTSIDE_METRIC_IMAGE", name + " is not an exact integer")
    return value.numerator


def _bit(value: Fraction, name: str) -> int:
    _require(value in (0, 1), "OUTSIDE_METRIC_IMAGE", name + " is not an exact bit")
    return int(value)


@dataclass(frozen=True)
class PhysioSemanticEvent:
    elapsed_minutes: int
    parameter: str
    value: Fraction | None

    def to_metric_event(self) -> cks.ExactEvent:
        _require(self.value is None or type(self.value) is Fraction,
                 "EXACT_SEMANTIC_RECORD_REQUIRED", "Physio value")
        _require(self.value is None or self.value >= 0,
                 "OUTSIDE_METRIC_IMAGE", "negative present Physio value")
        try:
            base = cks.physionet_event_from_binary64(
                elapsed_minutes=self.elapsed_minutes, parameter=self.parameter,
                value=None if self.value is None else 0.0)
        except (TypeError, ValueError) as error:
            raise GenerativeChartError("OUTSIDE_METRIC_IMAGE", str(error)) from error
        if self.value is None:
            return base
        values = list(base.coordinates)
        index = cks.PHYSIONET_PARAMETERS.index(self.parameter)
        values[75 + index] = self.value / (1 + self.value)
        return cks.ExactEvent(cks.PHYSIONET_DOMAIN_ID, tuple(values))


@dataclass(frozen=True)
class RetailSemanticEvent:
    invoice_no: str
    stock_code: str
    description: str | None
    quantity: int
    invoice_calendar: tuple[int, ...]
    unit_price: Fraction
    country: str | None

    def to_metric_event(self) -> cks.ExactEvent:
        _require(type(self.unit_price) is Fraction, "EXACT_SEMANTIC_RECORD_REQUIRED", "Retail price")
        try:
            base = cks.retail_event_from_binary64(
                invoice_no=self.invoice_no, stock_code=self.stock_code,
                description=self.description, quantity=self.quantity,
                invoice_calendar=self.invoice_calendar, unit_price=0.0,
                country=self.country)
        except (TypeError, ValueError) as error:
            raise GenerativeChartError("OUTSIDE_METRIC_IMAGE", str(error)) from error
        values = list(base.coordinates)
        values[7] = _signed(self.unit_price)
        return cks.ExactEvent(cks.RETAIL_DOMAIN_ID, tuple(values))


def _decode_utf8_coordinate(coordinate: Fraction, *, maximum_bytes: int, name: str) -> str:
    _require(0 <= coordinate < 1, "OUTSIDE_METRIC_IMAGE", name + " code outside [0,1)")
    code = _integer(coordinate / (1 - coordinate), name + " UTF-8 code")
    # Finite length-prefix code intervals: [offset_n, offset_n + 256**n).
    # No float logarithm, integer rounding, Unicode normalization, or trimming.
    offset, width = 0, 1
    for length in range(maximum_bytes + 1):
        if code < offset + width:
            raw = (code - offset).to_bytes(length, "big")
            try:
                return raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise GenerativeChartError("OUTSIDE_METRIC_IMAGE", name + " invalid UTF-8") from error
        offset += width
        width *= 256
    raise GenerativeChartError("OUTSIDE_METRIC_IMAGE", name + " exceeds frozen UTF-8 byte bound")


def decode_metric_event(event: cks.ExactEvent) -> PhysioSemanticEvent | RetailSemanticEvent:
    """Exact inverse on the frozen semantic image; off-image inputs refuse.

    The ExactEvent carrier itself only checks dimension/Fraction types; it
    does not establish any of these discrete/support constraints. This new
    function does not weaken/change that frozen carrier or its score factory.
    The map's rational semantic image is broader than the accepted bounded
    decimal-token/finite-binary64 constructor inputs. Numeric input-origin
    eligibility and original source spelling are NOT proved by this inverse.
    """
    _require(type(event) is cks.ExactEvent, "EXACT_METRIC_EVENT_REQUIRED")
    _require(all(max(abs(v.numerator).bit_length(), v.denominator.bit_length())
                 <= MAX_EXACT_COORDINATE_BITS for v in event.coordinates),
             "LOCAL_EXACT_ARITHMETIC_LIMIT")
    coordinates = event.coordinates
    if event.domain_id == cks.PHYSIONET_DOMAIN_ID:
        one_hot = tuple(_bit(v, "Physio one-hot") for v in coordinates[:37])
        _require(sum(one_hot) == 1, "OUTSIDE_METRIC_IMAGE", "Physio one-hot must select one type")
        index = one_hot.index(1)
        minute = _integer(coordinates[37] * cks.PHYSIONET_HORIZON_MINUTES, "Physio elapsed minute")
        _require(0 <= minute <= cks.PHYSIONET_HORIZON_MINUTES, "OUTSIDE_METRIC_IMAGE", "Physio time horizon")
        masks, values = coordinates[38:75], coordinates[75:112]
        _require(all(masks[j] == 0 and values[j] == 0 for j in range(37) if j != index),
                 "OUTSIDE_METRIC_IMAGE", "Physio inactive slots must be zero")
        present = _bit(masks[index], "Physio presence")
        if not present:
            _require(values[index] == 0, "OUTSIDE_METRIC_IMAGE", "missing Physio value must have zero payload")
            value = None
        else:
            _require(0 <= values[index] < 1, "OUTSIDE_METRIC_IMAGE", "Physio transformed value outside [0,1)")
            value = values[index] / (1 - values[index])
        result = PhysioSemanticEvent(minute, cks.PHYSIONET_PARAMETERS[index], value)
    elif event.domain_id == cks.RETAIL_DOMAIN_ID:
        invoice = _decode_utf8_coordinate(coordinates[0], maximum_bytes=7, name="InvoiceNo")
        cancellation = _bit(coordinates[1], "cancellation")
        stock = _decode_utf8_coordinate(coordinates[2], maximum_bytes=256, name="StockCode")
        description_present = _bit(coordinates[3], "description presence")
        if description_present:
            description = _decode_utf8_coordinate(coordinates[4], maximum_bytes=4096, name="Description")
        else:
            _require(coordinates[4] == 0, "OUTSIDE_METRIC_IMAGE", "missing Description payload must be zero")
            description = None
        micros = _integer(coordinates[5] * cks.RETAIL_HORIZON_MICROSECONDS, "source-civil microsecond")
        _require(0 <= micros < cks.RETAIL_HORIZON_MICROSECONDS, "OUTSIDE_METRIC_IMAGE", "Retail time horizon")
        instant = datetime(2009, 12, 1) + timedelta(microseconds=micros)
        calendar = (instant.year, instant.month, instant.day, instant.hour,
                    instant.minute, instant.second, instant.microsecond)
        quantity = _integer(_inverse_signed(coordinates[6], "quantity"), "Quantity")
        price = _inverse_signed(coordinates[7], "price")
        country_present = _bit(coordinates[8], "country presence")
        if country_present:
            country = _decode_utf8_coordinate(coordinates[9], maximum_bytes=256, name="Country")
        else:
            _require(coordinates[9] == 0, "OUTSIDE_METRIC_IMAGE", "missing Country payload must be zero")
            country = None
        result = RetailSemanticEvent(invoice, stock, description, quantity, calendar, price, country)
        _require(cancellation == int(invoice.startswith(("c", "C"))),
                 "OUTSIDE_METRIC_IMAGE", "cancellation bit disagrees with InvoiceNo")
    else:
        raise GenerativeChartError("UNKNOWN_DOMAIN")
    _require(result.to_metric_event() == event, "OUTSIDE_METRIC_IMAGE", "exact re-encoding differs")
    return result


def audit_metric_configuration(configuration: cks.ExactConfiguration) -> dict:
    """Read-only supplied-object support audit; not a data admission receipt."""
    _require(type(configuration) is cks.ExactConfiguration, "EXACT_CONFIGURATION_REQUIRED")
    _require(len(configuration.events) <= MAX_AUDIT_EVENTS, "LOCAL_EVENT_AUDIT_LIMIT")
    failures = []
    for ordinal, event in enumerate(configuration.events):
        try:
            decode_metric_event(event)
        except GenerativeChartError as error:
            failures.append({"event_ordinal": ordinal, "code": error.code, "detail": str(error)})
    decision = "EXACT_F105_IMAGE_ONLY_NOT_GENERATIVE_CHART_ADMISSION"
    if failures:
        decision = ("LOCAL_AUDIT_LIMIT" if any(item["code"].startswith("LOCAL_") for item in failures)
                    else "OUTSIDE_F105_DOMAIN_IMAGE")
    return {"decision": decision, "domain_id": configuration.domain_id,
            "event_count": len(configuration.events), "failures": tuple(failures),
            "all_events_in_exact_semantic_image": not failures,
            "multiplicity_preserved": True, "rows_filtered_or_repaired": 0,
            "source_token_spelling_reconstructed": False,
            "raw_decimal_or_generated_binary64_origin_proven": False,
            "generative_chart_or_data_admitted": False}


@dataclass(frozen=True)
class PhysioFiberKey:
    elapsed_minutes: int
    parameter: str

    def __post_init__(self):
        PhysioSemanticEvent(self.elapsed_minutes, self.parameter, Fraction(0)).to_metric_event()

    @property
    def domain_id(self):
        return cks.PHYSIONET_DOMAIN_ID


@dataclass(frozen=True)
class RetailFiberKey:
    invoice_no: str
    stock_code: str
    description: str | None
    quantity: int
    invoice_calendar: tuple[int, ...]
    country: str | None

    def __post_init__(self):
        self.semantic(Fraction(0)).to_metric_event()

    @property
    def domain_id(self):
        return cks.RETAIL_DOMAIN_ID

    def semantic(self, price: Fraction) -> RetailSemanticEvent:
        return RetailSemanticEvent(self.invoice_no, self.stock_code, self.description,
                                   self.quantity, self.invoice_calendar, price, self.country)


@dataclass(frozen=True)
class ScalarFiberSpec:
    event_type: int
    key: PhysioFiberKey | RetailFiberKey
    branch: str

    def __post_init__(self):
        _require(type(self.event_type) is int and 0 <= self.event_type <= 2**63 - 1,
                 "INVALID_FIBER_TYPE_ID")
        _require(type(self.key) in (PhysioFiberKey, RetailFiberKey), "EXACT_FIBER_KEY_REQUIRED")
        branches = ("MISSING", "ZERO", "POSITIVE") if type(self.key) is PhysioFiberKey else ("NEGATIVE", "ZERO", "POSITIVE")
        _require(self.branch in branches, "INVALID_MARK_STRATUM")

    @property
    def dimension(self):
        return int(self.branch in ("NEGATIVE", "POSITIVE"))


@dataclass(frozen=True)
class ContinuousEncodingRecord:
    transformed_event: TransformedEvent
    source_fraction: Fraction | None
    binary64_native_value: float | None
    exact_native_conversion_error: Fraction | None
    decoded_native_roundtrip_error: Fraction | None
    conversion_policy: str

    def summary(self) -> dict:
        def ratio(value):
            return None if value is None else (value.numerator, value.denominator)
        return {"source_fraction": ratio(self.source_fraction),
                "binary64_native_value_hex": None if self.binary64_native_value is None else self.binary64_native_value.hex(),
                "exact_native_conversion_error": ratio(self.exact_native_conversion_error),
                "decoded_native_roundtrip_error": ratio(self.decoded_native_roundtrip_error),
                "conversion_policy": self.conversion_policy,
                "discrete_fields_rounded": False, "production_conversion_adopted": False}


@dataclass(frozen=True)
class ScalarFiberChartProposal:
    """Explicit finite subset of legal discrete strata; no learned codebook.

    No type weights, source-data selection, missing/zero probabilities, reference
    cap, clinical exclusion rule, or production architecture is chosen here.
    Flattening full raw-domain discrete support into this small interface is
    not claimed feasible. Metadata are immutable stratum labels, not context
    placeholders to be overwritten after Gaussian sampling.
    """

    fibers: tuple[ScalarFiberSpec, ...]
    domain_id: str

    def __init__(self, fibers: tuple[ScalarFiberSpec, ...]):
        _require(type(fibers) is tuple and 1 <= len(fibers) <= MAX_CONFIGURATION_EVENT_TYPES,
                 "BOUNDED_EXPLICIT_FIBER_TUPLE_REQUIRED")
        _require(all(type(fiber) is ScalarFiberSpec for fiber in fibers), "EXACT_FIBER_SPEC_REQUIRED")
        _require(len({fiber.event_type for fiber in fibers}) == len(fibers), "DUPLICATE_TYPE_ID")
        _require(len({(fiber.key, fiber.branch) for fiber in fibers}) == len(fibers), "DUPLICATE_SEMANTIC_FIBER")
        _require(len({fiber.key.domain_id for fiber in fibers}) == 1, "CROSS_DOMAIN_CHART_FORBIDDEN")
        object.__setattr__(self, "fibers", tuple(sorted(fibers, key=lambda fiber: fiber.event_type)))
        object.__setattr__(self, "domain_id", self.fibers[0].key.domain_id)

    @property
    def type_dimensions(self) -> dict[int, int]:
        return {fiber.event_type: fiber.dimension for fiber in self.fibers}

    def decode_transformed_event(self, event: TransformedEvent) -> cks.ExactEvent:
        _require(type(event) is TransformedEvent, "EXACT_TRANSFORMED_EVENT_REQUIRED")
        selected = tuple(fiber for fiber in self.fibers if fiber.event_type == event.event_type)
        _require(len(selected) == 1, "UNDECLARED_GENERATIVE_STRATUM")
        fiber = selected[0]
        _require(len(event.coordinates) == fiber.dimension, "UNPADDED_FIBER_DIMENSION_MISMATCH")
        if fiber.branch == "MISSING":
            native = None
        elif fiber.branch == "ZERO":
            native = 0.0
        else:
            try:
                magnitude = math.exp(event.coordinates[0])
            except OverflowError as error:
                raise GenerativeChartError("LOG_CHART_OVERFLOW_NO_CLIPPING") from error
            _require(math.isfinite(magnitude) and magnitude > 0, "LOG_CHART_UNDERFLOW_OR_NONFINITE_NO_CLIPPING")
            native = -magnitude if fiber.branch == "NEGATIVE" else magnitude
        if type(fiber.key) is PhysioFiberKey:
            return cks.physionet_event_from_binary64(
                elapsed_minutes=fiber.key.elapsed_minutes, parameter=fiber.key.parameter, value=native)
        key = fiber.key
        return cks.retail_event_from_binary64(
            invoice_no=key.invoice_no, stock_code=key.stock_code, description=key.description,
            quantity=key.quantity, invoice_calendar=key.invoice_calendar,
            unit_price=native, country=key.country)

    def decode_configuration(self, state: TransformedConfiguration) -> cks.ExactConfiguration:
        _require(type(state) is tuple and len(state) <= MAX_AUDIT_EVENTS, "LOCAL_CHART_CONFIGURATION_LIMIT")
        events = tuple(self.decode_transformed_event(event) for event in state)
        return (cks.physionet_configuration(events) if self.domain_id == cks.PHYSIONET_DOMAIN_ID
                else cks.retail_configuration(events))

    def encode_metric_event(self, event: cks.ExactEvent,
                            *, conversion_policy: str = STRICT_FLOAT_POLICY) -> ContinuousEncodingRecord:
        _require(conversion_policy in (STRICT_FLOAT_POLICY, REPORTED_FLOAT_POLICY), "EXPLICIT_FLOAT_CONVERSION_POLICY_REQUIRED")
        semantic = decode_metric_event(event)
        if type(semantic) is PhysioSemanticEvent:
            key = PhysioFiberKey(semantic.elapsed_minutes, semantic.parameter)
            value = semantic.value
        else:
            key = RetailFiberKey(semantic.invoice_no, semantic.stock_code, semantic.description,
                                 semantic.quantity, semantic.invoice_calendar, semantic.country)
            value = semantic.unit_price
        branch = "MISSING" if value is None else "ZERO" if value == 0 else "NEGATIVE" if value < 0 else "POSITIVE"
        selected = tuple(fiber for fiber in self.fibers if fiber.key == key and fiber.branch == branch)
        _require(len(selected) == 1, "UNDECLARED_GENERATIVE_STRATUM")
        fiber = selected[0]
        if not fiber.dimension:
            native = None if value is None else 0.0
            return ContinuousEncodingRecord(TransformedEvent(fiber.event_type, ()), value, native,
                                            None if value is None else Fraction(0),
                                            None if value is None else Fraction(0), conversion_policy)
        try:
            native = float(value)
        except OverflowError as error:
            raise GenerativeChartError("NATIVE_BINARY64_OVERFLOW_NO_CLIPPING") from error
        _require(math.isfinite(native) and native != 0.0, "NATIVE_BINARY64_UNDERFLOW_OR_NONFINITE")
        conversion_error = Fraction.from_float(native) - value
        _require(conversion_policy != STRICT_FLOAT_POLICY or conversion_error == 0,
                 "EXACT_BINARY64_CONVERSION_REQUIRED", "choose the explicit recorded-error policy to propose rounding")
        transformed = TransformedEvent(fiber.event_type, (math.log(abs(native)),))
        decoded = decode_metric_event(self.decode_transformed_event(transformed))
        decoded_value = decoded.value if type(decoded) is PhysioSemanticEvent else decoded.unit_price
        return ContinuousEncodingRecord(transformed, value, native, conversion_error,
                                        decoded_value - value, conversion_policy)

    def summary(self) -> dict:
        return {"scope": "SUPPLIED_STRATIFIED_SUBSET_CHART_PROPOSAL_ONLY", "domain_id": self.domain_id,
                "type_dimensions": self.type_dimensions, "full_domain_coverage_claimed": False,
                "f105_metric_unchanged": True, "f105_embedding_used_as_generative_chart": False,
                "discrete_fields_rounded_or_projected": False,
                "type_weights_or_reference_cap_selected": False,
                "production_schema_or_numeric_policy_adopted": False,
                "mathematical_scalar_chart": "positive:log(v); negative:log(-v); zero/missing:atomic",
                "machine_bitwise_roundtrip_claimed": False}


def domain_support_obligations() -> dict:
    """Executable structural facts; no rows, outcomes or external calls used."""
    return {
        "scope": "SCHEMA_SUCCESSOR_REQUIRED_NOT_SCIENTIFIC_ADOPTION",
        "physionet_metric_dimension": cks.PHYSIONET_SPEC.coordinate_dimension,
        "retail_metric_dimension": cks.RETAIL_SPEC.coordinate_dimension,
        "physionet_all_minute_parameter_missing_zero_positive_strata": (
            (cks.PHYSIONET_HORIZON_MINUTES + 1) * len(cks.PHYSIONET_PARAMETERS) * 3),
        "retail_source_civil_time_atom_count": cks.RETAIL_HORIZON_MICROSECONDS,
        "current_reference_type_limit": MAX_CONFIGURATION_EVENT_TYPES,
        "current_reference_cardinality_limit": MAX_CONFIGURATION_CARDINALITY,
        "f105_physionet_configuration_cap": cks.PHYSIONET_CONFIGURATION_CAP,
        "f105_retail_configuration_cap": cks.RETAIL_CONFIGURATION_CAP,
        "arbitrary_gaussian_f105_vectors_are_not_legal_domain_events": True,
        "frozen_observation_kernel_unchanged": "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1",
        "continuous_identity_emission_common_domination_claimed": False,
        "production_schema_selected": False,
        "required_successor_choices": (
            "FACTORISED_OR_OTHER_EXPLICIT_DISCRETE_STRATUM_REFERENCE_AND_BALANCED_JUMPS",
            "DECIMAL_MEASUREMENT_CONTINUOUS_VS_ATOMIC_MODEL_AND_NUMERIC_CONVERSION_POLICY",
            "FULL_DISCRETE_SUPPORT_INCLUDING_STRINGS_TIMES_QUANTITIES_AND_BOUNDARY_ATOMS",
            "B06_ARCHITECTURE_PARAMETER_COUNTS_AND_CAPACITY_FAIRNESS",
            "REFERENCE_IMPLEMENTATION_CAPS_WITHOUT_DROPPING_OR_TOP_CODING_ROWS",
            "DOMAIN_OBSERVATION_KERNEL_SUPPORT_AND_NORMALIZATION",
        ),
    }
