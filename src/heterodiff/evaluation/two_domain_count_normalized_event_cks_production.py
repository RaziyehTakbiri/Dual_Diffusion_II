"""Production projection for the frozen two-domain F105 CKS metric.

The exact metric definition lives in
``two_domain_count_normalized_event_cks``.  This module is the deliberately
small production integration layer: it constructs the same formal score,
projects its nested exponentials to binary64, records the exact formal-score
digest, and applies the frozen direct-minus-guide orientation.

It performs no parsing, fitting, randomness, I/O, data access, or threshold
decision.  Inputs must already be exact admitted-domain configurations.  A
deterministic work ceiling refuses impractically large symbolic evaluations
before evaluating a kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from typing import Dict, Mapping, Tuple

from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    CKSInstanceError,
    ConfigurationKernelSymbol,
    ExactConfiguration,
    FormalCKSScore,
    PRIMARY_METRIC_ID,
    configuration_kernel,
)


PRODUCTION_INTEGRATION_ID = "F105_CKS_BINARY64_PROJECTION_V1"
SCORE_DIRECTION = "LOWER_IS_BETTER"
COMPARISON_DIRECTION = "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE"
DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT = 10_000_000
MAX_SYMBOLIC_EVENT_PAIR_WORK_LIMIT = 1_000_000_000
_BINARY64_EPSILON = 2.0**-52


class CKSProductionError(ValueError):
    """Raised when a production-score input or projection is invalid."""


class CKSProductionResourceError(CKSProductionError):
    """Raised before evaluation when the frozen symbolic work cap is exceeded."""


_PRODUCTION_CONSTRUCTION_SEAL = object()


@dataclass(frozen=True, init=False)
class ProductionCKSScore:
    """Auditable binary64 projection of one exact formal F105 score."""

    metric_id: str
    integration_id: str
    domain_id: str
    draw_count: int
    formal_score: FormalCKSScore
    formal_score_sha256: str
    binary64_score: float
    binary64_score_hex: str
    score_direction: str
    symbolic_event_pair_work_units: int
    _integrity_sha256: str
    _construction_seal: object

    def __new__(cls, *args: object, **kwargs: object) -> "ProductionCKSScore":
        raise TypeError(
            "ProductionCKSScore is factory-only; use "
            "production_conditional_cks_score"
        )

    def __post_init__(self) -> None:
        if self.metric_id != PRIMARY_METRIC_ID:
            raise ValueError("metric_id differs from the frozen F105 metric")
        if self.integration_id != PRODUCTION_INTEGRATION_ID:
            raise ValueError("integration_id differs from the frozen production layer")
        if type(self.domain_id) is not str or not self.domain_id:
            raise TypeError("domain_id must be a nonempty exact string")
        if type(self.draw_count) is not int or not 2 <= self.draw_count <= 128:
            raise ValueError("draw_count must lie in the formal F105 domain 2..128")
        if type(self.formal_score) is not FormalCKSScore:
            raise TypeError("formal_score must be an exact FormalCKSScore")
        if (
            type(self.formal_score_sha256) is not str
            or len(self.formal_score_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.formal_score_sha256)
        ):
            raise ValueError("formal_score_sha256 must be lowercase SHA-256 hex")
        if type(self.binary64_score) is not float or not math.isfinite(self.binary64_score):
            raise TypeError("binary64_score must be a finite binary64 float")
        if self.binary64_score_hex != self.binary64_score.hex():
            raise ValueError("binary64_score_hex does not bind binary64_score")
        if self.score_direction != SCORE_DIRECTION:
            raise ValueError("score_direction differs from the frozen direction")
        if (
            type(self.symbolic_event_pair_work_units) is not int
            or self.symbolic_event_pair_work_units < 0
        ):
            raise TypeError("symbolic_event_pair_work_units must be nonnegative")
        if self._construction_seal is not _PRODUCTION_CONSTRUCTION_SEAL:
            raise ValueError("score lacks the production construction seal")
        if formal_score_sha256(self.formal_score) != self.formal_score_sha256:
            raise ValueError("formal_score_sha256 does not bind formal_score")
        projected = evaluate_formal_cks_score(self.formal_score)
        if projected != self.binary64_score:
            raise ValueError("binary64_score does not match formal_score")
        if self._integrity_sha256 != _score_integrity_sha256(self):
            raise ValueError("score fields differ from the factory-issued record")


@dataclass(frozen=True, init=False)
class ProductionCKSComparison:
    """Matched direct-versus-guide comparison for one target configuration."""

    metric_id: str
    integration_id: str
    domain_id: str
    draw_count: int
    direct: ProductionCKSScore
    guide: ProductionCKSScore
    direct_minus_guide: float
    direct_minus_guide_hex: str
    favorable_direction: str
    _integrity_sha256: str
    _construction_seal: object

    def __new__(cls, *args: object, **kwargs: object) -> "ProductionCKSComparison":
        raise TypeError(
            "ProductionCKSComparison is factory-only; use "
            "production_direct_minus_guide"
        )

    def __post_init__(self) -> None:
        if self.metric_id != PRIMARY_METRIC_ID:
            raise ValueError("comparison metric_id differs")
        if self.integration_id != PRODUCTION_INTEGRATION_ID:
            raise ValueError("comparison integration_id differs")
        if self.direct.domain_id != self.domain_id or self.guide.domain_id != self.domain_id:
            raise ValueError("comparison domains differ")
        if self.direct.draw_count != self.draw_count or self.guide.draw_count != self.draw_count:
            raise ValueError("comparison draw counts differ")
        if type(self.direct_minus_guide) is not float or not math.isfinite(
            self.direct_minus_guide
        ):
            raise TypeError("direct_minus_guide must be a finite binary64 float")
        if self.direct_minus_guide_hex != self.direct_minus_guide.hex():
            raise ValueError("direct_minus_guide_hex does not bind the effect")
        if self.favorable_direction != COMPARISON_DIRECTION:
            raise ValueError("favorable_direction differs from the frozen direction")
        if self._construction_seal is not _PRODUCTION_CONSTRUCTION_SEAL:
            raise ValueError("comparison lacks the production construction seal")
        _validate_score_integrity(self.direct)
        _validate_score_integrity(self.guide)
        expected_difference = self.direct.binary64_score - self.guide.binary64_score
        if expected_difference != self.direct_minus_guide:
            raise ValueError("direct_minus_guide does not match the bound scores")
        if self._integrity_sha256 != _comparison_integrity_sha256(self):
            raise ValueError("comparison fields differ from the factory-issued record")


def _integrity_digest(domain: str, payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256((domain + "\0").encode("ascii") + encoded).hexdigest()


def _score_integrity_sha256(score: ProductionCKSScore) -> str:
    return _integrity_digest(
        "heterodiff-production-cks-score-v1",
        {
            "metric_id": score.metric_id,
            "integration_id": score.integration_id,
            "domain_id": score.domain_id,
            "draw_count": score.draw_count,
            "formal_score_sha256": score.formal_score_sha256,
            "binary64_score_hex": score.binary64_score_hex,
            "score_direction": score.score_direction,
            "symbolic_event_pair_work_units": score.symbolic_event_pair_work_units,
        },
    )


def _comparison_integrity_sha256(
    comparison: ProductionCKSComparison,
) -> str:
    return _integrity_digest(
        "heterodiff-production-cks-comparison-v1",
        {
            "metric_id": comparison.metric_id,
            "integration_id": comparison.integration_id,
            "domain_id": comparison.domain_id,
            "draw_count": comparison.draw_count,
            "direct_integrity_sha256": comparison.direct._integrity_sha256,
            "guide_integrity_sha256": comparison.guide._integrity_sha256,
            "direct_minus_guide_hex": comparison.direct_minus_guide_hex,
            "favorable_direction": comparison.favorable_direction,
        },
    )


def _factory_instance(cls: type, **fields: object) -> object:
    """Construct one sealed frozen record without exposing a public constructor."""

    instance = object.__new__(cls)
    for name, value in fields.items():
        object.__setattr__(instance, name, value)
    object.__setattr__(instance, "_construction_seal", _PRODUCTION_CONSTRUCTION_SEAL)
    if cls is ProductionCKSScore:
        object.__setattr__(
            instance, "_integrity_sha256", _score_integrity_sha256(instance)
        )
    elif cls is ProductionCKSComparison:
        object.__setattr__(
            instance, "_integrity_sha256", _comparison_integrity_sha256(instance)
        )
    else:
        raise TypeError("unsupported production record class")
    instance.__post_init__()
    return instance


def _validate_score_integrity(score: object) -> ProductionCKSScore:
    if type(score) is not ProductionCKSScore:
        raise TypeError("score must be an exact ProductionCKSScore")
    score.__post_init__()
    return score


def _validate_comparison_integrity(
    comparison: object,
) -> ProductionCKSComparison:
    if type(comparison) is not ProductionCKSComparison:
        raise TypeError("comparison must be an exact ProductionCKSComparison")
    comparison.__post_init__()
    return comparison


def _positive_work_limit(value: object) -> int:
    if type(value) is not int:
        raise TypeError("symbolic_event_pair_work_limit must be an exact integer")
    if not 1 <= value <= MAX_SYMBOLIC_EVENT_PAIR_WORK_LIMIT:
        raise ValueError(
            "symbolic_event_pair_work_limit must lie in 1..1000000000"
        )
    return value


def _validated_inputs(
    draws: object, target: object
) -> Tuple[Tuple[ExactConfiguration, ...], ExactConfiguration]:
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
    return draws, target


def _pair_work(left: ExactConfiguration, right: ExactConfiguration) -> int:
    left_count = len(left.events)
    right_count = len(right.events)
    return (
        left_count * left_count
        + right_count * right_count
        + left_count * right_count
    )


def _canonical_pair_key(
    left_index: int, right_index: int
) -> Tuple[int, int]:
    return (
        (left_index, right_index)
        if left_index <= right_index
        else (right_index, left_index)
    )


def _required_score_pairs(draw_count: int) -> set[Tuple[int, int]]:
    target_index = draw_count
    required_pairs = {
        _canonical_pair_key(left, right)
        for left in range(draw_count)
        for right in range(left + 1, draw_count)
    }
    required_pairs.update(
        _canonical_pair_key(index, target_index) for index in range(draw_count)
    )
    return required_pairs


def _symbolic_work_units(
    draws: Tuple[ExactConfiguration, ...], target: ExactConfiguration
) -> int:
    configurations = draws + (target,)
    return sum(
        _pair_work(configurations[left], configurations[right])
        for left, right in _required_score_pairs(len(draws))
    )


def _formal_score_with_cache(
    draws: Tuple[ExactConfiguration, ...],
    target: ExactConfiguration,
    *,
    work_limit: int,
) -> Tuple[FormalCKSScore, int]:
    """Build the public formal score while caching symmetric kernel calls."""

    configurations = draws + (target,)
    target_index = len(draws)
    required_pairs = _required_score_pairs(len(draws))
    work_units = _symbolic_work_units(draws, target)
    if work_units > work_limit:
        raise CKSProductionResourceError(
            "symbolic event-pair work exceeds the frozen caller-visible ceiling"
        )

    symbols: Dict[Tuple[int, int], ConfigurationKernelSymbol] = {}
    for left_index, right_index in sorted(required_pairs):
        symbols[(left_index, right_index)] = configuration_kernel(
            configurations[left_index], configurations[right_index]
        )

    coefficients: Dict[ConfigurationKernelSymbol, Fraction] = {}
    pair_weight = Fraction(2, len(draws) * (len(draws) - 1))
    target_weight = Fraction(-2, len(draws))
    for left_index in range(len(draws)):
        for right_index in range(left_index + 1, len(draws)):
            symbol = symbols[(left_index, right_index)]
            coefficients[symbol] = coefficients.get(symbol, Fraction(0)) + pair_weight
        symbol = symbols[_canonical_pair_key(left_index, target_index)]
        coefficients[symbol] = coefficients.get(symbol, Fraction(0)) + target_weight
    formal = FormalCKSScore(
        tuple(
            (symbol, coefficient)
            for symbol, coefficient in sorted(coefficients.items())
            if coefficient != 0
        )
    )
    return formal, work_units


def _fraction_record(value: Fraction) -> Tuple[int, int]:
    return value.numerator, value.denominator


def _formal_score_bytes(score: FormalCKSScore) -> bytes:
    record = [
        {
            "rational_constant": _fraction_record(symbol.rational_constant),
            "event_exp_terms": [
                {
                    "exponent": _fraction_record(exponent),
                    "coefficient": _fraction_record(term_coefficient),
                }
                for exponent, term_coefficient in symbol.event_exp_terms
            ],
            "score_coefficient": _fraction_record(score_coefficient),
        }
        for symbol, score_coefficient in score.terms
    ]
    return json.dumps(
        record,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def formal_score_sha256(score: object) -> str:
    if type(score) is not FormalCKSScore:
        raise TypeError("score must be an exact FormalCKSScore")
    return hashlib.sha256(_formal_score_bytes(score)).hexdigest()


def evaluate_configuration_kernel_symbol(symbol: object) -> float:
    """Project one exact nested-exponential kernel symbol to binary64."""

    if type(symbol) is not ConfigurationKernelSymbol:
        raise TypeError("symbol must be an exact ConfigurationKernelSymbol")
    event_components = [
        float(coefficient) * math.exp(-float(exponent))
        for exponent, coefficient in symbol.event_exp_terms
    ]
    outer_components = [float(symbol.rational_constant), *event_components]
    outer_exponent = math.fsum(outer_components)
    absolute_scale = math.fsum(abs(component) for component in outer_components)
    tolerance = 128.0 * _BINARY64_EPSILON * max(1.0, absolute_scale)
    if not math.isfinite(outer_exponent):
        raise CKSProductionError("configuration-kernel exponent is not finite")
    if outer_exponent < -tolerance:
        raise CKSProductionError(
            "configuration-kernel squared-distance projection is materially negative"
        )
    if outer_exponent < 0.0:
        outer_exponent = 0.0
    value = math.exp(-outer_exponent)
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise CKSProductionError("configuration-kernel value is outside [0,1]")
    return value


def evaluate_formal_cks_score(score: object) -> float:
    """Project an exact formal score without changing its algebraic source."""

    if type(score) is not FormalCKSScore:
        raise TypeError("score must be an exact FormalCKSScore")
    value = math.fsum(
        float(coefficient) * evaluate_configuration_kernel_symbol(symbol)
        for symbol, coefficient in score.terms
    )
    if not math.isfinite(value):
        raise CKSProductionError("CKS score projection is not finite")
    tolerance = 512.0 * _BINARY64_EPSILON
    if value < -2.0 - tolerance or value > 1.0 + tolerance:
        raise CKSProductionError("CKS score projection is outside its formal bounds")
    if value < -2.0:
        value = -2.0
    elif value > 1.0:
        value = 1.0
    return value


def production_conditional_cks_score(
    draws: object,
    target: object,
    *,
    symbolic_event_pair_work_limit: object = DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT,
) -> ProductionCKSScore:
    """Return the production projection and its exact formal provenance."""

    checked_draws, checked_target = _validated_inputs(draws, target)
    work_limit = _positive_work_limit(symbolic_event_pair_work_limit)
    formal, work_units = _formal_score_with_cache(
        checked_draws, checked_target, work_limit=work_limit
    )
    projected = evaluate_formal_cks_score(formal)
    return _factory_instance(
        ProductionCKSScore,
        metric_id=PRIMARY_METRIC_ID,
        integration_id=PRODUCTION_INTEGRATION_ID,
        domain_id=checked_target.domain_id,
        draw_count=len(checked_draws),
        formal_score=formal,
        formal_score_sha256=formal_score_sha256(formal),
        binary64_score=projected,
        binary64_score_hex=projected.hex(),
        score_direction=SCORE_DIRECTION,
        symbolic_event_pair_work_units=work_units,
    )


def production_direct_minus_guide(
    direct_draws: object,
    guide_draws: object,
    target: object,
    *,
    symbolic_event_pair_work_limit: object = DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT,
) -> ProductionCKSComparison:
    """Evaluate a matched comparison; a positive result favors the guide."""

    if type(direct_draws) is not tuple or type(guide_draws) is not tuple:
        raise TypeError("direct_draws and guide_draws must be exact tuples")
    if len(direct_draws) != len(guide_draws):
        raise CKSProductionError("direct and guide draw counts must match")
    work_limit = _positive_work_limit(symbolic_event_pair_work_limit)
    checked_direct, checked_target = _validated_inputs(direct_draws, target)
    checked_guide, checked_guide_target = _validated_inputs(guide_draws, target)
    if checked_target != checked_guide_target:
        raise CKSProductionError("direct and guide targets differ")
    comparison_work = _symbolic_work_units(
        checked_direct, checked_target
    ) + _symbolic_work_units(checked_guide, checked_target)
    if comparison_work > work_limit:
        raise CKSProductionResourceError(
            "combined direct-and-guide symbolic work exceeds the frozen ceiling"
        )
    direct = production_conditional_cks_score(
        checked_direct,
        checked_target,
        symbolic_event_pair_work_limit=work_limit,
    )
    guide = production_conditional_cks_score(
        checked_guide,
        checked_target,
        symbolic_event_pair_work_limit=work_limit,
    )
    if direct.domain_id != guide.domain_id:
        raise CKSProductionError("direct and guide scores belong to different domains")
    difference = direct.binary64_score - guide.binary64_score
    if not math.isfinite(difference):
        raise CKSProductionError("direct-minus-guide projection is not finite")
    return _factory_instance(
        ProductionCKSComparison,
        metric_id=PRIMARY_METRIC_ID,
        integration_id=PRODUCTION_INTEGRATION_ID,
        domain_id=direct.domain_id,
        draw_count=direct.draw_count,
        direct=direct,
        guide=guide,
        direct_minus_guide=difference,
        direct_minus_guide_hex=difference.hex(),
        favorable_direction=COMPARISON_DIRECTION,
    )


def score_record(score: object) -> Mapping[str, object]:
    """Return a compact JSON-ready audit record for one production score."""

    score = _validate_score_integrity(score)
    return {
        "metric_id": score.metric_id,
        "integration_id": score.integration_id,
        "domain_id": score.domain_id,
        "draw_count": score.draw_count,
        "formal_score_sha256": score.formal_score_sha256,
        "formal_term_count": len(score.formal_score.terms),
        "binary64_score_hex": score.binary64_score_hex,
        "score_direction": score.score_direction,
        "symbolic_event_pair_work_units": score.symbolic_event_pair_work_units,
        "integrity_sha256": score._integrity_sha256,
    }


__all__ = [
    "CKSProductionError",
    "CKSProductionResourceError",
    "COMPARISON_DIRECTION",
    "DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT",
    "MAX_SYMBOLIC_EVENT_PAIR_WORK_LIMIT",
    "PRODUCTION_INTEGRATION_ID",
    "ProductionCKSComparison",
    "ProductionCKSScore",
    "SCORE_DIRECTION",
    "evaluate_configuration_kernel_symbol",
    "evaluate_formal_cks_score",
    "formal_score_sha256",
    "production_conditional_cks_score",
    "production_direct_minus_guide",
    "score_record",
]
