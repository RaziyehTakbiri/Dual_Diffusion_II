"""Compose one live CP27 word capsule with the supplied-word CP43 map.

This additive adapter binds one exact checkpoint-43 owner and its transitive
checkpoint-37, checkpoint-36, and checkpoint-27 ancestry.  For one exact
``(run_id, initialization_index)`` request it allocates exactly one complete
checkpoint-27 rejection capsule, applies checkpoint 36's deep structural
preflight and custody snapshot, flattens the raw words in chronological entry
order, partitions them with checkpoint 43's exact split/join operations, and
invokes checkpoint 43's combined ``G``/``H`` entry point exactly once.

Adapter refusal and the semantic codomain are deliberately distinct.  Failure
while allocating, preflighting, partitioning, invoking checkpoint 43, or
retaining final custody produces no adapter result.  A refusal can occur before
the combined evaluation or after checkpoint 43 has evaluated but before CP44
returns; neither chronology is relabelled as checkpoint 43's symbolic
preparation-failure atom ``F36`` or quota-certification-failure atom ``F37``.
For every call that does return a CP44 result, checkpoint 43 alone determines
whether its retained semantic status is ``preparation_failure``,
``quota_certification_failure``, ``selected``, or ``exhausted``.

"One allocation" means one adapter-level invocation of the exact CP27
``allocate`` operation.  CP27 performs its own inherited deterministic
validation and stream replay inside that boundary.  CP44 adds no second source
allocation, source word request, caller RNG, or global RNG operation.

This module does not call checkpoint 36 ``prepare`` or checkpoint 37 ``decide``
and therefore does not claim equivalence to either legacy operational record.
It also makes no live Philox uniformity, independence, source-law,
initializer-distribution, portability, or cryptographic claim.  Hashes and
runtime identities are same-process procedural custody witnesses only.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import marshal
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure,
    )

    _closure = plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "factorized rejection execution requires the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-factorized-execution-"
    "adapter-v2"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_POLICY = (
    "exact-checkpoint43-owner-and-transitive-checkpoint27-36-37-41-42-ancestry;"
    "one-exact-checkpoint27-full-prefix-allocation-per-adapter-call;complete-"
    "CP36-layout-word-capsule-validation-before-factorized-execution;exact-CP43-"
    "V-W-coordinate-split-and-order;single-CP43-combined-G-then-semantic-H-"
    "evaluation;no-CP36-prepare-or-CP37-decide-invocation;no-second-source-"
    "allocation-extra-word-caller-global-RNG-retry-fallback-or-rollback;pre-"
    "combined-source-refusal-and-post-combined-exception-or-custody-refusal-"
    "remain-no-result-not-F36-or-F37;post-source-typed-F36-F37-selected-"
    "exhausted-semantics-inherited-from-CP43-for-returned-results;pointwise-"
    "returned-result-adapter-relation;abstract-supplied-product-uniform-"
    "semantic-map-corollary-only-under-fixed-runtime-deterministic-replay-"
    "stable-total-G43-typed-error-premise;new-factorized-operational-path-"
    "bypasses-but-does-not-prove-the-legacy-CP41-live-parent-premise-v2"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SCOPE = (
    "bounded-one-allocation-factorized-execution-adapter;for-exact-valid-r-j-"
    "and-a-returned-CP44-result-after-one-successful-validated-source-"
    "allocation-and-final-custody;one-full-interleaved-CP36-layout-word-capsule-"
    "split-into-V-and-W;pointwise-canonical-semantic-projection-equality-to-"
    "CP43-combined-semantics;typed-post-source-preparation-and-quota-failure-"
    "atoms;pre-or-post-combined-refusal-is-no-result-not-F36-or-F37;F37-is-"
    "bounded-quota-certification-failure-with-reachability-unresolved;abstract-"
    "supplied-word-product-uniform-semantic-map-pushforward-only-under-total-"
    "G43-premise;not-unconditional-return-after-successful-allocation-or-live-"
    "adapter-law;not-legacy-CP36-prepare-CP37-decide-failure-record-or-whole-"
    "record-equivalence;not-discharge-of-CP41-original-live-parent-"
    "factorization-hypothesis;not-live-Philox-uniformity-independence-freshness-"
    "or-randomness;not-numeric-fibers-source-or-refusal-masses-global-"
    "initializer-admission-path-or-sampler;not-scientific-model-quality-or-"
    "cross-domain-generality-evidence;trusted-runtime-procedural-not-portable-"
    "or-cryptographic-custody"
)

INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_STATUSES = ("acquired",)
INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SEMANTIC_STATUSES = (
    "preparation_failure",
    "quota_certification_failure",
    "selected",
    "exhausted",
)
INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_THEOREM = (
    "for-one-exact-valid-r-j-on-every-call-that-returns-a-CP44-result-after-the-"
    "single-inherited-CP27-allocation-returned-a-complete-validated-full-word-"
    "capsule-Z-in-D^(M+A)-and-final-structural-and-custody-checks-passed;with-"
    "split43(Z)=(V,W)-the-adapter-made-no-further-source-allocation-and-"
    "pi(T44_rj(Z))=pi(T43_rj(V,W))=pi(H43_sem(G43_rj(V),W));pre-combined-source-"
    "refusal-and-post-combined-exception-or-custody-refusal-produce-no-CP44-"
    "result-and-are-neither-F36-nor-F37;under-a-separate-fixed-runtime-"
    "deterministic-replay-stable-total-G43-typed-error-premise-and-abstract-"
    "product-uniform-law-on-Z-the-coordinate-split-makes-V-and-W-independent-"
    "product-uniform-and-the-induced-successful-source-semantic-map-has-the-"
    "CP41-form-with-G43-fibers;this-is-not-a-live-Philox-law-unconditional-"
    "adapter-law-or-legacy-CP36-37-equivalence"
)
INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_FAILURE_SEMANTICS = (
    "CP27-allocation-exceptions-propagate-unchanged-with-no-result;malformed-"
    "source-preflight-split-or-join-failure-refuses-before-the-CP43-combined-"
    "call;unexpected-CP43-exception-or-late-owner-dependency-source-custody-"
    "failure-refuses-after-source-acquisition-and-may-follow-CP43-evaluation;"
    "every-refusal-produces-no-CP44-result-is-neither-F36-nor-F37-and-has-no-"
    "retry-fallback-or-relabeling"
)
INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_PRODUCT_UNIFORM_COROLLARY = (
    "for-one-fixed-certified-owner-and-runtime-with-deterministic-replay-stable-"
    "total-G43-under-the-declared-typed-error-contract-and-exact-distinct-CP36-"
    "derived-coordinates;define-the-abstract-successful-source-semantic-map-"
    "S44_rj(Z)=T43_rj(split43(Z));if-an-abstract-supplied-full-word-capsule-Z-is-"
    "product-uniform-on-D^(M+A);then-split43-is-a-coordinate-permutation-so-V-"
    "and-W-are-independent-product-uniform;with-G43-fiber-masses-phi36-phi37-"
    "and-lambda_B-the-S44-pushforward-satisfies-Q44(F36)=phi36;Q44(F37)=phi37;"
    "Q44(E)=sum_B(lambda_B*e_B);Q44(x)=sum_B(lambda_B*m_B(x));no-operational-"
    "source-or-refusal-mass-numeric-fiber-or-mass-is-materialized-and-no-live-"
    "Philox-source-or-unconditional-adapter-law-follows"
)
INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_CP41_SYMBOLIC_MIXTURE = (
    "under-one-fixed-certified-owner-and-runtime-with-deterministic-replay-"
    "stable-total-G43-under-the-declared-typed-error-contract-a-separate-"
    "abstract-product-uniform-law-on-Z-and-the-CP44-CP43-factorization-by-"
    "construction-not-the-CP41-legacy-parent-factorization-premise;"
    "G43(V)=F36-or-F37-or-B;N36=card(G43^-1(F36));N37=card(G43^-1(F37));"
    "N_B=card(G43^-1(B));phi36=N36/D^M;phi37=N37/D^M;lambda_B=N_B/D^M;the-"
    "abstract-successful-source-semantic-map-S44-pushforward-has-Q44(F36)=phi36;"
    "Q44(F37)=phi37;Q44(E)=sum_B(lambda_B*e_B);Q44(x)=sum_B(lambda_B*m_B(x));"
    "CP41-form-symbolic-only-no-operational-source-or-refusal-mass-fibers-or-"
    "numeric-masses-materialized"
)

_SCHEMA_VERSION = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SCHEMA_VERSION
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_POLICY
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SCOPE
_THEOREM = INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_THEOREM
_SOURCE_FAILURE_SEMANTICS = (
    INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_FAILURE_SEMANTICS
)
_PRODUCT_UNIFORM_COROLLARY = (
    INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_PRODUCT_UNIFORM_COROLLARY
)
_CP41_SYMBOLIC_MIXTURE = (
    INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_CP41_SYMBOLIC_MIXTURE
)
_SOURCE_STATUSES = INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_STATUSES
_SEMANTIC_STATUSES = (
    INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SEMANTIC_STATUSES
)
_D = 1 << 64
_ZERO_SHA256 = "0" * 64

_factorization = _closure._factorization
_prep = _factorization._prep
_decision = _factorization._decision
_protocol = _prep._PROTOCOL

_CP43_OWNER_TYPE = _closure.CounterKeyedInitialTiltRejectionFactorizationClosureOwner
_CP43_CERT_TYPE = (
    _closure.CounterKeyedInitialTiltRejectionFactorizationClosureCertificate
)
_CP43_APPLIED_TYPE = (
    _closure.CounterKeyedInitialTiltRejectionFactorizationClosureAppliedDecision
)
_CP37_OWNER_TYPE = _factorization._CP37_OWNER_TYPE
_CP37_CERT_TYPE = _factorization._CP37_CERT_TYPE
_CP36_OWNER_TYPE = _factorization._CP36_OWNER_TYPE
_CP36_CERT_TYPE = _factorization._CP36_CERT_TYPE
_CP27_OWNER_TYPE = _prep._CP27_TYPE
_CP27_CERT_TYPE = _prep._CP27_CERT_TYPE
_CP27_RESULT_TYPE = _prep._CP27_RESULT_TYPE

_CP43_CERTIFICATE_PROPERTY = _CP43_OWNER_TYPE.certificate
_CP43_OWNER_SNAPSHOT = _CP43_OWNER_TYPE._owner_snapshot
_CP43_REQUIRE_OWNER_SNAPSHOT = _CP43_OWNER_TYPE._require_owner_snapshot
_CP43_SPLIT_FULL_WORDS = _CP43_OWNER_TYPE.split_full_words
_CP43_JOIN_FULL_WORDS = _CP43_OWNER_TYPE.join_full_words
_CP43_EVALUATE_AND_APPLY = _CP43_OWNER_TYPE.evaluate_and_apply
_CP43_VALIDATE_CERTIFICATE = _closure._validate_certificate
_CP43_VALIDATE_APPLIED_RECORD = _closure._validate_applied_record

_CP37_CERTIFICATE_PROPERTY = _CP37_OWNER_TYPE.certificate
_CP37_PARENT_PROPERTY = _CP37_OWNER_TYPE.preparation_owner
_CP37_OWNER_SNAPSHOT = _CP37_OWNER_TYPE._owner_snapshot
_CP37_REQUIRE_OWNER_SNAPSHOT = _CP37_OWNER_TYPE._require_owner_snapshot
_CP37_LIVE_CERTIFICATE = _CP37_OWNER_TYPE._live_certificate
_CP37_VALIDATE_CERTIFICATE = _decision._validate_certificate

_CP36_CERTIFICATE_PROPERTY = _CP36_OWNER_TYPE.certificate
_CP36_OWNER_SNAPSHOT = _CP36_OWNER_TYPE._owner_snapshot
_CP36_REQUIRE_OWNER_SNAPSHOT = _CP36_OWNER_TYPE._require_owner_snapshot
_CP36_LIVE_CERTIFICATE = _CP36_OWNER_TYPE._live_certificate
_CP36_VALIDATE_CERTIFICATE = _prep._validate_certificate
_CP36_PREFLIGHT_PROTOCOL_TREE = _prep._preflight_protocol_tree
_CP36_PROTOCOL_TREE_SNAPSHOT = _prep._protocol_tree_snapshot
_CP36_REQUIRE_PARENT_UNCHANGED = _prep._require_parent_unchanged

_CP27_CERTIFICATE_PROPERTY = _CP27_OWNER_TYPE.certificate
_CP27_LIVE = _CP27_OWNER_TYPE._require_live_binding
_CP27_ALLOCATE = _CP27_OWNER_TYPE.allocate
_CP27_VALIDATE_CERTIFICATE = _protocol._validate_certificate
_CP27_VALIDATE_RESULT_RECORD = _protocol._validate_result_record

_REQUIRE_SHA256 = _closure._REQUIRE_SHA256
_REQUIRE_TEXT = _closure._REQUIRE_TEXT
_EXACT_INTEGER = _closure._EXACT_INTEGER
_EXACT_WORDS = _closure._EXACT_WORDS
_EXACT_BOOL = _closure._EXACT_BOOL
_SEMANTIC_DIGEST = _closure._SEMANTIC_DIGEST

_CERTIFICATE_TOKEN = object()
_RESULT_TOKEN = object()
_TRUSTED_SOURCE_TOKEN = object()
_OWNER_TOKEN = object()


class PluginBridgeCounterKeyedInitialTiltRejectionFactorizedExecutionAdapterError(
    ArithmeticError
):
    """Raised when CP44 procedural custody changes during an operation."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


