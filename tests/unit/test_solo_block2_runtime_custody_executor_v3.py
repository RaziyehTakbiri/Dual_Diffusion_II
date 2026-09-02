from __future__ import annotations

import ast
import enum
import fcntl
import hashlib
import importlib.util
import inspect
import json
import os
import socket
import ssl
import stat
import sys
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PARENT_PARSER_MODULE_NAME = "_heterodiff_accepted_solo_block2_parser_v2"
SOURCE = (
    ROOT
    / "src"
    / "heterodiff"
    / "artifacts"
    / "solo_block2_runtime_custody_executor_v3.py"
)


def _load():
    name = "solo_block2_runtime_custody_executor_v3_test_import"
    spec = importlib.util.spec_from_file_location(name, SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", autouse=True)
def isolate_parent_parser_module():
    """Keep other suites' accepted-parser import state outside this module."""

    prior = sys.modules.pop(PARENT_PARSER_MODULE_NAME, None)
    try:
        yield
    finally:
        sys.modules.pop(PARENT_PARSER_MODULE_NAME, None)
        if prior is not None:
            sys.modules[PARENT_PARSER_MODULE_NAME] = prior


@pytest.fixture(scope="module")
def runtime(isolate_parent_parser_module):
    del isolate_parent_parser_module
    return _load()


def _head(*headers: bytes, status: bytes = b"HTTP/1.1 200 OK") -> bytes:
    return status + b"\r\n" + b"\r\n".join(headers) + b"\r\n\r\n"


def _normalized_resolver_rows(runtime, *system_rows, host="example.com"):
    child_rows = [
        runtime._resolver_system_tuple_to_json_row(item) for item in system_rows
    ]
    json_rows = json.loads(json.dumps(child_rows))
    return runtime._strict_resolver_rows(json_rows, host)


def test_import_has_zero_network_process_or_entropy_calls(monkeypatch):
    calls: list[str] = []

    def forbidden(*args, **kwargs):
        calls.append("called")
        raise AssertionError("import reached operational API")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(ssl, "SSLContext", forbidden)
    monkeypatch.setattr(os, "fork", forbidden)
    import subprocess

    monkeypatch.setattr(subprocess, "run", forbidden)
    module = _load()
    assert module.OPERATIONS[0].host == "physionet.org"
    assert calls == []


def test_exact_closed_operation_roster_and_requests(runtime):
    assert len(runtime.OPERATIONS) == 2
    assert [item.ordinal for item in runtime.OPERATIONS] == [0, 1]
    assert [item.url for item in runtime.OPERATIONS] == [
        "https://physionet.org/content/challenge-2012/1.0.0/",
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
    ]
    for operation in runtime.OPERATIONS:
        request = operation.request_bytes
        assert request.startswith(b"GET " + operation.path.encode() + b" HTTP/1.1\r\n")
        assert request.count(b"\r\n\r\n") == 1
        assert request.endswith(b"Connection: close\r\n\r\n")
        assert b"Authorization:" not in request
        assert b"Cookie:" not in request
        assert b"Referer:" not in request
        assert b"Range:" not in request
    assert [item.operation_id for item in runtime.OPERATIONS] == [
        "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "SB2-PUBLIC-ROOT-UCI-001",
    ]
    assert [len(item.request_bytes) for item in runtime.OPERATIONS] == [282, 287]
    parent = runtime._ensure_parent_parser()
    for ordinal, operation in enumerate(runtime.OPERATIONS):
        assert operation.request_bytes == parent.exact_request_bytes(ordinal)
        assert operation.operation_id == parent.operation_spec(ordinal)["operation_id"]


def test_v3_machine_state_is_exact_and_prior_state_is_rejected(runtime):
    runtime._require_machine_state({"state": runtime.MACHINE_STATE})
    with pytest.raises(runtime.GateError, match="stopped v3 candidate state"):
        runtime._require_machine_state(
            {
                "state": (
                    "FINAL_EXECUTOR_QUALIFIED_OPERATIONAL_RECEIPTS_NULL_FETCH_HOLD"
                )
            }
        )


def test_v3_machine_non_effect_keys_and_null_root_are_exact(runtime):
    slots = {"package_lock": None, "row0_intent": None}
    runtime._require_machine_non_effects(
        {
            "checklist_effects": {
                "v3_fetch_performed": False,
                "v3_resolver_call_performed": False,
                "v3_durable_row_intent_created": False,
                "v3_operational_receipt_created": False,
                "v3_operational_root_created": False,
            },
            "current_operational_slots": slots,
            "operational_custody_root": None,
        }
    )
    with pytest.raises(runtime.GateError, match="v3 activity"):
        runtime._require_machine_non_effects(
            {
                "checklist_effects": {
                    "fetch_performed": False,
                    "resolver_call_performed": False,
                    "durable_row_intent_created": False,
                },
                "current_operational_slots": slots,
                "operational_custody_root": None,
            }
        )
    for key in (
        "v3_fetch_performed",
        "v3_resolver_call_performed",
        "v3_durable_row_intent_created",
        "v3_operational_receipt_created",
        "v3_operational_root_created",
    ):
        effects = {
            "v3_fetch_performed": False,
            "v3_resolver_call_performed": False,
            "v3_durable_row_intent_created": False,
            "v3_operational_receipt_created": False,
            "v3_operational_root_created": False,
        }
        effects[key] = True
        with pytest.raises(runtime.GateError, match="v3 activity"):
            runtime._require_machine_non_effects(
                {
                    "checklist_effects": effects,
                    "current_operational_slots": slots,
                    "operational_custody_root": None,
                }
            )


def test_load_machine_accepts_final_v3_fixture(runtime):
    machine, raw = runtime._load_machine()
    assert machine["state"] == runtime.MACHINE_STATE
    assert machine["schema_version"] == runtime.MACHINE_SCHEMA
    assert hashlib.sha256(raw).hexdigest()


def test_load_machine_rejects_resigned_final_fixture_mutants(runtime, monkeypatch):
    machine, _raw = runtime._load_machine()
    real_read = runtime._read_regular_path_nofollow

    def rejected(mutator):
        mutant = json.loads(json.dumps(machine))
        mutator(mutant)
        mutant["record_sha256"] = None
        mutant["record_sha256"] = runtime._self_digest(mutant)
        mutant_raw = runtime._canonical_bytes(mutant)

        def read(path, cap):
            if path.endswith(runtime.MACHINE_RELATIVE_PATH):
                return mutant_raw, {"sha256": hashlib.sha256(mutant_raw).hexdigest()}
            return real_read(path, cap)

        monkeypatch.setattr(runtime, "_read_regular_path_nofollow", read)
        with pytest.raises(runtime.GateError):
            runtime._load_machine()

    rejected(lambda value: value["checklist_effects"].pop("v3_fetch_performed"))
    rejected(
        lambda value: value["checklist_effects"].__setitem__(
            "v3_resolver_call_performed", True
        )
    )
    rejected(
        lambda value: value["executor_contract"].pop(
            "executing_image_one_open_attestation_claimed"
        )
    )
    rejected(
        lambda value: value["executor_contract"].__setitem__(
            "registrar_identity_and_time_are_caller_assertions", False
        )
    )


def test_production_surface_has_no_dependency_or_transcript_injection(runtime):
    assert list(inspect.signature(runtime.preflight).parameters) == ["custody_root"]
    assert list(inspect.signature(runtime.attempt).parameters) == ["custody_root", "row"]
    assert list(inspect.signature(runtime.main).parameters) == []
    for function in (runtime.preflight, runtime.attempt):
        names = set(inspect.signature(function).parameters)
        assert not names & {
            "transport",
            "resolver",
            "socket_factory",
            "clock",
            "environment",
            "filesystem",
            "client",
            "transcript",
            "dependencies",
        }


@pytest.mark.parametrize(
    "body,headers,framing",
    [
        (b"<html>official page</html>", [b"Content-Type: text/html", b"Content-Length: 26"], "CONTENT_LENGTH"),
        (b"plain official page", [b"Content-Type: text/plain"], "CONNECTION_CLOSE"),
        (
            b"5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n",
            [b"Content-Type: text/plain", b"Transfer-Encoding: chunked"],
            "CHUNKED",
        ),
    ],
)
def test_pure_loopback_free_response_success(runtime, body, headers, framing):
    result = runtime.qualify_retained_response(_head(*headers), body)
    assert result["status_code"] == 200
    assert result["framing"] == framing
    assert result["decoded_entity"]


@pytest.mark.parametrize(
    "head,body,error",
    [
        (_head(b"Content-Type: text/plain", b"Content-Length: 1", b"Content-Length: 1"), b"x", "ProtocolError"),
        (_head(b"Content-Type: text/plain", b"Content-Length: 1", b"Transfer-Encoding: chunked"), b"x", "ProtocolError"),
        (_head(b"Content-Type: text/plain", b"Location: https://example.invalid/"), b"x", "ScopeError"),
        (_head(b"Content-Type: text/plain", b"Set-Cookie: x=y"), b"x", "ScopeError"),
        (_head(b"Content-Type: text/plain", b"Content-Disposition: inline"), b"x", "ScopeError"),
        (_head(b"Content-Type: text/plain", status=b"HTTP/1.1 302 Found"), b"x", "ContentError"),
        (_head(b"Content-Type: text/plain", status=b"HTTP/1.1 100 Continue"), b"x", "ProtocolError"),
        (_head(b"Content-Type: application/octet-stream"), b"x", "ScopeError"),
        (_head(b"Content-Type: text/plain", b"Content-Encoding: gzip"), b"x", "ScopeError"),
        (_head(b"Content-Type: text/plain"), b"PK\x03\x04payload", "ScopeError"),
        (_head(b"Content-Type: text/plain"), b"verify you are human", "ScopeError"),
        (_head(b"Content-Type: text/plain"), b"\xff", "ContentError"),
        (_head(b"Content-Type: text/plain"), b"\xef\xbb\xbftext", "ContentError"),
        (_head(b"Content-Type: text/plain"), b"a\x00b", "ContentError"),
        (_head(b"Content-Type: text/plain", b" folded: no"), b"x", "ProtocolError"),
    ],
)
def test_hostile_response_rejections(runtime, head, body, error):
    with pytest.raises(getattr(runtime, error)):
        runtime.qualify_retained_response(head, body)


@pytest.mark.parametrize(
    "raw",
    [
        b"1;ext=x\r\na\r\n0\r\n\r\n",
        b"1\r\na\n0\r\n\r\n",
        b"1\r\na\r\n0\r\nX: y\r\n\r\n",
        b"1\r\na\r\n0\r\n\r\nextra",
        b"1\r\na\r\n",
    ],
)
def test_chunked_ambiguity_rejected(runtime, raw):
    with pytest.raises(runtime.ProtocolError):
        runtime.qualify_retained_response(
            _head(b"Content-Type: text/plain", b"Transfer-Encoding: chunked"), raw
        )


def test_chunked_leading_zero_matches_accepted_v2_semantics(runtime):
    result = runtime.qualify_retained_response(
        _head(b"Content-Type: text/plain", b"Transfer-Encoding: chunked"),
        b"01\r\na\r\n0\r\n\r\n",
    )
    assert result["accepted"] is True
    assert result["decoded_entity"] == b"a"


def test_body_cap_boundaries(runtime):
    cap = runtime.MAX_RAW_TRANSFER_BODY_BYTES
    head = _head(b"Content-Type: text/plain")
    accepted = b"a" * runtime.MAX_DECODED_ENTITY_BYTES
    result = runtime.qualify_retained_response(head, accepted)
    assert result["decoded_entity_bytes"] == runtime.MAX_DECODED_ENTITY_BYTES
    with pytest.raises(runtime.ContentError):
        runtime.qualify_retained_response(head, b"a" * (cap + 1))


def test_oversized_body_preserves_protocol_then_scope_precedence(runtime):
    oversized = b"a" * (runtime.MAX_RAW_TRANSFER_BODY_BYTES + 1)
    with pytest.raises(runtime.ProtocolError):
        runtime.qualify_retained_response(
            _head(
                b"Content-Type: text/plain",
                b"Content-Length: 1",
                b"Content-Length: 1",
            ),
            oversized,
        )
    with pytest.raises(runtime.ScopeError):
        runtime.qualify_retained_response(
            _head(b"Content-Type: text/plain", b"Location: https://example.invalid/"),
            oversized,
        )


def test_all_36_accepted_v2_diagnostics_are_preserved(runtime):
    result = runtime.qualify_retained_response(
        _head(b"Content-Type: text/plain", b"Content-Length: 1"), b"x"
    )
    parent = runtime._ensure_parent_parser()
    fields = {name for name, _kind in parent.OUTCOME_DIAGNOSTIC_FIELD_TYPES}
    assert set(result["diagnostics"]) == fields
    assert all(result[name] == result["diagnostics"][name] for name in fields)
    assert result["diagnostic_field_types_sha256"] == (
        parent.OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
    )


def test_row1_parser_replay_has_required_context(runtime):
    prior = (_head(b"Content-Type: text/plain", b"Content-Length: 1"), b"x")
    result = runtime.qualify_retained_response(
        _head(b"Content-Type: text/plain", b"Content-Length: 1"),
        b"x",
        row_ordinal=1,
        prior_row0=prior,
    )
    assert result["accepted"] is True
    assert result["status_code"] == 200


def test_row1_context_is_required_and_digest_sensitive(runtime):
    current_head = _head(b"Content-Type: text/plain", b"Content-Length: 1")
    with pytest.raises(TypeError, match="requires exact retained row 0 bytes"):
        runtime.qualify_retained_response(current_head, b"z", row_ordinal=1)
    with pytest.raises(runtime.GateError, match="custody-requalified row 0"):
        runtime._qualify_retained_response_observation(
            current_head, b"z", row_ordinal=1
        )
    first = runtime.qualify_retained_response(
        current_head,
        b"z",
        row_ordinal=1,
        prior_row0=(current_head, b"x"),
    )
    second = runtime.qualify_retained_response(
        current_head,
        b"z",
        row_ordinal=1,
        prior_row0=(current_head, b"y"),
    )
    assert first["previous_qualification_outcome_sha256"] != (
        second["previous_qualification_outcome_sha256"]
    )


@pytest.mark.parametrize(
    "value",
    [
        [],
        [[socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ["127.0.0.1", 443]]],
        [[socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ["10.0.0.1", 443]]],
        [[socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ["::1", 443, 0, 0]]],
        [[socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP, "", ["93.184.216.34", 443]]],
        [[socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ["93.184.216.34", 80]]],
    ],
)
def test_resolver_tuple_hostility(runtime, value):
    with pytest.raises(runtime.ExecutorError):
        runtime._strict_resolver_rows(value, "example.com")


def test_resolver_order_preserved_first_global_selected(runtime):
    rows = _normalized_resolver_rows(
        runtime,
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443)),
        (
            socket.AF_INET6,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("2606:2800:220:1:248:1893:25c8:1946", 443, 0, 0),
        ),
    )
    assert [item["numeric_ip"] for item in rows] == [
        "93.184.216.34",
        "2606:2800:220:1:248:1893:25c8:1946",
    ]


