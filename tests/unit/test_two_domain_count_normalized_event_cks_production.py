from __future__ import annotations

from fractions import Fraction
import math

import pytest

from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    CKSInstanceError,
    ConfigurationKernelSymbol,
    FormalCKSScore,
    PHYSIONET_DOMAIN_ID,
    RETAIL_DOMAIN_ID,
    conditional_cks_score,
    configuration_kernel,
    physionet_configuration,
    physionet_event_from_decimal_token,
    retail_configuration,
    retail_event_from_decimal_token,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    CKSProductionError,
    CKSProductionResourceError,
    COMPARISON_DIRECTION,
    PRODUCTION_INTEGRATION_ID,
    SCORE_DIRECTION,
    ProductionCKSComparison,
    ProductionCKSScore,
    evaluate_configuration_kernel_symbol,
    evaluate_formal_cks_score,
    formal_score_sha256,
    production_conditional_cks_score,
    production_direct_minus_guide,
    score_record,
)


def _phys(value: str, minute: int = 0):
    return physionet_configuration(
        (
            physionet_event_from_decimal_token(
                elapsed_minutes=minute,
                parameter="HR",
                value_text=value,
            ),
        )
    )


def _retail(quantity: int):
    return retail_configuration(
        (
            retail_event_from_decimal_token(
                invoice_no="123456",
                stock_code="SKU",
                description="item",
                quantity=quantity,
                invoice_calendar=(2010, 1, 2, 3, 4, 5, 6),
                unit_price_text="1.25",
                country="United Kingdom",
            ),
        )
    )


@pytest.mark.parametrize(
    "target,draws",
    [
        (
            physionet_configuration(()),
            (physionet_configuration(()), physionet_configuration(())),
        ),
        (_phys("80"), (_phys("80"), _phys("81"), _phys("82", 1))),
        (_retail(1), (_retail(1), _retail(2), _retail(-1))),
    ],
)
def test_production_formal_score_matches_frozen_public_api(target, draws):
    result = production_conditional_cks_score(draws, target)
    assert result.formal_score == conditional_cks_score(draws, target)
    assert result.formal_score_sha256 == formal_score_sha256(result.formal_score)
    assert result.binary64_score == evaluate_formal_cks_score(result.formal_score)
    assert result.binary64_score_hex == result.binary64_score.hex()
    assert -2.0 <= result.binary64_score <= 1.0


def test_empty_configuration_score_is_minus_one():
    empty = physionet_configuration(())
    result = production_conditional_cks_score((empty, empty), empty)
    assert result.binary64_score == -1.0
    assert result.symbolic_event_pair_work_units == 0
    assert result.metric_id == "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
    assert result.integration_id == PRODUCTION_INTEGRATION_ID
    assert result.domain_id == PHYSIONET_DOMAIN_ID
    assert result.score_direction == SCORE_DIRECTION


def test_configuration_kernel_projection_matches_identical_unit_value():
    configuration = _phys("80")
    symbol = configuration_kernel(configuration, configuration)
    assert evaluate_configuration_kernel_symbol(symbol) == 1.0


def test_direct_minus_guide_positive_favors_better_guide():
    target = _phys("80")
    direct = (_phys("160"), _phys("160"))
    guide = (target, target)
    result = production_direct_minus_guide(direct, guide, target)
    assert result.direct_minus_guide > 0.0
    assert result.direct_minus_guide == (
        result.direct.binary64_score - result.guide.binary64_score
    )
    assert result.direct_minus_guide_hex == result.direct_minus_guide.hex()
    assert result.favorable_direction == COMPARISON_DIRECTION


def test_retail_domain_is_preserved():
    target = _retail(1)
    result = production_conditional_cks_score((_retail(1), _retail(2)), target)
    assert result.domain_id == RETAIL_DOMAIN_ID


def test_score_record_is_compact_and_json_ready():
    target = _phys("80")
    result = production_conditional_cks_score((target, target), target)
    record = score_record(result)
    assert record == {
        "metric_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
        "integration_id": PRODUCTION_INTEGRATION_ID,
        "domain_id": PHYSIONET_DOMAIN_ID,
        "draw_count": 2,
        "formal_score_sha256": result.formal_score_sha256,
        "formal_term_count": 1,
        "binary64_score_hex": "-0x1.0000000000000p+0",
        "score_direction": SCORE_DIRECTION,
        "symbolic_event_pair_work_units": 9,
        "integrity_sha256": result._integrity_sha256,
    }