def _require_dependency_surfaces() -> None:
    module_expectations = (
        (_closure, "_validate_certificate", _CP43_VALIDATE_CERTIFICATE),
        (_closure, "_validate_applied_record", _CP43_VALIDATE_APPLIED_RECORD),
        (_decision, "_validate_certificate", _CP37_VALIDATE_CERTIFICATE),
        (_prep, "_validate_certificate", _CP36_VALIDATE_CERTIFICATE),
        (_prep, "_preflight_protocol_tree", _CP36_PREFLIGHT_PROTOCOL_TREE),
        (_prep, "_protocol_tree_snapshot", _CP36_PROTOCOL_TREE_SNAPSHOT),
        (_prep, "_require_parent_unchanged", _CP36_REQUIRE_PARENT_UNCHANGED),
        (_protocol, "_validate_certificate", _CP27_VALIDATE_CERTIFICATE),
        (_protocol, "_validate_result_record", _CP27_VALIDATE_RESULT_RECORD),
    )
    for module, name, expected in module_expectations:
        if not hasattr(module, name) or getattr(module, name) is not expected:
            raise ValueError("CP44 dependency surface changed: %s" % name)
    method_expectations = (
        (_CP43_OWNER_TYPE, "_owner_snapshot", _CP43_OWNER_SNAPSHOT),
        (
            _CP43_OWNER_TYPE,
            "_require_owner_snapshot",
            _CP43_REQUIRE_OWNER_SNAPSHOT,
        ),
        (_CP43_OWNER_TYPE, "split_full_words", _CP43_SPLIT_FULL_WORDS),
        (_CP43_OWNER_TYPE, "join_full_words", _CP43_JOIN_FULL_WORDS),
        (_CP43_OWNER_TYPE, "evaluate_and_apply", _CP43_EVALUATE_AND_APPLY),
        (_CP37_OWNER_TYPE, "_owner_snapshot", _CP37_OWNER_SNAPSHOT),
        (
            _CP37_OWNER_TYPE,
            "_require_owner_snapshot",
            _CP37_REQUIRE_OWNER_SNAPSHOT,
        ),
        (_CP37_OWNER_TYPE, "_live_certificate", _CP37_LIVE_CERTIFICATE),
        (_CP36_OWNER_TYPE, "_owner_snapshot", _CP36_OWNER_SNAPSHOT),
        (
            _CP36_OWNER_TYPE,
            "_require_owner_snapshot",
            _CP36_REQUIRE_OWNER_SNAPSHOT,
        ),
        (_CP36_OWNER_TYPE, "_live_certificate", _CP36_LIVE_CERTIFICATE),
        (_CP27_OWNER_TYPE, "_require_live_binding", _CP27_LIVE),
        (_CP27_OWNER_TYPE, "allocate", _CP27_ALLOCATE),
    )
    for owner_type, name, expected in method_expectations:
        if getattr(owner_type, name) is not expected:
            raise ValueError("CP44 parent method changed: %s" % name)
    property_expectations = (
        (_CP43_OWNER_TYPE, "certificate", _CP43_CERTIFICATE_PROPERTY),
        (_CP37_OWNER_TYPE, "certificate", _CP37_CERTIFICATE_PROPERTY),
        (_CP37_OWNER_TYPE, "preparation_owner", _CP37_PARENT_PROPERTY),
        (_CP36_OWNER_TYPE, "certificate", _CP36_CERTIFICATE_PROPERTY),
        (_CP27_OWNER_TYPE, "certificate", _CP27_CERTIFICATE_PROPERTY),
    )
    for owner_type, name, expected in property_expectations:
        if getattr(owner_type, name) is not expected:
            raise ValueError("CP44 parent property changed: %s" % name)


