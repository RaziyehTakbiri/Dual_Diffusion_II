from __future__ import annotations

from fractions import Fraction
from itertools import product
import inspect
import json
import math
import os
from pathlib import Path
import py_compile
import shutil
import stat
import sys
import types
from typing import Any, Callable, Dict

import pytest


WORKSPACE = Path(__file__).resolve().parents[2]
SOURCE = (
    WORKSPACE
    / "src/heterodiff/evaluation/count_normalized_event_cks_reference.py"
)
VALIDATOR = (
    WORKSPACE
    / "research/diagnostics/"
    "manuscript_v3_cks_count_normalized_event_reference_implementation_v1.py"
)


def _load_module(path: Path, name: str) -> types.ModuleType:
    raw = path.read_bytes()
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    code = compile(raw, str(path), "exec", flags=0, dont_inherit=True, optimize=0)
    prior = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)
    finally:
        if prior is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior
    return module


@pytest.fixture(scope="module")
def reference() -> types.ModuleType:
    return _load_module(SOURCE, "_generic_cks_reference_test_module")


@pytest.fixture(scope="module")
def validator() -> types.ModuleType:
    return _load_module(VALIDATOR, "_generic_cks_reference_validator_test_module")


def _rank_one_spec(reference: types.ModuleType, cap: int = 4) -> Any:
    return reference.FiniteCKSSpec(
        symbols=("u", "v"),
        event_gram=(
            (Fraction(1, 1), Fraction(2, 1)),
            (Fraction(2, 1), Fraction(4, 1)),
        ),
        configuration_cap=cap,
        count_scale_squared=Fraction(1, 1),
        event_scale_squared=Fraction(1, 1),
        outer_bandwidth_squared=Fraction(1, 1),
    )


def _identity_spec(reference: types.ModuleType, cap: int = 8) -> Any:
    return reference.FiniteCKSSpec(
        symbols=("a", "b", "c"),
        event_gram=(
            (Fraction(1), Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(1), Fraction(0)),
            (Fraction(0), Fraction(0), Fraction(1)),
        ),
        configuration_cap=cap,
        count_scale_squared=Fraction(3, 2),
        event_scale_squared=Fraction(5, 3),
        outer_bandwidth_squared=Fraction(7, 4),
    )


def test_singular_rank_one_event_kernel_is_characteristic_on_probabilities(
    reference: types.ModuleType,
) -> None:
    spec = _rank_one_spec(reference)
    assert spec.event_gram[0][1] == Fraction(2, 1)
    assert reference.configuration_distance(spec, ("u",), ("v",)).combined_squared == 1


def test_empty_configuration_totalization(reference: types.ModuleType) -> None:
    spec = _rank_one_spec(reference)
    result = reference.configuration_distance(spec, (), ())
    assert result == reference.DistanceBreakdown(
        left_count=0,
        right_count=0,
        count_channel_squared=Fraction(0, 1),
        event_channel_squared=Fraction(0, 1),
        combined_squared=Fraction(0, 1),
        same_counting_measure=True,
    )
    assert reference.configuration_kernel(spec, (), ()) == reference.GaussianValue(
        exponent=Fraction(0, 1)
    )


def test_empty_nonempty_and_unequal_count_separation(
    reference: types.ModuleType,
) -> None:
    spec = _rank_one_spec(reference)
    empty_nonempty = reference.configuration_distance(spec, (), ("u",))
    assert empty_nonempty.count_channel_squared == 1
    assert empty_nonempty.event_channel_squared == 1
    proportional = reference.configuration_distance(spec, ("u",), ("u", "u"))
    assert proportional.count_channel_squared == 1
    assert proportional.event_channel_squared == 0
    assert proportional.combined_squared == 1


def test_equal_count_multiplicity_separation(reference: types.ModuleType) -> None:
    spec = _rank_one_spec(reference)
    result = reference.configuration_distance(
        spec, ("u", "u", "v"), ("u", "v", "v")
    )
    assert result.count_channel_squared == 0
    assert result.event_channel_squared == Fraction(1, 9)
    assert result.combined_squared == Fraction(1, 9)
    assert result.same_counting_measure is False


def test_permutation_invariance_and_input_preservation(
    reference: types.ModuleType,
) -> None:
    spec = _identity_spec(reference)
    left = ("c", "a", "a", "b")
    right = ("a", "b", "a", "c")
    before = (left, right)
    result = reference.configuration_distance(spec, left, right)
    assert result.combined_squared == 0
    assert result.same_counting_measure is True
    assert (left, right) == before


def test_exhaustive_small_configuration_injection(reference: types.ModuleType) -> None:
    spec = _rank_one_spec(reference)
    configurations = [()]
    for size in range(1, 5):
        configurations.extend(product(("u", "v"), repeat=size))
    for left in configurations:
        for right in configurations:
            result = reference.configuration_distance(spec, left, right)
            same = sorted(left) == sorted(right)
            assert (result.combined_squared == 0) is same
            assert result.same_counting_measure is same


def test_outer_gaussian_exact_symbolic_descriptor(reference: types.ModuleType) -> None:
    spec = _rank_one_spec(reference)
    expected = reference.GaussianValue(exponent=Fraction(1, 2))
    assert reference.configuration_kernel(spec, ("u",), ("v",)) == expected
    assert reference.configuration_kernel(spec, ("v",), ("u",)) == expected


def test_large_outer_gaussian_exponent_remains_exact_symbolic(
    reference: types.ModuleType,
) -> None:
    spec = reference.FiniteCKSSpec(
        symbols=("u",),
        event_gram=((Fraction(0),),),
        configuration_cap=64,
        count_scale_squared=Fraction(1000),
        event_scale_squared=Fraction(1),
        outer_bandwidth_squared=Fraction(1),
    )
    assert reference.configuration_kernel(spec, (), ("u", "u")) == (
        reference.GaussianValue(exponent=Fraction(2000, 1))
    )


