from __future__ import annotations
import ast, copy, hashlib, importlib.util, json, os, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v4.py"
MACHINE = ROOT / "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v4.json"
EXECUTOR = ROOT / "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v4.py"
V4_ROOT = ROOT / "research/custody/solo_block2_public_documentation_runtime_v4"

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module); return module

@pytest.fixture(scope="module")
def validator(): return _load(VALIDATOR, "_solo_block2_v4_closure_validator")

def test_validator_passes_offline_from_unrelated_cwd(validator, monkeypatch):
    monkeypatch.chdir("/private/tmp"); result = validator.validate(ROOT)
    assert result["status"] == "PASS" and result["v4_network_actions"] == 0 and result["v4_activated_budget"] == 0

def test_machine_is_canonical_and_self_digested():
    raw = MACHINE.read_bytes(); value = json.loads(raw)
    assert raw == json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
    claimed = value["record_sha256"]; value["record_sha256"] = None
    assert hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n").hexdigest() == claimed

def test_exact_empty_root_and_no_receipts():
    machine = json.loads(MACHINE.read_bytes()); assert list(V4_ROOT.iterdir()) == []
    assert machine["operational_custody_root"]["empty_roster_at_construction"] == []
    assert all(value is None for value in machine["construction_operational_slots"].values())

def test_v3_and_v2_lineage_is_exact(validator):
    machine = json.loads(MACHINE.read_bytes()); v3 = json.loads((ROOT / "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v3.json").read_bytes())
    assert machine["v2_spent_incident"] == v3["v2_spent_incident"] and machine["v2_spent_incident"]["retry_permitted"] is False
    for relative, expected in validator.V3_PACKAGE.items():
        raw = (ROOT / relative).read_bytes(); assert (len(raw), hashlib.sha256(raw).hexdigest()) == expected

def test_budget_is_definition_only_and_permanently_dormant():
    budget = json.loads(MACHINE.read_bytes())["successor_budget_definition"]
    assert budget["authorized_definition"] == 1 and budget["activated"] == budget["remaining_usable"] == 0
    assert budget["activated_unique_one_use_budget_id"] is None and budget["activation_authority_present"] is False
    assert budget["fixture_resigning_can_activate"] is False

def test_operations_are_exact_and_ineligible():
    rows = json.loads(MACHINE.read_bytes())["operation_roster"]
    assert [r["operation_id"] for r in rows] == ["SB2-PUBLIC-ROOT-PHYSIONET-000", "SB2-PUBLIC-ROOT-UCI-001"]
    assert [r["request_sha256"] for r in rows] == ["ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449", "94271e586cfbec1d25c03754b1c4f47aadbd8e9459cffad6c050e0a80cf16b1b"]
    assert all(r["fetch_eligible"] is False for r in rows)

def test_executor_has_dormant_first_surfaces():
    tree = ast.parse(EXECUTOR.read_bytes()); funcs = {n.name:n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in ("preflight", "register_package_lock", "register_preflight_authority", "main"):
        body=funcs[name].body; first=body[1] if isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) else body[0]
        assert first.value.func.id == "_require_activation_authority_present"
    for name in ("register_independent_go", "register_row_authority", "attempt"):
        assert funcs[name].body[1].value.func.id == "_require_dormant_production_row0"

@pytest.mark.parametrize("gate,mutation", [
    ("_require_activation_authority_present", "return"),
    ("_require_activation_authority_present", "noop"),
    ("_require_activation_authority_present", "conditional"),
    ("_require_dormant_production_row0", "return"),
])
def test_hostile_gate_body_mutations_fail(validator, gate, mutation):
    tree = ast.parse(EXECUTOR.read_bytes()); function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == gate)
    if mutation == "return": function.body = [ast.Return(value=None)]
    elif mutation == "noop": function.body = [ast.Pass()]
    else: function.body = [ast.If(test=ast.Name(id="ACTIVATION_AUTHORITY_PRESENT", ctx=ast.Load()), body=[ast.Raise(exc=ast.Call(func=ast.Name(id="GateError",ctx=ast.Load()),args=[ast.Constant("x")],keywords=[]),cause=None)], orelse=[ast.Return(value=None)])]
    with pytest.raises(validator.ValidationError, match="gate AST mismatch"):
        validator._validate_executor_tree(tree)

