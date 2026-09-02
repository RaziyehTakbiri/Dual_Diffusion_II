"""Finite-resolution reference initialization from checkpoint-27 prefixes.

Checkpoint twenty-seven allocates fixed, uninterpreted tag-7 raw-word
prefixes.  This additive successor gives only the fixed-cost, no-retry
``reference`` strategy a deterministic interpretation.  For reference cap
``N`` and maximum fiber dimension ``D``, the exact fixed layout is

``1 + N * (1 + D)``

raw 64-bit words: one cardinality word, a contiguous segment of ``N`` type
words, and an ``N``-by-``D`` row-major coordinate segment.  Every raw slot's
type and all ``D`` coordinates are transformed before the cardinality word is
decoded.  Only afterward is the leading slot prefix marked active.  The
selected events are then canonicalized with a raw-slot tie break, so repeated
atomic events retain an unambiguous procedural provenance map.

Count and type categories use positive integer Hamilton quotas with exact
denominator ``2**64``.  A coordinate word retains its upper 53 bits and maps
that bucket through a symmetric midpoint normal quantile.  The midpoint is
strictly inside ``(0, 1)`` and the lower tail is used on both sides, avoiding
an inverse-CDF endpoint.  The resulting coordinate law is a same-runtime
finite codebook, not a continuous Gaussian.

Under a hypothetical product-uniform raw-word source, the output is exactly
the deterministic finite pushforward defined here.  The actual counter-keyed
Philox prefixes are procedural deterministic values: this module does not
certify their physical randomness, statistical independence, or equality to
the capped-Poisson continuous reference.  It also supplies no conditional or
tilted initializer, rejection/SIR semantics, lineage assignment, tag-3
payload coordination, Brownian motion, drift, path, or full sampler.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction
import math
import platform
import sys
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple

import numpy as np
import scipy
from scipy import special as _special

try:
    from heterodiff.models import (
        configuration_totalized_jump_potential_composer_torch as _potential,
    )
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initializer_protocol as _protocol,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "counter-keyed reference initialization requires the optional "
            "PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.processes.plugin_bridge_sampler import (
    ProcessValidReferenceJumpComposer,
)
from heterodiff.processes.reversible_hybrid_reference import (
    ReversibleHybridReference,
)
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    MAX_CONFIGURATION_EVENT_TYPES,
    MAX_TRANSFORMED_COORDINATE_DIMENSION,
    TransformedConfiguration,
    TransformedEvent,
)


PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-reference-initializer-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY = (
    "exact-checkpoint27-owner-and-result-binding;"
    "ancestry-derived-capped-poisson-reference-manifest;"
    "exact-rational-laws-induced-by-frozen-binary64-reference-parameters;"
    "bounded-hexadecimal-exact-rational-manifest-encoding;"
    "positive-dyadic-count-and-type-hamilton-quotas;"
    "fixed-count-type-max-dimension-word-layout;"
    "canonical-greedy-parent-block-partition;"
    "symmetric-top53-midpoint-normal-quantile-codebook;"
    "complete-raw-slot-transformation-before-cardinality-decoding;"
    "duplicate-stable-raw-slot-canonical-position-bijection;"
    "hypothetical-product-uniform-finite-pushforward;"
    "same-runtime-deterministic-replay;no-caller-rng-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCOPE = (
    "finite-resolution-fixed-cost-no-retry-reference-strategy-output;"
    "dyadic-quantization-of-exact-rational-parameter-induced-probabilities;"
    "finite-discrete-coordinate-codebook;"
    "not-exact-capped-poisson-or-continuous-gaussian-reference-law;"
    "not-quantitative-weak-wasserstein-or-full-configuration-tv-bound;"
    "not-actual-philox-uniformity-independence-or-physical-randomness;"
    "not-enumeration-rejection-sir-conditional-or-tilted-initialization;"
    "not-lineage-or-tag3-payload-coordination;"
    "not-brownian-drift-path-strang-liveness-or-full-sampler;"
    "not-analytic-target-stationarity-runtime-portability-or-authentication"
)
FINITE_RESOLUTION_REFERENCE_COORDINATE_TRANSFORM = (
    "upper53-bits;symmetric-lower-tail;"
    "p=(2r+1)/2^54;scipy-special-ndtri;binary64-output-v1"
)

COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS = 64
COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS = 53
COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS = 11
COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS = 64
COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES = 4_097
COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS = 131_072
COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS = 16_777_216

_DYADIC_DENOMINATOR = 1 << COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS
_COORDINATE_BUCKET_COUNT = (
    1 << COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS
)
_COORDINATE_HALF_BUCKET_COUNT = _COORDINATE_BUCKET_COUNT >> 1
_PARENT_CONTROL = _protocol._control
_PARENT_MAXIMUM_WORDS_PER_STREAM = (
    _PARENT_CONTROL.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
)
_PARENT_MAXIMUM_TOTAL_WORDS = (
    _PARENT_CONTROL.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS
)
_MANIFEST_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_SLOT_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()
_ZERO_SHA256 = "0" * 64


class PluginBridgeCounterKeyedReferenceInitializerError(ArithmeticError):
    """Fail-closed checkpoint-twenty-eight transformation error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    excluded = set(names)
    return {name: value for name, value in values.items() if name not in excluded}


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact bool" % name)
    return value


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    return value


def _bounded_exact_rational_integer(value: object, *, name: str) -> int:
    checked = _exact_nonnegative_integer(value, name=name)
    if (
        checked.bit_length()
        > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
    ):
        raise ValueError("%s exceeds the exact-rational integer-bit bound" % name)
    return checked


def _bounded_exact_tuple(
    value: object,
    *,
    name: str,
    maximum_items: int,
    exact_length: Optional[int] = None,
) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) > maximum_items:
        raise ValueError("%s exceeds its item bound" % name)
    if exact_length is not None and len(value) != exact_length:
        raise ValueError("%s has the wrong fixed length" % name)
    return value


def _reference_parameter_sha256(reference: CappedPoissonConfigurationReference) -> str:
    return _protocol._thinning._semantic_digest(
        {"reference_parameter_key": reference.parameter_key()}
    )


def _process_parameter_sha256(process: ReversibleHybridReference) -> str:
    return _potential._plain_key_sha256(
        process.parameter_key(),
        domain=b"heterodiff-totalized-jump-potential-process-v1\x00",
    )


def _coordinate_transform_details(
    raw_word: object,
) -> Tuple[int, int, str, float, str]:
    word = _protocol._lineage._exact_uint64(raw_word, name="coordinate raw word")
    bucket = word >> COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS
    if bucket < _COORDINATE_HALF_BUCKET_COUNT:
        reflected = bucket
        sign = -1.0
    else:
        reflected = _COORDINATE_BUCKET_COUNT - 1 - bucket
        sign = 1.0
    numerator = 2 * reflected + 1
    probability = math.ldexp(
        float(numerator),
        -(COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS + 1),
    )
    if not 0.0 < probability < 0.5:
        raise PluginBridgeCounterKeyedReferenceInitializerError(
            "coordinate midpoint is outside the strict lower tail"
        )
    magnitude = -float(_special.ndtri(probability))
    if (
        not math.isfinite(magnitude)
        or magnitude <= 0.0
        or magnitude < float(np.finfo(np.float64).tiny)
    ):
        raise PluginBridgeCounterKeyedReferenceInitializerError(
            "coordinate codebook magnitude is not positive normal binary64"
        )
    value = sign * magnitude
    if not math.isfinite(value) or (sign < 0.0) != (value < 0.0):
        raise PluginBridgeCounterKeyedReferenceInitializerError(
            "coordinate codebook value is not finite"
        )
    value = 0.0 if value == 0.0 else value
    return bucket, numerator, probability.hex(), value, value.hex()


def _canonical_word_blocks(total_words: object) -> Tuple[int, ...]:
    total = _exact_nonnegative_integer(total_words, name="total_words")
    if total == 0 or total > _PARENT_MAXIMUM_TOTAL_WORDS:
        raise ValueError("total_words is outside the parent allocation domain")
    full, remainder = divmod(total, _PARENT_MAXIMUM_WORDS_PER_STREAM)
    blocks = (int(_PARENT_MAXIMUM_WORDS_PER_STREAM),) * full
    if remainder:
        blocks += (remainder,)
    if not blocks or any(
        block <= 0 or block > _PARENT_MAXIMUM_WORDS_PER_STREAM for block in blocks
    ):
        raise RuntimeError("canonical initializer block partition is invalid")
    return blocks


