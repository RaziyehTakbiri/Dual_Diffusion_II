"""Fail-closed offline B12 evidence contracts; no execution or I/O."""
from __future__ import annotations
import copy, hashlib, json
from dataclasses import dataclass
from typing import Any, Sequence

SCHEMA="heterodiff-b12-integrated-offline-gap-v2"; ZERO="0"*64
_FORMAL_TEST_STATE_ITEMS=(("28","OPEN"),("29","OPEN"),("30","PENDING"))
FORMAL_TEST_STATES=dict(_FORMAL_TEST_STATE_ITEMS)
F144_CONTRACT={"metric_id":"TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
 "projection_id":"F105_CKS_BINARY64_PROJECTION_V1",
 "aggregation":"ARITHMETIC_MEAN_OVER_COMPLETE_F134_VALIDATION_GROUP_ROSTER",
 "cadence":"EVERY_256_COMPLETED_OPTIMIZER_UPDATES_AND_F143_BOUND",
 "direction":"LOWER_IS_BETTER","complete_roster_certificate_required":True,
 "checkpoint_tie_rule":"F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1",
 "test_data_permitted":False}
_F144_ITEMS=tuple(F144_CONTRACT.items())
TEST28_BLOCKERS=("PRODUCTION_SCHEMA_EXTERNAL_ACCEPTANCE","RUNNER_AND_RECOMPUTATION",
 "UNCONDITIONAL_OPERATIONAL_PREDICTIONS","PRODUCTION_RUNTIME_AND_DURABILITY")
TEST28_GATES=tuple(f"TEST28_PRODUCTION_GATE_{i:02d}" for i in range(1,18))
RESIDUALS=("B02_REAL_DATA_ACQUISITION","B03_REAL_DATA_SPLIT_AND_ESCROW",
 "B08_RUNTIME_COMPUTE_ENVELOPE","B09_REAL_LICENSE_PRIVACY_APPROVALS",
 "F172_PROSPECTIVE_FREEZE_AFTER_TEST_SEAL","ALL_PREEXECUTION_ARTIFACTS_ACCEPTED",
 "PRIMARY_64_DIMENSION_CONTEXT_ENCODER","PRIMARY_DOMAIN_SCALE_RUNTIME",
 "PRIMARY_ADAPTER_RETAIL","PRIMARY_ADAPTER_PHYSIONET","CONTROL_ADAPTER_RETAIL",
 "CONTROL_ADAPTER_PHYSIONET","LITERATURE_FAMILY_ADAPTER_RETAIL",
 "LITERATURE_FAMILY_ADAPTER_PHYSIONET",
 *(f"CSDI_AUTHOR_EXTENSION_{i}" for i in range(1,5)),
 *(f"EDITPP_AUTHOR_EXTENSION_{i}" for i in range(1,5)),*TEST28_BLOCKERS,*TEST28_GATES,
 "TEST29_PRODUCTION_ROUTE_RECEIPT","TEST29_WHOLE_METHOD_RESIDUAL",
 "TEST30_PRODUCTION_COUPLED_PATH_RECEIPT","TEST30_WHOLE_METHOD_RESIDUAL",
 "REAL_IMMUTABLE_EXECUTION_LEDGER","INDEPENDENT_REAL_RECOMPUTATION_RECEIPT",
 "TRAINING_CHECKPOINT_PLAN_F139_F144_F147_COMPLETE_AND_INTEGRATED")
_RESIDUAL_SNAPSHOT=tuple(RESIDUALS)
_DOMAINS=("online-retail-ii","physionet-challenge-2012")
_B06_IDS=(
 ("association-aware-guide-plus-residual","c44af50b915d024cb6019ee82a2998410afd3401fdb84c5313a84bc98fa543b1"),("unified-direct-conditioner","f5c87a6c66defe9e1e8bb12e9578bc9317892af06dce0b88a5b1b81933b742a5"),
 ("analytic-guide-only-residual-removed","37d5178c836ced493dec1fe49b08ab042e738c5c24edc5867830528154b51ae4"),("direct-or-residual-only-analytic-guide-removed","e175d468fb0df523c9adb2f6aa2e6f4b843b872e54234f63a1f41465f8bef212"),
 ("association-destroyed-or-factorized-eventwise","a2f91e01e1bdc6854fef6a045df802eaf4a5e60ef124c4303b0694d40ed36008"),("unconditional-base-sanity-reference","7ecfb6dd842a781d70ac147e374a501f819c8f61cd20f38442526079fb607032"))
