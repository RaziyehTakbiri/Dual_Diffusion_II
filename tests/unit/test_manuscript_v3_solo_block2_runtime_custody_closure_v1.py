from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    ROOT
    / "research"
    / "diagnostics"
    / "manuscript_v3_solo_block2_runtime_custody_closure_v1.py"
)
MACHINE_PATH = (
    ROOT
    / "research"
    / "fixtures"
    / "manuscript_v3_solo_block2_runtime_custody_closure_v1.json"
)
EXECUTOR_PATH = (
    ROOT
    / "src"
    / "heterodiff"
    / "artifacts"
    / "solo_block2_runtime_custody_executor_v1.py"
)


def _load_validator():
    name = "solo_block2_runtime_custody_closure_validator_test_import"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator():
    return _load_validator()


def _canonical(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _resign(value):
    clone = dict(value)
    clone["record_sha256"] = None
    value["record_sha256"] = hashlib.sha256(_canonical(clone)).hexdigest()
    return _canonical(value)


def test_live_package_passes_and_has_zero_effect(validator):
    result = validator.validate(ROOT)
    assert result["status"] == "PASS"
    assert result["state"] == validator.STATE
    assert result["operation_count"] == 2
    assert result["fetches_performed"] == 0
    assert result["durable_intents_created"] == 0
    assert result["operational_root_entries"] == 0
    assert result["scientific_delta"] == "ZERO"


def test_validator_cli_passes_from_unrelated_working_directory(tmp_path):
    completed = subprocess.run(
        [sys.executable, "-B", str(VALIDATOR_PATH), str(ROOT)],
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    payload = json.loads(completed.stdout)
    assert payload["status"] == "PASS"


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value.update(state="FETCH_ELIGIBLE"),
        lambda value: value.update(extra=False),
        lambda value: value["authority_provenance"].update(dns_or_https_authorized=True),
        lambda value: value["current_operational_slots"].update(row0_intent="forged"),
        lambda value: value["checklist_effects"].update(fetch_performed=True),
        lambda value: value["operation_roster"].append(dict(value["operation_roster"][0])),
    ],
)
def test_semantically_resigned_machine_mutants_fail(validator, tmp_path, mutator):
    value = json.loads(MACHINE_PATH.read_text(encoding="utf-8"))
    mutator(value)
    path = tmp_path / "machine.json"
    path.write_bytes(_resign(value))
    if "extra" in value or value["state"] != validator.STATE:
        with pytest.raises(validator.ValidationError):
            validator._read_machine(path)
    else:
        mutated, _ = validator._read_machine(path)
        if mutated["authority_provenance"] != json.loads(
            MACHINE_PATH.read_text(encoding="utf-8")
        )["authority_provenance"]:
            with pytest.raises(validator.ValidationError):
                validator._validate_authority(mutated)
        elif any(v is not None for v in mutated["current_operational_slots"].values()) or mutated[
            "checklist_effects"
        ] != json.loads(MACHINE_PATH.read_text(encoding="utf-8"))["checklist_effects"]:
            with pytest.raises(validator.ValidationError):
                validator._validate_null_effects(mutated)
        else:
            with pytest.raises(validator.ValidationError):
                validator._validate_operations(mutated)


def test_duplicate_key_and_noncanonical_machine_fail(validator, tmp_path):
    duplicate = b'{"record_sha256":"' + b"0" * 64 + b'","schema_version":"x","schema_version":"x"}\n'
    path = tmp_path / "duplicate.json"
    path.write_bytes(duplicate)
    with pytest.raises(validator.ValidationError):
        validator._read_machine(path)
    path.write_bytes(MACHINE_PATH.read_bytes() + b" ")
    with pytest.raises(validator.ValidationError):
        validator._read_machine(path)


def test_deep_machine_json_fails_as_validation_error(validator, tmp_path):
    path = tmp_path / "deep.json"
    path.write_bytes(b"[" * 1500 + b"0" + b"]" * 1500)
    with pytest.raises(validator.ValidationError, match="machine JSON invalid"):
        validator._read_machine(path)


def test_predecessor_and_additive_bindings_are_exact(validator):
    machine, _ = validator._read_machine(MACHINE_PATH)
    validator._validate_bindings(
        ROOT,
        machine["immutable_predecessor_bindings"],
        validator.EXPECTED_PREDECESSOR_PATHS,
        include_mtime=False,
    )
    validator._validate_bindings(
        ROOT,
        machine["package_bindings"],
        validator.EXPECTED_PACKAGE_PATHS,
        include_mtime=True,
    )


