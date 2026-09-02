from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ast
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import ModuleType

import pytest

from heterodiff.evaluation import formal_test28_30_nonconfirmatory_route_v2 as route


ROOT = Path(__file__).resolve().parents[2]


def _copy(relative: str, root: Path) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / relative, target)
    target.chmod(0o644)
    return target


def _whole_root(tmp_path: Path) -> Path:
    _copy(route.WHOLE_MACHINE_PATH, tmp_path)
    _copy(route.WHOLE_REVIEW_PATH, tmp_path)
    return tmp_path


def _full_root(tmp_path: Path) -> Path:
    for relative in (
        route.V1_SOURCE_PATH,
        "research/fixtures/cp50_test28_mixed_initializer_v26.json",
        "src/heterodiff/evaluation/mixed_initializer_test28_runner_recomputation_rehearsal.py",
        "src/heterodiff/evaluation/mixed_initializer_test28_independent_recomputation.py",
        "research/diagnostics/formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py",
        "src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py",
        "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
        "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
        "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
        route.WHOLE_MACHINE_PATH,
        route.WHOLE_REVIEW_PATH,
        "src/heterodiff/evaluation/formal_test28_30_nonconfirmatory_route_v2.py",
        "tests/unit/test_formal_test28_30_nonconfirmatory_route_v2.py",
        "PROJECT_FORMAL_TEST28_30_NONCONFIRMATORY_ROUTE_V2_SUCCESSOR.md",
        "research/fixtures/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.json",
        "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py",
    ):
        _copy(relative, tmp_path)
    return tmp_path


def _load_validator(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rewrite_machine(tmp_path: Path, mutate) -> Path:
    path = _copy(route.WHOLE_MACHINE_PATH, tmp_path)
    document = json.loads(path.read_text(encoding="ascii"))
    mutate(document)
    unsigned = dict(document)
    unsigned.pop("record_sha256", None)
    document["record_sha256"] = route._domain(route.WHOLE_MACHINE_RECORD_DOMAIN, unsigned)
    raw = route._canonical(document) + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)
    return path


def _accept_outer_machine_pin(monkeypatch, path: Path) -> None:
    raw = path.read_bytes()
    monkeypatch.setattr(route, "WHOLE_MACHINE_BYTES", len(raw))
    monkeypatch.setattr(route, "WHOLE_MACHINE_SHA256", hashlib.sha256(raw).hexdigest())
    document = json.loads(raw)
    monkeypatch.setattr(route, "WHOLE_MACHINE_RECORD_SHA256", document["record_sha256"])


def test_route_v2_runs_and_preserves_exact_scope() -> None:
    receipt = route.run_nonconfirmatory_test28_30_route_v2(str(ROOT))
    route.validate_nonconfirmatory_test28_30_route_v2_receipt(receipt)
    assert receipt.schema_version == route.SCHEMA_VERSION
    assert receipt.formal_test_28_state == "OPEN"
    assert receipt.formal_test_29_state == "OPEN"
    assert receipt.formal_test_30_state == "PENDING"
    assert receipt.formal_tests_closed == receipt.fields_closed == 0
    assert receipt.blockers_closed == receipt.result_slots_filled == 0
    assert receipt.b12_closed is False
    assert receipt.applied_timetable_task_closures == 0
    assert receipt.proposed_timetable_task_closures == 1
    assert receipt.proposed_timetable_task == route.PROPOSED_TIMETABLE_TASK
    assert all(
        value is False
        for value in (
            receipt.runtime_selected,
            receipt.data_contacted,
            receipt.network_contacted,
            receipt.entropy_consumed,
            receipt.science_executed,
            receipt.authority_asserted,
            receipt.production_receipt_issued,
            receipt.tracker_or_ledger_edited,
        )
    )


def test_historical_and_fresh_execution_counts_are_exact() -> None:
    receipt = route.run_nonconfirmatory_test28_30_route_v2(str(ROOT))
    cp63 = receipt.cp63_test28
    assert (cp63["row_count"], cp63["repetitions_per_row"], cp63["launch_count"]) == (16, 2, 32)
    assert cp63["estimand_count"] == 554
    assert cp63["fresh_execution_performed_here"] is False
    fresh = receipt.test29_test30_two_macrostep
    assert fresh["ordered_word_pair_cases_checked"] == 1024
    assert fresh["distinct_input_sha256_count"] == 1024
    assert fresh["distinct_report_sha256_count"] == 1024
    assert fresh["fresh_execution_performed_here"] is True


