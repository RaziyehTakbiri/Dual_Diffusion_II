from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Tuple


_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_PATH = _ROOT / (
    "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json"
)
_CHECKLIST_PATH = _ROOT / (
    "research/preregistrations/"
    "cp76_manuscript_v3_submission_readiness_checklist_v1.md"
)


def _no_duplicate_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _load_manifest() -> Tuple[bytes, Dict[str, Any]]:
    raw = _MANIFEST_PATH.read_bytes()
    decoded = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_object)
    assert isinstance(decoded, dict)
    return raw, decoded


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _walk(value: object) -> Iterable[object]:
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _assert_file_row(row: Dict[str, Any]) -> None:
    raw = (_ROOT / row["path"]).read_bytes()
    assert len(raw) == row["bytes"]
    assert raw.count(b"\n") == row["lf_count"]
    assert _sha256(raw) == row["sha256"]


def _markdown_local_support_names(text: str) -> List[str]:
    return re.findall(r"\]\(([^\s)#?]+\.md)(?:[?#][^)]*)?\)", text)


def _tex_local_support_names(text: str) -> List[str]:
    return re.findall(r"\\supportingfile\{[^}]*\}\{([^}]+\.md)\}", text)


def _submission_identity_findings(markdown_text: str, tex_text: str) -> List[str]:
    findings = []
    if markdown_text.count("> **Authors:** withheld in this working draft") != 1:
        findings.append("markdown-author-placeholder")
    if tex_text.count(r"\author{Authors withheld in this working draft}") != 1:
        findings.append("tex-author-placeholder")
    if tex_text.count("pdfauthor={Authors withheld in this working draft}") != 1:
        findings.append("pdf-author-placeholder")

    combined = markdown_text + "\n" + tex_text
    patterns = {
        "email-address": r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "orcid": r"(?i)\bORCID\b|\b\d{4}-\d{4}-\d{4}-[\dX]{4}\b",
        "unix-local-path": r"/(?:Users|home)/[^\s`{}]+|/private/tmp/[^\s`{}]+",
        "windows-local-path": r"(?i)\b[A-Z]:\\Users\\[^\s`{}]+",
        "tex-identity-field": (
            r"(?i)\\(?:affiliation|institute|institution|email|thanks)\s*\{"
        ),
    }
    for finding_id, pattern in patterns.items():
        if re.search(pattern, combined):
            findings.append(finding_id)
    return findings


def test_cp76_manifest_is_canonical_and_narrowly_not_ready() -> None:
    raw, manifest = _load_manifest()
    assert _sha256(raw) == (
        "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06"
    )
    assert raw == _canonical_json_bytes(manifest)
    assert not raw.endswith(b"\n")
    assert not any(isinstance(item, float) for item in _walk(manifest))

    assert manifest["schema_version"] == (
        "cp76-manuscript-v3-submission-readiness-audit-v1"
    )
    assert manifest["scope"] == "MANUSCRIPT_SUBMISSION_ONLY"
    assert manifest["audit_definition_valid"] is True
    assert manifest["snapshot_assessed"] is True
    assert manifest["readiness_status"] == "NOT_READY"
    assert manifest["manuscript_submission_disposition"] == ("NOT_READY_FOR_SUBMISSION")
    assert manifest["manuscript_submission_ready"] is False
    assert manifest["manifest_path"] == (
        "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json"
    )

    assert [
        (row["id"], row["state"], row["blocking"])
        for row in manifest["readiness_criteria"]
    ] == [
        ("claim-evidence-map-current", "BLOCKED", True),
        ("method-definition-frozen", "BLOCKED", True),
        ("novelty-independently-assessed", "BLOCKED", True),
        ("confirmatory-task-admitted", "BLOCKED", True),
        ("execution-preregistered", "BLOCKED", True),
        ("result-slots-executed", "BLOCKED", True),
        ("support-inventory-complete", "BLOCKED", True),
        ("clean-room-reproduction-complete", "NOT_STARTED", True),
        ("venue-and-anonymity-audit-complete", "BLOCKED", True),
        ("findings-dispositioned", "NOT_STARTED", True),
    ]

    expected_top_keys = {
        "audit_definition_valid",
        "checklist",
        "claim_ledger_observation",
        "cp75_bundle_pins",
        "cp75_effects",
        "direct_manuscript_support_inventory",
        "historical_artifacts",
        "manifest_path",
        "manuscript_inputs",
        "manuscript_submission_disposition",
        "manuscript_submission_ready",
        "marker_observations",
        "production_state_preserved",
        "readiness_criteria",
        "readiness_status",
        "schema_version",
        "scope",
        "snapshot_assessed",
        "submission_artifact_gaps",
        "supersession",
    }
    assert set(manifest) == expected_top_keys

    checklist = _CHECKLIST_PATH.read_bytes()
    checklist_row = manifest["checklist"]
    assert len(checklist) == checklist_row["bytes"]
    assert checklist.count(b"\n") == checklist_row["lf_count"]
    assert checklist.endswith(b"\n") is checklist_row["terminal_lf"]
    assert _sha256(checklist) == checklist_row["sha256"]
    checklist_text = checklist.decode("utf-8")
    for literal in (
        "NOT_READY",
        "MANUSCRIPT_SUBMISSION_ONLY",
        "CP75 artifacts are not invalidated",
        "all 17 production gates remain `MISSING`",
        "Passing the focused CP76 unit test proves only",
    ):
        assert literal in checklist_text


