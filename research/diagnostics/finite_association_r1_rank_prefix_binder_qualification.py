"""Static, zero-execution qualification of the finite-A1 R1 rank prefix.

This module deliberately does not import the production-order or rank-stress
implementation.  It only reopens a closed set of custody inputs, verifies
their exact bytes and a small fail-closed structural projection, and reports
whether that *static prefix* is still the one reviewed here.  It cannot create
a plan, consume a phase, issue a permit, launch a worker, compute a rank, train
a model, or admit D1 as production evidence.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple


QUALIFICATION_SCHEMA = "heterodiff-manuscript-v3-r1-rank-prefix-binder-qualification-v1"
QUALIFICATION_STATUS = "R1_RANK_BINDER_QUALIFIED_ZERO_EXECUTION"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
_RECORD_DOMAIN = b"heterodiff-manuscript-v3-r1-rank-prefix-binder-qualification-v1\0"
_D1_REGISTRATION_DOMAIN = (
    b"heterodiff-manuscript-v3-a1-d1-development-evidence-registration-v1\0"
)

_EXPECTED_BINDINGS = MappingProxyType(
    {
        "claim_ledger": (
            "manuscript_v3/claim_ledger.md",
            "793f7fbda938f66d771af3dc480d13dc784862a439ee65452b79c776d78e8245",
        ),
        "execution_preregistration_human": (
            "manuscript_v3/execution_preregistration.md",
            "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
        ),
        "execution_preregistration_machine": (
            "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
            "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        ),
        "scientific_route_test": (
            "tests/unit/test_manuscript_v3_scientific_route.py",
            "a76b2b7390999d2f43c1a7406f83f8347951d43b9762f3960410de3b188b01ae",
        ),
        "cp76_readiness_manifest": (
            "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json",
            "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06",
        ),
        "cp76_readiness_test": (
            "tests/unit/test_manuscript_v3_submission_readiness.py",
            "410a20e9444e5005481c2bb7c8acef0135061a86ce5bf3ad546fe3fffe83dcbc",
        ),
        "a1_specification": (
            "research/62_a1_association_guided_residual_falsification_spec.md",
            "475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c",
        ),
        "c17_theorem_target": (
            "manuscript_v3/c17_hybrid_path_error_theorem.md",
            "d11dc3a98d19a52e7ab653aca1e06598490ad098a450b526870508b4499b9d8d",
        ),
        "c17_a1_component_contract": (
            "manuscript_v3/c17_finite_a1_association_component_contract.md",
            "063a9acabd79a3c329aa721aded5c4ec8804749aaccde3d8e2096c41d5ce78c8",
        ),
        "a1_v2_freeze_human": (
            "manuscript_v3/a1_development_checkpoint_freeze_v2.md",
            "6639e0f15592558f03bae98fd7d75a56ec64564132f9631832c360a2be60f953",
        ),
        "a1_v2_freeze_machine": (
            "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v2.json",
            "b0b892db1041267defe664f59d57801e723f0115b8ac5ae9fc8656c3708cd8fc",
        ),
        "a1_v2_freeze_test": (
            "tests/unit/test_manuscript_v3_a1_development_checkpoint_freeze_v2.py",
            "fb5f6a4571d6fea7f8d7b7254648770e9d459d10a481bc3742e43330c416569c",
        ),
        "d1_freeze_human": (
            "manuscript_v3/a1_trained_checkpoint_diagnostic_freeze.md",
            "59f00d83aba2545ec80b4778cfa181b0a5a0be043bddfb42aef212aaf7533e6d",
        ),
        "d1_freeze_machine": (
            "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_freeze_v1.json",
            "11d341f65bde47caffcf3c946919c3c0c83254684fb58d0ad643b1874fb3a973",
        ),
        "d1_freeze_test": (
            "tests/unit/test_finite_association_trained_checkpoint_diagnostic.py",
            "fda8bafabcb8737035d0b342fd5639a6618900d0a958bd0dbbf0adb827ac0d25",
        ),
        "d1_orchestration_source": (
            "research/diagnostics/finite_association_trained_checkpoint_diagnostic.py",
            "7cf3a5785f6bb3576357fe8c9bd867955660c2ff2486ca0710c1398e32b1cb0e",
        ),
        "d1_evidence_human": (
            "manuscript_v3/a1_trained_checkpoint_diagnostic_evidence_registration.md",
            "bd00e6d145a5517ed8ecd34f6547c49d6d8d4eae67aeb8321037bf6ca54b3ba5",
        ),
        "d1_evidence_machine": (
            "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json",
            "b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0",
        ),
        "d1_evidence_test": (
            "tests/unit/test_manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration.py",
            "2c6ef628557c531b91c836113b9feb31e99ca48b4b7d16134c84998d739bd1e5",
        ),
        "d1_diagnostic_record": (
            "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/diagnostic-record.json",
            "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10",
        ),
        "d1_success_receipt": (
            "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/success-receipt.json",
            "eabecf04bfe0831fa14d60126c541774aaf25c58283ebb999dc3de2403e9cada",
        ),
        "d1_attempt_marker": (
            "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json",
            "acfc404eca9ed711279087861518b7e9b32dfdb5fec4aaba318b50e7b4854e14",
        ),
        "production_order_source": (
            "src/heterodiff/experiments/finite_association_production_order.py",
            "be2b4134672fc2895242d8cbb68d8c540345574f1b31ed8b04a50b88793235e1",
        ),
        "rank_stress_source": (
            "src/heterodiff/experiments/finite_association_rank_stress.py",
            "ead7544be821d58874fd07d4293adc078257f8efb47a82a1e91ea2fa0b702c67",
        ),
        "runtime_identity_source": (
            "src/heterodiff/experiments/finite_association_runtime_identity.py",
            "ba10c8053796b6d36bc02a2bea0716a443bba35fd1190333292b87701eb18bf0",
        ),
        "environment_lock": (
            "requirements/m1-reference-macos-arm64-py311.lock",
            "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d",
        ),
    }
)

_FORMAL_RUNTIME_MANIFEST = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
)
_PROTECTED_ROOTS = (
    "artifacts/a1_campaign_v4",
    "artifacts/a1_finite_association_production_order_v1",
)
_ALL_PRODUCTION_ROOTS = (
    "artifacts/a1_finite_association_production_order_v1",
    "artifacts/a1_rank_stress_gate_v1.json",
    "artifacts/a1_rank_stress_gate_v1.json.prepared.json",
    "artifacts/a1_rank_stress_gate_v1.json.parent-exit.json",
    "artifacts/a1_exact_population_campaign_v4",
    "artifacts/a1_campaign_v4",
    "artifacts/a1_primary_metrics_v1",
    "artifacts/a1_primary_metrics_v2",
    "artifacts/a1_candidate_decision_v1",
    "artifacts/a1_independent_audit_v1",
    "artifacts/a1_publication_decision_v1",
)
_DEFERRED_POSTEXECUTION_NULL_PATHS = frozenset(
    {
        "/ethics_release_and_review_plan/code_model_and_artifact_release_plan",
        "/ethics_release_and_review_plan/submission_anonymization_plan",
        "/ethics_release_and_review_plan/proof_and_code_audit_plan",
        "/ethics_release_and_review_plan/proof_and_code_audit_artifact_path",
        "/ethics_release_and_review_plan/methods_and_statistics_audit_plan",
        "/ethics_release_and_review_plan/clean_room_reproduction_audit_plan",
    }
)
_RESOLVED_POINTERS = frozenset(
    {
        "/theory_and_known_law_plan/a1_fixture_parameters",
        "/theory_and_known_law_plan/a1_evaluation_grid",
    }
)


class R1RankPrefixQualificationRefusal(RuntimeError):
    """Raised whenever the static prefix cannot be qualified fail-closed."""


def _refuse(code: str, detail: str) -> None:
    raise R1RankPrefixQualificationRefusal(code + ": " + detail)


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        _refuse("NONCANONICAL_VALUE", str(error))


def _reject_duplicate_keys(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _refuse("DUPLICATE_JSON_KEY", key)
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    _refuse("NONFINITE_JSON_NUMBER", value)


def _load_json(raw: bytes, *, role: str) -> Dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _refuse("INVALID_JSON", role + ": " + str(error))
    if type(value) is not dict:
        _refuse("INVALID_JSON_SCHEMA", role + " must be an object")
    return value


def _validated_root(workspace_root: os.PathLike[str] | str) -> Path:
    try:
        root = Path(os.fspath(workspace_root))
    except TypeError as error:
        _refuse("INVALID_WORKSPACE_ROOT", str(error))
    if not root.is_absolute():
        _refuse("INVALID_WORKSPACE_ROOT", "an absolute path is required")
    try:
        status = root.lstat()
    except OSError as error:
        _refuse("INVALID_WORKSPACE_ROOT", str(error))
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        _refuse("INVALID_WORKSPACE_ROOT", "root must be a non-symlink directory")
    return root


def _read_regular(root: Path, relative_path: str, *, role: str) -> bytes:
    path = root / relative_path
    current = root
    for part in Path(relative_path).parts[:-1]:
        current = current / part
        try:
            status = current.lstat()
        except OSError as error:
            _refuse("MISSING_BOUND_INPUT", role + ": " + str(error))
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            _refuse("UNSAFE_BOUND_INPUT", role + ": parent is not a plain directory")
    try:
        status = path.lstat()
    except OSError as error:
        _refuse("MISSING_BOUND_INPUT", role + ": " + str(error))
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        _refuse("UNSAFE_BOUND_INPUT", role + ": file is not plain and regular")
    try:
        return path.read_bytes()
    except OSError as error:
        _refuse("UNREADABLE_BOUND_INPUT", role + ": " + str(error))


def _count_null_paths(value: Any, pointer: str = "") -> Tuple[str, ...]:
    if value is None:
        return (pointer,)
    if type(value) is dict:
        paths = []
        for key, item in value.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            paths.extend(_count_null_paths(item, pointer + "/" + escaped))
        return tuple(paths)
    if type(value) is list:
        paths = []
        for index, item in enumerate(value):
            paths.extend(_count_null_paths(item, pointer + "/" + str(index)))
        return tuple(paths)
    return ()


def _literal_assignment(tree: ast.Module, name: str) -> object:
    for node in tree.body:
        if type(node) is ast.Assign:
            if any(
                type(target) is ast.Name and target.id == name
                for target in node.targets
            ):
                try:
                    return ast.literal_eval(node.value)
                except (TypeError, ValueError) as error:
                    _refuse("SOURCE_STRUCTURE_DRIFT", name + ": " + str(error))
    _refuse("SOURCE_STRUCTURE_DRIFT", "missing literal assignment " + name)


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if type(node) is ast.FunctionDef and node.name == name:
            return node
    _refuse("SOURCE_STRUCTURE_DRIFT", "missing function " + name)


def _find_exact_boolean_dict(node: ast.AST, expected: Mapping[str, bool]) -> bool:
    for candidate in ast.walk(node):
        if type(candidate) is not ast.Dict:
            continue
        observed: Dict[str, bool] = {}
        for key_node, value_node in zip(candidate.keys, candidate.values):
            if type(key_node) is ast.Constant and type(key_node.value) is str:
                if type(value_node) is ast.Constant and type(value_node.value) is bool:
                    observed[key_node.value] = value_node.value
        if all(observed.get(key) is value for key, value in expected.items()):
            return True
    return False


def _audit_order_source(raw: bytes) -> Dict[str, Any]:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename="production_order_source")
    except (UnicodeDecodeError, SyntaxError) as error:
        _refuse("SOURCE_STRUCTURE_DRIFT", str(error))
    seeds = _literal_assignment(tree, "PAIRED_SEEDS")
    budgets = _literal_assignment(tree, "SAMPLE_BUDGETS")
    exact_methods = _literal_assignment(tree, "EXACT_METHODS")
    methods = _literal_assignment(tree, "PRIMARY_METHODS")
    control_methods = _literal_assignment(tree, "CONTROL_METHODS")
    if seeds != (1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011):
        _refuse("SEED_SCHEDULE_DRIFT", repr(seeds))
    if (
        budgets != (512, 4096, 32768)
        or exact_methods != ("direct", "guided", "strong_direct")
        or methods != ("direct", "guided")
        or control_methods != ("strong_direct", "guide_input", "mismatch")
    ):
        _refuse(
            "COORDINATE_GRID_DRIFT",
            repr((budgets, exact_methods, methods, control_methods)),
        )

    plan_body = _function_node(tree, "_plan_body")
    plan_flags = {
        "production_order_authority": True,
        "production_execution_authority": False,
        "runner_integration_complete": False,
        "test_only_no_run": False,
        "opaque_evidence_admission_allowed": False,
    }
    if not _find_exact_boolean_dict(plan_body, plan_flags):
        _refuse("PLAN_GATE_DRIFT", "required plan flags were not found")

    consumption = _function_node(tree, "consume_production_phase_authorization")
    consumption_flags = {
        "production_execution_permit_issued": False,
        "runner_binding_complete": False,
        "scientific_execution_authorized": False,
    }
    if not _find_exact_boolean_dict(consumption, consumption_flags):
        _refuse("PHASE_GATE_DRIFT", "required phase-consumption flags were not found")

    permit = _function_node(tree, "issue_next_production_coordinate_permit")
    names = {node.id for node in ast.walk(permit) if type(node) is ast.Name}
    if "PermissionError" not in names or "ProductionPhaseConsumption" not in names:
        _refuse("PERMIT_REFUSAL_DRIFT", "typed refusal structure is missing")

    transitions = None
    for node in tree.body:
        if type(node) is ast.Assign and any(
            type(target) is ast.Name and target.id == "_EVIDENCE_TRANSITIONS"
            for target in node.targets
        ):
            transitions = node.value
            break
    if type(transitions) is not ast.Dict or len(transitions.keys) != 2:
        _refuse("TRANSITION_DRIFT", "transition set is not closed at two entries")
    keys = []
    for key in transitions.keys:
        if type(key) is ast.Name:
            keys.append(key.id)
        elif type(key) is ast.Constant:
            keys.append(key.value)
    if set(keys) != {"PREREQUISITE_EVIDENCE_TYPE_V2", "RANK_PHASE_OPENED_V1"}:
        _refuse("TRANSITION_DRIFT", repr(keys))
    return {
        "paired_seeds": list(seeds),
        "sample_budgets": list(budgets),
        "exact_methods": list(exact_methods),
        "primary_methods": list(methods),
        "control_methods": list(control_methods),
        "plan_gate_values": plan_flags,
        "phase_consumption_gate_values": consumption_flags,
        "implemented_evidence_transitions": [
            "FROZEN_PREREQUISITE_V2:NEW->PREREQUISITE_VERIFIED",
            "RANK_PHASE_OPENED_V1:PREREQUISITE_VERIFIED->RANK_AUTHORIZED",
        ],
        "furthest_structurally_implemented_state": "RANK_AUTHORIZED",
    }


def _audit_rank_source(raw: bytes) -> Dict[str, Any]:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename="rank_stress_source")
    except (UnicodeDecodeError, SyntaxError) as error:
        _refuse("SOURCE_STRUCTURE_DRIFT", str(error))
    functions = {node.name for node in tree.body if type(node) is ast.FunctionDef}
    required = {
        "build_frozen_association_rank_stress_fixture",
        "prepare_association_rank_stress_run",
        "launch_association_rank_stress_gate",
        "load_association_rank_stress_gate_result",
    }
    if not required.issubset(functions):
        _refuse("RANK_PREFIX_DRIFT", repr(sorted(required - functions)))
    return {
        "source_schema_qualified": True,
        "launcher_symbol_observed_but_not_called": True,
        "rank_result_loaded": False,
        "rank_computation_performed": False,
    }


def _audit_preregistration(value: Mapping[str, Any]) -> Dict[str, Any]:
    null_paths = frozenset(_count_null_paths(value))
    if len(null_paths) != 174:
        _refuse("PREREG_NULL_DRIFT", str(len(null_paths)))
    if not _RESOLVED_POINTERS.issubset(null_paths):
        _refuse("PREREG_RESOLUTION_DRIFT", "projected fields are not null")
    deferred = null_paths & _DEFERRED_POSTEXECUTION_NULL_PATHS
    if deferred != _DEFERRED_POSTEXECUTION_NULL_PATHS:
        _refuse("PREREG_DEFERRED_NULL_DRIFT", repr(sorted(deferred)))
    blockers = value.get("unresolved_blockers")
    if type(blockers) is not list or len(blockers) != 12:
        _refuse("PREREG_BLOCKER_DRIFT", "expected 12 blockers")
    stages: Dict[str, int] = {}
    for blocker in blockers:
        if type(blocker) is not dict:
            _refuse("PREREG_BLOCKER_DRIFT", "blocker is not an object")
        stage = blocker.get("blocking_stage")
        if type(stage) is not str:
            _refuse("PREREG_BLOCKER_DRIFT", "blocking stage is invalid")
        stages[stage] = stages.get(stage, 0) + 1
    expected_stages = {
        "CONFIRMATORY_EXECUTION": 10,
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 2,
    }
    if stages != expected_stages:
        _refuse("PREREG_BLOCKER_DRIFT", repr(stages))
    predicate = value.get("freeze_predicate")
    expected_predicate = {
        "all_required_preexecution_scientific_semantic_and_numeric_fields_nonnull": False,
        "all_confirmatory_execution_blockers_closed": False,
        "all_claim_promotion_and_submission_blockers_closed": False,
        "all_required_preexecution_artifacts_present_and_hash_bound": False,
        "claim_boundary_approved": False,
        "domain_admission_complete": False,
        "power_review_complete": False,
        "known_law_and_whole_method_gates_complete": False,
        "test_data_unopened_before_freeze": None,
        "freeze_receipt_present": False,
        "frozen_executable_state_if_and_only_if_execution_predicates_true": "FROZEN_EXECUTABLE",
        "claim_promotion_or_submission_permitted": False,
        "current_state": "DRAFT_NOT_EXECUTABLE",
    }
    if predicate != expected_predicate:
        _refuse("PREREG_FREEZE_DRIFT", "freeze predicate changed")
    if (
        value.get("state") != GLOBAL_STATE
        or value.get("confirmatory_execution_authorized") is not False
        or value.get("required_preexecution_null_fields_are_execution_blocking")
        is not True
        or value.get("postexecution_audit_plan_nulls_are_execution_blocking")
        is not False
        or value.get(
            "postexecution_audit_plan_nulls_block_claim_promotion_and_submission"
        )
        is not True
    ):
        _refuse("PREREG_STATE_DRIFT", "blocking or authority boundary changed")
    return {
        "historical_total_null_count": 174,
        "historical_preexecution_null_count": 168,
        "historical_deferred_postexecution_null_count": 6,
        "projected_resolved_pre_d1_null_count": 2,
        "effective_total_unresolved_null_count": 172,
        "effective_preexecution_unresolved_null_count": 166,
        "effective_deferred_postexecution_unresolved_null_count": 6,
        "unresolved_blocker_count": 12,
        "blocker_stage_counts": expected_stages,
        "blockers_closed": 0,
        "freeze_conditions_closed": 0,
    }


def _audit_d1_registration(value: Mapping[str, Any], raw: bytes) -> None:
    if raw != _canonical_json(value):
        _refuse("D1_REGISTRATION_NONCANONICAL", "raw bytes differ")
    body = dict(value)
    claimed = body.pop("record_sha256", None)
    if (
        type(claimed) is not str
        or hashlib.sha256(_D1_REGISTRATION_DOMAIN + _canonical_json(body)).hexdigest()
        != claimed
    ):
        _refuse("D1_REGISTRATION_DIGEST_DRIFT", "self digest is invalid")
    future = value.get("future_r1_boundary")
    if type(future) is not dict:
        _refuse("D1_BOUNDARY_DRIFT", "future boundary missing")
    required_false = (
        "eligible_for_confirmatory_decision",
        "may_change_overflow_policy_from_d1",
        "may_define_r1_success_from_d1",
        "may_exclude_overflow",
        "may_select_acceptance_threshold_from_d1",
        "may_select_checkpoint_from_d1",
        "may_select_primary_metric_from_d1",
        "may_select_seed_count_from_d1",
        "used_for_checkpoint_selection",
        "used_for_metric_selection",
        "used_for_overflow_policy_selection",
        "used_for_seed_selection",
        "used_for_threshold_selection",
    )
    if any(future.get(key) is not False for key in required_false):
        _refuse("D1_BOUNDARY_DRIFT", "anti-selection flag changed")
    if future.get("d1_is_prior_observed_development_knowledge") is not True:
        _refuse("D1_BOUNDARY_DRIFT", "prior-knowledge disclosure missing")
    state = value.get("state_preservation")
    if (
        type(state) is not dict
        or state.get("confirmatory_execution_authorized") is not False
        or state.get("production_execution_authorized") is not False
        or state.get("scientific_result_eligible") is not False
        or state.get("r1_a1")
        != {"qualified": False, "result": "Empty", "status": "NOT RUN"}
        or state.get("r2_hybrid")
        != {"qualified": False, "result": "Empty", "status": "NOT RUN"}
    ):
        _refuse("D1_STATE_DRIFT", "D1 state boundary changed")


def _assert_absent(root: Path, relative_path: str, *, code: str) -> None:
    path = root / relative_path
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        _refuse(code, relative_path + ": " + str(error))
    _refuse(code, relative_path)


def _record_with_digest(body: Dict[str, Any]) -> Mapping[str, Any]:
    record = dict(body)
    record["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAIN + _canonical_json(body)
    ).hexdigest()
    return MappingProxyType(record)


def audit_r1_rank_prefix(
    workspace_root: os.PathLike[str] | str,
) -> Mapping[str, Any]:
    """Return a deterministic static qualification record or refuse closed."""

    root = _validated_root(workspace_root)
    raw_by_role: Dict[str, bytes] = {}
    observed_hashes: Dict[str, str] = {}
    for role, (relative_path, expected_sha256) in _EXPECTED_BINDINGS.items():
        raw = _read_regular(root, relative_path, role=role)
        observed = hashlib.sha256(raw).hexdigest()
        if observed != expected_sha256:
            _refuse("STALE_BINDING", role + ": " + observed)
        raw_by_role[role] = raw
        observed_hashes[role] = observed

    prereg = _load_json(
        raw_by_role["execution_preregistration_machine"], role="preregistration"
    )
    prereg_projection = _audit_preregistration(prereg)
    d1_registration = _load_json(
        raw_by_role["d1_evidence_machine"], role="D1 evidence registration"
    )
    _audit_d1_registration(d1_registration, raw_by_role["d1_evidence_machine"])
    cp76 = _load_json(
        raw_by_role["cp76_readiness_manifest"], role="CP76 readiness manifest"
    )
    if (
        cp76.get("schema_version") != "cp76-manuscript-v3-submission-readiness-audit-v1"
        or cp76.get("readiness_status") != "NOT_READY"
        or cp76.get("manuscript_submission_ready") is not False
        or cp76.get("snapshot_assessed") is not True
    ):
        _refuse("CP76_STATE_DRIFT", "historical readiness snapshot changed")

    v2_freeze = _load_json(raw_by_role["a1_v2_freeze_machine"], role="V2 freeze")
    coordinate = v2_freeze.get("coordinate")
    if coordinate != {
        "accepted_example_budget": 32768,
        "batch_size": 128,
        "method": "guided",
        "optimizer_updates": 3000,
        "seed": 1729,
    }:
        _refuse("D1_COORDINATE_DRIFT", repr(coordinate))
    fixture = v2_freeze.get("fixture")
    if type(fixture) is not dict or fixture.get("production_fixture_sha256") != (
        "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
    ):
        _refuse("A1_FIXTURE_DRIFT", "fixture identity changed")

    order_projection = _audit_order_source(raw_by_role["production_order_source"])
    rank_projection = _audit_rank_source(raw_by_role["rank_stress_source"])
    if (
        coordinate["seed"] not in order_projection["paired_seeds"]
        or coordinate["accepted_example_budget"]
        not in order_projection["sample_budgets"]
        or coordinate["method"] not in order_projection["primary_methods"]
    ):
        _refuse("D1_GRID_DRIFT", "D1 is no longer inside the frozen primary grid")

    _assert_absent(root, _FORMAL_RUNTIME_MANIFEST, code="RUNTIME_MANIFEST_PRESENT")
    for relative_path in _ALL_PRODUCTION_ROOTS:
        _assert_absent(root, relative_path, code="PRODUCTION_ROOT_PRESENT")

    claim_ledger = raw_by_role["claim_ledger"].decode("utf-8")
    for literal in (
        "| C17 |",
        "**THEOREM-TARGET**",
        "| R1-A1 |",
        "| R2-HYBRID |",
        "**NOT RUN**",
    ):
        if literal not in claim_ledger:
            _refuse("CLAIM_STATE_DRIFT", literal)

    exposed_primary_examples = [
        {"seed": 1729, "accepted_example_budget": budget, "method": method}
        for budget in order_projection["sample_budgets"]
        for method in order_projection["primary_methods"]
    ]
    exposed_control_examples = [
        {"seed": 1729, "accepted_example_budget": budget, "method": method}
        for budget in order_projection["sample_budgets"]
        for method in order_projection["control_methods"]
    ]
    exposed_exact_examples = [
        {"seed": 1729, "accepted_example_budget": None, "method": method}
        for method in order_projection["exact_methods"]
    ]
    body = {
        "schema_version": QUALIFICATION_SCHEMA,
        "status": QUALIFICATION_STATUS,
        "global_state": GLOBAL_STATE,
        "qualification_kind": "STATIC_SCHEMA_AND_CUSTODY_PREFIX_ONLY",
        "closed_world_input_paths": [value[0] for value in _EXPECTED_BINDINGS.values()],
        "bound_raw_sha256": observed_hashes,
        "preregistration_projection": prereg_projection,
        "production_order_projection": order_projection,
        "rank_source_projection": rank_projection,
        "d1_prior_knowledge_boundary": {
            "observed_coordinate": {
                "seed": 1729,
                "accepted_example_budget": 32768,
                "method": "guided",
            },
            "observed_coordinate_is_inside_frozen_primary_grid": True,
            "whole_seed_exposure_selector": {
                "seed": 1729,
                "lane": "*",
                "method": "*",
                "accepted_example_budget": "*",
            },
            "whole_seed_exposure_scope": (
                "ALL_METHODS_LANES_AND_BUDGETS_"
                "WITH_BUDGET_WILDCARD_WHERE_NOT_APPLICABLE"
            ),
            "exposed_seed": 1729,
            "current_grid_examples_are_illustrative_not_exhaustive": True,
            "exposed_current_grid_examples": {
                "exact_budget_not_applicable": exposed_exact_examples,
                "primary": exposed_primary_examples,
                "controls": exposed_control_examples,
            },
            "seed_disposition": "PILOT_NONCONFIRMATORY_EXPOSED",
            "replacement_seed_selected": False,
            "seven_seed_confirmatory_design_selected": False,
            "confirmatory_seed_count_selected": False,
            "eligible_for_confirmatory_decision": False,
            "used_for_success_rule_selection": False,
            "may_define_r1_success_from_d1": False,
            "may_change_overflow_policy_from_d1": False,
            "d1_admissible_as_production_evidence": False,
        },
        "runtime_and_artifact_boundary": {
            "formal_runtime_identity_manifest_path": _FORMAL_RUNTIME_MANIFEST,
            "formal_runtime_identity_manifest_present": False,
            "protected_roots": list(_PROTECTED_ROOTS),
            "protected_roots_present": False,
            "all_checked_production_roots": list(_ALL_PRODUCTION_ROOTS),
            "any_checked_production_root_present": False,
            "production_plan_present": False,
            "production_phase_consumption_present": False,
            "production_coordinate_permit_present": False,
            "rank_result_present": False,
        },
        "authority_boundary": {
            "closed_world_paths_are_static_audit_inputs_not_execution_inputs": True,
            "development_artifacts_admissible_as_r1_execution_inputs": False,
            "development_checkpoints_admissible_as_r1_execution_inputs": False,
            "development_metrics_admissible_as_r1_execution_inputs": False,
            "development_results_admissible_as_r1_execution_inputs": False,
            "excluded_development_artifact_paths": [
                "artifacts/manuscript_v3_a1_development_checkpoint_v1",
                "artifacts/manuscript_v3_a1_development_checkpoint_v1/failure-receipt.json",
                "artifacts/manuscript_v3_a1_development_checkpoint_v2",
                "artifacts/manuscript_v3_a1_development_checkpoint_v2/success-receipt.json",
                "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1",
                "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/diagnostic-record.json",
                "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/success-receipt.json",
                "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json",
            ],
            "actual_production_plan_state": "ABSENT",
            "rank_phase_opened": False,
            "rank_phase_authorized": False,
            "production_order_admissible": False,
            "runner_binding_complete": False,
            "production_execution_authorized": False,
            "scientific_execution_authorized": False,
            "confirmatory_execution_authorized": False,
            "qualification_reusable_as_execution_permit": False,
            "plan_initialization_performed": False,
            "phase_consumption_performed": False,
            "coordinate_permit_issued": False,
            "worker_launched": False,
            "rank_computation_performed": False,
            "training_performed": False,
            "explicit_project_artifact_write_performed": False,
        },
        "state_preservation": {
            "claim_ledger_mutated": False,
            "execution_preregistration_mutated": False,
            "d1_or_v2_artifact_mutated": False,
            "c17_status": "THEOREM-TARGET",
            "c17_proved": False,
            "r1_a1_status": "NOT RUN",
            "r1_a1_qualified": False,
            "r2_hybrid_status": "NOT RUN",
            "r2_hybrid_qualified": False,
            "claim_promoted": False,
            "readiness_transition": "NONE",
            "readiness_basis": (
                "DIRECTLY_BOUND_CP76_HISTORICAL_SNAPSHOT_" "NO_LIVE_RECOMPUTATION"
            ),
            "cp76_historical_snapshot_mutated": False,
        },
    }
    return _record_with_digest(body)


def qualification_status(workspace_root: os.PathLike[str] | str) -> str:
    """Return only the static milestone label after performing the full audit."""

    return str(audit_r1_rank_prefix(workspace_root)["status"])


__all__ = (
    "R1RankPrefixQualificationRefusal",
    "audit_r1_rank_prefix",
    "qualification_status",
)
