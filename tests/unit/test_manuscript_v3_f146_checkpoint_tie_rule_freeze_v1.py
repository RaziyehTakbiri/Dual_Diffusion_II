from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from types import ModuleType
from typing import Any, Callable, Dict

import pytest


ROOT = Path(__file__).resolve().parents[2]
HUMAN_REL = Path("PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE.md")
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json"
)
VALIDATOR_REL = Path(
    "research/diagnostics/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py"
)
TEST_REL = Path(
    "tests/unit/test_manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("f146_validator", ROOT / VALIDATOR_REL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = _load_validator()
PACKAGE_READY = pytest.mark.skipif(
    not (ROOT / MACHINE_REL).exists(),
    reason="canonical machine record is generated only after final package bindings",
)


def _input(
    *pairs: tuple[int, str],
    unit: str | None = None,
    semantics: str | None = None,
) -> Dict[str, Any]:
    return M.synthetic_tied_best_input(
        unit or M.SYNTHETIC_SELECTION_UNIT_SHA256,
        semantics or M.SYNTHETIC_F144_SEMANTICS_SHA256,
        tuple(pairs),
    )


def _content(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _resign_roster(value: Dict[str, Any]) -> None:
    certificate = value["certificate"]
    value["tied_best_roster_sha256"] = M.certified_tied_best_roster_sha256(
        certificate["selection_unit_sha256"],
        certificate["f144_semantics_sha256"],
        value["rows"],
    )


def _refusal(value: Any) -> M.SelectionRefusal:
    with pytest.raises(M.SelectionRefusal) as caught:
        M.select_earliest_step_tied_best(value)
    return caught.value


def _machine(root: Path) -> Dict[str, Any]:
    return json.loads((root / MACHINE_REL).read_text(encoding="ascii"))


def _write_resigned_machine(root: Path, record: Dict[str, Any]) -> None:
    record["record_sha256"] = M.record_sha256(record)
    target = root / MACHINE_REL
    target.write_bytes(M.canonical_machine_bytes(record))
    target.chmod(0o644)


def _copy_bound_tree(target: Path) -> Path:
    paths = set(M.PACKAGE_ROSTER)
    paths.update(spec[2] for spec in M.PREDECESSOR_SPECS)
    for relative in sorted(paths):
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    return target


def test_literal_domain_labels_and_independent_known_answer() -> None:
    unit = _content("unit-a")
    content = _content("checkpoint-a")
    step = 17
    payload = {
        "checkpoint_content_sha256": content,
        "optimizer_step_index": step,
        "selection_unit_sha256": unit,
    }
    raw = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    expected = hashlib.sha256(
        b"heterodiff-f146-step-bound-checkpoint-identity-v1\0" + raw
    ).hexdigest()
    assert M.STEP_IDENTITY_DOMAIN == (
        b"heterodiff-f146-step-bound-checkpoint-identity-v1\0"
    )
    assert M.TIED_ROSTER_DOMAIN == (
        b"heterodiff-f146-certified-tied-best-roster-v1\0"
    )
    assert M.canonical_step_bound_checkpoint_identity(unit, step, content) == expected


def test_independent_tied_roster_digest_known_answer() -> None:
    unit = _content("roster-unit")
    semantics = _content("roster-f144-semantics")
    rows = tuple(
        {
            "checkpoint_content_sha256": _content(label),
            "checkpoint_identity_sha256": M.canonical_step_bound_checkpoint_identity(
                unit, step, _content(label)
            ),
            "optimizer_step_index": step,
            "ordinal": ordinal,
        }
        for ordinal, (step, label) in enumerate(((0, "zero"), (4, "four")))
    )
    payload = {
        "f144_semantics_sha256": semantics,
        "rows": list(rows),
        "selection_unit_sha256": unit,
    }
    raw = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    expected = hashlib.sha256(
        b"heterodiff-f146-certified-tied-best-roster-v1\0" + raw
    ).hexdigest()
    assert M.certified_tied_best_roster_sha256(unit, semantics, rows) == expected


def test_step_zero_is_accepted_and_selected() -> None:
    value = _input((0, _content("zero")), (1, _content("one")))
    result = M.select_earliest_step_tied_best(value)
    assert result["optimizer_step_index"] == 0


def test_changed_unit_with_stale_identities_refuses() -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    value["certificate"]["selection_unit_sha256"] = _content("changed-unit")
    _resign_roster(value)
    assert _refusal(value).reason_code == "STEP_BOUND_IDENTITY_MISMATCH"


def test_known_answer_selects_unique_smallest_step() -> None:
    value = _input((3, _content("c3")), (7, _content("c7")), (11, _content("c11")))
    result = M.select_earliest_step_tied_best(value)
    assert tuple(result) == M.SUCCESS_OUTPUT_KEYS
    assert result["checkpoint_selected"] is True
    assert result["optimizer_step_index"] == 3
    assert result["checkpoint_identity_sha256"] == value["rows"][0][
        "checkpoint_identity_sha256"
    ]
    assert result["caller_certifications_structurally_accepted"] is True
    assert result["production_history_authenticated"] is False
    assert result["tied_best_candidate_count"] == 3


def test_helper_is_pure_idempotent_but_does_not_authenticate_history() -> None:
    value = _input((2, _content("a")), (9, _content("b")))
    before = copy.deepcopy(value)
    first = M.select_earliest_step_tied_best(value)
    second = M.select_earliest_step_tied_best(value)
    assert first == second
    assert value == before
    assert first["production_history_authenticated"] is False


@pytest.mark.parametrize("pairs", [(), ((1, _content("single")),)])
def test_actual_tie_invocation_requires_at_least_two_rows(pairs) -> None:
    value = _input(*pairs)
    error = _refusal(value)
    assert error.reason_code == "TIE_CARDINALITY_BELOW_TWO"
    assert tuple(error.as_record()) == M.REFUSAL_OUTPUT_KEYS
    assert error.as_record()["checkpoint_selected"] is False


@pytest.mark.parametrize("bad_step", [True, False, -1, 1.0, "1", None])
def test_bool_negative_and_noninteger_steps_refuse(bad_step: Any) -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    rows = list(value["rows"])
    rows[0] = dict(rows[0])
    rows[0]["optimizer_step_index"] = bad_step
    value["rows"] = tuple(rows)
    assert _refusal(value).reason_code == "STEP_SCHEMA_NONCANONICAL"


def test_int_subclass_step_refuses() -> None:
    class IntSubclass(int):
        pass

    value = _input((1, _content("a")), (2, _content("b")))
    rows = list(value["rows"])
    rows[0] = dict(rows[0])
    rows[0]["optimizer_step_index"] = IntSubclass(1)
    value["rows"] = tuple(rows)
    assert _refusal(value).reason_code == "STEP_SCHEMA_NONCANONICAL"


def test_huge_integer_step_encoding_is_total_and_guard_independent() -> None:
    huge_step = 10**5000
    identity_default = M.canonical_step_bound_checkpoint_identity(
        M.SYNTHETIC_SELECTION_UNIT_SHA256,
        huge_step,
        _content("huge"),
    )
    assert identity_default == (
        "67773c728fef622b5b0e9ad8c18e71786e8118ecbfde349930f5a3a10c672748"
    )
    prior_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        identity_unlimited = M.canonical_step_bound_checkpoint_identity(
            M.SYNTHETIC_SELECTION_UNIT_SHA256,
            huge_step,
            _content("huge"),
        )
        value = _input((0, _content("zero")), (huge_step, _content("huge")))
        selected = M.select_earliest_step_tied_best(value)
    finally:
        sys.set_int_max_str_digits(prior_limit)
    assert identity_unlimited == identity_default
    assert selected["optimizer_step_index"] == 0


@pytest.mark.parametrize(
    "certificate_key",
    [
        "all_rows_eligible_under_f144_certified",
        "candidate_set_closed_under_future_freeze_certified",
        "complete_tied_best_roster_certified",
        "f144_semantics_final_and_frozen_certified",
        "first_and_only_invocation_certified",
    ],
)
@pytest.mark.parametrize("bad", [False, 0, 1, None, "true"])
def test_every_required_certification_must_be_exact_true(
    certificate_key: str, bad: Any
) -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    value["certificate"][certificate_key] = bad
    assert _refusal(value).reason_code == "CERTIFICATION_ABSENT_OR_FALSE"


@pytest.mark.parametrize("bad", [True, 1, -1, 1.0, "0", None])
def test_prior_invocation_count_must_be_exact_integer_zero(bad: Any) -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    value["certificate"]["prior_tie_break_invocation_count"] = bad
    assert _refusal(value).reason_code == "INVOCATION_HISTORY_SCHEMA_NONCANONICAL"


@pytest.mark.parametrize("bad", [True, 0, 1, None, "false"])
def test_helper_requires_explicit_nonauthentication_of_history(bad: Any) -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    value["certificate"]["production_history_authenticated_by_helper"] = bad
    assert _refusal(value).reason_code == "INVOCATION_HISTORY_SCHEMA_NONCANONICAL"


def test_missing_or_extra_top_level_certificate_and_row_keys_refuse() -> None:
    base = _input((1, _content("a")), (2, _content("b")))
    variants = []
    value = copy.deepcopy(base)
    value["metric_value"] = 0.1
    variants.append(value)
    value = copy.deepcopy(base)
    del value["certificate"]
    variants.append(value)
    value = copy.deepcopy(base)
    value["certificate"]["validation_direction"] = "MINIMIZE"
    variants.append(value)
    value = copy.deepcopy(base)
    rows = list(value["rows"])
    rows[0] = dict(rows[0])
    rows[0]["path"] = "checkpoint.pt"
    value["rows"] = tuple(rows)
    variants.append(value)
    for variant in variants:
        assert _refusal(variant).reason_code in {
            "TOP_LEVEL_SCHEMA_NONCANONICAL",
            "CERTIFICATE_SCHEMA_NONCANONICAL",
            "ROW_SCHEMA_NONCANONICAL",
        }


def test_exact_key_order_is_required_at_all_levels() -> None:
    base = _input((1, _content("a")), (2, _content("b")))
    top = {key: base[key] for key in reversed(M.TIE_INPUT_KEYS)}
    assert _refusal(top).reason_code == "TOP_LEVEL_SCHEMA_NONCANONICAL"

    value = copy.deepcopy(base)
    value["certificate"] = {
        key: value["certificate"][key]
        for key in reversed(M.TIE_CERTIFICATE_KEYS)
    }
    assert _refusal(value).reason_code == "CERTIFICATE_SCHEMA_NONCANONICAL"

    value = copy.deepcopy(base)
    rows = list(value["rows"])
    rows[0] = {key: rows[0][key] for key in reversed(M.TIE_ROW_KEYS)}
    value["rows"] = tuple(rows)
    assert _refusal(value).reason_code == "ROW_SCHEMA_NONCANONICAL"


def test_rows_must_be_tuple_and_ordinals_exact_ints() -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    value["rows"] = list(value["rows"])
    assert _refusal(value).reason_code == "ROW_SCHEMA_NONCANONICAL"

    for bad in (True, -1, 1.0, "0"):
        value = _input((1, _content("a")), (2, _content("b")))
        rows = list(value["rows"])
        rows[0] = dict(rows[0])
        rows[0]["ordinal"] = bad
        value["rows"] = tuple(rows)
        assert _refusal(value).reason_code == "ROW_ORDER_NONCANONICAL"


def test_duplicate_same_step_same_identity_refuses() -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    rows = [dict(value["rows"][0]), dict(value["rows"][0])]
    value["rows"] = tuple(rows)
    _resign_roster(value)
    assert _refusal(value).reason_code == "DUPLICATE_ROW_AT_ONE_STEP"


def test_same_step_conflicting_identity_or_content_refuses() -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    rows = [dict(row) for row in value["rows"]]
    rows[1]["optimizer_step_index"] = 1
    rows[1]["checkpoint_identity_sha256"] = M.canonical_step_bound_checkpoint_identity(
        value["certificate"]["selection_unit_sha256"],
        1,
        rows[1]["checkpoint_content_sha256"],
    )
    value["rows"] = tuple(rows)
    _resign_roster(value)
    assert _refusal(value).reason_code == "ROW_CONFLICT_AT_ONE_STEP"


def test_identity_reused_across_steps_refuses() -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    rows = [dict(row) for row in value["rows"]]
    rows[1]["checkpoint_identity_sha256"] = rows[0]["checkpoint_identity_sha256"]
    value["rows"] = tuple(rows)
    _resign_roster(value)
    assert _refusal(value).reason_code == "IDENTITY_ALIASED_ACROSS_STEPS"


def test_repeated_content_digest_at_distinct_steps_is_allowed() -> None:
    shared = _content("unchanged-checkpoint-content")
    value = _input((1, shared), (2, shared))
    result = M.select_earliest_step_tied_best(value)
    assert result["optimizer_step_index"] == 1
    assert value["rows"][0]["checkpoint_content_sha256"] == value["rows"][1][
        "checkpoint_content_sha256"
    ]
    assert value["rows"][0]["checkpoint_identity_sha256"] != value["rows"][1][
        "checkpoint_identity_sha256"
    ]


def test_out_of_order_rows_and_ordinal_drift_refuse() -> None:
    value = _input((1, _content("a")), (2, _content("b")), (3, _content("c")))
    rows = list(value["rows"])
    rows[1], rows[2] = rows[2], rows[1]
    rows[1] = dict(rows[1])
    rows[2] = dict(rows[2])
    rows[1]["ordinal"] = 1
    rows[2]["ordinal"] = 2
    value["rows"] = tuple(rows)
    _resign_roster(value)
    assert _refusal(value).reason_code == "ROW_ORDER_NONCANONICAL"


def test_step_bound_identity_and_roster_digest_tamper_refuse() -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    rows = list(value["rows"])
    rows[0] = dict(rows[0])
    rows[0]["checkpoint_identity_sha256"] = "0" * 64
    value["rows"] = tuple(rows)
    _resign_roster(value)
    assert _refusal(value).reason_code == "STEP_BOUND_IDENTITY_MISMATCH"

    value = _input((1, _content("a")), (2, _content("b")))
    value["tied_best_roster_sha256"] = "0" * 64
    assert _refusal(value).reason_code == "ROSTER_DIGEST_MISMATCH"


@pytest.mark.parametrize(
    "location,key",
    [
        ("certificate", "selection_unit_sha256"),
        ("certificate", "f144_semantics_sha256"),
        ("row", "checkpoint_content_sha256"),
        ("row", "checkpoint_identity_sha256"),
        ("top", "tied_best_roster_sha256"),
    ],
)
@pytest.mark.parametrize("bad", ["A" * 64, "0" * 63, "g" * 64, 0, None])
def test_every_digest_is_canonical_lowercase_sha256(
    location: str, key: str, bad: Any
) -> None:
    value = _input((1, _content("a")), (2, _content("b")))
    if location == "certificate":
        value["certificate"][key] = bad
    elif location == "row":
        rows = list(value["rows"])
        rows[0] = dict(rows[0])
        rows[0][key] = bad
        value["rows"] = tuple(rows)
    else:
        value[key] = bad
    assert _refusal(value).reason_code == "DIGEST_NONCANONICAL"


def test_rule_value_freezes_preimages_schemas_and_nonclaims() -> None:
    value = M.RULE_VALUE
    assert value["step_identity_domain_ascii"] + "\0" == M.STEP_IDENTITY_DOMAIN.decode(
        "ascii"
    )
    assert value["tied_roster_domain_ascii"] + "\0" == M.TIED_ROSTER_DOMAIN.decode(
        "ascii"
    )
    assert value["top_level_key_order"] == list(M.TIE_INPUT_KEYS)
    assert value["certificate_key_order"] == list(M.TIE_CERTIFICATE_KEYS)
    assert value["row_key_order"] == list(M.TIE_ROW_KEYS)
    assert value["success_output_key_order"] == list(M.SUCCESS_OUTPUT_KEYS)
    assert value["refusal_output_key_order"] == list(M.REFUSAL_OUTPUT_KEYS)
    assert value["pure_helper_authenticates_production_history"] is False
    assert value["future_integration_and_invocation_custody_remain_open"] is True
    assert value["optimizer_step_index_decimal_encoder_total"] is True
    assert value["optimizer_step_decimal_encoding"] == (
        "PACKAGE_LOCAL_TOTAL_BASE_1E9_CHUNKED_CANONICAL_BASE10"
    )
    assert value["repeated_content_digest_at_distinct_steps_permitted"] is True
    assert value["checkpoint_identity_reuse_across_steps_permitted"] is False
    assert value["refusal_is_not_a_scheduled_run_terminal_status"] is True
    assert value["existing_scheduled_run_terminal_status_roster"] == [
        "COMPLETE",
        "ALGORITHMIC_FAILURE",
        "NONFINITE",
        "OOM_OR_TIMEOUT",
        "INFRA_ABORT",
    ]


def test_validator_source_has_no_forbidden_effect_surface() -> None:
    source = (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed_import_roots = {
        "__future__",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "re",
        "stat",
        "typing",
    }
    forbidden_attributes = {
        "connect",
        "fork",
        "mkdir",
        "Popen",
        "rename",
        "replace",
        "run",
        "sendall",
        "socket",
        "unlink",
        "urandom",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert {alias.name.split(".")[0] for alias in node.names} <= allowed_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attributes
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "exec", "eval", "compile"}
    for token in ("random", "numpy", "scipy", "torch", "heterodiff."):
        assert token not in source


@PACKAGE_READY
def test_canonical_package_validates_exactly_one_field() -> None:
    status = M.validate(ROOT)
    assert status == {
        "B12_open": True,
        "F146_closed": True,
        "control_predicate": M.CONTROL_PREDICATE,
        "effective_open_blocker_count": 12,
        "effective_post_execution_closed": 3,
        "effective_post_execution_open": 3,
        "effective_pre_execution_closed": 23,
        "effective_pre_execution_open": 143,
        "formal_tests_closed": 0,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "results_filled": 0,
        "runtime_or_scientific_execution": False,
        "schema_version": M.SCHEMA,
        "selection_performed": False,
        "state": M.STATE,
        "tracker_edit_performed": False,
        "unresolved_fields_closed": 1,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


@PACKAGE_READY
def test_machine_is_canonical_and_exact_expected_record() -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert raw == M.canonical_machine_bytes(record)
    assert record == M.expected_record(ROOT)
    assert record["record_sha256"] == M.record_sha256(record)


@PACKAGE_READY
def test_exact_package_roster_and_noncyclic_machine_binding() -> None:
    record = _machine(ROOT)
    assert record["package_file_roster"] == [
        str(HUMAN_REL),
        str(MACHINE_REL),
        str(VALIDATOR_REL),
        str(TEST_REL),
    ]
    assert record["machine_self_binding"] == {
        "path": str(MACHINE_REL),
        "raw_self_hash_embedded": False,
        "semantic_self_digest_field": "record_sha256",
    }
    bindings = record["package_bindings_excluding_machine_self"]
    assert [row["role"] for row in bindings] == ["human", "validator", "test"]
    for row in bindings:
        raw = (ROOT / row["path"]).read_bytes()
        assert row["bytes"] == len(raw)
        assert row["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["mode_octal"] == "0644"
        assert row["nlink"] == 1
        assert row["terminal_lf"] is True


@PACKAGE_READY
def test_all_19_predecessors_are_exact_and_semantically_projected() -> None:
    record = _machine(ROOT)
    assert len(record["predecessor_bindings"]) == len(M.PREDECESSOR_SPECS) == 19
    assert record["predecessor_group_counts"] == M.PREDECESSOR_GROUP_COUNTS
    for ordinal, (row, spec) in enumerate(
        zip(record["predecessor_bindings"], M.PREDECESSOR_SPECS)
    ):
        group, role, path, byte_count, raw_sha, semantic_sha = spec
        raw = (ROOT / path).read_bytes()
        assert row["ordinal"] == ordinal
        assert row["group"] == group
        assert row["role"] == role
        assert row["path"] == path
        assert row["bytes"] == byte_count == len(raw)
        assert row["raw_sha256"] == raw_sha == hashlib.sha256(raw).hexdigest()
        assert row["terminal_lf"] is (
            path not in M.NONTERMINAL_LF_PREDECESSOR_PATHS
        )
        if semantic_sha is not None:
            assert row["record_sha256"] == semantic_sha
    assert record["predecessor_semantic_receipt"] == {
        "anti_drift_requires_named_direct_count_reduction": True,
        "base_F139_F147_values_remain_null_including_F144_and_F146": True,
        "base_optional_stopping_forbidden": True,
        "b11_after_pre_145_21_post_3_3_total_148_24": True,
        "b11_only_F168_F170_F171_closed_and_F169_open": True,
        "development_checkpoint_final_update_only_no_selection": True,
        "d1_checkpoint_ineligible_and_not_selected": True,
        "f137_after_pre_144_22_post_3_3_total_147_25": True,
        "f137_independent_review_go_and_only_F137_closed": True,
        "predecessor_execution_or_training_authorized": False,
    }


@PACKAGE_READY
def test_only_f146_and_exact_count_workstream_delta() -> None:
    record = _machine(ROOT)
    assert record["field_closures"] == [
        {
            "field_id": "F146",
            "json_pointer": M.F146_POINTER,
            "owner_role": "OWNER_B_METHOD_RUNTIME_AND_COMPUTE",
            "value": dict(M.RULE_VALUE),
        }
    ]
    assert record["count_transition"] == {
        "before": {
            "post_execution_closed": 3,
            "post_execution_open": 3,
            "pre_execution_closed": 22,
            "pre_execution_open": 144,
            "total_closed": 25,
            "total_open": 147,
        },
        "delta": {"closed": 1, "closed_fields": ["F146"], "open": -1},
        "after": {
            "post_execution_closed": 3,
            "post_execution_open": 3,
            "pre_execution_closed": 23,
            "pre_execution_open": 143,
            "total_closed": 26,
            "total_open": 146,
        },
    }
    workstreams = record["workstream_transition"]
    assert workstreams["before"]["method_runtime_compute"] == {
        "closed": 1,
        "open": 64,
    }
    assert workstreams["after"]["method_runtime_compute"] == {
        "closed": 2,
        "open": 63,
    }
    assert workstreams["before"]["theory_statistics"] == workstreams["after"][
        "theory_statistics"
    ] == {"closed": 20, "open": 34}


@PACKAGE_READY
def test_nonclosures_and_five_status_boundary_are_machine_asserted() -> None:
    record = _machine(ROOT)
    effects = record["project_effects_and_nonclaims"]
    for key in (
        "B07_remains_open",
        "B12_remains_open",
        "F139_F145_and_F147_remain_open",
        "F144_metric_direction_representation_equality_tolerance_remain_null",
        "F150_F162_compute_fields_remain_open",
        "all_12_blockers_remain_open",
    ):
        assert effects[key] is True
    for key in (
        "checkpoint_cadence_or_maximum_step_selected",
        "checkpoint_storage_retention_or_cadence_selected",
        "checkpoint_selection_or_training_performed",
        "data_entropy_runtime_or_scientific_execution_performed",
        "result_claim_or_submission_promoted",
        "tracker_or_evidence_ledger_edited",
    ):
        assert effects[key] is False
    assert record["rule_contract"][
        "refusal_is_not_a_scheduled_run_terminal_status"
    ] is True
    assert record["rule_contract"]["existing_scheduled_run_terminal_status_roster"] == [
        "COMPLETE",
        "ALGORITHMIC_FAILURE",
        "NONFINITE",
        "OOM_OR_TIMEOUT",
        "INFRA_ABORT",
    ]


@PACKAGE_READY
def test_human_contains_exact_registration_and_nonauthentication_boundary() -> None:
    human = (ROOT / HUMAN_REL).read_text(encoding="utf-8")
    assert M.EVIDENCE_READY_REGISTRATION in human
    for marker in (
        M.RULE_ID,
        M.REFUSAL,
        "f144_semantics_final_and_frozen_certified",
        "cannot observe call history",
        "production/training source",
        "same checkpoint-content digest may legitimately occur",
        "one checkpoint identity across different steps is forbidden",
        "package-local total base-`10^9` chunk encoder",
    ):
        assert marker in human


@pytest.mark.parametrize(
    "relative",
    ["../escape", "/absolute/path", "a/../b", "a/./b", "a//b", "a\\b"],
)
def test_stable_reader_rejects_noncanonical_or_escaping_paths(relative: str) -> None:
    with pytest.raises(M.ValidationError):
        M._stable_read(ROOT, relative)


def test_stable_reader_accepts_real_posix_path_and_rejects_relative_root(
    tmp_path: Path,
) -> None:
    assert M._stable_read(ROOT, M.HUMAN_PATH) == (ROOT / M.HUMAN_PATH).read_bytes()
    relative_root = Path(os.path.relpath(tmp_path, Path.cwd()))
    with pytest.raises(M.ValidationError, match="absolute"):
        M._stable_read(relative_root, M.HUMAN_PATH)


@PACKAGE_READY
@pytest.mark.parametrize("kind", ["mode", "hardlink", "symlink"])
def test_custody_substitutions_fail_closed(tmp_path: Path, kind: str) -> None:
    clone = _copy_bound_tree(tmp_path)
    target = clone / M.HUMAN_PATH
    if kind == "mode":
        target.chmod(0o755)
    elif kind == "hardlink":
        os.link(target, clone / "extra-hardlink")
    else:
        original = clone / "human-original"
        target.rename(original)
        target.symlink_to(original.name)
    with pytest.raises(M.ValidationError):
        M.validate(clone)


@PACKAGE_READY
def test_symlinked_ancestor_fails_closed(tmp_path: Path) -> None:
    clone = _copy_bound_tree(tmp_path / "clone")
    real_research = clone / "research-real"
    (clone / "research").rename(real_research)
    (clone / "research").symlink_to(real_research.name)
    with pytest.raises(M.ValidationError):
        M.validate(clone)


@PACKAGE_READY
def test_mid_read_chmod_race_is_detected(tmp_path: Path, monkeypatch) -> None:
    clone = _copy_bound_tree(tmp_path)
    target = clone / M.HUMAN_PATH
    original_read = M.os.read
    fired = False

    def racing_read(descriptor: int, count: int) -> bytes:
        nonlocal fired
        result = original_read(descriptor, count)
        if not fired:
            fired = True
            target.chmod(0o600)
        return result

    monkeypatch.setattr(M.os, "read", racing_read)
    with pytest.raises(M.ValidationError, match="after-descriptor|changed"):
        M._stable_read(clone, M.HUMAN_PATH)


@PACKAGE_READY
def test_mid_read_leaf_inode_swap_is_detected(tmp_path: Path, monkeypatch) -> None:
    clone = _copy_bound_tree(tmp_path)
    target = clone / M.HUMAN_PATH
    backup = clone / "human-race-backup"
    original_read = M.os.read
    fired = False

    def racing_read(descriptor: int, count: int) -> bytes:
        nonlocal fired
        result = original_read(descriptor, count)
        if not fired:
            fired = True
            target.rename(backup)
            shutil.copyfile(backup, target)
            target.chmod(0o644)
        return result

    monkeypatch.setattr(M.os, "read", racing_read)
    with pytest.raises(M.ValidationError, match="descriptor read|namespace changed"):
        M._stable_read(clone, M.HUMAN_PATH)


@PACKAGE_READY
def test_mid_read_ancestor_swap_is_detected(tmp_path: Path, monkeypatch) -> None:
    clone = _copy_bound_tree(tmp_path)
    target_rel = M.VALIDATOR_PATH
    research = clone / "research"
    old_research = clone / "research-race-old"
    original_read = M.os.read
    fired = False

    def racing_read(descriptor: int, count: int) -> bytes:
        nonlocal fired
        result = original_read(descriptor, count)
        if not fired:
            fired = True
            research.rename(old_research)
            research.mkdir(mode=0o755)
        return result

    monkeypatch.setattr(M.os, "read", racing_read)
    with pytest.raises(M.ValidationError, match="namespace changed"):
        M._stable_read(clone, target_rel)


def test_fingerprint_includes_full_permission_mode(tmp_path: Path) -> None:
    path = tmp_path / "mode.txt"
    path.write_text("x", encoding="ascii")
    path.chmod(0o644)
    before = M._fingerprint(path.stat())
    path.chmod(0o600)
    assert M._fingerprint(path.stat()) != before


@PACKAGE_READY
def test_noncanonical_duplicate_key_and_nonascii_machine_fail_closed(
    tmp_path: Path,
) -> None:
    clone = _copy_bound_tree(tmp_path / "space")
    machine = clone / M.MACHINE_PATH
    raw = machine.read_bytes()
    machine.write_bytes(raw[:-1] + b" \n")
    with pytest.raises(M.ValidationError, match="canonical"):
        M.validate(clone)

    clone = _copy_bound_tree(tmp_path / "duplicate")
    machine = clone / M.MACHINE_PATH
    raw = machine.read_bytes()
    machine.write_bytes(b'{"schema_version":"duplicate",' + raw[1:])
    with pytest.raises(M.ValidationError, match="strict JSON"):
        M.validate(clone)

    clone = _copy_bound_tree(tmp_path / "nonascii")
    machine = clone / M.MACHINE_PATH
    machine.write_bytes(b'{"x":"\xff"}\n')
    with pytest.raises(M.ValidationError, match="ASCII"):
        M.validate(clone)


@PACKAGE_READY
@pytest.mark.parametrize("spec_index", list(range(19)))
def test_every_predecessor_is_byte_pinned(tmp_path: Path, spec_index: int) -> None:
    clone = _copy_bound_tree(tmp_path)
    path = M.PREDECESSOR_SPECS[spec_index][2]
    target = clone / path
    target.write_bytes(target.read_bytes() + b"mutant\n")
    target.chmod(0o644)
    with pytest.raises(M.ValidationError, match="fixed binding drift"):
        M.validate(clone)


@PACKAGE_READY
@pytest.mark.parametrize("package_path", [M.HUMAN_PATH, M.VALIDATOR_PATH, M.TEST_PATH])
def test_every_nonmachine_package_byte_is_bound(
    tmp_path: Path, package_path: str
) -> None:
    clone = _copy_bound_tree(tmp_path)
    target = clone / package_path
    target.write_bytes(target.read_bytes() + b"mutant\n")
    target.chmod(0o644)
    with pytest.raises(M.ValidationError):
        M.validate(clone)


@PACKAGE_READY
@pytest.mark.parametrize(
    "mutator",
    [
        lambda r: r["field_closures"][0].__setitem__("field_id", "F144"),
        lambda r: r["field_closures"].append(
            {
                "field_id": "F143",
                "json_pointer": "/training_and_checkpoint_plan/maximum_epochs_or_steps",
                "owner_role": "OWNER_B_METHOD_RUNTIME_AND_COMPUTE",
                "value": 100,
            }
        ),
        lambda r: r["count_transition"]["after"].__setitem__("total_open", 145),
        lambda r: r["workstream_transition"]["after"]["method_runtime_compute"].__setitem__("open", 62),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("B12_remains_open", False),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("F144_metric_direction_representation_equality_tolerance_remain_null", False),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("checkpoint_storage_retention_or_cadence_selected", True),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("checkpoint_selection_or_training_performed", True),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("data_entropy_runtime_or_scientific_execution_performed", True),
        lambda r: r["rule_contract"].__setitem__("sequential_stopping_permitted", True),
        lambda r: r["rule_contract"].__setitem__("pure_helper_authenticates_production_history", True),
        lambda r: r["rule_contract"].__setitem__("f144_semantics_final_and_frozen_certification_required", False),
        lambda r: r["rule_contract"].__setitem__("optimizer_step_index_decimal_encoder_total", False),
        lambda r: r["rule_contract"].__setitem__("refusal_is_not_a_scheduled_run_terminal_status", False),
        lambda r: r["rule_contract"].__setitem__("existing_scheduled_run_terminal_status_roster", ["COMPLETE", M.REFUSAL]),
        lambda r: r["source_effect_surface"].__setitem__("validation_metric_value_accepted", True),
        lambda r: r["predecessor_semantic_receipt"].__setitem__("d1_checkpoint_ineligible_and_not_selected", False),
    ],
)
def test_fully_resigned_scope_and_false_promotion_mutants_fail(
    tmp_path: Path, mutator: Callable[[Dict[str, Any]], None]
) -> None:
    clone = _copy_bound_tree(tmp_path)
    record = _machine(clone)
    mutator(record)
    _write_resigned_machine(clone, record)
    with pytest.raises(M.ValidationError, match="machine record"):
        M.validate(clone)


@PACKAGE_READY
def test_stale_semantic_digest_fails_closed(tmp_path: Path) -> None:
    clone = _copy_bound_tree(tmp_path)
    record = _machine(clone)
    record["state"] = "MUTANT"
    (clone / M.MACHINE_PATH).write_bytes(M.canonical_machine_bytes(record))
    with pytest.raises(M.ValidationError):
        M.validate(clone)


@PACKAGE_READY
@pytest.mark.parametrize(
    "path,mutator",
    [
        (
            "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
            lambda d: d["training_and_checkpoint_plan"].__setitem__(
                "checkpoint_tie_rule", "MUTANT"
            ),
        ),
        (
            "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v2.json",
            lambda d: d["training_protocol"].__setitem__(
                "validation_checkpoint_selection_permitted", True
            ),
        ),
        (
            "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json",
            lambda d: d["future_r1_boundary"].__setitem__(
                "may_select_checkpoint_from_d1", True
            ),
        ),
        (
            "research/fixtures/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json",
            lambda d: d["comprehensive_field_sweep"].__setitem__("F169_value", "path"),
        ),
        (
            "research/fixtures/manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.json",
            lambda d: d["count_transition"]["after"].__setitem__(
                "pre_execution_open", 143
            ),
        ),
    ],
)
def test_fully_resigned_predecessor_semantic_drift_still_fails_fixed_binding(
    tmp_path: Path, path: str, mutator: Callable[[Dict[str, Any]], None]
) -> None:
    clone = _copy_bound_tree(tmp_path)
    target = clone / path
    record = json.loads(target.read_text(encoding="ascii"))
    mutator(record)
    if "record_sha256" in record:
        record["record_sha256"] = M._predecessor_record_sha256(record)
    raw = json.dumps(
        record,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    if path not in M.NONTERMINAL_LF_PREDECESSOR_PATHS:
        raw += b"\n"
    target.write_bytes(raw)
    target.chmod(0o644)
    machine = _machine(clone)
    for row in machine["predecessor_bindings"]:
        if row["path"] == path:
            row["bytes"] = len(raw)
            row["raw_sha256"] = hashlib.sha256(raw).hexdigest()
            if "record_sha256" in record:
                row["record_sha256"] = record["record_sha256"]
    _write_resigned_machine(clone, machine)
    with pytest.raises(M.ValidationError, match="fixed binding drift"):
        M.validate(clone)
