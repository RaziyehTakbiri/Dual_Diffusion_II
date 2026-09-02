"""Exact stress and refusal oracles for the Test-28 draft.

This development artifact has two deliberately separate records.
``T28-AESS`` is an exact-rational, finite all-atomic multiplicative-factor
law together with one predeclared eight-particle diagnostic cloud.  The cloud
has low effective sample size and freezes the expected *report-only* warning
behavior: the particle budget and strategy do not change, and the warning
causes no extra draw, fallback, or cloud reuse.

``T28-INVALID`` is a deterministic table of malformed-input cases.  Each case
binds an exact refusal code, exception type and message, validation boundary,
and RNG-custody expectation.  The observation verifier compares externally
supplied sentinel byte-state digests; those sentinels are not kernel-owned RNG
states.  The zero factory-call expectation is the pre-RNG boundary.
Ordinary construction is stdlib-only.  Explicit verification of the one
production exception type lazily imports that exact class for an identity
check.

The AESS factors are not exponentials of an exact rational score.  Neither
record integrates a score-provider facade or initializer kernel, identifies
an operational source law, executes a categorical draw, authorizes Formal
Test 28, or establishes a manuscript result.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
import hashlib
import json
import math
from typing import Mapping, Tuple


CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION = (
    "cp57-test28-atomic-low-ess-and-deterministic-refusal-v1"
)
CP57_TEST28_AESS_FIXTURE_ID = "T28-AESS"
CP57_TEST28_INVALID_FIXTURE_ID = "T28-INVALID"
CP57_TEST28_AESS_FORMULA_ID = "finite-atomic-rational-factor-low-ess-v1"
CP57_TEST28_INVALID_TABLE_ID = "deterministic-preexecution-refusal-table-v1"
CP57_TEST28_STRESS_REFUSAL_SCOPE = (
    "t28-aess-exact-rational-finite-all-atomic-multiplicative-factor-target;"
    "primitive-factorial-base-reconstruction;one-predeclared-j8-diagnostic-"
    "cloud;exact-ess-and-report-only-warning-contract;t28-invalid-complete-"
    "frozen-malformed-input-case-table;exact-refusal-code-exception-message-"
    "and-boundary;owned-rng-roles-not-constructed-and-zero-factory-call-"
    "expectation;external-sentinel-byte-state-digest-comparison;stdlib-only-"
    "module-import-and-oracle-table-construction;lazy-production-exception-"
    "identity-import-only-on-explicit-observation-verification;not-exp-"
    "of-exact-q-not-score-facade-not-kernel-integration-not-runtime-source-law-"
    "not-categorical-draw-not-confirmatory-not-formal-test28-not-manuscript"
)
CP57_TEST28_STRESS_REFUSAL_NONCLAIMS = (
    "the T28-AESS rational factors are not exponentials of an exact rational score",
    "the T28-AESS diagnostic cloud is predeclared analytic input, not a sampled cloud",
    "the ESS warning contract is report-only and does not establish production execution",
    "the T28-INVALID table alone specifies expectations and does not prove a production boundary; CP57 count/type pre-RNG kernel hardening and live tests are separate evidence",
    "no RNG uniformity, IID, stream independence, operational source law, categorical law, confirmatory run, Formal Test 28 closure, or manuscript claim is established",
)

MAX_CP57_TEXT_LENGTH = 4_096
MAX_CP57_EXACT_INTEGER_BITS = 32_768
MAX_CP57_REFUSAL_CASES = 64

_DIGEST_DOMAIN = CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION
_ZERO_SHA256 = "0" * 64
_ONE = Fraction(1, 1)
_ZERO = Fraction(0, 1)
_AESS_ACTIVITY = _ONE
_AESS_TOTAL_CAP = 2
_AESS_TYPE_LABELS = ("a", "b")
_AESS_EVENT_DIMENSIONS = (0, 0)
_AESS_TYPE_WEIGHTS = (Fraction(2, 5), Fraction(3, 5))
_AESS_SUPPORT_LABELS = ("empty", "a", "b", "aa", "ab", "bb")
_AESS_COUNT_VECTORS = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))
_AESS_FACTORS = (_ONE, _ONE, _ONE, _ONE, _ONE, Fraction(1024, 1))
_AESS_PARTICLE_COUNT = 8
_AESS_CLOUD_STATE_INDICES = (0, 1, 2, 3, 4, 5, 0, 1)
_AESS_ESS_WARNING_FRACTION = Fraction(1, 4)
_AESS_STRATEGY = "fixed-budget-sir"
_OWNED_RNG_ROLES = ("proposal", "rejection-decision", "sir-resampling")
_RECORD_CONSTRUCTION_TOKEN = object()


class _SealedRecord:
    __slots__ = ()

    def __new__(cls, *, _construction_token: object = None) -> "_SealedRecord":
        if _construction_token is not _RECORD_CONSTRUCTION_TOKEN:
            raise TypeError(cls.__name__ + " records are module-created")
        return super().__new__(cls)

    def __init__(self, *, _construction_token: object = None) -> None:
        if _construction_token is not _RECORD_CONSTRUCTION_TOKEN:
            raise TypeError(type(self).__name__ + " records are module-created")

    def __reduce__(self) -> object:
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")

    def __reduce_ex__(self, protocol: object) -> object:
        del protocol
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if cls.__bases__ != (_SealedRecord,):
            raise TypeError(cls.__name__ + " cannot be subclassed")


def _construct_record(record_type: type, values: Mapping[str, object]) -> object:
    if type(record_type) is not type or not issubclass(record_type, _SealedRecord):
        raise TypeError("record_type must be a sealed CP57 record class")
    if type(values) is not dict:
        raise TypeError("record values must be an exact dict")
    expected = tuple(record_type.__annotations__)
    if set(values) != set(expected):
        raise TypeError(record_type.__name__ + " construction fields differ")
    record = record_type(_construction_token=_RECORD_CONSTRUCTION_TOKEN)
    for name in expected:
        object.__setattr__(record, name, values[name])
    return record


def _text(value: object, name: str, maximum: int = MAX_CP57_TEXT_LENGTH) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value) > maximum:
        raise ValueError(name + " has invalid bounded length")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(name + " must contain printable ASCII only")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact non-boolean integer")
    if not minimum <= value <= maximum:
        raise ValueError(name + " lies outside its frozen bound")
    return value


def _fraction(
    value: object,
    name: str,
    *,
    nonnegative: bool = False,
    positive: bool = False,
) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if (
        max(value.numerator.bit_length(), value.denominator.bit_length())
        > MAX_CP57_EXACT_INTEGER_BITS
    ):
        raise ValueError(name + " exceeds the exact-integer bit bound")
    if positive and value <= 0:
        raise ValueError(name + " must be strictly positive")
    if nonnegative and value < 0:
        raise ValueError(name + " must be nonnegative")
    return value


def _exact_tuple(value: object, name: str, length: int) -> tuple:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) != length:
        raise ValueError(name + " has the wrong frozen length")
    return value


def _sha256(value: object, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return value


def _fraction_tuple(
    value: object,
    name: str,
    length: int,
    *,
    positive: bool = False,
) -> Tuple[Fraction, ...]:
    items = _exact_tuple(value, name, length)
    for index, item in enumerate(items):
        _fraction(item, "%s[%d]" % (name, index), positive=positive)
    return items


def _text_tuple(value: object, name: str, length: int) -> Tuple[str, ...]:
    items = _exact_tuple(value, name, length)
    for index, item in enumerate(items):
        _text(item, "%s[%d]" % (name, index))
    return items


def _integer_tuple(
    value: object,
    name: str,
    length: int,
    minimum: int,
    maximum: int,
) -> Tuple[int, ...]:
    items = _exact_tuple(value, name, length)
    for index, item in enumerate(items):
        _integer(item, "%s[%d]" % (name, index), minimum, maximum)
    return items


def _count_vector_tuple(value: object, name: str) -> Tuple[Tuple[int, ...], ...]:
    vectors = _exact_tuple(value, name, len(_AESS_COUNT_VECTORS))
    for index, vector in enumerate(vectors):
        checked = _integer_tuple(
            vector,
            "%s[%d]" % (name, index),
            len(_AESS_TYPE_LABELS),
            0,
            _AESS_TOTAL_CAP,
        )
        if sum(checked) > _AESS_TOTAL_CAP:
            raise ValueError("%s[%d] exceeds the total cap" % (name, index))
    return vectors


def _canonical(value: object) -> object:
    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-v1", str(value)]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is Fraction:
        _fraction(value, "canonical fraction")
        return ["fraction-v1", str(value.numerator), str(value.denominator)]
    if type(value) is tuple:
        return ["tuple-v1", [_canonical(item) for item in value]]
    if is_dataclass(value) and not isinstance(value, type):
        if type(value).__module__ != __name__:
            raise TypeError("unsupported canonical record")
        return [
            "record-v1",
            type(value).__name__,
            [
                [field.name, _canonical(getattr(value, field.name))]
                for field in fields(value)
                if field.name != "record_sha256"
            ],
        ]
    raise TypeError("unsupported canonical value " + type(value).__name__)


def _digest(kind: str, value: object) -> str:
    document = {
        "domain": _DIGEST_DOMAIN,
        "kind": _text(kind, "digest kind", 128),
        "payload": _canonical(value),
    }
    encoded = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _factorial(value: int) -> int:
    value = _integer(value, "factorial input", 0, _AESS_TOTAL_CAP)
    return math.factorial(value)


def _derive_aess_base_probabilities() -> Tuple[Fraction, ...]:
    raw = []
    for counts in _AESS_COUNT_VECTORS:
        cardinality = sum(counts)
        mass = _AESS_ACTIVITY**cardinality
        for index, count in enumerate(counts):
            mass *= _AESS_TYPE_WEIGHTS[index] ** count / _factorial(count)
        raw.append(mass)
    normalizer = sum(raw, _ZERO)
    if normalizer != Fraction(5, 2):
        raise ArithmeticError("T28-AESS primitive base normalizer differs")
    return tuple(value / normalizer for value in raw)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class AtomicLowESSDiagnosticV1(_SealedRecord):
    particle_count: int
    cloud_state_indices: Tuple[int, ...]
    unnormalized_weights: Tuple[Fraction, ...]
    weight_sum: Fraction
    squared_weight_sum: Fraction
    normalized_weights: Tuple[Fraction, ...]
    effective_sample_size: Fraction
    effective_sample_size_fraction: Fraction
    ess_warning_fraction: Fraction
    ess_warning_threshold: Fraction
    ess_warning_comparator: str
    expected_ess_warning: bool
    warning_policy_is_report_only: bool
    expected_reported_particle_count: int
    expected_warning_triggered_extra_particles: int
    expected_warning_triggered_extra_draws: int
    expected_warning_triggered_fallback: bool
    expected_warning_triggered_cloud_reuse: bool
    precommitted_strategy: str
    expected_strategy_after_warning: str
    expected_resampling_draw_count: int
    record_sha256: str


@dataclass(frozen=True, slots=True, init=False, eq=False)
class AtomicLowESSOracleV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    formula_id: str
    scope: str
    activity: Fraction
    total_cap: int
    type_labels: Tuple[str, ...]
    event_dimensions: Tuple[int, ...]
    type_weights: Tuple[Fraction, ...]
    support_labels: Tuple[str, ...]
    count_vectors: Tuple[Tuple[int, ...], ...]
    base_probabilities: Tuple[Fraction, ...]
    multiplicative_factors: Tuple[Fraction, ...]
    unnormalized_target_masses: Tuple[Fraction, ...]
    target_normalizer: Fraction
    target_probabilities: Tuple[Fraction, ...]
    heavy_state_index: int
    heavy_state_label: str
    diagnostic: AtomicLowESSDiagnosticV1
    finite_all_atomic_exact_target: bool
    primitive_factorial_base_reconstruction: bool
    exact_expected_ess_warning_decision: bool
    report_only_policy_bound: bool
    production_behavior_observed: bool
    factors_are_exp_of_exact_rational_q: bool
    score_provider_facade_integrated: bool
    initializer_kernel_integrated: bool
    diagnostic_cloud_sampled: bool
    runtime_source_or_rng_law_verified: bool
    operational_prediction: bool
    confirmatory_evidence: bool
    formal_test28_evidence: bool
    manuscript_claim: bool
    nonclaims: Tuple[str, ...]
    record_sha256: str


def _validate_aess_diagnostic(
    diagnostic: object,
) -> AtomicLowESSDiagnosticV1:
    if type(diagnostic) is not AtomicLowESSDiagnosticV1:
        raise TypeError("T28-AESS diagnostic has the wrong exact type")
    particle_count = _integer(
        diagnostic.particle_count,
        "T28-AESS particle count",
        _AESS_PARTICLE_COUNT,
        _AESS_PARTICLE_COUNT,
    )
    indices = _exact_tuple(
        diagnostic.cloud_state_indices,
        "T28-AESS cloud state indices",
        particle_count,
    )
    _integer_tuple(
        indices,
        "T28-AESS cloud state indices",
        particle_count,
        0,
        len(_AESS_SUPPORT_LABELS) - 1,
    )
    if indices != _AESS_CLOUD_STATE_INDICES:
        raise ValueError("T28-AESS diagnostic cloud differs")
    weights = _exact_tuple(
        diagnostic.unnormalized_weights,
        "T28-AESS diagnostic weights",
        particle_count,
    )
    expected_weights = tuple(_AESS_FACTORS[index] for index in indices)
    _fraction_tuple(
        weights,
        "T28-AESS diagnostic weights",
        particle_count,
        positive=True,
    )
    if weights != expected_weights:
        raise ValueError("T28-AESS diagnostic weights differ")
    total = sum(expected_weights, _ZERO)
    squared = sum((value * value for value in expected_weights), _ZERO)
    expected_normalized = tuple(value / total for value in expected_weights)
    expected_ess = total * total / squared
    expected_fraction = expected_ess / particle_count
    expected_threshold = _AESS_ESS_WARNING_FRACTION * particle_count
    for name, supplied, expected in (
        ("weight sum", diagnostic.weight_sum, total),
        ("squared weight sum", diagnostic.squared_weight_sum, squared),
        ("effective sample size", diagnostic.effective_sample_size, expected_ess),
        (
            "effective sample size fraction",
            diagnostic.effective_sample_size_fraction,
            expected_fraction,
        ),
        (
            "ESS warning fraction",
            diagnostic.ess_warning_fraction,
            _AESS_ESS_WARNING_FRACTION,
        ),
        ("ESS warning threshold", diagnostic.ess_warning_threshold, expected_threshold),
    ):
        _fraction(supplied, "T28-AESS " + name)
        if supplied != expected:
            raise ValueError("T28-AESS " + name + " differs")
    if (
        _text(
            diagnostic.ess_warning_comparator,
            "T28-AESS ESS warning comparator",
            128,
        )
        != "effective_sample_size < ess_warning_fraction * particle_count"
    ):
        raise ValueError("T28-AESS ESS warning comparator differs")
    normalized = _exact_tuple(
        diagnostic.normalized_weights,
        "T28-AESS normalized weights",
        particle_count,
    )
    _fraction_tuple(
        normalized,
        "T28-AESS normalized weights",
        particle_count,
        positive=True,
    )
    if normalized != expected_normalized:
        raise ValueError("T28-AESS normalized weights differ")
    if sum(normalized, _ZERO) != _ONE:
        raise ValueError("T28-AESS normalized weights do not sum exactly to one")
    if diagnostic.expected_ess_warning is not (expected_ess < expected_threshold):
        raise ValueError("T28-AESS warning decision differs")
    if diagnostic.expected_ess_warning is not True:
        raise ValueError("T28-AESS must exercise the low-ESS warning")
    expected_claims = {
        "warning_policy_is_report_only": True,
        "expected_warning_triggered_fallback": False,
        "expected_warning_triggered_cloud_reuse": False,
    }
    for name, expected in expected_claims.items():
        supplied = getattr(diagnostic, name)
        if type(supplied) is not bool or supplied is not expected:
            raise ValueError("T28-AESS diagnostic flag " + name + " differs")
    if (
        _integer(
            diagnostic.expected_reported_particle_count,
            "T28-AESS expected reported particle count",
            particle_count,
            particle_count,
        )
        != particle_count
    ):
        raise ValueError("T28-AESS warning altered the reported particle count")
    for name in (
        "expected_warning_triggered_extra_particles",
        "expected_warning_triggered_extra_draws",
    ):
        if _integer(getattr(diagnostic, name), "T28-AESS " + name, 0, 0) != 0:
            raise ValueError("T28-AESS warning triggered adaptive work")
    for name in ("precommitted_strategy", "expected_strategy_after_warning"):
        if _text(getattr(diagnostic, name), "T28-AESS " + name, 64) != _AESS_STRATEGY:
            raise ValueError("T28-AESS warning changed strategy")
    if (
        _integer(
            diagnostic.expected_resampling_draw_count,
            "T28-AESS expected resampling draw count",
            1,
            1,
        )
        != 1
    ):
        raise ValueError("T28-AESS resampling draw count differs")
    _sha256(diagnostic.record_sha256, "T28-AESS diagnostic digest")
    if diagnostic.record_sha256 != _digest("aess-diagnostic", diagnostic):
        raise ValueError("T28-AESS diagnostic digest differs")
    return diagnostic


def _make_aess_diagnostic() -> AtomicLowESSDiagnosticV1:
    indices = _AESS_CLOUD_STATE_INDICES
    weights = tuple(_AESS_FACTORS[index] for index in indices)
    total = sum(weights, _ZERO)
    squared = sum((value * value for value in weights), _ZERO)
    ess = total * total / squared
    values = {
        "particle_count": _AESS_PARTICLE_COUNT,
        "cloud_state_indices": indices,
        "unnormalized_weights": weights,
        "weight_sum": total,
        "squared_weight_sum": squared,
        "normalized_weights": tuple(value / total for value in weights),
        "effective_sample_size": ess,
        "effective_sample_size_fraction": ess / _AESS_PARTICLE_COUNT,
        "ess_warning_fraction": _AESS_ESS_WARNING_FRACTION,
        "ess_warning_threshold": _AESS_ESS_WARNING_FRACTION * _AESS_PARTICLE_COUNT,
        "ess_warning_comparator": (
            "effective_sample_size < ess_warning_fraction * particle_count"
        ),
        "expected_ess_warning": ess < _AESS_ESS_WARNING_FRACTION * _AESS_PARTICLE_COUNT,
        "warning_policy_is_report_only": True,
        "expected_reported_particle_count": _AESS_PARTICLE_COUNT,
        "expected_warning_triggered_extra_particles": 0,
        "expected_warning_triggered_extra_draws": 0,
        "expected_warning_triggered_fallback": False,
        "expected_warning_triggered_cloud_reuse": False,
        "precommitted_strategy": _AESS_STRATEGY,
        "expected_strategy_after_warning": _AESS_STRATEGY,
        "expected_resampling_draw_count": 1,
        "record_sha256": _ZERO_SHA256,
    }
    provisional = _construct_record(AtomicLowESSDiagnosticV1, values)
    values["record_sha256"] = _digest("aess-diagnostic", provisional)
    return _validate_aess_diagnostic(
        _construct_record(AtomicLowESSDiagnosticV1, values)
    )


def _validate_aess_oracle(record: object) -> AtomicLowESSOracleV1:
    if type(record) is not AtomicLowESSOracleV1:
        raise TypeError("T28-AESS oracle has the wrong exact type")
    for supplied, expected, name in (
        (record.schema_version, CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION, "schema"),
        (record.fixture_id, CP57_TEST28_AESS_FIXTURE_ID, "fixture identifier"),
        (record.formula_id, CP57_TEST28_AESS_FORMULA_ID, "formula identifier"),
        (record.scope, CP57_TEST28_STRESS_REFUSAL_SCOPE, "scope"),
    ):
        if _text(supplied, "T28-AESS " + name) != expected:
            raise ValueError("T28-AESS " + name + " differs")
    _fraction(record.activity, "T28-AESS activity", positive=True)
    if record.activity != _AESS_ACTIVITY:
        raise ValueError("T28-AESS activity differs")
    if _integer(record.total_cap, "T28-AESS total cap", 2, 2) != 2:
        raise ValueError("T28-AESS total cap differs")
    _text_tuple(record.type_labels, "T28-AESS type labels", 2)
    _integer_tuple(record.event_dimensions, "T28-AESS event dimensions", 2, 0, 0)
    _fraction_tuple(record.type_weights, "T28-AESS type weights", 2, positive=True)
    _text_tuple(record.support_labels, "T28-AESS support labels", 6)
    _count_vector_tuple(record.count_vectors, "T28-AESS count vectors")
    _fraction_tuple(
        record.multiplicative_factors,
        "T28-AESS multiplicative factors",
        6,
        positive=True,
    )
    expected_tuples = (
        ("type labels", record.type_labels, _AESS_TYPE_LABELS),
        ("event dimensions", record.event_dimensions, _AESS_EVENT_DIMENSIONS),
        ("type weights", record.type_weights, _AESS_TYPE_WEIGHTS),
        ("support labels", record.support_labels, _AESS_SUPPORT_LABELS),
        ("count vectors", record.count_vectors, _AESS_COUNT_VECTORS),
        ("multiplicative factors", record.multiplicative_factors, _AESS_FACTORS),
    )
    for name, supplied, expected in expected_tuples:
        if type(supplied) is not tuple or supplied != expected:
            raise ValueError("T28-AESS " + name + " differ")
    base = _derive_aess_base_probabilities()
    _fraction_tuple(
        record.base_probabilities, "T28-AESS base probabilities", 6, positive=True
    )
    if record.base_probabilities != base:
        raise ValueError("T28-AESS base probabilities differ")
    masses = tuple(base[index] * _AESS_FACTORS[index] for index in range(6))
    normalizer = sum(masses, _ZERO)
    target = tuple(value / normalizer for value in masses)
    _fraction_tuple(
        record.unnormalized_target_masses,
        "T28-AESS unnormalized target masses",
        6,
        positive=True,
    )
    if record.unnormalized_target_masses != masses:
        raise ValueError("T28-AESS target masses differ")
    _fraction(record.target_normalizer, "T28-AESS target normalizer", positive=True)
    if record.target_normalizer != normalizer:
        raise ValueError("T28-AESS target normalizer differs")
    _fraction_tuple(
        record.target_probabilities,
        "T28-AESS target probabilities",
        6,
        positive=True,
    )
    if record.target_probabilities != target or sum(target, _ZERO) != _ONE:
        raise ValueError("T28-AESS target probabilities differ")
    _integer(record.heavy_state_index, "T28-AESS heavy state index", 0, 5)
    _text(record.heavy_state_label, "T28-AESS heavy state label", 64)
    if record.heavy_state_index != 5 or record.heavy_state_label != "bb":
        raise ValueError("T28-AESS heavy-state binding differs")
    if target[record.heavy_state_index] <= Fraction(49, 50):
        raise ValueError("T28-AESS target is not sufficiently concentrated")
    _validate_aess_diagnostic(record.diagnostic)
    expected_flags = {
        "finite_all_atomic_exact_target": True,
        "primitive_factorial_base_reconstruction": True,
        "exact_expected_ess_warning_decision": True,
        "report_only_policy_bound": True,
        "production_behavior_observed": False,
        "factors_are_exp_of_exact_rational_q": False,
        "score_provider_facade_integrated": False,
        "initializer_kernel_integrated": False,
        "diagnostic_cloud_sampled": False,
        "runtime_source_or_rng_law_verified": False,
        "operational_prediction": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
    }
    for name, expected in expected_flags.items():
        supplied = getattr(record, name)
        if type(supplied) is not bool or supplied is not expected:
            raise ValueError("T28-AESS claim flag " + name + " differs")
    _text_tuple(
        record.nonclaims,
        "T28-AESS nonclaims",
        len(CP57_TEST28_STRESS_REFUSAL_NONCLAIMS),
    )
    if record.nonclaims != CP57_TEST28_STRESS_REFUSAL_NONCLAIMS:
        raise ValueError("T28-AESS nonclaims differ")
    _sha256(record.record_sha256, "T28-AESS oracle digest")
    if record.record_sha256 != _digest("aess-oracle", record):
        raise ValueError("T28-AESS oracle digest differs")
    return record


def t28_aess_low_ess_oracle_v1() -> AtomicLowESSOracleV1:
    """Return the sealed exact ``T28-AESS`` analytic/reporting oracle."""

    base = _derive_aess_base_probabilities()
    masses = tuple(base[index] * _AESS_FACTORS[index] for index in range(6))
    normalizer = sum(masses, _ZERO)
    values = {
        "schema_version": CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION,
        "fixture_id": CP57_TEST28_AESS_FIXTURE_ID,
        "formula_id": CP57_TEST28_AESS_FORMULA_ID,
        "scope": CP57_TEST28_STRESS_REFUSAL_SCOPE,
        "activity": _AESS_ACTIVITY,
        "total_cap": _AESS_TOTAL_CAP,
        "type_labels": _AESS_TYPE_LABELS,
        "event_dimensions": _AESS_EVENT_DIMENSIONS,
        "type_weights": _AESS_TYPE_WEIGHTS,
        "support_labels": _AESS_SUPPORT_LABELS,
        "count_vectors": _AESS_COUNT_VECTORS,
        "base_probabilities": base,
        "multiplicative_factors": _AESS_FACTORS,
        "unnormalized_target_masses": masses,
        "target_normalizer": normalizer,
        "target_probabilities": tuple(value / normalizer for value in masses),
        "heavy_state_index": 5,
        "heavy_state_label": "bb",
        "diagnostic": _make_aess_diagnostic(),
        "finite_all_atomic_exact_target": True,
        "primitive_factorial_base_reconstruction": True,
        "exact_expected_ess_warning_decision": True,
        "report_only_policy_bound": True,
        "production_behavior_observed": False,
        "factors_are_exp_of_exact_rational_q": False,
        "score_provider_facade_integrated": False,
        "initializer_kernel_integrated": False,
        "diagnostic_cloud_sampled": False,
        "runtime_source_or_rng_law_verified": False,
        "operational_prediction": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
        "nonclaims": CP57_TEST28_STRESS_REFUSAL_NONCLAIMS,
        "record_sha256": _ZERO_SHA256,
    }
    provisional = _construct_record(AtomicLowESSOracleV1, values)
    values["record_sha256"] = _digest("aess-oracle", provisional)
    return _validate_aess_oracle(_construct_record(AtomicLowESSOracleV1, values))


def validate_t28_aess_low_ess_oracle_v1(
    record: object,
) -> AtomicLowESSOracleV1:
    """Structurally validate a sealed AESS record without runtime execution."""

    return _validate_aess_oracle(record)


_INVALID_CATEGORY_REGISTRY = (
    "negative-factor",
    "nan-factor",
    "positive-infinite-factor",
    "false-envelope",
    "zero-categorical-mass",
    "invalid-categorical-mass",
    "wrong-dimension",
    "noncanonical-state",
    "resource-limit",
)
_ALL_STRATEGIES = (
    "finite-atomic-enumeration",
    "bounded-rejection",
    "fixed-budget-sir",
)
_STOCHASTIC_STRATEGIES = ("bounded-rejection", "fixed-budget-sir")
_SIR_STRATEGY = ("fixed-budget-sir",)
_REJECTION_STRATEGY = ("bounded-rejection",)
_ENUMERATION_STRATEGY = ("finite-atomic-enumeration",)
_INVALID_EXPECTATION_SCOPES = (
    "oracle-model-only",
    "direct-helper-preflight",
    "provider-preflight-only",
    "production-preflight",
)
_INVALID_CASE_SPECS = (
    (
        "T28-INVALID-NEGATIVE-FACTOR",
        "NEGATIVE_FACTOR",
        "negative-factor",
        "weights=(0x1.0000000000000p+0,-0x1.0000000000000p+0)",
        "independent-ess-weight-preflight",
        _SIR_STRATEGY,
        "builtins.ValueError",
        "weights[1] must be strictly positive",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-NAN-FACTOR",
        "NAN_FACTOR",
        "nan-factor",
        "weights=(0x1.0000000000000p+0,nan)",
        "independent-ess-weight-preflight",
        _SIR_STRATEGY,
        "builtins.ValueError",
        "weights[1] must not be NaN",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-POSITIVE-INFINITE-FACTOR",
        "POSITIVE_INFINITE_FACTOR",
        "positive-infinite-factor",
        "weights=(0x1.0000000000000p+0,+inf)",
        "independent-ess-weight-preflight",
        _SIR_STRATEGY,
        "builtins.ValueError",
        "weights[1] must be finite",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-FALSE-ENVELOPE",
        "FALSE_ENVELOPE",
        "false-envelope",
        "fixture=T28-A0-H;factors=(1/1,2/1,1/2,3/1,3/2,1/4);"
        "declared_envelope=2/1;declared_acceptance=549/1000",
        "independent-atomic-envelope-preflight",
        _REJECTION_STRATEGY,
        "builtins.ValueError",
        "A0 rejection envelope is invalid",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-ALL-ZERO-SIR-WEIGHTS",
        "ALL_ZERO_SIR_WEIGHTS",
        "zero-categorical-mass",
        "weights=(0x0.0p+0,0x0.0p+0)",
        "independent-ess-weight-preflight",
        _SIR_STRATEGY,
        "builtins.ValueError",
        "weights[0] must be strictly positive",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-ZERO-CATEGORICAL-BIN",
        "ZERO_CATEGORICAL_BIN",
        "zero-categorical-mass",
        "normalized_weights=(0x1.0000000000000p+0,0x0.0p+0);raw_word=0",
        "kernel-v2-categorical-transform-preflight",
        _SIR_STRATEGY,
        "builtins.ValueError",
        "normalized_weights must be strictly positive",
        "direct-helper-preflight",
    ),
    (
        "T28-INVALID-NONNORMALIZED-CATEGORICAL-MASS",
        "NONNORMALIZED_CATEGORICAL_MASS",
        "invalid-categorical-mass",
        "normalized_weights=(0x1.3333333333333p-1," "0x1.3333333333333p-1);raw_word=0",
        "kernel-v2-categorical-transform-preflight",
        _SIR_STRATEGY,
        "builtins.ValueError",
        "normalized_weights must sum to one",
        "direct-helper-preflight",
    ),
    (
        "T28-INVALID-COUNT-CATEGORICAL-RESOLUTION",
        "COUNT_CATEGORICAL_RESOLUTION",
        "invalid-categorical-mass",
        "type_dimensions=(0);type_weights=(0x1.0000000000000p+0);"
        "activity=0x1.0000000000000p-41;total_cap=1",
        "kernel-v2-reference-sampling-resolution-preflight",
        _STOCHASTIC_STRATEGIES,
        "heterodiff.theory.configuration_reference."
        "UnsupportedReferenceSamplingError",
        "count categorical law fails the pre-RNG sampling-resolution preflight",
        "production-preflight",
    ),
    (
        "T28-INVALID-TYPE-CATEGORICAL-RESOLUTION",
        "TYPE_CATEGORICAL_RESOLUTION",
        "invalid-categorical-mass",
        "type_dimensions=(0,0);type_weights=(0x1.0000000000000p-41,"
        "0x1.ffffffffff000p-1);activity=0x1.0000000000000p+0;total_cap=1",
        "kernel-v2-reference-sampling-resolution-preflight",
        _STOCHASTIC_STRATEGIES,
        "heterodiff.theory.configuration_reference."
        "UnsupportedReferenceSamplingError",
        "type categorical law fails the pre-RNG sampling-resolution preflight",
        "production-preflight",
    ),
    (
        "T28-INVALID-WRONG-EVENT-DIMENSION",
        "WRONG_EVENT_DIMENSION",
        "wrong-dimension",
        "fixture=T28-M1-Q;event_type=1;coordinates=()",
        "certified-score-provider-v1-configuration-preflight",
        _STOCHASTIC_STRATEGIES,
        "builtins.ValueError",
        "event coordinates have the wrong dimension",
        "provider-preflight-only",
    ),
    (
        "T28-INVALID-NONCANONICAL-NEGATIVE-ZERO-STATE",
        "NONCANONICAL_STATE",
        "noncanonical-state",
        "fixture=T28-M1-Q;event_type=1;coordinates=(-0x0.0p+0)",
        "certified-score-provider-v1-configuration-preflight",
        _STOCHASTIC_STRATEGIES,
        "builtins.ValueError",
        "event coordinates must use canonical positive zero",
        "provider-preflight-only",
    ),
    (
        "T28-INVALID-OCCURRENCE-WORK-LIMIT",
        "OCCURRENCE_WORK_LIMIT",
        "resource-limit",
        "type_dimensions=(0);type_weights=(0x1.0000000000000p+0);"
        "activity=0x1.0000000000000p+0;total_cap=123;budget=4096;"
        "worst_occurrences=503808;occurrence_limit=500000",
        "kernel-v2-stochastic-resource-preflight",
        _STOCHASTIC_STRATEGIES,
        "builtins.ValueError",
        "planned stochastic work exceeds reference resource limits",
        "production-preflight",
    ),
    (
        "T28-INVALID-COORDINATE-WORK-LIMIT",
        "COORDINATE_WORK_LIMIT",
        "resource-limit",
        "type_dimensions=(1000);type_weights=(0x1.0000000000000p+0);"
        "activity=0x1.0000000000000p+0;total_cap=1;budget=4096;"
        "worst_coordinates=4096000;coordinate_limit=4000000",
        "kernel-v2-stochastic-resource-preflight",
        _STOCHASTIC_STRATEGIES,
        "builtins.ValueError",
        "planned stochastic work exceeds reference resource limits",
        "production-preflight",
    ),
    (
        "T28-INVALID-FINITE-ATOMIC-SUPPORT-LIMIT",
        "FINITE_ATOMIC_SUPPORT_LIMIT",
        "resource-limit",
        "type_dimensions=(0,0);type_weights=(0x1.0000000000000p-1,"
        "0x1.0000000000000p-1);activity=0x1.0000000000000p+0;"
        "total_cap=22;support_states=276;support_limit=256",
        "kernel-v2-finite-atomic-oracle-resource-preflight",
        _ENUMERATION_STRATEGY,
        "builtins.ValueError",
        "counting space would have 276 states, exceeding the finite oracle limit of 256",
        "production-preflight",
    ),
)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class DeterministicRefusalCaseV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    case_id: str
    refusal_code: str
    category: str
    malformed_payload_encoding: str
    validation_boundary: str
    applicable_strategies: Tuple[str, ...]
    expected_exception_qualname: str
    expected_exception_message: str
    expectation_scope: str
    refusal_precedes_any_owned_rng_factory_call: bool
    expected_owned_rng_roles_not_constructed: Tuple[str, ...]
    expected_rng_factory_call_count: int
    expected_externally_supplied_sentinel_rng_state_byte_identity: bool
    expected_result_artifact_created: bool
    production_preflight_expectation: bool
    production_boundary_verified_by_this_record: bool
    confirmatory_evidence: bool
    formal_test28_evidence: bool
    manuscript_claim: bool
    record_sha256: str


@dataclass(frozen=True, slots=True, init=False, eq=False)
class DeterministicRefusalTableV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    table_id: str
    scope: str
    category_registry: Tuple[str, ...]
    cases: Tuple[DeterministicRefusalCaseV1, ...]
    required_case_count: int
    all_required_categories_covered: bool
    case_ids_unique: bool
    exact_exception_expectations_bound: bool
    pre_rng_custody_policy_bound: bool
    production_boundaries_verified_by_table: bool
    operational_source_or_rng_law_verified: bool
    confirmatory_evidence: bool
    formal_test28_evidence: bool
    manuscript_claim: bool
    nonclaims: Tuple[str, ...]
    record_sha256: str


@dataclass(frozen=True, slots=True, init=False, eq=False)
class DeterministicRefusalObservationV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    table_record_sha256: str
    case_id: str
    case_record_sha256: str
    validation_boundary: str
    expectation_scope: str
    observed_exception_qualname: str
    observed_exception_message: str
    owned_rng_roles_not_constructed: Tuple[str, ...]
    externally_supplied_sentinel_rng_state_sha256_before: Tuple[Tuple[str, str], ...]
    externally_supplied_sentinel_rng_state_sha256_after: Tuple[Tuple[str, str], ...]
    rng_factory_call_count: int
    result_artifact_created: bool
    supplied_exception_matches_frozen_expectation: bool
    externally_supplied_sentinel_rng_state_digests_byte_identical: bool
    supplied_observation_matches_frozen_expectation: bool
    case_expectation_is_production_preflight: bool
    exact_exception_class_identity_checked: bool
    builtin_value_error_identity_checked: bool
    production_unsupported_reference_error_identity_checked: bool
    boundary_invocation_provenance_verified: bool
    sentinel_rng_state_digest_provenance_verified: bool
    cryptographic_authentication: bool
    production_runner_evidence: bool
    confirmatory_evidence: bool
    formal_test28_evidence: bool
    manuscript_claim: bool
    record_sha256: str


@dataclass(frozen=True, slots=True, init=False, eq=False)
class Test28StressRefusalOracleBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    aess_oracle: AtomicLowESSOracleV1
    aess_record_sha256: str
    invalid_refusal_table: DeterministicRefusalTableV1
    invalid_refusal_table_record_sha256: str
    subrecord_digests_distinct: bool
    source_law_verified: bool
    confirmatory_evidence: bool
    formal_test28_evidence: bool
    manuscript_claim: bool
    record_sha256: str


def _case_spec_by_id(case_id: str) -> tuple:
    _text(case_id, "T28-INVALID case identifier", 128)
    matches = tuple(spec for spec in _INVALID_CASE_SPECS if spec[0] == case_id)
    if len(matches) != 1:
        raise ValueError("T28-INVALID case identifier is unknown")
    return matches[0]


def _validate_strategy_tuple(value: object, name: str) -> Tuple[str, ...]:
    if type(value) is not tuple or not 1 <= len(value) <= len(_ALL_STRATEGIES):
        raise ValueError(name + " has an unsupported length")
    for index, strategy in enumerate(value):
        if _text(strategy, "%s[%d]" % (name, index), 64) not in _ALL_STRATEGIES:
            raise ValueError(name + " contains an unknown strategy")
    if len(set(value)) != len(value):
        raise ValueError(name + " contains a duplicate strategy")
    return value


def _validate_refusal_case(record: object) -> DeterministicRefusalCaseV1:
    if type(record) is not DeterministicRefusalCaseV1:
        raise TypeError("T28-INVALID case has the wrong exact type")
    if _text(record.schema_version, "T28-INVALID case schema") != (
        CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION
    ):
        raise ValueError("T28-INVALID case schema differs")
    if _text(record.fixture_id, "T28-INVALID fixture identifier", 64) != (
        CP57_TEST28_INVALID_FIXTURE_ID
    ):
        raise ValueError("T28-INVALID fixture identifier differs")
    case_id = _text(record.case_id, "T28-INVALID case identifier", 128)
    spec = _case_spec_by_id(case_id)
    for name in (
        "refusal_code",
        "category",
        "malformed_payload_encoding",
        "validation_boundary",
        "expected_exception_qualname",
        "expected_exception_message",
        "expectation_scope",
    ):
        _text(getattr(record, name), "T28-INVALID " + name)
    _validate_strategy_tuple(
        record.applicable_strategies, "T28-INVALID applicable strategies"
    )
    actual_spec = (
        record.case_id,
        record.refusal_code,
        record.category,
        record.malformed_payload_encoding,
        record.validation_boundary,
        record.applicable_strategies,
        record.expected_exception_qualname,
        record.expected_exception_message,
        record.expectation_scope,
    )
    if actual_spec != spec:
        raise ValueError("T28-INVALID case fields differ from the frozen matrix")
    if record.category not in _INVALID_CATEGORY_REGISTRY:
        raise ValueError("T28-INVALID case category is unregistered")
    if record.expectation_scope not in _INVALID_EXPECTATION_SCOPES:
        raise ValueError("T28-INVALID expectation scope is unknown")
    if (
        _text_tuple(
            record.expected_owned_rng_roles_not_constructed,
            "T28-INVALID expected unconstructed RNG roles",
            3,
        )
        != _OWNED_RNG_ROLES
    ):
        raise ValueError("T28-INVALID expected unconstructed RNG roles differ")
    expected_flags = {
        "refusal_precedes_any_owned_rng_factory_call": True,
        "expected_externally_supplied_sentinel_rng_state_byte_identity": True,
        "expected_result_artifact_created": False,
        "production_preflight_expectation": (
            record.expectation_scope == "production-preflight"
        ),
        "production_boundary_verified_by_this_record": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
    }
    for name, expected in expected_flags.items():
        supplied = getattr(record, name)
        if type(supplied) is not bool or supplied is not expected:
            raise ValueError("T28-INVALID case flag " + name + " differs")
    if (
        _integer(
            record.expected_rng_factory_call_count,
            "T28-INVALID expected RNG factory call count",
            0,
            0,
        )
        != 0
    ):
        raise ValueError("T28-INVALID RNG factory expectation differs")
    _sha256(record.record_sha256, "T28-INVALID case digest")
    if record.record_sha256 != _digest("invalid-case", record):
        raise ValueError("T28-INVALID case digest differs")
    return record


def _make_refusal_case(spec: tuple) -> DeterministicRefusalCaseV1:
    (
        case_id,
        refusal_code,
        category,
        payload,
        boundary,
        strategies,
        exception_qualname,
        exception_message,
        expectation_scope,
    ) = spec
    values = {
        "schema_version": CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION,
        "fixture_id": CP57_TEST28_INVALID_FIXTURE_ID,
        "case_id": case_id,
        "refusal_code": refusal_code,
        "category": category,
        "malformed_payload_encoding": payload,
        "validation_boundary": boundary,
        "applicable_strategies": strategies,
        "expected_exception_qualname": exception_qualname,
        "expected_exception_message": exception_message,
        "expectation_scope": expectation_scope,
        "refusal_precedes_any_owned_rng_factory_call": True,
        "expected_owned_rng_roles_not_constructed": _OWNED_RNG_ROLES,
        "expected_rng_factory_call_count": 0,
        "expected_externally_supplied_sentinel_rng_state_byte_identity": True,
        "expected_result_artifact_created": False,
        "production_preflight_expectation": (
            expectation_scope == "production-preflight"
        ),
        "production_boundary_verified_by_this_record": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
        "record_sha256": _ZERO_SHA256,
    }
    provisional = _construct_record(DeterministicRefusalCaseV1, values)
    values["record_sha256"] = _digest("invalid-case", provisional)
    return _validate_refusal_case(_construct_record(DeterministicRefusalCaseV1, values))


def _validate_refusal_table(record: object) -> DeterministicRefusalTableV1:
    if type(record) is not DeterministicRefusalTableV1:
        raise TypeError("T28-INVALID table has the wrong exact type")
    for supplied, expected, name in (
        (record.schema_version, CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION, "schema"),
        (record.fixture_id, CP57_TEST28_INVALID_FIXTURE_ID, "fixture identifier"),
        (record.table_id, CP57_TEST28_INVALID_TABLE_ID, "table identifier"),
        (record.scope, CP57_TEST28_STRESS_REFUSAL_SCOPE, "scope"),
    ):
        if _text(supplied, "T28-INVALID " + name) != expected:
            raise ValueError("T28-INVALID " + name + " differs")
    if (
        _text_tuple(
            record.category_registry,
            "T28-INVALID category registry",
            len(_INVALID_CATEGORY_REGISTRY),
        )
        != _INVALID_CATEGORY_REGISTRY
    ):
        raise ValueError("T28-INVALID category registry differs")
    cases = _exact_tuple(record.cases, "T28-INVALID cases", len(_INVALID_CASE_SPECS))
    for case in cases:
        _validate_refusal_case(case)
    case_ids = tuple(case.case_id for case in cases)
    expected_ids = tuple(spec[0] for spec in _INVALID_CASE_SPECS)
    if case_ids != expected_ids:
        raise ValueError("T28-INVALID case order or completeness differs")
    categories = {case.category for case in cases}
    if categories != set(_INVALID_CATEGORY_REGISTRY):
        raise ValueError("T28-INVALID category coverage differs")
    if _integer(
        record.required_case_count,
        "T28-INVALID required case count",
        len(_INVALID_CASE_SPECS),
        len(_INVALID_CASE_SPECS),
    ) != len(_INVALID_CASE_SPECS):
        raise ValueError("T28-INVALID required case count differs")
    expected_flags = {
        "all_required_categories_covered": True,
        "case_ids_unique": True,
        "exact_exception_expectations_bound": True,
        "pre_rng_custody_policy_bound": True,
        "production_boundaries_verified_by_table": False,
        "operational_source_or_rng_law_verified": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
    }
    for name, expected in expected_flags.items():
        supplied = getattr(record, name)
        if type(supplied) is not bool or supplied is not expected:
            raise ValueError("T28-INVALID table flag " + name + " differs")
    _text_tuple(
        record.nonclaims,
        "T28-INVALID nonclaims",
        len(CP57_TEST28_STRESS_REFUSAL_NONCLAIMS),
    )
    if record.nonclaims != CP57_TEST28_STRESS_REFUSAL_NONCLAIMS:
        raise ValueError("T28-INVALID nonclaims differ")
    _sha256(record.record_sha256, "T28-INVALID table digest")
    if record.record_sha256 != _digest("invalid-table", record):
        raise ValueError("T28-INVALID table digest differs")
    return record


def t28_invalid_refusal_table_v1() -> DeterministicRefusalTableV1:
    """Return the complete 14-case deterministic refusal expectation table."""

    cases = tuple(_make_refusal_case(spec) for spec in _INVALID_CASE_SPECS)
    values = {
        "schema_version": CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION,
        "fixture_id": CP57_TEST28_INVALID_FIXTURE_ID,
        "table_id": CP57_TEST28_INVALID_TABLE_ID,
        "scope": CP57_TEST28_STRESS_REFUSAL_SCOPE,
        "category_registry": _INVALID_CATEGORY_REGISTRY,
        "cases": cases,
        "required_case_count": len(_INVALID_CASE_SPECS),
        "all_required_categories_covered": True,
        "case_ids_unique": True,
        "exact_exception_expectations_bound": True,
        "pre_rng_custody_policy_bound": True,
        "production_boundaries_verified_by_table": False,
        "operational_source_or_rng_law_verified": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
        "nonclaims": CP57_TEST28_STRESS_REFUSAL_NONCLAIMS,
        "record_sha256": _ZERO_SHA256,
    }
    provisional = _construct_record(DeterministicRefusalTableV1, values)
    values["record_sha256"] = _digest("invalid-table", provisional)
    return _validate_refusal_table(
        _construct_record(DeterministicRefusalTableV1, values)
    )


def validate_t28_invalid_refusal_table_v1(
    record: object,
) -> DeterministicRefusalTableV1:
    """Structurally validate the refusal table without exercising a boundary."""

    return _validate_refusal_table(record)


def _rng_state_tuple(value: object, name: str) -> Tuple[Tuple[str, str], ...]:
    entries = _exact_tuple(value, name, len(_OWNED_RNG_ROLES))
    roles = []
    for index, entry in enumerate(entries):
        pair = _exact_tuple(entry, "%s[%d]" % (name, index), 2)
        role = _text(pair[0], "%s[%d] role" % (name, index), 64)
        digest = _sha256(pair[1], "%s[%d] digest" % (name, index))
        roles.append((role, digest))
    checked = tuple(roles)
    if tuple(role for role, _ in checked) != _OWNED_RNG_ROLES:
        raise ValueError(name + " has the wrong frozen role order")
    return checked


def _exception_qualname(exception: object, expected: str) -> str:
    if not isinstance(exception, BaseException):
        raise TypeError("observed_exception must be an exception instance")
    if expected == "builtins.ValueError":
        if type(exception) is not ValueError:
            raise TypeError("observed exception has the wrong exact type")
    elif expected == (
        "heterodiff.theory.configuration_reference." "UnsupportedReferenceSamplingError"
    ):
        from heterodiff.theory.configuration_reference import (
            UnsupportedReferenceSamplingError,
        )

        if type(exception) is not UnsupportedReferenceSamplingError:
            raise TypeError("observed exception has the wrong exact type")
    else:  # pragma: no cover - the frozen table validator excludes this case
        raise RuntimeError("T28-INVALID exception registry escaped validation")
    return type(exception).__module__ + "." + type(exception).__qualname__


def _validate_refusal_observation(
    record: object,
    *,
    table: DeterministicRefusalTableV1,
) -> DeterministicRefusalObservationV1:
    if type(record) is not DeterministicRefusalObservationV1:
        raise TypeError("T28-INVALID observation has the wrong exact type")
    checked_table = _validate_refusal_table(table)
    if _text(record.schema_version, "T28-INVALID observation schema") != (
        CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION
    ):
        raise ValueError("T28-INVALID observation schema differs")
    if _text(record.fixture_id, "T28-INVALID observation fixture", 64) != (
        CP57_TEST28_INVALID_FIXTURE_ID
    ):
        raise ValueError("T28-INVALID observation fixture differs")
    _sha256(record.table_record_sha256, "T28-INVALID observation table digest")
    if record.table_record_sha256 != checked_table.record_sha256:
        raise ValueError("T28-INVALID observation belongs to another table")
    case_id = _text(record.case_id, "T28-INVALID observation case", 128)
    matches = tuple(case for case in checked_table.cases if case.case_id == case_id)
    if len(matches) != 1:
        raise ValueError("T28-INVALID observation case is unknown")
    case = matches[0]
    _sha256(record.case_record_sha256, "T28-INVALID observation case digest")
    if record.case_record_sha256 != case.record_sha256:
        raise ValueError("T28-INVALID observation case digest differs")
    for name, supplied, expected in (
        ("validation boundary", record.validation_boundary, case.validation_boundary),
        ("expectation scope", record.expectation_scope, case.expectation_scope),
        (
            "exception qualname",
            record.observed_exception_qualname,
            case.expected_exception_qualname,
        ),
        (
            "exception message",
            record.observed_exception_message,
            case.expected_exception_message,
        ),
    ):
        if _text(supplied, "T28-INVALID observation " + name) != expected:
            raise ValueError("T28-INVALID observation " + name + " differs")
    if (
        _text_tuple(
            record.owned_rng_roles_not_constructed,
            "T28-INVALID unconstructed RNG roles",
            3,
        )
        != _OWNED_RNG_ROLES
    ):
        raise ValueError("T28-INVALID unconstructed RNG roles differ")
    before = _rng_state_tuple(
        record.externally_supplied_sentinel_rng_state_sha256_before,
        "T28-INVALID external sentinel RNG states before",
    )
    after = _rng_state_tuple(
        record.externally_supplied_sentinel_rng_state_sha256_after,
        "T28-INVALID external sentinel RNG states after",
    )
    if before != after:
        raise ValueError("T28-INVALID external sentinel RNG states differ")
    if (
        _integer(
            record.rng_factory_call_count,
            "T28-INVALID RNG factory call count",
            0,
            0,
        )
        != 0
    ):
        raise ValueError("T28-INVALID refusal constructed an owned RNG")
    if type(record.result_artifact_created) is not bool:
        raise TypeError("T28-INVALID result-artifact flag must be Boolean")
    if record.result_artifact_created is not False:
        raise ValueError("T28-INVALID refusal created a result artifact")
    expected_flags = {
        "supplied_exception_matches_frozen_expectation": True,
        "externally_supplied_sentinel_rng_state_digests_byte_identical": True,
        "supplied_observation_matches_frozen_expectation": True,
        "case_expectation_is_production_preflight": (
            case.expectation_scope == "production-preflight"
        ),
        "exact_exception_class_identity_checked": True,
        "builtin_value_error_identity_checked": (
            case.expected_exception_qualname == "builtins.ValueError"
        ),
        "production_unsupported_reference_error_identity_checked": (
            case.expected_exception_qualname
            == "heterodiff.theory.configuration_reference."
            "UnsupportedReferenceSamplingError"
        ),
        "boundary_invocation_provenance_verified": False,
        "sentinel_rng_state_digest_provenance_verified": False,
        "cryptographic_authentication": False,
        "production_runner_evidence": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
    }
    for name, expected in expected_flags.items():
        supplied = getattr(record, name)
        if type(supplied) is not bool or supplied is not expected:
            raise ValueError("T28-INVALID observation flag " + name + " differs")
    _sha256(record.record_sha256, "T28-INVALID observation digest")
    if record.record_sha256 != _digest("invalid-observation", record):
        raise ValueError("T28-INVALID observation digest differs")
    return record


def verify_t28_invalid_refusal_observation_v1(
    table: DeterministicRefusalTableV1,
    *,
    case_id: object,
    observed_exception: object,
    validation_boundary: object,
    externally_supplied_sentinel_rng_state_sha256_before: object,
    externally_supplied_sentinel_rng_state_sha256_after: object,
    rng_factory_call_count: object,
    result_artifact_created: object,
) -> DeterministicRefusalObservationV1:
    """Compare one supplied refusal observation with a frozen expectation.

    This consumes an externally observed exception and unrelated sentinel
    custody data.  It does not call the malformed boundary, construct an RNG,
    or authenticate the supplied digests.  Matching values do not verify
    boundary-invocation provenance, sentinel provenance, cryptographic
    authenticity, or runner execution.
    """

    checked_table = _validate_refusal_table(table)
    checked_case_id = _text(case_id, "T28-INVALID observed case identifier", 128)
    matches = tuple(
        case for case in checked_table.cases if case.case_id == checked_case_id
    )
    if len(matches) != 1:
        raise ValueError("T28-INVALID observed case identifier is unknown")
    case = matches[0]
    qualname = _exception_qualname(observed_exception, case.expected_exception_qualname)
    message = str(observed_exception)
    if type(message) is not str or message != case.expected_exception_message:
        raise ValueError("observed exception message differs from the frozen case")
    boundary = _text(validation_boundary, "observed validation boundary")
    if boundary != case.validation_boundary:
        raise ValueError("observed validation boundary differs from the frozen case")
    before = _rng_state_tuple(
        externally_supplied_sentinel_rng_state_sha256_before,
        "external sentinel RNG states before",
    )
    after = _rng_state_tuple(
        externally_supplied_sentinel_rng_state_sha256_after,
        "external sentinel RNG states after",
    )
    if before != after:
        raise ValueError("external sentinel RNG states differ")
    factory_calls = _integer(
        rng_factory_call_count, "observed RNG factory call count", 0, 0
    )
    if type(result_artifact_created) is not bool:
        raise TypeError("result_artifact_created must be an exact Boolean")
    if result_artifact_created:
        raise ValueError("observed refusal created a result artifact")
    values = {
        "schema_version": CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION,
        "fixture_id": CP57_TEST28_INVALID_FIXTURE_ID,
        "table_record_sha256": checked_table.record_sha256,
        "case_id": case.case_id,
        "case_record_sha256": case.record_sha256,
        "validation_boundary": boundary,
        "expectation_scope": case.expectation_scope,
        "observed_exception_qualname": qualname,
        "observed_exception_message": message,
        "owned_rng_roles_not_constructed": _OWNED_RNG_ROLES,
        "externally_supplied_sentinel_rng_state_sha256_before": before,
        "externally_supplied_sentinel_rng_state_sha256_after": after,
        "rng_factory_call_count": factory_calls,
        "result_artifact_created": False,
        "supplied_exception_matches_frozen_expectation": True,
        "externally_supplied_sentinel_rng_state_digests_byte_identical": True,
        "supplied_observation_matches_frozen_expectation": True,
        "case_expectation_is_production_preflight": (
            case.expectation_scope == "production-preflight"
        ),
        "exact_exception_class_identity_checked": True,
        "builtin_value_error_identity_checked": (
            case.expected_exception_qualname == "builtins.ValueError"
        ),
        "production_unsupported_reference_error_identity_checked": (
            case.expected_exception_qualname
            == "heterodiff.theory.configuration_reference."
            "UnsupportedReferenceSamplingError"
        ),
        "boundary_invocation_provenance_verified": False,
        "sentinel_rng_state_digest_provenance_verified": False,
        "cryptographic_authentication": False,
        "production_runner_evidence": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
        "record_sha256": _ZERO_SHA256,
    }
    provisional = _construct_record(DeterministicRefusalObservationV1, values)
    values["record_sha256"] = _digest("invalid-observation", provisional)
    return _validate_refusal_observation(
        _construct_record(DeterministicRefusalObservationV1, values),
        table=checked_table,
    )


def _validate_bundle(record: object) -> Test28StressRefusalOracleBundleV1:
    if type(record) is not Test28StressRefusalOracleBundleV1:
        raise TypeError("CP57 stress/refusal bundle has the wrong exact type")
    if _text(record.schema_version, "CP57 bundle schema") != (
        CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION
    ):
        raise ValueError("CP57 bundle schema differs")
    if _text(record.scope, "CP57 bundle scope") != CP57_TEST28_STRESS_REFUSAL_SCOPE:
        raise ValueError("CP57 bundle scope differs")
    aess = _validate_aess_oracle(record.aess_oracle)
    table = _validate_refusal_table(record.invalid_refusal_table)
    _sha256(record.aess_record_sha256, "CP57 bundle AESS digest")
    _sha256(
        record.invalid_refusal_table_record_sha256,
        "CP57 bundle INVALID digest",
    )
    if record.aess_record_sha256 != aess.record_sha256:
        raise ValueError("CP57 bundle AESS digest differs")
    if record.invalid_refusal_table_record_sha256 != table.record_sha256:
        raise ValueError("CP57 bundle INVALID digest differs")
    expected_flags = {
        "subrecord_digests_distinct": aess.record_sha256 != table.record_sha256,
        "source_law_verified": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
    }
    for name, expected in expected_flags.items():
        supplied = getattr(record, name)
        if type(supplied) is not bool or supplied is not expected:
            raise ValueError("CP57 bundle flag " + name + " differs")
    _sha256(record.record_sha256, "CP57 bundle digest")
    if record.record_sha256 != _digest("stress-refusal-bundle", record):
        raise ValueError("CP57 bundle digest differs")
    return record


def t28_stress_refusal_oracle_bundle_v1() -> Test28StressRefusalOracleBundleV1:
    """Return the independently digested AESS oracle and INVALID table bundle."""

    aess = t28_aess_low_ess_oracle_v1()
    table = t28_invalid_refusal_table_v1()
    values = {
        "schema_version": CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION,
        "scope": CP57_TEST28_STRESS_REFUSAL_SCOPE,
        "aess_oracle": aess,
        "aess_record_sha256": aess.record_sha256,
        "invalid_refusal_table": table,
        "invalid_refusal_table_record_sha256": table.record_sha256,
        "subrecord_digests_distinct": aess.record_sha256 != table.record_sha256,
        "source_law_verified": False,
        "confirmatory_evidence": False,
        "formal_test28_evidence": False,
        "manuscript_claim": False,
        "record_sha256": _ZERO_SHA256,
    }
    provisional = _construct_record(Test28StressRefusalOracleBundleV1, values)
    values["record_sha256"] = _digest("stress-refusal-bundle", provisional)
    return _validate_bundle(
        _construct_record(Test28StressRefusalOracleBundleV1, values)
    )


def validate_t28_stress_refusal_oracle_bundle_v1(
    record: object,
) -> Test28StressRefusalOracleBundleV1:
    """Structurally validate the combined CP57 custody root."""

    return _validate_bundle(record)


__all__ = (
    "CP57_TEST28_STRESS_REFUSAL_SCHEMA_VERSION",
    "CP57_TEST28_AESS_FIXTURE_ID",
    "CP57_TEST28_INVALID_FIXTURE_ID",
    "CP57_TEST28_AESS_FORMULA_ID",
    "CP57_TEST28_INVALID_TABLE_ID",
    "CP57_TEST28_STRESS_REFUSAL_SCOPE",
    "CP57_TEST28_STRESS_REFUSAL_NONCLAIMS",
    "AtomicLowESSDiagnosticV1",
    "AtomicLowESSOracleV1",
    "DeterministicRefusalCaseV1",
    "DeterministicRefusalTableV1",
    "DeterministicRefusalObservationV1",
    "Test28StressRefusalOracleBundleV1",
    "t28_aess_low_ess_oracle_v1",
    "validate_t28_aess_low_ess_oracle_v1",
    "t28_invalid_refusal_table_v1",
    "validate_t28_invalid_refusal_table_v1",
    "verify_t28_invalid_refusal_observation_v1",
    "t28_stress_refusal_oracle_bundle_v1",
    "validate_t28_stress_refusal_oracle_bundle_v1",
)
