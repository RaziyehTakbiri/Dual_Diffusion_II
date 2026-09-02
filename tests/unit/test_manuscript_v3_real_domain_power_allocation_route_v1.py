"""Hostile tests for the static real-domain power/allocation route.

All mutation is confined to pytest temporary directories.  The canonical
package and its immutable predecessors are read only.  These tests do not
import project science, contact a source, use a network, inspect data, draw
entropy, or execute a scientific workload.
"""

from __future__ import annotations

import ast
from decimal import Decimal, localcontext
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, List

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json"
)
AUTHORITY_TEXT = "Alright, sounds good. Go ahead then."


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "real_domain_power_allocation_route_validator", ROOT / VALIDATOR_REL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _closed_roster(module: ModuleType) -> List[str]:
    return [
        module.HUMAN_PATH,
        module.MACHINE_PATH,
        module.VALIDATOR_PATH,
        module.TEST_PATH,
        *[row["path"] for row in module.LIVE_IMMUTABLE_BINDINGS],
    ]


def _copy_closed_roster(module: ModuleType, tmp_path: Path) -> Path:
    for relative in _closed_roster(module):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = module.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _replace(record: Dict[str, Any], pointer: str, value: Any) -> None:
    current: Any = record
    tokens = pointer.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def test_canonical_route_validates_with_exact_nonclosure(
    validator: ModuleType,
) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": (
            "REAL_DOMAIN_POWER_ALLOCATION_ROUTE_FROZEN_AND_SYNTHETICALLY_"
            "QUALIFIED_AWAITING_METRIC_MARGIN_PILOT_AND_COMPUTE"
        ),
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": "POWER_AND_ALLOCATION_ROUTE_DEPENDENCY_AUDIT_VALIDATED",
        "control_predicate_value": True,
        "synthetic_certified_seed_count": 241,
        "B07_open": True,
        "F060_open": True,
        "F061_open": True,
        "F110_open": True,
        "F128_through_F138_open_count": 11,
        "candidate_alpha_and_power_only": True,
        "scientific_effect": 0,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_exact_calculator_synthetic_vector_has_no_float(
    validator: ModuleType,
) -> None:
    result = validator.certified_seed_count(
        Fraction(6), Fraction(1, 40), Fraction(1, 20), Fraction(0), Fraction(1)
    )
    assert result["certified_seed_count"] == 241
    assert result["certificate_status"] == "EXACT_CONSERVATIVE_UPPER_BOUND"
    assert result["log_series_terms"] == 64
    upper = result["conservative_rational_upper"]
    rational = Fraction(upper["numerator"], upper["denominator"])
    assert 240 < rational < 241

    def assert_no_float(value: Any) -> None:
        assert type(value) is not float
        if type(value) is dict:
            for child in value.values():
                assert_no_float(child)
        elif type(value) is list:
            for child in value:
                assert_no_float(child)

    assert_no_float(result)


def test_exact_calculator_component_bit_bound_is_inclusive_and_normalized(
    validator: ModuleType,
) -> None:
    boundary = 1 << (validator.MAX_RATIONAL_COMPONENT_BITS - 1)
    assert validator._exact_fraction(boundary, "boundary") == Fraction(boundary, 1)
    assert validator._exact_fraction(Fraction(1, boundary), "boundary") == Fraction(
        1, boundary
    )
    normalized = Fraction(boundary * 3, 3)
    assert validator._exact_fraction(normalized, "normalized") == Fraction(boundary, 1)
    over = 1 << validator.MAX_RATIONAL_COMPONENT_BITS
    with pytest.raises(validator.ValidationError, match="rational bit bound"):
        validator._exact_fraction(over, "over numerator")
    with pytest.raises(validator.ValidationError, match="rational bit bound"):
        validator._exact_fraction(Fraction(1, over), "over denominator")


