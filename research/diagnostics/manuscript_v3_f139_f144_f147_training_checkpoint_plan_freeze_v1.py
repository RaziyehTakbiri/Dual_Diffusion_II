#!/usr/bin/env python3
"""Read-only hash-first validator for the exact seven-field training freeze.

The validator reads fixed bytes through no-follow descriptors, validates every
accepted predecessor before compiling the captured B06 registry and candidate
source, reconstructs the exact 22-row configuration roster, and refuses any
field, count, runtime, capacity, science, or B12-roster overclaim.

It has no writer, network, connector, subprocess, entropy, data, optimizer,
training, checkpoint, runtime, or project-control route.
"""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-f139-f144-f147-"
    "training-checkpoint-plan-freeze-v1"
)
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = (
    "F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FROZEN_"
    "PREOUTCOME_PENDING_INDEPENDENT_REVIEW"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-09-01"
PACKAGE_KIND = "ALL_OR_NOTHING_SEVEN_PREEXECUTION_FIELD_CLOSURE"
CONTROL_PREDICATE = (
    "F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FROZEN_PREOUTCOME_V1"
)
PASS_TOKEN = "PASS_F139_F144_F147_SEVEN_FIELDS_ONLY"

HUMAN_PATH = "PROJECT_F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FREEZE.md"
SOURCE_PATH = (
    "src/heterodiff/experiments/two_domain_training_checkpoint_plan.py"
)
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.py"
)
PACKAGE_ROSTER = (
    HUMAN_PATH,
    SOURCE_PATH,
    MACHINE_PATH,
    VALIDATOR_PATH,
    TEST_PATH,
)

EXPECTED_HUMAN_BYTES = 19707
EXPECTED_HUMAN_SHA256 = (
    "ac318d432b0634b96547ffd0773f93c3ad0f4978dc9db287b6b7f13e1cfdf442"
)
EXPECTED_SOURCE_BYTES = 33918
EXPECTED_SOURCE_SHA256 = (
    "9ac7d6e6d93bb0691fde67070dc97b566e716797dd05f82ed053c8dc77e2fbcf"
)
EXPECTED_TEST_BYTES = 19373
EXPECTED_TEST_SHA256 = (
    "433a2b8e746445371fc8bb50398c99040d0866d6f67b181e0ef4d749cb8b9449"
)
EXPECTED_PLAN_SEMANTICS_SHA256 = (
    "dd1c74d655f4cfeb4a895c11eb09a9e3ef41c328ce432ad782bce204e59585db"
)
EXPECTED_F144_SEMANTICS_SHA256 = (
    "040db767c5bae9879ca5f006095dace2c43d4a2640af19839994465cff2011d2"
)

FIELD_IDS = ("F139", "F140", "F141", "F142", "F143", "F144", "F147")
FIELD_POINTERS = {
    "F139": "/training_and_checkpoint_plan/optimizer",
    "F140": "/training_and_checkpoint_plan/learning_rate_schedule",
    "F141": "/training_and_checkpoint_plan/precision",
    "F142": "/training_and_checkpoint_plan/batch_construction",
    "F143": "/training_and_checkpoint_plan/maximum_epochs_or_steps",
    "F144": "/training_and_checkpoint_plan/validation_metric",
    "F147": "/training_and_checkpoint_plan/maximum_tuning_trials_per_method",
}

