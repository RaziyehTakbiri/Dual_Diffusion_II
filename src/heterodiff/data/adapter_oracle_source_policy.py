"""Pure static policy validation for one independently custodied oracle.

This module validates exact immutable Python source bytes against a deliberately
small, development-only language profile.  It performs no filesystem,
network, subprocess, import, compilation, or source execution.  The static
policy is defense in depth only: a passing receipt is not containment evidence
and is never decision eligible.

The accepted source is ASCII (and therefore canonical UTF-8), parses with the
Python 3.9 feature grammar, and may directly import only the fixed standard
library modules below.  Registry-supplied import and name bans are additive;
they can narrow but never widen the fixed policy.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import io
import json
import math
import re
import tokenize
from types import MappingProxyType
from typing import Dict, Iterable, Optional, Tuple


ORACLE_SOURCE_POLICY_ARTIFACT_TYPE = (
    "heterodiff.adapter.oracle-source-policy-receipt.v1"
)
ORACLE_SOURCE_POLICY_DIGEST_DOMAIN = (
    b"heterodiff.adapter.oracle-source-policy-receipt.v1"
)
ORACLE_SOURCE_POLICY_ID = "heterodiff-oracle-source-python-policy-v1"
ORACLE_SOURCE_PARSER_ID = "cpython-ast-feature-version-3.9-v1"
ORACLE_SOURCE_POLICY_STATUS = "pass"

MAXIMUM_ORACLE_SOURCE_BYTES = 1024 * 1024
MAXIMUM_ORACLE_SOURCE_LINES = 16_384
MAXIMUM_ORACLE_SOURCE_LINE_BYTES = 16 * 1024
MAXIMUM_ORACLE_SOURCE_TOKENS = 65_536
MAXIMUM_ORACLE_SOURCE_TOKEN_BYTES = 64 * 1024
MAXIMUM_ORACLE_SOURCE_INDENT_DEPTH = 32
MAXIMUM_ORACLE_SOURCE_BRACKET_DEPTH = 64
MAXIMUM_ORACLE_SOURCE_AST_NODES = 65_536
MAXIMUM_ORACLE_SOURCE_AST_DEPTH = 64
MAXIMUM_ORACLE_SOURCE_LITERAL_BYTES = 256 * 1024
MAXIMUM_ORACLE_SOURCE_IDENTIFIER_BYTES = 128
MAXIMUM_ORACLE_POLICY_BANS = 1024
MAXIMUM_ORACLE_POLICY_ID_BYTES = 128
MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES = 256 * 1024
MAXIMUM_ORACLE_WORKER_STDIN_READ_BYTES = 32 * 1024 * 1024 + 1

ALLOWED_ORACLE_SOURCE_IMPORT_IDS = (
    "base64",
    "binascii",
    "hashlib",
    "json",
    "sys",
)

_ALLOWED_MODULE_ATTRIBUTE_PATHS = MappingProxyType(
    {
        "base64": frozenset(
            (
                ("b64decode",),
                ("b64encode",),
            )
        ),
        "binascii": frozenset((("Error",),)),
        "hashlib": frozenset((("sha256",),)),
        "json": frozenset(
            (
                ("JSONDecodeError",),
                ("dumps",),
                ("loads",),
            )
        ),
        "sys": frozenset(
            (
                ("stderr",),
                ("stderr", "buffer"),
                ("stderr", "buffer", "flush"),
                ("stderr", "buffer", "write"),
                ("stdin",),
                ("stdin", "buffer"),
                ("stdin", "buffer", "read"),
                ("stdout",),
                ("stdout", "buffer"),
                ("stdout", "buffer", "close"),
                ("stdout", "buffer", "flush"),
                ("stdout", "buffer", "write"),
            )
        ),
    }
)

_ALLOWED_DATA_ATTRIBUTE_NAMES = frozenset(
    (
        "append",
        "decode",
        "encode",
        "extend",
        "format",
        "from_bytes",
        "fromhex",
        "get",
        "hex",
        "hexdigest",
        "items",
        "join",
        "lower",
        "pop",
        "startswith",
        "to_bytes",
        "update",
    )
)

_ALLOWED_DIRECT_CALL_NAMES = frozenset(
    (
        "SystemExit",
        "ValueError",
        "abs",
        "any",
        "dict",
        "float",
        "int",
        "len",
        "list",
        "range",
        "reversed",
        "sorted",
        "tuple",
        "type",
        "zip",
    )
)

_FIXED_FORBIDDEN_NAMES = frozenset(
    (
        "__builtins__",
        "__import__",
        "breakpoint",
        "compile",
        "delattr",
        "dir",
        "eval",
        "exec",
        "exit",
        "getattr",
        "globals",
        "help",
        "input",
        "locals",
        "open",
        "print",
        "quit",
        "setattr",
        "vars",
    )
)

_FIXED_FORBIDDEN_IMPORT_PREFIXES = (
    "asyncio",
    "builtins",
    "concurrent",
    "ctypes",
    "heterodiff",
    "http",
    "importlib",
    "inspect",
    "io",
    "marshal",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "pkgutil",
    "runpy",
    "shlex",
    "shutil",
    "signal",
    "site",
    "socket",
    "subprocess",
    "tempfile",
    "threading",
    "urllib",
)

_FORBIDDEN_SYNTAX_TYPES = (
    ast.AsyncFor,
    ast.AsyncFunctionDef,
    ast.AsyncWith,
    ast.Await,
    ast.ClassDef,
    ast.Delete,
    ast.Global,
    ast.Lambda,
    ast.Nonlocal,
    ast.Starred,
    ast.With,
    ast.Yield,
    ast.YieldFrom,
)

_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DUNDER_RE = re.compile(r"^__[A-Za-z0-9_]+__$")
_DUNDER_SEARCH_RE = re.compile(r"__[A-Za-z0-9_]+__")
_SAFE_FORMAT_LITERAL_RE = re.compile(r"^(?:[^{}]|\{\})*$")
_ENCODING_COOKIE_RE = re.compile(
    rb"coding[=:][ \t]*[-_.A-Za-z0-9]+"
)


class OracleSourcePolicyCode(str, Enum):
    """Closed failures for static source-policy validation."""

    POLICY_INPUT_TYPE = "POLICY_INPUT_TYPE"
    POLICY_SOURCE_IDENTITY = "POLICY_SOURCE_IDENTITY"
    POLICY_SOURCE_ENCODING = "POLICY_SOURCE_ENCODING"
    POLICY_SOURCE_RESOURCE = "POLICY_SOURCE_RESOURCE"
    POLICY_SOURCE_LEXICAL = "POLICY_SOURCE_LEXICAL"
    POLICY_SOURCE_SYNTAX = "POLICY_SOURCE_SYNTAX"
    POLICY_IMPORT_FORBIDDEN = "POLICY_IMPORT_FORBIDDEN"
    POLICY_NAME_FORBIDDEN = "POLICY_NAME_FORBIDDEN"
    POLICY_SYNTAX_FORBIDDEN = "POLICY_SYNTAX_FORBIDDEN"
    POLICY_CANONICALIZATION = "POLICY_CANONICALIZATION"


_ERROR_MESSAGES = MappingProxyType(
    {
        OracleSourcePolicyCode.POLICY_INPUT_TYPE: (
            "oracle source policy input has an invalid exact type"
        ),
        OracleSourcePolicyCode.POLICY_SOURCE_IDENTITY: (
            "oracle source bytes do not match their registered identity"
        ),
        OracleSourcePolicyCode.POLICY_SOURCE_ENCODING: (
            "oracle source is not strict ASCII and canonical UTF-8"
        ),
        OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE: (
            "oracle source exceeds a fixed static-analysis resource ceiling"
        ),
        OracleSourcePolicyCode.POLICY_SOURCE_LEXICAL: (
            "oracle source violates the fixed lexical profile"
        ),
        OracleSourcePolicyCode.POLICY_SOURCE_SYNTAX: (
            "oracle source does not parse under the fixed Python grammar"
        ),
        OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN: (
            "oracle source uses an import outside the fixed policy"
        ),
        OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN: (
            "oracle source uses a name outside the fixed policy"
        ),
        OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN: (
            "oracle source uses syntax outside the fixed policy"
        ),
        OracleSourcePolicyCode.POLICY_CANONICALIZATION: (
            "oracle source policy receipt cannot be canonicalized"
        ),
    }
)


class OracleSourcePolicyError(ValueError):
    """One fixed coded failure with no source-controlled message content."""

    def __init__(self, code: OracleSourcePolicyCode) -> None:
        if type(code) is not OracleSourcePolicyCode:
            raise TypeError("oracle source policy code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: OracleSourcePolicyCode) -> None:
    raise OracleSourcePolicyError(code) from None


def _token(value: object) -> str:
    if type(value) is not str:
        _fail(OracleSourcePolicyCode.POLICY_INPUT_TYPE)
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        _fail(OracleSourcePolicyCode.POLICY_INPUT_TYPE)
    if (
        not encoded
        or len(encoded) > MAXIMUM_ORACLE_POLICY_ID_BYTES
        or _TOKEN_RE.fullmatch(value) is None
    ):
        _fail(OracleSourcePolicyCode.POLICY_INPUT_TYPE)
    return value


def _digest(value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(OracleSourcePolicyCode.POLICY_INPUT_TYPE)
    return value


def _ban_tuple(value: object) -> Tuple[str, ...]:
    if type(value) is not tuple or not value:
        _fail(OracleSourcePolicyCode.POLICY_INPUT_TYPE)
    if len(value) > MAXIMUM_ORACLE_POLICY_BANS:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
    result = tuple(_token(item) for item in value)
    if result != tuple(sorted(set(result))):
        _fail(OracleSourcePolicyCode.POLICY_INPUT_TYPE)
    return result


def _source_identity(
    source_bytes: object,
    source_byte_count: object,
    source_sha256: object,
) -> Tuple[bytes, int, str]:
    if (
        type(source_bytes) is not bytes
        or type(source_byte_count) is not int
    ):
        _fail(OracleSourcePolicyCode.POLICY_INPUT_TYPE)
    digest = _digest(source_sha256)
    if (
        not source_bytes
        or source_byte_count <= 0
        or source_byte_count > MAXIMUM_ORACLE_SOURCE_BYTES
        or len(source_bytes) > MAXIMUM_ORACLE_SOURCE_BYTES
    ):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
    if (
        len(source_bytes) != source_byte_count
        or hashlib.sha256(source_bytes).hexdigest() != digest
    ):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_IDENTITY)
    return source_bytes, source_byte_count, digest


def _decode_source(source_bytes: bytes) -> str:
    if source_bytes.startswith(b"\xef\xbb\xbf"):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
    first_two_lines = b"\n".join(source_bytes.split(b"\n", 2)[:2])
    if _ENCODING_COOKIE_RE.search(first_two_lines) is not None:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
    if (
        b"\x00" in source_bytes
        or b"\r" in source_bytes
        or b"\t" in source_bytes
        or b"\x0c" in source_bytes
        or any(
            (byte < 0x20 and byte != 0x0A) or byte == 0x7F
            for byte in source_bytes
        )
        or any(byte >= 0x80 for byte in source_bytes)
    ):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
    try:
        text = source_bytes.decode("utf-8", "strict")
    except UnicodeError:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
    if text.encode("utf-8", "strict") != source_bytes:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
    lines = source_bytes.splitlines()
    if len(lines) > MAXIMUM_ORACLE_SOURCE_LINES:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
    if any(len(line) > MAXIMUM_ORACLE_SOURCE_LINE_BYTES for line in lines):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
    return text


def _lexical_preflight(text: str) -> None:
    token_count = 0
    indent_depth = 0
    bracket_depth = 0
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for item in tokens:
            token_count += 1
            if token_count > MAXIMUM_ORACLE_SOURCE_TOKENS:
                _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
            try:
                token_size = len(item.string.encode("ascii", "strict"))
            except UnicodeError:
                _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
            if token_size > MAXIMUM_ORACLE_SOURCE_TOKEN_BYTES:
                _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
            if item.type == tokenize.ERRORTOKEN:
                _fail(OracleSourcePolicyCode.POLICY_SOURCE_LEXICAL)
            if item.type == tokenize.INDENT:
                indent_depth += 1
                if indent_depth > MAXIMUM_ORACLE_SOURCE_INDENT_DEPTH:
                    _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
            elif item.type == tokenize.DEDENT:
                indent_depth -= 1
                if indent_depth < 0:
                    _fail(OracleSourcePolicyCode.POLICY_SOURCE_LEXICAL)
            elif item.type == tokenize.OP:
                if item.string in ("(", "[", "{"):
                    bracket_depth += 1
                    if bracket_depth > MAXIMUM_ORACLE_SOURCE_BRACKET_DEPTH:
                        _fail(
                            OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE
                        )
                elif item.string in (")", "]", "}"):
                    bracket_depth -= 1
                    if bracket_depth < 0:
                        _fail(OracleSourcePolicyCode.POLICY_SOURCE_LEXICAL)
                elif item.string == ";":
                    _fail(OracleSourcePolicyCode.POLICY_SOURCE_LEXICAL)
    except OracleSourcePolicyError:
        raise
    except (
        IndentationError,
        SyntaxError,
        tokenize.TokenError,
        UnicodeError,
    ):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_LEXICAL)
    if indent_depth != 0 or bracket_depth != 0:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_LEXICAL)


def _parse_source(text: str) -> ast.Module:
    try:
        tree = ast.parse(
            text,
            filename="<oracle-source>",
            mode="exec",
            type_comments=False,
            feature_version=9,
        )
    except (IndentationError, SyntaxError, ValueError):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_SYNTAX)
    except (MemoryError, RecursionError):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
    if type(tree) is not ast.Module:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_SYNTAX)
    return tree


def _ast_nodes_with_depth(tree: ast.AST) -> Tuple[Tuple[ast.AST, int], ...]:
    stack = [(tree, 0)]
    result = []
    while stack:
        node, depth = stack.pop()
        if type(node) is not ast.AST and not isinstance(node, ast.AST):
            _fail(OracleSourcePolicyCode.POLICY_SOURCE_SYNTAX)
        if depth > MAXIMUM_ORACLE_SOURCE_AST_DEPTH:
            _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
        result.append((node, depth))
        if len(result) > MAXIMUM_ORACLE_SOURCE_AST_NODES:
            _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
        children = tuple(ast.iter_child_nodes(node))
        stack.extend((child, depth + 1) for child in reversed(children))
    return tuple(result)


def _identifier(value: object) -> str:
    if type(value) is not str:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_SYNTAX)
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
    if (
        not encoded
        or len(encoded) > MAXIMUM_ORACLE_SOURCE_IDENTIFIER_BYTES
    ):
        _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
    return value


def _dunder_forbidden(value: str) -> bool:
    return _DUNDER_RE.fullmatch(value) is not None and value != "__name__"


def _matches_import_ban(module_name: str, ban: str) -> bool:
    return (
        module_name == ban
        or module_name.startswith(ban + ".")
        or ban.startswith(module_name + ".")
    )


def _attribute_path(value: ast.AST) -> Optional[Tuple[str, Tuple[str, ...]]]:
    parts = []
    current = value
    while isinstance(current, ast.Attribute):
        parts.append(_identifier(current.attr))
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    return _identifier(current.id), tuple(reversed(parts))


def _dotted_name(value: ast.AST) -> Optional[str]:
    path = _attribute_path(value)
    if path is None:
        return None
    root, parts = path
    return ".".join((root,) + parts)


def _name_is_banned(
    value: str,
    forbidden_names: Tuple[str, ...],
) -> bool:
    if value in _FIXED_FORBIDDEN_NAMES or _dunder_forbidden(value):
        return True
    return value in forbidden_names


def _validate_literal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value.bit_length() > 4096:
            _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
        return
    if type(value) is float:
        if not math.isfinite(value):
            _fail(OracleSourcePolicyCode.POLICY_SOURCE_SYNTAX)
        return
    if type(value) in (str, bytes):
        try:
            encoded = (
                value.encode("utf-8", "strict")
                if type(value) is str
                else value
            )
        except UnicodeError:
            _fail(OracleSourcePolicyCode.POLICY_SOURCE_ENCODING)
        if len(encoded) > MAXIMUM_ORACLE_SOURCE_LITERAL_BYTES:
            _fail(OracleSourcePolicyCode.POLICY_SOURCE_RESOURCE)
        if (
            type(value) is str
            and _DUNDER_SEARCH_RE.search(value) is not None
            and value != "__main__"
        ):
            _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
        return
    if value is Ellipsis or type(value) is complex:
        _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
    _fail(OracleSourcePolicyCode.POLICY_SOURCE_SYNTAX)


def _imported_modules(
    nodes: Iterable[Tuple[ast.AST, int]],
    forbidden_imports: Tuple[str, ...],
) -> Tuple[str, ...]:
    imported = []
    for node, _depth in nodes:
        if isinstance(node, ast.ImportFrom):
            _fail(OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN)
        if not isinstance(node, ast.Import):
            continue
        if not node.names:
            _fail(OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN)
        for alias in node.names:
            name = _identifier(alias.name)
            if alias.asname is not None or "." in name:
                _fail(OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN)
            if (
                name not in ALLOWED_ORACLE_SOURCE_IMPORT_IDS
                or any(
                    _matches_import_ban(name, prefix)
                    for prefix in _FIXED_FORBIDDEN_IMPORT_PREFIXES
                )
                or any(
                    _matches_import_ban(name, ban)
                    for ban in forbidden_imports
                )
            ):
                _fail(OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN)
            imported.append(name)
    if len(set(imported)) != len(imported):
        _fail(OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN)
    return tuple(imported)


def _parent_map(tree: ast.AST) -> Dict[ast.AST, ast.AST]:
    result = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            # CPython shares singleton operator/context nodes such as Load
            # across otherwise disjoint AST branches.  Identifier and
            # attribute nodes, the only parents consulted below, are not
            # shared; retaining the first parent is therefore unambiguous.
            result.setdefault(child, parent)
    return result


def _is_exception_type_attribute(
    node: ast.Attribute,
    parents: Dict[ast.AST, ast.AST],
) -> bool:
    current = node
    parent = parents.get(current)
    while isinstance(parent, ast.Tuple):
        current = parent
        parent = parents.get(current)
    return (
        isinstance(parent, ast.ExceptHandler)
        and parent.type is current
    )


def _validate_policy_tree(
    tree: ast.Module,
    *,
    forbidden_imports: Tuple[str, ...],
    forbidden_names: Tuple[str, ...],
) -> None:
    nodes = _ast_nodes_with_depth(tree)
    imported_modules = frozenset(
        _imported_modules(nodes, forbidden_imports)
    )
    parents = _parent_map(tree)
    defined_function_sequence = tuple(
        _identifier(node.name)
        for node, _depth in nodes
        if isinstance(node, ast.FunctionDef)
    )
    if len(set(defined_function_sequence)) != len(defined_function_sequence):
        _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
    defined_functions = frozenset(defined_function_sequence)

    for node, _depth in nodes:
        if isinstance(node, _FORBIDDEN_SYNTAX_TYPES):
            _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
        if isinstance(node, ast.Assert):
            _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
        if isinstance(node, ast.FunctionDef):
            name = _identifier(node.name)
            if (
                _name_is_banned(name, forbidden_names)
                or name in imported_modules
                or name in _ALLOWED_DIRECT_CALL_NAMES
            ):
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            if (
                node.decorator_list
                or node.returns is not None
                or node.type_comment is not None
            ):
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
        if isinstance(node, ast.arg):
            argument_name = _identifier(node.arg)
            if (
                _name_is_banned(argument_name, forbidden_names)
                or argument_name in imported_modules
                or argument_name in _ALLOWED_DIRECT_CALL_NAMES
                or argument_name in defined_functions
            ):
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            if (
                node.annotation is not None
                or getattr(node, "type_comment", None) is not None
            ):
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
        if isinstance(node, ast.AnnAssign):
            _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
        if isinstance(node, ast.Raise):
            if node.cause is not None or not isinstance(node.exc, ast.Call):
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
            raised_call = node.exc
            if not isinstance(raised_call.func, ast.Name):
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
            raised_name = _identifier(raised_call.func.id)
            if raised_name == "ValueError":
                if raised_call.args or raised_call.keywords:
                    _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
            elif raised_name == "SystemExit":
                if (
                    len(raised_call.args) != 1
                    or raised_call.keywords
                    or not isinstance(raised_call.args[0], ast.Call)
                    or not isinstance(
                        raised_call.args[0].func,
                        ast.Name,
                    )
                    or _identifier(
                        raised_call.args[0].func.id
                    ) != "_main"
                    or raised_call.args[0].args
                    or raised_call.args[0].keywords
                ):
                    _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
            else:
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
        if isinstance(node, ast.Name):
            name = _identifier(node.id)
            if _name_is_banned(name, forbidden_names):
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            if (
                isinstance(node.ctx, ast.Store)
                and (
                    name in imported_modules
                    or name in _ALLOWED_DIRECT_CALL_NAMES
                    or name in defined_functions
                )
            ):
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            if name in imported_modules:
                parent = parents.get(node)
                if not (
                    isinstance(parent, ast.Attribute)
                    and parent.value is node
                ):
                    _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
        if isinstance(node, ast.Attribute):
            attribute = _identifier(node.attr)
            if _name_is_banned(attribute, forbidden_names):
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            dotted = _dotted_name(node)
            if dotted is not None and dotted in forbidden_names:
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            path = _attribute_path(node)
            if path is not None and path[0] in imported_modules:
                if not isinstance(node.ctx, ast.Load):
                    _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
                if path[1] not in _ALLOWED_MODULE_ATTRIBUTE_PATHS[path[0]]:
                    _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            elif attribute not in _ALLOWED_DATA_ATTRIBUTE_NAMES:
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
            if attribute == "format":
                parent = parents.get(node)
                if not (
                    isinstance(parent, ast.Call)
                    and parent.func is node
                ):
                    _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
            parent = parents.get(node)
            if not (
                (
                    isinstance(parent, ast.Attribute)
                    and parent.value is node
                )
                or (
                    isinstance(parent, ast.Call)
                    and parent.func is node
                )
                or _is_exception_type_attribute(node, parents)
            ):
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
        if isinstance(node, ast.Import) and parents.get(node) is not tree:
            _fail(OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN)
        if isinstance(node, ast.alias):
            _identifier(node.name)
            if node.asname is not None:
                _fail(OracleSourcePolicyCode.POLICY_IMPORT_FORBIDDEN)
        if isinstance(node, ast.keyword):
            if node.arg is None:
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
            if _name_is_banned(_identifier(node.arg), forbidden_names):
                _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
        if isinstance(node, ast.Constant):
            _validate_literal(node.value)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_name = _identifier(node.func.id)
                if (
                    call_name not in _ALLOWED_DIRECT_CALL_NAMES
                    and call_name not in defined_functions
                ):
                    _fail(OracleSourcePolicyCode.POLICY_NAME_FORBIDDEN)
                if call_name == "type" and (
                    len(node.args) != 1 or node.keywords
                ):
                    _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
                if call_name == "ValueError" and (
                    node.args or node.keywords
                ):
                    _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
                if call_name == "sorted":
                    if len(node.args) != 1:
                        _fail(
                            OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN
                        )
                    if node.keywords:
                        if (
                            len(node.keywords) != 1
                            or node.keywords[0].arg != "key"
                            or not isinstance(
                                node.keywords[0].value,
                                ast.Name,
                            )
                            or _identifier(
                                node.keywords[0].value.id
                            ) not in defined_functions
                        ):
                            _fail(
                                OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN
                            )
            elif not isinstance(node.func, ast.Attribute):
                _fail(OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN)
            else:
                path = _attribute_path(node.func)
                if node.func.attr == "format":
                    receiver = node.func.value
                    if (
                        not isinstance(receiver, ast.Constant)
                        or type(receiver.value) is not str
                        or _SAFE_FORMAT_LITERAL_RE.fullmatch(
                            receiver.value
                        ) is None
                        or receiver.value.count("{}") != len(node.args)
                        or node.keywords
                    ):
                        _fail(
                            OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN
                        )
                if path == ("json", ("dumps",)):
                    keyword_names = tuple(
                        keyword.arg for keyword in node.keywords
                    )
                    if (
                        len(node.args) != 1
                        or set(keyword_names)
                        != {
                            "allow_nan",
                            "ensure_ascii",
                            "separators",
                            "sort_keys",
                        }
                    ):
                        _fail(
                            OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN
                        )
                if path == ("json", ("loads",)):
                    expected_keywords = (
                        "object_pairs_hook",
                        "parse_int",
                        "parse_float",
                        "parse_constant",
                    )
                    if (
                        len(node.args) != 1
                        or tuple(
                            keyword.arg for keyword in node.keywords
                        )
                        != expected_keywords
                        or any(
                            not isinstance(keyword.value, ast.Name)
                            or _identifier(keyword.value.id)
                            not in defined_functions
                            for keyword in node.keywords
                        )
                    ):
                        _fail(
                            OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN
                        )
                if path == ("sys", ("stdin", "buffer", "read")):
                    if (
                        len(node.args) != 1
                        or node.keywords
                        or not isinstance(node.args[0], ast.Constant)
                        or type(node.args[0].value) is not int
                        or node.args[0].value
                        != MAXIMUM_ORACLE_WORKER_STDIN_READ_BYTES
                    ):
                        _fail(
                            OracleSourcePolicyCode.POLICY_SYNTAX_FORBIDDEN
                        )


@dataclass(frozen=True)
class OracleSourcePolicyReceiptV1:
    """Canonical static-policy receipt; never execution evidence."""

    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    forbidden_import_ids: Tuple[str, ...]
    forbidden_name_ids: Tuple[str, ...]
    allowed_import_ids: Tuple[str, ...] = field(
        default=ALLOWED_ORACLE_SOURCE_IMPORT_IDS,
        init=False,
    )
    artifact_type: str = field(
        default=ORACLE_SOURCE_POLICY_ARTIFACT_TYPE,
        init=False,
    )
    decision_eligible: bool = field(default=False, init=False)
    format_version: str = field(default="1", init=False)
    parser_id: str = field(
        default=ORACLE_SOURCE_PARSER_ID,
        init=False,
    )
    policy_id: str = field(
        default=ORACLE_SOURCE_POLICY_ID,
        init=False,
    )
    status_id: str = field(
        default=ORACLE_SOURCE_POLICY_STATUS,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not OracleSourcePolicyReceiptV1:
            raise TypeError("oracle source policy receipt must be exact")
        try:
            _token(self.oracle_id)
            if (
                type(self.oracle_source_byte_count) is not int
                or self.oracle_source_byte_count <= 0
                or self.oracle_source_byte_count
                > MAXIMUM_ORACLE_SOURCE_BYTES
            ):
                raise TypeError("oracle source byte count is invalid")
            _digest(self.oracle_source_sha256)
            imports = _ban_tuple(self.forbidden_import_ids)
            names = _ban_tuple(self.forbidden_name_ids)
        except OracleSourcePolicyError as error:
            raise TypeError("oracle source policy receipt is invalid") from error
        if imports != self.forbidden_import_ids:
            raise TypeError("oracle source import bans are invalid")
        if names != self.forbidden_name_ids:
            raise TypeError("oracle source name bans are invalid")
        if self.allowed_import_ids != ALLOWED_ORACLE_SOURCE_IMPORT_IDS:
            raise TypeError("oracle source allowed imports are not fixed")
        if (
            self.artifact_type != ORACLE_SOURCE_POLICY_ARTIFACT_TYPE
            or self.decision_eligible is not False
            or self.format_version != "1"
            or self.parser_id != ORACLE_SOURCE_PARSER_ID
            or self.policy_id != ORACLE_SOURCE_POLICY_ID
            or self.status_id != ORACLE_SOURCE_POLICY_STATUS
        ):
            raise TypeError("oracle source policy receipt constants differ")


@dataclass(frozen=True)
class ValidatedOracleSourcePolicyV1:
    """Structurally validated receipt transport plus its commitment.

    Construction alone is not evidence that the represented source passed the
    static policy.  A consumer at a trust boundary must call
    :func:`validate_validated_oracle_source_policy` with the exact source bytes.
    """

    receipt: OracleSourcePolicyReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ValidatedOracleSourcePolicyV1:
            raise TypeError("validated oracle source policy must be exact")
        trusted_receipt = validate_oracle_source_policy_receipt(self.receipt)
        if type(self.receipt_bytes) is not bytes:
            raise TypeError("oracle source policy bytes must be exact")
        expected_bytes = oracle_source_policy_receipt_bytes(trusted_receipt)
        expected_sha256 = oracle_source_policy_receipt_sha256(trusted_receipt)
        if (
            self.receipt_bytes != expected_bytes
            or type(self.receipt_sha256) is not str
            or self.receipt_sha256 != expected_sha256
        ):
            raise TypeError("validated oracle source policy differs")


_RECEIPT_KEYS = (
    "allowed_import_ids",
    "artifact_type",
    "decision_eligible",
    "forbidden_import_ids",
    "forbidden_name_ids",
    "format_version",
    "oracle_id",
    "oracle_source_byte_count",
    "oracle_source_sha256",
    "parser_id",
    "policy_id",
    "status_id",
)


def validate_oracle_source_policy_receipt(
    value: object,
) -> OracleSourcePolicyReceiptV1:
    """Return a fresh, recursively validated exact receipt."""

    if type(value) is not OracleSourcePolicyReceiptV1:
        raise TypeError("oracle source policy receipt must be exact")
    try:
        return OracleSourcePolicyReceiptV1(
            oracle_id=value.oracle_id,
            oracle_source_byte_count=value.oracle_source_byte_count,
            oracle_source_sha256=value.oracle_source_sha256,
            forbidden_import_ids=value.forbidden_import_ids,
            forbidden_name_ids=value.forbidden_name_ids,
        )
    except (AttributeError, TypeError, ValueError):
        raise TypeError("oracle source policy receipt is invalid") from None


def validate_validated_oracle_source_policy(
    value: object,
    source_bytes: bytes,
) -> ValidatedOracleSourcePolicyV1:
    """Rerun the static policy on exact source and return a fresh transport."""

    if type(value) is not ValidatedOracleSourcePolicyV1:
        raise TypeError("validated oracle source policy must be exact")
    try:
        receipt = validate_oracle_source_policy_receipt(value.receipt)
        expected = validate_oracle_source_policy(
            source_bytes,
            oracle_id=receipt.oracle_id,
            oracle_source_byte_count=receipt.oracle_source_byte_count,
            oracle_source_sha256=receipt.oracle_source_sha256,
            forbidden_import_ids=receipt.forbidden_import_ids,
            forbidden_name_ids=receipt.forbidden_name_ids,
        )
        if (
            type(value.receipt_bytes) is not bytes
            or type(value.receipt_sha256) is not str
            or value.receipt_bytes != expected.receipt_bytes
            or value.receipt_sha256 != expected.receipt_sha256
        ):
            raise TypeError
        return expected
    except OracleSourcePolicyError:
        raise TypeError(
            "validated oracle source policy is invalid"
        ) from None
    except (AttributeError, TypeError, ValueError):
        raise TypeError("validated oracle source policy is invalid") from None


def oracle_source_policy_receipt_tree(
    value: OracleSourcePolicyReceiptV1,
) -> dict:
    """Return the exact plain canonical receipt projection."""

    trusted = validate_oracle_source_policy_receipt(value)
    return {
        name: (
            list(getattr(trusted, name))
            if name.endswith("_ids")
            else getattr(trusted, name)
        )
        for name in _RECEIPT_KEYS
    }


def oracle_source_policy_receipt_bytes(
    value: OracleSourcePolicyReceiptV1,
) -> bytes:
    """Return bounded ASCII canonical JSON for one policy receipt."""

    try:
        result = json.dumps(
            oracle_source_policy_receipt_tree(value),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(OracleSourcePolicyCode.POLICY_CANONICALIZATION)
    if not result or len(result) > MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES:
        _fail(OracleSourcePolicyCode.POLICY_CANONICALIZATION)
    return result


def oracle_source_policy_receipt_sha256(
    value: OracleSourcePolicyReceiptV1,
) -> str:
    """Return the receipt's domain-separated SHA-256 commitment."""

    payload = oracle_source_policy_receipt_bytes(value)
    digest = hashlib.sha256()
    digest.update(ORACLE_SOURCE_POLICY_DIGEST_DOMAIN)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def validate_oracle_source_policy(
    source_bytes: bytes,
    *,
    oracle_id: str,
    oracle_source_byte_count: int,
    oracle_source_sha256: str,
    forbidden_import_ids: Tuple[str, ...],
    forbidden_name_ids: Tuple[str, ...],
) -> ValidatedOracleSourcePolicyV1:
    """Validate one exact source under the fixed, non-executing policy."""

    source, source_count, source_digest = _source_identity(
        source_bytes,
        oracle_source_byte_count,
        oracle_source_sha256,
    )
    oracle = _token(oracle_id)
    import_bans = _ban_tuple(forbidden_import_ids)
    name_bans = _ban_tuple(forbidden_name_ids)
    text = _decode_source(source)
    _lexical_preflight(text)
    tree = _parse_source(text)
    _validate_policy_tree(
        tree,
        forbidden_imports=import_bans,
        forbidden_names=name_bans,
    )
    receipt = OracleSourcePolicyReceiptV1(
        oracle_id=oracle,
        oracle_source_byte_count=source_count,
        oracle_source_sha256=source_digest,
        forbidden_import_ids=import_bans,
        forbidden_name_ids=name_bans,
    )
    receipt_bytes = oracle_source_policy_receipt_bytes(receipt)
    receipt_sha256 = oracle_source_policy_receipt_sha256(receipt)
    return ValidatedOracleSourcePolicyV1(
        receipt=receipt,
        receipt_bytes=receipt_bytes,
        receipt_sha256=receipt_sha256,
    )


