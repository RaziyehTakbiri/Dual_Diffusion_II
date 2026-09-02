#!/usr/bin/env python3
"""Read-only validator for the F105 manuscript/production integration."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Dict, Mapping, Tuple


SCHEMA = "heterodiff-f105-manuscript-production-integration-v1"
STATE = "F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME"
PREDICATE = "F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME"
EXPECTED_RECORD_SHA256 = (
    "6c5480374ed3d1993e28711ef8640d8f12c0cadf40a51e0ce7d8991f5233f5ae"
)
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_f105_manuscript_production_integration_v1.json"
)
ROOT = Path(__file__).resolve().parents[2]
MAX_FILE_BYTES = 1_000_000

EXPECTED_FROZEN = {
    "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py":
        "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881",
    "research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json":
        "560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9",
    "manuscript_v3/manuscript_v3_locked_route_successor_v1.md":
        "e06cb6780974dea98b85df03c04104b034bfcf4bdd7b3825d9b375d6983849db",
}


class ValidationError(RuntimeError):
    """Raised when a package byte or semantic invariant fails."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_parts(relative: str) -> Tuple[str, ...]:
    if type(relative) is not str:
        raise ValidationError("path must be a built-in string")
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts:
        raise ValidationError("path must be nonempty and relative")
    if any(part in ("", ".", "..") for part in path.parts) or str(path) != relative:
        raise ValidationError("path must be canonical POSIX relative form")
    return path.parts


def _fingerprint(value: os.stat_result) -> Tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _canonical_root(root: Path) -> Path:
    supplied = Path(root)
    if not supplied.is_absolute():
        raise ValidationError("root must be an absolute path")
    try:
        lexical = supplied.absolute()
        resolved = supplied.resolve(strict=True)
        metadata = os.lstat(supplied)
    except OSError as exc:
        raise ValidationError("cannot resolve package root") from exc
    if lexical != resolved or stat.S_ISLNK(metadata.st_mode):
        raise ValidationError("root must be canonical and non-symlinked")
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValidationError("root must be a directory")
    return supplied


