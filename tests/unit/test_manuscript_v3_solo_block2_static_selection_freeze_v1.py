"""Hostile tests for the Solo Block 2 static selection package.

All mutation and materialization tests use pytest temporary directories.  The
canonical validator is read-only and imports no scientific project module.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, List, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/" "manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)
TEST_REL = Path(
    "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)
EXPECTED_AUTHORITY_TEXT = (
    "Alright, sounds good. I think that the next step is to cover the second "
    "week's tasks."
)


def _load_validator() -> ModuleType:
    path = ROOT / VALIDATOR_REL
    spec = importlib.util.spec_from_file_location(
        "solo_block2_static_selection_validator", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _closed_read_roster(module: ModuleType) -> List[str]:
    return [
        module.HUMAN_PATH,
        module.MACHINE_PATH,
        module.VALIDATOR_PATH,
        module.TEST_PATH,
        *[row["path"] for row in module.LIVE_IMMUTABLE_BINDINGS],
    ]


def _assert_not_canonical_write_target(path: Path) -> None:
    candidate = path.resolve(strict=False)
    canonical_root = ROOT.resolve()
    assert candidate != canonical_root
    assert canonical_root not in candidate.parents


def _copy_closed_roster(module: ModuleType, tmp_path: Path) -> Path:
    for relative in _closed_read_roster(module):
        source = ROOT / relative
        target = tmp_path / relative
        _assert_not_canonical_write_target(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    _assert_not_canonical_write_target(path)
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = module.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _replace(record: Dict[str, Any], path: str, value: Any) -> None:
    current: Any = record
    tokens = path.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def _mutation(path: str, value: Any) -> Callable[[Dict[str, Any]], None]:
    return lambda record: _replace(record, path, value)


def _flip_first_byte(path: Path) -> None:
    _assert_not_canonical_write_target(path)
    raw = path.read_bytes()
    assert raw
    replacement = bytes([raw[0] ^ 1]) + raw[1:]
    path.write_bytes(replacement)
    path.chmod(0o644)


def test_canonical_package_validates_exact_static_effects(
    validator: ModuleType,
) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "static_design_control_predicate": True,
        "theory_route_selection_frozen": True,
        "metric_route_selection_frozen": True,
        "method_gap_inventory_frozen": True,
        "static_precontact_protocol_design_frozen": True,
        "dataset_source_license_governance_or_access_requests_opened_by_package": False,
        "validator_and_tests_network_access": False,
        "primary_literature_lookup_performed_by_root": True,
        "global_external_request_absence_independently_verified": False,
        "populated_instance_present": False,
        "external_contact_authorized": False,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "formal_tests_closed": 0,
        "result_slots_filled": 0,
        "effective_unresolved_field_count": 172,
        "effective_open_blocker_count": 12,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_exact_visible_authority_and_agent_interpretation_are_bound(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == EXPECTED_AUTHORITY_TEXT
    assert (
        authority["normalized_visible_text_sha256"]
        == hashlib.sha256(EXPECTED_AUTHORITY_TEXT.encode("utf-8")).hexdigest()
    )
    assert authority["raw_transport_bytes_bound"] is False
    assert authority["conversation_envelope_bound"] is False
    assert authority["user_selected_file_paths_or_count"] is False
    assert authority["user_selected_route_values"] is False
    assert authority["agent_selected_route_values"] is True
    assert (
        authority["solo_block2_label_and_sw3_to_sw4_mapping_is_agent_interpretation"]
        is True
    )
    assert authority["user_selected_solo_block2_label_or_calendar_mapping"] is False
    assert authority["agent_selected_bounded_file_count"] == 4
    assert (
        authority["ordinary_software_qualification_interpreter_processes_performed"]
        is True
    )
    assert authority["pytest_temporary_fixtures_used"] is True
    assert authority["temporary_name_randomness_absence_claimed"] is False
    assert authority["authority_or_runtime_child_launched"] is False
    assert authority["scientific_seed_or_protocol_entropy_consumed"] is False
    assert authority["canonical_operational_or_scientific_effect"] is False


def test_exact_c17_support_and_cks_nonclaims(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    c17 = record["c17_selection"]
    support = record["common_support_selection"]
    cks = record["cks_selection"]
    assert c17["route"] == ("FORK_B_DIRECT_SIMULTANEOUS_TARGET_OCCUPATION_CERTIFICATES")
    assert c17["orientation"] == "KL(P_H || P_HHAT)_TARGET_FIRST"
    assert c17["c17_proved"] is False
    assert c17["c17_claim_promoted"] is False
    assert support["policy"] == (
        "ACQUISITION_JUSTIFIED_POSITIVE_DOMINATED_MIXTURE_WITH_SHARED_BASE_"
        "STRUCTURAL_ZEROS_AND_FAIL_CLOSED_NONADMISSION"
    )
    assert support["physionet_route_verified"] is False
    assert support["retail_route_verified"] is False
    assert cks["route_status"] == "CKS_PROOF_ROUTE_SELECTED_FOR_DEVELOPMENT"
    assert cks["cks_characteristicness_proved"] is False
    assert cks["cks_proof_complete"] is False
    assert cks["primary_metric_selected"] is False
    assert cks["primary_metric_proof_gate_passed"] is False
    obligations = cks["count_and_signed_measure_obligations"]
    assert len(obligations) == 12
    assert (
        "EVERY_NONZERO_ADMISSIBLE_FINITE_SIGNED_DIFFERENCE_MEASURE_DETECTED"
        in obligations
    )
    assert "EMPTY_CONFIGURATION_IDENTIFIED_SEPARATELY" in obligations
    assert "EVENT_MULTIPLICITIES_RETAINED" in obligations


def test_literature_lookup_provenance_is_narrow_and_not_a_proof(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    boundary = record["external_observation_boundary"]
    assert boundary["kernel_theory_literature_lookup_performed"] is True
    assert boundary["lookup_preceded_package"] is True
    assert boundary["prospective_seal_preceded_kernel_theory_lookup"] is True
    assert boundary["lookup_vs_seal_chronology_provenance"] == (
        "ORCHESTRATION_ORDERING_NOT_INDEPENDENT_TIMESTAMP_ATTESTATION"
    )
    assert boundary["exact_wall_clock_lookup_timestamp_bound"] is False
    assert boundary["lookup_authority_source"] == (
        "USER_RESEARCH_REQUEST_PLUS_SYSTEM_NICHE_FACT_BROWSE_RULE"
    )
    assert boundary["lookup_provenance_strength"] == (
        "ORCHESTRATION_DISCLOSURE_NOT_INDEPENDENT_NETWORK_AUDIT"
    )
    assert boundary["registered_targets_are_complete_http_request_roster"] is False
    assert boundary["exact_http_or_search_request_count_known"] is False
    assert boundary["remote_response_receipts_bound"] is False
    assert boundary["remote_scholarly_bytes_bound"] is False
    assert boundary["registered_dataset_source_contact_performed"] is False
    assert boundary["license_governance_access_request_performed"] is False
    assert boundary["protected_data_or_outcome_accessed"] is False
    assert boundary["global_network_absence_claimed"] is False
    assert boundary["prospective_seal_literal_scope_ambiguity_acknowledged"] is True
    assert boundary["independent_seal_compliance_adjudication_performed"] is False
    assert boundary["lookup_declared_seal_compliant"] is False
    assert boundary["lookup_declared_seal_violation"] is False
    assert boundary["scholarly_lookup_excluded_from_future_dataset_access_log"] is True
    assert (
        boundary[
            "dataset_documentation_license_governance_or_access_pages_excluded_from_future_log"
        ]
        is False
    )
    for row in record["cks_selection"]["reference_only_literature"]:
        assert row["previously_looked_up_by_root"] is True
        assert row["contacted_by_this_package"] is False
        assert row["remote_bytes_custody_bound"] is False
        assert row["exact_remote_response_receipt_bound"] is False
        assert row["proves_exact_project_kernel"] is False


def test_exact_fourteen_part_inventory_is_nonoverlapping_and_open(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    rows = record["method_gap_inventory"]
    assert rows == validator.expected_method_inventory()
    assert [row["ordinal"] for row in rows] == list(range(14))
    assert [row["inventory_id"] for row in rows] == [
        "PRIMARY_METHOD_AND_COMPARATOR_IDENTITIES",
        "FOUR_REQUIRED_CONTROLS",
        "FOUR_LITERATURE_COMPARATOR_FAMILIES",
        "TWO_EXTERNAL_DOMAIN_BASELINES",
        "MATCHED_COMPUTE_FORMULA",
        "RUNTIME_IDENTITY",
        "RESOURCE_CEILINGS_AND_ALLOCATIONS",
        "TRAINING_AND_CHECKPOINT_POLICY",
        "FORMAL_TEST_28",
        "FORMAL_TEST_29",
        "FORMAL_TEST_30",
        "WHOLE_METHOD_INTEGRATION",
        "GENERIC_PRODUCTION_RUNNER_AND_CUSTODY",
        "FINAL_TEST_ACCESS_FACT",
    ]
    ids = [item for row in rows for item in row["field_ids"]]
    pointers = [item for row in rows for item in row["json_pointers"]]
    assert len(ids) == len(set(ids)) == 66
    assert len(pointers) == len(set(pointers)) == 66
    assert sum(row["field_count"] for row in rows[:-1]) == 65
    assert ids.count("F172") == 1
    assert rows[8]["exact_missing_blockers"] == [
        "confirmatory_custody",
        "power_and_thresholds",
        "runner_and_recomputation",
        "unconditional_operational_predictions",
    ]
    assert rows[8]["cp75_reviewer_item_revived"] is False


def test_protocol_is_design_only_with_typed_future_nulls_and_terminal_no_go(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    protocol = record["precontact_protocol_design"]
    assert (
        protocol["protocol_kind"] == "STATIC_PRECONTACT_DESIGN_NOT_POPULATED_INSTANCE"
    )
    assert protocol["populated_instance_present"] is False
    assert protocol["populated_instance_admitted"] is False
    assert protocol["independent_review_present"] is False
    assert protocol["administrative_contact_authority_record_present"] is False
    assert protocol["data_access_authority_record_present"] is False
    assert protocol["future_instance_path_selected"] is None
    assert all(value is None for value in protocol["future_observed_slots"].values())
    operation = protocol["operation_contract"]
    assert operation["operation_rows_present"] is False
    assert operation["success_predicate_required_per_operation"] is True
    assert operation["terminal_disposition_required_per_operation"] is True
    assert operation["operation_row_required_fields"] == [
        "GLOBAL_ORDINAL",
        "DOMAIN_ID",
        "PHASE",
        "EXACT_TARGET",
        "EXACT_PERMITTED_REQUEST_KIND",
        "MAXIMUM_ATTEMPT_COUNT",
        "AUTHORIZED_RETRY_COUNT",
        "EXACT_SUCCESS_PREDICATE",
        "EXACT_TERMINAL_DISPOSITION",
    ]
    assert operation["maximum_attempt_count_per_operation"] == 1
    assert operation["authorized_retry_count_per_operation"] == 0
    assert operation["undeclared_operation_permitted"] is False
    assert operation["intent_claim_method"] == "O_EXCL_0600_FILE_FSYNC_PARENT_FSYNC"
    assert operation["intent_without_outcome_disposition"] == (
        "TERMINAL_SPENT_INCOMPLETE_NO_RETRY"
    )
    assert operation["named_failure_disposition_map"] == {
        "ADMIN_DENIED": "ADMIN_CONTACT_TERMINAL_NO_GO",
        "ADMIN_FAILED": "ADMIN_CONTACT_TERMINAL_NO_GO",
        "ADMIN_CANCELLED": "ADMIN_CONTACT_TERMINAL_NO_GO",
        "REQUIRED_APPROVALS_INCOMPLETE": "APPROVALS_INCOMPLETE_TERMINAL_NO_GO",
        "SELECTED_VERSION_UNAVAILABLE": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
        "ACQUISITION_SELECTOR_MISMATCH": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
        "SNAPSHOT_IDENTITY_OR_HASH_MISMATCH": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
        "DATA_ACCESS_DENIED": "DATA_ACCESS_TERMINAL_NO_GO",
        "DATA_ACCESS_FAILED": "DATA_ACCESS_TERMINAL_NO_GO",
        "DATA_ACCESS_CANCELLED": "DATA_ACCESS_TERMINAL_NO_GO",
    }
    assert operation["unknown_or_omitted_outcome_may_count_as_success"] is False
    assert operation["success_marker_without_full_predicate_may_advance"] is False
    assert (
        operation[
            "failure_mapping_total_nonoverlapping_and_precedence_ordered_required"
        ]
        is True
    )
    assert (
        protocol["phase_boundary"][
            "administrative_contact_phase_requires_approvals_already_complete"
        ]
        is False
    )
    assert protocol["only_exact_success_predicate_may_advance"] is True
    assert (
        protocol[
            "terminal_no_go_permits_replacement_source_selector_operation_or_retry"
        ]
        is False
    )
    assert protocol["terminal_no_go_states"] == [
        "ADMIN_CONTACT_TERMINAL_NO_GO",
        "APPROVALS_INCOMPLETE_TERMINAL_NO_GO",
        "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
        "DATA_ACCESS_TERMINAL_NO_GO",
    ]


def test_scope_review_does_not_close_tracker_or_formal_gate(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    review = record["scope_review"]
    checklist = record["checklist_effects"]
    assert review["physical_file_count"] == 4
    assert len(review["named_project_control_predicates"]) == 4
    assert review["targets_single_blocker"] is False
    assert review["automatic_two_artifact_exemption_claimed"] is False
    assert review["fields_closed"] == 0
    assert review["blockers_closed"] == 0
    assert review["formal_tests_closed"] == 0
    assert review["results_filled"] == 0
    assert checklist["timetable_checkbox_closed_by_package"] is False
    assert checklist["static_design_control_is_preregistration_field"] is False
    assert checklist["unresolved_fields_closed"] == 0
    assert checklist["blockers_closed"] == 0
    assert checklist["validator_source_process_writer_or_network_api_exposed"] is False
    assert checklist["hostile_test_source_process_or_network_api_exposed"] is False
    assert checklist["hostile_test_writer_scope"] == "PYTEST_TEMPORARY_REPLICAS_ONLY"
    assert (
        checklist["canonical_package_or_evidence_file_write_by_package_authored_code"]
        is False
    )
    assert checklist["pytest_cache_metadata_mutation_observed"] is True
    assert checklist["global_workspace_write_absence_claimed"] is False
    assert checklist["qualification_python_bytecode_disabled"] is True
    assert checklist["qualification_pytest_cacheprovider_disabled"] is True
    assert (
        checklist["source_safety_is_ast_and_runtime_guard_not_malicious_host_proof"]
        is True
    )


def test_validator_reads_only_closed_live_roster_and_changes_no_byte(
    validator: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _closed_read_roster(validator)
    before = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths
    }
    real_open = validator.os.open
    write_mask = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
    observed: List[str] = []

    def guarded_open(path: object, flags: int, *args: object) -> int:
        assert flags & write_mask == 0
        observed.append(os.fspath(path))
        return real_open(path, flags, *args)

    monkeypatch.setattr(validator.os, "open", guarded_open)
    validator.validate()
    assert len(observed) == 10
    assert {str(Path(path).relative_to(ROOT)) for path in observed} == set(paths)
    after = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths
    }
    assert after == before
    historical = {row["path"] for row in validator.HISTORICAL_SNAPSHOT_INPUTS}
    assert not historical.intersection(
        {str(Path(path).relative_to(ROOT)) for path in observed}
    )


DECLARED_TMP_WRITER_FUNCTIONS = {
    "_copy_closed_roster",
    "_rewrite_machine",
    "_flip_first_byte",
    "make_symlink",
    "make_hardlink",
    "make_wrong_mode",
    "test_historical_snapshot_materialization_or_change_is_not_live_gate",
    "test_prereg_nulls_and_registered_dataset_urls_remain_authoritative",
}


def _qualified_call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _enclosing_function(
    node: ast.AST, parents: Dict[ast.AST, ast.AST]
) -> ast.FunctionDef | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.FunctionDef):
            return current
    return None


def _static_safety_findings(source: str, role: str) -> Tuple[List[str], List[str], int]:
    assert role in {"validator", "hostile_test"}
    tree = ast.parse(source)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    forbidden_import_roots = {
        "aiohttp",
        "asyncio",
        "concurrent",
        "ftplib",
        "http",
        "httpx",
        "multiprocessing",
        "pty",
        "requests",
        "secrets",
        "smtplib",
        "socket",
        "ssl",
        "subprocess",
        "telnetlib",
        "urllib",
        "webbrowser",
    }
    process_calls = {
        "exec",
        "os.fork",
        "os.forkpty",
        "os.popen",
        "os.posix_spawn",
        "os.posix_spawnp",
        "os.system",
    }
    network_call_leaves = {
        "FTP",
        "HTTPConnection",
        "HTTPSConnection",
        "SMTP",
        "accept",
        "bind",
        "connect",
        "connect_ex",
        "create_connection",
        "listen",
        "recv",
        "recvfrom",
        "request",
        "send",
        "sendall",
        "sendto",
        "urlopen",
        "urlretrieve",
    }
    writer_call_leaves = {
        "chmod",
        "chown",
        "copy",
        "copy2",
        "copyfile",
        "hardlink_to",
        "lchmod",
        "link",
        "makedirs",
        "mkdir",
        "move",
        "open",
        "remove",
        "removedirs",
        "rename",
        "rmdir",
        "rmtree",
        "symlink",
        "symlink_to",
        "touch",
        "truncate",
        "unlink",
        "write",
        "write_bytes",
        "write_text",
        "writelines",
    }
    findings: List[str] = []
    writer_functions = set()
    os_open_count = 0
    imported = set()
    function_nodes = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        if not isinstance(node, ast.Call):
            continue
        qualified = _qualified_call_name(node.func)
        leaf = qualified.rsplit(".", 1)[-1]
        if qualified == "os.open":
            os_open_count += 1
            if role == "validator":
                continue
        if (
            qualified in process_calls
            or qualified.startswith("os.exec")
            or qualified.startswith("os.spawn")
            or qualified.startswith("subprocess.")
            or qualified.startswith("multiprocessing.")
            or qualified == "pty.spawn"
        ):
            findings.append("process:" + qualified)
        if leaf in network_call_leaves:
            findings.append("network-call:" + qualified)
        replace_is_writer = qualified in {
            "os.replace",
            "path.replace",
            "target.replace",
            "destination.replace",
            "candidate.replace",
        }
        if leaf in writer_call_leaves or replace_is_writer:
            if role == "validator":
                findings.append("validator-writer:" + qualified)
            else:
                enclosing = _enclosing_function(node, parents)
                name = enclosing.name if enclosing is not None else "<module>"
                writer_functions.add(name)
                if name not in DECLARED_TMP_WRITER_FUNCTIONS:
                    findings.append("undeclared-test-writer:" + name + ":" + qualified)

    for root in sorted(imported.intersection(forbidden_import_roots)):
        findings.append("forbidden-import:" + root)
    exact_import_allowlist = (
        {"__future__", "hashlib", "json", "os", "pathlib", "stat", "typing"}
        if role == "validator"
        else {
            "__future__",
            "ast",
            "hashlib",
            "importlib",
            "json",
            "os",
            "pathlib",
            "pytest",
            "shutil",
            "types",
            "typing",
        }
    )
    for root in sorted(imported.difference(exact_import_allowlist)):
        findings.append("unexpected-import:" + root)
    if role == "hostile_test":
        for name in sorted(writer_functions):
            function = function_nodes.get(name)
            guarded = function is not None and any(
                isinstance(call, ast.Call)
                and _qualified_call_name(call.func)
                == "_assert_not_canonical_write_target"
                for call in ast.walk(function)
            )
            if not guarded:
                findings.append("unguarded-test-writer:" + name)
    return findings, sorted(writer_functions), os_open_count


def test_validator_and_hostile_test_sources_are_statically_process_network_and_write_safe() -> None:
    validator_source = (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")
    test_source = (ROOT / TEST_REL).read_text(encoding="utf-8")
    validator_findings, validator_writers, validator_os_open = _static_safety_findings(
        validator_source, "validator"
    )
    test_findings, test_writers, test_os_open = _static_safety_findings(
        test_source, "hostile_test"
    )
    assert validator_findings == []
    assert validator_writers == []
    assert validator_os_open == 1
    assert test_findings == []
    assert set(test_writers) == DECLARED_TMP_WRITER_FUNCTIONS
    assert test_os_open == 0


@pytest.mark.parametrize(
    "source",
    [
        "import os\nos.system('forbidden')\n",
        "import os\nos.popen('forbidden')\n",
        "import os\nos.fork()\n",
        "import os\nos.execv('/bin/false', [])\n",
        "import os\nos.spawnv(0, '/bin/false', [])\n",
        "import os\nos.posix_spawn('/bin/false', [], {})\n",
        "import os\nos.write(1, b'forbidden')\n",
        "import os\nos.replace('a', 'b')\n",
        "import subprocess\nsubprocess.Popen([])\n",
        "import multiprocessing\nmultiprocessing.Process()\n",
        "import socket\nsocket.create_connection(('example.invalid', 1))\n",
        "import urllib.request\nurllib.request.urlopen('https://example.invalid')\n",
        "from pathlib import Path\nPath('x').write_text('x')\n",
        "open('x', 'w')\n",
    ],
)
def test_static_safety_analysis_rejects_process_network_and_validator_writer_hostiles(
    source: str,
) -> None:
    findings, _, _ = _static_safety_findings(source, "validator")
    assert findings


@pytest.mark.parametrize(
    "source",
    [
        "from pathlib import Path\ndef undeclared(path):\n path.write_bytes(b'x')\n",
        ("def _rewrite_machine(path):\n" " path.write_bytes(b'x')\n"),
    ],
)
def test_static_safety_analysis_rejects_undeclared_or_unguarded_test_writers(
    source: str,
) -> None:
    findings, _, _ = _static_safety_findings(source, "hostile_test")
    assert findings


@pytest.mark.parametrize(
    ("label", "mutate"),
    [
        (
            "raw_transport",
            _mutation("authority_provenance.raw_transport_bytes_bound", True),
        ),
        (
            "user_selected_paths",
            _mutation("authority_provenance.user_selected_file_paths_or_count", True),
        ),
        (
            "external_contact",
            _mutation("authority_provenance.external_contact_authorized", True),
        ),
        (
            "license_contact",
            _mutation(
                "authority_provenance.license_or_governance_request_authorized", True
            ),
        ),
        (
            "data_access",
            _mutation(
                "authority_provenance.data_access_or_acquisition_authorized", True
            ),
        ),
        (
            "network",
            _mutation("authority_provenance.network_or_connector_authorized", True),
        ),
        (
            "science",
            _mutation("authority_provenance.scientific_execution_authorized", True),
        ),
        (
            "runtime",
            _mutation("authority_provenance.runtime_approval_authorized", True),
        ),
        (
            "formal_test",
            _mutation("authority_provenance.formal_test_execution_authorized", True),
        ),
        (
            "scientific_entropy",
            _mutation(
                "authority_provenance.scientific_campaign_or_protocol_entropy_authorized",
                True,
            ),
        ),
        (
            "scientific_subprocess",
            _mutation(
                "authority_provenance.scientific_or_operational_subprocess_route_authorized",
                True,
            ),
        ),
        (
            "route_user_selected",
            _mutation("authority_provenance.user_selected_route_values", True),
        ),
        (
            "route_not_agent_selected",
            _mutation("authority_provenance.agent_selected_route_values", False),
        ),
        ("c17_route", _mutation("c17_selection.route", "FORK_A")),
        ("c17_proved", _mutation("c17_selection.c17_proved", True)),
        ("c17_promoted", _mutation("c17_selection.c17_claim_promoted", True)),
        ("nce_path", _mutation("c17_selection.nce_used_as_path_certificate", True)),
        ("support_policy", _mutation("common_support_selection.policy", "CLIPPED")),
        (
            "phys_support",
            _mutation("common_support_selection.physionet_route_verified", True),
        ),
        (
            "retail_support",
            _mutation("common_support_selection.retail_route_verified", True),
        ),
        (
            "domain_admission",
            _mutation("common_support_selection.domain_admission_promoted", True),
        ),
        (
            "cks_lookup_false",
            _mutation(
                "cks_selection.primary_literature_lookup_performed_by_root", False
            ),
        ),
        ("cks_proved", _mutation("cks_selection.cks_characteristicness_proved", True)),
        ("cks_complete", _mutation("cks_selection.cks_proof_complete", True)),
        ("primary_selected", _mutation("cks_selection.primary_metric_selected", True)),
        ("b04_closed", _mutation("cks_selection.b04_closed", True)),
        (
            "paper_bytes",
            _mutation(
                "cks_selection.reference_only_literature.0.remote_bytes_custody_bound",
                True,
            ),
        ),
        (
            "paper_proof",
            _mutation(
                "cks_selection.reference_only_literature.0.proves_exact_project_kernel",
                True,
            ),
        ),
        (
            "global_network_absence",
            _mutation(
                "external_observation_boundary.global_network_absence_claimed", True
            ),
        ),
        (
            "dataset_contact",
            _mutation(
                "external_observation_boundary.registered_dataset_source_contact_performed",
                True,
            ),
        ),
        (
            "lookup_roster_complete",
            _mutation(
                "external_observation_boundary.registered_targets_are_complete_http_request_roster",
                True,
            ),
        ),
        (
            "lookup_authority_source",
            _mutation(
                "external_observation_boundary.lookup_authority_source",
                "STATIC_PACKAGE_AUTHORITY",
            ),
        ),
        (
            "seal_not_before_lookup",
            _mutation(
                "external_observation_boundary.prospective_seal_preceded_kernel_theory_lookup",
                False,
            ),
        ),
        (
            "lookup_timestamp_bound",
            _mutation(
                "external_observation_boundary.exact_wall_clock_lookup_timestamp_bound",
                True,
            ),
        ),
        (
            "lookup_request_count_known",
            _mutation(
                "external_observation_boundary.exact_http_or_search_request_count_known",
                True,
            ),
        ),
        (
            "lookup_receipt",
            _mutation(
                "external_observation_boundary.remote_response_receipts_bound", True
            ),
        ),
        (
            "scholarly_bytes_bound",
            _mutation(
                "external_observation_boundary.remote_scholarly_bytes_bound", True
            ),
        ),
        (
            "dataset_docs_excluded",
            _mutation(
                "external_observation_boundary.dataset_documentation_license_governance_or_access_pages_excluded_from_future_log",
                True,
            ),
        ),
        (
            "bibliography_dataset_overlap",
            _mutation(
                "external_observation_boundary.registered_bibliographic_targets_included.0",
                "https://physionet.org/content/challenge-2012/1.0.0/",
            ),
        ),
        (
            "seal_bytes_modified",
            _mutation(
                "external_observation_boundary.prospective_seal_bytes_modified", True
            ),
        ),
        (
            "seal_scope_relaxed",
            _mutation(
                "external_observation_boundary.retroactive_scope_relaxation_claimed",
                True,
            ),
        ),
        (
            "seal_scope_ambiguity_denied",
            _mutation(
                "external_observation_boundary.prospective_seal_literal_scope_ambiguity_acknowledged",
                False,
            ),
        ),
        (
            "independent_seal_adjudication",
            _mutation(
                "external_observation_boundary.independent_seal_compliance_adjudication_performed",
                True,
            ),
        ),
        (
            "lookup_declared_compliant",
            _mutation(
                "external_observation_boundary.lookup_declared_seal_compliant", True
            ),
        ),
        (
            "lookup_declared_violation",
            _mutation(
                "external_observation_boundary.lookup_declared_seal_violation", True
            ),
        ),
        (
            "instance_present",
            _mutation("precontact_protocol_design.populated_instance_present", True),
        ),
        (
            "review_present",
            _mutation("precontact_protocol_design.independent_review_present", True),
        ),
        (
            "admin_auth",
            _mutation(
                "precontact_protocol_design.administrative_contact_authority_record_present",
                True,
            ),
        ),
        (
            "data_auth",
            _mutation(
                "precontact_protocol_design.data_access_authority_record_present", True
            ),
        ),
        (
            "source_contacted",
            _mutation(
                "precontact_protocol_design.registered_sources.0.url_contacted_by_this_package",
                True,
            ),
        ),
        (
            "future_hash",
            _mutation(
                "precontact_protocol_design.future_observed_slots.raw_snapshot_sha256_by_domain",
                ["0" * 64],
            ),
        ),
        (
            "retry",
            _mutation(
                "precontact_protocol_design.operation_contract.authorized_retry_count_per_operation",
                1,
            ),
        ),
        (
            "attempts",
            _mutation(
                "precontact_protocol_design.operation_contract.maximum_attempt_count_per_operation",
                2,
            ),
        ),
        (
            "undeclared",
            _mutation(
                "precontact_protocol_design.operation_contract.undeclared_operation_permitted",
                True,
            ),
        ),
        (
            "success_predicate_not_required",
            _mutation(
                "precontact_protocol_design.operation_contract.success_predicate_required_per_operation",
                False,
            ),
        ),
        (
            "operation_rows_fabricated",
            _mutation(
                "precontact_protocol_design.operation_contract.operation_rows_present",
                True,
            ),
        ),
        (
            "terminal_disposition_not_required",
            _mutation(
                "precontact_protocol_design.operation_contract.terminal_disposition_required_per_operation",
                False,
            ),
        ),
        (
            "success_predicate_row_field_removed",
            _mutation(
                "precontact_protocol_design.operation_contract.operation_row_required_fields.7",
                "OPTIONAL_SUCCESS_NOTE",
            ),
        ),
        (
            "unknown_outcome_as_success",
            _mutation(
                "precontact_protocol_design.operation_contract.unknown_or_omitted_outcome_may_count_as_success",
                True,
            ),
        ),
        (
            "bare_success_marker_advances",
            _mutation(
                "precontact_protocol_design.operation_contract.success_marker_without_full_predicate_may_advance",
                True,
            ),
        ),
        (
            "failure_map_not_total",
            _mutation(
                "precontact_protocol_design.operation_contract.failure_mapping_total_nonoverlapping_and_precedence_ordered_required",
                False,
            ),
        ),
        *[
            (
                "failure_map_" + key.lower(),
                _mutation(
                    "precontact_protocol_design.operation_contract.named_failure_disposition_map."
                    + key,
                    "WRONG_TERMINAL_STATE",
                ),
            )
            for key in [
                "ADMIN_DENIED",
                "ADMIN_FAILED",
                "ADMIN_CANCELLED",
                "REQUIRED_APPROVALS_INCOMPLETE",
                "SELECTED_VERSION_UNAVAILABLE",
                "ACQUISITION_SELECTOR_MISMATCH",
                "SNAPSHOT_IDENTITY_OR_HASH_MISMATCH",
                "DATA_ACCESS_DENIED",
                "DATA_ACCESS_FAILED",
                "DATA_ACCESS_CANCELLED",
            ]
        ],
        (
            "advance_failure",
            _mutation(
                "precontact_protocol_design.only_exact_success_predicate_may_advance",
                False,
            ),
        ),
        (
            "terminal_retry",
            _mutation(
                "precontact_protocol_design.terminal_no_go_permits_replacement_source_selector_operation_or_retry",
                True,
            ),
        ),
        ("fields_closed", _mutation("checklist_effects.unresolved_fields_closed", 1)),
        ("blockers_closed", _mutation("checklist_effects.blockers_closed", 1)),
        ("formal_closed", _mutation("checklist_effects.formal_tests_closed", 1)),
        (
            "requests_opened",
            _mutation(
                "checklist_effects.dataset_source_license_governance_or_access_requests_opened_by_package",
                True,
            ),
        ),
        (
            "validator_source_route_exposed",
            _mutation(
                "checklist_effects.validator_source_process_writer_or_network_api_exposed",
                True,
            ),
        ),
        (
            "test_source_route_exposed",
            _mutation(
                "checklist_effects.hostile_test_source_process_or_network_api_exposed",
                True,
            ),
        ),
        (
            "canonical_package_or_evidence_write",
            _mutation(
                "checklist_effects.canonical_package_or_evidence_file_write_by_package_authored_code",
                True,
            ),
        ),
        (
            "pytest_cache_mutation_denied",
            _mutation(
                "checklist_effects.pytest_cache_metadata_mutation_observed", False
            ),
        ),
        (
            "global_workspace_write_absence",
            _mutation("checklist_effects.global_workspace_write_absence_claimed", True),
        ),
        (
            "bytecode_not_disabled",
            _mutation(
                "checklist_effects.qualification_python_bytecode_disabled", False
            ),
        ),
        (
            "cacheprovider_not_disabled",
            _mutation(
                "checklist_effects.qualification_pytest_cacheprovider_disabled", False
            ),
        ),
        (
            "test_writer_scope",
            _mutation(
                "checklist_effects.hostile_test_writer_scope",
                "CANONICAL_WORKSPACE",
            ),
        ),
        (
            "source_safety_malicious_host_claim",
            _mutation(
                "checklist_effects.source_safety_is_ast_and_runtime_guard_not_malicious_host_proof",
                False,
            ),
        ),
        (
            "timetable_closed",
            _mutation("checklist_effects.timetable_checkbox_closed_by_package", True),
        ),
        (
            "automatic_exemption",
            _mutation("scope_review.automatic_two_artifact_exemption_claimed", True),
        ),
        ("single_blocker", _mutation("scope_review.targets_single_blocker", True)),
        (
            "public",
            _mutation(
                "publication_anonymity_boundary.anonymous_or_public_submission_inclusion_permitted",
                True,
            ),
        ),
        (
            "absolute_path",
            _mutation(
                "authority_provenance.authorized_package_paths.0", "/tmp/forbidden"
            ),
        ),
    ],
)
def test_every_overclaim_state_authority_and_contact_flip_fails_closed(
    validator: ModuleType,
    tmp_path: Path,
    label: str,
    mutate: Callable[[Dict[str, Any]], None],
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.ValidationError, match="mismatch|invalid|unsafe"):
        validator.validate(root)


@pytest.mark.parametrize(
    ("label", "mutate"),
    [
        (
            "bool_file_count",
            _mutation("authority_provenance.agent_selected_bounded_file_count", False),
        ),
        (
            "float_file_count",
            _mutation("authority_provenance.agent_selected_bounded_file_count", 4.0),
        ),
        ("bool_closed", _mutation("checklist_effects.unresolved_fields_closed", False)),
        ("bool_inventory_ordinal", _mutation("method_gap_inventory.0.ordinal", False)),
        ("bool_field_count", _mutation("method_gap_inventory.0.field_count", False)),
        (
            "string_null",
            _mutation(
                "precontact_protocol_design.future_instance_path_selected", "null"
            ),
        ),
    ],
)
def test_exact_types_reject_python_equality_aliases(
    validator: ModuleType,
    tmp_path: Path,
    label: str,
    mutate: Callable[[Dict[str, Any]], None],
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.ValidationError, match="type mismatch"):
        validator.validate(root)


def test_inventory_roster_overlap_fake_rows_and_count_changes_reject(
    validator: ModuleType, tmp_path: Path
) -> None:
    mutations: List[Callable[[Dict[str, Any]], None]] = [
        _mutation("method_gap_inventory.0.field_ids.0", "F063"),
        _mutation(
            "method_gap_inventory.0.json_pointers.0",
            "/method_and_baseline_plan/primary_method/commit",
        ),
        _mutation("method_gap_inventory.8.field_ids", ["F999"]),
        _mutation("method_gap_inventory.8.field_count", 1),
        _mutation("method_gap_inventory.8.dedicated_f_rows_present", True),
        _mutation("method_gap_inventory.13.field_ids.0", "F171"),
    ]
    for index, mutate in enumerate(mutations):
        case = tmp_path / str(index)
        root = _copy_closed_roster(validator, case)
        _rewrite_machine(validator, root, mutate)
        with pytest.raises(validator.ValidationError):
            validator.validate(root)


def test_record_self_digest_and_canonical_json_fail_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path / "digest")
    _rewrite_machine(
        validator,
        root,
        _mutation("record_sha256", "0" * 64),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError, match="self digest"):
        validator.validate(root)

    root = _copy_closed_roster(validator, tmp_path / "canonical")
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError, match="not canonical"):
        validator.validate(root)


@pytest.mark.parametrize(
    "binding_index",
    list(range(6)),
)
def test_every_live_immutable_input_hash_is_enforced(
    validator: ModuleType, tmp_path: Path, binding_index: int
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    relative = validator.LIVE_IMMUTABLE_BINDINGS[binding_index]["path"]
    _flip_first_byte(root / relative)
    with pytest.raises(validator.ValidationError, match="binding|input|decode|state"):
        validator.validate(root)


@pytest.mark.parametrize(
    "relative",
    [
        "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md",
        str(VALIDATOR_REL),
        "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py",
    ],
)
def test_each_package_binding_is_enforced(
    validator: ModuleType, tmp_path: Path, relative: str
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _flip_first_byte(root / relative)
    with pytest.raises(validator.ValidationError, match="package bindings"):
        validator.validate(root)


def test_symlink_hardlink_and_wrong_mode_custody_fail_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    cases: List[Tuple[str, Callable[[Path], None]]] = []

    def make_symlink(path: Path) -> None:
        replacement = path.parent / "replacement"
        _assert_not_canonical_write_target(path)
        _assert_not_canonical_write_target(replacement)
        replacement.write_bytes(path.read_bytes())
        replacement.chmod(0o644)
        path.unlink()
        path.symlink_to(replacement.name)

    def make_hardlink(path: Path) -> None:
        link = path.parent / "second-link"
        _assert_not_canonical_write_target(path)
        _assert_not_canonical_write_target(link)
        os.link(path, link)

    def make_wrong_mode(path: Path) -> None:
        _assert_not_canonical_write_target(path)
        path.chmod(0o600)

    cases.extend(
        [
            ("symlink", make_symlink),
            ("hardlink", make_hardlink),
            ("mode", make_wrong_mode),
        ]
    )
    for label, mutate in cases:
        root = _copy_closed_roster(validator, tmp_path / label)
        mutate(root / validator.CLOSURE_PATH)
        with pytest.raises(validator.ValidationError, match="custody invalid"):
            validator.validate(root)


def test_historical_snapshot_materialization_or_change_is_not_live_gate(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    for row in validator.HISTORICAL_SNAPSHOT_INPUTS:
        target = root / row["path"]
        _assert_not_canonical_write_target(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"future mutable bytes\n")
    future = root / "research/fixtures/future_populated_precontact_instance.json"
    _assert_not_canonical_write_target(future)
    future.parent.mkdir(parents=True, exist_ok=True)
    future.write_bytes(b"{}\n")
    assert validator.validate(root)["validation"] == "PASS"


def test_prereg_nulls_and_registered_dataset_urls_remain_authoritative(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    prereg_path = root / validator.PREREGISTRATION_PATH
    _assert_not_canonical_write_target(prereg_path)
    prereg = json.loads(prereg_path.read_text(encoding="ascii"))
    prereg["domains"][0]["positive_or_common_support_route"] = "CLAIMED"
    raw = json.dumps(prereg, indent=2, sort_keys=True).encode("ascii") + b"\n"
    prereg_path.write_bytes(raw)
    prereg_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_no_focused_bytecode_cache_is_present() -> None:
    names = {
        "manuscript_v3_solo_block2_static_selection_freeze_v1",
        "test_manuscript_v3_solo_block2_static_selection_freeze_v1",
    }
    found: List[Path] = []
    for directory in [
        ROOT / "research/diagnostics/__pycache__",
        ROOT / "tests/unit/__pycache__",
    ]:
        if directory.exists():
            for path in directory.iterdir():
                if path.is_file() and any(name in path.name for name in names):
                    found.append(path)
    assert found == []
