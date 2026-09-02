"""Hostile qualification for the exact two-domain F105 CKS instance."""

from __future__ import annotations

import ast
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT / "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py"
)
VALIDATOR_PATH = (
    ROOT
    / "research/diagnostics/"
    "manuscript_v3_f105_two_domain_cks_metric_instance_v1.py"
)

SOURCE_SPEC = importlib.util.spec_from_file_location("f105_two_domain_source", SOURCE_PATH)
assert SOURCE_SPEC is not None and SOURCE_SPEC.loader is not None
S = importlib.util.module_from_spec(SOURCE_SPEC)
sys.modules[SOURCE_SPEC.name] = S
SOURCE_SPEC.loader.exec_module(S)


def _phys(time=0, parameter="HR", value="80"):
    return S.physionet_event_from_decimal_token(
        elapsed_minutes=time, parameter=parameter, value_text=value
    )


def _retail(
    *,
    invoice="123456",
    stock="01234",
    description="Widget",
    quantity=2,
    calendar=(2009, 12, 1, 0, 0, 0, 0),
    price="1.25",
    country="United Kingdom",
):
    return S.retail_event_from_decimal_token(
        invoice_no=invoice,
        stock_code=stock,
        description=description,
        quantity=quantity,
        invoice_calendar=calendar,
        unit_price_text=price,
        country=country,
    )


def test_exact_public_constants_and_domain_specs():
    assert S.PRIMARY_METRIC_ID == "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
    assert len(S.PHYSIONET_PARAMETERS) == 37
    assert len(set(S.PHYSIONET_PARAMETERS)) == 37
    assert set(S.PHYSIONET_UNITS) == set(S.PHYSIONET_PARAMETERS)
    assert S.PHYSIONET_HORIZON_MINUTES == 2880
    assert S.PHYSIONET_CONFIGURATION_CAP == 2**17
    assert S.RETAIL_HORIZON_SECONDS == 739 * 24 * 60 * 60
    assert S.RETAIL_HORIZON_MICROSECONDS == 739 * 24 * 60 * 60 * 1_000_000
    assert S.RETAIL_CONFIGURATION_CAP == 1067371
    assert S.PHYSIONET_SPEC.coordinate_dimension == 112
    assert S.RETAIL_SPEC.coordinate_dimension == 10
    for spec in S.DOMAIN_SPECS.values():
        assert spec.event_tau2 == 1
        assert spec.count_scale2 == 1
        assert spec.event_scale2 == 1
        assert spec.outer_sigma2 == 1


def test_physionet_transform_is_type_time_mask_and_value_injective():
    base = _phys()
    changed_type = _phys(parameter="MAP")
    changed_time = _phys(time=1)
    changed_value = _phys(value="81")
    missing = _phys(value="-1")
    present_zero = _phys(value="0")
    assert len({base, changed_type, changed_time, changed_value, missing, present_zero}) == 6
    assert missing.coordinates != present_zero.coordinates
    assert sum(value != 0 for value in missing.coordinates) == 1
    assert sum(value != 0 for value in present_zero.coordinates) == 2


def test_physionet_decimal_source_is_exact_and_binary64_path_is_distinct():
    decimal = _phys(value="0.1")
    binary = S.physionet_event_from_binary64(
        elapsed_minutes=0, parameter="HR", value=0.1
    )
    value_coordinate = 75 + S.PHYSIONET_PARAMETERS.index("HR")
    assert decimal != binary
    assert decimal.coordinates[value_coordinate] == Fraction(1, 11)


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"elapsed_minutes": -1, "parameter": "HR", "value_text": "1"}, ValueError),
        ({"elapsed_minutes": 2881, "parameter": "HR", "value_text": "1"}, ValueError),
        ({"elapsed_minutes": 0, "parameter": "UNKNOWN", "value_text": "1"}, ValueError),
        ({"elapsed_minutes": 0, "parameter": "HR", "value_text": "-2"}, ValueError),
        ({"elapsed_minutes": True, "parameter": "HR", "value_text": "1"}, TypeError),
        ({"elapsed_minutes": 0, "parameter": "HR", "value_text": "1e2"}, ValueError),
    ],
)
def test_physionet_boundary_refuses_invalid_inputs(kwargs, error):
    with pytest.raises(error):
        S.physionet_event_from_decimal_token(**kwargs)


