"""Independent hostile tests for the source-independent CP74 validator."""

from __future__ import annotations

import ast
import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
import gc
import hashlib
import inspect
import json
from pathlib import Path
import pickle
import subprocess
from typing import Callable, Dict, List, Tuple, cast
import weakref

import heterodiff.evaluation.mixed_initializer_test28_independent_production_occurrence_output_schema_candidate_validator as cp74i
import heterodiff.evaluation.mixed_initializer_test28_production_occurrence_output_schema_candidate as cp74a
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_independent_production_occurrence_output_schema_candidate_validator.py"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")
_SCHEMA = (
    "cp74-test28-independent-production-occurrence-output-schema-candidate-"
    "validator-v1"
)
_SOURCE_SCHEMA = "cp74-test28-production-occurrence-output-schema-candidate-v1"
_AUTHORITATIVE_SOURCE_SHA256 = (
    "785f9738ebf168dfdf26c24751066b00a8c90a11b20bf60db8b02d8c9dbab347"
)
_AUTHORITATIVE_BUNDLE_BYTES = 512_612
_AUTHORITATIVE_BUNDLE_RECORD_SHA256 = (
    "1d01714f666bf229a0d7f0c3e0092064a96b71dd11bf4c5268ecbfe611a6904b"
)
_AUTHORITATIVE_BUNDLE_PUBLIC_SHA256 = (
    "9832a9a98f8c0545c2d42b71061f87b3a6aa959ab64fda74855949b1c5f6300d"
)
_CANDIDATE_SCHEMA_SEMANTIC_SHA256 = (
    "111ae93616ff0f5ba825d0d77d2b6790816ffe2974e8a45e1f58917b360a729a"
)
_SUMMARY_RECORD_SHA256 = (
    "bb2b206eae22a49498aed1887d8c916a864e03bea0c4b4f10c14b3ef2e6ec4f0"
)
_SUMMARY_PUBLIC_SHA256 = (
    "f8704b1a4653d4ef72f8a92b17f50b31055b43cb67d30a8733c4e2fe50f3c8d0"
)
_BUNDLE_RECORD_SHA256 = (
    "c56116aacb41d425c2ec0991b7e2298eb31c54a5088e687e0d12fcb1f48913ca"
)
_BUNDLE_PUBLIC_SHA256 = (
    "d360e9c79d46d09c880d2bfa69bab62668bd38f1538f5e39bce3c195c55e51e1"
)
_ZERO_SHA256 = "0" * 64
_RECORD_DOMAINS = {
    "predecessor_custody": b"cp74-test28-predecessor-custody-v1\0",
    "contract": b"cp74-test28-candidate-schema-contract-v1\0",
    "lifecycle_branch_rules": b"cp74-test28-lifecycle-branch-rule-v1\0",
    "crash_cut_rules": b"cp74-test28-crash-cut-rule-v1\0",
    "artifact_occurrence_rules": b"cp74-test28-artifact-occurrence-rule-v1\0",
    "execution_output_semantic_rules": (
        b"cp74-test28-execution-output-semantic-rule-v1\0"
    ),
    "output_cross_binding_rules": b"cp74-test28-output-cross-binding-rule-v1\0",
    "root": (b"cp74-test28-production-occurrence-output-schema-candidate-bundle-v1\0"),
}
_ORDERED_DOMAINS = {
    "lifecycle_branch_rules": (
        b"cp74-test28-ordered-lifecycle-branch-rule-digests-v1\0"
    ),
    "crash_cut_rules": b"cp74-test28-ordered-crash-cut-rule-digests-v1\0",
    "artifact_occurrence_rules": (
        b"cp74-test28-ordered-artifact-occurrence-rule-digests-v1\0"
    ),
    "execution_output_semantic_rules": (
        b"cp74-test28-ordered-execution-output-semantic-rule-digests-v1\0"
    ),
    "output_cross_binding_rules": (
        b"cp74-test28-ordered-output-cross-binding-rule-digests-v1\0"
    ),
}
_ORDERED_FIELDS = {
    "lifecycle_branch_rules": "ordered_lifecycle_branch_record_sha256",
    "crash_cut_rules": "ordered_crash_cut_record_sha256",
    "artifact_occurrence_rules": "ordered_artifact_occurrence_record_sha256",
    "execution_output_semantic_rules": (
        "ordered_execution_output_semantic_record_sha256"
    ),
    "output_cross_binding_rules": "ordered_output_cross_binding_record_sha256",
}
_SEMANTIC_DOMAIN = b"cp74-test28-candidate-schema-semantic-v1\0"
_ALL = (
    "CP74_INDEPENDENT_TEST28_SCHEMA_VERSION",
    "CP74_INDEPENDENT_TEST28_SCOPE",
    "CP74_INDEPENDENT_TEST28_SOURCE_SCHEMA_VERSION",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_INPUT_BYTES",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS",
    "CP74_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS",
    "CP74_INDEPENDENT_TEST28_ARTIFACT_COUNT",
    "CP74_INDEPENDENT_TEST28_REFERENCED_OUTPUT_COUNT",
    "CP74_INDEPENDENT_TEST28_LIFECYCLE_BRANCH_COUNT",
    "CP74_INDEPENDENT_TEST28_CRASH_CUT_COUNT",
    "CP74_INDEPENDENT_TEST28_OUTPUT_CROSS_BINDING_COUNT",
    "CP74_INDEPENDENT_TEST28_PRODUCTION_GATE_COUNT",
    "CP74_INDEPENDENT_TEST28_BLOCKER_COUNT",
    "CP74_INDEPENDENT_TEST28_ERROR_CODES",
    "CP74IndependentValidationError",
    "CP74IndependentPredecessorCustodyV1",
    "CP74IndependentValidationContractV1",
    "CP74IndependentCandidateSchemaValidationSummaryV1",
    "CP74IndependentProductionOccurrenceOutputSchemaCandidateValidatorBundleV1",
    "cp74_independent_candidate_schema_validator_bundle",
    "cp74_independently_validate_supplied_candidate_bundle_bytes",
    "cp74_independent_canonical_json_bytes",
    "cp74_independent_sha256",
)
_ERROR_CODES = (
    "CP74_INPUT_TYPE_MISMATCH",
    "CP74_INPUT_BYTE_LIMIT",
    "CP74_INPUT_ENCODING_INVALID",
    "CP74_INPUT_JSON_INVALID",
    "CP74_INPUT_RESOURCE_LIMIT",
    "CP74_INPUT_CANONICAL_MISMATCH",
    "CP74_INPUT_FIELD_SET_MISMATCH",
    "CP74_INPUT_FIELD_TYPE_MISMATCH",
    "CP74_INPUT_SCHEMA_MISMATCH",
    "CP74_INPUT_INVENTORY_MISMATCH",
    "CP74_INPUT_DIGEST_MISMATCH",
    "CP74_INPUT_OCCURRENCE_MISMATCH",
    "CP74_INPUT_OUTPUT_SEMANTIC_MISMATCH",
    "CP74_INPUT_CROSS_BINDING_MISMATCH",
    "CP74_RESOURCE_EXHAUSTED",
    "CP74_RECORD_TYPE_MISMATCH",
    "CP74_RECORD_NOT_ISSUED",
    "CP74_RECORD_TAMPERED",
    "CP74_INTERNAL_INVARIANT_FAILED",
)
_CUSTODY_FIELDS = (
    "schema_version",
    "authoritative_source_path",
    "authoritative_source_sha256",
    "authoritative_source_bytes",
    "authoritative_source_lf_count",
    "authoritative_schema_version",
    "expected_authoritative_bundle_canonical_json_bytes",
    "expected_authoritative_bundle_record_sha256",
    "expected_authoritative_bundle_public_sha256",
    "expected_candidate_schema_semantic_sha256",
    "v24_protocol_markdown_sha256",
    "v24_machine_manifest_sha256",
    "cp65_artifact_id_order_sha256",
    "cp65_artifact_schema_record_order_sha256",
    "cp65_referenced_output_id_order_sha256",
    "cp65_schema_semantic_sha256",
    "cp65_gate_evidence_dag_node_count",
    "cp65_gate_evidence_dag_edge_count",
    "cp65_gate_evidence_dag_semantic_sha256",
    "cp65_gate_evidence_dag_is_not_full_typed_graph",
    "cp65_gate_evidence_artifact_id_aliases",
    "cp65_typed_artifact_preimage_graph_vector_lengths",
    "cp65_typed_artifact_preimage_graph_semantic_sha256",
    "cp65_typed_digest_graph_inherited_by_hash_reference_only",
    "cp65_typed_digest_graph_revalidated_by_cp74",
    "custody_is_hash_reference_only",
    "authoritative_module_imported",
    "production_artifacts_observed",
    "record_sha256",
)
_CONTRACT_FIELDS = (
    "schema_version",
    "scope",
    "source_candidate_schema_version",
    "canonical_profile_id",
    "exact_bytes_only",
    "maximum_input_bytes",
    "maximum_json_depth",
    "maximum_json_nodes",
    "maximum_object_members",
    "maximum_array_items",
    "maximum_key_characters",
    "maximum_text_item_characters",
    "maximum_decoded_text_characters",
    "maximum_integer_decimal_digits",
    "expected_artifact_count",
    "expected_lifecycle_branch_count",
    "expected_crash_cut_count",
    "expected_referenced_output_count",
    "expected_output_cross_binding_count",
    "validation_phase_order",
    "error_codes",
    "source_project_modules_imported",
    "source_independent",
    "stdlib_only",
    "module_direct_filesystem_io",
    "path_api_exposed",
    "module_direct_clock",
    "module_direct_rng",
    "module_direct_network",
    "module_direct_subprocess",
    "production_output_bodies_accepted",
    "candidate_bundle_bytes_retained_after_successful_return",
    "dynamic_input_payload_or_output_body_cached",
    "sealed_summary_snapshot_retained_while_summary_live",
    "candidate_descriptor_packet_internally_consistent",
    "candidate_descriptor_definition_complete",
    "candidate_schema_executable",
    "primary_decision_semantics_resolved",
    "primary_decision_semantics_deferred_to_external_power_review",
    "schema_acceptance_independent",
    "authoritative_for_production",
    "production_schema_frozen",
    "production_evidence_accepted",
    "record_sha256",
)
_SUMMARY_FIELDS = (
    "schema_version",
    "source_candidate_schema_version",
    "input_canonical_json_bytes",
    "input_canonical_json_sha256",
    "candidate_bundle_record_sha256",
    "ordered_lifecycle_branch_record_sha256",
    "ordered_crash_cut_record_sha256",
    "ordered_artifact_occurrence_record_sha256",
    "ordered_execution_output_semantic_record_sha256",
    "ordered_output_cross_binding_record_sha256",
    "candidate_schema_semantic_sha256",
    "lifecycle_branch_count",
    "crash_cut_count",
    "artifact_occurrence_rule_count",
    "execution_output_semantic_rule_count",
    "output_cross_binding_rule_count",
    "canonical_syntax_verified",
    "root_schema_verified",
    "record_digests_verified",
    "inventory_verified",
    "occurrence_truth_table_verified",
    "conditional_arms_exhaustive_verified",
    "execution_output_semantics_verified",
    "cross_bindings_verified",
    "candidate_schema_inventory_complete",
    "candidate_descriptor_packet_internally_consistent",
    "candidate_descriptor_definition_complete",
    "candidate_schema_executable",
    "primary_decision_semantics_resolved",
    "primary_decision_semantics_deferred_to_external_power_review",
    "independent_structural_validation",
    "schema_acceptance_independent",
    "authoritative_for_production",
    "production_schema_frozen",
    "production_execution_and_output_schema_frozen",
    "production_receipt_schema_frozen",
    "production_artifacts_observed",
    "input_provenance_authenticated",
    "production_evidence_accepted",
    "gate_evidence_present",
    "production_gate_states",
    "draft_blocker_states",
    "formal_test_28_status",
    "formal_test_28_closed",
    "record_sha256",
)
_BUNDLE_FIELDS = (
    "schema_version",
    "scope",
    "predecessor_custody",
    "validation_contract",
    "public_caller_data_api_name",
    "public_caller_data_api_count",
    "public_parser_exposed",
    "public_path_api_exposed",
    "public_writer_exposed",
    "qualification_runner_exposed",
    "builder_validates",
    "authoritative_module_imported",
    "project_modules_imported",
    "source_independent",
    "stdlib_only",
    "production_output_bodies_accepted",
    "candidate_descriptor_packet_internally_consistent",
    "candidate_descriptor_definition_complete",
    "candidate_schema_executable",
    "primary_decision_semantics_resolved",
    "primary_decision_semantics_deferred_to_external_power_review",
    "schema_acceptance_independent",
    "authoritative_for_production",
    "production_schema_frozen",
    "production_evidence_accepted",
    "production_gate_states",
    "draft_blocker_states",
    "blocker_ledger_total_count",
    "blocker_ledger_satisfied_count",
    "blocker_ledger_missing_count",
    "formal_test_28_status",
    "formal_test_28_closed",
    "record_sha256",
)
_LAYOUTS = (
    (cp74i.CP74IndependentPredecessorCustodyV1, _CUSTODY_FIELDS),
    (cp74i.CP74IndependentValidationContractV1, _CONTRACT_FIELDS),
    (cp74i.CP74IndependentCandidateSchemaValidationSummaryV1, _SUMMARY_FIELDS),
    (
        cp74i.CP74IndependentProductionOccurrenceOutputSchemaCandidateValidatorBundleV1,
        _BUNDLE_FIELDS,
    ),
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _authoritative_payload() -> bytes:
    bundle = cp74a.cp74_production_occurrence_output_schema_candidate_bundle()
    payload = cp74a.cp74_canonical_json_bytes(bundle)
    assert len(payload) == _AUTHORITATIVE_BUNDLE_BYTES
    assert bundle.record_sha256 == _AUTHORITATIVE_BUNDLE_RECORD_SHA256
    assert bundle.candidate_schema_semantic_sha256 == _CANDIDATE_SCHEMA_SEMANTIC_SHA256
    assert cp74a.cp74_sha256(bundle) == _AUTHORITATIVE_BUNDLE_PUBLIC_SHA256
    return payload


def _decoded_payload() -> Dict[str, object]:
    return cast(Dict[str, object], json.loads(_authoritative_payload().decode("ascii")))


def _error_code(call: Callable[[], object], code: str) -> None:
    with pytest.raises(cp74i.CP74IndependentValidationError) as caught:
        call()
    assert caught.value.code == "CP74_" + code


def _record_digest(record: Dict[str, object], domain: bytes) -> str:
    body = copy.deepcopy(record)
    body["record_sha256"] = _ZERO_SHA256
    return hashlib.sha256(domain + _canonical(body)).hexdigest()


def _resign_record(record: Dict[str, object], collection: str) -> None:
    record["record_sha256"] = _record_digest(record, _RECORD_DOMAINS[collection])


def _resign_root(value: Dict[str, object]) -> bytes:
    ordered = []
    for collection, domain in _ORDERED_DOMAINS.items():
        records = cast(List[Dict[str, object]], value[collection])
        digest = hashlib.sha256(
            domain
            + b"".join(
                bytes.fromhex(cast(str, record["record_sha256"])) for record in records
            )
        ).hexdigest()
        value[_ORDERED_FIELDS[collection]] = digest
        ordered.append(digest)
    value["candidate_schema_semantic_sha256"] = hashlib.sha256(
        _SEMANTIC_DOMAIN
        + b"".join(bytes.fromhex(item) for item in ordered)
        + (64).to_bytes(2, "big")
        + (15).to_bytes(2, "big")
        + (11).to_bytes(2, "big")
        + (6).to_bytes(2, "big")
        + (24).to_bytes(2, "big")
    ).hexdigest()
    value["record_sha256"] = _record_digest(value, _RECORD_DOMAINS["root"])
    return _canonical(value)


def _resign_collections(value: Dict[str, object], *collections: str) -> bytes:
    for collection in collections:
        for record in cast(List[Dict[str, object]], value[collection]):
            _resign_record(record, collection)
    return _resign_root(value)


def _import_roots(tree: ast.AST) -> Tuple[str, ...]:
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
    return tuple(roots)


def test_independent_public_surface_constants_and_errors_are_exact() -> None:
    assert cp74i.__all__ == _ALL
    assert len(cp74i.__all__) == len(set(cp74i.__all__)) == 29
    assert cp74i.CP74_INDEPENDENT_TEST28_SCHEMA_VERSION == _SCHEMA
    assert cp74i.CP74_INDEPENDENT_TEST28_SOURCE_SCHEMA_VERSION == _SOURCE_SCHEMA
    assert (
        cp74i.CP74_INDEPENDENT_TEST28_ARTIFACT_COUNT,
        cp74i.CP74_INDEPENDENT_TEST28_REFERENCED_OUTPUT_COUNT,
        cp74i.CP74_INDEPENDENT_TEST28_LIFECYCLE_BRANCH_COUNT,
        cp74i.CP74_INDEPENDENT_TEST28_CRASH_CUT_COUNT,
        cp74i.CP74_INDEPENDENT_TEST28_OUTPUT_CROSS_BINDING_COUNT,
        cp74i.CP74_INDEPENDENT_TEST28_PRODUCTION_GATE_COUNT,
        cp74i.CP74_INDEPENDENT_TEST28_BLOCKER_COUNT,
    ) == (64, 15, 11, 6, 24, 17, 4)
    assert cp74i.CP74_INDEPENDENT_TEST28_ERROR_CODES == _ERROR_CODES


def test_independent_resource_caps_are_exact_and_live_constants() -> None:
    assert (
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_INPUT_BYTES,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_JSON_DEPTH,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_JSON_NODES,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_OBJECT_MEMBERS,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_KEY_CHARACTERS,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS,
        cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_INTEGER_DECIMAL_DIGITS,
    ) == (16_777_216, 16, 262_144, 128, 16_384, 128, 65_536, 8_388_608, 20)


@pytest.mark.parametrize(("record_type", "expected_fields"), _LAYOUTS)
def test_independent_record_layouts_and_sealing_are_exact(
    record_type: type, expected_fields: tuple
) -> None:
    assert is_dataclass(record_type)
    assert tuple(item.name for item in fields(record_type)) == expected_fields
    assert record_type.__slots__ == expected_fields
    with pytest.raises(TypeError, match="module-created only"):
        record_type()
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("HostileSubclass", (record_type,), {})


def test_independent_public_signatures_are_narrow() -> None:
    validator = inspect.signature(
        cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes
    )
    assert tuple(validator.parameters) == ("payload",)
    assert validator.parameters["payload"].annotation == "object"
    assert (
        validator.return_annotation
        == "CP74IndependentCandidateSchemaValidationSummaryV1"
    )
    builder = inspect.signature(
        cp74i.cp74_independent_candidate_schema_validator_bundle
    )
    assert tuple(builder.parameters) == ()
    assert (
        builder.return_annotation
        == "CP74IndependentProductionOccurrenceOutputSchemaCandidateValidatorBundleV1"
    )


def test_independent_scope_and_import_boundary_are_explicit() -> None:
    scope = cp74i.CP74_INDEPENDENT_TEST28_SCOPE
    required = (
        "source-independent-stdlib-only",
        "no-authoritative-module-import",
        "no-production-output-body-input",
        "no-independent-scientific-schema-acceptance",
        "no-production-schema-freeze",
        "caller-supplied-bundle-bytes-not-retained-after-successful-return",
        "module-owned-compressed-definition-oracle-is-static-not-caller-cache",
        "failure-exception-traceback-local-retention-unqualified",
        "no-path-writer-runner-or-io-api",
    )
    assert all(item in scope for item in required)
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"), filename=str(_SOURCE))
    assert set(_import_roots(tree)) == {
        "__future__",
        "base64",
        "dataclasses",
        "hashlib",
        "json",
        "re",
        "threading",
        "typing",
        "weakref",
        "zlib",
    }
    assert "heterodiff" not in _SOURCE.read_text(encoding="utf-8")


@pytest.mark.parametrize("value", ({}, [], (), b"", "", 0, False, None))
def test_independent_record_apis_reject_unissued_values(value: object) -> None:
    for function in (
        cp74i.cp74_independent_canonical_json_bytes,
        cp74i.cp74_independent_sha256,
    ):
        with pytest.raises(cp74i.CP74IndependentValidationError) as caught:
            function(value)
        assert caught.value.code == "CP74_RECORD_TYPE_MISMATCH"


def test_independent_locked_python39_structural_import() -> None:
    if not _PYTHON39.is_file():
        pytest.skip("locked Python 3.9 executable is unavailable")
    script = r"""
import heterodiff.evaluation.mixed_initializer_test28_independent_production_occurrence_output_schema_candidate_validator as cp74i
assert len(cp74i.__all__) == 29
assert cp74i.CP74_INDEPENDENT_TEST28_ARTIFACT_COUNT == 64
assert cp74i.CP74_INDEPENDENT_TEST28_REFERENCED_OUTPUT_COUNT == 15
assert cp74i.CP74_INDEPENDENT_TEST28_LIFECYCLE_BRANCH_COUNT == 11
assert cp74i.CP74_INDEPENDENT_TEST28_CRASH_CUT_COUNT == 6
assert cp74i.CP74_INDEPENDENT_TEST28_OUTPUT_CROSS_BINDING_COUNT == 24
"""
    completed = subprocess.run(
        (str(_PYTHON39), "-c", script),
        cwd=str(_ROOT),
        env={"PYTHONPATH": str(_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_independent_validator_accepts_exact_authoritative_candidate_bytes() -> None:
    payload = _authoritative_payload()
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(payload)
    decoded = _decoded_payload()
    assert summary.schema_version == _SCHEMA
    assert summary.source_candidate_schema_version == _SOURCE_SCHEMA
    assert summary.input_canonical_json_bytes == _AUTHORITATIVE_BUNDLE_BYTES
    assert summary.input_canonical_json_sha256 == hashlib.sha256(payload).hexdigest()
    assert summary.candidate_bundle_record_sha256 == _AUTHORITATIVE_BUNDLE_RECORD_SHA256
    for summary_name, root_name in (
        (
            "ordered_lifecycle_branch_record_sha256",
            "ordered_lifecycle_branch_record_sha256",
        ),
        ("ordered_crash_cut_record_sha256", "ordered_crash_cut_record_sha256"),
        (
            "ordered_artifact_occurrence_record_sha256",
            "ordered_artifact_occurrence_record_sha256",
        ),
        (
            "ordered_execution_output_semantic_record_sha256",
            "ordered_execution_output_semantic_record_sha256",
        ),
        (
            "ordered_output_cross_binding_record_sha256",
            "ordered_output_cross_binding_record_sha256",
        ),
    ):
        assert getattr(summary, summary_name) == decoded[root_name]
    assert summary.candidate_schema_semantic_sha256 == _CANDIDATE_SCHEMA_SEMANTIC_SHA256
    assert (
        summary.lifecycle_branch_count,
        summary.crash_cut_count,
        summary.artifact_occurrence_rule_count,
        summary.execution_output_semantic_rule_count,
        summary.output_cross_binding_rule_count,
    ) == (11, 6, 64, 15, 24)
    for name in (
        "canonical_syntax_verified",
        "root_schema_verified",
        "record_digests_verified",
        "inventory_verified",
        "occurrence_truth_table_verified",
        "conditional_arms_exhaustive_verified",
        "execution_output_semantics_verified",
        "cross_bindings_verified",
        "candidate_schema_inventory_complete",
        "candidate_descriptor_packet_internally_consistent",
        "candidate_descriptor_definition_complete",
        "primary_decision_semantics_deferred_to_external_power_review",
        "independent_structural_validation",
    ):
        assert getattr(summary, name) is True
    for name in (
        "candidate_schema_executable",
        "primary_decision_semantics_resolved",
        "schema_acceptance_independent",
        "authoritative_for_production",
        "production_schema_frozen",
        "production_execution_and_output_schema_frozen",
        "production_receipt_schema_frozen",
        "production_artifacts_observed",
        "input_provenance_authenticated",
        "production_evidence_accepted",
        "gate_evidence_present",
        "formal_test_28_closed",
    ):
        assert getattr(summary, name) is False
    assert summary.production_gate_states == ("MISSING",) * 17
    assert summary.draft_blocker_states == ("MISSING",) * 4
    assert summary.formal_test_28_status == "OPEN"
    assert summary.record_sha256 == _SUMMARY_RECORD_SHA256
    assert len(cp74i.cp74_independent_canonical_json_bytes(summary)) == 2_612
    assert cp74i.cp74_independent_sha256(summary) == _SUMMARY_PUBLIC_SHA256


def test_independent_bundle_pins_custody_caps_and_nonclaims() -> None:
    bundle = cp74i.cp74_independent_candidate_schema_validator_bundle()
    custody = bundle.predecessor_custody
    contract = bundle.validation_contract
    authoritative_source = (
        _ROOT
        / "src"
        / "heterodiff"
        / "evaluation"
        / "mixed_initializer_test28_production_occurrence_output_schema_candidate.py"
    ).read_bytes()
    assert (
        hashlib.sha256(authoritative_source).hexdigest() == _AUTHORITATIVE_SOURCE_SHA256
    )
    assert len(authoritative_source) == 251_995
    assert authoritative_source.count(b"\n") == 5_130
    assert custody.authoritative_source_sha256 == _AUTHORITATIVE_SOURCE_SHA256
    assert custody.authoritative_source_bytes == 251_995
    assert custody.authoritative_source_lf_count == 5_130
    assert (
        custody.expected_authoritative_bundle_canonical_json_bytes
        == _AUTHORITATIVE_BUNDLE_BYTES
    )
    assert (
        custody.expected_authoritative_bundle_record_sha256
        == _AUTHORITATIVE_BUNDLE_RECORD_SHA256
    )
    assert (
        custody.expected_authoritative_bundle_public_sha256
        == _AUTHORITATIVE_BUNDLE_PUBLIC_SHA256
    )
    assert (
        custody.expected_candidate_schema_semantic_sha256
        == _CANDIDATE_SCHEMA_SEMANTIC_SHA256
    )
    assert custody.cp65_gate_evidence_dag_node_count == 20
    assert custody.cp65_gate_evidence_dag_edge_count == 44
    assert custody.cp65_gate_evidence_dag_is_not_full_typed_graph is True
    assert custody.cp65_typed_artifact_preimage_graph_vector_lengths == (
        456,
        708,
        708,
        708,
        708,
        456,
    )
    assert custody.cp65_typed_digest_graph_inherited_by_hash_reference_only is True
    assert custody.cp65_typed_digest_graph_revalidated_by_cp74 is False
    assert custody.custody_is_hash_reference_only is True
    assert custody.authoritative_module_imported is False
    assert custody.production_artifacts_observed is False
    assert contract.validation_phase_order[6:14] == (
        "source-root-and-contract-schema",
        "ordered-inventories-identities-and-cardinalities",
        "all-individual-record-digests",
        "fixed-custody-contract-and-root-claims",
        "occurrence-lifecycle-crash-cut-and-dependency-closure",
        "execution-output-envelope-grammar-framing-and-digest-formulas",
        "output-cross-bindings-and-reciprocity",
        "ordered-semantic-and-root-digests",
    )
    assert contract.error_codes == _ERROR_CODES
    assert contract.candidate_descriptor_packet_internally_consistent is True
    assert contract.candidate_descriptor_definition_complete is True
    assert contract.candidate_schema_executable is False
    assert bundle.builder_validates is True
    assert bundle.public_caller_data_api_count == 1
    assert bundle.production_gate_states == ("MISSING",) * 17
    assert bundle.draft_blocker_states == ("MISSING",) * 4
    assert (
        bundle.blocker_ledger_total_count,
        bundle.blocker_ledger_satisfied_count,
        bundle.blocker_ledger_missing_count,
    ) == (29, 25, 4)
    for name in (
        "public_parser_exposed",
        "public_path_api_exposed",
        "public_writer_exposed",
        "qualification_runner_exposed",
        "authoritative_module_imported",
        "project_modules_imported",
        "production_output_bodies_accepted",
        "candidate_schema_executable",
        "primary_decision_semantics_resolved",
        "schema_acceptance_independent",
        "authoritative_for_production",
        "production_schema_frozen",
        "production_evidence_accepted",
        "formal_test_28_closed",
    ):
        assert getattr(bundle, name) is False
    assert bundle.record_sha256 == _BUNDLE_RECORD_SHA256
    assert len(cp74i.cp74_independent_canonical_json_bytes(bundle)) == 8_430
    assert cp74i.cp74_independent_sha256(bundle) == _BUNDLE_PUBLIC_SHA256


@pytest.mark.parametrize(
    ("payload", "code"),
    (
        (bytearray(b"{}"), "INPUT_TYPE_MISMATCH"),
        (memoryview(b"{}"), "INPUT_TYPE_MISMATCH"),
        ("{}", "INPUT_TYPE_MISMATCH"),
        (None, "INPUT_TYPE_MISMATCH"),
        (b"", "INPUT_BYTE_LIMIT"),
        (b"\xef\xbb\xbf{}", "INPUT_ENCODING_INVALID"),
        (b"\xff", "INPUT_ENCODING_INVALID"),
        (b"{", "INPUT_JSON_INVALID"),
        (b'{"x":1,"x":2}', "INPUT_JSON_INVALID"),
        (b'{"x":1.0}', "INPUT_JSON_INVALID"),
        (b'{"x":NaN}', "INPUT_JSON_INVALID"),
        (rb'{"x":"\ud800"}', "INPUT_ENCODING_INVALID"),
        (b"[]", "INPUT_FIELD_TYPE_MISMATCH"),
        (b" {}", "INPUT_CANONICAL_MISMATCH"),
        (b'{"z":0,"a":0}', "INPUT_CANONICAL_MISMATCH"),
        (rb'{"x":"\u0061"}', "INPUT_CANONICAL_MISMATCH"),
    ),
)
def test_independent_lexical_failures_have_stable_precedence(
    payload: object, code: str
) -> None:
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        code,
    )


def test_independent_input_and_decoded_text_byte_caps_are_live() -> None:
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            b"x" * (cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_INPUT_BYTES + 1)
        ),
        "INPUT_BYTE_LIMIT",
    )
    text_cap_payload = (
        b'"'
        + b"a" * cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_DECODED_TEXT_CHARACTERS
        + b'"'
    )
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            text_cap_payload
        ),
        "INPUT_RESOURCE_LIMIT",
    )