@pytest.mark.parametrize(
    "value",
    [
        Fraction(1, 1),
        Fraction(257, 256),
        Fraction(3, 2),
        Fraction(2, 1),
        Fraction(20, 1),
        Fraction(40, 1),
        Fraction(1 << 100, 1),
        Fraction(1 << 4095, 1),
    ],
)
def test_exact_log_interval_contains_independent_high_precision_value(
    validator: ModuleType, value: Fraction
) -> None:
    lower, upper = validator._log_interval_ge_one(value)
    assert lower <= upper
    with localcontext() as context:
        context.prec = 500
        observed = (
            Decimal(value.numerator) / Decimal(value.denominator)
        ).ln()
        lower_decimal = Decimal(lower.numerator) / Decimal(lower.denominator)
        upper_decimal = Decimal(upper.numerator) / Decimal(upper.denominator)
    assert lower_decimal <= observed <= upper_decimal


def test_conservative_seed_certificate_dominates_target_formula(
    validator: ModuleType,
) -> None:
    result = validator.certified_seed_count(
        Fraction(6), Fraction(1, 40), Fraction(1, 20), Fraction(0), Fraction(1)
    )
    upper = result["conservative_rational_upper"]
    with localcontext() as context:
        context.prec = 200
        rational_upper = Decimal(upper["numerator"]) / Decimal(upper["denominator"])
        target = (
            Decimal(36)
            * (Decimal(40).ln().sqrt() + Decimal(20).ln().sqrt()) ** 2
            / Decimal(2)
        )
    assert target < rational_upper
    assert int(target.to_integral_value(rounding="ROUND_CEILING")) == 240
    assert result["certified_seed_count"] == 241


@pytest.mark.parametrize(
    "arguments",
    [
        (6.0, Fraction(1, 40), Fraction(1, 20), 0, 1),
        (True, Fraction(1, 40), Fraction(1, 20), 0, 1),
        (6, 0, Fraction(1, 20), 0, 1),
        (6, 1, Fraction(1, 20), 0, 1),
        (6, Fraction(1, 40), 0, 0, 1),
        (6, Fraction(1, 40), 1, 0, 1),
        (0, Fraction(1, 40), Fraction(1, 20), 0, 1),
        (6, Fraction(1, 40), Fraction(1, 20), 1, 1),
        (6, Fraction(1, 40), Fraction(1, 20), 2, 1),
        (6, Fraction(1, 40), Fraction(1, 20), "0", 1),
    ],
)
def test_exact_calculator_refuses_invalid_domain(
    validator: ModuleType, arguments: Any
) -> None:
    with pytest.raises(validator.ValidationError):
        validator.certified_seed_count(*arguments)


