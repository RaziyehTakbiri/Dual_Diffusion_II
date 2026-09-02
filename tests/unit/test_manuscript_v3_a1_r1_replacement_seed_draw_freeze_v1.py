"""Hostile pre-draw checks for the one-shot R1-A1 seed replacement."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
HUMAN_PATH = ROOT / "manuscript_v3/a1_r1_replacement_seed_draw_freeze_v1.md"
MACHINE_PATH = ROOT / (
    "research/fixtures/" "manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.json"
)
MODULE_PATH = ROOT / (
    "research/diagnostics/finite_association_r1_replacement_seed_draw.py"
)
TEST_PATH = Path(__file__).resolve()
FREEZE_DOMAIN = b"heterodiff-manuscript-v3-a1-r1-replacement-seed-draw-freeze-v1\0"


def _load_module():
    specification = importlib.util.spec_from_file_location(
        "finite_association_r1_replacement_seed_draw_test_target", MODULE_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


DRAW = _load_module()


@pytest.fixture(autouse=True)
def _forbid_live_entropy_for_entire_suite(monkeypatch):
    def forbidden(_: int) -> bytes:
        raise AssertionError("focused pre-draw suite touched live entropy")

    monkeypatch.setattr(DRAW.secrets, "token_bytes", forbidden)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _semantic_digest(value: Mapping[str, Any], domain: bytes) -> str:
    body = dict(value)
    body["record_sha256"] = None
    return _sha256(domain + _canonical_json(body))


def _load_freeze(root: Path = ROOT) -> Tuple[bytes, Dict[str, Any]]:
    payload = (root / MACHINE_PATH.relative_to(ROOT)).read_bytes()
    value = json.loads(payload.decode("ascii"))
    assert type(value) is dict
    return payload, value


def _file_row(root: Path, relative_path: str) -> Dict[str, Any]:
    payload = (root / relative_path).read_bytes()
    return {
        "path": relative_path,
        "raw_sha256": _sha256(payload),
        "bytes": len(payload),
        "lf_count": payload.count(b"\n"),
        "terminal_lf": payload.endswith(b"\n"),
        "semantic_sha256": None,
    }


def _independent_unrank(rank: int) -> int:
    candidate = rank
    while True:
        fixed_point = rank + sum(
            1 for excluded in DRAW.ORIGINAL_SEEDS if excluded <= candidate
        )
        if fixed_point == candidate:
            return candidate
        candidate = fixed_point


def _copy_static_workspace(tmp_path: Path) -> Path:
    _, freeze = _load_freeze()
    groups = (
        "baseline_bindings",
        "closure_v2_bindings",
        "d1_bindings",
        "environment_bindings",
        "historical_source_bindings",
        "registration_bindings",
    )
    paths = {MACHINE_PATH.relative_to(ROOT).as_posix()}
    for group in groups:
        paths.update(row["path"] for row in freeze[group].values())
    for relative_path in sorted(paths):
        source = ROOT / relative_path
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    return tmp_path


def _synthetic_marker(
    workspace: Path,
) -> Tuple[Dict[str, Any], bytes, Dict[str, Any]]:
    _, freeze = DRAW._load_canonical_freeze(workspace)
    DRAW._assert_freeze_contract(workspace, freeze)
    marker_payload, marker = DRAW._consume_attempt(workspace, freeze)
    return freeze, marker_payload, marker


def test_machine_freeze_is_canonical_one_line_self_digested_json() -> None:
    payload, freeze = _load_freeze()
    assert payload == _canonical_json(freeze) + b"\n"
    assert payload.count(b"\n") == 1
    assert payload.endswith(b"\n")
    assert freeze["record_sha256"] == _semantic_digest(freeze, FREEZE_DOMAIN)


def test_four_new_paths_are_exactly_hash_bound_without_a_cycle() -> None:
    _, freeze = _load_freeze()
    expected = {
        "human_freeze": HUMAN_PATH.relative_to(ROOT).as_posix(),
        "orchestration_module": MODULE_PATH.relative_to(ROOT).as_posix(),
        "hostile_test": TEST_PATH.relative_to(ROOT).as_posix(),
    }
    assert set(freeze["registration_bindings"]) == set(expected)
    for role, relative_path in expected.items():
        assert freeze["registration_bindings"][role] == _file_row(ROOT, relative_path)


def test_all_predecessors_reopen_to_exact_bound_bytes() -> None:
    _, freeze = _load_freeze()
    expected_groups = {
        "baseline_bindings": DRAW.EXPECTED_BASELINE_BINDINGS,
        "closure_v2_bindings": DRAW.EXPECTED_CLOSURE_BINDINGS,
        "d1_bindings": DRAW.EXPECTED_D1_BINDINGS,
        "environment_bindings": DRAW.EXPECTED_ENVIRONMENT_BINDINGS,
        "historical_source_bindings": DRAW.EXPECTED_HISTORICAL_SOURCE_BINDINGS,
    }
    for group, expected in expected_groups.items():
        assert set(freeze[group]) == set(expected)
        for role, (relative_path, raw_sha256, semantic_sha256) in expected.items():
            row = _file_row(ROOT, relative_path)
            row["semantic_sha256"] = semantic_sha256
            assert freeze[group][role] == row
            assert row["raw_sha256"] == raw_sha256


def test_exact_historical_seven_are_custody_only_and_unchanged() -> None:
    _, freeze = _load_freeze()
    historical = freeze["historical_source_bindings"]
    assert len(historical) == 7
    assert set(historical) == {
        "residual_data",
        "residual_training",
        "exact_population",
        "sampled_isolated_runner",
        "exact_population_isolated_runner",
        "test_only_execution_order",
        "production_order",
    }
    boundary = freeze["state_preservation"]
    assert boundary["historical_sources_mutated"] is False
    assert boundary["historical_sources_imported_by_draw_module"] is False
    assert boundary["historical_sources_used_for_execution"] is False
    assert boundary["production_order_mutated"] is False
    assert boundary["production_order_admissible"] is False


def test_user_decision_binding_is_exact_but_not_selection_input() -> None:
    _, freeze = _load_freeze()
    decision = freeze["decision_binding"]
    assert decision == {
        "normalized_recommendation_text": (
            "One material statistical choice prevents an executable R1 freeze: "
            "should we preserve eight paired seeds by generating a new "
            "outcome-independent replacement for 1729—recommended—or proceed "
            "with seven clean seeds?"
        ),
        "normalized_recommendation_text_utf8_sha256": (
            "c15926195485cf8f6245fc57aca0c6951d408a7f33844551e596db061caacbb2"
        ),
        "normalized_assent_text": (
            "Please move forward with your recommended option above."
        ),
        "normalized_assent_text_utf8_sha256": (
            "0a8ee5fc5192bd9e2a6c11150e01b26418896eba08eb01af23eb6a210359e301"
        ),
        "normalization_policy": (
            "REMOVE_UI_FORMATTING_AND_TRAILING_WHITESPACE_PRESERVE_UNICODE_TEXT_UTF8"
        ),
        "interpretation": "ONE_REPLACEMENT_KEEP_EIGHT",
        "decision_selects_replacement_value": False,
        "decision_is_entropy": False,
    }
    assert _sha256(decision["normalized_recommendation_text"].encode("utf-8")) == (
        decision["normalized_recommendation_text_utf8_sha256"]
    )
    assert _sha256(decision["normalized_assent_text"].encode("utf-8")) == (
        decision["normalized_assent_text_utf8_sha256"]
    )
    anti = freeze["anti_selection_boundary"]
    assert anti["user_decision_bytes_used_in_mapping"] is False
    assert anti["user_decision_hash_used_in_mapping"] is False


def test_exact_unbiased_selection_constants_and_arithmetic() -> None:
    _, freeze = _load_freeze()
    selection = freeze["selection_contract"]
    assert DRAW.UNIVERSE_SIZE == 2**53 == 9007199254740992
    assert DRAW.ORIGINAL_SEEDS == (
        1729,
        3253,
        5003,
        7411,
        10007,
        13007,
        16001,
        20011,
    )
    assert DRAW.ALLOWED_COUNT == DRAW.UNIVERSE_SIZE - 8 == 9007199254740984
    assert (2**256) % DRAW.ALLOWED_COUNT == 64
    assert DRAW.REJECTION_REMAINDER == 64
    assert DRAW.ACCEPTANCE_LIMIT == 2**256 - 64
    assert selection["universe_size_u"] == DRAW.UNIVERSE_SIZE
    assert selection["allowed_count_m"] == DRAW.ALLOWED_COUNT
    assert selection["acceptance_limit_l"] == str(DRAW.ACCEPTANCE_LIMIT)
    assert selection["entropy_space"] == str(2**256)
    assert selection["redraw_permitted"] is False
    assert selection["rejection_burns_attempt"] is True


@pytest.mark.parametrize(
    ("entropy_integer", "accepted", "rank", "candidate"),
    [
        (0, True, 0, 0),
        (1728, True, 1728, 1728),
        (1729, True, 1729, 1730),
        (3251, True, 3251, 3252),
        (3252, True, 3252, 3254),
        (2**256 - 65, True, (2**256 - 65) % (2**53 - 8), None),
        (2**256 - 64, False, None, None),
        (2**256 - 1, False, None, None),
    ],
)
def test_selection_boundary_vectors_are_independently_recomputed(
    entropy_integer: int,
    accepted: bool,
    rank: Any,
    candidate: Any,
) -> None:
    entropy = entropy_integer.to_bytes(32, "big")
    selected = DRAW._select_replacement_seed(entropy)
    assert selected["accepted"] is accepted
    assert selected["rank"] == rank
    if accepted:
        independent_candidate = _independent_unrank(rank)
        if candidate is not None:
            assert independent_candidate == candidate
        assert selected["replacement_seed"] == independent_candidate
        assert selected["replacement_seed"] not in DRAW.ORIGINAL_SEEDS
    else:
        assert selected["replacement_seed"] is None


def test_unranking_boundaries_never_emit_an_original_seed() -> None:
    ranks = {0, DRAW.ALLOWED_COUNT - 1}
    for excluded in DRAW.ORIGINAL_SEEDS:
        ranks.update(
            rank
            for rank in range(max(0, excluded - 10), excluded + 10)
            if rank < DRAW.ALLOWED_COUNT
        )
    for rank in sorted(ranks):
        candidate = DRAW._unrank_allowed_seed(rank)
        assert candidate == _independent_unrank(rank)
        assert 0 <= candidate < 2**53
        assert candidate not in DRAW.ORIGINAL_SEEDS


def test_independent_terminal_oracle_matches_frozen_vectors() -> None:
    entropy_integers = [
        0,
        1728,
        1729,
        3251,
        3252,
        DRAW.ACCEPTANCE_LIMIT - 1,
        DRAW.ACCEPTANCE_LIMIT,
        2**256 - 1,
    ]
    for entropy_integer in entropy_integers:
        entropy = entropy_integer.to_bytes(32, "big")
        independent = DRAW._independent_audit_selection(entropy)
        production = DRAW._select_replacement_seed(entropy)
        assert independent == production


def test_terminal_audit_ast_cannot_call_production_selection_helpers() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    audit_source = ast.unparse(functions["_audit_terminal"])
    oracle_source = ast.unparse(functions["_independent_audit_selection"])
    expected_source = ast.unparse(functions["_independent_expected_draw"])
    for forbidden in ("_select_replacement_seed", "_unrank_allowed_seed"):
        assert forbidden not in audit_source
        assert forbidden not in oracle_source
        assert forbidden not in expected_source
    assert "divmod" in oracle_source
    assert "while lower < upper" in oracle_source


@pytest.mark.parametrize("bad", [b"", b"0" * 31, b"0" * 33, bytearray(32)])
def test_selection_rejects_nonexact_entropy_bytes(bad: Any) -> None:
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        DRAW._select_replacement_seed(bad)


def test_ast_has_one_literal_public_entropy_call_and_marker_precedes_it() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "secrets"
        and node.func.attr == "token_bytes"
    ]
    assert len(calls) == 1
    call = calls[0]
    assert len(call.args) == 1
    assert isinstance(call.args[0], ast.Constant) and call.args[0].value == 32
    execute = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_execute_one_shot_from_canonical_cli"
    )
    consume_calls = [
        node
        for node in ast.walk(execute)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_consume_attempt"
    ]
    assert len(consume_calls) == 1
    assert consume_calls[0].lineno < call.lineno
    signature = inspect.signature(DRAW._execute_one_shot_from_canonical_cli)
    assert list(signature.parameters) == []
    assert "execute_one_shot" not in DRAW.__all__


def test_ast_import_allowlist_and_selection_purity() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {
        "__future__",
        "argparse",
        "ctypes",
        "errno",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "secrets",
        "stat",
        "sys",
        "typing",
    }
    assert imported.isdisjoint(
        {
            "numpy",
            "torch",
            "subprocess",
            "socket",
            "urllib",
            "http",
            "requests",
            "time",
            "datetime",
            "uuid",
            "random",
            "heterodiff",
        }
    )
    function_nodes = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    selection_source = "\n".join(
        ast.unparse(function_nodes[name])
        for name in ("_select_replacement_seed", "_unrank_allowed_seed")
    ).lower()
    for forbidden in (
        "d1",
        "decision",
        "hash",
        "metric",
        "checkpoint",
        "path(",
        "open(",
        "seedsequence",
        "manual_seed",
    ):
        assert forbidden not in selection_source


def test_module_contains_required_exclusive_durable_primitives() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    for token in (
        "os.O_EXCL",
        "os.O_NOFOLLOW",
        "os.fsync",
        "_rename_directory_noclobber",
        "renameatx_np",
        "renameat2",
        "_revalidate_static_inputs",
        "_audit_terminal",
    ):
        assert token in source
    assert "os.rename(" not in source
    assert "os.replace(" not in source


def test_status_and_static_audit_touch_zero_entropy(monkeypatch, capsys) -> None:
    calls = []

    def forbidden_entropy(_: int) -> bytes:
        calls.append(True)
        raise AssertionError("read-only mode touched entropy")

    monkeypatch.setattr(DRAW.secrets, "token_bytes", forbidden_entropy)
    audit = DRAW.audit_freeze(ROOT)
    observed = DRAW.status(ROOT)
    assert audit["status"] == "PASS_ZERO_ENTROPY_ZERO_EXECUTION"
    assert observed == {
        "schema": "heterodiff-r1-a1-replacement-seed-draw-status-v1",
        "state": "R1_A1_SEED_DRAW_AUTHORIZED_NOT_YET_CONSUMED",
        "attempt_marker_present": False,
        "pending_terminal_present": False,
        "terminal_output_present": False,
        "validated_terminal_kind": None,
        "entropy_contacted_by_status": False,
        "candidate_seed_reported": False,
        "first_attempt_available": True,
        "retry_permitted": False,
    }
    assert DRAW.main(["--status"]) == 0
    assert DRAW.main(["--audit-freeze"]) == 0
    output = capsys.readouterr().out
    assert "candidate" not in output.lower()
    assert calls == []


def test_live_draw_is_canonical_direct_file_cli_only(monkeypatch) -> None:
    _, freeze = _load_freeze()
    custody = freeze["custody_protocol"]
    assert custody["live_execution_interface"] == (
        "CANONICAL_DIRECT_FILE_CLI_ONLY_ZERO_SUPPLIED_ROOT"
    )
    assert custody["canonical_workspace_root"] == ROOT.as_posix()
    assert custody["canonical_python_relative_path"] == ".venv-m1/bin/python"
    assert custody["canonical_execution_argv"] == [
        "research/diagnostics/finite_association_r1_replacement_seed_draw.py",
        "--execute-one-shot",
    ]
    assert custody["canonical_orig_argv"] == [
        "/Library/Frameworks/Python.framework/Versions/3.11/Resources/"
        "Python.app/Contents/MacOS/Python",
        "-I",
        "-S",
        "-B",
        "research/diagnostics/finite_association_r1_replacement_seed_draw.py",
        "--execute-one-shot",
    ]
    assert custody["native_process_argv_method"] == (
        "DARWIN_LIBC__NSGETARGC__NSGETARGV_UTF8_STRICT"
    )
    assert custody["canonical_native_process_argv"] == custody["canonical_orig_argv"]
    assert custody["canonical_interpreter_realpath"] == (
        "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
    )
    assert custody["canonical_execution_command"] == (
        ".venv-m1/bin/python -I -S -B "
        "research/diagnostics/finite_association_r1_replacement_seed_draw.py "
        "--execute-one-shot"
    )
    assert custody["required_python_flags"] == {
        "isolated": 1,
        "no_site": 1,
        "dont_write_bytecode": 1,
        "safe_path": True,
    }
    assert custody["readable_live_execution_capability_key_present"] is False
    assert custody["actual_main_module_identity_required"] is True
    assert custody["canonical_writers_recheck_complete_live_cli_boundary"] is True
    assert custody["canonical_writers_recheck_native_process_argv"] is True
    assert custody["python_argv_vectors_alone_are_authoritative"] is False
    assert (
        custody["native_process_argv_is_immutable_against_same_process_memory_mutation"]
        is False
    )
    assert custody["procedural_honest_host_process_boundary"] is True
    assert custody["hostile_same_user_process_sandbox_claimed"] is False
    assert custody["same_process_memory_tamper_resistance_claimed"] is False
    assert custody["module_global_tamper_resistance_claimed"] is False
    assert custody["registered_file_tamper_resistance_claimed"] is False
    assert custody["ordinary_import_runpy_python_vector_only_forgery_refuses"] is True
    assert (
        custody["ordinary_import_or_runpy_monkeypatched_entropy_execution_permitted"]
        is False
    )
    assert custody["runpy_forged_argv_execution_permitted"] is False
    assert custody["forged_python_argv_vectors_from_dash_c_permitted"] is False
    calls = []

    def forbidden_entropy(_: int) -> bytes:
        calls.append(True)
        raise AssertionError("imported execution touched entropy")

    monkeypatch.setattr(DRAW.secrets, "token_bytes", forbidden_entropy)
    with pytest.raises(DRAW.FreezeError, match="direct-file __main__"):
        DRAW._execute_one_shot_from_canonical_cli()
    with pytest.raises(DRAW.FreezeError, match="direct-file __main__"):
        DRAW.main(["--execute-one-shot"])
    assert not hasattr(DRAW, "_LIVE_EXECUTION_KEY")
    assert calls == []


def test_live_draw_refuses_alternate_root_wrong_flags_and_supplied_write(
    tmp_path: Path,
) -> None:
    with pytest.raises(DRAW.FreezeError, match="alternate workspace"):
        DRAW._require_canonical_workspace(tmp_path)
    for hostile in (
        SimpleNamespace(isolated=0, no_site=1, dont_write_bytecode=1, safe_path=True),
        SimpleNamespace(isolated=1, no_site=0, dont_write_bytecode=1, safe_path=True),
        SimpleNamespace(isolated=1, no_site=1, dont_write_bytecode=0, safe_path=True),
        SimpleNamespace(isolated=1, no_site=1, dont_write_bytecode=1, safe_path=False),
    ):
        with pytest.raises(DRAW.FreezeError, match="isolation flags"):
            DRAW._require_live_runtime_flags(hostile)
    _, freeze = DRAW._load_canonical_freeze(ROOT)
    with pytest.raises(DRAW.FreezeError, match="direct-file __main__"):
        DRAW._consume_attempt(ROOT, freeze)
    with pytest.raises(DRAW.FreezeError, match="direct-file __main__"):
        DRAW._publish_selection(ROOT, freeze, b"{}", {}, bytes(32))
    assert not (ROOT / DRAW.ATTEMPT_RELATIVE_PATH).exists()


def test_runpy_forged_sys_argv_cannot_bypass_orig_argv(
    monkeypatch,
) -> None:
    calls = []

    def forbidden_entropy(_: int) -> bytes:
        calls.append(True)
        raise AssertionError("runpy forgery touched entropy")

    monkeypatch.setattr(DRAW.secrets, "token_bytes", forbidden_entropy)
    monkeypatch.setattr(
        sys,
        "argv",
        [DRAW.MODULE_RELATIVE_PATH, "--execute-one-shot"],
    )
    with pytest.raises(RuntimeError, match="orig_argv"):
        runpy.run_path(DRAW.MODULE_RELATIVE_PATH, run_name="__main__")
    assert calls == []
    assert not (ROOT / DRAW.ATTEMPT_RELATIVE_PATH).exists()


def test_dash_c_forged_python_vectors_cannot_bypass_native_process_argv() -> None:
    module_path = (ROOT / DRAW.MODULE_RELATIVE_PATH).as_posix()
    marker_path = (ROOT / DRAW.ATTEMPT_RELATIVE_PATH).as_posix()
    forged_code = "\n".join(
        [
            "import os, pathlib, secrets, sys",
            "module_path = pathlib.Path(%r)" % module_path,
            "marker_path = pathlib.Path(%r)" % marker_path,
            "source = module_path.read_text(encoding='utf-8')",
            "def forbidden_entropy(_): raise RuntimeError('LIVE_ENTROPY_TOUCHED')",
            "secrets.token_bytes = forbidden_entropy",
            "real_os_open = os.open",
            "def guarded_os_open(path, flags, *args, **kwargs):",
            "    if pathlib.Path(path) == marker_path:",
            "        raise RuntimeError('CANONICAL_WRITE_ATTEMPTED')",
            "    return real_os_open(path, flags, *args, **kwargs)",
            "os.open = guarded_os_open",
            "sys.argv = %r" % list(DRAW.CANONICAL_EXECUTION_ARGV),
            "sys.orig_argv = %r" % list(DRAW.CANONICAL_ORIG_ARGV),
            "globals()['__file__'] = str(module_path)",
            "exec(compile(source, str(module_path), 'exec'), globals(), globals())",
        ]
    )
    completed = subprocess.run(
        [
            (ROOT / DRAW.CANONICAL_PYTHON_RELATIVE_PATH).as_posix(),
            "-I",
            "-S",
            "-B",
            "-c",
            forged_code,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "native process argv is not the frozen vector" in completed.stderr
    assert "LIVE_ENTROPY_TOUCHED" not in completed.stderr
    assert "CANONICAL_WRITE_ATTEMPTED" not in completed.stderr
    assert not (ROOT / DRAW.ATTEMPT_RELATIVE_PATH).exists()
    assert not (ROOT / DRAW.PENDING_RELATIVE_PATH).exists()
    assert not (ROOT / DRAW.OUTPUT_RELATIVE_PATH).exists()


def test_every_canonical_writer_rechecks_native_process_argv() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    assert "_native_process_argv" in ast.unparse(
        functions["_require_live_cli_boundary"]
    )
    expected_scope_guard = {
        "_write_new_file": "_require_path_write_scope",
        "_consume_attempt": "_require_write_scope",
        "_make_pending_directory": "_require_write_scope",
        "_rename_directory_noclobber": "_require_path_write_scope",
        "_publish_pending": "_require_write_scope",
        "_publish_failure_without_draw": "_require_write_scope",
        "_publish_selection": "_require_write_scope",
        "_execute_one_shot_from_canonical_cli": "_require_live_cli_boundary",
    }
    for name, guard in expected_scope_guard.items():
        assert guard in ast.unparse(functions[name])


def test_pre_draw_workspace_has_no_attempt_pending_or_terminal_output() -> None:
    for relative_path in (
        DRAW.ATTEMPT_RELATIVE_PATH,
        DRAW.PENDING_RELATIVE_PATH,
        DRAW.OUTPUT_RELATIVE_PATH,
    ):
        assert not (ROOT / relative_path).exists()
        assert not (ROOT / relative_path).is_symlink()
    assert len(DRAW.CHECKED_PRODUCTION_ROOTS) == 11
    for relative_path in DRAW.CHECKED_PRODUCTION_ROOTS:
        assert not (ROOT / relative_path).exists()
    assert not (ROOT / DRAW.FORMAL_RUNTIME_IDENTITY_RELATIVE_PATH).exists()


def test_synthetic_success_is_atomic_deeply_reopened_and_nonexecuting(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    selection = DRAW._select_replacement_seed(bytes(32))
    assert selection["replacement_seed"] == 0
    assert (
        DRAW._publish_selection(
            workspace,
            freeze,
            marker_payload,
            marker,
            bytes(32),
        )
        == "SUCCESS"
    )
    output = workspace / DRAW.OUTPUT_RELATIVE_PATH
    assert {path.name for path in output.iterdir()} == {
        "seed-draw-record.json",
        "replacement-seed-registry.json",
        "success-receipt.json",
    }
    registry = json.loads((output / "replacement-seed-registry.json").read_bytes())
    assert registry["replacement_seed_registry"] == [
        0,
        3253,
        5003,
        7411,
        10007,
        13007,
        16001,
        20011,
    ]
    assert registry["replacement_ordinal"] == 0
    assert output.stat().st_mode & 0o077 == 0
    assert (workspace / DRAW.ATTEMPT_RELATIVE_PATH).stat().st_mode & 0o077 == 0
    for path in output.iterdir():
        assert path.stat().st_mode & 0o077 == 0
    monkeypatch.setattr(
        DRAW.secrets,
        "token_bytes",
        lambda _: (_ for _ in ()).throw(AssertionError("entropy touched")),
    )
    observed = DRAW.status(workspace)
    assert observed["state"] == "ATTEMPT_SPENT_TERMINAL_SUCCESS"
    assert observed["validated_terminal_kind"] == "SUCCESS"
    with pytest.raises(DRAW.AttemptSpentError):
        DRAW._consume_attempt(workspace, freeze)


def test_synthetic_tail_rejection_burns_attempt_without_registry(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    entropy = DRAW.ACCEPTANCE_LIMIT.to_bytes(32, "big")
    selection = DRAW._select_replacement_seed(entropy)
    assert selection["accepted"] is False
    assert (
        DRAW._publish_selection(workspace, freeze, marker_payload, marker, entropy)
        == "FAILURE"
    )
    output = workspace / DRAW.OUTPUT_RELATIVE_PATH
    assert {path.name for path in output.iterdir()} == {
        "seed-draw-record.json",
        "failure-receipt.json",
    }
    assert not (output / "replacement-seed-registry.json").exists()
    monkeypatch.setattr(
        DRAW.secrets,
        "token_bytes",
        lambda _: (_ for _ in ()).throw(AssertionError("entropy touched")),
    )
    assert DRAW.status(workspace)["validated_terminal_kind"] == "FAILURE"
    with pytest.raises(DRAW.AttemptSpentError):
        DRAW._consume_attempt(workspace, freeze)


def test_consumed_marker_without_terminal_is_nonretryable_and_zero_entropy(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    _synthetic_marker(workspace)
    calls = []

    def forbidden_entropy(_: int) -> bytes:
        calls.append(True)
        raise AssertionError("replay touched entropy")

    monkeypatch.setattr(DRAW.secrets, "token_bytes", forbidden_entropy)
    observed = DRAW.status(workspace)
    assert observed["state"] == "ATTEMPT_SPENT_TERMINAL_ABSENT_OR_PENDING_NO_RETRY"
    assert observed["first_attempt_available"] is False
    assert observed["retry_permitted"] is False
    _, freeze = DRAW._load_canonical_freeze(workspace)
    with pytest.raises(DRAW.AttemptSpentError):
        DRAW._consume_attempt(workspace, freeze)
    assert calls == []


def test_artifacts_parent_symlink_is_refused_before_marker_or_entropy(
    tmp_path: Path,
) -> None:
    real_artifacts = tmp_path / "real-artifacts"
    real_artifacts.mkdir()
    (tmp_path / "artifacts").symlink_to(real_artifacts, target_is_directory=True)
    with pytest.raises(DRAW.FreezeError, match="nonsymlink directory"):
        DRAW._consume_attempt(tmp_path, {"record_sha256": "0" * 64})
    assert list(real_artifacts.iterdir()) == []


def test_terminal_publication_is_atomic_noclobber_under_race(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    original = DRAW._revalidate_static_inputs
    calls = []

    def race(root: Path, digest: str):
        value = original(root, digest)
        calls.append(True)
        if len(calls) == 1:
            (workspace / DRAW.OUTPUT_RELATIVE_PATH).mkdir()
        return value

    monkeypatch.setattr(DRAW, "_revalidate_static_inputs", race)
    with pytest.raises(DRAW.AttemptSpentError, match="appeared"):
        DRAW._publish_selection(
            workspace,
            freeze,
            marker_payload,
            marker,
            bytes(32),
        )
    assert (workspace / DRAW.PENDING_RELATIVE_PATH).is_dir()
    assert (workspace / DRAW.OUTPUT_RELATIVE_PATH).is_dir()


def test_static_input_mutation_before_publication_burns_and_refuses_success(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    original = DRAW._revalidate_static_inputs

    def mutate_then_validate(root: Path, digest: str):
        human = root / DRAW.HUMAN_FREEZE_RELATIVE_PATH
        human.write_bytes(human.read_bytes() + b"hostile-drift\n")
        return original(root, digest)

    monkeypatch.setattr(DRAW, "_revalidate_static_inputs", mutate_then_validate)
    with pytest.raises(DRAW.FreezeError, match="registration binding mismatch"):
        DRAW._publish_selection(
            workspace,
            freeze,
            marker_payload,
            marker,
            bytes(32),
        )
    assert (workspace / DRAW.ATTEMPT_RELATIVE_PATH).is_file()
    assert (workspace / DRAW.PENDING_RELATIVE_PATH).is_dir()
    assert not (workspace / DRAW.OUTPUT_RELATIVE_PATH).exists()


def test_production_root_appearance_before_rename_burns_and_refuses_publication(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    original = DRAW._revalidate_static_inputs

    def inject_root_then_validate(root: Path, digest: str):
        (root / DRAW.CHECKED_PRODUCTION_ROOTS[4]).mkdir(parents=True)
        return original(root, digest)

    monkeypatch.setattr(DRAW, "_revalidate_static_inputs", inject_root_then_validate)
    with pytest.raises(DRAW.FreezeError, match="production-root absence"):
        DRAW._publish_selection(workspace, freeze, marker_payload, marker, bytes(32))
    assert (workspace / DRAW.ATTEMPT_RELATIVE_PATH).is_file()
    assert (workspace / DRAW.PENDING_RELATIVE_PATH).is_dir()
    assert not (workspace / DRAW.OUTPUT_RELATIVE_PATH).exists()


def test_runtime_manifest_appearance_after_rename_invalidates_terminal(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    original = DRAW._rename_directory_noclobber

    def rename_then_inject_runtime(source: Path, target: Path) -> None:
        original(source, target)
        runtime = workspace / DRAW.FORMAL_RUNTIME_IDENTITY_RELATIVE_PATH
        runtime.write_bytes(b"hostile-runtime-manifest")

    monkeypatch.setattr(DRAW, "_rename_directory_noclobber", rename_then_inject_runtime)
    with pytest.raises(DRAW.FreezeError, match="formal-runtime-manifest absence"):
        DRAW._publish_selection(workspace, freeze, marker_payload, marker, bytes(32))
    assert (workspace / DRAW.ATTEMPT_RELATIVE_PATH).is_file()
    assert (workspace / DRAW.OUTPUT_RELATIVE_PATH).is_dir()
    with pytest.raises(DRAW.FreezeError, match="formal-runtime-manifest absence"):
        DRAW.status(workspace)


def test_deep_status_rejects_terminal_hash_registry_and_claim_forgery(
    tmp_path: Path,
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    entropy = (123456789).to_bytes(32, "big")
    DRAW._publish_selection(
        workspace,
        freeze,
        marker_payload,
        marker,
        entropy,
    )
    registry_path = (
        workspace / DRAW.OUTPUT_RELATIVE_PATH / "replacement-seed-registry.json"
    )
    registry = json.loads(registry_path.read_bytes())
    registry["r1_execution_authorized"] = True
    registry_path.write_bytes(_canonical_json(registry))
    with pytest.raises(DRAW.FreezeError):
        DRAW.status(workspace)


def test_deep_status_rejects_semantically_rehashed_bool_int_alias(
    tmp_path: Path,
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    entropy = (987654321).to_bytes(32, "big")
    DRAW._publish_selection(workspace, freeze, marker_payload, marker, entropy)
    output = workspace / DRAW.OUTPUT_RELATIVE_PATH
    registry_path = output / "replacement-seed-registry.json"
    receipt_path = output / "success-receipt.json"
    registry = json.loads(registry_path.read_bytes())
    registry["replacement_ordinal"] = False
    registry["record_sha256"] = DRAW._record_digest(registry, DRAW.REGISTRY_DOMAIN)
    registry_payload = _canonical_json(registry)
    registry_path.write_bytes(registry_payload)
    receipt = json.loads(receipt_path.read_bytes())
    receipt["replacement_seed_registry_raw_sha256"] = _sha256(registry_payload)
    receipt["replacement_seed_registry_sha256"] = registry["record_sha256"]
    receipt["record_sha256"] = DRAW._record_digest(receipt, DRAW.SUCCESS_DOMAIN)
    receipt_path.write_bytes(_canonical_json(receipt))
    with pytest.raises(DRAW.FreezeError, match="replacement registry mismatch"):
        DRAW.status(workspace)


@pytest.mark.parametrize(
    ("path", "hostile"),
    [
        (("selection_contract", "redraw_permitted"), True),
        (("selection_contract", "allowed_count_m"), 7),
        (("selection_contract", "draw_count"), True),
        (("decision_binding", "decision_is_entropy"), True),
        (("decision_binding", "decision_selects_replacement_value"), 0),
        (("nonclaims", "confirmatory_execution_authorized"), True),
        (("nonclaims", "production_execution_authorized"), 0),
        (("nonclaims", "claim_promoted"), True),
        (("current_pre_draw_state", "entropy_contacted"), True),
        (("d1_exposure_boundary", "d1_metric_bytes_used_in_selection"), True),
        (("custody_protocol", "procedural_honest_host_process_boundary"), False),
        (("custody_protocol", "hostile_same_user_process_sandbox_claimed"), True),
        (
            (
                "custody_protocol",
                "native_process_argv_is_immutable_against_same_process_memory_mutation",
            ),
            True,
        ),
    ],
)
def test_semantically_rehashed_hostile_gate_flips_are_rejected(
    path: Tuple[str, str], hostile: Any
) -> None:
    _, freeze = _load_freeze()
    forged = deepcopy(freeze)
    forged[path[0]][path[1]] = hostile
    forged["record_sha256"] = _semantic_digest(forged, FREEZE_DOMAIN)
    with pytest.raises(DRAW.FreezeError):
        DRAW._assert_freeze_contract(ROOT, forged)


@pytest.mark.parametrize(
    "path",
    [
        ("selection_contract",),
        ("decision_binding",),
        ("d1_exposure_boundary",),
        ("custody_protocol",),
        ("state_preservation",),
        ("nonclaims",),
        ("historical_source_bindings", "production_order"),
    ],
)
def test_unknown_nested_contradictions_are_rejected(path: Tuple[str, ...]) -> None:
    _, freeze = _load_freeze()
    forged = deepcopy(freeze)
    target = forged
    for component in path:
        target = target[component]
    target["hostile_unknown_permission"] = True
    forged["record_sha256"] = _semantic_digest(forged, FREEZE_DOMAIN)
    with pytest.raises(DRAW.FreezeError):
        DRAW._assert_freeze_contract(ROOT, forged)


def test_static_audit_rejects_stale_bound_bytes(tmp_path: Path) -> None:
    workspace = _copy_static_workspace(tmp_path)
    target = workspace / "requirements/m1-reference-macos-arm64-py311.lock"
    target.write_bytes(target.read_bytes() + b"drift\n")
    with pytest.raises(DRAW.FreezeError, match="binding mismatch"):
        DRAW.audit_freeze(workspace)


def test_draw_builder_rejects_caller_supplied_entropy_selection_mismatch(
    tmp_path: Path,
) -> None:
    workspace = _copy_static_workspace(tmp_path)
    freeze, marker_payload, marker = _synthetic_marker(workspace)
    entropy = bytes(32)
    hostile_selection = DRAW._select_replacement_seed(entropy)
    hostile_selection["replacement_seed"] = 1729
    with pytest.raises(DRAW.FreezeError, match="entropy selection mismatch"):
        DRAW._draw_record(
            freeze,
            marker_payload,
            marker,
            entropy,
            hostile_selection,
        )


def test_current_state_authorizes_only_the_future_draw() -> None:
    _, freeze = _load_freeze()
    assert freeze["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert freeze["milestone_state"] == ("R1_A1_SEED_DRAW_AUTHORIZED_NOT_YET_CONSUMED")
    current = freeze["current_pre_draw_state"]
    assert current == {
        "attempt_marker_present": False,
        "pending_terminal_present": False,
        "terminal_output_present": False,
        "attempt_consumed": False,
        "entropy_contacted": False,
        "draw_performed": False,
        "replacement_seed": None,
        "replacement_registry": None,
        "execution_performed": False,
    }
    assert all(value is False for value in freeze["nonclaims"].values())


def test_downstream_projection_is_frozen_before_seed_value() -> None:
    _, freeze = _load_freeze()
    projection = freeze["future_output_contract"]["downstream_coordinate_projection"]
    assert projection == {
        "exact_population_coordinate_count": 24,
        "primary_coordinate_count": 48,
        "control_coordinate_count": 72,
        "complete_sampled_coordinate_count": 120,
        "all_coordinates_including_exact_count": 144,
        "replacement_applies_to_ordinal_zero_across_every_method_lane_budget": True,
        "numeric_registry_resort_permitted": False,
        "post_draw_grid_pruning_permitted": False,
        "partial_lane_substitution_permitted": False,
    }
    assert 24 + 48 + 72 == 144
    assert 48 + 72 == 120


def test_post_draw_integration_is_separate_additive_and_not_authorized() -> None:
    _, freeze = _load_freeze()
    state = freeze["state_preservation"]
    assert state["all_checked_production_roots"] == list(DRAW.CHECKED_PRODUCTION_ROOTS)
    assert state["any_checked_production_root_present"] is False
    assert state["formal_runtime_identity_manifest_path"] == (
        DRAW.FORMAL_RUNTIME_IDENTITY_RELATIVE_PATH
    )
    assert state["formal_runtime_identity_manifest_present"] is False
    assert state["historical_sources_remain_immutable_through_draw_publication"] is True
    assert (
        state["separate_registry_integration_source_amendment_milestone_required"]
        is True
    )
    assert (
        state[
            "registry_integration_required_before_any_r1_runner_or_production_execution"
        ]
        is True
    )
    assert state["registry_integration_or_source_amendment_authorized_here"] is False


def test_raw_future_custody_is_internal_owner_only_and_not_publishable() -> None:
    _, freeze = _load_freeze()
    boundary = freeze["publication_anonymity_boundary"]
    paths = boundary["future_raw_custody_paths"]
    assert DRAW.ATTEMPT_RELATIVE_PATH in paths
    assert DRAW.PENDING_RELATIVE_PATH in paths
    assert DRAW.OUTPUT_RELATIVE_PATH in paths
    assert DRAW.OUTPUT_RELATIVE_PATH + "/seed-draw-record.json" in paths
    assert DRAW.OUTPUT_RELATIVE_PATH + "/replacement-seed-registry.json" in paths
    assert DRAW.OUTPUT_RELATIVE_PATH + "/success-receipt.json" in paths
    assert DRAW.OUTPUT_RELATIVE_PATH + "/failure-receipt.json" in paths
    assert boundary["future_raw_custody_contains_entropy_hex"] is True
    assert (
        boundary["future_raw_custody_anonymous_submission_inclusion_permitted"] is False
    )
    assert boundary["future_raw_custody_public_release_inclusion_permitted"] is False
    assert boundary["future_custody_directory_owner_only_mode_required"] == (
        "0700_NO_GROUP_OTHER_BITS"
    )
    assert boundary["future_custody_file_owner_only_mode_required"] == (
        "0600_NO_GROUP_OTHER_BITS"
    )


def test_d1_is_exposure_disclosure_only_and_cannot_select_anything() -> None:
    _, freeze = _load_freeze()
    d1 = freeze["d1_exposure_boundary"]
    assert d1["exposed_seed"] == 1729
    assert d1["whole_seed_exposure_scope"] == (
        "ALL_METHODS_LANES_AND_BUDGETS_WITH_BUDGET_WILDCARD_WHERE_NOT_APPLICABLE"
    )
    assert d1["disposition"] == "PILOT_NONCONFIRMATORY_EXPOSED"
    for name in (
        "d1_metric_bytes_used_in_selection",
        "d1_checkpoint_bytes_used_in_selection",
        "d1_hashes_used_in_selection",
        "d1_timestamps_used_in_selection",
        "d1_process_metadata_used_in_selection",
        "d1_runtime_metadata_used_in_selection",
        "d1_metric_direction_used_in_selection",
        "d1_used_to_define_success_rule",
        "d1_used_to_change_overflow_policy",
    ):
        assert d1[name] is False
    assert freeze["anti_selection_boundary"]["candidate_screening_permitted"] is False
    assert freeze["anti_selection_boundary"]["candidate_top_up_permitted"] is False
    assert freeze["anti_selection_boundary"]["candidate_redraw_permitted"] is False


def test_human_freeze_contains_mandatory_visible_boundaries() -> None:
    text = HUMAN_PATH.read_text(encoding="utf-8")
    required = (
        "One material statistical choice prevents an executable R1 freeze",
        "Please move forward with your recommended option above.",
        "ONE_REPLACEMENT_KEEP_EIGHT",
        "R1_A1_SEED_DRAW_AUTHORIZED_NOT_YET_CONSUMED",
        "DRAFT_NOT_EXECUTABLE",
        "2^53",
        "2^256 - 64",
        "secrets.token_bytes(32)",
        "ordinal zero",
        "all methods, lanes, and budgets",
        "rejection burns the attempt",
        "no redraw",
        "marker is durable before entropy",
        "O_EXCL",
        "O_NOFOLLOW",
        "atomic no-clobber",
        "no candidate is printed",
        "D1 metrics",
        "not selection inputs",
        "historical seven",
        "no rank execution",
        "no training execution",
        "not a submission artifact",
    )
    for phrase in required:
        assert phrase in text