def test_retail_transform_preserves_every_declared_event_component():
    base = _retail()
    variants = (
        _retail(invoice="C123456"),
        _retail(stock="POST"),
        _retail(description=None),
        _retail(description=""),
        _retail(quantity=-2),
        _retail(calendar=(2009, 12, 1, 0, 0, 0, 1)),
        _retail(price="1.26"),
        _retail(country="France"),
        _retail(country=None),
    )
    assert len({base, *variants}) == 1 + len(variants)


def test_retail_token_encoding_has_no_short_length_collision():
    values = ("", "\x01", "\x00\x00", "A", "AA", "AB", "B")
    coordinates = {S._byte_token_coordinate(value) for value in values}
    assert len(coordinates) == len(values)


def test_retail_present_source_tokens_are_not_trimmed_or_normalized():
    base = _retail(description="Widget", country="France")
    whitespace = _retail(description=" Widget\n", country=" France")
    composed = _retail(description="é", country="France")
    decomposed = _retail(description="e\u0301", country="France")
    missing_country = _retail(country=None)
    present_empty_country = _retail(country="")
    assert len(
        {base, whitespace, composed, decomposed, missing_country, present_empty_country}
    ) == 6


def test_retail_cancellation_is_case_insensitive_and_raw_invoice_id_is_state():
    lower = _retail(invoice="c123456")
    upper = _retail(invoice="C654321")
    other_cancel = _retail(invoice="C111111")
    ordinary_a = _retail(invoice="123456")
    ordinary_b = _retail(invoice="654321")
    assert len({lower, upper, other_cancel, ordinary_a, ordinary_b}) == 5
    assert lower.coordinates[1] == upper.coordinates[1] == other_cancel.coordinates[1] == 1
    assert ordinary_a.coordinates[1] == ordinary_b.coordinates[1] == 0
    assert lower != ordinary_a


def test_retail_decimal_source_is_exact_and_binary64_path_is_distinct():
    decimal = _retail(price="0.1")
    binary = S.retail_event_from_binary64(
        invoice_no="123456",
        stock_code="01234",
        description="Widget",
        quantity=2,
        invoice_calendar=(2009, 12, 1, 0, 0, 0, 0),
        unit_price=0.1,
        country="United Kingdom",
    )
    assert decimal != binary
    assert decimal.coordinates[7] == Fraction(1, 11)


def test_retail_source_civil_time_is_exact_and_timezone_agnostic():
    assert S.retail_source_civil_microseconds((2009, 12, 1, 0, 0, 0, 0)) == 0
    assert S.retail_source_civil_microseconds((2009, 12, 1, 0, 0, 0, 1)) == 1
    assert S.retail_source_civil_microseconds(
        (2011, 12, 9, 23, 59, 59, 999999)
    ) == S.RETAIL_HORIZON_MICROSECONDS - 1


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"invoice": "X123456"}, ValueError),
        ({"invoice": "1" * 10000}, ValueError),
        ({"stock": ""}, ValueError),
        ({"quantity": True}, TypeError),
        ({"calendar": (2009, 11, 30, 23, 59, 59, 999999)}, ValueError),
        ({"calendar": (2011, 12, 10, 0, 0, 0, 0)}, ValueError),
        ({"price": "NaN"}, ValueError),
        ({"price": "1" * 257}, ValueError),
        ({"country": "x" * 257}, ValueError),
        ({"description": "x" * 4097}, ValueError),
    ],
)
def test_retail_boundary_refuses_invalid_inputs(kwargs, error):
    with pytest.raises(error):
        _retail(**kwargs)


def test_retail_customer_context_is_exact_and_positive():
    assert S.validate_retail_customer_context(customer_id="12345") == "12345"
    assert S.validate_retail_customer_context(customer_id="1") == "1"
    assert S.retail_customer_key_hex(customer_id="12345") == "3132333435"
    for invalid in ("", "01", "00001", "00000", "123456", "12A45", " 123"):
        with pytest.raises(ValueError):
            S.validate_retail_customer_context(customer_id=invalid)
    with pytest.raises(TypeError):
        S.validate_retail_customer_context(customer_id=12345)