def _positive_hamilton_quotas(
    probabilities: Tuple[Fraction, ...],
    *,
    name: str,
) -> Tuple[Tuple[int, ...], Tuple[int, ...], int, int]:
    raw = _bounded_exact_tuple(
        probabilities,
        name=name,
        maximum_items=COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
    )
    if not raw:
        raise ValueError("%s must contain at least one category" % name)
    exact_probabilities = []
    aggregate_bits = 0
    for position, value in enumerate(raw):
        if type(value) is not Fraction:
            raise TypeError("%s[%d] must be an exact Fraction" % (name, position))
        if value <= 0:
            raise ValueError("%s must contain positive fractions" % name)
        if (
            value.numerator.bit_length()
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
            or value.denominator.bit_length()
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
        ):
            raise ValueError("%s exceeds the rational integer-bit bound" % name)
        aggregate_bits += value.numerator.bit_length() + value.denominator.bit_length()
        if (
            aggregate_bits
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS
        ):
            raise ValueError("%s exceeds the rational aggregate-bit bound" % name)
        exact_probabilities.append(value)
    total = Fraction(0)
    for value in exact_probabilities:
        denominator_gcd = math.gcd(total.denominator, value.denominator)
        prospective_denominator = (
            total.denominator // denominator_gcd
        ) * value.denominator
        if (
            prospective_denominator.bit_length()
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
        ):
            raise ValueError("%s has excessive common-denominator work" % name)
        total += value
        if (
            total.numerator.bit_length()
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
            or total.denominator.bit_length()
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
        ):
            raise ValueError("%s total exceeds the rational integer-bit bound" % name)
    if total <= 0:
        raise RuntimeError("represented categorical total is not positive")

    category_count = len(exact_probabilities)
    distributable = _DYADIC_DENOMINATOR - category_count
    if distributable < 0:  # pragma: no cover - fixed resource bound
        raise ValueError("categorical table exceeds the dyadic denominator")
    ideals = [
        probability * distributable / total for probability in exact_probabilities
    ]
    floors = [ideal.numerator // ideal.denominator for ideal in ideals]
    remainders = [ideal - floor for ideal, floor in zip(ideals, floors)]
    unassigned = distributable - sum(floors)
    if not 0 <= unassigned < category_count:
        raise RuntimeError("Hamilton remainder count is invalid")
    order = sorted(
        range(category_count),
        key=lambda index: (-remainders[index], index),
    )
    quotas = [1 + floor for floor in floors]
    for index in order[:unassigned]:
        quotas[index] += 1
    if any(quota <= 0 for quota in quotas) or sum(quotas) != _DYADIC_DENOMINATOR:
        raise RuntimeError("positive Hamilton quotas are invalid")

    cumulative = []
    cursor = 0
    for quota in quotas:
        cursor += quota
        cumulative.append(cursor)
    if cumulative[-1] != _DYADIC_DENOMINATOR:
        raise RuntimeError("categorical cumulative total is invalid")

    target = [probability / total for probability in exact_probabilities]
    dyadic = [Fraction(quota, _DYADIC_DENOMINATOR) for quota in quotas]
    total_variation = (
        sum(
            (abs(left - right) for left, right in zip(target, dyadic)),
            Fraction(0),
        )
        / 2
    )
    return (
        tuple(quotas),
        tuple(cumulative),
        total_variation.numerator,
        total_variation.denominator,
    )


def _quota_position(raw_word: object, cumulative: Tuple[int, ...]) -> int:
    word = _protocol._lineage._exact_uint64(raw_word, name="categorical raw word")
    checked = _bounded_exact_tuple(
        cumulative,
        name="cumulative quotas",
        maximum_items=COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
    )
    previous = 0
    for index, endpoint in enumerate(checked):
        endpoint_value = _exact_nonnegative_integer(
            endpoint,
            name="cumulative quotas[%d]" % index,
        )
        if endpoint_value <= previous or endpoint_value > _DYADIC_DENOMINATOR:
            raise ValueError("cumulative quotas are not strictly increasing")
        previous = endpoint_value
    if not checked or checked[-1] != _DYADIC_DENOMINATOR:
        raise ValueError("cumulative quotas do not cover the uint64 domain")
    position = bisect_right(checked, word)
    if position >= len(checked):  # pragma: no cover - terminal bound defensive
        raise RuntimeError("categorical word escaped its exact quota table")
    return position


def _reference_ancestry(
    protocol_owner: _protocol.CounterKeyedInitializerProtocolOwner,
) -> Tuple[
    ProcessValidReferenceJumpComposer,
    ReversibleHybridReference,
    CappedPoissonConfigurationReference,
]:
    if type(protocol_owner) is not _protocol.CounterKeyedInitializerProtocolOwner:
        raise TypeError("protocol_owner has the wrong exact checkpoint-27 type")
    protocol_owner._require_live_binding()
    composer = protocol_owner.control_owner.epoch_owner.reference_composer
    if type(composer) is not ProcessValidReferenceJumpComposer:
        raise TypeError("reference composer has the wrong exact type")
    process = composer.process
    if type(process) is not ReversibleHybridReference:
        raise TypeError("reference process has the wrong exact type")
    reference = process.reference
    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("configuration reference has the wrong exact type")
    if (
        _process_parameter_sha256(process)
        != protocol_owner.certificate.process_parameter_sha256
    ):
        raise ValueError("checkpoint-27 process binding differs from ancestry")
    return composer, process, reference


def _manifest_expected_values(
    reference: CappedPoissonConfigurationReference,
) -> Dict[str, object]:
    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("reference has the wrong exact capped-Poisson type")
    total_cap = _exact_nonnegative_integer(
        reference.total_cap,
        name="reference.total_cap",
    )
    if total_cap > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS:
        raise ValueError("reference cap exceeds the raw-slot work bound")
    if type(reference.type_ids) is not tuple:
        raise TypeError("reference.type_ids must remain an exact tuple")
    if (
        not reference.type_ids
        or len(reference.type_ids) > MAX_CONFIGURATION_EVENT_TYPES
    ):
        raise ValueError("reference type count exceeds the manifest bound")
    if type(reference.type_dimensions) is not MappingProxyType:
        raise TypeError("reference.type_dimensions must remain a mapping proxy")
    if type(reference.type_weights) is not MappingProxyType:
        raise TypeError("reference.type_weights must remain a mapping proxy")
    type_ids = []
    for position, type_id in enumerate(reference.type_ids):
        type_ids.append(
            _protocol._lineage._exact_uint64(
                type_id,
                name="reference.type_ids[%d]" % position,
            )
        )
    if tuple(sorted(type_ids)) != tuple(type_ids) or len(set(type_ids)) != len(
        type_ids
    ):
        raise ValueError("reference type IDs are not strictly increasing")
    type_ids = tuple(type_ids)
    if len(reference.type_dimensions) != len(type_ids) or len(
        reference.type_weights
    ) != len(type_ids):
        raise ValueError("reference type mappings differ from the type-ID tuple")
    type_dimensions = tuple(
        (
            type_id,
            _exact_nonnegative_integer(
                reference.type_dimensions[type_id],
                name="reference dimension for type %d" % type_id,
            ),
        )
        for type_id in type_ids
    )
    if any(
        dimension > MAX_TRANSFORMED_COORDINATE_DIMENSION
        for _, dimension in type_dimensions
    ):
        raise ValueError("reference dimension exceeds the coordinate bound")
    maximum_dimension = max(dimension for _, dimension in type_dimensions)
    required_words = 1 + total_cap * (1 + maximum_dimension)
    if required_words > _PARENT_MAXIMUM_TOTAL_WORDS:
        raise ValueError("reference initializer layout exceeds the word bound")

    if type(reference.activity) is not float or not (
        math.isfinite(reference.activity) and reference.activity > 0.0
    ):
        raise ValueError("reference activity is not a positive exact binary64")
    activity_fraction = Fraction.from_float(reference.activity)
    count_weights = [Fraction(1)]
    for cardinality in range(1, total_cap + 1):
        count_weights.append(count_weights[-1] * activity_fraction / cardinality)
    count_total = sum(count_weights, Fraction(0))
    count_probabilities = tuple(weight / count_total for weight in count_weights)
    type_weights = []
    for type_id in type_ids:
        weight = reference.type_weights[type_id]
        if type(weight) is not float or not (math.isfinite(weight) and weight > 0.0):
            raise ValueError("reference type weights are not positive binary64")
        type_weights.append(Fraction.from_float(weight))
    type_total = sum(type_weights, Fraction(0))
    type_probabilities = tuple(weight / type_total for weight in type_weights)
    (
        count_quotas,
        count_cumulative,
        count_tv_numerator,
        count_tv_denominator,
    ) = _positive_hamilton_quotas(
        count_probabilities,
        name="count_target_probabilities",
    )
    (
        type_quotas,
        type_cumulative,
        type_tv_numerator,
        type_tv_denominator,
    ) = _positive_hamilton_quotas(
        type_probabilities,
        name="type_target_probabilities",
    )
    parameter_key = reference.parameter_key()
    return {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
        ),
        "manifest_policy": (PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY),
        "reference": reference,
        "reference_parameter_key": parameter_key,
        "reference_parameter_sha256": _reference_parameter_sha256(reference),
        "type_ids": type_ids,
        "type_dimensions": type_dimensions,
        "activity": float(reference.activity),
        "total_cap": total_cap,
        "maximum_coordinate_dimension": maximum_dimension,
        "count_target_probability_ratios": tuple(
            (value.numerator, value.denominator) for value in count_probabilities
        ),
        "type_target_probability_ratios": tuple(
            (value.numerator, value.denominator) for value in type_probabilities
        ),
        "count_dyadic_quotas": count_quotas,
        "count_cumulative_ends": count_cumulative,
        "type_dyadic_quotas": type_quotas,
        "type_cumulative_ends": type_cumulative,
        "count_quantization_tv_numerator": count_tv_numerator,
        "count_quantization_tv_denominator": count_tv_denominator,
        "type_quantization_tv_numerator": type_tv_numerator,
        "type_quantization_tv_denominator": type_tv_denominator,
        "raw_word_bits": COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS,
        "coordinate_bucket_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS
        ),
        "coordinate_ignored_low_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS
        ),
        "coordinate_transform": (FINITE_RESOLUTION_REFERENCE_COORDINATE_TRANSFORM),
        "count_word_offset": 0,
        "type_segment_offset": 1,
        "coordinate_segment_offset": 1 + total_cap,
        "coordinate_row_stride": maximum_dimension,
        "required_raw64_words": required_words,
        "canonical_block_raw64_word_counts": _canonical_word_blocks(required_words),
        "manifest_runtime_sha256": _runtime_sha256(),
        "manifest_sha256": _ZERO_SHA256,
    }


