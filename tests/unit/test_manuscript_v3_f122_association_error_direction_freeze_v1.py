from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import stat
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "research/diagnostics/manuscript_v3_f122_association_error_direction_freeze_v1.py"
SPEC = importlib.util.spec_from_file_location("f122_freeze", SOURCE)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def payload(upper=(1, 2), threshold=(1, 2)):
    return {
        "certifications": {k: True for k in M.CERT_KEYS},
        "certified_upper_endpoint": {"denominator": upper[1], "numerator": upper[0]},
        "direction": M.DIRECTION,
        "f123_threshold": {"denominator": threshold[1], "numerator": threshold[0]},
        "f123_threshold_record_sha256": "2" * 64,
        "metric_id": M.METRIC_ID,
        "metric_index": M.METRIC_INDEX,
        "scalar_definition_sha256": "1" * 64,
    }


def refusal(value):
    with pytest.raises(M.F122Refusal) as exc:
        M.evaluate_association_error_gate(value)
    assert exc.value.disposition == M.REFUSAL
    assert exc.value.gate_decision_produced is False


def test_live_validation_passes():
    result = M.validate(ROOT)
    assert result["status"] == "PASS"
    assert result["sole_field"] == "F122"
    assert result["predecessors_verified"] == 15


def test_full_machine_record_is_exact_reconstruction():
    live = json.loads((ROOT / M.MACHINE_PATH).read_text())
    expected = M.expected_record(ROOT)
    assert live == expected
    assert live["record_sha256"] == M.semantic_digest(expected)
    boundary = live["qualification_boundary"]
    assert boundary["validator_raw_authenticity"] == "INDEPENDENT_REVIEW_BOUND_NOT_SELF_AUTHENTICATING"
    assert boundary["validator_raw_self_authenticating"] is False
    assert boundary["validator_raw_authenticity_becomes_durable_only_in_later_exact_independent_review_receipt"] is True


@pytest.mark.parametrize("upper,threshold,decision", [
    ((1, 3), (1, 2), "PASS"), ((1, 2), (1, 2), "PASS"),
    ((2, 3), (1, 2), "FAIL"), ((0, 1), (0, 1), "PASS"),
    ((10**100 + 1, 10**101), (1, 10), "FAIL"),
])
def test_exact_comparator(upper, threshold, decision):
    got = M.evaluate_association_error_gate(payload(upper, threshold))
    assert list(got) == M.RESULT_KEYS
    assert got["decision"] == decision
    assert got["equality_passes"] is True
    assert got["production_inputs_authenticated"] is False


@pytest.mark.parametrize("key,value", [
    ("metric_index", 3), ("metric_index", 5), ("metric_index", True),
    ("metric_index", 4.0), ("metric_id", "Association-approximation-error"),
    ("metric_id", "association-approximation-error "), ("direction", "LOWER_BOUND"),
    ("direction", "upper_bound"), ("scalar_definition_sha256", "A" * 64),
    ("f123_threshold_record_sha256", "2" * 63),
])
def test_identity_and_digest_hostiles_refuse(key, value):
    x = payload(); x[key] = value; refusal(x)


@pytest.mark.parametrize("name", M.CERT_KEYS)
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_missing_or_unverified_certifications_refuse(name, value):
    x = payload(); x["certifications"][name] = value; refusal(x)


@pytest.mark.parametrize("slot,bad", [
    ("certified_upper_endpoint", {"denominator": 0, "numerator": 0}),
    ("certified_upper_endpoint", {"denominator": -2, "numerator": 1}),
    ("certified_upper_endpoint", {"denominator": 2, "numerator": -1}),
    ("certified_upper_endpoint", {"denominator": 2, "numerator": 2}),
    ("certified_upper_endpoint", {"denominator": 2.0, "numerator": 1}),
    ("certified_upper_endpoint", {"denominator": 2, "numerator": True}),
    ("certified_upper_endpoint", {"denominator": float("inf"), "numerator": 1}),
    ("certified_upper_endpoint", {"denominator": 2, "numerator": float("nan")}),
    ("f123_threshold", {"denominator": 4, "numerator": 2}),
    ("f123_threshold", {"numerator": 1, "denominator": 2}),
])
def test_nonfinite_malformed_and_noncanonical_rationals_refuse(slot, bad):
    x = payload(); x[slot] = bad; refusal(x)


