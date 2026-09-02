#!/usr/bin/env python3
"""Read-only validator for the B08 Wave-2 local-capacity preflight."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from heterodiff.experiments import b08_wave2_capacity_preflight as preflight


MACHINE_PATH = Path(
    "research/fixtures/manuscript_v3_b08_wave2_capacity_preflight_v1.json"
)
MAX_FILE_BYTES = 8_000_000


def _read_regular(relative: Path, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("path must be safe and relative")
    path = ROOT / relative
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ValueError("file must be a regular single-link file: " + str(relative))
    if stat.S_IMODE(before.st_mode) != 0o644:
        raise ValueError("file mode must be 0644: " + str(relative))
    if before.st_size < 1 or before.st_size > maximum:
        raise ValueError("file size is out of bounds: " + str(relative))
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_size) != (
            before.st_dev, before.st_ino, before.st_size
        ):
            raise ValueError("file identity changed while opening")
        chunks = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(1 << 20, remaining))
            if not chunk:
                raise ValueError("short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        if (after.st_dev, after.st_ino, after.st_size) != (
            opened.st_dev, opened.st_ino, opened.st_size
        ):
            raise ValueError("file identity changed while reading")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _object_pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _parse_machine(raw: bytes):
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ValueError("machine record must have one terminal LF")
    try:
        raw[:-1].decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("machine record must be ASCII") from error
    record = json.loads(
        raw,
        object_pairs_hook=_object_pairs_no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError("non-finite JSON token: " + value)
        ),
    )
    if raw != preflight.canonical_json_bytes(record) + b"\n":
        raise ValueError("machine record is not canonical JSON")
    return record


def validate():
    raw = _read_regular(MACHINE_PATH)
    record = _parse_machine(raw)
    validated = preflight.validate_machine_record(record)

    for binding in validated["predecessor_bindings"]:
        relative = Path(binding["path"])
        predecessor = _read_regular(relative)
        if len(predecessor) != binding["bytes"]:
            raise ValueError("predecessor size differs: " + binding["path"])
        digest = hashlib.sha256(predecessor).hexdigest()
        if digest != binding["raw_sha256"]:
            raise ValueError("predecessor digest differs: " + binding["path"])

    cp50 = json.loads(
        _read_regular(Path("research/fixtures/cp50_test28_mixed_initializer_v26.json")),
        object_pairs_hook=_object_pairs_no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError("non-finite predecessor JSON token: " + value)
        ),
    )
    cp64 = cp50["execution_design"]["cp64_production_custody_preflight"]
    arithmetic = validated["supported_projection"]["capacity_arithmetic"]
    required_equalities = {
        "global_destination_reservation_bytes": arithmetic[
            "destination_reservation_bytes"
        ],
        "global_auxiliary_metadata_reservation_bytes": arithmetic[
            "auxiliary_reservation_bytes"
        ],
        "global_combined_reservation_bytes": arithmetic[
            "combined_reservation_bytes"
        ],
    }
    for key, expected in required_equalities.items():
        if type(cp64.get(key)) is not int or cp64[key] != expected:
            raise ValueError("CP64 capacity operand differs: " + key)
    for key in ("capacity_measured", "capacity_receipt_present", "production_resources_allocated"):
        if cp64.get(key) is not False:
            raise ValueError("CP64 nonreceipt boundary differs: " + key)

    return {
        "B08_closed": False,
        "available_bytes": arithmetic["available_bytes"],
        "combined_required_bytes": arithmetic["combined_reservation_bytes"],
        "record_sha256": validated["record_sha256"],
        "residual_field_ids": [
            row["field_id"] for row in validated["supported_projection"]["residual_gaps"]
        ],
        "shortfall_bytes": arithmetic["shortfall_bytes"],
        "state": validated["state"],
    }


def main() -> int:
    summary = validate()
    print("PASS_B08_WAVE2_LOCAL_CAPACITY_TERMINAL_NO_GO")
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