@dataclass(frozen=True, eq=False, init=False)
class FiniteResolutionCappedPoissonManifest:
    """Frozen finite-word interpretation of one exact reference object."""

    schema_version: str
    manifest_policy: str
    reference: CappedPoissonConfigurationReference
    reference_parameter_key: Tuple[object, ...]
    reference_parameter_sha256: str
    type_ids: Tuple[int, ...]
    type_dimensions: Tuple[Tuple[int, int], ...]
    activity: float
    total_cap: int
    maximum_coordinate_dimension: int
    count_target_probability_ratios: Tuple[Tuple[int, int], ...]
    type_target_probability_ratios: Tuple[Tuple[int, int], ...]
    count_dyadic_quotas: Tuple[int, ...]
    count_cumulative_ends: Tuple[int, ...]
    type_dyadic_quotas: Tuple[int, ...]
    type_cumulative_ends: Tuple[int, ...]
    count_quantization_tv_numerator: int
    count_quantization_tv_denominator: int
    type_quantization_tv_numerator: int
    type_quantization_tv_denominator: int
    raw_word_bits: int
    coordinate_bucket_bits: int
    coordinate_ignored_low_bits: int
    coordinate_transform: str
    count_word_offset: int
    type_segment_offset: int
    coordinate_segment_offset: int
    coordinate_row_stride: int
    required_raw64_words: int
    canonical_block_raw64_word_counts: Tuple[int, ...]
    manifest_runtime_sha256: str
    manifest_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("finite-resolution manifests cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _MANIFEST_TOKEN:
            raise TypeError("finite-resolution manifests are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("finite-resolution manifest fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_manifest(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("finite-resolution manifests are not pickle objects")


def _manifest_fields() -> Tuple[str, ...]:
    return tuple(FiniteResolutionCappedPoissonManifest.__annotations__)


def _manifest_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    payload = dict(_without(values, "reference", "manifest_sha256"))
    aggregate_bits = 0
    for field in (
        "count_target_probability_ratios",
        "type_target_probability_ratios",
    ):
        ratios = _bounded_exact_tuple(
            payload[field],
            name="manifest digest %s" % field,
            maximum_items=COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        )
        encoded_ratios = []
        for position, ratio in enumerate(ratios):
            if type(ratio) is not tuple or len(ratio) != 2:
                raise TypeError("manifest digest ratios must be exact pairs")
            checked_pair = tuple(
                _bounded_exact_rational_integer(
                    item,
                    name="manifest digest %s[%d][%d]"
                    % (field, position, item_position),
                )
                for item_position, item in enumerate(ratio)
            )
            aggregate_bits += sum(item.bit_length() for item in checked_pair)
            if (
                aggregate_bits
                > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS
            ):
                raise ValueError(
                    "manifest digest ratios exceed the aggregate integer-bit bound"
                )
            encoded_pair = tuple(
                ("nonnegative-integer-hex-v1", format(item, "x"))
                for item in checked_pair
            )
            encoded_ratios.append(encoded_pair)
        payload[field] = tuple(encoded_ratios)
    for field in (
        "count_quantization_tv_numerator",
        "count_quantization_tv_denominator",
        "type_quantization_tv_numerator",
        "type_quantization_tv_denominator",
    ):
        checked_value = _bounded_exact_rational_integer(
            payload[field],
            name="manifest digest %s" % field,
        )
        aggregate_bits += checked_value.bit_length()
        if (
            aggregate_bits
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS
        ):
            raise ValueError(
                "manifest digest ratios exceed the aggregate integer-bit bound"
            )
        payload[field] = (
            "nonnegative-integer-hex-v1",
            format(checked_value, "x"),
        )
    return payload


def _preflight_probability_ratios(
    value: object,
    *,
    name: str,
    exact_length: int,
) -> Tuple[Tuple[int, int], ...]:
    outer = _bounded_exact_tuple(
        value,
        name=name,
        maximum_items=COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        exact_length=exact_length,
    )
    checked = []
    aggregate_bits = 0
    for position, pair in enumerate(outer):
        if type(pair) is not tuple or len(pair) != 2:
            raise TypeError("%s[%d] must be an exact ratio pair" % (name, position))
        numerator = _bounded_exact_rational_integer(
            pair[0], name="%s[%d].numerator" % (name, position)
        )
        denominator = _bounded_exact_rational_integer(
            pair[1], name="%s[%d].denominator" % (name, position)
        )
        aggregate_bits += numerator.bit_length() + denominator.bit_length()
        if (
            aggregate_bits
            > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS
        ):
            raise ValueError("%s exceeds the aggregate integer-bit bound" % name)
        if numerator == 0 or denominator == 0 or numerator > denominator:
            raise ValueError("%s[%d] is not a positive probability" % (name, position))
        checked.append((numerator, denominator))
    return tuple(checked)


def _preflight_quota_table(
    quotas: object,
    cumulative: object,
    *,
    name: str,
    exact_length: int,
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    raw_quotas = _bounded_exact_tuple(
        quotas,
        name=name + " quotas",
        maximum_items=COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        exact_length=exact_length,
    )
    raw_cumulative = _bounded_exact_tuple(
        cumulative,
        name=name + " cumulative",
        maximum_items=COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        exact_length=exact_length,
    )
    checked_quotas = []
    checked_cumulative = []
    cursor = 0
    for position, (quota, endpoint) in enumerate(zip(raw_quotas, raw_cumulative)):
        checked_quota = _exact_nonnegative_integer(
            quota, name="%s quotas[%d]" % (name, position)
        )
        checked_endpoint = _exact_nonnegative_integer(
            endpoint, name="%s cumulative[%d]" % (name, position)
        )
        if checked_quota.bit_length() > 65 or checked_endpoint.bit_length() > 65:
            raise ValueError("%s quota table exceeds the uint64-domain bound" % name)
        if checked_quota == 0:
            raise ValueError("%s quotas must be positive" % name)
        cursor += checked_quota
        if checked_endpoint != cursor or cursor > _DYADIC_DENOMINATOR:
            raise ValueError("%s cumulative table differs from its quotas" % name)
        checked_quotas.append(checked_quota)
        checked_cumulative.append(checked_endpoint)
    if cursor != _DYADIC_DENOMINATOR:
        raise ValueError("%s quotas do not cover the uint64 domain" % name)
    return tuple(checked_quotas), tuple(checked_cumulative)


def _validate_manifest(value: object) -> FiniteResolutionCappedPoissonManifest:
    if type(value) is not FiniteResolutionCappedPoissonManifest:
        raise TypeError("manifest has the wrong exact finite-resolution type")
    for name, maximum in (
        (
            "type_ids",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        ),
        (
            "type_dimensions",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        ),
        (
            "count_target_probability_ratios",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        ),
        (
            "type_target_probability_ratios",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        ),
        ("count_dyadic_quotas", COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES),
        ("count_cumulative_ends", COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES),
        ("type_dyadic_quotas", COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES),
        ("type_cumulative_ends", COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES),
        ("canonical_block_raw64_word_counts", 16),
    ):
        _bounded_exact_tuple(
            getattr(value, name), name="manifest.%s" % name, maximum_items=maximum
        )
    values = {name: getattr(value, name) for name in _manifest_fields()}
    expected_text = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
        ),
        "manifest_policy": (PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY),
        "coordinate_transform": FINITE_RESOLUTION_REFERENCE_COORDINATE_TRANSFORM,
    }
    for name, expected in expected_text.items():
        if type(values[name]) is not str or values[name] != expected:
            raise ValueError("finite-resolution manifest %s differs" % name)
    if type(values["reference"]) is not CappedPoissonConfigurationReference:
        raise TypeError("manifest reference has the wrong exact type")
    if (
        type(values["reference_parameter_key"]) is not tuple
        or len(values["reference_parameter_key"]) != 4
    ):
        raise TypeError("manifest reference parameter key has the wrong shape")
    reference_key = values["reference_parameter_key"]
    if type(reference_key[0]) is not str:
        raise TypeError("manifest reference parameter tag must be exact text")
    key_types = _bounded_exact_tuple(
        reference_key[1],
        name="manifest reference parameter types",
        maximum_items=MAX_CONFIGURATION_EVENT_TYPES,
    )
    for position, entry in enumerate(key_types):
        if type(entry) is not tuple or len(entry) != 3:
            raise TypeError("manifest reference parameter types must be triples")
        _protocol._lineage._exact_uint64(
            entry[0], name="manifest reference type[%d].id" % position
        )
        dimension = _exact_nonnegative_integer(
            entry[1], name="manifest reference type[%d].dimension" % position
        )
        if dimension > MAX_TRANSFORMED_COORDINATE_DIMENSION:
            raise ValueError("manifest reference-key dimension exceeds its bound")
        if type(entry[2]) is not float or not (
            math.isfinite(entry[2]) and entry[2] > 0.0
        ):
            raise ValueError("manifest reference-key weight is not positive binary64")
    if type(reference_key[2]) is not float or not (
        math.isfinite(reference_key[2]) and reference_key[2] > 0.0
    ):
        raise ValueError("manifest reference-key activity is not positive binary64")
    reference_key_cap = _exact_nonnegative_integer(
        reference_key[3], name="manifest reference-key total cap"
    )
    if reference_key_cap > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS:
        raise ValueError("manifest reference-key cap exceeds the raw-slot bound")
    total_cap = _exact_nonnegative_integer(
        values["total_cap"], name="manifest.total_cap"
    )
    if total_cap > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS:
        raise ValueError("manifest total cap exceeds the raw-slot bound")
    type_count = len(values["type_ids"])
    if type_count == 0 or type_count > MAX_CONFIGURATION_EVENT_TYPES:
        raise ValueError("manifest type count exceeds the reference bound")
    for position, type_id in enumerate(values["type_ids"]):
        _protocol._lineage._exact_uint64(
            type_id, name="manifest.type_ids[%d]" % position
        )
    if (
        tuple(sorted(values["type_ids"])) != values["type_ids"]
        or len(set(values["type_ids"])) != type_count
    ):
        raise ValueError("manifest type IDs are not strictly increasing")
    if len(values["type_dimensions"]) != type_count:
        raise ValueError("manifest type-dimension count differs")
    for position, pair in enumerate(values["type_dimensions"]):
        if type(pair) is not tuple or len(pair) != 2:
            raise TypeError("manifest.type_dimensions entries must be exact pairs")
        _protocol._lineage._exact_uint64(
            pair[0], name="manifest.type_dimensions[%d].type" % position
        )
        dimension = _exact_nonnegative_integer(
            pair[1], name="manifest.type_dimensions[%d].dimension" % position
        )
        if dimension > MAX_TRANSFORMED_COORDINATE_DIMENSION:
            raise ValueError("manifest type dimension exceeds the reference bound")
        if pair[0] != values["type_ids"][position]:
            raise ValueError("manifest type dimensions do not follow type order")
    _preflight_probability_ratios(
        values["count_target_probability_ratios"],
        name="manifest.count_target_probability_ratios",
        exact_length=total_cap + 1,
    )
    _preflight_probability_ratios(
        values["type_target_probability_ratios"],
        name="manifest.type_target_probability_ratios",
        exact_length=type_count,
    )
    _preflight_quota_table(
        values["count_dyadic_quotas"],
        values["count_cumulative_ends"],
        name="manifest count",
        exact_length=total_cap + 1,
    )
    _preflight_quota_table(
        values["type_dyadic_quotas"],
        values["type_cumulative_ends"],
        name="manifest type",
        exact_length=type_count,
    )
    for prefix in ("count", "type"):
        numerator = _bounded_exact_rational_integer(
            values["%s_quantization_tv_numerator" % prefix],
            name="manifest.%s_quantization_tv_numerator" % prefix,
        )
        denominator = _bounded_exact_rational_integer(
            values["%s_quantization_tv_denominator" % prefix],
            name="manifest.%s_quantization_tv_denominator" % prefix,
        )
        if denominator == 0 or numerator > denominator:
            raise ValueError("manifest %s quantization TV ratio is invalid" % prefix)
        if math.gcd(numerator, denominator) != 1:
            raise ValueError(
                "manifest %s quantization TV ratio is not reduced" % prefix
            )
    if type(values["activity"]) is not float or not (
        math.isfinite(values["activity"]) and values["activity"] > 0.0
    ):
        raise ValueError("manifest activity is not positive binary64")
    for name in (
        "maximum_coordinate_dimension",
        "raw_word_bits",
        "coordinate_bucket_bits",
        "coordinate_ignored_low_bits",
        "count_word_offset",
        "type_segment_offset",
        "coordinate_segment_offset",
        "coordinate_row_stride",
        "required_raw64_words",
    ):
        _exact_nonnegative_integer(values[name], name="manifest.%s" % name)
    for position, block in enumerate(values["canonical_block_raw64_word_counts"]):
        block_count = _exact_nonnegative_integer(
            block,
            name="manifest.canonical_block_raw64_word_counts[%d]" % position,
        )
        if block_count == 0 or block_count > _PARENT_MAXIMUM_WORDS_PER_STREAM:
            raise ValueError("manifest canonical block size is outside its bound")
    _protocol._thinning._require_sha256(
        values["manifest_sha256"], name="manifest.manifest_sha256"
    )
    _protocol._thinning._require_sha256(
        values["reference_parameter_sha256"],
        name="manifest.reference_parameter_sha256",
    )
    _protocol._thinning._require_sha256(
        values["manifest_runtime_sha256"],
        name="manifest.manifest_runtime_sha256",
    )
    expected = _manifest_expected_values(value.reference)
    expected["manifest_sha256"] = _protocol._thinning._semantic_digest(
        _manifest_payload(expected)
    )
    for name in _manifest_fields():
        actual = values[name]
        wanted = expected[name]
        if name == "reference":
            if actual is not wanted:
                raise ValueError("finite-resolution manifest reference changed")
        elif not _protocol._thinning._field_matches(name, actual, wanted):
            raise ValueError("finite-resolution manifest field %s differs" % name)
    return value


def _make_manifest(
    reference: CappedPoissonConfigurationReference,
) -> FiniteResolutionCappedPoissonManifest:
    values = _manifest_expected_values(reference)
    values["manifest_sha256"] = _protocol._thinning._semantic_digest(
        _manifest_payload(values)
    )
    return FiniteResolutionCappedPoissonManifest(
        **values,
        _construction_token=_MANIFEST_TOKEN,
    )


def _runtime_sha256() -> str:
    expected = {
        "word_bits": 64,
        "bucket_bits": 53,
        "ignored_low_bits": 11,
        "maximum_raw_slots": 64,
        "maximum_categories": 4_097,
        "maximum_exact_rational_integer_bits": 131_072,
        "maximum_exact_rational_aggregate_bits": 16_777_216,
        "coordinate_transform": (
            "upper53-bits;symmetric-lower-tail;"
            "p=(2r+1)/2^54;scipy-special-ndtri;binary64-output-v1"
        ),
    }
    actual = {
        "word_bits": COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS,
        "bucket_bits": (COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS),
        "ignored_low_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS
        ),
        "maximum_raw_slots": COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        "maximum_categories": COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        "maximum_exact_rational_integer_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
        ),
        "maximum_exact_rational_aggregate_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS
        ),
        "coordinate_transform": FINITE_RESOLUTION_REFERENCE_COORDINATE_TRANSFORM,
    }
    if actual != expected:
        raise ValueError("finite-resolution initializer constants changed")
    sentinel_words = (
        0,
        (1 << 63) - 1,
        1 << 63,
        _DYADIC_DENOMINATOR - 1,
    )
    sentinels = tuple(_coordinate_transform_details(word) for word in sentinel_words)
    return _protocol._thinning._semantic_digest(
        {
            "schema_version": (
                PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
            ),
            "policy": PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY,
            "scope": PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCOPE,
            "python": tuple(sys.version_info[:3]),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "constants": tuple(sorted(actual.items())),
            "coordinate_sentinel_words": sentinel_words,
            "coordinate_sentinel_outputs": sentinels,
            "parent_maximum_words_per_stream": (_PARENT_MAXIMUM_WORDS_PER_STREAM),
            "parent_maximum_total_words": _PARENT_MAXIMUM_TOTAL_WORDS,
        }
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedReferenceInitializerCertificate:
    """Certificate for the checkpoint-twenty-eight finite transformer."""

    schema_version: str
    certificate_scope: str
    initializer_policy: str
    initializer_role_sha256: str
    process_parameter_sha256: str
    checkpoint27_certificate: _protocol.CounterKeyedInitializerProtocolCertificate
    checkpoint27_certificate_sha256: str
    checkpoint27_role_sha256: str
    checkpoint27_runtime_sha256: str
    manifest: FiniteResolutionCappedPoissonManifest
    manifest_sha256: str
    reference_parameter_sha256: str
    initializer_runtime_sha256: str
    maximum_raw_slots: int
    maximum_categories: int
    maximum_exact_rational_integer_bits: int
    maximum_exact_rational_aggregate_bits: int
    maximum_raw64_words: int
    raw_word_bits: int
    coordinate_bucket_bits: int
    coordinate_ignored_low_bits: int
    exact_checkpoint27_owner_binding_certified: bool
    ancestry_derived_reference_binding_certified: bool
    sealed_reference_manifest_certified: bool
    canonical_fixed_word_layout_certified: bool
    canonical_parent_block_partition_certified: bool
    positive_dyadic_count_quotas_certified: bool
    positive_dyadic_type_quotas_certified: bool
    exact_target_probability_tv_recorded: bool
    finite_coordinate_codebook_transform_certified: bool
    complete_raw_slot_materialization_certified: bool
    duplicate_stable_canonical_mapping_certified: bool
    finite_configuration_output_certified: bool
    hypothetical_product_uniform_pushforward_defined: bool
    exact_parent_result_replay_certified: bool
    no_caller_rng_certified: bool
    fixed_cost_no_retry_reference_transform_certified: bool
    exact_continuous_gaussian_law_certified: bool
    exact_capped_poisson_reference_law_certified: bool
    quantitative_weak_or_wasserstein_bound_certified: bool
    unconditional_full_configuration_tv_one_certified: bool
    actual_philox_uniformity_certified: bool
    statistical_independence_certified: bool
    physical_randomness_certified: bool
    enumeration_strategy_certified: bool
    rejection_strategy_certified: bool
    sir_strategy_certified: bool
    conditional_or_tilted_initializer_law_certified: bool
    accepted_configuration_to_lineage_mapping_certified: bool
    tag3_occurrence_payload_coordination_certified: bool
    tag3_cross_initialization_disjointness_certified: bool
    global_duplicate_address_use_prevention_certified: bool
    brownian_stream_consumption_certified: bool
    brownian_additive_coupling_certified: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    strang_sampler_admissible: bool
    full_sampler_admissible: bool
    analytic_target_preserved: bool
    rounded_stationarity_certified: bool
    sampler_liveness_certified: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("reference initializer certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("reference initializer certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("reference initializer certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("reference initializer certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedReferenceInitializerCertificate.__annotations__)


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "checkpoint27_certificate",
        "manifest",
        "certificate_sha256",
    )


def _validate_certificate(
    value: object,
) -> CounterKeyedReferenceInitializerCertificate:
    if type(value) is not CounterKeyedReferenceInitializerCertificate:
        raise TypeError("certificate has the wrong exact reference initializer type")
    values = {name: getattr(value, name) for name in _certificate_fields()}
    expected_text = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
        ),
        "certificate_scope": (PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCOPE),
        "initializer_policy": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY
        ),
    }
    for name, expected in expected_text.items():
        if type(values[name]) is not str or values[name] != expected:
            raise ValueError("reference initializer certificate %s differs" % name)
    _protocol._thinning._require_sha256(
        values["initializer_role_sha256"],
        name="certificate.initializer_role_sha256",
    )
    parent = _protocol._validate_certificate(values["checkpoint27_certificate"])
    manifest = _validate_manifest(values["manifest"])
    expected_scalars = {
        "process_parameter_sha256": parent.process_parameter_sha256,
        "checkpoint27_certificate_sha256": parent.certificate_sha256,
        "checkpoint27_role_sha256": parent.protocol_role_sha256,
        "checkpoint27_runtime_sha256": parent.protocol_runtime_sha256,
        "manifest_sha256": manifest.manifest_sha256,
        "reference_parameter_sha256": manifest.reference_parameter_sha256,
        "initializer_runtime_sha256": _runtime_sha256(),
        "maximum_raw_slots": COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        "maximum_categories": COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        "maximum_exact_rational_integer_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
        ),
        "maximum_exact_rational_aggregate_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS
        ),
        "maximum_raw64_words": parent.maximum_total_raw64_words,
        "raw_word_bits": COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS,
        "coordinate_bucket_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS
        ),
        "coordinate_ignored_low_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS
        ),
    }
    for name, expected in expected_scalars.items():
        if type(values[name]) is not type(expected) or values[name] != expected:
            raise ValueError("reference initializer certificate %s differs" % name)
    positive = (
        "exact_checkpoint27_owner_binding_certified",
        "ancestry_derived_reference_binding_certified",
        "sealed_reference_manifest_certified",
        "canonical_fixed_word_layout_certified",
        "canonical_parent_block_partition_certified",
        "positive_dyadic_count_quotas_certified",
        "positive_dyadic_type_quotas_certified",
        "exact_target_probability_tv_recorded",
        "finite_coordinate_codebook_transform_certified",
        "complete_raw_slot_materialization_certified",
        "duplicate_stable_canonical_mapping_certified",
        "finite_configuration_output_certified",
        "hypothetical_product_uniform_pushforward_defined",
        "exact_parent_result_replay_certified",
        "no_caller_rng_certified",
        "fixed_cost_no_retry_reference_transform_certified",
        "passed",
    )
    negative = (
        "exact_continuous_gaussian_law_certified",
        "exact_capped_poisson_reference_law_certified",
        "quantitative_weak_or_wasserstein_bound_certified",
        "unconditional_full_configuration_tv_one_certified",
        "actual_philox_uniformity_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "enumeration_strategy_certified",
        "rejection_strategy_certified",
        "sir_strategy_certified",
        "conditional_or_tilted_initializer_law_certified",
        "accepted_configuration_to_lineage_mapping_certified",
        "tag3_occurrence_payload_coordination_certified",
        "tag3_cross_initialization_disjointness_certified",
        "global_duplicate_address_use_prevention_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "analytic_target_preserved",
        "rounded_stationarity_certified",
        "sampler_liveness_certified",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in positive:
        if _exact_bool(values[name], name="certificate.%s" % name) is not True:
            raise ValueError("reference initializer positive claim %s differs" % name)
    for name in negative:
        if _exact_bool(values[name], name="certificate.%s" % name) is not False:
            raise ValueError("reference initializer negative claim %s differs" % name)
    for name in (
        "process_parameter_sha256",
        "checkpoint27_certificate_sha256",
        "checkpoint27_role_sha256",
        "checkpoint27_runtime_sha256",
        "manifest_sha256",
        "reference_parameter_sha256",
        "initializer_runtime_sha256",
        "certificate_sha256",
    ):
        _protocol._thinning._require_sha256(values[name], name="certificate.%s" % name)
    expected_digest = _protocol._thinning._semantic_digest(_certificate_payload(values))
    if values["certificate_sha256"] != expected_digest:
        raise ValueError("reference initializer certificate digest differs")
    return value


def _make_certificate(
    parent: _protocol.CounterKeyedInitializerProtocolCertificate,
    manifest: FiniteResolutionCappedPoissonManifest,
    *,
    initializer_role_sha256: str,
) -> CounterKeyedReferenceInitializerCertificate:
    checked_parent = _protocol._validate_certificate(parent)
    checked_manifest = _validate_manifest(manifest)
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
        ),
        "certificate_scope": (PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCOPE),
        "initializer_policy": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY
        ),
        "initializer_role_sha256": initializer_role_sha256,
        "process_parameter_sha256": checked_parent.process_parameter_sha256,
        "checkpoint27_certificate": parent,
        "checkpoint27_certificate_sha256": checked_parent.certificate_sha256,
        "checkpoint27_role_sha256": checked_parent.protocol_role_sha256,
        "checkpoint27_runtime_sha256": checked_parent.protocol_runtime_sha256,
        "manifest": manifest,
        "manifest_sha256": checked_manifest.manifest_sha256,
        "reference_parameter_sha256": (checked_manifest.reference_parameter_sha256),
        "initializer_runtime_sha256": _runtime_sha256(),
        "maximum_raw_slots": COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        "maximum_categories": COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES,
        "maximum_exact_rational_integer_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
        ),
        "maximum_exact_rational_aggregate_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS
        ),
        "maximum_raw64_words": checked_parent.maximum_total_raw64_words,
        "raw_word_bits": COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS,
        "coordinate_bucket_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS
        ),
        "coordinate_ignored_low_bits": (
            COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS
        ),
        "certificate_sha256": _ZERO_SHA256,
    }
    positive = {
        "exact_checkpoint27_owner_binding_certified",
        "ancestry_derived_reference_binding_certified",
        "sealed_reference_manifest_certified",
        "canonical_fixed_word_layout_certified",
        "canonical_parent_block_partition_certified",
        "positive_dyadic_count_quotas_certified",
        "positive_dyadic_type_quotas_certified",
        "exact_target_probability_tv_recorded",
        "finite_coordinate_codebook_transform_certified",
        "complete_raw_slot_materialization_certified",
        "duplicate_stable_canonical_mapping_certified",
        "finite_configuration_output_certified",
        "hypothetical_product_uniform_pushforward_defined",
        "exact_parent_result_replay_certified",
        "no_caller_rng_certified",
        "fixed_cost_no_retry_reference_transform_certified",
    }
    boolean_fields = tuple(
        name
        for name in CounterKeyedReferenceInitializerCertificate.__annotations__
        if name.endswith("certified")
        or name.endswith("defined")
        or name.endswith("recorded")
        or name.endswith("admissible")
    )
    for name in boolean_fields:
        values[name] = name in positive
    for name in (
        "analytic_target_preserved",
        "runtime_portable",
        "cryptographic_authentication",
    ):
        values[name] = False
    values["passed"] = True
    values["certificate_sha256"] = _protocol._thinning._semantic_digest(
        _certificate_payload(values)
    )
    return CounterKeyedReferenceInitializerCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _validated_event_key(
    event: object,
    *,
    name: str,
    exact_dimension: Optional[int] = None,
) -> Tuple[object, ...]:
    if type(event) is not TransformedEvent:
        raise TypeError("%s has the wrong exact transformed-event type" % name)
    event_type = _protocol._lineage._exact_uint64(
        event.event_type,
        name=name + ".event_type",
    )
    if event_type > (1 << 63) - 1:
        raise ValueError("%s event type exceeds the transformed-event bound" % name)
    coordinates = _bounded_exact_tuple(
        event.coordinates,
        name=name + ".coordinates",
        maximum_items=MAX_TRANSFORMED_COORDINATE_DIMENSION,
        exact_length=exact_dimension,
    )
    for position, coordinate in enumerate(coordinates):
        if type(coordinate) is not float or not math.isfinite(coordinate):
            raise ValueError(
                "%s.coordinates[%d] is not finite binary64" % (name, position)
            )
        if coordinate == 0.0 and math.copysign(1.0, coordinate) < 0.0:
            raise ValueError("%s coordinates must use positive zero" % name)
    return event_type, coordinates