def test_configuration_is_permutation_invariant_and_retains_multiplicity():
    first = _phys(time=1, value="80")
    second = _phys(time=2, value="81")
    left = S.physionet_configuration((first, second, first))
    right = S.physionet_configuration((first, first, second))
    fewer = S.physionet_configuration((first, second))
    assert left == right
    assert len(left.events) == 3
    assert left != fewer
    assert S.configuration_kernel(left, right) == S.ConfigurationKernelSymbol(
        Fraction(0), ()
    )
    assert S.configuration_kernel(left, fewer) != S.ConfigurationKernelSymbol(
        Fraction(0), ()
    )


def test_configuration_kernel_separates_empty_count_and_event_channels():
    empty = S.physionet_configuration(())
    one = S.physionet_configuration((_phys(),))
    two = S.physionet_configuration((_phys(), _phys()))
    changed = S.physionet_configuration((_phys(value="81"),))
    assert S.configuration_kernel(empty, empty) == S.ConfigurationKernelSymbol(
        Fraction(0), ()
    )
    assert S.configuration_kernel(one, two).rational_constant == Fraction(1, 2)
    assert S.configuration_kernel(one, changed).rational_constant == 0
    assert S.configuration_kernel(one, changed).event_exp_terms
    assert S.configuration_kernel(empty, one).event_exp_terms


def test_configuration_kernel_forbids_cross_domain_evaluation():
    phys = S.physionet_configuration((_phys(),))
    retail = S.retail_configuration((_retail(),))
    with pytest.raises(S.CKSInstanceError, match="cross-domain"):
        S.configuration_kernel(phys, retail)


def test_conditional_score_known_identity_and_permutation_invariance():
    first = S.physionet_configuration((_phys(value="80"),))
    second = S.physionet_configuration((_phys(value="81"),))
    identical = S.conditional_cks_score((first, first), first)
    assert identical == S.FormalCKSScore(
        ((S.ConfigurationKernelSymbol(Fraction(0), ()), Fraction(-1)),)
    )
    assert S.conditional_cks_score((first, second), first) == S.conditional_cks_score(
        (second, first), first
    )


@pytest.mark.parametrize("draws", [(), (_phys(),), tuple(_phys() for _ in range(129))])
def test_conditional_score_enforces_exact_draw_domain(draws):
    target = S.physionet_configuration(())
    if draws and type(draws[0]) is S.ExactEvent:
        draws = tuple(S.physionet_configuration((event,)) for event in draws)
    with pytest.raises(S.CKSInstanceError):
        S.conditional_cks_score(draws, target)


def test_cap_and_exact_type_boundaries_fail_closed_without_large_allocations():
    assert S.validate_configuration_count(S.PHYSIONET_DOMAIN_ID, 2**17) == 2**17
    assert S.validate_configuration_count(S.RETAIL_DOMAIN_ID, 1067371) == 1067371
    with pytest.raises(S.CKSInstanceError, match="cap exceeded"):
        S.validate_configuration_count(S.PHYSIONET_DOMAIN_ID, 2**17 + 1)
    with pytest.raises(S.CKSInstanceError, match="cap exceeded"):
        S.validate_configuration_count(S.RETAIL_DOMAIN_ID, 1067372)
    with pytest.raises(TypeError):
        S.validate_configuration_count(S.PHYSIONET_DOMAIN_ID, True)


def test_source_has_no_effectful_import_or_runtime_surface():
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    forbidden = {
        "asyncio",
        "http",
        "multiprocessing",
        "numpy",
        "os",
        "pandas",
        "pathlib",
        "random",
        "requests",
        "secrets",
        "socket",
        "subprocess",
        "urllib",
    }
    assert imported.isdisjoint(forbidden)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert names.isdisjoint({"eval", "exec", "open", "compile", "__import__"})


