"""Exact support/inverse and small supplied-fiber tests; no study data."""

from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import math

import numpy as np
import pytest

from heterodiff.data.two_domain_generative_chart_proposal import (
    GenerativeChartError,
    PhysioFiberKey,
    PhysioSemanticEvent,
    RetailFiberKey,
    RetailSemanticEvent,
    ScalarFiberChartProposal,
    ScalarFiberSpec,
    REPORTED_FLOAT_POLICY,
    audit_metric_configuration,
    decode_metric_event,
    domain_support_obligations,
)
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


def _phys(value_text="80.0", minute=12, parameter="HR"):
    return cks.physionet_event_from_decimal_token(elapsed_minutes=minute, parameter=parameter, value_text=value_text)


def _retail(**overrides):
    kwargs = dict(invoice_no="C123456", stock_code="sku-α", description="e\u0301  preserved",
                  quantity=-3, invoice_calendar=(2010, 2, 3, 4, 5, 6, 7),
                  unit_price_text="-1.125", country="")
    return cks.retail_event_from_decimal_token(**{**kwargs, **overrides})


def _mutate(event, position, value):
    coordinates = list(event.coordinates)
    coordinates[position] = value
    return cks.ExactEvent(event.domain_id, tuple(coordinates))


@pytest.mark.parametrize("parameter", cks.PHYSIONET_PARAMETERS)
@pytest.mark.parametrize("value", ["-1", "0", "0.1", "123.456"])
def test_every_physio_parameter_exact_semantic_roundtrip(parameter, value):
    event = _phys(value, parameter=parameter)
    decoded = decode_metric_event(event)
    assert type(decoded) is PhysioSemanticEvent
    assert decoded.parameter == parameter and decoded.elapsed_minutes == 12
    assert decoded.value == (None if value == "-1" else Fraction(value))
    assert decoded.to_metric_event() == event


@pytest.mark.parametrize("minute", [0, 2880])
def test_physio_time_endpoints_are_atoms_not_clipped_interior(minute):
    event = _phys(minute=minute)
    assert decode_metric_event(event).elapsed_minutes == minute
    assert PhysioFiberKey(minute, "HR").elapsed_minutes == minute


def test_numeric_equivalent_source_spellings_are_not_reconstructed():
    assert _phys("80") == _phys("80.00")
    decoded = decode_metric_event(_phys("80.00"))
    assert decoded.value == Fraction(80)
    assert not hasattr(decoded, "value_text")
    # The structural rational map has a larger semantic image than the two
    # bounded decimal/binary64 input constructors. Do not conflate the claims.
    rational_event = PhysioSemanticEvent(0, "HR", Fraction(1, 3)).to_metric_event()
    assert decode_metric_event(rational_event).value == Fraction(1, 3)
    audit = audit_metric_configuration(cks.physionet_configuration((rational_event,)))
    assert audit["raw_decimal_or_generated_binary64_origin_proven"] is False


@pytest.mark.parametrize("position,value", [
    (0, Fraction(1, 2)), (0, Fraction(1)), (37, Fraction(1, 2881)),
    (37, Fraction(-1)), (38, Fraction(1)), (75, Fraction(1)),
    (38 + 14, Fraction(1, 2)), (75 + 14, Fraction(1)),
])
def test_physio_off_image_discrete_and_support_coordinates_are_not_repaired(position, value):
    bad = _mutate(_phys(), position, value)
    with pytest.raises(GenerativeChartError, match="OUTSIDE_METRIC_IMAGE"):
        decode_metric_event(bad)


def test_physio_missing_and_zero_are_distinct_atoms():
    missing, zero = _phys("-1"), _phys("0")
    assert missing != zero
    assert decode_metric_event(missing).value is None
    assert decode_metric_event(zero).value == Fraction(0)
    with pytest.raises(GenerativeChartError, match="missing Physio value"):
        decode_metric_event(_mutate(missing, 75 + 14, Fraction(1, 2)))


@pytest.mark.parametrize("invoice", ["123456", "C123456", "c123456"])
@pytest.mark.parametrize("description,country", [(None, None), ("", ""), ("é", "日本"), ("e\u0301", "  UK  ")])
def test_retail_exact_utf8_civil_time_integer_and_signed_price_roundtrip(invoice, description, country):
    event = _retail(invoice_no=invoice, description=description, country=country)
    decoded = decode_metric_event(event)
    assert type(decoded) is RetailSemanticEvent
    assert decoded.invoice_no == invoice
    assert decoded.description == description and decoded.country == country
    assert decoded.invoice_calendar == (2010, 2, 3, 4, 5, 6, 7)
    assert decoded.quantity == -3 and decoded.unit_price == Fraction(-9, 8)
    assert decoded.to_metric_event() == event


