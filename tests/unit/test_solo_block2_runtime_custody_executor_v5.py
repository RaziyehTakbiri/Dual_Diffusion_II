"""Offline hostile qualification for the additive V5 successor executor."""
from __future__ import annotations
import ast, hashlib, importlib.util, inspect, json, os, sys, threading
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v5.py"

@pytest.fixture(scope="module")
def module():
    spec=importlib.util.spec_from_file_location("_solo_block2_runtime_v5",SOURCE)
    assert spec and spec.loader
    value=importlib.util.module_from_spec(spec); sys.modules[spec.name]=value
    try: spec.loader.exec_module(value)
    finally: sys.modules.pop(spec.name,None)
    return value

def test_exact_v5_contract(module):
    assert module.SCHEMA_VERSION=="heterodiff-solo-block2-runtime-custody-executor-v5"
    assert module.MACHINE_SCHEMA=="heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-v5"
    assert module.MACHINE_STATE=="FINAL_V5_OFFLINE_ACTIVATION_SUCCESSOR_FROZEN_RECEIPTS_NULL_NETWORK_HOLD"
    assert module.PACKAGE_AGGREGATE_SCHEMA.endswith("-v5")
    assert (module.V5_ROOT_DEVICE,module.V5_ROOT_INODE,module.V5_ROOT_UID,module.V5_ROOT_GID,module.V5_ROOT_MODE)==(16777234,67067435,501,20,0o700)

def test_predecessor_and_budget_bindings(module):
    assert module.V4_PACKAGE_AGGREGATE_SHA256=="449c5d4954e4ac3829994d4ba5dd17ed401388548a93469cf1f0bb35e67ecb02"
    assert module.V4_MACHINE_RAW_SHA256=="8a18ebb868b657282cba04c1be43ae0f953fabf870002a4edcbdd1bddcd9fc70"
    assert module.V4_MACHINE_SEMANTIC_SHA256=="b3e924742dd164583b5a0aac7a5aec5deca431f75395a3dd7e7800a276bfbea6"
    assert module.V2_PACKAGE_AGGREGATE_SHA256=="48091940a7ceb844c892fb06fd263e479b8c86a1f46c4f0c88d00d72a87439cb"
    assert module.SUCCESSOR_BUDGET_DEFINITION_ID=="da3af347580d19b11f83b8590018a61b2e4296c613f78d8a1039c1c9cfdfb9ce"

def test_row0_request(module):
    op=module.OPERATIONS[0]
    assert len(op.request_bytes)==282
    assert hashlib.sha256(op.request_bytes).hexdigest()=="ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449"

def test_production_signatures_have_no_row(module):
    assert tuple(inspect.signature(module.register_independent_go).parameters)==("custody_root","independent_reviewer_principal","created_unix_ns")
    assert tuple(inspect.signature(module.register_row_authority).parameters)==("custody_root","created_unix_ns","expires_unix_ns","normalized_visible_text")
    assert tuple(inspect.signature(module.attempt).parameters)==("custody_root",)
    assert tuple(inspect.signature(module.register_supersession_authority).parameters)==("custody_root","created_unix_ns","activated_successor_budget_id","normalized_visible_text")

def test_no_row_registrars_pass_none_to_exact_argv_gate():
    tree=ast.parse(SOURCE.read_bytes()); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    for name in ("register_independent_go","register_row_authority"):
        call=next(n for n in ast.walk(funcs[name]) if isinstance(n,ast.Call) and _dot(n.func)=="_open_registrar_root")
        assert isinstance(call.args[2],ast.Constant) and call.args[2].value is None

@pytest.mark.parametrize("bad",[1,True,False,0.0,"0",None])
def test_operation_rejects_nonzero_and_type_confusion(module,bad):
    with pytest.raises(module.GateError): module._operation(bad)

def _dot(node):
    return node.id if isinstance(node,ast.Name) else f"{_dot(node.value)}.{node.attr}" if isinstance(node,ast.Attribute) else ""