_LIT_IDS=(("ngdb-style-auxiliary-guide-plus-correction",("e5f37459809ad912af07daf42c7652968ab6ea7f54e936109752243a4357065a","1de711005c3c22de646dc870b4c6ac54c5a139fffd797a403072300bccfdfb52")),
 ("deft-style-generalized-h-frozen-base-correction",("fc2c415774ed73dd9ecadf69fa1d3add984779c4f6075aea75b8c529df581ef0","2d41a2d142260f00a10847844fcd49ed50759aaad990fb715d8de979e8c03b21")),
 ("task-compatible-same-base-smc-or-feynman-kac",("330de95230e6452d1fba9865e4ac4b991967f0e722b63ebb387fe59e2d5f2a60","8041429a94237b549961a01fe8e4e965bfff648951e0f4b6904a0e7ac9449366")),
 ("closest-variable-cardinality-point-or-edit-generator",("b04ae2fdc700e2b3677854b39f246f0188cf58f03adc11305e1258c04f14786b","192f069c927c3c6dc6356286f12e0a0c68d20b120651a1a72793a6eba59a5cca")))
REQUIRED_ADAPTER_ROSTER=tuple((x,d,h) for x,h in _B06_IDS for d in _DOMAINS)+tuple((x,d,hs[i]) for x,hs in _LIT_IDS for i,d in enumerate(_DOMAINS))+(
 ("CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1","physionet-challenge-2012","72fa143ace5a24e5338b89de37e2df1980174f10c1254f708dc238611c327046"),
 ("EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1","online-retail-ii","64cdfe9a4f985ba069874a4da3178595856b6dc97bfb29ffa575b48bd805d7ee"))
_ADAPTER_ROSTER_SNAPSHOT=tuple(REQUIRED_ADAPTER_ROSTER)

def canonical(v:Any)->bytes:
 return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def sha(domain:str,v:Any)->str:
 if type(domain) is not str or "\0" in domain: raise TypeError("domain")
 return hashlib.sha256(domain.encode()+b"\0"+canonical(v)).hexdigest()
def _hex(v:object)->bool:
 return type(v) is str and len(v)==64 and all(c in "0123456789abcdef" for c in v)

@dataclass(frozen=True)
class AuthenticatedPredicateReceipt:
 predicate_id:str; subject_sha256:str; reviewer_principal_id:str
 authentication_method_id:str; authentication_evidence_sha256:str
 disposition:str; receipt_sha256:str
 def payload(self)->dict[str,str]:
  if type(self) is not AuthenticatedPredicateReceipt:raise ValueError("predicate concrete type")
  p={"authentication_evidence_sha256":self.authentication_evidence_sha256,
   "authentication_method_id":self.authentication_method_id,"disposition":self.disposition,
   "predicate_id":self.predicate_id,"reviewer_principal_id":self.reviewer_principal_id,
   "subject_sha256":self.subject_sha256}
  if any(type(v) is not str for v in p.values()) or not _hex(self.subject_sha256) or not _hex(self.authentication_evidence_sha256): raise ValueError("predicate fields")
  if self.disposition!="ACCEPT" or not self.reviewer_principal_id or not self.authentication_method_id: raise ValueError("predicate authentication")
  if self.receipt_sha256!=sha("heterodiff-b12-authenticated-predicate-v1",p): raise ValueError("predicate digest")
  return p

@dataclass(frozen=True)
class AdapterReceipt:
 adapter_id:str; domain_id:str; config_sha256:str; implementation_source_sha256:str
 input_sha256:str; output_sha256:str; predicate:AuthenticatedPredicateReceipt
 def validate(self)->None:
  if type(self) is not AdapterReceipt or type(self.predicate) is not AuthenticatedPredicateReceipt:raise ValueError("adapter concrete type")
  if type(self.adapter_id) is not str or type(self.domain_id) is not str or self.domain_id not in ("online-retail-ii","physionet-challenge-2012"): raise ValueError("adapter identity")
  if not all(_hex(v) for v in (self.config_sha256,self.implementation_source_sha256,self.input_sha256,self.output_sha256)) or self.implementation_source_sha256==ZERO: raise ValueError("adapter digest")
  subject=sha("heterodiff-b12-adapter-subject-v1",{"adapter_id":self.adapter_id,"config_sha256":self.config_sha256,"domain_id":self.domain_id,"implementation_source_sha256":self.implementation_source_sha256,"input_sha256":self.input_sha256,"output_sha256":self.output_sha256})
  p=self.predicate.payload()
  if p["predicate_id"]!="ADAPTER_RECEIPT:"+self.adapter_id+":"+self.domain_id or p["subject_sha256"]!=subject:raise ValueError("adapter predicate binding")
 def subject_sha256(self)->str:
  self.validate();return sha("heterodiff-b12-adapter-subject-v1",{"adapter_id":self.adapter_id,"config_sha256":self.config_sha256,"domain_id":self.domain_id,"implementation_source_sha256":self.implementation_source_sha256,"input_sha256":self.input_sha256,"output_sha256":self.output_sha256})