def _event_sha256(event: TransformedEvent) -> str:
    event_type, coordinates = _validated_event_key(event, name="event")
    return _protocol._thinning._semantic_digest(
        {
            "event_type": event_type,
            "coordinates": coordinates,
        }
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedReferenceInitializerRawSlot:
    """One completely transformed raw slot, active or inactive."""

    schema_version: str
    certificate_sha256: str
    manifest_sha256: str
    raw_slot_index: int
    active: bool
    type_word_offset: int
    type_raw64_word: int
    type_quota_position: int
    event_type: int
    event_dimension: int
    coordinate_word_count: int
    coordinate_word_offsets: Tuple[int, ...]
    coordinate_raw64_words: Tuple[int, ...]
    coordinate_bucket_indices: Tuple[int, ...]
    coordinate_midpoint_numerators: Tuple[int, ...]
    coordinate_probability_hexes: Tuple[str, ...]
    coordinate_codebook_values: Tuple[float, ...]
    coordinate_value_hexes: Tuple[str, ...]
    active_coordinates: Tuple[float, ...]
    event: TransformedEvent
    event_sha256: str
    all_coordinate_padding_materialized: bool
    slot_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("reference initializer raw slots cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _SLOT_TOKEN:
            raise TypeError("reference initializer raw slots are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("reference initializer raw-slot fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_slot_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("reference initializer raw slots are not pickle objects")


def _slot_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedReferenceInitializerRawSlot.__annotations__)


def _slot_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "event", "slot_sha256")


def _validate_slot_record(
    value: object,
) -> CounterKeyedReferenceInitializerRawSlot:
    if type(value) is not CounterKeyedReferenceInitializerRawSlot:
        raise TypeError("raw slot has the wrong exact reference initializer type")
    values = {name: getattr(value, name) for name in _slot_fields()}
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"]
        != PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
    ):
        raise ValueError("reference initializer raw-slot schema differs")
    for name in (
        "certificate_sha256",
        "manifest_sha256",
        "event_sha256",
        "slot_sha256",
    ):
        _protocol._thinning._require_sha256(values[name], name="raw_slot.%s" % name)
    raw_slot_index = _exact_nonnegative_integer(
        values["raw_slot_index"], name="raw_slot.raw_slot_index"
    )
    if raw_slot_index >= COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS:
        raise ValueError("raw-slot index exceeds the work bound")
    _exact_bool(values["active"], name="raw_slot.active")
    type_word_offset = _exact_nonnegative_integer(
        values["type_word_offset"], name="raw_slot.type_word_offset"
    )
    if type_word_offset >= _PARENT_MAXIMUM_TOTAL_WORDS:
        raise ValueError("raw-slot type-word offset exceeds the parent word bound")
    _protocol._lineage._exact_uint64(
        values["type_raw64_word"], name="raw_slot.type_raw64_word"
    )
    type_quota_position = _exact_nonnegative_integer(
        values["type_quota_position"], name="raw_slot.type_quota_position"
    )
    if type_quota_position >= COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES:
        raise ValueError("raw-slot type quota position exceeds the category bound")
    _protocol._lineage._exact_uint64(values["event_type"], name="raw_slot.event_type")
    event_dimension = _exact_nonnegative_integer(
        values["event_dimension"], name="raw_slot.event_dimension"
    )
    if event_dimension > MAX_TRANSFORMED_COORDINATE_DIMENSION:
        raise ValueError("raw-slot event dimension exceeds the coordinate bound")
    coordinate_count = _exact_nonnegative_integer(
        values["coordinate_word_count"],
        name="raw_slot.coordinate_word_count",
    )
    if coordinate_count > MAX_TRANSFORMED_COORDINATE_DIMENSION:
        raise ValueError("raw-slot coordinate count exceeds the work bound")
    tuple_fields = (
        "coordinate_word_offsets",
        "coordinate_raw64_words",
        "coordinate_bucket_indices",
        "coordinate_midpoint_numerators",
        "coordinate_probability_hexes",
        "coordinate_codebook_values",
        "coordinate_value_hexes",
    )
    for name in tuple_fields:
        _bounded_exact_tuple(
            values[name],
            name="raw_slot.%s" % name,
            maximum_items=MAX_TRANSFORMED_COORDINATE_DIMENSION,
            exact_length=coordinate_count,
        )
    _bounded_exact_tuple(
        values["active_coordinates"],
        name="raw_slot.active_coordinates",
        maximum_items=MAX_TRANSFORMED_COORDINATE_DIMENSION,
        exact_length=event_dimension,
    )
    previous_offset = -1
    for index in range(coordinate_count):
        offset = _exact_nonnegative_integer(
            values["coordinate_word_offsets"][index],
            name="raw_slot.coordinate_word_offsets[%d]" % index,
        )
        if offset <= previous_offset:
            raise ValueError("raw-slot coordinate offsets are not increasing")
        if offset >= _PARENT_MAXIMUM_TOTAL_WORDS:
            raise ValueError("raw-slot coordinate offset exceeds the parent word bound")
        previous_offset = offset
        raw_word = _protocol._lineage._exact_uint64(
            values["coordinate_raw64_words"][index],
            name="raw_slot.coordinate_raw64_words[%d]" % index,
        )
        bucket = _exact_nonnegative_integer(
            values["coordinate_bucket_indices"][index],
            name="raw_slot.coordinate_bucket_indices[%d]" % index,
        )
        if bucket >= _COORDINATE_BUCKET_COUNT:
            raise ValueError("raw-slot coordinate bucket exceeds 53 bits")
        numerator = _exact_nonnegative_integer(
            values["coordinate_midpoint_numerators"][index],
            name="raw_slot.coordinate_midpoint_numerators[%d]" % index,
        )
        if numerator == 0 or numerator >= (1 << 53) or numerator % 2 != 1:
            raise ValueError("raw-slot midpoint numerator is invalid")
        probability_hex = values["coordinate_probability_hexes"][index]
        value_hex = values["coordinate_value_hexes"][index]
        if type(probability_hex) is not str or type(value_hex) is not str:
            raise TypeError("raw-slot coordinate hex evidence must be exact text")
        if len(probability_hex) > 32 or len(value_hex) > 32:
            raise ValueError("raw-slot coordinate hex evidence exceeds its bound")
        coordinate = values["coordinate_codebook_values"][index]
        if type(coordinate) is not float or not math.isfinite(coordinate):
            raise ValueError("raw-slot coordinate must be finite binary64")
        if coordinate == 0.0 or abs(coordinate) < float(np.finfo(np.float64).tiny):
            raise ValueError("raw-slot coordinate must be nonzero normal binary64")
        if coordinate.hex() != value_hex:
            raise ValueError("raw-slot coordinate hex evidence differs")
        expected_transform = _coordinate_transform_details(raw_word)
        if (
            bucket,
            numerator,
            probability_hex,
            coordinate,
            value_hex,
        ) != expected_transform:
            raise ValueError("raw-slot coordinate transform evidence differs")
    for index, coordinate in enumerate(values["active_coordinates"]):
        if type(coordinate) is not float or not math.isfinite(coordinate):
            raise ValueError(
                "raw_slot.active_coordinates[%d] is not finite binary64" % index
            )
    if (
        tuple(values["coordinate_codebook_values"][:event_dimension])
        != values["active_coordinates"]
    ):
        raise ValueError("raw-slot active coordinates are not the codebook prefix")
    event_type, event_coordinates = _validated_event_key(
        values["event"],
        name="raw_slot.event",
        exact_dimension=event_dimension,
    )
    if (
        event_type != values["event_type"]
        or event_coordinates != values["active_coordinates"]
    ):
        raise ValueError("raw-slot event differs from its transformed fields")
    if values["event_sha256"] != _event_sha256(values["event"]):
        raise ValueError("raw-slot event digest differs")
    if (
        _exact_bool(
            values["all_coordinate_padding_materialized"],
            name="raw_slot.all_coordinate_padding_materialized",
        )
        is not True
    ):
        raise ValueError("raw-slot coordinate materialization claim differs")
    expected_digest = _protocol._thinning._semantic_digest(_slot_payload(values))
    if values["slot_sha256"] != expected_digest:
        raise ValueError("reference initializer raw-slot digest differs")
    return value