def test_missing_extra_and_reordered_inputs_refuse():
    x = payload(); x.pop("f123_threshold"); refusal(x)
    x = payload(); x["threshold_fallback"] = {"denominator": 1, "numerator": 1}; refusal(x)
    x = dict(reversed(list(payload().items()))); refusal(x)
    x = payload(); x["certifications"]["kl_selected"] = True; refusal(x)
    x = payload(); x["certifications"] = dict(reversed(list(x["certifications"].items()))); refusal(x)


@pytest.mark.parametrize("shadow", [
    "KL", "TV", "MAX_KL_TV", "weighted_combination", "1e-8", "1e-6",
    "confidence_level", "interval_method", "aggregation",
])
def test_shadow_selection_not_present(shadow):
    record = json.loads((ROOT / M.MACHINE_PATH).read_text())
    field_value = record["field_closures"][0]["value"]
    assert field_value == "UPPER_BOUND"
    assert shadow not in field_value
    contract = record["direction_contract"]
    assert shadow not in json.dumps(contract, sort_keys=True)


def test_units_are_only_certified_not_selected():
    contract = json.loads((ROOT / M.MACHINE_PATH).read_text())["direction_contract"]
    assert "same_scalar_and_units" in contract["certification_keys"]
    assert "units" not in contract


def clone_package(tmp_path: Path) -> Path:
    for rel in M.PACKAGE_ROSTER:
        target = tmp_path / rel; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    record = json.loads((ROOT / M.MACHINE_PATH).read_text())
    for binding in record["predecessor_bindings"]:
        target = tmp_path / binding["path"]; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / binding["path"], target)
    return tmp_path


def resign(root: Path, mutate):
    p = root / M.MACHINE_PATH
    d = json.loads(p.read_text()); mutate(d)
    d["record_sha256"] = M.semantic_digest(d)
    p.write_bytes(M.canonical_json(d)); os.chmod(p, 0o644)


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(global_state="EXECUTABLE"),
    lambda d: d.update(state="F122_FAKE"),
    lambda d: d.update(package_kind="COMPOUND_CLOSURE"),
    lambda d: d["authority_provenance"].update(offline_local_package_construction_authorized=False),
    lambda d: d["authority_provenance"].update(network_contact_data_runtime_entropy_or_science_authorized=True),
    lambda d: d["source_effect_surface"].update(network=True),
    lambda d: d["source_effect_surface"].update(filesystem_writer=True),
    lambda d: d["qualification_boundary"].update(self_validation_is_independent_acceptance=True),
    lambda d: d["qualification_boundary"].update(read_only_stable_no_follow_validator=False),
    lambda d: d["qualification_boundary"].update(validator_raw_self_authenticating=True),
    lambda d: d["qualification_boundary"].update(validator_raw_authenticity="INTERNALLY_FIXED"),
    lambda d: d["qualification_boundary"].update(second_consecutive_B05_artifact=False),
    lambda d: d["qualification_boundary"].update(third_consecutive_B05_artifact_requires_explicit_scope_review=False),
    lambda d: d["direction_contract"].update(equality_passes=False),
    lambda d: d["direction_contract"].update(rational_key_order=["numerator", "denominator"]),
    lambda d: d["direction_contract"].update(certification_keys=list(reversed(d["direction_contract"]["certification_keys"]))),
    lambda d: d["direction_contract"].update(input_key_order=list(reversed(d["direction_contract"]["input_key_order"]))),
    lambda d: d["predecessor_bindings"][0].update(group="FAKE"),
    lambda d: d["predecessor_bindings"][0].update(ordinal=14),
    lambda d: d["predecessor_bindings"][0].update(role="machine"),
    lambda d: d["project_effects_and_nonclaims"].update(F114_F119_remain_open=False),
    lambda d: d["project_effects_and_nonclaims"].update(F120_prior_closure_preserved=False),
    lambda d: d["project_effects_and_nonclaims"].update(F123_F127_remain_open=False),
    lambda d: d["project_effects_and_nonclaims"].update(F149_remains_open=False),
    lambda d: d["project_effects_and_nonclaims"].update(formal_test_28_status="CLOSED"),
    lambda d: d["project_effects_and_nonclaims"].update(formal_test_29_status="CLOSED"),
    lambda d: d["project_effects_and_nonclaims"].update(formal_test_30_status="PASS"),
    lambda d: d["project_effects_and_nonclaims"].update(formal_tests_closed=1),
    lambda d: d["project_effects_and_nonclaims"].update(results_filled=1),
    lambda d: d["project_effects_and_nonclaims"].update(F121_status="CLOSED"),
    lambda d: d["project_effects_and_nonclaims"].update(second_consecutive_B05_artifact=False),
    lambda d: d["project_effects_and_nonclaims"].update(validator_raw_self_authenticated_by_package=True),
    lambda d: d["project_effects_and_nonclaims"].update(validator_raw_authenticity_boundary="SELF_AUTHENTICATING"),
    lambda d: d["package_bindings_excluding_machine_self"][0].update(role="machine"),
    lambda d: d["package_bindings_excluding_machine_self"][1].update(ordinal=9),
    lambda d: d["package_bindings_excluding_machine_self"][2].update(group="FLOATING"),
])
def test_every_central_machine_surface_is_exact_under_resigning(tmp_path, mutate):
    root = clone_package(tmp_path); resign(root, mutate)
    with pytest.raises(ValueError): M.validate(root)


