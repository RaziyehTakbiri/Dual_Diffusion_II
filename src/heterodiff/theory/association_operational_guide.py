"""Fail-closed represented jump-guide bridge for the analytic preconditioner.

The analytic range certificate bounds the exact model guide, but the existing
floating-point evaluator has no small uniform forward-error bound on
unbounded Gaussian coordinates.  This module therefore implements a coarse
range gate.  A raw finite log-guide evaluation is preserved bit for bit only
when it lies inside rigorously directed model bounds; every other result is
refused.

For every successful result, the raw represented log guide and the exact
model log guide lie in the same certified interval.  Its width is consequently
a uniform, if potentially loose, discrepancy bound and a direct represented
jump-edit envelope.  This module does not certify coordinate gradients,
continuous drift, residual composition, a controlled clock, or a sampler.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import math
from typing import Optional, Tuple

from .association_observation import (
    MAX_AFFINE_OBSERVATION_DIMENSION,
    MAX_ASSOCIATION_OCCURRENCES,
    AssociationObservationResourceError,
)
from .association_preconditioner import (
    AnalyticAssociationPreconditioner,
    AnalyticGuideRangeCertificate,
    BoundPreconditionerEditRatio,
    BoundPreconditionerEvaluation,
    PreconditionerObservation,
    _decimal_log_fraction_upper,
    _fraction_from_float,
    _outward_sum_upper,
    _plain_key_sha256,
    _validated_trusted_key,
)
from .configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    MAX_REFERENCE_DENSITY_COORDINATES,
    TransformedConfiguration,
    TransformedEvent,
)
from .finite_atomic_overflow_observation import (
    OVERFLOW_OBSERVATION,
)


RANGE_GATED_GUIDE_SCHEMA_VERSION = "range-gated-association-guide-v1"
RANGE_GATED_GUIDE_POLICY = (
    "preserve-finite-raw-log-inside-directed-certified-range;"
    "refuse-outside-without-tolerance-or-projection"
)
RANGE_GATED_GUIDE_CERTIFICATE_SCOPE = (
    "fixed-collapsed-observation;all-successful-restricted-point-evaluations;"
    "directed-model-log-range;coarse-uniform-log-discrepancy;"
    "direct-represented-jump-edit-envelope;trusted-runtime;"
    "not-total-over-unbounded-coordinates;not-small-forward-error-analysis;"
    "not-coordinate-gradient;not-continuous-drift;not-residual;"
    "not-controlled-total-exit;not-operational-sampler-admission"
)


_CERTIFICATE_TOKEN = object()
_EVALUATION_TOKEN = object()
_EDIT_TOKEN = object()
_BRIDGE_TOKEN = object()


class AssociationGuideOperationalError(ArithmeticError):
    """Raised when a raw guide value cannot enter the operational layer."""


def _validated_digest(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError("%s must be a 64-character hexadecimal digest" % name)
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("%s must contain hexadecimal text" % name) from error
    return value


def _validated_exact_float(
    value: object,
    *,
    name: str,
    nonnegative: bool = False,
) -> float:
    if type(value) is not float:
        raise TypeError("%s must be an exact float" % name)
    if not math.isfinite(value):
        raise ValueError("%s must be finite" % name)
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError("%s must use canonical positive zero" % name)
    if nonnegative and value < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    return value


def _same_float(left: float, right: float) -> bool:
    return left.hex() == right.hex()


def _downward_float_from_decimal(value: Decimal, *, name: str) -> float:
    """Round a finite Decimal toward negative infinity in binary64."""

    if not value.is_finite():
        raise AssociationGuideOperationalError(
            "%s has no finite binary64 lower witness" % name
        )
    try:
        rounded = float(value)
    except (OverflowError, ValueError) as error:
        raise AssociationGuideOperationalError(
            "%s has no finite binary64 lower witness" % name
        ) from error
    if not math.isfinite(rounded):
        raise AssociationGuideOperationalError(
            "%s has no finite binary64 lower witness" % name
        )
    if Decimal.from_float(rounded) > value:
        rounded = math.nextafter(rounded, -math.inf)
    if not math.isfinite(rounded):
        raise AssociationGuideOperationalError("%s cannot be rounded downward" % name)
    return 0.0 if rounded == 0.0 else rounded


def _log_lower_witness(contamination_probability: float) -> float:
    epsilon = _fraction_from_float(contamination_probability)
    inverse_log_upper = _decimal_log_fraction_upper(
        Fraction(1, 1) / epsilon,
        name="inverse contamination logarithm",
    )
    return _downward_float_from_decimal(
        -inverse_log_upper,
        name="contamination log lower witness",
    )


def _validated_outcome_key(value: object) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError("outcome_key must be an exact tuple")
    if value == ("overflow",):
        return value
    if len(value) != 2 or value[0] != "retained" or type(value[1]) is not tuple:
        raise ValueError("outcome_key has an unknown representation")
    if len(value[1]) > MAX_ASSOCIATION_OCCURRENCES:
        raise AssociationObservationResourceError(
            "outcome_key exceeds the association occurrence limit"
        )
    previous = None
    aggregate_coordinates = 0
    for item in value[1]:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not int
            or type(item[1]) is not tuple
        ):
            raise TypeError("retained outcome_key contains a malformed event")
        coordinates = item[1]
        if len(coordinates) > MAX_AFFINE_OBSERVATION_DIMENSION:
            raise AssociationObservationResourceError(
                "outcome_key event exceeds the affine coordinate limit"
            )
        aggregate_coordinates += len(coordinates)
        if aggregate_coordinates > MAX_REFERENCE_DENSITY_COORDINATES:
            raise AssociationObservationResourceError(
                "outcome_key exceeds the coordinate limit"
            )
        for coordinate in coordinates:
            _validated_exact_float(
                coordinate,
                name="outcome_key coordinate",
            )
        if previous is not None and item < previous:
            raise ValueError("retained outcome_key must be canonical")
        previous = item
    return value


def _state_key(
    state: object,
    *,
    maximum_cardinality: int = MAX_CONFIGURATION_CARDINALITY,
) -> Tuple[object, ...]:
    if type(state) is not tuple:
        raise TypeError("state must be an exact tuple")
    if len(state) > maximum_cardinality:
        raise AssociationObservationResourceError(
            "state exceeds the certified cardinality"
        )
    aggregate_coordinates = 0
    keys = []
    for event in state:
        if type(event) is not TransformedEvent:
            raise TypeError("state must contain exact TransformedEvent values")
        if type(event.event_type) is not int or type(event.coordinates) is not tuple:
            raise TypeError("state event has a noncanonical representation")
        aggregate_coordinates += len(event.coordinates)
        if aggregate_coordinates > MAX_REFERENCE_DENSITY_COORDINATES:
            raise AssociationObservationResourceError(
                "state exceeds the aggregate coordinate limit"
            )
        for coordinate in event.coordinates:
            _validated_exact_float(coordinate, name="state coordinate")
        keys.append((event.event_type, event.coordinates))
    result = tuple(keys)
    if result != tuple(sorted(result)):
        raise ValueError("state must be canonical")
    return result


def _copy_outcome(outcome: PreconditionerObservation) -> PreconditionerObservation:
    if outcome is OVERFLOW_OBSERVATION:
        return OVERFLOW_OBSERVATION
    return tuple(
        TransformedEvent(event.event_type, event.coordinates) for event in outcome
    )


def _certificate_contract_key(values: dict[str, object]) -> Tuple[object, ...]:
    return (
        values["schema_version"],
        values["certificate_scope"],
        values["gate_policy"],
        values["preconditioner_parameter_key"],
        values["outcome_key"],
        values["analytic_range_certificate_sha256"],
        values["state_cap"],
        values["contamination_probability"],
        values["operational_log_lower_bound"],
        values["operational_log_upper_bound"],
        values["uniform_successful_log_error_bound"],
        values["represented_edit_log_oscillation_bound"],
    )


@dataclass(frozen=True, eq=False, init=False)
class RangeGatedGuideForwardErrorCertificate:
    """Coarse successful-evaluation discrepancy and jump-edit certificate."""

    schema_version: str
    certificate_scope: str
    gate_policy: str
    preconditioner_parameter_key: Tuple[object, ...]
    outcome_key: Tuple[object, ...]
    analytic_range_certificate_sha256: str
    state_cap: int
    contamination_probability: float
    operational_log_lower_bound: float
    operational_log_upper_bound: float
    uniform_successful_log_error_bound: float
    represented_edit_log_oscillation_bound: float
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("RangeGatedGuideForwardErrorCertificate cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("range-gated guide certificates are not pickleable")

    def __init__(
        self,
        *,
        _construction_token: object = None,
        **raw_values: object,
    ) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError(
                "range-gated guide certificates can only be created by "
                "the operational bridge"
            )
        names = (
            "schema_version",
            "certificate_scope",
            "gate_policy",
            "preconditioner_parameter_key",
            "outcome_key",
            "analytic_range_certificate_sha256",
            "state_cap",
            "contamination_probability",
            "operational_log_lower_bound",
            "operational_log_upper_bound",
            "uniform_successful_log_error_bound",
            "represented_edit_log_oscillation_bound",
            "certificate_sha256",
        )
        if set(raw_values) != set(names):
            raise TypeError("range-gated certificate fields do not match the schema")
        values = dict(raw_values)
        if values["schema_version"] != RANGE_GATED_GUIDE_SCHEMA_VERSION:
            raise ValueError("unknown range-gated guide schema")
        if values["certificate_scope"] != RANGE_GATED_GUIDE_CERTIFICATE_SCOPE:
            raise ValueError("unknown range-gated guide scope")
        if values["gate_policy"] != RANGE_GATED_GUIDE_POLICY:
            raise ValueError("unknown range-gated guide policy")
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        values["outcome_key"] = _validated_outcome_key(values["outcome_key"])
        values["analytic_range_certificate_sha256"] = _validated_digest(
            values["analytic_range_certificate_sha256"],
            name="analytic_range_certificate_sha256",
        )
        if (
            type(values["state_cap"]) is not int
            or isinstance(values["state_cap"], bool)
            or not 0 <= values["state_cap"] <= MAX_CONFIGURATION_CARDINALITY
        ):
            raise ValueError("state_cap is outside the implementation limit")
        for name, nonnegative in (
            ("contamination_probability", False),
            ("operational_log_lower_bound", False),
            ("operational_log_upper_bound", False),
            ("uniform_successful_log_error_bound", True),
            ("represented_edit_log_oscillation_bound", True),
        ):
            values[name] = _validated_exact_float(
                values[name],
                name=name,
                nonnegative=nonnegative,
            )
        epsilon = values["contamination_probability"]
        if not 0.0 < epsilon < 1.0:
            raise ValueError("contamination_probability must lie in (0, 1)")
        lower = values["operational_log_lower_bound"]
        upper = values["operational_log_upper_bound"]
        if lower > upper:
            raise ValueError("operational guide interval is empty")
        exact_width = _fraction_from_float(upper) - _fraction_from_float(lower)
        for name in (
            "uniform_successful_log_error_bound",
            "represented_edit_log_oscillation_bound",
        ):
            if _fraction_from_float(values[name]) < exact_width:
                raise ValueError("%s lies below the represented interval width" % name)
        values["certificate_sha256"] = _validated_digest(
            values["certificate_sha256"],
            name="certificate_sha256",
        )
        expected = _plain_key_sha256(
            _certificate_contract_key(values),
            domain=b"heterodiff-range-gated-guide-certificate-v1\x00",
        )
        if values["certificate_sha256"] != expected:
            raise ValueError("certificate_sha256 does not match certificate fields")
        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def operational_jump_guide_admissible(self) -> bool:
        return True

    @property
    def successful_evaluation_only(self) -> bool:
        return True

    @property
    def unprojected_value_preserved(self) -> bool:
        return True

    @property
    def small_forward_error_analysis(self) -> bool:
        return False

    @property
    def operational_coordinate_derivatives_admissible(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "range-gated-guide-forward-error-certificate-v1",
            self.preconditioner_parameter_key,
            self.outcome_key,
            self.analytic_range_certificate_sha256,
            self.certificate_sha256,
        )


def _evaluation_contract_key(values: dict[str, object]) -> Tuple[object, ...]:
    return (
        values["preconditioner_parameter_key"],
        values["bridge_certificate_sha256"],
        values["analytic_range_certificate_sha256"],
        values["outcome_key"],
        values["reverse_time"],
        tuple(event.model_key() for event in values["state"]),
        values["raw_log_density"],
        values["operational_log_density"],
        values["operational_log_lower_bound"],
        values["operational_log_upper_bound"],
        values["uniform_log_error_bound"],
        values["represented_edit_log_oscillation_bound"],
        values["algorithm"],
        values["gate_policy"],
    )


@dataclass(frozen=True, eq=False, init=False)
class RangeGatedGuideEvaluation:
    """One exact raw point value admitted by the directed range gate."""

    preconditioner_parameter_key: Tuple[object, ...]
    bridge_certificate_sha256: str
    analytic_range_certificate_sha256: str
    outcome_key: Tuple[object, ...]
    reverse_time: float
    state: TransformedConfiguration
    raw_log_density: float
    operational_log_density: float
    operational_log_lower_bound: float
    operational_log_upper_bound: float
    uniform_log_error_bound: float
    represented_edit_log_oscillation_bound: float
    algorithm: str
    gate_policy: str
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("RangeGatedGuideEvaluation cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("range-gated guide evaluations are not pickleable")

    def __init__(
        self,
        *,
        _construction_token: object = None,
        **raw_values: object,
    ) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError(
                "range-gated guide evaluations can only be created by "
                "the operational bridge"
            )
        names = (
            "preconditioner_parameter_key",
            "bridge_certificate_sha256",
            "analytic_range_certificate_sha256",
            "outcome_key",
            "reverse_time",
            "state",
            "raw_log_density",
            "operational_log_density",
            "operational_log_lower_bound",
            "operational_log_upper_bound",
            "uniform_log_error_bound",
            "represented_edit_log_oscillation_bound",
            "algorithm",
            "gate_policy",
            "evaluation_sha256",
        )
        if set(raw_values) != set(names):
            raise TypeError("range-gated evaluation fields do not match the schema")
        values = dict(raw_values)
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        for name in (
            "bridge_certificate_sha256",
            "analytic_range_certificate_sha256",
            "evaluation_sha256",
        ):
            values[name] = _validated_digest(values[name], name=name)
        values["outcome_key"] = _validated_outcome_key(values["outcome_key"])
        _state_key(values["state"])
        for name, nonnegative in (
            ("reverse_time", True),
            ("raw_log_density", False),
            ("operational_log_density", False),
            ("operational_log_lower_bound", False),
            ("operational_log_upper_bound", False),
            ("uniform_log_error_bound", True),
            ("represented_edit_log_oscillation_bound", True),
        ):
            values[name] = _validated_exact_float(
                values[name],
                name=name,
                nonnegative=nonnegative,
            )
        if values["gate_policy"] != RANGE_GATED_GUIDE_POLICY:
            raise ValueError("range-gated evaluation has an unknown policy")
        if type(values["algorithm"]) is not str or not values["algorithm"]:
            raise TypeError("algorithm must be nonempty exact text")
        if not _same_float(
            values["raw_log_density"],
            values["operational_log_density"],
        ):
            raise ValueError("the range gate must preserve the raw log value")
        if not (
            values["operational_log_lower_bound"]
            <= values["raw_log_density"]
            <= values["operational_log_upper_bound"]
        ):
            raise ValueError("raw log guide lies outside the operational range")
        exact_width = _fraction_from_float(
            values["operational_log_upper_bound"]
        ) - _fraction_from_float(values["operational_log_lower_bound"])
        for name in (
            "uniform_log_error_bound",
            "represented_edit_log_oscillation_bound",
        ):
            if _fraction_from_float(values[name]) < exact_width:
                raise ValueError("%s lies below the represented interval width" % name)
        expected = _plain_key_sha256(
            _evaluation_contract_key(values),
            domain=b"heterodiff-range-gated-guide-evaluation-v1\x00",
        )
        if values["evaluation_sha256"] != expected:
            raise ValueError("evaluation_sha256 does not match evaluation fields")
        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def range_gate_passed(self) -> bool:
        return True

    @property
    def operational_jump_guide_admissible(self) -> bool:
        return True

    @property
    def operational_coordinate_derivatives_admissible(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "range-gated-guide-evaluation-v1",
            self.bridge_certificate_sha256,
            self.evaluation_sha256,
        )


def _edit_contract_key(values: dict[str, object]) -> Tuple[object, ...]:
    return (
        values["preconditioner_parameter_key"],
        values["bridge_certificate_sha256"],
        values["analytic_range_certificate_sha256"],
        values["outcome_key"],
        values["reverse_time"],
        values["edit_kind"],
        tuple(event.model_key() for event in values["source_state"]),
        tuple(event.model_key() for event in values["destination_state"]),
        values["source_evaluation_sha256"],
        values["destination_evaluation_sha256"],
        values["source_log_density"],
        values["destination_log_density"],
        values["log_ratio"],
        values["represented_edit_log_oscillation_bound"],
    )


@dataclass(frozen=True, eq=False, init=False)
class RangeGatedGuideEditRatio:
    """One represented legal edit assembled from two range-gated values."""

    preconditioner_parameter_key: Tuple[object, ...]
    bridge_certificate_sha256: str
    analytic_range_certificate_sha256: str
    outcome_key: Tuple[object, ...]
    reverse_time: float
    edit_kind: str
    source_state: TransformedConfiguration
    destination_state: TransformedConfiguration
    source_evaluation_sha256: str
    destination_evaluation_sha256: str
    source_log_density: float
    destination_log_density: float
    log_ratio: float
    represented_edit_log_oscillation_bound: float
    edit_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("RangeGatedGuideEditRatio cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("range-gated guide edits are not pickleable")

    def __init__(
        self,
        *,
        _construction_token: object = None,
        **raw_values: object,
    ) -> None:
        if _construction_token is not _EDIT_TOKEN:
            raise TypeError(
                "range-gated guide edits can only be created by "
                "the operational bridge"
            )
        names = (
            "preconditioner_parameter_key",
            "bridge_certificate_sha256",
            "analytic_range_certificate_sha256",
            "outcome_key",
            "reverse_time",
            "edit_kind",
            "source_state",
            "destination_state",
            "source_evaluation_sha256",
            "destination_evaluation_sha256",
            "source_log_density",
            "destination_log_density",
            "log_ratio",
            "represented_edit_log_oscillation_bound",
            "edit_sha256",
        )
        if set(raw_values) != set(names):
            raise TypeError("range-gated edit fields do not match the schema")
        values = dict(raw_values)
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        for name in (
            "bridge_certificate_sha256",
            "analytic_range_certificate_sha256",
            "source_evaluation_sha256",
            "destination_evaluation_sha256",
            "edit_sha256",
        ):
            values[name] = _validated_digest(values[name], name=name)
        values["outcome_key"] = _validated_outcome_key(values["outcome_key"])
        _state_key(values["source_state"])
        _state_key(values["destination_state"])
        for name, nonnegative in (
            ("reverse_time", True),
            ("source_log_density", False),
            ("destination_log_density", False),
            ("log_ratio", False),
            ("represented_edit_log_oscillation_bound", True),
        ):
            values[name] = _validated_exact_float(
                values[name],
                name=name,
                nonnegative=nonnegative,
            )
        if values["edit_kind"] not in ("birth", "death", "replacement"):
            raise ValueError("unknown edit kind")
        expected_ratio = (
            values["destination_log_density"] - values["source_log_density"]
        )
        if not _same_float(values["log_ratio"], expected_ratio):
            raise ValueError("log_ratio does not match its endpoint values")
        if abs(values["log_ratio"]) > values["represented_edit_log_oscillation_bound"]:
            raise ValueError("range-gated edit exceeds its certified envelope")
        expected = _plain_key_sha256(
            _edit_contract_key(values),
            domain=b"heterodiff-range-gated-guide-edit-v1\x00",
        )
        if values["edit_sha256"] != expected:
            raise ValueError("edit_sha256 does not match edit fields")
        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def operational_jump_guide_admissible(self) -> bool:
        return True

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "range-gated-guide-edit-v1",
            self.bridge_certificate_sha256,
            self.edit_sha256,
        )


def _make_certificate(
    preconditioner: AnalyticAssociationPreconditioner,
    range_certificate: AnalyticGuideRangeCertificate,
) -> RangeGatedGuideForwardErrorCertificate:
    lower = _log_lower_witness(range_certificate.contamination_probability)
    upper = range_certificate.guide_log_upper_bound
    width = _outward_sum_upper(
        (upper, -lower),
        name="range-gated guide log width",
    )
    values: dict[str, object] = {
        "schema_version": RANGE_GATED_GUIDE_SCHEMA_VERSION,
        "certificate_scope": RANGE_GATED_GUIDE_CERTIFICATE_SCOPE,
        "gate_policy": RANGE_GATED_GUIDE_POLICY,
        "preconditioner_parameter_key": preconditioner.parameter_key(),
        "outcome_key": range_certificate.outcome_key,
        "analytic_range_certificate_sha256": (range_certificate.certificate_sha256),
        "state_cap": range_certificate.state_cap,
        "contamination_probability": (range_certificate.contamination_probability),
        "operational_log_lower_bound": lower,
        "operational_log_upper_bound": upper,
        "uniform_successful_log_error_bound": width,
        "represented_edit_log_oscillation_bound": width,
    }
    digest = _plain_key_sha256(
        _certificate_contract_key(values),
        domain=b"heterodiff-range-gated-guide-certificate-v1\x00",
    )
    return RangeGatedGuideForwardErrorCertificate(
        **values,
        certificate_sha256=digest,
        _construction_token=_CERTIFICATE_TOKEN,
    )


class RangeGatedAssociationGuide:
    """Immutable evaluator bound to one model, outcome, and range certificate."""

    __slots__ = ("_preconditioner", "_outcome", "_certificate")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("RangeGatedAssociationGuide cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("range-gated association guides are not pickleable")

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("RangeGatedAssociationGuide is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("RangeGatedAssociationGuide is immutable")

    def __init__(
        self,
        preconditioner: AnalyticAssociationPreconditioner,
        outcome: PreconditionerObservation,
        certificate: RangeGatedGuideForwardErrorCertificate,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _BRIDGE_TOKEN:
            raise TypeError(
                "range-gated association guides can only be created by "
                "the certification factory"
            )
        if type(preconditioner) is not AnalyticAssociationPreconditioner:
            raise TypeError(
                "preconditioner must be an exact AnalyticAssociationPreconditioner"
            )
        if type(certificate) is not RangeGatedGuideForwardErrorCertificate:
            raise TypeError("certificate has the wrong type")
        checked_outcome = _copy_outcome(outcome)
        if (
            preconditioner._guide_outcome_key(checked_outcome)
            != certificate.outcome_key
        ):
            raise ValueError("bridge outcome does not match its certificate")
        object.__setattr__(self, "_preconditioner", preconditioner)
        object.__setattr__(self, "_outcome", checked_outcome)
        object.__setattr__(self, "_certificate", certificate)

    @property
    def preconditioner(self) -> AnalyticAssociationPreconditioner:
        return self._preconditioner

    @property
    def outcome(self) -> PreconditionerObservation:
        return self._outcome

    @property
    def certificate(self) -> RangeGatedGuideForwardErrorCertificate:
        return self._certificate

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "range-gated-association-guide-v1",
            self.certificate.parameter_key(),
        )

    def _require_live_binding(self) -> None:
        RangeGatedGuideForwardErrorCertificate(
            **{name: getattr(self.certificate, name) for name in _certificate_fields()},
            _construction_token=_CERTIFICATE_TOKEN,
        )
        live_key = self.preconditioner._require_live_guide_certificate_binding()
        live_digest = _plain_key_sha256(
            live_key,
            domain=b"heterodiff-range-gated-live-model-v1\x00",
        )
        certified_digest = _plain_key_sha256(
            self.certificate.preconditioner_parameter_key,
            domain=b"heterodiff-range-gated-live-model-v1\x00",
        )
        if live_digest != certified_digest:
            raise ValueError(
                "live preconditioner differs from the range-gated certificate"
            )
        if (
            self.preconditioner._guide_outcome_key(self.outcome)
            != self.certificate.outcome_key
        ):
            raise ValueError("live bridge outcome differs from its certificate")

    def _validate_raw_evaluation(
        self,
        raw: object,
        *,
        expected_reverse_time: float,
        expected_state: TransformedConfiguration,
    ) -> BoundPreconditionerEvaluation:
        if type(raw) is not BoundPreconditionerEvaluation:
            raise TypeError("raw evaluator returned the wrong record type")
        if raw.restricted is not True:
            raise ValueError("operational guide requires a restricted evaluation")
        if type(raw.reverse_time) is not float or not _same_float(
            raw.reverse_time,
            expected_reverse_time,
        ):
            raise ValueError("raw evaluator returned a different reverse time")
        if _state_key(
            raw.state,
            maximum_cardinality=self.certificate.state_cap,
        ) != _state_key(
            expected_state,
            maximum_cardinality=self.certificate.state_cap,
        ):
            raise ValueError("raw evaluator returned a different state")
        if (
            self.preconditioner._guide_outcome_key(raw.outcome)
            != self.certificate.outcome_key
        ):
            raise ValueError("raw evaluator returned a different outcome")
        raw_model_digest = _plain_key_sha256(
            raw.preconditioner_parameter_key,
            domain=b"heterodiff-range-gated-raw-model-v1\x00",
        )
        expected_model_digest = _plain_key_sha256(
            self.certificate.preconditioner_parameter_key,
            domain=b"heterodiff-range-gated-raw-model-v1\x00",
        )
        if raw_model_digest != expected_model_digest:
            raise ValueError("raw evaluator returned a foreign model binding")
        raw_log = raw.log_density
        if type(raw_log) is not float or not math.isfinite(raw_log):
            raise AssociationGuideOperationalError(
                "raw log guide must be an exact finite float"
            )
        if raw_log == 0.0 and math.copysign(1.0, raw_log) < 0.0:
            raise AssociationGuideOperationalError(
                "raw log guide must use canonical positive zero"
            )
        lower = self.certificate.operational_log_lower_bound
        upper = self.certificate.operational_log_upper_bound
        if raw_log < lower or raw_log > upper:
            raise AssociationGuideOperationalError(
                "raw log guide lies outside the directed certified range"
            )
        return raw

    def evaluate(
        self,
        reverse_time: object,
        state: object,
    ) -> RangeGatedGuideEvaluation:
        """Evaluate one restricted state and admit only an in-range raw value."""

        self._require_live_binding()
        expected_reverse_time = self.preconditioner._reverse_time(reverse_time)
        if expected_reverse_time == 0.0:
            expected_reverse_time = 0.0
        expected_state = self.preconditioner._canonical_restricted(state)
        raw = self._validate_raw_evaluation(
            self.preconditioner.evaluate(
                expected_reverse_time,
                expected_state,
                self.outcome,
            ),
            expected_reverse_time=expected_reverse_time,
            expected_state=expected_state,
        )
        values: dict[str, object] = {
            "preconditioner_parameter_key": (
                self.certificate.preconditioner_parameter_key
            ),
            "bridge_certificate_sha256": self.certificate.certificate_sha256,
            "analytic_range_certificate_sha256": (
                self.certificate.analytic_range_certificate_sha256
            ),
            "outcome_key": self.certificate.outcome_key,
            "reverse_time": raw.reverse_time,
            "state": raw.state,
            "raw_log_density": raw.log_density,
            "operational_log_density": raw.log_density,
            "operational_log_lower_bound": (
                self.certificate.operational_log_lower_bound
            ),
            "operational_log_upper_bound": (
                self.certificate.operational_log_upper_bound
            ),
            "uniform_log_error_bound": (
                self.certificate.uniform_successful_log_error_bound
            ),
            "represented_edit_log_oscillation_bound": (
                self.certificate.represented_edit_log_oscillation_bound
            ),
            "algorithm": raw.association_evaluation.algorithm,
            "gate_policy": self.certificate.gate_policy,
        }
        digest = _plain_key_sha256(
            _evaluation_contract_key(values),
            domain=b"heterodiff-range-gated-guide-evaluation-v1\x00",
        )
        return RangeGatedGuideEvaluation(
            **values,
            evaluation_sha256=digest,
            _construction_token=_EVALUATION_TOKEN,
        )

    def validate_evaluation(
        self,
        evaluation: object,
    ) -> RangeGatedGuideEvaluation:
        """Reconstruct, recompute, and require one exact point record."""

        if type(evaluation) is not RangeGatedGuideEvaluation:
            raise TypeError("evaluation must be an exact RangeGatedGuideEvaluation")
        names = (
            "preconditioner_parameter_key",
            "bridge_certificate_sha256",
            "analytic_range_certificate_sha256",
            "outcome_key",
            "reverse_time",
            "state",
            "raw_log_density",
            "operational_log_density",
            "operational_log_lower_bound",
            "operational_log_upper_bound",
            "uniform_log_error_bound",
            "represented_edit_log_oscillation_bound",
            "algorithm",
            "gate_policy",
            "evaluation_sha256",
        )
        RangeGatedGuideEvaluation(
            **{name: getattr(evaluation, name) for name in names},
            _construction_token=_EVALUATION_TOKEN,
        )
        if len(evaluation.state) > self.certificate.state_cap:
            raise AssociationObservationResourceError(
                "evaluation state exceeds the certified cap"
            )
        expected = self.evaluate(evaluation.reverse_time, evaluation.state)
        for name in names:
            supplied = getattr(evaluation, name)
            recomputed = getattr(expected, name)
            if type(supplied) is float and type(recomputed) is float:
                matches = _same_float(supplied, recomputed)
            else:
                matches = supplied == recomputed
            if not matches:
                raise ValueError(
                    "range-gated evaluation field %s differs from recomputation" % name
                )
        return evaluation

    def edit_log_ratio(
        self,
        reverse_time: object,
        source_state: object,
        destination_state: object,
    ) -> RangeGatedGuideEditRatio:
        """Build one legal represented edit from two successful point values."""

        self._require_live_binding()
        expected_reverse_time = self.preconditioner._reverse_time(reverse_time)
        if expected_reverse_time == 0.0:
            expected_reverse_time = 0.0
        expected_source = self.preconditioner._canonical_restricted(source_state)
        expected_destination = self.preconditioner._canonical_restricted(
            destination_state
        )
        expected_edit_kind = self.preconditioner._classify_edit(
            expected_source,
            expected_destination,
        )
        raw_edit = self.preconditioner.edit_log_ratio(
            expected_reverse_time,
            expected_source,
            expected_destination,
            self.outcome,
        )
        if type(raw_edit) is not BoundPreconditionerEditRatio:
            raise TypeError("raw edit evaluator returned the wrong record type")
        if raw_edit.edit_kind != expected_edit_kind:
            raise ValueError("raw edit evaluator returned a different edit kind")
        if type(raw_edit.reverse_time) is not float or not _same_float(
            raw_edit.reverse_time,
            expected_reverse_time,
        ):
            raise ValueError("raw edit evaluator returned a different reverse time")
        raw_model_digest = _plain_key_sha256(
            raw_edit.preconditioner_parameter_key,
            domain=b"heterodiff-range-gated-raw-edit-model-v1\x00",
        )
        expected_model_digest = _plain_key_sha256(
            self.certificate.preconditioner_parameter_key,
            domain=b"heterodiff-range-gated-raw-edit-model-v1\x00",
        )
        if raw_model_digest != expected_model_digest:
            raise ValueError("raw edit evaluator returned a foreign model binding")
        if (
            self.preconditioner._guide_outcome_key(raw_edit.outcome)
            != self.certificate.outcome_key
        ):
            raise ValueError("raw edit evaluator returned a different outcome")
        if _state_key(
            raw_edit.source_state,
            maximum_cardinality=self.certificate.state_cap,
        ) != _state_key(
            expected_source,
            maximum_cardinality=self.certificate.state_cap,
        ) or _state_key(
            raw_edit.destination_state,
            maximum_cardinality=self.certificate.state_cap,
        ) != _state_key(
            expected_destination,
            maximum_cardinality=self.certificate.state_cap,
        ):
            raise ValueError("raw edit evaluator returned different endpoint states")
        source = self.evaluate(expected_reverse_time, expected_source)
        destination = self.evaluate(
            expected_reverse_time,
            expected_destination,
        )
        if source.outcome_key != destination.outcome_key:
            raise ValueError("range-gated edit endpoints have different outcomes")
        if _state_key(raw_edit.source_state) != _state_key(source.state) or _state_key(
            raw_edit.destination_state
        ) != _state_key(destination.state):
            raise ValueError("raw edit binding differs from its endpoint records")
        log_ratio = destination.operational_log_density - source.operational_log_density
        if not _same_float(log_ratio, raw_edit.log_ratio):
            raise AssociationGuideOperationalError(
                "raw edit ratio is inconsistent with point evaluations"
            )
        bound = self.certificate.represented_edit_log_oscillation_bound
        if abs(log_ratio) > bound:
            raise AssociationGuideOperationalError(
                "represented edit exceeds the certified guide envelope"
            )
        values: dict[str, object] = {
            "preconditioner_parameter_key": (
                self.certificate.preconditioner_parameter_key
            ),
            "bridge_certificate_sha256": self.certificate.certificate_sha256,
            "analytic_range_certificate_sha256": (
                self.certificate.analytic_range_certificate_sha256
            ),
            "outcome_key": self.certificate.outcome_key,
            "reverse_time": source.reverse_time,
            "edit_kind": raw_edit.edit_kind,
            "source_state": source.state,
            "destination_state": destination.state,
            "source_evaluation_sha256": source.evaluation_sha256,
            "destination_evaluation_sha256": destination.evaluation_sha256,
            "source_log_density": source.operational_log_density,
            "destination_log_density": destination.operational_log_density,
            "log_ratio": log_ratio,
            "represented_edit_log_oscillation_bound": bound,
        }
        digest = _plain_key_sha256(
            _edit_contract_key(values),
            domain=b"heterodiff-range-gated-guide-edit-v1\x00",
        )
        return RangeGatedGuideEditRatio(
            **values,
            edit_sha256=digest,
            _construction_token=_EDIT_TOKEN,
        )

    def validate_edit_log_ratio(
        self,
        edit: object,
    ) -> RangeGatedGuideEditRatio:
        """Reconstruct, recompute, and require one exact represented edit."""

        if type(edit) is not RangeGatedGuideEditRatio:
            raise TypeError("edit must be an exact RangeGatedGuideEditRatio")
        names = (
            "preconditioner_parameter_key",
            "bridge_certificate_sha256",
            "analytic_range_certificate_sha256",
            "outcome_key",
            "reverse_time",
            "edit_kind",
            "source_state",
            "destination_state",
            "source_evaluation_sha256",
            "destination_evaluation_sha256",
            "source_log_density",
            "destination_log_density",
            "log_ratio",
            "represented_edit_log_oscillation_bound",
            "edit_sha256",
        )
        RangeGatedGuideEditRatio(
            **{name: getattr(edit, name) for name in names},
            _construction_token=_EDIT_TOKEN,
        )
        expected = self.edit_log_ratio(
            edit.reverse_time,
            edit.source_state,
            edit.destination_state,
        )
        for name in names:
            supplied = getattr(edit, name)
            recomputed = getattr(expected, name)
            if type(supplied) is float and type(recomputed) is float:
                matches = _same_float(supplied, recomputed)
            else:
                matches = supplied == recomputed
            if not matches:
                raise ValueError(
                    "range-gated edit field %s differs from recomputation" % name
                )
        return edit


def _certificate_fields() -> Tuple[str, ...]:
    return (
        "schema_version",
        "certificate_scope",
        "gate_policy",
        "preconditioner_parameter_key",
        "outcome_key",
        "analytic_range_certificate_sha256",
        "state_cap",
        "contamination_probability",
        "operational_log_lower_bound",
        "operational_log_upper_bound",
        "uniform_successful_log_error_bound",
        "represented_edit_log_oscillation_bound",
        "certificate_sha256",
    )


def certify_range_gated_association_guide(
    preconditioner: AnalyticAssociationPreconditioner,
    range_certificate: AnalyticGuideRangeCertificate,
    observation: Optional[object] = None,
) -> RangeGatedAssociationGuide:
    """Create a fixed-outcome, successful-evaluation range gate."""

    if type(preconditioner) is not AnalyticAssociationPreconditioner:
        raise TypeError(
            "preconditioner must be an exact AnalyticAssociationPreconditioner"
        )
    checked = preconditioner.validate_guide_range_certificate(
        range_certificate,
        observation=observation,
    )
    certificate = _make_certificate(preconditioner, checked)
    bridge = RangeGatedAssociationGuide(
        preconditioner,
        checked.outcome,
        certificate,
        _construction_token=_BRIDGE_TOKEN,
    )
    bridge._require_live_binding()
    return bridge


def require_matching_range_gated_association_guide(
    preconditioner: AnalyticAssociationPreconditioner,
    bridge: RangeGatedAssociationGuide,
    range_certificate: AnalyticGuideRangeCertificate,
    observation: Optional[object] = None,
) -> RangeGatedAssociationGuide:
    """Refuse unless live model, analytic certificate, and bridge all match."""

    if type(preconditioner) is not AnalyticAssociationPreconditioner:
        raise TypeError(
            "preconditioner must be an exact AnalyticAssociationPreconditioner"
        )
    if type(bridge) is not RangeGatedAssociationGuide:
        raise TypeError("bridge must be an exact RangeGatedAssociationGuide")
    if bridge.preconditioner is not preconditioner:
        raise ValueError("bridge is bound to a different preconditioner object")
    checked = preconditioner.validate_guide_range_certificate(
        range_certificate,
        observation=observation,
    )
    if type(bridge.certificate) is not RangeGatedGuideForwardErrorCertificate:
        raise TypeError("bridge certificate has the wrong type")
    RangeGatedGuideForwardErrorCertificate(
        **{name: getattr(bridge.certificate, name) for name in _certificate_fields()},
        _construction_token=_CERTIFICATE_TOKEN,
    )
    expected = _make_certificate(preconditioner, checked)
    for name in _certificate_fields():
        supplied = getattr(bridge.certificate, name)
        recomputed = getattr(expected, name)
        if type(supplied) is float and type(recomputed) is float:
            matches = _same_float(supplied, recomputed)
        else:
            matches = supplied == recomputed
        if not matches:
            raise ValueError(
                "range-gated certificate field %s differs from recomputation" % name
            )
    if preconditioner._guide_outcome_key(bridge.outcome) != checked.outcome_key:
        raise ValueError("bridge outcome differs from the analytic certificate")
    bridge._require_live_binding()
    return bridge


def validate_range_gated_guide_certificate(
    preconditioner: AnalyticAssociationPreconditioner,
    bridge: RangeGatedAssociationGuide,
    range_certificate: AnalyticGuideRangeCertificate,
    observation: Optional[object] = None,
) -> RangeGatedGuideForwardErrorCertificate:
    """Return the recomputation-validated range-gated certificate."""

    return require_matching_range_gated_association_guide(
        preconditioner,
        bridge,
        range_certificate,
        observation=observation,
    ).certificate


__all__ = [
    "AssociationGuideOperationalError",
    "RANGE_GATED_GUIDE_CERTIFICATE_SCOPE",
    "RANGE_GATED_GUIDE_POLICY",
    "RANGE_GATED_GUIDE_SCHEMA_VERSION",
    "RangeGatedAssociationGuide",
    "RangeGatedGuideEditRatio",
    "RangeGatedGuideEvaluation",
    "RangeGatedGuideForwardErrorCertificate",
    "certify_range_gated_association_guide",
    "require_matching_range_gated_association_guide",
    "validate_range_gated_guide_certificate",
]