def test_formal_digest_is_deterministic_and_lowercase():
    target = _phys("80")
    score = conditional_cks_score((target, _phys("81")), target)
    first = formal_score_sha256(score)
    second = formal_score_sha256(score)
    assert first == second
    assert len(first) == 64
    assert first == first.lower()


def test_resource_limit_refuses_before_symbolic_evaluation():
    target = _phys("80")
    with pytest.raises(CKSProductionResourceError):
        production_conditional_cks_score(
            (target, target),
            target,
            symbolic_event_pair_work_limit=8,
        )


@pytest.mark.parametrize("bad", [True, 0, -1, 1_000_000_001, 1.5, "10"])
def test_work_limit_is_strict(bad):
    empty = physionet_configuration(())
    with pytest.raises((TypeError, ValueError)):
        production_conditional_cks_score(
            (empty, empty),
            empty,
            symbolic_event_pair_work_limit=bad,
        )


@pytest.mark.parametrize("draws", [[], (object(), object()), (physionet_configuration(()),)])
def test_draw_container_and_count_are_strict(draws):
    target = physionet_configuration(())
    with pytest.raises((TypeError, CKSInstanceError)):
        production_conditional_cks_score(draws, target)


def test_cross_domain_score_refuses():
    with pytest.raises(CKSInstanceError):
        production_conditional_cks_score(
            (physionet_configuration(()), retail_configuration(())),
            physionet_configuration(()),
        )


def test_unmatched_comparison_draw_counts_refuse():
    target = _phys("80")
    with pytest.raises(CKSProductionError):
        production_direct_minus_guide((target, target), (target, target, target), target)


def test_kernel_projection_refuses_material_negative_squared_distance():
    hostile = ConfigurationKernelSymbol(
        Fraction(0),
        ((Fraction(0), Fraction(-1)),),
    )
    with pytest.raises(CKSProductionError):
        evaluate_configuration_kernel_symbol(hostile)


def test_projection_input_types_are_exact():
    with pytest.raises(TypeError):
        evaluate_configuration_kernel_symbol(object())
    with pytest.raises(TypeError):
        evaluate_formal_cks_score(object())
    with pytest.raises(TypeError):
        formal_score_sha256(object())
    with pytest.raises(TypeError):
        score_record(object())


@pytest.mark.parametrize(
    ("field", "hostile_value"),
    [
        ("formal_score_sha256", "0" * 64),
        ("domain_id", "online-retail-ii"),
        ("draw_count", 3),
        ("symbolic_event_pair_work_units", 999),
    ],
)
def test_score_record_constructor_is_factory_only_and_record_revalidates(
    field, hostile_value
):
    target = _phys("80")
    result = production_conditional_cks_score((target, target), target)
    with pytest.raises(TypeError):
        ProductionCKSScore()
    object.__setattr__(result, field, hostile_value)
    with pytest.raises(ValueError):
        score_record(result)


@pytest.mark.parametrize(
    ("field", "hostile_value"),
    [
        ("domain_id", "online-retail-ii"),
        ("draw_count", 3),
        ("direct_minus_guide", 0.25),
    ],
)
def test_comparison_record_detects_post_issue_mutation(field, hostile_value):
    target = _phys("80")
    result = production_direct_minus_guide((target, target), (target, target), target)
    object.__setattr__(result, field, hostile_value)
    with pytest.raises(ValueError):
        result.__post_init__()


def test_comparison_constructor_is_factory_only_and_total_work_is_bounded():
    target = _phys("80")
    result = production_direct_minus_guide((target, target), (target, target), target)
    assert result.direct_minus_guide == 0.0
    with pytest.raises(TypeError):
        ProductionCKSComparison()
    with pytest.raises(CKSProductionResourceError):
        production_direct_minus_guide(
            (target, target),
            (target, target),
            target,
            symbolic_event_pair_work_limit=17,
        )


def test_formal_score_projection_accepts_empty_term_zero():
    score = FormalCKSScore(())
    assert evaluate_formal_cks_score(score) == 0.0
    assert math.isfinite(evaluate_formal_cks_score(score))
