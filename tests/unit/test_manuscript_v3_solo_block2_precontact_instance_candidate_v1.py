"""Hostile tests for the Solo Block 2 precontact-instance candidate.

All materialization and mutation occurs inside pytest temporary directories.
The canonical package is read only.  No test imports scientific project code or
exposes a network, subprocess, connector, data, protocol, authority/runtime, or
scientific route.
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
from typing import Any, Callable, Dict, List, Set, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.json"
)
TEST_REL = Path(
    "tests/unit/test_manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)
AUTHORITY_TEXT = (
    "Okay, go ahead to the next step then.\n"
    "And dont forget to mark the steps carried out in the project plan."
)


def _load_validator() -> ModuleType:
    path = ROOT / VALIDATOR_REL
    spec = importlib.util.spec_from_file_location(
        "solo_block2_precontact_candidate_validator", path
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


def _require_tmp_target(root: Path, target: Path) -> None:
    resolved_root = root.resolve()
    resolved_target = target.resolve(strict=False)
    assert resolved_target != ROOT.resolve()
    assert ROOT.resolve() not in resolved_target.parents
    assert resolved_target == resolved_root or resolved_root in resolved_target.parents


def _copy_closed_roster(module: ModuleType, tmp_path: Path) -> Path:
    for relative in _closed_read_roster(module):
        source = ROOT / relative
        target = tmp_path / relative
        _require_tmp_target(tmp_path, target)
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
    _require_tmp_target(root, path)
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = module.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _replace(record: Dict[str, Any], pointer: str, value: Any) -> None:
    current: Any = record
    tokens = pointer.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def _mutation(pointer: str, value: Any) -> Callable[[Dict[str, Any]], None]:
    return lambda record: _replace(record, pointer, value)


def test_canonical_candidate_validates_with_exact_nonclosure(
    validator: ModuleType,
) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "candidate_control_predicate": True,
        "candidate_present": True,
        "populated_instance_present": False,
        "populated_instance_admitted": False,
        "precontact_population_blocked": True,
        "four_row_core_complete_for_admission": False,
        "approval_contact_roster_complete": False,
        "retail_exact_temporal_rule_populated": False,
        "future_observed_nonnull_count": 0,
        "external_contact_or_data_access_authorized": False,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "effective_unresolved_field_count": 172,
        "effective_open_blocker_count": 12,
        "original_populated_instance_checkbox_closed": False,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_authority_is_exact_and_does_not_promote_contact(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == AUTHORITY_TEXT
    assert authority["normalized_visible_text_utf8_bytes"] == 104
    assert authority["normalized_visible_text_sha256"] == hashlib.sha256(
        AUTHORITY_TEXT.encode("utf-8")
    ).hexdigest()
    assert authority["raw_transport_bytes_bound"] is False
    assert authority["conversation_envelope_bound"] is False
    assert authority["additive_static_candidate_package_authorized"] is True
    assert authority["tracker_edit_authorized_before_independent_go"] is False
    for key in (
        "external_contact_authorized",
        "dataset_page_browsing_authorized",
        "documentation_license_or_governance_browsing_authorized",
        "data_access_or_download_authorized",
        "approval_creation_authorized",
        "credential_use_authorized",
        "protocol_operation_authorized",
        "scientific_execution_authorized",
        "scientific_entropy_authorized",
    ):
        assert authority[key] is False
    assert authority["user_selected_roster_split_or_role_tokens"] is False
    assert authority["agent_selected_bounded_implementation_details"] is True


def test_candidate_core_is_explicitly_incomplete_and_ineligible(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    identity = record["candidate_identity"]
    assert identity["candidate_present"] is True
    assert identity["populated_instance_present"] is False
    assert identity["populated_instance_admitted"] is False
    assert identity["precontact_population_blocked"] is True
    assert identity["candidate_operation_roster_complete_for_admission"] is False
    assert identity["approval_contact_target_roster_complete"] is False
    assert identity["retail_exact_temporal_rule_populated"] is False
    rows = record["candidate_operation_roster"]
    assert len(rows) == 4
    assert [row["global_ordinal"] for row in rows] == [0, 1, 2, 3]
    assert [row["phase"] for row in rows] == ["ADMIN", "ADMIN", "DATA", "DATA"]
    assert all(row["maximum_attempt_count"] == 1 for row in rows)
    assert all(type(row["maximum_attempt_count"]) is int for row in rows)
    assert all(row["authorized_retry_count"] == 0 for row in rows)
    assert all(type(row["authorized_retry_count"]) is int for row in rows)
    assert all(row["currently_eligible"] is False for row in rows)
    assert all(row["current_intent_receipt"] is None for row in rows)
    assert all(row["current_outcome_receipt"] is None for row in rows)
    assert rows[0]["exact_target"] == validator.PHYSIONET_URL
    assert rows[1]["exact_target"] == validator.RETAIL_URL
    assert record["candidate_approval_gates"]["undeclared_approval_contact_permitted"] is False


def test_all_thirteen_future_observations_are_strict_null(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    slots = record["future_observed_slots"]
    assert len(slots) == 13
    assert set(slots) == set(validator.EXPECTED_FUTURE_SLOTS)
    assert all(value is None for value in slots.values())
    selectors = record["candidate_selectors"]
    for domain in ("physionet", "retail"):
        assert selectors[domain]["observed_archive_locator"] is None
        assert selectors[domain]["observed_version"] is None
        assert selectors[domain]["observed_sha256"] is None
        assert selectors[domain]["observed_byte_count"] is None


def test_split_candidate_preserves_no_exclusion_and_retail_gap(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    split = record["candidate_split_and_leakage_rules"]
    assert split["proportions"] == {
        "train_numerator": 70,
        "validation_numerator": 15,
        "test_numerator": 15,
        "denominator": 100,
    }
    assert split["power_justified"] is False
    assert split["seed_or_entropy_required"] is False
    assert split["minimum_group_count"] == 5
    assert split["exact_split_algorithm_populated"] is False
    assert split["physionet"]["exact_rule_populated"] is False
    assert split["physionet"]["literal_hash_domain_separator"] is None
    assert split["physionet"]["canonical_patient_id_byte_encoding_and_normalization"] is None
    assert split["physionet"]["hash_collision_tie_break_rule"] is None
    retail = split["retail"]
    assert retail["required_policy"] == "CUSTOMER_DISJOINT_AND_TEMPORAL"
    assert retail["test_set_exclusion_permitted"] is False
    assert retail["customer_invoice_or_row_censoring_permitted"] is False
    assert retail["boundary_spanning_customer_exclusion_permitted"] is False
    assert retail["exact_temporal_rule_populated"] is False
    assert retail["independent_consistency_review_complete"] is False
    assert record["gap_inventory"]["retail_temporal_rule_complete"] is False


def test_approval_and_escrow_are_labels_not_readiness(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    approvals = record["candidate_approval_gates"]
    assert len(approvals["required_receipt_classes"]) == 7
    assert approvals["receipt_values"] == [None] * 7
    assert approvals["concrete_approval_target_identities_present"] is False
    assert approvals["approval_contact_target_roster_complete"] is False
    assert approvals["undeclared_approval_contact_permitted"] is False
    assert approvals["scope_review_may_complete_roster_only_before_any_contact"] is True
    assert approvals[
        "post_contact_or_terminal_scope_review_may_repair_resume_insert_or_replace"
    ] is False
    escrow = record["candidate_escrow_controls"]
    assert len(escrow["candidate_role_tokens"]) == 4
    assert escrow["role_tokens_are_real_identities"] is False
    assert escrow["real_principal_identity_binding_present"] is False
    assert escrow["key_identity_binding_present"] is False
    assert escrow["acl_acceptance_receipt_present"] is False
    assert escrow["independent_escrow_ready"] is False
    assert escrow["solo_worker_self_escrow_called_independent"] is False


def test_gap_partition_does_not_authorize_reconnaissance(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    gaps = record["gap_inventory"]
    assert len(gaps["local_or_user_resolvable_precontact_prerequisites"]) == 5
    assert len(gaps["future_admin_observations_not_precontact_reconnaissance_authority"]) == 3
    assert gaps["precontact_population_blocked"] is True
    assert gaps["documentation_license_governance_reconnaissance_exception_permitted"] is False
    assert gaps["registered_urls_are_unverified_sole_targets"] is True
    assert gaps["target_mismatch_permits_amendment_or_reconnaissance"] is False
    assert gaps["four_row_core_complete_for_admission"] is False
    assert gaps["approval_contact_roster_incomplete"] is True
    assert gaps["physionet_exact_split_rule_complete"] is False


def test_failure_map_is_total_named_and_no_retry(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    failure = record["failure_and_state_contract"]
    assert failure["named_failure_disposition_map"] == dict(validator.FAILURE_MAP)
    assert len(failure["named_failure_disposition_map"]) == 10
    assert failure["protocol_violation_precedence"] == 0
    assert failure["intent_without_outcome_precedence"] == 1
    assert failure["named_failure_mapping_precedence"] == 2
    assert failure["residual_phase_non_success_precedence"] == 3
    assert failure["intent_without_outcome_disposition"] == "TERMINAL_SPENT_INCOMPLETE_NO_RETRY"
    assert all(
        row["failure_disposition_resolution_order"]
        == [
            "PROTOCOL_VIOLATION",
            "INTENT_WITHOUT_OUTCOME",
            "NAMED_FAILURE_DISPOSITION_MAP",
            "RESIDUAL_PHASE_NON_SUCCESS",
        ]
        for row in record["candidate_operation_roster"]
    )
    assert failure["unknown_or_missing_outcome_may_count_as_success"] is False
    assert failure["contact_from_current_candidate_state_is_protocol_violation"] is True
    assert failure[
        "terminal_no_go_permits_retry_repair_replacement_fallback_deletion_reacquisition_or_amendment"
    ] is False


def test_checklist_changes_only_candidate_control_predicate(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    effects = record["checklist_effects"]
    assert effects["candidate_control_predicate"] == validator.CONTROL_PREDICATE
    assert effects["candidate_control_predicate_value_after_validation"] is True
    assert effects["original_populated_instance_checkbox_closed"] is False
    assert effects["unresolved_fields_closed"] == 0
    assert type(effects["unresolved_fields_closed"]) is int
    assert effects["blockers_closed"] == 0
    assert effects["effective_unresolved_field_count"] == 172
    assert effects["effective_open_blocker_count"] == 12
    assert effects["tracker_edit_performed_by_this_package"] is False
    scope = record["scope_review"]
    assert scope["preparatory_package_ordinal_for_precontact"] == 2
    assert scope["second_and_last_preparatory_package_under_current_scope"] is True
    assert scope["third_micro_layer_permitted_without_explicit_new_scope_review"] is False
    assert scope["tracker_digest_bound_by_this_package"] is False


@pytest.mark.parametrize(
    ("pointer", "value"),
    [
        ("authority_provenance.normalized_visible_text", AUTHORITY_TEXT + " "),
        ("authority_provenance.raw_transport_bytes_bound", True),
        ("authority_provenance.conversation_envelope_bound", True),
        ("authority_provenance.external_contact_authorized", True),
        ("authority_provenance.dataset_page_browsing_authorized", True),
        ("authority_provenance.data_access_or_download_authorized", True),
        ("authority_provenance.scientific_execution_authorized", True),
        ("candidate_identity.candidate_present", False),
        ("candidate_identity.populated_instance_present", True),
        ("candidate_identity.populated_instance_admitted", True),
        ("candidate_identity.independent_review_present", True),
        ("candidate_identity.administrative_contact_authority_present", True),
        ("candidate_identity.data_access_performed_by_this_package", True),
        ("candidate_identity.precontact_population_blocked", False),
        ("candidate_identity.candidate_operation_roster_complete_for_admission", True),
        ("candidate_identity.approval_contact_target_roster_complete", True),
        ("candidate_identity.retail_exact_temporal_rule_populated", True),
        ("candidate_operation_roster.0.global_ordinal", False),
        ("candidate_operation_roster.0.maximum_attempt_count", True),
        ("candidate_operation_roster.0.failure_disposition_resolution_order", ["PROTOCOL_VIOLATION", "NAMED_FAILURE_DISPOSITION_MAP", "RESIDUAL_PHASE_NON_SUCCESS"]),
        ("candidate_operation_roster.1.authorized_retry_count", 1),
        ("candidate_operation_roster.2.currently_eligible", True),
        ("candidate_operation_roster.3.current_outcome_receipt", "SUCCESS"),
        ("candidate_operation_roster.0.exact_target", "*"),
        ("candidate_operation_roster.1.exact_target", "AS_NEEDED"),
        ("candidate_selectors.physionet.observed_version", "1.0.0"),
        ("candidate_selectors.retail.observed_archive_locator", "archive.zip"),
        ("candidate_selectors.retail.redirect_fallback_or_substitution_permitted", True),
        ("candidate_split_and_leakage_rules.power_justified", True),
        ("candidate_split_and_leakage_rules.exact_split_algorithm_populated", True),
        ("candidate_split_and_leakage_rules.physionet.exact_rule_populated", True),
        ("candidate_split_and_leakage_rules.seed_or_entropy_required", True),
        ("candidate_split_and_leakage_rules.retail.test_set_exclusion_permitted", True),
        ("candidate_split_and_leakage_rules.retail.customer_invoice_or_row_censoring_permitted", True),
        ("candidate_split_and_leakage_rules.retail.exact_temporal_rule_populated", True),
        ("candidate_approval_gates.concrete_approval_target_identities_present", True),
        ("candidate_approval_gates.approval_contact_target_roster_complete", True),
        ("candidate_approval_gates.undeclared_approval_contact_permitted", True),
        ("candidate_approval_gates.scope_review_may_complete_roster_only_before_any_contact", False),
        ("candidate_approval_gates.post_contact_or_terminal_scope_review_may_repair_resume_insert_or_replace", True),
        ("candidate_escrow_controls.role_tokens_are_real_identities", True),
        ("candidate_escrow_controls.independent_escrow_ready", True),
        ("candidate_escrow_controls.solo_worker_self_escrow_called_independent", True),
        ("gap_inventory.documentation_license_governance_reconnaissance_exception_permitted", True),
        ("gap_inventory.target_mismatch_permits_amendment_or_reconnaissance", True),
        ("gap_inventory.four_row_core_complete_for_admission", True),
        ("checklist_effects.original_populated_instance_checkbox_closed", True),
        ("checklist_effects.unresolved_fields_closed", 1),
        ("scope_review.third_micro_layer_permitted_without_explicit_new_scope_review", True),
        ("failure_and_state_contract.intent_without_outcome_precedence", 2),
        ("failure_and_state_contract.intent_without_outcome_disposition", "ADMIN_CONTACT_TERMINAL_NO_GO"),
        ("publication_anonymity_boundary.anonymous_or_public_supplement", True),
    ],
)
def test_semantic_overclaim_and_exact_type_flips_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
    pointer: str,
    value: Any,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(validator, root, _mutation(pointer, value))
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize("slot", sorted([key for key in _load_validator().EXPECTED_FUTURE_SLOTS]))
def test_every_future_observation_fabrication_fails_closed(
    validator: ModuleType,
    tmp_path: Path,
    slot: str,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        _mutation("future_observed_slots." + slot, "FABRICATED"),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize("failure_key", sorted([key for key in _load_validator().FAILURE_MAP]))
def test_every_named_failure_disposition_flip_fails_closed(
    validator: ModuleType,
    tmp_path: Path,
    failure_key: str,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        _mutation(
            "failure_and_state_contract.named_failure_disposition_map." + failure_key,
            "SUCCESS",
        ),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_missing_extra_and_reordered_operation_rows_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
) -> None:
    for mutation in (
        lambda record: record["candidate_operation_roster"].pop(),
        lambda record: record["candidate_operation_roster"].append(
            dict(record["candidate_operation_roster"][0])
        ),
        lambda record: record["candidate_operation_roster"].reverse(),
        lambda record: record["candidate_operation_roster"][0].update({"extra": False}),
        lambda record: record["candidate_operation_roster"][0].pop("exact_target"),
    ):
        case = tmp_path / ("case_" + str(len(list(tmp_path.iterdir()))))
        case.mkdir()
        root = _copy_closed_roster(validator, case)
        _rewrite_machine(validator, root, mutation)
        with pytest.raises(validator.ValidationError):
            validator.validate(root)


def test_machine_canonical_self_and_package_binding_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
) -> None:
    roots = [tmp_path / name for name in ("self", "pretty", "binding", "extra")]
    for root in roots:
        root.mkdir()
        _copy_closed_roster(validator, root)
    _rewrite_machine(
        validator,
        roots[0],
        _mutation("candidate_identity.candidate_present", False),
        recompute_digest=False,
    )
    _rewrite_machine(validator, roots[1], lambda record: None, canonical=False)
    _rewrite_machine(
        validator,
        roots[2],
        _mutation("package_bindings.0.raw_sha256", "0" * 64),
    )
    _rewrite_machine(
        validator,
        roots[3],
        lambda record: record.update({"extra": False}),
    )
    for root in roots:
        with pytest.raises(validator.ValidationError):
            validator.validate(root)


@pytest.mark.parametrize("kind", ["mode", "hardlink", "symlink", "bytes"])
def test_live_immutable_custody_mutations_fail_closed(
    validator: ModuleType,
    tmp_path: Path,
    kind: str,
) -> None:
    root = _copy_closed_roster(validator, tmp_path)
    relative = validator.CLOSURE_PATH
    path = root / relative
    _require_tmp_target(root, path)
    if kind == "mode":
        path.chmod(0o600)
    elif kind == "hardlink":
        os.link(path, root / "extra_link")
    elif kind == "symlink":
        raw_copy = root / "closure_copy"
        shutil.copyfile(path, raw_copy)
        path.unlink()
        path.symlink_to(raw_copy)
    else:
        raw = path.read_bytes()
        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
        path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_historical_snapshots_are_never_reopened(
    validator: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: List[str] = []
    original = validator._stable_read

    def tracking(root: Path, relative: str) -> bytes:
        observed.append(relative)
        return original(root, relative)

    monkeypatch.setattr(validator, "_stable_read", tracking)
    assert validator.validate()["validation"] == "PASS"
    historical = {row["path"] for row in validator.HISTORICAL_SNAPSHOT_INPUTS}
    assert historical.isdisjoint(observed)
    assert set(observed) == set(_closed_read_roster(validator))


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_name(node.value)
        return prefix + "." + node.attr if prefix else node.attr
    return ""


def test_validator_and_hostile_source_expose_no_process_network_or_canonical_writer(
    validator: ModuleType,
) -> None:
    sources = {
        "validator": (ROOT / VALIDATOR_REL).read_text(encoding="utf-8"),
        "test": (ROOT / TEST_REL).read_text(encoding="utf-8"),
    }
    expected_import_rosters = {
        "validator": {
            "__future__",
            "hashlib",
            "json",
            "os",
            "pathlib",
            "stat",
            "typing",
        },
        "test": {
            "__future__",
            "ast",
            "hashlib",
            "importlib.util",
            "json",
            "os",
            "pathlib",
            "pytest",
            "shutil",
            "types",
            "typing",
        },
    }
    process_prefixes = (
        "subprocess.",
        "multiprocessing.",
        "os.system",
        "os.popen",
        "os.fork",
        "os.exec",
        "os.spawn",
        "os.posix_spawn",
    )
    network_prefixes = (
        "socket.",
        "ssl.",
        "http.",
        "urllib.",
        "requests.",
        "ftplib.",
    )
    validator_writer_names = {
        "os.write",
        "Path.write_bytes",
        "Path.write_text",
        "Path.mkdir",
        "Path.unlink",
        "Path.symlink_to",
        "shutil.copyfile",
    }
    for label, source in sources.items():
        tree = ast.parse(source)
        imports: Set[str] = set()
        calls: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                calls.append(_qualified_name(node.func))
        assert imports == expected_import_rosters[label]
        assert not any(
            call == prefix or call.startswith(prefix)
            for call in calls
            for prefix in process_prefixes + network_prefixes
        )
        if label == "validator":
            assert validator_writer_names.isdisjoint(calls)
            open_calls = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and _qualified_name(node.func) == "os.open"
            ]
            assert len(open_calls) == 1
            assert "flags = os.O_RDONLY" in source
            for forbidden_flag in ("O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND"):
                assert forbidden_flag not in ast.unparse(open_calls[0])
    assert "_require_tmp_target" in sources["test"]
    assert "ROOT.resolve() not in resolved_target.parents" in sources["test"]


def test_package_contains_no_local_absolute_path_or_secret(
    validator: ModuleType,
) -> None:
    machine_raw = (ROOT / MACHINE_REL).read_bytes()
    human_raw = (ROOT / validator.HUMAN_PATH).read_bytes()
    for raw in (machine_raw, human_raw):
        assert b"/Users/" not in raw
        assert b"BEGIN PRIVATE KEY" not in raw
        assert b"password" not in raw.lower()
        assert b'"credentials_tokens_or_key_material_present":true' not in raw.lower()
    assert machine_raw.endswith(b"\n")
    assert validator.canonical_machine_bytes(json.loads(machine_raw)) == machine_raw


def test_no_focused_bytecode_cache_exists(validator: ModuleType) -> None:
    stems = (
        "manuscript_v3_solo_block2_precontact_instance_candidate_v1",
        "test_manuscript_v3_solo_block2_precontact_instance_candidate_v1",
    )
    found = [
        path
        for path in ROOT.rglob("*.pyc")
        if any(stem in path.name for stem in stems)
    ]
    assert found == []
