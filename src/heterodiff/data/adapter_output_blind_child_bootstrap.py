"""Fixed bootstrap and dedicated closure-pipe transport for adapter children.

The bootstrap is passed as exact ``-c`` bytes to an isolated-mode Python
interpreter.  It uses only the standard library until it has reconstructed the
module-content selection already fully validated by the supervisor from
path-free archive bytes received on a dedicated inherited pipe.  Its compact
child parser is not a second implementation of every ZIP custody rule.  A
meta-path loader resolves declared project modules from that selection and,
while it remains installed and receives resolution, raises for undeclared
imports under the protected ``heterodiff`` namespace instead of falling back
to the host import path.

This is a local development mechanism, not a sandbox.  The child retains the
host filesystem, network, native extensions, and process APIs.  The loader
report and call counters are software-generated evidence rather than
executed-source attestation.  Same-process adapter code is not prevented from
mutating Python runtime state, and externally loaded dependencies are not
closed by the project-source archive.  ``external_import_roots`` is a
supervisor-validated static source declaration, not a child runtime import
allowlist.
"""

from __future__ import annotations

import hashlib
from types import MappingProxyType

from .adapter_output_blind_trusted_runtime_profile import (
    OUTPUT_BLIND_TRUSTED_RUNTIME_CALLABLE_NAME,
    OUTPUT_BLIND_TRUSTED_RUNTIME_MODULE_NAME,
    OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES,
)


OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_DOMAIN = (
    "heterodiff.adapter.implementation-closure-pipe.v1"
)
OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_FIELD_NAMES = (
    "implementation_closure_bytes",
    "source_archive_inventory_bytes",
    "source_archive_bytes",
)
MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_BYTES = 4 * 1024 * 1024
MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_INVENTORY_BYTES = 4 * 1024 * 1024
MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_ARCHIVE_BYTES = 32 * 1024 * 1024
MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_BYTES = (
    MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_BYTES
    + MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_INVENTORY_BYTES
    + MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_ARCHIVE_BYTES
    + 2048
)


def _u64(value: int) -> bytes:
    if type(value) is not int or value < 0 or value >= (1 << 64):
        raise TypeError("closure-pipe integer is invalid")
    return value.to_bytes(8, "big")


def build_output_blind_implementation_closure_pipe_frame(
    implementation_closure_bytes: bytes,
    source_archive_inventory_bytes: bytes,
    source_archive_bytes: bytes,
) -> bytes:
    """Build the sole bounded transport admitted on the inherited pipe."""

    values = (
        implementation_closure_bytes,
        source_archive_inventory_bytes,
        source_archive_bytes,
    )
    maxima = (
        MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_BYTES,
        MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_INVENTORY_BYTES,
        MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_ARCHIVE_BYTES,
    )
    if any(
        type(value) is not bytes
        or not value
        or len(value) > maximum
        for value, maximum in zip(values, maxima)
    ):
        raise ValueError("closure-pipe field is outside its fixed bound")
    domain = OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_DOMAIN.encode("ascii")
    names = tuple(
        name.encode("ascii")
        for name in OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_FIELD_NAMES
    )
    parts = [domain, b"\x00", _u64(len(names))]
    for name, value in zip(names, values):
        parts.extend((_u64(len(name)), name, _u64(len(value)), value))
    frame = b"".join(parts)
    if (
        not frame
        or len(frame)
        > MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_BYTES
    ):
        raise ValueError("closure-pipe frame exceeds its fixed bound")
    return frame