def test_resolver_rejects_mixed_unsupported_tuple_and_preserves_duplicates(runtime):
    valid = [
        runtime.AF_INET_INT,
        runtime.SOCK_STREAM_INT,
        runtime.IPPROTO_TCP_INT,
        "",
        ["93.184.216.34", 443],
    ]
    rows = runtime._strict_resolver_rows([valid, valid], "example.com")
    assert len(rows) == 2
    invalid = [int(socket.AF_UNIX), runtime.SOCK_STREAM_INT, 0, "", ["x"]]
    with pytest.raises(runtime.ExecutorError, match="unsupported address family"):
        runtime._strict_resolver_rows([valid, invalid], "example.com")


def test_actual_socket_enums_normalize_to_exact_json_integers(runtime):
    system_row = (
        socket.AF_INET,
        socket.SOCK_STREAM,
        socket.IPPROTO_TCP,
        "",
        ("93.184.216.34", 443),
    )
    child_row = runtime._resolver_system_tuple_to_json_row(system_row)
    assert all(type(child_row[index]) is int for index in (0, 1, 2))
    rows = _normalized_resolver_rows(
        runtime, system_row, host=runtime._operation(0).host
    )
    row = rows[0]
    assert all(
        type(row[key]) is int
        for key in ("family", "socktype", "protocol", "port", "flowinfo", "scope_id")
    )
    assert runtime._validate_resolver_receipt_rows(rows, runtime._operation(0)) == rows


