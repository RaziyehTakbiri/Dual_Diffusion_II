#!/usr/bin/env python3
"""Read-only validator for the generic count-normalized-event CKS reference."""

from __future__ import annotations

import ast
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


SCHEMA = (
    "heterodiff-manuscript-v3-cks-count-normalized-event-reference-"
    "implementation-v1"
)
REPORTED_DATE = "2026-08-31"
STATE = "GENERIC_CKS_COUNT_NORMALIZED_EVENT_REFERENCE_IMPLEMENTATION_VALIDATED"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
CONTROL_PREDICATE = STATE

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = "src/heterodiff/evaluation/count_normalized_event_cks_reference.py"
HUMAN_PATH = "PROJECT_CKS_COUNT_NORMALIZED_EVENT_REFERENCE_IMPLEMENTATION.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_cks_count_normalized_event_reference_implementation_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_cks_count_normalized_event_reference_implementation_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_cks_count_normalized_event_reference_implementation_v1.py"
)

EXPECTED_SOURCE_SHA256 = (
    "e18cde4ed468d05fd463563117a1b4878cf00277898e4f55d4399acdf54dc217"
)
EXPECTED_SOURCE_BYTES = 41714
EXPECTED_HUMAN_SHA256 = (
    "6ab0413f900c0126094e178637106bd6375e36f697b07b92b9351bdd4fad8dd6"
)
EXPECTED_HUMAN_BYTES = 17236
EXPECTED_TEST_SHA256 = (
    "7867364a1f0f7898db88dbb4c12405c5c66ebef7c7deb40c15a398f8b3fa0c18"
)
EXPECTED_TEST_BYTES = 46846

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)
AUTHORITY_SHA256 = "44ed1336dd467043e3daebe7ad85093c5ab954921a895483153c98cb6d32bb9a"

MAX_MACHINE_JSON_DEPTH = 32
MAX_MACHINE_JSON_NODES = 20_000
MAX_MACHINE_CONTAINER_ITEMS = 8_192
MAX_MACHINE_TEXT_BYTES = 16_384
MAX_MACHINE_INTEGER_BITS = 16_384
MAX_MACHINE_BYTES = 1_000_000

EXPECTED_PREDECESSORS = (
    (
        "generic_cks_theorem_human",
        "PROJECT_CKS_COUNT_NORMALIZED_EVENT_THEOREM.md",
        16151,
        "53445cb8617fb6573105ad8912616967dcad601dcf6b30b4a28d3bf9a3034c15",
    ),
    (
        "generic_cks_theorem_machine",
        "research/fixtures/manuscript_v3_cks_count_normalized_event_theorem_v1.json",
        10073,
        "33dd22403ad7d71375c53c05028dd59567f127e233a8dc247a7a7ea730f13f6f",
    ),
    (
        "generic_cks_theorem_validator",
        "research/diagnostics/manuscript_v3_cks_count_normalized_event_theorem_v1.py",
        25728,
        "722d5781f05646e3252609939768a8e021274288ca90d9142eee7c220bf30576",
    ),
    (
        "generic_cks_theorem_test",
        "tests/unit/test_manuscript_v3_cks_count_normalized_event_theorem_v1.py",
        15192,
        "527e6349962e7180d19cfa6ebad9747a638b37a06225d3cc068fff7f1c15b61b",
    ),
    (
        "preoutcome_statistical_freeze_human",
        "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md",
        8073,
        "ca9a593c54a9d3587f58a3d414defd5cf81a3765395d5ebb8494e6effa6dd44d",
    ),
    (
        "preoutcome_statistical_freeze_machine",
        "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
        8455,
        "b8a74f1131f85aa1b7497f2f43bd34a0e30bc471953c935d4362a5a8dea1446a",
    ),
    (
        "preoutcome_statistical_freeze_validator",
        "research/diagnostics/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        22410,
        "3769017b9d6e2b1d2e1f876a84d5cfb49ccb9160e2505338ce5095b03bf790c5",
    ),
    (
        "preoutcome_statistical_freeze_test",
        "tests/unit/test_manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        28454,
        "82955f1d0cfefeef439e63ebf1cc8d478225b6529485257ccdb7a5d402d245e7",
    ),
)


