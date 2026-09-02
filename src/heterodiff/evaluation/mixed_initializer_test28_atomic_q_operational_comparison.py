"""CP56 operational comparison for the Test-28 ``T28-A0-Q`` fixture.

This module binds one already-executed kernel-v2 finite-atomic enumeration to
the CP55 direct-score oracle.  The kernel result is the deterministic float64
categorical-weight record ``P_enum^{kernel,b64}`` obtained by tilting the
``finite_atomic_oracle`` mass vector ``P_ref^{oracle,b64}``.  It is compared,
after an exact count-vector remapping, with the CP55 stored-parameter analytic
interval target ``Pi_A0Q^{b64}``.

The comparison embeds every binary64 value as its exact :class:`Fraction` and
reports signed discrepancy intervals and a rigorous half-L1 enclosure.  The
kernel vector has a nonzero exact mass residual, so the half-L1 quantity is not
called total variation.  Validation is structural: it does not execute the
kernel, call either score-provider ``evaluate`` method, replay randomness, or
call the reference sampler.  This artifact does not identify an operational
source law, prove equality to the analytic target, authorize Formal Test 28,
or establish a manuscript result.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import json
import math
import struct
from typing import Dict, Mapping, Tuple

from heterodiff.evaluation import mixed_initializer_test28_atomic_q_oracle as _oracle
from heterodiff.evaluation.mixed_initializer_test28_atomic_q_oracle import (
    AtomicQOraclePair,
    AtomicQScoreEvaluation,
    ClosedRationalInterval,
)
from heterodiff.processes import certified_initial_score_provider_v1 as _score
from heterodiff.processes import (
    plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as _kernel,
)
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
)


CP56_TEST28_ATOMIC_Q_COMPARISON_SCHEMA_VERSION = (
    "cp56-test28-atomic-q-operational-comparison-v1"
)
CP56_TEST28_ATOMIC_Q_BASE_LAW = "P_ref^{oracle,b64}"
CP56_TEST28_ATOMIC_Q_OUTPUT_RECORD = "P_enum^{kernel,b64}"
CP56_TEST28_ATOMIC_Q_ANALYTIC_COMPARATOR = "Pi_A0Q^{b64}"
CP56_TEST28_ATOMIC_Q_SCOPE = (
    "one-cp55-t28-a0-q-score-table-through-the-common-certified-score-facade;"
    "one-generic-kernel-v2-finite-atomic-enumeration;exact-count-vector-keyed-"
    "runtime-to-protocol-remapping;exact-binary64-embeddings;float-sum-residual;"
    "signed-and-absolute-output-minus-analytic-intervals;rigorous-half-l1-"
    "enclosure;structural-validation-without-execute-provider-evaluate-rng-or-"
    "reference-sampler-replay;not-source-law-target-equality-categorical-draw-"
    "confirmatory-formal-test28-or-manuscript-evidence"
)
CP56_TEST28_ATOMIC_Q_NONCLAIM = (
    "the finite_atomic_oracle binary64 mass vector is not identified with an "
    "operational reference-sampler law",
    "the kernel float64 categorical-weight record is not asserted equal to the "
    "CP55 stored-parameter analytic target",
    "the half-L1 enclosure is not called total variation because the exact sum "
    "of the stored float64 output vector differs from one",
    "no categorical draw, RNG law, IID law, confirmatory execution, Formal "
    "Test 28 closure, or manuscript claim is established",
)
CP56_TEST28_ATOMIC_Q_ADAPTER_ROLE_SHA256 = hashlib.sha256(
    b"cp56-t28-a0-q-certified-score-table-adapter-v1"
).hexdigest()
CP56_TEST28_ATOMIC_Q_INITIALIZER_ROLE_SHA256 = hashlib.sha256(
    b"cp56-t28-a0-q-finite-atomic-enumeration-v1"
).hexdigest()
CP56_TEST28_ATOMIC_Q_BASE_SUM_RESIDUAL = Fraction(11, 1 << 57)
CP56_TEST28_ATOMIC_Q_OUTPUT_SUM_RESIDUAL = Fraction(-1, 1 << 57)

MAX_CP56_EXACT_INTEGER_BITS = 32_768
MAX_CP56_TEXT_LENGTH = 4_096
_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_HALF = Fraction(1, 2)
_ZERO_SHA256 = "0" * 64
_CONSTRUCTION_TOKEN = object()
_OBJECT_FIELDS = ("oracle_pair", "kernel", "kernel_result")


def _text(value: object, name: str, maximum: int = MAX_CP56_TEXT_LENGTH) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value) > maximum:
        raise ValueError(name + " has invalid bounded length")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(name + " must contain printable ASCII only")
    return value


def _sha256(value: object, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return value


def _fraction(value: object, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if (
        max(value.numerator.bit_length(), value.denominator.bit_length())
        > MAX_CP56_EXACT_INTEGER_BITS
    ):
        raise ValueError(name + " exceeds the exact-integer bit bound")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact non-boolean integer")
    if not minimum <= value <= maximum:
        raise ValueError(name + " lies outside its bounded domain")
    return value


def _same_float(left: object, right: object) -> bool:
    return (
        type(left) is float
        and type(right) is float
        and struct.pack(">d", left) == struct.pack(">d", right)
    )


def _exact_float(value: object, name: str) -> float:
    if type(value) is not float or not math.isfinite(value):
        raise TypeError(name + " must be a finite built-in float")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(name + " must use canonical positive zero")
    return value


def _exact_tuple(value: object, name: str, length: int) -> tuple:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) != length:
        raise ValueError(name + " has the wrong frozen length")
    return value


def _canonical(value: object) -> object:
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-hex-v1", ("-" + hex(-value)) if value < 0 else hex(value)]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is float:
        _exact_float(value, "canonical float")
        return ["binary64-v1", value.hex()]
    if type(value) is Fraction:
        _fraction(value, "canonical fraction")
        numerator = (
            "-" + hex(-value.numerator) if value.numerator < 0 else hex(value.numerator)
        )
        return ["fraction-hex-v1", numerator, hex(value.denominator)]
    if type(value) is tuple:
        return ["tuple-v1", [_canonical(item) for item in value]]
    if type(value) is ClosedRationalInterval:
        value.__post_init__()
        return [
            "closed-rational-interval-v1",
            _canonical(value.lower),
            _canonical(value.upper),
        ]
    raise TypeError("unsupported canonical value " + type(value).__name__)


def _semantic_digest(payload: Mapping[str, object], *, domain: bytes) -> str:
    if type(payload) is not dict:
        raise TypeError("digest payload must be an exact dict")
    if type(domain) is not bytes or not domain or len(domain) > 512:
        raise ValueError("digest domain is invalid")
    document = {
        "payload": [
            [_canonical(key), _canonical(payload[key])] for key in sorted(payload)
        ]
    }
    encoded = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(domain + encoded).hexdigest()


def _float_vector_sha256(values: Tuple[float, ...], *, law: str) -> str:
    checked = _exact_tuple(values, law + " values", 6)
    digest = hashlib.sha256(
        b"heterodiff-cp56-t28-a0-q-binary64-vector-v1\x00"
        + _text(law, "law", 128).encode("ascii")
        + b"\x00"
    )
    digest.update(len(checked).to_bytes(8, "big"))
    for index, value in enumerate(checked):
        digest.update(struct.pack(">d", _exact_float(value, law + "[%d]" % index)))
    return digest.hexdigest()


def _point_minus_interval(
    point: Fraction, interval: ClosedRationalInterval
) -> ClosedRationalInterval:
    point = _fraction(point, "binary64 point")
    if type(interval) is not ClosedRationalInterval:
        raise TypeError("analytic target entry must be an exact interval")
    interval.__post_init__()
    return ClosedRationalInterval(point - interval.upper, point - interval.lower)


def _absolute_interval(value: ClosedRationalInterval) -> ClosedRationalInterval:
    if type(value) is not ClosedRationalInterval:
        raise TypeError("absolute interval input has the wrong exact type")
    value.__post_init__()
    if value.lower >= 0:
        return value
    if value.upper <= 0:
        return ClosedRationalInterval(-value.upper, -value.lower)
    return ClosedRationalInterval(_ZERO, max(-value.lower, value.upper))


def _sum_intervals(
    values: Tuple[ClosedRationalInterval, ...]
) -> ClosedRationalInterval:
    lower = _ZERO
    upper = _ZERO
    for value in values:
        if type(value) is not ClosedRationalInterval:
            raise TypeError("interval sum contains a wrong exact type")
        value.__post_init__()
        lower += value.lower
        upper += value.upper
    return ClosedRationalInterval(lower, upper)


def _score_for_count(
    pair: AtomicQOraclePair, count_vector: Tuple[int, int]
) -> Fraction:
    """Look up one score by its exact count key, never by runtime position."""

    if type(count_vector) is not tuple:
        raise TypeError("count vector must be an exact tuple")
    try:
        protocol_index = pair.score_provider.count_vectors.index(count_vector)
    except ValueError as error:
        raise ValueError("runtime count vector is outside the CP55 table") from error
    return pair.score_provider.exact_scores[protocol_index]


def _derive_semantic_fields(
    oracle_pair: AtomicQOraclePair,
    kernel: _kernel.MixedSupportInitialTiltInitializerKernelV2,
    kernel_result: _kernel.MixedSupportInitialTiltEnumerationResultV2,
) -> Dict[str, object]:
    pair = _oracle.validate_t28_a0_q_oracle_pair(oracle_pair)
    if type(kernel) is not _kernel.MixedSupportInitialTiltInitializerKernelV2:
        raise TypeError("kernel has the wrong exact kernel-v2 type")
    if type(kernel_result) is not _kernel.MixedSupportInitialTiltEnumerationResultV2:
        raise TypeError("kernel result has the wrong exact enumeration type")
    provider = kernel.provider
    result = kernel.validate_result(kernel_result)
    certificate = kernel.certificate
    provider_certificate = provider.certificate
    if certificate.strategy != "finite-atomic-enumeration":
        raise ValueError("T28-A0-Q comparison requires finite-atomic enumeration")
    if result.certificate is not certificate:
        raise ValueError("enumeration result belongs to another kernel certificate")
    if provider_certificate.backend_kind != "atomic-q-score-table-v1":
        raise ValueError("comparison requires the exact atomic score-table backend")
    if (
        provider_certificate.adapter_role_sha256
        != CP56_TEST28_ATOMIC_Q_ADAPTER_ROLE_SHA256
    ):
        raise ValueError("atomic score-table adapter role differs from CP56")
    if (
        kernel.plan.initializer_role_sha256
        != CP56_TEST28_ATOMIC_Q_INITIALIZER_ROLE_SHA256
    ):
        raise ValueError("initializer role differs from CP56")
    if not isinstance(provider.backend_adapter, _score.AtomicQScoreTableAdapterV1):
        raise TypeError("comparison requires the sealed atomic score-table adapter")
    if type(provider.backend_adapter) is not _score.AtomicQScoreTableAdapterV1:
        raise TypeError("atomic score-table adapter subclasses are forbidden")
    if provider.backend_adapter.source is not pair.score_provider:
        raise ValueError("atomic adapter source is not the supplied CP55 score table")

    protocol_counts = pair.score_provider.count_vectors
    runtime_atoms_by_count = {}
    runtime_counts_list = []
    runtime_source_evaluation_sha256s = []
    runtime_exact_scores = []
    for atom in result.atoms:
        count_state = atom.count_state
        if type(count_state) is not tuple or len(count_state) != 2:
            raise TypeError("runtime count state has the wrong exact structure")
        if count_state in runtime_atoms_by_count:
            raise ValueError("runtime enumeration contains a duplicate count state")
        source_evaluation = atom.scored.evaluation.source_evaluation
        if type(source_evaluation) is not AtomicQScoreEvaluation:
            raise TypeError("atomic source point has the wrong exact CP55 type")
        if source_evaluation.count_vector != count_state:
            raise ValueError("source score was not looked up by its count state")
        expected_score = _score_for_count(pair, count_state)
        if (
            source_evaluation.exact_score != expected_score
            or atom.scored.exact_log_weight != expected_score
        ):
            raise ValueError("runtime count-keyed score differs from CP55")
        runtime_atoms_by_count[count_state] = atom
        runtime_counts_list.append(count_state)
        runtime_source_evaluation_sha256s.append(source_evaluation.record_sha256)
        runtime_exact_scores.append(expected_score)

    runtime_counts = tuple(runtime_counts_list)
    if len(runtime_atoms_by_count) != len(protocol_counts) or set(
        runtime_atoms_by_count
    ) != set(protocol_counts):
        raise ValueError("runtime and protocol count supports differ")
    protocol_index_by_count = {
        count: index for index, count in enumerate(protocol_counts)
    }
    runtime_to_protocol = tuple(
        protocol_index_by_count[count] for count in runtime_counts
    )
    if runtime_to_protocol != pair.score_provider.runtime_to_protocol_permutation:
        raise ValueError("runtime-to-protocol count permutation differs from CP55")

    runtime_base = tuple(float(value) for value in result.base_masses)
    runtime_output = tuple(float(value) for value in result.normalized_probabilities)
    protocol_base = tuple(
        float(runtime_atoms_by_count[count].base_mass) for count in protocol_counts
    )
    protocol_output = tuple(
        float(runtime_atoms_by_count[count].normalized_probability)
        for count in protocol_counts
    )
    protocol_base_exact = tuple(Fraction.from_float(value) for value in protocol_base)
    protocol_output_exact = tuple(
        Fraction.from_float(value) for value in protocol_output
    )
    base_sum = sum(protocol_base_exact, _ZERO)
    output_sum = sum(protocol_output_exact, _ZERO)
    if base_sum - _ONE != CP56_TEST28_ATOMIC_Q_BASE_SUM_RESIDUAL:
        raise ArithmeticError("finite-atomic base float-sum residual differs from CP56")
    if output_sum - _ONE != CP56_TEST28_ATOMIC_Q_OUTPUT_SUM_RESIDUAL:
        raise ArithmeticError("kernel output float-sum residual differs from CP56")
    analytic = pair.binary64_parameter
    base_signed = tuple(
        protocol_base_exact[index] - analytic.normalized_base_masses[index]
        for index in range(6)
    )
    base_half_l1 = _HALF * sum((abs(value) for value in base_signed), _ZERO)
    output_signed = tuple(
        _point_minus_interval(
            protocol_output_exact[index], analytic.target_probability_intervals[index]
        )
        for index in range(6)
    )
    output_absolute = tuple(_absolute_interval(value) for value in output_signed)
    absolute_sum = _sum_intervals(output_absolute)
    half_l1 = ClosedRationalInterval(
        _HALF * absolute_sum.lower, _HALF * absolute_sum.upper
    )

    return {
        "schema_version": CP56_TEST28_ATOMIC_Q_COMPARISON_SCHEMA_VERSION,
        "fixture_id": _oracle.CP55_TEST28_ATOMIC_Q_FIXTURE_ID,
        "scope": CP56_TEST28_ATOMIC_Q_SCOPE,
        "nonclaims": CP56_TEST28_ATOMIC_Q_NONCLAIM,
        "base_law": CP56_TEST28_ATOMIC_Q_BASE_LAW,
        "output_record": CP56_TEST28_ATOMIC_Q_OUTPUT_RECORD,
        "analytic_comparator": CP56_TEST28_ATOMIC_Q_ANALYTIC_COMPARATOR,
        "oracle_pair_record_sha256": pair.record_sha256,
        "score_table_record_sha256": pair.score_provider.record_sha256,
        "analytic_layer_record_sha256": analytic.record_sha256,
        "adapter_role_sha256": provider_certificate.adapter_role_sha256,
        "initializer_role_sha256": kernel.plan.initializer_role_sha256,
        "provider_certificate_sha256": provider_certificate.certificate_sha256,
        "reference_parameter_sha256": provider_certificate.reference_parameter_sha256,
        "kernel_certificate_sha256": certificate.certificate_sha256,
        "kernel_result_sha256": result.result_sha256,
        "protocol_count_vectors": protocol_counts,
        "runtime_count_vectors": runtime_counts,
        "runtime_to_protocol_permutation": runtime_to_protocol,
        "runtime_exact_scores": tuple(runtime_exact_scores),
        "runtime_source_evaluation_sha256s": tuple(runtime_source_evaluation_sha256s),
        "runtime_base_masses_binary64": runtime_base,
        "protocol_base_masses_binary64": protocol_base,
        "runtime_output_weights_binary64": runtime_output,
        "protocol_output_weights_binary64": protocol_output,
        "runtime_base_masses_sha256": _float_vector_sha256(
            runtime_base, law="runtime-base"
        ),
        "protocol_base_masses_sha256": _float_vector_sha256(
            protocol_base, law="protocol-base"
        ),
        "runtime_output_weights_sha256": _float_vector_sha256(
            runtime_output, law="runtime-output"
        ),
        "protocol_output_weights_sha256": _float_vector_sha256(
            protocol_output, law="protocol-output"
        ),
        "represented_log_normalizer_float64": float(
            result.represented_log_normalizer_float64
        ),
        "exact_base_mass_sum": base_sum,
        "exact_base_mass_sum_residual": base_sum - _ONE,
        "base_minus_analytic_exact_discrepancies": base_signed,
        "base_half_l1_discrepancy": base_half_l1,
        "exact_output_weight_sum": output_sum,
        "exact_output_weight_sum_residual": output_sum - _ONE,
        "signed_output_weight_minus_analytic_intervals": output_signed,
        "absolute_output_weight_minus_analytic_intervals": output_absolute,
        "half_l1_discrepancy_interval": half_l1,
        "count_keyed_source_lookup_verified": True,
        "runtime_to_protocol_remapping_verified": True,
        "facade_adapter_integration_verified": True,
        "kernel_v2_enumeration_integration_verified": True,
        "structural_kernel_validation_without_execution": True,
        "structural_validation_replayed_provider_evaluate": False,
        "structural_validation_replayed_rng": False,
        "structural_validation_replayed_reference_sampler": False,
        "exact_output_probability_measure_verified": False,
        "half_l1_is_total_variation": False,
        "operational_reference_source_law_verified": False,
        "analytic_target_equality_verified": False,
        "categorical_draw_executed": False,
        "formal_test_28_closed": False,
        "confirmatory_evidence": False,
        "manuscript_claim": False,
        "semantic_digest_excludes_runtime_instance_digests": True,
        "semantic_digest_fresh_construction_stable": True,
        "semantic_digest_cross_process_stable_under_identical_runtime_and_float_outputs": True,
        "semantic_digest_runtime_portable": False,
        "runtime_instance_digests_bound": True,
        "instance_custody_digest_cross_process_stable": False,
        "cryptographic_authentication": False,
        "runtime_portable": False,
    }


@dataclass(frozen=True, eq=False, init=False)
class AtomicQOperationalComparisonV1:
    oracle_pair: AtomicQOraclePair
    kernel: _kernel.MixedSupportInitialTiltInitializerKernelV2
    kernel_result: _kernel.MixedSupportInitialTiltEnumerationResultV2
    schema_version: str
    fixture_id: str
    scope: str
    nonclaims: Tuple[str, ...]
    base_law: str
    output_record: str
    analytic_comparator: str
    oracle_pair_record_sha256: str
    score_table_record_sha256: str
    analytic_layer_record_sha256: str
    adapter_role_sha256: str
    initializer_role_sha256: str
    provider_certificate_sha256: str
    reference_parameter_sha256: str
    kernel_certificate_sha256: str
    kernel_result_sha256: str
    protocol_count_vectors: Tuple[Tuple[int, int], ...]
    runtime_count_vectors: Tuple[Tuple[int, int], ...]
    runtime_to_protocol_permutation: Tuple[int, ...]
    runtime_exact_scores: Tuple[Fraction, ...]
    runtime_source_evaluation_sha256s: Tuple[str, ...]
    runtime_base_masses_binary64: Tuple[float, ...]
    protocol_base_masses_binary64: Tuple[float, ...]
    runtime_output_weights_binary64: Tuple[float, ...]
    protocol_output_weights_binary64: Tuple[float, ...]
    runtime_base_masses_sha256: str
    protocol_base_masses_sha256: str
    runtime_output_weights_sha256: str
    protocol_output_weights_sha256: str
    represented_log_normalizer_float64: float
    exact_base_mass_sum: Fraction
    exact_base_mass_sum_residual: Fraction
    base_minus_analytic_exact_discrepancies: Tuple[Fraction, ...]
    base_half_l1_discrepancy: Fraction
    exact_output_weight_sum: Fraction
    exact_output_weight_sum_residual: Fraction
    signed_output_weight_minus_analytic_intervals: Tuple[ClosedRationalInterval, ...]
    absolute_output_weight_minus_analytic_intervals: Tuple[ClosedRationalInterval, ...]
    half_l1_discrepancy_interval: ClosedRationalInterval
    count_keyed_source_lookup_verified: bool
    runtime_to_protocol_remapping_verified: bool
    facade_adapter_integration_verified: bool
    kernel_v2_enumeration_integration_verified: bool
    structural_kernel_validation_without_execution: bool
    structural_validation_replayed_provider_evaluate: bool
    structural_validation_replayed_rng: bool
    structural_validation_replayed_reference_sampler: bool
    exact_output_probability_measure_verified: bool
    half_l1_is_total_variation: bool
    operational_reference_source_law_verified: bool
    analytic_target_equality_verified: bool
    categorical_draw_executed: bool
    formal_test_28_closed: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    semantic_digest_excludes_runtime_instance_digests: bool
    semantic_digest_fresh_construction_stable: bool
    semantic_digest_cross_process_stable_under_identical_runtime_and_float_outputs: bool
    semantic_digest_runtime_portable: bool
    runtime_instance_digests_bound: bool
    instance_custody_digest_cross_process_stable: bool
    cryptographic_authentication: bool
    runtime_portable: bool
    semantic_comparison_sha256: str
    instance_custody_sha256: str

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CONSTRUCTION_TOKEN:
            raise TypeError("operational comparisons require the public builder")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational comparison fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_comparison(self)

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("operational comparison records cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("operational comparison records are not pickle objects")

    def __reduce_ex__(self, protocol: object) -> object:
        del protocol
        raise TypeError("operational comparison records are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            CP56_TEST28_ATOMIC_Q_COMPARISON_SCHEMA_VERSION,
            self.oracle_pair_record_sha256,
            self.provider_certificate_sha256,
            self.semantic_comparison_sha256,
        )

    def runtime_instance_key(self) -> Tuple[object, ...]:
        return (
            "cp56-t28-a0-q-runtime-instance-v1",
            self.kernel_certificate_sha256,
            self.kernel_result_sha256,
            self.instance_custody_sha256,
        )


def _comparison_payload(value: AtomicQOperationalComparisonV1) -> Dict[str, object]:
    return {
        field.name: getattr(value, field.name)
        for field in fields(AtomicQOperationalComparisonV1)
        if field.name not in _OBJECT_FIELDS and field.name != "instance_custody_sha256"
    }


def _instance_custody_sha256(value: AtomicQOperationalComparisonV1) -> str:
    return _semantic_digest(
        _comparison_payload(value),
        domain=b"heterodiff-cp56-t28-a0-q-instance-custody-v1\x00",
    )


def _semantic_comparison_payload(
    value: AtomicQOperationalComparisonV1,
) -> Dict[str, object]:
    excluded = {
        "kernel_certificate_sha256",
        "kernel_result_sha256",
        "semantic_comparison_sha256",
        "instance_custody_sha256",
    }
    return {
        field.name: getattr(value, field.name)
        for field in fields(AtomicQOperationalComparisonV1)
        if field.name not in _OBJECT_FIELDS and field.name not in excluded
    }


def _semantic_comparison_sha256(value: AtomicQOperationalComparisonV1) -> str:
    return _semantic_digest(
        _semantic_comparison_payload(value),
        domain=b"heterodiff-cp56-t28-a0-q-semantic-comparison-v1\x00",
    )


def _validate_count_vector_tuple(value: object, name: str) -> None:
    rows = _exact_tuple(value, name, 6)
    for row_index, row in enumerate(rows):
        entries = _exact_tuple(row, "%s[%d]" % (name, row_index), 2)
        for column_index, entry in enumerate(entries):
            _integer(
                entry,
                "%s[%d][%d]" % (name, row_index, column_index),
                0,
                2,
            )


def _validate_fraction_tuple(value: object, name: str) -> None:
    entries = _exact_tuple(value, name, 6)
    for index, entry in enumerate(entries):
        _fraction(entry, "%s[%d]" % (name, index))


def _validate_float_tuple(value: object, name: str) -> None:
    entries = _exact_tuple(value, name, 6)
    for index, entry in enumerate(entries):
        _exact_float(entry, "%s[%d]" % (name, index))


def _validate_interval_tuple(value: object, name: str) -> None:
    entries = _exact_tuple(value, name, 6)
    for index, entry in enumerate(entries):
        if type(entry) is not ClosedRationalInterval:
            raise TypeError("%s[%d] has the wrong exact interval type" % (name, index))
        _fraction(entry.lower, "%s[%d].lower" % (name, index))
        _fraction(entry.upper, "%s[%d].upper" % (name, index))
        entry.__post_init__()


def _prevalidate_comparison_fields(value: AtomicQOperationalComparisonV1) -> None:
    """Reject hostile or oversized fields before any semantic equality."""

    if type(value.oracle_pair) is not AtomicQOraclePair:
        raise TypeError("comparison oracle_pair has the wrong exact type")
    if type(value.kernel) is not _kernel.MixedSupportInitialTiltInitializerKernelV2:
        raise TypeError("comparison kernel has the wrong exact type")
    if (
        type(value.kernel_result)
        is not _kernel.MixedSupportInitialTiltEnumerationResultV2
    ):
        raise TypeError("comparison kernel_result has the wrong exact type")
    for name in (
        "schema_version",
        "fixture_id",
        "scope",
        "base_law",
        "output_record",
        "analytic_comparator",
    ):
        _text(getattr(value, name), "comparison." + name)
    nonclaims = _exact_tuple(value.nonclaims, "comparison.nonclaims", 4)
    for index, nonclaim in enumerate(nonclaims):
        _text(nonclaim, "comparison.nonclaims[%d]" % index)
    for name in (
        "oracle_pair_record_sha256",
        "score_table_record_sha256",
        "analytic_layer_record_sha256",
        "adapter_role_sha256",
        "initializer_role_sha256",
        "provider_certificate_sha256",
        "reference_parameter_sha256",
        "kernel_certificate_sha256",
        "kernel_result_sha256",
        "runtime_base_masses_sha256",
        "protocol_base_masses_sha256",
        "runtime_output_weights_sha256",
        "protocol_output_weights_sha256",
        "semantic_comparison_sha256",
        "instance_custody_sha256",
    ):
        _sha256(getattr(value, name), "comparison." + name)
    _validate_count_vector_tuple(
        value.protocol_count_vectors, "comparison.protocol_count_vectors"
    )
    _validate_count_vector_tuple(
        value.runtime_count_vectors, "comparison.runtime_count_vectors"
    )
    permutation = _exact_tuple(
        value.runtime_to_protocol_permutation,
        "comparison.runtime_to_protocol_permutation",
        6,
    )
    for index, entry in enumerate(permutation):
        _integer(
            entry,
            "comparison.runtime_to_protocol_permutation[%d]" % index,
            0,
            5,
        )
    _validate_fraction_tuple(
        value.runtime_exact_scores, "comparison.runtime_exact_scores"
    )
    source_digests = _exact_tuple(
        value.runtime_source_evaluation_sha256s,
        "comparison.runtime_source_evaluation_sha256s",
        6,
    )
    for index, digest in enumerate(source_digests):
        _sha256(
            digest,
            "comparison.runtime_source_evaluation_sha256s[%d]" % index,
        )
    for name in (
        "runtime_base_masses_binary64",
        "protocol_base_masses_binary64",
        "runtime_output_weights_binary64",
        "protocol_output_weights_binary64",
    ):
        _validate_float_tuple(getattr(value, name), "comparison." + name)
    _exact_float(
        value.represented_log_normalizer_float64,
        "comparison.represented_log_normalizer_float64",
    )
    for name in (
        "exact_base_mass_sum",
        "exact_base_mass_sum_residual",
        "base_half_l1_discrepancy",
        "exact_output_weight_sum",
        "exact_output_weight_sum_residual",
    ):
        _fraction(getattr(value, name), "comparison." + name)
    _validate_fraction_tuple(
        value.base_minus_analytic_exact_discrepancies,
        "comparison.base_minus_analytic_exact_discrepancies",
    )
    _validate_interval_tuple(
        value.signed_output_weight_minus_analytic_intervals,
        "comparison.signed_output_weight_minus_analytic_intervals",
    )
    _validate_interval_tuple(
        value.absolute_output_weight_minus_analytic_intervals,
        "comparison.absolute_output_weight_minus_analytic_intervals",
    )
    if type(value.half_l1_discrepancy_interval) is not ClosedRationalInterval:
        raise TypeError("comparison half-L1 interval has the wrong exact type")
    _fraction(
        value.half_l1_discrepancy_interval.lower,
        "comparison.half_l1_discrepancy_interval.lower",
    )
    _fraction(
        value.half_l1_discrepancy_interval.upper,
        "comparison.half_l1_discrepancy_interval.upper",
    )
    value.half_l1_discrepancy_interval.__post_init__()
    for name in (
        "count_keyed_source_lookup_verified",
        "runtime_to_protocol_remapping_verified",
        "facade_adapter_integration_verified",
        "kernel_v2_enumeration_integration_verified",
        "structural_kernel_validation_without_execution",
        "structural_validation_replayed_provider_evaluate",
        "structural_validation_replayed_rng",
        "structural_validation_replayed_reference_sampler",
        "exact_output_probability_measure_verified",
        "half_l1_is_total_variation",
        "operational_reference_source_law_verified",
        "analytic_target_equality_verified",
        "categorical_draw_executed",
        "formal_test_28_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "semantic_digest_excludes_runtime_instance_digests",
        "semantic_digest_fresh_construction_stable",
        "semantic_digest_cross_process_stable_under_identical_runtime_and_float_outputs",
        "semantic_digest_runtime_portable",
        "runtime_instance_digests_bound",
        "instance_custody_digest_cross_process_stable",
        "cryptographic_authentication",
        "runtime_portable",
    ):
        if type(getattr(value, name)) is not bool:
            raise TypeError("comparison.%s must be an exact Boolean" % name)


def _validate_comparison(
    value: object,
) -> AtomicQOperationalComparisonV1:
    if type(value) is not AtomicQOperationalComparisonV1:
        raise TypeError("comparison has the wrong exact CP56 type")
    _prevalidate_comparison_fields(value)
    expected = _derive_semantic_fields(
        value.oracle_pair, value.kernel, value.kernel_result
    )
    for name, wanted in expected.items():
        supplied = getattr(value, name)
        if type(wanted) is float:
            matches = _same_float(supplied, wanted)
        else:
            matches = type(supplied) is type(wanted) and supplied == wanted
        if not matches:
            raise ValueError("comparison field %s differs" % name)
    if value.semantic_comparison_sha256 != _semantic_comparison_sha256(value):
        raise ValueError("semantic comparison digest differs")
    _sha256(value.instance_custody_sha256, "comparison instance-custody digest")
    if value.instance_custody_sha256 != _instance_custody_sha256(value):
        raise ValueError("comparison instance-custody digest differs")
    return value


def compare_t28_a0_q_kernel_enumeration_v1(
    oracle_pair: AtomicQOraclePair,
    kernel: _kernel.MixedSupportInitialTiltInitializerKernelV2,
    kernel_result: _kernel.MixedSupportInitialTiltEnumerationResultV2,
) -> AtomicQOperationalComparisonV1:
    """Bind an existing exact A0-Q kernel enumeration without re-executing it."""

    semantic = _derive_semantic_fields(oracle_pair, kernel, kernel_result)
    values = {
        "oracle_pair": oracle_pair,
        "kernel": kernel,
        "kernel_result": kernel_result,
        **semantic,
        "semantic_comparison_sha256": _ZERO_SHA256,
        "instance_custody_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(AtomicQOperationalComparisonV1)
    for name in AtomicQOperationalComparisonV1.__annotations__:
        object.__setattr__(provisional, name, values[name])
    values["semantic_comparison_sha256"] = _semantic_comparison_sha256(provisional)
    object.__setattr__(
        provisional,
        "semantic_comparison_sha256",
        values["semantic_comparison_sha256"],
    )
    values["instance_custody_sha256"] = _instance_custody_sha256(provisional)
    return AtomicQOperationalComparisonV1(
        **values, _construction_token=_CONSTRUCTION_TOKEN
    )


def t28_a0_q_operational_comparison_v1() -> AtomicQOperationalComparisonV1:
    """Execute the canonical deterministic CP56 enumeration once and compare it."""

    pair = _oracle.t28_a0_q_oracle_pair()
    reference = CappedPoissonConfigurationReference(
        {0: 0, 1: 0},
        {0: 0.4, 1: 0.6},
        activity=1.0,
        total_cap=2,
    )
    provider = _score.adapt_atomic_q_score_table_provider_v1(
        pair.score_provider,
        reference=reference,
        adapter_role_sha256=CP56_TEST28_ATOMIC_Q_ADAPTER_ROLE_SHA256,
    )
    plan = _kernel.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy="finite-atomic-enumeration",
        residual_context=(),
        initializer_role_sha256=CP56_TEST28_ATOMIC_Q_INITIALIZER_ROLE_SHA256,
    )
    owner = _kernel.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    return compare_t28_a0_q_kernel_enumeration_v1(pair, owner, result)


def validate_t28_a0_q_operational_comparison_v1(
    value: AtomicQOperationalComparisonV1,
) -> AtomicQOperationalComparisonV1:
    """Structurally validate the retained comparison without execution replay."""

    return _validate_comparison(value)


def t28_a0_q_operational_semantic_sha256(
    value: AtomicQOperationalComparisonV1,
) -> str:
    """Return the stable semantic digest, excluding instance-local custody."""

    return validate_t28_a0_q_operational_comparison_v1(value).semantic_comparison_sha256


def t28_a0_q_operational_instance_custody_sha256(
    value: AtomicQOperationalComparisonV1,
) -> str:
    """Return the validated instance-local kernel/result custody digest."""

    return validate_t28_a0_q_operational_comparison_v1(value).instance_custody_sha256


__all__ = (
    "AtomicQOperationalComparisonV1",
    "CP56_TEST28_ATOMIC_Q_ADAPTER_ROLE_SHA256",
    "CP56_TEST28_ATOMIC_Q_ANALYTIC_COMPARATOR",
    "CP56_TEST28_ATOMIC_Q_BASE_SUM_RESIDUAL",
    "CP56_TEST28_ATOMIC_Q_BASE_LAW",
    "CP56_TEST28_ATOMIC_Q_COMPARISON_SCHEMA_VERSION",
    "CP56_TEST28_ATOMIC_Q_INITIALIZER_ROLE_SHA256",
    "CP56_TEST28_ATOMIC_Q_NONCLAIM",
    "CP56_TEST28_ATOMIC_Q_OUTPUT_RECORD",
    "CP56_TEST28_ATOMIC_Q_OUTPUT_SUM_RESIDUAL",
    "CP56_TEST28_ATOMIC_Q_SCOPE",
    "MAX_CP56_EXACT_INTEGER_BITS",
    "MAX_CP56_TEXT_LENGTH",
    "compare_t28_a0_q_kernel_enumeration_v1",
    "t28_a0_q_operational_instance_custody_sha256",
    "t28_a0_q_operational_comparison_v1",
    "t28_a0_q_operational_semantic_sha256",
    "validate_t28_a0_q_operational_comparison_v1",
)
