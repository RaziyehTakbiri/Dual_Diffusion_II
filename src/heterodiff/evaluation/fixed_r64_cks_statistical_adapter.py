"""F109-fixed, address-aware adapter for the F105 production evaluator.

The underlying F105 implementation intentionally supports its theorem domain
``2 <= R <= 128``.  The confirmatory statistical plan is narrower: F109 fixes
exactly 64 conditional draws per case.  The comparison entrypoint consumes two
explicit address-bearing row rosters, requires their canonical non-method
addresses to be byte-for-byte equal, and refuses any other count or pairing
before invoking the general evaluator.  The check proves consistency of the
caller-supplied rosters; later execution custody must still prove that those
addresses truthfully describe the supplied configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT,
    CKSProductionError,
    ProductionCKSComparison,
    ProductionCKSScore,
    production_conditional_cks_score,
    production_direct_minus_guide,
)


F109_CONDITIONAL_DRAWS_PER_CASE = 64
FIXED_R64_ADAPTER_ID = "F105_F109_FIXED_R64_CONFIRMATORY_ADAPTER_V1"
F109_ADDRESS_FIELDS = (
    "domain_id",
    "seed_id",
    "group_id",
    "case_id",
    "draw_id",
    "conditioning_id",
)
_DOMAIN_IDS = ("R3-PHYS", "R4-RETAIL")


def _canonical_identity(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        raise TypeError(f"{label} must be a nonempty exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise CKSProductionError(f"{label} must be canonical ASCII") from error
    if any(byte < 0x21 or byte > 0x7E for byte in encoded):
        raise CKSProductionError(
            f"{label} must be visible ASCII without whitespace"
        )
    return value


@dataclass(frozen=True)
class F109DrawAddress:
    """Canonical method-neutral address for one conditional draw."""

    domain_id: str
    seed_id: str
    group_id: str
    case_id: str
    draw_id: str
    conditioning_id: str

    def __post_init__(self) -> None:
        for field in F109_ADDRESS_FIELDS:
            _canonical_identity(getattr(self, field), label=field)
        if self.domain_id not in _DOMAIN_IDS:
            raise CKSProductionError("domain_id is outside the frozen two-domain roster")


@dataclass(frozen=True)
class F109AddressedDraw:
    """One caller-supplied configuration bound to its explicit address."""

    address: F109DrawAddress
    configuration: object

    def __post_init__(self) -> None:
        if type(self.address) is not F109DrawAddress:
            raise TypeError("address must be an exact F109DrawAddress")


def _fixed_addressed_draws(
    value: object, *, label: str
) -> tuple[tuple[F109DrawAddress, ...], tuple[object, ...]]:
    if type(value) is not tuple:
        raise TypeError(f"{label} must be an exact tuple")
    if len(value) != F109_CONDITIONAL_DRAWS_PER_CASE:
        raise CKSProductionError(
            f"{label} must contain exactly 64 addressed draws under frozen F109"
        )
    addresses = []
    configurations = []
    for ordinal, row in enumerate(value):
        if type(row) is not F109AddressedDraw:
            raise TypeError(f"{label}[{ordinal}] must be an exact F109AddressedDraw")
        addresses.append(row.address)
        configurations.append(row.configuration)
    exact_addresses = tuple(addresses)
    if len(set(exact_addresses)) != F109_CONDITIONAL_DRAWS_PER_CASE:
        raise CKSProductionError(f"{label} contains a duplicate draw address")
    first = exact_addresses[0]
    expected_case = (
        first.domain_id,
        first.seed_id,
        first.group_id,
        first.case_id,
        first.conditioning_id,
    )
    for address in exact_addresses:
        actual_case = (
            address.domain_id,
            address.seed_id,
            address.group_id,
            address.case_id,
            address.conditioning_id,
        )
        if actual_case != expected_case:
            raise CKSProductionError(
                f"{label} spans more than one domain/seed/group/case/conditioning address"
            )
    return exact_addresses, tuple(configurations)


def fixed_r64_conditional_cks_score(
    addressed_draws: object,
    target: object,
    *,
    symbolic_event_pair_work_limit: object = DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT,
) -> ProductionCKSScore:
    """Evaluate one F109-conforming score and assert the returned bounds."""

    addresses, checked = _fixed_addressed_draws(
        addressed_draws, label="addressed_draws"
    )
    result = production_conditional_cks_score(
        checked,
        target,
        symbolic_event_pair_work_limit=symbolic_event_pair_work_limit,
    )
    if result.draw_count != F109_CONDITIONAL_DRAWS_PER_CASE:
        raise CKSProductionError("the production evaluator returned a non-F109 count")
    if result.domain_id != addresses[0].domain_id:
        raise CKSProductionError(
            "the production evaluator domain disagrees with the supplied address roster"
        )
    if not math.isfinite(result.binary64_score) or not -2.0 <= result.binary64_score <= 1.0:
        raise CKSProductionError("the production evaluator returned an invalid score")
    return result


def fixed_r64_direct_minus_guide(
    direct_addressed_draws: object,
    guide_addressed_draws: object,
    target: object,
    *,
    symbolic_event_pair_work_limit: object = DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT,
) -> ProductionCKSComparison:
    """Evaluate one matched F109 comparison with no variable-R fallback."""

    direct_addresses, direct = _fixed_addressed_draws(
        direct_addressed_draws, label="direct_addressed_draws"
    )
    guide_addresses, guide = _fixed_addressed_draws(
        guide_addressed_draws, label="guide_addressed_draws"
    )
    if direct_addresses != guide_addresses:
        raise CKSProductionError(
            "direct and guide draw-address rosters are not exactly paired"
        )
    result = production_direct_minus_guide(
        direct,
        guide,
        target,
        symbolic_event_pair_work_limit=symbolic_event_pair_work_limit,
    )
    if result.draw_count != F109_CONDITIONAL_DRAWS_PER_CASE:
        raise CKSProductionError("the production comparison returned a non-F109 count")
    if result.domain_id != direct_addresses[0].domain_id:
        raise CKSProductionError(
            "the production comparison domain disagrees with the paired address roster"
        )
    if (
        not math.isfinite(result.direct_minus_guide)
        or not -3.0 <= result.direct_minus_guide <= 3.0
    ):
        raise CKSProductionError("the paired score is outside the frozen [-3,3] range")
    return result


__all__ = [
    "F109_ADDRESS_FIELDS",
    "F109AddressedDraw",
    "F109_CONDITIONAL_DRAWS_PER_CASE",
    "F109DrawAddress",
    "FIXED_R64_ADAPTER_ID",
    "fixed_r64_conditional_cks_score",
    "fixed_r64_direct_minus_guide",
]