@pytest.mark.parametrize(
    "gram,match",
    [
        (((1, 2), (2, 1)), "positive semidefinite"),
        (((1, 1), (1, 1)), "not characteristic"),
        (((1, 0), (1, 1)), "symmetric"),
    ],
)
def test_event_gram_refusals(
    reference: types.ModuleType, gram: Any, match: str
) -> None:
    with pytest.raises(reference.CKSReferenceError, match=match):
        reference.FiniteCKSSpec(
            symbols=("u", "v"),
            event_gram=gram,
            configuration_cap=2,
            count_scale_squared=1,
            event_scale_squared=1,
            outer_bandwidth_squared=1,
        )


@pytest.mark.parametrize(
    "field,value,exception",
    [
        ("symbols", ["u"], TypeError),
        ("symbols", (), Exception),
        ("symbols", ("u", "u"), Exception),
        ("event_gram", [[1]], TypeError),
        ("configuration_cap", True, TypeError),
        ("configuration_cap", 0, Exception),
        ("count_scale_squared", True, TypeError),
        ("count_scale_squared", 0, Exception),
        ("event_scale_squared", 0.5, TypeError),
        ("event_scale_squared", -1, Exception),
        ("outer_bandwidth_squared", 0, Exception),
        ("outer_bandwidth_squared", 1 << 300, Exception),
    ],
)
def test_spec_strict_input_refusals(
    reference: types.ModuleType, field: str, value: Any, exception: type
) -> None:
    kwargs = {
        "symbols": ("u",),
        "event_gram": ((Fraction(1),),),
        "configuration_cap": 2,
        "count_scale_squared": Fraction(1),
        "event_scale_squared": Fraction(1),
        "outer_bandwidth_squared": Fraction(1),
    }
    kwargs[field] = value
    with pytest.raises(exception):
        reference.FiniteCKSSpec(**kwargs)


def test_fraction_and_string_subclasses_refused(reference: types.ModuleType) -> None:
    class FractionSubclass(Fraction):
        pass

    class StringSubclass(str):
        pass

    with pytest.raises(TypeError, match="int or Fraction"):
        reference.FiniteCKSSpec(
            symbols=("u",),
            event_gram=((FractionSubclass(1, 1),),),
            configuration_cap=2,
            count_scale_squared=1,
            event_scale_squared=1,
            outer_bandwidth_squared=1,
        )
    with pytest.raises(TypeError, match="exact nonempty text"):
        reference.FiniteCKSSpec(
            symbols=(StringSubclass("u"),),
            event_gram=((1,),),
            configuration_cap=2,
            count_scale_squared=1,
            event_scale_squared=1,
            outer_bandwidth_squared=1,
        )


@pytest.mark.parametrize(
    "configuration,match",
    [
        (["u"], "exact tuple"),
        (("x",), "outside"),
        ((1,), "exact nonempty text"),
        (("",), "exact nonempty text"),
        (("é",), "ASCII"),
        (("u" * 65,), "byte bound"),
        (("u", "u", "u", "u", "u"), "cap"),
    ],
)
def test_configuration_refusals(
    reference: types.ModuleType, configuration: Any, match: str
) -> None:
    with pytest.raises((TypeError, reference.CKSReferenceError), match=match):
        reference.configuration_distance(_rank_one_spec(reference), configuration, ())


def test_configuration_tuple_and_token_subclasses_refused(
    reference: types.ModuleType,
) -> None:
    class TupleSubclass(tuple):
        pass

    class StringSubclass(str):
        pass

    spec = _rank_one_spec(reference)
    with pytest.raises(TypeError, match="exact tuple"):
        reference.configuration_kernel(spec, TupleSubclass(("u",)), ())
    with pytest.raises(TypeError, match="exact nonempty text"):
        reference.configuration_kernel(spec, (StringSubclass("u"),), ())


def test_conditional_u_statistic_exact_formula_and_direction(
    reference: types.ModuleType,
) -> None:
    spec = _rank_one_spec(reference)
    draws = (("u",), ("v",))
    result = reference.conditional_cks_u_statistic(spec, draws, ("u",))
    identity = reference.GaussianValue(exponent=Fraction(0, 1))
    separated = reference.GaussianValue(exponent=Fraction(1, 2))
    assert result.off_diagonal_kernel_values == (separated,)
    assert result.target_kernel_values == (identity, separated)
    assert result.formal_loss == reference.FormalGaussianCombination(
        terms=(
            reference.GaussianTerm(
                exponent=Fraction(0, 1), coefficient=Fraction(-1, 1)
            ),
        )
    )
    assert result.score_direction == "LOWER_IS_BETTER"
    assert result.conditional_iid_premise_asserted_by_reference is False


def test_conditional_u_statistic_combines_equal_exponents_exactly(
    reference: types.ModuleType,
) -> None:
    spec = _rank_one_spec(reference)
    result = reference.conditional_cks_u_statistic(
        spec, (("u",), ("u",), ("v",)), ("v",)
    )
    assert result.formal_loss == reference.FormalGaussianCombination(
        terms=(
            reference.GaussianTerm(
                exponent=Fraction(0, 1), coefficient=Fraction(-1, 3)
            ),
            reference.GaussianTerm(
                exponent=Fraction(1, 2), coefficient=Fraction(-2, 3)
            ),
        )
    )


@pytest.mark.parametrize(
    "draws,match",
    [
        ([("u",), ("v",)], "exact tuple"),
        ((("u",),), "between 2 and 128"),
        (tuple(("u",) for _ in range(129)), "between 2 and 128"),
    ],
)
def test_conditional_draw_roster_refusals(
    reference: types.ModuleType, draws: Any, match: str
) -> None:
    with pytest.raises((TypeError, reference.CKSReferenceError), match=match):
        reference.conditional_cks_u_statistic(
            _rank_one_spec(reference), draws, ("u",)
        )


