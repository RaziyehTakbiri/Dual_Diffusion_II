from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT
    / "research"
    / "diagnostics"
    / "manuscript_v3_solo_block2_runtime_custody_closure_v3.py"
)
MACHINE = (
    ROOT
    / "research"
    / "fixtures"
    / "manuscript_v3_solo_block2_runtime_custody_closure_v3.json"
)
EXECUTOR = (
    ROOT
    / "src"
    / "heterodiff"
    / "artifacts"
    / "solo_block2_runtime_custody_executor_v3.py"
)
V2_ROOT = ROOT / "research" / "custody" / "solo_block2_public_documentation_runtime_v2"
V3_ROOT = ROOT / "research" / "custody" / "solo_block2_public_documentation_runtime_v3"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_final_validator_passes_from_unrelated_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load(VALIDATOR, "closure_v3_validator")
    monkeypatch.chdir("/private/tmp")
    result = module.validate(ROOT)
    assert result["status"] == "PASS"
    assert result["v3_network_actions"] == 0
    assert result["v2_attempt_spent_preserved"] is True


def test_machine_is_canonical_and_self_digested() -> None:
    raw = MACHINE.read_bytes()
    value = json.loads(raw)
    assert raw == json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode() + b"\n"
    claimed = value["record_sha256"]
    value["record_sha256"] = None
    assert hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
        + b"\n"
    ).hexdigest() == claimed


def test_v3_has_no_operational_root_or_receipts() -> None:
    machine = json.loads(MACHINE.read_bytes())
    assert machine["operational_custody_root"] is None
    assert all(value is None for value in machine["current_operational_slots"].values())
    assert machine["checklist_effects"]["v3_operational_root_created"] is False
    assert machine["checklist_effects"]["v3_operational_receipt_created"] is False
    assert not V3_ROOT.exists()


def test_v2_spent_incident_is_preserved_exactly() -> None:
    module = _load(VALIDATOR, "closure_v3_incident")
    machine = json.loads(MACHINE.read_bytes())
    module._validate_v2_incident(machine)
    incident = machine["v2_spent_incident"]
    assert incident["retry_permitted"] is False
    assert incident["qualified_observation"] is None
    assert incident["progress"]["sendall_call_count"] == 0
    assert incident["progress"]["tls_wrap_call_count"] == 1


def test_v2_locked_package_bytes_remain_exact() -> None:
    module = _load(VALIDATOR, "closure_v3_lineage")
    for relative, (size, digest) in module.V2_PACKAGE.items():
        raw = (ROOT / relative).read_bytes()
        assert (len(raw), hashlib.sha256(raw).hexdigest()) == (size, digest)


def test_exact_request_bytes_and_limits_remain_unchanged() -> None:
    module = _load(VALIDATOR, "closure_v3_requests")
    machine = json.loads(MACHINE.read_bytes())
    for row, request in zip(machine["operation_roster"], module.REQUESTS):
        assert row["request_bytes"] == len(request)
        assert row["request_sha256"] == hashlib.sha256(request).hexdigest()
        assert row["domain"] in {
            "PhysioNet",
            "UCI Machine Learning Repository",
        }
        assert (row["attempt_limit"], row["retry_limit"], row["redirect_limit"]) == (
            1,
            0,
            0,
        )
        assert row["fetch_eligible"] is False