@pytest.mark.parametrize(
    ("value", "code"),
    (
        ({"k" * 128: "v" * 65_536}, "INPUT_FIELD_SET_MISMATCH"),
        ({str(index): None for index in range(128)}, "INPUT_FIELD_SET_MISMATCH"),
        ([None] * 16_384, "INPUT_FIELD_TYPE_MISMATCH"),
        ({"x": 10**19}, "INPUT_FIELD_SET_MISMATCH"),
    ),
)
def test_independent_resource_cap_boundaries_are_inclusive(
    value: object, code: str
) -> None:
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        code,
    )


@pytest.mark.parametrize(
    "value",
    (
        {"k" * 129: 0},
        {"x": "v" * 65_537},
        {"x": [None] * 16_385},
        {str(index): None for index in range(129)},
        {"x": 10**20},
    ),
)
def test_independent_structural_resource_caps_are_live(value: object) -> None:
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_RESOURCE_LIMIT",
    )


def test_independent_depth_and_node_caps_are_live() -> None:
    depth_value: object = None
    for _index in range(18):
        depth_value = [depth_value]
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(depth_value)
        ),
        "INPUT_RESOURCE_LIMIT",
    )

    boundary: object = None
    for _index in range(16):
        boundary = [boundary]
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(boundary)
        ),
        "INPUT_FIELD_TYPE_MISMATCH",
    )


