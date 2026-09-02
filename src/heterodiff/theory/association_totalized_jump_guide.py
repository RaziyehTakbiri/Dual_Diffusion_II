"""Deterministically totalized, jump-only association guide.

The range-gated association guide preserves a successful represented point
value but deliberately refuses numerical failures and represented values
outside its certified interval.  This module closes exactly that liveness gap
for jump evaluation: on either of those two typed point failures it returns a
fixed, exactly specified interval midpoint.  All other failures -- including
invalid inputs, resource refusals, stale provenance, and live-model mismatch --
remain failures.

The resulting point function defines an operational surrogate jump potential.
It is not claimed to define the analytic conditional or posterior target.
Every edit is computed as the difference of two evaluations of this same
totalized point function; no upstream edit API is called.  The construction
supplies no coordinate derivatives, continuous drift, rate envelope, clock,
randomness, or sampler admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
import platform
import struct
import sys
from typing import Optional, Tuple

import numpy as np
import scipy

from .association_operational_guide import (
    AssociationGuideOperationalError,
    RANGE_GATED_GUIDE_SCHEMA_VERSION,
    RangeGatedAssociationGuide,
    _copy_outcome,
    _same_float,
    _state_key,
    _validated_digest,
    _validated_exact_float,
    _validated_outcome_key,
    require_matching_range_gated_association_guide,
)
from .association_observation import AssociationObservationResourceError
from .association_preconditioner import (
    ANALYTIC_GUIDE_RANGE_SCHEMA_VERSION,
    MAX_PRECONDITIONER_EVALUATION_WORK,
    AnalyticAssociationPreconditioner,
    AnalyticGuideRangeCertificate,
    AssociationPreconditionerNumericalError,
    BoundPreconditionerEvaluation,
    PreconditionerObservation,
    _fraction_from_float,
    _plain_key_sha256,
    _validated_trusted_key,
)
from .configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    MAX_REFERENCE_DENSITY_COORDINATES,
    TransformedConfiguration,
)


TOTALIZED_JUMP_GUIDE_SCHEMA_VERSION = "totalized-association-jump-guide-v1"
TOTALIZED_JUMP_GUIDE_POLICY = (
    "preserve-range-gated-success-bitwise;"
    "typed-numerical-or-range-point-failure-to-fixed-certified-midpoint;"
    "never-totalize-input-resource-provenance-or-live-binding-failure;"
    "edits-are-differences-of-two-totalized-point-values"
)
TOTALIZED_JUMP_GUIDE_CERTIFICATE_SCOPE = (
    "fixed-collapsed-observation;full-capped-finite-binary64-point-domain;"
    "deterministic-point-liveness-under-declared-resource-contract;"
    "coarse-point-and-edit-discrepancy-bounds;operational-surrogate-potential;"
    "jump-only;frozen-runtime-specific;not-exact-conditional-or-posterior-target;"
    "not-coordinate-derivative;not-continuous-drift;not-rate-envelope;"
    "not-operational-clock;not-randomness;not-sampler-admission;"
    "not-portable-across-runtime-or-unrecorded-blas-implementations"
)
TOTALIZED_JUMP_GUIDE_RESOURCE_DOMAIN_POLICY = (
    "fixed-outcome-full-domain-preflight;all-reverse-times-in-horizon;"
    "all-process-canonical-finite-binary64-states-through-certified-cap"
)
TOTALIZED_JUMP_GUIDE_MIDPOINT_ALGORITHM = (
    "exact-fraction-endpoint-midpoint-rounded-once-to-binary64-nearest-even"
)

PRESERVED_RANGE_GATED_BRANCH = "preserved-range-gated"
NUMERICAL_FALLBACK_BRANCH = "numerical-fallback"
RANGE_FALLBACK_BRANCH = "range-fallback"
_EVALUATION_BRANCHES = (
    PRESERVED_RANGE_GATED_BRANCH,
    NUMERICAL_FALLBACK_BRANCH,
    RANGE_FALLBACK_BRANCH,
)

_CERTIFICATE_TOKEN = object()
_EVALUATION_TOKEN = object()
_EDIT_TOKEN = object()
_GUIDE_TOKEN = object()


class AssociationGuideTotalizationError(ArithmeticError):
    """Raised when the totalized jump contract itself is unrepresentable."""


def _canonical_zero(value: float) -> float:
    return 0.0 if value == 0.0 else value


def _evaluator_runtime_key() -> Tuple[object, ...]:
    """Return the declared, deliberately incomplete runtime identity."""

    return (
        "totalized-association-guide-runtime-v1",
        sys.implementation.name,
        platform.python_implementation(),
        platform.python_version(),
        platform.system(),
        platform.machine(),
        np.__version__,
        scipy.__version__,
        ANALYTIC_GUIDE_RANGE_SCHEMA_VERSION,
        RANGE_GATED_GUIDE_SCHEMA_VERSION,
        TOTALIZED_JUMP_GUIDE_SCHEMA_VERSION,
    )


def _evaluator_runtime_sha256() -> str:
    return _plain_key_sha256(
        _evaluator_runtime_key(),
        domain=b"heterodiff-totalized-jump-guide-runtime-v1\x00",
    )


def _state_sha256(
    state: object,
    *,
    maximum_cardinality: int,
) -> str:
    """Hash a validated state with bounded-memory binary framing."""

    _state_key(state, maximum_cardinality=maximum_cardinality)
    canonical = state
    digest = hashlib.sha256()
    digest.update(b"heterodiff-totalized-jump-guide-state-v1\x00")
    digest.update(struct.pack(">Q", len(canonical)))
    for event in canonical:
        digest.update(b"E")
        digest.update(struct.pack(">Q", event.event_type))
        digest.update(struct.pack(">Q", len(event.coordinates)))
        for coordinate in event.coordinates:
            digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _validated_nonnegative_integer(
    value: object,
    *,
    name: str,
    maximum: int,
) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value < 0 or value > maximum:
        raise ValueError("%s lies outside the implementation limit" % name)
    return value


def _outward_nonnegative_fraction(value: Fraction, *, name: str) -> float:
    """Round a nonnegative exact rational toward positive infinity."""

    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    try:
        rounded = float(value)
    except OverflowError as error:
        raise AssociationGuideTotalizationError(
            "%s has no finite binary64 upper witness" % name
        ) from error
    if not math.isfinite(rounded):
        raise AssociationGuideTotalizationError(
            "%s has no finite binary64 upper witness" % name
        )
    if _fraction_from_float(rounded) < value:
        rounded = math.nextafter(rounded, math.inf)
    if not math.isfinite(rounded):
        raise AssociationGuideTotalizationError(
            "%s cannot be rounded outward in binary64" % name
        )
    return _canonical_zero(rounded)


def _rounded_fraction_midpoint(lower: float, upper: float) -> Tuple[Fraction, float]:
    exact = (_fraction_from_float(lower) + _fraction_from_float(upper)) / 2
    try:
        represented = float(exact)
    except OverflowError as error:
        raise AssociationGuideTotalizationError(
            "the exact interval midpoint is not representable in finite binary64"
        ) from error
    if not math.isfinite(represented):
        raise AssociationGuideTotalizationError(
            "the exact interval midpoint is not representable in finite binary64"
        )
    represented = _canonical_zero(represented)
    if represented < lower or represented > upper:
        raise AssociationGuideTotalizationError(
            "the rounded interval midpoint lies outside its finite endpoints"
        )
    return exact, represented


def _fallback_point_bound(lower: float, upper: float, midpoint: float) -> float:
    represented = _fraction_from_float(midpoint)
    discrepancy = max(
        represented - _fraction_from_float(lower),
        _fraction_from_float(upper) - represented,
    )
    return _outward_nonnegative_fraction(
        discrepancy,
        name="fallback point discrepancy",
    )


def _outward_float_sum(left: float, right: float, *, name: str) -> float:
    return _outward_nonnegative_fraction(
        _fraction_from_float(left) + _fraction_from_float(right),
        name=name,
    )


def _certificate_contract_key(values: dict[str, object]) -> Tuple[object, ...]:
    return (
        values["schema_version"],
        values["certificate_scope"],
        values["totalization_policy"],
        values["preconditioner_parameter_key"],
        values["outcome_key"],
        values["analytic_range_certificate_sha256"],
        values["range_gate_certificate_sha256"],
        values["evaluator_runtime_sha256"],
        values["state_cap"],
        values["maximum_coordinate_count"],
        values["reverse_time_horizon"],
        values["operational_log_lower_bound"],
        values["operational_log_upper_bound"],
        values["fallback_midpoint_numerator"],
        values["fallback_midpoint_denominator"],
        values["fallback_operational_log_density"],
        values["represented_to_exact_point_log_discrepancy_bound"],
        values["fallback_to_exact_point_log_discrepancy_bound"],
        values["represented_edit_log_magnitude_bound"],
        values["represented_to_exact_edit_log_discrepancy_bound"],
        values["maximum_capped_point_evaluation_work"],
        values["resource_domain_policy"],
        values["midpoint_rounding_algorithm"],
    )


def _certificate_fields() -> Tuple[str, ...]:
    return (
        "schema_version",
        "certificate_scope",
        "totalization_policy",
        "preconditioner_parameter_key",
        "outcome_key",
        "analytic_range_certificate_sha256",
        "range_gate_certificate_sha256",
        "evaluator_runtime_sha256",
        "state_cap",
        "maximum_coordinate_count",
        "reverse_time_horizon",
        "operational_log_lower_bound",
        "operational_log_upper_bound",
        "fallback_midpoint_numerator",
        "fallback_midpoint_denominator",
        "fallback_operational_log_density",
        "represented_to_exact_point_log_discrepancy_bound",
        "fallback_to_exact_point_log_discrepancy_bound",
        "represented_edit_log_magnitude_bound",
        "represented_to_exact_edit_log_discrepancy_bound",
        "maximum_capped_point_evaluation_work",
        "resource_domain_policy",
        "midpoint_rounding_algorithm",
        "certificate_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpGuideCertificate:
    """Certificate for one fixed-outcome totalized operational jump guide."""

    schema_version: str
    certificate_scope: str
    totalization_policy: str
    preconditioner_parameter_key: Tuple[object, ...]
    outcome_key: Tuple[object, ...]
    analytic_range_certificate_sha256: str
    range_gate_certificate_sha256: str
    evaluator_runtime_sha256: str
    state_cap: int
    maximum_coordinate_count: int
    reverse_time_horizon: float
    operational_log_lower_bound: float
    operational_log_upper_bound: float
    fallback_midpoint_numerator: int
    fallback_midpoint_denominator: int
    fallback_operational_log_density: float
    represented_to_exact_point_log_discrepancy_bound: float
    fallback_to_exact_point_log_discrepancy_bound: float
    represented_edit_log_magnitude_bound: float
    represented_to_exact_edit_log_discrepancy_bound: float
    maximum_capped_point_evaluation_work: int
    resource_domain_policy: str
    midpoint_rounding_algorithm: str
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("TotalizedJumpGuideCertificate cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("totalized jump-guide certificates are not pickleable")

    def __init__(
        self,
        *,
        _construction_token: object = None,
        **raw_values: object,
    ) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError(
                "totalized jump-guide certificates can only be created by "
                "the certification factory"
            )
        names = _certificate_fields()
        if set(raw_values) != set(names):
            raise TypeError(
                "totalized jump-guide certificate fields do not match the schema"
            )
        values = dict(raw_values)
        if values["schema_version"] != TOTALIZED_JUMP_GUIDE_SCHEMA_VERSION:
            raise ValueError("unknown totalized jump-guide schema")
        if values["certificate_scope"] != TOTALIZED_JUMP_GUIDE_CERTIFICATE_SCOPE:
            raise ValueError("unknown totalized jump-guide certificate scope")
        if values["totalization_policy"] != TOTALIZED_JUMP_GUIDE_POLICY:
            raise ValueError("unknown totalized jump-guide policy")
        if (
            values["resource_domain_policy"]
            != TOTALIZED_JUMP_GUIDE_RESOURCE_DOMAIN_POLICY
        ):
            raise ValueError("unknown totalized jump-guide resource policy")
        if (
            values["midpoint_rounding_algorithm"]
            != TOTALIZED_JUMP_GUIDE_MIDPOINT_ALGORITHM
        ):
            raise ValueError("unknown totalized jump-guide midpoint algorithm")
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        values["outcome_key"] = _validated_outcome_key(values["outcome_key"])
        for name in (
            "analytic_range_certificate_sha256",
            "range_gate_certificate_sha256",
            "evaluator_runtime_sha256",
            "certificate_sha256",
        ):
            values[name] = _validated_digest(values[name], name=name)
        values["state_cap"] = _validated_nonnegative_integer(
            values["state_cap"],
            name="state_cap",
            maximum=MAX_CONFIGURATION_CARDINALITY,
        )
        values["maximum_coordinate_count"] = _validated_nonnegative_integer(
            values["maximum_coordinate_count"],
            name="maximum_coordinate_count",
            maximum=MAX_REFERENCE_DENSITY_COORDINATES,
        )
        values["maximum_capped_point_evaluation_work"] = _validated_nonnegative_integer(
            values["maximum_capped_point_evaluation_work"],
            name="maximum_capped_point_evaluation_work",
            maximum=MAX_PRECONDITIONER_EVALUATION_WORK,
        )
        for name in ("fallback_midpoint_numerator", "fallback_midpoint_denominator"):
            if type(values[name]) is not int or isinstance(values[name], bool):
                raise TypeError("%s must be an exact integer" % name)
        if values["fallback_midpoint_denominator"] <= 0:
            raise ValueError("fallback_midpoint_denominator must be positive")
        exact_midpoint = Fraction(
            values["fallback_midpoint_numerator"],
            values["fallback_midpoint_denominator"],
        )
        if (
            exact_midpoint.numerator != values["fallback_midpoint_numerator"]
            or exact_midpoint.denominator != values["fallback_midpoint_denominator"]
        ):
            raise ValueError("fallback midpoint fraction must be reduced")
        for name, nonnegative in (
            ("reverse_time_horizon", True),
            ("operational_log_lower_bound", False),
            ("operational_log_upper_bound", False),
            ("fallback_operational_log_density", False),
            ("represented_to_exact_point_log_discrepancy_bound", True),
            ("fallback_to_exact_point_log_discrepancy_bound", True),
            ("represented_edit_log_magnitude_bound", True),
            ("represented_to_exact_edit_log_discrepancy_bound", True),
        ):
            values[name] = _validated_exact_float(
                values[name],
                name=name,
                nonnegative=nonnegative,
            )
        lower = values["operational_log_lower_bound"]
        upper = values["operational_log_upper_bound"]
        if lower > upper:
            raise ValueError("totalized operational guide interval is empty")
        expected_exact_midpoint, expected_midpoint = _rounded_fraction_midpoint(
            lower,
            upper,
        )
        if exact_midpoint != expected_exact_midpoint:
            raise ValueError("fallback midpoint fraction does not match the interval")
        if not _same_float(
            values["fallback_operational_log_density"], expected_midpoint
        ):
            raise ValueError("fallback operational value is not the rounded midpoint")
        exact_width = _fraction_from_float(upper) - _fraction_from_float(lower)
        expected_width = _outward_nonnegative_fraction(
            exact_width,
            name="represented point discrepancy",
        )
        if not _same_float(
            values["represented_to_exact_point_log_discrepancy_bound"],
            expected_width,
        ):
            raise ValueError("represented point discrepancy is not the interval width")
        if not _same_float(
            values["represented_edit_log_magnitude_bound"], expected_width
        ):
            raise ValueError("represented edit magnitude is not the interval width")
        expected_fallback_bound = _fallback_point_bound(
            lower,
            upper,
            expected_midpoint,
        )
        if not _same_float(
            values["fallback_to_exact_point_log_discrepancy_bound"],
            expected_fallback_bound,
        ):
            raise ValueError("fallback point discrepancy does not match the midpoint")
        expected_edit_discrepancy = _outward_float_sum(
            expected_width,
            expected_width,
            name="represented edit discrepancy",
        )
        if not _same_float(
            values["represented_to_exact_edit_log_discrepancy_bound"],
            expected_edit_discrepancy,
        ):
            raise ValueError("represented edit discrepancy is not outward 2W")
        expected_digest = _plain_key_sha256(
            _certificate_contract_key(values),
            domain=b"heterodiff-totalized-jump-guide-certificate-v1\x00",
        )
        if values["certificate_sha256"] != expected_digest:
            raise ValueError("certificate_sha256 does not match certificate fields")
        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def totalized_point_evaluation_admissible(self) -> bool:
        return True

    @property
    def raw_value_preserved_on_success(self) -> bool:
        return True

    @property
    def operational_jump_guide_admissible(self) -> bool:
        return True

    @property
    def defines_operational_surrogate_jump_potential(self) -> bool:
        return True

    @property
    def exact_conditional_or_posterior_target(self) -> bool:
        return False

    @property
    def exact_analytic_target_preserved(self) -> bool:
        return False

    @property
    def jump_only(self) -> bool:
        return True

    @property
    def operational_coordinate_derivatives_admissible(self) -> bool:
        return False

    @property
    def operational_continuous_drift_admissible(self) -> bool:
        return False

    @property
    def operational_rate_envelope_admissible(self) -> bool:
        return False

    @property
    def operational_clock_admissible(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    @property
    def runtime_portable(self) -> bool:
        return False

    @property
    def blas_identity_authenticated(self) -> bool:
        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "totalized-jump-guide-certificate-v1",
            self.preconditioner_parameter_key,
            self.outcome_key,
            self.analytic_range_certificate_sha256,
            self.range_gate_certificate_sha256,
            self.evaluator_runtime_sha256,
            self.certificate_sha256,
        )


def _evaluation_contract_key(values: dict[str, object]) -> Tuple[object, ...]:
    return (
        values["preconditioner_parameter_key"],
        values["totalized_certificate_sha256"],
        values["analytic_range_certificate_sha256"],
        values["range_gate_certificate_sha256"],
        values["outcome_key"],
        values["state_cap"],
        values["reverse_time"],
        values["state_sha256"],
        values["branch"],
        values["raw_log_density"],
        values["operational_log_density"],
        values["operational_log_lower_bound"],
        values["operational_log_upper_bound"],
        values["point_log_discrepancy_bound"],
        values["represented_edit_log_magnitude_bound"],
        values["evaluation_algorithm"],
        values["totalization_policy"],
    )


def _evaluation_fields() -> Tuple[str, ...]:
    return (
        "preconditioner_parameter_key",
        "totalized_certificate_sha256",
        "analytic_range_certificate_sha256",
        "range_gate_certificate_sha256",
        "outcome_key",
        "state_cap",
        "reverse_time",
        "state",
        "state_sha256",
        "branch",
        "raw_log_density",
        "operational_log_density",
        "operational_log_lower_bound",
        "operational_log_upper_bound",
        "point_log_discrepancy_bound",
        "represented_edit_log_magnitude_bound",
        "evaluation_algorithm",
        "totalization_policy",
        "evaluation_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpGuideEvaluation:
    """One preserved or deterministically totalized point evaluation."""

    preconditioner_parameter_key: Tuple[object, ...]
    totalized_certificate_sha256: str
    analytic_range_certificate_sha256: str
    range_gate_certificate_sha256: str
    outcome_key: Tuple[object, ...]
    state_cap: int
    reverse_time: float
    state: TransformedConfiguration
    state_sha256: str
    branch: str
    raw_log_density: Optional[float]
    operational_log_density: float
    operational_log_lower_bound: float
    operational_log_upper_bound: float
    point_log_discrepancy_bound: float
    represented_edit_log_magnitude_bound: float
    evaluation_algorithm: str
    totalization_policy: str
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("TotalizedJumpGuideEvaluation cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("totalized jump-guide evaluations are not pickleable")

    def __init__(
        self,
        *,
        _construction_token: object = None,
        **raw_values: object,
    ) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError(
                "totalized jump-guide evaluations can only be created by "
                "a certified guide"
            )
        names = _evaluation_fields()
        if set(raw_values) != set(names):
            raise TypeError(
                "totalized jump-guide evaluation fields do not match the schema"
            )
        values = dict(raw_values)
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        for name in (
            "totalized_certificate_sha256",
            "analytic_range_certificate_sha256",
            "range_gate_certificate_sha256",
            "evaluation_sha256",
        ):
            values[name] = _validated_digest(values[name], name=name)
        values["outcome_key"] = _validated_outcome_key(values["outcome_key"])
        values["state_cap"] = _validated_nonnegative_integer(
            values["state_cap"],
            name="state_cap",
            maximum=MAX_CONFIGURATION_CARDINALITY,
        )
        _state_key(values["state"], maximum_cardinality=values["state_cap"])
        values["state_sha256"] = _validated_digest(
            values["state_sha256"], name="state_sha256"
        )
        if values["state_sha256"] != _state_sha256(
            values["state"], maximum_cardinality=values["state_cap"]
        ):
            raise ValueError("state_sha256 does not match the stored state")
        for name, nonnegative in (
            ("reverse_time", True),
            ("operational_log_density", False),
            ("operational_log_lower_bound", False),
            ("operational_log_upper_bound", False),
            ("point_log_discrepancy_bound", True),
            ("represented_edit_log_magnitude_bound", True),
        ):
            values[name] = _validated_exact_float(
                values[name],
                name=name,
                nonnegative=nonnegative,
            )
        if values["branch"] not in _EVALUATION_BRANCHES:
            raise ValueError("unknown totalized point-evaluation branch")
        if values["totalization_policy"] != TOTALIZED_JUMP_GUIDE_POLICY:
            raise ValueError("unknown totalized point-evaluation policy")
        if (
            type(values["evaluation_algorithm"]) is not str
            or not values["evaluation_algorithm"]
        ):
            raise TypeError("evaluation_algorithm must be nonempty exact text")
        lower = values["operational_log_lower_bound"]
        upper = values["operational_log_upper_bound"]
        operational = values["operational_log_density"]
        if lower > upper or not lower <= operational <= upper:
            raise ValueError("operational log density lies outside its interval")
        if (
            values["point_log_discrepancy_bound"]
            > values["represented_edit_log_magnitude_bound"]
        ):
            raise ValueError("point discrepancy exceeds the global interval width")
        if values["branch"] == PRESERVED_RANGE_GATED_BRANCH:
            if values["raw_log_density"] is None:
                raise ValueError("preserved evaluation lacks its raw log density")
            values["raw_log_density"] = _validated_exact_float(
                values["raw_log_density"],
                name="raw_log_density",
            )
            if not _same_float(
                values["raw_log_density"], values["operational_log_density"]
            ):
                raise ValueError("preserved evaluation changed the raw value")
            if not _same_float(
                values["point_log_discrepancy_bound"],
                values["represented_edit_log_magnitude_bound"],
            ):
                raise ValueError("preserved evaluation must use the global width")
        else:
            if values["raw_log_density"] is not None:
                raise ValueError("fallback evaluation cannot expose a raw value")
        expected_digest = _plain_key_sha256(
            _evaluation_contract_key(values),
            domain=b"heterodiff-totalized-jump-guide-evaluation-v1\x00",
        )
        if values["evaluation_sha256"] != expected_digest:
            raise ValueError("evaluation_sha256 does not match evaluation fields")
        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def fallback_used(self) -> bool:
        return self.branch != PRESERVED_RANGE_GATED_BRANCH

    @property
    def raw_value_preserved(self) -> bool:
        return self.branch == PRESERVED_RANGE_GATED_BRANCH

    @property
    def defines_operational_surrogate_jump_potential(self) -> bool:
        return True

    @property
    def exact_conditional_or_posterior_target(self) -> bool:
        return False

    @property
    def operational_coordinate_derivatives_admissible(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "totalized-jump-guide-evaluation-v1",
            self.totalized_certificate_sha256,
            self.evaluation_sha256,
        )


def _edit_contract_key(values: dict[str, object]) -> Tuple[object, ...]:
    return (
        values["preconditioner_parameter_key"],
        values["totalized_certificate_sha256"],
        values["analytic_range_certificate_sha256"],
        values["range_gate_certificate_sha256"],
        values["outcome_key"],
        values["state_cap"],
        values["reverse_time"],
        values["edit_kind"],
        values["source_state_sha256"],
        values["destination_state_sha256"],
        values["source_evaluation_sha256"],
        values["destination_evaluation_sha256"],
        values["source_branch"],
        values["destination_branch"],
        values["source_operational_log_density"],
        values["destination_operational_log_density"],
        values["source_point_log_discrepancy_bound"],
        values["destination_point_log_discrepancy_bound"],
        values["exact_operational_endpoint_difference_numerator"],
        values["exact_operational_endpoint_difference_denominator"],
        values["log_ratio"],
        values["represented_edit_log_magnitude_bound"],
        values["represented_to_exact_edit_log_discrepancy_bound"],
        values["totalization_policy"],
    )


def _edit_fields() -> Tuple[str, ...]:
    return (
        "preconditioner_parameter_key",
        "totalized_certificate_sha256",
        "analytic_range_certificate_sha256",
        "range_gate_certificate_sha256",
        "outcome_key",
        "state_cap",
        "reverse_time",
        "edit_kind",
        "source_state",
        "destination_state",
        "source_state_sha256",
        "destination_state_sha256",
        "source_evaluation_sha256",
        "destination_evaluation_sha256",
        "source_branch",
        "destination_branch",
        "source_operational_log_density",
        "destination_operational_log_density",
        "source_point_log_discrepancy_bound",
        "destination_point_log_discrepancy_bound",
        "exact_operational_endpoint_difference_numerator",
        "exact_operational_endpoint_difference_denominator",
        "log_ratio",
        "represented_edit_log_magnitude_bound",
        "represented_to_exact_edit_log_discrepancy_bound",
        "totalization_policy",
        "edit_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpGuideEditRatio:
    """One legal jump edit formed from two totalized point evaluations."""

    preconditioner_parameter_key: Tuple[object, ...]
    totalized_certificate_sha256: str
    analytic_range_certificate_sha256: str
    range_gate_certificate_sha256: str
    outcome_key: Tuple[object, ...]
    state_cap: int
    reverse_time: float
    edit_kind: str
    source_state: TransformedConfiguration
    destination_state: TransformedConfiguration
    source_state_sha256: str
    destination_state_sha256: str
    source_evaluation_sha256: str
    destination_evaluation_sha256: str
    source_branch: str
    destination_branch: str
    source_operational_log_density: float
    destination_operational_log_density: float
    source_point_log_discrepancy_bound: float
    destination_point_log_discrepancy_bound: float
    exact_operational_endpoint_difference_numerator: int
    exact_operational_endpoint_difference_denominator: int
    log_ratio: float
    represented_edit_log_magnitude_bound: float
    represented_to_exact_edit_log_discrepancy_bound: float
    totalization_policy: str
    edit_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("TotalizedJumpGuideEditRatio cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("totalized jump-guide edits are not pickleable")

    def __init__(
        self,
        *,
        _construction_token: object = None,
        **raw_values: object,
    ) -> None:
        if _construction_token is not _EDIT_TOKEN:
            raise TypeError(
                "totalized jump-guide edits can only be created by a certified guide"
            )
        names = _edit_fields()
        if set(raw_values) != set(names):
            raise TypeError("totalized jump-guide edit fields do not match the schema")
        values = dict(raw_values)
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        for name in (
            "totalized_certificate_sha256",
            "analytic_range_certificate_sha256",
            "range_gate_certificate_sha256",
            "source_evaluation_sha256",
            "destination_evaluation_sha256",
            "edit_sha256",
        ):
            values[name] = _validated_digest(values[name], name=name)
        values["outcome_key"] = _validated_outcome_key(values["outcome_key"])
        values["state_cap"] = _validated_nonnegative_integer(
            values["state_cap"],
            name="state_cap",
            maximum=MAX_CONFIGURATION_CARDINALITY,
        )
        _state_key(values["source_state"], maximum_cardinality=values["state_cap"])
        _state_key(values["destination_state"], maximum_cardinality=values["state_cap"])
        for name, state_name in (
            ("source_state_sha256", "source_state"),
            ("destination_state_sha256", "destination_state"),
        ):
            values[name] = _validated_digest(values[name], name=name)
            if values[name] != _state_sha256(
                values[state_name], maximum_cardinality=values["state_cap"]
            ):
                raise ValueError("%s does not match the stored state" % name)
        for name in (
            "exact_operational_endpoint_difference_numerator",
            "exact_operational_endpoint_difference_denominator",
        ):
            if type(values[name]) is not int or isinstance(values[name], bool):
                raise TypeError("%s must be an exact integer" % name)
        if values["exact_operational_endpoint_difference_denominator"] <= 0:
            raise ValueError(
                "exact_operational_endpoint_difference_denominator must be positive"
            )
        exact_operational_difference = Fraction(
            values["exact_operational_endpoint_difference_numerator"],
            values["exact_operational_endpoint_difference_denominator"],
        )
        if (
            exact_operational_difference.numerator
            != values["exact_operational_endpoint_difference_numerator"]
            or exact_operational_difference.denominator
            != values["exact_operational_endpoint_difference_denominator"]
        ):
            raise ValueError(
                "exact operational endpoint-difference fraction must be reduced"
            )
        for name, nonnegative in (
            ("reverse_time", True),
            ("source_operational_log_density", False),
            ("destination_operational_log_density", False),
            ("source_point_log_discrepancy_bound", True),
            ("destination_point_log_discrepancy_bound", True),
            ("log_ratio", False),
            ("represented_edit_log_magnitude_bound", True),
            ("represented_to_exact_edit_log_discrepancy_bound", True),
        ):
            values[name] = _validated_exact_float(
                values[name],
                name=name,
                nonnegative=nonnegative,
            )
        if values["edit_kind"] not in ("birth", "death", "replacement"):
            raise ValueError("unknown totalized jump edit kind")
        if values["source_branch"] not in _EVALUATION_BRANCHES:
            raise ValueError("unknown source point-evaluation branch")
        if values["destination_branch"] not in _EVALUATION_BRANCHES:
            raise ValueError("unknown destination point-evaluation branch")
        if values["totalization_policy"] != TOTALIZED_JUMP_GUIDE_POLICY:
            raise ValueError("unknown totalized jump edit policy")
        expected_exact_ratio = _fraction_from_float(
            values["destination_operational_log_density"]
        ) - _fraction_from_float(values["source_operational_log_density"])
        if exact_operational_difference != expected_exact_ratio:
            raise ValueError(
                "exact operational endpoint difference does not match its endpoints"
            )
        expected_ratio = _canonical_zero(float(expected_exact_ratio))
        if not math.isfinite(expected_ratio):
            raise ValueError("exact endpoint difference has no finite binary64 value")
        if not math.isfinite(expected_ratio) or not _same_float(
            values["log_ratio"], expected_ratio
        ):
            raise ValueError("log_ratio does not match its endpoint point values")
        if abs(values["log_ratio"]) > values["represented_edit_log_magnitude_bound"]:
            raise ValueError("totalized edit exceeds the represented magnitude bound")
        for name in (
            "source_point_log_discrepancy_bound",
            "destination_point_log_discrepancy_bound",
        ):
            if values[name] > values["represented_edit_log_magnitude_bound"]:
                raise ValueError("endpoint discrepancy exceeds the interval width")
        expected_discrepancy = _outward_float_sum(
            values["source_point_log_discrepancy_bound"],
            values["destination_point_log_discrepancy_bound"],
            name="endpoint edit discrepancy",
        )
        if not _same_float(
            values["represented_to_exact_edit_log_discrepancy_bound"],
            expected_discrepancy,
        ):
            raise ValueError("edit discrepancy does not equal its endpoint sum")
        expected_digest = _plain_key_sha256(
            _edit_contract_key(values),
            domain=b"heterodiff-totalized-jump-guide-edit-v1\x00",
        )
        if values["edit_sha256"] != expected_digest:
            raise ValueError("edit_sha256 does not match edit fields")
        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def fallback_used(self) -> bool:
        return (
            self.source_branch != PRESERVED_RANGE_GATED_BRANCH
            or self.destination_branch != PRESERVED_RANGE_GATED_BRANCH
        )

    @property
    def operational_jump_guide_admissible(self) -> bool:
        return True

    @property
    def defines_operational_surrogate_jump_potential(self) -> bool:
        return True

    @property
    def exact_conditional_or_posterior_target(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "totalized-jump-guide-edit-v1",
            self.totalized_certificate_sha256,
            self.edit_sha256,
        )


def _make_certificate(
    preconditioner: AnalyticAssociationPreconditioner,
    range_gate: RangeGatedAssociationGuide,
    range_certificate: AnalyticGuideRangeCertificate,
    maximum_capped_point_evaluation_work: int,
) -> TotalizedJumpGuideCertificate:
    lower = range_gate.certificate.operational_log_lower_bound
    upper = range_gate.certificate.operational_log_upper_bound
    exact_midpoint, represented_midpoint = _rounded_fraction_midpoint(lower, upper)
    width = _outward_nonnegative_fraction(
        _fraction_from_float(upper) - _fraction_from_float(lower),
        name="totalized point discrepancy",
    )
    fallback_bound = _fallback_point_bound(lower, upper, represented_midpoint)
    edit_discrepancy = _outward_float_sum(
        width,
        width,
        name="totalized edit discrepancy",
    )
    values: dict[str, object] = {
        "schema_version": TOTALIZED_JUMP_GUIDE_SCHEMA_VERSION,
        "certificate_scope": TOTALIZED_JUMP_GUIDE_CERTIFICATE_SCOPE,
        "totalization_policy": TOTALIZED_JUMP_GUIDE_POLICY,
        "preconditioner_parameter_key": preconditioner.parameter_key(),
        "outcome_key": range_certificate.outcome_key,
        "analytic_range_certificate_sha256": range_certificate.certificate_sha256,
        "range_gate_certificate_sha256": range_gate.certificate.certificate_sha256,
        "evaluator_runtime_sha256": _evaluator_runtime_sha256(),
        "state_cap": range_certificate.state_cap,
        "maximum_coordinate_count": range_certificate.maximum_coordinate_count,
        "reverse_time_horizon": preconditioner.process.schedule.horizon,
        "operational_log_lower_bound": lower,
        "operational_log_upper_bound": upper,
        "fallback_midpoint_numerator": exact_midpoint.numerator,
        "fallback_midpoint_denominator": exact_midpoint.denominator,
        "fallback_operational_log_density": represented_midpoint,
        "represented_to_exact_point_log_discrepancy_bound": width,
        "fallback_to_exact_point_log_discrepancy_bound": fallback_bound,
        "represented_edit_log_magnitude_bound": width,
        "represented_to_exact_edit_log_discrepancy_bound": edit_discrepancy,
        "maximum_capped_point_evaluation_work": (maximum_capped_point_evaluation_work),
        "resource_domain_policy": TOTALIZED_JUMP_GUIDE_RESOURCE_DOMAIN_POLICY,
        "midpoint_rounding_algorithm": TOTALIZED_JUMP_GUIDE_MIDPOINT_ALGORITHM,
    }
    digest = _plain_key_sha256(
        _certificate_contract_key(values),
        domain=b"heterodiff-totalized-jump-guide-certificate-v1\x00",
    )
    return TotalizedJumpGuideCertificate(
        **values,
        certificate_sha256=digest,
        _construction_token=_CERTIFICATE_TOKEN,
    )


class TotalizedAssociationJumpGuide:
    """Immutable fixed-outcome evaluator for the totalized jump point function."""

    __slots__ = (
        "_preconditioner",
        "_range_gate",
        "_range_certificate",
        "_outcome",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("TotalizedAssociationJumpGuide cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("totalized association jump guides are not pickleable")

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("TotalizedAssociationJumpGuide is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("TotalizedAssociationJumpGuide is immutable")

    def __init__(
        self,
        preconditioner: AnalyticAssociationPreconditioner,
        range_gate: RangeGatedAssociationGuide,
        range_certificate: AnalyticGuideRangeCertificate,
        outcome: PreconditionerObservation,
        certificate: TotalizedJumpGuideCertificate,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _GUIDE_TOKEN:
            raise TypeError(
                "totalized association jump guides can only be created by "
                "the certification factory"
            )
        if type(preconditioner) is not AnalyticAssociationPreconditioner:
            raise TypeError(
                "preconditioner must be an exact AnalyticAssociationPreconditioner"
            )
        if type(range_gate) is not RangeGatedAssociationGuide:
            raise TypeError("range_gate must be an exact RangeGatedAssociationGuide")
        if type(range_certificate) is not AnalyticGuideRangeCertificate:
            raise TypeError(
                "range_certificate must be an exact AnalyticGuideRangeCertificate"
            )
        if type(certificate) is not TotalizedJumpGuideCertificate:
            raise TypeError("certificate has the wrong type")
        checked_outcome = _copy_outcome(outcome)
        if (
            preconditioner._guide_outcome_key(checked_outcome)
            != certificate.outcome_key
        ):
            raise ValueError("totalized guide outcome does not match its certificate")
        object.__setattr__(self, "_preconditioner", preconditioner)
        object.__setattr__(self, "_range_gate", range_gate)
        object.__setattr__(self, "_range_certificate", range_certificate)
        object.__setattr__(self, "_outcome", checked_outcome)
        object.__setattr__(self, "_certificate", certificate)

    @property
    def preconditioner(self) -> AnalyticAssociationPreconditioner:
        return self._preconditioner

    @property
    def range_gate(self) -> RangeGatedAssociationGuide:
        return self._range_gate

    @property
    def range_certificate(self) -> AnalyticGuideRangeCertificate:
        return self._range_certificate

    @property
    def outcome(self) -> PreconditionerObservation:
        return self._outcome

    @property
    def certificate(self) -> TotalizedJumpGuideCertificate:
        return self._certificate

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "totalized-association-jump-guide-v1",
            self.certificate.parameter_key(),
        )

    def _require_live_binding(self) -> None:
        TotalizedJumpGuideCertificate(
            **{name: getattr(self.certificate, name) for name in _certificate_fields()},
            _construction_token=_CERTIFICATE_TOKEN,
        )
        require_matching_range_gated_association_guide(
            self.preconditioner,
            self.range_gate,
            self.range_certificate,
            observation=self.outcome,
        )
        if self.range_gate.preconditioner is not self.preconditioner:
            raise ValueError("range gate is bound to a different preconditioner")
        if self.range_gate.certificate.certificate_sha256 != (
            self.certificate.range_gate_certificate_sha256
        ):
            raise ValueError("live range gate differs from the totalized certificate")
        if self.range_certificate.certificate_sha256 != (
            self.certificate.analytic_range_certificate_sha256
        ):
            raise ValueError(
                "live analytic range certificate differs from the totalized certificate"
            )
        if self.certificate.evaluator_runtime_sha256 != _evaluator_runtime_sha256():
            raise ValueError("live evaluator runtime differs from the certificate")
        if self.preconditioner._guide_outcome_key(self.outcome) != (
            self.certificate.outcome_key
        ):
            raise ValueError("live outcome differs from the totalized certificate")
        if not _same_float(
            self.preconditioner.process.schedule.horizon,
            self.certificate.reverse_time_horizon,
        ):
            raise ValueError("live horizon differs from the totalized certificate")
        work = self.preconditioner.preflight_capped_point_evaluation_resources(
            self.outcome
        )
        if type(work) is not int or isinstance(work, bool):
            raise TypeError("point-evaluation preflight returned a non-integer")
        if work != self.certificate.maximum_capped_point_evaluation_work:
            raise ValueError("live point-evaluation preflight differs from certificate")

    def evaluate(
        self,
        reverse_time: object,
        state: object,
    ) -> TotalizedJumpGuideEvaluation:
        """Evaluate the totalized point function on one admitted state."""

        self._require_live_binding()
        expected_reverse_time = self.preconditioner._reverse_time(reverse_time)
        expected_reverse_time = _canonical_zero(expected_reverse_time)
        expected_state = self.preconditioner._canonical_restricted(state)
        _state_key(
            expected_state,
            maximum_cardinality=self.certificate.state_cap,
        )
        raw: Optional[BoundPreconditionerEvaluation]
        try:
            unchecked_raw = self.preconditioner.evaluate(
                expected_reverse_time,
                expected_state,
                self.outcome,
            )
        except AssociationPreconditionerNumericalError:
            branch = NUMERICAL_FALLBACK_BRANCH
            raw = None
        else:
            try:
                raw = self.range_gate._validate_raw_evaluation(
                    unchecked_raw,
                    expected_reverse_time=expected_reverse_time,
                    expected_state=expected_state,
                )
            except AssociationGuideOperationalError:
                branch = RANGE_FALLBACK_BRANCH
                raw = None
        self._require_live_binding()
        if raw is None:
            operational = self.certificate.fallback_operational_log_density
            raw_log: Optional[float] = None
            point_bound = self.certificate.fallback_to_exact_point_log_discrepancy_bound
            algorithm = self.certificate.midpoint_rounding_algorithm
        else:
            branch = PRESERVED_RANGE_GATED_BRANCH
            operational = raw.log_density
            raw_log = raw.log_density
            point_bound = (
                self.certificate.represented_to_exact_point_log_discrepancy_bound
            )
            algorithm = raw.association_evaluation.algorithm
        values: dict[str, object] = {
            "preconditioner_parameter_key": (
                self.certificate.preconditioner_parameter_key
            ),
            "totalized_certificate_sha256": self.certificate.certificate_sha256,
            "analytic_range_certificate_sha256": (
                self.certificate.analytic_range_certificate_sha256
            ),
            "range_gate_certificate_sha256": (
                self.certificate.range_gate_certificate_sha256
            ),
            "outcome_key": self.certificate.outcome_key,
            "state_cap": self.certificate.state_cap,
            "reverse_time": expected_reverse_time,
            "state": expected_state,
            "state_sha256": _state_sha256(
                expected_state,
                maximum_cardinality=self.certificate.state_cap,
            ),
            "branch": branch,
            "raw_log_density": raw_log,
            "operational_log_density": operational,
            "operational_log_lower_bound": (
                self.certificate.operational_log_lower_bound
            ),
            "operational_log_upper_bound": (
                self.certificate.operational_log_upper_bound
            ),
            "point_log_discrepancy_bound": point_bound,
            "represented_edit_log_magnitude_bound": (
                self.certificate.represented_edit_log_magnitude_bound
            ),
            "evaluation_algorithm": algorithm,
            "totalization_policy": self.certificate.totalization_policy,
        }
        digest = _plain_key_sha256(
            _evaluation_contract_key(values),
            domain=b"heterodiff-totalized-jump-guide-evaluation-v1\x00",
        )
        return TotalizedJumpGuideEvaluation(
            **values,
            evaluation_sha256=digest,
            _construction_token=_EVALUATION_TOKEN,
        )

    def validate_evaluation(
        self,
        evaluation: object,
    ) -> TotalizedJumpGuideEvaluation:
        """Reconstruct, replay, and require one exact point record."""

        if type(evaluation) is not TotalizedJumpGuideEvaluation:
            raise TypeError("evaluation must be an exact TotalizedJumpGuideEvaluation")
        TotalizedJumpGuideEvaluation(
            **{name: getattr(evaluation, name) for name in _evaluation_fields()},
            _construction_token=_EVALUATION_TOKEN,
        )
        expected = self.evaluate(evaluation.reverse_time, evaluation.state)
        for name in _evaluation_fields():
            supplied = getattr(evaluation, name)
            recomputed = getattr(expected, name)
            if type(supplied) is float and type(recomputed) is float:
                matches = _same_float(supplied, recomputed)
            else:
                matches = supplied == recomputed
            if not matches:
                raise ValueError(
                    "totalized evaluation field %s differs from recomputation" % name
                )
        return evaluation

    def edit_log_ratio(
        self,
        reverse_time: object,
        source_state: object,
        destination_state: object,
    ) -> TotalizedJumpGuideEditRatio:
        """Form one legal jump edit from two totalized point evaluations."""

        self._require_live_binding()
        expected_reverse_time = self.preconditioner._reverse_time(reverse_time)
        expected_reverse_time = _canonical_zero(expected_reverse_time)
        expected_source = self.preconditioner._canonical_restricted(source_state)
        expected_destination = self.preconditioner._canonical_restricted(
            destination_state
        )
        edit_kind = self.preconditioner._classify_edit(
            expected_source,
            expected_destination,
        )
        source = self.evaluate(expected_reverse_time, expected_source)
        destination = self.evaluate(expected_reverse_time, expected_destination)
        if source.outcome_key != destination.outcome_key:
            raise ValueError("totalized edit endpoints have different outcomes")
        exact_operational_difference = _fraction_from_float(
            destination.operational_log_density
        ) - _fraction_from_float(source.operational_log_density)
        try:
            log_ratio = _canonical_zero(float(exact_operational_difference))
        except OverflowError as error:
            raise AssociationGuideTotalizationError(
                "exact totalized endpoint difference is not representable"
            ) from error
        if not math.isfinite(log_ratio):
            raise AssociationGuideTotalizationError(
                "totalized endpoint difference is not finite"
            )
        if abs(log_ratio) > self.certificate.represented_edit_log_magnitude_bound:
            raise AssociationGuideTotalizationError(
                "totalized endpoint difference exceeds the interval width"
            )
        discrepancy = _outward_float_sum(
            source.point_log_discrepancy_bound,
            destination.point_log_discrepancy_bound,
            name="totalized endpoint edit discrepancy",
        )
        if discrepancy > (
            self.certificate.represented_to_exact_edit_log_discrepancy_bound
        ):
            raise AssociationGuideTotalizationError(
                "endpoint discrepancy exceeds the global edit discrepancy"
            )
        values: dict[str, object] = {
            "preconditioner_parameter_key": (
                self.certificate.preconditioner_parameter_key
            ),
            "totalized_certificate_sha256": self.certificate.certificate_sha256,
            "analytic_range_certificate_sha256": (
                self.certificate.analytic_range_certificate_sha256
            ),
            "range_gate_certificate_sha256": (
                self.certificate.range_gate_certificate_sha256
            ),
            "outcome_key": self.certificate.outcome_key,
            "state_cap": self.certificate.state_cap,
            "reverse_time": expected_reverse_time,
            "edit_kind": edit_kind,
            "source_state": source.state,
            "destination_state": destination.state,
            "source_state_sha256": source.state_sha256,
            "destination_state_sha256": destination.state_sha256,
            "source_evaluation_sha256": source.evaluation_sha256,
            "destination_evaluation_sha256": destination.evaluation_sha256,
            "source_branch": source.branch,
            "destination_branch": destination.branch,
            "source_operational_log_density": source.operational_log_density,
            "destination_operational_log_density": (
                destination.operational_log_density
            ),
            "source_point_log_discrepancy_bound": (source.point_log_discrepancy_bound),
            "destination_point_log_discrepancy_bound": (
                destination.point_log_discrepancy_bound
            ),
            "exact_operational_endpoint_difference_numerator": (
                exact_operational_difference.numerator
            ),
            "exact_operational_endpoint_difference_denominator": (
                exact_operational_difference.denominator
            ),
            "log_ratio": log_ratio,
            "represented_edit_log_magnitude_bound": (
                self.certificate.represented_edit_log_magnitude_bound
            ),
            "represented_to_exact_edit_log_discrepancy_bound": discrepancy,
            "totalization_policy": self.certificate.totalization_policy,
        }
        digest = _plain_key_sha256(
            _edit_contract_key(values),
            domain=b"heterodiff-totalized-jump-guide-edit-v1\x00",
        )
        return TotalizedJumpGuideEditRatio(
            **values,
            edit_sha256=digest,
            _construction_token=_EDIT_TOKEN,
        )

    def validate_edit_log_ratio(
        self,
        edit: object,
    ) -> TotalizedJumpGuideEditRatio:
        """Reconstruct, replay, and require one exact totalized edit."""

        if type(edit) is not TotalizedJumpGuideEditRatio:
            raise TypeError("edit must be an exact TotalizedJumpGuideEditRatio")
        TotalizedJumpGuideEditRatio(
            **{name: getattr(edit, name) for name in _edit_fields()},
            _construction_token=_EDIT_TOKEN,
        )
        expected = self.edit_log_ratio(
            edit.reverse_time,
            edit.source_state,
            edit.destination_state,
        )
        for name in _edit_fields():
            supplied = getattr(edit, name)
            recomputed = getattr(expected, name)
            if type(supplied) is float and type(recomputed) is float:
                matches = _same_float(supplied, recomputed)
            else:
                matches = supplied == recomputed
            if not matches:
                raise ValueError(
                    "totalized edit field %s differs from recomputation" % name
                )
        return edit


def certify_totalized_association_jump_guide(
    preconditioner: AnalyticAssociationPreconditioner,
    range_gate: RangeGatedAssociationGuide,
    range_certificate: AnalyticGuideRangeCertificate,
    observation: Optional[object] = None,
) -> TotalizedAssociationJumpGuide:
    """Certify one fixed-outcome totalized operational jump guide."""

    if type(preconditioner) is not AnalyticAssociationPreconditioner:
        raise TypeError(
            "preconditioner must be an exact AnalyticAssociationPreconditioner"
        )
    checked_gate = require_matching_range_gated_association_guide(
        preconditioner,
        range_gate,
        range_certificate,
        observation=observation,
    )
    checked_range = preconditioner.validate_guide_range_certificate(
        range_certificate,
        observation=checked_gate.outcome,
    )
    outcome = _copy_outcome(checked_range.outcome)
    work = preconditioner.preflight_capped_point_evaluation_resources(outcome)
    if type(work) is not int or isinstance(work, bool):
        raise TypeError("point-evaluation preflight returned a non-integer")
    if work < 0 or work > MAX_PRECONDITIONER_EVALUATION_WORK:
        raise AssociationObservationResourceError(
            "capped point-evaluation work lies outside the implementation limit"
        )
    certificate = _make_certificate(
        preconditioner,
        checked_gate,
        checked_range,
        work,
    )
    guide = TotalizedAssociationJumpGuide(
        preconditioner,
        checked_gate,
        checked_range,
        outcome,
        certificate,
        _construction_token=_GUIDE_TOKEN,
    )
    guide._require_live_binding()
    return guide


def require_matching_totalized_association_jump_guide(
    preconditioner: AnalyticAssociationPreconditioner,
    guide: TotalizedAssociationJumpGuide,
    range_gate: RangeGatedAssociationGuide,
    range_certificate: AnalyticGuideRangeCertificate,
    observation: Optional[object] = None,
) -> TotalizedAssociationJumpGuide:
    """Refuse unless every live model, outcome, range, and resource binding matches."""

    if type(preconditioner) is not AnalyticAssociationPreconditioner:
        raise TypeError(
            "preconditioner must be an exact AnalyticAssociationPreconditioner"
        )
    if type(guide) is not TotalizedAssociationJumpGuide:
        raise TypeError("guide must be an exact TotalizedAssociationJumpGuide")
    if type(range_gate) is not RangeGatedAssociationGuide:
        raise TypeError("range_gate must be an exact RangeGatedAssociationGuide")
    if guide.preconditioner is not preconditioner:
        raise ValueError("guide is bound to a different preconditioner object")
    if guide.range_gate is not range_gate:
        raise ValueError("guide is bound to a different range-gate object")
    checked_gate = require_matching_range_gated_association_guide(
        preconditioner,
        range_gate,
        range_certificate,
        observation=observation,
    )
    checked_range = preconditioner.validate_guide_range_certificate(
        range_certificate,
        observation=checked_gate.outcome,
    )
    if guide.range_certificate is not range_certificate:
        raise ValueError("guide is bound to a different range-certificate object")
    work = preconditioner.preflight_capped_point_evaluation_resources(
        checked_range.outcome
    )
    expected = _make_certificate(
        preconditioner,
        checked_gate,
        checked_range,
        work,
    )
    TotalizedJumpGuideCertificate(
        **{name: getattr(guide.certificate, name) for name in _certificate_fields()},
        _construction_token=_CERTIFICATE_TOKEN,
    )
    for name in _certificate_fields():
        supplied = getattr(guide.certificate, name)
        recomputed = getattr(expected, name)
        if type(supplied) is float and type(recomputed) is float:
            matches = _same_float(supplied, recomputed)
        else:
            matches = supplied == recomputed
        if not matches:
            raise ValueError(
                "totalized certificate field %s differs from recomputation" % name
            )
    guide._require_live_binding()
    return guide


def validate_totalized_jump_guide_certificate(
    preconditioner: AnalyticAssociationPreconditioner,
    guide: TotalizedAssociationJumpGuide,
    range_gate: RangeGatedAssociationGuide,
    range_certificate: AnalyticGuideRangeCertificate,
    observation: Optional[object] = None,
) -> TotalizedJumpGuideCertificate:
    """Return the recomputation-validated totalized jump-guide certificate."""

    return require_matching_totalized_association_jump_guide(
        preconditioner,
        guide,
        range_gate,
        range_certificate,
        observation=observation,
    ).certificate


__all__ = [
    "AssociationGuideTotalizationError",
    "NUMERICAL_FALLBACK_BRANCH",
    "PRESERVED_RANGE_GATED_BRANCH",
    "RANGE_FALLBACK_BRANCH",
    "TOTALIZED_JUMP_GUIDE_CERTIFICATE_SCOPE",
    "TOTALIZED_JUMP_GUIDE_MIDPOINT_ALGORITHM",
    "TOTALIZED_JUMP_GUIDE_POLICY",
    "TOTALIZED_JUMP_GUIDE_RESOURCE_DOMAIN_POLICY",
    "TOTALIZED_JUMP_GUIDE_SCHEMA_VERSION",
    "TotalizedAssociationJumpGuide",
    "TotalizedJumpGuideCertificate",
    "TotalizedJumpGuideEditRatio",
    "TotalizedJumpGuideEvaluation",
    "certify_totalized_association_jump_guide",
    "require_matching_totalized_association_jump_guide",
    "validate_totalized_jump_guide_certificate",
]
