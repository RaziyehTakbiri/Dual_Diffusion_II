"""Process-owned reference proposals for the future plug-in bridge sampler.

This module implements only early sampler dependencies: a deterministic
no-RNG query of the state-dependent reference candidate intensity, and one
draw from the normalized reference jump kernel with a complete labelled-route
disintegration.  It does not simulate a reverse path, apply an association
guide, initialize a conditional law, or claim that a sampled tilted integrand
is a learned total exit rate.

The public composer accepts reverse/generative time ``u`` and derives direct
noising time ``s = S - u`` internally.  Callers cannot supply a reference
rate.  The optional configuration-energy projection imports PyTorch lazily so
that importing this process module keeps the base package model-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from numbers import Real
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np

from heterodiff.processes.reversible_hybrid_reference import (
    HybridJumpKind,
    HybridJumpRates,
    HybridReferenceJumpProposal,
    ReversibleHybridReference,
)
from heterodiff.theory.configuration_reference import (
    MIN_REFERENCE_CATEGORICAL_PROBABILITY,
    TransformedConfiguration,
    TransformedEvent,
)


PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCHEMA = "plugin-bridge-reference-proposal-v1"
PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCOPE = (
    "process-owned-normalized-reference-candidate;"
    "labelled-occurrence-disintegration;certified-base-energy-projection;"
    "not-learned-total-exit-rate;not-guide-admission;not-path-sampler"
)
PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCHEMA = "plugin-bridge-reference-intensity-v1"
PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCOPE = (
    "process-owned-no-rng-reference-intensity;canonical-state;"
    "reverse-to-direct-time;categorical-route-preflight;"
    "not-controlled-total-exit;not-waiting-time-draw;not-path-sampler"
)

_MIN_NORMAL_FLOAT64 = float(np.finfo(np.float64).tiny)
_LOG_MIN_NORMAL_FLOAT64 = math.log(_MIN_NORMAL_FLOAT64)
_LOG_TWO_PI = math.log(2.0 * math.pi)
_CATEGORICAL_ACCUMULATION_FACTOR = 32.0
_CATEGORICAL_INCREMENT_RTOL = 0.125
_MAX_CONTEXT_DIMENSION = 4_096
_MAX_PLUGIN_KEY_NODES = 1_000_000
_MAX_PLUGIN_KEY_DEPTH = 32

_FACTORIZATION_TOKEN = object()
_CANDIDATE_TOKEN = object()
_INTENSITY_TOKEN = object()
_ENERGY_EVALUATION_TOKEN = object()


class UnsupportedPluginBridgeSamplingError(ValueError):
    """Raised when the frozen reference proposal is not RNG-representable."""


def _validated_real(
    value: object,
    *,
    name: str,
    strictly_positive: bool = False,
    nonnegative: bool = False,
) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if strictly_positive:
        if result <= 0.0:
            raise ValueError("%s must be strictly positive" % name)
        if result < _MIN_NORMAL_FLOAT64:
            raise ArithmeticError("%s must be a normal float64 value" % name)
    elif nonnegative:
        if result < 0.0:
            raise ValueError("%s must be nonnegative" % name)
        if 0.0 < result < _MIN_NORMAL_FLOAT64:
            raise ArithmeticError("%s must be zero or a normal float64 value" % name)
    return result


def _checked_positive_product(left: float, right: float, *, name: str) -> float:
    result = left * right
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    if result <= 0.0 or result < _MIN_NORMAL_FLOAT64:
        raise ArithmeticError("positive %s is not a normal float64 value" % name)
    return result


def _validated_rng(rng: object) -> np.random.Generator:
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    return rng


def _validate_categorical_weights(weights: Sequence[float], *, context: str) -> None:
    """Mirror the reference process's no-clipping finite-RNG gate."""

    if not weights:
        raise ArithmeticError("%s categorical law has no positive categories" % context)
    try:
        total = math.fsum(weights)
    except OverflowError as error:
        raise ArithmeticError("%s categorical total overflowed" % context) from error
    if not math.isfinite(total) or total <= 0.0:
        raise ArithmeticError(
            "%s categorical total is not positive and finite" % context
        )
    probabilities = np.asarray(
        [float(weight) / total for weight in weights], dtype=np.float64
    )
    if np.any(~np.isfinite(probabilities)):
        raise ArithmeticError("%s categorical probabilities are invalid" % context)
    if np.any(probabilities <= 0.0):
        raise UnsupportedPluginBridgeSamplingError(
            "%s law has a positive category below float64 normalization range" % context
        )
    floor = max(
        MIN_REFERENCE_CATEGORICAL_PROBABILITY,
        _CATEGORICAL_ACCUMULATION_FACTOR
        * len(weights)
        * float(np.finfo(np.float64).eps),
    )
    if float(np.min(probabilities)) < floor:
        raise UnsupportedPluginBridgeSamplingError(
            "%s law has a positive category below the finite-RNG sampling "
            "resolution" % context
        )
    cdf = np.cumsum(probabilities, dtype=np.float64)
    if np.any(~np.isfinite(cdf)):
        raise UnsupportedPluginBridgeSamplingError(
            "%s categorical CDF is not representable" % context
        )
    cdf[-1] = 1.0
    increments = np.diff(np.concatenate((np.zeros(1), cdf)))
    if np.any(increments <= 0.0) or np.any(
        np.abs(increments - probabilities) / probabilities > _CATEGORICAL_INCREMENT_RTOL
    ):
        raise UnsupportedPluginBridgeSamplingError(
            "%s categorical CDF is below the finite-RNG resolution" % context
        )