def test_independent_very_deep_valid_json_is_stably_a_resource_error() -> None:
    payload = b"[" * 1_000 + b"null" + b"]" * 1_000
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_RESOURCE_LIMIT",
    )


def test_independent_depth_preflight_ignores_brackets_and_braces_inside_strings() -> None:
    payload = _canonical({"x": "[" * 1_000 + "}" * 1_000 + '\\"' * 100})
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_FIELD_SET_MISMATCH",
    )
    node_value = {str(index): [None] * 15_420 for index in range(17)}
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(node_value)
        ),
        "INPUT_RESOURCE_LIMIT",
    )


@pytest.mark.parametrize("variant", ("missing", "extra"))
def test_independent_root_field_set_is_exact(variant: str) -> None:
    value = _decoded_payload()
    if variant == "missing":
        value.pop("scope")
    else:
        value["hostile_extra"] = None
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_FIELD_SET_MISMATCH",
    )


def test_independent_exact_nested_types_precede_schema_checks() -> None:
    value = _decoded_payload()
    value["scope"] = None
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_FIELD_TYPE_MISMATCH",
    )


@pytest.mark.parametrize("target", ("root", "contract"))
def test_independent_source_schema_literals_are_exact(target: str) -> None:
    value = _decoded_payload()
    if target == "root":
        value["schema_version"] = "hostile-schema"
    else:
        cast(Dict[str, object], value["contract"])["schema_version"] = "hostile-schema"
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_SCHEMA_MISMATCH",
    )