def _read_regular(
    root: Path,
    relative: str,
    *,
    expected_bytes: int | None = None,
    expected_sha256: str | None = None,
) -> bytes:
    root = _canonical_root(root)
    parts = _relative_parts(relative)
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    descriptors = []
    custody = []
    try:
        directory_descriptor = os.open(root, directory_flags)
        descriptors.append(directory_descriptor)
        custody.append((root, os.lstat(root), os.fstat(directory_descriptor)))
    except OSError as exc:
        raise ValidationError("cannot open package root") from exc
    try:
        for index, component in enumerate(parts[:-1], start=1):
            try:
                next_descriptor = os.open(
                    component, directory_flags, dir_fd=directory_descriptor
                )
            except OSError as exc:
                raise ValidationError(
                    f"cannot component-wise no-follow open {relative}"
                ) from exc
            directory_descriptor = next_descriptor
            descriptors.append(directory_descriptor)
            component_path = root.joinpath(*parts[:index])
            custody.append(
                (
                    component_path,
                    os.lstat(component_path),
                    os.fstat(directory_descriptor),
                )
            )
        file_flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            file_flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(
                parts[-1], file_flags, dir_fd=directory_descriptor
            )
            descriptors.append(descriptor)
        except OSError as exc:
            raise ValidationError(f"cannot no-follow open {relative}") from exc
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError(f"{relative} is not regular")
        if before.st_nlink != 1:
            raise ValidationError(f"{relative} is not single-link custody")
        if stat.S_IMODE(before.st_mode) != 0o644:
            raise ValidationError(f"{relative} mode is not 0644")
        if before.st_size > MAX_FILE_BYTES:
            raise ValidationError(f"{relative} exceeds its byte ceiling")
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                raise ValidationError(f"short read for {relative}")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise ValidationError(f"growth during read for {relative}")
        after = os.fstat(descriptor)
        leaf_path = root / relative
        if _fingerprint(after) != _fingerprint(os.lstat(leaf_path)):
            raise ValidationError(f"leaf path identity changed for {relative}")
        for index, (path, path_before, fd_before) in enumerate(custody):
            fd_after = os.fstat(descriptors[index])
            path_after = os.lstat(path)
            if not (
                _fingerprint(path_before)
                == _fingerprint(fd_before)
                == _fingerprint(fd_after)
                == _fingerprint(path_after)
            ):
                raise ValidationError(f"ancestor identity changed for {relative}")
    finally:
        for open_descriptor in reversed(descriptors):
            try:
                os.close(open_descriptor)
            except OSError:
                pass
    stable_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    stable_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if stable_before != stable_after:
        raise ValidationError(f"unstable read for {relative}")
    data = b"".join(chunks)
    if expected_bytes is not None and len(data) != expected_bytes:
        raise ValidationError(f"byte count mismatch for {relative}")
    digest = _sha256(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValidationError(f"raw hash mismatch for {relative}")
    if not data.endswith(b"\n"):
        raise ValidationError(f"{relative} lacks terminal LF")
    return data


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(data: bytes) -> Dict[str, Any]:
    try:
        record = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValidationError(f"forbidden JSON constant {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("machine record is not strict UTF-8 JSON") from exc
    if type(record) is not dict:
        raise ValidationError("machine record must be an object")
    return record


def _semantic_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("machine record must be a built-in object")
    projection = dict(record)
    projection["record_sha256"] = None
    try:
        canonical = json.dumps(
            projection,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValidationError("machine record is not canonicalizable") from exc
    return _sha256((SCHEMA + "\0").encode("ascii") + canonical)


def _require_exact_keys(record: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "state",
        "target_predicate",
        "primary_metric_id",
        "production_integration_id",
        "package_bindings",
        "frozen_inputs",
        "metric_semantics",
        "production_contract",
        "closure_effect",
        "validator_and_tests_outside_semantic_self_binding",
        "record_sha256",
    }
    if set(record) != expected:
        raise ValidationError("machine top-level keys differ")


def _require_text_tokens(text: str, tokens: Tuple[str, ...], label: str) -> None:
    for token in tokens:
        if token not in text:
            raise ValidationError(f"{label} lacks required token {token!r}")


def validate_package(root: Path = ROOT) -> Dict[str, Any]:
    machine_bytes = _read_regular(root, MACHINE_PATH)
    record = _load_json(machine_bytes)
    _require_exact_keys(record)
    if record["schema_version"] != SCHEMA or record["state"] != STATE:
        raise ValidationError("machine schema/state differs")
    if record["record_sha256"] != EXPECTED_RECORD_SHA256:
        raise ValidationError("record_sha256 differs from the frozen validator")
    if _semantic_sha256(record) != EXPECTED_RECORD_SHA256:
        raise ValidationError("machine semantic digest mismatch")
    predicate = record["target_predicate"]
    if type(predicate) is not dict or predicate != {
        "predicate_id": PREDICATE,
        "value": True,
        "basis": "EXACT_DISPLAY_AND_CODE_MATCHED_PRODUCTION_PROJECTION_QUALIFIED",
    }:
        raise ValidationError("target predicate differs")
    if record["primary_metric_id"] != "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1":
        raise ValidationError("primary metric differs")
    if record["production_integration_id"] != "F105_CKS_BINARY64_PROJECTION_V1":
        raise ValidationError("production integration ID differs")

    bindings = record["package_bindings"]
    if type(bindings) is not list or len(bindings) != 6:
        raise ValidationError("package binding roster differs")
    seen = set()
    bound_data: Dict[str, bytes] = {}
    for binding in bindings:
        if type(binding) is not dict or set(binding) != {
            "path", "role", "bytes", "raw_sha256"
        }:
            raise ValidationError("package binding shape differs")
        path = binding["path"]
        if path in seen:
            raise ValidationError("duplicate package binding path")
        seen.add(path)
        bound_data[path] = _read_regular(
            root,
            path,
            expected_bytes=binding["bytes"],
            expected_sha256=binding["raw_sha256"],
        )

    frozen_inputs = record["frozen_inputs"]
    if type(frozen_inputs) is not list or len(frozen_inputs) != 3:
        raise ValidationError("frozen input roster differs")
    for item in frozen_inputs:
        if type(item) is not dict or "path" not in item or "raw_sha256" not in item:
            raise ValidationError("frozen input shape differs")
        path = item["path"]
        if EXPECTED_FROZEN.get(path) != item["raw_sha256"]:
            raise ValidationError("frozen input digest differs from validator")
        data = _read_regular(root, path, expected_sha256=item["raw_sha256"])
        if "semantic_sha256" in item:
            predecessor = _load_json(data)
            projection = {
                key: value
                for key, value in predecessor.items()
                if key != "record_sha256"
            }
            canonical = json.dumps(
                projection,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
            predecessor_schema = predecessor.get("schema_version")
            if type(predecessor_schema) is not str:
                raise ValidationError("F105 predecessor schema is missing")
            digest = _sha256(
                b"heterodiff:f105-two-domain-cks-instance:v1\0" + canonical
            )
            if digest != item["semantic_sha256"]:
                raise ValidationError("F105 predecessor semantic digest differs")

    semantics = record["metric_semantics"]
    if type(semantics) is not dict:
        raise ValidationError("metric_semantics must be an object")
    if semantics["domains"]["R3-PHYS"]["dimension"] != 112:
        raise ValidationError("PhysioNet dimension differs")
    if semantics["domains"]["R4-RETAIL"]["dimension"] != 10:
        raise ValidationError("Retail dimension differs")
    for key in (
        "event_tau_squared",
        "count_scale_squared",
        "event_scale_squared",
        "outer_sigma_squared",
    ):
        if semantics[key] != "1":
            raise ValidationError("kernel squared parameter differs")
    if semantics["draw_count_formal_domain"] != {"minimum": 2, "maximum": 128}:
        raise ValidationError("formal draw-count domain differs")
    if semantics["score_direction"] != "LOWER_IS_BETTER":
        raise ValidationError("score direction differs")
    if (
        semantics["comparison_direction"]
        != "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE"
    ):
        raise ValidationError("comparison direction differs")
    if semantics["cross_domain_evaluation"] != "FORBIDDEN":
        raise ValidationError("cross-domain rule differs")

    production = record["production_contract"]
    expected_production = {
        "builds_formal_score_from_frozen_configuration_kernel": True,
        "redefines_event_map_or_kernel": False,
        "binary64_projection_only_after_exact_symbol_construction": True,
        "formal_score_sha256_recorded": True,
        "binary64_hex_recorded": True,
        "default_symbolic_event_pair_work_limit": 10000000,
        "maximum_symbolic_event_pair_work_limit": 1000000000,
        "material_negative_squared_distance_refuses": True,
        "nonfinite_output_refuses": True,
        "cross_domain_input_refuses": True,
        "unmatched_direct_guide_draw_count_refuses": True,
        "comparison_work_ceiling_is_combined": True,
        "records_factory_only_and_revalidated": True,
        "factory_issued_field_integrity_digest_revalidated": True,
        "performs_io_or_randomness_or_fitting_or_threshold_decision": False,
    }
    if production != expected_production:
        raise ValidationError("production contract differs")

    closure = record["closure_effect"]
    if closure != {
        "timetable_task_closed": PREDICATE,
        "field_count_delta": 0,
        "blocker_count_delta": 0,
        "formal_test_count_delta": 0,
        "result_count_delta": 0,
        "f109_f112_closed": False,
        "b04_closed": False,
        "all_b01_b12_open": True,
        "data_or_domain_admission": False,
        "runtime_or_scientific_execution": False,
        "claim_promotion": False,
    }:
        raise ValidationError("closure boundary differs")

    source_path = (
        "src/heterodiff/evaluation/"
        "two_domain_count_normalized_event_cks_production.py"
    )
    markdown_path = (
        "manuscript_v3/"
        "manuscript_v3_f105_metric_integration_successor_v2.md"
    )
    tex_path = (
        "manuscript_v3/"
        "manuscript_v3_f105_metric_integration_successor_v2.tex"
    )
    claim_path = "manuscript_v3/claim_ledger_f105_metric_integration_successor_v2.md"
    source = bound_data[source_path].decode("utf-8")
    markdown = bound_data[markdown_path].decode("utf-8")
    tex = bound_data[tex_path].decode("utf-8")
    claim = bound_data[claim_path].decode("utf-8")
    _require_text_tokens(
        source,
        (
            "PRODUCTION_INTEGRATION_ID = \"F105_CKS_BINARY64_PROJECTION_V1\"",
            "SCORE_DIRECTION = \"LOWER_IS_BETTER\"",
            "COMPARISON_DIRECTION = \"POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE\"",
            "DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT = 10_000_000",
            "@dataclass(frozen=True, init=False)",
            "score fields differ from the factory-issued record",
            "combined direct-and-guide symbolic work exceeds the frozen ceiling",
            "configuration_kernel(",
            "FormalCKSScore(",
            "math.exp(-outer_exponent)",
            "formal_score_sha256",
            "draws and target must belong to one domain",
        ),
        "production source",
    )
    _require_text_tokens(
        markdown,
        (
            "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
            "F105_CKS_BINARY64_PROJECTION_V1",
            "D_{\\mathrm{PHYS}}=112",
            "D_{\\mathrm{RETAIL}}=10",
            "a_d^2=b_d^2=\\tau_d^2=\\sigma_d^2=1",
            "\\widehat{\\operatorname{CKS}}_d",
            "positive \\(\\Delta_d\\) favors the guide",
            "F109",
            "F112",
            "does not by itself close B04",
        ),
        "Markdown display",
    )
    _require_text_tokens(
        tex,
        (
            "TWO\\_DOMAIN\\_COUNT\\_NORMALIZED\\_EVENT\\_CKS\\_V1",
            "F105\\_CKS\\_BINARY64\\_PROJECTION\\_V1",
            "D_{\\mathrm{PHYS}}=112",
            "D_{\\mathrm{RETAIL}}=10",
            "a_d^2=b_d^2=\\tau_d^2=\\sigma_d^2=1",
            "\\widehat{\\operatorname{CKS}}_d",
            "F109--F112 and B04 remain open",
        ),
        "TeX display",
    )
    _require_text_tokens(
        claim,
        (
            "Manuscript display | Synchronized",
            "Production evaluator | Implemented",
            "F109--F112 | Open",
            "B04 is not closed",
            "No efficacy",
        ),
        "claim ledger",
    )

    return {
        "state": STATE,
        "record_sha256": EXPECTED_RECORD_SHA256,
        "package_binding_count": len(bindings),
        "field_count_delta": 0,
        "blocker_count_delta": 0,
        "target_predicate": True,
    }


def main() -> int:
    try:
        result = validate_package()
    except Exception as exc:
        print(json.dumps({"state": "HOLD", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
