#!/usr/bin/env python3
"""Read-only hash-first validator for the AWS Databricks B08 bundle."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import types


ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "PROJECT_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE.md": (
        25_824,
        "28b064a60e07e9179a4a870b97cf0ad8deb8503018555d486a36c8c941fc2dc4",
    ),
    "src/heterodiff/experiments/b08_databricks_aws_qualification.py": (
        24_825,
        "632bb5dd078cd91b9c7e4148e5d284d499f91f4ee5697df52a73e279f3c78e1f",
    ),
    "research/diagnostics/b08_databricks_aws_qualification_capture_v1.py": (
        39_191,
        "f1123e302f1f7731570d0649af45ed7fc881c7d4487beda29578a741d0b75642",
    ),
    "research/fixtures/manuscript_v3_b08_databricks_aws_qualification_template_v1.json": (
        3_834,
        "d5a31b69ee3a4aa586bc040c49d12d05e13fc11d66b81f1ef3a05db4958470ca",
    ),
    "research/fixtures/manuscript_v3_b08_databricks_aws_admin_storage_reservation_template_v1.json": (
        1_175,
        "f8a910f8c3d8c9458b7c68de18adcefc439fa2975f8fa83957ad2af1755ec8cf",
    ),
    "tests/unit/test_b08_databricks_aws_qualification.py": (
        8_568,
        "8a76dfd44c6542748b1911dceee49f03fb1b412de337b892aece78b470caaf60",
    ),
    "tests/unit/test_b08_databricks_aws_qualification_capture_v1.py": (
        7_244,
        "ee95a5dc522ab0ba3ee5ac25b3e8f23f8fd4a7cd0e374947df3f4196dad1ec9c",
    ),
}


class ValidationError(RuntimeError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def read_bound_file(relative_path: str) -> bytes:
    components = Path(relative_path).parts
    if (
        not components
        or Path(relative_path).is_absolute()
        or any(component in ("", ".", "..") for component in components)
    ):
        raise ValidationError(relative_path + ": unsafe relative path")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    leaf_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(ROOT, directory_flags)
    descriptor = -1
    try:
        for component in components[:-1]:
            next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        descriptor = os.open(components[-1], leaf_flags, dir_fd=directory_fd)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or stat.S_IMODE(before.st_mode) & 0o022
        ):
            raise ValidationError(
                relative_path + ": custody is not one non-writable regular link"
            )
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(1 << 20, remaining))
            if not chunk:
                raise ValidationError(relative_path + ": truncated during read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise ValidationError(relative_path + ": grew during read")
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValidationError(relative_path + ": identity changed during read")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(directory_fd)
    expected_bytes, expected_sha256 = EXPECTED[relative_path]
    if len(raw) != expected_bytes:
        raise ValidationError(relative_path + ": byte count differs")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValidationError(relative_path + ": raw SHA-256 differs")
    return raw


def load_hash_first_core(raw: bytes):
    module = types.ModuleType("_bound_b08_databricks_aws_qualification")
    module.__file__ = "<bound-b08-databricks-aws-qualification>"
    exec(compile(raw, module.__file__, "exec"), module.__dict__)
    return module


def parse_canonical_object(raw: bytes, label: str) -> dict:
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(label + ": invalid ASCII JSON") from error
    if type(value) is not dict or raw != canonical_json_bytes(value) + b"\n":
        raise ValidationError(label + ": noncanonical JSON bytes")
    return value


def tracker_counts() -> tuple[int, int]:
    text = (ROOT / "PROJECT_COMPLETION_TIMETABLE.md").read_text(encoding="utf-8")
    checked = len(re.findall(r"(?m)^- \[x\]", text))
    opened = len(re.findall(r"(?m)^- \[ \]", text))
    return checked, opened


def ledger_counts() -> dict:
    text = (ROOT / "PROJECT_EVIDENCE_LEDGER.md").read_text(encoding="utf-8")
    fields = {("PRE", "OPEN"): 0, ("PRE", "CLOSED"): 0, ("POST", "OPEN"): 0, ("POST", "CLOSED"): 0}
    blockers = {"OPEN": 0, "CLOSED": 0}
    b08_status = None
    for line in text.splitlines():
        if re.match(r"^\| F[0-9]{3} \| (PRE|POST) \|", line):
            cells = [cell.strip() for cell in line.split("|")]
            key = (cells[2], cells[6])
            if key not in fields:
                raise ValidationError("unexpected field status row")
            fields[key] += 1
        blocker = re.match(r"^\| (B(?:0[1-9]|1[0-2])) \|", line)
        if blocker:
            cells = [cell.strip() for cell in line.split("|")]
            status = cells[5]
            if status not in blockers:
                raise ValidationError("unexpected blocker status row")
            blockers[status] += 1
            if blocker.group(1) == "B08":
                b08_status = status
    if "Formal Test 28 `OPEN`; Formal Test 29 `OPEN`; Formal Test 30 `PENDING`" not in text:
        raise ValidationError("formal-test status boundary differs")
    return {"fields": fields, "blockers": blockers, "b08_status": b08_status}


def validate() -> dict:
    sealed = {path: read_bound_file(path) for path in EXPECTED}
    core = load_hash_first_core(
        sealed["src/heterodiff/experiments/b08_databricks_aws_qualification.py"]
    )
    template = parse_canonical_object(
        sealed["research/fixtures/manuscript_v3_b08_databricks_aws_qualification_template_v1.json"],
        "qualification template",
    )
    if core.validate_record(template) != template:
        raise ValidationError("qualification HOLD template did not round-trip")
    if template["semantic_disposition"] != core.HOLD_INCOMPLETE:
        raise ValidationError("qualification template is not HOLD")
    if template["project_effects"] != core._project_effects():
        raise ValidationError("qualification template project effect is not zero")

    admin = parse_canonical_object(
        sealed["research/fixtures/manuscript_v3_b08_databricks_aws_admin_storage_reservation_template_v1.json"],
        "admin storage template",
    )
    if (
        admin.get("record_state") != "HOLD_UNPOPULATED_TEMPLATE"
        or admin.get("externally_verified") is not False
        or admin.get("project_effects")
        != {
            "b08_closed": False,
            "blocker_count_delta": 0,
            "field_count_delta": 0,
            "timetable_checkbox_delta": 0,
        }
    ):
        raise ValidationError("admin storage template boundary differs")

    checked, opened = tracker_counts()
    if (checked, opened) != (62, 101):
        raise ValidationError("tracker counts differ from zero-delta checkpoint")
    ledger = ledger_counts()
    if ledger["fields"] != {
        ("PRE", "OPEN"): 23,
        ("PRE", "CLOSED"): 143,
        ("POST", "OPEN"): 1,
        ("POST", "CLOSED"): 5,
    }:
        raise ValidationError("field counts differ from zero-delta checkpoint")
    if ledger["blockers"] != {"OPEN": 7, "CLOSED": 5} or ledger["b08_status"] != "OPEN":
        raise ValidationError("blocker boundary differs")

    return {
        "decision": "PASS_DATABRICKS_AWS_QUALIFICATION_BUNDLE_HOLD_NO_CLOSURE",
        "b08": "OPEN",
        "calibration_authorized": False,
        "field_delta": 0,
        "blocker_delta": 0,
        "timetable_delta": 0,
        "formal_tests": ["OPEN", "OPEN", "PENDING"],
        "marked_tasks": {"checked": checked, "open": opened, "total": checked + opened},
        "sealed_file_count": len(sealed),
        "template_record_sha256": template["record_sha256"],
    }


if __name__ == "__main__":
    try:
        result = validate()
    except (OSError, ValueError, TypeError, ValidationError) as error:
        print("FAIL_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE:" + str(error))
        raise SystemExit(1)
    print("PASS_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE_HOLD_NO_CLOSURE")
    print(canonical_json_bytes(result).decode("ascii"))