@pytest.mark.parametrize(
    "variant",
    ("short", "duplicate-id", "wrong-ordinal", "wrong-root-count"),
)
def test_independent_ordered_inventory_cardinality_and_identity_are_exact(
    variant: str,
) -> None:
    value = _decoded_payload()
    lifecycle = cast(List[Dict[str, object]], value["lifecycle_branch_rules"])
    if variant == "short":
        lifecycle.pop()
    elif variant == "duplicate-id":
        contract = cast(Dict[str, object], value["contract"])
        identities = cast(List[object], contract["lifecycle_branch_ids"])
        identities[1] = identities[0]
    elif variant == "wrong-ordinal":
        lifecycle[-1]["branch_ordinal"] = 10
    else:
        value["lifecycle_branch_count"] = 10
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )


@pytest.mark.parametrize("variant", ("reordered", "duplicated", "long"))
def test_independent_collection_order_duplication_and_long_cardinality_fail(
    variant: str,
) -> None:
    value = _decoded_payload()
    rows = cast(List[Dict[str, object]], value["execution_output_semantic_rules"])
    if variant == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    elif variant == "duplicated":
        rows[1] = copy.deepcopy(rows[0])
    else:
        rows.append(copy.deepcopy(rows[-1]))
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )


@pytest.mark.parametrize(
    ("digest", "code"),
    (("1" * 64, "INPUT_DIGEST_MISMATCH"), ("A" * 64, "INPUT_FIELD_TYPE_MISMATCH")),
)
def test_independent_individual_record_digest_grammar_and_value_are_checked(
    digest: str, code: str
) -> None:
    value = _decoded_payload()
    cast(List[Dict[str, object]], value["crash_cut_rules"])[0]["record_sha256"] = digest
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        code,
    )


