"""Target-explicit composition of one totalized operational jump potential.

For reverse time ``u``, direct time ``s = S - u``, fixed guide observation,
and explicit base/residual contexts, this module selects the point target

``Phi_Q^op(u, x) = iota(V_64(s, x)) + iota(G_64^op(u, x))
                   + iota(R_64^op(s, x))``.

``iota`` interprets a finite binary64 value as an exact rational.  For one
process-valid jump, the three exact represented endpoint differences are
added as rationals and the aggregate is rounded once to binary64.  The exact
rational record is therefore a coboundary of one explicit operational point
potential.  Separately rounded binary64 edges need not telescope.

The base is evaluated through an unexposed model materialized from its
certified checkpoint.  The guide and residual are the separately certified
totalized owners.  This module catches no component failure and introduces no
additional fallback.  It does not exponentiate the aggregate or construct a
rate envelope, total exit, clock, random decision, drift, initializer, path,
or sampler.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from numbers import Real
import platform
import struct
import sys
from typing import Dict, Iterable, Mapping, Tuple

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch":
        raise ModuleNotFoundError(
            "configuration totalized jump-potential composition requires the "
            "optional PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.artifacts.manifest import canonical_config_digest
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy,
    CertifiedConfigurationEnergyCheckpoint,
    ConfigurationEnergyCheckpointCertificate,
    ConfigurationEnergyProvenance,
    TypedConfigurationBatch,
    materialize_configuration_energy_checkpoint,
    pack_typed_configuration_batch,
    require_matching_configuration_energy_certificate,
)
from heterodiff.models.configuration_totalized_jump_residual_torch import (
    EXACT_GATE_RESCALED_CORE_BRANCH,
    PRESERVED_CERTIFIED_RESIDUAL_BRANCH,
    TotalizedConditionalJumpResidual,
    TotalizedResidualJumpCertificate,
    TotalizedResidualJumpDifference,
    require_matching_totalized_conditional_jump_residual,
)
from heterodiff.processes.plugin_bridge_sampler import (
    ProcessValidReferenceJump,
    ProcessValidReferenceJumpComposer,
)
from heterodiff.theory.association_totalized_jump_guide import (
    NUMERICAL_FALLBACK_BRANCH,
    PRESERVED_RANGE_GATED_BRANCH,
    RANGE_FALLBACK_BRANCH,
    TotalizedAssociationJumpGuide,
    TotalizedJumpGuideCertificate,
    TotalizedJumpGuideEditRatio,
    require_matching_totalized_association_jump_guide,
)
from heterodiff.theory.association_preconditioner import _plain_key_sha256
from heterodiff.theory.configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    MAX_REFERENCE_DENSITY_COORDINATES,
    TransformedConfiguration,
    TransformedEvent,
)


CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCHEMA_VERSION = (
    "configuration-totalized-jump-potential-composition-v1"
)
CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY = (
    "operational-surrogate-jump-potential-v1;"
    "Phi_Q_op(u,x)=iota(V64(S-u,x,c_base))+"
    "iota(G64_totalized(u,x,fixed_observation))+"
    "iota(R64_totalized(S-u,x,c_residual));"
    "edge-is-destination-minus-source"
)
CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_COMPOSITION_POLICY = (
    "exact-rational-represented-endpoint-coboundary;"
    "ignore-component-rounded-edges-for-aggregate;"
    "single-final-binary64-nearest-even-round;canonical-positive-zero;"
    "no-added-fallback"
)
CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_ROUNDING_ALGORITHM = (
    "lift-six-represented-binary64-endpoint-values-to-exact-fractions;"
    "subtract-and-sum-exactly;round-aggregate-once-to-binary64-nearest-even;"
    "canonicalize-exact-zero-positive"
)
CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_FLOATING_POINT_POLICY = (
    "binary64-round-to-nearest-even-and-gradual-underflow-required;"
    "live-python-and-torch-arithmetic-probe-before-and-after-composition"
)
CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCOPE = (
    "one-active-process-valid-reference-candidate;checkpoint-materialized-base;"
    "fixed-observation-totalized-guide;totalized-jump-residual;"
    "explicit-base-and-residual-contexts;exact-operational-point-coboundary;"
    "global-operational-point-and-edge-magnitude-bounds;trusted-runtime;"
    "not-exact-analytic-conditional-or-posterior-target;"
    "not-small-forward-error;not-rounded-cycle-closure;"
    "not-aggregate-exponentiation;not-rate-envelope;not-total-exit;"
    "not-clock;not-rng;not-derivatives;not-drift;not-initializer;"
    "not-path;not-sampler-admission"
)


MAX_TOTALIZED_JUMP_POTENTIAL_EXACT_INTEGER_BITS = 8192
_MAX_CONTEXT_DIMENSION = 4096
_CERTIFICATE_TOKEN = object()
_COMPOSER_TOKEN = object()
_EVALUATION_TOKEN = object()

_GUIDE_BRANCHES = (
    PRESERVED_RANGE_GATED_BRANCH,
    NUMERICAL_FALLBACK_BRANCH,
    RANGE_FALLBACK_BRANCH,
)
_RESIDUAL_BRANCHES = (
    PRESERVED_CERTIFIED_RESIDUAL_BRANCH,
    EXACT_GATE_RESCALED_CORE_BRANCH,
)


class ConfigurationTotalizedJumpPotentialError(ArithmeticError):
    """Raised only when checkpoint-17 composition itself cannot be certified."""


def _same_float(left: float, right: float) -> bool:
    return struct.pack(">d", left) == struct.pack(">d", right)


def _canonical_zero(value: float) -> float:
    return 0.0 if value == 0.0 else value


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _validated_float(
    value: object,
    *,
    name: str,
    nonnegative: bool = False,
    strictly_positive: bool = False,
    canonical_zero: bool = False,
) -> float:
    if type(value) is not float:
        raise TypeError("%s must be an exact float" % name)
    if not math.isfinite(value):
        raise ValueError("%s must be finite" % name)
    if nonnegative and value < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    if strictly_positive and value <= 0.0:
        raise ValueError("%s must be strictly positive" % name)
    if canonical_zero and value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError("%s must use canonical positive zero" % name)
    return value


def _fraction(value: float) -> Fraction:
    return Fraction.from_float(value)


def _require_fraction_size(value: Fraction, *, name: str) -> Fraction:
    if (
        value.numerator.bit_length() > MAX_TOTALIZED_JUMP_POTENTIAL_EXACT_INTEGER_BITS
        or value.denominator.bit_length()
        > MAX_TOTALIZED_JUMP_POTENTIAL_EXACT_INTEGER_BITS
    ):
        raise ConfigurationTotalizedJumpPotentialError(
            "%s exceeds the exact-arithmetic resource limit" % name
        )
    return value


def _validated_fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    for field_name, value in (
        ("numerator", numerator),
        ("denominator", denominator),
    ):
        if type(value) is not int or isinstance(value, bool):
            raise TypeError("%s %s must be an exact integer" % (name, field_name))
        if value.bit_length() > MAX_TOTALIZED_JUMP_POTENTIAL_EXACT_INTEGER_BITS:
            raise ValueError("%s %s exceeds the resource limit" % (name, field_name))
    if denominator <= 0:
        raise ValueError("%s denominator must be positive" % name)
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        raise ValueError("%s must be stored in reduced form" % name)
    return _require_fraction_size(result, name=name)


def _round_fraction_once(value: Fraction, *, name: str) -> float:
    _require_fraction_size(value, name=name)
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ConfigurationTotalizedJumpPotentialError(
            "%s has no finite binary64 representation" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationTotalizedJumpPotentialError(
            "%s has no finite binary64 representation" % name
        )
    return _canonical_zero(result)


def _outward_nonnegative_fraction(value: Fraction, *, name: str) -> float:
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    _require_fraction_size(value, name=name)
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ConfigurationTotalizedJumpPotentialError(
            "%s has no finite binary64 upper witness" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationTotalizedJumpPotentialError(
            "%s has no finite binary64 upper witness" % name
        )
    if _fraction(result) < value:
        result = math.nextafter(result, math.inf)
    if not math.isfinite(result):
        raise ConfigurationTotalizedJumpPotentialError(
            "%s cannot be rounded outward" % name
        )
    return _canonical_zero(result)


def _outward_sum(values: Iterable[float], *, name: str) -> float:
    exact = Fraction(0)
    for value in values:
        checked = _validated_float(value, name=name, nonnegative=True)
        exact = _require_fraction_size(exact + _fraction(checked), name=name)
    return _outward_nonnegative_fraction(exact, name=name)


def _validated_context(
    context: object,
    *,
    dimension: int,
    name: str,
) -> Tuple[float, ...]:
    if type(dimension) is not int or not 0 <= dimension <= _MAX_CONTEXT_DIMENSION:
        raise ValueError("%s dimension is outside the adapter limit" % name)
    if isinstance(context, (str, bytes)):
        raise TypeError("%s must be a finite numeric sequence" % name)
    try:
        iterator = iter(context)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("%s must be a finite numeric sequence" % name) from error
    result = []
    for raw in iterator:
        if len(result) >= _MAX_CONTEXT_DIMENSION:
            raise ValueError("%s exceeds the adapter dimension limit" % name)
        if isinstance(raw, bool) or not isinstance(raw, Real):
            raise TypeError("%s entries must be real non-boolean scalars" % name)
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError("%s entries must be finite" % name)
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("%s entries must use canonical positive zero" % name)
        result.append(value)
    if len(result) != dimension:
        raise ValueError("%s must contain exactly %d entries" % (name, dimension))
    return tuple(result)


def _typed_digest_value(value: object) -> object:
    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-decimal-v1", str(value)]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("digest floats must be finite")
        return ["float64-hex-v1", value.hex()]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is tuple:
        return ["tuple-v1", [_typed_digest_value(item) for item in value]]
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("digest mappings require exact string keys")
            items.append((key, _typed_digest_value(item)))
        items.sort(key=lambda pair: pair[0])
        return ["mapping-v1", items]
    raise TypeError("unsupported digest value of type %s" % type(value).__name__)


def _semantic_digest(value: Mapping[str, object]) -> str:
    return canonical_config_digest(
        {"configuration_totalized_jump_potential": _typed_digest_value(value)}
    )


def _framed_update(digest: "hashlib._Hash", value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big", signed=False))
    digest.update(value)


def _configuration_sha256(configuration: TransformedConfiguration) -> str:
    if type(configuration) is not tuple:
        raise TypeError("candidate states must be exact tuples")
    if len(configuration) > MAX_CONFIGURATION_CARDINALITY:
        raise ValueError("candidate state exceeds the cardinality limit")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-totalized-jump-potential-state-v1\x00")
    digest.update(len(configuration).to_bytes(8, "big", signed=False))
    coordinate_count = 0
    for occurrence, event in enumerate(configuration):
        if type(event) is not TransformedEvent:
            raise TypeError(
                "candidate states must contain exact TransformedEvent values"
            )
        checked_event = TransformedEvent(event.event_type, event.coordinates)
        if event.model_key() != checked_event.model_key():
            raise ValueError("candidate state contains a noncanonical event")
        coordinate_count += len(checked_event.coordinates)
        if coordinate_count > MAX_REFERENCE_DENSITY_COORDINATES:
            raise ValueError("candidate state exceeds the coordinate limit")
        digest.update(occurrence.to_bytes(8, "big", signed=False))
        digest.update(checked_event.event_type.to_bytes(8, "big", signed=False))
        digest.update(len(checked_event.coordinates).to_bytes(8, "big", signed=False))
        for coordinate in checked_event.coordinates:
            digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _copy_configuration(
    configuration: TransformedConfiguration,
) -> TransformedConfiguration:
    return tuple(
        TransformedEvent(event.event_type, tuple(event.coordinates))
        for event in configuration
    )


def _candidate_sha256(candidate: ProcessValidReferenceJump) -> str:
    if type(candidate) is not ProcessValidReferenceJump:
        raise TypeError("candidate must be an exact ProcessValidReferenceJump")
    proposal = candidate.proposal
    factor = candidate.factorization
    digest = hashlib.sha256()
    digest.update(b"heterodiff-totalized-jump-potential-candidate-v1\x00")
    for value in (
        candidate.schema_version,
        candidate.contract_scope,
        _plain_key_sha256(
            candidate.process_parameter_key,
            domain=b"heterodiff-totalized-jump-potential-process-v1\x00",
        ),
        _plain_key_sha256(
            proposal.process_key,
            domain=b"heterodiff-totalized-jump-potential-proposal-process-v1\x00",
        ),
        proposal.kind.value,
    ):
        _framed_update(digest, value.encode("utf-8"))
    for value in (
        candidate.reverse_time,
        candidate.direct_time,
        candidate.reference_schedule_rate,
        candidate.scheduled_reference_exit_rate,
        proposal.base_rates.birth,
        proposal.base_rates.death,
        proposal.base_rates.replacement,
        proposal.base_rates.total,
        factor.family_rate,
        factor.family_probability,
        factor.occurrence_probability,
        factor.quotient_occurrence_probability,
        factor.destination_type_probability,
        factor.destination_coordinate_log_density,
        factor.destination_log_density,
        factor.proposal_log_density,
        factor.unscaled_reference_edge_log_density,
    ):
        digest.update(struct.pack(">d", value))
    for state in (
        proposal.source_configuration,
        proposal.destination_configuration,
    ):
        digest.update(bytes.fromhex(_configuration_sha256(state)))
    for value in (
        proposal.source_occurrence_index,
        factor.source_event_multiplicity,
    ):
        if value is None:
            digest.update(b"none\x00")
        else:
            digest.update(b"integer\x00")
            _framed_update(digest, str(value).encode("ascii"))
    for event in (proposal.source_event, proposal.destination_event):
        if event is None:
            digest.update(b"none-event\x00")
        else:
            digest.update(b"event\x00")
            digest.update(event.event_type.to_bytes(8, "big", signed=False))
            digest.update(len(event.coordinates).to_bytes(8, "big", signed=False))
            for coordinate in event.coordinates:
                digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _context_sha256(context: Tuple[float, ...], *, role: str) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-totalized-jump-potential-context-v1\x00")
    _framed_update(digest, role.encode("ascii"))
    digest.update(len(context).to_bytes(8, "big", signed=False))
    for value in context:
        digest.update(struct.pack(">d", value))
    return digest.hexdigest()


def _hash_tensor(digest: "hashlib._Hash", name: str, value: torch.Tensor) -> None:
    detached = value.detach().contiguous()
    for field in (
        name.encode("utf-8"),
        str(detached.dtype).encode("ascii"),
        repr(tuple(detached.shape)).encode("ascii"),
        detached.numpy().tobytes(order="C"),
    ):
        _framed_update(digest, field)


def _batch_sha256(batch: TypedConfigurationBatch, *, domain: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(batch.architecture_sha256.encode("ascii"))
    digest.update(batch.batch_size.to_bytes(8, "big", signed=False))
    digest.update(batch.total_occurrences.to_bytes(8, "big", signed=False))
    digest.update(batch.total_coordinates.to_bytes(8, "big", signed=False))
    _hash_tensor(digest, "forward_time", batch.forward_time)
    _hash_tensor(digest, "context", batch.context)
    for index, (event_type, coordinates, owners) in enumerate(
        zip(batch.type_ids, batch.coordinates, batch.batch_indices)
    ):
        digest.update(index.to_bytes(8, "big", signed=False))
        digest.update(event_type.to_bytes(8, "big", signed=False))
        _hash_tensor(digest, "coordinates[%d]" % index, coordinates)
        _hash_tensor(digest, "owners[%d]" % index, owners)
    return digest.hexdigest()


def _floating_point_environment_probe() -> Tuple[str, ...]:
    minimum_normal = struct.unpack(">d", bytes.fromhex("0010000000000000"))[0]
    half_minimum_normal = minimum_normal * 0.5
    minimum_subnormal = struct.unpack(">d", bytes.fromhex("0000000000000001"))[0]
    consumed_half = half_minimum_normal + half_minimum_normal
    consumed_subnormal = minimum_subnormal + minimum_subnormal
    with torch.no_grad():
        torch_half = torch.tensor(
            half_minimum_normal,
            dtype=torch.float64,
            device="cpu",
        )
        torch_consumed_half = float((torch_half + torch_half).item())
    one = struct.unpack(">d", bytes.fromhex("3ff0000000000000"))[0]
    positive_tie = one + math.ldexp(1.0, -53)
    negative_quarter_ulp = one - math.ldexp(1.0, -54)
    next_positive = math.nextafter(0.0, math.inf)
    return tuple(
        struct.pack(">d", value).hex()
        for value in (
            half_minimum_normal,
            consumed_half,
            consumed_subnormal,
            torch_consumed_half,
            positive_tie,
            negative_quarter_ulp,
            next_positive,
        )
    )


def _require_binary64_environment() -> Tuple[str, ...]:
    observed = _floating_point_environment_probe()
    expected = (
        "0008000000000000",
        "0010000000000000",
        "0000000000000002",
        "0010000000000000",
        "3ff0000000000000",
        "3ff0000000000000",
        "0000000000000001",
    )
    if observed != expected:
        raise ConfigurationTotalizedJumpPotentialError(
            "composition requires round-to-nearest-even binary64 arithmetic "
            "with gradual underflow"
        )
    return observed


def _runtime_sha256() -> str:
    return _semantic_digest(
        {
            "domain": "configuration-totalized-jump-potential-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "torch_version": str(torch.__version__),
            "schema_version": (CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCHEMA_VERSION),
            "floating_point_policy": (
                CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_FLOATING_POINT_POLICY
            ),
            "floating_point_probe": _require_binary64_environment(),
        }
    )


def _model_state_storage_intervals(
    model: BoundedConfigurationEnergy,
    *,
    name: str,
) -> Tuple[Tuple[str, int, int, int, str], ...]:
    result = []
    state_items = tuple(
        model.named_parameters(recurse=True, remove_duplicate=False)
    ) + tuple(model.named_buffers(recurse=True, remove_duplicate=False))
    for tensor_name, tensor in state_items:
        if type(tensor) is not torch.Tensor and not isinstance(
            tensor, torch.nn.Parameter
        ):
            raise TypeError("%s state contains a non-tensor value" % name)
        if tensor.numel() == 0:
            continue
        storage = tensor.untyped_storage()
        start = int(storage.data_ptr())
        byte_count = int(storage.nbytes())
        if start <= 0 or byte_count <= 0:
            raise RuntimeError("%s state has an invalid storage pointer" % name)
        end = start + byte_count
        if end <= start:
            raise RuntimeError("%s state has an invalid storage extent" % name)
        device_index = -1 if tensor.device.index is None else int(tensor.device.index)
        result.append((tensor.device.type, device_index, start, end, tensor_name))
    ordered = tuple(sorted(result))
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if right[:2] != left[:2]:
                if right[:2] > left[:2]:
                    break
                continue
            if right[2] >= left[3]:
                break
            raise ValueError(
                "%s internally aliases state storage between %s and %s"
                % (name, left[4], right[4])
            )
    return ordered


def _require_pairwise_disjoint_model_state_storage(
    models: Tuple[Tuple[str, BoundedConfigurationEnergy], ...]
) -> None:
    intervals = tuple(
        (name, model, _model_state_storage_intervals(model, name=name))
        for name, model in models
    )
    for index, (left_name, left_model, left_intervals) in enumerate(intervals):
        for right_name, right_model, right_intervals in intervals[index + 1 :]:
            if left_model is right_model:
                raise ValueError(
                    "%s and %s must be distinct model objects" % (left_name, right_name)
                )
            for left in left_intervals:
                for right in right_intervals:
                    if left[:2] != right[:2]:
                        continue
                    if left[2] < right[3] and right[2] < left[3]:
                        raise ValueError(
                            "%s and %s state storage overlaps between %s and %s"
                            % (left_name, right_name, left[4], right[4])
                        )


def _configuration_tensor_maps(
    architecture: object,
    configuration: TransformedConfiguration,
) -> Tuple[dict, dict]:
    coordinates = {}
    owners = {}
    for event_type, dimension in zip(
        architecture.type_ids,
        architecture.type_dimensions,
    ):
        events = tuple(
            event for event in configuration if event.event_type == event_type
        )
        if not events:
            continue
        if dimension == 0:
            coordinate_tensor = torch.empty(
                (len(events), 0), dtype=torch.float64, device="cpu"
            )
        else:
            coordinate_tensor = torch.tensor(
                [event.coordinates for event in events],
                dtype=torch.float64,
                device="cpu",
            )
        owner_tensor = torch.zeros((len(events),), dtype=torch.int64, device="cpu")
        coordinates[event_type] = coordinate_tensor
        owners[event_type] = owner_tensor
    return coordinates, owners


def _pack_configuration(
    architecture: object,
    configuration: TransformedConfiguration,
    *,
    direct_time: float,
    context: Tuple[float, ...],
) -> TypedConfigurationBatch:
    coordinates, owners = _configuration_tensor_maps(architecture, configuration)
    return pack_typed_configuration_batch(
        architecture,
        torch.tensor([direct_time], dtype=torch.float64, device="cpu"),
        torch.tensor([context], dtype=torch.float64, device="cpu").reshape(
            1, architecture.context_dimension
        ),
        coordinates,
        owners,
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: value for name, value in values.items() if name != "certificate_sha256"
    }


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpPotentialCompositionCertificate:
    """Transitive custody, target selection, bounds, and claim boundary."""

    schema_version: str
    certificate_scope: str
    target_policy: str
    composition_policy: str
    rounding_algorithm: str
    floating_point_environment_policy: str
    composition_role_sha256: str
    process_parameter_sha256: str
    reverse_time_horizon: float
    base_architecture_sha256: str
    base_context_schema_sha256: str
    base_context_dimension: int
    base_checkpoint_sha256: str
    base_certificate_sha256: str
    base_provenance_sha256: str
    base_runtime_sha256: str
    guide_preconditioner_sha256: str
    guide_outcome_sha256: str
    guide_totalized_certificate_sha256: str
    guide_analytic_range_certificate_sha256: str
    guide_range_gate_certificate_sha256: str
    guide_evaluator_runtime_sha256: str
    residual_totalized_certificate_sha256: str
    residual_contract_sha256: str
    residual_core_architecture_sha256: str
    residual_context_schema_sha256: str
    residual_context_dimension: int
    residual_observation_schema_sha256: str
    residual_task_schema_sha256: str
    residual_conditioning_adapter_sha256: str
    residual_role_sha256: str
    residual_core_checkpoint_sha256: str
    residual_core_certificate_sha256: str
    residual_certificate_sha256: str
    residual_provenance_sha256: str
    residual_runtime_sha256: str
    residual_evaluator_runtime_sha256: str
    composer_runtime_sha256: str
    base_point_magnitude_bound: float
    guide_operational_log_lower_bound: float
    guide_operational_log_upper_bound: float
    guide_point_magnitude_bound: float
    residual_point_magnitude_bound: float
    aggregate_point_magnitude_bound: float
    base_edge_magnitude_bound: float
    guide_edge_magnitude_bound: float
    guide_to_analytic_edit_discrepancy_bound: float
    residual_edge_magnitude_bound: float
    aggregate_edge_magnitude_bound: float
    maximum_exact_integer_bits: int
    operational_surrogate_target_selected: bool
    exact_operational_endpoint_coboundary: bool
    aggregate_rounded_once: bool
    component_rounded_edges_used: bool
    external_base_live_custody_authenticated: bool
    private_base_checkpoint_materialized: bool
    totalized_guide_required: bool
    totalized_residual_required: bool
    guide_successful_point_values_preserved: bool
    residual_successful_point_values_preserved: bool
    checkpoint14_combined_bits_preserved: bool
    conditioning_adapter_origin_authenticated: bool
    exact_analytic_target_preserved: bool
    exact_conditional_or_posterior_target: bool
    aggregate_analytic_target_discrepancy_certified: bool
    small_forward_error_certified: bool
    rounded_edge_cycle_closure_certified: bool
    full_composer_totality_certified: bool
    rate_space_envelope_certified: bool
    controlled_total_exit_certified: bool
    waiting_time_admissible: bool
    acceptance_decision_admissible: bool
    coordinate_derivatives_admissible: bool
    continuous_drift_admissible: bool
    randomness_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    operational_sampler_admissible: bool
    runtime_portable: bool
    blas_identity_authenticated: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "TotalizedJumpPotentialCompositionCertificate cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("composition certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("composition certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    @property
    def jump_only(self) -> bool:
        return True

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "configuration-totalized-jump-potential-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("composition certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(TotalizedJumpPotentialCompositionCertificate.__annotations__)


def _validate_certificate(
    certificate: object,
) -> TotalizedJumpPotentialCompositionCertificate:
    if type(certificate) is not TotalizedJumpPotentialCompositionCertificate:
        raise TypeError(
            "certificate must be an exact "
            "TotalizedJumpPotentialCompositionCertificate"
        )
    for name in (
        "composition_role_sha256",
        "process_parameter_sha256",
        "base_architecture_sha256",
        "base_context_schema_sha256",
        "base_checkpoint_sha256",
        "base_certificate_sha256",
        "base_provenance_sha256",
        "base_runtime_sha256",
        "guide_preconditioner_sha256",
        "guide_outcome_sha256",
        "guide_totalized_certificate_sha256",
        "guide_analytic_range_certificate_sha256",
        "guide_range_gate_certificate_sha256",
        "guide_evaluator_runtime_sha256",
        "residual_totalized_certificate_sha256",
        "residual_contract_sha256",
        "residual_core_architecture_sha256",
        "residual_context_schema_sha256",
        "residual_observation_schema_sha256",
        "residual_task_schema_sha256",
        "residual_conditioning_adapter_sha256",
        "residual_role_sha256",
        "residual_core_checkpoint_sha256",
        "residual_core_certificate_sha256",
        "residual_certificate_sha256",
        "residual_provenance_sha256",
        "residual_runtime_sha256",
        "residual_evaluator_runtime_sha256",
        "composer_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    expected_text = {
        "schema_version": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCOPE,
        "target_policy": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "composition_policy": (
            CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_COMPOSITION_POLICY
        ),
        "rounding_algorithm": (
            CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_ROUNDING_ALGORITHM
        ),
        "floating_point_environment_policy": (
            CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_FLOATING_POINT_POLICY
        ),
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("composition certificate %s is inconsistent" % name)
    for name in ("base_context_dimension", "residual_context_dimension"):
        value = getattr(certificate, name)
        if (
            type(value) is not int
            or isinstance(value, bool)
            or not 0 <= value <= _MAX_CONTEXT_DIMENSION
        ):
            raise ValueError("certificate.%s is outside the adapter limit" % name)
    if (
        type(certificate.maximum_exact_integer_bits) is not int
        or isinstance(certificate.maximum_exact_integer_bits, bool)
        or certificate.maximum_exact_integer_bits
        != MAX_TOTALIZED_JUMP_POTENTIAL_EXACT_INTEGER_BITS
    ):
        raise ValueError("certificate exact-integer limit is inconsistent")
    _validated_float(
        certificate.reverse_time_horizon,
        name="certificate.reverse_time_horizon",
        strictly_positive=True,
    )
    for name in (
        "base_point_magnitude_bound",
        "guide_point_magnitude_bound",
        "residual_point_magnitude_bound",
        "aggregate_point_magnitude_bound",
        "base_edge_magnitude_bound",
        "guide_edge_magnitude_bound",
        "guide_to_analytic_edit_discrepancy_bound",
        "residual_edge_magnitude_bound",
        "aggregate_edge_magnitude_bound",
    ):
        _validated_float(
            getattr(certificate, name),
            name="certificate.%s" % name,
            nonnegative=True,
        )
    lower = _validated_float(
        certificate.guide_operational_log_lower_bound,
        name="certificate.guide_operational_log_lower_bound",
    )
    upper = _validated_float(
        certificate.guide_operational_log_upper_bound,
        name="certificate.guide_operational_log_upper_bound",
    )
    if lower > upper:
        raise ValueError("certificate guide interval is empty")
    expected_guide_point = max(abs(lower), abs(upper))
    if not _same_float(certificate.guide_point_magnitude_bound, expected_guide_point):
        raise ValueError("certificate guide point bound is inconsistent")
    expected_point = _outward_sum(
        (
            certificate.base_point_magnitude_bound,
            certificate.guide_point_magnitude_bound,
            certificate.residual_point_magnitude_bound,
        ),
        name="aggregate operational point bound",
    )
    expected_edge = _outward_sum(
        (
            certificate.base_edge_magnitude_bound,
            certificate.guide_edge_magnitude_bound,
            certificate.residual_edge_magnitude_bound,
        ),
        name="aggregate operational edge bound",
    )
    if not _same_float(certificate.aggregate_point_magnitude_bound, expected_point):
        raise ValueError("certificate aggregate point bound is inconsistent")
    if not _same_float(certificate.aggregate_edge_magnitude_bound, expected_edge):
        raise ValueError("certificate aggregate edge bound is inconsistent")
    true_flags = (
        "operational_surrogate_target_selected",
        "exact_operational_endpoint_coboundary",
        "aggregate_rounded_once",
        "external_base_live_custody_authenticated",
        "private_base_checkpoint_materialized",
        "totalized_guide_required",
        "totalized_residual_required",
        "guide_successful_point_values_preserved",
        "residual_successful_point_values_preserved",
        "passed",
    )
    false_flags = (
        "component_rounded_edges_used",
        "checkpoint14_combined_bits_preserved",
        "conditioning_adapter_origin_authenticated",
        "exact_analytic_target_preserved",
        "exact_conditional_or_posterior_target",
        "aggregate_analytic_target_discrepancy_certified",
        "small_forward_error_certified",
        "rounded_edge_cycle_closure_certified",
        "full_composer_totality_certified",
        "rate_space_envelope_certified",
        "controlled_total_exit_certified",
        "waiting_time_admissible",
        "acceptance_decision_admissible",
        "coordinate_derivatives_admissible",
        "continuous_drift_admissible",
        "randomness_admissible",
        "initializer_admissible",
        "path_admissible",
        "operational_sampler_admissible",
        "runtime_portable",
        "blas_identity_authenticated",
    )
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("composition positive claim flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("composition negative claim flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    if certificate.certificate_sha256 != _semantic_digest(_certificate_payload(values)):
        raise ValueError("composition certificate digest is inconsistent")
    return certificate


def _make_certificate(
    *,
    reference_composer: ProcessValidReferenceJumpComposer,
    base_checkpoint: CertifiedConfigurationEnergyCheckpoint,
    base_certificate: ConfigurationEnergyCheckpointCertificate,
    guide_certificate: TotalizedJumpGuideCertificate,
    residual_certificate: TotalizedResidualJumpCertificate,
    residual_context_dimension: int,
    composition_role_sha256: str,
) -> TotalizedJumpPotentialCompositionCertificate:
    architecture = base_checkpoint.snapshot.architecture
    guide_lower = guide_certificate.operational_log_lower_bound
    guide_upper = guide_certificate.operational_log_upper_bound
    guide_point = max(abs(guide_lower), abs(guide_upper))
    process_sha256 = _plain_key_sha256(
        reference_composer.process_parameter_key,
        domain=b"heterodiff-totalized-jump-potential-process-v1\x00",
    )
    values: Dict[str, object] = {
        "schema_version": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCOPE,
        "target_policy": CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "composition_policy": (
            CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_COMPOSITION_POLICY
        ),
        "rounding_algorithm": (
            CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_ROUNDING_ALGORITHM
        ),
        "floating_point_environment_policy": (
            CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_FLOATING_POINT_POLICY
        ),
        "composition_role_sha256": composition_role_sha256,
        "process_parameter_sha256": process_sha256,
        "reverse_time_horizon": reference_composer.process.schedule.horizon,
        "base_architecture_sha256": architecture.architecture_sha256,
        "base_context_schema_sha256": architecture.context_schema_sha256,
        "base_context_dimension": architecture.context_dimension,
        "base_checkpoint_sha256": base_certificate.checkpoint_sha256,
        "base_certificate_sha256": base_certificate.certificate_sha256,
        "base_provenance_sha256": base_certificate.provenance_sha256,
        "base_runtime_sha256": base_certificate.runtime_sha256,
        "guide_preconditioner_sha256": _plain_key_sha256(
            guide_certificate.preconditioner_parameter_key,
            domain=(b"heterodiff-totalized-jump-potential-guide-preconditioner-v1\x00"),
        ),
        "guide_outcome_sha256": _plain_key_sha256(
            guide_certificate.outcome_key,
            domain=b"heterodiff-totalized-jump-potential-guide-outcome-v1\x00",
        ),
        "guide_totalized_certificate_sha256": (guide_certificate.certificate_sha256),
        "guide_analytic_range_certificate_sha256": (
            guide_certificate.analytic_range_certificate_sha256
        ),
        "guide_range_gate_certificate_sha256": (
            guide_certificate.range_gate_certificate_sha256
        ),
        "guide_evaluator_runtime_sha256": (guide_certificate.evaluator_runtime_sha256),
        "residual_totalized_certificate_sha256": (
            residual_certificate.certificate_sha256
        ),
        "residual_contract_sha256": residual_certificate.residual_contract_sha256,
        "residual_core_architecture_sha256": (
            residual_certificate.core_architecture_sha256
        ),
        "residual_context_schema_sha256": (residual_certificate.context_schema_sha256),
        "residual_context_dimension": residual_context_dimension,
        "residual_observation_schema_sha256": (
            residual_certificate.observation_schema_sha256
        ),
        "residual_task_schema_sha256": residual_certificate.task_schema_sha256,
        "residual_conditioning_adapter_sha256": (
            residual_certificate.conditioning_adapter_sha256
        ),
        "residual_role_sha256": residual_certificate.residual_role_sha256,
        "residual_core_checkpoint_sha256": (
            residual_certificate.core_checkpoint_sha256
        ),
        "residual_core_certificate_sha256": (
            residual_certificate.core_certificate_sha256
        ),
        "residual_certificate_sha256": (
            residual_certificate.residual_certificate_sha256
        ),
        "residual_provenance_sha256": (residual_certificate.residual_provenance_sha256),
        "residual_runtime_sha256": residual_certificate.residual_runtime_sha256,
        "residual_evaluator_runtime_sha256": (
            residual_certificate.evaluator_runtime_sha256
        ),
        "composer_runtime_sha256": _runtime_sha256(),
        "base_point_magnitude_bound": base_certificate.value_bound,
        "guide_operational_log_lower_bound": guide_lower,
        "guide_operational_log_upper_bound": guide_upper,
        "guide_point_magnitude_bound": guide_point,
        "residual_point_magnitude_bound": (
            residual_certificate.global_point_magnitude_bound
        ),
        "aggregate_point_magnitude_bound": _outward_sum(
            (
                base_certificate.value_bound,
                guide_point,
                residual_certificate.global_point_magnitude_bound,
            ),
            name="aggregate operational point bound",
        ),
        "base_edge_magnitude_bound": base_certificate.edge_difference_bound,
        "guide_edge_magnitude_bound": (
            guide_certificate.represented_edit_log_magnitude_bound
        ),
        "guide_to_analytic_edit_discrepancy_bound": (
            guide_certificate.represented_to_exact_edit_log_discrepancy_bound
        ),
        "residual_edge_magnitude_bound": (
            residual_certificate.global_edge_magnitude_bound
        ),
        "aggregate_edge_magnitude_bound": _outward_sum(
            (
                base_certificate.edge_difference_bound,
                guide_certificate.represented_edit_log_magnitude_bound,
                residual_certificate.global_edge_magnitude_bound,
            ),
            name="aggregate operational edge bound",
        ),
        "maximum_exact_integer_bits": (MAX_TOTALIZED_JUMP_POTENTIAL_EXACT_INTEGER_BITS),
        "operational_surrogate_target_selected": True,
        "exact_operational_endpoint_coboundary": True,
        "aggregate_rounded_once": True,
        "component_rounded_edges_used": False,
        "external_base_live_custody_authenticated": True,
        "private_base_checkpoint_materialized": True,
        "totalized_guide_required": True,
        "totalized_residual_required": True,
        "guide_successful_point_values_preserved": True,
        "residual_successful_point_values_preserved": True,
        "checkpoint14_combined_bits_preserved": False,
        "conditioning_adapter_origin_authenticated": False,
        "exact_analytic_target_preserved": False,
        "exact_conditional_or_posterior_target": False,
        "aggregate_analytic_target_discrepancy_certified": False,
        "small_forward_error_certified": False,
        "rounded_edge_cycle_closure_certified": False,
        "full_composer_totality_certified": False,
        "rate_space_envelope_certified": False,
        "controlled_total_exit_certified": False,
        "waiting_time_admissible": False,
        "acceptance_decision_admissible": False,
        "coordinate_derivatives_admissible": False,
        "continuous_drift_admissible": False,
        "randomness_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "operational_sampler_admissible": False,
        "runtime_portable": False,
        "blas_identity_authenticated": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return TotalizedJumpPotentialCompositionCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _evaluation_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "evaluation_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class TotalizedJumpPotentialCandidateEvaluation:
    """Primitive, replayable record for one exact operational coboundary."""

    certificate: TotalizedJumpPotentialCompositionCertificate
    certificate_sha256: str
    candidate_sha256: str
    candidate_process_sha256: str
    reverse_time: float
    direct_time: float
    reference_schedule_rate: float
    scheduled_reference_exit_rate: float
    edit_kind: str
    source_state_sha256: str
    destination_state_sha256: str
    base_context: Tuple[float, ...]
    base_context_sha256: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    base_source_batch_sha256: str
    base_destination_batch_sha256: str
    base_source_operational_energy: float
    base_destination_operational_energy: float
    base_exact_endpoint_difference_numerator: int
    base_exact_endpoint_difference_denominator: int
    base_operational_difference: float
    base_exact_rounding_error_numerator: int
    base_exact_rounding_error_denominator: int
    base_rounding_error_upper_bound: float
    guide_edit_sha256: str
    guide_source_evaluation_sha256: str
    guide_destination_evaluation_sha256: str
    guide_source_branch: str
    guide_destination_branch: str
    guide_source_operational_log_density: float
    guide_destination_operational_log_density: float
    guide_exact_endpoint_difference_numerator: int
    guide_exact_endpoint_difference_denominator: int
    guide_operational_difference: float
    guide_to_analytic_edit_discrepancy_bound: float
    residual_difference_sha256: str
    residual_source_batch_sha256: str
    residual_destination_batch_sha256: str
    residual_source_evaluation_sha256: str
    residual_destination_evaluation_sha256: str
    residual_source_branch: str
    residual_destination_branch: str
    residual_source_operational_value: float
    residual_destination_operational_value: float
    residual_exact_endpoint_difference_numerator: int
    residual_exact_endpoint_difference_denominator: int
    residual_operational_difference: float
    residual_exact_rounding_error_numerator: int
    residual_exact_rounding_error_denominator: int
    residual_rounding_error_upper_bound: float
    guide_fallback_used: bool
    residual_fallback_used: bool
    exact_source_target_value_numerator: int
    exact_source_target_value_denominator: int
    exact_destination_target_value_numerator: int
    exact_destination_target_value_denominator: int
    exact_operational_endpoint_difference_numerator: int
    exact_operational_endpoint_difference_denominator: int
    combined_log_increment: float
    exact_rounding_error_numerator: int
    exact_rounding_error_denominator: int
    rounding_error_upper_bound: float
    base_edge_magnitude_bound: float
    guide_edge_magnitude_bound: float
    residual_edge_magnitude_bound: float
    aggregate_point_magnitude_bound: float
    aggregate_edge_magnitude_bound: float
    target_policy: str
    composition_policy: str
    rounding_algorithm: str
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "TotalizedJumpPotentialCandidateEvaluation cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError("composition evaluations are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("composition evaluation fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("evaluation certificate digest is inconsistent")
        for name in (
            "certificate_sha256",
            "candidate_sha256",
            "candidate_process_sha256",
            "source_state_sha256",
            "destination_state_sha256",
            "base_context_sha256",
            "residual_context_sha256",
            "base_source_batch_sha256",
            "base_destination_batch_sha256",
            "guide_edit_sha256",
            "guide_source_evaluation_sha256",
            "guide_destination_evaluation_sha256",
            "residual_difference_sha256",
            "residual_source_batch_sha256",
            "residual_destination_batch_sha256",
            "residual_source_evaluation_sha256",
            "residual_destination_evaluation_sha256",
            "evaluation_sha256",
        ):
            _require_sha256(values[name], name="evaluation.%s" % name)
        if values["candidate_process_sha256"] != (certificate.process_parameter_sha256):
            raise ValueError("candidate process digest differs from certificate")
        reverse_time = _validated_float(
            values["reverse_time"],
            name="evaluation.reverse_time",
            nonnegative=True,
            canonical_zero=True,
        )
        direct_time = _validated_float(
            values["direct_time"],
            name="evaluation.direct_time",
            nonnegative=True,
            canonical_zero=True,
        )
        if reverse_time > certificate.reverse_time_horizon:
            raise ValueError("evaluation reverse time exceeds the horizon")
        expected_direct = _canonical_zero(
            certificate.reverse_time_horizon - reverse_time
        )
        if not _same_float(direct_time, expected_direct):
            raise ValueError("evaluation direct time is not S minus reverse time")
        for name in ("reference_schedule_rate", "scheduled_reference_exit_rate"):
            _validated_float(
                values[name],
                name="evaluation.%s" % name,
                strictly_positive=True,
            )
        if values["edit_kind"] not in ("birth", "death", "replacement"):
            raise ValueError("evaluation edit kind is unknown")
        for context_name, dimension in (
            ("base_context", certificate.base_context_dimension),
            ("residual_context", certificate.residual_context_dimension),
        ):
            if type(values[context_name]) is not tuple:
                raise TypeError("evaluation %s must be an exact tuple" % context_name)
            context = _validated_context(
                values[context_name],
                dimension=dimension,
                name="evaluation.%s" % context_name,
            )
            if context is not values[context_name] and context != values[context_name]:
                raise ValueError("evaluation %s is not canonical" % context_name)
            expected_sha = _context_sha256(
                context,
                role="base" if context_name == "base_context" else "residual",
            )
            if values[context_name + "_sha256"] != expected_sha:
                raise ValueError("evaluation %s digest is inconsistent" % context_name)
        float_fields = (
            "base_source_operational_energy",
            "base_destination_operational_energy",
            "base_operational_difference",
            "base_rounding_error_upper_bound",
            "guide_source_operational_log_density",
            "guide_destination_operational_log_density",
            "guide_operational_difference",
            "guide_to_analytic_edit_discrepancy_bound",
            "residual_source_operational_value",
            "residual_destination_operational_value",
            "residual_operational_difference",
            "residual_rounding_error_upper_bound",
            "combined_log_increment",
            "rounding_error_upper_bound",
            "base_edge_magnitude_bound",
            "guide_edge_magnitude_bound",
            "residual_edge_magnitude_bound",
            "aggregate_point_magnitude_bound",
            "aggregate_edge_magnitude_bound",
        )
        nonnegative_fields = {
            "base_rounding_error_upper_bound",
            "guide_to_analytic_edit_discrepancy_bound",
            "residual_rounding_error_upper_bound",
            "rounding_error_upper_bound",
            "base_edge_magnitude_bound",
            "guide_edge_magnitude_bound",
            "residual_edge_magnitude_bound",
            "aggregate_point_magnitude_bound",
            "aggregate_edge_magnitude_bound",
        }
        for name in float_fields:
            _validated_float(
                values[name],
                name="evaluation.%s" % name,
                nonnegative=name in nonnegative_fields,
                canonical_zero=name == "combined_log_increment",
            )
        if (
            values["guide_source_branch"] not in _GUIDE_BRANCHES
            or values["guide_destination_branch"] not in _GUIDE_BRANCHES
        ):
            raise ValueError("evaluation contains an unknown guide branch")
        if (
            values["residual_source_branch"] not in _RESIDUAL_BRANCHES
            or values["residual_destination_branch"] not in _RESIDUAL_BRANCHES
        ):
            raise ValueError("evaluation contains an unknown residual branch")
        if values["residual_source_branch"] != values["residual_destination_branch"]:
            raise ValueError("same-time residual endpoints use different branches")
        expected_guide_fallback = (
            values["guide_source_branch"] != PRESERVED_RANGE_GATED_BRANCH
            or values["guide_destination_branch"] != PRESERVED_RANGE_GATED_BRANCH
        )
        expected_residual_fallback = (
            values["residual_source_branch"] == EXACT_GATE_RESCALED_CORE_BRANCH
        )
        for name, expected in (
            ("guide_fallback_used", expected_guide_fallback),
            ("residual_fallback_used", expected_residual_fallback),
        ):
            if type(values[name]) is not bool or values[name] is not expected:
                raise ValueError("evaluation %s is inconsistent" % name)
        fractions = {}
        for prefix in (
            "base_exact_endpoint_difference",
            "base_exact_rounding_error",
            "guide_exact_endpoint_difference",
            "residual_exact_endpoint_difference",
            "residual_exact_rounding_error",
            "exact_source_target_value",
            "exact_destination_target_value",
            "exact_operational_endpoint_difference",
            "exact_rounding_error",
        ):
            fractions[prefix] = _validated_fraction_parts(
                values[prefix + "_numerator"],
                values[prefix + "_denominator"],
                name="evaluation.%s" % prefix,
            )
        expected_base = _fraction(
            values["base_destination_operational_energy"]
        ) - _fraction(values["base_source_operational_energy"])
        expected_guide = _fraction(
            values["guide_destination_operational_log_density"]
        ) - _fraction(values["guide_source_operational_log_density"])
        expected_residual = _fraction(
            values["residual_destination_operational_value"]
        ) - _fraction(values["residual_source_operational_value"])
        if fractions["base_exact_endpoint_difference"] != expected_base:
            raise ValueError("evaluation base endpoint difference is inconsistent")
        if fractions["guide_exact_endpoint_difference"] != expected_guide:
            raise ValueError("evaluation guide endpoint difference is inconsistent")
        if fractions["residual_exact_endpoint_difference"] != expected_residual:
            raise ValueError("evaluation residual endpoint difference is inconsistent")
        expected_base_rounded = _round_fraction_once(
            expected_base, name="base operational endpoint difference"
        )
        if not _same_float(
            values["base_operational_difference"], expected_base_rounded
        ):
            raise ValueError("evaluation base rounded difference is inconsistent")
        expected_base_error = abs(_fraction(expected_base_rounded) - expected_base)
        if fractions["base_exact_rounding_error"] != expected_base_error:
            raise ValueError("evaluation base rounding error is inconsistent")
        expected_base_upper = _outward_nonnegative_fraction(
            expected_base_error, name="base endpoint rounding error"
        )
        if not _same_float(
            values["base_rounding_error_upper_bound"], expected_base_upper
        ):
            raise ValueError("evaluation base rounding-error bound is inconsistent")
        for value_name, expected in (
            ("guide_operational_difference", expected_guide),
            ("residual_operational_difference", expected_residual),
        ):
            rounded = _round_fraction_once(expected, name=value_name)
            if not _same_float(values[value_name], rounded):
                raise ValueError("evaluation %s is inconsistent" % value_name)
        expected_residual_error = abs(
            _fraction(values["residual_operational_difference"]) - expected_residual
        )
        if fractions["residual_exact_rounding_error"] != expected_residual_error:
            raise ValueError("evaluation residual rounding error is inconsistent")
        expected_residual_upper = _outward_nonnegative_fraction(
            expected_residual_error, name="residual endpoint rounding error"
        )
        if not _same_float(
            values["residual_rounding_error_upper_bound"],
            expected_residual_upper,
        ):
            raise ValueError("evaluation residual rounding-error bound is inconsistent")
        expected_source_target = _require_fraction_size(
            _fraction(values["base_source_operational_energy"])
            + _fraction(values["guide_source_operational_log_density"])
            + _fraction(values["residual_source_operational_value"]),
            name="exact source operational target",
        )
        expected_destination_target = _require_fraction_size(
            _fraction(values["base_destination_operational_energy"])
            + _fraction(values["guide_destination_operational_log_density"])
            + _fraction(values["residual_destination_operational_value"]),
            name="exact destination operational target",
        )
        if fractions["exact_source_target_value"] != expected_source_target:
            raise ValueError("evaluation exact source target is inconsistent")
        if fractions["exact_destination_target_value"] != expected_destination_target:
            raise ValueError("evaluation exact destination target is inconsistent")
        expected_combined = _require_fraction_size(
            expected_destination_target - expected_source_target,
            name="exact combined operational endpoint difference",
        )
        component_sum = _require_fraction_size(
            expected_base + expected_guide + expected_residual,
            name="exact component endpoint-difference sum",
        )
        if expected_combined != component_sum:
            raise ValueError("exact endpoint and component sums differ")
        if fractions["exact_operational_endpoint_difference"] != expected_combined:
            raise ValueError("evaluation exact combined difference is inconsistent")
        expected_combined_rounded = _round_fraction_once(
            expected_combined, name="combined operational endpoint difference"
        )
        if not _same_float(values["combined_log_increment"], expected_combined_rounded):
            raise ValueError("evaluation combined rounding is inconsistent")
        expected_rounding_error = abs(
            _fraction(expected_combined_rounded) - expected_combined
        )
        if fractions["exact_rounding_error"] != expected_rounding_error:
            raise ValueError("evaluation aggregate rounding error is inconsistent")
        expected_rounding_upper = _outward_nonnegative_fraction(
            expected_rounding_error, name="aggregate endpoint rounding error"
        )
        if not _same_float(
            values["rounding_error_upper_bound"], expected_rounding_upper
        ):
            raise ValueError("evaluation aggregate rounding bound is inconsistent")
        for name in (
            "base_edge_magnitude_bound",
            "guide_edge_magnitude_bound",
            "residual_edge_magnitude_bound",
            "aggregate_point_magnitude_bound",
            "aggregate_edge_magnitude_bound",
        ):
            if not _same_float(values[name], getattr(certificate, name)):
                raise ValueError("evaluation %s differs from certificate" % name)
        if values["guide_to_analytic_edit_discrepancy_bound"] > (
            certificate.guide_to_analytic_edit_discrepancy_bound
        ):
            raise ValueError("evaluation guide discrepancy exceeds its certificate")
        for exact, bound, name in (
            (
                expected_base,
                certificate.base_edge_magnitude_bound,
                "base endpoint difference",
            ),
            (
                expected_guide,
                certificate.guide_edge_magnitude_bound,
                "guide endpoint difference",
            ),
            (
                expected_residual,
                certificate.residual_edge_magnitude_bound,
                "residual endpoint difference",
            ),
            (
                expected_combined,
                certificate.aggregate_edge_magnitude_bound,
                "aggregate endpoint difference",
            ),
        ):
            if abs(exact) > _fraction(bound):
                raise ValueError("evaluation %s exceeds its bound" % name)
        if abs(values["combined_log_increment"]) > (
            certificate.aggregate_edge_magnitude_bound
        ):
            raise ValueError("evaluation rounded aggregate exceeds its bound")
        for point, bound, name in (
            (
                values["base_source_operational_energy"],
                certificate.base_point_magnitude_bound,
                "base source",
            ),
            (
                values["base_destination_operational_energy"],
                certificate.base_point_magnitude_bound,
                "base destination",
            ),
            (
                values["residual_source_operational_value"],
                certificate.residual_point_magnitude_bound,
                "residual source",
            ),
            (
                values["residual_destination_operational_value"],
                certificate.residual_point_magnitude_bound,
                "residual destination",
            ),
        ):
            if abs(point) > bound:
                raise ValueError("evaluation %s point exceeds its bound" % name)
        for name in (
            "guide_source_operational_log_density",
            "guide_destination_operational_log_density",
        ):
            if not (
                certificate.guide_operational_log_lower_bound
                <= values[name]
                <= certificate.guide_operational_log_upper_bound
            ):
                raise ValueError("evaluation guide point lies outside its interval")
        for target_name in (
            "exact_source_target_value",
            "exact_destination_target_value",
        ):
            if abs(fractions[target_name]) > _fraction(
                certificate.aggregate_point_magnitude_bound
            ):
                raise ValueError("evaluation aggregate point exceeds its bound")
        expected_text = {
            "target_policy": certificate.target_policy,
            "composition_policy": certificate.composition_policy,
            "rounding_algorithm": certificate.rounding_algorithm,
        }
        for name, expected in expected_text.items():
            if values[name] != expected:
                raise ValueError("evaluation %s is inconsistent" % name)
        expected_digest = _semantic_digest(_evaluation_payload(values))
        if values["evaluation_sha256"] != expected_digest:
            raise ValueError("evaluation digest is inconsistent")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    @property
    def jump_only(self) -> bool:
        return True

    @property
    def exact_operational_coboundary(self) -> bool:
        return True

    @property
    def rounded_edge_cycle_closure_certified(self) -> bool:
        return False

    @property
    def exact_conditional_or_posterior_target(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("composition evaluations are not pickle objects")


def _evaluation_fields() -> Tuple[str, ...]:
    return tuple(TotalizedJumpPotentialCandidateEvaluation.__annotations__)


class TotalizedConfigurationJumpPotentialComposer:
    """Immutable owner of one checkpoint-defined operational point target."""

    __slots__ = (
        "_reference_composer",
        "_base_model",
        "_base_checkpoint",
        "_base_provenance",
        "_base_evaluation_model",
        "_guide",
        "_residual",
        "_composition_role_sha256",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "TotalizedConfigurationJumpPotentialComposer cannot be subclassed"
        )

    def __init__(
        self,
        *,
        reference_composer: ProcessValidReferenceJumpComposer,
        base_model: BoundedConfigurationEnergy,
        base_checkpoint: CertifiedConfigurationEnergyCheckpoint,
        base_provenance: ConfigurationEnergyProvenance,
        base_evaluation_model: BoundedConfigurationEnergy,
        guide: TotalizedAssociationJumpGuide,
        residual: TotalizedConditionalJumpResidual,
        composition_role_sha256: str,
        certificate: TotalizedJumpPotentialCompositionCertificate,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _COMPOSER_TOKEN:
            raise TypeError("composition owners require certification")
        role = _require_sha256(
            composition_role_sha256,
            name="composition_role_sha256",
        )
        if certificate.composition_role_sha256 != role:
            raise ValueError("composition certificate has a different role")
        object.__setattr__(self, "_reference_composer", reference_composer)
        object.__setattr__(self, "_base_model", base_model)
        object.__setattr__(self, "_base_checkpoint", base_checkpoint)
        object.__setattr__(self, "_base_provenance", base_provenance)
        object.__setattr__(self, "_base_evaluation_model", base_evaluation_model)
        object.__setattr__(self, "_guide", guide)
        object.__setattr__(self, "_residual", residual)
        object.__setattr__(self, "_composition_role_sha256", role)
        object.__setattr__(self, "_certificate", _validate_certificate(certificate))

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("TotalizedConfigurationJumpPotentialComposer is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("TotalizedConfigurationJumpPotentialComposer is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("composition owners are not pickle objects")

    @property
    def certificate(self) -> TotalizedJumpPotentialCompositionCertificate:
        return self._certificate

    @property
    def reference_composer(self) -> ProcessValidReferenceJumpComposer:
        return self._reference_composer

    @property
    def totalized_guide(self) -> TotalizedAssociationJumpGuide:
        return self._guide

    @property
    def totalized_residual(self) -> TotalizedConditionalJumpResidual:
        return self._residual

    def _live_components(
        self,
    ) -> Tuple[
        ConfigurationEnergyCheckpointCertificate,
        TotalizedJumpGuideCertificate,
        TotalizedResidualJumpCertificate,
    ]:
        if type(self._reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference composer has the wrong exact type")
        self._reference_composer._require_live_binding()
        if type(self._base_checkpoint) is not CertifiedConfigurationEnergyCheckpoint:
            raise TypeError("base checkpoint has the wrong exact type")
        if type(self._base_model) is not BoundedConfigurationEnergy:
            raise TypeError("external base model has the wrong exact type")
        if type(self._base_provenance) is not ConfigurationEnergyProvenance:
            raise TypeError("base provenance has the wrong exact type")
        if type(self._base_evaluation_model) is not BoundedConfigurationEnergy:
            raise TypeError("private base model has the wrong exact type")
        if type(self._guide) is not TotalizedAssociationJumpGuide:
            raise TypeError("totalized guide has the wrong exact type")
        if type(self._residual) is not TotalizedConditionalJumpResidual:
            raise TypeError("totalized residual has the wrong exact type")
        external_base = require_matching_configuration_energy_certificate(
            self._base_model,
            self._base_checkpoint,
            expected_provenance=self._base_provenance,
        )
        private_base = require_matching_configuration_energy_certificate(
            self._base_evaluation_model,
            self._base_checkpoint,
            expected_provenance=self._base_provenance,
        )
        checked_guide = require_matching_totalized_association_jump_guide(
            self._guide.preconditioner,
            self._guide,
            self._guide.range_gate,
            self._guide.range_certificate,
            observation=self._guide.outcome,
        )
        checked_residual = require_matching_totalized_conditional_jump_residual(
            self._residual.model,
            self._residual,
            self._residual.checkpoint,
            expected_provenance=self._residual.provenance,
        )
        residual_private = getattr(self._residual, "_evaluation_model", None)
        if type(residual_private) is not BoundedConfigurationEnergy:
            raise TypeError("private residual model has the wrong exact type")
        _require_pairwise_disjoint_model_state_storage(
            (
                ("private base model", self._base_evaluation_model),
                ("external base model", self._base_model),
                ("external residual model", self._residual.model),
                ("private residual model", residual_private),
            )
        )
        reference_key = self._reference_composer.process_parameter_key
        expected_process_sha = _plain_key_sha256(
            reference_key,
            domain=b"heterodiff-totalized-jump-potential-process-v1\x00",
        )
        for name, key in (
            (
                "base",
                self._base_model.architecture.process_parameter_key,
            ),
            ("guide", self._guide.preconditioner.process.parameter_key()),
            ("residual", self._residual.model.architecture.process_parameter_key),
        ):
            digest = _plain_key_sha256(
                key,
                domain=b"heterodiff-totalized-jump-potential-process-v1\x00",
            )
            if digest != expected_process_sha:
                raise ValueError("%s component belongs to a different process" % name)
        if external_base.certificate_sha256 != private_base.certificate_sha256:
            raise ValueError("external and private base certificates differ")
        if external_base.process_parameter_sha256 != (
            checked_residual.certificate.process_parameter_sha256
        ):
            raise ValueError("base and residual process certificate digests differ")
        if checked_guide.certificate.state_cap != (
            self._reference_composer.process.reference.total_cap
        ):
            raise ValueError("guide state cap differs from the process cap")
        horizon = self._reference_composer.process.schedule.horizon
        if not _same_float(
            checked_guide.certificate.reverse_time_horizon, horizon
        ) or not _same_float(checked_residual.certificate.schedule_horizon, horizon):
            raise ValueError("component horizons differ from the process horizon")
        current_runtime = _runtime_sha256()
        if current_runtime != self.certificate.composer_runtime_sha256:
            raise ValueError("live composer runtime differs from its certificate")
        expected = _make_certificate(
            reference_composer=self._reference_composer,
            base_checkpoint=self._base_checkpoint,
            base_certificate=external_base,
            guide_certificate=checked_guide.certificate,
            residual_certificate=checked_residual.certificate,
            residual_context_dimension=(
                self._residual.model.architecture.context_dimension
            ),
            composition_role_sha256=self._composition_role_sha256,
        )
        for name in _certificate_fields():
            supplied = getattr(self.certificate, name)
            recomputed = getattr(expected, name)
            if type(supplied) is float and type(recomputed) is float:
                matches = _same_float(supplied, recomputed)
            else:
                matches = supplied == recomputed
            if not matches:
                raise ValueError(
                    "composition certificate field %s differs from live state" % name
                )
        return (
            external_base,
            checked_guide.certificate,
            checked_residual.certificate,
        )

    def _snapshot_candidate(
        self,
        candidate: ProcessValidReferenceJump,
    ) -> Mapping[str, object]:
        checked = self.reference_composer.validate_candidate(candidate)
        before_candidate_sha = _candidate_sha256(checked)
        before_source_sha = _configuration_sha256(checked.source_configuration)
        before_destination_sha = _configuration_sha256(
            checked.destination_configuration
        )
        source = _copy_configuration(checked.source_configuration)
        destination = _copy_configuration(checked.destination_configuration)
        values: Dict[str, object] = {
            "candidate_sha256": before_candidate_sha,
            "reverse_time": float(checked.reverse_time),
            "direct_time": float(checked.direct_time),
            "reference_schedule_rate": float(checked.reference_schedule_rate),
            "scheduled_reference_exit_rate": float(
                checked.scheduled_reference_exit_rate
            ),
            "edit_kind": checked.kind.value,
            "source": source,
            "destination": destination,
            "source_state_sha256": _configuration_sha256(source),
            "destination_state_sha256": _configuration_sha256(destination),
        }
        checked_after = self.reference_composer.validate_candidate(candidate)
        after_candidate_sha = _candidate_sha256(checked_after)
        after_source_sha = _configuration_sha256(checked_after.source_configuration)
        after_destination_sha = _configuration_sha256(
            checked_after.destination_configuration
        )
        if not (
            before_candidate_sha == after_candidate_sha
            and before_source_sha == values["source_state_sha256"]
            and before_source_sha == after_source_sha
            and before_destination_sha == values["destination_state_sha256"]
            and before_destination_sha == after_destination_sha
        ):
            raise ValueError("candidate changed while taking its canonical snapshot")
        return values

    def evaluate(
        self,
        candidate: ProcessValidReferenceJump,
        *,
        base_context: object,
        residual_context: object,
    ) -> TotalizedJumpPotentialCandidateEvaluation:
        """Compose one active candidate without exponentiating the result."""

        pre_base, pre_guide, pre_residual = self._live_components()
        _require_binary64_environment()
        snapshot = self._snapshot_candidate(candidate)
        reverse_time = snapshot["reverse_time"]
        direct_time = snapshot["direct_time"]
        if type(reverse_time) is not float or type(direct_time) is not float:
            raise RuntimeError("candidate snapshot time types are inconsistent")
        if reverse_time == 0.0 and math.copysign(1.0, reverse_time) < 0.0:
            raise ValueError("candidate reverse time must use canonical positive zero")
        if snapshot["scheduled_reference_exit_rate"] <= 0.0:
            raise ValueError("composition requires an active positive-rate candidate")
        checked_base_context = _validated_context(
            base_context,
            dimension=self._base_checkpoint.snapshot.architecture.context_dimension,
            name="base_context",
        )
        checked_residual_context = _validated_context(
            residual_context,
            dimension=self._residual.model.architecture.context_dimension,
            name="residual_context",
        )
        source = snapshot["source"]
        destination = snapshot["destination"]
        if type(source) is not tuple or type(destination) is not tuple:
            raise RuntimeError("candidate snapshot state types are inconsistent")
        base_architecture = self._base_checkpoint.snapshot.architecture
        base_source_batch = _pack_configuration(
            base_architecture,
            source,
            direct_time=direct_time,
            context=checked_base_context,
        )
        base_destination_batch = _pack_configuration(
            base_architecture,
            destination,
            direct_time=direct_time,
            context=checked_base_context,
        )
        base_batch_domain = b"heterodiff-totalized-jump-potential-base-batch-v1\x00"
        base_source_batch_sha = _batch_sha256(
            base_source_batch, domain=base_batch_domain
        )
        base_destination_batch_sha = _batch_sha256(
            base_destination_batch, domain=base_batch_domain
        )
        with torch.no_grad():
            base_source_tensor = self._base_evaluation_model(base_source_batch)
            base_destination_tensor = self._base_evaluation_model(
                base_destination_batch
            )
        if tuple(base_source_tensor.shape) != (1,) or tuple(
            base_destination_tensor.shape
        ) != (1,):
            raise ArithmeticError("private base model returned the wrong shape")
        base_source = float(base_source_tensor.detach().item())
        base_destination = float(base_destination_tensor.detach().item())
        _validated_float(base_source, name="base source operational energy")
        _validated_float(base_destination, name="base destination operational energy")
        base_exact = _require_fraction_size(
            _fraction(base_destination) - _fraction(base_source),
            name="base exact endpoint difference",
        )
        base_rounded = _round_fraction_once(
            base_exact, name="base operational endpoint difference"
        )
        base_rounding_error = _require_fraction_size(
            abs(_fraction(base_rounded) - base_exact),
            name="base endpoint rounding error",
        )
        guide_edit = self._guide.edit_log_ratio(
            reverse_time,
            source,
            destination,
        )
        if type(guide_edit) is not TotalizedJumpGuideEditRatio:
            raise TypeError("totalized guide returned the wrong exact edit record")
        _validated_fraction_parts(
            guide_edit.exact_operational_endpoint_difference_numerator,
            guide_edit.exact_operational_endpoint_difference_denominator,
            name="untrusted guide exact endpoint difference",
        )
        if (
            _configuration_sha256(guide_edit.source_state)
            != snapshot["source_state_sha256"]
            or _configuration_sha256(guide_edit.destination_state)
            != snapshot["destination_state_sha256"]
        ):
            raise ValueError("guide edit endpoints differ from the candidate")
        guide_edit = self._guide.validate_edit_log_ratio(guide_edit)
        if guide_edit.totalized_certificate_sha256 != (
            self._guide.certificate.certificate_sha256
        ):
            raise ValueError("guide edit belongs to a different totalizer")
        if not _same_float(guide_edit.reverse_time, reverse_time):
            raise ValueError("guide reverse time differs from the candidate")
        if guide_edit.edit_kind != snapshot["edit_kind"]:
            raise ValueError("guide edit kind differs from the candidate")
        if (
            _configuration_sha256(guide_edit.source_state)
            != snapshot["source_state_sha256"]
            or _configuration_sha256(guide_edit.destination_state)
            != snapshot["destination_state_sha256"]
        ):
            raise ValueError("guide edit endpoints differ from the candidate")
        residual_architecture = self._residual.model.architecture
        residual_source_batch = _pack_configuration(
            residual_architecture,
            source,
            direct_time=direct_time,
            context=checked_residual_context,
        )
        residual_destination_batch = _pack_configuration(
            residual_architecture,
            destination,
            direct_time=direct_time,
            context=checked_residual_context,
        )
        residual_difference = self._residual.state_pair_difference(
            residual_source_batch,
            residual_destination_batch,
        )
        if type(residual_difference) is not TotalizedResidualJumpDifference:
            raise TypeError("totalized residual returned the wrong difference record")
        _validated_fraction_parts(
            residual_difference.exact_operational_endpoint_difference_numerator,
            residual_difference.exact_operational_endpoint_difference_denominator,
            name="untrusted residual exact endpoint difference",
        )
        _validated_fraction_parts(
            residual_difference.exact_rounding_error_numerator,
            residual_difference.exact_rounding_error_denominator,
            name="untrusted residual endpoint rounding error",
        )
        residual_difference = self._residual.validate_state_pair_difference(
            residual_difference,
            residual_source_batch,
            residual_destination_batch,
        )
        if residual_difference.certificate is not self._residual.certificate:
            raise ValueError("residual difference belongs to a different totalizer")
        if not _same_float(residual_difference.direct_time, direct_time):
            raise ValueError("residual direct time differs from the candidate")
        residual_batch_domain = b"heterodiff-totalized-residual-batch-v1\x00"
        expected_residual_source_sha = _batch_sha256(
            residual_source_batch, domain=residual_batch_domain
        )
        expected_residual_destination_sha = _batch_sha256(
            residual_destination_batch, domain=residual_batch_domain
        )
        if residual_difference.source_batch_sha256 != (
            expected_residual_source_sha
        ) or residual_difference.destination_batch_sha256 != (
            expected_residual_destination_sha
        ):
            raise ValueError("residual difference batches differ from the candidate")
        post_base, post_guide, post_residual = self._live_components()
        final_candidate = self.reference_composer.validate_candidate(candidate)
        if _candidate_sha256(final_candidate) != snapshot["candidate_sha256"]:
            raise ValueError("candidate changed during composition")
        for name, before, after in (
            ("base", pre_base.certificate_sha256, post_base.certificate_sha256),
            ("guide", pre_guide.certificate_sha256, post_guide.certificate_sha256),
            (
                "residual",
                pre_residual.certificate_sha256,
                post_residual.certificate_sha256,
            ),
        ):
            if before != after:
                raise ConfigurationTotalizedJumpPotentialError(
                    "%s component certificate changed during composition" % name
                )
        _require_binary64_environment()
        guide_exact = _validated_fraction_parts(
            guide_edit.exact_operational_endpoint_difference_numerator,
            guide_edit.exact_operational_endpoint_difference_denominator,
            name="guide exact endpoint difference",
        )
        residual_exact = _validated_fraction_parts(
            residual_difference.exact_operational_endpoint_difference_numerator,
            residual_difference.exact_operational_endpoint_difference_denominator,
            name="residual exact endpoint difference",
        )
        residual_rounding_error = _validated_fraction_parts(
            residual_difference.exact_rounding_error_numerator,
            residual_difference.exact_rounding_error_denominator,
            name="residual endpoint rounding error",
        )
        exact_source_target = _require_fraction_size(
            _fraction(base_source)
            + _fraction(guide_edit.source_operational_log_density)
            + _fraction(residual_difference.source_operational_residual),
            name="exact source operational target",
        )
        exact_destination_target = _require_fraction_size(
            _fraction(base_destination)
            + _fraction(guide_edit.destination_operational_log_density)
            + _fraction(residual_difference.destination_operational_residual),
            name="exact destination operational target",
        )
        exact_combined = _require_fraction_size(
            exact_destination_target - exact_source_target,
            name="exact combined operational endpoint difference",
        )
        exact_component_sum = _require_fraction_size(
            base_exact + guide_exact + residual_exact,
            name="exact component endpoint-difference sum",
        )
        if exact_combined != exact_component_sum:
            raise ConfigurationTotalizedJumpPotentialError(
                "endpoint and component exact sums differ"
            )
        combined = _round_fraction_once(
            exact_combined, name="combined operational endpoint difference"
        )
        aggregate_rounding_error = _require_fraction_size(
            abs(_fraction(combined) - exact_combined),
            name="aggregate endpoint rounding error",
        )
        _require_binary64_environment()
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "candidate_sha256": snapshot["candidate_sha256"],
            "candidate_process_sha256": (self.certificate.process_parameter_sha256),
            "reverse_time": reverse_time,
            "direct_time": direct_time,
            "reference_schedule_rate": snapshot["reference_schedule_rate"],
            "scheduled_reference_exit_rate": (
                snapshot["scheduled_reference_exit_rate"]
            ),
            "edit_kind": snapshot["edit_kind"],
            "source_state_sha256": snapshot["source_state_sha256"],
            "destination_state_sha256": snapshot["destination_state_sha256"],
            "base_context": checked_base_context,
            "base_context_sha256": _context_sha256(checked_base_context, role="base"),
            "residual_context": checked_residual_context,
            "residual_context_sha256": _context_sha256(
                checked_residual_context, role="residual"
            ),
            "base_source_batch_sha256": base_source_batch_sha,
            "base_destination_batch_sha256": base_destination_batch_sha,
            "base_source_operational_energy": base_source,
            "base_destination_operational_energy": base_destination,
            "base_exact_endpoint_difference_numerator": base_exact.numerator,
            "base_exact_endpoint_difference_denominator": base_exact.denominator,
            "base_operational_difference": base_rounded,
            "base_exact_rounding_error_numerator": (base_rounding_error.numerator),
            "base_exact_rounding_error_denominator": (base_rounding_error.denominator),
            "base_rounding_error_upper_bound": _outward_nonnegative_fraction(
                base_rounding_error, name="base endpoint rounding error"
            ),
            "guide_edit_sha256": guide_edit.edit_sha256,
            "guide_source_evaluation_sha256": guide_edit.source_evaluation_sha256,
            "guide_destination_evaluation_sha256": (
                guide_edit.destination_evaluation_sha256
            ),
            "guide_source_branch": guide_edit.source_branch,
            "guide_destination_branch": guide_edit.destination_branch,
            "guide_source_operational_log_density": (
                guide_edit.source_operational_log_density
            ),
            "guide_destination_operational_log_density": (
                guide_edit.destination_operational_log_density
            ),
            "guide_exact_endpoint_difference_numerator": guide_exact.numerator,
            "guide_exact_endpoint_difference_denominator": guide_exact.denominator,
            "guide_operational_difference": guide_edit.log_ratio,
            "guide_to_analytic_edit_discrepancy_bound": (
                guide_edit.represented_to_exact_edit_log_discrepancy_bound
            ),
            "residual_difference_sha256": residual_difference.difference_sha256,
            "residual_source_batch_sha256": (residual_difference.source_batch_sha256),
            "residual_destination_batch_sha256": (
                residual_difference.destination_batch_sha256
            ),
            "residual_source_evaluation_sha256": (
                residual_difference.source_evaluation_sha256
            ),
            "residual_destination_evaluation_sha256": (
                residual_difference.destination_evaluation_sha256
            ),
            "residual_source_branch": residual_difference.source_branch,
            "residual_destination_branch": residual_difference.destination_branch,
            "residual_source_operational_value": (
                residual_difference.source_operational_residual
            ),
            "residual_destination_operational_value": (
                residual_difference.destination_operational_residual
            ),
            "residual_exact_endpoint_difference_numerator": (residual_exact.numerator),
            "residual_exact_endpoint_difference_denominator": (
                residual_exact.denominator
            ),
            "residual_operational_difference": (
                residual_difference.operational_difference
            ),
            "residual_exact_rounding_error_numerator": (
                residual_rounding_error.numerator
            ),
            "residual_exact_rounding_error_denominator": (
                residual_rounding_error.denominator
            ),
            "residual_rounding_error_upper_bound": (
                residual_difference.rounding_error_upper_bound
            ),
            "guide_fallback_used": guide_edit.fallback_used,
            "residual_fallback_used": residual_difference.fallback_used,
            "exact_source_target_value_numerator": exact_source_target.numerator,
            "exact_source_target_value_denominator": (exact_source_target.denominator),
            "exact_destination_target_value_numerator": (
                exact_destination_target.numerator
            ),
            "exact_destination_target_value_denominator": (
                exact_destination_target.denominator
            ),
            "exact_operational_endpoint_difference_numerator": (
                exact_combined.numerator
            ),
            "exact_operational_endpoint_difference_denominator": (
                exact_combined.denominator
            ),
            "combined_log_increment": combined,
            "exact_rounding_error_numerator": (aggregate_rounding_error.numerator),
            "exact_rounding_error_denominator": (aggregate_rounding_error.denominator),
            "rounding_error_upper_bound": _outward_nonnegative_fraction(
                aggregate_rounding_error,
                name="aggregate endpoint rounding error",
            ),
            "base_edge_magnitude_bound": (self.certificate.base_edge_magnitude_bound),
            "guide_edge_magnitude_bound": (self.certificate.guide_edge_magnitude_bound),
            "residual_edge_magnitude_bound": (
                self.certificate.residual_edge_magnitude_bound
            ),
            "aggregate_point_magnitude_bound": (
                self.certificate.aggregate_point_magnitude_bound
            ),
            "aggregate_edge_magnitude_bound": (
                self.certificate.aggregate_edge_magnitude_bound
            ),
            "target_policy": self.certificate.target_policy,
            "composition_policy": self.certificate.composition_policy,
            "rounding_algorithm": self.certificate.rounding_algorithm,
            "evaluation_sha256": "0" * 64,
        }
        values["evaluation_sha256"] = _semantic_digest(_evaluation_payload(values))
        result = TotalizedJumpPotentialCandidateEvaluation(
            **values,
            _construction_token=_EVALUATION_TOKEN,
        )
        _require_binary64_environment()
        return result

    def validate_evaluation(
        self,
        evaluation: object,
        candidate: ProcessValidReferenceJump,
    ) -> TotalizedJumpPotentialCandidateEvaluation:
        """Structurally reconstruct and fully replay one primitive record."""

        if type(evaluation) is not TotalizedJumpPotentialCandidateEvaluation:
            raise TypeError(
                "evaluation must be an exact "
                "TotalizedJumpPotentialCandidateEvaluation"
            )
        TotalizedJumpPotentialCandidateEvaluation(
            **{name: getattr(evaluation, name) for name in _evaluation_fields()},
            _construction_token=_EVALUATION_TOKEN,
        )
        if evaluation.certificate is not self.certificate:
            raise ValueError("evaluation belongs to a different composer certificate")
        checked_candidate = self.reference_composer.validate_candidate(candidate)
        if _candidate_sha256(checked_candidate) != evaluation.candidate_sha256:
            raise ValueError("supplied candidate differs from the evaluation")
        expected = self.evaluate(
            candidate,
            base_context=evaluation.base_context,
            residual_context=evaluation.residual_context,
        )
        for name in _evaluation_fields():
            supplied = getattr(evaluation, name)
            recomputed = getattr(expected, name)
            if name == "certificate":
                matches = supplied is recomputed
            elif type(supplied) is float and type(recomputed) is float:
                matches = _same_float(supplied, recomputed)
            else:
                matches = supplied == recomputed
            if not matches:
                raise ValueError(
                    "composition evaluation field %s differs from replay" % name
                )
        return evaluation


def _require_target_policy(target_policy: object) -> str:
    if type(target_policy) is not str:
        raise TypeError("target_policy must be exact text")
    if target_policy != CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY:
        raise ValueError(
            "only the exported operational-surrogate jump target is supported; "
            "an analytic or posterior target cannot be inferred"
        )
    return target_policy


def certify_totalized_configuration_jump_potential_composer(
    reference_composer: ProcessValidReferenceJumpComposer,
    *,
    base_model: BoundedConfigurationEnergy,
    base_checkpoint: CertifiedConfigurationEnergyCheckpoint,
    base_provenance: ConfigurationEnergyProvenance,
    totalized_guide: TotalizedAssociationJumpGuide,
    totalized_residual: TotalizedConditionalJumpResidual,
    target_policy: object,
    composition_role_sha256: object,
) -> TotalizedConfigurationJumpPotentialComposer:
    """Select and certify the sole supported operational point target."""

    _require_target_policy(target_policy)
    role = _require_sha256(composition_role_sha256, name="composition_role_sha256")
    if type(reference_composer) is not ProcessValidReferenceJumpComposer:
        raise TypeError(
            "reference_composer must be an exact " "ProcessValidReferenceJumpComposer"
        )
    reference_composer._require_live_binding()
    if type(base_model) is not BoundedConfigurationEnergy:
        raise TypeError("base_model must be an exact BoundedConfigurationEnergy")
    if type(base_checkpoint) is not CertifiedConfigurationEnergyCheckpoint:
        raise TypeError(
            "base_checkpoint must be an exact CertifiedConfigurationEnergyCheckpoint"
        )
    if type(base_provenance) is not ConfigurationEnergyProvenance:
        raise TypeError("base_provenance must be exact ConfigurationEnergyProvenance")
    if type(totalized_guide) is not TotalizedAssociationJumpGuide:
        raise TypeError(
            "totalized_guide must be an exact TotalizedAssociationJumpGuide"
        )
    if type(totalized_residual) is not TotalizedConditionalJumpResidual:
        raise TypeError(
            "totalized_residual must be an exact TotalizedConditionalJumpResidual"
        )
    guide = require_matching_totalized_association_jump_guide(
        totalized_guide.preconditioner,
        totalized_guide,
        totalized_guide.range_gate,
        totalized_guide.range_certificate,
        observation=totalized_guide.outcome,
    )
    residual_owner = require_matching_totalized_conditional_jump_residual(
        totalized_residual.model,
        totalized_residual,
        totalized_residual.checkpoint,
        expected_provenance=totalized_residual.provenance,
    )
    require_matching_configuration_energy_certificate(
        base_model,
        base_checkpoint,
        expected_provenance=base_provenance,
    )
    residual_private = getattr(residual_owner, "_evaluation_model", None)
    if type(residual_private) is not BoundedConfigurationEnergy:
        raise TypeError("private residual model has the wrong exact type")
    _require_pairwise_disjoint_model_state_storage(
        (
            ("external base model", base_model),
            ("external residual model", residual_owner.model),
            ("private residual model", residual_private),
        )
    )
    base_evaluation_model = materialize_configuration_energy_checkpoint(
        base_checkpoint,
        expected_provenance=base_provenance,
    )
    base_certificate = require_matching_configuration_energy_certificate(
        base_evaluation_model,
        base_checkpoint,
        expected_provenance=base_provenance,
    )
    certificate = _make_certificate(
        reference_composer=reference_composer,
        base_checkpoint=base_checkpoint,
        base_certificate=base_certificate,
        guide_certificate=guide.certificate,
        residual_certificate=residual_owner.certificate,
        residual_context_dimension=(
            residual_owner.model.architecture.context_dimension
        ),
        composition_role_sha256=role,
    )
    composer = TotalizedConfigurationJumpPotentialComposer(
        reference_composer=reference_composer,
        base_model=base_model,
        base_checkpoint=base_checkpoint,
        base_provenance=base_provenance,
        base_evaluation_model=base_evaluation_model,
        guide=guide,
        residual=residual_owner,
        composition_role_sha256=role,
        certificate=certificate,
        _construction_token=_COMPOSER_TOKEN,
    )
    composer._live_components()
    return composer


def require_matching_totalized_configuration_jump_potential_composer(
    reference_composer: ProcessValidReferenceJumpComposer,
    composer: TotalizedConfigurationJumpPotentialComposer,
    *,
    base_model: BoundedConfigurationEnergy,
    base_checkpoint: CertifiedConfigurationEnergyCheckpoint,
    base_provenance: ConfigurationEnergyProvenance,
    totalized_guide: TotalizedAssociationJumpGuide,
    totalized_residual: TotalizedConditionalJumpResidual,
    target_policy: object,
    composition_role_sha256: object,
) -> TotalizedConfigurationJumpPotentialComposer:
    """Refuse unless every supplied owner is the certified live dependency."""

    _require_target_policy(target_policy)
    role = _require_sha256(composition_role_sha256, name="composition_role_sha256")
    if type(composer) is not TotalizedConfigurationJumpPotentialComposer:
        raise TypeError(
            "composer must be an exact TotalizedConfigurationJumpPotentialComposer"
        )
    if composer.reference_composer is not reference_composer:
        raise ValueError("composer is bound to a different reference composer")
    if composer._base_model is not base_model:
        raise ValueError("composer is bound to a different external base model")
    if composer._base_checkpoint is not base_checkpoint:
        raise ValueError("composer is bound to a different base checkpoint")
    if type(base_provenance) is not ConfigurationEnergyProvenance:
        raise TypeError("base_provenance must be exact ConfigurationEnergyProvenance")
    if composer._base_provenance.sha256 != base_provenance.sha256:
        raise ValueError("composer is bound to different base provenance")
    if composer.totalized_guide is not totalized_guide:
        raise ValueError("composer is bound to a different totalized guide")
    if composer.totalized_residual is not totalized_residual:
        raise ValueError("composer is bound to a different totalized residual")
    if composer.certificate.composition_role_sha256 != role:
        raise ValueError("composer is bound to a different composition role")
    composer._live_components()
    return composer


def validate_totalized_jump_potential_certificate(
    reference_composer: ProcessValidReferenceJumpComposer,
    composer: TotalizedConfigurationJumpPotentialComposer,
    *,
    base_model: BoundedConfigurationEnergy,
    base_checkpoint: CertifiedConfigurationEnergyCheckpoint,
    base_provenance: ConfigurationEnergyProvenance,
    totalized_guide: TotalizedAssociationJumpGuide,
    totalized_residual: TotalizedConditionalJumpResidual,
    target_policy: object,
    composition_role_sha256: object,
) -> TotalizedJumpPotentialCompositionCertificate:
    """Return the fully reconstructed live checkpoint-17 certificate."""

    return require_matching_totalized_configuration_jump_potential_composer(
        reference_composer,
        composer,
        base_model=base_model,
        base_checkpoint=base_checkpoint,
        base_provenance=base_provenance,
        totalized_guide=totalized_guide,
        totalized_residual=totalized_residual,
        target_policy=target_policy,
        composition_role_sha256=composition_role_sha256,
    ).certificate


__all__ = [
    "CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_COMPOSITION_POLICY",
    "CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_FLOATING_POINT_POLICY",
    "CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_ROUNDING_ALGORITHM",
    "CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCHEMA_VERSION",
    "CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_SCOPE",
    "CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY",
    "MAX_TOTALIZED_JUMP_POTENTIAL_EXACT_INTEGER_BITS",
    "ConfigurationTotalizedJumpPotentialError",
    "TotalizedConfigurationJumpPotentialComposer",
    "TotalizedJumpPotentialCandidateEvaluation",
    "TotalizedJumpPotentialCompositionCertificate",
    "certify_totalized_configuration_jump_potential_composer",
    "require_matching_totalized_configuration_jump_potential_composer",
    "validate_totalized_jump_potential_certificate",
]
