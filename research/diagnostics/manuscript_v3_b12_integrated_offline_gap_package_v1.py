#!/usr/bin/env python3
"""Hash-first, stable-descriptor B12 v2 candidate validator."""
import hashlib,json,os,stat,sys,types
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
FIXTURE=Path("research/fixtures/manuscript_v3_b12_integrated_offline_gap_package_v1.json")
EXPECTED_BINDINGS=(
("PROJECT_B12_INTEGRATED_OFFLINE_IMPLEMENTATION_GAP_PACKAGE.md",2414,"421ee28c8e4cf6e886e22759518fb8bfd125bf46891a42fbdecd8d7f589a9b95",True),
("src/heterodiff/evaluation/b12_integrated_offline_candidate.py",14944,"b77c6eea6859fa9d6181a94a27112d97555e5a4d60ab1df1ee03a30c7808defd",True),
("PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE_INDEPENDENT_REVIEW.md",13421,"a0aa207a0a68545d0af7ba5e252d7c30f1349d799e0e61ebf807c2426ee22209",True),
("research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json",186707,"b789b4b39aef1cef3134dddee506409f311b79cc70b1d121daa0a2ff22267f21",True),
("PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md",10230,"7694694d7fe2b0c2dd17f79b9e0f9d2f44c14c59c3f0568902e3cad7d75ae402",True),
("research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json",12639,"c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54",True),
("PROJECT_F105_MANUSCRIPT_PRODUCTION_INTEGRATION_INDEPENDENT_REVIEW.md",9128,"a8e6c5d42847b8dcf28e238bddd5d006852bbff85eb161967ca1ff398c204d82",True),
("research/fixtures/manuscript_v3_f105_manuscript_production_integration_v1.json",5495,"251edc5792dd5545c40eb45ec528f98b133a0b154f5d0f5ef3bb3db4df325126",True),
("PROJECT_FORMAL_TEST29_TEST30_TWO_MACROSTEP_PATH_INDEPENDENT_REVIEW.md",10216,"f5bf0587b8400999cfa35a3426661538d72bf0345aff22309016ac2e87a96eae",True),
("research/fixtures/manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.json",22780,"6909b2aeeb912024689b1dc43704549c855ccc1d37fbe67a8f412ed4adb38bb3",True),
("research/fixtures/cp75_test28_production_schema_acceptance_review_request_v1.json",45650,"7fa8601dc3c058489281509eacab4448560a468d1051a71092f40fe49a04155b",False),
("research/fixtures/cp75_test28_production_schema_acceptance_review_packet_manifest_v1.json",4347,"2f76e7bbd74f992a4307e7c2b06974c24e31eefbbe7c0237e2d7527ae2039708",False))
TOP_KEYS=("bindings","effects","record_sha256","schema_version","semantic_sha256","semantics","state")
EFFECTS={"blocker_delta":0,"field_delta":0,"formal_test_delta":0,"science_delta":0,"tracker_edited":False}
def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError("duplicate key")
  d[k]=v
 return d
def _read(root:Path,rel:Path,size:int)->bytes:
 if not hasattr(os,"O_NOFOLLOW") or not hasattr(os,"O_DIRECTORY"):raise ValueError("no-follow unavailable")
 opened=[];rf=os.open(str(root),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);opened.append(rf)
 try:
  before=os.fstat(rf);cur=rf
  for part in rel.parts[:-1]:cur=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=cur);opened.append(cur)
  fd=os.open(rel.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=cur);opened.append(fd);s=os.fstat(fd)
  if not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode)!=0o644 or s.st_nlink!=1 or s.st_size!=size:raise ValueError("custody")
  data=b""
  while len(data)<=size:
   chunk=os.read(fd,size+1-len(data))
   if not chunk:break
   data+=chunk
  after=os.fstat(fd);rb=os.fstat(rf)
  identity=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
  if identity(s)!=identity(after) or identity(before)!=identity(rb) or len(data)!=size:raise ValueError("unstable")
  return data
 finally:
  for fd in reversed(opened):os.close(fd)
def validate(root=ROOT,fixture_path=FIXTURE):
 if not isinstance(root,Path) or not root.is_absolute() or root.resolve()!=root:raise ValueError("canonical root")
 raw=_read(root,fixture_path,(root/fixture_path).stat().st_size);r=json.loads(raw,object_pairs_hook=pairs)
 if tuple(r)!=TOP_KEYS or raw!=json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()+b"\n":raise ValueError("machine schema")
 if type(r["schema_version"]) is not str or r["schema_version"]!="heterodiff-manuscript-v3-b12-integrated-offline-gap-package-v2" or type(r["state"]) is not str or r["state"]!="OFFLINE_GAP_CONTRACT_AWAITING_REAL_EVIDENCE" or r["effects"]!=EFFECTS:raise ValueError("fixed identity")
 expected=[{"bytes":n,"ordinal":i,"path":p,"raw_sha256":h,"terminal_lf":lf} for i,(p,n,h,lf) in enumerate(EXPECTED_BINDINGS)]
 if r["bindings"]!=expected:raise ValueError("binding roster")
 body=dict(r);claimed=body.pop("record_sha256")
 if claimed!=hashlib.sha256(b"heterodiff-b12-machine-v2\0"+json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest():raise ValueError("record")
 captured={}
 for p,n,h,lf in EXPECTED_BINDINGS:
  rel=PurePosixPath(p)
  if rel.is_absolute() or ".." in rel.parts:raise ValueError("path")
  data=_read(root,Path(*rel.parts),n)
  if hashlib.sha256(data).hexdigest()!=h or data.endswith(b"\n") is not lf:raise ValueError("binding")
  captured[p]=data
 name="b12_verified";mod=types.ModuleType(name);mod.__file__="<verified-b12-source>";sys.modules[name]=mod
 exec(compile(captured[EXPECTED_BINDINGS[1][0]],mod.__file__,"exec"),mod.__dict__)
 if mod.semantics()!=r["semantics"] or mod.semantic_sha256()!=r["semantic_sha256"]:raise ValueError("semantics")
 return {"status":"PASS","record_sha256":claimed,"semantic_sha256":r["semantic_sha256"],"binding_count":12}
if __name__=="__main__":print(json.dumps(validate(),sort_keys=True))
