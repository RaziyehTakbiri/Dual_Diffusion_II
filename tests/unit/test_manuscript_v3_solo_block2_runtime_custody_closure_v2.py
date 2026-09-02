from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v2.py"
EXECUTOR = ROOT / "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v2.py"
MACHINE = ROOT / "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v2.json"
V1_ROOT = ROOT / "research/custody/solo_block2_public_documentation_runtime_v1"
V2_ROOT = ROOT / "research/custody/solo_block2_public_documentation_runtime_v2"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_final_validator_passes_from_unrelated_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load(VALIDATOR, "closure_v2_validator")
    monkeypatch.chdir("/private/tmp")
    result = module.validate(ROOT)
    assert result["status"] == "PASS"
    assert result["v2_fetches_performed"] == 0


def test_machine_is_canonical_and_self_digested() -> None:
    raw = MACHINE.read_bytes()
    value = json.loads(raw)
    assert raw == json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
    claimed = value["record_sha256"]
    value["record_sha256"] = None
    assert hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n").hexdigest() == claimed


def test_exact_requests_and_limits_are_unchanged() -> None:
    module = _load(VALIDATOR, "closure_v2_requests")
    machine = json.loads(MACHINE.read_bytes())
    for row, request in zip(machine["operation_roster"], module.REQUESTS):
        assert row["request_sha256"] == hashlib.sha256(request).hexdigest()
        assert (row["attempt_limit"], row["retry_limit"], row["redirect_limit"]) == (1, 0, 0)


def test_executor_ast_has_exact_network_surface_and_order() -> None:
    source = EXECUTOR.read_text()
    tree = ast.parse(source)
    dotted = _load(VALIDATOR, "closure_v2_ast")._dotted
    calls = [dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    for name in ("socket.getaddrinfo", "socket.socket", "ssl.SSLContext", "tls.sendall"):
        assert calls.count(name) == 1
    attempt = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "attempt")
    text = ast.get_source_segment(source, attempt)
    assert text.index("_revalidate_runtime_immediately_before_reservation(") < text.index("_mkdir_row(")
    assert text.index('_exclusive_canonical_at(rowfd, "intent.json", intent)') < text.index("_perform_spent_attempt(")


def test_manifest_fix_is_exact_and_has_no_stable_volatile_carveout() -> None:
    source = EXECUTOR.read_text()
    assert "return [version, list(release), machine]" in source
    assert "_canonical_bytes(admitted) != _canonical_bytes(" in source
    machine = json.loads(MACHINE.read_bytes())
    contract = machine["runtime_manifest_contract"]
    assert contract["full_manifest_exact_no_stable_volatile_carveout"] is True
    assert contract["recursive_non_mac_version_tuple_prohibition_claimed"] is False


def test_v1_incident_roster_and_v2_empty_root_are_distinct() -> None:
    assert sorted(path.name for path in V1_ROOT.iterdir()) == sorted([
        "package-lock.json", "preflight-authority.json", "runtime-preflight.json",
        "row0-independent-go.json", "row0-authority.json",
    ])
    assert not (V1_ROOT / "row0-physionet-root-v1").exists()
    assert list(V2_ROOT.iterdir()) == []
    st = V2_ROOT.stat()
    assert (st.st_dev, st.st_ino, st.st_uid, st.st_gid, st.st_mode & 0o777, st.st_nlink) == (16777234, 66956470, 501, 20, 0o700, 2)


def test_v1_predecessor_files_remain_exact() -> None:
    module = _load(VALIDATOR, "closure_v2_lineage")
    for relative, (size, digest) in module.V1_PREDECESSOR.items():
        raw = (ROOT / relative).read_bytes()
        assert (len(raw), hashlib.sha256(raw).hexdigest()) == (size, digest)


def test_machine_root_swap_is_rejected(tmp_path: Path) -> None:
    module = _load(VALIDATOR, "closure_v2_swap")
    machine = json.loads(MACHINE.read_bytes())
    machine["operational_custody_root"]["absolute_path"] = str(V1_ROOT)
    with pytest.raises(module.ValidationError):
        module._validate_v2_root(machine)


def test_no_v1_operational_root_literal_in_executor() -> None:
    assert "solo_block2_public_documentation_runtime_v1" not in EXECUTOR.read_text()


def test_null_slots_and_v2_effects_are_exact() -> None:
    machine = json.loads(MACHINE.read_bytes())
    assert all(value is None for value in machine["current_operational_slots"].values())
    effects = machine["checklist_effects"]
    assert effects["v2_fetch_performed"] is False
    assert effects["v2_resolver_call_performed"] is False
    assert effects["v2_durable_row_intent_created"] is False


@pytest.mark.parametrize("field,bad", [
    ("attempt_limit", True), ("retry_limit", 0.0), ("redirect_limit", False),
    ("request_bytes", 282.0),
])
def test_operation_exact_integer_types_reject_bool_and_float(field: str, bad: object) -> None:
    module = _load(VALIDATOR, f"closure_v2_type_{field}")
    machine = json.loads(MACHINE.read_bytes())
    machine["operation_roster"][0][field] = bad
    with pytest.raises(module.ValidationError):
        module._validate_operations(machine)


def test_operation_extra_key_is_rejected() -> None:
    module = _load(VALIDATOR, "closure_v2_extra_key")
    machine = json.loads(MACHINE.read_bytes())
    machine["operation_roster"][0]["alternate_url"] = machine["operation_roster"][0]["url"]
    with pytest.raises(module.ValidationError):
        module._validate_operations(machine)


@pytest.mark.parametrize("needle,replacement", [
    ("raw_socket.connect(_numeric_sockaddr(chosen))", "raw_socket.connect(_numeric_sockaddr(chosen))\n        raw_socket.connect(_numeric_sockaddr(chosen))"),
    ("tls = context.wrap_socket(", "context.wrap_socket(raw_socket)\n        tls = context.wrap_socket("),
    ("tls.sendall(op.request_bytes)", "tls.sendall(op.request_bytes)\n            tls.sendall(op.request_bytes)"),
])
def test_duplicate_transport_call_is_rejected(needle: str, replacement: str) -> None:
    module = _load(VALIDATOR, "closure_v2_duplicate_transport")
    source = EXECUTOR.read_text()
    assert source.count(needle) == 1
    mutated = source.replace(needle, replacement, 1)
    with pytest.raises(module.ValidationError):
        module._validate_transport_call_placement(ast.parse(mutated))


def test_moved_pre_reservation_socket_call_is_rejected() -> None:
    module = _load(VALIDATOR, "closure_v2_moved_transport")
    source = EXECUTOR.read_text()
    mutated = source.replace(
        "def _revalidate_runtime_immediately_before_reservation(\n",
        "def _revalidate_runtime_immediately_before_reservation(\n",
        1,
    ).replace(
        "    current = _runtime_manifest(root_path, root_st)\n",
        "    socket.getaddrinfo('example.invalid', 443)\n    current = _runtime_manifest(root_path, root_st)\n",
        1,
    )
    with pytest.raises(module.ValidationError):
        module._validate_transport_call_placement(ast.parse(mutated))
