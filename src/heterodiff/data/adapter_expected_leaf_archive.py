"""Pure raw-byte archive validation for private expected-evidence leaf bundles.

This module assigns a closed, path-free meaning to a deterministic ZIP_STORED
archive and its external inventory.  The inventory maps each exact stable case
authority identifier to exactly one private expected-evidence leaf bundle.  It
binds both the ordinary SHA-256 of those bytes and the bundle-domain digest
used by the expected-leaf protocol.

The archive is deliberately private.  Validation proves in-memory byte
consistency and membership only.  It does not establish a chain of custody,
external possession or provenance, semantic truth, execution provenance,
publication authority, or a gate decision.  Every operation is a pure
in-memory function: no path, file, process, or network interface is accepted.
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
from typing import Tuple
import zipfile


EXPECTED_LEAF_ARCHIVE_INVENTORY_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-leaf-archive-inventory.v1"
)
EXPECTED_LEAF_ARCHIVE_INVENTORY_DIGEST_DOMAIN = (
    EXPECTED_LEAF_ARCHIVE_INVENTORY_ARTIFACT_TYPE
)
EXPECTED_LEAF_ARCHIVE_FORMAT_ID = (
    "zip-stored-path-free-expected-leaf-custody-v1"
)
# ``custody`` is the frozen format label, not an external-custody attestation.
EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-leaf-archive-membership-receipt.v1"
)
EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_RECEIPT_DIGEST_DOMAIN = (
    EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE
)
EXPECTED_LEAF_ARCHIVE_ROLE_ID = "expected-evidence-leaf-bundle"
EXPECTED_EVIDENCE_LEAF_BUNDLE_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-evidence-leaf-bundle.v1"
)

MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES = 128 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_ARCHIVE_EXPANDED_BYTES = 128 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES = 4 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES = 4096
MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES = 32 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_ARCHIVE_JSON_DEPTH = 32
MAXIMUM_EXPECTED_LEAF_ARCHIVE_JSON_NODES = 200_000
MAXIMUM_EXPECTED_LEAF_ARCHIVE_STRING_BYTES = 512 * 1024
MAXIMUM_CASE_AUTHORITY_ID_BYTES = 128
FIXED_EXPECTED_LEAF_ARCHIVE_TIME = (1980, 1, 1, 0, 0, 0)

_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_AUTHORITY_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
)
_MEMBER_NAME_RE = re.compile(
    r"^objects/[0-9a-f]{64}-[0-9a-f]{16}\.bin$"
)
_FIXED_UNIX_MODE = stat.S_IFREG | 0o444


class ExpectedLeafArchiveCode(str, Enum):
    """Closed, interpolation-free private archive failures."""

    INPUT_TYPE = "EXPECTED_LEAF_ARCHIVE_INPUT_TYPE"
    RESOURCE = "EXPECTED_LEAF_ARCHIVE_RESOURCE"
    INVENTORY_JSON = "EXPECTED_LEAF_ARCHIVE_INVENTORY_JSON"
    INVENTORY_NONCANONICAL = "EXPECTED_LEAF_ARCHIVE_INVENTORY_NONCANONICAL"
    INVENTORY_SCHEMA = "EXPECTED_LEAF_ARCHIVE_INVENTORY_SCHEMA"
    ARCHIVE_FORMAT = "EXPECTED_LEAF_ARCHIVE_FORMAT"
    ARCHIVE_CONTENT = "EXPECTED_LEAF_ARCHIVE_CONTENT"
    MEMBERSHIP_MISMATCH = "EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_MISMATCH"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExpectedLeafArchiveCode.INPUT_TYPE: (
            "expected-leaf archive input is invalid"
        ),
        ExpectedLeafArchiveCode.RESOURCE: (
            "expected-leaf archive input exceeds a resource ceiling"
        ),
        ExpectedLeafArchiveCode.INVENTORY_JSON: (
            "expected-leaf archive inventory JSON is invalid"
        ),
        ExpectedLeafArchiveCode.INVENTORY_NONCANONICAL: (
            "expected-leaf archive inventory JSON is not canonical"
        ),
        ExpectedLeafArchiveCode.INVENTORY_SCHEMA: (
            "expected-leaf archive inventory schema is invalid"
        ),
        ExpectedLeafArchiveCode.ARCHIVE_FORMAT: (
            "expected-leaf archive container format is invalid"
        ),
        ExpectedLeafArchiveCode.ARCHIVE_CONTENT: (
            "expected-leaf archive content does not match its inventory"
        ),
        ExpectedLeafArchiveCode.MEMBERSHIP_MISMATCH: (
            "expected-leaf archive membership does not match"
        ),
    }
)


class ExpectedLeafArchiveValidationError(ValueError):
    """One fixed coded validation failure without untrusted text."""

    def __init__(self, code: ExpectedLeafArchiveCode) -> None:
        if type(code) is not ExpectedLeafArchiveCode:
            raise TypeError("expected-leaf archive code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class ExpectedLeafArchiveTypeError(ValueError):
    """A typed expected-leaf archive object violates its exact contract."""


def _fail(code: ExpectedLeafArchiveCode) -> None:
    raise ExpectedLeafArchiveValidationError(code) from None


def _sha256_text(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ExpectedLeafArchiveTypeError(
            name + " must be a lowercase SHA-256"
        )
    return value


def _case_authority_id(value: object) -> str:
    if type(value) is not str:
        raise TypeError("case_authority_id must be an exact string")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        raise ExpectedLeafArchiveTypeError(
            "case_authority_id must contain only ASCII"
        ) from None
    if (
        not encoded
        or len(encoded) > MAXIMUM_CASE_AUTHORITY_ID_BYTES
        or _CASE_AUTHORITY_ID_RE.fullmatch(value) is None
    ):
        raise ExpectedLeafArchiveTypeError(
            "case_authority_id is not a canonical stable token"
        )
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
        raise ExpectedLeafArchiveTypeError(
            name + " is outside its exact bound"
        )
    return value


def _domain_sha256(domain: str, payload: bytes, *, maximum: int) -> str:
    if type(domain) is not str or type(payload) is not bytes:
        raise TypeError("digest inputs must have exact types")
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        raise TypeError("digest domain must be ASCII") from None
    if (
        not domain_bytes
        or len(domain_bytes) > 256
        or b"\x00" in domain_bytes
        or not payload
        or len(payload) > maximum
    ):
        raise ExpectedLeafArchiveTypeError(
            "digest input is outside its exact bound"
        )
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def expected_leaf_archive_bundle_domain_sha256(bundle_bytes: bytes) -> str:
    """Return the expected-evidence bundle-domain digest of exact bytes."""

    return _domain_sha256(
        EXPECTED_EVIDENCE_LEAF_BUNDLE_DIGEST_DOMAIN,
        bundle_bytes,
        maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES,
    )


def expected_leaf_archive_inventory_sha256(inventory_bytes: bytes) -> str:
    """Return the inventory artifact-domain digest of exact inventory bytes."""

    return _domain_sha256(
        EXPECTED_LEAF_ARCHIVE_INVENTORY_DIGEST_DOMAIN,
        inventory_bytes,
        maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES,
    )


@dataclass(frozen=True)
class ExpectedLeafArchiveMemberV1:
    """One unique ordinary content identity in the archive."""

    content_byte_count: int
    content_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafArchiveMemberV1:
            raise TypeError("expected-leaf archive member must be exact")
        _bounded_integer(
            self.content_byte_count,
            name="content_byte_count",
            maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES,
            allow_zero=False,
        )
        _sha256_text(self.content_sha256, name="content_sha256")


@dataclass(frozen=True)
class ExpectedLeafArchiveObjectV1:
    """One exact stable case identity resolved to one private bundle."""

    role_id: str
    case_authority_id: str
    bundle_byte_count: int
    bundle_plain_sha256: str
    bundle_domain_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafArchiveObjectV1:
            raise TypeError("expected-leaf archive object must be exact")
        if type(self.role_id) is not str:
            raise TypeError("role_id must be an exact string")
        if self.role_id != EXPECTED_LEAF_ARCHIVE_ROLE_ID:
            raise ExpectedLeafArchiveTypeError(
                "role_id is not the fixed expected-leaf role"
            )
        _case_authority_id(self.case_authority_id)
        _bounded_integer(
            self.bundle_byte_count,
            name="bundle_byte_count",
            maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES,
            allow_zero=False,
        )
        _sha256_text(
            self.bundle_plain_sha256,
            name="bundle_plain_sha256",
        )
        _sha256_text(
            self.bundle_domain_sha256,
            name="bundle_domain_sha256",
        )


@dataclass(frozen=True)
class ExpectedLeafArchiveInventoryV1:
    """External inventory for one exact private expected-leaf archive."""

    archive_byte_count: int
    archive_sha256: str
    members: Tuple[ExpectedLeafArchiveMemberV1, ...]
    expected_leaf_objects: Tuple[ExpectedLeafArchiveObjectV1, ...]
    archive_format_id: str = field(
        default=EXPECTED_LEAF_ARCHIVE_FORMAT_ID,
        init=False,
    )
    artifact_type: str = field(
        default=EXPECTED_LEAF_ARCHIVE_INVENTORY_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafArchiveInventoryV1:
            raise TypeError("expected-leaf archive inventory must be exact")
        if self.archive_format_id != EXPECTED_LEAF_ARCHIVE_FORMAT_ID:
            raise ExpectedLeafArchiveTypeError(
                "archive format identifier differs"
            )
        if (
            self.artifact_type
            != EXPECTED_LEAF_ARCHIVE_INVENTORY_ARTIFACT_TYPE
        ):
            raise ExpectedLeafArchiveTypeError(
                "inventory artifact type differs"
            )
        if self.format_version != "1":
            raise ExpectedLeafArchiveTypeError(
                "inventory format version differs"
            )
        _bounded_integer(
            self.archive_byte_count,
            name="archive_byte_count",
            maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES,
            allow_zero=False,
        )
        _sha256_text(self.archive_sha256, name="archive_sha256")
        if type(self.members) is not tuple or not self.members:
            raise TypeError("members must be a nonempty exact tuple")
        if len(self.members) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES:
            raise ExpectedLeafArchiveTypeError(
                "too many expected-leaf archive members"
            )
        if any(
            type(item) is not ExpectedLeafArchiveMemberV1
            for item in self.members
        ):
            raise TypeError("members must contain exact member records")
        for item in self.members:
            ExpectedLeafArchiveMemberV1.__post_init__(item)
        member_keys = tuple(
            (item.content_sha256, item.content_byte_count)
            for item in self.members
        )
        if member_keys != tuple(sorted(set(member_keys))):
            raise ExpectedLeafArchiveTypeError(
                "members must be sorted, unique, and alias-free"
            )
        if (
            sum(item.content_byte_count for item in self.members)
            > MAXIMUM_EXPECTED_LEAF_ARCHIVE_EXPANDED_BYTES
        ):
            raise ExpectedLeafArchiveTypeError(
                "expected-leaf expanded bytes exceed their ceiling"
            )
        if (
            type(self.expected_leaf_objects) is not tuple
            or not self.expected_leaf_objects
        ):
            raise TypeError(
                "expected_leaf_objects must be a nonempty exact tuple"
            )
        if (
            len(self.expected_leaf_objects)
            > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES
        ):
            raise ExpectedLeafArchiveTypeError(
                "too many expected-leaf archive objects"
            )
        if any(
            type(item) is not ExpectedLeafArchiveObjectV1
            for item in self.expected_leaf_objects
        ):
            raise TypeError(
                "expected_leaf_objects must contain exact object records"
            )
        for item in self.expected_leaf_objects:
            ExpectedLeafArchiveObjectV1.__post_init__(item)
        case_ids = tuple(
            item.case_authority_id for item in self.expected_leaf_objects
        )
        if case_ids != tuple(sorted(set(case_ids))):
            raise ExpectedLeafArchiveTypeError(
                "expected-leaf objects must be sorted by unique case identity"
            )
        object_member_keys = tuple(
            (item.bundle_plain_sha256, item.bundle_byte_count)
            for item in self.expected_leaf_objects
        )
        if len(set(object_member_keys)) != len(object_member_keys):
            raise ExpectedLeafArchiveTypeError(
                "expected-leaf object content aliases are forbidden"
            )
        if set(object_member_keys) != set(member_keys):
            raise ExpectedLeafArchiveTypeError(
                "objects and archive members must form an exact bijection"
            )


@dataclass(frozen=True)
class ValidatedExpectedLeafArchiveMemberV1:
    """One immutable member read from fully reconciled archive bytes."""

    content_byte_count: int
    content_sha256: str
    content_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not ValidatedExpectedLeafArchiveMemberV1:
            raise TypeError("validated expected-leaf member must be exact")
        _bounded_integer(
            self.content_byte_count,
            name="content_byte_count",
            maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES,
            allow_zero=False,
        )
        _sha256_text(self.content_sha256, name="content_sha256")
        if type(self.content_bytes) is not bytes:
            raise TypeError("content_bytes must be exact immutable bytes")


@dataclass(frozen=True)
class ValidatedExpectedLeafArchiveV1:
    """One fully reconciled inventory/archive pair."""

    inventory: ExpectedLeafArchiveInventoryV1
    inventory_bytes: bytes
    inventory_file_sha256: str
    inventory_sha256: str
    archive_bytes: bytes
    archive_sha256: str
    members: Tuple[ValidatedExpectedLeafArchiveMemberV1, ...]

    def __post_init__(self) -> None:
        if type(self) is not ValidatedExpectedLeafArchiveV1:
            raise TypeError("validated expected-leaf archive must be exact")
        if type(self.inventory) is not ExpectedLeafArchiveInventoryV1:
            raise TypeError("inventory must be an exact inventory")
        if type(self.inventory_bytes) is not bytes:
            raise TypeError("inventory_bytes must be exact immutable bytes")
        if type(self.archive_bytes) is not bytes:
            raise TypeError("archive_bytes must be exact immutable bytes")
        _sha256_text(
            self.inventory_file_sha256,
            name="inventory_file_sha256",
        )
        _sha256_text(self.inventory_sha256, name="inventory_sha256")
        _sha256_text(self.archive_sha256, name="archive_sha256")
        if type(self.members) is not tuple or any(
            type(item) is not ValidatedExpectedLeafArchiveMemberV1
            for item in self.members
        ):
            raise TypeError("members must be an exact member tuple")


@dataclass(frozen=True)
class ExpectedLeafArchiveMembershipRequestV1:
    """One case/bundle selection in an exact full-inventory batch."""

    role_id: str
    case_authority_id: str
    bundle_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not ExpectedLeafArchiveMembershipRequestV1:
            raise TypeError("expected-leaf membership request must be exact")
        if type(self.role_id) is not str:
            raise TypeError("role_id must be an exact string")
        if self.role_id != EXPECTED_LEAF_ARCHIVE_ROLE_ID:
            raise ExpectedLeafArchiveTypeError(
                "role_id is not the fixed expected-leaf role"
            )
        _case_authority_id(self.case_authority_id)
        if type(self.bundle_bytes) is not bytes:
            raise TypeError("bundle_bytes must be exact immutable bytes")
        if (
            not self.bundle_bytes
            or len(self.bundle_bytes)
            > MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES
        ):
            raise ExpectedLeafArchiveTypeError(
                "bundle_bytes are outside their exact byte bound"
            )


@dataclass(frozen=True)
class ValidatedExpectedLeafArchiveMembershipV1:
    """Path-free byte membership for one stable case identity."""

    archive_sha256: str
    inventory_file_sha256: str
    inventory_sha256: str
    role_id: str
    case_authority_id: str
    bundle_byte_count: int
    bundle_plain_sha256: str
    bundle_domain_sha256: str
    artifact_type: str = field(
        default=EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not ValidatedExpectedLeafArchiveMembershipV1:
            raise TypeError("expected-leaf membership receipt must be exact")
        if (
            self.artifact_type
            != EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE
        ):
            raise ExpectedLeafArchiveTypeError(
                "membership receipt artifact type differs"
            )
        if self.format_version != "1":
            raise ExpectedLeafArchiveTypeError(
                "membership receipt format version differs"
            )
        _sha256_text(self.archive_sha256, name="archive_sha256")
        _sha256_text(
            self.inventory_file_sha256,
            name="inventory_file_sha256",
        )
        _sha256_text(self.inventory_sha256, name="inventory_sha256")
        if type(self.role_id) is not str:
            raise TypeError("role_id must be an exact string")
        if self.role_id != EXPECTED_LEAF_ARCHIVE_ROLE_ID:
            raise ExpectedLeafArchiveTypeError(
                "role_id is not the fixed expected-leaf role"
            )
        _case_authority_id(self.case_authority_id)
        _bounded_integer(
            self.bundle_byte_count,
            name="bundle_byte_count",
            maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES,
            allow_zero=False,
        )
        _sha256_text(
            self.bundle_plain_sha256,
            name="bundle_plain_sha256",
        )
        _sha256_text(
            self.bundle_domain_sha256,
            name="bundle_domain_sha256",
        )


@dataclass(frozen=True)
class ValidatedExpectedLeafArchiveMembershipSetV1:
    """One raw-byte-validated archive and its batch-exact memberships."""

    expected_leaf_archive: ValidatedExpectedLeafArchiveV1
    memberships: Tuple[ValidatedExpectedLeafArchiveMembershipV1, ...]

    def __post_init__(self) -> None:
        if type(self) is not ValidatedExpectedLeafArchiveMembershipSetV1:
            raise TypeError("expected-leaf membership set must be exact")
        if (
            type(self.expected_leaf_archive)
            is not ValidatedExpectedLeafArchiveV1
        ):
            raise TypeError(
                "expected_leaf_archive must be an exact validated archive"
            )
        if type(self.memberships) is not tuple or any(
            type(item) is not ValidatedExpectedLeafArchiveMembershipV1
            for item in self.memberships
        ):
            raise TypeError("memberships must be an exact receipt tuple")


@dataclass(frozen=True)
class ResolvedExpectedLeafArchiveObjectV1:
    """One exact case object derived only from revalidated raw archive bytes."""

    expected_leaf_archive: ValidatedExpectedLeafArchiveV1
    membership: ValidatedExpectedLeafArchiveMembershipV1
    bundle_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not ResolvedExpectedLeafArchiveObjectV1:
            raise TypeError("resolved expected-leaf object must be exact")
        if (
            type(self.expected_leaf_archive)
            is not ValidatedExpectedLeafArchiveV1
        ):
            raise TypeError(
                "expected_leaf_archive must be an exact validated archive"
            )
        if (
            type(self.membership)
            is not ValidatedExpectedLeafArchiveMembershipV1
        ):
            raise TypeError("membership must be an exact receipt")
        if type(self.bundle_bytes) is not bytes:
            raise TypeError("bundle_bytes must be exact immutable bytes")


def _validate_json_tree(value: object) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_EXPECTED_LEAF_ARCHIVE_JSON_NODES:
            raise ExpectedLeafArchiveTypeError(
                "inventory tree has too many values"
            )
        if depth > MAXIMUM_EXPECTED_LEAF_ARCHIVE_JSON_DEPTH:
            raise ExpectedLeafArchiveTypeError(
                "inventory tree is too deeply nested"
            )
        if type(current) is int:
            if current < 0 or current > _MAXIMUM_SAFE_INTEGER:
                raise ExpectedLeafArchiveTypeError(
                    "inventory integer is outside range"
                )
            continue
        if type(current) is str:
            try:
                encoded = current.encode("utf-8", "strict")
            except UnicodeError:
                raise ExpectedLeafArchiveTypeError(
                    "inventory string is invalid Unicode"
                ) from None
            if (
                len(encoded)
                > MAXIMUM_EXPECTED_LEAF_ARCHIVE_STRING_BYTES
            ):
                raise ExpectedLeafArchiveTypeError(
                    "inventory string exceeds its byte ceiling"
                )
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    raise ExpectedLeafArchiveTypeError(
                        "inventory object key must be a string"
                    )
                stack.append((item, depth + 1))
                stack.append((key, depth + 1))
            continue
        raise ExpectedLeafArchiveTypeError(
            "inventory tree contains an invalid type"
        )


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
        raise ExpectedLeafArchiveTypeError(
            "inventory cannot be encoded canonically"
        ) from error
    if not encoded or len(encoded) > maximum:
        raise ExpectedLeafArchiveTypeError(
            "inventory bytes exceed their ceiling"
        )
    return encoded


def _inventory_tree(value: ExpectedLeafArchiveInventoryV1) -> dict:
    if type(value) is not ExpectedLeafArchiveInventoryV1:
        raise TypeError("expected-leaf archive inventory must be exact")
    return {
        "archive_byte_count": value.archive_byte_count,
        "archive_format_id": value.archive_format_id,
        "archive_sha256": value.archive_sha256,
        "artifact_type": value.artifact_type,
        "expected_leaf_objects": [
            {
                "bundle_byte_count": item.bundle_byte_count,
                "bundle_domain_sha256": item.bundle_domain_sha256,
                "bundle_plain_sha256": item.bundle_plain_sha256,
                "case_authority_id": item.case_authority_id,
                "role_id": item.role_id,
            }
            for item in value.expected_leaf_objects
        ],
        "format_version": value.format_version,
        "members": [
            {
                "content_byte_count": item.content_byte_count,
                "content_sha256": item.content_sha256,
            }
            for item in value.members
        ],
    }


def expected_leaf_archive_inventory_bytes(
    value: ExpectedLeafArchiveInventoryV1,
) -> bytes:
    """Return exact canonical external inventory bytes."""

    if type(value) is not ExpectedLeafArchiveInventoryV1:
        raise TypeError("expected-leaf archive inventory must be exact")
    ExpectedLeafArchiveInventoryV1.__post_init__(value)
    return _canonical_json_bytes(
        _inventory_tree(value),
        maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES,
    )


def _membership_tree(
    value: ValidatedExpectedLeafArchiveMembershipV1,
) -> dict:
    if type(value) is not ValidatedExpectedLeafArchiveMembershipV1:
        raise TypeError("expected-leaf membership receipt must be exact")
    return {
        "archive_sha256": value.archive_sha256,
        "artifact_type": value.artifact_type,
        "bundle_byte_count": value.bundle_byte_count,
        "bundle_domain_sha256": value.bundle_domain_sha256,
        "bundle_plain_sha256": value.bundle_plain_sha256,
        "case_authority_id": value.case_authority_id,
        "format_version": value.format_version,
        "inventory_file_sha256": value.inventory_file_sha256,
        "inventory_sha256": value.inventory_sha256,
        "role_id": value.role_id,
    }


def expected_leaf_archive_membership_receipt_bytes(
    value: ValidatedExpectedLeafArchiveMembershipV1,
) -> bytes:
    """Return canonical bytes for one non-decision membership receipt."""

    if type(value) is not ValidatedExpectedLeafArchiveMembershipV1:
        raise TypeError("expected-leaf membership receipt must be exact")
    ValidatedExpectedLeafArchiveMembershipV1.__post_init__(value)
    return _canonical_json_bytes(
        _membership_tree(value),
        maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES,
    )


def expected_leaf_archive_membership_receipt_sha256(
    value: ValidatedExpectedLeafArchiveMembershipV1,
) -> str:
    """Return the membership-receipt artifact-domain digest."""

    return _domain_sha256(
        EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_RECEIPT_DIGEST_DOMAIN,
        expected_leaf_archive_membership_receipt_bytes(value),
        maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES,
    )


def _lexical_preflight(value: bytes) -> None:
    if type(value) is not bytes:
        _fail(ExpectedLeafArchiveCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES
    ):
        _fail(ExpectedLeafArchiveCode.RESOURCE)
    if any(byte >= 0x80 for byte in value):
        _fail(ExpectedLeafArchiveCode.INVENTORY_JSON)
    depth = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            if not escaped and byte == 0x22:
                in_string = False
                continue
            string_bytes += 1
            if (
                string_bytes
                > MAXIMUM_EXPECTED_LEAF_ARCHIVE_STRING_BYTES
            ):
                _fail(ExpectedLeafArchiveCode.RESOURCE)
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > MAXIMUM_EXPECTED_LEAF_ARCHIVE_JSON_DEPTH:
                _fail(ExpectedLeafArchiveCode.INVENTORY_JSON)
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _fail(ExpectedLeafArchiveCode.INVENTORY_JSON)
    if in_string or depth != 0:
        _fail(ExpectedLeafArchiveCode.INVENTORY_JSON)


def _strict_inventory_tree(value: bytes) -> object:
    _lexical_preflight(value)
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(ExpectedLeafArchiveCode.INVENTORY_JSON)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ExpectedLeafArchiveTypeError("duplicate inventory key")
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise ExpectedLeafArchiveTypeError(
                "inventory integer token is too large"
            )
        result = int(token, 10)
        if result < 0 or result > _MAXIMUM_SAFE_INTEGER:
            raise ExpectedLeafArchiveTypeError(
                "inventory integer is outside range"
            )
        return result

    def reject_number(_token):
        raise ExpectedLeafArchiveTypeError(
            "inventory admits integers only"
        )

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
        _validate_json_tree(tree)
    except (
        ExpectedLeafArchiveTypeError,
        TypeError,
        ValueError,
        RecursionError,
    ):
        _fail(ExpectedLeafArchiveCode.INVENTORY_JSON)
    try:
        canonical = _canonical_json_bytes(
            tree,
            maximum=MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES,
        )
    except (ExpectedLeafArchiveTypeError, TypeError):
        _fail(ExpectedLeafArchiveCode.INVENTORY_JSON)
    if canonical != value:
        _fail(ExpectedLeafArchiveCode.INVENTORY_NONCANONICAL)
    return tree


def _keys(value: object, expected: Tuple[str, ...]) -> dict:
    if type(value) is not dict or tuple(sorted(value)) != tuple(
        sorted(expected)
    ):
        raise ExpectedLeafArchiveTypeError(
            "inventory object has invalid keys"
        )
    return value


_INVENTORY_KEYS = (
    "archive_byte_count",
    "archive_format_id",
    "archive_sha256",
    "artifact_type",
    "expected_leaf_objects",
    "format_version",
    "members",
)
_MEMBER_KEYS = ("content_byte_count", "content_sha256")
_EXPECTED_LEAF_OBJECT_KEYS = (
    "bundle_byte_count",
    "bundle_domain_sha256",
    "bundle_plain_sha256",
    "case_authority_id",
    "role_id",
)


def _inventory_from_tree(value: object) -> ExpectedLeafArchiveInventoryV1:
    tree = _keys(value, _INVENTORY_KEYS)
    if (
        tree["artifact_type"]
        != EXPECTED_LEAF_ARCHIVE_INVENTORY_ARTIFACT_TYPE
    ):
        raise ExpectedLeafArchiveTypeError(
            "inventory artifact type differs"
        )
    if tree["archive_format_id"] != EXPECTED_LEAF_ARCHIVE_FORMAT_ID:
        raise ExpectedLeafArchiveTypeError(
            "archive format identifier differs"
        )
    if tree["format_version"] != "1":
        raise ExpectedLeafArchiveTypeError(
            "inventory format version differs"
        )
    if type(tree["members"]) is not list or not tree["members"]:
        raise ExpectedLeafArchiveTypeError(
            "members must be a nonempty list"
        )
    if (
        type(tree["expected_leaf_objects"]) is not list
        or not tree["expected_leaf_objects"]
    ):
        raise ExpectedLeafArchiveTypeError(
            "expected_leaf_objects must be a nonempty list"
        )
    if (
        len(tree["members"]) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES
        or len(tree["expected_leaf_objects"])
        > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES
    ):
        raise ExpectedLeafArchiveTypeError(
            "inventory has too many records"
        )
    members = tuple(
        ExpectedLeafArchiveMemberV1(**_keys(item, _MEMBER_KEYS))
        for item in tree["members"]
    )
    objects = tuple(
        ExpectedLeafArchiveObjectV1(
            **_keys(item, _EXPECTED_LEAF_OBJECT_KEYS)
        )
        for item in tree["expected_leaf_objects"]
    )
    return ExpectedLeafArchiveInventoryV1(
        archive_byte_count=tree["archive_byte_count"],
        archive_sha256=tree["archive_sha256"],
        members=members,
        expected_leaf_objects=objects,
    )


def _snapshot_members(value: object) -> Tuple[bytes, ...]:
    if type(value) is not tuple or not value:
        raise TypeError("bundle members must be a nonempty exact tuple")
    if len(value) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES:
        raise ExpectedLeafArchiveTypeError(
            "too many expected-leaf archive members"
        )
    result = []
    identities = set()
    expanded = 0
    for raw in value:
        if type(raw) is not bytes:
            raise TypeError(
                "bundle members must be exact immutable bytes"
            )
        if (
            not raw
            or len(raw) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES
        ):
            raise ExpectedLeafArchiveTypeError(
                "bundle member is outside its exact byte bound"
            )
        identity = (hashlib.sha256(raw).hexdigest(), len(raw))
        if identity in identities:
            raise ExpectedLeafArchiveTypeError(
                "duplicate bundle content aliases are forbidden"
            )
        identities.add(identity)
        expanded += len(raw)
        if expanded > MAXIMUM_EXPECTED_LEAF_ARCHIVE_EXPANDED_BYTES:
            raise ExpectedLeafArchiveTypeError(
                "expected-leaf expanded bytes exceed their ceiling"
            )
        result.append(raw)
    return tuple(result)


def _member_records(
    members: Tuple[bytes, ...],
) -> Tuple[ExpectedLeafArchiveMemberV1, ...]:
    return tuple(
        ExpectedLeafArchiveMemberV1(
            content_byte_count=len(raw),
            content_sha256=hashlib.sha256(raw).hexdigest(),
        )
        for raw in sorted(
            members,
            key=lambda item: (
                hashlib.sha256(item).hexdigest(),
                len(item),
                item,
            ),
        )
    )


def _member_name(digest: str, byte_count: int) -> str:
    return "objects/{}-{:016x}.bin".format(digest, byte_count)


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_EXPECTED_LEAF_ARCHIVE_TIME)
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


def build_expected_leaf_archive(
    bundle_members: Tuple[bytes, ...],
) -> bytes:
    """Build deterministic path-free ZIP bytes for unique private bundles."""

    members = _snapshot_members(bundle_members)
    ordered = sorted(
        members,
        key=lambda raw: (hashlib.sha256(raw).hexdigest(), len(raw), raw),
    )
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
                digest = hashlib.sha256(raw).hexdigest()
                archive.writestr(
                    _zip_info(_member_name(digest, len(raw))),
                    raw,
                )
    except (
        OSError,
        RuntimeError,
        ValueError,
        zipfile.LargeZipFile,
    ) as error:
        raise ExpectedLeafArchiveTypeError(
            "expected-leaf archive cannot be built deterministically"
        ) from error
    result = output.getvalue()
    if (
        not result
        or len(result) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES
    ):
        raise ExpectedLeafArchiveTypeError(
            "expected-leaf archive bytes exceed their ceiling"
        )
    return result


def build_expected_leaf_archive_inventory(
    archive_bytes: bytes,
    bundle_members: Tuple[bytes, ...],
    expected_leaf_objects: Tuple[ExpectedLeafArchiveObjectV1, ...],
) -> ExpectedLeafArchiveInventoryV1:
    """Build an exact external inventory for deterministic captured bytes."""

    if type(archive_bytes) is not bytes:
        raise TypeError("archive_bytes must be exact immutable bytes")
    members = _snapshot_members(bundle_members)
    if build_expected_leaf_archive(members) != archive_bytes:
        raise ExpectedLeafArchiveTypeError(
            "archive bytes do not match deterministic bundle members"
        )
    if type(expected_leaf_objects) is not tuple:
        raise TypeError("expected_leaf_objects must be an exact tuple")
    raw_by_identity = {
        (hashlib.sha256(raw).hexdigest(), len(raw)): raw
        for raw in members
    }
    if any(
        type(item) is not ExpectedLeafArchiveObjectV1
        for item in expected_leaf_objects
    ):
        raise TypeError(
            "expected_leaf_objects must contain exact object records"
        )
    for item in expected_leaf_objects:
        ExpectedLeafArchiveObjectV1.__post_init__(item)
        raw = raw_by_identity.get(
            (item.bundle_plain_sha256, item.bundle_byte_count)
        )
        if (
            raw is None
            or item.bundle_domain_sha256
            != expected_leaf_archive_bundle_domain_sha256(raw)
        ):
            raise ExpectedLeafArchiveTypeError(
                "expected-leaf object digest does not match member bytes"
            )
    return ExpectedLeafArchiveInventoryV1(
        archive_byte_count=len(archive_bytes),
        archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        members=_member_records(members),
        expected_leaf_objects=expected_leaf_objects,
    )


def _preflight_zip_container(archive_bytes: bytes) -> None:
    """Bound and close the central directory before ZIP allocation."""

    if len(archive_bytes) < 22:
        _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
    end_record = archive_bytes[-22:]
    if end_record[:4] != b"PK\x05\x06":
        _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
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
        or entry_count > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES
        or central_size == 0
        or comment_size != 0
        or central_offset + central_size != len(archive_bytes) - 22
    ):
        _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
    central_end = central_offset + central_size
    position = central_offset
    observed_entries = 0
    expanded_bytes = 0
    while position < central_end:
        if (
            central_end - position < 46
            or archive_bytes[position : position + 4] != b"PK\x01\x02"
        ):
            _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
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
            or uncompressed_size
            > MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES
            or uncompressed_size == 0
            or name_size == 0
            or name_size > 128
            or extra_size != 0
            or member_comment_size != 0
            or member_disk != 0
            or internal_attr != 0
            or external_attr != (_FIXED_UNIX_MODE << 16)
            or local_offset >= central_offset
        ):
            _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
        name_start = position + 46
        name_bytes = archive_bytes[name_start : name_start + name_size]
        try:
            name = name_bytes.decode("ascii", "strict")
        except UnicodeError:
            _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
        if _MEMBER_NAME_RE.fullmatch(name) is None:
            _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
        observed_entries += 1
        expanded_bytes += uncompressed_size
        if (
            observed_entries > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES
            or expanded_bytes
            > MAXIMUM_EXPECTED_LEAF_ARCHIVE_EXPANDED_BYTES
        ):
            _fail(ExpectedLeafArchiveCode.RESOURCE)
        position += record_size
    if position != central_end or observed_entries != entry_count:
        _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)


def _read_archive_members(
    archive_bytes: bytes,
) -> Tuple[ValidatedExpectedLeafArchiveMemberV1, ...]:
    _preflight_zip_container(archive_bytes)
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), mode="r") as archive:
            if archive.comment != b"":
                _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
            infos = archive.infolist()
            if (
                not infos
                or len(infos) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES
            ):
                _fail(ExpectedLeafArchiveCode.RESOURCE)
            names = tuple(info.filename for info in infos)
            if names != tuple(sorted(set(names))):
                _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
            expanded = 0
            contents = []
            for info in infos:
                try:
                    name_bytes = info.filename.encode("ascii", "strict")
                except UnicodeError:
                    _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
                if (
                    not name_bytes
                    or len(name_bytes) > 128
                    or _MEMBER_NAME_RE.fullmatch(info.filename) is None
                    or info.orig_filename != info.filename
                    or info.date_time != FIXED_EXPECTED_LEAF_ARCHIVE_TIME
                    or info.compress_type != zipfile.ZIP_STORED
                    or info.create_system != 3
                    or info.create_version != 20
                    or info.extract_version != 20
                    or info.external_attr != (_FIXED_UNIX_MODE << 16)
                    or info.internal_attr != 0
                    or info.flag_bits != 0
                    or info.extra != b""
                    or info.comment != b""
                    or info.is_dir()
                    or info.file_size != info.compress_size
                    or info.file_size == 0
                    or info.file_size
                    > MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES
                ):
                    _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
                expanded += info.file_size
                if (
                    expanded
                    > MAXIMUM_EXPECTED_LEAF_ARCHIVE_EXPANDED_BYTES
                ):
                    _fail(ExpectedLeafArchiveCode.RESOURCE)
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
                    _fail(ExpectedLeafArchiveCode.ARCHIVE_CONTENT)
                digest = hashlib.sha256(raw).hexdigest()
                if (
                    len(raw) != info.file_size
                    or trailing != b""
                    or info.filename != _member_name(digest, len(raw))
                ):
                    _fail(ExpectedLeafArchiveCode.ARCHIVE_CONTENT)
                contents.append(raw)
    except ExpectedLeafArchiveValidationError:
        raise
    except (
        EOFError,
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ):
        _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
    ordered = sorted(
        contents,
        key=lambda raw: (hashlib.sha256(raw).hexdigest(), len(raw), raw),
    )
    if len(
        {(hashlib.sha256(raw).hexdigest(), len(raw)) for raw in ordered}
    ) != len(ordered):
        _fail(ExpectedLeafArchiveCode.ARCHIVE_CONTENT)
    expected_names = tuple(
        _member_name(hashlib.sha256(raw).hexdigest(), len(raw))
        for raw in ordered
    )
    if expected_names != names:
        _fail(ExpectedLeafArchiveCode.ARCHIVE_CONTENT)
    return tuple(
        ValidatedExpectedLeafArchiveMemberV1(
            content_byte_count=len(raw),
            content_sha256=hashlib.sha256(raw).hexdigest(),
            content_bytes=raw,
        )
        for raw in ordered
    )


def validate_expected_leaf_archive(
    inventory_bytes: bytes,
    archive_bytes: bytes,
) -> ValidatedExpectedLeafArchiveV1:
    """Strictly reconcile canonical inventory and exact captured ZIP bytes."""

    if type(inventory_bytes) is not bytes or type(archive_bytes) is not bytes:
        _fail(ExpectedLeafArchiveCode.INPUT_TYPE)
    if (
        not archive_bytes
        or len(archive_bytes) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES
    ):
        _fail(ExpectedLeafArchiveCode.RESOURCE)
    tree = _strict_inventory_tree(inventory_bytes)
    try:
        inventory = _inventory_from_tree(tree)
        if (
            expected_leaf_archive_inventory_bytes(inventory)
            != inventory_bytes
        ):
            raise ExpectedLeafArchiveTypeError(
                "inventory projection differs"
            )
    except (ExpectedLeafArchiveTypeError, TypeError, ValueError):
        _fail(ExpectedLeafArchiveCode.INVENTORY_SCHEMA)
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    if (
        inventory.archive_byte_count != len(archive_bytes)
        or inventory.archive_sha256 != archive_sha256
    ):
        _fail(ExpectedLeafArchiveCode.ARCHIVE_CONTENT)
    members = _read_archive_members(archive_bytes)
    observed_records = tuple(
        ExpectedLeafArchiveMemberV1(
            content_byte_count=item.content_byte_count,
            content_sha256=item.content_sha256,
        )
        for item in members
    )
    if observed_records != inventory.members:
        _fail(ExpectedLeafArchiveCode.ARCHIVE_CONTENT)
    try:
        rebuilt = build_expected_leaf_archive(
            tuple(item.content_bytes for item in members)
        )
    except (ExpectedLeafArchiveTypeError, TypeError, ValueError):
        _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
    if rebuilt != archive_bytes:
        _fail(ExpectedLeafArchiveCode.ARCHIVE_FORMAT)
    raw_by_identity = {
        (item.content_sha256, item.content_byte_count): item.content_bytes
        for item in members
    }
    for item in inventory.expected_leaf_objects:
        raw = raw_by_identity.get(
            (item.bundle_plain_sha256, item.bundle_byte_count)
        )
        if (
            raw is None
            or expected_leaf_archive_bundle_domain_sha256(raw)
            != item.bundle_domain_sha256
        ):
            _fail(ExpectedLeafArchiveCode.ARCHIVE_CONTENT)
    inventory_file_sha256 = hashlib.sha256(inventory_bytes).hexdigest()
    return ValidatedExpectedLeafArchiveV1(
        inventory=inventory,
        inventory_bytes=inventory_bytes,
        inventory_file_sha256=inventory_file_sha256,
        inventory_sha256=expected_leaf_archive_inventory_sha256(
            inventory_bytes
        ),
        archive_bytes=archive_bytes,
        archive_sha256=archive_sha256,
        members=members,
    )


def _membership_from_archive(
    value: ValidatedExpectedLeafArchiveV1,
    *,
    role_id: str,
    case_authority_id: str,
    bundle_bytes: bytes,
) -> ValidatedExpectedLeafArchiveMembershipV1:
    records = tuple(
        item
        for item in value.inventory.expected_leaf_objects
        if item.role_id == role_id
        and item.case_authority_id == case_authority_id
    )
    if len(records) != 1:
        _fail(ExpectedLeafArchiveCode.MEMBERSHIP_MISMATCH)
    record = records[0]
    plain_sha256 = hashlib.sha256(bundle_bytes).hexdigest()
    domain_sha256 = expected_leaf_archive_bundle_domain_sha256(
        bundle_bytes
    )
    if (
        record.bundle_byte_count != len(bundle_bytes)
        or record.bundle_plain_sha256 != plain_sha256
        or record.bundle_domain_sha256 != domain_sha256
        or not any(
            item.content_byte_count == len(bundle_bytes)
            and item.content_sha256 == plain_sha256
            and item.content_bytes == bundle_bytes
            for item in value.members
        )
    ):
        _fail(ExpectedLeafArchiveCode.MEMBERSHIP_MISMATCH)
    return ValidatedExpectedLeafArchiveMembershipV1(
        archive_sha256=value.archive_sha256,
        inventory_file_sha256=value.inventory_file_sha256,
        inventory_sha256=value.inventory_sha256,
        role_id=record.role_id,
        case_authority_id=record.case_authority_id,
        bundle_byte_count=record.bundle_byte_count,
        bundle_plain_sha256=record.bundle_plain_sha256,
        bundle_domain_sha256=record.bundle_domain_sha256,
    )


def validate_expected_leaf_archive_memberships(
    inventory_bytes: bytes,
    archive_bytes: bytes,
    requests: Tuple[ExpectedLeafArchiveMembershipRequestV1, ...],
) -> ValidatedExpectedLeafArchiveMembershipSetV1:
    """Validate one sorted batch that exactly covers every inventory object."""

    if type(requests) is not tuple or not requests:
        _fail(ExpectedLeafArchiveCode.INPUT_TYPE)
    if len(requests) > MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES:
        _fail(ExpectedLeafArchiveCode.RESOURCE)
    snapshots = []
    aggregate = 0
    for request in requests:
        if type(request) is not ExpectedLeafArchiveMembershipRequestV1:
            _fail(ExpectedLeafArchiveCode.INPUT_TYPE)
        try:
            ExpectedLeafArchiveMembershipRequestV1.__post_init__(request)
        except (
            ExpectedLeafArchiveTypeError,
            TypeError,
            ValueError,
        ):
            _fail(ExpectedLeafArchiveCode.INPUT_TYPE)
        aggregate += len(request.bundle_bytes)
        if aggregate > MAXIMUM_EXPECTED_LEAF_ARCHIVE_EXPANDED_BYTES:
            _fail(ExpectedLeafArchiveCode.RESOURCE)
        snapshots.append(
            ExpectedLeafArchiveMembershipRequestV1(
                role_id=request.role_id,
                case_authority_id=request.case_authority_id,
                bundle_bytes=request.bundle_bytes,
            )
        )
    request_ids = tuple(item.case_authority_id for item in snapshots)
    if request_ids != tuple(sorted(set(request_ids))):
        _fail(ExpectedLeafArchiveCode.MEMBERSHIP_MISMATCH)
    expected_leaf_archive = validate_expected_leaf_archive(
        inventory_bytes,
        archive_bytes,
    )
    inventory_ids = tuple(
        item.case_authority_id
        for item in expected_leaf_archive.inventory.expected_leaf_objects
    )
    if request_ids != inventory_ids:
        _fail(ExpectedLeafArchiveCode.MEMBERSHIP_MISMATCH)
    memberships = tuple(
        _membership_from_archive(
            expected_leaf_archive,
            role_id=request.role_id,
            case_authority_id=request.case_authority_id,
            bundle_bytes=request.bundle_bytes,
        )
        for request in snapshots
    )
    return ValidatedExpectedLeafArchiveMembershipSetV1(
        expected_leaf_archive=expected_leaf_archive,
        memberships=memberships,
    )


def resolve_expected_leaf_archive_object(
    inventory_bytes: bytes,
    archive_bytes: bytes,
    *,
    role_id: str,
    case_authority_id: str,
) -> ResolvedExpectedLeafArchiveObjectV1:
    """Resolve one case's bytes solely from a fully revalidated archive."""

    if type(role_id) is not str or type(case_authority_id) is not str:
        _fail(ExpectedLeafArchiveCode.INPUT_TYPE)
    try:
        if role_id != EXPECTED_LEAF_ARCHIVE_ROLE_ID:
            raise ExpectedLeafArchiveTypeError(
                "role_id is not the fixed expected-leaf role"
            )
        _case_authority_id(case_authority_id)
    except (ExpectedLeafArchiveTypeError, TypeError, ValueError):
        _fail(ExpectedLeafArchiveCode.INPUT_TYPE)
    expected_leaf_archive = validate_expected_leaf_archive(
        inventory_bytes,
        archive_bytes,
    )
    records = tuple(
        item
        for item in expected_leaf_archive.inventory.expected_leaf_objects
        if item.role_id == role_id
        and item.case_authority_id == case_authority_id
    )
    if len(records) != 1:
        _fail(ExpectedLeafArchiveCode.MEMBERSHIP_MISMATCH)
    record = records[0]
    matching_members = tuple(
        item
        for item in expected_leaf_archive.members
        if item.content_byte_count == record.bundle_byte_count
        and item.content_sha256 == record.bundle_plain_sha256
    )
    if len(matching_members) != 1:
        _fail(ExpectedLeafArchiveCode.MEMBERSHIP_MISMATCH)
    bundle_bytes = matching_members[0].content_bytes
    membership = _membership_from_archive(
        expected_leaf_archive,
        role_id=role_id,
        case_authority_id=case_authority_id,
        bundle_bytes=bundle_bytes,
    )
    return ResolvedExpectedLeafArchiveObjectV1(
        expected_leaf_archive=expected_leaf_archive,
        membership=membership,
        bundle_bytes=bundle_bytes,
    )


