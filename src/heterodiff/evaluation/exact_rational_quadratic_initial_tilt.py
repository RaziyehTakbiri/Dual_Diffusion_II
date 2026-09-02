"""Sealed exact-rational quadratic initial-score providers.

This module is a small known-law backend for mixed-support initializer tests.
It deliberately does not impersonate :class:`ConfigurationInitialTiltComposer`
and is not accepted by the CP50-v1 initializer kernel.  For a canonical
represented configuration ``x`` it evaluates, exactly in :class:`Fraction`,

``q_repr(x) = c[|x|] - sum_events sum_j a[type, j] * r_j**2``,

where ``r_j = Fraction.from_float(x_j)``, every ``a`` is nonnegative, and all
cardinality penalties are at most zero.  Hence the exact global upper bound is
``U = 0``.  Positive-dimensional quadratic terms make the ideal-real score
unbounded below, so no finite global lower bound is fabricated.

Five law layers are kept separate in every certificate:

* ``ideal_rational_analytic_law``: rational reference parameters and the
  independently declared real-polynomial score schema;
* ``binary64_parameter_analytic_law``: the mathematical law obtained by
  interpreting stored reference floats exactly;
* ``represented_exact_score_law``: pointwise exact arithmetic on canonical
  binary64 configurations;
* ``operational_runtime_proposal_law``: an unverified law induced by the
  runtime sampler and its random source; and
* ``learned_model_separation``: this handcrafted backend supplies no evidence
  about a learned composer, posterior, sampler, or scientific generality.

The two exported Test-28 builders retain the frozen ideal intent
``theta=1``, weights ``(2/5, 3/5)``, while separately binding the actual
binary64 reference values and their exact dyadic fractions.  The module does
not import the independent oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
import struct
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from heterodiff.artifacts.manifest import canonical_config_digest
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


EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCHEMA_VERSION = (
    "exact-rational-quadratic-initial-tilt-v1"
)
EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_BACKEND_KIND = (
    "handcrafted-exact-rational-quadratic-known-law"
)
EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA = (
    "q_bar=c_cardinality[n]-sum_events(sum_j a[type,j]*x_j^2),x_j-in-R"
)
EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA = (
    "q_repr=c_cardinality[n]-sum_events(sum_j " "a[type,j]*Fraction.from_float(x_j)^2)"
)
# Backward-readable name for the represented execution formula.  The ideal
# formula is deliberately a distinct exported constant and digest input.
EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_FORMULA = (
    EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA
)
EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_CANONICALIZATION_POLICY = (
    "validate-exact-event-fields-before-ordering;canonical-positive-zero;"
    "ascending-(type_id,coordinate_tuple);multiplicity-preserved"
)
EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_LAW_LAYERS = (
    "ideal_rational_analytic_law",
    "binary64_parameter_analytic_law",
    "represented_exact_score_law",
    "operational_runtime_proposal_law",
    "learned_model_separation",
)
EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCOPE = (
    "handcrafted-known-law-score-provider;exact-rational-point-score-on-"
    "canonical-binary64-configurations;exact-U-zero;"
    "no-finite-ideal-real-global-L;represented-global-L-not-certified;"
    "ideal-rational-reference-separately-bound-from-stored-binary64-reference;"
    "ideal-real-polynomial-schema-and-represented-restriction-bound;"
    "not-configuration-initial-tilt-composer;not-cp50-v1-kernel-compatible;"
    "not-reference-sampler-law;not-iid-or-independence;not-rng-law;"
    "not-normalization;not-posterior;not-learned-model-evidence;"
    "not-path-or-sampler-admission;not-formal-test-28-closure"
)

IDEAL_RATIONAL_ANALYTIC_LAW_STATEMENT = (
    "theta and type weights are independently declared exact rationals; "
    "fibers are ideal real standard Gaussians and q_bar uses the certified "
    "real-polynomial schema; analytic Pi_N^rat, its normalizer, and its "
    "marginals have no runtime implication"
)
BINARY64_PARAMETER_ANALYTIC_LAW_STATEMENT = (
    "Pi_N^b64 is the mathematical reference obtained by interpreting the "
    "stored binary64 activity and normalized type weights exactly; parameter "
    "hex and Fraction.from_float values are bound, while its normalizer and "
    "marginals are not derived by this provider; Pi_N^b64 and Pi_N^rat are "
    "kept separately bound, equality is never assumed, and parameter equality "
    "is recorded field by field"
)
REPRESENTED_EXACT_SCORE_LAW_STATEMENT = (
    "q_repr is computed in Q on independently validated canonical binary64 "
    "configurations and is the pointwise restriction of the declared q_bar "
    "algebraic schema; exact Fraction, rounded display, and direct binary64 "
    "formula values remain distinct"
)
OPERATIONAL_RUNTIME_PROPOSAL_LAW_STATEMENT = (
    "mu_fp induced by CappedPoissonConfigurationReference sampling and an "
    "external NumPy/Philox source law is unknown; object custody and "
    "deterministic score replay do not verify Gaussian transforms, IID, or "
    "independence"
)
LEARNED_MODEL_SEPARATION_STATEMENT = (
    "the backend is handcrafted and uses no CP30 composer, learned model, "
    "checkpoint, or conditioning adapter; it supplies no posterior, model-"
    "quality, cross-domain-generality, manuscript, path, or sampler evidence"
)

MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS = 8192
MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS = 100_000
_ZERO_SHA256 = "0" * 64
_CERTIFICATE_TOKEN = object()
_EVALUATION_TOKEN = object()
_OWNER_TOKEN = object()
_RESERVED_FIXTURE_TOKEN = object()
_RESERVED_FIXTURE_IDS = frozenset(("T28-M1-Q", "T28-M2-Q"))
_M1_ROLE = hashlib.sha256(b"heterodiff-test28-m1-q-exact-score-provider-v1").hexdigest()
_M2_ROLE = hashlib.sha256(b"heterodiff-test28-m2-q-exact-score-provider-v1").hexdigest()


class ExactRationalQuadraticInitialTiltError(ArithmeticError):
    """Raised when bounded exact-score work cannot be completed safely."""


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("%s must be lowercase SHA-256 text" % name)
    return value


def _require_fraction(value: object, *, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError("%s must be an exact Fraction" % name)
    if (
        value.numerator.bit_length() > MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS
        or value.denominator.bit_length() > MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS
    ):
        raise ExactRationalQuadraticInitialTiltError(
            "%s exceeds the exact-integer resource limit" % name
        )
    return value


def _require_exact_integer(
    value: object, *, name: str, minimum: int, maximum: int
) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s lies outside the supported range" % name)
    return value


def _checked_fraction_sum(values: Tuple[Fraction, ...], *, name: str) -> Fraction:
    total = Fraction(0, 1)
    for index, value in enumerate(values):
        checked = _require_fraction(value, name="%s[%d]" % (name, index))
        total = _require_fraction(total + checked, name="%s partial sum" % name)
    return total


def _typed(value: object) -> object:
    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-v1", str(value)]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("digest floats must be finite")
        return ["float64-hex-v1", value.hex()]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is Fraction:
        return ["fraction-v1", str(value.numerator), str(value.denominator)]
    if type(value) is tuple:
        return ["tuple-v1", [_typed(item) for item in value]]
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("digest mappings require exact string keys")
            items.append((key, _typed(item)))
        return ["mapping-v1", sorted(items)]
    raise TypeError("unsupported digest value %s" % type(value).__name__)


def _semantic_digest(payload: Mapping[str, object], *, domain: str) -> str:
    return canonical_config_digest({domain: _typed(payload)})


def _bounded_exact_integer_mapping_keys(
    mapping: object,
    *,
    name: str,
    maximum_items: int,
) -> Tuple[int, ...]:
    if not isinstance(mapping, Mapping):
        raise TypeError("%s must be a mapping" % name)
    keys = []
    for key in mapping.keys():
        if len(keys) >= maximum_items:
            raise ValueError("%s exceeds the mapping-key limit" % name)
        if type(key) is not int or isinstance(key, bool):
            raise TypeError("%s keys must be exact non-boolean integers" % name)
        if not 0 <= key <= 2**63 - 1:
            raise ValueError("%s key lies outside the event-type range" % name)
        keys.append(key)
    return tuple(keys)


def _validate_live_reference_fields(
    reference: object,
) -> CappedPoissonConfigurationReference:
    """Recheck primitive reference invariants without trusting construction."""

    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("reference must be an exact capped-Poisson reference")
    if type(reference.type_ids) is not tuple:
        raise TypeError("live reference type_ids must be an exact tuple")
    if not 1 <= len(reference.type_ids) <= MAX_CONFIGURATION_EVENT_TYPES:
        raise ValueError("live reference type count is outside the frozen limit")
    type_ids = []
    for type_id in reference.type_ids:
        if type(type_id) is not int or isinstance(type_id, bool):
            raise TypeError("live reference type ids must be exact integers")
        if not 0 <= type_id <= 2**63 - 1:
            raise ValueError("live reference type id lies outside the supported range")
        type_ids.append(type_id)
    if tuple(type_ids) != tuple(sorted(set(type_ids))):
        raise ValueError("live reference type ids must be sorted and unique")
    expected_ids = tuple(type_ids)
    if type(reference.type_dimensions) is not MappingProxyType:
        raise TypeError("live reference type_dimensions must be a mapping proxy")
    if type(reference.type_weights) is not MappingProxyType:
        raise TypeError("live reference type_weights must be a mapping proxy")
    dimension_keys = _bounded_exact_integer_mapping_keys(
        reference.type_dimensions,
        name="live reference type_dimensions",
        maximum_items=MAX_CONFIGURATION_EVENT_TYPES,
    )
    weight_keys = _bounded_exact_integer_mapping_keys(
        reference.type_weights,
        name="live reference type_weights",
        maximum_items=MAX_CONFIGURATION_EVENT_TYPES,
    )
    if tuple(sorted(dimension_keys)) != expected_ids:
        raise ValueError("live reference dimension-key coverage differs")
    if tuple(sorted(weight_keys)) != expected_ids:
        raise ValueError("live reference weight-key coverage differs")
    for type_id in expected_ids:
        _require_exact_integer(
            reference.type_dimensions[type_id],
            name="live reference type dimension",
            minimum=0,
            maximum=MAX_TRANSFORMED_COORDINATE_DIMENSION,
        )
    _require_exact_integer(
        reference.total_cap,
        name="live reference total_cap",
        minimum=0,
        maximum=MAX_CONFIGURATION_CARDINALITY,
    )
    if type(reference.activity) is not float or not math.isfinite(reference.activity):
        raise TypeError("live reference activity must be a finite built-in float")
    if reference.activity <= 0.0:
        raise ValueError("live reference activity must be strictly positive")
    minimum_normal = float.fromhex("0x1.0000000000000p-1022")
    weights = []
    for type_id in expected_ids:
        weight = reference.type_weights[type_id]
        if type(weight) is not float or not math.isfinite(weight):
            raise TypeError("live reference weights must be finite built-in floats")
        if weight < minimum_normal:
            raise ValueError("live reference weights must be positive normal floats")
        weights.append(weight)
    if not math.isclose(
        math.fsum(weights),
        1.0,
        rel_tol=0.0,
        abs_tol=TYPE_WEIGHT_SUM_ATOL,
    ):
        raise ValueError("live reference weights do not sum to one")
    return reference


def _reference_parameter_sha256(reference: CappedPoissonConfigurationReference) -> str:
    _validate_live_reference_fields(reference)
    return _semantic_digest(
        {"parameter_key": reference.parameter_key()},
        domain="exact-rational-quadratic-reference-v1",
    )


def _context_sha256(context: Tuple[float, ...]) -> str:
    return _semantic_digest(
        {"context": context}, domain="exact-rational-quadratic-context-v1"
    )


def _configuration_sha256(configuration: TransformedConfiguration) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-exact-rational-quadratic-state-v1\x00")
    digest.update(len(configuration).to_bytes(8, "big", signed=False))
    for occurrence, event in enumerate(configuration):
        digest.update(occurrence.to_bytes(8, "big", signed=False))
        digest.update(event.event_type.to_bytes(8, "big", signed=False))
        digest.update(len(event.coordinates).to_bytes(8, "big", signed=False))
        for coordinate in event.coordinates:
            digest.update(struct.pack(">d", coordinate))
    return digest.hexdigest()


def _validate_context(context: object) -> Tuple[float, ...]:
    if type(context) is not tuple:
        raise TypeError("residual_context must be an exact tuple")
    if context:
        raise ValueError("known-law score providers require explicit empty context")
    return ()


def _canonical_configuration(
    reference: CappedPoissonConfigurationReference,
    configuration: object,
) -> TransformedConfiguration:
    """Validate hostile event internals before any tuple comparison or sorting."""

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
        if coordinate_count > MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS:
            raise ExactRationalQuadraticInitialTiltError(
                "configuration exceeds the exact-score term limit"
            )
        rebuilt = TransformedEvent(event.event_type, tuple(coordinates))
        if rebuilt.event_type != event.event_type or rebuilt.coordinates != (
            event.coordinates
        ):
            raise ValueError("event is not canonically represented")
        checked.append(rebuilt)
    canonical = tuple(sorted(checked, key=TransformedEvent.model_key))
    # Re-run the reference dimension/cap checks after hostile validation.
    reference_checked = reference.canonicalize(canonical)
    if reference_checked != canonical:
        raise ValueError("reference canonicalization changed a validated state")
    return canonical


def _optional_rounded_fraction(value: Fraction) -> Optional[float]:
    try:
        rounded = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(rounded):
        return None
    return 0.0 if rounded == 0.0 else rounded


def _is_dyadic(value: Fraction) -> bool:
    return value.denominator & (value.denominator - 1) == 0


def _fixture_spec_sha256(
    *,
    fixture_id: str,
    ideal_activity: Fraction,
    ideal_type_weights: Tuple[Fraction, ...],
    type_ids: Tuple[int, ...],
    type_dimensions: Tuple[int, ...],
    total_cap: int,
    count_penalties: Tuple[Fraction, ...],
    quadratic_coefficients: Tuple[Tuple[Fraction, ...], ...],
) -> str:
    return _semantic_digest(
        {
            "fixture_id": fixture_id,
            "ideal_activity": ideal_activity,
            "ideal_type_weights": ideal_type_weights,
            "type_ids": type_ids,
            "type_dimensions": type_dimensions,
            "total_cap": total_cap,
            "count_penalties": count_penalties,
            "quadratic_coefficients": quadratic_coefficients,
            "ideal_real_formula": (
                EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA
            ),
            "represented_formula": (
                EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA
            ),
        },
        domain="exact-rational-quadratic-fixture-spec-v1",
    )


@dataclass(frozen=True, eq=False, init=False)
class ExactRationalQuadraticInitialTiltCertificate:
    """Sealed parameter, formula, resource, and nonclaim ledger."""

    schema_version: str
    certificate_scope: str
    backend_kind: str
    fixture_id: str
    fixture_spec_sha256: str
    formula: str
    ideal_real_formula: str
    qbar_schema_sha256: str
    restriction_bridge_sha256: str
    canonicalization_policy: str
    law_layers: Tuple[str, ...]
    ideal_rational_analytic_law_statement: str
    binary64_parameter_analytic_law_statement: str
    represented_exact_score_law_statement: str
    operational_runtime_proposal_law_statement: str
    learned_model_separation_statement: str
    provider_role_sha256: str
    reference: CappedPoissonConfigurationReference
    reference_runtime_identity: int
    reference_parameter_key: Tuple[object, ...]
    reference_parameter_sha256: str
    type_ids: Tuple[int, ...]
    type_dimensions: Tuple[int, ...]
    total_cap: int
    ideal_activity: Fraction
    ideal_type_weights: Tuple[Fraction, ...]
    binary64_parameter_activity: Fraction
    binary64_parameter_type_weights: Tuple[Fraction, ...]
    binary64_parameter_activity_hex: str
    binary64_parameter_type_weight_hexes: Tuple[str, ...]
    ideal_and_binary64_parameter_activity_equal: bool
    ideal_and_binary64_parameter_type_weight_equalities: Tuple[bool, ...]
    ideal_and_binary64_parameter_reference_parameters_equal: bool
    binary64_parameter_normalizer_and_marginals_derived: bool
    count_penalties: Tuple[Fraction, ...]
    quadratic_coefficients: Tuple[Tuple[Fraction, ...], ...]
    residual_context_dimension: int
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    exact_global_upper_bound: Fraction
    exact_global_lower_bound: Optional[Fraction]
    maximum_exact_integer_bits: int
    maximum_score_terms: int
    ideal_real_polynomial_extension_declared: bool
    represented_restriction_identity_verified: bool
    exact_upper_bound_verified: bool
    ideal_real_global_lower_bound_exists: bool
    represented_domain_global_lower_bound_certified: bool
    analytic_pi_n_target_equality_verified: bool
    operational_reference_sampling_law_verified: bool
    iid_sequence_law_verified: bool
    proposal_independence_verified: bool
    gaussian_transform_verified: bool
    learned_model_used: bool
    learned_model_quality_evidence: bool
    cp50_v1_kernel_type_compatible: bool
    cp50_v1_dyadic_quota_compatible: bool
    certificate_digest_excludes_runtime_identity: bool
    normalization_certified: bool
    path_or_sampler_admitted: bool
    formal_test_28_closed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("exact-score certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("exact-score certificates require certification")
        if set(values) != set(self.__annotations__):
            raise TypeError("exact-score certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("exact-score certificates are not pickle objects")

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            self.schema_version,
            self.fixture_spec_sha256,
            self.reference_parameter_sha256,
            self.qbar_schema_sha256,
            self.restriction_bridge_sha256,
            self.certificate_sha256,
        )


def _certificate_payload(
    certificate: ExactRationalQuadraticInitialTiltCertificate,
) -> Mapping[str, object]:
    return {
        name: getattr(certificate, name)
        for name in certificate.__annotations__
        if name not in ("reference", "reference_runtime_identity", "certificate_sha256")
    }


def _validate_certificate(
    certificate: object,
) -> ExactRationalQuadraticInitialTiltCertificate:
    if type(certificate) is not ExactRationalQuadraticInitialTiltCertificate:
        raise TypeError("certificate has the wrong exact type")
    expected_text = {
        "schema_version": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCHEMA_VERSION,
        "certificate_scope": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCOPE,
        "backend_kind": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_BACKEND_KIND,
        "formula": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA,
        "ideal_real_formula": (
            EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA
        ),
        "canonicalization_policy": (
            EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_CANONICALIZATION_POLICY
        ),
        "ideal_rational_analytic_law_statement": (
            IDEAL_RATIONAL_ANALYTIC_LAW_STATEMENT
        ),
        "binary64_parameter_analytic_law_statement": (
            BINARY64_PARAMETER_ANALYTIC_LAW_STATEMENT
        ),
        "represented_exact_score_law_statement": (
            REPRESENTED_EXACT_SCORE_LAW_STATEMENT
        ),
        "operational_runtime_proposal_law_statement": (
            OPERATIONAL_RUNTIME_PROPOSAL_LAW_STATEMENT
        ),
        "learned_model_separation_statement": LEARNED_MODEL_SEPARATION_STATEMENT,
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("certificate %s differs" % name)
    if type(certificate.law_layers) is not tuple or any(
        type(value) is not str for value in certificate.law_layers
    ):
        raise TypeError("certificate law layers must be exact text")
    if certificate.law_layers != EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_LAW_LAYERS:
        raise ValueError("certificate law layers differ")
    if (
        type(certificate.fixture_id) is not str
        or not certificate.fixture_id
        or len(certificate.fixture_id) > 128
    ):
        raise ValueError("fixture_id must be nonempty exact text")
    for name in (
        "fixture_spec_sha256",
        "qbar_schema_sha256",
        "restriction_bridge_sha256",
        "provider_role_sha256",
        "reference_parameter_sha256",
        "residual_context_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    if type(certificate.reference) is not CappedPoissonConfigurationReference:
        raise TypeError("certificate reference has the wrong exact type")
    reference = _validate_live_reference_fields(certificate.reference)
    _require_exact_integer(
        certificate.reference_runtime_identity,
        name="certificate.reference_runtime_identity",
        minimum=1,
        maximum=(1 << 64) - 1,
    )
    if certificate.reference_runtime_identity != id(certificate.reference):
        raise ValueError("certificate reference identity differs")
    if type(certificate.reference_parameter_key) is not tuple:
        raise TypeError("certificate reference parameter key must be an exact tuple")
    expected_reference_key = reference.parameter_key()
    if _typed(certificate.reference_parameter_key) != _typed(expected_reference_key):
        raise ValueError("certificate reference parameter key differs")
    if certificate.reference_parameter_sha256 != _reference_parameter_sha256(reference):
        raise ValueError("certificate reference digest differs")
    expected_ids = tuple(reference.type_ids)
    expected_dimensions = tuple(reference.type_dimensions[t] for t in expected_ids)
    if type(certificate.type_ids) is not tuple or any(
        type(value) is not int or isinstance(value, bool)
        for value in certificate.type_ids
    ):
        raise TypeError("certificate type ids must be exact integers")
    if type(certificate.type_dimensions) is not tuple or any(
        type(value) is not int or isinstance(value, bool)
        for value in certificate.type_dimensions
    ):
        raise TypeError("certificate type dimensions must be exact integers")
    if certificate.type_ids != expected_ids:
        raise ValueError("certificate type ids differ from reference")
    if certificate.type_dimensions != expected_dimensions:
        raise ValueError("certificate type dimensions differ from reference")
    _require_exact_integer(
        certificate.total_cap,
        name="certificate.total_cap",
        minimum=1,
        maximum=MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS - 1,
    )
    if certificate.total_cap != reference.total_cap:
        raise ValueError("certificate cap differs from reference")
    _require_fraction(certificate.ideal_activity, name="ideal_activity")
    _require_fraction(
        certificate.binary64_parameter_activity,
        name="binary64_parameter_activity",
    )
    if certificate.ideal_activity <= 0:
        raise ValueError("ideal activity must be positive")
    if certificate.binary64_parameter_activity != Fraction.from_float(
        reference.activity
    ):
        raise ValueError("binary64-parameter activity fraction differs")
    if type(certificate.binary64_parameter_activity_hex) is not str:
        raise TypeError("binary64-parameter activity hex must be exact text")
    if certificate.binary64_parameter_activity_hex != reference.activity.hex():
        raise ValueError("binary64-parameter activity hex differs")
    if type(certificate.ideal_type_weights) is not tuple:
        raise TypeError("ideal type weights must be an exact tuple")
    if len(certificate.ideal_type_weights) != len(expected_ids):
        raise ValueError("ideal type-weight count differs")
    if type(certificate.binary64_parameter_type_weights) is not tuple:
        raise TypeError("binary64-parameter type weights must be an exact tuple")
    if len(certificate.binary64_parameter_type_weights) != len(expected_ids):
        raise ValueError("binary64-parameter type-weight count differs")
    ideal_weights = tuple(
        _require_fraction(value, name="ideal type weight")
        for value in certificate.ideal_type_weights
    )
    if any(value <= 0 for value in ideal_weights) or _checked_fraction_sum(
        ideal_weights, name="ideal type weights"
    ) != Fraction(1):
        raise ValueError("ideal type weights must be positive and sum exactly to one")
    binary64_weights = tuple(
        Fraction.from_float(reference.type_weights[type_id]) for type_id in expected_ids
    )
    supplied_binary64_weights = tuple(
        _require_fraction(value, name="binary64-parameter type weight")
        for value in certificate.binary64_parameter_type_weights
    )
    if supplied_binary64_weights != binary64_weights:
        raise ValueError("binary64-parameter type-weight fractions differ")
    expected_hexes = tuple(reference.type_weights[t].hex() for t in expected_ids)
    if type(certificate.binary64_parameter_type_weight_hexes) is not tuple or any(
        type(value) is not str
        for value in certificate.binary64_parameter_type_weight_hexes
    ):
        raise TypeError("binary64-parameter type-weight hexes must be exact text")
    if certificate.binary64_parameter_type_weight_hexes != expected_hexes:
        raise ValueError("binary64-parameter type-weight hexes differ")
    activity_equal = (
        certificate.ideal_activity == certificate.binary64_parameter_activity
    )
    weight_equalities = tuple(
        ideal == binary64 for ideal, binary64 in zip(ideal_weights, binary64_weights)
    )
    if certificate.ideal_and_binary64_parameter_activity_equal is not activity_equal:
        raise ValueError("activity layer-equality flag differs")
    if type(
        certificate.ideal_and_binary64_parameter_type_weight_equalities
    ) is not tuple or any(
        type(value) is not bool
        for value in certificate.ideal_and_binary64_parameter_type_weight_equalities
    ):
        raise TypeError("type-weight layer-equality flags must be exact booleans")
    if (
        certificate.ideal_and_binary64_parameter_type_weight_equalities
        != weight_equalities
    ):
        raise ValueError("type-weight layer-equality flags differ")
    all_equal = activity_equal and all(weight_equalities)
    if (
        certificate.ideal_and_binary64_parameter_reference_parameters_equal
        is not all_equal
    ):
        raise ValueError("reference layer-equality flag differs")
    if certificate.binary64_parameter_normalizer_and_marginals_derived:
        raise ValueError("binary64 analytic normalizers are not derived here")
    if (
        type(certificate.count_penalties) is not tuple
        or len(certificate.count_penalties) != certificate.total_cap + 1
    ):
        raise ValueError("count-penalty table has the wrong length")
    penalties = tuple(
        _require_fraction(value, name="count penalty")
        for value in certificate.count_penalties
    )
    if any(value > 0 for value in penalties) or max(penalties) != 0:
        raise ValueError("count penalties must certify exact U=0")
    if type(certificate.quadratic_coefficients) is not tuple or len(
        certificate.quadratic_coefficients
    ) != len(expected_ids):
        raise ValueError("quadratic coefficient rows differ from reference types")
    coefficients = []
    for row, dimension in zip(certificate.quadratic_coefficients, expected_dimensions):
        if type(row) is not tuple or len(row) != dimension:
            raise ValueError("quadratic coefficient row has the wrong dimension")
        checked_row = tuple(
            _require_fraction(value, name="quadratic coefficient") for value in row
        )
        if any(value < 0 for value in checked_row):
            raise ValueError("quadratic coefficients must be nonnegative")
        coefficients.append(checked_row)
    if not any(value > 0 for row in coefficients for value in row):
        raise ValueError("a no-lower-bound provider requires a positive coefficient")
    context = _validate_context(certificate.residual_context)
    _require_exact_integer(
        certificate.residual_context_dimension,
        name="certificate.residual_context_dimension",
        minimum=0,
        maximum=0,
    )
    if certificate.residual_context_dimension != 0:
        raise ValueError("known-law residual context dimension must be zero")
    if certificate.residual_context_sha256 != _context_sha256(context):
        raise ValueError("residual context digest differs")
    _require_fraction(
        certificate.exact_global_upper_bound,
        name="certificate.exact_global_upper_bound",
    )
    if certificate.exact_global_upper_bound != Fraction(0, 1):
        raise ValueError("the exact global upper bound must equal zero")
    if certificate.exact_global_lower_bound is not None:
        raise ValueError("no finite exact global lower bound is certified")
    _require_exact_integer(
        certificate.maximum_exact_integer_bits,
        name="certificate.maximum_exact_integer_bits",
        minimum=1,
        maximum=MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS,
    )
    if certificate.maximum_exact_integer_bits != (
        MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS
    ):
        raise ValueError("exact-integer limit differs")
    _require_exact_integer(
        certificate.maximum_score_terms,
        name="certificate.maximum_score_terms",
        minimum=1,
        maximum=MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS,
    )
    if certificate.maximum_score_terms != MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS:
        raise ValueError("score-term limit differs")
    expected_spec = _fixture_spec_sha256(
        fixture_id=certificate.fixture_id,
        ideal_activity=certificate.ideal_activity,
        ideal_type_weights=ideal_weights,
        type_ids=expected_ids,
        type_dimensions=expected_dimensions,
        total_cap=certificate.total_cap,
        count_penalties=penalties,
        quadratic_coefficients=tuple(coefficients),
    )
    if certificate.fixture_spec_sha256 != expected_spec:
        raise ValueError("fixture specification digest differs")
    expected_qbar = _semantic_digest(
        {
            "ideal_real_formula": certificate.ideal_real_formula,
            "type_ids": expected_ids,
            "type_dimensions": expected_dimensions,
            "count_penalties": penalties,
            "quadratic_coefficients": tuple(coefficients),
        },
        domain="exact-rational-quadratic-qbar-schema-v1",
    )
    if certificate.qbar_schema_sha256 != expected_qbar:
        raise ValueError("qbar schema digest differs")
    expected_bridge = _semantic_digest(
        {
            "ideal_real_formula": certificate.ideal_real_formula,
            "represented_formula": certificate.formula,
            "type_ids": expected_ids,
            "type_dimensions": expected_dimensions,
            "count_penalties": penalties,
            "quadratic_coefficients": tuple(coefficients),
            "restriction_domain": "canonical-built-in-binary64-coordinates",
        },
        domain="exact-rational-quadratic-restriction-bridge-v1",
    )
    if certificate.restriction_bridge_sha256 != expected_bridge:
        raise ValueError("restriction bridge digest differs")
    if certificate.fixture_id in _RESERVED_FIXTURE_IDS:
        if certificate.fixture_id == "T28-M1-Q":
            reserved_expected = (
                (0, 1),
                (0, 1),
                1,
                Fraction(1),
                (Fraction(2, 5), Fraction(3, 5)),
                (Fraction(0), Fraction(0)),
                ((), (Fraction(1, 4),)),
                _M1_ROLE,
            )
        else:
            reserved_expected = (
                (0, 1),
                (1, 2),
                2,
                Fraction(1),
                (Fraction(2, 5), Fraction(3, 5)),
                (Fraction(0), Fraction(0), Fraction(-1, 4)),
                ((Fraction(1, 4),), (Fraction(1, 8), Fraction(1, 6))),
                _M2_ROLE,
            )
        reserved_supplied = (
            certificate.type_ids,
            certificate.type_dimensions,
            certificate.total_cap,
            certificate.ideal_activity,
            certificate.ideal_type_weights,
            penalties,
            tuple(coefficients),
            certificate.provider_role_sha256,
        )
        if reserved_supplied != reserved_expected:
            raise ValueError("canonical Test-28 certificate specification differs")
        if reference.activity.hex() != (1.0).hex() or tuple(
            reference.type_weights[t].hex() for t in reference.type_ids
        ) != ((0.4).hex(), (0.6).hex()):
            raise ValueError("canonical Test-28 certificate reference differs")
    expected_dyadic = all(
        _is_dyadic(value)
        for value in penalties + tuple(value for row in coefficients for value in row)
    )
    true_flags = (
        "ideal_real_polynomial_extension_declared",
        "represented_restriction_identity_verified",
        "exact_upper_bound_verified",
        "certificate_digest_excludes_runtime_identity",
    )
    false_flags = (
        "binary64_parameter_normalizer_and_marginals_derived",
        "ideal_real_global_lower_bound_exists",
        "represented_domain_global_lower_bound_certified",
        "analytic_pi_n_target_equality_verified",
        "operational_reference_sampling_law_verified",
        "iid_sequence_law_verified",
        "proposal_independence_verified",
        "gaussian_transform_verified",
        "learned_model_used",
        "learned_model_quality_evidence",
        "cp50_v1_kernel_type_compatible",
        "normalization_certified",
        "path_or_sampler_admitted",
        "formal_test_28_closed",
    )
    for name in true_flags + false_flags + ("cp50_v1_dyadic_quota_compatible",):
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("certificate positive claim flags differ")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("certificate negative claim flags differ")
    if certificate.cp50_v1_dyadic_quota_compatible is not expected_dyadic:
        raise ValueError("dyadic quota-compatibility flag differs")
    if certificate.fixture_id in _RESERVED_FIXTURE_IDS and (
        certificate.ideal_and_binary64_parameter_reference_parameters_equal
    ):
        raise ValueError("canonical Test-28 reference layers must remain unequal")
    expected_digest = _semantic_digest(
        _certificate_payload(certificate),
        domain="exact-rational-quadratic-certificate-v1",
    )
    if certificate.certificate_sha256 != expected_digest:
        raise ValueError("certificate digest differs")
    return certificate


def _make_certificate(
    reference: CappedPoissonConfigurationReference,
    *,
    fixture_id: str,
    ideal_activity: Fraction,
    ideal_type_weights: Tuple[Fraction, ...],
    count_penalties: Tuple[Fraction, ...],
    quadratic_coefficients: Tuple[Tuple[Fraction, ...], ...],
    residual_context: Tuple[float, ...],
    provider_role_sha256: str,
) -> ExactRationalQuadraticInitialTiltCertificate:
    reference = _validate_live_reference_fields(reference)
    type_ids = tuple(reference.type_ids)
    dimensions = tuple(reference.type_dimensions[t] for t in type_ids)
    binary64_activity = Fraction.from_float(reference.activity)
    binary64_weights = tuple(
        Fraction.from_float(reference.type_weights[t]) for t in type_ids
    )
    weight_equalities = tuple(
        ideal == binary64
        for ideal, binary64 in zip(ideal_type_weights, binary64_weights)
    )
    activity_equal = ideal_activity == binary64_activity
    spec_sha = _fixture_spec_sha256(
        fixture_id=fixture_id,
        ideal_activity=ideal_activity,
        ideal_type_weights=ideal_type_weights,
        type_ids=type_ids,
        type_dimensions=dimensions,
        total_cap=reference.total_cap,
        count_penalties=count_penalties,
        quadratic_coefficients=quadratic_coefficients,
    )
    qbar_sha = _semantic_digest(
        {
            "ideal_real_formula": (
                EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA
            ),
            "type_ids": type_ids,
            "type_dimensions": dimensions,
            "count_penalties": count_penalties,
            "quadratic_coefficients": quadratic_coefficients,
        },
        domain="exact-rational-quadratic-qbar-schema-v1",
    )
    bridge_sha = _semantic_digest(
        {
            "ideal_real_formula": (
                EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA
            ),
            "represented_formula": (
                EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA
            ),
            "type_ids": type_ids,
            "type_dimensions": dimensions,
            "count_penalties": count_penalties,
            "quadratic_coefficients": quadratic_coefficients,
            "restriction_domain": "canonical-built-in-binary64-coordinates",
        },
        domain="exact-rational-quadratic-restriction-bridge-v1",
    )
    dyadic = all(
        _is_dyadic(value)
        for value in count_penalties
        + tuple(value for row in quadratic_coefficients for value in row)
    )
    values = {
        "schema_version": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCHEMA_VERSION,
        "certificate_scope": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCOPE,
        "backend_kind": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_BACKEND_KIND,
        "fixture_id": fixture_id,
        "fixture_spec_sha256": spec_sha,
        "formula": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA,
        "ideal_real_formula": (
            EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA
        ),
        "qbar_schema_sha256": qbar_sha,
        "restriction_bridge_sha256": bridge_sha,
        "canonicalization_policy": (
            EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_CANONICALIZATION_POLICY
        ),
        "law_layers": EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_LAW_LAYERS,
        "ideal_rational_analytic_law_statement": (
            IDEAL_RATIONAL_ANALYTIC_LAW_STATEMENT
        ),
        "binary64_parameter_analytic_law_statement": (
            BINARY64_PARAMETER_ANALYTIC_LAW_STATEMENT
        ),
        "represented_exact_score_law_statement": (
            REPRESENTED_EXACT_SCORE_LAW_STATEMENT
        ),
        "operational_runtime_proposal_law_statement": (
            OPERATIONAL_RUNTIME_PROPOSAL_LAW_STATEMENT
        ),
        "learned_model_separation_statement": LEARNED_MODEL_SEPARATION_STATEMENT,
        "provider_role_sha256": provider_role_sha256,
        "reference": reference,
        "reference_runtime_identity": id(reference),
        "reference_parameter_key": reference.parameter_key(),
        "reference_parameter_sha256": _reference_parameter_sha256(reference),
        "type_ids": type_ids,
        "type_dimensions": dimensions,
        "total_cap": reference.total_cap,
        "ideal_activity": ideal_activity,
        "ideal_type_weights": ideal_type_weights,
        "binary64_parameter_activity": binary64_activity,
        "binary64_parameter_type_weights": binary64_weights,
        "binary64_parameter_activity_hex": reference.activity.hex(),
        "binary64_parameter_type_weight_hexes": tuple(
            reference.type_weights[t].hex() for t in type_ids
        ),
        "ideal_and_binary64_parameter_activity_equal": activity_equal,
        "ideal_and_binary64_parameter_type_weight_equalities": weight_equalities,
        "ideal_and_binary64_parameter_reference_parameters_equal": (
            activity_equal and all(weight_equalities)
        ),
        "binary64_parameter_normalizer_and_marginals_derived": False,
        "count_penalties": count_penalties,
        "quadratic_coefficients": quadratic_coefficients,
        "residual_context_dimension": 0,
        "residual_context": residual_context,
        "residual_context_sha256": _context_sha256(residual_context),
        "exact_global_upper_bound": Fraction(0, 1),
        "exact_global_lower_bound": None,
        "maximum_exact_integer_bits": MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS,
        "maximum_score_terms": MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS,
        "ideal_real_polynomial_extension_declared": True,
        "represented_restriction_identity_verified": True,
        "exact_upper_bound_verified": True,
        "ideal_real_global_lower_bound_exists": False,
        "represented_domain_global_lower_bound_certified": False,
        "analytic_pi_n_target_equality_verified": False,
        "operational_reference_sampling_law_verified": False,
        "iid_sequence_law_verified": False,
        "proposal_independence_verified": False,
        "gaussian_transform_verified": False,
        "learned_model_used": False,
        "learned_model_quality_evidence": False,
        "cp50_v1_kernel_type_compatible": False,
        "cp50_v1_dyadic_quota_compatible": dyadic,
        "certificate_digest_excludes_runtime_identity": True,
        "normalization_certified": False,
        "path_or_sampler_admitted": False,
        "formal_test_28_closed": False,
        "certificate_sha256": _ZERO_SHA256,
    }
    provisional = object.__new__(ExactRationalQuadraticInitialTiltCertificate)
    for name in ExactRationalQuadraticInitialTiltCertificate.__annotations__:
        object.__setattr__(provisional, name, values[name])
    values["certificate_sha256"] = _semantic_digest(
        _certificate_payload(provisional),
        domain="exact-rational-quadratic-certificate-v1",
    )
    return ExactRationalQuadraticInitialTiltCertificate(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class ExactRationalQuadraticInitialTiltPointEvaluation:
    """One sealed exact score with distinct represented numeric layers."""

    certificate: ExactRationalQuadraticInitialTiltCertificate
    certificate_sha256: str
    fixture_id: str
    configuration: TransformedConfiguration
    configuration_sha256: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    cardinality: int
    count_penalty: Fraction
    exact_log_weight: Fraction
    exact_log_weight_numerator: int
    exact_log_weight_denominator: int
    rounded_exact_log_weight: Optional[float]
    direct_binary64_log_weight: Optional[float]
    exact_upper_bound_respected: bool
    represented_restriction_identity_verified: bool
    evaluation_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("exact-score evaluations cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError("exact-score evaluations are provider-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("exact-score evaluation fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("exact-score evaluations are not pickle objects")


def _evaluation_payload(
    evaluation: ExactRationalQuadraticInitialTiltPointEvaluation,
) -> Mapping[str, object]:
    return {
        name: getattr(evaluation, name)
        for name in evaluation.__annotations__
        if name not in ("certificate", "configuration", "evaluation_sha256")
    }


def _optional_float_matches(left: object, right: object) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return (
        type(left) is float
        and type(right) is float
        and struct.pack(">d", left) == struct.pack(">d", right)
    )


def _score_layers(
    certificate: ExactRationalQuadraticInitialTiltCertificate,
    configuration: TransformedConfiguration,
) -> Tuple[Fraction, Optional[float], Optional[float]]:
    exact = certificate.count_penalties[len(configuration)]
    direct: Optional[float] = _optional_rounded_fraction(exact)
    coefficient_by_type = dict(
        zip(certificate.type_ids, certificate.quadratic_coefficients)
    )
    for event in configuration:
        row = coefficient_by_type[event.event_type]
        for coefficient, coordinate in zip(row, event.coordinates):
            exact -= coefficient * Fraction.from_float(coordinate) ** 2
            _require_fraction(exact, name="exact represented log weight")
            if direct is not None:
                try:
                    candidate = direct - float(coefficient) * (coordinate * coordinate)
                except (OverflowError, ValueError):
                    direct = None
                else:
                    direct = candidate if math.isfinite(candidate) else None
    rounded = _optional_rounded_fraction(exact)
    if direct == 0.0:
        direct = 0.0
    return exact, rounded, direct


class ExactRationalQuadraticInitialTilt:
    """Immutable owner of one reference-bound exact quadratic score."""

    __slots__ = (
        "_reference",
        "_certificate",
        "_reference_identity",
        "_certificate_identity",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("exact-score providers cannot be subclassed")

    def __init__(
        self,
        *,
        reference: CappedPoissonConfigurationReference = None,  # type: ignore[assignment]
        certificate: ExactRationalQuadraticInitialTiltCertificate = None,  # type: ignore[assignment]
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("exact-score providers require certification")
        object.__setattr__(self, "_reference", reference)
        object.__setattr__(self, "_certificate", certificate)
        object.__setattr__(self, "_reference_identity", reference)
        object.__setattr__(self, "_certificate_identity", certificate)
        self.revalidate_live_reference()

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("exact-score providers are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("exact-score providers are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("exact-score providers are not pickle objects")

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        self.revalidate_live_reference()
        return self._reference

    @property
    def certificate(self) -> ExactRationalQuadraticInitialTiltCertificate:
        self.revalidate_live_reference()
        return self._certificate

    @property
    def residual_context(self) -> Tuple[float, ...]:
        self.revalidate_live_reference()
        return self._certificate.residual_context

    def parameter_key(self) -> Tuple[object, ...]:
        certificate = self.revalidate_live_reference()
        return (
            EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCHEMA_VERSION,
            certificate.fixture_spec_sha256,
            certificate.reference_parameter_sha256,
            certificate.qbar_schema_sha256,
            certificate.restriction_bridge_sha256,
            certificate.certificate_sha256,
        )

    def revalidate_live_reference(
        self,
    ) -> ExactRationalQuadraticInitialTiltCertificate:
        if self._reference is not self._reference_identity:
            raise ValueError("provider reference identity sentinel differs")
        if self._certificate is not self._certificate_identity:
            raise ValueError("provider certificate identity sentinel differs")
        certificate = _validate_certificate(self._certificate)
        if certificate.reference is not self._reference:
            raise ValueError("provider reference identity differs from certificate")
        return certificate

    def evaluate(
        self,
        configuration: object,
        *,
        residual_context: object,
    ) -> ExactRationalQuadraticInitialTiltPointEvaluation:
        certificate = self.revalidate_live_reference()
        context = _validate_context(residual_context)
        if context != certificate.residual_context:
            raise ValueError("residual context differs from provider certificate")
        canonical = _canonical_configuration(self._reference, configuration)
        exact, rounded, direct_value = _score_layers(certificate, canonical)
        values = {
            "certificate": certificate,
            "certificate_sha256": certificate.certificate_sha256,
            "fixture_id": certificate.fixture_id,
            "configuration": canonical,
            "configuration_sha256": _configuration_sha256(canonical),
            "residual_context": context,
            "residual_context_sha256": certificate.residual_context_sha256,
            "cardinality": len(canonical),
            "count_penalty": certificate.count_penalties[len(canonical)],
            "exact_log_weight": exact,
            "exact_log_weight_numerator": exact.numerator,
            "exact_log_weight_denominator": exact.denominator,
            "rounded_exact_log_weight": rounded,
            "direct_binary64_log_weight": direct_value,
            "exact_upper_bound_respected": exact
            <= certificate.exact_global_upper_bound,
            "represented_restriction_identity_verified": True,
            "evaluation_sha256": _ZERO_SHA256,
        }
        provisional = object.__new__(ExactRationalQuadraticInitialTiltPointEvaluation)
        for name in ExactRationalQuadraticInitialTiltPointEvaluation.__annotations__:
            object.__setattr__(provisional, name, values[name])
        values["evaluation_sha256"] = _semantic_digest(
            _evaluation_payload(provisional),
            domain="exact-rational-quadratic-evaluation-v1",
        )
        result = ExactRationalQuadraticInitialTiltPointEvaluation(
            **values, _construction_token=_EVALUATION_TOKEN
        )
        return self._validate_evaluation_structure(result)

    def _validate_evaluation_structure(
        self,
        evaluation: object,
    ) -> ExactRationalQuadraticInitialTiltPointEvaluation:
        if type(evaluation) is not ExactRationalQuadraticInitialTiltPointEvaluation:
            raise TypeError("evaluation has the wrong exact type")
        certificate = self.revalidate_live_reference()
        if evaluation.certificate is not certificate:
            raise ValueError("evaluation belongs to a different certificate")
        if evaluation.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("evaluation certificate digest differs")
        if evaluation.fixture_id != certificate.fixture_id:
            raise ValueError("evaluation fixture differs")
        canonical = _canonical_configuration(self._reference, evaluation.configuration)
        if canonical != evaluation.configuration:
            raise ValueError("evaluation configuration is not canonical")
        if evaluation.configuration_sha256 != _configuration_sha256(canonical):
            raise ValueError("evaluation configuration digest differs")
        if (
            _validate_context(evaluation.residual_context)
            != certificate.residual_context
        ):
            raise ValueError("evaluation context differs")
        if evaluation.residual_context_sha256 != certificate.residual_context_sha256:
            raise ValueError("evaluation context digest differs")
        _require_exact_integer(
            evaluation.cardinality,
            name="evaluation.cardinality",
            minimum=0,
            maximum=certificate.total_cap,
        )
        if evaluation.cardinality != len(canonical):
            raise ValueError("evaluation cardinality differs")
        expected_penalty = certificate.count_penalties[len(canonical)]
        _require_fraction(evaluation.count_penalty, name="evaluation.count_penalty")
        if evaluation.count_penalty != expected_penalty:
            raise ValueError("evaluation count penalty differs")
        exact = _require_fraction(evaluation.exact_log_weight, name="exact log weight")
        _require_exact_integer(
            evaluation.exact_log_weight_numerator,
            name="evaluation.exact_log_weight_numerator",
            minimum=-(1 << MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS),
            maximum=(1 << MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS),
        )
        _require_exact_integer(
            evaluation.exact_log_weight_denominator,
            name="evaluation.exact_log_weight_denominator",
            minimum=1,
            maximum=(1 << MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS),
        )
        if (
            evaluation.exact_log_weight_numerator != exact.numerator
            or evaluation.exact_log_weight_denominator != exact.denominator
        ):
            raise ValueError("evaluation exact fraction parts differ")
        recomputed, recomputed_rounded, recomputed_direct = _score_layers(
            certificate, canonical
        )
        if exact != recomputed:
            raise ValueError("evaluation exact score differs from retained state")
        for optional_name in (
            "rounded_exact_log_weight",
            "direct_binary64_log_weight",
        ):
            value = getattr(evaluation, optional_name)
            if value is not None and (
                type(value) is not float or not math.isfinite(value)
            ):
                raise ValueError("evaluation optional score layer is invalid")
            if value == 0.0 and math.copysign(1.0, value) < 0.0:
                raise ValueError("evaluation optional score must use positive zero")
        if not _optional_float_matches(
            evaluation.rounded_exact_log_weight, recomputed_rounded
        ):
            raise ValueError("evaluation rounded exact score differs")
        if not _optional_float_matches(
            evaluation.direct_binary64_log_weight, recomputed_direct
        ):
            raise ValueError("evaluation direct binary64 score differs")
        if evaluation.exact_upper_bound_respected is not True:
            raise ValueError("evaluation upper-bound witness differs")
        if exact > certificate.exact_global_upper_bound:
            raise ValueError("evaluation exceeds exact U")
        if evaluation.represented_restriction_identity_verified is not True:
            raise ValueError("evaluation restriction-identity flag differs")
        _require_sha256(evaluation.evaluation_sha256, name="evaluation digest")
        expected_digest = _semantic_digest(
            _evaluation_payload(evaluation),
            domain="exact-rational-quadratic-evaluation-v1",
        )
        if evaluation.evaluation_sha256 != expected_digest:
            raise ValueError("evaluation digest differs")
        return evaluation

    def validate_evaluation(
        self,
        evaluation: object,
        configuration: object,
        *,
        residual_context: object,
    ) -> ExactRationalQuadraticInitialTiltPointEvaluation:
        checked = self._validate_evaluation_structure(evaluation)
        expected = self.evaluate(configuration, residual_context=residual_context)
        for name in ExactRationalQuadraticInitialTiltPointEvaluation.__annotations__:
            supplied = getattr(checked, name)
            wanted = getattr(expected, name)
            if name == "certificate":
                matches = supplied is wanted
            elif type(supplied) is float and type(wanted) is float:
                matches = struct.pack(">d", supplied) == struct.pack(">d", wanted)
            else:
                matches = supplied == wanted
            if not matches:
                raise ValueError("evaluation field %s differs from replay" % name)
        return checked


def _certify_exact_rational_quadratic_initial_tilt(
    reference: CappedPoissonConfigurationReference,
    *,
    fixture_id: object,
    ideal_activity: Fraction,
    ideal_type_weights: Mapping[int, Fraction],
    count_penalties: Tuple[Fraction, ...],
    quadratic_coefficients_by_type: Mapping[int, Tuple[Fraction, ...]],
    residual_context: object,
    provider_role_sha256: object,
    _reserved_fixture_token: object,
) -> ExactRationalQuadraticInitialTilt:
    """Certify one reference-bound exact quadratic known-law provider."""

    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("reference must be an exact capped-Poisson reference")
    reference = _validate_live_reference_fields(reference)
    if type(fixture_id) is not str or not fixture_id or len(fixture_id) > 128:
        raise ValueError("fixture_id must be nonempty exact text")
    if fixture_id in _RESERVED_FIXTURE_IDS:
        if _reserved_fixture_token is not _RESERVED_FIXTURE_TOKEN:
            raise ValueError("canonical Test-28 fixture ids are builder-reserved")
    elif _reserved_fixture_token is not None:
        raise ValueError("reserved fixture authority cannot label a generic fixture")
    if reference.total_cap < 1:
        raise ValueError("a no-global-lower-bound provider requires cap at least one")
    if reference.total_cap + 1 > MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS:
        raise ValueError("count-penalty specification exceeds the term limit")
    total_dimensions = sum(reference.type_dimensions.values())
    if total_dimensions > MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS:
        raise ValueError("coefficient specification exceeds the term limit")
    role = _require_sha256(provider_role_sha256, name="provider_role_sha256")
    ideal_theta = _require_fraction(ideal_activity, name="ideal_activity")
    if ideal_theta <= 0:
        raise ValueError("ideal_activity must be positive")
    if not isinstance(ideal_type_weights, Mapping):
        raise TypeError("ideal_type_weights must be a mapping")
    ideal_weight_keys = _bounded_exact_integer_mapping_keys(
        ideal_type_weights,
        name="ideal_type_weights",
        maximum_items=len(reference.type_ids),
    )
    if tuple(sorted(ideal_weight_keys)) != tuple(reference.type_ids):
        raise ValueError("ideal_type_weights must specify every reference type")
    ideal_weights = tuple(
        _require_fraction(ideal_type_weights[t], name="ideal type weight")
        for t in reference.type_ids
    )
    if any(value <= 0 for value in ideal_weights) or _checked_fraction_sum(
        ideal_weights, name="ideal type weights"
    ) != Fraction(1):
        raise ValueError("ideal type weights must be positive and sum to one")
    if type(count_penalties) is not tuple:
        raise TypeError("count_penalties must be an exact tuple")
    if len(count_penalties) > MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS:
        raise ValueError("count_penalties exceeds the specification limit")
    penalties = tuple(
        _require_fraction(value, name="count penalty") for value in count_penalties
    )
    if len(penalties) != reference.total_cap + 1:
        raise ValueError("count_penalties has the wrong length")
    if any(value > 0 for value in penalties) or max(penalties) != 0:
        raise ValueError("count_penalties must have exact global maximum zero")
    if not isinstance(quadratic_coefficients_by_type, Mapping):
        raise TypeError("quadratic_coefficients_by_type must be a mapping")
    coefficient_keys = _bounded_exact_integer_mapping_keys(
        quadratic_coefficients_by_type,
        name="quadratic_coefficients_by_type",
        maximum_items=len(reference.type_ids),
    )
    if tuple(sorted(coefficient_keys)) != tuple(reference.type_ids):
        raise ValueError("quadratic coefficients must specify every reference type")
    coefficient_rows = []
    for type_id in reference.type_ids:
        row = quadratic_coefficients_by_type[type_id]
        if type(row) is not tuple:
            raise TypeError("quadratic coefficient rows must be exact tuples")
        if len(row) != reference.type_dimensions[type_id]:
            raise ValueError("quadratic coefficient row has the wrong dimension")
        checked = tuple(
            _require_fraction(value, name="quadratic coefficient") for value in row
        )
        if any(value < 0 for value in checked):
            raise ValueError("quadratic coefficients must be nonnegative")
        coefficient_rows.append(checked)
    if not any(value > 0 for row in coefficient_rows for value in row):
        raise ValueError("at least one positive quadratic coefficient is required")
    context = _validate_context(residual_context)
    if fixture_id in _RESERVED_FIXTURE_IDS:
        if fixture_id == "T28-M1-Q":
            expected = (
                (0, 1),
                (0, 1),
                1,
                (Fraction(0), Fraction(0)),
                ((), (Fraction(1, 4),)),
                _M1_ROLE,
            )
        else:
            expected = (
                (0, 1),
                (1, 2),
                2,
                (Fraction(0), Fraction(0), Fraction(-1, 4)),
                ((Fraction(1, 4),), (Fraction(1, 8), Fraction(1, 6))),
                _M2_ROLE,
            )
        supplied = (
            tuple(reference.type_ids),
            tuple(reference.type_dimensions[t] for t in reference.type_ids),
            reference.total_cap,
            penalties,
            tuple(coefficient_rows),
            role,
        )
        if supplied != expected:
            raise ValueError("canonical Test-28 score specification differs")
        if ideal_theta != Fraction(1) or ideal_weights != (
            Fraction(2, 5),
            Fraction(3, 5),
        ):
            raise ValueError("canonical Test-28 ideal reference intent differs")
        if reference.activity.hex() != (1.0).hex() or tuple(
            reference.type_weights[t].hex() for t in reference.type_ids
        ) != ((0.4).hex(), (0.6).hex()):
            raise ValueError("canonical Test-28 binary64 reference differs")
        if context != ():
            raise ValueError("canonical Test-28 context differs")
    certificate = _make_certificate(
        reference,
        fixture_id=fixture_id,
        ideal_activity=ideal_theta,
        ideal_type_weights=ideal_weights,
        count_penalties=penalties,
        quadratic_coefficients=tuple(coefficient_rows),
        residual_context=context,
        provider_role_sha256=role,
    )
    return ExactRationalQuadraticInitialTilt(
        reference=reference,
        certificate=certificate,
        _construction_token=_OWNER_TOKEN,
    )


def certify_exact_rational_quadratic_initial_tilt(
    reference: CappedPoissonConfigurationReference,
    *,
    fixture_id: object,
    ideal_activity: Fraction,
    ideal_type_weights: Mapping[int, Fraction],
    count_penalties: Tuple[Fraction, ...],
    quadratic_coefficients_by_type: Mapping[int, Tuple[Fraction, ...]],
    residual_context: object,
    provider_role_sha256: object,
) -> ExactRationalQuadraticInitialTilt:
    """Certify a generic provider; canonical Test-28 ids remain reserved."""

    return _certify_exact_rational_quadratic_initial_tilt(
        reference,
        fixture_id=fixture_id,
        ideal_activity=ideal_activity,
        ideal_type_weights=ideal_type_weights,
        count_penalties=count_penalties,
        quadratic_coefficients_by_type=quadratic_coefficients_by_type,
        residual_context=residual_context,
        provider_role_sha256=provider_role_sha256,
        _reserved_fixture_token=None,
    )


def require_matching_exact_rational_quadratic_initial_tilt(
    reference: CappedPoissonConfigurationReference,
    provider: ExactRationalQuadraticInitialTilt,
) -> ExactRationalQuadraticInitialTilt:
    """Require exact reference custody and reconstruct live certificate state."""

    if type(reference) is not CappedPoissonConfigurationReference:
        raise TypeError("reference has the wrong exact type")
    if type(provider) is not ExactRationalQuadraticInitialTilt:
        raise TypeError("provider has the wrong exact type")
    if provider.reference is not reference:
        raise ValueError("provider belongs to a different reference object")
    provider.revalidate_live_reference()
    return provider


def validate_exact_rational_quadratic_initial_tilt_certificate(
    reference: CappedPoissonConfigurationReference,
    provider: ExactRationalQuadraticInitialTilt,
) -> ExactRationalQuadraticInitialTiltCertificate:
    """Return the structurally and live-reference validated certificate."""

    return require_matching_exact_rational_quadratic_initial_tilt(
        reference, provider
    ).certificate


def build_t28_m1_q_exact_score_provider() -> ExactRationalQuadraticInitialTilt:
    """Build the cap-one atom-plus-one-dimensional ``T28-M1-Q`` provider."""

    reference = CappedPoissonConfigurationReference(
        {0: 0, 1: 1},
        {0: 0.4, 1: 0.6},
        activity=1.0,
        total_cap=1,
    )
    return _certify_exact_rational_quadratic_initial_tilt(
        reference,
        fixture_id="T28-M1-Q",
        ideal_activity=Fraction(1, 1),
        ideal_type_weights={0: Fraction(2, 5), 1: Fraction(3, 5)},
        count_penalties=(Fraction(0, 1), Fraction(0, 1)),
        quadratic_coefficients_by_type={
            0: (),
            1: (Fraction(1, 4),),
        },
        residual_context=(),
        provider_role_sha256=_M1_ROLE,
        _reserved_fixture_token=_RESERVED_FIXTURE_TOKEN,
    )


def build_t28_m2_q_exact_score_provider() -> ExactRationalQuadraticInitialTilt:
    """Build the cap-two heterogeneous ``T28-M2-Q`` provider."""

    reference = CappedPoissonConfigurationReference(
        {0: 1, 1: 2},
        {0: 0.4, 1: 0.6},
        activity=1.0,
        total_cap=2,
    )
    return _certify_exact_rational_quadratic_initial_tilt(
        reference,
        fixture_id="T28-M2-Q",
        ideal_activity=Fraction(1, 1),
        ideal_type_weights={0: Fraction(2, 5), 1: Fraction(3, 5)},
        count_penalties=(
            Fraction(0, 1),
            Fraction(0, 1),
            Fraction(-1, 4),
        ),
        quadratic_coefficients_by_type={
            0: (Fraction(1, 4),),
            1: (Fraction(1, 8), Fraction(1, 6)),
        },
        residual_context=(),
        provider_role_sha256=_M2_ROLE,
        _reserved_fixture_token=_RESERVED_FIXTURE_TOKEN,
    )


__all__ = (
    "BINARY64_PARAMETER_ANALYTIC_LAW_STATEMENT",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_BACKEND_KIND",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_CANONICALIZATION_POLICY",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_FORMULA",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_LAW_LAYERS",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCHEMA_VERSION",
    "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCOPE",
    "IDEAL_RATIONAL_ANALYTIC_LAW_STATEMENT",
    "LEARNED_MODEL_SEPARATION_STATEMENT",
    "MAX_EXACT_RATIONAL_QUADRATIC_INTEGER_BITS",
    "MAX_EXACT_RATIONAL_QUADRATIC_SCORE_TERMS",
    "OPERATIONAL_RUNTIME_PROPOSAL_LAW_STATEMENT",
    "REPRESENTED_EXACT_SCORE_LAW_STATEMENT",
    "ExactRationalQuadraticInitialTilt",
    "ExactRationalQuadraticInitialTiltCertificate",
    "ExactRationalQuadraticInitialTiltError",
    "ExactRationalQuadraticInitialTiltPointEvaluation",
    "build_t28_m1_q_exact_score_provider",
    "build_t28_m2_q_exact_score_provider",
    "certify_exact_rational_quadratic_initial_tilt",
    "require_matching_exact_rational_quadratic_initial_tilt",
    "validate_exact_rational_quadratic_initial_tilt_certificate",
)