# group, role, path, bytes, raw SHA-256, terminal LF, semantic SHA-256, mode
BindingSpec = Tuple[str, str, str, int, str, bool, Optional[str], Optional[str]]
PREDECESSOR_SPECS: Tuple[BindingSpec, ...] = (
    (
        "ACCEPTED_B06",
        "human",
        "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md",
        41198,
        "6a10a546a70d43aa71cb878e72ba09c24be949cd932e1cdf5becdeb732fa816a",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_B06",
        "machine",
        "research/fixtures/"
        "manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json",
        186707,
        "b789b4b39aef1cef3134dddee506409f311b79cc70b1d121daa0a2ff22267f21",
        True,
        "aa3ab6c8cb05287304da321f2d5b4892b94d4483860d830a3e724c339b2809bd",
        "REMOVE",
    ),
    (
        "ACCEPTED_B06",
        "matched_compute_source",
        "src/heterodiff/experiments/matched_total_compute.py",
        15028,
        "be31b346c67b7d0ce0b82a3ff784739bf3d825fd9b94108dc1f8ae808586f8a0",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_B06",
        "registry_source",
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
        47098,
        "d8938ac2111000275a02ad9605602ecf11f2ef9c38903d5431d6c3604c1645f1",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_B06",
        "independent_review",
        "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE_INDEPENDENT_REVIEW.md",
        13421,
        "a0aa207a0a68545d0af7ba5e252d7c30f1349d799e0e61ebf807c2426ee22209",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F105_PRODUCTION",
        "human",
        "PROJECT_F105_MANUSCRIPT_PRODUCTION_INTEGRATION.md",
        7358,
        "954d914459362d6690028b93c3fa2c84fc37aeb2954e073a6c578bc3b812220a",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F105_PRODUCTION",
        "machine",
        "research/fixtures/manuscript_v3_f105_manuscript_production_integration_v1.json",
        5495,
        "251edc5792dd5545c40eb45ec528f98b133a0b154f5d0f5ef3bb3db4df325126",
        True,
        "6c5480374ed3d1993e28711ef8640d8f12c0cadf40a51e0ce7d8991f5233f5ae",
        "NULL",
    ),
    (
        "ACCEPTED_F105_PRODUCTION",
        "formal_metric_source",
        "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
        25342,
        "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F105_PRODUCTION",
        "production_source",
        "src/heterodiff/evaluation/two_domain_count_normalized_event_cks_production.py",
        21619,
        "42a023483816c391c1ba0e9d8bfb23c36d10d74d0ed55901727cda790c2f15ad",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F105_PRODUCTION",
        "independent_review",
        "PROJECT_F105_MANUSCRIPT_PRODUCTION_INTEGRATION_INDEPENDENT_REVIEW.md",
        9128,
        "a8e6c5d42847b8dcf28e238bddd5d006852bbff85eb161967ca1ff398c204d82",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F134_R64",
        "human",
        "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md",
        17299,
        "bb4438887f54710b0445e0b713ee086abc2523b2bf34b4a08d42ee586515d721",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F134_R64",
        "machine",
        "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json",
        20936,
        "2ff92ac1b4b6df75931791cd16ce7ade461c70b29042a17486bc2804f35295f1",
        True,
        "335879da927b14de0f2ab0cb69b531ea51f24d9734777cb33cdf1e90fb81a491",
        "REMOVE",
    ),
    (
        "ACCEPTED_F134_R64",
        "r64_adapter_source",
        "src/heterodiff/evaluation/fixed_r64_cks_statistical_adapter.py",
        7013,
        "63dbc81b804ed643406d401559b38305654ef43d0b9a4ade17feb9e2152eb278",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F134_R64",
        "independent_review",
        "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE_INDEPENDENT_REVIEW.md",
        3270,
        "ede11cff876c96cafe5734cee59ffae347b001dc8e16c3b3b71437d6cb4a0b64",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F145",
        "human",
        "PROJECT_F145_VALIDATION_EARLY_STOPPING_FREEZE.md",
        14003,
        "ef31cab9d4d8a245d8e88b47590d90a335b31f230a499893629d3a46e9a8eee4",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F145",
        "machine",
        "research/fixtures/manuscript_v3_f145_validation_early_stopping_freeze_v1.json",
        20891,
        "d2149abb5bab067cd7465f17e1bb8d1515a076834071536e355e15f9bae23a81",
        True,
        "a88a2d656d1d6f1af673609ab1127017e44f809d93ecb880bdd4c3f4d4c2f3e7",
        "REMOVE",
    ),
    (
        "ACCEPTED_F145",
        "independent_review",
        "PROJECT_F145_VALIDATION_EARLY_STOPPING_FREEZE_INDEPENDENT_REVIEW.md",
        14464,
        "844d334ffe59cfade890215e2e45f3488f2a0ff24cc28eea5f77a1f1e504be37",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F146",
        "human",
        "PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE.md",
        18409,
        "403858d0a1afe5c4498973b568ca2e528cb0cde54a02dde52f74123eb0b4c249",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F146",
        "machine",
        "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json",
        20813,
        "21dcfd76f4701f3be033f6ab70a7c93fd9b9b3475ab773d8709d5d027dcbf447",
        True,
        "33ae0137e1c41da0553b78d7790f4556ddf7d993bbf635fe9dd6abd46ec9c131",
        "REMOVE",
    ),
    (
        "ACCEPTED_F146",
        "independent_review",
        "PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE_INDEPENDENT_REVIEW.md",
        14443,
        "9c2858279242dc1005e792ce827e9d95a27b70a62baf6b605e2c21f25724b089",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F148",
        "human",
        "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md",
        8073,
        "ca9a593c54a9d3587f58a3d414defd5cf81a3765395d5ebb8494e6effa6dd44d",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_F148",
        "machine",
        "research/fixtures/"
        "manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
        8455,
        "b8a74f1131f85aa1b7497f2f43bd34a0e30bc471953c935d4362a5a8dea1446a",
        True,
        "aa3fe845190d6c74472706749598ba245de1925ce03a5702d1d2eed81a88bffa",
        "REMOVE",
    ),
    (
        "ACCEPTED_B12_SEMANTICS_ONLY",
        "human",
        "PROJECT_B12_INTEGRATED_OFFLINE_IMPLEMENTATION_GAP_PACKAGE.md",
        2414,
        "421ee28c8e4cf6e886e22759518fb8bfd125bf46891a42fbdecd8d7f589a9b95",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_B12_SEMANTICS_ONLY",
        "machine",
        "research/fixtures/manuscript_v3_b12_integrated_offline_gap_package_v1.json",
        8755,
        "825cfde8412474eba97dea4a4d2fb92fa8af99568ebeada05f6b33b71fcc680c",
        True,
        "5a37e70e4257e232205d7c6a4e30f342d45c4457596bdff5e59b5e7017c9b834",
        "B12",
    ),
    (
        "ACCEPTED_B12_SEMANTICS_ONLY",
        "contract_source",
        "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
        14944,
        "b77c6eea6859fa9d6181a94a27112d97555e5a4d60ab1df1ee03a30c7808defd",
        True,
        None,
        None,
    ),
    (
        "ACCEPTED_B12_SEMANTICS_ONLY",
        "independent_review",
        "PROJECT_B12_INTEGRATED_OFFLINE_IMPLEMENTATION_GAP_PACKAGE_INDEPENDENT_REVIEW.md",
        4988,
        "90e7d4f9f4f70bcd4a6da599c532a944629101d3d5b245f7b05ece01cb463a46",
        True,
        None,
        None,
    ),
)

PREDECESSOR_GROUP_COUNTS = {
    "ACCEPTED_B06": 5,
    "ACCEPTED_F105_PRODUCTION": 5,
    "ACCEPTED_F134_R64": 4,
    "ACCEPTED_F145": 3,
    "ACCEPTED_F146": 3,
    "ACCEPTED_F148": 2,
    "ACCEPTED_B12_SEMANTICS_ONLY": 4,
}

REGISTRATION_TEXT = (
    "Close all-or-nothing exactly F139--F144 and F147 through "
    "'F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FROZEN_PREOUTCOME_V1'. "
    "The accepted values are the exact AdamW optimizer, constant "
    "predeclared-candidate learning-rate schedule, binary32-training/"
    "binary64-F105-validation precision contract, 22-row B06-derived exact-16 "
    "domain-local no-shuffle batch construction, exact F143 integer bound 4096 "
    "in completed optimizer updates, exact complete-F134-roster F105 "
    "validation/certificate semantics at every 256 updates plus the terminal "
    "bound, and exact B06-grid-or-singleton per-method/domain tuning caps. PRE "
    "moves from 30 open / 136 closed to 23 open / 143 closed; POST remains 1 "
    "open / 5 closed; total fields move from 31 open / 141 closed to 24 open / "
    "148 closed; method/runtime/compute moves from 17/48 to 10/55. Mark the "
    "existing 'Freeze checkpoint-selection and training rules using training/"
    "validation data only' item complete, moving the marked-task view from "
    "58/105/163 to 59/104/163. Blockers remain 7/5, Gate A remains 5/8, and "
    "B08/B12 and Formal Tests 28--30 remain open or pending. No adapter/runtime/"
    "checkpoint/capacity, data access, entropy, training, result, science, "
    "claim, release, or submission is created."
)

_HEX = frozenset("0123456789abcdef")
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    (
        "asyncio",
        "http",
        "multiprocessing",
        "numpy",
        "os",
        "pathlib",
        "random",
        "requests",
        "secrets",
        "shutil",
        "socket",
        "subprocess",
        "tempfile",
        "time",
        "torch",
        "urllib",
    )
)
_FORBIDDEN_CALLS = frozenset(
    (
        "compile",
        "eval",
        "exec",
        "input",
        "open",
        "system",
        "popen",
        "remove",
        "rename",
        "replace",
        "unlink",
        "write",
        "write_bytes",
        "write_text",
    )
)


class ValidationError(ValueError):
    """The package, custody, or semantic projection differs."""