__all__ = [
    "ALLOWED_ORACLE_SOURCE_IMPORT_IDS",
    "MAXIMUM_ORACLE_POLICY_BANS",
    "MAXIMUM_ORACLE_SOURCE_AST_DEPTH",
    "MAXIMUM_ORACLE_SOURCE_AST_NODES",
    "MAXIMUM_ORACLE_SOURCE_BRACKET_DEPTH",
    "MAXIMUM_ORACLE_SOURCE_BYTES",
    "MAXIMUM_ORACLE_SOURCE_INDENT_DEPTH",
    "MAXIMUM_ORACLE_SOURCE_LINE_BYTES",
    "MAXIMUM_ORACLE_SOURCE_LINES",
    "MAXIMUM_ORACLE_SOURCE_LITERAL_BYTES",
    "MAXIMUM_ORACLE_SOURCE_TOKENS",
    "MAXIMUM_ORACLE_SOURCE_TOKEN_BYTES",
    "MAXIMUM_ORACLE_WORKER_STDIN_READ_BYTES",
    "ORACLE_SOURCE_PARSER_ID",
    "ORACLE_SOURCE_POLICY_ARTIFACT_TYPE",
    "ORACLE_SOURCE_POLICY_DIGEST_DOMAIN",
    "ORACLE_SOURCE_POLICY_ID",
    "ORACLE_SOURCE_POLICY_STATUS",
    "OracleSourcePolicyCode",
    "OracleSourcePolicyError",
    "OracleSourcePolicyReceiptV1",
    "ValidatedOracleSourcePolicyV1",
    "oracle_source_policy_receipt_bytes",
    "oracle_source_policy_receipt_sha256",
    "oracle_source_policy_receipt_tree",
    "validate_oracle_source_policy",
    "validate_oracle_source_policy_receipt",
    "validate_validated_oracle_source_policy",
]
