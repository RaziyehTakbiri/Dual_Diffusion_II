from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from heterodiff.evaluation.fixed_r64_cks_statistical_adapter import (
    F109AddressedDraw,
    F109DrawAddress,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    ExactConfiguration,
    physionet_configuration,
    retail_configuration,
)
from heterodiff.experiments import two_domain_baseline_adapter_contract as contract
from heterodiff.experiments import two_domain_baseline_registry as registry


ROOT = Path(__file__).resolve().parents[2]


def _external_method(domain_id: str) -> str:
    rows = [
        row
        for row in registry.FROZEN_REGISTRY["external_baselines"]
        if row["domain_id"] == domain_id
    ]
    assert len(rows) == 1
    return rows[0]["method_id"]


def _declaration(domain_id: str) -> contract.RegistryAdapterDeclaration:
    return contract.registry_adapter_declaration(
        _external_method(domain_id), domain_id
    )


def _addresses(
    domain_id: str, *, count: int = 64
) -> tuple[F109DrawAddress, ...]:
    f109_domain = contract.REGISTRY_TO_F109_DOMAIN[domain_id]
    return tuple(
        F109DrawAddress(
            domain_id=f109_domain,
            seed_id="SEED-000",
            group_id="GROUP-000",
            case_id="CASE-000",
            draw_id=f"DRAW-{ordinal:03d}",
            conditioning_id="CONDITION-000",
        )
        for ordinal in range(count)
    )


def _frozen_contract(domain_id: str) -> contract.BaselineAdapterContract:
    declaration = _declaration(domain_id)
    return contract.make_baseline_adapter_contract(
        method_id=declaration.method_id,
        registry_domain_id=domain_id,
        config_sha256=declaration.config_sha256,
        capability_declarations=declaration.capability_declarations,
        address_roster=_addresses(domain_id),
    )


def _empty_configuration(domain_id: str) -> ExactConfiguration:
    if domain_id == registry.PHYSIONET_DOMAIN_ID:
        return physionet_configuration(())
    return retail_configuration(())


def _draws(
    domain_id: str, *, configuration: object | None = None, count: int = 64
) -> tuple[F109AddressedDraw, ...]:
    if configuration is None:
        configuration = _empty_configuration(domain_id)
    return tuple(
        F109AddressedDraw(address=address, configuration=configuration)
        for address in _addresses(domain_id, count=count)
    )


def test_domain_mapping_is_exact_and_bijective() -> None:
    assert dict(contract.REGISTRY_TO_F109_DOMAIN) == {
        "physionet-challenge-2012": "R3-PHYS",
        "online-retail-ii": "R4-RETAIL",
    }
    assert dict(contract.F109_TO_REGISTRY_DOMAIN) == {
        "R3-PHYS": "physionet-challenge-2012",
        "R4-RETAIL": "online-retail-ii",
    }
    with pytest.raises(TypeError):
        contract.REGISTRY_TO_F109_DOMAIN["new-domain"] = "R5"  # type: ignore[index]


@pytest.mark.parametrize("domain_id", registry.DOMAIN_IDS)
def test_external_declaration_and_case_accept_exact_frozen_values(
    domain_id: str,
) -> None:
    declaration = _declaration(domain_id)
    frozen = _frozen_contract(domain_id)
    target = _empty_configuration(domain_id)
    draws = _draws(domain_id)
    validated = contract.validate_baseline_adapter_case(frozen, target, draws)

    assert declaration.registry_kind == "EXTERNAL_BASELINE"
    assert frozen.registry_kind == declaration.registry_kind
    assert frozen.f109_domain_id == contract.REGISTRY_TO_F109_DOMAIN[domain_id]
    assert frozen.state == contract.ADAPTER_CONTRACT_STATE
    assert frozen.b12_runtime_qualification_required is True
    assert frozen.external_execution_or_model_transformation_present is False
    assert validated.target is target
    assert validated.addressed_draws is draws
    assert validated.b12_execution_boundary == contract.B12_EXECUTION_BOUNDARY
    assert validated.external_execution_or_model_transformation_present is False
    with pytest.raises(FrozenInstanceError):
        frozen.method_id = "changed"  # type: ignore[misc]