def _standard_gaussian_log_density(event: TransformedEvent) -> float:
    try:
        squared_norm = math.fsum(
            coordinate * coordinate for coordinate in event.coordinates
        )
    except OverflowError as error:
        raise ArithmeticError(
            "destination squared norm is not representable"
        ) from error
    if not math.isfinite(squared_norm):
        raise ArithmeticError("destination squared norm is not representable")
    result = -0.5 * (len(event.coordinates) * _LOG_TWO_PI + squared_norm)
    if not math.isfinite(result):
        raise ArithmeticError("destination Gaussian log density is not finite")
    return result


def _materialize_normal_positive_density(log_density: float) -> float:
    if log_density < _LOG_MIN_NORMAL_FLOAT64:
        raise ArithmeticError(
            "destination density cannot be materialized as a normal float64; "
            "use the retained log density"
        )
    result = math.exp(log_density)
    if not math.isfinite(result) or result <= 0.0 or result < _MIN_NORMAL_FLOAT64:
        raise ArithmeticError(
            "destination density is not a normal positive float64 value"
        )
    return result


def _reverse_to_direct_time(
    process: ReversibleHybridReference, reverse_time: object
) -> Tuple[float, float]:
    reverse = _validated_real(reverse_time, name="reverse_time", nonnegative=True)
    horizon = process.schedule.horizon
    if reverse > horizon:
        raise ValueError("reverse_time must lie within [0, horizon]")
    direct = horizon - reverse
    if not math.isfinite(direct) or direct < 0.0 or direct > horizon:
        raise ArithmeticError("derived direct time is outside the process horizon")
    if 0.0 < reverse < horizon and (direct == 0.0 or direct == horizon):
        raise ArithmeticError(
            "interior reverse_time is not distinguishable at direct-time precision"
        )
    if any(
        direct == float(breakpoint) for breakpoint in process.schedule.time_grid[1:-1]
    ):
        exact_direct = Fraction.from_float(horizon) - Fraction.from_float(reverse)
        if exact_direct != Fraction.from_float(direct):
            raise ArithmeticError(
                "reverse_time is not distinguishable across a direct-time "
                "schedule breakpoint"
            )
    return reverse, direct