__all__ = [
    "EXPECTED_EVIDENCE_LEAF_BUNDLE_DIGEST_DOMAIN",
    "EXPECTED_LEAF_ARCHIVE_FORMAT_ID",
    "EXPECTED_LEAF_ARCHIVE_INVENTORY_ARTIFACT_TYPE",
    "EXPECTED_LEAF_ARCHIVE_INVENTORY_DIGEST_DOMAIN",
    "EXPECTED_LEAF_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE",
    "EXPECTED_LEAF_ARCHIVE_ROLE_ID",
    "MAXIMUM_EXPECTED_LEAF_ARCHIVE_BYTES",
    "MAXIMUM_EXPECTED_LEAF_ARCHIVE_ENTRIES",
    "MAXIMUM_EXPECTED_LEAF_ARCHIVE_EXPANDED_BYTES",
    "MAXIMUM_EXPECTED_LEAF_ARCHIVE_INVENTORY_BYTES",
    "MAXIMUM_EXPECTED_LEAF_ARCHIVE_MEMBER_BYTES",
    "ExpectedLeafArchiveCode",
    "ExpectedLeafArchiveInventoryV1",
    "ExpectedLeafArchiveMemberV1",
    "ExpectedLeafArchiveMembershipRequestV1",
    "ExpectedLeafArchiveObjectV1",
    "ExpectedLeafArchiveTypeError",
    "ExpectedLeafArchiveValidationError",
    "ResolvedExpectedLeafArchiveObjectV1",
    "ValidatedExpectedLeafArchiveMemberV1",
    "ValidatedExpectedLeafArchiveMembershipSetV1",
    "ValidatedExpectedLeafArchiveMembershipV1",
    "ValidatedExpectedLeafArchiveV1",
    "build_expected_leaf_archive",
    "build_expected_leaf_archive_inventory",
    "expected_leaf_archive_bundle_domain_sha256",
    "expected_leaf_archive_inventory_bytes",
    "expected_leaf_archive_inventory_sha256",
    "expected_leaf_archive_membership_receipt_bytes",
    "expected_leaf_archive_membership_receipt_sha256",
    "resolve_expected_leaf_archive_object",
    "validate_expected_leaf_archive",
    "validate_expected_leaf_archive_memberships",
]
