"""Definition-only whole-seed pushforward contract for Formal Test 28.

CP60 takes the correlated alternative left open by CP59.  It states a theorem
template for any *future* fully bound stochastic request ``R`` and runtime
environment ``E``.  Only after those objects exist may ``K_R,E(s)`` denote the
current kernel-v2 execution after inserting the uint64 plan seed ``s`` and may
its mathematical totalization ``F_R,E(s)`` retain a validated returned trace,
a pre-execution refusal, an execution failure, or nonreturn.  Under the
explicit *assumption* that the plan seed is uniform on the complete uint64
domain, probabilities would then be exact seed-fiber counts divided by
``2**64``.

The bundled fixture/strategy/budget rows are prospective grid templates.  Their
hashes do not fully bind ``R`` or ``E``, instantiate ``F_R,E``, or identify a
unique probability law.

This is a definition, not an operational prediction.  It neither executes nor
imports the kernel, NumPy, SciPy, a score provider, or an RNG.  It does not
enumerate the seed domain, compute a fiber count, identify a common proposal
law, prove any source law, or justify IID/product formulas.  In particular,
all derived Philox roles remain deterministic functions of one seed and may be
strongly correlated.  The optional dependency-lock and runtime-record digests
are custody labels only; their presence does not complete the transitive
source, compiled dependency, ABI, or libm binding required for an operational
law.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import json
from typing import Mapping, Optional, Tuple, cast


CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION = (
    "cp60-test28-whole-seed-pushforward-definition-v1"
)
CP60_TEST28_WHOLE_SEED_SCOPE = (
    "theorem-template-for-any-future-fully-bound-request-and-runtime;one-"
    "assumed-uniform-uint64-plan-seed;prospective-fixture-strategy-budget-grid-"
    "templates-do-not-identify-request-runtime-or-unique-law;mathematical-"
    "totalization-and-exact-"
    "seed-fiber-count-formulas;correlated-slot-and-role-pushforwards-only;"
    "optional-unverified-runtime-custody-labels;no-kernel-numpy-scipy-provider-"
    "or-rng-import-or-execution;no-seed-enumeration-no-numeric-fiber-counts-no-"
    "common-mu-fp-no-iid-no-role-independence-no-alpha-rho-product-formulas-no-"
    "operational-prediction-no-confirmatory-evidence-no-test28-closure"
)
CP60_TEST28_UNIFORM_SEED_ASSUMPTION_MODE = (
    "external-one-request-exact-uint64-unconditional-uniform-plan-seed-premise"
)
CP60_TEST28_UNIFORM_SEED_ASSUMPTION_SCOPE = (
    "assumption-only-becomes-operative-for-one-future-fully-bound-request-"
    "runtime-and-totalized-map;not-an-operational-seed-source-attestation;not-"
    "a-sequence-iid-cross-request-independence-derived-word-uniformity-role-"
    "independence-or-proposal-iid-premise"
)
CP60_TEST28_OUTCOME_STATUSES = (
    "returned-rejection-selected",
    "returned-rejection-exhausted",
    "returned-sir-selected",
    "preexecution-refusal",
    "execution-failure",
    "nonreturn",
)
CP60_TEST28_PREEXECUTION_REFUSAL_CLASSES = (
    "plan_validation_refusal",
    "provider_reference_binding_refusal",
    "resource_preflight_refusal",
    "runtime_binding_refusal",
    "other_preexecution_refusal",
)
CP60_TEST28_EXECUTION_FAILURE_CLASSES = (
    "reference_sampling_failure",
    "score_evaluation_failure",
    "quota_certification_failure",
    "float64_normalization_failure",
    "categorical_selection_failure",
    "structural_result_validation_failure",
    "other_execution_failure",
)
CP60_TEST28_REJECTION_TRACE_PAYLOAD = (
    "tagged-returned-rejection-trace-retains-canonical-proposal-configuration-"
    "values-exact-score-and-quota-records-decision-words-acceptance-vector-"
    "first-selected-index-and-selected-configuration-value-or-exhaustion;"
    "configuration-values-not-digest-only;selected-empty-configuration-remains-"
    "distinct-from-every-refusal-failure-and-nonreturn-tag"
)
CP60_TEST28_SIR_TRACE_PAYLOAD = (
    "tagged-returned-sir-trace-retains-canonical-proposal-cloud-values-exact-"
    "score-records-binary64-normalized-weight-bytes-resampling-word-uniform53-"
    "selected-index-and-selected-configuration-value;the-sequential-cdf-is-"
    "recomputable-under-the-frozen-formula-but-is-not-retained-by-kernel-v2;"
    "configuration-values-not-digest-only"
)
CP60_TEST28_TOTAL_MAP_DEFINITION = (
    "for-fixed-seed-free-request-R-and-fixed-runtime-E;K_R,E(s)-is-current-"
    "kernel-v2-after-inserting-exact-uint64-plan-seed-s;F_R,E(s)-is-the-"
    "corresponding-complete-validated-returned-trace-or-preexecution-refusal-or-"
    "execution-failure-or-nonreturn;these-disjoint-tags-mathematically-totalize-"
    "every-s-in-[0,2^64);failure-versus-nonreturn-need-not-be-mechanically-"
    "observable-by-a-returned-Python-record"
)
CP60_TEST28_FIBER_COUNT_FORMULA = (
    "N_E=cardinality({s-in-[0,2^64):F_R,E(s)-in-E});"
    "P(F_R,E(S)-in-E)=N_E/2^64-for-assumed-S-uniform-on-[0,2^64)"
)
CP60_TEST28_SINGLETON_FORMULA = (
    "N_y=cardinality({s-in-[0,2^64):F_R,E(s)=y});P(F_R,E(S)=y)=N_y/2^64"
)
CP60_TEST28_NORMALIZATION_FORMULA = (
    "the-disjoint-complete-outcome-fibers-partition-[0,2^64);"
    "sum_y-N_y=2^64-and-sum_y-N_y/2^64=1"
)
CP60_TEST28_REJECTION_FIBER_FORMULA = (
    "for-one-based-t-in-{1,...,A};N_first,t-counts-returned-selected-traces-"
    "with-zero-based-selected-index=t-1;P(first=t)=N_first,t/2^64;"
    "P(exhausted)=N_exhausted/2^64;P(preexecution-refusal)=N_refusal/2^64;"
    "P(selected-value=c)=N_select,c/"
    "2^64;P(selected-value=c|selected)=N_select,c/N_selected-only-if-"
    "N_selected>0;N_accept,t-counts-complete-validated-returned-rejection-"
    "traces-with-recorded-slot-t-accepted;P(slot-t-accepted-and-complete-"
    "validated-return)=N_accept,t/2^64;this-is-an-unconditional-subprobability-"
    "and-execution-failure-or-nonreturn-is-not-conditioned-away;no-common-"
    "alpha-or-(1-alpha)^A-formula-follows"
)
CP60_TEST28_NO_RETURNED_OUTPUT_FORMULA = (
    "P(no-validated-returned-output)=(N_preexecution_refusal+"
    "N_execution_failure+N_nonreturn)/2^64;these-three-fibers-are-distinct-"
    "and-N_refusal-never-denotes-their-aggregate"
)
CP60_TEST28_SIR_FIBER_FORMULA = (
    "P(finite-J-selected-value=c)=N_sir-select,c/2^64;arbitrary-cloud-weight-"
    "cell-and-selection-events-are-counted-by-the-same-whole-trace-fiber-"
    "formula;no-product-mu-fp^J-integral-follows"
)
CP60_TEST28_PROPOSAL_MARGINAL_FORMULA = (
    "on-each-explicitly-defined-reached-and-recorded-proposal-slot-t;the-"
    "slotwise-sublaw-is-the-corresponding-trace-projection-of-the-uniform-seed-"
    "pushforward;the-joint-realized-proposal-trace-sublaw-is-a-single-whole-"
    "seed-pushforward;neither-object-identifies-one-common-mu-fp-or-an-iid-"
    "product-law"
)
CP60_TEST28_FIXED_SEED_POINT_MASS_THEOREM = (
    "for-any-future-fully-fixed-R,E-and-one-fixed-s0-in-[0,2^64);"
    "Law(F_R,E(s0))=delta_{F_R,E(s0)};one-fixed-seed-replay-does-not-by-"
    "itself-establish-or-sample-the-uniform-seed-pushforward;the-two-laws-"
    "coincide-only-if-the-uniform-seed-pushforward-is-that-same-point-mass"
)
CP60_TEST28_FUTURE_VALIDATED_MC_REQUIREMENTS = (
    "fully-bound-request-and-totalized-runtime-map-before-sampling",
    "independently-verified-iid-uniform-uint64-plan-seeds-with-replacement",
    "or-separately-frozen-without-replacement-hypergeometric-design",
    "retain-every-refusal-execution-failure-and-nonreturn-outcome",
    "before-sampling-proved-termination-classifier-or-frozen-bounded-external-"
    "supervisor-with-timeout-censoring-retained-distinct-from-and-never-"
    "identified-with-semantic-nonreturn",
    "no-retry-drop-replacement-or-data-dependent-seed-selection",
    "prespecified-exact-binomial-multinomial-or-finite-population-uncertainty",
    "prespecified-familywise-multiplicity-control",
    "selected-law-claims-require-prespecified-positive-selected-count-rule",
    "seed-source-map-runtime-sample-and-interval-custody",
)
CP60_TEST28_RUNTIME_BINDING_REQUIREMENTS = (
    "transitive-local-source-file-hashes",
    "exact-python-executable-build-and-stdlib",
    "exact-numpy-and-scipy-distributions-and-loaded-extension-binaries",
    "numpy-philox-implementation-and-tables",
    "numpy-seedsequence-philox-seed-to-initial-state-mapping-and-state-schema",
    "numpy-generator-random-53bit-transform",
    "numpy-standard-normal-ziggurat-code-tables-and-variable-consumption",
    "numpy-exp-cumsum-searchsorted",
    "scipy-gammaln-and-logsumexp",
    "python-decimal-libmpdec-build-context-and-rounding-contract",
    "libc-libm-compiled-abi-and-linked-library-map",
    "operating-system-architecture-cpu-endianness-and-floating-rounding-mode",
    "dependency-lock-container-or-equivalent-runtime-record",
)
CP60_TEST28_FORMAL_TEST_28_STATUS = "OPEN"

CP60_TEST28_FIXTURE_IDS = ("T28-M1-Q", "T28-M2-Q")
CP60_TEST28_STRATEGIES = ("bounded-rejection", "fixed-budget-sir")
CP60_TEST28_REJECTION_BUDGET_GRID = (1, 4, 16, 64)
CP60_TEST28_SIR_BUDGET_GRID = (8, 32, 128, 512)
CP60_TEST28_MAX_BUDGET = 4_096
CP60_TEST28_PLAN_SEED_BITS = 64
CP60_TEST28_PLAN_SEED_DOMAIN_SIZE = 1 << CP60_TEST28_PLAN_SEED_BITS

CP60_TEST28_KERNEL_V2_SOURCE_SHA256 = (
    "a8164e10239bab6d43a8d8f068cf035d9a4c8b0b29ee233bf5b0af8d75a0684c"
)
CP60_TEST28_REFERENCE_SOURCE_SHA256 = (
    "725ddc4011e2c6cf15f1810be6fabc404c50bd53333e34ad22bedcdf4d6497da"
)
CP60_TEST28_PROVIDER_SOURCE_SHA256 = (
    "8aecb4ed75d4f88b7d6b0355f2d2c5ddad685d761fe4fbe63359bda672973234"
)
CP60_TEST28_EXACT_SCORE_SOURCE_SHA256 = (
    "87e197085ecee91ddbd78e1dfde3d0eb84797740946f76f1ee26f837d4149313"
)
CP60_TEST28_QUOTA_SOURCE_SHA256 = (
    "3985d23337f854e43a6ee766d4d9a0afeed0a60fd9e37855c064c88e7477dde1"
)
CP60_TEST28_CP59_SOURCE_SHA256 = (
    "e3e2b1384c1a7e8792dc96e64de9e7a7501bdbfc84a7a7bccf8455a78cf5ba4a"
)
CP60_TEST28_CP49_PRECEDENT_SOURCE_SHA256 = (
    "7951c02c60b6ca8dbbbf025f13e26e52eb7319cd4c48d416e5b841d99530bd39"
)

_ZERO_SHA256 = "0" * 64
_MAX_CANONICAL_NODES = 65_536
_MAX_CANONICAL_DEPTH = 32
_MAX_CANONICAL_TEXT_BYTES = 4_194_304
_MAX_CANONICAL_OUTPUT_BYTES = 8_388_608
_MAX_TEXT_BYTES = 65_536
_MAX_INTEGER_BITS = 256
_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        del cls, kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("the CP60 sealed-record base cannot be subclassed")

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("CP60 records are module-created")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP60 records are not pickle objects")


def _seal(cls: type, values: Mapping[str, object]) -> object:
    supplied = tuple(sorted(values))
    expected = tuple(sorted(item.name for item in fields(cls)))
    if supplied != expected:
        raise TypeError("sealed CP60 record field set differs")
    result = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result


def _text(value: object, name: str, maximum: int = _MAX_TEXT_BYTES) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(name + " must be bounded nonempty text")
    return value


def _sha256(value: object, name: str) -> str:
    checked = _text(value, name, 64)
    if len(checked) != 64 or any(c not in "0123456789abcdef" for c in checked):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return checked


def _optional_sha256(value: object, name: str) -> Optional[str]:
    if value is None:
        return None
    return _sha256(value, name)


def _bool(value: object, name: str, expected: Optional[bool] = None) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact bool")
    if expected is not None and value is not expected:
        raise ValueError(name + " differs")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError(name + " must be an exact integer")
    if not minimum <= value <= maximum:
        raise ValueError(name + " is outside the supported interval")
    return value


def _exact_tuple(value: object, name: str, expected: Tuple[object, ...]) -> tuple:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) != len(expected):
        raise ValueError(name + " differs")
    for index, (actual, wanted) in enumerate(zip(value, expected)):
        if type(actual) is not type(wanted):
            raise TypeError(name + "[%d] has the wrong exact type" % index)
    if value != expected:
        raise ValueError(name + " differs")
    return value


def _fixture(value: object) -> str:
    checked = _text(value, "fixture_id", 32)
    if checked not in CP60_TEST28_FIXTURE_IDS:
        raise ValueError("fixture_id is not a frozen CP60 fixture")
    return checked


def _strategy(value: object) -> str:
    checked = _text(value, "strategy", 64)
    if checked not in CP60_TEST28_STRATEGIES:
        raise ValueError("strategy is not a stochastic kernel-v2 strategy")
    return checked


def _budget(value: object) -> int:
    return _integer(value, "budget", 1, CP60_TEST28_MAX_BUDGET)


@dataclass(frozen=True, eq=False, init=False, slots=True)
class UniformPlanSeedAssumptionV1(_SealedRecord):
    schema_version: str
    scope: str
    assumption_mode: str
    assumption_scope: str
    request_template_sha256: str
    assumption_role_sha256: str
    seed_bits: int
    seed_domain_minimum: int
    seed_domain_maximum: int
    seed_domain_size: int
    uniform_seed_singleton_mass: Fraction
    one_exact_uint64_seed_almost_surely_supplied_assumed: bool
    unconditional_uniform_plan_seed_assumed: bool
    pointwise_one_future_fully_fixed_request_only: bool
    assumption_only: bool
    current_fixed_hash_seed_plan_matches: bool
    operational_seed_source_verified: bool
    backend_totality_verified: bool
    seed_sequence_iid_assumed: bool
    cross_request_iid_assumed: bool
    derived_philox_word_uniformity_assumed: bool
    derived_philox_product_law_assumed: bool
    role_stream_independence_assumed: bool
    proposal_iid_assumed: bool
    os_entropy_law_verified: bool
    physical_entropy_or_cryptographic_quality_verified: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("UniformPlanSeedAssumptionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class WholeSeedOutcomeAlphabetV1(_SealedRecord):
    schema_version: str
    scope: str
    statuses: Tuple[str, ...]
    preexecution_refusal_classes: Tuple[str, ...]
    execution_failure_classes: Tuple[str, ...]
    rejection_trace_payload: str
    sir_trace_payload: str
    total_map_definition: str
    returned_trace_retains_configuration_values_not_digest_only: bool
    selected_empty_configuration_distinct_from_nonreturn: bool
    outcome_tags_pairwise_disjoint: bool
    outcome_tags_mathematically_exhaustive: bool
    nonreturn_is_explicit: bool
    failure_versus_nonreturn_mechanically_observable: bool
    python_exception_catching_proves_nonreturn_mass_zero: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("WholeSeedOutcomeAlphabetV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class WholeSeedPushforwardDefinitionV1(_SealedRecord):
    schema_version: str
    scope: str
    fixture_id: str
    strategy: str
    budget: int
    request_template_sha256: str
    seed_assumption: UniformPlanSeedAssumptionV1
    seed_assumption_sha256: str
    outcome_alphabet: WholeSeedOutcomeAlphabetV1
    outcome_alphabet_sha256: str
    kernel_v2_source_sha256: str
    reference_source_sha256: str
    provider_source_sha256: str
    exact_score_source_sha256: str
    quota_source_sha256: str
    cp59_source_sha256: str
    cp49_precedent_source_sha256: str
    dependency_lock_sha256: Optional[str]
    runtime_record_sha256: Optional[str]
    runtime_binding_requirements: Tuple[str, ...]
    total_map_definition: str
    fiber_count_formula: str
    singleton_formula: str
    normalization_formula: str
    rejection_fiber_formula: str
    sir_fiber_formula: str
    proposal_marginal_formula: str
    no_returned_output_formula: str
    fixed_seed_point_mass_theorem: str
    future_validated_mc_requirements: Tuple[str, ...]
    request_parameters_fully_bound: bool
    fixed_request_map_instantiated: bool
    symbolic_pushforward_formula_defined_for_future_fixed_request_under_assumption: bool
    mathematical_totalization_formula_defined_for_future_fixed_request: bool
    correlated_whole_request_model_required: bool
    joint_realized_proposal_trace_sublaw_symbolically_defined: bool
    slotwise_proposal_marginals_symbolically_defined: bool
    fixed_seed_point_mass_theorem_recorded: bool
    future_validated_mc_requirements_recorded: bool
    source_file_digests_are_unverified_custody_labels: bool
    optional_runtime_digests_are_unverified_custody_labels: bool
    cp59_conditional_arithmetic_precursor_only: bool
    cp49_assumption_gate_semantic_precedent_only: bool
    cp49_artifact_ancestry_claimed: bool
    runtime_dependency_map_complete: bool
    compiled_dependency_abi_libm_map_complete: bool
    current_kernel_runtime_sha256_sufficient: bool
    fixed_seed_replay_establishes_or_samples_uniform_seed_law: bool
    runtime_map_executed: bool
    seed_domain_exhaustively_enumerated: bool
    numeric_fiber_counts_computed: bool
    outcome_status_fiber_counts: Optional[Tuple[int, ...]]
    rejection_first_acceptance_fiber_counts: Optional[Tuple[int, ...]]
    rejection_selected_value_fiber_counts: Optional[Tuple[int, ...]]
    sir_selected_value_fiber_counts: Optional[Tuple[int, ...]]
    refusal_fiber_count: Optional[int]
    exhaustion_fiber_count: Optional[int]
    execution_failure_fiber_count: Optional[int]
    nonreturn_fiber_count: Optional[int]
    execution_totality_proved: bool
    nonreturn_mass_proved_zero: bool
    common_mu_fp_identified: bool
    proposal_iid_verified: bool
    cross_request_iid_verified: bool
    derived_word_uniformity_verified: bool
    role_stream_independence_verified: bool
    alpha64_product_formula_permitted: bool
    rho64_product_formula_permitted: bool
    operational_alpha64_derived: bool
    operational_rho64_derived: bool
    operational_refusal_probability_derived: bool
    operational_exhaustion_probability_derived: bool
    unconditional_finite_j_sir_law_derived: bool
    future_mc_seed_source_verified: bool
    future_mc_map_and_runtime_fully_fixed: bool
    future_mc_failures_and_nonreturn_retained: bool
    future_mc_nonreturn_observability_mechanism_fixed: bool
    future_mc_no_retry_drop_or_seed_selection_verified: bool
    future_mc_uncertainty_method_prespecified: bool
    future_mc_multiplicity_method_prespecified: bool
    future_mc_positive_selected_count_rule_prespecified: bool
    validated_mc_executed: bool
    validated_mc_sample_recorded: bool
    validated_mc_intervals_computed: bool
    current_deterministic_seed_plan_is_validated_mc: bool
    operational_prediction: bool
    production_observed: bool
    confirmatory_evidence: bool
    manuscript_claim_promoted: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("WholeSeedPushforwardDefinitionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP60WholeSeedPushforwardBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    outcome_alphabet: WholeSeedOutcomeAlphabetV1
    ordered_definitions: Tuple[WholeSeedPushforwardDefinitionV1, ...]
    rejection_definitions: Tuple[WholeSeedPushforwardDefinitionV1, ...]
    sir_definitions: Tuple[WholeSeedPushforwardDefinitionV1, ...]
    fixture_ids: Tuple[str, ...]
    rejection_budget_grid: Tuple[int, ...]
    sir_budget_grid: Tuple[int, ...]
    all_grid_templates_predeclared: bool
    definition_only: bool
    kernel_numpy_scipy_provider_or_rng_imported_or_executed: bool
    runtime_dependency_map_complete: bool
    seed_domain_exhaustively_enumerated: bool
    numeric_fiber_counts_computed: bool
    request_parameters_fully_bound: bool
    fixed_request_maps_instantiated: bool
    future_validated_mc_requirements_recorded: bool
    validated_mc_executed: bool
    common_mu_fp_identified: bool
    operational_prediction: bool
    unconditional_operational_predictions_blocker_closed: bool
    production_observed: bool
    confirmatory_evidence: bool
    manuscript_claim_promoted: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP60WholeSeedPushforwardBundleV1 cannot be subclassed")


_ALLOW_RECORD_CLASS_DEFINITION = False
_RECORD_TYPE_TAGS = {
    UniformPlanSeedAssumptionV1: "uniform-plan-seed-assumption-v1",
    WholeSeedOutcomeAlphabetV1: "whole-seed-outcome-alphabet-v1",
    WholeSeedPushforwardDefinitionV1: "whole-seed-pushforward-definition-v1",
    CP60WholeSeedPushforwardBundleV1: "whole-seed-pushforward-bundle-v1",
}


def _canonical_value(value: object, *, state: list[int], depth: int) -> object:
    state[0] += 1
    if state[0] > _MAX_CANONICAL_NODES or depth > _MAX_CANONICAL_DEPTH:
        raise ValueError("CP60 canonical encoding exceeds node/depth limits")
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int:
        if value.bit_length() > _MAX_INTEGER_BITS:
            raise ValueError("CP60 canonical integer exceeds the bit limit")
        raw = format(abs(value), "x")
        state[1] += len(raw)
        if state[1] > _MAX_CANONICAL_TEXT_BYTES:
            raise ValueError("CP60 canonical generated text exceeds the byte limit")
        return ["int-hex", "negative" if value < 0 else "nonnegative", raw]
    if type(value) is str:
        encoded = value.encode("utf-8")
        if len(encoded) > _MAX_TEXT_BYTES:
            raise ValueError("CP60 canonical text exceeds the per-field limit")
        state[1] += len(encoded)
        if state[1] > _MAX_CANONICAL_TEXT_BYTES:
            raise ValueError("CP60 canonical generated text exceeds the byte limit")
        return ["str", value]
    if type(value) is Fraction:
        if (
            value.numerator.bit_length() > _MAX_INTEGER_BITS
            or value.denominator.bit_length() > _MAX_INTEGER_BITS
        ):
            raise ValueError("CP60 canonical fraction exceeds the bit limit")
        numerator = format(abs(value.numerator), "x")
        denominator = format(value.denominator, "x")
        state[1] += len(numerator) + len(denominator)
        if state[1] > _MAX_CANONICAL_TEXT_BYTES:
            raise ValueError("CP60 canonical generated text exceeds the byte limit")
        return [
            "fraction-hex",
            "negative" if value.numerator < 0 else "nonnegative",
            numerator,
            denominator,
        ]
    if type(value) is tuple:
        if len(value) > _MAX_CANONICAL_NODES:
            raise ValueError("CP60 canonical tuple exceeds the resource limit")
        return [
            "tuple",
            [_canonical_value(item, state=state, depth=depth + 1) for item in value],
        ]
    if type(value) is dict:
        if len(value) > 256 or not all(type(key) is str for key in value):
            raise TypeError("CP60 canonical mappings require bounded text keys")
        return [
            "mapping",
            [
                [
                    _canonical_value(key, state=state, depth=depth + 1),
                    _canonical_value(value[key], state=state, depth=depth + 1),
                ]
                for key in sorted(value)
            ],
        ]
    tag = _RECORD_TYPE_TAGS.get(type(value))
    if tag is not None:
        payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
        return [
            "record",
            tag,
            _canonical_value(payload, state=state, depth=depth + 1),
        ]
    raise TypeError("unsupported CP60 canonical type " + type(value).__name__)


def _canonical_bytes(value: object) -> bytes:
    encoded = json.dumps(
        _canonical_value(value, state=[0, 0], depth=0),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    if len(encoded) > _MAX_CANONICAL_OUTPUT_BYTES:
        raise ValueError("CP60 canonical output exceeds the byte limit")
    return encoded


def _digest(domain: str, values: Mapping[str, object]) -> str:
    if type(values) is not dict:
        values = dict(values)
    payload = {name: values[name] for name in values if name != "record_sha256"}
    return hashlib.sha256(
        ("cp60-test28-" + domain + "-v1\x00").encode("ascii")
        + _canonical_bytes(payload)
    ).hexdigest()


def _request_template_sha256(fixture_id: str, strategy: str, budget: int) -> str:
    return hashlib.sha256(
        b"cp60-test28-seed-free-request-template-v1\x00"
        + _canonical_bytes(
            {
                "fixture_id": fixture_id,
                "strategy": strategy,
                "budget": budget,
                "kernel_v2_source_sha256": CP60_TEST28_KERNEL_V2_SOURCE_SHA256,
                "reference_source_sha256": CP60_TEST28_REFERENCE_SOURCE_SHA256,
                "provider_source_sha256": CP60_TEST28_PROVIDER_SOURCE_SHA256,
                "exact_score_source_sha256": CP60_TEST28_EXACT_SCORE_SOURCE_SHA256,
                "quota_source_sha256": CP60_TEST28_QUOTA_SOURCE_SHA256,
                "cp59_source_sha256": CP60_TEST28_CP59_SOURCE_SHA256,
                "cp49_precedent_source_sha256": (
                    CP60_TEST28_CP49_PRECEDENT_SOURCE_SHA256
                ),
            }
        )
    ).hexdigest()


def _assumption_role_sha256(request_template_sha256: str) -> str:
    return hashlib.sha256(
        b"cp60-test28-uniform-seed-assumption-role-v1\x00"
        + bytes.fromhex(request_template_sha256)
    ).hexdigest()


def declare_cp60_uniform_plan_seed_assumption(
    *,
    request_template_sha256: object,
    assumption_role_sha256: object,
    one_exact_uint64_seed_almost_surely_supplied_assumed: object,
    unconditional_uniform_plan_seed_assumed: object,
) -> UniformPlanSeedAssumptionV1:
    """Declare, but do not verify, the sole CP60 one-request seed premise."""

    request = _sha256(request_template_sha256, "request_template_sha256")
    role = _sha256(assumption_role_sha256, "assumption_role_sha256")
    _bool(
        one_exact_uint64_seed_almost_surely_supplied_assumed,
        "one_exact_uint64_seed_almost_surely_supplied_assumed",
        True,
    )
    _bool(
        unconditional_uniform_plan_seed_assumed,
        "unconditional_uniform_plan_seed_assumed",
        True,
    )
    values = {
        "schema_version": CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "scope": CP60_TEST28_WHOLE_SEED_SCOPE,
        "assumption_mode": CP60_TEST28_UNIFORM_SEED_ASSUMPTION_MODE,
        "assumption_scope": CP60_TEST28_UNIFORM_SEED_ASSUMPTION_SCOPE,
        "request_template_sha256": request,
        "assumption_role_sha256": role,
        "seed_bits": CP60_TEST28_PLAN_SEED_BITS,
        "seed_domain_minimum": 0,
        "seed_domain_maximum": CP60_TEST28_PLAN_SEED_DOMAIN_SIZE - 1,
        "seed_domain_size": CP60_TEST28_PLAN_SEED_DOMAIN_SIZE,
        "uniform_seed_singleton_mass": Fraction(1, CP60_TEST28_PLAN_SEED_DOMAIN_SIZE),
        "one_exact_uint64_seed_almost_surely_supplied_assumed": True,
        "unconditional_uniform_plan_seed_assumed": True,
        "pointwise_one_future_fully_fixed_request_only": True,
        "assumption_only": True,
        "current_fixed_hash_seed_plan_matches": False,
        "operational_seed_source_verified": False,
        "backend_totality_verified": False,
        "seed_sequence_iid_assumed": False,
        "cross_request_iid_assumed": False,
        "derived_philox_word_uniformity_assumed": False,
        "derived_philox_product_law_assumed": False,
        "role_stream_independence_assumed": False,
        "proposal_iid_assumed": False,
        "os_entropy_law_verified": False,
        "physical_entropy_or_cryptographic_quality_verified": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("uniform-seed-assumption", values)
    result = cast(
        UniformPlanSeedAssumptionV1,
        _seal(UniformPlanSeedAssumptionV1, values),
    )
    return validate_cp60_uniform_plan_seed_assumption(result)


def cp60_whole_seed_outcome_alphabet() -> WholeSeedOutcomeAlphabetV1:
    """Return the strategy-disjunctive, mathematically total outcome alphabet."""

    values = {
        "schema_version": CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "scope": CP60_TEST28_WHOLE_SEED_SCOPE,
        "statuses": CP60_TEST28_OUTCOME_STATUSES,
        "preexecution_refusal_classes": CP60_TEST28_PREEXECUTION_REFUSAL_CLASSES,
        "execution_failure_classes": CP60_TEST28_EXECUTION_FAILURE_CLASSES,
        "rejection_trace_payload": CP60_TEST28_REJECTION_TRACE_PAYLOAD,
        "sir_trace_payload": CP60_TEST28_SIR_TRACE_PAYLOAD,
        "total_map_definition": CP60_TEST28_TOTAL_MAP_DEFINITION,
        "returned_trace_retains_configuration_values_not_digest_only": True,
        "selected_empty_configuration_distinct_from_nonreturn": True,
        "outcome_tags_pairwise_disjoint": True,
        "outcome_tags_mathematically_exhaustive": True,
        "nonreturn_is_explicit": True,
        "failure_versus_nonreturn_mechanically_observable": False,
        "python_exception_catching_proves_nonreturn_mass_zero": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("outcome-alphabet", values)
    result = cast(
        WholeSeedOutcomeAlphabetV1,
        _seal(WholeSeedOutcomeAlphabetV1, values),
    )
    return validate_cp60_whole_seed_outcome_alphabet(result)


def define_cp60_whole_seed_pushforward(
    *,
    fixture_id: object,
    strategy: object,
    budget: object,
    request_template_sha256: object,
    seed_assumption: object,
    kernel_v2_source_sha256: object,
    reference_source_sha256: object,
    provider_source_sha256: object,
    exact_score_source_sha256: object,
    quota_source_sha256: object,
    dependency_lock_sha256: object = None,
    runtime_record_sha256: object = None,
) -> WholeSeedPushforwardDefinitionV1:
    """Define one symbolic correlated whole-seed pushforward and no numbers."""

    fixture = _fixture(fixture_id)
    checked_strategy = _strategy(strategy)
    checked_budget = _budget(budget)
    permitted_grid = (
        CP60_TEST28_REJECTION_BUDGET_GRID
        if checked_strategy == "bounded-rejection"
        else CP60_TEST28_SIR_BUDGET_GRID
    )
    if checked_budget not in permitted_grid:
        raise ValueError("budget is not in the frozen strategy-specific CP60 grid")
    request = _sha256(request_template_sha256, "request_template_sha256")
    expected_request = _request_template_sha256(
        fixture, checked_strategy, checked_budget
    )
    if request != expected_request:
        raise ValueError(
            "request_template_sha256 differs from the frozen fixture request"
        )
    assumption = validate_cp60_uniform_plan_seed_assumption(seed_assumption)
    if assumption.request_template_sha256 != request:
        raise ValueError("seed assumption belongs to another request template")
    if assumption.assumption_role_sha256 != _assumption_role_sha256(request):
        raise ValueError("seed assumption role differs from the frozen request role")
    outcome = cp60_whole_seed_outcome_alphabet()
    values = {
        "schema_version": CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "scope": CP60_TEST28_WHOLE_SEED_SCOPE,
        "fixture_id": fixture,
        "strategy": checked_strategy,
        "budget": checked_budget,
        "request_template_sha256": request,
        "seed_assumption": assumption,
        "seed_assumption_sha256": assumption.record_sha256,
        "outcome_alphabet": outcome,
        "outcome_alphabet_sha256": outcome.record_sha256,
        "kernel_v2_source_sha256": _sha256(
            kernel_v2_source_sha256, "kernel_v2_source_sha256"
        ),
        "reference_source_sha256": _sha256(
            reference_source_sha256, "reference_source_sha256"
        ),
        "provider_source_sha256": _sha256(
            provider_source_sha256, "provider_source_sha256"
        ),
        "exact_score_source_sha256": _sha256(
            exact_score_source_sha256, "exact_score_source_sha256"
        ),
        "quota_source_sha256": _sha256(quota_source_sha256, "quota_source_sha256"),
        "cp59_source_sha256": CP60_TEST28_CP59_SOURCE_SHA256,
        "cp49_precedent_source_sha256": (CP60_TEST28_CP49_PRECEDENT_SOURCE_SHA256),
        "dependency_lock_sha256": _optional_sha256(
            dependency_lock_sha256, "dependency_lock_sha256"
        ),
        "runtime_record_sha256": _optional_sha256(
            runtime_record_sha256, "runtime_record_sha256"
        ),
        "runtime_binding_requirements": CP60_TEST28_RUNTIME_BINDING_REQUIREMENTS,
        "total_map_definition": CP60_TEST28_TOTAL_MAP_DEFINITION,
        "fiber_count_formula": CP60_TEST28_FIBER_COUNT_FORMULA,
        "singleton_formula": CP60_TEST28_SINGLETON_FORMULA,
        "normalization_formula": CP60_TEST28_NORMALIZATION_FORMULA,
        "rejection_fiber_formula": CP60_TEST28_REJECTION_FIBER_FORMULA,
        "sir_fiber_formula": CP60_TEST28_SIR_FIBER_FORMULA,
        "proposal_marginal_formula": CP60_TEST28_PROPOSAL_MARGINAL_FORMULA,
        "no_returned_output_formula": CP60_TEST28_NO_RETURNED_OUTPUT_FORMULA,
        "fixed_seed_point_mass_theorem": (CP60_TEST28_FIXED_SEED_POINT_MASS_THEOREM),
        "future_validated_mc_requirements": (
            CP60_TEST28_FUTURE_VALIDATED_MC_REQUIREMENTS
        ),
        "request_parameters_fully_bound": False,
        "fixed_request_map_instantiated": False,
        "symbolic_pushforward_formula_defined_for_future_fixed_request_under_assumption": True,
        "mathematical_totalization_formula_defined_for_future_fixed_request": True,
        "correlated_whole_request_model_required": True,
        "joint_realized_proposal_trace_sublaw_symbolically_defined": True,
        "slotwise_proposal_marginals_symbolically_defined": True,
        "fixed_seed_point_mass_theorem_recorded": True,
        "future_validated_mc_requirements_recorded": True,
        "source_file_digests_are_unverified_custody_labels": True,
        "optional_runtime_digests_are_unverified_custody_labels": True,
        "cp59_conditional_arithmetic_precursor_only": True,
        "cp49_assumption_gate_semantic_precedent_only": True,
        "cp49_artifact_ancestry_claimed": False,
        "runtime_dependency_map_complete": False,
        "compiled_dependency_abi_libm_map_complete": False,
        "current_kernel_runtime_sha256_sufficient": False,
        "fixed_seed_replay_establishes_or_samples_uniform_seed_law": False,
        "runtime_map_executed": False,
        "seed_domain_exhaustively_enumerated": False,
        "numeric_fiber_counts_computed": False,
        "outcome_status_fiber_counts": None,
        "rejection_first_acceptance_fiber_counts": None,
        "rejection_selected_value_fiber_counts": None,
        "sir_selected_value_fiber_counts": None,
        "refusal_fiber_count": None,
        "exhaustion_fiber_count": None,
        "execution_failure_fiber_count": None,
        "nonreturn_fiber_count": None,
        "execution_totality_proved": False,
        "nonreturn_mass_proved_zero": False,
        "common_mu_fp_identified": False,
        "proposal_iid_verified": False,
        "cross_request_iid_verified": False,
        "derived_word_uniformity_verified": False,
        "role_stream_independence_verified": False,
        "alpha64_product_formula_permitted": False,
        "rho64_product_formula_permitted": False,
        "operational_alpha64_derived": False,
        "operational_rho64_derived": False,
        "operational_refusal_probability_derived": False,
        "operational_exhaustion_probability_derived": False,
        "unconditional_finite_j_sir_law_derived": False,
        "future_mc_seed_source_verified": False,
        "future_mc_map_and_runtime_fully_fixed": False,
        "future_mc_failures_and_nonreturn_retained": False,
        "future_mc_nonreturn_observability_mechanism_fixed": False,
        "future_mc_no_retry_drop_or_seed_selection_verified": False,
        "future_mc_uncertainty_method_prespecified": False,
        "future_mc_multiplicity_method_prespecified": False,
        "future_mc_positive_selected_count_rule_prespecified": False,
        "validated_mc_executed": False,
        "validated_mc_sample_recorded": False,
        "validated_mc_intervals_computed": False,
        "current_deterministic_seed_plan_is_validated_mc": False,
        "operational_prediction": False,
        "production_observed": False,
        "confirmatory_evidence": False,
        "manuscript_claim_promoted": False,
        "formal_test_28_status": CP60_TEST28_FORMAL_TEST_28_STATUS,
        "formal_test_28_closed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("whole-seed-definition", values)
    result = cast(
        WholeSeedPushforwardDefinitionV1,
        _seal(WholeSeedPushforwardDefinitionV1, values),
    )
    return validate_cp60_whole_seed_pushforward(result)


def _validate_constant_text(value: object, expected: str, name: str) -> None:
    if _text(value, name) != expected:
        raise ValueError(name + " differs")


def validate_cp60_uniform_plan_seed_assumption(
    value: object,
) -> UniformPlanSeedAssumptionV1:
    if type(value) is not UniformPlanSeedAssumptionV1:
        raise TypeError("uniform seed assumption has the wrong exact CP60 type")
    _validate_constant_text(
        value.schema_version,
        CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "assumption.schema_version",
    )
    _validate_constant_text(
        value.scope, CP60_TEST28_WHOLE_SEED_SCOPE, "assumption.scope"
    )
    _validate_constant_text(
        value.assumption_mode,
        CP60_TEST28_UNIFORM_SEED_ASSUMPTION_MODE,
        "assumption.assumption_mode",
    )
    _validate_constant_text(
        value.assumption_scope,
        CP60_TEST28_UNIFORM_SEED_ASSUMPTION_SCOPE,
        "assumption.assumption_scope",
    )
    _sha256(value.request_template_sha256, "assumption.request_template_sha256")
    _sha256(value.assumption_role_sha256, "assumption.assumption_role_sha256")
    expected_scalars = {
        "seed_bits": CP60_TEST28_PLAN_SEED_BITS,
        "seed_domain_minimum": 0,
        "seed_domain_maximum": CP60_TEST28_PLAN_SEED_DOMAIN_SIZE - 1,
        "seed_domain_size": CP60_TEST28_PLAN_SEED_DOMAIN_SIZE,
    }
    for name, expected in expected_scalars.items():
        if type(getattr(value, name)) is not int or getattr(value, name) != expected:
            raise ValueError("assumption." + name + " differs")
    if type(
        value.uniform_seed_singleton_mass
    ) is not Fraction or value.uniform_seed_singleton_mass != Fraction(
        1, CP60_TEST28_PLAN_SEED_DOMAIN_SIZE
    ):
        raise ValueError("assumption uniform singleton mass differs")
    for name in (
        "one_exact_uint64_seed_almost_surely_supplied_assumed",
        "unconditional_uniform_plan_seed_assumed",
        "pointwise_one_future_fully_fixed_request_only",
        "assumption_only",
    ):
        _bool(getattr(value, name), "assumption." + name, True)
    for name in (
        "current_fixed_hash_seed_plan_matches",
        "operational_seed_source_verified",
        "backend_totality_verified",
        "seed_sequence_iid_assumed",
        "cross_request_iid_assumed",
        "derived_philox_word_uniformity_assumed",
        "derived_philox_product_law_assumed",
        "role_stream_independence_assumed",
        "proposal_iid_assumed",
        "os_entropy_law_verified",
        "physical_entropy_or_cryptographic_quality_verified",
    ):
        _bool(getattr(value, name), "assumption." + name, False)
    _sha256(value.record_sha256, "assumption.record_sha256")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    if value.record_sha256 != _digest("uniform-seed-assumption", payload):
        raise ValueError("uniform seed assumption digest differs")
    return value


def validate_cp60_whole_seed_outcome_alphabet(
    value: object,
) -> WholeSeedOutcomeAlphabetV1:
    if type(value) is not WholeSeedOutcomeAlphabetV1:
        raise TypeError("outcome alphabet has the wrong exact CP60 type")
    _validate_constant_text(
        value.schema_version,
        CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "alphabet.schema_version",
    )
    _validate_constant_text(value.scope, CP60_TEST28_WHOLE_SEED_SCOPE, "alphabet.scope")
    _exact_tuple(value.statuses, "alphabet.statuses", CP60_TEST28_OUTCOME_STATUSES)
    _exact_tuple(
        value.preexecution_refusal_classes,
        "alphabet.preexecution_refusal_classes",
        CP60_TEST28_PREEXECUTION_REFUSAL_CLASSES,
    )
    _exact_tuple(
        value.execution_failure_classes,
        "alphabet.execution_failure_classes",
        CP60_TEST28_EXECUTION_FAILURE_CLASSES,
    )
    _validate_constant_text(
        value.rejection_trace_payload,
        CP60_TEST28_REJECTION_TRACE_PAYLOAD,
        "alphabet.rejection_trace_payload",
    )
    _validate_constant_text(
        value.sir_trace_payload,
        CP60_TEST28_SIR_TRACE_PAYLOAD,
        "alphabet.sir_trace_payload",
    )
    _validate_constant_text(
        value.total_map_definition,
        CP60_TEST28_TOTAL_MAP_DEFINITION,
        "alphabet.total_map_definition",
    )
    for name in (
        "returned_trace_retains_configuration_values_not_digest_only",
        "selected_empty_configuration_distinct_from_nonreturn",
        "outcome_tags_pairwise_disjoint",
        "outcome_tags_mathematically_exhaustive",
        "nonreturn_is_explicit",
    ):
        _bool(getattr(value, name), "alphabet." + name, True)
    for name in (
        "failure_versus_nonreturn_mechanically_observable",
        "python_exception_catching_proves_nonreturn_mass_zero",
    ):
        _bool(getattr(value, name), "alphabet." + name, False)
    _sha256(value.record_sha256, "alphabet.record_sha256")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    if value.record_sha256 != _digest("outcome-alphabet", payload):
        raise ValueError("outcome alphabet digest differs")
    return value


def validate_cp60_whole_seed_pushforward(
    value: object,
) -> WholeSeedPushforwardDefinitionV1:
    if type(value) is not WholeSeedPushforwardDefinitionV1:
        raise TypeError("whole-seed definition has the wrong exact CP60 type")
    _validate_constant_text(
        value.schema_version,
        CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "definition.schema_version",
    )
    _validate_constant_text(
        value.scope, CP60_TEST28_WHOLE_SEED_SCOPE, "definition.scope"
    )
    _fixture(value.fixture_id)
    _strategy(value.strategy)
    _budget(value.budget)
    permitted_grid = (
        CP60_TEST28_REJECTION_BUDGET_GRID
        if value.strategy == "bounded-rejection"
        else CP60_TEST28_SIR_BUDGET_GRID
    )
    if value.budget not in permitted_grid:
        raise ValueError("definition budget is outside its frozen strategy grid")
    request = _sha256(
        value.request_template_sha256, "definition.request_template_sha256"
    )
    if type(value.seed_assumption) is not UniformPlanSeedAssumptionV1:
        raise TypeError("definition seed assumption has the wrong exact type")
    assumption = validate_cp60_uniform_plan_seed_assumption(value.seed_assumption)
    if assumption.request_template_sha256 != request:
        raise ValueError("definition seed assumption request differs")
    if assumption.assumption_role_sha256 != _assumption_role_sha256(request):
        raise ValueError("definition seed assumption role differs")
    if (
        _sha256(value.seed_assumption_sha256, "definition.seed_assumption_sha256")
        != assumption.record_sha256
    ):
        raise ValueError("definition seed assumption digest differs")
    if type(value.outcome_alphabet) is not WholeSeedOutcomeAlphabetV1:
        raise TypeError("definition outcome alphabet has the wrong exact type")
    outcome = validate_cp60_whole_seed_outcome_alphabet(value.outcome_alphabet)
    if (
        _sha256(value.outcome_alphabet_sha256, "definition.outcome_alphabet_sha256")
        != outcome.record_sha256
    ):
        raise ValueError("definition outcome alphabet digest differs")
    expected_source_hashes = {
        "kernel_v2_source_sha256": CP60_TEST28_KERNEL_V2_SOURCE_SHA256,
        "reference_source_sha256": CP60_TEST28_REFERENCE_SOURCE_SHA256,
        "provider_source_sha256": CP60_TEST28_PROVIDER_SOURCE_SHA256,
        "exact_score_source_sha256": CP60_TEST28_EXACT_SCORE_SOURCE_SHA256,
        "quota_source_sha256": CP60_TEST28_QUOTA_SOURCE_SHA256,
        "cp59_source_sha256": CP60_TEST28_CP59_SOURCE_SHA256,
        "cp49_precedent_source_sha256": (CP60_TEST28_CP49_PRECEDENT_SOURCE_SHA256),
    }
    for name, expected in expected_source_hashes.items():
        if _sha256(getattr(value, name), "definition." + name) != expected:
            raise ValueError("definition frozen source hash differs: " + name)
    if request != _request_template_sha256(
        value.fixture_id, value.strategy, value.budget
    ):
        raise ValueError("definition request-template digest differs")
    _optional_sha256(value.dependency_lock_sha256, "definition.dependency_lock_sha256")
    _optional_sha256(value.runtime_record_sha256, "definition.runtime_record_sha256")
    _exact_tuple(
        value.runtime_binding_requirements,
        "definition.runtime_binding_requirements",
        CP60_TEST28_RUNTIME_BINDING_REQUIREMENTS,
    )
    expected_text = {
        "total_map_definition": CP60_TEST28_TOTAL_MAP_DEFINITION,
        "fiber_count_formula": CP60_TEST28_FIBER_COUNT_FORMULA,
        "singleton_formula": CP60_TEST28_SINGLETON_FORMULA,
        "normalization_formula": CP60_TEST28_NORMALIZATION_FORMULA,
        "rejection_fiber_formula": CP60_TEST28_REJECTION_FIBER_FORMULA,
        "sir_fiber_formula": CP60_TEST28_SIR_FIBER_FORMULA,
        "proposal_marginal_formula": CP60_TEST28_PROPOSAL_MARGINAL_FORMULA,
        "no_returned_output_formula": CP60_TEST28_NO_RETURNED_OUTPUT_FORMULA,
        "fixed_seed_point_mass_theorem": (CP60_TEST28_FIXED_SEED_POINT_MASS_THEOREM),
        "formal_test_28_status": CP60_TEST28_FORMAL_TEST_28_STATUS,
    }
    for name, expected in expected_text.items():
        _validate_constant_text(getattr(value, name), expected, "definition." + name)
    _exact_tuple(
        value.future_validated_mc_requirements,
        "definition.future_validated_mc_requirements",
        CP60_TEST28_FUTURE_VALIDATED_MC_REQUIREMENTS,
    )
    for name in (
        "symbolic_pushforward_formula_defined_for_future_fixed_request_under_assumption",
        "mathematical_totalization_formula_defined_for_future_fixed_request",
        "correlated_whole_request_model_required",
        "joint_realized_proposal_trace_sublaw_symbolically_defined",
        "slotwise_proposal_marginals_symbolically_defined",
        "fixed_seed_point_mass_theorem_recorded",
        "future_validated_mc_requirements_recorded",
        "source_file_digests_are_unverified_custody_labels",
        "optional_runtime_digests_are_unverified_custody_labels",
        "cp59_conditional_arithmetic_precursor_only",
        "cp49_assumption_gate_semantic_precedent_only",
    ):
        _bool(getattr(value, name), "definition." + name, True)
    for name in (
        "request_parameters_fully_bound",
        "fixed_request_map_instantiated",
        "cp49_artifact_ancestry_claimed",
        "runtime_dependency_map_complete",
        "compiled_dependency_abi_libm_map_complete",
        "current_kernel_runtime_sha256_sufficient",
        "fixed_seed_replay_establishes_or_samples_uniform_seed_law",
        "runtime_map_executed",
        "seed_domain_exhaustively_enumerated",
        "numeric_fiber_counts_computed",
        "execution_totality_proved",
        "nonreturn_mass_proved_zero",
        "common_mu_fp_identified",
        "proposal_iid_verified",
        "cross_request_iid_verified",
        "derived_word_uniformity_verified",
        "role_stream_independence_verified",
        "alpha64_product_formula_permitted",
        "rho64_product_formula_permitted",
        "operational_alpha64_derived",
        "operational_rho64_derived",
        "operational_refusal_probability_derived",
        "operational_exhaustion_probability_derived",
        "unconditional_finite_j_sir_law_derived",
        "future_mc_seed_source_verified",
        "future_mc_map_and_runtime_fully_fixed",
        "future_mc_failures_and_nonreturn_retained",
        "future_mc_nonreturn_observability_mechanism_fixed",
        "future_mc_no_retry_drop_or_seed_selection_verified",
        "future_mc_uncertainty_method_prespecified",
        "future_mc_multiplicity_method_prespecified",
        "future_mc_positive_selected_count_rule_prespecified",
        "validated_mc_executed",
        "validated_mc_sample_recorded",
        "validated_mc_intervals_computed",
        "current_deterministic_seed_plan_is_validated_mc",
        "operational_prediction",
        "production_observed",
        "confirmatory_evidence",
        "manuscript_claim_promoted",
        "formal_test_28_closed",
    ):
        _bool(getattr(value, name), "definition." + name, False)
    for name in (
        "outcome_status_fiber_counts",
        "rejection_first_acceptance_fiber_counts",
        "rejection_selected_value_fiber_counts",
        "sir_selected_value_fiber_counts",
        "refusal_fiber_count",
        "exhaustion_fiber_count",
        "execution_failure_fiber_count",
        "nonreturn_fiber_count",
    ):
        if getattr(value, name) is not None:
            raise ValueError("definition." + name + " must remain absent/None")
    _sha256(value.record_sha256, "definition.record_sha256")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    if value.record_sha256 != _digest("whole-seed-definition", payload):
        raise ValueError("whole-seed definition digest differs")
    return value


def _bundle_definition(
    fixture_id: str, strategy: str, budget: int
) -> WholeSeedPushforwardDefinitionV1:
    request = _request_template_sha256(fixture_id, strategy, budget)
    assumption = declare_cp60_uniform_plan_seed_assumption(
        request_template_sha256=request,
        assumption_role_sha256=_assumption_role_sha256(request),
        one_exact_uint64_seed_almost_surely_supplied_assumed=True,
        unconditional_uniform_plan_seed_assumed=True,
    )
    return define_cp60_whole_seed_pushforward(
        fixture_id=fixture_id,
        strategy=strategy,
        budget=budget,
        request_template_sha256=request,
        seed_assumption=assumption,
        kernel_v2_source_sha256=CP60_TEST28_KERNEL_V2_SOURCE_SHA256,
        reference_source_sha256=CP60_TEST28_REFERENCE_SOURCE_SHA256,
        provider_source_sha256=CP60_TEST28_PROVIDER_SOURCE_SHA256,
        exact_score_source_sha256=CP60_TEST28_EXACT_SCORE_SOURCE_SHA256,
        quota_source_sha256=CP60_TEST28_QUOTA_SOURCE_SHA256,
    )


def cp60_whole_seed_pushforward_bundle() -> CP60WholeSeedPushforwardBundleV1:
    """Return the predeclared M1/M2 rejection and SIR definition grid."""

    outcome = cp60_whole_seed_outcome_alphabet()
    ordered = tuple(
        definition
        for fixture in CP60_TEST28_FIXTURE_IDS
        for definition in (
            *(
                _bundle_definition(fixture, "bounded-rejection", budget)
                for budget in CP60_TEST28_REJECTION_BUDGET_GRID
            ),
            *(
                _bundle_definition(fixture, "fixed-budget-sir", budget)
                for budget in CP60_TEST28_SIR_BUDGET_GRID
            ),
        )
    )
    rejection = tuple(
        definition
        for definition in ordered
        if definition.strategy == "bounded-rejection"
    )
    sir = tuple(
        definition
        for definition in ordered
        if definition.strategy == "fixed-budget-sir"
    )
    values = {
        "schema_version": CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "scope": CP60_TEST28_WHOLE_SEED_SCOPE,
        "outcome_alphabet": outcome,
        "ordered_definitions": ordered,
        "rejection_definitions": rejection,
        "sir_definitions": sir,
        "fixture_ids": CP60_TEST28_FIXTURE_IDS,
        "rejection_budget_grid": CP60_TEST28_REJECTION_BUDGET_GRID,
        "sir_budget_grid": CP60_TEST28_SIR_BUDGET_GRID,
        "all_grid_templates_predeclared": True,
        "definition_only": True,
        "kernel_numpy_scipy_provider_or_rng_imported_or_executed": False,
        "runtime_dependency_map_complete": False,
        "seed_domain_exhaustively_enumerated": False,
        "numeric_fiber_counts_computed": False,
        "request_parameters_fully_bound": False,
        "fixed_request_maps_instantiated": False,
        "future_validated_mc_requirements_recorded": True,
        "validated_mc_executed": False,
        "common_mu_fp_identified": False,
        "operational_prediction": False,
        "unconditional_operational_predictions_blocker_closed": False,
        "production_observed": False,
        "confirmatory_evidence": False,
        "manuscript_claim_promoted": False,
        "formal_test_28_status": CP60_TEST28_FORMAL_TEST_28_STATUS,
        "formal_test_28_closed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("whole-seed-bundle", values)
    result = cast(
        CP60WholeSeedPushforwardBundleV1,
        _seal(CP60WholeSeedPushforwardBundleV1, values),
    )
    return validate_cp60_whole_seed_pushforward_bundle(result)


def validate_cp60_whole_seed_pushforward_bundle(
    value: object,
) -> CP60WholeSeedPushforwardBundleV1:
    if type(value) is not CP60WholeSeedPushforwardBundleV1:
        raise TypeError("whole-seed bundle has the wrong exact CP60 type")
    _validate_constant_text(
        value.schema_version,
        CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION,
        "bundle.schema_version",
    )
    _validate_constant_text(value.scope, CP60_TEST28_WHOLE_SEED_SCOPE, "bundle.scope")
    if type(value.outcome_alphabet) is not WholeSeedOutcomeAlphabetV1:
        raise TypeError("bundle outcome alphabet has the wrong exact type")
    outcome = validate_cp60_whole_seed_outcome_alphabet(value.outcome_alphabet)
    canonical_outcome = cp60_whole_seed_outcome_alphabet()
    if _canonical_bytes(outcome) != _canonical_bytes(canonical_outcome):
        raise ValueError("bundle outcome alphabet differs from frozen replay")
    if type(value.ordered_definitions) is not tuple:
        raise TypeError("bundle ordered definitions must be an exact tuple")
    if len(value.ordered_definitions) != 16:
        raise ValueError("bundle ordered definition grid has the wrong shape")
    if type(value.rejection_definitions) is not tuple:
        raise TypeError("bundle rejection definitions must be an exact tuple")
    if len(value.rejection_definitions) != 8:
        raise ValueError("bundle rejection grid has the wrong shape")
    if type(value.sir_definitions) is not tuple:
        raise TypeError("bundle SIR definitions must be an exact tuple")
    if len(value.sir_definitions) != 8:
        raise ValueError("bundle SIR grid has the wrong shape")
    expected_order = tuple(
        (fixture, strategy, budget)
        for fixture in CP60_TEST28_FIXTURE_IDS
        for strategy, grid in (
            ("bounded-rejection", CP60_TEST28_REJECTION_BUDGET_GRID),
            ("fixed-budget-sir", CP60_TEST28_SIR_BUDGET_GRID),
        )
        for budget in grid
    )
    for child, (fixture, strategy, budget) in zip(
        value.ordered_definitions, expected_order
    ):
        if type(child) is not WholeSeedPushforwardDefinitionV1:
            raise TypeError("bundle ordered child has the wrong exact type")
        checked = validate_cp60_whole_seed_pushforward(child)
        if (checked.fixture_id, checked.strategy, checked.budget) != (
            fixture,
            strategy,
            budget,
        ):
            raise ValueError("bundle canonical template order differs")
        if checked.outcome_alphabet_sha256 != outcome.record_sha256:
            raise ValueError("bundle ordered child outcome alphabet differs")
        expected_child = _bundle_definition(fixture, strategy, budget)
        if _canonical_bytes(checked) != _canonical_bytes(expected_child):
            raise ValueError("bundle ordered child differs from frozen replay")
    expected_rejection = tuple(
        (fixture, budget)
        for fixture in CP60_TEST28_FIXTURE_IDS
        for budget in CP60_TEST28_REJECTION_BUDGET_GRID
    )
    expected_sir = tuple(
        (fixture, budget)
        for fixture in CP60_TEST28_FIXTURE_IDS
        for budget in CP60_TEST28_SIR_BUDGET_GRID
    )
    projected_rejection = tuple(
        child
        for child in value.ordered_definitions
        if child.strategy == "bounded-rejection"
    )
    projected_sir = tuple(
        child
        for child in value.ordered_definitions
        if child.strategy == "fixed-budget-sir"
    )
    for child, projected, (fixture, budget) in zip(
        value.rejection_definitions, projected_rejection, expected_rejection
    ):
        if type(child) is not WholeSeedPushforwardDefinitionV1:
            raise TypeError("bundle rejection child has the wrong exact type")
        if child is not projected:
            raise ValueError("bundle rejection projection lost child identity")
        checked = validate_cp60_whole_seed_pushforward(child)
        if (checked.fixture_id, checked.strategy, checked.budget) != (
            fixture,
            "bounded-rejection",
            budget,
        ):
            raise ValueError("bundle rejection child order differs")
        if checked.outcome_alphabet_sha256 != outcome.record_sha256:
            raise ValueError("bundle rejection outcome alphabet differs")
    for child, projected, (fixture, budget) in zip(
        value.sir_definitions, projected_sir, expected_sir
    ):
        if type(child) is not WholeSeedPushforwardDefinitionV1:
            raise TypeError("bundle SIR child has the wrong exact type")
        if child is not projected:
            raise ValueError("bundle SIR projection lost child identity")
        checked = validate_cp60_whole_seed_pushforward(child)
        if (checked.fixture_id, checked.strategy, checked.budget) != (
            fixture,
            "fixed-budget-sir",
            budget,
        ):
            raise ValueError("bundle SIR child order differs")
        if checked.outcome_alphabet_sha256 != outcome.record_sha256:
            raise ValueError("bundle SIR outcome alphabet differs")
    _exact_tuple(value.fixture_ids, "bundle.fixture_ids", CP60_TEST28_FIXTURE_IDS)
    _exact_tuple(
        value.rejection_budget_grid,
        "bundle.rejection_budget_grid",
        CP60_TEST28_REJECTION_BUDGET_GRID,
    )
    _exact_tuple(
        value.sir_budget_grid, "bundle.sir_budget_grid", CP60_TEST28_SIR_BUDGET_GRID
    )
    for name in (
        "all_grid_templates_predeclared",
        "definition_only",
        "future_validated_mc_requirements_recorded",
    ):
        _bool(getattr(value, name), "bundle." + name, True)
    for name in (
        "kernel_numpy_scipy_provider_or_rng_imported_or_executed",
        "runtime_dependency_map_complete",
        "seed_domain_exhaustively_enumerated",
        "numeric_fiber_counts_computed",
        "request_parameters_fully_bound",
        "fixed_request_maps_instantiated",
        "validated_mc_executed",
        "common_mu_fp_identified",
        "operational_prediction",
        "unconditional_operational_predictions_blocker_closed",
        "production_observed",
        "confirmatory_evidence",
        "manuscript_claim_promoted",
        "formal_test_28_closed",
    ):
        _bool(getattr(value, name), "bundle." + name, False)
    _validate_constant_text(
        value.formal_test_28_status,
        CP60_TEST28_FORMAL_TEST_28_STATUS,
        "bundle.formal_test_28_status",
    )
    _sha256(value.record_sha256, "bundle.record_sha256")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    if value.record_sha256 != _digest("whole-seed-bundle", payload):
        raise ValueError("whole-seed bundle digest differs")
    return value


def cp60_canonical_json_bytes(value: object) -> bytes:
    """Encode one exact validated public CP60 record canonically."""

    if type(value) is UniformPlanSeedAssumptionV1:
        checked = validate_cp60_uniform_plan_seed_assumption(value)
    elif type(value) is WholeSeedOutcomeAlphabetV1:
        checked = validate_cp60_whole_seed_outcome_alphabet(value)
    elif type(value) is WholeSeedPushforwardDefinitionV1:
        checked = validate_cp60_whole_seed_pushforward(value)
    elif type(value) is CP60WholeSeedPushforwardBundleV1:
        checked = validate_cp60_whole_seed_pushforward_bundle(value)
    else:
        raise TypeError("canonical encoding accepts exact public CP60 records only")
    return _canonical_bytes(checked)


__all__ = (
    "CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION",
    "CP60_TEST28_WHOLE_SEED_SCOPE",
    "CP60_TEST28_UNIFORM_SEED_ASSUMPTION_MODE",
    "CP60_TEST28_UNIFORM_SEED_ASSUMPTION_SCOPE",
    "CP60_TEST28_OUTCOME_STATUSES",
    "CP60_TEST28_PREEXECUTION_REFUSAL_CLASSES",
    "CP60_TEST28_EXECUTION_FAILURE_CLASSES",
    "CP60_TEST28_REJECTION_TRACE_PAYLOAD",
    "CP60_TEST28_SIR_TRACE_PAYLOAD",
    "CP60_TEST28_TOTAL_MAP_DEFINITION",
    "CP60_TEST28_FIBER_COUNT_FORMULA",
    "CP60_TEST28_SINGLETON_FORMULA",
    "CP60_TEST28_NORMALIZATION_FORMULA",
    "CP60_TEST28_REJECTION_FIBER_FORMULA",
    "CP60_TEST28_SIR_FIBER_FORMULA",
    "CP60_TEST28_PROPOSAL_MARGINAL_FORMULA",
    "CP60_TEST28_NO_RETURNED_OUTPUT_FORMULA",
    "CP60_TEST28_FIXED_SEED_POINT_MASS_THEOREM",
    "CP60_TEST28_FUTURE_VALIDATED_MC_REQUIREMENTS",
    "CP60_TEST28_RUNTIME_BINDING_REQUIREMENTS",
    "CP60_TEST28_FORMAL_TEST_28_STATUS",
    "CP60_TEST28_FIXTURE_IDS",
    "CP60_TEST28_STRATEGIES",
    "CP60_TEST28_REJECTION_BUDGET_GRID",
    "CP60_TEST28_SIR_BUDGET_GRID",
    "CP60_TEST28_MAX_BUDGET",
    "CP60_TEST28_PLAN_SEED_BITS",
    "CP60_TEST28_PLAN_SEED_DOMAIN_SIZE",
    "CP60_TEST28_KERNEL_V2_SOURCE_SHA256",
    "CP60_TEST28_REFERENCE_SOURCE_SHA256",
    "CP60_TEST28_PROVIDER_SOURCE_SHA256",
    "CP60_TEST28_EXACT_SCORE_SOURCE_SHA256",
    "CP60_TEST28_QUOTA_SOURCE_SHA256",
    "CP60_TEST28_CP59_SOURCE_SHA256",
    "CP60_TEST28_CP49_PRECEDENT_SOURCE_SHA256",
    "UniformPlanSeedAssumptionV1",
    "WholeSeedOutcomeAlphabetV1",
    "WholeSeedPushforwardDefinitionV1",
    "CP60WholeSeedPushforwardBundleV1",
    "declare_cp60_uniform_plan_seed_assumption",
    "cp60_whole_seed_outcome_alphabet",
    "define_cp60_whole_seed_pushforward",
    "cp60_whole_seed_pushforward_bundle",
    "validate_cp60_uniform_plan_seed_assumption",
    "validate_cp60_whole_seed_outcome_alphabet",
    "validate_cp60_whole_seed_pushforward",
    "validate_cp60_whole_seed_pushforward_bundle",
    "cp60_canonical_json_bytes",
)