@pytest.mark.parametrize("target", ("custody", "contract"))
def test_independent_fixed_custody_and_contract_claims_cannot_be_resigned(
    target: str,
) -> None:
    value = _decoded_payload()
    if target == "custody":
        custody = cast(Dict[str, object], value["predecessor_custody"])
        custody["production_artifacts_observed"] = True
        _resign_record(custody, "predecessor_custody")
        expected = "INPUT_INVENTORY_MISMATCH"
    else:
        contract = cast(Dict[str, object], value["contract"])
        contract["production_schema_frozen"] = True
        _resign_record(contract, "contract")
        expected = "INPUT_SCHEMA_MISMATCH"
    payload = _resign_root(value)
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        expected,
    )


def test_independent_reconstructs_all_64_by_11_occurrence_truth_table_cells() -> None:
    value = _decoded_payload()
    contract = cast(Dict[str, object], value["contract"])
    artifact_ids = tuple(cast(List[str], contract["artifact_ids"]))
    branch_ids = tuple(cast(List[str], contract["lifecycle_branch_ids"]))
    occurrences = cast(List[Dict[str, object]], value["artifact_occurrence_rules"])
    lifecycle = {
        cast(str, row["branch_id"]): row
        for row in cast(List[Dict[str, object]], value["lifecycle_branch_rules"])
    }
    assert len(artifact_ids) == len(occurrences) == 64
    assert len(branch_ids) == len(lifecycle) == 11
    assert tuple(row["artifact_id"] for row in occurrences) == artifact_ids
    expression_enum = set(
        cast(List[str], contract["branch_occurrence_expression_enum"])
    )
    for row in occurrences:
        expressions = cast(List[List[str]], row["branch_occurrence_expressions"])
        assert tuple(pair[0] for pair in expressions) == branch_ids
        assert len(expressions) == len({tuple(pair) for pair in expressions}) == 11
        assert {pair[1] for pair in expressions} <= expression_enum
    by_id = {cast(str, row["artifact_id"]): row for row in occurrences}
    for branch_id in branch_ids:
        expressions = {
            artifact_id: dict(
                cast(
                    List[List[str]], by_id[artifact_id]["branch_occurrence_expressions"]
                )
            )[branch_id]
            for artifact_id in artifact_ids
        }
        assert tuple(
            artifact_id
            for artifact_id in artifact_ids
            if expressions[artifact_id] in ("EXACT_GLOBAL_ONE", "EXACT_ALL_32_SHARDS")
        ) == tuple(
            cast(List[str], lifecycle[branch_id]["always_required_artifact_ids"])
        )
        assert tuple(
            artifact_id
            for artifact_id in artifact_ids
            if expressions[artifact_id] == "ABSENT"
        ) == tuple(
            cast(List[str], lifecycle[branch_id]["always_forbidden_artifact_ids"])
        )
        assert tuple(
            artifact_id
            for artifact_id in artifact_ids
            if expressions[artifact_id] == "DURABLE_PREFIX_DEPENDENCY_CLOSED"
        ) == tuple(cast(List[str], lifecycle[branch_id]["durable_prefix_artifact_ids"]))