@dataclass(frozen=True)
class CapsuleReceipt:
 capsule_id:str; ordered_file_sha256s:tuple[str,...]; manifest_sha256:str
 predicate:AuthenticatedPredicateReceipt
 def validate(self)->None:
  if type(self) is not CapsuleReceipt or type(self.predicate) is not AuthenticatedPredicateReceipt:raise ValueError("capsule concrete type")
  if type(self.capsule_id) is not str or type(self.ordered_file_sha256s) is not tuple or not self.ordered_file_sha256s or not all(_hex(v) for v in self.ordered_file_sha256s): raise ValueError("capsule")
  if len(set(self.ordered_file_sha256s))!=len(self.ordered_file_sha256s):raise ValueError("duplicate capsule files")
  p={"capsule_id":self.capsule_id,"ordered_file_sha256s":list(self.ordered_file_sha256s)}
  if self.manifest_sha256!=sha("heterodiff-b12-capsule-v1",p): raise ValueError("capsule digest")
  pr=self.predicate.payload()
  if pr["predicate_id"]!="CAPSULE_RECEIPT" or pr["subject_sha256"]!=self.manifest_sha256:raise ValueError("capsule predicate binding")

@dataclass(frozen=True)
class LedgerEvent:
 ordinal:int; event_kind:str; operation_id:str; request_sha256:str
 observation_sha256:str|None; previous_event_sha256:str; event_sha256:str
 def payload(self)->dict[str,Any]:
  if type(self) is not LedgerEvent:raise ValueError("ledger concrete type")
  if type(self.ordinal) is not int or self.ordinal<0 or type(self.event_kind) is not str or self.event_kind not in ("INTENT","OUTCOME"): raise ValueError("ledger identity")
  if type(self.operation_id) is not str or not _hex(self.request_sha256) or not _hex(self.previous_event_sha256): raise ValueError("ledger fields")
  if (self.event_kind=="INTENT")!=(self.observation_sha256 is None): raise ValueError("ledger pair type")
  if self.observation_sha256 is not None and not _hex(self.observation_sha256): raise ValueError("observation")
  p={"event_kind":self.event_kind,"observation_sha256":self.observation_sha256,
   "operation_id":self.operation_id,"ordinal":self.ordinal,
   "previous_event_sha256":self.previous_event_sha256,"request_sha256":self.request_sha256}
  if self.event_sha256!=sha("heterodiff-b12-ledger-event-v1",p): raise ValueError("event digest")
  return p

def validate_ledger(events:Sequence[LedgerEvent])->None:
 if type(events) is not tuple or not events or len(events)%2: raise ValueError("immutable nonempty paired ledger")
 previous=ZERO
 for i,event in enumerate(events):
  if type(event) is not LedgerEvent:raise ValueError("ledger member type")
  event.payload()
  if event.ordinal!=i or event.previous_event_sha256!=previous: raise ValueError("chain")
  if event.event_kind!=("INTENT" if i%2==0 else "OUTCOME"): raise ValueError("pair order")
  if i%2 and (event.operation_id!=events[i-1].operation_id or event.request_sha256!=events[i-1].request_sha256): raise ValueError("pair binding")
  previous=event.event_sha256

@dataclass(frozen=True)
class RecomputationReceipt:
 subject_sha256:str; independent_implementation_sha256:str
 candidate_output_sha256:str; independent_output_sha256:str
 predicate:AuthenticatedPredicateReceipt
 def validate(self,expected_subject:str|None=None)->None:
  if type(self) is not RecomputationReceipt or type(self.predicate) is not AuthenticatedPredicateReceipt:raise ValueError("recomputation concrete type")
  if not all(_hex(v) for v in (self.subject_sha256,self.independent_implementation_sha256,self.candidate_output_sha256,self.independent_output_sha256)): raise ValueError("recomputation digest")
  if self.candidate_output_sha256!=self.independent_output_sha256: raise ValueError("recomputation mismatch")
  if expected_subject is not None and (type(expected_subject) is not str or self.subject_sha256!=expected_subject):raise ValueError("recomputation execution subject")
  subject=sha("heterodiff-b12-recomputation-subject-v1",{"candidate_output_sha256":self.candidate_output_sha256,"independent_implementation_sha256":self.independent_implementation_sha256,"independent_output_sha256":self.independent_output_sha256,"subject_sha256":self.subject_sha256})
  p=self.predicate.payload()
  if p["predicate_id"]!="RECOMPUTATION_RECEIPT" or p["subject_sha256"]!=subject:raise ValueError("recomputation predicate binding")
 def receipt_subject_sha256(self)->str:
  self.validate();return sha("heterodiff-b12-recomputation-subject-v1",{"candidate_output_sha256":self.candidate_output_sha256,"independent_implementation_sha256":self.independent_implementation_sha256,"independent_output_sha256":self.independent_output_sha256,"subject_sha256":self.subject_sha256})

