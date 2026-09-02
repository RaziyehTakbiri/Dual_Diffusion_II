"""Dormant child-side projection and bootstrap protocol for A1 R1.

The module never imports the legacy project package or the parent authority,
never writes a ledger, and never launches a child.  It only projects already
validated successor requests into inert legacy-request field tuples.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from research.production import (
    finite_association_r1_successor_contracts_v1 as contracts,
)


DIRECT_FILE_ADAPTER_RELATIVE_PATH = (
    "research/production/finite_association_r1_successor_adapter_v1.py"
)
PERMANENTLY_ABSENT_LEGACY_PLANNED_SRC_TARGET = (
    "src/heterodiff/experiments/finite_association_registry_aware_capsule_v1.py"
)
FUTURE_CAPSULE_ADAPTER_COPY_PATH = (
    "protocol/research/production/finite_association_r1_successor_adapter_v1.py"
)
FUTURE_CAPSULE_CONTRACTS_COPY_PATH = (
    "protocol/research/production/finite_association_r1_successor_contracts_v1.py"
)
FUTURE_CAPSULE_BOOTSTRAP_SPEC_COPY_PATH = "protocol/adapter-bootstrap-spec.json"

ADAPTER_PROTOCOL_FROZEN = True
ADAPTER_IMPLEMENTED = False
AUTHORITY_IMPORTED_BY_CHILD = False
LEGACY_PROJECT_IMPORTED_BY_CHILD = False
CHILD_LEDGER_WRITE_IMPLEMENTED = False
CHILD_LAUNCH_IMPLEMENTED = False


@dataclass(frozen=True)
class LegacyCoordinateProjectionV1:
    """Inert field projection; not a legacy request object or launch capability."""

    phase: str
    phase_coordinate_ordinal: int
    legacy_request_type: str
    positional_fields: Tuple[Any, ...]
    authority_admission_bound: bool = False
    permit_admission_bound: bool = False
    legacy_object_constructed: bool = False
    launch_capability_present: bool = False

    def __post_init__(self) -> None:
        if self.phase not in contracts.COORDINATE_PHASES:
            raise contracts.ContractError("projection phase is not frozen")
        if type(self.phase_coordinate_ordinal) is not int:
            raise contracts.ContractError("projection ordinal has the wrong type")
        if type(self.legacy_request_type) is not str or not self.legacy_request_type:
            raise contracts.ContractError("projection request type is not frozen")
        if type(self.positional_fields) is not tuple:
            raise contracts.ContractError("projection fields have the wrong type")
        for name in (
            "authority_admission_bound",
            "permit_admission_bound",
            "legacy_object_constructed",
            "launch_capability_present",
        ):
            if getattr(self, name) is not False:
                raise contracts.ContractError(
                    "parser-only projection gained capability"
                )


@dataclass(frozen=True)
class RankPathProjectionV1:
    """Inert rank path projection; not a subprocess request."""

    destination_relative_path: str
    raw_result_relative_path: str
    prepared_custody_relative_path: str
    parent_exit_relative_path: str
    launch_capability_present: bool = False

    def __post_init__(self) -> None:
        for name in (
            "destination_relative_path",
            "raw_result_relative_path",
            "prepared_custody_relative_path",
            "parent_exit_relative_path",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value or value.startswith("/"):
                raise contracts.ContractError("rank projection path is not relative")
        if self.launch_capability_present is not False:
            raise contracts.ContractError(
                "rank projection cannot carry launch capability"
            )


def project_syntax_validated_coordinate_request(
    request: contracts.CoordinateRequestV1,
) -> LegacyCoordinateProjectionV1:
    """Project parser-only fields without authority or permit admission."""

    if type(request) is not contracts.CoordinateRequestV1:
        raise contracts.ContractError("coordinate request has the wrong exact type")
    record = request.to_record()
    tagged = record["tagged_coordinate"]
    projection = tuple(record["legacy_request_projection"])
    expected = (
        (tagged["seed"], tagged["method"])
        if record["phase"] == "EXACT"
        else (tagged["seed"], tagged["accepted_example_budget"], tagged["method"])
    )
    if projection != expected:
        raise contracts.ContractError("legacy request projection changed semantics")
    expected_type = (
        "FrozenExactPopulationRunRequest"
        if record["phase"] == "EXACT"
        else "FrozenAssociationSampledRunRequest"
    )
    if record["legacy_request_type"] != expected_type:
        raise contracts.ContractError("legacy request type changed")
    return LegacyCoordinateProjectionV1(
        phase=record["phase"],
        phase_coordinate_ordinal=record["phase_coordinate_ordinal"],
        legacy_request_type=expected_type,
        positional_fields=projection,
    )


def project_rank_request(request: contracts.RankRequestV1) -> RankPathProjectionV1:
    """Project rank custody paths without importing or invoking its launcher."""

    if type(request) is not contracts.RankRequestV1:
        raise contracts.ContractError("rank request has the wrong exact type")
    record = request.to_record()
    return RankPathProjectionV1(
        destination_relative_path=record["destination_relative_path"],
        raw_result_relative_path=record["raw_result_relative_path"],
        prepared_custody_relative_path=record["prepared_custody_relative_path"],
        parent_exit_relative_path=record["parent_exit_relative_path"],
    )


def frozen_bootstrap_spec() -> Dict[str, Any]:
    """Return the frozen future child bootstrap record; perform no bootstrap."""

    record = {
        "schema": contracts.ADAPTER_BOOTSTRAP_SPEC_SCHEMA,
        "interpreter_relative_path": contracts.BOOTSTRAP_INTERPRETER_RELATIVE_PATH,
        "interpreter_flags": list(contracts.BOOTSTRAP_INTERPRETER_FLAGS),
        "environment": dict(contracts.BOOTSTRAP_ENVIRONMENT),
        "environment_mode": "EXACT_REPLACEMENT_ALLOWLIST",
        "environment_inheritance_permitted": False,
        "forbidden_inherited_environment_keys": list(
            contracts.BOOTSTRAP_FORBIDDEN_INHERITED_ENVIRONMENT_KEYS
        ),
        "sys_path_order": list(contracts.BOOTSTRAP_SYS_PATH_ORDER),
        "pth_processing_permitted": False,
        "verify_every_file_hash": True,
        "verify_imported_module_file": True,
        "legacy_project_import_permitted": False,
        "bootstrap_spec_sha256": None,
    }
    record["bootstrap_spec_sha256"] = contracts.sha256_bytes(
        contracts.ADAPTER_BOOTSTRAP_SPEC_SCHEMA.encode("ascii")
        + b"\0"
        + contracts.canonical_json(record)
    )
    parsed = contracts.AdapterBootstrapSpecV1.parse(
        contracts.canonical_json(record) + b"\n"
    )
    return parsed.to_record()


def protocol_status() -> Dict[str, Any]:
    """Return zero-execution protocol facts without touching the filesystem."""

    return {
        "adapter_protocol_frozen": True,
        "adapter_implemented": False,
        "direct_file_adapter_is_authoritative_future_protocol": True,
        "legacy_planned_src_target_must_remain_permanently_absent": True,
        "parser_only_projection_is_not_authority_qualification": True,
        "future_child_requires_authority_admission_and_permit_before_legacy_construction": True,
        "authority_imported_by_child": False,
        "legacy_project_imported_by_child": False,
        "child_ledger_write_implemented": False,
        "child_launch_implemented": False,
        "bootstrap_environment_replaces_inherited_environment": True,
        "inherited_pythonhome_or_pythonpath_permitted": False,
        "bootstrap_spec": frozen_bootstrap_spec(),
    }


__all__ = [
    "ADAPTER_IMPLEMENTED",
    "ADAPTER_PROTOCOL_FROZEN",
    "DIRECT_FILE_ADAPTER_RELATIVE_PATH",
    "FUTURE_CAPSULE_ADAPTER_COPY_PATH",
    "FUTURE_CAPSULE_BOOTSTRAP_SPEC_COPY_PATH",
    "FUTURE_CAPSULE_CONTRACTS_COPY_PATH",
    "LegacyCoordinateProjectionV1",
    "PERMANENTLY_ABSENT_LEGACY_PLANNED_SRC_TARGET",
    "RankPathProjectionV1",
    "frozen_bootstrap_spec",
    "project_syntax_validated_coordinate_request",
    "project_rank_request",
    "protocol_status",
]