def test_candidate_family_does_not_close_F128_or_F129(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    dependencies = record["dependency_audit"]
    assert dependencies["F128"] == {
        "status": "OPEN",
        "value": None,
        "candidate_value": {"numerator": 1, "denominator": 20},
        "closed_by_this_package": False,
    }
    assert dependencies["F129"] == {
        "status": "OPEN",
        "value": None,
        "candidate_value": {"numerator": 9, "denominator": 10},
        "closed_by_this_package": False,
    }
    assert record["candidate_family_design"]["planning_alpha_star_per_domain"] == {
        "numerator": 1,
        "denominator": 40,
    }
    assert record["candidate_family_design"]["planning_beta_star_per_domain"] == {
        "numerator": 1,
        "denominator": 20,
    }
    assert record["candidate_family_design"]["candidate_values_close_F128_or_F129"] is False
    assert record["dependency_audit"]["F110"] == {
        "status": "OPEN",
        "value": None,
        "closed_by_this_package": False,
    }
    calculator = record["distribution_free_calculator_contract"]
    assert calculator["normalized_numerator_maximum_bit_length"] == 4096
    assert calculator["normalized_denominator_maximum_bit_length"] == 4096
    assert calculator["component_bit_bound_applied_after_fraction_normalization"] is True
    assert calculator["F110_delta0_value_selected"] is False
    assert calculator["F130_delta1_value_selected"] is False
    family = record["candidate_family_design"]
    assert family["null_margin_delta0"] is None
    assert family["minimum_effect_delta1"] is None
    assert family["delta0_project_field"].startswith("F110_")
    assert family["delta1_project_field"].startswith("F130_")
    assert family["delta1_strictly_greater_than_delta0_required"] is True


def test_every_required_dependency_remains_typed_null_open(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    dependencies = record["dependency_audit"]
    assert dependencies["B07"] == {
        "status": "OPEN",
        "closed_by_this_package": False,
    }
    for field in [
        "F060", "F061", "F110", *["F" + str(i) for i in range(128, 139)]
    ]:
        assert dependencies[field]["status"] == "OPEN"
        assert dependencies[field]["value"] is None
        assert dependencies[field]["closed_by_this_package"] is False
    assert record["scope_and_nonclaims"]["unresolved_fields_closed"] == 0
    assert record["scope_and_nonclaims"]["blockers_closed"] == 0
    assert record["route_identity"]["scientific_effect"] == 0


def test_authority_binds_normalized_visible_text_only(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == AUTHORITY_TEXT
    assert authority["normalized_visible_text_utf8_bytes"] == 36
    assert authority["normalized_visible_text_sha256"] == validator.AUTHORITY_TEXT_SHA256
    assert authority["raw_transport_bytes_bound"] is False
    assert authority["raw_trailing_transport_content_bound"] is False
    assert authority["tracker_edit_authorized"] is False
    assert authority["runtime_or_scientific_execution_authorized"] is False
    assert authority["pilot_execution_authorized"] is False


def test_crossed_pairing_draw_and_simulation_antidrift_contract(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    analysis = record["analysis_contract"]
    assert analysis["training_seed_is_replication_unit"] is True
    assert analysis["conditional_draw_is_independent_replication_unit"] is False
    assert analysis["draws_aggregate_inside_case"] is True
    assert analysis["seed_by_group_cells_treated_as_iid"] is False
    assert analysis["pairing"] == (
        "CROSSED_SEED_BY_NATURAL_GROUP_AND_CASE_WITH_DIRECT_GUIDE_PAIRED_WITHIN_CELL"
    )
    simulation = record["future_simulation_qualification_route"]
    assert simulation["status"] == "FUTURE_ROUTE_ONLY_NOT_EXECUTED"
    assert simulation["grid_fixed_before_simulation"] is True
    assert simulation["grid_expansion_after_results_permitted"] is False
    assert simulation["draws_are_replicates"] is False
    assert simulation[
        "clopper_pearson_requires_within_condition_independent_bernoulli_trials"
    ] is True
    assert simulation["bernoulli_success_indicator_exactly_frozen_before_simulation"] is True
    assert simulation["independence_established_by_distinct_addresses_alone"] is False
    assert simulation["literal_immutable_trial_stream_seed_registry_required"] is True
    assert simulation[
        "trial_registry_pairwise_disjoint_across_grid_condition_and_trial_ordinal"
    ] is True
    assert simulation[
        "trial_registry_disjoint_from_pilot_and_confirmatory_seed_registries"
    ] is True
    assert simulation["trial_registry_custody_required"] is True
    assert simulation["trial_stream_or_seed_reuse_permitted"] is False
    assert simulation[
        "three_named_null_truth_patterns_are_exhaustive_for_composite_null"
    ] is False
    assert simulation["null_configuration_list_semantics"] == (
        "THREE_NAMED_STRUCTURAL_TRUTH_PATTERNS_NOT_COMPOSITE_NULL_EXHAUSTION"
    )
    assert simulation["composite_null_coverage_required_before_execution"] is True
    assert simulation["uncovered_composite_null_disposition"] == "TERMINAL_NO_GO"
    required = simulation["required_before_execution"]
    assert "PROVED_WITHIN_CONDITION_INDEPENDENT_BERNOULLI_TRIAL_LAW" in required
    assert "DISJOINT_IMMUTABLE_TRIAL_STREAM_SEED_REGISTRY_AND_CUSTODY" in required
    assert "COMPOSITE_NULL_COVERAGE_PROOF_OR_FROZEN_NUISANCE_GRID" in required
    assert simulation["multiplicity"] == "EXACT_CONFIRMATORY_HOLM_RULE"
    assert "CLOPPER_PEARSON_UPPER_BOUNDS" in simulation["fwer_acceptance"]
    assert "CLOPPER_PEARSON_LOWER_BOUND" in simulation["power_acceptance"]
    assert simulation["topup_retry_replacement_or_favorable_selection_permitted"] is False
    assert simulation["no_passing_grid_point_disposition"] == (
        "TERMINAL_NO_GO_NEW_PREOUTCOME_VERSION_REQUIRED"
    )


def test_validator_import_boundary_is_static_stdlib_only() -> None:
    tree = ast.parse((ROOT / VALIDATOR_REL).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {
        "__future__", "fractions", "hashlib", "json", "os", "pathlib",
        "stat", "typing",
    }
    banned = {
        "socket", "urllib", "requests", "httpx", "subprocess", "secrets",
        "random", "numpy", "scipy", "torch", "heterodiff",
    }
    assert not (imported & banned)


@pytest.mark.parametrize(
    ("pointer", "value"),
    [
        ("route_identity.scientific_effect", 1),
        ("route_identity.control_predicate", "ANOTHER_PREDICATE"),
        ("authority_provenance.normalized_visible_text", "Go ahead."),
        ("dependency_audit.F128.value", {"numerator": 1, "denominator": 20}),
        ("dependency_audit.F128.status", "CLOSED"),
        ("dependency_audit.F130.value", {"numerator": 1, "denominator": 10}),
        ("dependency_audit.F110.value", {"numerator": 1, "denominator": 100}),
        ("candidate_family_design.candidate_values_close_F128_or_F129", True),
        ("candidate_family_design.null_margin_delta0", {"numerator": 0, "denominator": 1}),
        ("distribution_free_calculator_contract.normalized_numerator_maximum_bit_length", 4095),
        ("distribution_free_calculator_contract.normalized_denominator_maximum_bit_length", 4097),
        ("distribution_free_calculator_contract.F110_delta0_value_selected", True),
        ("distribution_free_calculator_contract.F130_delta1_value_selected", True),
        ("analysis_contract.conditional_draw_is_independent_replication_unit", True),
        ("analysis_contract.seed_by_group_cells_treated_as_iid", True),
        ("future_simulation_qualification_route.grid_expansion_after_results_permitted", True),
        ("future_simulation_qualification_route.clopper_pearson_requires_within_condition_independent_bernoulli_trials", False),
        ("future_simulation_qualification_route.bernoulli_success_indicator_exactly_frozen_before_simulation", False),
        ("future_simulation_qualification_route.independence_established_by_distinct_addresses_alone", True),
        ("future_simulation_qualification_route.literal_immutable_trial_stream_seed_registry_required", False),
        ("future_simulation_qualification_route.trial_registry_pairwise_disjoint_across_grid_condition_and_trial_ordinal", False),
        ("future_simulation_qualification_route.trial_registry_disjoint_from_pilot_and_confirmatory_seed_registries", False),
        ("future_simulation_qualification_route.trial_registry_custody_required", False),
        ("future_simulation_qualification_route.trial_stream_or_seed_reuse_permitted", True),
        ("future_simulation_qualification_route.three_named_null_truth_patterns_are_exhaustive_for_composite_null", True),
        ("future_simulation_qualification_route.composite_null_coverage_required_before_execution", False),
        ("future_simulation_qualification_route.required_before_execution.5", "MISSING_INDEPENDENCE_LAW"),
        ("future_simulation_qualification_route.topup_retry_replacement_or_favorable_selection_permitted", True),
        ("synthetic_qualification.certified_seed_count", 240),
        ("scope_and_nonclaims.tracker_edited", True),
    ],
)
def test_semantic_mutations_fail_even_with_recomputed_digest(
    validator: ModuleType,
    tmp_path: Path,
    pointer: str,
    value: Any,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(validator, root, lambda record: _replace(record, pointer, value))
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_noncanonical_machine_bytes_fail(
    validator: ModuleType,
    tmp_path: Path,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError, match="not canonical"):
        validator.validate(root)


def test_immutable_predecessor_mutation_fails(
    validator: ModuleType,
    tmp_path: Path,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    target = root / validator.PREREG_MACHINE_PATH
    raw = target.read_bytes()
    target.write_bytes(raw[:-1] + b" \n")
    target.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_machine_record_and_validator_schema_match(
    validator: ModuleType,
) -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert record["schema_version"] == validator.SCHEMA
    assert set(record) == validator.EXPECTED_TOP_LEVEL_KEYS
    assert validator.canonical_machine_bytes(record) == raw
    assert record["record_sha256"] == validator.record_sha256(record)