def test_independent_reconstructs_all_six_crash_cut_dependency_closures() -> None:
    value = _decoded_payload()
    contract = cast(Dict[str, object], value["contract"])
    artifact_ids = tuple(cast(List[str], contract["artifact_ids"]))
    order = {artifact_id: ordinal for ordinal, artifact_id in enumerate(artifact_ids)}
    occurrences = cast(List[Dict[str, object]], value["artifact_occurrence_rules"])
    dependencies = {
        cast(str, row["artifact_id"]): tuple(
            cast(List[str], row["dependency_predecessor_artifact_ids"])
        )
        for row in occurrences
    }

    def ancestors(artifact_id: str) -> set:
        pending = list(dependencies[artifact_id])
        result = set()
        while pending:
            current = pending.pop()
            if current not in result:
                result.add(current)
                pending.extend(dependencies[current])
        return result

    cuts = cast(List[Dict[str, object]], value["crash_cut_rules"])
    assert tuple(
        len(cast(List[str], cut["required_durable_artifact_ids"])) for cut in cuts
    ) == (
        20,
        20,
        22,
        29,
        38,
        39,
    )
    for cut in cuts:
        required = tuple(cast(List[str], cut["required_durable_artifact_ids"]))
        forbidden = set(cast(List[str], cut["forbidden_artifact_ids"]))
        conditional = set(cast(List[str], cut["conditional_artifact_ids"]))
        assert required == tuple(sorted(required, key=order.__getitem__))
        assert not set(required) & forbidden
        assert not conditional & forbidden
        assert (
            not {
                ancestor
                for artifact_id in required
                for ancestor in ancestors(artifact_id)
            }
            & forbidden
        )


def test_independent_reconstructs_all_15_execution_output_descriptors() -> None:
    value = _decoded_payload()
    outputs = cast(List[Dict[str, object]], value["execution_output_semantic_rules"])
    assert len(outputs) == 15
    assert (
        sum(cast(int, row["complete_attempt_instance_count"]) for row in outputs) == 201
    )
    assert (
        sum(cast(int, row["complete_attempt_total_unit_count"]) for row in outputs)
        == 196_617
    )
    for ordinal, row in enumerate(outputs, 1):
        assert row["output_ordinal"] == ordinal
        assert row["candidate_only"] is True
        assert row["production_values_present"] is False
        top_keys = tuple(cast(List[str], row["exact_top_level_keys"]))
        assert len(top_keys) == len(set(top_keys))
        grammar_paths = tuple(
            cast(str, rule).split("|", 3)[1][5:]
            for rule in cast(List[str], row["field_semantic_rules"])
            if cast(str, rule).startswith("field-grammar|path=")
        )
        assert len(grammar_paths) == len(set(grammar_paths))
        assert {"/" + key for key in top_keys} <= set(grammar_paths)
    by_id = {cast(str, row["artifact_id"]): row for row in outputs}
    assert (
        len(
            tuple(
                rule
                for rule in cast(
                    List[str], by_id["shard-raw-records"]["field_semantic_rules"]
                )
                if rule.startswith("field-grammar|path=")
            )
        )
        == 296
    )
    assert (
        len(
            tuple(
                rule
                for rule in cast(
                    List[str], by_id["shard-stable-traces"]["field_semantic_rules"]
                )
                if rule.startswith("field-grammar|path=")
            )
        )
        == 259
    )
    assert (
        by_id["shard-stable-traces"]["record_digest_domain"]
        == "plain-sha256-of-exact-canonical-stable-record-bytes-before-LF"
    )


def test_independent_reconstructs_all_24_cross_binding_rules_and_reciprocity() -> None:
    value = _decoded_payload()
    contract = cast(Dict[str, object], value["contract"])
    artifact_ids = set(cast(List[str], contract["artifact_ids"]))
    rows = cast(List[Dict[str, object]], value["output_cross_binding_rules"])
    expected_ids = tuple(cast(List[str], contract["output_cross_binding_rule_ids"]))
    assert len(rows) == 24
    assert tuple(row["rule_id"] for row in rows) == expected_ids
    by_id = {cast(str, row["rule_id"]): row for row in rows}
    for ordinal, row in enumerate(rows, 1):
        sources = set(cast(List[str], row["source_artifact_ids"]))
        targets = set(cast(List[str], row["target_artifact_ids"]))
        assert row["rule_ordinal"] == ordinal
        assert sources and targets and not sources & targets
        assert sources | targets <= artifact_ids
        assert row["required_in_complete_attempt"] is True
        assert row["candidate_only"] is True
    referenced = set()
    for output in cast(
        List[Dict[str, object]], value["execution_output_semantic_rules"]
    ):
        output_id = cast(str, output["artifact_id"])
        for rule_id in cast(List[str], output["cross_binding_rule_ids"]):
            referenced.add(rule_id)
            rule = by_id[rule_id]
            assert output_id in (
                cast(List[str], rule["source_artifact_ids"])
                + cast(List[str], rule["target_artifact_ids"])
            )
    assert referenced == set(expected_ids[:-1])


@pytest.mark.parametrize(
    ("collection", "mutation"),
    (
        ("lifecycle_branch_rules", "candidate_only"),
        ("crash_cut_rules", "required_durable_artifact_ids"),
        ("artifact_occurrence_rules", "branch_occurrence_expressions"),
        ("artifact_occurrence_rules", "manifest_bound_if_present"),
        (
            "artifact_occurrence_rules",
            "committed_marker_transitively_binds_if_present",
        ),
    ),
)
def test_independent_resigned_occurrence_lifecycle_and_crash_mutations_fail_deeply(
    collection: str, mutation: str
) -> None:
    value = _decoded_payload()
    rows = cast(List[Dict[str, object]], value[collection])
    row = rows[0]
    if mutation == "candidate_only":
        row[mutation] = False
    elif mutation == "required_durable_artifact_ids":
        cast(List[str], row[mutation]).pop()
    elif mutation == "branch_occurrence_expressions":
        cast(List[List[str]], row[mutation])[0][1] = "ABSENT"
    else:
        row[mutation] = not cast(bool, row[mutation])
    payload = _resign_collections(value, collection)
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_OCCURRENCE_MISMATCH",
    )


@pytest.mark.parametrize(
    ("collection", "field"),
    (
        ("lifecycle_branch_rules", "terminal_state"),
        ("lifecycle_branch_rules", "terminal_state_record_required"),
        ("crash_cut_rules", "terminal_state_rule"),
        ("crash_cut_rules", "recovery_rule"),
    ),
)
def test_independent_resigned_terminal_and_recovery_mutations_fail_deeply(
    collection: str, field: str
) -> None:
    value = _decoded_payload()
    row = cast(List[Dict[str, object]], value[collection])[0]
    if type(row[field]) is bool:
        row[field] = not cast(bool, row[field])
    else:
        row[field] = cast(str, row[field]) + "-hostile"
    payload = _resign_collections(value, collection)
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_OCCURRENCE_MISMATCH",
    )


@pytest.mark.parametrize("output_ordinal", range(15))
def test_independent_resigned_mutation_of_each_output_descriptor_fails_deeply(
    output_ordinal: int,
) -> None:
    value = _decoded_payload()
    rows = cast(List[Dict[str, object]], value["execution_output_semantic_rules"])
    rows[output_ordinal]["candidate_only"] = False
    payload = _resign_collections(value, "execution_output_semantic_rules")
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_OUTPUT_SEMANTIC_MISMATCH",
    )


@pytest.mark.parametrize(
    "field",
    (
        "framing_rule",
        "final_terminator_rule",
        "record_digest_domain",
        "ordered_record_digest_domain",
        "body_digest_domain",
        "exact_top_level_keys",
        "field_semantic_rules",
    ),
)
def test_independent_resigned_framing_grammar_and_digest_formula_mutations_fail(
    field: str,
) -> None:
    value = _decoded_payload()
    row = cast(List[Dict[str, object]], value["execution_output_semantic_rules"])[10]
    if type(row[field]) is list:
        cast(List[object], row[field]).pop()
    else:
        row[field] = cast(str, row[field]) + "-hostile"
    payload = _resign_collections(value, "execution_output_semantic_rules")
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_OUTPUT_SEMANTIC_MISMATCH",
    )


