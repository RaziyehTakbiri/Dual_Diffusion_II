"""Consolidated hostiles for the stopped Test-29/Test-30 integration precursor."""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List

import pytest

from heterodiff.evaluation import (
    formal_test29_test30_single_macrostep_integration as composite,
)
from heterodiff.evaluation import (
    formal_test30_synthetic_coupled_path_qualification as test30,
)
from heterodiff.processes import (
    formal_test29_finite_acyclic_route_oracle as test29,
)


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.json"
)

EXECUTION_PIN_PATHS = (
    "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
    "manuscript_v3/executable_method_spec.md",
    "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
    "PROJECT_FORMAL_TEST29_FINITE_ACYCLIC_ROUTE_QUALIFICATION.md",
    "research/fixtures/manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.json",
    "research/diagnostics/manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.py",
    "tests/unit/test_formal_test29_finite_acyclic_route_oracle.py",
    "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
    "PROJECT_FORMAL_TEST30_SYNTHETIC_COUPLED_PATH_QUALIFICATION.md",
    "research/fixtures/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.json",
    "research/diagnostics/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py",
    "tests/unit/test_manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py",
)
EXECUTABLE_SOURCE_PIN_PATHS = (
    EXECUTION_PIN_PATHS[0],
    EXECUTION_PIN_PATHS[2],
    EXECUTION_PIN_PATHS[7],
)


class StrangeInt(int):
    pass


class StrangeFloat(float):
    pass


class StrangeText(str):
    pass


class StrangeTuple(tuple):
    pass


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "formal_test29_test30_single_macrostep_validator", ROOT / VALIDATOR_REL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _roster(module: ModuleType) -> List[str]:
    return list(module.ALL_CUSTODY_PATHS)


def _copy_paths(paths: Iterable[str], tmp_path: Path) -> Path:
    for relative in paths:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _copy_package(module: ModuleType, tmp_path: Path) -> Path:
    return _copy_paths(_roster(module), tmp_path)


