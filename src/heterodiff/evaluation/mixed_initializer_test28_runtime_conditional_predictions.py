"""Conditional finite-precision arithmetic for Test 28.

CP59 deliberately stops short of an operational proposal-law prediction.  A
fixed seed and a fixed runtime determine a point trace; replaying that trace
does not establish a random-source law.  Without a separate external law for
the complete source capsules, this module cannot identify ``mu_fp``, prove
IID proposals, or derive unconditional ``alpha64``, ``rho64``, refusal, or
finite-J SIR laws.

The two calculations here are narrower and exact on their stated inputs.

* For one supplied realized SIR cloud, exact rational score differences are
  enclosed through the existing trusted Decimal/libmpdec quota contract.
  Supplied binary64 weights are retained exactly, NumPy is imported lazily to
  reproduce the kernel's sequential binary64 CDF with its final value forced
  to one, and the exact 53-bit categorical cell masses are counted.
* For one supplied finite rejection calibration law, exact uint64 quotas are
  converted into first-acceptance and exhaustion masses under a separate
  abstract premise of independent uniform uint64 decision words.

Neither calculation samples a reference, constructs Philox, executes an
initializer owner or plan, authenticates a supplied digest, or observes
production.  The SIR builder independently reproduces the frozen kernel-v2
normalization formula with lazy NumPy and records that narrow action explicitly.
The zero-argument bundle contains predeclared arithmetic inputs only.  It is
not a pilot, calibration sample, confirmatory run, or Formal-Test-28 result.
The Decimal quota dependency is separately source-hash-bound by the DRAFT
manifest and clean-process execution is assumed; this module does not attest
the integrity of an in-memory callable or independently reimplement CP52.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import importlib
import json
import math
import platform
import sys
from typing import Mapping, Optional, Tuple, cast


CP59_TEST28_RUNTIME_CONDITIONAL_SCHEMA_VERSION = (
    "cp59-test28-runtime-conditional-arithmetic-v1"
)
CP59_TEST28_RUNTIME_CONDITIONAL_SCOPE = (
    "supplied-realized-cloud-exact-score-exp-enclosures;supplied-float64-"
    "weight-record;lazy-current-numpy-sequential-cumsum-final-one;exact-"
    "cdf-increments;exact-right-sided-53-bit-cell-counts;half-l1-and-tv-"
    "enclosures;supplied-finite-rejection-law-exact-p64-first-accept-and-"
    "exhaustion-under-abstract-independent-uniform-uint64-decision-words;"
    "fixed-seed-point-mass-"
    "obstruction;external-source-law-assumption-required;no-sampler-no-"
    "kernel-owner-plan-or-rng-execution;independent-frozen-normalization-"
    "formula-recomputation-only;no-philox-no-mu-fp-no-iid-no-independence-no-"
    "unconditional-"
    "alpha64-rho64-refusal-or-finite-j-law-no-confirmatory-no-test28-closure"
)
CP59_TEST28_FIXED_ADDRESS_POINT_MASS_OBSTRUCTION = (
    "for fixed plan inputs, seed, code, dependencies, and runtime, the trace is "
    "a deterministic point mass; deterministic replay cannot establish a "
    "nondegenerate source law, IID sequence, or independent role streams"
)
CP59_TEST28_EXTERNAL_SOURCE_ASSUMPTION_REQUIREMENT = (
    "the current one-uint64-seed deterministic surface cannot realize a two-"
    "coordinate product-uniform source; unconditional closure requires either "
    "a richer external independent-word/capsule source API, or a finite seed-"
    "pushforward law with correlated whole-request predictions and no IID or "
    "role-independence formula; a declaration alone cannot change support"
)
CP59_TEST28_CURRENT_KERNEL_SOURCE_SUPPORT_OBSTRUCTION = (
    "D=2^64;one plan seed gives joint-trace support at most D;against two "
    "product-uniform uint64 coordinates of support D^2, TV is at least "
    "1-D/D^2=1-2^-64;for one fixed seed the point-mass TV is 1-D^-2"
)
CP59_TEST28_SOURCE_TO_OUTPUT_TV_NONCONVERSE = (
    "the source-law TV lower bound furnishes no output-law TV lower bound;"
    "data processing only contracts TV and a deterministic transform may "
    "collapse source discrepancies"
)
CP59_TEST28_SIR_CDF_FORMULA = (
    "C_i=sequential-binary64-cumsum(w)_i with C_(J-1)=1 exactly"
)
CP59_TEST28_SIR_53BIT_FORMULA = (
    "r_i=(ceil(2^53*C_i)-ceil(2^53*C_(i-1)))/2^53;C_(-1)=0;" "right-sided-searchsorted"
)
CP59_TEST28_REJECTION_BATCH_FORMULA = (
    "p_i=K_i/2^64;alpha=sum_i(nu_i*p_i);"
    "P(first-attempt=t)=(1-alpha)^(t-1)*alpha;"
    "P(exhausted)=(1-alpha)^A;P(atom=i|selected)=nu_i*p_i/alpha "
    "only when alpha>0;selected law is undefined/None when alpha=0"
)
CP59_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP59_TEST28_QUOTA_DEPENDENCY_SOURCE_SHA256 = (
    "3985d23337f854e43a6ee766d4d9a0afeed0a60fd9e37855c064c88e7477dde1"
)

CP59_TEST28_MAX_SIR_PARTICLES = 512
CP59_TEST28_MAX_REJECTION_ATTEMPTS = 64
CP59_TEST28_MAX_FRACTION_BITS = 256
CP59_TEST28_MAX_DISTINCT_SIR_SCORES = 512
CP59_TEST28_MAX_PROPOSAL_COMMON_DENOMINATOR_BITS = 256
CP59_TEST28_MAX_RESULT_FRACTION_BITS = 262_144
CP59_TEST28_MAX_CANONICAL_JSON_BYTES = 16_777_216
CP59_TEST28_MAX_CANONICAL_NODES = 65_536
CP59_TEST28_MAX_CANONICAL_SCALAR_BYTES = 8_388_608
CP59_TEST28_MAX_TEXT_BYTES = 512
CP59_TEST28_UINT64_DENOMINATOR = 1 << 64
CP59_TEST28_SIR_GRID_DENOMINATOR = 1 << 53
CP59_TEST28_MIN_CATEGORICAL_PROBABILITY = 2.0**-40
CP59_TEST28_CATEGORICAL_ACCUMULATION_FACTOR = 32.0
CP59_TEST28_CATEGORICAL_INCREMENT_RTOL = 0.125

_ZERO_SHA256 = "0" * 64
_ALLOWED_FIXTURES = ("T28-M1-Q", "T28-M2-Q")
_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_HALF = Fraction(1, 2)
_PLAN_SEED_DOMAIN_SIZE = 1 << 64
_TWO_WORD_PRODUCT_SUPPORT = 1 << 128
_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        del cls, kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("the CP59 sealed-record base cannot be subclassed")

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("CP59 records are module-created")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP59 records are not pickle objects")


def _seal(cls: type, values: Mapping[str, object]) -> object:
    if set(values) != {item.name for item in fields(cls)}:
        raise TypeError("sealed CP59 record field set differs")
    result = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result


def _text(value: object, name: str, maximum: int = CP59_TEST28_MAX_TEXT_BYTES) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value) > maximum:
        raise ValueError(name + " must be bounded nonempty text")
    if len(value.encode("utf-8")) > maximum:
        raise ValueError(name + " must be bounded nonempty text")
    return value


def _fixture(value: object) -> str:
    checked = _text(value, "fixture_id", 32)
    if checked not in _ALLOWED_FIXTURES:
        raise ValueError("fixture_id is not a frozen CP59 fixture")
    return checked


def _sha256(value: object, name: str) -> str:
    checked = _text(value, name, 64)
    if len(checked) != 64 or any(c not in "0123456789abcdef" for c in checked):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return checked


def _optional_sha256(value: object, name: str) -> Optional[str]:
    if value is None:
        return None
    return _sha256(value, name)


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < minimum or value > maximum:
        raise ValueError(name + " lies outside its frozen bound")
    return value


def _fraction(value: object, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > (
        CP59_TEST28_MAX_FRACTION_BITS
    ):
        raise ValueError(name + " exceeds the exact arithmetic bit bound")
    return value


def _result_fraction(value: Fraction, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > (
        CP59_TEST28_MAX_RESULT_FRACTION_BITS
    ):
        raise ValueError(name + " exceeds the result arithmetic bit bound")
    return value


def _tuple(value: object, name: str, minimum: int, maximum: int) -> tuple:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(name + " has an invalid bounded length")
    return value


def _positive_float(value: object, name: str) -> float:
    if type(value) is not float:
        raise TypeError(name + " must be a built-in binary64 float")
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(name + " must be finite and strictly positive")
    return value


def _canonical(value: object, _depth: int = 0) -> object:
    if _depth > 32:
        raise ValueError("canonical value exceeds the nesting-depth bound")
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            if len(value) > 16_384:
                raise ValueError("canonical text exceeds the byte bound")
            if len(value.encode("utf-8")) > 16_384:
                raise ValueError("canonical text exceeds the byte bound")
        return value
    if type(value) is int:
        if value.bit_length() > CP59_TEST28_MAX_RESULT_FRACTION_BITS:
            raise ValueError("canonical integer exceeds the bit bound")
        return {
            "cp59_exact_integer_hex": ("-" if value < 0 else "+")
            + format(abs(value), "x")
        }
    if type(value) is Fraction:
        return {
            "cp59_exact_fraction_v1": {
                "denominator": _canonical(value.denominator, _depth + 1),
                "numerator": _canonical(value.numerator, _depth + 1),
            }
        }
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("canonical floats must be finite")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("canonical floats must use positive zero")
        return {"binary64_hex": value.hex()}
    if type(value) is tuple:
        if len(value) > 4_096:
            raise ValueError("canonical tuple exceeds the item bound")
        return [_canonical(item, _depth + 1) for item in value]
    if type(value) is dict:
        if len(value) > 4_096:
            raise ValueError("canonical mapping exceeds the item bound")
        if not all(type(key) is str for key in value):
            raise TypeError("canonical mapping keys must be exact text")
        return {key: _canonical(value[key], _depth + 1) for key in sorted(value)}
    if isinstance(value, _SealedRecord):
        record_type = type(value)
        if record_type not in _CP59_RECORD_TYPE_TAGS:
            raise TypeError("unsupported CP59 sealed-record concrete type")
        return {
            "cp59_record_type": _CP59_RECORD_TYPE_TAGS[record_type],
            "fields": {
                item.name: _canonical(getattr(value, item.name), _depth + 1)
                for item in fields(record_type)
            },
        }
    raise TypeError("unsupported CP59 canonical value")


def _preflight_canonical(value: object) -> None:
    stack = [(value, 0)]
    nodes = 0
    scalar_bytes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > CP59_TEST28_MAX_CANONICAL_NODES:
            raise ValueError("canonical value exceeds the node bound")
        if depth > 32:
            raise ValueError("canonical value exceeds the nesting-depth bound")
        if current is None or type(current) is bool:
            scalar_bytes += 8
        elif type(current) is str:
            if len(current) > CP59_TEST28_MAX_CANONICAL_SCALAR_BYTES:
                raise ValueError("canonical scalar payload exceeds the byte bound")
            scalar_bytes += len(current.encode("utf-8")) + 16
        elif type(current) is int:
            bits = current.bit_length()
            if bits > CP59_TEST28_MAX_RESULT_FRACTION_BITS:
                raise ValueError("canonical integer exceeds the bit bound")
            scalar_bytes += (bits + 7) // 8 + 32
        elif type(current) is Fraction:
            bits = max(current.numerator.bit_length(), current.denominator.bit_length())
            if bits > CP59_TEST28_MAX_RESULT_FRACTION_BITS:
                raise ValueError("canonical Fraction exceeds the bit bound")
            scalar_bytes += (
                current.numerator.bit_length() + current.denominator.bit_length() + 7
            ) // 8 + 64
        elif type(current) is float:
            if not math.isfinite(current):
                raise ValueError("canonical floats must be finite")
            scalar_bytes += 48
        elif type(current) is tuple:
            if len(current) > 4_096:
                raise ValueError("canonical tuple exceeds the item bound")
            stack.extend((item, depth + 1) for item in current)
        elif type(current) is dict:
            if len(current) > 4_096:
                raise ValueError("canonical mapping exceeds the item bound")
            for key, item in current.items():
                if type(key) is not str:
                    raise TypeError("canonical mapping keys must be exact text")
                if len(key) > CP59_TEST28_MAX_CANONICAL_SCALAR_BYTES:
                    raise ValueError("canonical scalar payload exceeds the byte bound")
                scalar_bytes += len(key.encode("utf-8")) + 16
                stack.append((item, depth + 1))
        elif type(current) in _CP59_RECORD_TYPE_TAGS:
            stack.extend(
                (getattr(current, item.name), depth + 1)
                for item in fields(type(current))
            )
        else:
            raise TypeError("unsupported CP59 canonical value")
        if scalar_bytes > CP59_TEST28_MAX_CANONICAL_SCALAR_BYTES:
            raise ValueError("canonical scalar payload exceeds the byte bound")


def _canonical_json_bytes(value: object) -> bytes:
    _preflight_canonical(value)
    encoded = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    if len(encoded) > CP59_TEST28_MAX_CANONICAL_JSON_BYTES:
        raise ValueError("canonical JSON exceeds the byte resource bound")
    return encoded


def cp59_canonical_json_bytes(value: object) -> bytes:
    """Return semantic JSON for one exact public CP59 record."""

    if type(value) not in _CP59_RECORD_TYPE_TAGS:
        raise TypeError("canonical public input must be an exact CP59 record")
    return _canonical_json_bytes(value)


def _digest(kind: str, values: Mapping[str, object]) -> str:
    payload = {name: value for name, value in values.items() if name != "record_sha256"}
    return hashlib.sha256(
        b"cp59-test28-runtime-conditional-arithmetic-v1\x00"
        + kind.encode("ascii")
        + b"\x00"
        + _canonical_json_bytes(payload)
    ).hexdigest()


def _ceil_fraction(value: Fraction) -> int:
    return -((-value.numerator) // value.denominator)


def _sum_fractions(values: Tuple[Fraction, ...], name: str) -> Fraction:
    result = _ZERO
    for value in values:
        result = _result_fraction(result + value, name)
    return result


def _interval_half_l1(
    lower: Tuple[Fraction, ...],
    upper: Tuple[Fraction, ...],
    vector: Tuple[Fraction, ...],
    *,
    probability_vectors: bool,
) -> Tuple[Fraction, Fraction]:
    if not (len(lower) == len(upper) == len(vector)):
        raise ValueError("discrepancy vectors differ in length")
    minimum = _ZERO
    maximum = _ZERO
    for lo, hi, value in zip(lower, upper, vector):
        if lo > hi:
            raise ValueError("probability interval is reversed")
        if value < lo:
            minimum = _result_fraction(minimum + lo - value, "half-L1 lower")
        elif value > hi:
            minimum = _result_fraction(minimum + value - hi, "half-L1 lower")
        maximum = _result_fraction(
            maximum + max(abs(value - lo), abs(value - hi)), "half-L1 upper"
        )
    result = (
        _result_fraction(minimum * _HALF, "half-L1 lower result"),
        _result_fraction(maximum * _HALF, "half-L1 upper result"),
    )
    if probability_vectors:
        return (min(_ONE, result[0]), min(_ONE, result[1]))
    return result


def _half_l1(left: Tuple[Fraction, ...], right: Tuple[Fraction, ...]) -> Fraction:
    if len(left) != len(right):
        raise ValueError("half-L1 vectors differ in length")
    total = _ZERO
    for a, b in zip(left, right):
        total = _result_fraction(total + abs(a - b), "exact half-L1 sum")
    return _result_fraction(total * _HALF, "exact half-L1 result")


def _quota_values(delta: Fraction) -> Mapping[str, object]:
    # This import is intentionally lazy.  Importing this CP59 module alone does
    # not import NumPy, the reference sampler, a kernel, or a random source.
    quota_module = importlib.import_module(
        "heterodiff.processes.arbitrary_rational_uint64_exp_quota"
    )
    certificate = quota_module.certify_arbitrary_rational_uint64_exp_quota(delta)
    validated = quota_module.validate_arbitrary_rational_uint64_exp_quota_certificate(
        certificate
    )
    if validated is not certificate:
        raise ValueError("quota certificate validation changed identity")
    return {
        "quota": certificate.quota,
        "exp_lower": Fraction(
            certificate.exp_lower_numerator, certificate.exp_lower_denominator
        ),
        "exp_upper": Fraction(
            certificate.exp_upper_numerator, certificate.exp_upper_denominator
        ),
        "exp_lower_strict": certificate.exp_lower_strict,
        "exp_upper_strict": certificate.exp_upper_strict,
        "certificate_sha256": certificate.certificate_sha256,
        "runtime_sha256": certificate.runtime_sha256,
        "decimal_contract_required": (
            certificate.decimal_correct_rounding_contract_required
        ),
        "decimal_implementation_formally_verified": (
            certificate.decimal_implementation_formally_verified
        ),
    }


def _independent_frozen_normalized_weights(
    scores: Tuple[Fraction, ...],
) -> Tuple[float, ...]:
    # Independently reproduce the frozen kernel-v2 normalization formula.  No
    # production helper, initializer owner, reference, or RNG is invoked.
    np = importlib.import_module("numpy")
    logs = np.asarray([float(value) for value in scores], dtype=np.float64)
    if np.any(~np.isfinite(logs)):
        raise ValueError("exact scores do not have finite binary64 conversions")
    maximum = float(np.max(logs))
    shifted = np.exp(logs - maximum)
    if np.any(~np.isfinite(shifted)) or np.any(shifted <= 0.0):
        raise ValueError("frozen normalization shifted weights are invalid")
    total = math.fsum(float(value) for value in shifted)
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("frozen normalization sum is invalid")
    normalized = shifted / total
    if np.any(~np.isfinite(normalized)) or np.any(normalized <= 0.0):
        raise ValueError("frozen normalization output is invalid")
    return tuple(float(value) for value in normalized)


def _numpy_cdf(
    weights: Tuple[float, ...],
) -> Tuple[Tuple[float, ...], str, str]:
    # Importing NumPy and executing cumsum are explicit builder actions, never
    # module-import actions.  The returned runtime digest is custody, not a law
    # certificate or a portable loaded-code attestation.
    np = importlib.import_module("numpy")
    array = np.asarray(weights, dtype=np.float64)
    if array.ndim != 1 or len(array) != len(weights):
        raise ValueError("NumPy changed the retained weight shape")
    if np.any(~np.isfinite(array)) or np.any(array <= 0.0):
        raise ValueError("retained weights must be finite and positive")
    total = math.fsum(float(value) for value in array)
    tolerance = 32.0 * len(array) * float(np.finfo(np.float64).eps)
    if abs(total - 1.0) > tolerance:
        raise ValueError("retained weights fail the kernel sum tolerance")
    floor = max(
        CP59_TEST28_MIN_CATEGORICAL_PROBABILITY,
        CP59_TEST28_CATEGORICAL_ACCUMULATION_FACTOR
        * len(array)
        * float(np.finfo(np.float64).eps),
    )
    if float(np.min(array)) < floor:
        raise ValueError("retained weights fail the categorical resolution floor")
    cdf = np.cumsum(array, dtype=np.float64)
    if np.any(~np.isfinite(cdf)):
        raise ValueError("binary64 CDF became nonfinite")
    cdf[-1] = 1.0
    increments = np.diff(np.concatenate((np.zeros(1, dtype=np.float64), cdf)))
    if np.any(increments <= 0.0):
        raise ValueError("binary64 CDF contains a nonpositive increment")
    relative_error = np.abs(increments - array) / array
    if np.any(relative_error > CP59_TEST28_CATEGORICAL_INCREMENT_RTOL):
        raise ValueError("binary64 CDF fails the increment-relative-error gate")
    result = tuple(float(value) for value in cdf)
    probe = np.cumsum(
        np.asarray((0.5, 0.25, 0.125, 0.125), dtype=np.float64),
        dtype=np.float64,
    )
    runtime_values = {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "float_mantissa_bits": sys.float_info.mant_dig,
        "probe_cdf_hex": tuple(float(value).hex() for value in probe),
    }
    runtime_sha256 = hashlib.sha256(
        b"cp59-test28-current-numpy-cumsum-runtime-v1\x00"
        + _canonical_json_bytes(runtime_values)
    ).hexdigest()
    return result, str(np.__version__), runtime_sha256


@dataclass(frozen=True, eq=False, init=False, slots=True)
class SourceLawBoundaryV1(_SealedRecord):
    schema_version: str
    scope: str
    fixed_address_point_mass_obstruction: str
    external_source_assumption_requirement: str
    current_kernel_source_support_obstruction: str
    fixed_seed_replay_is_point_mass: bool
    deterministic_replay_establishes_source_law: bool
    plan_seed_bits: int
    maximum_seed_pushforward_joint_trace_support: int
    comparison_raw_word_coordinate_count: int
    product_uniform_comparison_support: int
    uniform_seed_pushforward_product_uniform_tv_lower_bound: Fraction
    fixed_seed_point_mass_product_uniform_tv: Fraction
    source_to_output_tv_nonconverse: str
    source_support_obstruction_implies_output_tv_lower_bound: bool
    current_kernel_iid_product_uniform_model_permitted: bool
    richer_external_source_api_or_correlated_seed_pushforward_required: bool
    external_joint_source_declaration_required: bool
    cp45_semantic_precedent_only: bool
    cp49_assumption_gate_semantic_precedent_only: bool
    cp45_or_cp49_artifact_ancestry_claimed: bool
    mu_fp_identified: bool
    numpy_transform_law_verified: bool
    philox_word_law_verified: bool
    runtime_dependency_source_map_frozen: bool
    numpy_version_alone_sufficient: bool
    standard_normal_variable_word_consumption_accounted: bool
    standard_normal_variable_consumption_totality_verified: bool
    compiled_numpy_scipy_abi_libm_lock_required: bool
    proposal_iid_verified: bool
    role_stream_independence_verified: bool
    decision_uint64_uniformity_verified: bool
    resampling_uniform53_verified: bool
    operational_alpha64_derived: bool
    operational_rho64_derived: bool
    operational_refusal_probability_derived: bool
    unconditional_finite_j_sir_law_derived: bool
    confirmatory_evidence: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("SourceLawBoundaryV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class RealizedSIRSlotPredictionV1(_SealedRecord):
    slot_index: int
    configuration_sha256: str
    exact_log_score: Fraction
    shifted_exact_log_score: Fraction
    exp_lower: Fraction
    exp_upper: Fraction
    exp_lower_strict: bool
    exp_upper_strict: bool
    quota_certificate_sha256: str
    retained_float64_weight: float
    retained_float64_weight_exact: Fraction
    nonoperational_exact_renormalized_weight: Fraction
    cdf_float64: float
    cdf_exact: Fraction
    cdf_increment_probability: Fraction
    categorical_53bit_cell_count: int
    categorical_53bit_probability: Fraction
    ideal_probability_lower: Fraction
    ideal_probability_upper: Fraction
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("RealizedSIRSlotPredictionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class RealizedSIRCloudPredictionV1(_SealedRecord):
    schema_version: str
    scope: str
    fixture_id: str
    particle_count: int
    source_law_boundary_sha256: str
    supplied_unverified_kernel_result_sha256: Optional[str]
    supplied_kernel_result_digest_provenance_verified: bool
    supplied_scores_fixture_membership_verified: bool
    configuration_digest_provenance_verified: bool
    exact_log_scores: Tuple[Fraction, ...]
    retained_float64_weights: Tuple[float, ...]
    configuration_sha256s: Tuple[str, ...]
    slots: Tuple[RealizedSIRSlotPredictionV1, ...]
    retained_float64_weight_sum_exact: Fraction
    retained_float64_weight_sum_residual: Fraction
    nonoperational_exact_renormalization_used: bool
    nonoperational_exact_renormalized_sum: Fraction
    cdf_formula: str
    categorical_53bit_formula: str
    cdf_last_forced_to_one: bool
    cdf_increment_sum: Fraction
    categorical_53bit_cell_count_sum: int
    categorical_53bit_probability_sum: Fraction
    abstract_uniform_53bit_grid_assumed_for_formula: bool
    ideal_to_retained_float_half_l1_lower: Fraction
    ideal_to_retained_float_half_l1_upper: Fraction
    ideal_to_nonoperational_renormalized_tv_lower: Fraction
    ideal_to_nonoperational_renormalized_tv_upper: Fraction
    retained_float_to_cdf_half_l1: Fraction
    nonoperational_renormalized_to_cdf_tv: Fraction
    cdf_to_categorical_53bit_tv: Fraction
    ideal_to_cdf_tv_lower: Fraction
    ideal_to_cdf_tv_upper: Fraction
    ideal_to_categorical_53bit_tv_lower: Fraction
    ideal_to_categorical_53bit_tv_upper: Fraction
    numpy_version: str
    numpy_cumsum_runtime_sha256: str
    numpy_cumsum_executed_by_builder: bool
    numpy_transform_law_verified: bool
    independent_normalization_formula: str
    independent_normalization_formula_recomputed: bool
    supplied_weights_byte_match_independent_formula: bool
    current_kernel_normalization_helper_invoked: bool
    full_initializer_kernel_executed: bool
    rng_executed: bool
    exp_enclosure_decimal_contract_may_be_required: bool
    decimal_implementation_formally_verified: bool
    quota_dependency_source_sha256: str
    quota_runtime_sha256s: Tuple[str, ...]
    quota_dependency_independently_reimplemented: bool
    clean_process_dependency_binding_assumed: bool
    in_memory_quota_callable_integrity_attested: bool
    source_law_verified: bool
    proposal_iid_verified: bool
    resampling_uniform53_verified: bool
    unconditional_finite_j_sir_law_derived: bool
    sampled_output_provenance_verified: bool
    production_observation_authenticated: bool
    confirmatory_evidence: bool
    formal_test_28_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("RealizedSIRCloudPredictionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class ConditionalRejectionAtomPredictionV1(_SealedRecord):
    atom_index: int
    configuration_sha256: str
    proposal_probability: Fraction
    exact_log_score: Fraction
    exact_upper_bound: Fraction
    exact_delta: Fraction
    quota: int
    p64: Fraction
    joint_proposal_and_acceptance_probability: Fraction
    selected_atom_probability: Optional[Fraction]
    quota_certificate_sha256: str
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ConditionalRejectionAtomPredictionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class ConditionalRejectionAttemptMassV1(_SealedRecord):
    attempt_index: int
    all_prior_rejected_probability: Fraction
    first_accept_probability: Fraction
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ConditionalRejectionAttemptMassV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class ConditionalRejectionFiniteLawPredictionV1(_SealedRecord):
    schema_version: str
    scope: str
    fixture_id: str
    support_size: int
    attempt_cap: int
    source_law_boundary_sha256: str
    supplied_unverified_kernel_result_sha256: Optional[str]
    supplied_kernel_result_digest_provenance_verified: bool
    supplied_scores_fixture_membership_verified: bool
    configuration_digest_provenance_verified: bool
    exact_log_scores: Tuple[Fraction, ...]
    exact_upper_bound: Fraction
    proposal_probabilities: Tuple[Fraction, ...]
    configuration_sha256s: Tuple[str, ...]
    atoms: Tuple[ConditionalRejectionAtomPredictionV1, ...]
    attempt_masses: Tuple[ConditionalRejectionAttemptMassV1, ...]
    rejection_batch_formula: str
    finite_calibration_acceptance_probability: Fraction
    selected_atom_probability_sum: Optional[Fraction]
    selection_within_attempt_cap_probability: Fraction
    exhaustion_probability: Fraction
    total_probability: Fraction
    finite_declared_proposal_law_is_synthetic_calibration: bool
    finite_declared_law_identified_with_mu_fp: bool
    iid_finite_law_proposals_assumed_for_formula: bool
    abstract_independent_uniform_uint64_decision_words_assumed_for_formula: bool
    proposal_decision_independence_assumed_for_formula: bool
    quota_runtime_sha256s: Tuple[str, ...]
    quota_decimal_contract_may_be_required: bool
    decimal_implementation_formally_verified: bool
    quota_dependency_source_sha256: str
    quota_dependency_independently_reimplemented: bool
    clean_process_dependency_binding_assumed: bool
    in_memory_quota_callable_integrity_attested: bool
    operational_decision_word_law_verified: bool
    operational_proposal_law_verified: bool
    finite_calibration_iid_premise_verified: bool
    proposal_decision_independence_verified: bool
    p64_mapping_computed_for_finite_calibration_support: bool
    operational_alpha64_derived: bool
    operational_rho64_derived: bool
    operational_refusal_probability_derived: bool
    sampled_output_provenance_verified: bool
    production_observation_authenticated: bool
    confirmatory_evidence: bool
    formal_test_28_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "ConditionalRejectionFiniteLawPredictionV1 cannot be subclassed"
        )


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP59ArithmeticCalibrationBundleV1(_SealedRecord):
    schema_version: str
    source_law_boundary: SourceLawBoundaryV1
    m1_realized_sir_calibration: RealizedSIRCloudPredictionV1
    m2_realized_sir_calibration: RealizedSIRCloudPredictionV1
    m1_conditional_rejection_calibrations: Tuple[
        ConditionalRejectionFiniteLawPredictionV1, ...
    ]
    m2_conditional_rejection_calibrations: Tuple[
        ConditionalRejectionFiniteLawPredictionV1, ...
    ]
    predeclared_fixture_labeled_calibration_tables_bound: bool
    fixture_score_formula_membership_proved_by_record: bool
    inputs_are_predeclared_arithmetic_only: bool
    sampler_executed: bool
    kernel_owner_or_plan_executed: bool
    independent_normalization_formula_recomputed: bool
    kernel_normalization_helper_invoked: bool
    rng_executed: bool
    production_observed: bool
    operational_prediction: bool
    operational_predictions_blocker_closed: bool
    confirmatory_evidence: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP59ArithmeticCalibrationBundleV1 cannot be subclassed")


_ALLOW_RECORD_CLASS_DEFINITION = False
_CP59_RECORD_TYPE_TAGS = {
    SourceLawBoundaryV1: "source-law-boundary-v1",
    RealizedSIRSlotPredictionV1: "realized-sir-slot-v1",
    RealizedSIRCloudPredictionV1: "realized-sir-cloud-v1",
    ConditionalRejectionAtomPredictionV1: "conditional-rejection-atom-v1",
    ConditionalRejectionAttemptMassV1: "conditional-rejection-attempt-mass-v1",
    ConditionalRejectionFiniteLawPredictionV1: ("conditional-rejection-finite-law-v1"),
    CP59ArithmeticCalibrationBundleV1: "arithmetic-calibration-bundle-v1",
}


def cp59_source_law_boundary() -> SourceLawBoundaryV1:
    """Return the frozen point-mass obstruction and assumption boundary."""

    values = {
        "schema_version": CP59_TEST28_RUNTIME_CONDITIONAL_SCHEMA_VERSION,
        "scope": CP59_TEST28_RUNTIME_CONDITIONAL_SCOPE,
        "fixed_address_point_mass_obstruction": (
            CP59_TEST28_FIXED_ADDRESS_POINT_MASS_OBSTRUCTION
        ),
        "external_source_assumption_requirement": (
            CP59_TEST28_EXTERNAL_SOURCE_ASSUMPTION_REQUIREMENT
        ),
        "current_kernel_source_support_obstruction": (
            CP59_TEST28_CURRENT_KERNEL_SOURCE_SUPPORT_OBSTRUCTION
        ),
        "fixed_seed_replay_is_point_mass": True,
        "deterministic_replay_establishes_source_law": False,
        "plan_seed_bits": 64,
        "maximum_seed_pushforward_joint_trace_support": _PLAN_SEED_DOMAIN_SIZE,
        "comparison_raw_word_coordinate_count": 2,
        "product_uniform_comparison_support": _TWO_WORD_PRODUCT_SUPPORT,
        "uniform_seed_pushforward_product_uniform_tv_lower_bound": Fraction(
            _TWO_WORD_PRODUCT_SUPPORT - _PLAN_SEED_DOMAIN_SIZE,
            _TWO_WORD_PRODUCT_SUPPORT,
        ),
        "fixed_seed_point_mass_product_uniform_tv": Fraction(
            _TWO_WORD_PRODUCT_SUPPORT - 1, _TWO_WORD_PRODUCT_SUPPORT
        ),
        "source_to_output_tv_nonconverse": (
            CP59_TEST28_SOURCE_TO_OUTPUT_TV_NONCONVERSE
        ),
        "source_support_obstruction_implies_output_tv_lower_bound": False,
        "current_kernel_iid_product_uniform_model_permitted": False,
        "richer_external_source_api_or_correlated_seed_pushforward_required": True,
        "external_joint_source_declaration_required": True,
        "cp45_semantic_precedent_only": True,
        "cp49_assumption_gate_semantic_precedent_only": True,
        "cp45_or_cp49_artifact_ancestry_claimed": False,
        "mu_fp_identified": False,
        "numpy_transform_law_verified": False,
        "philox_word_law_verified": False,
        "runtime_dependency_source_map_frozen": False,
        "numpy_version_alone_sufficient": False,
        "standard_normal_variable_word_consumption_accounted": False,
        "standard_normal_variable_consumption_totality_verified": False,
        "compiled_numpy_scipy_abi_libm_lock_required": True,
        "proposal_iid_verified": False,
        "role_stream_independence_verified": False,
        "decision_uint64_uniformity_verified": False,
        "resampling_uniform53_verified": False,
        "operational_alpha64_derived": False,
        "operational_rho64_derived": False,
        "operational_refusal_probability_derived": False,
        "unconditional_finite_j_sir_law_derived": False,
        "confirmatory_evidence": False,
        "formal_test_28_status": CP59_TEST28_FORMAL_TEST_28_STATUS,
        "formal_test_28_closed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("source-law-boundary", values)
    return cast(SourceLawBoundaryV1, _seal(SourceLawBoundaryV1, values))


def _make_sir_slot(values: Mapping[str, object]) -> RealizedSIRSlotPredictionV1:
    payload = dict(values)
    payload["record_sha256"] = _ZERO_SHA256
    payload["record_sha256"] = _digest("realized-sir-slot", payload)
    return cast(
        RealizedSIRSlotPredictionV1, _seal(RealizedSIRSlotPredictionV1, payload)
    )


def predict_cp59_realized_sir_cloud(
    *,
    fixture_id: str,
    exact_log_scores: Tuple[Fraction, ...],
    retained_float64_weights: Tuple[float, ...],
    configuration_sha256s: Tuple[str, ...],
    supplied_unverified_kernel_result_sha256: Optional[str] = None,
) -> RealizedSIRCloudPredictionV1:
    """Predict conditional categorical arithmetic for one supplied SIR cloud."""

    fixture = _fixture(fixture_id)
    raw_scores = _tuple(
        exact_log_scores,
        "exact_log_scores",
        1,
        CP59_TEST28_MAX_SIR_PARTICLES,
    )
    scores = tuple(
        _fraction(value, "exact_log_scores[%d]" % index)
        for index, value in enumerate(raw_scores)
    )
    raw_weights = _tuple(
        retained_float64_weights,
        "retained_float64_weights",
        len(scores),
        len(scores),
    )
    independent_weights = _independent_frozen_normalized_weights(scores)
    weights = tuple(
        _positive_float(value, "retained_float64_weights[%d]" % index)
        for index, value in enumerate(raw_weights)
    )
    if tuple(value.hex() for value in weights) != tuple(
        value.hex() for value in independent_weights
    ):
        raise ValueError(
            "retained weights differ from independent frozen normalization formula"
        )
    raw_digests = _tuple(
        configuration_sha256s,
        "configuration_sha256s",
        len(scores),
        len(scores),
    )
    # Repeated configuration values in different particle slots are allowed.
    configuration_digests = tuple(
        _sha256(value, "configuration_sha256s[%d]" % index)
        for index, value in enumerate(raw_digests)
    )
    supplied_digest = _optional_sha256(
        supplied_unverified_kernel_result_sha256,
        "supplied_unverified_kernel_result_sha256",
    )
    maximum = max(scores)
    deltas = tuple(
        _result_fraction(value - maximum, "shifted score") for value in scores
    )
    distinct_deltas = tuple(dict.fromkeys(deltas))
    if len(distinct_deltas) > CP59_TEST28_MAX_DISTINCT_SIR_SCORES:
        raise ValueError("SIR cloud exceeds the distinct-score work bound")
    quota_by_delta = {delta: _quota_values(delta) for delta in distinct_deltas}
    quota_values = tuple(quota_by_delta[delta] for delta in deltas)
    exp_lower = tuple(
        _result_fraction(value["exp_lower"], "exp_lower") for value in quota_values
    )
    exp_upper = tuple(
        _result_fraction(value["exp_upper"], "exp_upper") for value in quota_values
    )
    lower_sum = _sum_fractions(exp_lower, "exponential lower sum")
    upper_sum = _sum_fractions(exp_upper, "exponential upper sum")
    if lower_sum <= 0 or upper_sum < lower_sum:
        raise ArithmeticError("exponential enclosures do not normalize")
    ideal_lower = tuple(
        _result_fraction(value / upper_sum, "ideal probability lower")
        for value in exp_lower
    )
    ideal_upper = tuple(
        _result_fraction(min(_ONE, value / lower_sum), "ideal probability upper")
        for value in exp_upper
    )

    float_exact = tuple(Fraction.from_float(value) for value in weights)
    float_sum = _sum_fractions(float_exact, "float weight exact sum")
    if float_sum <= 0:
        raise ArithmeticError("supplied float weights have nonpositive exact sum")
    exact_renormalized = tuple(
        _result_fraction(value / float_sum, "exact-renormalized float weight")
        for value in float_exact
    )
    cdf_float, numpy_version, numpy_runtime_sha = _numpy_cdf(weights)
    cdf_exact = tuple(Fraction.from_float(value) for value in cdf_float)
    previous = _ZERO
    cdf_increments_list = []
    grid_counts_list = []
    for current in cdf_exact:
        increment = current - previous
        if increment <= 0:
            raise ArithmeticError("exact CDF increment is nonpositive")
        cdf_increments_list.append(_result_fraction(increment, "CDF increment"))
        count = _ceil_fraction(CP59_TEST28_SIR_GRID_DENOMINATOR * current) - (
            _ceil_fraction(CP59_TEST28_SIR_GRID_DENOMINATOR * previous)
        )
        if count <= 0:
            raise ArithmeticError("53-bit categorical bin is empty")
        grid_counts_list.append(count)
        previous = current
    cdf_increments = tuple(cdf_increments_list)
    grid_counts = tuple(grid_counts_list)
    grid_probabilities = tuple(
        Fraction(value, CP59_TEST28_SIR_GRID_DENOMINATOR) for value in grid_counts
    )
    if _sum_fractions(cdf_increments, "CDF increment sum") != _ONE:
        raise ArithmeticError("exact CDF increments do not sum to one")
    if sum(grid_counts) != CP59_TEST28_SIR_GRID_DENOMINATOR:
        raise ArithmeticError("53-bit categorical bins do not partition the grid")
    if _sum_fractions(grid_probabilities, "53-bit probability sum") != _ONE:
        raise ArithmeticError("53-bit categorical probabilities do not sum to one")

    slots = []
    for index in range(len(scores)):
        quota = quota_values[index]
        slots.append(
            _make_sir_slot(
                {
                    "slot_index": index,
                    "configuration_sha256": configuration_digests[index],
                    "exact_log_score": scores[index],
                    "shifted_exact_log_score": deltas[index],
                    "exp_lower": exp_lower[index],
                    "exp_upper": exp_upper[index],
                    "exp_lower_strict": quota["exp_lower_strict"],
                    "exp_upper_strict": quota["exp_upper_strict"],
                    "quota_certificate_sha256": quota["certificate_sha256"],
                    "retained_float64_weight": weights[index],
                    "retained_float64_weight_exact": float_exact[index],
                    "nonoperational_exact_renormalized_weight": (
                        exact_renormalized[index]
                    ),
                    "cdf_float64": cdf_float[index],
                    "cdf_exact": cdf_exact[index],
                    "cdf_increment_probability": cdf_increments[index],
                    "categorical_53bit_cell_count": grid_counts[index],
                    "categorical_53bit_probability": grid_probabilities[index],
                    "ideal_probability_lower": ideal_lower[index],
                    "ideal_probability_upper": ideal_upper[index],
                }
            )
        )
    ideal_float = _interval_half_l1(
        ideal_lower, ideal_upper, float_exact, probability_vectors=False
    )
    ideal_renormalized = _interval_half_l1(
        ideal_lower, ideal_upper, exact_renormalized, probability_vectors=True
    )
    ideal_cdf = _interval_half_l1(
        ideal_lower, ideal_upper, cdf_increments, probability_vectors=True
    )
    ideal_grid = _interval_half_l1(
        ideal_lower, ideal_upper, grid_probabilities, probability_vectors=True
    )
    boundary = cp59_source_law_boundary()
    values = {
        "schema_version": CP59_TEST28_RUNTIME_CONDITIONAL_SCHEMA_VERSION,
        "scope": CP59_TEST28_RUNTIME_CONDITIONAL_SCOPE,
        "fixture_id": fixture,
        "particle_count": len(scores),
        "source_law_boundary_sha256": boundary.record_sha256,
        "supplied_unverified_kernel_result_sha256": supplied_digest,
        "supplied_kernel_result_digest_provenance_verified": False,
        "supplied_scores_fixture_membership_verified": False,
        "configuration_digest_provenance_verified": False,
        "exact_log_scores": scores,
        "retained_float64_weights": weights,
        "configuration_sha256s": configuration_digests,
        "slots": tuple(slots),
        "retained_float64_weight_sum_exact": float_sum,
        "retained_float64_weight_sum_residual": _result_fraction(
            float_sum - _ONE, "float weight sum residual"
        ),
        "nonoperational_exact_renormalization_used": True,
        "nonoperational_exact_renormalized_sum": _sum_fractions(
            exact_renormalized, "exact-renormalized probability sum"
        ),
        "cdf_formula": CP59_TEST28_SIR_CDF_FORMULA,
        "categorical_53bit_formula": CP59_TEST28_SIR_53BIT_FORMULA,
        "cdf_last_forced_to_one": True,
        "cdf_increment_sum": _sum_fractions(cdf_increments, "CDF increment sum"),
        "categorical_53bit_cell_count_sum": sum(grid_counts),
        "categorical_53bit_probability_sum": _sum_fractions(
            grid_probabilities, "53-bit probability sum"
        ),
        "abstract_uniform_53bit_grid_assumed_for_formula": True,
        "ideal_to_retained_float_half_l1_lower": ideal_float[0],
        "ideal_to_retained_float_half_l1_upper": ideal_float[1],
        "ideal_to_nonoperational_renormalized_tv_lower": ideal_renormalized[0],
        "ideal_to_nonoperational_renormalized_tv_upper": ideal_renormalized[1],
        "retained_float_to_cdf_half_l1": _half_l1(float_exact, cdf_increments),
        "nonoperational_renormalized_to_cdf_tv": _half_l1(
            exact_renormalized, cdf_increments
        ),
        "cdf_to_categorical_53bit_tv": _half_l1(cdf_increments, grid_probabilities),
        "ideal_to_cdf_tv_lower": ideal_cdf[0],
        "ideal_to_cdf_tv_upper": ideal_cdf[1],
        "ideal_to_categorical_53bit_tv_lower": ideal_grid[0],
        "ideal_to_categorical_53bit_tv_upper": ideal_grid[1],
        "numpy_version": numpy_version,
        "numpy_cumsum_runtime_sha256": numpy_runtime_sha,
        "numpy_cumsum_executed_by_builder": True,
        "numpy_transform_law_verified": False,
        "independent_normalization_formula": (
            "logs=np.asarray([float(q_i)],dtype=np.float64);"
            "m=float(np.max(logs));shifted=np.exp(logs-m);"
            "S=math.fsum(float(shifted_i));weights=shifted/S"
        ),
        "independent_normalization_formula_recomputed": True,
        "supplied_weights_byte_match_independent_formula": True,
        "current_kernel_normalization_helper_invoked": False,
        "full_initializer_kernel_executed": False,
        "rng_executed": False,
        "exp_enclosure_decimal_contract_may_be_required": any(
            bool(value["decimal_contract_required"]) for value in quota_values
        ),
        "decimal_implementation_formally_verified": all(
            bool(value["decimal_implementation_formally_verified"])
            for value in quota_values
        ),
        "quota_dependency_source_sha256": CP59_TEST28_QUOTA_DEPENDENCY_SOURCE_SHA256,
        "quota_runtime_sha256s": tuple(
            _sha256(value["runtime_sha256"], "quota runtime SHA-256")
            for value in quota_values
        ),
        "quota_dependency_independently_reimplemented": False,
        "clean_process_dependency_binding_assumed": True,
        "in_memory_quota_callable_integrity_attested": False,
        "source_law_verified": False,
        "proposal_iid_verified": False,
        "resampling_uniform53_verified": False,
        "unconditional_finite_j_sir_law_derived": False,
        "sampled_output_provenance_verified": False,
        "production_observation_authenticated": False,
        "confirmatory_evidence": False,
        "formal_test_28_closed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("realized-sir-cloud", values)
    return cast(
        RealizedSIRCloudPredictionV1, _seal(RealizedSIRCloudPredictionV1, values)
    )


def _make_rejection_atom(
    values: Mapping[str, object],
) -> ConditionalRejectionAtomPredictionV1:
    payload = dict(values)
    payload["record_sha256"] = _ZERO_SHA256
    payload["record_sha256"] = _digest("conditional-rejection-atom", payload)
    return cast(
        ConditionalRejectionAtomPredictionV1,
        _seal(ConditionalRejectionAtomPredictionV1, payload),
    )


def _make_rejection_attempt_mass(
    values: Mapping[str, object],
) -> ConditionalRejectionAttemptMassV1:
    payload = dict(values)
    payload["record_sha256"] = _ZERO_SHA256
    payload["record_sha256"] = _digest("conditional-rejection-attempt-mass", payload)
    return cast(
        ConditionalRejectionAttemptMassV1,
        _seal(ConditionalRejectionAttemptMassV1, payload),
    )


def predict_cp59_conditional_rejection_finite_law(
    *,
    fixture_id: str,
    exact_log_scores: Tuple[Fraction, ...],
    exact_upper_bound: Fraction,
    proposal_probabilities: Tuple[Fraction, ...],
    attempt_cap: int,
    configuration_sha256s: Tuple[str, ...],
    supplied_unverified_kernel_result_sha256: Optional[str] = None,
) -> ConditionalRejectionFiniteLawPredictionV1:
    """Return exact finite-calibration-law rejection predictions."""

    fixture = _fixture(fixture_id)
    raw_scores = _tuple(
        exact_log_scores,
        "exact_log_scores",
        1,
        CP59_TEST28_MAX_REJECTION_ATTEMPTS,
    )
    scores = tuple(
        _fraction(value, "exact_log_scores[%d]" % index)
        for index, value in enumerate(raw_scores)
    )
    upper = _fraction(exact_upper_bound, "exact_upper_bound")
    if any(score > upper for score in scores):
        raise ValueError("a supplied score exceeds the exact upper bound")
    raw_probabilities = _tuple(
        proposal_probabilities,
        "proposal_probabilities",
        len(scores),
        len(scores),
    )
    probabilities = tuple(
        _fraction(value, "proposal_probabilities[%d]" % index)
        for index, value in enumerate(raw_probabilities)
    )
    if any(value <= 0 for value in probabilities):
        raise ValueError("proposal probabilities must be strictly positive")
    if any(
        max(value.numerator.bit_length(), value.denominator.bit_length())
        > CP59_TEST28_MAX_PROPOSAL_COMMON_DENOMINATOR_BITS
        for value in probabilities
    ):
        raise ValueError("proposal probability exceeds the dedicated bit bound")
    common_denominator = 1
    for probability in probabilities:
        common_denominator = math.lcm(common_denominator, probability.denominator)
        if common_denominator.bit_length() > (
            CP59_TEST28_MAX_PROPOSAL_COMMON_DENOMINATOR_BITS
        ):
            raise ValueError("proposal law common denominator exceeds its bit bound")
    if _sum_fractions(probabilities, "proposal probability sum") != _ONE:
        raise ValueError("proposal probabilities must sum exactly to one")
    cap = _integer(
        attempt_cap,
        "attempt_cap",
        1,
        CP59_TEST28_MAX_REJECTION_ATTEMPTS,
    )
    raw_digests = _tuple(
        configuration_sha256s,
        "configuration_sha256s",
        len(scores),
        len(scores),
    )
    configuration_digests = tuple(
        _sha256(value, "configuration_sha256s[%d]" % index)
        for index, value in enumerate(raw_digests)
    )
    supplied_digest = _optional_sha256(
        supplied_unverified_kernel_result_sha256,
        "supplied_unverified_kernel_result_sha256",
    )
    atom_components = []
    quota_rows = []
    for index, (score, probability, configuration_digest) in enumerate(
        zip(scores, probabilities, configuration_digests)
    ):
        delta = _result_fraction(score - upper, "rejection exact delta")
        quota = _quota_values(delta)
        integer_quota = _integer(
            quota["quota"],
            "quota",
            0,
            CP59_TEST28_UINT64_DENOMINATOR,
        )
        p64 = _result_fraction(
            Fraction(integer_quota, CP59_TEST28_UINT64_DENOMINATOR), "p64"
        )
        joint = _result_fraction(
            probability * p64, "joint proposal-and-acceptance probability"
        )
        quota_rows.append((delta, integer_quota, p64, joint, quota))
        atom_components.append(joint)
    alpha = _sum_fractions(
        tuple(atom_components), "finite calibration acceptance probability"
    )
    reject_probability = _result_fraction(
        _ONE - alpha, "finite calibration rejection probability"
    )
    atoms = []
    for index, (score, probability, configuration_digest, row) in enumerate(
        zip(scores, probabilities, configuration_digests, quota_rows)
    ):
        delta, integer_quota, p64, joint, quota = row
        atoms.append(
            _make_rejection_atom(
                {
                    "atom_index": index,
                    "configuration_sha256": configuration_digest,
                    "proposal_probability": probability,
                    "exact_log_score": score,
                    "exact_upper_bound": upper,
                    "exact_delta": delta,
                    "quota": integer_quota,
                    "p64": p64,
                    "joint_proposal_and_acceptance_probability": joint,
                    "selected_atom_probability": (
                        None
                        if alpha == 0
                        else _result_fraction(
                            joint / alpha, "selected atom probability"
                        )
                    ),
                    "quota_certificate_sha256": quota["certificate_sha256"],
                }
            )
        )
    all_prior_rejected = _ONE
    attempt_masses = []
    for attempt_index in range(1, cap + 1):
        first = _result_fraction(all_prior_rejected * alpha, "first-accept probability")
        attempt_masses.append(
            _make_rejection_attempt_mass(
                {
                    "attempt_index": attempt_index,
                    "all_prior_rejected_probability": all_prior_rejected,
                    "first_accept_probability": first,
                }
            )
        )
        all_prior_rejected = _result_fraction(
            all_prior_rejected * reject_probability,
            "all-prior-rejected probability",
        )
    exhaustion = all_prior_rejected
    selection_within_cap = _sum_fractions(
        tuple(attempt.first_accept_probability for attempt in attempt_masses),
        "selection-within-cap probability",
    )
    total_probability = _result_fraction(
        selection_within_cap + exhaustion, "total probability"
    )
    if total_probability != _ONE:
        raise ArithmeticError("finite-law attempt masses do not sum to one")
    selected_sum = (
        None
        if alpha == 0
        else _sum_fractions(
            tuple(
                atom.selected_atom_probability
                for atom in atoms
                if atom.selected_atom_probability is not None
            ),
            "selected atom probability sum",
        )
    )
    if selected_sum is not None and selected_sum != _ONE:
        raise ArithmeticError("selected atom probabilities do not sum to one")
    boundary = cp59_source_law_boundary()
    values = {
        "schema_version": CP59_TEST28_RUNTIME_CONDITIONAL_SCHEMA_VERSION,
        "scope": CP59_TEST28_RUNTIME_CONDITIONAL_SCOPE,
        "fixture_id": fixture,
        "support_size": len(scores),
        "attempt_cap": cap,
        "source_law_boundary_sha256": boundary.record_sha256,
        "supplied_unverified_kernel_result_sha256": supplied_digest,
        "supplied_kernel_result_digest_provenance_verified": False,
        "supplied_scores_fixture_membership_verified": False,
        "configuration_digest_provenance_verified": False,
        "exact_log_scores": scores,
        "exact_upper_bound": upper,
        "proposal_probabilities": probabilities,
        "configuration_sha256s": configuration_digests,
        "atoms": tuple(atoms),
        "attempt_masses": tuple(attempt_masses),
        "rejection_batch_formula": CP59_TEST28_REJECTION_BATCH_FORMULA,
        "finite_calibration_acceptance_probability": alpha,
        "selected_atom_probability_sum": selected_sum,
        "selection_within_attempt_cap_probability": selection_within_cap,
        "exhaustion_probability": exhaustion,
        "total_probability": total_probability,
        "finite_declared_proposal_law_is_synthetic_calibration": True,
        "finite_declared_law_identified_with_mu_fp": False,
        "iid_finite_law_proposals_assumed_for_formula": True,
        "abstract_independent_uniform_uint64_decision_words_assumed_for_formula": True,
        "proposal_decision_independence_assumed_for_formula": True,
        "quota_runtime_sha256s": tuple(
            _sha256(row[4]["runtime_sha256"], "quota runtime SHA-256")
            for row in quota_rows
        ),
        "quota_decimal_contract_may_be_required": any(
            bool(row[4]["decimal_contract_required"]) for row in quota_rows
        ),
        "decimal_implementation_formally_verified": all(
            bool(row[4]["decimal_implementation_formally_verified"])
            for row in quota_rows
        ),
        "quota_dependency_source_sha256": CP59_TEST28_QUOTA_DEPENDENCY_SOURCE_SHA256,
        "quota_dependency_independently_reimplemented": False,
        "clean_process_dependency_binding_assumed": True,
        "in_memory_quota_callable_integrity_attested": False,
        "operational_decision_word_law_verified": False,
        "operational_proposal_law_verified": False,
        "finite_calibration_iid_premise_verified": False,
        "proposal_decision_independence_verified": False,
        "p64_mapping_computed_for_finite_calibration_support": True,
        "operational_alpha64_derived": False,
        "operational_rho64_derived": False,
        "operational_refusal_probability_derived": False,
        "sampled_output_provenance_verified": False,
        "production_observation_authenticated": False,
        "confirmatory_evidence": False,
        "formal_test_28_closed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("conditional-rejection-finite-law", values)
    return cast(
        ConditionalRejectionFiniteLawPredictionV1,
        _seal(ConditionalRejectionFiniteLawPredictionV1, values),
    )


def _same_record(left: object, right: object) -> bool:
    return type(left) is type(right) and cp59_canonical_json_bytes(
        left
    ) == cp59_canonical_json_bytes(right)


def _validate_child_record_digest(
    value: object, expected_type: type, kind: str
) -> None:
    if type(value) is not expected_type:
        raise TypeError("nested CP59 record has the wrong exact type")
    actual = _sha256(getattr(value, "record_sha256"), "nested record SHA-256")
    payload = {item.name: getattr(value, item.name) for item in fields(expected_type)}
    expected = _digest(kind, payload)
    if actual != expected:
        raise ValueError("nested CP59 record digest differs")


def validate_cp59_source_law_boundary(
    value: object,
) -> SourceLawBoundaryV1:
    """Replay the frozen source-law boundary."""

    if type(value) is not SourceLawBoundaryV1:
        raise TypeError("source-law boundary has the wrong exact type")
    expected = cp59_source_law_boundary()
    if not _same_record(value, expected):
        raise ValueError("source-law boundary differs from frozen replay")
    return value


def validate_cp59_realized_sir_cloud_prediction(
    value: object,
) -> RealizedSIRCloudPredictionV1:
    """Recompute a conditional realized-cloud record under this runtime."""

    if type(value) is not RealizedSIRCloudPredictionV1:
        raise TypeError("realized SIR prediction has the wrong exact type")
    if type(value.exact_log_scores) is not tuple:
        raise TypeError("realized SIR exact scores must be an exact tuple")
    if type(value.slots) is not tuple or len(value.slots) != len(
        value.exact_log_scores
    ):
        raise TypeError("realized SIR slots have the wrong exact structure")
    for slot in value.slots:
        _validate_child_record_digest(
            slot, RealizedSIRSlotPredictionV1, "realized-sir-slot"
        )
    expected = predict_cp59_realized_sir_cloud(
        fixture_id=value.fixture_id,
        exact_log_scores=value.exact_log_scores,
        retained_float64_weights=value.retained_float64_weights,
        configuration_sha256s=value.configuration_sha256s,
        supplied_unverified_kernel_result_sha256=(
            value.supplied_unverified_kernel_result_sha256
        ),
    )
    if not _same_record(value, expected):
        raise ValueError("realized SIR prediction differs from exact replay")
    return value


def validate_cp59_conditional_rejection_finite_law_prediction(
    value: object,
) -> ConditionalRejectionFiniteLawPredictionV1:
    """Recompute one finite-calibration-law rejection record."""

    if type(value) is not ConditionalRejectionFiniteLawPredictionV1:
        raise TypeError("conditional finite-law prediction has the wrong exact type")
    if type(value.exact_log_scores) is not tuple:
        raise TypeError("conditional finite-law scores must be an exact tuple")
    if type(value.attempt_cap) is not int:
        raise TypeError("conditional finite-law attempt cap must be an exact integer")
    if type(value.atoms) is not tuple or len(value.atoms) != len(
        value.exact_log_scores
    ):
        raise TypeError("conditional finite-law atoms have the wrong exact structure")
    if type(value.attempt_masses) is not tuple or len(value.attempt_masses) != (
        value.attempt_cap
    ):
        raise TypeError(
            "conditional finite-law attempt masses have the wrong exact structure"
        )
    for atom in value.atoms:
        _validate_child_record_digest(
            atom, ConditionalRejectionAtomPredictionV1, "conditional-rejection-atom"
        )
    for attempt in value.attempt_masses:
        _validate_child_record_digest(
            attempt,
            ConditionalRejectionAttemptMassV1,
            "conditional-rejection-attempt-mass",
        )
    expected = predict_cp59_conditional_rejection_finite_law(
        fixture_id=value.fixture_id,
        exact_log_scores=value.exact_log_scores,
        exact_upper_bound=value.exact_upper_bound,
        proposal_probabilities=value.proposal_probabilities,
        attempt_cap=value.attempt_cap,
        configuration_sha256s=value.configuration_sha256s,
        supplied_unverified_kernel_result_sha256=(
            value.supplied_unverified_kernel_result_sha256
        ),
    )
    if not _same_record(value, expected):
        raise ValueError("conditional finite-law prediction differs from exact replay")
    return value


def _m1_calibration_weights() -> Tuple[float, ...]:
    """Frozen current-helper outputs for the predeclared M1 score table."""

    return tuple(
        float.fromhex(value)
        for value in (
            "0x1.7372503ccd535p-3",
            "0x1.7372503ccd535p-3",
            "0x1.7372503ccd535p-3",
            "0x1.2148691a76a09p-3",
            "0x1.2148691a76a09p-3",
            "0x1.114b8af04dd08p-4",
            "0x1.a749a79f9611dp-4",
            "0x1.b368f32e34eb0p-9",
        )
    )


def _m2_calibration_weights() -> Tuple[float, ...]:
    """Frozen current-helper outputs for the predeclared M2 score table."""

    return tuple(
        float.fromhex(value)
        for value in (
            "0x1.378b8e8baf14cp-3",
            "0x1.378b8e8baf14cp-3",
            "0x1.e54361556ca13p-4",
            "0x1.378b8e8baf14cp-3",
            "0x1.d17597e7d8d18p-4",
            "0x1.e54361556ca13p-4",
            "0x1.ac3e473b79cd0p-4",
            "0x1.6a8006ebb9a2ap-4",
        )
    )


def cp59_arithmetic_calibration_bundle() -> CP59ArithmeticCalibrationBundleV1:
    """Return predeclared zero-draw arithmetic records for CP59 tests/docs."""

    m1_sir_scores = (
        Fraction(0),
        Fraction(0),
        Fraction(0),
        Fraction(-1, 4),
        Fraction(-1, 4),
        Fraction(-1),
        Fraction(-9, 16),
        Fraction(-4),
    )
    m2_sir_scores = (
        Fraction(0),
        Fraction(0),
        Fraction(-1, 4),
        Fraction(0),
        Fraction(-7, 24),
        Fraction(-1, 4),
        Fraction(-3, 8),
        Fraction(-13, 24),
    )
    m1_sir_digests = tuple(
        hashlib.sha256(("cp59-m1-sir-slot-%d" % index).encode("ascii")).hexdigest()
        for index in range(8)
    )
    m2_sir_digests = tuple(
        hashlib.sha256(("cp59-m2-sir-slot-%d" % index).encode("ascii")).hexdigest()
        for index in range(8)
    )
    m1_sir = predict_cp59_realized_sir_cloud(
        fixture_id="T28-M1-Q",
        exact_log_scores=m1_sir_scores,
        retained_float64_weights=_m1_calibration_weights(),
        configuration_sha256s=m1_sir_digests,
    )
    m2_sir = predict_cp59_realized_sir_cloud(
        fixture_id="T28-M2-Q",
        exact_log_scores=m2_sir_scores,
        retained_float64_weights=_m2_calibration_weights(),
        configuration_sha256s=m2_sir_digests,
    )
    m1_rejection_scores = (
        Fraction(0),
        Fraction(0),
        Fraction(-1, 4),
        Fraction(-1),
    )
    m2_rejection_scores = (
        Fraction(0),
        Fraction(-1, 4),
        Fraction(-7, 24),
        Fraction(-3, 4),
        Fraction(-19, 24),
        Fraction(-1, 4),
    )
    m1_rejection_digests = tuple(
        hashlib.sha256(
            ("cp59-m1-rejection-atom-%d" % index).encode("ascii")
        ).hexdigest()
        for index in range(len(m1_rejection_scores))
    )
    m2_rejection_digests = tuple(
        hashlib.sha256(
            ("cp59-m2-rejection-atom-%d" % index).encode("ascii")
        ).hexdigest()
        for index in range(len(m2_rejection_scores))
    )
    attempt_caps = (1, 4, 16, 64)
    m1_rejections = tuple(
        predict_cp59_conditional_rejection_finite_law(
            fixture_id="T28-M1-Q",
            exact_log_scores=m1_rejection_scores,
            exact_upper_bound=Fraction(0, 1),
            proposal_probabilities=(Fraction(1, 4),) * 4,
            attempt_cap=attempt_cap,
            configuration_sha256s=m1_rejection_digests,
        )
        for attempt_cap in attempt_caps
    )
    m2_rejections = tuple(
        predict_cp59_conditional_rejection_finite_law(
            fixture_id="T28-M2-Q",
            exact_log_scores=m2_rejection_scores,
            exact_upper_bound=Fraction(0, 1),
            proposal_probabilities=(Fraction(1, 6),) * 6,
            attempt_cap=attempt_cap,
            configuration_sha256s=m2_rejection_digests,
        )
        for attempt_cap in attempt_caps
    )
    boundary = cp59_source_law_boundary()
    values = {
        "schema_version": CP59_TEST28_RUNTIME_CONDITIONAL_SCHEMA_VERSION,
        "source_law_boundary": boundary,
        "m1_realized_sir_calibration": m1_sir,
        "m2_realized_sir_calibration": m2_sir,
        "m1_conditional_rejection_calibrations": m1_rejections,
        "m2_conditional_rejection_calibrations": m2_rejections,
        "predeclared_fixture_labeled_calibration_tables_bound": True,
        "fixture_score_formula_membership_proved_by_record": False,
        "inputs_are_predeclared_arithmetic_only": True,
        "sampler_executed": False,
        "kernel_owner_or_plan_executed": False,
        "independent_normalization_formula_recomputed": True,
        "kernel_normalization_helper_invoked": False,
        "rng_executed": False,
        "production_observed": False,
        "operational_prediction": False,
        "operational_predictions_blocker_closed": False,
        "confirmatory_evidence": False,
        "formal_test_28_status": CP59_TEST28_FORMAL_TEST_28_STATUS,
        "formal_test_28_closed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest("arithmetic-calibration-bundle", values)
    return cast(
        CP59ArithmeticCalibrationBundleV1,
        _seal(CP59ArithmeticCalibrationBundleV1, values),
    )


def validate_cp59_arithmetic_calibration_bundle(
    value: object,
) -> CP59ArithmeticCalibrationBundleV1:
    """Replay the zero-argument CP59 arithmetic calibration bundle."""

    if type(value) is not CP59ArithmeticCalibrationBundleV1:
        raise TypeError("CP59 arithmetic bundle has the wrong exact type")
    validate_cp59_source_law_boundary(value.source_law_boundary)
    validate_cp59_realized_sir_cloud_prediction(value.m1_realized_sir_calibration)
    validate_cp59_realized_sir_cloud_prediction(value.m2_realized_sir_calibration)
    for name in (
        "m1_conditional_rejection_calibrations",
        "m2_conditional_rejection_calibrations",
    ):
        children = getattr(value, name)
        if type(children) is not tuple or len(children) != 4:
            raise TypeError("bundle rejection grid has the wrong exact structure")
        for child in children:
            validate_cp59_conditional_rejection_finite_law_prediction(child)
    expected = cp59_arithmetic_calibration_bundle()
    if not _same_record(value, expected):
        raise ValueError("CP59 arithmetic bundle differs from frozen replay")
    return value


__all__ = (
    "CP59ArithmeticCalibrationBundleV1",
    "CP59_TEST28_CATEGORICAL_ACCUMULATION_FACTOR",
    "CP59_TEST28_CATEGORICAL_INCREMENT_RTOL",
    "CP59_TEST28_CURRENT_KERNEL_SOURCE_SUPPORT_OBSTRUCTION",
    "CP59_TEST28_EXTERNAL_SOURCE_ASSUMPTION_REQUIREMENT",
    "CP59_TEST28_FIXED_ADDRESS_POINT_MASS_OBSTRUCTION",
    "CP59_TEST28_FORMAL_TEST_28_STATUS",
    "CP59_TEST28_MAX_CANONICAL_JSON_BYTES",
    "CP59_TEST28_MAX_CANONICAL_NODES",
    "CP59_TEST28_MAX_CANONICAL_SCALAR_BYTES",
    "CP59_TEST28_MAX_DISTINCT_SIR_SCORES",
    "CP59_TEST28_MAX_FRACTION_BITS",
    "CP59_TEST28_MAX_PROPOSAL_COMMON_DENOMINATOR_BITS",
    "CP59_TEST28_MAX_REJECTION_ATTEMPTS",
    "CP59_TEST28_MAX_RESULT_FRACTION_BITS",
    "CP59_TEST28_MAX_SIR_PARTICLES",
    "CP59_TEST28_MIN_CATEGORICAL_PROBABILITY",
    "CP59_TEST28_QUOTA_DEPENDENCY_SOURCE_SHA256",
    "CP59_TEST28_REJECTION_BATCH_FORMULA",
    "CP59_TEST28_RUNTIME_CONDITIONAL_SCHEMA_VERSION",
    "CP59_TEST28_RUNTIME_CONDITIONAL_SCOPE",
    "CP59_TEST28_SIR_53BIT_FORMULA",
    "CP59_TEST28_SIR_CDF_FORMULA",
    "CP59_TEST28_SIR_GRID_DENOMINATOR",
    "CP59_TEST28_SOURCE_TO_OUTPUT_TV_NONCONVERSE",
    "CP59_TEST28_UINT64_DENOMINATOR",
    "ConditionalRejectionAtomPredictionV1",
    "ConditionalRejectionAttemptMassV1",
    "ConditionalRejectionFiniteLawPredictionV1",
    "RealizedSIRCloudPredictionV1",
    "RealizedSIRSlotPredictionV1",
    "SourceLawBoundaryV1",
    "cp59_arithmetic_calibration_bundle",
    "cp59_canonical_json_bytes",
    "cp59_source_law_boundary",
    "predict_cp59_conditional_rejection_finite_law",
    "predict_cp59_realized_sir_cloud",
    "validate_cp59_arithmetic_calibration_bundle",
    "validate_cp59_conditional_rejection_finite_law_prediction",
    "validate_cp59_realized_sir_cloud_prediction",
    "validate_cp59_source_law_boundary",
)