def test_retail_missing_present_empty_and_unicode_normalization_remain_distinct():
    events = tuple(_retail(description=value) for value in (None, "", "é", "e\u0301"))
    assert len(set(events)) == 4
    assert tuple(decode_metric_event(event).description for event in events) == (None, "", "é", "e\u0301")


def test_retail_utf8_length_boundary_and_exact_calendar_last_microsecond():
    event = _retail(stock_code="x" * 256, description="a" * 4096,
                    country="y" * 256, invoice_calendar=(2011, 12, 9, 23, 59, 59, 999999))
    decoded = decode_metric_event(event)
    assert decoded.to_metric_event() == event
    assert decoded.invoice_calendar == (2011, 12, 9, 23, 59, 59, 999999)


@pytest.mark.parametrize("position,value", [
    (0, Fraction(1, 3)), (1, Fraction(0)), (2, Fraction(0)),
    (3, Fraction(1, 2)), (5, Fraction(1, 3 * cks.RETAIL_HORIZON_MICROSECONDS)),
    (5, Fraction(1)), (6, Fraction(1, 3)), (7, Fraction(1)), (8, Fraction(1, 2)),
])
def test_retail_off_image_codes_bits_times_quantities_are_not_rounded(position, value):
    with pytest.raises(GenerativeChartError, match="OUTSIDE_METRIC_IMAGE"):
        decode_metric_event(_mutate(_retail(), position, value))


def test_invalid_utf8_and_missing_payload_rejected():
    # The length-one code offset is1; 0xff therefore has code256.
    invalid_utf8 = Fraction(256, 257)
    with pytest.raises(GenerativeChartError, match="invalid UTF-8"):
        decode_metric_event(_mutate(_retail(), 2, invalid_utf8))
    with pytest.raises(GenerativeChartError, match="missing Country payload"):
        decode_metric_event(_mutate(_retail(country=None), 9, Fraction(1, 2)))
    with pytest.raises(GenerativeChartError, match="missing Description payload"):
        decode_metric_event(_mutate(_retail(description=None), 4, Fraction(1, 2)))


def test_f105_carrier_dimension_is_not_domain_image_validation():
    for domain, dimension in ((cks.PHYSIONET_DOMAIN_ID, 112), (cks.RETAIL_DOMAIN_ID, 10)):
        event = cks.ExactEvent(domain, tuple(Fraction(0) for _ in range(dimension)))
        configuration = cks.ExactConfiguration(domain, (event,))
        report = audit_metric_configuration(configuration)
        assert report["decision"] == "OUTSIDE_F105_DOMAIN_IMAGE"
        assert report["rows_filtered_or_repaired"] == 0
        assert report["generative_chart_or_data_admitted"] is False


def test_metric_image_audit_retains_duplicates_and_distinguishes_resource_refusal():
    event = _phys()
    report = audit_metric_configuration(cks.physionet_configuration((event, event)))
    assert report["event_count"] == 2 and report["all_events_in_exact_semantic_image"] is True
    enormous = _mutate(event, 37, Fraction(1 << 70000))
    report = audit_metric_configuration(cks.physionet_configuration((enormous,)))
    assert report["decision"] == "LOCAL_AUDIT_LIMIT"
    assert report["failures"][0]["code"] == "LOCAL_EXACT_ARITHMETIC_LIMIT"


def _phys_chart():
    key = PhysioFiberKey(0, "HR")
    return ScalarFiberChartProposal(tuple(ScalarFiberSpec(i, key, branch)
                                         for i, branch in enumerate(("MISSING", "ZERO", "POSITIVE"))))


def _retail_chart():
    key = RetailFiberKey("C123456", "SKU", None, -3, (2009, 12, 1, 0, 0, 0, 0), "")
    return ScalarFiberChartProposal(tuple(ScalarFiberSpec(i, key, branch)
                                         for i, branch in enumerate(("NEGATIVE", "ZERO", "POSITIVE"))))


@pytest.mark.parametrize("factory", [_phys_chart, _retail_chart])
def test_declared_scalar_fibers_produce_legal_events_without_discrete_projection(factory):
    chart = factory()
    state = tuple(TransformedEvent(fiber.event_type, (0.0,) if fiber.dimension else ())
                  for fiber in chart.fibers)
    configuration = chart.decode_configuration(state + state)
    assert len(configuration.events) == 6
    assert audit_metric_configuration(configuration)["all_events_in_exact_semantic_image"] is True
    for event in configuration.events:
        encoded = chart.encode_metric_event(event)
        assert encoded.exact_native_conversion_error in (None, Fraction(0))
        assert chart.decode_transformed_event(encoded.transformed_event) == event
        assert encoded.summary()["discrete_fields_rounded"] is False
    assert chart.summary()["full_domain_coverage_claimed"] is False