def test_conditional_draw_tuple_subclass_refused(reference: types.ModuleType) -> None:
    class TupleSubclass(tuple):
        pass

    with pytest.raises(TypeError, match="exact tuple"):
        reference.conditional_cks_u_statistic(
            _rank_one_spec(reference), TupleSubclass((("u",), ("v",))), ("u",)
        )


def test_report_is_configuration_and_draw_permutation_invariant(
    reference: types.ModuleType,
) -> None:
    spec = _identity_spec(reference)
    first = reference.build_reference_report(
        spec,
        (("a", "b", "a"), ("c",), ()),
        ("a", "c", "b"),
    )
    second = reference.build_reference_report(
        spec,
        ((), ("c",), ("a", "a", "b")),
        ("b", "a", "c"),
    )
    assert first == second
    assert reference.validate_reference_report(
        second,
        spec,
        (("c",), (), ("b", "a", "a")),
        ("c", "b", "a"),
    )


def test_report_digest_complete_and_recomputed_for_admitted_input(
    reference: types.ModuleType,
) -> None:
    spec = _rank_one_spec(reference)
    draws = ((), ("u",), ("v",))
    target = ("u", "v")
    report = reference.build_reference_report(spec, draws, target)
    assert report["report_sha256"] == reference.report_sha256(report)
    assert reference.validate_reference_report(report, spec, draws, target)


REPORT_MUTATIONS = [
    lambda r: r.__setitem__("control_predicate", "FALSE_PREDICATE"),
    lambda r: r.__setitem__("scope", "DOMAIN_INSTANCE"),
    lambda r: r["spec"].__setitem__("event_gram_psd", False),
    lambda r: r["spec"].__setitem__(
        "event_probability_mean_map_characteristic", False
    ),
    lambda r: r["canonical_inputs"].__setitem__("draw_multiset", []),
    lambda r: r["authoritative_kernel_value_contract"].__setitem__(
        "binary64_kernel_or_score_value_authoritative", True
    ),
    lambda r: r["authoritative_kernel_value_contract"].__setitem__(
        "implementation_computes_numeric_order_sign_or_comparison", True
    ),
    lambda r: r["conditional_cks_u_statistic"].__setitem__(
        "score_direction", "HIGHER_IS_BETTER"
    ),
    lambda r: r["conditional_cks_u_statistic"].__setitem__(
        "conditional_iid_premise_asserted_by_reference", True
    ),
    lambda r: r["conditional_cks_u_statistic"].__setitem__(
        "requires_R_at_least_two", False
    ),
    lambda r: r["conditional_cks_u_statistic"]["formal_loss"].__setitem__(
        "numeric_order_sign_or_comparison_computed", True
    ),
    lambda r: r["formula_counterexamples"].__setitem__("scientific_result", True),
    lambda r: r["formula_counterexamples"]["raw_unnormalized_collision"].__setitem__(
        "raw_squared_distance", {"numerator": 1, "denominator": 1}
    ),
    lambda r: r["binary64_failure_witnesses"]["constant_collapse"].__setitem__(
        "descriptors_equal", True
    ),
    lambda r: r["binary64_failure_witnesses"][
        "near_one_three_by_three_gram"
    ].__setitem__("rounded_gram_positive_semidefinite", True),
    lambda r: r["binary64_failure_witnesses"]["score_cancellation"].__setitem__(
        "binary64_subtraction_is_authoritative", True
    ),
    lambda r: r["report_resource_contract"].__setitem__(
        "cycles_or_repeated_containers_accepted", True
    ),
    lambda r: r["report_resource_contract"].__setitem__(
        "report_generation_total_over_score_domain", True
    ),
    lambda r: r["report_resource_contract"].__setitem__(
        "report_complete_for_report_admitted_inputs_only", False
    ),
    lambda r: r["report_resource_contract"].__setitem__(
        "build_reference_report_resource_refusal_invalidates_previously_constructed_score",
        True,
    ),
    lambda r: r["report_resource_contract"].__setitem__(
        "standalone_report_sha256_resource_refusal_implies_valid_score", True
    ),
    lambda r: r["report_resource_contract"].__setitem__(
        "identical_single_symbol_R62_score_succeeds_report_resource_refuses", False
    ),
    lambda r: r["nonclosures"].__setitem__("B04_closed", True),
    lambda r: r["nonclosures"].__setitem__("F105_closed", True),
    lambda r: r["nonclosures"].__setitem__("F106_modified", True),
    lambda r: r["nonclosures"].__setitem__("F108_modified", True),
    lambda r: r["nonclosures"].__setitem__("F109_through_F112_closed", True),
    lambda r: r["nonclosures"].__setitem__(
        "gate_a_exact_metric_checkbox_closed", True
    ),
    lambda r: r["nonclosures"].__setitem__("production_metric_implemented", True),
    lambda r: r["nonclosures"].__setitem__(
        "scientific_execution_performed", True
    ),
    lambda r: r["nonclosures"].__setitem__("tracker_modified", True),
    lambda r: r["publication_boundary"].__setitem__(
        "anonymous_or_public_inclusion_permitted", True
    ),
    lambda r: r.__setitem__("scientific_result", True),
]


@pytest.mark.parametrize("mutate", REPORT_MUTATIONS)
def test_report_semantic_flip_fails_even_after_rehash(
    reference: types.ModuleType, mutate: Callable[[Dict[str, Any]], None]
) -> None:
    spec = _rank_one_spec(reference)
    draws = ((), ("u",), ("v",))
    target = ("u", "v")
    report = reference.build_reference_report(spec, draws, target)
    mutate(report)
    with pytest.raises(reference.CKSReferenceError, match="digest"):
        reference.validate_reference_report(report, spec, draws, target)
    report["report_sha256"] = reference.report_sha256(report)
    with pytest.raises(reference.CKSReferenceError, match="report"):
        reference.validate_reference_report(report, spec, draws, target)


