"""Jump-only operational extension for unresolved residual boundary gates.

Checkpoint thirteen deliberately refuses a strictly active cubic boundary gate
when its staged binary64 value is subnormal or zero.  This module leaves that
contract unchanged and defines a separate point function for jump composition.
Successful certified residual point values are preserved bit for bit.  Only
the dedicated gate-resolution refusal activates the extension: the exact
rational cubic gate induced by the represented time endpoints is multiplied
by the represented bounded-core value, and that product is rounded once to
binary64.

The result is an operational surrogate.  In particular, the represented core
is not an exact real-arithmetic neural-network evaluation.  This module
certifies no small forward error, derivative, drift, exponentiated rate,
clock, randomness, path, or sampler.  Every failure other than the one typed
gate-resolution refusal remains a failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
import platform
import struct
import sys
from typing import Mapping, Optional, Tuple

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.configuration_totalized_jump_residual_torch "
            "requires the optional PyTorch dependency; install the "
            "'reference' extra"
        ) from error
    raise

from heterodiff.artifacts.manifest import canonical_config_digest
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy,
    TypedConfigurationBatch,
    pack_typed_configuration_batch,
)
from heterodiff.models.configuration_residual_torch import (
    CertifiedConditionalResidualCheckpoint,
    ConditionalResidualProvenance,
    ConfigurationResidualGateResolutionError,
    certified_configuration_residual,
    materialize_conditional_residual_checkpoint,
    require_matching_conditional_residual_certificate,
    _validate_model_and_batch,
)


CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCHEMA_VERSION = (
    "configuration-totalized-jump-residual-torch-v1"
)
CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_POLICY = (
    "preserve-certified-residual-point-success-bitwise;"
    "only-typed-active-tiny-gate-refusal-uses-exact-rational-cubic-gate-"
    "times-represented-bounded-core-rounded-once;"
    "all-state-pair-values-are-exact-operational-endpoint-differences;"
    "never-catch-input-resource-custody-core-or-generic-arithmetic-failure"
)
CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCOPE = (
    "single-row-same-condition-state-pair;jump-only;trusted-unmodified-"
    "python-torch-runtime;operational-surrogate-on-exact-rescaling-branch;"
    "not-real-neural-forward-error-certificate;not-exact-conditional-or-"
    "posterior-target;not-coordinate-or-time-derivative;not-drift;not-rate-"
    "envelope;not-clock;not-rng;not-path;not-sampler-admission"
)
CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_ROUNDING_ALGORITHM = (
    "exact-fraction-mathematical-cubic-gate-times-represented-core-"
    "rounded-once-to-binary64-nearest-even;exact-operational-endpoint-"
    "difference-rounded-once-to-binary64-nearest-even;zero-canonicalized-positive"
)
CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_FLOATING_POINT_POLICY = (
    "binary64-round-to-nearest-even-and-gradual-underflow-required;"
    "live-arithmetic-probe-replayed-before-and-after-evaluation"
)

PRESERVED_CERTIFIED_RESIDUAL_BRANCH = "preserved-certified-residual"
EXACT_GATE_RESCALED_CORE_BRANCH = "exact-gate-rescaled-core"
_BRANCHES = (
    PRESERVED_CERTIFIED_RESIDUAL_BRANCH,
    EXACT_GATE_RESCALED_CORE_BRANCH,
)

MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS = 8192
_MIN_NORMAL_FLOAT64 = float.fromhex("0x1.0p-1022")

_CERTIFICATE_TOKEN = object()
_EVALUATION_TOKEN = object()
_DIFFERENCE_TOKEN = object()
_OWNER_TOKEN = object()


class ConfigurationResidualJumpTotalizationError(ArithmeticError):
    """Raised when the operational extension itself is unrepresentable."""


def _canonical_zero(value: float) -> float:
    return 0.0 if value == 0.0 else value


def _same_float(left: float, right: float) -> bool:
    return struct.pack(">d", left) == struct.pack(">d", right)


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be text" % name)
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
) -> float:
    if type(value) is not float:
        raise TypeError("%s must be an exact binary64 float" % name)
    if not math.isfinite(value):
        raise ValueError("%s must be finite" % name)
    if nonnegative and value < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    if strictly_positive and not value > 0.0:
        raise ValueError("%s must be strictly positive" % name)
    return value


def _validated_optional_float(value: object, *, name: str) -> Optional[float]:
    if value is None:
        return None
    return _validated_float(value, name=name)


def _fraction(value: float) -> Fraction:
    numerator, denominator = value.as_integer_ratio()
    return Fraction(numerator, denominator)


def _require_fraction_size(value: Fraction, *, name: str) -> Fraction:
    if value.numerator.bit_length() > MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS:
        raise ConfigurationResidualJumpTotalizationError(
            "%s numerator exceeds the exact-integer resource limit" % name
        )
    if value.denominator.bit_length() > MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS:
        raise ConfigurationResidualJumpTotalizationError(
            "%s denominator exceeds the exact-integer resource limit" % name
        )
    return value


def _validated_fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    if type(numerator) is not int or isinstance(numerator, bool):
        raise TypeError("%s numerator must be an exact integer" % name)
    if type(denominator) is not int or isinstance(denominator, bool):
        raise TypeError("%s denominator must be an exact integer" % name)
    if denominator <= 0:
        raise ValueError("%s denominator must be positive" % name)
    if numerator.bit_length() > MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS:
        raise ValueError("%s numerator exceeds the exact-integer limit" % name)
    if denominator.bit_length() > MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS:
        raise ValueError("%s denominator exceeds the exact-integer limit" % name)
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        raise ValueError("%s fraction must be in canonical lowest terms" % name)
    return result


def _validated_optional_fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Optional[Fraction]:
    if numerator is None and denominator is None:
        return None
    if numerator is None or denominator is None:
        raise ValueError("%s fraction fields must both be present or absent" % name)
    return _validated_fraction_parts(numerator, denominator, name=name)


def _rounded_fraction(value: Fraction, *, name: str) -> float:
    _require_fraction_size(value, name=name)
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ConfigurationResidualJumpTotalizationError(
            "%s has no finite binary64 rounding" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationResidualJumpTotalizationError(
            "%s has no finite binary64 rounding" % name
        )
    return _canonical_zero(result)


def _outward_nonnegative_fraction(value: Fraction, *, name: str) -> float:
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    _require_fraction_size(value, name=name)
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ConfigurationResidualJumpTotalizationError(
            "%s has no finite binary64 upper witness" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationResidualJumpTotalizationError(
            "%s has no finite binary64 upper witness" % name
        )
    if _fraction(result) < value:
        result = math.nextafter(result, math.inf)
    if not math.isfinite(result):
        raise ConfigurationResidualJumpTotalizationError(
            "%s cannot be rounded outward" % name
        )
    return _canonical_zero(result)


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
        {"configuration_totalized_residual": _typed_digest_value(value)}
    )


def _floating_point_environment_probe() -> Tuple[str, ...]:
    """Observe the arithmetic modes used by this checkpoint without mutation."""

    minimum_normal = struct.unpack(">d", bytes.fromhex("0010000000000000"))[0]
    half_minimum_normal = minimum_normal * 0.5
    minimum_subnormal = struct.unpack(">d", bytes.fromhex("0000000000000001"))[0]
    consumed_half_minimum_normal = half_minimum_normal + half_minimum_normal
    consumed_minimum_subnormal = minimum_subnormal + minimum_subnormal
    with torch.no_grad():
        torch_half_minimum_normal = torch.tensor(
            half_minimum_normal,
            dtype=torch.float64,
            device="cpu",
        )
        torch_consumed_half_minimum_normal = float(
            (torch_half_minimum_normal + torch_half_minimum_normal).item()
        )
    one = struct.unpack(">d", bytes.fromhex("3ff0000000000000"))[0]
    positive_tie = one + math.ldexp(1.0, -53)
    negative_quarter_ulp = one - math.ldexp(1.0, -54)
    next_positive = math.nextafter(0.0, math.inf)
    return tuple(
        struct.pack(">d", value).hex()
        for value in (
            half_minimum_normal,
            consumed_half_minimum_normal,
            consumed_minimum_subnormal,
            torch_consumed_half_minimum_normal,
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
        raise ConfigurationResidualJumpTotalizationError(
            "totalized residual requires round-to-nearest-even binary64 "
            "arithmetic with gradual underflow"
        )
    return observed


def _runtime_sha256() -> str:
    floating_point_probe = _require_binary64_environment()
    return _semantic_digest(
        {
            "domain": "configuration-totalized-jump-residual-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "torch_version": str(torch.__version__),
            "schema_version": CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCHEMA_VERSION,
            "floating_point_environment_policy": (
                CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_FLOATING_POINT_POLICY
            ),
            "floating_point_environment_probe": floating_point_probe,
        }
    )


def _hash_tensor(digest: "hashlib._Hash", name: str, value: torch.Tensor) -> None:
    detached = value.detach().contiguous()
    fields = (
        name.encode("utf-8"),
        str(detached.dtype).encode("ascii"),
        repr(tuple(detached.shape)).encode("ascii"),
        detached.numpy().tobytes(order="C"),
    )
    for field in fields:
        digest.update(len(field).to_bytes(8, "big"))
        digest.update(field)


def _batch_sha256(batch: TypedConfigurationBatch) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-totalized-residual-batch-v1\x00")
    digest.update(batch.architecture_sha256.encode("ascii"))
    digest.update(batch.batch_size.to_bytes(8, "big"))
    digest.update(batch.total_occurrences.to_bytes(8, "big"))
    digest.update(batch.total_coordinates.to_bytes(8, "big"))
    _hash_tensor(digest, "forward_time", batch.forward_time)
    _hash_tensor(digest, "context", batch.context)
    for index, (event_type, coordinates, owners) in enumerate(
        zip(batch.type_ids, batch.coordinates, batch.batch_indices)
    ):
        digest.update(index.to_bytes(8, "big"))
        digest.update(event_type.to_bytes(8, "big", signed=False))
        _hash_tensor(digest, "coordinates[%d]" % index, coordinates)
        _hash_tensor(digest, "owners[%d]" % index, owners)
    return digest.hexdigest()


def _exact_mathematical_gate(
    direct_time: float,
    clean_hold: float,
    schedule_horizon: float,
) -> Fraction:
    if direct_time <= clean_hold:
        return Fraction(0, 1)
    numerator = _fraction(direct_time) - _fraction(clean_hold)
    duration = _fraction(schedule_horizon) - _fraction(clean_hold)
    if numerator <= 0 or duration <= 0 or numerator > duration:
        raise ValueError("direct time is inconsistent with the residual boundary")
    return _require_fraction_size(
        (numerator / duration) ** 3,
        name="exact mathematical gate",
    )


def _legacy_staged_gate(
    direct_time: float,
    clean_hold: float,
    active_reverse_duration: float,
) -> float:
    """Mirror checkpoint thirteen's scalar staging for branch verification."""

    if direct_time <= clean_hold:
        return 0.0
    ratio = (direct_time - clean_hold) / active_reverse_duration
    return (ratio * ratio) * ratio