def test_cp76_preserves_exact_v26_cp75_and_manuscript_bytes() -> None:
    _, manifest = _load_manifest()
    historical = manifest["historical_artifacts"]
    manuscript = manifest["manuscript_inputs"]
    assert len(historical) == 14
    assert len(manuscript) == 6
    assert [row["artifact_id"] for row in historical[:2]] == [
        "final-v26-protocol",
        "final-v26-machine-manifest",
    ]
    assert [row["artifact_id"] for row in historical[2:6]] == [
        "cp75-authoritative-source",
        "cp75-authoritative-test",
        "cp75-independent-source",
        "cp75-independent-test",
    ]
    for row in historical + manuscript:
        _assert_file_row(row)

    supersession = manifest["supersession"]
    assert supersession == {
        "cp75_artifacts_invalidated": False,
        "cp75_external_response_workflow_advisory_only_for_manuscript_submission": True,
        "cp75_external_response_workflow_superseded_as_manuscript_submission_prerequisite": True,
        "cp75_history_unchanged": True,
        "cp75_required_for_manuscript_submission": False,
        "cp75_superseded_for_production_governance": False,
        "cp75_workflow_revoked": False,
        "formal_test_28_state_changed": False,
        "historical_v26_required_evidence_unchanged": True,
        "production_gate_or_blocker_state_changed": False,
        "production_requirements_changed": False,
        "supersession_scope": "MANUSCRIPT_SUBMISSION_ONLY",
        "v26_history_mutated": False,
    }


def test_cp76_claim_status_result_and_marker_projection_matches_snapshot() -> None:
    _, manifest = _load_manifest()
    observation = manifest["claim_ledger_observation"]
    ledger_text = (_ROOT / "manuscript_v3/claim_ledger.md").read_text("utf-8")

    claim_rows = []
    for match in re.finditer(
        r"^\| (C\d+) \|.*?\| \*\*(.*?)\*\* \|", ledger_text, re.MULTILINE
    ):
        claim_rows.append([match.group(1), match.group(2)])
    assert claim_rows == observation["claim_rows"]
    assert len(claim_rows) == observation["claim_row_count"] == 21
    assert [row[0] for row in claim_rows] == [f"C{ordinal}" for ordinal in range(21)]
    assert len({row[0] for row in claim_rows}) == len(claim_rows)
    assert observation["promoted_empirical_result_claim_count"] == 0

    evidence_match = re.search(
        r"^\| E29-REF \|.*?\| \*\*(.*?)\*\* \|.*?\|.*?\| (.*?) \|$",
        ledger_text,
        re.MULTILINE,
    )
    assert evidence_match is not None
    assert evidence_match.group(1) == "PASS WITH EXPLICIT SCOPE LIMITS"
    assert "No C-row or R-slot promotion" in evidence_match.group(2)
    assert observation["engineering_evidence_row"] == {
        "id": "E29-REF",
        "promotion_effect": "NONE",
        "status": "PASS WITH EXPLICIT SCOPE LIMITS",
    }

    result_slots = []
    for line in ledger_text.splitlines():
        if line.startswith("| R") or line.startswith("| F1-TIME"):
            fields = [field.strip() for field in line.strip().strip("|").split("|")]
            if fields[0] in {
                "R1-A1",
                "R2-HYBRID",
                "R3-PHYS",
                "R4-RETAIL",
                "R5-ASAP",
                "F1-TIME",
            }:
                result_slots.append(
                    {
                        "id": fields[0],
                        "result_cell": fields[-2],
                        "status": fields[-1].replace("**", ""),
                    }
                )
    assert result_slots == observation["result_slots"]

    marker_observations = manifest["marker_observations"]
    assert [row["path"] for row in marker_observations] == [
        "manuscript_v3/manuscript_v3.md",
        "manuscript_v3/manuscript_v3.tex",
    ]
    for marker_row in marker_observations:
        text = (_ROOT / marker_row["path"]).read_text("utf-8")
        for marker, expected_count in marker_row["counts"].items():
            assert text.count(marker) == expected_count
        assert text.count("PENDING") == marker_row["pending_substring_count"]
        listed_pending = sum(
            count
            for marker, count in marker_row["counts"].items()
            if marker != "THEOREM-TARGET"
        )
        assert listed_pending == marker_row["total_listed_pending_markers"] == 25
        assert marker_row["unresolved_theorem_target_count"] == 4


