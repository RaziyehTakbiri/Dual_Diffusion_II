"""Certified time-zero guide-plus-residual initializer log factor.

The selected implementation uses the process capped-Poisson law ``Pi_N`` as
its base initial law.  Consequently the pointwise log factor multiplying that
law is

``L_init(x; c) = G_64^op(0, x) + R_64^op(S, x, c)``.

The base energy ``V`` is intentionally absent.  Both represented component
values are lifted to exact rationals, added exactly, and rounded once to
binary64.  This module authenticates that deterministic point computation and
its outward interval witnesses.  It does not exponentiate or normalize the
factor, enumerate a support, perform rejection or SIR, consume randomness, or
return an initialized state.  Certificates bind in-process owner identities;
certificate and evaluation digests are therefore local custody records, not
cross-run semantic-reproducibility identifiers.
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
from typing import Mapping, Tuple

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch":
        raise ModuleNotFoundError(
            "configuration initial-tilt composition requires the optional "
            "PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.artifacts.manifest import canonical_config_digest
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy,
    TypedConfigurationBatch,
    pack_typed_configuration_batch,
)
from heterodiff.models.configuration_totalized_jump_residual_torch import (
    EXACT_GATE_RESCALED_CORE_BRANCH,
    PRESERVED_CERTIFIED_RESIDUAL_BRANCH,
    TotalizedConditionalJumpResidual,
    TotalizedResidualJumpCertificate,
    TotalizedResidualPointEvaluation,
    require_matching_totalized_conditional_jump_residual,
)
from heterodiff.processes.plugin_bridge_sampler import (
    ProcessValidReferenceJumpComposer,
)
from heterodiff.theory.association_preconditioner import _plain_key_sha256
from heterodiff.theory.association_totalized_jump_guide import (
    NUMERICAL_FALLBACK_BRANCH,
    PRESERVED_RANGE_GATED_BRANCH,
    RANGE_FALLBACK_BRANCH,
    TotalizedAssociationJumpGuide,
    TotalizedJumpGuideCertificate,
    TotalizedJumpGuideEvaluation,
    require_matching_totalized_association_jump_guide,
)
from heterodiff.theory.configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    MAX_REFERENCE_DENSITY_COORDINATES,
    TransformedConfiguration,
    TransformedEvent,
)


CONFIGURATION_INITIAL_TILT_SCHEMA_VERSION = "configuration-initial-tilt-v1"
CONFIGURATION_INITIAL_TILT_TARGET_POLICY = (
    "operational-initial-log-factor-v1;"
    "rho0=Pi_N;u=0;s=S;"
    "L_init(x,c)=iota(G64_totalized(0,x))+"
    "iota(R64_totalized(S,x,c));exclude-base-energy-V"
)
CONFIGURATION_INITIAL_TILT_BASE_LAW_POLICY = (
    "process-owned-capped-poisson-reference-Pi_N-v1"
)
CONFIGURATION_INITIAL_TILT_COMPOSITION_POLICY = (
    "guide-plus-residual-only;exact-rational-represented-component-sum;"
    "single-final-binary64-nearest-even-round;canonical-positive-zero;"
    "no-added-fallback"
)
CONFIGURATION_INITIAL_TILT_ROUNDING_ALGORITHM = (
    "lift-two-represented-binary64-point-values-to-exact-fractions;"
    "sum-exactly;round-once-to-binary64-nearest-even;"
    "outward-binary64-interval-witnesses;canonical-positive-zero"
)
CONFIGURATION_INITIAL_TILT_FLOATING_POINT_POLICY = (
    "binary64-round-to-nearest-even-and-gradual-underflow-required;"
    "live-python-and-torch-arithmetic-probe-before-and-after-composition"
)
CONFIGURATION_INITIAL_TILT_SCOPE = (
    "one-canonical-configuration;process-owned-Pi_N-base-initial-law;"
    "fixed-reverse-time-zero-and-direct-time-horizon;"
    "fixed-observation-totalized-guide;checkpoint-totalized-residual;"
    "explicit-residual-context;deterministic-operational-log-factor;"
    "residual-context-values-not-adapter-origin-authenticated;"
    "base-energy-and-observation-only-nuisance-input-excluded;trusted-runtime;"
    "runtime-object-identity-witnesses-procedural-not-cryptographic;"
    "certificate-and-evaluation-digests-process-instance-local-not-cross-run;"
    "not-loaded-code-integrity-or-monkeypatch-resistance;"
    "not-exact-analytic-factor;not-exact-conditional-or-posterior-target;"
    "not-exponentiation;not-normalization;not-enumeration;not-rejection;"
    "not-SIR;not-categorical-selection;not-rng;not-initializer;"
    "not-path;not-sampler-admission"
)

MAX_INITIAL_TILT_EXACT_INTEGER_BITS = 8192
MAX_INITIAL_TILT_RUNTIME_IDENTITY = 2**64 - 1
_MAX_CONTEXT_DIMENSION = 4096
_CERTIFICATE_TOKEN = object()
_OWNER_TOKEN = object()
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


class ConfigurationInitialTiltError(ArithmeticError):
    """Raised when deterministic initial log-factor composition fails."""


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


def _validated_runtime_identity(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if not 1 <= value <= MAX_INITIAL_TILT_RUNTIME_IDENTITY:
        raise ValueError("%s lies outside the unsigned 64-bit identity range" % name)
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
        value.numerator.bit_length() > MAX_INITIAL_TILT_EXACT_INTEGER_BITS
        or value.denominator.bit_length() > MAX_INITIAL_TILT_EXACT_INTEGER_BITS
    ):
        raise ConfigurationInitialTiltError(
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
        if value.bit_length() > MAX_INITIAL_TILT_EXACT_INTEGER_BITS:
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
        raise ConfigurationInitialTiltError(
            "%s has no finite binary64 representation" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationInitialTiltError(
            "%s has no finite binary64 representation" % name
        )
    return _canonical_zero(result)


def _outward_lower_fraction(value: Fraction, *, name: str) -> float:
    _require_fraction_size(value, name=name)
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ConfigurationInitialTiltError(
            "%s has no finite binary64 lower witness" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationInitialTiltError(
            "%s has no finite binary64 lower witness" % name
        )
    if _fraction(result) > value:
        result = math.nextafter(result, -math.inf)
    if not math.isfinite(result):
        raise ConfigurationInitialTiltError("%s cannot be rounded outward" % name)
    return _canonical_zero(result)


def _outward_upper_fraction(value: Fraction, *, name: str) -> float:
    _require_fraction_size(value, name=name)
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ConfigurationInitialTiltError(
            "%s has no finite binary64 upper witness" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationInitialTiltError(
            "%s has no finite binary64 upper witness" % name
        )
    if _fraction(result) < value:
        result = math.nextafter(result, math.inf)
    if not math.isfinite(result):
        raise ConfigurationInitialTiltError("%s cannot be rounded outward" % name)
    return _canonical_zero(result)


def _outward_interval(
    guide_lower: float,
    guide_upper: float,
    residual_bound: float,
) -> Tuple[float, float]:
    lower_exact = _require_fraction_size(
        _fraction(guide_lower) - _fraction(residual_bound),
        name="initial log-factor lower endpoint",
    )
    upper_exact = _require_fraction_size(
        _fraction(guide_upper) + _fraction(residual_bound),
        name="initial log-factor upper endpoint",
    )
    return (
        _outward_lower_fraction(lower_exact, name="initial log-factor lower endpoint"),
        _outward_upper_fraction(upper_exact, name="initial log-factor upper endpoint"),
    )


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
    values = []
    for raw in iterator:
        if len(values) >= _MAX_CONTEXT_DIMENSION:
            raise ValueError("%s exceeds the adapter dimension limit" % name)
        if isinstance(raw, bool) or not isinstance(raw, Real):
            raise TypeError("%s entries must be real non-boolean scalars" % name)
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError("%s entries must be finite" % name)
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("%s entries must use canonical positive zero" % name)
        values.append(value)
    if len(values) != dimension:
        raise ValueError("%s must contain exactly %d entries" % (name, dimension))
    return tuple(values)


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
        {"configuration_initial_tilt": _typed_digest_value(value)}
    )


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
        raise ConfigurationInitialTiltError(
            "initial log-factor composition requires round-to-nearest-even "
            "binary64 arithmetic with gradual underflow"
        )
    return observed


def _runtime_sha256() -> str:
    return _semantic_digest(
        {
            "domain": "configuration-initial-tilt-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "torch_version": str(torch.__version__),
            "schema_version": CONFIGURATION_INITIAL_TILT_SCHEMA_VERSION,
            "floating_point_policy": CONFIGURATION_INITIAL_TILT_FLOATING_POINT_POLICY,
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


def _require_disjoint_residual_model_state_storage(
    external_model: BoundedConfigurationEnergy,
    private_model: BoundedConfigurationEnergy,
) -> None:
    if external_model is private_model:
        raise ValueError("external and private residual models must be distinct")
    external_intervals = _model_state_storage_intervals(
        external_model, name="external residual model"
    )
    private_intervals = _model_state_storage_intervals(
        private_model, name="private residual model"
    )
    for external in external_intervals:
        for private in private_intervals:
            if external[:2] != private[:2]:
                continue
            if external[2] < private[3] and private[2] < external[3]:
                raise ValueError(
                    "external and private residual model state storage overlaps "
                    "between %s and %s" % (external[4], private[4])
                )


def _configuration_sha256(configuration: TransformedConfiguration) -> str:
    if type(configuration) is not tuple:
        raise TypeError("configuration must be an exact tuple")
    if len(configuration) > MAX_CONFIGURATION_CARDINALITY:
        raise ValueError("configuration exceeds the cardinality limit")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-configuration-initial-tilt-state-v1\x00")
    digest.update(len(configuration).to_bytes(8, "big", signed=False))
    coordinate_count = 0
    previous_key = None
    for occurrence, event in enumerate(configuration):
        if type(event) is not TransformedEvent:
            raise TypeError("configuration must contain exact TransformedEvent values")
        checked = TransformedEvent(event.event_type, event.coordinates)
        key = checked.model_key()
        if event.model_key() != key:
            raise ValueError("configuration contains a noncanonical event")
        if previous_key is not None and key < previous_key:
            raise ValueError("configuration is not canonically ordered")
        previous_key = key
        coordinate_count += len(checked.coordinates)
        if coordinate_count > MAX_REFERENCE_DENSITY_COORDINATES:
            raise ValueError("configuration exceeds the coordinate limit")
        digest.update(occurrence.to_bytes(8, "big", signed=False))
        digest.update(checked.event_type.to_bytes(8, "big", signed=False))
        digest.update(len(checked.coordinates).to_bytes(8, "big", signed=False))
        for coordinate in checked.coordinates:
            digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _copy_configuration(
    configuration: TransformedConfiguration,
) -> TransformedConfiguration:
    return tuple(
        TransformedEvent(event.event_type, event.coordinates) for event in configuration
    )


def _context_sha256(context: Tuple[float, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-configuration-initial-tilt-context-v1\x00")
    digest.update(len(context).to_bytes(8, "big", signed=False))
    for value in context:
        digest.update(struct.pack(">d", value))
    return digest.hexdigest()


def _configuration_tensor_maps(
    architecture: object,
    configuration: TransformedConfiguration,
) -> Tuple[dict, dict]:
    coordinates = {}
    owners = {}
    grouped = {event_type: [] for event_type in architecture.type_ids}
    for event in configuration:
        try:
            grouped[event.event_type].append(event.coordinates)
        except KeyError as error:
            raise ValueError(
                "configuration contains an event type outside the architecture"
            ) from error
    for event_type, dimension in zip(
        architecture.type_ids,
        architecture.type_dimensions,
    ):
        event_coordinates = grouped[event_type]
        if not event_coordinates:
            continue
        if dimension == 0:
            coordinate_tensor = torch.empty(
                (len(event_coordinates), 0), dtype=torch.float64, device="cpu"
            )
        else:
            coordinate_tensor = torch.tensor(
                event_coordinates,
                dtype=torch.float64,
                device="cpu",
            )
        owner_tensor = torch.zeros(
            (len(event_coordinates),), dtype=torch.int64, device="cpu"
        )
        coordinates[event_type] = coordinate_tensor
        owners[event_type] = owner_tensor
    return coordinates, owners


def _pack_residual_configuration(
    model: BoundedConfigurationEnergy,
    configuration: TransformedConfiguration,
    *,
    direct_time: float,
    context: Tuple[float, ...],
) -> TypedConfigurationBatch:
    architecture = model.architecture
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
class InitialTiltCompositionCertificate:
    """Sealed custody, factorization, bounds, and negative claim boundary."""

    schema_version: str
    certificate_scope: str
    target_policy: str
    base_initial_law_policy: str
    composition_policy: str
    rounding_algorithm: str
    floating_point_environment_policy: str
    composition_role_sha256: str
    process_parameter_sha256: str
    reference_base_law_sha256: str
    reference_composer_runtime_identity: int
    guide_runtime_identity: int
    residual_runtime_identity: int
    reverse_time: float
    direct_time: float
    guide_preconditioner_sha256: str
    guide_outcome_sha256: str
    guide_totalized_certificate_sha256: str
    guide_evaluator_runtime_sha256: str
    guide_operational_log_lower_bound: float
    guide_operational_log_upper_bound: float
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
    residual_global_point_magnitude_bound: float
    initial_log_factor_lower_bound: float
    initial_log_factor_upper_bound: float
    initial_log_factor_magnitude_bound: float
    composer_runtime_sha256: str
    maximum_exact_integer_bits: int
    operational_surrogate_initial_log_factor_selected: bool
    reference_base_initial_law_is_pi_n: bool
    base_energy_excluded: bool
    observation_only_nuisance_excluded: bool
    totalized_guide_required: bool
    totalized_residual_required: bool
    reverse_time_fixed_at_zero: bool
    direct_time_fixed_at_horizon: bool
    exact_represented_component_sum: bool
    aggregate_rounded_once: bool
    deterministic_point_factor_admissible: bool
    base_energy_included: bool
    conditioning_adapter_origin_authenticated: bool
    exact_analytic_factor_preserved: bool
    exact_conditional_or_posterior_target: bool
    exact_factor_exponentiation_certified: bool
    normalization_certified: bool
    support_enumeration_admissible: bool
    rejection_sampling_admissible: bool
    sir_admissible: bool
    categorical_selection_admissible: bool
    randomness_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    operational_sampler_admissible: bool
    coordinate_derivatives_admissible: bool
    continuous_drift_admissible: bool
    runtime_portable: bool
    blas_identity_authenticated: bool
    loaded_code_identity_authenticated: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("InitialTiltCompositionCertificate cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("initial-tilt certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initial-tilt certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initial-tilt certificates are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return ("configuration-initial-tilt-certificate-v1", self.certificate_sha256)


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(InitialTiltCompositionCertificate.__annotations__)


def _validate_certificate(
    certificate: object,
) -> InitialTiltCompositionCertificate:
    if type(certificate) is not InitialTiltCompositionCertificate:
        raise TypeError(
            "certificate must be an exact InitialTiltCompositionCertificate"
        )
    digest_fields = (
        "composition_role_sha256",
        "process_parameter_sha256",
        "reference_base_law_sha256",
        "guide_preconditioner_sha256",
        "guide_outcome_sha256",
        "guide_totalized_certificate_sha256",
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
    )
    for name in digest_fields:
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    for name in (
        "reference_composer_runtime_identity",
        "guide_runtime_identity",
        "residual_runtime_identity",
    ):
        _validated_runtime_identity(
            getattr(certificate, name), name="certificate.%s" % name
        )
    expected_text = {
        "schema_version": CONFIGURATION_INITIAL_TILT_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_INITIAL_TILT_SCOPE,
        "target_policy": CONFIGURATION_INITIAL_TILT_TARGET_POLICY,
        "base_initial_law_policy": CONFIGURATION_INITIAL_TILT_BASE_LAW_POLICY,
        "composition_policy": CONFIGURATION_INITIAL_TILT_COMPOSITION_POLICY,
        "rounding_algorithm": CONFIGURATION_INITIAL_TILT_ROUNDING_ALGORITHM,
        "floating_point_environment_policy": (
            CONFIGURATION_INITIAL_TILT_FLOATING_POINT_POLICY
        ),
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("initial-tilt certificate %s is inconsistent" % name)
    _validated_float(
        certificate.reverse_time,
        name="certificate.reverse_time",
        nonnegative=True,
        canonical_zero=True,
    )
    if not _same_float(certificate.reverse_time, 0.0):
        raise ValueError("certificate reverse time must be positive zero")
    _validated_float(
        certificate.direct_time,
        name="certificate.direct_time",
        strictly_positive=True,
    )
    if (
        type(certificate.residual_context_dimension) is not int
        or isinstance(certificate.residual_context_dimension, bool)
        or not 0 <= certificate.residual_context_dimension <= _MAX_CONTEXT_DIMENSION
    ):
        raise ValueError("certificate residual context dimension is invalid")
    if (
        type(certificate.maximum_exact_integer_bits) is not int
        or isinstance(certificate.maximum_exact_integer_bits, bool)
        or certificate.maximum_exact_integer_bits != MAX_INITIAL_TILT_EXACT_INTEGER_BITS
    ):
        raise ValueError("certificate exact-integer limit is inconsistent")
    lower = _validated_float(
        certificate.guide_operational_log_lower_bound,
        name="certificate.guide_operational_log_lower_bound",
    )
    upper = _validated_float(
        certificate.guide_operational_log_upper_bound,
        name="certificate.guide_operational_log_upper_bound",
    )
    residual_bound = _validated_float(
        certificate.residual_global_point_magnitude_bound,
        name="certificate.residual_global_point_magnitude_bound",
        nonnegative=True,
    )
    if lower > upper:
        raise ValueError("certificate guide interval is empty")
    expected_lower, expected_upper = _outward_interval(lower, upper, residual_bound)
    if not _same_float(certificate.initial_log_factor_lower_bound, expected_lower):
        raise ValueError("certificate initial-factor lower bound is inconsistent")
    if not _same_float(certificate.initial_log_factor_upper_bound, expected_upper):
        raise ValueError("certificate initial-factor upper bound is inconsistent")
    expected_magnitude = max(abs(expected_lower), abs(expected_upper))
    if not _same_float(
        certificate.initial_log_factor_magnitude_bound, expected_magnitude
    ):
        raise ValueError("certificate initial-factor magnitude bound is inconsistent")
    true_flags = (
        "operational_surrogate_initial_log_factor_selected",
        "reference_base_initial_law_is_pi_n",
        "base_energy_excluded",
        "observation_only_nuisance_excluded",
        "totalized_guide_required",
        "totalized_residual_required",
        "reverse_time_fixed_at_zero",
        "direct_time_fixed_at_horizon",
        "exact_represented_component_sum",
        "aggregate_rounded_once",
        "deterministic_point_factor_admissible",
        "passed",
    )
    false_flags = (
        "base_energy_included",
        "conditioning_adapter_origin_authenticated",
        "exact_analytic_factor_preserved",
        "exact_conditional_or_posterior_target",
        "exact_factor_exponentiation_certified",
        "normalization_certified",
        "support_enumeration_admissible",
        "rejection_sampling_admissible",
        "sir_admissible",
        "categorical_selection_admissible",
        "randomness_admissible",
        "initializer_admissible",
        "path_admissible",
        "operational_sampler_admissible",
        "coordinate_derivatives_admissible",
        "continuous_drift_admissible",
        "runtime_portable",
        "blas_identity_authenticated",
        "loaded_code_identity_authenticated",
    )
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("initial-tilt positive claim flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("initial-tilt negative claim flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    if certificate.certificate_sha256 != _semantic_digest(_certificate_payload(values)):
        raise ValueError("initial-tilt certificate digest is inconsistent")
    return certificate


def _make_certificate(
    *,
    reference_composer: ProcessValidReferenceJumpComposer,
    guide_owner: TotalizedAssociationJumpGuide,
    residual_owner: TotalizedConditionalJumpResidual,
    guide_certificate: TotalizedJumpGuideCertificate,
    residual_certificate: TotalizedResidualJumpCertificate,
    residual_context_dimension: int,
    composition_role_sha256: str,
) -> InitialTiltCompositionCertificate:
    process_key = reference_composer.process_parameter_key
    process_sha = _plain_key_sha256(
        process_key,
        domain=b"heterodiff-configuration-initial-tilt-process-v1\x00",
    )
    reference_sha = _plain_key_sha256(
        reference_composer.process.reference.parameter_key(),
        domain=b"heterodiff-configuration-initial-tilt-base-law-v1\x00",
    )
    guide_lower = guide_certificate.operational_log_lower_bound
    guide_upper = guide_certificate.operational_log_upper_bound
    residual_bound = residual_certificate.global_point_magnitude_bound
    lower, upper = _outward_interval(guide_lower, guide_upper, residual_bound)
    values = {
        "schema_version": CONFIGURATION_INITIAL_TILT_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_INITIAL_TILT_SCOPE,
        "target_policy": CONFIGURATION_INITIAL_TILT_TARGET_POLICY,
        "base_initial_law_policy": CONFIGURATION_INITIAL_TILT_BASE_LAW_POLICY,
        "composition_policy": CONFIGURATION_INITIAL_TILT_COMPOSITION_POLICY,
        "rounding_algorithm": CONFIGURATION_INITIAL_TILT_ROUNDING_ALGORITHM,
        "floating_point_environment_policy": (
            CONFIGURATION_INITIAL_TILT_FLOATING_POINT_POLICY
        ),
        "composition_role_sha256": composition_role_sha256,
        "process_parameter_sha256": process_sha,
        "reference_base_law_sha256": reference_sha,
        "reference_composer_runtime_identity": id(reference_composer),
        "guide_runtime_identity": id(guide_owner),
        "residual_runtime_identity": id(residual_owner),
        "reverse_time": 0.0,
        "direct_time": reference_composer.process.schedule.horizon,
        "guide_preconditioner_sha256": _plain_key_sha256(
            guide_certificate.preconditioner_parameter_key,
            domain=b"heterodiff-configuration-initial-tilt-guide-v1\x00",
        ),
        "guide_outcome_sha256": _plain_key_sha256(
            guide_certificate.outcome_key,
            domain=b"heterodiff-configuration-initial-tilt-outcome-v1\x00",
        ),
        "guide_totalized_certificate_sha256": guide_certificate.certificate_sha256,
        "guide_evaluator_runtime_sha256": guide_certificate.evaluator_runtime_sha256,
        "guide_operational_log_lower_bound": guide_lower,
        "guide_operational_log_upper_bound": guide_upper,
        "residual_totalized_certificate_sha256": (
            residual_certificate.certificate_sha256
        ),
        "residual_contract_sha256": residual_certificate.residual_contract_sha256,
        "residual_core_architecture_sha256": (
            residual_certificate.core_architecture_sha256
        ),
        "residual_context_schema_sha256": residual_certificate.context_schema_sha256,
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
        "residual_global_point_magnitude_bound": residual_bound,
        "initial_log_factor_lower_bound": lower,
        "initial_log_factor_upper_bound": upper,
        "initial_log_factor_magnitude_bound": max(abs(lower), abs(upper)),
        "composer_runtime_sha256": _runtime_sha256(),
        "maximum_exact_integer_bits": MAX_INITIAL_TILT_EXACT_INTEGER_BITS,
        "operational_surrogate_initial_log_factor_selected": True,
        "reference_base_initial_law_is_pi_n": True,
        "base_energy_excluded": True,
        "observation_only_nuisance_excluded": True,
        "totalized_guide_required": True,
        "totalized_residual_required": True,
        "reverse_time_fixed_at_zero": True,
        "direct_time_fixed_at_horizon": True,
        "exact_represented_component_sum": True,
        "aggregate_rounded_once": True,
        "deterministic_point_factor_admissible": True,
        "base_energy_included": False,
        "conditioning_adapter_origin_authenticated": False,
        "exact_analytic_factor_preserved": False,
        "exact_conditional_or_posterior_target": False,
        "exact_factor_exponentiation_certified": False,
        "normalization_certified": False,
        "support_enumeration_admissible": False,
        "rejection_sampling_admissible": False,
        "sir_admissible": False,
        "categorical_selection_admissible": False,
        "randomness_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "operational_sampler_admissible": False,
        "coordinate_derivatives_admissible": False,
        "continuous_drift_admissible": False,
        "runtime_portable": False,
        "blas_identity_authenticated": False,
        "loaded_code_identity_authenticated": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return InitialTiltCompositionCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _evaluation_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "configuration", "evaluation_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class InitialTiltPointEvaluation:
    """One sealed and replayable initial operational log-factor point."""

    certificate: InitialTiltCompositionCertificate
    certificate_sha256: str
    process_parameter_sha256: str
    reverse_time: float
    direct_time: float
    configuration: TransformedConfiguration
    configuration_sha256: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    guide_evaluation_sha256: str
    guide_branch: str
    guide_operational_log_density: float
    guide_operational_log_lower_bound: float
    guide_operational_log_upper_bound: float
    guide_point_log_discrepancy_bound: float
    residual_evaluation_sha256: str
    residual_batch_sha256: str
    residual_branch: str
    residual_operational_value: float
    residual_operational_point_magnitude_bound: float
    residual_mathematical_gate_numerator: int
    residual_mathematical_gate_denominator: int
    exact_initial_log_factor_numerator: int
    exact_initial_log_factor_denominator: int
    initial_log_factor: float
    exact_rounding_error_numerator: int
    exact_rounding_error_denominator: int
    rounding_error_upper_bound: float
    initial_log_factor_lower_bound: float
    initial_log_factor_upper_bound: float
    initial_log_factor_magnitude_bound: float
    base_initial_law_policy: str
    target_policy: str
    composition_policy: str
    rounding_algorithm: str
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("InitialTiltPointEvaluation cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError("initial-tilt point evaluations are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initial-tilt point evaluation fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("point certificate digest is inconsistent")
        for name in (
            "certificate_sha256",
            "process_parameter_sha256",
            "configuration_sha256",
            "residual_context_sha256",
            "guide_evaluation_sha256",
            "residual_evaluation_sha256",
            "residual_batch_sha256",
            "evaluation_sha256",
        ):
            _require_sha256(values[name], name="evaluation.%s" % name)
        if values["process_parameter_sha256"] != certificate.process_parameter_sha256:
            raise ValueError("point process digest differs from certificate")
        for name, expected in (
            ("reverse_time", certificate.reverse_time),
            ("direct_time", certificate.direct_time),
        ):
            _validated_float(
                values[name],
                name="evaluation.%s" % name,
                nonnegative=True,
                canonical_zero=name == "reverse_time",
            )
            if not _same_float(values[name], expected):
                raise ValueError("point %s differs from certificate" % name)
        if type(values["configuration"]) is not tuple:
            raise TypeError("evaluation configuration must be an exact tuple")
        expected_configuration_sha = _configuration_sha256(values["configuration"])
        if values["configuration_sha256"] != expected_configuration_sha:
            raise ValueError("point configuration digest is inconsistent")
        if type(values["residual_context"]) is not tuple:
            raise TypeError("evaluation residual_context must be an exact tuple")
        context = _validated_context(
            values["residual_context"],
            dimension=certificate.residual_context_dimension,
            name="evaluation.residual_context",
        )
        if context != values["residual_context"]:
            raise ValueError("point residual context is noncanonical")
        if values["residual_context_sha256"] != _context_sha256(context):
            raise ValueError("point residual context digest is inconsistent")
        if values["guide_branch"] not in _GUIDE_BRANCHES:
            raise ValueError("point guide branch is unknown")
        if values["residual_branch"] not in _RESIDUAL_BRANCHES:
            raise ValueError("point residual branch is unknown")
        if values["residual_branch"] != PRESERVED_CERTIFIED_RESIDUAL_BRANCH:
            raise ValueError(
                "direct-horizon residual point must use the preserved branch"
            )
        for name in (
            "guide_operational_log_density",
            "guide_operational_log_lower_bound",
            "guide_operational_log_upper_bound",
            "guide_point_log_discrepancy_bound",
            "residual_operational_value",
            "residual_operational_point_magnitude_bound",
            "initial_log_factor",
            "rounding_error_upper_bound",
            "initial_log_factor_lower_bound",
            "initial_log_factor_upper_bound",
            "initial_log_factor_magnitude_bound",
        ):
            _validated_float(
                values[name],
                name="evaluation.%s" % name,
                nonnegative=name
                in (
                    "guide_point_log_discrepancy_bound",
                    "residual_operational_point_magnitude_bound",
                    "rounding_error_upper_bound",
                    "initial_log_factor_magnitude_bound",
                ),
                canonical_zero=name == "initial_log_factor",
            )
        if not _same_float(
            values["guide_operational_log_lower_bound"],
            certificate.guide_operational_log_lower_bound,
        ) or not _same_float(
            values["guide_operational_log_upper_bound"],
            certificate.guide_operational_log_upper_bound,
        ):
            raise ValueError("point guide interval differs from certificate")
        guide_value = values["guide_operational_log_density"]
        if not (
            values["guide_operational_log_lower_bound"]
            <= guide_value
            <= values["guide_operational_log_upper_bound"]
        ):
            raise ValueError("point guide value lies outside its interval")
        residual_bound = values["residual_operational_point_magnitude_bound"]
        if not _same_float(
            residual_bound,
            certificate.residual_global_point_magnitude_bound,
        ):
            raise ValueError("point residual bound differs from certificate")
        if abs(values["residual_operational_value"]) > residual_bound:
            raise ValueError("point residual value exceeds its bound")
        gate = _validated_fraction_parts(
            values["residual_mathematical_gate_numerator"],
            values["residual_mathematical_gate_denominator"],
            name="evaluation.residual_mathematical_gate",
        )
        if gate != Fraction(1, 1):
            raise ValueError("time-zero residual mathematical gate must equal one")
        exact = _validated_fraction_parts(
            values["exact_initial_log_factor_numerator"],
            values["exact_initial_log_factor_denominator"],
            name="evaluation.exact_initial_log_factor",
        )
        expected_exact = _require_fraction_size(
            _fraction(guide_value) + _fraction(values["residual_operational_value"]),
            name="initial log factor",
        )
        if exact != expected_exact:
            raise ValueError("point exact initial log factor is inconsistent")
        rounded = _round_fraction_once(expected_exact, name="initial log factor")
        if not _same_float(values["initial_log_factor"], rounded):
            raise ValueError("point initial log factor is not one-round composition")
        exact_error = _validated_fraction_parts(
            values["exact_rounding_error_numerator"],
            values["exact_rounding_error_denominator"],
            name="evaluation.exact_rounding_error",
        )
        expected_error = abs(_fraction(rounded) - expected_exact)
        if exact_error != expected_error:
            raise ValueError("point exact rounding error is inconsistent")
        expected_error_upper = _outward_upper_fraction(
            expected_error, name="initial log-factor rounding error"
        )
        if not _same_float(values["rounding_error_upper_bound"], expected_error_upper):
            raise ValueError("point rounding-error witness is inconsistent")
        expected_lower, expected_upper = _outward_interval(
            values["guide_operational_log_lower_bound"],
            values["guide_operational_log_upper_bound"],
            residual_bound,
        )
        if not _same_float(values["initial_log_factor_lower_bound"], expected_lower):
            raise ValueError("point initial-factor lower witness is inconsistent")
        if not _same_float(values["initial_log_factor_upper_bound"], expected_upper):
            raise ValueError("point initial-factor upper witness is inconsistent")
        expected_magnitude = max(abs(expected_lower), abs(expected_upper))
        if not _same_float(
            values["initial_log_factor_magnitude_bound"], expected_magnitude
        ):
            raise ValueError("point initial-factor magnitude witness is inconsistent")
        if not expected_lower <= exact <= expected_upper:
            raise ValueError("point exact initial log factor lies outside witnesses")
        for name, expected in (
            ("base_initial_law_policy", certificate.base_initial_law_policy),
            ("target_policy", certificate.target_policy),
            ("composition_policy", certificate.composition_policy),
            ("rounding_algorithm", certificate.rounding_algorithm),
        ):
            if values[name] != expected:
                raise ValueError("point %s is inconsistent" % name)
        expected_digest = _semantic_digest(_evaluation_payload(values))
        if values["evaluation_sha256"] != expected_digest:
            raise ValueError("point evaluation digest is inconsistent")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    @property
    def base_energy_excluded(self) -> bool:
        return True

    @property
    def exact_factor_exponentiation_certified(self) -> bool:
        return False

    @property
    def normalization_certified(self) -> bool:
        return False

    @property
    def randomness_admissible(self) -> bool:
        return False

    @property
    def initializer_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initial-tilt point evaluations are not pickle objects")


def _evaluation_fields() -> Tuple[str, ...]:
    return tuple(InitialTiltPointEvaluation.__annotations__)


def _field_matches(name: str, supplied: object, expected: object) -> bool:
    if name == "certificate":
        return supplied is expected
    if type(supplied) is float and type(expected) is float:
        return _same_float(supplied, expected)
    return supplied == expected


class ConfigurationInitialTiltComposer:
    """Immutable owner of one authenticated initial operational log factor."""

    __slots__ = (
        "_reference_composer",
        "_reference_composer_identity",
        "_guide",
        "_guide_identity",
        "_residual",
        "_residual_identity",
        "_composition_role_sha256",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ConfigurationInitialTiltComposer cannot be subclassed")

    def __init__(
        self,
        *,
        reference_composer: ProcessValidReferenceJumpComposer,
        guide: TotalizedAssociationJumpGuide,
        residual: TotalizedConditionalJumpResidual,
        composition_role_sha256: str,
        certificate: InitialTiltCompositionCertificate,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("initial-tilt owners require certification")
        if type(reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference_composer has the wrong exact type")
        if type(guide) is not TotalizedAssociationJumpGuide:
            raise TypeError("guide has the wrong exact type")
        if type(residual) is not TotalizedConditionalJumpResidual:
            raise TypeError("residual has the wrong exact type")
        role = _require_sha256(composition_role_sha256, name="composition_role_sha256")
        if certificate.composition_role_sha256 != role:
            raise ValueError("certificate has a different composition role")
        object.__setattr__(self, "_reference_composer", reference_composer)
        object.__setattr__(self, "_reference_composer_identity", reference_composer)
        object.__setattr__(self, "_guide", guide)
        object.__setattr__(self, "_guide_identity", guide)
        object.__setattr__(self, "_residual", residual)
        object.__setattr__(self, "_residual_identity", residual)
        object.__setattr__(self, "_composition_role_sha256", role)
        object.__setattr__(self, "_certificate", _validate_certificate(certificate))

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("ConfigurationInitialTiltComposer is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("ConfigurationInitialTiltComposer is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initial-tilt owners are not pickle objects")

    @property
    def certificate(self) -> InitialTiltCompositionCertificate:
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

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "configuration-initial-tilt-composer-v1",
            self.certificate.parameter_key(),
        )

    def _require_owner_snapshot(
        self,
        snapshot: object,
    ) -> Tuple[
        ProcessValidReferenceJumpComposer,
        TotalizedAssociationJumpGuide,
        TotalizedConditionalJumpResidual,
        InitialTiltCompositionCertificate,
        str,
    ]:
        if type(snapshot) is not tuple or len(snapshot) != 5:
            raise TypeError("owner snapshot must be an exact five-item tuple")
        reference_composer, guide, residual, certificate, role = snapshot
        if type(reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("snapshot reference composer has the wrong exact type")
        if type(guide) is not TotalizedAssociationJumpGuide:
            raise TypeError("snapshot guide has the wrong exact type")
        if type(residual) is not TotalizedConditionalJumpResidual:
            raise TypeError("snapshot residual has the wrong exact type")
        if type(certificate) is not InitialTiltCompositionCertificate:
            raise TypeError("snapshot certificate has the wrong exact type")
        checked_role = _require_sha256(role, name="snapshot.composition_role_sha256")
        if self._reference_composer is not reference_composer or (
            self._reference_composer_identity is not reference_composer
        ):
            raise ValueError(
                "reference composer differs from the evaluation-time owner snapshot"
            )
        if self._guide is not guide or self._guide_identity is not guide:
            raise ValueError("guide differs from the evaluation-time owner snapshot")
        if self._residual is not residual or self._residual_identity is not residual:
            raise ValueError("residual differs from the evaluation-time owner snapshot")
        if self._certificate is not certificate:
            raise ValueError("certificate differs from the evaluation-time snapshot")
        if self._composition_role_sha256 != checked_role:
            raise ValueError(
                "composition role differs from the evaluation-time snapshot"
            )
        _validate_certificate(certificate)
        if certificate.composition_role_sha256 != checked_role:
            raise ValueError("snapshot certificate has a different composition role")
        return reference_composer, guide, residual, certificate, checked_role

    def _owner_snapshot(
        self,
    ) -> Tuple[
        ProcessValidReferenceJumpComposer,
        TotalizedAssociationJumpGuide,
        TotalizedConditionalJumpResidual,
        InitialTiltCompositionCertificate,
        str,
    ]:
        snapshot = (
            self._reference_composer,
            self._guide,
            self._residual,
            self._certificate,
            self._composition_role_sha256,
        )
        return self._require_owner_snapshot(snapshot)

    def _live_components(
        self,
        expected_snapshot: object,
    ) -> Tuple[TotalizedJumpGuideCertificate, TotalizedResidualJumpCertificate]:
        (
            reference_composer,
            guide,
            residual,
            certificate,
            composition_role_sha256,
        ) = self._require_owner_snapshot(expected_snapshot)
        reference_composer._require_live_binding()
        self._require_owner_snapshot(expected_snapshot)
        checked_guide = require_matching_totalized_association_jump_guide(
            guide.preconditioner,
            guide,
            guide.range_gate,
            guide.range_certificate,
            observation=guide.outcome,
        )
        self._require_owner_snapshot(expected_snapshot)
        checked_residual = require_matching_totalized_conditional_jump_residual(
            residual.model,
            residual,
            residual.checkpoint,
            expected_provenance=residual.provenance,
        )
        self._require_owner_snapshot(expected_snapshot)
        residual_private = getattr(residual, "_evaluation_model", None)
        if type(residual_private) is not BoundedConfigurationEnergy:
            raise TypeError("private residual model has the wrong exact type")
        _require_disjoint_residual_model_state_storage(
            residual.model,
            residual_private,
        )
        self._require_owner_snapshot(expected_snapshot)
        process_key = reference_composer.process_parameter_key
        expected_process_sha = _plain_key_sha256(
            process_key,
            domain=b"heterodiff-configuration-initial-tilt-process-v1\x00",
        )
        for name, key in (
            ("guide", guide.preconditioner.process.parameter_key()),
            ("residual", residual.model.architecture.process_parameter_key),
        ):
            component_sha = _plain_key_sha256(
                key,
                domain=b"heterodiff-configuration-initial-tilt-process-v1\x00",
            )
            if component_sha != expected_process_sha:
                raise ValueError("%s component belongs to a different process" % name)
        horizon = reference_composer.process.schedule.horizon
        if not _same_float(
            checked_guide.certificate.reverse_time_horizon, horizon
        ) or not _same_float(checked_residual.certificate.schedule_horizon, horizon):
            raise ValueError("component horizons differ from the process horizon")
        if certificate.composer_runtime_sha256 != _runtime_sha256():
            raise ValueError("live composer runtime differs from certificate")
        expected = _make_certificate(
            reference_composer=reference_composer,
            guide_owner=guide,
            residual_owner=residual,
            guide_certificate=checked_guide.certificate,
            residual_certificate=checked_residual.certificate,
            residual_context_dimension=residual.model.architecture.context_dimension,
            composition_role_sha256=composition_role_sha256,
        )
        for name in _certificate_fields():
            if not _field_matches(
                name, getattr(certificate, name), getattr(expected, name)
            ):
                raise ValueError(
                    "initial-tilt certificate field %s differs from live state" % name
                )
        self._require_owner_snapshot(expected_snapshot)
        return checked_guide.certificate, checked_residual.certificate

    def _canonical_configuration(
        self,
        reference_composer: ProcessValidReferenceJumpComposer,
        configuration: object,
    ) -> TransformedConfiguration:
        canonical = reference_composer.process.reference.canonicalize(
            configuration  # type: ignore[arg-type]
        )
        copied = _copy_configuration(canonical)
        _configuration_sha256(copied)
        return copied

    def evaluate(
        self,
        configuration: object,
        *,
        residual_context: object,
    ) -> InitialTiltPointEvaluation:
        """Compose guide and residual at fixed ``u=0`` / ``s=S`` without RNG."""

        owner_snapshot = self._owner_snapshot()
        (
            reference_composer,
            guide,
            residual,
            certificate,
            _,
        ) = owner_snapshot
        pre_guide, pre_residual = self._live_components(owner_snapshot)
        _require_binary64_environment()
        self._require_owner_snapshot(owner_snapshot)
        canonical = self._canonical_configuration(reference_composer, configuration)
        self._require_owner_snapshot(owner_snapshot)
        configuration_sha = _configuration_sha256(canonical)
        context = _validated_context(
            residual_context,
            dimension=certificate.residual_context_dimension,
            name="residual_context",
        )
        self._require_owner_snapshot(owner_snapshot)
        guide_evaluation = guide.evaluate(0.0, canonical)
        self._require_owner_snapshot(owner_snapshot)
        if type(guide_evaluation) is not TotalizedJumpGuideEvaluation:
            raise TypeError("totalized guide returned the wrong exact point record")
        guide_evaluation = guide.validate_evaluation(guide_evaluation)
        self._require_owner_snapshot(owner_snapshot)
        if guide_evaluation.totalized_certificate_sha256 != (
            certificate.guide_totalized_certificate_sha256
        ):
            raise ValueError("guide point belongs to a different totalizer")
        if not _same_float(guide_evaluation.reverse_time, 0.0):
            raise ValueError("guide point was not evaluated at reverse time zero")
        if _configuration_sha256(guide_evaluation.state) != configuration_sha:
            raise ValueError(
                "guide point state differs from the canonical configuration"
            )
        if guide_evaluation.state != canonical:
            raise ValueError("guide point state value differs from the configuration")
        residual_batch = _pack_residual_configuration(
            residual.model,
            canonical,
            direct_time=certificate.direct_time,
            context=context,
        )
        residual_evaluation = residual.evaluate(residual_batch)
        self._require_owner_snapshot(owner_snapshot)
        if type(residual_evaluation) is not TotalizedResidualPointEvaluation:
            raise TypeError("totalized residual returned the wrong exact point record")
        residual_evaluation = residual.validate_evaluation(
            residual_evaluation, residual_batch
        )
        self._require_owner_snapshot(owner_snapshot)
        if residual_evaluation.certificate is not residual.certificate:
            raise ValueError("residual point belongs to a different totalizer")
        if not _same_float(residual_evaluation.direct_time, certificate.direct_time):
            raise ValueError("residual point was not evaluated at direct horizon")
        gate = _validated_fraction_parts(
            residual_evaluation.mathematical_gate_numerator,
            residual_evaluation.mathematical_gate_denominator,
            name="residual mathematical gate",
        )
        if gate != Fraction(1, 1):
            raise ValueError("direct-horizon residual gate does not equal one")
        post_guide, post_residual = self._live_components(owner_snapshot)
        if pre_guide.certificate_sha256 != post_guide.certificate_sha256:
            raise ConfigurationInitialTiltError(
                "guide certificate changed during point composition"
            )
        if pre_residual.certificate_sha256 != post_residual.certificate_sha256:
            raise ConfigurationInitialTiltError(
                "residual certificate changed during point composition"
            )
        _require_binary64_environment()
        exact = _require_fraction_size(
            _fraction(guide_evaluation.operational_log_density)
            + _fraction(residual_evaluation.operational_residual),
            name="initial log factor",
        )
        rounded = _round_fraction_once(exact, name="initial log factor")
        exact_error = _require_fraction_size(
            abs(_fraction(rounded) - exact), name="initial log-factor rounding error"
        )
        residual_bound = residual_evaluation.operational_point_magnitude_bound
        lower, upper = _outward_interval(
            guide_evaluation.operational_log_lower_bound,
            guide_evaluation.operational_log_upper_bound,
            residual_bound,
        )
        values = {
            "certificate": certificate,
            "certificate_sha256": certificate.certificate_sha256,
            "process_parameter_sha256": certificate.process_parameter_sha256,
            "reverse_time": 0.0,
            "direct_time": certificate.direct_time,
            "configuration": canonical,
            "configuration_sha256": configuration_sha,
            "residual_context": context,
            "residual_context_sha256": _context_sha256(context),
            "guide_evaluation_sha256": guide_evaluation.evaluation_sha256,
            "guide_branch": guide_evaluation.branch,
            "guide_operational_log_density": (guide_evaluation.operational_log_density),
            "guide_operational_log_lower_bound": (
                guide_evaluation.operational_log_lower_bound
            ),
            "guide_operational_log_upper_bound": (
                guide_evaluation.operational_log_upper_bound
            ),
            "guide_point_log_discrepancy_bound": (
                guide_evaluation.point_log_discrepancy_bound
            ),
            "residual_evaluation_sha256": residual_evaluation.evaluation_sha256,
            "residual_batch_sha256": residual_evaluation.batch_sha256,
            "residual_branch": residual_evaluation.branch,
            "residual_operational_value": residual_evaluation.operational_residual,
            "residual_operational_point_magnitude_bound": residual_bound,
            "residual_mathematical_gate_numerator": gate.numerator,
            "residual_mathematical_gate_denominator": gate.denominator,
            "exact_initial_log_factor_numerator": exact.numerator,
            "exact_initial_log_factor_denominator": exact.denominator,
            "initial_log_factor": rounded,
            "exact_rounding_error_numerator": exact_error.numerator,
            "exact_rounding_error_denominator": exact_error.denominator,
            "rounding_error_upper_bound": _outward_upper_fraction(
                exact_error, name="initial log-factor rounding error"
            ),
            "initial_log_factor_lower_bound": lower,
            "initial_log_factor_upper_bound": upper,
            "initial_log_factor_magnitude_bound": max(abs(lower), abs(upper)),
            "base_initial_law_policy": certificate.base_initial_law_policy,
            "target_policy": certificate.target_policy,
            "composition_policy": certificate.composition_policy,
            "rounding_algorithm": certificate.rounding_algorithm,
            "evaluation_sha256": "0" * 64,
        }
        values["evaluation_sha256"] = _semantic_digest(_evaluation_payload(values))
        result = InitialTiltPointEvaluation(
            **values,
            _construction_token=_EVALUATION_TOKEN,
        )
        self._live_components(owner_snapshot)
        self._require_owner_snapshot(owner_snapshot)
        return result

    def validate_evaluation(
        self,
        evaluation: object,
        configuration: object,
        *,
        residual_context: object,
    ) -> InitialTiltPointEvaluation:
        """Reconstruct and replay one point record against explicit inputs."""

        if type(evaluation) is not InitialTiltPointEvaluation:
            raise TypeError("evaluation must be an exact InitialTiltPointEvaluation")
        owner_snapshot = self._owner_snapshot()
        certificate = owner_snapshot[3]
        InitialTiltPointEvaluation(
            **{name: getattr(evaluation, name) for name in _evaluation_fields()},
            _construction_token=_EVALUATION_TOKEN,
        )
        self._require_owner_snapshot(owner_snapshot)
        if evaluation.certificate is not certificate:
            raise ValueError("point record belongs to a different composer certificate")
        expected = self.evaluate(
            configuration,
            residual_context=residual_context,
        )
        self._require_owner_snapshot(owner_snapshot)
        for name in _evaluation_fields():
            if not _field_matches(
                name, getattr(evaluation, name), getattr(expected, name)
            ):
                raise ValueError(
                    "initial-tilt point field %s differs from replay" % name
                )
        self._require_owner_snapshot(owner_snapshot)
        return evaluation


def _require_target_policy(target_policy: object) -> str:
    if type(target_policy) is not str:
        raise TypeError("target_policy must be exact text")
    if target_policy != CONFIGURATION_INITIAL_TILT_TARGET_POLICY:
        raise ValueError(
            "only the exported Pi_N-based operational initial log factor is "
            "supported; base-energy, analytic, or posterior targets cannot be inferred"
        )
    return target_policy


def _require_process_compatibility(
    reference_composer: ProcessValidReferenceJumpComposer,
    guide: TotalizedAssociationJumpGuide,
    residual: TotalizedConditionalJumpResidual,
) -> None:
    process_key = reference_composer.process_parameter_key
    expected_sha = _plain_key_sha256(
        process_key,
        domain=b"heterodiff-configuration-initial-tilt-process-v1\x00",
    )
    for name, key in (
        ("guide", guide.preconditioner.process.parameter_key()),
        ("residual", residual.model.architecture.process_parameter_key),
    ):
        component_sha = _plain_key_sha256(
            key,
            domain=b"heterodiff-configuration-initial-tilt-process-v1\x00",
        )
        if component_sha != expected_sha:
            raise ValueError("%s component belongs to a different process" % name)


def certify_configuration_initial_tilt_composer(
    reference_composer: ProcessValidReferenceJumpComposer,
    *,
    totalized_guide: TotalizedAssociationJumpGuide,
    totalized_residual: TotalizedConditionalJumpResidual,
    target_policy: object,
    composition_role_sha256: object,
) -> ConfigurationInitialTiltComposer:
    """Certify the deterministic time-zero guide-plus-residual log factor."""

    _require_target_policy(target_policy)
    role = _require_sha256(composition_role_sha256, name="composition_role_sha256")
    if type(reference_composer) is not ProcessValidReferenceJumpComposer:
        raise TypeError(
            "reference_composer must be an exact ProcessValidReferenceJumpComposer"
        )
    reference_composer._require_live_binding()
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
    residual = require_matching_totalized_conditional_jump_residual(
        totalized_residual.model,
        totalized_residual,
        totalized_residual.checkpoint,
        expected_provenance=totalized_residual.provenance,
    )
    _require_process_compatibility(reference_composer, guide, residual)
    horizon = reference_composer.process.schedule.horizon
    if not _same_float(
        guide.certificate.reverse_time_horizon, horizon
    ) or not _same_float(residual.certificate.schedule_horizon, horizon):
        raise ValueError("component horizons differ from the process horizon")
    certificate = _make_certificate(
        reference_composer=reference_composer,
        guide_owner=guide,
        residual_owner=residual,
        guide_certificate=guide.certificate,
        residual_certificate=residual.certificate,
        residual_context_dimension=residual.model.architecture.context_dimension,
        composition_role_sha256=role,
    )
    owner = ConfigurationInitialTiltComposer(
        reference_composer=reference_composer,
        guide=guide,
        residual=residual,
        composition_role_sha256=role,
        certificate=certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner_snapshot = owner._owner_snapshot()
    owner._live_components(owner_snapshot)
    return owner


def require_matching_configuration_initial_tilt_composer(
    reference_composer: ProcessValidReferenceJumpComposer,
    composer: ConfigurationInitialTiltComposer,
    *,
    totalized_guide: TotalizedAssociationJumpGuide,
    totalized_residual: TotalizedConditionalJumpResidual,
    target_policy: object,
    composition_role_sha256: object,
) -> ConfigurationInitialTiltComposer:
    """Require exact owner identities and fully reconstructed live custody."""

    _require_target_policy(target_policy)
    role = _require_sha256(composition_role_sha256, name="composition_role_sha256")
    if type(composer) is not ConfigurationInitialTiltComposer:
        raise TypeError("composer must be an exact ConfigurationInitialTiltComposer")
    if composer.reference_composer is not reference_composer:
        raise ValueError("composer is bound to a different reference composer")
    if composer.totalized_guide is not totalized_guide:
        raise ValueError("composer is bound to a different totalized guide")
    if composer.totalized_residual is not totalized_residual:
        raise ValueError("composer is bound to a different totalized residual")
    if composer.certificate.composition_role_sha256 != role:
        raise ValueError("composer is bound to a different composition role")
    owner_snapshot = composer._owner_snapshot()
    composer._live_components(owner_snapshot)
    return composer


def validate_configuration_initial_tilt_certificate(
    reference_composer: ProcessValidReferenceJumpComposer,
    composer: ConfigurationInitialTiltComposer,
    *,
    totalized_guide: TotalizedAssociationJumpGuide,
    totalized_residual: TotalizedConditionalJumpResidual,
    target_policy: object,
    composition_role_sha256: object,
) -> InitialTiltCompositionCertificate:
    """Return the fully reconstructed live initial-tilt certificate."""

    return require_matching_configuration_initial_tilt_composer(
        reference_composer,
        composer,
        totalized_guide=totalized_guide,
        totalized_residual=totalized_residual,
        target_policy=target_policy,
        composition_role_sha256=composition_role_sha256,
    ).certificate


__all__ = [
    "CONFIGURATION_INITIAL_TILT_BASE_LAW_POLICY",
    "CONFIGURATION_INITIAL_TILT_COMPOSITION_POLICY",
    "CONFIGURATION_INITIAL_TILT_FLOATING_POINT_POLICY",
    "CONFIGURATION_INITIAL_TILT_ROUNDING_ALGORITHM",
    "CONFIGURATION_INITIAL_TILT_SCHEMA_VERSION",
    "CONFIGURATION_INITIAL_TILT_SCOPE",
    "CONFIGURATION_INITIAL_TILT_TARGET_POLICY",
    "MAX_INITIAL_TILT_EXACT_INTEGER_BITS",
    "MAX_INITIAL_TILT_RUNTIME_IDENTITY",
    "ConfigurationInitialTiltComposer",
    "ConfigurationInitialTiltError",
    "InitialTiltCompositionCertificate",
    "InitialTiltPointEvaluation",
    "certify_configuration_initial_tilt_composer",
    "require_matching_configuration_initial_tilt_composer",
    "validate_configuration_initial_tilt_certificate",
]