@pytest.mark.parametrize("call", ["socket.getaddrinfo", "socket.socket", "raw_socket.connect", "ssl.SSLContext", "context.wrap_socket", "tls.sendall", "os.fork", "subprocess.run"])
def test_hostile_duplicated_operational_call_fails(validator, call):
    tree = ast.parse(EXECUTOR.read_bytes()); funcs = {n.name:n for n in tree.body if isinstance(n, ast.FunctionDef)}
    owner = {"socket.getaddrinfo":"_bounded_single_getaddrinfo","os.fork":"_bounded_single_getaddrinfo","subprocess.run":"_capture_scutil_dns"}.get(call,"_perform_spent_attempt")
    parts=call.split("."); target=ast.Name(id=parts[0],ctx=ast.Load())
    for part in parts[1:]: target=ast.Attribute(value=target,attr=part,ctx=ast.Load())
    funcs[owner].body.append(ast.Expr(value=ast.Call(func=target,args=[],keywords=[])))
    with pytest.raises(validator.ValidationError, match="operational call ownership"):
        validator._validate_executor_tree(tree)

def test_hostile_relocated_operational_call_fails(validator):
    tree=ast.parse(EXECUTOR.read_bytes()); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    target=None
    for node in ast.walk(funcs["_perform_spent_attempt"]):
        if isinstance(node,ast.Call) and validator._dotted(node.func)=="socket.socket": target=copy.deepcopy(node); break
    assert target is not None
    class Drop(ast.NodeTransformer):
        def visit_Call(self,node):
            if validator._dotted(node.func)=="socket.socket": return ast.Constant(None)
            return self.generic_visit(node)
    Drop().visit(funcs["_perform_spent_attempt"]); funcs["preflight"].body.append(ast.Expr(value=target))
    with pytest.raises(validator.ValidationError, match="operational call ownership"):
        validator._validate_executor_tree(tree)

def _full_validate_resigned_source(validator, monkeypatch, source: bytes):
    machine=json.loads(MACHINE.read_bytes()); digest=hashlib.sha256(source).hexdigest(); original_read=validator._read; original_record=validator._record
    executor_stat=EXECUTOR.stat()
    for item in machine["package_bindings"]:
        if item["path"]==validator.EXECUTOR_RELATIVE: item.update(bytes=len(source),sha256=digest)
    machine["executor_source_binding"]={"path":validator.EXECUTOR_RELATIVE,"bytes":len(source),"sha256":digest}
    machine["record_sha256"]=None
    canonical=lambda v:json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()+b"\n"
    machine["record_sha256"]=hashlib.sha256(canonical(machine)).hexdigest(); machine_raw=canonical(machine)
    def fake_read(path):
        if path.absolute()==EXECUTOR.absolute(): return source,executor_stat
        return original_read(path)
    def fake_record(path):
        if path.absolute()==MACHINE.absolute(): return machine,machine_raw
        return original_record(path)
    monkeypatch.setattr(validator,"_read",fake_read); monkeypatch.setattr(validator,"_record",fake_record); monkeypatch.setattr(validator,"EXECUTOR_SHA256",digest)
    with pytest.raises(validator.ValidationError): validator.validate(ROOT)