def test_whole_successor_exact_positive_chain_and_go() -> None:
    value = route._whole_binding(ROOT)
    assert value.machine.sha256 == route.WHOLE_MACHINE_SHA256
    assert value.machine_record_sha256 == route.WHOLE_MACHINE_RECORD_SHA256
    assert value.receipt_sha256 == route.WHOLE_RECEIPT_SHA256
    assert value.core_output_sha256 == route.WHOLE_CORE_SHA256
    assert value.supplied_input_sha256 == route.WHOLE_SUPPLIED_INPUT_SHA256
    assert value.selected_configuration_sha256 == route.WHOLE_SELECTED_CONFIGURATION_SHA256
    assert value.transform_sha256 == route.WHOLE_TRANSFORM_SHA256
    assert value.derived_initial_state_sha256 == route.WHOLE_INITIAL_STATE_SHA256
    assert value.integrated_path_input_sha256 == route.WHOLE_PATH_INPUT_SHA256
    assert value.integrated_path_report_sha256 == route.WHOLE_PATH_REPORT_SHA256
    assert value.custody_chain_sha256 == route.WHOLE_CUSTODY_SHA256
    assert value.independent_review_go is True
    assert value.isolated_hash_first_validator_pass is True
    assert value.test28_initializer_admissible is True
    assert value.initializer_to_path_integrated is True
    assert value.bounded_two_macrostep_path_integrated is True
    assert value.test29_route_and_lineage_semantics_integrated is True
    assert value.test30_heun_primitive_integrated is True
    assert value.confirmatory_evidence is False


@pytest.mark.parametrize(
    "name,replacement",
    (
        ("receipt_sha256", "1" * 64),
        ("core_output_sha256", "2" * 64),
        ("selected_configuration_sha256", "3" * 64),
        ("transform_sha256", "4" * 64),
        ("derived_initial_state_sha256", "5" * 64),
        ("integrated_path_input_sha256", "6" * 64),
        ("integrated_path_report_sha256", "7" * 64),
        ("custody_chain_sha256", "8" * 64),
        ("independent_review_go", False),
        ("test28_initializer_admissible", False),
        ("initializer_to_path_integrated", False),
        ("open_residual_slot_count", 49),
        ("confirmatory_evidence", True),
    ),
)
def test_whole_binding_substitution_is_rejected(name, replacement) -> None:
    value = route._whole_binding(ROOT)
    with pytest.raises(route.NonconfirmatoryRouteV2Error):
        route._validate_whole(replace(value, **{name: replacement}))


def test_route_subject_prevents_nested_substitution() -> None:
    receipt = route.run_nonconfirmatory_test28_30_route_v2(str(ROOT))
    changed = dict(receipt.cp63_test28)
    changed["launch_count"] = 31
    with pytest.raises(route.NonconfirmatoryRouteV2Error):
        route.validate_nonconfirmatory_test28_30_route_v2_receipt(
            replace(receipt, cp63_test28=changed)
        )


@pytest.mark.parametrize("component", ("cp63", "two"))
def test_fully_resigned_forged_component_is_rejected(component) -> None:
    receipt = route.run_nonconfirmatory_test28_30_route_v2(str(ROOT))
    changed = replace(
        receipt,
        **({"cp63_test28": {"forged_cp63": True}} if component == "cp63" else {"test29_test30_two_macrostep": {"forged_two": True}}),
    )
    subject = {
        "cp63_test28": route._plain(changed.cp63_test28),
        "route_component_ids": route._plain(changed.route_component_ids),
        "test29_test30_two_macrostep": route._plain(changed.test29_test30_two_macrostep),
        "whole_method_successor": route._plain(changed.whole_method_successor),
    }
    changed = replace(
        changed,
        route_subject_sha256=hashlib.sha256(route.SUBJECT_DOMAIN + route._canonical(subject)).hexdigest(),
        receipt_sha256=route.ZERO_SHA256,
    )
    changed = replace(
        changed,
        receipt_sha256=hashlib.sha256(route.RECEIPT_DOMAIN + route._canonical(route._plain(changed))).hexdigest(),
    )
    with pytest.raises(route.NonconfirmatoryRouteV2Error, match="key roster"):
        route.validate_nonconfirmatory_test28_30_route_v2_receipt(changed)