def test_literature_family_adapter_identity_is_also_registry_bound() -> None:
    family = registry.FROZEN_REGISTRY["literature_families"][0]
    domain_id = registry.PHYSIONET_DOMAIN_ID
    method_id = family["implementation_by_domain"][domain_id]["implementation_id"]
    declaration = contract.registry_adapter_declaration(method_id, domain_id)
    frozen = contract.make_baseline_adapter_contract(
        method_id=method_id,
        registry_domain_id=domain_id,
        config_sha256=declaration.config_sha256,
        capability_declarations=declaration.capability_declarations,
        address_roster=_addresses(domain_id),
    )
    assert declaration.registry_kind == "LITERATURE_FAMILY"
    assert frozen.registry_kind == "LITERATURE_FAMILY"


def test_primary_methods_and_controls_cannot_use_the_external_adapter_contract() -> None:
    with pytest.raises(contract.BaselineAdapterContractError, match="adapter-bearing"):
        contract.registry_adapter_declaration(
            registry.PRIMARY_METHOD_IDS[0], registry.PHYSIONET_DOMAIN_ID
        )
    with pytest.raises(contract.BaselineAdapterContractError, match="adapter-bearing"):
        contract.registry_adapter_declaration(
            registry.CONTROL_IDS[0], registry.PHYSIONET_DOMAIN_ID
        )


def test_method_domain_and_config_identity_are_noninterchangeable() -> None:
    phys = _declaration(registry.PHYSIONET_DOMAIN_ID)
    retail = _declaration(registry.RETAIL_DOMAIN_ID)
    with pytest.raises(contract.BaselineAdapterContractError, match="adapter-bearing"):
        contract.registry_adapter_declaration(
            phys.method_id, registry.RETAIL_DOMAIN_ID
        )
    with pytest.raises(contract.BaselineAdapterContractError, match="config identity"):
        contract.make_baseline_adapter_contract(
            method_id=phys.method_id,
            registry_domain_id=registry.PHYSIONET_DOMAIN_ID,
            config_sha256=retail.config_sha256,
            capability_declarations=phys.capability_declarations,
            address_roster=_addresses(registry.PHYSIONET_DOMAIN_ID),
        )


def test_capability_axes_states_and_order_are_exact() -> None:
    domain_id = registry.PHYSIONET_DOMAIN_ID
    declaration = _declaration(domain_id)
    changed = list(declaration.capability_declarations)
    changed[0] = (changed[0][0], "NATIVE")
    if tuple(changed) == declaration.capability_declarations:
        changed[0] = (changed[0][0], "AUTHOR_EXTENSION")
    with pytest.raises(contract.BaselineAdapterContractError, match="capability"):
        contract.make_baseline_adapter_contract(
            method_id=declaration.method_id,
            registry_domain_id=domain_id,
            config_sha256=declaration.config_sha256,
            capability_declarations=tuple(changed),
            address_roster=_addresses(domain_id),
        )
    with pytest.raises(contract.BaselineAdapterContractError, match="capability"):
        contract.make_baseline_adapter_contract(
            method_id=declaration.method_id,
            registry_domain_id=domain_id,
            config_sha256=declaration.config_sha256,
            capability_declarations=tuple(
                reversed(declaration.capability_declarations)
            ),
            address_roster=_addresses(domain_id),
        )


@pytest.mark.parametrize("count", [0, 1, 63, 65, 128])
def test_contract_refuses_every_non_r64_address_count(count: int) -> None:
    domain_id = registry.PHYSIONET_DOMAIN_ID
    declaration = _declaration(domain_id)
    with pytest.raises(contract.BaselineAdapterContractError, match="R64"):
        contract.make_baseline_adapter_contract(
            method_id=declaration.method_id,
            registry_domain_id=domain_id,
            config_sha256=declaration.config_sha256,
            capability_declarations=declaration.capability_declarations,
            address_roster=_addresses(domain_id, count=count),
        )


