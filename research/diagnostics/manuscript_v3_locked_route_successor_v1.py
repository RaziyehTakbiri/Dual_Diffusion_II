"""Read-only final validator for the locked-route manuscript successor.

This validator binds the byte-stable historical manuscript predecessors, the
settled project-control inputs, the independently audited B05 design-freeze
package, and the seven-file additive successor.  A PASS makes only the narrow
manuscript-synchronization predicate true.  It has no scientific, claim,
runtime, data, citation, or tracker effect.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


SCHEMA = "heterodiff-manuscript-v3-locked-route-successor-v1"
STATE = "MANUSCRIPT_V3_LOCKED_ROUTE_SUCCESSOR_PREOUTCOME"
BINDING_STATUS = "FINAL_B05_BOUND_LOCKED_ROUTE_SYNCHRONIZED"
TARGET_PREDICATE = (
    "MANUSCRIPT_METHOD_DOMAIN_TEXT_SYNCHRONIZED_TO_LOCKED_ROUTE_WITH_"
    "HISTORICAL_PREDECESSORS_BYTE_STABLE"
)
MACHINE_PATH = "research/fixtures/manuscript_v3_locked_route_successor_v1.json"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
B05_CONTROL_PREDICATE = (
    "B05_F007_F018_ALL_OR_NOTHING_KNOWN_LAW_DESIGN_FREEZE_CERTIFIED"
)
B05_STATE = "GATE_A_B05_F007_F018_KNOWN_LAW_DESIGN_FROZEN_PREOUTCOME"
B05_RECORD_SHA256 = (
    "d81b52f94fe420b50f3aa5bf5d0edc97c5b55bdedf19c5bb9a8b499a23397e8b"
)
MAX_FILE_BYTES = 1_000_000
MAX_TREE_NODES = 20_000
MAX_TREE_DEPTH = 24


class ValidationError(ValueError):
    """Raised when an exact binding or synchronization invariant fails."""


HISTORICAL: Tuple[Tuple[str, int, str], ...] = (
    (
        "manuscript_v3/manuscript_v3.md",
        66023,
        "0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8",
    ),
    (
        "manuscript_v3/manuscript_v3.tex",
        75457,
        "0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9",
    ),
    (
        "manuscript_v3/claim_ledger.md",
        130915,
        "793f7fbda938f66d771af3dc480d13dc784862a439ee65452b79c776d78e8245",
    ),
)


SETTLED_INPUTS: Tuple[Tuple[str, int, str, str, str], ...] = (
    (
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        39771,
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        "manuscript-v3-execution-preregistration-v1",
        "DRAFT_NOT_EXECUTABLE",
    ),
    (
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        24571,
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "heterodiff-manuscript-v3-execution-preregistration-preexecution-closure-v2",
        "STATIC_PREFIX_QUALIFIED_NOT_EXECUTABLE",
    ),
    (
        "research/fixtures/manuscript_v3_cks_count_normalized_event_theorem_v1.json",
        10073,
        "33dd22403ad7d71375c53c05028dd59567f127e233a8dc247a7a7ea730f13f6f",
        "heterodiff-manuscript-v3-cks-count-normalized-event-theorem-v1",
        "GENERIC_CKS_THEOREM_PROVED_EXACT_DOMAIN_INSTANCE_PENDING",
    ),
    (
        "research/fixtures/manuscript_v3_cks_count_normalized_event_reference_implementation_v1.json",
        10720,
        "9842d49a2a14ecaaa1f968ffd427f1792b31aa6d3c67384fcf0de5702db95dbb",
        "heterodiff-manuscript-v3-cks-count-normalized-event-reference-implementation-v1",
        "GENERIC_CKS_COUNT_NORMALIZED_EVENT_REFERENCE_IMPLEMENTATION_VALIDATED",
    ),
    (
        "research/fixtures/manuscript_v3_c17_po13_initializer_kl_proof_v1.json",
        23091,
        "ac7338877223bc4aeab58d28289d7342ce4bd6acf6f21573f372f9a537233a64",
        "heterodiff-manuscript-v3-c17-po13-initializer-kl-proof-v1",
        "C17_GATE_A_ROUTE_NARROWED_NO_GO_PO13_PROVED_C17_UNPROVED",
    ),
    (
        "research/fixtures/manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.json",
        20823,
        "38c0f11f03fe11d61660823e36404b0c26ff5a3de012400675ba8452c045a9a1",
        "heterodiff-manuscript-v3-gate-a-minimum-contribution-route-rebaseline-v1",
        "GATE_A_MINIMUM_EMPIRICAL_CONTRIBUTION_ROUTE_REBASELINED_PREOUTCOME",
    ),
    (
        "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
        8455,
        "b8a74f1131f85aa1b7497f2f43bd34a0e30bc471953c935d4362a5a8dea1446a",
        "heterodiff-manuscript-v3-gate-a-local-statistical-and-downstream-decision-freeze-v1",
        "GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISIONS_FROZEN",
    ),
    (
        "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json",
        21912,
        "0e91275c1671e2725aea60c32d4cac2216c6bb71c2cda195b53b79d8fd295388",
        "heterodiff-manuscript-v3-retail-task-and-dual-domain-manifest-drafts-v1",
        "RETAIL_TASK_AND_DUAL_DOMAIN_MANIFEST_DRAFTS_SYNTHETICALLY_VALIDATED",
    ),
    (
        "research/fixtures/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json",
        19860,
        "b7dc23fd0dfee04ffe4834ff1b186ca99dce23f784c4555a245aab0cfb47f068",
        "heterodiff-manuscript-v3-gate-a-retail-temporal-rule-field-freeze-v1",
        "GATE_A_RETAIL_F060_TEMPORAL_RULE_FROZEN_PREOUTCOME",
    ),
    (
        "research/fixtures/manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.json",
        12279,
        "79fb7722a9007d18d0fe6f0c7f00026b37170930b87686e910d472b28e54b2b9",
        "heterodiff-manuscript-v3-formal-test29-finite-acyclic-route-v1",
        "FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED",
    ),
    (
        "research/fixtures/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.json",
        13465,
        "03b6ff21dedc065a3385f403f7631ee89023bd9572d5793405fa2d8492cb7cb5",
        "heterodiff-manuscript-v3-formal-test30-synthetic-coupled-path-qualification-v1",
        "SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED",
    ),
    (
        "research/fixtures/manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.json",
        22780,
        "6909b2aeeb912024689b1dc43704549c855ccc1d37fbe67a8f412ed4adb38bb3",
        "heterodiff-manuscript-v3-formal-test29-test30-single-macrostep-integration-qualification-v1",
        "SYNTHETIC_SUPPLIED_INPUT_SINGLE_MACROSTEP_LEFT_JUMP_RIGHT_INTEGRATION_VALIDATED",
    ),
    (
        "research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json",
        8461,
        "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8",
        "heterodiff-manuscript-v3-test-data-prospective-no-acquisition-seal-v1",
        "NO_TEST_DATA_ACQUIRED_USER_REPORTED_PROSPECTIVE_SEAL_ACTIVE",
    ),
)


B05_INPUTS: Tuple[Tuple[str, str, int, str], ...] = (
    (
        "src/heterodiff/evaluation/"
        "mixed_marked_ctmc_ou_known_law_certified_reference.py",
        "CERTIFIED_REFERENCE_SOURCE",
        124895,
        "98ffb1f42bee3efc097f378cc55a00b88f2d8570b9f3e8de1fe5f9a727f2e268",
    ),
    (
        "PROJECT_GATE_A_B05_KNOWN_LAW_DESIGN_FREEZE.md",
        "HUMAN_DESIGN_FREEZE_RECORD",
        13766,
        "ad03491578ba81c597906495f5aec5ceb36508cb9c0736f5f33af6d9babbc05d",
    ),
    (
        "research/fixtures/"
        "manuscript_v3_gate_a_b05_known_law_design_freeze_v1.json",
        "MACHINE_DESIGN_FREEZE_RECORD",
        269205,
        "c49ef829cab9c8a7459216d37cb70382d4c0027e20aa3c343c5fbd0ed825ee32",
    ),
    (
        "research/diagnostics/"
        "manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py",
        "READ_ONLY_DESIGN_FREEZE_VALIDATOR",
        33523,
        "d53a5656e4322e5b169bd859af531ea208ccaf413ddd9660a31c350d93cc2eb2",
    ),
    (
        "tests/unit/"
        "test_manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py",
        "HOSTILE_DESIGN_FREEZE_TESTS",
        18517,
        "052190e27ea71f06b1f93ba8df647867d813447464870c6e0f78c75f61b8524a",
    ),
)


SUCCESSOR_PATHS = (
    "manuscript_v3/manuscript_v3_locked_route_successor_v1.md",
    "manuscript_v3/manuscript_v3_locked_route_successor_v1.tex",
    "manuscript_v3/claim_ledger_locked_route_successor_v1.md",
    "PROJECT_MANUSCRIPT_V3_LOCKED_ROUTE_SUCCESSOR.md",
    MACHINE_PATH,
    "research/diagnostics/manuscript_v3_locked_route_successor_v1.py",
    "tests/unit/test_manuscript_v3_locked_route_successor_v1.py",
)


FROZEN_SUCCESSOR_NONVALIDATOR: Tuple[Tuple[str, str, int, str], ...] = (
    (
        SUCCESSOR_PATHS[0],
        "CURRENT_MARKDOWN_ROUTE_SUCCESSOR",
        16351,
        "e06cb6780974dea98b85df03c04104b034bfcf4bdd7b3825d9b375d6983849db",
    ),
    (
        SUCCESSOR_PATHS[1],
        "CURRENT_TEX_ROUTE_SUCCESSOR",
        10953,
        "39b063821595dcda93102361c3310c166fa64b222fda193495dc0e1e7315bb13",
    ),
    (
        SUCCESSOR_PATHS[2],
        "CURRENT_CLAIM_LEDGER_SUCCESSOR",
        8944,
        "11fb98d733c402b9ae3e05a561a01fb00f7cecee7a99a9d241f65e0b4a5fb6c6",
    ),
    (
        SUCCESSOR_PATHS[3],
        "HUMAN_PACKAGE_RECORD",
        7630,
        "da43f5802fe71f17d95b1515163f2cf373d12c072e2058595b0978d0efc64f2f",
    ),
    (
        SUCCESSOR_PATHS[6],
        "FINAL_HOSTILE_TESTS",
        7637,
        "2423361968445a42b7b2f36d9fc6f77a56b89999e7f585aa6e264b8557b72f8d",
    ),
)


REQUIRED_TEXT: Mapping[str, Tuple[str, ...]] = {
    SUCCESSOR_PATHS[0]: (
        "R1-A1",
        "R4-RETAIL",
        "REAL_DOMAIN_C17_PROMOTION_UNDER_CURRENT_FORK_B_OBSERVABILITY = NO_GO",
        "\\Phi(x)=",
        "count-normalized-event CKS",
        "cap-one quantitative path core and three disjoint",
        "cap-two structural subcases",
        "ordinary continuous-time CTMC with exponential jump times",
        "matrix-analytic uniformization",
        B05_CONTROL_PREDICATE,
        "accepted all-or-nothing design freeze closes exactly",
        "not normalized evidence and is not a KL/TV aggregand",
        "Formal Test 29 remains `OPEN`",
        "Formal Test 30 remains `PENDING`",
        "| Pre-execution fields | 146 | 20 |",
        "| Total fields | 152 | 20 |",
        "All twelve blockers remain open",
        "No result prose is authorized",
    ),
    SUCCESSOR_PATHS[1]: (
        "R1-A1",
        "R4-RETAIL",
        "REAL\\_DOMAIN\\_C17\\_PROMOTION",
        "\\Phi(x)=",
        "three disjoint cap-two structural subcases",
        "ordinary continuous-time CTMC with exponential jump times",
        "matrix-analytic uniformization",
        "B05_F007_F018_ALL_OR_NOTHING",
        "146 open and 20 closed pre-execution fields",
        "152 open and 20 closed total",
        "not a cap-two quantitative path result",
        "Formal Test 29 is open",
        "Formal Test 30 is pending",
    ),
    SUCCESSOR_PATHS[2]: (
        "UNPROVED_REAL_DOMAIN_PROMOTION_NO_GO",
        "GENERIC_THEOREM_PROVED",
        "RETAIL_TASK_SCHEMA_AND_DUAL_DOMAIN_SNAPSHOT_SPLIT_MANIFEST_DRAFTS_VALIDATED",
        "RETAIL_F060_PARAMETERIZED_TEMPORAL_CUTOFF_WINDOW_RULE_FROZEN",
        "F007`--`F018",
        "ordinary continuous-time CTMC with exponential jump times",
        B05_CONTROL_PREDICATE,
        TARGET_PREDICATE,
        "152 open and 20 closed total",
        "Claims promoted:** 0",
    ),
    SUCCESSOR_PATHS[3]: (
        TARGET_PREDICATE,
        BINDING_STATUS,
        "one-way current successor",
        "three disjoint cap-two",
        "ordinary continuous-time/exponential cap-one CTMC jumps",
        "matrix-analytic uniformization",
        B05_CONTROL_PREDICATE,
        "current settled counts 146/20 pre",
        "target predicate is true for the exact stopped-byte package",
    ),
}


FORBIDDEN_AFFIRMATIVE_MARKERS = (
    "CURRENT_ROUTE_USES_R5_ASAP",
    "CURRENT_ROUTE_HAS_THREE_REAL_DOMAINS",
    "ROUTE_B_IS_A_FALLBACK",
    "RAW_UNNORMALIZED_CKS_IS_CURRENT",
    "C17_IS_REQUIRED_REAL_DOMAIN_HEADLINE",
    "FORMAL_TEST_28_CLOSED",
    "FORMAL_TEST_29_CLOSED",
    "FORMAL_TEST_30_CLOSED",
    "SCIENTIFIC_RESULT_PRESENT",
    "PROVISIONAL_PENDING_B05_FINAL_GO",
    "OPEN_PENDING_B05_FINAL_AUDIT",
)


def _safe_relative_path(value: object) -> str:
    if type(value) is not str or not value or len(value) > 512:
        raise ValidationError("path must be a bounded nonempty string")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise ValidationError("path is not a canonical workspace-relative path")
    return value


def _stable_read(workspace: Path, relative: str) -> bytes:
    relative = _safe_relative_path(relative)
    path = workspace / relative
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError(relative + " is not a regular non-symlink file")
    if before.st_nlink != 1:
        raise ValidationError(relative + " has a forbidden hard-link count")
    if before.st_size < 0 or before.st_size > MAX_FILE_BYTES:
        raise ValidationError(relative + " is outside the byte bound")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValidationError(relative + " changed before open")
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, MAX_FILE_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                raise ValidationError(relative + " exceeded the byte bound")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        raise ValidationError(relative + " changed during stable read")
    payload = b"".join(chunks)
    if len(payload) != before.st_size:
        raise ValidationError(relative + " byte count changed")
    return payload


def _strict_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValidationError("JSON contains a duplicate or non-string key")
        result[key] = value
    return result


def _bounded_tree(value: Any) -> None:
    stack = [(value, 0)]
    seen = set()
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_TREE_NODES or depth > MAX_TREE_DEPTH:
            raise ValidationError("JSON tree exceeds provisional bounds")
        if item is None or type(item) in (bool, int, str):
            continue
        if type(item) is float:
            if not math.isfinite(item):
                raise ValidationError("JSON contains a nonfinite number")
            continue
        if type(item) not in (dict, list):
            raise ValidationError("JSON contains a forbidden scalar type")
        identity = id(item)
        if identity in seen:
            raise ValidationError("JSON contains a cycle or container alias")
        seen.add(identity)
        children: Iterable[Any]
        if type(item) is dict:
            children = item.values()
        else:
            children = item
        stack.extend((child, depth + 1) for child in children)


def _load_json(payload: bytes, label: str) -> Dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(label + " is not UTF-8") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValidationError("JSON contains a nonstandard constant: " + token)
            ),
        )
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValidationError(label + " is not strict JSON") from error
    if type(value) is not dict:
        raise ValidationError(label + " must contain one object")
    _bounded_tree(value)
    return value


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    if type(value) is not dict:
        raise ValidationError("semantic record must be an exact object")
    _bounded_tree(value)
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def record_sha256(record: Mapping[str, Any]) -> str:
    """Return the schema-domain semantic self-digest, excluding its field."""

    if type(record) is not dict:
        raise ValidationError("machine record must be an exact object")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _foreign_record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("foreign machine record must be an exact object")
    schema = record.get("schema_version")
    if type(schema) is not str or not schema or not schema.isascii():
        raise ValidationError("foreign machine schema is invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(
        (schema + "\0").encode("ascii") + _canonical_payload_bytes(payload)
    )


def _record_state(path: str, value: Mapping[str, Any]) -> object:
    if path.endswith("execution_preregistration_preexecution_closure_v2.json"):
        return value.get("disposition")
    return value.get("state")


def _validate_bound_inputs(workspace: Path, record: Mapping[str, Any]) -> Dict[str, Any]:
    expected_historical = [
        {
            "path": path,
            "role": role,
            "bytes": byte_count,
            "raw_sha256": digest,
        }
        for (path, byte_count, digest), role in zip(
            HISTORICAL,
            (
                "HISTORICAL_MARKDOWN_EVIDENCE_ONLY",
                "HISTORICAL_TEX_EVIDENCE_ONLY",
                "HISTORICAL_CLAIM_LEDGER_EVIDENCE_ONLY",
            ),
        )
    ]
    if record.get("historical_predecessors") != expected_historical:
        raise ValidationError("historical predecessor roster changed")
    for path, byte_count, digest in HISTORICAL:
        payload = _stable_read(workspace, path)
        if len(payload) != byte_count or _sha256(payload) != digest:
            raise ValidationError(path + " historical bytes changed")

    expected_settled = [
        {
            "path": path,
            "bytes": byte_count,
            "raw_sha256": digest,
            "schema_version": schema,
            "state": state_value,
        }
        for path, byte_count, digest, schema, state_value in SETTLED_INPUTS
    ]
    if record.get("settled_machine_inputs") != expected_settled:
        raise ValidationError("settled machine-input roster changed")
    loaded: Dict[str, Dict[str, Any]] = {}
    for path, byte_count, digest, schema, state_value in SETTLED_INPUTS:
        payload = _stable_read(workspace, path)
        if len(payload) != byte_count or _sha256(payload) != digest:
            raise ValidationError(path + " settled bytes changed")
        value = _load_json(payload, path)
        if value.get("schema_version") != schema or _record_state(path, value) != state_value:
            raise ValidationError(path + " settled schema/state changed")
        loaded[path] = value
    return loaded


def _validate_settled_semantics(loaded: Mapping[str, Mapping[str, Any]]) -> None:
    theorem = loaded[
        "research/fixtures/manuscript_v3_cks_count_normalized_event_theorem_v1.json"
    ]
    theorem_effects = theorem["project_effects"]
    if (
        theorem_effects["project_control_predicate"]
        != "GATE_A_CKS_COUNT_NORMALIZED_EVENT_ROUTE_MATHEMATICALLY_VIABLE"
        or theorem_effects["project_control_predicate_value_after_independent_validation"]
        is not True
        or theorem_effects["gate_a_exact_metric_checkbox_closed"] is not False
    ):
        raise ValidationError("generic CKS theorem boundary changed")

    reference = loaded[
        "research/fixtures/manuscript_v3_cks_count_normalized_event_reference_implementation_v1.json"
    ]["project_effects"]
    if (
        reference["project_control_predicate"]
        != "GENERIC_CKS_COUNT_NORMALIZED_EVENT_REFERENCE_IMPLEMENTATION_VALIDATED"
        or reference["project_control_value_after_independent_validation"] is not True
        or reference["domain_instance_bound"] is not False
    ):
        raise ValidationError("generic CKS reference boundary changed")

    c17 = loaded[
        "research/fixtures/manuscript_v3_c17_po13_initializer_kl_proof_v1.json"
    ]
    decision = c17["gate_A_route_narrowing_decision"]
    effects = c17["field_blocker_gate_effects"]
    if (
        decision["C17_theorem_status"] != "UNPROVED"
        or decision["real_domain_C17_promotion_under_current_Fork_B_observability"]
        != "NO_GO"
        or effects["control_predicate"]
        != "C17_PO13_INITIALIZER_KL_DERIVATION_AND_ORIENTATION_PROVED"
        or effects["control_predicate_value_after_validation_and_independent_audit"]
        is not True
    ):
        raise ValidationError("C17/PO13 boundary changed")

    contribution = loaded[
        "research/fixtures/manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.json"
    ]
    if (
        contribution["contribution_route"]["route_control_predicate"]
        != "EMPIRICAL_CONTRIBUTION_ROUTE_FROZEN_PREOUTCOME"
        or contribution["contribution_route"]["current_projection"][
            "empirical_contribution_pending"
        ]
        is not True
        or contribution["c17_disposition"]["c17_required_real_domain_headline"]
        is not False
        or [row["field_id"] for row in contribution["field_closures"]]
        != ["F106", "F108"]
    ):
        raise ValidationError("contribution rebaseline boundary changed")

    retail = loaded[
        "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json"
    ]
    if (
        retail["control_predicate"]
        != "RETAIL_TASK_SCHEMA_AND_DUAL_DOMAIN_SNAPSHOT_SPLIT_MANIFEST_DRAFTS_VALIDATED"
        or retail["scope_and_nonclaims"]["real_snapshot_or_split_manifest_present"]
        is not False
    ):
        raise ValidationError("Retail/dual-manifest boundary changed")

    f060 = loaded[
        "research/fixtures/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json"
    ]
    after = f060["count_transition"]["after"]
    if (
        f060["control_predicate"]
        != "RETAIL_F060_PARAMETERIZED_TEMPORAL_CUTOFF_WINDOW_RULE_FROZEN"
        or after
        != {
            "post_execution_closed": 0,
            "post_execution_open": 6,
            "pre_execution_closed": 8,
            "pre_execution_open": 158,
            "total_closed": 8,
            "total_open": 164,
        }
        or f060["f060_f061_separation"]["f061_value_selected_or_shadow_bound_by_package"]
        is not False
    ):
        raise ValidationError("F060/current-count boundary changed")


def _expected_b05_binding() -> Dict[str, Any]:
    return {
        "control_predicate": B05_CONTROL_PREDICATE,
        "control_predicate_value": True,
        "state": B05_STATE,
        "machine_record_sha256": B05_RECORD_SHA256,
        "bindings": [
            {
                "path": path,
                "role": role,
                "bytes": byte_count,
                "raw_sha256": digest,
            }
            for path, role, byte_count, digest in B05_INPUTS
        ],
        "closed_field_ids": ["F%03d" % index for index in range(7, 19)],
        "cannot_close": [
            "B05",
            "F114-F127",
            "F149",
            "EXECUTION",
            "R1",
            "R2",
            "C17",
            "FORMAL_TEST",
            "BLOCKER",
            "SCIENTIFIC_RESULT",
        ],
    }


def _validate_b05_inputs(
    workspace: Path, record: Mapping[str, Any]
) -> Mapping[str, Any]:
    if record.get("b05_binding") != _expected_b05_binding():
        raise ValidationError("B05 binding boundary changed")

    machine_record: Dict[str, Any] | None = None
    for path, _role, byte_count, digest in B05_INPUTS:
        payload = _stable_read(workspace, path)
        if len(payload) != byte_count or _sha256(payload) != digest:
            raise ValidationError(path + " B05 stopped bytes changed")
        if path.endswith("gate_a_b05_known_law_design_freeze_v1.json"):
            machine_record = _load_json(payload, path)

    if machine_record is None:
        raise ValidationError("B05 machine record was not loaded")
    if (
        machine_record.get("schema_version")
        != "heterodiff-manuscript-v3-gate-a-b05-known-law-design-freeze-v1"
        or machine_record.get("state") != B05_STATE
        or machine_record.get("control_predicate") != B05_CONTROL_PREDICATE
        or machine_record.get("record_sha256") != B05_RECORD_SHA256
        or _foreign_record_sha256(machine_record) != B05_RECORD_SHA256
    ):
        raise ValidationError("B05 machine state or semantic self-digest changed")
    expected_ids = ["F%03d" % index for index in range(7, 19)]
    closure = machine_record.get("all_or_nothing_closure")
    counts = machine_record.get("count_transition")
    effects = machine_record.get("project_effects_and_nonclaims")
    qualification = machine_record.get("qualification_boundary")
    if (
        type(closure) is not dict
        or closure.get("closed_field_ids") != expected_ids
        or closure.get("closed_count") != 12
        or closure.get("partial_credit_permitted") is not False
        or type(counts) is not dict
        or counts.get("after")
        != {
            "post_execution_closed": 0,
            "post_execution_open": 6,
            "pre_execution_closed": 20,
            "pre_execution_open": 146,
            "total_closed": 20,
            "total_open": 152,
        }
        or counts.get("blockers_open_after") != 12
        or counts.get("formal_tests_closed") != 0
        or counts.get("results_filled") != 0
        or type(effects) is not dict
        or effects.get("only_fields_closed") != expected_ids
        or effects.get("B05_remains_open") is not True
        or effects.get("F114_F127_and_F149_remain_open") is not True
        or effects.get("C17_remains_unproved") is not True
        or effects.get("formal_test_28_status") != "OPEN"
        or effects.get("formal_test_29_status") != "OPEN"
        or effects.get("formal_test_30_status") != "PENDING"
        or effects.get("result_or_claim_promoted") is not False
        or effects.get("scientific_execution_performed") is not False
        or effects.get("tracker_edit_performed") is not False
        or type(qualification) is not dict
        or qualification.get("exact_self_reference_only") is not True
        or qualification.get("nonzero_reference_perturbation_is_decision_candidate")
        is not False
    ):
        raise ValidationError("B05 all-or-nothing or nonclosure semantics changed")
    return machine_record


def _validate_successor_texts(workspace: Path) -> Dict[str, str]:
    digests: Dict[str, str] = {}
    for path, required in REQUIRED_TEXT.items():
        payload = _stable_read(workspace, path)
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValidationError(path + " is not UTF-8") from error
        normalized_text = " ".join(text.split())
        for token in required:
            if " ".join(token.split()) not in normalized_text:
                raise ValidationError(path + " lacks synchronized token: " + token)
        for marker in FORBIDDEN_AFFIRMATIVE_MARKERS:
            if marker in text:
                raise ValidationError(path + " contains forbidden current-route marker")
        if path.endswith("locked_route_successor_v1.md") and "\\mu_x=\\int" in text:
            raise ValidationError("raw unnormalized CKS formula reappeared in current Markdown")
        if path.endswith("locked_route_successor_v1.tex") and "\\mu_x=\\int" in text:
            raise ValidationError("raw unnormalized CKS formula reappeared in current TeX")
        if "fixed or atomic event times" in normalized_text.lower():
            raise ValidationError(
                path + " reintroduces superseded fixed/atomic event-time evidence"
            )
        digests[path] = _sha256(payload)
    return digests


def _validate_successor_bindings(
    workspace: Path, record: Mapping[str, Any]
) -> Dict[str, str]:
    roster = record.get("successor_file_roster")
    if type(roster) is not list or [row.get("path") for row in roster] != list(
        SUCCESSOR_PATHS
    ):
        raise ValidationError("seven-path successor roster changed")
    rows = {row["path"]: row for row in roster}

    for path, role, byte_count, digest in FROZEN_SUCCESSOR_NONVALIDATOR:
        if rows.get(path) != {
            "path": path,
            "role": role,
            "bytes": byte_count,
            "raw_sha256": digest,
        }:
            raise ValidationError(path + " frozen successor receipt changed")

    if rows.get(MACHINE_PATH) != {
        "path": MACHINE_PATH,
        "role": "CANONICAL_MACHINE_RECORD_SEMANTIC_SELF_BINDING",
        "bytes": None,
        "raw_sha256": None,
        "semantic_self_digest_field": "record_sha256",
    }:
        raise ValidationError("machine semantic self-binding changed")

    validator_path = SUCCESSOR_PATHS[5]
    validator_row = rows.get(validator_path)
    if (
        type(validator_row) is not dict
        or set(validator_row) != {"path", "role", "bytes", "raw_sha256"}
        or validator_row.get("path") != validator_path
        or validator_row.get("role") != "READ_ONLY_FINAL_VALIDATOR"
        or type(validator_row.get("bytes")) is not int
        or type(validator_row.get("raw_sha256")) is not str
    ):
        raise ValidationError("final validator binding shape changed")

    digests: Dict[str, str] = {}
    for row in roster:
        path = row["path"]
        if path == MACHINE_PATH:
            continue
        payload = _stable_read(workspace, path)
        digest = _sha256(payload)
        if len(payload) != row["bytes"] or digest != row["raw_sha256"]:
            raise ValidationError(path + " successor binding changed")
        digests[path] = digest
    return digests


def _validate_record_shape(record: Mapping[str, Any]) -> None:
    expected_keys = {
        "schema_version",
        "state",
        "binding_status",
        "package_kind",
        "target_predicate",
        "machine_binding_finalized",
        "successor_file_roster",
        "historical_predecessors",
        "settled_machine_inputs",
        "b05_binding",
        "semantic_projection",
        "one_way_supersession",
        "nonclaims",
        "record_sha256",
    }
    if set(record) != expected_keys:
        raise ValidationError("machine-record top-level roster changed")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine record semantic self-digest mismatch")
    if (
        record["schema_version"] != SCHEMA
        or record["state"] != STATE
        or record["binding_status"] != BINDING_STATUS
        or record["package_kind"]
        != "ADDITIVE_ONE_WAY_MANUSCRIPT_METHOD_DOMAIN_AND_CLAIM_LEDGER_SUCCESSOR"
        or record["machine_binding_finalized"] is not True
        or record["target_predicate"]
        != {
            "predicate_id": TARGET_PREDICATE,
            "value": True,
            "basis": "FINAL_AUDITED_B05_BOUND_AND_SEVEN_FILE_SUCCESSOR_QUALIFIED",
        }
    ):
        raise ValidationError("final state or target predicate changed")

    projection = record["semantic_projection"]
    expected_closed = ["F%03d" % index for index in range(7, 19)] + [
        "F060",
        "F106",
        "F107",
        "F108",
        "F113",
        "F128",
        "F129",
        "F148",
    ]
    if (
        projection.get("route_slots")
        != ["R1-A1", "R2-HYBRID", "R3-PHYS", "R4-RETAIL"]
        or projection.get("real_domains")
        != ["PHYSIONET_CHALLENGE_2012", "ONLINE_RETAIL_II"]
        or projection.get("alternate_route_or_domain_fallback_permitted") is not False
        or projection.get("c17_status") != "UNPROVED_REAL_DOMAIN_PROMOTION_NO_GO"
        or projection.get("cks_route")
        != "COUNT_PLUS_NORMALIZED_EVENT_MEAN_ORTHOGONAL_DIRECT_SUM_GAUSSIAN_PULLBACK"
        or projection.get("cks_exact_domain_instance_admitted") is not False
        or projection.get("novel_method_or_mechanism_claim_permitted") is not False
        or projection.get("empirical_contribution_component_count") != 14
        or projection.get("empirical_contribution_state") != "PENDING"
        or projection.get("mixed_cap1_clock")
        != "CONTINUOUS_TIME_EXPONENTIAL_CTMC_MATRIX_UNIFORMIZATION"
        or projection.get("mixed_cap2_role")
        != "THREE_DISJOINT_STRUCTURAL_SUBCASES_NON_SUBSTITUTIVE"
        or projection.get("current_closed_preexecution_fields") != expected_closed
        or projection.get("current_counts")
        != {
            "pre_execution_open": 146,
            "pre_execution_closed": 20,
            "post_execution_open": 6,
            "post_execution_closed": 0,
            "total_open": 152,
            "total_closed": 20,
            "blockers_open": 12,
            "formal_tests_closed": 0,
            "results_filled": 0,
        }
        or projection.get("formal_test_28") != "OPEN"
        or projection.get("formal_test_29") != "OPEN"
        or projection.get("formal_test_30") != "PENDING"
        or projection.get("r1_r2_scientific_result") != "NOT_RUN"
        or projection.get("r3_r4_domain_admission") != "ABSENT"
        or projection.get("tracker_is_input_or_output") is not False
    ):
        raise ValidationError("final semantic projection changed")

    if record["one_way_supersession"] != {
        "historical_files_mutated": False,
        "historical_validators_rebound": False,
        "successor_validator_reverse_binds_tracker": False,
        "conflicting_historical_current_route_text_is_authoritative": False,
        "successor_current_route_text_is_authoritative_after_final_predicate": True,
    }:
        raise ValidationError("one-way supersession boundary changed")

    expected_nonclaims = {
        "b05_closed",
        "c17_proved",
        "claim_promoted",
        "citation_refresh_completed",
        "data_or_test_outcome_accessed",
        "domain_admitted",
        "formal_test_closed",
        "network_or_external_contact_performed",
        "r1_or_r2_executed",
        "result_filled",
        "runtime_or_training_performed",
        "scientific_execution_performed",
        "submission_ready",
        "tracker_edited",
    }
    if (
        set(record["nonclaims"]) != expected_nonclaims
        or not all(value is False for value in record["nonclaims"].values())
    ):
        raise ValidationError("final nonclaim boundary changed")


def validate(workspace: Path | str) -> Dict[str, Any]:
    """Validate the final successor and its narrow synchronization predicate."""

    root = Path(workspace)
    machine_payload = _stable_read(root, MACHINE_PATH)
    record = _load_json(machine_payload, MACHINE_PATH)
    _validate_record_shape(record)
    loaded = _validate_bound_inputs(root, record)
    _validate_settled_semantics(loaded)
    _validate_b05_inputs(root, record)
    text_digests = _validate_successor_texts(root)
    successor_digests = _validate_successor_bindings(root, record)
    if any(successor_digests[path] != digest for path, digest in text_digests.items()):
        raise ValidationError("successor text digest recomposition changed")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "binding_status": BINDING_STATUS,
        "record_sha256": record["record_sha256"],
        "validation": "PASS",
        "target_predicate_id": TARGET_PREDICATE,
        "target_predicate_value": True,
        "b05_control_predicate": B05_CONTROL_PREDICATE,
        "b05_control_predicate_value": True,
        "effective_pre_execution_open": 146,
        "effective_post_execution_open": 6,
        "effective_unresolved_field_count": 152,
        "effective_closed_field_count": 20,
        "B05_closed": False,
        "historical_predecessors_byte_stable": True,
        "settled_machine_input_count": len(SETTLED_INPUTS),
        "b05_stopped_file_count": len(B05_INPUTS),
        "successor_raw_binding_count": len(SUCCESSOR_PATHS) - 1,
        "scientific_effect": 0,
        "tracker_effect": 0,
    }


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    print(json.dumps(validate(workspace), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "B05_INPUTS",
    "BINDING_STATUS",
    "MACHINE_PATH",
    "SCHEMA",
    "STATE",
    "TARGET_PREDICATE",
    "ValidationError",
    "record_sha256",
    "validate",
]