# The executable source is deliberately self-contained.  It duplicates the
# small framing vocabulary instead of importing supervisor code from the host.
_CHILD_BOOTSTRAP_SOURCE_TEMPLATE = r'''
import hashlib
import importlib
import importlib.abc
import importlib.util
import io
import json
import os
import re
import sys
import zipfile

PIPE_DOMAIN = b"heterodiff.adapter.implementation-closure-pipe.v1"
PIPE_NAMES = (
    b"implementation_closure_bytes",
    b"source_archive_inventory_bytes",
    b"source_archive_bytes",
)
REQUEST_DOMAIN = b"heterodiff.adapter.output-blind-adapter-child-request.v1"
REQUEST_NAMES = (b"case_input_bytes",)
MODULE_DOMAIN = b"heterodiff.adapter.output-blind-adapter-child-source-module.v1"
MODULE_NAMES = (
    b"module_name",
    b"source_object_id",
    b"source_byte_count",
    b"source_sha256",
)
REPORT_DOMAIN = b"heterodiff.adapter.output-blind-adapter-child-source-load-report.v1"
REPORT_NAMES = (
    b"implementation_closure_sha256",
    b"entrypoint_module_name",
    b"entrypoint_callable_name",
    b"loaded_project_modules",
    b"protected_namespace_host_fallback_count",
)
SUCCESS_DOMAIN = b"heterodiff.adapter.output-blind-adapter-child-success-response.v1"
SUCCESS_NAMES = (
    b"request_frame_sha256",
    b"case_input_sha256",
    b"implementation_closure_sha256",
    b"adapter_id",
    b"adapter_version",
    b"runner_direct_adapt_complete_call_count",
    b"runner_direct_adapt_call_count",
    b"source_load_report_bytes",
    b"adapted_evidence_bundle_bytes",
)
FAILURE_DOMAIN = b"heterodiff.adapter.output-blind-adapter-child-failure-response.v1"
FAILURE_NAMES = (
    b"request_frame_sha256",
    b"case_input_sha256",
    b"implementation_closure_sha256",
    b"failure_code",
)
CLOSURE_ARTIFACT = "heterodiff.adapter.implementation-closure.v1"
CASE_DOMAIN = "heterodiff.adapter.output-blind-case-input.v1"
MAX_PIPE = 40 * 1024 * 1024 + 2048
MAX_REQUEST = 4 * 1024 * 1024 + 1024
MAX_REPORT = 1024 * 1024
MAX_SUCCESS = 2 * 1024 * 1024
MAX_FAILURE = 64 * 1024
MAX_MODULES = 4096
MAX_SOURCE = 8 * 1024 * 1024
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
PUBLIC_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
MODULE_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
CHILD_FAILURE_CODES = frozenset(
    (
        "CHILD_CLOSURE_INVALID",
        "CHILD_SOURCE_LOAD_FAILED",
        "CHILD_ENTRYPOINT_INVALID",
        "CHILD_PROTOCOL_INVALID",
        "CHILD_DESCRIPTOR_INVALID",
        "CHILD_ADAPT_COMPLETE_FAILED",
        "CHILD_OUTPUT_INVALID",
        "CHILD_BUNDLE_BUILD_FAILED",
        "CHILD_POSTMUTATION",
        "CHILD_INTERNAL",
    )
)
TRUSTED_RUNTIME_MODULE = "__TRUSTED_RUNTIME_MODULE__"
TRUSTED_RUNTIME_CALLABLE = "__TRUSTED_RUNTIME_CALLABLE__"
TRUSTED_RUNTIME_SOURCE_PROFILE = __TRUSTED_RUNTIME_SOURCE_PROFILE__

for _key in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_key] = "1"


class ChildFailure(Exception):
    def __init__(self, code):
        self.code = code


class CountingAdapterProxy:
    __slots__ = (
        "_adapter",
        "adapt_complete_call_count",
        "adapt_call_count",
    )

    def __init__(self, adapter):
        self._adapter = adapter
        self.adapt_complete_call_count = 0
        self.adapt_call_count = 0

    def descriptor(self):
        return self._adapter.descriptor()

    def adapt_complete(self, source_bytes, partition, split_manifest):
        self.adapt_complete_call_count += 1
        return self._adapter.adapt_complete(
            source_bytes,
            partition,
            split_manifest,
        )

    def adapt(self, source_bytes, partition, split_manifest):
        self.adapt_call_count += 1
        return self._adapter.adapt(
            source_bytes,
            partition,
            split_manifest,
        )


def fail(code):
    raise ChildFailure(code)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def domain_sha256(domain, raw):
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(raw).to_bytes(8, "big"))
    digest.update(raw)
    return digest.hexdigest()


def read_all(fd, maximum):
    output = bytearray()
    while True:
        chunk = os.read(fd, min(65536, maximum + 1 - len(output)))
        if not chunk:
            break
        output.extend(chunk)
        if len(output) > maximum:
            fail("CHILD_PROTOCOL_INVALID")
    return bytes(output)


def read_u64(raw, offset):
    if offset < 0 or offset + 8 > len(raw):
        fail("CHILD_PROTOCOL_INVALID")
    return int.from_bytes(raw[offset : offset + 8], "big"), offset + 8


def parse_frame(raw, domain, names, maximum):
    if type(raw) is not bytes or not raw or len(raw) > maximum:
        fail("CHILD_PROTOCOL_INVALID")
    prefix = domain + b"\x00"
    if not raw.startswith(prefix):
        fail("CHILD_PROTOCOL_INVALID")
    offset = len(prefix)
    count, offset = read_u64(raw, offset)
    if count != len(names):
        fail("CHILD_PROTOCOL_INVALID")
    values = []
    for expected in names:
        size, offset = read_u64(raw, offset)
        if size != len(expected) or offset + size > len(raw):
            fail("CHILD_PROTOCOL_INVALID")
        if raw[offset : offset + size] != expected:
            fail("CHILD_PROTOCOL_INVALID")
        offset += size
        value_size, offset = read_u64(raw, offset)
        if value_size > maximum or offset + value_size > len(raw):
            fail("CHILD_PROTOCOL_INVALID")
        values.append(raw[offset : offset + value_size])
        offset += value_size
    if offset != len(raw):
        fail("CHILD_PROTOCOL_INVALID")
    return tuple(values)


def build_frame(domain, names, values, maximum):
    parts = [domain, b"\x00", len(names).to_bytes(8, "big")]
    for name, value in zip(names, values):
        if type(value) is not bytes:
            fail("CHILD_INTERNAL")
        parts.extend(
            (
                len(name).to_bytes(8, "big"),
                name,
                len(value).to_bytes(8, "big"),
                value,
            )
        )
    raw = b"".join(parts)
    if not raw or len(raw) > maximum:
        fail("CHILD_INTERNAL")
    return raw


class DuplicateKey(Exception):
    pass


def lexical_json_preflight(raw):
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in raw:
        if in_string:
            if not escaped and byte == 34:
                in_string = False
                continue
            string_bytes += 1
            if string_bytes > 512 * 1024:
                fail("CHILD_CLOSURE_INVALID")
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            continue
        if byte == 34:
            in_string = True
            string_bytes = 0
            tokens += 1
        elif byte in (123, 91):
            depth += 1
            tokens += 1
            if depth > 32:
                fail("CHILD_CLOSURE_INVALID")
        elif byte in (125, 93):
            depth -= 1
            if depth < 0:
                fail("CHILD_CLOSURE_INVALID")
        elif byte in (44, 58):
            tokens += 1
        if tokens > 200000:
            fail("CHILD_CLOSURE_INVALID")
    if in_string or depth != 0:
        fail("CHILD_CLOSURE_INVALID")


def strict_json(raw, maximum):
    if type(raw) is not bytes or not raw or len(raw) > maximum:
        fail("CHILD_CLOSURE_INVALID")
    if any(byte >= 128 for byte in raw):
        fail("CHILD_CLOSURE_INVALID")
    lexical_json_preflight(raw)
    try:
        text = raw.decode("ascii", "strict")

        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise DuplicateKey()
                result[key] = value
            return result

        def integer(token):
            digits = token[1:] if token.startswith("-") else token
            if len(digits) > 16:
                raise ValueError()
            value = int(token, 10)
            if value < 0 or value > (1 << 53) - 1:
                raise ValueError()
            return value

        def reject(_token):
            raise ValueError()

        tree = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_int=integer,
            parse_float=reject,
            parse_constant=reject,
        )
        canonical = json.dumps(
            tree,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except BaseException:
        fail("CHILD_CLOSURE_INVALID")
    if canonical != raw:
        fail("CHILD_CLOSURE_INVALID")
    return tree


def exact_keys(value, names):
    if type(value) is not dict or tuple(sorted(value)) != tuple(sorted(names)):
        fail("CHILD_CLOSURE_INVALID")
    return value


def ascii_text(value, maximum):
    if type(value) is not str:
        fail("CHILD_CLOSURE_INVALID")
    try:
        raw = value.encode("ascii", "strict")
    except BaseException:
        fail("CHILD_CLOSURE_INVALID")
    if not raw or len(raw) > maximum:
        fail("CHILD_CLOSURE_INVALID")
    return value


def patterned_text(value, maximum, pattern):
    value = ascii_text(value, maximum)
    if pattern.fullmatch(value) is None:
        fail("CHILD_CLOSURE_INVALID")
    return value


def canonical_sha(value):
    value = ascii_text(value, 64)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        fail("CHILD_CLOSURE_INVALID")
    return value


def closure_state(closure_raw, inventory_raw, archive_raw):
    closure = exact_keys(
        strict_json(closure_raw, 4 * 1024 * 1024),
        (
            "adapter_id",
            "adapter_version",
            "artifact_type",
            "dependency_lock_sha256",
            "entry_point",
            "external_import_roots",
            "format_version",
            "modules",
            "protected_namespace_roots",
            "runtime_entry_point",
            "source_archive_inventory_sha256",
            "source_archive_sha256",
        ),
    )
    if (
        closure["artifact_type"] != CLOSURE_ARTIFACT
        or closure["format_version"] != "1"
    ):
        fail("CHILD_CLOSURE_INVALID")
    closure_sha = domain_sha256(CLOSURE_ARTIFACT, closure_raw)
    adapter_id = patterned_text(closure["adapter_id"], 128, PUBLIC_ID_RE)
    adapter_version = patterned_text(
        closure["adapter_version"], 10, VERSION_RE
    )
    canonical_sha(closure["dependency_lock_sha256"])
    if (
        canonical_sha(closure["source_archive_inventory_sha256"])
        != sha256(inventory_raw)
        or canonical_sha(closure["source_archive_sha256"])
        != sha256(archive_raw)
    ):
        fail("CHILD_CLOSURE_INVALID")
    entry = exact_keys(
        closure["entry_point"],
        ("callable_name", "construction_mode_id", "module_name"),
    )
    runtime = exact_keys(
        closure["runtime_entry_point"],
        ("callable_name", "module_name"),
    )
    entry_module = patterned_text(entry["module_name"], 256, MODULE_RE)
    entry_callable = patterned_text(
        entry["callable_name"], 128, IDENTIFIER_RE
    )
    if entry["construction_mode_id"] != "zero-argument-factory-v1":
        fail("CHILD_ENTRYPOINT_INVALID")
    runtime_module = patterned_text(runtime["module_name"], 256, MODULE_RE)
    runtime_callable = patterned_text(
        runtime["callable_name"], 128, IDENTIFIER_RE
    )
    protected = closure["protected_namespace_roots"]
    external = closure["external_import_roots"]
    if (
        type(protected) is not list
        or not protected
        or tuple(protected) != tuple(sorted(set(protected)))
        or type(external) is not list
        or tuple(external) != tuple(sorted(set(external)))
    ):
        fail("CHILD_CLOSURE_INVALID")
    protected = tuple(
        patterned_text(item, 128, MODULE_RE) for item in protected
    )
    external = tuple(
        patterned_text(item, 128, MODULE_RE) for item in external
    )
    if protected != ("heterodiff",) or "heterodiff" in external:
        fail("CHILD_CLOSURE_INVALID")

    modules_tree = closure["modules"]
    if (
        type(modules_tree) is not list
        or not modules_tree
        or len(modules_tree) > MAX_MODULES
    ):
        fail("CHILD_CLOSURE_INVALID")
    records = {}
    for raw_record in modules_tree:
        record = exact_keys(
            raw_record,
            (
                "is_package",
                "module_name",
                "role_id",
                "source_byte_count",
                "source_object_id",
                "source_sha256",
            ),
        )
        name = patterned_text(record["module_name"], 256, MODULE_RE)
        if name in records or type(record["is_package"]) is not bool:
            fail("CHILD_CLOSURE_INVALID")
        if name != "heterodiff" and not name.startswith("heterodiff."):
            fail("CHILD_CLOSURE_INVALID")
        role = ascii_text(record["role_id"], 64)
        if role not in ("adapter-source", "contract-source", "support-source"):
            fail("CHILD_CLOSURE_INVALID")
        count = record["source_byte_count"]
        if type(count) is not int or count < 0 or count > MAX_SOURCE:
            fail("CHILD_CLOSURE_INVALID")
        object_id = patterned_text(
            record["source_object_id"], 128, TOKEN_RE
        )
        source_sha = canonical_sha(record["source_sha256"])
        records[name] = {
            "is_package": record["is_package"],
            "module_name": name,
            "role_id": role,
            "source_byte_count": count,
            "source_object_id": object_id,
            "source_sha256": source_sha,
        }
    if tuple(records) != tuple(sorted(records)):
        fail("CHILD_CLOSURE_INVALID")
    if entry_module not in records or runtime_module not in records:
        fail("CHILD_ENTRYPOINT_INVALID")
    if (
        entry_module != "heterodiff"
        and not entry_module.startswith("heterodiff.")
    ) or (
        runtime_module != "heterodiff"
        and not runtime_module.startswith("heterodiff.")
    ):
        fail("CHILD_ENTRYPOINT_INVALID")

    inventory = exact_keys(
        strict_json(inventory_raw, 4 * 1024 * 1024),
        (
            "archive_byte_count",
            "archive_format_id",
            "archive_sha256",
            "artifact_type",
            "format_version",
            "members",
            "source_objects",
        ),
    )
    if (
        inventory["archive_byte_count"] != len(archive_raw)
        or inventory["archive_sha256"] != sha256(archive_raw)
        or inventory["archive_format_id"]
        != "zip-stored-path-free-source-custody-v1"
        or inventory["artifact_type"]
        != "heterodiff.adapter.source-archive-inventory.v1"
        or inventory["format_version"] != "1"
    ):
        fail("CHILD_CLOSURE_INVALID")
    objects = inventory["source_objects"]
    if type(objects) is not list or len(objects) != len(records):
        fail("CHILD_CLOSURE_INVALID")
    object_map = {}
    for item in objects:
        item = exact_keys(
            item,
            (
                "role_id",
                "source_byte_count",
                "source_object_id",
                "source_sha256",
            ),
        )
        key = (item["role_id"], item["source_object_id"])
        if key in object_map:
            fail("CHILD_CLOSURE_INVALID")
        object_map[key] = item
    try:
        with zipfile.ZipFile(io.BytesIO(archive_raw), "r") as archive:
            infos = archive.infolist()
            if len(infos) != len(records):
                fail("CHILD_CLOSURE_INVALID")
            contents = []
            for info in infos:
                if (
                    info.compress_type != zipfile.ZIP_STORED
                    or info.flag_bits != 0
                    or info.file_size > MAX_SOURCE
                ):
                    fail("CHILD_CLOSURE_INVALID")
                source = archive.read(info)
                if len(source) != info.file_size:
                    fail("CHILD_CLOSURE_INVALID")
                contents.append(source)
    except ChildFailure:
        raise
    except BaseException:
        fail("CHILD_CLOSURE_INVALID")
    available = {}
    for source in contents:
        key = (len(source), sha256(source))
        available.setdefault(key, []).append(source)
    sources = {}
    expected_counts = {}
    for name, record in records.items():
        key = (record["role_id"], record["source_object_id"])
        item = object_map.get(key)
        if (
            type(item) is not dict
            or item.get("source_byte_count") != record["source_byte_count"]
            or item.get("source_sha256") != record["source_sha256"]
        ):
            fail("CHILD_CLOSURE_INVALID")
        identity = (record["source_byte_count"], record["source_sha256"])
        candidates = available.get(identity, ())
        if not candidates:
            fail("CHILD_CLOSURE_INVALID")
        source = candidates[0]
        if len(source) != identity[0] or sha256(source) != identity[1]:
            fail("CHILD_CLOSURE_INVALID")
        sources[name] = source
        expected_counts[identity] = expected_counts.get(identity, 0) + 1
    observed_counts = {}
    for source in contents:
        identity = (len(source), sha256(source))
        observed_counts[identity] = observed_counts.get(identity, 0) + 1
    if expected_counts != observed_counts:
        fail("CHILD_CLOSURE_INVALID")
    if (
        runtime_module != TRUSTED_RUNTIME_MODULE
        or runtime_callable != TRUSTED_RUNTIME_CALLABLE
    ):
        fail("CHILD_CLOSURE_INVALID")
    for expected in TRUSTED_RUNTIME_SOURCE_PROFILE:
        name, is_package, role, count, object_id, source_sha = expected
        record = records.get(name)
        source = sources.get(name)
        if (
            record is None
            or source is None
            or record["is_package"] is not is_package
            or record["role_id"] != role
            or record["source_byte_count"] != count
            or record["source_object_id"] != object_id
            or record["source_sha256"] != source_sha
            or len(source) != count
            or sha256(source) != source_sha
        ):
            fail("CHILD_CLOSURE_INVALID")
    return {
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "closure_sha256": closure_sha,
        "entry_module": entry_module,
        "entry_callable": entry_callable,
        "runtime_module": runtime_module,
        "runtime_callable": runtime_callable,
        "protected": protected,
        "records": records,
        "sources": sources,
    }


class ClosureFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, state):
        self.records = dict(state["records"])
        self.sources = dict(state["sources"])
        self.protected = tuple(state["protected"])
        self.loaded = {}
        self.fallback_count = 0

    def protected_name(self, fullname):
        return any(
            fullname == root or fullname.startswith(root + ".")
            for root in self.protected
        )

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.records:
            return importlib.util.spec_from_loader(
                fullname,
                self,
                is_package=self.records[fullname]["is_package"],
            )
        if self.protected_name(fullname):
            self.fallback_count += 1
            raise ModuleNotFoundError("protected project import denied")
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        name = module.__spec__.name
        record = self.records.get(name)
        source = self.sources.get(name)
        if record is None or type(source) is not bytes:
            fail("CHILD_SOURCE_LOAD_FAILED")
        if (
            len(source) != record["source_byte_count"]
            or sha256(source) != record["source_sha256"]
        ):
            fail("CHILD_SOURCE_LOAD_FAILED")
        try:
            code = compile(
                source,
                "<implementation-closure:" + name + ">",
                "exec",
                dont_inherit=True,
                optimize=0,
            )
            exec(code, module.__dict__)
        except ChildFailure:
            raise
        except BaseException:
            fail("CHILD_SOURCE_LOAD_FAILED")
        self.loaded[name] = (
            record["source_object_id"],
            record["source_byte_count"],
            record["source_sha256"],
        )


def loaded_modules_bytes(finder):
    modules = []
    for name in sorted(finder.loaded):
        object_id, count, source_sha = finder.loaded[name]
        frame = build_frame(
            MODULE_DOMAIN,
            MODULE_NAMES,
            (
                name.encode("ascii"),
                object_id.encode("ascii"),
                count.to_bytes(8, "big"),
                source_sha.encode("ascii"),
            ),
            MAX_REPORT,
        )
        modules.append(frame)
    if not modules or len(modules) > MAX_MODULES:
        fail("CHILD_SOURCE_LOAD_FAILED")
    parts = [len(modules).to_bytes(8, "big")]
    for frame in modules:
        parts.extend((len(frame).to_bytes(8, "big"), frame))
    raw = b"".join(parts)
    if len(raw) > MAX_REPORT:
        fail("CHILD_SOURCE_LOAD_FAILED")
    return raw


def verify_loader_after_run(state, finder):
    if not sys.meta_path or sys.meta_path[0] is not finder:
        fail("CHILD_SOURCE_LOAD_FAILED")
    if finder.fallback_count != 0:
        fail("CHILD_SOURCE_LOAD_FAILED")
    for name, source in state["sources"].items():
        if (
            finder.sources.get(name) != source
            or finder.records.get(name) != state["records"][name]
        ):
            fail("CHILD_SOURCE_LOAD_FAILED")
    for name, module in tuple(sys.modules.items()):
        if finder.protected_name(name):
            if name not in state["records"]:
                fail("CHILD_SOURCE_LOAD_FAILED")
            if getattr(module, "__loader__", None) is not finder:
                fail("CHILD_SOURCE_LOAD_FAILED")
    if (
        state["entry_module"] not in finder.loaded
        or state["runtime_module"] not in finder.loaded
        or any(
            item[0] not in finder.loaded
            for item in TRUSTED_RUNTIME_SOURCE_PROFILE
        )
    ):
        fail("CHILD_SOURCE_LOAD_FAILED")


def runtime_failure_code(error):
    value = getattr(error, "code", "")
    mapping = {
        "CHILD_RUNTIME_INPUT_TYPE": "CHILD_PROTOCOL_INVALID",
        "CHILD_RUNTIME_CASE_INPUT_INVALID": "CHILD_PROTOCOL_INVALID",
        "CHILD_RUNTIME_ADAPTER_PROTOCOL_INVALID": "CHILD_PROTOCOL_INVALID",
        "CHILD_RUNTIME_DESCRIPTOR_INVALID": "CHILD_DESCRIPTOR_INVALID",
        "CHILD_RUNTIME_ADAPT_COMPLETE_FAILED": "CHILD_ADAPT_COMPLETE_FAILED",
        "CHILD_RUNTIME_OUTPUT_INVALID": "CHILD_OUTPUT_INVALID",
        "CHILD_RUNTIME_BUNDLE_BUILD_FAILED": "CHILD_BUNDLE_BUILD_FAILED",
        "CHILD_RUNTIME_POSTMUTATION": "CHILD_POSTMUTATION",
    }
    return mapping.get(value, "CHILD_INTERNAL")


def run_case(state, case_bytes):
    for name in tuple(sys.modules):
        if any(
            name == root or name.startswith(root + ".")
            for root in state["protected"]
        ):
            fail("CHILD_SOURCE_LOAD_FAILED")
    finder = ClosureFinder(state)
    sys.meta_path.insert(0, finder)
    try:
        runtime_module = importlib.import_module(state["runtime_module"])
        runtime = getattr(runtime_module, state["runtime_callable"])
        if not callable(runtime):
            fail("CHILD_ENTRYPOINT_INVALID")
        entry_module = importlib.import_module(state["entry_module"])
        factory = getattr(entry_module, state["entry_callable"])
        if (
            not callable(factory)
            or sys.modules.get(state["runtime_module"]) is not runtime_module
            or getattr(runtime_module, state["runtime_callable"], None)
            is not runtime
        ):
            fail("CHILD_ENTRYPOINT_INVALID")
        try:
            adapter = factory()
        except BaseException:
            fail("CHILD_ENTRYPOINT_INVALID")
        if (
            sys.modules.get(state["runtime_module"]) is not runtime_module
            or getattr(runtime_module, state["runtime_callable"], None)
            is not runtime
        ):
            fail("CHILD_SOURCE_LOAD_FAILED")
        counted_adapter = CountingAdapterProxy(adapter)
        try:
            result = runtime(case_bytes, counted_adapter)
        except ChildFailure:
            raise
        except BaseException as error:
            fail(runtime_failure_code(error))
        if (
            type(getattr(result, "adapter_id", None)) is not str
            or type(getattr(result, "adapter_version", None)) is not str
            or result.adapter_id != state["adapter_id"]
            or result.adapter_version != state["adapter_version"]
            or type(counted_adapter.adapt_complete_call_count) is not int
            or counted_adapter.adapt_complete_call_count != 1
            or type(counted_adapter.adapt_call_count) is not int
            or counted_adapter.adapt_call_count != 0
        ):
            fail("CHILD_DESCRIPTOR_INVALID")
        bundle = getattr(
            getattr(result, "adapted_evidence_bundle", None),
            "bundle_bytes",
            None,
        )
        if type(bundle) is not bytes or not bundle or len(bundle) > MAX_SUCCESS:
            fail("CHILD_OUTPUT_INVALID")
        verify_loader_after_run(state, finder)
        report = build_frame(
            REPORT_DOMAIN,
            REPORT_NAMES,
            (
                state["closure_sha256"].encode("ascii"),
                state["entry_module"].encode("ascii"),
                state["entry_callable"].encode("ascii"),
                loaded_modules_bytes(finder),
                (0).to_bytes(8, "big"),
            ),
            MAX_REPORT,
        )
        return (
            result,
            report,
            bundle,
            counted_adapter.adapt_complete_call_count,
            counted_adapter.adapt_call_count,
        )
    finally:
        if sys.meta_path and sys.meta_path[0] is finder:
            sys.meta_path.pop(0)


def emit(raw):
    offset = 0
    while offset < len(raw):
        count = os.write(1, raw[offset:])
        if type(count) is not int or count <= 0:
            os._exit(74)
        offset += count


def failure_frame(request_sha, case_sha, closure_sha, code):
    if code not in CHILD_FAILURE_CODES:
        code = "CHILD_INTERNAL"
    return build_frame(
        FAILURE_DOMAIN,
        FAILURE_NAMES,
        (
            request_sha.encode("ascii"),
            case_sha.encode("ascii"),
            closure_sha.encode("ascii"),
            code.encode("ascii"),
        ),
        MAX_FAILURE,
    )


def main():
    request_sha = EMPTY_SHA256
    case_sha = EMPTY_SHA256
    closure_sha = EMPTY_SHA256
    try:
        if len(sys.argv) != 2:
            fail("CHILD_PROTOCOL_INVALID")
        try:
            closure_fd = int(sys.argv[1], 10)
        except BaseException:
            fail("CHILD_PROTOCOL_INVALID")
        if closure_fd < 3:
            fail("CHILD_PROTOCOL_INVALID")
        pipe_raw = read_all(closure_fd, MAX_PIPE)
        try:
            os.close(closure_fd)
        except BaseException:
            pass
        request_raw = read_all(0, MAX_REQUEST)
        request_sha = sha256(request_raw)
        request_values = parse_frame(
            request_raw,
            REQUEST_DOMAIN,
            REQUEST_NAMES,
            MAX_REQUEST,
        )
        case_bytes = request_values[0]
        if not case_bytes or len(case_bytes) > 4 * 1024 * 1024:
            fail("CHILD_PROTOCOL_INVALID")
        case_sha = domain_sha256(CASE_DOMAIN, case_bytes)
        pipe_values = parse_frame(
            pipe_raw,
            PIPE_DOMAIN,
            PIPE_NAMES,
            MAX_PIPE,
        )
        closure_raw, inventory_raw, archive_raw = pipe_values
        closure_sha = domain_sha256(CLOSURE_ARTIFACT, closure_raw)
        state = closure_state(closure_raw, inventory_raw, archive_raw)
        if state["closure_sha256"] != closure_sha:
            fail("CHILD_CLOSURE_INVALID")
        (
            result,
            report,
            bundle,
            adapt_complete_call_count,
            adapt_call_count,
        ) = run_case(state, case_bytes)
        success = build_frame(
            SUCCESS_DOMAIN,
            SUCCESS_NAMES,
            (
                request_sha.encode("ascii"),
                case_sha.encode("ascii"),
                closure_sha.encode("ascii"),
                result.adapter_id.encode("ascii"),
                result.adapter_version.encode("ascii"),
                adapt_complete_call_count.to_bytes(8, "big"),
                adapt_call_count.to_bytes(8, "big"),
                report,
                bundle,
            ),
            MAX_SUCCESS,
        )
        emit(success)
        return 0
    except ChildFailure as error:
        try:
            emit(
                failure_frame(
                    request_sha,
                    case_sha,
                    closure_sha,
                    error.code,
                )
            )
            return 0
        except BaseException:
            return 75
    except BaseException:
        try:
            emit(
                failure_frame(
                    request_sha,
                    case_sha,
                    closure_sha,
                    "CHILD_INTERNAL",
                )
            )
            return 0
        except BaseException:
            return 76


os._exit(main())
'''