class _HostileIntEnum(enum.IntEnum):
    VALUE = 1


class _HostileInt(int):
    pass


@pytest.mark.parametrize(
    "index,bad",
    [
        (0, _HostileInt(2)),
        (1, _HostileIntEnum.VALUE),
        (2, _HostileInt(6)),
        (2, True),
    ],
)
def test_system_resolver_boundary_rejects_unapproved_integer_subclasses(
    runtime, index, bad
):
    system_row = [
        socket.AF_INET,
        socket.SOCK_STREAM,
        socket.IPPROTO_TCP,
        "",
        ("93.184.216.34", 443),
    ]
    system_row[index] = bad
    with pytest.raises(runtime.ExecutorError, match="system resolver tuple leaf type invalid"):
        runtime._resolver_system_tuple_to_json_row(tuple(system_row))


@pytest.mark.parametrize(
    "key,bad",
    [
        ("family", socket.AF_INET),
        ("socktype", socket.SOCK_STREAM),
        ("protocol", _HostileInt(6)),
        ("port", True),
        ("flowinfo", 0.0),
        ("scope_id", _HostileIntEnum.VALUE),
    ],
)
def test_resolver_receipt_rejects_non_builtin_integer_leaves(runtime, key, bad):
    rows = _normalized_resolver_rows(
        runtime,
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("93.184.216.34", 443),
        ),
    )
    rows[0][key] = bad
    with pytest.raises(runtime.GateError, match="resolver receipt row value invalid"):
        runtime._validate_resolver_receipt_rows(rows, runtime._operation(0))