@dataclass(frozen=True)
class RunnerReceipt:
 capsule:CapsuleReceipt; adapters:tuple[AdapterReceipt,...]; ledger:tuple[LedgerEvent,...]
 recomputation:RecomputationReceipt; predicate_receipts:tuple[AuthenticatedPredicateReceipt,...]
 def validate(self)->None:
  if type(self) is not RunnerReceipt or type(self.capsule) is not CapsuleReceipt or type(self.recomputation) is not RecomputationReceipt:raise ValueError("runner concrete type")
  self.capsule.validate()
  if type(self.adapters) is not tuple: raise ValueError("adapters")
  if not all(type(item) is AdapterReceipt for item in self.adapters):raise ValueError("adapter member concrete type")
  for item in self.adapters:item.validate()
  if tuple((item.adapter_id,item.domain_id,item.config_sha256) for item in self.adapters)!=_ADAPTER_ROSTER_SNAPSHOT:raise ValueError("adapter roster")
  validate_ledger(self.ledger)
  execution_subject=sha("heterodiff-b12-execution-subject-v1",{"adapter_subject_sha256s":[item.subject_sha256() for item in self.adapters],"capsule_manifest_sha256":self.capsule.manifest_sha256,"ledger_event_sha256s":[item.event_sha256 for item in self.ledger]})
  self.recomputation.validate(execution_subject)
  if type(self.predicate_receipts) is not tuple: raise ValueError("predicates")
  if not all(type(item) is AuthenticatedPredicateReceipt for item in self.predicate_receipts):raise ValueError("predicate member concrete type")
  ids=[r.payload()["predicate_id"] for r in self.predicate_receipts]
  if tuple(ids)!=_RESIDUAL_SNAPSHOT: raise ValueError("residual roster")
  runner_subject=sha("heterodiff-b12-runner-subject-v1",{"adapter_subject_sha256s":[item.subject_sha256() for item in self.adapters],"capsule_manifest_sha256":self.capsule.manifest_sha256,"ledger_final_event_sha256":self.ledger[-1].event_sha256,"recomputation_subject_sha256":self.recomputation.receipt_subject_sha256()})
  if any(r.payload()["subject_sha256"]!=runner_subject for r in self.predicate_receipts):raise ValueError("runner predicate subject")

def semantics()->dict[str,Any]:
 return copy.deepcopy({"schema":SCHEMA,"state":"OFFLINE_GAP_CONTRACT_AWAITING_REAL_EVIDENCE",
  "effects":{"field_delta":0,"blocker_delta":0,"formal_test_delta":0,"science_delta":0,"tracker_edited":False},
  "formal_test_states":dict(_FORMAL_TEST_STATE_ITEMS),"f142_scope":{"status":"OPEN",
   "batch_semantics":"PER_METHOD_AND_DOMAIN_ADAPTER_DEFINED_NO_CROSS_DOMAIN_BATCH_ASSUMPTION","shuffle_policy":None},
  "f144_candidate_contract":dict(_F144_ITEMS),"training_fields":{f"F{i}":("NOT_ASSERTED_BY_B12_PACKAGE" if i in (145,146) else "OPEN") for i in range(139,148)},
  "required_adapter_roster":[list(x) for x in _ADAPTER_ROSTER_SNAPSHOT],"residual_predicate_ids":list(_RESIDUAL_SNAPSHOT),"authority":{"runtime":False,"network":False,"data":False,"science":False}})
def semantic_sha256()->str:return sha("heterodiff-b12-gap-semantics-v2",semantics())
def evaluate(receipt:RunnerReceipt|None)->dict[str,Any]:
 if receipt is None:return {"decision":"HOLD","b12_closed":False,"missing_predicates":list(_RESIDUAL_SNAPSHOT),"formal_test_states":dict(_FORMAL_TEST_STATE_ITEMS)}
 receipt.validate()
 return {"decision":"ELIGIBLE_FOR_INDEPENDENT_B12_REVIEW","b12_closed":False,"missing_predicates":[],"formal_test_states":dict(_FORMAL_TEST_STATE_ITEMS)}
