"""Read-only custody and semantic validator for the F061 proposal successor.

The validator never imports or executes the candidate successor source.  It
pins every bound byte first, independently checks the proposal and exact-count
guard codecs, and preserves strict null review/definition slots.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, Mapping, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-f061-preservation-first-allocation-proposal-v1"
)
STATE = "F061_PROPOSAL_FROZEN_AWAITING_SEPARATE_INDEPENDENT_POWER_REVIEW"
PACKAGE_KIND = "ADDITIVE_F061_PROPOSAL_AND_EXACT_COUNT_COMPATIBILITY_GUARD"
REPORTED_DATE = "2026-09-01"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
PACKAGE_AGGREGATE_DOMAIN = (
    b"heterodiff/manuscript-v3-f061-preservation-first-package-aggregate/v1\0"
)
PROPOSAL_DOMAIN = b"heterodiff/two-domain-f061-shared-policy-proposal/v1\0"
GUARD_DOMAIN = b"heterodiff/two-domain-f061-exact-count-guard-contract/v1\0"

HUMAN_PATH = "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_PROPOSAL.md"
SOURCE_PATH = (
    "src/heterodiff/data/two_domain_f061_preservation_first_successor.py"
)
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_f061_preservation_first_allocation_proposal_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_f061_preservation_first_allocation_proposal_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_f061_preservation_first_allocation_proposal_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, SOURCE_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)
NONMACHINE_PACKAGE_ROSTER = (HUMAN_PATH, SOURCE_PATH, VALIDATOR_PATH, TEST_PATH)

PROPOSAL_SHA256 = (
    "cf26d91eb850990d3fb179c376ab27ca12d0ff0de490f2ee4a5c6020fe66c679"
)
GUARD_SHA256 = (
    "98a9ec44fb76b08285ac86e63e4fbb3db3b6b232f16a12b436f3d9f8283b3fef"
)
ALLOCATION_ID = (
    "TWO_DOMAIN_F061_HAMILTON_70_15_15_EXACT_128_VALIDATION_TEST_V1"
)
POWER_REQUIREMENT_ID = (
    "B07_F134_EXACT_128_VALIDATION_AND_TEST_GROUPS_NO_EXCLUSION_V1"
)
ROUNDING_RULE_ID = (
    "HAMILTON_DESCENDING_INTEGER_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
)
TERMINAL_NO_GO_CODE = (
    "F061_EXACT_128_VALIDATION_TEST_COMPATIBILITY_TERMINAL_NO_GO"
)
SOLE_SUPPORTED_ENTRYPOINTS = (
    "project_reviewed_shared_policy_to_retail",
    "resolve_reviewed_retail_policy",
    "project_reviewed_shared_policy_to_physionet_review_candidate",
)
ADMISSIBLE_PAIRS = (
    (852, (596, 128, 128)),
    (853, (597, 128, 128)),
    (854, (598, 128, 128)),
    (855, (599, 128, 128)),
)

# Every byte accepted by the B02/B03 review plus that review receipt, followed
# by every byte accepted by the theory/statistics review plus that receipt.
PREDECESSOR_SPECS = (
    ("ACCEPTED_B02_B03_ACTIVATION", "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md", 17235, "a7e882f209b26d9cf6dec449eb4fd93b78df0903be9294704ea857066dfe00ed", "human"),
    ("ACCEPTED_B02_B03_ACTIVATION", "src/heterodiff/data/two_domain_offline_precontact_activation.py", 51882, "f192e3eedbeb73f2eb1ea0705e56af65ea723a91071db93835b9b8f56046d97c", "source"),
    ("ACCEPTED_B02_B03_ACTIVATION", "tests/unit/test_two_domain_offline_precontact_activation.py", 32506, "e96d4648095fe25332ae36deac5f27a1aafe80cc5ac3b50a1efcd9f39b4b1144", "test"),
    ("ACCEPTED_B02_B03_ACTIVATION", "src/heterodiff/data/physionet_2012_admission_preflight.py", 136305, "bf5c12dcb5debe99533d00a813d7b522c42b588f5431803a8c2bac99b0f2bf07", "source"),
    ("ACCEPTED_B02_B03_ACTIVATION", "tests/unit/test_physionet_2012_admission_preflight.py", 67299, "25786cf1d2bc971c8b8f08c2aabc18fa192ed7b75fd67944486238fb83c8d57c", "test"),
    ("ACCEPTED_B02_B03_ACTIVATION", "src/heterodiff/data/online_retail_ii_admission_preflight.py", 89545, "3f204d65c87b8ee7896209c687f2394a1a9c23cdf9a7670b40227cf46e518764", "source"),
    ("ACCEPTED_B02_B03_ACTIVATION", "tests/unit/test_online_retail_ii_admission_preflight.py", 52656, "1016755132b5bfd0ef8378c6adee60eacbe5fb571240c06d5e84804c99769c5a", "test"),
    ("ACCEPTED_B02_B03_ACTIVATION", "research/fixtures/manuscript_v3_b02_b03_offline_precontact_activation_v1.json", 22137, "d74333a2c381daa953803e9346efb0ab63d6744265bfa8e7e260b1d1932fc0ee", "machine"),
    ("ACCEPTED_B02_B03_ACTIVATION", "research/diagnostics/manuscript_v3_b02_b03_offline_precontact_activation_v1.py", 35949, "e1803c8ecccb63d0da4ebb71a9676291c45678b735f4cffc58b5073814d4647b", "validator"),
    ("ACCEPTED_B02_B03_ACTIVATION", "tests/unit/test_manuscript_v3_b02_b03_offline_precontact_activation_v1.py", 23669, "03e85a57f4b57fca8d498295650a0672dbfb8f2e1c17358c93141370ca8c5716", "test"),
    ("ACCEPTED_B02_B03_ACTIVATION", "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION_INDEPENDENT_REVIEW.md", 10196, "a1baf2b04740ac38540a4008dcb09042f8c92fa978c51fe22ac54cb30c81f0d0", "independent_review"),
    ("ACCEPTED_THEORY_STATISTICS", "src/heterodiff/evaluation/preoutcome_theory_statistics_contract.py", 26545, "1ad767ea4e6d8fec0b19837ba26a9bd6f920fc90be48fc7bb4059c30b10ea718", "source"),
    ("ACCEPTED_THEORY_STATISTICS", "src/heterodiff/evaluation/fixed_r64_cks_statistical_adapter.py", 7013, "63dbc81b804ed643406d401559b38305654ef43d0b9a4ade17feb9e2152eb278", "source"),
    ("ACCEPTED_THEORY_STATISTICS", "manuscript_v3/c17_retirement_no_claim_successor_v1.md", 2234, "de9de9039c9826ad4755158b6cc6d50cf5201f5d27bbde6f084884c7bb72c85d", "manuscript"),
    ("ACCEPTED_THEORY_STATISTICS", "manuscript_v3/manuscript_v3_f109_f112_statistical_successor_v1.md", 3378, "d3a23b2a78327b00146a03ff6a88a22aa08e0452b5b2c00067b538873761d688", "manuscript"),
    ("ACCEPTED_THEORY_STATISTICS", "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md", 17299, "bb4438887f54710b0445e0b713ee086abc2523b2bf34b4a08d42ee586515d721", "human"),
    ("ACCEPTED_THEORY_STATISTICS", "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json", 20936, "2ff92ac1b4b6df75931791cd16ce7ade461c70b29042a17486bc2804f35295f1", "machine"),
    ("ACCEPTED_THEORY_STATISTICS", "research/diagnostics/manuscript_v3_theory_statistics_blocker_closure_v1.py", 42464, "17a2b3e38618ccbcd5127e58173a563299467840776572e6507041109c6d32f4", "validator"),
    ("ACCEPTED_THEORY_STATISTICS", "tests/unit/test_manuscript_v3_theory_statistics_blocker_closure_v1.py", 28916, "09a0bf4171dab42a759802ab10b59106c6c830f1fd7d4952d89e50b47467655f", "test"),
    ("ACCEPTED_THEORY_STATISTICS", "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE_INDEPENDENT_REVIEW.md", 3270, "ede11cff876c96cafe5734cee59ffae347b001dc8e16c3b3b71437d6cb4a0b64", "independent_review"),
)


class ValidationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValidationError("value is not canonical ASCII JSON") from error


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict or record.get("schema_version") != SCHEMA:
        raise ValidationError("successor machine schema mismatch")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return hashlib.sha256(RECORD_DOMAIN + canonical_bytes(payload)).hexdigest()


def package_aggregate_sha256(bindings: Any) -> str:
    if type(bindings) is not list:
        raise ValidationError("package bindings must be a built-in array")
    return hashlib.sha256(
        PACKAGE_AGGREGATE_DOMAIN + canonical_bytes(bindings)
    ).hexdigest()


def _reject_duplicate_pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def strict_json(data: bytes, *, canonical_lf: bool) -> Dict[str, Any]:
    if canonical_lf:
        if not data.endswith(b"\n") or data.endswith(b"\n\n"):
            raise ValidationError("machine record must end in exactly one LF")
        body = data[:-1]
    else:
        body = data
    try:
        text = body.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValidationError("forbidden JSON constant: " + token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("record is not strict ASCII JSON") from error
    if type(value) is not dict:
        raise ValidationError("record must be a built-in object")
    if canonical_lf and body != canonical_bytes(value):
        raise ValidationError("machine record bytes are not canonical")
    return value


def _validate_relative_path(relative: str) -> Tuple[str, ...]:
    if type(relative) is not str or not relative or relative.startswith("/"):
        raise ValidationError("unsafe relative path")
    parts = tuple(relative.split("/"))
    if any(not part or part in (".", "..") or "\x00" in part for part in parts):
        raise ValidationError("unsafe relative path component")
    return parts


def _open_component(parent_fd: int, name: str, *, directory: bool) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    return os.open(name, flags, dir_fd=parent_fd)


def read_stable_regular(root: Path, relative: str, *, ceiling: int = 2_000_000) -> bytes:
    parts = _validate_relative_path(relative)
    if not root.is_absolute() or root != Path(os.path.realpath(root)):
        raise ValidationError("workspace root must be absolute and canonical")
    root_fd = os.open(
        str(root),
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0),
    )
    opened = [root_fd]
    try:
        root_before = os.fstat(root_fd)
        if not stat.S_ISDIR(root_before.st_mode):
            raise ValidationError("workspace root is not a directory")
        parent = root_fd
        for part in parts[:-1]:
            parent = _open_component(parent, part, directory=True)
            opened.append(parent)
            info = os.fstat(parent)
            if not stat.S_ISDIR(info.st_mode):
                raise ValidationError("path ancestor is not a directory")
        leaf = _open_component(parent, parts[-1], directory=False)
        opened.append(leaf)
        before = os.fstat(leaf)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError("bound leaf is not regular")
        if stat.S_IMODE(before.st_mode) != 0o644 or before.st_nlink != 1:
            raise ValidationError("bound leaf mode or link count drift")
        if before.st_size < 1 or before.st_size > ceiling:
            raise ValidationError("bound leaf size outside ceiling")
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                raise ValidationError("short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(leaf, 1):
            raise ValidationError("file grew during read")
        after = os.fstat(leaf)
        namespace = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        root_after = os.fstat(root_fd)
        stable = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        if stable != (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValidationError("bound leaf changed during read")
        if (namespace.st_dev, namespace.st_ino) != (before.st_dev, before.st_ino):
            raise ValidationError("bound leaf namespace changed during read")
        if (root_after.st_dev, root_after.st_ino) != (
            root_before.st_dev,
            root_before.st_ino,
        ):
            raise ValidationError("workspace root changed during read")
        return b"".join(chunks)
    except OSError as error:
        raise ValidationError("safe file open failed: " + relative) from error
    finally:
        for descriptor in reversed(opened):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _binding(
    ordinal: int,
    path: str,
    data: bytes,
    role: str,
    group: str,
) -> Dict[str, Any]:
    return {
        "ordinal": ordinal,
        "path": path,
        "role": role,
        "group": group,
        "bytes": len(data),
        "raw_sha256": _sha256(data),
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": data.endswith(b"\n"),
    }


def expected_predecessor_bindings() -> list[Dict[str, Any]]:
    rows = []
    for ordinal, (group, path, size, digest, role) in enumerate(PREDECESSOR_SPECS):
        rows.append(
            {
                "ordinal": ordinal,
                "path": path,
                "role": role,
                "group": group,
                "bytes": size,
                "raw_sha256": digest,
                "mode_octal": "0644",
                "nlink": 1,
                "terminal_lf": True,
            }
        )
    return rows


def _proposal_expected() -> Dict[str, Any]:
    return {
        "schema_version": "heterodiff-two-domain-f061-shared-policy-v1",
        "allocation_id": ALLOCATION_ID,
        "mode": "EXACT_PROPORTIONS_HAMILTON",
        "values": [70, 15, 15],
        "denominator_is_null": False,
        "denominator": 100,
        "minimum_counts": [1, 128, 128],
        "rounding_rule_id": ROUNDING_RULE_ID,
        "power_requirement_id": POWER_REQUIREMENT_ID,
    }


def _guard_expected() -> Dict[str, Any]:
    return {
        "schema_version": "heterodiff-two-domain-f061-exact-count-guard-contract-v1",
        "shared_policy_proposal_sha256": PROPOSAL_SHA256,
        "split_names": ["TRAIN", "VALIDATION", "TEST"],
        "values": [70, 15, 15],
        "denominator": 100,
        "minimum_counts": [1, 128, 128],
        "required_exact_counts": {"VALIDATION": 128, "TEST": 128},
        "admissible_natural_group_totals": [852, 853, 854, 855],
        "admissible_total_count_pairs": [
            [852, [596, 128, 128]],
            [853, [597, 128, 128]],
            [854, [598, 128, 128]],
            [855, [599, 128, 128]],
        ],
        "all_natural_groups_must_be_allocated": True,
        "exclusion_topup_retry_resplit_or_proportion_change_permitted": False,
        "larger_than_128_validation_or_test_substitution_permitted": False,
        "terminal_no_go_code": TERMINAL_NO_GO_CODE,
        "sole_supported_projection_resolution_entrypoints": list(
            SOLE_SUPPORTED_ENTRYPOINTS
        ),
        "direct_generic_predecessor_projection_or_resolution_supported_for_this_policy": False,
        "retail_temporal_feasibility_claimed_by_count_resolution": False,
        "physionet_resolved_counts_require_separate_external_review": True,
        "guarded_review_receipt_carrier": (
            "CANONICAL_DUPLICATE_FREE_ASCII_JSON_NO_TERMINAL_LF"
        ),
        "reviewer_attestation_domain_ascii": (
            "heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1"
        ),
        "reviewer_attestation_domain_suffix_hex": "00",
        "reviewer_attestation_preimage": (
            "ALL_EXACT_RECEIPT_FIELDS_EXCLUDING_"
            "INDEPENDENT_REVIEWER_ATTESTATION_SHA256"
        ),
        "reviewer_attestation_is_identity_signature": False,
        "independent_custody_reopens_actual_candidate_bytes": True,
        "source_self_pins_own_raw_sha256": False,
    }


def _semantic_predecessor_sha256(
    record: Dict[str, Any], *, schema: str, null_instead_of_remove: bool
) -> str:
    payload = dict(record)
    if null_instead_of_remove:
        payload["record_sha256"] = None
    else:
        payload.pop("record_sha256", None)
    return hashlib.sha256(
        schema.encode("ascii") + b"\0" + canonical_bytes(payload)
    ).hexdigest()


def _validate_predecessor_semantics(captured: Mapping[str, bytes]) -> None:
    b02_path = "research/fixtures/manuscript_v3_b02_b03_offline_precontact_activation_v1.json"
    theory_path = "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json"
    b02 = strict_json(captured[b02_path], canonical_lf=False)
    theory = strict_json(captured[theory_path], canonical_lf=False)
    if b02.get("record_sha256") != "2a150e0b3037d01e6b311d9ab4c17157f20031f75b644a7c8778007c168b9fec":
        raise ValidationError("accepted activation semantic digest drift")
    if b02["record_sha256"] != _semantic_predecessor_sha256(
        b02,
        schema="heterodiff-b02-b03-offline-precontact-activation-v1",
        null_instead_of_remove=True,
    ):
        raise ValidationError("accepted activation semantic digest mismatch")
    boundary = b02.get("shared_f061_policy_boundary")
    if type(boundary) is not dict or boundary.get("f061_field_status") != "OPEN":
        raise ValidationError("accepted activation F061 status drift")
    slots = boundary.get("unresolved_policy_slots")
    if type(slots) is not dict or len(slots) != 12 or any(
        value is not None for value in slots.values()
    ):
        raise ValidationError("accepted activation F061 null boundary drift")
    effect = b02.get("closure_effect")
    if (
        type(effect) is not dict
        or effect.get("b02_closed") is not False
        or effect.get("b03_closed") is not False
        or effect.get("field_count_delta") != 0
        or effect.get("blocker_count_delta") != 0
    ):
        raise ValidationError("accepted activation closure boundary drift")
    if theory.get("record_sha256") != "335879da927b14de0f2ab0cb69b531ea51f24d9734777cb33cdf1e90fb81a491":
        raise ValidationError("accepted theory semantic digest drift")
    if theory["record_sha256"] != _semantic_predecessor_sha256(
        theory,
        schema="heterodiff-manuscript-v3-theory-statistics-blocker-closure-v1",
        null_instead_of_remove=False,
    ):
        raise ValidationError("accepted theory semantic digest mismatch")
    fields = theory.get("field_closures")
    if type(fields) is not list:
        raise ValidationError("accepted theory field roster missing")
    values = {
        row.get("field_id"): row.get("value")
        for row in fields
        if type(row) is dict and row.get("field_id") in ("F111", "F134")
    }
    if values != {
        "F111": "VALIDATION_ONLY_GROUP_DISJOINT_SAME_CKS_BIASED_MMD2_DETERMINISTIC_256_SPLIT_Q95_NOT_SUBTRACTED",
        "F134": {"R3-PHYS": 128, "R4-RETAIL": 128},
    }:
        raise ValidationError("accepted F111/F134 evidence drift")
    if theory.get("blocker_effects", {}).get("B07") != (
        "CLOSED_BY_FIXED_DISTRIBUTION_FREE_POWER_AND_SEED_SCHEDULE"
    ):
        raise ValidationError("accepted B07 evidence drift")
    if theory.get("nonclaims", {}).get("ledger_or_timetable_edited") is not False:
        raise ValidationError("accepted theory nonclaim drift")


def _validate_source_surface(source: bytes) -> None:
    try:
        tree = ast.parse(source.decode("utf-8"), filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("successor source is not valid UTF-8 Python") from error
    forbidden_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "random",
        "requests",
        "socket",
        "subprocess",
    }
    forbidden_calls = {
        "open",
        "request",
        "send",
        "sendall",
        "urlopen",
        "write_bytes",
        "write_text",
    }
    imported = set()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    if imported & forbidden_imports or called & forbidden_calls:
        raise ValidationError("successor source exposes prohibited I/O surface")


def _validate_machine(record: Dict[str, Any]) -> None:
    expected_keys = {
        "schema_version",
        "state",
        "package_kind",
        "reported_date",
        "authority_provenance",
        "proposal_slot_state",
        "exact_count_guard_contract",
        "guarded_review_requirement",
        "review_remediation",
        "domain_projection_boundary",
        "accepted_predecessor_bindings",
        "predecessor_semantic_receipt",
        "package_file_roster",
        "package_bindings_excluding_machine_self",
        "package_aggregate_sha256",
        "machine_self_binding",
        "closure_effect",
        "nonclaims",
        "record_sha256",
    }
    if set(record) != expected_keys:
        raise ValidationError("successor machine top-level roster drift")
    if (
        type(record["schema_version"]) is not str
        or record["schema_version"] != SCHEMA
        or record["state"] != STATE
        or record["package_kind"] != PACKAGE_KIND
        or record["reported_date"] != REPORTED_DATE
    ):
        raise ValidationError("successor machine identity drift")
    slots = record["proposal_slot_state"]
    if type(slots) is not dict or set(slots) != {
        "f061_allocation_id",
        "f061_mode",
        "f061_values",
        "f061_denominator_is_null",
        "f061_denominator",
        "f061_minimum_counts",
        "f061_rounding_rule_id",
        "f061_power_requirement_id",
        "f061_allocation_proposal_sha256",
        "f061_power_review_receipt_sha256",
        "f061_power_review_accepted",
        "f061_allocation_definition_sha256",
        "f061_field_status",
    }:
        raise ValidationError("F061 proposal slot roster drift")
    proposal = {
        "schema_version": "heterodiff-two-domain-f061-shared-policy-v1",
        "allocation_id": slots["f061_allocation_id"],
        "mode": slots["f061_mode"],
        "values": slots["f061_values"],
        "denominator_is_null": slots["f061_denominator_is_null"],
        "denominator": slots["f061_denominator"],
        "minimum_counts": slots["f061_minimum_counts"],
        "rounding_rule_id": slots["f061_rounding_rule_id"],
        "power_requirement_id": slots["f061_power_requirement_id"],
    }
    if proposal != _proposal_expected():
        raise ValidationError("exact F061 proposal drift")
    proposal_digest = hashlib.sha256(
        PROPOSAL_DOMAIN + canonical_bytes(proposal)
    ).hexdigest()
    if proposal_digest != PROPOSAL_SHA256 or slots[
        "f061_allocation_proposal_sha256"
    ] != PROPOSAL_SHA256:
        raise ValidationError("F061 proposal digest mismatch")
    if (
        slots["f061_power_review_receipt_sha256"] is not None
        or slots["f061_power_review_accepted"] is not None
        or slots["f061_allocation_definition_sha256"] is not None
        or slots["f061_field_status"] != "OPEN"
    ):
        raise ValidationError("review acceptance or F061 closure smuggled")
    guard = record["exact_count_guard_contract"]
    if guard != _guard_expected():
        raise ValidationError("exact-count guard contract drift")
    guard_digest = hashlib.sha256(GUARD_DOMAIN + canonical_bytes(guard)).hexdigest()
    if guard_digest != GUARD_SHA256:
        raise ValidationError("exact-count guard digest mismatch")
    review = record["guarded_review_requirement"]
    if type(review) is not dict or review != {
        "schema_version": "heterodiff-two-domain-f061-guarded-power-review-receipt-v1",
        "review_scope": "SHARED_F061_POWER_AND_EXACT_COUNT_GUARD_ACCEPTANCE",
        "review_kind": "INDEPENDENT_TECHNICAL_STATISTICAL_POLICY_REVIEW",
        "current_guarded_review_receipt_sha256": None,
        "current_guarded_review_accepted": None,
        "current_shared_definition_sha256": None,
        "future_receipt_must_bind_proposal_sha256": PROPOSAL_SHA256,
        "future_receipt_must_bind_guard_contract_sha256": GUARD_SHA256,
        "future_receipt_must_bind_successor_source_human_machine_and_package": True,
        "future_receipt_raw_sha_must_equal_activation_review_slot": True,
        "independent_custody_reopening_and_reviewer_separation_required": True,
        "institutional_operational_or_governance_approval": False,
        "reviewer_identity_externally_authenticated": False,
        "authoritative_receipt_carrier": (
            "CANONICAL_DUPLICATE_FREE_ASCII_JSON_NO_TERMINAL_LF"
        ),
        "sole_supported_entrypoints_json_carrier": "EXACT_BUILTIN_LIST",
        "reviewer_attestation_domain_ascii": (
            "heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1"
        ),
        "reviewer_attestation_domain_suffix_hex": "00",
        "reviewer_attestation_preimage": (
            "ALL_EXACT_RECEIPT_FIELDS_EXCLUDING_"
            "INDEPENDENT_REVIEWER_ATTESTATION_SHA256"
        ),
        "reviewer_attestation_is_identity_signature": False,
        "source_self_pins_own_raw_sha256": False,
        "independent_custody_must_reopen_actual_candidate_bytes": True,
        "self_authored_review_permitted": False,
    }:
        raise ValidationError("guarded review requirement drift")
    remediation = record["review_remediation"]
    if type(remediation) is not dict or remediation != {
        "prior_independent_review_decision": "NO_GO",
        "prior_review_receipt_created": False,
        "p1_json_native_list_and_authoritative_raw_byte_validation_remediated": True,
        "p2_noncircular_domain_separated_reviewer_attestation_remediated": True,
        "remediation_is_review_acceptance": False,
        "f061_remains_open": True,
    }:
        raise ValidationError("review remediation receipt drift")
    domain = record["domain_projection_boundary"]
    if type(domain) is not dict or domain != {
        "retail_native_proposal_present": False,
        "retail_resolved_counts_present": False,
        "retail_temporal_feasibility_claimed": False,
        "physionet_natural_group_count_observed": False,
        "physionet_native_proposal_present": False,
        "physionet_exact_count_review_present": False,
        "shared_review_would_accept_physionet_resolved_counts": False,
        "direct_generic_predecessor_entrypoints_supported_for_this_policy": False,
        "sole_supported_projection_resolution_entrypoints": list(
            SOLE_SUPPORTED_ENTRYPOINTS
        ),
    }:
        raise ValidationError("domain projection boundary drift")
    effect = record["closure_effect"]
    zero_fields = (
        "field_count_delta",
        "blocker_count_delta",
        "formal_test_count_delta",
        "scientific_result_count_delta",
        "operational_task_count_delta",
        "timetable_checked_task_delta",
    )
    if type(effect) is not dict or any(
        type(effect.get(key)) is not int or effect.get(key) != 0
        for key in zero_fields
    ):
        raise ValidationError("nonzero closure delta")
    if (
        effect.get("f061_closed") is not False
        or effect.get("b02_closed") is not False
        or effect.get("b03_closed") is not False
        or effect.get("tracker_edited") is not False
        or effect.get("evidence_ledger_edited") is not False
        or effect.get("permitted_field_delta") != []
    ):
        raise ValidationError("closure or tracker edit smuggled")
    nonclaims = record["nonclaims"]
    if type(nonclaims) is not dict or not nonclaims or any(
        type(value) is not bool or value is not False for value in nonclaims.values()
    ):
        raise ValidationError("nonclaim boundary drift")
    authority = record["authority_provenance"]
    if type(authority) is not dict or authority != {
        "normalized_visible_text": "Sounds good. Go ahead and finish them.",
        "normalized_visible_text_sha256": "3603d28cfd23787f17c427626c20792e9e66f3383b55d6d8090915ea9c7bea5c",
        "offline_local_construction_and_qualification_authorized": True,
        "network_contact_data_runtime_or_science_authorized": False,
        "tracker_ledger_or_accepted_predecessor_edit_authorized": False,
        "account_identity_externally_authenticated": False,
        "created_time_externally_attested": False,
    }:
        raise ValidationError("authority provenance drift")
    semantic = record["predecessor_semantic_receipt"]
    if type(semantic) is not dict or semantic != {
        "accepted_activation_record_sha256": "2a150e0b3037d01e6b311d9ab4c17157f20031f75b644a7c8778007c168b9fec",
        "accepted_activation_f061_slots_all_null": True,
        "accepted_activation_b02_b03_open": True,
        "accepted_theory_record_sha256": "335879da927b14de0f2ab0cb69b531ea51f24d9734777cb33cdf1e90fb81a491",
        "accepted_f111_validation_group_count": 128,
        "accepted_f134_natural_group_count_by_domain": {"R3-PHYS": 128, "R4-RETAIL": 128},
        "accepted_b07_closed": True,
        "historical_70_15_15_design_recharacterized_as_power_acceptance": False,
    }:
        raise ValidationError("predecessor semantic receipt drift")
    if record["package_file_roster"] != list(PACKAGE_ROSTER):
        raise ValidationError("package file roster drift")
    self_binding = record["machine_self_binding"]
    if type(self_binding) is not dict or self_binding != {
        "path": MACHINE_PATH,
        "raw_self_hash_embedded": False,
        "semantic_self_digest_field": "record_sha256",
    }:
        raise ValidationError("machine self-binding drift")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("machine semantic self-digest mismatch")


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = Path(root)
    machine_bytes = read_stable_regular(root, MACHINE_PATH)
    record = strict_json(machine_bytes, canonical_lf=True)
    _validate_machine(record)

    captured: Dict[str, bytes] = {}
    expected_predecessors = expected_predecessor_bindings()
    if record["accepted_predecessor_bindings"] != expected_predecessors:
        raise ValidationError("predecessor binding roster drift")
    for expected in expected_predecessors:
        data = read_stable_regular(root, expected["path"])
        captured[expected["path"]] = data
        if len(data) != expected["bytes"] or _sha256(data) != expected["raw_sha256"]:
            raise ValidationError("predecessor byte binding mismatch: " + expected["path"])
        if data.endswith(b"\n") is not expected["terminal_lf"]:
            raise ValidationError("predecessor LF binding mismatch: " + expected["path"])
    _validate_predecessor_semantics(captured)

    package_bindings = record["package_bindings_excluding_machine_self"]
    if type(package_bindings) is not list or len(package_bindings) != 4:
        raise ValidationError("non-machine package binding count drift")
    if [row.get("path") for row in package_bindings if type(row) is dict] != list(
        NONMACHINE_PACKAGE_ROSTER
    ):
        raise ValidationError("non-machine package binding order drift")
    for ordinal, (row, path) in enumerate(
        zip(package_bindings, NONMACHINE_PACKAGE_ROSTER)
    ):
        if type(row) is not dict:
            raise ValidationError("package binding is not a built-in object")
        data = read_stable_regular(root, path)
        expected = _binding(
            ordinal,
            path,
            data,
            {HUMAN_PATH: "human", SOURCE_PATH: "source", VALIDATOR_PATH: "validator", TEST_PATH: "test"}[path],
            "CURRENT_SUCCESSOR_PACKAGE",
        )
        if row != expected:
            raise ValidationError("package byte binding mismatch: " + path)
        captured[path] = data
    aggregate = package_aggregate_sha256(package_bindings)
    if record["package_aggregate_sha256"] != aggregate:
        raise ValidationError("package aggregate digest mismatch")
    _validate_source_surface(captured[SOURCE_PATH])
    if PROJECT_TRACKER_PATHS & set(PACKAGE_ROSTER):
        raise ValidationError("mutable tracker included in package roster")
    if PROJECT_TRACKER_PATHS & {
        row["path"] for row in package_bindings + expected_predecessors
    }:
        raise ValidationError("mutable tracker included in binding roster")
    return {
        "decision": "PASS_PROPOSAL_ONLY_F061_REMAINS_OPEN",
        "record_sha256": record["record_sha256"],
        "package_aggregate_sha256": aggregate,
        "proposal_sha256": PROPOSAL_SHA256,
        "exact_count_guard_contract_sha256": GUARD_SHA256,
        "accepted_predecessor_binding_count": len(expected_predecessors),
        "package_nonmachine_binding_count": len(package_bindings),
        "f061_closed": False,
        "power_review_present": False,
        "prior_review_receipt_created": False,
    }


PROJECT_TRACKER_PATHS = {
    "PROJECT_COMPLETION_TIMETABLE.md",
    "PROJECT_EVIDENCE_LEDGER.md",
}


def main() -> int:
    try:
        report = validate()
    except ValidationError as error:
        print(json.dumps({"decision": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
