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
HUMAN_REL = Path("PROJECT_F145_VALIDATION_EARLY_STOPPING_FREEZE.md")
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_f145_validation_early_stopping_freeze_v1.json"
)
VALIDATOR_REL = Path(
    "research/diagnostics/manuscript_v3_f145_validation_early_stopping_freeze_v1.py"
)
TEST_REL = Path(
    "tests/unit/test_manuscript_v3_f145_validation_early_stopping_freeze_v1.py"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("f145_validator", ROOT / VALIDATOR_REL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = _load_validator()
PACKAGE_READY = pytest.mark.skipif(
    not (ROOT / MACHINE_REL).exists(),
    reason="canonical machine record is generated only after final package bindings",
)


def _policy(
    bound: int = 8,
    unit: str = "COMPLETED_OPTIMIZER_UPDATES",
    completed: int = 3,
    event: str = "PROGRESS",
    status: str | None = None,
    run_unit: str | None = None,
) -> Dict[str, Any]:
    return M.synthetic_policy_input(
        bound,
        unit,
        completed,
        event,
        status,
        run_unit or M.SYNTHETIC_TRAINING_RUN_UNIT_SHA256,
    )


def _refusal(value: Any) -> M.PolicyRefusal:
    with pytest.raises(M.PolicyRefusal) as caught:
        M.evaluate_no_validation_early_stopping(value)
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


def _content(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def test_exact_sentinel_pointer_policy_and_predicate() -> None:
    assert M.F145_POINTER == "/training_and_checkpoint_plan/early_stopping_patience"
    assert M.FIELD_VALUE == "DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY"
    assert M.POLICY_ID == "F145_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY_V1"
    assert M.REFUSAL == "F145_POLICY_REFUSAL_NO_EXECUTABLE_TRAINING_PLAN"
    assert M.STATE == "F145_VALIDATION_EARLY_STOPPING_DISABLED_F143_BOUND_ONLY_PREOUTCOME"


def test_independent_f143_bound_digest_known_answer() -> None:
    unit = "COMPLETED_OPTIMIZER_UPDATES"
    bound = 17
    payload = {
        "f143_bound_unit": unit,
        "f143_bound_value": bound,
    }
    raw = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    expected = hashlib.sha256(
        b"heterodiff-f145-certified-f143-bound-v1\0" + raw
    ).hexdigest()
    assert M.F143_BOUND_DOMAIN == b"heterodiff-f145-certified-f143-bound-v1\0"
    assert M.canonical_f143_bound_sha256(unit, bound) == expected


def test_huge_bound_digest_is_total_and_interpreter_guard_independent() -> None:
    huge = 10**5000
    observed_default = M.canonical_f143_bound_sha256(
        "COMPLETED_OPTIMIZER_UPDATES", huge
    )
    prior_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        payload = {
            "f143_bound_unit": "COMPLETED_OPTIMIZER_UPDATES",
            "f143_bound_value": huge,
        }
        raw = json.dumps(
            payload,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        independently_computed = hashlib.sha256(M.F143_BOUND_DOMAIN + raw).hexdigest()
        observed_unlimited = M.canonical_f143_bound_sha256(
            "COMPLETED_OPTIMIZER_UPDATES", huge
        )
        result = M.evaluate_no_validation_early_stopping(
            _policy(bound=huge, completed=0)
        )
    finally:
        sys.set_int_max_str_digits(prior_limit)
    assert observed_default == (
        "4a505819360f58720b4960d73b98ddd95f9c365f4a8c9463ebc5ce3810673f96"
    )
    assert observed_default == independently_computed == observed_unlimited
    assert result["action"] == "CONTINUE_TO_F143_BOUND"


@pytest.mark.parametrize(
    "unit,bound",
    [
        ("COMPLETED_OPTIMIZER_UPDATES", 1),
        ("COMPLETED_OPTIMIZER_UPDATES", 19),
        ("COMPLETED_EPOCHS", 1),
        ("COMPLETED_EPOCHS", 7),
    ],
)
def test_two_units_and_two_bounds_complete_only_at_exact_bound(
    unit: str, bound: int
) -> None:
    progress = M.evaluate_no_validation_early_stopping(
        _policy(bound=bound, unit=unit, completed=0)
    )
    complete = M.evaluate_no_validation_early_stopping(
        _policy(
            bound=bound,
            unit=unit,
            completed=bound,
            event="TERMINAL_STATUS",
            status="COMPLETE",
        )
    )
    assert progress["action"] == "CONTINUE_TO_F143_BOUND"
    assert progress["scheduled_run_status"] is None
    assert complete["action"] == "TERMINAL_COMPLETE_AT_EXACT_F143_BOUND"
    assert complete["scheduled_run_status"] == "COMPLETE"
    assert complete["f143_bound_unit"] == unit
    assert complete["f143_bound_value"] == bound


@pytest.mark.parametrize("completed", [0, 2, 7])
def test_progress_before_bound_continues_without_validation_signal(
    completed: int,
) -> None:
    result = M.evaluate_no_validation_early_stopping(
        _policy(bound=8, completed=completed)
    )
    assert result["action"] == "CONTINUE_TO_F143_BOUND"
    assert result["validation_early_stopping_used"] is False
    assert result["production_history_authenticated"] is False


@pytest.mark.parametrize("status", list(M.FAILURE_STATUSES))
@pytest.mark.parametrize("completed", [0, 7, 8])
def test_each_existing_failure_status_may_terminate_without_early_stopping(
    status: str, completed: int
) -> None:
    result = M.evaluate_no_validation_early_stopping(
        _policy(
            bound=8,
            completed=completed,
            event="TERMINAL_STATUS",
            status=status,
        )
    )
    assert result["action"] == "TERMINAL_EXISTING_FAILURE_STATUS"
    assert result["scheduled_run_status"] == status
    assert result["validation_early_stopping_used"] is False


@pytest.mark.parametrize("completed", [0, 1, 7])
def test_complete_before_bound_refuses(completed: int) -> None:
    value = _policy(
        bound=8,
        completed=completed,
        event="TERMINAL_STATUS",
        status="COMPLETE",
    )
    assert _refusal(value).reason_code == "STATUS_BOUNDARY_MISMATCH"


def test_progress_at_bound_and_any_overshoot_refuse() -> None:
    assert _refusal(_policy(bound=8, completed=8)).reason_code == (
        "PROGRESS_AT_BOUND_REQUIRES_COMPLETE_STATUS"
    )
    for event, status in (
        ("PROGRESS", None),
        ("TERMINAL_STATUS", "COMPLETE"),
        ("TERMINAL_STATUS", "INFRA_ABORT"),
    ):
        assert _refusal(
            _policy(bound=8, completed=9, event=event, status=status)
        ).reason_code == "F143_BOUND_OVERSHOOT"


@pytest.mark.parametrize("bad", [0, -1, True, False, 1.0, "1", None])
def test_bound_requires_positive_exact_builtin_integer(bad: Any) -> None:
    value = _policy()
    value["certificate"]["f143_bound_value"] = bad
    assert _refusal(value).reason_code == "BOUND_SCHEMA_NONCANONICAL"


def test_bound_integer_subclass_refuses() -> None:
    class IntSubclass(int):
        pass

    value = _policy()
    value["certificate"]["f143_bound_value"] = IntSubclass(8)
    assert _refusal(value).reason_code == "BOUND_SCHEMA_NONCANONICAL"


@pytest.mark.parametrize("bad", [-1, True, False, 1.0, "1", None])
def test_completed_units_require_nonnegative_exact_builtin_integer(bad: Any) -> None:
    value = _policy()
    value["observation"]["completed_units"] = bad
    assert _refusal(value).reason_code == "EVENT_SCHEMA_NONCANONICAL"


def test_completed_integer_subclass_refuses() -> None:
    class IntSubclass(int):
        pass

    value = _policy()
    value["observation"]["completed_units"] = IntSubclass(3)
    assert _refusal(value).reason_code == "EVENT_SCHEMA_NONCANONICAL"


@pytest.mark.parametrize(
    "bad",
    [
        "completed_optimizer_updates",
        "COMPLETED_OPTIMIZER_UPDATE",
        "COMPLETED_EPOCH",
        " COMPLETED_EPOCHS",
        "COMPLETED_EPOCHS ",
        "",
        None,
        1,
        True,
    ],
)
def test_bound_unit_requires_one_exact_allowed_builtin_string(bad: Any) -> None:
    value = _policy()
    value["certificate"]["f143_bound_unit"] = bad
    assert _refusal(value).reason_code == "BOUND_UNIT_NONCANONICAL"


def test_bound_unit_string_subclass_refuses() -> None:
    class StringSubclass(str):
        pass

    value = _policy()
    value["certificate"]["f143_bound_unit"] = StringSubclass(
        "COMPLETED_OPTIMIZER_UPDATES"
    )
    assert _refusal(value).reason_code == "BOUND_UNIT_NONCANONICAL"


@pytest.mark.parametrize(
    "bad",
    [
        None,
        0,
        False,
        True,
        "",
        "DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY ",
        "disabled_no_validation_early_stopping_f143_bound_only",
        "NOT_APPLICABLE_VALIDATION_EARLY_STOPPING_DISABLED",
        {"disabled": True},
        float("inf"),
    ],
)
def test_neutral_sentinel_rejects_every_alias_or_nonstring(bad: Any) -> None:
    value = _policy()
    value["policy_value"] = bad
    assert _refusal(value).reason_code == "POLICY_SENTINEL_NONCANONICAL"


def test_sentinel_string_subclass_refuses() -> None:
    class StringSubclass(str):
        pass

    value = _policy()
    value["policy_value"] = StringSubclass(M.FIELD_VALUE)
    assert _refusal(value).reason_code == "POLICY_SENTINEL_NONCANONICAL"


@pytest.mark.parametrize("bad", [False, 0, 1, None, "true"])
def test_f143_finality_certificate_must_be_exact_true(bad: Any) -> None:
    value = _policy()
    value["certificate"]["f143_bound_final_and_frozen_certified"] = bad
    assert _refusal(value).reason_code == "BOUND_NOT_FINAL_OR_FROZEN"


@pytest.mark.parametrize("bad", [True, 0, 1, None, "false"])
def test_helper_requires_explicit_production_history_nonauthentication(
    bad: Any,
) -> None:
    value = _policy()
    value["certificate"]["production_history_authenticated_by_helper"] = bad
    assert _refusal(value).reason_code == (
        "HISTORY_AUTHENTICATION_CLAIM_NONCANONICAL"
    )


def test_bound_digest_mismatch_refuses_after_value_or_unit_change() -> None:
    value = _policy()
    value["certificate"]["f143_bound_value"] = 9
    assert _refusal(value).reason_code == "F143_BOUND_DIGEST_MISMATCH"

    value = _policy()
    value["certificate"]["f143_bound_unit"] = "COMPLETED_EPOCHS"
    assert _refusal(value).reason_code == "F143_BOUND_DIGEST_MISMATCH"


def test_correctly_recomputed_bound_digest_accepts_changed_bound_and_unit() -> None:
    value = _policy(bound=12, unit="COMPLETED_EPOCHS", completed=4)
    result = M.evaluate_no_validation_early_stopping(value)
    assert result["f143_bound_sha256"] == M.canonical_f143_bound_sha256(
        "COMPLETED_EPOCHS", 12
    )


@pytest.mark.parametrize("bad", ["0" * 64, "A" * 64, "x", None, 1, True])
def test_bound_or_run_digest_requires_canonical_lowercase_sha256(bad: Any) -> None:
    for location in (
        ("certificate", "f143_bound_sha256"),
        ("certificate", "training_run_unit_sha256"),
        ("observation", "training_run_unit_sha256"),
    ):
        value = _policy()
        value[location[0]][location[1]] = bad
        assert _refusal(value).reason_code in {
            "DIGEST_NONCANONICAL",
            "F143_BOUND_DIGEST_MISMATCH",
            "TRAINING_RUN_UNIT_MISMATCH",
        }


def test_training_run_unit_mismatch_refuses() -> None:
    value = _policy()
    value["observation"]["training_run_unit_sha256"] = _content("other-run")
    assert _refusal(value).reason_code == "TRAINING_RUN_UNIT_MISMATCH"


def test_policy_id_requires_exact_builtin_string() -> None:
    for bad in (M.POLICY_ID + " ", M.POLICY_ID.lower(), None, 1, True):
        value = _policy()
        value["certificate"]["policy_id"] = bad
        assert _refusal(value).reason_code == "POLICY_SENTINEL_NONCANONICAL"

    class StringSubclass(str):
        pass

    value = _policy()
    value["certificate"]["policy_id"] = StringSubclass(M.POLICY_ID)
    assert _refusal(value).reason_code == "POLICY_SENTINEL_NONCANONICAL"


def test_exact_key_order_required_at_all_levels() -> None:
    base = _policy()
    top = {key: base[key] for key in reversed(M.POLICY_INPUT_KEYS)}
    assert _refusal(top).reason_code == "POLICY_INPUT_SCHEMA_NONCANONICAL"

    value = _policy()
    value["certificate"] = {
        key: value["certificate"][key]
        for key in reversed(M.POLICY_CERTIFICATE_KEYS)
    }
    assert _refusal(value).reason_code == "CERTIFICATE_SCHEMA_NONCANONICAL"

    value = _policy()
    value["observation"] = {
        key: value["observation"][key]
        for key in reversed(M.POLICY_OBSERVATION_KEYS)
    }
    assert _refusal(value).reason_code == "OBSERVATION_SCHEMA_NONCANONICAL"


@pytest.mark.parametrize("shadow", list(M.POLICY_CONTRACT["shadow_fields_forbidden"]))
def test_every_patience_monitor_or_shadow_field_is_refused(shadow: str) -> None:
    for location in ("top", "certificate", "observation"):
        value = _policy()
        target = value if location == "top" else value[location]
        target[shadow] = 1
        assert _refusal(value).reason_code in {
            "POLICY_INPUT_SCHEMA_NONCANONICAL",
            "CERTIFICATE_SCHEMA_NONCANONICAL",
            "OBSERVATION_SCHEMA_NONCANONICAL",
        }


@pytest.mark.parametrize(
    "shadow",
    [
        "validation_metric",
        "validation_value",
        "f144_semantics_sha256",
        "checkpoint_identity_sha256",
        "f146_checkpoint_choice",
        "retry_count",
        "resume_from_checkpoint",
        "extra_epochs",
        "duration_seconds",
    ],
)
def test_cross_field_or_runtime_shadow_inputs_are_refused(shadow: str) -> None:
    value = _policy()
    value["observation"][shadow] = None
    assert _refusal(value).reason_code == "OBSERVATION_SCHEMA_NONCANONICAL"


@pytest.mark.parametrize("bad", ["", "PROGRESS ", "COMPLETE", None, 1, True])
def test_event_kind_requires_exact_known_string(bad: Any) -> None:
    value = _policy()
    value["observation"]["event_kind"] = bad
    assert _refusal(value).reason_code == "EVENT_SCHEMA_NONCANONICAL"


@pytest.mark.parametrize(
    "bad",
    ["EARLY_STOPPED", M.FIELD_VALUE, M.REFUSAL, "PASS", "", None, 1, True],
)
def test_terminal_event_rejects_unknown_or_sixth_status(bad: Any) -> None:
    value = _policy(event="TERMINAL_STATUS", status=bad)
    assert _refusal(value).reason_code == "TERMINAL_STATUS_NONCANONICAL"


def test_progress_event_rejects_any_terminal_status() -> None:
    for status in M.SCHEDULED_RUN_STATUSES:
        assert _refusal(_policy(event="PROGRESS", status=status)).reason_code == (
            "EVENT_SCHEMA_NONCANONICAL"
        )


def test_helper_is_pure_idempotent_but_does_not_authenticate_or_prevent_replay() -> None:
    value = _policy()
    before = copy.deepcopy(value)
    first = M.evaluate_no_validation_early_stopping(value)
    second = M.evaluate_no_validation_early_stopping(value)
    assert first == second
    assert value == before
    assert first["production_history_authenticated"] is False


def test_success_and_refusal_output_schemas_are_exact() -> None:
    success = M.evaluate_no_validation_early_stopping(_policy())
    assert tuple(success) == M.SUCCESS_OUTPUT_KEYS
    assert success["policy_value"] == M.FIELD_VALUE
    assert success["validation_early_stopping_used"] is False

    refusal = _refusal(None)
    record = refusal.as_record()
    assert tuple(record) == M.REFUSAL_OUTPUT_KEYS
    assert record == {
        "disposition": M.REFUSAL,
        "executable_training_plan_produced": False,
        "policy_id": M.POLICY_ID,
        "reason_code": "POLICY_INPUT_SCHEMA_NONCANONICAL",
    }


def test_policy_contract_freezes_nonclaims_statuses_and_schemas() -> None:
    contract = M.POLICY_CONTRACT
    assert contract["exact_field_value"] == M.FIELD_VALUE
    assert contract["f143_bound_units"] == list(M.BOUND_UNITS)
    assert contract["f143_bound_digest_domain_ascii"] + "\0" == (
        M.F143_BOUND_DOMAIN.decode("ascii")
    )
    assert contract["existing_scheduled_run_terminal_status_roster"] == list(
        M.SCHEDULED_RUN_STATUSES
    )
    assert contract["earlier_terminal_statuses"] == list(M.FAILURE_STATUSES)
    assert contract["refusal_is_not_a_scheduled_run_terminal_status"] is True
    assert contract["validation_early_stopping_enabled"] is False
    assert contract["patience_counter_exists"] is False
    assert contract[
        "validation_monitor_direction_min_delta_or_stop_signal_exists"
    ] is False
    assert contract[
        "validation_warmup_cadence_reset_smoothing_or_best_so_far_exists"
    ] is False
    assert contract["validation_shadow_stopping_field_exists"] is False
    assert contract[
        "resume_restart_retry_rerun_or_replacement_permitted_by_f145"
    ] is False
    assert contract["f148_infrastructure_rerun_permitted"] is False
    assert contract["f146_checkpoint_choice_may_change_training_duration"] is False
    assert contract["pure_helper_authenticates_production_history_or_f143_finality"] is False
    assert contract["top_level_key_order"] == list(M.POLICY_INPUT_KEYS)
    assert contract["certificate_key_order"] == list(M.POLICY_CERTIFICATE_KEYS)
    assert contract["observation_key_order"] == list(M.POLICY_OBSERVATION_KEYS)
    assert contract["success_output_key_order"] == list(M.SUCCESS_OUTPUT_KEYS)
    assert contract["refusal_output_key_order"] == list(M.REFUSAL_OUTPUT_KEYS)


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
        "F145_closed": True,
        "control_predicate": M.CONTROL_PREDICATE,
        "effective_open_blocker_count": 12,
        "effective_post_execution_closed": 3,
        "effective_post_execution_open": 3,
        "effective_pre_execution_closed": 24,
        "effective_pre_execution_open": 142,
        "formal_tests_closed": 0,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "results_filled": 0,
        "runtime_or_scientific_execution": False,
        "schema_version": M.SCHEMA,
        "state": M.STATE,
        "tracker_edit_performed": False,
        "training_or_early_stopping_performed": False,
        "unresolved_fields_closed": 1,
        "validation": "PASS",
    }


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
def test_all_28_predecessors_are_exact_and_semantically_projected() -> None:
    record = _machine(ROOT)
    assert len(record["predecessor_bindings"]) == len(M.PREDECESSOR_SPECS) == 28
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
        "base_F143_F144_F145_values_null": True,
        "base_validation_early_stopping_allowed_only_if_frozen": True,
        "base_experiment_optional_stopping_forbidden": True,
        "b11_after_pre_145_21_post_3_3_total_148_24": True,
        "b11_only_F168_F170_F171_closed_and_F169_open": True,
        "development_final_update_only_no_selection_or_early_stopping": True,
        "d1_checkpoint_ineligible_and_not_selected": True,
        "f148_never_true_no_infrastructure_rerun": True,
        "f137_after_pre_144_22_post_3_3_total_147_25": True,
        "f137_independent_review_go_and_only_F137_closed": True,
        "f146_after_pre_143_23_post_3_3_total_146_26": True,
        "f146_independent_review_go_and_only_F146_closed": True,
        "f146_preserves_existing_five_scheduled_statuses": True,
        "predecessor_execution_or_training_authorized": False,
    }


@PACKAGE_READY
def test_only_f145_exact_string_and_exact_count_workstream_delta() -> None:
    record = _machine(ROOT)
    assert record["field_closures"] == [
        {
            "field_id": "F145",
            "json_pointer": M.F145_POINTER,
            "owner_role": "OWNER_B_METHOD_RUNTIME_AND_COMPUTE",
            "value": M.FIELD_VALUE,
        }
    ]
    assert type(record["field_closures"][0]["value"]) is str
    assert record["count_transition"] == {
        "before": {
            "post_execution_closed": 3,
            "post_execution_open": 3,
            "pre_execution_closed": 23,
            "pre_execution_open": 143,
            "total_closed": 26,
            "total_open": 146,
        },
        "delta": {"closed": 1, "closed_fields": ["F145"], "open": -1},
        "after": {
            "post_execution_closed": 3,
            "post_execution_open": 3,
            "pre_execution_closed": 24,
            "pre_execution_open": 142,
            "total_closed": 27,
            "total_open": 145,
        },
    }
    workstreams = record["workstream_transition"]
    assert workstreams["before"]["method_runtime_compute"] == {
        "closed": 2,
        "open": 63,
    }
    assert workstreams["after"]["method_runtime_compute"] == {
        "closed": 3,
        "open": 62,
    }


@PACKAGE_READY
def test_nonclosures_f146_f148_and_second_b12_boundary_are_machine_asserted() -> None:
    record = _machine(ROOT)
    effects = record["project_effects_and_nonclaims"]
    for key in (
        "B07_remains_open",
        "B12_remains_open",
        "F139_F144_and_F147_remain_open",
        "F143_bound_value_and_unit_remain_open",
        "F144_metric_direction_representation_equality_tolerance_remain_null",
        "F146_prior_checkpoint_tie_rule_closure_preserved",
        "F148_never_true_no_infrastructure_rerun_preserved",
        "F150_F162_compute_fields_remain_open",
        "all_12_blockers_remain_open",
    ):
        assert effects[key] is True
    for key in (
        "checkpoint_choice_may_change_training_duration",
        "checkpoint_cadence_or_maximum_horizon_selected",
        "checkpoint_storage_retention_or_cadence_selected",
        "checkpoint_selection_or_training_performed",
        "data_entropy_runtime_or_scientific_execution_performed",
        "result_claim_or_submission_promoted",
        "third_consecutive_B12_package_authorized_without_scope_review",
        "tracker_or_evidence_ledger_edited",
        "validation_early_stopping_patience_counter_or_shadow_field_created",
    ):
        assert effects[key] is False
    qualification = record["qualification_boundary"]
    assert qualification["second_consecutive_B12_package"] is True
    assert qualification[
        "pure_helper_authenticates_f143_finality_or_production_history"
    ] is False


@PACKAGE_READY
def test_human_contains_exact_policy_registration_and_nonauthentication() -> None:
    human = (ROOT / HUMAN_REL).read_text(encoding="utf-8")
    assert M.EVIDENCE_READY_REGISTRATION in human
    for marker in (
        M.FIELD_VALUE,
        M.POLICY_ID,
        M.REFUSAL,
        "cannot prove that a future F143 record is truly final",
        "second consecutive B12 package",
        "any third consecutive B12 package requires explicit scope review",
        "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN",
        "checkpoint choice under F146 may not",
        "production/training source",
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
        M._stable_read(clone, M.VALIDATOR_PATH)


def test_fingerprint_includes_full_permission_mode(tmp_path: Path) -> None:
    path = tmp_path / "mode.txt"
    path.write_text("x", encoding="ascii")
    path.chmod(0o644)
    before = M._fingerprint(path.stat())
    path.chmod(0o600)
    assert M._fingerprint(path.stat()) != before


@PACKAGE_READY
@pytest.mark.parametrize("kind", ["whitespace", "duplicate", "nonascii"])
def test_noncanonical_machine_json_fails_closed(tmp_path: Path, kind: str) -> None:
    clone = _copy_bound_tree(tmp_path)
    machine = clone / M.MACHINE_PATH
    raw = machine.read_bytes()
    if kind == "whitespace":
        machine.write_bytes(raw[:-1] + b" \n")
    elif kind == "duplicate":
        machine.write_bytes(b'{"state":"MUTANT",' + raw[1:])
    else:
        machine.write_bytes(raw[:-1] + b"\xc3\xa9\n")
    machine.chmod(0o644)
    with pytest.raises(M.ValidationError):
        M.validate(clone)


@PACKAGE_READY
@pytest.mark.parametrize("spec_index", list(range(28)))
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
        lambda r: r["field_closures"][0].__setitem__("field_id", "F143"),
        lambda r: r["field_closures"][0].__setitem__("value", None),
        lambda r: r["field_closures"][0].__setitem__("value", 0),
        lambda r: r["field_closures"][0].__setitem__("value", {"disabled": True}),
        lambda r: r["count_transition"]["after"].__setitem__("total_open", 144),
        lambda r: r["workstream_transition"]["after"]["method_runtime_compute"].__setitem__("open", 61),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("B12_remains_open", False),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("F143_bound_value_and_unit_remain_open", False),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("F146_prior_checkpoint_tie_rule_closure_preserved", False),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("F148_never_true_no_infrastructure_rerun_preserved", False),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("checkpoint_choice_may_change_training_duration", True),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("validation_early_stopping_patience_counter_or_shadow_field_created", True),
        lambda r: r["project_effects_and_nonclaims"].__setitem__("third_consecutive_B12_package_authorized_without_scope_review", True),
        lambda r: r["policy_contract"].__setitem__("validation_early_stopping_enabled", True),
        lambda r: r["policy_contract"].__setitem__("patience_counter_exists", True),
        lambda r: r["policy_contract"].__setitem__("validation_monitor_direction_min_delta_or_stop_signal_exists", True),
        lambda r: r["policy_contract"].__setitem__("validation_shadow_stopping_field_exists", True),
        lambda r: r["policy_contract"].__setitem__("f148_infrastructure_rerun_permitted", True),
        lambda r: r["policy_contract"].__setitem__("f146_checkpoint_choice_may_change_training_duration", True),
        lambda r: r["policy_contract"].__setitem__("existing_scheduled_run_terminal_status_roster", [*M.SCHEDULED_RUN_STATUSES, M.REFUSAL]),
        lambda r: r["policy_contract"].__setitem__("pure_helper_authenticates_production_history_or_f143_finality", True),
        lambda r: r["qualification_boundary"].__setitem__("second_consecutive_B12_package", False),
        lambda r: r["source_effect_surface"].__setitem__("validation_metric_value_accepted", True),
        lambda r: r["source_effect_surface"].__setitem__("validation_patience_monitor_or_stop_signal_accepted", True),
        lambda r: r["predecessor_semantic_receipt"].__setitem__("f148_never_true_no_infrastructure_rerun", False),
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


def _rebind_mutated_predecessor(
    clone: Path,
    path: str,
    mutator: Callable[[Dict[str, Any]], None],
    monkeypatch,
) -> None:
    target = clone / path
    record = json.loads(target.read_text(encoding="ascii"))
    mutator(record)
    if "record_sha256" in record:
        record["record_sha256"] = M._predecessor_record_sha256(record)
    raw = M.canonical_machine_bytes(record)
    target.write_bytes(raw)
    target.chmod(0o644)
    specs = list(M.PREDECESSOR_SPECS)
    index = next(index for index, spec in enumerate(specs) if spec[2] == path)
    group, role, _, _, _, semantic = specs[index]
    specs[index] = (
        group,
        role,
        path,
        len(raw),
        hashlib.sha256(raw).hexdigest(),
        record.get("record_sha256") if semantic is not None else None,
    )
    monkeypatch.setattr(M, "PREDECESSOR_SPECS", tuple(specs))


@PACKAGE_READY
@pytest.mark.parametrize(
    "path,mutator,expected",
    [
        (
            "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
            lambda d: d["training_and_checkpoint_plan"].__setitem__(
                "early_stopping_patience", 3
            ),
            "base preregistration training plan",
        ),
        (
            "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
            lambda d: d["training_and_checkpoint_plan"].__setitem__(
                "maximum_epochs_or_steps", 100
            ),
            "base preregistration training plan",
        ),
        (
            "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
            lambda d: d["downstream_contract"].__setitem__(
                "infrastructure_rerun_predicate", "RETRY_ONCE"
            ),
            "Gate-A F148",
        ),
        (
            "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json",
            lambda d: d["count_transition"]["after"].__setitem__(
                "pre_execution_open", 142
            ),
            "F146 count anchor",
        ),
        (
            "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json",
            lambda d: d["rule_contract"].__setitem__(
                "existing_scheduled_run_terminal_status_roster",
                [*M.SCHEDULED_RUN_STATUSES, "EARLY_STOPPED"],
            ),
            "F146 five-status",
        ),
        (
            "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json",
            lambda d: d["project_effects_and_nonclaims"].__setitem__(
                "B12_remains_open", False
            ),
            "F146 nonclosure",
        ),
    ],
)
def test_fully_resigned_and_rebound_predecessor_semantic_drift_fails(
    tmp_path: Path,
    monkeypatch,
    path: str,
    mutator: Callable[[Dict[str, Any]], None],
    expected: str,
) -> None:
    clone = _copy_bound_tree(tmp_path)
    _rebind_mutated_predecessor(clone, path, mutator, monkeypatch)
    with pytest.raises(M.ValidationError, match=expected):
        M.validate(clone)