def test_resolver_validation_precedes_socket_and_tls(runtime):
    source = inspect.getsource(runtime._perform_spent_attempt)
    assert source.index("_validate_resolver_receipt_rows(") < source.index("socket.socket(")
    assert source.index("_validate_resolver_receipt_rows(") < source.index("ssl.SSLContext(")


def test_invalid_resolver_receipt_cannot_reach_socket_or_tls(
    runtime, monkeypatch
):
    calls: list[str] = []

    def forbidden_socket(*_args, **_kwargs):
        calls.append("socket")
        raise AssertionError("invalid resolver receipt reached socket creation")

    def forbidden_tls(*_args, **_kwargs):
        calls.append("tls")
        raise AssertionError("invalid resolver receipt reached TLS context creation")

    op = runtime._operation(0)
    invalid = [
        {
            "family": runtime.AF_INET_INT,
            "socktype": socket.SOCK_STREAM,
            "protocol": runtime.IPPROTO_TCP_INT,
            "canonical_name": "",
            "numeric_ip": "93.184.216.34",
            "port": 443,
            "flowinfo": 0,
            "scope_id": 0,
            "queried_host": op.host,
        }
    ]
    monkeypatch.setattr(
        runtime,
        "_bounded_single_getaddrinfo",
        lambda *_args: invalid,
    )
    monkeypatch.setattr(runtime.socket, "socket", forbidden_socket)
    monkeypatch.setattr(runtime.ssl, "SSLContext", forbidden_tls)
    with pytest.raises(runtime.GateError, match="resolver receipt row value invalid"):
        runtime._perform_spent_attempt(
            op,
            {},
            time.monotonic() + 1,
            runtime.AttemptProgress(),
            None,
        )
    assert calls == []