def test_report_exact_top_level_and_nested_key_types_refused(
    reference: types.ModuleType,
) -> None:
    class StringSubclass(str):
        pass

    spec = _rank_one_spec(reference)
    report = reference.build_reference_report(spec, (("u",), ("v",)), ("u",))
    value = report.pop("scope")
    report[StringSubclass("scope")] = value
    with pytest.raises(TypeError, match="keys"):
        reference.report_sha256(report)

    report = reference.build_reference_report(spec, (("u",), ("v",)), ("u",))
    value = report["nonclosures"].pop("B04_closed")
    report["nonclosures"][StringSubclass("B04_closed")] = value
    with pytest.raises(TypeError, match="keys"):
        reference.report_sha256(report)


def test_report_exact_nested_scalar_types_refused(reference: types.ModuleType) -> None:
    class IntegerSubclass(int):
        pass

    spec = _rank_one_spec(reference)
    report = reference.build_reference_report(spec, (("u",), ("v",)), ("u",))
    report["conditional_cks_u_statistic"]["draw_count"] = IntegerSubclass(2)
    with pytest.raises(TypeError, match="non-exact"):
        reference.report_sha256(report)


def test_report_cycle_and_repeated_container_refused_before_serialization(
    reference: types.ModuleType,
) -> None:
    assert reference.CKSReportResourceError.__doc__ == (
        "A report graph or generated report exceeds bounded report-resource admission."
    )
    cyclic: Dict[str, Any] = {}
    cyclic["self"] = cyclic
    with pytest.raises(reference.CKSReportResourceError, match="cycle|repeated"):
        reference.report_sha256(cyclic)

    shared: list = []
    aliased = {"left": shared, "right": shared}
    with pytest.raises(reference.CKSReportResourceError, match="cycle|repeated"):
        reference.report_sha256(aliased)

    admitted = reference.build_reference_report(
        _rank_one_spec(reference), (("u",), ("v",)), ("u",)
    )
    assert (
        admitted["report_resource_contract"][
            "standalone_report_sha256_resource_refusal_implies_valid_score"
        ]
        is False
    )


def test_report_depth_node_and_container_bounds(reference: types.ModuleType) -> None:
    deep: Any = None
    for _ in range(reference.MAX_REPORT_JSON_DEPTH + 1):
        deep = [deep]
    with pytest.raises(reference.CKSReportResourceError, match="depth"):
        reference.report_sha256({"value": deep})

    many_nodes = [[None, None] for _ in range(3_334)]
    with pytest.raises(reference.CKSReportResourceError, match="node"):
        reference.report_sha256({"value": many_nodes})

    too_many_items = [None] * (reference.MAX_REPORT_CONTAINER_ITEMS + 1)
    with pytest.raises(reference.CKSReportResourceError, match="container item"):
        reference.report_sha256({"value": too_many_items})


def test_report_text_integer_rational_and_nonfinite_bounds(
    reference: types.ModuleType,
) -> None:
    long_text = "x" * (reference.MAX_REPORT_TEXT_BYTES + 1)
    with pytest.raises(reference.CKSReportResourceError, match="text byte"):
        reference.report_sha256({"value": long_text})
    with pytest.raises(reference.CKSReportResourceError, match="text byte"):
        reference.report_sha256({long_text: 1})

    huge_integer = 1 << reference.MAX_REPORT_INTEGER_BITS
    with pytest.raises(reference.CKSReportResourceError, match="integer bit"):
        reference.report_sha256({"value": huge_integer})
    with pytest.raises(reference.CKSReportResourceError, match="integer bit"):
        reference.report_sha256(
            {"exponent": {"numerator": huge_integer, "denominator": 1}}
        )
    with pytest.raises(reference.CKSReferenceError, match="nonfinite"):
        reference.report_sha256({"value": math.inf})


def test_report_container_subclasses_refused(reference: types.ModuleType) -> None:
    class ListSubclass(list):
        pass

    class DictSubclass(dict):
        pass

    with pytest.raises(TypeError, match="non-exact"):
        reference.report_sha256({"value": ListSubclass()})
    with pytest.raises(TypeError, match="non-exact"):
        reference.report_sha256({"value": DictSubclass()})


def test_report_exact_payload_byte_cap_after_bounded_serialization(
    reference: types.ModuleType,
) -> None:
    oversized_payload = {
        "value": ["x" * reference.MAX_REPORT_TEXT_BYTES for _ in range(300)]
    }
    with pytest.raises(reference.CKSReportResourceError, match="byte bound"):
        reference.report_sha256(oversized_payload)


def _one_symbol_report_boundary_spec(reference: types.ModuleType) -> Any:
    return reference.FiniteCKSSpec(
        symbols=("u",),
        event_gram=((Fraction(1),),),
        configuration_cap=1,
        count_scale_squared=Fraction(1),
        event_scale_squared=Fraction(1),
        outer_bandwidth_squared=Fraction(1),
    )


def test_identical_one_symbol_R61_score_and_report_succeed(
    reference: types.ModuleType,
) -> None:
    spec = _one_symbol_report_boundary_spec(reference)
    draws = tuple(("u",) for _ in range(61))
    score = reference.conditional_cks_u_statistic(spec, draws, ("u",))
    assert score.draw_count == 61
    assert score.formal_loss == reference.FormalGaussianCombination(
        terms=(reference.GaussianTerm(Fraction(0), Fraction(-1)),)
    )
    report = reference.build_reference_report(spec, draws, ("u",))
    contract = report["report_resource_contract"]
    assert contract["report_generation_total_over_score_domain"] is False
    assert contract["report_complete_for_report_admitted_inputs_only"] is True
    assert (
        contract[
            "build_reference_report_resource_refusal_invalidates_previously_constructed_score"
        ]
        is False
    )
    assert (
        contract["standalone_report_sha256_resource_refusal_implies_valid_score"]
        is False
    )
    assert contract["report_admission_worst_case_totality_claimed"] is False
    assert reference.validate_reference_report(report, spec, draws, ("u",))


