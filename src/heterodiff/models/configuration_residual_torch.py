"""Boundary-gated conditional residual on typed hybrid configurations.

This optional-PyTorch module gives the domain-neutral residual term

``R(S-s, y, c) = a_R(S-s) * C_B(F(s, y, c))``

where ``s`` is the process-owned direct time carried by an existing
``TypedConfigurationBatch`` and

``a_R(S-s) = ((max(s - clean_hold, 0)) / (S - clean_hold)) ** 3``.

The typed DeepSets backbone and its analytic physical-coordinate certificate
are reused from :mod:`heterodiff.models.configuration_energy_torch`.  The
backbone already applies ``C_B(v) = B * tanh(v / B)``; this module never
applies a second saturation.  A separate contract, provenance record, and
checkpoint prevent an ordinary base-energy checkpoint from being silently
relabelled as a residual checkpoint.

The certificate covers values, same-condition state-pair differences, and
first/second derivatives with respect to the full flattened *physical latent
coordinates* within each fixed configuration stratum.  It does not certify
time, observation, task, or context derivatives; smoothness across discrete
edits; a small binary64 forward error; or sampler admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from numbers import Real
from typing import Dict, Mapping, Optional, Tuple

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.configuration_residual_torch requires the "
            "optional PyTorch dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.artifacts.manifest import canonical_config_digest
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy,
    CertifiedConfigurationEnergyCheckpoint,
    ConfigurationEnergyArchitecture,
    ConfigurationEnergyCheckpointCertificate,
    ConfigurationEnergyDerivatives,
    ConfigurationEnergyProvenance,
    ConfigurationEnergyResourceError,
    MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_COORDINATES,
    TypedConfigurationBatch,
    certify_configuration_energy,
    configuration_energy_coordinate_gradients,
    configuration_energy_edge_difference,
    configuration_energy_exact_laplacian,
    materialize_configuration_energy_checkpoint,
    pack_typed_configuration_batch,
    require_matching_configuration_energy_certificate,
    _require_batch_inputs_independent_of_model,
)


CONFIGURATION_RESIDUAL_SCHEMA_VERSION = "configuration-residual-torch-v1"
CONFIGURATION_RESIDUAL_GATE_POLICY = (
    "direct-time-positive-part-cubic-v1:"
    "((max(s-clean_hold,0))/(horizon-clean_hold))**3"
)
CONFIGURATION_RESIDUAL_CERTIFICATE_SCOPE = (
    "real-arithmetic-global-physical-coordinate-bounds;"
    "mathematical-gate-derivatives-use-exact-represented-endpoint-difference;"
    "binary64-operational-gate-separately-guarded;"
    "fixed-finite-dimensional-declared-conditioner;"
    "trusted-unmodified-python-torch-runtime;"
    "not-time-context-observation-derivative-certificate;"
    "not-forward-error-enclosure;not-sampler-admission"
)
CONFIGURATION_RESIDUAL_CONDITIONER_SCOPE = (
    "fixed-finite-dimensional-context-vector;observation-task-adapter-"
    "externally-frozen-procedural-digest;context-tensor-origin-not-runtime-"
    "authenticated;variable-cardinality-native-observation-encoder-not-certified"
)

_CONTRACT_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_CHECKPOINT_TOKEN = object()
_DERIVATIVE_TOKEN = object()

_MIN_NORMAL_FLOAT64 = float.fromhex("0x1.0p-1022")


class ConfigurationResidualCertificateError(RuntimeError):
    """Raised when a residual checkpoint cannot carry its declared bounds."""


class ConfigurationResidualGateResolutionError(ArithmeticError):
    """Raised when an active residual gate is not normal in binary64."""


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be text" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _validated_real(
    value: object,
    *,
    name: str,
    strictly_positive: bool = False,
    nonnegative: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("%s must be a real scalar" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if strictly_positive and not result > 0.0:
        raise ValueError("%s must be strictly positive" % name)
    if nonnegative and result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    return result


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
    if type(value) is list:
        return ["list-v1", [_typed_digest_value(item) for item in value]]
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
        {"configuration_residual_typed_semantics": _typed_digest_value(value)}
    )


def _fraction(value: float) -> Fraction:
    numerator, denominator = value.as_integer_ratio()
    return Fraction(numerator, denominator)


def _outward_float(value: Fraction, *, name: str) -> float:
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    if value == 0:
        return 0.0
    try:
        result = float(value)
    except OverflowError as error:
        raise ConfigurationResidualCertificateError(
            "%s exceeds binary64 range" % name
        ) from error
    if not math.isfinite(result):
        raise ConfigurationResidualCertificateError(
            "%s has no finite binary64 upper bound" % name
        )
    if _fraction(result) < value:
        result = math.nextafter(result, math.inf)
    if not math.isfinite(result):
        raise ConfigurationResidualCertificateError(
            "%s cannot be rounded outward" % name
        )
    return result


def _architecture_boundary(
    architecture: ConfigurationEnergyArchitecture,
) -> Tuple[float, float, float]:
    if type(architecture) is not ConfigurationEnergyArchitecture:
        raise TypeError("architecture must be an exact ConfigurationEnergyArchitecture")
    horizon = _validated_real(
        architecture.schedule_horizon,
        name="architecture.schedule_horizon",
        strictly_positive=True,
    )
    clean_hold = _validated_real(
        architecture.clean_hold,
        name="architecture.clean_hold",
        nonnegative=True,
    )
    if not clean_hold < horizon:
        raise ValueError("clean hold must lie strictly inside the horizon")
    active_duration = horizon - clean_hold
    if not math.isfinite(active_duration) or not active_duration > 0.0:
        raise ConfigurationResidualCertificateError(
            "active reverse duration is not representable"
        )
    if active_duration < float.fromhex("0x1.0p-1022"):
        raise ConfigurationResidualCertificateError(
            "active reverse duration must be a normal binary64 value"
        )
    return horizon, clean_hold, active_duration


@dataclass(frozen=True, eq=False, init=False)
class ConditionalResidualContract:
    """Sealed semantic role for one reverse-time conditional residual."""

    schema_version: str
    core_architecture_sha256: str
    process_parameter_sha256: str
    context_schema_sha256: str
    observation_schema_sha256: str
    task_schema_sha256: str
    conditioning_adapter_sha256: str
    residual_role_sha256: str
    schedule_horizon: float
    clean_hold: float
    active_reverse_duration: float
    gate_policy: str
    conditioner_scope: str
    contract_sha256: str

    def __init__(
        self,
        *,
        schema_version: str,
        core_architecture_sha256: str,
        process_parameter_sha256: str,
        context_schema_sha256: str,
        observation_schema_sha256: str,
        task_schema_sha256: str,
        conditioning_adapter_sha256: str,
        residual_role_sha256: str,
        schedule_horizon: float,
        clean_hold: float,
        active_reverse_duration: float,
        gate_policy: str,
        conditioner_scope: str,
        contract_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _CONTRACT_TOKEN:
            raise TypeError("residual contracts must be created by the module")
        values = locals().copy()
        values.pop("self")
        values.pop("_construction_token")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("residual contracts are not pickle transport objects")


def _contract_mapping(contract: ConditionalResidualContract) -> Dict[str, object]:
    return {
        "schema_version": contract.schema_version,
        "core_architecture_sha256": contract.core_architecture_sha256,
        "process_parameter_sha256": contract.process_parameter_sha256,
        "context_schema_sha256": contract.context_schema_sha256,
        "observation_schema_sha256": contract.observation_schema_sha256,
        "task_schema_sha256": contract.task_schema_sha256,
        "conditioning_adapter_sha256": contract.conditioning_adapter_sha256,
        "residual_role_sha256": contract.residual_role_sha256,
        "schedule_horizon": contract.schedule_horizon,
        "clean_hold": contract.clean_hold,
        "active_reverse_duration": contract.active_reverse_duration,
        "active_reverse_duration_semantics": (
            "binary64 runtime denominator fl(horizon-clean_hold); mathematical "
            "gate derivatives use the exact rational difference of the two "
            "represented endpoints"
        ),
        "gate_policy": contract.gate_policy,
        "conditioner_scope": contract.conditioner_scope,
        "time_input_semantics": ("direct process time s; reverse time is u=S-s"),
        "coordinate_derivative_semantics": (
            "full flattened physical latent coordinates within one fixed stratum"
        ),
    }


def _validate_contract(contract: object) -> ConditionalResidualContract:
    if type(contract) is not ConditionalResidualContract:
        raise TypeError("contract must be an exact ConditionalResidualContract")
    if contract.schema_version != CONFIGURATION_RESIDUAL_SCHEMA_VERSION:
        raise ValueError("residual contract schema differs from this module")
    for name in (
        "core_architecture_sha256",
        "process_parameter_sha256",
        "context_schema_sha256",
        "observation_schema_sha256",
        "task_schema_sha256",
        "conditioning_adapter_sha256",
        "residual_role_sha256",
        "contract_sha256",
    ):
        _require_sha256(getattr(contract, name), name="contract.%s" % name)
    horizon = _validated_real(
        contract.schedule_horizon,
        name="contract.schedule_horizon",
        strictly_positive=True,
    )
    clean_hold = _validated_real(
        contract.clean_hold,
        name="contract.clean_hold",
        nonnegative=True,
    )
    active_duration = _validated_real(
        contract.active_reverse_duration,
        name="contract.active_reverse_duration",
        strictly_positive=True,
    )
    if horizon - clean_hold != active_duration:
        raise ValueError("residual active duration is inconsistent")
    if contract.gate_policy != CONFIGURATION_RESIDUAL_GATE_POLICY:
        raise ValueError("residual gate policy is inconsistent")
    if contract.conditioner_scope != CONFIGURATION_RESIDUAL_CONDITIONER_SCOPE:
        raise ValueError("residual conditioner scope is inconsistent")
    if contract.contract_sha256 != _semantic_digest(_contract_mapping(contract)):
        raise ValueError("residual contract digest is inconsistent")
    return contract


def make_conditional_residual_contract(
    architecture: ConfigurationEnergyArchitecture,
    *,
    observation_schema_sha256: object,
    task_schema_sha256: object,
    conditioning_adapter_sha256: object,
    residual_role_sha256: object,
) -> ConditionalResidualContract:
    """Bind a finite conditioner adapter and residual role to one backbone."""

    horizon, clean_hold, active_duration = _architecture_boundary(architecture)
    values = {
        "schema_version": CONFIGURATION_RESIDUAL_SCHEMA_VERSION,
        "core_architecture_sha256": _require_sha256(
            architecture.architecture_sha256,
            name="architecture.architecture_sha256",
        ),
        "process_parameter_sha256": _require_sha256(
            architecture.process_parameter_sha256,
            name="architecture.process_parameter_sha256",
        ),
        "context_schema_sha256": _require_sha256(
            architecture.context_schema_sha256,
            name="architecture.context_schema_sha256",
        ),
        "observation_schema_sha256": _require_sha256(
            observation_schema_sha256, name="observation_schema_sha256"
        ),
        "task_schema_sha256": _require_sha256(
            task_schema_sha256, name="task_schema_sha256"
        ),
        "conditioning_adapter_sha256": _require_sha256(
            conditioning_adapter_sha256, name="conditioning_adapter_sha256"
        ),
        "residual_role_sha256": _require_sha256(
            residual_role_sha256, name="residual_role_sha256"
        ),
        "schedule_horizon": horizon,
        "clean_hold": clean_hold,
        "active_reverse_duration": active_duration,
        "gate_policy": CONFIGURATION_RESIDUAL_GATE_POLICY,
        "conditioner_scope": CONFIGURATION_RESIDUAL_CONDITIONER_SCOPE,
    }
    provisional = ConditionalResidualContract(
        **values,
        contract_sha256="0" * 64,
        _construction_token=_CONTRACT_TOKEN,
    )
    result = ConditionalResidualContract(
        **values,
        contract_sha256=_semantic_digest(_contract_mapping(provisional)),
        _construction_token=_CONTRACT_TOKEN,
    )
    return _validate_contract(result)


def _require_matching_contract_architecture(
    contract: ConditionalResidualContract,
    architecture: ConfigurationEnergyArchitecture,
) -> ConditionalResidualContract:
    checked = _validate_contract(contract)
    horizon, clean_hold, active_duration = _architecture_boundary(architecture)
    if (
        checked.core_architecture_sha256 != architecture.architecture_sha256
        or checked.process_parameter_sha256 != architecture.process_parameter_sha256
        or checked.context_schema_sha256 != architecture.context_schema_sha256
        or checked.schedule_horizon != horizon
        or checked.clean_hold != clean_hold
        or checked.active_reverse_duration != active_duration
    ):
        raise ValueError("residual contract and backbone architecture differ")
    return checked


@dataclass(frozen=True)
class ConditionalResidualProvenance:
    """Procedural digests for a run trained specifically as a residual."""

    method_freeze_sha256: str
    training_run_sha256: str
    data_manifest_sha256: str
    selection_rule_sha256: str
    observation_schema_sha256: str
    task_schema_sha256: str
    conditioning_adapter_sha256: str
    residual_role_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "method_freeze_sha256",
            "training_run_sha256",
            "data_manifest_sha256",
            "selection_rule_sha256",
            "observation_schema_sha256",
            "task_schema_sha256",
            "conditioning_adapter_sha256",
            "residual_role_sha256",
        ):
            object.__setattr__(
                self,
                name,
                _require_sha256(getattr(self, name), name=name),
            )

    @property
    def core_provenance(self) -> ConfigurationEnergyProvenance:
        return ConfigurationEnergyProvenance(
            method_freeze_sha256=self.method_freeze_sha256,
            training_run_sha256=self.training_run_sha256,
            data_manifest_sha256=self.data_manifest_sha256,
            selection_rule_sha256=self.selection_rule_sha256,
        )

    @property
    def sha256(self) -> str:
        return _semantic_digest(
            {
                "method_freeze_sha256": self.method_freeze_sha256,
                "training_run_sha256": self.training_run_sha256,
                "data_manifest_sha256": self.data_manifest_sha256,
                "selection_rule_sha256": self.selection_rule_sha256,
                "observation_schema_sha256": self.observation_schema_sha256,
                "task_schema_sha256": self.task_schema_sha256,
                "conditioning_adapter_sha256": self.conditioning_adapter_sha256,
                "residual_role_sha256": self.residual_role_sha256,
            }
        )


@dataclass(frozen=True, eq=False, init=False)
class ConditionalResidualCheckpointCertificate:
    """Global physical-coordinate witness for one residual checkpoint."""

    schema_version: str
    certificate_scope: str
    contract_sha256: str
    core_architecture_sha256: str
    process_parameter_sha256: str
    context_schema_sha256: str
    observation_schema_sha256: str
    task_schema_sha256: str
    conditioning_adapter_sha256: str
    residual_role_sha256: str
    core_checkpoint_sha256: str
    core_certificate_sha256: str
    provenance: ConditionalResidualProvenance
    provenance_sha256: str
    runtime_sha256: str
    schedule_horizon: float
    clean_hold: float
    active_reverse_duration: float
    gate_policy: str
    gate_value_bound: float
    mathematical_gate_first_reverse_derivative_bound: float
    mathematical_gate_second_reverse_derivative_bound: float
    value_bound: float
    edge_difference_bound: float
    log_jump_multiplier_bound: float
    jump_rate_multiplier_bound: float
    first_coordinate_derivative_bound: float
    second_coordinate_derivative_bound: float
    laplacian_bound: float
    maximum_reference_exit_rate: float
    maximum_residual_tilted_exit_rate: float
    physical_coordinate_derivatives_certified: bool
    time_derivatives_certified: bool
    conditioner_derivatives_certified: bool
    conditioning_adapter_operationally_authenticated: bool
    small_forward_error_certified: bool
    operational_sampler_admissible: bool
    passed: bool
    certificate_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("residual certificates must be created by the module")
        expected = set(self.__annotations__)
        if set(values) != expected:
            raise TypeError("residual certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("residual certificates are not pickle transport objects")


def _certificate_mapping(
    certificate: ConditionalResidualCheckpointCertificate,
) -> Dict[str, object]:
    return {
        name: (
            certificate.provenance.sha256
            if name == "provenance"
            else getattr(certificate, name)
        )
        for name in certificate.__annotations__
        if name != "certificate_sha256"
    }


def _make_residual_certificate(
    contract: ConditionalResidualContract,
    core: ConfigurationEnergyCheckpointCertificate,
    provenance: ConditionalResidualProvenance,
) -> ConditionalResidualCheckpointCertificate:
    checked_contract = _validate_contract(contract)
    if type(core) is not ConfigurationEnergyCheckpointCertificate:
        raise TypeError(
            "core certificate must be an exact "
            "ConfigurationEnergyCheckpointCertificate"
        )
    if type(provenance) is not ConditionalResidualProvenance:
        raise TypeError("provenance must be an exact ConditionalResidualProvenance")
    if (
        provenance.observation_schema_sha256
        != checked_contract.observation_schema_sha256
        or provenance.task_schema_sha256 != checked_contract.task_schema_sha256
        or provenance.conditioning_adapter_sha256
        != checked_contract.conditioning_adapter_sha256
        or provenance.residual_role_sha256 != checked_contract.residual_role_sha256
    ):
        raise ValueError("residual provenance and semantic contract differ")
    if (
        core.architecture_sha256 != checked_contract.core_architecture_sha256
        or core.process_parameter_sha256 != checked_contract.process_parameter_sha256
    ):
        raise ValueError("core certificate and residual contract differ")
    mathematical_duration = _fraction(checked_contract.schedule_horizon) - _fraction(
        checked_contract.clean_hold
    )
    first_gate = _outward_float(
        Fraction(3, 1) / mathematical_duration,
        name="gate derivative",
    )
    second_gate = _outward_float(
        Fraction(6, 1) / (mathematical_duration * mathematical_duration),
        name="gate second derivative",
    )
    values: Dict[str, object] = {
        "schema_version": CONFIGURATION_RESIDUAL_SCHEMA_VERSION,
        "certificate_scope": CONFIGURATION_RESIDUAL_CERTIFICATE_SCOPE,
        "contract_sha256": checked_contract.contract_sha256,
        "core_architecture_sha256": core.architecture_sha256,
        "process_parameter_sha256": core.process_parameter_sha256,
        "context_schema_sha256": checked_contract.context_schema_sha256,
        "observation_schema_sha256": checked_contract.observation_schema_sha256,
        "task_schema_sha256": checked_contract.task_schema_sha256,
        "conditioning_adapter_sha256": (checked_contract.conditioning_adapter_sha256),
        "residual_role_sha256": checked_contract.residual_role_sha256,
        "core_checkpoint_sha256": core.checkpoint_sha256,
        "core_certificate_sha256": core.certificate_sha256,
        "provenance": provenance,
        "provenance_sha256": provenance.sha256,
        "runtime_sha256": core.runtime_sha256,
        "schedule_horizon": checked_contract.schedule_horizon,
        "clean_hold": checked_contract.clean_hold,
        "active_reverse_duration": checked_contract.active_reverse_duration,
        "gate_policy": CONFIGURATION_RESIDUAL_GATE_POLICY,
        "gate_value_bound": 1.0,
        "mathematical_gate_first_reverse_derivative_bound": first_gate,
        "mathematical_gate_second_reverse_derivative_bound": second_gate,
        "value_bound": core.value_bound,
        "edge_difference_bound": core.edge_difference_bound,
        "log_jump_multiplier_bound": core.edge_difference_bound,
        "jump_rate_multiplier_bound": core.jump_rate_multiplier_bound,
        "first_coordinate_derivative_bound": core.first_derivative_bound,
        "second_coordinate_derivative_bound": core.second_derivative_bound,
        "laplacian_bound": core.laplacian_bound,
        "maximum_reference_exit_rate": core.maximum_reference_exit_rate,
        "maximum_residual_tilted_exit_rate": core.maximum_learned_exit_rate,
        "physical_coordinate_derivatives_certified": True,
        "time_derivatives_certified": False,
        "conditioner_derivatives_certified": False,
        "conditioning_adapter_operationally_authenticated": False,
        "small_forward_error_certified": False,
        "operational_sampler_admissible": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    provisional = ConditionalResidualCheckpointCertificate(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )
    values["certificate_sha256"] = _semantic_digest(_certificate_mapping(provisional))
    return ConditionalResidualCheckpointCertificate(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


def _validate_certificate(
    certificate: object,
) -> ConditionalResidualCheckpointCertificate:
    if type(certificate) is not ConditionalResidualCheckpointCertificate:
        raise TypeError(
            "certificate must be an exact " "ConditionalResidualCheckpointCertificate"
        )
    for name in (
        "contract_sha256",
        "core_architecture_sha256",
        "process_parameter_sha256",
        "context_schema_sha256",
        "observation_schema_sha256",
        "task_schema_sha256",
        "conditioning_adapter_sha256",
        "residual_role_sha256",
        "core_checkpoint_sha256",
        "core_certificate_sha256",
        "provenance_sha256",
        "runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    if certificate.schema_version != CONFIGURATION_RESIDUAL_SCHEMA_VERSION:
        raise ValueError("residual certificate schema is inconsistent")
    if certificate.certificate_scope != CONFIGURATION_RESIDUAL_CERTIFICATE_SCOPE:
        raise ValueError("residual certificate scope is inconsistent")
    if certificate.gate_policy != CONFIGURATION_RESIDUAL_GATE_POLICY:
        raise ValueError("residual certificate gate policy is inconsistent")
    if type(certificate.provenance) is not ConditionalResidualProvenance:
        raise TypeError("certificate provenance has the wrong type")
    if certificate.provenance_sha256 != certificate.provenance.sha256:
        raise ValueError("residual certificate provenance digest is inconsistent")
    for name in (
        "physical_coordinate_derivatives_certified",
        "time_derivatives_certified",
        "conditioner_derivatives_certified",
        "conditioning_adapter_operationally_authenticated",
        "small_forward_error_certified",
        "operational_sampler_admissible",
        "passed",
    ):
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if not certificate.physical_coordinate_derivatives_certified:
        raise ValueError("physical-coordinate certificate must be present")
    if (
        certificate.time_derivatives_certified
        or certificate.conditioner_derivatives_certified
        or certificate.conditioning_adapter_operationally_authenticated
        or certificate.small_forward_error_certified
        or certificate.operational_sampler_admissible
        or not certificate.passed
    ):
        raise ValueError("residual certificate claim flags are inconsistent")
    for name in (
        "schedule_horizon",
        "active_reverse_duration",
        "gate_value_bound",
        "mathematical_gate_first_reverse_derivative_bound",
        "mathematical_gate_second_reverse_derivative_bound",
        "value_bound",
        "edge_difference_bound",
        "log_jump_multiplier_bound",
        "jump_rate_multiplier_bound",
        "first_coordinate_derivative_bound",
        "second_coordinate_derivative_bound",
        "laplacian_bound",
        "maximum_reference_exit_rate",
        "maximum_residual_tilted_exit_rate",
    ):
        _validated_real(
            getattr(certificate, name),
            name="certificate.%s" % name,
            nonnegative=True,
        )
    _validated_real(
        certificate.clean_hold,
        name="certificate.clean_hold",
        nonnegative=True,
    )
    if certificate.certificate_sha256 != _semantic_digest(
        _certificate_mapping(certificate)
    ):
        raise ValueError("residual certificate digest is inconsistent")
    return certificate


@dataclass(frozen=True, eq=False, init=False)
class CertifiedConditionalResidualCheckpoint:
    contract: ConditionalResidualContract
    core_checkpoint: CertifiedConfigurationEnergyCheckpoint
    certificate: ConditionalResidualCheckpointCertificate

    def __init__(
        self,
        *,
        contract: ConditionalResidualContract,
        core_checkpoint: CertifiedConfigurationEnergyCheckpoint,
        certificate: ConditionalResidualCheckpointCertificate,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _CHECKPOINT_TOKEN:
            raise TypeError("residual checkpoints must be created by the module")
        object.__setattr__(self, "contract", contract)
        object.__setattr__(self, "core_checkpoint", core_checkpoint)
        object.__setattr__(self, "certificate", certificate)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("residual checkpoints are not pickle transport objects")


def _validate_checkpoint_shell(
    checkpoint: object,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> CertifiedConditionalResidualCheckpoint:
    if type(checkpoint) is not CertifiedConditionalResidualCheckpoint:
        raise TypeError(
            "checkpoint must be an exact CertifiedConditionalResidualCheckpoint"
        )
    contract = _validate_contract(checkpoint.contract)
    certificate = _validate_certificate(checkpoint.certificate)
    if type(expected_provenance) is not ConditionalResidualProvenance:
        raise TypeError(
            "expected_provenance must be an exact ConditionalResidualProvenance"
        )
    if certificate.provenance_sha256 != expected_provenance.sha256:
        raise ValueError("residual checkpoint provenance differs from trusted record")
    if (
        certificate.contract_sha256 != contract.contract_sha256
        or certificate.core_architecture_sha256 != contract.core_architecture_sha256
        or certificate.process_parameter_sha256 != contract.process_parameter_sha256
        or certificate.context_schema_sha256 != contract.context_schema_sha256
        or certificate.observation_schema_sha256 != contract.observation_schema_sha256
        or certificate.task_schema_sha256 != contract.task_schema_sha256
        or certificate.conditioning_adapter_sha256
        != contract.conditioning_adapter_sha256
        or certificate.residual_role_sha256 != contract.residual_role_sha256
        or certificate.schedule_horizon != contract.schedule_horizon
        or certificate.clean_hold != contract.clean_hold
        or certificate.active_reverse_duration != contract.active_reverse_duration
    ):
        raise ValueError("residual checkpoint certificate and contract differ")
    core = checkpoint.core_checkpoint
    if type(core) is not CertifiedConfigurationEnergyCheckpoint:
        raise TypeError("residual checkpoint carries the wrong core checkpoint type")
    if (
        certificate.core_checkpoint_sha256 != core.certificate.checkpoint_sha256
        or certificate.core_certificate_sha256 != core.certificate.certificate_sha256
    ):
        raise ValueError("residual and core checkpoint records differ")
    expected = _make_residual_certificate(
        contract, core.certificate, expected_provenance
    )
    if expected.certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("residual analytic certificate is inconsistent")
    return checkpoint


def certify_conditional_residual(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    *,
    provenance: ConditionalResidualProvenance,
) -> CertifiedConditionalResidualCheckpoint:
    """Mint a role-separated residual certificate for one stable model."""

    if type(model) is not BoundedConfigurationEnergy:
        raise TypeError("model must be an exact BoundedConfigurationEnergy")
    checked_contract = _require_matching_contract_architecture(
        contract, model.architecture
    )
    if type(provenance) is not ConditionalResidualProvenance:
        raise TypeError("provenance must be exact ConditionalResidualProvenance")
    if (
        provenance.observation_schema_sha256
        != checked_contract.observation_schema_sha256
        or provenance.task_schema_sha256 != checked_contract.task_schema_sha256
        or provenance.conditioning_adapter_sha256
        != checked_contract.conditioning_adapter_sha256
        or provenance.residual_role_sha256 != checked_contract.residual_role_sha256
    ):
        raise ValueError("residual provenance and contract differ")
    core_checkpoint = certify_configuration_energy(
        model, provenance=provenance.core_provenance
    )
    certificate = _make_residual_certificate(
        checked_contract, core_checkpoint.certificate, provenance
    )
    result = CertifiedConditionalResidualCheckpoint(
        contract=checked_contract,
        core_checkpoint=core_checkpoint,
        certificate=certificate,
        _construction_token=_CHECKPOINT_TOKEN,
    )
    return _validate_checkpoint_shell(result, expected_provenance=provenance)


def require_matching_conditional_residual_certificate(
    model: BoundedConfigurationEnergy,
    checkpoint: CertifiedConditionalResidualCheckpoint,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> ConditionalResidualCheckpointCertificate:
    """Refuse unless live core, residual role, schemas, and custody all match."""

    checked = _validate_checkpoint_shell(
        checkpoint, expected_provenance=expected_provenance
    )
    _require_matching_contract_architecture(checked.contract, model.architecture)
    core = require_matching_configuration_energy_certificate(
        model,
        checked.core_checkpoint,
        expected_provenance=expected_provenance.core_provenance,
    )
    if (
        core.checkpoint_sha256 != checked.certificate.core_checkpoint_sha256
        or core.certificate_sha256 != checked.certificate.core_certificate_sha256
    ):
        raise ConfigurationResidualCertificateError(
            "live core certificate differs from the residual certificate"
        )
    final = _make_residual_certificate(checked.contract, core, expected_provenance)
    if final.certificate_sha256 != checked.certificate.certificate_sha256:
        raise ConfigurationResidualCertificateError(
            "residual certificate reconstruction failed"
        )
    return checked.certificate


def materialize_conditional_residual_checkpoint(
    checkpoint: CertifiedConditionalResidualCheckpoint,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> BoundedConfigurationEnergy:
    """Materialize the owned backbone while retaining the residual contract."""

    checked = _validate_checkpoint_shell(
        checkpoint, expected_provenance=expected_provenance
    )
    model = materialize_configuration_energy_checkpoint(
        checked.core_checkpoint,
        expected_provenance=expected_provenance.core_provenance,
    )
    require_matching_conditional_residual_certificate(
        model, checked, expected_provenance=expected_provenance
    )
    return model


def _validate_model_and_batch(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    batch: TypedConfigurationBatch,
) -> Tuple[ConditionalResidualContract, TypedConfigurationBatch]:
    if type(model) is not BoundedConfigurationEnergy:
        raise TypeError("model must be an exact BoundedConfigurationEnergy")
    checked_contract = _require_matching_contract_architecture(
        contract, model.architecture
    )
    if type(batch) is not TypedConfigurationBatch:
        raise TypeError("batch must be an exact TypedConfigurationBatch")
    if type(batch.type_ids) is not tuple or type(batch.coordinates) is not tuple:
        raise TypeError("batch typed fields must be exact tuples")
    if (
        type(batch.batch_indices) is not tuple
        or type(batch.occurrence_counts) is not tuple
    ):
        raise TypeError("batch ragged fields must be exact tuples")
    if batch.type_ids != model.architecture.type_ids:
        raise ValueError("batch type order differs from the residual architecture")
    if batch.architecture_sha256 != model.architecture.architecture_sha256:
        raise ValueError("batch and residual architecture differ")
    if not (
        len(batch.coordinates)
        == len(batch.batch_indices)
        == len(model.architecture.type_ids)
    ):
        raise ValueError("batch ragged fields are inconsistent")
    coordinates = dict(zip(batch.type_ids, batch.coordinates))
    owners = dict(zip(batch.type_ids, batch.batch_indices))
    repacked = pack_typed_configuration_batch(
        model.architecture,
        batch.forward_time,
        batch.context,
        coordinates,
        owners,
    )
    if (
        batch.occurrence_counts != repacked.occurrence_counts
        or batch.batch_size != repacked.batch_size
        or batch.total_occurrences != repacked.total_occurrences
        or batch.total_coordinates != repacked.total_coordinates
    ):
        raise ValueError("batch metadata changed after packing")
    model._validate_state()  # pylint: disable=protected-access
    # The public packer validates direct tensor storage and hooks.  The frozen
    # core's input-only validator additionally walks hidden autograd leaves,
    # rejects ancestry shared across logical inputs, and rejects ancestry in
    # model parameters.  This call is essential on clean-hold rows, where the
    # neural forward is deliberately skipped.
    _require_batch_inputs_independent_of_model(model, (batch,))
    return checked_contract, batch


def _boundary_gate(
    contract: ConditionalResidualContract,
    batch: TypedConfigurationBatch,
) -> Tuple[torch.Tensor, torch.Tensor]:
    active = batch.forward_time > contract.clean_hold
    numerator = batch.forward_time - contract.clean_hold
    ratio = numerator / contract.active_reverse_duration
    active_gate = ratio * ratio * ratio
    gate = torch.where(active, active_gate, torch.zeros_like(active_gate))
    if bool(torch.any(~torch.isfinite(gate)).detach().item()):
        raise ArithmeticError("residual boundary gate is non-finite")
    if bool(torch.any(gate < 0.0).detach().item()) or bool(
        torch.any(gate > 1.0).detach().item()
    ):
        raise ArithmeticError("residual boundary gate left [0,1]")
    if bool(torch.any(active & (gate < _MIN_NORMAL_FLOAT64)).detach().item()):
        raise ConfigurationResidualGateResolutionError(
            "positive residual boundary gate is subnormal or underflowed"
        )
    if bool(torch.any(torch.signbit(gate[~active])).detach().item()):
        raise ArithmeticError("clean-hold gate is not canonical positive zero")
    return gate, active


def configuration_residual_boundary_gate(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    batch: TypedConfigurationBatch,
) -> torch.Tensor:
    """Return the represented gate; this operation never queries the network."""

    checked_contract, checked_batch = _validate_model_and_batch(model, contract, batch)
    gate, _ = _boundary_gate(checked_contract, checked_batch)
    return gate


def _select_rows(
    architecture: ConfigurationEnergyArchitecture,
    batch: TypedConfigurationBatch,
    selected: torch.Tensor,
) -> Tuple[TypedConfigurationBatch, torch.Tensor]:
    indices = torch.nonzero(selected, as_tuple=False).squeeze(-1)
    if indices.numel() == 0:
        raise ValueError("at least one active residual row is required")
    remap = torch.full((batch.batch_size,), -1, dtype=torch.int64, device="cpu")
    remap[indices] = torch.arange(indices.numel(), dtype=torch.int64)
    coordinates: Dict[int, torch.Tensor] = {}
    owners: Dict[int, torch.Tensor] = {}
    for event_type, values, batch_indices in zip(
        batch.type_ids, batch.coordinates, batch.batch_indices
    ):
        remapped = remap.index_select(0, batch_indices)
        mask = remapped >= 0
        coordinates[event_type] = values[mask]
        owners[event_type] = remapped[mask]
    result = pack_typed_configuration_batch(
        architecture,
        batch.forward_time.index_select(0, indices),
        batch.context.index_select(0, indices),
        coordinates,
        owners,
    )
    return result, indices


def _zero_links(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
) -> torch.Tensor:
    # Bounded squares keep successful finite inputs representable while leaving
    # an exact-zero graph with first and second autodiff paths.  The latter is
    # important at the C2 clean-hold splice; a detached literal zero has no
    # second-derivative path.
    linked = torch.tanh(batch.forward_time).square() * 0.0
    linked = linked + torch.tanh(batch.context).square().sum(dim=1) * 0.0
    for coordinates, owners in zip(batch.coordinates, batch.batch_indices):
        per_occurrence = torch.tanh(coordinates).square().sum(dim=1) * 0.0
        linked = linked.index_add(0, owners, per_occurrence)
    for parameter in model.parameters():
        if parameter.numel():
            linked = linked + torch.tanh(parameter.reshape(-1)[0]).square() * 0.0
    return linked


def _assemble_active_values(
    model: BoundedConfigurationEnergy,
    batch: TypedConfigurationBatch,
    active: torch.Tensor,
    indices: torch.Tensor,
    active_values: torch.Tensor,
) -> torch.Tensor:
    linked = _zero_links(model, batch)
    candidate = linked.index_copy(0, indices, active_values)
    return torch.where(active, candidate, linked)


def configuration_residual(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    batch: TypedConfigurationBatch,
) -> torch.Tensor:
    """Evaluate the residual, short-circuiting every clean-hold row."""

    checked_contract, checked_batch = _validate_model_and_batch(model, contract, batch)
    gate, active = _boundary_gate(checked_contract, checked_batch)
    if bool(torch.any(active).detach().item()):
        active_batch, indices = _select_rows(model.architecture, checked_batch, active)
        active_values = model(active_batch) * gate.index_select(0, indices)
    else:
        indices = torch.empty((0,), dtype=torch.int64, device="cpu")
        active_values = torch.empty((0,), dtype=torch.float64, device="cpu")
    result = _assemble_active_values(
        model, checked_batch, active, indices, active_values
    )
    if bool(torch.any(~torch.isfinite(result)).detach().item()):
        raise ArithmeticError("conditional residual is non-finite")
    if bool(
        torch.any(torch.abs(result) > model.architecture.value_bound).detach().item()
    ):
        raise ArithmeticError("conditional residual exceeded its value bound")
    if bool(torch.any(torch.signbit(result[~active])).detach().item()):
        raise ArithmeticError("clean-hold residual is not canonical positive zero")
    return result


def certified_configuration_residual(
    model: BoundedConfigurationEnergy,
    checkpoint: CertifiedConditionalResidualCheckpoint,
    batch: TypedConfigurationBatch,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> torch.Tensor:
    """Evaluate only after live residual checkpoint custody succeeds."""

    certificate = require_matching_conditional_residual_certificate(
        model, checkpoint, expected_provenance=expected_provenance
    )
    result = configuration_residual(model, checkpoint.contract, batch)
    bound = math.nextafter(certificate.value_bound, math.inf)
    if bool(torch.any(torch.abs(result) > bound).detach().item()):
        raise ConfigurationResidualCertificateError(
            "evaluated residual exceeds the certified value envelope"
        )
    return result


def _validate_shared_batches(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    source: TypedConfigurationBatch,
    destination: TypedConfigurationBatch,
) -> Tuple[
    ConditionalResidualContract, TypedConfigurationBatch, TypedConfigurationBatch
]:
    checked_contract, checked_source = _validate_model_and_batch(
        model, contract, source
    )
    _, checked_destination = _validate_model_and_batch(
        model, checked_contract, destination
    )
    if checked_source.batch_size != checked_destination.batch_size:
        raise ValueError("source and destination batch sizes differ")
    if not torch.equal(checked_source.forward_time, checked_destination.forward_time):
        raise ValueError("source and destination direct times differ")
    if not torch.equal(checked_source.context, checked_destination.context):
        raise ValueError("source and destination conditioners differ")
    return checked_contract, checked_source, checked_destination


def configuration_residual_state_pair_difference(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    source: TypedConfigurationBatch,
    destination: TypedConfigurationBatch,
) -> torch.Tensor:
    """Subtract same-condition states; this does not validate a process edit."""

    checked_contract, checked_source, checked_destination = _validate_shared_batches(
        model, contract, source, destination
    )
    gate, active = _boundary_gate(checked_contract, checked_source)
    if bool(torch.any(active).detach().item()):
        active_source, indices = _select_rows(
            model.architecture, checked_source, active
        )
        active_destination, destination_indices = _select_rows(
            model.architecture, checked_destination, active
        )
        if not torch.equal(indices, destination_indices):
            raise RuntimeError("source and destination active rows differ")
        core_difference = configuration_energy_edge_difference(
            model, active_source, active_destination
        )
        active_difference = core_difference * gate.index_select(0, indices)
    else:
        indices = torch.empty((0,), dtype=torch.int64, device="cpu")
        active_difference = torch.empty((0,), dtype=torch.float64, device="cpu")
    result = _assemble_active_values(
        model, checked_source, active, indices, active_difference
    )
    # The clean-hold difference is constant in both endpoints.  Retain an
    # exact-zero destination graph without evaluating the neural core so
    # first- and second-coordinate derivatives are defined as zero rather
    # than reported as unused by autograd.
    result = result + _zero_links(model, checked_destination)
    if bool(torch.any(~torch.isfinite(result)).detach().item()):
        raise ArithmeticError("residual state-pair difference is non-finite")
    edge_bound = math.nextafter(2.0 * model.architecture.value_bound, math.inf)
    if bool(torch.any(torch.abs(result) > edge_bound).detach().item()):
        raise ArithmeticError("residual state-pair difference exceeded 2B")
    if bool(torch.any(torch.signbit(result[~active])).detach().item()):
        raise ArithmeticError("clean-hold residual difference is not positive zero")
    return result


def certified_configuration_residual_state_pair_difference(
    model: BoundedConfigurationEnergy,
    checkpoint: CertifiedConditionalResidualCheckpoint,
    source: TypedConfigurationBatch,
    destination: TypedConfigurationBatch,
    *,
    expected_provenance: ConditionalResidualProvenance,
) -> torch.Tensor:
    """Evaluate a same-condition residual difference under live custody."""

    certificate = require_matching_conditional_residual_certificate(
        model, checkpoint, expected_provenance=expected_provenance
    )
    difference = configuration_residual_state_pair_difference(
        model, checkpoint.contract, source, destination
    )
    bound = math.nextafter(certificate.edge_difference_bound, math.inf)
    if bool(torch.any(torch.abs(difference) > bound).detach().item()):
        raise ConfigurationResidualCertificateError(
            "residual difference exceeds the certified envelope"
        )
    return difference


@dataclass(frozen=True, eq=False, init=False)
class ConditionalResidualDerivatives:
    residual: torch.Tensor
    coordinate_gradients: Tuple[torch.Tensor, ...]
    laplacian: Optional[torch.Tensor]
    laplacian_method: str

    def __init__(
        self,
        *,
        residual: torch.Tensor,
        coordinate_gradients: Tuple[torch.Tensor, ...],
        laplacian: Optional[torch.Tensor],
        laplacian_method: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _DERIVATIVE_TOKEN:
            raise TypeError("residual derivative records must be created by the module")
        object.__setattr__(self, "residual", residual)
        object.__setattr__(self, "coordinate_gradients", coordinate_gradients)
        object.__setattr__(self, "laplacian", laplacian)
        object.__setattr__(self, "laplacian_method", laplacian_method)

    @property
    def operational_sampler_admissible(self) -> bool:
        return False

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("residual derivative records are not pickle objects")


def _scatter_active_gradients(
    batch: TypedConfigurationBatch,
    active_batch: TypedConfigurationBatch,
    active_gradients: Tuple[torch.Tensor, ...],
    active_rows: torch.Tensor,
    gate: torch.Tensor,
) -> Tuple[torch.Tensor, ...]:
    remap = torch.full((batch.batch_size,), -1, dtype=torch.int64, device="cpu")
    remap[active_rows] = torch.arange(active_rows.numel(), dtype=torch.int64)
    result = []
    for coordinates, owners, active_owners, gradient in zip(
        batch.coordinates,
        batch.batch_indices,
        active_batch.batch_indices,
        active_gradients,
    ):
        remapped = remap.index_select(0, owners)
        mask = remapped >= 0
        scaled = gradient * gate.index_select(0, active_rows).index_select(
            0, active_owners
        ).unsqueeze(-1)
        full = torch.tanh(coordinates).square() * 0.0
        occurrence_indices = torch.nonzero(mask, as_tuple=False).squeeze(-1)
        full = full.index_copy(0, occurrence_indices, scaled)
        result.append(full)
    return tuple(result)


def configuration_residual_coordinate_gradients(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    batch: TypedConfigurationBatch,
    *,
    create_graph: bool = False,
) -> ConditionalResidualDerivatives:
    """Return gradients in architecture type order, excluding time/context."""

    checked_contract, checked_batch = _validate_model_and_batch(model, contract, batch)
    if type(create_graph) is not bool:
        raise TypeError("create_graph must be boolean")
    for coordinates in checked_batch.coordinates:
        if coordinates.numel() and not coordinates.requires_grad:
            raise ValueError("nonempty continuous coordinates must require gradients")
    gate, active = _boundary_gate(checked_contract, checked_batch)
    if bool(torch.any(active).detach().item()):
        active_batch, indices = _select_rows(model.architecture, checked_batch, active)
        core = configuration_energy_coordinate_gradients(
            model, active_batch, create_graph=create_graph
        )
        residual = _assemble_active_values(
            model,
            checked_batch,
            active,
            indices,
            core.energy * gate.index_select(0, indices),
        )
        gradients = _scatter_active_gradients(
            checked_batch,
            active_batch,
            core.coordinate_gradients,
            indices,
            gate,
        )
    else:
        residual = configuration_residual(model, checked_contract, checked_batch)
        gradients = tuple(
            torch.tanh(value).square() * 0.0 for value in checked_batch.coordinates
        )
    if not create_graph:
        gradients = tuple(value.detach() for value in gradients)
    return ConditionalResidualDerivatives(
        residual=residual,
        coordinate_gradients=gradients,
        laplacian=None,
        laplacian_method="not-requested",
        _construction_token=_DERIVATIVE_TOKEN,
    )


def configuration_residual_exact_laplacian(
    model: BoundedConfigurationEnergy,
    contract: ConditionalResidualContract,
    batch: TypedConfigurationBatch,
    *,
    create_graph: bool = False,
) -> ConditionalResidualDerivatives:
    """Return the exact physical-coordinate Laplacian for active rows."""

    checked_contract, checked_batch = _validate_model_and_batch(model, contract, batch)
    if type(create_graph) is not bool:
        raise TypeError("create_graph must be boolean")
    if (
        checked_batch.total_coordinates
        > MAX_CONFIGURATION_ENERGY_EXACT_LAPLACIAN_COORDINATES
    ):
        raise ConfigurationEnergyResourceError(
            "residual exact Laplacian exceeds the coordinate limit"
        )
    for coordinates in checked_batch.coordinates:
        if coordinates.numel() and not coordinates.requires_grad:
            raise ValueError("nonempty continuous coordinates must require gradients")
    gate, active = _boundary_gate(checked_contract, checked_batch)
    if bool(torch.any(active).detach().item()):
        active_batch, indices = _select_rows(model.architecture, checked_batch, active)
        core: ConfigurationEnergyDerivatives = configuration_energy_exact_laplacian(
            model, active_batch, create_graph=create_graph
        )
        if core.laplacian is None:  # pragma: no cover - core invariant
            raise RuntimeError("core exact Laplacian is missing")
        residual = _assemble_active_values(
            model,
            checked_batch,
            active,
            indices,
            core.energy * gate.index_select(0, indices),
        )
        gradients = _scatter_active_gradients(
            checked_batch,
            active_batch,
            core.coordinate_gradients,
            indices,
            gate,
        )
        active_laplacian = core.laplacian * gate.index_select(0, indices)
        laplacian = _assemble_active_values(
            model,
            checked_batch,
            active,
            indices,
            active_laplacian,
        )
    else:
        residual = configuration_residual(model, checked_contract, checked_batch)
        gradients = tuple(
            torch.tanh(value).square() * 0.0 for value in checked_batch.coordinates
        )
        linked = _zero_links(model, checked_batch)
        laplacian = linked
    if not create_graph:
        gradients = tuple(value.detach() for value in gradients)
        laplacian = laplacian.detach()
    return ConditionalResidualDerivatives(
        residual=residual,
        coordinate_gradients=gradients,
        laplacian=laplacian,
        laplacian_method="exact-active-row-autodiff-diagonal-v1",
        _construction_token=_DERIVATIVE_TOKEN,
    )


def residual_time_specific_bounds(
    certificate: ConditionalResidualCheckpointCertificate,
    contract: ConditionalResidualContract,
    *,
    direct_time: object,
) -> Dict[str, float]:
    """Derive and apply the gate for one contract-bound direct timestamp."""

    checked = _validate_certificate(certificate)
    checked_contract = _validate_contract(contract)
    if (
        checked.contract_sha256 != checked_contract.contract_sha256
        or checked.schedule_horizon != checked_contract.schedule_horizon
        or checked.clean_hold != checked_contract.clean_hold
        or checked.active_reverse_duration != checked_contract.active_reverse_duration
    ):
        raise ValueError("certificate and residual contract differ")
    time = _validated_real(direct_time, name="direct_time", nonnegative=True)
    if time > checked_contract.schedule_horizon:
        raise ValueError("direct_time lies outside the process horizon")
    if time <= checked_contract.clean_hold:
        mathematical_gate_upper = 0.0
        operational_gate_upper = 0.0
    else:
        mathematical_duration = _fraction(
            checked_contract.schedule_horizon
        ) - _fraction(checked_contract.clean_hold)
        mathematical_gate_upper = _outward_float(
            (
                (_fraction(time) - _fraction(checked_contract.clean_hold))
                / mathematical_duration
            )
            ** 3,
            name="mathematical gate",
        )
        # Mirror the runtime's subtraction, division, and two multiplications
        # with a monotone directed upper witness at every stage.  Rounding only
        # the final product is insufficient: a downward-rounded gate can make
        # a supposedly outward scaled certificate too small.
        numerator_upper = _outward_float(
            _fraction(time) - _fraction(checked_contract.clean_hold),
            name="gate numerator",
        )
        ratio_upper = _outward_float(
            _fraction(numerator_upper)
            / _fraction(checked_contract.active_reverse_duration),
            name="gate ratio",
        )
        # Direct times are bounded by the horizon and the runtime gate refuses
        # values above one.  This clamp removes harmless directed overshoot at
        # the exactly active endpoint.
        ratio_upper = min(ratio_upper, 1.0)
        square_upper = _outward_float(
            _fraction(ratio_upper) * _fraction(ratio_upper),
            name="gate square",
        )
        operational_gate_upper = _outward_float(
            _fraction(square_upper) * _fraction(ratio_upper),
            name="gate cube",
        )
        operational_gate_upper = min(operational_gate_upper, 1.0)
        if operational_gate_upper < _MIN_NORMAL_FLOAT64:
            raise ConfigurationResidualGateResolutionError(
                "positive residual boundary gate is subnormal or underflowed"
            )
    gate_bound = max(mathematical_gate_upper, operational_gate_upper)
    factor = _fraction(gate_bound)
    return {
        "mathematical_gate_upper_bound": mathematical_gate_upper,
        "operational_gate_upper_bound": operational_gate_upper,
        "gate_bound_used": gate_bound,
        "value_bound": _outward_float(
            factor * _fraction(checked.value_bound), name="scaled value bound"
        ),
        "edge_difference_bound": _outward_float(
            factor * _fraction(checked.edge_difference_bound),
            name="scaled edge bound",
        ),
        "first_coordinate_derivative_bound": _outward_float(
            factor * _fraction(checked.first_coordinate_derivative_bound),
            name="scaled first-coordinate bound",
        ),
        "second_coordinate_derivative_bound": _outward_float(
            factor * _fraction(checked.second_coordinate_derivative_bound),
            name="scaled second-coordinate bound",
        ),
        "laplacian_bound": _outward_float(
            factor * _fraction(checked.laplacian_bound),
            name="scaled Laplacian bound",
        ),
    }


__all__ = [
    "CONFIGURATION_RESIDUAL_CERTIFICATE_SCOPE",
    "CONFIGURATION_RESIDUAL_CONDITIONER_SCOPE",
    "CONFIGURATION_RESIDUAL_GATE_POLICY",
    "CONFIGURATION_RESIDUAL_SCHEMA_VERSION",
    "CertifiedConditionalResidualCheckpoint",
    "ConditionalResidualCheckpointCertificate",
    "ConditionalResidualContract",
    "ConditionalResidualDerivatives",
    "ConditionalResidualProvenance",
    "ConfigurationResidualCertificateError",
    "ConfigurationResidualGateResolutionError",
    "certified_configuration_residual",
    "certified_configuration_residual_state_pair_difference",
    "certify_conditional_residual",
    "configuration_residual",
    "configuration_residual_boundary_gate",
    "configuration_residual_coordinate_gradients",
    "configuration_residual_exact_laplacian",
    "configuration_residual_state_pair_difference",
    "make_conditional_residual_contract",
    "materialize_conditional_residual_checkpoint",
    "require_matching_conditional_residual_certificate",
    "residual_time_specific_bounds",
]
