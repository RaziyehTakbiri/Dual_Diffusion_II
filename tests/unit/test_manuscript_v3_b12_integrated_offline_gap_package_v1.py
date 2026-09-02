import dataclasses
import importlib.util,json,os
from pathlib import Path
import pytest
from heterodiff.evaluation import b12_integrated_offline_candidate as m

def pred(pid="X",subject=m.ZERO):
 p={"authentication_evidence_sha256":m.ZERO,"authentication_method_id":"EXTERNAL-METHOD","disposition":"ACCEPT","predicate_id":pid,"reviewer_principal_id":"INDEPENDENT-REVIEWER","subject_sha256":subject}
 return m.AuthenticatedPredicateReceipt(pid,subject,"INDEPENDENT-REVIEWER","EXTERNAL-METHOD",m.ZERO,"ACCEPT",m.sha("heterodiff-b12-authenticated-predicate-v1",p))
def event(n,kind,prev,obs=None):
 p={"event_kind":kind,"observation_sha256":obs,"operation_id":"OP","ordinal":n,"previous_event_sha256":prev,"request_sha256":m.ZERO}
 return m.LedgerEvent(n,kind,"OP",m.ZERO,obs,prev,m.sha("heterodiff-b12-ledger-event-v1",p))
def test_zero_delta_and_complete_residual_boundary():
 s=m.semantics();assert all(v==0 or v is False for v in s["effects"].values())
 assert s["training_fields"]["F139"]=="OPEN" and s["training_fields"]["F147"]=="OPEN"
 assert len(m.TEST28_BLOCKERS)==4 and len(m.TEST28_GATES)==17
 assert {"B02_REAL_DATA_ACQUISITION","B03_REAL_DATA_SPLIT_AND_ESCROW","B09_REAL_LICENSE_PRIVACY_APPROVALS","F172_PROSPECTIVE_FREEZE_AFTER_TEST_SEAL"}<set(m.RESIDUALS)
def test_semantics_are_deep_copied():
 a=m.semantics();a["formal_test_states"]["28"]="PASS";assert m.semantics()["formal_test_states"]["28"]=="OPEN"
 old_states=m.FORMAL_TEST_STATES;old_f144=m.F144_CONTRACT
 try:
  m.FORMAL_TEST_STATES={"28":"PASS"};m.F144_CONTRACT={"metric_id":"FOREIGN"}
  assert m.evaluate(None)["formal_test_states"]["28"]=="OPEN"
  assert m.semantics()["f144_candidate_contract"]["metric_id"]=="TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
 finally:m.FORMAL_TEST_STATES=old_states;m.F144_CONTRACT=old_f144
def test_predicate_requires_digest_and_authentication():
 pred().payload()
 with pytest.raises(ValueError):dataclasses.replace(pred(),receipt_sha256=m.ZERO).payload()
 with pytest.raises(ValueError):dataclasses.replace(pred(),disposition="ACCEPTED").payload()
def test_ledger_pairing_chain_and_bool_ordinal():
 i=event(0,"INTENT",m.ZERO);o=event(1,"OUTCOME",i.event_sha256,m.ZERO);m.validate_ledger((i,o))
 with pytest.raises(ValueError):m.validate_ledger((i,))
 with pytest.raises(ValueError):dataclasses.replace(i,ordinal=False).payload()
 with pytest.raises(ValueError):m.validate_ledger((i,dataclasses.replace(o,operation_id="OTHER")))
 with pytest.raises(ValueError):m.validate_ledger([])
 with pytest.raises(ValueError):m.validate_ledger([i,o])
def test_capsule_adapter_and_recomputation_are_typed():
 body={"capsule_id":"C","ordered_file_sha256s":[m.ZERO]};manifest=m.sha("heterodiff-b12-capsule-v1",body)
 m.CapsuleReceipt("C",(m.ZERO,),manifest,pred("CAPSULE_RECEIPT",manifest)).validate()
 subject=m.sha("heterodiff-b12-adapter-subject-v1",{"adapter_id":"A","config_sha256":m.ZERO,"domain_id":"online-retail-ii","implementation_source_sha256":"1"*64,"input_sha256":m.ZERO,"output_sha256":m.ZERO})
 m.AdapterReceipt("A","online-retail-ii",m.ZERO,"1"*64,m.ZERO,m.ZERO,pred("ADAPTER_RECEIPT:A:online-retail-ii",subject)).validate()
 rs=m.sha("heterodiff-b12-recomputation-subject-v1",{"candidate_output_sha256":m.ZERO,"independent_implementation_sha256":m.ZERO,"independent_output_sha256":m.ZERO,"subject_sha256":m.ZERO})
 r=m.RecomputationReceipt(m.ZERO,m.ZERO,m.ZERO,m.ZERO,pred("RECOMPUTATION_RECEIPT",rs));r.validate()
 with pytest.raises(ValueError):dataclasses.replace(r,independent_output_sha256="1"*64).validate()
