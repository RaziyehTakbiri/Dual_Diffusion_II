"""Hostile offline qualification for the dormant Solo Block 2 simulator."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from heterodiff.artifacts import (
    solo_block2_public_documentation_reconnaissance_executor_v2 as subject,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / subject.EXECUTOR_RELATIVE_PATH


def _http_response(
    body: bytes,
    *,
    headers: list[tuple[str, str]] | None = None,
    status: str = "200 OK",
) -> bytes:
    supplied = (
        [("Content-Type", "text/html; charset=utf-8")]
        if headers is None
        else headers
    )
    lines = [f"HTTP/1.1 {status}"] + [f"{key}: {value}" for key, value in supplied]
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body


def _content_length_success() -> bytes:
    body = (
        b"<!doctype html><html><title>Official root</title>"
        b"<body>public documentation</body></html>"
    )
    return _http_response(
        body,
        headers=[
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Connection", "close"),
        ],
    )


def _chunked_success() -> tuple[bytes, bytes]:
    first = b"<!doctype html><html><title>Official root</title>"
    second = b"<body>public documentation</body></html>"
    decoded = first + second
    encoded = (
        f"{len(first):X}\r\n".encode("ascii")
        + first
        + b"\r\n"
        + f"{len(second):X}\r\n".encode("ascii")
        + second
        + b"\r\n0\r\n\r\n"
    )
    return (
        _http_response(
            encoded,
            headers=[
                ("Content-Type", "text/html"),
                ("Transfer-Encoding", "chunked"),
                ("Connection", "close"),
            ],
        ),
        decoded,
    )


def _transcript(
    row: int = 0,
    *,
    raw_response: bytes | None = None,
    response_chunks: tuple[bytes, ...] | None = None,
    failure_stage: str | None = None,
    tls_version: str = "TLSv1.3",
    alpn: str = "http/1.1",
) -> subject.InertTranscript:
    operation = subject.operation_spec(row)
    offset = 0 if row == 0 else 5
    stamp = lambda second: f"2030-01-01T00:00:{second + offset:02d}Z"
    connect_failure = failure_stage == "CONNECT_FAILURE"
    policy_valid = tls_version in {"TLSv1.2", "TLSv1.3"} and alpn == "http/1.1"
    send_event = not connect_failure and (
        failure_stage == "SEND_FAILURE" or policy_valid
    )
    if raw_response is None:
        raw_response = _content_length_success()
    if response_chunks is None:
        response_chunks = (raw_response, b"")
    retained_chunks = response_chunks if send_event and failure_stage is None else ()
    return subject.InertTranscript(
        intent_utc=stamp(5),
        started_utc=stamp(6),
        finished_utc=stamp(7),
        simulated_resolver_host=operation["host"],
        simulated_resolver_port=443,
        simulated_resolver_results=(
            "192.0.2.10:443",
            "[2001:db8::10]:443",
        ),
        simulated_selected_address="192.0.2.10:443",
        simulated_socket_instance_count=1,
        simulated_connect_attempt_count=1,
        simulated_tls_wrap_count=0 if connect_failure else 1,
        simulated_send_attempt_count=1 if send_event else 0,
        simulated_emitted_request_bytes=(
            subject.exact_request_bytes(row) if send_event else None
        ),
        supplied_tls_version=None if connect_failure else tls_version,
        supplied_alpn=None if connect_failure else alpn,
        supplied_cipher_name=None if connect_failure else "TLS_AES_256_GCM_SHA384",
        supplied_cipher_protocol=None if connect_failure else "TLSv1.3",
        supplied_cipher_bits=None if connect_failure else 256,
        supplied_peer_certificate_bytes=(
            None if connect_failure else b"inert-supplied-der-certificate"
        ),
        response_chunks=retained_chunks,
        injected_failure_stage=failure_stage,
    )


def _clone_record(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value))


def _reseal(value: dict[str, Any]) -> dict[str, Any]:
    result = _clone_record(value)
    result["record_sha256"] = None
    result["record_sha256"] = subject._self_digest(result)
    return result


def test_contract_is_dormant_exact_two_operation_and_zero_effect() -> None:
    contract = subject.executor_contract()
    assert contract["package_role"] == "DORMANT_TRANSCRIPT_SIMULATOR"
    assert [item["url"] for item in contract["operation_roster"]] == [
        "https://physionet.org/content/challenge-2012/1.0.0/",
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
    ]
    assert contract["fetch_eligible"] is False
    assert contract["production_execution_entrypoint"] is False
    assert contract["general_url_input"] is False
    assert set(contract["effects"].values()) == {0}
    assert all(value is None for value in contract["operational_bindings"].values())


def test_exact_request_bytes_and_digests_are_frozen() -> None:
    expected = [
        (282, "ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449"),
        (287, "94271e586cfbec1d25c03754b1c4f47aadbd8e9459cffad6c050e0a80cf16b1b"),
    ]
    for row, (count, digest) in enumerate(expected):
        request = subject.exact_request_bytes(row)
        assert len(request) == count
        assert hashlib.sha256(request).hexdigest() == digest
        assert request.count(b"GET ") == 1
        assert request.endswith(b"Connection: close\r\n\r\n")
        assert b"Authorization:" not in request
        assert b"Cookie:" not in request
        assert b"Content-Length:" not in request


def test_source_ast_has_no_effectful_import_or_call_surface() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported_roots <= {
        "__future__",
        "datetime",
        "hashlib",
        "json",
        "re",
        "dataclasses",
        "typing",
    }
    banned_roots = {
        "os",
        "pathlib",
        "socket",
        "ssl",
        "subprocess",
        "urllib",
        "http",
        "requests",
        "httpx",
        "time",
        "random",
        "secrets",
    }
    assert imported_roots.isdisjoint(banned_roots)
    banned_calls = {
        "open",
        "write",
        "mkdir",
        "makedirs",
        "fsync",
        "socket",
        "getaddrinfo",
        "connect",
        "send",
        "sendall",
        "recv",
        "wrap_socket",
        "Popen",
        "run",
        "system",
        "urandom",
        "now",
        "utcnow",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node.func, ast.Attribute):
            assert node.func.attr not in banned_calls
    text = SOURCE.read_text(encoding="utf-8")
    assert "Callable" not in text
    assert "from typing import Protocol" not in text
    assert "create_connection" not in text
    assert "O_TRUNC" not in text


def test_public_api_has_no_path_url_or_callable_seam() -> None:
    assert not hasattr(subject, "execute_row")
    assert not hasattr(subject, "fresh_authority_text")
    assert not hasattr(subject, "inspect_local_environment")
    signatures = {
        name: inspect.signature(getattr(subject, name))
        for name in (
            "executor_contract",
            "custody_plan",
            "transcript_receipt",
            "qualify_row_from_inert_transcript",
        )
    }
    for signature in signatures.values():
        assert not {
            "path",
            "repo_root",
            "custody_root",
            "url",
            "resolver",
            "socket",
            "tls",
            "send",
            "recv",
        }.intersection(signature.parameters)


def test_public_calls_leave_workspace_snapshot_unchanged(tmp_path: Path) -> None:
    sentinel = tmp_path / "sentinel.bin"
    sentinel.write_bytes(b"unchanged")
    before = [(item.name, item.read_bytes()) for item in tmp_path.iterdir()]
    subject.executor_contract()
    subject.custody_plan(0)
    subject.transcript_receipt(0, _transcript())
    outcome = subject.qualify_row_from_inert_transcript(0, transcript=_transcript())
    after = [(item.name, item.read_bytes()) for item in tmp_path.iterdir()]
    assert before == after
    assert outcome["external_network_effect"] == 0


def test_custody_plan_is_explicitly_unmaterialized_and_unproved() -> None:
    plan = subject.custody_plan(0)
    assert plan["filesystem_materialized"] is False
    assert plan["dirfd_mechanics_implemented"] is False
    assert plan["exclusive_creation_qualified"] is False
    assert plan["nofollow_qualified"] is False
    assert plan["durability_qualified"] is False
    assert plan["filesystem_effect"] == 0
    assert plan["operational_row_directory_basename"] is None
    assert [item["role"] for item in plan["artifacts"]] == [
        "intent",
        "raw_request",
        "raw_response_head",
        "raw_transfer_body",
        "raw_metadata",
        "raw_stderr",
        "decoded_entity_body",
        "outcome",
    ]
    assert [item["logical_name"] for item in plan["artifacts"]] == [
        "row-000.intent.json",
        "row-000.raw-request.bin",
        "row-000.raw-response-head.bin",
        "row-000.raw-transfer-body.bin",
        "row-000.raw-metadata.bin",
        "row-000.raw-stderr.bin",
        "row-000.decoded-entity-body.bin",
        "row-000.outcome.json",
    ]
    assert all(
        item["future_create_flags"]
        == ["O_WRONLY", "O_CREAT", "O_EXCL", "O_NOFOLLOW"]
        for item in plan["artifacts"]
    )
    assert all(item["future_mode_octal"] == "0600" for item in plan["artifacts"])


def test_contract_and_custody_copies_are_detached() -> None:
    contract = subject.executor_contract()
    contract["effects"]["network_calls"] = 99
    assert subject.executor_contract()["effects"]["network_calls"] == 0
    plan = subject.custody_plan(0)
    plan["artifacts"][0]["future_mode_octal"] = "0777"
    assert subject.custody_plan(0)["artifacts"][0]["future_mode_octal"] == "0600"


def test_transcript_receipt_is_deterministic_and_chunk_addressed() -> None:
    transcript = _transcript(response_chunks=(b"alpha", b"beta", b""))
    first = subject.transcript_receipt(0, transcript)
    second = subject.transcript_receipt(0, transcript)
    assert first == second
    assert first["external_effect"] == 0
    assert first["inert_transcript_sha256"] == subject._sha256(
        subject._canonical_no_lf({key: value for key, value in first.items() if key != "inert_transcript_sha256"})
    )
    assert [item["raw_sha256"] for item in first["response_chunks"]] == [
        subject._sha256(b"alpha"),
        subject._sha256(b"beta"),
        subject._sha256(b""),
    ]


@pytest.mark.parametrize("row", [True, False, -1, 2, 0.0, "0", None])
def test_row_ordinal_type_and_range_are_strict(row: Any) -> None:
    with pytest.raises(subject.AdmissionError):
        subject.qualify_row_from_inert_transcript(row, transcript=_transcript())


def test_transcript_requires_exact_dataclass() -> None:
    with pytest.raises(subject.AdmissionError, match="exact InertTranscript"):
        subject.qualify_row_from_inert_transcript(0, transcript={})


@pytest.mark.parametrize(
    "field,value",
    [
        ("intent_utc", b"2030-01-01T00:00:05Z"),
        ("simulated_resolver_port", True),
        ("simulated_resolver_results", ["192.0.2.10:443"]),
        ("simulated_socket_instance_count", 1.0),
        ("simulated_emitted_request_bytes", bytearray(b"x")),
        ("supplied_cipher_bits", True),
        ("response_chunks", [b"x"]),
        ("injected_failure_stage", 1),
    ],
)
def test_transcript_field_types_are_strict(field: str, value: Any) -> None:
    transcript = dataclasses.replace(_transcript(), **{field: value})
    with pytest.raises(subject.AdmissionError):
        subject.qualify_row_from_inert_transcript(0, transcript=transcript)


def test_transcript_scalar_bounds_precede_comparison_and_hashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subject, "MAX_PLAIN_STRING_CODEPOINTS", 4)
    oversized_string = dataclasses.replace(
        _transcript(), simulated_resolver_host="abcde"
    )
    with pytest.raises(subject.AdmissionError, match="codepoint ceiling"):
        subject.qualify_row_from_inert_transcript(0, transcript=oversized_string)

    monkeypatch.setattr(subject, "MAX_PLAIN_STRING_CODEPOINTS", 262_144)
    invalid_utf8_string = dataclasses.replace(
        _transcript(), simulated_resolver_host="\ud800"
    )
    with pytest.raises(subject.AdmissionError, match="valid UTF-8"):
        subject.qualify_row_from_inert_transcript(0, transcript=invalid_utf8_string)

    oversized_integer = dataclasses.replace(
        _transcript(), simulated_connect_attempt_count=1 << 256
    )
    with pytest.raises(subject.AdmissionError, match="exact int"):
        subject.qualify_row_from_inert_transcript(0, transcript=oversized_integer)


def test_qualification_after_import_has_no_lazy_file_or_module_reads() -> None:
    assert ".strptime(" not in SOURCE.read_text(encoding="utf-8")
    observed: list[str] = []
    armed = [True]

    def audit_hook(event: str, _args: tuple[Any, ...]) -> None:
        if armed[0] and event in {"open", "import"}:
            observed.append(event)

    sys.addaudithook(audit_hook)
    try:
        outcome = subject.qualify_row_from_inert_transcript(
            0, transcript=_transcript()
        )
    finally:
        armed[0] = False
    assert outcome["inert_transcript_accepted"] is True
    assert observed == []


class _Explosive:
    def __init__(self) -> None:
        self.touched = False

    def _explode(self, *_args: Any, **_kwargs: Any) -> Any:
        self.touched = True
        raise AssertionError("caller protocol was invoked")

    __eq__ = _explode
    __iter__ = _explode
    __deepcopy__ = _explode
    __str__ = _explode
    __bytes__ = _explode
    __fspath__ = _explode


class _ExplosiveTuple(tuple[Any, ...]):
    def __new__(cls, values: tuple[Any, ...]) -> _ExplosiveTuple:
        value = super().__new__(cls, values)
        value.touched = False
        return value

    def _explode(self, *_args: Any, **_kwargs: Any) -> Any:
        self.touched = True
        raise AssertionError("tuple protocol was invoked")

    __len__ = _explode
    __iter__ = _explode


def test_malicious_transcript_value_is_rejected_without_protocol_invocation() -> None:
    explosive = _Explosive()
    transcript = dataclasses.replace(
        _transcript(), simulated_resolver_host=explosive
    )
    with pytest.raises(subject.AdmissionError, match="exact string"):
        subject.qualify_row_from_inert_transcript(0, transcript=transcript)
    assert explosive.touched is False


def test_container_type_precedes_length_and_element_access() -> None:
    hostile = _ExplosiveTuple((b"x",))
    with pytest.raises(subject.ProtocolError, match="exact bytes tuple"):
        subject._receive_response(hostile)
    assert hostile.touched is False

    transcript = dataclasses.replace(_transcript(), response_chunks=hostile)
    with pytest.raises(subject.AdmissionError, match="exact bytes tuple"):
        subject.qualify_row_from_inert_transcript(0, transcript=transcript)
    assert hostile.touched is False


def test_container_count_precedes_element_scan_for_public_transcript_inputs() -> None:
    explosive = _Explosive()
    over_count = (explosive,) * (subject.MAX_TRANSCRIPT_CHUNK_COUNT + 1)
    with pytest.raises(subject.ProtocolError, match="chunk count ceiling"):
        subject._receive_response(over_count)
    assert explosive.touched is False

    response_transcript = dataclasses.replace(
        _transcript(), response_chunks=over_count
    )
    with pytest.raises(subject.AdmissionError, match="chunk count ceiling"):
        subject.qualify_row_from_inert_transcript(
            0, transcript=response_transcript
        )
    assert explosive.touched is False

    resolver_transcript = dataclasses.replace(
        _transcript(), simulated_resolver_results=(explosive, explosive, explosive)
    )
    with pytest.raises(subject.AdmissionError, match="result count"):
        subject.qualify_row_from_inert_transcript(
            0, transcript=resolver_transcript
        )
    assert explosive.touched is False


def test_malicious_prior_value_is_rejected_without_protocol_invocation() -> None:
    row0_transcript = _transcript()
    prior = subject.qualify_row_from_inert_transcript(
        0, transcript=row0_transcript
    )
    explosive = _Explosive()
    prior["machine_raw_sha256"] = explosive
    with pytest.raises(subject.AdmissionError, match="plain data"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=row0_transcript,
            prior_outcome=prior,
        )
    assert explosive.touched is False


class _ArmableKey:
    def __init__(self) -> None:
        self.armed = False
        self.post_arm_calls = 0

    def __hash__(self) -> int:
        if self.armed:
            self.post_arm_calls += 1
            raise AssertionError("armed key hash invoked")
        return 7

    def __eq__(self, _other: Any) -> bool:
        if self.armed:
            self.post_arm_calls += 1
            raise AssertionError("armed key equality invoked")
        return False


def test_armed_hostile_prior_key_is_rejected_before_hash_or_equality() -> None:
    key = _ArmableKey()
    hostile_prior = {key: False}
    key.armed = True
    with pytest.raises(subject.AdmissionError, match="plain data"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=_transcript(),
            prior_outcome=hostile_prior,
        )
    assert key.post_arm_calls == 0


def _assert_nonplain_prior_is_deterministically_rejected(
    claimed_prior: dict[Any, Any],
) -> None:
    with pytest.raises(subject.AdmissionError, match="exact plain data"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=_transcript(),
            prior_outcome=claimed_prior,
        )


def test_cyclic_dict_and_list_priors_are_deterministically_rejected() -> None:
    cyclic_dict: dict[Any, Any] = {}
    cyclic_dict["self"] = cyclic_dict
    _assert_nonplain_prior_is_deterministically_rejected(cyclic_dict)

    cyclic_list: list[Any] = []
    cyclic_list.append(cyclic_list)
    _assert_nonplain_prior_is_deterministically_rejected({"cycle": cyclic_list})


def test_over_depth_prior_is_deterministically_rejected() -> None:
    deep: list[Any] = []
    cursor = deep
    for _ in range(subject.MAX_PLAIN_CLONE_DEPTH + 2):
        child: list[Any] = []
        cursor.append(child)
        cursor = child
    _assert_nonplain_prior_is_deterministically_rejected({"deep": deep})


def test_over_node_prior_is_deterministically_rejected() -> None:
    group_count = subject.MAX_PLAIN_CLONE_NODES // 9 + 1
    assert group_count < subject.MAX_PLAIN_CONTAINER_ITEMS
    many_nodes = [[None] * 8 for _ in range(group_count)]
    _assert_nonplain_prior_is_deterministically_rejected({"many": many_nodes})


def test_over_container_prior_is_deterministically_rejected() -> None:
    oversized = [None] * (subject.MAX_PLAIN_CONTAINER_ITEMS + 1)
    _assert_nonplain_prior_is_deterministically_rejected({"oversized": oversized})


def test_over_scalar_priors_are_deterministically_rejected() -> None:
    values = [
        "x" * (subject.MAX_PLAIN_STRING_CODEPOINTS + 1),
        b"x" * (subject.MAX_PLAIN_BYTES_LENGTH + 1),
        1 << subject.MAX_PLAIN_INTEGER_BITS,
        float("inf"),
        "\ud800",
    ]
    for value in values:
        _assert_nonplain_prior_is_deterministically_rejected({"value": value})


def test_content_length_success_parser_has_exact_offsets() -> None:
    result = subject._receive_response((_content_length_success(), b""))
    assert result.status_code == 200
    assert result.protocol == "HTTP/1.1"
    assert result.framing == "CONTENT_LENGTH"
    assert result.dechunk_complete is True
    assert result.rejection_substring_matches == []
    assert result.raw_status_start == 0
    assert result.raw_status_end_exclusive == result.raw_headers_start
    assert result.raw_headers_end_exclusive == len(result.raw_head)
    assert result.raw_body == result.decoded_body


def test_chunked_success_retains_raw_and_dechunks_separately() -> None:
    raw, decoded = _chunked_success()
    result = subject._receive_response((raw, b""))
    assert result.framing == "CHUNKED"
    assert result.transfer_encoding_header_count == 1
    assert result.transfer_encoding_raw_values == ["chunked"]
    assert result.transfer_encoding_normalized_values == ["chunked"]
    assert result.transfer_encoding_semantics_valid is True
    assert result.dechunk_complete is True
    assert result.raw_body.endswith(b"0\r\n\r\n")
    assert result.decoded_body == decoded
    assert result.raw_body != result.decoded_body


def test_connection_close_success_is_supported_only_from_supplied_eof() -> None:
    body = b"plain public documentation"
    result = subject._receive_response(
        (_http_response(body, headers=[("Content-Type", "text/plain")]), b"")
    )
    assert result.framing == "CONNECTION_CLOSE"
    assert result.raw_body == body
    assert result.decoded_body == body


def test_connection_close_without_explicit_terminal_eof_is_protocol_failure() -> None:
    assert subject.executor_contract()["response_predicates"][
        "connection_close_requires_exactly_one_final_inert_eof_event"
    ] is True
    body = b"plain public documentation"
    raw = _http_response(body, headers=[("Content-Type", "text/plain")])
    body_start = raw.index(b"\r\n\r\n") + 4
    with pytest.raises(subject.ProtocolError, match="explicit terminal inert EOF") as error:
        subject._receive_response((raw,))
    assert error.value.captured_head == raw[:body_start]
    assert error.value.captured_body == body
    assert error.value.evidence["framing"] == "CONNECTION_CLOSE"
    assert error.value.evidence["framing_complete"] is False

    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(response_chunks=(raw,))
    )
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert outcome["failure_code"] == "PROTOCOL_VIOLATION"
    assert outcome["framing_complete"] is False
    assert artifacts["raw_transfer_body"]["bytes"] == len(body)
    assert artifacts["raw_transfer_body"]["raw_sha256"] == subject._sha256(body)


def test_connection_close_duplicate_or_nonterminal_eof_is_protocol_failure() -> None:
    body = b"plain public documentation"
    raw = _http_response(body, headers=[("Content-Type", "text/plain")])
    body_start = raw.index(b"\r\n\r\n") + 4
    hostile_chunk_rosters = (
        (raw, b"", b""),
        (raw[:body_start], b"", body, b""),
    )
    for chunks in hostile_chunk_rosters:
        with pytest.raises(subject.ProtocolError, match="EOF marker must be terminal") as error:
            subject._receive_response(chunks)
        assert error.value.captured_head == raw[:body_start]
        assert error.value.captured_body == body


@pytest.mark.parametrize(
    "raw,error",
    [
        (b"HTTP/1.1 200 OK\nContent-Type: text/html\n\n<html></html>", subject.ProtocolError),
        (
            _http_response(
                b"x",
                headers=[
                    ("Content-Type", "text/plain"),
                    ("Content-Length", "1"),
                    ("Transfer-Encoding", "chunked"),
                ],
            ),
            subject.ProtocolError,
        ),
        (
            _http_response(
                b"ab",
                headers=[
                    ("Content-Type", "text/plain"),
                    ("Content-Length", "1"),
                    ("Content-Length", "1"),
                ],
            ),
            subject.ProtocolError,
        ),
        (
            _http_response(
                b"1\r\na\r\n",
                headers=[("Content-Type", "text/plain"), ("Transfer-Encoding", "chunked")],
            ),
            subject.ProtocolError,
        ),
        (
            _http_response(
                b"1;foo=bar\r\na\r\n0\r\n\r\n",
                headers=[("Content-Type", "text/plain"), ("Transfer-Encoding", "chunked")],
            ),
            subject.ProtocolError,
        ),
        (
            _http_response(
                b"1\r\na\r\n0\r\nX: y\r\n\r\n",
                headers=[("Content-Type", "text/plain"), ("Transfer-Encoding", "chunked")],
            ),
            subject.ProtocolError,
        ),
        (
            _http_response(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nsecond",
                headers=[("Content-Type", "text/plain")],
            ),
            subject.ProtocolError,
        ),
        (
            b"HTTP/1.1 100 Continue\r\n\r\nHTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nx",
            subject.ProtocolError,
        ),
    ],
)
def test_malformed_ambiguous_interim_or_multiple_framing_rejected(
    raw: bytes, error: type[Exception]
) -> None:
    with pytest.raises(error):
        subject._receive_response((raw, b""))


@pytest.mark.parametrize("status", ["200 OK", "500 Internal Server Error"])
def test_protocol_precedence_over_scope_and_status(status: str) -> None:
    raw = _http_response(
        b"x",
        status=status,
        headers=[
            ("Location", "https://example.invalid/"),
            ("Content-Type", "text/plain"),
            ("Content-Length", "1"),
            ("Content-Length", "1"),
        ],
    )
    with pytest.raises(subject.ProtocolError, match="multiple Content-Length"):
        subject._receive_response((raw, b""))


def test_scope_precedence_over_non_200_content_decision() -> None:
    raw = _http_response(
        b"error",
        status="500 Internal Server Error",
        headers=[
            ("Location", "https://example.invalid/"),
            ("Content-Type", "text/plain"),
        ],
    )
    with pytest.raises(subject.ScopeError, match="location"):
        subject._receive_response((raw, b""))


@pytest.mark.parametrize(
    "raw",
    [
        _http_response(
            b"ab",
            headers=[
                ("Location", "https://example.invalid/"),
                ("Content-Type", "text/plain"),
                ("Content-Length", "1"),
            ],
        ),
        _http_response(
            b"1;bad=x\r\na\r\n0\r\n\r\n",
            headers=[
                ("Location", "https://example.invalid/"),
                ("Content-Type", "text/plain"),
                ("Transfer-Encoding", "chunked"),
            ],
        ),
        _http_response(
            b"ab",
            status="500 Internal Server Error",
            headers=[("Content-Type", "text/plain"), ("Content-Length", "1")],
        ),
        _http_response(
            b"a",
            headers=[
                ("Content-Disposition", "inline"),
                ("Content-Type", "text/plain"),
                ("Content-Length", "2"),
            ],
        ),
        _http_response(
            b"1\r\na\r\n",
            headers=[
                ("Content-Type", "text/html"),
                ("Content-Type", "text/plain"),
                ("Transfer-Encoding", "chunked"),
            ],
        ),
        _http_response(
            b"1\r\na\r\n0\r\nX: y\r\n\r\n",
            status="500 Internal Server Error",
            headers=[
                ("Content-Type", "text/plain"),
                ("Transfer-Encoding", "chunked"),
            ],
        ),
        _http_response(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nx",
            headers=[
                ("Location", "https://example.invalid/"),
                ("Content-Type", "text/plain"),
            ],
        ),
    ],
)
def test_body_framing_protocol_precedes_scope_status_and_content(raw: bytes) -> None:
    body_start = raw.index(b"\r\n\r\n") + 4
    with pytest.raises(subject.ProtocolError) as error:
        subject._receive_response((raw, b""))
    assert error.value.captured_head == raw[:body_start]
    assert error.value.captured_body == raw[body_start:]
    assert error.value.evidence["header_diagnostics_complete"] is True
    assert error.value.evidence["framing_complete"] is False
    assert error.value.evidence["decoded_entity_body_receipt_complete"] is False
    assert error.value.evidence["body_truncated"] is False

    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    assert outcome["failure_code"] == "PROTOCOL_VIOLATION"
    assert outcome["body_truncated"] is False


def test_late_scope_and_status_failures_preserve_complete_raw_body_custody() -> None:
    body = b"public body"
    cases = [
        _http_response(
            body,
            headers=[
                ("Location", "https://example.invalid/"),
                ("Content-Type", "text/plain"),
                ("Content-Length", str(len(body))),
            ],
        ),
        _http_response(
            body,
            status="500 Internal Server Error",
            headers=[
                ("Content-Type", "text/plain"),
                ("Content-Length", str(len(body))),
            ],
        ),
    ]
    for ordinal, raw in enumerate(cases):
        body_start = raw.index(b"\r\n\r\n") + 4
        outcome = subject.qualify_row_from_inert_transcript(
            0, transcript=_transcript(raw_response=raw)
        )
        artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
        assert artifacts["raw_response_head"]["bytes"] == body_start
        assert artifacts["raw_response_head"]["raw_sha256"] == subject._sha256(
            raw[:body_start]
        )
        assert artifacts["raw_transfer_body"]["bytes"] == len(body)
        assert artifacts["raw_transfer_body"]["raw_sha256"] == subject._sha256(body)
        assert artifacts["decoded_entity_body"]["bytes"] == len(body)
        assert artifacts["decoded_entity_body"]["raw_sha256"] == subject._sha256(body)
        assert outcome["header_diagnostics_complete"] is True
        assert outcome["framing_complete"] is True
        assert outcome["decoded_entity_body_receipt_complete"] is True
        assert outcome["body_truncated"] is False
        assert outcome["body_utf8_valid"] is (ordinal == 1)
        assert outcome["location_header_count"] == (1 if ordinal == 0 else 0)


def test_head_stage_protocol_rejection_preserves_same_chunk_body_custody() -> None:
    body = b"ab"
    raw = _http_response(
        body,
        headers=[
            ("Content-Type", "text/plain"),
            ("Content-Length", "2"),
            ("Content-Length", "2"),
        ],
    )
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert outcome["failure_code"] == "PROTOCOL_VIOLATION"
    assert outcome["header_diagnostics_complete"] is False
    assert outcome["content_type_header_count"] is None
    assert outcome["content_type_raw_values"] == []
    assert outcome["framing_complete"] is False
    assert outcome["decoded_entity_body_receipt_complete"] is False
    assert artifacts["raw_transfer_body"]["bytes"] == len(body)
    assert artifacts["raw_transfer_body"]["raw_sha256"] == subject._sha256(body)


def test_scope_rejection_drains_and_preserves_all_supplied_body_chunks() -> None:
    body = b"alpha-beta-gamma"
    raw = _http_response(
        body,
        headers=[
            ("Location", "https://example.invalid/"),
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ],
    )
    body_start = raw.index(b"\r\n\r\n") + 4
    chunks = (
        raw[: body_start + 2],
        raw[body_start + 2 : body_start + 7],
        raw[body_start + 7 :],
        b"",
    )
    with pytest.raises(subject.ScopeError) as error:
        subject._receive_response(chunks)
    assert error.value.captured_head == raw[:body_start]
    assert error.value.captured_body == body
    assert error.value.decoded_body == body

    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(response_chunks=chunks)
    )
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert artifacts["raw_transfer_body"]["bytes"] == len(body)
    assert artifacts["raw_transfer_body"]["raw_sha256"] == subject._sha256(body)
    assert artifacts["decoded_entity_body"]["bytes"] == len(body)
    assert artifacts["decoded_entity_body"]["raw_sha256"] == subject._sha256(body)


@pytest.mark.parametrize(
    "headers,error",
    [
        ([], subject.ScopeError),
        ([('Content-Type', 'text/html'), ('Content-Type', 'text/plain')], subject.ScopeError),
        ([('Content-Type', 'text/html, text/plain')], subject.ScopeError),
        ([('Content-Type', 'application/octet-stream')], subject.ScopeError),
        ([('Content-Type', 'text/html'), ('Content-Encoding', 'gzip')], subject.ScopeError),
        ([('Content-Type', 'text/html'), ('Content-Encoding', 'identity'), ('Content-Encoding', 'identity')], subject.ScopeError),
        ([('Content-Type', 'text/html'), ('Content-Disposition', 'inline')], subject.ScopeError),
        ([('Content-Type', 'text/html'), ('Location', 'https://example.invalid/')], subject.ScopeError),
        ([('Content-Type', 'text/html'), ('Set-Cookie', 'x=y')], subject.ScopeError),
        ([('Content-Type', 'text/html'), ('Connection', 'keep-alive')], subject.ScopeError),
    ],
)
def test_response_header_scope_is_fail_closed(
    headers: list[tuple[str, str]], error: type[Exception]
) -> None:
    with pytest.raises(error):
        subject._receive_response(
            (_http_response(b"<html>public</html>", headers=headers), b"")
        )


@pytest.mark.parametrize(
    "body",
    [
        b"<html><input type=\"password\"></html>",
        b"<html>CAPTCHA verify you are human</html>",
        b"<html><title>Access denied</title></html>",
        b"<html>internal server error</html>",
        b"<html>consent required</html>",
    ],
)
def test_login_consent_challenge_robot_and_error_pages_rejected(body: bytes) -> None:
    with pytest.raises(subject.ScopeError):
        subject._receive_response((_http_response(body), b""))


@pytest.mark.parametrize(
    "body,marker",
    [
        (b"<html>Enable\n\tJavaScript   and Cookies</html>", "enable javascript and cookies"),
        (b"<html>CLOUDFLARE\r\nRAY ID</html>", "cloudflare ray id"),
        (b"<html>LOGIN\tREQUIRED</html>", "login required"),
        (b"<html>SIGN\nIN</html>", "sign in"),
    ],
)
def test_unicode_casefold_and_ascii_whitespace_collapse_marker_matching(
    body: bytes, marker: str
) -> None:
    with pytest.raises(subject.ScopeError) as error:
        subject._receive_response((_http_response(body), b""))
    assert marker in error.value.evidence["rejection_substring_matches"]
    allowed = set(subject.executor_contract()["response_predicates"]["rejection_substrings"])
    assert set(error.value.evidence["rejection_substring_matches"]) <= allowed


@pytest.mark.parametrize(
    "body",
    [
        bytes.fromhex("1f8b") + b"archive",
        bytes.fromhex("504b0304") + b"archive",
        bytes.fromhex("53514c69746520666f726d6174203300") + b"data",
        b"\x80\x04pickle",
    ],
)
def test_archive_and_data_magic_rejected(body: bytes) -> None:
    with pytest.raises(subject.ScopeError):
        subject._receive_response(
            (_http_response(body, headers=[("Content-Type", "text/plain")]), b"")
        )


def test_magic_and_title_diagnostics_never_pollute_page_marker_matches() -> None:
    magic = bytes.fromhex("504b0304") + b"archive"
    with pytest.raises(subject.ScopeError) as magic_error:
        subject._receive_response(
            (_http_response(magic, headers=[("Content-Type", "text/plain")]), b"")
        )
    assert magic_error.value.evidence["rejection_substring_matches"] == []
    assert magic_error.value.evidence["forbidden_magic_prefix_matches"] == ["504b0304"]
    assert magic_error.value.evidence["title_classifier_matches"] == []

    with pytest.raises(subject.ScopeError) as title_error:
        subject._receive_response((_http_response(b"<html><title>Login</title></html>"), b""))
    assert title_error.value.evidence["rejection_substring_matches"] == []
    assert title_error.value.evidence["forbidden_magic_prefix_matches"] == []
    assert title_error.value.evidence["title_classifier_matches"] == ["login"]


def test_title_classifier_uses_bounded_linear_scans_not_backtracking_regex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert r"<title(?:\s[^>]*)?>(.*?)</title\s*>" not in source

    def forbidden_regex_search(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("title classification must not call regex search")

    monkeypatch.setattr(subject.re, "search", forbidden_regex_search)
    repeated_unclosed = b"<html>" + (b"<title>" * 10_000) + b"public</html>"
    evidence = subject._validate_body(repeated_unclosed, "text/html")
    assert evidence["title_classifier_matches"] == []

    with pytest.raises(subject.ScopeError) as error:
        subject._validate_body(
            b"<html><title data-kind='root'>Login</title \t></html>",
            "text/html",
        )
    assert error.value.evidence["title_classifier_matches"] == ["login"]


def test_exact_content_length_and_eof_are_required() -> None:
    body = b"<html>short</html>"
    with pytest.raises(subject.ProtocolError, match="incomplete"):
        subject._receive_response(
            (
                _http_response(
                    body,
                    headers=[
                        ("Content-Type", "text/html"),
                        ("Content-Length", str(len(body) + 1)),
                    ],
                ),
                b"",
            )
        )
    with pytest.raises(subject.ProtocolError, match="beyond Content-Length"):
        subject._receive_response(
            (
                _http_response(
                    body + b"x",
                    headers=[
                        ("Content-Type", "text/html"),
                        ("Content-Length", str(len(body))),
                    ],
                ),
                b"",
            )
        )


def test_extreme_content_length_is_runtime_independent_protocol_failure() -> None:
    body = b"x"
    raw = _http_response(
        body,
        headers=[
            ("Content-Type", "text/plain"),
            ("Content-Length", "1" * 5_000),
        ],
    )
    body_start = raw.index(b"\r\n\r\n") + 4
    with pytest.raises(subject.ProtocolError, match="frozen body ceiling") as error:
        subject._receive_response((raw, b""))
    assert error.value.captured_head == raw[:body_start]
    assert error.value.captured_body == body

    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert outcome["failure_code"] == "PROTOCOL_VIOLATION"
    assert artifacts["raw_transfer_body"]["bytes"] == 1
    assert artifacts["raw_transfer_body"]["raw_sha256"] == subject._sha256(body)


def test_content_length_decimal_boundary_is_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subject, "MAX_ENCODED_BODY_BYTES", 10)
    accepted_body = b"0123456789"
    accepted = _http_response(
        accepted_body,
        headers=[("Content-Type", "text/plain"), ("Content-Length", "10")],
    )
    assert subject._receive_response((accepted, b"")).decoded_body == accepted_body

    oversized_body = b"01234567890"
    oversized = _http_response(
        oversized_body,
        headers=[("Content-Type", "text/plain"), ("Content-Length", "11")],
    )
    with pytest.raises(subject.ProtocolError, match="frozen body ceiling") as error:
        subject._receive_response((oversized, b""))
    assert error.value.captured_body == oversized_body[:10]

    leading_zero = _http_response(
        b"",
        headers=[("Content-Type", "text/plain"), ("Content-Length", "00")],
    )
    with pytest.raises(subject.ProtocolError, match="invalid Content-Length"):
        subject._receive_response((leading_zero, b""))


def test_inert_eof_marker_must_be_terminal() -> None:
    with pytest.raises(subject.ProtocolError, match="EOF marker"):
        subject._receive_response((b"", _content_length_success()))


def test_transcript_total_and_chunk_count_caps_are_pre_hash_admission_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subject, "MAX_TRANSCRIPT_CHUNK_COUNT", 1)
    with pytest.raises(subject.AdmissionError, match="chunk count ceiling"):
        subject.transcript_receipt(
            0, _transcript(response_chunks=(b"a", b"b"))
        )
    with pytest.raises(subject.ProtocolError, match="chunk count ceiling"):
        subject._receive_response((b"a", b"b"))

    monkeypatch.setattr(subject, "MAX_TRANSCRIPT_CHUNK_COUNT", 4_096)
    monkeypatch.setattr(subject, "MAX_TOTAL_RESPONSE_BYTES", 4)
    with pytest.raises(subject.AdmissionError, match="total byte ceiling"):
        subject.transcript_receipt(
            0, _transcript(response_chunks=(b"abc", b"de"))
        )


def test_status_header_and_body_caps_retain_exact_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subject, "MAX_STATUS_BYTES", 8)
    with pytest.raises(subject.ProtocolError, match="status byte ceiling") as status_error:
        subject._receive_response((b"HTTP/1.1 200 OK\r\n", b""))
    assert len(status_error.value.captured_head) == 8

    monkeypatch.setattr(subject, "MAX_STATUS_BYTES", 8_192)
    monkeypatch.setattr(subject, "MAX_HEADER_BYTES", 16)
    with pytest.raises(subject.ProtocolError, match="header byte ceiling") as header_error:
        subject._receive_response(
            (b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nX-Long: abcdef\r\n\r\nx", b"")
        )
    status_end = len(b"HTTP/1.1 200 OK\r\n")
    assert len(header_error.value.captured_head) == status_end + 16

    monkeypatch.setattr(subject, "MAX_HEADER_BYTES", 131_072)
    monkeypatch.setattr(subject, "MAX_ENCODED_BODY_BYTES", 10)
    with pytest.raises(subject.ContentError, match="encoded body byte ceiling") as body_error:
        oversized_raw = _http_response(
            b"01234567890", headers=[("Content-Type", "text/plain")]
        )
        subject._receive_response((oversized_raw, b""))
    assert len(body_error.value.captured_body) == 10
    assert body_error.value.evidence["body_truncated"] is True

    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=oversized_raw)
    )
    assert outcome["body_truncated"] is True
    assert outcome["framing_complete"] is True
    assert outcome["decoded_entity_body_receipt_complete"] is False
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert artifacts["raw_transfer_body"]["bytes"] == 10


@pytest.mark.parametrize(
    "raw",
    [
        _http_response(
            b"<html>login required</html>",
            headers=[("Content-Type", "text/html")],
        ),
        _http_response(
            b"valid utf-8 but no root marker",
            headers=[("Content-Type", "text/html")],
        ),
        _http_response(
            b"valid utf-8 status body",
            status="500 Internal Server Error",
            headers=[("Content-Type", "text/plain")],
        ),
    ],
)
def test_successful_utf8_decode_survives_later_rejection(raw: bytes) -> None:
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    assert outcome["inert_transcript_accepted"] is False
    assert outcome["body_utf8_valid"] is True
    assert outcome["body_truncated"] is False


def test_decoded_chunk_ceiling_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subject, "MAX_DECODED_BODY_BYTES", 10)
    encoded = b"B\r\n01234567890\r\n0\r\n\r\n"
    raw = _http_response(
        encoded,
        headers=[("Content-Type", "text/plain"), ("Transfer-Encoding", "chunked")],
    )
    with pytest.raises(subject.ContentError, match="decoded body ceiling"):
        subject._receive_response((raw, b""))


def test_success_outcome_is_explicitly_offline_and_nonoperational() -> None:
    outcome = subject.qualify_row_from_inert_transcript(0, transcript=_transcript())
    assert outcome["terminal_state"] == (
        "QUALIFICATION_ONLY_TERMINAL_INERT_ROOT_PAGE_TRANSCRIPT_ACCEPTED_NO_NETWORK"
    )
    assert outcome["inert_transcript_accepted"] is True
    assert outcome["root_page_success"] is False
    assert outcome["fetch_eligible"] is False
    assert outcome["request_emitted_count"] == 0
    assert outcome["live_request_emitted_count"] == 0
    assert outcome["transcript_request_emission_event_count"] == 1
    assert outcome["external_network_effect"] == 0
    assert outcome["effective_url"] is None
    assert outcome["retry_count"] == outcome["redirect_count"] == 0
    assert outcome["filesystem_materialized"] is False
    assert outcome["custody_mechanics_qualified"] is False
    assert outcome["intent_durable"] is False
    assert outcome["attempt_spent_in_external_system"] is False
    assert outcome["scientific_effect"] == 0


def test_outcome_diagnostic_roster_is_exact_public_and_alias_free() -> None:
    expected = (
        ("status_code", "EXACT_INT_OR_NULL"),
        ("protocol", "EXACT_STRING_OR_NULL"),
        ("framing", "EXACT_STRING_OR_NULL"),
        ("framing_complete", "EXACT_BOOL"),
        ("header_diagnostics_complete", "EXACT_BOOL"),
        ("content_type_header_count", "EXACT_INT_OR_NULL"),
        ("content_type_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
        ("normalized_media_type", "EXACT_STRING_OR_NULL"),
        ("content_disposition_header_count", "EXACT_INT_OR_NULL"),
        ("content_disposition_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
        ("location_header_count", "EXACT_INT_OR_NULL"),
        ("location_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
        ("content_encoding_header_count", "EXACT_INT_OR_NULL"),
        ("content_encoding_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
        ("content_encoding_normalized_values", "EXACT_LIST_OF_EXACT_STRING"),
        ("transfer_encoding_header_count", "EXACT_INT_OR_NULL"),
        ("transfer_encoding_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
        ("transfer_encoding_normalized_values", "EXACT_LIST_OF_EXACT_STRING"),
        ("transfer_encoding_semantics_valid", "EXACT_BOOL"),
        ("dechunk_complete", "EXACT_BOOL"),
        ("decoded_entity_body_receipt_complete", "EXACT_BOOL"),
        ("body_utf8_valid", "EXACT_BOOL"),
        ("forbidden_magic_detected", "EXACT_BOOL"),
        ("forbidden_magic_prefix_matches", "EXACT_LIST_OF_EXACT_STRING"),
        ("challenge_page_detected", "EXACT_BOOL"),
        ("login_wall_detected", "EXACT_BOOL"),
        ("consent_wall_detected", "EXACT_BOOL"),
        ("robot_block_detected", "EXACT_BOOL"),
        ("error_page_detected", "EXACT_BOOL"),
        ("rejection_substring_matches", "EXACT_LIST_OF_EXACT_STRING"),
        ("title_classifier_matches", "EXACT_LIST_OF_EXACT_STRING"),
        ("raw_status_start", "EXACT_INT_OR_NULL"),
        ("raw_status_end_exclusive", "EXACT_INT_OR_NULL"),
        ("raw_headers_start", "EXACT_INT_OR_NULL"),
        ("raw_headers_end_exclusive", "EXACT_INT_OR_NULL"),
        ("body_truncated", "EXACT_BOOL"),
    )
    assert subject.OUTCOME_DIAGNOSTIC_FIELD_TYPES == expected
    canonical_roster = [
        {"field": field, "exact_type": exact_type}
        for field, exact_type in expected
    ]
    assert subject.OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256 == subject._sha256(
        subject._canonical_no_lf(canonical_roster)
    )
    contract = subject.executor_contract()
    assert contract["outcome_diagnostic_field_types"] == canonical_roster
    assert contract["outcome_diagnostic_field_types_sha256"] == (
        subject.OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
    )
    outcome = subject.qualify_row_from_inert_transcript(0, transcript=_transcript())
    assert {field for field, _exact_type in expected} <= set(outcome)
    assert {
        "content_type_count",
        "content_type_raw",
        "content_disposition_count",
        "content_encoding_count",
        "content_encoding_raw",
        "content_encoding_normalized",
        "transfer_encoding_count",
        "transfer_encoding_raw",
        "transfer_encoding_normalized",
        "challenge_detected",
        "login_detected",
        "consent_detected",
        "robot_detected",
    }.isdisjoint(outcome)


def test_success_header_body_diagnostics_have_exact_relations() -> None:
    outcome = subject.qualify_row_from_inert_transcript(0, transcript=_transcript())
    assert outcome["header_diagnostics_complete"] is True
    assert outcome["framing_complete"] is True
    assert outcome["content_type_header_count"] == 1
    assert outcome["content_type_raw_values"] == ["text/html; charset=utf-8"]
    assert outcome["content_disposition_header_count"] == 0
    assert outcome["content_disposition_raw_values"] == []
    assert outcome["location_header_count"] == 0
    assert outcome["location_raw_values"] == []
    assert outcome["content_encoding_header_count"] == 0
    assert outcome["content_encoding_raw_values"] == []
    assert outcome["content_encoding_normalized_values"] == []
    assert outcome["transfer_encoding_header_count"] == 0
    assert outcome["transfer_encoding_raw_values"] == []
    assert outcome["transfer_encoding_normalized_values"] == []
    assert outcome["transfer_encoding_semantics_valid"] is True
    assert outcome["dechunk_complete"] is True
    assert outcome["decoded_entity_body_receipt_complete"] is True


def test_success_outcome_operational_bindings_are_strict_null() -> None:
    outcome = subject.qualify_row_from_inert_transcript(0, transcript=_transcript())
    for key in (
        "machine_raw_sha256",
        "machine_record_sha256",
        "package_aggregate_sha256",
        "executor_raw_sha256",
        "environment_manifest_sha256",
        "operational_admission_receipt_sha256",
        "operational_qualification_receipt_sha256",
        "operational_independent_go_receipt_sha256",
        "operational_fresh_authority_receipt_sha256",
        "operational_custody_root_path",
        "custody_root_identity_sha256",
        "operational_row_directory_basename",
    ):
        assert outcome[key] is None


def test_modeled_artifacts_and_forward_chain_are_exact_and_in_memory() -> None:
    outcome = subject.qualify_row_from_inert_transcript(0, transcript=_transcript())
    artifacts = outcome["modeled_artifacts"]
    assert [item["role"] for item in artifacts] == [
        "intent",
        "raw_request",
        "raw_response_head",
        "raw_transfer_body",
        "raw_metadata",
        "raw_stderr",
        "decoded_entity_body",
    ]
    assert all(item["filesystem_materialized"] is False for item in artifacts)
    assert all(item["filesystem_effect"] == 0 for item in artifacts)
    assert artifacts[1]["bytes"] == len(subject.exact_request_bytes(0))
    assert artifacts[1]["raw_sha256"] == subject.operation_spec(0)["exact_request_sha256"]
    assert artifacts[5]["raw_sha256"] == subject._sha256(b"NONE\n")
    assert outcome["forward_hash_chain"] == subject._chain_links(None, artifacts)
    assert len(outcome["forward_hash_chain"]) == 7
    assert outcome["record_sha256"] == subject._self_digest(outcome)


def test_chunked_outcome_receipts_distinguish_raw_and_decoded() -> None:
    raw, decoded = _chunked_success()
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert outcome["framing"] == "CHUNKED"
    assert artifacts["raw_transfer_body"]["raw_sha256"] != artifacts["decoded_entity_body"]["raw_sha256"]
    assert artifacts["decoded_entity_body"]["raw_sha256"] == subject._sha256(decoded)


def test_content_encoding_and_transfer_receipts_are_exact() -> None:
    body = b"plain public documentation"
    raw = _http_response(
        body,
        headers=[
            ("Content-Type", "text/plain"),
            ("Content-Encoding", "identity"),
            ("Content-Length", str(len(body))),
        ],
    )
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    assert outcome["content_encoding_header_count"] == 1
    assert outcome["content_encoding_raw_values"] == ["identity"]
    assert outcome["content_encoding_normalized_values"] == ["identity"]
    assert outcome["transfer_encoding_header_count"] == 0
    assert outcome["transfer_encoding_raw_values"] == []
    assert outcome["transfer_encoding_normalized_values"] == []
    assert outcome["transfer_encoding_semantics_valid"] is True


def test_connect_failure_is_terminal_zero_simulated_emission_and_no_retry() -> None:
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(failure_stage="CONNECT_FAILURE")
    )
    assert outcome["inert_transcript_accepted"] is False
    assert outcome["failure_code"] == "TRANSPORT_FAILURE"
    assert outcome["transcript_request_emission_event_count"] == 0
    assert outcome["live_request_emitted_count"] == 0
    assert outcome["retry_count"] == 0
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert artifacts["raw_stderr"]["raw_sha256"] == subject._sha256(
        b"TRANSPORT_FAILURE\n"
    )


def test_partial_send_failure_records_only_simulated_event_and_no_retry() -> None:
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(failure_stage="SEND_FAILURE")
    )
    assert outcome["failure_code"] == "TRANSPORT_FAILURE"
    assert outcome["transcript_request_emission_event_count"] == 1
    assert outcome["request_emitted_count"] == 0
    assert outcome["live_request_emitted_count"] == 0
    assert outcome["external_network_effect"] == 0
    assert outcome["retry_count"] == 0


@pytest.mark.parametrize(
    "version,alpn",
    [("TLSv1.1", "http/1.1"), ("TLSv1.3", "h2")],
)
def test_tls_policy_failure_has_zero_simulated_send_event(
    version: str, alpn: str
) -> None:
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(tls_version=version, alpn=alpn)
    )
    assert outcome["failure_code"] == "PROTOCOL_VIOLATION"
    assert outcome["transcript_request_emission_event_count"] == 0
    assert outcome["external_network_effect"] == 0


def test_protocol_failure_has_one_simulated_event_zero_retry() -> None:
    raw = _http_response(
        b"<html>redirect</html>",
        status="302 Found",
        headers=[("Content-Type", "text/html")],
    )
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    assert outcome["inert_transcript_accepted"] is False
    assert outcome["transcript_request_emission_event_count"] == 1
    assert outcome["request_emitted_count"] == 0
    assert outcome["retry_count"] == outcome["redirect_count"] == 0


def test_structured_challenge_evidence_survives_outcome() -> None:
    body = b'<!doctype html><html><title>Login</title><input type="password"></html>'
    raw = _http_response(
        body,
        headers=[
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(body))),
            ("Connection", "close"),
        ],
    )
    outcome = subject.qualify_row_from_inert_transcript(
        0, transcript=_transcript(raw_response=raw)
    )
    assert outcome["inert_transcript_accepted"] is False
    assert outcome["challenge_page_detected"] is True
    assert outcome["login_wall_detected"] is True
    assert 'type="password"' in outcome["rejection_substring_matches"]
    assert outcome["forbidden_magic_prefix_matches"] == []
    assert outcome["title_classifier_matches"] == ["login"]
    assert outcome["body_truncated"] is False
    artifacts = {item["role"]: item for item in outcome["modeled_artifacts"]}
    assert artifacts["decoded_entity_body"]["raw_sha256"] == subject._sha256(body)


def test_row1_is_preempted_without_exact_row0_acceptance() -> None:
    with pytest.raises(subject.AdmissionError, match="row0 InertTranscript"):
        subject.qualify_row_from_inert_transcript(1, transcript=_transcript(1))
    failed_transcript = _transcript(failure_stage="CONNECT_FAILURE")
    failed = subject.qualify_row_from_inert_transcript(
        0, transcript=failed_transcript
    )
    with pytest.raises(subject.AdmissionError, match="not accepted"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=failed_transcript,
            prior_outcome=failed,
        )


def test_row1_accepts_exact_prior_model_and_chains_in_memory() -> None:
    row0_transcript = _transcript()
    row0 = subject.qualify_row_from_inert_transcript(
        0, transcript=row0_transcript
    )
    row1 = subject.qualify_row_from_inert_transcript(
        1,
        transcript=_transcript(1),
        prior_transcript=row0_transcript,
        prior_outcome=row0,
    )
    prior_sha = subject._sha256(subject._canonical(row0))
    assert row1["inert_transcript_accepted"] is True
    assert row1["previous_qualification_outcome_sha256"] == prior_sha
    assert row1["forward_hash_chain"][0]["previous_link_sha256"] == prior_sha
    assert row1["external_network_effect"] == 0


@pytest.mark.parametrize(
    "key,value",
    [
        ("fetch_eligible", True),
        ("root_page_success", True),
        ("live_request_emitted_count", 1),
        ("external_network_effect", 1),
        ("effective_url", "https://physionet.org/content/challenge-2012/1.0.0/"),
        ("operational_independent_go_receipt_sha256", "0" * 64),
        ("filesystem_materialized", True),
        ("scientific_effect", 1),
    ],
)
def test_row1_prior_gate_rejects_promoted_or_effectful_claim(
    key: str, value: Any
) -> None:
    row0_transcript = _transcript()
    row0 = subject.qualify_row_from_inert_transcript(
        0, transcript=row0_transcript
    )
    row0[key] = value
    row0 = _reseal(row0)
    with pytest.raises(subject.AdmissionError, match="contextual recomputation"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=row0_transcript,
            prior_outcome=row0,
        )


def test_row1_prior_gate_rejects_artifact_and_chain_mutation() -> None:
    row0_transcript = _transcript()
    row0 = subject.qualify_row_from_inert_transcript(
        0, transcript=row0_transcript
    )
    row0["modeled_artifacts"][1]["raw_sha256"] = "0" * 64
    row0 = _reseal(row0)
    with pytest.raises(subject.AdmissionError, match="contextual recomputation"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=row0_transcript,
            prior_outcome=row0,
        )


def test_row1_prior_gate_rejects_extra_key_even_with_new_self_digest() -> None:
    row0_transcript = _transcript()
    row0 = subject.qualify_row_from_inert_transcript(
        0, transcript=row0_transcript
    )
    row0["extra"] = False
    row0 = _reseal(row0)
    with pytest.raises(subject.AdmissionError, match="contextual recomputation"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=row0_transcript,
            prior_outcome=row0,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "cipher_shape",
        "top_level_bool_for_int",
        "top_level_float_for_int",
        "artifact_bool_for_int",
        "artifact_float_for_int",
        "chain_bool_for_int",
        "header_relationship",
        "offset_relationship",
    ],
)
def test_row1_prior_gate_rejects_redigested_type_and_relationship_mutations(
    mutation: str,
) -> None:
    row0_transcript = _transcript()
    row0 = subject.qualify_row_from_inert_transcript(
        0, transcript=row0_transcript
    )
    if mutation == "cipher_shape":
        row0["cipher_bits"] = {"nonsense": []}
    elif mutation == "top_level_bool_for_int":
        row0["content_encoding_header_count"] = True
    elif mutation == "top_level_float_for_int":
        row0["raw_status_start"] = 0.0
    elif mutation == "artifact_bool_for_int":
        row0["modeled_artifacts"][0]["bytes"] = True
    elif mutation == "artifact_float_for_int":
        row0["modeled_artifacts"][0]["future_nlink_required"] = 1.0
    elif mutation == "chain_bool_for_int":
        row0["forward_hash_chain"][0]["ordinal"] = False
    elif mutation == "header_relationship":
        row0["content_encoding_header_count"] = 1
    elif mutation == "offset_relationship":
        row0["raw_headers_start"] = 999
    else:  # pragma: no cover - the parametrization is closed above
        raise AssertionError(mutation)
    row0 = _reseal(row0)
    with pytest.raises(subject.AdmissionError, match="contextual recomputation"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=row0_transcript,
            prior_outcome=row0,
        )


def test_row1_prior_gate_recomputes_the_supplied_row0_transcript_context() -> None:
    claimed_transcript = _transcript()
    claimed = subject.qualify_row_from_inert_transcript(
        0, transcript=claimed_transcript
    )
    chunked_raw, _decoded = _chunked_success()
    different_transcript = _transcript(raw_response=chunked_raw)
    with pytest.raises(subject.AdmissionError, match="contextual recomputation"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=_transcript(1),
            prior_transcript=different_transcript,
            prior_outcome=claimed,
        )


def test_row1_prior_gate_rejects_noncanonical_chronology() -> None:
    row0_transcript = _transcript()
    row0 = subject.qualify_row_from_inert_transcript(
        0, transcript=row0_transcript
    )
    late = dataclasses.replace(
        _transcript(1),
        intent_utc="2030-01-01T00:00:07Z",
        started_utc="2030-01-01T00:00:07Z",
        finished_utc="2030-01-01T00:00:08Z",
    )
    with pytest.raises(subject.AdmissionError, match="does not follow"):
        subject.qualify_row_from_inert_transcript(
            1,
            transcript=late,
            prior_transcript=row0_transcript,
            prior_outcome=row0,
        )


def test_runtime_hold_and_schema_roster_are_explicit() -> None:
    assert subject.EXACT_RUNTIME_ADMITTED is False
    assert subject.FETCH_ELIGIBLE is False
    assert "UNIMPLEMENTED_UNPROVED" in subject.RUNTIME_HOLD_REASON
    assert subject.SIMULATION_RESULT_SCHEMA_VERSION == subject.OUTCOME_SCHEMA_VERSION
    assert not hasattr(subject, "ADMISSION_SCHEMA_VERSION")
    assert not hasattr(subject, "GO_SCHEMA_VERSION")
    assert not hasattr(subject, "AUTHORITY_SCHEMA_VERSION")
    contract = subject.executor_contract()
    assert contract["row1_prior_input"] == (
        "EXACT_ROW0_INERT_TRANSCRIPT_PLUS_CLAIMED_FULL_ROW0_OUTCOME"
    )
    assert contract["row1_prior_validation"] == (
        "FULL_CONTEXTUAL_RECOMPUTATION_THEN_STRICT_RECURSIVE_EQUALITY"
    )
    assert type(contract["limits"]) is dict
    assert contract["limits"]["max_plain_clone_depth"] == 64
    assert contract["limits"]["max_plain_clone_nodes"] == 65_536
    assert contract["limits"]["max_plain_container_items"] == 8_192
    assert contract["limits"]["max_plain_string_codepoints"] == 262_144
    assert contract["limits"]["max_plain_string_utf8_bytes"] == 1_048_576
    assert contract["limits"]["max_plain_bytes_length"] == (
        subject.MAX_TOTAL_RESPONSE_BYTES
    )
    assert contract["limits"]["max_plain_integer_bits"] == 256
    assert contract["limits"]["max_plain_float_abs"] == 1.0e100


def test_operation_and_contract_hashes_are_stable_within_bytes() -> None:
    contract = subject.executor_contract()
    assert subject.OPERATION_ROSTER_SHA256 == subject._sha256(
        subject._canonical_no_lf(contract["operation_roster"])
    )
    assert subject.EXECUTOR_CONTRACT_SHA256 == subject._sha256(
        subject._canonical_no_lf(contract)
    )
    assert len(subject.OPERATION_ROSTER_SHA256) == 64
    assert len(subject.EXECUTOR_CONTRACT_SHA256) == 64