def test_raw_receipt_forward_link_does_not_confuse_semantic_self_digest(runtime):
    record = {
        "schema_version": "test",
        "record_sha256": None,
        "value": 1,
    }
    record["record_sha256"] = runtime._self_digest(record)
    raw = runtime._canonical_bytes(record)
    raw_digest = hashlib.sha256(raw).hexdigest()
    assert raw_digest != record["record_sha256"]
    runtime._require_raw_receipt_forward_link(raw_digest, raw, "test intent")
    with pytest.raises(runtime.GateError, match="raw receipt forward link mismatch"):
        runtime._require_raw_receipt_forward_link(
            record["record_sha256"], raw, "test intent"
        )


def test_canonical_json_rejects_duplicate_extra_and_bool_integer(runtime):
    raw = b'{"record_sha256":"' + b"0" * 64 + b'","schema_version":"x","schema_version":"x"}\n'
    with pytest.raises(runtime.GateError):
        runtime._parse_canonical_record(raw, schema="x")
    operation = runtime._operation(0)
    assert operation.ordinal == 0
    with pytest.raises(runtime.GateError):
        runtime._operation(False)
    value = {"schema_version": "x", "record_sha256": None, "extra": False}
    value["record_sha256"] = runtime._self_digest(value)
    with pytest.raises(runtime.GateError):
        runtime._parse_canonical_record(
            runtime._canonical_bytes(value),
            schema="x",
            exact_keys=("record_sha256", "schema_version"),
        )


def test_componentwise_nofollow_root_and_exclusive_custody(runtime, tmp_path):
    real = tmp_path / "real" / "root"
    real.mkdir(parents=True, mode=0o700)
    real.chmod(0o700)
    fd, st = runtime._open_root(str(real))
    assert stat.S_IMODE(st.st_mode) == 0o700
    try:
        record = {"schema_version": "test", "record_sha256": None, "value": 1}
        digest, _ = runtime._exclusive_canonical_at(fd, "one.json", record)
        assert len(digest) == 64
        with pytest.raises(FileExistsError):
            runtime._exclusive_canonical_at(
                fd,
                "one.json",
                {"schema_version": "test", "record_sha256": None, "value": 2},
            )
    finally:
        os.close(fd)
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real", target_is_directory=True)
    with pytest.raises(OSError):
        runtime._open_root(str(link / "root"))


def test_componentwise_nofollow_runtime_file_rejects_intermediate_symlink(
    runtime, tmp_path
):
    real = tmp_path / "real"
    real.mkdir()
    target = real / "input.bin"
    target.write_bytes(b"bound")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(OSError):
        runtime._hash_path_nofollow(str(alias / "input.bin"))


