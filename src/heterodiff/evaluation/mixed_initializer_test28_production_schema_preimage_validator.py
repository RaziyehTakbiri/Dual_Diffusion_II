"""CP65 zero-execution production receipt-schema and preimage catalog.

The module is deliberately standard-library-only.  It accepts caller-supplied
bytes for bounded syntax and digest validation, but it never reads a path,
observes a host, verifies an authority trust root, authorizes a launch, or
executes a production request.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
import math
import hashlib
import hmac
import json
import re
import threading
from typing import Mapping, Tuple, cast
import weakref


CP65_TEST28_SCHEMA_VERSION = "cp65-test28-production-schema-preimage-validator-v1"
CP65_TEST28_SCOPE = (
    "zero-execution-production-schema-preimage-and-syntax-validation-only;"
    "no-external-receipts;no-seeds;no-host-probes;no-filesystem-write;"
    "no-trust-root;no-authority-verification;no-gate-evidence;no-authorization;"
    "no-launch;no-execution;no-blocker-closure"
)

_ZERO_SHA256 = "0" * 64
_CANONICAL_PROFILE_ID = "cp65-ascii-canonical-json-v1"
_MAX_SUPPLIED_ARTIFACT_SET_ITEMS = 312
_MAX_SUPPLIED_ARTIFACT_SET_BYTES = 536_870_912
_MAX_SUPPLIED_ARTIFACT_SET_NODES = 1_048_576
_MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS = 268_435_456
_MAX_SOURCE_MANIFEST_ENTRIES = 4_096
_MAX_TERMINAL_PUBLICATION_ENTRIES = 312
_PINNED_PREDECESSOR_MANIFEST_MAX_NODES = 37_036
_PINNED_PREDECESSOR_MANIFEST_MAX_DECODED_STRING_CHARACTERS = 1_280_910
_PINNED_PREDECESSOR_MANIFEST_MAX_OBJECT_MEMBERS = 111
_PINNED_PREDECESSOR_MANIFEST_MAX_DEPTH = 11
_PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_ABSOLUTE = 2**128
_PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_DIGITS = 39
_FROZEN_PROTOCOL_BYTES = 125_063
_FROZEN_PROTOCOL_SHA256 = (
    "79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8"
)
_FROZEN_MACHINE_MANIFEST_BYTES = 2_038_189
_FROZEN_MACHINE_MANIFEST_SHA256 = (
    "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376"
)
_FROZEN_DEPENDENCY_LOCK_BYTES = 736
_FROZEN_DEPENDENCY_LOCK_SHA256 = (
    "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
)
_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP65 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP65 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP65 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP65PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    cp64_schema_version: str
    cp64_source_relative_path: str
    cp64_source_sha256: str
    cp64_source_bytes: int
    cp64_source_lines: int
    cp64_test_relative_path: str
    cp64_test_sha256: str
    cp64_test_bytes: int
    cp64_test_lines: int
    v15_protocol_relative_path: str
    v15_protocol_sha256: str
    v15_protocol_bytes: int
    v15_protocol_lines: int
    v15_manifest_relative_path: str
    v15_manifest_sha256: str
    v15_manifest_bytes: int
    v15_manifest_lines: int
    cp64_bundle_record_sha256: str
    cp64_bundle_public_sha256: str
    cp64_bundle_canonical_json_sha256: str
    cp64_bundle_canonical_json_bytes: int
    cp64_no_execution_gate_contract_record_sha256: str
    cp64_false_schema_definition_flags: Tuple[str, ...]
    cp64_gate_count: int
    cp64_evidence_present_count: int
    cp64_ledger_total_count: int
    cp64_ledger_satisfied_count: int
    cp64_ledger_missing_count: int
    v15_protocol_state: str
    v15_lifecycle_current_state: str
    v15_complete_production_roster_frozen: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    cp65_source_hashes_external_binding_required: bool
    predecessor_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65FieldRuleV1(_SealedRecord):
    schema_version: str
    rule_id: str
    artifact_id: str
    json_pointer: str
    value_kind: str
    required: bool
    integer_interval: Tuple[int, ...]
    length_interval: Tuple[int, ...]
    boolean_domain: Tuple[bool, ...]
    string_domain: Tuple[str, ...]
    string_pattern_id: str
    array_item_rule_ids: Tuple[str, ...]
    exact_object_keys: Tuple[str, ...]
    cross_constraint_ids: Tuple[str, ...]
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65ArtifactSchemaV1(_SealedRecord):
    schema_version: str
    artifact_id: str
    path_template: str
    path_scope: str
    presence_rule_id: str
    encoding: str
    media_kind: str
    exact_keys: Tuple[str, ...]
    field_rule_ids: Tuple[str, ...]
    record_rule_id: str
    minimum_instances: int
    maximum_instances: int
    minimum_bytes_per_instance: int
    maximum_bytes_per_instance: int
    final_newline_rule: str
    digest_preimage_contract_id: str
    dag_node_ids: Tuple[str, ...]
    auxiliary_reservation_class: str
    cp64_contract_preserved: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65TransientPathContractV1(_SealedRecord):
    schema_version: str
    transient_ordinal: int
    transient_path_id: str
    owner_artifact_id: str
    final_relative_path: str
    alternate_final_relative_path: str
    transient_relative_path: str
    primary_publication_arm_id: str
    alternate_publication_arm_id: str
    path_scope: str
    shard_ordinal: int
    transient_kind: str
    aliases_final_inode_when_published: bool
    prepared_authorization_alias: bool
    retained_at_committed: bool
    sha256_manifest_included: bool
    collision_free: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65DigestPreimageContractV1(_SealedRecord):
    schema_version: str
    contract_id: str
    artifact_id: str
    digest_field_pointer: str
    algorithm_id: str
    domain_separator: str
    canonical_profile_id: str
    zeroed_field_pointers: Tuple[str, ...]
    ordered_component_ids: Tuple[str, ...]
    output_encoding: str
    output_bytes: int
    verifier_implemented: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65Sha256PointerContractV1(_SealedRecord):
    schema_version: str
    classification_id: str
    target_artifact_id: str
    target_json_pointer: str
    semantic_class: str
    digest_kind: str
    source_artifact_id: str
    source_json_pointer: str
    source_contract_id: str
    source_availability_cut_id: str
    instance_selector_id: str
    cardinality_rule_id: str
    preimage_encoding: str
    domain_separator: str
    zero_policy_id: str
    conditional_binding_rule_id: str
    externally_retained_preimage_required: bool
    preimage_registry_entry_required: bool
    validator_implemented: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65PredicateContractV1(_SealedRecord):
    schema_version: str
    predicate_id: str
    applies_to_artifact_ids: Tuple[str, ...]
    input_json_pointers: Tuple[str, ...]
    operation_id: str
    operand_json_ascii: str
    child_predicate_ids: Tuple[str, ...]
    evaluation_order: Tuple[str, ...]
    failure_code: str
    validator_implemented: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65GateRequirementV1(_SealedRecord):
    schema_version: str
    gate_ordinal: int
    gate_id: str
    evidence_node_id: str
    evidence_artifact_id: str
    required_artifact_ids: Tuple[str, ...]
    predicate_id: str
    predicate_clause_ids: Tuple[str, ...]
    preflight_summary_covered: bool
    requires_external_provenance: bool
    requires_independent_authority: bool
    evidence_present: bool
    gate_state: str
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65AuxiliaryArtifactBoundV1(_SealedRecord):
    schema_version: str
    bound_id: str
    artifact_id: str
    physical_slot_group_id: str
    mutually_exclusive_artifact_ids: Tuple[str, ...]
    maximum_instance_count: int
    maximum_logical_bytes_per_instance: int
    maximum_reserved_bytes_per_instance: int
    maximum_total_reserved_bytes: int
    simultaneous_presence_rule_id: str
    reservation_partition_id: str
    destination_reservation_excluded: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65AuxiliarySizeProofV1(_SealedRecord):
    schema_version: str
    proof_id: str
    cp64_capacity_schema_record_sha256: str
    auxiliary_reservation_floor_bytes: int
    artifact_bound_ids: Tuple[str, ...]
    covered_complete_roster_artifact_ids: Tuple[str, ...]
    destination_artifact_ids: Tuple[str, ...]
    maximum_auxiliary_artifact_logical_bytes: int
    maximum_auxiliary_artifact_slot_reserved_bytes: int
    allocation_and_directory_charge_policy_slot_bytes: int
    maximum_auxiliary_policy_required_bytes: int
    exclusive_reserved_policy_headroom_bytes: int
    maximum_dynamic_hold_bytes: int
    arithmetic_formula: str
    every_auxiliary_artifact_covered_exactly_once: bool
    simultaneous_branch_upper_bound_conservative: bool
    integer_arithmetic_verified: bool
    fits_exclusive_auxiliary_reservation: bool
    definition_only: bool
    production_reservation_observed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65AuthorizationSignatureContractV1(_SealedRecord):
    schema_version: str
    scheme_id: str
    public_key_artifact_id: str
    authorization_artifact_id: str
    hash_algorithm_id: str
    mgf_algorithm_id: str
    modulus_bytes: int
    modulus_bit_length: int
    public_exponent: int
    signature_bytes: int
    signature_hex_characters: int
    salt_bytes: int
    em_bits: int
    em_bytes: int
    trailer_field: int
    unused_high_bits: int
    signing_preimage_domain: str
    signing_preimage_zeroed_field_pointers: Tuple[str, ...]
    signature_digest_formula: str
    public_key_identity_formula: str
    strict_pss_verification_steps: Tuple[str, ...]
    signer_implemented: bool
    key_generation_implemented: bool
    public_key_present: bool
    trust_root_bound: bool
    signature_instance_present: bool
    verifier_implemented: bool
    authority_verified: bool
    launch_authorized: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65SuppliedValidationV1(_SealedRecord):
    schema_version: str
    validation_scope: str
    caller_supplied_bytes_only: bool
    input_artifact_ids: Tuple[str, ...]
    input_relative_paths: Tuple[str, ...]
    input_sha256s: Tuple[str, ...]
    input_byte_lengths: Tuple[int, ...]
    validated_artifact_ids: Tuple[str, ...]
    validated_relative_paths: Tuple[str, ...]
    validated_body_sha256s: Tuple[str, ...]
    syntax_valid: bool
    intrinsic_digest_preimages_valid: bool
    all_required_digest_preimage_sources_supplied: bool
    validated_digest_preimage_count: int
    unresolved_digest_preimage_count: int
    digest_preimages_valid: bool
    all_required_cross_binding_targets_supplied: bool
    validated_cross_binding_count: int
    unresolved_cross_binding_count: int
    cross_bindings_valid: bool
    signature_verification_applicable: bool
    signature_mathematically_valid_under_supplied_key: bool
    parser_input_resource_limits_satisfied: bool
    external_production_receipts_observed: bool
    external_provenance_verified: bool
    filesystem_observed: bool
    source_authority_verified: bool
    authorization_trust_root_bound: bool
    authority_verified: bool
    production_evidence_accepted: bool
    gate_transition_permitted: bool
    launch_authorized: bool
    execution_permitted: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65ProductionSchemaPreimageValidatorBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    predecessor_custody: CP65PredecessorCustodyV1
    canonical_profile_id: str
    field_rules: Tuple[CP65FieldRuleV1, ...]
    artifact_schemas: Tuple[CP65ArtifactSchemaV1, ...]
    transient_path_contracts: Tuple[CP65TransientPathContractV1, ...]
    digest_preimage_contracts: Tuple[CP65DigestPreimageContractV1, ...]
    sha256_pointer_contracts: Tuple[CP65Sha256PointerContractV1, ...]
    predicate_contracts: Tuple[CP65PredicateContractV1, ...]
    gate_requirements: Tuple[CP65GateRequirementV1, ...]
    auxiliary_artifact_bounds: Tuple[CP65AuxiliaryArtifactBoundV1, ...]
    auxiliary_size_proof: CP65AuxiliarySizeProofV1
    authorization_signature_contract: CP65AuthorizationSignatureContractV1
    schema_semantic_sha256: str
    sha256_pointer_contract_count: int
    sha256_pointer_contracts_cover_every_sha256_field_rule: bool
    registry_required_targets_all_durable_by_gate15: bool
    later_artifacts_have_no_registry_dependency: bool
    all_schema_references_resolve_exactly_once: bool
    no_orphan_or_unused_rule_predicate_digest_or_artifact_ids: bool
    all_referenced_rules_have_executable_validator_semantics: bool
    global_path_count: int
    per_shard_path_template_count: int
    conditional_path_count: int
    expanded_final_path_count: int
    reserved_destination_partial_path_count: int
    prepared_authorization_partial_path_count: int
    auxiliary_reserved_partial_or_existing_final_slot_count: int
    auxiliary_reservation_hold_path_count: int
    ordinary_auxiliary_partial_candidate_path_count: int
    expanded_transient_path_count: int
    expanded_final_and_transient_path_count: int
    generic_writer_partial_paths_are_state_aliases: bool
    expanded_final_and_transient_paths_collision_free: bool
    candidate_shard_count: int
    gate_count: int
    evidence_present_count: int
    digest_dag_node_count: int
    digest_dag_edge_count: int
    digest_dag_node_ids: Tuple[str, ...]
    digest_dag_edges: Tuple[Tuple[str, str], ...]
    digest_dag_edge_target_pointers: Tuple[str, ...]
    digest_dag_edge_source_contract_ids: Tuple[str, ...]
    digest_dag_edge_digest_kinds: Tuple[str, ...]
    digest_dag_is_gate_evidence_only: bool
    artifact_preimage_dependency_node_ids: Tuple[str, ...]
    artifact_preimage_dependency_edges: Tuple[Tuple[str, str], ...]
    artifact_preimage_edge_target_pointers: Tuple[str, ...]
    artifact_preimage_edge_source_contract_ids: Tuple[str, ...]
    artifact_preimage_edge_digest_kinds: Tuple[str, ...]
    artifact_preimage_topological_order: Tuple[str, ...]
    artifact_preimage_node_count: int
    artifact_preimage_edge_count: int
    artifact_preimage_dag_acyclic: bool
    artifact_preimage_dag_complete: bool
    artifact_body_domain_separators_unique: bool
    receipt_envelope_artifact_ids: Tuple[str, ...]
    referenced_execution_output_artifact_ids: Tuple[str, ...]
    frozen_or_binary_custody_artifact_ids: Tuple[str, ...]
    receipt_envelope_schema_count: int
    referenced_execution_output_schema_count: int
    frozen_or_binary_custody_schema_count: int
    artifact_kind_partitions_disjoint_and_exhaustive: bool
    schema_completeness_claim_scope: str
    all_required_production_receipt_keysets_predeclared: bool
    complete_receipt_type_range_size_and_domain_schemas_frozen: bool
    complete_auxiliary_artifact_size_schema_frozen: bool
    bounded_auxiliary_artifact_size_proof_present: bool
    generic_prestart_terminal_record_schema_frozen: bool
    all_required_production_receipt_digest_preimages_frozen: bool
    complete_production_digest_instance_validation_interface_frozen: bool
    authorization_signature_preimage_and_verifier_frozen: bool
    requirement_schemas_frozen: bool
    complete_final_path_template_roster_frozen: bool
    complete_production_roster_frozen: bool
    artifact_occurrence_and_branch_schema_frozen: bool
    production_receipt_schema_frozen: bool
    production_execution_and_output_schema_frozen: bool
    production_schema_frozen: bool
    source_receipt_binds_capsule_body: bool
    capacity_receipt_binds_shard_map: bool
    external_production_receipts_observed: bool
    external_seed_values_present: bool
    source_authority_verified: bool
    production_runtime_observed: bool
    capacity_observed: bool
    durability_observed: bool
    candidate_shard_policy_selected: bool
    production_shard_map_instantiated: bool
    runner_supervisor_qualified: bool
    closed_classifier_qualified: bool
    power_thresholds_frozen: bool
    freeze_receipt_present: bool
    independent_signoffs_present: bool
    launch_authorization_present: bool
    started: bool
    production_requests_materialized: bool
    production_campaign_exposed: bool
    production_execution_authorized: bool
    production_execution_observed: bool
    estimates_computed: bool
    intervals_computed: bool
    decision_made: bool
    runner_and_recomputation_blocker_closed: bool
    unconditional_operational_predictions_blocker_closed: bool
    power_and_thresholds_blocker_closed: bool
    confirmatory_custody_blocker_closed: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    ledger_prerequisite_id: str
    ledger_total_count: int
    ledger_satisfied_count: int
    ledger_missing_count: int
    zero_argument_builder: bool
    stdlib_only_import: bool
    project_modules_imported: bool
    host_filesystem_probed: bool
    clock_read: bool
    rng_used: bool
    network_used: bool
    subprocess_api_exposed: bool
    filesystem_path_api_exposed: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_RECORD_DOMAINS = {
    CP65PredecessorCustodyV1: b"cp65-predecessor-custody-v1",
    CP65FieldRuleV1: b"cp65-field-rule-v1",
    CP65ArtifactSchemaV1: b"cp65-artifact-schema-v1",
    CP65TransientPathContractV1: b"cp65-transient-path-contract-v1",
    CP65DigestPreimageContractV1: b"cp65-digest-preimage-contract-v1",
    CP65Sha256PointerContractV1: b"cp65-sha256-pointer-contract-v1",
    CP65PredicateContractV1: b"cp65-predicate-contract-v1",
    CP65GateRequirementV1: b"cp65-gate-requirement-v1",
    CP65AuxiliaryArtifactBoundV1: b"cp65-auxiliary-artifact-bound-v1",
    CP65AuxiliarySizeProofV1: b"cp65-auxiliary-size-proof-v1",
    CP65AuthorizationSignatureContractV1: b"cp65-authorization-signature-contract-v1",
    CP65SuppliedValidationV1: b"cp65-supplied-validation-v1",
    CP65ProductionSchemaPreimageValidatorBundleV1: (
        b"cp65-production-schema-preimage-validator-bundle-v1"
    ),
}

_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS: weakref.WeakKeyDictionary[
    _SealedRecord, bytes
] = weakref.WeakKeyDictionary()


def _canonical_value(value: object, *, require_issued: bool) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is tuple:
        return tuple(
            _canonical_value(item, require_issued=require_issued) for item in value
        )
    if isinstance(value, _SealedRecord):
        if type(value) not in _RECORD_DOMAINS:
            raise TypeError("unsupported CP65 sealed record type")
        if require_issued:
            with _ISSUED_RECORD_LOCK:
                if _ISSUED_RECORD_SNAPSHOTS.get(value) is None:
                    raise TypeError("CP65 record was not module-created")
        return {
            item.name: _canonical_value(
                getattr(value, item.name), require_issued=require_issued
            )
            for item in fields(type(value))
        }
    raise TypeError("value has no CP65 canonical representation")


def _canonical_bytes(value: object, *, require_issued: bool) -> bytes:
    return json.dumps(
        _canonical_value(value, require_issued=require_issued),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _record(cls: type, values: Mapping[str, object]) -> object:
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP65 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    provisional = object.__new__(cls)
    for name in names:
        object.__setattr__(provisional, name, complete[name])
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls]
        + b"\0"
        + _canonical_bytes(provisional, require_issued=False)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _canonical_bytes(result, require_issued=False)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = snapshot
    return result


def _reject_float(_text: str) -> object:
    raise ValueError("CP65 canonical JSON forbids floating-point values")


def _reject_constant(_text: str) -> object:
    raise ValueError("CP65 canonical JSON forbids nonfinite constants")


def _bounded_parse_int(text: str) -> int:
    unsigned = text[1:] if text.startswith("-") else text
    if len(unsigned) > 20:
        raise ValueError("CP65 canonical JSON integer token is too long")
    value = int(text, 10)
    if not -(2**63) <= value <= 2**64 - 1:
        raise ValueError("CP65 canonical JSON integer is outside parser bounds")
    return value


def _bounded_predecessor_manifest_parse_int(text: str) -> int:
    """Parse only the already hash-pinned v15 manifest's wider integers."""

    unsigned = text[1:] if text.startswith("-") else text
    if len(unsigned) > _PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_DIGITS:
        raise ValueError("frozen predecessor manifest integer token is too long")
    value = int(text, 10)
    if abs(value) > _PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_ABSOLUTE:
        raise ValueError("frozen predecessor manifest integer is outside its bound")
    return value


def _unique_object(pairs: list) -> dict:
    if len(pairs) > 128:
        raise ValueError("CP65 canonical JSON object has too many members")
    result = {}
    for key, value in pairs:
        try:
            key_bytes = key.encode("ascii")
        except (AttributeError, UnicodeEncodeError) as exc:
            raise ValueError("CP65 canonical JSON key is outside its bound") from exc
        if len(key_bytes) > 128:
            raise ValueError("CP65 canonical JSON key is outside its bound")
        if key in result:
            raise ValueError("CP65 canonical JSON contains a duplicate key")
        result[key] = value
    return result


def _unique_predecessor_manifest_object(pairs: list) -> dict:
    if len(pairs) > _PINNED_PREDECESSOR_MANIFEST_MAX_OBJECT_MEMBERS:
        raise ValueError("frozen predecessor manifest object is too wide")
    return _unique_object(pairs)


def _validate_lexical_json_nesting(payload: bytes) -> None:
    depth = 0
    structural_node_lower_bound = 1
    in_string = False
    escaped = False
    for byte in payload:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            structural_node_lower_bound += 1
            if structural_node_lower_bound > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
                raise ValueError("CP65 canonical JSON contains too many nodes")
            if depth > 16:
                raise ValueError("CP65 canonical JSON nesting is too deep")
        elif byte in (0x5D, 0x7D):
            depth -= 1
            if depth < 0:
                raise ValueError("CP65 canonical JSON nesting is malformed")
        elif byte == 0x2C:
            structural_node_lower_bound += 1
            if structural_node_lower_bound > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
                raise ValueError("CP65 canonical JSON contains too many nodes")


def _validate_json_resources(value: object) -> Tuple[int, int]:
    stack = [(value, 1)]
    node_count = 0
    decoded_string_characters = 0
    while stack:
        current, depth = stack.pop()
        node_count += 1
        if node_count > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
            raise ValueError("CP65 canonical JSON contains too many nodes")
        if depth > 16:
            raise ValueError("CP65 canonical JSON nesting is too deep")
        if current is None:
            raise ValueError("CP65 canonical JSON forbids null")
        if type(current) in (bool, int):
            continue
        if type(current) is str:
            try:
                length = len(current.encode("ascii"))
            except UnicodeEncodeError as exc:
                raise ValueError("CP65 canonical JSON strings must be ASCII") from exc
            if length > 1_048_576:
                raise ValueError("CP65 canonical JSON string is too long")
            decoded_string_characters += len(current)
            if (
                decoded_string_characters
                > _MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS
            ):
                raise ValueError("CP65 canonical JSON decoded strings exceed their cap")
            continue
        if type(current) is list:
            if len(current) > 32_768:
                raise ValueError("CP65 canonical JSON array is too long")
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            decoded_string_characters += sum(len(key) for key in current)
            if (
                decoded_string_characters
                > _MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS
            ):
                raise ValueError("CP65 canonical JSON decoded strings exceed their cap")
            stack.extend((item, depth + 1) for item in current.values())
            continue
        raise ValueError("CP65 canonical JSON contains an unsupported value")
    return node_count, decoded_string_characters


def _validate_pinned_predecessor_manifest_resources(
    value: object,
) -> Tuple[int, int, int, int, int, int]:
    """Apply the measured, predecessor-only resource profile to v15 JSON."""

    stack = [(value, 1)]
    node_count = 0
    decoded_string_characters = 0
    maximum_depth = 0
    maximum_object_members = 0
    maximum_integer_absolute = 0
    maximum_integer_digits = 0
    while stack:
        current, depth = stack.pop()
        node_count += 1
        maximum_depth = max(maximum_depth, depth)
        if node_count > _PINNED_PREDECESSOR_MANIFEST_MAX_NODES:
            raise ValueError("frozen predecessor manifest has too many nodes")
        if depth > _PINNED_PREDECESSOR_MANIFEST_MAX_DEPTH:
            raise ValueError("frozen predecessor manifest nesting is too deep")
        # The already hash-pinned predecessor manifest contains JSON null
        # sentinels.  They remain forbidden by the ordinary CP65 parser but
        # are a measured scalar in this predecessor-only decoding profile.
        if current is None:
            continue
        if type(current) is bool:
            continue
        if type(current) is int:
            absolute = abs(current)
            digits = len(str(absolute))
            if absolute > _PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_ABSOLUTE:
                raise ValueError("frozen predecessor manifest integer is too large")
            if digits > _PINNED_PREDECESSOR_MANIFEST_MAX_INTEGER_DIGITS:
                raise ValueError(
                    "frozen predecessor manifest integer token is too long"
                )
            maximum_integer_absolute = max(maximum_integer_absolute, absolute)
            maximum_integer_digits = max(maximum_integer_digits, digits)
            continue
        if type(current) is str:
            try:
                current.encode("ascii")
            except UnicodeEncodeError as exc:
                raise ValueError(
                    "frozen predecessor manifest string is not ASCII"
                ) from exc
            decoded_string_characters += len(current)
        elif type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
        elif type(current) is dict:
            width = len(current)
            maximum_object_members = max(maximum_object_members, width)
            if width > _PINNED_PREDECESSOR_MANIFEST_MAX_OBJECT_MEMBERS:
                raise ValueError("frozen predecessor manifest object is too wide")
            for key in current:
                if type(key) is not str:
                    raise ValueError("frozen predecessor manifest key is not text")
                try:
                    key.encode("ascii")
                except UnicodeEncodeError as exc:
                    raise ValueError(
                        "frozen predecessor manifest key is not ASCII"
                    ) from exc
                decoded_string_characters += len(key)
            stack.extend((item, depth + 1) for item in current.values())
        else:
            raise ValueError("frozen predecessor manifest value kind differs")
        if (
            decoded_string_characters
            > _PINNED_PREDECESSOR_MANIFEST_MAX_DECODED_STRING_CHARACTERS
        ):
            raise ValueError(
                "frozen predecessor manifest decoded strings exceed their cap"
            )
    return (
        node_count,
        decoded_string_characters,
        maximum_depth,
        maximum_object_members,
        maximum_integer_absolute,
        maximum_integer_digits,
    )


def _parse_canonical_json_object_impl(payload: object, maximum_bytes: int) -> dict:
    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    if type(maximum_bytes) is not int or maximum_bytes < 2:
        raise TypeError("maximum_bytes must be a positive exact integer")
    if not 2 <= len(payload) <= maximum_bytes:
        raise ValueError("payload byte length is outside the frozen bound")
    _validate_lexical_json_nesting(payload)
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("payload must be ASCII") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_int=_bounded_parse_int,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (
        json.JSONDecodeError,
        UnicodeError,
        RecursionError,
        OverflowError,
        MemoryError,
    ) as exc:
        raise ValueError("payload is not bounded CP65 canonical JSON") from exc
    if type(value) is not dict:
        raise ValueError("payload must contain one top-level object")
    _validate_json_resources(value)
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if canonical != payload:
        raise ValueError("payload differs from exact CP65 canonical JSON")
    return value


def _parse_canonical_json_object(payload: object, maximum_bytes: int) -> dict:
    try:
        return _parse_canonical_json_object_impl(payload, maximum_bytes)
    except MemoryError as exc:
        raise ValueError("payload is not bounded CP65 canonical JSON") from exc


def _parse_pinned_predecessor_manifest(payload: bytes) -> dict:
    """Parse the exact v15 manifest after its immutable byte pin is checked."""

    try:
        _validate_lexical_json_nesting(payload)
        text = payload.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_unique_predecessor_manifest_object,
            parse_int=_bounded_predecessor_manifest_parse_int,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
        if type(value) is not dict:
            raise ValueError("frozen predecessor manifest must be an object")
        _validate_pinned_predecessor_manifest_resources(value)
    except (
        json.JSONDecodeError,
        UnicodeError,
        RecursionError,
        OverflowError,
        MemoryError,
    ) as exc:
        raise ValueError("frozen predecessor manifest is not canonical JSON") from exc
    return value


def _mgf1_sha256(seed: bytes, output_length: int) -> bytes:
    if type(seed) is not bytes or type(output_length) is not int:
        raise TypeError("MGF1 inputs have the wrong exact type")
    if not 0 <= output_length <= 351:
        raise ValueError("MGF1 output length is outside the CP65 profile")
    result = bytearray()
    counter = 0
    while len(result) < output_length:
        result.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(result[:output_length])


def _verify_rsa_pss_sha256_3072(
    message: bytes, modulus: bytes, signature: bytes
) -> bool:
    """Verify the fixed CP65 RSA-PSS profile; never sign or generate a key."""

    if type(message) is not bytes or type(modulus) is not bytes:
        raise TypeError("RSA-PSS inputs must be exact bytes")
    if type(signature) is not bytes:
        raise TypeError("RSA-PSS signature must be exact bytes")
    if len(modulus) != 384 or len(signature) != 384:
        return False
    modulus_integer = int.from_bytes(modulus, "big")
    if (
        modulus_integer.bit_length() != 3_072
        or modulus_integer % 2 == 0
        or math.gcd(modulus_integer, 65_537) != 1
    ):
        return False
    signature_integer = int.from_bytes(signature, "big")
    if signature_integer >= modulus_integer:
        return False
    encoded = pow(signature_integer, 65_537, modulus_integer).to_bytes(384, "big")
    if encoded[-1] != 0xBC:
        return False
    masked_db = encoded[:351]
    encoded_hash = encoded[351:383]
    if masked_db[0] & 0x80:
        return False
    mask = _mgf1_sha256(encoded_hash, 351)
    data_block = bytearray(left ^ right for left, right in zip(masked_db, mask))
    data_block[0] &= 0x7F
    if data_block[:318] != b"\0" * 318 or data_block[318] != 0x01:
        return False
    salt = bytes(data_block[319:351])
    message_hash = hashlib.sha256(message).digest()
    expected_hash = hashlib.sha256(b"\0" * 8 + message_hash + salt).digest()
    return hmac.compare_digest(encoded_hash, expected_hash)


def _validate_public_record(record: object) -> Tuple[_SealedRecord, bytes]:
    if type(record) not in _RECORD_DOMAINS:
        raise TypeError("unsupported CP65 record type")
    sealed = cast(_SealedRecord, record)
    with _ISSUED_RECORD_LOCK:
        snapshot = _ISSUED_RECORD_SNAPSHOTS.get(sealed)
        if snapshot is None:
            raise TypeError("CP65 record was not module-created")
        current = _canonical_bytes(sealed, require_issued=True)
    if current != snapshot:
        raise ValueError("CP65 issued record was mutated")
    names = tuple(item.name for item in fields(type(sealed)))
    provisional = object.__new__(type(sealed))
    for name in names:
        object.__setattr__(
            provisional,
            name,
            _ZERO_SHA256 if name == "record_sha256" else getattr(sealed, name),
        )
    expected = hashlib.sha256(
        _RECORD_DOMAINS[type(sealed)]
        + b"\0"
        + _canonical_bytes(provisional, require_issued=False)
    ).hexdigest()
    if sealed.record_sha256 != expected:
        raise ValueError("CP65 record digest differs")
    return sealed, snapshot


_GLOBAL_PATHS = (
    "frozen_inputs/protocol.md",
    "frozen_inputs/protocol.sha256",
    "frozen_inputs/machine_manifest.json",
    "frozen_inputs/bound_files.json",
    "frozen_inputs/dependency_lock.txt",
    "freeze_receipt.json",
    "power_threshold_receipt.json",
    "preflight_gate_summary.json",
    "independent_signoff.json",
    "capacity_receipt.json",
    "auxiliary_metadata_reservation.json",
    "reservation_manifest.json",
    "production_runtime_receipt.json",
    "seed_acquisition_start_receipt.json",
    "seed_acquisition_journal.bin",
    "seed_source_receipt.json",
    "seed_capsule.json",
    "shard_map.json",
    "durability_receipt.json",
    "preauthorization_outcome.json",
    "launch_authorization.json",
    "postauthorization_outcome.json",
    "STARTED.json",
    "environment.json",
    "launch_receipt.json",
    "metrics/primary_metrics.json",
    "metrics/secondary_diagnostics.json",
    "independent_recomputation.json",
    "decisions.json",
    "deviations.json",
    "failures.json",
    "exclusions.json",
    "reruns.json",
    "terminal_state.json",
    "sha256_manifest.json",
    "COMMITTED.json",
    "frozen_inputs/launch_authority_public_key.json",
    "dependency_lock_match_receipt.json",
    "seed_source_custody_artifact.json",
    "seed_capsule_sequence_crosscheck_receipt.json",
    "production_schedule.json",
    "production_runner_supervisor_qualification_receipt.json",
    "closed_refusal_failure_classifier_qualification_receipt.json",
    "independent_554_estimate_interval_decision_path_qualification_receipt.json",
    "independent_full_32768_recomputation_qualification_receipt.json",
    "frozen_inputs/independent_reviewer_public_keys.json",
    "frozen_inputs/seed_source_authority_public_key.json",
    "seed_source_authority_attestation.json",
    "frozen_inputs/source_fixture_materialization.bin",
    "frozen_inputs/production_schema_preimage_validator_bundle.json",
    "power_review_signoff.json",
    "preterminal_durable_artifact_inventory.json",
    "external_digest_preimage_registry.json",
    "auxiliary_reservation_transition_journal.bin",
)
_PER_SHARD_PATHS = (
    "shards/{shard_id}/requests.jsonl",
    "shards/{shard_id}/raw_records.jsonl",
    "shards/{shard_id}/stable_traces.jsonl",
    "shards/{shard_id}/stderr_records.bin",
    "shards/{shard_id}/rng_initial_states.json",
    "shards/{shard_id}/rng_final_states.json",
    "shards/{shard_id}/shard_index.json",
    "shards/{shard_id}/shard_receipt.json",
)
_CONDITIONAL_PATHS = (
    "seed_partial_acquisition_terminal_receipt.json",
    "rejected_launch_authorization_candidate.json",
)

_EXTERNAL_SEED_SOURCE_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "cp61_stable_design_sha256",
    "seed_count",
    "seed_encoding",
    "source_method_id",
    "acquisition_start_receipt_sha256",
    "acquisition_session_sha256",
    "acquisition_journal_sha256",
    "acquisition_journal_head_sha256",
    "acquisition_journal_entry_count",
    "ordered_seed_values_commitment_sha256",
    "custody_artifact_sha256",
    "source_authority_attestation_sha256",
    "body_sha256",
)
_ACQUISITION_START_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "source_method_id",
    "acquisition_journal_relative_path",
    "acquisition_journal_device_identity_sha256",
    "acquisition_journal_inode",
    "acquisition_journal_preallocated_bytes",
    "acquisition_journal_allocation_method_id",
    "acquisition_journal_extent_map_sha256",
    "acquisition_journal_file_fsync_completed_at_utc",
    "acquisition_journal_directory_fsync_completed_at_utc",
    "acquisition_journal_inode_recheck_sha256",
    "acquisition_session_id",
    "started_at_utc",
    "body_sha256",
)
_PARTIAL_ACQUISITION_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "acquisition_start_receipt_sha256",
    "source_method_id",
    "expected_seed_count",
    "acquired_seed_count",
    "acquisition_journal_sha256",
    "acquisition_journal_head_sha256",
    "acquisition_journal_entry_count",
    "acquisition_journal_raw_bytes",
    "seed_encoding",
    "ordered_partial_seed_values",
    "ordered_partial_seed_values_commitment_sha256",
    "terminal_state",
    "topup_redraw_reselection_permitted",
    "body_sha256",
)
_RUNTIME_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "observation_session_sha256",
    "observed_at_utc",
    "source_manifest_sha256",
    "dependency_lock_sha256",
    "runtime_profile_id",
    "python_executable_sha256",
    "python_framework_sha256",
    "stdlib_closure_sha256",
    "numpy_record_sha256",
    "numpy_payload_closure_sha256",
    "scipy_record_sha256",
    "scipy_payload_closure_sha256",
    "loaded_local_source_closure_sha256",
    "abi_map_sha256",
    "environment_sha256",
    "body_sha256",
)
_CAPACITY_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "destination_reservation_required_bytes",
    "auxiliary_metadata_reservation_required_bytes",
    "combined_available_and_quota_required_before_reservation_bytes",
    "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
    "schedule_sha256",
    "capacity_schema_sha256",
    "storage_root_identity_sha256",
    "filesystem_identity_sha256",
    "measurement_session_sha256",
    "measured_at_utc",
    "measurement_method_id",
    "quota_method_id",
    "reservation_method_id",
    "auxiliary_metadata_reservation_method_id",
    "allocation_unit_bytes",
    "auxiliary_metadata_reservation_artifact_sha256",
    "available_bytes_before_reservation",
    "quota_headroom_bytes_before_reservation",
    "physically_allocated_reservation_bytes",
    "physically_allocated_auxiliary_metadata_bytes",
    "auxiliary_metadata_reserved_quota_bytes",
    "usable_reserved_bytes_after_allocation",
    "available_bytes_after_reservation",
    "quota_headroom_bytes_after_reservation",
    "available_inodes_after_reservation",
    "non_sparse_allocation_verified",
    "reservation_same_filesystem_verified",
    "reservation_exclusive_verified",
    "reservation_durable_verified",
    "auxiliary_metadata_reservation_exclusive_verified",
    "auxiliary_metadata_non_sparse_allocation_verified",
    "auxiliary_metadata_reserved_quota_verified",
    "auxiliary_metadata_reservation_durable_verified",
    "auxiliary_metadata_reservation_same_storage_root_verified",
    "destination_and_auxiliary_reservation_no_double_count_verified",
    "shard_count",
    "atomic_rename_supported",
    "file_fsync_supported",
    "directory_fsync_supported",
    "auxiliary_artifact_size_proof_sha256",
    "maximum_auxiliary_artifact_logical_bytes",
    "maximum_auxiliary_reserved_bytes",
    "allocation_and_directory_charge_policy_slot_bytes",
    "observed_allocation_and_directory_charge_bytes",
    "allocation_and_directory_charge_within_policy",
    "reservation_manifest_sha256",
    "body_sha256",
)
_DURABILITY_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "capacity_receipt_sha256",
    "layout_contract_sha256",
    "writer_source_manifest_sha256",
    "qualification_session_sha256",
    "filesystem_identity_sha256",
    "atomic_rename_verified",
    "file_fsync_verified",
    "directory_fsync_verified",
    "exclusive_create_verified",
    "no_symlink_verified",
    "no_hardlink_verified",
    "no_overwrite_verified",
    "body_sha256",
)
_SHARD_MAP_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "seed_capsule_body_sha256",
    "schedule_sha256",
    "capacity_receipt_sha256",
    "durability_receipt_sha256",
    "candidate_shard_policy_sha256",
    "reservation_manifest_sha256",
    "shard_count",
    "shards",
    "body_sha256",
)
_SHARD_ROW_KEYS = (
    "shard_ordinal",
    "shard_id",
    "seed_ordinal_min",
    "seed_ordinal_max",
    "logical_request_ordinal_min",
    "logical_request_ordinal_max",
    "logical_request_count",
    "relative_directory",
    "capacity_partition_bytes",
    "per_file_reservation_manifest_entry_sha256s",
    "shard_record_sha256",
)
_LAUNCH_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "attempt_state",
    "protocol_sha256",
    "machine_manifest_sha256",
    "source_manifest_sha256",
    "dependency_lock_sha256",
    "seed_source_receipt_sha256",
    "seed_capsule_body_sha256",
    "schedule_sha256",
    "production_runtime_receipt_sha256",
    "capacity_receipt_sha256",
    "durability_receipt_sha256",
    "production_shard_map_receipt_sha256",
    "preflight_gate_summary_sha256",
    "power_threshold_receipt_sha256",
    "freeze_receipt_sha256",
    "independent_signoff_sha256",
    "authorized_attempt_number",
    "authorization_issued_at_utc",
    "authorization_expires_at_utc",
    "authority_scheme_id",
    "authority_identity_sha256",
    "authority_signature_hex",
    "authority_signature_sha256",
    "body_sha256",
)
_PREFLIGHT_SUMMARY_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "covered_gate_ids",
    "covered_gate_states",
    "covered_evidence_node_ids",
    "ordered_evidence_receipt_sha256s",
    "external_digest_preimage_registry_sha256",
    "body_sha256",
)
_PREAUTH_OUTCOME_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "outcome_arm",
    "prepared_launch_authorization_sha256",
    "terminal_state",
    "selected_at_utc",
    "body_sha256",
)
_POSTAUTH_OUTCOME_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "launch_authorization_sha256",
    "outcome_arm",
    "terminal_state",
    "selected_at_utc",
    "body_sha256",
)
_COMMITTED_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "terminal_state_sha256",
    "sha256_manifest_sha256",
    "auxiliary_metadata_reservation_sha256",
    "auxiliary_reservation_transition_journal_sha256",
    "auxiliary_reservation_transition_journal_final_head_sha256",
    "auxiliary_reservation_transition_journal_final_entry_count",
    "auxiliary_reservation_transition_journal_file_fsync_completed_at_utc",
    "auxiliary_reservation_transition_journal_directory_fsync_completed_at_utc",
    "hold_relative_path",
    "hold_device_identity_sha256",
    "hold_inode",
    "hold_extent_map_sha256",
    "hold_removed_at_utc",
    "hold_removal_directory_fsync_completed_at_utc",
    "hold_absence_verified",
    "committed_at_utc",
    "body_sha256",
)
_SOURCE_MANIFEST_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "protocol_sha256",
    "machine_manifest_sha256",
    "entry_count",
    "total_bytes",
    "entries",
    "ordered_entries_sha256",
    "body_sha256",
)
_SOURCE_MANIFEST_ENTRY_KEYS = (
    "ordinal",
    "role",
    "relative_path",
    "bytes",
    "lines",
    "sha256",
)
_DEPENDENCY_MATCH_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "dependency_lock_relative_path",
    "expected_sha256",
    "observed_sha256",
    "observed_bytes",
    "match_verified",
    "verified_at_utc",
    "body_sha256",
)
_POWER_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "protocol_sha256",
    "machine_manifest_sha256",
    "power_review_ascii",
    "power_review_sha256",
    "selected_count_justification_ascii",
    "selected_count_justification_sha256",
    "primary_slot_count",
    "ordered_slot_thresholds",
    "ordered_slot_threshold_row_sha256s",
    "ordered_slot_thresholds_sha256",
    "reviewer_signoff_sha256",
    "completed_at_utc",
    "body_sha256",
)
_THRESHOLD_ROW_KEYS = (
    "slot_ordinal",
    "gate_id",
    "estimand_id",
    "threshold_encoding",
    "threshold_value",
    "design_minimum_selected_count",
    "justification_ascii",
    "justification_sha256",
    "row_sha256",
)
_FREEZE_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "from_state",
    "to_state",
    "protocol_sha256",
    "machine_manifest_sha256",
    "bound_files_sha256",
    "frozen_source_fixture_materialization_sha256",
    "dependency_lock_sha256",
    "power_threshold_receipt_sha256",
    "launch_authority_public_key_sha256",
    "independent_reviewer_public_key_set_sha256",
    "seed_source_authority_public_key_sha256",
    "production_receipt_schema_bundle_sha256",
    "frozen_at_utc",
    "freezer_identity_sha256",
    "body_sha256",
)
_PUBLIC_KEY_KEYS = (
    "schema",
    "purpose",
    "authority_scheme_id",
    "authority_id",
    "modulus_hex",
    "public_exponent",
    "valid_from_utc",
    "valid_until_utc",
    "body_sha256",
)
_SOURCE_CUSTODY_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "source_method_id",
    "acquisition_session_sha256",
    "custody_media_type",
    "custody_encoding",
    "custody_bytes",
    "custody_payload_sha256",
    "retention_location_identity_sha256",
    "created_at_utc",
    "body_sha256",
)
_CAPSULE_CROSSCHECK_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "source_receipt_sha256",
    "seed_capsule_body_sha256",
    "source_sequence_commitment_sha256",
    "capsule_sequence_commitment_sha256",
    "seed_count",
    "seed_encoding",
    "sequence_equal",
    "checked_at_utc",
    "body_sha256",
)
_SCHEDULE_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "seed_capsule_body_sha256",
    "schedule_contract_sha256",
    "request_count",
    "requests",
    "ordered_request_record_sha256s",
    "ordered_requests_sha256",
    "body_sha256",
)
_SEED_CAPSULE_KEYS = (
    "schema",
    "purpose",
    "cp61_stable_design_sha256",
    "seed_count",
    "seed_ordinals",
    "seed_encoding",
    "ordered_seed_values",
    "source_method_id",
    "source_receipt_sha256",
    "acquisition_session_sha256",
    "body_sha256",
)
_SCHEDULE_REQUEST_KEYS = (
    "schema_version",
    "seed_capsule_body_sha256",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "seed_free_request_sha256",
    "runtime_lock_sha256",
    "request_instance_sha256",
    "request_row_sha256",
)
_TERMINAL_COUNT_KEYS = (
    "returned_rejection_selected_before_deadline",
    "returned_rejection_exhausted_before_deadline",
    "returned_sir_selected_before_deadline",
    "preexecution_refusal_before_deadline",
    "execution_failure_before_deadline",
    "timeout_censored_at_deadline",
)
_RUNNER_QUALIFICATION_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "source_manifest_sha256",
    "runtime_receipt_sha256",
    "supervisor_contract_sha256",
    "qualification_fixture_set_sha256",
    "qualification_test_count",
    "timeout_case_count",
    "process_group_cleanup_case_count",
    "fd_leak_case_count",
    "environment_drift_case_count",
    "all_cases_passed",
    "qualified_at_utc",
    "body_sha256",
)
_CLASSIFIER_QUALIFICATION_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "classifier_source_manifest_sha256",
    "supervisor_contract_sha256",
    "closed_refusal_codes",
    "closed_failure_codes",
    "reachability_case_count",
    "all_closed_arms_reachable",
    "unknown_codes_rejected",
    "qualified_at_utc",
    "body_sha256",
)
_FULL_QUALIFICATION_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "qualification_fixture_set_sha256",
    "production_schedule_contract_sha256",
    "raw_record_schema_sha256",
    "stable_projection_schema_sha256",
    "independent_recomputation_source_manifest_sha256",
    "qualification_case_count",
    "expected_request_count_supported",
    "expected_estimand_count_supported",
    "repetition_blind_recomputation_verified",
    "all_cases_passed",
    "qualified_at_utc",
    "body_sha256",
)
_INDEPENDENT_554_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "qualification_fixture_set_sha256",
    "estimand_contract_sha256",
    "independent_source_manifest_sha256",
    "expected_estimand_count_supported",
    "estimate_path_qualification_case_count",
    "interval_path_qualification_case_count",
    "decision_path_qualification_case_count",
    "repetition_blind_recomputation_verified",
    "all_554_estimands_supported",
    "all_cases_passed",
    "qualified_at_utc",
    "body_sha256",
)
_SIGNOFF_SET_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "preflight_gate_summary_sha256",
    "reviewer_public_key_set_sha256",
    "required_reviewer_roles",
    "ordered_signoffs",
    "signoff_count",
    "all_required_roles_present",
    "all_decisions_approve",
    "all_signatures_mathematically_valid_under_declared_keys",
    "body_sha256",
)
_SIGNOFF_ROW_KEYS = (
    "reviewer_role",
    "reviewer_identity_sha256",
    "reviewer_public_key_identity_sha256",
    "reviewed_artifact_sha256s",
    "decision",
    "signed_at_utc",
    "signature_scheme_id",
    "reviewer_signature_sha256",
    "reviewer_signature_hex",
    "signoff_sha256",
)
_REVIEWER_KEY_SET_KEYS = (
    "schema",
    "purpose",
    "protocol_sha256",
    "machine_manifest_sha256",
    "required_reviewer_roles",
    "key_count",
    "ordered_keys",
    "ordered_public_key_identity_sha256s",
    "body_sha256",
)
_REVIEWER_KEY_ROW_KEYS = (
    "reviewer_role",
    "reviewer_identity_sha256",
    "signature_scheme_id",
    "authority_id",
    "public_key_identity_sha256",
    "modulus_hex",
    "public_exponent",
    "valid_from_utc",
    "valid_until_utc",
    "row_sha256",
)
_SEED_AUTHORITY_KEY_KEYS = (
    "schema",
    "purpose",
    "source_authority_scheme_id",
    "source_authority_id",
    "modulus_hex",
    "public_exponent",
    "valid_from_utc",
    "valid_until_utc",
    "body_sha256",
)
_SEED_AUTHORITY_ATTESTATION_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "acquisition_start_receipt_sha256",
    "acquisition_journal_sha256",
    "acquisition_journal_head_sha256",
    "acquisition_journal_entry_count",
    "ordered_seed_values_commitment_sha256",
    "seed_source_custody_artifact_sha256",
    "source_method_id",
    "source_authority_scheme_id",
    "source_authority_identity_sha256",
    "attested_at_utc",
    "attestation_expires_at_utc",
    "source_authority_signature_hex",
    "source_authority_signature_sha256",
    "body_sha256",
)
_POWER_REVIEW_SIGNOFF_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "protocol_sha256",
    "machine_manifest_sha256",
    "power_review_sha256",
    "selected_count_justification_sha256",
    "primary_slot_count",
    "ordered_slot_threshold_row_sha256s",
    "ordered_slot_thresholds_sha256",
    "reviewer_role",
    "reviewer_identity_sha256",
    "reviewer_public_key_identity_sha256",
    "decision",
    "signed_at_utc",
    "signature_scheme_id",
    "reviewer_signature_sha256",
    "reviewer_signature_hex",
    "body_sha256",
)
_TERMINAL_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "terminal_arm",
    "previous_lifecycle_state",
    "terminal_state",
    "freeze_receipt_sha256",
    "preauthorization_outcome_sha256",
    "launch_authorization_sha256",
    "postauthorization_outcome_sha256",
    "started_receipt_sha256",
    "durable_artifact_inventory_sha256",
    "auxiliary_transition_journal_after_inventory_entry_count",
    "auxiliary_transition_journal_after_inventory_head_sha256",
    "reason_code",
    "terminalized_at_utc",
    "body_sha256",
)
_STARTED_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "launch_authorization_sha256",
    "postauthorization_outcome_sha256",
    "started_at_utc",
    "production_runner_rng_or_child_started_before_receipt",
    "body_sha256",
)
_LAUNCH_RECEIPT_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "launch_authorization_sha256",
    "postauthorization_outcome_sha256",
    "started_receipt_sha256",
    "production_schedule_sha256",
    "runner_source_manifest_sha256",
    "runtime_receipt_sha256",
    "shard_map_receipt_sha256",
    "launched_at_utc",
    "body_sha256",
)
_AUXILIARY_RESERVATION_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "schedule_sha256",
    "capacity_schema_sha256",
    "measurement_session_sha256",
    "exclusive_root_charge_measurement_sha256",
    "storage_root_identity_sha256",
    "filesystem_identity_sha256",
    "reservation_method_id",
    "allocation_unit_bytes",
    "artifact_entry_count",
    "artifact_entries",
    "artifact_slot_reserved_bytes",
    "allocated_existing_final_bytes",
    "allocated_future_partial_bytes",
    "unique_nonhold_artifact_allocated_bytes",
    "exclusive_root_charge_baseline_bytes",
    "exclusive_root_charge_current_bytes",
    "disjoint_allocation_and_directory_charge_bytes",
    "hold_relative_path",
    "hold_device_identity_sha256",
    "hold_inode",
    "hold_extent_map_sha256",
    "hold_allocated_bytes",
    "allocation_and_directory_charge_policy_slot_bytes",
    "exclusive_reserved_headroom_bytes",
    "physical_reservation_sum_bytes",
    "enforced_quota_bytes",
    "exclusive_verified",
    "non_sparse_verified",
    "durable_verified",
    "same_root_verified",
    "created_at_utc",
    "body_sha256",
)
_AUXILIARY_RESERVATION_ENTRY_KEYS = (
    "ordinal",
    "artifact_id",
    "final_relative_path",
    "alternate_final_relative_path",
    "reservation_state",
    "partial_relative_path",
    "primary_publication_arm_id",
    "alternate_publication_arm_id",
    "device_identity_sha256",
    "inode",
    "extent_map_sha256",
    "maximum_logical_bytes",
    "reserved_bytes",
    "non_sparse_verified",
    "exclusive_verified",
    "file_fsync_completed_at_utc",
    "directory_fsync_completed_at_utc",
    "entry_sha256",
)
_RESERVATION_MANIFEST_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "freeze_receipt_sha256",
    "schedule_sha256",
    "capacity_schema_sha256",
    "measurement_session_sha256",
    "storage_root_identity_sha256",
    "filesystem_identity_sha256",
    "allocation_unit_bytes",
    "entry_count",
    "entries",
    "total_logical_reserved_bytes",
    "total_allocated_reserved_bytes",
    "created_at_utc",
    "body_sha256",
)
_RESERVATION_ENTRY_KEYS = (
    "ordinal",
    "final_relative_path",
    "partial_relative_path",
    "device_identity_sha256",
    "inode",
    "extent_map_sha256",
    "logical_reserved_bytes",
    "allocated_reserved_bytes",
    "non_sparse_verified",
    "exclusive_verified",
    "file_fsync_completed_at_utc",
    "directory_fsync_completed_at_utc",
    "entry_sha256",
)
_SHARD_INDEX_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "shard_id",
    "shard_record_sha256",
    "request_count",
    "ordered_request_entries",
    "raw_file_sha256",
    "stable_file_sha256",
    "stderr_file_sha256",
    "rng_initial_file_sha256",
    "rng_final_file_sha256",
    "created_at_utc",
    "body_sha256",
)
_SHARD_INDEX_ENTRY_KEYS = (
    "logical_request_ordinal",
    "request_offset",
    "request_length",
    "request_sha256",
    "raw_offset",
    "raw_length",
    "raw_sha256",
    "stable_offset",
    "stable_length",
    "stable_sha256",
    "stderr_offset",
    "stderr_frame_length",
    "stderr_payload_length",
    "stderr_sha256",
    "rng_initial_sha256",
    "rng_final_sha256",
    "row_sha256",
)
_SHARD_RECEIPT_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "shard_id",
    "production_shard_map_receipt_sha256",
    "shard_index_sha256",
    "requests_file_sha256",
    "raw_file_sha256",
    "stable_file_sha256",
    "stderr_file_sha256",
    "rng_initial_file_sha256",
    "rng_final_file_sha256",
    "request_count",
    "terminal_counts",
    "committed_at_utc",
    "body_sha256",
)
_SHA_MANIFEST_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "terminal_state_sha256",
    "auxiliary_transition_journal_after_terminal_entry_count",
    "auxiliary_transition_journal_after_terminal_head_sha256",
    "entry_count",
    "entries",
    "ordered_entries_sha256",
    "created_at_utc",
    "body_sha256",
)
_SHA_MANIFEST_ENTRY_KEYS = ("path", "bytes", "sha256")
_PRETERMINAL_INVENTORY_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "terminal_arm",
    "auxiliary_transition_journal_prefix_entry_count",
    "auxiliary_transition_journal_prefix_head_sha256",
    "entry_count",
    "entries",
    "ordered_entries_sha256",
    "created_at_utc",
    "body_sha256",
)
_PRETERMINAL_INVENTORY_ENTRY_KEYS = (
    "ordinal",
    "path",
    "bytes",
    "sha256",
    "entry_sha256",
)
_EXTERNAL_DIGEST_PREIMAGE_REGISTRY_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "protocol_sha256",
    "machine_manifest_sha256",
    "schema_semantic_sha256",
    "entry_count",
    "entries",
    "ordered_entry_sha256s",
    "ordered_entries_sha256",
    "finalized_at_utc",
    "body_sha256",
)
_EXTERNAL_DIGEST_PREIMAGE_REGISTRY_ENTRY_KEYS = (
    "ordinal",
    "classification_id",
    "target_artifact_id",
    "target_relative_path",
    "target_json_pointer",
    "target_instance_selector_json_ascii",
    "target_artifact_raw_sha256",
    "digest_kind",
    "domain_separator",
    "preimage_encoding",
    "preimage_bytes",
    "preimage_ascii",
    "digest_sha256",
    "entry_sha256",
)

_CLOSED_REFUSAL_CODES = (
    "plan_validation_refusal",
    "provider_reference_binding_refusal",
    "resource_preflight_refusal",
    "runtime_binding_refusal",
    "other_preexecution_refusal",
)
_CLOSED_FAILURE_CODES = (
    "reference_sampling_failure",
    "score_evaluation_failure",
    "quota_certification_failure",
    "float64_normalization_failure",
    "categorical_selection_failure",
    "structural_result_validation_failure",
    "other_execution_failure",
)
_REQUIRED_REVIEWER_ROLES = (
    "protocol-and-provenance-reviewer",
    "runtime-and-durability-reviewer",
    "statistical-power-and-decision-reviewer",
    "independent-recomputation-reviewer",
)
_POWER_PRIMARY_SLOT_IDS = tuple(
    "cp65-power-primary-slot-%02d" % ordinal for ordinal in range(1, 33)
)

_REFERENCED_OUTPUT_IDS = (
    "environment",
    "primary-metrics",
    "secondary-diagnostics",
    "postexecution-independent-recomputation",
    "decisions",
    "deviations",
    "failures",
    "exclusions",
    "reruns",
    "shard-requests",
    "shard-raw-records",
    "shard-stable-traces",
    "shard-stderr-records",
    "shard-rng-initial-states",
    "shard-rng-final-states",
)

# id, retained path template, scope, media kind, exact top-level keys,
# nested-array keysets, body-domain/schema-id, CP64-preserved contract.
_ARTIFACT_DECLARATIONS = (
    (
        "frozen-protocol",
        _GLOBAL_PATHS[0],
        "global",
        "frozen-input-opaque",
        (),
        (),
        "",
        False,
    ),
    (
        "frozen-protocol-sha256",
        _GLOBAL_PATHS[1],
        "global",
        "sha256-text",
        (),
        (),
        "",
        False,
    ),
    (
        "frozen-machine-manifest",
        _GLOBAL_PATHS[2],
        "global",
        "frozen-input-canonical-json",
        (),
        (),
        "",
        False,
    ),
    (
        "source-manifest",
        _GLOBAL_PATHS[3],
        "global",
        "receipt-envelope-canonical-json",
        _SOURCE_MANIFEST_KEYS,
        (("entries", _SOURCE_MANIFEST_ENTRY_KEYS),),
        "cp65-test28-source-manifest-v1",
        False,
    ),
    (
        "dependency-lock",
        _GLOBAL_PATHS[4],
        "global",
        "receipt-envelope-opaque-bytes",
        (),
        (),
        "",
        False,
    ),
    (
        "freeze-receipt",
        _GLOBAL_PATHS[5],
        "global",
        "receipt-envelope-canonical-json",
        _FREEZE_KEYS,
        (),
        "cp65-test28-freeze-receipt-v2",
        False,
    ),
    (
        "power-threshold-receipt",
        _GLOBAL_PATHS[6],
        "global",
        "receipt-envelope-canonical-json",
        _POWER_KEYS,
        (("ordered_slot_thresholds", _THRESHOLD_ROW_KEYS),),
        "cp65-test28-power-threshold-receipt-v2",
        False,
    ),
    (
        "preflight-gate-summary",
        _GLOBAL_PATHS[7],
        "global",
        "receipt-envelope-canonical-json",
        _PREFLIGHT_SUMMARY_KEYS,
        (),
        "cp65-test28-preflight-gate-summary-v2",
        False,
    ),
    (
        "independent-signoff-set",
        _GLOBAL_PATHS[8],
        "global",
        "receipt-envelope-canonical-json",
        _SIGNOFF_SET_KEYS,
        (("ordered_signoffs", _SIGNOFF_ROW_KEYS),),
        "cp65-test28-independent-signoff-set-v1",
        False,
    ),
    (
        "capacity-receipt",
        _GLOBAL_PATHS[9],
        "global",
        "receipt-envelope-canonical-json",
        _CAPACITY_KEYS,
        (),
        "cp65-test28-capacity-receipt-v2",
        False,
    ),
    (
        "auxiliary-metadata-reservation",
        _GLOBAL_PATHS[10],
        "global",
        "receipt-envelope-canonical-json",
        _AUXILIARY_RESERVATION_KEYS,
        (("artifact_entries", _AUXILIARY_RESERVATION_ENTRY_KEYS),),
        "cp65-test28-auxiliary-metadata-reservation-v3",
        False,
    ),
    (
        "reservation-manifest",
        _GLOBAL_PATHS[11],
        "global",
        "receipt-envelope-canonical-json",
        _RESERVATION_MANIFEST_KEYS,
        (("entries", _RESERVATION_ENTRY_KEYS),),
        "cp65-test28-reservation-manifest-v2",
        False,
    ),
    (
        "production-runtime-receipt",
        _GLOBAL_PATHS[12],
        "global",
        "receipt-envelope-canonical-json",
        _RUNTIME_KEYS,
        (),
        "cp64-test28-production-runtime-receipt-v1",
        True,
    ),
    (
        "external-seed-acquisition-start-receipt",
        _GLOBAL_PATHS[13],
        "global",
        "receipt-envelope-canonical-json",
        _ACQUISITION_START_KEYS,
        (),
        "cp64-test28-external-seed-acquisition-start-receipt-v1",
        True,
    ),
    (
        "external-seed-acquisition-journal",
        _GLOBAL_PATHS[14],
        "global",
        "binary-journal",
        (),
        (),
        "cp64-external-seed-acquisition-journal-entry-v1",
        True,
    ),
    (
        "external-seed-source-receipt",
        _GLOBAL_PATHS[15],
        "global",
        "receipt-envelope-canonical-json",
        _EXTERNAL_SEED_SOURCE_KEYS,
        (),
        "cp65-test28-external-seed-source-receipt-v2",
        False,
    ),
    (
        "seed-capsule-body",
        _GLOBAL_PATHS[16],
        "global",
        "receipt-envelope-canonical-json",
        _SEED_CAPSULE_KEYS,
        (),
        "cp63-test28-seed-capsule-v1",
        True,
    ),
    (
        "production-shard-map-receipt",
        _GLOBAL_PATHS[17],
        "global",
        "receipt-envelope-canonical-json",
        _SHARD_MAP_KEYS,
        (("shards", _SHARD_ROW_KEYS),),
        "cp64-test28-production-shard-map-receipt-v1",
        True,
    ),
    (
        "durability-receipt",
        _GLOBAL_PATHS[18],
        "global",
        "receipt-envelope-canonical-json",
        _DURABILITY_KEYS,
        (),
        "cp64-test28-durability-receipt-v1",
        True,
    ),
    (
        "preauthorization-outcome",
        _GLOBAL_PATHS[19],
        "global",
        "receipt-envelope-canonical-json",
        _PREAUTH_OUTCOME_KEYS,
        (),
        "cp64-test28-preauthorization-outcome-v1",
        True,
    ),
    (
        "launch-authorization",
        _GLOBAL_PATHS[20],
        "global",
        "receipt-envelope-canonical-json",
        _LAUNCH_KEYS,
        (),
        "cp65-test28-launch-authorization-receipt-v2",
        False,
    ),
    (
        "postauthorization-outcome",
        _GLOBAL_PATHS[21],
        "global",
        "receipt-envelope-canonical-json",
        _POSTAUTH_OUTCOME_KEYS,
        (),
        "cp64-test28-postauthorization-outcome-v1",
        True,
    ),
    (
        "started-receipt",
        _GLOBAL_PATHS[22],
        "global",
        "receipt-envelope-canonical-json",
        _STARTED_KEYS,
        (),
        "cp65-test28-started-receipt-v1",
        False,
    ),
    (
        "environment",
        _GLOBAL_PATHS[23],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "launch-receipt",
        _GLOBAL_PATHS[24],
        "global",
        "receipt-envelope-canonical-json",
        _LAUNCH_RECEIPT_KEYS,
        (),
        "cp65-test28-launch-receipt-v1",
        False,
    ),
    (
        "primary-metrics",
        _GLOBAL_PATHS[25],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "secondary-diagnostics",
        _GLOBAL_PATHS[26],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "postexecution-independent-recomputation",
        _GLOBAL_PATHS[27],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "decisions",
        _GLOBAL_PATHS[28],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "deviations",
        _GLOBAL_PATHS[29],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "failures",
        _GLOBAL_PATHS[30],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "exclusions",
        _GLOBAL_PATHS[31],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "reruns",
        _GLOBAL_PATHS[32],
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "terminal-state",
        _GLOBAL_PATHS[33],
        "global",
        "receipt-envelope-canonical-json",
        _TERMINAL_KEYS,
        (),
        "cp65-test28-terminal-state-v1",
        False,
    ),
    (
        "sha256-manifest",
        _GLOBAL_PATHS[34],
        "global",
        "receipt-envelope-canonical-json",
        _SHA_MANIFEST_KEYS,
        (("entries", _SHA_MANIFEST_ENTRY_KEYS),),
        "cp65-test28-sha256-manifest-v1",
        False,
    ),
    (
        "committed-marker",
        _GLOBAL_PATHS[35],
        "global",
        "receipt-envelope-canonical-json",
        _COMMITTED_KEYS,
        (),
        "cp65-test28-committed-marker-v3",
        False,
    ),
    (
        "launch-authority-public-key",
        _GLOBAL_PATHS[36],
        "global",
        "receipt-envelope-canonical-json",
        _PUBLIC_KEY_KEYS,
        (),
        "cp65-test28-launch-authority-public-key-v1",
        False,
    ),
    (
        "dependency-lock-match-receipt",
        _GLOBAL_PATHS[37],
        "global",
        "receipt-envelope-canonical-json",
        _DEPENDENCY_MATCH_KEYS,
        (),
        "cp65-test28-dependency-lock-match-receipt-v2",
        False,
    ),
    (
        "seed-source-custody-artifact",
        _GLOBAL_PATHS[38],
        "global",
        "receipt-envelope-canonical-json",
        _SOURCE_CUSTODY_KEYS,
        (),
        "cp65-test28-seed-source-custody-artifact-v1",
        False,
    ),
    (
        "seed-capsule-sequence-crosscheck-receipt",
        _GLOBAL_PATHS[39],
        "global",
        "receipt-envelope-canonical-json",
        _CAPSULE_CROSSCHECK_KEYS,
        (),
        "cp65-test28-seed-capsule-sequence-crosscheck-receipt-v1",
        False,
    ),
    (
        "production-schedule",
        _GLOBAL_PATHS[40],
        "global",
        "receipt-envelope-canonical-json",
        _SCHEDULE_KEYS,
        (("requests", _SCHEDULE_REQUEST_KEYS),),
        "cp65-test28-production-schedule-v1",
        False,
    ),
    (
        "production-runner-supervisor-qualification-receipt",
        _GLOBAL_PATHS[41],
        "global",
        "receipt-envelope-canonical-json",
        _RUNNER_QUALIFICATION_KEYS,
        (),
        "cp65-test28-production-runner-supervisor-qualification-receipt-v1",
        False,
    ),
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        _GLOBAL_PATHS[42],
        "global",
        "receipt-envelope-canonical-json",
        _CLASSIFIER_QUALIFICATION_KEYS,
        (),
        "cp65-test28-closed-refusal-failure-classifier-qualification-receipt-v1",
        False,
    ),
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        _GLOBAL_PATHS[43],
        "global",
        "receipt-envelope-canonical-json",
        _INDEPENDENT_554_KEYS,
        (),
        "cp65-test28-independent-554-estimate-interval-decision-path-qualification-receipt-v1",
        False,
    ),
    (
        "independent-full-32768-recomputation-qualification-receipt",
        _GLOBAL_PATHS[44],
        "global",
        "receipt-envelope-canonical-json",
        _FULL_QUALIFICATION_KEYS,
        (),
        "cp65-test28-independent-full-32768-recomputation-qualification-receipt-v1",
        False,
    ),
    (
        "independent-reviewer-public-key-set",
        _GLOBAL_PATHS[45],
        "global",
        "receipt-envelope-canonical-json",
        _REVIEWER_KEY_SET_KEYS,
        (("ordered_keys", _REVIEWER_KEY_ROW_KEYS),),
        "cp65-test28-independent-reviewer-public-key-set-v1",
        False,
    ),
    (
        "seed-source-authority-public-key",
        _GLOBAL_PATHS[46],
        "global",
        "receipt-envelope-canonical-json",
        _SEED_AUTHORITY_KEY_KEYS,
        (),
        "cp65-test28-seed-source-authority-public-key-v1",
        False,
    ),
    (
        "seed-source-authority-attestation",
        _GLOBAL_PATHS[47],
        "global",
        "receipt-envelope-canonical-json",
        _SEED_AUTHORITY_ATTESTATION_KEYS,
        (),
        "cp65-test28-seed-source-authority-attestation-v1",
        False,
    ),
    (
        "frozen-source-fixture-materialization",
        _GLOBAL_PATHS[48],
        "global",
        "frozen-input-binary-archive",
        (),
        (),
        "cp65-test28-frozen-source-fixture-materialization-v1",
        False,
    ),
    (
        "production-schema-preimage-validator-bundle",
        _GLOBAL_PATHS[49],
        "global",
        "frozen-input-canonical-json",
        (),
        (),
        "",
        False,
    ),
    (
        "power-review-signoff",
        _GLOBAL_PATHS[50],
        "global",
        "receipt-envelope-canonical-json",
        _POWER_REVIEW_SIGNOFF_KEYS,
        (),
        "cp65-test28-power-review-signoff-v1",
        False,
    ),
    (
        "preterminal-durable-artifact-inventory",
        _GLOBAL_PATHS[51],
        "global",
        "receipt-envelope-canonical-json",
        _PRETERMINAL_INVENTORY_KEYS,
        (("entries", _PRETERMINAL_INVENTORY_ENTRY_KEYS),),
        "cp65-test28-preterminal-durable-artifact-inventory-v1",
        False,
    ),
    (
        "external-digest-preimage-registry",
        _GLOBAL_PATHS[52],
        "global",
        "receipt-envelope-canonical-json",
        _EXTERNAL_DIGEST_PREIMAGE_REGISTRY_KEYS,
        (("entries", _EXTERNAL_DIGEST_PREIMAGE_REGISTRY_ENTRY_KEYS),),
        "cp65-test28-external-digest-preimage-registry-v1",
        False,
    ),
    (
        "auxiliary-reservation-transition-journal",
        _GLOBAL_PATHS[53],
        "global",
        "binary-transition-journal",
        (),
        (),
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        False,
    ),
    (
        "shard-requests",
        _PER_SHARD_PATHS[0],
        "per-shard",
        "referenced-predecessor-jsonl",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-raw-records",
        _PER_SHARD_PATHS[1],
        "per-shard",
        "referenced-predecessor-jsonl",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-stable-traces",
        _PER_SHARD_PATHS[2],
        "per-shard",
        "referenced-predecessor-jsonl",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-stderr-records",
        _PER_SHARD_PATHS[3],
        "per-shard",
        "referenced-predecessor-binary-frames",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-rng-initial-states",
        _PER_SHARD_PATHS[4],
        "per-shard",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-rng-final-states",
        _PER_SHARD_PATHS[5],
        "per-shard",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-index",
        _PER_SHARD_PATHS[6],
        "per-shard",
        "receipt-envelope-canonical-json",
        _SHARD_INDEX_KEYS,
        (("ordered_request_entries", _SHARD_INDEX_ENTRY_KEYS),),
        "cp65-test28-shard-index-v1",
        False,
    ),
    (
        "shard-receipt",
        _PER_SHARD_PATHS[7],
        "per-shard",
        "receipt-envelope-canonical-json",
        _SHARD_RECEIPT_KEYS,
        (("terminal_counts", _TERMINAL_COUNT_KEYS),),
        "cp65-test28-shard-receipt-v1",
        False,
    ),
    (
        "partial-seed-acquisition-terminal-receipt",
        _CONDITIONAL_PATHS[0],
        "conditional-global",
        "receipt-envelope-canonical-json",
        _PARTIAL_ACQUISITION_KEYS,
        (),
        "cp64-test28-partial-acquisition-terminal-receipt-v1",
        True,
    ),
    (
        "rejected-launch-authorization-candidate",
        _CONDITIONAL_PATHS[1],
        "conditional-global",
        "receipt-envelope-canonical-json",
        _LAUNCH_KEYS,
        (),
        "cp65-test28-launch-authorization-receipt-v2",
        False,
    ),
)

_ARTIFACT_BY_ID = {row[0]: row for row in _ARTIFACT_DECLARATIONS}
_FROZEN_OR_BINARY_CUSTODY_IDS = (
    "frozen-protocol",
    "frozen-protocol-sha256",
    "frozen-machine-manifest",
    "dependency-lock",
    "external-seed-acquisition-journal",
    "frozen-source-fixture-materialization",
    "production-schema-preimage-validator-bundle",
    "auxiliary-reservation-transition-journal",
)
_RECEIPT_ENVELOPE_IDS = tuple(
    row[0]
    for row in _ARTIFACT_DECLARATIONS
    if row[0] not in _REFERENCED_OUTPUT_IDS
    and row[0] not in _FROZEN_OR_BINARY_CUSTODY_IDS
)

_GATE_IDS = (
    "v15-protocol-sidecar-and-machine-manifest-frozen",
    "complete-production-source-manifest",
    "exact-dependency-lock-matched",
    "full-production-runtime-lock-recomputed-and-matched",
    "external-seed-source-receipt-and-authority",
    "external-seed-capsule-sequence-crosscheck",
    "production-request-schedule-materialized",
    "capacity-receipt-meets-usable-and-quota-floor",
    "durable-writer-qualified",
    "production-shard-map-selected-and-materialized",
    "production-runner-supervisor-qualified",
    "closed-refusal-failure-classifier-qualified",
    "independent-full-32768-recomputation-qualified",
    "independent-554-estimate-interval-decision-path-qualified",
    "power-review-and-32-primary-thresholds-frozen",
    "independent-review-signoffs-present",
    "explicit-launch-authorization-present",
)
_GATE_EVIDENCE_NODES = (
    "freeze-receipt",
    "source-manifest",
    "dependency-lock-match-receipt",
    "production-runtime-receipt",
    "external-seed-source-receipt",
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
    "capacity-receipt",
    "durability-receipt",
    "production-shard-map-receipt",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-full-32768-recomputation-receipt",
    "independent-554-estimate-interval-decision-path-receipt",
    "power-threshold-receipt",
    "independent-signoff-set",
    "launch-authorization",
)
_GATE_DAG_NODES = (
    "source-manifest",
    "dependency-lock-match-receipt",
    "power-threshold-receipt",
    "freeze-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-source-receipt",
    "seed-capsule-body",
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
    "production-runtime-receipt",
    "capacity-receipt",
    "durability-receipt",
    "production-shard-map-receipt",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-full-32768-recomputation-receipt",
    "independent-554-estimate-interval-decision-path-receipt",
    "preflight-gate-summary",
    "independent-signoff-set",
    "launch-authorization",
)
_GATE_DAG_EDGES = (
    ("source-manifest", "freeze-receipt"),
    ("source-manifest", "production-runtime-receipt"),
    ("source-manifest", "launch-authorization"),
    ("power-threshold-receipt", "freeze-receipt"),
    ("power-threshold-receipt", "launch-authorization"),
    ("freeze-receipt", "external-seed-acquisition-start-receipt"),
    ("freeze-receipt", "external-seed-source-receipt"),
    ("freeze-receipt", "production-runtime-receipt"),
    ("freeze-receipt", "launch-authorization"),
    ("external-seed-acquisition-start-receipt", "external-seed-source-receipt"),
    ("external-seed-source-receipt", "seed-capsule-body"),
    ("external-seed-source-receipt", "seed-capsule-sequence-crosscheck-receipt"),
    ("external-seed-source-receipt", "launch-authorization"),
    ("seed-capsule-body", "production-schedule"),
    ("seed-capsule-body", "seed-capsule-sequence-crosscheck-receipt"),
    ("seed-capsule-body", "launch-authorization"),
    ("production-schedule", "capacity-receipt"),
    ("production-schedule", "production-shard-map-receipt"),
    ("production-schedule", "launch-authorization"),
    ("production-runtime-receipt", "launch-authorization"),
    ("capacity-receipt", "durability-receipt"),
    ("capacity-receipt", "production-shard-map-receipt"),
    ("capacity-receipt", "launch-authorization"),
    ("durability-receipt", "production-shard-map-receipt"),
    ("durability-receipt", "launch-authorization"),
    ("production-shard-map-receipt", "launch-authorization"),
    ("preflight-gate-summary", "independent-signoff-set"),
    ("preflight-gate-summary", "launch-authorization"),
    ("independent-signoff-set", "launch-authorization"),
    ("freeze-receipt", "preflight-gate-summary"),
    ("source-manifest", "preflight-gate-summary"),
    ("dependency-lock-match-receipt", "preflight-gate-summary"),
    ("production-runtime-receipt", "preflight-gate-summary"),
    ("external-seed-source-receipt", "preflight-gate-summary"),
    ("seed-capsule-sequence-crosscheck-receipt", "preflight-gate-summary"),
    ("production-schedule", "preflight-gate-summary"),
    ("capacity-receipt", "preflight-gate-summary"),
    ("durability-receipt", "preflight-gate-summary"),
    ("production-shard-map-receipt", "preflight-gate-summary"),
    ("production-runner-supervisor-qualification-receipt", "preflight-gate-summary"),
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "preflight-gate-summary",
    ),
    ("independent-full-32768-recomputation-receipt", "preflight-gate-summary"),
    (
        "independent-554-estimate-interval-decision-path-receipt",
        "preflight-gate-summary",
    ),
    ("power-threshold-receipt", "preflight-gate-summary"),
)


def _gate_edge_target_pointers() -> Tuple[str, ...]:
    direct = {
        ("source-manifest", "freeze-receipt"): "/bound_files_sha256",
        ("source-manifest", "production-runtime-receipt"): "/source_manifest_sha256",
        ("source-manifest", "launch-authorization"): "/source_manifest_sha256",
        (
            "power-threshold-receipt",
            "freeze-receipt",
        ): "/power_threshold_receipt_sha256",
        (
            "power-threshold-receipt",
            "launch-authorization",
        ): "/power_threshold_receipt_sha256",
        (
            "external-seed-acquisition-start-receipt",
            "external-seed-source-receipt",
        ): "/acquisition_start_receipt_sha256",
        ("external-seed-source-receipt", "seed-capsule-body"): "/source_receipt_sha256",
        (
            "external-seed-source-receipt",
            "seed-capsule-sequence-crosscheck-receipt",
        ): "/source_receipt_sha256",
        (
            "external-seed-source-receipt",
            "launch-authorization",
        ): "/seed_source_receipt_sha256",
        ("seed-capsule-body", "production-schedule"): "/seed_capsule_body_sha256",
        (
            "seed-capsule-body",
            "seed-capsule-sequence-crosscheck-receipt",
        ): "/seed_capsule_body_sha256",
        ("seed-capsule-body", "launch-authorization"): "/seed_capsule_body_sha256",
        ("production-schedule", "capacity-receipt"): "/schedule_sha256",
        ("production-schedule", "production-shard-map-receipt"): "/schedule_sha256",
        ("production-schedule", "launch-authorization"): "/schedule_sha256",
        (
            "production-runtime-receipt",
            "launch-authorization",
        ): "/production_runtime_receipt_sha256",
        ("capacity-receipt", "durability-receipt"): "/capacity_receipt_sha256",
        (
            "capacity-receipt",
            "production-shard-map-receipt",
        ): "/capacity_receipt_sha256",
        ("capacity-receipt", "launch-authorization"): "/capacity_receipt_sha256",
        (
            "durability-receipt",
            "production-shard-map-receipt",
        ): "/durability_receipt_sha256",
        ("durability-receipt", "launch-authorization"): "/durability_receipt_sha256",
        (
            "production-shard-map-receipt",
            "launch-authorization",
        ): "/production_shard_map_receipt_sha256",
        (
            "preflight-gate-summary",
            "independent-signoff-set",
        ): "/preflight_gate_summary_sha256",
        (
            "preflight-gate-summary",
            "launch-authorization",
        ): "/preflight_gate_summary_sha256",
        (
            "independent-signoff-set",
            "launch-authorization",
        ): "/independent_signoff_sha256",
    }
    pointers = []
    summary_sources = _GATE_EVIDENCE_NODES[:15]
    for edge in _GATE_DAG_EDGES:
        if edge[1] == "preflight-gate-summary":
            pointers.append(
                "/ordered_evidence_receipt_sha256s/%d" % summary_sources.index(edge[0])
            )
        elif edge[0] == "freeze-receipt":
            pointers.append("/freeze_receipt_sha256")
        else:
            pointers.append(direct[edge])
    return tuple(pointers)


_GATE_DAG_EDGE_TARGET_POINTERS = _gate_edge_target_pointers()


def _gate_edge_source_contracts_and_kinds() -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    contract_ids = []
    kinds = []
    for (source, target), pointer in zip(
        _GATE_DAG_EDGES, _GATE_DAG_EDGE_TARGET_POINTERS
    ):
        artifact_id = {
            "independent-full-32768-recomputation-receipt": "independent-full-32768-recomputation-qualification-receipt",
            "independent-554-estimate-interval-decision-path-receipt": "independent-554-estimate-interval-decision-path-qualification-receipt",
        }.get(source, source)
        body_kind = (
            source == "seed-capsule-body" and "seed_capsule_body" in pointer
        ) or (
            source == "external-seed-acquisition-start-receipt"
            and pointer == "/acquisition_start_receipt_sha256"
        )
        contract_ids.append(
            artifact_id + (":body-sha256" if body_kind else ":raw-sha256")
        )
        kinds.append("body-domain-sha256" if body_kind else "plain-raw-file-sha256")
    return tuple(contract_ids), tuple(kinds)


(
    _GATE_DAG_EDGE_SOURCE_CONTRACT_IDS,
    _GATE_DAG_EDGE_DIGEST_KINDS,
) = _gate_edge_source_contracts_and_kinds()

_GATE_REQUIRED_ARTIFACT_IDS = (
    (
        "frozen-protocol",
        "frozen-protocol-sha256",
        "frozen-machine-manifest",
        "production-schema-preimage-validator-bundle",
        "frozen-source-fixture-materialization",
        "source-manifest",
        "dependency-lock",
        "power-review-signoff",
        "power-threshold-receipt",
        "launch-authority-public-key",
        "independent-reviewer-public-key-set",
        "seed-source-authority-public-key",
        "freeze-receipt",
    ),
    (
        "frozen-protocol",
        "frozen-machine-manifest",
        "production-schema-preimage-validator-bundle",
        "frozen-source-fixture-materialization",
        "source-manifest",
    ),
    ("freeze-receipt", "dependency-lock", "dependency-lock-match-receipt"),
    (
        "freeze-receipt",
        "source-manifest",
        "dependency-lock",
        "dependency-lock-match-receipt",
        "production-runtime-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-acquisition-journal",
        "seed-source-custody-artifact",
        "seed-source-authority-public-key",
        "seed-source-authority-attestation",
        "external-seed-source-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-acquisition-journal",
        "seed-source-custody-artifact",
        "seed-source-authority-public-key",
        "seed-source-authority-attestation",
        "external-seed-source-receipt",
        "seed-capsule-body",
        "seed-capsule-sequence-crosscheck-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-source-receipt",
        "seed-capsule-body",
        "production-runtime-receipt",
        "production-schedule",
    ),
    (
        "freeze-receipt",
        "production-schema-preimage-validator-bundle",
        "production-schedule",
        "auxiliary-metadata-reservation",
        "reservation-manifest",
        "capacity-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "capacity-receipt",
        "auxiliary-metadata-reservation",
        "reservation-manifest",
        "durability-receipt",
    ),
    (
        "freeze-receipt",
        "seed-capsule-body",
        "production-schedule",
        "capacity-receipt",
        "durability-receipt",
        "reservation-manifest",
        "production-shard-map-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-runtime-receipt",
        "production-runner-supervisor-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-runner-supervisor-qualification-receipt",
        "closed-refusal-failure-classifier-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-schedule",
        "independent-full-32768-recomputation-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-schedule",
        "independent-554-estimate-interval-decision-path-qualification-receipt",
    ),
    (
        "frozen-protocol",
        "frozen-machine-manifest",
        "independent-reviewer-public-key-set",
        "power-review-signoff",
        "power-threshold-receipt",
    ),
    (
        "freeze-receipt",
        "preflight-gate-summary",
        "external-digest-preimage-registry",
        "independent-reviewer-public-key-set",
        "independent-signoff-set",
    ),
    (),
)

_REGISTRY_CUT_DURABLE_ARTIFACT_IDS = frozenset(
    artifact_id for group in _GATE_REQUIRED_ARTIFACT_IDS[:15] for artifact_id in group
)


def _authorization_required_artifacts() -> Tuple[str, ...]:
    ordered = []
    for group in _GATE_REQUIRED_ARTIFACT_IDS[:16]:
        for artifact_id in group:
            if artifact_id not in ordered:
                ordered.append(artifact_id)
    for artifact_id in (
        "launch-authority-public-key",
        "preauthorization-outcome",
        "launch-authorization",
    ):
        if artifact_id not in ordered:
            ordered.append(artifact_id)
    return tuple(ordered)


_BOOLEAN_KEYS = frozenset(
    {
        "match_verified",
        "sequence_equal",
        "all_cases_passed",
        "all_closed_arms_reachable",
        "unknown_codes_rejected",
        "all_554_estimands_supported",
        "all_required_roles_present",
        "all_decisions_approve",
        "all_signatures_mathematically_valid_under_declared_keys",
        "repetition_blind_recomputation_verified",
        "production_runner_rng_or_child_started_before_receipt",
        "non_sparse_allocation_verified",
        "reservation_same_filesystem_verified",
        "reservation_exclusive_verified",
        "reservation_durable_verified",
        "auxiliary_metadata_reservation_exclusive_verified",
        "auxiliary_metadata_non_sparse_allocation_verified",
        "auxiliary_metadata_reserved_quota_verified",
        "auxiliary_metadata_reservation_durable_verified",
        "auxiliary_metadata_reservation_same_storage_root_verified",
        "destination_and_auxiliary_reservation_no_double_count_verified",
        "atomic_rename_supported",
        "file_fsync_supported",
        "directory_fsync_supported",
        "allocation_and_directory_charge_within_policy",
        "atomic_rename_verified",
        "file_fsync_verified",
        "directory_fsync_verified",
        "exclusive_create_verified",
        "no_symlink_verified",
        "no_hardlink_verified",
        "no_overwrite_verified",
        "exclusive_verified",
        "non_sparse_verified",
        "durable_verified",
        "same_root_verified",
        "topup_redraw_reselection_permitted",
        "hold_absence_verified",
        "definition_only",
        "production_execution_authorized",
    }
)
_ARRAY_KEYS = frozenset(
    {
        "artifact_entries",
        "entries",
        "ordered_slot_thresholds",
        "ordered_slot_threshold_row_sha256s",
        "ordered_entry_sha256s",
        "covered_gate_ids",
        "covered_gate_states",
        "covered_evidence_node_ids",
        "ordered_evidence_receipt_sha256s",
        "required_reviewer_roles",
        "ordered_signoffs",
        "reviewed_artifact_sha256s",
        "seed_ordinals",
        "ordered_seed_values",
        "ordered_partial_seed_values",
        "shards",
        "requests",
        "ordered_request_record_sha256s",
        "closed_refusal_codes",
        "closed_failure_codes",
        "per_file_reservation_manifest_entry_sha256s",
        "ordered_request_entries",
        "ordered_keys",
        "ordered_public_key_identity_sha256s",
    }
)
_INTEGER_EXACT = {
    ("seed-capsule-body", "seed_count"): 2_048,
    ("external-seed-source-receipt", "seed_count"): 2_048,
    ("external-seed-source-receipt", "acquisition_journal_entry_count"): 2_048,
    ("partial-seed-acquisition-terminal-receipt", "expected_seed_count"): 2_048,
    ("seed-source-authority-attestation", "acquisition_journal_entry_count"): 2_048,
    ("seed-capsule-sequence-crosscheck-receipt", "seed_count"): 2_048,
    ("production-schedule", "request_count"): 32_768,
    ("production-shard-map-receipt", "shard_count"): 32,
    ("production-shard-map-receipt", "logical_request_count"): 1_024,
    ("shard-index", "request_count"): 1_024,
    ("shard-receipt", "request_count"): 1_024,
    ("power-threshold-receipt", "primary_slot_count"): 32,
    ("power-review-signoff", "primary_slot_count"): 32,
    ("power-threshold-receipt", "design_minimum_selected_count"): 1_040,
    ("capacity-receipt", "shard_count"): 32,
    ("reservation-manifest", "entry_count"): 128,
    ("independent-signoff-set", "signoff_count"): 4,
    ("independent-reviewer-public-key-set", "key_count"): 4,
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "expected_request_count_supported",
    ): 32_768,
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "expected_estimand_count_supported",
    ): 554,
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "expected_estimand_count_supported",
    ): 554,
    ("launch-authority-public-key", "public_exponent"): 65_537,
    ("seed-source-authority-public-key", "public_exponent"): 65_537,
    ("independent-reviewer-public-key-set", "public_exponent"): 65_537,
    ("auxiliary-metadata-reservation", "required_bytes"): 34_359_738_368,
    ("capacity-receipt", "destination_reservation_required_bytes"): 1_099_511_627_776,
    (
        "capacity-receipt",
        "auxiliary_metadata_reservation_required_bytes",
    ): 34_359_738_368,
    (
        "capacity-receipt",
        "combined_available_and_quota_required_before_reservation_bytes",
    ): 1_133_871_366_144,
    (
        "capacity-receipt",
        "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
    ): 34_359_738_368,
    ("capacity-receipt", "maximum_auxiliary_artifact_logical_bytes"): 21_845_344_321,
    ("capacity-receipt", "maximum_auxiliary_reserved_bytes"): 23_286_841_344,
    (
        "capacity-receipt",
        "allocation_and_directory_charge_policy_slot_bytes",
    ): 1_073_741_824,
    ("auxiliary-metadata-reservation", "artifact_entry_count"): 183,
    ("auxiliary-metadata-reservation", "artifact_slot_reserved_bytes"): 22_213_099_520,
    (
        "auxiliary-metadata-reservation",
        "allocation_and_directory_charge_policy_slot_bytes",
    ): 1_073_741_824,
    (
        "auxiliary-metadata-reservation",
        "exclusive_reserved_headroom_bytes",
    ): 11_072_897_024,
}
_INTEGER_INTERVALS = {
    (
        "preterminal-durable-artifact-inventory",
        "/auxiliary_transition_journal_prefix_entry_count",
    ): (0, 251),
    (
        "terminal-state",
        "/auxiliary_transition_journal_after_inventory_entry_count",
    ): (1, 252),
    (
        "sha256-manifest",
        "/auxiliary_transition_journal_after_terminal_entry_count",
    ): (2, 253),
    (
        "committed-marker",
        "/auxiliary_reservation_transition_journal_final_entry_count",
    ): (4, 255),
    ("preterminal-durable-artifact-inventory", "/entry_count"): (
        1,
        _MAX_TERMINAL_PUBLICATION_ENTRIES,
    ),
    ("sha256-manifest", "/entry_count"): (
        1,
        _MAX_TERMINAL_PUBLICATION_ENTRIES,
    ),
    ("external-digest-preimage-registry", "/entry_count"): (0, 4_096),
}
_ARRAY_LENGTH_EXACT = {
    ("seed-capsule-body", "seed_ordinals"): 2_048,
    ("seed-capsule-body", "ordered_seed_values"): 2_048,
    ("production-schedule", "requests"): 32_768,
    ("production-schedule", "ordered_request_record_sha256s"): 32_768,
    ("production-shard-map-receipt", "shards"): 32,
    ("power-threshold-receipt", "ordered_slot_thresholds"): 32,
    ("power-threshold-receipt", "ordered_slot_threshold_row_sha256s"): 32,
    ("preflight-gate-summary", "covered_gate_ids"): 15,
    ("preflight-gate-summary", "covered_gate_states"): 15,
    ("preflight-gate-summary", "covered_evidence_node_ids"): 15,
    ("preflight-gate-summary", "ordered_evidence_receipt_sha256s"): 15,
    ("independent-signoff-set", "required_reviewer_roles"): 4,
    ("independent-signoff-set", "ordered_signoffs"): 4,
    ("independent-reviewer-public-key-set", "required_reviewer_roles"): 4,
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "closed_refusal_codes",
    ): 5,
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "closed_failure_codes",
    ): 7,
    ("shard-index", "ordered_request_entries"): 1_024,
    ("auxiliary-metadata-reservation", "artifact_entries"): 183,
    ("reservation-manifest", "entries"): 128,
    (
        "production-shard-map-receipt",
        "per_file_reservation_manifest_entry_sha256s",
    ): 4,
    ("independent-reviewer-public-key-set", "ordered_keys"): 4,
    (
        "independent-reviewer-public-key-set",
        "ordered_public_key_identity_sha256s",
    ): 4,
    ("power-review-signoff", "ordered_slot_threshold_row_sha256s"): 32,
}

_DESTINATION_IDS = (
    "shard-requests",
    "shard-raw-records",
    "shard-stable-traces",
    "shard-stderr-records",
)


def _build_auxiliary_bounds() -> Tuple[CP65AuxiliaryArtifactBoundV1, ...]:
    result = []
    destination_reserved = {
        "shard-requests": 67_109_888,
        "shard-stable-traces": 8_589_935_616,
        "shard-stderr-records": 1_073_750_016,
        "shard-raw-records": 24_628_942_848,
    }
    reserved_overrides = {
        "reservation-manifest": 268_435_456,
        "primary-metrics": 268_435_456,
        "secondary-diagnostics": 536_870_912,
        "postexecution-independent-recomputation": 536_870_912,
        "external-digest-preimage-registry": 67_108_864,
        "frozen-source-fixture-materialization": 134_217_728,
        "auxiliary-reservation-transition-journal": 65_536,
        "shard-rng-initial-states": 134_217_728,
        "shard-rng-final-states": 134_217_728,
        "shard-index": 134_217_728,
        "shard-receipt": 134_217_728,
    }
    for (
        artifact_id,
        _path,
        scope,
        _media,
        _keys,
        _nested,
        _domain,
        _preserved,
    ) in _ARTIFACT_DECLARATIONS:
        count = 32 if scope == "per-shard" else 1
        reserved = destination_reserved.get(
            artifact_id, reserved_overrides.get(artifact_id, 67_108_864)
        )
        authorization_aliases = (
            "launch-authorization",
            "rejected-launch-authorization-candidate",
        )
        shares_authorization_slot = artifact_id in authorization_aliases
        result.append(
            cast(
                CP65AuxiliaryArtifactBoundV1,
                _record(
                    CP65AuxiliaryArtifactBoundV1,
                    {
                        "schema_version": CP65_TEST28_SCHEMA_VERSION,
                        "bound_id": "aux-bound:" + artifact_id,
                        "artifact_id": artifact_id,
                        "physical_slot_group_id": (
                            "auxiliary-slot:launch-authorization-candidate"
                            if shares_authorization_slot
                            else "auxiliary-slot:" + artifact_id
                        ),
                        "mutually_exclusive_artifact_ids": (
                            authorization_aliases
                            if shares_authorization_slot
                            else (artifact_id,)
                        ),
                        "maximum_instance_count": count,
                        "maximum_logical_bytes_per_instance": _artifact_maximum_bytes(
                            artifact_id
                        ),
                        "maximum_reserved_bytes_per_instance": reserved,
                        "maximum_total_reserved_bytes": count * reserved,
                        "simultaneous_presence_rule_id": (
                            "mutual-exclusion:launch-or-rejected-authorization"
                            if shares_authorization_slot
                            else "presence:" + artifact_id
                        ),
                        "reservation_partition_id": "destination-reservation"
                        if artifact_id in _DESTINATION_IDS
                        else "exclusive-auxiliary-metadata-reservation",
                        "destination_reservation_excluded": artifact_id
                        not in _DESTINATION_IDS,
                    },
                ),
            )
        )
    result.append(
        cast(
            CP65AuxiliaryArtifactBoundV1,
            _record(
                CP65AuxiliaryArtifactBoundV1,
                {
                    "schema_version": CP65_TEST28_SCHEMA_VERSION,
                    "bound_id": "allocation-and-directory-charge-policy-slot",
                    "artifact_id": "__allocation_and_directory_charge_policy_slot__",
                    "physical_slot_group_id": "auxiliary-slot:allocation-and-directory-charge-policy",
                    "mutually_exclusive_artifact_ids": (
                        "__allocation_and_directory_charge_policy_slot__",
                    ),
                    "maximum_instance_count": 1,
                    "maximum_logical_bytes_per_instance": 0,
                    "maximum_reserved_bytes_per_instance": 1_073_741_824,
                    "maximum_total_reserved_bytes": 1_073_741_824,
                    "simultaneous_presence_rule_id": "always-reserved-with-auxiliary-partition",
                    "reservation_partition_id": "exclusive-auxiliary-metadata-reservation",
                    "destination_reservation_excluded": False,
                },
            ),
        )
    )
    return tuple(result)


def _build_auxiliary_size_proof(
    bounds: Tuple[CP65AuxiliaryArtifactBoundV1, ...],
) -> CP65AuxiliarySizeProofV1:
    by_artifact = {bound.artifact_id: bound for bound in bounds}
    if len(by_artifact) != len(bounds):
        raise RuntimeError("duplicate CP65 auxiliary artifact bound")
    grouped = {}
    for bound in bounds:
        members = bound.mutually_exclusive_artifact_ids
        if bound.artifact_id not in members or len(members) != len(set(members)):
            raise RuntimeError("CP65 auxiliary physical-slot membership differs")
        grouped.setdefault(bound.physical_slot_group_id, []).append(bound)
    for rows in grouped.values():
        expected_members = tuple(row.artifact_id for row in rows)
        for row in rows:
            if set(row.mutually_exclusive_artifact_ids) != set(expected_members):
                raise RuntimeError("CP65 auxiliary physical-slot group differs")
            if (
                row.maximum_instance_count,
                row.maximum_logical_bytes_per_instance,
                row.maximum_reserved_bytes_per_instance,
            ) != (
                rows[0].maximum_instance_count,
                rows[0].maximum_logical_bytes_per_instance,
                rows[0].maximum_reserved_bytes_per_instance,
            ):
                raise RuntimeError("CP65 shared physical-slot capacity differs")
    auxiliary_groups = tuple(
        rows
        for rows in grouped.values()
        if rows[0].destination_reservation_excluded
        and not rows[0].artifact_id.startswith("__")
    )
    logical_maximum = sum(
        max(
            row.maximum_instance_count * row.maximum_logical_bytes_per_instance
            for row in rows
        )
        for rows in auxiliary_groups
    )
    slot_maximum = sum(
        max(row.maximum_total_reserved_bytes for row in rows)
        for rows in auxiliary_groups
    )
    policy = by_artifact[
        "__allocation_and_directory_charge_policy_slot__"
    ].maximum_total_reserved_bytes
    maximum = slot_maximum + policy
    if logical_maximum != 21_845_344_321 or slot_maximum != 22_213_099_520:
        raise RuntimeError("CP65 auxiliary slot-group arithmetic differs")
    if maximum != 23_286_841_344:
        raise RuntimeError("CP65 auxiliary arithmetic differs")
    return cast(
        CP65AuxiliarySizeProofV1,
        _record(
            CP65AuxiliarySizeProofV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "proof_id": "cp65-exclusive-auxiliary-reservation-size-proof-v1",
                "cp64_capacity_schema_record_sha256": "968108bda050687408fe989186aff3137560b827d1c83622f685a597d208ecfe",
                "auxiliary_reservation_floor_bytes": 34_359_738_368,
                "artifact_bound_ids": tuple(bound.bound_id for bound in bounds),
                "covered_complete_roster_artifact_ids": tuple(
                    row[0] for row in _ARTIFACT_DECLARATIONS
                ),
                "destination_artifact_ids": _DESTINATION_IDS,
                "maximum_auxiliary_artifact_logical_bytes": logical_maximum,
                "maximum_auxiliary_artifact_slot_reserved_bytes": slot_maximum,
                "allocation_and_directory_charge_policy_slot_bytes": policy,
                "maximum_auxiliary_policy_required_bytes": maximum,
                "exclusive_reserved_policy_headroom_bytes": 11_072_897_024,
                "maximum_dynamic_hold_bytes": 34_359_738_368,
                "arithmetic_formula": "mutually-exclusive-launch-alias-counted-once+54-global+2-conditional+4*32-shard-auxiliary-slots+1073741824=23286841344",
                "every_auxiliary_artifact_covered_exactly_once": True,
                "simultaneous_branch_upper_bound_conservative": True,
                "integer_arithmetic_verified": True,
                "fits_exclusive_auxiliary_reservation": True,
                "definition_only": True,
                "production_reservation_observed": False,
            },
        ),
    )


def _signature_contract() -> CP65AuthorizationSignatureContractV1:
    return cast(
        CP65AuthorizationSignatureContractV1,
        _record(
            CP65AuthorizationSignatureContractV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "scheme_id": "rsa-pss-sha256-3072-e65537-salt32-v1",
                "public_key_artifact_id": "launch-authority-public-key",
                "authorization_artifact_id": "launch-authorization",
                "hash_algorithm_id": "sha256",
                "mgf_algorithm_id": "mgf1-sha256",
                "modulus_bytes": 384,
                "modulus_bit_length": 3_072,
                "public_exponent": 65_537,
                "signature_bytes": 384,
                "signature_hex_characters": 768,
                "salt_bytes": 32,
                "em_bits": 3_071,
                "em_bytes": 384,
                "trailer_field": 188,
                "unused_high_bits": 1,
                "signing_preimage_domain": "cp65-test28-launch-authorization-signature-preimage-v1\0",
                "signing_preimage_zeroed_field_pointers": (
                    "/authority_signature_hex",
                    "/authority_signature_sha256",
                    "/body_sha256",
                ),
                "signature_digest_formula": "SHA256(raw-384-byte-signature)",
                "public_key_identity_formula": "SHA256(cp65-test28-launch-authority-public-key-identity-v1\\0+canonical(authority_scheme_id,authority_id,modulus_hex,public_exponent))",
                "strict_pss_verification_steps": (
                    "parse-exact-3072-bit-odd-modulus-and-e65537",
                    "require-gcd-modulus-exponent-one-and-signature-less-than-modulus",
                    "perform-one-modular-exponentiation",
                    "require-emBits3071-emLen384-trailer-bc-unused-high-bit-zero",
                    "mgf1-sha256-exactly-eleven-blocks",
                    "require-318-zero-ps-bytes-01-delimiter-and-32-byte-salt",
                    "constant-time-compare-recomputed-sha256-hash",
                    "check-valid-from-less-equal-issued-less-than-expires-less-equal-valid-until",
                ),
                "signer_implemented": False,
                "key_generation_implemented": False,
                "public_key_present": False,
                "trust_root_bound": False,
                "signature_instance_present": False,
                "verifier_implemented": True,
                "authority_verified": False,
                "launch_authorized": False,
                "definition_only": True,
            },
        ),
    )


_PURPOSE_BY_ARTIFACT = {
    "source-manifest": "frozen-source-fixture-materialization-custody",
    "freeze-receipt": "attempt-frozen-input-closure",
    "power-threshold-receipt": "production-power-review-and-primary-threshold-freeze",
    "preflight-gate-summary": "preauthorization-gates-1-through-15-summary",
    "independent-signoff-set": "independent-preauthorization-signoff-set",
    "capacity-receipt": "production-capacity-and-exclusive-reservation-observation",
    "auxiliary-metadata-reservation": "exclusive-dynamic-auxiliary-reservation",
    "reservation-manifest": "destination-and-auxiliary-reservation-manifest",
    "production-runtime-receipt": "production-runtime-lock-observation",
    "external-seed-acquisition-start-receipt": "durable-start-before-external-source-contact",
    "external-seed-source-receipt": "completed-external-seed-source-custody",
    "seed-capsule-body": "future-production-external-iid-uniform-uint64-with-replacement",
    "production-shard-map-receipt": "candidate-production-shard-map-custody",
    "durability-receipt": "production-writer-durability-qualification",
    "preauthorization-outcome": "preauthorization-atomic-outcome",
    "launch-authorization": "explicit-production-launch-authorization",
    "postauthorization-outcome": "postauthorization-prestart-atomic-outcome",
    "started-receipt": "production-started-custody",
    "launch-receipt": "production-launch-custody",
    "terminal-state": "attempt-terminal-state-publication",
    "sha256-manifest": "terminal-corpus-sha256-manifest",
    "committed-marker": "final-corpus-publication-after-sealed-transition-journal-and-hold-release",
    "launch-authority-public-key": "launch-authority-public-key-custody",
    "dependency-lock-match-receipt": "dependency-lock-match-observation",
    "seed-source-custody-artifact": "external-seed-source-custody-preimage",
    "seed-capsule-sequence-crosscheck-receipt": "seed-capsule-sequence-crosscheck",
    "production-schedule": "production-request-schedule-custody",
    "production-runner-supervisor-qualification-receipt": "production-runner-supervisor-qualification",
    "closed-refusal-failure-classifier-qualification-receipt": "closed-refusal-failure-classifier-qualification",
    "independent-554-estimate-interval-decision-path-qualification-receipt": "independent-554-estimate-interval-decision-path-qualification",
    "independent-full-32768-recomputation-qualification-receipt": "independent-full-32768-recomputation-qualification",
    "independent-reviewer-public-key-set": "independent-reviewer-public-key-set-custody",
    "seed-source-authority-public-key": "seed-source-authority-public-key-custody",
    "seed-source-authority-attestation": "external-seed-source-authority-attestation",
    "power-review-signoff": "signed-power-review-custody",
    "preterminal-durable-artifact-inventory": "preterminal-durable-artifact-inventory",
    "external-digest-preimage-registry": "post-gate15-pre-summary-bounded-external-digest-preimage-custody",
    "shard-index": "production-shard-index-custody",
    "shard-receipt": "production-shard-terminal-custody",
    "partial-seed-acquisition-terminal-receipt": "terminal-custody-of-recovered-prefix",
    "rejected-launch-authorization-candidate": "rejected-launch-authorization-candidate-custody",
}


_STRING_DOMAINS = {
    **{
        (artifact_id, "purpose"): (purpose,)
        for artifact_id, purpose in _PURPOSE_BY_ARTIFACT.items()
    },
    ("freeze-receipt", "from_state"): ("DRAFT_PRE_FREEZE",),
    ("freeze-receipt", "to_state"): ("FROZEN",),
    ("launch-authorization", "attempt_state"): ("FROZEN",),
    ("rejected-launch-authorization-candidate", "attempt_state"): ("FROZEN",),
    ("started-receipt", "purpose"): ("production-started-custody",),
    ("seed-capsule-body", "purpose"): (
        "future-production-external-iid-uniform-uint64-with-replacement",
    ),
    ("seed-capsule-body", "seed_encoding"): ("uint64-16-lowercase-hex-big-endian",),
    ("external-seed-source-receipt", "seed_encoding"): (
        "uint64-16-lowercase-hex-big-endian",
    ),
    ("partial-seed-acquisition-terminal-receipt", "seed_encoding"): (
        "uint64-16-lowercase-hex-big-endian",
    ),
    ("partial-seed-acquisition-terminal-receipt", "terminal_state"): ("INCOMPLETE",),
    ("launch-authority-public-key", "authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("launch-authorization", "authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("rejected-launch-authorization-candidate", "authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("seed-source-authority-public-key", "source_authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("seed-source-authority-attestation", "source_authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("independent-reviewer-public-key-set", "signature_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("independent-signoff-set", "signature_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("power-review-signoff", "signature_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("independent-reviewer-public-key-set", "reviewer_role"): _REQUIRED_REVIEWER_ROLES,
    ("independent-signoff-set", "reviewer_role"): _REQUIRED_REVIEWER_ROLES,
    ("power-review-signoff", "reviewer_role"): (
        "statistical-power-and-decision-reviewer",
    ),
    ("independent-signoff-set", "decision"): ("APPROVE",),
    ("power-review-signoff", "decision"): ("APPROVE",),
    ("auxiliary-metadata-reservation", "hold_relative_path"): (
        ".cp65_auxiliary_reservation_hold.partial",
    ),
    ("auxiliary-metadata-reservation", "reservation_state"): (
        "existing-final-in-place",
        "preallocated-partial-in-place",
        "preallocated-live-journal-in-place",
        "future-o-excl-covered-by-hold",
    ),
    ("preauthorization-outcome", "outcome_arm"): (
        "AUTHORIZATION",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    ),
    ("postauthorization-outcome", "outcome_arm"): (
        "STARTED",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    ),
    ("terminal-state", "terminal_arm"): (
        "PREAUTHORIZATION",
        "POSTAUTHORIZATION_PRESTART",
        "STARTED",
    ),
    ("preterminal-durable-artifact-inventory", "terminal_arm"): (
        "PREAUTHORIZATION",
        "POSTAUTHORIZATION_PRESTART",
        "STARTED",
    ),
    ("terminal-state", "previous_lifecycle_state"): ("FROZEN", "STARTED"),
    ("terminal-state", "terminal_state"): (
        "PASS",
        "FAIL",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    ),
    ("terminal-state", "reason_code"): (
        "completed-as-preregistered",
        "primary-or-structural-failure",
        "frozen-input-or-protocol-invalid",
        "infrastructure-abort",
        "attempt-incomplete",
    ),
    ("external-digest-preimage-registry", "purpose"): (
        "post-gate15-pre-summary-bounded-external-digest-preimage-custody",
    ),
    ("external-digest-preimage-registry", "digest_kind"): (
        "plain-sha256",
        "domain-separated-sha256",
    ),
    ("external-digest-preimage-registry", "preimage_encoding"): (
        "ascii",
        "lowercase-hex",
    ),
    ("committed-marker", "purpose"): (
        "final-corpus-publication-after-sealed-transition-journal-and-hold-release",
    ),
    ("seed-source-custody-artifact", "custody_media_type"): (
        "application/octet-stream",
    ),
    ("seed-source-custody-artifact", "custody_encoding"): ("identity",),
    ("seed-capsule-sequence-crosscheck-receipt", "seed_encoding"): (
        "uint64-16-lowercase-hex-big-endian",
    ),
    ("production-runtime-receipt", "runtime_profile_id"): (
        "cp62-darwin-arm64-cpython3115-numpy246-scipy1171-calibration",
    ),
}


def _string_domain_for_field(
    artifact_id: str,
    pointer: str,
    key: str,
) -> Tuple[str, ...]:
    """Return the closed string domain for one exact issued field rule."""

    domain = _STRING_DOMAINS.get((artifact_id, key), ())
    if artifact_id == "production-schedule":
        if pointer == "/requests/*/schema_version":
            return (_CP63_SCHEMA_VERSION,)
        if pointer == "/requests/*/row_key":
            return tuple(row[1] for row in _ROW_INVENTORY)
        if pointer == "/requests/*/fixture_id":
            return tuple(dict.fromkeys(row[2] for row in _ROW_INVENTORY))
        if pointer == "/requests/*/strategy":
            return tuple(dict.fromkeys(row[3] for row in _ROW_INVENTORY))
    if artifact_id == "closed-refusal-failure-classifier-qualification-receipt":
        if pointer == "/closed_refusal_codes/*":
            return _CLOSED_REFUSAL_CODES
        if pointer == "/closed_failure_codes/*":
            return _CLOSED_FAILURE_CODES
    if artifact_id == "preflight-gate-summary":
        if pointer == "/covered_gate_ids/*":
            return _GATE_IDS[:15]
        if pointer == "/covered_gate_states/*":
            return ("PASS",)
        if pointer == "/covered_evidence_node_ids/*":
            return _GATE_EVIDENCE_NODES[:15]
    if pointer == "/required_reviewer_roles/*" and artifact_id in (
        "independent-signoff-set",
        "independent-reviewer-public-key-set",
    ):
        return _REQUIRED_REVIEWER_ROLES
    if artifact_id == "auxiliary-metadata-reservation" and pointer.startswith(
        "/artifact_entries/*/"
    ):
        slots = _auxiliary_expected_slots()
        if key == "artifact_id":
            return tuple(dict.fromkeys(cast(str, row[0]) for row in slots))
        if key == "primary_publication_arm_id":
            return tuple(dict.fromkeys(cast(str, row[5]) for row in slots))
        if key == "alternate_publication_arm_id":
            return tuple(dict.fromkeys(cast(str, row[6]) for row in slots))
    return domain


def _artifact_maximum_bytes(artifact_id: str) -> int:
    overrides = {
        "frozen-protocol": 16_777_216,
        "frozen-protocol-sha256": 65,
        "frozen-machine-manifest": 16_777_216,
        "dependency-lock": 1_048_576,
        "external-seed-acquisition-journal": 163_840,
        "auxiliary-reservation-transition-journal": 65_536,
        "seed-capsule-body": 131_072,
        "reservation-manifest": 268_435_456,
        "primary-metrics": 268_435_456,
        "secondary-diagnostics": 536_870_912,
        "postexecution-independent-recomputation": 536_870_912,
        "frozen-source-fixture-materialization": 134_217_728,
        "shard-requests": 67_109_888,
        "shard-raw-records": 17_179_870_208,
        "shard-stable-traces": 8_589_935_616,
        "shard-stderr-records": 1_073_750_016,
        "shard-rng-initial-states": 134_217_728,
        "shard-rng-final-states": 134_217_728,
        "shard-index": 134_217_728,
        "shard-receipt": 134_217_728,
    }
    return overrides.get(artifact_id, 67_108_864)


def _artifact_minimum_bytes(artifact_id: str, has_json_keys: bool) -> int:
    """Return the exact lower byte bound for one retained artifact instance."""

    fixed = {
        "frozen-protocol-sha256": 65,
        "external-seed-acquisition-journal": 163_840,
        "auxiliary-reservation-transition-journal": 65_536,
    }
    if artifact_id in fixed:
        return fixed[artifact_id]
    return 2 if has_json_keys else 0


def _explicit_field_kind(key: str, nested_keys: Tuple[str, ...] = ()) -> str:
    """Return the explicitly catalogued JSON kind for one frozen field name.

    This is deliberately a closed-name lookup.  In particular, it must never
    infer an integer merely because a digest field happens to contain a word
    such as ``count`` or ``inode``.
    """

    if key == "terminal_counts":
        return "object"
    if nested_keys or key in _ARRAY_KEYS:
        return "array"
    if key in _BOOLEAN_KEYS:
        return "boolean"
    integer_field_names = frozenset(
        {
            "acquired_seed_count",
            "acquisition_journal_entry_count",
            "acquisition_journal_inode",
            "acquisition_journal_preallocated_bytes",
            "acquisition_journal_raw_bytes",
            "allocated_existing_final_bytes",
            "allocated_future_partial_bytes",
            "unique_nonhold_artifact_allocated_bytes",
            "exclusive_root_charge_baseline_bytes",
            "exclusive_root_charge_current_bytes",
            "disjoint_allocation_and_directory_charge_bytes",
            "allocated_reserved_bytes",
            "allocation_and_directory_charge_policy_slot_bytes",
            "allocation_unit_bytes",
            "artifact_entry_count",
            "artifact_slot_reserved_bytes",
            "authorized_attempt_number",
            "auxiliary_metadata_reservation_required_bytes",
            "auxiliary_metadata_reserved_quota_bytes",
            "auxiliary_transition_journal_after_inventory_entry_count",
            "auxiliary_transition_journal_after_terminal_entry_count",
            "auxiliary_reservation_transition_journal_final_entry_count",
            "auxiliary_transition_journal_prefix_entry_count",
            "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
            "available_bytes_after_reservation",
            "available_bytes_before_reservation",
            "available_inodes_after_reservation",
            "budget",
            "bytes",
            "capacity_partition_bytes",
            "combined_available_and_quota_required_before_reservation_bytes",
            "custody_bytes",
            "decision_path_qualification_case_count",
            "destination_reservation_required_bytes",
            "enforced_quota_bytes",
            "entry_count",
            "environment_drift_case_count",
            "estimate_path_qualification_case_count",
            "exclusive_reserved_headroom_bytes",
            "execution_failure_before_deadline",
            "expected_estimand_count_supported",
            "expected_request_count_supported",
            "expected_seed_count",
            "fd_leak_case_count",
            "hold_allocated_bytes",
            "hold_inode",
            "inode",
            "interval_path_qualification_case_count",
            "key_count",
            "lines",
            "logical_request_count",
            "logical_request_ordinal",
            "logical_request_ordinal_max",
            "logical_request_ordinal_min",
            "logical_reserved_bytes",
            "maximum_auxiliary_artifact_logical_bytes",
            "maximum_auxiliary_reserved_bytes",
            "maximum_logical_bytes",
            "observed_allocation_and_directory_charge_bytes",
            "observed_bytes",
            "ordinal",
            "physical_reservation_sum_bytes",
            "preimage_bytes",
            "physically_allocated_auxiliary_metadata_bytes",
            "physically_allocated_reservation_bytes",
            "preexecution_refusal_before_deadline",
            "primary_slot_count",
            "process_group_cleanup_case_count",
            "public_exponent",
            "qualification_case_count",
            "qualification_test_count",
            "quota_headroom_bytes_after_reservation",
            "quota_headroom_bytes_before_reservation",
            "raw_length",
            "raw_offset",
            "reachability_case_count",
            "request_count",
            "request_length",
            "request_offset",
            "reserved_bytes",
            "returned_rejection_exhausted_before_deadline",
            "returned_rejection_selected_before_deadline",
            "returned_sir_selected_before_deadline",
            "row_ordinal",
            "seed_count",
            "seed_ordinal",
            "seed_ordinal_max",
            "seed_ordinal_min",
            "design_minimum_selected_count",
            "shard_count",
            "shard_ordinal",
            "signoff_count",
            "slot_ordinal",
            "stable_length",
            "stable_offset",
            "stderr_frame_length",
            "stderr_offset",
            "stderr_payload_length",
            "timeout_case_count",
            "timeout_censored_at_deadline",
            "total_allocated_reserved_bytes",
            "total_bytes",
            "total_logical_reserved_bytes",
            "usable_reserved_bytes_after_allocation",
        }
    )
    if key in integer_field_names:
        return "integer"
    return "string"


def _pattern_id(key: str) -> str:
    if key.endswith("_sha256") or key == "sha256":
        return "lowercase-sha256-hex"
    if key.endswith("_signature_hex") or key == "signature_hex":
        return "lowercase-hex-768"
    if key == "modulus_hex":
        return "lowercase-hex-768"
    if key in ("plan_seed_hex",) or "seed_value" in key:
        return "lowercase-hex-16"
    if key.endswith("_utc"):
        return "utc-microseconds-z"
    if "path" in key or key == "relative_directory":
        return "posix-relative-path"
    if key == "shard_id":
        return "shard-id-0001-through-0032"
    if key == "attempt_id":
        return "attempt-id-v1"
    if (
        key.endswith("_method_id")
        or key.endswith("_session_id")
        or key.endswith("_authority_id")
        or key == "authority_id"
    ):
        return "opaque-method-session-authority-id-v1"
    if key == "threshold_value":
        return "canonical-rational-threshold-v1"
    return "bounded-nonempty-ascii"


def _field_rule(
    artifact_id: str,
    pointer: str,
    key: str,
    nested_keys: Tuple[str, ...] = (),
) -> CP65FieldRuleV1:
    exact_integer = _INTEGER_EXACT.get((artifact_id, key))
    kind = _explicit_field_kind(key, nested_keys)
    if exact_integer is not None or "/terminal_counts/" in pointer:
        kind = "integer"
    if key in ("lines", "budget"):
        kind = "integer"
    integer_interval = (
        (exact_integer, exact_integer)
        if exact_integer is not None
        else ((0, 2**64 - 1) if kind == "integer" else ())
    )
    if (artifact_id, pointer) in _INTEGER_INTERVALS:
        integer_interval = _INTEGER_INTERVALS[(artifact_id, pointer)]
    if artifact_id == "external-digest-preimage-registry" and key == "preimage_bytes":
        integer_interval = (0, 65_536)
    if artifact_id == "source-manifest" and pointer == "/entry_count":
        integer_interval = (1, _MAX_SOURCE_MANIFEST_ENTRIES)
    exact_length = _ARRAY_LENGTH_EXACT.get((artifact_id, key))
    if exact_length is not None:
        length_interval = (exact_length, exact_length)
    elif kind == "array":
        length_interval = (0, 32_768)
    elif kind == "string":
        length_interval = (1, 1_048_576)
    else:
        length_interval = ()
    domains = _string_domain_for_field(artifact_id, pointer, key)
    if artifact_id == "source-manifest" and pointer == "/entries/*/role":
        domains = (
            "production-runner-source",
            "independent-recomputation-source",
        )
    if artifact_id == "power-threshold-receipt":
        if key == "gate_id":
            domains = _POWER_PRIMARY_SLOT_IDS
        elif key == "estimand_id":
            domains = _CP61_ESTIMAND_IDS
        elif key == "threshold_encoding":
            domains = (
                "canonical-rational-signed-numerator-positive-denominator-lowest-terms-v1",
            )
    if key == "terminal_state" and artifact_id in (
        "preauthorization-outcome",
        "postauthorization-outcome",
    ):
        domains = ("", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE")
        length_interval = (0, 16)
    if artifact_id == "auxiliary-metadata-reservation" and key in (
        "alternate_final_relative_path",
        "alternate_publication_arm_id",
        "partial_relative_path",
        "file_fsync_completed_at_utc",
        "directory_fsync_completed_at_utc",
    ):
        length_interval = (0, 1_048_576)
    if artifact_id == "power-threshold-receipt":
        if pointer == "/power_review_ascii":
            length_interval = (1, 1_048_576)
        elif pointer in (
            "/selected_count_justification_ascii",
            "/ordered_slot_thresholds/*/justification_ascii",
        ):
            length_interval = (1, 16_384)
    if artifact_id == "external-digest-preimage-registry":
        if pointer in ("/entries", "/ordered_entry_sha256s"):
            length_interval = (0, 4_096)
        elif pointer.endswith("/preimage_ascii"):
            length_interval = (0, 131_072)
    if artifact_id == "source-manifest" and pointer == "/entries":
        length_interval = (1, _MAX_SOURCE_MANIFEST_ENTRIES)
    if (
        artifact_id
        in (
            "preterminal-durable-artifact-inventory",
            "sha256-manifest",
        )
        and pointer == "/entries"
    ):
        length_interval = (1, _MAX_TERMINAL_PUBLICATION_ENTRIES)
    if (
        artifact_id == "independent-signoff-set"
        and pointer == "/ordered_signoffs/*/reviewed_artifact_sha256s"
    ):
        length_interval = (1, 1)
    if kind == "string":
        pattern_id = _pattern_id(key)
        if pattern_id == "lowercase-sha256-hex":
            length_interval = (64, 64)
        elif pattern_id == "lowercase-hex-16":
            length_interval = (16, 16)
        elif pattern_id == "lowercase-hex-768":
            length_interval = (768, 768)
        elif pattern_id == "utc-microseconds-z":
            length_interval = (27, 27)
    declaration = _ARTIFACT_BY_ID[artifact_id]
    if key == "schema" and declaration[6]:
        domains = (declaration[6],)
    if kind == "array" and nested_keys:
        item_rule_ids = tuple(
            "%s:/%s/*/%s" % (artifact_id, pointer.strip("/"), child)
            for child in nested_keys
        )
    elif kind == "array":
        item_rule_ids = ("%s:/%s/*" % (artifact_id, pointer.strip("/")),)
    else:
        item_rule_ids = ()
    return cast(
        CP65FieldRuleV1,
        _record(
            CP65FieldRuleV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "rule_id": "%s:%s" % (artifact_id, pointer),
                "artifact_id": artifact_id,
                "json_pointer": pointer,
                "value_kind": kind,
                "required": True,
                "integer_interval": integer_interval,
                "length_interval": length_interval,
                "boolean_domain": (
                    (
                        (True,)
                        if artifact_id == "committed-marker"
                        and key == "hold_absence_verified"
                        else (
                            (False,)
                            if key
                            in (
                                "production_runner_rng_or_child_started_before_receipt",
                                "topup_redraw_reselection_permitted",
                            )
                            else (False, True)
                        )
                    )
                    if kind == "boolean"
                    else ()
                ),
                "string_domain": domains,
                "string_pattern_id": pattern_id if kind == "string" else "",
                "array_item_rule_ids": item_rule_ids,
                "exact_object_keys": nested_keys,
                "cross_constraint_ids": ("field:%s:%s" % (artifact_id, pointer),)
                + (
                    ("independent-signoff-reviewed-summary-raw-binding",)
                    if artifact_id == "independent-signoff-set"
                    and pointer == "/ordered_signoffs/*/reviewed_artifact_sha256s"
                    else ()
                )
                + tuple(
                    "constraint:" + predicate_id
                    for predicate_id, artifact_ids, _operation, pointers, _operand in _CROSS_PREDICATE_SPECS
                    if artifact_id in artifact_ids and pointer in pointers
                ),
            },
        ),
    )


def _build_field_rules() -> Tuple[CP65FieldRuleV1, ...]:
    result = []
    for (
        artifact_id,
        _path,
        _scope,
        _media,
        keys,
        nested,
        _domain,
        _preserved,
    ) in _ARTIFACT_DECLARATIONS:
        nested_by_key = dict(nested)
        for key in keys:
            children = nested_by_key.get(key, ())
            result.append(_field_rule(artifact_id, "/" + key, key, children))
            for child in children:
                child_pointer = (
                    "/%s/%s" % (key, child)
                    if key == "terminal_counts"
                    else "/%s/*/%s" % (key, child)
                )
                result.append(
                    _field_rule(
                        artifact_id,
                        child_pointer,
                        child,
                    )
                )
                if _explicit_field_kind(child) == "array":
                    result.append(
                        _field_rule(
                            artifact_id,
                            child_pointer + "/*",
                            child[:-1] or "item",
                        )
                    )
        primitive_arrays = tuple(
            key
            for key in keys
            if key not in nested_by_key and _explicit_field_kind(key) == "array"
        )
        for key in primitive_arrays:
            result.append(_field_rule(artifact_id, "/%s/*" % key, key[:-1] or "item"))
    return tuple(result)


def _predicate(
    predicate_id: str,
    artifact_ids: Tuple[str, ...],
    operation_id: str,
    pointers: Tuple[str, ...],
    operand: object,
    child_predicate_ids: Tuple[str, ...] = (),
) -> CP65PredicateContractV1:
    return cast(
        CP65PredicateContractV1,
        _record(
            CP65PredicateContractV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "predicate_id": predicate_id,
                "applies_to_artifact_ids": artifact_ids,
                "input_json_pointers": pointers,
                "operation_id": operation_id,
                "operand_json_ascii": _plain_json_bytes(operand).decode("ascii"),
                "child_predicate_ids": child_predicate_ids,
                "evaluation_order": pointers,
                "failure_code": "cp65-predicate-failed:" + predicate_id,
                "validator_implemented": operation_id in _PREDICATE_EVALUATORS,
                "definition_only": True,
            },
        ),
    )


_PREDICATE_OPERATION_IDS = frozenset(
    {
        "all-equal",
        "contiguous-cover",
        "cross-constraint-satisfied",
        "digest-sequence-equal",
        "discriminated-union",
        "exact-equal",
        "field-rule-satisfied",
        "integer-formula-equal",
        "integer-sum-equal",
        "length-equal",
        "logical-and",
        "logical-not",
        "logical-or",
        "member-of",
        "not-equal",
        "ordered-equal",
        "relative-path-template-match",
        "rsa-pss-verify",
        "sha256-body-equal",
        "sha256-raw-equal",
        "strictly-increasing",
        "utc-interval-contained",
    }
)


def _operand_interval_matches(value: object, interval: object) -> bool:
    return (
        type(value) is int
        and type(interval) is list
        and len(interval) == 2
        and type(interval[0]) is int
        and type(interval[1]) is int
        and interval[0] <= value <= interval[1]
    )


def _predicate_exact_equal(values: tuple, operand: dict) -> bool:
    if "expected" in operand:
        return len(values) == 1 and values[0] == operand["expected"]
    if operand.get("value_kind") == "integer":
        return len(values) == 1 and _operand_interval_matches(
            values[0], operand.get("integer_interval")
        )
    if operand.get("value_kind") == "string":
        if len(values) != 1 or type(values[0]) is not str:
            return False
        domain = operand.get("string_domain", [])
        interval = operand.get("length_interval", [])
        return (not domain or values[0] in domain) and (
            not interval or interval[0] <= len(values[0].encode("ascii")) <= interval[1]
        )
    if operand.get("value_kind") == "object":
        return (
            len(values) == 1
            and type(values[0]) is dict
            and tuple(values[0]) == tuple(operand.get("exact_object_keys", []))
        )
    return len(values) <= 1 or all(value == values[0] for value in values[1:])


def _predicate_member_of(values: tuple, operand: dict) -> bool:
    domain = operand.get(
        "string_domain", operand.get("boolean_domain", operand.get("members", []))
    )
    return len(values) == 1 and values[0] in domain


def _predicate_field_rule_satisfied(values: tuple, operand: dict) -> bool:
    if len(values) != 1 or set(operand) != {"rule_id"}:
        return False
    rules, _predicates = _predicate_execution_catalog()
    matching = tuple(rule for rule in rules if rule.rule_id == operand["rule_id"])
    if len(matching) != 1:
        return False
    return _field_rule_value_satisfied(
        matching[0], values[0], {rule.rule_id: rule for rule in rules}, ()
    )


def _field_rule_string_pattern_satisfied(rule: CP65FieldRuleV1, value: str) -> bool:
    pattern = rule.string_pattern_id
    if not pattern:
        return True
    if value == "" and (
        value in rule.string_domain or rule.length_interval[:1] == (0,)
    ):
        return True
    if pattern == "lowercase-sha256-hex":
        return _SHA256_RE.fullmatch(value) is not None
    if pattern == "lowercase-hex-16":
        return _HEX16_RE.fullmatch(value) is not None
    if pattern == "lowercase-hex-768":
        return _HEX768_RE.fullmatch(value) is not None
    if pattern == "utc-microseconds-z":
        return _UTC_RE.fullmatch(value) is not None
    if pattern == "posix-relative-path":
        try:
            _require_relative_path(value, rule.rule_id)
        except ValueError:
            return False
        return True
    if pattern == "shard-id-0001-through-0032":
        return _SHARD_ID_RE.fullmatch(value) is not None
    if pattern == "attempt-id-v1":
        return _ATTEMPT_ID_RE.fullmatch(value) is not None
    if pattern == "opaque-method-session-authority-id-v1":
        return _OPAQUE_METHOD_SESSION_AUTHORITY_ID_RE.fullmatch(value) is not None
    if pattern == "canonical-rational-threshold-v1":
        try:
            _parse_canonical_threshold_rational(value, rule.rule_id)
        except ValueError:
            return False
        return True
    if pattern == "bounded-nonempty-ascii":
        return bool(value)
    return False


def _field_rule_value_satisfied(
    rule: CP65FieldRuleV1,
    value: object,
    rules_by_id: Mapping[str, CP65FieldRuleV1],
    active_rule_ids: Tuple[str, ...],
) -> bool:
    """Execute one closed field rule, including its recursive item rules."""

    if rule.rule_id in active_rule_ids:
        return False
    active = active_rule_ids + (rule.rule_id,)
    if rule.value_kind == "boolean":
        return type(value) is bool and value in rule.boolean_domain
    if rule.value_kind == "integer":
        return (
            type(value) is int
            and rule.integer_interval[0] <= value <= rule.integer_interval[1]
        )
    if rule.value_kind == "string":
        if type(value) is not str:
            return False
        try:
            size = len(value.encode("ascii"))
        except UnicodeEncodeError:
            return False
        return (
            rule.length_interval[0] <= size <= rule.length_interval[1]
            and (not rule.string_domain or value in rule.string_domain)
            and _field_rule_string_pattern_satisfied(rule, value)
        )
    if rule.value_kind == "array":
        if (
            type(value) is not list
            or not rule.length_interval[0] <= len(value) <= rule.length_interval[1]
        ):
            return False
        if not rule.array_item_rule_ids:
            return True
        item_rules = []
        for rule_id in rule.array_item_rule_ids:
            item_rule = rules_by_id.get(rule_id)
            if item_rule is None:
                return False
            item_rules.append(item_rule)
        if rule.exact_object_keys:
            for item in value:
                if (
                    type(item) is not dict
                    or len(item) != len(rule.exact_object_keys)
                    or set(item) != set(rule.exact_object_keys)
                ):
                    return False
                for key, item_rule in zip(rule.exact_object_keys, item_rules):
                    if not _field_rule_value_satisfied(
                        item_rule, item[key], rules_by_id, active
                    ):
                        return False
            return True
        if len(item_rules) != 1:
            return False
        return all(
            _field_rule_value_satisfied(item_rules[0], item, rules_by_id, active)
            for item in value
        )
    if rule.value_kind == "object":
        if (
            type(value) is not dict
            or len(value) != len(rule.exact_object_keys)
            or set(value) != set(rule.exact_object_keys)
        ):
            return False
        prefix = rule.rule_id + "/"
        child_rules = tuple(
            candidate
            for candidate in rules_by_id.values()
            if candidate.rule_id.startswith(prefix)
            and "/" not in candidate.rule_id[len(prefix) :]
        )
        if len(child_rules) != len(rule.exact_object_keys):
            return not rule.exact_object_keys
        child_by_key = {
            candidate.json_pointer.rsplit("/", 1)[-1]: candidate
            for candidate in child_rules
        }
        return all(
            key in child_by_key
            and _field_rule_value_satisfied(
                child_by_key[key], value[key], rules_by_id, active
            )
            for key in rule.exact_object_keys
        )
    return False


def _predicate_length_equal(values: tuple, operand: dict) -> bool:
    if not values:
        return False
    interval = operand.get("length_interval", [])
    if interval:
        return (
            hasattr(values[0], "__len__")
            and interval[0] <= len(values[0]) <= interval[1]
        )
    lengths = [len(value) if hasattr(value, "__len__") else value for value in values]
    return all(length == lengths[0] for length in lengths[1:])


def _predicate_all_equal(values: tuple, _operand: dict) -> bool:
    return bool(values) and all(value == values[0] for value in values[1:])


def _predicate_not_equal(values: tuple, operand: dict) -> bool:
    when = operand.get("when")
    if when is not None:
        if len(values) != 2 or type(when) is not dict or len(when) != 1:
            return False
        expected_arm = next(iter(when.values()))
        return values[0] != expected_arm or values[1] != operand.get("value")
    return len(values) == 1 and values[0] != operand.get("value")


def _predicate_ordered_equal(values: tuple, operand: dict) -> bool:
    expected_sequences = operand.get("expected_sequences")
    if expected_sequences is not None:
        return len(values) == len(expected_sequences) and all(
            type(value) in (tuple, list) and list(value) == expected
            for value, expected in zip(values, expected_sequences)
        )
    expected = operand.get("expected")
    if expected is not None:
        return len(values) == 1 and list(values[0]) == expected
    return bool(values) and all(
        tuple(value) == tuple(values[0]) for value in values[1:]
    )


def _predicate_strictly_increasing(values: tuple, operand: dict) -> bool:
    if len(values) != 1 or type(values[0]) not in (tuple, list):
        return False
    sequence = values[0]
    if not sequence or any(type(item) is not int for item in sequence):
        return False
    step = operand.get("step")
    if step is not None:
        first = operand.get("first", sequence[0] if sequence else 0)
        return list(sequence) == [
            first + step * index for index in range(len(sequence))
        ]
    return all(left < right for left, right in zip(sequence, sequence[1:]))


def _predicate_contiguous_cover(values: tuple, operand: dict) -> bool:
    if len(values) != 4:
        return False
    seed_minima, seed_maxima, logical_minima, logical_maxima = values
    sequences = (seed_minima, seed_maxima, logical_minima, logical_maxima)
    if any(type(sequence) not in (tuple, list) for sequence in sequences):
        return False
    if not seed_minima or len({len(sequence) for sequence in sequences}) != 1:
        return False
    if any(any(type(item) is not int for item in sequence) for sequence in sequences):
        return False

    def exact_cover(minima: object, maxima: object, expected: object) -> bool:
        return (
            type(expected) is list
            and len(expected) == 2
            and minima[0] == expected[0]
            and maxima[-1] == expected[1]
            and all(left <= right for left, right in zip(minima, maxima))
            and all(
                minima[index] == maxima[index - 1] + 1
                for index in range(1, len(minima))
            )
        )

    return exact_cover(
        seed_minima, seed_maxima, operand.get("seed_cover")
    ) and exact_cover(logical_minima, logical_maxima, operand.get("logical_cover"))


def _predicate_integer_sum_equal(values: tuple, _operand: dict) -> bool:
    return (
        len(values) == 2
        and type(values[0]) in (tuple, list, dict)
        and type(values[1]) is int
        and sum(values[0].values() if type(values[0]) is dict else values[0])
        == values[1]
    )


def _predicate_integer_formula_equal(values: tuple, operand: dict) -> bool:
    formula = operand.get("formula")
    if (
        formula
        == "entry-count=acquired-count;raw-file-bytes=163840;valid-prefix-bytes=80*entry-count"
    ):
        return len(values) == 3 and values[0] == values[1] and values[2] == 163_840
    return False


def _predicate_digest_sequence_equal(values: tuple, _operand: dict) -> bool:
    return len(values) == 2 and tuple(values[0]) == tuple(values[1])


def _predicate_discriminated_union(values: tuple, operand: dict) -> bool:
    arms = operand.get("arms", [])
    if not values or values[0] not in arms:
        return False
    arm = values[0]
    if arms and arms[0] == "AUTHORIZATION":
        if len(values) != 3 or type(values[1]) is not str or type(values[2]) is not str:
            return False
        return (_SHA256_RE.fullmatch(values[1]) is not None) and (
            (arm == "AUTHORIZATION" and values[1] != _ZERO_SHA256 and values[2] == "")
            or (
                arm in ("INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE")
                and values[2] == arm
            )
        )
    if arms and arms[0] == "STARTED":
        if len(values) != 3 or type(values[1]) is not str or type(values[2]) is not str:
            return False
        return (
            _SHA256_RE.fullmatch(values[1]) is not None
            and values[1] != _ZERO_SHA256
            and (
                (arm == "STARTED" and values[2] == "")
                or (
                    arm in ("INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE")
                    and values[2] == arm
                )
            )
        )
    if arms and arms[0] == "PREAUTHORIZATION":
        if len(values) != 10:
            return False
        (
            _terminal_arm,
            previous,
            state,
            freeze_digest,
            preauth_digest,
            launch_digest,
            postauth_digest,
            started_digest,
            inventory_digest,
            reason,
        ) = values
        if any(
            type(item) is not str
            for item in (
                previous,
                state,
                freeze_digest,
                preauth_digest,
                launch_digest,
                postauth_digest,
                started_digest,
                inventory_digest,
                reason,
            )
        ):
            return False
        reason_by_state = {
            "PASS": "completed-as-preregistered",
            "FAIL": "primary-or-structural-failure",
            "INVALID_PROTOCOL": "frozen-input-or-protocol-invalid",
            "ABORTED_INFRA": "infrastructure-abort",
            "INCOMPLETE": "attempt-incomplete",
        }
        if reason_by_state.get(state) != reason:
            return False
        digests = (
            freeze_digest,
            preauth_digest,
            launch_digest,
            postauth_digest,
            started_digest,
            inventory_digest,
        )
        if any(_SHA256_RE.fullmatch(item) is None for item in digests):
            return False
        nonzero_common = (
            freeze_digest != _ZERO_SHA256
            and preauth_digest != _ZERO_SHA256
            and inventory_digest != _ZERO_SHA256
        )
        terminal_states = ("INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE")
        if arm == "PREAUTHORIZATION":
            return (
                nonzero_common
                and previous == "FROZEN"
                and state in terminal_states
                and launch_digest == postauth_digest == started_digest == _ZERO_SHA256
            )
        if arm == "POSTAUTHORIZATION_PRESTART":
            return (
                nonzero_common
                and previous == "FROZEN"
                and state in terminal_states
                and launch_digest != _ZERO_SHA256
                and postauth_digest != _ZERO_SHA256
                and started_digest == _ZERO_SHA256
            )
        return (
            nonzero_common
            and previous == "STARTED"
            and state in tuple(reason_by_state)
            and launch_digest != _ZERO_SHA256
            and postauth_digest != _ZERO_SHA256
            and started_digest != _ZERO_SHA256
        )
    return False


def _predicate_logical_and(values: tuple, _operand: dict) -> bool:
    return bool(values) and all(value is True for value in values)


def _predicate_logical_or(values: tuple, operand: dict) -> bool:
    if values and type(values[0]) is str and "arms" in operand:
        if len(values) != 2 or type(values[1]) is not str:
            return False
        arm, terminal_state = values
        return arm in operand["arms"] and (
            (arm == "AUTHORIZATION" and terminal_state == "")
            or (arm != "AUTHORIZATION" and terminal_state == arm)
        )
    return any(value is True for value in values)


def _predicate_logical_not(values: tuple, operand: dict) -> bool:
    if operand.get("forbidden") == "both-present":
        return len(values) == 2 and not (values[0] and values[1])
    return len(values) == 1 and values[0] is False


def _predicate_relative_path(values: tuple, operand: dict) -> bool:
    if len(values) != 1 or type(values[0]) is not str:
        return False
    template = operand["path_template"]
    if "{shard_id}" not in template:
        return values[0] == template
    prefix, suffix = template.split("{shard_id}")
    candidate = values[0]
    if not candidate.startswith(prefix) or not candidate.endswith(suffix):
        return False
    shard_id = candidate[len(prefix) : len(candidate) - len(suffix)]
    return (
        re.fullmatch(r"shard-(?:000[1-9]|00[12][0-9]|003[0-2])", shard_id) is not None
    )


def _predicate_sha256_raw(values: tuple, _operand: dict) -> bool:
    return (
        len(values) == 2
        and type(values[0]) is str
        and type(values[1]) is bytes
        and hmac.compare_digest(values[0], hashlib.sha256(values[1]).hexdigest())
    )


def _predicate_sha256_body(values: tuple, operand: dict) -> bool:
    if len(values) != 2 or type(values[0]) is not str:
        return False
    if type(values[1]) is str:
        return (
            _SHA256_RE.fullmatch(values[0]) is not None
            and _SHA256_RE.fullmatch(values[1]) is not None
            and hmac.compare_digest(values[0], values[1])
        )
    if type(values[1]) is not dict:
        return False
    domain = operand.get("domain", "").encode("ascii")
    zeroed = dict(values[1])
    zeroed["body_sha256"] = _ZERO_SHA256
    return hmac.compare_digest(
        values[0],
        hashlib.sha256(domain + b"\0" + _plain_json_bytes(zeroed)).hexdigest(),
    )


def _predicate_utc_interval(values: tuple, _operand: dict) -> bool:
    if len(values) != 4:
        return False
    try:
        parsed = tuple(_require_utc(value, "predicate timestamp") for value in values)
    except ValueError:
        return False
    return parsed[0] <= parsed[1] < parsed[2] <= parsed[3]


def _predicate_rsa_pss(values: tuple, _operand: dict) -> bool:
    return (
        len(values) == 3
        and type(values[0]) is bytes
        and type(values[1]) is bytes
        and type(values[2]) is bytes
        and _verify_rsa_pss_sha256_3072(values[0], values[1], values[2])
    )


def _cross_auxiliary_disjoint_conservation(values: tuple) -> bool:
    if len(values) != 6 or any(type(value) is not int for value in values):
        return False
    baseline, current, unique_nonhold, hold, disjoint, physical = values
    return (
        0 <= baseline <= current
        and 0 <= unique_nonhold
        and 0 <= disjoint <= 1_073_741_824
        and current - baseline == unique_nonhold + hold + disjoint
        and hold >= 11_140_005_888
        and physical == unique_nonhold + disjoint + hold
        and physical >= 34_359_738_368
    )


def _cross_source_manifest_roles_disjoint(values: tuple) -> bool:
    if len(values) != 1 or type(values[0]) is not list:
        return False
    independent_paths = set()
    production_paths = set()
    for row in values[0]:
        if type(row) is not dict:
            return False
        role = row.get("role")
        path = row.get("relative_path")
        if (
            role
            not in (
                "production-runner-source",
                "independent-recomputation-source",
            )
            or type(path) is not str
        ):
            return False
        if role == "production-runner-source":
            production_paths.add(path)
        else:
            independent_paths.add(path)
    return bool(independent_paths) and independent_paths.isdisjoint(production_paths)


def _cross_signoffs_bind_summary(values: tuple) -> bool:
    if len(values) != 2 or type(values[0]) not in (tuple, list):
        return False
    reviewed_vectors, summary_digest = values
    return (
        type(summary_digest) is str
        and _SHA256_RE.fullmatch(summary_digest) is not None
        and summary_digest != _ZERO_SHA256
        and len(reviewed_vectors) == 4
        and all(
            type(reviewed) in (tuple, list) and list(reviewed) == [summary_digest]
            for reviewed in reviewed_vectors
        )
    )


_CROSS_CONSTRAINT_EVALUATORS = {
    "auxiliary-exclusive-root-charge-disjoint-conservation": (
        _cross_auxiliary_disjoint_conservation
    ),
    "source-manifest-role-partitions-disjoint": (_cross_source_manifest_roles_disjoint),
    "independent-signoff-reviewed-summary-raw-binding": (_cross_signoffs_bind_summary),
}


def _predicate_cross_constraint_satisfied(values: tuple, operand: dict) -> bool:
    constraint_id = operand.get("constraint_id")
    if type(constraint_id) is not str or not constraint_id:
        raise ValueError("cross-constraint predicate has no closed constraint id")
    for (
        predicate_id,
        _artifacts,
        operation_id,
        _pointers,
        direct_operand,
    ) in _CROSS_PREDICATE_SPECS:
        if predicate_id == constraint_id:
            evaluator = _PREDICATE_EVALUATORS.get(operation_id)
            if evaluator is None or operation_id == "cross-constraint-satisfied":
                raise ValueError("cross-constraint dispatch is recursive or unknown")
            return evaluator(values, direct_operand)
    evaluator = _CROSS_CONSTRAINT_EVALUATORS.get(constraint_id)
    if evaluator is None:
        raise ValueError("unknown CP65 cross-constraint id")
    return evaluator(values)


_PREDICATE_EVALUATORS = {
    "all-equal": _predicate_all_equal,
    "contiguous-cover": _predicate_contiguous_cover,
    "cross-constraint-satisfied": _predicate_cross_constraint_satisfied,
    "digest-sequence-equal": _predicate_digest_sequence_equal,
    "discriminated-union": _predicate_discriminated_union,
    "exact-equal": _predicate_exact_equal,
    "field-rule-satisfied": _predicate_field_rule_satisfied,
    "integer-formula-equal": _predicate_integer_formula_equal,
    "integer-sum-equal": _predicate_integer_sum_equal,
    "length-equal": _predicate_length_equal,
    "logical-and": _predicate_logical_and,
    "logical-not": _predicate_logical_not,
    "logical-or": _predicate_logical_or,
    "member-of": _predicate_member_of,
    "not-equal": _predicate_not_equal,
    "ordered-equal": _predicate_ordered_equal,
    "relative-path-template-match": _predicate_relative_path,
    "rsa-pss-verify": _predicate_rsa_pss,
    "sha256-body-equal": _predicate_sha256_body,
    "sha256-raw-equal": _predicate_sha256_raw,
    "strictly-increasing": _predicate_strictly_increasing,
    "utc-interval-contained": _predicate_utc_interval,
}

if frozenset(_PREDICATE_EVALUATORS) != _PREDICATE_OPERATION_IDS:
    raise RuntimeError("CP65 predicate operation dispatch differs")


_CROSS_PREDICATE_SPECS = (
    (
        "cross:preauthorization-outcome-discriminated-union",
        ("preauthorization-outcome",),
        "discriminated-union",
        ("/outcome_arm", "/prepared_launch_authorization_sha256", "/terminal_state"),
        {"arms": ["AUTHORIZATION", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"]},
    ),
    (
        "cross:postauthorization-outcome-discriminated-union",
        ("postauthorization-outcome",),
        "discriminated-union",
        ("/outcome_arm", "/launch_authorization_sha256", "/terminal_state"),
        {"arms": ["STARTED", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"]},
    ),
    (
        "cross:terminal-arm-member-of-closed-domain",
        ("terminal-state",),
        "member-of",
        ("/terminal_arm",),
        {"members": ["PREAUTHORIZATION", "POSTAUTHORIZATION_PRESTART", "STARTED"]},
    ),
    (
        "cross:source-start-and-session-digests-equal",
        ("external-seed-source-receipt",),
        "all-equal",
        ("/acquisition_start_receipt_sha256", "/acquisition_session_sha256"),
        {},
    ),
    (
        "cross:shard-map-ranges-contiguously-cover-production",
        ("production-shard-map-receipt",),
        "contiguous-cover",
        (
            "/shards/*/seed_ordinal_min",
            "/shards/*/seed_ordinal_max",
            "/shards/*/logical_request_ordinal_min",
            "/shards/*/logical_request_ordinal_max",
        ),
        {"seed_cover": [1, 2048], "logical_cover": [1, 32768]},
    ),
    (
        "cross:schedule-row-digest-sequence-equals-outer-sequence",
        ("production-schedule",),
        "digest-sequence-equal",
        ("/requests/*/request_row_sha256", "/ordered_request_record_sha256s"),
        {},
    ),
    (
        "cross:terminal-state-is-exact-discriminated-union",
        ("terminal-state",),
        "discriminated-union",
        (
            "/terminal_arm",
            "/previous_lifecycle_state",
            "/terminal_state",
            "/freeze_receipt_sha256",
            "/preauthorization_outcome_sha256",
            "/launch_authorization_sha256",
            "/postauthorization_outcome_sha256",
            "/started_receipt_sha256",
            "/durable_artifact_inventory_sha256",
            "/reason_code",
        ),
        {"arms": ["PREAUTHORIZATION", "POSTAUTHORIZATION_PRESTART", "STARTED"]},
    ),
    (
        "cross:partial-journal-valid-prefix-formula",
        ("partial-seed-acquisition-terminal-receipt",),
        "integer-formula-equal",
        (
            "/acquired_seed_count",
            "/acquisition_journal_entry_count",
            "/acquisition_journal_raw_bytes",
        ),
        {
            "formula": "entry-count=acquired-count;raw-file-bytes=163840;valid-prefix-bytes=80*entry-count"
        },
    ),
    (
        "cross:shard-terminal-counts-sum-to-request-count",
        ("shard-receipt",),
        "integer-sum-equal",
        ("/terminal_counts", "/request_count"),
        {},
    ),
    (
        "cross:seed-capsule-array-lengths-equal-count",
        ("seed-capsule-body",),
        "length-equal",
        ("/seed_ordinals", "/ordered_seed_values", "/seed_count"),
        {},
    ),
    (
        "cross:preauthorization-record-is-one-allowed-arm",
        ("preauthorization-outcome",),
        "logical-or",
        ("/outcome_arm", "/terminal_state"),
        {"arms": ["AUTHORIZATION", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"]},
    ),
    (
        "cross:published-and-rejected-authorization-not-copresent",
        ("launch-authorization", "rejected-launch-authorization-candidate"),
        "logical-not",
        (
            "launch-authorization:$present",
            "rejected-launch-authorization-candidate:$present",
        ),
        {"forbidden": "both-present"},
    ),
    (
        "cross:authorization-arm-prepared-digest-nonzero",
        ("preauthorization-outcome",),
        "not-equal",
        ("/outcome_arm", "/prepared_launch_authorization_sha256"),
        {"value": _ZERO_SHA256, "when": {"/outcome_arm": "AUTHORIZATION"}},
    ),
    (
        "cross:preflight-summary-vectors-ordered",
        ("preflight-gate-summary",),
        "ordered-equal",
        ("/covered_gate_ids", "/covered_gate_states", "/covered_evidence_node_ids"),
        {
            "expected_sequences": [
                list(_GATE_IDS[:15]),
                ["PASS"] * 15,
                list(_GATE_EVIDENCE_NODES[:15]),
            ]
        },
    ),
    (
        "cross:launch-authorization-rsa-pss-mathematics",
        ("launch-authorization", "launch-authority-public-key"),
        "rsa-pss-verify",
        (
            "launch-authorization:$signature-preimage-bytes",
            "launch-authority-public-key:$modulus-bytes",
            "launch-authorization:$signature-bytes",
        ),
        {"scheme": "rsa-pss-sha256-3072-e65537-salt32-v1"},
    ),
    (
        "cross:source-receipt-binds-start-body-digest",
        ("external-seed-source-receipt", "external-seed-acquisition-start-receipt"),
        "sha256-body-equal",
        (
            "external-seed-source-receipt:/acquisition_start_receipt_sha256",
            "external-seed-acquisition-start-receipt:/body_sha256",
        ),
        {"domain": "cp64-test28-external-seed-acquisition-start-receipt-v1"},
    ),
    (
        "cross:freeze-binds-source-manifest-raw-bytes",
        ("freeze-receipt", "source-manifest"),
        "sha256-raw-equal",
        ("freeze-receipt:/bound_files_sha256", "source-manifest:$raw_sha256"),
        {},
    ),
    (
        "cross:source-manifest-entry-ordinals-strictly-increase",
        ("source-manifest",),
        "strictly-increasing",
        ("/entries/*/ordinal",),
        {"first": 1, "step": 1},
    ),
    (
        "cross:launch-authorization-validity-contained-by-key",
        ("launch-authorization", "launch-authority-public-key"),
        "utc-interval-contained",
        (
            "launch-authority-public-key:/valid_from_utc",
            "launch-authorization:/authorization_issued_at_utc",
            "launch-authorization:/authorization_expires_at_utc",
            "launch-authority-public-key:/valid_until_utc",
        ),
        {"inequality": "valid-from<=issued<expires<=valid-until"},
    ),
)


def _field_predicate_operation(rule: CP65FieldRuleV1) -> str:
    del rule
    return "field-rule-satisfied"


def _field_predicate_operand(rule: CP65FieldRuleV1) -> dict:
    return {"rule_id": rule.rule_id}


def _build_predicates(
    field_rules: Tuple[CP65FieldRuleV1, ...] = (),
) -> Tuple[CP65PredicateContractV1, ...]:
    if not field_rules:
        field_rules = _build_field_rules()
    result = []
    by_artifact = {}
    for rule in field_rules:
        predicate_id = "field:" + rule.rule_id
        by_artifact.setdefault(rule.artifact_id, []).append(predicate_id)
        result.append(
            _predicate(
                predicate_id,
                (rule.artifact_id,),
                _field_predicate_operation(rule),
                (rule.json_pointer,),
                _field_predicate_operand(rule),
            )
        )
    cross_by_artifact = {}
    for (
        predicate_id,
        artifact_ids,
        operation_id,
        pointers,
        operand,
    ) in _CROSS_PREDICATE_SPECS:
        wrapper_id = "constraint:" + predicate_id
        for artifact_id in artifact_ids:
            cross_by_artifact.setdefault(artifact_id, []).append(wrapper_id)
        result.append(
            _predicate(
                predicate_id,
                artifact_ids,
                operation_id,
                pointers,
                operand,
                (
                    (
                        "field:preauthorization-outcome:/outcome_arm",
                        "field:preauthorization-outcome:/terminal_state",
                    )
                    if predicate_id
                    == "cross:preauthorization-record-is-one-allowed-arm"
                    else (
                        ("cross:preauthorization-record-is-one-allowed-arm",)
                        if operation_id == "logical-not"
                        else ()
                    )
                ),
            )
        )
        result.append(
            _predicate(
                wrapper_id,
                artifact_ids,
                "cross-constraint-satisfied",
                pointers,
                {"constraint_id": predicate_id},
                (predicate_id,),
            )
        )
    cross_by_artifact.setdefault("auxiliary-metadata-reservation", []).append(
        "always-reserved-with-auxiliary-partition"
    )
    result.append(
        _predicate(
            "auxiliary-exclusive-root-charge-disjoint-conservation",
            ("auxiliary-metadata-reservation",),
            "cross-constraint-satisfied",
            (
                "/exclusive_root_charge_baseline_bytes",
                "/exclusive_root_charge_current_bytes",
                "/unique_nonhold_artifact_allocated_bytes",
                "/hold_allocated_bytes",
                "/disjoint_allocation_and_directory_charge_bytes",
                "/physical_reservation_sum_bytes",
            ),
            {
                "constraint_id": (
                    "auxiliary-exclusive-root-charge-disjoint-conservation"
                )
            },
        )
    )
    cross_by_artifact.setdefault("launch-authorization", []).append(
        "mutual-exclusion:launch-or-rejected-authorization"
    )
    cross_by_artifact.setdefault("auxiliary-metadata-reservation", []).append(
        "auxiliary-exclusive-root-charge-disjoint-conservation"
    )
    result.append(
        _predicate(
            "source-manifest-role-partitions-disjoint",
            ("source-manifest",),
            "cross-constraint-satisfied",
            ("/entries",),
            {"constraint_id": "source-manifest-role-partitions-disjoint"},
        )
    )
    cross_by_artifact.setdefault("source-manifest", []).append(
        "source-manifest-role-partitions-disjoint"
    )
    result.append(
        _predicate(
            "independent-signoff-reviewed-summary-raw-binding",
            ("independent-signoff-set", "preflight-gate-summary"),
            "cross-constraint-satisfied",
            (
                "/ordered_signoffs/*/reviewed_artifact_sha256s",
                "preflight-gate-summary:$raw_sha256",
            ),
            {"constraint_id": ("independent-signoff-reviewed-summary-raw-binding")},
        )
    )
    cross_by_artifact.setdefault("independent-signoff-set", []).append(
        "independent-signoff-reviewed-summary-raw-binding"
    )
    for (
        artifact_id,
        path,
        _scope,
        _media,
        _keys,
        _nested,
        _domain,
        _preserved,
    ) in _ARTIFACT_DECLARATIONS:
        result.append(
            _predicate(
                "presence:" + artifact_id,
                (artifact_id,),
                "relative-path-template-match",
                ("$relative_path",),
                {"path_template": path},
            )
        )
        result.append(
            _predicate(
                "record:" + artifact_id,
                (artifact_id,),
                "logical-and",
                (),
                {},
                ("presence:" + artifact_id,)
                + tuple(by_artifact.get(artifact_id, ()))
                + tuple(cross_by_artifact.get(artifact_id, ())),
            )
        )
    result.append(
        _predicate(
            "always-reserved-with-auxiliary-partition",
            (),
            "exact-equal",
            ("$policy-reserved",),
            {"expected": True, "actual": True},
        )
    )
    result.append(
        _predicate(
            "co-presence:launch-and-rejected-authorization",
            (
                "launch-authorization",
                "rejected-launch-authorization-candidate",
            ),
            "logical-and",
            (),
            {},
            (
                "presence:launch-authorization",
                "presence:rejected-launch-authorization-candidate",
            ),
        )
    )
    result.append(
        _predicate(
            "mutual-exclusion:launch-or-rejected-authorization",
            (
                "launch-authorization",
                "rejected-launch-authorization-candidate",
            ),
            "logical-not",
            (),
            {},
            ("co-presence:launch-and-rejected-authorization",),
        )
    )
    gate_pass_conditions = {
        1: (("freeze-receipt", "/to_state", "FROZEN"),),
        2: (("source-manifest", "/body_sha256", "$valid-body"),),
        3: (("dependency-lock-match-receipt", "/match_verified", True),),
        4: (("production-runtime-receipt", "/body_sha256", "$valid-body"),),
        5: (("external-seed-source-receipt", "$external_authority_verified", True),),
        6: (("seed-capsule-sequence-crosscheck-receipt", "/sequence_equal", True),),
        7: (("production-schedule", "/request_count", 32_768),),
        8: (
            (
                "capacity-receipt",
                "/destination_and_auxiliary_reservation_no_double_count_verified",
                True,
            ),
        ),
        9: (("durability-receipt", "/directory_fsync_verified", True),),
        10: (("production-shard-map-receipt", "/shard_count", 32),),
        11: (
            (
                "production-runner-supervisor-qualification-receipt",
                "/all_cases_passed",
                True,
            ),
        ),
        12: (
            (
                "closed-refusal-failure-classifier-qualification-receipt",
                "/all_closed_arms_reachable",
                True,
            ),
            (
                "closed-refusal-failure-classifier-qualification-receipt",
                "/unknown_codes_rejected",
                True,
            ),
        ),
        13: (
            (
                "independent-full-32768-recomputation-qualification-receipt",
                "/repetition_blind_recomputation_verified",
                True,
            ),
            (
                "independent-full-32768-recomputation-qualification-receipt",
                "/all_cases_passed",
                True,
            ),
        ),
        14: (
            (
                "independent-554-estimate-interval-decision-path-qualification-receipt",
                "/repetition_blind_recomputation_verified",
                True,
            ),
            (
                "independent-554-estimate-interval-decision-path-qualification-receipt",
                "/all_554_estimands_supported",
                True,
            ),
            (
                "independent-554-estimate-interval-decision-path-qualification-receipt",
                "/all_cases_passed",
                True,
            ),
        ),
        15: (("power-review-signoff", "/decision", "APPROVE"),),
        16: (
            ("independent-signoff-set", "/all_required_roles_present", True),
            ("independent-signoff-set", "/all_decisions_approve", True),
            (
                "independent-signoff-set",
                "/all_signatures_mathematically_valid_under_declared_keys",
                True,
            ),
            ("independent-signoff-set", "$external_reviewer_authority_verified", True),
        ),
        17: (("launch-authorization", "$external_launch_authority_verified", True),),
    }
    for gate_ordinal, (gate_id, artifact_id) in enumerate(
        zip(_GATE_IDS, _GATE_EVIDENCE_NODES), 1
    ):
        artifact_id = {
            "independent-full-32768-recomputation-receipt": "independent-full-32768-recomputation-qualification-receipt",
            "independent-554-estimate-interval-decision-path-receipt": "independent-554-estimate-interval-decision-path-qualification-receipt",
        }.get(artifact_id, artifact_id)
        pass_children = []
        for condition_ordinal, (condition_artifact, pointer, expected) in enumerate(
            gate_pass_conditions[gate_ordinal], 1
        ):
            condition_id = "gate-pass-condition:%02d:%02d" % (
                gate_ordinal,
                condition_ordinal,
            )
            pass_children.append(condition_id)
            result.append(
                _predicate(
                    condition_id,
                    (condition_artifact,),
                    "exact-equal",
                    (pointer,),
                    {"expected": expected},
                )
            )
        gate_pass_id = "gate-pass:" + gate_id
        result.append(
            _predicate(
                gate_pass_id,
                (artifact_id,),
                "logical-and",
                (),
                {},
                tuple(pass_children),
            )
        )
        required_artifacts = (
            _authorization_required_artifacts()
            if gate_ordinal == 17
            else _GATE_REQUIRED_ARTIFACT_IDS[gate_ordinal - 1]
        )
        clauses = tuple("record:" + item for item in required_artifacts) + (
            gate_pass_id,
        )
        result.append(
            _predicate(
                "gate:" + gate_id,
                (artifact_id,),
                "logical-and",
                (),
                {"required_gate_state": "PASS"},
                clauses,
            )
        )
    operations = {record.operation_id for record in result}
    if operations != _PREDICATE_OPERATION_IDS:
        raise RuntimeError("CP65 predicate operation registry is incomplete")
    return tuple(result)


_PREDICATE_RSA_MESSAGE = b"cp65-predicate-witness-v1"
_PREDICATE_RSA_MODULUS = bytes.fromhex(
    "d6bd979dc04df9b8b2f0a44d8fedc5acc83bfac1eee9205f68064fd00348d425"
    "99f591c66350f64862ed47ef162c5047e6b099cb60bbea5b6476764b466d47d3"
    "b79b9d247fc71b1e344a72b35394973b2e0567cd405fad7837e7d3b1426b27c9"
    "76a59de3dd87490bad87cd38668cf755b77c450ae83fbb9380e5aab28096e60b0"
    "aa7aaf51d9bacf9f5ef8ccadd9639254510ca26b2b348d2599cbf3ec2e86254e4"
    "8d781fc3db4298f912c9ed72633ede902622118946d9ec9614e0930bea5b90b84"
    "45d321cc86fbca79b7ebe86020069b56503df6b890798082189f428eb77b2b347"
    "3fc434a9e46e3842a64f263b431e9a5940c165feef82eb59360db3de42e6e59d"
    "b0ee7d567cfe96076e230c72b3858931a50bd7c5c86918fa1837f8d45fa47969"
    "a40bd5fd3850c3a26079930eeec5be77ca8b0c3e988b63a2de056ab25fb95db31"
    "43ccb243c611319ef8ea44e690b9a38b542e16832db0c9f06d1ba4fb1ca06b740"
    "8fc19b6a6cdd26b02552c9a15cf146be2ab653ddacca63065db812c081"
)
_PREDICATE_RSA_SIGNATURE = bytes.fromhex(
    "0ed7516dda4866dd8dcfc283220ced5204fe50ced6c280497815251c8e71ec2f7"
    "f1765b9f056716925e9f9cd2967690b70244efc267946879dc23267e091e99ab"
    "2680981a416f60cf0c50d319442afeb90d332782538b83ac6ed07657ab65bc0f"
    "2d3e9964d549396fb89f232e91e7174fad31fbe0bba79cf87d62b1647cb80385"
    "0824ff91ab08ac429ca0a1e340a5d02903a2a2153649dd3fd9392ed0ddbfb2fa"
    "77115099a3ba982d6e3920957eb0ba4d87f6dc8cd44ac6b675b5f3adba335fd2"
    "4212fd95ad21d71fa5f7a93ac41fa4a2221984ae9a5fb50aeef35ba642216dd9"
    "ae87e3012d0e733102355f6165ab517238d4f64e1730740a0e8a7a2e37e39640"
    "a9225cc79619a0cff142c35262f46a855de4987c61b535d80840b9ca6752cdfca"
    "21167ae3328622bdd926e9c57120f1416e9dffb83e81762a4de79692c372e18e9"
    "40f8fc4f7c357b9e9cc345756def97fc3c5a13c24d9c25ae19b736e48a37398f"
    "9968b3265b4cddca6e8d12835ff9c545ebb48dcbccdf7f0bd1265534a3ea6"
)

_PREDICATE_EXECUTION_RULES: Tuple[CP65FieldRuleV1, ...] = ()
_PREDICATE_EXECUTION_PREDICATES: Tuple[CP65PredicateContractV1, ...] = ()


def _predicate_execution_catalog() -> Tuple[
    Tuple[CP65FieldRuleV1, ...], Tuple[CP65PredicateContractV1, ...]
]:
    """Return one private immutable predicate catalog for repeated evaluation."""

    global _PREDICATE_EXECUTION_RULES, _PREDICATE_EXECUTION_PREDICATES
    with _ISSUED_RECORD_LOCK:
        if not _PREDICATE_EXECUTION_RULES:
            rules = _build_field_rules()
            predicates = _build_predicates(rules)
            _PREDICATE_EXECUTION_RULES = rules
            _PREDICATE_EXECUTION_PREDICATES = predicates
        return _PREDICATE_EXECUTION_RULES, _PREDICATE_EXECUTION_PREDICATES


def _field_rule_positive_witness(
    rule: CP65FieldRuleV1,
    rules_by_id: Mapping[str, CP65FieldRuleV1],
) -> object:
    if rule.value_kind == "boolean":
        return rule.boolean_domain[0]
    if rule.value_kind == "integer":
        return rule.integer_interval[0]
    if rule.value_kind == "string":
        if rule.string_domain:
            return rule.string_domain[0]
        values = {
            "lowercase-sha256-hex": "1" * 64,
            "lowercase-hex-16": "0" * 16,
            "lowercase-hex-768": "1" * 768,
            "utc-microseconds-z": "2000-01-01T00:00:00.000000Z",
            "posix-relative-path": "x",
            "shard-id-0001-through-0032": "shard-0001",
            "attempt-id-v1": "A",
            "opaque-method-session-authority-id-v1": "a",
            "canonical-rational-threshold-v1": "0/1",
            "bounded-nonempty-ascii": "x",
        }
        value = values.get(rule.string_pattern_id, "x")
        if len(value) < rule.length_interval[0]:
            value += "x" * (rule.length_interval[0] - len(value))
        return value
    if rule.value_kind == "array":
        item_count = (
            rule.length_interval[0]
            if rule.length_interval[0] == rule.length_interval[1]
            else min(1, rule.length_interval[1])
        )
        if not rule.array_item_rule_ids:
            return [None] * item_count
        item_rules = tuple(rules_by_id[item] for item in rule.array_item_rule_ids)
        if rule.exact_object_keys:
            item = {
                key: _field_rule_positive_witness(item_rule, rules_by_id)
                for key, item_rule in zip(rule.exact_object_keys, item_rules)
            }
        else:
            item = _field_rule_positive_witness(item_rules[0], rules_by_id)
        return [item] * item_count
    if rule.value_kind == "object":
        child_by_key = {
            candidate.json_pointer.rsplit("/", 1)[-1]: candidate
            for candidate in rules_by_id.values()
            if candidate.rule_id.startswith(rule.rule_id + "/")
            and "/" not in candidate.rule_id[len(rule.rule_id) + 1 :]
        }
        return {
            key: _field_rule_positive_witness(child_by_key[key], rules_by_id)
            for key in rule.exact_object_keys
        }
    raise ValueError("field-rule witness kind is not closed")


def _predicate_direct_witness(
    predicate: CP65PredicateContractV1,
    operand: dict,
    rules_by_id: Mapping[str, CP65FieldRuleV1],
) -> Tuple[tuple, tuple]:
    predicate_id = predicate.predicate_id
    operation = predicate.operation_id
    if operation == "field-rule-satisfied":
        rule = rules_by_id[operand["rule_id"]]
        positive = _field_rule_positive_witness(rule, rules_by_id)
        invalid_by_kind = {
            "boolean": 0,
            "integer": False,
            "string": b"not-a-string",
            "array": (),
            "object": [],
        }
        return (positive,), (invalid_by_kind[rule.value_kind],)
    if operation == "exact-equal":
        expected = operand["expected"]
        invalid = (
            not expected
            if type(expected) is bool
            else (expected + 1 if type(expected) is int else str(expected) + ":invalid")
        )
        return (expected,), (invalid,)
    if operation == "member-of":
        members = operand.get("members", operand.get("string_domain", []))
        return (members[0],), ("__not-a-member__",)
    if operation == "all-equal":
        return ("x", "x"), ("x", "y")
    if operation == "contiguous-cover":
        seed_min = [1 + 64 * index for index in range(32)]
        seed_max = [64 * (index + 1) for index in range(32)]
        logical_min = [1 + 1_024 * index for index in range(32)]
        logical_max = [1_024 * (index + 1) for index in range(32)]
        negative_logical_max = list(logical_max)
        negative_logical_max[-1] -= 1
        return (
            (seed_min, seed_max, logical_min, logical_max),
            (seed_min, seed_max, logical_min, negative_logical_max),
        )
    if operation == "digest-sequence-equal":
        digest = "1" * 64
        return ([digest], [digest]), ([digest], ["2" * 64])
    if operation == "discriminated-union":
        arms = operand["arms"]
        digest = "1" * 64
        if arms[0] == "AUTHORIZATION":
            return (
                ("AUTHORIZATION", digest, ""),
                ("AUTHORIZATION", _ZERO_SHA256, ""),
            )
        if arms[0] == "STARTED":
            return (
                ("STARTED", digest, ""),
                ("STARTED", digest, "INCOMPLETE"),
            )
        return (
            (
                "PREAUTHORIZATION",
                "FROZEN",
                "INCOMPLETE",
                digest,
                digest,
                _ZERO_SHA256,
                _ZERO_SHA256,
                _ZERO_SHA256,
                digest,
                "attempt-incomplete",
            ),
            (
                "PREAUTHORIZATION",
                "STARTED",
                "INCOMPLETE",
                digest,
                digest,
                _ZERO_SHA256,
                _ZERO_SHA256,
                _ZERO_SHA256,
                digest,
                "attempt-incomplete",
            ),
        )
    if operation == "integer-formula-equal":
        return (1, 1, 163_840), (1, 2, 163_840)
    if operation == "integer-sum-equal":
        return ({"PASS": 1, "FAIL": 1}, 2), ({"PASS": 1, "FAIL": 1}, 3)
    if operation == "length-equal":
        return ([1], [2], 1), ([1], [2], 2)
    if operation == "logical-or":
        return ("AUTHORIZATION", ""), ("AUTHORIZATION", "INCOMPLETE")
    if operation == "logical-not" and predicate.input_json_pointers:
        return (True, False), (True, True)
    if operation == "not-equal":
        if "when" in operand:
            return ("AUTHORIZATION", "1" * 64), (
                "AUTHORIZATION",
                _ZERO_SHA256,
            )
        return ("1",), (operand.get("value"),)
    if operation == "ordered-equal":
        sequences = operand.get("expected_sequences")
        if sequences is not None:
            positive = tuple(list(sequence) for sequence in sequences)
            negative_last = [list(sequence) for sequence in sequences]
            negative_last[-1] = list(negative_last[-1])
            negative_last[-1][-1] += ":invalid"
            return positive, tuple(negative_last)
        expected = operand.get("expected", ["x"])
        return (list(expected),), (["__invalid__"],)
    if operation == "relative-path-template-match":
        template = operand["path_template"]
        positive = template.replace("{shard_id}", "shard-0001")
        return (positive,), (template if "{shard_id}" in template else "invalid",)
    if operation == "rsa-pss-verify":
        mutated = bytearray(_PREDICATE_RSA_SIGNATURE)
        mutated[-1] ^= 1
        return (
            (_PREDICATE_RSA_MESSAGE, _PREDICATE_RSA_MODULUS, _PREDICATE_RSA_SIGNATURE),
            (_PREDICATE_RSA_MESSAGE, _PREDICATE_RSA_MODULUS, bytes(mutated)),
        )
    if operation == "sha256-body-equal":
        body = {"body_sha256": _ZERO_SHA256}
        domain = operand["domain"].encode("ascii") + b"\0"
        digest = hashlib.sha256(domain + _plain_json_bytes(body)).hexdigest()
        return (digest, body), (_ZERO_SHA256, body)
    if operation == "sha256-raw-equal":
        raw = b"x"
        return (hashlib.sha256(raw).hexdigest(), raw), (_ZERO_SHA256, raw)
    if operation == "strictly-increasing":
        return ([1, 2],), ([1, 1],)
    if operation == "utc-interval-contained":
        return (
            (
                "2000-01-01T00:00:00.000000Z",
                "2000-01-01T00:00:01.000000Z",
                "2000-01-01T00:00:02.000000Z",
                "2000-01-01T00:00:03.000000Z",
            ),
            (
                "2000-01-01T00:00:00.000000Z",
                "2000-01-01T00:00:02.000000Z",
                "2000-01-01T00:00:02.000000Z",
                "2000-01-01T00:00:03.000000Z",
            ),
        )
    if operation == "cross-constraint-satisfied":
        constraint_id = operand["constraint_id"]
        direct_spec = next(
            (row for row in _CROSS_PREDICATE_SPECS if row[0] == constraint_id),
            None,
        )
        if direct_spec is not None:
            direct = _predicate(
                direct_spec[0],
                direct_spec[1],
                direct_spec[2],
                direct_spec[3],
                direct_spec[4],
            )
            return _predicate_direct_witness(direct, direct_spec[4], rules_by_id)
        digest = "1" * 64
        if constraint_id == "auxiliary-exclusive-root-charge-disjoint-conservation":
            return (
                (0, 34_359_738_368, 0, 34_359_738_368, 0, 34_359_738_368),
                (0, 34_359_738_368, 0, 34_359_738_368, 0, 34_359_738_367),
            )
        if constraint_id == "source-manifest-role-partitions-disjoint":
            return (
                ([{"role": "independent-recomputation-source", "relative_path": "x"}],),
                ([{"role": "production-runner-source", "relative_path": "x"}],),
            )
        if constraint_id == "independent-signoff-reviewed-summary-raw-binding":
            return (
                ([[digest], [digest], [digest], [digest]], digest),
                ([[digest], [digest], [digest], []], digest),
            )
    raise ValueError("predicate witness operation is not closed: " + predicate_id)


def _evaluate_predicate_contract(
    predicate_id: str,
    input_values: tuple,
    child_results: tuple,
) -> bool:
    """Evaluate exactly one issued predicate against caller-provided values."""

    if type(predicate_id) is not str:
        raise TypeError("predicate_id must be an exact string")
    if type(input_values) is not tuple or type(child_results) is not tuple:
        raise TypeError("predicate values and child results must be exact tuples")
    _rules, issued_predicates = _predicate_execution_catalog()
    predicates = tuple(
        predicate
        for predicate in issued_predicates
        if predicate.predicate_id == predicate_id
    )
    if len(predicates) != 1:
        raise ValueError("unknown or duplicate CP65 predicate id")
    predicate = predicates[0]
    if len(input_values) != len(predicate.input_json_pointers):
        raise ValueError("predicate input arity differs")
    if len(child_results) != len(predicate.child_predicate_ids):
        raise ValueError("predicate child arity differs")
    if any(type(result) is not bool for result in child_results):
        raise TypeError("predicate child results must be exact booleans")
    try:
        operand = json.loads(predicate.operand_json_ascii)
    except (MemoryError, ValueError) as exc:
        raise ValueError("predicate operand is not canonical JSON") from exc
    if type(operand) is not dict:
        raise ValueError("predicate operand must be an exact object")
    evaluator = _PREDICATE_EVALUATORS.get(predicate.operation_id)
    if evaluator is None:
        raise ValueError("predicate operation is not executable")
    if predicate.operation_id == "logical-and" and not input_values:
        return evaluator(child_results, operand)
    if predicate.operation_id == "logical-not" and not input_values:
        return evaluator(child_results, operand)
    evaluated = evaluator(input_values, operand)
    return bool(evaluated and all(child_results))


_PREDICATE_SYNTHETIC_INPUT_SUFFIXES = frozenset(
    {
        "$policy-reserved",
        "$external_authority_verified",
        "$external_launch_authority_verified",
        "$external_reviewer_authority_verified",
        "$signature-preimage-bytes",
        "$modulus-bytes",
        "$signature-bytes",
    }
)
_PREDICATE_DERIVED_INPUT_SUFFIXES = frozenset(
    {"$relative_path", "$present", "$raw_sha256", "$raw"}
)


def _predicate_json_pointer_value(document: object, pointer: str) -> object:
    if type(pointer) is not str or not pointer.startswith("/"):
        raise ValueError("predicate JSON pointer is not absolute")
    tokens = tuple(
        token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")
    )

    def resolve(current: object, index: int) -> object:
        if index == len(tokens):
            return current
        token = tokens[index]
        if token == "*":
            if type(current) is not list:
                raise ValueError("predicate wildcard does not select an array")
            return [resolve(item, index + 1) for item in current]
        if type(current) is dict:
            if token not in current:
                raise ValueError("predicate JSON pointer target is missing")
            return resolve(current[token], index + 1)
        if type(current) is list and token.isdigit():
            ordinal = int(token)
            if ordinal >= len(current):
                raise ValueError("predicate JSON pointer index is outside the array")
            return resolve(current[ordinal], index + 1)
        raise ValueError("predicate JSON pointer traverses a scalar")

    return resolve(document, 0)


def _evaluate_predicate_graph(
    predicate_id: str,
    documents: Mapping[str, object],
    synthetic_values: Mapping[str, object],
    *,
    _active_predicate_ids: tuple = (),
) -> bool:
    """Resolve and recursively execute one issued predicate graph root."""

    if type(predicate_id) is not str:
        raise TypeError("predicate_id must be an exact string")
    if not isinstance(documents, Mapping) or not isinstance(synthetic_values, Mapping):
        raise TypeError("predicate graph inputs must be mappings")
    if type(_active_predicate_ids) is not tuple or any(
        type(item) is not str for item in _active_predicate_ids
    ):
        raise TypeError("active predicate ids must be an exact string tuple")
    if predicate_id in _active_predicate_ids:
        raise ValueError("predicate graph contains a cycle")

    _rules, issued = _predicate_execution_catalog()
    matches = tuple(row for row in issued if row.predicate_id == predicate_id)
    if len(matches) != 1:
        raise ValueError("unknown or duplicate CP65 predicate id")
    predicate = matches[0]

    declared_synthetic = {
        pointer
        for row in issued
        for pointer in row.input_json_pointers
        if pointer.rsplit(":", 1)[-1] in _PREDICATE_SYNTHETIC_INPUT_SUFFIXES
    }
    if any(
        type(key) is not str
        or key not in declared_synthetic
        or key.rsplit(":", 1)[-1] in _PREDICATE_DERIVED_INPUT_SUFFIXES
        for key in synthetic_values
    ):
        raise ValueError("predicate synthetic input is not explicitly declared")

    def document_row(artifact_id: str) -> dict:
        if artifact_id not in documents:
            raise ValueError("predicate artifact input is missing")
        row = documents[artifact_id]
        if type(row) is not dict or set(row) != {
            "relative_path",
            "raw_bytes",
            "document",
        }:
            raise ValueError("predicate artifact input envelope differs")
        if type(row["relative_path"]) is not str or type(row["raw_bytes"]) is not bytes:
            raise ValueError("predicate artifact path/raw input type differs")
        return row

    def resolve_input(pointer: str) -> object:
        if type(pointer) is not str or not pointer:
            raise ValueError("predicate input pointer differs")
        artifact_id = ""
        selector = pointer
        if ":/" in pointer or ":$" in pointer:
            artifact_id, selector = pointer.split(":", 1)
            if artifact_id not in predicate.applies_to_artifact_ids:
                raise ValueError("predicate input artifact is outside its contract")
        elif selector.startswith("/") or selector in _PREDICATE_DERIVED_INPUT_SUFFIXES:
            if len(predicate.applies_to_artifact_ids) != 1:
                raise ValueError("predicate unqualified input artifact is ambiguous")
            artifact_id = predicate.applies_to_artifact_ids[0]

        if selector in _PREDICATE_SYNTHETIC_INPUT_SUFFIXES:
            if pointer not in synthetic_values:
                raise ValueError("predicate synthetic input is missing")
            return synthetic_values[pointer]
        if selector == "$present":
            return artifact_id in documents
        if selector == "$relative_path":
            return document_row(artifact_id)["relative_path"]
        if selector in ("$raw_sha256", "$raw"):
            # These predicate inputs denote the selected raw preimage bytes;
            # sha256-raw-equal performs the digest itself.
            return document_row(artifact_id)["raw_bytes"]
        if selector.startswith("/"):
            return _predicate_json_pointer_value(
                document_row(artifact_id)["document"], selector
            )
        raise ValueError("predicate input is neither derived nor synthetic")

    active = _active_predicate_ids + (predicate_id,)
    child_results = tuple(
        _evaluate_predicate_graph(
            child_id,
            documents,
            synthetic_values,
            _active_predicate_ids=active,
        )
        for child_id in predicate.child_predicate_ids
    )
    input_values = tuple(
        resolve_input(pointer) for pointer in predicate.input_json_pointers
    )
    return _evaluate_predicate_contract(predicate_id, input_values, child_results)


def _predicate_contract_test_vectors() -> Tuple[
    Tuple[str, tuple, tuple, tuple, tuple], ...
]:
    """Return one independently constructed positive/negative witness per predicate."""

    rules, predicates = _predicate_execution_catalog()
    rules_by_id = {rule.rule_id: rule for rule in rules}
    result = []
    for predicate in predicates:
        operand = json.loads(predicate.operand_json_ascii)
        if (
            predicate.operation_id == "logical-and"
            and not predicate.input_json_pointers
        ):
            positive_values = negative_values = ()
            positive_children = (True,) * len(predicate.child_predicate_ids)
            negative_children = (
                positive_children[:-1] + (False,) if positive_children else ()
            )
        elif (
            predicate.operation_id == "logical-not"
            and not predicate.input_json_pointers
        ):
            positive_values = negative_values = ()
            positive_children = (False,)
            negative_children = (True,)
        else:
            positive_values, negative_values = _predicate_direct_witness(
                predicate, operand, rules_by_id
            )
            positive_children = (True,) * len(predicate.child_predicate_ids)
            negative_children = positive_children
        result.append(
            (
                predicate.predicate_id,
                tuple(positive_values),
                tuple(positive_children),
                tuple(negative_values),
                tuple(negative_children),
            )
        )
    return tuple(result)


_NESTED_DIGESTS = {
    ("external-digest-preimage-registry", "entries"): (
        "entry_sha256",
        "cp65-test28-external-digest-preimage-registry-entry-v1",
    ),
    ("auxiliary-metadata-reservation", "artifact_entries"): (
        "entry_sha256",
        "cp65-test28-auxiliary-metadata-reservation-entry-v3",
    ),
    ("power-threshold-receipt", "ordered_slot_thresholds"): (
        "row_sha256",
        "cp65-test28-power-threshold-row-v1",
    ),
    ("independent-signoff-set", "ordered_signoffs"): (
        "signoff_sha256",
        "cp65-test28-independent-signoff-row-v1",
    ),
    ("reservation-manifest", "entries"): (
        "entry_sha256",
        "cp65-test28-reservation-manifest-entry-v1",
    ),
    ("production-shard-map-receipt", "shards"): (
        "shard_record_sha256",
        "cp64-test28-production-shard-map-shard-record-v1",
    ),
    ("production-schedule", "requests"): (
        "request_row_sha256",
        "cp65-test28-production-schedule-request-row-v1",
    ),
    ("independent-reviewer-public-key-set", "ordered_keys"): (
        "row_sha256",
        "cp65-test28-independent-reviewer-public-key-row-v1",
    ),
    ("shard-index", "ordered_request_entries"): (
        "row_sha256",
        "cp65-test28-shard-index-request-entry-v1",
    ),
    ("preterminal-durable-artifact-inventory", "entries"): (
        "entry_sha256",
        "cp65-test28-preterminal-durable-artifact-inventory-entry-v1",
    ),
}
_INTERNAL_DIGEST_DECLARATIONS = (
    (
        "seed-capsule-body:ordered-seed-sequence",
        "seed-capsule-body",
        "/ordered_seed_values",
        "cp64-test28-ordered-seed-sequence-v1",
        (),
        (),
    ),
    (
        "power-threshold-receipt:power-review-text",
        "power-threshold-receipt",
        "/power_review_sha256",
        "cp65-test28-power-review-text-v1",
        (),
        (),
        "exact-ascii-bytes-v1",
    ),
    (
        "power-threshold-receipt:selected-count-justification-text",
        "power-threshold-receipt",
        "/selected_count_justification_sha256",
        "cp65-test28-selected-count-justification-v1",
        (),
        (),
        "exact-ascii-bytes-v1",
    ),
    (
        "power-threshold-receipt:threshold-row-justification-text",
        "power-threshold-receipt",
        "/ordered_slot_thresholds/*/justification_sha256",
        "cp65-test28-threshold-row-justification-v1",
        (),
        (),
        "exact-ascii-bytes-v1",
    ),
    (
        "power-threshold-receipt:ordered-threshold-rows",
        "power-threshold-receipt",
        "/ordered_slot_thresholds_sha256",
        "cp65-test28-power-threshold-rows-v1",
        (),
        ("power-threshold-receipt:ordered_slot_thresholds-row-digest",),
    ),
    (
        "production-schedule:ordered-request-records",
        "production-schedule",
        "/ordered_requests_sha256",
        "cp65-test28-production-schedule-ordered-requests-v1",
        (),
        ("production-schedule:requests-row-digest",),
    ),
    (
        "source-manifest:ordered-entries",
        "source-manifest",
        "/ordered_entries_sha256",
        "cp65-test28-source-manifest-ordered-entries-v1",
        (),
        (),
    ),
    (
        "external-digest-preimage-registry:ordered-entries",
        "external-digest-preimage-registry",
        "/ordered_entries_sha256",
        "cp65-test28-external-digest-preimage-registry-ordered-entries-v1",
        (),
        ("external-digest-preimage-registry:entries-row-digest",),
    ),
    (
        "launch-authority-public-key:identity",
        "launch-authority-public-key",
        "$public_key_identity",
        "cp65-test28-launch-authority-public-key-identity-v1",
        (),
        (),
    ),
    (
        "seed-source-authority-public-key:identity",
        "seed-source-authority-public-key",
        "$public_key_identity",
        "cp65-test28-seed-source-authority-public-key-identity-v1",
        (),
        (),
    ),
    (
        "independent-reviewer-public-key-set:key-identity",
        "independent-reviewer-public-key-set",
        "/ordered_keys/*/public_key_identity_sha256",
        "cp65-test28-independent-reviewer-public-key-identity-v1",
        (),
        (),
    ),
    (
        "launch-authorization:unsigned-preimage",
        "launch-authorization",
        "$unsigned_preimage",
        "cp65-test28-launch-authorization-signature-preimage-v1",
        ("/authority_signature_hex", "/authority_signature_sha256", "/body_sha256"),
        (),
    ),
    (
        "launch-authorization:raw-signature",
        "launch-authorization",
        "/authority_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "launch-authorization-candidate:prepared-raw-sha256",
        "launch-authorization",
        "$prepared_candidate_raw_sha256",
        "",
        (),
        ("launch-authorization:body-sha256",),
        "prepared-canonical-launch-authorization-bytes-v1",
    ),
    (
        "rejected-launch-authorization-candidate:raw-sha256",
        "rejected-launch-authorization-candidate",
        "$raw_sha256",
        "",
        (),
        ("launch-authorization-candidate:prepared-raw-sha256",),
        "byte-identical-prepared-candidate-published-to-rejected-path-v1",
    ),
    (
        "seed-source-authority-attestation:unsigned-preimage",
        "seed-source-authority-attestation",
        "$unsigned_preimage",
        "cp65-test28-seed-source-authority-attestation-signature-preimage-v1",
        (
            "/source_authority_signature_hex",
            "/source_authority_signature_sha256",
            "/body_sha256",
        ),
        (),
    ),
    (
        "seed-source-authority-attestation:raw-signature",
        "seed-source-authority-attestation",
        "/source_authority_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "independent-signoff-set:row-unsigned-preimage",
        "independent-signoff-set",
        "/ordered_signoffs/*/$unsigned_preimage",
        "cp65-test28-independent-signoff-row-signature-preimage-v1",
        (
            "/ordered_signoffs/*/reviewer_signature_hex",
            "/ordered_signoffs/*/reviewer_signature_sha256",
            "/ordered_signoffs/*/signoff_sha256",
        ),
        (),
    ),
    (
        "independent-signoff-set:row-raw-signature",
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewer_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "power-review-signoff:unsigned-preimage",
        "power-review-signoff",
        "$unsigned_preimage",
        "cp65-test28-power-review-signoff-signature-preimage-v1",
        (
            "/reviewer_signature_hex",
            "/reviewer_signature_sha256",
            "/body_sha256",
        ),
        (),
    ),
    (
        "power-review-signoff:raw-signature",
        "power-review-signoff",
        "/reviewer_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "external-seed-acquisition-journal:entry",
        "external-seed-acquisition-journal",
        "$entry_sha256",
        "cp64-external-seed-acquisition-journal-entry-v1",
        (),
        (),
    ),
    (
        "external-seed-acquisition-journal:head",
        "external-seed-acquisition-journal",
        "$journal_head_sha256",
        "cp64-external-seed-acquisition-journal-head-v1",
        (),
        ("external-seed-acquisition-journal:entry",),
    ),
    (
        "sha256-manifest:ordered-entries",
        "sha256-manifest",
        "/ordered_entries_sha256",
        "cp65-test28-sha256-manifest-ordered-entries-v1",
        (),
        (),
    ),
    (
        "preterminal-durable-artifact-inventory:ordered-entries",
        "preterminal-durable-artifact-inventory",
        "/ordered_entries_sha256",
        "cp65-test28-preterminal-durable-artifact-inventory-ordered-entries-v1",
        (),
        ("preterminal-durable-artifact-inventory:entries-row-digest",),
    ),
    (
        "source-manifest:selected-entry-raw-sha256",
        "source-manifest",
        "/entries/*/sha256",
        "",
        (),
        (),
        "path-selected-retained-raw-file-v1",
    ),
    (
        "preterminal-durable-artifact-inventory:selected-entry-raw-sha256",
        "preterminal-durable-artifact-inventory",
        "/entries/*/sha256",
        "",
        (),
        (),
        "path-selected-retained-raw-file-v1",
    ),
    (
        "sha256-manifest:selected-entry-raw-sha256",
        "sha256-manifest",
        "/entries/*/sha256",
        "",
        (),
        (),
        "path-selected-retained-raw-file-v1",
    ),
    (
        "external-digest-preimage-registry:selected-target-raw-sha256",
        "external-digest-preimage-registry",
        "/entries/*/target_artifact_raw_sha256",
        "",
        (),
        (),
        "registry-selected-target-raw-file-v1",
    ),
    (
        "external-digest-preimage-registry:declared-preimage-sha256",
        "external-digest-preimage-registry",
        "/entries/*/digest_sha256",
        "",
        (),
        (),
        "registry-row-declared-preimage-v1",
    ),
    (
        "production-schema-preimage-validator-bundle:schema-semantic-sha256",
        "production-schema-preimage-validator-bundle",
        "$schema_semantic_sha256",
        "cp65-test28-production-schema-semantic-v1",
        (),
        (),
    ),
    (
        "production-schema-preimage-validator-bundle:auxiliary-size-proof-record-sha256",
        "production-schema-preimage-validator-bundle",
        "$auxiliary_size_proof.record_sha256",
        "cp65-auxiliary-size-proof-v1",
        (),
        (),
    ),
    (
        "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/bundle/capacity_receipt_schema/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp61-stable-design-semantic-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_validated_mc_design/bundle/stable_design_semantic_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp64-candidate-shard-policy-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/bundle/candidate_shard_policy/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp64-durability-receipt-schema-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/bundle/durability_receipt_schema/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp63-schedule-contract-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/runner_bundle/canonical_record/fields/schedule_contract/fields/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp62-supervisor-contract-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/supervisor_contract/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp63-raw-record-schema-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/runner_bundle/canonical_record/fields/raw_record_schema/fields/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp62-projection-contract-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/stable_trace_projection/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp62-runtime-lock-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/runtime_source_abi_lock/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "source-manifest:independent-recomputation-submanifest",
        "source-manifest",
        "$independent_recomputation_source_submanifest_sha256",
        "cp65-test28-independent-recomputation-source-submanifest-v1",
        (),
        ("source-manifest:selected-entry-raw-sha256",),
        "role-filtered-ordered-source-manifest-submanifest-v1",
    ),
    (
        "independent-reviewer-public-key-set:selected-reviewer-identity-sha256",
        "independent-reviewer-public-key-set",
        "$selected_reviewer_identity_sha256",
        "",
        (),
        (
            "external-preimage:independent-reviewer-public-key-set:/ordered_keys/*/reviewer_identity_sha256",
        ),
        "role-selected-stored-digest-field-v1",
    ),
    (
        "production-schedule:cp62-seed-free-request-sha256",
        "production-schedule",
        "/requests/*/seed_free_request_sha256",
        "cp62-test28-seed-free-request-v1",
        (),
        (),
    ),
    (
        "production-schedule:request-instance-sha256",
        "production-schedule",
        "/requests/*/request_instance_sha256",
        "cp63-test28-bound-request-v1",
        (),
        (),
    ),
    (
        "shard-index:request-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/request_sha256",
        "",
        (),
        (),
        "offset-length-selected-payload-bytes-v1",
    ),
    (
        "shard-index:raw-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/raw_sha256",
        "",
        (),
        (),
        "offset-length-selected-payload-bytes-v1",
    ),
    (
        "shard-index:stable-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/stable_sha256",
        "",
        (),
        (),
        "offset-length-selected-payload-bytes-v1",
    ),
    (
        "shard-index:stderr-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/stderr_sha256",
        "",
        (),
        (),
        "length-frame-selected-payload-bytes-v1",
    ),
    (
        "shard-index:rng-initial-state-row-sha256",
        "shard-index",
        "/ordered_request_entries/*/rng_initial_sha256",
        "",
        (),
        (),
        "ordered-rng-container-state-row-v1",
    ),
    (
        "shard-index:rng-final-state-row-sha256",
        "shard-index",
        "/ordered_request_entries/*/rng_final_sha256",
        "",
        (),
        (),
        "ordered-rng-container-state-row-v1",
    ),
    (
        "preflight-gate-summary:selected-evidence-raw-sha256",
        "preflight-gate-summary",
        "/ordered_evidence_receipt_sha256s/*",
        "",
        (),
        (),
        "gate-ordinal-selected-retained-raw-file-v1",
    ),
    (
        "production-shard-map-receipt:selected-reservation-entry-sha256",
        "production-shard-map-receipt",
        "/shards/*/per_file_reservation_manifest_entry_sha256s/*",
        "cp65-test28-reservation-manifest-entry-v1",
        (),
        (),
    ),
    (
        "external-seed-acquisition-journal:ordered-seed-values-commitment",
        "external-seed-acquisition-journal",
        "$ordered_seed_values_commitment_sha256",
        "cp64-test28-ordered-seed-sequence-v1",
        (),
        ("external-seed-acquisition-journal:head",),
    ),
    (
        "auxiliary-reservation-transition-journal:head0",
        "auxiliary-reservation-transition-journal",
        "$header.head0_sha256",
        "cp65-test28-auxiliary-reservation-transition-head-v1",
        (),
        (),
    ),
    (
        "auxiliary-reservation-transition-journal:preinventory-prefix",
        "auxiliary-reservation-transition-journal",
        "$preinventory_prefix.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:head0",),
    ),
    (
        "auxiliary-reservation-transition-journal:after-inventory",
        "auxiliary-reservation-transition-journal",
        "$after_inventory.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:preinventory-prefix",),
    ),
    (
        "auxiliary-reservation-transition-journal:after-terminal",
        "auxiliary-reservation-transition-journal",
        "$after_terminal.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:after-inventory",),
    ),
    (
        "auxiliary-reservation-transition-journal:final-head",
        "auxiliary-reservation-transition-journal",
        "$final.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:after-terminal",),
    ),
)


def _digest_contract(
    contract_id: str,
    artifact_id: str,
    pointer: str,
    domain: str,
    zeroed: Tuple[str, ...],
    components: Tuple[str, ...],
    canonical_profile_id: str = "",
) -> CP65DigestPreimageContractV1:
    return cast(
        CP65DigestPreimageContractV1,
        _record(
            CP65DigestPreimageContractV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "contract_id": contract_id,
                "artifact_id": artifact_id,
                "digest_field_pointer": pointer,
                "algorithm_id": "sha256",
                "domain_separator": domain + ("\0" if domain else ""),
                "canonical_profile_id": canonical_profile_id
                or (_CANONICAL_PROFILE_ID if domain else "exact-raw-bytes-v1"),
                "zeroed_field_pointers": zeroed,
                "ordered_component_ids": components,
                "output_encoding": "64-lowercase-hex",
                "output_bytes": 32,
                "verifier_implemented": True,
                "definition_only": True,
            },
        ),
    )


def _is_sha256_field_rule(rule: CP65FieldRuleV1) -> bool:
    parts = rule.json_pointer.split("/")
    leaf = parts[-1]
    parent = parts[-2] if len(parts) > 1 else ""
    return (
        leaf == "sha256"
        or leaf.endswith("_sha256")
        or (leaf == "*" and parent.endswith("_sha256s"))
    )


def _intrinsic_owned_sha256_pointer_keys() -> frozenset:
    keys = {
        (
            artifact_id,
            "/%s/*/%s" % (array_key, digest_key),
        )
        for (artifact_id, array_key), (digest_key, _domain) in _NESTED_DIGESTS.items()
    }
    keys.update(
        (artifact_id, pointer)
        for (
            _contract_id,
            artifact_id,
            pointer,
            _domain,
            _zeroed,
            _components,
            *_rest,
        ) in _INTERNAL_DIGEST_DECLARATIONS
        if pointer.startswith("/")
    )
    keys.update(
        (artifact_id, "/body_sha256")
        for artifact_id, _path, _scope, _media, artifact_keys, *_rest in _ARTIFACT_DECLARATIONS
        if "body_sha256" in artifact_keys
        and artifact_id != "rejected-launch-authorization-candidate"
    )
    return frozenset(keys)


def _sha256_pointer_is_intrinsic_owned(
    row: CP65Sha256PointerContractV1,
) -> bool:
    if type(row) is not CP65Sha256PointerContractV1:
        raise TypeError("SHA256 pointer row has the wrong exact type")
    return (
        row.target_artifact_id,
        row.target_json_pointer,
    ) in _intrinsic_owned_sha256_pointer_keys()


def _external_preimage_contract_id(artifact_id: str, pointer: str) -> str:
    if (artifact_id, pointer,) == (
        "auxiliary-metadata-reservation",
        "/exclusive_root_charge_measurement_sha256",
    ):
        return (
            "auxiliary-metadata-reservation:" "exclusive-root-charge-measurement-sha256"
        )
    return "external-preimage:%s:%s" % (artifact_id, pointer)


# Exact semantic field names whose stored digest is the raw retained bytes of
# the named artifact.  This is a closed mapping, not a suffix/name heuristic:
# an unlisted SHA pointer fails bundle construction below.
_RAW_ARTIFACT_SHA256_FIELD_SOURCES = {
    "protocol_sha256": "frozen-protocol",
    "machine_manifest_sha256": "frozen-machine-manifest",
    "bound_files_sha256": "source-manifest",
    "source_manifest_sha256": "source-manifest",
    "writer_source_manifest_sha256": "source-manifest",
    "runner_source_manifest_sha256": "source-manifest",
    "classifier_source_manifest_sha256": "source-manifest",
    "frozen_source_fixture_materialization_sha256": "frozen-source-fixture-materialization",
    "dependency_lock_sha256": "dependency-lock",
    "expected_sha256": "dependency-lock",
    "observed_sha256": "dependency-lock",
    "power_threshold_receipt_sha256": "power-threshold-receipt",
    "launch_authority_public_key_sha256": "launch-authority-public-key",
    "independent_reviewer_public_key_set_sha256": "independent-reviewer-public-key-set",
    "seed_source_authority_public_key_sha256": "seed-source-authority-public-key",
    "production_receipt_schema_bundle_sha256": "production-schema-preimage-validator-bundle",
    "capacity_schema_sha256": "production-schema-preimage-validator-bundle",
    "freeze_receipt_sha256": "freeze-receipt",
    "seed_source_receipt_sha256": "external-seed-source-receipt",
    "source_receipt_sha256": "external-seed-source-receipt",
    "schedule_sha256": "production-schedule",
    "production_schedule_sha256": "production-schedule",
    "production_runtime_receipt_sha256": "production-runtime-receipt",
    "runtime_receipt_sha256": "production-runtime-receipt",
    "capacity_receipt_sha256": "capacity-receipt",
    "durability_receipt_sha256": "durability-receipt",
    "production_shard_map_receipt_sha256": "production-shard-map-receipt",
    "shard_map_receipt_sha256": "production-shard-map-receipt",
    "preflight_gate_summary_sha256": "preflight-gate-summary",
    "independent_signoff_sha256": "independent-signoff-set",
    "launch_authorization_sha256": "launch-authorization",
    "postauthorization_outcome_sha256": "postauthorization-outcome",
    "started_receipt_sha256": "started-receipt",
    "terminal_state_sha256": "terminal-state",
    "sha256_manifest_sha256": "sha256-manifest",
    "auxiliary_metadata_reservation_sha256": "auxiliary-metadata-reservation",
    "auxiliary_metadata_reservation_artifact_sha256": "auxiliary-metadata-reservation",
    "reservation_manifest_sha256": "reservation-manifest",
    "external_digest_preimage_registry_sha256": "external-digest-preimage-registry",
    "reviewer_public_key_set_sha256": "independent-reviewer-public-key-set",
    "source_authority_attestation_sha256": "seed-source-authority-attestation",
    "acquisition_journal_sha256": "external-seed-acquisition-journal",
    "custody_artifact_sha256": "seed-source-custody-artifact",
    "seed_source_custody_artifact_sha256": "seed-source-custody-artifact",
    "reviewer_signoff_sha256": "power-review-signoff",
    "preauthorization_outcome_sha256": "preauthorization-outcome",
    "durable_artifact_inventory_sha256": "preterminal-durable-artifact-inventory",
    "shard_index_sha256": "shard-index",
    "requests_file_sha256": "shard-requests",
    "raw_file_sha256": "shard-raw-records",
    "stable_file_sha256": "shard-stable-traces",
    "stderr_file_sha256": "shard-stderr-records",
    "rng_initial_file_sha256": "shard-rng-initial-states",
    "rng_final_file_sha256": "shard-rng-final-states",
}

_BODY_ARTIFACT_SHA256_FIELD_SOURCES = {
    "acquisition_start_receipt_sha256": "external-seed-acquisition-start-receipt",
    "acquisition_session_sha256": "external-seed-acquisition-start-receipt",
    "seed_capsule_body_sha256": "seed-capsule-body",
}


def _source_contract_for_artifact(artifact_id: str, *, body: bool = False) -> str:
    return artifact_id + (":body-sha256" if body else ":raw-sha256")


# Pointers whose source is neither the uniform raw/body field mapping above
# nor their own digest contract.  Values are exact source contract IDs.
_SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES = {
    (
        "capacity-receipt",
        "/capacity_schema_sha256",
    ): "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
    (
        "auxiliary-metadata-reservation",
        "/capacity_schema_sha256",
    ): "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
    (
        "reservation-manifest",
        "/capacity_schema_sha256",
    ): "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
    (
        "external-seed-source-receipt",
        "/cp61_stable_design_sha256",
    ): "v15-machine-manifest:cp61-stable-design-semantic-sha256",
    (
        "seed-capsule-body",
        "/cp61_stable_design_sha256",
    ): "v15-machine-manifest:cp61-stable-design-semantic-sha256",
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "/estimand_contract_sha256",
    ): "v15-machine-manifest:cp61-stable-design-semantic-sha256",
    (
        "production-shard-map-receipt",
        "/candidate_shard_policy_sha256",
    ): "v15-machine-manifest:cp64-candidate-shard-policy-record-sha256",
    (
        "durability-receipt",
        "/layout_contract_sha256",
    ): "v15-machine-manifest:cp64-durability-receipt-schema-record-sha256",
    (
        "production-schedule",
        "/schedule_contract_sha256",
    ): "v15-machine-manifest:cp63-schedule-contract-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/production_schedule_contract_sha256",
    ): "v15-machine-manifest:cp63-schedule-contract-record-sha256",
    (
        "production-runner-supervisor-qualification-receipt",
        "/supervisor_contract_sha256",
    ): "v15-machine-manifest:cp62-supervisor-contract-record-sha256",
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "/supervisor_contract_sha256",
    ): "v15-machine-manifest:cp62-supervisor-contract-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/raw_record_schema_sha256",
    ): "v15-machine-manifest:cp63-raw-record-schema-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/stable_projection_schema_sha256",
    ): "v15-machine-manifest:cp62-projection-contract-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/independent_recomputation_source_manifest_sha256",
    ): "source-manifest:independent-recomputation-submanifest",
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "/independent_source_manifest_sha256",
    ): "source-manifest:independent-recomputation-submanifest",
    (
        "external-digest-preimage-registry",
        "/schema_semantic_sha256",
    ): "production-schema-preimage-validator-bundle:schema-semantic-sha256",
    (
        "external-digest-preimage-registry",
        "/ordered_entry_sha256s/*",
    ): "external-digest-preimage-registry:entries-row-digest",
    (
        "production-schedule",
        "/requests/*/seed_capsule_body_sha256",
    ): "seed-capsule-body:body-sha256",
    (
        "production-schedule",
        "/requests/*/runtime_lock_sha256",
    ): "v15-machine-manifest:cp62-runtime-lock-record-sha256",
    (
        "production-schedule",
        "/ordered_request_record_sha256s/*",
    ): "production-schedule:requests-row-digest",
    (
        "power-threshold-receipt",
        "/ordered_slot_threshold_row_sha256s/*",
    ): "power-threshold-receipt:ordered_slot_thresholds-row-digest",
    (
        "power-review-signoff",
        "/power_review_sha256",
    ): "power-threshold-receipt:power-review-text",
    (
        "power-review-signoff",
        "/selected_count_justification_sha256",
    ): "power-threshold-receipt:selected-count-justification-text",
    (
        "power-review-signoff",
        "/ordered_slot_thresholds_sha256",
    ): "power-threshold-receipt:ordered-threshold-rows",
    (
        "power-review-signoff",
        "/ordered_slot_threshold_row_sha256s/*",
    ): "power-threshold-receipt:ordered_slot_thresholds-row-digest",
    (
        "preflight-gate-summary",
        "/ordered_evidence_receipt_sha256s/*",
    ): "preflight-gate-summary:selected-evidence-raw-sha256",
    (
        "independent-reviewer-public-key-set",
        "/ordered_public_key_identity_sha256s/*",
    ): "independent-reviewer-public-key-set:key-identity",
    (
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewed_artifact_sha256s/*",
    ): "preflight-gate-summary:raw-sha256",
    (
        "production-shard-map-receipt",
        "/shards/*/per_file_reservation_manifest_entry_sha256s/*",
    ): "reservation-manifest:entries-row-digest",
    (
        "shard-index",
        "/shard_record_sha256",
    ): "production-shard-map-receipt:shards-row-digest",
    (
        "launch-authorization",
        "/authority_identity_sha256",
    ): "launch-authority-public-key:identity",
    (
        "rejected-launch-authorization-candidate",
        "/authority_identity_sha256",
    ): "launch-authority-public-key:identity",
    (
        "seed-source-authority-attestation",
        "/source_authority_identity_sha256",
    ): "seed-source-authority-public-key:identity",
    (
        "power-review-signoff",
        "/reviewer_public_key_identity_sha256",
    ): "independent-reviewer-public-key-set:key-identity",
    (
        "power-review-signoff",
        "/reviewer_identity_sha256",
    ): "independent-reviewer-public-key-set:selected-reviewer-identity-sha256",
    (
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewer_public_key_identity_sha256",
    ): "independent-reviewer-public-key-set:key-identity",
    (
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewer_identity_sha256",
    ): "independent-reviewer-public-key-set:selected-reviewer-identity-sha256",
    (
        "external-seed-source-receipt",
        "/acquisition_journal_head_sha256",
    ): "external-seed-acquisition-journal:head",
    (
        "partial-seed-acquisition-terminal-receipt",
        "/acquisition_journal_head_sha256",
    ): "external-seed-acquisition-journal:head",
    (
        "seed-source-authority-attestation",
        "/acquisition_journal_head_sha256",
    ): "external-seed-acquisition-journal:head",
    (
        "seed-source-authority-attestation",
        "/ordered_seed_values_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "external-seed-source-receipt",
        "/ordered_seed_values_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "partial-seed-acquisition-terminal-receipt",
        "/ordered_partial_seed_values_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "seed-capsule-sequence-crosscheck-receipt",
        "/source_sequence_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "seed-capsule-sequence-crosscheck-receipt",
        "/capsule_sequence_commitment_sha256",
    ): "seed-capsule-body:ordered-seed-sequence",
    (
        "preterminal-durable-artifact-inventory",
        "/auxiliary_transition_journal_prefix_head_sha256",
    ): "auxiliary-reservation-transition-journal:preinventory-prefix",
    (
        "terminal-state",
        "/auxiliary_transition_journal_after_inventory_head_sha256",
    ): "auxiliary-reservation-transition-journal:after-inventory",
    (
        "sha256-manifest",
        "/auxiliary_transition_journal_after_terminal_head_sha256",
    ): "auxiliary-reservation-transition-journal:after-terminal",
    (
        "committed-marker",
        "/auxiliary_reservation_transition_journal_final_head_sha256",
    ): "auxiliary-reservation-transition-journal:final-head",
    (
        "committed-marker",
        "/auxiliary_reservation_transition_journal_sha256",
    ): "auxiliary-reservation-transition-journal:raw-sha256",
    (
        "committed-marker",
        "/hold_device_identity_sha256",
    ): "external-preimage:auxiliary-metadata-reservation:/hold_device_identity_sha256",
    (
        "committed-marker",
        "/hold_extent_map_sha256",
    ): "external-preimage:auxiliary-metadata-reservation:/hold_extent_map_sha256",
    (
        "capacity-receipt",
        "/auxiliary_artifact_size_proof_sha256",
    ): "production-schema-preimage-validator-bundle:auxiliary-size-proof-record-sha256",
    ("launch-receipt", "/runner_source_manifest_sha256"): "source-manifest:raw-sha256",
    (
        "preauthorization-outcome",
        "/prepared_launch_authorization_sha256",
    ): "launch-authorization-candidate:prepared-raw-sha256",
}


_EXTERNAL_REGISTRY_SHA256_POINTERS = frozenset(
    {
        ("auxiliary-metadata-reservation", "/measurement_session_sha256"),
        (
            "auxiliary-metadata-reservation",
            "/exclusive_root_charge_measurement_sha256",
        ),
        ("auxiliary-metadata-reservation", "/storage_root_identity_sha256"),
        ("auxiliary-metadata-reservation", "/filesystem_identity_sha256"),
        ("auxiliary-metadata-reservation", "/hold_device_identity_sha256"),
        ("auxiliary-metadata-reservation", "/hold_extent_map_sha256"),
        (
            "auxiliary-metadata-reservation",
            "/artifact_entries/*/device_identity_sha256",
        ),
        (
            "auxiliary-metadata-reservation",
            "/artifact_entries/*/extent_map_sha256",
        ),
        ("capacity-receipt", "/storage_root_identity_sha256"),
        ("capacity-receipt", "/filesystem_identity_sha256"),
        ("capacity-receipt", "/measurement_session_sha256"),
        ("durability-receipt", "/filesystem_identity_sha256"),
        ("durability-receipt", "/qualification_session_sha256"),
        (
            "external-seed-acquisition-start-receipt",
            "/acquisition_journal_device_identity_sha256",
        ),
        (
            "external-seed-acquisition-start-receipt",
            "/acquisition_journal_extent_map_sha256",
        ),
        (
            "external-seed-acquisition-start-receipt",
            "/acquisition_journal_inode_recheck_sha256",
        ),
        ("freeze-receipt", "/freezer_identity_sha256"),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/qualification_fixture_set_sha256",
        ),
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/qualification_fixture_set_sha256",
        ),
        (
            "independent-reviewer-public-key-set",
            "/ordered_keys/*/reviewer_identity_sha256",
        ),
        (
            "production-runner-supervisor-qualification-receipt",
            "/qualification_fixture_set_sha256",
        ),
        ("production-runtime-receipt", "/abi_map_sha256"),
        ("production-runtime-receipt", "/environment_sha256"),
        ("production-runtime-receipt", "/loaded_local_source_closure_sha256"),
        ("production-runtime-receipt", "/numpy_payload_closure_sha256"),
        ("production-runtime-receipt", "/numpy_record_sha256"),
        ("production-runtime-receipt", "/observation_session_sha256"),
        ("production-runtime-receipt", "/python_executable_sha256"),
        ("production-runtime-receipt", "/python_framework_sha256"),
        ("production-runtime-receipt", "/scipy_payload_closure_sha256"),
        ("production-runtime-receipt", "/scipy_record_sha256"),
        ("production-runtime-receipt", "/stdlib_closure_sha256"),
        ("reservation-manifest", "/measurement_session_sha256"),
        ("reservation-manifest", "/storage_root_identity_sha256"),
        ("reservation-manifest", "/filesystem_identity_sha256"),
        ("reservation-manifest", "/entries/*/device_identity_sha256"),
        ("reservation-manifest", "/entries/*/extent_map_sha256"),
        ("seed-source-custody-artifact", "/custody_payload_sha256"),
        ("seed-source-custody-artifact", "/retention_location_identity_sha256"),
    }
)


def _sha256_pointer_source_contract_id(
    artifact_id: str,
    pointer: str,
    contracts_by_target: Mapping[Tuple[str, str], str],
) -> str:
    """Resolve one frozen SHA pointer to exactly one preimage contract."""

    key = (artifact_id, pointer)
    override = _SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES.get(key)
    if override is not None:
        return override
    if key in _EXTERNAL_REGISTRY_SHA256_POINTERS:
        return _external_preimage_contract_id(*key)
    own = contracts_by_target.get(key)
    if own is not None:
        return own
    if artifact_id == "rejected-launch-authorization-candidate":
        launch_key = ("launch-authorization", pointer)
        source = contracts_by_target.get(launch_key)
        if source is not None:
            return source
        return _sha256_pointer_source_contract_id(
            launch_key[0], launch_key[1], contracts_by_target
        )
    leaf = pointer.rsplit("/", 1)[-1]
    raw_artifact = _RAW_ARTIFACT_SHA256_FIELD_SOURCES.get(leaf)
    if raw_artifact is not None:
        return _source_contract_for_artifact(raw_artifact)
    body_artifact = _BODY_ARTIFACT_SHA256_FIELD_SOURCES.get(leaf)
    if body_artifact is not None:
        return _source_contract_for_artifact(body_artifact, body=True)
    raise RuntimeError(
        "unclassified CP65 SHA256 pointer: %s%s" % (artifact_id, pointer)
    )


def _build_digest_contracts(
    field_rules: Tuple[CP65FieldRuleV1, ...] = (),
) -> Tuple[CP65DigestPreimageContractV1, ...]:
    if set(_SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES).intersection(
        _EXTERNAL_REGISTRY_SHA256_POINTERS
    ):
        raise RuntimeError("CP65 exact SHA route also appears in registry allowlist")
    result = []
    nested_ids = {}
    for (artifact_id, key), (_digest_key, domain) in _NESTED_DIGESTS.items():
        contract_id = "%s:%s-row-digest" % (artifact_id, key)
        nested_ids.setdefault(artifact_id, []).append(contract_id)
        components = (
            ("power-threshold-receipt:threshold-row-justification-text",)
            if (artifact_id, key)
            == ("power-threshold-receipt", "ordered_slot_thresholds")
            else ()
        )
        result.append(
            _digest_contract(
                contract_id,
                artifact_id,
                "/%s/*/%s" % (key, _digest_key),
                domain,
                ("/%s/*/%s" % (key, _digest_key),),
                components,
            )
        )
    internal_by_artifact = {}
    for declaration in _INTERNAL_DIGEST_DECLARATIONS:
        internal_by_artifact.setdefault(declaration[1], []).append(declaration[0])
        result.append(_digest_contract(*declaration))
    for (
        artifact_id,
        _path,
        _scope,
        _media,
        keys,
        _nested,
        domain,
        _preserved,
    ) in _ARTIFACT_DECLARATIONS:
        if artifact_id == "rejected-launch-authorization-candidate":
            continue
        has_body = "body_sha256" in keys
        body_internal_components = tuple(
            contract_id
            for contract_id in internal_by_artifact.get(artifact_id, ())
            if contract_id != "launch-authorization-candidate:prepared-raw-sha256"
        )
        components = tuple(nested_ids.get(artifact_id, ())) + body_internal_components
        result.append(
            _digest_contract(
                artifact_id + (":body-sha256" if has_body else ":raw-sha256"),
                artifact_id,
                "/body_sha256" if has_body else "$raw_sha256",
                domain if has_body else "",
                ("/body_sha256",) if has_body else (),
                components,
            )
        )
        if has_body:
            result.append(
                _digest_contract(
                    artifact_id + ":raw-sha256",
                    artifact_id,
                    "$raw_sha256",
                    "",
                    (),
                    (artifact_id + ":body-sha256",),
                )
            )
    owned = {
        (contract.artifact_id, contract.digest_field_pointer) for contract in result
    }
    sha_keys = tuple(
        (rule.artifact_id, rule.json_pointer)
        for rule in field_rules
        if _is_sha256_field_rule(rule)
    )
    unknown_registry_keys = _EXTERNAL_REGISTRY_SHA256_POINTERS - set(sha_keys)
    if unknown_registry_keys:
        raise RuntimeError("CP65 external-registry SHA pointer is not a field rule")
    for artifact_id, pointer in sorted(_EXTERNAL_REGISTRY_SHA256_POINTERS):
        if (artifact_id, pointer) in owned:
            raise RuntimeError("CP65 intrinsic SHA pointer cannot use the registry")
        result.append(
            _digest_contract(
                _external_preimage_contract_id(artifact_id, pointer),
                artifact_id,
                pointer,
                (
                    "cp65-test28-exclusive-root-charge-measurement-v1"
                    if (
                        artifact_id,
                        pointer,
                    )
                    == (
                        "auxiliary-metadata-reservation",
                        "/exclusive_root_charge_measurement_sha256",
                    )
                    else ""
                ),
                (),
                (),
                "external-registry-exact-preimage-v1",
            )
        )
        owned.add((artifact_id, pointer))
    by_target = {
        (contract.artifact_id, contract.digest_field_pointer): contract.contract_id
        for contract in result
    }
    available_ids = {contract.contract_id for contract in result}
    for artifact_id, pointer in sha_keys:
        key = (artifact_id, pointer)
        if key in owned:
            continue
        source_contract_id = _sha256_pointer_source_contract_id(
            artifact_id, pointer, by_target
        )
        if source_contract_id not in available_ids:
            raise RuntimeError("CP65 SHA pointer source contract is unresolved")
    return tuple(result)


def _build_artifact_schemas(
    field_rules: Tuple[CP65FieldRuleV1, ...],
) -> Tuple[CP65ArtifactSchemaV1, ...]:
    by_artifact = {}
    for rule in field_rules:
        by_artifact.setdefault(rule.artifact_id, []).append(rule.rule_id)
    result = []
    for (
        artifact_id,
        path,
        scope,
        media,
        keys,
        _nested,
        _domain,
        preserved,
    ) in _ARTIFACT_DECLARATIONS:
        maximum_instances = 32 if scope == "per-shard" else 1
        final_newline = "none"
        if media == "sha256-text":
            final_newline = "exactly-one-lf"
        elif media == "referenced-predecessor-jsonl":
            final_newline = "one-lf-per-record-including-final-record"
        elif media in (
            "binary-journal",
            "binary-transition-journal",
            "referenced-predecessor-binary-frames",
        ):
            final_newline = "not-applicable-no-trailing-bytes"
        result.append(
            cast(
                CP65ArtifactSchemaV1,
                _record(
                    CP65ArtifactSchemaV1,
                    {
                        "schema_version": CP65_TEST28_SCHEMA_VERSION,
                        "artifact_id": artifact_id,
                        "path_template": path,
                        "path_scope": scope,
                        "presence_rule_id": "presence:" + artifact_id,
                        "encoding": "ascii-canonical-json"
                        if "canonical-json" in media
                        else "exact-bytes",
                        "media_kind": media,
                        "exact_keys": keys,
                        "field_rule_ids": tuple(by_artifact.get(artifact_id, ())),
                        "record_rule_id": "record:" + artifact_id,
                        "minimum_instances": 0,
                        "maximum_instances": maximum_instances,
                        "minimum_bytes_per_instance": _artifact_minimum_bytes(
                            artifact_id, bool(keys)
                        ),
                        "maximum_bytes_per_instance": _artifact_maximum_bytes(
                            artifact_id
                        ),
                        "final_newline_rule": final_newline,
                        "digest_preimage_contract_id": (
                            "launch-authorization:body-sha256"
                            if artifact_id == "rejected-launch-authorization-candidate"
                            else artifact_id
                            + (
                                ":body-sha256"
                                if "body_sha256" in keys
                                else ":raw-sha256"
                            )
                        ),
                        "dag_node_ids": (
                            (
                                (
                                    "digest:launch-authorization:body-sha256",
                                    _primary_raw_node(artifact_id),
                                )
                                if artifact_id
                                == "rejected-launch-authorization-candidate"
                                else (
                                    _body_node(artifact_id),
                                    _primary_raw_node(artifact_id),
                                )
                                if "body_sha256" in keys
                                else (_primary_raw_node(artifact_id),)
                            )
                        ),
                        "auxiliary_reservation_class": "destination-reservation"
                        if artifact_id
                        in (
                            "shard-requests",
                            "shard-raw-records",
                            "shard-stable-traces",
                            "shard-stderr-records",
                        )
                        else "exclusive-auxiliary-metadata-reservation",
                        "cp64_contract_preserved": preserved,
                        "definition_only": True,
                    },
                ),
            )
        )
    return tuple(result)


def _expanded_final_path_rows() -> Tuple[Tuple[str, str, int], ...]:
    """Expand the exact retained final-path roster in canonical path order."""

    rows = []
    for artifact_id, path, scope, *_rest in _ARTIFACT_DECLARATIONS:
        if scope == "per-shard":
            for shard_ordinal in range(1, 33):
                rows.append(
                    (
                        artifact_id,
                        path.replace("{shard_id}", "shard-%04d" % shard_ordinal),
                        shard_ordinal,
                    )
                )
        else:
            rows.append((artifact_id, path, 0))
    rows.sort(key=lambda row: row[1])
    if len(rows) != 312 or len({row[1] for row in rows}) != 312:
        raise RuntimeError("CP65 expanded final-path roster differs")
    return tuple(rows)


def _build_transient_path_contracts() -> Tuple[CP65TransientPathContractV1, ...]:
    """Build the exact collision-free transient namespace."""

    rows = []
    final_by_artifact_and_path = {
        (artifact_id, path): shard_ordinal
        for artifact_id, path, shard_ordinal in _expanded_final_path_rows()
    }
    for artifact_id in _DESTINATION_IDS:
        template = _ARTIFACT_BY_ID[artifact_id][1]
        for shard_ordinal in range(1, 33):
            final_path = template.replace("{shard_id}", "shard-%04d" % shard_ordinal)
            rows.append(
                (
                    artifact_id,
                    final_path,
                    "",
                    final_path + ".partial",
                    "per-shard",
                    shard_ordinal,
                    "destination-reserved-partial",
                    False,
                    "UNCONDITIONAL",
                    "",
                )
            )
    for (
        artifact_id,
        final_path,
        alternate_final_path,
        _logical,
        _reserved,
        primary_arm,
        alternate_arm,
    ) in _auxiliary_expected_slots():
        if artifact_id in (
            "committed-marker",
            "auxiliary-reservation-transition-journal",
        ):
            continue
        shard_ordinal = final_by_artifact_and_path[(artifact_id, final_path)]
        rows.append(
            (
                artifact_id,
                final_path,
                alternate_final_path,
                final_path + ".partial",
                _ARTIFACT_BY_ID[artifact_id][2],
                shard_ordinal,
                "auxiliary-partial-candidate",
                artifact_id == "launch-authorization",
                primary_arm,
                alternate_arm,
            )
        )
    rows.append(
        (
            "__auxiliary_dynamic_hold__",
            "",
            "",
            ".cp65_auxiliary_reservation_hold.partial",
            "global",
            0,
            "dynamic-auxiliary-reservation-hold",
            False,
            "",
            "",
        )
    )
    rows.sort(key=lambda row: row[3])
    if len(rows) != 310 or len({row[3] for row in rows}) != 310:
        raise RuntimeError("CP65 expanded transient-path roster differs")
    final_paths = {row[1] for row in _expanded_final_path_rows()}
    if final_paths.intersection(row[3] for row in rows):
        raise RuntimeError("CP65 final/transient path collision")
    result = []
    for ordinal, row in enumerate(rows, 1):
        (
            artifact_id,
            final_path,
            alternate_final_path,
            transient_path,
            path_scope,
            shard_ordinal,
            transient_kind,
            prepared_alias,
            primary_arm,
            alternate_arm,
        ) = row
        result.append(
            cast(
                CP65TransientPathContractV1,
                _record(
                    CP65TransientPathContractV1,
                    {
                        "schema_version": CP65_TEST28_SCHEMA_VERSION,
                        "transient_ordinal": ordinal,
                        "transient_path_id": "transient-path:%04d" % ordinal,
                        "owner_artifact_id": artifact_id,
                        "final_relative_path": final_path,
                        "alternate_final_relative_path": alternate_final_path,
                        "transient_relative_path": transient_path,
                        "primary_publication_arm_id": primary_arm,
                        "alternate_publication_arm_id": alternate_arm,
                        "path_scope": path_scope,
                        "shard_ordinal": shard_ordinal,
                        "transient_kind": transient_kind,
                        "aliases_final_inode_when_published": artifact_id
                        != "__auxiliary_dynamic_hold__",
                        "prepared_authorization_alias": prepared_alias,
                        "retained_at_committed": False,
                        "sha256_manifest_included": False,
                        "collision_free": True,
                        "definition_only": True,
                    },
                ),
            )
        )
    return tuple(result)


_SHA256_POINTER_SEMANTIC_CLASSES = frozenset(
    {
        "self-body",
        "raw-artifact",
        "body-artifact",
        "nested-domain",
        "signature",
        "key-identity",
        "binary-chain",
        "externally-retained-preimage",
        "conditional-zero-or-cross",
        "selected-stored-digest",
        "nested-domain-digest",
    }
)

_SHA256_SOURCE_AVAILABILITY_CUT_IDS = frozenset(
    {
        "intrinsic-same-record",
        "frozen-before-acquisition-start",
        "durable-by-gate15-before-registry-finalization",
        "registry-finalized-before-summary",
        "summary-finalized-before-signoff",
        "signoff-finalized-before-authorization",
        "authorization-candidate-prepared-before-preauth-cas",
        "preauth-outcome-before-postauth",
        "postauth-outcome-before-started-or-terminal",
        "started-before-launch-and-terminal",
        "shards-finalized-before-preterminal-inventory",
        "preterminal-inventory-before-terminal",
        "terminal-before-manifest",
        "manifest-before-final-journal-seal",
        "final-journal-sealed-before-committed",
    }
)

_FROZEN_BEFORE_ACQUISITION_ARTIFACT_IDS = frozenset(
    {
        "frozen-protocol",
        "frozen-protocol-sha256",
        "frozen-machine-manifest",
        "frozen-source-fixture-materialization",
        "production-schema-preimage-validator-bundle",
        "source-manifest",
        "dependency-lock",
        "freeze-receipt",
        "power-review-signoff",
        "power-threshold-receipt",
        "launch-authority-public-key",
        "independent-reviewer-public-key-set",
        "seed-source-authority-public-key",
    }
)


def _sha256_source_availability_cut_id(
    target_artifact_id: str,
    semantic_class: str,
    source_artifact_id: str,
    source_contract_id: str,
) -> str:
    if semantic_class == "externally-retained-preimage" or (
        semantic_class == "conditional-zero-or-cross"
        and target_artifact_id == "auxiliary-metadata-reservation"
    ):
        return "durable-by-gate15-before-registry-finalization"
    if source_contract_id.endswith(":body-sha256") and (
        source_artifact_id == target_artifact_id
    ):
        return "intrinsic-same-record"
    if semantic_class in ("nested-domain", "signature", "key-identity") and (
        source_artifact_id == target_artifact_id
    ):
        return "intrinsic-same-record"
    if source_contract_id.startswith("auxiliary-reservation-transition-journal:"):
        if source_contract_id.endswith(":final-head") or (
            source_contract_id.endswith(":raw-sha256")
            and target_artifact_id == "committed-marker"
        ):
            return "final-journal-sealed-before-committed"
        if source_contract_id.endswith(":after-terminal"):
            return "terminal-before-manifest"
        if source_contract_id.endswith(":after-inventory"):
            return "preterminal-inventory-before-terminal"
        if source_contract_id.endswith(":preinventory-prefix"):
            return "shards-finalized-before-preterminal-inventory"
        return "durable-by-gate15-before-registry-finalization"
    if source_artifact_id in _FROZEN_BEFORE_ACQUISITION_ARTIFACT_IDS:
        return "frozen-before-acquisition-start"
    if source_artifact_id == "external-digest-preimage-registry":
        return "registry-finalized-before-summary"
    if source_artifact_id == "preflight-gate-summary":
        return "summary-finalized-before-signoff"
    if source_artifact_id == "independent-signoff-set":
        return "signoff-finalized-before-authorization"
    if source_artifact_id in (
        "launch-authorization",
        "rejected-launch-authorization-candidate",
    ):
        return "authorization-candidate-prepared-before-preauth-cas"
    if source_artifact_id == "preauthorization-outcome":
        return "preauth-outcome-before-postauth"
    if source_artifact_id == "postauthorization-outcome":
        return "postauth-outcome-before-started-or-terminal"
    if source_artifact_id in ("started-receipt", "launch-receipt"):
        return "started-before-launch-and-terminal"
    if source_artifact_id.startswith("shard-"):
        return "shards-finalized-before-preterminal-inventory"
    if source_artifact_id == "preterminal-durable-artifact-inventory":
        return "preterminal-inventory-before-terminal"
    if source_artifact_id == "terminal-state":
        return "terminal-before-manifest"
    if source_artifact_id == "sha256-manifest":
        return "manifest-before-final-journal-seal"
    return "durable-by-gate15-before-registry-finalization"


def _sha256_pointer_validator_implemented(
    target_artifact_id: str, pointer: str, source_artifact_id: str
) -> bool:
    """State whether the bounded bytes API can replay this digest instance."""

    if (
        target_artifact_id
        in (
            "preterminal-durable-artifact-inventory",
            "sha256-manifest",
        )
        and pointer == "/entries/*/sha256"
    ):
        return False
    if target_artifact_id == "shard-index" and pointer in {
        "/ordered_request_entries/*/request_sha256",
        "/ordered_request_entries/*/raw_sha256",
        "/ordered_request_entries/*/stable_sha256",
        "/ordered_request_entries/*/stderr_sha256",
        "/ordered_request_entries/*/rng_initial_sha256",
        "/ordered_request_entries/*/rng_final_sha256",
        "/raw_file_sha256",
        "/stable_file_sha256",
        "/stderr_file_sha256",
        "/rng_initial_file_sha256",
        "/rng_final_file_sha256",
    }:
        return False
    if target_artifact_id == "shard-receipt" and pointer in {
        "/requests_file_sha256",
        "/raw_file_sha256",
        "/stable_file_sha256",
        "/stderr_file_sha256",
        "/rng_initial_file_sha256",
        "/rng_final_file_sha256",
    }:
        return False
    return source_artifact_id not in _REFERENCED_OUTPUT_IDS


def _build_sha256_pointer_contracts(
    field_rules: Tuple[CP65FieldRuleV1, ...],
    digest_contracts: Tuple[CP65DigestPreimageContractV1, ...],
) -> Tuple[CP65Sha256PointerContractV1, ...]:
    by_target = {
        (contract.artifact_id, contract.digest_field_pointer): contract
        for contract in digest_contracts
    }
    by_id = {contract.contract_id: contract for contract in digest_contracts}
    result = []
    seen = set()
    for rule in field_rules:
        if not _is_sha256_field_rule(rule):
            continue
        key = (rule.artifact_id, rule.json_pointer, "pointer-wildcards-in-path-order")
        if key in seen:
            raise RuntimeError("duplicate CP65 SHA256 pointer classification")
        seen.add(key)
        source_contract_id = _sha256_pointer_source_contract_id(
            rule.artifact_id,
            rule.json_pointer,
            {target: contract.contract_id for target, contract in by_target.items()},
        )
        source_contract = by_id[source_contract_id]
        semantic_source_contract = source_contract
        external = (
            rule.artifact_id,
            rule.json_pointer,
        ) in _EXTERNAL_REGISTRY_SHA256_POINTERS
        if external:
            semantic_class = "externally-retained-preimage"
            digest_kind = (
                "body-domain-sha256"
                if semantic_source_contract.domain_separator
                else "plain-raw-bytes-sha256"
            )
            source_artifact_id = "external-digest-preimage-registry"
            source_pointer = "/entries/*/digest_sha256"
        elif semantic_source_contract.contract_id.startswith("v15-machine-manifest:"):
            semantic_class = "selected-stored-digest"
            digest_kind = "selected-stored-sha256-cross-binding"
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = semantic_source_contract.digest_field_pointer
        elif semantic_source_contract.contract_id == (
            "source-manifest:independent-recomputation-submanifest"
        ):
            semantic_class = "nested-domain-digest"
            digest_kind = "domain-separated-canonical-json-sha256"
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = semantic_source_contract.digest_field_pointer
        elif semantic_source_contract.contract_id.endswith(":body-sha256"):
            semantic_class = (
                "self-body"
                if semantic_source_contract.artifact_id == rule.artifact_id
                and rule.json_pointer == "/body_sha256"
                else "body-artifact"
            )
            digest_kind = "body-domain-sha256"
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = semantic_source_contract.digest_field_pointer
        elif "raw-signature" in semantic_source_contract.contract_id:
            semantic_class = "signature"
            digest_kind = "plain-raw-bytes-sha256"
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = rule.json_pointer.replace("_sha256", "_hex")
        elif "identity" in semantic_source_contract.contract_id:
            semantic_class = "key-identity"
            digest_kind = "key-identity-domain-sha256"
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = semantic_source_contract.digest_field_pointer
        elif "journal" in semantic_source_contract.contract_id:
            semantic_class = "binary-chain"
            digest_kind = "ordered-domain-sha256"
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = semantic_source_contract.digest_field_pointer
        elif (
            "row-digest" in semantic_source_contract.contract_id
            or "ordered" in semantic_source_contract.contract_id
            or "segment" in semantic_source_contract.contract_id
            or "selected-entry" in semantic_source_contract.contract_id
            or "selected-target" in semantic_source_contract.contract_id
            or "declared-preimage" in semantic_source_contract.contract_id
            or "request-instance" in semantic_source_contract.contract_id
            or "seed-free-request" in semantic_source_contract.contract_id
            or "selected-evidence" in semantic_source_contract.contract_id
            or "selected-reservation-entry" in semantic_source_contract.contract_id
        ):
            semantic_class = "nested-domain"
            digest_kind = (
                "record-row-domain-sha256"
                if "row-digest" in semantic_source_contract.contract_id
                or "request-instance" in semantic_source_contract.contract_id
                or "seed-free-request" in semantic_source_contract.contract_id
                else (
                    "plain-raw-bytes-sha256"
                    if "segment" in semantic_source_contract.contract_id
                    or "selected-entry" in semantic_source_contract.contract_id
                    or "selected-target" in semantic_source_contract.contract_id
                    or "declared-preimage" in semantic_source_contract.contract_id
                    or "selected-evidence" in semantic_source_contract.contract_id
                    else "ordered-domain-sha256"
                )
            )
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = semantic_source_contract.digest_field_pointer
        else:
            semantic_class = "raw-artifact"
            digest_kind = "plain-raw-file-sha256"
            source_artifact_id = semantic_source_contract.artifact_id
            source_pointer = semantic_source_contract.digest_field_pointer
        conditional_zero = {
            ("preauthorization-outcome", "/prepared_launch_authorization_sha256",): (
                "authorization-arm-nonzero-final-launch-raw;terminal-arm-zero-iff-no-prepared-candidate-else-nonzero-rejected-candidate-raw",
                "preauthorization-prepared-candidate-branch-binding",
            ),
            ("terminal-state", "/launch_authorization_sha256"): (
                "zero-iff-preauthorization-terminal-otherwise-exact-raw-cross",
                "terminal-launch-authorization-arm-binding",
            ),
            ("terminal-state", "/postauthorization_outcome_sha256"): (
                "zero-unless-postauthorization-arm-exact-raw-cross",
                "terminal-postauthorization-outcome-arm-binding",
            ),
            ("terminal-state", "/started_receipt_sha256"): (
                "zero-unless-started-arm-exact-raw-cross",
                "terminal-started-receipt-arm-binding",
            ),
            (
                "auxiliary-metadata-reservation",
                "/artifact_entries/*/device_identity_sha256",
            ): (
                "zero-iff-committed-marker-future-o-excl-covered-by-hold-otherwise-nonzero",
                "auxiliary-device-identity-committed-marker-zero-arm-binding",
            ),
            (
                "auxiliary-metadata-reservation",
                "/artifact_entries/*/extent_map_sha256",
            ): (
                "zero-iff-committed-marker-future-o-excl-covered-by-hold-otherwise-nonzero",
                "auxiliary-extent-map-committed-marker-zero-arm-binding",
            ),
        }
        policy, binding_rule = conditional_zero.get(
            (rule.artifact_id, rule.json_pointer),
            ("nonzero-required", "unconditional-classified-digest-binding"),
        )
        if (rule.artifact_id, rule.json_pointer) in conditional_zero:
            semantic_class = "conditional-zero-or-cross"
        shard_segment_sources = {
            "/ordered_request_entries/*/request_sha256": "shard-requests",
            "/ordered_request_entries/*/raw_sha256": "shard-raw-records",
            "/ordered_request_entries/*/stable_sha256": "shard-stable-traces",
            "/ordered_request_entries/*/stderr_sha256": "shard-stderr-records",
            "/ordered_request_entries/*/rng_initial_sha256": "shard-rng-initial-states",
            "/ordered_request_entries/*/rng_final_sha256": "shard-rng-final-states",
        }
        if rule.artifact_id == "shard-index" and (
            rule.json_pointer in shard_segment_sources
        ):
            source_artifact_id = shard_segment_sources[rule.json_pointer]
        result.append(
            cast(
                CP65Sha256PointerContractV1,
                _record(
                    CP65Sha256PointerContractV1,
                    {
                        "schema_version": CP65_TEST28_SCHEMA_VERSION,
                        "classification_id": "sha256-pointer:%s:%s" % key[:2],
                        "target_artifact_id": rule.artifact_id,
                        "target_json_pointer": rule.json_pointer,
                        "semantic_class": semantic_class,
                        "digest_kind": digest_kind,
                        "source_artifact_id": source_artifact_id,
                        "source_json_pointer": source_pointer,
                        "source_contract_id": source_contract_id,
                        "source_availability_cut_id": _sha256_source_availability_cut_id(
                            rule.artifact_id,
                            semantic_class,
                            source_artifact_id,
                            source_contract_id,
                        ),
                        "instance_selector_id": key[2],
                        "cardinality_rule_id": "exactly-one-classification-per-expanded-pointer-instance",
                        "preimage_encoding": (
                            "registry-row-declared-ascii-or-lowercase-hex"
                            if external
                            else semantic_source_contract.canonical_profile_id
                        ),
                        "domain_separator": semantic_source_contract.domain_separator,
                        "zero_policy_id": policy,
                        "conditional_binding_rule_id": binding_rule,
                        "externally_retained_preimage_required": external,
                        "preimage_registry_entry_required": external,
                        "validator_implemented": _sha256_pointer_validator_implemented(
                            rule.artifact_id,
                            rule.json_pointer,
                            source_artifact_id,
                        ),
                        "definition_only": True,
                    },
                ),
            )
        )
    if len(result) != len(seen):
        raise RuntimeError("CP65 SHA256 pointer classifications differ")
    if any(
        row.semantic_class not in _SHA256_POINTER_SEMANTIC_CLASSES for row in result
    ):
        raise RuntimeError("CP65 SHA256 pointer semantic class differs")
    if any(
        row.source_availability_cut_id not in _SHA256_SOURCE_AVAILABILITY_CUT_IDS
        for row in result
    ):
        raise RuntimeError("CP65 SHA256 source availability cut differs")
    return tuple(result)


_POINTER_WILDCARD_CARDINALITIES = {
    ("source-manifest", "entries"): _MAX_SOURCE_MANIFEST_ENTRIES,
    ("power-threshold-receipt", "ordered_slot_thresholds"): 32,
    ("external-digest-preimage-registry", "entries"): 4_096,
    ("external-digest-preimage-registry", "ordered_entry_sha256s"): 4_096,
    ("auxiliary-metadata-reservation", "artifact_entries"): 183,
    ("reservation-manifest", "entries"): 128,
    ("production-schedule", "requests"): 32_768,
    ("production-schedule", "ordered_request_record_sha256s"): 32_768,
    ("production-shard-map-receipt", "shards"): 32,
    (
        "production-shard-map-receipt",
        "per_file_reservation_manifest_entry_sha256s",
    ): 4,
    ("independent-signoff-set", "ordered_signoffs"): 4,
    ("independent-signoff-set", "reviewed_artifact_sha256s"): 1,
    ("independent-reviewer-public-key-set", "ordered_keys"): 4,
    (
        "independent-reviewer-public-key-set",
        "ordered_public_key_identity_sha256s",
    ): 4,
    ("power-threshold-receipt", "ordered_slot_threshold_row_sha256s"): 32,
    ("power-review-signoff", "ordered_slot_threshold_row_sha256s"): 32,
    ("preflight-gate-summary", "ordered_evidence_receipt_sha256s"): 15,
    ("shard-index", "ordered_request_entries"): 1_024,
    (
        "preterminal-durable-artifact-inventory",
        "entries",
    ): _MAX_TERMINAL_PUBLICATION_ENTRIES,
    ("sha256-manifest", "entries"): _MAX_TERMINAL_PUBLICATION_ENTRIES,
}


def _sha256_pointer_expanded_cardinality(
    contract: CP65Sha256PointerContractV1,
) -> int:
    """Return the exact maximum expanded instance count for one SHA pointer."""

    if type(contract) is not CP65Sha256PointerContractV1:
        raise TypeError("contract must be an exact CP65 SHA pointer contract")
    declaration = _ARTIFACT_BY_ID.get(contract.target_artifact_id)
    if declaration is None:
        raise ValueError("SHA pointer target artifact is not catalogued")
    cardinality = 32 if declaration[2] == "per-shard" else 1
    parts = tuple(part for part in contract.target_json_pointer.split("/") if part)
    for index, part in enumerate(parts):
        if part != "*":
            continue
        if index == 0:
            raise ValueError("SHA pointer wildcard lacks a containing field")
        container_key = parts[index - 1]
        maximum = _POINTER_WILDCARD_CARDINALITIES.get(
            (contract.target_artifact_id, container_key)
        )
        if maximum is None:
            raise ValueError("SHA pointer wildcard cardinality is not frozen")
        cardinality *= maximum
    return cardinality


def _sha256_pointer_registry_entry_cardinality(
    contract: CP65Sha256PointerContractV1,
) -> int:
    """Return the maximum populated-registry rows required by a pointer."""

    if type(contract) is not CP65Sha256PointerContractV1:
        raise TypeError("contract must be an exact CP65 SHA pointer contract")
    if not contract.preimage_registry_entry_required:
        return 0
    key = (contract.target_artifact_id, contract.target_json_pointer)
    if key in {
        (
            "auxiliary-metadata-reservation",
            "/artifact_entries/*/device_identity_sha256",
        ),
        (
            "auxiliary-metadata-reservation",
            "/artifact_entries/*/extent_map_sha256",
        ),
    }:
        return 182
    if contract.semantic_class == "conditional-zero-or-cross":
        return 0
    return _sha256_pointer_expanded_cardinality(contract)


def _build_gate_requirements() -> Tuple[CP65GateRequirementV1, ...]:
    result = []
    for ordinal, (gate_id, node_id) in enumerate(
        zip(_GATE_IDS, _GATE_EVIDENCE_NODES), 1
    ):
        artifact_id = {
            "independent-554-estimate-interval-decision-path-receipt": "independent-554-estimate-interval-decision-path-qualification-receipt",
            "independent-full-32768-recomputation-receipt": "independent-full-32768-recomputation-qualification-receipt",
        }.get(node_id, node_id)
        required_artifact_ids = (
            _authorization_required_artifacts()
            if ordinal == 17
            else _GATE_REQUIRED_ARTIFACT_IDS[ordinal - 1]
        )
        predicate_clause_ids = tuple(
            "record:" + item for item in required_artifact_ids
        ) + ("gate-pass:" + gate_id,)
        result.append(
            cast(
                CP65GateRequirementV1,
                _record(
                    CP65GateRequirementV1,
                    {
                        "schema_version": CP65_TEST28_SCHEMA_VERSION,
                        "gate_ordinal": ordinal,
                        "gate_id": gate_id,
                        "evidence_node_id": node_id,
                        "evidence_artifact_id": artifact_id,
                        "required_artifact_ids": required_artifact_ids,
                        "predicate_id": "gate:" + gate_id,
                        "predicate_clause_ids": predicate_clause_ids,
                        "preflight_summary_covered": ordinal <= 15,
                        "requires_external_provenance": True,
                        "requires_independent_authority": ordinal in (5, 15, 16, 17),
                        "evidence_present": False,
                        "gate_state": "MISSING",
                        "definition_only": True,
                    },
                ),
            )
        )
    return tuple(result)


def _primary_raw_node(artifact_id: str) -> str:
    return "digest:" + artifact_id + ":raw-sha256"


def _body_node(artifact_id: str) -> str:
    return "digest:" + artifact_id + ":body-sha256"


def _build_artifact_preimage_graph(
    contracts: Tuple[CP65DigestPreimageContractV1, ...],
    sha256_pointer_contracts: Tuple[CP65Sha256PointerContractV1, ...],
) -> Tuple[
    Tuple[str, ...],
    Tuple[Tuple[str, str], ...],
    Tuple[str, ...],
    Tuple[str, ...],
    Tuple[str, ...],
    Tuple[str, ...],
]:
    nodes = ["digest:" + contract.contract_id for contract in contracts]
    edges = []
    pointers = []
    state_source_contract_ids = {}
    edge_source_contract_overrides = {}
    edge_digest_kind_overrides = {}

    def add_node(node: str) -> None:
        if node not in nodes:
            nodes.append(node)

    def add_edge(
        source: str,
        target: str,
        pointer: str,
        source_contract_id: str = "",
        digest_kind: str = "",
    ) -> None:
        add_node(source)
        add_node(target)
        item = (source, target)
        if item in edges:
            if pointers[edges.index(item)] == pointer:
                return
            raise RuntimeError(
                "duplicate CP65 artifact-preimage edge: %r via %s" % (item, pointer)
            )
        edges.append(item)
        pointers.append(pointer)
        if source_contract_id:
            edge_source_contract_overrides[item] = source_contract_id
        if digest_kind:
            edge_digest_kind_overrides[item] = digest_kind

    contracts_by_id = {contract.contract_id: contract for contract in contracts}
    contract_ids = set(contracts_by_id)
    for contract in contracts:
        target = "digest:" + contract.contract_id
        for component_id in contract.ordered_component_ids:
            if component_id not in contract_ids:
                raise RuntimeError("unresolved CP65 digest component")
            add_edge(
                "digest:" + component_id,
                target,
                (
                    "$classified-source-contract"
                    if contract.contract_id.startswith("classified-binding:")
                    else contracts_by_id[component_id].digest_field_pointer
                ),
            )
    for pointer_contract in sha256_pointer_contracts:
        if pointer_contract.target_artifact_id not in _ARTIFACT_BY_ID:
            raise RuntimeError("CP65 classified digest artifact is unresolved")
        target = (
            "state:rejected-launch-authorization-candidate:validated-envelope"
            if pointer_contract.target_artifact_id
            == "rejected-launch-authorization-candidate"
            else _body_node(pointer_contract.target_artifact_id)
        )
        source = "digest:" + pointer_contract.source_contract_id
        if _sha256_pointer_is_intrinsic_owned(pointer_contract):
            if source != target:
                add_edge(
                    source,
                    target,
                    pointer_contract.target_json_pointer,
                    pointer_contract.source_contract_id,
                    pointer_contract.digest_kind,
                )
            continue
        binding_state = "binding:" + pointer_contract.classification_id
        state_source_contract_ids[binding_state] = pointer_contract.source_contract_id
        add_edge(
            source,
            binding_state,
            "$selected-source-digest",
            pointer_contract.source_contract_id,
            pointer_contract.digest_kind,
        )
        add_edge(
            binding_state,
            target,
            pointer_contract.target_json_pointer,
            pointer_contract.source_contract_id,
            "digest-value-equality",
        )

    # The historical 20-node/44-edge gate graph is published separately as a
    # gate-evidence-only view.  Re-injecting it here would duplicate (and in a
    # few cases conflate) the pointer-classified full-preimage relationships.

    extra_artifact_edges = (
        ("frozen-protocol", "source-manifest", "/entries/*/sha256"),
        ("frozen-machine-manifest", "source-manifest", "/entries/*/sha256"),
        ("dependency-lock", "source-manifest", "/entries/*/sha256"),
        (
            "frozen-source-fixture-materialization",
            "source-manifest",
            "/entries/*/sha256",
        ),
        (
            "production-schema-preimage-validator-bundle",
            "source-manifest",
            "/entries/*/sha256",
        ),
        ("launch-authority-public-key", "source-manifest", "/entries/*/sha256"),
        ("independent-reviewer-public-key-set", "source-manifest", "/entries/*/sha256"),
        ("seed-source-authority-public-key", "source-manifest", "/entries/*/sha256"),
        (
            "frozen-source-fixture-materialization",
            "freeze-receipt",
            "/frozen_source_fixture_materialization_sha256",
        ),
        (
            "production-schema-preimage-validator-bundle",
            "freeze-receipt",
            "/production_receipt_schema_bundle_sha256",
        ),
        (
            "launch-authority-public-key",
            "freeze-receipt",
            "/launch_authority_public_key_sha256",
        ),
        (
            "independent-reviewer-public-key-set",
            "freeze-receipt",
            "/independent_reviewer_public_key_set_sha256",
        ),
        (
            "seed-source-authority-public-key",
            "freeze-receipt",
            "/seed_source_authority_public_key_sha256",
        ),
        ("dependency-lock", "freeze-receipt", "/dependency_lock_sha256"),
        ("frozen-protocol", "power-review-signoff", "/protocol_sha256"),
        ("frozen-machine-manifest", "power-review-signoff", "/machine_manifest_sha256"),
        ("power-review-signoff", "power-threshold-receipt", "/reviewer_signoff_sha256"),
        (
            "external-digest-preimage-registry",
            "preflight-gate-summary",
            "/external_digest_preimage_registry_sha256",
        ),
        (
            "independent-reviewer-public-key-set",
            "independent-signoff-set",
            "/reviewer_public_key_set_sha256",
        ),
        (
            "external-seed-acquisition-start-receipt",
            "seed-source-authority-attestation",
            "/acquisition_start_receipt_sha256",
        ),
        (
            "external-seed-acquisition-journal",
            "seed-source-authority-attestation",
            "/acquisition_journal_sha256",
        ),
        (
            "seed-source-custody-artifact",
            "seed-source-authority-attestation",
            "/seed_source_custody_artifact_sha256",
        ),
        (
            "seed-source-authority-attestation",
            "external-seed-source-receipt",
            "/source_authority_attestation_sha256",
        ),
        ("freeze-receipt", "auxiliary-metadata-reservation", "/freeze_receipt_sha256"),
        ("production-schedule", "auxiliary-metadata-reservation", "/schedule_sha256"),
        (
            "production-schema-preimage-validator-bundle",
            "auxiliary-metadata-reservation",
            "/capacity_schema_sha256",
        ),
        ("freeze-receipt", "reservation-manifest", "/freeze_receipt_sha256"),
        ("production-schedule", "reservation-manifest", "/schedule_sha256"),
        (
            "production-schema-preimage-validator-bundle",
            "reservation-manifest",
            "/capacity_schema_sha256",
        ),
        (
            "auxiliary-metadata-reservation",
            "capacity-receipt",
            "/auxiliary_metadata_reservation_artifact_sha256",
        ),
        ("reservation-manifest", "capacity-receipt", "/reservation_manifest_sha256"),
        (
            "preauthorization-outcome",
            "launch-authorization",
            "$publication-order-and-byte-identity",
        ),
        (
            "preterminal-durable-artifact-inventory",
            "terminal-state",
            "/durable_artifact_inventory_sha256",
        ),
        (
            "preterminal-durable-artifact-inventory",
            "sha256-manifest",
            "/entries/*/sha256",
        ),
        ("terminal-state", "sha256-manifest", "/terminal_state_sha256"),
        ("sha256-manifest", "committed-marker", "/sha256_manifest_sha256"),
        ("terminal-state", "committed-marker", "/terminal_state_sha256"),
    )
    for source_id, target_id, pointer in extra_artifact_edges:
        identity_source_ids = {
            (
                "launch-authority-public-key",
                "/authority_identity_sha256",
            ): "launch-authority-public-key:identity",
            (
                "seed-source-authority-public-key",
                "/source_authority_identity_sha256",
            ): "seed-source-authority-public-key:identity",
            (
                "independent-reviewer-public-key-set",
                "/reviewer_public_key_identity_sha256",
            ): "independent-reviewer-public-key-set:key-identity",
            (
                "independent-reviewer-public-key-set",
                "/ordered_signoffs/*/reviewer_public_key_identity_sha256",
            ): "independent-reviewer-public-key-set:key-identity",
        }
        identity_contract = identity_source_ids.get((source_id, pointer))
        source = (
            "digest:" + identity_contract
            if identity_contract is not None
            else _primary_raw_node(source_id)
        )
        if (
            target_id == "launch-authorization"
            and pointer == "$publication-order-and-byte-identity"
        ):
            prepared_digest = (
                "digest:launch-authorization-candidate:prepared-raw-sha256"
            )
            prepared_state = "state:launch-authorization-candidate:prepared-raw"
            authorization_winner = "state:preauthorization-outcome:authorization-winner"
            terminal_winner = "state:preauthorization-outcome:terminal-winner"
            add_edge(
                prepared_digest,
                prepared_state,
                "$prepared_exact_bytes",
            )
            add_edge(
                prepared_state,
                _body_node("preauthorization-outcome"),
                "/prepared_launch_authorization_sha256",
            )
            add_edge(
                _primary_raw_node("preauthorization-outcome"),
                authorization_winner,
                "$authorization-arm",
            )
            add_edge(
                _primary_raw_node("preauthorization-outcome"),
                terminal_winner,
                "$terminal-arm",
            )
            add_edge(
                authorization_winner,
                _primary_raw_node("launch-authorization"),
                "$rename-no-replace-identical-bytes",
            )
            add_edge(
                prepared_state,
                _primary_raw_node("launch-authorization"),
                "$authorization-candidate-byte-identity",
            )
            add_edge(
                terminal_winner,
                _primary_raw_node("rejected-launch-authorization-candidate"),
                "$rename-no-replace-identical-bytes",
            )
            add_edge(
                prepared_state,
                _primary_raw_node("rejected-launch-authorization-candidate"),
                "$rejected-candidate-byte-identity",
            )
            continue
        target = (
            "digest:source-manifest:selected-entry-raw-sha256"
            if target_id == "source-manifest" and pointer == "/entries/*/sha256"
            else (
                "digest:launch-authorization:unsigned-preimage"
                if target_id == "launch-authorization"
                else _body_node(target_id)
            )
        )
        add_edge(source, target, pointer)

    # The transition journal is mutable until it is sealed, so its custody is
    # represented by versioned states rather than by a single raw-file node.
    journal_states = (
        "state:auxiliary-transition-journal:head0",
        "state:auxiliary-transition-journal:preinventory-prefix",
        "state:auxiliary-transition-journal:after-inventory",
        "state:auxiliary-transition-journal:after-terminal",
        "state:auxiliary-transition-journal:final",
    )
    for state in journal_states:
        add_node(state)
    add_edge(
        _primary_raw_node("auxiliary-metadata-reservation"),
        journal_states[0],
        "$header.auxiliary_reservation_raw_sha256",
    )
    add_edge(
        journal_states[0],
        journal_states[1],
        "$valid_prefix.previous_entry_sha256",
    )
    add_edge(
        journal_states[1],
        _body_node("preterminal-durable-artifact-inventory"),
        "/auxiliary_transition_journal_prefix_head_sha256",
    )
    add_edge(
        _primary_raw_node("preterminal-durable-artifact-inventory"),
        journal_states[2],
        "$transition-code-3.target_raw_sha256",
    )
    add_edge(
        journal_states[2],
        _body_node("terminal-state"),
        "/auxiliary_transition_journal_after_inventory_head_sha256",
    )
    add_edge(
        _primary_raw_node("terminal-state"),
        journal_states[3],
        "$transition-code-4.target_raw_sha256",
    )
    add_edge(
        journal_states[3],
        _body_node("sha256-manifest"),
        "/auxiliary_transition_journal_after_terminal_head_sha256",
    )
    add_edge(
        _primary_raw_node("sha256-manifest"),
        journal_states[4],
        "$transition-code-5.target_raw_sha256",
    )
    add_edge(
        journal_states[4],
        _body_node("committed-marker"),
        "/auxiliary_reservation_transition_journal_final_head_sha256",
    )
    add_edge(
        _primary_raw_node("auxiliary-reservation-transition-journal"),
        _body_node("committed-marker"),
        "/auxiliary_reservation_transition_journal_sha256",
    )

    # The retained preterminal inventory is a branch-sensitive closure over
    # every earlier durable artifact.  Schema-level edges conservatively
    # include all possible earlier arms; predicates enforce mutual exclusion.
    inventory_target = (
        "digest:preterminal-durable-artifact-inventory:selected-entry-raw-sha256"
    )
    excluded = {
        "auxiliary-reservation-transition-journal",
        "preterminal-durable-artifact-inventory",
        "terminal-state",
        "sha256-manifest",
        "committed-marker",
    }
    for artifact_id, *_rest in _ARTIFACT_DECLARATIONS:
        if artifact_id not in excluded:
            edge = (_primary_raw_node(artifact_id), inventory_target)
            if edge not in edges:
                add_edge(edge[0], edge[1], "/entries/*/sha256")

    indegree = {node: 0 for node in nodes}
    children = {node: [] for node in nodes}
    for source, target in edges:
        indegree[target] += 1
        children[source].append(target)
    ready = [node for node in nodes if indegree[node] == 0]
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(order) != len(nodes):
        cyclic_nodes = tuple(node for node in nodes if indegree[node] > 0)
        raise RuntimeError(
            "CP65 artifact-preimage dependency graph is cyclic: %r" % (cyclic_nodes,)
        )
    source_contract_ids = []
    digest_kinds = []
    for source, target in edges:
        edge = (source, target)
        if edge in edge_source_contract_overrides:
            contract_id = edge_source_contract_overrides[edge]
        elif source.startswith("digest:"):
            contract_id = source[len("digest:") :]
        elif source == "state:launch-authorization-candidate:prepared-raw":
            contract_id = "launch-authorization-candidate:prepared-raw-sha256"
        elif source == "state:preauthorization-outcome:authorization-winner":
            contract_id = "preauthorization-outcome:raw-sha256"
        elif source == "state:preauthorization-outcome:terminal-winner":
            contract_id = "preauthorization-outcome:raw-sha256"
        elif source == "state:auxiliary-transition-journal:head0":
            contract_id = "auxiliary-reservation-transition-journal:head0"
        elif source == "state:auxiliary-transition-journal:preinventory-prefix":
            contract_id = "auxiliary-reservation-transition-journal:preinventory-prefix"
        elif source == "state:auxiliary-transition-journal:after-inventory":
            contract_id = "auxiliary-reservation-transition-journal:after-inventory"
        elif source == "state:auxiliary-transition-journal:after-terminal":
            contract_id = "auxiliary-reservation-transition-journal:after-terminal"
        elif source == "state:auxiliary-transition-journal:final":
            contract_id = "auxiliary-reservation-transition-journal:final-head"
        elif source in state_source_contract_ids:
            contract_id = state_source_contract_ids[source]
        else:
            raise RuntimeError("CP65 graph source has no digest contract")
        if contract_id not in contracts_by_id:
            raise RuntimeError("CP65 graph source digest contract is unresolved")
        source_contract_ids.append(contract_id)
        contract = contracts_by_id[contract_id]
        if edge in edge_digest_kind_overrides:
            kind = edge_digest_kind_overrides[edge]
        elif source.startswith(("state:", "binding:")):
            kind = "byte-identity"
        elif "unsigned-preimage" in contract_id:
            kind = "signature-preimage-sha256"
        elif "identity" in contract_id:
            kind = "key-identity-domain-sha256"
        elif "raw-signature" in contract_id:
            kind = "plain-raw-bytes-sha256"
        elif "row-digest" in contract_id or contract_id.endswith(":entry"):
            kind = "record-row-domain-sha256"
        elif "ordered" in contract_id or contract_id.endswith(":head"):
            kind = "ordered-domain-sha256"
        elif contract.domain_separator:
            kind = "body-domain-sha256"
        else:
            kind = "plain-raw-file-sha256"
        digest_kinds.append(kind)
    return (
        tuple(nodes),
        tuple(edges),
        tuple(pointers),
        tuple(source_contract_ids),
        tuple(digest_kinds),
        tuple(order),
    )


def _predecessor_custody() -> CP65PredecessorCustodyV1:
    return cast(
        CP65PredecessorCustodyV1,
        _record(
            CP65PredecessorCustodyV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "cp64_schema_version": "cp64-test28-production-custody-preflight-v1",
                "cp64_source_relative_path": "src/heterodiff/evaluation/mixed_initializer_test28_production_custody_preflight.py",
                "cp64_source_sha256": "d35cbacb84e3348ae10549e053a0bb1572569583cdd03e66119353af4148bec2",
                "cp64_source_bytes": 109_716,
                "cp64_source_lines": 2_409,
                "cp64_test_relative_path": "tests/unit/test_mixed_initializer_test28_production_custody_preflight.py",
                "cp64_test_sha256": "5e2d3a4ee4803556812983a01506e1f0b146c62ac2e2017c98914474a799fca4",
                "cp64_test_bytes": 125_001,
                "cp64_test_lines": 2_944,
                "v15_protocol_relative_path": "research/preregistrations/cp50_test28_mixed_initializer_v15.md",
                "v15_protocol_sha256": "79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8",
                "v15_protocol_bytes": 125_063,
                "v15_protocol_lines": 2_265,
                "v15_manifest_relative_path": "research/fixtures/cp50_test28_mixed_initializer_v15.json",
                "v15_manifest_sha256": "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376",
                "v15_manifest_bytes": 2_038_189,
                "v15_manifest_lines": 39_046,
                "cp64_bundle_record_sha256": "32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39",
                "cp64_bundle_public_sha256": "caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83",
                "cp64_bundle_canonical_json_sha256": "31c1ff133f9dc6c3f9a5810359bd313f5fe5f46cb5e2bd6801b8dac0e241ae23",
                "cp64_bundle_canonical_json_bytes": 77_595,
                "cp64_no_execution_gate_contract_record_sha256": "7ceb4f12ce712e7123509eb6380e134876855bb91e90c64a951f7e1bcbcb2633",
                "cp64_false_schema_definition_flags": (
                    "all_required_production_receipt_keysets_predeclared",
                    "complete_receipt_type_range_size_and_domain_schemas_frozen",
                    "complete_auxiliary_artifact_size_schema_frozen",
                    "bounded_auxiliary_artifact_size_proof_present",
                    "generic_prestart_terminal_record_schema_frozen",
                    "all_required_production_receipt_digest_preimages_frozen",
                    "authorization_signature_preimage_and_verifier_frozen",
                    "requirement_schemas_frozen",
                ),
                "cp64_gate_count": 17,
                "cp64_evidence_present_count": 0,
                "cp64_ledger_total_count": 19,
                "cp64_ledger_satisfied_count": 15,
                "cp64_ledger_missing_count": 4,
                "v15_protocol_state": "DRAFT",
                "v15_lifecycle_current_state": "DRAFT_PRE_FREEZE",
                "v15_complete_production_roster_frozen": False,
                "formal_test_28_status": "OPEN",
                "formal_test_28_closed": False,
                "cp65_source_hashes_external_binding_required": True,
                "predecessor_only": True,
            },
        ),
    )


def _record_primitive(record: _SealedRecord) -> dict:
    return {
        item.name: _canonical_value(getattr(record, item.name), require_issued=True)
        for item in fields(type(record))
        if item.name != "record_sha256"
    }


def _semantic_sha256(
    field_rules: Tuple[CP65FieldRuleV1, ...],
    artifact_schemas: Tuple[CP65ArtifactSchemaV1, ...],
    transient_path_contracts: Tuple[CP65TransientPathContractV1, ...],
    digest_contracts: Tuple[CP65DigestPreimageContractV1, ...],
    sha256_pointer_contracts: Tuple[CP65Sha256PointerContractV1, ...],
    predicates: Tuple[CP65PredicateContractV1, ...],
    gates: Tuple[CP65GateRequirementV1, ...],
    bounds: Tuple[CP65AuxiliaryArtifactBoundV1, ...],
    proof: CP65AuxiliarySizeProofV1,
    signature: CP65AuthorizationSignatureContractV1,
    graph: tuple,
) -> str:
    payload = {
        "artifact_preimage_dependency_edges": graph[1],
        "artifact_preimage_dependency_node_ids": graph[0],
        "artifact_preimage_edge_target_pointers": graph[2],
        "artifact_preimage_source_contract_ids": graph[3],
        "artifact_preimage_digest_kinds": graph[4],
        "artifact_preimage_topological_order": graph[5],
        "artifact_schemas": tuple(_record_primitive(item) for item in artifact_schemas),
        "transient_path_contracts": tuple(
            _record_primitive(item) for item in transient_path_contracts
        ),
        "authorization_signature_contract": _record_primitive(signature),
        "auxiliary_artifact_bounds": tuple(_record_primitive(item) for item in bounds),
        "auxiliary_size_proof": _record_primitive(proof),
        "canonical_profile_id": _CANONICAL_PROFILE_ID,
        "conditional_paths": _CONDITIONAL_PATHS,
        "digest_dag_edges": _GATE_DAG_EDGES,
        "digest_dag_nodes": _GATE_DAG_NODES,
        "digest_preimage_contracts": tuple(
            _record_primitive(item) for item in digest_contracts
        ),
        "sha256_pointer_contracts": tuple(
            _record_primitive(item) for item in sha256_pointer_contracts
        ),
        "field_rules": tuple(_record_primitive(item) for item in field_rules),
        "gate_requirements": tuple(_record_primitive(item) for item in gates),
        "global_paths": _GLOBAL_PATHS,
        "path_precision": (312, 128, 1, 183, 1, 181, 310, 622, True, True),
        "per_shard_path_templates": _PER_SHARD_PATHS,
        "predicate_contracts": tuple(_record_primitive(item) for item in predicates),
        "schema_version": CP65_TEST28_SCHEMA_VERSION,
    }
    return hashlib.sha256(
        b"cp65-test28-production-schema-semantic-v1\0" + _plain_json_bytes(payload)
    ).hexdigest()


_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_HEX16_RE = re.compile(r"[0-9a-f]{16}\Z")
_HEX768_RE = re.compile(r"[0-9a-f]{768}\Z")
_UTC_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z"
)
_SHARD_ID_RE = re.compile(r"shard-00(?:0[1-9]|[12][0-9]|3[0-2])\Z")
_ATTEMPT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_OPAQUE_METHOD_SESSION_AUTHORITY_ID_RE = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,127}\Z")
_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP63_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_CP63_SCHEMA_VERSION = "cp63-test28-runner-recomputation-rehearsal-v1"
_CP61_ESTIMAND_IDS = (
    "cp61/observable/row-01/T28-M1-Q/bounded-rejection/budget-1/returned-rejection-selected-before-deadline",
    "cp61/observable/row-01/T28-M1-Q/bounded-rejection/budget-1/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-01/T28-M1-Q/bounded-rejection/budget-1/preexecution-refusal-before-deadline",
    "cp61/observable/row-01/T28-M1-Q/bounded-rejection/budget-1/execution-failure-before-deadline",
    "cp61/observable/row-01/T28-M1-Q/bounded-rejection/budget-1/timeout-censored-at-deadline",
    "cp61/observable/row-02/T28-M1-Q/bounded-rejection/budget-4/returned-rejection-selected-before-deadline",
    "cp61/observable/row-02/T28-M1-Q/bounded-rejection/budget-4/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-02/T28-M1-Q/bounded-rejection/budget-4/preexecution-refusal-before-deadline",
    "cp61/observable/row-02/T28-M1-Q/bounded-rejection/budget-4/execution-failure-before-deadline",
    "cp61/observable/row-02/T28-M1-Q/bounded-rejection/budget-4/timeout-censored-at-deadline",
    "cp61/observable/row-03/T28-M1-Q/bounded-rejection/budget-16/returned-rejection-selected-before-deadline",
    "cp61/observable/row-03/T28-M1-Q/bounded-rejection/budget-16/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-03/T28-M1-Q/bounded-rejection/budget-16/preexecution-refusal-before-deadline",
    "cp61/observable/row-03/T28-M1-Q/bounded-rejection/budget-16/execution-failure-before-deadline",
    "cp61/observable/row-03/T28-M1-Q/bounded-rejection/budget-16/timeout-censored-at-deadline",
    "cp61/observable/row-04/T28-M1-Q/bounded-rejection/budget-64/returned-rejection-selected-before-deadline",
    "cp61/observable/row-04/T28-M1-Q/bounded-rejection/budget-64/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-04/T28-M1-Q/bounded-rejection/budget-64/preexecution-refusal-before-deadline",
    "cp61/observable/row-04/T28-M1-Q/bounded-rejection/budget-64/execution-failure-before-deadline",
    "cp61/observable/row-04/T28-M1-Q/bounded-rejection/budget-64/timeout-censored-at-deadline",
    "cp61/observable/row-05/T28-M1-Q/fixed-budget-sir/budget-8/returned-sir-selected-before-deadline",
    "cp61/observable/row-05/T28-M1-Q/fixed-budget-sir/budget-8/preexecution-refusal-before-deadline",
    "cp61/observable/row-05/T28-M1-Q/fixed-budget-sir/budget-8/execution-failure-before-deadline",
    "cp61/observable/row-05/T28-M1-Q/fixed-budget-sir/budget-8/timeout-censored-at-deadline",
    "cp61/observable/row-06/T28-M1-Q/fixed-budget-sir/budget-32/returned-sir-selected-before-deadline",
    "cp61/observable/row-06/T28-M1-Q/fixed-budget-sir/budget-32/preexecution-refusal-before-deadline",
    "cp61/observable/row-06/T28-M1-Q/fixed-budget-sir/budget-32/execution-failure-before-deadline",
    "cp61/observable/row-06/T28-M1-Q/fixed-budget-sir/budget-32/timeout-censored-at-deadline",
    "cp61/observable/row-07/T28-M1-Q/fixed-budget-sir/budget-128/returned-sir-selected-before-deadline",
    "cp61/observable/row-07/T28-M1-Q/fixed-budget-sir/budget-128/preexecution-refusal-before-deadline",
    "cp61/observable/row-07/T28-M1-Q/fixed-budget-sir/budget-128/execution-failure-before-deadline",
    "cp61/observable/row-07/T28-M1-Q/fixed-budget-sir/budget-128/timeout-censored-at-deadline",
    "cp61/observable/row-08/T28-M1-Q/fixed-budget-sir/budget-512/returned-sir-selected-before-deadline",
    "cp61/observable/row-08/T28-M1-Q/fixed-budget-sir/budget-512/preexecution-refusal-before-deadline",
    "cp61/observable/row-08/T28-M1-Q/fixed-budget-sir/budget-512/execution-failure-before-deadline",
    "cp61/observable/row-08/T28-M1-Q/fixed-budget-sir/budget-512/timeout-censored-at-deadline",
    "cp61/observable/row-09/T28-M2-Q/bounded-rejection/budget-1/returned-rejection-selected-before-deadline",
    "cp61/observable/row-09/T28-M2-Q/bounded-rejection/budget-1/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-09/T28-M2-Q/bounded-rejection/budget-1/preexecution-refusal-before-deadline",
    "cp61/observable/row-09/T28-M2-Q/bounded-rejection/budget-1/execution-failure-before-deadline",
    "cp61/observable/row-09/T28-M2-Q/bounded-rejection/budget-1/timeout-censored-at-deadline",
    "cp61/observable/row-10/T28-M2-Q/bounded-rejection/budget-4/returned-rejection-selected-before-deadline",
    "cp61/observable/row-10/T28-M2-Q/bounded-rejection/budget-4/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-10/T28-M2-Q/bounded-rejection/budget-4/preexecution-refusal-before-deadline",
    "cp61/observable/row-10/T28-M2-Q/bounded-rejection/budget-4/execution-failure-before-deadline",
    "cp61/observable/row-10/T28-M2-Q/bounded-rejection/budget-4/timeout-censored-at-deadline",
    "cp61/observable/row-11/T28-M2-Q/bounded-rejection/budget-16/returned-rejection-selected-before-deadline",
    "cp61/observable/row-11/T28-M2-Q/bounded-rejection/budget-16/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-11/T28-M2-Q/bounded-rejection/budget-16/preexecution-refusal-before-deadline",
    "cp61/observable/row-11/T28-M2-Q/bounded-rejection/budget-16/execution-failure-before-deadline",
    "cp61/observable/row-11/T28-M2-Q/bounded-rejection/budget-16/timeout-censored-at-deadline",
    "cp61/observable/row-12/T28-M2-Q/bounded-rejection/budget-64/returned-rejection-selected-before-deadline",
    "cp61/observable/row-12/T28-M2-Q/bounded-rejection/budget-64/returned-rejection-exhausted-before-deadline",
    "cp61/observable/row-12/T28-M2-Q/bounded-rejection/budget-64/preexecution-refusal-before-deadline",
    "cp61/observable/row-12/T28-M2-Q/bounded-rejection/budget-64/execution-failure-before-deadline",
    "cp61/observable/row-12/T28-M2-Q/bounded-rejection/budget-64/timeout-censored-at-deadline",
    "cp61/observable/row-13/T28-M2-Q/fixed-budget-sir/budget-8/returned-sir-selected-before-deadline",
    "cp61/observable/row-13/T28-M2-Q/fixed-budget-sir/budget-8/preexecution-refusal-before-deadline",
    "cp61/observable/row-13/T28-M2-Q/fixed-budget-sir/budget-8/execution-failure-before-deadline",
    "cp61/observable/row-13/T28-M2-Q/fixed-budget-sir/budget-8/timeout-censored-at-deadline",
    "cp61/observable/row-14/T28-M2-Q/fixed-budget-sir/budget-32/returned-sir-selected-before-deadline",
    "cp61/observable/row-14/T28-M2-Q/fixed-budget-sir/budget-32/preexecution-refusal-before-deadline",
    "cp61/observable/row-14/T28-M2-Q/fixed-budget-sir/budget-32/execution-failure-before-deadline",
    "cp61/observable/row-14/T28-M2-Q/fixed-budget-sir/budget-32/timeout-censored-at-deadline",
    "cp61/observable/row-15/T28-M2-Q/fixed-budget-sir/budget-128/returned-sir-selected-before-deadline",
    "cp61/observable/row-15/T28-M2-Q/fixed-budget-sir/budget-128/preexecution-refusal-before-deadline",
    "cp61/observable/row-15/T28-M2-Q/fixed-budget-sir/budget-128/execution-failure-before-deadline",
    "cp61/observable/row-15/T28-M2-Q/fixed-budget-sir/budget-128/timeout-censored-at-deadline",
    "cp61/observable/row-16/T28-M2-Q/fixed-budget-sir/budget-512/returned-sir-selected-before-deadline",
    "cp61/observable/row-16/T28-M2-Q/fixed-budget-sir/budget-512/preexecution-refusal-before-deadline",
    "cp61/observable/row-16/T28-M2-Q/fixed-budget-sir/budget-512/execution-failure-before-deadline",
    "cp61/observable/row-16/T28-M2-Q/fixed-budget-sir/budget-512/timeout-censored-at-deadline",
    "cp61/rejection-first-attempt/row-01/T28-M1-Q/bounded-rejection/budget-1/attempt-1",
    "cp61/rejection-first-attempt/row-02/T28-M1-Q/bounded-rejection/budget-4/attempt-1",
    "cp61/rejection-first-attempt/row-02/T28-M1-Q/bounded-rejection/budget-4/attempt-2",
    "cp61/rejection-first-attempt/row-02/T28-M1-Q/bounded-rejection/budget-4/attempt-3",
    "cp61/rejection-first-attempt/row-02/T28-M1-Q/bounded-rejection/budget-4/attempt-4",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-1",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-2",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-3",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-4",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-5",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-6",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-7",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-8",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-9",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-10",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-11",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-12",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-13",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-14",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-15",
    "cp61/rejection-first-attempt/row-03/T28-M1-Q/bounded-rejection/budget-16/attempt-16",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-1",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-2",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-3",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-4",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-5",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-6",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-7",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-8",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-9",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-10",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-11",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-12",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-13",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-14",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-15",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-16",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-17",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-18",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-19",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-20",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-21",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-22",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-23",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-24",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-25",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-26",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-27",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-28",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-29",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-30",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-31",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-32",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-33",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-34",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-35",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-36",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-37",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-38",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-39",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-40",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-41",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-42",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-43",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-44",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-45",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-46",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-47",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-48",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-49",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-50",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-51",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-52",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-53",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-54",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-55",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-56",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-57",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-58",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-59",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-60",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-61",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-62",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-63",
    "cp61/rejection-first-attempt/row-04/T28-M1-Q/bounded-rejection/budget-64/attempt-64",
    "cp61/rejection-first-attempt/row-09/T28-M2-Q/bounded-rejection/budget-1/attempt-1",
    "cp61/rejection-first-attempt/row-10/T28-M2-Q/bounded-rejection/budget-4/attempt-1",
    "cp61/rejection-first-attempt/row-10/T28-M2-Q/bounded-rejection/budget-4/attempt-2",
    "cp61/rejection-first-attempt/row-10/T28-M2-Q/bounded-rejection/budget-4/attempt-3",
    "cp61/rejection-first-attempt/row-10/T28-M2-Q/bounded-rejection/budget-4/attempt-4",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-1",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-2",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-3",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-4",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-5",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-6",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-7",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-8",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-9",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-10",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-11",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-12",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-13",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-14",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-15",
    "cp61/rejection-first-attempt/row-11/T28-M2-Q/bounded-rejection/budget-16/attempt-16",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-1",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-2",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-3",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-4",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-5",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-6",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-7",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-8",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-9",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-10",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-11",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-12",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-13",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-14",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-15",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-16",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-17",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-18",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-19",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-20",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-21",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-22",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-23",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-24",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-25",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-26",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-27",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-28",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-29",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-30",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-31",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-32",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-33",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-34",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-35",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-36",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-37",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-38",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-39",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-40",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-41",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-42",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-43",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-44",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-45",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-46",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-47",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-48",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-49",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-50",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-51",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-52",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-53",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-54",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-55",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-56",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-57",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-58",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-59",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-60",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-61",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-62",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-63",
    "cp61/rejection-first-attempt/row-12/T28-M2-Q/bounded-rejection/budget-64/attempt-64",
    "cp61/selected-feature/row-01/T28-M1-Q/bounded-rejection/budget-1/count/eq/0",
    "cp61/selected-feature/row-01/T28-M1-Q/bounded-rejection/budget-1/count/eq/1",
    "cp61/selected-feature/row-01/T28-M1-Q/bounded-rejection/budget-1/type/0/occupancy",
    "cp61/selected-feature/row-01/T28-M1-Q/bounded-rejection/budget-1/type/1/occupancy",
    "cp61/selected-feature/row-01/T28-M1-Q/bounded-rejection/budget-1/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-01/T28-M1-Q/bounded-rejection/budget-1/coordinate/1/axis0/even",
    "cp61/selected-feature/row-02/T28-M1-Q/bounded-rejection/budget-4/count/eq/0",
    "cp61/selected-feature/row-02/T28-M1-Q/bounded-rejection/budget-4/count/eq/1",
    "cp61/selected-feature/row-02/T28-M1-Q/bounded-rejection/budget-4/type/0/occupancy",
    "cp61/selected-feature/row-02/T28-M1-Q/bounded-rejection/budget-4/type/1/occupancy",
    "cp61/selected-feature/row-02/T28-M1-Q/bounded-rejection/budget-4/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-02/T28-M1-Q/bounded-rejection/budget-4/coordinate/1/axis0/even",
    "cp61/selected-feature/row-03/T28-M1-Q/bounded-rejection/budget-16/count/eq/0",
    "cp61/selected-feature/row-03/T28-M1-Q/bounded-rejection/budget-16/count/eq/1",
    "cp61/selected-feature/row-03/T28-M1-Q/bounded-rejection/budget-16/type/0/occupancy",
    "cp61/selected-feature/row-03/T28-M1-Q/bounded-rejection/budget-16/type/1/occupancy",
    "cp61/selected-feature/row-03/T28-M1-Q/bounded-rejection/budget-16/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-03/T28-M1-Q/bounded-rejection/budget-16/coordinate/1/axis0/even",
    "cp61/selected-feature/row-04/T28-M1-Q/bounded-rejection/budget-64/count/eq/0",
    "cp61/selected-feature/row-04/T28-M1-Q/bounded-rejection/budget-64/count/eq/1",
    "cp61/selected-feature/row-04/T28-M1-Q/bounded-rejection/budget-64/type/0/occupancy",
    "cp61/selected-feature/row-04/T28-M1-Q/bounded-rejection/budget-64/type/1/occupancy",
    "cp61/selected-feature/row-04/T28-M1-Q/bounded-rejection/budget-64/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-04/T28-M1-Q/bounded-rejection/budget-64/coordinate/1/axis0/even",
    "cp61/selected-feature/row-05/T28-M1-Q/fixed-budget-sir/budget-8/count/eq/0",
    "cp61/selected-feature/row-05/T28-M1-Q/fixed-budget-sir/budget-8/count/eq/1",
    "cp61/selected-feature/row-05/T28-M1-Q/fixed-budget-sir/budget-8/type/0/occupancy",
    "cp61/selected-feature/row-05/T28-M1-Q/fixed-budget-sir/budget-8/type/1/occupancy",
    "cp61/selected-feature/row-05/T28-M1-Q/fixed-budget-sir/budget-8/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-05/T28-M1-Q/fixed-budget-sir/budget-8/coordinate/1/axis0/even",
    "cp61/selected-feature/row-06/T28-M1-Q/fixed-budget-sir/budget-32/count/eq/0",
    "cp61/selected-feature/row-06/T28-M1-Q/fixed-budget-sir/budget-32/count/eq/1",
    "cp61/selected-feature/row-06/T28-M1-Q/fixed-budget-sir/budget-32/type/0/occupancy",
    "cp61/selected-feature/row-06/T28-M1-Q/fixed-budget-sir/budget-32/type/1/occupancy",
    "cp61/selected-feature/row-06/T28-M1-Q/fixed-budget-sir/budget-32/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-06/T28-M1-Q/fixed-budget-sir/budget-32/coordinate/1/axis0/even",
    "cp61/selected-feature/row-07/T28-M1-Q/fixed-budget-sir/budget-128/count/eq/0",
    "cp61/selected-feature/row-07/T28-M1-Q/fixed-budget-sir/budget-128/count/eq/1",
    "cp61/selected-feature/row-07/T28-M1-Q/fixed-budget-sir/budget-128/type/0/occupancy",
    "cp61/selected-feature/row-07/T28-M1-Q/fixed-budget-sir/budget-128/type/1/occupancy",
    "cp61/selected-feature/row-07/T28-M1-Q/fixed-budget-sir/budget-128/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-07/T28-M1-Q/fixed-budget-sir/budget-128/coordinate/1/axis0/even",
    "cp61/selected-feature/row-08/T28-M1-Q/fixed-budget-sir/budget-512/count/eq/0",
    "cp61/selected-feature/row-08/T28-M1-Q/fixed-budget-sir/budget-512/count/eq/1",
    "cp61/selected-feature/row-08/T28-M1-Q/fixed-budget-sir/budget-512/type/0/occupancy",
    "cp61/selected-feature/row-08/T28-M1-Q/fixed-budget-sir/budget-512/type/1/occupancy",
    "cp61/selected-feature/row-08/T28-M1-Q/fixed-budget-sir/budget-512/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-08/T28-M1-Q/fixed-budget-sir/budget-512/coordinate/1/axis0/even",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/count/eq/0",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/count/eq/1",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/count/eq/2",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/type/0/occupancy",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/type/1/occupancy",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/0/axis0/even",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/axis0/even",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/axis1/even",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-type/0/0",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-type/0/1",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-type/1/1",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-09/T28-M2-Q/bounded-rejection/budget-1/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/count/eq/0",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/count/eq/1",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/count/eq/2",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/type/0/occupancy",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/type/1/occupancy",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/0/axis0/even",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/axis0/even",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/axis1/even",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-type/0/0",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-type/0/1",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-type/1/1",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-10/T28-M2-Q/bounded-rejection/budget-4/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/count/eq/0",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/count/eq/1",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/count/eq/2",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/type/0/occupancy",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/type/1/occupancy",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/0/axis0/even",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/axis0/even",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/axis1/even",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-type/0/0",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-type/0/1",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-type/1/1",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-11/T28-M2-Q/bounded-rejection/budget-16/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/count/eq/0",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/count/eq/1",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/count/eq/2",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/type/0/occupancy",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/type/1/occupancy",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/0/axis0/even",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/axis0/even",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/axis1/even",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-type/0/0",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-type/0/1",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-type/1/1",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-12/T28-M2-Q/bounded-rejection/budget-64/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/count/eq/0",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/count/eq/1",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/count/eq/2",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/type/0/occupancy",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/type/1/occupancy",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/0/axis0/even",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/axis0/even",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/axis1/even",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-type/0/0",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-type/0/1",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-type/1/1",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-13/T28-M2-Q/fixed-budget-sir/budget-8/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/count/eq/0",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/count/eq/1",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/count/eq/2",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/type/0/occupancy",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/type/1/occupancy",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/0/axis0/even",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/axis0/even",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/axis1/even",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-type/0/0",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-type/0/1",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-type/1/1",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-14/T28-M2-Q/fixed-budget-sir/budget-32/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/count/eq/0",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/count/eq/1",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/count/eq/2",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/type/0/occupancy",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/type/1/occupancy",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/0/axis0/even",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/axis0/even",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/axis1/even",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-type/0/0",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-type/0/1",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-type/1/1",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-15/T28-M2-Q/fixed-budget-sir/budget-128/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/count/eq/0",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/count/eq/1",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/count/eq/2",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/type/0/occupancy",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/type/1/occupancy",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/0/axis0/odd",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/0/axis0/even",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/axis0/odd",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/axis0/even",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/axis1/odd",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/axis1/even",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/diag-plus-3-4/odd",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/diag-plus-3-4/even",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/diag-minus-3-4/odd",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/coordinate/1/diag-minus-3-4/even",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-type/0/0",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-type/0/1",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-type/1/1",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/0/axis0/0/axis0",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/0/axis0/1/axis0",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/0/axis0/1/axis1",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/0/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/0/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/axis0/1/axis0",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/axis0/1/axis1",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/axis0/1/diag-plus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/axis0/1/diag-minus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/axis1/1/axis1",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/axis1/1/diag-plus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/axis1/1/diag-minus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "cp61/selected-feature/row-16/T28-M2-Q/fixed-budget-sir/budget-512/pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
)
_ROW_INVENTORY = (
    (
        1,
        "row-01/T28-M1-Q/bounded-rejection/budget-1",
        "T28-M1-Q",
        "bounded-rejection",
        1,
        "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a",
    ),
    (
        2,
        "row-02/T28-M1-Q/bounded-rejection/budget-4",
        "T28-M1-Q",
        "bounded-rejection",
        4,
        "f9f2d4f1d8aad14bbe5075b4febd763af4652fb4dda337e7a8d295b3a6045ec2",
    ),
    (
        3,
        "row-03/T28-M1-Q/bounded-rejection/budget-16",
        "T28-M1-Q",
        "bounded-rejection",
        16,
        "4413d707c0165dbf18e88df043edd760a75d4eed44d039a611402e06de9c4eb8",
    ),
    (
        4,
        "row-04/T28-M1-Q/bounded-rejection/budget-64",
        "T28-M1-Q",
        "bounded-rejection",
        64,
        "29f1f28fb222d258746cb7956a9ca0d65a6e97d398eddb1612720a9339eed338",
    ),
    (
        5,
        "row-05/T28-M1-Q/fixed-budget-sir/budget-8",
        "T28-M1-Q",
        "fixed-budget-sir",
        8,
        "71701768f889fee219b854217de255f3d034202a3a66875ceade1cd55955896a",
    ),
    (
        6,
        "row-06/T28-M1-Q/fixed-budget-sir/budget-32",
        "T28-M1-Q",
        "fixed-budget-sir",
        32,
        "bd7c4fd661bda70f29b8582c0db52d91d68fc703ae8838295a21cf9e6e55f23a",
    ),
    (
        7,
        "row-07/T28-M1-Q/fixed-budget-sir/budget-128",
        "T28-M1-Q",
        "fixed-budget-sir",
        128,
        "801f600536240a2f6f3de0dcac8d4092c2121fd17dc14fb0ca0bfc3b0260acb8",
    ),
    (
        8,
        "row-08/T28-M1-Q/fixed-budget-sir/budget-512",
        "T28-M1-Q",
        "fixed-budget-sir",
        512,
        "8e5458a8dfca1e49875cad53deff7447274ce3055960a0031cc07c4ec4de33e0",
    ),
    (
        9,
        "row-09/T28-M2-Q/bounded-rejection/budget-1",
        "T28-M2-Q",
        "bounded-rejection",
        1,
        "7d32b4e85d39504864268b7ba39189f17c3171d11079638e37a6614b97a543bf",
    ),
    (
        10,
        "row-10/T28-M2-Q/bounded-rejection/budget-4",
        "T28-M2-Q",
        "bounded-rejection",
        4,
        "17f11b448585709ef35a172e86665c83b2ea50a907caacdd400dbd8ce625771b",
    ),
    (
        11,
        "row-11/T28-M2-Q/bounded-rejection/budget-16",
        "T28-M2-Q",
        "bounded-rejection",
        16,
        "57937405e7302fcd9b9935050050a74e4b2c2818e17d720cde1ee2a56352bcf3",
    ),
    (
        12,
        "row-12/T28-M2-Q/bounded-rejection/budget-64",
        "T28-M2-Q",
        "bounded-rejection",
        64,
        "878797b61ec628ae5db0e882d6f3c34531468fbbc35fd92325063a3b017c1bd8",
    ),
    (
        13,
        "row-13/T28-M2-Q/fixed-budget-sir/budget-8",
        "T28-M2-Q",
        "fixed-budget-sir",
        8,
        "bc7b374f072aa402264634bcf520834a71609af5f6705b9b8ac3079884cd0376",
    ),
    (
        14,
        "row-14/T28-M2-Q/fixed-budget-sir/budget-32",
        "T28-M2-Q",
        "fixed-budget-sir",
        32,
        "1b60b917c4fba30085678101276fe2a210aaa82f34deb6ad4f9440a38cc3b074",
    ),
    (
        15,
        "row-15/T28-M2-Q/fixed-budget-sir/budget-128",
        "T28-M2-Q",
        "fixed-budget-sir",
        128,
        "a88491906e47ec4f5483b638ce411b8afd4ce7b5d73f19e372ab68a405f6d81c",
    ),
    (
        16,
        "row-16/T28-M2-Q/fixed-budget-sir/budget-512",
        "T28-M2-Q",
        "fixed-budget-sir",
        512,
        "0667c6c19a9b54db91f2167f685abdcaafcab73cbc4bcfaebcb420511ecc89c8",
    ),
)


def _require_sha256(value: object, name: str, *, nonzero: bool = False) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(name + " must be exact lowercase SHA256 hex")
    if nonzero and value == _ZERO_SHA256:
        raise ValueError(name + " must be nonzero")
    return value


def _require_utc(value: object, name: str) -> str:
    if type(value) is not str or _UTC_RE.fullmatch(value) is None:
        raise ValueError(name + " must be exact UTC microsecond text")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ValueError(name + " calendar value differs") from exc
    return value


def _parse_canonical_threshold_rational(value: str, name: str) -> Tuple[int, int]:
    match = re.fullmatch(r"(-?(?:0|[1-9][0-9]*))/([1-9][0-9]*)", value)
    if match is None or value.startswith("-0"):
        raise ValueError(name + " must be a canonical rational threshold")
    numerator_text, denominator_text = match.groups()
    if len(numerator_text.lstrip("-")) > 39 or len(denominator_text) > 39:
        raise ValueError(name + " rational integer is outside its lexical bound")
    numerator = int(numerator_text)
    denominator = int(denominator_text)
    if not -(2**127) + 1 <= numerator <= 2**127 - 1:
        raise ValueError(name + " numerator is outside signed-127 bounds")
    if not 1 <= denominator <= 2**127 - 1:
        raise ValueError(name + " denominator is outside positive-127 bounds")
    if math.gcd(abs(numerator), denominator) != 1:
        raise ValueError(name + " rational is not in lowest terms")
    if numerator == 0 and denominator != 1:
        raise ValueError(name + " zero rational must be 0/1")
    return numerator, denominator


def _require_relative_path(value: object, name: str) -> str:
    if type(value) is not str:
        raise ValueError(name + " must be a relative path string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(name + " must be ASCII") from exc
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or "\0" in value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise ValueError(name + " is not a normalized POSIX relative path")
    return value


def _schema_value(artifact_id: str) -> str:
    if artifact_id == "seed-capsule-body":
        return _CP63_SCHEMA_VERSION
    return _ARTIFACT_BY_ID[artifact_id][6]


def _relative_path_matches(artifact_id: str, relative_path: str) -> bool:
    template = _ARTIFACT_BY_ID[artifact_id][1]
    if "{shard_id}" in template:
        prefix, suffix = template.split("{shard_id}")
        if relative_path.startswith(prefix) and relative_path.endswith(suffix):
            shard_id = relative_path[
                len(prefix) : len(relative_path) - len(suffix) if suffix else None
            ]
            return _SHARD_ID_RE.fullmatch(shard_id) is not None
        return False
    return relative_path == template


def _validate_scalar_field(
    artifact_id: str,
    pointer: str,
    key: str,
    value: object,
) -> None:
    exact_integer = _INTEGER_EXACT.get((artifact_id, key))
    if exact_integer is not None:
        if type(value) is not int or value != exact_integer:
            raise ValueError(pointer + " differs from its exact integer")
        return
    integer_interval = _INTEGER_INTERVALS.get((artifact_id, pointer))
    if integer_interval is not None:
        if (
            type(value) is not int
            or not integer_interval[0] <= value <= integer_interval[1]
        ):
            raise ValueError(pointer + " differs from its exact integer interval")
        return
    if "/terminal_counts/" in pointer or key in ("lines", "budget"):
        if type(value) is not int or not 0 <= value <= 2**63 - 1:
            raise ValueError(pointer + " must be a bounded nonnegative integer")
        return
    kind = _explicit_field_kind(key)
    if kind == "boolean":
        if type(value) is not bool:
            raise ValueError(pointer + " must be an exact boolean")
        if (
            key
            in (
                "production_runner_rng_or_child_started_before_receipt",
                "topup_redraw_reselection_permitted",
            )
            and value is not False
        ):
            raise ValueError(pointer + " must be the exact false sentinel")
        return
    if kind == "integer":
        if type(value) is not int or not 0 <= value <= 2**64 - 1:
            raise ValueError(pointer + " must be a bounded nonnegative integer")
        return
    if kind == "object":
        if type(value) is not dict:
            raise ValueError(pointer + " must be an exact object")
        return
    if type(value) is not str:
        raise ValueError(pointer + " must be an exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(pointer + " must be ASCII") from exc
    maximum_string_bytes = 1_048_576
    if artifact_id == "power-threshold-receipt" and key in (
        "selected_count_justification_ascii",
        "justification_ascii",
    ):
        maximum_string_bytes = 16_384
    elif artifact_id == "external-digest-preimage-registry" and key == "preimage_ascii":
        maximum_string_bytes = 131_072
    if len(encoded) > maximum_string_bytes:
        raise ValueError(pointer + " string is too long")
    if (
        artifact_id == "auxiliary-metadata-reservation"
        and key
        in (
            "alternate_final_relative_path",
            "alternate_publication_arm_id",
            "partial_relative_path",
            "file_fsync_completed_at_utc",
            "directory_fsync_completed_at_utc",
        )
        and value == ""
    ):
        return
    if (
        artifact_id == "external-digest-preimage-registry"
        and key in ("domain_separator", "preimage_ascii")
        and value == ""
    ):
        return
    domain = _string_domain_for_field(artifact_id, pointer, key)
    if key == "schema":
        domain = (_schema_value(artifact_id),)
    if key == "schema_version" and artifact_id == "production-schedule":
        domain = (_CP63_SCHEMA_VERSION,)
    if key == "terminal_state" and artifact_id in (
        "preauthorization-outcome",
        "postauthorization-outcome",
    ):
        domain = ("", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE")
    if domain and value not in domain:
        raise ValueError(pointer + " differs from its closed string domain")
    pattern = _pattern_id(key)
    if pattern == "lowercase-sha256-hex":
        _require_sha256(value, pointer)
    elif pattern == "lowercase-hex-16" and _HEX16_RE.fullmatch(value) is None:
        raise ValueError(pointer + " must be 16 lowercase hex characters")
    elif pattern == "lowercase-hex-768" and _HEX768_RE.fullmatch(value) is None:
        raise ValueError(pointer + " must be 768 lowercase hex characters")
    elif pattern == "utc-microseconds-z":
        _require_utc(value, pointer)
    elif pattern == "posix-relative-path":
        _require_relative_path(value, pointer)
    elif (
        pattern == "shard-id-0001-through-0032"
        and _SHARD_ID_RE.fullmatch(value) is None
    ):
        raise ValueError(pointer + " must be a canonical shard id")
    elif pattern == "attempt-id-v1" and _ATTEMPT_ID_RE.fullmatch(value) is None:
        raise ValueError(pointer + " must be a canonical attempt id")
    elif (
        pattern == "opaque-method-session-authority-id-v1"
        and _OPAQUE_METHOD_SESSION_AUTHORITY_ID_RE.fullmatch(value) is None
    ):
        raise ValueError(pointer + " must be a canonical opaque identifier")
    elif pattern == "canonical-rational-threshold-v1":
        _parse_canonical_threshold_rational(value, pointer)
    elif (
        pattern == "bounded-nonempty-ascii"
        and not encoded
        and not (
            key == "terminal_state"
            and artifact_id
            in (
                "preauthorization-outcome",
                "postauthorization-outcome",
            )
        )
    ):
        raise ValueError(pointer + " must be nonempty")


def _validate_nested_rows(
    artifact_id: str,
    document: dict,
    nested: Tuple[Tuple[str, Tuple[str, ...]], ...],
) -> None:
    for container_key, exact_keys in nested:
        container = document[container_key]
        if container_key == "terminal_counts":
            if (
                type(container) is not dict
                or set(container) != set(exact_keys)
                or len(container) != len(exact_keys)
            ):
                raise ValueError("terminal_counts field set differs")
            for key in exact_keys:
                _validate_scalar_field(
                    artifact_id, "/terminal_counts/" + key, key, container[key]
                )
            continue
        if type(container) is not list:
            raise ValueError("/%s must be an exact array" % container_key)
        exact_length = _ARRAY_LENGTH_EXACT.get((artifact_id, container_key))
        if exact_length is not None and len(container) != exact_length:
            raise ValueError("/%s array length differs" % container_key)
        for index, row in enumerate(container):
            if (
                type(row) is not dict
                or set(row) != set(exact_keys)
                or len(row) != len(exact_keys)
            ):
                raise ValueError("/%s/%d field set differs" % (container_key, index))
            for key in exact_keys:
                if _explicit_field_kind(key) == "array":
                    _validate_primitive_array(artifact_id, key, row[key])
                else:
                    _validate_scalar_field(
                        artifact_id,
                        "/%s/%d/%s" % (container_key, index, key),
                        key,
                        row[key],
                    )
            digest_info = _NESTED_DIGESTS.get((artifact_id, container_key))
            if digest_info is not None:
                digest_key, domain = digest_info
                supplied = _require_sha256(row[digest_key], digest_key)
                zeroed = dict(row)
                zeroed[digest_key] = _ZERO_SHA256
                expected = hashlib.sha256(
                    domain.encode("ascii") + b"\0" + _plain_json_bytes(zeroed)
                ).hexdigest()
                if supplied != expected:
                    raise ValueError(
                        "/%s/%d nested digest differs" % (container_key, index)
                    )


def _validate_body_digest(artifact_id: str, document: dict) -> str:
    declaration = _ARTIFACT_BY_ID[artifact_id]
    domain = declaration[6]
    supplied = _require_sha256(document["body_sha256"], "/body_sha256")
    zeroed = dict(document)
    zeroed["body_sha256"] = _ZERO_SHA256
    expected = hashlib.sha256(
        domain.encode("ascii") + b"\0" + _plain_json_bytes(zeroed)
    ).hexdigest()
    if supplied != expected:
        raise ValueError("artifact body digest differs")
    return supplied


def _validate_primitive_array(artifact_id: str, key: str, value: object) -> list:
    if type(value) is not list:
        raise ValueError("/%s must be an exact array" % key)
    exact_length = _ARRAY_LENGTH_EXACT.get((artifact_id, key))
    if exact_length is not None and len(value) != exact_length:
        raise ValueError("/%s array length differs" % key)
    if len(value) > 32_768:
        raise ValueError("/%s array exceeds the frozen bound" % key)
    if key == "seed_ordinals":
        if value != list(range(1, 2_049)):
            raise ValueError("seed ordinals differ from 1..2048")
    elif key in ("ordered_seed_values", "ordered_partial_seed_values"):
        if any(
            type(item) is not str or _HEX16_RE.fullmatch(item) is None for item in value
        ):
            raise ValueError("seed value array is not exact uint64 hex")
    elif key in (
        "ordered_slot_threshold_row_sha256s",
        "ordered_entry_sha256s",
        "ordered_public_key_identity_sha256s",
        "ordered_request_record_sha256s",
        "per_file_reservation_manifest_entry_sha256s",
        "ordered_evidence_receipt_sha256s",
        "reviewed_artifact_sha256s",
    ):
        for item in value:
            _require_sha256(item, "/%s/*" % key)
    elif key == "closed_refusal_codes" and tuple(value) != _CLOSED_REFUSAL_CODES:
        raise ValueError("closed refusal code tuple differs")
    elif key == "closed_failure_codes" and tuple(value) != _CLOSED_FAILURE_CODES:
        raise ValueError("closed failure code tuple differs")
    elif key == "covered_gate_ids" and tuple(value) != _GATE_IDS[:15]:
        raise ValueError("preflight covered gate order differs")
    elif key == "covered_gate_states" and tuple(value) != ("PASS",) * 15:
        raise ValueError("preflight covered gate states differ")
    elif (
        key == "covered_evidence_node_ids" and tuple(value) != _GATE_EVIDENCE_NODES[:15]
    ):
        raise ValueError("preflight evidence node order differs")
    elif key == "required_reviewer_roles" and tuple(value) != _REQUIRED_REVIEWER_ROLES:
        raise ValueError("required reviewer roles differ")
    return value


def _auxiliary_expected_slots() -> Tuple[Tuple[object, ...], ...]:
    bounds = {
        bound.artifact_id: bound
        for bound in _build_auxiliary_bounds()
        if not bound.artifact_id.startswith("__")
    }
    result = []
    for (
        artifact_id,
        path,
        scope,
        _media,
        _keys,
        _nested,
        _domain,
        _preserved,
    ) in _ARTIFACT_DECLARATIONS:
        if artifact_id in _DESTINATION_IDS:
            continue
        if artifact_id == "rejected-launch-authorization-candidate":
            continue
        if scope == "per-shard":
            for ordinal in range(1, 33):
                final_path = path.replace("{shard_id}", "shard-%04d" % ordinal)
                result.append(
                    (
                        artifact_id,
                        final_path,
                        "",
                        bounds[artifact_id].maximum_logical_bytes_per_instance,
                        bounds[artifact_id].maximum_reserved_bytes_per_instance,
                        "UNCONDITIONAL",
                        "",
                    )
                )
        else:
            alternate_path = (
                _ARTIFACT_BY_ID["rejected-launch-authorization-candidate"][1]
                if artifact_id == "launch-authorization"
                else ""
            )
            primary_arm = "UNCONDITIONAL"
            alternate_arm = ""
            if artifact_id == "launch-authorization":
                primary_arm = "AUTHORIZATION"
                alternate_arm = "PREAUTHORIZATION_TERMINAL"
            elif artifact_id == "committed-marker":
                primary_arm = "DIRECT_O_EXCL_AFTER_HOLD_RELEASE"
            elif artifact_id == "auxiliary-reservation-transition-journal":
                primary_arm = "IN_PLACE_TRANSITION_JOURNAL"
            result.append(
                (
                    artifact_id,
                    path,
                    alternate_path,
                    bounds[artifact_id].maximum_logical_bytes_per_instance,
                    bounds[artifact_id].maximum_reserved_bytes_per_instance,
                    primary_arm,
                    alternate_arm,
                )
            )
    result.sort(key=lambda row: row[1])
    if len(result) != 183 or len({row[1] for row in result}) != 183:
        raise RuntimeError("CP65 auxiliary slot expansion differs")
    return tuple(result)


def _independent_recomputation_source_submanifest_sha256(
    document: object,
) -> str:
    """Hash the nonempty, role-filtered independent source submanifest."""

    if type(document) is not dict or set(document) != set(_SOURCE_MANIFEST_KEYS):
        raise ValueError("source manifest keyset differs")
    entries = document.get("entries")
    entry_count = document.get("entry_count")
    if (
        type(entries) is not list
        or type(entry_count) is not int
        or entry_count != len(entries)
    ):
        raise ValueError("source manifest entry count differs")
    selected = []
    production_paths = set()
    independent_paths = set()
    previous_path = ""
    allowed_roles = {
        "production-runner-source",
        "independent-recomputation-source",
    }
    for ordinal, entry in enumerate(entries, 1):
        if type(entry) is not dict or set(entry) != set(_SOURCE_MANIFEST_ENTRY_KEYS):
            raise ValueError("source manifest entry keyset differs")
        if entry["ordinal"] != ordinal:
            raise ValueError("source manifest entry ordinals differ")
        role = entry["role"]
        path = entry["relative_path"]
        if role not in allowed_roles:
            raise ValueError("source manifest role differs")
        if (
            type(path) is not str
            or not path
            or (previous_path and path <= previous_path)
        ):
            raise ValueError("source manifest path order differs")
        previous_path = path
        if role == "independent-recomputation-source":
            selected.append(entry)
            independent_paths.add(path)
        else:
            production_paths.add(path)
    if not selected:
        raise ValueError("independent recomputation source submanifest is empty")
    if independent_paths.intersection(production_paths):
        raise ValueError("source manifest role partitions overlap")
    preimage = {"entry_count": len(selected), "entries": selected}
    return hashlib.sha256(
        b"cp65-test28-independent-recomputation-source-submanifest-v1\0"
        + _plain_json_bytes(preimage)
    ).hexdigest()


def _validate_preflight_gate_summary_evidence(
    document: dict,
    evidence_raw_by_artifact_id: Mapping[str, bytes],
) -> int:
    if type(document) is not dict or set(document) != set(_PREFLIGHT_SUMMARY_KEYS):
        raise ValueError("preflight gate summary keyset differs")
    if type(evidence_raw_by_artifact_id) is not dict:
        raise TypeError("preflight evidence map must be an exact dictionary")
    requirements = _build_gate_requirements()[:15]
    evidence_ids = tuple(row.evidence_artifact_id for row in requirements)
    if tuple(document["covered_gate_ids"]) != tuple(
        row.gate_id for row in requirements
    ):
        raise ValueError("preflight covered gate IDs differ")
    if tuple(document["covered_gate_states"]) != ("PASS",) * 15:
        raise ValueError("preflight covered gate states differ")
    if tuple(document["covered_evidence_node_ids"]) != tuple(
        row.evidence_node_id for row in requirements
    ):
        raise ValueError("preflight evidence node IDs differ")
    if (
        set(evidence_raw_by_artifact_id) != set(evidence_ids)
        or len(evidence_raw_by_artifact_id) != 15
    ):
        raise ValueError("preflight evidence artifact set differs")
    ordered = []
    for artifact_id in evidence_ids:
        raw = evidence_raw_by_artifact_id[artifact_id]
        if type(raw) is not bytes:
            raise TypeError("preflight evidence bytes have the wrong exact type")
        ordered.append(hashlib.sha256(raw).hexdigest())
    if tuple(document["ordered_evidence_receipt_sha256s"]) != tuple(ordered):
        raise ValueError("preflight ordered evidence digest vector differs")
    return 15


def _validate_receipt_specific(artifact_id: str, document: dict) -> None:
    if artifact_id == "external-digest-preimage-registry":
        entries = document["entries"]
        count = document["entry_count"]
        if type(count) is not int or not 0 <= count <= 4_096 or len(entries) != count:
            raise ValueError("external digest registry entry count differs")
        registry_field_rules = _build_field_rules()
        registry_digest_contracts = _build_digest_contracts(registry_field_rules)
        registry_pointer_contracts = {
            row.classification_id: row
            for row in _build_sha256_pointer_contracts(
                registry_field_rules, registry_digest_contracts
            )
            if row.preimage_registry_entry_required
        }
        encoded_total = 0
        ordered = []
        sort_keys = []
        for ordinal, row in enumerate(entries, 1):
            if row["ordinal"] != ordinal:
                raise ValueError("external digest registry ordinals differ")
            pointer_contract = registry_pointer_contracts.get(row["classification_id"])
            if pointer_contract is None or (
                row["target_artifact_id"],
                row["target_json_pointer"],
            ) != (
                pointer_contract.target_artifact_id,
                pointer_contract.target_json_pointer,
            ):
                raise ValueError("external digest registry classification differs")
            if row["target_artifact_id"] not in _ARTIFACT_BY_ID:
                raise ValueError("external digest registry target artifact differs")
            if not _relative_path_matches(
                row["target_artifact_id"], row["target_relative_path"]
            ):
                raise ValueError("external digest registry target path differs")
            selector_ascii = row["target_instance_selector_json_ascii"]
            if not 1 <= len(selector_ascii.encode("ascii")) <= 4_096:
                raise ValueError("external digest registry selector size differs")
            selector = _parse_canonical_json_object(
                selector_ascii.encode("ascii"), 4_096
            )
            if tuple(selector) != (
                "artifact_instance_ordinal",
                "shard_ordinal",
                "wildcard_indices",
            ):
                raise ValueError("external digest registry selector keys differ")
            instance_ordinal = selector["artifact_instance_ordinal"]
            shard_ordinal = selector["shard_ordinal"]
            wildcard_indices = selector["wildcard_indices"]
            if type(instance_ordinal) is not int or not 1 <= instance_ordinal <= 312:
                raise ValueError("registry artifact instance ordinal differs")
            if type(shard_ordinal) is not int or not (
                shard_ordinal == 0 or 1 <= shard_ordinal <= 32
            ):
                raise ValueError("registry shard ordinal differs")
            if (
                type(wildcard_indices) is not list
                or len(wildcard_indices) > 8
                or any(
                    type(index) is not int or not 0 <= index <= 32_767
                    for index in wildcard_indices
                )
            ):
                raise ValueError("registry wildcard selector differs")
            wildcard_count = pointer_contract.target_json_pointer.count("*")
            if len(wildcard_indices) != wildcard_count:
                raise ValueError("registry wildcard selector cardinality differs")
            pointer_parts = tuple(
                part for part in pointer_contract.target_json_pointer.split("/") if part
            )
            wildcard_ordinal = 0
            for part_index, part in enumerate(pointer_parts):
                if part != "*":
                    continue
                container_key = pointer_parts[part_index - 1]
                maximum = _POINTER_WILDCARD_CARDINALITIES.get(
                    (pointer_contract.target_artifact_id, container_key)
                )
                selected_index = wildcard_indices[wildcard_ordinal]
                wildcard_ordinal += 1
                if maximum is None or selected_index >= maximum:
                    raise ValueError("registry wildcard selector is out of range")
                if (
                    pointer_contract.target_artifact_id
                    == "auxiliary-metadata-reservation"
                    and container_key == "artifact_entries"
                    and _auxiliary_expected_slots()[selected_index][0]
                    == "committed-marker"
                ):
                    raise ValueError("registry selector targets a conditional zero arm")
            target_scope = _ARTIFACT_BY_ID[row["target_artifact_id"]][2]
            if target_scope == "per-shard":
                if shard_ordinal == 0 or instance_ordinal != shard_ordinal:
                    raise ValueError("registry shard instance selector differs")
            elif shard_ordinal != 0 or instance_ordinal != 1:
                raise ValueError("registry global instance selector differs")
            _require_sha256(
                row["target_artifact_raw_sha256"],
                "registry target raw digest",
                nonzero=True,
            )
            encoding = row["preimage_encoding"]
            preimage_ascii = row["preimage_ascii"]
            if encoding == "ascii":
                decoded = preimage_ascii.encode("ascii")
            elif encoding == "lowercase-hex":
                if (
                    len(preimage_ascii) % 2
                    or re.fullmatch(r"[0-9a-f]*", preimage_ascii) is None
                ):
                    raise ValueError("registry lowercase-hex preimage differs")
                decoded = bytes.fromhex(preimage_ascii)
            else:
                raise ValueError("registry preimage encoding differs")
            if len(decoded) != row["preimage_bytes"] or len(decoded) > 65_536:
                raise ValueError("registry decoded preimage size differs")
            encoded_total += len(preimage_ascii)
            digest_kind = row["digest_kind"]
            domain = row["domain_separator"]
            expected_kind = (
                "domain-separated-sha256"
                if pointer_contract.domain_separator
                else "plain-sha256"
            )
            if (
                digest_kind != expected_kind
                or domain != pointer_contract.domain_separator
            ):
                raise ValueError(
                    "registry digest profile differs from pointer contract"
                )
            if digest_kind == "plain-sha256":
                if domain != "":
                    raise ValueError("plain registry digest has a domain")
                expected_digest = hashlib.sha256(decoded).hexdigest()
            elif digest_kind == "domain-separated-sha256":
                domain_bytes = domain.encode("ascii")
                if not 1 <= len(domain_bytes) <= 256 or not domain.endswith("\0"):
                    raise ValueError("registry digest domain differs")
                expected_digest = hashlib.sha256(domain_bytes + decoded).hexdigest()
            else:
                raise ValueError("registry digest kind differs")
            if row["digest_sha256"] != expected_digest:
                raise ValueError("registry supplied preimage digest differs")
            ordered.append(row["entry_sha256"])
            sort_keys.append(
                (
                    row["target_artifact_id"],
                    row["target_relative_path"],
                    row["target_json_pointer"],
                    selector_ascii,
                    row["classification_id"],
                )
            )
        if encoded_total > 62_914_560:
            raise ValueError("registry encoded preimage aggregate exceeds its cap")
        if sort_keys != sorted(sort_keys) or len(set(sort_keys)) != len(sort_keys):
            raise ValueError("registry targets are not canonical and unique")
        if tuple(document["ordered_entry_sha256s"]) != tuple(ordered):
            raise ValueError("registry entry digest vector differs")
        expected_ordered = hashlib.sha256(
            b"cp65-test28-external-digest-preimage-registry-ordered-entries-v1\0"
            + b"".join(bytes.fromhex(item) for item in ordered)
        ).hexdigest()
        if document["ordered_entries_sha256"] != expected_ordered:
            raise ValueError("registry ordered-entry digest differs")
    elif artifact_id == "power-threshold-receipt":
        review = document["power_review_ascii"].encode("ascii")
        selected = document["selected_count_justification_ascii"].encode("ascii")
        if not review or not selected:
            raise ValueError("power-review preimage text must be nonempty")
        if (
            document["power_review_sha256"]
            != hashlib.sha256(
                b"cp65-test28-power-review-text-v1\0" + review
            ).hexdigest()
        ):
            raise ValueError("power-review text digest differs")
        if (
            document["selected_count_justification_sha256"]
            != hashlib.sha256(
                b"cp65-test28-selected-count-justification-v1\0" + selected
            ).hexdigest()
        ):
            raise ValueError("selected-count justification digest differs")
        row_digests = []
        estimand_positions = []
        estimand_index = {
            estimand_id: index for index, estimand_id in enumerate(_CP61_ESTIMAND_IDS)
        }
        for ordinal, row in enumerate(document["ordered_slot_thresholds"], 1):
            if (
                row["slot_ordinal"] != ordinal
                or row["gate_id"] != _POWER_PRIMARY_SLOT_IDS[ordinal - 1]
                or row["threshold_encoding"]
                != "canonical-rational-signed-numerator-positive-denominator-lowest-terms-v1"
                or row["design_minimum_selected_count"] != 1_040
            ):
                raise ValueError("power threshold row design identity differs")
            if row["estimand_id"] not in estimand_index:
                raise ValueError("power threshold estimand is outside CP61 inventory")
            estimand_positions.append(estimand_index[row["estimand_id"]])
            _parse_canonical_threshold_rational(
                row["threshold_value"], "threshold_value"
            )
            justification = row["justification_ascii"].encode("ascii")
            if not justification:
                raise ValueError("threshold-row justification must be nonempty")
            if (
                row["justification_sha256"]
                != hashlib.sha256(
                    b"cp65-test28-threshold-row-justification-v1\0" + justification
                ).hexdigest()
            ):
                raise ValueError("threshold-row justification digest differs")
            row_digests.append(row["row_sha256"])
        if estimand_positions != sorted(set(estimand_positions)):
            raise ValueError("power threshold estimands are not unique and ordered")
        if tuple(document["ordered_slot_threshold_row_sha256s"]) != tuple(row_digests):
            raise ValueError("power threshold row-digest vector differs")
        if (
            document["ordered_slot_thresholds_sha256"]
            != hashlib.sha256(
                b"cp65-test28-power-threshold-rows-v1\0"
                + _plain_json_bytes(row_digests)
            ).hexdigest()
        ):
            raise ValueError("ordered power-threshold digest differs")
    elif artifact_id == "seed-capsule-body":
        if document["cp61_stable_design_sha256"] != _CP61_STABLE_DESIGN_SHA256:
            raise ValueError("seed capsule design custody differs")
        if document["seed_count"] != 2_048:
            raise ValueError("seed capsule count differs")
        if (
            type(document["source_method_id"]) is not str
            or not 1 <= len(document["source_method_id"].encode("ascii")) <= 4_096
        ):
            raise ValueError("seed capsule source method differs")
    elif artifact_id == "external-seed-source-receipt":
        if document["seed_count"] != 2_048:
            raise ValueError("completed source receipt seed count differs")
        if document["acquisition_journal_entry_count"] != 2_048:
            raise ValueError("completed source journal count differs")
        if (
            document["acquisition_start_receipt_sha256"]
            != document["acquisition_session_sha256"]
        ):
            raise ValueError("completed source start-receipt aliases differ")
    elif artifact_id == "partial-seed-acquisition-terminal-receipt":
        count = document["acquired_seed_count"]
        if type(count) is not int or not 0 <= count <= 2_048:
            raise ValueError("partial acquisition count differs")
        if document["acquisition_journal_entry_count"] != count:
            raise ValueError("partial journal count differs")
        if document["acquisition_journal_raw_bytes"] != 163_840:
            raise ValueError("partial journal full preallocation bytes differ")
        if len(document["ordered_partial_seed_values"]) != count:
            raise ValueError("partial seed list length differs")
        if document["topup_redraw_reselection_permitted"] is not False:
            raise ValueError("partial source topup/redraw must be false")
    elif artifact_id == "production-schedule":
        requests = document["requests"]
        digests = document["ordered_request_record_sha256s"]
        if len(requests) != 32_768 or len(digests) != 32_768:
            raise ValueError("production schedule row count differs")
        for index, row in enumerate(requests, 1):
            seed_ordinal = (index - 1) // 16 + 1
            row_ordinal = (index - 1) % 16 + 1
            inventory = _ROW_INVENTORY[row_ordinal - 1]
            exact = {
                "schema_version": _CP63_SCHEMA_VERSION,
                "seed_ordinal": seed_ordinal,
                "row_ordinal": row_ordinal,
                "logical_request_ordinal": index,
                "row_key": inventory[1],
                "fixture_id": inventory[2],
                "strategy": inventory[3],
                "budget": inventory[4],
                "seed_free_request_sha256": inventory[5],
                "runtime_lock_sha256": _CP63_RUNTIME_LOCK_SHA256,
            }
            if any(
                type(row[key]) is not type(expected) or row[key] != expected
                for key, expected in exact.items()
            ):
                raise ValueError("production schedule request identity differs")
            identity = {key: row[key] for key in _SCHEDULE_REQUEST_KEYS[:12]}
            expected_instance = hashlib.sha256(
                b"cp63-test28-bound-request-v1\0" + _plain_json_bytes(identity)
            ).hexdigest()
            if row["request_instance_sha256"] != expected_instance:
                raise ValueError("production schedule request instance digest differs")
            if digests[index - 1] != row["request_row_sha256"]:
                raise ValueError("production schedule digest vector differs")
        expected_ordered = hashlib.sha256(
            b"cp65-test28-production-schedule-ordered-requests-v1\0"
            + _plain_json_bytes(digests)
        ).hexdigest()
        if document["ordered_requests_sha256"] != expected_ordered:
            raise ValueError("production schedule ordered digest differs")
    elif artifact_id == "source-manifest":
        entries = document["entries"]
        if not 1 <= len(entries) <= _MAX_SOURCE_MANIFEST_ENTRIES or document[
            "entry_count"
        ] != len(entries):
            raise ValueError("source manifest entry count differs")
        ordinals = [row["ordinal"] for row in entries]
        paths = [row["relative_path"] for row in entries]
        if ordinals != list(range(1, len(entries) + 1)) or paths != sorted(set(paths)):
            raise ValueError("source manifest entries are not ordered and unique")
        if document["total_bytes"] != sum(row["bytes"] for row in entries):
            raise ValueError("source manifest total bytes differs")
        expected_ordered = hashlib.sha256(
            b"cp65-test28-source-manifest-ordered-entries-v1\0"
            + _plain_json_bytes(entries)
        ).hexdigest()
        if document["ordered_entries_sha256"] != expected_ordered:
            raise ValueError("source manifest ordered-entry digest differs")
        _independent_recomputation_source_submanifest_sha256(document)
    elif artifact_id == "preflight-gate-summary":
        for digest in document["ordered_evidence_receipt_sha256s"]:
            _require_sha256(digest, "preflight evidence digest", nonzero=True)
    elif artifact_id == "closed-refusal-failure-classifier-qualification-receipt":
        pass
    elif artifact_id == "started-receipt":
        if (
            document["production_runner_rng_or_child_started_before_receipt"]
            is not False
        ):
            raise ValueError("STARTED receipt ordering boolean differs")
    elif artifact_id == "shard-receipt":
        if sum(document["terminal_counts"].values()) != document["request_count"]:
            raise ValueError("shard terminal counts do not sum to request count")
        if document["request_count"] != 1_024:
            raise ValueError("shard receipt request count differs")
    elif artifact_id in ("preauthorization-outcome",):
        arm = document["outcome_arm"]
        if arm not in (
            "AUTHORIZATION",
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("preauthorization outcome arm differs")
        if arm == "AUTHORIZATION":
            _require_sha256(
                document["prepared_launch_authorization_sha256"],
                "prepared authorization",
                nonzero=True,
            )
            if document["terminal_state"] != "":
                raise ValueError("authorization arm terminal state must be empty")
        elif document["terminal_state"] != arm:
            raise ValueError("preauthorization terminal arm differs")
    elif artifact_id == "postauthorization-outcome":
        arm = document["outcome_arm"]
        if arm not in ("STARTED", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"):
            raise ValueError("postauthorization outcome arm differs")
        _require_sha256(
            document["launch_authorization_sha256"],
            "launch authorization",
            nonzero=True,
        )
        if (arm == "STARTED" and document["terminal_state"] != "") or (
            arm != "STARTED" and document["terminal_state"] != arm
        ):
            raise ValueError("postauthorization terminal state differs")
    elif artifact_id == "terminal-state":
        _validate_terminal_union(document)
    elif artifact_id == "preterminal-durable-artifact-inventory":
        _validate_preterminal_inventory_intrinsic(document)
    elif artifact_id == "sha256-manifest":
        _validate_sha256_manifest_intrinsic(document)
    elif artifact_id == "auxiliary-metadata-reservation":
        expected_slots = _auxiliary_expected_slots()
        rows = document["artifact_entries"]
        if document["artifact_entry_count"] != 183 or len(rows) != 183:
            raise ValueError("auxiliary reservation entry count differs")
        existing_bytes = 0
        future_bytes = 0
        identities = set()
        extent_maps = set()
        for ordinal, (row, expected) in enumerate(zip(rows, expected_slots), 1):
            (
                artifact,
                final_path,
                alternate_final_path,
                logical_cap,
                reserved_cap,
                primary_arm,
                alternate_arm,
            ) = expected
            if (
                row["ordinal"] != ordinal
                or row["artifact_id"] != artifact
                or row["final_relative_path"] != final_path
                or row["alternate_final_relative_path"] != alternate_final_path
                or row["primary_publication_arm_id"] != primary_arm
                or row["alternate_publication_arm_id"] != alternate_arm
                or row["maximum_logical_bytes"] != logical_cap
                or not 0 <= row["reserved_bytes"] <= reserved_cap
            ):
                raise ValueError("auxiliary reservation canonical row differs")
            state = row["reservation_state"]
            if artifact == "committed-marker":
                if (
                    state != "future-o-excl-covered-by-hold"
                    or row["partial_relative_path"] != ""
                    or row["device_identity_sha256"] != _ZERO_SHA256
                    or row["inode"] != 0
                    or row["extent_map_sha256"] != _ZERO_SHA256
                    or row["reserved_bytes"] != reserved_cap
                    or row["non_sparse_verified"] is not False
                    or row["exclusive_verified"] is not False
                    or row["file_fsync_completed_at_utc"] != ""
                    or row["directory_fsync_completed_at_utc"] != ""
                ):
                    raise ValueError("COMMITTED auxiliary row sentinel differs")
                continue
            is_live_journal = artifact == "auxiliary-reservation-transition-journal"
            if state not in (
                "existing-final-in-place",
                "preallocated-partial-in-place",
                "preallocated-live-journal-in-place",
            ):
                raise ValueError("auxiliary reservation row state differs")
            if is_live_journal:
                if state != "preallocated-live-journal-in-place":
                    raise ValueError("auxiliary transition journal row state differs")
                expected_partial = final_path
            else:
                if state == "preallocated-live-journal-in-place":
                    raise ValueError("live-journal state used by another artifact")
                expected_partial = (
                    ""
                    if state == "existing-final-in-place"
                    else final_path + ".partial"
                )
            if row["partial_relative_path"] != expected_partial:
                raise ValueError("auxiliary reservation row partial path differs")
            _require_sha256(
                row["device_identity_sha256"], "auxiliary row device", nonzero=True
            )
            _require_sha256(
                row["extent_map_sha256"], "auxiliary row extents", nonzero=True
            )
            if row["inode"] <= 0:
                raise ValueError("auxiliary reservation row inode differs")
            if (
                row["non_sparse_verified"] is not True
                or row["exclusive_verified"] is not True
            ):
                raise ValueError("auxiliary reservation row qualification differs")
            _require_utc(row["file_fsync_completed_at_utc"], "auxiliary row file fsync")
            _require_utc(
                row["directory_fsync_completed_at_utc"], "auxiliary row directory fsync"
            )
            identity = (row["device_identity_sha256"], row["inode"])
            if identity in identities or row["extent_map_sha256"] in extent_maps:
                raise ValueError("auxiliary reservation inode/extent alias differs")
            identities.add(identity)
            extent_maps.add(row["extent_map_sha256"])
            if state == "existing-final-in-place":
                existing_bytes += row["reserved_bytes"]
            else:
                if row["reserved_bytes"] != reserved_cap:
                    raise ValueError("future auxiliary partial is not fully reserved")
                future_bytes += row["reserved_bytes"]
        if document["allocated_existing_final_bytes"] != existing_bytes:
            raise ValueError("auxiliary existing-final total differs")
        if document["allocated_future_partial_bytes"] != future_bytes:
            raise ValueError("auxiliary future-partial total differs")
        unique_nonhold = existing_bytes + future_bytes
        if document["unique_nonhold_artifact_allocated_bytes"] != unique_nonhold:
            raise ValueError("auxiliary unique nonhold allocation differs")
        if document["artifact_slot_reserved_bytes"] != 22_213_099_520:
            raise ValueError("auxiliary static slot total differs")
        if document["hold_relative_path"] != ".cp65_auxiliary_reservation_hold.partial":
            raise ValueError("auxiliary reservation hold path differs")
        if not 11_140_005_888 <= document["hold_allocated_bytes"] <= 34_359_738_368:
            raise ValueError("auxiliary dynamic hold is outside its bound")
        _require_sha256(
            document["hold_device_identity_sha256"],
            "auxiliary hold device identity",
            nonzero=True,
        )
        _require_sha256(
            document["hold_extent_map_sha256"],
            "auxiliary hold extent map",
            nonzero=True,
        )
        if document["hold_inode"] <= 0:
            raise ValueError("auxiliary hold inode differs")
        if (
            not 0
            <= document["disjoint_allocation_and_directory_charge_bytes"]
            <= 1_073_741_824
        ):
            raise ValueError("observed allocation/directory charge exceeds policy")
        baseline = document["exclusive_root_charge_baseline_bytes"]
        current = document["exclusive_root_charge_current_bytes"]
        if baseline < 0 or current < baseline:
            raise ValueError("exclusive-root charge measurements differ")
        disjoint_charge = document["disjoint_allocation_and_directory_charge_bytes"]
        physical = unique_nonhold + disjoint_charge + document["hold_allocated_bytes"]
        if (
            document["physical_reservation_sum_bytes"] != physical
            or physical < 34_359_738_368
        ):
            raise ValueError("auxiliary physical reservation floor differs")
        if current - baseline != physical:
            raise ValueError("exclusive-root charge conservation differs")
        measurement_preimage = {
            "schema": "cp65-test28-exclusive-root-charge-measurement-v1",
            "attempt_id": document["attempt_id"],
            "measurement_session_sha256": document["measurement_session_sha256"],
            "storage_root_identity_sha256": document["storage_root_identity_sha256"],
            "filesystem_identity_sha256": document["filesystem_identity_sha256"],
            "exclusive_root_charge_baseline_bytes": baseline,
            "exclusive_root_charge_current_bytes": current,
            "unique_nonhold_artifact_allocated_bytes": unique_nonhold,
            "hold_allocated_bytes": document["hold_allocated_bytes"],
            "disjoint_allocation_and_directory_charge_bytes": disjoint_charge,
        }
        expected_measurement_sha256 = hashlib.sha256(
            b"cp65-test28-exclusive-root-charge-measurement-v1\0"
            + _plain_json_bytes(measurement_preimage)
        ).hexdigest()
        if (
            document["exclusive_root_charge_measurement_sha256"]
            != expected_measurement_sha256
        ):
            raise ValueError("exclusive-root charge measurement digest differs")
        if document["enforced_quota_bytes"] < 34_359_738_368:
            raise ValueError("auxiliary quota reservation floor differs")
        if (
            document["allocation_unit_bytes"] <= 0
            or (
                document["allocation_unit_bytes"]
                & (document["allocation_unit_bytes"] - 1)
            )
            or document["allocation_unit_bytes"] > 1_073_741_824
            or (34_359_738_368 % document["allocation_unit_bytes"])
        ):
            raise ValueError("auxiliary allocation unit differs")
        required_hold = max(
            0,
            34_359_738_368 - unique_nonhold - disjoint_charge,
        )
        allocation_unit = document["allocation_unit_bytes"]
        expected_hold = (
            (required_hold + allocation_unit - 1) // allocation_unit
        ) * allocation_unit
        if document["hold_allocated_bytes"] != expected_hold:
            raise ValueError("auxiliary dynamic hold complement differs")
        hold_identity = (
            document["hold_device_identity_sha256"],
            document["hold_inode"],
        )
        if (
            hold_identity in identities
            or document["hold_extent_map_sha256"] in extent_maps
        ):
            raise ValueError("auxiliary hold aliases an artifact reservation")
        for key in (
            "exclusive_verified",
            "non_sparse_verified",
            "durable_verified",
            "same_root_verified",
        ):
            if document[key] is not True:
                raise ValueError("auxiliary reservation qualification differs: " + key)
    elif artifact_id == "independent-reviewer-public-key-set":
        if (
            document["key_count"] != 4
            or tuple(document["required_reviewer_roles"]) != _REQUIRED_REVIEWER_ROLES
        ):
            raise ValueError("reviewer key set role count differs")
        roles = tuple(row["reviewer_role"] for row in document["ordered_keys"])
        if roles != _REQUIRED_REVIEWER_ROLES:
            raise ValueError("reviewer key order differs")
        identities = []
        reviewer_identities = set()
        for row in document["ordered_keys"]:
            identity = _reviewer_key_identity(row)
            if row["public_key_identity_sha256"] != identity:
                raise ValueError("reviewer public-key identity differs")
            if row["reviewer_identity_sha256"] in reviewer_identities:
                raise ValueError("reviewer identities must be unique")
            reviewer_identities.add(row["reviewer_identity_sha256"])
            if not row["valid_from_utc"] < row["valid_until_utc"]:
                raise ValueError("reviewer key validity interval differs")
            identities.append(identity)
        if tuple(document["ordered_public_key_identity_sha256s"]) != tuple(identities):
            raise ValueError("reviewer key identity vector differs")
    elif artifact_id == "independent-signoff-set":
        if (
            document["signoff_count"] != 4
            or tuple(document["required_reviewer_roles"]) != _REQUIRED_REVIEWER_ROLES
        ):
            raise ValueError("independent signoff count differs")
    elif artifact_id == "power-review-signoff":
        if (
            document["reviewer_role"] != "statistical-power-and-decision-reviewer"
            or document["decision"] != "APPROVE"
        ):
            raise ValueError("power reviewer role/decision differs")
    elif artifact_id == "committed-marker":
        if document["hold_relative_path"] != ".cp65_auxiliary_reservation_hold.partial":
            raise ValueError("COMMITTED hold path differs")
        if document["hold_absence_verified"] is not True:
            raise ValueError("COMMITTED must attest hold absence")
        removed = document["hold_removed_at_utc"]
        directory_fsynced = document["hold_removal_directory_fsync_completed_at_utc"]
        committed = document["committed_at_utc"]
        if not removed < directory_fsynced < committed:
            raise ValueError("COMMITTED hold-removal publication order differs")


def _validate_terminal_union(document: dict) -> None:
    arm = document["terminal_arm"]
    state = document["terminal_state"]
    zero_fields = ()
    nonzero_fields = ("freeze_receipt_sha256", "durable_artifact_inventory_sha256")
    if arm == "PREAUTHORIZATION":
        if document["previous_lifecycle_state"] != "FROZEN" or state not in (
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("PREAUTHORIZATION terminal discriminator differs")
        nonzero_fields += ("preauthorization_outcome_sha256",)
        zero_fields = (
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
            "started_receipt_sha256",
        )
    elif arm == "POSTAUTHORIZATION_PRESTART":
        if document["previous_lifecycle_state"] != "FROZEN" or state not in (
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("POSTAUTHORIZATION_PRESTART discriminator differs")
        nonzero_fields += (
            "preauthorization_outcome_sha256",
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
        )
        zero_fields = ("started_receipt_sha256",)
    elif arm == "STARTED":
        if document["previous_lifecycle_state"] != "STARTED" or state not in (
            "PASS",
            "FAIL",
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("STARTED terminal discriminator differs")
        nonzero_fields += (
            "preauthorization_outcome_sha256",
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
            "started_receipt_sha256",
        )
    else:
        raise ValueError("terminal arm differs")
    for key in nonzero_fields:
        _require_sha256(document[key], key, nonzero=True)
    for key in zero_fields:
        if document[key] != _ZERO_SHA256:
            raise ValueError(key + " must use the zero digest sentinel")
    reasons = {
        "PASS": "completed-as-preregistered",
        "FAIL": "primary-or-structural-failure",
        "INVALID_PROTOCOL": "frozen-input-or-protocol-invalid",
        "ABORTED_INFRA": "infrastructure-abort",
        "INCOMPLETE": "attempt-incomplete",
    }
    if document["reason_code"] != reasons[state]:
        raise ValueError("terminal reason code differs")


def _validate_preterminal_inventory_intrinsic(document: dict) -> None:
    entries = document["entries"]
    if (
        document["entry_count"] != len(entries)
        or not 1 <= len(entries) <= _MAX_TERMINAL_PUBLICATION_ENTRIES
    ):
        raise ValueError("preterminal inventory entry count differs")
    ordinals = [row["ordinal"] for row in entries]
    paths = [row["path"] for row in entries]
    if ordinals != list(range(1, len(entries) + 1)):
        raise ValueError("preterminal inventory ordinals differ")
    if paths != sorted(set(paths)):
        raise ValueError("preterminal inventory paths are not sorted and unique")
    forbidden = {
        "preterminal_durable_artifact_inventory.json",
        "terminal_state.json",
        "sha256_manifest.json",
        "COMMITTED.json",
        "auxiliary_reservation_transition_journal.bin",
    }
    for row in entries:
        _require_relative_path(row["path"], "preterminal inventory path")
        if row["path"] in forbidden:
            raise ValueError("preterminal inventory contains a forbidden artifact")
        zeroed = dict(row)
        zeroed["entry_sha256"] = _ZERO_SHA256
        expected = hashlib.sha256(
            b"cp65-test28-preterminal-durable-artifact-inventory-entry-v1\0"
            + _plain_json_bytes(zeroed)
        ).hexdigest()
        if row["entry_sha256"] != expected:
            raise ValueError("preterminal inventory entry digest differs")
    ordered = hashlib.sha256(
        b"cp65-test28-preterminal-durable-artifact-inventory-ordered-entries-v1\0"
        + b"".join(bytes.fromhex(row["entry_sha256"]) for row in entries)
    ).hexdigest()
    if document["ordered_entries_sha256"] != ordered:
        raise ValueError("preterminal inventory ordered digest differs")


def _validate_sha256_manifest_intrinsic(document: dict) -> None:
    entries = document["entries"]
    if (
        document["entry_count"] != len(entries)
        or not 1 <= len(entries) <= _MAX_TERMINAL_PUBLICATION_ENTRIES
    ):
        raise ValueError("SHA256 manifest entry count differs")
    paths = [row["path"] for row in entries]
    if paths != sorted(set(paths)):
        raise ValueError("SHA256 manifest paths are not sorted and unique")
    forbidden = {
        "sha256_manifest.json",
        "COMMITTED.json",
        "auxiliary_reservation_transition_journal.bin",
    }
    for row in entries:
        _require_relative_path(row["path"], "SHA256 manifest path")
        if row["path"] in forbidden:
            raise ValueError("SHA256 manifest contains a forbidden artifact")
    ordered = hashlib.sha256(
        b"cp65-test28-sha256-manifest-ordered-entries-v1\0" + _plain_json_bytes(entries)
    ).hexdigest()
    if document["ordered_entries_sha256"] != ordered:
        raise ValueError("SHA256 manifest ordered digest differs")


def _intrinsic_digest_instance_counts(
    artifact_id: str, document: object
) -> Tuple[int, int]:
    """Return exact locally validated and absent-source digest work counts."""

    if artifact_id == "preflight-gate-summary":
        if type(document) is not dict:
            raise ValueError("preflight gate summary document differs")
        return 1, len(document["ordered_evidence_receipt_sha256s"]) + 2
    if artifact_id == "production-schedule":
        if type(document) is not dict or type(document.get("requests")) is not list:
            raise ValueError("production schedule document differs")
        request_count = len(document["requests"])
        # Three independently replayable request formulas, followed by the
        # ordered aggregate, body digest, and retained raw-file digest.
        return 3 * request_count + 3, 2 * request_count + 3
    if artifact_id == "power-threshold-receipt":
        if (
            type(document) is not dict
            or type(document.get("ordered_slot_thresholds")) is not list
        ):
            raise ValueError("power threshold receipt document differs")
        row_count = len(document["ordered_slot_thresholds"])
        # Row digests plus ordered aggregate, body, and retained raw digest are
        # intrinsic.  Text/justification custody and three outer references
        # remain externally sourced.
        return row_count + 3, row_count + 5
    if artifact_id == "capacity-receipt":
        return 1, 8
    if artifact_id == "external-digest-preimage-registry":
        if type(document) is not dict or type(document.get("entries")) is not list:
            raise ValueError("external digest registry document differs")
        entry_count = len(document["entries"])
        # Each row owns its decoded-preimage digest and row digest; the ordered
        # aggregate and body are also intrinsic.  Target raw bytes plus the
        # protocol/manifest/schema references are supplied-source obligations.
        return 2 * entry_count + 2, entry_count + 3
    if artifact_id == "preterminal-durable-artifact-inventory":
        if type(document) is not dict:
            raise ValueError("preterminal inventory document differs")
        count = len(document["entries"])
        return count + 2, count + 1
    if artifact_id == "terminal-state":
        return 1, 4
    if artifact_id == "sha256-manifest":
        if type(document) is not dict:
            raise ValueError("SHA256 manifest document differs")
        return 2, len(document["entries"]) + 2
    return 1, 1


def _validate_source_materialization(
    payload: bytes,
) -> Tuple[Tuple[str, int, int, str], ...]:
    if len(payload) < 44 or len(payload) > 134_217_728 or payload[:8] != b"CP65SRC1":
        raise ValueError("source materialization framing differs")
    expected_archive = hashlib.sha256(
        b"cp65-test28-frozen-source-fixture-materialization-v1\0" + payload[:-32]
    ).digest()
    if not hmac.compare_digest(payload[-32:], expected_archive):
        raise ValueError("source materialization archive digest differs")
    view = memoryview(payload)
    limit = len(payload) - 32
    offset = 8
    if offset + 4 > limit:
        raise ValueError("source materialization header is truncated")
    count = int.from_bytes(view[offset : offset + 4], "big")
    offset += 4
    if not 1 <= count <= 4_096:
        raise ValueError("source materialization entry count differs")
    result = []
    aggregate = 12
    previous_path = ""
    for _ordinal in range(1, count + 1):
        if offset + 4 > limit:
            raise ValueError("source materialization path length is truncated")
        path_length = int.from_bytes(view[offset : offset + 4], "big")
        offset += 4
        if not 1 <= path_length <= 4_096 or offset + path_length + 40 > limit:
            raise ValueError("source materialization path frame differs")
        try:
            path = bytes(view[offset : offset + path_length]).decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("source materialization path is not ASCII") from exc
        offset += path_length
        _require_relative_path(path, "source materialization path")
        if path <= previous_path or path in (
            "frozen_inputs/bound_files.json",
            "freeze_receipt.json",
            "frozen_inputs/source_fixture_materialization.bin",
        ):
            raise ValueError("source materialization path order/exclusion differs")
        previous_path = path
        content_length = int.from_bytes(view[offset : offset + 8], "big")
        offset += 8
        if content_length > 16_777_216 or offset + 32 + content_length > limit:
            raise ValueError("source materialization content length differs")
        content_sha = bytes(view[offset : offset + 32])
        offset += 32
        content = view[offset : offset + content_length]
        offset += content_length
        if not hmac.compare_digest(hashlib.sha256(content).digest(), content_sha):
            raise ValueError("source materialization content SHA differs")
        content_bytes = bytes(content)
        line_count = (
            0
            if not content_bytes
            else content_bytes.count(b"\n") + int(not content_bytes.endswith(b"\n"))
        )
        aggregate += 44 + path_length + content_length
        if aggregate > 134_217_728:
            raise ValueError("source materialization aggregate exceeds bound")
        result.append((path, content_length, line_count, content_sha.hex()))
    if offset != limit:
        raise ValueError("source materialization contains trailing bytes")
    return tuple(result)


def _validate_journal_bytes(payload: bytes) -> None:
    if len(payload) != 163_840:
        raise ValueError("acquisition journal must be the full preallocated file")


def _auxiliary_transition_journal_prefix(
    payload: bytes,
    *,
    expected_auxiliary_reservation_raw_sha256: str = "",
    expected_schema_semantic_sha256: str = "",
) -> Tuple[int, str, Tuple[Tuple[int, ...], ...]]:
    if type(payload) is not bytes or len(payload) != 65_536:
        raise ValueError("auxiliary transition journal must be exactly 65536 bytes")
    header = payload[:256]
    if header[:8] != b"CP65AUX1" or int.from_bytes(header[8:16], "big") != 1:
        raise ValueError("auxiliary transition journal header differs")
    auxiliary_raw = header[16:48]
    semantic_raw = header[48:80]
    supplied_head0 = header[80:112]
    if (
        int.from_bytes(header[112:120], "big") != 255
        or int.from_bytes(header[120:128], "big") != 256
        or header[128:] != b"\0" * 128
    ):
        raise ValueError("auxiliary transition journal header framing differs")
    expected_head0 = hashlib.sha256(
        b"cp65-test28-auxiliary-reservation-transition-head-v1\0"
        + auxiliary_raw
        + semantic_raw
    ).digest()
    if not hmac.compare_digest(supplied_head0, expected_head0):
        raise ValueError("auxiliary transition journal initial head differs")
    if expected_auxiliary_reservation_raw_sha256:
        _require_sha256(
            expected_auxiliary_reservation_raw_sha256,
            "auxiliary reservation raw digest",
            nonzero=True,
        )
        if auxiliary_raw.hex() != expected_auxiliary_reservation_raw_sha256:
            raise ValueError("auxiliary transition journal reservation digest differs")
    if expected_schema_semantic_sha256:
        _require_sha256(
            expected_schema_semantic_sha256,
            "schema semantic digest",
            nonzero=True,
        )
        if semantic_raw.hex() != expected_schema_semantic_sha256:
            raise ValueError("auxiliary transition journal schema digest differs")
    head = supplied_head0
    parsed = []
    seen_code1_slots = set()
    checkpoint_codes = []
    checkpoint_slots = {
        3: next(
            index
            for index, row in enumerate(_auxiliary_expected_slots(), 1)
            if row[0] == "preterminal-durable-artifact-inventory"
        ),
        4: next(
            index
            for index, row in enumerate(_auxiliary_expected_slots(), 1)
            if row[0] == "terminal-state"
        ),
        5: next(
            index
            for index, row in enumerate(_auxiliary_expected_slots(), 1)
            if row[0] == "sha256-manifest"
        ),
    }
    zero_slot = b"\0" * 256
    ended = False
    for index in range(255):
        slot = payload[256 + index * 256 : 512 + index * 256]
        if slot == zero_slot:
            ended = True
            continue
        if ended or slot[184:] != b"\0" * 72:
            raise ValueError("auxiliary transition journal suffix is torn")
        ordinal = int.from_bytes(slot[0:8], "big")
        artifact_slot = int.from_bytes(slot[8:16], "big")
        transition_code = int.from_bytes(slot[16:24], "big")
        allocated_before = int.from_bytes(slot[24:32], "big")
        allocated_after = int.from_bytes(slot[32:40], "big")
        hold_before = int.from_bytes(slot[40:48], "big")
        hold_after = int.from_bytes(slot[48:56], "big")
        target_path_sha256 = slot[56:88]
        target_raw_sha256 = slot[88:120]
        previous_head = slot[120:152]
        entry_sha256 = slot[152:184]
        if ordinal != index + 1 or transition_code not in range(1, 7):
            raise ValueError("auxiliary transition journal ordinal/code differs")
        if not (
            1 <= artifact_slot <= 183 or (transition_code == 6 and artifact_slot == 0)
        ):
            raise ValueError("auxiliary transition journal artifact slot differs")
        if (
            allocated_before + hold_before != 34_359_738_368
            or allocated_after + hold_after != 34_359_738_368
        ):
            raise ValueError("auxiliary transition journal hold complement differs")
        if parsed and (
            allocated_before != parsed[-1][4] or hold_before != parsed[-1][6]
        ):
            raise ValueError("auxiliary transition journal totals are discontinuous")
        zero_digest = b"\0" * 32
        if transition_code == 6:
            if (
                artifact_slot != 0
                or target_path_sha256 != zero_digest
                or target_raw_sha256 != zero_digest
                or allocated_before != allocated_after
                or hold_before != hold_after
            ):
                raise ValueError("auxiliary transition journal final seal differs")
        elif target_path_sha256 == zero_digest or target_raw_sha256 == zero_digest:
            raise ValueError("auxiliary transition journal target digest is zero")
        if transition_code in (1, 2) and checkpoint_codes:
            raise ValueError("auxiliary transition follows a terminal checkpoint")
        if transition_code == 1:
            if artifact_slot in seen_code1_slots:
                raise ValueError("auxiliary transition artifact slot repeats")
            seen_code1_slots.add(artifact_slot)
        elif transition_code == 2:
            if allocated_after != allocated_before or hold_after != hold_before:
                raise ValueError("auxiliary recovery recheck changes accounting")
        elif transition_code in (3, 4, 5):
            if artifact_slot != checkpoint_slots[transition_code]:
                raise ValueError("auxiliary checkpoint artifact slot differs")
            checkpoint_codes.append(transition_code)
            if checkpoint_codes != list(range(3, 3 + len(checkpoint_codes))):
                raise ValueError("auxiliary checkpoint code order differs")
        elif transition_code == 6 and checkpoint_codes != [3, 4, 5]:
            raise ValueError("auxiliary final seal precedes required checkpoints")
        if not hmac.compare_digest(previous_head, head):
            raise ValueError("auxiliary transition journal previous head differs")
        expected_entry = hashlib.sha256(
            b"cp65-test28-auxiliary-reservation-transition-entry-v1\0"
            + auxiliary_raw
            + slot[:152]
        ).digest()
        if not hmac.compare_digest(entry_sha256, expected_entry):
            raise ValueError("auxiliary transition journal entry digest differs")
        parsed.append(
            (
                ordinal,
                artifact_slot,
                transition_code,
                allocated_before,
                allocated_after,
                hold_before,
                hold_after,
                target_path_sha256.hex(),
                target_raw_sha256.hex(),
            )
        )
        head = entry_sha256
    if (
        parsed
        and parsed[-1][2] == 6
        and tuple(row[2] for row in parsed[-4:])
        != (
            3,
            4,
            5,
            6,
        )
    ):
        raise ValueError("auxiliary sealed journal suffix differs")
    return len(parsed), head.hex(), tuple(parsed)


def _validate_auxiliary_transition_journal_against_reservation(
    reservation_document: dict,
    reservation_raw_bytes: bytes,
    journal_bytes: bytes,
    schema_semantic_sha256: str,
    supplied_by_path: Mapping[str, bytes],
) -> Tuple[int, int]:
    """Validate journal slot state transitions against the frozen aux snapshot."""

    count, _head, parsed = _auxiliary_transition_journal_prefix(
        journal_bytes,
        expected_auxiliary_reservation_raw_sha256=hashlib.sha256(
            reservation_raw_bytes
        ).hexdigest(),
        expected_schema_semantic_sha256=schema_semantic_sha256,
    )
    rows = reservation_document.get("artifact_entries")
    if type(rows) is not list or len(rows) != 183:
        raise ValueError("auxiliary transition journal reservation rows differ")
    rows_by_ordinal = {
        row["ordinal"]: row
        for row in rows
        if type(row) is dict and type(row.get("ordinal")) is int
    }
    if set(rows_by_ordinal) != set(range(1, 184)):
        raise ValueError("auxiliary transition journal reservation slots differ")
    expected_allocated = (
        reservation_document["unique_nonhold_artifact_allocated_bytes"]
        + reservation_document["disjoint_allocation_and_directory_charge_bytes"]
    )
    expected_hold = reservation_document["hold_allocated_bytes"]
    if parsed and (parsed[0][3], parsed[0][5]) != (
        expected_allocated,
        expected_hold,
    ):
        raise ValueError("auxiliary transition journal initial totals differ")

    transitioned_slots = set()
    validated = 2  # Header binds the reservation raw SHA and schema semantic SHA.
    unresolved = 0
    for entry in parsed:
        artifact_slot = entry[1]
        code = entry[2]
        if code == 6:
            continue
        row = rows_by_ordinal[artifact_slot]
        initial_state = row["reservation_state"]
        if code == 1:
            if (
                initial_state != "preallocated-partial-in-place"
                or row["artifact_id"]
                in ("auxiliary-reservation-transition-journal", "committed-marker")
                or artifact_slot in transitioned_slots
            ):
                raise ValueError("auxiliary code1 initial slot state differs")
            transitioned_slots.add(artifact_slot)
        elif code == 2:
            if not (
                initial_state == "existing-final-in-place"
                or artifact_slot in transitioned_slots
            ):
                raise ValueError("auxiliary code2 target is not an existing final")

        primary_path = row["final_relative_path"]
        alternate_path = row["alternate_final_relative_path"]
        path_digest = entry[7]
        selected_path = ""
        for candidate in (primary_path, alternate_path):
            if (
                candidate
                and hashlib.sha256(candidate.encode("ascii")).hexdigest() == path_digest
            ):
                selected_path = candidate
                break
        if not selected_path:
            raise ValueError("auxiliary transition target path differs")
        if selected_path not in supplied_by_path:
            unresolved += 1
        else:
            if hashlib.sha256(supplied_by_path[selected_path]).hexdigest() != entry[8]:
                raise ValueError("auxiliary transition target raw bytes differ")
            validated += 1

    return validated + count, unresolved


def _journal_prefix(
    payload: bytes, acquisition_start_body_sha256: str
) -> Tuple[int, str, Tuple[str, ...]]:
    """Recover only the longest valid CP64 fsynced-entry-shaped prefix."""

    _validate_journal_bytes(payload)
    _require_sha256(
        acquisition_start_body_sha256,
        "acquisition start receipt body digest",
        nonzero=True,
    )
    start_digest = bytes.fromhex(acquisition_start_body_sha256)
    head = hashlib.sha256(
        b"cp64-external-seed-acquisition-journal-head-v1\0" + start_digest
    ).digest()
    values = []
    zero_slot = b"\0" * 80
    for index in range(2_048):
        slot = payload[index * 80 : (index + 1) * 80]
        if slot == zero_slot:
            break
        ordinal_bytes = slot[:8]
        value_bytes = slot[8:16]
        previous = slot[16:48]
        supplied_entry = slot[48:80]
        ordinal = int.from_bytes(ordinal_bytes, "big")
        expected_entry = hashlib.sha256(
            b"cp64-external-seed-acquisition-journal-entry-v1\0"
            + start_digest
            + ordinal_bytes
            + value_bytes
            + previous
        ).digest()
        if (
            ordinal != index + 1
            or not hmac.compare_digest(previous, head)
            or not hmac.compare_digest(supplied_entry, expected_entry)
        ):
            break
        values.append(value_bytes.hex())
        head = supplied_entry
    return len(values), head.hex(), tuple(values)


def _ordered_seed_values_commitment(values: Tuple[str, ...]) -> str:
    return hashlib.sha256(
        b"cp64-test28-ordered-seed-sequence-v1\0"
        + _plain_json_bytes(
            {
                "seed_count": len(values),
                "seed_encoding": "uint64-16-lowercase-hex-big-endian",
                "ordered_seed_values": list(values),
            }
        )
    ).hexdigest()


def _validate_artifact_payload(
    artifact_id: str,
    relative_path: str,
    payload: bytes,
) -> Tuple[str, object]:
    if artifact_id not in _ARTIFACT_BY_ID:
        raise ValueError("unknown CP65 artifact id")
    _require_relative_path(relative_path, "relative_path")
    if not _relative_path_matches(artifact_id, relative_path):
        raise ValueError("relative_path does not expand the artifact template")
    declaration = _ARTIFACT_BY_ID[artifact_id]
    maximum = _artifact_maximum_bytes(artifact_id)
    if len(payload) > maximum:
        raise ValueError("artifact payload exceeds its schema-specific byte cap")
    if artifact_id in _REFERENCED_OUTPUT_IDS:
        raise ValueError(
            "referenced execution/output containers are not semantic validator inputs"
        )
    if artifact_id == "frozen-protocol-sha256":
        expected = _FROZEN_PROTOCOL_SHA256.encode("ascii") + b"\n"
        if payload != expected:
            raise ValueError("frozen protocol SHA sidecar framing differs")
        try:
            value = payload[:-1].decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("frozen protocol SHA sidecar is not ASCII") from exc
        _require_sha256(value, "frozen protocol SHA")
        return hashlib.sha256(payload).hexdigest(), value
    if artifact_id == "frozen-protocol":
        if (
            len(payload) != _FROZEN_PROTOCOL_BYTES
            or hashlib.sha256(payload).hexdigest() != _FROZEN_PROTOCOL_SHA256
        ):
            raise ValueError("frozen protocol immutable bytes differ")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "dependency-lock":
        if (
            len(payload) != _FROZEN_DEPENDENCY_LOCK_BYTES
            or hashlib.sha256(payload).hexdigest() != _FROZEN_DEPENDENCY_LOCK_SHA256
        ):
            raise ValueError("frozen dependency-lock immutable bytes differ")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "external-seed-acquisition-journal":
        _validate_journal_bytes(payload)
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "auxiliary-reservation-transition-journal":
        parsed = _auxiliary_transition_journal_prefix(payload)
        return hashlib.sha256(payload).hexdigest(), parsed
    if artifact_id == "frozen-source-fixture-materialization":
        rows = _validate_source_materialization(payload)
        return hashlib.sha256(payload).hexdigest(), rows
    if artifact_id == "production-schema-preimage-validator-bundle":
        expected = cp65_canonical_json_bytes(
            cp65_production_schema_preimage_validator_bundle()
        )
        if payload != expected:
            raise ValueError("retained CP65 schema bundle bytes differ")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "frozen-machine-manifest":
        if (
            len(payload) != _FROZEN_MACHINE_MANIFEST_BYTES
            or hashlib.sha256(payload).hexdigest() != _FROZEN_MACHINE_MANIFEST_SHA256
        ):
            raise ValueError("frozen machine-manifest immutable bytes differ")
        document = _parse_pinned_predecessor_manifest(payload)
        return hashlib.sha256(payload).hexdigest(), document
    if not declaration[4]:
        raise ValueError("artifact has no CP65 semantic bytes validator")
    document = _parse_canonical_json_object(payload, maximum)
    exact_keys = declaration[4]
    if set(document) != set(exact_keys) or len(document) != len(exact_keys):
        raise ValueError("artifact exact top-level key set differs")
    nested = declaration[5]
    nested_by_key = dict(nested)
    for key in exact_keys:
        if key in nested_by_key:
            continue
        if _explicit_field_kind(key) == "array":
            _validate_primitive_array(artifact_id, key, document[key])
        else:
            _validate_scalar_field(artifact_id, "/" + key, key, document[key])
    _validate_nested_rows(artifact_id, document, nested)
    body_sha256 = _validate_body_digest(artifact_id, document)
    _validate_receipt_specific(artifact_id, document)
    return body_sha256, document


def _supplied_validation(
    artifact_ids: Tuple[str, ...],
    relative_paths: Tuple[str, ...],
    payloads: Tuple[bytes, ...],
    body_sha256s: Tuple[str, ...],
    *,
    signature_applicable: bool = False,
    signature_valid: bool = False,
    validated_digest_preimage_count: int = 1,
    unresolved_digest_preimage_count: int = 1,
    validated_cross_binding_count: int = 0,
    unresolved_cross_binding_count: int = 0,
) -> CP65SuppliedValidationV1:
    return cast(
        CP65SuppliedValidationV1,
        _record(
            CP65SuppliedValidationV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "validation_scope": "caller-supplied-development-bytes-only",
                "caller_supplied_bytes_only": True,
                "input_artifact_ids": artifact_ids,
                "input_relative_paths": relative_paths,
                "input_sha256s": tuple(
                    hashlib.sha256(item).hexdigest() for item in payloads
                ),
                "input_byte_lengths": tuple(len(item) for item in payloads),
                "validated_artifact_ids": artifact_ids,
                "validated_relative_paths": relative_paths,
                "validated_body_sha256s": body_sha256s,
                "syntax_valid": True,
                "intrinsic_digest_preimages_valid": True,
                "all_required_digest_preimage_sources_supplied": (
                    unresolved_digest_preimage_count == 0
                ),
                "validated_digest_preimage_count": validated_digest_preimage_count,
                "unresolved_digest_preimage_count": unresolved_digest_preimage_count,
                "digest_preimages_valid": unresolved_digest_preimage_count == 0,
                "all_required_cross_binding_targets_supplied": (
                    unresolved_cross_binding_count == 0
                ),
                "validated_cross_binding_count": validated_cross_binding_count,
                "unresolved_cross_binding_count": unresolved_cross_binding_count,
                "cross_bindings_valid": unresolved_cross_binding_count == 0,
                "signature_verification_applicable": signature_applicable,
                "signature_mathematically_valid_under_supplied_key": signature_valid,
                "parser_input_resource_limits_satisfied": True,
                "external_production_receipts_observed": False,
                "external_provenance_verified": False,
                "filesystem_observed": False,
                "source_authority_verified": False,
                "authorization_trust_root_bound": False,
                "authority_verified": False,
                "production_evidence_accepted": False,
                "gate_transition_permitted": False,
                "launch_authorized": False,
                "execution_permitted": False,
                "definition_only": True,
            },
        ),
    )


def _resolve_closed_json_pointer(document: object, pointer: str) -> object:
    if type(pointer) is not str or not pointer.startswith("/") or "*" in pointer:
        raise ValueError("closed JSON pointer differs")
    current = document
    for encoded in pointer[1:].split("/"):
        key = encoded.replace("~1", "/").replace("~0", "~")
        if type(current) is not dict or key not in current:
            raise ValueError("closed JSON pointer does not resolve")
        current = current[key]
    return current


def _resolve_registry_target_pointer(
    document: object,
    pointer: str,
    wildcard_indices: Tuple[int, ...],
) -> object:
    """Resolve one catalogued target pointer under its exact row selector."""

    if type(pointer) is not str or not pointer.startswith("/"):
        raise ValueError("registry target pointer differs")
    current = document
    wildcard_ordinal = 0
    for encoded in pointer[1:].split("/"):
        part = encoded.replace("~1", "/").replace("~0", "~")
        if part == "*":
            if type(current) is not list or wildcard_ordinal >= len(wildcard_indices):
                raise ValueError("registry target pointer does not resolve")
            selected = wildcard_indices[wildcard_ordinal]
            wildcard_ordinal += 1
            if not 0 <= selected < len(current):
                raise ValueError("registry target pointer selector is out of range")
            current = current[selected]
        else:
            if type(current) is not dict or part not in current:
                raise ValueError("registry target pointer does not resolve")
            current = current[part]
    if wildcard_ordinal != len(wildcard_indices):
        raise ValueError("registry target pointer selector cardinality differs")
    return current


def _validate_registry_target_bindings(
    by_id: dict,
) -> Tuple[int, Tuple[Tuple[str, str], ...]]:
    """Bind every supplied registry row to exact retained target bytes/value."""

    if "external-digest-preimage-registry" not in by_id:
        return 0, ()
    registry_document = by_id["external-digest-preimage-registry"][0][3]
    if type(registry_document) is not dict:
        raise ValueError("external digest registry document differs")
    validated = 0
    resolved_targets = []
    for entry in registry_document["entries"]:
        selector = _parse_canonical_json_object(
            entry["target_instance_selector_json_ascii"].encode("ascii"),
            4_096,
        )
        wildcard_indices = tuple(selector["wildcard_indices"])
        candidates = tuple(
            row
            for row in by_id.get(entry["target_artifact_id"], ())
            if row[0] == entry["target_relative_path"]
        )
        if not candidates:
            continue
        if len(candidates) != 1:
            raise ValueError("registry target artifact instance is ambiguous")
        target_path, target_raw, _target_body, target_document = candidates[0]
        if (
            hashlib.sha256(target_raw).hexdigest()
            != entry["target_artifact_raw_sha256"]
        ):
            raise ValueError("registry target raw digest differs")
        try:
            selected_value = _resolve_registry_target_pointer(
                target_document,
                entry["target_json_pointer"],
                wildcard_indices,
            )
        except ValueError as exc:
            raise ValueError("registry target pointer does not resolve") from exc
        if selected_value != entry["digest_sha256"]:
            raise ValueError("registry target pointer digest differs")
        validated += 1
        resolved_targets.append((entry["target_artifact_id"], target_path))
    return validated, tuple(resolved_targets)


def _validate_independent_signoff_aggregation(
    by_id: dict,
) -> Tuple[bool, bool, int]:
    """Verify all four reviewer rows and their exact summary coverage."""

    if "independent-signoff-set" not in by_id:
        return False, False, 0
    if (
        "independent-reviewer-public-key-set" not in by_id
        or "preflight-gate-summary" not in by_id
    ):
        return False, False, 0
    document = by_id["independent-signoff-set"][0][3]
    key_set = by_id["independent-reviewer-public-key-set"][0][3]
    summary_raw = hashlib.sha256(by_id["preflight-gate-summary"][0][1]).hexdigest()
    key_set_raw = hashlib.sha256(
        by_id["independent-reviewer-public-key-set"][0][1]
    ).hexdigest()
    if (
        document["preflight_gate_summary_sha256"] != summary_raw
        or document["reviewer_public_key_set_sha256"] != key_set_raw
    ):
        raise ValueError("independent signoff outer raw binding differs")
    rows = document["ordered_signoffs"]
    keys = key_set["ordered_keys"]
    roles = tuple(row["reviewer_role"] for row in rows)
    if (
        len(rows) != 4
        or len(keys) != 4
        or roles != _REQUIRED_REVIEWER_ROLES
        or len(set(roles)) != 4
    ):
        raise ValueError("independent signoff reviewer role coverage differs")
    signatures_valid = []
    for row, key, expected_role in zip(rows, keys, _REQUIRED_REVIEWER_ROLES):
        if (
            key["reviewer_role"] != expected_role
            or row["reviewer_role"] != expected_role
            or row["reviewed_artifact_sha256s"] != [summary_raw]
            or row["decision"] != "APPROVE"
            or row["reviewer_identity_sha256"] != key["reviewer_identity_sha256"]
            or row["reviewer_public_key_identity_sha256"] != _reviewer_key_identity(key)
            or row["signature_scheme_id"] != key["signature_scheme_id"]
            or row["signature_scheme_id"] != "rsa-pss-sha256-3072-e65537-salt32-v1"
            or key["public_exponent"] != 65_537
        ):
            raise ValueError("independent signoff row/key binding differs")
        signed_at = _require_utc(row["signed_at_utc"], "signed_at_utc")
        valid_from = _require_utc(key["valid_from_utc"], "valid_from_utc")
        valid_until = _require_utc(key["valid_until_utc"], "valid_until_utc")
        signature = bytes.fromhex(row["reviewer_signature_hex"])
        unsigned = dict(row)
        unsigned["reviewer_signature_hex"] = ""
        unsigned["reviewer_signature_sha256"] = _ZERO_SHA256
        unsigned["signoff_sha256"] = _ZERO_SHA256
        valid = (
            valid_from <= signed_at < valid_until
            and row["reviewer_signature_sha256"]
            == hashlib.sha256(signature).hexdigest()
            and _verify_rsa_pss_sha256_3072(
                b"cp65-test28-independent-signoff-row-signature-preimage-v1\0"
                + _plain_json_bytes(unsigned),
                bytes.fromhex(key["modulus_hex"]),
                signature,
            )
        )
        signatures_valid.append(valid)
    derived = (
        roles == _REQUIRED_REVIEWER_ROLES,
        all(row["decision"] == "APPROVE" for row in rows),
        all(signatures_valid),
    )
    declared = (
        document["all_required_roles_present"],
        document["all_decisions_approve"],
        document["all_signatures_mathematically_valid_under_declared_keys"],
    )
    if derived != (True, True, True) or declared != derived:
        raise ValueError("independent signoff derived aggregate differs")
    return True, True, 12


def _validate_supplied_signature_aggregation(
    by_id: dict,
) -> Tuple[bool, bool, int, int]:
    """Aggregate every supplied signed family without asserting key trust."""

    applicable = False
    validities = []
    validated = 0
    unresolved = 0

    for signed_id in (
        "launch-authorization",
        "rejected-launch-authorization-candidate",
    ):
        if signed_id not in by_id:
            continue
        applicable = True
        if "launch-authority-public-key" not in by_id:
            unresolved += 1
            validities.append(False)
            continue
        validities.append(
            _verify_signed_document(
                by_id[signed_id][0][3],
                by_id["launch-authority-public-key"][0][3],
                scheme_field="authority_scheme_id",
                identity_field="authority_identity_sha256",
                signature_hex_field="authority_signature_hex",
                signature_sha_field="authority_signature_sha256",
                issued_field="authorization_issued_at_utc",
                expires_field="authorization_expires_at_utc",
                key_scheme_field="authority_scheme_id",
                key_identity_domain=(
                    b"cp65-test28-launch-authority-public-key-identity-v1\0"
                ),
                signing_domain=(
                    b"cp65-test28-launch-authorization-signature-preimage-v1\0"
                ),
            )
        )
        validated += 1

    if "seed-source-authority-attestation" in by_id:
        applicable = True
        if "seed-source-authority-public-key" not in by_id:
            unresolved += 1
            validities.append(False)
        else:
            validities.append(
                _verify_signed_document(
                    by_id["seed-source-authority-attestation"][0][3],
                    by_id["seed-source-authority-public-key"][0][3],
                    scheme_field="source_authority_scheme_id",
                    identity_field="source_authority_identity_sha256",
                    signature_hex_field="source_authority_signature_hex",
                    signature_sha_field="source_authority_signature_sha256",
                    issued_field="attested_at_utc",
                    expires_field="attestation_expires_at_utc",
                    key_scheme_field="source_authority_scheme_id",
                    key_identity_domain=(
                        b"cp65-test28-seed-source-authority-public-key-identity-v1\0"
                    ),
                    signing_domain=(
                        b"cp65-test28-seed-source-authority-attestation-signature-preimage-v1\0"
                    ),
                )
            )
            validated += 1

    if "power-review-signoff" in by_id:
        applicable = True
        if "independent-reviewer-public-key-set" not in by_id:
            unresolved += 1
            validities.append(False)
        else:
            document = by_id["power-review-signoff"][0][3]
            keys = tuple(
                key
                for key in by_id["independent-reviewer-public-key-set"][0][3][
                    "ordered_keys"
                ]
                if key["reviewer_role"] == "statistical-power-and-decision-reviewer"
            )
            if len(keys) != 1:
                raise ValueError("power reviewer role does not select one key")
            key = keys[0]
            signature = bytes.fromhex(document["reviewer_signature_hex"])
            unsigned = dict(document)
            unsigned["reviewer_signature_hex"] = ""
            unsigned["reviewer_signature_sha256"] = _ZERO_SHA256
            unsigned["body_sha256"] = _ZERO_SHA256
            validities.append(
                document["reviewer_role"] == key["reviewer_role"]
                and document["reviewer_identity_sha256"]
                == key["reviewer_identity_sha256"]
                and document["reviewer_public_key_identity_sha256"]
                == _reviewer_key_identity(key)
                and document["decision"] == "APPROVE"
                and document["signature_scheme_id"] == key["signature_scheme_id"]
                and document["signature_scheme_id"]
                == "rsa-pss-sha256-3072-e65537-salt32-v1"
                and key["public_exponent"] == 65_537
                and key["valid_from_utc"]
                <= document["signed_at_utc"]
                < key["valid_until_utc"]
                and document["reviewer_signature_sha256"]
                == hashlib.sha256(signature).hexdigest()
                and _verify_rsa_pss_sha256_3072(
                    b"cp65-test28-power-review-signoff-signature-preimage-v1\0"
                    + _plain_json_bytes(unsigned),
                    bytes.fromhex(key["modulus_hex"]),
                    signature,
                )
            )
            validated += 1

    if "independent-signoff-set" in by_id:
        applicable = True
        missing = tuple(
            artifact_id
            for artifact_id in (
                "independent-reviewer-public-key-set",
                "preflight-gate-summary",
            )
            if artifact_id not in by_id
        )
        if missing:
            unresolved += len(missing)
            validities.append(False)
        else:
            _applies, valid, binding_count = _validate_independent_signoff_aggregation(
                by_id
            )
            validities.append(valid)
            validated += binding_count

    return (
        applicable,
        bool(applicable and unresolved == 0 and all(validities)),
        validated,
        unresolved,
    )


def _validate_terminal_publication_cross_bindings(by_id: dict) -> Tuple[int, int]:
    """Validate the inventory -> terminal -> manifest retained-byte chain."""

    validated = 0
    unresolved = 0
    by_path = {row[0]: row for rows in by_id.values() for row in rows}

    def require_raw_entry(entry: dict) -> None:
        nonlocal validated, unresolved
        source = by_path.get(entry["path"])
        if source is None:
            unresolved += 1
            return
        raw_bytes = source[1]
        if (
            entry["bytes"] != len(raw_bytes)
            or entry["sha256"] != hashlib.sha256(raw_bytes).hexdigest()
        ):
            raise ValueError("terminal publication member raw bytes differ")
        validated += 1

    inventory = None
    if "preterminal-durable-artifact-inventory" in by_id:
        candidate_inventory = by_id["preterminal-durable-artifact-inventory"][0][3]
        inventory = (
            candidate_inventory
            if type(candidate_inventory) is dict and "entries" in candidate_inventory
            else None
        )
    if inventory is not None:
        for entry in inventory["entries"]:
            require_raw_entry(entry)
        excluded_paths = {
            "preterminal_durable_artifact_inventory.json",
            "terminal_state.json",
            "sha256_manifest.json",
            "COMMITTED.json",
            "auxiliary_reservation_transition_journal.bin",
        }
        eligible_supplied_paths = {
            path for path in by_path if path not in excluded_paths
        }
        inventoried_paths = {entry["path"] for entry in inventory["entries"]}
        if not eligible_supplied_paths.issubset(inventoried_paths):
            raise ValueError("preterminal inventory omits a supplied durable artifact")
        # The inventory records the pre-code3 transition-journal state.
        unresolved += 1

    terminal = None
    if "terminal-state" in by_id:
        terminal = by_id["terminal-state"][0][3]
        if "preterminal-durable-artifact-inventory" not in by_id:
            unresolved += 1
        else:
            expected = hashlib.sha256(
                by_id["preterminal-durable-artifact-inventory"][0][1]
            ).hexdigest()
            if terminal["durable_artifact_inventory_sha256"] != expected:
                raise ValueError(
                    "cross-artifact digest binding differs: "
                    "durable_artifact_inventory_sha256"
                )
            if (
                inventory is not None
                and inventory["terminal_arm"] != terminal["terminal_arm"]
            ):
                raise ValueError("inventory and terminal arms differ")
            validated += 1
        branch_sources = [
            ("freeze-receipt", "freeze_receipt_sha256"),
            ("preauthorization-outcome", "preauthorization_outcome_sha256"),
        ]
        if terminal["terminal_arm"] in (
            "POSTAUTHORIZATION_PRESTART",
            "STARTED",
        ):
            branch_sources.extend(
                (
                    ("launch-authorization", "launch_authorization_sha256"),
                    (
                        "postauthorization-outcome",
                        "postauthorization_outcome_sha256",
                    ),
                )
            )
        if terminal["terminal_arm"] == "STARTED":
            branch_sources.append(("started-receipt", "started_receipt_sha256"))
        for source_id, pointer in branch_sources:
            if source_id not in by_id:
                unresolved += 1
            else:
                expected = hashlib.sha256(by_id[source_id][0][1]).hexdigest()
                if terminal[pointer] != expected:
                    raise ValueError(
                        "cross-artifact digest binding differs: " + pointer
                    )
                validated += 1
        # The terminal records the post-code3 transition-journal state.
        if "auxiliary_transition_journal_after_inventory_head_sha256" in terminal:
            unresolved += 1

    if "sha256-manifest" in by_id:
        manifest = by_id["sha256-manifest"][0][3]
        if "terminal-state" not in by_id:
            unresolved += 1
        else:
            expected_terminal_raw = hashlib.sha256(
                by_id["terminal-state"][0][1]
            ).hexdigest()
            if manifest["terminal_state_sha256"] != expected_terminal_raw:
                raise ValueError("SHA256 manifest terminal raw binding differs")
            validated += 1
        for entry in manifest["entries"]:
            require_raw_entry(entry)
        # The manifest records the post-code4 transition-journal state.
        unresolved += 1
        if inventory is not None and terminal is not None:
            expected_entries = [
                {
                    "path": row["path"],
                    "bytes": row["bytes"],
                    "sha256": row["sha256"],
                }
                for row in inventory["entries"]
            ]
            inventory_payload = by_id["preterminal-durable-artifact-inventory"][0][1]
            terminal_payload = by_id["terminal-state"][0][1]
            expected_entries.extend(
                (
                    {
                        "path": "preterminal_durable_artifact_inventory.json",
                        "bytes": len(inventory_payload),
                        "sha256": hashlib.sha256(inventory_payload).hexdigest(),
                    },
                    {
                        "path": "terminal_state.json",
                        "bytes": len(terminal_payload),
                        "sha256": hashlib.sha256(terminal_payload).hexdigest(),
                    },
                )
            )
            expected_entries.sort(key=lambda row: row["path"])
            if manifest["entries"] != expected_entries:
                raise ValueError("SHA256 manifest branch membership differs")
            if not (
                inventory["created_at_utc"]
                < terminal["terminalized_at_utc"]
                < manifest["created_at_utc"]
            ):
                raise ValueError("terminal publication chronology differs")
    return validated, unresolved


def _validate_supplied_cross_bindings(by_id: dict) -> Tuple[int, int]:
    documents = []
    for rows in by_id.values():
        for _path, _payload, _body, document in rows:
            if type(document) is dict:
                documents.append(document)
    attempt_ids = {
        document["attempt_id"] for document in documents if "attempt_id" in document
    }
    if len(attempt_ids) > 1:
        raise ValueError("supplied artifacts cross different attempt ids")
    validated_count = 0
    unresolved_count = 0
    (
        terminal_validated,
        terminal_unresolved,
    ) = _validate_terminal_publication_cross_bindings(by_id)
    validated_count += terminal_validated
    unresolved_count += terminal_unresolved

    auxiliary_present = "auxiliary-metadata-reservation" in by_id
    transition_journal_present = "auxiliary-reservation-transition-journal" in by_id
    if auxiliary_present or transition_journal_present:
        if not (auxiliary_present and transition_journal_present):
            unresolved_count += 1
        else:
            supplied_by_path = {
                path: payload
                for rows in by_id.values()
                for path, payload, _body_digest, _document in rows
            }
            (
                journal_validated,
                journal_unresolved,
            ) = _validate_auxiliary_transition_journal_against_reservation(
                by_id["auxiliary-metadata-reservation"][0][3],
                by_id["auxiliary-metadata-reservation"][0][1],
                by_id["auxiliary-reservation-transition-journal"][0][1],
                cp65_production_schema_preimage_validator_bundle().schema_semantic_sha256,
                supplied_by_path,
            )
            validated_count += journal_validated
            unresolved_count += journal_unresolved

    if "committed-marker" in by_id:
        if "auxiliary-reservation-transition-journal" not in by_id:
            unresolved_count += 3
        else:
            committed_document = by_id["committed-marker"][0][3]
            journal_payload = by_id["auxiliary-reservation-transition-journal"][0][1]
            (
                final_count,
                final_head,
                final_entries,
            ) = _auxiliary_transition_journal_prefix(journal_payload)
            if (
                final_count < 4
                or not final_entries
                or tuple(row[2] for row in final_entries[-4:]) != (3, 4, 5, 6)
            ):
                raise ValueError("COMMITTED transition journal is not finally sealed")
            if (
                committed_document["auxiliary_reservation_transition_journal_sha256"]
                != hashlib.sha256(journal_payload).hexdigest()
            ):
                raise ValueError("COMMITTED transition journal raw digest differs")
            if (
                committed_document[
                    "auxiliary_reservation_transition_journal_final_head_sha256"
                ]
                != final_head
            ):
                raise ValueError("COMMITTED transition journal final head differs")
            if (
                committed_document[
                    "auxiliary_reservation_transition_journal_final_entry_count"
                ]
                != final_count
            ):
                raise ValueError("COMMITTED transition journal final count differs")
            journal_file_fsync = committed_document[
                "auxiliary_reservation_transition_journal_file_fsync_completed_at_utc"
            ]
            journal_directory_fsync = committed_document[
                "auxiliary_reservation_transition_journal_directory_fsync_completed_at_utc"
            ]
            if not (
                journal_file_fsync
                < journal_directory_fsync
                < committed_document["hold_removed_at_utc"]
                < committed_document["hold_removal_directory_fsync_completed_at_utc"]
                < committed_document["committed_at_utc"]
            ):
                raise ValueError("COMMITTED transition journal chronology differs")
            if (
                "preterminal-durable-artifact-inventory" in by_id
                and "terminal-state" in by_id
                and "sha256-manifest" in by_id
                and not (
                    by_id["preterminal-durable-artifact-inventory"][0][3][
                        "created_at_utc"
                    ]
                    < by_id["terminal-state"][0][3]["terminalized_at_utc"]
                    < by_id["sha256-manifest"][0][3]["created_at_utc"]
                    < journal_file_fsync
                )
            ):
                raise ValueError("COMMITTED terminal publication chronology differs")
            validated_count += 3

    def raw(artifact_id: str) -> str:
        return hashlib.sha256(by_id[artifact_id][0][1]).hexdigest()

    def body(artifact_id: str) -> str:
        return by_id[artifact_id][0][2]

    links = (
        (
            "external-seed-acquisition-start-receipt",
            "freeze-receipt",
            "freeze_receipt_sha256",
            "raw",
        ),
        ("freeze-receipt", "frozen-protocol", "protocol_sha256", "raw"),
        (
            "freeze-receipt",
            "frozen-machine-manifest",
            "machine_manifest_sha256",
            "raw",
        ),
        ("freeze-receipt", "source-manifest", "bound_files_sha256", "raw"),
        (
            "freeze-receipt",
            "dependency-lock",
            "dependency_lock_sha256",
            "raw",
        ),
        (
            "freeze-receipt",
            "frozen-source-fixture-materialization",
            "frozen_source_fixture_materialization_sha256",
            "raw",
        ),
        (
            "freeze-receipt",
            "production-schema-preimage-validator-bundle",
            "production_receipt_schema_bundle_sha256",
            "raw",
        ),
        (
            "freeze-receipt",
            "power-threshold-receipt",
            "power_threshold_receipt_sha256",
            "raw",
        ),
        (
            "freeze-receipt",
            "launch-authority-public-key",
            "launch_authority_public_key_sha256",
            "raw",
        ),
        (
            "freeze-receipt",
            "independent-reviewer-public-key-set",
            "independent_reviewer_public_key_set_sha256",
            "raw",
        ),
        (
            "freeze-receipt",
            "seed-source-authority-public-key",
            "seed_source_authority_public_key_sha256",
            "raw",
        ),
        (
            "external-seed-source-receipt",
            "external-seed-acquisition-start-receipt",
            "acquisition_start_receipt_sha256",
            "body",
        ),
        (
            "external-seed-source-receipt",
            "seed-source-authority-attestation",
            "source_authority_attestation_sha256",
            "raw",
        ),
        (
            "seed-capsule-body",
            "external-seed-source-receipt",
            "source_receipt_sha256",
            "raw",
        ),
        (
            "production-schedule",
            "seed-capsule-body",
            "seed_capsule_body_sha256",
            "body",
        ),
        ("capacity-receipt", "production-schedule", "schedule_sha256", "raw"),
        (
            "capacity-receipt",
            "auxiliary-metadata-reservation",
            "auxiliary_metadata_reservation_artifact_sha256",
            "raw",
        ),
        (
            "capacity-receipt",
            "reservation-manifest",
            "reservation_manifest_sha256",
            "raw",
        ),
        ("durability-receipt", "capacity-receipt", "capacity_receipt_sha256", "raw"),
        (
            "production-shard-map-receipt",
            "capacity-receipt",
            "capacity_receipt_sha256",
            "raw",
        ),
        (
            "production-shard-map-receipt",
            "durability-receipt",
            "durability_receipt_sha256",
            "raw",
        ),
        (
            "independent-signoff-set",
            "preflight-gate-summary",
            "preflight_gate_summary_sha256",
            "raw",
        ),
        (
            "independent-signoff-set",
            "independent-reviewer-public-key-set",
            "reviewer_public_key_set_sha256",
            "raw",
        ),
        (
            "preflight-gate-summary",
            "external-digest-preimage-registry",
            "external_digest_preimage_registry_sha256",
            "raw",
        ),
        (
            "preflight-gate-summary",
            "freeze-receipt",
            "freeze_receipt_sha256",
            "raw",
        ),
        ("launch-authorization", "frozen-protocol", "protocol_sha256", "raw"),
        (
            "launch-authorization",
            "frozen-machine-manifest",
            "machine_manifest_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "source-manifest",
            "source_manifest_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "dependency-lock",
            "dependency_lock_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "external-seed-source-receipt",
            "seed_source_receipt_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "seed-capsule-body",
            "seed_capsule_body_sha256",
            "body",
        ),
        (
            "launch-authorization",
            "production-schedule",
            "schedule_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "production-runtime-receipt",
            "production_runtime_receipt_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "capacity-receipt",
            "capacity_receipt_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "durability-receipt",
            "durability_receipt_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "production-shard-map-receipt",
            "production_shard_map_receipt_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "preflight-gate-summary",
            "preflight_gate_summary_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "power-threshold-receipt",
            "power_threshold_receipt_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "freeze-receipt",
            "freeze_receipt_sha256",
            "raw",
        ),
        (
            "launch-authorization",
            "independent-signoff-set",
            "independent_signoff_sha256",
            "raw",
        ),
        ("committed-marker", "terminal-state", "terminal_state_sha256", "raw"),
        ("committed-marker", "sha256-manifest", "sha256_manifest_sha256", "raw"),
        (
            "committed-marker",
            "auxiliary-metadata-reservation",
            "auxiliary_metadata_reservation_sha256",
            "raw",
        ),
    )
    for target_id, source_id, pointer, digest_kind in links:
        if target_id not in by_id:
            continue
        target = by_id[target_id][0][3]
        # Private cross-binding tests may supply a source-only placeholder
        # document.  Such a row is not the target instance for this link.
        if type(target) is not dict or pointer not in target:
            continue
        if source_id not in by_id:
            unresolved_count += 1
            continue
        expected = body(source_id) if digest_kind == "body" else raw(source_id)
        if target[pointer] != expected:
            raise ValueError("cross-artifact digest binding differs: " + pointer)
        validated_count += 1
    if "frozen-protocol-sha256" in by_id:
        if "frozen-protocol" not in by_id:
            unresolved_count += 1
        else:
            sidecar_value = by_id["frozen-protocol-sha256"][0][3]
            if sidecar_value != raw("frozen-protocol"):
                raise ValueError(
                    "cross-artifact digest binding differs: frozen protocol sidecar"
                )
            validated_count += 1
    selected_contracts = {
        contract.contract_id: contract
        for contract in _build_digest_contracts(_build_field_rules())
        if contract.contract_id.startswith("v15-machine-manifest:")
    }
    for (
        target_id,
        target_pointer,
    ), contract_id in _SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES.items():
        if contract_id not in selected_contracts or target_id not in by_id:
            continue
        if "frozen-machine-manifest" not in by_id:
            unresolved_count += 1
            continue
        source_contract = selected_contracts[contract_id]
        selected_value = _resolve_closed_json_pointer(
            by_id["frozen-machine-manifest"][0][3],
            source_contract.digest_field_pointer,
        )
        _require_sha256(
            selected_value, "selected predecessor stored digest", nonzero=True
        )
        target_document = by_id[target_id][0][3]
        if target_pointer == "/requests/*/runtime_lock_sha256":
            target_values = tuple(
                row["runtime_lock_sha256"] for row in target_document["requests"]
            )
            if not target_values or any(
                value != selected_value for value in target_values
            ):
                raise ValueError("selected predecessor stored digest binding differs")
            validated_count += len(target_values)
        else:
            target_value = _resolve_closed_json_pointer(target_document, target_pointer)
            if target_value != selected_value:
                raise ValueError("selected predecessor stored digest binding differs")
            validated_count += 1
    if "committed-marker" in by_id and "auxiliary-metadata-reservation" in by_id:
        committed = by_id["committed-marker"][0][3]
        reservation = by_id["auxiliary-metadata-reservation"][0][3]
        for key in (
            "hold_relative_path",
            "hold_device_identity_sha256",
            "hold_inode",
            "hold_extent_map_sha256",
        ):
            if committed[key] != reservation[key]:
                raise ValueError("COMMITTED hold identity differs: " + key)
        validated_count += 4
    if (
        "source-manifest" in by_id
        and type(by_id["source-manifest"][0][3]) is dict
        and "entries" in by_id["source-manifest"][0][3]
    ):
        if "frozen-source-fixture-materialization" not in by_id:
            unresolved_count += 1
        else:
            manifest_rows = by_id["source-manifest"][0][3]["entries"]
            archive_rows = by_id["frozen-source-fixture-materialization"][0][3]
            manifest_projection = tuple(
                (
                    row["relative_path"],
                    row["bytes"],
                    row["lines"],
                    row["sha256"],
                )
                for row in manifest_rows
            )
            if manifest_projection != archive_rows:
                raise ValueError(
                    "source materialization rows differ from source manifest"
                )
            validated_count += len(archive_rows)
    for qualification_id, pointer in (
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "independent_recomputation_source_manifest_sha256",
        ),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "independent_source_manifest_sha256",
        ),
    ):
        if qualification_id not in by_id:
            continue
        if "source-manifest" not in by_id:
            unresolved_count += 1
            continue
        expected_submanifest = _independent_recomputation_source_submanifest_sha256(
            by_id["source-manifest"][0][3]
        )
        if by_id[qualification_id][0][3][pointer] != expected_submanifest:
            raise ValueError(
                "independent qualification source submanifest digest differs"
            )
        validated_count += 1
    if "power-review-signoff" in by_id:
        if "power-threshold-receipt" not in by_id:
            unresolved_count += 1
        else:
            signoff = by_id["power-review-signoff"][0][3]
            receipt = by_id["power-threshold-receipt"][0][3]
            for key in (
                "protocol_sha256",
                "machine_manifest_sha256",
                "power_review_sha256",
                "selected_count_justification_sha256",
                "primary_slot_count",
                "ordered_slot_threshold_row_sha256s",
                "ordered_slot_thresholds_sha256",
            ):
                if signoff[key] != receipt[key]:
                    raise ValueError("power-review signoff binding differs: " + key)
                validated_count += 1
    journal_dependents = tuple(
        artifact_id
        for artifact_id in (
            "partial-seed-acquisition-terminal-receipt",
            "external-seed-source-receipt",
            "seed-source-authority-attestation",
        )
        if artifact_id in by_id
    )
    if journal_dependents:
        missing = tuple(
            artifact_id
            for artifact_id in (
                "external-seed-acquisition-start-receipt",
                "external-seed-acquisition-journal",
            )
            if artifact_id not in by_id
        )
        if missing:
            unresolved_count += len(missing) * len(journal_dependents)
        else:
            start_body = body("external-seed-acquisition-start-receipt")
            journal_payload = by_id["external-seed-acquisition-journal"][0][1]
            prefix_count, prefix_head, prefix_values = _journal_prefix(
                journal_payload, start_body
            )
            journal_sha = hashlib.sha256(journal_payload).hexdigest()
            commitment = _ordered_seed_values_commitment(prefix_values)
            for artifact_id in journal_dependents:
                document = by_id[artifact_id][0][3]
                if document["acquisition_start_receipt_sha256"] != start_body:
                    raise ValueError("journal dependent start digest differs")
                if document["acquisition_journal_sha256"] != journal_sha:
                    raise ValueError("journal dependent full-file digest differs")
                if document["acquisition_journal_head_sha256"] != prefix_head:
                    raise ValueError("journal dependent recovered head differs")
                if document["acquisition_journal_entry_count"] != prefix_count:
                    raise ValueError("journal dependent recovered count differs")
                commitment_key = (
                    "ordered_partial_seed_values_commitment_sha256"
                    if artifact_id == "partial-seed-acquisition-terminal-receipt"
                    else "ordered_seed_values_commitment_sha256"
                )
                if document[commitment_key] != commitment:
                    raise ValueError("journal dependent sequence commitment differs")
                if artifact_id == "partial-seed-acquisition-terminal-receipt":
                    if document["acquisition_journal_raw_bytes"] != 163_840:
                        raise ValueError("partial journal raw-byte count differs")
                    if tuple(document["ordered_partial_seed_values"]) != prefix_values:
                        raise ValueError("partial journal values differ")
                elif prefix_count != 2_048:
                    raise ValueError(
                        "completed journal does not contain 2048 valid entries"
                    )
                validated_count += 5
    if (
        "partial-seed-acquisition-terminal-receipt" in by_id
        and "external-seed-source-receipt" in by_id
    ):
        raise ValueError("partial and completed source receipt arms cannot coexist")
    if (
        "preauthorization-outcome" in by_id
        and type(by_id["preauthorization-outcome"][0][3]) is dict
        and "prepared_launch_authorization_sha256"
        in by_id["preauthorization-outcome"][0][3]
    ):
        outcome = by_id["preauthorization-outcome"][0][3]
        prepared = outcome["prepared_launch_authorization_sha256"]
        if outcome["outcome_arm"] == "AUTHORIZATION":
            if "launch-authorization" not in by_id or prepared != raw(
                "launch-authorization"
            ):
                raise ValueError(
                    "authorization outcome does not bind published identical bytes"
                )
            if "rejected-launch-authorization-candidate" in by_id:
                raise ValueError(
                    "authorization winner cannot retain rejected candidate"
                )
        elif prepared != _ZERO_SHA256:
            if "rejected-launch-authorization-candidate" not in by_id:
                raise ValueError(
                    "losing prepared authorization candidate is not retained"
                )
            if prepared != raw("rejected-launch-authorization-candidate"):
                raise ValueError("rejected authorization candidate bytes differ")
            if "launch-authorization" in by_id:
                raise ValueError(
                    "terminal preauthorization arm published final authorization"
                )
    if "production-schedule" in by_id and "seed-capsule-body" in by_id:
        schedule = by_id["production-schedule"][0][3]
        capsule = by_id["seed-capsule-body"][0][3]
        for row in schedule["requests"]:
            if (
                row["plan_seed_hex"]
                != capsule["ordered_seed_values"][row["seed_ordinal"] - 1]
            ):
                raise ValueError("schedule plan seed differs from capsule ordinal")
        validated_count += 1
    return validated_count, unresolved_count


def _public_key_identity(
    key: dict,
    *,
    scheme_field: str,
    identity_domain: bytes,
) -> str:
    identity = {
        scheme_field: key[scheme_field],
        "authority_id": key.get("authority_id", key.get("source_authority_id")),
        "modulus_hex": key["modulus_hex"],
        "public_exponent": key["public_exponent"],
    }
    if scheme_field == "source_authority_scheme_id":
        identity["source_authority_id"] = identity.pop("authority_id")
    return hashlib.sha256(identity_domain + _plain_json_bytes(identity)).hexdigest()


def _reviewer_key_identity(key: dict) -> str:
    identity = {
        "reviewer_role": key["reviewer_role"],
        "reviewer_identity_sha256": key["reviewer_identity_sha256"],
        "signature_scheme_id": key["signature_scheme_id"],
        "authority_id": key["authority_id"],
        "modulus_hex": key["modulus_hex"],
        "public_exponent": key["public_exponent"],
    }
    return hashlib.sha256(
        b"cp65-test28-independent-reviewer-public-key-identity-v1\0"
        + _plain_json_bytes(identity)
    ).hexdigest()


def _verify_signed_document(
    document: dict,
    key: dict,
    *,
    scheme_field: str,
    identity_field: str,
    signature_hex_field: str,
    signature_sha_field: str,
    issued_field: str,
    expires_field: str,
    key_scheme_field: str,
    key_identity_domain: bytes,
    signing_domain: bytes,
) -> bool:
    if document[scheme_field] != key[key_scheme_field]:
        return False
    if key["public_exponent"] != 65_537:
        return False
    expected_identity = _public_key_identity(
        key,
        scheme_field=key_scheme_field,
        identity_domain=key_identity_domain,
    )
    if document[identity_field] != expected_identity:
        return False
    issued = _require_utc(document[issued_field], issued_field)
    expires = _require_utc(document[expires_field], expires_field)
    valid_from = _require_utc(key["valid_from_utc"], "valid_from_utc")
    valid_until = _require_utc(key["valid_until_utc"], "valid_until_utc")
    if not valid_from <= issued < expires <= valid_until:
        return False
    signature_hex = document[signature_hex_field]
    if type(signature_hex) is not str or _HEX768_RE.fullmatch(signature_hex) is None:
        return False
    signature = bytes.fromhex(signature_hex)
    if document[signature_sha_field] != hashlib.sha256(signature).hexdigest():
        return False
    unsigned = dict(document)
    unsigned[signature_hex_field] = ""
    unsigned[signature_sha_field] = _ZERO_SHA256
    unsigned["body_sha256"] = _ZERO_SHA256
    message = signing_domain + _plain_json_bytes(unsigned)
    return _verify_rsa_pss_sha256_3072(
        message,
        bytes.fromhex(key["modulus_hex"]),
        signature,
    )


def _candidate_completeness_flags(
    field_rules: Tuple[CP65FieldRuleV1, ...],
    artifact_schemas: Tuple[CP65ArtifactSchemaV1, ...],
    transient_path_contracts: Tuple[CP65TransientPathContractV1, ...],
    digest_contracts: Tuple[CP65DigestPreimageContractV1, ...],
    sha256_pointer_contracts: Tuple[CP65Sha256PointerContractV1, ...],
    predicates: Tuple[CP65PredicateContractV1, ...],
    gates: Tuple[CP65GateRequirementV1, ...],
    bounds: Tuple[CP65AuxiliaryArtifactBoundV1, ...],
    proof: CP65AuxiliarySizeProofV1,
    signature: CP65AuthorizationSignatureContractV1,
    graph: Tuple[object, ...],
) -> Mapping[str, bool]:
    """Recompute the narrow definition-completeness claims from the catalog."""

    def unique(rows: tuple, attribute: str) -> bool:
        values = tuple(getattr(row, attribute) for row in rows)
        return len(values) == len(set(values))

    artifact_ids = {row.artifact_id for row in artifact_schemas}
    rule_ids = {row.rule_id for row in field_rules}
    predicate_ids = {row.predicate_id for row in predicates}
    digest_ids = {row.contract_id for row in digest_contracts}
    pointer_ids = {row.classification_id for row in sha256_pointer_contracts}
    bound_ids = {row.bound_id for row in bounds}
    identities_unique = all(
        (
            unique(artifact_schemas, "artifact_id"),
            unique(field_rules, "rule_id"),
            unique(predicates, "predicate_id"),
            unique(digest_contracts, "contract_id"),
            unique(sha256_pointer_contracts, "classification_id"),
            unique(bounds, "bound_id"),
        )
    )

    rule_pairs = {(row.artifact_id, row.json_pointer) for row in field_rules}
    keysets_complete = identities_unique and set(_RECEIPT_ENVELOPE_IDS) <= artifact_ids
    for schema in artifact_schemas:
        if schema.media_kind == "receipt-envelope-canonical-json":
            keysets_complete = (
                keysets_complete
                and bool(schema.exact_keys)
                and all(
                    (schema.artifact_id, "/" + key) in rule_pairs
                    for key in schema.exact_keys
                )
            )
        keysets_complete = keysets_complete and set(schema.field_rule_ids) <= rule_ids

    field_semantics_complete = identities_unique
    for row in field_rules:
        field_semantics_complete = (
            field_semantics_complete
            and row.artifact_id in artifact_ids
            and row.required is True
            and set(row.array_item_rule_ids) <= rule_ids
            and set(row.cross_constraint_ids) <= predicate_ids
        )
        if row.value_kind == "boolean":
            field_semantics_complete = field_semantics_complete and bool(
                row.boolean_domain
            )
        elif row.value_kind == "integer":
            field_semantics_complete = field_semantics_complete and (
                len(row.integer_interval) == 2
                and row.integer_interval[0] <= row.integer_interval[1]
            )
        elif row.value_kind == "string":
            field_semantics_complete = field_semantics_complete and bool(
                row.string_domain or row.string_pattern_id
            )
        elif row.value_kind == "array":
            field_semantics_complete = field_semantics_complete and (
                len(row.length_interval) == 2
                and row.length_interval[0] <= row.length_interval[1]
                and bool(row.array_item_rule_ids)
            )
        elif row.value_kind == "object":
            field_semantics_complete = field_semantics_complete and bool(
                row.exact_object_keys
            )
        else:
            field_semantics_complete = False

    referenced_rules = set()
    referenced_predicates = set()
    referenced_digests = set()
    referenced_artifacts = set()
    for schema in artifact_schemas:
        referenced_rules.update(schema.field_rule_ids)
        referenced_predicates.update((schema.presence_rule_id, schema.record_rule_id))
        referenced_digests.add(schema.digest_preimage_contract_id)
    for row in field_rules:
        referenced_artifacts.add(row.artifact_id)
        referenced_rules.update(row.array_item_rule_ids)
        referenced_predicates.update(row.cross_constraint_ids)
    for row in predicates:
        referenced_artifacts.update(row.applies_to_artifact_ids)
        referenced_predicates.update(row.child_predicate_ids)
    for row in gates:
        referenced_artifacts.add(row.evidence_artifact_id)
        referenced_artifacts.update(row.required_artifact_ids)
        referenced_predicates.add(row.predicate_id)
        referenced_predicates.update(row.predicate_clause_ids)
    for row in bounds:
        if not row.artifact_id.startswith("__"):
            referenced_artifacts.add(row.artifact_id)
        referenced_predicates.add(row.simultaneous_presence_rule_id)
    referenced_digests.update(_GATE_DAG_EDGE_SOURCE_CONTRACT_IDS)
    referenced_digests.update(cast(Tuple[str, ...], graph[3]))
    referenced_digests.update(
        row.source_contract_id
        for row in sha256_pointer_contracts
        if row.source_contract_id
    )
    references_resolve = (
        referenced_rules <= rule_ids
        and referenced_predicates <= predicate_ids
        and referenced_digests <= digest_ids
        and referenced_artifacts <= artifact_ids
    )
    no_orphans = (
        references_resolve
        and referenced_rules == rule_ids
        and referenced_predicates == predicate_ids
        and referenced_artifacts == artifact_ids
        and digest_ids - referenced_digests == {"committed-marker:raw-sha256"}
    )
    digest_validators_complete = all(
        row.verifier_implemented for row in digest_contracts
    )
    pointer_validator_scope_complete = all(
        row.validator_implemented
        == _sha256_pointer_validator_implemented(
            row.target_artifact_id,
            row.target_json_pointer,
            row.source_artifact_id,
        )
        for row in sha256_pointer_contracts
    )
    executable = (
        references_resolve
        and field_semantics_complete
        and digest_validators_complete
        and pointer_validator_scope_complete
        and all(
            row.validator_implemented and row.operation_id in _PREDICATE_OPERATION_IDS
            for row in predicates
        )
    )

    sha_rule_pairs = {
        (row.artifact_id, row.json_pointer)
        for row in field_rules
        if _is_sha256_field_rule(row)
    }
    pointer_pairs = {
        (row.target_artifact_id, row.target_json_pointer)
        for row in sha256_pointer_contracts
    }
    pointer_cover = (
        identities_unique
        and len(pointer_ids) == len(sha256_pointer_contracts)
        and len(pointer_pairs) == len(sha256_pointer_contracts)
        and pointer_pairs == sha_rule_pairs
        and all(
            "fallback" not in row.classification_id for row in sha256_pointer_contracts
        )
    )

    gate15_artifacts = {
        artifact_id
        for row in gates
        if 1 <= row.gate_ordinal <= 15
        for artifact_id in (row.evidence_artifact_id,) + row.required_artifact_ids
    }
    registry_rows = tuple(
        row for row in sha256_pointer_contracts if row.preimage_registry_entry_required
    )
    registry_temporal = bool(registry_rows) and all(
        row.externally_retained_preimage_required
        and row.target_artifact_id in gate15_artifacts
        and row.source_availability_cut_id
        == "durable-by-gate15-before-registry-finalization"
        for row in registry_rows
    )
    no_late_registry = all(
        not row.preimage_registry_entry_required
        for row in sha256_pointer_contracts
        if row.target_artifact_id not in gate15_artifacts
    )

    nodes = cast(Tuple[str, ...], graph[0])
    edges = cast(Tuple[Tuple[str, str], ...], graph[1])
    order = cast(Tuple[str, ...], graph[5])
    positions = {node: ordinal for ordinal, node in enumerate(order)}
    graph_complete = (
        len(nodes) == len(set(nodes))
        and len(edges) == len(set(edges))
        and len(order) == len(nodes)
        and set(order) == set(nodes)
        and all(
            source in positions
            and target in positions
            and positions[source] < positions[target]
            for source, target in edges
        )
        and len(cast(tuple, graph[2])) == len(edges)
        and len(cast(tuple, graph[3])) == len(edges)
        and len(cast(tuple, graph[4])) == len(edges)
        and set(cast(Tuple[str, ...], graph[3])) <= digest_ids
        and {row.source_contract_id for row in sha256_pointer_contracts}
        <= set(cast(Tuple[str, ...], graph[3]))
    )

    expanded_paths = []
    scopes = {"global": 0, "per-shard": 0, "conditional-global": 0}
    for schema in artifact_schemas:
        if schema.path_scope not in scopes:
            continue
        scopes[schema.path_scope] += 1
        if schema.path_scope == "per-shard":
            expanded_paths.extend(
                schema.path_template.replace("{shard_id}", "shard-%04d" % shard_ordinal)
                for shard_ordinal in range(1, 33)
            )
        else:
            expanded_paths.append(schema.path_template)
    transient_ids = tuple(row.transient_path_id for row in transient_path_contracts)
    roster_complete = (
        identities_unique
        and len(expanded_paths) == len(set(expanded_paths)) == 312
        and scopes == {"global": 54, "per-shard": 8, "conditional-global": 2}
        and len(transient_ids) == len(set(transient_ids)) == 310
        and all(row.collision_free for row in transient_path_contracts)
        and set(_RECEIPT_ENVELOPE_IDS)
        | set(_REFERENCED_OUTPUT_IDS)
        | set(_FROZEN_OR_BINARY_CUSTODY_IDS)
        == artifact_ids
        and not (set(_RECEIPT_ENVELOPE_IDS) & set(_REFERENCED_OUTPUT_IDS))
        and not (set(_RECEIPT_ENVELOPE_IDS) & set(_FROZEN_OR_BINARY_CUSTODY_IDS))
        and not (set(_REFERENCED_OUTPUT_IDS) & set(_FROZEN_OR_BINARY_CUSTODY_IDS))
    )

    grouped = {}
    for row in bounds:
        if row.destination_reservation_excluded and not row.artifact_id.startswith(
            "__"
        ):
            grouped.setdefault(row.physical_slot_group_id, []).append(row)
    derived_logical = sum(
        max(
            row.maximum_instance_count * row.maximum_logical_bytes_per_instance
            for row in rows
        )
        for rows in grouped.values()
    )
    derived_reserved = sum(
        max(row.maximum_total_reserved_bytes for row in rows)
        for rows in grouped.values()
    )
    auxiliary_complete = (
        identities_unique
        and set(proof.artifact_bound_ids) == bound_ids
        and len(proof.artifact_bound_ids) == len(bounds)
        and set(proof.covered_complete_roster_artifact_ids) == artifact_ids
        and all(
            set(row.mutually_exclusive_artifact_ids) <= artifact_ids
            for row in bounds
            if not row.artifact_id.startswith("__")
        )
        and derived_logical == proof.maximum_auxiliary_artifact_logical_bytes
        and derived_reserved == proof.maximum_auxiliary_artifact_slot_reserved_bytes
        and derived_reserved + proof.allocation_and_directory_charge_policy_slot_bytes
        == proof.maximum_auxiliary_policy_required_bytes
        and proof.maximum_auxiliary_policy_required_bytes
        + proof.exclusive_reserved_policy_headroom_bytes
        == proof.auxiliary_reservation_floor_bytes
    )

    gate_complete = (
        len(gates) == 17
        and tuple(row.gate_ordinal for row in gates) == tuple(range(1, 18))
        and len({row.gate_id for row in gates}) == 17
        and all(
            row.evidence_artifact_id in artifact_ids
            and set(row.required_artifact_ids) <= artifact_ids
            and row.predicate_id in predicate_ids
            and set(row.predicate_clause_ids) <= predicate_ids
            and not row.evidence_present
            and row.gate_state == "MISSING"
            for row in gates
        )
        and all(row.preflight_summary_covered for row in gates[:15])
        and all(not row.preflight_summary_covered for row in gates[15:])
    )
    signature_complete = (
        signature.scheme_id == "rsa-pss-sha256-3072-e65537-salt32-v1"
        and signature.hash_algorithm_id == "sha256"
        and signature.mgf_algorithm_id == "mgf1-sha256"
        and (
            signature.modulus_bytes,
            signature.modulus_bit_length,
            signature.public_exponent,
            signature.signature_bytes,
            signature.signature_hex_characters,
            signature.salt_bytes,
            signature.em_bits,
            signature.em_bytes,
        )
        == (384, 3072, 65_537, 384, 768, 32, 3071, 384)
        and signature.verifier_implemented
        and not signature.signer_implemented
        and not signature.key_generation_implemented
        and not signature.public_key_present
        and not signature.trust_root_bound
        and not signature.signature_instance_present
        and not signature.authority_verified
        and not signature.launch_authorized
    )
    terminal_complete = all(
        artifact_id in artifact_ids
        for artifact_id in (
            "preauthorization-outcome",
            "postauthorization-outcome",
            "preterminal-durable-artifact-inventory",
            "terminal-state",
            "sha256-manifest",
            "committed-marker",
        )
    ) and {
        row.string_domain
        for row in field_rules
        if row.artifact_id == "preterminal-durable-artifact-inventory"
        and row.json_pointer == "/terminal_arm"
    } == {
        ("PREAUTHORIZATION", "POSTAUTHORIZATION_PRESTART", "STARTED")
    }
    digest_complete = (
        pointer_cover
        and references_resolve
        and graph_complete
        and registry_temporal
        and no_late_registry
        and digest_validators_complete
        and pointer_validator_scope_complete
    )
    return {
        "sha256_pointer_contracts_cover_every_sha256_field_rule": pointer_cover,
        "registry_required_targets_all_durable_by_gate15": registry_temporal,
        "later_artifacts_have_no_registry_dependency": no_late_registry,
        "all_schema_references_resolve_exactly_once": references_resolve
        and identities_unique,
        "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids": no_orphans
        and identities_unique,
        "all_referenced_rules_have_executable_validator_semantics": executable,
        "artifact_preimage_dag_complete": graph_complete,
        "all_required_production_receipt_keysets_predeclared": keysets_complete,
        "complete_receipt_type_range_size_and_domain_schemas_frozen": field_semantics_complete
        and keysets_complete,
        "complete_auxiliary_artifact_size_schema_frozen": auxiliary_complete,
        "bounded_auxiliary_artifact_size_proof_present": auxiliary_complete,
        "generic_prestart_terminal_record_schema_frozen": terminal_complete,
        "all_required_production_receipt_digest_preimages_frozen": digest_complete,
        "authorization_signature_preimage_and_verifier_frozen": signature_complete,
        "requirement_schemas_frozen": gate_complete and executable,
        "complete_final_path_template_roster_frozen": roster_complete,
    }


def cp65_production_schema_preimage_validator_bundle() -> CP65ProductionSchemaPreimageValidatorBundleV1:
    """Return the deterministic definition-only CP65 catalog bundle."""

    field_rules = _build_field_rules()
    artifact_schemas = _build_artifact_schemas(field_rules)
    transient_path_contracts = _build_transient_path_contracts()
    digest_contracts = _build_digest_contracts(field_rules)
    sha256_pointer_contracts = _build_sha256_pointer_contracts(
        field_rules, digest_contracts
    )
    predicates = _build_predicates(field_rules)
    gates = _build_gate_requirements()
    bounds = _build_auxiliary_bounds()
    proof = _build_auxiliary_size_proof(bounds)
    signature = _signature_contract()
    graph = _build_artifact_preimage_graph(digest_contracts, sha256_pointer_contracts)
    semantic_sha256 = _semantic_sha256(
        field_rules,
        artifact_schemas,
        transient_path_contracts,
        digest_contracts,
        sha256_pointer_contracts,
        predicates,
        gates,
        bounds,
        proof,
        signature,
        graph,
    )
    completeness_flags = _candidate_completeness_flags(
        field_rules,
        artifact_schemas,
        transient_path_contracts,
        digest_contracts,
        sha256_pointer_contracts,
        predicates,
        gates,
        bounds,
        proof,
        signature,
        graph,
    )
    satisfied_definition_count = sum(completeness_flags.values())
    if satisfied_definition_count != 16:
        raise RuntimeError("CP65 candidate definition completeness audit differs")
    return cast(
        CP65ProductionSchemaPreimageValidatorBundleV1,
        _record(
            CP65ProductionSchemaPreimageValidatorBundleV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "scope": CP65_TEST28_SCOPE,
                "predecessor_custody": _predecessor_custody(),
                "canonical_profile_id": _CANONICAL_PROFILE_ID,
                "field_rules": field_rules,
                "artifact_schemas": artifact_schemas,
                "transient_path_contracts": transient_path_contracts,
                "digest_preimage_contracts": digest_contracts,
                "sha256_pointer_contracts": sha256_pointer_contracts,
                "predicate_contracts": predicates,
                "gate_requirements": gates,
                "auxiliary_artifact_bounds": bounds,
                "auxiliary_size_proof": proof,
                "authorization_signature_contract": signature,
                "schema_semantic_sha256": semantic_sha256,
                "sha256_pointer_contract_count": len(sha256_pointer_contracts),
                "sha256_pointer_contracts_cover_every_sha256_field_rule": completeness_flags[
                    "sha256_pointer_contracts_cover_every_sha256_field_rule"
                ],
                "registry_required_targets_all_durable_by_gate15": completeness_flags[
                    "registry_required_targets_all_durable_by_gate15"
                ],
                "later_artifacts_have_no_registry_dependency": completeness_flags[
                    "later_artifacts_have_no_registry_dependency"
                ],
                "all_schema_references_resolve_exactly_once": completeness_flags[
                    "all_schema_references_resolve_exactly_once"
                ],
                "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids": completeness_flags[
                    "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids"
                ],
                "all_referenced_rules_have_executable_validator_semantics": completeness_flags[
                    "all_referenced_rules_have_executable_validator_semantics"
                ],
                "global_path_count": len(_GLOBAL_PATHS),
                "per_shard_path_template_count": len(_PER_SHARD_PATHS),
                "conditional_path_count": len(_CONDITIONAL_PATHS),
                "expanded_final_path_count": 312,
                "reserved_destination_partial_path_count": 128,
                "prepared_authorization_partial_path_count": 1,
                "auxiliary_reserved_partial_or_existing_final_slot_count": 183,
                "auxiliary_reservation_hold_path_count": 1,
                "ordinary_auxiliary_partial_candidate_path_count": 181,
                "expanded_transient_path_count": 310,
                "expanded_final_and_transient_path_count": 622,
                "generic_writer_partial_paths_are_state_aliases": True,
                "expanded_final_and_transient_paths_collision_free": True,
                "candidate_shard_count": 32,
                "gate_count": 17,
                "evidence_present_count": 0,
                "digest_dag_node_count": len(_GATE_DAG_NODES),
                "digest_dag_edge_count": len(_GATE_DAG_EDGES),
                "digest_dag_node_ids": _GATE_DAG_NODES,
                "digest_dag_edges": _GATE_DAG_EDGES,
                "digest_dag_edge_target_pointers": _GATE_DAG_EDGE_TARGET_POINTERS,
                "digest_dag_edge_source_contract_ids": _GATE_DAG_EDGE_SOURCE_CONTRACT_IDS,
                "digest_dag_edge_digest_kinds": _GATE_DAG_EDGE_DIGEST_KINDS,
                "digest_dag_is_gate_evidence_only": True,
                "artifact_preimage_dependency_node_ids": graph[0],
                "artifact_preimage_dependency_edges": graph[1],
                "artifact_preimage_edge_target_pointers": graph[2],
                "artifact_preimage_edge_source_contract_ids": graph[3],
                "artifact_preimage_edge_digest_kinds": graph[4],
                "artifact_preimage_topological_order": graph[5],
                "artifact_preimage_node_count": len(graph[0]),
                "artifact_preimage_edge_count": len(graph[1]),
                "artifact_preimage_dag_acyclic": True,
                "artifact_preimage_dag_complete": completeness_flags[
                    "artifact_preimage_dag_complete"
                ],
                "artifact_body_domain_separators_unique": True,
                "receipt_envelope_artifact_ids": _RECEIPT_ENVELOPE_IDS,
                "referenced_execution_output_artifact_ids": _REFERENCED_OUTPUT_IDS,
                "frozen_or_binary_custody_artifact_ids": _FROZEN_OR_BINARY_CUSTODY_IDS,
                "receipt_envelope_schema_count": len(_RECEIPT_ENVELOPE_IDS),
                "referenced_execution_output_schema_count": len(_REFERENCED_OUTPUT_IDS),
                "frozen_or_binary_custody_schema_count": len(
                    _FROZEN_OR_BINARY_CUSTODY_IDS
                ),
                "artifact_kind_partitions_disjoint_and_exhaustive": True,
                "schema_completeness_claim_scope": "supplied-receipt-envelope-instance-canonical-fields-digests-and-pure-gate-predicates-only;excludes-lifecycle-occurrence-branch-presence-provenance-trust-evidence-and-execution-output-semantics",
                "all_required_production_receipt_keysets_predeclared": completeness_flags[
                    "all_required_production_receipt_keysets_predeclared"
                ],
                "complete_receipt_type_range_size_and_domain_schemas_frozen": completeness_flags[
                    "complete_receipt_type_range_size_and_domain_schemas_frozen"
                ],
                "complete_auxiliary_artifact_size_schema_frozen": completeness_flags[
                    "complete_auxiliary_artifact_size_schema_frozen"
                ],
                "bounded_auxiliary_artifact_size_proof_present": completeness_flags[
                    "bounded_auxiliary_artifact_size_proof_present"
                ],
                "generic_prestart_terminal_record_schema_frozen": completeness_flags[
                    "generic_prestart_terminal_record_schema_frozen"
                ],
                "all_required_production_receipt_digest_preimages_frozen": completeness_flags[
                    "all_required_production_receipt_digest_preimages_frozen"
                ],
                "complete_production_digest_instance_validation_interface_frozen": False,
                "authorization_signature_preimage_and_verifier_frozen": completeness_flags[
                    "authorization_signature_preimage_and_verifier_frozen"
                ],
                "requirement_schemas_frozen": completeness_flags[
                    "requirement_schemas_frozen"
                ],
                "complete_final_path_template_roster_frozen": completeness_flags[
                    "complete_final_path_template_roster_frozen"
                ],
                "complete_production_roster_frozen": False,
                "artifact_occurrence_and_branch_schema_frozen": False,
                "production_receipt_schema_frozen": False,
                "production_execution_and_output_schema_frozen": False,
                "production_schema_frozen": False,
                "source_receipt_binds_capsule_body": False,
                "capacity_receipt_binds_shard_map": False,
                "external_production_receipts_observed": False,
                "external_seed_values_present": False,
                "source_authority_verified": False,
                "production_runtime_observed": False,
                "capacity_observed": False,
                "durability_observed": False,
                "candidate_shard_policy_selected": False,
                "production_shard_map_instantiated": False,
                "runner_supervisor_qualified": False,
                "closed_classifier_qualified": False,
                "power_thresholds_frozen": False,
                "freeze_receipt_present": False,
                "independent_signoffs_present": False,
                "launch_authorization_present": False,
                "started": False,
                "production_requests_materialized": False,
                "production_campaign_exposed": False,
                "production_execution_authorized": False,
                "production_execution_observed": False,
                "estimates_computed": False,
                "intervals_computed": False,
                "decision_made": False,
                "runner_and_recomputation_blocker_closed": False,
                "unconditional_operational_predictions_blocker_closed": False,
                "power_and_thresholds_blocker_closed": False,
                "confirmatory_custody_blocker_closed": False,
                "confirmatory_evidence": False,
                "manuscript_claim": False,
                "formal_test_28_status": "OPEN",
                "formal_test_28_closed": False,
                "ledger_prerequisite_id": "whole_seed_production_schema_preimage_and_validator_definition",
                "ledger_total_count": 20,
                "ledger_satisfied_count": satisfied_definition_count,
                "ledger_missing_count": 20 - satisfied_definition_count,
                "zero_argument_builder": True,
                "stdlib_only_import": True,
                "project_modules_imported": False,
                "host_filesystem_probed": False,
                "clock_read": False,
                "rng_used": False,
                "network_used": False,
                "subprocess_api_exposed": False,
                "filesystem_path_api_exposed": False,
                "definition_only": True,
            },
        ),
    )


def cp65_artifact_schema(artifact_id: object) -> CP65ArtifactSchemaV1:
    """Return one exact artifact schema from the frozen catalog."""

    if type(artifact_id) is not str:
        raise TypeError("artifact_id must be an exact string")
    for schema in cp65_production_schema_preimage_validator_bundle().artifact_schemas:
        if schema.artifact_id == artifact_id:
            return schema
    raise ValueError("unknown CP65 artifact id")


def _validate_supplied_artifact_bytes_impl(
    artifact_id: object, relative_path: object, payload: object
) -> CP65SuppliedValidationV1:
    """Validate caller-supplied bytes without treating them as evidence."""

    if type(artifact_id) is not str:
        raise TypeError("artifact_id must be an exact string")
    if type(relative_path) is not str:
        raise TypeError("relative_path must be an exact string")
    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    body_sha256, _document = _validate_artifact_payload(
        artifact_id, relative_path, payload
    )
    validated_count, unresolved_count = _validate_supplied_cross_bindings(
        {
            artifact_id: [
                (relative_path, payload, body_sha256, _document),
            ]
        }
    )
    digest_validated_count, digest_unresolved_count = _intrinsic_digest_instance_counts(
        artifact_id, _document
    )
    return _supplied_validation(
        (artifact_id,),
        (relative_path,),
        (payload,),
        (body_sha256,),
        validated_digest_preimage_count=digest_validated_count,
        unresolved_digest_preimage_count=digest_unresolved_count,
        validated_cross_binding_count=validated_count,
        unresolved_cross_binding_count=unresolved_count,
    )


def _validate_supplied_artifact_set_impl(items: object) -> CP65SuppliedValidationV1:
    """Validate a bounded tuple of artifact-id/path/bytes triples."""

    if type(items) is not tuple:
        raise TypeError("items must be an exact tuple")
    if not 1 <= len(items) <= _MAX_SUPPLIED_ARTIFACT_SET_ITEMS:
        raise ValueError("supplied artifact set cardinality is outside 1..312")
    normalized = []
    total_bytes = 0
    paths = set()
    for item in items:
        if type(item) is not tuple or len(item) != 3:
            raise TypeError("each supplied item must be an exact three-tuple")
        artifact_id, relative_path, payload = item
        if type(artifact_id) is not str or type(relative_path) is not str:
            raise TypeError("supplied artifact id/path must be exact strings")
        if type(payload) is not bytes:
            raise TypeError("supplied artifact payload must be exact bytes")
        if relative_path in paths:
            raise ValueError("supplied artifact paths must be unique")
        paths.add(relative_path)
        total_bytes += len(payload)
        if total_bytes > _MAX_SUPPLIED_ARTIFACT_SET_BYTES:
            raise ValueError("supplied artifact set exceeds 512 MiB")
        normalized.append((artifact_id, relative_path, payload))
    by_id = {}
    body_sha256s = []
    aggregate_nodes = 0
    aggregate_decoded_characters = 0
    for artifact_id, relative_path, payload in normalized:
        body_sha256, document = _validate_artifact_payload(
            artifact_id, relative_path, payload
        )
        body_sha256s.append(body_sha256)
        if type(document) is dict:
            nodes, decoded_characters = _validate_json_resources(document)
            aggregate_nodes += nodes
            aggregate_decoded_characters += decoded_characters
            if aggregate_nodes > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
                raise ValueError("supplied artifact set contains too many parsed nodes")
            if (
                aggregate_decoded_characters
                > _MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS
            ):
                raise ValueError(
                    "supplied artifact set contains too many decoded string characters"
                )
        by_id.setdefault(artifact_id, []).append(
            (relative_path, payload, body_sha256, document)
        )
    for artifact_id, schema_rows in by_id.items():
        maximum = 32 if _ARTIFACT_BY_ID[artifact_id][2] == "per-shard" else 1
        if len(schema_rows) > maximum:
            raise ValueError("artifact multiplicity exceeds its schema bound")
    if (
        "launch-authorization" in by_id
        and "rejected-launch-authorization-candidate" in by_id
    ):
        raise ValueError(
            "final and rejected launch authorization aliases cannot coexist"
        )
    validated_count, unresolved_count = _validate_supplied_cross_bindings(by_id)
    (
        signature_applicable,
        signature_valid,
        signature_binding_count,
        signature_unresolved_count,
    ) = _validate_supplied_signature_aggregation(by_id)
    validated_count += signature_binding_count
    unresolved_count += signature_unresolved_count
    digest_counts = tuple(
        (
            artifact_id,
            path,
            *_intrinsic_digest_instance_counts(artifact_id, document),
        )
        for artifact_id, rows in by_id.items()
        for path, _payload, _body, document in rows
    )
    digest_validated_count = sum(row[2] for row in digest_counts)
    digest_unresolved_count = sum(row[3] for row in digest_counts)
    (
        registry_binding_count,
        resolved_registry_targets,
    ) = _validate_registry_target_bindings(by_id)
    digest_validated_count += registry_binding_count
    if registry_binding_count:
        # The set worklist is a union: a resolved registry relation replaces
        # both the registry row's target-raw obligation and the target
        # artifact's otherwise-unsupplied digest-source work, rather than
        # counting those endpoints a second time.
        digest_unresolved_count = max(
            0, digest_unresolved_count - registry_binding_count
        )
        for target in set(resolved_registry_targets):
            matching = tuple(row for row in digest_counts if (row[0], row[1]) == target)
            if len(matching) != 1:
                raise ValueError("registry resolved target worklist is ambiguous")
            digest_unresolved_count = max(0, digest_unresolved_count - matching[0][3])
    return _supplied_validation(
        tuple(row[0] for row in normalized),
        tuple(row[1] for row in normalized),
        tuple(row[2] for row in normalized),
        tuple(body_sha256s),
        signature_applicable=signature_applicable,
        signature_valid=signature_valid,
        validated_digest_preimage_count=digest_validated_count,
        unresolved_digest_preimage_count=digest_unresolved_count,
        validated_cross_binding_count=validated_count,
        unresolved_cross_binding_count=unresolved_count,
    )


def cp65_validate_supplied_artifact_bytes(
    artifact_id: object, relative_path: object, payload: object
) -> CP65SuppliedValidationV1:
    """Validate one bounded caller-supplied artifact, normalizing exhaustion."""

    try:
        return _validate_supplied_artifact_bytes_impl(
            artifact_id, relative_path, payload
        )
    except MemoryError as exc:
        raise ValueError("caller-supplied artifact exceeded parser limits") from exc


def cp65_validate_supplied_artifact_set(items: object) -> CP65SuppliedValidationV1:
    """Validate a bounded caller-supplied artifact set, normalizing exhaustion."""

    try:
        return _validate_supplied_artifact_set_impl(items)
    except MemoryError as exc:
        raise ValueError("caller-supplied artifact set exceeded parser limits") from exc


def cp65_verify_launch_authorization_signature(
    receipt_payload: object, public_key_payload: object
) -> CP65SuppliedValidationV1:
    """Verify the fixed signature profile without asserting authority trust."""

    if type(receipt_payload) is not bytes or type(public_key_payload) is not bytes:
        raise TypeError("signature verifier inputs must be exact bytes")
    try:
        return _validate_supplied_artifact_set_impl(
            (
                (
                    "launch-authorization",
                    "launch_authorization.json",
                    receipt_payload,
                ),
                (
                    "launch-authority-public-key",
                    "frozen_inputs/launch_authority_public_key.json",
                    public_key_payload,
                ),
            )
        )
    except MemoryError as exc:
        raise ValueError("signature verifier exceeded parser limits") from exc


def _verify_seed_source_authority_attestation_signature(
    attestation_payload: object, public_key_payload: object
) -> CP65SuppliedValidationV1:
    """Verify a supplied source attestation mathematically, never as trust."""

    if type(attestation_payload) is not bytes or type(public_key_payload) is not bytes:
        raise TypeError("signature verifier inputs must be exact bytes")
    attestation_body, attestation = _validate_artifact_payload(
        "seed-source-authority-attestation",
        "seed_source_authority_attestation.json",
        attestation_payload,
    )
    key_body, key = _validate_artifact_payload(
        "seed-source-authority-public-key",
        "frozen_inputs/seed_source_authority_public_key.json",
        public_key_payload,
    )
    valid = _verify_signed_document(
        attestation,
        key,
        scheme_field="source_authority_scheme_id",
        identity_field="source_authority_identity_sha256",
        signature_hex_field="source_authority_signature_hex",
        signature_sha_field="source_authority_signature_sha256",
        issued_field="attested_at_utc",
        expires_field="attestation_expires_at_utc",
        key_scheme_field="source_authority_scheme_id",
        key_identity_domain=b"cp65-test28-seed-source-authority-public-key-identity-v1\0",
        signing_domain=b"cp65-test28-seed-source-authority-attestation-signature-preimage-v1\0",
    )
    return _supplied_validation(
        ("seed-source-authority-attestation", "seed-source-authority-public-key"),
        (
            "seed_source_authority_attestation.json",
            "frozen_inputs/seed_source_authority_public_key.json",
        ),
        (attestation_payload, public_key_payload),
        (attestation_body, key_body),
        signature_applicable=True,
        signature_valid=valid,
        unresolved_cross_binding_count=5,
    )


def _verify_independent_signoff_signature(
    signoff_row_payload: object, reviewer_public_key_set_payload: object
) -> CP65SuppliedValidationV1:
    """Verify one supplied reviewer signoff row under its declared key."""

    if (
        type(signoff_row_payload) is not bytes
        or type(reviewer_public_key_set_payload) is not bytes
    ):
        raise TypeError("signature verifier inputs must be exact bytes")
    row = _parse_canonical_json_object(signoff_row_payload, 67_108_864)
    if set(row) != set(_SIGNOFF_ROW_KEYS) or len(row) != len(_SIGNOFF_ROW_KEYS):
        raise ValueError("independent signoff row key set differs")
    for key in _SIGNOFF_ROW_KEYS:
        if _explicit_field_kind(key) == "array":
            _validate_primitive_array("independent-signoff-set", key, row[key])
        else:
            _validate_scalar_field(
                "independent-signoff-set", "/ordered_signoffs/*/" + key, key, row[key]
            )
    supplied_row_digest = _require_sha256(row["signoff_sha256"], "signoff row digest")
    zeroed_row = dict(row)
    zeroed_row["signoff_sha256"] = _ZERO_SHA256
    expected_row_digest = hashlib.sha256(
        b"cp65-test28-independent-signoff-row-v1\0" + _plain_json_bytes(zeroed_row)
    ).hexdigest()
    if supplied_row_digest != expected_row_digest:
        raise ValueError("independent signoff row digest differs")
    key_set_body, key_set = _validate_artifact_payload(
        "independent-reviewer-public-key-set",
        "frozen_inputs/independent_reviewer_public_keys.json",
        reviewer_public_key_set_payload,
    )
    matching = tuple(
        key
        for key in key_set["ordered_keys"]
        if key["reviewer_role"] == row["reviewer_role"]
    )
    if len(matching) != 1:
        raise ValueError("reviewer signoff role does not select exactly one key")
    key = matching[0]
    expected_identity = _reviewer_key_identity(key)
    if (
        row["reviewer_identity_sha256"] != key["reviewer_identity_sha256"]
        or row["reviewer_public_key_identity_sha256"] != expected_identity
        or row["signature_scheme_id"] != key["signature_scheme_id"]
    ):
        valid = False
    else:
        signed_at = _require_utc(row["signed_at_utc"], "signed_at_utc")
        valid_from = _require_utc(key["valid_from_utc"], "valid_from_utc")
        valid_until = _require_utc(key["valid_until_utc"], "valid_until_utc")
        signature = bytes.fromhex(row["reviewer_signature_hex"])
        unsigned = dict(row)
        unsigned["reviewer_signature_hex"] = ""
        unsigned["reviewer_signature_sha256"] = _ZERO_SHA256
        unsigned["signoff_sha256"] = _ZERO_SHA256
        valid = (
            valid_from <= signed_at < valid_until
            and row["reviewer_signature_sha256"]
            == hashlib.sha256(signature).hexdigest()
            and _verify_rsa_pss_sha256_3072(
                b"cp65-test28-independent-signoff-row-signature-preimage-v1\0"
                + _plain_json_bytes(unsigned),
                bytes.fromhex(key["modulus_hex"]),
                signature,
            )
        )
    return _supplied_validation(
        ("independent-signoff-set", "independent-reviewer-public-key-set"),
        (
            "independent_signoff.json",
            "frozen_inputs/independent_reviewer_public_keys.json",
        ),
        (signoff_row_payload, reviewer_public_key_set_payload),
        (supplied_row_digest, key_set_body),
        signature_applicable=True,
        signature_valid=valid,
        validated_cross_binding_count=1,
        unresolved_cross_binding_count=2,
    )


def cp65_canonical_json_bytes(record: object) -> bytes:
    """Encode one unchanged, module-issued CP65 record."""

    _validated, snapshot = _validate_public_record(record)
    return snapshot


def cp65_sha256(record: object) -> str:
    """Hash one validated CP65 record with its exact public type tag."""

    validated, snapshot = _validate_public_record(record)
    return hashlib.sha256(
        b"cp65-public-record-v1\0"
        + type(validated).__name__.encode("ascii")
        + b"\0"
        + snapshot
    ).hexdigest()


__all__ = (
    "CP65_TEST28_SCHEMA_VERSION",
    "CP65_TEST28_SCOPE",
    "CP65PredecessorCustodyV1",
    "CP65FieldRuleV1",
    "CP65ArtifactSchemaV1",
    "CP65TransientPathContractV1",
    "CP65DigestPreimageContractV1",
    "CP65Sha256PointerContractV1",
    "CP65PredicateContractV1",
    "CP65GateRequirementV1",
    "CP65AuxiliaryArtifactBoundV1",
    "CP65AuxiliarySizeProofV1",
    "CP65AuthorizationSignatureContractV1",
    "CP65SuppliedValidationV1",
    "CP65ProductionSchemaPreimageValidatorBundleV1",
    "cp65_production_schema_preimage_validator_bundle",
    "cp65_artifact_schema",
    "cp65_validate_supplied_artifact_bytes",
    "cp65_validate_supplied_artifact_set",
    "cp65_verify_launch_authorization_signature",
    "cp65_canonical_json_bytes",
    "cp65_sha256",
)
