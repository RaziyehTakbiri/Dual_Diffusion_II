"""Hostile independence tests for the CP65 source-independent validator."""

from __future__ import annotations

import ast
import gc
import hashlib
import inspect
import json
import pickle
from pathlib import Path
import runpy
import weakref

import heterodiff.evaluation.mixed_initializer_test28_independent_production_schema_preimage_validator as independent
import heterodiff.evaluation.mixed_initializer_test28_production_schema_preimage_validator as authoritative
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_independent_production_schema_preimage_validator.py"
)
_AUTHORITATIVE_HOSTILE_TEST = (
    _ROOT
    / "tests"
    / "unit"
    / "test_mixed_initializer_test28_production_schema_preimage_validator.py"
)

_AUTHORITATIVE_CANONICAL_BYTES = 2_488_135
_AUTHORITATIVE_CANONICAL_SHA256 = (
    "fd755453f7359f8db7c1dbbeea63748fd74551707ff8f5fd7e5d80a6982aa576"
)
_AUTHORITATIVE_SCHEMA_SEMANTIC_SHA256 = (
    "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
)
_AUTHORITATIVE_RECORD_SHA256 = (
    "597f2b4b557bffb529d951858fd84e454135220db0c19dcd05fcf7ce93710f89"
)
_AUTHORITATIVE_CATALOG_COUNTS = {
    "artifact_ids": 64,
    "transient_path_ids": 310,
    "field_rule_ids": 801,
    "digest_contract_ids": 211,
    "sha256_pointer_classification_ids": 315,
    "predicate_ids": 1_031,
    "gate_ids": 17,
    "auxiliary_bound_ids": 65,
}

_PSS_VECTOR_MESSAGE = b"cp65-development-rsa-pss-vector-v1\n"
_PSS_VECTOR_MODULUS = bytes.fromhex(
    "c09f7750d9ed2c65a1e67a91e3f2710c2035390cc119d5259caaec207fa5eadb"
    "8ee92336fe339eca2fd3d8c8bc86eea0be11cbeac7affe4b413d37607f351ef2"
    "717cc3d82df072a1f415cd002611d45e809e7388e4edb57015896a54e56e60c1"
    "1b36cbbe1386307b9aaed4e72654131851407e10185bd8ea5394d6459379e936"
    "9093ea429a170b4a336c59baadcc99c3f51ad41937487196db4572b92eaed5ee"
    "f5054c31e835d7f3ce78c222835e7413d0b6a2754d09caaa108e4f0223d0c888"
    "215f84023b7e3bf630f10f15ccec39628a671960b0a6efc69b6258a8d988a7c8"
    "3290fc4213fd0cba642e10140591d71215e57070058f787f513a3de8d51614754"
    "fa8ea8f7547af53035d62802e9ee876f11f7333db7d31e6f9cd4af1a64befdf8"
    "ba7d81427dcf67f46869f054dda26c500fb18a50f090947fae422c64c5a28f4f"
    "9aad7d226e35cc0188b524a2eaf104910ba3c6d2478044272b09f33c0a2af18b"
    "1d143cad58518d3127adb83636a7fdcb1160e01a841fbe1b469ffe32f649613"
)
_PSS_VECTOR_SIGNATURE = bytes.fromhex(
    "70584af97b6d3e3cbd530fd53c1e6477256ac5b15ce30b7f4e60423a6a5dcbcd"
    "0861436bda270bd17d7f9b1b854799b80feed86c8eb60cf9b5cb9556e8683138f"
    "dfba1b2d4928335131b0f81154cf0be416e6219dbae6fedb8f667909d40f369d"
    "2d8af93ecabc2f032dad92fc631b9eac115e5190733316258924a34b3b08b838"
    "a3d6fcd6ce395ccb4388c1ae9369ac5dd42d3867f67cd68a5b8e558150a60511"
    "ee204529c88b61a8762bd9d72cf7f21842242d6ef4e6a43f850c076e16c07b49"
    "5916a2538b3f3fbb1b4c3d8e3ee4a27af12813328d8f3e718257709b8a8e5699"
    "36509c156fcaa294febc5353107ae8185c10f772e06e5625dad049ef1f790ae49"
    "00aafd931f66d175b5afad34c756d7405f238d77a822797afadf79f59baaf38a"
    "7ef04b7a2af89ef8d8e9fe6ecc1b2667fb7e0916259df732c532a60d41332f8b"
    "d0064c5b7fd973aea4178f96e986bf07413a9418d594b97e431b0d9398b57fc8"
    "6e5be6e6e04e481af124e2054d629cdd104a69ce5d860e383bf3eb2a78348e"
)


def _validation_semantics(record: object, module: object) -> dict:
    payload = module.cp65_canonical_json_bytes(record)
    document = json.loads(payload)
    document.pop("record_sha256")
    return document


def _independent_validation_semantics(record: object) -> dict:
    payload = independent.cp65_independent_canonical_json_bytes(record)
    document = json.loads(payload)
    document.pop("record_sha256")
    return document


def _assert_never_evidence_or_authority(result: object) -> None:
    for name in (
        "external_production_receipts_observed",
        "external_provenance_verified",
        "filesystem_observed",
        "source_authority_verified",
        "authorization_trust_root_bound",
        "authority_verified",
        "production_evidence_accepted",
        "gate_transition_permitted",
        "launch_authorized",
        "execution_permitted",
    ):
        assert getattr(result, name) is False
    assert result.definition_only is True


@pytest.fixture(scope="module")
def authoritative_hostile_helpers() -> dict:
    """Load independently stated fixture encoders without importing test symbols."""

    return runpy.run_path(str(_AUTHORITATIVE_HOSTILE_TEST))


def test_cp65_independent_source_module_is_present() -> None:
    assert _SOURCE.is_file()
    assert independent.CP65_TEST28_SCHEMA_VERSION == (
        "cp65-test28-production-schema-preimage-validator-v1"
    )


def test_cp65_independent_surface_is_path_aware_and_verify_only() -> None:
    assert independent.__all__ == (
        "CP65_TEST28_SCHEMA_VERSION",
        "CP65_TEST28_SCOPE",
        "CP65IndependentSuppliedValidationV1",
        "CP65IndependentProductionSchemaPreimageValidatorBundleV1",
        "cp65_independent_validator_bundle",
        "cp65_independently_validate_supplied_artifact_bytes",
        "cp65_independently_validate_supplied_artifact_set",
        "cp65_independently_verify_launch_authorization_signature",
        "cp65_independent_canonical_json_bytes",
        "cp65_independent_sha256",
    )
    assert tuple(
        inspect.signature(
            independent.cp65_independently_validate_supplied_artifact_bytes
        ).parameters
    ) == ("artifact_id", "relative_path", "payload")
    assert tuple(
        inspect.signature(
            independent.cp65_independently_validate_supplied_artifact_set
        ).parameters
    ) == ("items",)
    assert tuple(
        inspect.signature(
            independent.cp65_independently_verify_launch_authorization_signature
        ).parameters
    ) == ("receipt_payload", "public_key_payload")
    forbidden_tokens = (
        "execute",
        "issue",
        "keygen",
        "launch_campaign",
        "materialize",
        "run_campaign",
        "sign_authorization",
        "transition_gate",
        "write",
    )
    assert not any(
        token in name for name in independent.__all__ for token in forbidden_tokens
    )


def test_cp65_independent_source_has_no_project_or_authoritative_import() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = (
        "heterodiff",
        "numpy",
        "scipy",
        "mixed_initializer_test28_production_schema_preimage_validator",
    )
    assert not any(
        name == token or name.startswith(token + ".") or token in name
        for name in imports
        for token in forbidden
    )


def test_cp65_independent_source_generates_semantics_without_a_golden_blob() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    imported_roots = set()
    forbidden_calls = []
    literal_lengths = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            if isinstance(node.func, ast.Name) and name in {
                "__import__",
                "compile",
                "eval",
                "exec",
                "open",
            }:
                forbidden_calls.append((name, node.lineno))
            if name in {
                "b64decode",
                "b85decode",
                "decodebytes",
                "decompress",
                "load",
                "read_bytes",
                "read_text",
                "run_path",
                "unmarshal",
            }:
                forbidden_calls.append((name, node.lineno))
        elif isinstance(node, ast.Constant) and isinstance(node.value, (bytes, str)):
            literal_lengths.append(len(node.value))

    assert imported_roots.isdisjoint(
        {"base64", "bz2", "gzip", "lzma", "marshal", "pickle", "zlib"}
    )
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "hashlib",
        "hmac",
        "json",
        "math",
        "re",
        "threading",
        "typing",
        "weakref",
    }
    assert not forbidden_calls
    assert max(literal_lengths) < 16_384
    source_text = _SOURCE.read_text(encoding="utf-8")
    assert "authoritative_bundle_canonical_b85" not in source_text
    assert "authoritative_bundle_canonical_zlib" not in source_text