def _materialize_slot_fields(
    manifest: FiniteResolutionCappedPoissonManifest,
    words: Tuple[int, ...],
    *,
    raw_slot_index: int,
) -> Dict[str, object]:
    """Transform one full raw slot without consulting the count word."""

    type_offset = manifest.type_segment_offset + raw_slot_index
    type_word = words[type_offset]
    type_position = _quota_position(type_word, manifest.type_cumulative_ends)
    event_type = manifest.type_ids[type_position]
    dimension_by_type = dict(manifest.type_dimensions)
    event_dimension = dimension_by_type[event_type]
    coordinate_offsets = tuple(
        manifest.coordinate_segment_offset
        + raw_slot_index * manifest.coordinate_row_stride
        + coordinate_index
        for coordinate_index in range(manifest.maximum_coordinate_dimension)
    )
    coordinate_words = tuple(words[offset] for offset in coordinate_offsets)
    transformed = tuple(
        _coordinate_transform_details(word) for word in coordinate_words
    )
    buckets = tuple(item[0] for item in transformed)
    numerators = tuple(item[1] for item in transformed)
    probability_hexes = tuple(item[2] for item in transformed)
    codebook_values = tuple(item[3] for item in transformed)
    value_hexes = tuple(item[4] for item in transformed)
    active_coordinates = codebook_values[:event_dimension]
    event = TransformedEvent(event_type, active_coordinates)
    return {
        "raw_slot_index": raw_slot_index,
        "type_word_offset": type_offset,
        "type_raw64_word": type_word,
        "type_quota_position": type_position,
        "event_type": event_type,
        "event_dimension": event_dimension,
        "coordinate_word_count": manifest.maximum_coordinate_dimension,
        "coordinate_word_offsets": coordinate_offsets,
        "coordinate_raw64_words": coordinate_words,
        "coordinate_bucket_indices": buckets,
        "coordinate_midpoint_numerators": numerators,
        "coordinate_probability_hexes": probability_hexes,
        "coordinate_codebook_values": codebook_values,
        "coordinate_value_hexes": value_hexes,
        "active_coordinates": active_coordinates,
        "event": event,
        "event_sha256": _event_sha256(event),
    }


def _make_slot(
    certificate: CounterKeyedReferenceInitializerCertificate,
    manifest: FiniteResolutionCappedPoissonManifest,
    materialized_fields: Mapping[str, object],
    *,
    active: bool,
) -> CounterKeyedReferenceInitializerRawSlot:
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
        ),
        "certificate_sha256": certificate.certificate_sha256,
        "manifest_sha256": manifest.manifest_sha256,
        **materialized_fields,
        "active": active,
        "all_coordinate_padding_materialized": True,
        "slot_sha256": _ZERO_SHA256,
    }
    values["slot_sha256"] = _protocol._thinning._semantic_digest(_slot_payload(values))
    return CounterKeyedReferenceInitializerRawSlot(
        **values,
        _construction_token=_SLOT_TOKEN,
    )