@pytest.mark.parametrize("mutation", ["gate_return","gate_noop","activation_true","fetch_true","budget_one","duplicate_module","duplicate_nested","relocate_wrong_function"])
def test_full_validation_rejects_resigned_semantic_source_mutants(validator, monkeypatch, mutation):
    tree=ast.parse(EXECUTOR.read_bytes()); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    if mutation in ("gate_return","gate_noop"):
        funcs["_require_activation_authority_present"].body=[ast.Return(value=None) if mutation=="gate_return" else ast.Pass()]
    elif mutation in ("activation_true","fetch_true","budget_one"):
        name={"activation_true":"ACTIVATION_AUTHORITY_PRESENT","fetch_true":"FETCH_ELIGIBLE","budget_one":"AUTHORIZED_SUCCESSOR_ATTEMPT_BUDGET"}[mutation]
        node=next(n for n in tree.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id==name); node.value=ast.Constant(True if mutation!="budget_one" else 1)
    else:
        call=ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id="socket",ctx=ast.Load()),attr="socket",ctx=ast.Load()),args=[],keywords=[]))
        if mutation=="duplicate_module": tree.body.append(call)
        elif mutation=="duplicate_nested": funcs["preflight"].body.append(ast.FunctionDef(name="nested",args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[call],decorator_list=[]))
        else: funcs["preflight"].body.append(call)
    ast.fix_missing_locations(tree); _full_validate_resigned_source(validator,monkeypatch,(ast.unparse(tree)+"\n").encode())

def test_import_and_dormant_calls_do_not_touch_root_or_network(monkeypatch):
    before = os.stat(V4_ROOT, follow_symlinks=False), tuple(V4_ROOT.iterdir()); module = _load(EXECUTOR, "_solo_block2_v4_dormant_executor")
    monkeypatch.setattr(module.socket, "socket", lambda *a, **k: pytest.fail("socket reached")); monkeypatch.setattr(module.socket, "getaddrinfo", lambda *a, **k: pytest.fail("resolver reached"))
    for call in (lambda: module.preflight(str(V4_ROOT)), lambda: module.register_independent_go(str(V4_ROOT),0,"x",1), lambda: module.attempt(str(V4_ROOT),0)):
        with pytest.raises(module.GateError, match="separately frozen successor"): call()
    after = os.stat(V4_ROOT, follow_symlinks=False), tuple(V4_ROOT.iterdir()); assert (before[0].st_ino,before[1]) == (after[0].st_ino,after[1])

@pytest.mark.parametrize("mutation", ["root_inode","budget_activation","authority_text","authority_hash","row_eligibility","extra_top"])
def test_hostile_resigned_mutations_fail(validator, mutation):
    machine=json.loads(MACHINE.read_bytes()); bad=copy.deepcopy(machine)
    if mutation=="root_inode": bad["operational_custody_root"]["inode"]+=1
    elif mutation=="budget_activation": bad["successor_budget_definition"]["activated"]=1
    elif mutation=="authority_text": bad["offline_construction_authority"]["normalized_visible_text"]+="x"
    elif mutation=="authority_hash": bad["offline_construction_authority"]["normalized_visible_text_sha256"]="0"*64
    elif mutation=="row_eligibility": bad["operation_roster"][0]["fetch_eligible"]=True
    else: bad["unexpected"]=False
    if mutation.startswith("authority"):
        with pytest.raises(validator.ValidationError): validator._validate_authority(bad)
    elif mutation=="root_inode":
        with pytest.raises(validator.ValidationError): validator._validate_root(bad)
    elif mutation=="budget_activation": assert bad["successor_budget_definition"] != validator.EXPECTED_BUDGET
    elif mutation=="row_eligibility": assert bad["operation_roster"] != machine["operation_roster"]
    else: assert set(bad) != validator.EXPECTED_TOP_KEYS

def test_extra_live_root_entry_is_rejected_without_creating_one(validator, monkeypatch):
    real=os.listdir; monkeypatch.setattr(os,"listdir",lambda p:["unexpected"] if isinstance(p,int) else real(p))
    with pytest.raises(validator.ValidationError,match="exact empty"): validator._validate_root(json.loads(MACHINE.read_bytes()))