def test_cp65_independent_generator_reconstructs_the_full_canonical_catalog() -> None:
    authoritative_bundle = (
        authoritative.cp65_production_schema_preimage_validator_bundle()
    )
    authoritative_payload = authoritative.cp65_canonical_json_bytes(
        authoritative_bundle
    )
    independent_payload = (
        independent._independent_authoritative_bundle_canonical_bytes()
    )
    primitive = independent._independent_authoritative_bundle_primitive()

    assert len(authoritative_payload) == _AUTHORITATIVE_CANONICAL_BYTES
    assert (
        hashlib.sha256(authoritative_payload).hexdigest()
        == _AUTHORITATIVE_CANONICAL_SHA256
    )
    assert independent_payload == authoritative_payload
    assert len(independent_payload) == _AUTHORITATIVE_CANONICAL_BYTES
    assert hashlib.sha256(independent_payload).hexdigest() == (
        _AUTHORITATIVE_CANONICAL_SHA256
    )
    assert json.loads(independent_payload) == json.loads(authoritative_payload)
    primitive_payload = json.dumps(
        primitive,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    assert primitive_payload == independent_payload
    assert primitive["record_sha256"] == _AUTHORITATIVE_RECORD_SHA256
    assert primitive["schema_semantic_sha256"] == (
        _AUTHORITATIVE_SCHEMA_SEMANTIC_SHA256
    )
    assert independent._independent_schema_semantic_sha256() == (
        _AUTHORITATIVE_SCHEMA_SEMANTIC_SHA256
    )

    second = independent._independent_authoritative_bundle_primitive()
    assert second == primitive and second is not primitive
    primitive["schema_version"] = "forged"
    assert second["schema_version"] == independent.CP65_TEST28_SCHEMA_VERSION
    assert (
        independent._independent_authoritative_bundle_canonical_bytes()
        == authoritative_payload
    )


def test_cp65_independent_records_use_manual_slots_for_python39() -> None:
    for name in independent.__all__:
        value = getattr(independent, name)
        if inspect.isclass(value) and name.startswith("CP65"):
            assert "__slots__" in value.__dict__
            assert "__dict__" not in value.__dict__


def test_cp65_independent_validation_field_order_is_exact() -> None:
    assert tuple(
        field.name
        for field in __import__("dataclasses").fields(
            independent.CP65IndependentSuppliedValidationV1
        )
    ) == (
        "schema_version",
        "validation_scope",
        "caller_supplied_bytes_only",
        "input_artifact_ids",
        "input_relative_paths",
        "input_sha256s",
        "input_byte_lengths",
        "validated_artifact_ids",
        "validated_relative_paths",
        "validated_body_sha256s",
        "syntax_valid",
        "intrinsic_digest_preimages_valid",
        "all_required_digest_preimage_sources_supplied",
        "validated_digest_preimage_count",
        "unresolved_digest_preimage_count",
        "digest_preimages_valid",
        "all_required_cross_binding_targets_supplied",
        "validated_cross_binding_count",
        "unresolved_cross_binding_count",
        "cross_bindings_valid",
        "signature_verification_applicable",
        "signature_mathematically_valid_under_supplied_key",
        "parser_input_resource_limits_satisfied",
        "external_production_receipts_observed",
        "external_provenance_verified",
        "filesystem_observed",
        "source_authority_verified",
        "authorization_trust_root_bound",
        "authority_verified",
        "production_evidence_accepted",
        "gate_transition_permitted",
        "launch_authorized",
        "execution_permitted",
        "definition_only",
        "record_sha256",
    )


def test_cp65_independent_bundle_field_order_is_exact() -> None:
    assert tuple(
        field.name
        for field in __import__("dataclasses").fields(
            independent.CP65IndependentProductionSchemaPreimageValidatorBundleV1
        )
    ) == (
        "schema_version",
        "scope",
        "canonical_profile_id",
        "artifact_ids",
        "transient_path_ids",
        "field_rule_ids",
        "digest_contract_ids",
        "sha256_pointer_classification_ids",
        "predicate_ids",
        "gate_ids",
        "auxiliary_bound_ids",
        "schema_semantic_sha256",
        "sha256_pointer_contract_count",
        "sha256_pointer_contracts_cover_every_sha256_field_rule",
        "registry_required_targets_all_durable_by_gate15",
        "later_artifacts_have_no_registry_dependency",
        "all_schema_references_resolve_exactly_once",
        "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids",
        "all_referenced_rules_have_executable_validator_semantics",
        "global_path_count",
        "per_shard_path_template_count",
        "conditional_path_count",
        "expanded_final_path_count",
        "reserved_destination_partial_path_count",
        "prepared_authorization_partial_path_count",
        "auxiliary_reserved_partial_or_existing_final_slot_count",
        "auxiliary_reservation_hold_path_count",
        "ordinary_auxiliary_partial_candidate_path_count",
        "expanded_transient_path_count",
        "expanded_final_and_transient_path_count",
        "generic_writer_partial_paths_are_state_aliases",
        "expanded_final_and_transient_paths_collision_free",
        "complete_final_path_template_roster_frozen",
        "complete_production_roster_frozen",
        "gate_count",
        "evidence_present_count",
        "digest_dag_node_count",
        "digest_dag_edge_count",
        "digest_dag_node_ids",
        "digest_dag_edges",
        "digest_dag_edge_target_pointers",
        "digest_dag_edge_source_contract_ids",
        "digest_dag_edge_digest_kinds",
        "digest_dag_is_gate_evidence_only",
        "artifact_preimage_dependency_node_ids",
        "artifact_preimage_dependency_edges",
        "artifact_preimage_edge_target_pointers",
        "artifact_preimage_edge_source_contract_ids",
        "artifact_preimage_edge_digest_kinds",
        "artifact_preimage_topological_order",
        "artifact_preimage_node_count",
        "artifact_preimage_edge_count",
        "artifact_preimage_dag_acyclic",
        "artifact_preimage_dag_complete",
        "artifact_body_domain_separators_unique",
        "receipt_envelope_artifact_ids",
        "referenced_execution_output_artifact_ids",
        "frozen_or_binary_custody_artifact_ids",
        "receipt_envelope_schema_count",
        "referenced_execution_output_schema_count",
        "frozen_or_binary_custody_schema_count",
        "artifact_kind_partitions_disjoint_and_exhaustive",
        "schema_completeness_claim_scope",
        "all_required_production_receipt_keysets_predeclared",
        "complete_receipt_type_range_size_and_domain_schemas_frozen",
        "complete_auxiliary_artifact_size_schema_frozen",
        "bounded_auxiliary_artifact_size_proof_present",
        "generic_prestart_terminal_record_schema_frozen",
        "all_required_production_receipt_digest_preimages_frozen",
        "complete_production_digest_instance_validation_interface_frozen",
        "authorization_signature_preimage_and_verifier_frozen",
        "requirement_schemas_frozen",
        "artifact_occurrence_and_branch_schema_frozen",
        "production_receipt_schema_frozen",
        "production_execution_and_output_schema_frozen",
        "production_schema_frozen",
        "external_production_receipts_observed",
        "authority_verified",
        "production_evidence_accepted",
        "launch_authorized",
        "execution_permitted",
        "authoritative_module_imported",
        "project_modules_imported",
        "filesystem_path_api_exposed",
        "definition_only",
        "record_sha256",
    )


@pytest.mark.parametrize(
    "payload",
    (
        b'{"a":1,"a":2}',
        b'{"a":1.0}',
        b'{"a":NaN}',
        b'{"a":null}',
        b'{"a":"\\u00e9"}',
        b'{ "a":1}',
        b'{"b":1,"a":2}',
        b'{"a":1}\n',
        b'\xef\xbb\xbf{"a":1}',
        b'{"a":18446744073709551616}',
        (b'{"' + b"a" * 129 + b'":1}'),
        (b'{"a":' + b"[" * 17 + b"0" + b"]" * 17 + b"}"),
    ),
)
def test_cp65_independent_parser_rejects_same_hostile_json(payload: bytes) -> None:
    with pytest.raises(ValueError):
        independent._parse_canonical_json_object(payload, 67_108_864)


def test_cp65_two_pss_implementations_accept_fixed_external_vector() -> None:
    assert len(_PSS_VECTOR_MODULUS) == 384
    assert len(_PSS_VECTOR_SIGNATURE) == 384
    assert authoritative._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE, _PSS_VECTOR_MODULUS, _PSS_VECTOR_SIGNATURE
    )
    assert independent._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE, _PSS_VECTOR_MODULUS, _PSS_VECTOR_SIGNATURE
    )


@pytest.mark.parametrize("implementation", (authoritative, independent))
def test_cp65_pss_core_rejects_message_signature_and_key_mutations(
    implementation: object,
) -> None:
    mutated_signature = (
        bytes([_PSS_VECTOR_SIGNATURE[0] ^ 1]) + _PSS_VECTOR_SIGNATURE[1:]
    )
    assert not implementation._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE + b"x", _PSS_VECTOR_MODULUS, _PSS_VECTOR_SIGNATURE
    )
    assert not implementation._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE, _PSS_VECTOR_MODULUS, mutated_signature
    )
    assert not implementation._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE, _PSS_VECTOR_MODULUS[:-1], _PSS_VECTOR_SIGNATURE
    )
    even_modulus = _PSS_VECTOR_MODULUS[:-1] + bytes([_PSS_VECTOR_MODULUS[-1] & 0xFE])
    assert not implementation._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE, even_modulus, _PSS_VECTOR_SIGNATURE
    )
    assert not implementation._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE,
        _PSS_VECTOR_MODULUS,
        int.from_bytes(_PSS_VECTOR_MODULUS, "big").to_bytes(384, "big"),
    )


@pytest.mark.parametrize("implementation", (authoritative, independent))
def test_cp65_pss_core_rejects_modulus_not_coprime_to_exponent(
    implementation: object,
) -> None:
    quotient = ((1 << 3071) + 65_536) // 65_537
    if quotient % 2 == 0:
        quotient += 1
    non_coprime_modulus = (quotient * 65_537).to_bytes(384, "big")
    assert int.from_bytes(non_coprime_modulus, "big").bit_length() == 3072
    assert not implementation._verify_rsa_pss_sha256_3072(
        _PSS_VECTOR_MESSAGE, non_coprime_modulus, _PSS_VECTOR_SIGNATURE
    )