def test_default_evaluation_never_promotes_formal_tests():
 out=m.evaluate(None);assert out["decision"]=="HOLD" and out["b12_closed"] is False
 assert out["formal_test_states"]=={"28":"OPEN","29":"OPEN","30":"PENDING"}
def test_fixed_string_subclass_rejected():
 class S(str):pass
 with pytest.raises(ValueError):dataclasses.replace(pred(),disposition=S("ACCEPT")).payload()
 class P(m.AuthenticatedPredicateReceipt):pass
 base=pred();bad=P(*[getattr(base,f.name) for f in dataclasses.fields(base)])
 with pytest.raises(ValueError):bad.payload()

def test_exact_b06_adapter_roster_is_22_identity_bound_rows():
 assert len(m.REQUIRED_ADAPTER_ROSTER)==22 and len(set(m.REQUIRED_ADAPTER_ROSTER))==22
 assert sum(x[0].startswith("CSDI") for x in m.REQUIRED_ADAPTER_ROSTER)==1
 assert sum(x[0].startswith("EDITPP") for x in m.REQUIRED_ADAPTER_ROSTER)==1
 assert len(m.RESIDUALS)==50 and len(set(m.RESIDUALS))==50
 assert "TRAINING_CHECKPOINT_PLAN_F139_F144_F147_COMPLETE_AND_INTEGRATED" in m.RESIDUALS

def test_recomputation_execution_subject_mismatch_rejected():
 rs=m.sha("heterodiff-b12-recomputation-subject-v1",{"candidate_output_sha256":m.ZERO,"independent_implementation_sha256":m.ZERO,"independent_output_sha256":m.ZERO,"subject_sha256":m.ZERO})
 r=m.RecomputationReceipt(m.ZERO,m.ZERO,m.ZERO,m.ZERO,pred("RECOMPUTATION_RECEIPT",rs))
 with pytest.raises(ValueError,match="execution subject"):r.validate("1"*64)

def complete_runner():
 body={"capsule_id":"C","ordered_file_sha256s":[m.ZERO]};manifest=m.sha("heterodiff-b12-capsule-v1",body)
 capsule=m.CapsuleReceipt("C",(m.ZERO,),manifest,pred("CAPSULE_RECEIPT",manifest))
 adapters=[]
 for aid,domain,config in m.REQUIRED_ADAPTER_ROSTER:
  subject=m.sha("heterodiff-b12-adapter-subject-v1",{"adapter_id":aid,"config_sha256":config,"domain_id":domain,"implementation_source_sha256":"1"*64,"input_sha256":m.ZERO,"output_sha256":m.ZERO})
  adapters.append(m.AdapterReceipt(aid,domain,config,"1"*64,m.ZERO,m.ZERO,pred("ADAPTER_RECEIPT:"+aid+":"+domain,subject)))
 intent=event(0,"INTENT",m.ZERO);outcome=event(1,"OUTCOME",intent.event_sha256,m.ZERO);ledger=(intent,outcome)
 execution=m.sha("heterodiff-b12-execution-subject-v1",{"adapter_subject_sha256s":[x.subject_sha256() for x in adapters],"capsule_manifest_sha256":manifest,"ledger_event_sha256s":[x.event_sha256 for x in ledger]})
 rs=m.sha("heterodiff-b12-recomputation-subject-v1",{"candidate_output_sha256":m.ZERO,"independent_implementation_sha256":m.ZERO,"independent_output_sha256":m.ZERO,"subject_sha256":execution})
 recomputation=m.RecomputationReceipt(execution,m.ZERO,m.ZERO,m.ZERO,pred("RECOMPUTATION_RECEIPT",rs))
 runner_subject=m.sha("heterodiff-b12-runner-subject-v1",{"adapter_subject_sha256s":[x.subject_sha256() for x in adapters],"capsule_manifest_sha256":manifest,"ledger_final_event_sha256":outcome.event_sha256,"recomputation_subject_sha256":recomputation.receipt_subject_sha256()})
 return m.RunnerReceipt(capsule,tuple(adapters),ledger,recomputation,tuple(pred(x,runner_subject) for x in m.RESIDUALS))

def test_complete_runner_and_adapter_roster_hostility():
 runner=complete_runner();runner.validate()
 with pytest.raises(ValueError,match="adapter roster"):dataclasses.replace(runner,adapters=runner.adapters[:-1]).validate()
 foreign=dataclasses.replace(runner.adapters[0],adapter_id="FOREIGN")
 with pytest.raises(ValueError):dataclasses.replace(runner,adapters=(foreign,)+runner.adapters[1:]).validate()
 duplicate=dataclasses.replace(runner,adapters=(runner.adapters[0],)+runner.adapters[:-1])
 with pytest.raises(ValueError):duplicate.validate()
 omitted=tuple(r for r in runner.predicate_receipts if not r.predicate_id.startswith("CSDI_AUTHOR_EXTENSION_"))
 with pytest.raises(ValueError,match="residual roster"):dataclasses.replace(runner,predicate_receipts=omitted).validate()