def test_identical_one_symbol_R62_score_succeeds_report_resource_refuses(
    reference: types.ModuleType,
) -> None:
    spec = _one_symbol_report_boundary_spec(reference)
    draws = tuple(("u",) for _ in range(62))
    score = reference.conditional_cks_u_statistic(spec, draws, ("u",))
    assert score.draw_count == 62
    assert score.formal_loss.terms == (
        reference.GaussianTerm(Fraction(0), Fraction(-1)),
    )
    with pytest.raises(reference.CKSReportResourceError, match="node bound"):
        reference.build_reference_report(spec, draws, ("u",))


def test_identical_one_symbol_R128_score_succeeds_report_resource_refuses(
    reference: types.ModuleType,
) -> None:
    spec = _one_symbol_report_boundary_spec(reference)
    draws = tuple(("u",) for _ in range(128))
    score = reference.conditional_cks_u_statistic(spec, draws, ("u",))
    assert score.draw_count == 128
    assert score.formal_loss.terms == (
        reference.GaussianTerm(Fraction(0), Fraction(-1)),
    )
    with pytest.raises(reference.CKSReportResourceError, match="container item"):
        reference.build_reference_report(spec, draws, ("u",))


def test_invalid_score_input_is_not_report_resource_refusal(
    reference: types.ModuleType,
) -> None:
    spec = _one_symbol_report_boundary_spec(reference)
    with pytest.raises(reference.CKSReferenceError) as captured:
        reference.conditional_cks_u_statistic(spec, (("u",),), ("u",))
    assert not isinstance(captured.value, reference.CKSReportResourceError)
    with pytest.raises(TypeError) as type_captured:
        reference.conditional_cks_u_statistic(spec, [("u",), ("u",)], ("u",))
    assert not isinstance(type_captured.value, reference.CKSReportResourceError)


PUBLIC_SPEC_CONSUMERS = [
    lambda m, s: m.configuration_distance(s, (), ()),
    lambda m, s: m.configuration_kernel(s, (), ()),
    lambda m, s: m.conditional_cks_u_statistic(s, ((), ()), ()),
    lambda m, s: m.build_reference_report(s, ((), ()), ()),
    lambda m, s: m.validate_reference_report(
        m.build_reference_report(_rank_one_spec(m), ((), ()), ()), s, ((), ()), ()
    ),
]


@pytest.mark.parametrize("consume", PUBLIC_SPEC_CONSUMERS)
@pytest.mark.parametrize(
    "field,value",
    [
        ("configuration_cap", True),
        ("symbols", ["u", "v"]),
        ("event_gram", ((Fraction(-1), Fraction(0)), (Fraction(0), Fraction(1)))),
        ("count_scale_squared", Fraction(0)),
        ("event_scale_squared", 1.0),
        ("outer_bandwidth_squared", Fraction(0)),
    ],
)
def test_low_level_frozen_spec_corruption_refused_at_every_public_boundary(
    reference: types.ModuleType,
    consume: Callable[[types.ModuleType, Any], Any],
    field: str,
    value: Any,
) -> None:
    spec = _rank_one_spec(reference)
    object.__setattr__(spec, field, value)
    with pytest.raises((TypeError, reference.CKSReferenceError)):
        consume(reference, spec)


def test_spec_subclass_refused_at_every_public_boundary(
    reference: types.ModuleType,
) -> None:
    class SpecSubclass(reference.FiniteCKSSpec):
        pass

    spec = SpecSubclass(
        symbols=("u",),
        event_gram=((Fraction(1),),),
        configuration_cap=2,
        count_scale_squared=Fraction(1),
        event_scale_squared=Fraction(1),
        outer_bandwidth_squared=Fraction(1),
    )
    for consume in PUBLIC_SPEC_CONSUMERS:
        with pytest.raises(TypeError, match="exact FiniteCKSSpec"):
            consume(reference, spec)


def test_symbolic_gaussian_descriptor_and_formal_term_strict_types(
    reference: types.ModuleType,
) -> None:
    with pytest.raises(TypeError, match="int or Fraction"):
        reference.GaussianValue(exponent=True)
    with pytest.raises(TypeError, match="int or Fraction"):
        reference.GaussianTerm(exponent=Fraction(0), coefficient=1.0)
    with pytest.raises(reference.CKSReferenceError, match="nonnegative"):
        reference.GaussianValue(exponent=Fraction(-1))
    with pytest.raises(reference.CKSReferenceError, match="nonzero"):
        reference.GaussianTerm(exponent=Fraction(0), coefficient=Fraction(0))
    first = reference.GaussianTerm(Fraction(1), Fraction(1))
    second = reference.GaussianTerm(Fraction(0), Fraction(1))
    with pytest.raises(reference.CKSReferenceError, match="sorted"):
        reference.FormalGaussianCombination(terms=(first, second))
    duplicate = reference.GaussianTerm(Fraction(1), Fraction(-1))
    with pytest.raises(reference.CKSReferenceError, match="unique"):
        reference.FormalGaussianCombination(terms=(first, duplicate))


