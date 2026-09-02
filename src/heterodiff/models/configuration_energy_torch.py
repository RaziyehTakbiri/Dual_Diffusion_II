"""Bounded typed-configuration energy and analytic checkpoint certificate.

This optional-PyTorch module is the correctness implementation of Section 4.3
of ``manuscript_v3/executable_method_spec.md``.  It deliberately uses CPU
``torch.float64`` tensors, type-specific smooth encoders, deterministic
multiplicity-preserving sum pooling, and one outer bounded scalar,

``V = B * tanh(F / B)``.

The certificate is global and analytic: it propagates conservative outward
matrix-norm bounds through the declared graph and binds them to the complete
reference-process contract, architecture, buffers, and parameter bytes.  It is
not a training-run approval, an authentication mechanism, a safe loader for
untrusted files, or evidence that a fitted energy equals the exact reversal
energy.  Numerical preregistration and data-law assumptions remain separate
method-freeze gates.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import OrderedDict
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import marshal
import math
from numbers import Integral, Real
import platform
import sys
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Sequence, Tuple

try:
    import torch
    from torch import nn
    from torch.nn import functional as F
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.configuration_energy_torch requires the "
            "optional PyTorch dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.artifacts.manifest import canonical_config_digest
from heterodiff.processes.reversible_hybrid_reference import (
    ReversibleHybridReference,
)
from heterodiff.theory.reverse_energy_objective import EnergyBoundConsequences


CONFIGURATION_ENERGY_SCHEMA_VERSION = "configuration-energy-torch-v2"
CONFIGURATION_ENERGY_DTYPE = "torch.float64"
CONFIGURATION_ENERGY_DEVICE = "cpu"

MAX_CONFIGURATION_ENERGY_TYPES = 128
MAX_CONFIGURATION_ENERGY_COORDINATE_DIMENSION = 4_096
MAX_CONFIGURATION_ENERGY_CONTEXT_DIMENSION = 4_096
MAX_CONFIGURATION_ENERGY_CAP = 10_000
MAX_CONFIGURATION_ENERGY_WIDTH = 1_024
MAX_CONFIGURATION_ENERGY_PARAMETERS = 2_000_000
MAX_CONFIGURATION_ENERGY_BATCH_SIZE = 4_096
MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES = 100_000
MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES = 2_000_000
MAX_CONFIGURATION_ENERGY_POOL_WORK = 20_000_000
MAX_CONFIGURATION_ENERGY_FORWARD_WORK = 100_000_000
MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_COORDINATES = 4_096
MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_WORK = 50_000_000
MAX_CONFIGURATION_ENERGY_HUTCHINSON_PROBES = 256
MAX_CONFIGURATION_ENERGY_HUTCHINSON_WORK = 20_000_000
MAX_CONFIGURATION_ENERGY_AUTOGRAD_NODES = 100_000
MAX_CONFIGURATION_ENERGY_NORM_CEILING = 1_000_000.0
MAX_CONFIGURATION_ENERGY_BIAS_CEILING = 1_000_000.0
MIN_CONFIGURATION_ENERGY_SCALE = float.fromhex("0x1.0p-256")
MAX_CONFIGURATION_ENERGY_SCALE = float.fromhex("0x1.0p+256")

_ARCHITECTURE_TOKEN = object()
_BATCH_TOKEN = object()
_SNAPSHOT_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_CHECKPOINT_TOKEN = object()
_DERIVATIVE_TOKEN = object()
_HUTCHINSON_TOKEN = object()

CONFIGURATION_ENERGY_CERTIFICATE_SCOPE = (
    "real-arithmetic-global-bounds-and-binary64-operational-guards;"
    "trusted-unmodified-python-torch-runtime;not-runtime-tamper-attestation;"
    "not-sampler-admission"
)

_MIN_NORMAL_FLOAT64 = float.fromhex("0x1.0p-1022")


class ConfigurationEnergyResourceError(RuntimeError):
    """Raised before an energy operation exceeds its declared work surface."""


class ConfigurationEnergyCertificateError(RuntimeError):
    """Raised when a checkpoint cannot carry the declared global bounds."""


def _semantic_digest_value(value: object) -> object:
    """Encode plain semantic data without JSON's 53-bit integer restriction."""

    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-decimal-v1", str(value)]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("semantic digest data must be finite")
        return ["float64-hex-v1", float(value).hex()]
    if type(value) is str:
        return ["string-v1", value]
    if isinstance(value, tuple):
        return [
            "tuple-v1",
            [_semantic_digest_value(item) for item in value],
        ]
    if isinstance(value, list):
        return [
            "list-v1",
            [_semantic_digest_value(item) for item in value],
        ]
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("semantic digest mappings require string keys")
            items.append((key, _semantic_digest_value(item)))
        items.sort(key=lambda pair: pair[0])
        return ["mapping-v1", items]
    raise TypeError(
        "unsupported semantic digest value of type %s" % type(value).__name__
    )


def _semantic_digest(value: Mapping[str, object]) -> str:
    encoded = _semantic_digest_value(value)
    if not isinstance(encoded, list):  # pragma: no cover - defensive
        raise RuntimeError("semantic digest root encoding is invalid")
    return canonical_config_digest({"typed_semantic_data": encoded})


def _fraction_from_float(value: float) -> Fraction:
    numerator, denominator = value.as_integer_ratio()
    return Fraction(numerator, denominator)


def _outward_float(value: Fraction, *, name: str) -> float:
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    if value == 0:
        return 0.0
    try:
        rounded = float(value)
    except OverflowError as error:
        raise ArithmeticError("%s exceeds binary64 range" % name) from error
    if not math.isfinite(rounded):
        raise ArithmeticError("%s has no finite binary64 upper bound" % name)
    if _fraction_from_float(rounded) < value:
        rounded = math.nextafter(rounded, math.inf)
    if not math.isfinite(rounded):
        raise ArithmeticError("%s cannot be rounded outward" % name)
    return rounded