def test_cp76_missing_support_and_submission_gap_projection_is_fail_closed() -> None:
    _, manifest = _load_manifest()
    support = manifest["direct_manuscript_support_inventory"]
    assert support["referenced_unique_count"] == 10
    assert support["present_unique_count"] == 2
    assert support["missing_unique_count"] == 8
    assert all((_ROOT / path).is_file() for path in support["present_paths"])
    # CP76 is an immutable assessment of the workspace snapshot that existed
    # when it was issued.  Later publication work may resolve a path that this
    # historical manifest correctly recorded as missing, so do not turn the
    # snapshot into a perpetual absence assertion.
    assert len(set(support["missing_paths"])) == support["missing_unique_count"]
    assert all(not Path(path).is_absolute() for path in support["missing_paths"])

    missing_names = [Path(path).name for path in support["missing_paths"]]
    for source, expected_occurrences in support["missing_link_occurrences_by_source"]:
        text = (_ROOT / source).read_text("utf-8")
        assert sum(text.count(name) for name in missing_names) == expected_occurrences

    gaps = manifest["submission_artifact_gaps"]
    assert gaps["anonymity_scan_scope"] == "manuscript_v3/*.md"
    assert gaps["submission_route"] == "UNSELECTED"
    assert gaps["venue_template_deferred"] is True
    assert gaps["submission_include_exclude_roster_frozen"] is False
    assert gaps["submission_pdf_exists"] is False
    assert not (_ROOT / gaps["submission_pdf_path"]).exists()
    assert gaps["checkpoint_description_synchronized"] is False

    stub = gaps["invalid_stub_artifact"]
    _assert_file_row(stub)
    assert (_ROOT / stub["path"]).read_bytes() == b"identity-13\n"
    assert stub["substantive_evidence"] is False

    absolute_path_files = []
    for path in sorted((_ROOT / "manuscript_v3").glob("*.md")):
        text = path.read_text("utf-8")
        if "/Users/mahtab" in text or "/private/tmp" in text:
            absolute_path_files.append(path.relative_to(_ROOT).as_posix())
    assert absolute_path_files == gaps["manuscript_markdown_absolute_local_path_files"]
    assert (
        len(absolute_path_files)
        == gaps["manuscript_markdown_absolute_local_path_file_count"]
        == 6
    )
    assert gaps["verification_archive_identifiers_present"] is True

    tex = (_ROOT / "manuscript_v3/manuscript_v3.tex").read_text("utf-8")
    readme = (_ROOT / "manuscript_v3/README.md").read_text("utf-8")
    ledger = (_ROOT / "manuscript_v3/claim_ledger.md").read_text("utf-8")
    assert "Six incremental layers" in tex
    assert "forty-nine checkpoints" in ledger
    assert "first forty-nine checkpoints" in readme
    assert "venue template intentionally deferred" in readme


def test_cp76_support_inventory_and_anonymity_oracles_are_fail_closed() -> None:
    _, manifest = _load_manifest()
    markdown_text = (_ROOT / "manuscript_v3/manuscript_v3.md").read_text("utf-8")
    tex_text = (_ROOT / "manuscript_v3/manuscript_v3.tex").read_text("utf-8")

    expected_support_names = [
        "executable_method_spec.md",
        "configuration_reference_code_audit.md",
        "reversible_hybrid_reference_code_audit.md",
        "reverse_energy_objective_code_audit.md",
        "association_observation_code_audit.md",
        "association_preconditioner_code_audit.md",
        "configuration_energy_code_audit.md",
        "novelty_audit_matrix.md",
        "claim_ledger.md",
        "execution_preregistration.md",
        "executable_method_spec.md",
        "executable_method_spec.md",
        "executable_method_spec.md",
        "executable_method_spec.md",
        "executable_method_spec.md",
        "execution_preregistration.md",
    ]
    markdown_support_names = _markdown_local_support_names(markdown_text)
    tex_support_names = _tex_local_support_names(tex_text)
    assert markdown_support_names == expected_support_names
    assert tex_support_names == expected_support_names

    support = manifest["direct_manuscript_support_inventory"]
    manifest_support_names = {
        Path(path).name for path in support["present_paths"] + support["missing_paths"]
    }
    assert set(expected_support_names) == manifest_support_names
    assert len(manifest_support_names) == support["referenced_unique_count"] == 10

    assert _submission_identity_findings(markdown_text, tex_text) == []
    hostile_cases = [
        (
            markdown_text.replace(
                "Authors:** withheld in this working draft",
                "Authors:** Example Researcher",
                1,
            ),
            tex_text,
            "markdown-author-placeholder",
        ),
        (
            markdown_text,
            tex_text.replace(
                r"\author{Authors withheld in this working draft}",
                r"\author{Example Researcher}",
                1,
            ),
            "tex-author-placeholder",
        ),
        (
            markdown_text,
            tex_text.replace(
                "pdfauthor={Authors withheld in this working draft}",
                "pdfauthor={Example Researcher}",
                1,
            ),
            "pdf-author-placeholder",
        ),
        (markdown_text + "\ncontact@example.edu\n", tex_text, "email-address"),
        (markdown_text + "\nORCID 0000-0002-1825-0097\n", tex_text, "orcid"),
        (
            markdown_text + "\n/Users/reviewer/private/draft.md\n",
            tex_text,
            "unix-local-path",
        ),
        (
            markdown_text + "\nC:\\Users\\reviewer\\private\\draft.md\n",
            tex_text,
            "windows-local-path",
        ),
        (
            markdown_text,
            tex_text + "\n" + r"\affiliation{Example University}" + "\n",
            "tex-identity-field",
        ),
    ]
    for hostile_markdown, hostile_tex, expected_finding in hostile_cases:
        assert expected_finding in _submission_identity_findings(
            hostile_markdown, hostile_tex
        )