def test_cp65_independent_bundle_reconstructs_authoritative_semantics() -> None:
    authoritative_bundle = (
        authoritative.cp65_production_schema_preimage_validator_bundle()
    )
    independent_bundle = independent.cp65_independent_validator_bundle()
    assert independent_bundle.schema_version == authoritative_bundle.schema_version
    assert independent_bundle.scope == authoritative_bundle.scope
    assert (
        independent_bundle.canonical_profile_id
        == authoritative_bundle.canonical_profile_id
    )
    assert independent_bundle.artifact_ids == tuple(
        row.artifact_id for row in authoritative_bundle.artifact_schemas
    )
    assert independent_bundle.transient_path_ids == tuple(
        row.transient_path_id for row in authoritative_bundle.transient_path_contracts
    )
    assert independent_bundle.field_rule_ids == tuple(
        row.rule_id for row in authoritative_bundle.field_rules
    )
    assert independent_bundle.digest_contract_ids == tuple(
        row.contract_id for row in authoritative_bundle.digest_preimage_contracts
    )
    assert independent_bundle.sha256_pointer_classification_ids == tuple(
        row.classification_id for row in authoritative_bundle.sha256_pointer_contracts
    )
    assert independent_bundle.predicate_ids == tuple(
        row.predicate_id for row in authoritative_bundle.predicate_contracts
    )
    assert independent_bundle.gate_ids == tuple(
        row.gate_id for row in authoritative_bundle.gate_requirements
    )
    assert independent_bundle.auxiliary_bound_ids == tuple(
        row.bound_id for row in authoritative_bundle.auxiliary_artifact_bounds
    )
    assert independent_bundle.schema_semantic_sha256 == (
        authoritative_bundle.schema_semantic_sha256
    )
    assert independent_bundle.schema_semantic_sha256 == (
        _AUTHORITATIVE_SCHEMA_SEMANTIC_SHA256
    )
    for name, expected_count in _AUTHORITATIVE_CATALOG_COUNTS.items():
        identifiers = getattr(independent_bundle, name)
        assert len(identifiers) == expected_count
        assert len(set(identifiers)) == expected_count
    assert independent_bundle.artifact_preimage_node_count == 456
    assert independent_bundle.artifact_preimage_edge_count == 708
    assert len(set(independent_bundle.artifact_preimage_dependency_node_ids)) == 456
    assert len(set(independent_bundle.artifact_preimage_dependency_edges)) == 708
    assert tuple(independent_bundle.artifact_preimage_topological_order) == tuple(
        dict.fromkeys(independent_bundle.artifact_preimage_topological_order)
    )
    assert set(independent_bundle.artifact_preimage_topological_order) == set(
        independent_bundle.artifact_preimage_dependency_node_ids
    )
    exact_fields = (
        "global_path_count",
        "per_shard_path_template_count",
        "conditional_path_count",
        "expanded_final_path_count",
        "reserved_destination_partial_path_count",
        "prepared_authorization_partial_path_count",
        "auxiliary_reserved_partial_or_existing_final_slot_count",
        "auxiliary_reservation_hold_path_count",
        "ordinary_auxiliary_partial_candidate_path_count",
        "expanded_transient_path_count",
        "expanded_final_and_transient_path_count",
        "gate_count",
        "evidence_present_count",
        "digest_dag_node_count",
        "digest_dag_edge_count",
        "digest_dag_node_ids",
        "digest_dag_edges",
        "digest_dag_edge_target_pointers",
        "digest_dag_edge_source_contract_ids",
        "digest_dag_edge_digest_kinds",
        "artifact_preimage_dependency_node_ids",
        "artifact_preimage_dependency_edges",
        "artifact_preimage_edge_target_pointers",
        "artifact_preimage_edge_source_contract_ids",
        "artifact_preimage_edge_digest_kinds",
        "artifact_preimage_topological_order",
        "artifact_preimage_node_count",
        "artifact_preimage_edge_count",
        "receipt_envelope_artifact_ids",
        "referenced_execution_output_artifact_ids",
        "frozen_or_binary_custody_artifact_ids",
        "receipt_envelope_schema_count",
        "referenced_execution_output_schema_count",
        "frozen_or_binary_custody_schema_count",
        "sha256_pointer_contract_count",
        "sha256_pointer_contracts_cover_every_sha256_field_rule",
        "registry_required_targets_all_durable_by_gate15",
        "later_artifacts_have_no_registry_dependency",
    )
    for name in exact_fields:
        assert getattr(independent_bundle, name) == getattr(authoritative_bundle, name)

    true_definition_flags = (
        "all_schema_references_resolve_exactly_once",
        "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids",
        "all_referenced_rules_have_executable_validator_semantics",
        "sha256_pointer_contracts_cover_every_sha256_field_rule",
        "registry_required_targets_all_durable_by_gate15",
        "later_artifacts_have_no_registry_dependency",
        "generic_writer_partial_paths_are_state_aliases",
        "expanded_final_and_transient_paths_collision_free",
        "complete_final_path_template_roster_frozen",
        "artifact_preimage_dag_acyclic",
        "artifact_preimage_dag_complete",
        "artifact_body_domain_separators_unique",
        "artifact_kind_partitions_disjoint_and_exhaustive",
        "all_required_production_receipt_keysets_predeclared",
        "complete_receipt_type_range_size_and_domain_schemas_frozen",
        "complete_auxiliary_artifact_size_schema_frozen",
        "bounded_auxiliary_artifact_size_proof_present",
        "generic_prestart_terminal_record_schema_frozen",
        "all_required_production_receipt_digest_preimages_frozen",
        "authorization_signature_preimage_and_verifier_frozen",
        "requirement_schemas_frozen",
    )
    assert all(
        getattr(independent_bundle, name) is True for name in true_definition_flags
    )
    assert independent_bundle.schema_completeness_claim_scope == (
        "supplied-receipt-envelope-instance-canonical-fields-digests-and-pure-"
        "gate-predicates-only;excludes-lifecycle-occurrence-branch-presence-"
        "provenance-trust-evidence-and-execution-output-semantics"
    )
    assert independent_bundle.complete_production_roster_frozen is False
    assert independent_bundle.artifact_occurrence_and_branch_schema_frozen is False
    assert independent_bundle.production_receipt_schema_frozen is False
    assert independent_bundle.production_execution_and_output_schema_frozen is False
    assert independent_bundle.production_schema_frozen is False
    assert (
        independent_bundle.complete_production_digest_instance_validation_interface_frozen
        is False
    )
    assert independent_bundle.evidence_present_count == 0
    assert independent_bundle.external_production_receipts_observed is False
    assert independent_bundle.authority_verified is False
    assert independent_bundle.production_evidence_accepted is False
    assert independent_bundle.launch_authorized is False
    assert independent_bundle.execution_permitted is False
    assert independent_bundle.authoritative_module_imported is False
    assert independent_bundle.project_modules_imported is False
    assert independent_bundle.filesystem_path_api_exposed is False
    assert independent_bundle.definition_only is True

    authoritative_fields = {
        field.name
        for field in __import__("dataclasses").fields(type(authoritative_bundle))
    }
    independent_fields = {
        field.name
        for field in __import__("dataclasses").fields(type(independent_bundle))
    }
    for name in sorted((authoritative_fields & independent_fields) - {"record_sha256"}):
        assert getattr(independent_bundle, name) == getattr(authoritative_bundle, name)


def test_cp65_independent_bundle_roundtrips_and_is_issued_identity_sealed() -> None:
    bundle = independent.cp65_independent_validator_bundle()
    payload = independent.cp65_independent_canonical_json_bytes(bundle)
    parsed = independent._parse_canonical_json_object(payload, 67_108_864)
    assert 65 <= len(parsed) <= 128
    assert len(independent.cp65_independent_sha256(bundle)) == 64

    forged = object.__new__(type(bundle))
    for field in __import__("dataclasses").fields(type(bundle)):
        object.__setattr__(forged, field.name, getattr(bundle, field.name))
    with pytest.raises(TypeError):
        independent.cp65_independent_canonical_json_bytes(forged)
    with pytest.raises(TypeError):
        pickle.dumps(bundle)

    gc.collect()
    baseline = len(independent._ISSUED_RECORD_SNAPSHOTS)
    temporary = independent.cp65_independent_validator_bundle()
    reference = weakref.ref(temporary)
    assert len(independent._ISSUED_RECORD_SNAPSHOTS) == baseline + 1
    del temporary
    gc.collect()
    assert reference() is None
    assert len(independent._ISSUED_RECORD_SNAPSHOTS) == baseline


def test_cp65_independent_validates_retained_bundle_without_claiming_evidence() -> None:
    authoritative_bundle = (
        authoritative.cp65_production_schema_preimage_validator_bundle()
    )
    payload = authoritative.cp65_canonical_json_bytes(authoritative_bundle)
    result = independent.cp65_independently_validate_supplied_artifact_bytes(
        "production-schema-preimage-validator-bundle",
        "frozen_inputs/production_schema_preimage_validator_bundle.json",
        payload,
    )
    assert result.syntax_valid and result.intrinsic_digest_preimages_valid
    assert not result.all_required_digest_preimage_sources_supplied
    assert (
        result.validated_digest_preimage_count,
        result.unresolved_digest_preimage_count,
        result.validated_cross_binding_count,
        result.unresolved_cross_binding_count,
    ) == (1, 1, 0, 0)
    assert not result.digest_preimages_valid
    assert result.all_required_cross_binding_targets_supplied
    assert result.cross_bindings_valid
    assert not result.external_production_receipts_observed
    assert not result.external_provenance_verified
    assert not result.production_evidence_accepted
    assert not result.gate_transition_permitted
    assert not result.launch_authorized
    assert not result.execution_permitted

    authoritative_result = authoritative.cp65_validate_supplied_artifact_bytes(
        "production-schema-preimage-validator-bundle",
        "frozen_inputs/production_schema_preimage_validator_bundle.json",
        payload,
    )
    assert _independent_validation_semantics(result) == _validation_semantics(
        authoritative_result, authoritative
    )

    forged = payload.replace(b"zero-execution", b"xero-execution", 1)
    assert forged != payload and len(forged) == len(payload)
    with pytest.raises(ValueError):
        independent.cp65_independently_validate_supplied_artifact_bytes(
            "production-schema-preimage-validator-bundle",
            "frozen_inputs/production_schema_preimage_validator_bundle.json",
            forged,
        )


