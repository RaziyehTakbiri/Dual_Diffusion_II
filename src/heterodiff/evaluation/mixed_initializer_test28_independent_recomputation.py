"""Independent compact recomputation for the CP63 Test-28 rehearsal.

This module deliberately has no dependency on the CP63 runner, CP62, CP61,
the production kernel, NumPy, or SciPy.  It independently decodes the stable
JSON projection, evaluates the frozen CP58 bounded features with exact
``Fraction`` arithmetic, and maps one all-row rehearsal into the 554-entry
CP61 contribution inventory.  It does not expose the future n=2048
aggregation, confidence intervals, a decision, or a production runner.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import decimal
from decimal import Context, Decimal, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import json
import math
import struct
import threading
from typing import Mapping, Optional, Tuple, cast
import weakref


CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION = (
    "cp63-test28-independent-compact-recomputation-v1"
)
CP63_INDEPENDENT_RECOMPUTATION_SCOPE = (
    "stdlib-only-independent-stable-json-parser-and-exact-cp58-feature-"
    "recomputation;one-sixteen-row-development-rehearsal-only;"
    "no-runner-cp62-cp61-kernel-provider-numpy-scipy-import;"
    "no-full-sample-no-interval-no-decision-no-production-no-confirmatory-"
    "no-test28-closure"
)

_CP61_SOURCE_SHA256 = "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP58_SOURCE_SHA256 = "24649278e40c49bb1c7eae0f3b00a3c5694020844b986aa836b98c02c3024822"
_M1_REGISTRY_SHA256 = "314a54638d17f8dcb4b4313a92594306643254ab4a958aeb9d81efd5786a0406"
_M2_REGISTRY_SHA256 = "e740e5927d2242aa0d945f4a252a638cae6aa4757f31ed24094c188b715929e8"
_M1 = "T28-M1-Q"
_M2 = "T28-M2-Q"
_RUNNER_SCHEMA = "cp63-test28-runner-recomputation-rehearsal-v1"
_RUNNER_PURPOSE = "development-runner-rehearsal-only"
_REHEARSAL_ID = "cp63-all-row-rehearsal-v1"
_REHEARSAL_SEED_HEX = "12a5228200019dae"
_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_ZERO_SHA256 = "0" * 64
_MAX_JSON_BYTES = 8_388_608
_MAX_NODES = 262_144
_MAX_DEPTH = 64
_MAX_TEXT_BYTES = 4_096
_MAX_INTEGER_BITS = 16_384

_REJECTION_CELLS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_SIR_CELLS = (
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_ROW_SHAPES = tuple(
    (fixture, strategy, budget)
    for fixture in (_M1, _M2)
    for strategy, budgets in (
        ("bounded-rejection", (1, 4, 16, 64)),
        ("fixed-budget-sir", (8, 32, 128, 512)),
    )
    for budget in budgets
)
_SEED_FREE_REQUEST_SHA256S = (
    "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a",
    "f9f2d4f1d8aad14bbe5075b4febd763af4652fb4dda337e7a8d295b3a6045ec2",
    "4413d707c0165dbf18e88df043edd760a75d4eed44d039a611402e06de9c4eb8",
    "29f1f28fb222d258746cb7956a9ca0d65a6e97d398eddb1612720a9339eed338",
    "71701768f889fee219b854217de255f3d034202a3a66875ceade1cd55955896a",
    "bd7c4fd661bda70f29b8582c0db52d91d68fc703ae8838295a21cf9e6e55f23a",
    "801f600536240a2f6f3de0dcac8d4092c2121fd17dc14fb0ca0bfc3b0260acb8",
    "8e5458a8dfca1e49875cad53deff7447274ce3055960a0031cc07c4ec4de33e0",
    "7d32b4e85d39504864268b7ba39189f17c3171d11079638e37a6614b97a543bf",
    "17f11b448585709ef35a172e86665c83b2ea50a907caacdd400dbd8ce625771b",
    "57937405e7302fcd9b9935050050a74e4b2c2818e17d720cde1ee2a56352bcf3",
    "878797b61ec628ae5db0e882d6f3c34531468fbbc35fd92325063a3b017c1bd8",
    "bc7b374f072aa402264634bcf520834a71609af5f6705b9b8ac3079884cd0376",
    "1b60b917c4fba30085678101276fe2a210aaa82f34deb6ad4f9440a38cc3b074",
    "a88491906e47ec4f5483b638ce411b8afd4ce7b5d73f19e372ab68a405f6d81c",
    "0667c6c19a9b54db91f2167f685abdcaafcab73cbc4bcfaebcb420511ecc89c8",
)
_FIXTURE_BINDINGS = {
    _M1: {
        "source_certificate_sha256": "3b29d26b3f50d63e6a52ca5033264e2346d7b4175342ac86c20254b98b745cc3",
        "source_parameter_sha256": "7cdd3f34b36d71fdd094c8db03dd34f1bc4aa8790c76c3f3d0409ad83e5b4dff",
        "reference_parameter_sha256": "8a07e6ee27a31bbfacc7f23531ca62a02e940838dca8f7bb39d660ed5c41aefd",
        "facade_certificate_sha256": "252d79a82b71951a28b5107d40f86d4a655d86242428fdae3fed8298fa35dda6",
        "adapter_role_sha256": "e93c2bd1bb9181ed21538d15e5618753a92048f7f3b5647250db2c570df0b2fc",
        "initializer_role_sha256": "a4ccf3fd3c63ac740e723d1bf6e30bcdb155089ce0901c0c5e0dee53936f6b38",
    },
    _M2: {
        "source_certificate_sha256": "d6f6b25794d3e1759f5a169a9a3c55e94af37d498117cce6dcb0644342edb8de",
        "source_parameter_sha256": "2031ac8bc0f9cc338d7784e9aba9264d369b96b6bf87482440c673a273882044",
        "reference_parameter_sha256": "3a2a7d39b64318b7e37b760fc48b11b9421869cb3f292b590af02ac22fcbc926",
        "facade_certificate_sha256": "be672223c1806ad3fe54f251d8d4b8822ad76d2a93c2c6f9c1f01ab75314da2d",
        "adapter_role_sha256": "334d63f46dc53483717ab5017373622a7626e194e33f0de0b2d13b938abf793d",
        "initializer_role_sha256": "7c1e6a032b3da0e83756a00dc2fb6b4c28fad88bed9dcb3b548a3a79a8013677",
    },
}
_RESIDUAL_CONTEXT_SHA256 = (
    "8176a4298d195a7c4f82c579db2b23dd9fdaed9b7ffc1f687b7e980a99f1720f"
)
_RUNTIME_OBSERVATION = {
    "runtime_profile_id": "cp62-darwin-arm64-cpython3115-numpy246-scipy1171-calibration",
    "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    "python_version": "3.11.5",
    "python_implementation": "CPython",
    "python_soabi": "cpython-311-darwin",
    "platform_system": "Darwin",
    "platform_release": "25.3.0",
    "machine": "arm64",
    "byteorder": "little",
    "floating_rounding_mode": "FE_TONEAREST-0",
    "numpy_version": "2.4.6",
    "scipy_version": "1.17.1",
    "threadpoolctl_version": "3.6.0",
    "decimal_module_version": "1.70",
    "libmpdec_version": "2.5.1",
    "cp62_source_sha256": _CP62_SOURCE_SHA256,
    "kernel_source_sha256": "a8164e10239bab6d43a8d8f068cf035d9a4c8b0b29ee233bf5b0af8d75a0684c",
    "reference_source_sha256": "725ddc4011e2c6cf15f1810be6fabc404c50bd53333e34ad22bedcdf4d6497da",
    "facade_source_sha256": "8aecb4ed75d4f88b7d6b0355f2d2c5ddad685d761fe4fbe63359bda672973234",
    "exact_score_source_sha256": "87e197085ecee91ddbd78e1dfde3d0eb84797740946f76f1ee26f837d4149313",
    "quota_source_sha256": "3985d23337f854e43a6ee766d4d9a0afeed0a60fd9e37855c064c88e7477dde1",
    "full_runtime_lock_recomputed": False,
}
_PREEXECUTION_REFUSAL_CODES = (
    "plan_validation_refusal",
    "provider_reference_binding_refusal",
    "resource_preflight_refusal",
    "runtime_binding_refusal",
    "other_preexecution_refusal",
)
_EXECUTION_FAILURE_CODES = (
    "reference_sampling_failure",
    "score_evaluation_failure",
    "quota_certification_failure",
    "float64_normalization_failure",
    "categorical_selection_failure",
    "structural_result_validation_failure",
    "other_execution_failure",
)
_STABLE_KEYS = (
    "schema",
    "purpose",
    "rehearsal_id",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "seed_free_request_sha256",
    "request_instance_sha256",
    "runtime_lock_sha256",
    "phase",
    "closed_status",
    "failure_code",
    "kernel_trace",
)
_CONFIGURATION_KEYS = ("events", "cp62_configuration_sha256")
_SOURCE_EVALUATION_KEYS = (
    "fixture_id",
    "residual_context_float64_be",
    "cardinality",
    "count_penalty",
    "exact_log_weight",
    "rounded_exact_log_weight_float64_be",
    "direct_binary64_log_weight_float64_be",
    "exact_upper_bound_respected",
    "represented_restriction_identity_verified",
    "cp62_source_evaluation_sha256",
)
_FACADE_EVALUATION_KEYS = (
    "backend_kind",
    "residual_context_float64_be",
    "exact_log_weight",
    "rounded_log_weight_float64_be",
    "exact_upper_bound_respected",
    "exact_lower_bound_respected",
    "structural_validation_replayed_learned_model",
    "structural_validation_replayed_rng",
    "source_evaluation",
    "cp62_facade_evaluation_sha256",
)
_SCORED_KEYS = (
    "index",
    "configuration",
    "facade_evaluation",
    "exact_log_weight",
    "rounded_log_weight_float64_be",
    "cp62_scored_sha256",
)
_ATTEMPT_KEYS = (
    "attempt_index",
    "scored",
    "exact_delta",
    "quota",
    "decision_word_hex",
    "accepted",
    "cp62_attempt_sha256",
)
_PARTICLE_KEYS = (
    "particle_index",
    "scored",
    "normalized_weight_float64_be",
    "cp62_particle_sha256",
)
_QUOTA_TEXT_FIELDS = (
    "schema_version",
    "certificate_scope",
    "proof_policy",
    "proof_contract",
    "branch",
)
_QUOTA_INTEGER_FIELDS = (
    "delta_numerator",
    "delta_denominator",
    "precision",
    "adaptive_rounds",
    "decision_denominator",
    "quota",
    "input_lower_numerator",
    "input_lower_denominator",
    "input_upper_numerator",
    "input_upper_denominator",
    "exp_lower_numerator",
    "exp_lower_denominator",
    "exp_upper_numerator",
    "exp_upper_denominator",
)
_QUOTA_BOOLEAN_FIELDS = (
    "input_lower_strict",
    "input_upper_strict",
    "exp_lower_strict",
    "exp_upper_strict",
    "terminal_rational_inequality_certified",
    "exact_divmod_input_enclosure_certified",
    "exponential_monotonicity_transfer_certified",
    "adjacent_decimal_outward_padding_certified",
    "adaptive_nested_enclosures_certified",
    "unique_scaled_floor_certified",
    "exact_scaled_floor_under_stated_contract_certified",
    "decimal_correct_rounding_contract_required",
    "decimal_implementation_formally_verified",
    "independent_transcendental_backend_verified",
    "binary_float_exp_used",
    "external_numeric_dependency_used",
    "exact_exponential_bernoulli_certified",
    "rejection_kernel_integrated",
    "runtime_portable",
    "cryptographic_authentication",
)
_QUOTA_KEYS = (
    *_QUOTA_TEXT_FIELDS,
    *_QUOTA_INTEGER_FIELDS,
    *_QUOTA_BOOLEAN_FIELDS,
    "cp62_quota_sha256",
)
_QUOTA_SCHEMA = "arbitrary-rational-uint64-exp-quota-v1"
_QUOTA_POLICY = (
    "exact-Fraction-nonpositive-gap;terminal-rational-inequalities;"
    "exact-divmod-outward-decimal-input-bracket;monotone-exp-transfer;"
    "trusted-correctly-rounded-Decimal-exp;adjacent-context-outward-padding;"
    "adaptive-nested-rational-exp-enclosures;unique-scaled-half-open-cell;"
    "recompute-every-field-validation;fail-closed-resource-or-ambiguity-v1"
)
_QUOTA_PROOF = (
    "delta=0 is exact unity;delta<=-64 uses e>2;"
    "-2^-64<delta<0 uses 1+delta<exp(delta)<1;"
    "otherwise integer-divmod gives exact finite-decimal x_lo<=delta<=x_hi;"
    "exp monotonicity and documented correctly-rounded Decimal Context.exp,"
    "padded by next_minus/next_plus, give strict rational L<exp(delta)<U;"
    "nested L,U with floor(2^64*L)=k and 2^64*U<=k+1 prove the exact floor;"
    "Hermite-Lindemann excludes an exact scaled integer tie for nonzero "
    "rational delta but finite precision exhaustion still fails closed;"
    "adaptive claims are conditional on the recorded trusted unchanged "
    "Python-Decimal-libmpdec contract and are not formal verification"
)
_QUOTA_SCOPE = (
    "standalone-exact-scaled-floor-certificate-under-frozen-decimal-contract;"
    "arbitrary-bounded-exact-rational-delta;no-binary64-exp;no-external-"
    "numeric-dependency;not-runtime-portable;not-formal-libmpdec-verification;"
    "not-exact-exp-bernoulli;not-rejection-kernel-integration;"
    "not-initializer-target-path-sampler-or-test28-admission"
)
_SEMANTIC_TRACE_KEYS = (
    "trace_schema",
    "stable_request_sha256",
    "calibration_instance_sha256",
    "plan_seed_hex",
    "fixture_id",
    "strategy",
    "budget",
    "source_certificate_sha256",
    "source_parameter_sha256",
    "reference_parameter_sha256",
    "facade_certificate_sha256",
    "adapter_role_sha256",
    "initializer_role_sha256",
    "residual_context_sha256",
    "runtime_observation",
    "exact_log_weight_upper_bound",
    "exact_log_weight_lower_bound",
    "proposal_seed_hex",
    "rejection_decision_seed_hex",
    "sir_resampling_seed_hex",
    "resource_preflight",
    "explicit_rejection_exhaustion",
    "structural_result_validation_replays_provider_evaluate",
    "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation",
    "structural_result_validation_replays_reference_sampler",
    "structural_result_validation_replays_rng",
    "operational_reference_sampling_law_verified",
    "philox_uniformity_verified",
    "stream_independence_verified",
    "iid_proposals_verified",
    "analytic_target_equality_verified",
    "exact_operational_rejection_bernoulli_verified",
    "finite_j_sir_exact_target_verified",
    "source_or_model_quality_evidence",
    "path_or_sampler_admitted",
    "formal_test_28_closed",
    "result_status",
    "proposal_stream_initial_state_sha256",
    "proposal_stream_final_state_sha256",
    "decision_stream_initial_state_sha256",
    "decision_stream_final_state_sha256",
    "resampling_stream_initial_state_sha256",
    "resampling_stream_final_state_sha256",
    "resampling_word_hex",
    "resampling_uniform_53",
    "effective_sample_size_float64_be",
    "maximum_normalized_weight_float64_be",
    "ess_warning",
    "attempts",
    "particles",
    "normalized_weights_float64_be",
    "selected_index",
    "selected_configuration",
    "cp62_semantic_trace_sha256",
)
_CLOSED_SEMANTIC_TRACE_KEYS = (
    "trace_schema",
    "stable_request_sha256",
    "calibration_instance_sha256",
    "plan_seed_hex",
    "fixture_id",
    "strategy",
    "budget",
    "source_certificate_sha256",
    "source_parameter_sha256",
    "reference_parameter_sha256",
    "facade_certificate_sha256",
    "adapter_role_sha256",
    "initializer_role_sha256",
    "residual_context_sha256",
    "runtime_lock_sha256",
    "runtime_observation",
    "outcome_kind",
    "failure_code",
    "completed_kernel_trace_present",
    "timeout_is_semantic_nonreturn",
    "cp62_closed_trace_sha256",
)


class CP63IndependentRecomputationError(ValueError):
    """Fail-closed error for the independent CP63 boundary."""


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP63 independent records are module-created")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP63 independent records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63CompactObservationV1(_SealedRecord):
    schema_version: str
    seed_ordinal: int
    row_ordinal: int
    logical_request_ordinal: int
    row_key: str
    fixture_id: str
    strategy: str
    budget: int
    plan_seed_hex: str
    seed_free_request_sha256: str
    request_instance_sha256: str
    runtime_lock_sha256: str
    stable_trace_sha256: str
    observable_cell_label: str
    observable_contribution_ordinal: int
    first_selected_attempt_one_based: Optional[int]
    selected: bool
    selected_feature_ids: Tuple[str, ...]
    selected_feature_values: Tuple[Fraction, ...]
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP63CompactObservationV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63RehearsalRecomputationReceiptV1(_SealedRecord):
    schema_version: str
    request_count: int
    row_ordinals: Tuple[int, ...]
    logical_request_ordinals: Tuple[int, ...]
    stable_trace_sha256s: Tuple[str, ...]
    compact_observation_sha256s: Tuple[str, ...]
    observable_contributions: Tuple[int, ...]
    first_attempt_contributions: Tuple[int, ...]
    selected_feature_present: Tuple[bool, ...]
    selected_feature_values: Tuple[Optional[Fraction], ...]
    missing_count: int
    duplicate_count: int
    invalid_count: int
    independent_parser: bool
    runner_source_imported: bool
    intervals_computed: bool
    decision_made: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP63RehearsalRecomputationReceiptV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63IndependentRecomputationBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    cp61_source_sha256: str
    cp61_stable_design_sha256: str
    cp58_source_sha256: str
    m1_feature_registry_sha256: str
    m2_feature_registry_sha256: str
    row_count: int
    observable_estimand_ids: Tuple[str, ...]
    rejection_first_attempt_estimand_ids: Tuple[str, ...]
    selected_feature_estimand_ids: Tuple[str, ...]
    observable_estimand_count: int
    rejection_first_attempt_estimand_count: int
    selected_feature_estimand_count: int
    estimand_count: int
    compact_projection_formula: str
    independent_parser: bool
    runner_source_imported: bool
    cp62_source_imported: bool
    kernel_or_numerical_dependency_imported: bool
    full_32768_recomputation_exposed: bool
    n2048_intervals_computed: bool
    decision_made: bool
    runner_and_recomputation_blocker_closed: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP63IndependentRecomputationBundleV1 cannot be subclassed")


_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS: weakref.WeakKeyDictionary[
    _SealedRecord, bytes
] = weakref.WeakKeyDictionary()


def _record(cls: type, domain: bytes, values: Mapping[str, object]) -> object:
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP63 independent sealed field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    complete["record_sha256"] = hashlib.sha256(
        domain + b"\0" + _canonical_json_bytes(complete)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _canonical_json_bytes(result)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = snapshot
    return result


def _canonical(value: object, *, depth: int = 0, budget: list[int]) -> object:
    if depth > _MAX_DEPTH:
        raise ValueError("CP63 independent canonical depth exceeded")
    budget[0] += 1
    if budget[0] > _MAX_NODES:
        raise ValueError("CP63 independent canonical node cap exceeded")
    if value is None or type(value) in (bool, str):
        if type(value) is str and len(value.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise ValueError("CP63 independent canonical text is oversized")
        return value
    if type(value) is int:
        if value.bit_length() > _MAX_INTEGER_BITS:
            raise ValueError("CP63 independent canonical integer is oversized")
        return value
    if type(value) is Fraction:
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > (
            _MAX_INTEGER_BITS
        ):
            raise ValueError("CP63 independent canonical fraction is oversized")
        return {"$fraction": [str(value.numerator), str(value.denominator)]}
    if type(value) is tuple:
        return [_canonical(item, depth=depth + 1, budget=budget) for item in value]
    if isinstance(value, _SealedRecord):
        return {
            item.name: _canonical(
                getattr(value, item.name), depth=depth + 1, budget=budget
            )
            for item in fields(type(value))
        }
    if type(value) is dict:
        keys = tuple(value.keys())
        if any(type(key) is not str for key in keys):
            raise TypeError("CP63 independent canonical keys must be exact text")
        return {
            key: _canonical(value[key], depth=depth + 1, budget=budget)
            for key in sorted(keys)
        }
    raise TypeError("unsupported CP63 independent canonical value")


def _canonical_json_bytes(value: object) -> bytes:
    encoded = json.dumps(
        _canonical(value, budget=[0]),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if len(encoded) > _MAX_JSON_BYTES:
        raise ValueError("CP63 independent canonical output is oversized")
    return encoded


def _row_key(row_ordinal: int) -> str:
    fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    return "row-%02d/%s/%s/budget-%d" % (
        row_ordinal,
        fixture,
        strategy,
        budget,
    )


def _projections(fixture_id: str) -> Tuple[Tuple[int, str, Tuple[Fraction, ...]], ...]:
    if fixture_id == _M1:
        return ((1, "axis0", (Fraction(1),)),)
    return (
        (0, "axis0", (Fraction(1),)),
        (1, "axis0", (Fraction(1), Fraction(0))),
        (1, "axis1", (Fraction(0), Fraction(1))),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )


def _feature_ids(fixture_id: str) -> Tuple[str, ...]:
    cap = 1 if fixture_id == _M1 else 2
    dimensions = (0, 1) if fixture_id == _M1 else (1, 2)
    projections = _projections(fixture_id)
    result = ["count/eq/%d" % count for count in range(cap + 1)]
    result.extend("type/%d/occupancy" % index for index in range(len(dimensions)))
    for type_index, projection_id, _coefficients in projections:
        result.extend(
            (
                "coordinate/%d/%s/odd" % (type_index, projection_id),
                "coordinate/%d/%s/even" % (type_index, projection_id),
            )
        )
    if cap == 2:
        by_type = {
            type_index: tuple(item for item in projections if item[0] == type_index)
            for type_index in range(len(dimensions))
        }
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                result.append("pair-type/%d/%d" % (left_type, right_type))
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left in enumerate(by_type[left_type]):
                    for right_position, right in enumerate(by_type[right_type]):
                        if left_type == right_type and right_position < left_position:
                            continue
                        result.append(
                            "pair-projection/%d/%s/%d/%s"
                            % (left_type, left[1], right_type, right[1])
                        )
    return tuple(result)


def _estimand_ids() -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    observable = []
    first = []
    features = []
    for row_ordinal, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        key = _row_key(row_ordinal)
        cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        observable.extend("cp61/observable/%s/%s" % (key, cell) for cell in cells)
        if strategy == "bounded-rejection":
            first.extend(
                "cp61/rejection-first-attempt/%s/attempt-%d" % (key, attempt)
                for attempt in range(1, budget + 1)
            )
        features.extend(
            "cp61/selected-feature/%s/%s" % (key, feature_id)
            for feature_id in _feature_ids(_fixture)
        )
    return tuple(observable), tuple(first), tuple(features)


def _contribution_ordinals(
    row_ordinal: int,
    observable_cell_label: str,
    first_selected_attempt_one_based: Optional[int],
) -> Tuple[int, Tuple[int, ...]]:
    observable_offset = 0
    first_offset = 0
    for current, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        if current == row_ordinal:
            try:
                observable_ordinal = (
                    observable_offset + cells.index(observable_cell_label) + 1
                )
            except ValueError as error:
                raise CP63IndependentRecomputationError(
                    "observable cell is not in the row family"
                ) from error
            if strategy == "bounded-rejection" and first_selected_attempt_one_based:
                if not 1 <= first_selected_attempt_one_based <= budget:
                    raise CP63IndependentRecomputationError(
                        "first-selected attempt is outside the row budget"
                    )
                first_ordinals = (first_offset + first_selected_attempt_one_based,)
            else:
                first_ordinals = ()
            return observable_ordinal, first_ordinals
        observable_offset += len(cells)
        if strategy == "bounded-rejection":
            first_offset += budget
    raise CP63IndependentRecomputationError("row ordinal is outside the inventory")


def _bundle() -> CP63IndependentRecomputationBundleV1:
    observable, first, selected = _estimand_ids()
    if (len(observable), len(first), len(selected)) != (72, 170, 312):
        raise AssertionError("CP63 independent frozen estimand inventory differs")
    return cast(
        CP63IndependentRecomputationBundleV1,
        _record(
            CP63IndependentRecomputationBundleV1,
            b"cp63-independent-recomputation-bundle-v1",
            {
                "schema_version": CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION,
                "scope": CP63_INDEPENDENT_RECOMPUTATION_SCOPE,
                "cp61_source_sha256": _CP61_SOURCE_SHA256,
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "cp58_source_sha256": _CP58_SOURCE_SHA256,
                "m1_feature_registry_sha256": _M1_REGISTRY_SHA256,
                "m2_feature_registry_sha256": _M2_REGISTRY_SHA256,
                "row_count": 16,
                "observable_estimand_ids": observable,
                "rejection_first_attempt_estimand_ids": first,
                "selected_feature_estimand_ids": selected,
                "observable_estimand_count": 72,
                "rejection_first_attempt_estimand_count": 170,
                "selected_feature_estimand_count": 312,
                "estimand_count": 554,
                "compact_projection_formula": (
                    "independently-parse-one-complete-canonical-stable-trace;"
                    "emit-one-of-the-row-observable-cells;emit-the-one-based-"
                    "first-selected-rejection-attempt-only-for-a-selected-"
                    "rejection-return;and-only-for-a-selected-return-evaluate-"
                    "the-complete-applicable-cp58-feature-registry-with-exact-"
                    "fraction-arithmetic"
                ),
                "independent_parser": True,
                "runner_source_imported": False,
                "cp62_source_imported": False,
                "kernel_or_numerical_dependency_imported": False,
                "full_32768_recomputation_exposed": False,
                "n2048_intervals_computed": False,
                "decision_made": False,
                "runner_and_recomputation_blocker_closed": False,
                "confirmatory_evidence": False,
                "manuscript_claim": False,
                "formal_test_28_status": "OPEN",
                "formal_test_28_closed": False,
            },
        ),
    )


def cp63_independent_recomputation_bundle() -> CP63IndependentRecomputationBundleV1:
    """Return the independent, rehearsal-only recomputation contract."""

    return _bundle()


def _duplicate_rejecting_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CP63IndependentRecomputationError("duplicate JSON key")
        result[key] = value
    return result


def _parse_bounded_integer(text: str) -> int:
    if len(text) > 5_000:
        raise CP63IndependentRecomputationError("JSON integer is oversized")
    try:
        value = int(text, 10)
    except ValueError as error:
        raise CP63IndependentRecomputationError("JSON integer is invalid") from error
    if value.bit_length() > _MAX_INTEGER_BITS:
        raise CP63IndependentRecomputationError("JSON integer is oversized")
    return value


def _reject_json_float(_text: str) -> object:
    raise CP63IndependentRecomputationError("JSON floats are forbidden")


def _walk_json(value: object, *, depth: int = 0, budget: list[int]) -> None:
    if depth > _MAX_DEPTH:
        raise CP63IndependentRecomputationError("stable JSON depth exceeded")
    budget[0] += 1
    if budget[0] > _MAX_NODES:
        raise CP63IndependentRecomputationError("stable JSON node cap exceeded")
    if value is None or type(value) in (bool, int, str):
        if type(value) is int and value.bit_length() > _MAX_INTEGER_BITS:
            raise CP63IndependentRecomputationError("stable integer is oversized")
        if type(value) is str and len(value.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise CP63IndependentRecomputationError("stable text is oversized")
        return
    if type(value) is list:
        for item in value:
            _walk_json(item, depth=depth + 1, budget=budget)
        return
    if type(value) is dict:
        keys = tuple(value.keys())
        if any(type(key) is not str for key in keys):
            raise CP63IndependentRecomputationError("stable key is not exact text")
        if any(len(key.encode("utf-8")) > _MAX_TEXT_BYTES for key in keys):
            raise CP63IndependentRecomputationError("stable key is oversized")
        for key in keys:
            _walk_json(value[key], depth=depth + 1, budget=budget)
        return
    raise CP63IndependentRecomputationError("stable payload is not plain JSON")


def _sha256(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise CP63IndependentRecomputationError(name + " is not SHA-256 text")
    return value


def _uint64_hex(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 16
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise CP63IndependentRecomputationError(name + " is not uint64 hex")
    return value


def _rehearsal_request_instance_sha256(row_ordinal: int) -> str:
    fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    identity = {
        "schema": _RUNNER_SCHEMA,
        "rehearsal_id": _REHEARSAL_ID,
        "seed_ordinal": 1,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": row_ordinal,
        "row_key": _row_key(row_ordinal),
        "fixture_id": fixture,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "seed_free_request_sha256": _SEED_FREE_REQUEST_SHA256S[row_ordinal - 1],
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    }
    return hashlib.sha256(
        b"cp63-test28-rehearsal-request-instance-v1\0" + _plain_json_bytes(identity)
    ).hexdigest()


def cp63_independently_validate_stable_trace_bytes(payload: object) -> dict:
    """Decode canonical CP63 stable bytes without importing the runner."""

    if type(payload) is not bytes:
        raise TypeError("stable trace payload must be exact bytes")
    if (
        not payload
        or len(payload) > _MAX_JSON_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
    ):
        raise CP63IndependentRecomputationError("stable trace byte bounds differ")
    try:
        value = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=_duplicate_rejecting_object,
            parse_float=_reject_json_float,
            parse_int=_parse_bounded_integer,
            parse_constant=_reject_json_float,
        )
    except CP63IndependentRecomputationError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as error:
        raise CP63IndependentRecomputationError(
            "stable trace JSON is invalid"
        ) from error
    _walk_json(value, budget=[0])
    if type(value) is not dict or _plain_json_bytes(value) != payload:
        raise CP63IndependentRecomputationError("stable trace is not canonical JSON")
    if set(value) != set(_STABLE_KEYS):
        raise CP63IndependentRecomputationError("stable trace field set differs")
    if (
        value["schema"] != _RUNNER_SCHEMA
        or value["purpose"] != _RUNNER_PURPOSE
        or value["rehearsal_id"] != _REHEARSAL_ID
    ):
        raise CP63IndependentRecomputationError(
            "stable schema, purpose, or rehearsal id differs"
        )
    row = value["row_ordinal"]
    if type(row) is not int or not 1 <= row <= 16:
        raise CP63IndependentRecomputationError("stable row ordinal differs")
    fixture, strategy, budget = _ROW_SHAPES[row - 1]
    exact = {
        "seed_ordinal": 1,
        "logical_request_ordinal": row,
        "row_key": _row_key(row),
        "fixture_id": fixture,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "seed_free_request_sha256": _SEED_FREE_REQUEST_SHA256S[row - 1],
        "request_instance_sha256": _rehearsal_request_instance_sha256(row),
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    }
    for field, wanted in exact.items():
        if type(value[field]) is not type(wanted) or value[field] != wanted:
            raise CP63IndependentRecomputationError("stable trace %s differs" % field)
    phase = value["phase"]
    status = value["closed_status"]
    failure = value["failure_code"]
    if phase == "returned-before-deadline":
        allowed = (
            _REJECTION_CELLS[:2] if strategy == "bounded-rejection" else _SIR_CELLS[:1]
        )
        if status not in allowed or failure is not None:
            raise CP63IndependentRecomputationError("returned stable arm differs")
    elif phase == "preexecution-refusal-before-deadline":
        if status != phase or failure not in _PREEXECUTION_REFUSAL_CODES:
            raise CP63IndependentRecomputationError("refusal stable arm differs")
    elif phase == "execution-failure-before-deadline":
        if status != phase or failure not in _EXECUTION_FAILURE_CODES:
            raise CP63IndependentRecomputationError("failure stable arm differs")
    elif phase == "timeout-at-deadline":
        if status != "timeout-censored-at-deadline" or failure is not None:
            raise CP63IndependentRecomputationError("timeout stable arm differs")
    else:
        raise CP63IndependentRecomputationError("stable phase differs")
    _validate_kernel_trace(value["kernel_trace"], value)
    return value


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _exact_keys(value: object, expected: Tuple[str, ...], name: str) -> dict:
    if type(value) is not dict:
        raise CP63IndependentRecomputationError(name + " is not an exact object")
    keys = tuple(value.keys())
    if any(
        type(key) is not str or not key or len(key.encode("utf-8")) > _MAX_TEXT_BYTES
        for key in keys
    ):
        raise CP63IndependentRecomputationError(name + " has invalid keys")
    if len(keys) != len(expected) or set(keys) != set(expected):
        raise CP63IndependentRecomputationError(name + " field set differs")
    return value


def _verify_owned_leaf(value: dict, field: str, domain: bytes, name: str) -> None:
    supplied = _sha256(value[field], name + " digest")
    body = dict(value)
    body.pop(field)
    expected = hashlib.sha256(domain + b"\0" + _plain_json_bytes(body)).hexdigest()
    if supplied != expected:
        raise CP63IndependentRecomputationError(name + " digest differs")


def _decimal_integer_text(
    value: object, name: str, *, minimum: Optional[int] = None
) -> int:
    if type(value) is not str or not value or len(value) > 5_000:
        raise CP63IndependentRecomputationError(name + " is not bounded decimal text")
    try:
        parsed = int(value, 10)
    except ValueError as error:
        raise CP63IndependentRecomputationError(name + " is invalid") from error
    if str(parsed) != value or parsed.bit_length() > _MAX_INTEGER_BITS:
        raise CP63IndependentRecomputationError(name + " is noncanonical")
    if minimum is not None and parsed < minimum:
        raise CP63IndependentRecomputationError(name + " is below its minimum")
    return parsed


def _fraction_tag(value: object, name: str) -> Fraction:
    checked = _exact_keys(value, ("$fraction",), name)
    parts = checked["$fraction"]
    if type(parts) is not list or len(parts) != 2:
        raise CP63IndependentRecomputationError(name + " is not an exact pair")
    numerator = _decimal_integer_text(parts[0], name + " numerator")
    denominator = _decimal_integer_text(parts[1], name + " denominator", minimum=1)
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        raise CP63IndependentRecomputationError(name + " is not reduced")
    return result


def _optional_float_value(value: object, name: str) -> Optional[float]:
    if value is None:
        return None
    return float(_float_tag(value, name))


def _configuration_value(
    value: object, *, fixture_id: str, name: str
) -> Tuple[tuple, ...]:
    checked = _exact_keys(value, _CONFIGURATION_KEYS, name)
    events = checked["events"]
    cap = 1 if fixture_id == _M1 else 2
    dimensions = (0, 1) if fixture_id == _M1 else (1, 2)
    if type(events) is not list or len(events) > cap:
        raise CP63IndependentRecomputationError(name + " cardinality differs")
    result = []
    prior = None
    for index, event in enumerate(events):
        item = _exact_keys(
            event,
            ("event_type", "coordinates_float64_be"),
            "%s event %d" % (name, index),
        )
        event_type = item["event_type"]
        if type(event_type) is not int or not 0 <= event_type < len(dimensions):
            raise CP63IndependentRecomputationError(name + " event type differs")
        coordinates = item["coordinates_float64_be"]
        if type(coordinates) is not list or len(coordinates) != dimensions[event_type]:
            raise CP63IndependentRecomputationError(name + " event dimension differs")
        exact_coordinates = tuple(
            _float_tag(coordinate, name + " coordinate") for coordinate in coordinates
        )
        ordering_key = (event_type, exact_coordinates)
        if prior is not None and ordering_key < prior:
            raise CP63IndependentRecomputationError(name + " is noncanonical")
        prior = ordering_key
        result.append(ordering_key)
    _verify_owned_leaf(
        checked,
        "cp62_configuration_sha256",
        b"cp62-test28-configuration-v1",
        name,
    )
    return tuple(result)


def _fixture_score(
    fixture_id: str, configuration: Tuple[tuple, ...]
) -> Tuple[Fraction, Fraction, float]:
    penalty = (
        Fraction(-1, 4)
        if fixture_id == _M2 and len(configuration) == 2
        else Fraction(0)
    )
    score = penalty
    direct = float(penalty)
    for event_type, coordinates in configuration:
        if fixture_id == _M1:
            coefficients = () if event_type == 0 else (Fraction(1, 4),)
        else:
            coefficients = (
                (Fraction(1, 4),)
                if event_type == 0
                else (Fraction(1, 8), Fraction(1, 6))
            )
        score -= sum(
            (
                coefficient * coordinate * coordinate
                for coefficient, coordinate in zip(coefficients, coordinates)
            ),
            Fraction(0),
        )
        for coefficient, coordinate in zip(coefficients, coordinates):
            coordinate_float = float(coordinate)
            direct -= float(coefficient) * (coordinate_float * coordinate_float)
    if direct == 0.0:
        direct = 0.0
    return score, penalty, direct


def _validate_source_evaluation(
    value: object,
    *,
    fixture_id: str,
    configuration: Tuple[tuple, ...],
    name: str,
) -> dict:
    checked = _exact_keys(value, _SOURCE_EVALUATION_KEYS, name)
    exact, penalty, direct_expected = _fixture_score(fixture_id, configuration)
    if (
        checked["fixture_id"] != fixture_id
        or checked["residual_context_float64_be"] != []
        or type(checked["cardinality"]) is not int
        or checked["cardinality"] != len(configuration)
        or _fraction_tag(checked["count_penalty"], name + " count penalty") != penalty
        or _fraction_tag(checked["exact_log_weight"], name + " exact score") != exact
        or checked["exact_upper_bound_respected"] is not True
        or checked["represented_restriction_identity_verified"] is not True
    ):
        raise CP63IndependentRecomputationError(name + " semantics differ")
    rounded = _optional_float_value(
        checked["rounded_exact_log_weight_float64_be"], name + " rounded score"
    )
    direct = _optional_float_value(
        checked["direct_binary64_log_weight_float64_be"], name + " direct score"
    )
    expected_float = float(exact)
    if rounded != expected_float or direct != direct_expected:
        raise CP63IndependentRecomputationError(name + " binary64 layers differ")
    _verify_owned_leaf(
        checked,
        "cp62_source_evaluation_sha256",
        b"cp62-test28-source-evaluation-v1",
        name,
    )
    return checked


def _validate_scored(
    value: object, *, index: int, fixture_id: str, name: str
) -> Tuple[dict, Tuple[tuple, ...], Fraction]:
    checked = _exact_keys(value, _SCORED_KEYS, name)
    if checked["index"] != index or type(checked["index"]) is not int:
        raise CP63IndependentRecomputationError(name + " index differs")
    configuration = _configuration_value(
        checked["configuration"], fixture_id=fixture_id, name=name + " configuration"
    )
    facade = _exact_keys(
        checked["facade_evaluation"], _FACADE_EVALUATION_KEYS, name + " facade"
    )
    if (
        facade["backend_kind"] != "exact-rational-quadratic-initial-tilt-v1"
        or facade["residual_context_float64_be"] != []
        or facade["exact_upper_bound_respected"] is not True
        or facade["exact_lower_bound_respected"] is not None
        or facade["structural_validation_replayed_learned_model"] is not False
        or facade["structural_validation_replayed_rng"] is not False
    ):
        raise CP63IndependentRecomputationError(name + " facade semantics differ")
    source = _validate_source_evaluation(
        facade["source_evaluation"],
        fixture_id=fixture_id,
        configuration=configuration,
        name=name + " source",
    )
    exact = _fraction_tag(checked["exact_log_weight"], name + " exact score")
    if exact != _fraction_tag(
        facade["exact_log_weight"], name + " facade exact score"
    ) or exact != _fraction_tag(
        source["exact_log_weight"], name + " source exact score"
    ):
        raise CP63IndependentRecomputationError(name + " score layers differ")
    scored_rounded = _optional_float_value(
        checked["rounded_log_weight_float64_be"], name + " rounded score"
    )
    facade_rounded = _optional_float_value(
        facade["rounded_log_weight_float64_be"], name + " facade rounded score"
    )
    if scored_rounded != facade_rounded or scored_rounded != float(exact):
        raise CP63IndependentRecomputationError(name + " rounded score differs")
    _verify_owned_leaf(
        facade,
        "cp62_facade_evaluation_sha256",
        b"cp62-test28-facade-evaluation-v1",
        name + " facade",
    )
    _verify_owned_leaf(
        checked,
        "cp62_scored_sha256",
        b"cp62-test28-scored-slot-v1",
        name,
    )
    return checked, configuration, exact


def _quota_precision_schedule() -> Tuple[int, ...]:
    result = []
    precision = 192
    while precision < 3_072:
        result.append(precision)
        precision *= 2
    result.append(3_072)
    return tuple(result)


def _quota_decimal_context(precision: int) -> Context:
    return Context(
        prec=precision,
        rounding=ROUND_HALF_EVEN,
        Emin=-999_999,
        Emax=999_999,
        clamp=0,
        traps=[
            decimal.InvalidOperation,
            decimal.DivisionByZero,
            decimal.Overflow,
            decimal.Underflow,
        ],
    )


def _scaled_decimal(coefficient: int, places: int) -> Decimal:
    digits = tuple(int(character) for character in str(abs(coefficient)))
    return Decimal((1 if coefficient < 0 else 0, digits, -places))


def _quota_adaptive_enclosure(
    delta: Fraction, precision: int
) -> Tuple[Fraction, Fraction, Fraction, Fraction]:
    scale = 10**precision
    lower_coefficient, remainder = divmod(delta.numerator * scale, delta.denominator)
    upper_coefficient = lower_coefficient if remainder == 0 else lower_coefficient + 1
    lower_decimal = _scaled_decimal(lower_coefficient, precision)
    upper_decimal = _scaled_decimal(upper_coefficient, precision)
    context = _quota_decimal_context(precision)
    rounded_lower = context.exp(lower_decimal)
    rounded_upper = context.exp(upper_decimal)
    exp_lower = Fraction(context.next_minus(rounded_lower))
    exp_upper = Fraction(context.next_plus(rounded_upper))
    return (
        Fraction(lower_coefficient, scale),
        Fraction(upper_coefficient, scale),
        exp_lower,
        exp_upper,
    )


def _expected_quota_semantics(delta: Fraction) -> dict:
    denominator = 2**64
    precision = 0
    rounds = 0
    input_lower = input_upper = delta
    if delta == 0:
        branch = "unity"
        exp_lower = exp_upper = Fraction(1)
        quota = denominator
        input_lower_strict = input_upper_strict = False
        exp_lower_strict = exp_upper_strict = False
        decimal_required = False
    elif delta <= -64:
        branch = "below_uint64_resolution"
        exp_lower, exp_upper, quota = Fraction(0), Fraction(1, denominator), 0
        input_lower_strict = input_upper_strict = False
        exp_lower_strict = exp_upper_strict = True
        decimal_required = False
    elif delta > Fraction(-1, denominator):
        branch = "below_one_uint64_cell"
        exp_lower = Fraction(denominator - 1, denominator)
        exp_upper = Fraction(1)
        quota = denominator - 1
        input_lower_strict = input_upper_strict = False
        exp_lower_strict = exp_upper_strict = True
        decimal_required = False
    else:
        branch = "adaptive_decimal_rational_input"
        quota = -1
        previous = None
        for rounds, precision in enumerate(_quota_precision_schedule(), 1):
            input_lower, input_upper, exp_lower, exp_upper = _quota_adaptive_enclosure(
                delta, precision
            )
            if previous is not None and not (
                previous[0] <= exp_lower <= exp_upper <= previous[1]
            ):
                raise CP63IndependentRecomputationError(
                    "independent quota enclosures are not nested"
                )
            previous = (exp_lower, exp_upper)
            scaled_lower = denominator * exp_lower
            scaled_upper = denominator * exp_upper
            candidate = scaled_lower.numerator // scaled_lower.denominator
            if scaled_lower >= candidate and scaled_upper <= candidate + 1:
                quota = candidate
                break
        if quota < 0:
            raise CP63IndependentRecomputationError(
                "independent quota replay exhausted precision"
            )
        input_lower_strict = input_lower < delta
        input_upper_strict = delta < input_upper
        exp_lower_strict = exp_upper_strict = True
        decimal_required = True
    result = {
        "schema_version": _QUOTA_SCHEMA,
        "certificate_scope": _QUOTA_SCOPE,
        "proof_policy": _QUOTA_POLICY,
        "proof_contract": _QUOTA_PROOF,
        "delta_numerator": str(delta.numerator),
        "delta_denominator": str(delta.denominator),
        "branch": branch,
        "precision": str(precision),
        "adaptive_rounds": str(rounds),
        "decision_denominator": str(denominator),
        "quota": str(quota),
        "input_lower_numerator": str(input_lower.numerator),
        "input_lower_denominator": str(input_lower.denominator),
        "input_upper_numerator": str(input_upper.numerator),
        "input_upper_denominator": str(input_upper.denominator),
        "exp_lower_numerator": str(exp_lower.numerator),
        "exp_lower_denominator": str(exp_lower.denominator),
        "exp_upper_numerator": str(exp_upper.numerator),
        "exp_upper_denominator": str(exp_upper.denominator),
        "input_lower_strict": input_lower_strict,
        "input_upper_strict": input_upper_strict,
        "exp_lower_strict": exp_lower_strict,
        "exp_upper_strict": exp_upper_strict,
        "terminal_rational_inequality_certified": not decimal_required,
        "exact_divmod_input_enclosure_certified": decimal_required,
        "exponential_monotonicity_transfer_certified": decimal_required,
        "adjacent_decimal_outward_padding_certified": decimal_required,
        "adaptive_nested_enclosures_certified": decimal_required,
        "unique_scaled_floor_certified": True,
        "exact_scaled_floor_under_stated_contract_certified": True,
        "decimal_correct_rounding_contract_required": decimal_required,
        "decimal_implementation_formally_verified": False,
        "independent_transcendental_backend_verified": False,
        "binary_float_exp_used": False,
        "external_numeric_dependency_used": False,
        "exact_exponential_bernoulli_certified": False,
        "rejection_kernel_integrated": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
    }
    return result


def _validate_quota(value: object, *, delta: Fraction, name: str) -> Tuple[dict, int]:
    checked = _exact_keys(value, _QUOTA_KEYS, name)
    for field in _QUOTA_TEXT_FIELDS:
        if type(checked[field]) is not str or not checked[field]:
            raise CP63IndependentRecomputationError(name + " text field differs")
    integers = {}
    for field in _QUOTA_INTEGER_FIELDS:
        minimum = 1 if field.endswith("denominator") else None
        integers[field] = _decimal_integer_text(
            checked[field], name + " " + field, minimum=minimum
        )
    if (
        integers["decision_denominator"] != 2**64
        or not 0 <= integers["quota"] <= 2**64
        or Fraction(integers["delta_numerator"], integers["delta_denominator"]) != delta
    ):
        raise CP63IndependentRecomputationError(name + " arithmetic fields differ")
    for field in _QUOTA_BOOLEAN_FIELDS:
        if type(checked[field]) is not bool:
            raise CP63IndependentRecomputationError(name + " boolean field differs")
    expected_semantics = _expected_quota_semantics(delta)
    if any(checked[field] != wanted for field, wanted in expected_semantics.items()):
        raise CP63IndependentRecomputationError(name + " exact replay differs")
    _verify_owned_leaf(
        checked,
        "cp62_quota_sha256",
        b"cp62-test28-quota-certificate-v1",
        name,
    )
    return checked, integers["quota"]


def _validate_attempt(
    value: object, *, index: int, fixture_id: str, name: str
) -> Tuple[dict, Tuple[tuple, ...], bool]:
    checked = _exact_keys(value, _ATTEMPT_KEYS, name)
    if checked["attempt_index"] != index or type(checked["attempt_index"]) is not int:
        raise CP63IndependentRecomputationError(name + " index differs")
    _scored, configuration, exact = _validate_scored(
        checked["scored"], index=index, fixture_id=fixture_id, name=name + " scored"
    )
    delta = _fraction_tag(checked["exact_delta"], name + " delta")
    if delta != exact or delta > 0:
        raise CP63IndependentRecomputationError(name + " delta differs from q-U")
    _quota, quota_value = _validate_quota(
        checked["quota"], delta=delta, name=name + " quota"
    )
    word = int(_uint64_hex(checked["decision_word_hex"], name + " word"), 16)
    accepted = checked["accepted"]
    if type(accepted) is not bool or accepted != (word < quota_value):
        raise CP63IndependentRecomputationError(name + " acceptance differs")
    _verify_owned_leaf(
        checked,
        "cp62_attempt_sha256",
        b"cp62-test28-rejection-attempt-v1",
        name,
    )
    return checked, configuration, accepted


def _validate_particle(
    value: object, *, index: int, fixture_id: str, name: str
) -> Tuple[dict, Tuple[tuple, ...], float]:
    checked = _exact_keys(value, _PARTICLE_KEYS, name)
    if checked["particle_index"] != index or type(checked["particle_index"]) is not int:
        raise CP63IndependentRecomputationError(name + " index differs")
    _scored, configuration, _exact = _validate_scored(
        checked["scored"], index=index, fixture_id=fixture_id, name=name + " scored"
    )
    weight = float(
        _float_tag(checked["normalized_weight_float64_be"], name + " weight")
    )
    if not 0.0 < weight <= 1.0:
        raise CP63IndependentRecomputationError(name + " weight differs")
    _verify_owned_leaf(
        checked,
        "cp62_particle_sha256",
        b"cp62-test28-sir-particle-v1",
        name,
    )
    return checked, configuration, weight


def _calibration_instance_sha256(seed_free_request_sha256: str) -> str:
    return hashlib.sha256(
        b"cp62-test28-calibration-request-instance-v1\0"
        + bytes.fromhex(seed_free_request_sha256)
        + bytes.fromhex(_REHEARSAL_SEED_HEX)
    ).hexdigest()


def _derive_stream_seed(
    *, strategy: str, stream_role: str, role_sha256: str, budget: int
) -> int:
    digest = hashlib.sha256(b"heterodiff-mixed-support-initializer-derived-stream-v2\0")
    digest.update(strategy.encode("ascii") + b"\0")
    digest.update(stream_role.encode("ascii") + b"\0")
    seed = int(_REHEARSAL_SEED_HEX, 16)
    digest.update(seed.to_bytes(8, "big"))
    digest.update(bytes.fromhex(role_sha256))
    digest.update(bytes.fromhex(_RESIDUAL_CONTEXT_SHA256))
    fixture = (
        _M1 if role_sha256 == _FIXTURE_BINDINGS[_M1]["initializer_role_sha256"] else _M2
    )
    digest.update(
        bytes.fromhex(_FIXTURE_BINDINGS[fixture]["facade_certificate_sha256"])
    )
    if stream_role == "sir-resampling":
        digest.update(b"sir-particle-budget\0")
        digest.update(budget.to_bytes(8, "big"))
    else:
        digest.update(b"no-particle-budget\0")
    result = int.from_bytes(digest.digest()[:8], "big")
    return result ^ (1 << 63) if result == seed else result


def _expected_stream_seeds(trace: dict) -> Tuple[int, Optional[int], Optional[int]]:
    role = _FIXTURE_BINDINGS[trace["fixture_id"]]["initializer_role_sha256"]
    seed = int(_REHEARSAL_SEED_HEX, 16)
    proposal = _derive_stream_seed(
        strategy=trace["strategy"],
        stream_role="proposal",
        role_sha256=role,
        budget=trace["budget"],
    )
    used = {seed, proposal}

    def unique(candidate: int) -> int:
        while candidate in used:
            candidate = (candidate + 1) % (1 << 64)
        used.add(candidate)
        return candidate

    if trace["strategy"] == "bounded-rejection":
        decision = _derive_stream_seed(
            strategy=trace["strategy"],
            stream_role="rejection-decision",
            role_sha256=role,
            budget=trace["budget"],
        )
        return proposal, unique(decision), None
    resampling = _derive_stream_seed(
        strategy=trace["strategy"],
        stream_role="sir-resampling",
        role_sha256=role,
        budget=trace["budget"],
    )
    return proposal, None, unique(resampling)


def _validate_resource_preflight(value: object, trace: dict) -> None:
    checked = _exact_keys(
        value,
        (
            "mode",
            "reference_occurrence_limit",
            "reference_coordinate_limit",
            "worst_case_occurrences",
            "worst_case_coordinates",
            "fixed_budget_work_certified",
            "arbitrary_rational_quota_required",
        ),
        "resource preflight",
    )
    multiplier_occurrences = 1 if trace["fixture_id"] == _M1 else 2
    multiplier_coordinates = 1 if trace["fixture_id"] == _M1 else 4
    expected = {
        "mode": "stochastic-worst-case",
        "reference_occurrence_limit": 500_000,
        "reference_coordinate_limit": 4_000_000,
        "worst_case_occurrences": trace["budget"] * multiplier_occurrences,
        "worst_case_coordinates": trace["budget"] * multiplier_coordinates,
        "fixed_budget_work_certified": True,
        "arbitrary_rational_quota_required": trace["strategy"] == "bounded-rejection",
    }
    if any(
        type(checked[field]) is not type(wanted) or checked[field] != wanted
        for field, wanted in expected.items()
    ):
        raise CP63IndependentRecomputationError("resource preflight differs")


def _validate_common_semantic_bindings(
    semantic: dict, trace: dict, *, trace_schema: str, runtime_required: bool
) -> None:
    fixture_id = trace["fixture_id"]
    bindings = _FIXTURE_BINDINGS[fixture_id]
    exact = {
        "trace_schema": trace_schema,
        "stable_request_sha256": trace["seed_free_request_sha256"],
        "calibration_instance_sha256": _calibration_instance_sha256(
            trace["seed_free_request_sha256"]
        ),
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "fixture_id": fixture_id,
        "strategy": trace["strategy"],
        "budget": trace["budget"],
        **bindings,
        "residual_context_sha256": _RESIDUAL_CONTEXT_SHA256,
    }
    for field, wanted in exact.items():
        if type(semantic[field]) is not type(wanted) or semantic[field] != wanted:
            raise CP63IndependentRecomputationError(
                "semantic %s binding differs" % field
            )
    runtime = semantic["runtime_observation"]
    if runtime is None and not runtime_required:
        return
    if type(runtime) is not dict or set(runtime) != set(_RUNTIME_OBSERVATION):
        raise CP63IndependentRecomputationError("semantic runtime custody differs")
    if any(
        type(runtime[field]) is not type(wanted) or runtime[field] != wanted
        for field, wanted in _RUNTIME_OBSERVATION.items()
    ):
        raise CP63IndependentRecomputationError("semantic runtime custody differs")


def _validate_returned_semantic(value: object, trace: dict) -> dict:
    semantic = _exact_keys(value, _SEMANTIC_TRACE_KEYS, "returned semantic trace")
    _validate_common_semantic_bindings(
        semantic,
        trace,
        trace_schema="cp62-test28-stable-kernel-trace-v1",
        runtime_required=True,
    )
    if (
        _fraction_tag(semantic["exact_log_weight_upper_bound"], "upper bound") != 0
        or semantic["exact_log_weight_lower_bound"] is not None
    ):
        raise CP63IndependentRecomputationError("semantic score bounds differ")
    proposal_seed, decision_seed, resampling_seed = _expected_stream_seeds(trace)
    expected_seed_fields = {
        "proposal_seed_hex": proposal_seed.to_bytes(8, "big").hex(),
        "rejection_decision_seed_hex": (
            None if decision_seed is None else decision_seed.to_bytes(8, "big").hex()
        ),
        "sir_resampling_seed_hex": (
            None
            if resampling_seed is None
            else resampling_seed.to_bytes(8, "big").hex()
        ),
    }
    if any(semantic[field] != wanted for field, wanted in expected_seed_fields.items()):
        raise CP63IndependentRecomputationError("derived stream seed differs")
    _validate_resource_preflight(semantic["resource_preflight"], trace)
    for field in (
        "structural_result_validation_replays_provider_evaluate",
        "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation",
        "structural_result_validation_replays_reference_sampler",
        "structural_result_validation_replays_rng",
        "operational_reference_sampling_law_verified",
        "philox_uniformity_verified",
        "stream_independence_verified",
        "iid_proposals_verified",
        "analytic_target_equality_verified",
        "exact_operational_rejection_bernoulli_verified",
        "finite_j_sir_exact_target_verified",
        "source_or_model_quality_evidence",
        "path_or_sampler_admitted",
        "formal_test_28_closed",
    ):
        if semantic[field] is not False:
            raise CP63IndependentRecomputationError(
                "semantic nonclaim %s differs" % field
            )
    _sha256(semantic["proposal_stream_initial_state_sha256"], "proposal initial")
    _sha256(semantic["proposal_stream_final_state_sha256"], "proposal final")
    attempts = semantic["attempts"]
    particles = semantic["particles"]
    weights = semantic["normalized_weights_float64_be"]
    selected_index = semantic["selected_index"]
    selected_configuration = semantic["selected_configuration"]
    fixture_id = trace["fixture_id"]
    budget = trace["budget"]
    if trace["strategy"] == "bounded-rejection":
        expected_outer_status = {
            "selected": "returned-rejection-selected-before-deadline",
            "exhausted": "returned-rejection-exhausted-before-deadline",
        }.get(semantic["result_status"])
        if (
            trace["closed_status"] != expected_outer_status
            or semantic["explicit_rejection_exhaustion"] is not True
            or semantic["result_status"] not in ("selected", "exhausted")
            or type(attempts) is not list
            or len(attempts) != budget
            or particles != []
            or weights != []
        ):
            raise CP63IndependentRecomputationError("rejection result shape differs")
        for field in (
            "decision_stream_initial_state_sha256",
            "decision_stream_final_state_sha256",
        ):
            _sha256(semantic[field], "rejection " + field)
        for field in (
            "resampling_stream_initial_state_sha256",
            "resampling_stream_final_state_sha256",
            "resampling_word_hex",
            "resampling_uniform_53",
            "effective_sample_size_float64_be",
            "maximum_normalized_weight_float64_be",
            "ess_warning",
        ):
            if semantic[field] is not None:
                raise CP63IndependentRecomputationError(
                    "rejection inapplicable field differs"
                )
        checked_attempts = [
            _validate_attempt(
                item,
                index=index,
                fixture_id=fixture_id,
                name="attempt %d" % index,
            )
            for index, item in enumerate(attempts)
        ]
        accepted = [item[2] for item in checked_attempts]
        if semantic["result_status"] == "selected":
            if (
                type(selected_index) is not int
                or not 0 <= selected_index < budget
                or not accepted[selected_index]
                or any(accepted[:selected_index])
                or selected_configuration
                != attempts[selected_index]["scored"]["configuration"]
            ):
                raise CP63IndependentRecomputationError(
                    "selected rejection semantics differ"
                )
            _configuration_value(
                selected_configuration,
                fixture_id=fixture_id,
                name="selected configuration",
            )
        elif (
            selected_index is not None
            or selected_configuration is not None
            or any(accepted)
        ):
            raise CP63IndependentRecomputationError(
                "exhausted rejection semantics differ"
            )
    else:
        if (
            semantic["explicit_rejection_exhaustion"] is not False
            or semantic["result_status"] != "selected"
            or attempts != []
            or type(particles) is not list
            or len(particles) != budget
            or type(weights) is not list
            or len(weights) != budget
            or type(selected_index) is not int
            or not 0 <= selected_index < budget
        ):
            raise CP63IndependentRecomputationError("SIR result shape differs")
        for field in (
            "decision_stream_initial_state_sha256",
            "decision_stream_final_state_sha256",
        ):
            if semantic[field] is not None:
                raise CP63IndependentRecomputationError("SIR decision field differs")
        for field in (
            "resampling_stream_initial_state_sha256",
            "resampling_stream_final_state_sha256",
        ):
            _sha256(semantic[field], "SIR " + field)
        word = int(_uint64_hex(semantic["resampling_word_hex"], "SIR word"), 16)
        if (
            type(semantic["resampling_uniform_53"]) is not int
            or semantic["resampling_uniform_53"] != word >> 11
        ):
            raise CP63IndependentRecomputationError("SIR uniform53 differs")
        checked_particles = [
            _validate_particle(
                item,
                index=index,
                fixture_id=fixture_id,
                name="particle %d" % index,
            )
            for index, item in enumerate(particles)
        ]
        decoded_weights = [
            float(_float_tag(item, "normalized weight")) for item in weights
        ]
        if (
            any(
                weights[index] != particles[index]["normalized_weight_float64_be"]
                or decoded_weights[index] != checked_particles[index][2]
                for index in range(budget)
            )
            or abs(math.fsum(decoded_weights) - 1.0) > 32.0 * budget * 2.0**-52
        ):
            raise CP63IndependentRecomputationError("SIR weights differ")
        exact_scores = [
            _fraction_tag(
                particle["scored"]["exact_log_weight"],
                "SIR particle exact score",
            )
            for particle in particles
        ]
        float_scores = [float(value) for value in exact_scores]
        maximum_score = max(float_scores)
        shifted = [math.exp(value - maximum_score) for value in float_scores]
        if any(not math.isfinite(value) or value <= 0.0 for value in shifted):
            raise CP63IndependentRecomputationError("SIR shifted weights differ")
        shifted_total = math.fsum(shifted)
        expected_weights = [value / shifted_total for value in shifted]
        if decoded_weights != expected_weights:
            raise CP63IndependentRecomputationError(
                "SIR normalization differs from independent replay"
            )
        expected_ess = 1.0 / math.fsum(value * value for value in expected_weights)
        expected_maximum = max(expected_weights)
        supplied_ess = float(
            _float_tag(semantic["effective_sample_size_float64_be"], "SIR ESS")
        )
        supplied_maximum = float(
            _float_tag(semantic["maximum_normalized_weight_float64_be"], "SIR max")
        )
        if (
            supplied_ess != expected_ess
            or supplied_maximum != expected_maximum
            or type(semantic["ess_warning"]) is not bool
            or semantic["ess_warning"] != (expected_ess < 0.25 * budget)
        ):
            raise CP63IndependentRecomputationError("SIR diagnostics differ")
        floor = max(2.0**-40, 32.0 * budget * 2.0**-52)
        if min(expected_weights) < floor:
            raise CP63IndependentRecomputationError("SIR categorical floor differs")
        cdf = []
        running = 0.0
        for expected_weight in expected_weights:
            running += expected_weight
            cdf.append(running)
        cdf[-1] = 1.0
        previous = 0.0
        for expected_weight, cumulative in zip(expected_weights, cdf):
            increment = cumulative - previous
            if (
                increment <= 0.0
                or abs(increment - expected_weight) / expected_weight > 0.125
            ):
                raise CP63IndependentRecomputationError(
                    "SIR categorical resolution differs"
                )
            previous = cumulative
        uniform = (word >> 11) * 2.0**-53
        expected_selected = next(
            (index for index, cumulative in enumerate(cdf) if cumulative > uniform),
            None,
        )
        if selected_index != expected_selected:
            raise CP63IndependentRecomputationError("SIR selected index differs")
        if (
            selected_configuration
            != particles[selected_index]["scored"]["configuration"]
        ):
            raise CP63IndependentRecomputationError("SIR selection differs")
        _configuration_value(
            selected_configuration,
            fixture_id=fixture_id,
            name="selected configuration",
        )
    _verify_owned_leaf(
        semantic,
        "cp62_semantic_trace_sha256",
        b"cp62-test28-semantic-kernel-trace-v1",
        "returned semantic trace",
    )
    return semantic


def _validate_closed_semantic(value: object, trace: dict) -> dict:
    semantic = _exact_keys(value, _CLOSED_SEMANTIC_TRACE_KEYS, "closed semantic trace")
    _validate_common_semantic_bindings(
        semantic,
        trace,
        trace_schema="cp62-test28-closed-kernel-outcome-v1",
        runtime_required=False,
    )
    if semantic["runtime_lock_sha256"] != _RUNTIME_LOCK_SHA256:
        raise CP63IndependentRecomputationError("closed runtime lock differs")
    phase = trace["phase"]
    wanted_kind = (
        "preexecution-refusal"
        if phase == "preexecution-refusal-before-deadline"
        else "execution-failure"
        if phase == "execution-failure-before-deadline"
        else "timeout-censored"
    )
    if (
        semantic["outcome_kind"] != wanted_kind
        or semantic["failure_code"] != trace["failure_code"]
        or semantic["completed_kernel_trace_present"] is not False
        or semantic["timeout_is_semantic_nonreturn"] is not False
    ):
        raise CP63IndependentRecomputationError("closed semantic arm differs")
    _verify_owned_leaf(
        semantic,
        "cp62_closed_trace_sha256",
        b"cp62-test28-closed-kernel-outcome-v1",
        "closed semantic trace",
    )
    return semantic


def _validate_kernel_trace(value: object, trace: dict) -> dict:
    if trace["phase"] == "returned-before-deadline":
        return _validate_returned_semantic(value, trace)
    return _validate_closed_semantic(value, trace)


def _float_tag(value: object, name: str) -> Fraction:
    if type(value) is not dict or set(value) != {"$float64_be"}:
        raise CP63IndependentRecomputationError(name + " is not a float64 tag")
    raw = value["$float64_be"]
    if (
        type(raw) is not str
        or len(raw) != 16
        or any(character not in "0123456789abcdef" for character in raw)
    ):
        raise CP63IndependentRecomputationError(name + " float64 bytes differ")
    number = struct.unpack(">d", bytes.fromhex(raw))[0]
    if not math.isfinite(number) or (
        number == 0.0 and math.copysign(1.0, number) < 0.0
    ):
        raise CP63IndependentRecomputationError(name + " is noncanonical")
    return Fraction.from_float(number)


def _selected_configuration(trace: dict) -> Optional[Tuple[tuple, ...]]:
    if trace["closed_status"] not in (
        "returned-rejection-selected-before-deadline",
        "returned-sir-selected-before-deadline",
    ):
        return None
    semantic = trace["kernel_trace"]
    configuration = semantic.get("selected_configuration")
    return _configuration_value(
        configuration,
        fixture_id=trace["fixture_id"],
        name="selected configuration",
    )


def _odd(value: Fraction) -> Fraction:
    return max(Fraction(-1), min(Fraction(1), value))


def _even(value: Fraction) -> Fraction:
    return Fraction(1) if abs(value) >= 1 else value * value


def _project(event: tuple, coefficients: Tuple[Fraction, ...]) -> Fraction:
    return sum(
        (
            coefficient * coordinate
            for coefficient, coordinate in zip(coefficients, event[1])
        ),
        Fraction(0),
    )


def _feature_vector(fixture_id: str, configuration: Tuple[tuple, ...]) -> tuple:
    cap = 1 if fixture_id == _M1 else 2
    dimensions = (0, 1) if fixture_id == _M1 else (1, 2)
    projections = _projections(fixture_id)
    projection_map = {(item[0], item[1]): item[2] for item in projections}
    result = []
    for count in range(cap + 1):
        result.append(Fraction(int(len(configuration) == count)))
    for event_type in range(len(dimensions)):
        result.append(
            Fraction(sum(1 for event in configuration if event[0] == event_type), cap)
        )
    for event_type, projection_id, coefficients in projections:
        values = [
            _project(event, coefficients)
            for event in configuration
            if event[0] == event_type
        ]
        result.append(sum((_odd(value) for value in values), Fraction(0)) / cap)
        result.append(sum((_even(value) for value in values), Fraction(0)) / cap)
    if cap == 2:
        pairs = tuple(
            (configuration[left], configuration[right])
            for left in range(len(configuration))
            for right in range(left + 1, len(configuration))
        )
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                result.append(
                    Fraction(
                        sum(
                            1
                            for left, right in pairs
                            if (left[0], right[0]) == (left_type, right_type)
                        )
                    )
                )
        by_type = {
            event_type: tuple(item for item in projections if item[0] == event_type)
            for event_type in range(len(dimensions))
        }
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left_projection in enumerate(by_type[left_type]):
                    for right_position, right_projection in enumerate(
                        by_type[right_type]
                    ):
                        if left_type == right_type and right_position < left_position:
                            continue
                        total = Fraction(0)
                        for left, right in pairs:
                            if (left[0], right[0]) != (left_type, right_type):
                                continue
                            direct = _odd(
                                _project(
                                    left,
                                    projection_map[(left_type, left_projection[1])],
                                )
                            ) * _odd(
                                _project(
                                    right,
                                    projection_map[(right_type, right_projection[1])],
                                )
                            )
                            if (
                                left_type == right_type
                                and left_projection[1] != right_projection[1]
                            ):
                                reverse = _odd(
                                    _project(
                                        left,
                                        projection_map[
                                            (left_type, right_projection[1])
                                        ],
                                    )
                                ) * _odd(
                                    _project(
                                        right,
                                        projection_map[
                                            (right_type, left_projection[1])
                                        ],
                                    )
                                )
                                direct = (direct + reverse) / 2
                            total += direct
                        result.append(total)
    feature_ids = _feature_ids(fixture_id)
    if len(result) != len(feature_ids):
        raise AssertionError("CP63 feature value inventory differs")
    return tuple(zip(feature_ids, result))


def cp63_compact_observation(payload: object) -> CP63CompactObservationV1:
    """Independently reduce one stable trace to its CP61 compact semantics."""

    trace = cp63_independently_validate_stable_trace_bytes(payload)
    selected_configuration = _selected_configuration(trace)
    selected = selected_configuration is not None
    first_attempt = None
    semantic = trace["kernel_trace"]
    if selected and trace["strategy"] == "bounded-rejection":
        selected_index = semantic.get("selected_index")
        if type(selected_index) is not int or not 0 <= selected_index < trace["budget"]:
            raise CP63IndependentRecomputationError("selected attempt differs")
        first_attempt = selected_index + 1
    selected_features = (
        _feature_vector(trace["fixture_id"], cast(tuple, selected_configuration))
        if selected_configuration is not None
        else ()
    )
    observable_ordinal, _first_ordinals = _contribution_ordinals(
        trace["row_ordinal"], trace["closed_status"], first_attempt
    )
    stable_sha256 = hashlib.sha256(
        b"cp63-test28-stable-trace-v1\0" + cast(bytes, payload)
    ).hexdigest()
    return cast(
        CP63CompactObservationV1,
        _record(
            CP63CompactObservationV1,
            b"cp63-compact-observation-v1",
            {
                "schema_version": CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION,
                "seed_ordinal": trace["seed_ordinal"],
                "row_ordinal": trace["row_ordinal"],
                "logical_request_ordinal": trace["logical_request_ordinal"],
                "row_key": trace["row_key"],
                "fixture_id": trace["fixture_id"],
                "strategy": trace["strategy"],
                "budget": trace["budget"],
                "plan_seed_hex": trace["plan_seed_hex"],
                "seed_free_request_sha256": trace["seed_free_request_sha256"],
                "request_instance_sha256": trace["request_instance_sha256"],
                "runtime_lock_sha256": trace["runtime_lock_sha256"],
                "stable_trace_sha256": stable_sha256,
                "observable_cell_label": trace["closed_status"],
                "observable_contribution_ordinal": observable_ordinal,
                "first_selected_attempt_one_based": first_attempt,
                "selected": selected,
                "selected_feature_ids": tuple(
                    feature_id for feature_id, _value in selected_features
                ),
                "selected_feature_values": tuple(
                    value for _feature_id, value in selected_features
                ),
            },
        ),
    )


def cp63_recompute_rehearsal(
    stable_trace_payloads: object,
) -> CP63RehearsalRecomputationReceiptV1:
    """Recompute exactly one complete sixteen-row development rehearsal."""

    if type(stable_trace_payloads) is not tuple or len(stable_trace_payloads) != 16:
        raise TypeError("rehearsal requires an exact tuple of sixteen stable payloads")
    observations = tuple(
        cp63_compact_observation(item) for item in stable_trace_payloads
    )
    if tuple(item.row_ordinal for item in observations) != tuple(range(1, 17)):
        raise CP63IndependentRecomputationError(
            "rehearsal stable payload order differs from rows 1 through 16"
        )
    by_row = {item.row_ordinal: item for item in observations}
    if len(by_row) != 16 or tuple(sorted(by_row)) != tuple(range(1, 17)):
        raise CP63IndependentRecomputationError("rehearsal rows differ")
    plan_seeds = {item.plan_seed_hex for item in observations}
    if len(plan_seeds) != 1:
        raise CP63IndependentRecomputationError("rehearsal plan seed differs by row")
    observable_vector = [0] * 72
    first_vector = [0] * 170
    feature_present = []
    feature_values = []
    for row_ordinal, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        observation = by_row[row_ordinal]
        observable_vector[observation.observable_contribution_ordinal - 1] = 1
        _observable_ordinal, first_ordinals = _contribution_ordinals(
            row_ordinal,
            observation.observable_cell_label,
            observation.first_selected_attempt_one_based,
        )
        for ordinal in first_ordinals:
            first_vector[ordinal - 1] = 1
        supplied = dict(
            zip(
                observation.selected_feature_ids,
                observation.selected_feature_values,
            )
        )
        for feature_id in _feature_ids(fixture):
            present = feature_id in supplied
            feature_present.append(present)
            feature_values.append(supplied[feature_id] if present else None)
    if (len(observable_vector), len(first_vector), len(feature_present)) != (
        72,
        170,
        312,
    ):
        raise AssertionError("CP63 rehearsal contribution length differs")
    return cast(
        CP63RehearsalRecomputationReceiptV1,
        _record(
            CP63RehearsalRecomputationReceiptV1,
            b"cp63-rehearsal-recomputation-receipt-v1",
            {
                "schema_version": CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION,
                "request_count": 16,
                "row_ordinals": tuple(range(1, 17)),
                "logical_request_ordinals": tuple(
                    by_row[row].logical_request_ordinal for row in range(1, 17)
                ),
                "stable_trace_sha256s": tuple(
                    by_row[row].stable_trace_sha256 for row in range(1, 17)
                ),
                "compact_observation_sha256s": tuple(
                    by_row[row].record_sha256 for row in range(1, 17)
                ),
                "observable_contributions": tuple(observable_vector),
                "first_attempt_contributions": tuple(first_vector),
                "selected_feature_present": tuple(feature_present),
                "selected_feature_values": tuple(feature_values),
                "missing_count": 0,
                "duplicate_count": 0,
                "invalid_count": 0,
                "independent_parser": True,
                "runner_source_imported": False,
                "intervals_computed": False,
                "decision_made": False,
            },
        ),
    )


def _validate_compact_record(record: CP63CompactObservationV1) -> None:
    row = record.row_ordinal
    if type(row) is not int or not 1 <= row <= 16:
        raise ValueError("compact row ordinal differs")
    fixture, strategy, budget = _ROW_SHAPES[row - 1]
    exact = {
        "schema_version": CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION,
        "seed_ordinal": 1,
        "logical_request_ordinal": row,
        "row_key": _row_key(row),
        "fixture_id": fixture,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "seed_free_request_sha256": _SEED_FREE_REQUEST_SHA256S[row - 1],
        "request_instance_sha256": _rehearsal_request_instance_sha256(row),
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    }
    for field, wanted in exact.items():
        supplied = getattr(record, field)
        if type(supplied) is not type(wanted) or supplied != wanted:
            raise ValueError("compact %s differs" % field)
    _sha256(record.stable_trace_sha256, "compact stable trace")
    selected = record.observable_cell_label in (
        "returned-rejection-selected-before-deadline",
        "returned-sir-selected-before-deadline",
    )
    first = record.first_selected_attempt_one_based
    wanted_first = first if strategy == "bounded-rejection" and selected else None
    if (
        type(record.selected) is not bool
        or record.selected != selected
        or first != wanted_first
        or (first is not None and (type(first) is not int or not 1 <= first <= budget))
    ):
        raise ValueError("compact selected semantics differ")
    ordinal, _first_ordinals = _contribution_ordinals(
        row, record.observable_cell_label, first
    )
    if (
        type(record.observable_contribution_ordinal) is not int
        or record.observable_contribution_ordinal != ordinal
    ):
        raise ValueError("compact observable ordinal differs")
    expected_ids = _feature_ids(fixture) if selected else ()
    if (
        type(record.selected_feature_ids) is not tuple
        or record.selected_feature_ids != expected_ids
    ):
        raise ValueError("compact feature id inventory differs")
    values = record.selected_feature_values
    if type(values) is not tuple or len(values) != len(expected_ids):
        raise ValueError("compact feature value inventory differs")
    for feature_id, value in zip(expected_ids, values):
        if type(value) is not Fraction:
            raise TypeError("compact feature value is not an exact Fraction")
        lower = (
            -1
            if ("/odd" in feature_id or feature_id.startswith("pair-projection/"))
            else 0
        )
        if not Fraction(lower) <= value <= 1:
            raise ValueError("compact feature value lies outside its range")


def _validate_receipt_record(record: CP63RehearsalRecomputationReceiptV1) -> None:
    expected_ordinals = tuple(range(1, 17))
    if (
        type(record.schema_version) is not str
        or record.schema_version != CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION
        or type(record.request_count) is not int
        or record.request_count != 16
        or type(record.row_ordinals) is not tuple
        or len(record.row_ordinals) != 16
        or any(type(value) is not int for value in record.row_ordinals)
        or record.row_ordinals != expected_ordinals
        or type(record.logical_request_ordinals) is not tuple
        or len(record.logical_request_ordinals) != 16
        or any(type(value) is not int for value in record.logical_request_ordinals)
        or record.logical_request_ordinals != expected_ordinals
        or type(record.missing_count) is not int
        or record.missing_count != 0
        or type(record.duplicate_count) is not int
        or record.duplicate_count != 0
        or type(record.invalid_count) is not int
        or record.invalid_count != 0
        or record.independent_parser is not True
        or record.runner_source_imported is not False
        or record.intervals_computed is not False
        or record.decision_made is not False
    ):
        raise ValueError("recomputation receipt invariant differs")
    for name, values, length in (
        ("stable hashes", record.stable_trace_sha256s, 16),
        ("compact hashes", record.compact_observation_sha256s, 16),
    ):
        if type(values) is not tuple or len(values) != length:
            raise ValueError("receipt %s length differs" % name)
        for value in values:
            _sha256(value, "receipt " + name)
        if len(set(values)) != length:
            raise ValueError("receipt %s are not row-distinct" % name)
    for name, values, length in (
        ("observable", record.observable_contributions, 72),
        ("first-attempt", record.first_attempt_contributions, 170),
    ):
        if (
            type(values) is not tuple
            or len(values) != length
            or any(type(value) is not int or value not in (0, 1) for value in values)
        ):
            raise ValueError("receipt %s contribution vector differs" % name)
    observable_offset = 0
    first_offset = 0
    selected_by_row = []
    for _row, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        cell_count = 5 if strategy == "bounded-rejection" else 4
        observable_block = record.observable_contributions[
            observable_offset : observable_offset + cell_count
        ]
        if sum(observable_block) != 1:
            raise ValueError("receipt row observable contribution differs")
        selected = observable_block[0] == 1
        selected_by_row.append(selected)
        observable_offset += cell_count
        if strategy == "bounded-rejection":
            first_sum = sum(
                record.first_attempt_contributions[first_offset : first_offset + budget]
            )
            if first_sum != int(selected):
                raise ValueError("receipt row first-attempt contribution differs")
            first_offset += budget
    present = record.selected_feature_present
    values = record.selected_feature_values
    if (
        type(present) is not tuple
        or type(values) is not tuple
        or len(present) != 312
        or len(values) != 312
    ):
        raise ValueError("receipt selected-feature vectors differ")
    offset = 0
    for row_index, (fixture, _strategy, _budget) in enumerate(_ROW_SHAPES):
        ids = _feature_ids(fixture)
        block = present[offset : offset + len(ids)]
        if any(type(item) is not bool for item in block) or (
            block and not (all(block) or not any(block))
        ):
            raise ValueError("receipt selected-feature presence block differs")
        if bool(block and all(block)) != selected_by_row[row_index]:
            raise ValueError("receipt selected-feature/status linkage differs")
        for feature_id, is_present, value in zip(
            ids, block, values[offset : offset + len(ids)]
        ):
            if not is_present:
                if value is not None:
                    raise ValueError("absent feature retains a value")
                continue
            if type(value) is not Fraction:
                raise TypeError("present feature lacks an exact Fraction")
            lower = (
                -1
                if ("/odd" in feature_id or feature_id.startswith("pair-projection/"))
                else 0
            )
            if not Fraction(lower) <= value <= 1:
                raise ValueError("receipt feature value lies outside its range")
        offset += len(ids)


def _validate_public_record(record: object) -> Tuple[_SealedRecord, bytes]:
    if type(record) not in (
        CP63CompactObservationV1,
        CP63RehearsalRecomputationReceiptV1,
        CP63IndependentRecomputationBundleV1,
    ):
        raise TypeError("unsupported CP63 independent record type")
    sealed = cast(_SealedRecord, record)
    with _ISSUED_RECORD_LOCK:
        issued_snapshot = _ISSUED_RECORD_SNAPSHOTS.get(sealed)
        if issued_snapshot is None:
            raise TypeError("CP63 independent record was not module-created")
        if type(record) is CP63CompactObservationV1:
            _validate_compact_record(cast(CP63CompactObservationV1, record))
        elif type(record) is CP63RehearsalRecomputationReceiptV1:
            _validate_receipt_record(cast(CP63RehearsalRecomputationReceiptV1, record))
        elif _canonical_json_bytes(record) != _canonical_json_bytes(_bundle()):
            raise ValueError("CP63 independent bundle differs from canonical replay")
        supplied = getattr(record, "record_sha256")
        body = {item.name: getattr(record, item.name) for item in fields(type(record))}
        body["record_sha256"] = _ZERO_SHA256
        domains = {
            CP63CompactObservationV1: b"cp63-compact-observation-v1",
            CP63RehearsalRecomputationReceiptV1: (
                b"cp63-rehearsal-recomputation-receipt-v1"
            ),
            CP63IndependentRecomputationBundleV1: (
                b"cp63-independent-recomputation-bundle-v1"
            ),
        }
        expected = hashlib.sha256(
            domains[type(record)] + b"\0" + _canonical_json_bytes(body)
        ).hexdigest()
        if supplied != expected:
            raise ValueError("CP63 independent record digest differs")
        if _canonical_json_bytes(record) != issued_snapshot:
            raise ValueError("CP63 independent issued record was mutated")
        return sealed, issued_snapshot


def cp63_recomputation_canonical_json_bytes(record: object) -> bytes:
    """Encode one exact validated CP63 independent record."""

    _validated, issued_snapshot = _validate_public_record(record)
    return issued_snapshot


def cp63_recomputation_sha256(record: object) -> str:
    """Hash the exact tagged canonical bytes of one independent record."""

    validated, issued_snapshot = _validate_public_record(record)
    tag = type(validated).__name__.encode("ascii")
    return hashlib.sha256(
        b"cp63-independent-public-record-v1\0" + tag + b"\0" + issued_snapshot
    ).hexdigest()


__all__ = (
    "CP63IndependentRecomputationError",
    "CP63CompactObservationV1",
    "CP63RehearsalRecomputationReceiptV1",
    "CP63IndependentRecomputationBundleV1",
    "CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION",
    "CP63_INDEPENDENT_RECOMPUTATION_SCOPE",
    "cp63_independent_recomputation_bundle",
    "cp63_independently_validate_stable_trace_bytes",
    "cp63_compact_observation",
    "cp63_recompute_rehearsal",
    "cp63_recomputation_canonical_json_bytes",
    "cp63_recomputation_sha256",
)
