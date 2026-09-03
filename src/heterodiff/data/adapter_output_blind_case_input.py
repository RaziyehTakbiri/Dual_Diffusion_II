"""Exact pre-output case input for an additive actual-output boundary.

The wire schema has fields only for source bytes and their partition context;
it has no dedicated adapter selector, V2, authority, expected-evidence,
caller-complete-sample, golden-output, or post-output field.  The arbitrary
source and identifier values can still encode other material, so this schema
fact is not a content-flow or nonexposure guarantee.

Constructing, parsing, or validating this artifact proves only byte-level
transport coherence.  This module does not execute an adapter, enforce
information-flow blindness, load adapter source, create a separate process,
compare actual and expected output, or make a gate decision.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import NamedTuple, Tuple

from .adapter_contract import (
    UNICODE_PROFILE,
    SamplePartition,
    SplitManifest,
)
from .adapter_evidence import (
    MAXIMUM_SOURCE_BYTES,
    MAXIMUM_SPLIT_ENTRIES,
    MAXIMUM_SPLIT_GROUPS,
)


OUTPUT_BLIND_CASE_INPUT_V1_ARTIFACT_TYPE = (
    "heterodiff.adapter.output-blind-case-input.v1"
)
OUTPUT_BLIND_CASE_INPUT_V1_DIGEST_DOMAIN = (
    OUTPUT_BLIND_CASE_INPUT_V1_ARTIFACT_TYPE
)
MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES = 4 * 1024 * 1024
MAXIMUM_OUTPUT_BLIND_CASE_SOURCE_BYTES = MAXIMUM_SOURCE_BYTES
MAXIMUM_OUTPUT_BLIND_SPLIT_ENTRIES = MAXIMUM_SPLIT_ENTRIES
MAXIMUM_OUTPUT_BLIND_SPLIT_GROUPS = MAXIMUM_SPLIT_GROUPS
MAXIMUM_OUTPUT_BLIND_CASE_INPUT_JSON_DEPTH = 8
MAXIMUM_OUTPUT_BLIND_CASE_INPUT_JSON_TOKENS = 200_000
MAXIMUM_OUTPUT_BLIND_CASE_INPUT_STRING_BYTES = 512 * 1024
_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1


class OutputBlindCaseInputCode(str, Enum):
    """Closed failure codes for the output-blind case-input transport."""

    INPUT_TYPE = "OUTPUT_BLIND_CASE_INPUT_TYPE"
    INPUT_RESOURCE = "OUTPUT_BLIND_CASE_INPUT_RESOURCE"
    INPUT_JSON = "OUTPUT_BLIND_CASE_INPUT_JSON"
    INPUT_NONCANONICAL = "OUTPUT_BLIND_CASE_INPUT_NONCANONICAL"
    INPUT_SCHEMA = "OUTPUT_BLIND_CASE_INPUT_SCHEMA"
    INPUT_BASE64 = "OUTPUT_BLIND_CASE_INPUT_BASE64"
    INPUT_RELATION = "OUTPUT_BLIND_CASE_INPUT_RELATION"
    INPUT_TRANSPORT = "OUTPUT_BLIND_CASE_INPUT_TRANSPORT"


_ERROR_MESSAGES = MappingProxyType(
    {
        OutputBlindCaseInputCode.INPUT_TYPE: (
            "output-blind case input has an invalid exact type"
        ),
        OutputBlindCaseInputCode.INPUT_RESOURCE: (
            "output-blind case input exceeds a resource ceiling"
        ),
        OutputBlindCaseInputCode.INPUT_JSON: (
            "output-blind case input is not strict canonical-profile JSON"
        ),
        OutputBlindCaseInputCode.INPUT_NONCANONICAL: (
            "output-blind case input JSON is not canonical"
        ),
        OutputBlindCaseInputCode.INPUT_SCHEMA: (
            "output-blind case input has an invalid closed schema"
        ),
        OutputBlindCaseInputCode.INPUT_BASE64: (
            "output-blind case input source payload is not canonical base64"
        ),
        OutputBlindCaseInputCode.INPUT_RELATION: (
            "output-blind case input partition context is inconsistent"
        ),
        OutputBlindCaseInputCode.INPUT_TRANSPORT: (
            "output-blind prepared transport is inconsistent"
        ),
    }
)


class OutputBlindCaseInputError(ValueError):
    """One coded failure whose message never reflects untrusted input."""

    def __init__(self, code: OutputBlindCaseInputCode) -> None:
        if type(code) is not OutputBlindCaseInputCode:
            raise TypeError("output-blind case input code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: OutputBlindCaseInputCode) -> None:
    raise OutputBlindCaseInputError(code) from None


def _snapshot_partition(value: object) -> SamplePartition:
    if type(value) is not SamplePartition:
        _fail(OutputBlindCaseInputCode.INPUT_TYPE)
    try:
        return SamplePartition(
            sample_id=value.sample_id,
            group_id=value.group_id,
            split=value.split,
        )
    except (TypeError, ValueError, UnicodeError):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)


def _snapshot_split_manifest(value: object) -> SplitManifest:
    if type(value) is not SplitManifest:
        _fail(OutputBlindCaseInputCode.INPUT_TYPE)
    if (
        type(value.entries) is not tuple
        or not value.entries
        or len(value.entries) > MAXIMUM_OUTPUT_BLIND_SPLIT_ENTRIES
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    if any(type(entry) is not SamplePartition for entry in value.entries):
        _fail(OutputBlindCaseInputCode.INPUT_TYPE)
    try:
        snapshot = SplitManifest(
            tuple(
                SamplePartition(
                    sample_id=entry.sample_id,
                    group_id=entry.group_id,
                    split=entry.split,
                )
                for entry in value.entries
            )
        )
    except (TypeError, ValueError, UnicodeError):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)
    if (
        len({entry.group_id for entry in snapshot.entries})
        > MAXIMUM_OUTPUT_BLIND_SPLIT_GROUPS
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    return snapshot


@dataclass(frozen=True)
class ActualAdapterCaseInputV1:
    """Exact immutable pre-output input supplied to one adapter case."""

    source_bytes: bytes
    partition: SamplePartition
    split_manifest: SplitManifest

    def __post_init__(self) -> None:
        if type(self) is not ActualAdapterCaseInputV1:
            _fail(OutputBlindCaseInputCode.INPUT_TYPE)
        if type(self.source_bytes) is not bytes:
            _fail(OutputBlindCaseInputCode.INPUT_TYPE)
        if (
            not self.source_bytes
            or len(self.source_bytes)
            > MAXIMUM_OUTPUT_BLIND_CASE_SOURCE_BYTES
        ):
            _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
        partition = _snapshot_partition(self.partition)
        split_manifest = _snapshot_split_manifest(self.split_manifest)
        if not split_manifest.contains_exactly(partition):
            _fail(OutputBlindCaseInputCode.INPUT_RELATION)
        object.__setattr__(self, "source_bytes", bytes(self.source_bytes))
        object.__setattr__(self, "partition", partition)
        object.__setattr__(self, "split_manifest", split_manifest)


class PreparedOutputBlindCaseInputV1(NamedTuple):
    """Exact typed snapshot plus canonical bytes and both byte identities."""

    case_input: ActualAdapterCaseInputV1
    input_bytes: bytes
    input_byte_count: int
    input_file_sha256: str
    input_sha256: str


def _snapshot_case_input(value: object) -> ActualAdapterCaseInputV1:
    if type(value) is not ActualAdapterCaseInputV1:
        _fail(OutputBlindCaseInputCode.INPUT_TYPE)
    try:
        return ActualAdapterCaseInputV1(
            source_bytes=value.source_bytes,
            partition=value.partition,
            split_manifest=value.split_manifest,
        )
    except OutputBlindCaseInputError:
        raise
    except (TypeError, ValueError, UnicodeError):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)


def _partition_tree(value: SamplePartition) -> dict:
    return {
        "group_id": value.group_id,
        "sample_id": value.sample_id,
        "split": value.split,
    }


def output_blind_case_input_v1_tree(
    value: ActualAdapterCaseInputV1,
) -> dict:
    """Return the exact five-key pre-output wire tree."""

    snapshot = _snapshot_case_input(value)
    return {
        "artifact_type": OUTPUT_BLIND_CASE_INPUT_V1_ARTIFACT_TYPE,
        "format_version": "1",
        "partition": _partition_tree(snapshot.partition),
        "source": {
            "byte_count": len(snapshot.source_bytes),
            "payload_base64": base64.b64encode(
                snapshot.source_bytes
            ).decode("ascii"),
        },
        "split_manifest": {
            "entries": [
                _partition_tree(entry)
                for entry in snapshot.split_manifest.entries
            ],
            "unicode_profile": UNICODE_PROFILE,
        },
    }


def _canonical_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)
    if (
        not encoded
        or len(encoded) > MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    return encoded


def output_blind_case_input_v1_bytes(
    value: ActualAdapterCaseInputV1,
) -> bytes:
    """Serialize one exact typed input as bounded canonical ASCII JSON."""

    return _canonical_bytes(output_blind_case_input_v1_tree(value))


def output_blind_case_input_v1_sha256(value: bytes) -> str:
    """Return the domain-separated, length-framed digest of exact bytes."""

    if type(value) is not bytes:
        _fail(OutputBlindCaseInputCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    domain = OUTPUT_BLIND_CASE_INPUT_V1_DIGEST_DOMAIN.encode(
        "ascii", "strict"
    )
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(b"\x00")
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)
    return digest.hexdigest()


def build_output_blind_case_input_v1(
    case_input: ActualAdapterCaseInputV1,
) -> PreparedOutputBlindCaseInputV1:
    """Snapshot and prepare one exact typed pre-output input."""

    snapshot = _snapshot_case_input(case_input)
    input_bytes = output_blind_case_input_v1_bytes(snapshot)
    return PreparedOutputBlindCaseInputV1(
        case_input=snapshot,
        input_bytes=input_bytes,
        input_byte_count=len(input_bytes),
        input_file_sha256=hashlib.sha256(input_bytes).hexdigest(),
        input_sha256=output_blind_case_input_v1_sha256(input_bytes),
    )


def _lexical_preflight(value: object) -> bytes:
    if type(value) is not bytes:
        _fail(OutputBlindCaseInputCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    if any(byte >= 0x80 for byte in value):
        _fail(OutputBlindCaseInputCode.INPUT_JSON)
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            string_bytes += 1
            if (
                string_bytes
                > MAXIMUM_OUTPUT_BLIND_CASE_INPUT_STRING_BYTES
            ):
                _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
            tokens += 1
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAXIMUM_OUTPUT_BLIND_CASE_INPUT_JSON_DEPTH:
                _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _fail(OutputBlindCaseInputCode.INPUT_JSON)
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAXIMUM_OUTPUT_BLIND_CASE_INPUT_JSON_TOKENS:
            _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    if in_string or depth != 0:
        _fail(OutputBlindCaseInputCode.INPUT_JSON)
    return value


class _DuplicateKeyError(ValueError):
    pass


def _strict_tree(value: object) -> object:
    raw = _lexical_preflight(value)
    try:
        text = raw.decode("ascii", "strict")
    except UnicodeError:
        _fail(OutputBlindCaseInputCode.INPUT_JSON)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise _DuplicateKeyError()
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise ValueError()
        result = int(token, 10)
        if result < 0 or result > _MAXIMUM_SAFE_INTEGER:
            raise ValueError()
        return result

    def reject_number(_token):
        raise ValueError()

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
    except (_DuplicateKeyError, TypeError, ValueError, RecursionError):
        _fail(OutputBlindCaseInputCode.INPUT_JSON)
    try:
        canonical = _canonical_bytes(tree)
    except OutputBlindCaseInputError as error:
        if error.code == OutputBlindCaseInputCode.INPUT_RESOURCE.value:
            raise
        _fail(OutputBlindCaseInputCode.INPUT_JSON)
    if canonical != raw:
        _fail(OutputBlindCaseInputCode.INPUT_NONCANONICAL)
    return tree


def _keys(value: object, expected: Tuple[str, ...]) -> dict:
    if (
        type(value) is not dict
        or tuple(sorted(value)) != tuple(sorted(expected))
    ):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)
    return value


def _partition_from_tree(value: object) -> SamplePartition:
    tree = _keys(value, ("group_id", "sample_id", "split"))
    if any(type(tree[name]) is not str for name in tree):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)
    try:
        return SamplePartition(
            sample_id=tree["sample_id"],
            group_id=tree["group_id"],
            split=tree["split"],
        )
    except (TypeError, ValueError, UnicodeError):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)


def _case_input_from_tree(value: object) -> ActualAdapterCaseInputV1:
    tree = _keys(
        value,
        (
            "artifact_type",
            "format_version",
            "partition",
            "source",
            "split_manifest",
        ),
    )
    if (
        tree["artifact_type"]
        != OUTPUT_BLIND_CASE_INPUT_V1_ARTIFACT_TYPE
        or type(tree["artifact_type"]) is not str
        or tree["format_version"] != "1"
        or type(tree["format_version"]) is not str
    ):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)
    partition = _partition_from_tree(tree["partition"])
    source_tree = _keys(
        tree["source"], ("byte_count", "payload_base64")
    )
    byte_count = source_tree["byte_count"]
    payload_base64 = source_tree["payload_base64"]
    if (
        type(byte_count) is not int
        or byte_count <= 0
        or byte_count > MAXIMUM_OUTPUT_BLIND_CASE_SOURCE_BYTES
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    if type(payload_base64) is not str:
        _fail(OutputBlindCaseInputCode.INPUT_BASE64)
    try:
        encoded_payload = payload_base64.encode("ascii", "strict")
        source_bytes = base64.b64decode(
            encoded_payload,
            validate=True,
        )
    except (UnicodeError, ValueError, binascii.Error):
        _fail(OutputBlindCaseInputCode.INPUT_BASE64)
    if (
        base64.b64encode(source_bytes) != encoded_payload
        or len(source_bytes) != byte_count
    ):
        _fail(OutputBlindCaseInputCode.INPUT_BASE64)

    split_tree = _keys(
        tree["split_manifest"], ("entries", "unicode_profile")
    )
    if (
        type(split_tree["unicode_profile"]) is not str
        or split_tree["unicode_profile"] != UNICODE_PROFILE
    ):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)
    entries_tree = split_tree["entries"]
    if (
        type(entries_tree) is not list
        or not entries_tree
        or len(entries_tree) > MAXIMUM_OUTPUT_BLIND_SPLIT_ENTRIES
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    entries = tuple(_partition_from_tree(item) for item in entries_tree)
    if (
        len({entry.group_id for entry in entries})
        > MAXIMUM_OUTPUT_BLIND_SPLIT_GROUPS
    ):
        _fail(OutputBlindCaseInputCode.INPUT_RESOURCE)
    try:
        split_manifest = SplitManifest(entries)
    except (TypeError, ValueError, UnicodeError):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)
    try:
        return ActualAdapterCaseInputV1(
            source_bytes=source_bytes,
            partition=partition,
            split_manifest=split_manifest,
        )
    except OutputBlindCaseInputError:
        raise
    except (TypeError, ValueError, UnicodeError):
        _fail(OutputBlindCaseInputCode.INPUT_SCHEMA)


def parse_output_blind_case_input_v1(
    input_bytes: bytes,
) -> PreparedOutputBlindCaseInputV1:
    """Strict-parse arbitrary bytes and return a re-prepared exact snapshot."""

    tree = _strict_tree(input_bytes)
    case_input = _case_input_from_tree(tree)
    prepared = build_output_blind_case_input_v1(case_input)
    if prepared.input_bytes != input_bytes:
        _fail(OutputBlindCaseInputCode.INPUT_NONCANONICAL)
    return prepared


def _canonical_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def validate_prepared_output_blind_case_input_v1(
    prepared: PreparedOutputBlindCaseInputV1,
) -> PreparedOutputBlindCaseInputV1:
    """Rebuild every field and return a fresh coherent transport snapshot."""

    if type(prepared) is not PreparedOutputBlindCaseInputV1:
        _fail(OutputBlindCaseInputCode.INPUT_TYPE)
    if (
        type(prepared.input_bytes) is not bytes
        or type(prepared.input_byte_count) is not int
        or not _canonical_sha256(prepared.input_file_sha256)
        or not _canonical_sha256(prepared.input_sha256)
    ):
        _fail(OutputBlindCaseInputCode.INPUT_TRANSPORT)
    rebuilt = build_output_blind_case_input_v1(prepared.case_input)
    if prepared != rebuilt:
        _fail(OutputBlindCaseInputCode.INPUT_TRANSPORT)
    parsed = parse_output_blind_case_input_v1(prepared.input_bytes)
    if parsed != rebuilt:
        _fail(OutputBlindCaseInputCode.INPUT_TRANSPORT)
    return rebuilt


__all__ = [
    "ActualAdapterCaseInputV1",
    "MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES",
    "MAXIMUM_OUTPUT_BLIND_CASE_INPUT_JSON_DEPTH",
    "MAXIMUM_OUTPUT_BLIND_CASE_INPUT_JSON_TOKENS",
    "MAXIMUM_OUTPUT_BLIND_CASE_INPUT_STRING_BYTES",
    "MAXIMUM_OUTPUT_BLIND_CASE_SOURCE_BYTES",
    "MAXIMUM_OUTPUT_BLIND_SPLIT_ENTRIES",
    "MAXIMUM_OUTPUT_BLIND_SPLIT_GROUPS",
    "OUTPUT_BLIND_CASE_INPUT_V1_ARTIFACT_TYPE",
    "OUTPUT_BLIND_CASE_INPUT_V1_DIGEST_DOMAIN",
    "OutputBlindCaseInputCode",
    "OutputBlindCaseInputError",
    "PreparedOutputBlindCaseInputV1",
    "build_output_blind_case_input_v1",
    "output_blind_case_input_v1_bytes",
    "output_blind_case_input_v1_sha256",
    "output_blind_case_input_v1_tree",
    "parse_output_blind_case_input_v1",
    "validate_prepared_output_blind_case_input_v1",
]
