"""Sealed mixed-support initial-score initializer kernels, version 2.

This module consumes only an exact :class:`CertifiedInitialScoreProviderV1`.
It deliberately does not import the CP50-v1 composer kernel.  A plan commits to
one of three bounded strategies before execution:

* complete finite-atomic enumeration when every reference fiber is atomic;
* fixed-budget rejection using an exact rational score gap and the separately
  certified arbitrary-rational uint64 exponential quota; or
* fixed-budget sampling-importance-resampling (SIR).

The provider's exact global upper bound is sufficient for rejection.  Its
optional lower bound is retained as a diagnostic certificate field but is not
required by any strategy and is never fabricated.  SIR and enumeration fail
closed if their realized exact scores cannot be normalized safely in float64.

Executions are deterministic interface traces under a trusted unchanged
runtime.  This module does not certify the operational reference-sampling law,
Philox uniformity or independence, IID proposals, equality to an analytic
target, an exact exponential Bernoulli draw, source/model quality, path or
sampler admission, or closure of Formal Test 28.  Structural result validation
checks retained records and arithmetic but never calls ``provider.evaluate``,
the source replay validator, a reference sampler, or Philox.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
import platform
import struct
from typing import Mapping, Optional, Tuple, Union

import numpy as np

from heterodiff.processes.arbitrary_rational_uint64_exp_quota import (
    ArbitraryRationalUInt64ExpQuotaCertificate,
    UINT64_EXP_QUOTA_DENOMINATOR,
    certify_arbitrary_rational_uint64_exp_quota,
    validate_arbitrary_rational_uint64_exp_quota_certificate,
)
from heterodiff.processes import certified_initial_score_provider_v1 as _score
from heterodiff.processes.certified_initial_score_provider_v1 import (
    CertifiedInitialScorePointEvaluationV1,
    CertifiedInitialScoreProviderCertificateV1,
    CertifiedInitialScoreProviderV1,
    require_matching_certified_initial_score_provider_v1,
    validate_certified_initial_score_provider_v1_certificate,
)
from heterodiff.theory import configuration_reference as _reference
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedConfiguration,
    TransformedEvent,
)


MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCHEMA_VERSION = (
    "mixed-support-initial-tilt-initializer-kernel-v2"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_TARGET_POLICY = (
    "strategy-disjunctive-representation-policy;stochastic-strategies-use-"
    "conceptual-rho_repr(dx)=exp(q_repr(x))*P_ref^op(dx)/Z_repr-with-"
    "P_ref^op-unspecified;finite-enumeration-float64-approximates-normalization-"
    "from-exact-q_repr-inputs-and-the-finite_atomic_oracle-binary64-mass-vector-"
    "P_ref^{oracle,b64};no-equality-"
    "between-operational-oracle-binary64-and-analytic-reference-laws-certified"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_STRATEGIES = (
    "finite-atomic-enumeration",
    "bounded-rejection",
    "fixed-budget-sir",
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCOPE = (
    "one-exact-CertifiedInitialScoreProviderV1;one-fixed-context;one-exact-"
    "capped-poisson-reference-object;one-precommitted-strategy;exact-rational-"
    "point-scores;certified-exact-upper-envelope;optional-lower-envelope-"
    "retained-but-never-required;arbitrary-rational-uint64-rejection-quota;"
    "fixed-bounded-work;pre-rng-recomputed-reference-categorical-sampling-"
    "resolution-preflight;explicit-exhaustion;structural-result-validation-"
    "without-provider-evaluate-source-public-validate_evaluation-RNG-or-reference-"
    "sampler-replay;live-ancestry-and-certificate-validation-permitted;"
    "retained-source-point-structural-arithmetic-and-custody-validation-permitted;"
    "trusted-runtime;"
    "not-operational-or-analytic-source-law-IID-independence-normalization-"
    "target-equality-exact-Bernoulli-model-quality-path-sampler-or-Test28"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_NONCLAIM = (
    "kernel-v2-records-a-bounded-interface-execution-only;it-does-not-prove-"
    "the-reference-sampling-law-Philox-uniformity-stream-independence-IID-"
    "proposals-an-analytic-real-fiber-extension-target-or-normalizer-exact-"
    "operational-rejection-Bernoulli-finite-J-SIR-exactness-source-or-model-"
    "quality-generality-path-or-sampler-admission-or-Formal-Test-28-closure"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_REJECTION_CAVEAT = (
    "K=floor(2^64*exp(q-U))-certificate-is-conditional-on-the-frozen-Decimal-"
    "contract;acceptance-under-an-abstract-uniform-uint64-word-is-K/2^64;"
    "the-live-Philox-premise-and-exact-exponential-Bernoulli-are-not-certified"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SIR_CAVEAT = (
    "finite-J-self-normalized-resampling-is-not-an-exact-target-sample;"
    "realized-float64-normalization-is-fail-closed-and-needs-no-global-L;"
    "proposal-IID-and-live-categorical-law-antecedents-are-not-certified"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_ENUMERATION_CAVEAT = (
    "finite-atomic-enumeration-tilts-the-reference-finite_atomic_oracle-float64-"
    "mass-vector-P_ref^{oracle,b64};it-does-not-certify-equality-to-an-"
    "operational-sampler-law-an-analytic-Pi_N-or-an-analytic-normalizer"
)
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_FORMAL_TEST_28_STATUS = "OPEN"
MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_EXECUTED_MEASURE_POLICIES = (
    "finite-atomic-oracle-binary64-mass-vector;float64-approximate-"
    "normalization-from-exact-q_repr-inputs;not-operational-sampler-or-"
    "analytic-reference-law-or-analytic-normalizer",
    "operational-reference-sampling-interface-trace;conceptual-P_ref^op-law-"
    "unspecified;uint64-quota-acceptance-not-exact-exponential-Bernoulli",
    "operational-reference-sampling-interface-trace;conceptual-P_ref^op-law-"
    "unspecified;float64-realized-weight-normalization-and-53-bit-categorical-"
    "transform;finite-J-SIR-not-exact-target-sampling",
)

MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET = 4_096
MIXED_SUPPORT_INITIALIZER_V2_RAW_WORD_BITS = 64
MIXED_SUPPORT_INITIALIZER_V2_SIR_UNIFORM_BITS = 53
MIXED_SUPPORT_INITIALIZER_V2_DEFAULT_ESS_WARNING_FRACTION = 0.25

_SCHEMA = MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCHEMA_VERSION
_STRATEGIES = MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_STRATEGIES
_D = UINT64_EXP_QUOTA_DENOMINATOR
_MAX_ID = (1 << 64) - 1
_MAX_EXACT_BITS = 16_384
_ZERO_SHA256 = "0" * 64
_MAX_DIGEST_NODES = 200_000
_MAX_DIGEST_DEPTH = 32
_MAX_DIGEST_TEXT_BYTES = 1_000_000

_PLAN_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_SCORED_TOKEN = object()
_ATTEMPT_TOKEN = object()
_PARTICLE_TOKEN = object()
_ATOM_TOKEN = object()
_REJECTION_RESULT_TOKEN = object()
_SIR_RESULT_TOKEN = object()
_ENUMERATION_RESULT_TOKEN = object()
_OWNER_TOKEN = object()


class MixedSupportInitialTiltInitializerV2Error(ArithmeticError):
    """Raised when a v2 initializer cannot satisfy its sealed contract."""


def _require_text(
    value: object,
    *,
    name: str,
    expected: Optional[str] = None,
    maximum_length: int = 65_536,
) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > maximum_length:
        raise ValueError("%s exceeds the text resource limit" % name)
    if expected is not None and value != expected:
        raise ValueError("%s differs" % name)
    return value


def _require_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _require_int(value: object, *, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s lies outside the supported interval" % name)
    return value


def _require_fraction(value: object, *, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError("%s must be an exact Fraction" % name)
    if (
        value.numerator.bit_length() > _MAX_EXACT_BITS
        or value.denominator.bit_length() > _MAX_EXACT_BITS
    ):
        raise MixedSupportInitialTiltInitializerV2Error(
            "%s exceeds the exact-integer resource limit" % name
        )
    return value


def _fraction_parts(numerator: object, denominator: object, *, name: str) -> Fraction:
    bound = 1 << _MAX_EXACT_BITS
    checked_numerator = _require_int(
        numerator, name=name + " numerator", minimum=-bound, maximum=bound
    )
    checked_denominator = _require_int(
        denominator, name=name + " denominator", minimum=1, maximum=bound
    )
    value = Fraction(checked_numerator, checked_denominator)
    if value.numerator != checked_numerator or value.denominator != checked_denominator:
        raise ValueError("%s fraction parts are not reduced" % name)
    return _require_fraction(value, name=name)


def _same_float(left: object, right: object) -> bool:
    return (
        type(left) is float
        and type(right) is float
        and struct.pack(">d", left) == struct.pack(">d", right)
    )


def _optional_float(value: Fraction) -> Optional[float]:
    try:
        rounded = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(rounded):
        return None
    return 0.0 if rounded == 0.0 else rounded


def _typed(
    value: object,
    *,
    state: list[int],
    depth: int,
) -> object:
    state[0] += 1
    if state[0] > _MAX_DIGEST_NODES or depth > _MAX_DIGEST_DEPTH:
        raise ValueError("semantic digest exceeds the node/depth resource limit")
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int:
        if value.bit_length() > _MAX_EXACT_BITS:
            raise ValueError("semantic digest integer exceeds the bit limit")
        encoded_integer = format(abs(value), "x")
        state[1] += len(encoded_integer)
        if state[1] > _MAX_DIGEST_TEXT_BYTES:
            raise ValueError(
                "semantic digest generated text exceeds the resource limit"
            )
        return [
            "int-hex",
            "negative" if value < 0 else "nonnegative",
            encoded_integer,
        ]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("semantic digests accept only finite floats")
        return ["float64", value.hex()]
    if type(value) is str:
        if len(value) > 65_536:
            raise ValueError("semantic digest text exceeds the per-field limit")
        encoded_length = len(value.encode("utf-8"))
        state[1] += encoded_length
        if state[1] > _MAX_DIGEST_TEXT_BYTES:
            raise ValueError("semantic digest text exceeds the resource limit")
        return ["str", value]
    if type(value) is Fraction:
        _require_fraction(value, name="semantic digest fraction")
        numerator_text = format(abs(value.numerator), "x")
        denominator_text = format(value.denominator, "x")
        state[1] += len(numerator_text) + len(denominator_text)
        if state[1] > _MAX_DIGEST_TEXT_BYTES:
            raise ValueError(
                "semantic digest generated text exceeds the resource limit"
            )
        return [
            "fraction-hex",
            "negative" if value.numerator < 0 else "nonnegative",
            numerator_text,
            denominator_text,
        ]
    if type(value) is tuple:
        if len(value) > 100_000:
            raise ValueError("semantic digest tuple exceeds the resource limit")
        return [
            "tuple",
            [_typed(item, state=state, depth=depth + 1) for item in value],
        ]
    if type(value) is dict:
        if len(value) > 1_024:
            raise ValueError("semantic digest mapping exceeds the resource limit")
        items = []
        for key in value:
            if type(key) is not str:
                raise TypeError("semantic digest mapping keys must be exact text")
        for key in sorted(value):
            items.append(
                (
                    _typed(key, state=state, depth=depth + 1),
                    _typed(value[key], state=state, depth=depth + 1),
                )
            )
        return ["mapping", items]
    raise TypeError("unsupported semantic digest type %s" % type(value).__name__)


def _digest(payload: Mapping[str, object], *, domain: bytes) -> str:
    if type(payload) is not dict:
        raise TypeError("semantic digest payload must be an exact dict")
    if type(domain) is not bytes or not domain or len(domain) > 512:
        raise ValueError("semantic digest domain is invalid")
    encoded = json.dumps(
        _typed(payload, state=[0, 0], depth=0),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(domain + encoded).hexdigest()


def _context(
    context: object, *, certificate: CertifiedInitialScoreProviderCertificateV1
) -> Tuple[float, ...]:
    if type(context) is not tuple:
        raise TypeError("residual_context must be an exact tuple")
    if len(context) != certificate.residual_context_dimension:
        raise ValueError("residual_context has the wrong dimension")
    checked = []
    for value in context:
        if type(value) is not float or not math.isfinite(value):
            raise TypeError("residual_context must contain finite built-in floats")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("residual_context must use canonical positive zero")
        checked.append(value)
    result = tuple(checked)
    if (
        certificate.residual_context_policy == "provider-fixed-exact-context"
        and result != certificate.fixed_residual_context
    ):
        raise ValueError("residual_context differs from provider-fixed context")
    return result


def _context_sha256(context: Tuple[float, ...]) -> str:
    return _digest(
        {"residual_context": context},
        domain=b"heterodiff-mixed-support-initializer-v2-context\x00",
    )


def _immutable_array(value: object, *, name: str) -> np.ndarray:
    if type(value) is not np.ndarray or value.dtype != np.dtype(np.float64):
        raise TypeError("%s must be an exact float64 ndarray" % name)
    if value.ndim != 1 or len(value) > MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET * 8:
        raise ValueError("%s has an unsupported shape" % name)
    if value.flags.writeable or not value.flags.c_contiguous:
        raise ValueError("%s must be immutable and C-contiguous" % name)
    if np.any(~np.isfinite(value)):
        raise ValueError("%s must be finite" % name)
    return value


def _make_array(values: object, *, name: str) -> np.ndarray:
    result = np.array(values, dtype=np.float64, copy=True)
    if result.ndim != 1 or np.any(~np.isfinite(result)):
        raise ValueError("%s must be a finite one-dimensional array" % name)
    result.setflags(write=False)
    return _immutable_array(result, name=name)


def _array_sha256(value: np.ndarray) -> str:
    checked = _immutable_array(value, name="digest array")
    digest = hashlib.sha256(b"heterodiff-mixed-support-initializer-v2-array\x00")
    digest.update(len(checked).to_bytes(8, "big"))
    digest.update(checked.tobytes(order="C"))
    return digest.hexdigest()


def _same_array(left: object, right: object) -> bool:
    try:
        a = _immutable_array(left, name="left array")
        b = _immutable_array(right, name="right array")
    except (TypeError, ValueError):
        return False
    return a.shape == b.shape and a.tobytes() == b.tobytes()


def _reference_sampling_array(
    value: object, *, name: str, expected_length: int
) -> np.ndarray:
    expected_length = _require_int(
        expected_length,
        name=name + " expected length",
        minimum=1,
        maximum=_reference.MAX_CONFIGURATION_CARDINALITY + 1,
    )
    if type(value) is not np.ndarray or value.dtype != np.dtype(np.float64):
        raise TypeError(name + " must be an exact float64 ndarray")
    if value.ndim != 1 or len(value) != expected_length:
        raise ValueError(name + " has the wrong exact shape")
    if value.flags.writeable or not value.flags.c_contiguous:
        raise ValueError(name + " must be immutable and C-contiguous")
    if np.any(~np.isfinite(value)):
        raise ValueError(name + " must be finite")
    return value


def _same_reference_sampling_array(
    left: object, right: object, *, expected_length: int
) -> bool:
    try:
        checked_left = _reference_sampling_array(
            left,
            name="left reference sampling array",
            expected_length=expected_length,
        )
        checked_right = _reference_sampling_array(
            right,
            name="right reference sampling array",
            expected_length=expected_length,
        )
    except (TypeError, ValueError):
        return False
    return checked_left.tobytes(order="C") == checked_right.tobytes(order="C")


def _exact_scores(values: object, *, name: str) -> Tuple[Fraction, ...]:
    if type(values) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if not 1 <= len(values) <= MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET * 8:
        raise ValueError("%s has an unsupported length" % name)
    checked = []
    for value in values:
        exact = _require_fraction(value, name=name + " entry")
        if _optional_float(exact) is None:
            raise MixedSupportInitialTiltInitializerV2Error(
                "%s contains a score outside float64 normalization range" % name
            )
        checked.append(exact)
    return tuple(checked)


def normalize_mixed_support_sir_exact_log_weights_v2(
    exact_log_weights: Tuple[Fraction, ...],
) -> np.ndarray:
    """Normalize a realized exact score batch; no global lower bound is used."""

    checked = _exact_scores(exact_log_weights, name="exact_log_weights")
    logs = np.asarray([float(value) for value in checked], dtype=np.float64)
    maximum = float(np.max(logs))
    shifted = np.exp(logs - maximum)
    if np.any(~np.isfinite(shifted)) or np.any(shifted <= 0.0):
        raise MixedSupportInitialTiltInitializerV2Error(
            "positive realized SIR weights underflowed or became nonfinite"
        )
    total = math.fsum(float(value) for value in shifted)
    if not math.isfinite(total) or total <= 0.0:
        raise MixedSupportInitialTiltInitializerV2Error(
            "realized SIR weight normalization failed"
        )
    probabilities = shifted / total
    if np.any(~np.isfinite(probabilities)) or np.any(probabilities <= 0.0):
        raise MixedSupportInitialTiltInitializerV2Error(
            "normalized SIR weights are not strictly positive and finite"
        )
    return _make_array(probabilities, name="normalized SIR weights")


def select_mixed_support_sir_index_v2(normalized_weights: object, raw_word: int) -> int:
    """Apply the frozen resolution-gated 53-bit categorical transform."""

    weights = _immutable_array(normalized_weights, name="normalized_weights")
    if not 1 <= len(weights) <= MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET:
        raise ValueError("normalized_weights has an unsupported length")
    if np.any(weights <= 0.0):
        raise ValueError("normalized_weights must be strictly positive")
    if abs(math.fsum(float(value) for value in weights) - 1.0) > (
        32.0 * len(weights) * np.finfo(np.float64).eps
    ):
        raise ValueError("normalized_weights must sum to one")
    word = _require_int(raw_word, name="raw_word", minimum=0, maximum=_D - 1)
    cdf = _reference._resolution_safe_cdf(weights)
    if cdf is None:
        raise MixedSupportInitialTiltInitializerV2Error(
            "categorical weights fail the float64 resolution gate"
        )
    uniform53 = word >> (
        MIXED_SUPPORT_INITIALIZER_V2_RAW_WORD_BITS
        - MIXED_SUPPORT_INITIALIZER_V2_SIR_UNIFORM_BITS
    )
    uniform = uniform53 * (2.0**-MIXED_SUPPORT_INITIALIZER_V2_SIR_UNIFORM_BITS)
    selected = int(np.searchsorted(cdf, uniform, side="right"))
    if not 0 <= selected < len(weights):
        raise MixedSupportInitialTiltInitializerV2Error(
            "categorical transform escaped the particle range"
        )
    return selected


def normalize_mixed_support_atomic_exact_log_weights_v2(
    base_masses: object,
    exact_log_weights: Tuple[Fraction, ...],
) -> Tuple[np.ndarray, float]:
    """Normalize a finite represented atomic PMF times exact score weights."""

    exact = _exact_scores(exact_log_weights, name="exact_log_weights")
    masses = _immutable_array(base_masses, name="base_masses")
    if len(masses) != len(exact) or not len(masses):
        raise ValueError("base_masses and scores must have one matching support")
    if np.any(masses <= 0.0):
        raise ValueError("base_masses must be strictly positive")
    base_total = math.fsum(float(value) for value in masses)
    if abs(base_total - 1.0) > (32.0 * len(masses) * np.finfo(np.float64).eps):
        raise ValueError("base_masses must sum to one")
    normalized_base = _make_array(
        masses / base_total,
        name="normalized finite-atomic base masses",
    )
    if all(value == exact[0] for value in exact):
        constant = _optional_float(exact[0])
        if constant is None:  # pragma: no cover - protected by _exact_scores
            raise MixedSupportInitialTiltInitializerV2Error(
                "constant atomic score is outside float64 range"
            )
        return normalized_base, constant
    logs = np.asarray(
        [
            math.log(float(normalized_base[index])) + float(q)
            for index, q in enumerate(exact)
        ],
        dtype=np.float64,
    )
    if np.any(~np.isfinite(logs)):
        raise MixedSupportInitialTiltInitializerV2Error(
            "finite-atomic represented log mass is nonfinite"
        )
    maximum = float(np.max(logs))
    shifted = np.exp(logs - maximum)
    if np.any(~np.isfinite(shifted)) or np.any(shifted <= 0.0):
        raise MixedSupportInitialTiltInitializerV2Error(
            "a positive finite-atomic represented mass underflowed"
        )
    total = math.fsum(float(value) for value in shifted)
    probabilities = _make_array(
        shifted / total, name="finite-atomic normalized probabilities"
    )
    if np.any(probabilities <= 0.0):
        raise MixedSupportInitialTiltInitializerV2Error(
            "normalization erased a positive finite-atomic mass"
        )
    return probabilities, maximum + math.log(total)


def _rng_state_sha256(state: object) -> str:
    digest = hashlib.sha256(b"heterodiff-mixed-support-initializer-v2-philox-state\x00")
    nodes = [0]

    def update(value: object, depth: int) -> None:
        nodes[0] += 1
        if nodes[0] > 4_096 or depth > 16:
            raise ValueError("Philox state exceeds the digest resource limit")
        if value is None:
            digest.update(b"N")
        elif type(value) is bool:
            digest.update(b"B1" if value else b"B0")
        elif isinstance(value, np.integer) or type(value) is int:
            integer = int(value)
            raw = abs(integer).to_bytes(
                max(1, (abs(integer).bit_length() + 7) // 8), "big"
            )
            digest.update(b"I-" if integer < 0 else b"I+")
            digest.update(len(raw).to_bytes(8, "big"))
            digest.update(raw)
        elif type(value) is str:
            raw = value.encode("utf-8")
            digest.update(b"S" + len(raw).to_bytes(8, "big") + raw)
        elif type(value) is dict:
            digest.update(b"D")
            for key in sorted(value):
                if type(key) is not str:
                    raise TypeError("Philox state keys must be exact text")
                update(key, depth + 1)
                update(value[key], depth + 1)
            digest.update(b"d")
        elif type(value) is tuple:
            digest.update(b"T")
            for item in value:
                update(item, depth + 1)
            digest.update(b"t")
        elif type(value) is np.ndarray:
            if value.nbytes > 16_384 or value.dtype.hasobject:
                raise ValueError("Philox state array is unsupported")
            digest.update(b"A")
            update(value.dtype.str, depth + 1)
            update(tuple(int(item) for item in value.shape), depth + 1)
            digest.update(value.tobytes(order="C"))
        else:
            raise TypeError("unsupported Philox state value")

    update(state, 0)
    return digest.hexdigest()


def _new_philox(seed: int) -> np.random.Generator:
    checked = _require_int(seed, name="Philox seed", minimum=0, maximum=_MAX_ID)
    rng = np.random.Generator(np.random.Philox(checked))
    if type(rng.bit_generator) is not np.random.Philox:
        raise RuntimeError("NumPy did not construct exact Philox")
    _rng_state_sha256(rng.bit_generator.state)
    return rng


def _derive_seed(
    seed: int,
    stream_role: str,
    role_sha256: str,
    context_sha256: str,
    provider_certificate_sha256: str,
    *,
    strategy: str,
    sir_particle_budget: Optional[int] = None,
) -> int:
    if strategy not in ("bounded-rejection", "fixed-budget-sir"):
        raise ValueError("stochastic strategy is unknown")
    if stream_role not in ("proposal", "rejection-decision", "sir-resampling"):
        raise ValueError("stream role is unknown")
    if stream_role == "rejection-decision" and strategy != "bounded-rejection":
        raise ValueError("rejection stream requires bounded rejection")
    if stream_role == "sir-resampling" and strategy != "fixed-budget-sir":
        raise ValueError("resampling stream requires SIR")
    if stream_role == "sir-resampling":
        bound_budget = _require_int(
            sir_particle_budget,
            name="SIR stream particle budget",
            minimum=1,
            maximum=MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET,
        )
    else:
        if sir_particle_budget is not None:
            raise ValueError("only the SIR resampling stream binds a budget")
        bound_budget = None
    digest = hashlib.sha256(
        b"heterodiff-mixed-support-initializer-derived-stream-v2\x00"
    )
    digest.update(strategy.encode("ascii") + b"\x00")
    digest.update(stream_role.encode("ascii") + b"\x00")
    digest.update(seed.to_bytes(8, "big"))
    digest.update(bytes.fromhex(role_sha256))
    digest.update(bytes.fromhex(context_sha256))
    digest.update(
        bytes.fromhex(
            _require_sha256(
                provider_certificate_sha256,
                name="stream provider-certificate digest",
            )
        )
    )
    if bound_budget is None:
        digest.update(b"no-particle-budget\x00")
    else:
        digest.update(b"sir-particle-budget\x00")
        digest.update(bound_budget.to_bytes(8, "big"))
    result = int.from_bytes(digest.digest()[:8], "big")
    return result ^ (1 << 63) if result == seed else result


def _runtime_sha256() -> str:
    probe = _new_philox(0)
    first = int(probe.bit_generator.random_raw())
    return _digest(
        {
            "schema": _SCHEMA,
            "python": platform.python_implementation(),
            "python_version": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.system(),
            "machine": platform.machine(),
            "philox": np.random.Philox.__module__ + "." + np.random.Philox.__name__,
            "seed_zero_first_word": first,
        },
        domain=b"heterodiff-mixed-support-initializer-runtime-v2\x00",
    )


def _preflight_resources(
    reference: CappedPoissonConfigurationReference, *, strategy: str, budget: int
) -> Tuple[
    str, int, int, int, int, Optional[Tuple[Tuple[int, ...], ...]], Optional[np.ndarray]
]:
    occurrence_limit = _require_int(
        _reference.MAX_REFERENCE_BATCH_OCCURRENCES,
        name="reference occurrence limit",
        minimum=1,
        maximum=(1 << 63) - 1,
    )
    coordinate_limit = _require_int(
        _reference.MAX_REFERENCE_BATCH_COORDINATES,
        name="reference coordinate limit",
        minimum=1,
        maximum=(1 << 63) - 1,
    )
    if strategy == "finite-atomic-enumeration":
        if budget != 0:
            raise ValueError("enumeration preflight requires zero budget")
        space, _, masses = reference.finite_atomic_oracle()
        states = tuple(tuple(int(value) for value in state) for state in space.states)
        immutable_masses = _make_array(masses, name="oracle base masses")
        return (
            "finite-atomic-oracle",
            occurrence_limit,
            coordinate_limit,
            0,
            0,
            states,
            immutable_masses,
        )
    checked_budget = _require_int(
        budget,
        name="stochastic budget",
        minimum=1,
        maximum=MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET,
    )
    worst_occurrences = checked_budget * reference.total_cap
    worst_coordinates = worst_occurrences * max(reference.type_dimensions.values())
    if worst_occurrences > occurrence_limit or worst_coordinates > coordinate_limit:
        raise ValueError("planned stochastic work exceeds reference resource limits")
    rebuilt_count_reference = _reference.CappedPoissonConfigurationReference(
        {0: 0},
        {0: 1.0},
        activity=reference.activity,
        total_cap=reference.total_cap,
    )
    count_probabilities = reference._count_probability_vector
    expected_count_probabilities = rebuilt_count_reference._count_probability_vector
    expected_count_cdf = rebuilt_count_reference._count_sampling_cdf
    actual_count_cdf = reference._count_sampling_cdf
    if (
        expected_count_probabilities is None
        or count_probabilities is None
        or not _same_reference_sampling_array(
            count_probabilities,
            expected_count_probabilities,
            expected_length=reference.total_cap + 1,
        )
        or expected_count_cdf is None
        or actual_count_cdf is None
        or not _same_reference_sampling_array(
            actual_count_cdf,
            expected_count_cdf,
            expected_length=reference.total_cap + 1,
        )
    ):
        raise _reference.UnsupportedReferenceSamplingError(
            "count categorical law fails the pre-RNG sampling-resolution preflight"
        )
    if reference.total_cap > 0:
        type_probabilities = reference._type_weight_vector
        raw_expected_type_probabilities = np.array(
            [reference.type_weights[type_id] for type_id in reference.type_ids],
            dtype=np.float64,
        )
        raw_expected_type_probabilities.setflags(write=False)
        expected_type_probabilities = _reference_sampling_array(
            raw_expected_type_probabilities,
            name="rebuilt reference type probabilities",
            expected_length=len(reference.type_ids),
        )
        expected_type_cdf = _reference._resolution_safe_cdf(expected_type_probabilities)
        actual_type_cdf = reference._type_sampling_cdf
        if (
            not _same_reference_sampling_array(
                type_probabilities,
                expected_type_probabilities,
                expected_length=len(reference.type_ids),
            )
            or expected_type_cdf is None
            or actual_type_cdf is None
            or not _same_reference_sampling_array(
                actual_type_cdf,
                expected_type_cdf,
                expected_length=len(reference.type_ids),
            )
        ):
            raise _reference.UnsupportedReferenceSamplingError(
                "type categorical law fails the pre-RNG sampling-resolution preflight"
            )
    return (
        "stochastic-worst-case",
        occurrence_limit,
        coordinate_limit,
        worst_occurrences,
        worst_coordinates,
        None,
        None,
    )


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltInitializerPlanV2:
    schema_version: str
    provider: CertifiedInitialScoreProviderV1
    provider_certificate: CertifiedInitialScoreProviderCertificateV1
    provider_certificate_sha256: str
    provider_runtime_identity: int
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    initializer_role_sha256: str
    strategy: str
    seed: Optional[int]
    budget: int
    ess_warning_fraction: Optional[float]
    adaptive_fallback_permitted: bool
    plan_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _PLAN_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("plans require the exact public factory fields")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_plan(self)

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 plans cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 plans are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return ("mixed-support-initializer-plan-v2", self.plan_sha256)


def _plan_payload(
    plan: MixedSupportInitialTiltInitializerPlanV2,
) -> Mapping[str, object]:
    return {
        "schema_version": plan.schema_version,
        "provider_certificate_sha256": plan.provider_certificate_sha256,
        "provider_runtime_identity": plan.provider_runtime_identity,
        "residual_context_sha256": plan.residual_context_sha256,
        "initializer_role_sha256": plan.initializer_role_sha256,
        "strategy": plan.strategy,
        "seed": plan.seed,
        "budget": plan.budget,
        "ess_warning_fraction": plan.ess_warning_fraction,
        "adaptive_fallback_permitted": plan.adaptive_fallback_permitted,
    }


def _validate_plan(plan: object) -> MixedSupportInitialTiltInitializerPlanV2:
    if type(plan) is not MixedSupportInitialTiltInitializerPlanV2:
        raise TypeError("plan has the wrong exact v2 type")
    _require_text(
        plan.schema_version,
        name="plan.schema_version",
        expected=_SCHEMA,
    )
    if type(plan.provider) is not CertifiedInitialScoreProviderV1:
        raise TypeError("plan provider has the wrong exact type")
    certificate = validate_certified_initial_score_provider_v1_certificate(
        plan.provider
    )
    if plan.provider_certificate is not certificate:
        raise ValueError("plan provider certificate identity differs")
    _require_sha256(
        plan.provider_certificate_sha256,
        name="plan provider-certificate digest",
    )
    if plan.provider_certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("plan provider certificate digest differs")
    _require_int(
        plan.provider_runtime_identity,
        name="provider identity",
        minimum=0,
        maximum=_MAX_ID,
    )
    if plan.provider_runtime_identity != id(plan.provider):
        raise ValueError("plan provider identity differs")
    context = _context(plan.residual_context, certificate=certificate)
    if context != plan.residual_context:
        raise ValueError("plan context is noncanonical")
    _require_sha256(
        plan.residual_context_sha256,
        name="plan residual-context digest",
    )
    if plan.residual_context_sha256 != _context_sha256(context):
        raise ValueError("plan context digest differs")
    _require_sha256(plan.initializer_role_sha256, name="initializer role")
    strategy = _require_text(
        plan.strategy,
        name="plan.strategy",
        maximum_length=64,
    )
    if strategy not in _STRATEGIES:
        raise ValueError("plan strategy is unknown")
    if (
        type(plan.adaptive_fallback_permitted) is not bool
        or plan.adaptive_fallback_permitted
    ):
        raise ValueError("adaptive fallback is forbidden")
    if strategy == "finite-atomic-enumeration":
        _require_int(
            plan.budget,
            name="enumeration plan budget",
            minimum=0,
            maximum=0,
        )
        if plan.seed is not None or plan.ess_warning_fraction is not None:
            raise ValueError("enumeration requires no seed, budget, or ESS threshold")
    else:
        _require_int(plan.seed, name="plan seed", minimum=0, maximum=_MAX_ID)
        _require_int(
            plan.budget,
            name="plan budget",
            minimum=1,
            maximum=MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET,
        )
        if strategy == "bounded-rejection":
            if plan.ess_warning_fraction is not None:
                raise ValueError("rejection accepts no ESS threshold")
        else:
            if type(plan.ess_warning_fraction) is not float or not math.isfinite(
                plan.ess_warning_fraction
            ):
                raise TypeError("SIR ESS threshold must be a finite exact float")
            if not 0.0 < plan.ess_warning_fraction <= 1.0:
                raise ValueError("SIR ESS threshold must lie in (0,1]")
    _require_sha256(plan.plan_sha256, name="plan digest")
    if plan.plan_sha256 != _digest(
        _plan_payload(plan), domain=b"heterodiff-mixed-support-initializer-plan-v2\x00"
    ):
        raise ValueError("plan digest differs")
    return plan


def make_mixed_support_initial_tilt_initializer_plan_v2(
    provider: CertifiedInitialScoreProviderV1,
    *,
    strategy: object,
    residual_context: object,
    initializer_role_sha256: object,
    seed: Optional[object] = None,
    budget: Optional[object] = None,
    ess_warning_fraction: Optional[object] = None,
) -> MixedSupportInitialTiltInitializerPlanV2:
    """Freeze provider, context, strategy, and all stochastic resources."""

    if type(provider) is not CertifiedInitialScoreProviderV1:
        raise TypeError("provider must be an exact CertifiedInitialScoreProviderV1")
    certificate = validate_certified_initial_score_provider_v1_certificate(provider)
    if type(strategy) is not str or strategy not in _STRATEGIES:
        raise ValueError("strategy must be one of the exported v2 strategies")
    context = _context(residual_context, certificate=certificate)
    role = _require_sha256(initializer_role_sha256, name="initializer_role_sha256")
    if strategy == "finite-atomic-enumeration":
        if seed is not None or ess_warning_fraction is not None:
            raise ValueError("enumeration accepts no stochastic arguments")
        if budget is not None:
            _require_int(
                budget,
                name="enumeration budget",
                minimum=0,
                maximum=0,
            )
        checked_seed, checked_budget, checked_ess = None, 0, None
    else:
        checked_seed = _require_int(seed, name="seed", minimum=0, maximum=_MAX_ID)
        checked_budget = _require_int(
            budget,
            name="budget",
            minimum=1,
            maximum=MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET,
        )
        if strategy == "fixed-budget-sir":
            raw = (
                MIXED_SUPPORT_INITIALIZER_V2_DEFAULT_ESS_WARNING_FRACTION
                if ess_warning_fraction is None
                else ess_warning_fraction
            )
            if type(raw) is not float or not math.isfinite(raw) or not 0.0 < raw <= 1.0:
                raise ValueError("ess_warning_fraction must be an exact float in (0,1]")
            checked_ess = raw
        else:
            if ess_warning_fraction is not None:
                raise ValueError("rejection accepts no ESS threshold")
            checked_ess = None
    values = {
        "schema_version": _SCHEMA,
        "provider": provider,
        "provider_certificate": certificate,
        "provider_certificate_sha256": certificate.certificate_sha256,
        "provider_runtime_identity": id(provider),
        "residual_context": context,
        "residual_context_sha256": _context_sha256(context),
        "initializer_role_sha256": role,
        "strategy": strategy,
        "seed": checked_seed,
        "budget": checked_budget,
        "ess_warning_fraction": checked_ess,
        "adaptive_fallback_permitted": False,
        "plan_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(MixedSupportInitialTiltInitializerPlanV2)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["plan_sha256"] = _digest(
        _plan_payload(provisional),
        domain=b"heterodiff-mixed-support-initializer-plan-v2\x00",
    )
    return MixedSupportInitialTiltInitializerPlanV2(
        **values, _construction_token=_PLAN_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltInitializerCertificateV2:
    schema_version: str
    certificate_scope: str
    target_policy: str
    executed_measure_policy: str
    nonclaim_statement: str
    provider: CertifiedInitialScoreProviderV1
    provider_runtime_identity: int
    provider_certificate: CertifiedInitialScoreProviderCertificateV1
    provider_certificate_sha256: str
    reference: CappedPoissonConfigurationReference
    reference_runtime_identity: int
    reference_parameter_sha256: str
    plan: MixedSupportInitialTiltInitializerPlanV2
    plan_sha256: str
    strategy: str
    exact_log_weight_upper_bound: Fraction
    exact_log_weight_upper_bound_numerator: int
    exact_log_weight_upper_bound_denominator: int
    exact_log_weight_lower_bound: Optional[Fraction]
    exact_global_lower_bound_available: bool
    lower_bound_required_by_strategy: bool
    proposal_seed: Optional[int]
    rejection_decision_seed: Optional[int]
    sir_resampling_seed: Optional[int]
    resource_preflight_mode: str
    reference_occurrence_limit: int
    reference_coordinate_limit: int
    worst_case_occurrences: int
    worst_case_coordinates: int
    enumeration_state_count: Optional[int]
    enumeration_states_sha256: Optional[str]
    enumeration_base_masses_sha256: Optional[str]
    arbitrary_rational_quota_required: bool
    fixed_budget_work_certified: bool
    explicit_rejection_exhaustion: bool
    structural_result_validation_replays_provider_evaluate: bool
    structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation: bool
    structural_result_validation_replays_reference_sampler: bool
    structural_result_validation_replays_rng: bool
    operational_reference_sampling_law_verified: bool
    philox_uniformity_verified: bool
    stream_independence_verified: bool
    iid_proposals_verified: bool
    analytic_target_equality_verified: bool
    exact_operational_rejection_bernoulli_verified: bool
    finite_j_sir_exact_target_verified: bool
    source_or_model_quality_evidence: bool
    path_or_sampler_admitted: bool
    formal_test_28_closed: bool
    certificate_digest_cross_process_stable: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    runtime_sha256: str
    certificate_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("certificates require the exact module-created fields")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 certificates cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 certificates are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "mixed-support-initializer-kernel-certificate-v2",
            self.certificate_sha256,
        )


def _certificate_payload(
    certificate: MixedSupportInitialTiltInitializerCertificateV2,
) -> Mapping[str, object]:
    omitted = {
        "provider",
        "provider_certificate",
        "reference",
        "plan",
        "certificate_sha256",
    }
    return {
        name: getattr(certificate, name)
        for name in certificate.__annotations__
        if name not in omitted
    }


def _planned_seeds(
    plan: MixedSupportInitialTiltInitializerPlanV2,
) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    if plan.strategy == "finite-atomic-enumeration":
        return None, None, None
    proposal = _derive_seed(
        plan.seed,
        "proposal",
        plan.initializer_role_sha256,
        plan.residual_context_sha256,
        plan.provider_certificate_sha256,
        strategy=plan.strategy,
    )
    used = {plan.seed, proposal}

    def unique(candidate: int) -> int:
        while candidate in used:
            candidate = (candidate + 1) % (1 << 64)
        used.add(candidate)
        return candidate

    if plan.strategy == "bounded-rejection":
        decision = unique(
            _derive_seed(
                plan.seed,
                "rejection-decision",
                plan.initializer_role_sha256,
                plan.residual_context_sha256,
                plan.provider_certificate_sha256,
                strategy=plan.strategy,
            )
        )
        return proposal, decision, None
    resampling = unique(
        _derive_seed(
            plan.seed,
            "sir-resampling",
            plan.initializer_role_sha256,
            plan.residual_context_sha256,
            plan.provider_certificate_sha256,
            strategy=plan.strategy,
            sir_particle_budget=plan.budget,
        )
    )
    return proposal, None, resampling


def _executed_measure_policy(strategy: str) -> str:
    checked = _require_text(
        strategy,
        name="executed-measure strategy",
        maximum_length=64,
    )
    try:
        index = _STRATEGIES.index(checked)
    except ValueError as error:
        raise ValueError("executed-measure strategy is unknown") from error
    return MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_EXECUTED_MEASURE_POLICIES[index]


def _make_certificate(
    provider: CertifiedInitialScoreProviderV1,
    plan: MixedSupportInitialTiltInitializerPlanV2,
) -> MixedSupportInitialTiltInitializerCertificateV2:
    checked_plan = _validate_plan(plan)
    matched = require_matching_certified_initial_score_provider_v1(
        provider, provider.reference
    )
    if checked_plan.provider is not matched:
        raise ValueError("plan belongs to another provider")
    source = validate_certified_initial_score_provider_v1_certificate(provider)
    reference = provider.reference
    preflight = _preflight_resources(
        reference, strategy=plan.strategy, budget=plan.budget
    )
    (
        mode,
        occurrence_limit,
        coordinate_limit,
        worst_occurrences,
        worst_coordinates,
        states,
        masses,
    ) = preflight
    proposal, decision, resampling = _planned_seeds(plan)
    upper = _require_fraction(
        source.exact_log_weight_upper_bound, name="provider upper bound"
    )
    lower = source.exact_log_weight_lower_bound
    if lower is not None:
        lower = _require_fraction(lower, name="provider optional lower bound")
    values = {
        "schema_version": _SCHEMA,
        "certificate_scope": MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCOPE,
        "target_policy": MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_TARGET_POLICY,
        "executed_measure_policy": _executed_measure_policy(plan.strategy),
        "nonclaim_statement": MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_NONCLAIM,
        "provider": provider,
        "provider_runtime_identity": id(provider),
        "provider_certificate": source,
        "provider_certificate_sha256": source.certificate_sha256,
        "reference": reference,
        "reference_runtime_identity": id(reference),
        "reference_parameter_sha256": source.reference_parameter_sha256,
        "plan": plan,
        "plan_sha256": plan.plan_sha256,
        "strategy": plan.strategy,
        "exact_log_weight_upper_bound": upper,
        "exact_log_weight_upper_bound_numerator": upper.numerator,
        "exact_log_weight_upper_bound_denominator": upper.denominator,
        "exact_log_weight_lower_bound": lower,
        "exact_global_lower_bound_available": lower is not None,
        "lower_bound_required_by_strategy": False,
        "proposal_seed": proposal,
        "rejection_decision_seed": decision,
        "sir_resampling_seed": resampling,
        "resource_preflight_mode": mode,
        "reference_occurrence_limit": occurrence_limit,
        "reference_coordinate_limit": coordinate_limit,
        "worst_case_occurrences": worst_occurrences,
        "worst_case_coordinates": worst_coordinates,
        "enumeration_state_count": None if states is None else len(states),
        "enumeration_states_sha256": None
        if states is None
        else _digest(
            {"states": states},
            domain=b"heterodiff-mixed-support-enumeration-states-v2\x00",
        ),
        "enumeration_base_masses_sha256": None
        if masses is None
        else _array_sha256(masses),
        "arbitrary_rational_quota_required": plan.strategy == "bounded-rejection",
        "fixed_budget_work_certified": True,
        "explicit_rejection_exhaustion": plan.strategy == "bounded-rejection",
        "structural_result_validation_replays_provider_evaluate": False,
        "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation": False,
        "structural_result_validation_replays_reference_sampler": False,
        "structural_result_validation_replays_rng": False,
        "operational_reference_sampling_law_verified": False,
        "philox_uniformity_verified": False,
        "stream_independence_verified": False,
        "iid_proposals_verified": False,
        "analytic_target_equality_verified": False,
        "exact_operational_rejection_bernoulli_verified": False,
        "finite_j_sir_exact_target_verified": False,
        "source_or_model_quality_evidence": False,
        "path_or_sampler_admitted": False,
        "formal_test_28_closed": False,
        "certificate_digest_cross_process_stable": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "runtime_sha256": _runtime_sha256(),
        "certificate_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(MixedSupportInitialTiltInitializerCertificateV2)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["certificate_sha256"] = _digest(
        _certificate_payload(provisional),
        domain=b"heterodiff-mixed-support-initializer-certificate-v2\x00",
    )
    return MixedSupportInitialTiltInitializerCertificateV2(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


def _validate_certificate(
    certificate: object,
) -> MixedSupportInitialTiltInitializerCertificateV2:
    if type(certificate) is not MixedSupportInitialTiltInitializerCertificateV2:
        raise TypeError("certificate has the wrong exact v2 type")
    _require_text(
        certificate.schema_version,
        name="certificate.schema_version",
        expected=_SCHEMA,
    )
    _require_text(
        certificate.certificate_scope,
        name="certificate.certificate_scope",
        expected=MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCOPE,
    )
    _require_text(
        certificate.target_policy,
        name="certificate.target_policy",
        expected=MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_TARGET_POLICY,
    )
    _require_text(
        certificate.executed_measure_policy,
        name="certificate.executed_measure_policy",
        expected=_executed_measure_policy(certificate.strategy),
    )
    _require_text(
        certificate.nonclaim_statement,
        name="certificate.nonclaim_statement",
        expected=MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_NONCLAIM,
    )
    plan = _validate_plan(certificate.plan)
    provider_source = validate_certified_initial_score_provider_v1_certificate(
        certificate.provider
    )
    if (
        certificate.provider is not plan.provider
        or certificate.provider_certificate is not provider_source
    ):
        raise ValueError("certificate provider ancestry differs")
    for value, expected, name in (
        (certificate.provider_runtime_identity, id(certificate.provider), "provider"),
        (
            certificate.reference_runtime_identity,
            id(certificate.reference),
            "reference",
        ),
    ):
        _require_int(value, name=name + " identity", minimum=0, maximum=_MAX_ID)
        if value != expected:
            raise ValueError("certificate %s identity differs" % name)
    if certificate.reference is not provider_source.reference:
        raise ValueError("certificate reference differs")
    _require_sha256(
        certificate.provider_certificate_sha256,
        name="certificate provider digest",
    )
    if certificate.provider_certificate_sha256 != provider_source.certificate_sha256:
        raise ValueError("certificate provider digest differs")
    _require_sha256(
        certificate.reference_parameter_sha256,
        name="certificate reference-parameter digest",
    )
    if (
        certificate.reference_parameter_sha256
        != provider_source.reference_parameter_sha256
    ):
        raise ValueError("certificate reference parameter digest differs")
    _require_sha256(certificate.plan_sha256, name="certificate plan digest")
    certificate_strategy = _require_text(
        certificate.strategy,
        name="certificate.strategy",
        maximum_length=64,
    )
    if (
        certificate.plan_sha256 != plan.plan_sha256
        or certificate_strategy != plan.strategy
    ):
        raise ValueError("certificate plan binding differs")
    upper = _require_fraction(
        certificate.exact_log_weight_upper_bound, name="certificate upper bound"
    )
    if upper != provider_source.exact_log_weight_upper_bound:
        raise ValueError("certificate upper bound differs")
    if (
        _fraction_parts(
            certificate.exact_log_weight_upper_bound_numerator,
            certificate.exact_log_weight_upper_bound_denominator,
            name="certificate upper bound",
        )
        != upper
    ):
        raise ValueError("certificate upper bound parts differ")
    lower = certificate.exact_log_weight_lower_bound
    if lower is not None:
        lower = _require_fraction(lower, name="certificate optional lower bound")
    if lower != provider_source.exact_log_weight_lower_bound:
        raise ValueError("certificate optional lower bound differs")
    if type(certificate.exact_global_lower_bound_available) is not bool:
        raise TypeError(
            "certificate.exact_global_lower_bound_available must be an exact Boolean"
        )
    if certificate.exact_global_lower_bound_available != (lower is not None):
        raise ValueError("certificate lower-bound availability differs")
    true_flags = ("fixed_budget_work_certified",)
    false_flags = (
        "lower_bound_required_by_strategy",
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
        "certificate_digest_cross_process_stable",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in true_flags + false_flags + ("arbitrary_rational_quota_required",):
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be an exact Boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags) or any(
        getattr(certificate, name) for name in false_flags
    ):
        raise ValueError("certificate claim flags differ")
    if certificate.arbitrary_rational_quota_required != (
        plan.strategy == "bounded-rejection"
    ):
        raise ValueError("certificate quota requirement differs")
    if type(certificate.explicit_rejection_exhaustion) is not bool:
        raise TypeError(
            "certificate.explicit_rejection_exhaustion must be an exact Boolean"
        )
    if certificate.explicit_rejection_exhaustion != (
        plan.strategy == "bounded-rejection"
    ):
        raise ValueError("certificate exhaustion flag differs")
    expected = _make_certificate_fields_without_runtime_reentry(certificate)
    for name, wanted in expected.items():
        supplied = getattr(certificate, name)
        if type(supplied) is float and type(wanted) is float:
            matches = _same_float(supplied, wanted)
        else:
            matches = type(supplied) is type(wanted) and supplied == wanted
        if not matches:
            raise ValueError("certificate.%s differs from sealed plan" % name)
    _require_sha256(certificate.runtime_sha256, name="certificate runtime digest")
    _require_sha256(certificate.certificate_sha256, name="certificate digest")
    if certificate.certificate_sha256 != _digest(
        _certificate_payload(certificate),
        domain=b"heterodiff-mixed-support-initializer-certificate-v2\x00",
    ):
        raise ValueError("certificate digest differs")
    return certificate


def _make_certificate_fields_without_runtime_reentry(
    certificate: MixedSupportInitialTiltInitializerCertificateV2,
) -> Mapping[str, object]:
    plan = certificate.plan
    reference = certificate.reference
    (
        mode,
        occurrence_limit,
        coordinate_limit,
        worst_occurrences,
        worst_coordinates,
        states,
        masses,
    ) = _preflight_resources(reference, strategy=plan.strategy, budget=plan.budget)
    proposal, decision, resampling = _planned_seeds(plan)
    return {
        "proposal_seed": proposal,
        "rejection_decision_seed": decision,
        "sir_resampling_seed": resampling,
        "resource_preflight_mode": mode,
        "reference_occurrence_limit": occurrence_limit,
        "reference_coordinate_limit": coordinate_limit,
        "worst_case_occurrences": worst_occurrences,
        "worst_case_coordinates": worst_coordinates,
        "enumeration_state_count": None if states is None else len(states),
        "enumeration_states_sha256": None
        if states is None
        else _digest(
            {"states": states},
            domain=b"heterodiff-mixed-support-enumeration-states-v2\x00",
        ),
        "enumeration_base_masses_sha256": None
        if masses is None
        else _array_sha256(masses),
    }


def validate_mixed_support_initial_tilt_initializer_certificate_v2(
    certificate: object,
) -> MixedSupportInitialTiltInitializerCertificateV2:
    """Structurally validate one v2 kernel certificate."""

    return _validate_certificate(certificate)


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltScoredConfigurationV2:
    certificate: MixedSupportInitialTiltInitializerCertificateV2
    certificate_sha256: str
    index: int
    configuration: TransformedConfiguration
    configuration_sha256: str
    evaluation: CertifiedInitialScorePointEvaluationV1
    evaluation_sha256: str
    exact_log_weight: Fraction
    exact_log_weight_numerator: int
    exact_log_weight_denominator: int
    rounded_log_weight: Optional[float]
    scored_configuration_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _SCORED_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("scored records are kernel-created")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_scored(self, certificate=values["certificate"])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 scored records are not pickle objects")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 scored records cannot be subclassed")


def _scored_payload(
    record: MixedSupportInitialTiltScoredConfigurationV2,
) -> Mapping[str, object]:
    return {
        "certificate_sha256": record.certificate_sha256,
        "index": record.index,
        "configuration_sha256": record.configuration_sha256,
        "evaluation_sha256": record.evaluation_sha256,
        "exact_log_weight": record.exact_log_weight,
        "rounded_log_weight": record.rounded_log_weight,
    }


def _validate_scored(
    record: object, *, certificate: MixedSupportInitialTiltInitializerCertificateV2
) -> MixedSupportInitialTiltScoredConfigurationV2:
    if type(record) is not MixedSupportInitialTiltScoredConfigurationV2:
        raise TypeError("scored record has the wrong exact v2 type")
    _require_sha256(record.certificate_sha256, name="scored certificate digest")
    if (
        record.certificate is not certificate
        or record.certificate_sha256 != certificate.certificate_sha256
    ):
        raise ValueError("scored record certificate differs")
    _require_int(
        record.index,
        name="scored index",
        minimum=0,
        maximum=MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET * 8,
    )
    evaluation = _score._validate_evaluation_structure(
        record.evaluation, certificate=certificate.provider_certificate
    )
    _require_sha256(record.configuration_sha256, name="scored configuration digest")
    _require_sha256(record.evaluation_sha256, name="scored evaluation digest")
    if (
        record.configuration is not evaluation.configuration
        or record.configuration_sha256 != evaluation.configuration_sha256
    ):
        raise ValueError("scored configuration differs from provider evaluation")
    if record.evaluation_sha256 != evaluation.evaluation_sha256:
        raise ValueError("scored evaluation digest differs")
    exact = _require_fraction(record.exact_log_weight, name="scored exact log weight")
    if (
        exact != evaluation.exact_log_weight
        or _fraction_parts(
            record.exact_log_weight_numerator,
            record.exact_log_weight_denominator,
            name="scored exact log weight",
        )
        != exact
    ):
        raise ValueError("scored exact log weight differs")
    expected_rounded = _optional_float(exact)
    if expected_rounded is None:
        if record.rounded_log_weight is not None:
            raise ValueError("scored optional rounded value differs")
    elif not _same_float(record.rounded_log_weight, expected_rounded):
        raise ValueError("scored rounded value differs")
    if exact > certificate.exact_log_weight_upper_bound:
        raise ValueError("scored value exceeds certified upper bound")
    _require_sha256(record.scored_configuration_sha256, name="scored digest")
    if record.scored_configuration_sha256 != _digest(
        _scored_payload(record),
        domain=b"heterodiff-mixed-support-scored-configuration-v2\x00",
    ):
        raise ValueError("scored digest differs")
    return record


def _make_scored(
    index: int,
    evaluation: CertifiedInitialScorePointEvaluationV1,
    certificate: MixedSupportInitialTiltInitializerCertificateV2,
) -> MixedSupportInitialTiltScoredConfigurationV2:
    exact = _require_fraction(evaluation.exact_log_weight, name="provider exact score")
    values = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "index": index,
        "configuration": evaluation.configuration,
        "configuration_sha256": evaluation.configuration_sha256,
        "evaluation": evaluation,
        "evaluation_sha256": evaluation.evaluation_sha256,
        "exact_log_weight": exact,
        "exact_log_weight_numerator": exact.numerator,
        "exact_log_weight_denominator": exact.denominator,
        "rounded_log_weight": _optional_float(exact),
        "scored_configuration_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(MixedSupportInitialTiltScoredConfigurationV2)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["scored_configuration_sha256"] = _digest(
        _scored_payload(provisional),
        domain=b"heterodiff-mixed-support-scored-configuration-v2\x00",
    )
    return MixedSupportInitialTiltScoredConfigurationV2(
        **values, _construction_token=_SCORED_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltRejectionAttemptV2:
    scored: MixedSupportInitialTiltScoredConfigurationV2
    exact_delta: Fraction
    exact_delta_numerator: int
    exact_delta_denominator: int
    quota_certificate: ArbitraryRationalUInt64ExpQuotaCertificate
    quota_certificate_sha256: str
    decision_word: int
    accepted: bool
    attempt_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ATTEMPT_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("rejection attempts are kernel-created")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 rejection attempts are not pickle objects")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 rejection attempts cannot be subclassed")


def _attempt_payload(
    attempt: MixedSupportInitialTiltRejectionAttemptV2,
) -> Mapping[str, object]:
    return {
        "scored": attempt.scored.scored_configuration_sha256,
        "delta": attempt.exact_delta,
        "quota": attempt.quota_certificate_sha256,
        "decision_word": attempt.decision_word,
        "accepted": attempt.accepted,
    }


def _validate_attempt(
    attempt: object, *, certificate: MixedSupportInitialTiltInitializerCertificateV2
) -> MixedSupportInitialTiltRejectionAttemptV2:
    if type(attempt) is not MixedSupportInitialTiltRejectionAttemptV2:
        raise TypeError("attempt has the wrong exact v2 type")
    scored = _validate_scored(attempt.scored, certificate=certificate)
    delta = _require_fraction(attempt.exact_delta, name="attempt exact delta")
    if (
        _fraction_parts(
            attempt.exact_delta_numerator,
            attempt.exact_delta_denominator,
            name="attempt exact delta",
        )
        != delta
    ):
        raise ValueError("attempt delta parts differ")
    if (
        delta != scored.exact_log_weight - certificate.exact_log_weight_upper_bound
        or delta > 0
    ):
        raise ValueError("attempt delta differs from q-U or is positive")
    quota = validate_arbitrary_rational_uint64_exp_quota_certificate(
        attempt.quota_certificate
    )
    if Fraction(quota.delta_numerator, quota.delta_denominator) != delta:
        raise ValueError("attempt quota belongs to another delta")
    _require_sha256(
        attempt.quota_certificate_sha256,
        name="attempt quota-certificate digest",
    )
    if attempt.quota_certificate_sha256 != quota.certificate_sha256:
        raise ValueError("attempt quota digest differs")
    word = _require_int(
        attempt.decision_word, name="decision word", minimum=0, maximum=_D - 1
    )
    if type(attempt.accepted) is not bool or attempt.accepted != (word < quota.quota):
        raise ValueError("attempt acceptance decision differs")
    _require_sha256(attempt.attempt_sha256, name="attempt digest")
    if attempt.attempt_sha256 != _digest(
        _attempt_payload(attempt),
        domain=b"heterodiff-mixed-support-rejection-attempt-v2\x00",
    ):
        raise ValueError("attempt digest differs")
    return attempt


def _make_attempt(
    scored: MixedSupportInitialTiltScoredConfigurationV2,
    word: int,
    certificate: MixedSupportInitialTiltInitializerCertificateV2,
) -> MixedSupportInitialTiltRejectionAttemptV2:
    delta = scored.exact_log_weight - certificate.exact_log_weight_upper_bound
    if delta > 0:
        raise ValueError("provider score violates certified upper bound")
    quota = certify_arbitrary_rational_uint64_exp_quota(delta)
    values = {
        "scored": scored,
        "exact_delta": delta,
        "exact_delta_numerator": delta.numerator,
        "exact_delta_denominator": delta.denominator,
        "quota_certificate": quota,
        "quota_certificate_sha256": quota.certificate_sha256,
        "decision_word": word,
        "accepted": word < quota.quota,
        "attempt_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(MixedSupportInitialTiltRejectionAttemptV2)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["attempt_sha256"] = _digest(
        _attempt_payload(provisional),
        domain=b"heterodiff-mixed-support-rejection-attempt-v2\x00",
    )
    result = MixedSupportInitialTiltRejectionAttemptV2(
        **values, _construction_token=_ATTEMPT_TOKEN
    )
    return _validate_attempt(result, certificate=certificate)


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltSIRParticleV2:
    scored: MixedSupportInitialTiltScoredConfigurationV2
    normalized_weight: float
    particle_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _PARTICLE_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("SIR particles are kernel-created")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 SIR particles are not pickle objects")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 SIR particles cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltEnumerationAtomV2:
    count_state: Tuple[int, ...]
    base_mass: float
    scored: MixedSupportInitialTiltScoredConfigurationV2
    normalized_probability: float
    atom_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ATOM_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("enumeration atoms are kernel-created")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 enumeration atoms are not pickle objects")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 enumeration atoms cannot be subclassed")


def _particle_sha(scored_sha: str, weight: float) -> str:
    return _digest(
        {"scored": scored_sha, "weight": weight},
        domain=b"heterodiff-mixed-support-sir-particle-v2\x00",
    )


def _atom_sha(
    state: Tuple[int, ...], mass: float, scored_sha: str, probability: float
) -> str:
    return _digest(
        {
            "state": state,
            "base_mass": mass,
            "scored": scored_sha,
            "probability": probability,
        },
        domain=b"heterodiff-mixed-support-enumeration-atom-v2\x00",
    )


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltRejectionResultV2:
    certificate: MixedSupportInitialTiltInitializerCertificateV2
    certificate_sha256: str
    status: str
    attempts: Tuple[MixedSupportInitialTiltRejectionAttemptV2, ...]
    selected_index: Optional[int]
    selected_configuration: Optional[TransformedConfiguration]
    selected_configuration_sha256: Optional[str]
    proposal_stream_initial_state_sha256: str
    proposal_stream_final_state_sha256: str
    decision_stream_initial_state_sha256: str
    decision_stream_final_state_sha256: str
    result_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _REJECTION_RESULT_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("rejection results are kernel-created")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 rejection results are not pickle objects")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 rejection results cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltSIRResultV2:
    certificate: MixedSupportInitialTiltInitializerCertificateV2
    certificate_sha256: str
    status: str
    particles: Tuple[MixedSupportInitialTiltSIRParticleV2, ...]
    normalized_weights: np.ndarray
    effective_sample_size: float
    maximum_normalized_weight: float
    ess_warning: bool
    selected_index: int
    selected_configuration: TransformedConfiguration
    selected_configuration_sha256: str
    proposal_stream_initial_state_sha256: str
    proposal_stream_final_state_sha256: str
    resampling_stream_initial_state_sha256: str
    resampling_stream_final_state_sha256: str
    resampling_word: int
    resampling_uniform_53: int
    result_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _SIR_RESULT_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("SIR results are kernel-created")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 SIR results are not pickle objects")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 SIR results cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False)
class MixedSupportInitialTiltEnumerationResultV2:
    certificate: MixedSupportInitialTiltInitializerCertificateV2
    certificate_sha256: str
    status: str
    atoms: Tuple[MixedSupportInitialTiltEnumerationAtomV2, ...]
    base_masses: np.ndarray
    normalized_probabilities: np.ndarray
    represented_log_normalizer_float64: float
    result_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ENUMERATION_RESULT_TOKEN or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("enumeration results are kernel-created")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 enumeration results are not pickle objects")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 enumeration results cannot be subclassed")


MixedSupportInitialTiltInitializerResultV2 = Union[
    MixedSupportInitialTiltRejectionResultV2,
    MixedSupportInitialTiltSIRResultV2,
    MixedSupportInitialTiltEnumerationResultV2,
]


def _rejection_payload(
    result: MixedSupportInitialTiltRejectionResultV2,
) -> Mapping[str, object]:
    return {
        "certificate": result.certificate_sha256,
        "status": result.status,
        "attempts": tuple(attempt.attempt_sha256 for attempt in result.attempts),
        "selected_index": result.selected_index,
        "selected_configuration": result.selected_configuration_sha256,
        "proposal_before": result.proposal_stream_initial_state_sha256,
        "proposal_after": result.proposal_stream_final_state_sha256,
        "decision_before": result.decision_stream_initial_state_sha256,
        "decision_after": result.decision_stream_final_state_sha256,
    }


def _sir_payload(result: MixedSupportInitialTiltSIRResultV2) -> Mapping[str, object]:
    return {
        "certificate": result.certificate_sha256,
        "status": result.status,
        "particles": tuple(particle.particle_sha256 for particle in result.particles),
        "weights": _array_sha256(result.normalized_weights),
        "ess": result.effective_sample_size,
        "maximum_weight": result.maximum_normalized_weight,
        "ess_warning": result.ess_warning,
        "selected_index": result.selected_index,
        "selected_configuration": result.selected_configuration_sha256,
        "proposal_before": result.proposal_stream_initial_state_sha256,
        "proposal_after": result.proposal_stream_final_state_sha256,
        "resampling_before": result.resampling_stream_initial_state_sha256,
        "resampling_after": result.resampling_stream_final_state_sha256,
        "word": result.resampling_word,
        "uniform53": result.resampling_uniform_53,
    }


def _enumeration_payload(
    result: MixedSupportInitialTiltEnumerationResultV2,
) -> Mapping[str, object]:
    return {
        "certificate": result.certificate_sha256,
        "status": result.status,
        "atoms": tuple(atom.atom_sha256 for atom in result.atoms),
        "base_masses": _array_sha256(result.base_masses),
        "probabilities": _array_sha256(result.normalized_probabilities),
        "log_normalizer": result.represented_log_normalizer_float64,
    }


def _validate_rejection_result(
    result: object, *, certificate: MixedSupportInitialTiltInitializerCertificateV2
) -> MixedSupportInitialTiltRejectionResultV2:
    if type(result) is not MixedSupportInitialTiltRejectionResultV2:
        raise TypeError("rejection result has the wrong exact v2 type")
    _require_text(
        result.status,
        name="rejection result status",
        maximum_length=16,
    )
    _require_sha256(
        result.certificate_sha256,
        name="rejection result certificate digest",
    )
    if (
        certificate.strategy != "bounded-rejection"
        or result.certificate is not certificate
        or result.certificate_sha256 != certificate.certificate_sha256
    ):
        raise ValueError("rejection result certificate differs")
    if (
        type(result.attempts) is not tuple
        or len(result.attempts) != certificate.plan.budget
    ):
        raise ValueError("rejection result must retain every planned attempt")
    attempts = tuple(
        _validate_attempt(value, certificate=certificate) for value in result.attempts
    )
    if tuple(attempt.scored.index for attempt in attempts) != tuple(
        range(len(attempts))
    ):
        raise ValueError("rejection attempt indices are noncanonical")
    selected = next((attempt for attempt in attempts if attempt.accepted), None)
    if selected is None:
        if (
            result.status != "exhausted"
            or result.selected_index is not None
            or result.selected_configuration is not None
            or result.selected_configuration_sha256 is not None
        ):
            raise ValueError("rejection exhaustion fields differ")
    else:
        _require_int(
            result.selected_index,
            name="rejection selected index",
            minimum=0,
            maximum=len(attempts) - 1,
        )
        if type(result.selected_configuration) is not tuple:
            raise TypeError("selected configuration must be an exact tuple")
        _require_sha256(
            result.selected_configuration_sha256,
            name="rejection selected-configuration digest",
        )
        if (
            result.status != "selected"
            or result.selected_index != selected.scored.index
            or result.selected_configuration is not selected.scored.configuration
            or result.selected_configuration_sha256
            != selected.scored.configuration_sha256
        ):
            raise ValueError("rejection selected fields differ")
    for name in (
        "proposal_stream_initial_state_sha256",
        "proposal_stream_final_state_sha256",
        "decision_stream_initial_state_sha256",
        "decision_stream_final_state_sha256",
    ):
        _require_sha256(getattr(result, name), name=name)
    _require_sha256(result.result_sha256, name="rejection result digest")
    if result.result_sha256 != _digest(
        _rejection_payload(result),
        domain=b"heterodiff-mixed-support-rejection-result-v2\x00",
    ):
        raise ValueError("rejection result digest differs")
    return result


def _validate_sir_result(
    result: object, *, certificate: MixedSupportInitialTiltInitializerCertificateV2
) -> MixedSupportInitialTiltSIRResultV2:
    if type(result) is not MixedSupportInitialTiltSIRResultV2:
        raise TypeError("SIR result has the wrong exact v2 type")
    _require_text(
        result.status,
        name="SIR result status",
        maximum_length=16,
    )
    _require_sha256(
        result.certificate_sha256,
        name="SIR result certificate digest",
    )
    if (
        certificate.strategy != "fixed-budget-sir"
        or result.certificate is not certificate
        or result.certificate_sha256 != certificate.certificate_sha256
    ):
        raise ValueError("SIR result certificate differs")
    if (
        result.status != "selected"
        or type(result.particles) is not tuple
        or len(result.particles) != certificate.plan.budget
    ):
        raise ValueError("SIR result shape or status differs")
    scored = []
    weights = _immutable_array(result.normalized_weights, name="SIR normalized weights")
    if len(weights) != len(result.particles):
        raise ValueError("SIR particle and weight lengths differ")
    for index, particle in enumerate(result.particles):
        if type(particle) is not MixedSupportInitialTiltSIRParticleV2:
            raise TypeError("SIR particle has the wrong exact type")
        record = _validate_scored(particle.scored, certificate=certificate)
        if record.index != index or not _same_float(
            particle.normalized_weight, float(weights[index])
        ):
            raise ValueError("SIR particle index or weight differs")
        _require_sha256(particle.particle_sha256, name="SIR particle digest")
        if particle.particle_sha256 != _particle_sha(
            record.scored_configuration_sha256, particle.normalized_weight
        ):
            raise ValueError("SIR particle digest differs")
        scored.append(record)
    expected_weights = normalize_mixed_support_sir_exact_log_weights_v2(
        tuple(record.exact_log_weight for record in scored)
    )
    if not _same_array(weights, expected_weights):
        raise ValueError("SIR normalized weights differ")
    expected_ess = 1.0 / math.fsum(float(value * value) for value in weights)
    expected_maximum = float(np.max(weights))
    if not _same_float(result.effective_sample_size, expected_ess) or not _same_float(
        result.maximum_normalized_weight, expected_maximum
    ):
        raise ValueError("SIR diagnostics differ")
    expected_warning = (
        expected_ess < certificate.plan.ess_warning_fraction * certificate.plan.budget
    )
    if type(result.ess_warning) is not bool or result.ess_warning != expected_warning:
        raise ValueError("SIR ESS warning differs")
    word = _require_int(
        result.resampling_word, name="SIR word", minimum=0, maximum=_D - 1
    )
    uniform53 = word >> (
        MIXED_SUPPORT_INITIALIZER_V2_RAW_WORD_BITS
        - MIXED_SUPPORT_INITIALIZER_V2_SIR_UNIFORM_BITS
    )
    _require_int(
        result.resampling_uniform_53,
        name="SIR uniform53",
        minimum=0,
        maximum=(1 << MIXED_SUPPORT_INITIALIZER_V2_SIR_UNIFORM_BITS) - 1,
    )
    if result.resampling_uniform_53 != uniform53:
        raise ValueError("SIR uniform53 differs")
    selected_index = select_mixed_support_sir_index_v2(weights, word)
    selected = scored[selected_index]
    _require_int(
        result.selected_index,
        name="SIR selected index",
        minimum=0,
        maximum=len(scored) - 1,
    )
    if type(result.selected_configuration) is not tuple:
        raise TypeError("SIR selected configuration must be an exact tuple")
    _require_sha256(
        result.selected_configuration_sha256,
        name="SIR selected-configuration digest",
    )
    if (
        result.selected_index != selected_index
        or result.selected_configuration is not selected.configuration
        or result.selected_configuration_sha256 != selected.configuration_sha256
    ):
        raise ValueError("SIR selected fields differ")
    for name in (
        "proposal_stream_initial_state_sha256",
        "proposal_stream_final_state_sha256",
        "resampling_stream_initial_state_sha256",
        "resampling_stream_final_state_sha256",
    ):
        _require_sha256(getattr(result, name), name=name)
    _require_sha256(result.result_sha256, name="SIR result digest")
    if result.result_sha256 != _digest(
        _sir_payload(result), domain=b"heterodiff-mixed-support-SIR-result-v2\x00"
    ):
        raise ValueError("SIR result digest differs")
    return result


def _validate_enumeration_result(
    result: object, *, certificate: MixedSupportInitialTiltInitializerCertificateV2
) -> MixedSupportInitialTiltEnumerationResultV2:
    if type(result) is not MixedSupportInitialTiltEnumerationResultV2:
        raise TypeError("enumeration result has the wrong exact v2 type")
    _require_text(
        result.status,
        name="enumeration result status",
        maximum_length=16,
    )
    _require_sha256(
        result.certificate_sha256,
        name="enumeration result certificate digest",
    )
    if (
        certificate.strategy != "finite-atomic-enumeration"
        or result.certificate is not certificate
        or result.certificate_sha256 != certificate.certificate_sha256
        or result.status != "enumerated"
    ):
        raise ValueError("enumeration result certificate or status differs")
    if (
        type(result.atoms) is not tuple
        or len(result.atoms) != certificate.enumeration_state_count
    ):
        raise ValueError("enumeration atom count differs")
    masses = _immutable_array(result.base_masses, name="enumeration base masses")
    probabilities = _immutable_array(
        result.normalized_probabilities, name="enumeration probabilities"
    )
    if len(masses) != len(result.atoms) or len(probabilities) != len(result.atoms):
        raise ValueError("enumeration arrays have the wrong length")
    states, scored = [], []
    for index, atom in enumerate(result.atoms):
        if (
            type(atom) is not MixedSupportInitialTiltEnumerationAtomV2
            or type(atom.count_state) is not tuple
        ):
            raise TypeError("enumeration atom has the wrong exact structure")
        state = tuple(
            _require_int(
                value,
                name="count state",
                minimum=0,
                maximum=certificate.reference.total_cap,
            )
            for value in atom.count_state
        )
        if (
            len(state) != len(certificate.reference.type_ids)
            or sum(state) > certificate.reference.total_cap
        ):
            raise ValueError("enumeration count state differs")
        record = _validate_scored(atom.scored, certificate=certificate)
        expected_events = tuple(
            TransformedEvent(type_id, ())
            for type_id, count in zip(certificate.reference.type_ids, state)
            for _ in range(count)
        )
        expected_configuration = certificate.reference.canonicalize(expected_events)
        if record.configuration_sha256 != _score._configuration_sha256(
            expected_configuration
        ):
            raise ValueError(
                "enumeration scored configuration differs from its count state"
            )
        if (
            record.index != index
            or not _same_float(atom.base_mass, float(masses[index]))
            or not _same_float(atom.normalized_probability, float(probabilities[index]))
        ):
            raise ValueError("enumeration atom fields differ")
        _require_sha256(atom.atom_sha256, name="enumeration atom digest")
        if atom.atom_sha256 != _atom_sha(
            state,
            atom.base_mass,
            record.scored_configuration_sha256,
            atom.normalized_probability,
        ):
            raise ValueError("enumeration atom digest differs")
        states.append(state)
        scored.append(record)
    state_tuple = tuple(states)
    if certificate.enumeration_states_sha256 != _digest(
        {"states": state_tuple},
        domain=b"heterodiff-mixed-support-enumeration-states-v2\x00",
    ) or certificate.enumeration_base_masses_sha256 != _array_sha256(masses):
        raise ValueError("enumeration support differs from certificate")
    (
        expected_probabilities,
        expected_log_z,
    ) = normalize_mixed_support_atomic_exact_log_weights_v2(
        masses, tuple(record.exact_log_weight for record in scored)
    )
    if not _same_array(probabilities, expected_probabilities) or not _same_float(
        result.represented_log_normalizer_float64, expected_log_z
    ):
        raise ValueError("enumeration normalization differs")
    _require_sha256(result.result_sha256, name="enumeration result digest")
    if result.result_sha256 != _digest(
        _enumeration_payload(result),
        domain=b"heterodiff-mixed-support-enumeration-result-v2\x00",
    ):
        raise ValueError("enumeration result digest differs")
    return result


class MixedSupportInitialTiltInitializerKernelV2:
    """Immutable owner of one certified v2 initializer."""

    __slots__ = (
        "_provider",
        "_provider_identity",
        "_reference",
        "_reference_identity",
        "_plan",
        "_plan_identity",
        "_certificate",
        "_certificate_identity",
    )

    def __init__(
        self,
        *,
        provider: CertifiedInitialScoreProviderV1,
        reference: CappedPoissonConfigurationReference,
        plan: MixedSupportInitialTiltInitializerPlanV2,
        certificate: MixedSupportInitialTiltInitializerCertificateV2,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("v2 kernels require certification")
        object.__setattr__(self, "_provider", provider)
        object.__setattr__(self, "_provider_identity", provider)
        object.__setattr__(self, "_reference", reference)
        object.__setattr__(self, "_reference_identity", reference)
        object.__setattr__(self, "_plan", plan)
        object.__setattr__(self, "_plan_identity", plan)
        object.__setattr__(self, "_certificate", certificate)
        object.__setattr__(self, "_certificate_identity", certificate)
        self._require_snapshot()

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("v2 kernels cannot be subclassed")

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("v2 kernels are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("v2 kernels are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("v2 kernels are not pickle objects")

    @property
    def provider(self) -> CertifiedInitialScoreProviderV1:
        self._require_snapshot()
        return self._provider

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        self._require_snapshot()
        return self._reference

    @property
    def plan(self) -> MixedSupportInitialTiltInitializerPlanV2:
        self._require_snapshot()
        return self._plan

    @property
    def certificate(self) -> MixedSupportInitialTiltInitializerCertificateV2:
        self._require_snapshot()
        return self._certificate

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "mixed-support-initializer-kernel-v2",
            self.certificate.certificate_sha256,
        )

    def _require_snapshot(self) -> None:
        if (
            self._provider is not self._provider_identity
            or self._reference is not self._reference_identity
            or self._plan is not self._plan_identity
            or self._certificate is not self._certificate_identity
        ):
            raise ValueError("v2 kernel identity sentinel differs")
        _validate_plan(self._plan)
        _validate_certificate(self._certificate)
        if (
            self._plan.provider is not self._provider
            or self._certificate.provider is not self._provider
            or self._certificate.reference is not self._reference
        ):
            raise ValueError("v2 kernel ancestry differs")

    def revalidate_live_components(
        self,
    ) -> MixedSupportInitialTiltInitializerCertificateV2:
        """Explicitly revalidate provider, reference, preflight, and runtime."""

        self._require_snapshot()
        self._provider.revalidate_live_components()
        require_matching_certified_initial_score_provider_v1(
            self._provider, self._reference
        )
        _preflight_resources(
            self._reference, strategy=self._plan.strategy, budget=self._plan.budget
        )
        if self._certificate.runtime_sha256 != _runtime_sha256():
            raise ValueError("live v2 runtime differs from certification")
        expected = _make_certificate(self._provider, self._plan)
        for name in self._certificate.__annotations__:
            supplied, wanted = getattr(self._certificate, name), getattr(expected, name)
            if name in ("provider", "provider_certificate", "reference", "plan"):
                matches = supplied is wanted
            elif type(supplied) is float and type(wanted) is float:
                matches = _same_float(supplied, wanted)
            else:
                matches = type(supplied) is type(wanted) and supplied == wanted
            if not matches:
                raise ValueError("live v2 certificate field %s differs" % name)
        self._require_snapshot()
        return self._certificate

    def _evaluate(
        self, index: int, configuration: TransformedConfiguration
    ) -> MixedSupportInitialTiltScoredConfigurationV2:
        evaluation = self._provider.evaluate(
            configuration, residual_context=self._plan.residual_context
        )
        return _make_scored(index, evaluation, self._certificate)

    def _execute_rejection(self) -> MixedSupportInitialTiltRejectionResultV2:
        proposal_rng = _new_philox(self._certificate.proposal_seed)
        proposal_before = _rng_state_sha256(proposal_rng.bit_generator.state)
        configurations = tuple(
            self._reference.sample_configuration(proposal_rng)
            for _ in range(self._plan.budget)
        )
        proposal_after = _rng_state_sha256(proposal_rng.bit_generator.state)
        decision_rng = _new_philox(self._certificate.rejection_decision_seed)
        decision_before = _rng_state_sha256(decision_rng.bit_generator.state)
        words = tuple(
            int(decision_rng.bit_generator.random_raw())
            for _ in range(self._plan.budget)
        )
        decision_after = _rng_state_sha256(decision_rng.bit_generator.state)
        scored = tuple(
            self._evaluate(index, configuration)
            for index, configuration in enumerate(configurations)
        )
        attempts = tuple(
            _make_attempt(record, words[index], self._certificate)
            for index, record in enumerate(scored)
        )
        selected = next((attempt for attempt in attempts if attempt.accepted), None)
        values = {
            "certificate": self._certificate,
            "certificate_sha256": self._certificate.certificate_sha256,
            "status": "selected" if selected is not None else "exhausted",
            "attempts": attempts,
            "selected_index": None if selected is None else selected.scored.index,
            "selected_configuration": None
            if selected is None
            else selected.scored.configuration,
            "selected_configuration_sha256": None
            if selected is None
            else selected.scored.configuration_sha256,
            "proposal_stream_initial_state_sha256": proposal_before,
            "proposal_stream_final_state_sha256": proposal_after,
            "decision_stream_initial_state_sha256": decision_before,
            "decision_stream_final_state_sha256": decision_after,
            "result_sha256": _ZERO_SHA256,
        }
        provisional = object.__new__(MixedSupportInitialTiltRejectionResultV2)
        for name, value in values.items():
            object.__setattr__(provisional, name, value)
        values["result_sha256"] = _digest(
            _rejection_payload(provisional),
            domain=b"heterodiff-mixed-support-rejection-result-v2\x00",
        )
        result = MixedSupportInitialTiltRejectionResultV2(
            **values, _construction_token=_REJECTION_RESULT_TOKEN
        )
        return _validate_rejection_result(result, certificate=self._certificate)

    def _execute_sir(self) -> MixedSupportInitialTiltSIRResultV2:
        proposal_rng = _new_philox(self._certificate.proposal_seed)
        proposal_before = _rng_state_sha256(proposal_rng.bit_generator.state)
        scored = tuple(
            self._evaluate(index, self._reference.sample_configuration(proposal_rng))
            for index in range(self._plan.budget)
        )
        proposal_after = _rng_state_sha256(proposal_rng.bit_generator.state)
        weights = normalize_mixed_support_sir_exact_log_weights_v2(
            tuple(record.exact_log_weight for record in scored)
        )
        resampling_rng = _new_philox(self._certificate.sir_resampling_seed)
        resampling_before = _rng_state_sha256(resampling_rng.bit_generator.state)
        word = int(resampling_rng.bit_generator.random_raw())
        selected_index = select_mixed_support_sir_index_v2(weights, word)
        resampling_after = _rng_state_sha256(resampling_rng.bit_generator.state)
        particles = tuple(
            MixedSupportInitialTiltSIRParticleV2(
                scored=record,
                normalized_weight=float(weights[index]),
                particle_sha256=_particle_sha(
                    record.scored_configuration_sha256, float(weights[index])
                ),
                _construction_token=_PARTICLE_TOKEN,
            )
            for index, record in enumerate(scored)
        )
        selected = scored[selected_index]
        ess = 1.0 / math.fsum(float(value * value) for value in weights)
        values = {
            "certificate": self._certificate,
            "certificate_sha256": self._certificate.certificate_sha256,
            "status": "selected",
            "particles": particles,
            "normalized_weights": weights,
            "effective_sample_size": ess,
            "maximum_normalized_weight": float(np.max(weights)),
            "ess_warning": ess < self._plan.ess_warning_fraction * self._plan.budget,
            "selected_index": selected_index,
            "selected_configuration": selected.configuration,
            "selected_configuration_sha256": selected.configuration_sha256,
            "proposal_stream_initial_state_sha256": proposal_before,
            "proposal_stream_final_state_sha256": proposal_after,
            "resampling_stream_initial_state_sha256": resampling_before,
            "resampling_stream_final_state_sha256": resampling_after,
            "resampling_word": word,
            "resampling_uniform_53": word
            >> (
                MIXED_SUPPORT_INITIALIZER_V2_RAW_WORD_BITS
                - MIXED_SUPPORT_INITIALIZER_V2_SIR_UNIFORM_BITS
            ),
            "result_sha256": _ZERO_SHA256,
        }
        provisional = object.__new__(MixedSupportInitialTiltSIRResultV2)
        for name, value in values.items():
            object.__setattr__(provisional, name, value)
        values["result_sha256"] = _digest(
            _sir_payload(provisional),
            domain=b"heterodiff-mixed-support-SIR-result-v2\x00",
        )
        result = MixedSupportInitialTiltSIRResultV2(
            **values, _construction_token=_SIR_RESULT_TOKEN
        )
        return _validate_sir_result(result, certificate=self._certificate)

    def _execute_enumeration(self) -> MixedSupportInitialTiltEnumerationResultV2:
        space, _, oracle_masses = self._reference.finite_atomic_oracle()
        scored, states = [], []
        for index, state in enumerate(space.states):
            events = tuple(
                TransformedEvent(type_id, ())
                for type_id, count in zip(self._reference.type_ids, state)
                for _ in range(count)
            )
            scored.append(self._evaluate(index, self._reference.canonicalize(events)))
            states.append(tuple(int(value) for value in state))
        masses = _make_array(oracle_masses, name="oracle base masses")
        probabilities, log_z = normalize_mixed_support_atomic_exact_log_weights_v2(
            masses, tuple(record.exact_log_weight for record in scored)
        )
        atoms = tuple(
            MixedSupportInitialTiltEnumerationAtomV2(
                count_state=states[index],
                base_mass=float(masses[index]),
                scored=record,
                normalized_probability=float(probabilities[index]),
                atom_sha256=_atom_sha(
                    states[index],
                    float(masses[index]),
                    record.scored_configuration_sha256,
                    float(probabilities[index]),
                ),
                _construction_token=_ATOM_TOKEN,
            )
            for index, record in enumerate(scored)
        )
        values = {
            "certificate": self._certificate,
            "certificate_sha256": self._certificate.certificate_sha256,
            "status": "enumerated",
            "atoms": atoms,
            "base_masses": masses,
            "normalized_probabilities": probabilities,
            "represented_log_normalizer_float64": log_z,
            "result_sha256": _ZERO_SHA256,
        }
        provisional = object.__new__(MixedSupportInitialTiltEnumerationResultV2)
        for name, value in values.items():
            object.__setattr__(provisional, name, value)
        values["result_sha256"] = _digest(
            _enumeration_payload(provisional),
            domain=b"heterodiff-mixed-support-enumeration-result-v2\x00",
        )
        result = MixedSupportInitialTiltEnumerationResultV2(
            **values, _construction_token=_ENUMERATION_RESULT_TOKEN
        )
        return _validate_enumeration_result(result, certificate=self._certificate)

    def execute(self) -> MixedSupportInitialTiltInitializerResultV2:
        """Execute the precommitted bounded strategy or fail closed."""

        self.revalidate_live_components()
        if self._plan.strategy == "bounded-rejection":
            result = self._execute_rejection()
        elif self._plan.strategy == "fixed-budget-sir":
            result = self._execute_sir()
        else:
            result = self._execute_enumeration()
        self._require_snapshot()
        return self.validate_result(result)

    def validate_result(
        self, result: object
    ) -> MixedSupportInitialTiltInitializerResultV2:
        """Validate structure without full point, sampler, or RNG replay.

        This never calls ``provider.evaluate`` or public ``validate_evaluation``.
        Live ancestry, certificates, and retained point structural arithmetic
        and custody are still validated.
        """

        self._require_snapshot()
        if type(result) is MixedSupportInitialTiltRejectionResultV2:
            checked = _validate_rejection_result(result, certificate=self._certificate)
        elif type(result) is MixedSupportInitialTiltSIRResultV2:
            checked = _validate_sir_result(result, certificate=self._certificate)
        elif type(result) is MixedSupportInitialTiltEnumerationResultV2:
            checked = _validate_enumeration_result(
                result, certificate=self._certificate
            )
        else:
            raise TypeError("result has no supported exact v2 result type")
        self._require_snapshot()
        return checked


def certify_mixed_support_initial_tilt_initializer_kernel_v2(
    provider: CertifiedInitialScoreProviderV1,
    *,
    plan: MixedSupportInitialTiltInitializerPlanV2,
) -> MixedSupportInitialTiltInitializerKernelV2:
    """Certify one v2 kernel after aggregate resource preflight."""

    if type(provider) is not CertifiedInitialScoreProviderV1:
        raise TypeError("provider must be an exact CertifiedInitialScoreProviderV1")
    checked_plan = _validate_plan(plan)
    if checked_plan.provider is not provider:
        raise ValueError("plan belongs to another provider")
    reference = provider.reference
    _preflight_resources(reference, strategy=plan.strategy, budget=plan.budget)
    certificate = _make_certificate(provider, plan)
    return MixedSupportInitialTiltInitializerKernelV2(
        provider=provider,
        reference=reference,
        plan=plan,
        certificate=certificate,
        _construction_token=_OWNER_TOKEN,
    )


def require_matching_mixed_support_initial_tilt_initializer_kernel_v2(
    kernel: MixedSupportInitialTiltInitializerKernelV2,
    provider: CertifiedInitialScoreProviderV1,
) -> MixedSupportInitialTiltInitializerKernelV2:
    """Require exact kernel/provider custody and replay live certification."""

    if type(kernel) is not MixedSupportInitialTiltInitializerKernelV2:
        raise TypeError("kernel has the wrong exact v2 type")
    if type(provider) is not CertifiedInitialScoreProviderV1:
        raise TypeError("provider has the wrong exact provider type")
    if kernel.provider is not provider:
        raise ValueError("kernel belongs to another provider")
    kernel.revalidate_live_components()
    return kernel


__all__ = (
    "MAX_MIXED_SUPPORT_INITIALIZER_V2_BUDGET",
    "MIXED_SUPPORT_INITIALIZER_V2_DEFAULT_ESS_WARNING_FRACTION",
    "MIXED_SUPPORT_INITIALIZER_V2_RAW_WORD_BITS",
    "MIXED_SUPPORT_INITIALIZER_V2_SIR_UNIFORM_BITS",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_ENUMERATION_CAVEAT",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_EXECUTED_MEASURE_POLICIES",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_FORMAL_TEST_28_STATUS",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_NONCLAIM",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_REJECTION_CAVEAT",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCHEMA_VERSION",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCOPE",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SIR_CAVEAT",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_STRATEGIES",
    "MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_TARGET_POLICY",
    "MixedSupportInitialTiltEnumerationAtomV2",
    "MixedSupportInitialTiltEnumerationResultV2",
    "MixedSupportInitialTiltInitializerCertificateV2",
    "MixedSupportInitialTiltInitializerKernelV2",
    "MixedSupportInitialTiltInitializerPlanV2",
    "MixedSupportInitialTiltInitializerResultV2",
    "MixedSupportInitialTiltInitializerV2Error",
    "MixedSupportInitialTiltRejectionAttemptV2",
    "MixedSupportInitialTiltRejectionResultV2",
    "MixedSupportInitialTiltSIRParticleV2",
    "MixedSupportInitialTiltSIRResultV2",
    "MixedSupportInitialTiltScoredConfigurationV2",
    "certify_mixed_support_initial_tilt_initializer_kernel_v2",
    "make_mixed_support_initial_tilt_initializer_plan_v2",
    "normalize_mixed_support_atomic_exact_log_weights_v2",
    "normalize_mixed_support_sir_exact_log_weights_v2",
    "require_matching_mixed_support_initial_tilt_initializer_kernel_v2",
    "select_mixed_support_sir_index_v2",
    "validate_mixed_support_initial_tilt_initializer_certificate_v2",
)
