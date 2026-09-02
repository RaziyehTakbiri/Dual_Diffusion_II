"""Closed, torch-lazy interface for certified exact initial-score providers.

The kernel-facing object in this module is deliberately an exact sealed owner,
not a duck-typed ``Protocol``.  It admits three source families:

* the bounded operational score produced by a certified
  ``ConfigurationInitialTiltComposer``; and
* the exact known-law score produced by an
  ``ExactRationalQuadraticInitialTilt``; and
* the exact finite-support score produced by the sealed CP55
  ``AtomicQScoreTableProvider``.

All three are projected onto one small contract: an exact rational represented-state
score, one exact global upper envelope, an optional exact global lower envelope,
an exact capped-Poisson reference object, and a context policy.  The source
point record is retained.  Structural validation checks its sealed arithmetic
and custody without running a learned forward pass or consuming randomness;
``validate_evaluation`` is the explicit replaying operation.

The atomic adapter binds the exact stored-binary64 ``T28-A0-Q`` reference and
maps configurations to table keys by counts in ascending reference-type order.
Imports of the PyTorch-backed composer are local to its adapter branch.  Merely
importing this module or using either exact adapter therefore does not require
PyTorch.  Object identity and hashes are local custody witnesses under an
unchanged runtime.  They are not cryptographic code authentication, a proposal-
law proof, a normalization proof, a path/sampler admission, model-quality
evidence, or closure of Formal Test 28.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from types import MappingProxyType
import struct
from typing import Mapping, Optional, Tuple, Union

from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    MAX_CONFIGURATION_CARDINALITY,
    MAX_CONFIGURATION_EVENT_TYPES,
    MAX_REFERENCE_DENSITY_COORDINATES,
    MAX_TRANSFORMED_COORDINATE_DIMENSION,
    TYPE_WEIGHT_SUM_ATOL,
    TransformedConfiguration,
    TransformedEvent,
)


CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCHEMA_VERSION = (
    "certified-initial-score-provider-v1"
)
CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS = (
    "configuration-initial-tilt-composer-v1",
    "exact-rational-quadratic-initial-tilt-v1",
    "atomic-q-score-table-v1",
)
CERTIFIED_INITIAL_SCORE_PROVIDER_V1_CONTEXT_POLICIES = (
    "plan-supplied-fixed-dimension",
    "provider-fixed-exact-context",
)
CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCOPE = (
    "one-sealed-source-adapter;one-exact-capped-poisson-reference-object;"
    "canonical-binary64-represented-configurations;exact-rational-point-score;"
    "exact-count-keyed-finite-atomic-table-source;"
    "one-exact-global-upper-bound;optional-exact-global-lower-bound;"
    "explicit-context-policy;retained-source-point-and-digest;"
    "structural-validation-without-learned-forward-or-RNG-replay;"
    "explicit-full-source-replay-only;trusted-unchanged-runtime;"
    "not-proposal-law-IID-independence-normalization-analytic-target-equality-"
    "posterior-model-quality-path-sampler-or-Formal-Test-28-closure"
)
CERTIFIED_INITIAL_SCORE_PROVIDER_V1_NONCLAIM = (
    "adapter-certification-proves-only-local-custody-exact-represented-point-"
    "score-and-declared-envelope;it-does-not-prove-the-operational-reference-"
    "sampling-law-or-identify-an-atomic-source-artifact-as-an-operational-law-"
    "IID-or-source-independence-any-analytic-Pi_N-equality-a-"
    "normalizer-a-true-conditional-or-posterior-factor-learned-model-quality-"
    "path-or-sampler-validity-generality-or-Formal-Test-28-closure"
)

MAX_CERTIFIED_INITIAL_SCORE_CONTEXT_DIMENSION = 4_096
MAX_CERTIFIED_INITIAL_SCORE_COORDINATES = 100_000
MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS = 16_384
MAX_CERTIFIED_INITIAL_SCORE_DIGEST_NODES = 16_384
MAX_CERTIFIED_INITIAL_SCORE_DIGEST_DEPTH = 64
MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TEXT_BYTES = 65_536
MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TOTAL_TEXT_BYTES = 1_000_000

_BACKEND_COMPOSER = CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS[0]
_BACKEND_EXACT = CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS[1]
_BACKEND_ATOMIC_Q = CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS[2]
_CONTEXT_PLAN = CERTIFIED_INITIAL_SCORE_PROVIDER_V1_CONTEXT_POLICIES[0]
_CONTEXT_FIXED = CERTIFIED_INITIAL_SCORE_PROVIDER_V1_CONTEXT_POLICIES[1]
_ZERO_SHA256 = "0" * 64
_MAX_RUNTIME_IDENTITY = (1 << 64) - 1
_ATOMIC_Q_ACTIVITY = Fraction(1, 1)
_ATOMIC_Q_TYPE_WEIGHTS = (
    Fraction(3_602_879_701_896_397, 1 << 53),
    Fraction(5_404_319_552_844_595, 1 << 53),
)
_ATOMIC_Q_TOTAL_CAP = 2

_COMPOSER_ADAPTER_TOKEN = object()
_EXACT_ADAPTER_TOKEN = object()
_ATOMIC_Q_ADAPTER_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_EVALUATION_TOKEN = object()
_OWNER_TOKEN = object()


class CertifiedInitialScoreProviderV1Error(ArithmeticError):
    """Raised when exact provider projection must fail closed."""


def _require_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("%s must be a lowercase SHA-256 hex digest" % name)
    return value


def _require_exact_text(
    value: object,
    *,
    name: str,
    expected: Optional[str] = None,
) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TEXT_BYTES:
        raise ValueError("%s exceeds the text-length limit" % name)
    if expected is not None and value != expected:
        raise ValueError("%s differs" % name)
    return value


def _require_runtime_identity(value: object, *, name: str) -> int:
    if (
        type(value) is not int
        or isinstance(value, bool)
        or not 0 <= value <= _MAX_RUNTIME_IDENTITY
    ):
        raise ValueError("%s is outside the runtime-identity domain" % name)
    return value


def _require_exact_integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s lies outside the supported interval" % name)
    return value


def _require_fraction(value: object, *, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError("%s must be an exact Fraction" % name)
    if (
        value.numerator.bit_length() > MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS
        or value.denominator.bit_length()
        > MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS
    ):
        raise CertifiedInitialScoreProviderV1Error(
            "%s exceeds the exact-integer resource limit" % name
        )
    return value


def _fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    bound = 1 << MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS
    checked_numerator = _require_exact_integer(
        numerator,
        name="%s.numerator" % name,
        minimum=-bound,
        maximum=bound,
    )
    checked_denominator = _require_exact_integer(
        denominator,
        name="%s.denominator" % name,
        minimum=1,
        maximum=bound,
    )
    result = Fraction(checked_numerator, checked_denominator)
    if (
        result.numerator != checked_numerator
        or result.denominator != checked_denominator
    ):
        raise ValueError("%s fraction parts are not reduced" % name)
    return _require_fraction(result, name=name)


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


def _same_optional_float(left: object, right: object) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return _same_float(left, right)


def _charge_digest_text_bytes(byte_count: int, budget: list) -> None:
    if byte_count > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TEXT_BYTES:
        raise CertifiedInitialScoreProviderV1Error(
            "semantic-digest text exceeds the byte limit"
        )
    budget[1] += byte_count
    if budget[1] > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TOTAL_TEXT_BYTES:
        raise CertifiedInitialScoreProviderV1Error(
            "semantic-digest input exceeds the cumulative text-byte limit"
        )


def _bounded_digest_integer_text(value: int, budget: list) -> str:
    # 30103 / 100000 is a strict decimal upper approximation to log10(2).
    magnitude_bits = abs(value).bit_length()
    estimated_digits = (
        1 if magnitude_bits == 0 else (magnitude_bits * 30_103 // 100_000 + 2)
    )
    estimated_bytes = estimated_digits + (1 if value < 0 else 0)
    _charge_digest_text_bytes(estimated_bytes, budget)
    if value == 0:
        return "0"
    remaining = abs(value)
    blocks = []
    while remaining:
        remaining, block = divmod(remaining, 1_000_000_000)
        blocks.append(block)
    pieces = [str(blocks.pop())]
    pieces.extend("%09d" % block for block in reversed(blocks))
    text = "".join(pieces)
    return "-" + text if value < 0 else text


def _typed(
    value: object,
    *,
    _depth: int = 0,
    _node_counter: Optional[list] = None,
) -> object:
    if _node_counter is None:
        # Mutable two-word budget: visited nodes and cumulative UTF-8 text bytes.
        _node_counter = [0, 0]
    _node_counter[0] += 1
    if _node_counter[0] > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_NODES:
        raise CertifiedInitialScoreProviderV1Error(
            "semantic-digest input exceeds the node limit"
        )
    if _depth > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_DEPTH:
        raise CertifiedInitialScoreProviderV1Error(
            "semantic-digest input exceeds the depth limit"
        )
    if value is None:
        return {"type": "none"}
    if type(value) is bool:
        return {"type": "bool", "value": value}
    if type(value) is int:
        if value.bit_length() > MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS:
            raise CertifiedInitialScoreProviderV1Error(
                "semantic-digest integer exceeds the bit limit"
            )
        return {
            "type": "int",
            "value": _bounded_digest_integer_text(value, _node_counter),
        }
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("semantic digests accept only finite floats")
        return {"type": "float64", "value": value.hex()}
    if type(value) is str:
        if len(value) > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TEXT_BYTES:
            raise CertifiedInitialScoreProviderV1Error(
                "semantic-digest text exceeds the character limit"
            )
        encoded_length = len(value.encode("utf-8"))
        _charge_digest_text_bytes(encoded_length, _node_counter)
        return {"type": "str", "value": value}
    if type(value) is Fraction:
        _require_fraction(value, name="semantic-digest fraction")
        return {
            "type": "fraction",
            "numerator": _bounded_digest_integer_text(value.numerator, _node_counter),
            "denominator": _bounded_digest_integer_text(
                value.denominator, _node_counter
            ),
        }
    if type(value) is tuple:
        if len(value) > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_NODES:
            raise CertifiedInitialScoreProviderV1Error(
                "semantic-digest tuple exceeds the item limit"
            )
        return {
            "type": "tuple",
            "items": [
                _typed(item, _depth=_depth + 1, _node_counter=_node_counter)
                for item in value
            ],
        }
    if type(value) is dict or type(value) is MappingProxyType:
        if len(value) > MAX_CERTIFIED_INITIAL_SCORE_DIGEST_NODES:
            raise CertifiedInitialScoreProviderV1Error(
                "semantic-digest mapping exceeds the item limit"
            )
        items = []
        for key, item in value.items():
            items.append(
                (
                    _typed(
                        key,
                        _depth=_depth + 1,
                        _node_counter=_node_counter,
                    ),
                    _typed(
                        item,
                        _depth=_depth + 1,
                        _node_counter=_node_counter,
                    ),
                )
            )
        items.sort(
            key=lambda pair: json.dumps(
                pair[0], sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
        )
        return {"type": "mapping", "items": items}
    raise TypeError("unsupported semantic-digest value %s" % type(value).__name__)


def _bounded_exact_integer_mapping_keys(
    value: object,
    *,
    name: str,
    maximum_items: int,
) -> Tuple[int, ...]:
    if type(value) is not MappingProxyType:
        raise TypeError("%s must be an exact mapping proxy" % name)
    if len(value) > maximum_items:
        raise ValueError("%s exceeds the key-count limit" % name)
    keys = []
    for key in value:
        keys.append(
            _require_exact_integer(
                key,
                name="%s key" % name,
                minimum=0,
                maximum=(1 << 63) - 1,
            )
        )
    return tuple(keys)


def _semantic_digest(payload: Mapping[str, object], *, domain: bytes) -> str:
    encoded = json.dumps(
        _typed(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(encoded)
    return digest.hexdigest()


def _validate_live_reference(
    reference: object,
) -> CappedPoissonConfigurationReference:
    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("reference must be an exact capped-Poisson reference")
    if type(reference.type_ids) is not tuple:
        raise TypeError("reference type_ids must be an exact tuple")
    if not 1 <= len(reference.type_ids) <= MAX_CONFIGURATION_EVENT_TYPES:
        raise ValueError("reference type count lies outside the supported range")
    checked_ids = []
    for type_id in reference.type_ids:
        checked_ids.append(
            _require_exact_integer(
                type_id,
                name="reference type id",
                minimum=0,
                maximum=(1 << 63) - 1,
            )
        )
    if tuple(checked_ids) != tuple(sorted(set(checked_ids))):
        raise ValueError("reference type ids must be sorted and unique")
    expected_ids = tuple(checked_ids)
    if type(reference.type_dimensions) is not MappingProxyType:
        raise TypeError("reference dimensions must be a mapping proxy")
    if type(reference.type_weights) is not MappingProxyType:
        raise TypeError("reference weights must be a mapping proxy")
    dimension_keys = _bounded_exact_integer_mapping_keys(
        reference.type_dimensions,
        name="reference dimensions",
        maximum_items=MAX_CONFIGURATION_EVENT_TYPES,
    )
    weight_keys = _bounded_exact_integer_mapping_keys(
        reference.type_weights,
        name="reference weights",
        maximum_items=MAX_CONFIGURATION_EVENT_TYPES,
    )
    if tuple(sorted(dimension_keys)) != expected_ids:
        raise ValueError("reference dimension keys differ from type ids")
    if tuple(sorted(weight_keys)) != expected_ids:
        raise ValueError("reference weight keys differ from type ids")
    for type_id in expected_ids:
        _require_exact_integer(
            reference.type_dimensions[type_id],
            name="reference type dimension",
            minimum=0,
            maximum=MAX_TRANSFORMED_COORDINATE_DIMENSION,
        )
    _require_exact_integer(
        reference.total_cap,
        name="reference total cap",
        minimum=0,
        maximum=MAX_CONFIGURATION_CARDINALITY,
    )
    if type(reference.activity) is not float or not math.isfinite(reference.activity):
        raise TypeError("reference activity must be a finite built-in float")
    if reference.activity <= 0.0:
        raise ValueError("reference activity must be strictly positive")
    minimum_normal = float.fromhex("0x1.0000000000000p-1022")
    weights = []
    for type_id in expected_ids:
        weight = reference.type_weights[type_id]
        if type(weight) is not float or not math.isfinite(weight):
            raise TypeError("reference weights must be finite built-in floats")
        if weight < minimum_normal:
            raise ValueError("reference weights must be positive normal floats")
        weights.append(weight)
    if not math.isclose(
        math.fsum(weights),
        1.0,
        rel_tol=0.0,
        abs_tol=TYPE_WEIGHT_SUM_ATOL,
    ):
        raise ValueError("reference weights do not sum to one")
    if type(reference.parameter_key()) is not tuple:
        raise TypeError("reference parameter key must be an exact tuple")
    return reference


def _reference_parameter_sha256(
    reference: CappedPoissonConfigurationReference,
) -> str:
    checked = _validate_live_reference(reference)
    return _semantic_digest(
        {"parameter_key": checked.parameter_key()},
        domain=b"heterodiff-certified-initial-score-reference-v1\x00",
    )


def _configuration_sha256(configuration: TransformedConfiguration) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-certified-initial-score-state-v1\x00")
    digest.update(len(configuration).to_bytes(8, "big", signed=False))
    for occurrence, event in enumerate(configuration):
        digest.update(occurrence.to_bytes(8, "big", signed=False))
        digest.update(event.event_type.to_bytes(8, "big", signed=False))
        digest.update(len(event.coordinates).to_bytes(8, "big", signed=False))
        for coordinate in event.coordinates:
            digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _context_sha256(context: Tuple[float, ...]) -> str:
    return _semantic_digest(
        {"residual_context": context},
        domain=b"heterodiff-certified-initial-score-context-v1\x00",
    )


def _canonical_configuration(
    reference: CappedPoissonConfigurationReference,
    configuration: object,
) -> TransformedConfiguration:
    _validate_live_reference(reference)
    if type(configuration) is not tuple:
        raise TypeError("configuration must be an exact tuple")
    if len(configuration) > reference.total_cap:
        raise ValueError("configuration cardinality exceeds the reference cap")
    checked = []
    coordinate_count = 0
    for event_index, event in enumerate(configuration):
        if type(event) is not TransformedEvent:
            raise TypeError("configuration must contain exact TransformedEvent values")
        if type(event.event_type) is not int or isinstance(event.event_type, bool):
            raise TypeError("event_type must be an exact integer")
        if event.event_type not in reference.type_ids:
            raise ValueError("configuration contains an unknown event type")
        if type(event.coordinates) is not tuple:
            raise TypeError("event coordinates must be an exact tuple")
        expected_dimension = reference.type_dimensions[event.event_type]
        if len(event.coordinates) != expected_dimension:
            raise ValueError("event coordinates have the wrong dimension")
        coordinates = []
        for coordinate_index, coordinate in enumerate(event.coordinates):
            if type(coordinate) is not float:
                raise TypeError(
                    "coordinate %d of event %d must be an exact built-in float"
                    % (coordinate_index, event_index)
                )
            if not math.isfinite(coordinate):
                raise ValueError("event coordinates must be finite")
            if coordinate == 0.0 and math.copysign(1.0, coordinate) < 0.0:
                raise ValueError("event coordinates must use canonical positive zero")
            coordinates.append(coordinate)
        coordinate_count += len(coordinates)
        if coordinate_count > MAX_REFERENCE_DENSITY_COORDINATES:
            raise ValueError("configuration exceeds the reference coordinate limit")
        if coordinate_count > MAX_CERTIFIED_INITIAL_SCORE_COORDINATES:
            raise CertifiedInitialScoreProviderV1Error(
                "configuration exceeds the provider coordinate-work limit"
            )
        rebuilt = TransformedEvent(event.event_type, tuple(coordinates))
        if rebuilt.event_type != event.event_type or rebuilt.coordinates != (
            event.coordinates
        ):
            raise ValueError("event is not canonically represented")
        checked.append(rebuilt)
    canonical = tuple(sorted(checked, key=TransformedEvent.model_key))
    if reference.canonicalize(canonical) != canonical:
        raise ValueError("reference canonicalization changed a validated state")
    _configuration_sha256(canonical)
    return canonical


def _validated_context(
    context: object,
    *,
    dimension: int,
    name: str,
) -> Tuple[float, ...]:
    checked_dimension = _require_exact_integer(
        dimension,
        name="%s dimension" % name,
        minimum=0,
        maximum=MAX_CERTIFIED_INITIAL_SCORE_CONTEXT_DIMENSION,
    )
    if type(context) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(context) != checked_dimension:
        raise ValueError("%s has the wrong dimension" % name)
    checked = []
    for value in context:
        if type(value) is not float or not math.isfinite(value):
            raise TypeError("%s must contain finite built-in floats" % name)
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("%s must use canonical positive zero" % name)
        checked.append(value)
    return tuple(checked)


@dataclass(frozen=True)
class _BackendState:
    backend_kind: str
    source_owner: object
    source_certificate: object
    source_certificate_sha256: str
    source_parameter_key: Tuple[object, ...]
    reference: CappedPoissonConfigurationReference
    residual_context_policy: str
    residual_context_dimension: int
    fixed_residual_context: Optional[Tuple[float, ...]]
    exact_log_weight_upper_bound: Fraction
    exact_log_weight_lower_bound: Optional[Fraction]
    learned_operational_surrogate_source: bool
    handcrafted_known_law_source: bool
    ideal_real_extension_declared: bool
    represented_restriction_identity_verified: bool
    certificate_digest_cross_process_stable: bool


class ConfigurationInitialTiltComposerScoreAdapterV1:
    """Sealed lazy adapter for one exact CP30 composer owner."""

    __slots__ = (
        "_source",
        "_source_identity",
        "_source_certificate_identity",
        "_reference_identity",
        "_adapter_role_sha256",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("composer score adapters cannot be subclassed")

    def __init__(
        self,
        *,
        source: object,
        adapter_role_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _COMPOSER_ADAPTER_TOKEN:
            raise TypeError("composer score adapters require certification")
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_source_identity", source)
        state = _composer_backend_state(self, require_sentinels=False)
        object.__setattr__(
            self, "_source_certificate_identity", state.source_certificate
        )
        object.__setattr__(self, "_reference_identity", state.reference)
        object.__setattr__(
            self,
            "_adapter_role_sha256",
            _require_sha256(adapter_role_sha256, name="adapter_role_sha256"),
        )
        _composer_backend_state(self)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("composer score adapters are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("composer score adapters are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("composer score adapters are not pickle objects")

    @property
    def source(self) -> object:
        _composer_backend_state(self)
        return self._source

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        return _composer_backend_state(self).reference

    @property
    def adapter_role_sha256(self) -> str:
        _composer_backend_state(self)
        return self._adapter_role_sha256

    def parameter_key(self) -> Tuple[object, ...]:
        state = _composer_backend_state(self)
        return (
            "configuration-initial-tilt-composer-score-adapter-v1",
            state.source_parameter_key,
            self._adapter_role_sha256,
        )


class ExactRationalQuadraticInitialTiltScoreAdapterV1:
    """Sealed lazy adapter for one exact known-law score owner."""

    __slots__ = (
        "_source",
        "_source_identity",
        "_source_certificate_identity",
        "_reference_identity",
        "_adapter_role_sha256",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("exact score adapters cannot be subclassed")

    def __init__(
        self,
        *,
        source: object,
        adapter_role_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _EXACT_ADAPTER_TOKEN:
            raise TypeError("exact score adapters require certification")
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_source_identity", source)
        state = _exact_backend_state(self, require_sentinels=False)
        object.__setattr__(
            self, "_source_certificate_identity", state.source_certificate
        )
        object.__setattr__(self, "_reference_identity", state.reference)
        object.__setattr__(
            self,
            "_adapter_role_sha256",
            _require_sha256(adapter_role_sha256, name="adapter_role_sha256"),
        )
        _exact_backend_state(self)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("exact score adapters are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("exact score adapters are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("exact score adapters are not pickle objects")

    @property
    def source(self) -> object:
        _exact_backend_state(self)
        return self._source

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        return _exact_backend_state(self).reference

    @property
    def adapter_role_sha256(self) -> str:
        _exact_backend_state(self)
        return self._adapter_role_sha256

    def parameter_key(self) -> Tuple[object, ...]:
        state = _exact_backend_state(self)
        return (
            "exact-rational-quadratic-initial-tilt-score-adapter-v1",
            state.source_parameter_key,
            self._adapter_role_sha256,
        )


class AtomicQScoreTableAdapterV1:
    """Sealed count-keyed adapter for the exact CP55 ``T28-A0-Q`` table."""

    __slots__ = (
        "_source",
        "_source_identity",
        "_source_certificate_identity",
        "_reference",
        "_reference_identity",
        "_adapter_role_sha256",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("atomic score-table adapters cannot be subclassed")

    def __init__(
        self,
        *,
        source: object,
        reference: CappedPoissonConfigurationReference,
        adapter_role_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _ATOMIC_Q_ADAPTER_TOKEN:
            raise TypeError("atomic score-table adapters require certification")
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_source_identity", source)
        object.__setattr__(self, "_source_certificate_identity", source)
        object.__setattr__(self, "_reference", reference)
        object.__setattr__(self, "_reference_identity", reference)
        object.__setattr__(
            self,
            "_adapter_role_sha256",
            _require_sha256(adapter_role_sha256, name="adapter_role_sha256"),
        )
        _atomic_q_backend_state(self)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("atomic score-table adapters are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("atomic score-table adapters are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("atomic score-table adapters are not pickle objects")

    @property
    def source(self) -> object:
        _atomic_q_backend_state(self)
        return self._source

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        return _atomic_q_backend_state(self).reference

    @property
    def adapter_role_sha256(self) -> str:
        _atomic_q_backend_state(self)
        return self._adapter_role_sha256

    def parameter_key(self) -> Tuple[object, ...]:
        state = _atomic_q_backend_state(self)
        return (
            "atomic-q-score-table-adapter-v1",
            state.source_parameter_key,
            state.reference.parameter_key(),
            self._adapter_role_sha256,
        )


CertifiedInitialScoreBackendAdapterV1 = Union[
    ConfigurationInitialTiltComposerScoreAdapterV1,
    ExactRationalQuadraticInitialTiltScoreAdapterV1,
    AtomicQScoreTableAdapterV1,
]


def _composer_backend_state(
    adapter: ConfigurationInitialTiltComposerScoreAdapterV1,
    *,
    require_sentinels: bool = True,
) -> _BackendState:
    # Local import is the critical torch-lazy boundary.
    from heterodiff.models import (
        configuration_initial_tilt_composer_torch as source_module,
    )

    if type(adapter) is not ConfigurationInitialTiltComposerScoreAdapterV1:
        raise TypeError("composer adapter has the wrong exact type")
    source = adapter._source
    if type(source) is not source_module.ConfigurationInitialTiltComposer:
        raise TypeError("composer adapter source has the wrong exact type")
    if require_sentinels and source is not adapter._source_identity:
        raise ValueError("composer adapter source identity sentinel differs")
    snapshot = source._owner_snapshot()
    source._live_components(snapshot)
    certificate = source_module._validate_certificate(source.certificate)
    reference = source.reference_composer.process.reference
    reference = _validate_live_reference(reference)
    if require_sentinels:
        if certificate is not adapter._source_certificate_identity:
            raise ValueError("composer adapter certificate identity differs")
        if reference is not adapter._reference_identity:
            raise ValueError("composer adapter reference identity differs")
    source_key = source.parameter_key()
    if type(source_key) is not tuple:
        raise TypeError("composer source parameter key must be an exact tuple")
    dimension = _require_exact_integer(
        certificate.residual_context_dimension,
        name="composer residual context dimension",
        minimum=0,
        maximum=MAX_CERTIFIED_INITIAL_SCORE_CONTEXT_DIMENSION,
    )
    lower = _require_fraction(
        Fraction.from_float(certificate.initial_log_factor_lower_bound),
        name="composer exact lower envelope",
    )
    upper = _require_fraction(
        Fraction.from_float(certificate.initial_log_factor_upper_bound),
        name="composer exact upper envelope",
    )
    if lower > upper:
        raise ValueError("composer score envelope is empty")
    return _BackendState(
        backend_kind=_BACKEND_COMPOSER,
        source_owner=source,
        source_certificate=certificate,
        source_certificate_sha256=_require_sha256(
            certificate.certificate_sha256,
            name="composer source certificate digest",
        ),
        source_parameter_key=source_key,
        reference=reference,
        residual_context_policy=_CONTEXT_PLAN,
        residual_context_dimension=dimension,
        fixed_residual_context=None,
        exact_log_weight_upper_bound=upper,
        exact_log_weight_lower_bound=lower,
        learned_operational_surrogate_source=True,
        handcrafted_known_law_source=False,
        ideal_real_extension_declared=False,
        represented_restriction_identity_verified=False,
        certificate_digest_cross_process_stable=False,
    )


def _exact_backend_state(
    adapter: ExactRationalQuadraticInitialTiltScoreAdapterV1,
    *,
    require_sentinels: bool = True,
) -> _BackendState:
    from heterodiff.evaluation import (
        exact_rational_quadratic_initial_tilt as source_module,
    )

    if type(adapter) is not ExactRationalQuadraticInitialTiltScoreAdapterV1:
        raise TypeError("exact adapter has the wrong exact type")
    source = adapter._source
    if type(source) is not source_module.ExactRationalQuadraticInitialTilt:
        raise TypeError("exact adapter source has the wrong exact type")
    if require_sentinels and source is not adapter._source_identity:
        raise ValueError("exact adapter source identity sentinel differs")
    certificate = source.revalidate_live_reference()
    reference = _validate_live_reference(source.reference)
    if require_sentinels:
        if certificate is not adapter._source_certificate_identity:
            raise ValueError("exact adapter certificate identity differs")
        if reference is not adapter._reference_identity:
            raise ValueError("exact adapter reference identity differs")
    source_key = source.parameter_key()
    if type(source_key) is not tuple:
        raise TypeError("exact source parameter key must be an exact tuple")
    context = _validated_context(
        source.residual_context,
        dimension=certificate.residual_context_dimension,
        name="exact provider residual context",
    )
    upper = _require_fraction(
        certificate.exact_global_upper_bound,
        name="exact provider upper envelope",
    )
    lower = certificate.exact_global_lower_bound
    if lower is not None:
        lower = _require_fraction(lower, name="exact provider lower envelope")
        if lower > upper:
            raise ValueError("exact provider score envelope is empty")
    return _BackendState(
        backend_kind=_BACKEND_EXACT,
        source_owner=source,
        source_certificate=certificate,
        source_certificate_sha256=_require_sha256(
            certificate.certificate_sha256,
            name="exact source certificate digest",
        ),
        source_parameter_key=source_key,
        reference=reference,
        residual_context_policy=_CONTEXT_FIXED,
        residual_context_dimension=certificate.residual_context_dimension,
        fixed_residual_context=context,
        exact_log_weight_upper_bound=upper,
        exact_log_weight_lower_bound=lower,
        learned_operational_surrogate_source=False,
        handcrafted_known_law_source=True,
        ideal_real_extension_declared=(
            certificate.ideal_real_polynomial_extension_declared
        ),
        represented_restriction_identity_verified=(
            certificate.represented_restriction_identity_verified
        ),
        certificate_digest_cross_process_stable=(
            certificate.certificate_digest_excludes_runtime_identity
        ),
    )


def _validate_atomic_q_reference(
    reference: object,
) -> CappedPoissonConfigurationReference:
    """Bind the exact stored-binary64 reference used by the CP55 table."""

    checked = _validate_live_reference(reference)
    if len(checked.type_ids) != 2:
        raise ValueError("atomic-q reference must have exactly two types")
    if tuple(checked.type_dimensions[type_id] for type_id in checked.type_ids) != (
        0,
        0,
    ):
        raise ValueError("atomic-q reference types must both be zero-dimensional")
    if checked.total_cap != _ATOMIC_Q_TOTAL_CAP:
        raise ValueError("atomic-q reference total cap differs")
    if not _same_float(checked.activity, float(_ATOMIC_Q_ACTIVITY)):
        raise ValueError("atomic-q reference activity differs")
    exact_weights = tuple(
        _require_fraction(
            Fraction.from_float(checked.type_weights[type_id]),
            name="atomic-q reference exact binary64 weight",
        )
        for type_id in checked.type_ids
    )
    if exact_weights != _ATOMIC_Q_TYPE_WEIGHTS:
        raise ValueError("atomic-q reference binary64 weights differ")
    return checked


def _atomic_q_backend_state(
    adapter: AtomicQScoreTableAdapterV1,
    *,
    require_sentinels: bool = True,
) -> _BackendState:
    from heterodiff.evaluation import (
        mixed_initializer_test28_atomic_q_oracle as source_module,
    )

    if type(adapter) is not AtomicQScoreTableAdapterV1:
        raise TypeError("atomic-q adapter has the wrong exact type")
    source = adapter._source
    if type(source) is not source_module.AtomicQScoreTableProvider:
        raise TypeError("atomic-q adapter source has the wrong exact type")
    if require_sentinels and source is not adapter._source_identity:
        raise ValueError("atomic-q adapter source identity sentinel differs")
    source.__post_init__()
    reference = _validate_atomic_q_reference(adapter._reference)
    if require_sentinels:
        if source is not adapter._source_certificate_identity:
            raise ValueError("atomic-q adapter source certificate identity differs")
        if reference is not adapter._reference_identity:
            raise ValueError("atomic-q adapter reference identity differs")
    source_sha = _require_sha256(
        source.record_sha256,
        name="atomic-q source record digest",
    )
    source_key = (
        "cp55-t28-a0-q-score-table-provider-v1",
        source.schema_version,
        source.fixture_id,
        source.record_sha256,
    )
    return _BackendState(
        backend_kind=_BACKEND_ATOMIC_Q,
        source_owner=source,
        # CP55 has one self-validating sealed table record rather than a
        # distinct certificate object.  The common ledger states this exact
        # alias and binds the record digest; it does not relabel the CP55
        # artifact's historical facade/kernel flags.
        source_certificate=source,
        source_certificate_sha256=source_sha,
        source_parameter_key=source_key,
        reference=reference,
        residual_context_policy=_CONTEXT_FIXED,
        residual_context_dimension=0,
        fixed_residual_context=(),
        exact_log_weight_upper_bound=_require_fraction(
            source.upper_score_bound,
            name="atomic-q source upper envelope",
        ),
        exact_log_weight_lower_bound=_require_fraction(
            source.lower_score_bound,
            name="atomic-q source lower envelope",
        ),
        learned_operational_surrogate_source=False,
        handcrafted_known_law_source=True,
        ideal_real_extension_declared=False,
        represented_restriction_identity_verified=True,
        certificate_digest_cross_process_stable=True,
    )


def _adapter_state(adapter: object) -> _BackendState:
    if type(adapter) is ConfigurationInitialTiltComposerScoreAdapterV1:
        return _composer_backend_state(adapter)
    if type(adapter) is ExactRationalQuadraticInitialTiltScoreAdapterV1:
        return _exact_backend_state(adapter)
    if type(adapter) is AtomicQScoreTableAdapterV1:
        return _atomic_q_backend_state(adapter)
    raise TypeError("backend adapter has no supported exact type")


def _adapter_role(adapter: object) -> str:
    if type(adapter) is ConfigurationInitialTiltComposerScoreAdapterV1:
        return _require_sha256(
            adapter._adapter_role_sha256, name="composer adapter role"
        )
    if type(adapter) is ExactRationalQuadraticInitialTiltScoreAdapterV1:
        return _require_sha256(adapter._adapter_role_sha256, name="exact adapter role")
    if type(adapter) is AtomicQScoreTableAdapterV1:
        return _require_sha256(
            adapter._adapter_role_sha256,
            name="atomic-q adapter role",
        )
    raise TypeError("backend adapter has no supported exact type")


@dataclass(frozen=True, eq=False, init=False)
class CertifiedInitialScoreProviderCertificateV1:
    """Sealed common score, envelope, context, custody, and nonclaim ledger."""

    schema_version: str
    certificate_scope: str
    nonclaim_statement: str
    backend_kind: str
    backend_adapter: CertifiedInitialScoreBackendAdapterV1
    backend_adapter_runtime_identity: int
    adapter_role_sha256: str
    source_owner: object
    source_owner_runtime_identity: int
    source_certificate: object
    source_certificate_runtime_identity: int
    source_certificate_sha256: str
    source_parameter_key: Tuple[object, ...]
    source_parameter_sha256: str
    reference: CappedPoissonConfigurationReference
    reference_runtime_identity: int
    reference_parameter_key: Tuple[object, ...]
    reference_parameter_sha256: str
    residual_context_policy: str
    residual_context_dimension: int
    fixed_residual_context: Optional[Tuple[float, ...]]
    fixed_residual_context_sha256: Optional[str]
    exact_log_weight_upper_bound: Fraction
    exact_log_weight_lower_bound: Optional[Fraction]
    exact_global_upper_bound_certified: bool
    exact_global_lower_bound_certified: bool
    exact_rational_point_score: bool
    canonical_binary64_configuration_required: bool
    source_point_retained: bool
    certificate_digest_directly_excludes_runtime_identity: bool
    certificate_digest_cross_process_stable: bool
    learned_operational_surrogate_source: bool
    handcrafted_known_law_source: bool
    ideal_real_extension_declared: bool
    represented_restriction_identity_verified: bool
    structural_validation_replays_learned_model: bool
    structural_validation_replays_rng: bool
    proposal_sampling_law_verified: bool
    iid_sequence_law_verified: bool
    proposal_independence_verified: bool
    analytic_pi_n_target_equality_verified: bool
    normalization_certified: bool
    true_conditional_or_posterior_factor_verified: bool
    learned_model_quality_evidence: bool
    path_or_sampler_admitted: bool
    formal_test_28_closed: bool
    runtime_portable: bool
    certificate_structural_contract_passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("provider certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("provider certificates require adapter certification")
        if set(values) != set(self.__annotations__):
            raise TypeError("provider certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("provider certificates are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCHEMA_VERSION,
            self.backend_kind,
            self.source_parameter_sha256,
            self.reference_parameter_sha256,
            self.certificate_sha256,
        )


def _certificate_payload(
    certificate: CertifiedInitialScoreProviderCertificateV1,
) -> Mapping[str, object]:
    omitted = {
        "backend_adapter",
        "backend_adapter_runtime_identity",
        "source_owner",
        "source_owner_runtime_identity",
        "source_certificate",
        "source_certificate_runtime_identity",
        "reference",
        "reference_runtime_identity",
        "certificate_sha256",
    }
    return {
        name: getattr(certificate, name)
        for name in certificate.__annotations__
        if name not in omitted
    }


def _validate_certificate(
    certificate: object,
) -> CertifiedInitialScoreProviderCertificateV1:
    if type(certificate) is not CertifiedInitialScoreProviderCertificateV1:
        raise TypeError(
            "certificate must be an exact CertifiedInitialScoreProviderCertificateV1"
        )
    _require_exact_text(
        certificate.schema_version,
        name="provider certificate schema version",
        expected=CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCHEMA_VERSION,
    )
    _require_exact_text(
        certificate.certificate_scope,
        name="provider certificate scope",
        expected=CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCOPE,
    )
    _require_exact_text(
        certificate.nonclaim_statement,
        name="provider certificate nonclaim statement",
        expected=CERTIFIED_INITIAL_SCORE_PROVIDER_V1_NONCLAIM,
    )
    state = _adapter_state(certificate.backend_adapter)
    _require_exact_text(
        certificate.backend_kind,
        name="provider certificate backend kind",
        expected=state.backend_kind,
    )
    _require_runtime_identity(
        certificate.backend_adapter_runtime_identity,
        name="certificate backend-adapter runtime identity",
    )
    if certificate.backend_adapter_runtime_identity != id(certificate.backend_adapter):
        raise ValueError("provider certificate backend-adapter identity differs")
    role = _require_sha256(
        certificate.adapter_role_sha256, name="certificate adapter role"
    )
    if role != _adapter_role(certificate.backend_adapter):
        raise ValueError("provider certificate adapter role differs")
    for name, supplied, expected in (
        (
            "source owner",
            certificate.source_owner_runtime_identity,
            id(state.source_owner),
        ),
        (
            "source certificate",
            certificate.source_certificate_runtime_identity,
            id(state.source_certificate),
        ),
        (
            "reference",
            certificate.reference_runtime_identity,
            id(state.reference),
        ),
    ):
        _require_runtime_identity(supplied, name="certificate %s identity" % name)
        if supplied != expected:
            raise ValueError("provider certificate %s identity differs" % name)
    if certificate.source_owner is not state.source_owner:
        raise ValueError("provider certificate source owner differs")
    if certificate.source_certificate is not state.source_certificate:
        raise ValueError("provider certificate source certificate differs")
    if certificate.reference is not state.reference:
        raise ValueError("provider certificate reference differs")
    _require_sha256(
        certificate.source_certificate_sha256,
        name="certificate source certificate digest",
    )
    if certificate.source_certificate_sha256 != state.source_certificate_sha256:
        raise ValueError("provider certificate source certificate digest differs")
    if type(certificate.source_parameter_key) is not tuple:
        raise TypeError("certificate source parameter key must be an exact tuple")
    if _typed(certificate.source_parameter_key) != _typed(state.source_parameter_key):
        raise ValueError("provider certificate source parameter key differs")
    _require_sha256(
        certificate.source_parameter_sha256,
        name="certificate source parameter digest",
    )
    expected_source_sha = _semantic_digest(
        {
            "backend_kind": state.backend_kind,
            "source_parameter_key": state.source_parameter_key,
        },
        domain=b"heterodiff-certified-initial-score-source-v1\x00",
    )
    if certificate.source_parameter_sha256 != expected_source_sha:
        raise ValueError("provider certificate source parameter digest differs")
    reference = _validate_live_reference(certificate.reference)
    if type(certificate.reference_parameter_key) is not tuple:
        raise TypeError("certificate reference parameter key must be an exact tuple")
    if _typed(certificate.reference_parameter_key) != _typed(reference.parameter_key()):
        raise ValueError("provider certificate reference parameter key differs")
    _require_sha256(
        certificate.reference_parameter_sha256,
        name="certificate reference parameter digest",
    )
    if certificate.reference_parameter_sha256 != _reference_parameter_sha256(reference):
        raise ValueError("provider certificate reference parameter digest differs")
    _require_exact_text(
        certificate.residual_context_policy,
        name="provider certificate context policy",
        expected=state.residual_context_policy,
    )
    dimension = _require_exact_integer(
        certificate.residual_context_dimension,
        name="certificate residual context dimension",
        minimum=0,
        maximum=MAX_CERTIFIED_INITIAL_SCORE_CONTEXT_DIMENSION,
    )
    if dimension != state.residual_context_dimension:
        raise ValueError("provider certificate residual context dimension differs")
    if state.residual_context_policy == _CONTEXT_PLAN:
        if (
            certificate.fixed_residual_context is not None
            or certificate.fixed_residual_context_sha256 is not None
        ):
            raise ValueError(
                "plan-supplied context policy cannot retain a fixed context"
            )
    elif state.residual_context_policy == _CONTEXT_FIXED:
        context = _validated_context(
            certificate.fixed_residual_context,
            dimension=dimension,
            name="certificate fixed residual context",
        )
        if context != state.fixed_residual_context:
            raise ValueError("provider certificate fixed residual context differs")
        _require_sha256(
            certificate.fixed_residual_context_sha256,
            name="certificate fixed residual-context digest",
        )
        if certificate.fixed_residual_context_sha256 != _context_sha256(context):
            raise ValueError("provider certificate fixed context digest differs")
    else:  # pragma: no cover - protected by exact adapter state
        raise ValueError("provider certificate context policy is unknown")
    upper = _require_fraction(
        certificate.exact_log_weight_upper_bound,
        name="certificate exact upper envelope",
    )
    if upper != state.exact_log_weight_upper_bound:
        raise ValueError("provider certificate exact upper envelope differs")
    lower = certificate.exact_log_weight_lower_bound
    if lower is not None:
        lower = _require_fraction(lower, name="certificate exact lower envelope")
        if lower > upper:
            raise ValueError("provider certificate score envelope is empty")
    if lower != state.exact_log_weight_lower_bound:
        raise ValueError("provider certificate exact lower envelope differs")
    true_flags = (
        "exact_global_upper_bound_certified",
        "exact_rational_point_score",
        "canonical_binary64_configuration_required",
        "source_point_retained",
        "certificate_digest_directly_excludes_runtime_identity",
        "certificate_structural_contract_passed",
    )
    false_flags = (
        "structural_validation_replays_learned_model",
        "structural_validation_replays_rng",
        "proposal_sampling_law_verified",
        "iid_sequence_law_verified",
        "proposal_independence_verified",
        "analytic_pi_n_target_equality_verified",
        "normalization_certified",
        "true_conditional_or_posterior_factor_verified",
        "learned_model_quality_evidence",
        "path_or_sampler_admitted",
        "formal_test_28_closed",
        "runtime_portable",
    )
    backend_semantic_flags = (
        "certificate_digest_cross_process_stable",
        "learned_operational_surrogate_source",
        "handcrafted_known_law_source",
        "ideal_real_extension_declared",
        "represented_restriction_identity_verified",
    )
    for name in (
        true_flags
        + false_flags
        + ("exact_global_lower_bound_certified",)
        + backend_semantic_flags
    ):
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("provider certificate positive claim flags differ")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("provider certificate negative claim flags differ")
    if certificate.exact_global_lower_bound_certified != (lower is not None):
        raise ValueError("provider certificate lower-bound flag differs")
    for name in backend_semantic_flags:
        if getattr(certificate, name) != getattr(state, name):
            raise ValueError("provider certificate backend semantic %s differs" % name)
    if certificate.learned_operational_surrogate_source == (
        certificate.handcrafted_known_law_source
    ):
        raise ValueError("provider certificate source-family flags are ambiguous")
    _require_sha256(certificate.certificate_sha256, name="provider certificate digest")
    expected_digest = _semantic_digest(
        _certificate_payload(certificate),
        domain=b"heterodiff-certified-initial-score-certificate-v1\x00",
    )
    if certificate.certificate_sha256 != expected_digest:
        raise ValueError("provider certificate digest differs")
    return certificate


def _make_certificate(
    adapter: CertifiedInitialScoreBackendAdapterV1,
) -> CertifiedInitialScoreProviderCertificateV1:
    state = _adapter_state(adapter)
    reference_key = state.reference.parameter_key()
    fixed_context_sha = (
        None
        if state.fixed_residual_context is None
        else _context_sha256(state.fixed_residual_context)
    )
    values = {
        "schema_version": CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCHEMA_VERSION,
        "certificate_scope": CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCOPE,
        "nonclaim_statement": CERTIFIED_INITIAL_SCORE_PROVIDER_V1_NONCLAIM,
        "backend_kind": state.backend_kind,
        "backend_adapter": adapter,
        "backend_adapter_runtime_identity": id(adapter),
        "adapter_role_sha256": _adapter_role(adapter),
        "source_owner": state.source_owner,
        "source_owner_runtime_identity": id(state.source_owner),
        "source_certificate": state.source_certificate,
        "source_certificate_runtime_identity": id(state.source_certificate),
        "source_certificate_sha256": state.source_certificate_sha256,
        "source_parameter_key": state.source_parameter_key,
        "source_parameter_sha256": _semantic_digest(
            {
                "backend_kind": state.backend_kind,
                "source_parameter_key": state.source_parameter_key,
            },
            domain=b"heterodiff-certified-initial-score-source-v1\x00",
        ),
        "reference": state.reference,
        "reference_runtime_identity": id(state.reference),
        "reference_parameter_key": reference_key,
        "reference_parameter_sha256": _reference_parameter_sha256(state.reference),
        "residual_context_policy": state.residual_context_policy,
        "residual_context_dimension": state.residual_context_dimension,
        "fixed_residual_context": state.fixed_residual_context,
        "fixed_residual_context_sha256": fixed_context_sha,
        "exact_log_weight_upper_bound": state.exact_log_weight_upper_bound,
        "exact_log_weight_lower_bound": state.exact_log_weight_lower_bound,
        "exact_global_upper_bound_certified": True,
        "exact_global_lower_bound_certified": (
            state.exact_log_weight_lower_bound is not None
        ),
        "exact_rational_point_score": True,
        "canonical_binary64_configuration_required": True,
        "source_point_retained": True,
        "certificate_digest_directly_excludes_runtime_identity": True,
        "certificate_digest_cross_process_stable": (
            state.certificate_digest_cross_process_stable
        ),
        "learned_operational_surrogate_source": (
            state.learned_operational_surrogate_source
        ),
        "handcrafted_known_law_source": state.handcrafted_known_law_source,
        "ideal_real_extension_declared": state.ideal_real_extension_declared,
        "represented_restriction_identity_verified": (
            state.represented_restriction_identity_verified
        ),
        "structural_validation_replays_learned_model": False,
        "structural_validation_replays_rng": False,
        "proposal_sampling_law_verified": False,
        "iid_sequence_law_verified": False,
        "proposal_independence_verified": False,
        "analytic_pi_n_target_equality_verified": False,
        "normalization_certified": False,
        "true_conditional_or_posterior_factor_verified": False,
        "learned_model_quality_evidence": False,
        "path_or_sampler_admitted": False,
        "formal_test_28_closed": False,
        "runtime_portable": False,
        "certificate_structural_contract_passed": True,
        "certificate_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(CertifiedInitialScoreProviderCertificateV1)
    for name in CertifiedInitialScoreProviderCertificateV1.__annotations__:
        object.__setattr__(provisional, name, values[name])
    values["certificate_sha256"] = _semantic_digest(
        _certificate_payload(provisional),
        domain=b"heterodiff-certified-initial-score-certificate-v1\x00",
    )
    return CertifiedInitialScoreProviderCertificateV1(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CertifiedInitialScorePointEvaluationV1:
    """One sealed common exact score retaining its source point record."""

    certificate: CertifiedInitialScoreProviderCertificateV1
    certificate_sha256: str
    backend_kind: str
    configuration: TransformedConfiguration
    configuration_sha256: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    source_evaluation: object
    source_evaluation_sha256: str
    exact_log_weight: Fraction
    exact_log_weight_numerator: int
    exact_log_weight_denominator: int
    rounded_log_weight: Optional[float]
    exact_upper_bound_respected: bool
    exact_lower_bound_respected: Optional[bool]
    structural_validation_replayed_learned_model: bool
    structural_validation_replayed_rng: bool
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("provider point evaluations cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError("provider point evaluations are provider-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("provider point evaluation fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_evaluation_structure(self, certificate=values["certificate"])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("provider point evaluations are not pickle objects")


def _evaluation_fields() -> Tuple[str, ...]:
    return tuple(CertifiedInitialScorePointEvaluationV1.__annotations__)


def _evaluation_payload(
    evaluation: CertifiedInitialScorePointEvaluationV1,
) -> Mapping[str, object]:
    omitted = {
        "certificate",
        "configuration",
        "source_evaluation",
        "evaluation_sha256",
    }
    return {
        name: getattr(evaluation, name)
        for name in evaluation.__annotations__
        if name not in omitted
    }


def _atomic_q_count_vector(
    reference: CappedPoissonConfigurationReference,
    configuration: TransformedConfiguration,
) -> Tuple[int, int]:
    """Return count-table components in bound ascending reference-type order."""

    checked_reference = _validate_atomic_q_reference(reference)
    canonical = _canonical_configuration(checked_reference, configuration)
    counts = [0, 0]
    first_type, second_type = checked_reference.type_ids
    for event in canonical:
        if event.event_type == first_type:
            counts[0] += 1
        elif event.event_type == second_type:
            counts[1] += 1
        else:  # pragma: no cover - canonical validation rejects this first
            raise ValueError("atomic-q configuration contains an unknown type")
    result = (counts[0], counts[1])
    if sum(result) != len(canonical) or sum(result) > _ATOMIC_Q_TOTAL_CAP:
        raise ArithmeticError("atomic-q configuration count mapping differs")
    return result


def _source_evaluation_structure(
    adapter: CertifiedInitialScoreBackendAdapterV1,
    evaluation: object,
    *,
    configuration: TransformedConfiguration,
    residual_context: Tuple[float, ...],
) -> Tuple[object, str, Fraction]:
    state = _adapter_state(adapter)
    if type(adapter) is ConfigurationInitialTiltComposerScoreAdapterV1:
        from heterodiff.models import (
            configuration_initial_tilt_composer_torch as module,
        )

        if type(evaluation) is not module.InitialTiltPointEvaluation:
            raise TypeError("composer source evaluation has the wrong exact type")
        if evaluation.certificate is not state.source_certificate:
            raise ValueError("composer source point belongs to another certificate")
        retained_configuration = _canonical_configuration(
            state.reference, evaluation.configuration
        )
        if retained_configuration != configuration:
            raise ValueError("composer source point configuration differs")
        retained_context = _validated_context(
            evaluation.residual_context,
            dimension=state.residual_context_dimension,
            name="composer source residual context",
        )
        if retained_context != residual_context:
            raise ValueError("composer source point residual context differs")
        _fraction_parts(
            evaluation.exact_initial_log_factor_numerator,
            evaluation.exact_initial_log_factor_denominator,
            name="composer source exact score preflight",
        )
        # Constructor validation rechecks the retained arithmetic and digest.  It
        # does not invoke either the guide or residual model.
        module.InitialTiltPointEvaluation(
            **{name: getattr(evaluation, name) for name in module._evaluation_fields()},
            _construction_token=module._EVALUATION_TOKEN,
        )
        q = _fraction_parts(
            evaluation.exact_initial_log_factor_numerator,
            evaluation.exact_initial_log_factor_denominator,
            name="composer source exact score",
        )
        digest = _require_sha256(
            evaluation.evaluation_sha256,
            name="composer source evaluation digest",
        )
        if not _same_float(evaluation.initial_log_factor, float(q)):
            raise ValueError("composer source point rounded score differs")
        return evaluation, digest, q
    if type(adapter) is ExactRationalQuadraticInitialTiltScoreAdapterV1:
        from heterodiff.evaluation import (
            exact_rational_quadratic_initial_tilt as module,
        )

        if (
            type(evaluation)
            is not module.ExactRationalQuadraticInitialTiltPointEvaluation
        ):
            raise TypeError("exact source evaluation has the wrong exact type")
        if evaluation.certificate is not state.source_certificate:
            raise ValueError("exact source point belongs to another certificate")
        retained_configuration = _canonical_configuration(
            state.reference, evaluation.configuration
        )
        if retained_configuration != configuration:
            raise ValueError("exact source point configuration differs")
        retained_context = _validated_context(
            evaluation.residual_context,
            dimension=state.residual_context_dimension,
            name="exact source residual context",
        )
        if retained_context != residual_context:
            raise ValueError("exact source point residual context differs")
        _fraction_parts(
            evaluation.exact_log_weight_numerator,
            evaluation.exact_log_weight_denominator,
            name="exact source score preflight",
        )
        checked = adapter._source._validate_evaluation_structure(evaluation)
        if checked.certificate is not state.source_certificate:
            raise ValueError("exact source point belongs to another certificate")
        if checked.configuration != configuration:
            raise ValueError("exact source point configuration differs")
        if checked.residual_context != residual_context:
            raise ValueError("exact source point residual context differs")
        q = _require_fraction(checked.exact_log_weight, name="exact source score")
        if (
            checked.exact_log_weight_numerator != q.numerator
            or checked.exact_log_weight_denominator != q.denominator
        ):
            raise ValueError("exact source score parts differ")
        digest = _require_sha256(
            checked.evaluation_sha256,
            name="exact source evaluation digest",
        )
        return checked, digest, q
    if type(adapter) is AtomicQScoreTableAdapterV1:
        from heterodiff.evaluation import (
            mixed_initializer_test28_atomic_q_oracle as module,
        )

        if type(evaluation) is not module.AtomicQScoreEvaluation:
            raise TypeError("atomic-q source evaluation has the wrong exact type")
        # This is structural record validation only.  It deliberately does not
        # call source.evaluate; explicit full replay is the sole dispatch path.
        evaluation.__post_init__()
        count_vector = _atomic_q_count_vector(state.reference, configuration)
        if evaluation.count_vector != count_vector:
            raise ValueError("atomic-q source point count vector differs")
        try:
            index = state.source_owner.count_vectors.index(count_vector)
        except ValueError as error:  # pragma: no cover - complete cap-two table
            raise ValueError(
                "atomic-q count vector is outside the source table"
            ) from error
        if (
            evaluation.protocol_index != index
            or evaluation.state_label != state.source_owner.state_labels[index]
        ):
            raise ValueError("atomic-q source point state identity differs")
        q = _require_fraction(
            evaluation.exact_score,
            name="atomic-q source exact score",
        )
        if q != state.source_owner.exact_scores[index]:
            raise ValueError("atomic-q source point exact score differs")
        digest = _require_sha256(
            evaluation.record_sha256,
            name="atomic-q source evaluation digest",
        )
        return evaluation, digest, q
    raise TypeError("source evaluation adapter has no supported exact type")


def _evaluate_source(
    adapter: CertifiedInitialScoreBackendAdapterV1,
    configuration: TransformedConfiguration,
    residual_context: Tuple[float, ...],
) -> object:
    if type(adapter) is ConfigurationInitialTiltComposerScoreAdapterV1:
        return adapter._source.evaluate(
            configuration, residual_context=residual_context
        )
    if type(adapter) is ExactRationalQuadraticInitialTiltScoreAdapterV1:
        return adapter._source.evaluate(
            configuration, residual_context=residual_context
        )
    if type(adapter) is AtomicQScoreTableAdapterV1:
        if residual_context != ():
            raise ValueError("atomic-q source requires the fixed empty context")
        return adapter._source.evaluate(
            _atomic_q_count_vector(adapter._reference, configuration)
        )
    raise TypeError("source evaluation adapter has no supported exact type")


def _replay_source_evaluation(
    adapter: CertifiedInitialScoreBackendAdapterV1,
    evaluation: object,
    *,
    configuration: TransformedConfiguration,
    residual_context: Tuple[float, ...],
) -> object:
    if type(adapter) is ConfigurationInitialTiltComposerScoreAdapterV1:
        return adapter._source.validate_evaluation(
            evaluation,
            configuration,
            residual_context=residual_context,
        )
    if type(adapter) is ExactRationalQuadraticInitialTiltScoreAdapterV1:
        return adapter._source.validate_evaluation(
            evaluation,
            configuration,
            residual_context=residual_context,
        )
    if type(adapter) is AtomicQScoreTableAdapterV1:
        if residual_context != ():
            raise ValueError("atomic-q source requires the fixed empty context")
        replayed = adapter._source.evaluate(
            _atomic_q_count_vector(adapter._reference, configuration)
        )
        replayed.__post_init__()
        evaluation.__post_init__()
        for name in replayed.__annotations__:
            if getattr(replayed, name) != getattr(evaluation, name):
                raise ValueError("atomic-q source replay field %s differs" % name)
        # The table returns a fresh sealed point.  Exact fields and its digest,
        # rather than object identity, are the replay witness.
        return evaluation
    raise TypeError("source replay adapter has no supported exact type")


def _validate_evaluation_structure(
    evaluation: object,
    *,
    certificate: CertifiedInitialScoreProviderCertificateV1,
) -> CertifiedInitialScorePointEvaluationV1:
    if type(evaluation) is not CertifiedInitialScorePointEvaluationV1:
        raise TypeError("evaluation has the wrong exact provider point type")
    checked_certificate = _validate_certificate(certificate)
    if evaluation.certificate is not checked_certificate:
        raise ValueError("evaluation belongs to another provider certificate")
    _require_sha256(evaluation.certificate_sha256, name="evaluation certificate digest")
    if evaluation.certificate_sha256 != checked_certificate.certificate_sha256:
        raise ValueError("evaluation certificate digest differs")
    _require_exact_text(
        evaluation.backend_kind,
        name="evaluation backend kind",
        expected=checked_certificate.backend_kind,
    )
    canonical = _canonical_configuration(
        checked_certificate.reference, evaluation.configuration
    )
    if canonical != evaluation.configuration:
        raise ValueError("evaluation configuration is not canonical")
    _require_sha256(evaluation.configuration_sha256, name="configuration digest")
    if evaluation.configuration_sha256 != _configuration_sha256(canonical):
        raise ValueError("evaluation configuration digest differs")
    context = _validated_context(
        evaluation.residual_context,
        dimension=checked_certificate.residual_context_dimension,
        name="evaluation residual context",
    )
    if (
        checked_certificate.residual_context_policy == _CONTEXT_FIXED
        and context != checked_certificate.fixed_residual_context
    ):
        raise ValueError("evaluation residual context differs from fixed context")
    _require_sha256(evaluation.residual_context_sha256, name="context digest")
    if evaluation.residual_context_sha256 != _context_sha256(context):
        raise ValueError("evaluation residual-context digest differs")
    source, source_sha, source_q = _source_evaluation_structure(
        checked_certificate.backend_adapter,
        evaluation.source_evaluation,
        configuration=canonical,
        residual_context=context,
    )
    if source is not evaluation.source_evaluation:
        raise ValueError("evaluation source point identity differs")
    _require_sha256(
        evaluation.source_evaluation_sha256,
        name="source evaluation digest",
    )
    if evaluation.source_evaluation_sha256 != source_sha:
        raise ValueError("evaluation source digest differs")
    q = _require_fraction(evaluation.exact_log_weight, name="evaluation exact score")
    parts = _fraction_parts(
        evaluation.exact_log_weight_numerator,
        evaluation.exact_log_weight_denominator,
        name="evaluation exact score",
    )
    if q != parts or q != source_q:
        raise ValueError("evaluation exact score differs from source")
    expected_rounded = _optional_float(q)
    if not _same_optional_float(evaluation.rounded_log_weight, expected_rounded):
        raise ValueError("evaluation rounded display score differs")
    if evaluation.exact_upper_bound_respected is not True:
        raise ValueError("evaluation upper-bound witness differs")
    if q > checked_certificate.exact_log_weight_upper_bound:
        raise ValueError("evaluation exact score exceeds certified U")
    lower = checked_certificate.exact_log_weight_lower_bound
    if lower is None:
        if evaluation.exact_lower_bound_respected is not None:
            raise ValueError("evaluation fabricated a lower-bound witness")
    else:
        if evaluation.exact_lower_bound_respected is not True:
            raise ValueError("evaluation lower-bound witness differs")
        if q < lower:
            raise ValueError("evaluation exact score lies below certified L")
    for name in (
        "structural_validation_replayed_learned_model",
        "structural_validation_replayed_rng",
    ):
        if getattr(evaluation, name) is not False:
            raise ValueError("evaluation nonreplay flag %s differs" % name)
    _require_sha256(evaluation.evaluation_sha256, name="provider evaluation digest")
    expected_digest = _semantic_digest(
        _evaluation_payload(evaluation),
        domain=b"heterodiff-certified-initial-score-evaluation-v1\x00",
    )
    if evaluation.evaluation_sha256 != expected_digest:
        raise ValueError("provider evaluation digest differs")
    return evaluation


def _make_evaluation(
    certificate: CertifiedInitialScoreProviderCertificateV1,
    *,
    configuration: TransformedConfiguration,
    residual_context: Tuple[float, ...],
    source_evaluation: object,
) -> CertifiedInitialScorePointEvaluationV1:
    source, source_sha, q = _source_evaluation_structure(
        certificate.backend_adapter,
        source_evaluation,
        configuration=configuration,
        residual_context=residual_context,
    )
    lower = certificate.exact_log_weight_lower_bound
    values = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "backend_kind": certificate.backend_kind,
        "configuration": configuration,
        "configuration_sha256": _configuration_sha256(configuration),
        "residual_context": residual_context,
        "residual_context_sha256": _context_sha256(residual_context),
        "source_evaluation": source,
        "source_evaluation_sha256": source_sha,
        "exact_log_weight": q,
        "exact_log_weight_numerator": q.numerator,
        "exact_log_weight_denominator": q.denominator,
        "rounded_log_weight": _optional_float(q),
        "exact_upper_bound_respected": q <= certificate.exact_log_weight_upper_bound,
        "exact_lower_bound_respected": None if lower is None else q >= lower,
        "structural_validation_replayed_learned_model": False,
        "structural_validation_replayed_rng": False,
        "evaluation_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(CertifiedInitialScorePointEvaluationV1)
    for name in CertifiedInitialScorePointEvaluationV1.__annotations__:
        object.__setattr__(provisional, name, values[name])
    values["evaluation_sha256"] = _semantic_digest(
        _evaluation_payload(provisional),
        domain=b"heterodiff-certified-initial-score-evaluation-v1\x00",
    )
    return CertifiedInitialScorePointEvaluationV1(
        **values, _construction_token=_EVALUATION_TOKEN
    )


class CertifiedInitialScoreProviderV1:
    """Exact sealed kernel-facing owner for a supported certified source family."""

    __slots__ = (
        "_backend_adapter",
        "_backend_adapter_identity",
        "_certificate",
        "_certificate_identity",
        "_reference_identity",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("certified score providers cannot be subclassed")

    def __init__(
        self,
        *,
        backend_adapter: CertifiedInitialScoreBackendAdapterV1,
        certificate: CertifiedInitialScoreProviderCertificateV1,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("certified score providers require adaptation")
        object.__setattr__(self, "_backend_adapter", backend_adapter)
        object.__setattr__(self, "_backend_adapter_identity", backend_adapter)
        object.__setattr__(self, "_certificate", certificate)
        object.__setattr__(self, "_certificate_identity", certificate)
        object.__setattr__(self, "_reference_identity", certificate.reference)
        self.revalidate_live_components()

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("certified score providers are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("certified score providers are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("certified score providers are not pickle objects")

    @property
    def backend_adapter(self) -> CertifiedInitialScoreBackendAdapterV1:
        self.revalidate_live_components()
        return self._backend_adapter

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        self.revalidate_live_components()
        return self._certificate.reference

    @property
    def certificate(self) -> CertifiedInitialScoreProviderCertificateV1:
        self.revalidate_live_components()
        return self._certificate

    def parameter_key(self) -> Tuple[object, ...]:
        certificate = self.revalidate_live_components()
        return (
            CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCHEMA_VERSION,
            certificate.backend_kind,
            certificate.source_parameter_sha256,
            certificate.reference_parameter_sha256,
            certificate.certificate_sha256,
        )

    def revalidate_live_components(
        self,
    ) -> CertifiedInitialScoreProviderCertificateV1:
        if self._backend_adapter is not self._backend_adapter_identity:
            raise ValueError("provider backend-adapter identity sentinel differs")
        if self._certificate is not self._certificate_identity:
            raise ValueError("provider certificate identity sentinel differs")
        certificate = _validate_certificate(self._certificate)
        if certificate.backend_adapter is not self._backend_adapter:
            raise ValueError("provider certificate belongs to another adapter")
        if certificate.reference is not self._reference_identity:
            raise ValueError("provider reference identity sentinel differs")
        expected = _make_certificate(self._backend_adapter)
        for name in certificate.__annotations__:
            supplied = getattr(certificate, name)
            wanted = getattr(expected, name)
            if name in (
                "backend_adapter",
                "source_owner",
                "source_certificate",
                "reference",
            ):
                matches = supplied is wanted
            elif type(supplied) is float and type(wanted) is float:
                matches = _same_float(supplied, wanted)
            else:
                matches = supplied == wanted
            if not matches:
                raise ValueError("live provider certificate field %s differs" % name)
        return certificate

    def _validated_inputs(
        self,
        configuration: object,
        residual_context: object,
    ) -> Tuple[TransformedConfiguration, Tuple[float, ...]]:
        certificate = self.revalidate_live_components()
        canonical = _canonical_configuration(certificate.reference, configuration)
        context = _validated_context(
            residual_context,
            dimension=certificate.residual_context_dimension,
            name="residual_context",
        )
        if (
            certificate.residual_context_policy == _CONTEXT_FIXED
            and context != certificate.fixed_residual_context
        ):
            raise ValueError("residual_context differs from provider-fixed context")
        return canonical, context

    def evaluate(
        self,
        configuration: object,
        *,
        residual_context: object,
    ) -> CertifiedInitialScorePointEvaluationV1:
        """Evaluate one exact represented score without randomness."""

        certificate = self.revalidate_live_components()
        canonical, context = self._validated_inputs(configuration, residual_context)
        source_evaluation = _evaluate_source(self._backend_adapter, canonical, context)
        self.revalidate_live_components()
        result = _make_evaluation(
            certificate,
            configuration=canonical,
            residual_context=context,
            source_evaluation=source_evaluation,
        )
        self.revalidate_live_components()
        return result

    def validate_evaluation_structure(
        self,
        evaluation: object,
    ) -> CertifiedInitialScorePointEvaluationV1:
        """Validate retained arithmetic/custody without learned-model or RNG replay."""

        certificate = self.revalidate_live_components()
        return _validate_evaluation_structure(evaluation, certificate=certificate)

    def validate_evaluation(
        self,
        evaluation: object,
        configuration: object,
        *,
        residual_context: object,
    ) -> CertifiedInitialScorePointEvaluationV1:
        """Fully replay the source point against explicit inputs."""

        checked = self.validate_evaluation_structure(evaluation)
        canonical, context = self._validated_inputs(configuration, residual_context)
        if checked.configuration != canonical:
            raise ValueError("evaluation configuration differs from replay input")
        if checked.residual_context != context:
            raise ValueError("evaluation residual context differs from replay input")
        replayed = _replay_source_evaluation(
            self._backend_adapter,
            checked.source_evaluation,
            configuration=canonical,
            residual_context=context,
        )
        if replayed is not checked.source_evaluation:
            raise ValueError("source replay returned another point object")
        self.revalidate_live_components()
        return self.validate_evaluation_structure(checked)


def _adapt(
    adapter: CertifiedInitialScoreBackendAdapterV1,
) -> CertifiedInitialScoreProviderV1:
    certificate = _make_certificate(adapter)
    return CertifiedInitialScoreProviderV1(
        backend_adapter=adapter,
        certificate=certificate,
        _construction_token=_OWNER_TOKEN,
    )


def adapt_configuration_initial_tilt_composer_score_provider_v1(
    composer: object,
    *,
    adapter_role_sha256: object,
) -> CertifiedInitialScoreProviderV1:
    """Adapt one exact CP30 composer without widening any source claim."""

    role = _require_sha256(adapter_role_sha256, name="adapter_role_sha256")
    adapter = ConfigurationInitialTiltComposerScoreAdapterV1(
        source=composer,
        adapter_role_sha256=role,
        _construction_token=_COMPOSER_ADAPTER_TOKEN,
    )
    return _adapt(adapter)


def adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
    provider: object,
    *,
    adapter_role_sha256: object,
) -> CertifiedInitialScoreProviderV1:
    """Adapt one exact known-law score owner without fabricating a lower bound."""

    role = _require_sha256(adapter_role_sha256, name="adapter_role_sha256")
    adapter = ExactRationalQuadraticInitialTiltScoreAdapterV1(
        source=provider,
        adapter_role_sha256=role,
        _construction_token=_EXACT_ADAPTER_TOKEN,
    )
    return _adapt(adapter)


def adapt_atomic_q_score_table_provider_v1(
    source: object,
    *,
    reference: object,
    adapter_role_sha256: object,
) -> CertifiedInitialScoreProviderV1:
    """Adapt the exact CP55 table against its stored-binary64 A0-Q reference."""

    role = _require_sha256(adapter_role_sha256, name="adapter_role_sha256")
    checked_reference = _validate_atomic_q_reference(reference)
    adapter = AtomicQScoreTableAdapterV1(
        source=source,
        reference=checked_reference,
        adapter_role_sha256=role,
        _construction_token=_ATOMIC_Q_ADAPTER_TOKEN,
    )
    return _adapt(adapter)


def require_matching_certified_initial_score_provider_v1(
    provider: CertifiedInitialScoreProviderV1,
    reference: CappedPoissonConfigurationReference,
) -> CertifiedInitialScoreProviderV1:
    """Require exact provider/reference identity and fully revalidate custody."""

    if type(provider) is not CertifiedInitialScoreProviderV1:
        raise TypeError(
            "provider has the wrong exact CertifiedInitialScoreProviderV1 type"
        )
    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("reference has the wrong exact capped-Poisson type")
    provider.revalidate_live_components()
    if provider.reference is not reference:
        raise ValueError("provider belongs to another reference object")
    return provider


def validate_certified_initial_score_provider_v1_certificate(
    provider: CertifiedInitialScoreProviderV1,
) -> CertifiedInitialScoreProviderCertificateV1:
    """Return the fully reconstructed live common provider certificate."""

    if type(provider) is not CertifiedInitialScoreProviderV1:
        raise TypeError(
            "provider has the wrong exact CertifiedInitialScoreProviderV1 type"
        )
    return provider.revalidate_live_components()


__all__ = (
    "CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS",
    "CERTIFIED_INITIAL_SCORE_PROVIDER_V1_CONTEXT_POLICIES",
    "CERTIFIED_INITIAL_SCORE_PROVIDER_V1_NONCLAIM",
    "CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCHEMA_VERSION",
    "CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCOPE",
    "MAX_CERTIFIED_INITIAL_SCORE_CONTEXT_DIMENSION",
    "MAX_CERTIFIED_INITIAL_SCORE_COORDINATES",
    "MAX_CERTIFIED_INITIAL_SCORE_DIGEST_DEPTH",
    "MAX_CERTIFIED_INITIAL_SCORE_DIGEST_NODES",
    "MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TEXT_BYTES",
    "MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TOTAL_TEXT_BYTES",
    "MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS",
    "AtomicQScoreTableAdapterV1",
    "CertifiedInitialScoreBackendAdapterV1",
    "CertifiedInitialScorePointEvaluationV1",
    "CertifiedInitialScoreProviderCertificateV1",
    "CertifiedInitialScoreProviderV1",
    "CertifiedInitialScoreProviderV1Error",
    "ConfigurationInitialTiltComposerScoreAdapterV1",
    "ExactRationalQuadraticInitialTiltScoreAdapterV1",
    "adapt_atomic_q_score_table_provider_v1",
    "adapt_configuration_initial_tilt_composer_score_provider_v1",
    "adapt_exact_rational_quadratic_initial_tilt_score_provider_v1",
    "require_matching_certified_initial_score_provider_v1",
    "validate_certified_initial_score_provider_v1_certificate",
)