@pytest.mark.parametrize(
    "field",
    (
        "complete_attempt_instance_count",
        "complete_attempt_units_per_instance",
        "complete_attempt_total_unit_count",
        "closed_outcome_arms",
    ),
)
def test_independent_resigned_output_cardinality_and_terminal_arm_mutations_fail(
    field: str,
) -> None:
    value = _decoded_payload()
    row = cast(List[Dict[str, object]], value["execution_output_semantic_rules"])[0]
    if type(row[field]) is int:
        row[field] = cast(int, row[field]) + 1
    elif type(row[field]) is list:
        items = cast(List[object], row[field])
        if items:
            items.pop()
        else:
            items.append("hostile-arm")
    else:
        row[field] = cast(str, row[field]) + "-hostile"
    payload = _resign_collections(value, "execution_output_semantic_rules")
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_OUTPUT_SEMANTIC_MISMATCH",
    )


@pytest.mark.parametrize(
    "field",
    (
        "source_artifact_ids",
        "target_artifact_ids",
        "source_pointer_or_components",
        "target_pointer_or_components",
        "preimage_or_equality_formula",
        "cardinality_rule",
        "ordering_rule",
    ),
)
def test_independent_resigned_cross_binding_mutations_fail_deeply(field: str) -> None:
    value = _decoded_payload()
    row = cast(List[Dict[str, object]], value["output_cross_binding_rules"])[0]
    if type(row[field]) is list:
        cast(List[object], row[field]).pop()
    else:
        row[field] = cast(str, row[field]) + "-hostile"
    payload = _resign_collections(value, "output_cross_binding_rules")
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_CROSS_BINDING_MISMATCH",
    )


@pytest.mark.parametrize(
    "field",
    (
        "ordered_lifecycle_branch_record_sha256",
        "candidate_schema_semantic_sha256",
        "record_sha256",
    ),
)
def test_independent_enclosing_ordered_semantic_and_root_digests_are_exact(
    field: str,
) -> None:
    value = _decoded_payload()
    value[field] = "1" * 64
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_DIGEST_MISMATCH",
    )


def test_independent_inventory_precedes_digest_and_fixed_claim_interpretation() -> None:
    value = _decoded_payload()
    cast(List[Dict[str, object]], value["lifecycle_branch_rules"])[-1][
        "branch_ordinal"
    ] = 10
    custody = cast(Dict[str, object], value["predecessor_custody"])
    custody["production_artifacts_observed"] = True
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_INVENTORY_MISMATCH",
    )


def test_independent_digest_precedes_fixed_claim_and_occurrence_interpretation() -> None:
    value = _decoded_payload()
    custody = cast(Dict[str, object], value["predecessor_custody"])
    custody["production_artifacts_observed"] = True
    cast(List[Dict[str, object]], value["artifact_occurrence_rules"])[0][
        "candidate_only"
    ] = False
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_DIGEST_MISMATCH",
    )


def test_independent_occurrence_precedes_output_semantic_mismatch() -> None:
    value = _decoded_payload()
    cast(List[Dict[str, object]], value["artifact_occurrence_rules"])[0][
        "candidate_only"
    ] = False
    cast(List[Dict[str, object]], value["execution_output_semantic_rules"])[0][
        "candidate_only"
    ] = False
    payload = _resign_collections(
        value,
        "artifact_occurrence_rules",
        "execution_output_semantic_rules",
    )
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_OCCURRENCE_MISMATCH",
    )


def test_independent_output_semantics_precede_cross_binding_mismatch() -> None:
    value = _decoded_payload()
    cast(List[Dict[str, object]], value["execution_output_semantic_rules"])[0][
        "candidate_only"
    ] = False
    cast(List[Dict[str, object]], value["output_cross_binding_rules"])[0][
        "candidate_only"
    ] = False
    payload = _resign_collections(
        value,
        "execution_output_semantic_rules",
        "output_cross_binding_rules",
    )
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            payload
        ),
        "INPUT_OUTPUT_SEMANTIC_MISMATCH",
    )


def test_independent_cross_binding_precedes_enclosing_digest_mismatch() -> None:
    value = _decoded_payload()
    cast(List[Dict[str, object]], value["output_cross_binding_rules"])[0][
        "candidate_only"
    ] = False
    payload = _resign_collections(value, "output_cross_binding_rules")
    mutated = cast(Dict[str, object], json.loads(payload.decode("ascii")))
    mutated["record_sha256"] = "1" * 64
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(mutated)
        ),
        "INPUT_CROSS_BINDING_MISMATCH",
    )


def test_independent_invalid_calls_issue_no_partial_summary() -> None:
    gc.collect()
    before = sum(
        type(record) is cp74i.CP74IndependentCandidateSchemaValidationSummaryV1
        for record in cp74i._ISSUED_RECORD_SNAPSHOTS
    )
    value = _decoded_payload()
    cast(List[Dict[str, object]], value["artifact_occurrence_rules"])[0][
        "record_sha256"
    ] = ("1" * 64)
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            _canonical(value)
        ),
        "INPUT_DIGEST_MISMATCH",
    )
    gc.collect()
    after = sum(
        type(record) is cp74i.CP74IndependentCandidateSchemaValidationSummaryV1
        for record in cp74i._ISSUED_RECORD_SNAPSHOTS
    )
    assert after == before


def test_independent_success_retains_only_sealed_summary_snapshot_while_live() -> None:
    payload = _authoritative_payload()
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(payload)
    reference = weakref.ref(summary)
    assert summary in cp74i._ISSUED_RECORD_SNAPSHOTS
    assert not any(
        type(value) is bytes and value == payload for value in vars(cp74i).values()
    )
    del summary, payload
    gc.collect()
    assert reference() is None
    assert not any(
        type(record) is cp74i.CP74IndependentCandidateSchemaValidationSummaryV1
        for record in cp74i._ISSUED_RECORD_SNAPSHOTS
    )


def test_independent_concurrent_validation_is_deterministic_and_uncached() -> None:
    payload = _authoritative_payload()
    with ThreadPoolExecutor(max_workers=8) as executor:
        summaries = list(
            executor.map(
                lambda _index: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
                    payload
                ),
                range(24),
            )
        )
    assert len({id(summary) for summary in summaries}) == 24
    assert {summary.record_sha256 for summary in summaries} == {_SUMMARY_RECORD_SHA256}
    assert {cp74i.cp74_independent_sha256(summary) for summary in summaries} == {
        _SUMMARY_PUBLIC_SHA256
    }


def test_independent_concurrent_bundle_builds_validate_and_issue_fresh_records() -> None:
    with ThreadPoolExecutor(max_workers=8) as executor:
        bundles = list(
            executor.map(
                lambda _index: cp74i.cp74_independent_candidate_schema_validator_bundle(),
                range(16),
            )
        )
    assert len({id(bundle) for bundle in bundles}) == 16
    assert {bundle.record_sha256 for bundle in bundles} == {_BUNDLE_RECORD_SHA256}
    assert {cp74i.cp74_independent_sha256(bundle) for bundle in bundles} == {
        _BUNDLE_PUBLIC_SHA256
    }


def test_independent_bundle_builder_runs_deep_validation_before_issuance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gc.collect()
    before = sum(
        type(record)
        is cp74i.CP74IndependentProductionOccurrenceOutputSchemaCandidateValidatorBundleV1
        for record in cp74i._ISSUED_RECORD_SNAPSHOTS
    )

    def drift(_value: object, _expected: object) -> None:
        raise cp74i.CP74IndependentValidationError(
            "CP74_INPUT_OCCURRENCE_MISMATCH", "injected definition drift"
        )

    monkeypatch.setattr(cp74i, "_validate_occurrence_semantics", drift)
    _error_code(
        cp74i.cp74_independent_candidate_schema_validator_bundle,
        "INTERNAL_INVARIANT_FAILED",
    )
    gc.collect()
    after = sum(
        type(record)
        is cp74i.CP74IndependentProductionOccurrenceOutputSchemaCandidateValidatorBundleV1
        for record in cp74i._ISSUED_RECORD_SNAPSHOTS
    )
    assert after == before


