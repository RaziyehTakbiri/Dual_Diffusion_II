"""Hostile and regression tests for the bounded two-macrostep precursor."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from heterodiff.evaluation import (
    formal_test29_test30_single_macrostep_integration as single,
)
from heterodiff.evaluation import (
    formal_test29_test30_two_macrostep_path_qualification as path,
)
from heterodiff.evaluation import (
    formal_test30_synthetic_coupled_path_qualification as test30,
)
from heterodiff.processes import formal_test29_finite_acyclic_route_oracle as test29


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / (
    "src/heterodiff/evaluation/"
    "formal_test29_test30_two_macrostep_path_qualification.py"
)
TIMETABLE = ROOT / "PROJECT_COMPLETION_TIMETABLE.md"


def _frozen(first: int = 2, second: int = 27):
    return path.build_frozen_two_macrostep_path_input(
        single, test29, test30, first, second
    )


def _run(first: int = 2, second: int = 27):
    return path.run_supplied_two_macrostep_path(
        single, test29, test30, _frozen(first, second)
    )


@pytest.fixture(scope="module")
def qualification():
    return path.run_frozen_two_macrostep_qualification(single, test29, test30)


def test_complete_low_word_pair_space_has_exact_nonvacuous_coverage(
    qualification,
):
    assert type(qualification) is path.FrozenTwoMacrostepQualification
    assert qualification.passed is True
    assert qualification.ordered_word_pair_cases_checked == 1024
    assert qualification.route_pair_counts == (
        ("birth->birth", 256),
        ("birth->death", 128),
        ("birth->replacement", 128),
        ("death->birth", 128),
        ("death->death", 64),
        ("death->replacement", 64),
        ("replacement->birth", 128),
        ("replacement->death", 64),
        ("replacement->replacement", 64),
    )
    assert qualification.boundary_cardinality_counts == (
        (1, 256),
        (2, 256),
        (3, 512),
    )
    assert qualification.final_cardinality_counts == (
        (0, 64),
        (1, 128),
        (2, 320),
        (3, 256),
        (4, 256),
    )
    assert qualification.distinct_input_sha256_count == 1024
    assert qualification.distinct_report_sha256_count == 1024
    assert qualification.ordered_case_commitment_sha256 == (
        "3273b1c5e553093a3d5a35f4e7686b018363ac609bb300dd6dbb87f66daf7591"
    )
    assert qualification.report_sha256 == (
        "2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53"
    )
    assert (
        path.recompute_frozen_two_macrostep_qualification_report_sha256(
            qualification
        )
        == qualification.report_sha256
    )


def test_representative_replacement_then_death_carries_exact_boundary_state():
    result = _run()
    assert type(result) is path.TwoMacrostepPathResult
    assert result.input_sha256 == (
        "11decfb2a16606b69404958d2e7cac2b75808f78adc00ab8c562da8f993ece8e"
    )
    assert result.report_sha256 == (
        "9c66342668b2225cbe5d8705a175dd857fd1aa9d2411bbeea489a41e884b7c94"
    )
    first, second = result.steps
    assert first.family == "replacement"
    assert first.source_serial == 1
    assert first.created_serial == 3
    assert first.active_serials_before == (1, 2)
    assert first.active_serials_after == (2, 3)
    assert first.retired_serials_after == (1,)
    assert second.family == "death"
    assert second.source_serial == 3
    assert second.created_serial is None
    assert second.active_serials_before == (2, 3)
    assert second.active_serials_after == (2,)
    assert second.retired_serials_after == (1, 3)
    assert first.state_after_right == second.state_before
    assert result.total_address_count == 9
    assert (
        path.validate_two_macrostep_path_result(
            single, test29, test30, _frozen(), result
        )
        is result
    )


def test_two_replacements_use_monotone_fresh_serials_without_resurrection():
    result = _run(2, 2)
    first, second = result.steps
    assert first.active_serials_after == (2, 3)
    assert first.retired_serials_after == (1,)
    assert first.next_serial_after == 4
    assert second.source_serial == 2
    assert second.created_serial == 4
    assert second.active_serials_after == (3, 4)
    assert second.retired_serials_after == (1, 2)
    assert second.next_serial_after == 5
    assert not set(second.active_serials_after).intersection(
        second.retired_serials_after
    )


def test_two_deaths_safely_reach_an_empty_terminal_coordinate_roster():
    result = _run(3, 3)
    first, second = result.steps
    assert first.family == second.family == "death"
    assert first.active_serials_after == (2,)
    assert second.active_serials_after == ()
    assert second.state_after_jump == ()
    assert second.state_after_right == ()
    assert second.right_heun_application_count == 0
    assert result.boundary_state_continuity is True


def test_each_step_uses_exact_cp23_cp24_addresses_and_the_path_is_disjoint():
    supplied = _frozen()
    identities = []
    for step_index, step in enumerate(supplied.steps):
        for item in step.left_increments:
            address = item.address
            assert address.domain_tag == test30.TAG_BROWNIAN_LEFT
            assert address.run_id == path.FROZEN_RUN_ID
            assert address.step_index == step_index
            assert address.philox_key == (
                path.FROZEN_RUN_ID,
                test30.TAG_BROWNIAN_LEFT,
            )
            assert address.philox_counter == (
                0,
                step_index,
                address.occurrence_serial,
                0,
            )
            identities.append((address.philox_key, address.philox_counter))
        central = step.central_word.address
        assert central.key == (path.FROZEN_RUN_ID, 6)
        assert central.counter == (0, step_index, 0, 0)
        identities.append((central.key, central.counter))
        for item in step.right_increments:
            address = item.address
            assert address.domain_tag == test30.TAG_BROWNIAN_RIGHT
            assert address.step_index == step_index
            identities.append((address.philox_key, address.philox_counter))
    assert len(identities) == len(set(identities))


def test_second_step_roster_failure_occurs_before_any_heun_arithmetic(monkeypatch):
    supplied = _frozen()
    second = supplied.steps[1]
    bad_second = replace(second, right_increments=second.right_increments[:-1])
    hostile = replace(supplied, steps=(supplied.steps[0], bad_second))
    calls = []

    def forbidden_heun(*args: Any, **kwargs: Any):
        calls.append((args, kwargs))
        raise AssertionError("arithmetic must not begin before complete preflight")

    monkeypatch.setattr(test30, "_heun_half", forbidden_heun)
    with pytest.raises((TypeError, ValueError)):
        path.run_supplied_two_macrostep_path(single, test29, test30, hostile)
    assert calls == []


@pytest.mark.parametrize("side", ("left", "right"))
def test_missing_extra_and_reordered_second_step_rosters_fail_closed(side: str):
    supplied = _frozen()
    second = supplied.steps[1]
    roster = getattr(second, side + "_increments")
    hostiles = (roster[:-1], roster + roster[:1], tuple(reversed(roster)))
    for hostile_roster in hostiles:
        if hostile_roster == roster:
            continue
        hostile_step = replace(second, **{side + "_increments": hostile_roster})
        hostile = replace(supplied, steps=(supplied.steps[0], hostile_step))
        with pytest.raises((TypeError, ValueError)):
            path.run_supplied_two_macrostep_path(
                single, test29, test30, hostile
            )


def test_wrong_step_cp24_word_fails_closed():
    supplied = _frozen()
    second = supplied.steps[1]
    wrong_word = test29.AddressedUint64Word(
        test29.CP24CompatibleAddress(path.FROZEN_RUN_ID, 0, 0),
        second.central_word.raw64_word,
    )
    hostile_step = replace(second, central_word=wrong_word)
    hostile = replace(supplied, steps=(supplied.steps[0], hostile_step))
    with pytest.raises((TypeError, ValueError)):
        path.run_supplied_two_macrostep_path(single, test29, test30, hostile)


def test_input_boundary_revalidates_object_mutated_scalars_and_exact_types():
    supplied = _frozen()
    mutated = replace(supplied)
    object.__setattr__(mutated, "run_id", True)
    with pytest.raises(TypeError):
        path.run_supplied_two_macrostep_path(single, test29, test30, mutated)

    mutated = replace(supplied)
    object.__setattr__(mutated, "macrostep_width", float("nan"))
    with pytest.raises(ValueError):
        path.run_supplied_two_macrostep_path(single, test29, test30, mutated)

    mutated = replace(supplied)
    object.__setattr__(mutated, "steps", list(mutated.steps))
    with pytest.raises((TypeError, ValueError)):
        path.run_supplied_two_macrostep_path(single, test29, test30, mutated)


def test_contextual_validation_rejects_redigested_semantic_result_forgery():
    supplied = _frozen()
    result = _run()
    second = result.steps[1]
    final = second.state_after_right
    forged_second = replace(
        second,
        state_after_right=final[:-1]
        + ((final[-1][0], final[-1][1], final[-1][2] + 0.125),),
    )
    forged = replace(
        result,
        steps=(result.steps[0], forged_second),
        report_sha256="0" * 64,
    )
    forged = replace(
        forged,
        report_sha256=path.recompute_two_macrostep_path_report_sha256(forged),
    )
    assert forged.report_sha256 != result.report_sha256
    with pytest.raises((TypeError, ValueError)):
        path.validate_two_macrostep_path_result(
            single, test29, test30, supplied, forged
        )


def test_contextual_qualification_validation_rejects_redigested_commitment(
    qualification,
):
    forged = replace(
        qualification,
        ordered_case_commitment_sha256="0" * 64,
        report_sha256="0" * 64,
    )
    forged = replace(
        forged,
        report_sha256=(
            path.recompute_frozen_two_macrostep_qualification_report_sha256(
                forged
            )
        ),
    )
    with pytest.raises((TypeError, ValueError)):
        path.validate_frozen_two_macrostep_qualification(
            single, test29, test30, forged
        )


def test_all_broader_claims_and_project_deltas_remain_false_or_zero(
    qualification,
):
    result = _run()
    assert result.bounded_two_macrostep_path_integrated is True
    assert result.arbitrary_length_general_strang_path_integrated is False
    assert result.parent_custody_authenticated is False
    assert result.test28_initializer_admissible is False
    assert result.live_cp23_stream_consumed is False
    assert result.live_cp24_stream_consumed is False
    assert result.continuous_gaussian_destination_sampled is False
    assert result.waiting_clock_or_acceptance_thinning_executed is False
    assert result.step_halving_or_endpoint_law_qualified is False
    assert result.formal_test28_closed is False
    assert result.formal_test29_closed is False
    assert result.formal_test30_closed is False
    assert (
        result.fields_closed,
        result.blockers_closed,
        result.result_slots_filled,
        result.tracker_files_edited,
    ) == (0, 0, 0, 0)
    assert qualification.arbitrary_length_general_strang_path_integrated is False
    assert qualification.parent_custody_authenticated is False
    assert (
        qualification.formal_tests_closed,
        qualification.fields_closed,
        qualification.blockers_closed,
        qualification.result_slots_filled,
        qualification.tracker_files_edited,
    ) == (0, 0, 0, 0, 0)


def test_parent_boundaries_require_exact_modules_schemas_and_symbols():
    supplied = _frozen()
    with pytest.raises(TypeError):
        path.run_supplied_two_macrostep_path(object(), test29, test30, supplied)
    fake = ModuleType("fake_single")
    fake.SCHEMA_VERSION = single.SCHEMA_VERSION
    with pytest.raises(ValueError):
        path.run_supplied_two_macrostep_path(fake, test29, test30, supplied)


def test_source_has_no_rng_network_process_write_or_tracker_surface():
    raw = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(raw)
    imported = set()
    called_names = set()
    called_attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_attributes.add(node.func.attr)
    assert not imported.intersection(
        {
            "random",
            "secrets",
            "socket",
            "ssl",
            "urllib",
            "http",
            "requests",
            "subprocess",
            "pathlib",
            "os",
        }
    )
    assert not called_names.intersection({"open", "exec", "eval", "compile"})
    assert not called_attributes.intersection(
        {
            "open",
            "write",
            "write_bytes",
            "write_text",
            "unlink",
            "rename",
            "replace",
            "connect",
            "send",
            "sendall",
            "request",
            "run",
            "Popen",
        }
    )
    assert "PROJECT_COMPLETION_TIMETABLE" not in raw
    assert TIMETABLE.is_file()