def test_public_roster_rebinding_has_no_semantic_or_admission_effect():
 runner=complete_runner();old_r=m.RESIDUALS;old_a=m.REQUIRED_ADAPTER_ROSTER
 try:
  m.RESIDUALS=();m.REQUIRED_ADAPTER_ROSTER=(("FOREIGN","foreign","0"*64),)
  assert len(m.semantics()["residual_predicate_ids"])==50
  assert len(m.evaluate(None)["missing_predicates"])==50
  runner.validate()
  with pytest.raises(ValueError):dataclasses.replace(runner,predicate_receipts=()).validate()
 finally:m.RESIDUALS=old_r;m.REQUIRED_ADAPTER_ROSTER=old_a

def test_zero_or_foreign_implementation_source_rejected():
 a=complete_runner().adapters[0]
 with pytest.raises(ValueError):dataclasses.replace(a,implementation_source_sha256=m.ZERO).validate()

def test_runner_rejects_duck_and_subclass_adapter_members_before_calls():
 runner=complete_runner();real=runner.adapters[0]
 class Duck:
  adapter_id=real.adapter_id;domain_id=real.domain_id;config_sha256=real.config_sha256
  def validate(self):pass
  def subject_sha256(self):return real.subject_sha256()
 with pytest.raises(ValueError,match="concrete type"):dataclasses.replace(runner,adapters=(Duck(),)+runner.adapters[1:]).validate()
 class Sub(m.AdapterReceipt):pass
 sub=Sub(*[getattr(real,f.name) for f in dataclasses.fields(real)])
 with pytest.raises(ValueError,match="concrete type"):dataclasses.replace(runner,adapters=(sub,)+runner.adapters[1:]).validate()

def test_runner_rejects_duck_and_subclass_predicate_members_before_calls():
 runner=complete_runner();real=runner.predicate_receipts[0]
 class Duck:
  def payload(self):return real.payload()
 with pytest.raises(ValueError,match="concrete type"):dataclasses.replace(runner,predicate_receipts=(Duck(),)+runner.predicate_receipts[1:]).validate()
 class Sub(m.AuthenticatedPredicateReceipt):pass
 sub=Sub(*[getattr(real,f.name) for f in dataclasses.fields(real)])
 with pytest.raises(ValueError,match="concrete type"):dataclasses.replace(runner,predicate_receipts=(sub,)+runner.predicate_receipts[1:]).validate()

ROOT=Path(__file__).resolve().parents[2]
VP=ROOT/"research/diagnostics/manuscript_v3_b12_integrated_offline_gap_package_v1.py"
SPEC=importlib.util.spec_from_file_location("b12_validator_test",VP);V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V)
def copy_package(tmp_path):
 paths=[V.FIXTURE]+[Path(p) for p,_,_,_ in V.EXPECTED_BINDINGS]
 for p in paths:
  q=tmp_path/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/p).read_bytes());q.chmod(0o644)
 return tmp_path/V.FIXTURE
def test_hash_first_validator_pass_and_unrelated_cwd(tmp_path,monkeypatch):
 assert V.validate(ROOT)["status"]=="PASS";monkeypatch.chdir(tmp_path);assert V.validate(ROOT)["binding_count"]==12
@pytest.mark.parametrize("mutation",["empty","reorder","extra","schema","state","effects","source"])
def test_validator_rejects_resigned_hostile_machine(tmp_path,mutation):
 f=copy_package(tmp_path);d=json.loads(f.read_text())
 if mutation=="empty":d["bindings"]=[]
 elif mutation=="reorder":d["bindings"][0],d["bindings"][1]=d["bindings"][1],d["bindings"][0]
 elif mutation=="extra":d["bindings"].append(dict(d["bindings"][0]))
 elif mutation=="schema":d["schema_version"]="FOREIGN"
 elif mutation=="state":d["state"]="READY"
 elif mutation=="effects":d["effects"]["field_delta"]=1
 else:d["bindings"][1]["raw_sha256"]="0"*64
 body=dict(d);body.pop("record_sha256");import hashlib
 d["record_sha256"]=hashlib.sha256(b"heterodiff-b12-machine-v2\0"+json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 f.write_text(json.dumps(d,sort_keys=True,separators=(",",":"))+"\n");f.chmod(0o644)
 with pytest.raises(ValueError):V.validate(tmp_path.resolve())
def test_validator_rejects_mode_hardlink_and_symlink(tmp_path):
 copy_package(tmp_path);p=tmp_path/Path(V.EXPECTED_BINDINGS[0][0]);p.chmod(0o600)
 with pytest.raises(ValueError):V.validate(tmp_path.resolve())
 copy_package(tmp_path);p=tmp_path/Path(V.EXPECTED_BINDINGS[0][0]);os.link(p,tmp_path/"alias")
 with pytest.raises(ValueError):V.validate(tmp_path.resolve())
 copy_package(tmp_path);p=tmp_path/Path(V.EXPECTED_BINDINGS[0][0]);p.unlink();p.symlink_to(ROOT/Path(V.EXPECTED_BINDINGS[0][0]))
 with pytest.raises((ValueError,OSError)):V.validate(tmp_path.resolve())