EXPECTED_CORE: Dict[str, Any] = {
    "schema_version": SCHEMA,
    "reported_date": REPORTED_DATE,
    "state": STATE,
    "global_state": GLOBAL_STATE,
    "package_kind": "ADDITIVE_PURE_GENERIC_REFERENCE_IMPLEMENTATION",
    "independent_hold_repair": {
        "retired_candidate_disposition": "HOLD_P0_0_P1_1_P2_1_NO_PREDICATE_ACCEPTED",
        "retired_first_repair_disposition": "HOLD_P0_0_P1_0_P2_1_NO_PREDICATE_ACCEPTED",
        "retired_dual_contract_disposition": "HOLD_P0_0_P1_0_P2_1_EXCEPTION_CLAIM_API_SCOPE_NO_PREDICATE_ACCEPTED",
        "P1_binary64_kernel_and_score_contract_replaced": True,
        "P2_recursive_unbounded_report_prevalidation_replaced": True,
        "P2_partial_fail_closed_report_admission_contract_added": True,
        "P2_generated_report_and_standalone_hash_refusal_scopes_separated": True,
        "all_five_files_rebound_for_fresh_independent_audit": True,
    },
    "authority_boundary": {
        "normalized_visible_text": AUTHORITY_TEXT,
        "normalized_visible_text_sha256": AUTHORITY_SHA256,
        "normalized_visible_text_utf8_bytes": 207,
        "substantial_local_project_work_authorized": True,
        "agent_selected_bounded_paths_schema_and_reference_packaging": True,
        "network_contact_data_entropy_runtime_training_science_or_submission_authorized": False,
        "tracker_edit_authorized_for_this_package": False,
        "raw_transport_html_space_timestamp_account_or_signature_bound": False,
    },
    "predecessor_contract": {
        "independently_audited_generic_theorem_quartet_hard_bound": True,
        "current_preoutcome_statistical_freeze_quartet_hard_bound": True,
        "all_predecessors_and_source_verified_before_source_execution": True,
        "source_executed_from_verified_in_memory_bytes": True,
        "source_path_loader_or_bytecode_cache_used": False,
    },
    "construction_contract": {
        "finite_anonymous_event_alphabet": True,
        "caller_supplied_exact_rational_event_gram": True,
        "event_gram_positive_semidefinite_checked_exactly": True,
        "event_probability_mean_characteristicness_checked_on_zero_sum_subspace": True,
        "positive_count_channel": True,
        "positive_normalized_event_mean_channel": True,
        "empty_event_channel_is_zero_without_invented_probability": True,
        "multiplicity_retained": True,
        "permutation_invariant": True,
        "outer_gaussian_configuration_kernel": True,
        "configuration_distance_exact_rational": True,
        "authoritative_kernel_value_exact_symbolic_exp_negative_rational": True,
        "symbolic_descriptor_denotes_exact_real_gaussian_value": True,
        "binary64_kernel_value_authoritative": False,
        "binary64_used_for_identity_psd_strict_propriety_or_score_claim": False,
        "arbitrary_kernel_callback_or_module_accepted": False,
        "all_semantic_inputs_caller_supplied": True,
    },
    "strict_boundary_contract": {
        "exact_builtin_tuple_str_int_or_fraction_types_required": True,
        "bool_as_int_rejected": True,
        "subclass_substitution_rejected": True,
        "frozen_dataclass_revalidated_at_every_public_consumption_boundary": True,
        "low_level_attribute_replacement_refused": True,
        "finite_alphabet_cap_configuration_draw_token_and_component_bounds": True,
    },
    "edge_case_contract": {
        "empty_vs_empty_totalized": True,
        "empty_vs_nonempty_count_separated": True,
        "unequal_counts_count_separated": True,
        "proportional_duplicate_counts_count_separated": True,
        "equal_count_different_multiplicity_event_separated": True,
        "raw_unnormalized_formula_counterexample_present": True,
        "drop_count_counterexample_present": True,
        "binary64_constant_collapse_witness_present": True,
        "binary64_indefinite_near_one_three_by_three_gram_witness_present": True,
        "binary64_score_cancellation_witness_present": True,
        "non_psd_or_noncharacteristic_event_gram_refused": True,
        "nonpositive_scale_or_bandwidth_refused": True,
    },
    "score_contract": {
        "formula": "ONE_OVER_R_R_MINUS_ONE_SUM_R_NOT_S_K_XR_XS_MINUS_TWO_OVER_R_SUM_R_K_XR_Y",
        "R_at_least_two_required": True,
        "maximum_R": 128,
        "lower_is_better": True,
        "positive_direct_minus_guide_favors_guide_for_this_candidate": True,
        "conditional_iid_required_for_unbiasedness": True,
        "conditional_iid_tested_or_asserted_by_reference": False,
        "empirical_guide_improvement_claimed": False,
        "authoritative_score_is_canonical_exact_formal_gaussian_combination": True,
        "equal_exponents_combined_and_zero_coefficients_removed": True,
        "formal_combination_denotes_exact_real_sum": True,
        "numerical_score_value_provided": False,
        "numeric_order_sign_or_comparison_computed": False,
    },
    "report_contract": {
        "report_generation_total_over_score_domain": False,
        "report_complete_for_report_admitted_inputs_only": True,
        "report_resource_refusal_exception": "CKSReportResourceError",
        "build_reference_report_resource_refusal_invalidates_previously_constructed_score": False,
        "standalone_report_sha256_resource_refusal_implies_valid_score": False,
        "report_admission_worst_case_totality_claimed": False,
        "score_generation_supported_R_minimum": 2,
        "score_generation_supported_R_maximum": 128,
        "identical_single_symbol_R61_report_admitted": True,
        "identical_single_symbol_R62_score_succeeds_report_resource_refuses": True,
        "identical_single_symbol_R128_score_succeeds_report_resource_refuses": True,
        "domain_separated_sha256": True,
        "digest_covers_spec_inputs_symbolic_terms_formal_score_direction_premise_all_witnesses_resource_nonclosures_publication_and_result_flag": True,
        "validation_recomputes_full_report_for_report_admitted_inputs": True,
        "rehash_after_semantic_flip_still_refused": True,
        "bounded_iterative_graph_walk_before_serialization": True,
        "cycles_and_repeated_container_identities_refused": True,
        "maximum_depth": 24,
        "maximum_nodes": 10000,
        "maximum_container_items": 4096,
        "maximum_text_utf8_bytes": 4096,
        "maximum_integer_or_rational_component_bits": 8192,
        "maximum_report_bytes": 1000000,
        "exact_byte_cap_checked_immediately_after_bounded_serialization": True,
    },
    "effect_boundary": {
        "pure_source_standard_library_only": True,
        "filesystem_environment_process_network_clock_entropy_dynamic_import_project_numpy_torch_surface": False,
        "no_effect_claim_scoped_to_exact_hard_pinned_source_and_validator_path": True,
        "arbitrary_python_execution_claimed_effect_free": False,
    },
    "project_effects": {
        "project_control_predicate": CONTROL_PREDICATE,
        "project_control_value_after_independent_validation": True,
        "B04_status": "OPEN",
        "F105_status": "OPEN",
        "F106_modified": False,
        "F108_modified": False,
        "F109_through_F112_status": "OPEN",
        "gate_a_exact_metric_checkbox_closed": False,
        "domain_instance_bound": False,
        "production_metric_implemented": False,
        "fields_closed": 0,
        "blockers_closed": 0,
        "formal_tests_closed": 0,
        "results_filled": 0,
        "scientific_scorecard_effect": 0,
        "tracker_modified": False,
    },
    "anti_drift_contract": {
        "generic_theorem_was_first_B04_precursor": True,
        "this_reference_is_second_and_final_generic_B04_precursor": True,
        "third_B04_artifact_before_exact_domain_instance_or_field_disposition_permitted": False,
        "next_B04_work_must_bind_exact_domain_instance_and_close_field_or_terminal_field_no_go": True,
    },
    "publication_boundary": {
        "internal_evidence_only": True,
        "anonymous_or_public_inclusion_permitted": False,
        "absolute_user_path_credentials_person_or_dataset_rows_present": False,
        "publication_safe_derivative_requires_fresh_anonymity_provenance_proof_code_and_receipt_review": True,
    },
}