def _outward_sqrt_fraction(value: Fraction, *, name: str) -> float:
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    if value == 0:
        return 0.0
    numerator_root = math.isqrt(value.numerator)
    denominator_root = math.isqrt(value.denominator)
    if (
        numerator_root * numerator_root == value.numerator
        and denominator_root * denominator_root == value.denominator
    ):
        return _outward_float(
            Fraction(numerator_root, denominator_root), name=name
        )
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    even_exponent = exponent if exponent % 2 == 0 else exponent - 1
    scaled = value / Fraction(2) ** even_exponent
    approximate = math.sqrt(float(scaled)) * (2.0 ** (even_exponent // 2))
    if not math.isfinite(approximate) or approximate <= 0.0:
        raise ArithmeticError("%s has no finite positive approximation" % name)
    while _fraction_from_float(approximate) ** 2 < value:
        approximate = math.nextafter(approximate, math.inf)
        if not math.isfinite(approximate):
            raise ArithmeticError("%s cannot be rounded outward" % name)
    return approximate


def _outward_reference_exit_rate(
    process: ReversibleHybridReference,
    *,
    cap: int,
    type_ids: Tuple[int, ...],
) -> float:
    """Bound every scheduled base exit rate using exact represented inputs."""

    if cap == 0:
        return 0.0
    maximum_outgoing = max(
        (
            process.rates.outgoing_replacement_rate(event_type)
            for event_type in type_ids
        ),
        default=0.0,
    )
    death_rate = _fraction_from_float(
        process.rates.per_particle_death_rate
    )
    outgoing_rate = _fraction_from_float(maximum_outgoing)

    def rounded_base_upper(count: int, birth: float) -> float:
        death = _outward_float(
            count * death_rate, name="aggregate death-rate upper bound"
        )
        replacement = _outward_float(
            count * outgoing_rate,
            name="aggregate replacement-rate upper bound",
        )
        exact_upper = (
            _fraction_from_float(birth)
            + _fraction_from_float(death)
            + _fraction_from_float(replacement)
        )
        return _outward_float(
            exact_upper, name="aggregate base exit-rate upper bound"
        )

    at_cap = rounded_base_upper(cap, 0.0)
    below_cap = rounded_base_upper(
        cap - 1, process.rates.birth_rate
    )
    base = max(at_cap, below_cap)
    schedule = max(
        (float(value) for value in process.schedule.jump_rates), default=0.0
    )
    return _outward_float(
        _fraction_from_float(base) * _fraction_from_float(schedule),
        name="maximum reference exit rate",
    )


def _validated_integer(
    value: object, *, name: str, minimum: int, maximum: int
) -> int:
    if isinstance(value, (bool, torch.Tensor)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError("%s must lie in [%d, %d]" % (name, minimum, maximum))
    return result


def _validated_real(
    value: object,
    *,
    name: str,
    strictly_positive: bool = False,
    nonnegative: bool = False,
    maximum: Optional[float] = None,
) -> float:
    if isinstance(value, (bool, torch.Tensor)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean value" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if strictly_positive and result <= 0.0:
        raise ValueError("%s must be strictly positive" % name)
    if nonnegative and result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    if maximum is not None and result > maximum:
        raise ValueError("%s exceeds the implementation maximum" % name)
    if result != 0.0 and abs(result) < float.fromhex("0x1.0p-1022"):
        raise ValueError("%s must be zero or a normal float64 value" % name)
    return 0.0 if result == 0.0 else result


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be a string" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase 64-hex SHA-256 digest" % name)
    return value


def _require_exact_tensor_hook_registries(
    value: torch.Tensor, *, name: str
) -> None:
    for field_name in ("_backward_hooks", "_post_accumulate_grad_hooks"):
        registry = getattr(value, field_name, None)
        if registry is None:
            continue
        if type(registry) is not OrderedDict or registry:
            raise ValueError("%s carries unsupported autograd hooks" % name)


def _require_float64_cpu_tensor(
    value: object,
    *,
    name: str,
    shape: Optional[Tuple[int, ...]] = None,
    finite: bool = True,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise TypeError("%s must be an exact torch.Tensor" % name)
    if value.layout != torch.strided:
        raise TypeError("%s must use the dense strided layout" % name)
    if value.dtype != torch.float64:
        raise TypeError("%s must have torch.float64 dtype" % name)
    if value.device.type != "cpu":
        raise ValueError("%s must be on the CPU" % name)
    _require_exact_tensor_hook_registries(value, name=name)
    if vars(value):
        raise ValueError(
            "%s carries unsupported tensor instance attributes" % name
        )
    if shape is not None and tuple(value.shape) != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    if finite and bool(torch.any(~torch.isfinite(value)).detach().item()):
        raise ValueError("%s must contain only finite values" % name)
    return value


def _require_owner_tensor(
    value: object,
    *,
    name: str,
    occurrence_count: int,
    batch_size: int,
    check_range: bool = True,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise TypeError("%s must be an exact torch.Tensor" % name)
    if value.layout != torch.strided:
        raise TypeError("%s must use the dense strided layout" % name)
    if value.dtype != torch.int64:
        raise TypeError("%s must have torch.int64 dtype" % name)
    if value.device.type != "cpu":
        raise ValueError("%s must be on the CPU" % name)
    if vars(value):
        raise ValueError(
            "%s carries unsupported tensor instance attributes" % name
        )
    if tuple(value.shape) != (occurrence_count,):
        raise ValueError("%s must have shape (%d,)" % (name, occurrence_count))
    if check_range and occurrence_count and (
        int(torch.min(value).detach().item()) < 0
        or int(torch.max(value).detach().item()) >= batch_size
    ):
        raise ValueError("%s contains an out-of-range batch index" % name)
    return value


def _require_independent_batch_float_storage(
    forward_time: torch.Tensor,
    context: torch.Tensor,
    coordinates: Tuple[torch.Tensor, ...],
) -> None:
    """Reject overlapping byte ranges between logical batch fields."""

    named_tensors = [
        ("forward_time", forward_time),
        ("context", context),
    ]
    named_tensors.extend(
        ("coordinates[%d]" % index, value)
        for index, value in enumerate(coordinates)
    )
    occupied = []
    for name, value in named_tensors:
        if not value.is_contiguous():
            raise ValueError(
                "batch float tensor %s must be contiguous and non-overlapping"
                % name
            )
        if value.numel() == 0:
            continue
        start = value.data_ptr()
        end = start + value.numel() * value.element_size()
        for previous_start, previous_end, previous_name in occupied:
            if start < previous_end and previous_start < end:
                raise ValueError(
                    "batch float tensors %s and %s must not overlap in storage"
                    % (previous_name, name)
                )
        occupied.append((start, end, name))


def _validated_type_mapping_keys(
    value: Mapping[object, object], *, name: str
) -> Tuple[int, ...]:
    keys = []
    for raw_key in value:
        if len(keys) >= MAX_CONFIGURATION_ENERGY_TYPES:
            raise ConfigurationEnergyResourceError(
                "%s contains too many type keys" % name
            )
        key = _validated_integer(
            raw_key,
            name="%s key" % name,
            minimum=0,
            maximum=2**63 - 1,
        )
        keys.append(key)
    if len(set(keys)) != len(keys):
        raise ValueError("%s contains aliased type keys" % name)
    return tuple(keys)


def _forward_work_estimate(
    architecture: ConfigurationEnergyArchitecture,
    *,
    batch_size: int,
    occurrence_counts: Tuple[int, ...],
) -> int:
    event_work = sum(
        count
        * (
            architecture.event_hidden_width * dimension
            + architecture.event_embedding_width
            * architecture.event_hidden_width
            + architecture.event_embedding_width
        )
        for count, dimension in zip(
            occurrence_counts, architecture.type_dimensions
        )
    )
    context_work = batch_size * (
        architecture.context_hidden_width
        * (architecture.context_dimension + 1)
        + architecture.context_embedding_width
        * architecture.context_hidden_width
    )
    readout_input = (
        architecture.event_embedding_width
        + architecture.context_embedding_width
        + 1
    )
    readout_work = batch_size * (
        architecture.readout_hidden_width * readout_input
        + architecture.readout_hidden_width**2
        + architecture.readout_hidden_width
    )
    pooling_work = (
        sum(occurrence_counts) * architecture.event_embedding_width
    )
    return event_work + context_work + readout_work + pooling_work


def _preflight_forward_work(
    architecture: ConfigurationEnergyArchitecture,
    *,
    batch_size: int,
    occurrence_counts: Tuple[int, ...],
) -> None:
    if (
        sum(occurrence_counts) * architecture.event_embedding_width
        > MAX_CONFIGURATION_ENERGY_POOL_WORK
    ):
        raise ConfigurationEnergyResourceError(
            "deterministic pooling exceeds the implementation work limit"
        )
    if (
        _forward_work_estimate(
            architecture,
            batch_size=batch_size,
            occurrence_counts=occurrence_counts,
        )
        > MAX_CONFIGURATION_ENERGY_FORWARD_WORK
    ):
        raise ConfigurationEnergyResourceError(
            "configuration-energy forward pass exceeds the work limit"
        )


def _normal_positive_tuple(
    values: object, *, name: str, length: int
) -> Tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("%s must be a sequence of positive scales" % name)
    try:
        iterator = iter(values)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("%s must be iterable" % name) from error
    collected = []
    for value in iterator:
        if len(collected) >= length:
            raise ValueError("%s must have length %d" % (name, length))
        collected.append(value)
    raw = tuple(collected)
    if len(raw) != length:
        raise ValueError("%s must have length %d" % (name, length))
    result = tuple(
        _validated_real(
            value,
            name="%s[%d]" % (name, index),
            strictly_positive=True,
        )
        for index, value in enumerate(raw)
    )
    if any(value < MIN_CONFIGURATION_ENERGY_SCALE for value in result):
        raise ValueError(
            "%s is below the stable binary64 scale minimum" % name
        )
    if any(value > MAX_CONFIGURATION_ENERGY_SCALE for value in result):
        raise ValueError(
            "%s exceeds the stable binary64 scale maximum" % name
        )
    return result


@dataclass(frozen=True)
class SpectralNormCeilings:
    """Frozen per-layer upper ceilings for spectral norms.

    Certification uses an outward Frobenius upper bound, which safely dominates
    the spectral norm but can be conservative.
    """

    event_input: float
    event_output: float
    context_input: float
    context_output: float
    readout_input: float
    readout_hidden: float
    readout_output: float

    def __post_init__(self) -> None:
        for field_name in (
            "event_input",
            "event_output",
            "context_input",
            "context_output",
            "readout_input",
            "readout_hidden",
            "readout_output",
        ):
            object.__setattr__(
                self,
                field_name,
                _validated_real(
                    getattr(self, field_name),
                    name="spectral ceiling %s" % field_name,
                    strictly_positive=True,
                    maximum=MAX_CONFIGURATION_ENERGY_NORM_CEILING,
                ),
            )

    def as_tuple(self) -> Tuple[float, ...]:
        return (
            self.event_input,
            self.event_output,
            self.context_input,
            self.context_output,
            self.readout_input,
            self.readout_hidden,
            self.readout_output,
        )


@dataclass(frozen=True, init=False)
class ConfigurationEnergyArchitecture:
    """Immutable process-bound contract for one typed DeepSets scalar."""

    process_parameter_key: Tuple[object, ...]
    process_parameter_sha256: str
    type_ids: Tuple[int, ...]
    type_dimensions: Tuple[int, ...]
    coordinate_scales: Tuple[Tuple[float, ...], ...]
    total_cap: int
    schedule_horizon: float
    clean_hold: float
    maximum_reference_exit_rate: float
    context_dimension: int
    context_scales: Tuple[float, ...]
    context_schema_sha256: str
    event_hidden_width: int
    event_embedding_width: int
    context_hidden_width: int
    context_embedding_width: int
    readout_hidden_width: int
    value_bound: float
    spectral_ceilings: SpectralNormCeilings
    bias_ceiling: float
    first_derivative_ceiling: float
    second_derivative_ceiling: float
    expected_parameter_count: int
    architecture_sha256: str

    def __init__(
        self,
        *,
        process_parameter_key: Tuple[object, ...],
        process_parameter_sha256: str,
        type_ids: Tuple[int, ...],
        type_dimensions: Tuple[int, ...],
        coordinate_scales: Tuple[Tuple[float, ...], ...],
        total_cap: int,
        schedule_horizon: float,
        clean_hold: float,
        maximum_reference_exit_rate: float,
        context_dimension: int,
        context_scales: Tuple[float, ...],
        context_schema_sha256: str,
        event_hidden_width: int,
        event_embedding_width: int,
        context_hidden_width: int,
        context_embedding_width: int,
        readout_hidden_width: int,
        value_bound: float,
        spectral_ceilings: SpectralNormCeilings,
        bias_ceiling: float,
        first_derivative_ceiling: float,
        second_derivative_ceiling: float,
        expected_parameter_count: int,
        architecture_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _ARCHITECTURE_TOKEN:
            raise TypeError(
                "configuration-energy architectures must be built from a process"
            )
        values = locals().copy()
        values.pop("self")
        values.pop("_construction_token")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @staticmethod
    def _parameter_count(
        type_dimensions: Tuple[int, ...],
        *,
        context_dimension: int,
        event_hidden_width: int,
        event_embedding_width: int,
        context_hidden_width: int,
        context_embedding_width: int,
        readout_hidden_width: int,
    ) -> int:
        event = sum(
            event_hidden_width * dimension
            + event_hidden_width
            + event_embedding_width * event_hidden_width
            + event_embedding_width
            for dimension in type_dimensions
        )
        context = (
            context_hidden_width * (context_dimension + 1)
            + context_hidden_width
            + context_embedding_width * context_hidden_width
            + context_embedding_width
        )
        readout_input = event_embedding_width + context_embedding_width + 1
        readout = (
            readout_hidden_width * readout_input
            + readout_hidden_width
            + readout_hidden_width * readout_hidden_width
            + readout_hidden_width
            + readout_hidden_width
            + 1
        )
        return event + context + readout

    @classmethod
    def from_process(
        cls,
        process: ReversibleHybridReference,
        *,
        coordinate_scales_by_type: Mapping[int, Sequence[float]],
        context_dimension: object,
        context_scales: Sequence[float],
        context_schema_sha256: object,
        event_hidden_width: object,
        event_embedding_width: object,
        context_hidden_width: object,
        context_embedding_width: object,
        readout_hidden_width: object,
        value_bound: object,
        spectral_ceilings: SpectralNormCeilings,
        bias_ceiling: object,
        first_derivative_ceiling: object,
        second_derivative_ceiling: object,
    ) -> "ConfigurationEnergyArchitecture":
        if type(process) is not ReversibleHybridReference:
            raise TypeError("process must be an exact ReversibleHybridReference")
        reference = process.reference
        type_ids = tuple(reference.type_ids)
        if len(type_ids) > MAX_CONFIGURATION_ENERGY_TYPES:
            raise ConfigurationEnergyResourceError(
                "energy type count exceeds the implementation limit"
            )
        dimensions = tuple(
            _validated_integer(
                reference.type_dimensions[event_type],
                name="type dimension",
                minimum=0,
                maximum=MAX_CONFIGURATION_ENERGY_COORDINATE_DIMENSION,
            )
            for event_type in type_ids
        )
        if not isinstance(coordinate_scales_by_type, Mapping):
            raise TypeError("coordinate_scales_by_type must be a mapping")
        scale_keys = _validated_type_mapping_keys(
            coordinate_scales_by_type, name="coordinate_scales_by_type"
        )
        if set(scale_keys) != set(type_ids):
            raise ValueError("coordinate scales must specify every process type")
        scale_mapping = {
            event_type: coordinate_scales_by_type[event_type]
            for event_type in scale_keys
        }
        scales = tuple(
            _normal_positive_tuple(
                scale_mapping[event_type],
                name="coordinate scales for type %d" % event_type,
                length=dimension,
            )
            for event_type, dimension in zip(type_ids, dimensions)
        )
        cap = _validated_integer(
            reference.total_cap,
            name="configuration cap",
            minimum=0,
            maximum=MAX_CONFIGURATION_ENERGY_CAP,
        )
        context_dim = _validated_integer(
            context_dimension,
            name="context_dimension",
            minimum=0,
            maximum=MAX_CONFIGURATION_ENERGY_CONTEXT_DIMENSION,
        )
        checked_context_scales = _normal_positive_tuple(
            context_scales,
            name="context_scales",
            length=context_dim,
        )
        context_digest = _require_sha256(
            context_schema_sha256, name="context_schema_sha256"
        )
        widths = tuple(
            _validated_integer(
                value,
                name=name,
                minimum=1,
                maximum=MAX_CONFIGURATION_ENERGY_WIDTH,
            )
            for name, value in (
                ("event_hidden_width", event_hidden_width),
                ("event_embedding_width", event_embedding_width),
                ("context_hidden_width", context_hidden_width),
                ("context_embedding_width", context_embedding_width),
                ("readout_hidden_width", readout_hidden_width),
            )
        )
        if type(spectral_ceilings) is not SpectralNormCeilings:
            raise TypeError("spectral_ceilings must be exact SpectralNormCeilings")
        if "as_tuple" in vars(spectral_ceilings):
            raise ValueError("spectral_ceilings overrides its frozen accessor")
        spectral_values = (
            spectral_ceilings.event_input,
            spectral_ceilings.event_output,
            spectral_ceilings.context_input,
            spectral_ceilings.context_output,
            spectral_ceilings.readout_input,
            spectral_ceilings.readout_hidden,
            spectral_ceilings.readout_output,
        )
        bound = _validated_real(
            value_bound, name="value_bound", strictly_positive=True
        )
        bias = _validated_real(
            bias_ceiling,
            name="bias_ceiling",
            strictly_positive=True,
            maximum=MAX_CONFIGURATION_ENERGY_BIAS_CEILING,
        )
        first = _validated_real(
            first_derivative_ceiling,
            name="first_derivative_ceiling",
            strictly_positive=True,
        )
        second = _validated_real(
            second_derivative_ceiling,
            name="second_derivative_ceiling",
            strictly_positive=True,
        )
        EnergyBoundConsequences(bound, first, second)
        expected_parameters = cls._parameter_count(
            dimensions,
            context_dimension=context_dim,
            event_hidden_width=widths[0],
            event_embedding_width=widths[1],
            context_hidden_width=widths[2],
            context_embedding_width=widths[3],
            readout_hidden_width=widths[4],
        )
        if expected_parameters > MAX_CONFIGURATION_ENERGY_PARAMETERS:
            raise ConfigurationEnergyResourceError(
                "energy parameter count exceeds the implementation limit"
            )
        process_key = process.parameter_key()
        process_digest = _semantic_digest(
            {"process_parameter_key": process_key}
        )
        maximum_reference_exit = _outward_reference_exit_rate(
            process, cap=cap, type_ids=type_ids
        )
        contract = {
            "schema": CONFIGURATION_ENERGY_SCHEMA_VERSION,
            "process_parameter_sha256": process_digest,
            "process_parameter_key": process_key,
            "type_ids": type_ids,
            "type_dimensions": dimensions,
            "coordinate_scales": scales,
            "total_cap": cap,
            "schedule_horizon": process.schedule.horizon,
            "clean_hold": process.schedule.clean_hold,
            "maximum_reference_exit_rate": maximum_reference_exit,
            "context_dimension": context_dim,
            "context_scales": checked_context_scales,
            "context_schema_sha256": context_digest,
            "event_hidden_width": widths[0],
            "event_embedding_width": widths[1],
            "context_hidden_width": widths[2],
            "context_embedding_width": widths[3],
            "readout_hidden_width": widths[4],
            "value_bound": bound,
            "spectral_ceilings": spectral_values,
            "bias_ceiling": bias,
            "first_derivative_ceiling": first,
            "second_derivative_ceiling": second,
            "expected_parameter_count": expected_parameters,
            "dtype": CONFIGURATION_ENERGY_DTYPE,
            "device": CONFIGURATION_ENERGY_DEVICE,
            "pooling": "cpython-math-fsum-segment-v1",
            "coordinate_transform": "two-over-pi-stable-atan2-scale-v2",
            "scale_interval": (
                MIN_CONFIGURATION_ENERGY_SCALE,
                MAX_CONFIGURATION_ENERGY_SCALE,
            ),
            "activation": "tanh",
            "event_depth": 2,
            "context_depth": 2,
            "readout_depth": 3,
            "resource_limits": (
                MAX_CONFIGURATION_ENERGY_BATCH_SIZE,
                MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES,
                MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES,
                MAX_CONFIGURATION_ENERGY_POOL_WORK,
                MAX_CONFIGURATION_ENERGY_FORWARD_WORK,
                MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_COORDINATES,
                MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_WORK,
                MAX_CONFIGURATION_ENERGY_HUTCHINSON_PROBES,
                MAX_CONFIGURATION_ENERGY_HUTCHINSON_WORK,
                MAX_CONFIGURATION_ENERGY_AUTOGRAD_NODES,
            ),
            "first_derivative_semantics": (
                "euclidean norm of full flattened physical-coordinate gradient"
            ),
            "second_derivative_semantics": (
                "euclidean operator norm of full flattened physical-coordinate "
                "Hessian, including cross-occurrence blocks"
            ),
            "certificate_scope": CONFIGURATION_ENERGY_CERTIFICATE_SCOPE,
        }
        architecture_digest = _semantic_digest(contract)
        result = cls(
            process_parameter_key=process_key,
            process_parameter_sha256=process_digest,
            type_ids=type_ids,
            type_dimensions=dimensions,
            coordinate_scales=scales,
            total_cap=cap,
            schedule_horizon=float(process.schedule.horizon),
            clean_hold=float(process.schedule.clean_hold),
            maximum_reference_exit_rate=maximum_reference_exit,
            context_dimension=context_dim,
            context_scales=checked_context_scales,
            context_schema_sha256=context_digest,
            event_hidden_width=widths[0],
            event_embedding_width=widths[1],
            context_hidden_width=widths[2],
            context_embedding_width=widths[3],
            readout_hidden_width=widths[4],
            value_bound=bound,
            spectral_ceilings=spectral_ceilings,
            bias_ceiling=bias,
            first_derivative_ceiling=first,
            second_derivative_ceiling=second,
            expected_parameter_count=expected_parameters,
            architecture_sha256=architecture_digest,
            _construction_token=_ARCHITECTURE_TOKEN,
        )
        return _validate_architecture(result)

    @property
    def type_dimension_map(self) -> Mapping[int, int]:
        return MappingProxyType(dict(zip(self.type_ids, self.type_dimensions)))


def _architecture_contract_mapping(
    architecture: ConfigurationEnergyArchitecture,
) -> Dict[str, object]:
    return {
        "schema": CONFIGURATION_ENERGY_SCHEMA_VERSION,
        "process_parameter_sha256": architecture.process_parameter_sha256,
        "process_parameter_key": architecture.process_parameter_key,
        "type_ids": architecture.type_ids,
        "type_dimensions": architecture.type_dimensions,
        "coordinate_scales": architecture.coordinate_scales,
        "total_cap": architecture.total_cap,
        "schedule_horizon": architecture.schedule_horizon,
        "clean_hold": architecture.clean_hold,
        "maximum_reference_exit_rate": architecture.maximum_reference_exit_rate,
        "context_dimension": architecture.context_dimension,
        "context_scales": architecture.context_scales,
        "context_schema_sha256": architecture.context_schema_sha256,
        "event_hidden_width": architecture.event_hidden_width,
        "event_embedding_width": architecture.event_embedding_width,
        "context_hidden_width": architecture.context_hidden_width,
        "context_embedding_width": architecture.context_embedding_width,
        "readout_hidden_width": architecture.readout_hidden_width,
        "value_bound": architecture.value_bound,
        "spectral_ceilings": (
            architecture.spectral_ceilings.event_input,
            architecture.spectral_ceilings.event_output,
            architecture.spectral_ceilings.context_input,
            architecture.spectral_ceilings.context_output,
            architecture.spectral_ceilings.readout_input,
            architecture.spectral_ceilings.readout_hidden,
            architecture.spectral_ceilings.readout_output,
        ),
        "bias_ceiling": architecture.bias_ceiling,
        "first_derivative_ceiling": architecture.first_derivative_ceiling,
        "second_derivative_ceiling": architecture.second_derivative_ceiling,
        "expected_parameter_count": architecture.expected_parameter_count,
        "dtype": CONFIGURATION_ENERGY_DTYPE,
        "device": CONFIGURATION_ENERGY_DEVICE,
        "pooling": "cpython-math-fsum-segment-v1",
        "coordinate_transform": "two-over-pi-stable-atan2-scale-v2",
        "scale_interval": (
            MIN_CONFIGURATION_ENERGY_SCALE,
            MAX_CONFIGURATION_ENERGY_SCALE,
        ),
        "activation": "tanh",
        "event_depth": 2,
        "context_depth": 2,
        "readout_depth": 3,
        "resource_limits": (
            MAX_CONFIGURATION_ENERGY_BATCH_SIZE,
            MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES,
            MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES,
            MAX_CONFIGURATION_ENERGY_POOL_WORK,
            MAX_CONFIGURATION_ENERGY_FORWARD_WORK,
            MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_COORDINATES,
            MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_WORK,
            MAX_CONFIGURATION_ENERGY_HUTCHINSON_PROBES,
            MAX_CONFIGURATION_ENERGY_HUTCHINSON_WORK,
            MAX_CONFIGURATION_ENERGY_AUTOGRAD_NODES,
        ),
        "first_derivative_semantics": (
            "euclidean norm of full flattened physical-coordinate gradient"
        ),
        "second_derivative_semantics": (
            "euclidean operator norm of full flattened physical-coordinate "
            "Hessian, including cross-occurrence blocks"
        ),
        "certificate_scope": CONFIGURATION_ENERGY_CERTIFICATE_SCOPE,
    }


def _validate_architecture(
    architecture: object,
) -> ConfigurationEnergyArchitecture:
    if type(architecture) is not ConfigurationEnergyArchitecture:
        raise TypeError(
            "architecture must be an exact ConfigurationEnergyArchitecture"
        )
    if type(architecture.process_parameter_key) is not tuple:
        raise TypeError("architecture process key must be a tuple")
    for field_name in (
        "type_ids",
        "type_dimensions",
        "coordinate_scales",
        "context_scales",
    ):
        if type(getattr(architecture, field_name)) is not tuple:
            raise TypeError(
                "architecture.%s must be an exact tuple" % field_name
            )
    for index, values in enumerate(architecture.coordinate_scales):
        if type(values) is not tuple:
            raise TypeError(
                "architecture.coordinate_scales[%d] must be an exact tuple"
                % index
            )
    process_digest = _semantic_digest(
        {"process_parameter_key": architecture.process_parameter_key}
    )
    if process_digest != _require_sha256(
        architecture.process_parameter_sha256,
        name="architecture.process_parameter_sha256",
    ):
        raise ValueError("architecture process digest is inconsistent")
    type_ids = tuple(
        _validated_integer(
            event_type,
            name="architecture type id",
            minimum=0,
            maximum=2**63 - 1,
        )
        for event_type in architecture.type_ids
    )
    if type_ids != architecture.type_ids or tuple(sorted(set(type_ids))) != type_ids:
        raise ValueError("architecture type ids must be unique and sorted")
    if len(type_ids) > MAX_CONFIGURATION_ENERGY_TYPES:
        raise ConfigurationEnergyResourceError(
            "energy type count exceeds the implementation limit"
        )
    dimensions = tuple(
        _validated_integer(
            dimension,
            name="architecture type dimension",
            minimum=0,
            maximum=MAX_CONFIGURATION_ENERGY_COORDINATE_DIMENSION,
        )
        for dimension in architecture.type_dimensions
    )
    if len(dimensions) != len(type_ids):
        raise ValueError("architecture type dimensions are inconsistent")
    if len(architecture.coordinate_scales) != len(type_ids):
        raise ValueError("architecture coordinate scales are inconsistent")
    scales = tuple(
        _normal_positive_tuple(
            values,
            name="architecture coordinate scales[%d]" % index,
            length=dimension,
        )
        for index, (values, dimension) in enumerate(
            zip(architecture.coordinate_scales, dimensions)
        )
    )
    if scales != architecture.coordinate_scales:
        raise ValueError("architecture coordinate scales are not canonical")
    _validated_integer(
        architecture.total_cap,
        name="architecture total_cap",
        minimum=0,
        maximum=MAX_CONFIGURATION_ENERGY_CAP,
    )
    horizon = _validated_real(
        architecture.schedule_horizon,
        name="architecture schedule_horizon",
        strictly_positive=True,
    )
    hold = _validated_real(
        architecture.clean_hold,
        name="architecture clean_hold",
        nonnegative=True,
    )
    if hold > horizon:
        raise ValueError("architecture clean hold exceeds its horizon")
    _validated_real(
        architecture.maximum_reference_exit_rate,
        name="architecture maximum_reference_exit_rate",
        nonnegative=True,
    )
    context_dimension = _validated_integer(
        architecture.context_dimension,
        name="architecture context_dimension",
        minimum=0,
        maximum=MAX_CONFIGURATION_ENERGY_CONTEXT_DIMENSION,
    )
    checked_context_scales = _normal_positive_tuple(
        architecture.context_scales,
        name="architecture context scales",
        length=context_dimension,
    )
    if checked_context_scales != architecture.context_scales:
        raise ValueError("architecture context scales are not canonical")
    _require_sha256(
        architecture.context_schema_sha256,
        name="architecture context_schema_sha256",
    )
    widths = tuple(
        _validated_integer(
            value,
            name=name,
            minimum=1,
            maximum=MAX_CONFIGURATION_ENERGY_WIDTH,
        )
        for name, value in (
            ("architecture event_hidden_width", architecture.event_hidden_width),
            (
                "architecture event_embedding_width",
                architecture.event_embedding_width,
            ),
            (
                "architecture context_hidden_width",
                architecture.context_hidden_width,
            ),
            (
                "architecture context_embedding_width",
                architecture.context_embedding_width,
            ),
            (
                "architecture readout_hidden_width",
                architecture.readout_hidden_width,
            ),
        )
    )
    if type(architecture.spectral_ceilings) is not SpectralNormCeilings:
        raise TypeError("architecture spectral ceilings have the wrong type")
    if "as_tuple" in vars(architecture.spectral_ceilings):
        raise ValueError("architecture spectral ceilings override their accessor")
    for value in (
        architecture.spectral_ceilings.event_input,
        architecture.spectral_ceilings.event_output,
        architecture.spectral_ceilings.context_input,
        architecture.spectral_ceilings.context_output,
        architecture.spectral_ceilings.readout_input,
        architecture.spectral_ceilings.readout_hidden,
        architecture.spectral_ceilings.readout_output,
    ):
        _validated_real(
            value,
            name="architecture spectral ceiling",
            strictly_positive=True,
            maximum=MAX_CONFIGURATION_ENERGY_NORM_CEILING,
        )
    value_bound = _validated_real(
        architecture.value_bound,
        name="architecture value_bound",
        strictly_positive=True,
    )
    _validated_real(
        architecture.bias_ceiling,
        name="architecture bias_ceiling",
        strictly_positive=True,
        maximum=MAX_CONFIGURATION_ENERGY_BIAS_CEILING,
    )
    first = _validated_real(
        architecture.first_derivative_ceiling,
        name="architecture first_derivative_ceiling",
        strictly_positive=True,
    )
    second = _validated_real(
        architecture.second_derivative_ceiling,
        name="architecture second_derivative_ceiling",
        strictly_positive=True,
    )
    EnergyBoundConsequences(value_bound, first, second)
    expected_parameters = ConfigurationEnergyArchitecture._parameter_count(
        dimensions,
        context_dimension=context_dimension,
        event_hidden_width=widths[0],
        event_embedding_width=widths[1],
        context_hidden_width=widths[2],
        context_embedding_width=widths[3],
        readout_hidden_width=widths[4],
    )
    if expected_parameters != architecture.expected_parameter_count:
        raise ValueError("architecture parameter count is inconsistent")
    if expected_parameters > MAX_CONFIGURATION_ENERGY_PARAMETERS:
        raise ConfigurationEnergyResourceError(
            "energy parameter count exceeds the implementation limit"
        )
    expected_digest = _semantic_digest(
        _architecture_contract_mapping(architecture)
    )
    if expected_digest != _require_sha256(
        architecture.architecture_sha256,
        name="architecture.architecture_sha256",
    ):
        raise ValueError("architecture digest is inconsistent")
    return architecture


class _Linear64(nn.Module):
    def __init__(
        self,
        input_features: int,
        output_features: int,
        *,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        self.input_features = input_features
        self.output_features = output_features
        self.weight = nn.Parameter(
            torch.empty(
                (output_features, input_features),
                dtype=torch.float64,
                device="cpu",
            )
        )
        self.bias = nn.Parameter(
            torch.zeros(output_features, dtype=torch.float64, device="cpu")
        )
        if self.weight.numel():
            nn.init.xavier_uniform_(self.weight, gain=1.0, generator=generator)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        result = F.linear(inputs, self.weight, self.bias)
        if bool(torch.any(~torch.isfinite(result)).detach().item()):
            raise ArithmeticError("configuration-energy affine map is non-finite")
        return result


def _stable_atan2_scale_first_derivative(
    coordinates: torch.Tensor, scales: torch.Tensor
) -> torch.Tensor:
    """Evaluate ``(2/pi) s / (x^2+s^2)`` without unsafe powers."""

    small = torch.abs(coordinates) <= scales
    small_coordinates = torch.where(
        small, coordinates, torch.zeros_like(coordinates)
    )
    large_coordinates = torch.where(small, scales, coordinates)
    small_ratio = small_coordinates / scales
    large_ratio = scales / large_coordinates
    small_denominator = 1.0 + small_ratio * small_ratio
    large_denominator = 1.0 + large_ratio * large_ratio
    constant = 2.0 / math.pi
    small_result = (constant / scales) / small_denominator
    large_result = (
        constant * large_ratio / large_coordinates
    ) / large_denominator
    return torch.where(small, small_result, large_result)


def _stable_atan2_scale_second_derivative(
    coordinates: torch.Tensor, scales: torch.Tensor
) -> torch.Tensor:
    """Evaluate the coordinate second derivative with bounded ratios."""

    small = torch.abs(coordinates) <= scales
    small_coordinates = torch.where(
        small, coordinates, torch.zeros_like(coordinates)
    )
    large_coordinates = torch.where(small, scales, coordinates)
    small_ratio = small_coordinates / scales
    large_ratio = scales / large_coordinates
    small_denominator = 1.0 + small_ratio * small_ratio
    large_denominator = 1.0 + large_ratio * large_ratio
    inverse_scale = 1.0 / scales
    inverse_large_coordinate = 1.0 / large_coordinates
    constant = -4.0 / math.pi
    small_result = (
        constant
        * small_ratio
        * inverse_scale
        * inverse_scale
        / (small_denominator * small_denominator)
    )
    large_result = (
        constant
        * large_ratio
        * inverse_large_coordinate
        * inverse_large_coordinate
        / (large_denominator * large_denominator)
    )
    return torch.where(small, small_result, large_result)


class _StableAtan2ScaleFirstDerivative(torch.autograd.Function):
    """First derivative primitive with an explicit stable second backward."""

    @staticmethod
    def forward(
        ctx: object, coordinates: torch.Tensor, scales: torch.Tensor
    ) -> torch.Tensor:
        ctx.save_for_backward(coordinates, scales)
        return _stable_atan2_scale_first_derivative(coordinates, scales)

    @staticmethod
    def backward(
        ctx: object, output_gradient: torch.Tensor
    ) -> Tuple[torch.Tensor, None]:
        coordinates, scales = ctx.saved_tensors
        second = _stable_atan2_scale_second_derivative(coordinates, scales)
        return output_gradient * second, None


class _StableAtan2Scale(torch.autograd.Function):
    """Native stable value with a range-partitioned stable backward."""

    @staticmethod
    def forward(
        ctx: object, coordinates: torch.Tensor, scales: torch.Tensor
    ) -> torch.Tensor:
        ctx.save_for_backward(coordinates, scales)
        return (2.0 / math.pi) * torch.atan2(coordinates, scales)

    @staticmethod
    def backward(
        ctx: object, output_gradient: torch.Tensor
    ) -> Tuple[torch.Tensor, None]:
        coordinates, scales = ctx.saved_tensors
        derivative = _StableAtan2ScaleFirstDerivative.apply(
            coordinates, scales
        )
        return output_gradient * derivative, None


class _EventEncoder(nn.Module):
    def __init__(
        self,
        scales: Tuple[float, ...],
        hidden_width: int,
        embedding_width: int,
        *,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        self.input_dimension = len(scales)
        self.hidden_width = hidden_width
        self.embedding_width = embedding_width
        self.register_buffer(
            "coordinate_scales",
            torch.tensor(scales, dtype=torch.float64, device="cpu"),
        )
        self.linear1 = _Linear64(
            self.input_dimension, hidden_width, generator=generator
        )
        self.linear2 = _Linear64(
            hidden_width, embedding_width, generator=generator
        )

    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        transformed = _StableAtan2Scale.apply(
            coordinates, self.coordinate_scales
        )
        if bool(torch.any(~torch.isfinite(transformed)).detach().item()):
            raise ArithmeticError("bounded coordinate transform is non-finite")
        hidden = torch.tanh(self.linear1(transformed))
        return torch.tanh(self.linear2(hidden))


class _ContextEncoder(nn.Module):
    def __init__(
        self,
        context_scales: Tuple[float, ...],
        hidden_width: int,
        embedding_width: int,
        *,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        self.context_dimension = len(context_scales)
        self.hidden_width = hidden_width
        self.embedding_width = embedding_width
        self.register_buffer(
            "context_scales",
            torch.tensor(context_scales, dtype=torch.float64, device="cpu"),
        )
        self.linear1 = _Linear64(
            self.context_dimension + 1, hidden_width, generator=generator
        )
        self.linear2 = _Linear64(
            hidden_width, embedding_width, generator=generator
        )

    def forward(
        self, normalized_time: torch.Tensor, context: torch.Tensor
    ) -> torch.Tensor:
        transformed_context = _StableAtan2Scale.apply(
            context, self.context_scales
        )
        inputs = torch.cat(
            (normalized_time.unsqueeze(-1), transformed_context), dim=-1
        )
        if bool(torch.any(~torch.isfinite(inputs)).detach().item()):
            raise ArithmeticError("bounded context transform is non-finite")
        hidden = torch.tanh(self.linear1(inputs))
        return torch.tanh(self.linear2(hidden))


class _Readout(nn.Module):
    def __init__(
        self,
        input_width: int,
        hidden_width: int,
        *,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        self.input_width = input_width
        self.hidden_width = hidden_width
        self.linear1 = _Linear64(input_width, hidden_width, generator=generator)
        self.linear2 = _Linear64(hidden_width, hidden_width, generator=generator)
        self.linear3 = _Linear64(hidden_width, 1, generator=generator)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        hidden1 = torch.tanh(self.linear1(inputs))
        hidden2 = torch.tanh(self.linear2(hidden1))
        return self.linear3(hidden2).squeeze(-1)


class _ExactSegmentSum(torch.autograd.Function):
    @staticmethod
    def forward(  # type: ignore[override]
        ctx: object,
        values: torch.Tensor,
        owners: torch.Tensor,
        batch_size: int,
    ) -> torch.Tensor:
        ctx.save_for_backward(owners)  # type: ignore[attr-defined]
        ctx.batch_size = batch_size  # type: ignore[attr-defined]
        buckets = [list() for _ in range(batch_size)]
        owner_values = tuple(int(value) for value in owners.detach().tolist())
        for row_index, owner in enumerate(owner_values):
            buckets[owner].append(row_index)
        rows = []
        width = int(values.shape[1])
        detached = values.detach()
        for indices in buckets:
            row = []
            for column in range(width):
                addends = [
                    float(detached[row_index, column].item())
                    for row_index in indices
                ]
                addends.sort(key=lambda scalar: (abs(scalar), scalar.hex()))
                row.append(math.fsum(addends))
            rows.append(row)
        result = torch.tensor(rows, dtype=torch.float64, device="cpu")
        if bool(torch.any(~torch.isfinite(result)).detach().item()):
            raise ArithmeticError("configuration-energy pooled value is non-finite")
        return result

    @staticmethod
    def backward(  # type: ignore[override]
        ctx: object, gradient: torch.Tensor
    ) -> Tuple[torch.Tensor, None, None]:
        (owners,) = ctx.saved_tensors  # type: ignore[attr-defined]
        return gradient.index_select(0, owners), None, None


def _exact_segment_sum(
    values: torch.Tensor, owners: torch.Tensor, batch_size: int
) -> torch.Tensor:
    return _ExactSegmentSum.apply(values, owners, batch_size)


@dataclass(frozen=True, eq=False, init=False)
class TypedConfigurationBatch:
    """Sealed ragged batch aligned to one architecture's sorted type order."""

    architecture_sha256: str
    forward_time: torch.Tensor
    context: torch.Tensor
    type_ids: Tuple[int, ...]
    coordinates: Tuple[torch.Tensor, ...]
    batch_indices: Tuple[torch.Tensor, ...]
    occurrence_counts: Tuple[int, ...]
    batch_size: int
    total_occurrences: int
    total_coordinates: int

    def __init__(
        self,
        *,
        architecture_sha256: str,
        forward_time: torch.Tensor,
        context: torch.Tensor,
        type_ids: Tuple[int, ...],
        coordinates: Tuple[torch.Tensor, ...],
        batch_indices: Tuple[torch.Tensor, ...],
        occurrence_counts: Tuple[int, ...],
        batch_size: int,
        total_occurrences: int,
        total_coordinates: int,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _BATCH_TOKEN:
            raise TypeError("typed configuration batches must be packed by the module")
        object.__setattr__(self, "architecture_sha256", architecture_sha256)
        object.__setattr__(self, "forward_time", forward_time)
        object.__setattr__(self, "context", context)
        object.__setattr__(self, "type_ids", type_ids)
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "batch_indices", batch_indices)
        object.__setattr__(self, "occurrence_counts", occurrence_counts)
        object.__setattr__(self, "batch_size", batch_size)
        object.__setattr__(self, "total_occurrences", total_occurrences)
        object.__setattr__(self, "total_coordinates", total_coordinates)


def _validate_batch(
    architecture: ConfigurationEnergyArchitecture,
    batch: object,
) -> TypedConfigurationBatch:
    architecture = _validate_architecture(architecture)
    if type(batch) is not TypedConfigurationBatch:
        raise TypeError("batch must be an exact TypedConfigurationBatch")
    if _require_sha256(
        batch.architecture_sha256, name="batch.architecture_sha256"
    ) != architecture.architecture_sha256:
        raise ValueError("batch and energy architecture differ")
    for field_name in (
        "type_ids",
        "coordinates",
        "batch_indices",
        "occurrence_counts",
    ):
        if type(getattr(batch, field_name)) is not tuple:
            raise TypeError("batch.%s must be an exact tuple" % field_name)
    if any(type(value) is not int for value in batch.type_ids):
        raise TypeError("batch.type_ids must contain exact integers")
    if any(type(value) is not int for value in batch.occurrence_counts):
        raise TypeError("batch.occurrence_counts must contain exact integers")
    for field_name in (
        "batch_size",
        "total_occurrences",
        "total_coordinates",
    ):
        if type(getattr(batch, field_name)) is not int:
            raise TypeError("batch.%s must be an exact integer" % field_name)
    if batch.type_ids != architecture.type_ids:
        raise ValueError("batch type order differs from the architecture")
    if not (
        len(batch.coordinates)
        == len(batch.batch_indices)
        == len(batch.occurrence_counts)
        == len(architecture.type_ids)
    ):
        raise ValueError("batch ragged fields are inconsistent")
    batch_size = _validated_integer(
        batch.batch_size,
        name="batch.batch_size",
        minimum=1,
        maximum=MAX_CONFIGURATION_ENERGY_BATCH_SIZE,
    )
    time = _require_float64_cpu_tensor(
        batch.forward_time,
        name="batch.forward_time",
        shape=(batch_size,),
        finite=False,
    )
    checked_context = _require_float64_cpu_tensor(
        batch.context,
        name="batch.context",
        shape=(batch_size, architecture.context_dimension),
        finite=False,
    )
    total_occurrences = 0
    total_coordinates = 0
    checked_coordinate_tensors = []
    checked_owner_tensors = []
    derived_counts = []
    for position, (dimension, coordinates, owners, declared_count) in enumerate(
        zip(
            architecture.type_dimensions,
            batch.coordinates,
            batch.batch_indices,
            batch.occurrence_counts,
        )
    ):
        checked_coordinates = _require_float64_cpu_tensor(
            coordinates,
            name="batch.coordinates[%d]" % position,
            finite=False,
        )
        if checked_coordinates.ndim != 2 or tuple(checked_coordinates.shape[1:]) != (
            dimension,
        ):
            raise ValueError(
                "batch coordinates for type %d have the wrong dimension"
                % architecture.type_ids[position]
            )
        count = int(checked_coordinates.shape[0])
        if _validated_integer(
            declared_count,
            name="batch.occurrence_counts[%d]" % position,
            minimum=0,
            maximum=MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES,
        ) != count:
            raise ValueError("batch occurrence count metadata changed")
        checked_owners = _require_owner_tensor(
            owners,
            name="batch.batch_indices[%d]" % position,
            occurrence_count=count,
            batch_size=batch_size,
            check_range=False,
        )
        checked_coordinate_tensors.append(checked_coordinates)
        checked_owner_tensors.append(checked_owners)
        derived_counts.append(count)
        total_occurrences += count
        total_coordinates += count * dimension
        if total_occurrences > MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES:
            raise ConfigurationEnergyResourceError(
                "batch occurrences exceed the implementation limit"
            )
        if total_coordinates > MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES:
            raise ConfigurationEnergyResourceError(
                "batch coordinates exceed the implementation limit"
            )
    if _validated_integer(
        batch.total_occurrences,
        name="batch.total_occurrences",
        minimum=0,
        maximum=MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES,
    ) != total_occurrences:
        raise ValueError("batch total-occurrence metadata changed")
    if _validated_integer(
        batch.total_coordinates,
        name="batch.total_coordinates",
        minimum=0,
        maximum=MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES,
    ) != total_coordinates:
        raise ValueError("batch total-coordinate metadata changed")
    if total_occurrences > MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES:
        raise ConfigurationEnergyResourceError(
            "batch occurrences exceed the implementation limit"
        )
    if total_coordinates > MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES:
        raise ConfigurationEnergyResourceError(
            "batch coordinates exceed the implementation limit"
        )
    counts_tuple = tuple(derived_counts)
    _preflight_forward_work(
        architecture,
        batch_size=batch_size,
        occurrence_counts=counts_tuple,
    )
    _require_independent_batch_float_storage(
        time, checked_context, tuple(checked_coordinate_tensors)
    )
    _require_float64_cpu_tensor(
        time,
        name="batch.forward_time",
        shape=(batch_size,),
    )
    _require_float64_cpu_tensor(
        checked_context,
        name="batch.context",
        shape=(batch_size, architecture.context_dimension),
    )
    if bool(torch.any(time < 0.0).detach().item()) or bool(
        torch.any(time > architecture.schedule_horizon).detach().item()
    ):
        raise ValueError("forward_time must lie in the process horizon")
    per_batch = torch.zeros(batch_size, dtype=torch.int64)
    for position, (coordinates, owners, count) in enumerate(
        zip(checked_coordinate_tensors, checked_owner_tensors, counts_tuple)
    ):
        _require_float64_cpu_tensor(
            coordinates,
            name="batch.coordinates[%d]" % position,
        )
        _require_owner_tensor(
            owners,
            name="batch.batch_indices[%d]" % position,
            occurrence_count=count,
            batch_size=batch_size,
        )
        if count:
            per_batch += torch.bincount(owners, minlength=batch_size)
    if int(torch.max(per_batch).item()) > architecture.total_cap:
        raise ValueError("a packed configuration exceeds the process cap")
    return batch


def pack_typed_configuration_batch(
    architecture: ConfigurationEnergyArchitecture,
    forward_time: object,
    context: object,
    coordinates_by_type: Mapping[int, torch.Tensor],
    batch_indices_by_type: Mapping[int, torch.Tensor],
) -> TypedConfigurationBatch:
    """Validate one differentiable ragged batch without padding coordinates."""

    architecture = _validate_architecture(architecture)
    time = _require_float64_cpu_tensor(
        forward_time, name="forward_time", finite=False
    )
    if time.ndim != 1:
        raise ValueError("forward_time must be one-dimensional")
    batch_size = _validated_integer(
        int(time.shape[0]),
        name="batch size",
        minimum=1,
        maximum=MAX_CONFIGURATION_ENERGY_BATCH_SIZE,
    )
    checked_context = _require_float64_cpu_tensor(
        context,
        name="context",
        shape=(batch_size, architecture.context_dimension),
        finite=False,
    )
    if not isinstance(coordinates_by_type, Mapping) or not isinstance(
        batch_indices_by_type, Mapping
    ):
        raise TypeError("coordinate and batch-index collections must be mappings")
    coordinate_keys_tuple = _validated_type_mapping_keys(
        coordinates_by_type, name="coordinates_by_type"
    )
    owner_keys_tuple = _validated_type_mapping_keys(
        batch_indices_by_type, name="batch_indices_by_type"
    )
    coordinate_keys = set(coordinate_keys_tuple)
    owner_keys = set(owner_keys_tuple)
    known = set(architecture.type_ids)
    if coordinate_keys != owner_keys:
        raise ValueError("coordinate and batch-index mappings have different keys")
    if not coordinate_keys.issubset(known):
        raise ValueError("packed batch contains an unknown event type")
    coordinate_mapping = {
        event_type: coordinates_by_type[event_type]
        for event_type in coordinate_keys_tuple
    }
    owner_mapping = {
        event_type: batch_indices_by_type[event_type]
        for event_type in owner_keys_tuple
    }
    coordinates = []
    owners = []
    counts = []
    total_occurrences = 0
    total_coordinates = 0
    for event_type, dimension in zip(
        architecture.type_ids, architecture.type_dimensions
    ):
        if event_type not in coordinate_keys:
            coordinate = torch.empty(
                (0, dimension), dtype=torch.float64, device="cpu"
            )
            owner = torch.empty((0,), dtype=torch.int64, device="cpu")
        else:
            coordinate = _require_float64_cpu_tensor(
                coordinate_mapping[event_type],
                name="coordinates_by_type[%d]" % event_type,
                finite=False,
            )
            if coordinate.ndim != 2 or tuple(coordinate.shape[1:]) != (dimension,):
                raise ValueError(
                    "coordinates for type %d must have shape (n, %d)"
                    % (event_type, dimension)
                )
            owner = _require_owner_tensor(
                owner_mapping[event_type],
                name="batch_indices_by_type[%d]" % event_type,
                occurrence_count=int(coordinate.shape[0]),
                batch_size=batch_size,
                check_range=False,
            )
        count = int(coordinate.shape[0])
        coordinates.append(coordinate)
        owners.append(owner)
        counts.append(count)
        total_occurrences += count
        total_coordinates += count * dimension
        if total_occurrences > MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES:
            raise ConfigurationEnergyResourceError(
                "batch occurrences exceed the implementation limit"
            )
        if total_coordinates > MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES:
            raise ConfigurationEnergyResourceError(
                "batch coordinates exceed the implementation limit"
            )
    counts_tuple = tuple(counts)
    _preflight_forward_work(
        architecture,
        batch_size=batch_size,
        occurrence_counts=counts_tuple,
    )
    _require_independent_batch_float_storage(
        time, checked_context, tuple(coordinates)
    )
    _require_float64_cpu_tensor(
        time, name="forward_time", shape=(batch_size,)
    )
    _require_float64_cpu_tensor(
        checked_context,
        name="context",
        shape=(batch_size, architecture.context_dimension),
    )
    if bool(torch.any(time < 0.0).detach().item()) or bool(
        torch.any(time > architecture.schedule_horizon).detach().item()
    ):
        raise ValueError("forward_time must lie in the process horizon")
    per_batch = torch.zeros(batch_size, dtype=torch.int64)
    for position, (coordinate, owner, count) in enumerate(
        zip(coordinates, owners, counts_tuple)
    ):
        _require_float64_cpu_tensor(
            coordinate,
            name="coordinates_by_type[%d]" % architecture.type_ids[position],
        )
        _require_owner_tensor(
            owner,
            name="batch_indices_by_type[%d]" % architecture.type_ids[position],
            occurrence_count=count,
            batch_size=batch_size,
        )
        if count:
            per_batch += torch.bincount(owner, minlength=batch_size)
    if int(torch.max(per_batch).item()) > architecture.total_cap:
        raise ValueError("a packed configuration exceeds the process cap")
    result = TypedConfigurationBatch(
        architecture_sha256=architecture.architecture_sha256,
        forward_time=time,
        context=checked_context,
        type_ids=architecture.type_ids,
        coordinates=tuple(coordinates),
        batch_indices=tuple(owners),
        occurrence_counts=counts_tuple,
        batch_size=batch_size,
        total_occurrences=total_occurrences,
        total_coordinates=total_coordinates,
        _construction_token=_BATCH_TOKEN,
    )
    return _validate_batch(architecture, result)


class BoundedConfigurationEnergy(nn.Module):
    """Frozen-graph typed DeepSets scalar on CPU binary64 tensors."""

    def __init__(
        self,
        architecture: ConfigurationEnergyArchitecture,
        *,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        architecture = _validate_architecture(architecture)
        if not isinstance(generator, torch.Generator):
            raise TypeError("generator must be a torch.Generator")
        if generator.device.type != "cpu":
            raise ValueError("generator must be a CPU generator")
        self.architecture = architecture
        self.event_encoders = nn.ModuleList(
            [
                _EventEncoder(
                    scales,
                    architecture.event_hidden_width,
                    architecture.event_embedding_width,
                    generator=generator,
                )
                for scales in architecture.coordinate_scales
            ]
        )
        self.context_encoder = _ContextEncoder(
            architecture.context_scales,
            architecture.context_hidden_width,
            architecture.context_embedding_width,
            generator=generator,
        )
        self.readout = _Readout(
            architecture.event_embedding_width
            + architecture.context_embedding_width
            + 1,
            architecture.readout_hidden_width,
            generator=generator,
        )
        if self.parameter_count != architecture.expected_parameter_count:
            raise ArithmeticError("constructed energy parameter count is inconsistent")

    @property
    def parameter_count(self) -> int:
        return sum(int(parameter.numel()) for parameter in self.parameters())

    def _validate_state(self) -> None:
        _validate_architecture(self.architecture)
        if self.parameter_count != self.architecture.expected_parameter_count:
            raise ValueError("energy parameter count changed")
        for name, tensor in self.state_dict().items():
            _require_float64_cpu_tensor(tensor, name="energy state %s" % name)
        for index, (encoder, scales) in enumerate(
            zip(self.event_encoders, self.architecture.coordinate_scales)
        ):
            expected = torch.tensor(scales, dtype=torch.float64, device="cpu")
            if not torch.equal(encoder.coordinate_scales, expected):
                raise ValueError(
                    "event coordinate-scale buffer %d differs from the architecture"
                    % index
                )
        expected_context = torch.tensor(
            self.architecture.context_scales,
            dtype=torch.float64,
            device="cpu",
        )
        if not torch.equal(
            self.context_encoder.context_scales, expected_context
        ):
            raise ValueError(
                "context-scale buffer differs from the architecture"
            )

    def raw_scalar(self, batch: TypedConfigurationBatch) -> torch.Tensor:
        checked = _validate_batch(self.architecture, batch)
        self._validate_state()
        _require_batch_inputs_independent_of_model(self, (checked,))
        pooled = torch.zeros(
            (
                checked.batch_size,
                self.architecture.event_embedding_width,
            ),
            dtype=torch.float64,
            device="cpu",
        )
        for encoder, coordinates, owners in zip(
            self.event_encoders,
            checked.coordinates,
            checked.batch_indices,
        ):
            if coordinates.shape[0] == 0:
                continue
            encoded = encoder(coordinates)
            pooled = pooled + _exact_segment_sum(
                encoded, owners, checked.batch_size
            )
        normalized_time = 2.0 * (
            checked.forward_time / self.architecture.schedule_horizon
        ) - 1.0
        context_embedding = self.context_encoder(
            normalized_time, checked.context
        )
        counts = torch.zeros(checked.batch_size, dtype=torch.float64)
        for owners in checked.batch_indices:
            if owners.numel():
                counts += torch.bincount(
                    owners, minlength=checked.batch_size
                ).to(dtype=torch.float64)
        denominator = max(1, self.architecture.total_cap)
        normalized_count = counts / float(denominator)
        readout_input = torch.cat(
            (pooled, context_embedding, normalized_count.unsqueeze(-1)), dim=-1
        )
        raw = self.readout(readout_input)
        if bool(torch.any(~torch.isfinite(raw)).detach().item()):
            raise ArithmeticError("configuration-energy raw scalar is non-finite")
        return raw

    def forward(self, batch: TypedConfigurationBatch) -> torch.Tensor:
        raw = self.raw_scalar(batch)
        bound = self.architecture.value_bound
        result = bound * torch.tanh(raw / bound)
        if bool(torch.any(~torch.isfinite(result)).detach().item()):
            raise ArithmeticError("bounded configuration energy is non-finite")
        if bool(torch.any(torch.abs(result) > bound).detach().item()):
            raise ArithmeticError("bounded configuration energy exceeded its bound")
        return result


def _python_callable_fingerprint(value: object) -> str:
    code = getattr(value, "__code__", None)
    if code is None:
        raise TypeError("frozen Python callable has no code object")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-configuration-energy-callable-v1\x00")
    digest.update(marshal.dumps(code))
    digest.update(repr(getattr(value, "__defaults__", None)).encode("utf-8"))
    digest.update(repr(getattr(value, "__kwdefaults__", None)).encode("utf-8"))
    closure = getattr(value, "__closure__", None)
    if closure:
        digest.update(
            repr(tuple(cell.cell_contents for cell in closure)).encode("utf-8")
        )
    return digest.hexdigest()


def _frozen_python_callable(value: object) -> Tuple[object, str]:
    return value, _python_callable_fingerprint(value)


def _class_namespace_value_fingerprint(value: object) -> object:
    if type(value) in (staticmethod, classmethod):
        functions = (value.__func__,)
    elif type(value) is property:
        functions = (value.fget, value.fset, value.fdel)
    elif getattr(value, "__code__", None) is not None:
        functions = (value,)
    else:
        return None
    return tuple(
        None if function is None else _python_callable_fingerprint(function)
        for function in functions
    )


_FROZEN_CONFIGURATION_ENERGY_CLASS_METHODS = (
    (
        _StableAtan2ScaleFirstDerivative,
        "forward",
        *_frozen_python_callable(_StableAtan2ScaleFirstDerivative.forward),
    ),
    (
        _StableAtan2ScaleFirstDerivative,
        "backward",
        *_frozen_python_callable(_StableAtan2ScaleFirstDerivative.backward),
    ),
    (
        _StableAtan2Scale,
        "forward",
        *_frozen_python_callable(_StableAtan2Scale.forward),
    ),
    (
        _StableAtan2Scale,
        "backward",
        *_frozen_python_callable(_StableAtan2Scale.backward),
    ),
    (_Linear64, "forward", *_frozen_python_callable(_Linear64.forward)),
    (_EventEncoder, "forward", *_frozen_python_callable(_EventEncoder.forward)),
    (
        _ContextEncoder,
        "forward",
        *_frozen_python_callable(_ContextEncoder.forward),
    ),
    (_Readout, "forward", *_frozen_python_callable(_Readout.forward)),
    (
        _ExactSegmentSum,
        "forward",
        *_frozen_python_callable(_ExactSegmentSum.forward),
    ),
    (
        _ExactSegmentSum,
        "backward",
        *_frozen_python_callable(_ExactSegmentSum.backward),
    ),
    (
        BoundedConfigurationEnergy,
        "_validate_state",
        *_frozen_python_callable(BoundedConfigurationEnergy._validate_state),
    ),
    (
        BoundedConfigurationEnergy,
        "raw_scalar",
        *_frozen_python_callable(BoundedConfigurationEnergy.raw_scalar),
    ),
    (
        BoundedConfigurationEnergy,
        "forward",
        *_frozen_python_callable(BoundedConfigurationEnergy.forward),
    ),
)
_FROZEN_CONFIGURATION_ENERGY_GLOBAL_CALLABLES = (
    (
        "_stable_atan2_scale_first_derivative",
        *_frozen_python_callable(_stable_atan2_scale_first_derivative),
    ),
    (
        "_stable_atan2_scale_second_derivative",
        *_frozen_python_callable(_stable_atan2_scale_second_derivative),
    ),
    ("_exact_segment_sum", *_frozen_python_callable(_exact_segment_sum)),
    ("_validate_batch", *_frozen_python_callable(_validate_batch)),
)

_CONFIGURATION_ENERGY_CUSTOM_MODULE_CLASSES = (
    _Linear64,
    _EventEncoder,
    _ContextEncoder,
    _Readout,
    BoundedConfigurationEnergy,
)
_CONFIGURATION_ENERGY_AUTOGRAD_FUNCTION_CLASSES = (
    _StableAtan2ScaleFirstDerivative,
    _StableAtan2Scale,
    _ExactSegmentSum,
)
_CONFIGURATION_ENERGY_RESOLVED_CUSTODY_METHOD_NAMES = (
    "__call__",
    "__getattribute__",
    "__getattr__",
    "__setattr__",
    "__delattr__",
    "_wrapped_call_impl",
    "_call_impl",
    "_compiled_call_impl",
    "_slow_forward",
    "state_dict",
    "_save_to_state_dict",
    "load_state_dict",
    "_load_from_state_dict",
    "named_modules",
    "named_parameters",
    "named_buffers",
    "parameters",
    "buffers",
    "_named_members",
)
_FROZEN_CONFIGURATION_ENERGY_RESOLVED_CUSTODY_METHODS = tuple(
    (
        owner,
        name,
        getattr(owner, name, None),
        (
            _python_callable_fingerprint(getattr(owner, name))
            if getattr(getattr(owner, name, None), "__code__", None)
            is not None
            else None
        ),
    )
    for owner in _CONFIGURATION_ENERGY_CUSTOM_MODULE_CLASSES
    for name in _CONFIGURATION_ENERGY_RESOLVED_CUSTODY_METHOD_NAMES
)
_FROZEN_CONFIGURATION_ENERGY_CLASS_NAMESPACE = tuple(
    (
        owner,
        tuple(
            (
                name,
                value,
                _class_namespace_value_fingerprint(value),
            )
            for name, value in vars(owner).items()
        ),
    )
    for owner in (
        *_CONFIGURATION_ENERGY_CUSTOM_MODULE_CLASSES,
        *_CONFIGURATION_ENERGY_AUTOGRAD_FUNCTION_CLASSES,
    )
)

_CONFIGURATION_ENERGY_BASE_MODULE_INSTANCE_KEYS = frozenset(
    (
        "training",
        "_parameters",
        "_buffers",
        "_non_persistent_buffers_set",
        "_backward_pre_hooks",
        "_backward_hooks",
        "_is_full_backward_hook",
        "_forward_hooks",
        "_forward_hooks_with_kwargs",
        "_forward_hooks_always_called",
        "_forward_pre_hooks",
        "_forward_pre_hooks_with_kwargs",
        "_state_dict_hooks",
        "_state_dict_pre_hooks",
        "_load_state_dict_pre_hooks",
        "_load_state_dict_post_hooks",
        "_modules",
    )
)


def _expected_module_instance_keys(module: nn.Module) -> frozenset[str]:
    metadata = {
        BoundedConfigurationEnergy: ("architecture",),
        nn.ModuleList: (),
        _EventEncoder: (
            "input_dimension",
            "hidden_width",
            "embedding_width",
        ),
        _ContextEncoder: (
            "context_dimension",
            "hidden_width",
            "embedding_width",
        ),
        _Readout: ("input_width", "hidden_width"),
        _Linear64: ("input_features", "output_features"),
    }
    extra = metadata.get(type(module))
    if extra is None:  # pragma: no cover - frozen graph establishes the types
        raise TypeError("unsupported configuration-energy module type")
    return _CONFIGURATION_ENERGY_BASE_MODULE_INSTANCE_KEYS | frozenset(extra)


def _require_exact_module_metadata(
    module: nn.Module,
    *,
    name: str,
    expected: Tuple[Tuple[str, int], ...],
) -> None:
    namespace = vars(module)
    if type(namespace) is not dict:
        raise ValueError(
            "model module %s has a non-exact instance namespace" % name
        )
    for field_name, expected_value in expected:
        value = namespace.get(field_name)
        if type(value) is not int or value != expected_value:
            raise ValueError(
                "model module %s has invalid integer metadata %s"
                % (name, field_name)
            )


def _expected_state_shapes(
    architecture: ConfigurationEnergyArchitecture,
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    result = []
    for index, dimension in enumerate(architecture.type_dimensions):
        prefix = "event_encoders.%d" % index
        result.extend(
            (
                (prefix + ".coordinate_scales", (dimension,)),
                (
                    prefix + ".linear1.weight",
                    (architecture.event_hidden_width, dimension),
                ),
                (
                    prefix + ".linear1.bias",
                    (architecture.event_hidden_width,),
                ),
                (
                    prefix + ".linear2.weight",
                    (
                        architecture.event_embedding_width,
                        architecture.event_hidden_width,
                    ),
                ),
                (
                    prefix + ".linear2.bias",
                    (architecture.event_embedding_width,),
                ),
            )
        )
    result.extend(
        (
            (
                "context_encoder.context_scales",
                (architecture.context_dimension,),
            ),
            (
                "context_encoder.linear1.weight",
                (
                    architecture.context_hidden_width,
                    architecture.context_dimension + 1,
                ),
            ),
            (
                "context_encoder.linear1.bias",
                (architecture.context_hidden_width,),
            ),
            (
                "context_encoder.linear2.weight",
                (
                    architecture.context_embedding_width,
                    architecture.context_hidden_width,
                ),
            ),
            (
                "context_encoder.linear2.bias",
                (architecture.context_embedding_width,),
            ),
            (
                "readout.linear1.weight",
                (
                    architecture.readout_hidden_width,
                    architecture.event_embedding_width
                    + architecture.context_embedding_width
                    + 1,
                ),
            ),
            (
                "readout.linear1.bias",
                (architecture.readout_hidden_width,),
            ),
            (
                "readout.linear2.weight",
                (
                    architecture.readout_hidden_width,
                    architecture.readout_hidden_width,
                ),
            ),
            (
                "readout.linear2.bias",
                (architecture.readout_hidden_width,),
            ),
            (
                "readout.linear3.weight",
                (1, architecture.readout_hidden_width),
            ),
            ("readout.linear3.bias", (1,)),
        )
    )
    return tuple(result)


def _expected_modules(
    model: BoundedConfigurationEnergy,
) -> Dict[str, nn.Module]:
    result: Dict[str, nn.Module] = {
        "": model,
        "event_encoders": model.event_encoders,
    }
    for index, encoder in enumerate(model.event_encoders):
        prefix = "event_encoders.%d" % index
        result[prefix] = encoder
        result[prefix + ".linear1"] = encoder.linear1
        result[prefix + ".linear2"] = encoder.linear2
    result.update(
        {
            "context_encoder": model.context_encoder,
            "context_encoder.linear1": model.context_encoder.linear1,
            "context_encoder.linear2": model.context_encoder.linear2,
            "readout": model.readout,
            "readout.linear1": model.readout.linear1,
            "readout.linear2": model.readout.linear2,
            "readout.linear3": model.readout.linear3,
        }
    )
    return result


def _require_exact_module_registries(module: nn.Module, *, name: str) -> None:
    for field_name in ("_parameters", "_buffers", "_modules"):
        registry = getattr(module, field_name, None)
        if type(registry) is not dict:
            raise ValueError(
                "model module %s has a non-exact %s registry"
                % (name, field_name)
            )
        if any(value is None for value in registry.values()):
            raise ValueError(
                "model module %s has a ghost %s registry entry"
                % (name, field_name)
            )
    if type(getattr(module, "_non_persistent_buffers_set", None)) is not set:
        raise ValueError(
            "model module %s has a non-exact buffer-persistence registry"
            % name
        )
    if module._non_persistent_buffers_set:
        raise ValueError(
            "model module %s has unsupported nonpersistent buffers" % name
        )
    for field_name in (
        "_forward_hooks",
        "_forward_hooks_with_kwargs",
        "_forward_hooks_always_called",
        "_forward_pre_hooks",
        "_forward_pre_hooks_with_kwargs",
        "_backward_hooks",
        "_backward_pre_hooks",
        "_state_dict_hooks",
        "_state_dict_pre_hooks",
        "_load_state_dict_pre_hooks",
        "_load_state_dict_post_hooks",
    ):
        if type(getattr(module, field_name, None)) is not OrderedDict:
            raise ValueError(
                "model module %s has a non-exact hook registry" % name
            )
    if getattr(module, "_is_full_backward_hook", None) is not None:
        raise ValueError("model module %s carries unsupported hooks" % name)


def _require_direct_module_registry_keys(
    module: nn.Module,
    *,
    name: str,
    parameter_keys: Tuple[str, ...] = (),
    buffer_keys: Tuple[str, ...] = (),
    module_keys: Tuple[str, ...] = (),
) -> None:
    expected = (
        ("_parameters", parameter_keys),
        ("_buffers", buffer_keys),
        ("_modules", module_keys),
    )
    for field_name, keys in expected:
        observed = tuple(getattr(module, field_name))
        if any(type(key) is not str for key in observed) or observed != keys:
            raise ValueError(
                "model module %s direct %s registry keys differ"
                % (name, field_name)
            )


def _validate_frozen_graph(model: object) -> BoundedConfigurationEnergy:
    for owner, expected_items in (
        _FROZEN_CONFIGURATION_ENERGY_CLASS_NAMESPACE
    ):
        current_namespace = vars(owner)
        if tuple(current_namespace) != tuple(
            name for name, _, _ in expected_items
        ):
            raise ValueError(
                "configuration-energy class namespace or class method %s changed"
                % owner.__name__
            )
        for name, expected_value, expected_fingerprint in expected_items:
            current_value = current_namespace[name]
            if current_value is not expected_value or (
                expected_fingerprint is not None
                and _class_namespace_value_fingerprint(current_value)
                != expected_fingerprint
            ):
                raise ValueError(
                    "configuration-energy class namespace or class method "
                    "%s changed"
                    % owner.__name__
                )
    for owner, name, expected, fingerprint in (
        _FROZEN_CONFIGURATION_ENERGY_RESOLVED_CUSTODY_METHODS
    ):
        current = getattr(owner, name, None)
        if current is not expected or (
            fingerprint is not None
            and _python_callable_fingerprint(current) != fingerprint
        ):
            raise ValueError(
                "configuration-energy resolved class method %s.%s changed"
                % (owner.__name__, name)
            )
    for owner in _CONFIGURATION_ENERGY_AUTOGRAD_FUNCTION_CLASSES:
        if "apply" in owner.__dict__:
            raise ValueError(
                "configuration-energy autograd dispatch %s.apply changed"
                % owner.__name__
            )
    for owner, name, expected, fingerprint in (
        _FROZEN_CONFIGURATION_ENERGY_CLASS_METHODS
    ):
        current = getattr(owner, name, None)
        if current is not expected or (
            _python_callable_fingerprint(current) != fingerprint
        ):
            raise ValueError(
                "configuration-energy class method %s.%s changed"
                % (owner.__name__, name)
            )
    for name, expected, fingerprint in (
        _FROZEN_CONFIGURATION_ENERGY_GLOBAL_CALLABLES
    ):
        current = globals().get(name)
        if current is not expected or (
            _python_callable_fingerprint(current) != fingerprint
        ):
            raise ValueError(
                "configuration-energy evaluation function %s changed" % name
            )
    if type(model) is not BoundedConfigurationEnergy:
        raise TypeError("model must be an exact BoundedConfigurationEnergy")
    _require_exact_module_registries(model, name="<root>")
    _require_direct_module_registry_keys(
        model,
        name="<root>",
        module_keys=("event_encoders", "context_encoder", "readout"),
    )
    architecture = _validate_architecture(model.architecture)
    if type(model.event_encoders) is not nn.ModuleList:
        raise ValueError("event encoder container differs from the frozen graph")
    _require_exact_module_registries(
        model.event_encoders, name="event_encoders"
    )
    _require_direct_module_registry_keys(
        model.event_encoders,
        name="event_encoders",
        module_keys=tuple(
            str(index) for index in range(len(architecture.type_ids))
        ),
    )
    if len(model.event_encoders) != len(architecture.type_ids):
        raise ValueError("event encoder count differs from the architecture")
    for index, (encoder, dimension) in enumerate(
        zip(model.event_encoders, architecture.type_dimensions)
    ):
        if type(encoder) is not _EventEncoder:
            raise ValueError("event encoder %d has the wrong graph type" % index)
        _require_exact_module_registries(
            encoder, name="event_encoders.%d" % index
        )
        _require_direct_module_registry_keys(
            encoder,
            name="event_encoders.%d" % index,
            buffer_keys=("coordinate_scales",),
            module_keys=("linear1", "linear2"),
        )
        if type(encoder.linear1) is not _Linear64 or type(
            encoder.linear2
        ) is not _Linear64:
            raise ValueError("event encoder affine graph changed")
        _require_exact_module_metadata(
            encoder,
            name="event_encoders.%d" % index,
            expected=(
                ("input_dimension", dimension),
                ("hidden_width", architecture.event_hidden_width),
                ("embedding_width", architecture.event_embedding_width),
            ),
        )
        _require_exact_module_metadata(
            encoder.linear1,
            name="event_encoders.%d.linear1" % index,
            expected=(
                ("input_features", dimension),
                ("output_features", architecture.event_hidden_width),
            ),
        )
        _require_exact_module_metadata(
            encoder.linear2,
            name="event_encoders.%d.linear2" % index,
            expected=(
                ("input_features", architecture.event_hidden_width),
                ("output_features", architecture.event_embedding_width),
            ),
        )
        _require_exact_module_registries(
            encoder.linear1, name="event_encoders.%d.linear1" % index
        )
        _require_exact_module_registries(
            encoder.linear2, name="event_encoders.%d.linear2" % index
        )
        _require_direct_module_registry_keys(
            encoder.linear1,
            name="event_encoders.%d.linear1" % index,
            parameter_keys=("weight", "bias"),
        )
        _require_direct_module_registry_keys(
            encoder.linear2,
            name="event_encoders.%d.linear2" % index,
            parameter_keys=("weight", "bias"),
        )
    if type(model.context_encoder) is not _ContextEncoder or type(
        model.context_encoder.linear1
    ) is not _Linear64 or type(model.context_encoder.linear2) is not _Linear64:
        raise ValueError("context encoder graph changed")
    _require_exact_module_metadata(
        model.context_encoder,
        name="context_encoder",
        expected=(
            ("context_dimension", architecture.context_dimension),
            ("hidden_width", architecture.context_hidden_width),
            ("embedding_width", architecture.context_embedding_width),
        ),
    )
    _require_exact_module_metadata(
        model.context_encoder.linear1,
        name="context_encoder.linear1",
        expected=(
            ("input_features", architecture.context_dimension + 1),
            ("output_features", architecture.context_hidden_width),
        ),
    )
    _require_exact_module_metadata(
        model.context_encoder.linear2,
        name="context_encoder.linear2",
        expected=(
            ("input_features", architecture.context_hidden_width),
            ("output_features", architecture.context_embedding_width),
        ),
    )
    _require_exact_module_registries(
        model.context_encoder, name="context_encoder"
    )
    _require_exact_module_registries(
        model.context_encoder.linear1, name="context_encoder.linear1"
    )
    _require_exact_module_registries(
        model.context_encoder.linear2, name="context_encoder.linear2"
    )
    _require_direct_module_registry_keys(
        model.context_encoder,
        name="context_encoder",
        buffer_keys=("context_scales",),
        module_keys=("linear1", "linear2"),
    )
    _require_direct_module_registry_keys(
        model.context_encoder.linear1,
        name="context_encoder.linear1",
        parameter_keys=("weight", "bias"),
    )
    _require_direct_module_registry_keys(
        model.context_encoder.linear2,
        name="context_encoder.linear2",
        parameter_keys=("weight", "bias"),
    )
    if type(model.readout) is not _Readout:
        raise ValueError("readout graph changed")
    _require_exact_module_metadata(
        model.readout,
        name="readout",
        expected=(
            (
                "input_width",
                architecture.event_embedding_width
                + architecture.context_embedding_width
                + 1,
            ),
            ("hidden_width", architecture.readout_hidden_width),
        ),
    )
    _require_exact_module_registries(model.readout, name="readout")
    if any(
        type(layer) is not _Linear64
        for layer in (
            model.readout.linear1,
            model.readout.linear2,
            model.readout.linear3,
        )
    ):
        raise ValueError("readout affine graph changed")
    _require_exact_module_registries(
        model.readout.linear1, name="readout.linear1"
    )
    _require_exact_module_registries(
        model.readout.linear2, name="readout.linear2"
    )
    _require_exact_module_registries(
        model.readout.linear3, name="readout.linear3"
    )
    _require_direct_module_registry_keys(
        model.readout,
        name="readout",
        module_keys=("linear1", "linear2", "linear3"),
    )
    for index, layer in enumerate(
        (
            model.readout.linear1,
            model.readout.linear2,
            model.readout.linear3,
        ),
        start=1,
    ):
        _require_direct_module_registry_keys(
            layer,
            name="readout.linear%d" % index,
            parameter_keys=("weight", "bias"),
        )
    _require_exact_module_metadata(
        model.readout.linear1,
        name="readout.linear1",
        expected=(
            ("input_features", model.readout.input_width),
            ("output_features", architecture.readout_hidden_width),
        ),
    )
    _require_exact_module_metadata(
        model.readout.linear2,
        name="readout.linear2",
        expected=(
            ("input_features", architecture.readout_hidden_width),
            ("output_features", architecture.readout_hidden_width),
        ),
    )
    _require_exact_module_metadata(
        model.readout.linear3,
        name="readout.linear3",
        expected=(
            ("input_features", architecture.readout_hidden_width),
            ("output_features", 1),
        ),
    )
    expected_modules = _expected_modules(model)
    custody_method_names = (
        "forward",
        "_call_impl",
        "_compiled_call_impl",
        "_slow_forward",
        "state_dict",
        "_save_to_state_dict",
        "load_state_dict",
        "_load_from_state_dict",
        "named_modules",
        "named_parameters",
        "named_buffers",
        "parameters",
        "buffers",
        "_named_members",
    )
    for name, module in expected_modules.items():
        namespace = vars(module)
        if type(namespace) is not dict:
            raise ValueError(
                "model module %s has a non-exact instance namespace"
                % (name or "<root>")
            )
        instance_keys = tuple(namespace)
        if any(type(key) is not str for key in instance_keys):
            raise ValueError(
                "model module %s has unexpected instance attributes"
                % (name or "<root>")
            )
        for method_name in custody_method_names:
            if method_name in namespace:
                raise ValueError(
                    "model module %s overrides custody method %s"
                    % (name or "<root>", method_name)
                )
        if frozenset(instance_keys) != _expected_module_instance_keys(module):
            raise ValueError(
                "model module %s has unexpected instance attributes"
                % (name or "<root>")
            )
        if type(module.training) is not bool:
            raise ValueError(
                "model module %s has invalid training metadata"
                % (name or "<root>")
            )
    if dict(model.named_modules()) != expected_modules:
        raise ValueError("model graph differs from the frozen architecture")
    hook_fields = (
        "_forward_hooks",
        "_forward_hooks_with_kwargs",
        "_forward_hooks_always_called",
        "_forward_pre_hooks",
        "_forward_pre_hooks_with_kwargs",
        "_backward_hooks",
        "_backward_pre_hooks",
        "_state_dict_hooks",
        "_state_dict_pre_hooks",
        "_load_state_dict_pre_hooks",
        "_load_state_dict_post_hooks",
    )
    for name, module in expected_modules.items():
        for field_name in hook_fields:
            hooks = getattr(module, field_name, None)
            if hooks:
                raise ValueError(
                    "model module %s carries unsupported hooks" % (name or "<root>")
                )
        parametrizations = getattr(module, "parametrizations", None)
        if parametrizations is not None and len(parametrizations):
            raise ValueError("model parametrizations are not certificate-admissible")
    if "raw_scalar" in model.__dict__ or "_validate_state" in model.__dict__:
        raise ValueError("model overrides a frozen evaluation method")
    live_parameter_items = tuple(
        model.named_parameters(remove_duplicate=False)
    )
    live_buffer_items = tuple(model.named_buffers(remove_duplicate=False))
    for name, parameter in live_parameter_items:
        if type(parameter) is not nn.Parameter:
            raise ValueError("model parameter %s has the wrong tensor type" % name)
        if vars(parameter):
            raise ValueError(
                "model parameter %s carries unsupported instance attributes"
                % name
            )
        if not parameter.requires_grad:
            raise ValueError(
                "model parameter %s must require gradients" % name
            )
        _require_exact_tensor_hook_registries(
            parameter, name="model parameter %s" % name
        )
    for name, buffer in live_buffer_items:
        if type(buffer) is not torch.Tensor:
            raise ValueError("model buffer %s has the wrong tensor type" % name)
        if vars(buffer):
            raise ValueError(
                "model buffer %s carries unsupported instance attributes"
                % name
            )
        if buffer.requires_grad:
            raise ValueError("model buffer %s must not require gradients" % name)
    expected_shapes = _expected_state_shapes(architecture)
    state = model.state_dict()
    if tuple(state) != tuple(name for name, _ in expected_shapes):
        raise ValueError("model state keys differ from the frozen architecture")
    occupied_state = []
    for (name, shape), tensor in zip(expected_shapes, state.values()):
        if tuple(tensor.shape) != shape:
            raise ValueError("model state tensor %s has the wrong shape" % name)
        if not tensor.is_contiguous():
            raise ValueError("model state tensor %s must be contiguous" % name)
        if tensor.numel():
            start = tensor.data_ptr()
            end = start + tensor.numel() * tensor.element_size()
            for previous_start, previous_end, previous_name in occupied_state:
                if start < previous_end and previous_start < end:
                    raise ValueError(
                        "model state tensors %s and %s contain unsupported "
                        "shared storage" % (previous_name, name)
                    )
            occupied_state.append((start, end, name))
    parameter_names = tuple(name for name, _ in live_parameter_items)
    expected_parameter_names = tuple(
        name for name, _ in expected_shapes if not name.endswith("scales")
    )
    if parameter_names != expected_parameter_names:
        raise ValueError("model parameters differ from the frozen architecture")
    parameter_values = tuple(
        parameter for _, parameter in live_parameter_items
    )
    if len({id(parameter) for parameter in parameter_values}) != len(
        parameter_values
    ):
        raise ValueError("model parameters contain an unsupported alias")
    model._validate_state()
    return model


def _tensor_sha256_items(
    architecture_sha256: str,
    items: Tuple[Tuple[str, torch.Tensor], ...],
) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-configuration-energy-state-v1\x00")
    digest.update(architecture_sha256.encode("ascii"))
    for name, tensor in items:
        checked = _require_float64_cpu_tensor(
            tensor, name="checkpoint tensor %s" % name
        )
        contiguous = checked.detach().contiguous()
        encoded_name = name.encode("utf-8")
        encoded_dtype = str(contiguous.dtype).encode("ascii")
        encoded_shape = repr(tuple(contiguous.shape)).encode("ascii")
        encoded_bytes = contiguous.numpy().tobytes(order="C")
        for payload in (
            encoded_name,
            encoded_dtype,
            encoded_shape,
            encoded_bytes,
        ):
            digest.update(len(payload).to_bytes(8, "big"))
            digest.update(payload)
    return digest.hexdigest()


def _require_normal_or_zero_tensor(value: torch.Tensor, *, name: str) -> None:
    if value.numel() == 0:
        return
    detached = torch.abs(value.detach())
    if bool(
        torch.any((detached > 0.0) & (detached < _MIN_NORMAL_FLOAT64)).item()
    ):
        raise ConfigurationEnergyCertificateError(
            "%s contains a nonzero subnormal value" % name
        )


@dataclass(frozen=True, eq=False, init=False)
class ConfigurationEnergySnapshot:
    """Owned clone of the exact frozen graph state."""

    architecture: ConfigurationEnergyArchitecture
    state_names: Tuple[str, ...]
    state_tensors: Tuple[torch.Tensor, ...]
    state_sha256: str
    checkpoint_sha256: str

    def __init__(
        self,
        *,
        architecture: ConfigurationEnergyArchitecture,
        state_names: Tuple[str, ...],
        state_tensors: Tuple[torch.Tensor, ...],
        state_sha256: str,
        checkpoint_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _SNAPSHOT_TOKEN:
            raise TypeError("energy snapshots must be created by the module")
        object.__setattr__(self, "architecture", architecture)
        object.__setattr__(self, "state_names", state_names)
        object.__setattr__(self, "state_tensors", state_tensors)
        object.__setattr__(self, "state_sha256", state_sha256)
        object.__setattr__(self, "checkpoint_sha256", checkpoint_sha256)


def _snapshot_items(
    snapshot: ConfigurationEnergySnapshot,
) -> Tuple[Tuple[str, torch.Tensor], ...]:
    return tuple(zip(snapshot.state_names, snapshot.state_tensors))


def _checkpoint_digest(
    architecture_sha256: str, state_sha256: str
) -> str:
    return _semantic_digest(
        {
            "schema": CONFIGURATION_ENERGY_SCHEMA_VERSION,
            "architecture_sha256": architecture_sha256,
            "state_sha256": state_sha256,
        }
    )


def _validate_snapshot(snapshot: object) -> ConfigurationEnergySnapshot:
    if type(snapshot) is not ConfigurationEnergySnapshot:
        raise TypeError("snapshot must be an exact ConfigurationEnergySnapshot")
    if type(snapshot.state_names) is not tuple:
        raise TypeError("snapshot.state_names must be an exact tuple")
    if type(snapshot.state_tensors) is not tuple:
        raise TypeError("snapshot.state_tensors must be an exact tuple")
    architecture = _validate_architecture(snapshot.architecture)
    expected_shapes = _expected_state_shapes(architecture)
    expected_names = tuple(name for name, _ in expected_shapes)
    if snapshot.state_names != expected_names:
        raise ValueError("snapshot state names differ from the architecture")
    if len(snapshot.state_tensors) != len(expected_shapes):
        raise ValueError("snapshot state tensor count is inconsistent")
    occupied_state = []
    for (name, shape), tensor in zip(expected_shapes, snapshot.state_tensors):
        _require_float64_cpu_tensor(
            tensor, name="snapshot.%s" % name, shape=shape
        )
        if tensor.requires_grad:
            raise ValueError(
                "snapshot state tensor %s must not require gradients" % name
            )
        if not tensor.is_contiguous():
            raise ValueError(
                "snapshot state tensor %s must be contiguous" % name
            )
        if tensor.numel():
            start = tensor.data_ptr()
            end = start + tensor.numel() * tensor.element_size()
            for previous_start, previous_end, previous_name in occupied_state:
                if start < previous_end and previous_start < end:
                    raise ValueError(
                        "snapshot state tensors %s and %s contain unsupported "
                        "shared storage" % (previous_name, name)
                    )
            occupied_state.append((start, end, name))
        _require_normal_or_zero_tensor(tensor, name="snapshot.%s" % name)
    state_digest = _tensor_sha256_items(
        architecture.architecture_sha256, _snapshot_items(snapshot)
    )
    if state_digest != _require_sha256(
        snapshot.state_sha256, name="snapshot.state_sha256"
    ):
        raise ValueError("snapshot state digest is inconsistent")
    checkpoint_digest = _checkpoint_digest(
        architecture.architecture_sha256, state_digest
    )
    if checkpoint_digest != _require_sha256(
        snapshot.checkpoint_sha256, name="snapshot.checkpoint_sha256"
    ):
        raise ValueError("snapshot checkpoint digest is inconsistent")
    state = dict(_snapshot_items(snapshot))
    for index, scales in enumerate(architecture.coordinate_scales):
        expected = torch.tensor(scales, dtype=torch.float64)
        name = "event_encoders.%d.coordinate_scales" % index
        if not torch.equal(state[name], expected):
            raise ValueError("snapshot coordinate scales differ from architecture")
    expected_context = torch.tensor(
        architecture.context_scales, dtype=torch.float64
    )
    if not torch.equal(
        state["context_encoder.context_scales"], expected_context
    ):
        raise ValueError("snapshot context scales differ from architecture")
    return snapshot


def snapshot_configuration_energy(
    model: BoundedConfigurationEnergy,
) -> ConfigurationEnergySnapshot:
    """Clone and hash a stable instance of the exact declared graph."""

    checked = _validate_frozen_graph(model)
    architecture = checked.architecture
    live_items = tuple(checked.state_dict().items())
    before = _tensor_sha256_items(
        architecture.architecture_sha256, live_items
    )
    clones = tuple(tensor.detach().clone() for _, tensor in live_items)
    names = tuple(name for name, _ in live_items)
    _validate_frozen_graph(checked)
    after_items = tuple(checked.state_dict().items())
    after = _tensor_sha256_items(
        architecture.architecture_sha256, after_items
    )
    if before != after:
        raise ConfigurationEnergyCertificateError(
            "model state changed while the snapshot was being created"
        )
    cloned_items = tuple(zip(names, clones))
    state_digest = _tensor_sha256_items(
        architecture.architecture_sha256, cloned_items
    )
    if state_digest != before:
        raise ConfigurationEnergyCertificateError(
            "owned snapshot bytes differ from the source state"
        )
    result = ConfigurationEnergySnapshot(
        architecture=architecture,
        state_names=names,
        state_tensors=clones,
        state_sha256=state_digest,
        checkpoint_sha256=_checkpoint_digest(
            architecture.architecture_sha256, state_digest
        ),
        _construction_token=_SNAPSHOT_TOKEN,
    )
    return _validate_snapshot(result)


def outward_frobenius_norm(weight: object) -> float:
    """Return an exact-accumulation outward Frobenius upper bound."""

    matrix = _require_float64_cpu_tensor(weight, name="weight")
    if matrix.ndim != 2:
        raise ValueError("weight must be a two-dimensional tensor")
    _require_normal_or_zero_tensor(matrix, name="weight")
    exact = Fraction(0)
    for entry in matrix.detach().reshape(-1):
        value = _fraction_from_float(float(entry.item()))
        exact += value * value
    return _outward_sqrt_fraction(exact, name="Frobenius norm")


def _outward_vector_norm(value: torch.Tensor, *, name: str) -> float:
    checked = _require_float64_cpu_tensor(value, name=name)
    _require_normal_or_zero_tensor(checked, name=name)
    exact = Fraction(0)
    for entry in checked.detach().reshape(-1):
        item = _fraction_from_float(float(entry.item()))
        exact += item * item
    return _outward_sqrt_fraction(exact, name=name + " norm")


@dataclass(frozen=True)
class ConfigurationEnergyProvenance:
    """Trusted external digests bound procedurally to one certificate."""

    method_freeze_sha256: str
    training_run_sha256: str
    data_manifest_sha256: str
    selection_rule_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "method_freeze_sha256",
            "training_run_sha256",
            "data_manifest_sha256",
            "selection_rule_sha256",
        ):
            object.__setattr__(
                self,
                name,
                _require_sha256(getattr(self, name), name=name),
            )

    @property
    def sha256(self) -> str:
        return _semantic_digest(
            {
                "method_freeze_sha256": self.method_freeze_sha256,
                "training_run_sha256": self.training_run_sha256,
                "data_manifest_sha256": self.data_manifest_sha256,
                "selection_rule_sha256": self.selection_rule_sha256,
            }
        )


@dataclass(frozen=True)
class LayerNormWitness:
    state_name: str
    outward_frobenius_norm: float
    frozen_ceiling: float

    def __post_init__(self) -> None:
        if type(self.state_name) is not str or not self.state_name:
            raise TypeError("layer norm witness name must be nonempty text")
        object.__setattr__(
            self,
            "outward_frobenius_norm",
            _validated_real(
                self.outward_frobenius_norm,
                name="outward_frobenius_norm",
                nonnegative=True,
            ),
        )
        object.__setattr__(
            self,
            "frozen_ceiling",
            _validated_real(
                self.frozen_ceiling,
                name="frozen_ceiling",
                strictly_positive=True,
                maximum=MAX_CONFIGURATION_ENERGY_NORM_CEILING,
            ),
        )
        if self.outward_frobenius_norm > self.frozen_ceiling:
            raise ConfigurationEnergyCertificateError(
                "layer norm witness exceeds its frozen ceiling"
            )


def _runtime_contract_mapping() -> Dict[str, object]:
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": tuple(sys.version_info[:3]),
        "torch_version": str(torch.__version__),
        "machine": platform.machine(),
        "system": platform.system(),
        "byteorder": sys.byteorder,
        "dtype": CONFIGURATION_ENERGY_DTYPE,
        "device": CONFIGURATION_ENERGY_DEVICE,
    }


def _runtime_sha256() -> str:
    return _semantic_digest(_runtime_contract_mapping())


@dataclass(frozen=True, eq=False, init=False)
class ConfigurationEnergyCheckpointCertificate:
    """Global analytic witness for one owned represented checkpoint."""

    schema_version: str
    certificate_scope: str
    architecture_sha256: str
    process_parameter_sha256: str
    state_sha256: str
    checkpoint_sha256: str
    provenance: ConfigurationEnergyProvenance
    provenance_sha256: str
    runtime_sha256: str
    layer_norm_witnesses: Tuple[LayerNormWitness, ...]
    maximum_absolute_bias: float
    maximum_intermediate_vector_norm: float
    event_first_derivative_bounds: Tuple[float, ...]
    event_second_derivative_bounds: Tuple[float, ...]
    pooled_first_derivative_bound: float
    pooled_second_derivative_bound: float
    raw_first_derivative_bound: float
    raw_second_derivative_bound: float
    first_coordinate_partial_bound: float
    hessian_entry_bound: float
    first_derivative_bound: float
    second_derivative_bound: float
    laplacian_bound: float
    value_bound: float
    edge_difference_bound: float
    jump_rate_multiplier_bound: float
    maximum_reference_exit_rate: float
    maximum_learned_exit_rate: float
    passed: bool
    certificate_sha256: str

    def __init__(
        self,
        *,
        schema_version: str,
        certificate_scope: str,
        architecture_sha256: str,
        process_parameter_sha256: str,
        state_sha256: str,
        checkpoint_sha256: str,
        provenance: ConfigurationEnergyProvenance,
        provenance_sha256: str,
        runtime_sha256: str,
        layer_norm_witnesses: Tuple[LayerNormWitness, ...],
        maximum_absolute_bias: float,
        maximum_intermediate_vector_norm: float,
        event_first_derivative_bounds: Tuple[float, ...],
        event_second_derivative_bounds: Tuple[float, ...],
        pooled_first_derivative_bound: float,
        pooled_second_derivative_bound: float,
        raw_first_derivative_bound: float,
        raw_second_derivative_bound: float,
        first_coordinate_partial_bound: float,
        hessian_entry_bound: float,
        first_derivative_bound: float,
        second_derivative_bound: float,
        laplacian_bound: float,
        value_bound: float,
        edge_difference_bound: float,
        jump_rate_multiplier_bound: float,
        maximum_reference_exit_rate: float,
        maximum_learned_exit_rate: float,
        passed: bool,
        certificate_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("checkpoint certificates must be created by the module")
        values = locals().copy()
        values.pop("self")
        values.pop("_construction_token")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def energy_bounds(self) -> EnergyBoundConsequences:
        return EnergyBoundConsequences(
            self.value_bound,
            self.first_derivative_bound,
            self.second_derivative_bound,
        )


@dataclass(frozen=True, eq=False, init=False)
class CertifiedConfigurationEnergyCheckpoint:
    snapshot: ConfigurationEnergySnapshot
    certificate: ConfigurationEnergyCheckpointCertificate

    def __init__(
        self,
        *,
        snapshot: ConfigurationEnergySnapshot,
        certificate: ConfigurationEnergyCheckpointCertificate,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _CHECKPOINT_TOKEN:
            raise TypeError("certified checkpoints must be created by the module")
        object.__setattr__(self, "snapshot", snapshot)
        object.__setattr__(self, "certificate", certificate)


def _layer_specifications(
    architecture: ConfigurationEnergyArchitecture,
) -> Tuple[Tuple[str, float], ...]:
    result = []
    for index in range(len(architecture.type_ids)):
        result.extend(
            (
                (
                    "event_encoders.%d.linear1.weight" % index,
                    architecture.spectral_ceilings.event_input,
                ),
                (
                    "event_encoders.%d.linear2.weight" % index,
                    architecture.spectral_ceilings.event_output,
                ),
            )
        )
    result.extend(
        (
            (
                "context_encoder.linear1.weight",
                architecture.spectral_ceilings.context_input,
            ),
            (
                "context_encoder.linear2.weight",
                architecture.spectral_ceilings.context_output,
            ),
            (
                "readout.linear1.weight",
                architecture.spectral_ceilings.readout_input,
            ),
            (
                "readout.linear2.weight",
                architecture.spectral_ceilings.readout_hidden,
            ),
            (
                "readout.linear3.weight",
                architecture.spectral_ceilings.readout_output,
            ),
        )
    )
    return tuple(result)


def _maximum_intermediate_bound(
    snapshot: ConfigurationEnergySnapshot,
    norm_by_name: Mapping[str, float],
) -> float:
    architecture = snapshot.architecture
    state = dict(_snapshot_items(snapshot))
    candidates = []

    def affine_bound(weight_name: str, input_bound: float) -> Fraction:
        bias_name = weight_name[:-6] + "bias"
        bias_bound = _outward_vector_norm(
            state[bias_name], name="checkpoint bias %s" % bias_name
        )
        return (
            _fraction_from_float(norm_by_name[weight_name])
            * _fraction_from_float(input_bound)
            + _fraction_from_float(bias_bound)
        )

    event_hidden_input = _outward_sqrt_fraction(
        Fraction(architecture.event_hidden_width),
        name="event hidden activation norm",
    )
    for index, dimension in enumerate(architecture.type_dimensions):
        input_norm = _outward_sqrt_fraction(
            Fraction(dimension), name="bounded event input norm"
        )
        candidates.append(
            affine_bound(
                "event_encoders.%d.linear1.weight" % index, input_norm
            )
        )
        candidates.append(
            affine_bound(
                "event_encoders.%d.linear2.weight" % index,
                event_hidden_input,
            )
        )
    context_input = _outward_sqrt_fraction(
        Fraction(architecture.context_dimension + 1),
        name="bounded context input norm",
    )
    candidates.append(
        affine_bound("context_encoder.linear1.weight", context_input)
    )
    context_hidden = _outward_sqrt_fraction(
        Fraction(architecture.context_hidden_width),
        name="context hidden activation norm",
    )
    candidates.append(
        affine_bound("context_encoder.linear2.weight", context_hidden)
    )
    readout_input_squared = (
        Fraction(
            architecture.total_cap**2
            * architecture.event_embedding_width
        )
        + Fraction(architecture.context_embedding_width + 1)
    )
    readout_input = _outward_sqrt_fraction(
        readout_input_squared, name="readout input norm"
    )
    candidates.append(affine_bound("readout.linear1.weight", readout_input))
    readout_hidden = _outward_sqrt_fraction(
        Fraction(architecture.readout_hidden_width),
        name="readout hidden activation norm",
    )
    candidates.append(
        affine_bound("readout.linear2.weight", readout_hidden)
    )
    candidates.append(
        affine_bound("readout.linear3.weight", readout_hidden)
    )
    return _outward_float(
        max(candidates, default=Fraction(0)),
        name="maximum intermediate vector norm",
    )


def _certificate_contract_mapping(
    certificate: ConfigurationEnergyCheckpointCertificate,
) -> Dict[str, object]:
    return {
        "schema_version": certificate.schema_version,
        "certificate_scope": certificate.certificate_scope,
        "architecture_sha256": certificate.architecture_sha256,
        "process_parameter_sha256": certificate.process_parameter_sha256,
        "state_sha256": certificate.state_sha256,
        "checkpoint_sha256": certificate.checkpoint_sha256,
        "provenance_sha256": certificate.provenance_sha256,
        "runtime_sha256": certificate.runtime_sha256,
        "layer_norm_witnesses": tuple(
            (
                witness.state_name,
                witness.outward_frobenius_norm,
                witness.frozen_ceiling,
            )
            for witness in certificate.layer_norm_witnesses
        ),
        "maximum_absolute_bias": certificate.maximum_absolute_bias,
        "maximum_intermediate_vector_norm": (
            certificate.maximum_intermediate_vector_norm
        ),
        "event_first_derivative_bounds": (
            certificate.event_first_derivative_bounds
        ),
        "event_second_derivative_bounds": (
            certificate.event_second_derivative_bounds
        ),
        "pooled_first_derivative_bound": (
            certificate.pooled_first_derivative_bound
        ),
        "pooled_second_derivative_bound": (
            certificate.pooled_second_derivative_bound
        ),
        "raw_first_derivative_bound": certificate.raw_first_derivative_bound,
        "raw_second_derivative_bound": certificate.raw_second_derivative_bound,
        "first_coordinate_partial_bound": (
            certificate.first_coordinate_partial_bound
        ),
        "hessian_entry_bound": certificate.hessian_entry_bound,
        "first_derivative_bound": certificate.first_derivative_bound,
        "second_derivative_bound": certificate.second_derivative_bound,
        "laplacian_bound": certificate.laplacian_bound,
        "value_bound": certificate.value_bound,
        "edge_difference_bound": certificate.edge_difference_bound,
        "jump_rate_multiplier_bound": certificate.jump_rate_multiplier_bound,
        "maximum_reference_exit_rate": certificate.maximum_reference_exit_rate,
        "maximum_learned_exit_rate": certificate.maximum_learned_exit_rate,
        "maximum_learned_exit_rate_semantics": (
            "single-supplied-rate-binary64-operational-threshold;"
            "not-real-expression-interval;not-production-edge-aggregation"
        ),
        "activation_first_derivative_bound": 1.0,
        "activation_second_derivative_bound": 1.0,
        "coordinate_transform_first_bound": "one-over-scale",
        "coordinate_transform_second_bound": "one-over-scale-squared",
        "passed": certificate.passed,
    }


def _make_certificate(
    snapshot: ConfigurationEnergySnapshot,
    provenance: ConfigurationEnergyProvenance,
) -> ConfigurationEnergyCheckpointCertificate:
    checked = _validate_snapshot(snapshot)
    if type(provenance) is not ConfigurationEnergyProvenance:
        raise TypeError("provenance must be exact ConfigurationEnergyProvenance")
    architecture = checked.architecture
    state = dict(_snapshot_items(checked))
    witnesses = []
    norm_by_name: Dict[str, float] = {}
    for state_name, ceiling in _layer_specifications(architecture):
        norm = outward_frobenius_norm(state[state_name])
        witness = LayerNormWitness(state_name, norm, ceiling)
        witnesses.append(witness)
        norm_by_name[state_name] = norm
    bias_values = []
    for name, tensor in _snapshot_items(checked):
        if name.endswith(".bias"):
            if tensor.numel():
                bias_values.append(float(torch.max(torch.abs(tensor)).item()))
    maximum_bias = max(bias_values, default=0.0)
    if maximum_bias > architecture.bias_ceiling:
        raise ConfigurationEnergyCertificateError(
            "checkpoint bias exceeds the frozen ceiling"
        )
    event_first_exact = []
    event_second_exact = []
    for index, scales in enumerate(architecture.coordinate_scales):
        if not scales:
            event_first_exact.append(Fraction(0))
            event_second_exact.append(Fraction(0))
            continue
        input_first = max(
            Fraction(1, 1) / _fraction_from_float(scale) for scale in scales
        )
        input_second = max(
            Fraction(1, 1) / (_fraction_from_float(scale) ** 2)
            for scale in scales
        )
        first_weight = _fraction_from_float(
            norm_by_name["event_encoders.%d.linear1.weight" % index]
        )
        second_weight = _fraction_from_float(
            norm_by_name["event_encoders.%d.linear2.weight" % index]
        )
        first = second_weight * first_weight * input_first
        second = (
            first_weight**2
            * (second_weight**2 + second_weight)
            * input_first**2
            + second_weight * first_weight * input_second
        )
        event_first_exact.append(first)
        event_second_exact.append(second)
    maximum_event_first = max(event_first_exact, default=Fraction(0))
    maximum_event_second = max(event_second_exact, default=Fraction(0))
    pooled_first_squared = (
        architecture.total_cap * maximum_event_first**2
    )
    pooled_first = _outward_sqrt_fraction(
        pooled_first_squared, name="pooled first-derivative bound"
    )
    pooled_first_exact = _fraction_from_float(pooled_first)
    readout_first = _fraction_from_float(
        norm_by_name["readout.linear1.weight"]
    )
    readout_second = _fraction_from_float(
        norm_by_name["readout.linear2.weight"]
    )
    readout_output = _fraction_from_float(
        norm_by_name["readout.linear3.weight"]
    )
    raw_first_exact = (
        readout_output
        * readout_second
        * readout_first
        * pooled_first_exact
    )
    raw_second_exact = readout_output * (
        readout_first**2
        * (readout_second**2 + readout_second)
        * pooled_first_squared
        + readout_second * readout_first * maximum_event_second
    )
    second_exact = raw_second_exact + (
        raw_first_exact**2 / _fraction_from_float(architecture.value_bound)
    )
    first_exact = raw_first_exact
    if first_exact > _fraction_from_float(
        architecture.first_derivative_ceiling
    ):
        raise ConfigurationEnergyCertificateError(
            "derived first-derivative bound exceeds its frozen ceiling"
        )
    if second_exact > _fraction_from_float(
        architecture.second_derivative_ceiling
    ):
        raise ConfigurationEnergyCertificateError(
            "derived second-derivative bound exceeds its frozen ceiling"
        )
    event_first = tuple(
        _outward_float(value, name="event first-derivative bound")
        for value in event_first_exact
    )
    event_second = tuple(
        _outward_float(value, name="event second-derivative bound")
        for value in event_second_exact
    )
    pooled_second = _outward_float(
        maximum_event_second, name="pooled second-derivative bound"
    )
    raw_first = _outward_float(
        raw_first_exact, name="raw first-derivative bound"
    )
    raw_second = _outward_float(
        raw_second_exact, name="raw second-derivative bound"
    )
    first_bound = _outward_float(
        first_exact, name="configuration first-derivative bound"
    )
    second_bound = _outward_float(
        second_exact, name="configuration second-derivative bound"
    )
    maximum_coordinate_count = architecture.total_cap * max(
        architecture.type_dimensions, default=0
    )
    laplacian = _outward_float(
        maximum_coordinate_count * second_exact,
        name="configuration Laplacian bound",
    )
    bounds = EnergyBoundConsequences(
        architecture.value_bound, first_bound, second_bound
    )
    maximum_learned_exit = bounds.tilted_rate_upper_bound(
        architecture.maximum_reference_exit_rate
    )
    fields: Dict[str, object] = {
        "schema_version": CONFIGURATION_ENERGY_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_ENERGY_CERTIFICATE_SCOPE,
        "architecture_sha256": architecture.architecture_sha256,
        "process_parameter_sha256": architecture.process_parameter_sha256,
        "state_sha256": checked.state_sha256,
        "checkpoint_sha256": checked.checkpoint_sha256,
        "provenance": provenance,
        "provenance_sha256": provenance.sha256,
        "runtime_sha256": _runtime_sha256(),
        "layer_norm_witnesses": tuple(witnesses),
        "maximum_absolute_bias": maximum_bias,
        "maximum_intermediate_vector_norm": _maximum_intermediate_bound(
            checked, norm_by_name
        ),
        "event_first_derivative_bounds": event_first,
        "event_second_derivative_bounds": event_second,
        "pooled_first_derivative_bound": pooled_first,
        "pooled_second_derivative_bound": pooled_second,
        "raw_first_derivative_bound": raw_first,
        "raw_second_derivative_bound": raw_second,
        "first_coordinate_partial_bound": first_bound,
        "hessian_entry_bound": second_bound,
        "first_derivative_bound": first_bound,
        "second_derivative_bound": second_bound,
        "laplacian_bound": laplacian,
        "value_bound": architecture.value_bound,
        "edge_difference_bound": bounds.edge_difference_bound,
        "jump_rate_multiplier_bound": bounds.jump_rate_multiplier_bound,
        "maximum_reference_exit_rate": architecture.maximum_reference_exit_rate,
        "maximum_learned_exit_rate": maximum_learned_exit,
        "passed": True,
    }
    provisional = ConfigurationEnergyCheckpointCertificate(
        **fields,
        certificate_sha256="0" * 64,
        _construction_token=_CERTIFICATE_TOKEN,
    )
    digest = _semantic_digest(_certificate_contract_mapping(provisional))
    return ConfigurationEnergyCheckpointCertificate(
        **fields,
        certificate_sha256=digest,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _validate_certificate_record(
    certificate: object,
) -> ConfigurationEnergyCheckpointCertificate:
    if type(certificate) is not ConfigurationEnergyCheckpointCertificate:
        raise TypeError(
            "certificate must be an exact ConfigurationEnergyCheckpointCertificate"
        )
    if certificate.schema_version != CONFIGURATION_ENERGY_SCHEMA_VERSION:
        raise ValueError("certificate schema version is unsupported")
    if certificate.certificate_scope != CONFIGURATION_ENERGY_CERTIFICATE_SCOPE:
        raise ValueError("certificate scope is inconsistent")
    for name in (
        "architecture_sha256",
        "process_parameter_sha256",
        "state_sha256",
        "checkpoint_sha256",
        "provenance_sha256",
        "runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    if type(certificate.provenance) is not ConfigurationEnergyProvenance:
        raise TypeError("certificate provenance has the wrong type")
    if certificate.provenance.sha256 != certificate.provenance_sha256:
        raise ValueError("certificate provenance digest is inconsistent")
    if certificate.runtime_sha256 != _runtime_sha256():
        raise ValueError("certificate runtime differs from the active runtime")
    if certificate.passed is not True:
        raise ValueError("checkpoint certificate is not a PASS record")
    for field_name in (
        "layer_norm_witnesses",
        "event_first_derivative_bounds",
        "event_second_derivative_bounds",
    ):
        if type(getattr(certificate, field_name)) is not tuple:
            raise TypeError(
                "certificate.%s must be an exact tuple" % field_name
            )
    for witness in certificate.layer_norm_witnesses:
        if type(witness) is not LayerNormWitness:
            raise TypeError("certificate layer witness has the wrong type")
        LayerNormWitness(
            witness.state_name,
            witness.outward_frobenius_norm,
            witness.frozen_ceiling,
        )
    numerical = (
        certificate.maximum_absolute_bias,
        certificate.maximum_intermediate_vector_norm,
        *certificate.event_first_derivative_bounds,
        *certificate.event_second_derivative_bounds,
        certificate.pooled_first_derivative_bound,
        certificate.pooled_second_derivative_bound,
        certificate.raw_first_derivative_bound,
        certificate.raw_second_derivative_bound,
        certificate.first_coordinate_partial_bound,
        certificate.hessian_entry_bound,
        certificate.first_derivative_bound,
        certificate.second_derivative_bound,
        certificate.laplacian_bound,
        certificate.value_bound,
        certificate.edge_difference_bound,
        certificate.jump_rate_multiplier_bound,
        certificate.maximum_reference_exit_rate,
        certificate.maximum_learned_exit_rate,
    )
    for index, value in enumerate(numerical):
        _validated_real(
            value,
            name="certificate numerical field %d" % index,
            nonnegative=True,
        )
    if certificate.certificate_sha256 != _semantic_digest(
        _certificate_contract_mapping(certificate)
    ):
        raise ValueError("certificate witness digest is inconsistent")
    return certificate


def _validate_checkpoint(
    checkpoint: object,
    *,
    expected_provenance: Optional[ConfigurationEnergyProvenance] = None,
) -> CertifiedConfigurationEnergyCheckpoint:
    if type(checkpoint) is not CertifiedConfigurationEnergyCheckpoint:
        raise TypeError(
            "checkpoint must be an exact CertifiedConfigurationEnergyCheckpoint"
        )
    snapshot = _validate_snapshot(checkpoint.snapshot)
    certificate = _validate_certificate_record(checkpoint.certificate)
    if (
        certificate.architecture_sha256
        != snapshot.architecture.architecture_sha256
        or certificate.process_parameter_sha256
        != snapshot.architecture.process_parameter_sha256
        or certificate.state_sha256 != snapshot.state_sha256
        or certificate.checkpoint_sha256 != snapshot.checkpoint_sha256
    ):
        raise ValueError("checkpoint certificate and snapshot differ")
    if expected_provenance is not None:
        if type(expected_provenance) is not ConfigurationEnergyProvenance:
            raise TypeError(
                "expected_provenance must be exact ConfigurationEnergyProvenance"
            )
        if certificate.provenance_sha256 != expected_provenance.sha256:
            raise ValueError("checkpoint provenance differs from the trusted record")
    expected = _make_certificate(snapshot, certificate.provenance)
    if expected.certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("checkpoint analytic certificate is inconsistent")
    return checkpoint


def certify_configuration_energy(
    model: BoundedConfigurationEnergy,
    *,
    provenance: ConfigurationEnergyProvenance,
) -> CertifiedConfigurationEnergyCheckpoint:
    """Mint a global analytic certificate for an owned stable snapshot."""

    if type(provenance) is not ConfigurationEnergyProvenance:
        raise TypeError("provenance must be exact ConfigurationEnergyProvenance")
    snapshot = snapshot_configuration_energy(model)
    certificate = _make_certificate(snapshot, provenance)
    final_live = snapshot_configuration_energy(model)
    if final_live.checkpoint_sha256 != snapshot.checkpoint_sha256:
        raise ConfigurationEnergyCertificateError(
            "model state changed while the certificate was being created"
        )
    result = CertifiedConfigurationEnergyCheckpoint(
        snapshot=snapshot,
        certificate=certificate,
        _construction_token=_CHECKPOINT_TOKEN,
    )
    return _validate_checkpoint(result, expected_provenance=provenance)


def require_matching_configuration_energy_certificate(
    model: BoundedConfigurationEnergy,
    checkpoint: CertifiedConfigurationEnergyCheckpoint,
    *,
    expected_provenance: ConfigurationEnergyProvenance,
) -> ConfigurationEnergyCheckpointCertificate:
    """Refuse unless live graph, state, certificate, and trusted digests match."""

    checked = _validate_checkpoint(
        checkpoint, expected_provenance=expected_provenance
    )
    live = snapshot_configuration_energy(model)
    if live.checkpoint_sha256 != checked.snapshot.checkpoint_sha256:
        raise ConfigurationEnergyCertificateError(
            "live model does not match the certified checkpoint"
        )
    return checked.certificate


def materialize_configuration_energy_checkpoint(
    checkpoint: CertifiedConfigurationEnergyCheckpoint,
    *,
    expected_provenance: ConfigurationEnergyProvenance,
) -> BoundedConfigurationEnergy:
    """Create an independent in-memory model from a validated owned snapshot."""

    checked = _validate_checkpoint(
        checkpoint, expected_provenance=expected_provenance
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(0)
    model = BoundedConfigurationEnergy(
        checked.snapshot.architecture, generator=generator
    )
    state = {
        name: tensor.detach().clone()
        for name, tensor in _snapshot_items(checked.snapshot)
    }
    model.load_state_dict(state, strict=True)
    _validate_frozen_graph(model)
    live = snapshot_configuration_energy(model)
    if live.checkpoint_sha256 != checked.snapshot.checkpoint_sha256:
        raise ConfigurationEnergyCertificateError(
            "materialized model differs from the certified snapshot"
        )
    return model


def _validate_shared_edge_batches(
    architecture: ConfigurationEnergyArchitecture,
    source: object,
    destination: object,
) -> Tuple[TypedConfigurationBatch, TypedConfigurationBatch]:
    checked_source = _validate_batch(architecture, source)
    checked_destination = _validate_batch(architecture, destination)
    if checked_source.batch_size != checked_destination.batch_size:
        raise ValueError("source and destination batch sizes differ")
    if not torch.equal(
        checked_source.forward_time, checked_destination.forward_time
    ):
        raise ValueError("source and destination direct times differ")
    if not torch.equal(checked_source.context, checked_destination.context):
        raise ValueError("source and destination contexts differ")
    return checked_source, checked_destination


def _validate_gauge(
    gauge: object,
    *,
    batch_size: int,
    name: str = "shared_gauge",
) -> torch.Tensor:
    return _require_float64_cpu_tensor(
        gauge, name=name, shape=(batch_size,)
    )


def _autograd_leaf_tensors(value: torch.Tensor) -> Tuple[torch.Tensor, ...]:
    """Return the differentiable leaves feeding one tensor's live graph."""

    if not value.requires_grad:
        return ()
    if value.is_leaf:
        return (value,)
    if value.grad_fn is None:  # pragma: no cover - PyTorch invariant
        raise RuntimeError("differentiable nonleaf tensor has no autograd graph")
    leaves = []
    seen_leaves = set()
    pending = [value.grad_fn]
    seen_functions = set()
    retained_functions = []
    traversed_edges = 0
    while pending:
        function = pending.pop()
        function_id = id(function)
        if function_id in seen_functions:
            continue
        if len(seen_functions) >= MAX_CONFIGURATION_ENERGY_AUTOGRAD_NODES:
            raise ConfigurationEnergyResourceError(
                "input autograd graph exceeds the node limit"
            )
        seen_functions.add(function_id)
        retained_functions.append(function)
        variable = getattr(function, "variable", None)
        if (
            isinstance(variable, torch.Tensor)
            and variable.requires_grad
            and variable.is_leaf
            and id(variable) not in seen_leaves
        ):
            leaves.append(variable)
            seen_leaves.add(id(variable))
        for next_function, _ in function.next_functions:
            if next_function is not None:
                traversed_edges += 1
                if traversed_edges > MAX_CONFIGURATION_ENERGY_AUTOGRAD_NODES:
                    raise ConfigurationEnergyResourceError(
                        "input autograd graph exceeds the edge limit"
                    )
                pending.append(next_function)
    if not leaves:
        raise RuntimeError(
            "input autograd graph has no identifiable differentiable leaf"
        )
    return tuple(leaves)


def _require_batch_inputs_independent_of_model(
    model: BoundedConfigurationEnergy,
    batches: Tuple[TypedConfigurationBatch, ...],
) -> None:
    parameter_ids = {id(parameter) for parameter in model.parameters()}
    state_intervals = []
    for state_name, state_tensor in model.state_dict().items():
        if state_tensor.numel():
            state_start = state_tensor.data_ptr()
            state_end = (
                state_start
                + state_tensor.numel() * state_tensor.element_size()
            )
            state_intervals.append((state_start, state_end, state_name))
    for batch in batches:
        leaf_owners: Dict[int, str] = {}
        named_inputs = (
            ("forward_time", batch.forward_time),
            ("context", batch.context),
            *(
                ("coordinates[%d]" % index, coordinates)
                for index, coordinates in enumerate(batch.coordinates)
            ),
        )
        for name, value in named_inputs:
            if value.numel():
                start = value.data_ptr()
                end = start + value.numel() * value.element_size()
                for state_start, state_end, state_name in state_intervals:
                    if start < state_end and state_start < end:
                        raise ValueError(
                            "batch input %s must not overlap energy state %s"
                            % (name, state_name)
                        )
            for leaf in _autograd_leaf_tensors(value):
                previous_name = leaf_owners.get(id(leaf))
                if previous_name is not None and previous_name != name:
                    raise ValueError(
                        "batch logical float inputs %s and %s must have "
                        "disjoint autograd ancestry" % (previous_name, name)
                    )
                leaf_owners[id(leaf)] = name
                if id(leaf) in parameter_ids:
                    raise ValueError(
                        "batch input %s must be independent of energy "
                        "parameters" % name
                    )
                if type(leaf) is not torch.Tensor:
                    raise ValueError(
                        "batch input %s must have exact tensor autograd leaves"
                        % name
                    )
                if (
                    leaf.layout != torch.strided
                    or leaf.device.type != "cpu"
                    or not leaf.is_contiguous()
                ):
                    raise ValueError(
                        "batch input %s must have contiguous CPU autograd leaves"
                        % name
                    )
                _require_exact_tensor_hook_registries(
                    leaf, name="batch input %s autograd leaf" % name
                )
                if vars(leaf):
                    raise ValueError(
                        "batch input %s autograd leaf carries unsupported "
                        "instance attributes" % name
                    )
                if leaf.numel():
                    leaf_start = leaf.data_ptr()
                    leaf_end = (
                        leaf_start + leaf.numel() * leaf.element_size()
                    )
                    for state_start, state_end, state_name in state_intervals:
                        if leaf_start < state_end and state_start < leaf_end:
                            raise ValueError(
                                "batch input %s autograd leaf must not overlap "
                                "energy state %s" % (name, state_name)
                            )


_FROZEN_CONFIGURATION_ENERGY_GLOBAL_CALLABLES = (
    *_FROZEN_CONFIGURATION_ENERGY_GLOBAL_CALLABLES,
    (
        "_autograd_leaf_tensors",
        *_frozen_python_callable(_autograd_leaf_tensors),
    ),
    (
        "_require_batch_inputs_independent_of_model",
        *_frozen_python_callable(_require_batch_inputs_independent_of_model),
    ),
)


def _require_state_independent_gauge(
    gauge: torch.Tensor,
    model: BoundedConfigurationEnergy,
    batches: Tuple[TypedConfigurationBatch, ...],
) -> None:
    if not gauge.requires_grad:
        return
    forbidden_leaf_ids = {
        id(parameter)
        for parameter in model.parameters()
        if parameter.requires_grad
    }
    for batch in batches:
        for coordinates in batch.coordinates:
            for leaf in _autograd_leaf_tensors(coordinates):
                forbidden_leaf_ids.add(id(leaf))
    gauge_leaf_ids = {
        id(leaf) for leaf in _autograd_leaf_tensors(gauge)
    }
    if forbidden_leaf_ids & gauge_leaf_ids:
        raise ValueError(
            "shared_gauge must be independent of state coordinates and energy "
            "parameters"
        )


def gauged_configuration_energy(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
    *,
    shared_gauge: object,
) -> torch.Tensor:
    """Materialize an output-level gauge for diagnostics, never certification."""

    checked_model = _validate_frozen_graph(model)
    checked_batch = _validate_batch(checked_model.architecture, batch)
    gauge = _validate_gauge(
        shared_gauge, batch_size=checked_batch.batch_size
    )
    _require_state_independent_gauge(
        gauge, checked_model, (checked_batch,)
    )
    result = checked_model.forward(checked_batch) + gauge
    if bool(torch.any(~torch.isfinite(result)).detach().item()):
        raise ArithmeticError("gauged absolute energy is not representable")
    return result


def configuration_energy_edge_difference(
    model: BoundedConfigurationEnergy,
    source: TypedConfigurationBatch,
    destination: TypedConfigurationBatch,
    *,
    shared_gauge: Optional[object] = None,
) -> torch.Tensor:
    """Return a canonical edge difference, cancelling any gauge symbolically."""

    checked_model = _validate_frozen_graph(model)
    checked_source, checked_destination = _validate_shared_edge_batches(
        checked_model.architecture, source, destination
    )
    difference = checked_model.forward(
        checked_destination
    ) - checked_model.forward(checked_source)
    if shared_gauge is not None:
        gauge = _validate_gauge(
            shared_gauge, batch_size=checked_source.batch_size
        )
        _require_state_independent_gauge(
            gauge,
            checked_model,
            (checked_source, checked_destination),
        )
        difference = difference + gauge * 0.0
    if bool(torch.any(~torch.isfinite(difference)).detach().item()):
        raise ArithmeticError("configuration-energy edge difference is non-finite")
    return difference


@dataclass(frozen=True, eq=False, init=False)
class ConfigurationEnergyDerivatives:
    energy: torch.Tensor
    coordinate_gradients: Tuple[torch.Tensor, ...]
    laplacian: Optional[torch.Tensor]
    laplacian_method: str

    def __init__(
        self,
        *,
        energy: torch.Tensor,
        coordinate_gradients: Tuple[torch.Tensor, ...],
        laplacian: Optional[torch.Tensor],
        laplacian_method: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _DERIVATIVE_TOKEN:
            raise TypeError("energy derivative records must be created by the module")
        object.__setattr__(self, "energy", energy)
        object.__setattr__(self, "coordinate_gradients", coordinate_gradients)
        object.__setattr__(self, "laplacian", laplacian)
        object.__setattr__(self, "laplacian_method", laplacian_method)


def _first_coordinate_derivatives(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
    *,
    create_graph: bool,
) -> Tuple[torch.Tensor, Tuple[torch.Tensor, ...]]:
    active_positions = tuple(
        index
        for index, coordinates in enumerate(batch.coordinates)
        if coordinates.numel() > 0
    )
    for index in active_positions:
        if not batch.coordinates[index].requires_grad:
            raise ValueError(
                "nonempty continuous coordinates must require gradients"
            )
    energy = model.forward(batch)
    gradients = [torch.zeros_like(value) for value in batch.coordinates]
    if active_positions:
        active_coordinates = tuple(
            batch.coordinates[index] for index in active_positions
        )
        active_gradients = torch.autograd.grad(
            energy.sum(),
            active_coordinates,
            create_graph=create_graph,
            retain_graph=True,
            allow_unused=False,
        )
        for index, gradient in zip(active_positions, active_gradients):
            _require_float64_cpu_tensor(
                gradient, name="coordinate gradient", shape=tuple(
                    batch.coordinates[index].shape
                )
            )
            gradients[index] = gradient
    return energy, tuple(gradients)


def configuration_energy_coordinate_gradients(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
    *,
    create_graph: bool = False,
) -> ConfigurationEnergyDerivatives:
    checked_model = _validate_frozen_graph(model)
    checked_batch = _validate_batch(checked_model.architecture, batch)
    if type(create_graph) is not bool:
        raise TypeError("create_graph must be boolean")
    energy, gradients = _first_coordinate_derivatives(
        checked_model, checked_batch, create_graph=create_graph
    )
    return ConfigurationEnergyDerivatives(
        energy=energy,
        coordinate_gradients=gradients,
        laplacian=None,
        laplacian_method="not-requested",
        _construction_token=_DERIVATIVE_TOKEN,
    )


def _batch_forward_work(
    architecture: ConfigurationEnergyArchitecture,
    batch: TypedConfigurationBatch,
) -> int:
    return _forward_work_estimate(
        architecture,
        batch_size=batch.batch_size,
        occurrence_counts=batch.occurrence_counts,
    )


def configuration_energy_exact_laplacian(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
    *,
    create_graph: bool = False,
) -> ConfigurationEnergyDerivatives:
    checked_model = _validate_frozen_graph(model)
    checked_batch = _validate_batch(checked_model.architecture, batch)
    if type(create_graph) is not bool:
        raise TypeError("create_graph must be boolean")
    if (
        checked_batch.total_coordinates
        > MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_COORDINATES
    ):
        raise ConfigurationEnergyResourceError(
            "exact Laplacian exceeds the coordinate limit"
        )
    work = checked_batch.total_coordinates * max(
        1, _batch_forward_work(checked_model.architecture, checked_batch)
    )
    if work > MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_WORK:
        raise ConfigurationEnergyResourceError(
            "exact Laplacian exceeds the work limit"
        )
    energy, gradients = _first_coordinate_derivatives(
        checked_model, checked_batch, create_graph=True
    )
    laplacian = torch.zeros(
        checked_batch.batch_size, dtype=torch.float64, device="cpu"
    )
    for coordinates, owners, gradient in zip(
        checked_batch.coordinates,
        checked_batch.batch_indices,
        gradients,
    ):
        if coordinates.numel() == 0:
            continue
        diagonal = []
        flat_gradient = gradient.reshape(-1)
        flat_coordinates = coordinates.reshape(-1)
        for index in range(flat_gradient.numel()):
            entry = flat_gradient[index]
            if entry.requires_grad:
                second = torch.autograd.grad(
                    entry,
                    coordinates,
                    create_graph=create_graph,
                    retain_graph=True,
                    allow_unused=True,
                )[0]
                if second is None:
                    diagonal_entry = flat_coordinates[index] * 0.0
                else:
                    diagonal_entry = second.reshape(-1)[index]
            else:
                diagonal_entry = flat_coordinates[index] * 0.0
            diagonal.append(diagonal_entry)
        per_occurrence = torch.stack(diagonal).reshape_as(coordinates).sum(dim=1)
        laplacian = laplacian + _exact_segment_sum(
            per_occurrence.unsqueeze(-1),
            owners,
            checked_batch.batch_size,
        ).squeeze(-1)
    if create_graph:
        laplacian = laplacian + _zero_model_objective(checked_model)
    _require_float64_cpu_tensor(
        laplacian,
        name="exact configuration-energy Laplacian",
        shape=(checked_batch.batch_size,),
    )
    returned_gradients = (
        gradients if create_graph else tuple(value.detach() for value in gradients)
    )
    returned_laplacian = laplacian if create_graph else laplacian.detach()
    return ConfigurationEnergyDerivatives(
        energy=energy,
        coordinate_gradients=returned_gradients,
        laplacian=returned_laplacian,
        laplacian_method="exact-autodiff-diagonal-v1",
        _construction_token=_DERIVATIVE_TOKEN,
    )


@dataclass(frozen=True)
class HutchinsonProbeSpec:
    distribution: str
    probe_count: int
    seed: int

    def __post_init__(self) -> None:
        if self.distribution != "rademacher":
            raise ValueError("only Rademacher Hutchinson probes are supported")
        object.__setattr__(
            self,
            "probe_count",
            _validated_integer(
                self.probe_count,
                name="probe_count",
                minimum=1,
                maximum=MAX_CONFIGURATION_ENERGY_HUTCHINSON_PROBES,
            ),
        )
        object.__setattr__(
            self,
            "seed",
            _validated_integer(
                self.seed,
                name="Hutchinson seed",
                minimum=0,
                maximum=2**63 - 1,
            ),
        )


def configuration_energy_hutchinson_laplacian(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
    *,
    probe_spec: HutchinsonProbeSpec,
    create_graph: bool = False,
) -> ConfigurationEnergyDerivatives:
    checked_model = _validate_frozen_graph(model)
    checked_batch = _validate_batch(checked_model.architecture, batch)
    if type(probe_spec) is not HutchinsonProbeSpec:
        raise TypeError("probe_spec must be an exact HutchinsonProbeSpec")
    if type(create_graph) is not bool:
        raise TypeError("create_graph must be boolean")
    work = probe_spec.probe_count * max(
        1,
        checked_batch.total_coordinates
        + _batch_forward_work(checked_model.architecture, checked_batch),
    )
    if work > MAX_CONFIGURATION_ENERGY_HUTCHINSON_WORK:
        raise ConfigurationEnergyResourceError(
            "Hutchinson Laplacian exceeds the work limit"
        )
    energy, gradients = _first_coordinate_derivatives(
        checked_model, checked_batch, create_graph=True
    )
    active = tuple(
        (coordinates, owners, gradient)
        for coordinates, owners, gradient in zip(
            checked_batch.coordinates,
            checked_batch.batch_indices,
            gradients,
        )
        if coordinates.numel() > 0
    )
    if not active:
        laplacian = torch.zeros(
            checked_batch.batch_size, dtype=torch.float64, device="cpu"
        )
    else:
        generator = torch.Generator(device="cpu")
        generator.manual_seed(probe_spec.seed)
        estimates = []
        active_coordinates = tuple(item[0] for item in active)
        for _ in range(probe_spec.probe_count):
            probes = tuple(
                (
                    2
                    * torch.randint(
                        0,
                        2,
                        coordinates.shape,
                        dtype=torch.int64,
                        device="cpu",
                        generator=generator,
                    )
                    - 1
                ).to(dtype=torch.float64)
                for coordinates, _, _ in active
            )
            directional = sum(
                (gradient * probe).sum()
                for (_, _, gradient), probe in zip(active, probes)
            )
            products = torch.autograd.grad(
                directional,
                active_coordinates,
                create_graph=create_graph,
                retain_graph=True,
                allow_unused=True,
            )
            estimate = torch.zeros(
                checked_batch.batch_size, dtype=torch.float64, device="cpu"
            )
            for (coordinates, owners, _), probe, product in zip(
                active, probes, products
            ):
                if product is None:
                    row = (coordinates * 0.0).sum(dim=1)
                else:
                    row = (product * probe).sum(dim=1)
                estimate = estimate + _exact_segment_sum(
                    row.unsqueeze(-1), owners, checked_batch.batch_size
                ).squeeze(-1)
            estimates.append(estimate)
        laplacian = torch.stack(estimates).mean(dim=0)
    if create_graph:
        laplacian = laplacian + _zero_model_objective(checked_model)
    _require_float64_cpu_tensor(
        laplacian,
        name="Hutchinson configuration-energy Laplacian",
        shape=(checked_batch.batch_size,),
    )
    returned_gradients = (
        gradients if create_graph else tuple(value.detach() for value in gradients)
    )
    returned_laplacian = laplacian if create_graph else laplacian.detach()
    return ConfigurationEnergyDerivatives(
        energy=energy,
        coordinate_gradients=returned_gradients,
        laplacian=returned_laplacian,
        laplacian_method=(
            "hutchinson-rademacher-v1:%d:%d"
            % (probe_spec.probe_count, probe_spec.seed)
        ),
        _construction_token=_DERIVATIVE_TOKEN,
    )


def _zero_model_objective(
    model: BoundedConfigurationEnergy,
    *,
    gauge: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    result = torch.zeros((), dtype=torch.float64, device="cpu")
    for parameter in model.parameters():
        result = result + (parameter * 0.0).sum()
    if gauge is not None:
        result = result + (gauge * 0.0).sum()
    return result


def _validated_reference_scores(
    batch: TypedConfigurationBatch,
    reference_scores_by_type: Mapping[int, torch.Tensor],
) -> Tuple[torch.Tensor, ...]:
    if not isinstance(reference_scores_by_type, Mapping):
        raise TypeError("reference_scores_by_type must be a mapping")
    keys = _validated_type_mapping_keys(
        reference_scores_by_type, name="reference_scores_by_type"
    )
    if set(keys) != set(batch.type_ids):
        raise ValueError("reference scores must specify every architecture type")
    score_mapping = {
        event_type: reference_scores_by_type[event_type]
        for event_type in keys
    }
    result = []
    for event_type, coordinates in zip(batch.type_ids, batch.coordinates):
        score = _require_float64_cpu_tensor(
            score_mapping[event_type],
            name="reference_scores_by_type[%d]" % event_type,
            shape=tuple(coordinates.shape),
        )
        if not torch.equal(score.detach(), coordinates.detach()):
            raise ValueError(
                "standard-Gaussian reference coordinates must equal the "
                "packed transformed coordinates"
            )
        result.append(score)
    return tuple(value.detach() for value in result)


def _expected_continuous_schedule_rate(
    architecture: ConfigurationEnergyArchitecture,
    forward_time: torch.Tensor,
) -> torch.Tensor:
    process_key = architecture.process_parameter_key
    try:
        schedule_key = process_key[2]
        if (
            type(schedule_key) is not tuple
            or schedule_key[0] != "piecewise-constant-hybrid-schedule-v1"
        ):
            raise ValueError
        grid = tuple(float(value) for value in schedule_key[1])
        rates = tuple(float(value) for value in schedule_key[2])
    except (IndexError, TypeError, ValueError) as error:
        raise ValueError(
            "architecture process key has an unsupported schedule contract"
        ) from error
    if len(grid) != len(rates) + 1:
        raise ValueError("architecture schedule contract is inconsistent")
    expected = []
    for value in forward_time.detach().tolist():
        position = bisect_left(grid, float(value)) - 1
        expected.append(rates[max(0, position)])
    return torch.tensor(expected, dtype=torch.float64, device="cpu")


def configuration_energy_continuous_loss(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
    *,
    continuous_schedule_rate: object,
    reference_scores_by_type: Mapping[int, torch.Tensor],
    probe_spec: Optional[HutchinsonProbeSpec] = None,
    shared_gauge: Optional[object] = None,
) -> torch.Tensor:
    """Evaluate the relative continuous score-matching integrand."""

    checked_model = _validate_frozen_graph(model)
    checked_batch = _validate_batch(checked_model.architecture, batch)
    if bool(
        torch.any(
            checked_batch.forward_time <= checked_model.architecture.clean_hold
        ).item()
    ):
        raise ValueError(
            "continuous training times must lie strictly after the clean hold"
        )
    schedule_rate = _require_float64_cpu_tensor(
        continuous_schedule_rate,
        name="continuous_schedule_rate",
        shape=(checked_batch.batch_size,),
    )
    _require_normal_or_zero_tensor(
        schedule_rate, name="continuous_schedule_rate"
    )
    expected_schedule_rate = _expected_continuous_schedule_rate(
        checked_model.architecture, checked_batch.forward_time
    )
    if not torch.equal(schedule_rate, expected_schedule_rate):
        raise ValueError(
            "continuous_schedule_rate differs from the bound process schedule"
        )
    if bool(torch.any(schedule_rate <= 0.0).item()):
        raise ValueError("continuous schedule rates must be strictly positive")
    schedule_rate = schedule_rate.detach()
    scores = _validated_reference_scores(
        checked_batch, reference_scores_by_type
    )
    if probe_spec is None:
        derivatives = configuration_energy_exact_laplacian(
            checked_model, checked_batch, create_graph=True
        )
    else:
        if type(probe_spec) is not HutchinsonProbeSpec:
            raise TypeError("probe_spec must be exact HutchinsonProbeSpec")
        derivatives = configuration_energy_hutchinson_laplacian(
            checked_model,
            checked_batch,
            probe_spec=probe_spec,
            create_graph=True,
        )
    if derivatives.laplacian is None:  # pragma: no cover - internal invariant
        raise RuntimeError("continuous loss requires a Laplacian")
    state_term = torch.zeros(
        checked_batch.batch_size, dtype=torch.float64, device="cpu"
    )
    for gradient, score, owners in zip(
        derivatives.coordinate_gradients,
        scores,
        checked_batch.batch_indices,
    ):
        if gradient.numel() == 0:
            continue
        per_occurrence = 0.5 * (gradient * gradient).sum(dim=1) - (
            score * gradient
        ).sum(dim=1)
        state_term = state_term + _exact_segment_sum(
            per_occurrence.unsqueeze(-1), owners, checked_batch.batch_size
        ).squeeze(-1)
    per_sample = schedule_rate * (state_term + derivatives.laplacian)
    gauge = None
    if shared_gauge is not None:
        gauge = _validate_gauge(
            shared_gauge, batch_size=checked_batch.batch_size
        )
        _require_state_independent_gauge(
            gauge, checked_model, (checked_batch,)
        )
        per_sample = per_sample + gauge * 0.0
    if bool(torch.any(~torch.isfinite(per_sample)).detach().item()):
        raise ArithmeticError("continuous energy loss is non-finite")
    result = per_sample.mean() + _zero_model_objective(
        checked_model, gauge=gauge
    )
    if not bool(torch.isfinite(result).detach().item()):
        raise ArithmeticError("continuous energy objective is non-finite")
    return result


def _select_batch_rows(
    architecture: ConfigurationEnergyArchitecture,
    batch: TypedConfigurationBatch,
    selected: torch.Tensor,
) -> Tuple[TypedConfigurationBatch, Tuple[torch.Tensor, ...]]:
    checked = _validate_batch(architecture, batch)
    if not isinstance(selected, torch.Tensor) or selected.dtype != torch.bool:
        raise TypeError("selected rows must be a boolean tensor")
    if selected.device.type != "cpu" or tuple(selected.shape) != (
        checked.batch_size,
    ):
        raise ValueError("selected rows have the wrong shape or device")
    indices = torch.nonzero(selected, as_tuple=False).squeeze(-1)
    if indices.numel() == 0:
        raise ValueError("at least one batch row must be selected")
    remap = torch.full(
        (checked.batch_size,), -1, dtype=torch.int64, device="cpu"
    )
    remap[indices] = torch.arange(indices.numel(), dtype=torch.int64)
    coordinates_by_type: Dict[int, torch.Tensor] = {}
    owners_by_type: Dict[int, torch.Tensor] = {}
    masks = []
    for event_type, coordinates, owners in zip(
        checked.type_ids, checked.coordinates, checked.batch_indices
    ):
        remapped = remap.index_select(0, owners)
        mask = remapped >= 0
        masks.append(mask)
        coordinates_by_type[event_type] = coordinates[mask]
        owners_by_type[event_type] = remapped[mask]
    result = pack_typed_configuration_batch(
        architecture,
        checked.forward_time.index_select(0, indices),
        checked.context.index_select(0, indices),
        coordinates_by_type,
        owners_by_type,
    )
    return result, tuple(masks)


def configuration_energy_jump_flux_loss(
    model: BoundedConfigurationEnergy,
    source: TypedConfigurationBatch,
    destination: TypedConfigurationBatch,
    *,
    unnormalized_reference_weights: object,
    shared_gauge: Optional[object] = None,
) -> torch.Tensor:
    """Evaluate the positive-linear-sign jump-flux objective without clipping."""

    checked_model = _validate_frozen_graph(model)
    checked_source, checked_destination = _validate_shared_edge_batches(
        checked_model.architecture, source, destination
    )
    weights = _require_float64_cpu_tensor(
        unnormalized_reference_weights,
        name="unnormalized_reference_weights",
        shape=(checked_source.batch_size,),
    )
    _require_normal_or_zero_tensor(
        weights, name="unnormalized_reference_weights"
    )
    if bool(torch.any(weights < 0.0).item()):
        raise ValueError("unnormalized reference weights must be nonnegative")
    weights = weights.detach()
    hold_rows = (
        checked_source.forward_time <= checked_model.architecture.clean_hold
    )
    if bool(torch.any(weights[hold_rows] != 0.0).item()):
        raise ValueError("clean-hold jump weights must be exactly zero")
    active = weights > 0.0
    gauge = None
    if shared_gauge is not None:
        gauge = _validate_gauge(
            shared_gauge, batch_size=checked_source.batch_size
        )
        _require_state_independent_gauge(
            gauge,
            checked_model,
            (checked_source, checked_destination),
        )
    if not bool(torch.any(active).item()):
        return _zero_model_objective(checked_model, gauge=gauge)
    active_source, _ = _select_batch_rows(
        checked_model.architecture, checked_source, active
    )
    active_destination, _ = _select_batch_rows(
        checked_model.architecture, checked_destination, active
    )
    active_gauge = None if gauge is None else gauge[active]
    difference = configuration_energy_edge_difference(
        checked_model,
        active_source,
        active_destination,
        shared_gauge=active_gauge,
    )
    contribution = weights[active] * (torch.exp(difference) + difference)
    if bool(torch.any(~torch.isfinite(contribution)).detach().item()):
        raise ArithmeticError("jump-flux contribution is non-finite")
    result = contribution.sum() / float(
        checked_source.batch_size
    ) + _zero_model_objective(checked_model, gauge=gauge)
    if not bool(torch.isfinite(result).detach().item()):
        raise ArithmeticError("jump-flux objective is non-finite")
    return result


def combine_configuration_energy_losses(
    continuous_loss: object,
    jump_loss: object,
    *,
    jump_weight: object,
) -> torch.Tensor:
    continuous = _require_float64_cpu_tensor(
        continuous_loss, name="continuous_loss", shape=()
    )
    jump = _require_float64_cpu_tensor(jump_loss, name="jump_loss", shape=())
    weight = _validated_real(
        jump_weight, name="jump_weight", strictly_positive=True
    )
    result = continuous + weight * jump
    if not bool(torch.isfinite(result).detach().item()):
        raise ArithmeticError("combined configuration-energy loss is non-finite")
    return result


def certified_tilted_jump_rates(
    model: BoundedConfigurationEnergy,
    checkpoint: CertifiedConfigurationEnergyCheckpoint,
    source: TypedConfigurationBatch,
    destination: TypedConfigurationBatch,
    *,
    reference_rates: object,
    expected_provenance: ConfigurationEnergyProvenance,
    shared_gauge: Optional[object] = None,
) -> torch.Tensor:
    """Tilt exact reference rates without querying structural-zero rows."""

    checked_model = _validate_frozen_graph(model)
    checked_source, checked_destination = _validate_shared_edge_batches(
        checked_model.architecture, source, destination
    )
    rates = _require_float64_cpu_tensor(
        reference_rates,
        name="reference_rates",
        shape=(checked_source.batch_size,),
    )
    _require_normal_or_zero_tensor(rates, name="reference_rates")
    if bool(torch.any(rates < 0.0).item()):
        raise ValueError("reference rates must be nonnegative")
    rates = rates.detach()
    certificate = require_matching_configuration_energy_certificate(
        checked_model,
        checkpoint,
        expected_provenance=expected_provenance,
    )
    if checked_model.architecture.architecture_sha256 != (
        checkpoint.snapshot.architecture.architecture_sha256
    ):
        raise ValueError("rate batch and certified architecture differ")
    hold_rows = checked_source.forward_time <= checked_model.architecture.clean_hold
    if bool(torch.any(rates[hold_rows] != 0.0).item()):
        raise ValueError("clean-hold reference rates must be exactly zero")
    if bool(torch.any(rates > certificate.maximum_reference_exit_rate).item()):
        raise ValueError("reference rate exceeds the certified exit envelope")
    gauge = None
    if shared_gauge is not None:
        gauge = _validate_gauge(
            shared_gauge, batch_size=checked_source.batch_size
        )
        _require_state_independent_gauge(
            gauge,
            checked_model,
            (checked_source, checked_destination),
        )
    active = rates > 0.0
    if not bool(torch.any(active).item()):
        return torch.zeros_like(rates) + _zero_model_objective(
            checked_model, gauge=gauge
        )
    active_source, _ = _select_batch_rows(
        checked_model.architecture, checked_source, active
    )
    active_destination, _ = _select_batch_rows(
        checked_model.architecture, checked_destination, active
    )
    active_gauge = None if gauge is None else gauge[active]
    difference = configuration_energy_edge_difference(
        checked_model,
        active_source,
        active_destination,
        shared_gauge=active_gauge,
    )
    operational_edge_bound = math.nextafter(
        certificate.edge_difference_bound, math.inf
    )
    if bool(torch.any(torch.abs(difference) > operational_edge_bound).item()):
        raise ConfigurationEnergyCertificateError(
            "evaluated edge exceeds the certified value envelope"
        )
    multiplier = torch.exp(difference)
    if bool(torch.any(~torch.isfinite(multiplier)).detach().item()):
        raise ArithmeticError("learned jump multiplier is non-finite")
    if bool(
        torch.any(
            multiplier
            > math.nextafter(
                certificate.jump_rate_multiplier_bound, math.inf
            )
        ).item()
    ):
        raise ConfigurationEnergyCertificateError(
            "learned jump multiplier exceeds its certified envelope"
        )
    active_rates = rates[active] * multiplier
    if bool(torch.any(~torch.isfinite(active_rates)).detach().item()):
        raise ArithmeticError("tilted jump rate is non-finite")
    if bool(torch.any(active_rates < _MIN_NORMAL_FLOAT64).item()):
        raise ArithmeticError("positive tilted jump rate is subnormal or zero")
    bounds = certificate.energy_bounds
    for base_rate, learned_rate in zip(
        rates[active].detach().tolist(), active_rates.detach().tolist()
    ):
        envelope = bounds.tilted_rate_upper_bound(float(base_rate))
        if float(learned_rate) > math.nextafter(envelope, math.inf):
            raise ConfigurationEnergyCertificateError(
                "tilted jump rate exceeds its per-edge envelope"
            )
    if bool(
        torch.any(
            active_rates
            > math.nextafter(certificate.maximum_learned_exit_rate, math.inf)
        ).item()
    ):
        raise ConfigurationEnergyCertificateError(
            "tilted jump rate exceeds the maximum learned exit envelope"
        )
    result = torch.zeros_like(rates).index_copy(
        0, torch.nonzero(active, as_tuple=False).squeeze(-1), active_rates
    )
    if bool(torch.any(~torch.isfinite(result)).detach().item()):
        raise ArithmeticError("tilted jump-rate vector is non-finite")
    return result


__all__ = [
    "CONFIGURATION_ENERGY_CERTIFICATE_SCOPE",
    "CONFIGURATION_ENERGY_DEVICE",
    "CONFIGURATION_ENERGY_DTYPE",
    "CONFIGURATION_ENERGY_SCHEMA_VERSION",
    "MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES",
    "MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES",
    "MAX_CONFIGURATION_ENERGY_BATCH_SIZE",
    "MAX_CONFIGURATION_ENERGY_CAP",
    "MAX_CONFIGURATION_ENERGY_CONTEXT_DIMENSION",
    "MAX_CONFIGURATION_ENERGY_COORDINATE_DIMENSION",
    "MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_COORDINATES",
    "MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_WORK",
    "MAX_CONFIGURATION_ENERGY_FORWARD_WORK",
    "MAX_CONFIGURATION_ENERGY_HUTCHINSON_PROBES",
    "MAX_CONFIGURATION_ENERGY_HUTCHINSON_WORK",
    "MAX_CONFIGURATION_ENERGY_PARAMETERS",
    "MAX_CONFIGURATION_ENERGY_POOL_WORK",
    "MAX_CONFIGURATION_ENERGY_TYPES",
    "MAX_CONFIGURATION_ENERGY_WIDTH",
    "MAX_CONFIGURATION_ENERGY_AUTOGRAD_NODES",
    "MAX_CONFIGURATION_ENERGY_SCALE",
    "MIN_CONFIGURATION_ENERGY_SCALE",
    "BoundedConfigurationEnergy",
    "CertifiedConfigurationEnergyCheckpoint",
    "ConfigurationEnergyArchitecture",
    "ConfigurationEnergyCertificateError",
    "ConfigurationEnergyCheckpointCertificate",
    "ConfigurationEnergyDerivatives",
    "ConfigurationEnergyProvenance",
    "ConfigurationEnergyResourceError",
    "ConfigurationEnergySnapshot",
    "HutchinsonProbeSpec",
    "LayerNormWitness",
    "SpectralNormCeilings",
    "TypedConfigurationBatch",
    "certified_tilted_jump_rates",
    "certify_configuration_energy",
    "combine_configuration_energy_losses",
    "configuration_energy_continuous_loss",
    "configuration_energy_coordinate_gradients",
    "configuration_energy_edge_difference",
    "configuration_energy_exact_laplacian",
    "configuration_energy_hutchinson_laplacian",
    "configuration_energy_jump_flux_loss",
    "gauged_configuration_energy",
    "materialize_configuration_energy_checkpoint",
    "outward_frobenius_norm",
    "pack_typed_configuration_batch",
    "require_matching_configuration_energy_certificate",
    "snapshot_configuration_energy",
]