def _configuration_sha256(configuration: TransformedConfiguration) -> str:
    if type(configuration) is not tuple:
        raise TypeError("configuration must be an exact tuple")
    if len(configuration) > COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS:
        raise ValueError("configuration exceeds the initializer slot bound")
    event_keys = []
    for position, event in enumerate(configuration):
        event_keys.append(
            _validated_event_key(event, name="configuration[%d]" % position)
        )
    return _protocol._thinning._semantic_digest(
        {"configuration_event_keys": tuple(event_keys)}
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedReferenceInitializerResult:
    """One finite configuration with complete parent and raw-slot evidence."""

    schema_version: str
    certificate: CounterKeyedReferenceInitializerCertificate
    certificate_sha256: str
    manifest: FiniteResolutionCappedPoissonManifest
    manifest_sha256: str
    parent_protocol_result: _protocol.CounterKeyedInitializerProtocolResult
    parent_result_sha256: str
    run_id: int
    initialization_index: int
    parent_block_count: int
    parent_entry_sha256s: Tuple[str, ...]
    raw64_blocks: Tuple[Tuple[int, ...], ...]
    raw64_block_offsets: Tuple[int, ...]
    concatenated_raw64_words: Tuple[int, ...]
    total_raw64_words: int
    count_word_offset: int
    count_raw64_word: int
    count_quota_position: int
    sampled_cardinality: int
    raw_slots: Tuple[CounterKeyedReferenceInitializerRawSlot, ...]
    raw_slot_sha256s: Tuple[str, ...]
    selected_raw_events: TransformedConfiguration
    selected_raw_event_sha256s: Tuple[str, ...]
    canonical_configuration: TransformedConfiguration
    canonical_configuration_sha256: str
    canonical_position_to_raw_slot: Tuple[int, ...]
    raw_slot_to_canonical_position: Tuple[Optional[int], ...]
    exact_fixed_layout_consumed: bool
    all_raw_slot_transforms_completed_before_cardinality_decoding: bool
    duplicate_stable_canonical_bijection: bool
    finite_product_uniform_pushforward_only: bool
    no_caller_rng: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("reference initializer results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("reference initializer results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("reference initializer result fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_result_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("reference initializer results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedReferenceInitializerResult.__annotations__)


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "manifest",
        "parent_protocol_result",
        "raw_slots",
        "selected_raw_events",
        "canonical_configuration",
        "result_sha256",
    )


def _validate_result_record(
    value: object,
) -> CounterKeyedReferenceInitializerResult:
    if type(value) is not CounterKeyedReferenceInitializerResult:
        raise TypeError("result has the wrong exact reference initializer type")
    for name, maximum in (
        ("parent_entry_sha256s", 16),
        ("raw64_blocks", 16),
        ("raw64_block_offsets", 17),
        ("concatenated_raw64_words", _PARENT_MAXIMUM_TOTAL_WORDS),
        ("raw_slots", COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS),
        ("raw_slot_sha256s", COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS),
        (
            "selected_raw_events",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        ),
        (
            "selected_raw_event_sha256s",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        ),
        (
            "canonical_configuration",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        ),
        (
            "canonical_position_to_raw_slot",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        ),
        (
            "raw_slot_to_canonical_position",
            COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        ),
    ):
        _bounded_exact_tuple(
            getattr(value, name),
            name="result.%s" % name,
            maximum_items=maximum,
        )
    values = {name: getattr(value, name) for name in _result_fields()}
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"]
        != PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
    ):
        raise ValueError("reference initializer result schema differs")
    certificate = _validate_certificate(values["certificate"])
    manifest = _validate_manifest(values["manifest"])
    if certificate.manifest is not manifest:
        raise ValueError("reference initializer result manifest identity differs")
    parent = _protocol._validate_result_record(values["parent_protocol_result"])
    if parent.certificate is not certificate.checkpoint27_certificate:
        raise ValueError("reference initializer parent certificate differs")
    for name in (
        "certificate_sha256",
        "manifest_sha256",
        "parent_result_sha256",
        "canonical_configuration_sha256",
        "result_sha256",
    ):
        _protocol._thinning._require_sha256(values[name], name="result.%s" % name)
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("reference initializer result certificate digest differs")
    if values["manifest_sha256"] != manifest.manifest_sha256:
        raise ValueError("reference initializer result manifest digest differs")
    if values["parent_result_sha256"] != parent.result_sha256:
        raise ValueError("reference initializer parent-result digest differs")
    run_id = _protocol._lineage._exact_uint64(values["run_id"], name="result.run_id")
    initialization_index = _protocol._lineage._exact_uint64(
        values["initialization_index"], name="result.initialization_index"
    )
    if parent.run_id != run_id or parent.initialization_index != initialization_index:
        raise ValueError("reference initializer parent coordinates differ")
    if (
        parent.strategy != _protocol.INITIALIZER_STRATEGY_REFERENCE
        or parent.strategy_budget != 1
        or parent.work_item_raw64_word_counts
        != manifest.canonical_block_raw64_word_counts
        or parent.selection_raw64_word_count != 0
    ):
        raise ValueError("reference initializer parent allocation differs")
    block_count = _exact_nonnegative_integer(
        values["parent_block_count"], name="result.parent_block_count"
    )
    if block_count != len(manifest.canonical_block_raw64_word_counts):
        raise ValueError("reference initializer parent block count differs")
    if len(values["parent_entry_sha256s"]) != block_count:
        raise ValueError("reference initializer parent digest count differs")
    if len(values["raw64_blocks"]) != block_count:
        raise ValueError("reference initializer raw-block count differs")
    if len(values["raw64_block_offsets"]) != block_count + 1:
        raise ValueError("reference initializer block-offset count differs")
    for position, digest in enumerate(values["parent_entry_sha256s"]):
        _protocol._thinning._require_sha256(
            digest,
            name="result.parent_entry_sha256s[%d]" % position,
        )
    for position, offset in enumerate(values["raw64_block_offsets"]):
        checked_offset = _exact_nonnegative_integer(
            offset,
            name="result.raw64_block_offsets[%d]" % position,
        )
        if checked_offset > _PARENT_MAXIMUM_TOTAL_WORDS:
            raise ValueError("reference initializer block offset exceeds its bound")
    if values["parent_entry_sha256s"] != parent.entry_sha256s:
        raise ValueError("reference initializer parent entry digests differ")
    expected_offsets = [0]
    for position, (block, expected_count, entry) in enumerate(
        zip(
            values["raw64_blocks"],
            manifest.canonical_block_raw64_word_counts,
            parent.entries,
        )
    ):
        _bounded_exact_tuple(
            block,
            name="result.raw64_blocks[%d]" % position,
            maximum_items=_PARENT_MAXIMUM_WORDS_PER_STREAM,
            exact_length=expected_count,
        )
        if block is not entry.raw64_words:
            raise ValueError("reference initializer lost parent raw-block identity")
        for word_index, word in enumerate(block):
            _protocol._lineage._exact_uint64(
                word,
                name="result.raw64_blocks[%d][%d]" % (position, word_index),
            )
        expected_offsets.append(expected_offsets[-1] + len(block))
    if values["raw64_block_offsets"] != tuple(expected_offsets):
        raise ValueError("reference initializer block offsets differ")
    words = values["concatenated_raw64_words"]
    total_words = _exact_nonnegative_integer(
        values["total_raw64_words"], name="result.total_raw64_words"
    )
    if total_words != manifest.required_raw64_words or len(words) != total_words:
        raise ValueError("reference initializer total word count differs")
    for position, word in enumerate(words):
        _protocol._lineage._exact_uint64(
            word, name="result.concatenated_raw64_words[%d]" % position
        )
    expected_words = tuple(word for block in values["raw64_blocks"] for word in block)
    if words != expected_words:
        raise ValueError("reference initializer block concatenation differs")
    count_offset = _exact_nonnegative_integer(
        values["count_word_offset"], name="result.count_word_offset"
    )
    if count_offset != manifest.count_word_offset:
        raise ValueError("reference initializer count offset differs")
    count_word = _protocol._lineage._exact_uint64(
        values["count_raw64_word"], name="result.count_raw64_word"
    )
    if count_word != words[count_offset]:
        raise ValueError("reference initializer count word differs")
    count_position = _exact_nonnegative_integer(
        values["count_quota_position"], name="result.count_quota_position"
    )
    cardinality = _exact_nonnegative_integer(
        values["sampled_cardinality"], name="result.sampled_cardinality"
    )
    expected_cardinality = _quota_position(count_word, manifest.count_cumulative_ends)
    if count_position != expected_cardinality or cardinality != expected_cardinality:
        raise ValueError("reference initializer cardinality transform differs")
    if cardinality > manifest.total_cap:
        raise ValueError("reference initializer cardinality exceeds the cap")
    if len(values["raw_slots"]) != manifest.total_cap:
        raise ValueError("reference initializer raw-slot count differs")
    if len(values["raw_slot_sha256s"]) != manifest.total_cap:
        raise ValueError("reference initializer raw-slot digest count differs")
    for position, digest in enumerate(values["raw_slot_sha256s"]):
        _protocol._thinning._require_sha256(
            digest,
            name="result.raw_slot_sha256s[%d]" % position,
        )
    for position, slot in enumerate(values["raw_slots"]):
        if type(slot) is not CounterKeyedReferenceInitializerRawSlot:
            raise TypeError("reference initializer raw slot has the wrong exact type")
        coordinate_count = _exact_nonnegative_integer(
            slot.coordinate_word_count,
            name="result.raw_slots[%d].coordinate_word_count" % position,
        )
        if coordinate_count != manifest.maximum_coordinate_dimension:
            raise ValueError("reference initializer raw-slot coordinate count differs")
    dimension_by_type = dict(manifest.type_dimensions)
    occupied_offsets = [count_offset]
    for position, slot in enumerate(values["raw_slots"]):
        _validate_slot_record(slot)
        if slot.raw_slot_index != position:
            raise ValueError("reference initializer raw-slot order differs")
        if slot.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("reference initializer raw-slot certificate differs")
        if slot.manifest_sha256 != manifest.manifest_sha256:
            raise ValueError("reference initializer raw-slot manifest differs")
        if slot.active is not (position < cardinality):
            raise ValueError("reference initializer raw-slot activity differs")
        if values["raw_slot_sha256s"][position] != slot.slot_sha256:
            raise ValueError("reference initializer raw-slot digest differs")
        expected_type_offset = manifest.type_segment_offset + position
        if slot.type_word_offset != expected_type_offset:
            raise ValueError("reference initializer raw-slot type offset differs")
        if slot.type_raw64_word != words[expected_type_offset]:
            raise ValueError("reference initializer raw-slot type word differs")
        expected_type_position = _quota_position(
            slot.type_raw64_word,
            manifest.type_cumulative_ends,
        )
        if slot.type_quota_position != expected_type_position:
            raise ValueError("reference initializer raw-slot type transform differs")
        expected_type = manifest.type_ids[expected_type_position]
        if slot.event_type != expected_type:
            raise ValueError("reference initializer raw-slot event type differs")
        if slot.event_dimension != dimension_by_type[expected_type]:
            raise ValueError("reference initializer raw-slot dimension differs")
        expected_coordinate_offsets = tuple(
            manifest.coordinate_segment_offset
            + position * manifest.coordinate_row_stride
            + coordinate_index
            for coordinate_index in range(manifest.maximum_coordinate_dimension)
        )
        if slot.coordinate_word_count != manifest.maximum_coordinate_dimension:
            raise ValueError("reference initializer raw-slot coordinate count differs")
        if slot.coordinate_word_offsets != expected_coordinate_offsets:
            raise ValueError("reference initializer raw-slot coordinate offsets differ")
        if slot.coordinate_raw64_words != tuple(
            words[offset] for offset in expected_coordinate_offsets
        ):
            raise ValueError("reference initializer raw-slot coordinate words differ")
        occupied_offsets.append(expected_type_offset)
        occupied_offsets.extend(expected_coordinate_offsets)
    if len(set(occupied_offsets)) != total_words or tuple(
        sorted(occupied_offsets)
    ) != tuple(range(total_words)):
        raise ValueError("reference initializer word-role partition differs")
    if len(values["selected_raw_events"]) != cardinality:
        raise ValueError("reference initializer selected-event count differs")
    if len(values["selected_raw_event_sha256s"]) != cardinality:
        raise ValueError("reference initializer selected-event digest count differs")
    for position, digest in enumerate(values["selected_raw_event_sha256s"]):
        _protocol._thinning._require_sha256(
            digest,
            name="result.selected_raw_event_sha256s[%d]" % position,
        )
    for position, event in enumerate(values["selected_raw_events"]):
        if type(event) is not TransformedEvent:
            raise TypeError(
                "result.selected_raw_events[%d] has the wrong exact type" % position
            )
    for position, raw_position in enumerate(values["canonical_position_to_raw_slot"]):
        checked_position = _exact_nonnegative_integer(
            raw_position,
            name="result.canonical_position_to_raw_slot[%d]" % position,
        )
        if checked_position >= manifest.total_cap:
            raise ValueError("reference initializer canonical map exceeds the cap")
    for position, canonical_position in enumerate(
        values["raw_slot_to_canonical_position"]
    ):
        if canonical_position is None:
            continue
        checked_position = _exact_nonnegative_integer(
            canonical_position,
            name="result.raw_slot_to_canonical_position[%d]" % position,
        )
        if checked_position >= cardinality:
            raise ValueError("reference initializer inverse map exceeds cardinality")
    for position, event in enumerate(values["canonical_configuration"]):
        if type(event) is not TransformedEvent:
            raise TypeError(
                "result.canonical_configuration[%d] has the wrong exact type" % position
            )
    for position, event in enumerate(values["selected_raw_events"]):
        if event is not values["raw_slots"][position].event:
            raise ValueError("reference initializer selected-event identity differs")
        if values["selected_raw_event_sha256s"][position] != _event_sha256(event):
            raise ValueError("reference initializer selected-event digest differs")
    canonical_order = tuple(
        sorted(
            range(cardinality),
            key=lambda index: (
                values["raw_slots"][index].event.model_key(),
                index,
            ),
        )
    )
    if values["canonical_position_to_raw_slot"] != canonical_order:
        raise ValueError("reference initializer canonical-to-raw map differs")
    raw_to_canonical = [None] * manifest.total_cap
    for canonical_position, raw_position in enumerate(canonical_order):
        raw_to_canonical[raw_position] = canonical_position
    if values["raw_slot_to_canonical_position"] != tuple(raw_to_canonical):
        raise ValueError("reference initializer raw-to-canonical map differs")
    if len(values["canonical_configuration"]) != cardinality:
        raise ValueError("reference initializer canonical count differs")
    for canonical_position, raw_position in enumerate(canonical_order):
        if (
            values["canonical_configuration"][canonical_position]
            is not values["raw_slots"][raw_position].event
        ):
            raise ValueError("reference initializer canonical event identity differs")
    expected_canonical = tuple(
        values["raw_slots"][raw_position].event for raw_position in canonical_order
    )
    if values["canonical_configuration"] != expected_canonical:
        raise ValueError("reference initializer canonical configuration differs")
    if values["canonical_configuration_sha256"] != _configuration_sha256(
        values["canonical_configuration"]
    ):
        raise ValueError("reference initializer configuration digest differs")
    for name in (
        "exact_fixed_layout_consumed",
        "all_raw_slot_transforms_completed_before_cardinality_decoding",
        "duplicate_stable_canonical_bijection",
        "finite_product_uniform_pushforward_only",
        "no_caller_rng",
    ):
        if _exact_bool(values[name], name="result.%s" % name) is not True:
            raise ValueError("reference initializer result flag %s differs" % name)
    expected_digest = _protocol._thinning._semantic_digest(_result_payload(values))
    if values["result_sha256"] != expected_digest:
        raise ValueError("reference initializer result digest differs")
    return value