def test_cp65_independent_validates_exact_immutable_leaf_with_result_parity() -> None:
    payload = b"79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8\n"
    artifact_id = "frozen-protocol-sha256"
    relative_path = "frozen_inputs/protocol.sha256"
    authoritative_result = authoritative.cp65_validate_supplied_artifact_bytes(
        artifact_id, relative_path, payload
    )
    independent_result = (
        independent.cp65_independently_validate_supplied_artifact_bytes(
            artifact_id, relative_path, payload
        )
    )
    assert _independent_validation_semantics(
        independent_result
    ) == _validation_semantics(authoritative_result, authoritative)
    assert independent_result.validated_digest_preimage_count == 1
    assert independent_result.unresolved_digest_preimage_count == 1
    assert independent_result.unresolved_cross_binding_count == 1
    assert not independent_result.digest_preimages_valid
    assert not independent_result.cross_bindings_valid
    assert not independent_result.production_evidence_accepted

    hostile_inputs = (
        (artifact_id, relative_path, payload[:-1]),
        (artifact_id, relative_path, b"f" * 64 + b"\n"),
        (artifact_id, relative_path + ".partial", payload),
        (artifact_id, "frozen_inputs/{protocol}.sha256", payload),
    )
    for hostile_artifact_id, hostile_path, hostile_payload in hostile_inputs:
        with pytest.raises(ValueError):
            independent.cp65_independently_validate_supplied_artifact_bytes(
                hostile_artifact_id, hostile_path, hostile_payload
            )
    with pytest.raises(TypeError):
        independent.cp65_independently_validate_supplied_artifact_bytes(
            artifact_id, relative_path, bytearray(payload)
        )


def test_cp65_independent_set_is_path_aware_and_rejects_duplicate_instances() -> None:
    payload = b"79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8\n"
    item = (
        "frozen-protocol-sha256",
        "frozen_inputs/protocol.sha256",
        payload,
    )
    with pytest.raises(ValueError):
        independent.cp65_independently_validate_supplied_artifact_set((item, item))
    for wrong_path in (
        "frozen_inputs/protocol.sha256.partial",
        "frozen_inputs/{protocol}.sha256",
        "/frozen_inputs/protocol.sha256",
        "frozen_inputs/../protocol.sha256",
    ):
        with pytest.raises(ValueError):
            independent.cp65_independently_validate_supplied_artifact_set(
                ((item[0], wrong_path, item[2]),)
            )


def test_cp65_independent_registry_resolution_and_mutations_match_authoritative(
    authoritative_hostile_helpers: dict,
) -> None:
    preimage_ascii = "capacity-observation-session-001"
    measurement_digest = hashlib.sha256(preimage_ascii.encode("ascii")).hexdigest()
    capacity = authoritative_hostile_helpers["_capacity_receipt_payload"](
        measurement_digest
    )
    registry = authoritative_hostile_helpers["_external_digest_registry_payload"](
        preimage_ascii=preimage_ascii,
        target_artifact_raw_sha256=hashlib.sha256(capacity).hexdigest(),
    )
    items = (
        (
            "external-digest-preimage-registry",
            "external_digest_preimage_registry.json",
            registry,
        ),
        ("capacity-receipt", "capacity_receipt.json", capacity),
    )
    authoritative_result = authoritative.cp65_validate_supplied_artifact_set(items)
    independent_result = independent.cp65_independently_validate_supplied_artifact_set(
        items
    )
    assert _independent_validation_semantics(
        independent_result
    ) == _validation_semantics(authoritative_result, authoritative)
    assert independent_result.intrinsic_digest_preimages_valid
    assert (
        independent_result.validated_digest_preimage_count,
        independent_result.unresolved_digest_preimage_count,
        independent_result.validated_cross_binding_count,
        independent_result.unresolved_cross_binding_count,
    ) == (6, 3, 0, 4)
    assert not independent_result.digest_preimages_valid
    _assert_never_evidence_or_authority(independent_result)

    forged_registry = authoritative_hostile_helpers[
        "_external_digest_registry_payload"
    ](
        preimage_ascii=preimage_ascii,
        target_artifact_raw_sha256="f" * 64,
    )
    forged_items = ((items[0][0], items[0][1], forged_registry), items[1])
    for implementation in (authoritative, independent):
        validator = (
            implementation.cp65_validate_supplied_artifact_set
            if implementation is authoritative
            else implementation.cp65_independently_validate_supplied_artifact_set
        )
        with pytest.raises(ValueError):
            validator(forged_items)


def test_cp65_independent_cross_link_table_is_exactly_authoritative() -> None:
    tree = ast.parse(inspect.getsource(authoritative._validate_supplied_cross_bindings))
    authoritative_links = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "links"
            for target in node.targets
        ):
            authoritative_links = ast.literal_eval(node.value)
            break
    assert authoritative_links is not None
    assert len(authoritative_links) == len(set(authoritative_links)) == 43
    assert tuple(independent._I_VALIDATION_CROSS_LINKS) == tuple(authoritative_links)


def test_cp65_independent_all_selected_v15_manifest_values_resolve_and_reject_mutation() -> None:
    selected_routes = (
        (
            "capacity-receipt",
            "/capacity_schema_sha256",
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/capacity_receipt_schema/record_sha256",
        ),
        (
            "auxiliary-metadata-reservation",
            "/capacity_schema_sha256",
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/capacity_receipt_schema/record_sha256",
        ),
        (
            "reservation-manifest",
            "/capacity_schema_sha256",
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/capacity_receipt_schema/record_sha256",
        ),
        (
            "external-seed-source-receipt",
            "/cp61_stable_design_sha256",
            "/diagnostic_contracts/whole_seed_validated_mc_design/bundle/"
            "stable_design_semantic_sha256",
        ),
        (
            "seed-capsule-body",
            "/cp61_stable_design_sha256",
            "/diagnostic_contracts/whole_seed_validated_mc_design/bundle/"
            "stable_design_semantic_sha256",
        ),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/estimand_contract_sha256",
            "/diagnostic_contracts/whole_seed_validated_mc_design/bundle/"
            "stable_design_semantic_sha256",
        ),
        (
            "production-shard-map-receipt",
            "/candidate_shard_policy_sha256",
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/candidate_shard_policy/record_sha256",
        ),
        (
            "durability-receipt",
            "/layout_contract_sha256",
            "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/"
            "bundle/durability_receipt_schema/record_sha256",
        ),
        (
            "production-schedule",
            "/schedule_contract_sha256",
            "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/"
            "runner_bundle/canonical_record/fields/schedule_contract/fields/"
            "record_sha256",
        ),
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/production_schedule_contract_sha256",
            "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/"
            "runner_bundle/canonical_record/fields/schedule_contract/fields/"
            "record_sha256",
        ),
        (
            "production-runner-supervisor-qualification-receipt",
            "/supervisor_contract_sha256",
            "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/"
            "supervisor_contract/record_sha256",
        ),
        (
            "closed-refusal-failure-classifier-qualification-receipt",
            "/supervisor_contract_sha256",
            "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/"
            "supervisor_contract/record_sha256",
        ),
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/raw_record_schema_sha256",
            "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/"
            "runner_bundle/canonical_record/fields/raw_record_schema/fields/"
            "record_sha256",
        ),
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/stable_projection_schema_sha256",
            "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/"
            "stable_trace_projection/record_sha256",
        ),
        (
            "production-schedule",
            "/requests/*/runtime_lock_sha256",
            "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/"
            "runtime_source_abi_lock/record_sha256",
        ),
    )
    assert len(selected_routes) == 15

    def resolve(document: object, pointer: str) -> object:
        current = document
        for key in pointer[1:].split("/"):
            assert type(current) is dict and key in current
            current = current[key]
        return current

    manifest_payload = (
        _ROOT / "research/fixtures/cp50_test28_mixed_initializer_v15.json"
    ).read_bytes()
    assert hashlib.sha256(manifest_payload).hexdigest() == (
        "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376"
    )
    manifest = json.loads(manifest_payload)
    manifest_row = (
        "frozen_inputs/machine_manifest.json",
        manifest_payload,
        hashlib.sha256(manifest_payload).hexdigest(),
        manifest,
    )
    routes_by_artifact: dict[str, list[tuple[str, str]]] = {}
    for artifact_id, target_pointer, manifest_pointer in selected_routes:
        routes_by_artifact.setdefault(artifact_id, []).append(
            (target_pointer, manifest_pointer)
        )
    assert len(routes_by_artifact) == 12
    expected_counts = {
        "capacity-receipt": ((0, 1), (1, 0)),
        "auxiliary-metadata-reservation": ((0, 2), (1, 1)),
        "reservation-manifest": ((0, 1), (1, 0)),
        "external-seed-source-receipt": ((0, 3), (1, 2)),
        "seed-capsule-body": ((0, 1), (1, 0)),
        "independent-554-estimate-interval-decision-path-qualification-receipt": (
            (0, 2),
            (1, 1),
        ),
        "production-shard-map-receipt": ((0, 1), (1, 0)),
        "durability-receipt": ((0, 1), (1, 0)),
        "production-schedule": ((0, 2), (32_769, 0)),
        "independent-full-32768-recomputation-qualification-receipt": (
            (0, 4),
            (3, 1),
        ),
        "production-runner-supervisor-qualification-receipt": ((0, 1), (1, 0)),
        "closed-refusal-failure-classifier-qualification-receipt": (
            (0, 1),
            (1, 0),
        ),
    }
    dependency_lock_payload = (
        _ROOT / "requirements/m1-reference-macos-arm64-py311.lock"
    ).read_bytes()
    dependency_lock_raw_sha256 = hashlib.sha256(dependency_lock_payload).hexdigest()
    assert dependency_lock_raw_sha256 == (
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
    )

    for artifact_id, routes in routes_by_artifact.items():
        document = {}
        for target_pointer, manifest_pointer in routes:
            selected = resolve(manifest, manifest_pointer)
            assert type(selected) is str and len(selected) == 64
            if target_pointer == "/requests/*/runtime_lock_sha256":
                document["requests"] = [
                    {"runtime_lock_sha256": selected} for _index in range(32_768)
                ]
            else:
                document[target_pointer[1:]] = selected
        target_row = (
            artifact_id + ".json",
            ("selected-target:" + artifact_id).encode("ascii"),
            "1" * 64,
            document,
        )
        missing_manifest = {artifact_id: (target_row,)}
        with_manifest = {
            artifact_id: (target_row,),
            "frozen-machine-manifest": (manifest_row,),
        }
        for implementation in (authoritative, independent):
            assert (
                implementation._validate_supplied_cross_bindings(missing_manifest)
                == expected_counts[artifact_id][0]
            )
            assert (
                implementation._validate_supplied_cross_bindings(with_manifest)
                == expected_counts[artifact_id][1]
            )

        for target_pointer, manifest_pointer in routes:
            selected = resolve(manifest, manifest_pointer)
            if target_pointer == "/requests/*/runtime_lock_sha256":
                original = document["requests"][0]["runtime_lock_sha256"]
                assert original == selected
                document["requests"][0][
                    "runtime_lock_sha256"
                ] = dependency_lock_raw_sha256
            else:
                key = target_pointer[1:]
                original = document[key]
                assert original == selected
                document[key] = "f" * 64
            for implementation in (authoritative, independent):
                with pytest.raises(ValueError):
                    implementation._validate_supplied_cross_bindings(with_manifest)
            if target_pointer == "/requests/*/runtime_lock_sha256":
                document["requests"][0]["runtime_lock_sha256"] = original
            else:
                document[target_pointer[1:]] = original