def _runtime_sha256() -> str:
    _require_dependency_surfaces()

    code_type = type(_runtime_sha256.__code__)

    def require_deterministic_constant_domain(value: object) -> None:
        value_type = type(value)
        if value_type in (type(None), bool, int, str):
            return
        if value_type is tuple:
            for item in value:
                require_deterministic_constant_domain(item)
            return
        if value_type is code_type:
            for item in value.co_consts:
                require_deterministic_constant_domain(item)
            return
        raise TypeError("CP44 runtime code constant has an unsupported exact type")

    def code_sha256(function: object) -> str:
        code = getattr(function, "__code__", None)
        if type(code) is not code_type:
            raise TypeError("CP44 runtime function has no exact Python code object")
        require_deterministic_constant_domain(code)
        return hashlib.sha256(marshal.dumps(code, 2)).hexdigest()

    owner_type = CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner
    return _SEMANTIC_DIGEST(
        {
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "theorem": _THEOREM,
            "source_failure_semantics": _SOURCE_FAILURE_SEMANTICS,
            "product_uniform_corollary": _PRODUCT_UNIFORM_COROLLARY,
            "cp41_symbolic_mixture": _CP41_SYMBOLIC_MIXTURE,
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "code_fingerprint_format": (
                "python-marshal-v2-no-reference-table-exact-constant-domain-v1"
            ),
            "cp27_allocate_code_sha256": code_sha256(_CP27_ALLOCATE),
            "cp27_structural_result_code_sha256": code_sha256(
                _CP27_VALIDATE_RESULT_RECORD
            ),
            "cp36_preflight_code_sha256": code_sha256(_CP36_PREFLIGHT_PROTOCOL_TREE),
            "cp36_snapshot_code_sha256": code_sha256(_CP36_PROTOCOL_TREE_SNAPSHOT),
            "cp36_custody_code_sha256": code_sha256(_CP36_REQUIRE_PARENT_UNCHANGED),
            "cp43_split_code_sha256": code_sha256(_CP43_SPLIT_FULL_WORDS),
            "cp43_join_code_sha256": code_sha256(_CP43_JOIN_FULL_WORDS),
            "cp43_combined_code_sha256": code_sha256(_CP43_EVALUATE_AND_APPLY),
            "cp44_bound_ancestry_code_sha256": code_sha256(_bound_ancestry),
            "cp44_flatten_words_code_sha256": code_sha256(_flatten_protocol_words),
            "cp44_partition_words_code_sha256": code_sha256(_partition_full_words),
            "cp44_semantic_projection_code_sha256": code_sha256(
                _canonical_semantic_projection
            ),
            "cp44_full_words_sha256_code_sha256": code_sha256(_full_words_sha256),
            "cp44_proposal_words_sha256_code_sha256": code_sha256(
                _proposal_words_sha256
            ),
            "cp44_decision_words_sha256_code_sha256": code_sha256(
                _decision_words_sha256
            ),
            "cp44_semantic_projection_sha256_code_sha256": code_sha256(
                _semantic_projection_sha256
            ),
            "cp44_validate_result_values_code_sha256": code_sha256(
                _validate_result_values
            ),
            "cp44_validate_result_record_code_sha256": code_sha256(
                _validate_result_record
            ),
            "cp44_make_result_code_sha256": code_sha256(_make_result),
            "cp44_require_record_unchanged_code_sha256": code_sha256(
                _require_record_unchanged
            ),
            "cp44_execute_code_sha256": code_sha256(owner_type.execute),
            "cp44_validate_result_code_sha256": code_sha256(owner_type.validate_result),
            "cp44_owner_snapshot_code_sha256": code_sha256(owner_type._owner_snapshot),
            "cp44_require_owner_snapshot_code_sha256": code_sha256(
                owner_type._require_owner_snapshot
            ),
        }
    )


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint43_owner_binding_certified",
    "exact_checkpoint42_41_hypothesis_binding_certified",
    "exact_transitive_checkpoint37_36_27_ancestry_certified",
    "single_complete_checkpoint27_capsule_allocation_certified",
    "no_second_source_allocation_certified",
    "no_adapter_added_source_word_or_caller_global_rng_call_certified",
    "exact_checkpoint36_rejection_layout_certified",
    "checkpoint36_deep_source_custody_certified",
    "checkpoint43_split_join_partition_certified",
    "source_acquisition_checks_precede_semantic_execution_certified",
    "post_combined_custody_checks_certified",
    "checkpoint43_combined_entrypoint_once_certified",
    "pointwise_returned_result_relation_certified",
    "canonical_semantic_projection_equality_certified",
    "all_quotas_before_comparisons_certified",
    "f37_without_semantic_w_interpretation_certified",
    "adapter_factorization_by_construction_certified",
    "legacy_checkpoint36_37_route_bypass_certified",
    "abstract_product_uniform_corollary_recorded_under_explicit_premises",
    "cp41_symbolic_mixture_recorded_under_explicit_premises",
    "structural_nonreplaying_result_validation_certified",
    "sealed_source_and_semantic_custody_certified",
    "adapter_refusal_distinct_from_f36_f37_certified",
    "source_word_retention_is_boundary_evidence_certified",
    "no_checkpoint36_prepare_or_checkpoint37_decide_certified",
    "construction_contract_enforced",
)