def _make_result(
    certificate: CounterKeyedReferenceInitializerCertificate,
    manifest: FiniteResolutionCappedPoissonManifest,
    parent: _protocol.CounterKeyedInitializerProtocolResult,
) -> CounterKeyedReferenceInitializerResult:
    raw_blocks = tuple(entry.raw64_words for entry in parent.entries)
    block_offsets = [0]
    for block in raw_blocks:
        block_offsets.append(block_offsets[-1] + len(block))
    words = tuple(word for block in raw_blocks for word in block)
    materialized_slot_fields = tuple(
        _materialize_slot_fields(
            manifest,
            words,
            raw_slot_index=raw_slot_index,
        )
        for raw_slot_index in range(manifest.total_cap)
    )
    count_word = words[manifest.count_word_offset]
    cardinality = _quota_position(count_word, manifest.count_cumulative_ends)
    slots = tuple(
        _make_slot(
            certificate,
            manifest,
            materialized_fields,
            active=raw_slot_index < cardinality,
        )
        for raw_slot_index, materialized_fields in enumerate(materialized_slot_fields)
    )
    selected = tuple(slot.event for slot in slots[:cardinality])
    canonical_order = tuple(
        sorted(
            range(cardinality),
            key=lambda index: (slots[index].event.model_key(), index),
        )
    )
    canonical = tuple(slots[index].event for index in canonical_order)
    raw_to_canonical = [None] * manifest.total_cap
    for canonical_position, raw_position in enumerate(canonical_order):
        raw_to_canonical[raw_position] = canonical_position
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION
        ),
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "manifest": manifest,
        "manifest_sha256": manifest.manifest_sha256,
        "parent_protocol_result": parent,
        "parent_result_sha256": parent.result_sha256,
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "parent_block_count": len(raw_blocks),
        "parent_entry_sha256s": parent.entry_sha256s,
        "raw64_blocks": raw_blocks,
        "raw64_block_offsets": tuple(block_offsets),
        "concatenated_raw64_words": words,
        "total_raw64_words": len(words),
        "count_word_offset": manifest.count_word_offset,
        "count_raw64_word": count_word,
        "count_quota_position": cardinality,
        "sampled_cardinality": cardinality,
        "raw_slots": slots,
        "raw_slot_sha256s": tuple(slot.slot_sha256 for slot in slots),
        "selected_raw_events": selected,
        "selected_raw_event_sha256s": tuple(_event_sha256(event) for event in selected),
        "canonical_configuration": canonical,
        "canonical_configuration_sha256": _configuration_sha256(canonical),
        "canonical_position_to_raw_slot": canonical_order,
        "raw_slot_to_canonical_position": tuple(raw_to_canonical),
        "exact_fixed_layout_consumed": True,
        "all_raw_slot_transforms_completed_before_cardinality_decoding": True,
        "duplicate_stable_canonical_bijection": True,
        "finite_product_uniform_pushforward_only": True,
        "no_caller_rng": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _protocol._thinning._semantic_digest(
        _result_payload(values)
    )
    return CounterKeyedReferenceInitializerResult(
        **values,
        _construction_token=_RESULT_TOKEN,
    )