@pytest.mark.parametrize(
    "name,value",
    (
        ("isolated_hash_first_validator_pass", 1),
        ("independent_review_go", 1),
        ("test28_initializer_admissible", 1),
        ("initializer_to_path_integrated", 1),
        ("bounded_two_macrostep_path_integrated", 1),
        ("test29_route_and_lineage_semantics_integrated", 1),
        ("test30_heun_primitive_integrated", 1),
        ("separate_recomputation_bytes_equal", 1),
        ("confirmatory_evidence", 0),
        ("open_residual_slot_count", True),
    ),
)
def test_whole_binding_rejects_bool_int_aliases(name, value) -> None:
    whole = route._whole_binding(ROOT)
    with pytest.raises(TypeError):
        route._validate_whole(replace(whole, **{name: value}))


@pytest.mark.parametrize(
    "name,value",
    (
        ("formal_tests_closed", False),
        ("fields_closed", False),
        ("blockers_closed", False),
        ("result_slots_filled", False),
        ("proposed_timetable_task_closures", True),
        ("applied_timetable_task_closures", False),
    ),
)
def test_route_receipt_rejects_bool_int_aliases(name, value) -> None:
    receipt = route.run_nonconfirmatory_test28_30_route_v2(str(ROOT))
    with pytest.raises(TypeError):
        route.validate_nonconfirmatory_test28_30_route_v2_receipt(
            replace(receipt, **{name: value})
        )


def test_old_whole_method_machine_is_rejected(monkeypatch, tmp_path) -> None:
    _copy(route.WHOLE_REVIEW_PATH, tmp_path)
    old = _copy(
        "research/fixtures/manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json",
        tmp_path,
    )
    monkeypatch.setattr(route, "WHOLE_MACHINE_PATH", str(old.relative_to(tmp_path)))
    monkeypatch.setattr(route, "WHOLE_MACHINE_BYTES", old.stat().st_size)
    monkeypatch.setattr(route, "WHOLE_MACHINE_SHA256", hashlib.sha256(old.read_bytes()).hexdigest())
    with pytest.raises(route.NonconfirmatoryRouteV2Error):
        route._whole_binding(tmp_path)


def test_false_admissibility_fails_even_with_resealed_outer_record(monkeypatch, tmp_path) -> None:
    _copy(route.WHOLE_REVIEW_PATH, tmp_path)
    path = _rewrite_machine(
        tmp_path,
        lambda document: document["route_binding"].__setitem__("test28_initializer_admissible", False),
    )
    _accept_outer_machine_pin(monkeypatch, path)
    with pytest.raises(route.NonconfirmatoryRouteV2Error, match="accepted value"):
        route._whole_binding(tmp_path)


def test_boolean_integer_alias_in_resealed_machine_is_rejected(monkeypatch, tmp_path) -> None:
    _copy(route.WHOLE_REVIEW_PATH, tmp_path)
    path = _rewrite_machine(
        tmp_path,
        lambda document: document["route_binding"].__setitem__("test28_initializer_admissible", 1),
    )
    _accept_outer_machine_pin(monkeypatch, path)
    with pytest.raises(route.NonconfirmatoryRouteV2Error, match="accepted value"):
        route._whole_binding(tmp_path)


def test_chain_consistent_wrong_values_fail_against_exact_acceptance(monkeypatch, tmp_path) -> None:
    _copy(route.WHOLE_REVIEW_PATH, tmp_path)
    def mutate(document):
        wrong = "9" * 64
        document["route_binding"]["selected_configuration_sha256"] = wrong
        document["semantics"]["core"]["initializer"]["selected_configuration_sha256"] = wrong
        document["semantics"]["core"]["initializer_path_state"]["selected_configuration_sha256"] = wrong
    path = _rewrite_machine(tmp_path, mutate)
    _accept_outer_machine_pin(monkeypatch, path)
    with pytest.raises(route.NonconfirmatoryRouteV2Error):
        route._whole_binding(tmp_path)