class ValidationError(RuntimeError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _validate_strict_json_value(value: object, label: str) -> None:
    stack = [(value, 0)]
    seen_containers = set()
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_MACHINE_JSON_NODES:
            raise ValidationError(label + " exceeds machine JSON node bound")
        if depth > MAX_MACHINE_JSON_DEPTH:
            raise ValidationError(label + " exceeds machine JSON depth bound")
        if type(current) is dict:
            identity = id(current)
            if identity in seen_containers:
                raise ValidationError(label + " contains a cycle or repeated container")
            seen_containers.add(identity)
            if len(current) > MAX_MACHINE_CONTAINER_ITEMS:
                raise ValidationError(label + " exceeds machine container bound")
            for key, item in current.items():
                if type(key) is not str:
                    raise ValidationError(label + " object key is not exact text")
                try:
                    encoded_key = key.encode("utf-8")
                except UnicodeEncodeError as error:
                    raise ValidationError(label + " key is not valid UTF-8") from error
                if len(encoded_key) > MAX_MACHINE_TEXT_BYTES:
                    raise ValidationError(label + " key exceeds machine text bound")
                stack.append((item, depth + 1))
            continue
        if type(current) is list:
            identity = id(current)
            if identity in seen_containers:
                raise ValidationError(label + " contains a cycle or repeated container")
            seen_containers.add(identity)
            if len(current) > MAX_MACHINE_CONTAINER_ITEMS:
                raise ValidationError(label + " exceeds machine container bound")
            stack.extend((item, depth + 1) for item in current)
            continue
        if current is None or type(current) is bool:
            continue
        if type(current) is int:
            if abs(current).bit_length() > MAX_MACHINE_INTEGER_BITS:
                raise ValidationError(label + " exceeds machine integer bound")
            continue
        if type(current) is str:
            try:
                encoded_text = current.encode("utf-8")
            except UnicodeEncodeError as error:
                raise ValidationError(label + " text is not valid UTF-8") from error
            if len(encoded_text) > MAX_MACHINE_TEXT_BYTES:
                raise ValidationError(label + " exceeds machine text bound")
            continue
        if type(current) is float and math.isfinite(current):
            continue
        raise ValidationError(label + " contains a non-exact or non-JSON value")


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    _validate_strict_json_value(value, "canonical JSON")
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if len(raw) > MAX_MACHINE_BYTES:
        raise ValidationError("canonical machine JSON exceeds its byte bound")
    return raw


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("machine record must be an exact dict")
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
        if any(type(key) is not str for key in actual) or any(
            type(key) is not str for key in expected
        ):
            raise ValidationError(label + " object key type mismatch")
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for index, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("relative path is not exact text")
    parts = relative_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValidationError("unsafe relative path")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts:
        raise ValidationError("unsafe relative path")
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


def _require_hash(raw: bytes, path: str, size: int, digest: str) -> None:
    if len(raw) != size or _sha256(raw) != digest:
        raise ValidationError("hard-pinned predecessor/source differs: " + path)


def _binding(ordinal: int, role: str, path: str, raw: bytes) -> Dict[str, Any]:
    return {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": raw.endswith(b"\n"),
    }


def _duplicate_refusing_hook(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _parse_machine(raw: bytes) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
        record = json.loads(
            text,
            object_pairs_hook=_duplicate_refusing_hook,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValidationError("nonfinite JSON constant: " + token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is not canonical ASCII JSON") from error
    if type(record) is not dict:
        raise ValidationError("machine record must be an object")
    if canonical_machine_bytes(record) != raw:
        raise ValidationError("machine record is not canonical")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine record digest mismatch")
    return record


def _attribute_root(node: ast.AST) -> Optional[str]:
    current = node
    while isinstance(current, ast.Attribute):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


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
        "typing",
    }
    imported_roots = set()
    forbidden_calls = {
        "__import__",
        "breakpoint",
        "compile",
        "eval",
        "exec",
        "input",
        "open",
    }
    forbidden_roots = {
        "asyncio",
        "builtins",
        "ctypes",
        "importlib",
        "multiprocessing",
        "numpy",
        "os",
        "pathlib",
        "random",
        "requests",
        "secrets",
        "socket",
        "subprocess",
        "sys",
        "time",
        "torch",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                imported_roots.add(root)
                if root not in allowed_roots:
                    raise ValidationError("source import is outside the pure allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or node.module is None:
                raise ValidationError("relative source import forbidden")
            root = node.module.split(".", 1)[0]
            imported_roots.add(root)
            if root not in allowed_roots:
                raise ValidationError("source import is outside the pure allowlist")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValidationError("source global/nonlocal statement forbidden")
        elif isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
            raise ValidationError("source asynchronous/generator surface forbidden")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                raise ValidationError("source effectful dynamic call forbidden")
            root = _attribute_root(node.func)
            if root in forbidden_roots:
                raise ValidationError("source effectful module call forbidden")
    if imported_roots != allowed_roots:
        raise ValidationError("source pure import roster mismatch")
    if any(
        token in source_raw
        for token in (
            b"/Users/",
            b"AKIA",
            b"BEGIN PRIVATE KEY",
            b"PhysioNet",
            b"retail",
        )
    ):
        raise ValidationError("source crosses publication-safe generic boundary")
    public_functions = {
        node.name: [argument.arg for argument in node.args.args]
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    expected_public = {
        "configuration_distance": ["spec", "left", "right"],
        "configuration_kernel": ["spec", "left", "right"],
        "conditional_cks_u_statistic": ["spec", "draws", "target"],
        "raw_formula_counterexamples": [],
        "binary64_failure_witnesses": [],
        "report_sha256": ["report"],
        "build_reference_report": ["spec", "draws", "target"],
        "validate_reference_report": ["report", "spec", "draws", "target"],
    }
    if public_functions != expected_public:
        raise ValidationError("source public function roster mismatch")
    return {
        "ast_parse": "PASS",
        "pure_import_roster": sorted(imported_roots),
        "public_callback_parameters": 0,
        "project_imports": 0,
        "effectful_imports_or_calls": 0,
    }


def _load_source(source_raw: bytes) -> ModuleType:
    _require_hash(
        source_raw, SOURCE_PATH, EXPECTED_SOURCE_BYTES, EXPECTED_SOURCE_SHA256
    )
    _source_safety(source_raw)
    digest = _sha256(source_raw)
    module_name = "_generic_cks_reference_validation_" + digest[:16]
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


def _oracle(module: ModuleType) -> Dict[str, Any]:
    spec = module.FiniteCKSSpec(
        symbols=("u", "v"),
        event_gram=((Fraction(1, 1), Fraction(2, 1)), (Fraction(2, 1), Fraction(4, 1))),
        configuration_cap=4,
        count_scale_squared=Fraction(1, 1),
        event_scale_squared=Fraction(1, 1),
        outer_bandwidth_squared=Fraction(1, 1),
    )
    empty = module.configuration_distance(spec, (), ())
    unequal = module.configuration_distance(spec, ("u",), ("u", "u"))
    multiplicity = module.configuration_distance(
        spec, ("u", "u", "v"), ("u", "v", "v")
    )
    raw = module.raw_formula_counterexamples()
    draws = ((), ("u",), ("u", "u"), ("v",))
    target = ("u", "v")
    report = module.build_reference_report(spec, draws, target)
    if not module.validate_reference_report(report, spec, draws, target):
        raise ValidationError("source report rejected its own exact recomputation")
    if (
        empty.combined_squared != Fraction(0, 1)
        or not empty.same_counting_measure
        or unequal.count_channel_squared != Fraction(1, 1)
        or unequal.event_channel_squared != Fraction(0, 1)
        or multiplicity.count_channel_squared != Fraction(0, 1)
        or multiplicity.event_channel_squared != Fraction(1, 9)
        or raw["raw_unnormalized_collision"]["raw_squared_distance"]
        != {"numerator": 0, "denominator": 1}
        or raw["drop_count_collision"]["normalized_event_squared_distance"]
        != {"numerator": 0, "denominator": 1}
    ):
        raise ValidationError("source exact edge oracle mismatch")
    score = report["conditional_cks_u_statistic"]
    if (
        score["draw_count"] != 4
        or score["score_direction"] != "LOWER_IS_BETTER"
        or score["requires_R_at_least_two"] is not True
        or score["conditional_iid_premise_asserted_by_reference"] is not False
        or score["formal_loss"]["numerical_value_provided"] is not False
        or score["formal_loss"]["numeric_order_sign_or_comparison_computed"]
        is not False
        or len(score["formal_loss"]["terms"]) != 6
    ):
        raise ValidationError("source score oracle mismatch")
    failure_witnesses = module.binary64_failure_witnesses()
    if (
        failure_witnesses["constant_collapse"]["descriptors_equal"] is not False
        or failure_witnesses["near_one_three_by_three_gram"][
            "rounded_gram_determinant"
        ]
        != {
            "numerator": -1,
            "denominator": 166153499473114484112975882535043072,
        }
        or failure_witnesses["near_one_three_by_three_gram"][
            "rounded_gram_positive_semidefinite"
        ]
        is not False
        or failure_witnesses["score_cancellation"][
            "binary64_subtraction_is_authoritative"
        ]
        is not False
    ):
        raise ValidationError("binary64 failure witness oracle mismatch")
    tampered = json.loads(json.dumps(report))
    tampered["scientific_result"] = True
    tampered["report_sha256"] = module.report_sha256(tampered)
    try:
        module.validate_reference_report(tampered, spec, draws, target)
    except module.CKSReferenceError:
        pass
    else:
        raise ValidationError("rehash-after-report-semantic-flip was accepted")
    cyclic: Dict[str, Any] = {}
    cyclic["self"] = cyclic
    try:
        module.report_sha256(cyclic)
    except module.CKSReportResourceError:
        pass
    else:
        raise ValidationError("cyclic report graph was accepted")
    shared: list = []
    try:
        module.report_sha256({"left": shared, "right": shared})
    except module.CKSReportResourceError:
        pass
    else:
        raise ValidationError("aliased report graph was accepted")
    deep: Any = None
    for _ in range(module.MAX_REPORT_JSON_DEPTH + 1):
        deep = [deep]
    try:
        module.report_sha256({"value": deep})
    except module.CKSReportResourceError:
        pass
    else:
        raise ValidationError("over-depth report graph was accepted")
    report_spec = module.FiniteCKSSpec(
        symbols=("u",),
        event_gram=((Fraction(1, 1),),),
        configuration_cap=1,
        count_scale_squared=Fraction(1, 1),
        event_scale_squared=Fraction(1, 1),
        outer_bandwidth_squared=Fraction(1, 1),
    )
    draws_61 = tuple(("u",) for _ in range(61))
    score_61 = module.conditional_cks_u_statistic(
        report_spec, draws_61, ("u",)
    )
    report_61 = module.build_reference_report(report_spec, draws_61, ("u",))
    report_contract = report_61["report_resource_contract"]
    if (
        score_61.draw_count != 61
        or report_contract["report_generation_total_over_score_domain"] is not False
        or report_contract["report_complete_for_report_admitted_inputs_only"]
        is not True
        or report_contract[
            "build_reference_report_resource_refusal_invalidates_previously_constructed_score"
        ]
        is not False
        or report_contract[
            "standalone_report_sha256_resource_refusal_implies_valid_score"
        ]
        is not False
    ):
        raise ValidationError("R61 admitted-report boundary mismatch")
    for report_draw_count in (62, 128):
        report_draws = tuple(("u",) for _ in range(report_draw_count))
        report_score = module.conditional_cks_u_statistic(
            report_spec, report_draws, ("u",)
        )
        if report_score.draw_count != report_draw_count:
            raise ValidationError("score-domain boundary mismatch")
        try:
            module.build_reference_report(report_spec, report_draws, ("u",))
        except module.CKSReportResourceError:
            pass
        else:
            raise ValidationError(
                "report resource boundary was unexpectedly admitted at R="
                + str(report_draw_count)
            )
    try:
        module.conditional_cks_u_statistic(report_spec, (("u",),), ("u",))
    except module.CKSReportResourceError as error:
        raise ValidationError("invalid score input mislabeled as report refusal") from error
    except module.CKSReferenceError:
        pass
    else:
        raise ValidationError("invalid R1 score input was accepted")
    corrupted = module.FiniteCKSSpec(
        symbols=("u",),
        event_gram=((Fraction(1, 1),),),
        configuration_cap=2,
        count_scale_squared=Fraction(1, 1),
        event_scale_squared=Fraction(1, 1),
        outer_bandwidth_squared=Fraction(1, 1),
    )
    object.__setattr__(corrupted, "configuration_cap", True)
    try:
        module.configuration_kernel(corrupted, (), ())
    except TypeError:
        pass
    else:
        raise ValidationError("low-level bool corruption was accepted")
    return {
        "empty_totalization": "PASS",
        "unequal_count_channel": "PASS",
        "equal_count_multiplicity_event_channel": "PASS",
        "raw_formula_counterexample": "PASS",
        "drop_count_counterexample": "PASS",
        "exact_symbolic_outer_gaussian": "PASS",
        "binary64_constant_collapse_witness": "PASS",
        "binary64_indefinite_near_one_gram_witness": "PASS",
        "binary64_score_cancellation_witness": "PASS",
        "R_at_least_two_exact_formal_u_statistic": "PASS",
        "lower_is_better": "PASS",
        "report_digest_and_full_recomputation": "PASS",
        "standalone_report_cycle_alias_depth_resource_refusal_without_score_validity_implication": "PASS",
        "R61_score_and_report_admitted": "PASS",
        "R62_score_succeeds_report_resource_refuses": "PASS",
        "R128_score_succeeds_report_resource_refuses": "PASS",
        "invalid_score_input_distinct_from_report_resource_refusal": "PASS",
        "tampered_frozen_spec_revalidation": "PASS",
        "scientific_result": False,
    }


def validate(root: Path = ROOT) -> Dict[str, Any]:
    if type(root) is not type(ROOT):
        raise ValidationError("root must be an exact platform pathlib path")
    resolved_root = root.resolve(strict=True)
    if not resolved_root.is_dir():
        raise ValidationError("root must resolve to a directory")

    # Read and hard-pin the source and every predecessor before source execution.
    source_raw = _stable_read(resolved_root, SOURCE_PATH)
    _require_hash(
        source_raw, SOURCE_PATH, EXPECTED_SOURCE_BYTES, EXPECTED_SOURCE_SHA256
    )
    predecessor_raw: Dict[str, bytes] = {}
    for role, path, size, digest in EXPECTED_PREDECESSORS:
        raw = _stable_read(resolved_root, path)
        _require_hash(raw, path, size, digest)
        predecessor_raw[path] = raw

    human_raw = _stable_read(resolved_root, HUMAN_PATH)
    machine_raw = _stable_read(resolved_root, MACHINE_PATH)
    validator_raw = _stable_read(resolved_root, VALIDATOR_PATH)
    test_raw = _stable_read(resolved_root, TEST_PATH)
    _require_hash(human_raw, HUMAN_PATH, EXPECTED_HUMAN_BYTES, EXPECTED_HUMAN_SHA256)
    _require_hash(test_raw, TEST_PATH, EXPECTED_TEST_BYTES, EXPECTED_TEST_SHA256)

    record = _parse_machine(machine_raw)
    core = dict(record)
    package_bindings = core.pop("package_bindings", None)
    predecessor_bindings = core.pop("predecessor_bindings", None)
    core.pop("record_sha256", None)
    _strict_equal(core, EXPECTED_CORE, "machine core")

    expected_predecessor_bindings = [
        _binding(index, role, path, predecessor_raw[path])
        for index, (role, path, _, _) in enumerate(EXPECTED_PREDECESSORS, start=1)
    ]
    _strict_equal(
        predecessor_bindings,
        expected_predecessor_bindings,
        "predecessor bindings",
    )
    package_roster = (
        ("pure_reference_source", SOURCE_PATH, source_raw),
        ("human_qualification", HUMAN_PATH, human_raw),
        ("read_only_validator", VALIDATOR_PATH, validator_raw),
        ("hostile_test", TEST_PATH, test_raw),
    )
    expected_package_bindings = [
        _binding(index, role, path, raw)
        for index, (role, path, raw) in enumerate(package_roster, start=1)
    ]
    _strict_equal(package_bindings, expected_package_bindings, "package bindings")

    safety = _source_safety(source_raw)
    module = _load_source(source_raw)
    oracle = _oracle(module)
    return {
        "validation": "PASS",
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value": True,
        "generic_reference_only": True,
        "source_safety": safety,
        "oracle": oracle,
        "B04_status": "OPEN",
        "F105_status": "OPEN",
        "F106_or_F108_modified": False,
        "F109_through_F112_status": "OPEN",
        "gate_a_exact_metric_checkbox_closed": False,
        "fields_blockers_formal_tests_or_results_closed": 0,
        "scientific_scorecard_effect": 0,
        "tracker_modified": False,
        "network_data_entropy_runtime_training_or_science_performed": False,
        "third_generic_B04_precursor_permitted": False,
    }


def main() -> int:
    try:
        result = validate(ROOT)
    except Exception as error:
        print("FAIL: " + str(error))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