def test_executor_ast_pins_repairs_before_transport() -> None:
    source = EXECUTOR.read_text()
    tree = ast.parse(source)
    functions = {
        node.name: ast.get_source_segment(source, node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    normalizer = functions["_resolver_system_tuple_to_json_row"]
    strict = functions["_strict_resolver_rows"]
    perform = functions["_perform_spent_attempt"]
    row1 = functions["_validate_row0_success_for_row1"]
    assert all(token in normalizer for token in ("int(family)", "int(socktype)", "int(proto)"))
    assert '"socktype": socktype' in strict
    assert '"socktype": socket.SOCK_STREAM' not in strict
    assert perform.index("_validate_resolver_receipt_rows(") < perform.index("socket.socket(")
    assert "_require_raw_receipt_forward_link(" in row1
    assert "intent_raw" in row1
    module = _load(VALIDATOR, "closure_v3_operation_literals")
    assert module._operation_literal_projection(tree)[1][2] == (
        "UCI Machine Learning Repository"
    )


@pytest.mark.parametrize(
    "needle,replacement",
    [
        (
            "raw_socket.connect(_numeric_sockaddr(chosen))",
            "raw_socket.connect(_numeric_sockaddr(chosen))\n"
            "        raw_socket.connect(_numeric_sockaddr(chosen))",
        ),
        (
            "tls = context.wrap_socket(",
            "context.wrap_socket(raw_socket)\n        tls = context.wrap_socket(",
        ),
        (
            "pid = os.fork()",
            "os.fork()\n    pid = os.fork()",
        ),
    ],
)
def test_duplicate_operational_call_is_rejected(needle: str, replacement: str) -> None:
    module = _load(VALIDATOR, "closure_v3_duplicate_call")
    source = EXECUTOR.read_text()
    assert source.count(needle) == 1
    mutant = source.replace(needle, replacement, 1)
    module_ast = ast.parse(mutant)
    with pytest.raises(module.ValidationError):
        module._validate_operational_call_ownership(module_ast)


def test_relocated_resolver_call_is_rejected() -> None:
    module = _load(VALIDATOR, "closure_v3_relocated_resolver")
    source = EXECUTOR.read_text()
    mutant = source.replace("socket.getaddrinfo(", "relocated_getaddrinfo(", 1)
    mutant = mutant.replace(
        "def _remaining(deadline: float, cap: float) -> float:\n",
        "def _remaining(deadline: float, cap: float) -> float:\n"
        "    socket.getaddrinfo('example.invalid', 443)\n",
        1,
    )
    with pytest.raises(module.ValidationError):
        module._validate_operational_call_ownership(ast.parse(mutant))


def test_attempt_order_mutation_is_rejected_by_full_executor_validator(monkeypatch) -> None:
    module = _load(VALIDATOR, "closure_v3_attempt_order")
    machine = json.loads(MACHINE.read_bytes())
    real_read = module._read_regular
    source = EXECUTOR.read_text()
    mutant = source.replace(
        "        _revalidate_runtime_immediately_before_reservation(\n"
        "            custody_root, root_st, preflight_receipt\n"
        "        )\n",
        "",
        1,
    )

    def read(path, cap=1_048_576):
        if Path(path) == EXECUTOR:
            raw = mutant.encode()
            st = os.stat(EXECUTOR, follow_symlinks=False)
            return raw, st
        return real_read(path, cap)

    machine["executor_source_binding"]["bytes"] = len(mutant.encode())
    machine["executor_source_binding"]["sha256"] = hashlib.sha256(mutant.encode()).hexdigest()
    monkeypatch.setattr(module, "_read_regular", read)
    with pytest.raises(module.ValidationError):
        module._validate_executor(ROOT, machine)


@pytest.mark.parametrize(
    "mutator,validator_name",
    [
        (
            lambda value: value["operation_roster"][0].__setitem__("retry_limit", 1),
            "_validate_operations",
        ),
        (
            lambda value: value["checklist_effects"].__setitem__(
                "v3_fetch_performed", True
            ),
            "_validate_contracts",
        ),
        (
            lambda value: value["supersession_contract"].__setitem__(
                "additional_attempts_if_authorized", 2
            ),
            "_validate_contracts",
        ),
    ],
)
def test_resigned_machine_mutants_are_rejected(mutator, validator_name: str) -> None:
    module = _load(VALIDATOR, f"closure_v3_mutant_{validator_name}")
    machine = json.loads(MACHINE.read_bytes())
    mutator(machine)
    with pytest.raises(module.ValidationError):
        getattr(module, validator_name)(machine)


@pytest.mark.parametrize(
    "contract",
    [
        "checklist_effects",
        "current_operational_slots",
        "repair_contract",
        "executor_contract",
        "qualification_contract",
        "supersession_contract",
    ],
)
def test_nested_contract_extra_key_is_rejected(contract: str) -> None:
    module = _load(VALIDATOR, f"closure_v3_extra_{contract}")
    machine = json.loads(MACHINE.read_bytes())
    machine[contract]["unbound_extra"] = False
    with pytest.raises(module.ValidationError, match="exact nested contract mismatch"):
        module._validate_contracts(machine)


def test_v2_incident_digest_substitution_is_rejected() -> None:
    module = _load(VALIDATOR, "closure_v3_incident_mutant")
    machine = json.loads(MACHINE.read_bytes())
    machine["v2_spent_incident"]["row_receipts"]["outcome.json"]["sha256"] = "0" * 64
    with pytest.raises(module.ValidationError):
        module._validate_v2_incident(machine)


@pytest.mark.parametrize(
    "key,bad",
    [
        ("http_request_bytes_emitted", True),
        ("row1_preempted", False),
        ("official_fact_verified", True),
        ("tracker_or_science_effect", True),
        ("operation_id", "SB2-PUBLIC-ROOT-UCI-001"),
        ("intent_record_sha256", "0" * 64),
    ],
)
def test_v2_incident_summary_contradictions_are_rejected(key: str, bad) -> None:
    module = _load(VALIDATOR, f"closure_v3_incident_summary_{key}")
    machine = json.loads(MACHINE.read_bytes())
    machine["v2_spent_incident"][key] = bad
    with pytest.raises(module.ValidationError, match="exact v2 incident summary"):
        module._validate_v2_incident(machine)


def test_componentwise_reader_rejects_intermediate_symlink(tmp_path: Path) -> None:
    module = _load(VALIDATOR, "closure_v3_componentwise")
    real = tmp_path / "real"
    real.mkdir()
    target = real / "receipt.json"
    target.write_bytes(b"{}\n")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises((OSError, module.ValidationError)):
        module._read_regular(alias / "receipt.json")


def test_package_binding_roster_is_exact() -> None:
    module = _load(VALIDATOR, "closure_v3_bindings")
    machine = json.loads(MACHINE.read_bytes())
    assert {item["path"] for item in machine["package_bindings"]} == module.V3_PACKAGE_PATHS
    module._validate_bindings(ROOT, machine)


def test_validator_and_executor_import_do_not_create_v3_root() -> None:
    before = V3_ROOT.exists()
    _load(VALIDATOR, "closure_v3_import_non_effect")
    _load(EXECUTOR, "closure_v3_executor_import_non_effect")
    assert before is False
    assert V3_ROOT.exists() is False
    assert set(os.listdir(V2_ROOT)) == {
        "package-lock.json",
        "preflight-authority.json",
        "runtime-preflight.json",
        "row0-independent-go.json",
        "row0-authority.json",
        "row0-physionet-root-v1",
    }
