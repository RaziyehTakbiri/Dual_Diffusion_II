"""Hostile checks for the dormant A1 R1 successor protocol freeze.

The suite performs no rank, training, scientific, production, entropy, network,
or child-process action.  Filesystem mutations are confined to pytest temp roots.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, Mapping

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.production import finite_association_r1_successor_adapter_v1 as ADAPTER
from research.production import (
    finite_association_r1_successor_authority_v1 as AUTHORITY,
)
from research.production import (
    finite_association_r1_successor_contracts_v1 as CONTRACTS,
)


SHA = lambda label: hashlib.sha256(label.encode("ascii")).hexdigest()


@pytest.fixture(autouse=True)
def _forbid_bytecode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "dont_write_bytecode", True)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _finish(record: Dict[str, Any], digest_key: str) -> Dict[str, Any]:
    body = dict(record)
    body[digest_key] = None
    record[digest_key] = hashlib.sha256(
        record["schema"].encode("ascii") + b"\0" + _canonical(body)
    ).hexdigest()
    return record


def _parse(cls: type, record: Dict[str, Any]) -> Any:
    return cls.parse(_canonical(record) + b"\n")


def _source_text(module_path: str) -> str:
    return (ROOT / module_path).read_text(encoding="utf-8")


def _copy_replica(tmp_path: Path) -> Path:
    replica = tmp_path / "workspace"
    machine = json.loads((ROOT / AUTHORITY.PREDECESSOR_MACHINE_PATH).read_text())
    snapshot = machine["qualification_snapshot"]
    source = snapshot["source_manifest"]
    paths = set(AUTHORITY.PREDECESSOR_RAW_SHA256)
    paths.add(source["registry_semantics"]["path"])
    paths.update(row["path"] for row in source["rows"])
    paths.update(
        row["path"]
        for row in source["deferred_runtime_boundary"]["deferred_source_rows"]
    )
    paths.update(row["path"] for row in source["nonpackage_candidate_inputs"])
    paths.update(row["path"] for row in snapshot["rosters"]["governance_custody"])
    paths.update(
        {
            AUTHORITY.HUMAN_PATH,
            AUTHORITY.MACHINE_PATH,
            AUTHORITY.CONTRACTS_PATH,
            AUTHORITY.AUTHORITY_PATH,
            AUTHORITY.ADAPTER_PATH,
            AUTHORITY.TEST_PATH,
        }
    )
    for relative_path in sorted(paths):
        target = replica / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, target)
    return replica.resolve()


def _binding_hashes(replica: Path, sidecar: Mapping[str, Any]) -> Dict[str, str]:
    return AUTHORITY._registration_binding_sha256s(
        replica, sidecar["registration_bindings"]
    )


def _write_marker(replica: Path, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    machine_payload = (replica / AUTHORITY.MACHINE_PATH).read_bytes()
    machine = json.loads(machine_payload)
    bindings = _binding_hashes(replica, machine)
    campaign_nonce = SHA("campaign-nonce")
    commitment = AUTHORITY._precreation_commitment(
        snapshot,
        registration_raw_sha256=hashlib.sha256(machine_payload).hexdigest(),
        registration_record_sha256=machine["record_sha256"],
        human_sha256=bindings["HUMAN_REGISTRATION"],
        test_sha256=bindings["HOSTILE_TEST"],
        campaign_nonce_sha256=campaign_nonce,
    )
    predecessor = snapshot["precreation_snapshot"]
    coordinates = predecessor["qualification_snapshot"]["coordinate_manifests"]
    record = {
        "schema": CONTRACTS.PRECREATION_ATTEMPT_MARKER_SCHEMA,
        "registration_raw_sha256": hashlib.sha256(machine_payload).hexdigest(),
        "registration_record_sha256": machine["record_sha256"],
        "predecessor_snapshot_sha256": predecessor["snapshot_sha256"],
        "source_capsule_manifest_sha256": snapshot["planned_source_capsule_manifest"][
            "capsule_manifest_sha256"
        ],
        "human_sha256": bindings["HUMAN_REGISTRATION"],
        "contracts_sha256": snapshot["implementation"]["contracts_sha256"],
        "authority_sha256": snapshot["implementation"]["authority_sha256"],
        "adapter_sha256": snapshot["implementation"]["adapter_sha256"],
        "test_sha256": bindings["HOSTILE_TEST"],
        "campaign_nonce_sha256": campaign_nonce,
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
        "contract_catalog_sha256": snapshot["contract_catalog"]["catalog_sha256"],
        "future_custody_path_roster_sha256": snapshot["activation_prerequisites"][
            "future_custody_path_roster_sha256"
        ],
        "precreation_plan_commitment_sha256": commitment[
            "precreation_plan_commitment_sha256"
        ],
        "all_future_roots_pristine_before_marker": True,
        "exclusive_create_completed": True,
        "attempt_state": "PRECREATION_ATTEMPT_SPENT_TERMINAL_NO_RETRY",
        "marker_sha256": None,
    }
    _finish(record, "marker_sha256")
    path = replica / AUTHORITY.PRECREATION_ATTEMPT_MARKER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(record) + b"\n")
    path.chmod(0o600)
    return record


def _runtime_chain(snapshot: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    capsule_sha = snapshot["planned_source_capsule_manifest"]["capsule_manifest_sha256"]
    candidate = _finish(
        {
            "schema": CONTRACTS.RUNTIME_CANDIDATE_SCHEMA,
            "target_profile_id": AUTHORITY.TARGET_PROFILE_ID,
            "capture_operation": "DOUBLE_CAPTURE_NO_SCIENTIFIC_COMPUTE",
            "capture_request_sha256": SHA("capture-request"),
            "capture_envelope_a_sha256": SHA("capture-a"),
            "capture_envelope_b_sha256": SHA("capture-b"),
            "runtime_manifest_preview_sha256": SHA("candidate-manifest-self"),
            "external_candidate_manifest_raw_sha256": SHA("candidate-manifest-raw"),
            "external_candidate_manifest_sha256": SHA("candidate-manifest-self"),
            "capsule_manifest_sha256": capsule_sha,
            "installed_files_manifest_sha256": SHA("installed-files"),
            "double_capture_stable": True,
            "complete_installed_file_verification": True,
            "scientific_compute_executed": False,
            "candidate_sha256": None,
        },
        "candidate_sha256",
    )
    review = _finish(
        {
            "schema": CONTRACTS.RUNTIME_REVIEW_SCHEMA,
            "target_profile_id": AUTHORITY.TARGET_PROFILE_ID,
            "candidate_sha256": candidate["candidate_sha256"],
            "candidate_raw_sha256": hashlib.sha256(
                _canonical(candidate) + b"\n"
            ).hexdigest(),
            "capsule_manifest_sha256": capsule_sha,
            "review_checks": {
                "candidate_hashes_recomputed": True,
                "capsule_hashes_recomputed": True,
                "complete_installed_file_verification": True,
                "double_capture_stable": True,
                "legacy_paths_absent": True,
                "no_scientific_compute": True,
            },
            "decision": "APPROVE",
            "operator_confirmation": True,
            "review_sha256": None,
        },
        "review_sha256",
    )
    runtime = snapshot["runtime_protocol"]
    implementation = snapshot["implementation"]
    approval = _finish(
        {
            "schema": CONTRACTS.RUNTIME_APPROVAL_SCHEMA,
            "target_profile_id": AUTHORITY.TARGET_PROFILE_ID,
            "candidate_sha256": candidate["candidate_sha256"],
            "review_sha256": review["review_sha256"],
            "fresh_recapture_envelope_sha256": SHA("fresh-recapture"),
            "final_runtime_manifest_sha256": SHA("approved-manifest-self"),
            "approved_runtime_manifest_raw_sha256": SHA("approved-manifest-raw"),
            "capsule_manifest_sha256": capsule_sha,
            "contracts_sha256": implementation["contracts_sha256"],
            "authority_sha256": implementation["authority_sha256"],
            "adapter_sha256": implementation["adapter_sha256"],
            "runtime_identity_source_sha256": runtime["external_loader_api"][
                "source_sha256"
            ],
            "runtime_identity_loader_api_sha256": runtime["external_loader_api"][
                "api_signature"
            ]["signature_sha256"],
            "runtime_capture_source_sha256": runtime["external_capture_validator_api"][
                "source_sha256"
            ],
            "runtime_capture_api_sha256": runtime["external_capture_validator_api"][
                "api_signature"
            ]["signature_sha256"],
            "approved": True,
            "limitations": list(AUTHORITY.RUNTIME_APPROVAL_LIMITATIONS),
            "approval_sha256": None,
        },
        "approval_sha256",
    )
    return (
        _parse(CONTRACTS.RuntimeCandidateV1, candidate),
        _parse(CONTRACTS.RuntimeReviewV1, review),
        _parse(CONTRACTS.RuntimeApprovalV1, approval),
    )


def _plan_activation(
    snapshot: Mapping[str, Any], transition: Mapping[str, str]
) -> tuple[Any, Any]:
    predecessor = snapshot["precreation_snapshot"]
    source = predecessor["qualification_snapshot"]["source_manifest"]
    coordinates = predecessor["qualification_snapshot"]["coordinate_manifests"]
    implementation = snapshot["implementation"]
    plan = _finish(
        {
            "schema": CONTRACTS.SUCCESSOR_PLAN_SCHEMA,
            "authority_domain": CONTRACTS.AUTHORITY_DOMAIN,
            "campaign_nonce_sha256": transition["campaign_nonce_sha256"],
            "initial_head_sha256": SHA("initial-head"),
            "precreation_plan_commitment_sha256": transition[
                "precreation_plan_commitment_sha256"
            ],
            "precreation_attempt_marker_raw_sha256": transition["marker_raw_sha256"],
            "precreation_attempt_marker_record_sha256": transition[
                "marker_record_sha256"
            ],
            "predecessor_registration_sha256": AUTHORITY.PREDECESSOR_RECORD_SHA256,
            "predecessor_snapshot_sha256": predecessor["snapshot_sha256"],
            "source_capsule_manifest_sha256": snapshot[
                "planned_source_capsule_manifest"
            ]["capsule_manifest_sha256"],
            "runtime_manifest_sha256": SHA("runtime-manifest"),
            "runtime_approval_sha256": SHA("runtime-approval"),
            "contracts_sha256": implementation["contracts_sha256"],
            "authority_sha256": implementation["authority_sha256"],
            "adapter_sha256": implementation["adapter_sha256"],
            "bootstrap_spec_sha256": snapshot["adapter_protocol"]["bootstrap_spec"][
                "bootstrap_spec_sha256"
            ],
            "protocol_registration_raw_sha256": transition["registration_raw_sha256"],
            "protocol_registration_record_sha256": transition[
                "registration_record_sha256"
            ],
            "protocol_test_sha256": transition["protocol_test_sha256"],
            "prerequisite_evidence_sha256": SHA("prerequisite-evidence"),
            "source_capsule_admission_sha256": SHA("capsule-admission"),
            "registry_raw_sha256": source["registry_semantics"]["raw_sha256"],
            "registry_record_sha256": source["registry_semantics"]["record_sha256"],
            "registry_semantic_sha256": coordinates["registry_sha256"],
            "exact_manifest_sha256": coordinates["manifests"]["exact"][
                "manifest_sha256"
            ],
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
            "phase_event_order": [
                "RANK",
                "EXACT",
                "PRIMARY",
                "PRIMARY_METRICS",
                "CONTROLS",
            ],
            "d1_disclosed_and_seed_1729_quarantined": True,
            "executable_preregistration_verified": False,
            "plan_sha256": None,
        },
        "plan_sha256",
    )
    activation = _finish(
        {
            "schema": CONTRACTS.SUCCESSOR_ACTIVATION_SCHEMA,
            "authority_domain": CONTRACTS.AUTHORITY_DOMAIN,
            "plan_sha256": plan["plan_sha256"],
            "campaign_nonce_sha256": plan["campaign_nonce_sha256"],
            "precreation_snapshot_sha256": predecessor["snapshot_sha256"],
            "precreation_plan_commitment_sha256": plan[
                "precreation_plan_commitment_sha256"
            ],
            "precreation_attempt_marker_raw_sha256": plan[
                "precreation_attempt_marker_raw_sha256"
            ],
            "precreation_attempt_marker_record_sha256": plan[
                "precreation_attempt_marker_record_sha256"
            ],
            "source_capsule_manifest_sha256": plan["source_capsule_manifest_sha256"],
            "runtime_manifest_sha256": plan["runtime_manifest_sha256"],
            "runtime_approval_sha256": plan["runtime_approval_sha256"],
            "contracts_sha256": plan["contracts_sha256"],
            "authority_sha256": plan["authority_sha256"],
            "adapter_sha256": plan["adapter_sha256"],
            "bootstrap_spec_sha256": plan["bootstrap_spec_sha256"],
            "protocol_registration_raw_sha256": plan[
                "protocol_registration_raw_sha256"
            ],
            "protocol_registration_record_sha256": plan[
                "protocol_registration_record_sha256"
            ],
            "protocol_test_sha256": plan["protocol_test_sha256"],
            "prerequisite_evidence_sha256": plan["prerequisite_evidence_sha256"],
            "source_capsule_admission_sha256": plan["source_capsule_admission_sha256"],
            "confirmatory_execution_blockers_remaining": 10,
            "executable_preregistration_verified": False,
            "d1_disclosure_verified": True,
            "seed_1729_quarantine_verified": True,
            "all_successor_roots_pristine": False,
            "activation_ready": False,
            "activation_sha256": None,
        },
        "activation_sha256",
    )
    return (
        _parse(CONTRACTS.SuccessorPlanV1, plan),
        _parse(CONTRACTS.SuccessorActivationV1, activation),
    )


def test_contract_catalog_is_exactly_22_closed_and_one_digest_each() -> None:
    catalog = CONTRACTS.contract_catalog()
    assert catalog["record_count"] == 22
    assert len(catalog["records"]) == len({row["schema"] for row in catalog["records"]})
    assert catalog["issued_record_count"] == 0
    assert catalog["one_terminal_digest_per_schema"] is True
    assert {row["contract_id"] for row in catalog["records"]} == set(
        CONTRACTS.CONTRACT_SPECS
    )
    assert "RUNTIME_MANIFEST" not in CONTRACTS.CONTRACT_SPECS
    loader_only = {
        row["contract_id"]
        for row in catalog["records"]
        if row["live_loader_only"] is True
    }
    assert loader_only == {"PREREQUISITE_EVIDENCE", "SOURCE_CAPSULE_ADMISSION"}
    for row in catalog["records"]:
        fields = row["fields"]
        assert len(fields) == len(set(fields))
        assert fields.count(row["digest_key"]) == 1


def test_loader_only_records_have_no_public_parser_route() -> None:
    for cls in (CONTRACTS.PrerequisiteEvidenceV1, CONTRACTS.SourceCapsuleAdmissionV1):
        with pytest.raises(TypeError, match="live loader"):
            cls.parse(b"{}\n")
        with pytest.raises(TypeError, match="parsed only"):
            cls()


def test_bootstrap_is_exact_and_rejects_semantically_rehashed_changes() -> None:
    record = ADAPTER.frozen_bootstrap_spec()
    assert record["interpreter_relative_path"] == ".venv-m1/bin/python"
    assert record["interpreter_flags"] == ["-P", "-B", "-S", "-X", "utf8"]
    assert "PYTHONPATH" not in record["environment"]
    assert "PYTHONHOME" not in record["environment"]
    assert record["environment_mode"] == "EXACT_REPLACEMENT_ALLOWLIST"
    assert record["environment_inheritance_permitted"] is False
    assert record["sys_path_order"][0].endswith("/protocol")
    assert all("authority" not in value for value in record["sys_path_order"])
    hostile = dict(record)
    hostile["interpreter_flags"] = ["-B"]
    _finish(hostile, "bootstrap_spec_sha256")
    with pytest.raises(CONTRACTS.ContractError):
        _parse(CONTRACTS.AdapterBootstrapSpecV1, hostile)
    hostile = dict(record)
    hostile["environment_inheritance_permitted"] = 0
    _finish(hostile, "bootstrap_spec_sha256")
    with pytest.raises(CONTRACTS.ContractError):
        _parse(CONTRACTS.AdapterBootstrapSpecV1, hostile)


def test_protocol_modules_are_read_only_and_have_closed_imports() -> None:
    paths = {
        "contracts": AUTHORITY.CONTRACTS_PATH,
        "authority": AUTHORITY.AUTHORITY_PATH,
        "adapter": AUTHORITY.ADAPTER_PATH,
    }
    allowed = {
        "__future__",
        "ast",
        "dataclasses",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "research",
        "stat",
        "typing",
        "research.production",
    }
    forbidden_calls = {
        "exec",
        "eval",
        "compile",
        "open",
        "system",
        "popen",
        "fork",
        "spawn",
        "run",
        "call",
        "check_call",
        "check_output",
        "urlopen",
        "token_bytes",
        "urandom",
    }
    for role, relative_path in paths.items():
        tree = ast.parse(_source_text(relative_path), filename=relative_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in allowed for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] in allowed
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert name not in forbidden_calls
        if role == "adapter":
            text = _source_text(relative_path)
            assert "successor_authority_v1" not in text
            assert "heterodiff." not in text
    assert ADAPTER.FUTURE_CAPSULE_CONTRACTS_COPY_PATH.startswith("protocol/")
    assert ADAPTER.FUTURE_CAPSULE_ADAPTER_COPY_PATH.startswith("protocol/")
    assert ADAPTER.FUTURE_CAPSULE_BOOTSTRAP_SPEC_COPY_PATH.endswith(".json")
    assert not hasattr(ADAPTER, "FUTURE_CAPSULE_AUTHORITY_COPY_PATH")


def test_stable_read_accepts_benign_sibling_churn_but_rejects_ancestor_rebind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custody = tmp_path / "custody"
    custody.mkdir()
    target = custody / "input.json"
    target.write_bytes(b"{}\n")
    original_read_bytes = Path.read_bytes
    churned = False

    def churn_sibling_directory(path: Path) -> bytes:
        nonlocal churned
        payload = original_read_bytes(path)
        if path == target and not churned:
            (tmp_path / "unrelated-sibling").mkdir()
            churned = True
        return payload

    monkeypatch.setattr(Path, "read_bytes", churn_sibling_directory)
    payload, _ = AUTHORITY._read_stable_file(target)
    assert payload == b"{}\n"
    assert churned is True

    rebound = tmp_path / "rebound"
    rebound.mkdir()
    rebound_target = rebound / "input.json"
    rebound_target.write_bytes(b"{}\n")
    rebound_once = False

    def replace_ancestor(path: Path) -> bytes:
        nonlocal rebound_once
        payload = original_read_bytes(path)
        if path == rebound_target and not rebound_once:
            rebound.rename(tmp_path / "rebound-old")
            rebound.mkdir()
            rebound_target.write_bytes(payload)
            rebound_once = True
        return payload

    monkeypatch.setattr(Path, "read_bytes", replace_ancestor)
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="ancestors changed"):
        AUTHORITY._read_stable_file(rebound_target)
    assert rebound_once is True

    real = tmp_path / "real"
    real.mkdir()
    (real / "input.json").write_bytes(b"{}\n")
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="symlink ancestor"):
        AUTHORITY._read_stable_file(linked / "input.json")


def test_live_precreation_snapshot_reopens_all_frozen_custody() -> None:
    snapshot = AUTHORITY.protocol_freeze_snapshot(ROOT)
    precreation = snapshot["precreation_snapshot"]
    custody = precreation["live_custody_verification"]
    assert custody["base_source_count"] == 45
    assert custody["deferred_runtime_source_count"] == 2
    assert custody["nonpackage_input_count"] == 3
    assert custody["governance_custody_count"] == 24
    assert custody["all_live_custody_reopened"] is True
    assert precreation["absence_path_count"] == 28
    assert snapshot["contract_catalog"]["record_count"] == 22
    assert (
        snapshot["activation_prerequisites"]["current_effective_unresolved_null_count"]
        == 172
    )
    assert snapshot["activation_prerequisites"]["current_open_blocker_count"] == 12
    assert snapshot["activation_prerequisites"]["current_activation_ready"] is False


def test_coordinate_manifests_and_seed_quarantine_are_exact() -> None:
    snapshot = AUTHORITY.protocol_freeze_snapshot(ROOT)
    coordinates = snapshot["precreation_snapshot"]["qualification_snapshot"][
        "coordinate_manifests"
    ]
    expected_registry = [
        4052249444591756,
        3253,
        5003,
        7411,
        10007,
        13007,
        16001,
        20011,
    ]
    assert coordinates["registry"] == expected_registry
    expected_counts = {
        "exact": 24,
        "primary": 48,
        "controls": 72,
        "complete_sampled": 120,
        "execution_phase_schedule": 144,
        "all_aggregate": 144,
    }
    for name, count in expected_counts.items():
        manifest = coordinates["manifests"][name]
        assert manifest["coordinate_count"] == count
        assert len(manifest["coordinates"]) == count
        assert all(row["seed"] != 1729 for row in manifest["coordinates"])
    first_seed_rows = {
        name: [
            row
            for row in coordinates["manifests"][name]["coordinates"]
            if row["seed_ordinal"] == 0
        ]
        for name in ("exact", "primary", "controls", "complete_sampled")
    }
    assert all(
        all(row["seed"] == expected_registry[0] for row in rows)
        for rows in first_seed_rows.values()
    )
    assert coordinates["exposed_seed"] == 1729


def test_event_ledger_formula_is_exact_and_transcript_entrypoints_refuse() -> None:
    protocol = AUTHORITY.frozen_event_ledger_protocol()
    ranges = protocol["global_authority_event_ranges"]
    assert ranges["RANK"] == {
        "authorization": 0,
        "request": 1,
        "completion": 2,
        "admission": 3,
    }
    assert ranges["EXACT"]["authorization"] == 4
    assert ranges["EXACT"]["aggregate_admission"] == 101
    assert ranges["PRIMARY"]["authorization"] == 102
    assert ranges["PRIMARY"]["aggregate_admission"] == 295
    assert ranges["PRIMARY_METRICS"] == {
        "authorization": 296,
        "request": 297,
        "completion": 298,
        "admission": 299,
    }
    assert ranges["CONTROLS"]["authorization"] == 300
    assert ranges["CONTROLS"]["aggregate_admission"] == 589
    assert protocol["next_unused_authority_event_ordinal"] == 590
    assert protocol["coordinate_event_formula"] == (
        "coordinate_phase_base + 4*phase_coordinate_ordinal + offset"
    )
    assert protocol["sequential_transcript_validator_enabled"] is False
    calls = (
        lambda: AUTHORITY.validate_phase_authorization(
            None,
            None,
            None,
            None,
            phase="RANK",
            previous_head_sha256=SHA("head"),
            prior_admission_sha256=None,
            authority_event_ordinal=0,
        ),
        lambda: AUTHORITY.validate_rank_chain(*([None] * 7)),
        lambda: AUTHORITY.validate_coordinate_chain(*([None] * 8)),
        lambda: AUTHORITY.validate_phase_aggregate(
            *([None] * 6),
            prior_phase_admission_sha256=None,
            primary_metrics_admission_sha256=None,
        ),
        lambda: AUTHORITY.validate_primary_metrics_chain(*([None] * 8)),
    )
    for call in calls:
        with pytest.raises(
            AUTHORITY.AuthorityProtocolError, match="not enabled|unavailable"
        ):
            call()


def test_runtime_wrapper_is_structural_only_and_rejects_changed_limitations() -> None:
    snapshot = AUTHORITY.protocol_freeze_snapshot(ROOT)
    candidate, review, approval = _runtime_chain(snapshot)
    result = AUTHORITY.validate_runtime_chain(candidate, review, approval, snapshot)
    assert result["runtime_admission_qualified"] is False
    assert result["external_runtime_files_reopened"] is False
    hostile = approval.to_record()
    hostile["limitations"] = ["THIS_APPROVES_PRODUCTION_EXECUTION"]
    _finish(hostile, "approval_sha256")
    parsed = _parse(CONTRACTS.RuntimeApprovalV1, hostile)
    with pytest.raises(AUTHORITY.AuthorityProtocolError):
        AUTHORITY.validate_runtime_chain(candidate, review, parsed, snapshot)
    candidate_hostile = candidate.to_record()
    candidate_hostile["scientific_compute_executed"] = 0
    _finish(candidate_hostile, "candidate_sha256")
    with pytest.raises(CONTRACTS.ContractError):
        _parse(CONTRACTS.RuntimeCandidateV1, candidate_hostile)


def test_d1_hashes_are_rejected_and_all_completion_levels_are_provisional() -> None:
    protocol = AUTHORITY.completion_evidence_protocol(ROOT)
    assert protocol["d1_execution_admissible"] is False
    assert protocol["exact_and_sampled_member_completions_are_provisional"] is True
    quarantine = protocol["d1_execution_lineage_quarantine"]
    assert quarantine["row_count"] > len(AUTHORITY.D1_FORBIDDEN_EVIDENCE_SHA256)
    values = {row["sha256"] for row in quarantine["rows"]}
    assert "008a0df7c67600932257991ddf5b69fa77fb9056b90f45ec280f45629ad89926" in values
    assert "f73a1a793aae93001d7537ddfdd44955d33bdc14ba37dbc397e056d67111d37d" in values
    assert (
        quarantine["roster_sha256"]
        == hashlib.sha256(
            AUTHORITY.D1_QUARANTINE_ROSTER_DOMAIN
            + _canonical(
                {
                    key: value
                    for key, value in quarantine.items()
                    if key != "roster_sha256"
                }
            )
        ).hexdigest()
    )
    for value in values:
        with pytest.raises(AUTHORITY.AuthorityProtocolError, match="not successor"):
            AUTHORITY._audit_value_against_quarantine({"nested": [value]}, values)
    assert AUTHORITY.audit_no_d1_evidence_replay({"safe": SHA("safe")}, ROOT) is True
    evidence_spec = CONTRACTS.CONTRACT_SPECS["COORDINATE_CONSUMPTION"]["fields"]
    evidence = next(row for row in evidence_spec if row[0] == "evidence_level")
    assert evidence[2] == (
        "PROVISIONAL_EXACT_MEMBER_COMPLETION",
        "PROVISIONAL_SAMPLED_MEMBER_LOADER_REVALIDATED",
    )


def test_precreation_commitment_is_acyclic_and_binds_exact_static_rosters() -> None:
    snapshot = AUTHORITY.protocol_freeze_snapshot(ROOT)
    protocol = snapshot["precreation_commitment_protocol"]
    assert protocol["final_plan_hash_is_not_a_marker_input"] is True
    assert protocol["post_marker_outcome_fields_are_null_in_commitment"] is True
    assert protocol["future_custody_paths"] == list(AUTHORITY.FUTURE_CUSTODY_PATHS)
    body_fields = protocol["commitment_body_fields"]
    assert "final_successor_plan_sha256" in body_fields
    assert "post_marker_runtime_manifest_sha256" in body_fields
    commitment = AUTHORITY._precreation_commitment(
        snapshot,
        registration_raw_sha256=SHA("registration-raw"),
        registration_record_sha256=SHA("registration-record"),
        human_sha256=SHA("human"),
        test_sha256=SHA("test"),
        campaign_nonce_sha256=SHA("campaign"),
    )
    assert commitment["body"]["final_successor_plan_sha256"] is None
    assert commitment["body"]["post_marker_runtime_approval_sha256"] is None
    changed = AUTHORITY._precreation_commitment(
        snapshot,
        registration_raw_sha256=SHA("registration-raw"),
        registration_record_sha256=SHA("registration-record"),
        human_sha256=SHA("human"),
        test_sha256=SHA("test"),
        campaign_nonce_sha256=SHA("different-campaign"),
    )
    assert (
        changed["precreation_plan_commitment_sha256"]
        != commitment["precreation_plan_commitment_sha256"]
    )


def test_transition_aware_loader_preserves_registration_after_marker(
    tmp_path: Path,
) -> None:
    replica = _copy_replica(tmp_path)
    pristine = AUTHORITY.load_dormant_protocol_qualification(replica)
    assert pristine.verification_mode == "LIVE_PRECREATION_ABSENCE"
    snapshot = pristine.snapshot()
    marker = _write_marker(replica, snapshot)
    created = replica / AUTHORITY.FUTURE_SUCCESSOR_ROOTS[1]
    created.mkdir(parents=True)
    superseded = AUTHORITY.load_dormant_protocol_qualification(replica)
    assert superseded.verification_mode == "BOUND_PRECREATION_ATTEMPT_SUPERSESSION"
    transition = superseded.snapshot()["live_transition_context"]
    assert transition["marker_record_sha256"] == marker["marker_sha256"]
    assert (
        transition["precreation_plan_commitment_sha256"]
        == marker["precreation_plan_commitment_sha256"]
    )
    marker_path = replica / AUTHORITY.PRECREATION_ATTEMPT_MARKER_PATH
    hostile = json.loads(marker_path.read_text())
    hostile["registry_semantic_sha256"] = SHA("wrong-registry")
    _finish(hostile, "marker_sha256")
    marker_path.write_bytes(_canonical(hostile) + b"\n")
    marker_path.chmod(0o600)
    with pytest.raises(AUTHORITY.AuthorityProtocolError):
        AUTHORITY.load_dormant_protocol_qualification(replica)


def test_static_plan_parser_crosslinks_marker_bootstrap_and_opaque_hash_slots(
    tmp_path: Path,
) -> None:
    replica = _copy_replica(tmp_path)
    pristine = AUTHORITY.load_dormant_protocol_qualification(replica)
    _write_marker(replica, pristine.snapshot())
    qualified = AUTHORITY.load_dormant_protocol_qualification(replica)
    snapshot = qualified.snapshot()
    transition = snapshot["live_transition_context"]
    plan, activation = _plan_activation(snapshot, transition)
    plan_row, activation_row = AUTHORITY._validate_plan(plan, activation, snapshot)
    assert (
        plan_row["bootstrap_spec_sha256"]
        == snapshot["adapter_protocol"]["bootstrap_spec"]["bootstrap_spec_sha256"]
    )
    assert activation_row["activation_ready"] is False
    assert snapshot["authority_protocol"]["plan_semantics_qualified"] is False
    assert snapshot["authority_protocol"]["activation_semantics_qualified"] is False
    hostile_plan = plan.to_record()
    hostile_plan["bootstrap_spec_sha256"] = SHA("hostile-bootstrap")
    _finish(hostile_plan, "plan_sha256")
    hostile_activation = activation.to_record()
    hostile_activation["plan_sha256"] = hostile_plan["plan_sha256"]
    hostile_activation["bootstrap_spec_sha256"] = hostile_plan["bootstrap_spec_sha256"]
    _finish(hostile_activation, "activation_sha256")
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="frozen context"):
        AUTHORITY._validate_plan(
            _parse(CONTRACTS.SuccessorPlanV1, hostile_plan),
            _parse(CONTRACTS.SuccessorActivationV1, hostile_activation),
            snapshot,
        )


def _materialize_capsule(replica: Path, snapshot: Mapping[str, Any]) -> Path:
    planned = snapshot["planned_source_capsule_manifest"]
    predecessor_source = snapshot["precreation_snapshot"]["qualification_snapshot"][
        "source_manifest"
    ]
    rules = {
        row["rule"]["path"]: row["rule"]
        for row in snapshot["precreation_snapshot"]["qualification_snapshot"][
            "overlay_rules"
        ]
    }
    capsule = replica / AUTHORITY.FUTURE_CAPSULE_ROOT
    capsule.mkdir(parents=True, mode=0o700)
    for row in planned["rows"]:
        payload = (replica / row["source_path"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row["raw_sha256"]:
            payload = AUTHORITY._apply_frozen_overlay(
                payload, rules[row["source_path"]]
            )
        assert hashlib.sha256(payload).hexdigest() == row["raw_sha256"]
        target = capsule / row["capsule_relative_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o600)
    protocol = {
        planned["contracts_copy_relative_path"]: (
            replica / AUTHORITY.CONTRACTS_PATH
        ).read_bytes(),
        planned["adapter_copy_relative_path"]: (
            replica / AUTHORITY.ADAPTER_PATH
        ).read_bytes(),
        planned["bootstrap_spec_copy_relative_path"]: (
            _canonical(ADAPTER.frozen_bootstrap_spec()) + b"\n"
        ),
    }
    for relative_path, payload in protocol.items():
        target = capsule / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o600)
    for path in [capsule, *[value for value in capsule.rglob("*") if value.is_dir()]]:
        path.chmod(0o700)
    assert len(predecessor_source["rows"]) == 45
    return capsule


def test_capsule_admission_loader_is_closed_world_and_parent_authority_is_excluded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replica = _copy_replica(tmp_path)
    pristine = AUTHORITY.load_dormant_protocol_qualification(replica)
    _write_marker(replica, pristine.snapshot())
    qualified = AUTHORITY.load_dormant_protocol_qualification(replica)
    capsule = _materialize_capsule(replica, qualified.snapshot())
    admission = AUTHORITY.load_source_capsule_admission(replica).to_record()
    assert admission["local_package_source_count"] == 47
    assert admission["nonpackage_input_count"] == 3
    assert admission["protocol_copy_count"] == 3
    assert admission["no_extra_files"] is True
    assert admission["planned_workspace_src_adapter_absent"] is True
    assert not (
        capsule
        / "protocol/research/production/finite_association_r1_successor_authority_v1.py"
    ).exists()
    extra = capsule / "protocol/extra.py"
    extra.write_bytes(b"pass\n")
    extra.chmod(0o600)
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="missing or extra"):
        AUTHORITY.load_source_capsule_admission(replica)
    extra.unlink()
    empty = capsule / "empty-extra-directory"
    empty.mkdir(mode=0o700)
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="missing or extra"):
        AUTHORITY.load_source_capsule_admission(replica)
    empty.rmdir()

    original = AUTHORITY._read_stable_file
    first = (
        capsule
        / qualified.snapshot()["planned_source_capsule_manifest"]["rows"][0][
            "capsule_relative_path"
        ]
    )
    seen_first = False
    swapped = False

    def swap_after_first_read(path: Path) -> tuple[bytes, Any]:
        nonlocal seen_first, swapped
        result = original(path)
        if path == first:
            seen_first = True
        elif seen_first and not swapped and capsule in path.parents:
            replacement = first.with_name(first.name + ".replacement")
            replacement.write_bytes(first.read_bytes())
            replacement.chmod(0o600)
            os.replace(replacement, first)
            swapped = True
        return result

    monkeypatch.setattr(AUTHORITY, "_read_stable_file", swap_after_first_read)
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="changed during audit"):
        AUTHORITY.load_source_capsule_admission(replica)
    assert swapped is True


def test_source_capsule_and_prerequisite_loaders_refuse_current_draft() -> None:
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="requires the bound"):
        AUTHORITY.load_source_capsule_admission(ROOT)
    with pytest.raises(AUTHORITY.AuthorityProtocolError, match="172 nulls"):
        AUTHORITY.load_prerequisite_evidence(ROOT)


def test_machine_registration_is_canonical_self_digested_and_live_bound() -> None:
    payload = (ROOT / AUTHORITY.MACHINE_PATH).read_bytes()
    record = json.loads(payload)
    assert payload == _canonical(record) + b"\n"
    body = dict(record)
    claimed = body["record_sha256"]
    body["record_sha256"] = None
    assert (
        hashlib.sha256(AUTHORITY.REGISTRATION_DOMAIN + _canonical(body)).hexdigest()
        == claimed
    )
    qualification = AUTHORITY.load_dormant_protocol_qualification(ROOT)
    assert qualification.record_sha256 == claimed
    assert qualification.verification_mode == "LIVE_PRECREATION_ABSENCE"
    assert record["qualification_snapshot"]["contract_catalog"]["record_count"] == 22
    assert record["nonclaims"] == AUTHORITY.NONCLAIMS
    status = AUTHORITY.status(ROOT)
    assert status["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert status["activation_ready"] is False
    assert status["execution_authorized"] is False


def test_human_registration_discloses_zero_execution_and_internal_boundary() -> None:
    text = (ROOT / AUTHORITY.HUMAN_PATH).read_text(encoding="utf-8")
    required = (
        "22",
        "172 unresolved null",
        "12 blockers",
        "zero execution",
        "precreation",
        "4052249444591756",
        "1729",
        "D1",
        "internal",
        "not executable",
        "publication-safe derivative",
    )
    for value in required:
        assert value.lower() in text.lower()
    assert "/Users/" not in text
    assert (
        "R1_A1_SUCCESSOR_RUNTIME_ADMISSION_ADAPTER_AUTHORITY_AND_TYPED_CUSTODY_PROTOCOL_FROZEN_ZERO_EXECUTION_ACTIVATION_DEFERRED_NOT_EXECUTABLE"
        in text
    )


def test_no_successor_outputs_runtime_files_or_pyc_exist() -> None:
    paths = [
        AUTHORITY.PRECREATION_ATTEMPT_MARKER_PATH,
        *AUTHORITY.FUTURE_SUCCESSOR_ROOTS,
        *AUTHORITY.SUCCESSOR_RUNTIME_CUSTODY_PATHS.values(),
        AUTHORITY.FUTURE_EXECUTABLE_PREREGISTRATION_PATH,
        AUTHORITY.FUTURE_EXECUTABLE_PREREGISTRATION_FREEZE_RECEIPT_PATH,
        ADAPTER.PERMANENTLY_ABSENT_LEGACY_PLANNED_SRC_TARGET,
    ]
    for relative_path in paths:
        with pytest.raises(FileNotFoundError):
            (ROOT / relative_path).lstat()
    focused = (
        "finite_association_r1_successor_contracts_v1",
        "finite_association_r1_successor_authority_v1",
        "finite_association_r1_successor_adapter_v1",
        "test_manuscript_v3_a1_r1_successor_runtime_adapter_authority_protocol_freeze_v1",
    )
    for path in ROOT.rglob("*.pyc"):
        assert not any(name in path.name for name in focused)