def _load_validator():
    spec = importlib.util.spec_from_file_location("f105_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _copy_package_tree(tmp_path: Path, validator):
    paths = set(validator.PACKAGE_PATHS)
    paths.update(spec[2] for spec in validator.PREDECESSOR_SPECS)
    for relative in sorted(paths):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        target.chmod(0o644)
    return tmp_path


def _resign(root: Path, validator, record):
    record["record_sha256"] = validator.record_sha256(record)
    (root / validator.MACHINE_PATH).write_bytes(validator.canonical_machine_bytes(record))


def test_package_validator_accepts_only_the_exact_machine_record():
    validator = _load_validator()
    record = validator.validate_package(ROOT)
    assert record["state"] == validator.STATE
    assert len(record["field_closures"]) == 18
    assert record["count_transition"]["after"]["pre_execution_open"] == 122


def test_semantic_mutation_is_rejected_even_after_resigning(tmp_path):
    validator = _load_validator()
    root = _copy_package_tree(tmp_path, validator)
    record = json.loads((root / validator.MACHINE_PATH).read_text(encoding="ascii"))
    record["metric_contract"]["shared_parameters"]["outer_sigma2"] = {
        "numerator": 2,
        "denominator": 1,
    }
    _resign(root, validator, record)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)


def test_false_field_closure_and_count_attack_are_rejected(tmp_path):
    validator = _load_validator()
    root = _copy_package_tree(tmp_path, validator)
    record = json.loads((root / validator.MACHINE_PATH).read_text(encoding="ascii"))
    record["field_closures"].append(
        {
            "field_id": "F109",
            "json_pointer": "/metric_and_estimand_plan/conditional_draws_per_case",
            "status": "CLOSED",
            "value": 2,
        }
    )
    record["count_transition"]["after"]["pre_execution_open"] = 121
    _resign(root, validator, record)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)


def test_f060_utc_repromotion_and_extra_field_are_rejected_after_resigning(tmp_path):
    validator = _load_validator()
    root = _copy_package_tree(tmp_path, validator)
    record = json.loads((root / validator.MACHINE_PATH).read_text(encoding="ascii"))
    correction = record["field_corrections"][0]
    correction["utc_timezone_offset_dst_or_instant_claimed"] = True
    correction["normalized_row_exact_keys"][2] = "timestamp_utc_microseconds"
    record["unauthorized_extra"] = True
    _resign(root, validator, record)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)


def test_bound_source_tamper_and_nonregular_custody_are_rejected(tmp_path):
    validator = _load_validator()
    root = _copy_package_tree(tmp_path, validator)
    source = root / validator.SOURCE_PATH
    source.write_text(source.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)

    root = _copy_package_tree(tmp_path / "symlink", validator)
    human = root / validator.HUMAN_PATH
    original = human.read_bytes()
    human.unlink()
    target = root / "replacement.md"
    target.write_bytes(original)
    target.chmod(0o644)
    human.symlink_to(target)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)

    root = _copy_package_tree(tmp_path / "hardlink", validator)
    human = root / validator.HUMAN_PATH
    os.link(human, root / "second-human-link.md")
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)


def test_bound_f060_predecessor_tamper_is_rejected(tmp_path):
    validator = _load_validator()
    root = _copy_package_tree(tmp_path, validator)
    predecessor = root / "PROJECT_GATE_A_RETAIL_TEMPORAL_RULE_FIELD_FREEZE.md"
    predecessor.write_bytes(predecessor.read_bytes() + b"drift\n")
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)


def test_intermediate_directory_symlink_is_rejected(tmp_path):
    validator = _load_validator()
    root = _copy_package_tree(tmp_path, validator)
    source_tree = root / "src"
    relocated = root / "relocated-src"
    source_tree.rename(relocated)
    source_tree.symlink_to(relocated, target_is_directory=True)
    with pytest.raises(validator.ValidationError):
        validator.validate_package(root)


def test_validator_ast_has_no_writer_network_rng_or_subprocess_surface():
    tree = ast.parse(VALIDATOR_PATH.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported.isdisjoint(
        {"random", "secrets", "socket", "subprocess", "urllib", "requests"}
    )
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert calls.isdisjoint(
        {"write_bytes", "write_text", "unlink", "rename", "replace", "mkdir"}
    )
