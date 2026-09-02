#!/usr/bin/env python3
"""Hash-first validator for the Retail public-documentation selector package."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import Any, Dict, Iterable, Tuple


MACHINE_DOMAIN = b"heterodiff/retail/public-documentation-selector-machine/v1\0"
SELECTOR_DOMAIN = b"heterodiff/retail/public-documentation-selector-core/v1\0"

PACKAGE_FILES = (
    (
        "PROJECT_RETAIL_PUBLIC_DOCUMENTATION_ACQUISITION_SELECTOR_V1.md",
        6569,
        "cd920ff38f6478b91d3e763206abbe175fe407335edbc09d07dcc062dc51db0f",
    ),
    (
        "src/heterodiff/data/retail_public_documentation_acquisition_selector.py",
        17279,
        "225d82fd1449eeb709674e4395f5b1e683d895621aef30344b0f877d5a39be4f",
    ),
    (
        "research/fixtures/manuscript_v3_retail_public_documentation_acquisition_selector_v1.json",
        8910,
        "6cf978a194899778c6bf1c2de4eb535a91f6ca490a5cbee8328d5558ef1f782e",
    ),
)

PREDECESSORS = (
    (
        "research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json",
        17729,
        "340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c",
    ),
    (
        "PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS_INDEPENDENT_REVIEW.md",
        10999,
        "951efca8ae87a6aab80c6dbd9e07bb42769fcf0424eb544e6d90c4cb94cdffa3",
    ),
    (
        "research/fixtures/manuscript_v3_b02_b03_offline_precontact_activation_v1.json",
        22137,
        "d74333a2c381daa953803e9346efb0ab63d6744265bfa8e7e260b1d1932fc0ee",
    ),
    (
        "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION_INDEPENDENT_REVIEW.md",
        10196,
        "a1baf2b04740ac38540a4008dcb09042f8c92fa978c51fe22ac54cb30c81f0d0",
    ),
    (
        "research/fixtures/manuscript_v3_b02_b03_b09_external_evidence_intake_v1.json",
        11920,
        "af4d46e652d24d71382a746e3a043491c2f978275098e266e6f77f4286906a9f",
    ),
    (
        "PROJECT_B02_B03_B09_EXTERNAL_EVIDENCE_INTAKE_INDEPENDENT_REVIEW.md",
        7792,
        "f69e29bebcee4f16eea354e2810085de8e0df4c07570e1aec378e96c70132101",
    ),
    (
        "research/fixtures/manuscript_v3_f061_preservation_first_allocation_proposal_v1.json",
        15037,
        "4a6414b494328a7f7cd4030718af960764bb2ce1946fb7de093985983e725d32",
    ),
    (
        "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_INDEPENDENT_REVIEW.md",
        6841,
        "053de959f3fffabf0da21a4c9e997b96e170f1fbc4b9295d71fef8e8347835eb",
    ),
)

SOURCE_ASSIGNMENTS = (
    "SCHEMA_VERSION",
    "PACKAGE_STATE",
    "PUBLIC_DOCUMENTATION_RECORD",
    "ACQUISITION_SELECTOR_CORE",
    "EXTERNAL_READINESS_CHECKLIST",
    "NONCLAIMS",
)


class ValidationError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ValidationError("NONCANONICAL_VALUE") from error


def _strict_json(raw: bytes) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValidationError("MACHINE_NON_ASCII") from error
    if not text.endswith("\n") or text.endswith("\n\n"):
        raise ValidationError("MACHINE_TERMINAL_LF_INVALID")
    duplicates = []

    def hook(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
        value: Dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    try:
        value = json.loads(
            text,
            object_pairs_hook=hook,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValidationError("MACHINE_FORBIDDEN_JSON_CONSTANT:" + token)
            ),
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValidationError("MACHINE_JSON_MALFORMED") from error
    if duplicates:
        raise ValidationError("MACHINE_DUPLICATE_JSON_KEY")
    if type(value) is not dict:
        raise ValidationError("MACHINE_ROOT_NOT_OBJECT")
    if raw != _canonical(value) + b"\n":
        raise ValidationError("MACHINE_BYTES_NONCANONICAL")
    return value


def _safe_parts(relative: str) -> Tuple[str, ...]:
    path = PurePosixPath(relative)
    parts = path.parts
    if (
        not parts
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in parts)
    ):
        raise ValidationError("UNSAFE_RELATIVE_PATH:" + relative)
    return tuple(parts)


def _open_root(root: Path) -> Tuple[int, os.stat_result]:
    if not root.is_absolute():
        raise ValidationError("ROOT_NOT_ABSOLUTE")
    try:
        before = os.lstat(root)
    except OSError as error:
        raise ValidationError("ROOT_LSTAT_FAILED") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise ValidationError("ROOT_NOT_PHYSICAL_DIRECTORY")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(root, flags)
    except OSError as error:
        raise ValidationError("ROOT_OPEN_FAILED") from error
    opened = os.fstat(descriptor)
    if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
        os.close(descriptor)
        raise ValidationError("ROOT_IDENTITY_CHANGED")
    return descriptor, opened


def _read_once(root_fd: int, relative: str) -> Tuple[bytes, Tuple[int, int, int, int]]:
    parts = _safe_parts(relative)
    current = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            flags = (
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                following = os.open(part, flags, dir_fd=current)
            except OSError as error:
                raise ValidationError("PARENT_COMPONENT_OPEN_FAILED:" + relative) from error
            parent_stat = os.fstat(following)
            if not stat.S_ISDIR(parent_stat.st_mode):
                os.close(following)
                raise ValidationError("PARENT_COMPONENT_NOT_DIRECTORY:" + relative)
            os.close(current)
            current = following
        try:
            leaf = os.open(
                parts[-1],
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
        except OSError as error:
            raise ValidationError("LEAF_OPEN_FAILED:" + relative) from error
        try:
            first = os.fstat(leaf)
            if not stat.S_ISREG(first.st_mode):
                raise ValidationError("LEAF_NOT_REGULAR:" + relative)
            if stat.S_IMODE(first.st_mode) != 0o644:
                raise ValidationError("LEAF_MODE_NOT_0644:" + relative)
            if first.st_nlink != 1:
                raise ValidationError("LEAF_LINK_COUNT_NOT_ONE:" + relative)
            chunks = []
            while True:
                chunk = os.read(leaf, 1 << 20)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
            second = os.fstat(leaf)
            identity = (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns)
            if identity != (
                second.st_dev,
                second.st_ino,
                second.st_size,
                second.st_mtime_ns,
            ) or len(raw) != first.st_size:
                raise ValidationError("LEAF_CHANGED_DURING_READ:" + relative)
            return raw, identity
        finally:
            os.close(leaf)
    finally:
        os.close(current)


def _capture(root_fd: int, relative: str, size: int, digest: str) -> bytes:
    first, identity_one = _read_once(root_fd, relative)
    second, identity_two = _read_once(root_fd, relative)
    if identity_one != identity_two or first != second:
        raise ValidationError("LEAF_REOPEN_DRIFT:" + relative)
    if len(first) != size:
        raise ValidationError("BYTE_COUNT_MISMATCH:" + relative)
    if hashlib.sha256(first).hexdigest() != digest:
        raise ValidationError("RAW_SHA256_MISMATCH:" + relative)
    return first


def _source_literals(raw: bytes) -> Dict[str, Any]:
    try:
        tree = ast.parse(raw.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("SOURCE_SYNTAX_INVALID") from error
    found: Dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in SOURCE_ASSIGNMENTS:
                if target.id in found:
                    raise ValidationError("SOURCE_ASSIGNMENT_DUPLICATE:" + target.id)
                try:
                    found[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError) as error:
                    raise ValidationError("SOURCE_ASSIGNMENT_NONLITERAL:" + target.id) from error
    if tuple(found.keys()) != SOURCE_ASSIGNMENTS:
        raise ValidationError("SOURCE_ASSIGNMENT_ROSTER_OR_ORDER_MISMATCH")
    allowed_import_roots = {"__future__", "hashlib", "json", "re", "typing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] not in allowed_import_roots for alias in node.names):
                raise ValidationError("SOURCE_IMPORT_BOUNDARY_EXPANDED")
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in allowed_import_roots:
                raise ValidationError("SOURCE_IMPORT_BOUNDARY_EXPANDED")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"open", "exec", "eval", "compile", "__import__"}:
                raise ValidationError("SOURCE_IO_OR_DYNAMIC_EXECUTION_CALL")
    return found


def validate(root: Path) -> Dict[str, Any]:
    root_fd, root_identity = _open_root(root)
    try:
        package_raw = {
            path: _capture(root_fd, path, size, digest)
            for path, size, digest in PACKAGE_FILES
        }
        for path, size, digest in PREDECESSORS:
            _capture(root_fd, path, size, digest)
        final_root = os.fstat(root_fd)
        if (root_identity.st_dev, root_identity.st_ino) != (
            final_root.st_dev,
            final_root.st_ino,
        ):
            raise ValidationError("ROOT_IDENTITY_CHANGED_DURING_VALIDATION")
    finally:
        os.close(root_fd)

    machine_path = PACKAGE_FILES[2][0]
    machine = _strict_json(package_raw[machine_path])
    semantic = machine.get("semantic_sha256")
    if type(semantic) is not str:
        raise ValidationError("MACHINE_SEMANTIC_SHA256_ABSENT")
    semantic_payload = dict(machine)
    del semantic_payload["semantic_sha256"]
    if hashlib.sha256(MACHINE_DOMAIN + _canonical(semantic_payload)).hexdigest() != semantic:
        raise ValidationError("MACHINE_SEMANTIC_SHA256_MISMATCH")

    source = _source_literals(package_raw[PACKAGE_FILES[1][0]])
    if machine.get("schema_version") != (
        "heterodiff-retail-public-documentation-acquisition-selector-machine-v1"
    ):
        raise ValidationError("MACHINE_SCHEMA_MISMATCH")
    if machine.get("package_state") != source["PACKAGE_STATE"]:
        raise ValidationError("PACKAGE_STATE_MISMATCH")
    if machine.get("public_documentation_record") != source[
        "PUBLIC_DOCUMENTATION_RECORD"
    ]:
        raise ValidationError("PUBLIC_DOCUMENTATION_RECORD_MISMATCH")
    if machine.get("selector_core") != source["ACQUISITION_SELECTOR_CORE"]:
        raise ValidationError("SELECTOR_CORE_MISMATCH")
    checklist = json.loads(_canonical(source["EXTERNAL_READINESS_CHECKLIST"]))
    if machine.get("external_readiness_checklist") != checklist:
        raise ValidationError("READINESS_CHECKLIST_MISMATCH")
    if machine.get("nonclaims") != source["NONCLAIMS"]:
        raise ValidationError("NONCLAIMS_MISMATCH")
    selector_sha = hashlib.sha256(
        SELECTOR_DOMAIN + _canonical(source["ACQUISITION_SELECTOR_CORE"])
    ).hexdigest()
    if machine.get("selector_core_sha256") != selector_sha:
        raise ValidationError("SELECTOR_CORE_SHA256_MISMATCH")

    expected_bindings = {
        "human": {
            "path": PACKAGE_FILES[0][0],
            "bytes": PACKAGE_FILES[0][1],
            "raw_sha256": PACKAGE_FILES[0][2],
        },
        "source": {
            "path": PACKAGE_FILES[1][0],
            "bytes": PACKAGE_FILES[1][1],
            "raw_sha256": PACKAGE_FILES[1][2],
        },
    }
    if machine.get("package_bindings") != expected_bindings:
        raise ValidationError("PACKAGE_BINDINGS_MISMATCH")
    expected_predecessors = [
        {"path": path, "bytes": size, "raw_sha256": digest}
        for path, size, digest in PREDECESSORS
    ]
    if machine.get("accepted_predecessor_bindings") != expected_predecessors:
        raise ValidationError("PREDECESSOR_BINDINGS_MISMATCH")

    current = machine.get("current_readiness")
    identifiers = [row["obligation_id"] for row in checklist]
    if current != {
        "decision": "HOLD_REAL_RETAIL_EVIDENCE_INCOMPLETE",
        "completed_count": 0,
        "remaining_obligation_ids": identifiers,
        "field_closure_authorized": False,
        "blocker_closure_authorized": False,
    }:
        raise ValidationError("CURRENT_READINESS_MISMATCH")
    boundary = machine.get("closure_boundary")
    if (
        type(boundary) is not dict
        or boundary.get("eligible_field_ids") != []
        or boundary.get("eligible_blocker_ids") != []
        or boundary.get("tracker_or_ledger_edit_authorized") is not False
        or boundary.get("open_field_ids_preserved")
        != ["F038", "F039", "F041", "F053", "F054", "F059"]
        or boundary.get("open_blocker_ids_preserved") != ["B03", "B09"]
    ):
        raise ValidationError("CLOSURE_BOUNDARY_MISMATCH")
    verification = machine.get("official_verification_boundary")
    if (
        type(verification) is not dict
        or verification.get("official_page_semantics_checked") is not True
        or verification.get("dataset_bytes_requested_or_stored") is not False
        or verification.get("immutable_revision_observed") is not False
        or verification.get("raw_archive_sha256_observed") is not False
    ):
        raise ValidationError("OFFICIAL_VERIFICATION_BOUNDARY_MISMATCH")
    return {
        "decision": "PASS_RETAIL_PUBLIC_DOCUMENTATION_SELECTOR_NO_FIELD_CLOSURE",
        "machine_raw_sha256": PACKAGE_FILES[2][2],
        "machine_semantic_sha256": semantic,
        "selector_core_sha256": selector_sha,
        "readiness_obligation_count": len(identifiers),
        "eligible_field_ids": [],
        "eligible_blocker_ids": [],
        "tracker_or_ledger_edit_authorized": False,
    }


def main() -> int:
    root = (
        Path(sys.argv[1])
        if len(sys.argv) == 2
        else Path(__file__).absolute().parents[2]
    )
    try:
        result = validate(root)
    except (ValidationError, OSError, ValueError, TypeError) as error:
        print("FAIL:" + str(error), file=sys.stderr)
        return 1
    print(_canonical(result).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