def test_operational_call_ownership():
    tree=ast.parse(SOURCE.read_bytes()); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    calls=[_dot(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
    expected={"socket.getaddrinfo":"_bounded_single_getaddrinfo","socket.socket":"_perform_spent_attempt","raw_socket.connect":"_perform_spent_attempt","ssl.SSLContext":"_perform_spent_attempt","context.wrap_socket":"_perform_spent_attempt","tls.sendall":"_perform_spent_attempt","os.fork":"_bounded_single_getaddrinfo","subprocess.run":"_capture_scutil_dns","_bounded_single_getaddrinfo":"_perform_spent_attempt","_perform_spent_attempt":"attempt"}
    for call,owner in expected.items():
        assert calls.count(call)==1
        assert sum(_dot(n.func)==call for n in ast.walk(funcs[owner]) if isinstance(n,ast.Call))==1

def test_spend_precedes_mkdir_intent_network():
    tree=ast.parse(SOURCE.read_bytes()); text=ast.unparse(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="attempt"))
    tokens=("_spend_successor_budget_after_last_authority_gate(","_mkdir_row(","_make_intent(","_exclusive_canonical_at(rowfd, 'intent.json', intent)","_perform_spent_attempt(")
    assert [text.index(x) for x in tokens]==sorted(text.index(x) for x in tokens)

def test_late_gate_call_is_statement_adjacent_to_transport():
    tree=ast.parse(SOURCE.read_bytes()); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="attempt")
    transport=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and _dot(n.func)=="_perform_spent_attempt")
    owner=next(n for n in ast.walk(fn) if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and isinstance(x.value,ast.Call) and _dot(x.value.func)=="_perform_spent_attempt" for x in n.body))
    calls=[node for node in owner.body if isinstance(node,ast.Expr) or isinstance(node,ast.Assign)]
    assert _dot(calls[0].value.func)=="_late_pretransport_gate"
    assert isinstance(calls[1],ast.Assign) and _dot(calls[1].value.func)=="_perform_spent_attempt"