_CHILD_BOOTSTRAP_SOURCE = (
    _CHILD_BOOTSTRAP_SOURCE_TEMPLATE.replace(
        '"__TRUSTED_RUNTIME_MODULE__"',
        repr(OUTPUT_BLIND_TRUSTED_RUNTIME_MODULE_NAME),
    )
    .replace(
        '"__TRUSTED_RUNTIME_CALLABLE__"',
        repr(OUTPUT_BLIND_TRUSTED_RUNTIME_CALLABLE_NAME),
    )
    .replace(
        "__TRUSTED_RUNTIME_SOURCE_PROFILE__",
        repr(
            tuple(
                (
                    item.module_name,
                    item.is_package,
                    item.role_id,
                    item.source_byte_count,
                    item.source_object_id,
                    item.source_sha256,
                )
                for item in OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES
            )
        ),
    )
)


OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_BYTES = (
    _CHILD_BOOTSTRAP_SOURCE.encode("utf-8", "strict")
)
OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256 = hashlib.sha256(
    OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_BYTES
).hexdigest()
OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_EXECUTION_PROFILE = MappingProxyType(
    {
        "argv_mode": "explicit-interpreter-I-B-c-fixed-bootstrap-v1",
        "closure_channel": "dedicated-inherited-read-descriptor-v1",
        "request_channel": "stdin-one-field-frame-v1",
        "response_channel": "stdout-one-complete-frame-v1",
        "spawn_environment": "empty-before-bootstrap-v1",
        "external_import_roots": (
            "supervisor-static-declaration-not-runtime-allowlist-v1"
        ),
    }
)


__all__ = [
    "MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_ARCHIVE_BYTES",
    "MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_BYTES",
    "MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_BYTES",
    "MAXIMUM_OUTPUT_BLIND_IMPLEMENTATION_INVENTORY_BYTES",
    "OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_EXECUTION_PROFILE",
    "OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_BYTES",
    "OUTPUT_BLIND_ADAPTER_CHILD_BOOTSTRAP_SOURCE_SHA256",
    "OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_DOMAIN",
    "OUTPUT_BLIND_IMPLEMENTATION_CLOSURE_PIPE_FIELD_NAMES",
    "build_output_blind_implementation_closure_pipe_frame",
]