_CERTIFICATE_NEGATIVE_FLAGS = (
    "precombined_source_refusal_totalized",
    "postcombined_refusal_totalized",
    "successful_source_allocation_implies_return_certified",
    "unconditional_adapter_pushforward_certified",
    "inherited_cp27_internal_validation_replay_free",
    "generic_exception_totalization_certified",
    "semantic_no_w_access_before_g_at_adapter_level_certified",
    "checkpoint41_original_live_parent_factorization_discharged",
    "legacy_checkpoint36_prepare_equivalence_certified",
    "legacy_checkpoint37_decide_equivalence_certified",
    "legacy_checkpoint36_37_failure_equivalence_certified",
    "legacy_checkpoint36_37_execution_equivalence_certified",
    "whole_record_equivalence_certified",
    "live_philox_source_law_certified",
    "live_uniformity_independence_or_randomness_certified",
    "live_v_w_independence_certified",
    "live_word_freshness_certified",
    "concurrent_or_aba_external_record_mutation_resilience_certified",
    "natural_f37_failure_exhibited",
    "natural_f37_unreachability_proved",
    "adaptive_floor_separation_proved",
    "numeric_fibers_or_masses_materialized",
    "allocation_success_probability_certified",
    "source_failure_probability_certified",
    "retry_fallback_or_rollback_certified",
    "initializer_distribution_certified",
    "global_initializer_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "scientific_claim_promoted",
    "model_quality_claim_promoted",
    "generality_claim_promoted",
    "runtime_portable",
    "cryptographic_authentication",
    "loaded_code_integrity_certified",
)


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate:
    """Sealed CP43/CP27-bound factorized-execution certificate."""

    schema_version: str
    certificate_scope: str
    execution_policy: str
    execution_role_sha256: str
    checkpoint43_certificate: _CP43_CERT_TYPE
    checkpoint43_certificate_sha256: str
    checkpoint43_owner_runtime_identity: int
    checkpoint42_certificate_sha256: str
    checkpoint42_owner_runtime_identity: int
    checkpoint41_certificate_sha256: str
    checkpoint41_owner_runtime_identity: int
    factorization_hypothesis_sha256: str
    checkpoint37_certificate: _CP37_CERT_TYPE
    checkpoint37_certificate_sha256: str
    checkpoint37_owner_runtime_identity: int
    checkpoint36_certificate: _CP36_CERT_TYPE
    checkpoint36_certificate_sha256: str
    checkpoint36_owner_runtime_identity: int
    checkpoint27_certificate: _CP27_CERT_TYPE
    checkpoint27_certificate_sha256: str
    checkpoint27_owner_runtime_identity: int
    process_parameter_sha256: str
    attempt_budget: int
    blocks_per_attempt: int
    block_raw64_word_counts: Tuple[int, ...]
    total_stream_records: int
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    raw_word_domain_size: int
    full_coordinate_sha256: str
    proposal_coordinate_sha256: str
    decision_coordinate_sha256: str
    factorized_execution_theorem: str
    source_failure_semantics: str
    abstract_product_uniform_corollary: str
    cp41_symbolic_mixture: str
    execution_runtime_sha256: str
    exact_checkpoint43_owner_binding_certified: bool
    exact_checkpoint42_41_hypothesis_binding_certified: bool
    exact_transitive_checkpoint37_36_27_ancestry_certified: bool
    single_complete_checkpoint27_capsule_allocation_certified: bool
    no_second_source_allocation_certified: bool
    no_adapter_added_source_word_or_caller_global_rng_call_certified: bool
    exact_checkpoint36_rejection_layout_certified: bool
    checkpoint36_deep_source_custody_certified: bool
    checkpoint43_split_join_partition_certified: bool
    source_acquisition_checks_precede_semantic_execution_certified: bool
    post_combined_custody_checks_certified: bool
    checkpoint43_combined_entrypoint_once_certified: bool
    pointwise_returned_result_relation_certified: bool
    canonical_semantic_projection_equality_certified: bool
    all_quotas_before_comparisons_certified: bool
    f37_without_semantic_w_interpretation_certified: bool
    adapter_factorization_by_construction_certified: bool
    legacy_checkpoint36_37_route_bypass_certified: bool
    abstract_product_uniform_corollary_recorded_under_explicit_premises: bool
    cp41_symbolic_mixture_recorded_under_explicit_premises: bool
    structural_nonreplaying_result_validation_certified: bool
    sealed_source_and_semantic_custody_certified: bool
    adapter_refusal_distinct_from_f36_f37_certified: bool
    source_word_retention_is_boundary_evidence_certified: bool
    no_checkpoint36_prepare_or_checkpoint37_decide_certified: bool
    construction_contract_enforced: bool
    precombined_source_refusal_totalized: bool
    postcombined_refusal_totalized: bool
    successful_source_allocation_implies_return_certified: bool
    unconditional_adapter_pushforward_certified: bool
    inherited_cp27_internal_validation_replay_free: bool
    generic_exception_totalization_certified: bool
    semantic_no_w_access_before_g_at_adapter_level_certified: bool
    checkpoint41_original_live_parent_factorization_discharged: bool
    legacy_checkpoint36_prepare_equivalence_certified: bool
    legacy_checkpoint37_decide_equivalence_certified: bool
    legacy_checkpoint36_37_failure_equivalence_certified: bool
    legacy_checkpoint36_37_execution_equivalence_certified: bool
    whole_record_equivalence_certified: bool
    live_philox_source_law_certified: bool
    live_uniformity_independence_or_randomness_certified: bool
    live_v_w_independence_certified: bool
    live_word_freshness_certified: bool
    concurrent_or_aba_external_record_mutation_resilience_certified: bool
    natural_f37_failure_exhibited: bool
    natural_f37_unreachability_proved: bool
    adaptive_floor_separation_proved: bool
    numeric_fibers_or_masses_materialized: bool
    allocation_success_probability_certified: bool
    source_failure_probability_certified: bool
    retry_fallback_or_rollback_certified: bool
    initializer_distribution_certified: bool
    global_initializer_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    loaded_code_integrity_certified: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("factorized-execution certificates cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("factorized-execution certificates are sealed")
        if set(values) != set(self.__annotations__):
            raise TypeError("factorized-execution certificate is incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("factorized-execution certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate.__annotations__
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "checkpoint43_certificate",
        "checkpoint37_certificate",
        "checkpoint36_certificate",
        "checkpoint27_certificate",
        "certificate_sha256",
    )


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    for name, expected in (
        ("schema_version", _SCHEMA_VERSION),
        ("certificate_scope", _SCOPE),
        ("execution_policy", _POLICY),
        ("factorized_execution_theorem", _THEOREM),
        ("source_failure_semantics", _SOURCE_FAILURE_SEMANTICS),
        ("abstract_product_uniform_corollary", _PRODUCT_UNIFORM_COROLLARY),
        ("cp41_symbolic_mixture", _CP41_SYMBOLIC_MIXTURE),
    ):
        _REQUIRE_TEXT(values[name], expected, name="certificate." + name)
    _REQUIRE_SHA256(
        values["execution_role_sha256"],
        name="certificate.execution_role_sha256",
    )

    cp43 = values["checkpoint43_certificate"]
    if type(cp43) is not _CP43_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP43 parent type")
    if _CP43_VALIDATE_CERTIFICATE(cp43) is not cp43:
        raise ValueError("CP43 certificate validation substituted")
    cp42 = cp43.checkpoint42_certificate
    inherited_cp42_41 = (
        ("checkpoint42_certificate_sha256", cp42.certificate_sha256),
        ("checkpoint41_certificate_sha256", cp42.checkpoint41_certificate_sha256),
        ("factorization_hypothesis_sha256", cp42.factorization_hypothesis_sha256),
    )
    for name, expected in inherited_cp42_41:
        digest = _REQUIRE_SHA256(values[name], name="certificate." + name)
        if digest != expected:
            raise ValueError("certificate.%s differs from CP43/CP42" % name)
    inherited_owner_identities = (
        (
            "checkpoint42_owner_runtime_identity",
            cp43.checkpoint42_owner_runtime_identity,
        ),
        (
            "checkpoint41_owner_runtime_identity",
            cp42.checkpoint41_owner_runtime_identity,
        ),
        (
            "checkpoint37_owner_runtime_identity",
            cp42.checkpoint37_owner_runtime_identity,
        ),
        (
            "checkpoint36_owner_runtime_identity",
            cp42.checkpoint36_owner_runtime_identity,
        ),
    )
    for name, expected in inherited_owner_identities:
        if values[name] != expected:
            raise ValueError("certificate.%s differs from transitive ancestry" % name)

    cp37 = values["checkpoint37_certificate"]
    if type(cp37) is not _CP37_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP37 parent type")
    if _CP37_VALIDATE_CERTIFICATE(cp37) is not cp37:
        raise ValueError("CP37 certificate validation substituted")
    if cp37 is not cp42.checkpoint37_certificate:
        raise ValueError("certificate CP43-to-CP37 identity differs")

    cp36 = values["checkpoint36_certificate"]
    if type(cp36) is not _CP36_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP36 parent type")
    if _CP36_VALIDATE_CERTIFICATE(cp36) is not cp36:
        raise ValueError("CP36 certificate validation substituted")
    if cp36 is not cp42.checkpoint36_certificate:
        raise ValueError("certificate CP43-to-CP36 identity differs")
    if cp37.preparation_certificate is not cp36:
        raise ValueError("certificate CP37-to-CP36 identity differs")

    cp27 = values["checkpoint27_certificate"]
    if type(cp27) is not _CP27_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP27 parent type")
    if _CP27_VALIDATE_CERTIFICATE(cp27) is not cp27:
        raise ValueError("CP27 certificate validation substituted")
    if cp36.checkpoint27_certificate is not cp27:
        raise ValueError("certificate CP36-to-CP27 identity differs")

    inherited_digests = (
        ("checkpoint43_certificate_sha256", cp43.certificate_sha256),
        ("checkpoint37_certificate_sha256", cp37.certificate_sha256),
        ("checkpoint36_certificate_sha256", cp36.certificate_sha256),
        ("checkpoint27_certificate_sha256", cp27.certificate_sha256),
        ("process_parameter_sha256", cp43.process_parameter_sha256),
        ("full_coordinate_sha256", cp36.logical_word_coordinate_sha256),
        ("proposal_coordinate_sha256", cp43.proposal_coordinate_sha256),
        ("decision_coordinate_sha256", cp43.decision_coordinate_sha256),
    )
    for name, expected in inherited_digests:
        digest = _REQUIRE_SHA256(values[name], name="certificate." + name)
        if digest != expected:
            raise ValueError("certificate.%s differs from its ancestry" % name)
    if cp36.process_parameter_sha256 != values["process_parameter_sha256"]:
        raise ValueError("CP36 and CP43 process parameters differ")

    block_counts = values["block_raw64_word_counts"]
    if type(block_counts) is not tuple or not block_counts:
        raise TypeError("certificate block counts must be a nonempty exact tuple")
    for position, count in enumerate(block_counts):
        _EXACT_INTEGER(
            count,
            name="certificate.block_raw64_word_counts[%d]" % position,
            minimum=1,
            maximum=cp27.maximum_raw64_words_per_stream,
        )
    if block_counts != cp36.block_raw64_word_counts:
        raise ValueError("certificate block counts differ from CP36")
    if block_counts[-1] != 1:
        raise ValueError("certificate final rejection block is not one word")

    attempt_budget = _EXACT_INTEGER(
        values["attempt_budget"],
        name="certificate.attempt_budget",
        minimum=1,
        maximum=64,
    )
    expected_proposal = attempt_budget * sum(block_counts[:-1])
    expected_full = attempt_budget * sum(block_counts)
    expected_streams = attempt_budget * len(block_counts)
    expected_integers = (
        ("attempt_budget", cp36.attempt_budget),
        ("blocks_per_attempt", cp36.blocks_per_attempt),
        ("total_stream_records", cp36.total_stream_records),
        ("full_word_count", cp36.total_raw64_words),
        ("proposal_word_count", cp43.proposal_word_count),
        ("decision_word_count", cp43.decision_word_count),
        ("raw_word_domain_size", _D),
    )
    for name, expected in expected_integers:
        actual = _EXACT_INTEGER(
            values[name],
            name="certificate." + name,
            minimum=1,
            maximum=max(_D, cp36.total_raw64_words),
        )
        if actual != expected:
            raise ValueError("certificate.%s differs" % name)
    if values["blocks_per_attempt"] != len(block_counts):
        raise ValueError("certificate blocks-per-attempt differs from layout")
    if values["total_stream_records"] != expected_streams:
        raise ValueError("certificate stream count differs from layout")
    if values["full_word_count"] != expected_full:
        raise ValueError("certificate full-word count differs from layout")
    if values["proposal_word_count"] != expected_proposal:
        raise ValueError("certificate proposal-word count differs from layout")
    if values["decision_word_count"] != attempt_budget:
        raise ValueError("certificate decision-word count differs from budget")

    for name in (
        "checkpoint43_owner_runtime_identity",
        "checkpoint42_owner_runtime_identity",
        "checkpoint41_owner_runtime_identity",
        "checkpoint37_owner_runtime_identity",
        "checkpoint36_owner_runtime_identity",
        "checkpoint27_owner_runtime_identity",
    ):
        _EXACT_INTEGER(
            values[name],
            name="certificate." + name,
            minimum=1,
            maximum=(1 << 128) - 1,
        )
    if values["execution_runtime_sha256"] != _runtime_sha256():
        raise ValueError("certificate runtime digest differs")
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _EXACT_BOOL(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _EXACT_BOOL(values[name], False, name="certificate." + name)
    _REQUIRE_SHA256(values["certificate_sha256"], name="certificate.certificate_sha256")
    if values["certificate_sha256"] != _SEMANTIC_DIGEST(_certificate_payload(values)):
        raise ValueError("factorized-execution certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate
    ):
        raise TypeError("certificate has the wrong exact CP44 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _full_words_sha256(words: Tuple[int, ...]) -> str:
    return _SEMANTIC_DIGEST({"domain": "cp44-source-full-words-v1", "words": words})


def _proposal_words_sha256(words: Tuple[int, ...]) -> str:
    return _SEMANTIC_DIGEST({"domain": "cp44-source-proposal-words-v1", "words": words})


def _decision_words_sha256(words: Tuple[int, ...]) -> str:
    return _SEMANTIC_DIGEST({"domain": "cp44-source-decision-words-v1", "words": words})


def _flatten_protocol_words(source: _CP27_RESULT_TYPE) -> Tuple[int, ...]:
    return tuple(word for entry in source.entries for word in entry.raw64_words)


def _partition_full_words(
    full_words: Tuple[int, ...],
    certificate: CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate,
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    proposal = []
    decision = []
    cursor = 0
    block_counts = certificate.block_raw64_word_counts
    for _attempt_index in range(certificate.attempt_budget):
        for block_index, count in enumerate(block_counts):
            segment = full_words[cursor : cursor + count]
            if len(segment) != count:
                raise ValueError("CP44 full-word partition ended early")
            if block_index == len(block_counts) - 1:
                decision.extend(segment)
            else:
                proposal.extend(segment)
            cursor += count
    if cursor != len(full_words):
        raise ValueError("CP44 full-word partition did not consume its input")
    result = (tuple(proposal), tuple(decision))
    if len(result[0]) != certificate.proposal_word_count or (
        len(result[1]) != certificate.decision_word_count
    ):
        raise ValueError("CP44 full-word partition has the wrong shape")
    return result


def _canonical_semantic_projection(
    applied: _CP43_APPLIED_TYPE,
) -> Tuple[object, ...]:
    return (
        applied.status,
        applied.comparison_count,
        applied.selected_attempt_index,
        applied.selected_configuration_sha256,
    )


def _semantic_projection_sha256(projection: Tuple[object, ...]) -> str:
    return _SEMANTIC_DIGEST(
        {"domain": "cp44-canonical-semantic-projection-v1", "value": projection}
    )


def _require_callback_custody(callback: object | None) -> None:
    if callback is not None:
        if not callable(callback):
            raise TypeError("CP44 custody callback is not callable")
        callback()


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult:
    """One sealed successful-source acquisition and CP43 semantic result."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate
    certificate_sha256: str
    run_id: int
    initialization_index: int
    source_status: str
    source_protocol_result: _CP27_RESULT_TYPE
    source_protocol_result_sha256: str
    source_entry_sha256s: Tuple[str, ...]
    source_full_words: Tuple[int, ...]
    source_full_words_sha256: str
    source_proposal_words: Tuple[int, ...]
    source_proposal_words_sha256: str
    source_decision_words: Tuple[int, ...]
    source_decision_words_sha256: str
    checkpoint43_applied_decision: _CP43_APPLIED_TYPE
    checkpoint43_applied_decision_sha256: str
    semantic_status: str
    comparison_count: int
    selected_attempt_index: Optional[int]
    selected_configuration_sha256: Optional[str]
    canonical_semantic_projection: Tuple[object, ...]
    canonical_semantic_projection_sha256: str
    source_boundary_complete: bool
    complete_source_capsule_retained: bool
    full_word_partition_verified: bool
    checkpoint43_combined_evaluated_once: bool
    source_decision_words_are_boundary_evidence: bool
    source_failure_totalized_as_f36_or_f37: bool
    legacy_checkpoint36_or_checkpoint37_result_claimed: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("factorized-execution results cannot subclass")

    def __init__(
        self,
        *,
        _construction_token: object,
        _trusted_source_token: object,
        _trusted_certificate: Optional[
            CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate
        ] = None,
        _custody_check: object | None = None,
        **values: object,
    ) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("factorized-execution results are sealed")
        if _trusted_source_token is not _TRUSTED_SOURCE_TOKEN:
            raise TypeError("factorized-execution source fast path is sealed")
        if set(values) != set(self.__annotations__):
            raise TypeError("factorized-execution result is incomplete")
        _validate_result_values(
            values,
            trusted_certificate=_trusted_certificate,
            custody_check=_custody_check,
        )
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("factorized-execution results are not pickleable")


def _result_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult.__annotations__
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "source_protocol_result",
        "checkpoint43_applied_decision",
        "result_sha256",
    )


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate
    ] = None,
    custody_check: object | None = None,
) -> None:
    _REQUIRE_TEXT(values["schema_version"], _SCHEMA_VERSION, name="result.schema")
    certificate = values["certificate"]
    if trusted_certificate is None:
        checked_certificate = _validate_certificate(certificate)
    else:
        if certificate is not trusted_certificate:
            raise ValueError("CP44 result certificate identity differs")
        checked_certificate = trusted_certificate
    _require_callback_custody(custody_check)
    if values["certificate_sha256"] != checked_certificate.certificate_sha256:
        raise ValueError("CP44 result certificate digest differs")
    run_id = _EXACT_INTEGER(values["run_id"], name="result.run_id")
    initialization_index = _EXACT_INTEGER(
        values["initialization_index"], name="result.initialization_index"
    )
    _REQUIRE_TEXT(
        values["source_status"], _SOURCE_STATUSES[0], name="result.source_status"
    )

    source = values["source_protocol_result"]
    if type(source) is not _CP27_RESULT_TYPE:
        raise TypeError("CP44 source has the wrong exact CP27 result type")
    preflighted = _CP36_PREFLIGHT_PROTOCOL_TREE(
        source,
        certificate=checked_certificate.checkpoint36_certificate,
    )
    _require_callback_custody(custody_check)
    if preflighted is not source:
        raise ValueError("CP36 source preflight substituted its result")
    if source.certificate is not checked_certificate.checkpoint27_certificate:
        raise ValueError("CP44 source belongs to another CP27 certificate")
    if source.run_id != run_id or source.initialization_index != initialization_index:
        raise ValueError("CP44 source request coordinates differ")
    if (
        source.strategy != _protocol.INITIALIZER_STRATEGY_REJECTION
        or source.strategy_budget != checked_certificate.attempt_budget
        or source.work_item_raw64_word_counts
        != checked_certificate.block_raw64_word_counts
        or source.selection_raw64_word_count != 0
    ):
        raise ValueError("CP44 source rejection request differs")
    if source.stream_record_count != checked_certificate.total_stream_records or (
        source.total_raw64_words != checked_certificate.full_word_count
    ):
        raise ValueError("CP44 source capsule size differs")
    if values["source_protocol_result_sha256"] != source.result_sha256:
        raise ValueError("CP44 source-result digest differs")
    if values["source_entry_sha256s"] is not source.entry_sha256s:
        raise ValueError("CP44 source-entry digest tuple identity differs")

    full = _EXACT_WORDS(
        values["source_full_words"],
        name="result.source_full_words",
        length=checked_certificate.full_word_count,
    )
    if full is not values["source_full_words"]:
        raise ValueError("CP44 source full words are not canonical")
    if full != _flatten_protocol_words(source):
        raise ValueError("CP44 source full words differ from the capsule")
    if values["source_full_words_sha256"] != _full_words_sha256(full):
        raise ValueError("CP44 source full-word digest differs")

    proposal = _EXACT_WORDS(
        values["source_proposal_words"],
        name="result.source_proposal_words",
        length=checked_certificate.proposal_word_count,
    )
    decision = _EXACT_WORDS(
        values["source_decision_words"],
        name="result.source_decision_words",
        length=checked_certificate.decision_word_count,
    )
    expected_proposal, expected_decision = _partition_full_words(
        full, checked_certificate
    )
    if proposal != expected_proposal or decision != expected_decision:
        raise ValueError("CP44 retained V/W partition differs")
    if values["source_proposal_words_sha256"] != _proposal_words_sha256(proposal):
        raise ValueError("CP44 source proposal-word digest differs")
    if values["source_decision_words_sha256"] != _decision_words_sha256(decision):
        raise ValueError("CP44 source decision-word digest differs")
    _require_callback_custody(custody_check)

    applied = _CP43_VALIDATE_APPLIED_RECORD(
        values["checkpoint43_applied_decision"],
        trusted_certificate=checked_certificate.checkpoint43_certificate,
    )
    _require_callback_custody(custody_check)
    if (
        values["checkpoint43_applied_decision_sha256"]
        != applied.applied_decision_sha256
    ):
        raise ValueError("CP44 CP43 applied-decision digest differs")
    predecision = applied.predecision_result
    if predecision.run_id != run_id or (
        predecision.initialization_index != initialization_index
    ):
        raise ValueError("CP44 and CP43 request coordinates differ")
    if predecision.proposal_words != proposal:
        raise ValueError("CP44 source V differs from CP43 predecision V")
    status = values["semantic_status"]
    if type(status) is not str or status not in _SEMANTIC_STATUSES:
        raise ValueError("CP44 semantic status differs")
    if status != applied.status:
        raise ValueError("CP44 and CP43 semantic statuses differ")
    if status in ("selected", "exhausted"):
        if applied.decision_words != decision:
            raise ValueError("CP44 source W differs from CP43 decision W")
    elif applied.decision_words is not None:
        raise ValueError("CP43 F36/F37 must not retain semantic decision words")

    comparison_count = _EXACT_INTEGER(
        values["comparison_count"],
        name="result.comparison_count",
        maximum=checked_certificate.attempt_budget,
    )
    if comparison_count != applied.comparison_count:
        raise ValueError("CP44 comparison count differs from CP43")
    if values["selected_attempt_index"] != applied.selected_attempt_index:
        raise ValueError("CP44 selected index differs from CP43")
    if values["selected_configuration_sha256"] != applied.selected_configuration_sha256:
        raise ValueError("CP44 selected configuration digest differs from CP43")

    projection = values["canonical_semantic_projection"]
    if type(projection) is not tuple or len(projection) != 4:
        raise TypeError("CP44 semantic projection must be an exact four-tuple")
    expected_projection = _canonical_semantic_projection(applied)
    if projection != expected_projection:
        raise ValueError("CP44 canonical semantic projection differs")
    if values["canonical_semantic_projection_sha256"] != (
        _semantic_projection_sha256(projection)
    ):
        raise ValueError("CP44 canonical semantic-projection digest differs")

    for name, expected in (
        ("source_boundary_complete", True),
        ("complete_source_capsule_retained", True),
        ("full_word_partition_verified", True),
        ("checkpoint43_combined_evaluated_once", True),
        ("source_decision_words_are_boundary_evidence", True),
        ("source_failure_totalized_as_f36_or_f37", False),
        ("legacy_checkpoint36_or_checkpoint37_result_claimed", False),
    ):
        _EXACT_BOOL(values[name], expected, name="result." + name)
    _REQUIRE_SHA256(values["result_sha256"], name="result.result_sha256")
    if values["result_sha256"] != _SEMANTIC_DIGEST(_result_payload(values)):
        raise ValueError("factorized-execution result digest differs")
    _require_callback_custody(custody_check)


def _validate_result_record(
    result: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate
    ] = None,
    custody_check: object | None = None,
) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult:
    if (
        type(result)
        is not CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult
    ):
        raise TypeError("result has the wrong exact CP44 type")
    _validate_result_values(
        {name: getattr(result, name) for name in _result_fields()},
        trusted_certificate=trusted_certificate,
        custody_check=custody_check,
    )
    return result


def _bound_ancestry(closure_owner: object) -> Tuple[object, ...]:
    """Resolve and custody-check the exact CP43->CP37->CP36->CP27 chain."""

    _require_dependency_surfaces()
    if type(closure_owner) is not _CP43_OWNER_TYPE:
        raise TypeError("factorization_closure_owner has the wrong exact CP43 type")
    cp43_snapshot = _CP43_OWNER_SNAPSHOT(closure_owner)
    cp43_certificate = _CP43_VALIDATE_CERTIFICATE(
        _CP43_CERTIFICATE_PROPERTY.__get__(closure_owner, _CP43_OWNER_TYPE)
    )
    _CP43_REQUIRE_OWNER_SNAPSHOT(closure_owner, cp43_snapshot)

    decision_owner = closure_owner._decision_owner
    if type(decision_owner) is not _CP37_OWNER_TYPE:
        raise TypeError("CP43 exposes the wrong exact CP37 owner")
    decision_snapshot = _CP37_OWNER_SNAPSHOT(decision_owner)
    decision_certificate = _CP37_LIVE_CERTIFICATE(decision_owner, decision_snapshot)
    _CP37_REQUIRE_OWNER_SNAPSHOT(decision_owner, decision_snapshot)
    cp42_certificate = cp43_certificate.checkpoint42_certificate
    if decision_certificate is not cp42_certificate.checkpoint37_certificate:
        raise ValueError("CP43-to-CP37 live certificate identity differs")

    preparation_owner = _CP37_PARENT_PROPERTY.__get__(decision_owner, _CP37_OWNER_TYPE)
    if type(preparation_owner) is not _CP36_OWNER_TYPE:
        raise TypeError("CP37 exposes the wrong exact CP36 owner")
    preparation_snapshot = _CP36_OWNER_SNAPSHOT(preparation_owner)
    preparation_certificate = _CP36_LIVE_CERTIFICATE(
        preparation_owner, preparation_snapshot
    )
    _CP36_REQUIRE_OWNER_SNAPSHOT(preparation_owner, preparation_snapshot)
    if preparation_certificate is not cp42_certificate.checkpoint36_certificate:
        raise ValueError("CP43-to-CP36 live certificate identity differs")
    if decision_certificate.preparation_certificate is not preparation_certificate:
        raise ValueError("CP37-to-CP36 live certificate identity differs")

    protocol_owner = preparation_owner._protocol_owner
    if type(protocol_owner) is not _CP27_OWNER_TYPE:
        raise TypeError("CP36 exposes the wrong exact CP27 owner")
    protocol_certificate = _CP27_LIVE(protocol_owner)
    if protocol_certificate is not preparation_certificate.checkpoint27_certificate:
        raise ValueError("CP36-to-CP27 live certificate identity differs")
    if (
        _CP27_CERTIFICATE_PROPERTY.__get__(protocol_owner, _CP27_OWNER_TYPE)
        is not protocol_certificate
    ):
        raise ValueError("CP27 certificate property identity differs")

    _CP43_REQUIRE_OWNER_SNAPSHOT(closure_owner, cp43_snapshot)
    _CP37_REQUIRE_OWNER_SNAPSHOT(decision_owner, decision_snapshot)
    _CP36_REQUIRE_OWNER_SNAPSHOT(preparation_owner, preparation_snapshot)
    if _CP27_LIVE(protocol_owner) is not protocol_certificate:
        raise ValueError("CP27 live certificate identity changed")
    return (
        decision_owner,
        preparation_owner,
        protocol_owner,
        cp43_certificate,
        decision_certificate,
        preparation_certificate,
        protocol_certificate,
        cp43_snapshot,
        decision_snapshot,
        preparation_snapshot,
    )


def _make_certificate(
    closure_owner: _CP43_OWNER_TYPE,
    ancestry: Tuple[object, ...],
    role: str,
) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate:
    (
        decision_owner,
        preparation_owner,
        protocol_owner,
        cp43,
        cp37,
        cp36,
        cp27,
        cp43_snapshot,
        decision_snapshot,
        preparation_snapshot,
    ) = ancestry
    _CP43_REQUIRE_OWNER_SNAPSHOT(closure_owner, cp43_snapshot)
    _CP37_REQUIRE_OWNER_SNAPSHOT(decision_owner, decision_snapshot)
    _CP36_REQUIRE_OWNER_SNAPSHOT(preparation_owner, preparation_snapshot)
    if _CP27_LIVE(protocol_owner) is not cp27:
        raise ValueError("CP27 certificate changed during CP44 certification")
    cp42 = cp43.checkpoint42_certificate
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "execution_policy": _POLICY,
        "execution_role_sha256": role,
        "checkpoint43_certificate": cp43,
        "checkpoint43_certificate_sha256": cp43.certificate_sha256,
        "checkpoint43_owner_runtime_identity": id(closure_owner),
        "checkpoint42_certificate_sha256": cp42.certificate_sha256,
        "checkpoint42_owner_runtime_identity": (
            cp43.checkpoint42_owner_runtime_identity
        ),
        "checkpoint41_certificate_sha256": cp42.checkpoint41_certificate_sha256,
        "checkpoint41_owner_runtime_identity": cp42.checkpoint41_owner_runtime_identity,
        "factorization_hypothesis_sha256": cp42.factorization_hypothesis_sha256,
        "checkpoint37_certificate": cp37,
        "checkpoint37_certificate_sha256": cp37.certificate_sha256,
        "checkpoint37_owner_runtime_identity": id(decision_owner),
        "checkpoint36_certificate": cp36,
        "checkpoint36_certificate_sha256": cp36.certificate_sha256,
        "checkpoint36_owner_runtime_identity": id(preparation_owner),
        "checkpoint27_certificate": cp27,
        "checkpoint27_certificate_sha256": cp27.certificate_sha256,
        "checkpoint27_owner_runtime_identity": id(protocol_owner),
        "process_parameter_sha256": cp43.process_parameter_sha256,
        "attempt_budget": cp36.attempt_budget,
        "blocks_per_attempt": cp36.blocks_per_attempt,
        "block_raw64_word_counts": cp36.block_raw64_word_counts,
        "total_stream_records": cp36.total_stream_records,
        "full_word_count": cp36.total_raw64_words,
        "proposal_word_count": cp43.proposal_word_count,
        "decision_word_count": cp43.decision_word_count,
        "raw_word_domain_size": _D,
        "full_coordinate_sha256": cp36.logical_word_coordinate_sha256,
        "proposal_coordinate_sha256": cp43.proposal_coordinate_sha256,
        "decision_coordinate_sha256": cp43.decision_coordinate_sha256,
        "factorized_execution_theorem": _THEOREM,
        "source_failure_semantics": _SOURCE_FAILURE_SEMANTICS,
        "abstract_product_uniform_corollary": _PRODUCT_UNIFORM_COROLLARY,
        "cp41_symbolic_mixture": _CP41_SYMBOLIC_MIXTURE,
        "execution_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_POSITIVE_FLAGS},
        **{name: False for name in _CERTIFICATE_NEGATIVE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _SEMANTIC_DIGEST(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


def _record_snapshot(record: object, fields: Tuple[str, ...]) -> Tuple[object, ...]:
    return tuple(getattr(record, name) for name in fields)


def _require_record_unchanged(
    record: object,
    fields: Tuple[str, ...],
    before: Tuple[object, ...],
    *,
    name: str,
) -> None:
    if type(before) is not tuple or len(before) != len(fields):
        raise TypeError("%s snapshot is malformed" % name)
    after = _record_snapshot(record, fields)
    if any(current is not previous for current, previous in zip(after, before)):
        raise PluginBridgeCounterKeyedInitialTiltRejectionFactorizedExecutionAdapterError(
            "%s changed during operation" % name
        )


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate,
    source: _CP27_RESULT_TYPE,
    full_words: Tuple[int, ...],
    proposal_words: Tuple[int, ...],
    decision_words: Tuple[int, ...],
    applied: _CP43_APPLIED_TYPE,
    *,
    custody_check: object,
) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult:
    projection = _canonical_semantic_projection(applied)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": source.run_id,
        "initialization_index": source.initialization_index,
        "source_status": "acquired",
        "source_protocol_result": source,
        "source_protocol_result_sha256": source.result_sha256,
        "source_entry_sha256s": source.entry_sha256s,
        "source_full_words": full_words,
        "source_full_words_sha256": _full_words_sha256(full_words),
        "source_proposal_words": proposal_words,
        "source_proposal_words_sha256": _proposal_words_sha256(proposal_words),
        "source_decision_words": decision_words,
        "source_decision_words_sha256": _decision_words_sha256(decision_words),
        "checkpoint43_applied_decision": applied,
        "checkpoint43_applied_decision_sha256": applied.applied_decision_sha256,
        "semantic_status": applied.status,
        "comparison_count": applied.comparison_count,
        "selected_attempt_index": applied.selected_attempt_index,
        "selected_configuration_sha256": applied.selected_configuration_sha256,
        "canonical_semantic_projection": projection,
        "canonical_semantic_projection_sha256": (
            _semantic_projection_sha256(projection)
        ),
        "source_boundary_complete": True,
        "complete_source_capsule_retained": True,
        "full_word_partition_verified": True,
        "checkpoint43_combined_evaluated_once": True,
        "source_decision_words_are_boundary_evidence": True,
        "source_failure_totalized_as_f36_or_f37": False,
        "legacy_checkpoint36_or_checkpoint37_result_claimed": False,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _SEMANTIC_DIGEST(_result_payload(values))
    result = CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult(
        _construction_token=_RESULT_TOKEN,
        _trusted_source_token=_TRUSTED_SOURCE_TOKEN,
        _trusted_certificate=certificate,
        _custody_check=custody_check,
        **values,
    )
    _require_callback_custody(custody_check)
    return result


class CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner:
    """Immutable owner of one CP27-source-backed CP43 execution adapter."""

    __slots__ = (
        "_factorization_closure_owner",
        "_factorization_closure_owner_identity",
        "_decision_owner",
        "_decision_owner_identity",
        "_preparation_owner",
        "_preparation_owner_identity",
        "_protocol_owner",
        "_protocol_owner_identity",
        "_execution_policy",
        "_execution_policy_identity",
        "_execution_role_sha256",
        "_execution_role_sha256_identity",
        "_certificate",
        "_certificate_identity",
        "_certificate_snapshot",
        "_certificate_snapshot_identity",
        "_protocol_allocate",
        "_validate_protocol_result_record",
        "_preflight_protocol_tree",
        "_protocol_tree_snapshot",
        "_require_parent_unchanged",
        "_split_full_words",
        "_join_full_words",
        "_evaluate_and_apply",
        "_validate_applied_record",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("factorized-execution adapter owners cannot subclass")

    def __init__(
        self,
        factorization_closure_owner: _CP43_OWNER_TYPE,
        decision_owner: _CP37_OWNER_TYPE,
        preparation_owner: _CP36_OWNER_TYPE,
        protocol_owner: _CP27_OWNER_TYPE,
        execution_policy: str,
        execution_role_sha256: str,
        certificate: CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("factorized-execution adapter owners require certification")
        if type(factorization_closure_owner) is not _CP43_OWNER_TYPE:
            raise TypeError("factorization_closure_owner has the wrong CP43 type")
        if type(decision_owner) is not _CP37_OWNER_TYPE:
            raise TypeError("decision_owner has the wrong CP37 type")
        if type(preparation_owner) is not _CP36_OWNER_TYPE:
            raise TypeError("preparation_owner has the wrong CP36 type")
        if type(protocol_owner) is not _CP27_OWNER_TYPE:
            raise TypeError("protocol_owner has the wrong CP27 type")
        policy = _REQUIRE_TEXT(execution_policy, _POLICY, name="execution_policy")
        role = _REQUIRE_SHA256(execution_role_sha256, name="execution_role_sha256")
        checked = _validate_certificate(certificate)
        if checked.execution_role_sha256 != role:
            raise ValueError("CP44 certificate role differs")
        identities = (
            (
                "CP43",
                checked.checkpoint43_owner_runtime_identity,
                id(factorization_closure_owner),
            ),
            ("CP37", checked.checkpoint37_owner_runtime_identity, id(decision_owner)),
            (
                "CP36",
                checked.checkpoint36_owner_runtime_identity,
                id(preparation_owner),
            ),
            ("CP27", checked.checkpoint27_owner_runtime_identity, id(protocol_owner)),
        )
        for name, expected, actual in identities:
            if expected != actual:
                raise ValueError("CP44 certificate %s owner identity differs" % name)
        if factorization_closure_owner._decision_owner is not decision_owner:
            raise ValueError("CP44 CP43-to-CP37 owner ancestry differs")
        if (
            _CP37_PARENT_PROPERTY.__get__(decision_owner, _CP37_OWNER_TYPE)
            is not preparation_owner
        ):
            raise ValueError("CP44 CP37-to-CP36 owner ancestry differs")
        if preparation_owner._protocol_owner is not protocol_owner:
            raise ValueError("CP44 CP36-to-CP27 owner ancestry differs")
        certificate_snapshot = tuple(
            getattr(checked, name) for name in _certificate_fields()
        )
        bindings = (
            ("_factorization_closure_owner", factorization_closure_owner),
            (
                "_factorization_closure_owner_identity",
                factorization_closure_owner,
            ),
            ("_decision_owner", decision_owner),
            ("_decision_owner_identity", decision_owner),
            ("_preparation_owner", preparation_owner),
            ("_preparation_owner_identity", preparation_owner),
            ("_protocol_owner", protocol_owner),
            ("_protocol_owner_identity", protocol_owner),
            ("_execution_policy", policy),
            ("_execution_policy_identity", policy),
            ("_execution_role_sha256", role),
            ("_execution_role_sha256_identity", role),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_certificate_snapshot", certificate_snapshot),
            ("_certificate_snapshot_identity", certificate_snapshot),
            ("_protocol_allocate", _CP27_ALLOCATE),
            ("_validate_protocol_result_record", _CP27_VALIDATE_RESULT_RECORD),
            ("_preflight_protocol_tree", _CP36_PREFLIGHT_PROTOCOL_TREE),
            ("_protocol_tree_snapshot", _CP36_PROTOCOL_TREE_SNAPSHOT),
            ("_require_parent_unchanged", _CP36_REQUIRE_PARENT_UNCHANGED),
            ("_split_full_words", _CP43_SPLIT_FULL_WORDS),
            ("_join_full_words", _CP43_JOIN_FULL_WORDS),
            ("_evaluate_and_apply", _CP43_EVALUATE_AND_APPLY),
            ("_validate_applied_record", _CP43_VALIDATE_APPLIED_RECORD),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("factorized-execution adapter owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("factorized-execution adapter owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("factorized-execution adapter owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate:
        return self._certificate

    @property
    def factorization_closure_owner(self) -> _CP43_OWNER_TYPE:
        return self._factorization_closure_owner

    def _owner_snapshot(self) -> Tuple[object, ...]:
        _require_dependency_surfaces()
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("CP44 owner seal differs")
        checked = _validate_certificate(self._certificate)
        if checked is not self._certificate_identity:
            raise ValueError("CP44 live certificate identity differs")
        current = (
            self._factorization_closure_owner,
            self._decision_owner,
            self._preparation_owner,
            self._protocol_owner,
            self._execution_policy,
            self._execution_role_sha256,
            self._certificate,
            self._certificate_snapshot,
        )
        frozen = (
            self._factorization_closure_owner_identity,
            self._decision_owner_identity,
            self._preparation_owner_identity,
            self._protocol_owner_identity,
            self._execution_policy_identity,
            self._execution_role_sha256_identity,
            self._certificate_identity,
            self._certificate_snapshot_identity,
        )
        if any(actual is not expected for actual, expected in zip(current, frozen)):
            raise ValueError("factorized-execution adapter owner identity changed")
        if tuple(getattr(checked, name) for name in _certificate_fields()) != (
            self._certificate_snapshot
        ):
            raise ValueError("factorized-execution adapter certificate changed")
        callbacks = (
            (self._protocol_allocate, _CP27_ALLOCATE),
            (
                self._validate_protocol_result_record,
                _CP27_VALIDATE_RESULT_RECORD,
            ),
            (self._preflight_protocol_tree, _CP36_PREFLIGHT_PROTOCOL_TREE),
            (self._protocol_tree_snapshot, _CP36_PROTOCOL_TREE_SNAPSHOT),
            (self._require_parent_unchanged, _CP36_REQUIRE_PARENT_UNCHANGED),
            (self._split_full_words, _CP43_SPLIT_FULL_WORDS),
            (self._join_full_words, _CP43_JOIN_FULL_WORDS),
            (self._evaluate_and_apply, _CP43_EVALUATE_AND_APPLY),
            (self._validate_applied_record, _CP43_VALIDATE_APPLIED_RECORD),
        )
        if any(actual is not expected for actual, expected in callbacks):
            raise ValueError("factorized-execution adapter cached callback changed")
        ancestry = _bound_ancestry(self._factorization_closure_owner)
        if ancestry[0] is not self._decision_owner:
            raise ValueError("CP44 live CP37 owner identity differs")
        if ancestry[1] is not self._preparation_owner:
            raise ValueError("CP44 live CP36 owner identity differs")
        if ancestry[2] is not self._protocol_owner:
            raise ValueError("CP44 live CP27 owner identity differs")
        if ancestry[3] is not checked.checkpoint43_certificate:
            raise ValueError("CP44 live CP43 certificate identity differs")
        if ancestry[4] is not checked.checkpoint37_certificate:
            raise ValueError("CP44 live CP37 certificate identity differs")
        if ancestry[5] is not checked.checkpoint36_certificate:
            raise ValueError("CP44 live CP36 certificate identity differs")
        if ancestry[6] is not checked.checkpoint27_certificate:
            raise ValueError("CP44 live CP27 certificate identity differs")
        return current + (ancestry[7], ancestry[8], ancestry[9], ancestry[6])

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 12:
            raise TypeError("CP44 owner snapshot is malformed")
        current = self._owner_snapshot()
        if any(
            actual is not expected
            for actual, expected in zip(current[:8], snapshot[:8])
        ):
            raise PluginBridgeCounterKeyedInitialTiltRejectionFactorizedExecutionAdapterError(
                "factorized-execution adapter owner changed during operation"
            )
        _CP43_REQUIRE_OWNER_SNAPSHOT(self._factorization_closure_owner, snapshot[8])
        _CP37_REQUIRE_OWNER_SNAPSHOT(self._decision_owner, snapshot[9])
        _CP36_REQUIRE_OWNER_SNAPSHOT(self._preparation_owner, snapshot[10])
        if _CP27_LIVE(self._protocol_owner) is not snapshot[11]:
            raise PluginBridgeCounterKeyedInitialTiltRejectionFactorizedExecutionAdapterError(
                "CP27 owner changed during factorized execution"
            )

    def execute(
        self,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult:
        """Allocate one source capsule and apply CP43's combined map once."""

        checked_run = _EXACT_INTEGER(run_id, name="run_id")
        checked_initialization = _EXACT_INTEGER(
            initialization_index, name="initialization_index"
        )
        owner_snapshot = self._owner_snapshot()
        certificate = self._certificate

        source = self._protocol_allocate(
            self._protocol_owner,
            checked_run,
            checked_initialization,
            strategy=_protocol.INITIALIZER_STRATEGY_REJECTION,
            strategy_budget=certificate.attempt_budget,
            work_item_raw64_word_counts=certificate.block_raw64_word_counts,
            selection_raw64_word_count=0,
        )
        self._require_owner_snapshot(owner_snapshot)
        checked_source = self._preflight_protocol_tree(
            source,
            certificate=certificate.checkpoint36_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        if checked_source is not source:
            raise ValueError("CP36 source preflight substituted its result")
        source_snapshot = self._protocol_tree_snapshot(source)

        def require_source_custody() -> None:
            self._require_parent_unchanged(source, source_snapshot)
            self._require_owner_snapshot(owner_snapshot)

        require_source_custody()
        full_words = _flatten_protocol_words(source)
        full_words = _EXACT_WORDS(
            full_words,
            name="source_full_words",
            length=certificate.full_word_count,
        )
        require_source_custody()
        split = self._split_full_words(self._factorization_closure_owner, full_words)
        require_source_custody()
        if type(split) is not tuple or len(split) != 2:
            raise TypeError("CP43 split returned the wrong exact pair")
        proposal_words, decision_words = split
        expected_partition = _partition_full_words(full_words, certificate)
        if split != expected_partition:
            raise ValueError("CP43 split differs from the CP36 layout partition")
        joined = self._join_full_words(
            self._factorization_closure_owner,
            proposal_words,
            decision_words,
        )
        require_source_custody()
        if joined != full_words:
            raise ValueError("CP43 split/join round trip differs from the source")

        applied = self._evaluate_and_apply(
            self._factorization_closure_owner,
            checked_run,
            checked_initialization,
            proposal_words,
            decision_words,
        )
        require_source_custody()
        checked_applied = self._validate_applied_record(
            applied,
            trusted_certificate=certificate.checkpoint43_certificate,
        )
        require_source_custody()
        if checked_applied is not applied:
            raise ValueError("CP43 structural validation substituted its result")
        if applied.predecision_result.proposal_words != proposal_words:
            raise ValueError("CP43 returned a different proposal-word tuple")
        if applied.status in ("selected", "exhausted"):
            if applied.decision_words != decision_words:
                raise ValueError("CP43 returned a different decision-word tuple")
        elif applied.decision_words is not None:
            raise ValueError("CP43 F36/F37 retained semantic decision words")

        result = _make_result(
            certificate,
            source,
            full_words,
            proposal_words,
            decision_words,
            applied,
            custody_check=require_source_custody,
        )
        require_source_custody()
        return result

    def validate_result(
        self,
        result: object,
    ) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult:
        """Structurally validate retained source and CP43 records without replay."""

        if (
            type(result)
            is not CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult
        ):
            raise TypeError("result has the wrong exact CP44 type")
        owner_snapshot = self._owner_snapshot()
        source = result.source_protocol_result
        self._preflight_protocol_tree(
            source,
            certificate=self._certificate.checkpoint36_certificate,
        )
        source_snapshot = self._protocol_tree_snapshot(source)
        result_fields = _result_fields()
        result_snapshot = _record_snapshot(result, result_fields)
        applied = result.checkpoint43_applied_decision
        applied_fields = tuple(_CP43_APPLIED_TYPE.__annotations__)
        applied_snapshot = _record_snapshot(applied, applied_fields)
        predecision = applied.predecision_result
        predecision_fields = tuple(type(predecision).__annotations__)
        predecision_snapshot = _record_snapshot(predecision, predecision_fields)

        def require_result_custody() -> None:
            self._require_parent_unchanged(source, source_snapshot)
            _require_record_unchanged(
                result,
                result_fields,
                result_snapshot,
                name="CP44 result",
            )
            _require_record_unchanged(
                applied,
                applied_fields,
                applied_snapshot,
                name="CP43 applied result",
            )
            _require_record_unchanged(
                predecision,
                predecision_fields,
                predecision_snapshot,
                name="CP43 predecision result",
            )
            self._require_owner_snapshot(owner_snapshot)

        require_result_custody()
        checked_source = self._validate_protocol_result_record(source)
        require_result_custody()
        if checked_source is not source:
            raise ValueError("CP27 structural validation substituted its result")
        checked = _validate_result_record(
            result,
            trusted_certificate=self._certificate,
            custody_check=require_result_custody,
        )
        if checked is not result:
            raise ValueError("CP44 structural validation substituted its result")
        require_result_custody()
        return result


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter(
    factorization_closure_owner: object,
    *,
    execution_policy: object,
    execution_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner:
    """Certify one exact CP43/CP27 factorized-execution adapter."""

    if type(factorization_closure_owner) is not _CP43_OWNER_TYPE:
        raise TypeError("factorization_closure_owner has the wrong exact CP43 type")
    policy = _REQUIRE_TEXT(execution_policy, _POLICY, name="execution_policy")
    role = _REQUIRE_SHA256(execution_role_sha256, name="execution_role_sha256")
    ancestry = _bound_ancestry(factorization_closure_owner)
    certificate = _make_certificate(
        factorization_closure_owner,
        ancestry,
        role,
    )
    owner = CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner(
        factorization_closure_owner,
        ancestry[0],
        ancestry[1],
        ancestry[2],
        policy,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._owner_snapshot()
    return owner


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter(
    factorization_closure_owner: object,
    owner: object,
    *,
    execution_policy: object,
    execution_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner:
    if type(factorization_closure_owner) is not _CP43_OWNER_TYPE:
        raise TypeError("factorization_closure_owner has the wrong exact CP43 type")
    if (
        type(owner)
        is not CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner
    ):
        raise TypeError("owner has the wrong exact CP44 type")
    policy = _REQUIRE_TEXT(execution_policy, _POLICY, name="execution_policy")
    role = _REQUIRE_SHA256(execution_role_sha256, name="execution_role_sha256")
    snapshot = owner._owner_snapshot()
    if owner.factorization_closure_owner is not factorization_closure_owner:
        raise ValueError("CP44 owner belongs to another CP43 parent")
    if owner._execution_policy != policy or owner._execution_role_sha256 != role:
        raise ValueError("CP44 owner policy or role differs")
    owner._require_owner_snapshot(snapshot)
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter_certificate(
    factorization_closure_owner: object,
    owner: object,
    *,
    execution_policy: object,
    execution_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate:
    matching = require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter
    return matching(
        factorization_closure_owner,
        owner,
        execution_policy=execution_policy,
        execution_role_sha256=execution_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_"
    "ADAPTER_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_"
    "ADAPTER_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_"
    "ADAPTER_SCOPE",
    "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_STATUSES",
    "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SEMANTIC_STATUSES",
    "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_THEOREM",
    "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_FAILURE_SEMANTICS",
    "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_PRODUCT_UNIFORM_COROLLARY",
    "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_CP41_SYMBOLIC_MIXTURE",
    "CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate",
    "CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult",
    "CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionFactorizedExecutionAdapterError",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorized_execution_adapter",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorized_execution_adapter",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorized_execution_adapter_certificate",
]