def test_cp76_production_and_cp75_no_effect_state_is_unchanged() -> None:
    _, manifest = _load_manifest()
    v26 = json.loads(
        (_ROOT / "research/fixtures/cp50_test28_mixed_initializer_v26.json").read_text(
            "utf-8"
        )
    )
    state = manifest["production_state_preserved"]
    assert v26["draft_blocker_status_counts"] == {
        "missing": state["draft_blocker_missing_count"],
        "satisfied": state["draft_blocker_satisfied_count"],
        "total": state["draft_blocker_total_count"],
    }
    missing = [
        blocker_id
        for blocker_id, row in v26["draft_blockers"].items()
        if row["state"] == "MISSING"
    ]
    assert missing == state["missing_draft_blocker_ids"]
    assert v26["confirmatory_execution_authorized"] is False
    assert v26["lifecycle"]["current_state"] == state["lifecycle_state"]
    assert v26["protocol_state"] == state["protocol_state"]
    assert v26["formal_test_28"]["status"] == state["formal_test_28_status"]

    request = json.loads(
        (
            _ROOT / "research/fixtures/"
            "cp75_test28_production_schema_acceptance_review_request_v1.json"
        ).read_text("utf-8")
    )
    assert (
        request["production_gate_states"]
        == ["MISSING"] * state["production_gate_count"]
    )
    assert request["draft_blocker_states"] == ["MISSING"] * 4
    assert request["formal_test_28_status"] == "OPEN"

    effects = manifest["cp75_effects"]
    for key, value in effects.items():
        source_key = {
            "candidate_descriptor_review_outcome": (
                "current_candidate_descriptor_review_outcome"
            ),
            "production_executable_schema_review_outcome": (
                "current_production_executable_schema_review_outcome"
            ),
        }.get(key, key)
        assert request[source_key] == value


def test_cp76_live_cp75_bundle_pins_remain_exact() -> None:
    from heterodiff.evaluation.mixed_initializer_test28_independent_production_schema_acceptance_review_response_validator import (
        cp75_build_independent_review_response_validator_bundle,
        cp75_independent_canonical_json_bytes,
        cp75_independent_public_record_sha256,
        cp75_independent_record_sha256,
    )
    from heterodiff.evaluation.mixed_initializer_test28_production_schema_acceptance_review_request import (
        cp75_build_production_schema_acceptance_review_request_bundle,
        cp75_canonical_json_bytes,
        cp75_public_record_sha256,
        cp75_record_sha256,
    )

    _, manifest = _load_manifest()
    pins = manifest["cp75_bundle_pins"]

    authoritative = cp75_build_production_schema_acceptance_review_request_bundle()
    authoritative_bytes = cp75_canonical_json_bytes(authoritative)
    assert {
        "canonical_json_bytes": len(authoritative_bytes),
        "canonical_json_sha256": _sha256(authoritative_bytes),
        "public_sha256": cp75_public_record_sha256(authoritative),
        "record_sha256": cp75_record_sha256(authoritative),
    } == pins["authoritative_request_bundle"]

    independent = cp75_build_independent_review_response_validator_bundle()
    independent_bytes = cp75_independent_canonical_json_bytes(independent)
    assert {
        "canonical_json_bytes": len(independent_bytes),
        "canonical_json_sha256": _sha256(independent_bytes),
        "public_sha256": cp75_independent_public_record_sha256(independent),
        "record_sha256": cp75_independent_record_sha256(independent),
    } == pins["independent_validator_bundle"]