def test_raw_formula_and_drop_count_counterexamples(reference: types.ModuleType) -> None:
    witness = reference.raw_formula_counterexamples()
    assert witness["characteristic_on_event_probabilities"] is True
    assert witness["raw_unnormalized_collision"] == {
        "left": [["u", 2]],
        "right": [["v", 1]],
        "left_raw_mean": {"numerator": 2, "denominator": 1},
        "right_raw_mean": {"numerator": 2, "denominator": 1},
        "raw_squared_distance": {"numerator": 0, "denominator": 1},
        "corrected_count_channel_squared_at_unit_scale": {
            "numerator": 1,
            "denominator": 1,
        },
        "corrected_normalized_event_channel_squared_at_unit_scale": {
            "numerator": 1,
            "denominator": 1,
        },
    }
    assert witness["drop_count_collision"] == {
        "left": [["u", 1]],
        "right": [["u", 2]],
        "normalized_event_squared_distance": {"numerator": 0, "denominator": 1},
        "count_channel_squared_at_unit_scale": {"numerator": 1, "denominator": 1},
    }
    assert witness["scientific_result"] is False


def test_binary64_constant_collapse_is_avoided_symbolically(
    reference: types.ModuleType,
) -> None:
    spec = reference.FiniteCKSSpec(
        symbols=("u",),
        event_gram=((Fraction(0),),),
        configuration_cap=2,
        count_scale_squared=Fraction(1),
        event_scale_squared=Fraction(1),
        outer_bandwidth_squared=Fraction(1 << 59),
    )
    identity = reference.configuration_kernel(spec, (), ())
    distinct = reference.configuration_kernel(spec, (), ("u",))
    assert identity == reference.GaussianValue(exponent=Fraction(0, 1))
    assert distinct == reference.GaussianValue(exponent=Fraction(1, 1 << 60))
    assert identity != distinct
    witness = reference.binary64_failure_witnesses()["constant_collapse"]
    assert witness["descriptors_equal"] is False
    assert witness["binary64_hex_for_both"] == "0x1.0000000000000p+0"


def test_binary64_near_one_gram_indefiniteness_witness(
    reference: types.ModuleType,
) -> None:
    spec = reference.FiniteCKSSpec(
        symbols=("u",),
        event_gram=((Fraction(0),),),
        configuration_cap=2,
        count_scale_squared=Fraction(1),
        event_scale_squared=Fraction(1),
        outer_bandwidth_squared=Fraction(1 << 39),
    )
    configurations = ((), ("u",), ("u", "u"))
    exponents = tuple(
        tuple(
            reference.configuration_kernel(spec, left, right).exponent
            for right in configurations
        )
        for left in configurations
    )
    assert exponents == (
        (Fraction(0), Fraction(1, 1 << 40), Fraction(1, 1 << 38)),
        (Fraction(1, 1 << 40), Fraction(0), Fraction(1, 1 << 40)),
        (Fraction(1, 1 << 38), Fraction(1, 1 << 40), Fraction(0)),
    )
    witness = reference.binary64_failure_witnesses()[
        "near_one_three_by_three_gram"
    ]
    assert witness["rounded_gram_determinant"] == {
        "numerator": -1,
        "denominator": 166153499473114484112975882535043072,
    }
    assert witness["rounded_gram_positive_semidefinite"] is False
    assert witness["symbolic_gaussian_gram_governed_by_generic_theorem"] is True


def test_binary64_score_cancellation_witness_is_nonauthoritative(
    reference: types.ModuleType,
) -> None:
    witness = reference.binary64_failure_witnesses()["score_cancellation"]
    assert witness["authoritative_difference_is_formally_zero"] is False
    assert witness["binary64_subtraction_result"] == {
        "numerator": 0,
        "denominator": 1,
    }
    assert witness["binary64_subtraction_is_authoritative"] is False
    formal = witness["authoritative_formal_difference"]
    assert formal["numerical_value_provided"] is False
    assert formal["numeric_order_sign_or_comparison_computed"] is False


def test_public_api_has_no_callback_or_module_surface(reference: types.ModuleType) -> None:
    expected = {
        "configuration_distance": ("spec", "left", "right"),
        "configuration_kernel": ("spec", "left", "right"),
        "conditional_cks_u_statistic": ("spec", "draws", "target"),
        "raw_formula_counterexamples": (),
        "binary64_failure_witnesses": (),
        "report_sha256": ("report",),
        "build_reference_report": ("spec", "draws", "target"),
        "validate_reference_report": ("report", "spec", "draws", "target"),
    }
    for name, parameters in expected.items():
        signature = inspect.signature(getattr(reference, name))
        assert tuple(signature.parameters) == parameters
        assert not any(
            token in parameter.lower()
            for parameter in parameters
            for token in ("callback", "callable", "module", "kernel_fn")
        )


def _copy_roster(validator: types.ModuleType, tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    paths = [validator.SOURCE_PATH, validator.HUMAN_PATH, validator.MACHINE_PATH]
    paths.extend([validator.VALIDATOR_PATH, validator.TEST_PATH])
    paths.extend(path for _, path, _, _ in validator.EXPECTED_PREDECESSORS)
    for relative in paths:
        source = WORKSPACE / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=False)
        os.chmod(target, 0o644)
    return root


def _rewrite_machine(
    validator: types.ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
) -> None:
    path = root / validator.MACHINE_PATH
    record = json.loads(path.read_text("ascii"))
    mutate(record)
    record["record_sha256"] = validator.record_sha256(record)
    path.write_bytes(validator.canonical_machine_bytes(record))
    os.chmod(path, 0o644)


def test_live_validator_and_exact_nonclosure(validator: types.ModuleType) -> None:
    result = validator.validate(WORKSPACE)
    assert result["validation"] == "PASS"
    assert result["control_predicate"] == (
        "GENERIC_CKS_COUNT_NORMALIZED_EVENT_REFERENCE_IMPLEMENTATION_VALIDATED"
    )
    assert result["control_predicate_value"] is True
    assert result["generic_reference_only"] is True
    assert result["B04_status"] == "OPEN"
    assert result["F105_status"] == "OPEN"
    assert result["F106_or_F108_modified"] is False
    assert result["F109_through_F112_status"] == "OPEN"
    assert result["gate_a_exact_metric_checkbox_closed"] is False
    assert result["fields_blockers_formal_tests_or_results_closed"] == 0
    assert result["scientific_scorecard_effect"] == 0
    assert result["tracker_modified"] is False
    assert result["network_data_entropy_runtime_training_or_science_performed"] is False
    assert result["third_generic_B04_precursor_permitted"] is False