def test_binding_rejects_hardlink_and_hash_mutation(validator, tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    path = root / "x"
    path.write_bytes(b"one")
    receipt = validator._regular_receipt(root, "x")
    projection = dict(receipt)
    projection.pop("mtime_ns")
    validator._validate_bindings(root, [projection], {"x"}, include_mtime=False)
    path.write_bytes(b"two")
    with pytest.raises(validator.ValidationError):
        validator._validate_bindings(root, [projection], {"x"}, include_mtime=False)
    os.link(path, root / "y")
    with pytest.raises(validator.ValidationError):
        validator._regular_receipt(root, "x")


def test_binding_rejects_intermediate_symlink(validator, tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "x").write_bytes(b"one")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(OSError):
        validator._regular_receipt(tmp_path, "alias/x")


def test_root_validator_accepts_only_forward_prefix_states(
    validator, tmp_path, monkeypatch
):
    root = tmp_path / "custody"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    st = os.stat(root, follow_symlinks=False)
    identity = {
        "absolute_path": str(root),
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode_octal": "0700",
        "nlink_at_package_construction": st.st_nlink,
        "empty_at_package_construction": True,
        "row_directories_present": False,
    }
    monkeypatch.setattr(validator, "EXPECTED_ROOT", str(root))
    monkeypatch.setattr(validator, "EXPECTED_ROOT_IDENTITY", identity)
    machine = {"operational_custody_root": identity}
    assert validator._validate_root(machine) == 0
    for count, name in enumerate(validator.FORWARD_ROOT_PREFIX, start=1):
        path = root / name
        if name.startswith("row") and name.endswith("-v1"):
            path.mkdir(mode=0o700)
            path.chmod(0o700)
        else:
            path.write_bytes(b"x")
            path.chmod(0o600)
        assert validator._validate_root(machine) == count
    extra = root / "unexpected"
    extra.write_bytes(b"x")
    extra.chmod(0o600)
    with pytest.raises(validator.ValidationError):
        validator._validate_root(machine)


def _executor_machine_for(path: Path):
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8"))

    def literal(name):
        for node in tree.body:
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == name
            ):
                return ast.literal_eval(node.value)
        raise AssertionError(name)

    roster_names = (
        "PACKAGE_LOCK_KEYS",
        "PREFLIGHT_AUTHORITY_KEYS",
        "RUNTIME_PREFLIGHT_KEYS",
        "INDEPENDENT_GO_KEYS",
        "ROW_AUTHORITY_KEYS",
        "INTENT_KEYS",
        "OUTCOME_KEYS",
    )
    interpreter = literal("EXPECTED_INTERPRETER")
    return {
        "executor_source_binding": {
            "path": "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v1.py",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
        "runtime_contract": {
            "operational_receipt_key_rosters": {
                name: list(literal(name)) for name in roster_names
            },
            "sidecar_basenames": list(literal("SIDECAR_BASENAMES")),
            "dyld_arm64e_cache_paths": list(literal("DYLD_CACHE_PATHS")),
            "exact_launcher_prefix": [
                "/usr/bin/env",
                "-i",
                interpreter,
                "-I",
                "-S",
                "-B",
                str(path),
            ],
            "python_flags_exact": literal("EXPECTED_PYTHON_FLAGS"),
        },
    }


def test_executor_ast_positive_control_passes(validator, tmp_path):
    relative = Path("src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v1.py")
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(EXECUTOR_PATH.read_bytes())
    validator._validate_executor_ast(tmp_path, _executor_machine_for(target))


@pytest.mark.parametrize(
    "old,new",
    [
        ("socket.getaddrinfo(\n", "socket.getaddrinfo(\n" * 2),
        ("socket.socket(family", "socket.socket(family\n    socket.socket(family"),
        ("_perform_spent_attempt(\n", "_perform_spent_attempt(\n"),
        ("row directory already exists; attempt cannot start or retry", "row can retry"),
    ],
)
def test_executor_ast_hostile_mutants_fail(validator, tmp_path, old, new):
    relative = Path("src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v1.py")
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    source = EXECUTOR_PATH.read_text(encoding="utf-8")
    if old == new:
        source = source.replace(
            '_exclusive_canonical_at(rowfd, "intent.json", intent)',
            '_perform_spent_attempt(\n                op, sidecars, deadline, AttemptProgress(), None\n            )\n        _exclusive_canonical_at(rowfd, "intent.json", intent)',
            1,
        )
    else:
        assert old in source
        source = source.replace(old, new, 1)
    target.write_text(source, encoding="utf-8")
    with pytest.raises((validator.ValidationError, SyntaxError, IndentationError)):
        validator._validate_executor_ast(tmp_path, _executor_machine_for(target))


def test_validator_ast_is_read_only_and_network_free():
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not imports & {"socket", "ssl", "urllib", "requests", "http.client"}
    dotted = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            dotted.add(f"{node.func.value.id}.{node.func.attr}")
    assert not dotted & {
        "os.remove",
        "os.unlink",
        "os.rename",
        "os.replace",
        "subprocess.run",
    }


def test_executor_uses_raw_byte_loader_and_no_proposal_staging():
    source = EXECUTOR_PATH.read_text(encoding="utf-8")
    assert "compile(raw" in source
    assert "exec(code" in source
    assert "spec_from_file_location" not in source
    assert "exec_module" not in source
    assert ".proposal.json" not in source


def test_executor_test_never_invokes_resolver_or_live_attempt():
    test_path = ROOT / "tests" / "unit" / "test_solo_block2_runtime_custody_executor_v1.py"
    source = test_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                calls.append(f"{node.func.value.id}.{node.func.attr}")
    assert "socket.getaddrinfo" not in calls
    assert "socket.socket" not in calls
    assert "ssl.SSLContext" not in calls
    assert "runtime._bounded_single_getaddrinfo" not in calls
    # The only attempt calls are deliberately imported-module pre-gate mutants;
    # the exact direct-script launcher equality rejects them before any root I/O.
    assert "runtime.attempt" in calls


def test_operational_root_and_all_operational_slots_remain_empty(validator):
    machine, _ = validator._read_machine(MACHINE_PATH)
    validator._validate_root(machine)
    assert all(value is None for value in machine["current_operational_slots"].values())
    assert list(Path(validator.EXPECTED_ROOT).iterdir()) == []