def test_cp65_independent_freeze_crosslinks_are_nonvacuous_and_reject_mismatch() -> None:
    source_rows = {
        "frozen-protocol": (
            "frozen_inputs/protocol.md",
            b"protocol",
            "1" * 64,
            b"protocol",
        ),
        "frozen-machine-manifest": (
            "frozen_inputs/machine_manifest.json",
            b"manifest",
            "2" * 64,
            b"manifest",
        ),
        "source-manifest": (
            "frozen_inputs/bound_files.json",
            b"source-manifest",
            "3" * 64,
            b"source-manifest",
        ),
        "dependency-lock": (
            "frozen_inputs/dependency_lock.txt",
            b"dependency-lock",
            "4" * 64,
            b"dependency-lock",
        ),
    }
    pointer_by_source = {
        "frozen-protocol": "protocol_sha256",
        "frozen-machine-manifest": "machine_manifest_sha256",
        "source-manifest": "bound_files_sha256",
        "dependency-lock": "dependency_lock_sha256",
    }
    freeze = {
        "protocol_sha256": hashlib.sha256(
            source_rows["frozen-protocol"][1]
        ).hexdigest(),
        "machine_manifest_sha256": hashlib.sha256(
            source_rows["frozen-machine-manifest"][1]
        ).hexdigest(),
        "bound_files_sha256": hashlib.sha256(
            source_rows["source-manifest"][1]
        ).hexdigest(),
        "dependency_lock_sha256": hashlib.sha256(
            source_rows["dependency-lock"][1]
        ).hexdigest(),
        "frozen_source_fixture_materialization_sha256": "5" * 64,
        "production_receipt_schema_bundle_sha256": "6" * 64,
        "power_threshold_receipt_sha256": "7" * 64,
        "launch_authority_public_key_sha256": "8" * 64,
        "independent_reviewer_public_key_set_sha256": "9" * 64,
        "seed_source_authority_public_key_sha256": "a" * 64,
    }
    target = {"freeze-receipt": (("freeze_receipt.json", b"freeze", "b" * 64, freeze),)}
    assert authoritative._validate_supplied_cross_bindings(target) == (0, 10)
    assert independent._validate_supplied_cross_bindings(target) == (0, 10)

    supplied = dict(target)
    supplied.update({artifact_id: (row,) for artifact_id, row in source_rows.items()})
    assert authoritative._validate_supplied_cross_bindings(supplied) == (4, 6)
    assert independent._validate_supplied_cross_bindings(supplied) == (4, 6)
    for source_id, pointer in pointer_by_source.items():
        del source_id
        original = freeze[pointer]
        freeze[pointer] = "f" * 64
        for implementation in (authoritative, independent):
            with pytest.raises(ValueError, match="cross-artifact digest binding"):
                implementation._validate_supplied_cross_bindings(supplied)
        freeze[pointer] = original


@pytest.mark.parametrize(
    "target_id,source_id,pointer,digest_kind,target_extras",
    (
        (
            "external-seed-acquisition-start-receipt",
            "freeze-receipt",
            "freeze_receipt_sha256",
            "raw",
            {},
        ),
        (
            "external-seed-source-receipt",
            "external-seed-acquisition-start-receipt",
            "acquisition_start_receipt_sha256",
            "body",
            {},
        ),
        (
            "external-seed-source-receipt",
            "seed-source-authority-attestation",
            "source_authority_attestation_sha256",
            "raw",
            {},
        ),
        (
            "seed-capsule-body",
            "external-seed-source-receipt",
            "source_receipt_sha256",
            "raw",
            {},
        ),
        (
            "production-schedule",
            "seed-capsule-body",
            "seed_capsule_body_sha256",
            "body",
            {"requests": []},
        ),
        (
            "durability-receipt",
            "capacity-receipt",
            "capacity_receipt_sha256",
            "raw",
            {},
        ),
        (
            "production-shard-map-receipt",
            "capacity-receipt",
            "capacity_receipt_sha256",
            "raw",
            {},
        ),
        (
            "production-shard-map-receipt",
            "durability-receipt",
            "durability_receipt_sha256",
            "raw",
            {},
        ),
    ),
)
def test_cp65_independent_previously_missing_link_families_resolve_and_reject_mismatch(
    target_id: str,
    source_id: str,
    pointer: str,
    digest_kind: str,
    target_extras: dict,
) -> None:
    source_payload = ("source:" + source_id).encode("ascii")
    source_body = hashlib.sha256(b"body:" + source_payload).hexdigest()
    expected = (
        source_body
        if digest_kind == "body"
        else hashlib.sha256(source_payload).hexdigest()
    )
    target_document = dict(target_extras)
    target_document[pointer] = expected
    target_row = (
        target_id + ".json",
        ("target:" + target_id).encode("ascii"),
        "c" * 64,
        target_document,
    )
    source_row = (source_id + ".json", source_payload, source_body, b"source")
    target_only = {target_id: (target_row,)}
    supplied = {target_id: (target_row,), source_id: (source_row,)}

    authoritative_missing = authoritative._validate_supplied_cross_bindings(target_only)
    independent_missing = independent._validate_supplied_cross_bindings(target_only)
    assert independent_missing == authoritative_missing
    assert independent_missing[1] > 0
    authoritative_present = authoritative._validate_supplied_cross_bindings(supplied)
    independent_present = independent._validate_supplied_cross_bindings(supplied)
    assert independent_present == authoritative_present
    assert independent_present[0] >= 1

    target_document[pointer] = "f" * 64
    for implementation in (authoritative, independent):
        with pytest.raises(ValueError, match="cross-artifact digest binding"):
            implementation._validate_supplied_cross_bindings(supplied)


def test_cp65_independent_acquisition_start_has_one_unresolved_freeze_binding(
    authoritative_hostile_helpers: dict,
) -> None:
    payload = authoritative_hostile_helpers["_acquisition_start_payload"]()
    authoritative_result = authoritative.cp65_validate_supplied_artifact_bytes(
        "external-seed-acquisition-start-receipt",
        "seed_acquisition_start_receipt.json",
        payload,
    )
    independent_result = (
        independent.cp65_independently_validate_supplied_artifact_bytes(
            "external-seed-acquisition-start-receipt",
            "seed_acquisition_start_receipt.json",
            payload,
        )
    )
    assert _independent_validation_semantics(
        independent_result
    ) == _validation_semantics(authoritative_result, authoritative)
    assert (
        independent_result.validated_digest_preimage_count,
        independent_result.unresolved_digest_preimage_count,
        independent_result.validated_cross_binding_count,
        independent_result.unresolved_cross_binding_count,
    ) == (1, 1, 0, 1)
    assert not independent_result.cross_bindings_valid
    _assert_never_evidence_or_authority(independent_result)


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong-ordinal",
        "wrong-previous-head",
        "wrong-entry-digest",
        "claimed-value-differs",
        "claimed-head-differs",
        "claimed-count-differs",
        "claimed-raw-digest-differs",
    ),
)
def test_cp65_independent_cp64_journal_rejects_forged_claimed_prefix(
    authoritative_hostile_helpers: dict,
    mutation: str,
) -> None:
    start_payload = authoritative_hostile_helpers["_acquisition_start_payload"]()
    start_body = json.loads(start_payload)["body_sha256"]
    values = (7, 11)
    journal, head = authoritative_hostile_helpers["_journal_with_values"](
        start_body, values
    )
    claimed_values = values
    claimed_head = head
    claimed_journal = journal
    if mutation == "wrong-ordinal":
        changed = bytearray(journal)
        changed[7] = 2
        claimed_journal = bytes(changed)
    elif mutation == "wrong-previous-head":
        changed = bytearray(journal)
        changed[16] ^= 1
        claimed_journal = bytes(changed)
    elif mutation == "wrong-entry-digest":
        changed = bytearray(journal)
        changed[48] ^= 1
        claimed_journal = bytes(changed)
    elif mutation == "claimed-value-differs":
        claimed_values = (8, 11)
    elif mutation == "claimed-head-differs":
        claimed_head = "f" * 64
    elif mutation == "claimed-count-differs":
        claimed_values = (7,)
    elif mutation != "claimed-raw-digest-differs":  # pragma: no cover
        raise AssertionError(mutation)
    partial_payload = authoritative_hostile_helpers["_partial_acquisition_payload"](
        start_body, claimed_journal, claimed_head, claimed_values
    )
    if mutation == "claimed-raw-digest-differs":
        document = json.loads(partial_payload)
        document["acquisition_journal_sha256"] = "f" * 64
        partial_payload = authoritative_hostile_helpers["_receipt_payload"](
            "partial-seed-acquisition-terminal-receipt", document
        )
    items = (
        (
            "external-seed-acquisition-start-receipt",
            "seed_acquisition_start_receipt.json",
            start_payload,
        ),
        (
            "external-seed-acquisition-journal",
            "seed_acquisition_journal.bin",
            claimed_journal,
        ),
        (
            "partial-seed-acquisition-terminal-receipt",
            "seed_partial_acquisition_terminal_receipt.json",
            partial_payload,
        ),
    )
    for validator in (
        authoritative.cp65_validate_supplied_artifact_set,
        independent.cp65_independently_validate_supplied_artifact_set,
    ):
        with pytest.raises(ValueError):
            validator(items)