MACHINE_MUTATIONS = [
    lambda r: r.__setitem__("state", "UNVALIDATED"),
    lambda r: r["independent_hold_repair"].__setitem__(
        "P1_binary64_kernel_and_score_contract_replaced", False
    ),
    lambda r: r["independent_hold_repair"].__setitem__(
        "P2_recursive_unbounded_report_prevalidation_replaced", False
    ),
    lambda r: r["independent_hold_repair"].__setitem__(
        "P2_partial_fail_closed_report_admission_contract_added", False
    ),
    lambda r: r["independent_hold_repair"].__setitem__(
        "P2_generated_report_and_standalone_hash_refusal_scopes_separated", False
    ),
    lambda r: r["authority_boundary"].__setitem__(
        "network_contact_data_entropy_runtime_training_science_or_submission_authorized",
        True,
    ),
    lambda r: r["predecessor_contract"].__setitem__(
        "all_predecessors_and_source_verified_before_source_execution", False
    ),
    lambda r: r["predecessor_contract"].__setitem__(
        "source_path_loader_or_bytecode_cache_used", True
    ),
    lambda r: r["construction_contract"].__setitem__("positive_count_channel", False),
    lambda r: r["construction_contract"].__setitem__(
        "event_probability_mean_characteristicness_checked_on_zero_sum_subspace",
        False,
    ),
    lambda r: r["construction_contract"].__setitem__(
        "arbitrary_kernel_callback_or_module_accepted", True
    ),
    lambda r: r["construction_contract"].__setitem__(
        "authoritative_kernel_value_exact_symbolic_exp_negative_rational", False
    ),
    lambda r: r["construction_contract"].__setitem__(
        "binary64_kernel_value_authoritative", True
    ),
    lambda r: r["strict_boundary_contract"].__setitem__(
        "frozen_dataclass_revalidated_at_every_public_consumption_boundary", False
    ),
    lambda r: r["strict_boundary_contract"].__setitem__("bool_as_int_rejected", False),
    lambda r: r["edge_case_contract"].__setitem__(
        "raw_unnormalized_formula_counterexample_present", False
    ),
    lambda r: r["edge_case_contract"].__setitem__(
        "binary64_indefinite_near_one_three_by_three_gram_witness_present", False
    ),
    lambda r: r["score_contract"].__setitem__("lower_is_better", False),
    lambda r: r["score_contract"].__setitem__(
        "conditional_iid_tested_or_asserted_by_reference", True
    ),
    lambda r: r["score_contract"].__setitem__(
        "authoritative_score_is_canonical_exact_formal_gaussian_combination", False
    ),
    lambda r: r["score_contract"].__setitem__(
        "numerical_score_value_provided", True
    ),
    lambda r: r["score_contract"].__setitem__(
        "numeric_order_sign_or_comparison_computed", True
    ),
    lambda r: r["report_contract"].__setitem__(
        "validation_recomputes_full_report_for_report_admitted_inputs", False
    ),
    lambda r: r["report_contract"].__setitem__(
        "rehash_after_semantic_flip_still_refused", False
    ),
    lambda r: r["report_contract"].__setitem__(
        "report_generation_total_over_score_domain", True
    ),
    lambda r: r["report_contract"].__setitem__(
        "report_complete_for_report_admitted_inputs_only", False
    ),
    lambda r: r["report_contract"].__setitem__(
        "build_reference_report_resource_refusal_invalidates_previously_constructed_score",
        True,
    ),
    lambda r: r["report_contract"].__setitem__(
        "standalone_report_sha256_resource_refusal_implies_valid_score", True
    ),
    lambda r: r["report_contract"].__setitem__(
        "report_admission_worst_case_totality_claimed", True
    ),
    lambda r: r["report_contract"].__setitem__(
        "identical_single_symbol_R62_score_succeeds_report_resource_refuses", False
    ),
    lambda r: r["report_contract"].__setitem__(
        "bounded_iterative_graph_walk_before_serialization", False
    ),
    lambda r: r["report_contract"].__setitem__(
        "cycles_and_repeated_container_identities_refused", False
    ),
    lambda r: r["report_contract"].__setitem__("maximum_depth", 10_000),
    lambda r: r["report_contract"].__setitem__(
        "exact_byte_cap_checked_immediately_after_bounded_serialization", False
    ),
    lambda r: r["effect_boundary"].__setitem__(
        "no_effect_claim_scoped_to_exact_hard_pinned_source_and_validator_path",
        False,
    ),
    lambda r: r["project_effects"].__setitem__("B04_status", "CLOSED"),
    lambda r: r["project_effects"].__setitem__("F106_modified", True),
    lambda r: r["project_effects"].__setitem__("F108_modified", True),
    lambda r: r["project_effects"].__setitem__("fields_closed", 1),
    lambda r: r["project_effects"].__setitem__("tracker_modified", True),
    lambda r: r["anti_drift_contract"].__setitem__(
        "third_B04_artifact_before_exact_domain_instance_or_field_disposition_permitted",
        True,
    ),
    lambda r: r["publication_boundary"].__setitem__(
        "anonymous_or_public_inclusion_permitted", True
    ),
]