@pytest.mark.parametrize("mutate", [
    lambda d: d["field_closures"].append({"field_id":"F123","json_pointer":"/metric_and_estimand_plan/constraint_metrics/4/threshold_or_margin","owner_role":"OWNER_A_THEORY_AND_STATISTICS","value":"1e-6"}),
    lambda d: d["field_closures"][0].update(field_id="F119"),
    lambda d: d["field_closures"][0].update(json_pointer="/metric_and_estimand_plan/constraint_metrics/3/direction"),
    lambda d: d["field_closures"][0].update(value="MAX_KL_TV"),
    lambda d: d["count_transition"]["after"].update(pre_execution_open=139),
    lambda d: d["workstream_transition"]["after"]["theory_statistics"].update(closed=23),
    lambda d: d["project_effects_and_nonclaims"].update(B05_remains_open=False),
    lambda d: d["project_effects_and_nonclaims"].update(all_12_blockers_remain_open=False),
    lambda d: d["direction_contract"].update(f123_threshold_selected_here=True),
    lambda d: d["direction_contract"].update(kl_or_tv_selected_here=True),
])
def test_resigned_false_promotions_fail(tmp_path, mutate):
    root = clone_package(tmp_path); resign(root, mutate)
    with pytest.raises(ValueError): M.validate(root)


def test_duplicate_key_and_noncanonical_machine_fail(tmp_path):
    root = clone_package(tmp_path); p = root / M.MACHINE_PATH
    raw = p.read_text(); p.write_text(raw.replace('{"authority_provenance":', '{"schema_version":"duplicate","authority_provenance":', 1))
    with pytest.raises(ValueError): M.validate(root)
    root = clone_package(tmp_path / "second"); p = root / M.MACHINE_PATH
    p.write_text(json.dumps(json.loads(p.read_text()), indent=2) + "\n")
    with pytest.raises(ValueError): M.validate(root)


def test_predecessor_mutation_fails(tmp_path):
    root = clone_package(tmp_path)
    p = root / "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md"; p.write_bytes(p.read_bytes() + b"x")
    with pytest.raises(ValueError): M.validate(root)