def test_no_go_review_is_rejected(monkeypatch, tmp_path) -> None:
    _copy(route.WHOLE_MACHINE_PATH, tmp_path)
    review = _copy(route.WHOLE_REVIEW_PATH, tmp_path)
    raw = review.read_bytes().replace(b"**GO ", b"**NO ", 1)
    review.write_bytes(raw)
    review.chmod(0o644)
    monkeypatch.setattr(route, "WHOLE_REVIEW_BYTES", len(raw))
    monkeypatch.setattr(route, "WHOLE_REVIEW_SHA256", hashlib.sha256(raw).hexdigest())
    with pytest.raises(route.NonconfirmatoryRouteV2Error, match="GO review"):
        route._whole_binding(tmp_path)


@pytest.mark.parametrize("payload", (b'{"a":1,"a":2}\n', b'{"a":NaN}\n', b'{}', b'\xff\n'))
def test_strict_json_and_framing_reject_malformed_values(payload) -> None:
    with pytest.raises(route.NonconfirmatoryRouteV2Error):
        route._decode(payload, "hostile", terminal_lf=True)


def test_machine_leaf_symlink_is_rejected(tmp_path) -> None:
    _copy(route.WHOLE_REVIEW_PATH, tmp_path)
    target = tmp_path / "target.json"
    target.write_bytes((ROOT / route.WHOLE_MACHINE_PATH).read_bytes())
    target.chmod(0o644)
    link = tmp_path / route.WHOLE_MACHINE_PATH
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)
    with pytest.raises(OSError):
        route._whole_binding(tmp_path)


def test_hardlinked_review_is_rejected(tmp_path) -> None:
    _copy(route.WHOLE_MACHINE_PATH, tmp_path)
    source = tmp_path / "review-source.md"
    source.write_bytes((ROOT / route.WHOLE_REVIEW_PATH).read_bytes())
    source.chmod(0o644)
    review = tmp_path / route.WHOLE_REVIEW_PATH
    review.hardlink_to(source)
    with pytest.raises(route.NonconfirmatoryRouteV2Error, match="custody"):
        route._whole_binding(tmp_path)


def test_wrong_mode_is_rejected(tmp_path) -> None:
    root = _whole_root(tmp_path)
    (root / route.WHOLE_MACHINE_PATH).chmod(0o600)
    with pytest.raises(route.NonconfirmatoryRouteV2Error, match="custody"):
        route._whole_binding(root)


@pytest.mark.parametrize("suffix", ("/", "/./", "//"))
def test_noncanonical_root_text_is_rejected(suffix) -> None:
    with pytest.raises(route.NonconfirmatoryRouteV2Error):
        route.run_nonconfirmatory_test28_30_route_v2(str(ROOT) + suffix)


@pytest.mark.parametrize("preload", ("module", "none"))
def test_v1_private_cache_spoof_is_ignored_and_restored(monkeypatch, preload) -> None:
    name = "_formal_test28_30_route_v2_bound_v1"
    prior = ModuleType(name) if preload == "module" else None
    marker = []
    if type(prior) is ModuleType:
        prior._cp63_binding = lambda root: marker.append(root)
    monkeypatch.setitem(sys.modules, name, prior)
    module = route._load_v1(ROOT)
    assert type(module) is ModuleType
    assert marker == []
    assert sys.modules[name] is prior


@pytest.mark.parametrize("preload", ("module", "none", "absent"))
def test_concurrent_routes_are_deterministic(monkeypatch, preload) -> None:
    name = "_formal_test28_30_route_v2_bound_v1"
    sentinel = ModuleType(name) if preload == "module" else None
    if preload == "absent":
        monkeypatch.delitem(sys.modules, name, raising=False)
    else:
        monkeypatch.setitem(sys.modules, name, sentinel)
    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(lambda _: route.run_nonconfirmatory_test28_30_route_v2(str(ROOT)), range(2)))
    assert values[0].receipt_sha256 == values[1].receipt_sha256
    assert route.route_v2_receipt_canonical_json_bytes(values[0]) == route.route_v2_receipt_canonical_json_bytes(values[1])
    if preload == "absent":
        assert name not in sys.modules
    else:
        assert sys.modules[name] is sentinel


def test_full_unrelated_physical_copy_executes(tmp_path) -> None:
    root = _full_root(tmp_path)
    receipt = route.run_nonconfirmatory_test28_30_route_v2(str(root))
    assert receipt.whole_method_successor.independent_review_go is True
    assert receipt.receipt_sha256 == route.run_nonconfirmatory_test28_30_route_v2(str(ROOT)).receipt_sha256