def test_independent_bundle_builder_memoryerror_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exhausted(_value: object, _expected: object, _encoded: object) -> None:
        raise MemoryError("hostile")

    monkeypatch.setattr(cp74i, "_validate_candidate_mapping", exhausted)
    _error_code(
        cp74i.cp74_independent_candidate_schema_validator_bundle,
        "RESOURCE_EXHAUSTED",
    )


@pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit, GeneratorExit))
def test_independent_bundle_builder_control_flow_is_reraised(
    monkeypatch: pytest.MonkeyPatch, exception: type
) -> None:
    def interrupted(_value: object, _expected: object, _encoded: object) -> None:
        raise exception()

    monkeypatch.setattr(cp74i, "_validate_candidate_mapping", interrupted)
    with pytest.raises(exception):
        cp74i.cp74_independent_candidate_schema_validator_bundle()


def test_independent_records_are_nonpickleable_and_unissued_records_are_rejected() -> None:
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
        _authoritative_payload()
    )
    with pytest.raises(TypeError, match="not pickle"):
        pickle.dumps(summary)
    unissued = object.__new__(cp74i.CP74IndependentCandidateSchemaValidationSummaryV1)
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(unissued),
        "RECORD_NOT_ISSUED",
    )


def test_independent_private_sealed_base_instance_is_not_a_public_record() -> None:
    forged = object.__new__(cp74i._SealedRecord)
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(forged),
        "RECORD_TYPE_MISMATCH",
    )


def test_independent_ordinary_issued_record_mutation_is_detected() -> None:
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
        _authoritative_payload()
    )
    object.__setattr__(summary, "formal_test_28_closed", True)
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(summary),
        "RECORD_TAMPERED",
    )


def test_independent_json_equal_tuple_to_list_record_tamper_is_detected() -> None:
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
        _authoritative_payload()
    )
    object.__setattr__(
        summary, "production_gate_states", list(summary.production_gate_states)
    )
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(summary),
        "RECORD_TAMPERED",
    )


def test_independent_deleted_record_slot_tamper_is_normalized() -> None:
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
        _authoritative_payload()
    )
    object.__delattr__(summary, "schema_version")
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(summary),
        "RECORD_TAMPERED",
    )


def test_independent_nested_record_to_equal_mapping_tamper_is_detected() -> None:
    bundle = cp74i.cp74_independent_candidate_schema_validator_bundle()
    custody_mapping = json.loads(
        cp74i.cp74_independent_canonical_json_bytes(bundle.predecessor_custody).decode(
            "ascii"
        )
    )
    object.__setattr__(bundle, "predecessor_custody", custody_mapping)
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(bundle),
        "RECORD_TAMPERED",
    )


@pytest.mark.parametrize(
    "hostile",
    (object(), tuple(tuple() for _index in range(40))),
)
def test_independent_serialization_breaking_record_tamper_is_normalized(
    hostile: object,
) -> None:
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
        _authoritative_payload()
    )
    object.__setattr__(summary, "schema_version", hostile)
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(summary),
        "RECORD_TAMPERED",
    )


@pytest.mark.parametrize(
    ("field", "hostile"),
    (
        (
            "schema_version",
            "x" * (cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_TEXT_ITEM_CHARACTERS + 1),
        ),
        (
            "production_gate_states",
            ["MISSING"] * (cp74i.CP74_INDEPENDENT_TEST28_MAXIMUM_ARRAY_ITEMS + 1),
        ),
    ),
)
def test_independent_oversize_issued_record_tamper_is_normalized_before_json(
    field: str, hostile: object
) -> None:
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
        _authoritative_payload()
    )
    object.__setattr__(summary, field, hostile)
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(summary),
        "RECORD_TAMPERED",
    )


def test_independent_record_serialization_memoryerror_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
        _authoritative_payload()
    )

    def exhausted(_value: object) -> bytes:
        raise MemoryError("hostile")

    monkeypatch.setattr(cp74i, "_plain_json_bytes", exhausted)
    _error_code(
        lambda: cp74i.cp74_independent_canonical_json_bytes(summary),
        "RESOURCE_EXHAUSTED",
    )


def test_independent_validation_memoryerror_is_normalized_without_partial_issuance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gc.collect()
    before = sum(
        type(record) is cp74i.CP74IndependentCandidateSchemaValidationSummaryV1
        for record in cp74i._ISSUED_RECORD_SNAPSHOTS
    )

    def exhausted(_payload: object) -> object:
        raise MemoryError("hostile")

    monkeypatch.setattr(cp74i, "_decode_candidate_payload", exhausted)
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            b"{}"
        ),
        "RESOURCE_EXHAUSTED",
    )
    gc.collect()
    after = sum(
        type(record) is cp74i.CP74IndependentCandidateSchemaValidationSummaryV1
        for record in cp74i._ISSUED_RECORD_SNAPSHOTS
    )
    assert after == before


@pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit, GeneratorExit))
def test_independent_control_flow_exceptions_are_reraised(
    monkeypatch: pytest.MonkeyPatch, exception: type
) -> None:
    def interrupted(_payload: object) -> object:
        raise exception()

    monkeypatch.setattr(cp74i, "_decode_candidate_payload", interrupted)
    with pytest.raises(exception):
        cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(b"{}")


def test_independent_unexpected_exception_is_internal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(_payload: object) -> object:
        raise RuntimeError("hostile")

    monkeypatch.setattr(cp74i, "_decode_candidate_payload", broken)
    _error_code(
        lambda: cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(
            b"{}"
        ),
        "INTERNAL_INVARIANT_FAILED",
    )


def test_independent_locked_python39_accepts_exact_authoritative_bytes() -> None:
    if not _PYTHON39.is_file():
        pytest.skip("locked Python 3.9 executable is unavailable")
    script = r"""
import sys
import heterodiff.evaluation.mixed_initializer_test28_independent_production_occurrence_output_schema_candidate_validator as cp74i
payload = sys.stdin.buffer.read()
summary = cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(payload)
assert summary.record_sha256 == 'bb2b206eae22a49498aed1887d8c916a864e03bea0c4b4f10c14b3ef2e6ec4f0'
assert cp74i.cp74_independent_sha256(summary) == 'f8704b1a4653d4ef72f8a92b17f50b31055b43cb67d30a8733c4e2fe50f3c8d0'
"""
    completed = subprocess.run(
        (str(_PYTHON39), "-c", script),
        cwd=str(_ROOT),
        env={"PYTHONPATH": str(_ROOT / "src")},
        input=_authoritative_payload(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_independent_locked_python39_deep_json_is_resource_not_syntax_error() -> None:
    if not _PYTHON39.is_file():
        pytest.skip("locked Python 3.9 executable is unavailable")
    script = r"""
import sys
import heterodiff.evaluation.mixed_initializer_test28_independent_production_occurrence_output_schema_candidate_validator as cp74i
try:
    cp74i.cp74_independently_validate_supplied_candidate_bundle_bytes(sys.stdin.buffer.read())
except cp74i.CP74IndependentValidationError as exc:
    assert exc.code == 'CP74_INPUT_RESOURCE_LIMIT', exc.code
else:
    raise AssertionError('deep hostile unexpectedly validated')
"""
    completed = subprocess.run(
        (str(_PYTHON39), "-c", script),
        cwd=str(_ROOT),
        env={"PYTHONPATH": str(_ROOT / "src")},
        input=b"[" * 1_000 + b"null" + b"]" * 1_000,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