def _exact_json_tree(value: object, path: str = "$") -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for ordinal, member in enumerate(value):
            _exact_json_tree(member, "{}[{}]".format(path, ordinal))
        return
    if type(value) is dict:
        for key, member in value.items():
            if type(key) is not str:
                raise ValidationError(path + " contains a non-string key")
            _exact_json_tree(member, path + "." + key)
        return
    raise ValidationError(path + " is outside the exact JSON tree")


def canonical_json_bytes(value: object) -> bytes:
    _exact_json_tree(value)
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _domain_sha256(domain: str, value: object) -> str:
    return _sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(value))


def _require_sha256(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValidationError(label + " is not lowercase SHA-256")
    return value


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("record must be an exact object")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + canonical_json_bytes(payload))


def _pairs(items: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str, exact_tree: bool = False) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValidationError("forbidden JSON constant: " + token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(label + " is not strict ASCII JSON") from error
    if type(value) is not dict:
        raise ValidationError(label + " must be an exact JSON object")
    if exact_tree:
        _exact_json_tree(value)
    return value


def _canonical_parts(relative: str) -> Tuple[str, ...]:
    if type(relative) is not str or not relative or "\\" in relative:
        raise ValidationError("binding path must be nonempty canonical POSIX")
    path = Path(relative)
    if path.is_absolute() or "/".join(path.parts) != relative:
        raise ValidationError("binding path must be canonical and relative")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValidationError("binding path traversal is forbidden")
    return tuple(path.parts)


def _fingerprint(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _validate_root(root: Path) -> Path:
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("workspace root must be an absolute Path")
    if Path(os.path.abspath(str(root))) != root:
        raise ValidationError("workspace root must be lexically canonical")
    cursor = Path(root.anchor)
    for component in root.parts[1:]:
        cursor = cursor / component
        status = cursor.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise ValidationError("workspace root ancestry contains a symlink")
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValidationError("workspace root must be a directory")
    return root


def _validate_leaf(value: os.stat_result, label: str) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise ValidationError(label + " must be a regular file")
    if stat.S_IMODE(value.st_mode) != 0o644:
        raise ValidationError(label + " mode must be exactly 0644")
    if value.st_nlink != 1:
        raise ValidationError(label + " must have exactly one hard link")


def _stable_read(
    root: Path,
    relative: str,
    *,
    expected_bytes: Optional[int] = None,
    maximum_bytes: int = 8 * 1024 * 1024,
) -> bytes:
    root = _validate_root(root)
    parts = _canonical_parts(relative)
    descriptors: List[int] = []
    namespace: List[Tuple[int, str, Tuple[int, ...], bool]] = []
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    if nofollow is None or directory is None:
        raise ValidationError("platform lacks required no-follow descriptors")
    root_before = root.lstat()
    try:
        root_fd = os.open(
            str(root), os.O_RDONLY | directory | nofollow | cloexec
        )
        descriptors.append(root_fd)
        root_open = os.fstat(root_fd)
        if (
            stat.S_ISLNK(root_before.st_mode)
            or not stat.S_ISDIR(root_before.st_mode)
            or _fingerprint(root_before) != _fingerprint(root_open)
        ):
            raise ValidationError("workspace root identity changed")
        parent_fd = root_fd
        for component in parts[:-1]:
            before = os.stat(
                component, dir_fd=parent_fd, follow_symlinks=False
            )
            child_fd = os.open(
                component,
                os.O_RDONLY | directory | nofollow | cloexec,
                dir_fd=parent_fd,
            )
            descriptors.append(child_fd)
            opened = os.fstat(child_fd)
            if (
                stat.S_ISLNK(before.st_mode)
                or not stat.S_ISDIR(before.st_mode)
                or _fingerprint(before) != _fingerprint(opened)
            ):
                raise ValidationError("unsafe or changed path component")
            namespace.append(
                (parent_fd, component, _fingerprint(before), False)
            )
            parent_fd = child_fd

        leaf = parts[-1]
        before_path = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        _validate_leaf(before_path, "before-path binding")
        leaf_fd = os.open(
            leaf, os.O_RDONLY | nofollow | cloexec, dir_fd=parent_fd
        )
        descriptors.append(leaf_fd)
        before_fd = os.fstat(leaf_fd)
        _validate_leaf(before_fd, "before-descriptor binding")
        if (
            stat.S_ISLNK(before_path.st_mode)
            or _fingerprint(before_path) != _fingerprint(before_fd)
        ):
            raise ValidationError("binding identity changed before read")
        if expected_bytes is not None and before_fd.st_size != expected_bytes:
            raise ValidationError("binding byte count differs: " + relative)
        if before_fd.st_size > maximum_bytes:
            raise ValidationError("binding exceeds read ceiling: " + relative)
        namespace.append(
            (parent_fd, leaf, _fingerprint(before_path), True)
        )

        chunks: List[bytes] = []
        total = 0
        while True:
            chunk = os.read(leaf_fd, min(131072, maximum_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum_bytes:
                raise ValidationError("binding exceeds read ceiling: " + relative)
        after_fd = os.fstat(leaf_fd)
        _validate_leaf(after_fd, "after-descriptor binding")
        if _fingerprint(before_fd) != _fingerprint(after_fd):
            raise ValidationError("binding changed during descriptor read")
        for parent, component, expected, is_leaf in namespace:
            current = os.stat(
                component, dir_fd=parent, follow_symlinks=False
            )
            if is_leaf:
                _validate_leaf(current, "after-path binding")
            elif not stat.S_ISDIR(current.st_mode):
                raise ValidationError("path component stopped being a directory")
            if _fingerprint(current) != expected:
                raise ValidationError("binding namespace changed during read")
        if _fingerprint(root_before) != _fingerprint(root.lstat()):
            raise ValidationError("workspace root changed during read")
        raw = b"".join(chunks)
        if len(raw) != before_fd.st_size:
            raise ValidationError("binding read was short")
        return raw
    except OSError as error:
        raise ValidationError("stable no-follow read failed: " + relative) from error
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _binding(
    ordinal: int,
    group: str,
    role: str,
    path: str,
    raw: bytes,
    semantic_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "bytes": len(raw),
        "group": group,
        "mode_octal": "0644",
        "nlink": 1,
        "ordinal": ordinal,
        "path": path,
        "raw_sha256": _sha256(raw),
        "role": role,
        "terminal_lf": raw.endswith(b"\n"),
    }
    if semantic_sha256 is not None:
        row["record_sha256"] = semantic_sha256
    return row


def _semantic_self_digest(record: Mapping[str, Any], mode: str) -> str:
    if type(record) is not dict:
        raise ValidationError("predecessor machine must be exact object")
    schema = record.get("schema_version")
    if type(schema) is not str or not schema:
        raise ValidationError("predecessor schema is not exact")
    projection = dict(record)
    if mode == "REMOVE":
        projection.pop("record_sha256", None)
        domain = (schema + "\0").encode("ascii")
    elif mode == "NULL":
        projection["record_sha256"] = None
        domain = (schema + "\0").encode("ascii")
    elif mode == "B12":
        projection.pop("record_sha256", None)
        domain = b"heterodiff-b12-machine-v2\0"
    else:
        raise ValidationError("unknown predecessor semantic digest mode")
    return _sha256(
        domain
        + json.dumps(
            projection,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    )


def _fixed_predecessors(
    root: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, bytes]]:
    rows = []
    captured: Dict[str, bytes] = {}
    observed_counts: Dict[str, int] = {}
    for ordinal, spec in enumerate(PREDECESSOR_SPECS):
        group, role, path, size, digest, terminal_lf, semantic, mode = spec
        raw = _stable_read(root, path, expected_bytes=size)
        if _sha256(raw) != digest or raw.endswith(b"\n") is not terminal_lf:
            raise ValidationError("fixed predecessor drift: " + path)
        if semantic is not None:
            machine = _parse_json(raw, path)
            if machine.get("record_sha256") != semantic:
                raise ValidationError("predecessor semantic claim differs: " + path)
            if _semantic_self_digest(machine, str(mode)) != semantic:
                raise ValidationError("predecessor semantic digest differs: " + path)
        rows.append(_binding(ordinal, group, role, path, raw, semantic))
        captured[path] = raw
        observed_counts[group] = observed_counts.get(group, 0) + 1
    if observed_counts != PREDECESSOR_GROUP_COUNTS:
        raise ValidationError("predecessor group counts differ")
    return rows, captured


def _current_package_bindings(
    root: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, bytes]]:
    fixed = (
        ("human", HUMAN_PATH, EXPECTED_HUMAN_BYTES, EXPECTED_HUMAN_SHA256),
        ("source", SOURCE_PATH, EXPECTED_SOURCE_BYTES, EXPECTED_SOURCE_SHA256),
        ("test", TEST_PATH, EXPECTED_TEST_BYTES, EXPECTED_TEST_SHA256),
    )
    captured: Dict[str, bytes] = {}
    rows = []
    for role, path, size, digest in fixed:
        raw = _stable_read(root, path, expected_bytes=size)
        if _sha256(raw) != digest or not raw.endswith(b"\n"):
            raise ValidationError("fixed candidate binding drift: " + path)
        captured[path] = raw
    validator_raw = _stable_read(root, VALIDATOR_PATH)
    if not validator_raw.endswith(b"\n"):
        raise ValidationError("validator must end in LF")
    captured[VALIDATOR_PATH] = validator_raw
    ordered = (
        ("human", HUMAN_PATH),
        ("source", SOURCE_PATH),
        ("validator", VALIDATOR_PATH),
        ("test", TEST_PATH),
    )
    for ordinal, (role, path) in enumerate(ordered):
        rows.append(
            _binding(
                ordinal,
                "CURRENT_PACKAGE",
                role,
                path,
                captured[path],
            )
        )
    return rows, captured


def _source_effect_surface(raw: bytes) -> Dict[str, Any]:
    try:
        tree = ast.parse(raw.decode("ascii"), filename="<verified-candidate>")
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("candidate source does not parse") from error
    imports = []
    forbidden_imports = []
    forbidden_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                if alias.name.split(".")[0] in _FORBIDDEN_IMPORT_ROOTS:
                    forbidden_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
            if module.split(".")[0] in _FORBIDDEN_IMPORT_ROOTS:
                forbidden_imports.append(module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                name = ""
            if name in _FORBIDDEN_CALLS:
                forbidden_calls.append(name)
    result = {
        "ast_node_count": sum(1 for _ in ast.walk(tree)),
        "forbidden_call_hits": sorted(forbidden_calls),
        "forbidden_import_hits": sorted(forbidden_imports),
        "import_roster": sorted(imports),
    }
    if result["forbidden_call_hits"] or result["forbidden_import_hits"]:
        raise ValidationError("candidate source exposes a forbidden effect")
    if result["import_roster"] != [
        "__future__",
        "copy",
        "fractions",
        "functools",
        "hashlib",
        "heterodiff.experiments",
        "json",
        "math",
        "typing",
    ]:
        raise ValidationError("candidate import roster differs")
    return result


def _compile_verified_modules(
    captured: Mapping[str, bytes],
) -> Tuple[types.ModuleType, types.ModuleType]:
    names = (
        "heterodiff",
        "heterodiff.experiments",
        "heterodiff.experiments.matched_total_compute",
        "heterodiff.experiments.two_domain_baseline_registry",
        "heterodiff.experiments.two_domain_training_checkpoint_plan",
    )
    saved = {name: sys.modules.get(name) for name in names}
    try:
        package = types.ModuleType("heterodiff")
        package.__path__ = []  # type: ignore[attr-defined]
        experiments = types.ModuleType("heterodiff.experiments")
        experiments.__path__ = []  # type: ignore[attr-defined]
        setattr(package, "experiments", experiments)
        sys.modules["heterodiff"] = package
        sys.modules["heterodiff.experiments"] = experiments

        matched_name = "heterodiff.experiments.matched_total_compute"
        matched = types.ModuleType(matched_name)
        matched.__file__ = "<verified-matched-total-compute>"
        matched.__package__ = "heterodiff.experiments"
        sys.modules[matched_name] = matched
        exec(
            compile(
                captured[
                    "src/heterodiff/experiments/matched_total_compute.py"
                ],
                matched.__file__,
                "exec",
            ),
            matched.__dict__,
        )
        setattr(experiments, "matched_total_compute", matched)

        b06_name = "heterodiff.experiments.two_domain_baseline_registry"
        b06 = types.ModuleType(b06_name)
        b06.__file__ = "<verified-b06-registry>"
        b06.__package__ = "heterodiff.experiments"
        sys.modules[b06_name] = b06
        exec(
            compile(
                captured[
                    "src/heterodiff/experiments/two_domain_baseline_registry.py"
                ],
                b06.__file__,
                "exec",
            ),
            b06.__dict__,
        )
        setattr(experiments, "two_domain_baseline_registry", b06)

        candidate_name = (
            "heterodiff.experiments.two_domain_training_checkpoint_plan"
        )
        candidate = types.ModuleType(candidate_name)
        candidate.__file__ = "<verified-training-checkpoint-plan>"
        candidate.__package__ = "heterodiff.experiments"
        sys.modules[candidate_name] = candidate
        exec(
            compile(captured[SOURCE_PATH], candidate.__file__, "exec"),
            candidate.__dict__,
        )
        setattr(experiments, "two_domain_training_checkpoint_plan", candidate)
        return b06, candidate
    except Exception as error:
        raise ValidationError("verified source compilation failed") from error
    finally:
        for name in reversed(names):
            previous = saved[name]
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


def _machine_by_path(
    captured: Mapping[str, bytes], path: str
) -> Dict[str, Any]:
    return _parse_json(captured[path], path)


def _closure_value(machine: Mapping[str, Any], field_id: str) -> object:
    rows = machine.get("field_closures")
    if type(rows) is not list:
        raise ValidationError("predecessor field closure roster is absent")
    matches = [
        row
        for row in rows
        if type(row) is dict and row.get("field_id") == field_id
    ]
    if len(matches) != 1:
        raise ValidationError("predecessor field closure is not unique")
    return matches[0].get("value")


def _direct_b06_rows(b06: types.ModuleType) -> List[Tuple[str, str, str, str]]:
    registry = b06.validate_registry(deepcopy(b06.FROZEN_REGISTRY))
    rows = []
    for primary in registry["primary_pair"]:
        for domain_id in b06.DOMAIN_IDS:
            rows.append(
                (
                    primary["method_id"],
                    domain_id,
                    primary["config_sha256"],
                    "PRIMARY",
                )
            )
    for control in registry["controls"]:
        for domain_id in b06.DOMAIN_IDS:
            rows.append(
                (
                    control["control_id"],
                    domain_id,
                    control["config_sha256"],
                    "CONTROL",
                )
            )
    for family in registry["literature_families"]:
        for domain_id in b06.DOMAIN_IDS:
            implementation = family["implementation_by_domain"][domain_id]
            rows.append(
                (
                    implementation["implementation_id"],
                    domain_id,
                    implementation["config_sha256"],
                    "LITERATURE_FAMILY",
                )
            )
    for external in registry["external_baselines"]:
        rows.append(
            (
                external["method_id"],
                external["domain_id"],
                external["config_sha256"],
                "EXTERNAL_BASELINE",
            )
        )
    result = sorted(rows)
    if len(result) != 22 or len(
        {(row[0], row[1]) for row in result}
    ) != 22:
        raise ValidationError("verified B06 roster is not exact-22")
    return result


def _synthetic_structural_qualification(
    candidate: types.ModuleType,
) -> Dict[str, Any]:
    executable = candidate.executable_configuration_rows()[0]
    checkpoint_sha = "1" * 64
    selection_sha = "2" * 64
    domain_id = executable["domain_id"]
    method_id = executable["method_id"]
    executable_sha = executable["executable_configuration_sha256"]
    rows = []
    for ordinal in range(128):
        score_hex = (
            "-0x1.0000000000000p+0"
            if ordinal % 2 == 0
            else "0x1.0000000000000p-1"
        )
        group_sha = _sha256(
            ("synthetic-group-" + str(ordinal)).encode("ascii")
        )
        formal_sha = _sha256(
            ("synthetic-formal-" + str(ordinal)).encode("ascii")
        )
        factory_sha = _domain_sha256(
            "heterodiff-production-cks-score-v1",
            {
                "binary64_score_hex": score_hex,
                "domain_id": domain_id,
                "draw_count": 64,
                "formal_score_sha256": formal_sha,
                "integration_id": "F105_CKS_BINARY64_PROJECTION_V1",
                "metric_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
                "score_direction": "LOWER_IS_BETTER",
                "symbolic_event_pair_work_units": 0,
            },
        )
        bound_sha = _domain_sha256(
            "heterodiff-f144-bound-group-score-integrity-v1",
            {
                "binary64_score_hex": score_hex,
                "checkpoint_content_sha256": checkpoint_sha,
                "domain_id": domain_id,
                "draw_count": 64,
                "executable_configuration_sha256": executable_sha,
                "f105_factory_score_integrity_sha256": factory_sha,
                "group_id_sha256": group_sha,
                "integration_id": "F105_CKS_BINARY64_PROJECTION_V1",
                "method_id": method_id,
                "metric_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
                "ordinal": ordinal,
                "selection_unit_sha256": selection_sha,
            },
        )
        rows.append(
            {
                "binary64_score_hex": score_hex,
                "f105_factory_score_integrity_sha256": factory_sha,
                "formal_score_sha256": formal_sha,
                "group_id_sha256": group_sha,
                "ordinal": ordinal,
                "score_integrity_sha256": bound_sha,
                "symbolic_event_pair_work_units": 0,
            }
        )
    roster_sha = _domain_sha256(
        "heterodiff-f144-complete-f134-validation-group-roster-v1",
        [row["group_id_sha256"] for row in rows],
    )
    certificate_sha = candidate.complete_roster_certificate_subject_sha256(
        checkpoint_content_sha256=checkpoint_sha,
        domain_id=domain_id,
        executable_configuration_sha256=executable_sha,
        group_roster_sha256=roster_sha,
        group_score_integrity_sha256s=[
            row["score_integrity_sha256"] for row in rows
        ],
        method_id=method_id,
        selection_unit_sha256=selection_sha,
    )
    value = {
        "checkpoint_content_sha256": checkpoint_sha,
        "complete_roster_certificate_subject_sha256": certificate_sha,
        "completed_optimizer_updates": 256,
        "domain_id": domain_id,
        "executable_configuration_sha256": executable_sha,
        "group_roster_sha256": roster_sha,
        "group_scores": rows,
        "method_id": method_id,
        "selection_unit_sha256": selection_sha,
    }
    receipt = candidate.validate_structural_checkpoint_validation(value)
    if (
        receipt["aggregate_binary64_hex"] != "-0x1.0000000000000p-2"
        or receipt["eligible_under_f144_structure"] is not True
        or receipt["production_history_authenticated"] is not False
    ):
        raise ValidationError("synthetic negative-score F144 KAT differs")
    hostile = deepcopy(value)
    hostile["group_scores"][0]["f105_factory_score_integrity_sha256"] = "0" * 64
    try:
        candidate.validate_structural_checkpoint_validation(hostile)
    except candidate.TrainingCheckpointPlanError:
        hostile_refused = True
    else:
        hostile_refused = False
    if not hostile_refused:
        raise ValidationError("F144 accepted a false factory integrity digest")
    return {
        "aggregate_binary64_hex": receipt["aggregate_binary64_hex"],
        "bound_group_score_count": len(rows),
        "factory_integrity_hostile_mutation_refused": hostile_refused,
        "negative_scores_accepted_under_f105_interval": True,
        "production_history_authenticated": False,
        "structural_receipt_sha256": receipt["structural_receipt_sha256"],
    }


def _validate_semantics(
    b06: types.ModuleType,
    candidate: types.ModuleType,
    predecessors: Mapping[str, bytes],
) -> Dict[str, Any]:
    b06_machine = _machine_by_path(
        predecessors,
        "research/fixtures/"
        "manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json",
    )
    f105_machine = _machine_by_path(
        predecessors,
        "research/fixtures/"
        "manuscript_v3_f105_manuscript_production_integration_v1.json",
    )
    theory_machine = _machine_by_path(
        predecessors,
        "research/fixtures/"
        "manuscript_v3_theory_statistics_blocker_closure_v1.json",
    )
    f145_machine = _machine_by_path(
        predecessors,
        "research/fixtures/"
        "manuscript_v3_f145_validation_early_stopping_freeze_v1.json",
    )
    f146_machine = _machine_by_path(
        predecessors,
        "research/fixtures/"
        "manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json",
    )
    f148_machine = _machine_by_path(
        predecessors,
        "research/fixtures/"
        "manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
    )
    b12_machine = _machine_by_path(
        predecessors,
        "research/fixtures/"
        "manuscript_v3_b12_integrated_offline_gap_package_v1.json",
    )

    registry = b06.validate_registry(deepcopy(b06.FROZEN_REGISTRY))
    if canonical_json_bytes(b06_machine.get("registry")) != canonical_json_bytes(
        registry
    ):
        raise ValidationError("accepted B06 machine registry differs from source")

    if (
        candidate.SCHEMA
        != "HETERODIFF_F139_F144_F147_TRAINING_CHECKPOINT_PLAN_V1"
        or tuple(candidate.FIELD_IDS) != FIELD_IDS
        or candidate.FIELD_POINTERS != FIELD_POINTERS
        or candidate.plan_semantics_sha256()
        != EXPECTED_PLAN_SEMANTICS_SHA256
        or candidate.f144_semantics_sha256()
        != EXPECTED_F144_SEMANTICS_SHA256
    ):
        raise ValidationError("candidate fixed identity differs")
    plan = candidate.validate_plan(candidate.plan_semantics())
    if plan["effects"] != {
        "b08_closed": False,
        "b12_closed": False,
        "blocker_delta": 0,
        "field_delta": 7,
        "formal_test_delta": 0,
        "result_delta": 0,
        "runtime_or_science_executed": False,
        "timetable_task_delta": 1,
    }:
        raise ValidationError("candidate effect surface differs")

    direct_rows = _direct_b06_rows(b06)
    actual_rows = sorted(
        (
            row["method_id"],
            row["domain_id"],
            row["b06_config_sha256"],
            row["registry_kind"],
        )
        for row in candidate.executable_configuration_rows()
    )
    if actual_rows != direct_rows:
        raise ValidationError("candidate roster is not directly B06-derived")
    executable_rows = candidate.executable_configuration_rows()
    if len(executable_rows) != 22 or len(
        {row["executable_configuration_sha256"] for row in executable_rows}
    ) != 22:
        raise ValidationError("executable configuration byte bindings differ")
    for domain_id in b06.DOMAIN_IDS:
        budget = b06.training_compute_budget(domain_id)[
            "phase_event_count_ceilings"
        ]
        if (
            budget["TUNING"]["BASE_FORWARD"] != 8 * 1024
            or budget["TUNING"]["DATA_ADAPTER_RECORD"] != 8 * 1024 * 16
            or budget["FINAL_TRAINING"]["BASE_FORWARD"] != 256 * 4096
            or budget["FINAL_TRAINING"]["DATA_ADAPTER_RECORD"]
            != 256 * 4096 * 16
        ):
            raise ValidationError("accepted B06 budget arithmetic differs")

    fields = candidate.field_values()
    if fields["F139"] != {
        "algorithm": "ADAMW_DECOUPLED_WEIGHT_DECAY",
        "algorithm_class": "torch.optim.AdamW",
        "amsgrad": False,
        "beta1": {"denominator": 10, "numerator": 9},
        "beta2": {"denominator": 1000, "numerator": 999},
        "capturable": False,
        "differentiable": False,
        "epsilon": {"denominator": 100000000, "numerator": 1},
        "foreach": False,
        "fused": False,
        "gradient_accumulation_steps": 1,
        "maximize": False,
        "one_optimizer_update_per_admitted_batch": True,
        "optimizer_id": "TORCH_ADAMW_EXACT_RATIONAL_SINGLE_GROUP_V1",
        "parameter_group_policy": "ONE_GROUP_ALL_AND_ONLY_TRAINABLE_PARAMETERS",
        "weight_decay": {"denominator": 1, "numerator": 0},
    }:
        raise ValidationError("F139 exact optimizer differs")

    schedule = fields["F140"]
    if (
        schedule["schedule_kind"]
        != "CONSTANT_AT_SELECTED_PREDECLARED_CANDIDATE_BASE_RATE"
        or schedule["warmup_completed_optimizer_updates"] != 0
        or schedule["learning_rate_multiplier"]
        != {"denominator": 1, "numerator": 1}
        or schedule["adaptive_or_validation_driven_change_permitted"] is not False
    ):
        raise ValidationError("F140 exact schedule differs")
    csdi = [
        row
        for row in schedule["rows"]
        if row["method_id"] == "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1"
    ]
    if (
        len(csdi) != 1
        or csdi[0]["base_learning_rate_candidates_exact_rational"]
        != ["1/2000", "1/1000"]
    ):
        raise ValidationError("F140 CSDI exact B06 rates differ")
    if any(
        row["base_learning_rate_candidates_exact_rational"] != ["1/1000"]
        for row in schedule["rows"]
        if row["method_id"] != "CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1"
    ):
        raise ValidationError("F140 singleton rates differ")

    precision = fields["F141"]
    if (
        precision["model_parameter_dtype"] != "IEEE754_BINARY32"
        or precision["gradient_dtype"] != "IEEE754_BINARY32"
        or precision["optimizer_moment_dtype"] != "IEEE754_BINARY32"
        or precision["f105_group_score_representation"]
        != "IEEE754_BINARY64_HEX_BOUND"
        or precision["validation_equality"]
        != "EXACT_CANONICAL_BINARY64_HEX_IDENTITY_NO_TOLERANCE"
        or precision["autocast_permitted"] is not False
        or precision["mixed_precision_permitted"] is not False
        or precision["tf32_permitted"] is not False
    ):
        raise ValidationError("F141 precision contract differs")

    batches = fields["F142"]
    if (
        batches["b06_data_adapter_records_per_optimizer_update"] != 16
        or batches["cross_domain_batch_permitted"] is not False
        or batches["implicit_or_random_shuffle_permitted"] is not False
        or len(batches["method_domain_contracts"]) != 22
    ):
        raise ValidationError("F142 batch construction differs")
    for row in batches["method_domain_contracts"]:
        if (
            row["batch_size_logical_records"] != 16
            or row["record_index_formula"]
            != "(16*COMPLETED_OPTIMIZER_UPDATES+j)_MOD_N_FOR_j_0_TO_15"
            or row["cross_domain_batch_permitted"] is not False
            or row["implicit_or_random_shuffle_permitted"] is not False
            or row["test_record_permitted"] is not False
        ):
            raise ValidationError("F142 method/domain contract differs")

    if type(fields["F143"]) is not int or fields["F143"] != 4096:
        raise ValidationError("F143 must be exact positive integer 4096")

    f144 = fields["F144"]
    if (
        f144["metric_id"] != "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
        or f144["production_integration_id"]
        != "F105_CKS_BINARY64_PROJECTION_V1"
        or f144["draw_count_per_group"] != 64
        or f144["f134_validation_group_count"] != 128
        or f144["direction"] != "LOWER_IS_BETTER"
        or f144["f105_formal_score_interval"]
        != {"closed_lower": -2, "closed_upper": 1}
        or f144["checkpoint_cadence"]
        != {
            "every_completed_optimizer_updates": 256,
            "terminal_f143_bound_included": True,
        }
        or f144["pure_structural_helper_authenticates_production_history"]
        is not False
    ):
        raise ValidationError("F144 exact validation contract differs")

    tuning = fields["F147"]["rows"]
    external = [row for row in tuning if row["maximum_trials"] == 8]
    singleton = [row for row in tuning if row["maximum_trials"] == 1]
    if (
        len(tuning) != 22
        or len(external) != 2
        or len(singleton) != 20
        or any(row["b06_global_tuning_trial_ceiling"] != 8 for row in tuning)
        or any(
            row["tuning_completed_optimizer_updates_per_trial"] != 1024
            for row in tuning
        )
        or any(row["test_access_permitted"] is not False for row in tuning)
    ):
        raise ValidationError("F147 exact B06 caps differ")

    if (
        f105_machine.get("primary_metric_id")
        != "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
        or f105_machine.get("production_integration_id")
        != "F105_CKS_BINARY64_PROJECTION_V1"
        or f105_machine.get("metric_semantics", {}).get("score_direction")
        != "LOWER_IS_BETTER"
        or f105_machine.get("production_contract", {}).get(
            "factory_issued_field_integrity_digest_revalidated"
        )
        is not True
    ):
        raise ValidationError("accepted F105 production semantics differ")
    if (
        _closure_value(theory_machine, "F134")
        != {"R3-PHYS": 128, "R4-RETAIL": 128}
        or _closure_value(theory_machine, "F136") != 64
        or theory_machine.get("r64_adapter_contract", {}).get(
            "draws_per_method"
        )
        != 64
    ):
        raise ValidationError("accepted F134/R64 semantics differ")
    if _closure_value(f145_machine, "F145") != candidate.F145_POLICY_VALUE:
        raise ValidationError("accepted F145 policy differs")
    f146_value = _closure_value(f146_machine, "F146")
    if (
        type(f146_value) is not dict
        or f146_value.get("rule_id") != candidate.F146_RULE_ID
        or f146_value.get(
            "complete_tied_best_roster_must_be_f144_certified"
        )
        is not True
    ):
        raise ValidationError("accepted F146 rule differs")
    if _closure_value(f148_machine, "F148") != candidate.F148_PREDICATE:
        raise ValidationError("accepted F148 predicate differs")

    b12_semantics = b12_machine.get("semantics")
    if (
        type(b12_semantics) is not dict
        or b12_machine.get("semantic_sha256")
        != "c5196b6bf3b7cfa2055aaeeb50d990bc3263d4e304fcfdbce3d11b2a3245b545"
        or b12_semantics.get("f144_candidate_contract")
        != {
            "aggregation": "ARITHMETIC_MEAN_OVER_COMPLETE_F134_VALIDATION_GROUP_ROSTER",
            "cadence": "EVERY_256_COMPLETED_OPTIMIZER_UPDATES_AND_F143_BOUND",
            "checkpoint_tie_rule": candidate.F146_RULE_ID,
            "complete_roster_certificate_required": True,
            "direction": "LOWER_IS_BETTER",
            "metric_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
            "projection_id": "F105_CKS_BINARY64_PROJECTION_V1",
            "test_data_permitted": False,
        }
        or b12_semantics.get("effects", {}).get("field_delta") != 0
        or b12_semantics.get("authority")
        != {"data": False, "network": False, "runtime": False, "science": False}
    ):
        raise ValidationError("accepted B12 stable semantics differ")

    b12_rows = {
        tuple(row) for row in b12_semantics["required_adapter_roster"]
    }
    direct_identity_rows = {
        (row[0], row[1], row[2]) for row in direct_rows
    }
    obsolete_b12_rows = b12_rows - direct_identity_rows
    missing_direct_rows = direct_identity_rows - b12_rows
    if (
        len(obsolete_b12_rows) != 8
        or len(missing_direct_rows) != 8
        or not all(
            row[3] == "LITERATURE_FAMILY"
            for row in direct_rows
            if (row[0], row[1], row[2]) in missing_direct_rows
        )
    ):
        raise ValidationError("obsolete B12 literature mismatch projection differs")
    if (
        "TRAINING_CHECKPOINT_PLAN_F139_F144_F147_COMPLETE_AND_INTEGRATED"
        not in b12_semantics.get("residual_predicate_ids", [])
    ):
        raise ValidationError("B12 training residual identity differs")

    return {
        "accepted_b06_record_sha256": b06_machine["record_sha256"],
        "accepted_b12_record_sha256": b12_machine["record_sha256"],
        "accepted_b12_semantic_sha256": b12_machine["semantic_sha256"],
        "accepted_f105_record_sha256": f105_machine["record_sha256"],
        "accepted_f134_r64_record_sha256": theory_machine["record_sha256"],
        "accepted_f145_record_sha256": f145_machine["record_sha256"],
        "accepted_f146_record_sha256": f146_machine["record_sha256"],
        "accepted_f148_record_sha256": f148_machine["record_sha256"],
        "b06_direct_adapter_row_count": len(direct_rows),
        "b12_obsolete_literature_rows_refused_as_authority": len(
            obsolete_b12_rows
        ),
        "b12_predecessor_scope": "STABLE_SEMANTICS_ONLY_NOT_ADAPTER_ROSTER",
        "b12_training_residual_eligible_on_independent_acceptance": True,
        "new_unaccepted_b12_successor_bytes_bound": False,
        "production_receipts_supplied_or_authenticated": False,
    }


def _expected_record(
    *,
    package_bindings: List[Dict[str, Any]],
    predecessor_bindings: List[Dict[str, Any]],
    source_effect_surface: Dict[str, Any],
    plan_semantics: Dict[str, Any],
    plan_semantics_sha256: str,
    predecessor_projection: Dict[str, Any],
    synthetic_qualification: Dict[str, Any],
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "authority_provenance": {
            "data_entropy_training_runtime_science_or_network_authorized": False,
            "offline_local_package_construction_authorized": True,
            "predecessor_tracker_or_ledger_edit_authorized": False,
            "registration_requires_separate_independent_acceptance": True,
        },
        "control_predicate": CONTROL_PREDICATE,
        "count_transition": {
            "after": {
                "post_closed": 5,
                "post_open": 1,
                "pre_closed": 143,
                "pre_open": 23,
                "total_closed": 148,
                "total_open": 24,
            },
            "before": {
                "post_closed": 5,
                "post_open": 1,
                "pre_closed": 136,
                "pre_open": 30,
                "total_closed": 141,
                "total_open": 31,
            },
            "delta": {
                "closed": 7,
                "closed_fields": list(FIELD_IDS),
                "open": -7,
            },
        },
        "evidence_ready_registration": {
            "conditional_on_independent_acceptance": True,
            "permitted_blocker_delta": [],
            "permitted_field_delta": list(FIELD_IDS),
            "permitted_formal_test_delta": [],
            "permitted_result_delta": [],
            "proposed_text": REGISTRATION_TEXT,
            "registration_performed_by_this_package": False,
        },
        "global_state": GLOBAL_STATE,
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "raw_self_hash_embedded": False,
            "semantic_self_digest_field": "record_sha256",
        },
        "package_bindings_excluding_machine_self": package_bindings,
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_kind": PACKAGE_KIND,
        "plan_semantics": plan_semantics,
        "plan_semantics_sha256": plan_semantics_sha256,
        "predecessor_bindings": predecessor_bindings,
        "predecessor_group_counts": dict(PREDECESSOR_GROUP_COUNTS),
        "predecessor_semantic_projection": predecessor_projection,
        "project_effects_and_nonclaims": {
            "B08_closed": False,
            "B12_closed": False,
            "F145_or_F146_reclosed_or_modified": False,
            "adapter_runner_capsule_ledger_or_recomputation_candidate_accepted": False,
            "all_seven_fields_close_only_all_or_nothing": True,
            "blocker_delta": 0,
            "capacity_hardware_or_runtime_identity_claimed": False,
            "checkpoint_or_production_receipt_created": False,
            "data_accessed": False,
            "entropy_consumed": False,
            "formal_test_delta": 0,
            "independent_acceptance_performed": False,
            "model_trained": False,
            "new_b12_successor_bytes_bound": False,
            "real_production_receipt_exists": False,
            "result_or_scientific_claim_created": False,
            "submission_or_release_performed": False,
            "timetable_or_evidence_ledger_edited": False,
        },
        "qualification_boundary": {
            "candidate_and_b06_source_compiled_only_after_raw_hash_validation": True,
            "hostile_tests_write_only_disposable_pytest_roots": True,
            "predecessor_bytes_modified": False,
            "pure_structural_helper_authenticates_production_history": False,
            "read_only_validator": True,
            "self_validation_is_independent_acceptance": False,
            "validator_writer_network_connector_subprocess_entropy_data_training_runtime_or_science_route_present": False,
        },
        "reported_date": REPORTED_DATE,
        "source_effect_surface": source_effect_surface,
        "state": STATE,
        "synthetic_structural_qualification": synthetic_qualification,
        "timetable_transition": {
            "after": {"checked": 59, "open": 104, "total": 163},
            "before": {"checked": 58, "open": 105, "total": 163},
            "closed_existing_task": (
                "Freeze checkpoint-selection and training rules using "
                "training/validation data only"
            ),
            "new_task_created": False,
        },
        "workstream_transition": {
            "after": {"closed": 55, "open": 10},
            "before": {"closed": 48, "open": 17},
            "gate_a_after": {"closed": 5, "open": 3, "total": 8},
            "gate_a_before": {"closed": 5, "open": 3, "total": 8},
            "open_blockers_after": 7,
            "open_blockers_before": 7,
        },
        "schema_version": SCHEMA,
    }
    record["record_sha256"] = record_sha256(record)
    return record


def construct_expected_record(
    root: Path = WORKSPACE_ROOT,
) -> Dict[str, Any]:
    """Construct the exact expected machine record without reading it."""

    root = _validate_root(root)
    package_bindings, current = _current_package_bindings(root)
    predecessor_bindings, predecessors = _fixed_predecessors(root)
    captured = dict(predecessors)
    captured.update(current)
    source_surface = _source_effect_surface(current[SOURCE_PATH])
    b06, candidate = _compile_verified_modules(captured)
    predecessor_projection = _validate_semantics(
        b06, candidate, predecessors
    )
    synthetic = _synthetic_structural_qualification(candidate)
    plan = candidate.validate_plan(candidate.plan_semantics())
    return _expected_record(
        package_bindings=package_bindings,
        predecessor_bindings=predecessor_bindings,
        source_effect_surface=source_surface,
        plan_semantics=plan,
        plan_semantics_sha256=candidate.plan_semantics_sha256(),
        predecessor_projection=predecessor_projection,
        synthetic_qualification=synthetic,
    )


def validate_package(
    root: Path = WORKSPACE_ROOT,
    machine_path: str = MACHINE_PATH,
) -> Dict[str, Any]:
    root = _validate_root(root)
    machine_raw = _stable_read(root, machine_path)
    if not machine_raw.endswith(b"\n"):
        raise ValidationError("machine record must end in one LF")
    machine = _parse_json(machine_raw, machine_path, exact_tree=True)
    if machine_raw != canonical_json_bytes(machine) + b"\n":
        raise ValidationError("machine record is not canonical ASCII JSON")
    expected = construct_expected_record(root)
    if canonical_json_bytes(machine) != canonical_json_bytes(expected):
        raise ValidationError("machine record differs from reconstructed package")
    if machine.get("record_sha256") != record_sha256(machine):
        raise ValidationError("machine semantic self-digest differs")
    return {
        "closed_field_count": 7,
        "closed_field_ids": list(FIELD_IDS),
        "field_delta": 7,
        "plan_semantics_sha256": machine["plan_semantics_sha256"],
        "record_sha256": machine["record_sha256"],
        "status": PASS_TOKEN,
        "timetable_task_delta": 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the exact F139--F144/F147 candidate package."
    )
    parser.add_argument("--root", type=Path, default=WORKSPACE_ROOT)
    arguments = parser.parse_args()
    result = validate_package(arguments.root)
    if result["status"] != PASS_TOKEN:
        raise ValidationError("unexpected validation status")
    print(PASS_TOKEN)


if __name__ == "__main__":
    main()
