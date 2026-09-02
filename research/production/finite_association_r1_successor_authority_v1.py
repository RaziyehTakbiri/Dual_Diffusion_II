"""Dormant parent-side validation protocol for the A1 R1 successor authority.

The module owns no active authority.  It validates supplied typed records,
constructs a future materialization plan in memory, and audits the preactivation
snapshot.  It cannot issue, mint, consume, materialize, launch, or write.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, Mapping, Sequence, Tuple

from research.production import finite_association_r1_successor_adapter_v1 as adapter
from research.production import (
    finite_association_r1_successor_contracts_v1 as contracts,
)


PREDECESSOR_HUMAN_PATH = (
    "manuscript_v3/a1_r1_registry_aware_source_execution_capsule_freeze_v1.md"
)
PREDECESSOR_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.json"
)
PREDECESSOR_MODULE_PATH = (
    "research/diagnostics/finite_association_r1_registry_aware_capsule_v1.py"
)
PREDECESSOR_TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_a1_r1_registry_aware_source_execution_capsule_freeze_v1.py"
)
PREDECESSOR_RAW_SHA256 = {
    PREDECESSOR_HUMAN_PATH: (
        "69b03c19332d4e38fdd3ba9980d338643b28df0c12adaa53d2e40f5c389e6fe1"
    ),
    PREDECESSOR_MACHINE_PATH: (
        "445d4b82b717121063b2471f2bba7abf166b4c6d6d4982e8d0d7e6555a232160"
    ),
    PREDECESSOR_MODULE_PATH: (
        "77d2330d7deb0e2b6c5f4ebdaf1db68efaae098f66b87f9f24e67feda091b338"
    ),
    PREDECESSOR_TEST_PATH: (
        "0d48d31dbe7517fde53391febc115d4a80f6c83f534e06af333e5439dee585f6"
    ),
}
PREDECESSOR_RECORD_SHA256 = (
    "7c02fcfb1d12bf36bad6cdce1c62921a238249180da32e5b5942a9f8a1219f50"
)
PREDECESSOR_REGISTRATION_DOMAIN = (
    b"heterodiff-manuscript-v3-a1-r1-registry-aware-overlay-source-registration-v1\0"
)
PREDECESSOR_SOURCE_MANIFEST_SHA256 = (
    "15b04fd7a59ffbb9fdb3cca9abf4e231fce046be3fbc19cee94d29f619f8a4d1"
)
PREDECESSOR_REGISTRY_SEMANTIC_SHA256 = (
    "33ac19d64b10571dd8aa53aad6b5219845c6505c23bf1938ff490b471c251780"
)
PREDECESSOR_MANIFEST_SHA256 = {
    "exact": "cddb2f41afac894efc70113a51e273fe228c1f862f5a486eda9f1763f3b17768",
    "primary": "74cba81f4587b55c9112a46da58b94cc73c47a65e2827d6e6ec20e7c53f23f28",
    "controls": "2f55f5561debfb978591a9d4e81f50ab0fee17eac862c45073076dc3865fc460",
    "complete_sampled": (
        "99e4320ee36c298ea3fd410bfe3d0b624df2e501837d3ad99a396eef701d0a50"
    ),
    "execution_phase_schedule": (
        "b9541b1e247d4cf025408063bdcb2462b4c9186b7e6f929efa967c9c98fe2272"
    ),
    "all_aggregate": (
        "df5b513d80bab4c9ef97c555ea8622396716ec38a7dafb2866298cb2704a73fd"
    ),
}
PREDECESSOR_PHASE_EVENT_SCHEDULE_SHA256 = (
    "488e4223c16dbbc54e4f6a438acf629fd5c0c1e8e53f262e53759295afc7cb9c"
)

CONTRACTS_PATH = "research/production/finite_association_r1_successor_contracts_v1.py"
AUTHORITY_PATH = "research/production/finite_association_r1_successor_authority_v1.py"
ADAPTER_PATH = "research/production/finite_association_r1_successor_adapter_v1.py"
HUMAN_PATH = (
    "manuscript_v3/a1_r1_successor_runtime_adapter_authority_protocol_freeze_v1.md"
)
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_successor_runtime_adapter_authority_protocol_freeze_v1.json"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_a1_r1_successor_runtime_adapter_authority_protocol_freeze_v1.py"
)
REGISTRATION_DOMAIN = (contracts.REGISTRATION_SCHEMA + "\0").encode("ascii")
PRECREATION_COMMITMENT_DOMAIN = (
    b"heterodiff-a1-r1-successor-precreation-plan-commitment-v1\0"
)
FUTURE_CUSTODY_PATH_ROSTER_DOMAIN = (
    b"heterodiff-a1-r1-successor-future-custody-path-roster-v1\0"
)
REGISTRATION_ID = "A1_R1_SUCCESSOR_RUNTIME_ADAPTER_AUTHORITY_PROTOCOL_FREEZE_V1"
FUTURE_CAPSULE_ROOT = "artifacts/a1_r1_successor_source_capsule_v1"
PRECREATION_ATTEMPT_MARKER_PATH = (
    "artifacts/a1_r1_successor_precreation_attempt_v1.json"
)
TARGET_PROFILE_ID = "M1_REFERENCE_MACOS_ARM64_PY311_SUCCESSOR_V1"
EXTERNAL_RUNTIME_MANIFEST_SCHEMA = (
    "heterodiff-a1-production-runtime-identity-manifest-v1"
)
EXTERNAL_RUNTIME_MANIFEST_TOP_LEVEL_FIELDS = (
    "accelerators",
    "approved",
    "distributions",
    "editable_install",
    "lockfile",
    "manifest_sha256",
    "modules",
    "native_libraries",
    "native_pools",
    "profile",
    "python_files",
    "schema",
)
SUCCESSOR_RUNTIME_CUSTODY_ROOT = "requirements/a1_r1_successor_runtime_admission_v1"
SUCCESSOR_RUNTIME_CUSTODY_PATHS = {
    "candidate": SUCCESSOR_RUNTIME_CUSTODY_ROOT + "/candidate-manifest.json",
    "review": SUCCESSOR_RUNTIME_CUSTODY_ROOT + "/review-report.json",
    "approval": SUCCESSOR_RUNTIME_CUSTODY_ROOT + "/approval-receipt.json",
    "manifest": SUCCESSOR_RUNTIME_CUSTODY_ROOT + "/runtime-identity.json",
}
RUNTIME_APPROVAL_LIMITATIONS = (
    "RUNTIME_APPROVAL_DOES_NOT_AUTHORIZE_RANK_TRAINING_PRODUCTION_SCIENTIFIC_"
    "EXECUTION_OR_CLAIM_PROMOTION",
    "RUNTIME_APPROVAL_IS_RESTRICTED_TO_THE_BOUND_TARGET_PROFILE_AND_SOURCE_CAPSULE",
)
RANK_ROOT = "artifacts/a1_r1_successor_rank_gate_v1"
RANK_PATHS = {
    "destination_relative_path": RANK_ROOT,
    "raw_result_relative_path": RANK_ROOT + "/result.json",
    "prepared_custody_relative_path": RANK_ROOT + "/prepared.json",
    "parent_exit_relative_path": RANK_ROOT + "/parent-exit.json",
}
D1_FORBIDDEN_EVIDENCE_SHA256 = {
    "e414fc880a04df2a868855c195666ce400ca3f975278900aaa450032b6c66e7c",
    "7c730742f38c0ad1dbfd023ee65851328f3655769ae58d23e6cdca8bbb11b885",
    "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10",
    "68434890dbd3157b70e700d6a649000dbc9ee60e297b9196af46e312beba07e6",
    "eabecf04bfe0831fa14d60126c541774aaf25c58283ebb999dc3de2403e9cada",
    "54167cf673861b93db3dd6cd354f9e08796bef59ef19b08ca4b03e59c4a62105",
}
D1_HUMAN_PATH = (
    "manuscript_v3/a1_trained_checkpoint_diagnostic_evidence_registration.md"
)
D1_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json"
)
D1_DIAGNOSTIC_PATH = (
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/diagnostic-record.json"
)
D1_ATTEMPT_PATH = (
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json"
)
D1_SUCCESS_PATH = (
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/success-receipt.json"
)
V2_SUCCESS_PATH = (
    "artifacts/manuscript_v3_a1_development_checkpoint_v2/success-receipt.json"
)
D1_QUARANTINE_ROSTER_DOMAIN = (
    b"heterodiff-a1-r1-successor-d1-execution-lineage-quarantine-roster-v1\0"
)
D1_REQUIRED_RAW_SHA256 = {
    D1_HUMAN_PATH: "bd00e6d145a5517ed8ecd34f6547c49d6d8d4eae67aeb8321037bf6ca54b3ba5",
    D1_MACHINE_PATH: "b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0",
    D1_DIAGNOSTIC_PATH: "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10",
}
FUTURE_EXECUTABLE_PREREGISTRATION_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_successor_executable_preregistration_v1.json"
)
FUTURE_EXECUTABLE_PREREGISTRATION_FREEZE_RECEIPT_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_successor_executable_preregistration_freeze_receipt_v1.json"
)
FUTURE_SUCCESSOR_ROOTS = (
    FUTURE_CAPSULE_ROOT,
    "artifacts/a1_r1_successor_authority_ledger_v1",
    "artifacts/a1_r1_successor_rank_gate_v1",
    "artifacts/a1_r1_successor_exact_campaign_v1",
    "artifacts/a1_r1_successor_sampled_campaign_v1",
    "artifacts/a1_r1_successor_primary_metrics_v1",
    "artifacts/a1_r1_successor_candidate_decision_v1",
    "artifacts/a1_r1_successor_independent_audit_v1",
    "artifacts/a1_r1_successor_publication_decision_v1",
    SUCCESSOR_RUNTIME_CUSTODY_ROOT,
)
FUTURE_CUSTODY_PATHS = tuple(
    sorted(
        {
            PRECREATION_ATTEMPT_MARKER_PATH,
            FUTURE_EXECUTABLE_PREREGISTRATION_PATH,
            FUTURE_EXECUTABLE_PREREGISTRATION_FREEZE_RECEIPT_PATH,
            *FUTURE_SUCCESSOR_ROOTS,
            *SUCCESSOR_RUNTIME_CUSTODY_PATHS.values(),
        }
    )
)

NONCLAIMS = {
    "activation_complete": False,
    "adapter_implemented": False,
    "authority_activated": False,
    "authority_event_issued": False,
    "binder_integration_complete": False,
    "candidate_decision_integration_complete": False,
    "campaign_nonce_generation_qualified": False,
    "claim_promoted": False,
    "execution_capsule_complete": False,
    "materialization_performed": False,
    "permit_issued": False,
    "plan_semantics_qualified": False,
    "phase_aggregate_admission_issued": False,
    "phase_consumption_issued": False,
    "primary_metrics_integration_complete": False,
    "precreation_marker_writer_implemented": False,
    "production_execution_authorized": False,
    "production_execution_performed": False,
    "r1_qualified": False,
    "r2_qualified": False,
    "rank_execution_authorized": False,
    "rank_execution_performed": False,
    "record_minted": False,
    "registry_integration_complete": False,
    "runtime_approval_issued": False,
    "runtime_bundle_complete": False,
    "scientific_execution_authorized": False,
    "scientific_result_eligible": False,
    "source_amendment_complete": False,
    "submission_ready": False,
    "training_execution_authorized": False,
    "training_execution_performed": False,
    "typed_consumption_qualified": False,
    "activation_semantics_qualified": False,
    "authority_ledger_implemented": False,
    "prerequisite_evidence_loaded": False,
    "replay_prevention_activated": False,
    "runtime_admitted": False,
    "sequential_transcript_validator_enabled": False,
    "source_capsule_materialized": False,
    "source_capsule_materialization_admission_qualified": False,
}

PUBLICATION_ANONYMITY_BOUNDARY = {
    "internal_registration_not_submission_artifact": True,
    "anonymous_submission_inclusion_permitted": False,
    "public_release_inclusion_permitted": False,
    "raw_milestone_artifact_paths": [
        HUMAN_PATH,
        MACHINE_PATH,
        CONTRACTS_PATH,
        AUTHORITY_PATH,
        ADAPTER_PATH,
        TEST_PATH,
    ],
    "raw_milestone_artifact_inclusion_permitted": False,
    "raw_predecessor_custody_inclusion_permitted": False,
    "source_paths_and_local_custody_metadata_internal_only": True,
    "publication_safe_derivative_required": True,
    "publication_safe_derivative_path": None,
    "publication_roster_frozen": False,
    "fresh_anonymity_audit_required": True,
}


class AuthorityProtocolError(RuntimeError):
    """Fail-closed dormant authority-protocol error."""


def _canonical_json(value: Any) -> bytes:
    return contracts.canonical_json(value)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _stat_identity(value: Any) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _ancestor_identity(value: Any) -> Tuple[int, ...]:
    """Return structural directory identity, excluding benign directory churn."""

    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_uid,
        value.st_gid,
    )


def _existing_ancestors(path: Path) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    rows = []
    for ancestor in reversed(path.absolute().parents):
        try:
            information = ancestor.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
            raise AuthorityProtocolError("custody path has a symlink ancestor")
        rows.append((str(ancestor), _ancestor_identity(information)))
    return tuple(rows)


def _read_stable_file(path: Path) -> Tuple[bytes, Any]:
    ancestors_before = _existing_ancestors(path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise AuthorityProtocolError("custody input is not a regular nonsymlink file")
    payload = path.read_bytes()
    after = path.lstat()
    if ancestors_before != _existing_ancestors(path):
        raise AuthorityProtocolError("custody ancestors changed during read")
    if _stat_identity(before) != _stat_identity(after) or len(payload) != after.st_size:
        raise AuthorityProtocolError("custody input changed during read")
    return payload, after


def _require_absent(path: Path) -> None:
    before = _existing_ancestors(path)
    try:
        path.lstat()
    except FileNotFoundError:
        if before != _existing_ancestors(path):
            raise AuthorityProtocolError("absence-gate ancestors changed")
        return
    raise AuthorityProtocolError("required-absent path has an entry")


def _load_canonical_json(path: Path) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(path)
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuthorityProtocolError("custody JSON is not ASCII JSON") from error
    if type(record) is not dict or payload != _canonical_json(record) + b"\n":
        raise AuthorityProtocolError("custody JSON is not canonical and LF-terminated")
    return payload, record


def _predecessor_record(root: Path) -> Dict[str, Any]:
    for relative_path, expected in PREDECESSOR_RAW_SHA256.items():
        payload, _ = _read_stable_file(root / relative_path)
        if _sha256(payload) != expected:
            raise AuthorityProtocolError("predecessor exact bytes changed")
    payload, record = _load_canonical_json(root / PREDECESSOR_MACHINE_PATH)
    if _sha256(payload) != PREDECESSOR_RAW_SHA256[PREDECESSOR_MACHINE_PATH]:
        raise AuthorityProtocolError("predecessor machine raw identity changed")
    body = dict(record)
    if body.get("record_sha256") != PREDECESSOR_RECORD_SHA256:
        raise AuthorityProtocolError("predecessor machine self identity changed")
    body["record_sha256"] = None
    if (
        _sha256(PREDECESSOR_REGISTRATION_DOMAIN + _canonical_json(body))
        != PREDECESSOR_RECORD_SHA256
    ):
        raise AuthorityProtocolError("predecessor machine self digest is invalid")
    return record


def _apply_frozen_overlay(payload: bytes, rule: Mapping[str, Any]) -> bytes:
    prefix = rule["assignment_prefix_utf8"].encode("ascii")
    old = rule["old_literal_utf8"].encode("ascii")
    new = rule["new_literal_utf8"].encode("ascii")
    if payload.count(prefix) != rule["required_assignment_occurrences"]:
        raise AuthorityProtocolError("overlay assignment occurrence count changed")
    start = payload.find(prefix) + len(prefix)
    if start < len(prefix) or payload[start : start + len(old)] != old:
        raise AuthorityProtocolError("overlay literal moved from its frozen position")
    virtual = payload[:start] + new + payload[start + len(old) :]
    if virtual.count(prefix + new) != rule["required_literal_replacements"]:
        raise AuthorityProtocolError("overlay replacement count changed")
    if (
        virtual[:start] != payload[:start]
        or virtual[start + len(new) :] != payload[start + len(old) :]
    ):
        raise AuthorityProtocolError("overlay changed bytes outside its one literal")
    return virtual


def _module_level_tuple(
    payload: bytes, constant_name: str, path: str
) -> Tuple[int, ...]:
    tree = ast.parse(payload, filename=path)
    matches = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(
            isinstance(target, ast.Name) and target.id == constant_name
            for target in targets
        ):
            try:
                matches.append(ast.literal_eval(node.value))
            except (TypeError, ValueError) as error:
                raise AuthorityProtocolError(
                    "overlaid seed assignment is not literal"
                ) from error
    if (
        len(matches) != 1
        or type(matches[0]) is not tuple
        or any(type(value) is not int for value in matches[0])
    ):
        raise AuthorityProtocolError(
            "overlaid seed assignment is not one integer tuple"
        )
    return matches[0]


def _verify_registry_custody(root: Path, source: Mapping[str, Any]) -> Tuple[int, ...]:
    registry = source["registry_semantics"]
    payload, _ = _read_stable_file(root / registry["path"])
    if len(payload) == 0 or _sha256(payload) != registry["raw_sha256"]:
        raise AuthorityProtocolError("replacement registry raw custody changed")
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuthorityProtocolError(
            "replacement registry is not ASCII JSON"
        ) from error
    if type(record) is not dict:
        raise AuthorityProtocolError("replacement registry is not a JSON object")
    claimed = record.get("record_sha256")
    body = dict(record)
    body["record_sha256"] = None
    if (
        claimed != registry["record_sha256"]
        or _sha256(
            b"heterodiff-r1-a1-replacement-seed-registry-v1\0" + _canonical_json(body)
        )
        != claimed
    ):
        raise AuthorityProtocolError("replacement registry self digest changed")
    values = record.get("replacement_seed_registry")
    expected = (4052249444591756, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
    if (
        type(values) is not list
        or tuple(values) != expected
        or any(
            type(value) is not int or value < 0 or value >= 2**53 for value in values
        )
        or len(set(values)) != 8
        or record.get("replacement_ordinal") != 0
        or type(record.get("replacement_ordinal")) is not int
        or record.get("replacement_seed") != expected[0]
        or type(record.get("replacement_seed")) is not int
        or record.get("exposed_seed") != 1729
        or record.get("r1_execution_authorized") is not False
    ):
        raise AuthorityProtocolError("replacement registry semantics changed")
    return expected


def _verify_coordinate_custody(
    coordinates: Mapping[str, Any], registry: Tuple[int, ...]
) -> None:
    if (
        coordinates.get("registry") != list(registry)
        or coordinates.get("registry_length") != 8
        or type(coordinates.get("registry_length")) is not int
        or coordinates.get("registry_unique") is not True
        or coordinates.get("replacement_ordinal") != 0
        or type(coordinates.get("replacement_ordinal")) is not int
        or coordinates.get("exposed_seed") != 1729
        or _sha256(
            b"heterodiff-r1-registry-aware-seed-registry-v1\0"
            + _canonical_json(list(registry))
        )
        != coordinates.get("registry_sha256")
    ):
        raise AuthorityProtocolError("coordinate registry custody changed")
    manifests = coordinates.get("manifests")
    expected_counts = {
        "exact": 24,
        "primary": 48,
        "controls": 72,
        "complete_sampled": 120,
        "execution_phase_schedule": 144,
        "all_aggregate": 144,
    }
    if type(manifests) is not dict or set(manifests) != set(expected_counts):
        raise AuthorityProtocolError("coordinate manifest inventory changed")
    prefix = bytes.fromhex(
        coordinates["coordinate_manifest_digest_domain_encoding"]["exact_prefix_hex"]
    )
    normalized = {}
    for key, expected_count in expected_counts.items():
        manifest = manifests[key]
        body = dict(manifest)
        claimed = body.pop("manifest_sha256")
        rows = body.get("coordinates")
        projections = body.get("underlying_request_projections")
        if (
            claimed != PREDECESSOR_MANIFEST_SHA256[key]
            or _sha256(prefix + _canonical_json(body)) != claimed
            or body.get("coordinate_count") != expected_count
            or type(body.get("coordinate_count")) is not int
            or type(rows) is not list
            or type(projections) is not list
            or len(rows) != expected_count
            or len(projections) != expected_count
        ):
            raise AuthorityProtocolError("coordinate manifest custody changed")
        normalized_rows = []
        for ordinal, (row, projection) in enumerate(zip(rows, projections)):
            seed_ordinal = row.get("seed_ordinal") if type(row) is dict else None
            if (
                type(row) is not dict
                or row.get("manifest_ordinal") != ordinal
                or type(row.get("manifest_ordinal")) is not int
                or type(seed_ordinal) is not int
                or seed_ordinal < 0
                or seed_ordinal >= len(registry)
                or row.get("seed") != registry[seed_ordinal]
                or row.get("seed") == 1729
                or type(row.get("phase_coordinate_ordinal")) is not int
            ):
                raise AuthorityProtocolError("coordinate order or seed custody changed")
            stripped = dict(row)
            stripped.pop("manifest_ordinal")
            stripped.pop("manifest_ordinal_domain")
            expected_projection = (
                [stripped["seed"], stripped["method"]]
                if stripped["phase"] == "EXACT"
                else [
                    stripped["seed"],
                    stripped["accepted_example_budget"],
                    stripped["method"],
                ]
            )
            if projection != expected_projection:
                raise AuthorityProtocolError("coordinate request projection changed")
            normalized_rows.append(stripped)
        normalized[key] = normalized_rows
    exact_expected = [
        {
            "phase": "EXACT",
            "phase_coordinate_ordinal": seed_ordinal * 3 + method_ordinal,
            "seed_ordinal": seed_ordinal,
            "coordinate_tag": "EXACT_SEED_METHOD",
            "seed": seed,
            "accepted_example_budget": None,
            "method": method,
        }
        for seed_ordinal, seed in enumerate(registry)
        for method_ordinal, method in enumerate(("direct", "guided", "strong_direct"))
    ]
    primary_expected = [
        {
            "phase": "PRIMARY",
            "phase_coordinate_ordinal": seed_ordinal * 6
            + budget_ordinal * 2
            + method_ordinal,
            "seed_ordinal": seed_ordinal,
            "coordinate_tag": "SAMPLED_SEED_BUDGET_METHOD",
            "seed": seed,
            "accepted_example_budget": budget,
            "method": method,
        }
        for seed_ordinal, seed in enumerate(registry)
        for budget_ordinal, budget in enumerate((512, 4096, 32768))
        for method_ordinal, method in enumerate(("direct", "guided"))
    ]
    controls_expected = [
        {
            "phase": "CONTROLS",
            "phase_coordinate_ordinal": seed_ordinal * 9
            + budget_ordinal * 3
            + method_ordinal,
            "seed_ordinal": seed_ordinal,
            "coordinate_tag": "SAMPLED_SEED_BUDGET_METHOD",
            "seed": seed,
            "accepted_example_budget": budget,
            "method": method,
        }
        for seed_ordinal, seed in enumerate(registry)
        for budget_ordinal, budget in enumerate((512, 4096, 32768))
        for method_ordinal, method in enumerate(
            ("strong_direct", "guide_input", "mismatch")
        )
    ]
    complete_expected = []
    primary_by_key = {
        (row["seed"], row["accepted_example_budget"], row["method"]): row
        for row in primary_expected
    }
    controls_by_key = {
        (row["seed"], row["accepted_example_budget"], row["method"]): row
        for row in controls_expected
    }
    for seed in registry:
        for budget in (512, 4096, 32768):
            for method in (
                "direct",
                "guided",
                "strong_direct",
                "guide_input",
                "mismatch",
            ):
                source = (
                    primary_by_key
                    if method in {"direct", "guided"}
                    else controls_by_key
                )
                complete_expected.append(dict(source[(seed, budget, method)]))
    if (
        normalized["exact"] != exact_expected
        or normalized["primary"] != primary_expected
        or normalized["controls"] != controls_expected
        or normalized["complete_sampled"] != complete_expected
    ):
        raise AuthorityProtocolError(
            "coordinate domain, ordinal, or method order changed"
        )
    if (
        normalized["execution_phase_schedule"]
        != normalized["exact"] + normalized["primary"] + normalized["controls"]
        or normalized["all_aggregate"]
        != normalized["exact"] + normalized["complete_sampled"]
    ):
        raise AuthorityProtocolError("phase schedule and aggregate order changed")
    event = coordinates.get("phase_event_schedule")
    if type(event) is not dict:
        raise AuthorityProtocolError("phase-event schedule is missing")
    event_body = dict(event)
    event_claimed = event_body.pop("schedule_sha256")
    if (
        event_claimed != PREDECESSOR_PHASE_EVENT_SCHEDULE_SHA256
        or _sha256(
            b"heterodiff-r1-registry-aware-phase-event-schedule-v1\0"
            + _canonical_json(event_body)
        )
        != event_claimed
        or event.get("event_order")
        != ["RANK", "EXACT", "PRIMARY", "PRIMARY_METRICS", "CONTROLS"]
        or event.get("issues_authority") is not False
    ):
        raise AuthorityProtocolError("phase-event schedule custody changed")


def _verify_live_predecessor_custody(
    root: Path, snapshot: Mapping[str, Any]
) -> Dict[str, Any]:
    source = snapshot["source_manifest"]
    manifest_body = dict(source)
    manifest_claimed = manifest_body.pop("manifest_sha256")
    if (
        manifest_claimed != PREDECESSOR_SOURCE_MANIFEST_SHA256
        or _sha256(
            b"heterodiff-r1-registry-aware-preactivation-overlay-source-manifest-v1\0"
            + _canonical_json(manifest_body)
        )
        != manifest_claimed
    ):
        raise AuthorityProtocolError("predecessor source manifest self digest changed")
    registry = _verify_registry_custody(root, source)
    overlay_rows = snapshot.get("overlay_rules")
    if type(overlay_rows) is not list or len(overlay_rows) != 5:
        raise AuthorityProtocolError("overlay rule inventory changed")
    rules = {}
    for row in overlay_rows:
        rule = row.get("rule") if type(row) is dict else None
        if type(rule) is not dict or set(row) != {"rule", "rule_sha256"}:
            raise AuthorityProtocolError("overlay rule row changed")
        rule_sha256 = _sha256(
            b"heterodiff-r1-registry-aware-overlay-rule-v1\0" + _canonical_json(rule)
        )
        if row["rule_sha256"] != rule_sha256 or rule["path"] in rules:
            raise AuthorityProtocolError("overlay rule digest or path changed")
        rules[rule["path"]] = rule
    source_rows = source.get("rows")
    if type(source_rows) is not list or len(source_rows) != 45:
        raise AuthorityProtocolError("base source roster changed")
    for ordinal, row in enumerate(source_rows):
        if type(row) is not dict or row.get("ordinal") != ordinal:
            raise AuthorityProtocolError("base source ordinal changed")
        payload, _ = _read_stable_file(root / row["path"])
        if _sha256(payload) != row["base_raw_sha256"]:
            raise AuthorityProtocolError("base source bytes changed")
        rule = rules.get(row["path"])
        virtual = payload if rule is None else _apply_frozen_overlay(payload, rule)
        expected_kind = "UNCHANGED_BASE" if rule is None else "ONE_LITERAL_OVERLAY"
        if (
            row["source_kind"] != expected_kind
            or len(virtual) != row["bytes"]
            or _sha256(virtual) != row["virtual_raw_sha256"]
            or row["execution_admissible"] is not False
        ):
            raise AuthorityProtocolError("virtual source identity changed")
        if rule is not None:
            if _module_level_tuple(
                virtual, rule["constant_name"], row["path"]
            ) != registry or 1729 in _module_level_tuple(
                virtual, rule["constant_name"], row["path"]
            ):
                raise AuthorityProtocolError(
                    "overlay seed tuple changed or replays 1729"
                )
    for roster_key in (
        ("deferred_runtime_boundary", "deferred_source_rows", 2),
        (None, "nonpackage_candidate_inputs", 3),
    ):
        parent_key, rows_key, expected_count = roster_key
        rows = source[parent_key][rows_key] if parent_key else source[rows_key]
        if type(rows) is not list or len(rows) != expected_count:
            raise AuthorityProtocolError("frozen source-input roster changed")
        for ordinal, row in enumerate(rows):
            payload, information = _read_stable_file(root / row["path"])
            if (
                row["ordinal"] != ordinal
                or type(row["ordinal"]) is not int
                or len(payload) != row["bytes"]
                or _sha256(payload) != row["raw_sha256"]
                or format(stat.S_IMODE(information.st_mode), "04o") != row["mode_octal"]
                or row["execution_admissible"] is not False
            ):
                raise AuthorityProtocolError("frozen source-input custody changed")
    governance = snapshot["rosters"]["governance_custody"]
    if type(governance) is not list or len(governance) != 24:
        raise AuthorityProtocolError("governance custody roster changed")
    for ordinal, row in enumerate(governance):
        payload, information = _read_stable_file(root / row["path"])
        if (
            row["ordinal"] != ordinal
            or type(row["ordinal"]) is not int
            or len(payload) != row["bytes"]
            or _sha256(payload) != row["raw_sha256"]
            or format(stat.S_IMODE(information.st_mode), "04o") != row["mode_octal"]
            or row["execution_admissible"] is not False
        ):
            raise AuthorityProtocolError("governance custody bytes changed")
    _verify_coordinate_custody(snapshot["coordinate_manifests"], registry)
    body = {
        "base_source_count": 45,
        "overlay_count": 5,
        "deferred_runtime_source_count": 2,
        "nonpackage_input_count": 3,
        "governance_custody_count": 24,
        "source_manifest_sha256": manifest_claimed,
        "registry_raw_sha256": source["registry_semantics"]["raw_sha256"],
        "registry_record_sha256": source["registry_semantics"]["record_sha256"],
        "registry_semantic_sha256": snapshot["coordinate_manifests"]["registry_sha256"],
        "all_live_custody_reopened": True,
        "all_execution_admissible": False,
    }
    return {
        **body,
        "live_custody_sha256": _sha256(
            b"heterodiff-a1-r1-successor-live-predecessor-custody-v1\0"
            + _canonical_json(body)
        ),
    }


def frozen_precreation_snapshot(workspace_root: Any) -> Dict[str, Any]:
    """Reopen the predecessor bytes and all of its current absence gates."""

    root = Path(workspace_root).absolute()
    if root.resolve(strict=True) != root:
        raise AuthorityProtocolError("workspace root is not canonical")
    predecessor = _predecessor_record(root)
    snapshot = predecessor.get("qualification_snapshot")
    if type(snapshot) is not dict:
        raise AuthorityProtocolError("predecessor qualification snapshot is missing")
    source = snapshot.get("source_manifest")
    coordinates = snapshot.get("coordinate_manifests")
    if (
        type(source) is not dict
        or source.get("manifest_sha256") != PREDECESSOR_SOURCE_MANIFEST_SHA256
        or type(coordinates) is not dict
        or coordinates.get("registry_sha256") != PREDECESSOR_REGISTRY_SEMANTIC_SHA256
    ):
        raise AuthorityProtocolError("predecessor source or registry identity changed")
    manifests = coordinates.get("manifests")
    if type(manifests) is not dict:
        raise AuthorityProtocolError("predecessor coordinate manifests are missing")
    for key, expected in PREDECESSOR_MANIFEST_SHA256.items():
        if (
            type(manifests.get(key)) is not dict
            or manifests[key].get("manifest_sha256") != expected
        ):
            raise AuthorityProtocolError("predecessor coordinate identity changed")
    if (
        coordinates.get("phase_event_schedule", {}).get("schedule_sha256")
        != PREDECESSOR_PHASE_EVENT_SCHEDULE_SHA256
    ):
        raise AuthorityProtocolError("predecessor event schedule changed")
    live_custody = _verify_live_predecessor_custody(root, snapshot)

    absence_paths = []
    absence_paths.extend(snapshot["planned_output_boundary"]["planned_output_roots"])
    absence_paths.extend(snapshot["legacy_production_roots"]["paths"])
    absence_paths.append(snapshot["source_target_state"]["planned_adapter_target_path"])
    for row in snapshot["rosters"]["runtime_inputs"]:
        if row.get("present") is False:
            absence_paths.append(row["path"])
    if len(absence_paths) != 28 or len(set(absence_paths)) != 28:
        raise AuthorityProtocolError("predecessor absence-gate inventory changed")
    for relative_path in absence_paths:
        _require_absent(root / relative_path)
    body = {
        "predecessor_human_raw_sha256": PREDECESSOR_RAW_SHA256[PREDECESSOR_HUMAN_PATH],
        "predecessor_machine_raw_sha256": PREDECESSOR_RAW_SHA256[
            PREDECESSOR_MACHINE_PATH
        ],
        "predecessor_machine_record_sha256": PREDECESSOR_RECORD_SHA256,
        "predecessor_module_raw_sha256": PREDECESSOR_RAW_SHA256[
            PREDECESSOR_MODULE_PATH
        ],
        "predecessor_test_raw_sha256": PREDECESSOR_RAW_SHA256[PREDECESSOR_TEST_PATH],
        "qualification_snapshot": snapshot,
        "live_custody_verification": live_custody,
        "absence_paths": sorted(absence_paths),
        "absence_path_count": 28,
        "all_absence_gates_lstat_absent": True,
        "captured_before_any_successor_path_creation": True,
    }
    return {
        **body,
        "snapshot_sha256": _sha256(
            b"heterodiff-a1-r1-successor-precreation-snapshot-v1\0"
            + _canonical_json(body)
        ),
    }


def _api_signature(
    root: Path, relative_path: str, module: str, qualname: str
) -> Dict[str, Any]:
    payload, _ = _read_stable_file(root / relative_path)
    tree = ast.parse(payload, filename=relative_path)
    current = list(tree.body)
    definition = None
    for part in qualname.split("."):
        matches = [
            node
            for node in current
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == part
        ]
        if len(matches) != 1:
            raise AuthorityProtocolError("API qualname is not exact")
        definition = matches[0]
        current = list(definition.body) if isinstance(definition, ast.ClassDef) else []
    if not isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise AuthorityProtocolError("API binding is not a function")
    arguments = definition.args

    def argument_row(value: ast.arg) -> Dict[str, Any]:
        return {
            "name": value.arg,
            "annotation_ast": (
                None
                if value.annotation is None
                else ast.dump(value.annotation, include_attributes=False)
            ),
        }

    body = {
        "module": module,
        "qualname": qualname,
        "definition_kind": type(definition).__name__,
        "positional_only": [argument_row(value) for value in arguments.posonlyargs],
        "positional_or_keyword": [argument_row(value) for value in arguments.args],
        "keyword_only": [argument_row(value) for value in arguments.kwonlyargs],
        "vararg": None if arguments.vararg is None else argument_row(arguments.vararg),
        "kwarg": None if arguments.kwarg is None else argument_row(arguments.kwarg),
        "positional_default_count": len(arguments.defaults),
        "keyword_default_presence": [
            value is not None for value in arguments.kw_defaults
        ],
        "return_annotation_ast": (
            None
            if definition.returns is None
            else ast.dump(definition.returns, include_attributes=False)
        ),
    }
    return {
        **body,
        "signature_sha256": _sha256(
            b"heterodiff-r1-registry-aware-api-signature-v1\0" + _canonical_json(body)
        ),
    }


def _extra_api_inventory(root: Path, predecessor: Mapping[str, Any]) -> Dict[str, Any]:
    source_manifest = predecessor["qualification_snapshot"]["source_manifest"]
    rows = list(source_manifest["rows"])
    rows.extend(source_manifest["deferred_runtime_boundary"]["deferred_source_rows"])
    by_path = {row["path"]: row for row in rows}
    sampled_path = "src/heterodiff/experiments/finite_association_isolated_runner.py"
    metrics_path = "src/heterodiff/experiments/finite_association_primary_metrics.py"
    sampled_module = "heterodiff.experiments.finite_association_isolated_runner"
    metrics_module = "heterodiff.experiments.finite_association_primary_metrics"
    definitions = (
        (
            "SAMPLED_MEMBER_LOADER",
            sampled_path,
            sampled_module,
            "load_successful_frozen_association_checkpoint",
        ),
        (
            "SAMPLED_MEMBER_REVALIDATOR",
            sampled_path,
            sampled_module,
            "revalidate_successful_frozen_association_checkpoint",
        ),
        (
            "PRIMARY_METRICS_COMPUTE",
            metrics_path,
            metrics_module,
            "compute_and_commit_frozen_association_primary_metrics",
        ),
        (
            "PRIMARY_METRICS_LOADER",
            metrics_path,
            metrics_module,
            "load_committed_frozen_association_primary_metrics",
        ),
        (
            "PRIMARY_METRICS_REVALIDATOR",
            metrics_path,
            metrics_module,
            "revalidate_committed_frozen_association_primary_metrics",
        ),
        (
            "EXTERNAL_RUNTIME_IDENTITY_LOADER",
            "src/heterodiff/experiments/finite_association_runtime_identity.py",
            "heterodiff.experiments.finite_association_runtime_identity",
            "load_runtime_identity_manifest",
        ),
        (
            "EXTERNAL_RUNTIME_CAPTURE_VALIDATOR",
            "src/heterodiff/experiments/finite_association_runtime_identity_capture.py",
            "heterodiff.experiments.finite_association_runtime_identity_capture",
            "validate_capture_envelope",
        ),
    )
    result = {}
    for role, path, module, qualname in definitions:
        result[role] = {
            "module": module,
            "qualname": qualname,
            "source_sha256": (
                by_path[path]["virtual_raw_sha256"]
                if "virtual_raw_sha256" in by_path[path]
                else by_path[path]["raw_sha256"]
            ),
            "api_signature": _api_signature(root, path, module, qualname),
        }
    return result


def _file_sha256(root: Path, relative_path: str) -> str:
    payload, _ = _read_stable_file(root / relative_path)
    return _sha256(payload)


def planned_source_capsule_manifest(
    workspace_root: Any, precreation: Mapping[str, Any]
) -> Dict[str, Any]:
    """Build the in-memory 50-row future capsule identity; write nothing."""

    root = Path(workspace_root).absolute()
    snapshot = precreation["qualification_snapshot"]
    source = snapshot["source_manifest"]
    rows = []
    for source_row in source["rows"]:
        rows.append(
            {
                "ordinal": len(rows),
                "source_role": source_row["source_kind"],
                "source_path": source_row["path"],
                "capsule_relative_path": source_row["path"],
                "raw_sha256": source_row["virtual_raw_sha256"],
                "bytes": source_row["bytes"],
                "execution_admissible": False,
            }
        )
    for runtime_row in source["deferred_runtime_boundary"]["deferred_source_rows"]:
        rows.append(
            {
                "ordinal": len(rows),
                "source_role": runtime_row["role"],
                "source_path": runtime_row["path"],
                "capsule_relative_path": runtime_row["path"],
                "raw_sha256": runtime_row["raw_sha256"],
                "bytes": runtime_row["bytes"],
                "execution_admissible": False,
            }
        )
    for input_row in source["nonpackage_candidate_inputs"]:
        rows.append(
            {
                "ordinal": len(rows),
                "source_role": input_row["role"],
                "source_path": input_row["path"],
                "capsule_relative_path": "inputs/" + input_row["path"],
                "raw_sha256": input_row["raw_sha256"],
                "bytes": input_row["bytes"],
                "execution_admissible": False,
            }
        )
    if len(rows) != 50:
        raise AuthorityProtocolError("planned source capsule is not exactly 50 rows")
    bootstrap_spec_payload = _canonical_json(adapter.frozen_bootstrap_spec()) + b"\n"
    record = {
        "schema": contracts.SOURCE_CAPSULE_MANIFEST_SCHEMA,
        "capsule_root_relative_path": FUTURE_CAPSULE_ROOT,
        "source_manifest_sha256": source["manifest_sha256"],
        "registry_semantic_sha256": snapshot["coordinate_manifests"]["registry_sha256"],
        "base_module_count": 45,
        "deferred_runtime_source_count": 2,
        "nonpackage_input_count": 3,
        "rows": rows,
        "adapter_copy_relative_path": adapter.FUTURE_CAPSULE_ADAPTER_COPY_PATH,
        "contracts_copy_relative_path": adapter.FUTURE_CAPSULE_CONTRACTS_COPY_PATH,
        "bootstrap_spec_copy_relative_path": (
            adapter.FUTURE_CAPSULE_BOOTSTRAP_SPEC_COPY_PATH
        ),
        "adapter_sha256": _file_sha256(root, ADAPTER_PATH),
        "contracts_sha256": _file_sha256(root, CONTRACTS_PATH),
        "bootstrap_spec_raw_sha256": _sha256(bootstrap_spec_payload),
        "capsule_src_excludes_adapter_protocol": True,
        "capsule_manifest_sha256": None,
    }
    record["capsule_manifest_sha256"] = _sha256(
        contracts.SOURCE_CAPSULE_MANIFEST_SCHEMA.encode("ascii")
        + b"\0"
        + _canonical_json(record)
    )
    return contracts.MaterializedSourceCapsuleManifestV1.parse(
        _canonical_json(record) + b"\n"
    ).to_record()


def _roster_digest(label: str, rows: Sequence[Mapping[str, Any]]) -> str:
    return _sha256(
        ("heterodiff-a1-r1-successor-" + label + "-roster-v1\0").encode("ascii")
        + _canonical_json(list(rows))
    )


def _capsule_tree_snapshot(
    capsule_root: Path,
) -> Tuple[
    Tuple[Tuple[str, Tuple[int, ...]], ...],
    Tuple[Tuple[str, Tuple[int, ...]], ...],
]:
    root_information = capsule_root.lstat()
    if (
        stat.S_ISLNK(root_information.st_mode)
        or not stat.S_ISDIR(root_information.st_mode)
        or stat.S_IMODE(root_information.st_mode) != 0o700
    ):
        raise AuthorityProtocolError(
            "materialized capsule root is not a 0700 directory"
        )
    result = []
    directory_identities = [("", _stat_identity(root_information))]
    stack = [capsule_root]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as entries:
            children = sorted(entries, key=lambda value: value.name)
        for entry in children:
            path = Path(entry.path)
            information = path.lstat()
            relative = path.relative_to(capsule_root).as_posix()
            if stat.S_ISLNK(information.st_mode):
                raise AuthorityProtocolError("materialized capsule contains a symlink")
            if stat.S_ISDIR(information.st_mode):
                if stat.S_IMODE(information.st_mode) != 0o700:
                    raise AuthorityProtocolError(
                        "materialized capsule directory mode changed"
                    )
                stack.append(path)
                directory_identities.append((relative, _stat_identity(information)))
            elif stat.S_ISREG(information.st_mode):
                if (
                    stat.S_IMODE(information.st_mode) != 0o600
                    or information.st_nlink != 1
                ):
                    raise AuthorityProtocolError(
                        "materialized capsule file mode or link count changed"
                    )
                if relative.endswith(".pyc") or "/__pycache__/" in "/" + relative:
                    raise AuthorityProtocolError(
                        "materialized capsule contains bytecode"
                    )
                result.append((relative, _stat_identity(information)))
            else:
                raise AuthorityProtocolError(
                    "materialized capsule contains a non-file entry"
                )
    return tuple(sorted(result)), tuple(sorted(directory_identities))


def _required_capsule_directories(paths: Sequence[str]) -> Tuple[str, ...]:
    result = {""}
    for relative_path in paths:
        parts = relative_path.split("/")[:-1]
        for stop in range(1, len(parts) + 1):
            result.add("/".join(parts[:stop]))
    return tuple(sorted(result))


def _load_source_capsule_admission_from_snapshot(
    root: Path, qualification_snapshot: Mapping[str, Any]
) -> contracts.SourceCapsuleAdmissionV1:
    """Live-open a future capsule; current absent state necessarily refuses."""

    planned = qualification_snapshot["planned_source_capsule_manifest"]
    capsule_root = root / FUTURE_CAPSULE_ROOT
    expected_rows = []
    for row in planned["rows"]:
        expected_rows.append(
            {
                "path": row["capsule_relative_path"],
                "bytes": row["bytes"],
                "raw_sha256": row["raw_sha256"],
                "roster": (
                    "NONPACKAGE_INPUT"
                    if row["source_role"]
                    in {"PYPROJECT", "ENVIRONMENT_LOCK", "A1_SPECIFICATION_62"}
                    else "LOCAL_PACKAGE_SOURCE"
                ),
            }
        )
    implementation = qualification_snapshot["implementation"]
    protocol_payloads = {
        planned["contracts_copy_relative_path"]: _read_stable_file(
            root / CONTRACTS_PATH
        )[0],
        planned["adapter_copy_relative_path"]: _read_stable_file(root / ADAPTER_PATH)[
            0
        ],
        planned["bootstrap_spec_copy_relative_path"]: (
            _canonical_json(adapter.frozen_bootstrap_spec()) + b"\n"
        ),
    }
    expected_protocol_hashes = {
        planned["contracts_copy_relative_path"]: implementation["contracts_sha256"],
        planned["adapter_copy_relative_path"]: implementation["adapter_sha256"],
        planned["bootstrap_spec_copy_relative_path"]: planned[
            "bootstrap_spec_raw_sha256"
        ],
    }
    for relative_path, source_payload in protocol_payloads.items():
        sha256 = expected_protocol_hashes[relative_path]
        if _sha256(source_payload) != sha256:
            raise AuthorityProtocolError("protocol source changed before capsule load")
        expected_rows.append(
            {
                "path": relative_path,
                "bytes": len(source_payload),
                "raw_sha256": sha256,
                "roster": "PROTOCOL_COPY",
            }
        )
    if (
        len(expected_rows) != 53
        or sum(row["roster"] == "LOCAL_PACKAGE_SOURCE" for row in expected_rows) != 47
        or sum(row["roster"] == "NONPACKAGE_INPUT" for row in expected_rows) != 3
        or sum(row["roster"] == "PROTOCOL_COPY" for row in expected_rows) != 3
    ):
        raise AuthorityProtocolError("materialized capsule roster cardinality changed")
    expected_paths = tuple(sorted(row["path"] for row in expected_rows))
    expected_directories = _required_capsule_directories(expected_paths)
    if len(set(expected_paths)) != 53:
        raise AuthorityProtocolError("materialized capsule paths are not unique")
    before_tree = _capsule_tree_snapshot(capsule_root)
    if (
        tuple(row[0] for row in before_tree[0]) != expected_paths
        or tuple(row[0] for row in before_tree[1]) != expected_directories
    ):
        raise AuthorityProtocolError(
            "materialized capsule has missing or extra entries"
        )
    for row in expected_rows:
        payload, information = _read_stable_file(capsule_root / row["path"])
        if (
            len(payload) != row["bytes"]
            or _sha256(payload) != row["raw_sha256"]
            or stat.S_IMODE(information.st_mode) != 0o600
            or information.st_nlink != 1
        ):
            raise AuthorityProtocolError("materialized capsule row custody changed")
    after_tree = _capsule_tree_snapshot(capsule_root)
    if (
        after_tree != before_tree
        or tuple(row[0] for row in after_tree[0]) != expected_paths
        or tuple(row[0] for row in after_tree[1]) != expected_directories
    ):
        raise AuthorityProtocolError("materialized capsule tree changed during audit")
    local = [row for row in expected_rows if row["roster"] == "LOCAL_PACKAGE_SOURCE"]
    nonpackage = [row for row in expected_rows if row["roster"] == "NONPACKAGE_INPUT"]
    protocol = [row for row in expected_rows if row["roster"] == "PROTOCOL_COPY"]
    source_manifest = qualification_snapshot["precreation_snapshot"][
        "qualification_snapshot"
    ]["source_manifest"]
    overlay_roster_sha256 = _sha256(
        b"heterodiff-a1-r1-successor-overlay-rule-roster-v1\0"
        + _canonical_json(
            qualification_snapshot["precreation_snapshot"]["qualification_snapshot"][
                "overlay_rules"
            ]
        )
    )
    root_identity_body = {
        "capsule_root_relative_path": FUTURE_CAPSULE_ROOT,
        "materialized_capsule_manifest_sha256": planned["capsule_manifest_sha256"],
        "ordered_file_paths": list(expected_paths),
        "ordered_file_sha256s": [
            next(row["raw_sha256"] for row in expected_rows if row["path"] == path)
            for path in expected_paths
        ],
    }
    record = {
        "schema": contracts.SOURCE_CAPSULE_ADMISSION_SCHEMA,
        "authority_domain": contracts.AUTHORITY_DOMAIN,
        "predecessor_qualification_snapshot_sha256": qualification_snapshot[
            "precreation_snapshot"
        ]["snapshot_sha256"],
        "preactivation_source_manifest_sha256": source_manifest["manifest_sha256"],
        "materialized_capsule_manifest_sha256": planned["capsule_manifest_sha256"],
        "canonical_capsule_root_identity_sha256": _sha256(
            b"heterodiff-a1-r1-successor-canonical-capsule-root-v1\0"
            + _canonical_json(root_identity_body)
        ),
        "local_package_source_count": 47,
        "local_package_source_roster_sha256": _roster_digest(
            "local-package-source", local
        ),
        "nonpackage_input_count": 3,
        "nonpackage_input_roster_sha256": _roster_digest(
            "nonpackage-input", nonpackage
        ),
        "protocol_copy_count": 3,
        "protocol_copy_roster_sha256": _roster_digest("protocol-copy", protocol),
        "overlay_rule_count": 5,
        "overlay_rule_roster_sha256": overlay_roster_sha256,
        "registry_semantic_sha256": qualification_snapshot["precreation_snapshot"][
            "qualification_snapshot"
        ]["coordinate_manifests"]["registry_sha256"],
        "all_live_rows_verified": True,
        "regular_files_only": True,
        "no_symlinks": True,
        "no_hardlinks": True,
        "no_extra_files": True,
        "no_pyc": True,
        "planned_workspace_src_adapter_absent": True,
        "dynamic_local_edge_count": 6,
        "dynamic_local_edges_satisfied": True,
        "external_numerical_modules_deferred_to_runtime": True,
        "admission_sha256": None,
    }
    _require_absent(root / adapter.PERMANENTLY_ABSENT_LEGACY_PLANNED_SRC_TARGET)
    record["admission_sha256"] = _sha256(
        contracts.SOURCE_CAPSULE_ADMISSION_SCHEMA.encode("ascii")
        + b"\0"
        + _canonical_json(record)
    )
    return contracts._parse_record_payload(
        contracts.SourceCapsuleAdmissionV1, _canonical_json(record) + b"\n"
    )


def frozen_event_ledger_protocol() -> Dict[str, Any]:
    """Return the exact future event order without validating or issuing a record."""

    body = {
        "schema": "heterodiff-a1-r1-successor-event-ledger-protocol-v1",
        "phase_event_order": [
            "RANK",
            "EXACT",
            "PRIMARY",
            "PRIMARY_METRICS",
            "CONTROLS",
        ],
        "phase_event_ordinals": dict(contracts.PHASE_EVENT_ORDINAL),
        "global_authority_event_ranges": {
            "RANK": {
                "authorization": 0,
                "request": 1,
                "completion": 2,
                "admission": 3,
            },
            "EXACT": {
                "authorization": 4,
                "coordinate_phase_base": 4,
                "coordinate_count": 24,
                "permit_offset": 1,
                "request_offset": 2,
                "completion_offset": 3,
                "consumption_offset": 4,
                "aggregate_admission": 101,
            },
            "PRIMARY": {
                "authorization": 102,
                "coordinate_phase_base": 102,
                "coordinate_count": 48,
                "permit_offset": 1,
                "request_offset": 2,
                "completion_offset": 3,
                "consumption_offset": 4,
                "aggregate_admission": 295,
            },
            "PRIMARY_METRICS": {
                "authorization": 296,
                "request": 297,
                "completion": 298,
                "admission": 299,
            },
            "CONTROLS": {
                "authorization": 300,
                "coordinate_phase_base": 300,
                "coordinate_count": 72,
                "permit_offset": 1,
                "request_offset": 2,
                "completion_offset": 3,
                "consumption_offset": 4,
                "aggregate_admission": 589,
            },
        },
        "coordinate_event_formula": (
            "coordinate_phase_base + 4*phase_coordinate_ordinal + offset"
        ),
        "coordinate_previous_head_rule": (
            "ordinal zero permit follows phase authorization; every later permit "
            "follows the immediately prior validated consumption; request follows "
            "permit; completion follows request; consumption follows completion"
        ),
        "phase_aggregate_previous_head_rule": (
            "aggregate admission follows the final ordered coordinate consumption"
        ),
        "phase_predecessor_rule": {
            "RANK": "PLAN_INITIAL_HEAD_AND_NO_PRIOR_ADMISSION",
            "EXACT": "RANK_ADMISSION",
            "PRIMARY": "EXACT_AGGREGATE_ADMISSION",
            "PRIMARY_METRICS": "PRIMARY_AGGREGATE_ADMISSION",
            "CONTROLS": "PRIMARY_METRICS_ADMISSION_WITH_PRIMARY_AGGREGATE_CUSTODY",
        },
        "controls_required_custody": {
            "controls_coordinate_count": 72,
            "prior_primary_coordinate_count": 48,
            "complete_sampled_coordinate_count": 120,
            "primary_metrics_barrier_required": True,
        },
        "final_terminal_event_ordinal": 589,
        "next_unused_authority_event_ordinal": 590,
        "all_nonces_and_terminal_hashes_unique_required": True,
        "unused_to_spent_exactly_once_required": True,
        "cross_plan_cross_nonce_cross_head_replay_rejection_required": True,
        "sequential_transcript_validator_enabled": False,
        "issues_authority": False,
    }
    return {
        **body,
        "protocol_sha256": _sha256(
            b"heterodiff-a1-r1-successor-event-ledger-protocol-v1\0"
            + _canonical_json(body)
        ),
    }


def _collect_sha256_values(value: Any, destination: set[str]) -> None:
    if type(value) is str:
        if len(value) == 64 and all(
            character in "0123456789abcdef" for character in value
        ):
            destination.add(value)
        return
    if type(value) is list:
        for item in value:
            _collect_sha256_values(item, destination)
        return
    if type(value) is dict:
        for item in value.values():
            _collect_sha256_values(item, destination)


def d1_execution_lineage_quarantine_roster(workspace_root: Any) -> Dict[str, Any]:
    """Derive the frozen D1/V2 execution-lineage digest closure from custody."""

    root = Path(workspace_root).absolute()
    registration_payload, _ = _read_stable_file(root / D1_MACHINE_PATH)
    if _sha256(registration_payload) != D1_REQUIRED_RAW_SHA256[D1_MACHINE_PATH]:
        raise AuthorityProtocolError("D1 registration custody changed")
    try:
        registration = json.loads(registration_payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuthorityProtocolError("D1 registration is not ASCII JSON") from error
    if type(registration) is not dict:
        raise AuthorityProtocolError("D1 registration is not an object")
    bindings = registration["d1_artifact_bindings"]["files"]
    expected_paths = {
        "attempt_marker": D1_ATTEMPT_PATH,
        "diagnostic_record": D1_DIAGNOSTIC_PATH,
        "success_receipt": D1_SUCCESS_PATH,
    }
    loaded = {}
    for role, relative_path in expected_paths.items():
        row = bindings[role]
        if row["path"] != relative_path:
            raise AuthorityProtocolError("D1 artifact path changed")
        payload, _ = _read_stable_file(root / relative_path)
        if _sha256(payload) != row["raw_sha256"]:
            raise AuthorityProtocolError("D1 artifact raw custody changed")
        try:
            loaded[role] = json.loads(payload.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AuthorityProtocolError("D1 artifact is not ASCII JSON") from error
    checkpoint = registration["checkpoint_custody"]
    v2_payload, _ = _read_stable_file(root / V2_SUCCESS_PATH)
    if _sha256(v2_payload) != checkpoint["outer_success_receipt_raw_sha256"]:
        raise AuthorityProtocolError("V2 success receipt custody changed")
    try:
        v2 = json.loads(v2_payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuthorityProtocolError("V2 receipt is not ASCII JSON") from error

    by_role: Dict[str, set[str]] = {}

    def add(role: str, value: Any) -> None:
        values: set[str] = set()
        _collect_sha256_values(value, values)
        for sha256 in values:
            by_role.setdefault(sha256, set()).add(role)

    for sha256 in D1_FORBIDDEN_EVIDENCE_SHA256:
        by_role.setdefault(sha256, set()).add("EXPLICIT_REGISTERED_D1_BOUNDARY")
    add("REGISTERED_CHECKPOINT_CUSTODY", checkpoint)
    diagnostic = loaded["diagnostic_record"]
    add("D1_DIAGNOSTIC_FULL_RECORD", diagnostic)
    add("D1_ATTEMPT_FULL_RECORD", loaded["attempt_marker"])
    add("D1_SUCCESS_FULL_RECORD", loaded["success_receipt"])
    add("V2_SUCCESS_FULL_RECORD", v2)
    rows = [
        {"sha256": sha256, "source_roles": sorted(roles)}
        for sha256, roles in sorted(by_role.items())
    ]
    body = {
        "schema": "heterodiff-a1-r1-successor-d1-execution-lineage-quarantine-roster-v1",
        "row_count": len(rows),
        "rows": rows,
        "full_record_recursive_collection_intentionally_over_quarantines_governance": True,
        "governance_hash_exception_permitted_only_in_exact_prerequisite_fields": True,
        "completion_and_output_evidence_match_rejected": True,
    }
    return {
        **body,
        "roster_sha256": _sha256(D1_QUARANTINE_ROSTER_DOMAIN + _canonical_json(body)),
    }


def completion_evidence_protocol(workspace_root: Any) -> Dict[str, Any]:
    """Freeze the D1 exclusion and provisional-completion boundary."""

    quarantine = d1_execution_lineage_quarantine_roster(workspace_root)
    return {
        "d1_execution_lineage_quarantine": quarantine,
        "known_d1_hashes_forbidden_in_every_completion_and_evidence_field": True,
        "exact_and_sampled_member_completions_are_provisional": True,
        "parent_reopened_member_loader_receipt_required": True,
        "reopened_tagged_coordinate_identity_required": True,
        "typed_phase_aggregate_parent_revalidation_required": True,
        "boolean_only_member_revalidation_never_confers_admission": True,
        "d1_execution_admissible": False,
    }


def _audit_value_against_quarantine(value: Any, quarantine: set[str]) -> bool:
    if type(value) is str:
        if value in quarantine:
            raise AuthorityProtocolError("D1/V2 evidence is not successor-admissible")
        return True
    if type(value) is list or type(value) is tuple:
        for item in value:
            _audit_value_against_quarantine(item, quarantine)
        return True
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise AuthorityProtocolError("evidence mapping key has the wrong type")
            _audit_value_against_quarantine(item, quarantine)
        return True
    if value is None or type(value) in {bool, int}:
        return True
    raise AuthorityProtocolError("evidence value is outside the frozen JSON types")


def audit_no_d1_evidence_replay(value: Any, workspace_root: Any = None) -> bool:
    """Reject every occurrence of a frozen D1/V2 evidence digest."""

    root = Path.cwd() if workspace_root is None else Path(workspace_root).absolute()
    roster = d1_execution_lineage_quarantine_roster(root)
    quarantine = {row["sha256"] for row in roster["rows"]}
    return _audit_value_against_quarantine(value, quarantine)


def _future_custody_path_roster_sha256() -> str:
    return _sha256(
        FUTURE_CUSTODY_PATH_ROSTER_DOMAIN + _canonical_json(list(FUTURE_CUSTODY_PATHS))
    )


def _precreation_commitment(
    snapshot: Mapping[str, Any],
    *,
    registration_raw_sha256: str,
    registration_record_sha256: str,
    human_sha256: str,
    test_sha256: str,
    campaign_nonce_sha256: str,
) -> Dict[str, Any]:
    """Compute the acyclic precreation commitment; no outcome SHA is admitted."""

    for name, value in (
        ("registration_raw_sha256", registration_raw_sha256),
        ("registration_record_sha256", registration_record_sha256),
        ("human_sha256", human_sha256),
        ("test_sha256", test_sha256),
        ("campaign_nonce_sha256", campaign_nonce_sha256),
    ):
        contracts.require_sha256(value, name)
    predecessor = snapshot["precreation_snapshot"]
    coordinates = predecessor["qualification_snapshot"]["coordinate_manifests"]
    implementation = snapshot["implementation"]
    body = {
        "schema": "heterodiff-a1-r1-successor-precreation-plan-commitment-v1",
        "authority_domain": contracts.AUTHORITY_DOMAIN,
        "registration_raw_sha256": registration_raw_sha256,
        "registration_record_sha256": registration_record_sha256,
        "predecessor_snapshot_sha256": predecessor["snapshot_sha256"],
        "source_capsule_manifest_sha256": snapshot["planned_source_capsule_manifest"][
            "capsule_manifest_sha256"
        ],
        "human_sha256": human_sha256,
        "contracts_sha256": implementation["contracts_sha256"],
        "authority_sha256": implementation["authority_sha256"],
        "adapter_sha256": implementation["adapter_sha256"],
        "test_sha256": test_sha256,
        "bootstrap_spec_sha256": snapshot["adapter_protocol"]["bootstrap_spec"][
            "bootstrap_spec_sha256"
        ],
        "campaign_nonce_sha256": campaign_nonce_sha256,
        "preactivation_source_manifest_sha256": predecessor["qualification_snapshot"][
            "source_manifest"
        ]["manifest_sha256"],
        "registry_semantic_sha256": coordinates["registry_sha256"],
        "execution_phase_schedule_sha256": coordinates["manifests"][
            "execution_phase_schedule"
        ]["manifest_sha256"],
        "all_aggregate_manifest_sha256": coordinates["manifests"]["all_aggregate"][
            "manifest_sha256"
        ],
        "phase_event_schedule_sha256": coordinates["phase_event_schedule"][
            "schedule_sha256"
        ],
        "event_ledger_protocol_sha256": snapshot["event_ledger_protocol"][
            "protocol_sha256"
        ],
        "contract_catalog_sha256": snapshot["contract_catalog"]["catalog_sha256"],
        "future_custody_path_roster_sha256": (_future_custody_path_roster_sha256()),
        "post_marker_source_capsule_admission_sha256": None,
        "post_marker_runtime_manifest_sha256": None,
        "post_marker_runtime_approval_sha256": None,
        "post_marker_prerequisite_evidence_sha256": None,
        "final_successor_plan_sha256": None,
    }
    return {
        "body": body,
        "precreation_plan_commitment_sha256": _sha256(
            PRECREATION_COMMITMENT_DOMAIN + _canonical_json(body)
        ),
    }


def precreation_commitment_protocol() -> Dict[str, Any]:
    """Describe the exact acyclic commitment preimage without choosing a nonce."""

    return {
        "schema": "heterodiff-a1-r1-successor-precreation-commitment-protocol-v1",
        "commitment_digest_domain_ascii": (
            "heterodiff-a1-r1-successor-precreation-plan-commitment-v1"
        ),
        "commitment_digest_domain_terminated_by_nul": True,
        "future_custody_path_roster_digest_domain_ascii": (
            "heterodiff-a1-r1-successor-future-custody-path-roster-v1"
        ),
        "future_custody_path_roster_digest_domain_terminated_by_nul": True,
        "future_custody_paths": list(FUTURE_CUSTODY_PATHS),
        "future_custody_path_roster_sha256": (_future_custody_path_roster_sha256()),
        "commitment_body_fields": [
            "schema",
            "authority_domain",
            "registration_raw_sha256",
            "registration_record_sha256",
            "predecessor_snapshot_sha256",
            "source_capsule_manifest_sha256",
            "human_sha256",
            "contracts_sha256",
            "authority_sha256",
            "adapter_sha256",
            "test_sha256",
            "bootstrap_spec_sha256",
            "campaign_nonce_sha256",
            "preactivation_source_manifest_sha256",
            "registry_semantic_sha256",
            "execution_phase_schedule_sha256",
            "all_aggregate_manifest_sha256",
            "phase_event_schedule_sha256",
            "event_ledger_protocol_sha256",
            "contract_catalog_sha256",
            "future_custody_path_roster_sha256",
            "post_marker_source_capsule_admission_sha256",
            "post_marker_runtime_manifest_sha256",
            "post_marker_runtime_approval_sha256",
            "post_marker_prerequisite_evidence_sha256",
            "final_successor_plan_sha256",
        ],
        "post_marker_outcome_fields_are_null_in_commitment": True,
        "final_plan_hash_is_not_a_marker_input": True,
        "marker_precedes_capsule_runtime_evidence_and_final_plan": True,
    }


def _build_protocol_freeze_snapshot(
    workspace_root: Any, *, require_live_precreation_absence: bool
) -> Dict[str, Any]:
    """Build the frozen snapshot, optionally reopening its precreation absences."""

    root = Path(workspace_root).absolute()
    precreation = frozen_precreation_snapshot(root)
    if require_live_precreation_absence:
        _require_absent(root / PRECREATION_ATTEMPT_MARKER_PATH)
        for relative_path in FUTURE_SUCCESSOR_ROOTS:
            _require_absent(root / relative_path)
    capsule = planned_source_capsule_manifest(root, precreation)
    extra_apis = _extra_api_inventory(root, precreation)
    event_protocol = frozen_event_ledger_protocol()
    future_custody_path_roster_sha256 = _future_custody_path_roster_sha256()
    implementation = {
        "contracts_path": CONTRACTS_PATH,
        "contracts_sha256": _file_sha256(root, CONTRACTS_PATH),
        "authority_path": AUTHORITY_PATH,
        "authority_sha256": _file_sha256(root, AUTHORITY_PATH),
        "adapter_path": ADAPTER_PATH,
        "adapter_sha256": _file_sha256(root, ADAPTER_PATH),
    }
    predecessor_state = precreation["qualification_snapshot"]["preregistration_state"]
    return {
        "schema": contracts.QUALIFICATION_SCHEMA,
        "status": "DORMANT_PROTOCOL_STATIC_AUDIT_PASS_ZERO_EXECUTION_NOT_EXECUTABLE",
        "milestone_state": contracts.MILESTONE_STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "authority_domain": contracts.AUTHORITY_DOMAIN,
        "precreation_snapshot": precreation,
        "contract_catalog": contracts.contract_catalog(),
        "implementation": implementation,
        "planned_source_capsule_manifest": capsule,
        "adapter_protocol": adapter.protocol_status(),
        "event_ledger_protocol": event_protocol,
        "completion_evidence_protocol": completion_evidence_protocol(root),
        "precreation_commitment_protocol": precreation_commitment_protocol(),
        "legacy_runner_api_inventory": precreation["qualification_snapshot"][
            "runner_api_inventory"
        ],
        "additional_api_inventory": extra_apis,
        "runtime_protocol": {
            "candidate_schema": contracts.RUNTIME_CANDIDATE_SCHEMA,
            "review_schema": contracts.RUNTIME_REVIEW_SCHEMA,
            "approval_schema": contracts.RUNTIME_APPROVAL_SCHEMA,
            "external_runtime_manifest_schema": EXTERNAL_RUNTIME_MANIFEST_SCHEMA,
            "external_runtime_manifest_top_level_fields": list(
                EXTERNAL_RUNTIME_MANIFEST_TOP_LEVEL_FIELDS
            ),
            "external_runtime_manifest_binds_successor_approval": False,
            "successor_approval_binds_external_runtime_manifest": True,
            "successor_plan_binds_manifest_and_approval": True,
            "future_custody_paths": dict(SUCCESSOR_RUNTIME_CUSTODY_PATHS),
            "external_loader_api": extra_apis["EXTERNAL_RUNTIME_IDENTITY_LOADER"],
            "external_capture_validator_api": extra_apis[
                "EXTERNAL_RUNTIME_CAPTURE_VALIDATOR"
            ],
            "legacy_runtime_approval_parser_reused": False,
            "candidate_record": None,
            "review_record": None,
            "external_runtime_manifest_record": None,
            "approval_record": None,
            "runtime_admission_semantics_qualified": False,
            "runtime_chain_semantics_qualified": False,
            "issued_record_count": 0,
        },
        "activation_prerequisites": {
            "current_effective_unresolved_null_count": predecessor_state[
                "effective_unresolved_null_projection"
            ]["total"],
            "current_open_blocker_count": predecessor_state["blockers"]["remaining"],
            "current_confirmatory_execution_blocker_count": predecessor_state[
                "blockers"
            ]["confirmatory_execution"],
            "executable_preregistration_required": True,
            "d1_disclosure_and_seed_1729_quarantine_required": True,
            "content_addressed_capsule_required": True,
            "successor_runtime_approval_required": True,
            "pristine_successor_roots_required": True,
            "future_successor_roots": list(FUTURE_SUCCESSOR_ROOTS),
            "future_successor_root_count": len(FUTURE_SUCCESSOR_ROOTS),
            "future_custody_paths": list(FUTURE_CUSTODY_PATHS),
            "future_custody_path_count": len(FUTURE_CUSTODY_PATHS),
            "future_custody_path_roster_sha256": (future_custody_path_roster_sha256),
            "all_future_successor_roots_lstat_absent": True,
            "precreation_attempt_marker_lstat_absent": True,
            "absence_assertions_are_frozen_historical_pre_marker_facts": True,
            "code_and_test_hashes_required": True,
            "plan_and_campaign_nonce_required": True,
            "ungated_precreation_attempt_marker_required": True,
            "ungated_precreation_attempt_marker_path": PRECREATION_ATTEMPT_MARKER_PATH,
            "ungated_precreation_attempt_marker_schema": (
                contracts.PRECREATION_ATTEMPT_MARKER_SCHEMA
            ),
            "future_activation_must_use_frozen_snapshot_not_live_predecessor_loader": True,
            "prerequisite_evidence_schema": contracts.PREREQUISITE_EVIDENCE_SCHEMA,
            "source_capsule_admission_schema": (
                contracts.SOURCE_CAPSULE_ADMISSION_SCHEMA
            ),
            "current_activation_ready": False,
            "precreation_marker_then_capsule_runtime_evidence_then_plan_then_activation": True,
            "precreation_marker_binds_final_plan_sha256": False,
            "precreation_marker_binds_static_plan_commitment": True,
            "final_plan_must_bind_marker_raw_and_record_sha256": True,
            "campaign_nonce_generation_and_one_shot_custody_deferred": True,
            "marker_boolean_and_terminal_string_are_not_historical_proof_alone": True,
        },
        "authority_protocol": {
            "parent_is_sole_future_authority_writer": True,
            "parent_writer_implemented": False,
            "child_authority_import_permitted": False,
            "opaque_runner_id_permitted": False,
            "issued_record_count": 0,
            "mint_route_present": False,
            "issue_route_present": False,
            "consume_route_present": False,
            "materialize_route_present": False,
            "launch_route_present": False,
            "admit_route_enabled": False,
            "activation_semantics_qualified": False,
            "plan_semantics_qualified": False,
            "source_capsule_admission_currently_loadable": False,
            "prerequisite_evidence_currently_loadable": False,
            "rank_and_coordinate_contracts_distinct": True,
            "primary_metrics_is_hard_controls_head_prerequisite": True,
            "exact_member_completions_provisional_until_aggregate": True,
            "event_ledger_formula_frozen": True,
            "event_ledger_protocol_sha256": event_protocol["protocol_sha256"],
            "sequential_transcript_validator_enabled": False,
            "runtime_chain_semantics_qualified": False,
            "runtime_manifest_external_schema_dependency_only": True,
            "legacy_runtime_approval_receipt_reused": False,
            "source_capsule_admission_loader_frozen": True,
            "prerequisite_evidence_loader_refuses_current_draft": True,
        },
        "nonclaims": dict(NONCLAIMS),
    }


def protocol_freeze_snapshot(workspace_root: Any) -> Dict[str, Any]:
    """Audit the current precreation state; issue no records or authority."""

    return _build_protocol_freeze_snapshot(
        workspace_root, require_live_precreation_absence=True
    )


def _exact_record(value: Any, expected_type: type, name: str) -> Dict[str, Any]:
    if type(value) is not expected_type:
        raise AuthorityProtocolError(name + " has the wrong exact record type")
    return value.to_record()


def validate_runtime_chain(
    candidate: contracts.RuntimeCandidateV1,
    review: contracts.RuntimeReviewV1,
    approval: contracts.RuntimeApprovalV1,
    snapshot: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate successor wrapper structure; do not admit the external runtime."""

    candidate_row = _exact_record(candidate, contracts.RuntimeCandidateV1, "candidate")
    review_row = _exact_record(review, contracts.RuntimeReviewV1, "review")
    approval_row = _exact_record(approval, contracts.RuntimeApprovalV1, "approval")
    implementation = snapshot["implementation"]
    runtime_apis = snapshot["runtime_protocol"]
    if (
        candidate_row["target_profile_id"] != TARGET_PROFILE_ID
        or candidate_row["capture_operation"] != "DOUBLE_CAPTURE_NO_SCIENTIFIC_COMPUTE"
        or candidate_row["scientific_compute_executed"] is not False
        or candidate_row["double_capture_stable"] is not True
        or candidate_row["complete_installed_file_verification"] is not True
        or candidate_row["external_candidate_manifest_sha256"]
        != candidate_row["runtime_manifest_preview_sha256"]
    ):
        raise AuthorityProtocolError("runtime candidate gates are not satisfied")
    if (
        review_row["target_profile_id"] != TARGET_PROFILE_ID
        or review_row["candidate_sha256"] != candidate_row["candidate_sha256"]
        or review_row["candidate_raw_sha256"]
        != _sha256(_canonical_json(candidate_row) + b"\n")
        or review_row["capsule_manifest_sha256"]
        != candidate_row["capsule_manifest_sha256"]
        or review_row["decision"] != "APPROVE"
        or review_row["operator_confirmation"] is not True
        or any(value is not True for value in review_row["review_checks"].values())
    ):
        raise AuthorityProtocolError("runtime review is not an exact approval review")
    expected_runtime_apis = {
        "runtime_identity_source_sha256": runtime_apis["external_loader_api"][
            "source_sha256"
        ],
        "runtime_identity_loader_api_sha256": runtime_apis["external_loader_api"][
            "api_signature"
        ]["signature_sha256"],
        "runtime_capture_source_sha256": runtime_apis["external_capture_validator_api"][
            "source_sha256"
        ],
        "runtime_capture_api_sha256": runtime_apis["external_capture_validator_api"][
            "api_signature"
        ]["signature_sha256"],
    }
    if (
        approval_row["target_profile_id"] != TARGET_PROFILE_ID
        or approval_row["candidate_sha256"] != candidate_row["candidate_sha256"]
        or approval_row["review_sha256"] != review_row["review_sha256"]
        or approval_row["capsule_manifest_sha256"]
        != candidate_row["capsule_manifest_sha256"]
        or any(
            approval_row[name] != implementation[name]
            for name in ("contracts_sha256", "authority_sha256", "adapter_sha256")
        )
        or any(
            approval_row[name] != value for name, value in expected_runtime_apis.items()
        )
        or approval_row["approved"] is not True
        or approval_row["limitations"] != list(RUNTIME_APPROVAL_LIMITATIONS)
    ):
        raise AuthorityProtocolError("runtime approval chain is inconsistent")
    return {
        "candidate_sha256": candidate_row["candidate_sha256"],
        "review_sha256": review_row["review_sha256"],
        "runtime_manifest_sha256": approval_row["final_runtime_manifest_sha256"],
        "runtime_approval_sha256": approval_row["approval_sha256"],
        "runtime_admission_qualified": False,
        "runtime_identity_stability_proven": False,
        "hash_inequality_used_as_stability_proof": False,
        "live_external_manifest_semantics_validated": False,
        "external_runtime_files_reopened": False,
    }


