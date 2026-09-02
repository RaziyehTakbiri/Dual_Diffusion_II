"""Hostile qualification for the all-or-nothing B05 F007--F018 freeze."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / (
    "research/diagnostics/"
    "manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py"
)
VALIDATOR_SHA256 = "d53a5656e4322e5b169bd859af531ea208ccaf413ddd9660a31c350d93cc2eb2"
SOURCE_PATH = ROOT / (
    "src/heterodiff/evaluation/"
    "mixed_marked_ctmc_ou_known_law_certified_reference.py"
)
SOURCE_SHA256 = "98ffb1f42bee3efc097f378cc55a00b88f2d8570b9f3e8de1fe5f9a727f2e268"


def _load_verified_module(path: Path, digest: str, name: str) -> ModuleType:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = None
    exec(compile(raw, str(path), "exec", dont_inherit=True, optimize=0), module.__dict__)
    return module


@pytest.fixture(scope="session")
def validator() -> ModuleType:
    return _load_verified_module(VALIDATOR_PATH, VALIDATOR_SHA256, "_b05_validator")


@pytest.fixture(scope="session")
def expected(validator: ModuleType) -> dict:
    return validator.expected_record(ROOT)


@pytest.fixture(scope="session")
def reference_source() -> ModuleType:
    return _load_verified_module(SOURCE_PATH, SOURCE_SHA256, "_b05_reference")


@pytest.fixture(scope="session")
def reference_tables(reference_source: ModuleType) -> dict:
    return reference_source.build_reference_tables()


def _redigest(validator: ModuleType, record: dict) -> dict:
    record["record_sha256"] = validator.record_sha256(record)
    return record


def _field(record: dict, field_id: str) -> dict:
    matches = [item for item in record["field_closures"] if item["field_id"] == field_id]
    assert len(matches) == 1
    return matches[0]


def _set_first_key(value, key: str, replacement) -> bool:
    if type(value) is dict:
        if key in value:
            value[key] = replacement
            return True
        return any(_set_first_key(item, key, replacement) for item in value.values())
    if type(value) is list:
        return any(_set_first_key(item, key, replacement) for item in value)
    return False


def _fraction(text: str) -> Fraction:
    numerator, denominator = text.split("/", 1)
    return Fraction(int(numerator), int(denominator))


def _interval(record: dict) -> tuple[Fraction, Fraction]:
    assert set(record) == {"lower", "upper", "width"}
    lower = _fraction(record["lower"])
    upper = _fraction(record["upper"])
    assert upper - lower == _fraction(record["width"])
    return lower, upper


def _sum_intervals(values) -> tuple[Fraction, Fraction]:
    values = list(values)
    return sum((value[0] for value in values), Fraction(0)), sum(
        (value[1] for value in values), Fraction(0)
    )


def _validate_route_receipt(route: dict) -> None:
    approximation = _interval(route["simpson_approximation_enclosure"])
    jet_four = _interval(route["fourth_taylor_coefficient_enclosure"])
    maximum = max(abs(jet_four[0]), abs(jet_four[1]))
    derivative_bound = Fraction(24) * maximum
    assert _fraction(route["fourth_derivative_bound"]) == derivative_bound
    step = _fraction(route["step"])
    assert step == Fraction(1, route["subinterval_count"])
    remainder = step**4 * derivative_bound / 180
    assert _fraction(route["remainder_upper"]) == remainder
    unclamped = (approximation[0] - remainder, approximation[1] + remainder)
    assert _interval(route["unclamped_final_enclosure"]) == unclamped
    final = (max(Fraction(0), unclamped[0]), unclamped[1])
    assert _interval(route["final_nonnegative_enclosure"]) == final
    weight = _fraction(route["target_occupation_rate_weight"])
    contribution = (final[0] * weight, final[1] * weight)
    assert _interval(route["weighted_component_contribution"]) == contribution
    assert route["receipt_values_derived_topologically_from_serialized_parents"] is True
    assert route["adaptive_quadrature_estimate_used"] is False


def test_exact_machine_record_and_all_or_nothing_state(
    validator: ModuleType, expected: dict
) -> None:
    raw = (ROOT / validator.MACHINE_PATH).read_bytes()
    actual = validator._parse_json(raw, "machine")
    assert raw == validator.canonical_machine_bytes(actual)
    validator._validate_against_expected(actual, expected)
    assert [item["field_id"] for item in actual["field_closures"]] == [
        "F007", "F008", "F009", "F010", "F011", "F012",
        "F013", "F014", "F015", "F016", "F017", "F018",
    ]
    assert actual["all_or_nothing_closure"]["partial_credit_permitted"] is False
    assert actual["count_transition"]["before"]["total_open"] == 164
    assert actual["count_transition"]["after"]["total_open"] == 152
    assert actual["count_transition"]["after"]["total_closed"] == 20
    assert actual["project_effects_and_nonclaims"]["B05_remains_open"] is True
    assert actual["project_effects_and_nonclaims"]["formal_test_28_status"] == "OPEN"
    assert actual["project_effects_and_nonclaims"]["formal_test_29_status"] == "OPEN"
    assert actual["project_effects_and_nonclaims"]["formal_test_30_status"] == "PENDING"


def test_source_certificate_grid_and_three_budget_roles(expected: dict) -> None:
    certificate = expected["known_law_certificate"]
    assert certificate["certificate_sha256"] == (
        "e202379f735e76dc43105cff62e4ff443a97ff810d89edecaf8091e5eefe187d"
    )
    assert certificate["grid"]["path_quadrature_grid"]["subinterval_count"] == 1024
    assert certificate["grid"]["path_quadrature_grid"]["node_count"] == 1025
    assert certificate["grid"]["table_counts"]["total_bound_union_cells"] == 1392
    assert certificate["reference_summary"]["all_reference_precision_budgets_pass"] is True
    assert certificate["reference_summary"][
        "reference_precision_is_distinct_from_scientific_error_and_candidate_enclosure_width"
    ] is True
    assert expected["exact_self_reference_qualification"]["validation"] == "PASS"


def test_f007_roster_f008_literal_projection_and_f018_formula(expected: dict) -> None:
    f007 = _field(expected, "F007")["value"]
    assert [item["bucket_id"] for item in f007["ordered_nonoverlapping_error_bucket_roster"]] == [
        "TARGET_REFERENCE_MISMATCH", "ANALYTIC_GUIDE_APPROXIMATION",
        "RESIDUAL_ESTIMATION", "CAP_RESTRICTION_OR_DEFECT", "INITIALIZATION",
        "TERMINAL_REFERENCE", "NUMERICAL",
    ]
    assert f007["cap_defect_is_sixth_kl_term"] is False
    assert f007["association_guide_error_owned_inside_bucket_2_exactly_once"] is True
    f008 = _field(expected, "F008")["value"]
    assert f008["literal_table_row_count"] == 11
    assert f008["canonical_decision_row_count"] == 12
    assert f008["solver_controls_are_thresholds"] is False
    f018 = _field(expected, "F018")["value"]
    assert f018["required_components"] == [
        "K0", "KC", "K_BIRTH", "K_DEATH", "K_REPLACEMENT"
    ]
    assert f018["jump_increment_orientation"] == "DELTA_E=E(DESTINATION)-E(SOURCE)"
    assert f018["cap_defect_component_permitted"] is False


def test_composite_fixture_has_disjoint_cap2_witnesses(expected: dict) -> None:
    f009 = _field(expected, "F009")["value"]
    assert f009["caps"] == [1, 2]
    perturbation = f009["nonzero_reference_perturbation"]
    assert perturbation["mode_constants_empty_alpha_beta"] == ["0/1", "1/5", "-1/4"]
    assert perturbation["mark_slope"] == "1/3"
    assert perturbation["candidate_pass_value"] is False
    cap2 = f009["cap2_structural_witness"]
    assert cap2["three_subcases_are_disjoint_and_not_cross_substituted"] is True
    assert cap2[
        "borrowing_flux_factorial_rn_or_association_facts_across_subcase_measures_permitted"
    ] is False
    assert cap2["subcase_B_continuous_nonunit_rn_route_sum"][
        "reverse_deterministic_mark_map"
    ] == "X=Y/2"
    assert cap2["subcase_C_distinct_mark_association_permanent"][
        "bijection_count"
    ] == 2
    assert cap2["cap_boundary_attempted_birth"][
        "legal_cap2_outward_birth_flux_by_type"
    ] == {"ALPHA": "0/1", "BETA": "0/1"}


def test_reference_route_receipts_are_topologically_recomputable(reference_tables: dict) -> None:
    witness = reference_tables["nonzero_residual_path_witness"]
    routes = witness["ordered_six_route_quadrature_certificates"]
    assert [(row["family"], row["source"], row["destination"]) for row in routes] == [
        ("BIRTH", "EMPTY", "ALPHA"),
        ("BIRTH", "EMPTY", "BETA"),
        ("DEATH", "ALPHA", "EMPTY"),
        ("DEATH", "BETA", "EMPTY"),
        ("REPLACEMENT", "ALPHA", "BETA"),
        ("REPLACEMENT", "BETA", "ALPHA"),
    ]
    for route in routes:
        _validate_route_receipt(route)
    components = witness["components"]
    for family, component in (
        ("BIRTH", "birth"), ("DEATH", "death"), ("REPLACEMENT", "replacement")
    ):
        route_sum = _sum_intervals(
            _interval(row["weighted_component_contribution"])
            for row in routes if row["family"] == family
        )
        assert _interval(components[component]) == route_sum
    required = ["initializer", "continuous", "birth", "death", "replacement"]
    assert all(_interval(components[name])[0] >= 0 for name in required)
    assert _interval(components["total"]) == _sum_intervals(
        _interval(components[name]) for name in required
    )
    assert _interval(components["dynamic"]) == _sum_intervals(
        _interval(components[name])
        for name in ("continuous", "birth", "death", "replacement")
    )


@pytest.mark.parametrize(
    "key",
    [
        "simpson_approximation_enclosure",
        "fourth_taylor_coefficient_enclosure",
        "fourth_derivative_bound",
        "remainder_upper",
        "unclamped_final_enclosure",
        "final_nonnegative_enclosure",
        "target_occupation_rate_weight",
        "weighted_component_contribution",
    ],
)
def test_hostile_route_receipt_parent_or_child_mutation_fails(
    reference_tables: dict, key: str
) -> None:
    route = deepcopy(
        reference_tables["nonzero_residual_path_witness"]
        ["ordered_six_route_quadrature_certificates"][0]
    )
    if type(route[key]) is dict:
        route[key]["upper"] = str(_fraction(route[key]["upper"]) + Fraction(1, 10**30))
        route[key]["width"] = str(
            _fraction(route[key]["upper"]) - _fraction(route[key]["lower"])
        )
    else:
        route[key] = "1/1"
    with pytest.raises(AssertionError):
        _validate_route_receipt(route)


def test_source_authority_is_immutable_and_cache_poisoning_is_rejected(
    validator: ModuleType, reference_source: ModuleType, expected: dict
) -> None:
    with pytest.raises(TypeError):
        reference_source.SCIENTIFIC_THRESHOLDS["F018_PATH_KL"] = Fraction(1)
    with pytest.raises(TypeError):
        reference_source.NUMERICAL_WIDTH_BUDGETS["F018_PATH_KL"] = Fraction(1)
    with pytest.raises(TypeError):
        reference_source.REFERENCE_WIDTH_BUDGETS["F018_PATH_COMPONENT_REFERENCE"] = Fraction(1)
    with pytest.raises(TypeError):
        reference_source.CAP2_STRUCTURAL_INVARIANTS["factorial_two"] = Fraction(3)
    with pytest.raises(TypeError):
        reference_source.A1_SECTION_7_3[0]["threshold"] = "1/1"
    assert not hasattr(reference_source, "_TRANSITION_CACHE")
    assert not hasattr(reference_source, "_MARK_COEFFICIENT_CACHE")
    reference_source._MARK_COEFFICIENT_CACHE = {Fraction(0): "POISON"}
    with pytest.raises(validator.ValidationError, match="cache"):
        validator._validate_certificate_semantics(
            reference_source, expected["known_law_certificate"]
        )
    del reference_source._MARK_COEFFICIENT_CACHE


def test_builder_fails_closed_on_coherent_computation_drift(reference_source: ModuleType) -> None:
    original_tables = reference_source.build_reference_tables
    original_summary = reference_source._reference_summary
    try:
        reference_source.build_reference_tables = lambda: {"coherent_hostile": True}
        reference_source._reference_summary = lambda _tables: {"coherent_hostile": True}
        with pytest.raises(reference_source.CertificationError, match="frozen digest"):
            reference_source.build_certificate()
    finally:
        reference_source.build_reference_tables = original_tables
        reference_source._reference_summary = original_summary


def test_duplicate_source_dict_key_and_forbidden_import_fail(validator: ModuleType) -> None:
    with pytest.raises(validator.ValidationError, match="duplicate"):
        validator._source_ast_safety(b'X={"continuous":1,"continuous":2}\n')
    with pytest.raises(validator.ValidationError, match="import"):
        validator._source_ast_safety(b"import scipy\n")


@pytest.mark.parametrize(
    "hostile",
    [
        "partial_11_of_12",
        "reverse_kl",
        "sixth_cap_component",
        "reference_output_as_threshold",
        "simpson_grid_loosened",
        "birth_coordinate_swapped",
        "factorial_broken",
        "association_term_omitted",
        "blocked_alpha_legalized",
        "blocked_beta_legalized",
        "rn_inverted",
        "reverse_kernel_noninverse",
        "nuisance_time_dependent",
        "calibration_omitted",
        "wide_error_with_tiny_width",
        "path_total_independent",
        "scipy_claimed_certified",
        "f148_conflated_with_v4",
        "formal_test_30_open_instead_of_pending",
    ],
)
def test_coherently_redigested_semantic_hostiles_fail(
    validator: ModuleType, expected: dict, hostile: str
) -> None:
    record = deepcopy(expected)
    if hostile == "partial_11_of_12":
        record["field_closures"].pop()
        record["all_or_nothing_closure"]["closed_count"] = 11
        record["all_or_nothing_closure"]["closed_field_ids"].pop()
    elif hostile == "reverse_kl":
        record["known_law_certificate"]["orientation"] = "KL(P_CANDIDATE||P_EXACT)"
    elif hostile == "sixth_cap_component":
        _field(record, "F018")["value"]["required_components"].append("K_CAP")
    elif hostile == "reference_output_as_threshold":
        _field(record, "F018")["value"]["metric"]["scientific_error_threshold"] = "226/1000"
    elif hostile == "simpson_grid_loosened":
        _field(record, "F010")["value"]["path_quadrature_grid"]["subinterval_count"] = 256
    elif hostile == "birth_coordinate_swapped":
        _field(record, "F013")["value"]["coordinate_role"] = "REMOVED_SOURCE_MARK"
    elif hostile == "factorial_broken":
        assert _set_first_key(_field(record, "F009")["value"], "orbit_multiplicity", 3)
    elif hostile == "association_term_omitted":
        assert _set_first_key(_field(record, "F009")["value"], "bijection_count", 1)
    elif hostile == "blocked_alpha_legalized":
        record["exact_self_reference_candidate"]["cap2_blocked_alpha_birth_checked"] = False
    elif hostile == "blocked_beta_legalized":
        record["exact_self_reference_candidate"]["cap2_blocked_beta_birth_checked"] = False
    elif hostile == "rn_inverted":
        assert _set_first_key(_field(record, "F009")["value"], "pushforward_rn_wrt_destination_measure", "2*EXP(-3*Y^2/8)")
    elif hostile == "reverse_kernel_noninverse":
        assert _set_first_key(_field(record, "F009")["value"], "reverse_deterministic_mark_map", "X=Y")
    elif hostile == "nuisance_time_dependent":
        _field(record, "F009")["value"]["classifier_nuisance_identity"]["forbidden_process_inputs"] = ["Y"]
    elif hostile == "calibration_omitted":
        record["exact_self_reference_candidate"]["equal_prior_calibration_all_cells_checked"] = False
    elif hostile == "wide_error_with_tiny_width":
        record["exact_self_reference_candidate"]["errors"]["F018_PATH_KL"] = {
            "lower": "1/1", "upper": "1/1"
        }
    elif hostile == "path_total_independent":
        record["exact_self_reference_candidate"]["path_components"]["TOTAL"] = {
            "lower": "0/1", "upper": "1/100000000"
        }
    elif hostile == "scipy_claimed_certified":
        record["known_law_certificate"]["arithmetic"]["binary64_crosscheck_used_as_bound"] = True
    elif hostile == "f148_conflated_with_v4":
        record["project_effects_and_nonclaims"]["F148_prior_separate_closure_preserved"] = "V4_TERMINAL_PASS"
    elif hostile == "formal_test_30_open_instead_of_pending":
        record["project_effects_and_nonclaims"]["formal_test_30_status"] = "OPEN"
    else:
        raise AssertionError(hostile)
    _redigest(validator, record)
    with pytest.raises(validator.ValidationError):
        validator._validate_against_expected(record, expected)


def test_machine_duplicate_key_noncanonical_and_self_digest_hostiles(
    validator: ModuleType, expected: dict
) -> None:
    canonical = validator.canonical_machine_bytes(expected)
    text = canonical.decode("ascii")
    duplicate = text.replace(
        '{"all_or_nothing_closure":',
        '{"schema_version":"DUPLICATE","all_or_nothing_closure":',
        1,
    )
    with pytest.raises(validator.ValidationError, match="duplicate"):
        validator._parse_json(duplicate.encode("ascii"), "duplicate")
    noncanonical = json.dumps(expected, indent=2, sort_keys=False).encode("ascii") + b"\n"
    parsed = validator._parse_json(noncanonical, "noncanonical")
    assert noncanonical != validator.canonical_machine_bytes(parsed)
    corrupt = deepcopy(expected)
    corrupt["record_sha256"] = "0" * 64
    with pytest.raises(validator.ValidationError, match="self-digest"):
        validator._validate_against_expected(corrupt, expected)


def test_no_new_package_bytecode_and_no_global_cache_absence_claim() -> None:
    forbidden = []
    for directory in (
        ROOT / "src/heterodiff/evaluation/__pycache__",
        ROOT / "research/diagnostics/__pycache__",
        ROOT / "tests/unit/__pycache__",
    ):
        if directory.exists():
            forbidden.extend(
                path for path in directory.iterdir()
                if "mixed_marked_ctmc_ou_known_law_certified_reference" in path.name
                or "manuscript_v3_gate_a_b05_known_law_design_freeze_v1" in path.name
            )
    assert forbidden == []
    # The workspace may already contain an unrelated .pytest_cache.  The
    # qualification command disables pytest's cache provider and makes no
    # global cache-absence claim.
