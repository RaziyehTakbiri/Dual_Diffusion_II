#!/usr/bin/env python3
"""Read-only validator for the stopped Formal-Test-30 synthetic precursor."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


SCHEMA = (
    "heterodiff-manuscript-v3-formal-test30-synthetic-coupled-path-qualification-v1"
)
REPORTED_DATE = "2026-08-30"
STATE = "SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"

ROOT = Path(__file__).resolve().parents[2]
HUMAN_PATH = "PROJECT_FORMAL_TEST30_SYNTHETIC_COUPLED_PATH_QUALIFICATION.md"
MACHINE_PATH = "research/fixtures/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.json"
VALIDATOR_PATH = "research/diagnostics/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py"
TEST_PATH = "tests/unit/test_manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py"
SOURCE_PATH = (
    "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py"
)
SPEC_PATH = "manuscript_v3/executable_method_spec.md"
CP23_PATH = "src/heterodiff/processes/plugin_bridge_counter_keyed_lineage_contract.py"
FREEZE_PATH = "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md"
FREEZE_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)

EXPECTED_SOURCE_SHA256 = (
    "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0"
)
EXPECTED_INPUT_SHA256 = {
    SPEC_PATH: "58bdfd689caa1698a07e415074e98bd3a80e9d69467d9ddec8f8471aba36c34d",
    CP23_PATH: "e728ef0149a3c3275a3b7c1efba8f038279db86cc05e06c56a09545374197557",
    FREEZE_PATH: "ab80a009f3d83be4186d3d2da13e3efd5939362e4215477dd2b1a89b870b3126",
    FREEZE_MACHINE_PATH: (
        "7ff0bf3bb5d9a03e2212f2f7f1853cde2283694b33e072931d258d98e1882590"
    ),
}

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)
AUTHORITY_SHA256 = "44ed1336dd467043e3daebe7ad85093c5ab954921a895483153c98cb6d32bb9a"
CONTROL_PREDICATE = "SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED"
FULL_CLOSURE_PREDICATE = (
    "COUPLED_PATH_COARSE_EQUALS_SUM_FINE_PERSISTENT_LINEAGE_"
    "FROZEN_LEVELS_AND_TOLERANCES_WITH_RECOMPUTATION"
)


class ValidationError(RuntimeError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def record_sha256(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("machine schema must be exact ASCII text")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256((schema + "\0").encode("ascii") + _canonical_payload_bytes(payload))


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for ordinal, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(ordinal) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("relative path is not exact text")
    parts = relative_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValidationError("unsafe relative path: " + relative_path)
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts:
        raise ValidationError("unsafe relative path: " + relative_path)
    result = root.joinpath(*pure.parts)
    if result == root or root not in result.parents:
        raise ValidationError("relative path escaped workspace")
    return result


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    rows = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("ancestor custody invalid")
        rows.append(
            (
                str(current),
                status.st_dev,
                status.st_ino,
                stat.S_IFMT(status.st_mode),
                stat.S_IMODE(status.st_mode),
                status.st_uid,
                status.st_gid,
            )
        )
        if current == root:
            break
        if root not in current.parents:
            raise ValidationError("ancestor escaped workspace")
        current = current.parent
    return tuple(reversed(rows))


def _fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(root: Path, relative_path: str) -> bytes:
    path = _safe_relative_path(root, relative_path)
    ancestors = _ancestor_snapshot(root, path)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("file custody invalid: " + relative_path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    if not (
        _fingerprint(before_path)
        == _fingerprint(before_fd)
        == _fingerprint(after_fd)
        == _fingerprint(after_path)
    ):
        raise ValidationError("file changed during stable read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during stable read")
    raw = b"".join(chunks)
    if len(raw) != after_fd.st_size:
        raise ValidationError("short stable read: " + relative_path)
    return raw


def _require_hard_pinned_sha256(
    raw: bytes, *, relative_path: str, expected_sha256: str
) -> bytes:
    if _sha256(raw) != expected_sha256:
        raise ValidationError(
            "hard-pinned SHA-256 differs before source execution: " + relative_path
        )
    return raw


def _stable_read_hard_pinned(
    root: Path, relative_path: str, expected_sha256: str
) -> bytes:
    raw = _stable_read(root, relative_path)
    return _require_hard_pinned_sha256(
        raw, relative_path=relative_path, expected_sha256=expected_sha256
    )


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    expected_symbols: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    row = {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": raw.endswith(b"\n"),
    }
    if expected_symbols is not None:
        row["expected_symbols"] = list(expected_symbols)
    return row


def _load_source(source_raw: bytes) -> ModuleType:
    """Execute exactly the stable-read, hard-pinned source payload."""

    _require_hard_pinned_sha256(
        source_raw,
        relative_path=SOURCE_PATH,
        expected_sha256=EXPECTED_SOURCE_SHA256,
    )
    _source_safety(source_raw)
    digest = _sha256(source_raw)
    module_name = (
        "_formal_test30_synthetic_coupled_path_qualification_validation_" + digest[:16]
    )
    module = ModuleType(module_name)
    module.__file__ = SOURCE_PATH
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    code = compile(
        source_raw,
        SOURCE_PATH,
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=0,
    )
    prior = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    finally:
        if prior is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = prior
    return module


def _source_safety(source_raw: bytes) -> Dict[str, Any]:
    try:
        text = source_raw.decode("utf-8")
        tree = ast.parse(text, filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("source is not valid UTF-8 Python") from error
    allowed_roots = {
        "__future__",
        "dataclasses",
        "fractions",
        "hashlib",
        "json",
        "math",
        "numbers",
        "typing",
    }
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            root_name = name.split(".", 1)[0]
            if root_name not in allowed_roots:
                raise ValidationError("source imports forbidden module: " + name)
            imports.append(name)
    banned_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "input",
        "system",
        "popen",
        "remove",
        "unlink",
        "rename",
    }
    observed_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            name = ""
        if name in banned_calls:
            raise ValidationError("source contains forbidden call: " + name)
        if name:
            observed_calls.append(name)
    required_tokens = (
        "PHYSICAL_HALF_STEP_INCREMENT_DELTA_W_NOT_STANDARDIZED_NORMAL_Z",
        "Fraction.from_float",
        "CP23BrownianAddress",
        "TAG_BROWNIAN_LEFT = 4",
        "TAG_BROWNIAN_RIGHT = 5",
        '"live_cp23_stream_consumed": False',
        '"gaussian_source_law_certified": False',
        '"general_split_step_integrated": False',
        '"independent_recomputation_present": False',
        '"formal_test30_closed": False',
    )
    for token in required_tokens:
        if token not in text:
            raise ValidationError("source lacks required scope token: " + token)
    return {
        "ast_parsed": True,
        "allowed_import_roots": sorted(allowed_roots),
        "observed_import_count": len(imports),
        "observed_call_count": len(observed_calls),
        "filesystem_write_call_present": False,
        "rng_or_entropy_import_present": False,
        "network_import_present": False,
        "subprocess_import_present": False,
        "tracker_mutation_present": False,
    }


def _qualification_receipt(module: ModuleType) -> Dict[str, Any]:
    result = module.run_frozen_synthetic_qualification()
    if type(result) is not module.SyntheticCoupledPathQualification:
        raise ValidationError("source returned another qualification type")
    expected = {
        "schema_version": "heterodiff-formal-test30-synthetic-coupled-path-v1",
        "scope": (
            "SUPPLIED_FINEST_CP23_TAG4_TAG5_VALUES;DERIVED_COARSE_SUMS;"
            "FROZEN_SYNTHETIC_BOUNDARY_EDITS;ADDITIVE_OU_HEUN;"
            "PATH_EDIT_ENDPOINT_LAW_QUALIFICATION_ONLY"
        ),
        "input_semantics": (
            "PHYSICAL_HALF_STEP_INCREMENT_DELTA_W_NOT_STANDARDIZED_NORMAL_Z;"
            "COARSE_DELTA_W_EQUALS_EXACT_DYADIC_REAL_SUM_OF_BINARY64_LEAF_VALUES;"
            "DERIVED_SUM_ROUNDED_ONCE_ONLY_WHEN_SIMULATED"
        ),
        "path_norm": (
            "MAX_ABSOLUTE_CONTINUOUS_COORDINATE_DIFFERENCE_AT_FROZEN_SHARED_"
            "PRE_AND_POST_EDIT_CHECKPOINTS_NOT_CONTINUUM_SUP_NORM"
        ),
        "endpoint_metric": (
            "MAX_COMPONENT_ONE_DIMENSIONAL_GAUSSIAN_W2_UNDER_IDEAL_IID_GAUSSIAN_"
            "MOMENT_PREMISE_AGAINST_SYNTHETIC_ANALYTIC_OU_ORACLE_NOT_PRODUCTION_"
            "ENDPOINT_LAW"
        ),
        "endpoint_law_premise": (
            "HYPOTHETICAL_INDEPENDENT_CENTERED_GAUSSIAN_HALF_INCREMENTS_WITH_"
            "VARIANCE_EQUAL_TO_HALF_STEP;NOT_ASSERTED_OF_SUPPLIED_VALUES"
        ),
        "failure_policy": "FAIL_CLOSED_NO_RETRY_NO_FALLBACK_NO_TOLERANCE_SUBSTITUTION",
        "levels": [2, 3, 4, 5],
        "explicit_input_count": 160,
        "tag4_input_count": 80,
        "tag5_input_count": 80,
        "derived_coarse_increment_count": 140,
        "coarse_sum_comparisons": 140,
        "coarse_equal_sum_fine": True,
        "persistent_lineage_across_levels": True,
        "retired_lineage_ledger_across_levels": True,
        "edit_family_counts_match_oracle": True,
        "path_pair_gaps": [
            0.012165171492164367,
            0.0031967310499734225,
            0.0014979918645190993,
        ],
        "endpoint_w2_by_level": [
            0.0007573522254040962,
            0.00018472254789865305,
            4.5611333826692866e-05,
            1.1332163239868087e-05,
        ],
        "path_contraction_passed": True,
        "finest_path_tolerance_passed": True,
        "endpoint_contraction_passed": True,
        "finest_endpoint_tolerance_passed": True,
        "frozen_levels_and_tolerances_used": True,
        "design_sha256": "72be25d5cf27b94330f9c42ea21013aef06b1ae8a70aa01b12fa23212506ed83",
        "input_sha256": "fe19802595eac780b95954124b276bf121f2a014bd651de10d7adc280da44315",
        "report_sha256": "9f01d9e2de05836a463d64403d96ce441b45dc01a56160408db13e2b7e76b498",
        "live_cp23_stream_consumed": False,
        "gaussian_source_law_certified": False,
        "general_split_step_integrated": False,
        "independent_recomputation_present": False,
        "formal_test30_closed": False,
        "passed": True,
    }
    actual = {
        key: list(getattr(result, key))
        if key in ("levels", "path_pair_gaps", "endpoint_w2_by_level")
        else getattr(result, key)
        for key in expected
    }
    _strict_equal(actual, expected, "qualification_receipt")
    return expected


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    base = ROOT if root is None else Path(root).resolve()
    human = _stable_read(base, HUMAN_PATH)
    source = _stable_read_hard_pinned(base, SOURCE_PATH, EXPECTED_SOURCE_SHA256)
    validator = _stable_read(base, VALIDATOR_PATH)
    hostile_test = _stable_read(base, TEST_PATH)
    spec = _stable_read_hard_pinned(base, SPEC_PATH, EXPECTED_INPUT_SHA256[SPEC_PATH])
    cp23 = _stable_read_hard_pinned(base, CP23_PATH, EXPECTED_INPUT_SHA256[CP23_PATH])
    freeze = _stable_read_hard_pinned(
        base, FREEZE_PATH, EXPECTED_INPUT_SHA256[FREEZE_PATH]
    )
    freeze_machine = _stable_read_hard_pinned(
        base,
        FREEZE_MACHINE_PATH,
        EXPECTED_INPUT_SHA256[FREEZE_MACHINE_PATH],
    )
    safety = _source_safety(source)
    module = _load_source(source)
    receipt = _qualification_receipt(module)
    record = {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": "ADDITIVE_PURE_SYNTHETIC_TEST30_PRECURSOR_NO_SCIENTIFIC_EFFECT",
        "scope_review": {
            "physical_file_count": 5,
            "pure_source_file_count": 1,
            "evidence_artifact_count": 4,
            "exact_package_roster": [
                SOURCE_PATH,
                HUMAN_PATH,
                MACHINE_PATH,
                VALIDATOR_PATH,
                TEST_PATH,
            ],
            "consolidated_hostile_test": True,
            "unlisted_package_file_present": False,
            "hard_pinned_source_file_count": 1,
            "hard_pinned_input_file_count": 4,
        },
        "authority_provenance": {
            "source": "CONVERSATION_VISIBLE_TEXT",
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_utf8_bytes": 207,
            "normalized_visible_text_sha256": AUTHORITY_SHA256,
            "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_UNBOUND",
            "raw_transport_bytes_bound": False,
            "conversation_envelope_bound": False,
            "account_identity_bound": False,
            "cryptographic_user_authentication_claimed": False,
            "continued_bounded_local_project_work_authorized": True,
            "external_contact_or_browsing_authorized": False,
            "data_access_or_download_authorized": False,
            "entropy_or_live_randomness_authorized": False,
            "runtime_approval_authorized": False,
            "scientific_execution_authorized": False,
            "training_authorized": False,
            "claim_promotion_or_submission_authorized": False,
            "tracker_edit_authorized_by_package": False,
        },
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_required": True,
            "fresh_anonymity_audit_required": True,
            "visible_authority_text_permitted_in_derivative": False,
            "internal_paths_hashes_or_receipts_permitted_in_derivative": False,
            "account_identity_present": False,
            "absolute_local_paths_present": False,
            "credentials_tokens_cookies_or_secrets_present": False,
            "raw_data_or_test_data_content_present": False,
            "sanitized_method_content_and_unresolved_status_only": True,
        },
        "formal_test30_contract": {
            "exact_definition": (
                "Coupled step halving converges on the mixed oracle for continuous "
                "paths, edit counts, and endpoint conditional law."
            ),
            "minimum_full_closure": FULL_CLOSURE_PREDICATE,
            "prior_state": "PENDING",
            "state_after_package": "PENDING",
            "formal_test_closed_by_package": False,
            "existing_missing_obligations_declared_closed": [],
            "existing_missing_obligations_remaining": [
                "TAG4_BROWNIAN_STREAM_CONSUMPTION",
                "TAG5_BROWNIAN_STREAM_CONSUMPTION",
                "PERSISTENT_EDIT_LINEAGE",
                "STEP_HALVING_COUPLING",
            ],
            "reason_full_test_remains_pending": (
                "SUPPLIED_VALUE_AND_SYNTHETIC_ORACLE_SCOPE_LACKS_LIVE_SOURCE_LAW_"
                "GENERAL_SPLIT_STEP_INTEGRATION_AND_INDEPENDENT_RECOMPUTATION"
            ),
        },
        "cp23_contract": {
            "philox_key": "(run_id,domain_tag)",
            "philox_counter": "(0,step_index,occurrence_serial,proposal_index)",
            "tag4_domain": "brownian_left",
            "tag5_domain": "brownian_right",
            "brownian_proposal_index": 0,
            "positive_occurrence_serial_required": True,
            "level_limb_present": False,
            "receipt_initially_unused": True,
            "receipt_certifies_brownian_law": False,
            "receipt_certifies_coarse_fine_coupling": False,
            "safe_v1_strategy": (
                "FINEST_LEVEL_ONLY_DIRECT_CP23_SHAPED_INPUTS;"
                "ALL_COARSER_VALUES_EXACT_DYADIC_DERIVATIONS_NOT_RECEIPTS"
            ),
            "independent_direct_redraw_at_each_level_permitted": False,
        },
        "frozen_design": {
            "run_id": 23030,
            "levels": [2, 3, 4, 5],
            "horizon": 1.0,
            "mean_reversion": 0.7,
            "diffusion": 0.8,
            "long_run_means": {"A": 0.35, "B": -0.25},
            "path_tolerance": 0.025,
            "endpoint_w2_tolerance": 0.006,
            "strict_contraction_required": True,
            "failure_policy": "FAIL_CLOSED_NO_RETRY_NO_FALLBACK_NO_TOLERANCE_SUBSTITUTION",
            "design_sha256": receipt["design_sha256"],
        },
        "lineage_fixture": {
            "bootstrap": [
                {"serial": 1, "kind": "A", "coordinate": 0.75},
                {"serial": 2, "kind": "B", "coordinate": -0.4},
            ],
            "accepted_edits": [
                {"boundary": 1, "kind": "birth", "source": None, "created": 3},
                {"boundary": 2, "kind": "replacement", "source": 1, "created": 4},
                {"boundary": 3, "kind": "death", "source": 2, "created": None},
            ],
            "retired_serials": [1, 2],
            "final_live_serials": [3, 4],
            "edit_family_counts_each_level": {
                "birth": 1,
                "death": 1,
                "replacement": 1,
            },
            "all_edits_coarsest_boundary_aligned": True,
            "aggregation_interval_crosses_lineage_change": False,
        },
        "qualification_receipt": receipt,
        "source_safety": safety,
        "source_execution_custody": {
            "hard_pinned_source_sha256": EXPECTED_SOURCE_SHA256,
            "hard_pinned_input_sha256": dict(EXPECTED_INPUT_SHA256),
            "all_five_hard_pins_checked_before_source_execution": True,
            "stable_read_source_payload_executed_directly": True,
            "source_path_reopened_for_execution": False,
            "cached_bytecode_loader_used": False,
            "importlib_path_loader_used": False,
        },
        "source_crosswalk": [
            {
                "ordinal": 0,
                "obligation": "EXPLICIT_CP23_TAG4_TAG5_INPUT_SHAPE",
                "symbols": ["CP23BrownianAddress", "AddressedBrownianIncrement"],
                "scope": "SUPPLIED_FINEST_BINARY64_VALUES_ONLY",
            },
            {
                "ordinal": 1,
                "obligation": "COARSE_EQUALS_SUM_FINE",
                "symbols": ["_derive_all_levels", "Fraction.from_float"],
                "scope": "EXACT_DYADIC_REAL_SUM_OF_SUPPLIED_BINARY64_LEAVES",
            },
            {
                "ordinal": 2,
                "obligation": "PERSISTENT_EDIT_LINEAGE",
                "symbols": ["_replay_lineage", "_live_roster_by_step", "_apply_edit"],
                "scope": "FROZEN_ACCEPTED_BOUNDARY_EDIT_TRANSCRIPT_ONLY",
            },
            {
                "ordinal": 3,
                "obligation": "CONTINUOUS_PATH_CHECKPOINT_CONTRACTION",
                "symbols": ["_heun_half", "_simulate_level", "_checkpoint_gap"],
                "scope": "SHARED_PRE_POST_EDIT_CHECKPOINTS_NOT_CONTINUUM_SUP_NORM",
            },
            {
                "ordinal": 4,
                "obligation": "SYNTHETIC_ENDPOINT_MOMENT_ORACLE",
                "symbols": ["_endpoint_oracle", "_simulate_level"],
                "scope": "HYPOTHETICAL_IDEAL_IID_GAUSSIAN_PREMISE_NOT_LIVE_LAW",
            },
        ],
        "control_effects": {
            "eligible_new_project_control_after_independent_audit": CONTROL_PREDICATE,
            "eligible_value_after_independent_audit": True,
            "tracker_edited": False,
            "formal_tests_closed": 0,
            "existing_fields_closed": 0,
            "blockers_closed": 0,
            "scientific_results_produced": 0,
            "claims_promoted": 0,
            "test30_state": "PENDING",
        },
        "strict_nonclaims": {
            "live_cp23_stream_consumed": False,
            "finite_words_mapped_to_gaussian_law": False,
            "gaussian_marginal_law_certified": False,
            "independence_law_certified": False,
            "stochastic_brownian_path_law_certified": False,
            "general_frozen_jump_coupling_integrated": False,
            "general_strang_split_step_integrated": False,
            "learned_or_native_drift_integrated": False,
            "production_endpoint_conditional_law_validated": False,
            "continuous_time_supremum_path_norm_validated": False,
            "scientific_runner_or_runtime_custody_present": False,
            "independent_recomputation_present": False,
            "formal_test30_closed": False,
            "tracker_edit_authorized": False,
        },
        "remaining_gaps": [
            "LIVE_TAG4_TAG5_ONE_SHOT_STREAM_CONSUMPTION_AND_WORD_TO_GAUSSIAN_MAP",
            "GAUSSIAN_MARGINAL_INDEPENDENCE_AND_CROSS_LEVEL_SOURCE_LAW",
            "COLLISION_FREE_LIVE_LEVEL_STRATEGY",
            "COUPLED_FROZEN_JUMP_PROPOSAL_AND_DESTINATION_LAW",
            "CP24_CP29_LINEAGE_DESTINATION_AND_STRANG_INTEGRATION",
            "GENERAL_CONFIGURATION_PATH_AND_LEARNED_NATIVE_DRIFT",
            "PRODUCTION_ENDPOINT_PATH_EDIT_METRICS_AND_THRESHOLDS",
            "RUNNER_RUNTIME_CUSTODY_AND_INDEPENDENT_RECOMPUTATION",
            "SEPARATE_SCIENTIFIC_EXECUTION_AUTHORITY",
        ],
        "input_bindings": [
            _binding(
                0,
                "EXECUTABLE_METHOD_SPEC",
                SPEC_PATH,
                spec,
                expected_symbols=[
                    "Coupled step halving converges on the mixed oracle",
                    "coarse Brownian increments are sums",
                ],
            ),
            _binding(
                1,
                "CP23_TAG4_TAG5_AND_LINEAGE_SOURCE",
                CP23_PATH,
                cp23,
                expected_symbols=[
                    "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT = 4",
                    "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT = 5",
                    "make_brownian_left_stream",
                    "make_brownian_right_stream",
                ],
            ),
            _binding(
                2,
                "STATIC_TEST30_GAP_INVENTORY",
                FREEZE_PATH,
                freeze,
                expected_symbols=[
                    "Formal Test 30",
                    "tag-4/tag-5 Brownian coupling",
                ],
            ),
            _binding(
                3,
                "STATIC_TEST30_EXACT_MACHINE_GAP_INVENTORY",
                FREEZE_MACHINE_PATH,
                freeze_machine,
                expected_symbols=["FORMAL_TEST_30", FULL_CLOSURE_PREDICATE],
            ),
        ],
        "package_bindings": [
            _binding(
                0,
                "PURE_COUPLED_PATH_SOURCE",
                SOURCE_PATH,
                source,
                expected_symbols=[
                    "qualify_synthetic_coupled_path",
                    "run_frozen_synthetic_qualification",
                ],
            ),
            _binding(1, "HUMAN_CONTRACT", HUMAN_PATH, human),
            _binding(2, "READ_ONLY_VALIDATOR", VALIDATOR_PATH, validator),
            _binding(3, "CONSOLIDATED_HOSTILE_TEST", TEST_PATH, hostile_test),
        ],
        "record_sha256": "0" * 64,
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _require_text_tokens(raw: bytes, tokens: Iterable[str], label: str) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(label + " is not UTF-8") from error
    for token in tokens:
        if token not in text:
            raise ValidationError(label + " lacks token: " + token)


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    base = ROOT if root is None else Path(root).resolve()
    machine_raw = _stable_read(base, MACHINE_PATH)
    try:
        if not machine_raw.endswith(b"\n") or b"\r" in machine_raw:
            raise ValidationError("machine record line ending differs")
        record = json.loads(machine_raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is not canonical ASCII JSON") from error
    if type(record) is not dict:
        raise ValidationError("machine record root must be an object")
    if canonical_machine_bytes(record) != machine_raw:
        raise ValidationError("machine record bytes are not canonical")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine self-digest differs")
    expected = expected_record(base)
    _strict_equal(record, expected, "record")

    human = _stable_read(base, HUMAN_PATH)
    _stable_read_hard_pinned(base, SOURCE_PATH, EXPECTED_SOURCE_SHA256)
    spec = _stable_read_hard_pinned(base, SPEC_PATH, EXPECTED_INPUT_SHA256[SPEC_PATH])
    cp23 = _stable_read_hard_pinned(base, CP23_PATH, EXPECTED_INPUT_SHA256[CP23_PATH])
    freeze = _stable_read_hard_pinned(
        base, FREEZE_PATH, EXPECTED_INPUT_SHA256[FREEZE_PATH]
    )
    freeze_machine = _stable_read_hard_pinned(
        base,
        FREEZE_MACHINE_PATH,
        EXPECTED_INPUT_SHA256[FREEZE_MACHINE_PATH],
    )
    _require_text_tokens(
        human,
        (
            AUTHORITY_TEXT,
            CONTROL_PREDICATE,
            "Formal Test 30 remains `PENDING`",
            "physical half-step increment",
            "standardized normal",
            "The CP23 key/counter layout has no discretization-level limb",
            "hard-pins the exact",
            "already stable-read",
            "does not reopen the source path",
            "Any publication use requires a",
            "publication-safe derivative",
        ),
        "human contract",
    )
    _require_text_tokens(
        spec,
        (
            "Coupled step halving converges on the mixed oracle for continuous paths, edit",
            "coarse Brownian increments are sums of the corresponding",
        ),
        "executable method spec",
    )
    _require_text_tokens(
        cp23,
        (
            "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT = 4",
            "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT = 5",
            "no increment law is certified",
        ),
        "CP23 source",
    )
    _require_text_tokens(
        freeze,
        ("Formal Test 30", "tag-4/tag-5 Brownian coupling"),
        "static selection freeze",
    )
    _require_text_tokens(
        freeze_machine,
        ("FORMAL_TEST_30", FULL_CLOSURE_PREDICATE),
        "static selection freeze machine record",
    )
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "eligible_after_independent_audit": True,
        "formal_test30": "PENDING",
        "formal_tests_closed": 0,
        "existing_fields_closed": 0,
        "blockers_closed": 0,
        "scientific_effect": 0,
        "validation": "PASS",
    }


def main() -> int:
    try:
        status = validate()
    except Exception as error:
        print("FORMAL_TEST30_SYNTHETIC_COUPLING_VALIDATION_FAIL: " + str(error))
        return 1
    print(
        "FORMAL_TEST30_SYNTHETIC_COUPLING_VALIDATION_PASS "
        + json.dumps(status, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