def test_predecessor_semantic_resigning_fails(tmp_path):
    root = clone_package(tmp_path)
    p = root / "research/fixtures/manuscript_v3_f120_initializer_error_direction_freeze_v1.json"
    d = json.loads(p.read_text()); d["global_state"] = "EXECUTABLE"
    d["record_sha256"] = M.semantic_digest(d); p.write_bytes(M.canonical_json(d))
    with pytest.raises(ValueError): M.validate(root)


@pytest.mark.parametrize("index", [0, 2])
def test_resigned_machine_cannot_float_fixed_human_or_test_binding(tmp_path, index):
    root = clone_package(tmp_path)
    record = json.loads((root / M.MACHINE_PATH).read_text())
    row = record["package_bindings_excluding_machine_self"][index]
    path = root / row["path"]
    path.write_bytes(path.read_bytes() + b"\n"); os.chmod(path, 0o644)
    def mutate(d):
        target = d["package_bindings_excluding_machine_self"][index]
        raw = path.read_bytes(); target["bytes"] = len(raw); target["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    resign(root, mutate)
    with pytest.raises(ValueError): M.validate(root)


def test_validator_binding_is_current_raw_but_not_self_authenticated():
    record = json.loads((ROOT / M.MACHINE_PATH).read_text())
    row = record["package_bindings_excluding_machine_self"][1]
    raw = SOURCE.read_bytes()
    assert row["bytes"] == len(raw)
    assert row["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    text = SOURCE.read_text()
    assert "EXPECTED_VALIDATOR_NORMALIZED_SHA256" not in text
    assert "EXPECTED_VALIDATOR_BYTES_DECIMAL" not in text
    assert M.VALIDATOR_RAW_AUTHENTICITY_BOUNDARY == "INDEPENDENT_REVIEW_BOUND_NOT_SELF_AUTHENTICATING"
    nonclaims = record["project_effects_and_nonclaims"]
    assert nonclaims["validator_raw_authenticity_boundary"] == M.VALIDATOR_RAW_AUTHENTICITY_BOUNDARY
    assert nonclaims["validator_raw_self_authenticated_by_package"] is False


def test_semantic_digest_cannot_be_floated(tmp_path):
    root = clone_package(tmp_path); p = root / M.MACHINE_PATH
    d = json.loads(p.read_text()); d["record_sha256"] = "0" * 64
    p.write_bytes(M.canonical_json(d))
    with pytest.raises(ValueError): M.validate(root)


def test_symlink_hardlink_and_mode_custody_fail(tmp_path):
    root = clone_package(tmp_path); p = root / "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md"
    real = root / "real.md"; p.rename(real); p.symlink_to(real.name)
    with pytest.raises((ValueError, OSError)): M.validate(root)
    root = clone_package(tmp_path / "hard"); p = root / "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md"
    os.link(p, root / "alias.md")
    with pytest.raises(ValueError): M.validate(root)
    root = clone_package(tmp_path / "mode"); p = root / "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md"
    os.chmod(p, 0o600)
    with pytest.raises(ValueError): M.validate(root)


def _simple_custody_file(tmp_path: Path):
    root = tmp_path / "root"; leaf = root / "a" / "leaf"
    leaf.parent.mkdir(parents=True); leaf.write_bytes(b"x" * 300000); os.chmod(leaf, 0o644)
    return root, leaf


def test_root_symlink_refuses(tmp_path):
    real, _ = _simple_custody_file(tmp_path)
    link = tmp_path / "root-link"; link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError): M.stable_read(link, "a/leaf")


def test_leaf_inode_swap_during_read_refuses(tmp_path, monkeypatch):
    root, leaf = _simple_custody_file(tmp_path); original = os.read; fired = False
    def racing_read(fd, size):
        nonlocal fired
        chunk = original(fd, size)
        if not fired:
            fired = True; old = leaf.with_name("old"); leaf.rename(old); leaf.write_bytes(old.read_bytes()); os.chmod(leaf, 0o644)
        return chunk
    monkeypatch.setattr(os, "read", racing_read)
    with pytest.raises(ValueError): M.stable_read(root, "a/leaf")


def test_ancestor_inode_swap_during_read_refuses(tmp_path, monkeypatch):
    root, leaf = _simple_custody_file(tmp_path); original = os.read; fired = False
    def racing_read(fd, size):
        nonlocal fired
        chunk = original(fd, size)
        if not fired:
            fired = True; ancestor = leaf.parent; old = root / "old-a"; ancestor.rename(old); ancestor.mkdir(); replacement = ancestor / "leaf"; replacement.write_bytes((old / "leaf").read_bytes()); os.chmod(replacement, 0o644)
        return chunk
    monkeypatch.setattr(os, "read", racing_read)
    with pytest.raises(ValueError): M.stable_read(root, "a/leaf")


def test_chmod_during_read_refuses(tmp_path, monkeypatch):
    root, leaf = _simple_custody_file(tmp_path); original = os.read; fired = False
    def racing_read(fd, size):
        nonlocal fired
        chunk = original(fd, size)
        if not fired: fired = True; os.chmod(leaf, 0o600)
        return chunk
    monkeypatch.setattr(os, "read", racing_read)
    with pytest.raises(ValueError): M.stable_read(root, "a/leaf")


def test_short_read_refuses(tmp_path, monkeypatch):
    root, _ = _simple_custody_file(tmp_path)
    monkeypatch.setattr(os, "read", lambda fd, size: b"")
    with pytest.raises(ValueError): M.stable_read(root, "a/leaf")


def test_unsafe_paths_refuse(tmp_path):
    for unsafe in ("/etc/passwd", "../x", "a/../b", "./x"):
        with pytest.raises(ValueError): M.stable_read(tmp_path, unsafe)


def test_tracker_and_ledger_excluded():
    d = json.loads((ROOT / M.MACHINE_PATH).read_text())
    paths = d["predecessor_path_roster"]
    assert not any("TIMETABLE" in p or "LEDGER" in p for p in paths)
    assert "PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW.md" not in paths
    assert "PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW_V2.md" in paths
    source = SOURCE.read_text()
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in source
    assert "PROJECT_EVIDENCE_LEDGER.md" not in source


def test_package_roster_and_bindings_are_receipt_lifecycle_stable():
    assert M.PACKAGE_ROSTER == [
        "PROJECT_F122_ASSOCIATION_ERROR_DIRECTION_FREEZE.md",
        "research/fixtures/manuscript_v3_f122_association_error_direction_freeze_v1.json",
        "research/diagnostics/manuscript_v3_f122_association_error_direction_freeze_v1.py",
        "tests/unit/test_manuscript_v3_f122_association_error_direction_freeze_v1.py",
    ]
    record = json.loads((ROOT / M.MACHINE_PATH).read_text())
    current_paths = [row["path"] for row in record["package_bindings_excluding_machine_self"]]
    receipt_names = {
        "PROJECT_F122_ASSOCIATION_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW.md",
        "PROJECT_F122_ASSOCIATION_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW_V2.md",
    }
    assert receipt_names.isdisjoint(M.PACKAGE_ROSTER)
    assert receipt_names.isdisjoint(current_paths)
    source = SOURCE.read_text()
    assert all(name not in source for name in receipt_names)
    assert record["authority_provenance"]["tracker_ledger_predecessor_or_receipt_edit_authorized"] is False
    assert record["source_effect_surface"]["filesystem_writer"] is False


def test_all_live_package_files_regular_single_link_0644():
    for rel in M.PACKAGE_ROSTER:
        s = os.lstat(ROOT / rel)
        assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and stat.S_IMODE(s.st_mode) == 0o644


def test_machine_self_digest_and_ascii_canonical():
    raw = (ROOT / M.MACHINE_PATH).read_bytes(); d = json.loads(raw)
    assert raw == M.canonical_json(d)
    assert d["record_sha256"] == M.semantic_digest(d)
    raw.decode("ascii")
