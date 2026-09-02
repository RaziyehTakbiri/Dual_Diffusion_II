"""Hostile tests for the nonconfirmatory Formal-Test-28--30 route."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import re
import shutil
import sys
from types import ModuleType, SimpleNamespace

import pytest

from heterodiff.evaluation import formal_test28_30_nonconfirmatory_route as route


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    ROOT
    / "research/diagnostics/"
    "manuscript_v3_formal_test28_30_nonconfirmatory_route_candidate_v1.py"
)


def _copy(relative: str, target: Path) -> Path:
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / relative, destination)
    destination.chmod(0o644)
    return destination


def _resign(
    value: route.NonconfirmatoryRouteReceipt,
) -> route.NonconfirmatoryRouteReceipt:
    zeroed = dataclasses.replace(value, receipt_sha256="0" * 64)
    return dataclasses.replace(
        zeroed,
        receipt_sha256=route._sha256(
            route.RECEIPT_DOMAIN + route._canonical_json_bytes(zeroed)
        ),
    )


def _load_validator(name: str):
    spec = importlib.util.spec_from_file_location(name, VALIDATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name, dataclasses.MISSING)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is dataclasses.MISSING:
            del sys.modules[name]
        else:
            sys.modules[name] = previous
        raise
    return module


@pytest.fixture(scope="module")
def exact_receipt() -> route.NonconfirmatoryRouteReceipt:
    return route.run_nonconfirmatory_test28_30_route(str(ROOT))


def test_public_surface_and_signatures_are_exact() -> None:
    expected = {
        "NonconfirmatoryRouteError",
        "SourcePin",
        "CP63NonconfirmatoryExecutionBinding",
        "TwoMacrostepExecutionBinding",
        "WholeMethodExecutionBinding",
        "NonconfirmatoryRouteReceipt",
        "SCHEMA_VERSION",
        "STATE",
        "PROPOSED_TIMETABLE_TASK",
        "run_nonconfirmatory_test28_30_route",
        "validate_nonconfirmatory_test28_30_route_receipt",
        "route_receipt_canonical_json_bytes",
    }
    assert set(route.__all__) == expected
    assert tuple(
        inspect.signature(route.run_nonconfirmatory_test28_30_route).parameters
    ) == ("project_root",)
    assert tuple(
        inspect.signature(
            route.validate_nonconfirmatory_test28_30_route_receipt
        ).parameters
    ) == ("receipt",)
    assert tuple(
        inspect.signature(route.route_receipt_canonical_json_bytes).parameters
    ) == ("receipt",)


def test_exact_route_jointly_binds_all_three_nonconfirmatory_components(
    exact_receipt,
) -> None:
    assert route.validate_nonconfirmatory_test28_30_route_receipt(exact_receipt) is (
        exact_receipt
    )
    assert exact_receipt.route_component_ids == (
        "CP63_TEST28_ACCEPTED_16X2_RUNNER_AND_INDEPENDENT_RECOMPUTATION",
        "HASH_FIRST_TEST29_TEST30_TWO_MACROSTEP_1024_CASE_PATH",
        "WHOLE_METHOD_SUPPLIED_INPUT_SYNTHETIC_INTEGRATION",
    )
    assert exact_receipt.route_components_jointly_bound is True
    assert (
        exact_receipt.cp63_test28.historical_nonconfirmatory_execution_receipt_revalidated
        is True
    )
    assert exact_receipt.cp63_test28.fresh_execution_performed_here is False
    assert exact_receipt.cp63_test28.row_count == 16
    assert exact_receipt.cp63_test28.repetitions_per_row == 2
    assert exact_receipt.cp63_test28.estimand_count == 554
    assert exact_receipt.test29_test30_two_macrostep.fresh_execution_performed_here
    assert (
        exact_receipt.test29_test30_two_macrostep.ordered_word_pair_cases_checked
        == 1_024
    )
    assert exact_receipt.whole_method.separately_executed_and_validated is True
    assert exact_receipt.whole_method.implementation_obligation_count == 19
    assert exact_receipt.whole_method.open_residual_slot_count == 50


def test_route_preserves_every_prohibited_delta(exact_receipt) -> None:
    assert (
        exact_receipt.formal_test_28_state,
        exact_receipt.formal_test_29_state,
        exact_receipt.formal_test_30_state,
    ) == ("OPEN", "OPEN", "PENDING")
    assert exact_receipt.formal_tests_closed == 0
    assert exact_receipt.b12_closed is False
    assert (
        exact_receipt.fields_closed,
        exact_receipt.blockers_closed,
        exact_receipt.result_slots_filled,
    ) == (0, 0, 0)
    assert not any(
        (
            exact_receipt.runtime_selected,
            exact_receipt.data_contacted,
            exact_receipt.network_contacted,
            exact_receipt.entropy_consumed,
            exact_receipt.science_executed,
            exact_receipt.authority_asserted,
            exact_receipt.production_receipt_issued,
            exact_receipt.tracker_or_ledger_edited,
        )
    )
    assert exact_receipt.proposed_timetable_task == route.PROPOSED_TIMETABLE_TASK
    assert exact_receipt.proposed_timetable_task_closures == 1
    assert exact_receipt.applied_timetable_task_closures == 0


def test_receipt_serialization_is_canonical_duplicate_free_and_lf_terminated(
    exact_receipt,
) -> None:
    raw = route.route_receipt_canonical_json_bytes(exact_receipt)
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    seen = []

    def pairs_hook(pairs):
        keys = [key for key, _value in pairs]
        assert len(keys) == len(set(keys))
        seen.extend(keys)
        return dict(pairs)

    document = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=pairs_hook)
    assert seen
    assert document["receipt_sha256"] == exact_receipt.receipt_sha256
    assert (
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        + b"\n"
        == raw
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: dataclasses.replace(value, formal_test_28_state="CLOSED"),
        lambda value: dataclasses.replace(value, b12_closed=True),
        lambda value: dataclasses.replace(value, fields_closed=1),
        lambda value: dataclasses.replace(value, fields_closed=False),
        lambda value: dataclasses.replace(value, runtime_selected=True),
        lambda value: dataclasses.replace(value, science_executed=True),
        lambda value: dataclasses.replace(value, tracker_or_ledger_edited=True),
        lambda value: dataclasses.replace(
            value, applied_timetable_task_closures=1
        ),
        lambda value: dataclasses.replace(
            value,
            cp63_test28=dataclasses.replace(
                value.cp63_test28, fresh_execution_performed_here=True
            ),
        ),
        lambda value: dataclasses.replace(
            value,
            test29_test30_two_macrostep=dataclasses.replace(
                value.test29_test30_two_macrostep,
                report_sha256="1" * 64,
            ),
        ),
        lambda value: dataclasses.replace(
            value,
            whole_method=dataclasses.replace(
                value.whole_method, open_residual_slot_count=49
            ),
        ),
    ),
)
def test_semantic_tamper_is_rejected_even_after_attacker_resigns(
    exact_receipt, mutation
) -> None:
    forged = _resign(mutation(exact_receipt))
    with pytest.raises((route.NonconfirmatoryRouteError, TypeError)):
        route.validate_nonconfirmatory_test28_30_route_receipt(forged)


def test_exact_concrete_type_rejects_subclass_and_duck(exact_receipt) -> None:
    class ReceiptSubclass(route.NonconfirmatoryRouteReceipt):
        pass

    hostile = object.__new__(ReceiptSubclass)
    with pytest.raises(TypeError):
        route.validate_nonconfirmatory_test28_30_route_receipt(hostile)
    with pytest.raises(TypeError):
        route.validate_nonconfirmatory_test28_30_route_receipt(
            SimpleNamespace(**dataclasses.asdict(exact_receipt))
        )


@pytest.mark.parametrize(
    "value",
    ("a//b", "a/./b", "a/b/", "../a", "/absolute", "a\\b", ""),
)
def test_relative_path_aliases_and_escapes_are_rejected(value) -> None:
    with pytest.raises(route.NonconfirmatoryRouteError):
        route._safe_relative_path(value)


@pytest.mark.parametrize(
    "value",
    (
        str(ROOT) + "/",
        str(ROOT.parent) + "//" + ROOT.name,
        str(ROOT) + "/.",
        "relative/root",
    ),
)
def test_project_root_text_aliases_are_rejected(value) -> None:
    with pytest.raises(route.NonconfirmatoryRouteError):
        route._canonical_root(value)


def test_duplicate_json_keys_and_nonfinite_values_are_rejected() -> None:
    with pytest.raises(route.NonconfirmatoryRouteError, match="duplicate JSON key"):
        route._decode_json(b'{"a":1,"a":2}', "hostile")
    with pytest.raises(route.NonconfirmatoryRouteError, match="non-finite"):
        route._decode_json(b'{"a":NaN}', "hostile")


def test_cp63_fixture_drift_is_rejected_before_semantic_use(tmp_path) -> None:
    paths = (
        route.CP63_FIXTURE_PATH,
        route.CP63_RUNNER_PATH,
        route.CP63_INDEPENDENT_PATH,
    )
    for relative in paths:
        _copy(relative, tmp_path)
    fixture = tmp_path / route.CP63_FIXTURE_PATH
    raw = bytearray(fixture.read_bytes())
    raw[-2] ^= 1
    fixture.write_bytes(bytes(raw))
    fixture.chmod(0o644)
    with pytest.raises(route.NonconfirmatoryRouteError, match="pin mismatch"):
        route._cp63_binding(tmp_path)


def test_hostile_two_macrostep_wrapper_never_executes(tmp_path) -> None:
    wrapper = _copy(route.TWO_MACROSTEP_WRAPPER_PATH, tmp_path)
    marker = tmp_path / "hostile-wrapper-executed"
    wrapper.write_text(
        "from pathlib import Path\n"
        + "Path(%r).write_bytes(b'executed')\n" % str(marker),
        encoding="utf-8",
    )
    wrapper.chmod(0o644)
    with pytest.raises(route.NonconfirmatoryRouteError, match="pin mismatch"):
        route._two_macrostep_binding(tmp_path)
    assert not marker.exists()


@pytest.mark.parametrize("preload", ("module", "none"))
def test_preloaded_wrapper_cache_is_ignored_and_restored(monkeypatch, preload) -> None:
    name = "_formal_test28_30_route_bound_two_macrostep_wrapper"
    marker = []
    if preload == "module":
        previous = ModuleType(name)
        previous.validate = lambda _root: marker.append("executed")
    else:
        previous = None
    monkeypatch.setitem(sys.modules, name, previous)
    binding = route._two_macrostep_binding(ROOT)
    assert binding.report_sha256 == route.TWO_MACROSTEP_REPORT_SHA256
    assert marker == []
    assert sys.modules[name] is previous


def test_whole_method_machine_receipt_drift_is_rejected(tmp_path) -> None:
    machine = _copy(route.WHOLE_METHOD_MACHINE_PATH, tmp_path)
    assert route._whole_method_binding(tmp_path).receipt_sha256 == (
        route.WHOLE_METHOD_RECEIPT_SHA256
    )
    raw = bytearray(machine.read_bytes())
    raw[-2] ^= 1
    machine.write_bytes(bytes(raw))
    machine.chmod(0o644)
    with pytest.raises(route.NonconfirmatoryRouteError, match="pin mismatch"):
        route._whole_method_binding(tmp_path)


def test_hash_first_package_validator_passes_from_unrelated_cwd(
    monkeypatch, tmp_path
) -> None:
    validator = _load_validator("_test28_30_route_package_validator")
    monkeypatch.chdir(tmp_path)
    result = validator.validate()
    assert result["status"] == "PASS"
    assert result["route_component_count"] == 3
    assert (
        result["test28_state"],
        result["test29_state"],
        result["test30_state"],
    ) == ("OPEN", "OPEN", "PENDING")
    assert (
        result["formal_tests_closed"],
        result["fields_closed"],
        result["blockers_closed"],
        result["result_slots_filled"],
        result["applied_timetable_task_closures"],
        result["proposed_timetable_task_closures"],
    ) == (0, 0, 0, 0, 0, 1)
    assert result["tracker_or_ledger_edited"] is False


@pytest.mark.parametrize("preload", ("module", "none"))
def test_validator_ignores_preloaded_route_and_wrapper_modules(
    monkeypatch, preload
) -> None:
    validator = _load_validator(
        "_test28_30_route_cache_validator_" + preload
    )
    names = (
        "_bound_formal_test28_30_nonconfirmatory_route",
        "_formal_test28_30_route_bound_two_macrostep_wrapper",
    )
    markers = []
    prior = {}
    for name in names:
        if preload == "module":
            value = ModuleType(name)
            value.run_nonconfirmatory_test28_30_route = (
                lambda _root: markers.append("route-spoof")
            )
            value.validate = lambda _root: markers.append("wrapper-spoof")
        else:
            value = None
        prior[name] = value
        monkeypatch.setitem(sys.modules, name, value)
    assert validator.validate()["status"] == "PASS"
    assert markers == []
    for name in names:
        assert sys.modules[name] is prior[name]


def test_validator_rejects_route_source_tamper_before_compile(
    monkeypatch, tmp_path
) -> None:
    validator = _load_validator("_test28_30_route_hostile_source_validator")
    marker = tmp_path / "hostile-route-source-executed"
    hostile = (
        "from pathlib import Path\n"
        + "Path(%r).write_bytes(b'executed')\n" % str(marker)
    ).encode("ascii")
    original = validator._read_stable_regular

    def substituted(relative):
        raw, identity = original(relative)
        if relative == validator.SOURCE_REL:
            return hostile, identity
        return raw, identity

    monkeypatch.setattr(validator, "_read_stable_regular", substituted)
    with pytest.raises(validator.ValidationError, match="pin mismatch"):
        validator.validate()
    assert not marker.exists()


def test_validator_rejects_machine_tamper_before_route_execution(
    monkeypatch,
) -> None:
    validator = _load_validator("_test28_30_route_hostile_machine_validator")
    original = validator._read_stable_regular
    route_executed = []

    def substituted(relative):
        raw, identity = original(relative)
        if relative == validator.MACHINE_REL:
            changed = bytearray(raw)
            changed[-2] ^= 1
            return bytes(changed), identity
        return raw, identity

    monkeypatch.setattr(validator, "_read_stable_regular", substituted)
    monkeypatch.setattr(
        validator,
        "_execute_captured_route_source",
        lambda _captured: route_executed.append(True),
    )
    with pytest.raises(validator.ValidationError, match="machine raw pin differs"):
        validator.validate()
    assert route_executed == []


def test_machine_receipt_is_canonical_and_self_digesting() -> None:
    validator = _load_validator("_test28_30_route_machine_validator")
    raw = (ROOT / validator.MACHINE_REL).read_bytes()
    machine = validator._decode_machine(raw)
    unsigned = dict(machine)
    unsigned["record_sha256"] = validator.ZERO_SHA256
    assert hashlib.sha256(
        validator.MACHINE_DOMAIN + validator._canonical_bytes(unsigned)
    ).hexdigest() == machine["record_sha256"]
    assert machine["record_sha256"] == validator.EXPECTED_MACHINE_RECORD_SHA256
    assert machine["route_receipt"]["receipt_sha256"] == (
        validator.EXPECTED_ROUTE_RECEIPT_SHA256
    )


def test_human_candidate_links_resolve_and_nonclaims_are_explicit() -> None:
    human = ROOT / "PROJECT_FORMAL_TEST28_30_NONCONFIRMATORY_ROUTE_CANDIDATE.md"
    text = human.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    assert links
    for relative in links:
        assert not relative.startswith(("http://", "https://", "/"))
        assert (ROOT / relative).exists(), relative
    for phrase in (
        "Formal Test 28: `OPEN`",
        "Formal Test 29: `OPEN`",
        "Formal Test 30: `PENDING`",
        "science executed: `false`",
        "external authority asserted: `false`",
        "tracker or ledger edited: `false`",
        "applied timetable-task closures: `0`",
    ):
        assert phrase in text