def test_fd_baseline_detects_descriptor_above_1023(runtime, tmp_path):
    existing = set()
    for name in os.listdir("/dev/fd"):
        if name.isdecimal() and int(name) >= 3:
            try:
                fcntl.fcntl(int(name), fcntl.F_GETFD)
            except OSError:
                continue
            existing.add(int(name))
    base = os.open(tmp_path / "fd-source", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    high = fcntl.fcntl(base, fcntl.F_DUPFD, 2048)
    try:
        assert high >= 2048
        with pytest.raises(runtime.GateError, match="unexpected inherited descriptors"):
            runtime._require_fd_baseline(frozenset(existing | {base}))
        runtime._require_fd_baseline(frozenset(existing | {base, high}))
    finally:
        os.close(high)
        os.close(base)


def test_hardlinked_receipt_rejected(runtime, tmp_path):
    root = tmp_path / "root"
    root.mkdir(mode=0o700)
    path = root / "receipt.json"
    path.write_bytes(b"{}\n")
    path.chmod(0o600)
    os.link(path, root / "second-link")
    fd, _ = runtime._open_root(str(root))
    try:
        with pytest.raises(runtime.GateError):
            runtime._read_receipt_at(fd, "receipt.json", schema="x")
    finally:
        os.close(fd)


def test_write_all_survives_short_local_writes(runtime, monkeypatch, tmp_path):
    path = tmp_path / "sink"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    original = runtime.os.write

    def one_byte(target, data):
        return original(target, data[:1])

    monkeypatch.setattr(runtime.os, "write", one_byte)
    try:
        runtime._write_all(fd, b"abcdef")
        os.fsync(fd)
    finally:
        os.close(fd)
    assert path.read_bytes() == b"abcdef"


def test_all_pre_gate_mutants_make_zero_operational_calls(runtime, monkeypatch):
    calls: list[str] = []

    def forbidden(*args, **kwargs):
        calls.append("operational")
        raise AssertionError("pre-gate mutant reached operational call")

    monkeypatch.setattr(runtime.socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(runtime.socket, "socket", forbidden)
    monkeypatch.setattr(runtime.ssl, "SSLContext", forbidden)
    monkeypatch.setattr(runtime.os, "fork", forbidden)
    for root, row in [("relative", 0), ("/private/tmp/nonexistent", 0), ("/private/tmp/nonexistent", 1)]:
        with pytest.raises(runtime.GateError):
            runtime.attempt(root, row)
    assert calls == []


def test_ast_has_one_resolver_socket_context_and_no_destructive_paths(runtime):
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]

    def dotted(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return dotted(node.value) + "." + node.attr
        return ""

    names = [dotted(call.func) for call in calls]
    assert names.count("socket.getaddrinfo") == 1
    assert names.count("socket.socket") == 1
    assert names.count("ssl.SSLContext") == 1
    assert names.count("os.fork") == 1
    assert not set(names) & {
        "os.remove",
        "os.unlink",
        "os.rename",
        "os.replace",
        "shutil.rmtree",
        "urllib.request.urlopen",
        "requests.get",
    }
    attempt_source = inspect.getsource(runtime.attempt)
    assert attempt_source.index("_exclusive_canonical_at(rowfd, \"intent.json\"") < attempt_source.index(
        "_perform_spent_attempt("
    )
    assert "row directory already exists; attempt cannot start or retry" in attempt_source
    assert "spec_from_file_location" not in source
    assert "exec_module" not in source
    assert ".proposal.json" not in source
    assert "range(3, 1024)" not in source


def test_production_guard_binds_exact_original_argv_and_python_flags(runtime):
    guard = inspect.getsource(runtime._require_production_process)
    manifest = inspect.getsource(runtime._runtime_manifest)
    assert "sys.orig_argv != expected_original_argv" in guard
    assert guard.count("_require_exact_python_runtime_flags()") == 1
    assert manifest.count("_require_exact_python_runtime_flags()") == 1
    assert runtime.EXPECTED_PYTHON_FLAGS == {
        "bytes_warning": 0,
        "debug": 0,
        "dev_mode": False,
        "dont_write_bytecode": 1,
        "hash_randomization": 1,
        "ignore_environment": 1,
        "inspect": 0,
        "int_max_str_digits": 4300,
        "interactive": 0,
        "isolated": 1,
        "no_site": 1,
        "no_user_site": 1,
        "optimize": 0,
        "quiet": 0,
        "safe_path": True,
        "utf8_mode": 1,
        "verbose": 0,
        "warn_default_encoding": 0,
    }


def test_registrar_rosters_make_identity_and_time_nonclaims_explicit(runtime):
    assert {
        "reviewer_identity_externally_authenticated",
        "created_time_externally_attested",
    }.issubset(runtime.PACKAGE_LOCK_KEYS)
    assert {
        "authority_identity_externally_authenticated",
        "created_time_externally_attested",
    }.issubset(runtime.PREFLIGHT_AUTHORITY_KEYS)
    assert {
        "reviewer_identity_externally_authenticated",
        "created_time_externally_attested",
    }.issubset(runtime.INDEPENDENT_GO_KEYS)
    assert {
        "authority_identity_externally_authenticated",
        "created_time_externally_attested",
        "expiry_time_externally_attested",
    }.issubset(runtime.ROW_AUTHORITY_KEYS)
    source = SOURCE.read_text(encoding="utf-8")
    assert "executing_image_one_open_attestation_claimed" in source
    assert "registrar_identity_and_time_are_caller_assertions" in source


def test_deep_canonical_input_fails_closed_as_gate_error(runtime):
    raw = b"[" * 1500 + b"0" + b"]" * 1500
    with pytest.raises(runtime.GateError, match="parse failure"):
        runtime._parse_nonself_canonical(raw, "hostile")


def _sidecar(runtime, path, basename):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    st = os.fstat(fd)
    return runtime.Sidecar(basename, fd, st, st.st_dev, hashlib.sha256())


def test_receive_exception_retains_pending_head_exactly_once(runtime, tmp_path):
    class FakeTLS:
        def __init__(self):
            self.events = [b"HTTP/1.1 200 OK\r\nContent-T", OSError("cut")]

        def settimeout(self, _value):
            return None

        def recv(self, _size):
            event = self.events.pop(0)
            if isinstance(event, BaseException):
                raise event
            return event

    head = _sidecar(runtime, tmp_path / "head", "response-head.raw")
    body = _sidecar(runtime, tmp_path / "body", "transfer-body.raw")
    overflow = _sidecar(runtime, tmp_path / "overflow", "overflow-witness.raw")
    expected = b"HTTP/1.1 200 OK\r\nContent-T"
    try:
        got_head, got_body, overflow_kind, error = runtime._recv_exact_response(
            FakeTLS(), head, body, overflow, time.monotonic() + 2.0
        )
        assert got_head == expected
        assert got_body == b""
        assert overflow_kind is None
        assert error.startswith("OSError: cut")
        os.fsync(head.fd)
    finally:
        os.close(head.fd)
        os.close(body.fd)
        os.close(overflow.fd)
    assert (tmp_path / "head").read_bytes() == expected


def test_sidecar_verification_detects_same_inode_byte_mutation(runtime, tmp_path):
    path = tmp_path / "sidecar"
    fd = os.open(path, runtime.SIDECAR_CREATE_FLAGS, 0o600)
    st = os.fstat(fd)
    sidecar = runtime.Sidecar("request.raw", fd, st, st.st_dev, hashlib.sha256())
    try:
        sidecar.write(b"abc", 3)
        sidecar.verify_current_bytes()
        os.pwrite(fd, b"z", 0)
        with pytest.raises(runtime.CustodyError, match="byte custody mismatch"):
            sidecar.verify_current_bytes()
    finally:
        os.close(fd)


@pytest.mark.parametrize(
    "failure,message,overflow,transport,framing,framing_complete,expected",
    [
        ("PROTOCOL_VIOLATION", "multiple Content-Length forbidden", None, "cut", None, False, "PROTOCOL_VIOLATION"),
        ("PROTOCOL_VIOLATION", "EOF before complete response head", None, "cut", None, False, "TRANSPORT_FAILURE"),
        ("PROTOCOL_VIOLATION", "incomplete chunked body", "BODY", None, "CHUNKED", False, "TRANSPORT_OR_CONTENT_NO_GO"),
        ("SCOPE_VIOLATION", "forbidden response header: location", None, "cut", "CONTENT_LENGTH", True, "SCOPE_VIOLATION"),
        (None, None, "BODY", None, "CONTENT_LENGTH", True, "PROTOCOL_VIOLATION"),
    ],
)
def test_receive_terminal_precedence(
    runtime,
    failure,
    message,
    overflow,
    transport,
    framing,
    framing_complete,
    expected,
):
    qualified = {
        "accepted": False,
        "failure_code": failure,
        "parent_terminal_state": "before",
        "parent_parser_error_text": message,
        "diagnostics": {"body_truncated": False},
        "body_truncated": False,
        "framing": framing,
        "framing_complete": framing_complete,
    }
    runtime._apply_receive_terminal_precedence(qualified, overflow, transport)
    assert qualified["failure_code"] == expected


def _manifest_with_digest(runtime, **values):
    manifest = {
        "schema_version": "heterodiff-solo-block2-loaded-runtime-manifest-v3",
        **values,
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        runtime._canonical_bytes(manifest)
    ).hexdigest()
    return manifest


def test_mac_version_is_fully_json_native(runtime, monkeypatch):
    monkeypatch.setattr(
        runtime.platform,
        "mac_ver",
        lambda: ("15.6", ("15", "6", "0"), "arm64"),
    )
    value = runtime._normalized_mac_version()
    assert value == ["15.6", ["15", "6", "0"], "arm64"]
    assert type(value) is list
    assert type(value[1]) is list
    assert json.loads(json.dumps(value)) == value


def test_manifest_json_round_trip_does_not_false_hold(runtime, monkeypatch):
    current = _manifest_with_digest(
        runtime,
        mac_version=["15.6", ["15", "6", "0"], "arm64"],
        nested={"alpha": [1, 2], "beta": {"enabled": False}},
    )
    admitted = json.loads(json.dumps(current))
    monkeypatch.setattr(runtime, "_runtime_manifest", lambda *_args: current)
    runtime._revalidate_runtime_immediately_before_reservation(
        "/nonoperational/read-only-test-root", object(),
        {
            "runtime_manifest": admitted,
            "runtime_manifest_sha256": admitted["manifest_sha256"],
        },
    )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value["mac_version"][1].__setitem__(1, "7"),
        lambda value: value["mac_version"][1].reverse(),
        lambda value: value["mac_version"][1].append("extra"),
        lambda value: value.__setitem__("mac_version", "15.6"),
        lambda value: value["nested"].__setitem__("alpha", [1, float("nan")]),
        lambda value: value["nested"].__setitem__("alpha", {1, 2}),
    ],
)
def test_manifest_true_or_non_json_drift_fails_before_reservation(
    runtime, monkeypatch, mutator
):
    admitted = _manifest_with_digest(
        runtime,
        mac_version=["15.6", ["15", "6", "0"], "arm64"],
        nested={"alpha": [1, 2], "beta": {"enabled": False}},
    )
    current = json.loads(json.dumps(admitted))
    mutator(current)
    if isinstance(current.get("nested", {}).get("alpha"), list) and not any(
        isinstance(item, float) and item != item
        for item in current.get("nested", {}).get("alpha", [])
    ):
        payload = dict(current)
        payload.pop("manifest_sha256", None)
        current["manifest_sha256"] = hashlib.sha256(
            runtime._canonical_bytes(payload)
        ).hexdigest()
    monkeypatch.setattr(runtime, "_runtime_manifest", lambda *_args: current)
    with pytest.raises((runtime.GateError, TypeError, ValueError)):
        runtime._revalidate_runtime_immediately_before_reservation(
            "/nonoperational/read-only-test-root",
            object(),
            {
                "runtime_manifest": admitted,
                "runtime_manifest_sha256": admitted["manifest_sha256"],
            },
        )