def test_last_gate_immediately_precedes_exclusive_marker():
    source=SOURCE.read_text(); tree=ast.parse(source)
    text=ast.get_source_segment(source,next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_spend_successor_budget_after_last_authority_gate"))
    assert text
    tail=text[text.index("authority_reopened, authority_raw"):text.index("_exclusive_precomputed_successor_budget_marker(")]
    assert "_validate_supersession_authority" not in tail
    assert "row0-authority.revoked" in tail and "expires_unix_ns" in tail

def test_marker_writer_opens_before_any_other_action():
    tree=ast.parse(SOURCE.read_bytes()); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_exclusive_precomputed_successor_budget_marker")
    first=fn.body[1] if isinstance(fn.body[0],ast.Expr) else fn.body[0]
    assert isinstance(first,ast.Assign) and isinstance(first.value,ast.Call) and _dot(first.value.func)=="os.open"

def test_direct_binding_key_rosters(module):
    assert {"exact_url","socket_instance_limit","preflight_authority_record_sha256","runtime_manifest_sha256"} <= set(module.SUCCESSOR_BUDGET_SPEND_KEYS)
    assert {"successor_budget_definition_id","activated_successor_budget_id"} <= set(module.ROW_AUTHORITY_KEYS)
    assert {"successor_budget_scope","row1_may_consume","v2_receipts_reused","version_or_root_reset_spent_budget"} <= set(module.ROW_AUTHORITY_KEYS)
    assert {"authority_expires_unix_ns","authority_negated_or_revoked","authority_revocation_slot_absent","resolver_child_fork_site_limit"} <= set(module.SUCCESSOR_BUDGET_SPEND_KEYS)
    source=SOURCE.read_text(); assert '"activated_successor_budget_id": supersession["activated_successor_budget_id"]' in source

def test_final_authority_direct_flags_are_typed_and_validated():
    tree=ast.parse(SOURCE.read_bytes()); text=ast.unparse(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_validate_row_authority"))
    for fragment in ("'successor_budget_scope': SUCCESSOR_BUDGET_SCOPE","'row1_may_consume': False","'v2_receipts_reused': False","'version_or_root_reset_spent_budget': False","type(authority.get(key)) is not type(expected)"):
        assert fragment in text

def test_go_validation_map_binds_activated_id():
    tree=ast.parse(SOURCE.read_bytes()); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_validate_go")
    text=ast.unparse(fn)
    assert "'activated_successor_budget_id': supersession['activated_successor_budget_id']" in text

def test_no_duplicate_literal_dict_keys():
    for node in ast.walk(ast.parse(SOURCE.read_bytes())):
        if isinstance(node,ast.Dict):
            keys=[key.value for key in node.keys if isinstance(key,ast.Constant) and isinstance(key.value,str)]
            assert len(keys)==len(set(keys)),f"duplicate dict key at line {node.lineno}"

def test_fixed_key_rosters_equal_builder_literals(module):
    tree=ast.parse(SOURCE.read_bytes()); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    pairs=(("register_supersession_authority",module.SUPERSESSION_AUTHORITY_KEYS),("register_preflight_authority",module.PREFLIGHT_AUTHORITY_KEYS),("_runtime_preflight_record",module.RUNTIME_PREFLIGHT_KEYS),("register_independent_go",module.INDEPENDENT_GO_KEYS),("register_row_authority",module.ROW_AUTHORITY_KEYS),("_spend_successor_budget_after_last_authority_gate",module.SUCCESSOR_BUDGET_SPEND_KEYS))
    for name,roster in pairs:
        candidates=[]
        for node in ast.walk(funcs[name]):
            if isinstance(node,ast.Dict):
                keys={key.value for key in node.keys if isinstance(key,ast.Constant) and isinstance(key.value,str)}
                if {"schema_version","record_sha256"}<=keys: candidates.append(keys)
        assert candidates==[set(roster)],name

def test_visible_authorities_bind_ids_times_and_acknowledgements():
    source=SOURCE.read_text()
    for token in ("activated_successor_budget_id=","created_unix_ns=","expires_unix_ns=","negated_or_revoked=false","acknowledge_v2_row0_spent_at_durable_intent=true","acknowledge_v2_terminal_no_retry=true","acknowledge_sendall_zero_does_not_restore_budget=true"):
        assert token in source

def test_preflight_chronology_explicitly_postdates_supersession():
    tree=ast.parse(SOURCE.read_bytes()); funcs={n.name:ast.unparse(n) for n in tree.body if isinstance(n,ast.FunctionDef)}
    for name in ("register_preflight_authority","_validate_preflight_authority"):
        assert "supersession['created_unix_ns']" in funcs[name] or "supersession.get('created_unix_ns', 0)" in funcs[name]

def test_late_revocation_blocks_transport_and_retains_spend_intent(module,tmp_path,monkeypatch):
    bundle=_bundle(module,tmp_path,monkeypatch)
    try:
        spend,raw_sha=module._spend_successor_budget_after_last_authority_gate(*bundle)
        (tmp_path/"intent.json").write_bytes(b"durable-intent")
        (tmp_path/"row0-authority.revoked").write_bytes(b"")
        entered=[]; monkeypatch.setattr(module,"_perform_spent_attempt",lambda *a,**k:entered.append(True))
        with pytest.raises(module.GateError,match="late pre-transport"):
            module._late_pretransport_gate(bundle[0],module._validate_row_authority(),spend,raw_sha,{"successor-budget-spend.json","intent.json"})
        assert entered==[] and (tmp_path/"successor-budget-spend.json").exists() and (tmp_path/"intent.json").exists()
    finally: os.close(bundle[0])

def _bundle(module,tmp_path,monkeypatch):
    fd=os.open(tmp_path,os.O_RDONLY|os.O_DIRECTORY); op=module.OPERATIONS[0]
    package={"record_sha256":"1"*64,"package_aggregate_sha256":"2"*64}; preflight={"record_sha256":"3"*64,"preflight_authority_record_sha256":"8"*64,"runtime_manifest_sha256":"9"*64}; go={"record_sha256":"4"*64}
    root={"absolute_path":module.V5_OPERATIONAL_ROOT,"device":module.V5_ROOT_DEVICE,"inode":module.V5_ROOT_INODE,"uid":501,"gid":20,"mode_octal":"0700","nlink":2}
    authority={key:None for key in module.ROW_AUTHORITY_KEYS}; authority.update(schema_version=module.ROW_AUTHORITY_SCHEMA,record_sha256="5"*64,expires_unix_ns=2**63,negated_or_revoked=False)
    raw=module._canonical_bytes(authority); monkeypatch.setattr(module,"_validate_row_authority",lambda *a:authority); original=module._read_receipt_at
    def read(dirfd,basename,**kwargs):
        if basename=="row0-authority.json":
            class St: st_mode=0o100600; st_nlink=1
            return authority,raw,St()
        return original(dirfd,basename,**kwargs)
    monkeypatch.setattr(module,"_read_receipt_at",read)
    supersession={"record_sha256":"6"*64,"activated_successor_budget_id":"7"*64}
    return fd,op,package,preflight,go,root,supersession

def test_marker_durable_and_second_spend_blocked(module,tmp_path,monkeypatch):
    b=_bundle(module,tmp_path,monkeypatch)
    try:
        record,digest=module._spend_successor_budget_after_last_authority_gate(*b); raw=(tmp_path/"successor-budget-spend.json").read_bytes()
        parsed=json.loads(raw)
        assert hashlib.sha256(raw).hexdigest()==digest and parsed["record_sha256"]==record["record_sha256"]
        assert parsed["row1_may_consume"] is False and parsed["version_or_root_reset_spent_budget"] is False
        assert parsed["v2_receipts_reused"] is False and parsed["address_fallback_limit"]==0
        with pytest.raises(module.CustodyError,match="budget is spent"): module._spend_successor_budget_after_last_authority_gate(*b)
    finally: os.close(b[0])

@pytest.mark.parametrize("existing",[b"",b"partial",b"{}\n"])
def test_partial_marker_is_spent(module,tmp_path,monkeypatch,existing):
    (tmp_path/"successor-budget-spend.json").write_bytes(existing); b=_bundle(module,tmp_path,monkeypatch)
    try:
        with pytest.raises(module.CustodyError,match="budget is spent"): module._spend_successor_budget_after_last_authority_gate(*b)
    finally: os.close(b[0])

def test_crash_after_exclusive_create_retains_spend(module,tmp_path,monkeypatch):
    b=_bundle(module,tmp_path,monkeypatch); original=module._write_all
    def crash(fd,raw): os.write(fd,raw[:7]); raise OSError("injected crash")
    monkeypatch.setattr(module,"_write_all",crash)
    try:
        with pytest.raises(OSError,match="injected crash"): module._spend_successor_budget_after_last_authority_gate(*b)
        assert (tmp_path/"successor-budget-spend.json").exists(); monkeypatch.setattr(module,"_write_all",original)
        with pytest.raises(module.CustodyError,match="budget is spent"): module._spend_successor_budget_after_last_authority_gate(*b)
    finally: os.close(b[0])

def test_concurrent_spends_have_at_most_one_winner(module,tmp_path,monkeypatch):
    b=_bundle(module,tmp_path,monkeypatch); results=[]
    def run():
        try: module._spend_successor_budget_after_last_authority_gate(*b); results.append("won")
        except (module.CustodyError,FileExistsError): results.append("lost")
    threads=[threading.Thread(target=run) for _ in range(2)]
    try:
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        assert results.count("won")==1 and results.count("lost")==1
    finally: os.close(b[0])

def test_revocation_is_pre_marker_zero_mutation(module,tmp_path,monkeypatch):
    (tmp_path/"row0-authority.revoked").write_bytes(b""); b=_bundle(module,tmp_path,monkeypatch)
    try:
        with pytest.raises(module.GateError,match="revocation"): module._spend_successor_budget_after_last_authority_gate(*b)
        assert not (tmp_path/"successor-budget-spend.json").exists()
    finally: os.close(b[0])

def test_alternate_root_fails_before_open(module,monkeypatch):
    monkeypatch.setattr(module.os,"open",lambda *a,**k:pytest.fail("open reached"))
    with pytest.raises(module.GateError,match="one exact V5 operational root"): module._open_root("/private/tmp/not-v5")

def test_no_legacy_authority_or_cli_labels():
    source=SOURCE.read_text(); assert "0|1" not in source and "ROOT_PAGE_ATTEMPT_V3" not in source and "OFFLINE_RUNTIME_PREFLIGHT_V2" not in source