class CounterKeyedReferenceInitializerOwner:
    """Immutable owner of one ancestry-bound finite reference transformer."""

    __slots__ = (
        "_protocol_owner",
        "_certified_protocol_owner",
        "_reference_composer",
        "_certified_reference_composer",
        "_process",
        "_certified_process",
        "_reference",
        "_certified_reference",
        "_reference_parameter_sha256",
        "_certified_reference_parameter_sha256",
        "_initializer_role_sha256",
        "_certified_initializer_role_sha256",
        "_manifest",
        "_certified_manifest",
        "_certificate",
        "_certified_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedReferenceInitializerOwner cannot be subclassed")

    def __init__(
        self,
        protocol_owner: _protocol.CounterKeyedInitializerProtocolOwner,
        reference_composer: ProcessValidReferenceJumpComposer,
        process: ReversibleHybridReference,
        reference: CappedPoissonConfigurationReference,
        initializer_role_sha256: str,
        manifest: FiniteResolutionCappedPoissonManifest,
        certificate: CounterKeyedReferenceInitializerCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("reference initializer owners require certification")
        if type(protocol_owner) is not _protocol.CounterKeyedInitializerProtocolOwner:
            raise TypeError("protocol_owner has the wrong exact checkpoint-27 type")
        if type(reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference_composer has the wrong exact type")
        if type(process) is not ReversibleHybridReference:
            raise TypeError("process has the wrong exact type")
        if type(reference) is not CappedPoissonConfigurationReference:
            raise TypeError("reference has the wrong exact type")
        role = _protocol._thinning._require_sha256(
            initializer_role_sha256, name="initializer_role_sha256"
        )
        checked_manifest = _validate_manifest(manifest)
        checked_certificate = _validate_certificate(certificate)
        if checked_manifest.reference is not reference:
            raise ValueError("reference initializer manifest uses another reference")
        if checked_certificate.manifest is not checked_manifest:
            raise ValueError("reference initializer certificate uses another manifest")
        if checked_certificate.initializer_role_sha256 != role:
            raise ValueError("reference initializer role differs from certificate")
        reference_digest = _reference_parameter_sha256(reference)
        object.__setattr__(self, "_protocol_owner", protocol_owner)
        object.__setattr__(self, "_certified_protocol_owner", protocol_owner)
        object.__setattr__(self, "_reference_composer", reference_composer)
        object.__setattr__(self, "_certified_reference_composer", reference_composer)
        object.__setattr__(self, "_process", process)
        object.__setattr__(self, "_certified_process", process)
        object.__setattr__(self, "_reference", reference)
        object.__setattr__(self, "_certified_reference", reference)
        object.__setattr__(self, "_reference_parameter_sha256", reference_digest)
        object.__setattr__(
            self,
            "_certified_reference_parameter_sha256",
            reference_digest,
        )
        object.__setattr__(self, "_initializer_role_sha256", role)
        object.__setattr__(self, "_certified_initializer_role_sha256", role)
        object.__setattr__(self, "_manifest", checked_manifest)
        object.__setattr__(self, "_certified_manifest", checked_manifest)
        object.__setattr__(self, "_certificate", checked_certificate)
        object.__setattr__(self, "_certified_certificate", checked_certificate)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("reference initializer owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("reference initializer owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("reference initializer owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedReferenceInitializerCertificate:
        return self._certificate

    @property
    def manifest(self) -> FiniteResolutionCappedPoissonManifest:
        return self._manifest

    @property
    def protocol_owner(self) -> _protocol.CounterKeyedInitializerProtocolOwner:
        return self._protocol_owner

    def _require_live_binding(
        self,
    ) -> CounterKeyedReferenceInitializerCertificate:
        _protocol._thinning._require_binary64_environment()
        if self._protocol_owner is not self._certified_protocol_owner:
            raise ValueError("reference initializer checkpoint-27 owner changed")
        if self._reference_composer is not self._certified_reference_composer:
            raise ValueError("reference initializer composer binding changed")
        if self._process is not self._certified_process:
            raise ValueError("reference initializer process binding changed")
        if self._reference is not self._certified_reference:
            raise ValueError("reference initializer reference binding changed")
        if self._manifest is not self._certified_manifest:
            raise ValueError("reference initializer manifest binding changed")
        if self._certificate is not self._certified_certificate:
            raise ValueError("reference initializer certificate binding changed")
        for name, digest in (
            ("initializer_role_sha256", self._initializer_role_sha256),
            (
                "certified_initializer_role_sha256",
                self._certified_initializer_role_sha256,
            ),
            ("reference_parameter_sha256", self._reference_parameter_sha256),
            (
                "certified_reference_parameter_sha256",
                self._certified_reference_parameter_sha256,
            ),
        ):
            _protocol._thinning._require_sha256(
                digest,
                name="owner.%s" % name,
            )
        if self._initializer_role_sha256 != self._certified_initializer_role_sha256:
            raise ValueError("reference initializer certified role changed")
        composer, process, reference = _reference_ancestry(self._protocol_owner)
        if composer is not self._reference_composer:
            raise ValueError("reference initializer ancestry composer changed")
        if process is not self._process:
            raise ValueError("reference initializer ancestry process changed")
        if reference is not self._reference:
            raise ValueError("reference initializer ancestry reference changed")
        live_reference_digest = _reference_parameter_sha256(reference)
        if (
            live_reference_digest != self._reference_parameter_sha256
            or live_reference_digest != self._certified_reference_parameter_sha256
        ):
            raise ValueError("reference initializer reference parameters changed")
        manifest = _validate_manifest(self._manifest)
        if manifest.reference is not reference:
            raise ValueError("reference initializer manifest ancestry changed")
        parent = self._protocol_owner._require_live_binding()
        certificate = _validate_certificate(self._certificate)
        if certificate.checkpoint27_certificate is not parent:
            raise ValueError("reference initializer parent certificate changed")
        if certificate.manifest is not manifest:
            raise ValueError("reference initializer certificate manifest changed")
        if certificate.initializer_runtime_sha256 != _runtime_sha256():
            raise ValueError("live reference initializer runtime differs")
        expected = _make_certificate(
            parent,
            manifest,
            initializer_role_sha256=self._initializer_role_sha256,
        )
        for name in _certificate_fields():
            actual_value = getattr(certificate, name)
            expected_value = getattr(expected, name)
            if name in ("checkpoint27_certificate", "manifest"):
                if actual_value is not expected_value:
                    raise ValueError(
                        "reference initializer certificate %s identity differs" % name
                    )
            elif not _protocol._thinning._field_matches(
                name, actual_value, expected_value
            ):
                raise ValueError(
                    "reference initializer certificate field %s differs" % name
                )
        _protocol._thinning._require_binary64_environment()
        return certificate

    def initialize(
        self,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedReferenceInitializerResult:
        """Allocate and transform one complete fixed reference capsule."""

        self._require_live_binding()
        checked_run = _protocol._lineage._exact_uint64(run_id, name="run_id")
        checked_initialization = _protocol._lineage._exact_uint64(
            initialization_index, name="initialization_index"
        )
        parent = self.protocol_owner.allocate(
            checked_run,
            checked_initialization,
            strategy=_protocol.INITIALIZER_STRATEGY_REFERENCE,
            strategy_budget=1,
            work_item_raw64_word_counts=(
                self.manifest.canonical_block_raw64_word_counts
            ),
            selection_raw64_word_count=0,
        )
        result = _make_result(self.certificate, self.manifest, parent)
        self.validate_result(result, checked_run, checked_initialization)
        return result

    def validate_result(
        self,
        result: CounterKeyedReferenceInitializerResult,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedReferenceInitializerResult:
        """Deeply replay one finite initializer result and its checkpoint 27 parent."""

        self._require_live_binding()
        checked_run = _protocol._lineage._exact_uint64(run_id, name="run_id")
        checked_initialization = _protocol._lineage._exact_uint64(
            initialization_index, name="initialization_index"
        )
        if type(result) is not CounterKeyedReferenceInitializerResult:
            raise TypeError("result has the wrong exact reference initializer type")
        _bounded_exact_tuple(
            result.raw_slots,
            name="result.raw_slots",
            maximum_items=COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS,
        )
        _bounded_exact_tuple(
            result.concatenated_raw64_words,
            name="result.concatenated_raw64_words",
            maximum_items=_PARENT_MAXIMUM_TOTAL_WORDS,
        )
        checked = _validate_result_record(result)
        result_fields = _result_fields()
        result_before = _protocol._control._capture_fields(result, result_fields)
        manifest_fields = _manifest_fields()
        manifest_before = _protocol._control._capture_fields(
            checked.manifest, manifest_fields
        )
        slot_fields = _slot_fields()
        slot_befores = tuple(
            _protocol._control._capture_fields(slot, slot_fields)
            for slot in checked.raw_slots
        )
        parent = checked.parent_protocol_result
        parent_fields = _protocol._result_fields()
        parent_before = _protocol._control._capture_fields(parent, parent_fields)
        parent_entry_fields = _protocol._entry_fields()
        parent_entry_befores = tuple(
            _protocol._control._capture_fields(entry, parent_entry_fields)
            for entry in parent.entries
        )
        if checked.certificate is not self.certificate:
            raise ValueError("reference initializer result belongs to another owner")
        if checked.manifest is not self.manifest:
            raise ValueError("reference initializer result uses another manifest")
        if parent.certificate is not self.protocol_owner.certificate:
            raise ValueError("reference initializer parent belongs to another owner")
        if checked.run_id != checked_run or (
            checked.initialization_index != checked_initialization
        ):
            raise ValueError("reference initializer request differs from result")
        self.protocol_owner.validate_result(
            parent,
            checked_run,
            checked_initialization,
            strategy=_protocol.INITIALIZER_STRATEGY_REFERENCE,
            strategy_budget=1,
            work_item_raw64_word_counts=(
                self.manifest.canonical_block_raw64_word_counts
            ),
            selection_raw64_word_count=0,
        )
        expected = _make_result(self.certificate, self.manifest, parent)
        for name in _result_fields():
            actual_value = getattr(checked, name)
            expected_value = getattr(expected, name)
            if name in ("certificate", "manifest", "parent_protocol_result"):
                if actual_value is not expected_value:
                    raise ValueError(
                        "reference initializer result %s identity differs" % name
                    )
            elif name == "raw_slots":
                if len(actual_value) != len(expected_value):
                    raise ValueError("reference initializer raw-slot count changed")
                for position, (actual_slot, expected_slot) in enumerate(
                    zip(actual_value, expected_value)
                ):
                    for field in _slot_fields():
                        actual_field = getattr(actual_slot, field)
                        expected_field = getattr(expected_slot, field)
                        if field == "event":
                            if actual_field.model_key() != expected_field.model_key():
                                raise ValueError(
                                    "reference initializer raw-slot event differs"
                                )
                        elif not _protocol._thinning._field_matches(
                            field, actual_field, expected_field
                        ):
                            raise ValueError(
                                "reference initializer raw-slot %d field %s differs"
                                % (position, field)
                            )
            elif not _protocol._thinning._field_matches(
                name, actual_value, expected_value
            ):
                raise ValueError("reference initializer result field %s differs" % name)
        self._require_live_binding()
        _validate_result_record(result)
        _protocol._control._require_fields_unchanged(
            result,
            result_fields,
            result_before,
            identity_fields=(
                "certificate",
                "manifest",
                "parent_protocol_result",
                "parent_entry_sha256s",
                "raw64_blocks",
                "raw64_block_offsets",
                "concatenated_raw64_words",
                "raw_slots",
                "raw_slot_sha256s",
                "selected_raw_events",
                "selected_raw_event_sha256s",
                "canonical_configuration",
                "canonical_position_to_raw_slot",
                "raw_slot_to_canonical_position",
            ),
            name="reference initializer result",
        )
        _protocol._control._require_fields_unchanged(
            result.manifest,
            manifest_fields,
            manifest_before,
            identity_fields=(
                "reference",
                "reference_parameter_key",
                "type_ids",
                "type_dimensions",
                "count_target_probability_ratios",
                "type_target_probability_ratios",
                "count_dyadic_quotas",
                "count_cumulative_ends",
                "type_dyadic_quotas",
                "type_cumulative_ends",
                "canonical_block_raw64_word_counts",
            ),
            name="reference initializer manifest",
        )
        for position, (slot, before) in enumerate(zip(result.raw_slots, slot_befores)):
            _protocol._control._require_fields_unchanged(
                slot,
                slot_fields,
                before,
                identity_fields=(
                    "coordinate_word_offsets",
                    "coordinate_raw64_words",
                    "coordinate_bucket_indices",
                    "coordinate_midpoint_numerators",
                    "coordinate_probability_hexes",
                    "coordinate_codebook_values",
                    "coordinate_value_hexes",
                    "active_coordinates",
                    "event",
                ),
                name="reference initializer raw slot %d" % position,
            )
        _protocol._control._require_fields_unchanged(
            parent,
            parent_fields,
            parent_before,
            identity_fields=(
                "certificate",
                "control_plan",
                "parent_control_result",
                "entries",
                "entry_sha256s",
            ),
            name="reference initializer checkpoint-27 parent",
        )
        for position, (entry, before) in enumerate(
            zip(parent.entries, parent_entry_befores)
        ):
            _protocol._control._require_fields_unchanged(
                entry,
                parent_entry_fields,
                before,
                identity_fields=("parent_consumption", "raw64_words"),
                name="reference initializer checkpoint-27 entry %d" % position,
            )
        return result


def certify_plugin_bridge_counter_keyed_reference_initializer(
    protocol_owner: _protocol.CounterKeyedInitializerProtocolOwner,
    *,
    initializer_policy: object,
    initializer_role_sha256: object,
) -> CounterKeyedReferenceInitializerOwner:
    """Certify the checkpoint-twenty-eight finite reference transformer."""

    if type(initializer_policy) is not str:
        raise TypeError("initializer_policy must be exact text")
    if initializer_policy != PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY:
        raise ValueError("only the exported reference initializer is supported")
    role = _protocol._thinning._require_sha256(
        initializer_role_sha256, name="initializer_role_sha256"
    )
    composer, process, reference = _reference_ancestry(protocol_owner)
    parent = protocol_owner._require_live_binding()
    manifest = _make_manifest(reference)
    certificate = _make_certificate(
        parent,
        manifest,
        initializer_role_sha256=role,
    )
    owner = CounterKeyedReferenceInitializerOwner(
        protocol_owner,
        composer,
        process,
        reference,
        role,
        manifest,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_counter_keyed_reference_initializer(
    protocol_owner: _protocol.CounterKeyedInitializerProtocolOwner,
    owner: CounterKeyedReferenceInitializerOwner,
    *,
    initializer_policy: object,
    initializer_role_sha256: object,
) -> CounterKeyedReferenceInitializerOwner:
    """Require exact checkpoint-27 identity, policy, role, and live custody."""

    if type(initializer_policy) is not str:
        raise TypeError("initializer_policy must be exact text")
    if initializer_policy != PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY:
        raise ValueError("only the exported reference initializer is supported")
    role = _protocol._thinning._require_sha256(
        initializer_role_sha256, name="initializer_role_sha256"
    )
    if type(owner) is not CounterKeyedReferenceInitializerOwner:
        raise TypeError("owner has the wrong exact reference initializer type")
    if owner.protocol_owner is not protocol_owner:
        raise ValueError("reference initializer owner uses another checkpoint-27 owner")
    owner._require_live_binding()
    if owner.certificate.initializer_role_sha256 != role:
        raise ValueError("reference initializer owner uses another role")
    return owner


def validate_plugin_bridge_counter_keyed_reference_initializer_certificate(
    protocol_owner: _protocol.CounterKeyedInitializerProtocolOwner,
    owner: CounterKeyedReferenceInitializerOwner,
    *,
    initializer_policy: object,
    initializer_role_sha256: object,
) -> CounterKeyedReferenceInitializerCertificate:
    """Return the reconstructed live checkpoint-twenty-eight certificate."""

    return require_matching_plugin_bridge_counter_keyed_reference_initializer(
        protocol_owner,
        owner,
        initializer_policy=initializer_policy,
        initializer_role_sha256=initializer_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCOPE",
    "FINITE_RESOLUTION_REFERENCE_COORDINATE_TRANSFORM",
    "COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS",
    "COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS",
    "COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS",
    "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS",
    "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES",
    "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS",
    "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS",
    "FiniteResolutionCappedPoissonManifest",
    "CounterKeyedReferenceInitializerCertificate",
    "CounterKeyedReferenceInitializerRawSlot",
    "CounterKeyedReferenceInitializerResult",
    "CounterKeyedReferenceInitializerOwner",
    "PluginBridgeCounterKeyedReferenceInitializerError",
    "certify_plugin_bridge_counter_keyed_reference_initializer",
    "require_matching_plugin_bridge_counter_keyed_reference_initializer",
    "validate_plugin_bridge_counter_keyed_reference_initializer_certificate",
]