def test_manifest_dict_key_order_is_semantically_stable(runtime, monkeypatch):
    current = _manifest_with_digest(
        runtime,
        mac_version=["15.6", ["15", "6", "0"], "arm64"],
        nested={"alpha": [1, 2], "beta": {"enabled": False}},
    )
    admitted = dict(reversed(list(current.items())))
    monkeypatch.setattr(runtime, "_runtime_manifest", lambda *_args: current)
    runtime._revalidate_runtime_immediately_before_reservation(
        "/nonoperational/read-only-test-root",
        object(),
        {
            "runtime_manifest": admitted,
            "runtime_manifest_sha256": admitted["manifest_sha256"],
        },
    )


def test_v3_paths_are_additive_and_prior_roots_are_not_reused(runtime):
    assert runtime.SCHEMA_VERSION.endswith("-v3")
    assert runtime.MACHINE_RELATIVE_PATH.endswith("closure_v3.json")
    assert runtime.SOURCE_RELATIVE_PATH.endswith("executor_v3.py")
    assert (SOURCE.parent / "solo_block2_runtime_custody_executor_v1.py").is_file()
    v1_root = (
        ROOT
        / "research"
        / "custody"
        / "solo_block2_public_documentation_runtime_v1"
    )
    st = os.stat(v1_root, follow_symlinks=False)
    assert stat.S_ISDIR(st.st_mode)
    assert stat.S_IMODE(st.st_mode) == 0o700
    assert {entry.name for entry in v1_root.iterdir()} == {
        "package-lock.json",
        "preflight-authority.json",
        "runtime-preflight.json",
        "row0-independent-go.json",
        "row0-authority.json",
    }
    assert not any(entry.name.startswith("row0-") and entry.is_dir() for entry in v1_root.iterdir())
    v2_root = (
        ROOT
        / "research"
        / "custody"
        / "solo_block2_public_documentation_runtime_v2"
    )
    v2_st = os.stat(v2_root, follow_symlinks=False)
    assert stat.S_ISDIR(v2_st.st_mode)
    assert stat.S_IMODE(v2_st.st_mode) == 0o700
    assert v2_st.st_ino == 66956470
    assert {entry.name for entry in v2_root.iterdir()} == {
        "package-lock.json",
        "preflight-authority.json",
        "runtime-preflight.json",
        "row0-independent-go.json",
        "row0-authority.json",
        "row0-physionet-root-v1",
    }
    assert not (
        ROOT
        / "research"
        / "custody"
        / "solo_block2_public_documentation_runtime_v3"
    ).exists()