def test_cp65_independent_cp64_journal_positive_torn_and_completed_arms_match(
    authoritative_hostile_helpers: dict,
) -> None:
    start_payload = authoritative_hostile_helpers["_acquisition_start_payload"]()
    start_body = json.loads(start_payload)["body_sha256"]
    journal, head = authoritative_hostile_helpers["_journal_with_values"](
        start_body, (19,)
    )
    partial_payload = authoritative_hostile_helpers["_partial_acquisition_payload"](
        start_body, journal, head, (19,)
    )
    partial_items = (
        (
            "external-seed-acquisition-start-receipt",
            "seed_acquisition_start_receipt.json",
            start_payload,
        ),
        (
            "external-seed-acquisition-journal",
            "seed_acquisition_journal.bin",
            journal,
        ),
        (
            "partial-seed-acquisition-terminal-receipt",
            "seed_partial_acquisition_terminal_receipt.json",
            partial_payload,
        ),
    )
    authoritative_partial = authoritative.cp65_validate_supplied_artifact_set(
        partial_items
    )
    independent_partial = independent.cp65_independently_validate_supplied_artifact_set(
        partial_items
    )
    assert _independent_validation_semantics(
        independent_partial
    ) == _validation_semantics(authoritative_partial, authoritative)
    assert (
        independent_partial.validated_digest_preimage_count,
        independent_partial.unresolved_digest_preimage_count,
        independent_partial.validated_cross_binding_count,
        independent_partial.unresolved_cross_binding_count,
    ) == (3, 3, 5, 1)

    torn = bytearray(journal)
    torn[80] = 1
    torn_journal = bytes(torn)
    torn_partial = authoritative_hostile_helpers["_partial_acquisition_payload"](
        start_body, torn_journal, head, (19,)
    )
    torn_items = (
        partial_items[0],
        (partial_items[1][0], partial_items[1][1], torn_journal),
        (partial_items[2][0], partial_items[2][1], torn_partial),
    )
    authoritative_torn = authoritative.cp65_validate_supplied_artifact_set(torn_items)
    independent_torn = independent.cp65_independently_validate_supplied_artifact_set(
        torn_items
    )
    assert _independent_validation_semantics(independent_torn) == _validation_semantics(
        authoritative_torn, authoritative
    )
    forged_two = authoritative_hostile_helpers["_partial_acquisition_payload"](
        start_body, torn_journal, "e" * 64, (19, 23)
    )
    forged_torn_items = (
        torn_items[0],
        torn_items[1],
        (torn_items[2][0], torn_items[2][1], forged_two),
    )
    for validator in (
        authoritative.cp65_validate_supplied_artifact_set,
        independent.cp65_independently_validate_supplied_artifact_set,
    ):
        with pytest.raises(ValueError):
            validator(forged_torn_items)

    completed_values = tuple(range(2_048))
    completed_journal, completed_head = authoritative_hostile_helpers[
        "_journal_with_values"
    ](start_body, completed_values)
    completed_payload = authoritative_hostile_helpers[
        "_completed_source_receipt_payload"
    ](start_body, completed_journal, completed_head, completed_values)
    completed_items = (
        partial_items[0],
        (partial_items[1][0], partial_items[1][1], completed_journal),
        (
            "external-seed-source-receipt",
            "seed_source_receipt.json",
            completed_payload,
        ),
    )
    authoritative_completed = authoritative.cp65_validate_supplied_artifact_set(
        completed_items
    )
    independent_completed = (
        independent.cp65_independently_validate_supplied_artifact_set(completed_items)
    )
    assert _independent_validation_semantics(
        independent_completed
    ) == _validation_semantics(authoritative_completed, authoritative)
    assert (
        independent_completed.validated_digest_preimage_count,
        independent_completed.unresolved_digest_preimage_count,
        independent_completed.validated_cross_binding_count,
        independent_completed.unresolved_cross_binding_count,
    ) == (3, 3, 6, 3)

    completed_partial = authoritative_hostile_helpers["_partial_acquisition_payload"](
        start_body, completed_journal, completed_head, completed_values
    )
    mutually_exclusive = completed_items + (
        (
            "partial-seed-acquisition-terminal-receipt",
            "seed_partial_acquisition_terminal_receipt.json",
            completed_partial,
        ),
    )
    for validator in (
        authoritative.cp65_validate_supplied_artifact_set,
        independent.cp65_independently_validate_supplied_artifact_set,
    ):
        with pytest.raises(ValueError, match="cannot coexist"):
            validator(mutually_exclusive)


@pytest.mark.parametrize(
    "terminal_arm,conditional_sources,expected_count",
    (
        ("PREAUTHORIZATION", (), 3),
        (
            "POSTAUTHORIZATION_PRESTART",
            ("launch-authorization", "postauthorization-outcome"),
            5,
        ),
        (
            "STARTED",
            (
                "launch-authorization",
                "postauthorization-outcome",
                "started-receipt",
            ),
            6,
        ),
    ),
)
def test_cp65_independent_terminal_arm_links_are_conditional_raw_bindings(
    terminal_arm: str,
    conditional_sources: tuple[str, ...],
    expected_count: int,
) -> None:
    always_sources = (
        "freeze-receipt",
        "preauthorization-outcome",
        "preterminal-durable-artifact-inventory",
    )
    payloads = {
        artifact_id: ("cp65-terminal-source:" + artifact_id).encode("ascii")
        for artifact_id in always_sources + conditional_sources
    }
    pointer_by_source = {
        "freeze-receipt": "freeze_receipt_sha256",
        "preauthorization-outcome": "preauthorization_outcome_sha256",
        "preterminal-durable-artifact-inventory": ("durable_artifact_inventory_sha256"),
        "launch-authorization": "launch_authorization_sha256",
        "postauthorization-outcome": "postauthorization_outcome_sha256",
        "started-receipt": "started_receipt_sha256",
    }
    terminal = {
        "terminal_arm": terminal_arm,
        "freeze_receipt_sha256": hashlib.sha256(payloads["freeze-receipt"]).hexdigest(),
        "preauthorization_outcome_sha256": hashlib.sha256(
            payloads["preauthorization-outcome"]
        ).hexdigest(),
        "durable_artifact_inventory_sha256": hashlib.sha256(
            payloads["preterminal-durable-artifact-inventory"]
        ).hexdigest(),
        "launch_authorization_sha256": "0" * 64,
        "postauthorization_outcome_sha256": "0" * 64,
        "started_receipt_sha256": "0" * 64,
        "auxiliary_transition_journal_after_inventory_head_sha256": "1" * 64,
    }
    for source_id in conditional_sources:
        terminal[pointer_by_source[source_id]] = hashlib.sha256(
            payloads[source_id]
        ).hexdigest()
    target_only = {
        "terminal-state": (("terminal_state.json", b"terminal", "1" * 64, terminal),)
    }
    for implementation in (authoritative, independent):
        assert implementation._validate_supplied_cross_bindings(target_only) == (
            0,
            expected_count + 1,
        )

    supplied = dict(target_only)
    for source_id, payload in payloads.items():
        supplied[source_id] = (
            (
                source_id + ".json",
                payload,
                hashlib.sha256(payload).hexdigest(),
                payload,
            ),
        )
    for implementation in (authoritative, independent):
        assert implementation._validate_supplied_cross_bindings(supplied) == (
            expected_count,
            1,
        )
    for source_id in always_sources + conditional_sources:
        pointer = pointer_by_source[source_id]
        original = terminal[pointer]
        terminal[pointer] = "f" * 64
        for implementation in (authoritative, independent):
            with pytest.raises(ValueError):
                implementation._validate_supplied_cross_bindings(supplied)
        terminal[pointer] = original


def test_cp65_independent_preauthorization_candidate_alias_has_two_exact_arms() -> None:
    launch_payload = b"prepared launch candidate"
    rejected_payload = launch_payload
    prepared_sha256 = hashlib.sha256(launch_payload).hexdigest()
    launch_row = (
        "launch_authorization.json",
        launch_payload,
        "1" * 64,
        b"launch",
    )
    rejected_row = (
        "rejected_launch_authorization_candidate.json",
        rejected_payload,
        "1" * 64,
        b"rejected",
    )

    authorization = {
        "preauthorization-outcome": (
            (
                "preauthorization_outcome.json",
                b"authorization outcome",
                "2" * 64,
                {
                    "outcome_arm": "AUTHORIZATION",
                    "prepared_launch_authorization_sha256": prepared_sha256,
                },
            ),
        ),
        "launch-authorization": (launch_row,),
    }
    for implementation in (authoritative, independent):
        assert implementation._validate_supplied_cross_bindings(authorization) == (
            0,
            0,
        )
    authorization["preauthorization-outcome"][0][3][
        "prepared_launch_authorization_sha256"
    ] = ("f" * 64)
    for implementation in (authoritative, independent):
        with pytest.raises(ValueError, match="published identical bytes"):
            implementation._validate_supplied_cross_bindings(authorization)
    authorization["preauthorization-outcome"][0][3][
        "prepared_launch_authorization_sha256"
    ] = prepared_sha256
    authorization["rejected-launch-authorization-candidate"] = (rejected_row,)
    for implementation in (authoritative, independent):
        with pytest.raises(ValueError, match="cannot retain rejected candidate"):
            implementation._validate_supplied_cross_bindings(authorization)

    terminal_without_candidate = {
        "preauthorization-outcome": (
            (
                "preauthorization_outcome.json",
                b"terminal outcome",
                "3" * 64,
                {
                    "outcome_arm": "INCOMPLETE",
                    "prepared_launch_authorization_sha256": "0" * 64,
                },
            ),
        )
    }
    terminal_with_candidate = {
        "preauthorization-outcome": (
            (
                "preauthorization_outcome.json",
                b"terminal outcome",
                "3" * 64,
                {
                    "outcome_arm": "INCOMPLETE",
                    "prepared_launch_authorization_sha256": prepared_sha256,
                },
            ),
        ),
        "rejected-launch-authorization-candidate": (rejected_row,),
    }
    for implementation in (authoritative, independent):
        assert implementation._validate_supplied_cross_bindings(
            terminal_without_candidate
        ) == (0, 0)
        assert implementation._validate_supplied_cross_bindings(
            terminal_with_candidate
        ) == (0, 0)
    del terminal_with_candidate["rejected-launch-authorization-candidate"]
    for implementation in (authoritative, independent):
        with pytest.raises(ValueError, match="candidate is not retained"):
            implementation._validate_supplied_cross_bindings(terminal_with_candidate)