@pytest.mark.parametrize("mutate", MACHINE_MUTATIONS)
def test_machine_semantic_mutations_fail_after_rehash(
    validator: types.ModuleType,
    tmp_path: Path,
    mutate: Callable[[Dict[str, Any]], None],
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_machine_exact_top_level_and_nested_key_types_refused(
    validator: types.ModuleType,
) -> None:
    class StringSubclass(str):
        pass

    record = json.loads((WORKSPACE / validator.MACHINE_PATH).read_text("ascii"))
    value = record.pop("state")
    record[StringSubclass("state")] = value
    with pytest.raises(validator.ValidationError, match="key"):
        validator.record_sha256(record)

    record = json.loads((WORKSPACE / validator.MACHINE_PATH).read_text("ascii"))
    value = record["project_effects"].pop("B04_status")
    record["project_effects"][StringSubclass("B04_status")] = value
    with pytest.raises(validator.ValidationError, match="key"):
        validator.record_sha256(record)


def test_predecessor_drift_fails(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.EXPECTED_PREDECESSORS[0][1]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError, match="predecessor/source"):
        validator.validate(root)


@pytest.mark.parametrize("relative", ["HUMAN_PATH", "TEST_PATH", "VALIDATOR_PATH"])
def test_package_binding_drift_fails(
    validator: types.ModuleType, tmp_path: Path, relative: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / getattr(validator, relative)
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_alternate_source_fails_before_execution(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    marker = tmp_path / "effect-marker"
    source = root / validator.SOURCE_PATH
    source.write_text(
        "from pathlib import Path\nPath(%r).write_text('effect')\n" % str(marker),
        encoding="utf-8",
    )
    os.chmod(source, 0o644)
    with pytest.raises(validator.ValidationError, match="hard-pinned"):
        validator.validate(root)
    assert not marker.exists()


def test_verified_source_buffer_not_reopened_after_path_rebind(
    validator: types.ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_roster(validator, tmp_path)
    marker = tmp_path / "rebind-effect-marker"
    original = validator._stable_read
    rebound = {"done": False}

    def stable_then_rebind(read_root: Path, relative: str) -> bytes:
        raw = original(read_root, relative)
        if relative == validator.SOURCE_PATH and not rebound["done"]:
            rebound["done"] = True
            path = read_root / relative
            path.write_text(
                "from pathlib import Path\nPath(%r).write_text('effect')\n"
                % str(marker),
                encoding="utf-8",
            )
            os.chmod(path, 0o644)
        return raw

    monkeypatch.setattr(validator, "_stable_read", stable_then_rebind)
    assert validator.validate(root)["validation"] == "PASS"
    assert rebound["done"] is True
    assert not marker.exists()


def test_adjacent_effectful_bytecode_is_not_consulted(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    marker = tmp_path / "pyc-effect-marker"
    alternate = tmp_path / "alternate_source.py"
    alternate.write_text(
        "from pathlib import Path\nPath(%r).write_text('effect')\n" % str(marker),
        encoding="utf-8",
    )
    cache_dir = (root / validator.SOURCE_PATH).parent / "__pycache__"
    cache_dir.mkdir()
    cache = cache_dir / "count_normalized_event_cks_reference.cpython-hostile.pyc"
    py_compile.compile(str(alternate), cfile=str(cache), doraise=True)
    assert validator.validate(root)["validation"] == "PASS"
    assert not marker.exists()


def test_machine_record_digest_noncanonical_and_duplicate_key_refusals(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    machine = root / validator.MACHINE_PATH
    record = json.loads(machine.read_text("ascii"))
    record["record_sha256"] = "0" * 64
    machine.write_bytes(validator.canonical_machine_bytes(record))
    with pytest.raises(validator.ValidationError, match="digest"):
        validator.validate(root)

    root = _copy_roster(validator, tmp_path / "second")
    machine = root / validator.MACHINE_PATH
    record = json.loads(machine.read_text("ascii"))
    machine.write_text(json.dumps(record), encoding="ascii")
    with pytest.raises(validator.ValidationError, match="canonical"):
        validator.validate(root)

    root = _copy_roster(validator, tmp_path / "third")
    machine = root / validator.MACHINE_PATH
    machine.write_text('{"schema_version":"x","schema_version":"y"}\n', "ascii")
    with pytest.raises(validator.ValidationError, match="duplicate"):
        validator.validate(root)


def test_mode_hardlink_and_symlink_custody_refusals(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    machine = root / validator.MACHINE_PATH
    os.chmod(machine, 0o600)
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)

    root = _copy_roster(validator, tmp_path / "hardlink")
    machine = root / validator.MACHINE_PATH
    os.link(machine, tmp_path / "machine-alias.json")
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)

    root = _copy_roster(validator, tmp_path / "symlink")
    source = root / validator.SOURCE_PATH
    target = tmp_path / "source-target.py"
    shutil.copy2(source, target)
    source.unlink()
    source.symlink_to(target)
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)


def test_source_safety_and_exact_public_roster(validator: types.ModuleType) -> None:
    result = validator._source_safety(SOURCE.read_bytes())
    assert result == {
        "ast_parse": "PASS",
        "pure_import_roster": [
            "__future__",
            "dataclasses",
            "fractions",
            "hashlib",
            "json",
            "math",
            "typing",
        ],
        "public_callback_parameters": 0,
        "project_imports": 0,
        "effectful_imports_or_calls": 0,
    }


def test_publication_safe_derivative_boundary_is_fail_closed(
    validator: types.ModuleType,
) -> None:
    record = json.loads((WORKSPACE / validator.MACHINE_PATH).read_text("ascii"))
    assert record["publication_boundary"] == {
        "internal_evidence_only": True,
        "anonymous_or_public_inclusion_permitted": False,
        "absolute_user_path_credentials_person_or_dataset_rows_present": False,
        "publication_safe_derivative_requires_fresh_anonymity_provenance_proof_code_and_receipt_review": True,
    }
    assert b"/Users/" not in SOURCE.read_bytes()
    assert b"PhysioNet" not in SOURCE.read_bytes()
    assert b"retail" not in SOURCE.read_bytes()