def _expected_point_branch(
    direct_time: float,
    clean_hold: float,
    active_reverse_duration: float,
) -> str:
    legacy_gate = _legacy_staged_gate(
        direct_time,
        clean_hold,
        active_reverse_duration,
    )
    if not math.isfinite(legacy_gate) or not 0.0 <= legacy_gate <= 1.0:
        raise ValueError("recorded time has no admissible staged residual gate")
    if direct_time > clean_hold and legacy_gate < _MIN_NORMAL_FLOAT64:
        return EXACT_GATE_RESCALED_CORE_BRANCH
    return PRESERVED_CERTIFIED_RESIDUAL_BRANCH


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: value for name, value in values.items() if name != "certificate_sha256"
    }


@dataclass(frozen=True, eq=False, init=False)
class TotalizedResidualJumpCertificate:
    """Sealed custody and claim boundary for the jump-only extension."""

    schema_version: str
    certificate_scope: str
    totalization_policy: str
    rounding_algorithm: str
    floating_point_environment_policy: str
    residual_contract_sha256: str
    core_architecture_sha256: str
    process_parameter_sha256: str
    context_schema_sha256: str
    observation_schema_sha256: str
    task_schema_sha256: str
    conditioning_adapter_sha256: str
    residual_role_sha256: str
    core_checkpoint_sha256: str
    core_certificate_sha256: str
    residual_certificate_sha256: str
    residual_provenance_sha256: str
    residual_runtime_sha256: str
    evaluator_runtime_sha256: str
    schedule_horizon: float
    clean_hold: float
    active_reverse_duration: float
    global_point_magnitude_bound: float
    global_edge_magnitude_bound: float
    maximum_exact_integer_bits: int
    successful_point_values_preserved: bool
    successful_state_pair_bits_preserved: bool
    tiny_gate_exact_rescaling: bool
    small_forward_error_certified: bool
    coordinate_derivatives_admissible: bool
    time_derivatives_admissible: bool
    continuous_drift_admissible: bool
    rate_space_envelope_admissible: bool
    controlled_clock_admissible: bool
    randomness_admissible: bool
    path_admissible: bool
    operational_sampler_admissible: bool
    exact_conditional_or_posterior_target: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedResidualJumpCertificate cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("totalized residual certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("totalized residual certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    @property
    def jump_only(self) -> bool:
        return True

    @property
    def defines_operational_surrogate_jump_residual(self) -> bool:
        return True

    @property
    def exact_mathematical_residual_preserved(self) -> bool:
        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "totalized-conditional-jump-residual-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("totalized residual certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(TotalizedResidualJumpCertificate.__annotations__)


def _make_certificate(
    checkpoint: CertifiedConditionalResidualCheckpoint,
    provenance: ConditionalResidualProvenance,
) -> TotalizedResidualJumpCertificate:
    source = checkpoint.certificate
    values: dict[str, object] = {
        "schema_version": CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCOPE,
        "totalization_policy": CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_POLICY,
        "rounding_algorithm": (
            CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_ROUNDING_ALGORITHM
        ),
        "floating_point_environment_policy": (
            CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_FLOATING_POINT_POLICY
        ),
        "residual_contract_sha256": source.contract_sha256,
        "core_architecture_sha256": source.core_architecture_sha256,
        "process_parameter_sha256": source.process_parameter_sha256,
        "context_schema_sha256": source.context_schema_sha256,
        "observation_schema_sha256": source.observation_schema_sha256,
        "task_schema_sha256": source.task_schema_sha256,
        "conditioning_adapter_sha256": source.conditioning_adapter_sha256,
        "residual_role_sha256": source.residual_role_sha256,
        "core_checkpoint_sha256": source.core_checkpoint_sha256,
        "core_certificate_sha256": source.core_certificate_sha256,
        "residual_certificate_sha256": source.certificate_sha256,
        "residual_provenance_sha256": provenance.sha256,
        "residual_runtime_sha256": source.runtime_sha256,
        "evaluator_runtime_sha256": _runtime_sha256(),
        "schedule_horizon": source.schedule_horizon,
        "clean_hold": source.clean_hold,
        "active_reverse_duration": source.active_reverse_duration,
        "global_point_magnitude_bound": source.value_bound,
        "global_edge_magnitude_bound": source.edge_difference_bound,
        "maximum_exact_integer_bits": (MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS),
        "successful_point_values_preserved": True,
        "successful_state_pair_bits_preserved": False,
        "tiny_gate_exact_rescaling": True,
        "small_forward_error_certified": False,
        "coordinate_derivatives_admissible": False,
        "time_derivatives_admissible": False,
        "continuous_drift_admissible": False,
        "rate_space_envelope_admissible": False,
        "controlled_clock_admissible": False,
        "randomness_admissible": False,
        "path_admissible": False,
        "operational_sampler_admissible": False,
        "exact_conditional_or_posterior_target": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return TotalizedResidualJumpCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _validate_certificate(
    certificate: object,
) -> TotalizedResidualJumpCertificate:
    if type(certificate) is not TotalizedResidualJumpCertificate:
        raise TypeError("certificate must be an exact TotalizedResidualJumpCertificate")
    for name in (
        "residual_contract_sha256",
        "core_architecture_sha256",
        "process_parameter_sha256",
        "context_schema_sha256",
        "observation_schema_sha256",
        "task_schema_sha256",
        "conditioning_adapter_sha256",
        "residual_role_sha256",
        "core_checkpoint_sha256",
        "core_certificate_sha256",
        "residual_certificate_sha256",
        "residual_provenance_sha256",
        "residual_runtime_sha256",
        "evaluator_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    if certificate.schema_version != (
        CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCHEMA_VERSION
    ):
        raise ValueError("totalized residual schema is inconsistent")
    if certificate.certificate_scope != CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCOPE:
        raise ValueError("totalized residual scope is inconsistent")
    if certificate.totalization_policy != (
        CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_POLICY
    ):
        raise ValueError("totalized residual policy is inconsistent")
    if certificate.rounding_algorithm != (
        CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_ROUNDING_ALGORITHM
    ):
        raise ValueError("totalized residual rounding algorithm is inconsistent")
    if certificate.floating_point_environment_policy != (
        CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_FLOATING_POINT_POLICY
    ):
        raise ValueError("totalized residual floating-point policy is inconsistent")
    _validated_float(
        certificate.schedule_horizon,
        name="certificate.schedule_horizon",
        strictly_positive=True,
    )
    _validated_float(
        certificate.clean_hold,
        name="certificate.clean_hold",
        nonnegative=True,
    )
    _validated_float(
        certificate.active_reverse_duration,
        name="certificate.active_reverse_duration",
        strictly_positive=True,
    )
    if not certificate.clean_hold < certificate.schedule_horizon:
        raise ValueError("certificate clean hold must precede its horizon")
    if not _same_float(
        certificate.active_reverse_duration,
        certificate.schedule_horizon - certificate.clean_hold,
    ):
        raise ValueError("certificate active duration is inconsistent")
    _validated_float(
        certificate.global_point_magnitude_bound,
        name="certificate.global_point_magnitude_bound",
        strictly_positive=True,
    )
    _validated_float(
        certificate.global_edge_magnitude_bound,
        name="certificate.global_edge_magnitude_bound",
        strictly_positive=True,
    )
    if certificate.global_edge_magnitude_bound != (
        2.0 * certificate.global_point_magnitude_bound
    ):
        raise ValueError("certificate global edge bound is inconsistent")
    if type(certificate.maximum_exact_integer_bits) is not int or isinstance(
        certificate.maximum_exact_integer_bits, bool
    ):
        raise TypeError("certificate exact-integer limit must be an exact integer")
    if certificate.maximum_exact_integer_bits != (
        MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS
    ):
        raise ValueError("certificate exact-integer limit is inconsistent")
    true_flags = (
        "successful_point_values_preserved",
        "tiny_gate_exact_rescaling",
        "passed",
    )
    false_flags = (
        "successful_state_pair_bits_preserved",
        "small_forward_error_certified",
        "coordinate_derivatives_admissible",
        "time_derivatives_admissible",
        "continuous_drift_admissible",
        "rate_space_envelope_admissible",
        "controlled_clock_admissible",
        "randomness_admissible",
        "path_admissible",
        "operational_sampler_admissible",
        "exact_conditional_or_posterior_target",
    )
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("totalized residual positive claim flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("totalized residual negative claim flags are inconsistent")
    expected = _semantic_digest(
        _certificate_payload(
            {name: getattr(certificate, name) for name in _certificate_fields()}
        )
    )
    if certificate.certificate_sha256 != expected:
        raise ValueError("totalized residual certificate digest is inconsistent")
    return certificate


def _evaluation_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "evaluation_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class TotalizedResidualPointEvaluation:
    """One replayable point evaluation of the operational jump residual."""

    certificate: TotalizedResidualJumpCertificate
    certificate_sha256: str
    residual_certificate_sha256: str
    batch_sha256: str
    direct_time: float
    branch: str
    legacy_residual_value: Optional[float]
    fallback_core_value: Optional[float]
    mathematical_gate_numerator: int
    mathematical_gate_denominator: int
    mathematical_gate_upper_bound: float
    exact_rescaled_core_product_numerator: Optional[int]
    exact_rescaled_core_product_denominator: Optional[int]
    operational_residual: float
    exact_fallback_rounding_error_numerator: Optional[int]
    exact_fallback_rounding_error_denominator: Optional[int]
    fallback_rounding_error_upper_bound: Optional[float]
    operational_point_magnitude_bound: float
    evaluation_algorithm: str
    totalization_policy: str
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedResidualPointEvaluation cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError("totalized residual point records are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("totalized residual point fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("point certificate digest differs from its certificate")
        if values["residual_certificate_sha256"] != (
            certificate.residual_certificate_sha256
        ):
            raise ValueError("point residual certificate digest is inconsistent")
        _require_sha256(values["batch_sha256"], name="point.batch_sha256")
        _require_sha256(values["evaluation_sha256"], name="point.evaluation_sha256")
        direct_time = _validated_float(
            values["direct_time"], name="point.direct_time", nonnegative=True
        )
        if direct_time > certificate.schedule_horizon:
            raise ValueError("point direct time lies outside the horizon")
        if values["branch"] not in _BRANCHES:
            raise ValueError("unknown totalized residual point branch")
        expected_branch = _expected_point_branch(
            direct_time,
            certificate.clean_hold,
            certificate.active_reverse_duration,
        )
        if values["branch"] != expected_branch:
            raise ValueError("point branch is inconsistent with its direct time")
        if values["totalization_policy"] != certificate.totalization_policy:
            raise ValueError("point totalization policy is inconsistent")
        expected_gate = _exact_mathematical_gate(
            direct_time,
            certificate.clean_hold,
            certificate.schedule_horizon,
        )
        supplied_gate = _validated_fraction_parts(
            values["mathematical_gate_numerator"],
            values["mathematical_gate_denominator"],
            name="point mathematical gate",
        )
        if supplied_gate != expected_gate:
            raise ValueError("point mathematical gate is inconsistent")
        gate_upper = _validated_float(
            values["mathematical_gate_upper_bound"],
            name="point.mathematical_gate_upper_bound",
            nonnegative=True,
        )
        if not _same_float(
            gate_upper,
            _outward_nonnegative_fraction(
                expected_gate, name="point mathematical gate"
            ),
        ):
            raise ValueError("point mathematical gate upper bound is inconsistent")
        operational = _validated_float(
            values["operational_residual"], name="point.operational_residual"
        )
        legacy = _validated_optional_float(
            values["legacy_residual_value"], name="point.legacy_residual_value"
        )
        core = _validated_optional_float(
            values["fallback_core_value"], name="point.fallback_core_value"
        )
        exact_product = _validated_optional_fraction_parts(
            values["exact_rescaled_core_product_numerator"],
            values["exact_rescaled_core_product_denominator"],
            name="point exact rescaled product",
        )
        exact_error = _validated_optional_fraction_parts(
            values["exact_fallback_rounding_error_numerator"],
            values["exact_fallback_rounding_error_denominator"],
            name="point exact fallback rounding error",
        )
        error_upper = values["fallback_rounding_error_upper_bound"]
        magnitude_bound = _validated_float(
            values["operational_point_magnitude_bound"],
            name="point.operational_point_magnitude_bound",
            nonnegative=True,
        )
        if values["branch"] == PRESERVED_CERTIFIED_RESIDUAL_BRANCH:
            if legacy is None or not _same_float(legacy, operational):
                raise ValueError("preserved point must retain its legacy value")
            if any(
                value is not None
                for value in (core, exact_product, exact_error, error_upper)
            ):
                raise ValueError("preserved point carries fallback-only fields")
            if values["evaluation_algorithm"] != (
                "certified-residual-point-preserved-bitwise-v1"
            ):
                raise ValueError("preserved point algorithm is inconsistent")
            expected_magnitude = certificate.global_point_magnitude_bound
        else:
            if legacy is not None or core is None or exact_product is None:
                raise ValueError("rescaled point fields are incomplete")
            if abs(core) > certificate.global_point_magnitude_bound:
                raise ValueError("rescaled point core exceeds its certified bound")
            if operational == 0.0 and math.copysign(1.0, operational) < 0.0:
                raise ValueError(
                    "rescaled point operational zero must be canonical positive zero"
                )
            if direct_time <= certificate.clean_hold:
                raise ValueError("rescaled point must be strictly active")
            legacy_gate = _legacy_staged_gate(
                direct_time,
                certificate.clean_hold,
                certificate.active_reverse_duration,
            )
            if not math.isfinite(legacy_gate) or not (
                0.0 <= legacy_gate < _MIN_NORMAL_FLOAT64
            ):
                raise ValueError(
                    "rescaled point does not lie on the typed tiny-gate branch"
                )
            if exact_product != expected_gate * _fraction(core):
                raise ValueError("rescaled point exact product is inconsistent")
            if not _same_float(
                operational,
                _rounded_fraction(exact_product, name="rescaled core product"),
            ):
                raise ValueError("rescaled point rounding is inconsistent")
            expected_error = abs(_fraction(operational) - exact_product)
            if exact_error != expected_error:
                raise ValueError("rescaled point exact rounding error is inconsistent")
            if error_upper is None:
                raise ValueError("rescaled point lacks a rounding-error witness")
            checked_error_upper = _validated_float(
                error_upper,
                name="point.fallback_rounding_error_upper_bound",
                nonnegative=True,
            )
            if not _same_float(
                checked_error_upper,
                _outward_nonnegative_fraction(
                    expected_error, name="fallback rounding error"
                ),
            ):
                raise ValueError("fallback rounding-error bound is inconsistent")
            if values["evaluation_algorithm"] != (
                CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_ROUNDING_ALGORITHM
            ):
                raise ValueError("rescaled point algorithm is inconsistent")
            expected_magnitude = _outward_nonnegative_fraction(
                expected_gate * _fraction(certificate.global_point_magnitude_bound),
                name="rescaled point magnitude bound",
            )
        if not _same_float(magnitude_bound, expected_magnitude):
            raise ValueError("point magnitude bound is inconsistent")
        if abs(operational) > magnitude_bound:
            raise ValueError("point exceeds its operational magnitude bound")
        expected_digest = _semantic_digest(_evaluation_payload(values))
        if values["evaluation_sha256"] != expected_digest:
            raise ValueError("point evaluation digest is inconsistent")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    @property
    def fallback_used(self) -> bool:
        return self.branch == EXACT_GATE_RESCALED_CORE_BRANCH

    @property
    def raw_value_preserved(self) -> bool:
        return self.branch == PRESERVED_CERTIFIED_RESIDUAL_BRANCH

    @property
    def jump_only(self) -> bool:
        return True

    @property
    def defines_operational_surrogate_jump_residual(self) -> bool:
        return True

    @property
    def exact_conditional_or_posterior_target(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("totalized residual point records are not pickle objects")


def _evaluation_fields() -> Tuple[str, ...]:
    return tuple(TotalizedResidualPointEvaluation.__annotations__)


def _difference_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {"certificate", "difference_sha256"}
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class TotalizedResidualJumpDifference:
    """Exact endpoint coboundary plus one rounded operational difference."""

    certificate: TotalizedResidualJumpCertificate
    certificate_sha256: str
    source_batch_sha256: str
    destination_batch_sha256: str
    direct_time: float
    source_evaluation_sha256: str
    destination_evaluation_sha256: str
    source_branch: str
    destination_branch: str
    source_operational_residual: float
    destination_operational_residual: float
    exact_operational_endpoint_difference_numerator: int
    exact_operational_endpoint_difference_denominator: int
    operational_difference: float
    exact_rounding_error_numerator: int
    exact_rounding_error_denominator: int
    rounding_error_upper_bound: float
    operational_edge_magnitude_bound: float
    difference_algorithm: str
    totalization_policy: str
    difference_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedResidualJumpDifference cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _DIFFERENCE_TOKEN:
            raise TypeError("totalized residual difference records are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("totalized residual difference fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("difference certificate digest is inconsistent")
        for name in (
            "source_batch_sha256",
            "destination_batch_sha256",
            "source_evaluation_sha256",
            "destination_evaluation_sha256",
            "difference_sha256",
        ):
            _require_sha256(values[name], name="difference.%s" % name)
        direct_time = _validated_float(
            values["direct_time"], name="difference.direct_time", nonnegative=True
        )
        if direct_time > certificate.schedule_horizon:
            raise ValueError("difference direct time lies outside the horizon")
        if (
            values["source_branch"] not in _BRANCHES
            or values["destination_branch"] not in _BRANCHES
        ):
            raise ValueError("difference contains an unknown point branch")
        if values["source_branch"] != values["destination_branch"]:
            raise ValueError("same-time residual endpoints must use the same branch")
        expected_branch = _expected_point_branch(
            direct_time,
            certificate.clean_hold,
            certificate.active_reverse_duration,
        )
        if values["source_branch"] != expected_branch:
            raise ValueError("difference branches are inconsistent with direct time")
        source = _validated_float(
            values["source_operational_residual"],
            name="difference.source_operational_residual",
        )
        destination = _validated_float(
            values["destination_operational_residual"],
            name="difference.destination_operational_residual",
        )
        endpoint_bound = certificate.global_point_magnitude_bound
        if expected_branch == EXACT_GATE_RESCALED_CORE_BRANCH:
            exact_gate = _exact_mathematical_gate(
                direct_time,
                certificate.clean_hold,
                certificate.schedule_horizon,
            )
            endpoint_bound = _outward_nonnegative_fraction(
                exact_gate * _fraction(certificate.global_point_magnitude_bound),
                name="difference fallback endpoint magnitude bound",
            )
        if abs(source) > endpoint_bound:
            raise ValueError(
                "difference source endpoint exceeds its admissible point bound"
            )
        if abs(destination) > endpoint_bound:
            raise ValueError(
                "difference destination endpoint exceeds its admissible point bound"
            )
        exact = _validated_fraction_parts(
            values["exact_operational_endpoint_difference_numerator"],
            values["exact_operational_endpoint_difference_denominator"],
            name="exact operational endpoint difference",
        )
        expected_exact = _fraction(destination) - _fraction(source)
        if exact != expected_exact:
            raise ValueError("exact endpoint difference is inconsistent")
        operational = _validated_float(
            values["operational_difference"],
            name="difference.operational_difference",
        )
        if not _same_float(
            operational,
            _rounded_fraction(exact, name="operational endpoint difference"),
        ):
            raise ValueError("operational endpoint difference is inconsistent")
        exact_error = _validated_fraction_parts(
            values["exact_rounding_error_numerator"],
            values["exact_rounding_error_denominator"],
            name="difference exact rounding error",
        )
        expected_error = abs(_fraction(operational) - exact)
        if exact_error != expected_error:
            raise ValueError("difference exact rounding error is inconsistent")
        upper = _validated_float(
            values["rounding_error_upper_bound"],
            name="difference.rounding_error_upper_bound",
            nonnegative=True,
        )
        if not _same_float(
            upper,
            _outward_nonnegative_fraction(
                expected_error, name="difference rounding error"
            ),
        ):
            raise ValueError("difference rounding-error bound is inconsistent")
        edge_bound = _validated_float(
            values["operational_edge_magnitude_bound"],
            name="difference.operational_edge_magnitude_bound",
            nonnegative=True,
        )
        if not _same_float(edge_bound, certificate.global_edge_magnitude_bound):
            raise ValueError("difference magnitude bound is inconsistent")
        if abs(operational) > edge_bound:
            raise ValueError("operational difference exceeds its global bound")
        if values["difference_algorithm"] != (
            "exact-operational-endpoint-difference-rounded-once-v1"
        ):
            raise ValueError("difference algorithm is inconsistent")
        if values["totalization_policy"] != certificate.totalization_policy:
            raise ValueError("difference totalization policy is inconsistent")
        expected_digest = _semantic_digest(_difference_payload(values))
        if values["difference_sha256"] != expected_digest:
            raise ValueError("difference digest is inconsistent")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    @property
    def fallback_used(self) -> bool:
        return self.source_branch == EXACT_GATE_RESCALED_CORE_BRANCH

    @property
    def jump_only(self) -> bool:
        return True

    @property
    def defines_operational_surrogate_jump_residual(self) -> bool:
        return True

    @property
    def exact_conditional_or_posterior_target(self) -> bool:
        return False

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("totalized residual difference records are not pickle objects")


def _difference_fields() -> Tuple[str, ...]:
    return tuple(TotalizedResidualJumpDifference.__annotations__)


def _record_values(record: object, names: Tuple[str, ...]) -> dict[str, object]:
    return {name: getattr(record, name) for name in names}


def _field_matches(name: str, supplied: object, expected: object) -> bool:
    if name == "certificate":
        return supplied is expected
    if type(supplied) is float and type(expected) is float:
        return _same_float(supplied, expected)
    return supplied == expected


class TotalizedConditionalJumpResidual:
    """Immutable owner of one checkpoint-bound operational point function."""

    __slots__ = (
        "_model",
        "_evaluation_model",
        "_checkpoint",
        "_provenance",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("TotalizedConditionalJumpResidual cannot be subclassed")

    def __init__(
        self,
        model: BoundedConfigurationEnergy,
        evaluation_model: BoundedConfigurationEnergy,
        checkpoint: CertifiedConditionalResidualCheckpoint,
        provenance: ConditionalResidualProvenance,
        certificate: TotalizedResidualJumpCertificate,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("totalized residual owners are certification-factory-only")
        if type(model) is not BoundedConfigurationEnergy:
            raise TypeError("model must be an exact BoundedConfigurationEnergy")
        if type(evaluation_model) is not BoundedConfigurationEnergy:
            raise TypeError(
                "evaluation_model must be an exact BoundedConfigurationEnergy"
            )
        if evaluation_model is model:
            raise ValueError("the private evaluation model must have separate custody")
        if type(checkpoint) is not CertifiedConditionalResidualCheckpoint:
            raise TypeError(
                "checkpoint must be an exact CertifiedConditionalResidualCheckpoint"
            )
        if type(provenance) is not ConditionalResidualProvenance:
            raise TypeError("provenance must be an exact ConditionalResidualProvenance")
        _validate_certificate(certificate)
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_evaluation_model", evaluation_model)
        object.__setattr__(self, "_checkpoint", checkpoint)
        object.__setattr__(self, "_provenance", provenance)
        object.__setattr__(self, "_certificate", certificate)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("TotalizedConditionalJumpResidual is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("TotalizedConditionalJumpResidual is immutable")

    def __reduce__(self) -> object:
        raise TypeError("totalized residual owners are not pickleable")

    @property
    def model(self) -> BoundedConfigurationEnergy:
        return self._model

    @property
    def checkpoint(self) -> CertifiedConditionalResidualCheckpoint:
        return self._checkpoint

    @property
    def provenance(self) -> ConditionalResidualProvenance:
        return self._provenance

    @property
    def certificate(self) -> TotalizedResidualJumpCertificate:
        return self._certificate

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "totalized-conditional-jump-residual-v1",
            self.certificate.parameter_key(),
        )

    def _require_live_binding(self) -> None:
        _require_binary64_environment()
        _validate_certificate(self.certificate)
        source = require_matching_conditional_residual_certificate(
            self.model,
            self.checkpoint,
            expected_provenance=self.provenance,
        )
        evaluation_source = require_matching_conditional_residual_certificate(
            self._evaluation_model,
            self.checkpoint,
            expected_provenance=self.provenance,
        )
        if source.certificate_sha256 != (self.certificate.residual_certificate_sha256):
            raise ValueError("live residual certificate differs from the totalizer")
        if evaluation_source.certificate_sha256 != (
            self.certificate.residual_certificate_sha256
        ):
            raise ValueError("private residual certificate differs from the totalizer")
        expected = _make_certificate(self.checkpoint, self.provenance)
        for name in _certificate_fields():
            supplied = getattr(self.certificate, name)
            recomputed = getattr(expected, name)
            if not _field_matches(name, supplied, recomputed):
                raise ValueError(
                    "totalized residual certificate field %s differs from live state"
                    % name
                )

    def _validated_single_batch(
        self, batch: object
    ) -> Tuple[TypedConfigurationBatch, str]:
        _, checked = _validate_model_and_batch(
            self.model,
            self.checkpoint.contract,
            batch,
        )
        if checked.batch_size != 1:
            raise ValueError("totalized residual evaluation requires one batch row")
        before_digest = _batch_sha256(checked)
        with torch.no_grad():
            snapshot = pack_typed_configuration_batch(
                self._evaluation_model.architecture,
                checked.forward_time.detach().clone(),
                checked.context.detach().clone(),
                {
                    event_type: coordinates.detach().clone()
                    for event_type, coordinates in zip(
                        checked.type_ids, checked.coordinates
                    )
                },
                {
                    event_type: owners.detach().clone()
                    for event_type, owners in zip(
                        checked.type_ids, checked.batch_indices
                    )
                },
            )
        _, snapshot = _validate_model_and_batch(
            self._evaluation_model,
            self.checkpoint.contract,
            snapshot,
        )
        snapshot_digest = _batch_sha256(snapshot)
        _, checked = _validate_model_and_batch(
            self.model,
            self.checkpoint.contract,
            checked,
        )
        after_digest = _batch_sha256(checked)
        if not (before_digest == snapshot_digest == after_digest):
            raise ValueError("batch changed while taking its detached snapshot")
        return snapshot, snapshot_digest

    def _evaluate_snapshot(
        self,
        checked: TypedConfigurationBatch,
        before_digest: str,
    ) -> TotalizedResidualPointEvaluation:
        """Evaluate one private-model-bound canonical batch snapshot."""

        direct_time = _canonical_zero(float(checked.forward_time[0].detach().item()))
        gate = _exact_mathematical_gate(
            direct_time,
            self.certificate.clean_hold,
            self.certificate.schedule_horizon,
        )
        try:
            with torch.no_grad():
                raw_tensor = certified_configuration_residual(
                    self._evaluation_model,
                    self.checkpoint,
                    checked,
                    expected_provenance=self.provenance,
                )
        except ConfigurationResidualGateResolutionError as error:
            if type(error) is not ConfigurationResidualGateResolutionError:
                raise
            legacy_gate = _legacy_staged_gate(
                direct_time,
                self.certificate.clean_hold,
                self.certificate.active_reverse_duration,
            )
            if direct_time <= self.certificate.clean_hold or not (
                math.isfinite(legacy_gate) and 0.0 <= legacy_gate < _MIN_NORMAL_FLOAT64
            ):
                raise
            branch = EXACT_GATE_RESCALED_CORE_BRANCH
            self._require_live_binding()
            with torch.no_grad():
                core_tensor = self._evaluation_model(checked)
            if tuple(core_tensor.shape) != (1,):
                raise ArithmeticError("bounded residual core returned the wrong shape")
            core_value = float(core_tensor.detach().item())
            _validated_float(core_value, name="fallback core value")
            exact_product = _require_fraction_size(
                gate * _fraction(core_value),
                name="exact rescaled core product",
            )
            operational = _rounded_fraction(
                exact_product, name="exact rescaled core product"
            )
            exact_error = abs(_fraction(operational) - exact_product)
            error_upper: Optional[float] = _outward_nonnegative_fraction(
                exact_error, name="fallback rounding error"
            )
            point_bound = _outward_nonnegative_fraction(
                gate * _fraction(self.certificate.global_point_magnitude_bound),
                name="fallback point magnitude bound",
            )
            legacy_value: Optional[float] = None
            algorithm = CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_ROUNDING_ALGORITHM
        else:
            branch = PRESERVED_CERTIFIED_RESIDUAL_BRANCH
            if tuple(raw_tensor.shape) != (1,):
                raise ArithmeticError("certified residual returned the wrong shape")
            operational = float(raw_tensor.detach().item())
            _validated_float(operational, name="certified residual point")
            legacy_value = operational
            core_value = None
            exact_product = None
            exact_error = None
            error_upper = None
            point_bound = self.certificate.global_point_magnitude_bound
            algorithm = "certified-residual-point-preserved-bitwise-v1"
        _, checked = _validate_model_and_batch(
            self._evaluation_model,
            self.checkpoint.contract,
            checked,
        )
        after_digest = _batch_sha256(checked)
        if after_digest != before_digest:
            raise ValueError("batch snapshot changed during residual point evaluation")
        values: dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "residual_certificate_sha256": (
                self.certificate.residual_certificate_sha256
            ),
            "batch_sha256": before_digest,
            "direct_time": direct_time,
            "branch": branch,
            "legacy_residual_value": legacy_value,
            "fallback_core_value": core_value,
            "mathematical_gate_numerator": gate.numerator,
            "mathematical_gate_denominator": gate.denominator,
            "mathematical_gate_upper_bound": _outward_nonnegative_fraction(
                gate, name="mathematical gate"
            ),
            "exact_rescaled_core_product_numerator": (
                None if exact_product is None else exact_product.numerator
            ),
            "exact_rescaled_core_product_denominator": (
                None if exact_product is None else exact_product.denominator
            ),
            "operational_residual": operational,
            "exact_fallback_rounding_error_numerator": (
                None if exact_error is None else exact_error.numerator
            ),
            "exact_fallback_rounding_error_denominator": (
                None if exact_error is None else exact_error.denominator
            ),
            "fallback_rounding_error_upper_bound": error_upper,
            "operational_point_magnitude_bound": point_bound,
            "evaluation_algorithm": algorithm,
            "totalization_policy": self.certificate.totalization_policy,
            "evaluation_sha256": "0" * 64,
        }
        values["evaluation_sha256"] = _semantic_digest(_evaluation_payload(values))
        return TotalizedResidualPointEvaluation(
            **values,
            _construction_token=_EVALUATION_TOKEN,
        )

    def evaluate(self, batch: object) -> TotalizedResidualPointEvaluation:
        """Evaluate one detached, single-row operational residual point."""

        self._require_live_binding()
        checked, before_digest = self._validated_single_batch(batch)
        result = self._evaluate_snapshot(checked, before_digest)
        self._require_live_binding()
        return result

    def validate_evaluation(
        self,
        evaluation: object,
        batch: object,
    ) -> TotalizedResidualPointEvaluation:
        """Reconstruct and replay one point record against a supplied batch."""

        if type(evaluation) is not TotalizedResidualPointEvaluation:
            raise TypeError(
                "evaluation must be an exact TotalizedResidualPointEvaluation"
            )
        TotalizedResidualPointEvaluation(
            **_record_values(evaluation, _evaluation_fields()),
            _construction_token=_EVALUATION_TOKEN,
        )
        if evaluation.certificate is not self.certificate:
            raise ValueError(
                "point record belongs to a different totalizer certificate"
            )
        expected = self.evaluate(batch)
        for name in _evaluation_fields():
            if not _field_matches(
                name, getattr(evaluation, name), getattr(expected, name)
            ):
                raise ValueError(
                    "totalized residual point field %s differs from replay" % name
                )
        return evaluation

    def state_pair_difference(
        self,
        source: object,
        destination: object,
    ) -> TotalizedResidualJumpDifference:
        """Subtract two same-time/same-context operational endpoint values."""

        self._require_live_binding()
        checked_source, source_digest = self._validated_single_batch(source)
        checked_destination, destination_digest = self._validated_single_batch(
            destination
        )
        if not torch.equal(
            checked_source.forward_time, checked_destination.forward_time
        ):
            raise ValueError("source and destination direct times differ")
        if not torch.equal(checked_source.context, checked_destination.context):
            raise ValueError("source and destination conditioners differ")
        source_point = self._evaluate_snapshot(checked_source, source_digest)
        destination_point = self._evaluate_snapshot(
            checked_destination,
            destination_digest,
        )
        exact = _require_fraction_size(
            _fraction(destination_point.operational_residual)
            - _fraction(source_point.operational_residual),
            name="exact operational endpoint difference",
        )
        operational = _rounded_fraction(
            exact, name="exact operational endpoint difference"
        )
        exact_error = abs(_fraction(operational) - exact)
        values: dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "source_batch_sha256": source_point.batch_sha256,
            "destination_batch_sha256": destination_point.batch_sha256,
            "direct_time": source_point.direct_time,
            "source_evaluation_sha256": source_point.evaluation_sha256,
            "destination_evaluation_sha256": destination_point.evaluation_sha256,
            "source_branch": source_point.branch,
            "destination_branch": destination_point.branch,
            "source_operational_residual": source_point.operational_residual,
            "destination_operational_residual": (
                destination_point.operational_residual
            ),
            "exact_operational_endpoint_difference_numerator": exact.numerator,
            "exact_operational_endpoint_difference_denominator": exact.denominator,
            "operational_difference": operational,
            "exact_rounding_error_numerator": exact_error.numerator,
            "exact_rounding_error_denominator": exact_error.denominator,
            "rounding_error_upper_bound": _outward_nonnegative_fraction(
                exact_error, name="endpoint-difference rounding error"
            ),
            "operational_edge_magnitude_bound": (
                self.certificate.global_edge_magnitude_bound
            ),
            "difference_algorithm": (
                "exact-operational-endpoint-difference-rounded-once-v1"
            ),
            "totalization_policy": self.certificate.totalization_policy,
            "difference_sha256": "0" * 64,
        }
        values["difference_sha256"] = _semantic_digest(_difference_payload(values))
        result = TotalizedResidualJumpDifference(
            **values,
            _construction_token=_DIFFERENCE_TOKEN,
        )
        self._require_live_binding()
        return result

    def validate_state_pair_difference(
        self,
        difference: object,
        source: object,
        destination: object,
    ) -> TotalizedResidualJumpDifference:
        """Reconstruct and replay one operational endpoint difference."""

        if type(difference) is not TotalizedResidualJumpDifference:
            raise TypeError(
                "difference must be an exact TotalizedResidualJumpDifference"
            )
        TotalizedResidualJumpDifference(
            **_record_values(difference, _difference_fields()),
            _construction_token=_DIFFERENCE_TOKEN,
        )
        if difference.certificate is not self.certificate:
            raise ValueError(
                "difference record belongs to a different totalizer certificate"
            )
        expected = self.state_pair_difference(source, destination)
        for name in _difference_fields():
            if not _field_matches(
                name, getattr(difference, name), getattr(expected, name)
            ):
                raise ValueError(
                    "totalized residual difference field %s differs from replay" % name
                )
        return difference


def certify_totalized_conditional_jump_residual(
    model: BoundedConfigurationEnergy,
    checkpoint: CertifiedConditionalResidualCheckpoint,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> TotalizedConditionalJumpResidual:
    """Bind the jump-only operational extension to one live checkpoint."""

    if type(model) is not BoundedConfigurationEnergy:
        raise TypeError("model must be an exact BoundedConfigurationEnergy")
    if type(checkpoint) is not CertifiedConditionalResidualCheckpoint:
        raise TypeError(
            "checkpoint must be an exact CertifiedConditionalResidualCheckpoint"
        )
    if type(expected_provenance) is not ConditionalResidualProvenance:
        raise TypeError(
            "expected_provenance must be an exact ConditionalResidualProvenance"
        )
    _require_binary64_environment()
    require_matching_conditional_residual_certificate(
        model,
        checkpoint,
        expected_provenance=expected_provenance,
    )
    evaluation_model = materialize_conditional_residual_checkpoint(
        checkpoint,
        expected_provenance=expected_provenance,
    )
    if evaluation_model is model:
        raise RuntimeError("checkpoint materialization did not create private custody")
    certificate = _make_certificate(checkpoint, expected_provenance)
    owner = TotalizedConditionalJumpResidual(
        model,
        evaluation_model,
        checkpoint,
        expected_provenance,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_totalized_conditional_jump_residual(
    model: BoundedConfigurationEnergy,
    owner: TotalizedConditionalJumpResidual,
    checkpoint: CertifiedConditionalResidualCheckpoint,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> TotalizedConditionalJumpResidual:
    """Require exact owner identity and reconstructed live custody."""

    if type(owner) is not TotalizedConditionalJumpResidual:
        raise TypeError("owner must be an exact TotalizedConditionalJumpResidual")
    if owner.model is not model:
        raise ValueError("totalized residual is bound to a different model")
    if owner.checkpoint is not checkpoint:
        raise ValueError("totalized residual is bound to a different checkpoint")
    if type(expected_provenance) is not ConditionalResidualProvenance:
        raise TypeError(
            "expected_provenance must be an exact ConditionalResidualProvenance"
        )
    if owner.provenance.sha256 != expected_provenance.sha256:
        raise ValueError("totalized residual is bound to different provenance")
    owner._require_live_binding()
    return owner


def validate_totalized_residual_jump_certificate(
    model: BoundedConfigurationEnergy,
    owner: TotalizedConditionalJumpResidual,
    checkpoint: CertifiedConditionalResidualCheckpoint,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> TotalizedResidualJumpCertificate:
    """Return the live-recomputed totalized residual certificate."""

    return require_matching_totalized_conditional_jump_residual(
        model,
        owner,
        checkpoint,
        expected_provenance=expected_provenance,
    ).certificate


__all__ = [
    "CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_POLICY",
    "CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_FLOATING_POINT_POLICY",
    "CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_ROUNDING_ALGORITHM",
    "CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCHEMA_VERSION",
    "CONFIGURATION_TOTALIZED_JUMP_RESIDUAL_SCOPE",
    "EXACT_GATE_RESCALED_CORE_BRANCH",
    "MAX_TOTALIZED_RESIDUAL_EXACT_INTEGER_BITS",
    "PRESERVED_CERTIFIED_RESIDUAL_BRANCH",
    "ConfigurationResidualJumpTotalizationError",
    "TotalizedConditionalJumpResidual",
    "TotalizedResidualJumpCertificate",
    "TotalizedResidualJumpDifference",
    "TotalizedResidualPointEvaluation",
    "certify_totalized_conditional_jump_residual",
    "require_matching_totalized_conditional_jump_residual",
    "validate_totalized_residual_jump_certificate",
]