def test_cp65_independent_schedule_seed_ordinal_crosscheck_is_not_just_a_digest_link() -> None:
    seed_value = "0000000000000007"
    capsule_payload = b"capsule"
    capsule_body = hashlib.sha256(b"capsule body").hexdigest()
    capsule = {
        "ordered_seed_values": [seed_value],
    }
    schedule = {
        "seed_capsule_body_sha256": capsule_body,
        "requests": [{"seed_ordinal": 1, "plan_seed_hex": seed_value}],
    }
    supplied = {
        "seed-capsule-body": (
            ("seed_capsule.json", capsule_payload, capsule_body, capsule),
        ),
        "production-schedule": (
            ("production_schedule.json", b"schedule", "4" * 64, schedule),
        ),
    }
    for implementation in (authoritative, independent):
        assert implementation._validate_supplied_cross_bindings(supplied) == (2, 3)
    schedule["requests"][0]["plan_seed_hex"] = "0000000000000008"
    for implementation in (authoritative, independent):
        with pytest.raises(ValueError, match="plan seed differs"):
            implementation._validate_supplied_cross_bindings(supplied)


@pytest.mark.parametrize(
    "builder_name,artifact_id,relative_path,key_artifact_id,key_relative_path,"
    "expected_unresolved_cross_bindings",
    (
        (
            "_launch_authorization_pair",
            "launch-authorization",
            "launch_authorization.json",
            "launch-authority-public-key",
            "frozen_inputs/launch_authority_public_key.json",
            15,
        ),
        (
            "_seed_source_attestation_pair",
            "seed-source-authority-attestation",
            "seed_source_authority_attestation.json",
            "seed-source-authority-public-key",
            "frozen_inputs/seed_source_authority_public_key.json",
            2,
        ),
        (
            "_power_review_signoff_pair",
            "power-review-signoff",
            "power_review_signoff.json",
            "independent-reviewer-public-key-set",
            "frozen_inputs/independent_reviewer_public_keys.json",
            1,
        ),
    ),
)
def test_cp65_independent_signed_family_set_validation_matches_authoritative(
    authoritative_hostile_helpers: dict,
    builder_name: str,
    artifact_id: str,
    relative_path: str,
    key_artifact_id: str,
    key_relative_path: str,
    expected_unresolved_cross_bindings: int,
) -> None:
    builder = authoritative_hostile_helpers[builder_name]
    signed_payload, key_payload = builder()
    items = (
        (artifact_id, relative_path, signed_payload),
        (key_artifact_id, key_relative_path, key_payload),
    )
    authoritative_result = authoritative.cp65_validate_supplied_artifact_set(items)
    independent_result = independent.cp65_independently_validate_supplied_artifact_set(
        items
    )
    assert _independent_validation_semantics(
        independent_result
    ) == _validation_semantics(authoritative_result, authoritative)
    assert independent_result.signature_verification_applicable
    assert independent_result.signature_mathematically_valid_under_supplied_key
    assert (
        independent_result.validated_digest_preimage_count,
        independent_result.unresolved_digest_preimage_count,
        independent_result.validated_cross_binding_count,
        independent_result.unresolved_cross_binding_count,
    ) == (2, 2, 1, expected_unresolved_cross_bindings)
    _assert_never_evidence_or_authority(independent_result)

    authoritative_missing_key = authoritative.cp65_validate_supplied_artifact_set(
        (items[0],)
    )
    independent_missing_key = (
        independent.cp65_independently_validate_supplied_artifact_set((items[0],))
    )
    assert _independent_validation_semantics(
        independent_missing_key
    ) == _validation_semantics(authoritative_missing_key, authoritative)
    assert independent_missing_key.signature_verification_applicable
    assert not (
        independent_missing_key.signature_mathematically_valid_under_supplied_key
    )
    assert independent_missing_key.unresolved_cross_binding_count > 0
    _assert_never_evidence_or_authority(independent_missing_key)
    if artifact_id == "launch-authorization":
        independent_direct = (
            independent.cp65_independently_verify_launch_authorization_signature(
                signed_payload, key_payload
            )
        )
        authoritative_direct = authoritative.cp65_verify_launch_authorization_signature(
            signed_payload, key_payload
        )
        assert _independent_validation_semantics(
            independent_direct
        ) == _validation_semantics(authoritative_direct, authoritative)
        assert independent_direct.signature_mathematically_valid_under_supplied_key
        _assert_never_evidence_or_authority(independent_direct)

    corrupted_payload, corrupted_key = builder(corrupt_signature=True)
    corrupted_items = (
        (artifact_id, relative_path, corrupted_payload),
        (key_artifact_id, key_relative_path, corrupted_key),
    )
    independent_corrupted = (
        independent.cp65_independently_validate_supplied_artifact_set(corrupted_items)
    )
    authoritative_corrupted = authoritative.cp65_validate_supplied_artifact_set(
        corrupted_items
    )
    assert _independent_validation_semantics(
        independent_corrupted
    ) == _validation_semantics(authoritative_corrupted, authoritative)
    assert independent_corrupted.signature_verification_applicable
    assert not independent_corrupted.signature_mathematically_valid_under_supplied_key
    _assert_never_evidence_or_authority(independent_corrupted)


def test_cp65_independent_four_role_signoff_aggregation_matches_authoritative(
    authoritative_hostile_helpers: dict,
) -> None:
    summary = authoritative_hostile_helpers["_preflight_summary_payload"]()
    key_set, key_rows = authoritative_hostile_helpers["_reviewer_key_set_payload"]()
    signoff = authoritative_hostile_helpers["_independent_signoff_set_payload"](
        summary, key_set, key_rows
    )
    items = (
        ("preflight-gate-summary", "preflight_gate_summary.json", summary),
        (
            "independent-reviewer-public-key-set",
            "frozen_inputs/independent_reviewer_public_keys.json",
            key_set,
        ),
        ("independent-signoff-set", "independent_signoff.json", signoff),
    )
    authoritative_result = authoritative.cp65_validate_supplied_artifact_set(items)
    independent_result = independent.cp65_independently_validate_supplied_artifact_set(
        items
    )
    assert _independent_validation_semantics(
        independent_result
    ) == _validation_semantics(authoritative_result, authoritative)
    assert independent_result.signature_verification_applicable
    assert independent_result.signature_mathematically_valid_under_supplied_key
    assert (
        independent_result.validated_digest_preimage_count,
        independent_result.unresolved_digest_preimage_count,
        independent_result.validated_cross_binding_count,
        independent_result.unresolved_cross_binding_count,
    ) == (3, 19, 14, 2)
    _assert_never_evidence_or_authority(independent_result)

    signoff_only = (("independent-signoff-set", "independent_signoff.json", signoff),)
    authoritative_missing_keys = authoritative.cp65_validate_supplied_artifact_set(
        signoff_only
    )
    independent_missing_keys = (
        independent.cp65_independently_validate_supplied_artifact_set(signoff_only)
    )
    assert _independent_validation_semantics(
        independent_missing_keys
    ) == _validation_semantics(authoritative_missing_keys, authoritative)
    assert independent_missing_keys.signature_verification_applicable
    assert not (
        independent_missing_keys.signature_mathematically_valid_under_supplied_key
    )
    assert independent_missing_keys.unresolved_cross_binding_count > 0
    _assert_never_evidence_or_authority(independent_missing_keys)

    for mutation in (
        {"duplicate_role": True},
        {"empty_reviewed": True},
        {"false_derived_booleans": True},
        {"corrupt_signature": True},
    ):
        forged = authoritative_hostile_helpers["_independent_signoff_set_payload"](
            summary, key_set, key_rows, **mutation
        )
        forged_items = items[:-1] + (
            ("independent-signoff-set", "independent_signoff.json", forged),
        )
        with pytest.raises(ValueError):
            independent.cp65_independently_validate_supplied_artifact_set(forged_items)


def test_cp65_independent_aux_journal_terminal_chain_and_mutations_match(
    authoritative_hostile_helpers: dict,
) -> None:
    items, payloads = authoritative_hostile_helpers[
        "_complete_auxiliary_terminal_publication_items"
    ]()
    authoritative_result = authoritative.cp65_validate_supplied_artifact_set(items)
    independent_result = independent.cp65_independently_validate_supplied_artifact_set(
        items
    )
    assert _independent_validation_semantics(
        independent_result
    ) == _validation_semantics(authoritative_result, authoritative)
    assert independent_result.intrinsic_digest_preimages_valid
    assert (
        independent_result.validated_digest_preimage_count,
        independent_result.unresolved_digest_preimage_count,
        independent_result.validated_cross_binding_count,
        independent_result.unresolved_cross_binding_count,
    ) == (11, 17, 29, 6)
    _assert_never_evidence_or_authority(independent_result)

    corrupted_journal = bytearray(payloads["auxiliary-reservation-transition-journal"])
    corrupted_journal[512] ^= 1
    corrupted_items = tuple(
        (
            artifact_id,
            relative_path,
            bytes(corrupted_journal)
            if artifact_id == "auxiliary-reservation-transition-journal"
            else payload,
        )
        for artifact_id, relative_path, payload in items
    )
    with pytest.raises(ValueError):
        independent.cp65_independently_validate_supplied_artifact_set(corrupted_items)

    committed = json.loads(payloads["committed-marker"])
    committed["auxiliary_reservation_transition_journal_final_head_sha256"] = "f" * 64
    forged_committed = authoritative_hostile_helpers["_receipt_payload"](
        "committed-marker", committed
    )
    forged_items = tuple(
        (
            artifact_id,
            relative_path,
            forged_committed if artifact_id == "committed-marker" else payload,
        )
        for artifact_id, relative_path, payload in items
    )
    with pytest.raises(ValueError):
        independent.cp65_independently_validate_supplied_artifact_set(forged_items)