def test_package_validator_passes_from_root() -> None:
    validator = _load_validator(
        ROOT / "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py",
        "_route_v2_validator_root",
    )
    result = validator.validate(str(ROOT))
    assert result["status"] == "PASS"
    assert result["receipt_sha256"] == route.run_nonconfirmatory_test28_30_route_v2(str(ROOT)).receipt_sha256
    assert result["formal_test_states"] == ["OPEN", "OPEN", "PENDING"]
    assert result["applied_timetable_task_closures"] == 0


def test_validator_source_has_no_duplicate_literal_dict_keys() -> None:
    path = ROOT / "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [key.value for key in node.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)]
            assert len(keys) == len(set(keys))


def test_package_validator_passes_from_unrelated_physical_copy(tmp_path) -> None:
    copy_root = _full_root(tmp_path)
    validator = _load_validator(
        copy_root / "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py",
        "_route_v2_validator_copy",
    )
    assert validator.validate(str(copy_root))["status"] == "PASS"


@pytest.mark.parametrize("preload", ("module", "none", "absent"))
def test_validator_ignores_and_restores_preloaded_route_cache(monkeypatch, preload) -> None:
    validator = _load_validator(
        ROOT / "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py",
        "_route_v2_validator_cache_" + preload,
    )
    name = "_formal_test28_30_route_v2_validator_bound_source"
    marker = []
    previous = ModuleType(name) if preload == "module" else None
    if type(previous) is ModuleType:
        previous.run_nonconfirmatory_test28_30_route_v2 = lambda root: marker.append(root)
    if preload == "absent":
        monkeypatch.delitem(sys.modules, name, raising=False)
    else:
        monkeypatch.setitem(sys.modules, name, previous)
    module = validator._load_route(ROOT)
    assert type(module) is ModuleType
    assert marker == []
    if preload == "absent":
        assert name not in sys.modules
    else:
        assert sys.modules[name] is previous


@pytest.mark.parametrize("suffix", ("/", "/./", "//"))
def test_validator_rejects_noncanonical_root_text(suffix) -> None:
    validator = _load_validator(
        ROOT / "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py",
        "_route_v2_validator_root_alias_" + suffix.replace("/", "x").replace(".", "d"),
    )
    with pytest.raises(validator.ValidationError, match="root differs"):
        validator.validate(str(ROOT) + suffix)


def test_validator_recaptures_machine_identity_after_full_run(monkeypatch) -> None:
    validator = _load_validator(
        ROOT / "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py",
        "_route_v2_validator_machine_reopen",
    )
    original = validator._capture
    calls = 0
    def changed(root, relative, size, digest):
        nonlocal calls
        raw, identity = original(root, relative, size, digest)
        if relative == validator.MACHINE:
            calls += 1
            if calls == 2:
                identity = identity[:-1] + (identity[-1] + 1,)
        return raw, identity
    monkeypatch.setattr(validator, "_capture", changed)
    with pytest.raises(validator.ValidationError, match="machine identity changed"):
        validator.validate(str(ROOT))


@pytest.mark.parametrize("preload", ("module", "none", "absent"))
def test_concurrent_validator_calls_serialize_and_restore_cache(monkeypatch, preload) -> None:
    validator = _load_validator(
        ROOT / "research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.py",
        "_route_v2_validator_concurrent_" + preload,
    )
    name = "_formal_test28_30_route_v2_validator_bound_source"
    sentinel = ModuleType(name) if preload == "module" else None
    marker = []
    if type(sentinel) is ModuleType:
        sentinel.run_nonconfirmatory_test28_30_route_v2 = lambda root: marker.append(root)
    if preload == "absent":
        monkeypatch.delitem(sys.modules, name, raising=False)
    else:
        monkeypatch.setitem(sys.modules, name, sentinel)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: validator.validate(str(ROOT)), range(2)))
    assert [item["receipt_sha256"] for item in results] == [
        "eab918f4aa9a58f56466673f5e8bcaefb6180692acbdfd9a6e6a694c2a3b6c4f"
    ] * 2
    assert marker == []
    if preload == "absent":
        assert name not in sys.modules
    else:
        assert sys.modules[name] is sentinel
