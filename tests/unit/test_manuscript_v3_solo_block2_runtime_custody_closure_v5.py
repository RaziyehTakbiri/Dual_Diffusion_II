from __future__ import annotations
import ast,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
VALIDATOR=ROOT/"research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v5.py"
MACHINE=ROOT/"research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v5.json"
EXECUTOR=ROOT/"src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v5.py"
LIVE_ROOT=ROOT/"research/custody/solo_block2_public_documentation_runtime_v4"
def _load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);assert spec and spec.loader
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
@pytest.fixture(scope="module")
def validator():return _load(VALIDATOR,"_v5_closure_validator")
def test_validator_passes_unrelated_cwd(validator,monkeypatch):
 monkeypatch.chdir("/private/tmp");r=validator.validate(ROOT);assert r["status"]=="PASS" and r["v5_network_actions"]==r["v5_operational_receipts"]==r["v5_activated_budget"]==0
def test_canonical_self_digest():
 raw=MACHINE.read_bytes();m=json.loads(raw);assert raw==json.dumps(m,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()+b"\n"
 claimed=m["record_sha256"];m["record_sha256"]=None;assert hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()+b"\n").hexdigest()==claimed
def test_exact_root_empty_slots_null():
 m=json.loads(MACHINE.read_bytes());assert list(LIVE_ROOT.iterdir())==[] and all(v is None for v in m["activation_operational_slots"].values())
 assert m["activation_checklist_effects"]["v5_root_newly_created"] is False and m["activation_checklist_effects"]["v5_reused_exact_authorized_v4_root"] is True
def test_exact_authority_and_lineage(validator):
 m=json.loads(MACHINE.read_bytes());validator._validate_authority(m);assert m["v2_spent_incident"]["retry_permitted"] is False
 for p,e in validator.V4_PACKAGE.items():
  b=(ROOT/p).read_bytes();assert (len(b),hashlib.sha256(b).hexdigest())==e