def test_contract_refuses_wrong_domain_duplicate_cross_case_and_noncanonical_order() -> None:
    domain_id = registry.PHYSIONET_DOMAIN_ID
    declaration = _declaration(domain_id)

    wrong_domain = list(_addresses(domain_id))
    wrong_domain[-1] = replace(wrong_domain[-1], domain_id="R4-RETAIL")
    duplicate = list(_addresses(domain_id))
    duplicate[-1] = duplicate[-2]
    cross_case = list(_addresses(domain_id))
    cross_case[-1] = replace(cross_case[-1], case_id="CASE-OTHER")
    reversed_order = tuple(reversed(_addresses(domain_id)))

    for roster, message in (
        (tuple(wrong_domain), "mapped registry domain"),
        (tuple(duplicate), "duplicates"),
        (tuple(cross_case), "more than one"),
        (reversed_order, "canonical"),
    ):
        with pytest.raises(contract.BaselineAdapterContractError, match=message):
            contract.make_baseline_adapter_contract(
                method_id=declaration.method_id,
                registry_domain_id=domain_id,
                config_sha256=declaration.config_sha256,
                capability_declarations=declaration.capability_declarations,
                address_roster=roster,
            )


def test_case_requires_exact_f105_target_and_draw_configurations() -> None:
    domain_id = registry.PHYSIONET_DOMAIN_ID
    frozen = _frozen_contract(domain_id)
    target = _empty_configuration(domain_id)

    with pytest.raises(TypeError, match="ExactConfiguration"):
        contract.validate_baseline_adapter_case(frozen, object(), _draws(domain_id))
    with pytest.raises(contract.BaselineAdapterContractError, match="target domain"):
        contract.validate_baseline_adapter_case(
            frozen, retail_configuration(()), _draws(domain_id)
        )
    with pytest.raises(TypeError, match="materialized draw"):
        contract.validate_baseline_adapter_case(
            frozen, target, _draws(domain_id, configuration=object())
        )
    with pytest.raises(contract.BaselineAdapterContractError, match="another F105"):
        contract.validate_baseline_adapter_case(
            frozen,
            target,
            _draws(domain_id, configuration=retail_configuration(())),
        )


def test_case_requires_the_contracts_exact_draw_order() -> None:
    domain_id = registry.PHYSIONET_DOMAIN_ID
    frozen = _frozen_contract(domain_id)
    target = _empty_configuration(domain_id)
    draws = list(_draws(domain_id))
    draws[0], draws[1] = draws[1], draws[0]
    with pytest.raises(contract.BaselineAdapterContractError, match="exact ordered"):
        contract.validate_baseline_adapter_case(frozen, target, tuple(draws))


@pytest.mark.parametrize("count", [0, 1, 63, 65, 128])
def test_case_refuses_every_non_r64_materialized_draw_count(count: int) -> None:
    domain_id = registry.PHYSIONET_DOMAIN_ID
    frozen = _frozen_contract(domain_id)
    with pytest.raises(contract.BaselineAdapterContractError, match="R64"):
        contract.validate_baseline_adapter_case(
            frozen,
            _empty_configuration(domain_id),
            _draws(domain_id, count=count),
        )


def test_contract_explicitly_preserves_b12_and_has_no_runtime_surface() -> None:
    assert contract.ADAPTER_CONTRACT_STATE.endswith("VALIDATION_ONLY")
    assert contract.B12_EXECUTION_BOUNDARY == (
        "ACTUAL_EXTERNAL_PACKAGE_EXECUTION_MODEL_TRANSFORMATION_AND_END_TO_END_"
        "QUALIFICATION_REMAIN_B12"
    )
    source = (
        ROOT
        / "src/heterodiff/experiments/two_domain_baseline_adapter_contract.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "import os",
        "import random",
        "import secrets",
        "import socket",
        "import subprocess",
        "import requests",
        "urllib",
        "open(",
        "Path(",
        "numpy",
        "scipy",
        "torch",
        "jax",
        "importlib",
    )
    assert not any(token in source for token in forbidden)
