"""Pure B06-to-B12 contract for two-domain baseline adapters.

This module validates identities and already-materialized values only.  It has
no model loader, external-package import, data conversion, training,
inference, metric evaluation, randomness, filesystem access, or network
surface.  In particular, satisfying this contract does not demonstrate that
an upstream model can produce an F105 configuration.  Actual external-package
execution, every author-written model transformation, and end-to-end
qualification remain B12 obligations.

The contract deliberately accepts only the external-baseline and
literature-family adapter rows that carry complete capability matrices in the
frozen B06 registry.  Primary methods and local interpretation controls have
different interfaces and cannot be smuggled through this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Tuple

from heterodiff.evaluation.fixed_r64_cks_statistical_adapter import (
    F109_ADDRESS_FIELDS,
    F109AddressedDraw,
    F109_CONDITIONAL_DRAWS_PER_CASE,
    F109DrawAddress,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    ExactConfiguration,
)
from heterodiff.experiments import two_domain_baseline_registry as registry


ADAPTER_CONTRACT_STATE = "STATIC_IDENTITY_AND_MATERIALIZED_INPUT_VALIDATION_ONLY"
B12_EXECUTION_BOUNDARY = (
    "ACTUAL_EXTERNAL_PACKAGE_EXECUTION_MODEL_TRANSFORMATION_AND_END_TO_END_"
    "QUALIFICATION_REMAIN_B12"
)

REGISTRY_TO_F109_DOMAIN: Mapping[str, str] = MappingProxyType(
    {
        registry.PHYSIONET_DOMAIN_ID: "R3-PHYS",
        registry.RETAIL_DOMAIN_ID: "R4-RETAIL",
    }
)
F109_TO_REGISTRY_DOMAIN: Mapping[str, str] = MappingProxyType(
    {value: key for key, value in REGISTRY_TO_F109_DOMAIN.items()}
)


class BaselineAdapterContractError(ValueError):
    """Raised when a proposed adapter contract differs from the B06 freeze."""


CapabilityDeclarations = Tuple[Tuple[str, str], ...]
AddressRoster = Tuple[F109DrawAddress, ...]
AddressedDrawRoster = Tuple[F109AddressedDraw, ...]


def _exact_capability_declarations(value: object) -> CapabilityDeclarations:
    if type(value) is not dict:
        raise BaselineAdapterContractError(
            "the frozen capability matrix must be an exact dictionary"
        )
    if tuple(value) != registry.CAPABILITY_AXES:
        raise BaselineAdapterContractError(
            "the capability axes or their canonical order differ from B06"
        )
    declarations = tuple(value.items())
    for axis, state in declarations:
        if type(axis) is not str or type(state) is not str:
            raise BaselineAdapterContractError(
                "capability declarations must contain exact strings"
            )
        if state not in registry.FINAL_CAPABILITY_STATES:
            raise BaselineAdapterContractError(
                "a capability declaration is not a frozen final state"
            )
    return declarations


@dataclass(frozen=True)
class RegistryAdapterDeclaration:
    """One immutable projection of an adapter-bearing B06 registry row."""

    registry_kind: str
    method_id: str
    registry_domain_id: str
    f109_domain_id: str
    config_sha256: str
    capability_declarations: CapabilityDeclarations
    b12_runtime_qualification_required: bool

    def __post_init__(self) -> None:
        if self.registry_kind not in ("EXTERNAL_BASELINE", "LITERATURE_FAMILY"):
            raise BaselineAdapterContractError("registry_kind is not adapter-bearing")
        if type(self.method_id) is not str or not self.method_id:
            raise TypeError("method_id must be a nonempty exact string")
        if self.registry_domain_id not in REGISTRY_TO_F109_DOMAIN:
            raise BaselineAdapterContractError("registry domain is not frozen")
        if self.f109_domain_id != REGISTRY_TO_F109_DOMAIN[self.registry_domain_id]:
            raise BaselineAdapterContractError("registry/F109 domain mapping differs")
        if type(self.config_sha256) is not str or len(self.config_sha256) != 64:
            raise BaselineAdapterContractError("config_sha256 is not exact")
        if type(self.capability_declarations) is not tuple:
            raise TypeError("capability_declarations must be an exact tuple")
        if self.b12_runtime_qualification_required is not True:
            raise BaselineAdapterContractError(
                "adapter execution qualification must remain owned by B12"
            )


def _adapter_candidates(
    method_id: str, registry_domain_id: str
) -> Tuple[RegistryAdapterDeclaration, ...]:
    candidates = []
    frozen = registry.FROZEN_REGISTRY

    for row in frozen["external_baselines"]:
        if (
            row["method_id"] == method_id
            and row["domain_id"] == registry_domain_id
        ):
            statement = row["native_capability_and_extension_statement"]
            required = (
                row["config"]["b12_runtime_qualification_required"] is True
                and statement["runtime_qualification_owned_by_B12"] is True
            )
            candidates.append(
                RegistryAdapterDeclaration(
                    registry_kind="EXTERNAL_BASELINE",
                    method_id=method_id,
                    registry_domain_id=registry_domain_id,
                    f109_domain_id=REGISTRY_TO_F109_DOMAIN[registry_domain_id],
                    config_sha256=row["config_sha256"],
                    capability_declarations=_exact_capability_declarations(
                        statement["capability_matrix"]
                    ),
                    b12_runtime_qualification_required=required,
                )
            )

    for family in frozen["literature_families"]:
        implementation = family["implementation_by_domain"][registry_domain_id]
        if implementation["implementation_id"] != method_id:
            continue
        config = family["configs_by_domain"][registry_domain_id]
        required = (
            implementation["b12_runtime_qualification_required"] is True
            and config["b12_runtime_qualification_required"] is True
        )
        candidates.append(
            RegistryAdapterDeclaration(
                registry_kind="LITERATURE_FAMILY",
                method_id=method_id,
                registry_domain_id=registry_domain_id,
                f109_domain_id=REGISTRY_TO_F109_DOMAIN[registry_domain_id],
                config_sha256=implementation["config_sha256"],
                capability_declarations=_exact_capability_declarations(
                    implementation["capability_matrix"]
                ),
                b12_runtime_qualification_required=required,
            )
        )

    return tuple(candidates)


def registry_adapter_declaration(
    method_id: object, registry_domain_id: object
) -> RegistryAdapterDeclaration:
    """Resolve exactly one external or literature adapter identity from B06."""

    if type(method_id) is not str or not method_id:
        raise TypeError("method_id must be a nonempty exact string")
    if type(registry_domain_id) is not str:
        raise TypeError("registry_domain_id must be an exact string")
    if registry_domain_id not in REGISTRY_TO_F109_DOMAIN:
        raise BaselineAdapterContractError("registry_domain_id is not frozen")
    candidates = _adapter_candidates(method_id, registry_domain_id)
    if not candidates:
        raise BaselineAdapterContractError(
            "method/domain identity is not an adapter-bearing B06 registry row"
        )
    if len(candidates) != 1:
        raise BaselineAdapterContractError(
            "method/domain identity is ambiguous in the B06 registry"
        )
    return candidates[0]


def _address_key(address: F109DrawAddress) -> Tuple[str, ...]:
    return tuple(getattr(address, field_name) for field_name in F109_ADDRESS_FIELDS)


def _case_key(address: F109DrawAddress) -> Tuple[str, ...]:
    return (
        address.domain_id,
        address.seed_id,
        address.group_id,
        address.case_id,
        address.conditioning_id,
    )


def _validate_address_roster(
    value: object, *, f109_domain_id: str
) -> AddressRoster:
    if type(value) is not tuple:
        raise TypeError("address_roster must be an exact tuple")
    if len(value) != F109_CONDITIONAL_DRAWS_PER_CASE:
        raise BaselineAdapterContractError(
            "address_roster must contain exactly the frozen R64 draw count"
        )
    if any(type(address) is not F109DrawAddress for address in value):
        raise TypeError("address_roster must contain exact F109DrawAddress values")
    addresses = tuple(value)
    if any(address.domain_id != f109_domain_id for address in addresses):
        raise BaselineAdapterContractError(
            "an F109 address disagrees with the mapped registry domain"
        )
    first_case = _case_key(addresses[0])
    if any(_case_key(address) != first_case for address in addresses):
        raise BaselineAdapterContractError(
            "address_roster spans more than one seed/group/case/conditioning key"
        )
    keys = tuple(_address_key(address) for address in addresses)
    if len(set(keys)) != F109_CONDITIONAL_DRAWS_PER_CASE:
        raise BaselineAdapterContractError("address_roster contains duplicates")
    if keys != tuple(sorted(keys)):
        raise BaselineAdapterContractError(
            "address_roster is not in exact canonical F109 address order"
        )
    return addresses


@dataclass(frozen=True)
class BaselineAdapterContract:
    """Frozen identity plus one exact method-neutral F109 address roster."""

    method_id: str
    registry_domain_id: str
    config_sha256: str
    capability_declarations: CapabilityDeclarations
    address_roster: AddressRoster
    registry_kind: str = field(init=False)
    f109_domain_id: str = field(init=False)
    state: str = field(init=False, default=ADAPTER_CONTRACT_STATE)
    b12_execution_boundary: str = field(init=False, default=B12_EXECUTION_BOUNDARY)
    b12_runtime_qualification_required: bool = field(init=False, default=True)
    external_execution_or_model_transformation_present: bool = field(
        init=False, default=False
    )

    def __post_init__(self) -> None:
        if type(self.method_id) is not str or not self.method_id:
            raise TypeError("method_id must be a nonempty exact string")
        if type(self.registry_domain_id) is not str:
            raise TypeError("registry_domain_id must be an exact string")
        if type(self.config_sha256) is not str:
            raise TypeError("config_sha256 must be an exact string")
        if type(self.capability_declarations) is not tuple:
            raise TypeError("capability_declarations must be an exact tuple")
        declaration = registry_adapter_declaration(
            self.method_id, self.registry_domain_id
        )
        if self.config_sha256 != declaration.config_sha256:
            raise BaselineAdapterContractError(
                "method/domain/config identity differs from the B06 registry"
            )
        if self.capability_declarations != declaration.capability_declarations:
            raise BaselineAdapterContractError(
                "capability declarations differ from the B06 registry"
            )
        addresses = _validate_address_roster(
            self.address_roster, f109_domain_id=declaration.f109_domain_id
        )
        object.__setattr__(self, "address_roster", addresses)
        object.__setattr__(self, "registry_kind", declaration.registry_kind)
        object.__setattr__(self, "f109_domain_id", declaration.f109_domain_id)


def make_baseline_adapter_contract(
    *,
    method_id: object,
    registry_domain_id: object,
    config_sha256: object,
    capability_declarations: object,
    address_roster: object,
) -> BaselineAdapterContract:
    """Construct a contract only when every caller assertion is registry-exact."""

    return BaselineAdapterContract(
        method_id=method_id,  # type: ignore[arg-type]
        registry_domain_id=registry_domain_id,  # type: ignore[arg-type]
        config_sha256=config_sha256,  # type: ignore[arg-type]
        capability_declarations=capability_declarations,  # type: ignore[arg-type]
        address_roster=address_roster,  # type: ignore[arg-type]
    )


@dataclass(frozen=True)
class ValidatedBaselineAdapterCase:
    """Already-materialized F105 target and ordered F109 draws; no execution."""

    contract: BaselineAdapterContract
    target: ExactConfiguration
    addressed_draws: AddressedDrawRoster
    state: str = field(init=False, default=ADAPTER_CONTRACT_STATE)
    b12_execution_boundary: str = field(init=False, default=B12_EXECUTION_BOUNDARY)
    external_execution_or_model_transformation_present: bool = field(
        init=False, default=False
    )

    def __post_init__(self) -> None:
        if type(self.contract) is not BaselineAdapterContract:
            raise TypeError("contract must be an exact BaselineAdapterContract")
        if type(self.target) is not ExactConfiguration:
            raise TypeError("target must be an exact F105 ExactConfiguration")
        if self.target.domain_id != self.contract.f109_domain_id:
            raise BaselineAdapterContractError(
                "target domain disagrees with the adapter registry identity"
            )
        if type(self.addressed_draws) is not tuple:
            raise TypeError("addressed_draws must be an exact tuple")
        if len(self.addressed_draws) != F109_CONDITIONAL_DRAWS_PER_CASE:
            raise BaselineAdapterContractError(
                "addressed_draws must contain exactly the frozen R64 draw count"
            )
        if any(type(row) is not F109AddressedDraw for row in self.addressed_draws):
            raise TypeError(
                "addressed_draws must contain exact F109AddressedDraw values"
            )
        draws = tuple(self.addressed_draws)
        if tuple(row.address for row in draws) != self.contract.address_roster:
            raise BaselineAdapterContractError(
                "addressed_draws differ from the exact ordered contract roster"
            )
        for row in draws:
            if type(row.configuration) is not ExactConfiguration:
                raise TypeError(
                    "each materialized draw must be an exact F105 ExactConfiguration"
                )
            if row.configuration.domain_id != self.contract.f109_domain_id:
                raise BaselineAdapterContractError(
                    "a materialized draw belongs to another F105 domain"
                )
        object.__setattr__(self, "addressed_draws", draws)


def validate_baseline_adapter_case(
    contract: object, target: object, addressed_draws: object
) -> ValidatedBaselineAdapterCase:
    """Validate materialized inputs without invoking or transforming a model."""

    return ValidatedBaselineAdapterCase(
        contract=contract,  # type: ignore[arg-type]
        target=target,  # type: ignore[arg-type]
        addressed_draws=addressed_draws,  # type: ignore[arg-type]
    )


__all__ = [
    "ADAPTER_CONTRACT_STATE",
    "AddressRoster",
    "AddressedDrawRoster",
    "B12_EXECUTION_BOUNDARY",
    "BaselineAdapterContract",
    "BaselineAdapterContractError",
    "CapabilityDeclarations",
    "F109_TO_REGISTRY_DOMAIN",
    "REGISTRY_TO_F109_DOMAIN",
    "RegistryAdapterDeclaration",
    "ValidatedBaselineAdapterCase",
    "make_baseline_adapter_contract",
    "registry_adapter_declaration",
    "validate_baseline_adapter_case",
]
