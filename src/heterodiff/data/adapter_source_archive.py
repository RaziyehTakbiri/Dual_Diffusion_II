"""Pure validation of path-free publication source archives.

The publication binding already carries exact manifest and archive bytes.
This module gives those two byte strings a closed meaning without reopening a
path, extracting a member, invoking an adapter or oracle, or making a gate
decision.  The external inventory commits the exact archive and its complete
content multiset.  Logical source identities resolve to content, never to a
filesystem path.

This is publisher-side development code.  A decision-capable verifier must
reimplement the format independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import io
import json
from types import MappingProxyType
import re
import stat
from typing import NamedTuple, Tuple
import zipfile


SOURCE_ARCHIVE_INVENTORY_ARTIFACT_TYPE = (
    "heterodiff.adapter.source-archive-inventory.v1"
)
SOURCE_ARCHIVE_FORMAT_ID = "zip-stored-path-free-source-custody-v1"
SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.source-archive-membership-receipt.v1"
)
SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_DIGEST_DOMAIN = (
    SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE
)
SOURCE_ARCHIVE_ORACLE_ROLE_ID = "oracle-source"
SOURCE_ARCHIVE_ROLE_IDS = (
    "adapter-source",
    "contract-source",
    "execution-guard-source",
    SOURCE_ARCHIVE_ORACLE_ROLE_ID,
    "oracle-worker-source",
    "publisher-source",
    "support-source",
    "test-source",
    "verifier-source",
)

MAXIMUM_SOURCE_ARCHIVE_BYTES = 32 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES = 4 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_ENTRIES = 4096
MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES = 8 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES = 32 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_JSON_DEPTH = 32
MAXIMUM_SOURCE_ARCHIVE_JSON_TOKENS = 200_000
MAXIMUM_SOURCE_ARCHIVE_STRING_BYTES = 512 * 1024
MAXIMUM_SOURCE_OBJECT_ID_BYTES = 128
FIXED_SOURCE_ARCHIVE_TIME = (1980, 1, 1, 0, 0, 0)

_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_MEMBER_NAME_RE = re.compile(
    r"^objects/[0-9a-f]{64}-[0-9a-f]{16}-[0-9]{8}\.bin$"
)
_FIXED_UNIX_MODE = stat.S_IFREG | 0o444


class SourceArchiveCode(str, Enum):
    """Closed, interpolation-free source-custody failures."""

    INPUT_TYPE = "SOURCE_ARCHIVE_INPUT_TYPE"
    RESOURCE = "SOURCE_ARCHIVE_RESOURCE"
    INVENTORY_JSON = "SOURCE_ARCHIVE_INVENTORY_JSON"
    INVENTORY_NONCANONICAL = "SOURCE_ARCHIVE_INVENTORY_NONCANONICAL"
    INVENTORY_SCHEMA = "SOURCE_ARCHIVE_INVENTORY_SCHEMA"
    ARCHIVE_FORMAT = "SOURCE_ARCHIVE_FORMAT"
    ARCHIVE_CONTENT = "SOURCE_ARCHIVE_CONTENT"
    MEMBERSHIP_MISMATCH = "SOURCE_ARCHIVE_MEMBERSHIP_MISMATCH"


_ERROR_MESSAGES = MappingProxyType(
    {
        SourceArchiveCode.INPUT_TYPE: "source archive input is invalid",
        SourceArchiveCode.RESOURCE: (
            "source archive input exceeds a resource ceiling"
        ),
        SourceArchiveCode.INVENTORY_JSON: (
            "source archive inventory JSON is invalid"
        ),
        SourceArchiveCode.INVENTORY_NONCANONICAL: (
            "source archive inventory JSON is not canonical"
        ),
        SourceArchiveCode.INVENTORY_SCHEMA: (
            "source archive inventory schema is invalid"
        ),
        SourceArchiveCode.ARCHIVE_FORMAT: (
            "source archive container format is invalid"
        ),
        SourceArchiveCode.ARCHIVE_CONTENT: (
            "source archive content does not match its inventory"
        ),
        SourceArchiveCode.MEMBERSHIP_MISMATCH: (
            "source archive membership does not match"
        ),
    }
)


class SourceArchiveValidationError(ValueError):
    """One fixed coded validation failure without untrusted text."""

    def __init__(self, code: SourceArchiveCode) -> None:
        if type(code) is not SourceArchiveCode:
            raise TypeError("source archive code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class SourceArchiveTypeError(ValueError):
    """A typed source-custody object violates its exact contract."""


def _fail(code: SourceArchiveCode) -> None:
    raise SourceArchiveValidationError(code) from None


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise SourceArchiveTypeError(name + " must be a lowercase SHA-256")
    return value


def _token(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be an exact string")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        raise SourceArchiveTypeError(name + " must contain only ASCII") from None
    if (
        not encoded
        or len(encoded) > MAXIMUM_SOURCE_OBJECT_ID_BYTES
        or _TOKEN_RE.fullmatch(value) is None
    ):
        raise SourceArchiveTypeError(name + " is not a canonical token")
    return value


def _bounded_integer(
    value: object,
    *,
    name: str,
    maximum: int,
    allow_zero: bool,
) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < 0 or value > maximum or (value == 0 and not allow_zero):
        raise SourceArchiveTypeError(name + " is outside its exact bound")
    return value


@dataclass(frozen=True)
class SourceArchiveMemberV1:
    """One unique content identity and its physical archive multiplicity."""

    content_byte_count: int
    content_sha256: str
    occurrence_count: int

    def __post_init__(self) -> None:
        if type(self) is not SourceArchiveMemberV1:
            raise TypeError("source archive member must be exact")
        _bounded_integer(
            self.content_byte_count,
            name="content_byte_count",
            maximum=MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES,
            allow_zero=True,
        )
        _sha256(self.content_sha256, name="content_sha256")
        _bounded_integer(
            self.occurrence_count,
            name="occurrence_count",
            maximum=MAXIMUM_SOURCE_ARCHIVE_ENTRIES,
            allow_zero=False,
        )


@dataclass(frozen=True)
class SourceArchiveObjectV1:
    """One path-free logical role resolved to exact archive content."""

    role_id: str
    source_byte_count: int
    source_object_id: str
    source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not SourceArchiveObjectV1:
            raise TypeError("source archive object must be exact")
        if type(self.role_id) is not str:
            raise TypeError("role_id must be an exact string")
        if self.role_id not in SOURCE_ARCHIVE_ROLE_IDS:
            raise SourceArchiveTypeError("role_id is not a fixed source role")
        _bounded_integer(
            self.source_byte_count,
            name="source_byte_count",
            maximum=MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES,
            allow_zero=True,
        )
        _token(self.source_object_id, name="source_object_id")
        _sha256(self.source_sha256, name="source_sha256")


@dataclass(frozen=True)
class SourceArchiveInventoryV1:
    """External manifest for one exact path-free source archive."""

    archive_byte_count: int
    archive_sha256: str
    members: Tuple[SourceArchiveMemberV1, ...]
    source_objects: Tuple[SourceArchiveObjectV1, ...]
    archive_format_id: str = field(
        default=SOURCE_ARCHIVE_FORMAT_ID,
        init=False,
    )
    artifact_type: str = field(
        default=SOURCE_ARCHIVE_INVENTORY_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not SourceArchiveInventoryV1:
            raise TypeError("source archive inventory must be exact")
        if self.archive_format_id != SOURCE_ARCHIVE_FORMAT_ID:
            raise SourceArchiveTypeError("archive format identifier differs")
        if self.artifact_type != SOURCE_ARCHIVE_INVENTORY_ARTIFACT_TYPE:
            raise SourceArchiveTypeError("inventory artifact type differs")
        if self.format_version != "1":
            raise SourceArchiveTypeError("inventory format version differs")
        _bounded_integer(
            self.archive_byte_count,
            name="archive_byte_count",
            maximum=MAXIMUM_SOURCE_ARCHIVE_BYTES,
            allow_zero=False,
        )
        _sha256(self.archive_sha256, name="archive_sha256")
        if type(self.members) is not tuple or not self.members:
            raise TypeError("members must be a nonempty exact tuple")
        if len(self.members) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES:
            raise SourceArchiveTypeError("too many source archive members")
        if any(type(item) is not SourceArchiveMemberV1 for item in self.members):
            raise TypeError("members must contain exact member records")
        for item in self.members:
            SourceArchiveMemberV1.__post_init__(item)
        member_keys = tuple(
            (item.content_sha256, item.content_byte_count)
            for item in self.members
        )
        if member_keys != tuple(sorted(set(member_keys))):
            raise SourceArchiveTypeError(
                "members must be sorted and duplicate-free"
            )
        occurrence_total = sum(
            item.occurrence_count for item in self.members
        )
        if occurrence_total > MAXIMUM_SOURCE_ARCHIVE_ENTRIES:
            raise SourceArchiveTypeError("too many source archive occurrences")
        expanded_total = sum(
            item.content_byte_count * item.occurrence_count
            for item in self.members
        )
        if expanded_total > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES:
            raise SourceArchiveTypeError(
                "source archive expanded bytes exceed their ceiling"
            )
        if type(self.source_objects) is not tuple or not self.source_objects:
            raise TypeError("source_objects must be a nonempty exact tuple")
        if len(self.source_objects) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES:
            raise SourceArchiveTypeError("too many source objects")
        if any(
            type(item) is not SourceArchiveObjectV1
            for item in self.source_objects
        ):
            raise TypeError("source_objects must contain exact object records")
        for item in self.source_objects:
            SourceArchiveObjectV1.__post_init__(item)
        source_keys = tuple(
            (item.role_id, item.source_object_id)
            for item in self.source_objects
        )
        if source_keys != tuple(sorted(set(source_keys))):
            raise SourceArchiveTypeError(
                "source objects must be sorted and duplicate-free"
            )
        member_identities = set(member_keys)
        if any(
            (item.source_sha256, item.source_byte_count)
            not in member_identities
            for item in self.source_objects
        ):
            raise SourceArchiveTypeError(
                "source object does not resolve to an archive member"
            )
        oracle_digests = {
            item.source_sha256
            for item in self.source_objects
            if item.role_id == SOURCE_ARCHIVE_ORACLE_ROLE_ID
        }
        nonoracle_digests = {
            item.source_sha256
            for item in self.source_objects
            if item.role_id != SOURCE_ARCHIVE_ORACLE_ROLE_ID
        }
        if oracle_digests.intersection(nonoracle_digests):
            raise SourceArchiveTypeError(
                "oracle content must be role-disjoint"
            )


class ValidatedSourceArchiveMemberV1(NamedTuple):
    """One exact immutable member read from captured archive bytes."""

    content_byte_count: int
    content_sha256: str
    occurrence_ordinal: int
    content_bytes: bytes


class ValidatedSourceArchiveV1(NamedTuple):
    """One fully reconciled inventory/archive pair."""

    inventory: SourceArchiveInventoryV1
    inventory_bytes: bytes
    inventory_sha256: str
    archive_bytes: bytes
    archive_sha256: str
    members: Tuple[ValidatedSourceArchiveMemberV1, ...]


@dataclass(frozen=True)
class SourceArchiveMembershipRequestV1:
    """One exact logical source selection to validate in a bounded batch."""

    role_id: str
    source_bytes: bytes
    source_object_id: str

    def __post_init__(self) -> None:
        if type(self) is not SourceArchiveMembershipRequestV1:
            raise TypeError("source archive membership request must be exact")
        if type(self.role_id) is not str:
            raise TypeError("role_id must be an exact string")
        if self.role_id not in SOURCE_ARCHIVE_ROLE_IDS:
            raise SourceArchiveTypeError("role_id is not a fixed source role")
        if type(self.source_bytes) is not bytes:
            raise TypeError("source_bytes must be exact immutable bytes")
        if len(self.source_bytes) > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES:
            raise SourceArchiveTypeError(
                "source_bytes exceeds its byte ceiling"
            )
        _token(self.source_object_id, name="source_object_id")


@dataclass(frozen=True)
class ValidatedSourceArchiveMembershipV1:
    """Path-free proof that exact supplied bytes are one declared source."""

    archive_sha256: str
    inventory_sha256: str
    role_id: str
    source_byte_count: int
    source_object_id: str
    source_sha256: str
    artifact_type: str = field(
        default=SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not ValidatedSourceArchiveMembershipV1:
            raise TypeError("source archive membership must be exact")
        if (
            self.artifact_type
            != SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE
        ):
            raise SourceArchiveTypeError(
                "membership receipt artifact type differs"
            )
        if self.format_version != "1":
            raise SourceArchiveTypeError(
                "membership receipt format version differs"
            )
        _sha256(self.archive_sha256, name="archive_sha256")
        _sha256(self.inventory_sha256, name="inventory_sha256")
        if type(self.role_id) is not str:
            raise TypeError("role_id must be an exact string")
        if self.role_id not in SOURCE_ARCHIVE_ROLE_IDS:
            raise SourceArchiveTypeError("role_id is not a fixed source role")
        _bounded_integer(
            self.source_byte_count,
            name="source_byte_count",
            maximum=MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES,
            allow_zero=True,
        )
        _token(self.source_object_id, name="source_object_id")
        _sha256(self.source_sha256, name="source_sha256")


class ValidatedSourceArchiveMembershipSetV1(NamedTuple):
    """One raw-byte-validated archive and its ordered membership results."""

    source_archive: ValidatedSourceArchiveV1
    memberships: Tuple[ValidatedSourceArchiveMembershipV1, ...]


class ResolvedSourceArchiveObjectV1(NamedTuple):
    """One resolver transport, not authority from its constructible type alone.

    Consumers at a raw-byte trust boundary must call
    :func:`resolve_source_archive_object`; constructing this tuple directly
    carries no custody or validation claim.
    """

    source_archive: ValidatedSourceArchiveV1
    membership: ValidatedSourceArchiveMembershipV1
    source_bytes: bytes


def _validate_json_tree(value: object) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_SOURCE_ARCHIVE_JSON_TOKENS:
            raise SourceArchiveTypeError("inventory tree has too many values")
        if depth > MAXIMUM_SOURCE_ARCHIVE_JSON_DEPTH:
            raise SourceArchiveTypeError("inventory tree is too deeply nested")
        if type(current) is int:
            if current < 0 or current > _MAXIMUM_SAFE_INTEGER:
                raise SourceArchiveTypeError("inventory integer is outside range")
            continue
        if type(current) is str:
            try:
                encoded = current.encode("utf-8", "strict")
            except UnicodeError:
                raise SourceArchiveTypeError(
                    "inventory string is invalid Unicode"
                ) from None
            if len(encoded) > MAXIMUM_SOURCE_ARCHIVE_STRING_BYTES:
                raise SourceArchiveTypeError(
                    "inventory string exceeds its token ceiling"
                )
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    raise SourceArchiveTypeError(
                        "inventory object key must be a string"
                    )
                stack.append((item, depth + 1))
                stack.append((key, depth + 1))
            continue
        raise SourceArchiveTypeError("inventory tree contains an invalid type")


def _canonical_json_bytes(value: object, *, maximum: int) -> bytes:
    _validate_json_tree(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise SourceArchiveTypeError(
            "inventory cannot be encoded canonically"
        ) from error
    if not encoded or len(encoded) > maximum:
        raise SourceArchiveTypeError("inventory bytes exceed their ceiling")
    return encoded


def _inventory_tree(value: SourceArchiveInventoryV1) -> dict:
    if type(value) is not SourceArchiveInventoryV1:
        raise TypeError("source archive inventory must be exact")
    return {
        "archive_byte_count": value.archive_byte_count,
        "archive_format_id": value.archive_format_id,
        "archive_sha256": value.archive_sha256,
        "artifact_type": value.artifact_type,
        "format_version": value.format_version,
        "members": [
            {
                "content_byte_count": item.content_byte_count,
                "content_sha256": item.content_sha256,
                "occurrence_count": item.occurrence_count,
            }
            for item in value.members
        ],
        "source_objects": [
            {
                "role_id": item.role_id,
                "source_byte_count": item.source_byte_count,
                "source_object_id": item.source_object_id,
                "source_sha256": item.source_sha256,
            }
            for item in value.source_objects
        ],
    }


def source_archive_inventory_bytes(
    value: SourceArchiveInventoryV1,
) -> bytes:
    """Return the exact canonical external inventory bytes."""

    if type(value) is not SourceArchiveInventoryV1:
        raise TypeError("source archive inventory must be exact")
    SourceArchiveInventoryV1.__post_init__(value)
    return _canonical_json_bytes(
        _inventory_tree(value),
        maximum=MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
    )


def _membership_tree(value: ValidatedSourceArchiveMembershipV1) -> dict:
    if type(value) is not ValidatedSourceArchiveMembershipV1:
        raise TypeError("source archive membership must be exact")
    return {
        "archive_sha256": value.archive_sha256,
        "artifact_type": value.artifact_type,
        "format_version": value.format_version,
        "inventory_sha256": value.inventory_sha256,
        "role_id": value.role_id,
        "source_byte_count": value.source_byte_count,
        "source_object_id": value.source_object_id,
        "source_sha256": value.source_sha256,
    }


def source_archive_membership_receipt_bytes(
    value: ValidatedSourceArchiveMembershipV1,
) -> bytes:
    """Return canonical bytes for the non-decision membership result."""

    if type(value) is not ValidatedSourceArchiveMembershipV1:
        raise TypeError("source archive membership must be exact")
    ValidatedSourceArchiveMembershipV1.__post_init__(value)
    return _canonical_json_bytes(
        _membership_tree(value),
        maximum=MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
    )


def source_archive_membership_receipt_sha256(
    value: ValidatedSourceArchiveMembershipV1,
) -> str:
    """Return the length-framed membership-receipt digest."""

    payload = source_archive_membership_receipt_bytes(value)
    domain = SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_DIGEST_DOMAIN.encode(
        "ascii"
    )
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _lexical_preflight(value: bytes) -> None:
    if type(value) is not bytes:
        _fail(SourceArchiveCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES
    ):
        _fail(SourceArchiveCode.RESOURCE)
    if any(byte >= 0x80 for byte in value):
        _fail(SourceArchiveCode.INVENTORY_JSON)
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            if not escaped and byte == 0x22:
                in_string = False
                continue
            string_bytes += 1
            if string_bytes > MAXIMUM_SOURCE_ARCHIVE_STRING_BYTES:
                _fail(SourceArchiveCode.RESOURCE)
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
            tokens += 1
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAXIMUM_SOURCE_ARCHIVE_JSON_DEPTH:
                _fail(SourceArchiveCode.INVENTORY_JSON)
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _fail(SourceArchiveCode.INVENTORY_JSON)
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAXIMUM_SOURCE_ARCHIVE_JSON_TOKENS:
            _fail(SourceArchiveCode.RESOURCE)
    if in_string or depth != 0:
        _fail(SourceArchiveCode.INVENTORY_JSON)


def _strict_inventory_tree(value: bytes) -> object:
    _lexical_preflight(value)
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(SourceArchiveCode.INVENTORY_JSON)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise SourceArchiveTypeError("duplicate inventory key")
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise SourceArchiveTypeError("inventory integer token is too large")
        result = int(token, 10)
        if result < 0 or result > _MAXIMUM_SAFE_INTEGER:
            raise SourceArchiveTypeError("inventory integer is outside range")
        return result

    def reject_number(_token):
        raise SourceArchiveTypeError("inventory admits integers only")

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
        _validate_json_tree(tree)
    except (SourceArchiveTypeError, TypeError, ValueError, RecursionError):
        _fail(SourceArchiveCode.INVENTORY_JSON)
    try:
        canonical = _canonical_json_bytes(
            tree,
            maximum=MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
        )
    except (SourceArchiveTypeError, TypeError):
        _fail(SourceArchiveCode.INVENTORY_JSON)
    if canonical != value:
        _fail(SourceArchiveCode.INVENTORY_NONCANONICAL)
    return tree


def _keys(value: object, expected: Tuple[str, ...]) -> dict:
    if type(value) is not dict or tuple(sorted(value)) != tuple(
        sorted(expected)
    ):
        raise SourceArchiveTypeError("inventory object has invalid keys")
    return value


_INVENTORY_KEYS = (
    "archive_byte_count",
    "archive_format_id",
    "archive_sha256",
    "artifact_type",
    "format_version",
    "members",
    "source_objects",
)
_MEMBER_KEYS = (
    "content_byte_count",
    "content_sha256",
    "occurrence_count",
)
_SOURCE_OBJECT_KEYS = (
    "role_id",
    "source_byte_count",
    "source_object_id",
    "source_sha256",
)


def _inventory_from_tree(value: object) -> SourceArchiveInventoryV1:
    tree = _keys(value, _INVENTORY_KEYS)
    if tree["artifact_type"] != SOURCE_ARCHIVE_INVENTORY_ARTIFACT_TYPE:
        raise SourceArchiveTypeError("inventory artifact type differs")
    if tree["archive_format_id"] != SOURCE_ARCHIVE_FORMAT_ID:
        raise SourceArchiveTypeError("archive format identifier differs")
    if tree["format_version"] != "1":
        raise SourceArchiveTypeError("inventory format version differs")
    if type(tree["members"]) is not list or not tree["members"]:
        raise SourceArchiveTypeError("members must be a nonempty list")
    if type(tree["source_objects"]) is not list or not tree["source_objects"]:
        raise SourceArchiveTypeError("source_objects must be a nonempty list")
    if (
        len(tree["members"]) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
        or len(tree["source_objects"]) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
    ):
        raise SourceArchiveTypeError("source inventory has too many records")
    members = tuple(
        SourceArchiveMemberV1(**_keys(item, _MEMBER_KEYS))
        for item in tree["members"]
    )
    objects = tuple(
        SourceArchiveObjectV1(**_keys(item, _SOURCE_OBJECT_KEYS))
        for item in tree["source_objects"]
    )
    return SourceArchiveInventoryV1(
        archive_byte_count=tree["archive_byte_count"],
        archive_sha256=tree["archive_sha256"],
        members=members,
        source_objects=objects,
    )


def _member_identity_records(
    source_members: Tuple[bytes, ...],
) -> Tuple[SourceArchiveMemberV1, ...]:
    counts = {}
    for raw in source_members:
        identity = (hashlib.sha256(raw).hexdigest(), len(raw))
        counts[identity] = counts.get(identity, 0) + 1
    return tuple(
        SourceArchiveMemberV1(
            content_byte_count=byte_count,
            content_sha256=digest,
            occurrence_count=counts[(digest, byte_count)],
        )
        for digest, byte_count in sorted(counts)
    )


def _snapshot_source_members(value: object) -> Tuple[bytes, ...]:
    if type(value) is not tuple or not value:
        raise TypeError("source members must be a nonempty exact tuple")
    if len(value) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES:
        raise SourceArchiveTypeError("too many source archive members")
    result = []
    expanded = 0
    for raw in value:
        if type(raw) is not bytes:
            raise TypeError("source members must be exact immutable bytes")
        if len(raw) > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES:
            raise SourceArchiveTypeError(
                "source archive member exceeds its byte ceiling"
            )
        expanded += len(raw)
        if expanded > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES:
            raise SourceArchiveTypeError(
                "source archive expanded bytes exceed their ceiling"
            )
        result.append(raw)
    return tuple(result)


def _member_name(
    digest: str,
    byte_count: int,
    occurrence_ordinal: int,
) -> str:
    return "objects/{}-{:016x}-{:08d}.bin".format(
        digest,
        byte_count,
        occurrence_ordinal,
    )


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_SOURCE_ARCHIVE_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.create_version = 20
    info.extract_version = 20
    info.external_attr = _FIXED_UNIX_MODE << 16
    info.internal_attr = 0
    info.flag_bits = 0
    info.extra = b""
    info.comment = b""
    info.volume = 0
    return info


def build_source_archive(source_members: Tuple[bytes, ...]) -> bytes:
    """Build deterministic path-free ZIP bytes for already captured members."""

    members = _snapshot_source_members(source_members)
    ordered = sorted(
        members,
        key=lambda raw: (hashlib.sha256(raw).hexdigest(), len(raw), raw),
    )
    occurrences = {}
    output = io.BytesIO()
    try:
        with zipfile.ZipFile(
            output,
            mode="w",
            compression=zipfile.ZIP_STORED,
            allowZip64=False,
        ) as archive:
            archive.comment = b""
            for raw in ordered:
                identity = (hashlib.sha256(raw).hexdigest(), len(raw))
                ordinal = occurrences.get(identity, 0)
                occurrences[identity] = ordinal + 1
                archive.writestr(
                    _zip_info(_member_name(identity[0], identity[1], ordinal)),
                    raw,
                )
    except (OSError, RuntimeError, ValueError, zipfile.LargeZipFile) as error:
        raise SourceArchiveTypeError(
            "source archive cannot be built deterministically"
        ) from error
    result = output.getvalue()
    if not result or len(result) > MAXIMUM_SOURCE_ARCHIVE_BYTES:
        raise SourceArchiveTypeError(
            "source archive bytes exceed their ceiling"
        )
    return result


def build_source_archive_inventory(
    archive_bytes: bytes,
    source_members: Tuple[bytes, ...],
    source_objects: Tuple[SourceArchiveObjectV1, ...],
) -> SourceArchiveInventoryV1:
    """Build the external inventory for deterministic captured member bytes."""

    if type(archive_bytes) is not bytes:
        raise TypeError("archive_bytes must be exact immutable bytes")
    members = _snapshot_source_members(source_members)
    if build_source_archive(members) != archive_bytes:
        raise SourceArchiveTypeError(
            "archive bytes do not match deterministic source members"
        )
    if type(source_objects) is not tuple:
        raise TypeError("source_objects must be an exact tuple")
    return SourceArchiveInventoryV1(
        archive_byte_count=len(archive_bytes),
        archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        members=_member_identity_records(members),
        source_objects=source_objects,
    )


def _preflight_zip_container(archive_bytes: bytes) -> None:
    """Bound the central directory before ``zipfile`` allocates its entries."""

    if len(archive_bytes) < 22:
        _fail(SourceArchiveCode.ARCHIVE_FORMAT)
    end_record = archive_bytes[-22:]
    if end_record[:4] != b"PK\x05\x06":
        _fail(SourceArchiveCode.ARCHIVE_FORMAT)
    disk_number = int.from_bytes(end_record[4:6], "little")
    central_disk = int.from_bytes(end_record[6:8], "little")
    entries_on_disk = int.from_bytes(end_record[8:10], "little")
    entry_count = int.from_bytes(end_record[10:12], "little")
    central_size = int.from_bytes(end_record[12:16], "little")
    central_offset = int.from_bytes(end_record[16:20], "little")
    comment_size = int.from_bytes(end_record[20:22], "little")
    if (
        disk_number != 0
        or central_disk != 0
        or entries_on_disk != entry_count
        or entry_count == 0
        or entry_count > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
        or central_size == 0
        or comment_size != 0
        or central_offset + central_size != len(archive_bytes) - 22
    ):
        _fail(SourceArchiveCode.ARCHIVE_FORMAT)
    central_end = central_offset + central_size
    position = central_offset
    observed_entries = 0
    expanded_bytes = 0
    while position < central_end:
        if (
            central_end - position < 46
            or archive_bytes[position : position + 4] != b"PK\x01\x02"
        ):
            _fail(SourceArchiveCode.ARCHIVE_FORMAT)
        header = archive_bytes[position : position + 46]
        version_made_by = int.from_bytes(header[4:6], "little")
        version_needed = int.from_bytes(header[6:8], "little")
        flag_bits = int.from_bytes(header[8:10], "little")
        compression = int.from_bytes(header[10:12], "little")
        modified_time = int.from_bytes(header[12:14], "little")
        modified_date = int.from_bytes(header[14:16], "little")
        compressed_size = int.from_bytes(header[20:24], "little")
        uncompressed_size = int.from_bytes(header[24:28], "little")
        name_size = int.from_bytes(header[28:30], "little")
        extra_size = int.from_bytes(header[30:32], "little")
        member_comment_size = int.from_bytes(header[32:34], "little")
        member_disk = int.from_bytes(header[34:36], "little")
        internal_attr = int.from_bytes(header[36:38], "little")
        external_attr = int.from_bytes(header[38:42], "little")
        local_offset = int.from_bytes(header[42:46], "little")
        record_size = 46 + name_size + extra_size + member_comment_size
        if (
            record_size > central_end - position
            or version_made_by != ((3 << 8) | 20)
            or version_needed != 20
            or flag_bits != 0
            or compression != 0
            or modified_time != 0
            or modified_date != 0x21
            or compressed_size != uncompressed_size
            or uncompressed_size > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES
            or name_size == 0
            or name_size > 128
            or extra_size != 0
            or member_comment_size != 0
            or member_disk != 0
            or internal_attr != 0
            or external_attr != (_FIXED_UNIX_MODE << 16)
            or local_offset >= central_offset
        ):
            _fail(SourceArchiveCode.ARCHIVE_FORMAT)
        name_start = position + 46
        name_bytes = archive_bytes[name_start : name_start + name_size]
        try:
            name = name_bytes.decode("ascii", "strict")
        except UnicodeError:
            _fail(SourceArchiveCode.ARCHIVE_FORMAT)
        if _MEMBER_NAME_RE.fullmatch(name) is None:
            _fail(SourceArchiveCode.ARCHIVE_FORMAT)
        observed_entries += 1
        if observed_entries > MAXIMUM_SOURCE_ARCHIVE_ENTRIES:
            _fail(SourceArchiveCode.ARCHIVE_FORMAT)
        expanded_bytes += uncompressed_size
        if expanded_bytes > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES:
            _fail(SourceArchiveCode.RESOURCE)
        position += record_size
    if position != central_end or observed_entries != entry_count:
        _fail(SourceArchiveCode.ARCHIVE_FORMAT)


def _read_archive_members(
    archive_bytes: bytes,
) -> Tuple[ValidatedSourceArchiveMemberV1, ...]:
    _preflight_zip_container(archive_bytes)
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), mode="r") as archive:
            if archive.comment != b"":
                _fail(SourceArchiveCode.ARCHIVE_FORMAT)
            infos = archive.infolist()
            if (
                not infos
                or len(infos) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
            ):
                _fail(SourceArchiveCode.RESOURCE)
            names = tuple(info.filename for info in infos)
            if names != tuple(sorted(set(names))):
                _fail(SourceArchiveCode.ARCHIVE_FORMAT)
            expanded = 0
            for info in infos:
                try:
                    name_bytes = info.filename.encode("ascii", "strict")
                except UnicodeError:
                    _fail(SourceArchiveCode.ARCHIVE_FORMAT)
                if (
                    not name_bytes
                    or len(name_bytes) > 128
                    or _MEMBER_NAME_RE.fullmatch(info.filename) is None
                    or info.orig_filename != info.filename
                    or info.date_time != FIXED_SOURCE_ARCHIVE_TIME
                    or info.compress_type != zipfile.ZIP_STORED
                    or info.create_system != 3
                    or info.external_attr != (_FIXED_UNIX_MODE << 16)
                    or info.internal_attr != 0
                    or info.flag_bits != 0
                    or info.extra != b""
                    or info.comment != b""
                    or info.is_dir()
                    or info.file_size != info.compress_size
                    or info.file_size > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES
                ):
                    _fail(SourceArchiveCode.ARCHIVE_FORMAT)
                expanded += info.file_size
                if expanded > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES:
                    _fail(SourceArchiveCode.RESOURCE)
            contents = []
            for info in infos:
                try:
                    with archive.open(info, mode="r") as member:
                        raw = member.read(info.file_size + 1)
                        trailing = member.read(1)
                except (
                    EOFError,
                    OSError,
                    RuntimeError,
                    ValueError,
                    zipfile.BadZipFile,
                ):
                    _fail(SourceArchiveCode.ARCHIVE_CONTENT)
                if (
                    len(raw) != info.file_size
                    or trailing != b""
                    or hashlib.sha256(raw).hexdigest()
                    not in info.filename
                ):
                    _fail(SourceArchiveCode.ARCHIVE_CONTENT)
                contents.append(raw)
    except SourceArchiveValidationError:
        raise
    except (
        EOFError,
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ):
        _fail(SourceArchiveCode.ARCHIVE_FORMAT)

    ordered = sorted(
        contents,
        key=lambda raw: (hashlib.sha256(raw).hexdigest(), len(raw), raw),
    )
    occurrences = {}
    expected_names = []
    result = []
    for raw in ordered:
        identity = (hashlib.sha256(raw).hexdigest(), len(raw))
        ordinal = occurrences.get(identity, 0)
        occurrences[identity] = ordinal + 1
        expected_names.append(_member_name(identity[0], identity[1], ordinal))
        result.append(
            ValidatedSourceArchiveMemberV1(
                content_byte_count=identity[1],
                content_sha256=identity[0],
                occurrence_ordinal=ordinal,
                content_bytes=raw,
            )
        )
    if tuple(expected_names) != names:
        _fail(SourceArchiveCode.ARCHIVE_CONTENT)
    return tuple(result)


def validate_source_archive(
    inventory_bytes: bytes,
    archive_bytes: bytes,
) -> ValidatedSourceArchiveV1:
    """Strictly reconcile exact external inventory and captured ZIP bytes."""

    if type(inventory_bytes) is not bytes or type(archive_bytes) is not bytes:
        _fail(SourceArchiveCode.INPUT_TYPE)
    if (
        not archive_bytes
        or len(archive_bytes) > MAXIMUM_SOURCE_ARCHIVE_BYTES
    ):
        _fail(SourceArchiveCode.RESOURCE)
    tree = _strict_inventory_tree(inventory_bytes)
    try:
        inventory = _inventory_from_tree(tree)
        if source_archive_inventory_bytes(inventory) != inventory_bytes:
            raise SourceArchiveTypeError("inventory projection differs")
    except (SourceArchiveTypeError, TypeError, ValueError):
        _fail(SourceArchiveCode.INVENTORY_SCHEMA)
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    if (
        inventory.archive_byte_count != len(archive_bytes)
        or inventory.archive_sha256 != archive_sha256
    ):
        _fail(SourceArchiveCode.ARCHIVE_CONTENT)
    members = _read_archive_members(archive_bytes)
    observed_records = _member_identity_records(
        tuple(item.content_bytes for item in members)
    )
    if observed_records != inventory.members:
        _fail(SourceArchiveCode.ARCHIVE_CONTENT)
    try:
        rebuilt = build_source_archive(
            tuple(item.content_bytes for item in members)
        )
    except (SourceArchiveTypeError, TypeError, ValueError):
        _fail(SourceArchiveCode.ARCHIVE_FORMAT)
    if rebuilt != archive_bytes:
        _fail(SourceArchiveCode.ARCHIVE_FORMAT)
    return ValidatedSourceArchiveV1(
        inventory=inventory,
        inventory_bytes=inventory_bytes,
        inventory_sha256=hashlib.sha256(inventory_bytes).hexdigest(),
        archive_bytes=archive_bytes,
        archive_sha256=archive_sha256,
        members=members,
    )


def _validate_membership_from_archive(
    value: ValidatedSourceArchiveV1,
    *,
    role_id: str,
    source_object_id: str,
    source_bytes: bytes,
) -> ValidatedSourceArchiveMembershipV1:
    records = tuple(
        item
        for item in value.inventory.source_objects
        if item.role_id == role_id
        and item.source_object_id == source_object_id
    )
    if len(records) != 1:
        _fail(SourceArchiveCode.MEMBERSHIP_MISMATCH)
    record = records[0]
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if (
        record.source_byte_count != len(source_bytes)
        or record.source_sha256 != source_sha256
        or not any(
            item.content_byte_count == len(source_bytes)
            and item.content_sha256 == source_sha256
            and item.content_bytes == source_bytes
            for item in value.members
        )
    ):
        _fail(SourceArchiveCode.MEMBERSHIP_MISMATCH)
    return ValidatedSourceArchiveMembershipV1(
        archive_sha256=value.archive_sha256,
        inventory_sha256=value.inventory_sha256,
        role_id=record.role_id,
        source_byte_count=record.source_byte_count,
        source_object_id=record.source_object_id,
        source_sha256=record.source_sha256,
    )


def resolve_source_archive_object(
    inventory_bytes: bytes,
    archive_bytes: bytes,
    *,
    role_id: str,
    source_object_id: str,
) -> ResolvedSourceArchiveObjectV1:
    """Resolve one logical source from fully revalidated raw custody bytes.

    Unlike the membership APIs, this boundary accepts no caller-supplied source
    bytes.  It strict-validates the complete inventory/archive pair, selects one
    exact logical object, and obtains its immutable bytes only from the
    reconciled archive members.
    """

    if type(role_id) is not str or type(source_object_id) is not str:
        _fail(SourceArchiveCode.INPUT_TYPE)
    try:
        if role_id not in SOURCE_ARCHIVE_ROLE_IDS:
            raise SourceArchiveTypeError("role_id is not a fixed source role")
        _token(source_object_id, name="source_object_id")
    except (SourceArchiveTypeError, TypeError, ValueError):
        _fail(SourceArchiveCode.INPUT_TYPE)

    source_archive = validate_source_archive(inventory_bytes, archive_bytes)
    records = tuple(
        item
        for item in source_archive.inventory.source_objects
        if item.role_id == role_id
        and item.source_object_id == source_object_id
    )
    if len(records) != 1:
        _fail(SourceArchiveCode.MEMBERSHIP_MISMATCH)
    record = records[0]
    matching_members = tuple(
        item
        for item in source_archive.members
        if item.content_byte_count == record.source_byte_count
        and item.content_sha256 == record.source_sha256
    )
    if not matching_members:
        _fail(SourceArchiveCode.MEMBERSHIP_MISMATCH)
    source_bytes = matching_members[0].content_bytes
    if (
        type(source_bytes) is not bytes
        or any(
            type(item.content_bytes) is not bytes
            or item.content_bytes != source_bytes
            for item in matching_members
        )
        or len(source_bytes) != record.source_byte_count
        or hashlib.sha256(source_bytes).hexdigest() != record.source_sha256
    ):
        _fail(SourceArchiveCode.MEMBERSHIP_MISMATCH)
    membership = _validate_membership_from_archive(
        source_archive,
        role_id=role_id,
        source_object_id=source_object_id,
        source_bytes=source_bytes,
    )
    return ResolvedSourceArchiveObjectV1(
        source_archive=source_archive,
        membership=membership,
        source_bytes=source_bytes,
    )


def validate_source_archive_memberships(
    inventory_bytes: bytes,
    archive_bytes: bytes,
    requests: Tuple[SourceArchiveMembershipRequestV1, ...],
) -> ValidatedSourceArchiveMembershipSetV1:
    """Validate raw custody bytes once and resolve an ordered source batch."""

    if type(requests) is not tuple or not requests:
        _fail(SourceArchiveCode.INPUT_TYPE)
    if len(requests) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES:
        _fail(SourceArchiveCode.RESOURCE)
    aggregate_source_bytes = 0
    snapshots = []
    for request in requests:
        if type(request) is not SourceArchiveMembershipRequestV1:
            _fail(SourceArchiveCode.INPUT_TYPE)
        try:
            SourceArchiveMembershipRequestV1.__post_init__(request)
        except (SourceArchiveTypeError, TypeError, ValueError):
            _fail(SourceArchiveCode.INPUT_TYPE)
        aggregate_source_bytes += len(request.source_bytes)
        if aggregate_source_bytes > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES:
            _fail(SourceArchiveCode.RESOURCE)
        snapshots.append(
            SourceArchiveMembershipRequestV1(
                role_id=request.role_id,
                source_bytes=request.source_bytes,
                source_object_id=request.source_object_id,
            )
        )
    source_archive = validate_source_archive(inventory_bytes, archive_bytes)
    memberships = tuple(
        _validate_membership_from_archive(
            source_archive,
            role_id=request.role_id,
            source_object_id=request.source_object_id,
            source_bytes=request.source_bytes,
        )
        for request in snapshots
    )
    return ValidatedSourceArchiveMembershipSetV1(
        source_archive=source_archive,
        memberships=memberships,
    )


def validate_source_archive_membership(
    value: ValidatedSourceArchiveV1,
    *,
    role_id: str,
    source_object_id: str,
    source_bytes: bytes,
) -> ValidatedSourceArchiveMembershipV1:
    """Revalidate raw custody bytes and resolve one logical source."""

    if type(value) is not ValidatedSourceArchiveV1:
        _fail(SourceArchiveCode.INPUT_TYPE)
    if (
        type(role_id) is not str
        or type(source_object_id) is not str
        or type(source_bytes) is not bytes
    ):
        _fail(SourceArchiveCode.INPUT_TYPE)
    if len(source_bytes) > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES:
        _fail(SourceArchiveCode.RESOURCE)
    try:
        request = SourceArchiveMembershipRequestV1(
            role_id=role_id,
            source_bytes=source_bytes,
            source_object_id=source_object_id,
        )
    except (SourceArchiveTypeError, TypeError, ValueError):
        _fail(SourceArchiveCode.INPUT_TYPE)
    result = validate_source_archive_memberships(
        value.inventory_bytes,
        value.archive_bytes,
        (request,),
    )
    if result.source_archive != value:
        _fail(SourceArchiveCode.INPUT_TYPE)
    return result.memberships[0]


__all__ = [
    "MAXIMUM_SOURCE_ARCHIVE_BYTES",
    "MAXIMUM_SOURCE_ARCHIVE_ENTRIES",
    "MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES",
    "MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES",
    "MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES",
    "SOURCE_ARCHIVE_FORMAT_ID",
    "SOURCE_ARCHIVE_INVENTORY_ARTIFACT_TYPE",
    "SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE",
    "SOURCE_ARCHIVE_ORACLE_ROLE_ID",
    "SOURCE_ARCHIVE_ROLE_IDS",
    "ResolvedSourceArchiveObjectV1",
    "SourceArchiveCode",
    "SourceArchiveInventoryV1",
    "SourceArchiveMemberV1",
    "SourceArchiveMembershipRequestV1",
    "SourceArchiveObjectV1",
    "SourceArchiveTypeError",
    "SourceArchiveValidationError",
    "ValidatedSourceArchiveMembershipV1",
    "ValidatedSourceArchiveMembershipSetV1",
    "ValidatedSourceArchiveV1",
    "build_source_archive",
    "build_source_archive_inventory",
    "source_archive_inventory_bytes",
    "source_archive_membership_receipt_bytes",
    "source_archive_membership_receipt_sha256",
    "resolve_source_archive_object",
    "validate_source_archive",
    "validate_source_archive_membership",
    "validate_source_archive_memberships",
]