def _same_plain_type_tree(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is tuple:
        return len(actual) == len(expected) and all(  # type: ignore[arg-type]
            _same_plain_type_tree(actual_item, expected_item)
            for actual_item, expected_item in zip(  # type: ignore[arg-type]
                actual, expected
            )
        )
    if type(expected) is float:
        return actual.hex() == expected.hex()  # type: ignore[union-attr]
    return actual == expected


def _validate_plain_key(
    value: object,
    *,
    remaining_nodes: list[int],
    depth: int = 0,
) -> None:
    if depth > _MAX_PLUGIN_KEY_DEPTH:
        raise ValueError("plugin key exceeds the nesting-depth limit")
    remaining_nodes[0] -= 1
    if remaining_nodes[0] < 0:
        raise ValueError("plugin key exceeds the node-count limit")
    if type(value) is tuple:
        for item in value:
            _validate_plain_key(
                item,
                remaining_nodes=remaining_nodes,
                depth=depth + 1,
            )
        return
    if type(value) not in (str, int, float, type(None)):
        raise TypeError("plugin keys must contain only immutable plain values")
    if type(value) is float and not math.isfinite(value):
        raise ValueError("plugin key floats must be finite")


def _require_exact_canonical_configuration(
    configuration: object,
    *,
    name: str,
) -> TransformedConfiguration:
    if type(configuration) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    for event in configuration:
        if type(event) is not TransformedEvent:
            raise TypeError("%s requires exact TransformedEvent values" % name)
        if type(event.event_type) is not int:
            raise TypeError("%s event types must be exact integers" % name)
        if type(event.coordinates) is not tuple:
            raise TypeError("%s event coordinates must be exact tuples" % name)
        for coordinate in event.coordinates:
            if type(coordinate) is not float:
                raise TypeError("%s coordinates must be exact floats" % name)
            if not math.isfinite(coordinate):
                raise ValueError("%s coordinates must be finite" % name)
            if coordinate == 0.0 and math.copysign(1.0, coordinate) < 0.0:
                raise ValueError("%s coordinates must use canonical zero" % name)
        reconstructed = TransformedEvent(event.event_type, event.coordinates)
        if reconstructed.model_key() != event.model_key():
            raise ValueError("%s contains a noncanonical event" % name)
    if tuple(sorted(configuration, key=TransformedEvent.model_key)) != configuration:
        raise ValueError("%s must be canonical" % name)
    return configuration


def _require_exact_candidate_representation(
    candidate: "ProcessValidReferenceJump",
) -> None:
    for name in (
        "reverse_time",
        "direct_time",
        "reference_schedule_rate",
        "scheduled_reference_exit_rate",
    ):
        if type(getattr(candidate, name)) is not float:
            raise TypeError("candidate %s must be an exact float" % name)
    if type(candidate.schema_version) is not str:
        raise TypeError("candidate schema_version must be exact text")
    if type(candidate.contract_scope) is not str:
        raise TypeError("candidate contract_scope must be exact text")
    if type(candidate.process_parameter_key) is not tuple:
        raise TypeError("candidate process_parameter_key must be an exact tuple")
    _validate_plain_key(
        candidate.process_parameter_key,
        remaining_nodes=[_MAX_PLUGIN_KEY_NODES],
    )
    if type(candidate.proposal) is not HybridReferenceJumpProposal:
        raise TypeError("candidate proposal has the wrong exact type")
    _require_exact_canonical_configuration(
        candidate.proposal.source_configuration,
        name="candidate proposal source_configuration",
    )
    _require_exact_canonical_configuration(
        candidate.proposal.destination_configuration,
        name="candidate proposal destination_configuration",
    )
    for name, event in (
        ("source_event", candidate.proposal.source_event),
        ("destination_event", candidate.proposal.destination_event),
    ):
        if event is not None:
            _require_exact_canonical_configuration(
                (event,),
                name="candidate proposal %s" % name,
            )
    if type(candidate.factorization) is not ReferenceJumpFactorization:
        raise TypeError("candidate factorization has the wrong exact type")
    factorization = candidate.factorization
    for name in (
        "family_rate",
        "family_probability",
        "occurrence_probability",
        "quotient_occurrence_probability",
        "destination_type_probability",
        "destination_coordinate_log_density",
        "destination_log_density",
        "proposal_log_density",
        "unscaled_reference_edge_log_density",
    ):
        if type(getattr(factorization, name)) is not float:
            raise TypeError("candidate factorization %s must be an exact float" % name)
    if type(factorization.source_event_multiplicity) is not int:
        raise TypeError(
            "candidate factorization source_event_multiplicity must be an exact int"
        )


def _require_exact_intensity_representation(
    intensity: "ReferenceCandidateIntensity",
) -> None:
    for name in (
        "schema_version",
        "contract_scope",
    ):
        if type(getattr(intensity, name)) is not str:
            raise TypeError("intensity %s must be exact text" % name)
    if type(intensity.process_parameter_key) is not tuple:
        raise TypeError("intensity process_parameter_key must be an exact tuple")
    _validate_plain_key(
        intensity.process_parameter_key,
        remaining_nodes=[_MAX_PLUGIN_KEY_NODES],
    )
    _require_exact_canonical_configuration(
        intensity.source_configuration,
        name="intensity source_configuration",
    )
    for name in (
        "reverse_time",
        "direct_time",
        "reference_schedule_rate",
        "scheduled_reference_exit_rate",
    ):
        if type(getattr(intensity, name)) is not float:
            raise TypeError("intensity %s must be an exact float" % name)
    if intensity.base_rates is not None:
        if type(intensity.base_rates) is not HybridJumpRates:
            raise TypeError(
                "intensity base_rates must be exact HybridJumpRates or None"
            )
        for name in ("birth", "death", "replacement", "total"):
            if type(getattr(intensity.base_rates, name)) is not float:
                raise TypeError("intensity base-rate fields must be exact floats")


@dataclass(frozen=True, init=False)
class ReferenceJumpFactorization:
    """Exact factors for the sampled labelled reference-edit route."""

    family_rate: float
    family_probability: float
    occurrence_probability: float
    source_event_multiplicity: int
    quotient_occurrence_probability: float
    destination_type_probability: float
    destination_coordinate_log_density: float
    destination_log_density: float
    proposal_log_density: float
    unscaled_reference_edge_log_density: float

    def __init__(
        self,
        *,
        family_rate: float,
        family_probability: float,
        occurrence_probability: float,
        source_event_multiplicity: int,
        quotient_occurrence_probability: float,
        destination_type_probability: float,
        destination_coordinate_log_density: float,
        destination_log_density: float,
        proposal_log_density: float,
        unscaled_reference_edge_log_density: float,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _FACTORIZATION_TOKEN:
            raise TypeError("reference-jump factorizations are composer-owned")
        values = locals().copy()
        values.pop("self")
        values.pop("_construction_token")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def __reduce__(self) -> object:
        raise TypeError("reference-jump factorizations are not pickle records")


@dataclass(frozen=True, init=False)
class ReferenceCandidateIntensity:
    """Sealed deterministic preflight for one reference candidate clock.

    A zero ``scheduled_reference_exit_rate`` is an exact short circuit.  A
    positive value is the represented arrival intensity of normalized
    reference proposals at the bound state and reverse time.  It is not a
    controlled/learned total exit rate and it performs no random draw.
    """

    schema_version: str
    contract_scope: str
    process_parameter_key: Tuple[object, ...]
    source_configuration: TransformedConfiguration
    reverse_time: float
    direct_time: float
    base_rates: Optional[HybridJumpRates]
    reference_schedule_rate: float
    scheduled_reference_exit_rate: float

    def __init__(
        self,
        *,
        schema_version: str,
        contract_scope: str,
        process_parameter_key: Tuple[object, ...],
        source_configuration: TransformedConfiguration,
        reverse_time: float,
        direct_time: float,
        base_rates: Optional[HybridJumpRates],
        reference_schedule_rate: float,
        scheduled_reference_exit_rate: float,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _INTENSITY_TOKEN:
            raise TypeError("reference candidate intensities are composer-owned")
        values = locals().copy()
        values.pop("self")
        values.pop("_construction_token")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def is_zero(self) -> bool:
        return self.scheduled_reference_exit_rate == 0.0

    @property
    def is_clean_hold(self) -> bool:
        return self.base_rates is None

    def __reduce__(self) -> object:
        raise TypeError("reference candidate intensities are not pickle records")


@dataclass(frozen=True, init=False)
class ProcessValidReferenceJump:
    """Sealed process-valid candidate under the normalized reference kernel."""

    schema_version: str
    contract_scope: str
    process_parameter_key: Tuple[object, ...]
    reverse_time: float
    direct_time: float
    reference_schedule_rate: float
    scheduled_reference_exit_rate: float
    proposal: HybridReferenceJumpProposal
    factorization: ReferenceJumpFactorization

    def __init__(
        self,
        *,
        schema_version: str,
        contract_scope: str,
        process_parameter_key: Tuple[object, ...],
        reverse_time: float,
        direct_time: float,
        reference_schedule_rate: float,
        scheduled_reference_exit_rate: float,
        proposal: HybridReferenceJumpProposal,
        factorization: ReferenceJumpFactorization,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _CANDIDATE_TOKEN:
            raise TypeError("process-valid reference jumps are composer-owned")
        values = locals().copy()
        values.pop("self")
        values.pop("_construction_token")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def source_configuration(self) -> TransformedConfiguration:
        return self.proposal.source_configuration

    @property
    def destination_configuration(self) -> TransformedConfiguration:
        return self.proposal.destination_configuration

    @property
    def kind(self) -> HybridJumpKind:
        return self.proposal.kind

    @property
    def reference_to_proposal_log_ratio(self) -> float:
        """Log RN ratio for this labelled draw, equal to ``log(gamma Lambda)``."""

        # The occurrence and destination factors are identical under the
        # normalized reference proposal.  Cancel them symbolically; subtracting
        # two very negative Gaussian log densities would lose precision.
        return math.fsum(
            (
                math.log(self.reference_schedule_rate),
                math.log(self.factorization.family_rate),
                -math.log(self.factorization.family_probability),
            )
        )

    def __reduce__(self) -> object:
        raise TypeError("process-valid reference jumps are not pickle records")


@dataclass(frozen=True, init=False)
class CertifiedBaseEnergyEvaluation:
    """Certified base-energy integrand and ratio, never sampler admission."""

    candidate: ProcessValidReferenceJump
    context: Tuple[float, ...]
    architecture_sha256: str
    checkpoint_sha256: str
    certificate_sha256: str
    provenance_sha256: str
    energy_difference: float
    energy_multiplier: float
    sampled_tilted_integrand: float
    operational_envelope: float
    base_energy_acceptance_ratio: float

    def __init__(
        self,
        *,
        candidate: ProcessValidReferenceJump,
        context: Tuple[float, ...],
        architecture_sha256: str,
        checkpoint_sha256: str,
        certificate_sha256: str,
        provenance_sha256: str,
        energy_difference: float,
        energy_multiplier: float,
        sampled_tilted_integrand: float,
        operational_envelope: float,
        base_energy_acceptance_ratio: float,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _ENERGY_EVALUATION_TOKEN:
            raise TypeError("certified energy evaluations are module-owned")
        values = locals().copy()
        values.pop("self")
        values.pop("_construction_token")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def __reduce__(self) -> object:
        raise TypeError("certified energy evaluations are not pickle records")


def _family_rate(proposal: HybridReferenceJumpProposal) -> float:
    if proposal.kind is HybridJumpKind.BIRTH:
        return proposal.base_rates.birth
    if proposal.kind is HybridJumpKind.DEATH:
        return proposal.base_rates.death
    return proposal.base_rates.replacement


def _factorization(
    process: ReversibleHybridReference,
    proposal: HybridReferenceJumpProposal,
) -> ReferenceJumpFactorization:
    total = proposal.base_rates.total
    family_rate = _family_rate(proposal)
    family_probability = family_rate / total
    if (
        not math.isfinite(family_probability)
        or family_probability <= 0.0
        or family_probability > 1.0
    ):
        raise ArithmeticError("proposal family probability is invalid")

    occurrence_probability = 1.0
    source_multiplicity = 1
    quotient_occurrence_probability = 1.0
    destination_type_probability = 1.0
    destination_coordinate_log_density = 0.0

    if proposal.kind is HybridJumpKind.BIRTH:
        destination = proposal.destination_event
        assert destination is not None
        destination_type_probability = process.reference.type_weights[
            destination.event_type
        ]
        destination_coordinate_log_density = _standard_gaussian_log_density(destination)
    elif proposal.kind is HybridJumpKind.DEATH:
        source = proposal.source_event
        assert source is not None
        source_multiplicity = proposal.source_configuration.count(source)
        occurrence_probability = 1.0 / len(proposal.source_configuration)
        quotient_occurrence_probability = source_multiplicity * occurrence_probability
    else:
        source = proposal.source_event
        destination = proposal.destination_event
        assert source is not None
        assert destination is not None
        source_multiplicity = proposal.source_configuration.count(source)
        outgoing = process.rates.outgoing_replacement_rate(source.event_type)
        primitive = process.rates.replacement_rate(
            source.event_type, destination.event_type
        )
        occurrence_probability = outgoing / proposal.base_rates.replacement
        quotient_occurrence_probability = source_multiplicity * occurrence_probability
        destination_type_probability = primitive / outgoing
        destination_coordinate_log_density = _standard_gaussian_log_density(destination)

    for name, probability in (
        ("occurrence_probability", occurrence_probability),
        ("quotient_occurrence_probability", quotient_occurrence_probability),
        ("destination_type_probability", destination_type_probability),
    ):
        if not math.isfinite(probability) or probability <= 0.0 or probability > 1.0:
            raise ArithmeticError("%s is invalid" % name)

    destination_log_density = math.fsum(
        (
            math.log(destination_type_probability),
            destination_coordinate_log_density,
        )
    )
    proposal_log_density = math.fsum(
        (
            math.log(family_probability),
            math.log(occurrence_probability),
            destination_log_density,
        )
    )
    reference_edge_log_density = math.fsum(
        (
            math.log(family_rate),
            math.log(occurrence_probability),
            destination_log_density,
        )
    )
    if not all(
        math.isfinite(value)
        for value in (
            destination_log_density,
            proposal_log_density,
            reference_edge_log_density,
        )
    ):
        raise ArithmeticError("reference proposal log factors are not finite")
    return ReferenceJumpFactorization(
        family_rate=family_rate,
        family_probability=family_probability,
        occurrence_probability=occurrence_probability,
        source_event_multiplicity=source_multiplicity,
        quotient_occurrence_probability=quotient_occurrence_probability,
        destination_type_probability=destination_type_probability,
        destination_coordinate_log_density=destination_coordinate_log_density,
        destination_log_density=destination_log_density,
        proposal_log_density=proposal_log_density,
        unscaled_reference_edge_log_density=reference_edge_log_density,
        _construction_token=_FACTORIZATION_TOKEN,
    )


class ProcessValidReferenceJumpComposer:
    """Immutable process owner for one normalized reference candidate draw."""

    __slots__ = ("_process", "_process_parameter_key")

    def __init__(self, process: ReversibleHybridReference) -> None:
        if type(process) is not ReversibleHybridReference:
            raise TypeError("process must be an exact ReversibleHybridReference")
        object.__setattr__(self, "_process", process)
        object.__setattr__(self, "_process_parameter_key", process.parameter_key())

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("ProcessValidReferenceJumpComposer is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("ProcessValidReferenceJumpComposer is immutable")

    @property
    def process(self) -> ReversibleHybridReference:
        return self._process

    @property
    def process_parameter_key(self) -> Tuple[object, ...]:
        return self._process_parameter_key

    def _require_live_binding(self) -> None:
        if type(self._process) is not ReversibleHybridReference:
            raise RuntimeError("composer process binding has the wrong exact type")
        live_key = self._process.parameter_key()
        cached_key = self._process_parameter_key
        try:
            _validate_plain_key(
                live_key,
                remaining_nodes=[_MAX_PLUGIN_KEY_NODES],
            )
            _validate_plain_key(
                cached_key,
                remaining_nodes=[_MAX_PLUGIN_KEY_NODES],
            )
        except (TypeError, ValueError) as error:
            raise RuntimeError("composer process binding is noncanonical") from error
        if not _same_plain_type_tree(live_key, cached_key):
            raise RuntimeError("composer process binding changed")

    def _preflight_categorical_laws(
        self,
        source: TransformedConfiguration,
        base_rates: HybridJumpRates,
    ) -> None:
        family_weights = tuple(
            value
            for value in (
                base_rates.birth,
                base_rates.death,
                base_rates.replacement,
            )
            if value > 0.0
        )
        _validate_categorical_weights(family_weights, context="reference jump family")
        if base_rates.birth > 0.0:
            _validate_categorical_weights(
                tuple(
                    self.process.reference.type_weights[event_type]
                    for event_type in self.process.reference.type_ids
                ),
                context="reference birth destination type",
            )
        if base_rates.replacement > 0.0:
            source_weights_list = []
            source_types_set = set()
            for event in source:
                outgoing = self.process.rates.outgoing_replacement_rate(
                    event.event_type
                )
                if outgoing > 0.0:
                    source_weights_list.append(outgoing)
                    source_types_set.add(event.event_type)
            _validate_categorical_weights(
                tuple(source_weights_list),
                context="reference replacement source",
            )
            for source_type in sorted(source_types_set):
                destination_rates = tuple(
                    rate
                    for _, rate in self.process.rates.replacement_destinations(
                        source_type
                    )
                )
                _validate_categorical_weights(
                    destination_rates,
                    context=(
                        "reference replacement destination from type %d" % source_type
                    ),
                )

    def preflight_candidate_intensity(
        self,
        state: Iterable[TransformedEvent],
        *,
        reverse_time: object,
    ) -> ReferenceCandidateIntensity:
        """Return the process-owned candidate rate without consuming RNG.

        Positive categorical route laws are checked here so a future waiting
        time is never drawn for a candidate clock whose normalized reference
        edit cannot subsequently be sampled under the frozen float64 contract.
        The exact clean hold and a structurally zero base exit return a sealed
        zero-rate record without evaluating any model.
        """

        self._require_live_binding()
        source = self.process.reference.canonicalize(state)
        _require_exact_canonical_configuration(
            source,
            name="candidate intensity source",
        )
        reverse, direct = _reverse_to_direct_time(self.process, reverse_time)
        schedule_rate = _validated_real(
            self.process.schedule.jump_rate(direct),
            name="reference_schedule_rate",
            nonnegative=True,
        )
        if direct <= self.process.schedule.clean_hold:
            if schedule_rate != 0.0:
                raise RuntimeError("clean-hold reference schedule is not zero")
            base_rates = None
            scheduled_exit = 0.0
        else:
            base_rates = self.process.base_jump_rates(source)
            if base_rates.total == 0.0:
                scheduled_exit = 0.0
            else:
                if schedule_rate <= 0.0:
                    raise RuntimeError("active reference schedule is not positive")
                scheduled_exit = _checked_positive_product(
                    schedule_rate,
                    base_rates.total,
                    name="scheduled reference candidate intensity",
                )
                self._preflight_categorical_laws(source, base_rates)
        return ReferenceCandidateIntensity(
            schema_version=PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCHEMA,
            contract_scope=PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCOPE,
            process_parameter_key=self.process_parameter_key,
            source_configuration=source,
            reverse_time=reverse,
            direct_time=direct,
            base_rates=base_rates,
            reference_schedule_rate=schedule_rate,
            scheduled_reference_exit_rate=scheduled_exit,
            _construction_token=_INTENSITY_TOKEN,
        )

    def validate_candidate_intensity(
        self,
        intensity: ReferenceCandidateIntensity,
    ) -> ReferenceCandidateIntensity:
        """Recompute a deterministic preflight and reject altered records."""

        self._require_live_binding()
        if type(intensity) is not ReferenceCandidateIntensity:
            raise TypeError("intensity must be an exact ReferenceCandidateIntensity")
        _require_exact_intensity_representation(intensity)
        if intensity.schema_version != PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCHEMA:
            raise ValueError("intensity schema version differs")
        if intensity.contract_scope != PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCOPE:
            raise ValueError("intensity contract scope differs")
        if not _same_plain_type_tree(
            intensity.process_parameter_key,
            self.process_parameter_key,
        ):
            raise ValueError("intensity belongs to a different process")
        canonical = self.process.reference.canonicalize(intensity.source_configuration)
        if canonical != intensity.source_configuration:
            raise ValueError("intensity source configuration is not canonical")
        expected = self.preflight_candidate_intensity(
            canonical,
            reverse_time=intensity.reverse_time,
        )
        for name in (
            "source_configuration",
            "reverse_time",
            "direct_time",
            "base_rates",
            "reference_schedule_rate",
            "scheduled_reference_exit_rate",
        ):
            if getattr(intensity, name) != getattr(expected, name):
                raise ValueError("intensity %s differs from the process" % name)
        return intensity

    def sample_candidate(
        self,
        state: Iterable[TransformedEvent],
        *,
        reverse_time: object,
        rng: np.random.Generator,
    ) -> Optional[ProcessValidReferenceJump]:
        """Draw one labelled route from ``q_s^0 / Lambda_s^0``.

        The returned scheduled rate is the arrival intensity of candidate
        proposals.  It is neither a pointwise continuous edge density nor an
        integrated learned total exit rate.
        """

        generator = _validated_rng(rng)
        intensity = self.preflight_candidate_intensity(
            state,
            reverse_time=reverse_time,
        )
        return self.sample_candidate_from_intensity(intensity, rng=generator)

    def sample_candidate_from_intensity(
        self,
        intensity: ReferenceCandidateIntensity,
        *,
        rng: np.random.Generator,
    ) -> Optional[ProcessValidReferenceJump]:
        """Draw the normalized route after revalidating a no-RNG preflight."""

        generator = _validated_rng(rng)
        checked = self.validate_candidate_intensity(intensity)
        if checked.is_zero:
            return None
        if checked.base_rates is None:
            raise RuntimeError("positive intensity has no base-rate decomposition")
        proposal = self.process.sample_base_jump(
            checked.source_configuration,
            rng=generator,
        )
        if proposal.base_rates != checked.base_rates:
            raise RuntimeError("sampled proposal rates changed after preflight")
        factors = _factorization(self.process, proposal)
        candidate = ProcessValidReferenceJump(
            schema_version=PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCHEMA,
            contract_scope=PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCOPE,
            process_parameter_key=self.process_parameter_key,
            reverse_time=checked.reverse_time,
            direct_time=checked.direct_time,
            reference_schedule_rate=checked.reference_schedule_rate,
            scheduled_reference_exit_rate=checked.scheduled_reference_exit_rate,
            proposal=proposal,
            factorization=factors,
            _construction_token=_CANDIDATE_TOKEN,
        )
        return self.validate_candidate(candidate)

    def validate_candidate(
        self, candidate: ProcessValidReferenceJump
    ) -> ProcessValidReferenceJump:
        """Recompute all process, time, rate, edit, and density fields."""

        self._require_live_binding()
        if type(candidate) is not ProcessValidReferenceJump:
            raise TypeError("candidate must be an exact ProcessValidReferenceJump")
        _require_exact_candidate_representation(candidate)
        if candidate.schema_version != PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCHEMA:
            raise ValueError("candidate schema version differs")
        if candidate.contract_scope != PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCOPE:
            raise ValueError("candidate contract scope differs")
        if not _same_plain_type_tree(
            candidate.process_parameter_key, self.process_parameter_key
        ):
            raise ValueError("candidate belongs to a different process")
        proposal = self.process.validate_jump_proposal(candidate.proposal)
        intensity = self.preflight_candidate_intensity(
            proposal.source_configuration,
            reverse_time=candidate.reverse_time,
        )
        if intensity.is_zero:
            raise ValueError("an active candidate has zero reference intensity")
        if candidate.direct_time != intensity.direct_time:
            raise ValueError("candidate direct time is inconsistent")
        if proposal.base_rates != intensity.base_rates:
            raise ValueError("candidate base rates differ from the process")
        if candidate.reference_schedule_rate != intensity.reference_schedule_rate:
            raise ValueError("candidate schedule rate differs from the process")
        if (
            candidate.scheduled_reference_exit_rate
            != intensity.scheduled_reference_exit_rate
        ):
            raise ValueError("candidate arrival intensity differs from the process")
        expected_factors = _factorization(self.process, proposal)
        if (
            type(candidate.factorization) is not ReferenceJumpFactorization
            or candidate.factorization != expected_factors
        ):
            raise ValueError("candidate proposal factors differ from the process")
        expected_log_ratio = math.log(intensity.scheduled_reference_exit_rate)
        actual_log_ratio = candidate.reference_to_proposal_log_ratio
        tolerance = (
            32.0 * float(np.finfo(np.float64).eps) * max(1.0, abs(expected_log_ratio))
        )
        if not math.isclose(
            actual_log_ratio,
            expected_log_ratio,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            raise ArithmeticError(
                "reference-to-proposal ratio is inconsistent with arrival intensity"
            )
        if intensity.reverse_time != candidate.reverse_time:
            raise RuntimeError("validated reverse time changed unexpectedly")
        return candidate

    def jump_flux_proposal_factors(
        self,
        candidate: ProcessValidReferenceJump,
        *,
        target_time_density: object,
        proposal_time_density: object,
        target_state_density: object,
        proposal_state_density: object,
    ) -> object:
        """Compose complete objective factors when densities are normal.

        Gaussian log densities remain authoritative.  If their ordinary value
        would be subnormal or zero, this convenience conversion fails instead
        of erasing a positive destination density.  The training caller must
        supply all four time/state densities explicitly; those laws are not
        owned by the reference process and are never silently set to one.
        """

        checked = self.validate_candidate(candidate)
        from heterodiff.theory.reverse_energy_objective import (
            JumpFluxProposalFactors,
        )

        destination_density = _materialize_normal_positive_density(
            checked.factorization.destination_log_density
        )
        return JumpFluxProposalFactors(
            target_time_density=target_time_density,
            proposal_time_density=proposal_time_density,
            target_state_density=target_state_density,
            proposal_state_density=proposal_state_density,
            reference_schedule_rate=checked.reference_schedule_rate,
            reference_family_rate=checked.factorization.family_rate,
            proposal_family_probability=(checked.factorization.family_probability),
            reference_occurrence_probability=(
                checked.factorization.occurrence_probability
            ),
            proposal_occurrence_probability=(
                checked.factorization.occurrence_probability
            ),
            reference_destination_density=destination_density,
            proposal_destination_density=destination_density,
        )


def _validated_context(context: object, *, dimension: int) -> Tuple[float, ...]:
    if dimension < 0 or dimension > _MAX_CONTEXT_DIMENSION:
        raise ValueError("energy context dimension is outside the adapter limit")
    if isinstance(context, (str, bytes)):
        raise TypeError("context must be a finite numeric sequence")
    try:
        iterator = iter(context)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("context must be a finite numeric sequence") from error
    result = []
    for value in iterator:
        if len(result) >= _MAX_CONTEXT_DIMENSION:
            raise ValueError("context exceeds the adapter dimension limit")
        result.append(_validated_real(value, name="context entry"))
    if len(result) != dimension:
        raise ValueError("context must contain exactly %d entries" % dimension)
    return tuple(result)


def _configuration_tensor_maps(
    torch_module: object,
    architecture: object,
    configuration: TransformedConfiguration,
) -> Tuple[dict, dict]:
    coordinates = {}
    owners = {}
    for event_type, dimension in zip(
        architecture.type_ids, architecture.type_dimensions
    ):
        events = tuple(
            event for event in configuration if event.event_type == event_type
        )
        if not events:
            continue
        if dimension == 0:
            coordinate_tensor = torch_module.empty(
                (len(events), 0), dtype=torch_module.float64, device="cpu"
            )
        else:
            coordinate_tensor = torch_module.tensor(
                [event.coordinates for event in events],
                dtype=torch_module.float64,
                device="cpu",
            )
        owner_tensor = torch_module.zeros(
            (len(events),), dtype=torch_module.int64, device="cpu"
        )
        coordinates[event_type] = coordinate_tensor
        owners[event_type] = owner_tensor
    return coordinates, owners


def evaluate_certified_base_energy(
    composer: ProcessValidReferenceJumpComposer,
    candidate: ProcessValidReferenceJump,
    *,
    model: object,
    checkpoint: object,
    expected_provenance: object,
    context: object,
) -> CertifiedBaseEnergyEvaluation:
    """Project one process-valid candidate through a certified base energy.

    The returned ``sampled_tilted_integrand`` is
    ``gamma_J(s) Lambda^0(x) exp(V(s,y,z)-V(s,x,z))`` under one draw from the
    normalized reference proposal.  It must not be aggregated or reported as
    the learned total exit rate without a separate integration procedure.
    The retained envelope ratio is arithmetic only; this module does not draw
    a Bernoulli decision or certify that its probability is RNG-resolvable.
    """

    if type(composer) is not ProcessValidReferenceJumpComposer:
        raise TypeError("composer must be an exact ProcessValidReferenceJumpComposer")
    checked = composer.validate_candidate(candidate)

    try:
        import torch
        from heterodiff.models.configuration_energy_torch import (
            certified_tilted_jump_rates,
            configuration_energy_edge_difference,
            pack_typed_configuration_batch,
            require_matching_configuration_energy_certificate,
        )
    except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
        if error.name == "torch":
            raise ModuleNotFoundError(
                "certified base-energy projection requires the optional "
                "PyTorch reference dependency"
            ) from error
        raise

    preflight_certificate = require_matching_configuration_energy_certificate(
        model,
        checkpoint,
        expected_provenance=expected_provenance,
    )
    architecture = model.architecture
    if architecture.process_parameter_key != composer.process_parameter_key:
        raise ValueError("certified energy belongs to a different process")
    checked_context = _validated_context(
        context, dimension=architecture.context_dimension
    )

    def pack(configuration: TransformedConfiguration) -> object:
        coordinates, owners = _configuration_tensor_maps(
            torch, architecture, configuration
        )
        return pack_typed_configuration_batch(
            architecture,
            torch.tensor([checked.direct_time], dtype=torch.float64, device="cpu"),
            torch.tensor([checked_context], dtype=torch.float64, device="cpu").reshape(
                1, architecture.context_dimension
            ),
            coordinates,
            owners,
        )

    source_batch = pack(checked.source_configuration)
    destination_batch = pack(checked.destination_configuration)
    difference_tensor = configuration_energy_edge_difference(
        model, source_batch, destination_batch
    )
    reference_rate_tensor = torch.tensor(
        [checked.scheduled_reference_exit_rate],
        dtype=torch.float64,
        device="cpu",
    )
    tilted_tensor = certified_tilted_jump_rates(
        model,
        checkpoint,
        source_batch,
        destination_batch,
        reference_rates=reference_rate_tensor,
        expected_provenance=expected_provenance,
    )
    expected_tilted_tensor = reference_rate_tensor * torch.exp(
        difference_tensor.detach()
    )
    if not torch.equal(tilted_tensor.detach(), expected_tilted_tensor):
        raise RuntimeError(
            "certified tilted value differs from the recorded energy difference"
        )
    postflight_certificate = require_matching_configuration_energy_certificate(
        model,
        checkpoint,
        expected_provenance=expected_provenance,
    )
    if (
        postflight_certificate.certificate_sha256
        != preflight_certificate.certificate_sha256
    ):
        raise RuntimeError("energy certificate changed during candidate evaluation")

    difference = float(difference_tensor.detach().item())
    multiplier = float(torch.exp(difference_tensor.detach()).item())
    tilted = float(tilted_tensor.detach().item())
    for name, value in (
        ("energy_difference", difference),
        ("energy_multiplier", multiplier),
        ("sampled_tilted_integrand", tilted),
    ):
        if not math.isfinite(value):
            raise ArithmeticError("%s is not finite" % name)
    if multiplier <= 0.0 or tilted <= 0.0:
        raise ArithmeticError("certified active energy projection must be positive")
    envelope = postflight_certificate.energy_bounds.tilted_rate_upper_bound(
        checked.scheduled_reference_exit_rate
    )
    acceptance = tilted / envelope
    if not math.isfinite(acceptance) or acceptance <= 0.0 or acceptance > 1.0:
        raise ArithmeticError(
            "base-energy candidate acceptance ratio is outside (0, 1]"
        )
    return CertifiedBaseEnergyEvaluation(
        candidate=checked,
        context=checked_context,
        architecture_sha256=architecture.architecture_sha256,
        checkpoint_sha256=checkpoint.snapshot.checkpoint_sha256,
        certificate_sha256=postflight_certificate.certificate_sha256,
        provenance_sha256=postflight_certificate.provenance_sha256,
        energy_difference=difference,
        energy_multiplier=multiplier,
        sampled_tilted_integrand=tilted,
        operational_envelope=envelope,
        base_energy_acceptance_ratio=acceptance,
        _construction_token=_ENERGY_EVALUATION_TOKEN,
    )


__all__ = [
    "PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCHEMA",
    "PLUGIN_BRIDGE_REFERENCE_INTENSITY_SCOPE",
    "PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCHEMA",
    "PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCOPE",
    "CertifiedBaseEnergyEvaluation",
    "ProcessValidReferenceJump",
    "ProcessValidReferenceJumpComposer",
    "ReferenceCandidateIntensity",
    "ReferenceJumpFactorization",
    "UnsupportedPluginBridgeSamplingError",
    "evaluate_certified_base_energy",
]