def _validate_plan(
    plan: contracts.SuccessorPlanV1,
    activation: contracts.SuccessorActivationV1,
    snapshot: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    plan_row = _exact_record(plan, contracts.SuccessorPlanV1, "plan")
    activation_row = _exact_record(
        activation, contracts.SuccessorActivationV1, "activation"
    )
    implementation = snapshot["implementation"]
    predecessor = snapshot["precreation_snapshot"]
    capsule = snapshot["planned_source_capsule_manifest"]
    coordinates = predecessor["qualification_snapshot"]["coordinate_manifests"]
    transition = snapshot.get("live_transition_context")
    if (
        type(transition) is not dict
        or transition.get("verification_mode")
        != "BOUND_PRECREATION_ATTEMPT_SUPERSESSION"
    ):
        raise AuthorityProtocolError(
            "static plan validation requires the bound precreation transition"
        )
    expected = {
        "authority_domain": contracts.AUTHORITY_DOMAIN,
        "campaign_nonce_sha256": transition["campaign_nonce_sha256"],
        "precreation_plan_commitment_sha256": transition[
            "precreation_plan_commitment_sha256"
        ],
        "precreation_attempt_marker_raw_sha256": transition["marker_raw_sha256"],
        "precreation_attempt_marker_record_sha256": transition["marker_record_sha256"],
        "predecessor_registration_sha256": PREDECESSOR_RECORD_SHA256,
        "predecessor_snapshot_sha256": predecessor["snapshot_sha256"],
        "source_capsule_manifest_sha256": capsule["capsule_manifest_sha256"],
        "contracts_sha256": implementation["contracts_sha256"],
        "authority_sha256": implementation["authority_sha256"],
        "adapter_sha256": implementation["adapter_sha256"],
        "bootstrap_spec_sha256": snapshot["adapter_protocol"]["bootstrap_spec"][
            "bootstrap_spec_sha256"
        ],
        "protocol_registration_raw_sha256": transition["registration_raw_sha256"],
        "protocol_registration_record_sha256": transition["registration_record_sha256"],
        "protocol_test_sha256": transition["protocol_test_sha256"],
        "registry_raw_sha256": predecessor["qualification_snapshot"]["source_manifest"][
            "registry_semantics"
        ]["raw_sha256"],
        "registry_record_sha256": predecessor["qualification_snapshot"][
            "source_manifest"
        ]["registry_semantics"]["record_sha256"],
        "registry_semantic_sha256": coordinates["registry_sha256"],
        "exact_manifest_sha256": coordinates["manifests"]["exact"]["manifest_sha256"],
        "primary_manifest_sha256": coordinates["manifests"]["primary"][
            "manifest_sha256"
        ],
        "controls_manifest_sha256": coordinates["manifests"]["controls"][
            "manifest_sha256"
        ],
        "complete_sampled_manifest_sha256": coordinates["manifests"][
            "complete_sampled"
        ]["manifest_sha256"],
        "execution_phase_schedule_manifest_sha256": coordinates["manifests"][
            "execution_phase_schedule"
        ]["manifest_sha256"],
        "all_aggregate_manifest_sha256": coordinates["manifests"]["all_aggregate"][
            "manifest_sha256"
        ],
        "phase_event_schedule_sha256": coordinates["phase_event_schedule"][
            "schedule_sha256"
        ],
    }
    if any(plan_row[name] != value for name, value in expected.items()):
        raise AuthorityProtocolError("successor plan differs from the frozen context")
    if plan_row["phase_event_order"] != [
        "RANK",
        "EXACT",
        "PRIMARY",
        "PRIMARY_METRICS",
        "CONTROLS",
    ]:
        raise AuthorityProtocolError("successor plan event order changed")
    if (
        activation_row["plan_sha256"] != plan_row["plan_sha256"]
        or activation_row["campaign_nonce_sha256"] != plan_row["campaign_nonce_sha256"]
        or activation_row["precreation_snapshot_sha256"]
        != predecessor["snapshot_sha256"]
        or activation_row["precreation_plan_commitment_sha256"]
        != plan_row["precreation_plan_commitment_sha256"]
        or activation_row["precreation_attempt_marker_raw_sha256"]
        != plan_row["precreation_attempt_marker_raw_sha256"]
        or activation_row["precreation_attempt_marker_record_sha256"]
        != plan_row["precreation_attempt_marker_record_sha256"]
        or activation_row["source_capsule_manifest_sha256"]
        != plan_row["source_capsule_manifest_sha256"]
        or activation_row["runtime_manifest_sha256"]
        != plan_row["runtime_manifest_sha256"]
        or activation_row["runtime_approval_sha256"]
        != plan_row["runtime_approval_sha256"]
        or any(
            activation_row[name] != plan_row[name]
            for name in (
                "contracts_sha256",
                "authority_sha256",
                "adapter_sha256",
                "bootstrap_spec_sha256",
                "protocol_registration_raw_sha256",
                "protocol_registration_record_sha256",
                "protocol_test_sha256",
                "prerequisite_evidence_sha256",
                "source_capsule_admission_sha256",
            )
        )
    ):
        raise AuthorityProtocolError("successor plan and activation custody diverged")
    return plan_row, activation_row


def _validate_common(
    row: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    phase: str,
    previous_head_sha256: str,
    authority_event_ordinal: int,
) -> None:
    expected = {
        "authority_domain": contracts.AUTHORITY_DOMAIN,
        "plan_sha256": plan["plan_sha256"],
        "campaign_nonce_sha256": plan["campaign_nonce_sha256"],
        "authority_event_ordinal": authority_event_ordinal,
        "phase_event_ordinal": contracts.PHASE_EVENT_ORDINAL[phase],
        "previous_head_sha256": previous_head_sha256,
        "source_capsule_manifest_sha256": plan["source_capsule_manifest_sha256"],
        "runtime_manifest_sha256": plan["runtime_manifest_sha256"],
        "runtime_approval_sha256": plan["runtime_approval_sha256"],
        "contracts_sha256": plan["contracts_sha256"],
        "authority_sha256": plan["authority_sha256"],
        "adapter_sha256": plan["adapter_sha256"],
        "bootstrap_spec_sha256": plan["bootstrap_spec_sha256"],
        "protocol_registration_raw_sha256": plan["protocol_registration_raw_sha256"],
        "protocol_registration_record_sha256": plan[
            "protocol_registration_record_sha256"
        ],
        "protocol_test_sha256": plan["protocol_test_sha256"],
        "prerequisite_evidence_sha256": plan["prerequisite_evidence_sha256"],
        "source_capsule_admission_sha256": plan["source_capsule_admission_sha256"],
    }
    if any(
        type(row.get(name)) is not type(value) or row.get(name) != value
        for name, value in expected.items()
    ):
        raise AuthorityProtocolError("authority-common custody link changed")


def validate_phase_authorization(
    authorization: contracts.PhaseAuthorizationV1,
    plan: contracts.SuccessorPlanV1,
    activation: contracts.SuccessorActivationV1,
    snapshot: Mapping[str, Any],
    *,
    phase: str,
    previous_head_sha256: str,
    prior_admission_sha256: Any,
    authority_event_ordinal: int,
) -> Dict[str, Any]:
    """Fail closed until a later ledger implementation proves every invariant."""

    del (
        authorization,
        plan,
        activation,
        snapshot,
        phase,
        previous_head_sha256,
        prior_admission_sha256,
        authority_event_ordinal,
    )
    raise AuthorityProtocolError(
        "phase authorization is unavailable until the later activation milestone"
    )


def _runner_row(snapshot: Mapping[str, Any], phase: str) -> Mapping[str, Any]:
    rows = snapshot["legacy_runner_api_inventory"]["phase_rows"]
    matches = [row for row in rows if row["phase"] == phase]
    if len(matches) != 1:
        raise AuthorityProtocolError("legacy runner phase inventory changed")
    return matches[0]


def _check_api_fields(
    row: Mapping[str, Any], prefix: str, expected: Mapping[str, Any]
) -> None:
    values = {
        prefix + "_module": expected["module"],
        prefix + "_qualname": expected["qualname"],
        prefix + "_source_sha256": expected["source_sha256"],
        prefix + "_api_sha256": expected["api_signature"]["signature_sha256"],
    }
    if any(row.get(name) != value for name, value in values.items()):
        raise AuthorityProtocolError(prefix + " API identity changed")


def _inventory_api(row: Mapping[str, Any], prefix: str) -> Dict[str, Any]:
    return {
        "module": row[prefix + "_module"],
        "qualname": row[prefix + "_qualname"],
        "source_sha256": row[prefix + "_source_sha256"],
        "api_signature": row[prefix + "_api_signature"],
    }


def validate_rank_chain(
    request: contracts.RankRequestV1,
    completion: contracts.RankCompletionV1,
    admission: contracts.RankAdmissionV1,
    authorization: contracts.PhaseAuthorizationV1,
    plan: contracts.SuccessorPlanV1,
    activation: contracts.SuccessorActivationV1,
    snapshot: Mapping[str, Any],
) -> Dict[str, str]:
    """Fail closed; the distinct rank transcript schema issues no authority."""

    del request, completion, admission, authorization, plan, activation, snapshot
    raise AuthorityProtocolError(
        "rank transcript admission is frozen but deliberately not enabled"
    )


def _coordinate_identity(
    snapshot: Mapping[str, Any], phase: str, ordinal: int
) -> Tuple[Mapping[str, Any], str, Sequence[Any]]:
    key = phase.lower()
    manifest = snapshot["precreation_snapshot"]["qualification_snapshot"][
        "coordinate_manifests"
    ]["manifests"][key]
    if (
        type(ordinal) is not int
        or ordinal < 0
        or ordinal >= manifest["coordinate_count"]
    ):
        raise AuthorityProtocolError("coordinate ordinal is outside the frozen phase")
    row = dict(manifest["coordinates"][ordinal])
    row.pop("manifest_ordinal")
    row.pop("manifest_ordinal_domain")
    return (
        row,
        manifest["manifest_sha256"],
        manifest["underlying_request_projections"][ordinal],
    )


def validate_coordinate_chain(
    permit: contracts.CoordinatePermitV1,
    request: contracts.CoordinateRequestV1,
    completion: contracts.CoordinateCompletionV1,
    consumption: contracts.CoordinateConsumptionV1,
    authorization: contracts.PhaseAuthorizationV1,
    plan: contracts.SuccessorPlanV1,
    activation: contracts.SuccessorActivationV1,
    snapshot: Mapping[str, Any],
) -> Dict[str, Any]:
    """Fail closed; no partial coordinate lifecycle can qualify or consume."""

    del (
        permit,
        request,
        completion,
        consumption,
        authorization,
        plan,
        activation,
        snapshot,
    )
    raise AuthorityProtocolError(
        "coordinate transcript admission is frozen but deliberately not enabled"
    )


def _list_digest(label: str, values: Sequence[str]) -> str:
    return _sha256(
        ("heterodiff-a1-r1-successor-" + label + "-list-v1\0").encode("ascii")
        + _canonical_json(list(values))
    )


def validate_phase_aggregate(
    admission: contracts.PhaseAggregateAdmissionV1,
    coordinate_validations: Sequence[Mapping[str, Any]],
    authorization: contracts.PhaseAuthorizationV1,
    plan: contracts.SuccessorPlanV1,
    activation: contracts.SuccessorActivationV1,
    snapshot: Mapping[str, Any],
    *,
    prior_phase_admission_sha256: Any,
    primary_metrics_admission_sha256: Any,
) -> Dict[str, Any]:
    """Fail closed; no mapping or partial list can stand for typed phase custody."""

    del (
        admission,
        coordinate_validations,
        authorization,
        plan,
        activation,
        snapshot,
        prior_phase_admission_sha256,
        primary_metrics_admission_sha256,
    )
    raise AuthorityProtocolError(
        "phase aggregate admission is frozen but deliberately not enabled"
    )


def validate_primary_metrics_chain(
    request: contracts.PrimaryMetricsRequestV1,
    completion: contracts.PrimaryMetricsCompletionV1,
    admission: contracts.PrimaryMetricsAdmissionV1,
    authorization: contracts.PhaseAuthorizationV1,
    primary_aggregate_admission_sha256: str,
    plan: contracts.SuccessorPlanV1,
    activation: contracts.SuccessorActivationV1,
    snapshot: Mapping[str, Any],
) -> Dict[str, str]:
    """Fail closed; the metrics barrier cannot be asserted by supplied Booleans."""

    del (
        request,
        completion,
        admission,
        authorization,
        primary_aggregate_admission_sha256,
        plan,
        activation,
        snapshot,
    )
    raise AuthorityProtocolError(
        "primary-metrics transcript admission is frozen but deliberately not enabled"
    )


def _path_has_entry(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _registration_binding_sha256s(root: Path, bindings: Any) -> Dict[str, str]:
    expected = (
        ("HUMAN_REGISTRATION", HUMAN_PATH),
        ("CONTRACTS_MODULE", CONTRACTS_PATH),
        ("AUTHORITY_MODULE", AUTHORITY_PATH),
        ("ADAPTER_MODULE", ADAPTER_PATH),
        ("HOSTILE_TEST", TEST_PATH),
    )
    if type(bindings) is not list or len(bindings) != len(expected):
        raise AuthorityProtocolError("registration binding count changed")
    result = {}
    for ordinal, (row, (role, relative_path)) in enumerate(zip(bindings, expected)):
        row_fields = {
            "ordinal",
            "role",
            "path",
            "bytes",
            "raw_sha256",
            "lf_only",
            "is_regular_file",
            "is_symlink",
        }
        if type(row) is not dict or set(row) != row_fields:
            raise AuthorityProtocolError("registration binding fields changed")
        bound, information = _read_stable_file(root / relative_path)
        if (
            type(row["ordinal"]) is not int
            or row["ordinal"] != ordinal
            or row["role"] != role
            or row["path"] != relative_path
            or type(row["bytes"]) is not int
            or row["bytes"] != len(bound)
            or row["raw_sha256"] != _sha256(bound)
            or row["lf_only"] is not True
            or row["is_regular_file"] is not True
            or row["is_symlink"] is not False
            or not stat.S_ISREG(information.st_mode)
            or stat.S_ISLNK(information.st_mode)
            or b"\r" in bound
        ):
            raise AuthorityProtocolError("registration binding custody changed")
        result[role] = row["raw_sha256"]
    return result


def _validate_precreation_marker(
    root: Path,
    sidecar_payload: bytes,
    sidecar_record: Mapping[str, Any],
    frozen_snapshot: Mapping[str, Any],
    binding_sha256s: Mapping[str, str],
) -> Dict[str, str]:
    """Validate the terminal marker without reopening post-marker absence gates."""

    marker_payload, marker_information = _read_stable_file(
        root / PRECREATION_ATTEMPT_MARKER_PATH
    )
    if (
        stat.S_IMODE(marker_information.st_mode) != 0o600
        or marker_information.st_nlink != 1
    ):
        raise AuthorityProtocolError("precreation marker custody mode changed")
    try:
        marker = contracts.PrecreationAttemptMarkerV1.parse(marker_payload)
    except contracts.ContractError as error:
        raise AuthorityProtocolError("precreation marker contract changed") from error
    row = marker.to_record()
    predecessor = frozen_snapshot["precreation_snapshot"]
    coordinates = predecessor["qualification_snapshot"]["coordinate_manifests"]
    source_manifest = predecessor["qualification_snapshot"]["source_manifest"]
    implementation = frozen_snapshot["implementation"]
    expected = {
        "registration_raw_sha256": _sha256(sidecar_payload),
        "registration_record_sha256": sidecar_record["record_sha256"],
        "predecessor_snapshot_sha256": predecessor["snapshot_sha256"],
        "source_capsule_manifest_sha256": frozen_snapshot[
            "planned_source_capsule_manifest"
        ]["capsule_manifest_sha256"],
        "human_sha256": binding_sha256s["HUMAN_REGISTRATION"],
        "contracts_sha256": implementation["contracts_sha256"],
        "authority_sha256": implementation["authority_sha256"],
        "adapter_sha256": implementation["adapter_sha256"],
        "test_sha256": binding_sha256s["HOSTILE_TEST"],
        "preactivation_source_manifest_sha256": source_manifest["manifest_sha256"],
        "registry_semantic_sha256": coordinates["registry_sha256"],
        "execution_phase_schedule_sha256": coordinates["manifests"][
            "execution_phase_schedule"
        ]["manifest_sha256"],
        "all_aggregate_manifest_sha256": coordinates["manifests"]["all_aggregate"][
            "manifest_sha256"
        ],
        "phase_event_schedule_sha256": coordinates["phase_event_schedule"][
            "schedule_sha256"
        ],
        "contract_catalog_sha256": frozen_snapshot["contract_catalog"][
            "catalog_sha256"
        ],
        "future_custody_path_roster_sha256": (_future_custody_path_roster_sha256()),
    }
    if any(
        type(row.get(name)) is not str or row.get(name) != value
        for name, value in expected.items()
    ):
        raise AuthorityProtocolError("precreation marker static custody changed")
    commitment = _precreation_commitment(
        frozen_snapshot,
        registration_raw_sha256=expected["registration_raw_sha256"],
        registration_record_sha256=expected["registration_record_sha256"],
        human_sha256=expected["human_sha256"],
        test_sha256=expected["test_sha256"],
        campaign_nonce_sha256=row["campaign_nonce_sha256"],
    )
    if (
        row["precreation_plan_commitment_sha256"]
        != commitment["precreation_plan_commitment_sha256"]
        or row["all_future_roots_pristine_before_marker"] is not True
        or row["exclusive_create_completed"] is not True
        or row["attempt_state"] != "PRECREATION_ATTEMPT_SPENT_TERMINAL_NO_RETRY"
    ):
        raise AuthorityProtocolError("precreation marker commitment changed")
    return {
        "verification_mode": "BOUND_PRECREATION_ATTEMPT_SUPERSESSION",
        "marker_raw_sha256": _sha256(marker_payload),
        "marker_record_sha256": row["marker_sha256"],
        "registration_raw_sha256": expected["registration_raw_sha256"],
        "registration_record_sha256": expected["registration_record_sha256"],
        "protocol_test_sha256": expected["test_sha256"],
        "campaign_nonce_sha256": row["campaign_nonce_sha256"],
        "precreation_plan_commitment_sha256": row["precreation_plan_commitment_sha256"],
    }


class DormantAuthorityProtocolQualification:
    """Immutable proof of the canonical zero-execution sidecar snapshot."""

    __slots__ = ("_snapshot", "_record_sha256", "_verification_mode")

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise TypeError("qualification is constructed only by the canonical loader")

    @property
    def record_sha256(self) -> str:
        return self._record_sha256

    @property
    def verification_mode(self) -> str:
        return self._verification_mode

    def snapshot(self) -> Dict[str, Any]:
        value = json.loads(self._snapshot.decode("ascii"))
        if type(value) is not dict:
            raise AuthorityProtocolError("qualification snapshot changed type")
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise AttributeError("dormant authority qualification is immutable")


def load_dormant_protocol_qualification(
    workspace_root: Any,
) -> DormantAuthorityProtocolQualification:
    """Reopen either pristine precreation or its exact bound supersession marker."""

    root = Path(workspace_root).absolute()
    payload, record = _load_canonical_json(root / MACHINE_PATH)
    fields = {
        "schema_version",
        "registration_id",
        "registration_mode",
        "scope",
        "milestone_state",
        "global_state",
        "qualification_snapshot",
        "nonclaims",
        "publication_anonymity_boundary",
        "next_gate",
        "registration_bindings",
        "record_sha256",
    }
    if set(record) != fields:
        raise AuthorityProtocolError("registration sidecar fields changed")
    claimed = contracts.require_sha256(record["record_sha256"], "record_sha256")
    body = dict(record)
    body["record_sha256"] = None
    if _sha256(REGISTRATION_DOMAIN + _canonical_json(body)) != claimed:
        raise AuthorityProtocolError("registration sidecar self digest changed")
    if (
        record["schema_version"] != contracts.REGISTRATION_SCHEMA
        or record["registration_id"] != REGISTRATION_ID
        or record["registration_mode"] != "ADDITIVE_DORMANT_PROTOCOL_ZERO_EXECUTION"
        or record["scope"] != "INTERNAL_PREREGISTRATION_DEVELOPMENT_CUSTODY"
        or record["milestone_state"] != contracts.MILESTONE_STATE
        or record["global_state"] != "DRAFT_NOT_EXECUTABLE"
        or record["nonclaims"] != NONCLAIMS
        or record["publication_anonymity_boundary"] != PUBLICATION_ANONYMITY_BOUNDARY
    ):
        raise AuthorityProtocolError("registration sidecar state changed")
    binding_sha256s = _registration_binding_sha256s(
        root, record["registration_bindings"]
    )
    marker_present = _path_has_entry(root / PRECREATION_ATTEMPT_MARKER_PATH)
    if marker_present:
        fresh = _build_protocol_freeze_snapshot(
            root, require_live_precreation_absence=False
        )
        marker = _validate_precreation_marker(
            root, payload, record, fresh, binding_sha256s
        )
        verification_mode = "BOUND_PRECREATION_ATTEMPT_SUPERSESSION"
    else:
        fresh = protocol_freeze_snapshot(root)
        marker = None
        verification_mode = "LIVE_PRECREATION_ABSENCE"
    if _canonical_json(record["qualification_snapshot"]) != _canonical_json(fresh):
        raise AuthorityProtocolError("registration snapshot differs from live audit")
    if record["next_gate"] != fresh["activation_prerequisites"]:
        raise AuthorityProtocolError("registration next gate changed")
    if payload != _canonical_json(record) + b"\n":
        raise AuthorityProtocolError("registration sidecar bytes changed")
    qualified_snapshot = dict(fresh)
    if marker is not None:
        qualified_snapshot["live_transition_context"] = marker
    value = object.__new__(DormantAuthorityProtocolQualification)
    object.__setattr__(value, "_snapshot", _canonical_json(qualified_snapshot))
    object.__setattr__(value, "_record_sha256", claimed)
    object.__setattr__(value, "_verification_mode", verification_mode)
    if marker is not None and marker["marker_record_sha256"] == claimed:
        raise AuthorityProtocolError("marker and registration digests cannot alias")
    return value


def load_source_capsule_admission(
    workspace_root: Any,
) -> contracts.SourceCapsuleAdmissionV1:
    """Live-open the future capsule only after the exact attempt marker exists."""

    qualification = load_dormant_protocol_qualification(workspace_root)
    if qualification.verification_mode != "BOUND_PRECREATION_ATTEMPT_SUPERSESSION":
        raise AuthorityProtocolError(
            "source capsule admission requires the bound precreation marker"
        )
    return _load_source_capsule_admission_from_snapshot(
        Path(workspace_root).absolute(), qualification.snapshot()
    )


def load_prerequisite_evidence(workspace_root: Any) -> contracts.PrerequisiteEvidenceV1:
    """Recompute prerequisite state and refuse the current non-executable draft."""

    qualification = load_dormant_protocol_qualification(workspace_root)
    snapshot = qualification.snapshot()
    state = snapshot["precreation_snapshot"]["qualification_snapshot"][
        "preregistration_state"
    ]
    unresolved = state["effective_unresolved_null_projection"]["total"]
    blockers = state["blockers"]
    if (
        state["global_state"] != "DRAFT_NOT_EXECUTABLE"
        or type(unresolved) is not int
        or unresolved != 172
        or type(blockers["remaining"]) is not int
        or blockers["remaining"] != 12
        or blockers["confirmatory_execution"] != 10
        or blockers["claim_promotion_and_submission"] != 2
    ):
        raise AuthorityProtocolError("current prerequisite baseline changed")
    for relative_path, expected in D1_REQUIRED_RAW_SHA256.items():
        payload, _ = _read_stable_file(Path(workspace_root).absolute() / relative_path)
        if _sha256(payload) != expected:
            raise AuthorityProtocolError("D1 disclosure custody changed")
    raise AuthorityProtocolError(
        "prerequisite evidence cannot load while 172 nulls and 12 blockers remain"
    )


def status(workspace_root: Any) -> Dict[str, Any]:
    qualification = load_dormant_protocol_qualification(workspace_root)
    snapshot = qualification.snapshot()
    return {
        "schema": "heterodiff-a1-r1-successor-dormant-protocol-status-v1",
        "state": contracts.MILESTONE_STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "qualification_status": snapshot["status"],
        "verification_mode": qualification.verification_mode,
        "precreation_marker_supersession_bound": (
            qualification.verification_mode == "BOUND_PRECREATION_ATTEMPT_SUPERSESSION"
        ),
        "frozen_absence_facts_are_historical_after_marker": True,
        "future_root_absence_live_verified_in_this_status": (
            qualification.verification_mode == "LIVE_PRECREATION_ABSENCE"
        ),
        "registration_record_sha256": qualification.record_sha256,
        "issued_record_count": 0,
        "activation_ready": False,
        "authority_activated": False,
        "materialization_performed": False,
        "execution_authorized": False,
    }


__all__ = [
    "ADAPTER_PATH",
    "AUTHORITY_PATH",
    "AuthorityProtocolError",
    "CONTRACTS_PATH",
    "DormantAuthorityProtocolQualification",
    "FUTURE_CAPSULE_ROOT",
    "FUTURE_CUSTODY_PATHS",
    "FUTURE_SUCCESSOR_ROOTS",
    "HUMAN_PATH",
    "MACHINE_PATH",
    "NONCLAIMS",
    "PREDECESSOR_RECORD_SHA256",
    "PUBLICATION_ANONYMITY_BOUNDARY",
    "REGISTRATION_ID",
    "TEST_PATH",
    "audit_no_d1_evidence_replay",
    "completion_evidence_protocol",
    "d1_execution_lineage_quarantine_roster",
    "frozen_precreation_snapshot",
    "frozen_event_ledger_protocol",
    "load_dormant_protocol_qualification",
    "load_prerequisite_evidence",
    "load_source_capsule_admission",
    "planned_source_capsule_manifest",
    "precreation_commitment_protocol",
    "protocol_freeze_snapshot",
    "status",
    "validate_runtime_chain",
]