def test_source_hash_and_public_surfaces_row0_only(validator):
 raw=EXECUTOR.read_bytes();assert hashlib.sha256(raw).hexdigest()==validator.EXECUTOR_SHA256
 t=ast.parse(raw);f={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
 for n in ("register_independent_go","register_row_authority","attempt"):assert all(a.arg!="row" for a in f[n].args.args)
 validator._validate_executor_tree(t)
def test_direct_rosters_and_marker_ast():
 t=ast.parse(EXECUTOR.read_bytes());assign={n.target.id:ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in {"ROW_AUTHORITY_KEYS","SUCCESSOR_BUDGET_SPEND_KEYS"}}
 for v in assign.values():assert len(v)==len(set(v))
 required={"successor_budget_definition_id","activated_successor_budget_id","supersession_authority_record_sha256","custody_root","exact_url","exact_request_sha256","operation_id","resolver_child_fork_site_limit","resolver_high_level_call_limit","socket_instance_limit","connect_limit","tls_wrap_limit","request_send_limit","retry_limit","redirect_limit","address_fallback_limit","row1_may_consume","successor_budget_scope","v2_receipts_reused","version_or_root_reset_spent_budget"}
 assert required<=set(assign["ROW_AUTHORITY_KEYS"]) and required<=set(assign["SUCCESSOR_BUDGET_SPEND_KEYS"])
def test_import_has_zero_live_effect():
 before=(LIVE_ROOT.stat().st_ino,tuple(LIVE_ROOT.iterdir()));_load(EXECUTOR,"_v5_inert_import");assert before==(LIVE_ROOT.stat().st_ino,tuple(LIVE_ROOT.iterdir()))
def test_executor_accepts_final_machine_non_effect_contract():
 module=_load(EXECUTOR,"_v5_machine_contract");machine=json.loads(MACHINE.read_bytes());module._require_machine_state(machine);module._require_machine_non_effects(machine)
def _resigned_validate_rejects(validator,monkeypatch,source):
 m=json.loads(MACHINE.read_bytes());d=hashlib.sha256(source).hexdigest();orig_read=validator._read;orig_record=validator._record;st=EXECUTOR.stat()
 for x in m["package_bindings"]:
  if x["path"]==validator.EXECUTOR_RELATIVE:x.update(bytes=len(source),sha256=d)
 m["executor_source_binding"]={"path":validator.EXECUTOR_RELATIVE,"bytes":len(source),"sha256":d};m["record_sha256"]=None
 can=lambda v:json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()+b"\n";m["record_sha256"]=hashlib.sha256(can(m)).hexdigest();mr=can(m)
 monkeypatch.setattr(validator,"EXECUTOR_SHA256",d);monkeypatch.setattr(validator,"_read",lambda p:(source,st) if p.absolute()==EXECUTOR.absolute() else orig_read(p));monkeypatch.setattr(validator,"_record",lambda p:(m,mr) if p.absolute()==MACHINE.absolute() else orig_record(p))
 with pytest.raises(validator.ValidationError):validator.validate(ROOT)
@pytest.mark.parametrize("mutation",["duplicate_socket","move_send","row_arg","marker_not_first","delete_api","flags_mutant","late_gap","chronology","authority_leaf"])
def test_fully_resigned_hostile_source_mutants_fail(validator,monkeypatch,mutation):
 t=ast.parse(EXECUTOR.read_bytes());f={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
 if mutation=="duplicate_socket":f["_perform_spent_attempt"].body.append(ast.parse("socket.socket()").body[0])
 elif mutation=="move_send":f["preflight"].body.append(ast.parse("tls.sendall(b'x')").body[0])
 elif mutation=="row_arg":f["attempt"].args.args.append(ast.arg(arg="row"))
 elif mutation=="marker_not_first":f["_exclusive_precomputed_successor_budget_marker"].body.insert(1,ast.parse("time.time_ns()").body[0])
 elif mutation=="delete_api":f["attempt"].body.append(ast.parse("os.unlink('x')").body[0])
 elif mutation=="late_gap":
  class Gap(ast.NodeTransformer):
   def visit_Try(self,node):
    self.generic_visit(node)
    for i,s in enumerate(node.body[:-1]):
     if any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=="_late_pretransport_gate" for c in ast.walk(s)):node.body.insert(i+1,ast.parse("time.time_ns()").body[0]);break
    return node
  Gap().visit(f["attempt"])
 elif mutation=="chronology":f["register_preflight_authority"].body.append(ast.parse("created_unix_ns = 0").body[0])
 elif mutation=="authority_leaf":
  node=next(n for n in t.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=="ROW_AUTHORITY_KEYS");node.value.elts.pop()
 else:
  node=next(n for n in t.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=="FILE_CREATE_FLAGS");node.value=ast.parse("os.O_WRONLY | os.O_CREAT").body[0].value
 ast.fix_missing_locations(t);_resigned_validate_rejects(validator,monkeypatch,(ast.unparse(t)+"\n").encode())
def _resigned_machine_rejects(validator,monkeypatch,mutate):
 m=json.loads(MACHINE.read_bytes());mutate(m);m["record_sha256"]=None
 can=lambda v:json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()+b"\n";m["record_sha256"]=hashlib.sha256(can(m)).hexdigest();raw=can(m);orig=validator._record
 monkeypatch.setattr(validator,"_record",lambda p:(m,raw) if p.absolute()==MACHINE.absolute() else orig(p))
 with pytest.raises(validator.ValidationError):validator.validate(ROOT)
@pytest.mark.parametrize("mutation",["activated","remaining","authority_text","authority_hash","authority_scope","root_inode","root_path","extra_top","removed_top","nonnull_slot","effect_true","v2","v4","package","eligibility","row1","nonclaim"])
def test_fully_resigned_machine_mutants_fail(validator,monkeypatch,mutation):
 def mutate(m):
  if mutation=="activated":m["successor_budget_definition"]["activated"]=1
  elif mutation=="remaining":m["successor_budget_definition"]["remaining_usable"]=1
  elif mutation=="authority_text":m["offline_construction_authority"]["normalized_visible_text"]+="x"
  elif mutation=="authority_hash":m["offline_construction_authority"]["normalized_visible_text_sha256"]="0"*64
  elif mutation=="authority_scope":m["offline_construction_authority"]["scope"]="wrong"
  elif mutation=="root_inode":m["operational_custody_root"]["inode"]+=1
  elif mutation=="root_path":m["operational_custody_root"]["absolute_path"]+="x"
  elif mutation=="extra_top":m["extra"]=False
  elif mutation=="removed_top":m.pop("qualification_contract")
  elif mutation=="nonnull_slot":m["activation_operational_slots"]["package_lock"]={}
  elif mutation=="effect_true":m["activation_checklist_effects"]["v5_fetch_performed"]=True
  elif mutation=="v2":m["v2_spent_incident"]["retry_permitted"]=True
  elif mutation=="v4":m["v4_package_aggregate_sha256"]="0"*64
  elif mutation=="package":m["package_bindings"][0]["sha256"]="0"*64
  elif mutation=="eligibility":m["operation_roster"][0]["fetch_eligible"]=True
  elif mutation=="row1":m["operation_roster"].append(copy.deepcopy(m["operation_roster"][0]))
  else:m["executor_contract"]["registrar_identity_externally_authenticated"]=True
 _resigned_machine_rejects(validator,monkeypatch,mutate)