def _replace_pointer(record: Dict[str, Any], pointer: str, value: Any) -> None:
    current: Any = record
    tokens = pointer.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    redigest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if redigest:
        record["record_sha256"] = module.record_sha256(record)
    if canonical:
        raw = module.canonical_machine_bytes(record)
    else:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _coherently_rebind(record: Dict[str, Any], relative: str, raw: bytes) -> None:
    rows = [
        row
        for group in ("package_bindings", "parent_bindings", "input_bindings")
        for row in record[group]
        if row["path"] == relative
    ]
    assert len(rows) == 1
    rows[0]["bytes"] = len(raw)
    rows[0]["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    rows[0]["trailing_lf"] = raw.endswith(b"\n")


def _frozen(word: int = 2):
    return composite.build_frozen_single_macrostep_input(test29, test30, word)


def _run(word: int = 2):
    return composite.run_supplied_single_macrostep(test29, test30, _frozen(word))


def _mutated_dataclass(value: Any, field: str, hostile: Any) -> Any:
    clone = replace(value)
    object.__setattr__(clone, field, hostile)
    return clone


def test_frozen_qualification_exhausts_the_exact_nonvacuous_low_word_space():
    result = composite.run_frozen_single_macrostep_qualification(test29, test30)
    assert type(result) is composite.FrozenSingleMacrostepQualification
    assert result.passed is True
    assert result.low_word_cases_checked == 16
    assert result.route_family_counts == (
        ("birth", 8),
        ("death", 4),
        ("replacement", 4),
    )
    assert result.final_cardinality_counts == ((1, 4), (2, 4), (3, 8))
    assert result.source_serial_counts == ((1, 4), (2, 4))
    assert result.normal_cell_counts == ((0, 6), (1, 6))
    assert result.distinct_input_sha256_count == 16
    assert result.distinct_report_sha256_count == 16
    assert len(result.case_input_sha256s) == 16
    assert len(result.case_report_sha256s) == 16
    assert len(set(result.case_input_sha256s)) == 16
    assert len(set(result.case_report_sha256s)) == 16
    assert result.report_sha256 == (
        "ccf2639c539d312463209bd165cc288df1ba77518f1d31aa7e616df18b66455f"
    )
    assert (
        composite.validate_frozen_single_macrostep_qualification(test29, test30, result)
        is result
    )
    assert (
        composite.recompute_frozen_single_macrostep_qualification_report_sha256(result)
        == result.report_sha256
    )


@pytest.mark.parametrize(
    ("word", "family", "source", "cell", "cardinality"),
    (
        (0, "birth", None, (0,), 3),
        (1, "birth", None, (0,), 3),
        (2, "replacement", 1, (0,), 2),
        (3, "death", 1, (), 1),
        (4, "birth", None, (0,), 3),
        (5, "birth", None, (0,), 3),
        (6, "replacement", 2, (0,), 2),
        (7, "death", 2, (), 1),
        (8, "birth", None, (1,), 3),
        (9, "birth", None, (1,), 3),
        (10, "replacement", 1, (1,), 2),
        (11, "death", 1, (), 1),
        (12, "birth", None, (1,), 3),
        (13, "birth", None, (1,), 3),
        (14, "replacement", 2, (1,), 2),
        (15, "death", 2, (), 1),
    ),
)
def test_each_low_word_has_exact_route_source_cell_and_lineage_shape(
    word: int,
    family: str,
    source: Any,
    cell: Any,
    cardinality: int,
):
    result = _run(word)
    assert type(result) is composite.SingleMacrostepResult
    assert result.passed is True
    assert result.family == family
    assert result.source_serial == source
    assert result.normal_cell_indices == cell
    assert len(result.state_after_right) == cardinality
    assert result.left_heun_application_count == 2
    assert result.central_jump_count == 1
    assert result.right_heun_application_count == cardinality
    assert result.address_count == 3 + cardinality
    assert result.address_identities_unique is True
    assert result.lineage_matches_test29 is True


def test_exact_replacement_case_receipt_and_physical_heun_coordinates():
    result = _run(2)
    assert result.input_sha256 == (
        "9593712e78babf05ce8f8b4f2faf4d255d890ce8c519023038e5af1b8e17ff14"
    )
    assert result.report_sha256 == (
        "870861f8dd42b7ba16032c2ed37561acdefd9e7ccab0baf197ba7f73c6354b5b"
    )
    assert (
        composite.validate_single_macrostep_result(test29, test30, _frozen(2), result)
        is result
    )
    assert composite.recompute_single_macrostep_report_sha256(result) == (
        result.report_sha256
    )
    assert result.state_before == ((1, "A", 0.75), (2, "B", -0.4))
    assert [(s, k, x.hex()) for s, k, x in result.state_after_left] == [
        (1, "A", "0x1.4a24dd2f1a9fcp-1"),
        (2, "B", "-0x1.8cbf7ced91688p-2"),
    ]
    assert [(s, k, x.hex()) for s, k, x in result.state_after_jump] == [
        (2, "B", "-0x1.8cbf7ced91688p-2"),
        (3, "B", "-0x1.d956b87528a49p-1"),
    ]
    assert [(s, k, x.hex()) for s, k, x in result.state_after_right] == [
        (2, "B", "-0x1.3788069d7342fp-2"),
        (3, "B", "-0x1.c8af0124cbbe0p-1"),
    ]


def test_case_report_payload_binds_every_material_result_field():
    result = _run(2)
    payload = composite._single_macrostep_report_payload(result)
    bound_fields = (set(payload) - {"macrostep_width_hex"}) | {"macrostep_width"}
    assert bound_fields == set(result.__dataclass_fields__) - {"report_sha256"}
    mutations = (
        replace(result, scope=result.scope + ";HOSTILE"),
        replace(result, failure_policy=result.failure_policy + "_HOSTILE"),
        replace(
            result,
            state_after_right=result.state_after_right[:-1]
            + ((3, "B", result.state_after_right[-1][2] + 0.125),),
        ),
        replace(result, address_count=result.address_count + 1),
        replace(result, address_identities_unique=False),
        replace(result, lineage_matches_test29=False),
        replace(result, formal_test29_closed=True),
        replace(result, live_cp24_stream_consumed=True),
        replace(result, passed=False),
    )
    for hostile in mutations:
        assert (
            composite.recompute_single_macrostep_report_sha256(hostile)
            != result.report_sha256
        )
        with pytest.raises((TypeError, ValueError)):
            composite.validate_single_macrostep_result(
                test29, test30, _frozen(2), hostile
            )


def test_context_validation_rejects_redigested_case_relation_mutations():
    supplied = _frozen(2)
    result = _run(2)
    other_input_sha256 = _run(3).input_sha256
    mutations = (
        replace(
            result,
            state_after_right=result.state_after_right[:-1]
            + ((3, "B", result.state_after_right[-1][2] + 0.125),),
        ),
        replace(result, route_id="macro-birth"),
        replace(result, family="birth"),
        replace(result, source_index=1),
        replace(result, source_serial=2),
        replace(result, created_serial=4),
        replace(result, normal_cell_indices=(1,)),
        replace(result, input_sha256=other_input_sha256),
    )
    for hostile in mutations:
        redigested = replace(
            hostile,
            report_sha256=composite.recompute_single_macrostep_report_sha256(hostile),
        )
        assert (
            composite._validate_single_macrostep_result_structure(redigested)
            is redigested
        )
        with pytest.raises(
            composite.SyntheticSingleMacrostepError,
            match="differs",
        ):
            composite.validate_single_macrostep_result(
                test29,
                test30,
                supplied,
                redigested,
            )
    with pytest.raises(composite.SyntheticSingleMacrostepError, match="differs"):
        composite.validate_single_macrostep_result(
            test29,
            test30,
            _frozen(3),
            result,
        )


def test_qualification_report_payload_binds_every_material_aggregate_field():
    result = composite.run_frozen_single_macrostep_qualification(test29, test30)
    payload = composite._qualification_report_payload(result)
    assert set(payload) == set(result.__dataclass_fields__) - {"report_sha256"}
    mutations = (
        replace(result, scope=result.scope + ";HOSTILE"),
        replace(result, failure_policy=result.failure_policy + "_HOSTILE"),
        replace(result, low_word_cases_checked=15),
        replace(result, case_input_sha256s=result.case_input_sha256s[::-1]),
        replace(result, case_report_sha256s=result.case_report_sha256s[::-1]),
        replace(result, every_case_address_unique=False),
        replace(result, every_case_lineage_matches_test29=False),
        replace(result, live_parent_stream_consumed=True),
        replace(result, formal_tests_closed=1),
        replace(result, passed=False),
    )
    for hostile in mutations:
        assert (
            composite.recompute_frozen_single_macrostep_qualification_report_sha256(
                hostile
            )
            != result.report_sha256
        )
        with pytest.raises((TypeError, ValueError)):
            composite.validate_frozen_single_macrostep_qualification(
                test29, test30, hostile
            )


def test_context_validation_rejects_redigested_qualification_case_hash_changes():
    result = composite.run_frozen_single_macrostep_qualification(test29, test30)
    mutations = (
        replace(result, case_input_sha256s=result.case_input_sha256s[::-1]),
        replace(result, case_report_sha256s=result.case_report_sha256s[::-1]),
        replace(
            result,
            case_input_sha256s=("0" * 64,) + result.case_input_sha256s[1:],
        ),
        replace(
            result,
            case_report_sha256s=("1" * 64,) + result.case_report_sha256s[1:],
        ),
    )
    for hostile in mutations:
        redigested = replace(
            hostile,
            report_sha256=(
                composite.recompute_frozen_single_macrostep_qualification_report_sha256(
                    hostile
                )
            ),
        )
        assert (
            composite._validate_frozen_single_macrostep_qualification_structure(
                redigested
            )
            is redigested
        )
        with pytest.raises(
            composite.SyntheticSingleMacrostepError,
            match="differs",
        ):
            composite.validate_frozen_single_macrostep_qualification(
                test29,
                test30,
                redigested,
            )


def test_execution_cores_do_not_recurse_through_public_run_or_validation(monkeypatch):
    supplied = _frozen(2)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("nonrecursive core called a public run or validator")

    monkeypatch.setattr(composite, "run_supplied_single_macrostep", forbidden)
    monkeypatch.setattr(composite, "validate_single_macrostep_result", forbidden)
    monkeypatch.setattr(
        composite,
        "validate_frozen_single_macrostep_qualification",
        forbidden,
    )
    case = composite._execute_single_macrostep_core(test29, test30, supplied)
    qualification = composite._execute_frozen_single_macrostep_qualification_core(
        test29,
        test30,
    )
    assert case.passed is True
    assert qualification.passed is True


def test_all_broader_claim_flags_and_project_deltas_remain_false_or_zero():
    result = _run()
    for field in (
        "test28_initializer_admissible",
        "live_cp23_stream_consumed",
        "live_cp24_stream_consumed",
        "continuous_gaussian_destination_sampled",
        "waiting_clock_or_acceptance_thinning_executed",
        "general_strang_path_integrated",
        "formal_test28_closed",
        "formal_test29_closed",
        "formal_test30_closed",
    ):
        assert getattr(result, field) is False
    qualification = composite.run_frozen_single_macrostep_qualification(test29, test30)
    for field in (
        "formal_tests_closed",
        "fields_closed",
        "blockers_closed",
        "result_slots_filled",
        "tracker_files_edited",
    ):
        assert getattr(qualification, field) == 0


def test_addresses_are_exact_cp23_left_cp24_central_cp23_right_and_disjoint():
    supplied = _frozen(0)
    identities = []
    for item in supplied.left_increments:
        assert item.address.domain == "brownian_left"
        assert item.address.domain_tag == 4
        assert item.address.philox_key == (29030, 4)
        identities.append((item.address.philox_key, item.address.philox_counter))
    assert supplied.central_word.address.key == (29030, 6)
    assert supplied.central_word.address.counter == (0, 0, 0, 0)
    identities.append(
        (supplied.central_word.address.key, supplied.central_word.address.counter)
    )
    for item in supplied.right_increments:
        assert item.address.domain == "brownian_right"
        assert item.address.domain_tag == 5
        assert item.address.philox_key == (29030, 5)
        identities.append((item.address.philox_key, item.address.philox_counter))
    assert len(identities) == len(set(identities))


def test_upper_word_bits_do_not_change_selection_but_remain_input_committed():
    low = _run(2)
    high = _run((1 << 63) + 2)
    for field in (
        "route_id",
        "family",
        "source_index",
        "source_serial",
        "created_serial",
        "normal_cell_indices",
        "state_after_left",
        "state_after_jump",
        "state_after_right",
    ):
        assert getattr(low, field) == getattr(high, field)
    assert low.input_sha256 != high.input_sha256
    assert low.report_sha256 != high.report_sha256


@pytest.mark.parametrize(
    "field,value,error",
    (
        ("run_id", True, TypeError),
        ("step_index", -1, ValueError),
        ("macrostep_width", 1, TypeError),
        ("macrostep_width", 0.0, ValueError),
        ("macrostep_width", math.inf, ValueError),
        ("left_increments", [], TypeError),
        ("right_increments", [], TypeError),
    ),
)
def test_public_input_constructor_rejects_noncanonical_or_unbounded_fields(
    field: str, value: Any, error: Any
):
    supplied = _frozen()
    with pytest.raises(error):
        replace(supplied, **{field: value})


@pytest.mark.parametrize("word", (True, -1, 1 << 64))
def test_raw_word_must_be_an_exact_uint64(word: Any):
    with pytest.raises((TypeError, ValueError)):
        composite.build_frozen_single_macrostep_input(test29, test30, word)


def test_public_inputs_reject_integer_float_tuple_and_input_subclasses():
    class StrangeInput(composite.SuppliedSingleMacrostepInput):
        pass

    with pytest.raises(TypeError):
        composite.build_frozen_single_macrostep_input(test29, test30, StrangeInt(2))
    supplied = _frozen()
    with pytest.raises(TypeError):
        replace(supplied, macrostep_width=StrangeFloat(0.25))
    with pytest.raises(TypeError):
        replace(supplied, left_increments=StrangeTuple(supplied.left_increments))
    strange = StrangeInput(
        supplied.run_id,
        supplied.step_index,
        supplied.macrostep_width,
        supplied.left_increments,
        supplied.central_word,
        supplied.right_increments,
    )
    with pytest.raises(TypeError, match="exact SuppliedSingleMacrostepInput"):
        composite.run_supplied_single_macrostep(test29, test30, strange)


def test_run_boundary_revalidates_mutated_supplied_scalars_and_tuple_rosters():
    supplied = _frozen()
    hostiles = (
        _mutated_dataclass(supplied, "run_id", StrangeInt(supplied.run_id)),
        _mutated_dataclass(supplied, "step_index", False),
        _mutated_dataclass(
            supplied, "macrostep_width", StrangeFloat(supplied.macrostep_width)
        ),
        _mutated_dataclass(
            supplied, "left_increments", StrangeTuple(supplied.left_increments)
        ),
        _mutated_dataclass(
            supplied, "right_increments", StrangeTuple(supplied.right_increments)
        ),
    )
    for hostile in hostiles:
        with pytest.raises(TypeError):
            composite.run_supplied_single_macrostep(test29, test30, hostile)


def _supplied_with_left_increment(supplied: Any, increment: Any) -> Any:
    return replace(
        supplied,
        left_increments=(increment,) + supplied.left_increments[1:],
    )


def test_run_boundary_revalidates_every_consumed_cp23_address_component():
    supplied = _frozen(0)
    item = supplied.left_increments[0]
    address = item.address
    address_mutations = (
        ("domain", StrangeText(address.domain)),
        ("domain_tag", StrangeInt(address.domain_tag)),
        ("run_id", StrangeInt(address.run_id)),
        ("step_index", False),
        ("occurrence_serial", True),
        ("proposal_index", False),
        ("philox_key", (StrangeInt(address.run_id), address.domain_tag)),
        (
            "philox_counter",
            (False, address.step_index, address.occurrence_serial, 0),
        ),
        ("philox_key", StrangeTuple(address.philox_key)),
        ("philox_counter", StrangeTuple(address.philox_counter)),
    )
    for field, hostile_value in address_mutations:
        hostile_address = _mutated_dataclass(address, field, hostile_value)
        hostile_item = _mutated_dataclass(item, "address", hostile_address)
        with pytest.raises(TypeError):
            composite.run_supplied_single_macrostep(
                test29,
                test30,
                _supplied_with_left_increment(supplied, hostile_item),
            )

    hostile_item = _mutated_dataclass(item, "increment", StrangeFloat(item.increment))
    with pytest.raises(TypeError):
        composite.run_supplied_single_macrostep(
            test29,
            test30,
            _supplied_with_left_increment(supplied, hostile_item),
        )


def test_run_boundary_rejects_cp23_increment_and_address_subclasses():
    class StrangeAddress(test30.CP23BrownianAddress):
        pass

    class StrangeIncrement(test30.AddressedBrownianIncrement):
        pass

    supplied = _frozen(0)
    item = supplied.left_increments[0]
    address = item.address
    strange_address = StrangeAddress(
        domain=address.domain,
        domain_tag=address.domain_tag,
        run_id=address.run_id,
        step_index=address.step_index,
        occurrence_serial=address.occurrence_serial,
        proposal_index=address.proposal_index,
        philox_key=address.philox_key,
        philox_counter=address.philox_counter,
    )
    hostile_address_item = _mutated_dataclass(item, "address", strange_address)
    strange_increment = StrangeIncrement(item.address, item.increment)
    for hostile_item in (hostile_address_item, strange_increment):
        with pytest.raises(TypeError):
            composite.run_supplied_single_macrostep(
                test29,
                test30,
                _supplied_with_left_increment(supplied, hostile_item),
            )


def test_run_boundary_revalidates_every_consumed_cp24_word_component():
    supplied = _frozen(0)
    word = supplied.central_word
    address = word.address
    address_mutations = (
        ("run_id", StrangeInt(address.run_id)),
        ("step_index", False),
        ("completed_proposals", False),
    )
    for field, hostile_value in address_mutations:
        hostile_address = _mutated_dataclass(address, field, hostile_value)
        hostile_word = _mutated_dataclass(word, "address", hostile_address)
        hostile = _mutated_dataclass(supplied, "central_word", hostile_word)
        with pytest.raises(TypeError):
            composite.run_supplied_single_macrostep(test29, test30, hostile)

    hostile_word = _mutated_dataclass(word, "raw64_word", StrangeInt(0))
    with pytest.raises(TypeError):
        composite.run_supplied_single_macrostep(
            test29,
            test30,
            _mutated_dataclass(supplied, "central_word", hostile_word),
        )


def test_run_boundary_rejects_cp24_address_and_word_subclasses():
    class StrangeCentralAddress(test29.CP24CompatibleAddress):
        pass

    class StrangeCentralWord(test29.AddressedUint64Word):
        pass

    supplied = _frozen()
    word = supplied.central_word
    address = word.address
    strange_address = StrangeCentralAddress(
        address.run_id,
        address.step_index,
        address.completed_proposals,
    )
    hostile_address_word = _mutated_dataclass(word, "address", strange_address)
    strange_word = StrangeCentralWord(address, word.raw64_word)
    for hostile_word in (hostile_address_word, strange_word):
        hostile = _mutated_dataclass(supplied, "central_word", hostile_word)
        with pytest.raises(TypeError):
            composite.run_supplied_single_macrostep(test29, test30, hostile)


def test_public_result_validators_reject_result_subclasses_and_mutated_types():
    class StrangeCaseResult(composite.SingleMacrostepResult):
        pass

    class StrangeQualification(composite.FrozenSingleMacrostepQualification):
        pass

    case = _run()
    qualification = composite.run_frozen_single_macrostep_qualification(test29, test30)
    with pytest.raises(TypeError):
        composite.validate_single_macrostep_result(
            test29,
            test30,
            _frozen(),
            StrangeCaseResult(**case.__dict__),
        )
    with pytest.raises(TypeError):
        composite.validate_frozen_single_macrostep_qualification(
            test29,
            test30,
            StrangeQualification(**qualification.__dict__),
        )
    case_hostiles = (
        _mutated_dataclass(case, "scope", StrangeText(case.scope)),
        _mutated_dataclass(case, "address_count", StrangeInt(case.address_count)),
        _mutated_dataclass(case, "passed", 1),
        _mutated_dataclass(
            case, "state_after_right", StrangeTuple(case.state_after_right)
        ),
    )
    for hostile in case_hostiles:
        with pytest.raises(TypeError):
            composite.validate_single_macrostep_result(
                test29, test30, _frozen(), hostile
            )
    qualification_hostiles = (
        _mutated_dataclass(
            qualification,
            "low_word_cases_checked",
            StrangeInt(qualification.low_word_cases_checked),
        ),
        _mutated_dataclass(qualification, "passed", 1),
        _mutated_dataclass(
            qualification,
            "case_report_sha256s",
            StrangeTuple(qualification.case_report_sha256s),
        ),
    )
    for hostile in qualification_hostiles:
        with pytest.raises(TypeError):
            composite.validate_frozen_single_macrostep_qualification(
                test29, test30, hostile
            )


def test_missing_extra_duplicate_and_reordered_left_or_right_rosters_fail_closed():
    supplied = _frozen(0)
    variants = (
        replace(supplied, left_increments=supplied.left_increments[:-1]),
        replace(
            supplied,
            left_increments=supplied.left_increments + (supplied.left_increments[-1],),
        ),
        replace(
            supplied,
            left_increments=(
                supplied.left_increments[1],
                supplied.left_increments[0],
            ),
        ),
        replace(supplied, right_increments=supplied.right_increments[:-1]),
        replace(
            supplied,
            right_increments=supplied.right_increments
            + (supplied.right_increments[-1],),
        ),
        replace(
            supplied,
            right_increments=(
                supplied.right_increments[1],
                supplied.right_increments[0],
            )
            + supplied.right_increments[2:],
        ),
    )
    for hostile in variants:
        with pytest.raises(composite.SyntheticSingleMacrostepError):
            composite.run_supplied_single_macrostep(test29, test30, hostile)


def test_wrong_run_step_and_central_address_fail_closed():
    supplied = _frozen()
    for hostile in (
        replace(supplied, run_id=29031),
        replace(supplied, step_index=1),
        replace(
            supplied,
            central_word=test29.AddressedUint64Word(
                test29.CP24CompatibleAddress(29031, 0, 0), 2
            ),
        ),
        replace(
            supplied,
            central_word=test29.AddressedUint64Word(
                test29.CP24CompatibleAddress(29030, 0, 1), 2
            ),
        ),
    ):
        with pytest.raises(composite.SyntheticSingleMacrostepError):
            composite.run_supplied_single_macrostep(test29, test30, hostile)


def _coherent_brownian_address(item, **changes):
    address = item.address
    tag = changes.get("domain_tag", address.domain_tag)
    run = changes.get("run_id", address.run_id)
    step = changes.get("step_index", address.step_index)
    serial = changes.get("occurrence_serial", address.occurrence_serial)
    proposal = changes.get("proposal_index", address.proposal_index)
    return test30.CP23BrownianAddress(
        domain=changes.get("domain", address.domain),
        domain_tag=tag,
        run_id=run,
        step_index=step,
        occurrence_serial=serial,
        proposal_index=proposal,
        philox_key=(run, tag),
        philox_counter=(0, step, serial, proposal),
    )


def test_wrong_but_internally_canonical_brownian_addresses_fail_roster_preflight():
    supplied = _frozen(0)
    left = supplied.left_increments[0]
    wrong_run = replace(left, address=_coherent_brownian_address(left, run_id=29031))
    wrong_step = replace(left, address=_coherent_brownian_address(left, step_index=1))
    wrong_serial = replace(
        left, address=_coherent_brownian_address(left, occurrence_serial=2)
    )
    for item in (wrong_run, wrong_step, wrong_serial):
        hostile = replace(
            supplied, left_increments=(item,) + supplied.left_increments[1:]
        )
        with pytest.raises(composite.SyntheticSingleMacrostepError):
            composite.run_supplied_single_macrostep(test29, test30, hostile)


def test_tampered_cross_domain_key_counter_collision_is_rejected():
    supplied = _frozen(0)
    left = supplied.left_increments[0]
    tampered_address = replace(left.address)
    object.__setattr__(tampered_address, "domain", "brownian_right")
    object.__setattr__(tampered_address, "domain_tag", 6)
    object.__setattr__(tampered_address, "philox_key", (29030, 6))
    object.__setattr__(tampered_address, "philox_counter", (0, 0, 0, 0))
    collided = replace(left, address=tampered_address)
    hostile = replace(
        supplied, left_increments=(collided,) + supplied.left_increments[1:]
    )
    with pytest.raises(composite.SyntheticSingleMacrostepError):
        composite.run_supplied_single_macrostep(test29, test30, hostile)


def test_all_input_rosters_are_preflighted_before_any_heun_arithmetic(monkeypatch):
    supplied = _frozen(0)
    hostile = replace(supplied, right_increments=supplied.right_increments[:-1])
    calls = []

    def forbidden_heun(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Heun arithmetic ran before complete preflight")

    monkeypatch.setattr(test30, "_heun_half", forbidden_heun)
    with pytest.raises(composite.SyntheticSingleMacrostepError):
        composite.run_supplied_single_macrostep(test29, test30, hostile)
    assert calls == []


@pytest.mark.parametrize("value", (True, math.inf, -math.inf, math.nan))
def test_nonfinite_or_boolean_increment_payloads_fail_before_execution(value: Any):
    supplied = _frozen()
    with pytest.raises((TypeError, ValueError)):
        replace(supplied.left_increments[0], increment=value)


def test_parent_modules_require_exact_module_schema_and_required_symbol_presence():
    with pytest.raises(TypeError):
        composite.run_frozen_single_macrostep_qualification(object(), test30)
    fake29 = ModuleType("fake29")
    fake29.FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION = "wrong"
    with pytest.raises(composite.SyntheticSingleMacrostepError, match="schema"):
        composite.run_frozen_single_macrostep_qualification(fake29, test30)
    fake30 = ModuleType("fake30")
    fake30.SCHEMA_VERSION = composite.EXPECTED_TEST30_SCHEMA
    with pytest.raises(composite.SyntheticSingleMacrostepError, match="symbol"):
        composite.run_frozen_single_macrostep_qualification(test29, fake30)


def test_source_ast_has_stdlib_only_no_rng_network_process_or_writer_surface():
    source = ROOT / (
        "src/heterodiff/evaluation/"
        "formal_test29_test30_single_macrostep_integration.py"
    )
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    assert imports <= {
        "__future__",
        "dataclasses",
        "fractions",
        "hashlib",
        "json",
        "math",
        "types",
        "typing",
    }
    assert not imports.intersection(
        {"random", "secrets", "numpy", "requests", "socket", "subprocess"}
    )
    assert not calls.intersection(
        {"open", "write", "write_text", "write_bytes", "system", "popen"}
    )


def test_canonical_five_file_package_validates_with_only_the_narrow_control(
    validator: ModuleType,
):
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": composite.PREDICATE,
        "eligible_after_independent_audit": True,
        "formal_test28": "OPEN",
        "formal_test29": "OPEN",
        "formal_test30": "PENDING",
        "formal_tests_closed": 0,
        "existing_fields_closed": 0,
        "blockers_closed": 0,
        "result_slots_filled": 0,
        "scientific_effect": 0,
        "tracker_files_edited": 0,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_exact_parent_and_package_rosters_are_custody_bound(validator: ModuleType):
    record = validator.expected_record()
    assert record["scope_review"]["physical_file_count"] == 5
    assert record["scope_review"]["parent_package_count"] == 2
    assert record["scope_review"]["parent_file_count"] == 10
    assert record["scope_review"]["hard_pinned_before_execution_count"] == 12
    assert len(record["parent_bindings"]) == 10
    assert len(record["package_bindings"]) == 4
    for row in record["parent_bindings"]:
        assert row["raw_sha256"] == validator.PARENT_EXPECTED_SHA256[row["path"]]


def test_exact_receipts_and_all_nonclosures_are_machine_bound(
    validator: ModuleType,
):
    record = validator.expected_record()
    receipt = record["qualification_receipt"]
    assert receipt["report_sha256"] == (
        "ccf2639c539d312463209bd165cc288df1ba77518f1d31aa7e616df18b66455f"
    )
    assert receipt["route_family_counts"] == [
        ["birth", 8],
        ["death", 4],
        ["replacement", 4],
    ]
    assert receipt["test28_initializer_admissible"] is False
    assert receipt["formal_tests_closed"] == 0
    assert receipt["tracker_files_edited"] == 0
    for value in record["strict_nonclaims"].values():
        assert value is False
    effects = record["control_effects"]
    assert effects["tracker_edited"] is False
    for field in (
        "formal_tests_closed",
        "existing_fields_closed",
        "blockers_closed",
        "result_slots_filled",
        "scientific_results_produced",
    ):
        assert effects[field] == 0
    contract = record["integration_contract"]
    assert contract["case_validation_requires_supplied_input_and_parent_apis"] is True
    assert contract["case_validation_reconstructs_with_nonrecursive_core"] is True
    assert (
        contract["qualification_validation_reruns_sixteen_ordered_canonical_cases"]
        is True
    )
    assert (
        contract["semantic_validation_strict_compares_every_field_and_digest"] is True
    )
    assert contract["digest_recomputation_alone_is_semantic_validation"] is False


def test_internal_publication_and_authority_boundaries_are_fail_closed(
    validator: ModuleType,
):
    record = validator.expected_record()
    authority = record["authority_provenance"]
    raw = authority["normalized_visible_text"].encode("utf-8")
    assert hashlib.sha256(raw).hexdigest() == validator.AUTHORITY_SHA256
    assert authority["continued_bounded_local_project_work_authorized"] is True
    for key, value in authority.items():
        if key.endswith("_authorized") and key != (
            "continued_bounded_local_project_work_authorized"
        ):
            assert value is False
    publication = record["publication_boundary"]
    assert publication["internal_evidence_only"] is True
    assert publication["anonymous_or_public_inclusion_permitted"] is False
    assert publication["publication_safe_derivative_required"] is True
    assert publication["fresh_anonymity_audit_required"] is True
    assert publication["visible_authority_text_permitted_in_derivative"] is False
    assert (
        publication["internal_paths_hashes_or_receipts_permitted_in_derivative"]
        is False
    )


def test_verified_byte_execution_custody_has_no_path_or_pyc_loader(
    validator: ModuleType,
):
    custody = validator.expected_record()["source_execution_custody"]
    assert custody["hard_pinned_before_any_source_execution"] is True
    assert custody["all_parent_five_file_pins_checked"] is True
    assert custody["stable_read_verified_parent_payloads_executed_directly"] is True
    assert custody["stable_read_verified_composite_payload_executed_directly"] is True
    assert custody["source_path_reopened_for_execution"] is False
    assert custody["cached_bytecode_loader_used"] is False
    assert custody["importlib_path_loader_used"] is False


def test_validator_rejects_a_name_only_qualification_result_impostor(
    validator: ModuleType,
):
    expected_type = type("ExpectedQualification", (), {})
    impostor_type = type("FrozenSingleMacrostepQualification", (), {})
    fake = ModuleType("qualification_result_impostor")
    fake.FrozenSingleMacrostepQualification = expected_type
    fake.run_frozen_single_macrostep_qualification = lambda *_: impostor_type()
    with pytest.raises(validator.ValidationError, match="another qualification type"):
        validator._qualification_receipt(fake, test29, test30)


def test_validator_rejects_a_name_only_case_result_impostor(validator: ModuleType):
    expected_type = type("ExpectedCaseResult", (), {})
    impostor_type = type("SingleMacrostepResult", (), {})
    fake = ModuleType("case_result_impostor")
    fake.SingleMacrostepResult = expected_type
    fake.build_frozen_single_macrostep_input = (
        composite.build_frozen_single_macrostep_input
    )
    fake.run_supplied_single_macrostep = lambda *_: impostor_type()
    with pytest.raises(validator.ValidationError, match="another case-result type"):
        validator._case_receipt(fake, test29, test30)


@pytest.mark.parametrize(
    ("pointer", "value"),
    (
        ("state", "FORMAL_TESTS_COMPLETE"),
        ("global_state", "EXECUTABLE"),
        ("scope_review.physical_file_count", 6),
        ("authority_provenance.scientific_execution_authorized", True),
        ("publication_boundary.anonymous_or_public_inclusion_permitted", True),
        ("formal_test_states.formal_test28_after", "PASS"),
        ("formal_test_states.formal_test29_after", "PASS"),
        ("formal_test_states.formal_test30_after", "PASS"),
        ("qualification_receipt.low_word_cases_checked", 15),
        ("qualification_receipt.report_sha256", "0" * 64),
        ("case_receipt.family", "birth"),
        (
            "integration_contract.qualification_validation_reruns_sixteen_ordered_canonical_cases",
            False,
        ),
        (
            "integration_contract.digest_recomputation_alone_is_semantic_validation",
            True,
        ),
        ("control_effects.formal_tests_closed", 1),
        ("control_effects.tracker_edited", True),
        ("remaining_gaps", []),
    ),
)
def test_rehashed_semantic_machine_mutations_are_rejected(
    validator: ModuleType, tmp_path: Path, pointer: str, value: Any
):
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace_pointer(record, pointer, value),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize(
    "field",
    (
        "test28_initializer_admitted",
        "live_cp23_stream_consumed",
        "live_cp24_stream_consumed",
        "brownian_or_independence_law_certified",
        "continuous_gaussian_destination_sampled",
        "waiting_clock_acceptance_or_thinning_executed",
        "general_strang_path_integrated",
        "independent_scientific_recomputation_present",
        "formal_test28_closed",
        "formal_test29_closed",
        "formal_test30_closed",
        "tracker_edit_authorized",
        "arbitrary_parent_modules_authenticated",
        "no_effect_claim_applies_to_arbitrary_parent_modules",
    ),
)
def test_each_negative_claim_flip_is_rejected_after_machine_redigest(
    validator: ModuleType, tmp_path: Path, field: str
):
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace_pointer(record, "strict_nonclaims." + field, True),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_wrong_self_digest_and_noncanonical_machine_bytes_are_rejected(
    validator: ModuleType, tmp_path: Path
):
    root = _copy_package(validator, tmp_path / "digest")
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace_pointer(record, "state", "OTHER"),
        redigest=False,
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)
    root = _copy_package(validator, tmp_path / "canonical")
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize("relative", EXECUTION_PIN_PATHS)
def test_hard_pins_reject_coherent_rebinding_before_any_execution(
    validator: ModuleType, tmp_path: Path, relative: str
):
    root = _copy_package(validator, tmp_path)
    path = root / relative
    raw = path.read_bytes() + b"\n# coherent drift must still fail\n"
    path.write_bytes(raw)
    path.chmod(0o644)
    _rewrite_machine(
        validator,
        root,
        lambda record: _coherently_rebind(record, relative, raw),
    )
    with pytest.raises(validator.ValidationError, match="hard-pinned SHA-256"):
        validator.validate(root)


@pytest.mark.parametrize("relative", EXECUTABLE_SOURCE_PIN_PATHS)
def test_effectful_coherently_rebound_source_never_executes(
    validator: ModuleType, tmp_path: Path, relative: str
):
    root = _copy_package(validator, tmp_path)
    path = root / relative
    marker = tmp_path / ("effectful-source-must-not-execute-" + str(len(relative)))
    raw = path.read_bytes() + (
        "\nfrom pathlib import Path\n"
        + "Path("
        + repr(str(marker))
        + ").write_text('executed')\n"
    ).encode("utf-8")
    path.write_bytes(raw)
    path.chmod(0o644)
    _rewrite_machine(
        validator,
        root,
        lambda record: _coherently_rebind(record, relative, raw),
    )
    with pytest.raises(validator.ValidationError, match="hard-pinned SHA-256"):
        validator.validate(root)
    assert not marker.exists()


def test_verified_payload_loader_ignores_alternate_path_and_cached_bytecode(
    validator: ModuleType, tmp_path: Path
):
    marker = tmp_path / "unbound-path-or-pyc-executed"
    hostile = tmp_path / "hostile.py"
    hostile.write_text(
        "from pathlib import Path\n"
        + "Path("
        + repr(str(marker))
        + ").write_text('executed')\n",
        encoding="utf-8",
    )
    hostile.chmod(0o644)
    py_compile.compile(str(hostile), doraise=True)
    verified = (ROOT / validator.SOURCE_PATH).read_bytes()
    loaded = validator._load_verified_module(
        verified,
        logical_path=str(hostile),
        expected_sha256=validator.EXPECTED_SOURCE_SHA256,
        module_stem="alternate_path_nonexecution",
        inspect_composite_safety=True,
    )
    assert loaded.SCHEMA_VERSION == composite.SCHEMA_VERSION
    assert not marker.exists()


def test_forbidden_composite_import_is_rejected_by_source_safety(
    validator: ModuleType,
):
    raw = (ROOT / validator.SOURCE_PATH).read_bytes() + b"\nimport random\n"
    with pytest.raises(validator.ValidationError, match="forbidden module"):
        validator._source_safety(raw)


def test_symlink_hardlink_and_executable_mode_fail_custody(
    validator: ModuleType, tmp_path: Path
):
    root = _copy_package(validator, tmp_path / "symlink")
    human = root / validator.HUMAN_PATH
    target = root / "human-copy"
    target.write_bytes(human.read_bytes())
    target.chmod(0o644)
    human.unlink()
    human.symlink_to(target)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)

    root = _copy_package(validator, tmp_path / "hardlink")
    source = root / validator.SOURCE_PATH
    os.link(source, root / "source-hardlink")
    with pytest.raises(validator.ValidationError):
        validator.validate(root)

    root = _copy_package(validator, tmp_path / "mode")
    (root / validator.VALIDATOR_PATH).chmod(0o755)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_unsafe_relative_paths_fail_closed(validator: ModuleType):
    for hostile in ("", ".", "..", "../escape", "/absolute", "a//b", "a/./b"):
        with pytest.raises(validator.ValidationError):
            validator._safe_relative_path(ROOT, hostile)


def test_validation_is_read_only(validator: ModuleType):
    paths = [ROOT / relative for relative in _roster(validator)]
    before = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in paths
    }
    validator.validate()
    after = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in paths
    }
    assert before == after


def test_validator_runs_from_an_unrelated_current_directory(
    validator: ModuleType, tmp_path: Path
):
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(ROOT / VALIDATOR_REL)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "FORMAL_TEST29_TEST30_SINGLE_MACROSTEP_VALIDATION_PASS" in completed.stdout