def test_cp65_independent_auxiliary_rows_cannot_be_renumbered_and_rehashed(
    authoritative_hostile_helpers: dict,
) -> None:
    document = authoritative_hostile_helpers["_auxiliary_reservation_document"]()
    row = document["artifact_entries"][0]
    row["ordinal"] = 2
    row["entry_sha256"] = "0" * 64
    row["entry_sha256"] = hashlib.sha256(
        b"cp65-test28-auxiliary-metadata-reservation-entry-v3\0"
        + json.dumps(
            row,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    forged = authoritative_hostile_helpers["_receipt_payload"](
        "auxiliary-metadata-reservation", document
    )
    for implementation in (authoritative, independent):
        validator = (
            implementation.cp65_validate_supplied_artifact_bytes
            if implementation is authoritative
            else implementation.cp65_independently_validate_supplied_artifact_bytes
        )
        with pytest.raises(ValueError):
            validator(
                "auxiliary-metadata-reservation",
                "auxiliary_metadata_reservation.json",
                forged,
            )


def test_cp65_independent_source_archive_manifest_parity_and_line_mutations(
    authoritative_hostile_helpers: dict,
) -> None:
    entries = (
        ("src/example.py", b"x = 1\n"),
        ("tests/empty.bin", b""),
        ("tests/fixture.json", b"{}\n"),
        ("tests/no_final_lf.txt", b"first\nsecond"),
    )
    archive = authoritative_hostile_helpers["_source_materialization"](entries)
    rows = [
        {
            "ordinal": ordinal,
            "role": (
                "production-runner-source"
                if path.startswith("src/")
                else "independent-recomputation-source"
            ),
            "relative_path": path,
            "bytes": len(content),
            "lines": (
                0
                if not content
                else content.count(b"\n") + int(not content.endswith(b"\n"))
            ),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for ordinal, (path, content) in enumerate(entries, 1)
    ]
    manifest = {
        "schema": "cp65-test28-source-manifest-v1",
        "purpose": "frozen-source-fixture-materialization-custody",
        "attempt_id": "attempt-development-only",
        "protocol_sha256": "1" * 64,
        "machine_manifest_sha256": "2" * 64,
        "entry_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "entries": rows,
        "ordered_entries_sha256": hashlib.sha256(
            b"cp65-test28-source-manifest-ordered-entries-v1\0"
            + json.dumps(
                rows,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        ).hexdigest(),
        "body_sha256": "0" * 64,
    }
    manifest_payload = authoritative_hostile_helpers["_receipt_payload"](
        "source-manifest", manifest
    )
    items = (
        (
            "frozen-source-fixture-materialization",
            "frozen_inputs/source_fixture_materialization.bin",
            archive,
        ),
        ("source-manifest", "frozen_inputs/bound_files.json", manifest_payload),
    )
    authoritative_result = authoritative.cp65_validate_supplied_artifact_set(items)
    independent_result = independent.cp65_independently_validate_supplied_artifact_set(
        items
    )
    assert _independent_validation_semantics(
        independent_result
    ) == _validation_semantics(authoritative_result, authoritative)
    assert independent_result.intrinsic_digest_preimages_valid
    assert (
        independent_result.validated_digest_preimage_count,
        independent_result.unresolved_digest_preimage_count,
        independent_result.validated_cross_binding_count,
        independent_result.unresolved_cross_binding_count,
    ) == (2, 2, 4, 0)
    assert not independent_result.digest_preimages_valid
    _assert_never_evidence_or_authority(independent_result)

    for row_index, changed_lines in ((0, 2), (1, 1), (2, 2), (3, 1)):
        forged = dict(manifest)
        forged_rows = [dict(row) for row in rows]
        forged_rows[row_index]["lines"] = changed_lines
        forged["entries"] = forged_rows
        forged["ordered_entries_sha256"] = hashlib.sha256(
            b"cp65-test28-source-manifest-ordered-entries-v1\0"
            + json.dumps(
                forged_rows,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        ).hexdigest()
        forged_payload = authoritative_hostile_helpers["_receipt_payload"](
            "source-manifest", forged
        )
        with pytest.raises(ValueError):
            independent.cp65_independently_validate_supplied_artifact_set(
                (items[0], (items[1][0], items[1][1], forged_payload))
            )


def test_cp65_independent_parser_member_cap_is_exactly_128() -> None:
    accepted = json.dumps(
        {"k%03d" % ordinal: ordinal for ordinal in range(128)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    rejected = json.dumps(
        {"k%03d" % ordinal: ordinal for ordinal in range(129)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    assert len(independent._parse_canonical_json_object(accepted, 67_108_864)) == 128
    with pytest.raises(ValueError):
        independent._parse_canonical_json_object(rejected, 67_108_864)


def test_cp65_independent_resource_caps_and_memory_failures_are_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert independent._MAX_SUPPLIED_ARTIFACT_SET_ITEMS == 312
    assert independent._MAX_SUPPLIED_ARTIFACT_SET_BYTES == 536_870_912
    assert independent._MAX_SUPPLIED_ARTIFACT_SET_NODES == 1_048_576
    assert (
        independent._MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS == 268_435_456
    )

    cases = (
        (
            "_validate_supplied_artifact_bytes_impl",
            independent.cp65_independently_validate_supplied_artifact_bytes,
            ("frozen-protocol", "frozen_inputs/protocol.md", b"x"),
        ),
        (
            "_validate_supplied_artifact_set_impl",
            independent.cp65_independently_validate_supplied_artifact_set,
            ((),),
        ),
        (
            "_verify_launch_authorization_signature_impl",
            independent.cp65_independently_verify_launch_authorization_signature,
            (b"{}", b"{}"),
        ),
    )
    for private_name, public_api, arguments in cases:
        with monkeypatch.context() as context:
            context.setattr(
                independent,
                private_name,
                lambda *args, **kwargs: (_ for _ in ()).throw(MemoryError()),
            )
            with pytest.raises(ValueError):
                public_api(*arguments)


@pytest.mark.parametrize("resource_kind", ("nodes", "decoded-characters"))
def test_cp65_independent_set_resource_caps_are_incremental_at_cap_plus_one(
    monkeypatch: pytest.MonkeyPatch,
    resource_kind: str,
) -> None:
    # Each document contributes exactly 1/256 of one aggregate resource cap.
    document = (
        {"v": [0] * 4_094} if resource_kind == "nodes" else {"k": "x" * 1_048_575}
    )
    expected_counts = independent._validate_json_resources(document)
    assert expected_counts == (
        (4_096, 1) if resource_kind == "nodes" else (2, 1_048_576)
    )
    items = tuple(
        ("synthetic-%03d" % index, "synthetic/%03d.json" % index, b"{}")
        for index in range(258)
    )
    artifact_table = {
        artifact_id: (artifact_id, relative_path, "global")
        for artifact_id, relative_path, _payload in items
    }
    parsed_count = 0

    def validate_payload(
        artifact_id: str, relative_path: str, payload: bytes
    ) -> tuple[str, object]:
        del artifact_id, relative_path, payload
        nonlocal parsed_count
        parsed_count += 1
        return "a" * 64, document

    monkeypatch.setattr(independent, "_I_ARTIFACT_BY_ID", artifact_table)
    monkeypatch.setattr(independent, "_validate_artifact_payload", validate_payload)
    monkeypatch.setattr(
        independent, "_validate_supplied_cross_bindings", lambda _by_id: (0, 0)
    )
    monkeypatch.setattr(
        independent,
        "_validate_supplied_signature_aggregation",
        lambda _by_id: (False, False, 0, 0),
    )
    monkeypatch.setattr(
        independent, "_intrinsic_digest_instance_counts", lambda _id, _doc: (0, 0)
    )

    accepted = independent.cp65_independently_validate_supplied_artifact_set(
        items[:256]
    )
    assert accepted.parser_input_resource_limits_satisfied
    assert parsed_count == 256

    parsed_count = 0
    with pytest.raises(ValueError):
        independent.cp65_independently_validate_supplied_artifact_set(items)
    # The 257th parsed document is cap+1.  The 258th must never be parsed or
    # retained after the aggregate limit is already known to be violated.
    assert parsed_count == 257


def test_cp65_independent_incremental_resource_memory_error_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    items = tuple(
        ("synthetic-%d" % index, "synthetic/%d.json" % index, b"{}")
        for index in range(3)
    )
    monkeypatch.setattr(
        independent,
        "_I_ARTIFACT_BY_ID",
        {
            artifact_id: (artifact_id, relative_path, "global")
            for artifact_id, relative_path, _payload in items
        },
    )
    parsed_count = 0
    resource_count = 0

    def validate_payload(
        artifact_id: str, relative_path: str, payload: bytes
    ) -> tuple[str, object]:
        del artifact_id, relative_path, payload
        nonlocal parsed_count
        parsed_count += 1
        return "a" * 64, {"value": parsed_count}

    def fail_on_second_document(_document: object) -> tuple[int, int]:
        nonlocal resource_count
        resource_count += 1
        if resource_count == 2:
            raise MemoryError
        return 2, 5

    monkeypatch.setattr(independent, "_validate_artifact_payload", validate_payload)
    monkeypatch.setattr(
        independent, "_validate_json_resources", fail_on_second_document
    )
    with pytest.raises(ValueError):
        independent.cp65_independently_validate_supplied_artifact_set(items)
    assert parsed_count == resource_count == 2