@pytest.mark.parametrize("factory", [_phys_chart, _retail_chart])
def test_declared_fiber_interface_works_with_actual_capped_gaussian_reference(factory):
    chart = factory()
    # Explicit synthetic weights/activity/cap: none is a real-domain selection.
    reference = CappedPoissonConfigurationReference(
        chart.type_dimensions, {0: 0.25, 1: 0.25, 2: 0.5}, activity=2.0, total_cap=10)
    rng = np.random.default_rng(41)
    for _ in range(16):
        state = reference.sample_configuration(rng)
        decoded = chart.decode_configuration(state)
        assert len(decoded.events) == len(state)
        assert audit_metric_configuration(decoded)["all_events_in_exact_semantic_image"] is True


def test_continuous_numeric_conversion_is_strict_unless_exact_error_record_requested():
    chart = _phys_chart()
    event = _phys("0.1", minute=0)
    with pytest.raises(GenerativeChartError, match="EXACT_BINARY64_CONVERSION_REQUIRED"):
        chart.encode_metric_event(event)
    result = chart.encode_metric_event(event, conversion_policy=REPORTED_FLOAT_POLICY)
    assert result.exact_native_conversion_error == Fraction.from_float(0.1) - Fraction(1, 10)
    assert result.exact_native_conversion_error != 0
    decoded = decode_metric_event(chart.decode_transformed_event(result.transformed_event))
    assert result.decoded_native_roundtrip_error == decoded.value - Fraction(1, 10)
    assert result.summary()["production_conversion_adopted"] is False
    assert result.summary()["conversion_policy"] == REPORTED_FLOAT_POLICY


def test_even_exact_native_binary64_does_not_claim_bitwise_log_exp_roundtrip():
    chart = _phys_chart()
    event = cks.physionet_event_from_binary64(elapsed_minutes=0, parameter="HR", value=3.0)
    record = chart.encode_metric_event(event)
    assert record.exact_native_conversion_error == 0
    actual = Fraction.from_float(math.exp(math.log(3.0))) - Fraction(3)
    assert record.decoded_native_roundtrip_error == actual
    assert chart.summary()["machine_bitwise_roundtrip_claimed"] is False


@pytest.mark.parametrize("coordinate", [-1000.0, 1000.0])
def test_log_chart_unrepresentable_tails_fail_without_clipping(coordinate):
    with pytest.raises(GenerativeChartError, match="NO_CLIPPING"):
        _phys_chart().decode_transformed_event(TransformedEvent(2, (coordinate,)))


def test_unselected_discrete_fields_cannot_be_overwritten_after_sampling():
    chart = _phys_chart()
    for event in (_phys(minute=1), _phys(minute=0, parameter="Temp")):
        with pytest.raises(GenerativeChartError, match="UNDECLARED_GENERATIVE_STRATUM"):
            chart.encode_metric_event(event)
    with pytest.raises(GenerativeChartError, match="UNDECLARED_GENERATIVE_STRATUM"):
        chart.decode_transformed_event(TransformedEvent(99, (0.0,)))
    with pytest.raises(GenerativeChartError, match="UNPADDED_FIBER_DIMENSION_MISMATCH"):
        chart.decode_transformed_event(TransformedEvent(0, (0.0,)))


def test_chart_rejects_duplicate_semantic_types_and_cross_domain_tables():
    phys, retail = _phys_chart(), _retail_chart()
    with pytest.raises(GenerativeChartError, match="DUPLICATE_TYPE_ID"):
        ScalarFiberChartProposal((phys.fibers[0], phys.fibers[0]))
    with pytest.raises(GenerativeChartError, match="DUPLICATE_SEMANTIC_FIBER"):
        ScalarFiberChartProposal((phys.fibers[0], replace(phys.fibers[0], event_type=99)))
    with pytest.raises(GenerativeChartError, match="CROSS_DOMAIN_CHART"):
        ScalarFiberChartProposal((phys.fibers[0], replace(retail.fibers[0], event_type=99)))
    with pytest.raises(FrozenInstanceError):
        phys.fibers = retail.fibers


def test_structural_obligations_are_computed_not_invented_closure():
    report = domain_support_obligations()
    assert report["physionet_all_minute_parameter_missing_zero_positive_strata"] == 319791
    assert report["retail_source_civil_time_atom_count"] == 63849600000000
    assert report["current_reference_type_limit"] == 4096
    assert report["current_reference_cardinality_limit"] == 100000
    assert report["f105_physionet_configuration_cap"] == 131072
    assert report["f105_retail_configuration_cap"] == 1067371
    assert report["production_schema_selected"] is False
    assert report["frozen_observation_kernel_unchanged"] == "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1"
